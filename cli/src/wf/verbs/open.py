"""消費 core/verbs.md §1 open／§2、core/card-schema.md §1–3／§5、
core/naming.md §1、core/state-machine.md §1–3、core/glossary.md 清單項／撤銷卡、
modules/initiative/module.md §0–1、ADOPTION.md §2；S06 派工單的 PM 預設。
"""
import argparse
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import re

from wf.compose.blocks import load_blocks, projection
from wf.compose.enable import is_enabled
from wf.compose.project_config import load_project_config, module_names, ProjectConfigError
from wf.compose.schema import compose_schema
from wf.compose.validate import validate
from wf.gh.writes import read_block
from wf.verbs._write import WriteResult, _prepare, reject, write_card


@dataclass(frozen=True)
class OpenResult(WriteResult):
    unverified: tuple[dict, ...] = ()


def missing_fields(card, root):
    """必填時點直接讀 core/card-schema.md §2 表；零不是空值。"""
    text = (Path(root) / 'core/card-schema.md').read_text(encoding='utf-8')
    section = re.split(r'^## 2\b.*$', text, flags=re.M)[1]
    section = re.split(r'^## ', section, flags=re.M)[0]
    fields = []
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        if len(cells) == 4 and cells[2] == '建卡':
            fields.extend(cells[0].replace('`', '').split('、'))
    return [key for key in fields if card.get(key) in (None, '', [], {})]


def _initial_card(schema):
    card = {}
    for key in schema['required']:
        prop = schema['properties'][key]
        nullable = not validate(None, {**prop, '$defs': schema.get('$defs', {})})
        card[key] = (prop['const'] if 'const' in prop else None if nullable
                     else [] if prop.get('type') == 'array'
                     else '' if prop.get('type') == 'string' else None)
    card.update(spec_version=1, iteration=0)
    return card


def _depth(card, cards):
    depth, seen = 0, {card['card_id']}
    while card.get('parent'):
        parent = card['parent']
        if parent in seen or parent not in cards:
            return None
        seen.add(parent)
        depth += 1
        card = cards[parent][1]
    return depth


def open_issue(number, *, client, root='.', catalog=None, parent=None, area=None, emit=print):
    """S15 可直接呼叫；所有 GitHub 操作經注入的 client，印項亦保留於結果。"""
    printed, unverified = [], []

    def finish(result):
        lines = tuple(dict.fromkeys([*printed, *result.printed]))
        for line in lines:
            emit(line)
        if result.rc:
            emit(result.reason)
        return OpenResult(result.rc, result.card, result.reason, result.rejection,
                          lines, tuple(unverified))

    def refuse(code, reason):
        return finish(reject(client, number, code, reason))

    try:
        cfg = load_project_config(root)
    except ProjectConfigError as exc:
        printed.append(str(exc))
        unverified.append({'item': '建卡', 'kind': 'cannot', 'reason': str(exc)})
        return finish(WriteResult(0))
    catalog = load_blocks(root) if catalog is None else catalog
    location = cfg['project']
    board = client.project(**location, field_names=projection(catalog)) if location else None
    if board is None:
        printed.append('無 Project 設定')
        unverified.append({'item': 'D2 在板判定', 'kind': 'deferred',
                           'reason': '無 Project 設定，依 PM 預設視為不在板'})
    on_board = {item['content']['number'] for item in board['items']
                if item.get('content') and item['content'].get('__typename') == 'Issue'
                and item['content'].get('repository', {}).get('nameWithOwner') == client.repo} if board else set()
    if number in on_board:
        return refuse('D2', '已在板上')
    source = client.issue(number)
    try:
        current = read_block(source['body'] or '', 'wf-card', required=False)
        intake = None if current is not None else read_block(source['body'] or '', 'wf-intake', required=False)
        if current is None and intake is None:
            return refuse('D2', '不是清單項也不是撤銷卡')
        if current is None:
            errors = validate(intake, compose_schema(catalog, 'wf-intake'))
            if errors:
                raise ValueError('; '.join(f'{e.path}: {e.message}' for e in errors))
        if area is not None and area not in cfg['areas']:
            return refuse('D3', '--area 不在 areas')
        schema = compose_schema(catalog, 'wf-card')
        cards = {}
        for issue in client.issues(state='all'):
            card = read_block(issue['body'] or '', 'wf-card', required=False)
            if card is not None:
                cards[card['card_id']] = (issue['number'], card)
        if current is None:
            area = cfg['areas'][0] if area is None and len(cfg['areas']) == 1 else area
            if area not in cfg['areas']:
                return refuse('D3', '缺 --area 或 --area 不在 areas')
            serials = [int(key.split('-')[1]) for key in cards
                       if re.fullmatch(schema['properties']['card_id']['pattern'], key)]
            card = _initial_card(schema)
            card.update(card_id=f'{area}-{max(serials, default=0) + 1:03d}',
                        source_issue=number, core_pain=intake['observation'], parent=parent)
            unverified.append({'item': '跨 session 發號原子性', 'kind': 'deferred',
                               'reason': '本版由 PM 序列執行；掃描與寫入之間沒有鎖'})
        else:
            card = deepcopy(current)
            if parent is not None or area is not None:
                printed.append('撤銷卡復板保留既有 JSON；--parent／--area 不改既有欄')
        machine, = (b.data for b in catalog.blocks if b.label == 'json wf-state-machine')
        card['stage'], card['state'] = machine['initial'].split('/')
        for target in dict.fromkeys(p for p in (parent, card.get('parent')) if p is not None):
            if target not in cards or (board is not None and cards[target][0] not in on_board):
                return refuse('D4', f'parent 不存在於' + ('板上：' if board else 'repo：') + target)
            if board is None:
                printed.append('無 Project 設定，未驗 parent 在板')
                unverified.append({'item': f'parent {target} 在板', 'kind': 'deferred',
                                   'reason': '僅驗 repo 內 card_id 相符的卡'})
        enabled = [b.data['name'] for b in catalog.blocks if b.label == 'yaml wf-module'
                   and is_enabled(b.data, modules_list=module_names(cfg), card=card)]
        if current is None and 'initiative' in enabled:
            card['parent_spec_version'] = cards[card['parent']][1]['spec_version']
        card, values = _prepare(card, current, None, catalog, enabled)
        if board is not None:
            for name, value in values.items():
                client.prepare_project_field(board, '', name, value)
        missing = missing_fields(card, root)
        depth = _depth(card, cards)
        printed.append('缺欄清單：' + '、'.join(missing))
        printed.append(f'鏈深：{depth}' if depth is not None else '鏈深無法計算：parent 鏈有循環或缺卡')
        if depth is None:
            unverified.append({'item': '鏈深', 'kind': 'cannot', 'reason': 'parent 鏈有循環或缺卡'})
        elif depth > 2:
            printed.append('上限 2')
        if current is None:
            count = len(client.comments(number))
            printed.append(f'清單項留言數：{count}')
            if count:
                printed.append(f'{count} 則留言，開卡前讀全部（F-需求-02）')
    except (ValueError, TypeError, KeyError) as exc:
        return refuse('D3', str(exc))
    item_id = None
    if board is not None:
        added = client.add_to_project(board['id'], source['node_id'])
        item_id = added['data']['addProjectV2ItemById']['item']['id']
    return finish(write_card(card, client=client, number=number, catalog=catalog,
                             project_owner=location['owner'] if location else None,
                             project_number=location['number'] if location else None,
                             item_id=item_id, enabled_modules=enabled, create=True))


def run(argv, *, client, root='.', catalog=None):
    """只解析本動詞參數；七動詞接線由 S15 提供。"""
    parser = argparse.ArgumentParser(prog='wf open')
    parser.add_argument('issue', type=int)
    parser.add_argument('--parent')
    parser.add_argument('--area')
    args = parser.parse_args(argv)
    return open_issue(args.issue, client=client, root=root, catalog=catalog,
                      parent=args.parent, area=args.area).rc
