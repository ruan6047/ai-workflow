"""動詞層共用的純讀函式；消費 core/verbs.md §1（open／edit／move／notes／brief 列）／§2、
core/card-schema.md §1／§2 表／§5、core/naming.md §3、core/return.md 與 core/ruling.md 區塊、
modules/resource-lock/module.md §0 板上事實。GitHub 讀取全經注入的 client；不寫、不印，印項由各動詞組。
"""
import argparse
from pathlib import Path
import re

from wf.compose.blocks import projection
from wf.compose.enable import is_enabled
from wf.compose.project_config import module_names
from wf.gh.client import NotFound
from wf.gh.writes import CardBodyError, block_value, read_block


class Printer(list):
    """印項收集：呼叫即印並留存（供 WriteResult.printed）。"""
    def __init__(self, emit):
        super().__init__()
        self.emit = emit

    def __call__(self, line):
        self.append(line)
        self.emit(line)

def parse_args(prog, argv, *specs):
    """各動詞 run()/main() 的參數解析；specs＝(旗標或位置名, add_argument 的關鍵字)。"""
    parser = argparse.ArgumentParser(prog=prog)
    for name, options in specs:
        parser.add_argument(name, **options)
    return parser.parse_args(argv)

def block_object(body, label, required=True):
    """區塊在而值 null／非物件＝CardBodyError（block_value 之上，⛔ 不判內容）；
    不在時 required 同 read_block 的 CardBodyError、否則 None。"""
    present, value = block_value(body or '', label)
    if not present:
        return read_block(body or '', label, required)
    if not isinstance(value, dict):
        raise CardBodyError(f'{label} 不是物件')
    return value

def comment_blocks(comment, labels=('wf-return', 'wf-ruling')):
    """留言的作者、所屬 issue 號與各區塊 (在不在, 值)；壞 JSON／重複＝(False, None) 並記 errors。"""
    blocks, errors = {}, []
    for label in labels:
        try:
            blocks[label] = block_value(comment.get('body') or '', label)
        except CardBodyError as exc:
            blocks[label] = (False, None)
            errors.append(str(exc))
    tail = (comment.get('issue_url') or '').rsplit('/', 1)[-1]
    return {'author': comment.get('author'), 'issue': int(tail) if tail.isdigit() else None,
            'blocks': blocks, 'errors': errors}

def _collect(pairs):
    """(issue 號, body) 序列 → card_id → (issue 號, 卡面)，與無法解析而略過的 issue 號。"""
    cards, skipped = {}, []
    for number, body in pairs:
        try:
            card = block_object(body, 'wf-card', required=False)
        except CardBodyError:
            card = None
            skipped.append(number)
        if card is not None:
            cards[card.get('card_id')] = (number, card)
    return cards, skipped

def repo_cards(client):
    """全 repo 帶 wf-card 的 issue（含關閉與撤銷卡）。"""
    return _collect((issue['number'], issue.get('body')) for issue in client.issues(state='all'))

def card_number(ref, client):
    """卡 ID 或 issue 號 → (issue 號, 略過的 issue 號)；別的 issue 壞區塊只略過，呼叫端印。"""
    if isinstance(ref, int) or str(ref).isdigit():
        return int(ref), []
    cards, skipped = repo_cards(client)
    if ref not in cards:
        raise NotFound(f'card 不存在：{ref}')
    return cards[ref][0], skipped

def board_items(project, repo=None, *, include_archived=False):
    """Project 上的 issue 項：issue 號 → item；repo 給定時只取該 repo，封存項預設排除。"""
    out = {}
    for item in (project or {}).get('items') or ():
        content = item.get('content') or {}
        if (content.get('__typename') == 'Issue' and (include_archived or not item.get('isArchived'))
                and (repo is None or (content.get('repository') or {}).get('nameWithOwner') == repo)):
            out[content['number']] = item
    return out

def board_cards(client, project):
    """板上（非封存、本 repo）卡：card_id → (issue 號, 卡面)，與略過的 issue 號（D4 parent 用）。"""
    return _collect((number, client.issue(number).get('body'))
                    for number in board_items(project, client.repo))

def field_values(item):
    """投影欄原始值 → 文字；空欄 None（gh/client.project 的 fieldValues 形狀）。"""
    return {name: (None if raw is None else raw.get('text', raw.get('name')))
            for name, raw in (item.get('fieldValues') or {}).items()}

def board_facts(project, catalog, *, self_number=None, repo=None):
    """resource-lock §0 的板上事實：非封存、非本卡（repo 給定時只本 repo）的 state 與 owner_actor。"""
    names = {spec['key']: name for name, spec in projection(catalog).items()}
    facts = []
    for number, item in board_items(project, repo).items():
        if number != self_number:
            values = field_values(item)
            facts.append({'state': values.get(names['state']),
                          'owner_actor': (values.get(names['owner']) or '').partition(':')[2] or None})
    return facts

def enabled_modules(catalog, cfg, card, *, client=None, project=None, number=None):
    """modules/*/module.md §0 enable_if 的啟用判定：專案設定＋卡面＋板上事實（open／move 同判）。"""
    facts = board_facts(project, catalog, self_number=number,
                        repo=None if client is None else client.repo)
    return [block.data for block in catalog.by_label('yaml wf-module')
            if is_enabled(block.data, modules_list=module_names(cfg), card=card, board_facts=facts)]

def chain_depth(card, cards):
    """parent 鏈深 (層數, 斷點)；斷點 None＝走完、'循環'、或第一個缺的 card_id。"""
    depth, seen, parent = 0, {card.get('card_id')}, card.get('parent')
    while parent is not None:
        if parent in seen:
            return depth, '循環'
        if parent not in cards:
            return depth, parent
        seen.add(parent)
        depth += 1
        parent = cards[parent][1].get('parent')
    return depth, None

def missing_fields(card, root):
    """必填時點直接讀 core/card-schema.md §2 表；零不是空值。"""
    text = (Path(root) / 'core/card-schema.md').read_text(encoding='utf-8')
    section = re.split(r'^## ', re.split(r'^## 2\b.*$', text, flags=re.M)[1], flags=re.M)[0]
    fields = [key for line in section.splitlines()
              for cells in [[cell.strip() for cell in line.split('|')[1:-1]]]
              if len(cells) == 4 and cells[2] == '建卡'
              for key in cells[0].replace('`', '').split('、')]
    return [key for key in fields if card.get(key) in (None, '', [], {})]
