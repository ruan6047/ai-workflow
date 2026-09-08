"""消費 core/verbs.md §1 edit／§2、core/card-schema.md §1／§2／§5、
core/naming.md §3、modules/*/module.md §0；設定介面依 ADOPTION.md §2。
"""
import argparse
from copy import deepcopy
from dataclasses import replace
import hashlib
import json

from wf.compose.project_config import load_project_config
from wf.compose.schema import compose_schema
from wf.compose.transitions import is_legal_plan
from wf.compose.validate import validate, _equal
from wf.gh.client import GhError, NotFound
from wf.gh.writes import InvalidCommentURL, block_span, read_card
from wf.verbs._write import WriteResult, reject, write_card


def _hash(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _board(client, owner, number):
    if owner is None or number is None:
        raise GhError('無 Project 設定，未能確認 parent')
    cards = {}
    for item in client.project(owner, number, ())['items']:
        content = item.get('content') or {}
        if (item.get('isArchived') or content.get('__typename') != 'Issue'
                or content['repository']['nameWithOwner'] != client.repo):
            continue
        body = client.issue(content['number'])['body'] or ''
        if block_span(body, 'wf-card', required=False) is not None:
            card = read_card(body)
            cards[card['card_id']] = card
    return cards


def _number(card, client):
    if isinstance(card, int) or str(card).isdigit():
        return int(card)
    for issue in client.issues():
        body = issue['body'] or ''
        if block_span(body, 'wf-card', required=False) is not None:
            if read_card(body)['card_id'] == card:
                return issue['number']
    raise NotFound(f'card 不存在：{card}')


def edit(card, assignment, *, client, catalog, ruling=None, enabled_modules=(),
         project_owner=None, project_number=None, emit=print):
    """card 為卡 ID 或 issue 號；catalog／已啟用模組由呼叫端供給。"""
    number = _number(card, client)
    printed = []

    def report(message):
        printed.append(message)
        emit(message)

    def refuse(code, reason):
        return reject(client, number, code, reason, tuple(printed))

    if ruling is None:
        report('無裁定連結')
    try:
        current = read_card(client.issue(number)['body'] or '')
        if not isinstance(current, dict):
            raise ValueError('wf-card 不是物件')
        key, separator, raw = assignment.partition('=')
        if not separator:
            raise ValueError('--set 須為欄=JSON')
        if key in ('stage', 'state'):
            return refuse('D1', f'{key} 只由 move 寫')
        counters = {key for block in catalog.by_label('yaml wf-module')
                    for key in block.data.get('adds', {}).get('counters', [])}
        if key in ('card_id', 'source_issue') or key in counters:
            return refuse('D3', f'{key} 不可由 edit 改')
        value = json.loads(raw)
        json.dumps(value, allow_nan=False)
        updated = deepcopy(current)
        if key == 'notes+':
            key = 'notes'
            value = current[key] + [value]
        updated[key] = value
        errors = validate(updated, compose_schema(catalog, 'wf-card', enabled_modules))
        if errors:
            raise ValueError('; '.join(f'{e.path}: {e.message}' for e in errors))
        if not is_legal_plan(updated['stage_plan'], catalog=catalog):
            raise ValueError('stage_plan 不合階段序')
    except (ValueError, TypeError, KeyError) as exc:
        return refuse('D3', str(exc))
    if current.get('stage') == '審核':
        report('卡在審核階段')
    if ruling is not None:
        try:
            client.comment_from_url(ruling)
        except (NotFound, InvalidCommentURL):
            return refuse('D4', f'ruling 不存在：{ruling}')
    if key == 'source_sha' and value is not None and not client.commit_exists(value):
        return refuse('D4', f'source_sha 不在遠端：{value}')
    if key == 'parent' and value is not None:
        parents = _board(client, project_owner, project_number)
        if value not in parents:
            return refuse('D4', f'parent 不存在：{value}')
        parents[current['card_id']] = updated
        parent, depth, seen = value, 0, set()
        while parent is not None:
            if parent in seen:
                report('parent 鏈有循環')
                break
            seen.add(parent)
            depth += 1
            if parent not in parents:
                report(f'parent 鏈無法續查：{parent}')
                break
            parent = parents[parent]['parent']
        if depth > 2:
            report('上限 2')
    if key in current and _equal(current[key], value):
        return WriteResult(0, card=current, printed=tuple(printed))
    if key in ('acceptance', 'verification', 'non_scope', 'resources'):
        updated['spec_version'] += 1
    old_hash, new_hash = _hash(current.get(key)), _hash(value)
    result = write_card(updated, client=client, number=number, catalog=catalog,
                        enabled_modules=enabled_modules, write_projection=False)
    if result.rc == 0:
        client.post_comment(number, 'wf:edit', f'{key}、{old_hash} → {new_hash}')
        if current['stage'] == '審核':
            client.post_comment(number, 'wf:edit', 'edit during review')
    return replace(result, printed=tuple(printed))


def main(argv=None, *, client, catalog, root='.', enabled_modules=()):
    """供總入口分派；本片不修改 verbs/main.py。"""
    parser = argparse.ArgumentParser(prog='wf edit')
    parser.add_argument('card')
    parser.add_argument('--set', required=True, dest='assignment')
    parser.add_argument('--ruling')
    args = parser.parse_args(argv)
    config = load_project_config(root)
    project = config['project'] or {}
    return edit(args.card, args.assignment, client=client, catalog=catalog,
                ruling=args.ruling, enabled_modules=enabled_modules,
                project_owner=project.get('owner'), project_number=project.get('number')).rc
