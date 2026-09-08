"""消費 core/verbs.md §1 brief 列／§2、core/dispatch.md（表、`json wf-module-sections`、
wf-contract schema、末段樣板）、core/handoff.md 每段首行、core/params.md rule_confirm_days、
core/return.md schema 的 required、core/glossary.md「來源（四個）」、
modules/resource-lock／initiative／identity §0；S11 派工單的 PM 預設。

段序、段名與誰填逐字讀 `core/dispatch.md` 的表，⛔ 不抄進程式碼；CLI 段只搬事實、⛔ 不改寫
不合併（第零條）。除 D3 的一則 `wf:reject` 外不寫任何遠端、⛔ 不自動 merge；`--for` 分派＝
TARGETS 字典（S12 掛 closeout 鍵）。卡號查找、留言區塊與板上事實住 verbs/_common.py（S10b）。
"""
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
from wf.gh.client import GhError
from wf.gh.localgit import LocalGitUnavailable, merge_tree
from wf.verbs._common import (Printer, block_object, board_facts, card_number, comment_blocks, parse_args,
                              repo_cards)
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
    """前輪列（C02′）：同 iteration 內時間序（created_at）最後一則 role=reviewer 的 `wf-return`；
    沒有才退到 iteration−1；都沒有印「無前輪」。壞 JSON／重複／非物件的區塊當成沒有。"""
    current, returns = ctx.card.get('iteration') or 0, []
    for comment in _remote(ctx.client.comments, ctx.number) or []:
        _, data = comment_blocks(comment, ('wf-return',))['blocks']['wf-return']
        if isinstance(data, dict) and data.get('role') == REVIEWER:
            returns.append((str(comment.get('created_at') or ''), data))
    returns.sort(key=lambda pair: pair[0])
    for want in (current, current - 1):
        found = [data for _, data in returns if data.get('iteration') == want]
        if found:
            return [json.dumps(item, ensure_ascii=False) for item in found[-1].get('findings') or []] or [NO_PREVIOUS]
    return [NO_PREVIOUS]

def _capability(ctx):
    """能力層級建議列（C11）：角色對應 capability 欄的 level 與 reason（card-schema §1 $defs/capability）。"""
    key = 'review_capability' if ctx.target == REVIEWER else 'exec_capability'
    value = ctx.card.get(key) if isinstance(ctx.card.get(key), dict) else {}
    return [f'{key}.{field}：{_plain(value.get(field))}' for field in ('level', 'reason')]

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
    cards, skipped = _remote(repo_cards, ctx.client) or ({}, [])
    version = _plain(cards[parent][1].get('spec_version')) if parent in cards else '未找到父卡'
    return [f'略過無法解析的 issue #{other}' for other in skipped] + [
        f'父卡 {_plain(parent)} spec_version：{version}',
        f"parent_spec_version：{_plain(ctx.card.get('parent_spec_version'))}"]

# 鍵＝(模組名, 該模組 §0 `adds.handoff_sections` 的序位)；段名逐字住宣告，⛔ 不抄進程式碼。
MODULE_SECTIONS = {('resource-lock', 0): _listing('resources'), ('resource-lock', 1): _intersection,
                   ('initiative', 0): _spec_baseline, ('identity', 0): lambda ctx: [HUMAN]}

def _module_sections(ctx):
    """dispatch.md `wf-module-sections` 的 brief 鍵＋S03 is_enabled；板上事實同 notes／move（_common）。"""
    declared, = ctx.catalog.by_label('json wf-module-sections')
    modules = {block.data['name']: block.data for block in ctx.catalog.by_label('yaml wf-module')}
    facts = board_facts(ctx.project, ctx.catalog, self_number=ctx.number, repo=ctx.client.repo)
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
    return WriteResult(0, card=current, printed=tuple(report))

def run(argv, *, client, root='.', catalog=None):
    """只解析本動詞參數；七動詞接線由 S15 提供。`--for` 值域＝TARGETS 的鍵。"""
    args = parse_args('wf brief', argv, ('card', {}), ('--for', {'dest': 'target', 'required': True,
                                                                   'choices': sorted(TARGETS)}))
    return brief(args.card, target=args.target, client=client, root=root, catalog=catalog).rc
