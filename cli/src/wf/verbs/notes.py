"""消費 core/verbs.md §1 notes／§2／§3、core/naming.md §3／§4、
core/card-schema.md §1 notes 欄／§4 wf-note、core/handoff.md 每段首行、
core/enums.md stages、modules/pitfalls-13/module.md §1。
"""
from dataclasses import dataclass
from pathlib import Path
import re

from wf.compose.blocks import Source, load_blocks, projection, source_line
from wf.compose.frontmatter import parse_frontmatter
from wf.compose.project_config import load_project_config
from wf.compose.schema import compose_schema
from wf.compose.validate import validate, _equal
from wf.gh.client import GhError
from wf.gh.writes import CardBodyError
from wf.verbs._common import (CardShapeError, Printer, block_object, card_number, enabled_modules,
                              note_blocks, parse_args)
from wf.verbs._write import WriteResult, blocked, check_card, reconcile_projection

ITEM = re.compile(r'^- ([FPT]-.+-[0-9]{2})：(.+)$')
BACKTICK = re.compile(r'`([^`]+)`')


@dataclass(frozen=True)
class Note:
    id: str
    text: str
    mark: str


def _section(text, heading):
    """只取該 ## 節的行；heading 為 None 時取全檔。其餘散文由 ITEM 過濾。"""
    if heading is None:
        return '', text.splitlines()
    title, lines, keep = '', [], False
    for line in text.splitlines():
        if line.startswith('## '):
            keep = line.startswith('## ' + heading)
            title = line[3:] if keep else title
        elif keep:
            lines.append(line)
    return title, lines


def _mark(origin, relative, section, meta):
    """core/handoff.md 的每段首行，前面補來源四值；無 frontmatter 則省略後兩段。"""
    if meta is None:
        return f'[來源: {origin}/{relative}' + (f'#{section}]' if section else ']')
    return source_line(Source(f'{origin}/{relative}', section, *meta))


def _file_notes(root, relative, heading, origin, prefix=''):
    path = Path(root) / relative
    if not path.is_file():
        return []
    text = path.read_text(encoding='utf-8')
    front = parse_frontmatter(text, relative, diagnostics=[])
    meta = (front.name, front.when, front.last_confirmed) if front.name else None
    section, lines = _section(text, heading)
    mark = _mark(origin, relative, section, meta)
    return [Note(match[1], match[2], mark)
            for match in (ITEM.match(line) for line in lines)
            if match is not None and match[1].startswith(prefix)]


def _sorted_relative(root, pattern):
    return sorted(path.relative_to(Path(root)).as_posix() for path in Path(root).glob(pattern))


def notes(card, *, client, root='.', catalog=None, stage=None, for_role=None, emit=print,
          fail=None):
    """verbs/main.py 可直接呼叫；讀側驗卡失敗＝本機硬擋、零遠端寫入；§2 對帳的投影回寫與其
    失敗拒收仍在。for_role＝`brief --for` 的角色（§3 第 1 條）；缺省取卡面 owner.role。
    fail＝讀側驗卡失敗的處置，取 (report, code, reason) 同 `_write.blocked`；缺省即本機硬擋。
    失敗處置歸**呼叫它的那個頂層動詞**的契約：`review` 這個內部消費者傳入既有的遠端拒收，
    其留痕逐字維持基線，⛔ 不因 notes／brief 改成本機硬擋而消失。"""
    handle = blocked if fail is None else fail
    report = Printer(emit)
    catalog = load_blocks(root) if catalog is None else catalog
    cfg = load_project_config(root)
    number, skipped = card_number(card, client)
    for other in skipped:
        report(f'略過無法解析的 issue #{other}')
    try:
        current = block_object(client.issue(number)['body'], 'wf-card')
    except (ValueError, TypeError, KeyError) as exc:
        return handle(report, 'D3', str(exc))
    enums, = catalog.by_label('json wf-enums')
    if stage is not None and stage not in enums.data['stages']['enum']:
        report(f'階段 {stage} 不在 enums.stages，改用卡當前階段')
        stage = None
    stage = current.get('stage') if stage is None else stage
    project = None
    if cfg['project'] is None:
        report('無 Project 設定，未評估 resource-lock')
    else:
        project = client.project(**cfg['project'], field_names=projection(catalog))
    try:  # §1 合成順序：上界預驗不過＝啟用判定不得發生，落既有 D3。
        enabled = enabled_modules(catalog, cfg, current, client=client, project=project, number=number)
    except CardShapeError as exc:
        return handle(report, 'D3', str(exc))
    failed = check_card(current, client=client, number=number, catalog=catalog,  # 驗卡面過了
                        enabled_modules=[module['name'] for module in enabled],  # 才對帳（§2）
                        fail=lambda reason: handle(report, 'D3', reason)) or reconcile_projection(
                            current, client=client, catalog=catalog, location=cfg['project'],
                            project=project, number=number, report=report)
    if failed is not None:
        return failed
    role = (current.get('owner') or {}).get('role') if for_role is None else for_role
    if role is None:
        report('卡面 owner 未填，角色注意事項全印')
    items = []
    for relative in _sorted_relative(root, 'stages/*.md'):
        items += _file_notes(root, relative, '6', 'core', f'F-{stage}-')
    for relative in _sorted_relative(root, 'roles/*.md'):
        if role is None or Path(relative).stem == role:  # §3：角色檔只取 owner.role／--for 那份
            items += _file_notes(root, relative, '4', 'core', 'F-')
    for module in enabled:
        relative = f"modules/{module['name']}/module.md"
        found = _file_notes(root, relative, '2', 'module')
        items += found
        for declared in module.get('adds', {}).get('notes', []):
            if declared not in {note.id for note in found}:
                report(f"模組 {module['name']} 宣告 {declared} 未在 §2")
    items += _file_notes(root, f'.wf/stages/{stage}.md', None, 'project')
    mark = _mark('card', f'issues/{number}', 'notes', None)
    items += [Note(note['id'], note['text'], mark) for note in current.get('notes') or []]
    for index, note in enumerate(items, 1):
        report(f'{index}. {note.id}：{note.text} {note.mark}')
    _candidates(client, number, catalog, report, current)
    if any(module['name'] == 'pitfalls-13' for module in enabled):
        _pitfalls(root, stage, report)
    return WriteResult(0, card=current, printed=tuple(report))


def read_comments(client, number, report, label):
    """留言讀不到＝印未知後續跑（§2「其餘一律印」；F-執行者-06 未知⛔ 不冒充沒有）。review 共用。"""
    try:
        return client.comments(number)
    except GhError as exc:
        report(f'未能取得{label}：{exc}')
        return ()


def _candidates(client, number, catalog, report, card):
    """naming.md §3：只讀 wf-note 區塊；散文與首行不讀。一則留言內的 N 個區塊逐個獨立處理——
    壞兄弟⛔ 不遮蔽合法區塊；不合法者帶留言 URL、區塊序號、可解析時的 id 與原因四件。
    已正式化（與卡面 notes 某一筆三鍵逐鍵相等）者印一行略過，⛔ 不靜默丟棄。"""
    schema = compose_schema(catalog, 'wf-note')
    formal = card.get('notes') or []
    for comment in read_comments(client, number, report, '候選'):
        url = comment.get('url')
        try:  # 只有 fence 未閉合而區塊邊界無法辨認時才回報留言級錯誤
            blocks = note_blocks(comment.get('body'))
        except CardBodyError as exc:
            report(f'候選 {url} {exc}')
            continue
        for index, data, reason in blocks:
            mark = f"（id={data['id']}）" if data is not None and 'id' in data else ''
            if reason is None:
                reason = '; '.join(f'{e.path}: {e.keyword}' for e in validate(data, schema)) or None
            if reason is not None:
                report(f'候選 {url} 區塊 {index}{mark} 不合法：{reason}')
            elif any(_equal(data, note) for note in formal):
                report(f'候選 {url} 區塊 {index}{mark}已正式化，略過')
            else:
                report(f"候選：{data['text']}｜{data['origin']}｜{url}")


def _pitfalls(root, stage, report):
    """族名逐字取 modules/pitfalls-13/module.md §1 第 2–3 條的反引號字串。"""
    text = (Path(root) / 'modules/pitfalls-13/module.md').read_text(encoding='utf-8')
    bullets = [line for line in _section(text, '1')[1] if line.startswith('- ')]
    families = BACKTICK.findall(bullets[1])
    if stage == '執行':
        families += BACKTICK.findall(bullets[2])
    for family in families:
        report(f'13 族踩坑清冊 {family}：已檢查／不適用／發現')


def run(argv, *, client, root='.', catalog=None):
    """只解析本動詞參數；七動詞接線由 verbs/main.py 提供。"""
    args = parse_args('wf notes', argv, ('card', {}), ('--stage', {}))
    return notes(args.card, client=client, root=root, catalog=catalog, stage=args.stage).rc
