"""消費 core/verbs.md §1 notes／§2／§3、core/naming.md §3／§4、
core/card-schema.md §1 notes 欄／§4 wf-note、core/handoff.md 每段首行、
core/enums.md stages、modules/pitfalls-13/module.md §1；S10 派工單的 PM 預設。
"""
from dataclasses import dataclass
from pathlib import Path
import re

from wf.compose.blocks import Source, load_blocks, projection, source_line
from wf.compose.frontmatter import parse_frontmatter
from wf.compose.project_config import load_project_config
from wf.compose.schema import compose_schema
from wf.compose.validate import validate
from wf.gh.client import GhError
from wf.gh.writes import CardBodyError
from wf.verbs._common import Printer, block_object, card_number, enabled_modules, parse_args
from wf.verbs._write import WriteResult, check_card, reconcile_projection, reject

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


def notes(card, *, client, root='.', catalog=None, stage=None, for_role=None, emit=print):
    """S15 可直接呼叫；除 D3 的一則 wf:reject 與 §2 對帳的投影回寫外不寫任何遠端。
    for_role＝`brief --for` 的角色（§3 第 1 條）；缺省取卡面 owner.role。"""
    report = Printer(emit)
    catalog = load_blocks(root) if catalog is None else catalog
    cfg = load_project_config(root)
    number, skipped = card_number(card, client)
    for other in skipped:
        report(f'略過無法解析的 issue #{other}')
    try:
        current = block_object(client.issue(number)['body'], 'wf-card')
    except (ValueError, TypeError, KeyError) as exc:
        return reject(client, number, 'D3', str(exc), tuple(report))
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
    enabled = enabled_modules(catalog, cfg, current, client=client, project=project, number=number)
    failed = check_card(current, client=client, number=number, catalog=catalog,
                        enabled_modules=[module['name'] for module in enabled],
                        printed=tuple(report))
    if failed is not None:
        return failed
    reconcile_projection(current, client=client, catalog=catalog, location=cfg['project'],
                         project=project, number=number, report=report)
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
    _candidates(client, number, catalog, report)
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


def _candidates(client, number, catalog, report):
    """naming.md §3：只讀 wf-note 區塊；散文與首行不讀。"""
    schema = compose_schema(catalog, 'wf-note')
    for comment in read_comments(client, number, report, '候選'):
        try:  # 區塊在而值 null／非物件＝不合法的候選，⛔ 不是沒有候選（S14b 同判）
            data = block_object(comment.get('body'), 'wf-note', required=False)
        except CardBodyError:
            data = False
        if data is None:
            continue
        if data is False or validate(data, schema):
            report(f"候選 {comment.get('url')} 區塊不合法")
        else:
            report(f"候選：{data['text']}｜{data['origin']}｜{comment.get('url')}")


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
    """只解析本動詞參數；七動詞接線由 S15 提供。"""
    args = parse_args('wf notes', argv, ('card', {}), ('--stage', {}))
    return notes(args.card, client=client, root=root, catalog=catalog, stage=args.stage).rc
