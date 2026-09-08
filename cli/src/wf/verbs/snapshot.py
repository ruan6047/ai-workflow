"""消費 core/verbs.md §1 snapshot 列／§2（對帳例外、每次拒收一則）、
core/card-schema.md §1 (b)／§2 last_cited／§4 wf-note／§5 投影欄、
core/return.md note_responses、modules/snapshot/module.md §1（唯讀）、roles/pm.md F-PM-04。

本機輸出＝ `<out>/snapshot.json` 與 `<out>/snapshot.md`（覆寫）；out 缺省 `<root>/.wf/snapshot`。
snapshot.json 鍵（本檔定義，供總入口與 PM 讀）：
generated_at、baseline{repo, project}、cards[{card_id, number, state_open, card, projection}]、
mismatches[{card_id, number, field, card, projection}]、candidates[{card_id, comment_url, created_at, note}]、
invalid_candidates[{card_id, comment_url, created_at, reason}]、last_cited{id: {card_id, comment_url, created_at}}。
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from wf.compose.blocks import load_blocks, projection
from wf.compose.enable import is_enabled
from wf.compose.project_config import load_project_config, module_names
from wf.compose.schema import compose_schema
from wf.compose.validate import validate, _equal
from wf.gh.writes import CardBodyError, block_value
from wf.verbs._common import Printer, board_items, field_values, parse_args
from wf.verbs._write import projected, reject

OUT_DEFAULT = '.wf/snapshot'


@dataclass(frozen=True)
class SnapshotResult:
    rc: int
    data: dict | None = None
    printed: tuple[str, ...] = ()
    paths: tuple[Path, ...] = ()


def _text(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def _line(value):
    return _text(value).replace('\n', ' ').replace('|', '\\|')


def _errors(errors):
    return '; '.join(f'{e.path}: {e.message}' for e in errors)


def _block(comment, label):
    """回傳（區塊在不在, 值, 不能解析的原因）；壞區塊只記錄，⛔ 不擋（派工單 §5）。"""
    try:
        return (*block_value(comment.get('body') or '', label), None)
    except CardBodyError as exc:
        return True, None, str(exc)


def _shape(value, label, schema):
    """區塊存在時的內容檢查：值不是物件（card-schema §1／§4）或 schema 不過；schema 可為 callable（依卡合成）。"""
    if not isinstance(value, dict):
        return f'{label} 不是物件'
    return _errors(validate(value, schema(value) if callable(schema) else schema)) or None


def _markdown(data):
    lines = [f"# snapshot {data['generated_at']}", '',
             '| 卡ID | 階段/狀態 | 級別 | owner |', '|---|---|---|---|']
    for row in data['cards']:
        card = row['card']
        owner = card['owner']
        owner = '' if owner is None else f"{owner['role']}:{owner['actor']}"
        lines.append(f"| {row['card_id']} | {card['stage']}/{card['state']} "
                     f"| {card['tier'] or ''} | {owner} |")
    lines += ['', '## 對帳不等'] + ([
        f"- {m['card_id']} {m['field']}：卡面={_line(m['card'])} 投影={_line(m['projection'])}"
        for m in data['mismatches']] or ['- 無'])
    lines += ['', '## 候選'] + ([
        f"- {c['card_id']} {_line(c['note']['text'])} {c['comment_url']}"
        for c in data['candidates']] or ['- 無'])
    lines += [f"- 不合法：{c['card_id']} {c['comment_url']}（{_line(c['reason'])}）"
              for c in data['invalid_candidates']]
    lines += ['', '## last_cited', '| id | 卡ID | 留言 | created_at |', '|---|---|---|---|']
    lines += [f"| {i} | {v['card_id']} | {v['comment_url']} | {v['created_at']} |"
              for i, v in data['last_cited'].items()]
    return '\n'.join(lines) + '\n'


def snapshot(*, client, root='.', catalog=None, out=None, now=None, emit=print):
    """對狀態面只讀；對帳只印不重寫（core/verbs.md §2 末、modules/snapshot §1）。"""
    report = Printer(emit)
    catalog = load_blocks(root) if catalog is None else catalog
    cfg = load_project_config(root)
    location, listed = cfg['project'], module_names(cfg)

    def schema(card):  # C10：D3 用 S03 is_enabled 判定的模組合成 schema（同 open）；⛔ 不做的是 notes 條文合成
        return compose_schema(catalog, 'wf-card', [b.data['name'] for b in catalog.by_label('yaml wf-module')
                                                   if is_enabled(b.data, modules_list=listed, card=card)])
    cards, bad = [], []
    for issue in client.issues(state='all'):
        try:  # 區塊在不在才決定母體；值為 null 仍是卡（R1.14-1）。
            present, card = block_value(issue['body'] or '', 'wf-card')
        except CardBodyError as exc:
            bad.append((issue['number'], str(exc)))
            continue
        if not present:
            continue
        reason = _shape(card, 'wf-card', schema)
        if reason is not None:
            bad.append((issue['number'], reason))
        else:
            cards.append((issue, card))
    for number, reason in bad:
        reject(client, number, 'D3', reason)
        report(f'#{number} 拒收・D3・{reason}')
    if bad:  # 檢查先於首次寫入（§2）；本機輸出同樣不寫。
        return SnapshotResult(1, printed=tuple(report))
    board = client.project(**location, field_names=projection(catalog)) if location else None
    if board is None:
        report('無 Project 設定')
    items = board_items(board, client.repo, include_archived=True)  # 對帳含封存項：仍在板上
    rows, mismatches, candidates, invalid, cited = [], [], [], [], {}
    note_schema = compose_schema(catalog, 'wf-note')
    for issue, card in cards:
        number, card_id = issue['number'], card['card_id']
        item = items.get(number)
        values = field_values(item) if item is not None else None
        rows.append({'card_id': card_id, 'number': number,
                     'state_open': issue.get('state') == 'open',
                     'card': card, 'projection': values})
        for name, value in (projected(card, catalog) if values is not None else {}).items():
            if not _equal(values.get(name), value):
                report(f'{card_id} {name}：卡面={_text(value)} 投影={_text(values.get(name))}')
                mismatches.append({'card_id': card_id, 'number': number, 'field': name,
                                   'card': value, 'projection': values.get(name)})
        for comment in client.comments(number):
            where = {'card_id': card_id, 'comment_url': comment.get('url'),
                     'created_at': comment.get('created_at')}
            present, note, reason = _block(comment, 'wf-note')
            if present and reason is None:
                reason = _shape(note, 'wf-note', note_schema)
            if present and reason is not None:
                invalid.append(where | {'reason': reason})
            elif present:
                candidates.append(where | {'note': note})
            _, responses, _ = _block(comment, 'wf-return')
            responses = responses.get('note_responses') if isinstance(responses, dict) else None
            for response in responses if isinstance(responses, list) else []:
                identifier = response.get('id') if isinstance(response, dict) else None
                previous = cited.get(identifier)
                if isinstance(identifier, str) and (
                        previous is None
                        or str(previous['created_at']) <= str(where['created_at'])):
                    cited[identifier] = where
    data = {'generated_at': now or datetime.now(timezone.utc).isoformat(),
            'baseline': {'repo': getattr(client, 'repo', None), 'project': location},
            'cards': rows, 'mismatches': mismatches, 'candidates': candidates,
            'invalid_candidates': invalid, 'last_cited': cited}
    directory = Path(root) / OUT_DEFAULT if out is None else Path(out)
    directory.mkdir(parents=True, exist_ok=True)
    paths = (directory / 'snapshot.json', directory / 'snapshot.md')
    paths[0].write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    paths[1].write_text(_markdown(data), encoding='utf-8')
    return SnapshotResult(0, data, tuple(report), paths)


def run(argv, *, client, root='.', catalog=None):
    """只解析本動詞參數；七動詞接線由 S15 提供。"""
    args = parse_args('wf snapshot', argv, ('--out', {}))
    return snapshot(client=client, root=root, catalog=catalog, out=args.out).rc
