"""消費 core/verbs.md §1 brief 列／§2、core/dispatch.md（表、`json wf-module-sections`、
wf-contract schema、末段樣板）、core/handoff.md 每段首行、core/params.md rule_confirm_days、
core/return.md schema 的 required、core/glossary.md「來源（四個）」、
modules/resource-lock／initiative／identity §0。

段序、段名與誰填逐字讀 `core/dispatch.md` 的表，⛔ 不抄進程式碼；CLI 段只搬事實、⛔ 不改寫
不合併（第零條）。讀側驗卡失敗＝本機硬擋、零遠端寫入；§2 對帳的投影回寫與其失敗拒收仍在。
⛔ 不自動 merge；`--for` 分派＝TARGETS 字典。卡號查找、留言區塊與板上事實住 verbs/_common.py。
規則檔（dispatch／params／frontmatter）只經 RulesSource 讀；`.wf/contracts` 與 merge-tree 的工作樹只用 project root；
基線的預設分支取 resolved repository 的 API 值（無 context 時取 client 綁定值），⛔ 不寫死 main。
"""
from datetime import date
import json
from pathlib import Path
import re
from types import SimpleNamespace

from wf.compose.blocks import Source, load_blocks, projection, source_line
from wf.compose.frontmatter import parse_frontmatter
from wf.compose.project_config import load_project_config
from wf.compose.schema import compose_schema
from wf.compose.validate import validate
from wf.context import IdentityError, default_branch, rules_of
from wf.gh.client import GhError
from wf.gh.localgit import LocalGitUnavailable, merge_tree
from wf.verbs._common import (CardShapeError, Printer, block_object, card_number,
                              comment_blocks, module_activation, parse_args, repo_cards, verify_source_issue)
from wf.verbs._write import WriteResult, blocked, check_card, reconcile_projection
from wf.verbs.move_modules import IN_PROGRESS, MOVE_PRINTS, NO_PROJECT
from wf.verbs.notes import notes
from wf.verbs import closeout

DISPATCH, PARAMS = 'core/dispatch.md', 'core/params.md'
REVIEWER = 'reviewer'  # core/enums.md roles
MODULE_SECTION = '0 · 宣告區塊'  # modules/*/module.md 宣告區塊的節名
HUMAN, UNWIRED, NONE = '（人填）', '模組層未接線', '無'
NO_BRANCH, NO_PREVIOUS = '無分支，基線＝main 頭', '無前輪'
UNKNOWN_PREVIOUS = '未能取得前輪 findings'
NO_CONTRACT, BAD_CONTRACT = '專案層未宣告', '契約檔不合 schema'
NO_MERGE_TREE, CONFLICT = '未能比對 merge-tree', 'merge-tree 衝突'
TEMPLATE_HEAD = '交回單 JSON 樣板'
HARD_BLOCK = '硬擋・'  # core/verbs.md §2 本機硬擋行的前綴（`硬擋・<D 編號>・<原因>`）
DAYS =re.compile(r'^\|[ \t]*rule_confirm_days[ \t]*\|[ \t]*([0-9]+)', re.M)
CONTRACT = re.compile(r'^```json wf-contract[ \t]*\r?\n(.*?)^```[ \t]*\r?$', re.M | re.S)


def _plain(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)

def _remote(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except GhError:
        return None

def _mark(ctx, kind, relative, section):
    """core/handoff.md 每段首行 `[來源: <kind>:<path>#<節> · …]`（path 相對 rules root，⛔ 不把 kind 串進 path）；
    節名為空不補 `#`，逾 params.md rule_confirm_days 標 ⚠️。"""
    front = parse_frontmatter(ctx.rules.read_text(relative), relative)
    line = source_line(Source(kind, relative, section, front.name, front.when, front.last_confirmed))
    try:
        stale = ctx.days is not None and (ctx.today - date.fromisoformat(front.last_confirmed)).days > ctx.days
    except ValueError:
        stale = False
    return line + (' ⚠️' if stale else '')

def _rows(rules):
    """core/dispatch.md 的表：(段, 誰填, 內容) 逐列，段名逐字讀檔、⛔ 不抄進程式碼；rules＝RulesSource 或路徑。"""
    rows = [[cell.strip() for cell in line.strip('|').split('|')]
            for line in rules_of(rules).read_text(DISPATCH).splitlines()
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
    """基線列：merge-base；無分支改用 main 頭。reviewer 另列被審分支、來源 SHA 與三印。
    merge-tree 取源＝遠端 main 頭 vs `source_sha`：merge-base 對「main 與分支改同一行」
    的真實分岔會漏報無衝突；兩者不同時段內註明。取不到 main 頭＝印未能比對，⛔ 不當成無衝突。"""
    branch, sha = ctx.card.get('branch'), ctx.card.get('source_sha')
    head = _remote(ctx.client.branch_head, branch) if branch else None
    base = _remote(ctx.client.merge_base, ctx.default_branch, branch) if head else None
    lines = [] if base else [NO_BRANCH]
    base = base or _remote(ctx.client.branch_head, ctx.default_branch)
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
    main_head = _remote(ctx.client.branch_head, ctx.default_branch)
    if main_head is None:
        return lines + [NO_MERGE_TREE]
    if main_head != base:
        lines.append(f'merge-tree 取源＝main 頭 {main_head}，非合併基底 {_plain(base)}')
    try:
        lines.append(CONFLICT if merge_tree(main_head, sha, root=ctx.root) else 'merge-tree 無衝突')
    except LocalGitUnavailable:
        lines.append(NO_MERGE_TREE)
    return lines

def _previous_findings(ctx):
    """前輪列：同 iteration 內時間序（created_at）最後一則 role=reviewer 的 `wf-return`；
    沒有才退到 iteration−1。讀取失敗或區塊不能解析＝印未能取得（F-執行者-06：未知⛔ 不冒充
    「無前輪」）；成功讀到而確實沒有才印「無前輪」。"""
    current, returns, errors = ctx.card.get('iteration') or 0, [], []
    try:
        comments = ctx.client.comments(ctx.number)
    except GhError as exc:
        return [f'{UNKNOWN_PREVIOUS}：{exc}']
    for comment in comments:
        parsed = comment_blocks(comment, ('wf-return',))
        errors.extend(parsed['errors'])
        present, data = parsed['blocks']['wf-return']
        if present and not isinstance(data, dict):
            errors.append('wf-return 不是物件')  # 區塊在而值非物件＝未知（同 _common.block_object）
        elif isinstance(data, dict) and data.get('role') == REVIEWER:
            returns.append((str(comment.get('created_at') or ''), data))
    returns.sort(key=lambda pair: pair[0])
    for want in (current, current - 1):
        found = [data for _, data in returns if data.get('iteration') == want]
        if found:
            lines = [json.dumps(item, ensure_ascii=False) for item in found[-1].get('findings') or []]
            return lines or ([f"{UNKNOWN_PREVIOUS}：{'；'.join(errors)}"] if errors else [NO_PREVIOUS])
    return [f"{UNKNOWN_PREVIOUS}：{'；'.join(errors)}"] if errors else [NO_PREVIOUS]

def _capability(ctx):
    """能力層級建議列：角色對應 capability 欄的 level 與 reason（card-schema §1 $defs/capability）。"""
    key = 'review_capability' if ctx.target == REVIEWER else 'exec_capability'
    value = ctx.card.get(key) if isinstance(ctx.card.get(key), dict) else {}
    return [f'{key}.{field}：{_plain(value.get(field))}' for field in ('level', 'reason')]

def _read_notes(ctx):
    """內層 `notes` 的重讀與驗卡。§2「檢查先於首次遠端寫入」⇒ 這一步必須排在本動詞的對帳
    （會寫投影欄）之前：內層會再讀一次卡，它的讀側 D3 若排在對帳之後，就會留下「板已改、動詞
    才失敗」的中間態。非零時只把內層已算好的 rc／reason 與本機硬擋行往上帶（內層 emit 是
    no-op，這一行只能由 brief 印），⛔ 不重跑、⛔ 不增寫遠端（含第二則 wf:reject）。
    `--for closeout` 不印注意事項段（closeout.sections ⛔ 不呼叫 notes），故不讀。"""
    if ctx.target == 'closeout':
        return None
    result = notes(ctx.number, client=ctx.client, root=ctx.root, catalog=ctx.catalog,
                   for_role=ctx.target, emit=lambda line: None, context=ctx.context,
                   listing=ctx.listing.append)  # 編號行的專用通道（§3），⛔ 不從 printed 反解析
    ctx.notes = result
    if result.rc == 0:
        ctx.note_ids = list(result.note_ids)  # 正式 id 通道（_write.NotesResult），⛔ 不反解析 printed
        for line in result.printed:  # 候選與診斷行留在 CLI 操作輸出，⛔ 不進注意事項段（A7）
            ctx.report(line)
        return None
    for line in result.printed:
        if line.startswith(HARD_BLOCK):
            ctx.report(line)
    return WriteResult(result.rc, reason=result.reason, rejection=result.rejection,
                       printed=tuple(ctx.report))

def _notes(ctx):
    """注意事項列：只搬 `notes` 的編號清單（帶正式 id 的 `<n>. <id>：` 行，經 `listing` 通道逐行取得、
    段內行數＝`NotesResult.note_ids` 筆數），⛔ 不重寫合成、⛔ 不重跑——結果由 `_read_notes` 在對帳之前
    算好（正式 id 同時取出供樣板）；候選（`wf:note`）與診斷行⛔ 不在本段。"""
    return list(ctx.listing)

def _side_effects(ctx):
    """副作用入口列：`.wf/contracts/*.md` 的 `json wf-contract` 區塊，用 compose/validate.py 驗。"""
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
    """寫入集交集＝`move_modules` 的交集函式（缺則未接線）；語意住 resource-lock §1。"""
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
    """dispatch.md `wf-module-sections` 的 brief 鍵；名單＝單一啟用入口算出的 `capable`
    （core/modules.md §3 七項之一 ⇒ 只有 maturity=ready 且已啟用者貢獻），⛔ 不在此重判啟用。"""
    declared, = ctx.catalog.by_label('json wf-module-sections')
    capable, out = {module['name'] for module in ctx.activation.capable}, []
    for name, titles in declared.data['brief'].items():
        if name not in capable:
            continue
        mark = _mark(ctx, 'module', f'modules/{name}/module.md', MODULE_SECTION)
        out += [(title, mark, MODULE_SECTIONS.get((name, index), _unwired)(ctx))
                for index, title in enumerate(titles)]
    return out

def _dispatch_sections(ctx):
    """段序＝表列序；CLI 列依序對位 CLI_SECTIONS，人填列只印段名＋（人填）。"""
    builders, mark, out = iter(CLI_SECTIONS), _mark(ctx, 'core', DISPATCH, ''), []
    for name, who, note in _rows(ctx.rules):
        if f'--for {ctx.target}` 不印' in note:  # 表註逐字：該角色不印此列
            continue
        if who == 'CLI':
            out.append((name, mark, next(builders, _unwired)(ctx)))
        elif who.startswith('人'):
            out.append((name, mark, [HUMAN]))
        else:
            out += _module_sections(ctx)
    return out

TARGETS = {'executor': _dispatch_sections, REVIEWER: _dispatch_sections, 'closeout': closeout.sections}

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

def brief(card, *, target, client, root='.', catalog=None, emit=print, today=None, context=None,
          **trailers):
    report = Printer(emit)
    rules = rules_of(root if context is None else context.rules)
    catalog = load_blocks(rules) if catalog is None else catalog
    cfg = load_project_config(root)
    try:
        number, skipped = card_number(card, client)
    except IdentityError as exc:
        return blocked(report, exc.code, str(exc))
    for other in skipped:
        report(f'略過無法解析的 issue #{other}')
    try:
        current = block_object(client.issue(number)['body'], 'wf-card')
        verify_source_issue(current, number)
    except IdentityError as exc:
        return blocked(report, exc.code, str(exc))
    except (ValueError, TypeError, KeyError) as exc:
        return blocked(report, 'D3', str(exc))
    match = DAYS.search(rules.read_text(PARAMS))
    if match is None:
        report('未能讀取 rule_confirm_days，未評估過期')
    project = None if cfg['project'] is None else _remote(
        client.project, **cfg['project'], field_names=projection(catalog))
    if cfg['project'] is not None and project is None:
        report('未能讀取 Project')
    try:  # §1 合成順序：上界預驗不過＝啟用判定不得發生，落既有 D3。
        activation = module_activation(catalog, cfg, current, client=client, project=project, number=number)
    except CardShapeError as exc:
        return blocked(report, 'D3', str(exc))
    ctx = SimpleNamespace(card=current, number=number, target=target, client=client, root=root,
                          rules=rules, context=context, default_branch=default_branch(client, context),
                          catalog=catalog, cfg=cfg, project=project, activation=activation,
                          note_ids=[], notes=None, listing=[],
                          report=report, days=None if match is None else int(match[1]),
                          today=date.today() if today is None else today)
    if target == 'closeout':
        ctx.trailers = trailers
    # §2 檢查先於首次遠端寫入：本動詞與內層 `notes` 兩次讀卡的驗證全部排在對帳（第一次投影
    # 寫入）之前，任一個讀側 D3 成立時該次執行對遠端零寫入；投影欄算不出的拒收仍歸對帳。
    failed = check_card(current, client=client, number=number, catalog=catalog,
                        enabled_modules=activation.names,
                        fail=lambda reason: blocked(report, 'D3', reason)) \
        or _read_notes(ctx) or reconcile_projection(
            current, client=client, catalog=catalog, location=cfg['project'],
            project=project, number=number, report=report, context=context)
    if failed is not None:
        return failed
    for name, mark, lines in TARGETS[target](ctx):
        report('## ' + name)
        report(mark)
        for line in lines:
            report(line)
    if target == 'closeout':
        for line in closeout.squash(ctx):
            report(line)
    else:
        report(TEMPLATE_HEAD)
        report(json.dumps(_template(ctx), ensure_ascii=False, indent=2))
    return WriteResult(0, card=current, printed=tuple(report))

def run(argv, *, client, root='.', catalog=None, context=None):
    """只解析本動詞參數；七動詞接線由 verbs/main.py 提供。`--for` 值域＝TARGETS 的鍵。"""
    args = parse_args('wf brief', argv, ('card', {}), ('--for', {'dest': 'target', 'required': True,
                                                                   'choices': sorted(TARGETS)}),
                      ('--requested-by', {}), ('--planned-by', {}), ('--implemented-by', {}),
                      ('--reviewed-by', {'action': 'append'}))
    trailers = {key: getattr(args, key) for key in
                ('requested_by', 'planned_by', 'implemented_by', 'reviewed_by')} if args.target == 'closeout' else {}
    return brief(args.card, target=args.target, client=client, root=root, catalog=catalog, context=context,
                 **trailers).rc
