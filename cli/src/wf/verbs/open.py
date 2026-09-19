"""消費 core/verbs.md §1 open／§2、core/card-schema.md §1–3／§5、
core/naming.md §1、core/state-machine.md §1–3、core/glossary.md 清單項／撤銷卡、
modules/initiative/module.md §0–1、ADOPTION.md §2。
operation-level precondition（core/verbs.md §2）：撤銷卡復板時核對 source_issue＝承載 issue；context 給定時
核對清單項所屬 repository 與 add_to_project 回傳 item 的 repository stable ID（在首次 write_project_field 之前）。
"""
from copy import deepcopy
from dataclasses import dataclass, replace
import re

from wf.compose.blocks import load_blocks, projection
from wf.compose.enable import activate
from wf.compose.project_config import load_project_config, module_names, ProjectConfigError
from wf.compose.schema import compose_schema
from wf.compose.validate import validate
from wf.context import IdentityError, rules_of
from wf.gh.target import check_item_repository, check_target_issue, item_ref, target_issue
from wf.verbs._common import (block_object, board_items, chain_depth, field_values, missing_fields,
                              parse_args, prevalidate_card, repo_cards, verify_source_issue)
from wf.verbs._ops import OperationOutcome, board_decision, receipt
from wf.verbs._write import WriteResult, guarded, prepare_card, reject, write_card


@dataclass(frozen=True)
class OpenResult(WriteResult):
    unverified: tuple[dict, ...] = ()


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


@guarded('open')
def open_issue(number, *, client, root='.', catalog=None, parent=None, area=None, emit=print,
               context=None):
    """verbs/main.py 可直接呼叫；所有 GitHub 操作經注入的 client，印項亦保留於結果。"""
    printed, unverified = [], []

    def finish(result):
        lines = tuple(dict.fromkeys([*printed, *result.printed]))
        for line in lines:
            emit(line)
        if result.rc:
            emit(result.reason)
        if isinstance(result, OperationOutcome):  # 收據型結果原樣帶出，⛔ 不把五鍵降級掉
            return replace(result, printed=lines)
        return OpenResult(result.rc, result.card, result.reason, result.rejection,
                          lines, tuple(unverified))

    def refuse(code, reason):
        return finish(reject(client, number, code, reason))

    def hard_block(exc, done=''):  # 身分不一致：本機一行、⛔ 不貼 wf:reject；done＝已完成的寫入（有才列）
        printed.append(f'硬擋・{exc.code}・{exc}' + done)
        return finish(WriteResult(1, reason=str(exc)))

    try:
        cfg = load_project_config(root)
    except ProjectConfigError as exc:
        printed.append(str(exc))
        unverified.append({'item': '建卡', 'kind': 'cannot', 'reason': str(exc)})
        return finish(WriteResult(0))
    rules = rules_of(root if context is None else context.rules)
    catalog = load_blocks(rules) if catalog is None else catalog
    location = cfg['project']
    board = client.project(**location, field_names=projection(catalog)) if location else None
    if board is None:
        printed.append('無 Project 設定')
        unverified.append({'item': 'D2 在板判定', 'kind': 'deferred',
                           'reason': '無 Project 設定，依 PM 預設視為不在板'})
    # 封存項仍在板上（core/verbs.md §2 D2：封存⛔ 不是撤銷卡），故 include_archived。
    items = board_items(board, client.repo, include_archived=True)
    on_board = set(items)
    source = client.issue(number)
    try:
        current = block_object(source['body'], 'wf-card', required=False)
        intake = None if current is not None else block_object(source['body'], 'wf-intake', required=False)
        if current is None and intake is None:
            return refuse('D2', '不是清單項也不是撤銷卡')
        if current is not None:
            verify_source_issue(current, number)
        if context is not None:
            check_target_issue(target_issue(source, number), context.repository)
        if current is None:
            errors = validate(intake, compose_schema(catalog, 'wf-intake'))
            if errors:
                raise ValueError('; '.join(f'{e.path}: {e.message}' for e in errors))
        if area is not None and area not in cfg['areas']:
            return refuse('D3', '--area 不在 areas')
        schema = compose_schema(catalog, 'wf-card')
        cards, skipped = repo_cards(client)
        printed.extend(f'略過無法解析的 issue #{other}' for other in skipped)
        if current is None:
            area = cfg['areas'][0] if area is None and len(cfg['areas']) == 1 else area
            if area not in cfg['areas']:
                return refuse('D3', '缺 --area 或 --area 不在 areas')
            # and 兩側次序⛔ 不可互換：缺 card_id 的卡在 cards 裡是 None 鍵（_common.py 用 card.get）。
            # re.fullmatch 在左時 None 讓它拋 TypeError，下方 except (ValueError, TypeError, KeyError)
            # 接得住 ⇒ 落 D3 拒收；把 area 篩選挪到左則變 None.split 的 AttributeError，該 except ⛔ 不接
            # ⇒ 整支 open 變 traceback。
            serials = [int(key.split('-')[1]) for key in cards
                       if re.fullmatch(schema['properties']['card_id']['pattern'], key) and key.split('-')[0] == area]
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
        # §1 合成順序：上界預驗在啟用判定與 parent D4 之前。
        prevalidate_card(card, catalog)
        for target in dict.fromkeys(p for p in (parent, card.get('parent')) if p is not None):
            if target not in cards or (board is not None and cards[target][0] not in on_board):
                return refuse('D4', f'parent 不存在於' + ('板上：' if board else 'repo：') + target)
            if board is None:
                printed.append('無 Project 設定，未驗 parent 在板')
                unverified.append({'item': f'parent {target} 在板', 'kind': 'deferred',
                                   'reason': '僅驗 repo 內 card_id 相符的卡'})
        enabled = activate([b.data for b in catalog.blocks if b.label == 'yaml wf-module'],
                           modules_list=module_names(cfg), card=card).names
        if current is None and 'initiative' in enabled:
            card['parent_spec_version'] = cards[card['parent']][1]['spec_version']
        card, values = prepare_card(card, current, None, catalog, enabled)
        if board is not None:
            for name, value in values.items():
                client.prepare_project_field(board, '', name, value)
        depth, broken = chain_depth(card, cards)
        printed.append('缺欄清單：' + '、'.join(missing_fields(card, rules)))
        printed.append(f'鏈深：{depth}' if broken is None else '鏈深無法計算：parent 鏈有循環或缺卡')
        if broken is not None:
            unverified.append({'item': '鏈深', 'kind': 'cannot', 'reason': 'parent 鏈有循環或缺卡'})
        elif depth > 2:
            printed.append('上限 2')
        if current is None:
            count = len(client.comments(number))
            printed.append(f'清單項留言數：{count}')
            if count:
                printed.append(f'{count} 則留言，開卡前讀全部（F-需求-02）')
    except IdentityError as exc:
        return hard_block(exc)
    except (ValueError, TypeError, KeyError) as exc:
        return refuse('D3', str(exc))
    # §2 D2 的回讀分流（WF-016）：在板上時先比回讀證據與本次 write plan，⛔ 不再一律拒收。
    # 回讀證據面含五個投影欄（`values`＝本次要寫進去的那批、`field_values` ＝板上現值）：
    # 只比卡面會把「卡面已寫成、投影欄還沒寫」誤判成收斂（查核序 1 finding WF-016-R1.1-001）。
    on_item = items.get(number)
    decision = board_decision(card, current, on_item, values if board is not None else None,
                              field_values(on_item) if on_item is not None else None)
    if decision.verdict == 'refuse':
        return refuse('D2', '已在板上')
    if decision.line:
        printed.append(decision.line)
    if decision.verdict == 'converge':
        return finish(receipt(WriteResult(0, card=current), decision.completed))
    item_id = decision.item_id  # resume 時沿用板上既有 item，⛔ 不重複 add_to_project
    if board is not None and item_id is None:
        added = client.add_to_project(board['id'], source['node_id'])['data']['addProjectV2ItemById']['item']
        item_id = added['id']
        if context is not None:  # A8：取得 item_id 之後、首次 write_project_field 之前；item 取自 mutation 回傳
            try:
                check_item_repository(item_ref(added, 'addProjectV2ItemById.item'), context.repository)
            except IdentityError as exc:
                return hard_block(exc, f'（已完成的寫入：add_to_project item {item_id}）')
    result = write_card(card, client=client, number=number, catalog=catalog,
                        project_owner=location['owner'] if location else None,
                        project_number=location['number'] if location else None,
                        item_id=item_id, enabled_modules=enabled, create=True)
    if decision.completed and not result.rc:  # 續作：上一次已完成的 add_to_project 要出現在收據
        result = receipt(result, decision.completed)
    if result.rc == 0 and current is not None:
        # §1 open 寫格：撤銷卡復板沿用 card_id／iteration 並寫轉移記錄留言（形狀同 move）。
        client.post_comment(number, 'wf:move', f"清單 → {machine['initial']}")
    return finish(result)


def run(argv, *, client, root='.', catalog=None, context=None):
    """只解析本動詞參數；七動詞接線由 verbs/main.py 提供。"""
    args = parse_args('wf open', argv, ('issue', {'type': int}), ('--parent', {}), ('--area', {}))
    return open_issue(args.issue, client=client, root=root, catalog=catalog,
                      parent=args.parent, area=args.area, context=context).rc
