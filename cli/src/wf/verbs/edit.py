"""消費 core/verbs.md §1 edit／§2、core/card-schema.md §1／§2／§5 wf-projection、
core/enums.md tiers、core/ruling.md kind、core/naming.md §3、modules/*/module.md §0；
設定介面依 ADOPTION.md §2。
"""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json

from wf.compose.blocks import projection
from wf.compose.project_config import load_project_config
from wf.compose.schema import compose_schema
from wf.compose.transitions import is_legal_plan
from wf.compose.validate import validate, _equal
from wf.gh.client import GhError, NotFound
from wf.gh.writes import InvalidCommentURL
from wf.verbs._common import (Printer, block_object, board_cards, board_items, card_number,
                              chain_depth, comment_blocks, parse_args)
from wf.verbs._write import (WriteResult, prepare_card, projection_values, reconcile_projection,
                             reject, write_card)

SPEC_KEYS = ('acceptance', 'verification', 'non_scope', 'resources')


def _hash(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _normalized(key):
    """`notes+` 只是卡面鍵 `notes` 的追加寫法；重複偵測一律先正規化成實際卡面鍵。"""
    return 'notes' if key == 'notes+' else key


def edit(card, assignments, *, client, catalog, ruling=None, enabled_modules=(),
         project_owner=None, project_number=None, emit=print):
    """card 為卡 ID 或 issue 號；assignments 為 `<欄>=<JSON>` 字串序列（⛔ 不收裸 str）；
    catalog／已啟用模組由呼叫端供給。整次提交要嘛全寫、要嘛零寫入。"""
    if isinstance(assignments, str):  # 裸 str 會被逐字元迭代成誤拒，且須早於任何遠端讀寫與 try
        raise TypeError('assignments 須為 <欄>=<JSON> 字串序列，⛔ 不收裸 str')
    assignments = list(assignments)
    number, skipped = card_number(card, client)
    report = Printer(emit)

    def refuse(code, reason):
        return reject(client, number, code, reason, tuple(report))

    for other in skipped:
        report(f'略過無法解析的 issue #{other}')
    if ruling is None:
        report('無裁定連結')
    try:  # ①賦值語法：全部 --set 逐項解析完才進下一層（層序由需求方 2026-09-12 裁定）
        current = block_object(client.issue(number)['body'], 'wf-card')
        items = []
        for assignment in assignments:
            key, separator, raw = assignment.partition('=')
            if not separator:
                raise ValueError('--set 須為欄=JSON')
            value = json.loads(raw)
            json.dumps(value, allow_nan=False)
            items.append((key, value))
    except (ValueError, TypeError, KeyError) as exc:
        return refuse('D3', str(exc))
    seen, duplicates = set(), {}  # ②正規化後重複欄位：順序＝各欄第二次出現的先後
    for key, _ in items:
        if _normalized(key) in seen:
            duplicates.setdefault(_normalized(key), None)
        seen.add(_normalized(key))
    if duplicates:
        return refuse('D3', '重複欄位：' + '、'.join(duplicates))
    for key, _ in items:  # ③禁寫欄位；同層多錯報 argv 最前的那一個
        if key in ('stage', 'state'):
            return refuse('D1', f'{key} 只由 move 寫')
        if key in ('card_id', 'source_issue'):
            return refuse('D3', f'{key} 不可由 edit 改')
    if {key for key, _ in items} & {k for block in catalog.by_label('yaml wf-module')
                                    for k in block.data.get('adds', {}).get('counters', [])}:
        report('模組欄由 `move` 寫')  # verbs.md §2 末句無「拒」字，硬擋只 D1–D4／P1–P5
    try:  # ④疊加後整卡 schema 與 stage_plan 階段序：整批疊完只驗一次
        updated = deepcopy(current)
        for key, value in items:
            updated[_normalized(key)] = current['notes'] + [value] if key == 'notes+' else value
        errors = validate(updated, compose_schema(catalog, 'wf-card', enabled_modules))
        if errors:
            raise ValueError('; '.join(f'{e.path}: {e.message}' for e in errors))
        if not is_legal_plan(updated['stage_plan'], catalog=catalog):
            raise ValueError('stage_plan 不合階段序')
    except (ValueError, TypeError, KeyError) as exc:
        return refuse('D3', str(exc))
    changed = [key for key in dict.fromkeys(_normalized(key) for key, _ in items)
               if not (key in current and _equal(current[key], updated[key]))]
    if current.get('stage') == '審核':
        report('卡在審核階段')
    comment = None
    if ruling is not None:
        try:
            comment = client.comment_from_url(ruling)
        except (NotFound, InvalidCommentURL):
            return refuse('D4', f'ruling 不存在：{ruling}')
    for key, value in items:  # ⑤D4；tier 降級只印不擋
        if key == 'tier':  # §1 edit 印格：降級（值域序自 core/enums.md tiers）而缺裁定或 kind 不符，只印不擋
            order, = (block.data['tiers']['enum'] for block in catalog.by_label('json wf-enums'))
            _, verdict = comment_blocks(comment or {}, ('wf-ruling',))['blocks']['wf-ruling']
            if (current.get(key) in order and value in order
                    and order.index(value) < order.index(current[key])
                    and (not isinstance(verdict, dict) or verdict.get('kind') != 'tier_change')):
                report('tier 降級而缺 --ruling 或 kind≠tier_change')
        if key == 'source_sha' and value is not None and not client.commit_exists(value):
            return refuse('D4', f'source_sha 不在遠端：{value}')
        if key == 'parent' and value is not None:
            if project_owner is None or project_number is None:
                raise GhError('無 Project 設定，未能確認 parent')
            parents, others = board_cards(client, client.project(project_owner, project_number, ()))
            for other in others:
                report(f'略過無法解析的 issue #{other}')
            if value not in parents:
                return refuse('D4', f'parent 不存在：{value}')
            parents[current['card_id']] = (number, updated)
            depth, broken = chain_depth(updated, parents)
            if broken is not None:
                report('parent 鏈有循環' if broken == '循環' else f'parent 鏈無法續查：{broken}')
            if depth > 2:
                report('上限 2')
    location = None if None in (project_owner, project_number) else {
        'owner': project_owner, 'number': project_number}
    board = None if location is None else client.project(project_owner, project_number,
                                                         projection(catalog))
    item_id = board_items(board, client.repo, include_archived=True).get(number, {}).get('id')
    # §1 edit 寫格：投影鍵變動即回寫該欄（§2 順序）；其餘鍵 ⛔ 不碰 Project。
    target = ({'project_owner': project_owner, 'project_number': project_number, 'item_id': item_id}
              if set(changed) & {spec['key'] for spec in projection(catalog).values()}
              else {'write_projection': False})
    try:  # ⑥投影預算與對帳。§2 檢查先於首次遠端寫入：新卡整批算完（含 max_bytes 與五欄可寫性）才對帳（同 move）
        snapshot = projection_values(board, item_id) if target.get('item_id') else None
        _, values = prepare_card(updated, current, snapshot, catalog, enabled_modules)
        for name, field in (values if item_id else {}).items():
            try:  # 算不出的欄，拒收本文要指得出是哪一欄（形狀同 _write.reconcile）
                client.prepare_project_field(board, item_id, name, field)
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(f'{name} 投影欄無法解析：{exc}') from exc
        failed = reconcile_projection(current, client=client, catalog=catalog, location=location,
                                      project=board, number=number, report=report)
    except (ValueError, TypeError, KeyError) as exc:
        return refuse('D3', str(exc))
    if failed is not None:  # 對帳自己的欄算不出＝已拒收（舊卡欄由 reconcile 先算後寫）
        return replace(failed, printed=tuple(report))
    if not changed:  # 全項等值＝沉默：⛔ 不寫卡面、⛔ 不貼留言
        return WriteResult(0, card=current, printed=tuple(report))
    if set(changed) & set(SPEC_KEYS):  # 規格欄整次提交只 +1，不論改了幾個規格欄
        updated['spec_version'] += 1
    body = '\n'.join(f'{key}、{_hash(current.get(key))} → {_hash(updated[key])}' for key in changed)
    result = write_card(updated, client=client, number=number, catalog=catalog,
                        enabled_modules=enabled_modules, **target)
    if result.rc == 0:
        client.post_comment(number, 'wf:edit', body)
        if current['stage'] == '審核':
            client.post_comment(number, 'wf:edit', 'edit during review')
    return replace(result, printed=tuple(report))


def run(argv=None, *, client, root='.', catalog=None, enabled_modules=()):
    """七動詞統一入口名；參數次序同其餘動詞的 run，行為不變。"""
    args = parse_args('wf edit', argv, ('card', {}),
                      ('--set', {'required': True, 'action': 'append', 'dest': 'assignments'}),
                      ('--ruling', {}))
    config = load_project_config(root)
    project = config['project'] or {}
    return edit(args.card, args.assignments, client=client, catalog=catalog,
                ruling=args.ruling, enabled_modules=enabled_modules,
                project_owner=project.get('owner'), project_number=project.get('number')).rc


main = run  # 舊名別名保留一版（既有呼叫端不改）
