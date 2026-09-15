"""消費 core/modules.md §1／§2／§4／§5 與 core/enums.md 的 module_scope／module_maturity。

被測物＝`wf.module_validation`（唯一邊界）與它在 `wf.verbs.main.bootstrap` 的 fail-closed 接線。
所有 GitHub 操作走 cli/tests/fakes.py 的替身；⛔ 不碰網路。
"""
import ast
import json
import sys

import pytest

from .fakes import FakeGhClient
from .test_compose_schema import ROOT
from wf.compose.blocks import Block, Catalog, Source, load_blocks
from wf.compose.enable import KINDS, READY, activate
from wf.compose.schema import compose_schema
from wf.module_validation import (ADDS_KEYS, DECLARATION_KEYS, ModuleValidationError,
                                  validate_modules)
from wf.verbs.main import main
from wf.verbs.move_modules import COUNTERS, MOVE_PRINTS

CATALOG = load_blocks(ROOT)
DECLARED = {block.data['name']: block.data for block in CATALOG.by_label('yaml wf-module')}
SEED = {'modules': [], 'areas': ['WF'], 'merge_method': 'squash', 'project': None}


def catalog_of(*modules):
    """只含 wf-enums 與給定宣告的 Catalog；值域仍取自 repo 的 core/enums.md（唯一居所）。"""
    enums, = CATALOG.by_label('json wf-enums')
    blocks = [enums] + [Block('yaml wf-module', data, json.dumps(data, ensure_ascii=False),
                              Source('module', f"modules/{data.get('name', '?')}/module.md",
                                     '0 · 宣告區塊'))
                        for data in modules]
    return Catalog(blocks, {})


def declaration(**changes):
    """以 escalation 的真宣告為底，逐鍵變形；⛔ 不重打九鍵字面。"""
    base = json.loads(json.dumps(DECLARED['escalation']))
    for key, value in changes.items():
        if value is None:
            base.pop(key, None)
        else:
            base[key] = value
    return base


# ── §1 宣告的封閉驗證 ──────────────────────────────────────────────────────────

def test_repo_declarations_and_config_are_clean():
    """正控：repo 現況的 11 份宣告與本 repo 的 `.wf/modules.json` 零錯誤。"""
    config = json.loads((ROOT / '.wf/modules.json').read_text(encoding='utf-8'))
    report = validate_modules(CATALOG, {**SEED, **config})
    assert report.ok, report.lines
    assert set(report.declarations) == set(DECLARED)
    print('MODULE_VALIDATION_CLEAN', len(report.declarations), 'declarations')


@pytest.mark.parametrize('case,changes,needle', [
    ('unknown_top_key', {'bogus': 1}, '未知頂層鍵 bogus'),
    ('missing_scope', {'scope': None}, '缺必填鍵 scope'),
    ('missing_maturity', {'maturity': None}, '缺必填鍵 maturity'),
    ('missing_fact_source', {'fact_source': None}, '缺必填鍵 fact_source'),
    ('scope_out_of_domain', {'scope': 'global'}, "scope 值 'global' 不在值域"),
    ('maturity_out_of_domain', {'maturity': 'beta'}, "maturity 值 'beta' 不在值域"),
    ('unknown_adds_subkey', {'adds': {'ghost': []}}, 'adds 未知子鍵 ghost'),
    ('unknown_enable_kind', {'enable_if': {'kind': 'vibes'}}, "enable_if.kind 'vibes' 不在已實作 kind 封閉集"),
    ('params_seed_is_container', {'params': {'escalate_after': [3]}}, 'params.escalate_after 種子型別 list'),
    ('params_seed_is_null', {'params': {'escalate_after': None}}, 'params.escalate_after 種子型別 NoneType'),
])
def test_each_declaration_defect_is_rejected_with_repair_information(case, changes, needle):
    report = validate_modules(catalog_of(declaration(**changes)), dict(SEED))
    assert not report.ok, case
    hits = [line for line in report.lines if needle in line]
    assert hits, (case, report.lines)
    assert all(line.startswith('escalation:') for line in hits), hits  # 逐條帶模組名
    print('DECLARATION_REJECT', case, hits)


def test_declaration_key_sets_are_closed_and_match_the_repo():
    """封閉集合的基數與內容：九個頂層鍵、九個 adds 子鍵；repo 的 11 份宣告不得越界。"""
    assert len(DECLARATION_KEYS) == 9 and len(ADDS_KEYS) == 9
    for name, module in DECLARED.items():
        assert set(module) == set(DECLARATION_KEYS), name
        assert set(module['adds']) <= set(ADDS_KEYS), name
        assert module['enable_if']['kind'] in KINDS, name
    print('DECLARATION_KEYS', list(DECLARATION_KEYS))
    print('ADDS_KEYS', list(ADDS_KEYS))


# ── §4 `.wf/modules.json` 的 modules[] 封閉驗證 ───────────────────────────────

@pytest.mark.parametrize('case,entries,needle', [
    ('unknown_module', [{'name': 'ghost'}], "modules[0] 'ghost': 未知模組名"),
    ('duplicate_module', [{'name': 'escalation'}, {'name': 'escalation'}],
     "modules[1] 'escalation': 重複模組名"),
    ('unknown_param_key', [{'name': 'escalation', 'params': {'bogus': 99}}],
     '未知 params 鍵 bogus'),
    ('param_type_mismatch', [{'name': 'escalation', 'params': {'escalate_after': '3'}}],
     'params.escalate_after 型別 string 不符宣告種子；期望 integer'),
    ('param_bool_is_not_integer', [{'name': 'escalation', 'params': {'escalate_after': True}}],
     'params.escalate_after 型別 boolean 不符宣告種子；期望 integer'),
])
def test_each_project_config_defect_is_rejected(case, entries, needle):
    report = validate_modules(CATALOG, {**SEED, 'modules': entries})
    assert not report.ok, case
    assert any(needle in line for line in report.lines), (case, report.lines)
    assert all(line.startswith('.wf/modules.json ') for line in report.lines), report.lines
    print('CONFIG_REJECT', case, report.lines)


@pytest.mark.parametrize('key', ['areas', 'merge_method', 'project', 'rules', 'remote'])
def test_non_modules_config_keys_stay_out_of_scope(key):
    """射程外的五個鍵：值怎麼放都不改變本邊界的結果（驗證行為仍歸 project_config.py）。"""
    config = {**SEED, key: {'deliberately': 'odd'}}
    assert validate_modules(CATALOG, config).ok, key
    print('CONFIG_OUT_OF_SCOPE', key)


def test_both_sides_aggregate_in_one_run_and_nothing_stops_at_the_first_error():
    """兩側錯誤同一次執行全部收齊：宣告 3 條 ＋ `.wf/modules.json` 3 條，逐條各自帶修正資訊。"""
    bad = declaration(bogus=1, scope='global', maturity='beta')
    entries = [{'name': 'ghost'}, {'name': 'escalation'}, {'name': 'escalation'}]
    report = validate_modules(catalog_of(bad), {**SEED, 'modules': entries})
    declaration_lines = [line for line in report.lines if line.startswith('escalation:')]
    config_lines = [line for line in report.lines if line.startswith('.wf/modules.json ')]
    assert len(declaration_lines) == 3, declaration_lines
    assert len(config_lines) == 2, config_lines  # ghost 未知名、第二個 escalation 重複
    with pytest.raises(ModuleValidationError) as caught:
        report.raise_for_status()
    assert caught.value.lines == list(report.lines)
    print('AGGREGATED', len(report.lines), report.lines)


# ── §5 ready 的宣告 ↔ hook 雙向核對 ──────────────────────────────────────────

def test_ready_module_missing_implementation_fails():
    bad = declaration(adds={**DECLARED['escalation']['adds'],
                            'counters': ['escalation_count', 'ghost_count'],
                            'move_prints': ['escalation_threshold', 'ghost_print']})
    report = validate_modules(catalog_of(bad, DECLARED['resource-lock'], DECLARED['initiative']),
                              dict(SEED))
    assert not report.ok
    assert any('adds.counters 的 ghost_count' in line and '缺實作' in line for line in report.lines)
    assert any('adds.move_prints 的 ghost_print' in line and '缺實作' in line for line in report.lines)
    print('HOOK_MISSING_IMPLEMENTATION', report.lines)


def test_non_ready_module_missing_implementation_is_not_a_failure():
    """負控：同一份缺實作宣告改成 experimental ⇒ 不構成失敗（非 ready ⛔ 不進自動能力組合）。"""
    adds = {**DECLARED['escalation']['adds'], 'counters': ['escalation_count', 'ghost_count'],
            'move_prints': ['escalation_threshold', 'ghost_print']}
    ready = validate_modules(catalog_of(declaration(adds=adds), DECLARED['resource-lock'],
                                        DECLARED['initiative']), dict(SEED))
    lenient = validate_modules(catalog_of(declaration(adds=adds, maturity='experimental'),
                                          DECLARED['resource-lock'], DECLARED['initiative']),
                               dict(SEED))
    assert not ready.ok and [line for line in lenient.lines if '缺實作' in line] == []
    print('HOOK_NON_READY_TOLERATED', lenient.lines)


def test_registry_implementation_without_any_declaration_fails():
    """反方向：registry 有實作而無任何宣告 ⇒ 明確失敗。母體＝真 registry 的鍵。"""
    report = validate_modules(catalog_of(DECLARED['escalation']), dict(SEED))
    orphans = (set(MOVE_PRINTS) | set(COUNTERS)) - {'escalation_count', 'escalation_threshold'}
    assert orphans, '負控失效：escalation 以外的 registry 鍵不存在'
    for identifier in orphans:
        assert any(identifier in line and '有實作而無任何宣告' in line for line in report.lines), identifier
    print('HOOK_ORPHAN_IMPLEMENTATION', sorted(orphans), report.lines)


def test_registry_import_error_is_an_explicit_failure(monkeypatch):
    monkeypatch.setitem(sys.modules, 'wf.verbs.move_modules', None)
    report = validate_modules(CATALOG, dict(SEED))
    assert not report.ok
    assert any('載入 production registry 失敗（ImportError' in line for line in report.lines), report.lines
    print('HOOK_IMPORT_ERROR', report.lines)


# ── 成熟度四值 × 貢獻矩陣 ────────────────────────────────────────────────────

def test_four_maturity_values_and_only_ready_has_automatic_capability():
    """四值都是合法宣告（`adds.fields` 的結構合法性容器不分成熟度），但自動能力只由 ready 貢獻。"""
    enums, = CATALOG.by_label('json wf-enums')
    values = enums.data['module_maturity']['enum']
    assert values == ['ready', 'manual', 'experimental', 'unavailable']
    adds = {**DECLARED['escalation']['adds'], 'counters': [], 'move_prints': []}
    for value in values:
        module = declaration(maturity=value, adds=adds)
        report = validate_modules(catalog_of(module), dict(SEED))
        assert [line for line in report.lines if line.startswith('escalation:')] == [], (value, report.lines)
        result = activate([module], modules_list=['escalation'])
        assert [item['name'] for item in result.enabled] == ['escalation'], value
        assert result.names == (['escalation'] if value == READY else []), value
        # 結構合法性容器：模組欄的型別住 core/card-schema.md §1 (b)，⛔ 不隨成熟度變
        assert compose_schema(CATALOG, 'wf-card')['properties'].keys() >= set(adds['fields']), value
        print('MATURITY', value, 'enabled=1 capable=' + str(len(result.names)))


def test_experimental_adds_no_production_switch():
    """`experimental` ⛔ 不新增任何 production 開關：CLI 原始碼與 CI 內不得出現據以放行的字面。"""
    sources = [path for path in sorted((ROOT / 'cli/src/wf').rglob('*.py'))]
    hits = [str(path.relative_to(ROOT)) for path in sources
            if 'experimental' in path.read_text(encoding='utf-8')]
    assert hits == [], hits
    env_hits = [str(path.relative_to(ROOT)) for path in sources
                if 'environ' in path.read_text(encoding='utf-8')
                and path.name != 'main.py']  # main.py 只讀 GH_REPO，⛔ 不是模組開關
    assert env_hits == [], env_hits
    print('EXPERIMENTAL_NO_PRODUCTION_SWITCH', len(sources), 'files scanned')


# ── fail-closed 接線：rc≠0、stdout 逐條、零遠端寫入 ──────────────────────────

def adopted(tmp_path, config, name='adopted'):
    """規則齊全、`.wf/modules.json` 由測試給定的 project root（只連規則目錄，⛔ 不動 repo）。"""
    target = tmp_path / name
    target.mkdir()
    for part in ('core', 'roles', 'stages', 'modules'):
        (target / part).symlink_to(ROOT / part, target_is_directory=True)
    (target / '.wf').mkdir()
    (target / '.wf/modules.json').write_text(json.dumps(config, ensure_ascii=False), encoding='utf-8')
    return target


BAD_CONFIG = {'modules': [{'name': 'ghost'}, {'name': 'escalation', 'params': {'escalate_after': '3'}}],
              'areas': ['WF'], 'project': None}


@pytest.mark.parametrize('verb,argv', [
    ('open', ['10']), ('move', ['WF-001', '--to', '待辦']),
    ('edit', ['WF-001', '--set', 'feature="a"']), ('notes', ['WF-001']),
    ('brief', ['WF-001', '--for', 'executor']),
    ('review', ['WF-001', '--file', 'r.json', '--role', 'executor']),
    ('snapshot', ['--out', 'o']),
])
def test_invalid_config_refuses_every_verb_with_zero_remote_calls(tmp_path, capsys, verb, argv):
    """既有專案的無效 `.wf/modules.json`：七個動詞一律 rc=1、stdout 逐條、對 GitHub 與 Project
    零呼叫（含零讀取 ⇒ 必然零寫入）。"""
    root = adopted(tmp_path, BAD_CONFIG, name=f'bad-{verb}')
    client = FakeGhClient()
    assert main([verb, *argv], client=client, root=root, env={}) == 1
    out = capsys.readouterr()
    lines = [line for line in out.out.splitlines() if line.startswith('模組宣告或設定不可用・')]
    assert len(lines) == 2, out.out
    assert any("'ghost': 未知模組名" in line for line in lines), lines
    assert any('params.escalate_after 型別 string 不符宣告種子' in line for line in lines), lines
    assert client.calls == [], client.calls
    print('FAIL_CLOSED', verb, lines)


def test_valid_config_reaches_the_verb(tmp_path, monkeypatch):
    """負控：同一路徑、同一 client，設定合法時動詞確實被呼叫到（證明上一條不是恆假）。"""
    from wf.verbs import notes as notes_verb
    root = adopted(tmp_path, {'modules': [{'name': 'escalation'}], 'areas': ['WF'], 'project': None},
                   name='good')
    calls = []
    monkeypatch.setattr(notes_verb, 'run', lambda argv, **rest: calls.append(argv) or 7)
    client = FakeGhClient()
    assert main(['notes', 'WF-001'], client=client, root=root, env={}) == 7
    assert calls == [['WF-001']] and client.calls != []
    print('FAIL_CLOSED_NEGATIVE_CONTROL', calls, [name for name, _ in client.calls])


def test_no_flag_or_environment_variable_lets_an_invalid_config_through(tmp_path, capsys):
    """⛔ 不以旗標或環境變數放行：三個全域旗標與整份環境都試過，仍是 rc=1。"""
    root = adopted(tmp_path, BAD_CONFIG, name='no-bypass')
    for extra_env in ({}, {'WF_SKIP_MODULE_VALIDATION': '1'}, {'WF_ALLOW_UNKNOWN_MODULES': '1'},
                      {'GH_REPO': 'ruan6047/ai-workflow'}):
        assert main(['notes', 'WF-001'], client=FakeGhClient(), root=root, env=extra_env) == 1
    for flag in ('--project-root', '--rules-root'):
        assert main([flag, str(root), 'notes', 'WF-001'], client=FakeGhClient(), root=root, env={}) == 1
    capsys.readouterr()
    print('NO_BYPASS flags=--project-root,--rules-root env=3 variants')


# ── 結構不變式：取得啟用集合只經單一入口 ────────────────────────────────────

def test_only_compose_enable_references_is_enabled():
    """core/modules.md §2：`cli/src/wf` 內除了 compose/enable.py 自身，沒有第二處引用 `is_enabled`
    ⇒ 動詞層⛔ 不自行組合 modules_list 與 predicate。負控＝把 enable.py 自己排除後母體仍非空。"""
    home = ROOT / 'cli/src/wf/compose/enable.py'
    offenders = []
    for path in sorted((ROOT / 'cli/src/wf').rglob('*.py')):
        if path == home:
            continue
        tree = ast.parse(path.read_text(encoding='utf-8'))
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        names |= {alias.name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
                  for alias in node.names}
        if 'is_enabled' in names:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == [], offenders
    assert 'is_enabled' in ast.dump(ast.parse(home.read_text(encoding='utf-8')))  # 負控：偵測器有效
    print('SINGLE_ACTIVATION_ENTRY scanned', len(list((ROOT / 'cli/src/wf').rglob('*.py'))), 'files')


def test_ready_is_the_only_capable_maturity_literal():
    assert READY == 'ready'
    enums, = CATALOG.by_label('json wf-enums')
    assert READY in enums.data['module_maturity']['enum']
