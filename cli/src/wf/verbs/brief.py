"""消費 core/verbs.md §1 brief 列／§2、core/dispatch.md（表、`json wf-module-sections`、
wf-contract schema、末段樣板）、core/handoff.md 每段首行、core/params.md rule_confirm_days、
core/return.md schema 的 required、core/glossary.md「來源（四個）」、
modules/resource-lock／initiative／identity §0；S11 派工單的 PM 預設。

段序、段名與誰填逐字讀 `core/dispatch.md` 的表，⛔ 不抄進程式碼；CLI 段只搬事實、⛔ 不改寫
不合併（第零條）。除 D3 的一則 `wf:reject` 外不寫任何遠端、⛔ 不自動 merge；`--for` 分派＝
TARGETS 字典（S12 掛 closeout 鍵）。行距壓成單行、輔助函式合併以壓行數，仍超出本片 240 行
上限（交回單 unverified 有量測）；`_block`／`_lookup`／`_mark`／`_plain`／`_remote` 是 S10b
`verbs/_common.py` 的收斂對象。
"""
import argparse
from datetime import date
import json
from pathlib import Path
import re
from types import SimpleNamespace

from wf.compose.blocks import Source, load_blocks, projection, source_line
from wf.compose.enable import is_enabled
from wf.compose.frontmatter import read_frontmatter
from wf.compose.project_config import load_project_config, module_names
from wf.compose.schema import compose_schema
from wf.compose.validate import validate
from wf.gh.client import GhError, NotFound
from wf.gh.localgit import LocalGitUnavailable, merge_tree
from wf.gh.writes import CardBodyError, read_block, read_card
from wf.verbs._write import WriteResult, reject
from wf.verbs.move_modules import IN_PROGRESS, MOVE_PRINTS, NO_PROJECT
from wf.verbs.notes import notes

DISPATCH, PARAMS = 'core/dispatch.md', 'core/params.md'
MAIN = 'main'  # 預設分支名（core/dispatch.md 基線列「基線＝main 頭」）
REVIEWER = 'reviewer'  # core/enums.md roles
MODULE_SECTION = '0 · 宣告區塊'  # modules/*/module.md 宣告區塊的節名
HUMAN, UNWIRED, NONE = '（人填）', '模組層未接線', '無'
NO_BRANCH, NO_PREVIOUS = '無分支，基線＝main 頭', '無前輪'
NO_CONTRACT, BAD_CONTRACT = '專案層未宣告', '契約檔不合 schema'
NO_MERGE_TREE, CONFLICT = '未能比對 merge-tree', 'merge-tree 衝突'
TEMPLATE_HEAD = '交回單 JSON 樣板'
NOTE_ID = re.compile(r'^[0-9]+\. ([FPT]-.+?-[0-9]{2})：')
DAYS = re.compile(r'^\|[ \t]*rule_confirm_days[ \t]*\|[ \t]*([0-9]+)', re.M)
CONTRACT = re.compile(r'^```json wf-contract[ \t]*\r?\n(.*?)^```[ \t]*\r?$', re.M | re.S)


def _plain(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)

def _remote(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except GhError:
        return None

def _block(body, label):
    """壞 JSON 或區塊重複＝當成沒有；卡面 wf-card 的 D3 另由 brief() 判。"""
    try:
        return read_block(body or '', label, required=False)
    except CardBodyError:
        return None

def _mark(ctx, origin, relative, section):
    """core/handoff.md 每段首行；節名為空不補空 `#`，逾 params.md rule_confirm_days 標 ⚠️。"""
    front = read_frontmatter(Path(ctx.root) / relative)
    line = source_line(Source(f'{origin}/{relative}', section, front.name, front.when,
                              front.last_confirmed))
    line = line if section else line.replace('# ·', ' ·', 1)
    try:
        stale = ctx.days is not None and (ctx.today - date.fromisoformat(front.last_confirmed)).days > ctx.days
    except ValueError:
        stale = False
    return line + (' ⚠️' if stale else '')

def _lookup(client, card_id):
    """卡ID→(issue 號, 卡面)；S10b 整併時收斂進 verbs/_common.py。"""
    for issue in _remote(client.issues, state='all') or []:
        found = _block(issue.get('body'), 'wf-card')
        if isinstance(found, dict) and found.get('card_id') == card_id:
            return issue['number'], found
    return None, None

def _rows(root):
    """core/dispatch.md 的表：(段, 誰填, 內容) 逐列，段名逐字讀檔、⛔ 不抄進程式碼。"""
    rows = [[cell.strip() for cell in line.strip('|').split('|')]
            for line in (Path(root) / DISPATCH).read_text(encoding='utf-8').splitlines()
            if line.startswith('|')]
    return [row for row in rows if len(row) == 3 and set(row[1]) - set('-: ')][1:]

_unwired = lambda ctx: [UNWIRED]  # 段名有宣告、實作未接線時的內容

def _listing(key, empty=NONE):
    """卡面陣列欄一條一列、逐字（含分號與換行的條目仍是一條），⛔ 不改寫不合併。"""
    return lambda ctx: [_plain(item) for item in ctx.card.get(key) or []] or [empty]

def _identity(ctx):
    keys = ('card_id', 'source_issue', 'tier', 'stage', 'iteration', 'parent', 'when')
    return [f'{k}：{_plain(ctx.card.get(k))}' for k in keys] + [f'from：pm · to：{ctx.target}']

def _baseline(ctx):
    """基線列：merge-base；無分支改用 main 頭。reviewer 另列被審分支、來源 SHA 與三印。"""
    branch, sha = ctx.card.get('branch'), ctx.card.get('source_sha')
    head = _remote(ctx.client.branch_head, branch) if branch else None
    base = _remote(ctx.client.merge_base, MAIN, branch) if head else None
    lines = [] if base else [NO_BRANCH]
    base = base or _remote(ctx.client.branch_head, MAIN)
    lines.append(f'合併基底 SHA：{_plain(base)}')
    if ctx.target != REVIEWER:
        return lines
    lines += [f'被審分支：{_plain(branch)}', f'來源 SHA：{_plain(sha)}']
    if not sha:
        return lines + ['來源 SHA 未填']
    if head is not None and head != sha:
        lines.append(f'分支頭 ≠ 來源 SHA：{head} ≠ {sha}')
    exists = _remote(ctx.client.commit_exists, sha)
    lines.append('來源 SHA 未 push' if exists is False
                 else '未能確認來源 SHA 是否已 push' if exists is None else '來源 SHA 已 push')
    try:
        lines.append(CONFLICT if merge_tree(base, sha, root=ctx.root) else 'merge-tree 無衝突')
    except LocalGitUnavailable:
        lines.append(NO_MERGE_TREE)
    return lines

def _previous_findings(ctx):
    """前輪列：本卡留言的 `wf-return`、`role`=reviewer、`iteration`＝卡面 iteration−1。"""
    lines, want = [], (ctx.card.get('iteration') or 0) - 1
    for comment in _remote(ctx.client.comments, ctx.number) or []:
        data = _block(comment.get('body'), 'wf-return')
        if isinstance(data, dict) and data.get('role') == REVIEWER and data.get('iteration') == want:
            lines += [json.dumps(item, ensure_ascii=False) for item in data.get('findings') or []]
    return lines or [NO_PREVIOUS]

def _capability(ctx):
    """能力層級建議列：角色對應的 capability 欄值＋tier_basis（理由欄規則未定，PM 預設）。"""
    key = 'review_capability' if ctx.target == REVIEWER else 'exec_capability'
    return [f'{key}：{_plain(ctx.card.get(key))}', f"tier_basis：{_plain(ctx.card.get('tier_basis'))}"]

def _notes(ctx):
    """注意事項列：S10 `notes` 的編號清單全文逐行搬入，⛔ 不重寫合成；正式 id 供樣板。"""
    result = notes(ctx.number, client=ctx.client, root=ctx.root, catalog=ctx.catalog,
                   emit=lambda line: None)
    ctx.note_ids = [m[1] for m in map(NOTE_ID.match, result.printed) if m]
    return list(result.printed)

def _side_effects(ctx):
    """副作用入口列：`.wf/contracts/*.md` 的 `json wf-contract` 區塊，用 S03 validate 驗。"""
    schema, lines, seen = compose_schema(ctx.catalog, 'wf-contract'), [], False
    for path in sorted(Path(ctx.root).glob('.wf/contracts/*.md')):
        for raw in CONTRACT.findall(path.read_text(encoding='utf-8')):
            seen = True
            try:
                data = json.loads(raw)
            except ValueError:
                data = None
            if not isinstance(data, dict) or validate(data, schema):
                lines.append(f'{BAD_CONTRACT}：{path.name}')
            else:
                lines += [_plain(item) for item in data['side_effects']]
    return lines if seen else [NO_CONTRACT]

# 依 core/dispatch.md 表中「誰填＝CLI」列的出現序對位；段名住表，⛔ 不抄進程式碼。
CLI_SECTIONS = (_identity, lambda ctx: [_plain(ctx.card.get('core_pain'))],
                _listing('acceptance'), _listing('non_scope'), _baseline,
                _previous_findings, _capability, _notes, _side_effects)

def _intersection(ctx):
    """寫入集交集＝S09 `move_modules` 的交集函式（缺則未接線）；語意住 resource-lock §1。"""
    emit = MOVE_PRINTS.get('resources_intersection')
    if emit is None:
        return [UNWIRED]
    if ctx.project is None:
        return [NO_PROJECT.format('寫入集交集')]
    stage = ctx.card.get('stage')
    return emit(ctx.card, f"{stage}/{ctx.card.get('state')}", f'{stage}/{IN_PROGRESS}',
                catalog=ctx.catalog, project=ctx.project, client=ctx.client) or [NONE]

def _spec_baseline(ctx):
    """規格基線：父卡 `spec_version` 與本卡 `parent_spec_version` 兩值並列。"""
    parent = ctx.card.get('parent')
    found = _lookup(ctx.client, parent)[1] if parent else None
    version = '未找到父卡' if found is None else _plain(found.get('spec_version'))
    return [f'父卡 {_plain(parent)} spec_version：{version}',
            f"parent_spec_version：{_plain(ctx.card.get('parent_spec_version'))}"]

# 鍵＝(模組名, 該模組 §0 `adds.handoff_sections` 的序位)；段名逐字住宣告，⛔ 不抄進程式碼。
MODULE_SECTIONS = {('resource-lock', 0): _listing('resources'), ('resource-lock', 1): _intersection,
                   ('initiative', 0): _spec_baseline, ('identity', 0): lambda ctx: [HUMAN]}

def _module_sections(ctx):
    """dispatch.md `wf-module-sections` 的 brief 鍵＋S03 is_enabled；板上事實與 notes 同形（私有故自寫）。"""
    declared, = ctx.catalog.by_label('json wf-module-sections')
    modules = {block.data['name']: block.data for block in ctx.catalog.by_label('yaml wf-module')}
    names = {spec['key']: name for name, spec in projection(ctx.catalog).items()}
    rows = [{name: (None if raw is None else raw.get('text', raw.get('name')))
             for name, raw in item['fieldValues'].items()}
            for item in (ctx.project or {}).get('items', [])]
    facts = [{'state': row.get(names['state']),
              'owner_actor': (row.get(names['owner']) or '').partition(':')[2] or None}
             for row in rows]
    listed, out = module_names(ctx.cfg), []
    for name, titles in declared.data['brief'].items():
        module = modules.get(name)
        if module is None or not is_enabled(module, modules_list=listed, card=ctx.card,
                                            board_facts=facts):
            continue
        mark = _mark(ctx, 'module', f'modules/{name}/module.md', MODULE_SECTION)
        out += [(title, mark, MODULE_SECTIONS.get((name, index), _unwired)(ctx))
                for index, title in enumerate(titles)]
    return out

def _dispatch_sections(ctx):
    """段序＝表列序；CLI 列依序對位 CLI_SECTIONS，人填列只印段名＋（人填）。"""
    builders, mark, out = iter(CLI_SECTIONS), _mark(ctx, 'core', DISPATCH, ''), []
    for name, who, note in _rows(ctx.root):
        if f'--for {ctx.target}` 不印' in note:  # 表註逐字：該角色不印此列
            continue
        if who == 'CLI':
            out.append((name, mark, next(builders, _unwired)(ctx)))
        elif who.startswith('人'):
            out.append((name, mark, [HUMAN]))
        else:
            out += _module_sections(ctx)
    return out

TARGETS = {'executor': _dispatch_sections, REVIEWER: _dispatch_sections}

def _template(ctx):
    """dispatch.md 末段的預填（note_responses ⛔ 不含候選）；其餘鍵留空依 return.md 的 required。"""
    body = {'card_id': ctx.card.get('card_id'), 'iteration': ctx.card.get('iteration'),
            'role': ctx.target,
            'acceptance': [{'text': text, 'method': '', 'evidence': '', 'falsifier': ''}
                           for text in ctx.card.get('acceptance') or []],
            'note_responses': [{'id': note, 'value': ''} for note in ctx.note_ids]}
    for key in compose_schema(ctx.catalog, 'wf-return').get('required', []):
        body.setdefault(key, '')
    return body

def brief(card, *, target, client, root='.', catalog=None, emit=print, today=None):
    printed = []

    def report(line):
        printed.append(line)
        emit(line)

    catalog = load_blocks(root) if catalog is None else catalog
    cfg = load_project_config(root)
    number = int(card) if str(card).isdigit() else _lookup(client, card)[0]
    if number is None:
        raise NotFound(f'card 不存在：{card}')
    try:
        current = read_card(client.issue(number)['body'] or '')
        if not isinstance(current, dict):
            raise CardBodyError('wf-card 不是物件')
    except (ValueError, TypeError, KeyError) as exc:
        return reject(client, number, 'D3', str(exc))
    match = DAYS.search((Path(root) / PARAMS).read_text(encoding='utf-8'))
    if match is None:
        report('未能讀取 rule_confirm_days，未評估過期')
    project = None if cfg['project'] is None else _remote(
        client.project, **cfg['project'], field_names=projection(catalog))
    if cfg['project'] is not None and project is None:
        report('未能讀取 Project')
    ctx = SimpleNamespace(card=current, number=number, target=target, client=client, root=root,
                          catalog=catalog, cfg=cfg, project=project, note_ids=[],
                          days=None if match is None else int(match[1]),
                          today=date.today() if today is None else today)
    for name, mark, lines in TARGETS[target](ctx):
        report('## ' + name)
        report(mark)
        for line in lines:
            report(line)
    report(TEMPLATE_HEAD)
    report(json.dumps(_template(ctx), ensure_ascii=False, indent=2))
    return WriteResult(0, card=current, printed=tuple(printed))

def run(argv, *, client, root='.', catalog=None):
    """只解析本動詞參數；七動詞接線由 S15 提供。`--for` 值域＝TARGETS 的鍵。"""
    parser = argparse.ArgumentParser(prog='wf brief')
    parser.add_argument('card')
    parser.add_argument('--for', dest='target', required=True, choices=sorted(TARGETS))
    args = parser.parse_args(argv)
    return brief(args.card, target=args.target, client=client, root=root, catalog=catalog).rc
