"""消費 core/verbs.md §1 move／§2、core/state-machine.md §1–4、
core/card-schema.md §1／§2／§5、core/enums.md 值域、core/naming.md §2／§3、
core/ruling.md 必要鍵、core/return.md 區塊、core/tiers.md §1、stages/closeout.md §2。
"""
import argparse
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import re

from wf.compose.blocks import load_blocks, projection
from wf.compose.enable import is_enabled
from wf.compose.project_config import load_project_config, module_names, ProjectConfigError
from wf.compose.schema import compose_schema
from wf.compose.transitions import blocked_node, expand, is_legal_move, is_legal_plan
from wf.compose.validate import validate
from wf.gh.client import NotFound
from wf.gh.writes import InvalidCommentURL, read_block, read_card
from wf.verbs._write import WriteResult, _prepare, _values, reconcile, reject, write_card
from wf.verbs.edit import _number
from wf.verbs.open import missing_fields


def _board_facts(project, catalog, number, repo):
    facts = []
    for item in project['items'] if project else ():
        content = item.get('content') or {}
        if (item.get('isArchived') or content.get('__typename') != 'Issue'
                or content.get('repository', {}).get('nameWithOwner') != repo
                or content['number'] == number):
            continue
        values = {spec['key']: (raw.get('text', raw.get('name')) if raw else None)
                  for name, spec in projection(catalog).items()
                  for raw in [item['fieldValues'].get(name)]}
        owner = values.get('owner')
        facts.append({'state': values.get('state'),
                      'owner_actor': owner.partition(':')[2] if owner else None})
    return facts


def _ruling_prints(comment, current, number, expected, *, client, catalog, root):
    printed, blocks = [], {}
    if comment is not None:
        printed.append(f"裁定留言作者：{comment['author']}")
        other = int(comment['issue_url'].rsplit('/', 1)[1])
        if other != number:
            try:
                other_id = read_card(client.issue(other)['body'] or '')['card_id']
            except (ValueError, TypeError, KeyError):
                other_id = f'issue #{other}（卡ID 無法解析）'
            printed.append(f"裁定留言不在本卡：{current['card_id']}、{other_id}")
        for label in ('wf-return', 'wf-ruling'):
            try:
                blocks[label] = read_block(comment['body'] or '', label, required=False)
            except ValueError as exc:
                printed.append(str(exc))
        if not any(value is not None for value in blocks.values()):
            printed.append('裁定留言無 wf-return／wf-ruling 區塊')
    ruling = blocks.get('wf-ruling')
    if expected == 'wf-return' and blocks.get(expected) is None:
        printed.append('缺 wf-return 區塊')
    if expected in ('block', 'stop') and (not isinstance(ruling, dict) or ruling.get('kind') != expected):
        printed.append(f'缺 wf-ruling kind={expected}')
    if ruling is not None:
        schema = compose_schema(catalog, 'wf-ruling')
        printed.extend(f'wf-ruling：{e.path}: {e.message}' for e in validate(ruling, schema))
        if isinstance(ruling, dict):
            # 必要鍵住原件散文；不把 kind 的鍵清單另存於 CLI。
            text = (Path(root) / 'core/ruling.md').read_text(encoding='utf-8')
            pairs = dict(re.findall(r'([a-z_]+)＝([a-z_]+(?:、[a-z_]+)*)', text))
            kind = ruling.get('kind')
            for key in (pairs.get(kind, '') if isinstance(kind, str) else '').split('、'):
                if key and key not in ruling:
                    printed.append(f'wf-ruling kind={ruling.get("kind")} 缺必要鍵：{key}')
    return printed


def _terminal_prints(card, client):
    printed = []
    branch = card['branch']
    if branch is None:
        return ['無 PR', '分支未填']
    pulls = client.pulls_for_branch(branch)
    if not pulls:
        printed.append('無 PR')
    for row in pulls:
        pr = client.pull_request(row['number'])
        printed.append('PR 狀態：' + json.dumps(pr, ensure_ascii=False))
        printed.append('CI 狀態：' + json.dumps(client.ci_checks(pr['head']['sha']), ensure_ascii=False))
        sha = pr.get('merge_commit_sha')
        printed.append(f'merge SHA {sha} 是否 main 祖先：{client.is_ancestor(sha)}'
                       if sha else 'merge SHA 未填')
    try:
        printed.append(f'分支 {branch}：{client.branch_head(branch)}')
    except NotFound:
        printed.append(f'分支不存在：{branch}')
    return printed


def move(card, to, *, client, root='.', catalog=None, actor=None, source_sha=None,
         ruling=None, emit=print):
    """卡 ID 或 issue 號；S09 接收一般 stage/state 節點，阻塞展開僅供 D1。"""
    number = _number(card, client)
    printed = []

    def finish(result):
        lines = tuple([*printed, *result.printed])
        for line in lines:
            emit(line)
        if result.rc:
            emit(result.reason)
        return replace(result, printed=lines)

    def refuse(code, reason):
        return finish(reject(client, number, code, reason))

    try:
        config = load_project_config(root)
    except ProjectConfigError as exc:
        return finish(WriteResult(0, printed=(str(exc),)))
    catalog = load_blocks(root) if catalog is None else catalog
    location = config['project']
    project = client.project(**location, field_names=projection(catalog)) if location else None
    item_id = next((i['id'] for i in project['items']
                    if (i.get('content') or {}).get('__typename') == 'Issue'
                    and i['content'].get('repository', {}).get('nameWithOwner') == client.repo
                    and i['content']['number'] == number), None) if project else None
    try:
        current = read_card(client.issue(number)['body'] or '')
        if not isinstance(current, dict):
            raise ValueError('wf-card 不是物件')
        if not is_legal_plan(current['stage_plan'], catalog=catalog):
            raise ValueError('stage_plan 不合階段序')
        snapshot = _values(project, item_id) if item_id else None
        if current.get('schema_version') == 1:
            current, _ = _prepare(current, current, snapshot, catalog, ())
        from_node = f"{current['stage']}/{current['state']}"
        to_node = to if '/' in to or to == '清單' else f"{current['stage']}/{to}"
        target_stage, _, target_state = to_node.partition('/')
        dispatch = (target_stage == current['stage'] and target_state == '進行中'
                    and current['state'] in ('待辦', '退回'))
        updated = deepcopy(current)
        if actor is not None:
            role, separator, name = actor.partition(':')
            enums, = catalog.by_label('json wf-enums')
            if not separator or role not in enums.data['roles']['enum']:
                raise ValueError('--actor role 不在四值或缺 role:actor')
            if dispatch:
                updated['owner'] = {'role': role, 'actor': name}
        facts = _board_facts(project, catalog, number, client.repo)
        enabled = [b.data for b in catalog.by_label('yaml wf-module')
                   if is_enabled(b.data, modules_list=module_names(config), card=updated,
                                 board_facts=facts)]
        enabled_names = {m['name'] for m in enabled}
        errors = validate(current, compose_schema(catalog, 'wf-card', enabled_names))
        if errors:
            raise ValueError('; '.join(f'{e.path}: {e.message}' for e in errors))
        edges = expand(current['stage_plan'], enabled, catalog=catalog)
        origin = (blocked_node(current['stage'], current['blocked']['from'])
                  if current['state'] == '阻塞' else from_node)
        target = blocked_node(target_stage, current['state']) if target_state == '阻塞' else to_node
    except (ValueError, TypeError, KeyError) as exc:
        return refuse('D3', str(exc))
    if edges.plan_unfilled:
        printed.append('stage_plan 空（合成表只有需求階段）')
    if not is_legal_move(origin, target, edges):
        return refuse('D1', f'{from_node} → {to_node} 不在合成表內')
    if source_sha is not None and not client.commit_exists(source_sha):
        return refuse('D4', f'source_sha 不在遠端：{source_sha}')
    comment = None
    if ruling is not None:
        try:
            comment = client.comment_from_url(ruling)
        except (NotFound, InvalidCommentURL):
            return refuse('D4', f'ruling 不存在：{ruling}')
    expected = ('block' if target_state == '阻塞' else 'stop' if target_state == '停止'
                else 'wf-return' if from_node == '審核/待確認' else None)
    if ruling is None and (expected or to_node == '清單'):
        printed.append('缺 --ruling')
    printed.extend(_ruling_prints(comment, current, number, expected,
                                 client=client, catalog=catalog, root=root))
    if current['stage'] == '需求' and target_stage != '需求':
        printed.append('缺欄清單：' + '、'.join(missing_fields(current, root)))
    if current['stage'] == '規劃' and target_stage != '規劃':
        printed.extend(f'{key} 空' for key in ('acceptance', 'verification') if not current[key])
    if current['tier'] == 'T4' and not current['grilling']:
        printed.append('T4 而 grilling 空')
    if current['tier'] in ('T2', 'T3', 'T4') and '規劃' not in current['stage_plan']:
        printed.append('T2+ 而 stage_plan 缺規劃')
    if dispatch and actor is None:
        printed.append('未指定 actor')
    if to_node != '清單':
        updated.update(stage=target_stage, state=target_state)
    if to_node == '執行/進行中':
        updated.update(iteration=current['iteration'] + 1, source_sha=None, branch=f"wf/{current['card_id']}")
    if from_node == '執行/進行中' and to_node == '執行/待確認':
        updated['source_sha'] = source_sha
    if target_state == '阻塞':
        updated['blocked'] = {'from': current['state'], 'ruling': ruling}
    elif current['state'] == '阻塞':
        updated['blocked'] = None
    try:
        from wf.verbs.move_modules import apply_counters, module_prints
    except ImportError:
        printed.append('模組層未接線')
    else:
        kwargs = dict(catalog=catalog, config=config, enabled_names=enabled_names)
        updated = apply_counters(updated, from_node, to_node, **kwargs)
        printed.extend(module_prints(updated, from_node, to_node, **kwargs, project=project, client=client))
    if target in edges.terminal_nodes:
        printed.extend(_terminal_prints(updated, client))
    try:
        updated, values = _prepare(updated, current, snapshot, catalog, enabled_names)
        if item_id:
            # 先解析整批新舊欄，確保對帳不會搶在 D3 檢查前寫入。
            for valueset in (values, _prepare(current, current, snapshot, catalog, enabled_names)[1]):
                for name, value in valueset.items():
                    client.prepare_project_field(project, item_id, name, value)
            changed = reconcile(current, client=client, catalog=catalog, item_id=item_id,
                                project_owner=location['owner'], project_number=location['number'])
            if changed:
                printed.append('重寫投影欄：' + '、'.join(changed))
    except (ValueError, TypeError, KeyError) as exc:
        return refuse('D3', str(exc))
    result = write_card(updated, client=client, number=number, catalog=catalog,
                        project_owner=location['owner'] if location else None,
                        project_number=location['number'] if location else None,
                        item_id=item_id, enabled_modules=enabled_names)
    if not result.rc:
        if to_node == '清單' and item_id:
            client.remove_from_project(project['id'], item_id)
        if target in edges.terminal_nodes:
            client.close_issue(number)
        client.post_comment(number, 'wf:move', f'{from_node} → {to_node}')
    return finish(result)


def run(argv=None, *, client, root='.', catalog=None):
    """S15 的參數接點；不修改總入口。"""
    parser = argparse.ArgumentParser(prog='wf move')
    parser.add_argument('card')
    parser.add_argument('--to', required=True)
    parser.add_argument('--actor')
    parser.add_argument('--source-sha')
    parser.add_argument('--ruling')
    return move(**vars(parser.parse_args(argv)), client=client, root=root, catalog=catalog).rc


main = run
