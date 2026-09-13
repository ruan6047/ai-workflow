"""消費 core/verbs.md §1 review／§2／§3、core/return.md 段落表／schema／末段必填性、
core/naming.md §3／§4、core/tiers.md §1、core/enums.md 值域、modules/*/module.md §0。
D4 階段限定與規劃前 main 回退依 core/verbs.md §1 review 列。
刻意降級：gh/localgit.py 只有 merge_tree，無本機頭、log、diffstat 介面；
印未能取得，⛔ 不繞過 gh 層新增 git 子指令，也不得推論本機與遠端相同。
"""
import json
from pathlib import Path
import re

from wf.compose.blocks import load_blocks, projection
from wf.compose.project_config import load_project_config
from wf.compose.schema import compose_schema
from wf.compose.validate import validate
from wf.gh.client import NotFound
from wf.verbs._common import (CardShapeError, Printer, block_object, card_number, comment_blocks,
                              enabled_modules, parse_args)
from wf.verbs._write import WriteResult, check_card, reconcile_projection, reject
from wf.verbs.notes import notes, read_comments


def _missing(root, data, current, role, sections, report):
    """直接讀 return.md 末段的缺段列舉；不建立完整性規則系統或 schema 副本。"""
    text = (Path(root) / 'core/return.md').read_text(encoding='utf-8')
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


def _hints(data, current, number, role, sections, schema, client, root, catalog, report):
    _missing(root, data, current, role, sections, report)
    result = notes(number, client=client, root=root, catalog=catalog, emit=lambda line: None,
                   # 失敗處置歸呼叫它的頂層動詞：review 的讀側 D3 留痕逐字維持基線的一則
                   # wf:reject，⛔ 不隨 notes／brief 的本機硬擋一起消失（`notes` 的 fail 參數）。
                   fail=lambda report_, code, reason: reject(client, number, code, reason,
                                                             tuple(report_)))
    if result.rc:
        return result  # notes 已寫拒收；不得再寫第二則留言。
    covered = {item['id'] for item in data.get('note_responses', [])}
    for line in result.printed:
        match = re.match(r'^[0-9]+\. ([FPT]-.+?-[0-9]{2})：', line)
        if match and match[1] not in covered:
            report(f'note_responses 未覆蓋：{match[1]}')
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


def review(card, *, file, role, client, root='.', catalog=None, emit=print):
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
    sha = current.get('source_sha')
    if role == 'executor':
        enums, = catalog.by_label('json wf-enums')
        stages = enums.data['stages']['enum']
        execution = current.get('stage') in stages[stages.index('執行'):]
        branch = current.get('branch')
        sha = _head(client, branch, schema['properties']['source_sha']) if branch else None
        if sha is None and execution:
            return reject(client, number, 'D4', 'branch 缺少或遠端 ref 無法解析為 commit SHA', tuple(report))
        if sha is None:
            sha = _head(client, 'main', schema['properties']['source_sha'])
        report('未能比對本機分支頭')
    data.update(card_id=current.get('card_id'), iteration=current.get('iteration'), role=role, source_sha=sha)
    errors = validate(data, schema)
    if errors:
        return reject(client, number, 'D3', '; '.join(f'{e.path}: {e.message}' for e in errors), tuple(report))
    # §2 檢查先於首次遠端寫入：交回單 D3 與來源 SHA D4 都過了才對帳，⛔ 不在拒收前寫板。
    failed = reconcile_projection(current, client=client, catalog=catalog, location=cfg['project'],
                                  project=project, number=number, report=report) or _hints(
        data, current, number, role, sections, schema, client, root, catalog, report)
    if failed is not None:
        return failed
    report('未能取得 git 附錄')
    body = '```json wf-return\n' + json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)
    body += '\n```\n\n未能取得 git 附錄\n'
    client.post_comment(number, 'wf:return' if role == 'executor' else 'wf:verdict', body)
    return WriteResult(0, card=current, printed=tuple(report))


def run(argv, *, client, root='.', catalog=None):
    """七動詞入口接線由 verbs/main.py 負責；role 值域取 return schema。"""
    catalog = load_blocks(root) if catalog is None else catalog
    args = parse_args('wf review', argv, ('card', {}), ('--file', {'required': True}),
                      ('--role', {'required': True, 'choices':
                                  compose_schema(catalog, 'wf-return')['properties']['role']['enum']}))
    return review(args.card, file=args.file, role=args.role, client=client, root=root, catalog=catalog).rc
