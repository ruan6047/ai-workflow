"""消費 core/verbs.md §1 snapshot 列／§2（對帳例外、每次拒收一則）、
core/card-schema.md §1 (b)／§2 last_cited／§4 wf-note／§5 投影欄、
core/return.md note_responses、modules/snapshot/module.md §1（唯讀）、roles/pm.md F-PM-04。

本機輸出＝ `<out>/snapshot.json` 與 `<out>/snapshot.md`（覆寫）；out 缺省 `<root>/.wf/snapshot`。
snapshot.json 鍵（本檔定義，供總入口與 PM 讀）：
generated_at、baseline{repo, project}、cards[{card_id, number, state_open, card, projection}]、
mismatches[{card_id, number, field, card, projection}]、candidates[{card_id, comment_url, created_at, note}]、
invalid_candidates[{card_id, comment_url, created_at, reason}]、last_cited{id: {card_id, comment_url, created_at}}。
"""
import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from wf.compose.blocks import load_blocks, projection
from wf.compose.project_config import load_project_config
from wf.compose.schema import compose_schema
from wf.compose.validate import validate, _equal
from wf.gh.writes import CardBodyError, read_block
from wf.verbs._write import projected, reject

OUT_DEFAULT = '.wf/snapshot'


@dataclass(frozen=True)
class SnapshotResult:
    rc: int
    data: dict | None = None
    printed: tuple[str, ...] = ()
    paths: tuple[Path, ...] = ()


def _values(item):
    """與 _write._values 同形的投影取值；_write 的是私有函式，本檔自寫、⛔ 不改該檔。"""
    return {name: (None if raw is None else raw.get('text', raw.get('name')))
            for name, raw in (item['fieldValues'] or {}).items()}


def _text(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def _line(value):
    return _text(value).replace('\n', ' ').replace('|', '\\|')


def _errors(errors):
    return '; '.join(f'{e.path}: {e.message}' for e in errors)


def _block(comment, label):
    """回傳（區塊資料, 不能解析的原因）；壞區塊只記錄，⛔ 不擋（派工單 §5）。"""
    try:
        return read_block(comment.get('body') or '', label, required=False), None
    except CardBodyError as exc:
        return None, str(exc)


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
    printed = []

    def report(line):
        printed.append(line)
        emit(line)

    catalog = load_blocks(root) if catalog is None else catalog
    location = load_project_config(root)['project']
    schema = compose_schema(catalog, 'wf-card')
    cards, bad = [], []
    for issue in client.issues(state='all'):
        try:
            card = read_block(issue['body'] or '', 'wf-card', required=False)
        except CardBodyError as exc:
            bad.append((issue['number'], str(exc)))
            continue
        if card is None:
            continue
        errors = validate(card, schema)  # core schema，⛔ 不做 §3 合成（§1 snapshot 列逐字）
        if errors:
            bad.append((issue['number'], _errors(errors)))
        else:
            cards.append((issue, card))
    for number, reason in bad:
        reject(client, number, 'D3', reason)
        report(f'#{number} 拒收・D3・{reason}')
    if bad:  # 檢查先於首次寫入（§2）；本機輸出同樣不寫。
        return SnapshotResult(1, printed=tuple(printed))
    board = client.project(**location, field_names=projection(catalog)) if location else None
    if board is None:
        report('無 Project 設定')
    items = {content['number']: item for item in (board['items'] if board else [])
             if (content := item.get('content') or {}).get('__typename') == 'Issue'
             and content.get('repository', {}).get('nameWithOwner') == client.repo}
    rows, mismatches, candidates, invalid, cited = [], [], [], [], {}
    note_schema = compose_schema(catalog, 'wf-note')
    for issue, card in cards:
        number, card_id = issue['number'], card['card_id']
        item = items.get(number)
        values = _values(item) if item is not None else None
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
            note, reason = _block(comment, 'wf-note')
            if note is not None:
                reason = _errors(validate(note, note_schema)) or None
            if reason is not None:
                invalid.append(where | {'reason': reason})
            elif note is not None:
                candidates.append(where | {'note': note})
            responses, _ = _block(comment, 'wf-return')
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
    return SnapshotResult(0, data, tuple(printed), paths)


def run(argv, *, client, root='.', catalog=None):
    """只解析本動詞參數；七動詞接線由 S15 提供。"""
    parser = argparse.ArgumentParser(prog='wf snapshot')
    parser.add_argument('--out')
    args = parser.parse_args(argv)
    return snapshot(client=client, root=root, catalog=catalog, out=args.out).rc
