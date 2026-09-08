"""消費 core/verbs.md §1 edit／§2、core/card-schema.md §1／§2／§5、
core/naming.md §3、modules/*/module.md §0；設定介面依 ADOPTION.md §2。
"""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json

from wf.compose.project_config import load_project_config
from wf.compose.schema import compose_schema
from wf.compose.transitions import is_legal_plan
from wf.compose.validate import validate, _equal
from wf.gh.client import GhError, NotFound
from wf.gh.writes import InvalidCommentURL
from wf.verbs._common import Printer, block_object, board_cards, card_number, chain_depth, parse_args
from wf.verbs._write import WriteResult, reject, write_card


def _hash(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def edit(card, assignment, *, client, catalog, ruling=None, enabled_modules=(),
         project_owner=None, project_number=None, emit=print):
    """card 為卡 ID 或 issue 號；catalog／已啟用模組由呼叫端供給。"""
    number, skipped = card_number(card, client)
    report = Printer(emit)

    def refuse(code, reason):
        return reject(client, number, code, reason, tuple(report))

    for other in skipped:
        report(f'略過無法解析的 issue #{other}')
    if ruling is None:
        report('無裁定連結')
    try:
        current = block_object(client.issue(number)['body'], 'wf-card')
        key, separator, raw = assignment.partition('=')
        if not separator:
            raise ValueError('--set 須為欄=JSON')
        if key in ('stage', 'state'):
            return refuse('D1', f'{key} 只由 move 寫')
        if key in ('card_id', 'source_issue'):
            return refuse('D3', f'{key} 不可由 edit 改')
        if key in {k for block in catalog.by_label('yaml wf-module')
                   for k in block.data.get('adds', {}).get('counters', [])}:
            report('模組欄由 `move` 寫')  # C09：verbs.md §2 末句無「拒」字，硬擋只 D1–D4／P1–P5
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
        if project_owner is None or project_number is None:
            raise GhError('無 Project 設定，未能確認 parent')
        parents, skipped = board_cards(client, client.project(project_owner, project_number, ()))
        for other in skipped:
            report(f'略過無法解析的 issue #{other}')
        if value not in parents:
            return refuse('D4', f'parent 不存在：{value}')
        parents[current['card_id']] = (number, updated)
        depth, broken = chain_depth(updated, parents)
        if broken is not None:
            report('parent 鏈有循環' if broken == '循環' else f'parent 鏈無法續查：{broken}')
        if depth > 2:
            report('上限 2')
    if key in current and _equal(current[key], value):
        return WriteResult(0, card=current, printed=tuple(report))
    if key in ('acceptance', 'verification', 'non_scope', 'resources'):
        updated['spec_version'] += 1
    old_hash, new_hash = _hash(current.get(key)), _hash(value)
    result = write_card(updated, client=client, number=number, catalog=catalog,
                        enabled_modules=enabled_modules, write_projection=False)
    if result.rc == 0:
        client.post_comment(number, 'wf:edit', f'{key}、{old_hash} → {new_hash}')
        if current['stage'] == '審核':
            client.post_comment(number, 'wf:edit', 'edit during review')
    return replace(result, printed=tuple(report))


def run(argv=None, *, client, root='.', catalog=None, enabled_modules=()):
    """七動詞統一入口名（S15）；參數次序同其餘動詞的 run，行為不變。"""
    args = parse_args('wf edit', argv, ('card', {}), ('--set', {'required': True, 'dest': 'assignment'}),
                      ('--ruling', {}))
    config = load_project_config(root)
    project = config['project'] or {}
    return edit(args.card, args.assignment, client=client, catalog=catalog,
                ruling=args.ruling, enabled_modules=enabled_modules,
                project_owner=project.get('owner'), project_number=project.get('number')).rc


main = run  # 舊名別名保留一版（既有呼叫端不改）
