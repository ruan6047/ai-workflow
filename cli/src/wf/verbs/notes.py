"""消費 core/verbs.md §1 notes／§2／§3、core/naming.md §3／§4、
core/card-schema.md §1 notes 欄／§4 wf-note、core/handoff.md 每段首行、
core/enums.md stages、modules/pitfalls-13/module.md §1；S10 派工單的 PM 預設。
"""
import argparse
from dataclasses import dataclass
from pathlib import Path
import re

from wf.compose.blocks import Source, load_blocks, projection, source_line
from wf.compose.enable import is_enabled
from wf.compose.frontmatter import parse_frontmatter
from wf.compose.project_config import load_project_config, module_names
from wf.compose.schema import compose_schema
from wf.compose.validate import validate
from wf.gh.writes import CardBodyError, read_block, read_card
from wf.verbs._write import WriteResult, reject
from wf.verbs.edit import _number

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


def _board_facts(client, catalog, location):
    """S02 project() 的板上事實；只取 resource-lock 要的 state 與 owner_actor。"""
    names = {spec['key']: name for name, spec in projection(catalog).items()}
    facts = []
    for item in client.project(**location, field_names=projection(catalog))['items']:
        values = {name: (None if raw is None else raw.get('text', raw.get('name')))
                  for name, raw in item['fieldValues'].items()}
        owner = values.get(names['owner']) or ''
        facts.append({'state': values.get(names['state']),
                      'owner_actor': owner.partition(':')[2] or None})
    return facts


def _sorted_relative(root, pattern):
    return sorted(path.relative_to(Path(root)).as_posix() for path in Path(root).glob(pattern))


def notes(card, *, client, root='.', catalog=None, stage=None, emit=print):
    """S15 可直接呼叫；除 D3 的一則 wf:reject 外不寫任何遠端。"""
    printed = []

    def report(line):
        printed.append(line)
        emit(line)

    catalog = load_blocks(root) if catalog is None else catalog
    cfg = load_project_config(root)
    number = _number(card, client)
    try:
        current = read_card(client.issue(number)['body'] or '')
        if not isinstance(current, dict):
            raise CardBodyError('wf-card 不是物件')
    except (ValueError, TypeError, KeyError) as exc:
        return reject(client, number, 'D3', str(exc))
    enums, = catalog.by_label('json wf-enums')
    if stage is not None and stage not in enums.data['stages']['enum']:
        report(f'階段 {stage} 不在 enums.stages，改用卡當前階段')
        stage = None
    stage = current.get('stage') if stage is None else stage
    if cfg['project'] is None:
        report('無 Project 設定，未評估 resource-lock')
        facts = ()
    else:
        facts = _board_facts(client, catalog, cfg['project'])
    enabled = [block.data for block in catalog.by_label('yaml wf-module')
               if is_enabled(block.data, modules_list=module_names(cfg),
                             card=current, board_facts=facts)]
    items = []
    for relative in _sorted_relative(root, 'stages/*.md'):
        items += _file_notes(root, relative, '6', 'core', f'F-{stage}-')
    for relative in _sorted_relative(root, 'roles/*.md'):
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
    return WriteResult(0, card=current, printed=tuple(printed))


def _candidates(client, number, catalog, report):
    """naming.md §3：只讀 wf-note 區塊；散文與首行不讀。"""
    schema = compose_schema(catalog, 'wf-note')
    for comment in client.comments(number):
        try:
            data = read_block(comment.get('body') or '', 'wf-note', required=False)
        except CardBodyError:
            data = False
        if data is None:
            continue
        if data is False or not isinstance(data, dict) or validate(data, schema):
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
    parser = argparse.ArgumentParser(prog='wf notes')
    parser.add_argument('card')
    parser.add_argument('--stage')
    args = parser.parse_args(argv)
    return notes(args.card, client=client, root=root, catalog=catalog, stage=args.stage).rc
