"""消費 core/verbs.md §1 move／§2、core/state-machine.md §1–4、
core/card-schema.md §1／§2／§5、core/enums.md 值域、core/naming.md §2／§3、
core/ruling.md 必要鍵、core/return.md 區塊、core/tiers.md §1、stages/closeout.md §2。
operation-level precondition（§2）：duplicate card_id、source_issue 承載核對、item 的 repository stable ID
都在讀到卡面／取得 item 之後、本動詞第一個遠端 mutation 之前；失敗＝本機硬擋一行、零遠端寫入。
"""
from copy import deepcopy
from dataclasses import replace
import json
import re

from wf.compose.blocks import load_blocks, projection
from wf.compose.enable import activate
from wf.compose.project_config import load_project_config, module_names, ProjectConfigError
from wf.compose.schema import compose_schema
from wf.compose.transitions import blocked_node, expand, is_legal_move, is_legal_plan
from wf.compose.validate import validate
from wf.context import IdentityError, default_branch, rules_of
from wf.gh.client import NotFound
from wf.gh.target import check_item_repository, item_ref
from wf.gh.writes import InvalidCommentURL
from wf.verbs._common import (block_object, board_facts, board_items, card_number, comment_blocks,
                              missing_fields, parse_args, prevalidate_card, verify_source_issue)
from wf.verbs._write import WriteResult, prepare_card, projection_values, reconcile, reject, write_card


def _ruling_prints(comment, current, number, expected, *, client, catalog, rules):
    """印項組合；區塊、作者與所屬 issue 的純讀住 _common.comment_blocks（與 review 共用）。"""
    printed, blocks = [], {}
    if comment is not None:
        found = comment_blocks(comment)
        blocks = found['blocks']
        printed.append(f"裁定留言作者：{found['author']}")
        if found['issue'] != number:
            try:
                other_id = block_object(client.issue(found['issue'])['body'], 'wf-card')['card_id']
            except (ValueError, TypeError, KeyError):
                other_id = f"issue #{found['issue']}（卡ID 無法解析）"
            printed.append(f"裁定留言不在本卡：{current['card_id']}、{other_id}")
        printed.extend(found['errors'])
        if not any(present for present, _ in blocks.values()):
            printed.append('裁定留言無 wf-return／wf-ruling 區塊')
    has_return, returned = blocks.get('wf-return', (False, None))
    has_ruling, ruling = blocks.get('wf-ruling', (False, None))
    if has_return and not isinstance(returned, dict):
        printed.append('wf-return 不是物件')
    if expected == 'wf-return' and not has_return:
        printed.append('缺 wf-return 區塊')
    if expected in ('block', 'stop') and (not isinstance(ruling, dict) or ruling.get('kind') != expected):
        printed.append(f'缺 wf-ruling kind={expected}')
    if has_ruling:
        schema = compose_schema(catalog, 'wf-ruling')
        printed.extend(f'wf-ruling：{e.path}: {e.message}' for e in validate(ruling, schema))
        if isinstance(ruling, dict):
            # 必要鍵住原件散文；不把 kind 的鍵清單另存於 CLI。
            text = rules.read_text('core/ruling.md')
            pairs = dict(re.findall(r'([a-z_]+)＝([a-z_]+(?:、[a-z_]+)*)', text))
            kind = ruling.get('kind')
            for key in (pairs.get(kind, '') if isinstance(kind, str) else '').split('、'):
                if key and key not in ruling:
                    printed.append(f'wf-ruling kind={ruling.get("kind")} 缺必要鍵：{key}')
    return printed


def _hard_block(printed, exc):
    """身分不一致：本機一行、零遠端寫入（§2 留痕條：沒有被拒的遠端寫入就⛔ 不貼 wf:reject）。"""
    printed.append(f'硬擋・{exc.code}・{exc}')
    return WriteResult(1, reason=str(exc))


def _terminal_prints(card, client, default):
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
        printed.append(f'merge SHA {sha} 是否 main 祖先：{client.is_ancestor(sha, default)}'
                       if sha else 'merge SHA 未填')
    try:
        printed.append(f'分支 {branch}：{client.branch_head(branch)}')
    except NotFound:
        printed.append(f'分支不存在：{branch}')
    return printed


def move(card, to, *, client, root='.', catalog=None, actor=None, source_sha=None,
         ruling=None, emit=print, context=None):
    """卡 ID 或 issue 號；move_modules 接收一般 stage/state 節點，阻塞展開僅供 D1。"""
    printed = []

    def finish(result):
        lines = tuple([*printed, *result.printed])
        for line in lines:
            emit(line)
        if result.rc:
            emit(result.reason)
        return replace(result, printed=lines)

    try:
        number, skipped = card_number(card, client)
    except IdentityError as exc:
        return finish(_hard_block(printed, exc))
    printed += [f'略過無法解析的 issue #{other}' for other in skipped]

    def refuse(code, reason):
        return finish(reject(client, number, code, reason))

    try:
        config = load_project_config(root)
    except ProjectConfigError as exc:
        return finish(WriteResult(0, printed=(str(exc),)))
    rules = rules_of(root if context is None else context.rules)
    catalog = load_blocks(rules) if catalog is None else catalog
    location = config['project']
    project = client.project(**location, field_names=projection(catalog)) if location else None
    item = board_items(project, client.repo, include_archived=True).get(number)
    item_id = item['id'] if item else None
    try:
        current = block_object(client.issue(number)['body'], 'wf-card')
        verify_source_issue(current, number)
        if item is not None and context is not None:  # A8：取得 item 之後、本動詞首次 mutation 之前
            check_item_repository(item_ref(item), context.repository)
        snapshot = projection_values(project, item_id) if item_id else None
        if current.get('schema_version') == 1:
            current, _ = prepare_card(current, current, snapshot, catalog, ())
        # §1 合成順序：上界預驗在啟用判定與任何語意判定之前；1→2 遷移仍先跑（§6 遷移路徑）。
        prevalidate_card(current, catalog)
        if not is_legal_plan(current['stage_plan'], catalog=catalog):
            raise ValueError('stage_plan 不合階段序')
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
        facts = board_facts(project, catalog, self_number=number, repo=client.repo)
        activation = activate([b.data for b in catalog.by_label('yaml wf-module')],
                              modules_list=module_names(config), card=updated, board_facts=facts)
        enabled = activation.capable  # 自動能力七項（core/modules.md §3）只收 capable
        enabled_names = set(activation.names)
        errors = validate(current, compose_schema(catalog, 'wf-card', enabled_names))
        if errors:
            raise ValueError('; '.join(f'{e.path}: {e.message}' for e in errors))
        edges = expand(current['stage_plan'], enabled, catalog=catalog)
        origin = (blocked_node(current['stage'], current['blocked']['from'])
                  if current['state'] == '阻塞' else from_node)
        target = blocked_node(target_stage, current['state']) if target_state == '阻塞' else to_node
    except IdentityError as exc:
        return finish(_hard_block(printed, exc))
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
                                 client=client, catalog=catalog, rules=rules))
    missing = missing_fields(current, rules) if current['stage'] == '需求' and target_stage != '需求' else []
    if missing and to_node != '清單':  # 非空且不是撤銷才印
        printed.append('缺欄清單：' + '、'.join(missing))
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
    # registry 載不進來＝ModuleValidation 的明確失敗（core/modules.md §5），在 bootstrap 就擋掉。
    # 刻意保留函式內 import（D1 之後才載，是既有的注入點），但⛔ 無 try/except：
    # ImportError 要一路炸上來，⛔ 不得推出「模組層可以未接線續跑」。
    from wf.verbs.move_modules import apply_counters, module_prints
    kwargs = dict(catalog=catalog, config=config, enabled_names=enabled_names)
    updated = apply_counters(updated, from_node, to_node, **kwargs)
    printed.extend(module_prints(updated, from_node, to_node, **kwargs, project=project, client=client))
    if target in edges.terminal_nodes:
        printed.extend(_terminal_prints(updated, client, default_branch(client, context)))
    try:
        updated, values = prepare_card(updated, current, snapshot, catalog, enabled_names)
        if item_id:
            for name, value in values.items():  # 先解析整批新卡欄，確保對帳不搶在 D3 檢查前寫入
                try:
                    client.prepare_project_field(project, item_id, name, value)
                except (ValueError, TypeError, KeyError) as exc:
                    raise ValueError(f'{name} 投影欄無法解析：{exc}') from exc
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


def run(argv=None, *, client, root='.', catalog=None, context=None):
    """verbs/main.py 的參數接點；不修改總入口。"""
    args = parse_args('wf move', argv, ('card', {}), ('--to', {'required': True}), ('--actor', {}),
                      ('--source-sha', {}), ('--ruling', {}))
    return move(**vars(args), client=client, root=root, catalog=catalog, context=context).rc


main = run
