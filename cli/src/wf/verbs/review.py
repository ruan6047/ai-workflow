"""消費 core/verbs.md §1 review／§2／§3、core/return.md 段落表／schema／末段必填性、
core/naming.md §3／§4、core/tiers.md §1、core/enums.md 值域、modules/*/module.md §0。
D4 階段限定與規劃前預設分支回退依 core/verbs.md §1 review 列（預設分支取 resolved repository 的 API 值）。
本機分支頭比對與 git 附錄的唯讀 git 子指令全走 gh/localrev.py（⛔ 不在本層自己開 subprocess）：
比對對象＝`refs/heads/<卡面 branch>`，`branch` null 時＝`refs/heads/<預設分支>`；附錄 base＝遠端預設
分支頭、head＝已補進交回單的 `source_sha`，在 project root 的本機工作樹上算。取不到就印一行帶
非空原因（rc 仍 0），⛔ 不印空區段、⛔ 不冒充無改動、⛔ 不推論本機與遠端相同。
兩者的本機讀取與 body 組裝都在首次遠端寫入之前（§2 檢查先於首次遠端寫入）。
"""
import json
from pathlib import Path
import re

from wf.compose.blocks import load_blocks, projection
from wf.compose.project_config import load_project_config
from wf.compose.schema import compose_schema
from wf.compose.validate import validate
from wf.context import IdentityError, default_branch, rules_of
from wf.gh.client import NotFound
from wf.gh.localrev import LocalRevUnavailable, diff_stat, log_commits, rev_parse
from wf.verbs._common import (CardShapeError, Printer, block_object, card_number, comment_blocks,
                              enabled_modules, parse_args, verify_source_issue)
from wf.verbs._write import WriteResult, blocked, check_card, reconcile_projection, reject
from wf.verbs.notes import notes, read_comments

NO_LOCAL_HEAD = '未能比對本機分支頭'
NO_APPENDIX = '未能取得 git 附錄'
COMMITS, CHANGES = 'commit 清單', '改動面'


def _missing(rules, data, current, role, sections, report):
    """直接讀 return.md 末段的缺段列舉；不建立完整性規則系統或 schema 副本。"""
    text = rules.read_text('core/return.md')
    line = next(line for line in text.splitlines() if line.startswith('一則留言只有一個'))
    clauses = line.split('缺段（', 1)[1].split('。', 1)[0].split('；')
    for clause in clauses:
        if '已啟用模組' in clause:
            continue
        if '全級別' not in clause and current.get('tier') in ('T0', 'T1'):
            continue
        match = re.search(r'`role=([^`]+)`', clause)
        if match and match[1] != role:
            continue
        for key in re.findall(r'`([^`]+)`', clause):
            if key == 'review' or key.startswith('role='):
                continue
            if key not in data:
                report(f'缺段：{key}')
    for key, spec in sections.items():
        if key not in data:
            report(f"缺段：{spec['label']}")


def _empty_text(value, path, report, markers, schema):
    """只查結構化欄位的字面與 text；字串模組段不做語意解析。"""
    if isinstance(value, dict):
        properties = schema.get('properties', {})
        if any(isinstance(v, str) and v in markers and v in properties.get(k, {}).get('enum', [])
               for k, v in value.items()):
            if not value.get('text', '').strip():
                report(f'{path}：text 空')
        for key, item in value.items():
            _empty_text(item, f'{path}.{key}', report, markers, properties.get(key, {}))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _empty_text(item, f'{path}[{index}]', report, markers, schema.get('items', {}))


def _hints(data, current, number, role, sections, schema, client, root, catalog, report, rules, context):
    _missing(rules, data, current, role, sections, report)
    result = notes(number, client=client, root=root, catalog=catalog, emit=lambda line: None,
                   # 失敗處置歸呼叫它的頂層動詞：review 的讀側 D3 留痕逐字維持基線的一則
                   # wf:reject，⛔ 不隨 notes／brief 的本機硬擋一起消失（`notes` 的 fail 參數）。
                   fail=lambda report_, code, reason: reject(client, number, code, reason,
                                                             tuple(report_)), context=context)
    if result.rc:
        return result  # notes 已寫拒收；不得再寫第二則留言。
    covered = {item['id'] for item in data.get('note_responses', [])}
    for note_id in result.note_ids:  # 正式 id 通道（_write.NotesResult），⛔ 不反解析 printed
        if note_id not in covered:
            report(f'note_responses 未覆蓋：{note_id}')
    _empty_text(data.get('note_responses', []), 'note_responses', report,
                ('not_applicable', 'found'), schema['properties']['note_responses'])
    for index, item in enumerate(data.get('unverified', [])):
        if not item['reason'].strip():
            report(f'unverified[{index}].reason 空')
    for key in sections:
        _empty_text(data.get(key), key, report, ('不適用', '發現'), sections[key])
    existing = set()
    for comment in read_comments(client, number, report, '既有交回單'):
        parsed = comment_blocks(comment, ('wf-return',))
        for error in parsed['errors']:
            report(f'既有交回單未能解析：{error}')
        _, previous = parsed['blocks']['wf-return']
        if isinstance(previous, dict) and isinstance(previous.get('findings'), list):
            existing.update(item['finding_id'] for item in previous['findings']
                            if isinstance(item, dict) and isinstance(item.get('finding_id'), str))
    for item in data.get('findings', []):
        if item['finding_id'] in existing:
            report(f"finding_id 撞號：{item['finding_id']}")
    if 'review_result' in data and 'findings' in data:
        # 不自行定義一致性規則；兩欄逐字並列交 PM 判（verbs.md §1 review 印格）。
        report('交回單欄位一致性（PM 判）：' + json.dumps(
            {key: data[key] for key in ('review_result', 'findings')}, ensure_ascii=False))
    return None


def _head(client, branch, sha_schema):
    try:
        sha = client.branch_head(branch)
    except (NotFound, KeyError, TypeError):
        return None
    return sha if not validate(sha, sha_schema) and sha != '0' * 40 else None


def _local_head(ref, remote, git_root):
    """verbs.md §1 review 列的本機分支頭比對：本機 `refs/heads/<ref>` 等於遠端頭＝兩句都⛔ 不印；
    不等＝恰一行同時帶兩個 40 碼 SHA；本機 git 狀態取不到（非工作樹、git 不可執行、本機無該 ref）
    ＝恰印「未能比對本機分支頭」，⛔ 不推論兩邊相同、⛔ 不因此改 rc。"""
    if not ref or remote is None:
        return (NO_LOCAL_HEAD,)
    try:
        local = rev_parse(f'refs/heads/{ref}', root=git_root)
    except LocalRevUnavailable:
        return (NO_LOCAL_HEAD,)
    if local is None:
        return (NO_LOCAL_HEAD,)
    return () if local == remote else (f'本機分支頭 ≠ 遠端頭：{local} ≠ {remote}',)


def _one_line(exc):
    """失敗原因的呈現邊界（`core/return.md`「卡與身分」列、`core/verbs.md` §1 review 列的「各恰一行」）：
    真 Git 的 stderr 常是多行——ownership 檢查失敗就是 fatal 行＋提示行＋空行＋指令行——直接內插會讓
    stdout 與 body 各多出幾行。這裡把所有空白序列（含換行、tab）折成單一空格，⛔ 不截斷內容。
    折完仍為空（例外自身無訊息）＝退到例外型別名，⛔ 不冒充已知原因、⛔ 不讓原因變空。
    正規化只做在呈現這一層：gh/localrev.py 仍原樣保留該次 stderr，⛔ 不在資料層改寫事實。"""
    return ' '.join(str(exc).split()) or type(exc).__name__


def _appendix(base, head, git_root):
    """return.md「卡與身分」列的 git 附錄：base＝遠端預設分支頭、head＝已解析的 `source_sha`，
    在 project root 的本機工作樹上算；commit 清單用兩點、改動面用三點（三點左端取 merge-base，
    兩點會把只在 base 上變動的檔算進來）。任一端缺席或子指令失敗＝恰一行帶非空原因，
    ⛔ 不印空區段、⛔ 不冒充無改動。"""
    try:
        if base is None:
            raise LocalRevUnavailable('未能取得遠端預設分支頭')
        if head is None:
            raise LocalRevUnavailable('來源 SHA 未解析為 commit SHA')
        for label, revision in (('base', base), ('head', head)):
            if rev_parse(revision, root=git_root) is None:
                raise LocalRevUnavailable(f'本機沒有 {label}：{revision}')
        return ([f'{COMMITS}（{base}..{head}）：'] + log_commits(base, head, root=git_root)
                + [f'{CHANGES}（{base}...{head}）：'] + diff_stat(base, head, root=git_root))
    except LocalRevUnavailable as exc:
        return [f'{NO_APPENDIX}：{_one_line(exc)}']


def review(card, *, file, role, client, root='.', catalog=None, emit=print, context=None):
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
        verify_source_issue(current, number)  # 身分不一致＝本機硬擋零寫入，⛔ 不貼 wf:reject
    except IdentityError as exc:
        return blocked(report, exc.code, str(exc))
    except (ValueError, TypeError, KeyError) as exc:
        return reject(client, number, 'D3', str(exc), tuple(report))
    project = None if cfg['project'] is None else client.project(
        **cfg['project'], field_names=projection(catalog))
    try:  # §1 合成順序：上界預驗不過＝啟用判定不得發生，落既有 D3。
        enabled = [module['name'] for module in
                   enabled_modules(catalog, cfg, current, client=client, project=project, number=number)]
    except CardShapeError as exc:
        return reject(client, number, 'D3', str(exc), tuple(report))
    failed = check_card(current, client=client, number=number, catalog=catalog,
                        enabled_modules=enabled, printed=tuple(report))
    if failed is not None:
        return failed  # 卡面 D3＝整卡拒：⛔ 不再往下做，⛔ 不貼 wf:verdict／wf:return
    try:
        data = json.loads(Path(file).read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise ValueError('交回單不是物件')
    except (ValueError, TypeError, KeyError, OSError) as exc:
        return reject(client, number, 'D3', str(exc), tuple(report))
    schema = compose_schema(catalog, 'wf-return', enabled)
    sections = {key: spec for name in enabled
                for key, spec in schema['$defs']['module_return_sections'].get(name, {}).items()}
    sha_schema = schema['properties']['source_sha']
    sha = current.get('source_sha')
    # 本機 git 一律用 project root：無 context（自舉直呼、測試）時才退到 root 參數。
    git_root = root if context is None else context.project.root.canonical
    remote_default = []  # 遠端預設分支頭本次只讀一次：executor 的回退與附錄 base 同一顆
    if role == 'executor':
        enums, = catalog.by_label('json wf-enums')
        stages = enums.data['stages']['enum']
        execution = current.get('stage') in stages[stages.index('執行'):]
        branch = current.get('branch')
        sha = _head(client, branch, sha_schema) if branch else None
        if sha is None and execution:
            return reject(client, number, 'D4', 'branch 缺少或遠端 ref 無法解析為 commit SHA', tuple(report))
        default = default_branch(client, context)
        if sha is None:  # 規劃前的回退：遠端側取源仍是遠端預設分支頭（§1 review 列）
            remote_default.append(_head(client, default, sha_schema))
            sha = remote_default[0]
        for line in _local_head(branch or default, sha, git_root):
            report(line)
    data.update(card_id=current.get('card_id'), iteration=current.get('iteration'), role=role, source_sha=sha)
    errors = validate(data, schema)
    if errors:
        return reject(client, number, 'D3', '; '.join(f'{e.path}: {e.message}' for e in errors), tuple(report))
    if not remote_default:
        remote_default.append(_head(client, default_branch(client, context), sha_schema))
    # §2 檢查先於首次遠端寫入：本機 ref 讀取、log、diffstat 與 body 組裝全在對帳（會寫板）之前。
    appendix = _appendix(remote_default[0], sha, git_root)
    body = '```json wf-return\n' + json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)
    body += '\n```\n\n' + '\n'.join(appendix) + '\n'
    failed = reconcile_projection(current, client=client, catalog=catalog, location=cfg['project'],
                                  project=project, number=number, report=report, context=context) or _hints(
        data, current, number, role, sections, schema, client, root, catalog, report, rules, context)
    if failed is not None:
        return failed
    for line in appendix:
        report(line)
    client.post_comment(number, 'wf:return' if role == 'executor' else 'wf:verdict', body)
    return WriteResult(0, card=current, printed=tuple(report))


def run(argv, *, client, root='.', catalog=None, context=None):
    """七動詞入口接線由 verbs/main.py 負責；role 值域取 return schema。"""
    catalog = load_blocks(rules_of(root if context is None else context.rules)) if catalog is None else catalog
    args = parse_args('wf review', argv, ('card', {}), ('--file', {'required': True}),
                      ('--role', {'required': True, 'choices':
                                  compose_schema(catalog, 'wf-return')['properties']['role']['enum']}))
    return review(args.card, file=args.file, role=args.role, client=client, root=root, catalog=catalog,
                  context=context).rc
