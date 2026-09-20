"""WF-015：manifest 的項鍵集合、所有權、單一 `path` 文法、`source_commit`、結構宣告的缺陷代號、
`pin` 彙整規則。消費 core/adopt.md §2／§1（版本值唯一居所）。

合成 consumer 樹＝`test_adopt_gitlink.py` 的 `adopted_consumer`（canonical install mode：真 submodule，
`core/adopt.md` §0）。manifest 的鍵集合、所有權分類與應安裝集合由 `wf.verbs._adopt` `import` 取得、
⛔ 不重打（F-執行者-04）；§2 的宣告則由解析 `core/adopt.md` 取得，兩側比對相等才成立。
所有 GitHub 操作走 `cli/tests/fakes.py` 替身；⛔ 不碰網路。
"""
import hashlib
import json
from pathlib import Path
import re
import tomllib

import pytest

from wf.gh.writes import MUTATIONS
from wf.verbs import _adopt
from wf.verbs.main import main
from .fakes import FakeGhClient
from .test_adopt_gitlink import RULES_PATH, adopted_consumer, framework_tree
from .test_adoption_contract import (adopt_section, manifest_defects, reconciliation_sources,
                                     smoke_sources)
from .test_compose_schema import ROOT
from .test_context_roots import RULE_DIRS, git, git_env

VERSION_DECLARATION = re.compile(r'^\s*version\s*=', re.M)
BACKTICKED = re.compile(r'`([a-z_]+)`')
# 掃描面內可能的落地物＝資產表的目標路徑集合（`import` 取得，⛔ 不逐檔重打）。**控制檔⛔ 不在內**：
# 方案 A 下它⛔ 不自登記，其寫入權限來自 §2 的控制檔具名宣告、⛔ 非來自任何登記項。
CANDIDATES = _adopt.INSTALL_SET


def tree_digests(root):
    """全樹 (路徑, 內容摘要)；明示排除 `.git/`（`core/adopt.md` §0 逐字）。⛔ 不比對 mtime。"""
    root = Path(root)
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob('*'))
            if path.is_file() and '.git' not in path.relative_to(root).parts}


def run_step(consumer, step, client=None):
    client = FakeGhClient() if client is None else client
    rc = main(['--project-root', str(consumer), 'snapshot', '--adopt', step],
              client=client, root=None, env={})
    return rc, client


def manifest_of(consumer):
    return json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))


def write_manifest_file(consumer, value):
    path = consumer / _adopt.MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def declared_asset_keys():
    """`core/adopt.md` §2 的「`assets` 每項恰四鍵」條目；⛔ 不重打鍵名。"""
    _, body = adopt_section(None, '2')
    clause, = [line for line in body.splitlines() if line.startswith('- `assets` 每項恰')]
    return tuple(BACKTICKED.findall(clause.split('：', 1)[1].split('。')[0]))


def consumer_owned(consumer):
    """三個 consumer 自有檔，其中一個與某 framework-managed 路徑同目錄。"""
    files = {'.github/scripts/mine.py': '# 採用專案自己的腳本\n',
             'src/app.py': 'print("hi")\n', 'README.md': '# consumer\n'}
    for relative, text in files.items():
        (consumer / relative).parent.mkdir(parents=True, exist_ok=True)
        (consumer / relative).write_text(text, encoding='utf-8')
    return files


def rows_of(out, prefix):
    rows = {}
    for line in out.splitlines():
        if line.startswith(prefix + '・'):
            _, name, status, reason = line.split('・', 3)
            rows[name] = (status, reason)
    return rows


@pytest.fixture
def env(tmp_path):
    return git_env(tmp_path)


# ── A4：落地物與 manifest 項雙向對應、每項四鍵、`path` 兩兩相異且文法歸類唯一 ─────────
def test_every_landed_asset_has_exactly_one_four_key_entry(tmp_path, env, capsys):
    consumer, _, _, installed, _ = adopted_consumer(tmp_path, env)
    consumer_owned(consumer)
    rc, client = run_step(consumer, 'install')
    out = capsys.readouterr().out
    assert rc == 0, out
    manifest = manifest_of(consumer)
    print('MANIFEST', json.dumps(manifest, ensure_ascii=False, indent=2))
    keys = declared_asset_keys()
    assert len(keys) == 4 and {'path', 'ownership'} <= set(keys), keys
    assert keys == _adopt.ASSET_KEYS, (keys, _adopt.ASSET_KEYS)
    managed = [e for e in manifest['assets'] if e['ownership'] == _adopt.OWNERSHIPS[0]]
    landed = {path for path in CANDIDATES if _adopt.asset_digest(consumer, path) is not None}
    assert landed, CANDIDATES                                  # 空集合⛔ 不滿足本條
    assert {e['path'] for e in managed} == landed, sorted({e['path'] for e in managed} ^ landed)
    # 方案 A：控制檔⛔ 不出現在任何 `assets` 項的 `path`（命中即結構宣告的 `control-path` 列）
    assert not ({e['path'] for e in manifest['assets']} & set(_adopt.CONTROL_SET)), manifest['assets']
    assert (consumer / _adopt.MANIFEST_PATH).is_file()          # 它仍被生成，只是⛔ 不自登記
    for entry in manifest['assets']:
        assert tuple(entry) == keys, entry                     # 每項恰四鍵、順序固定
        assert entry['ownership'] in _adopt.OWNERSHIPS, entry
    paths = [e['path'] for e in manifest['assets']]
    assert len(set(paths)) == len(paths), paths                # `path` 兩兩相異
    # `path` 只有整檔一種文法：CLI 新產生的登記項一律⛔ 不含 `#`（片段文法已隨本卡撤銷）
    assert all('#' not in p for p in paths), paths
    assert manifest['source_commit'] == installed and len(installed) == 40
    assert [call for call in client.calls if call[0] in MUTATIONS] == [], client.calls
    print('LANDED', sorted(landed), 'paths', sorted(paths))


# ── A5：install 對未登記的位元組零影響 ────────────────────────────────────────────
def test_install_touches_no_unregistered_byte(tmp_path, env, capsys):
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='a5-plain')
    consumer_owned(consumer)
    before = tree_digests(consumer)
    assert run_step(consumer, 'install')[0] == 0
    capsys.readouterr()
    after = tree_digests(consumer)
    registered = {e['path'] for e in manifest_of(consumer)['assets']}
    changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
    assert changed, 'install 什麼都沒動＝本條零資訊'
    # 零影響的宣告面＝**兩個集合的聯集**（§2）：資產表的目標路徑集合＋控制檔集合（基數恰 1）。
    declared = registered | set(_adopt.CONTROL_SET)
    assert changed <= declared, sorted(changed - declared)
    for path in set(before) - declared:
        assert before[path] == after.get(path), path
    print('UNTOUCHED changed', sorted(changed), 'registered', sorted(registered))


def test_the_untouched_check_has_a_negative_control(tmp_path, env, capsys):
    """負控（必須會響）：樹上多一個未登記的路徑 ⇒ 不變式判準抓得到。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='a5-neg')
    before = tree_digests(consumer)
    run_step(consumer, 'install')
    capsys.readouterr()
    (consumer / 'stray.txt').write_text('未登記\n', encoding='utf-8')
    after = tree_digests(consumer)
    registered = {e['path'] for e in manifest_of(consumer)['assets']}
    changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
    assert not changed <= registered and 'stray.txt' in changed - registered
    print('NEGATIVE_CONTROL unregistered_path', sorted(changed - registered))


# ── A6：`source_commit` 是頂層單一事實 ────────────────────────────────────────────
def test_source_commit_is_a_single_top_level_fact(tmp_path, env, capsys):
    consumer, _, _, installed, _ = adopted_consumer(tmp_path, env, name='a6')
    assert run_step(consumer, 'install')[0] == 0
    capsys.readouterr()
    manifest = manifest_of(consumer)
    assert manifest['source_commit'] == installed and re.fullmatch(r'[0-9a-f]{40}', installed)
    assert all('source_commit' not in entry for entry in manifest['assets']), manifest['assets']
    plain = tmp_path / 'a6-vendor'
    plain.mkdir()
    framework_tree(plain / 'rules')
    (plain / '.wf').mkdir()
    (plain / '.wf/modules.json').write_text(json.dumps(
        {'modules': [], 'areas': ['APP'], 'project': None, 'rules': {'path': 'rules'}}), encoding='utf-8')
    git(plain, 'init', '-q', '-b', 'main', env=env)
    rc, _ = run_step(plain, 'install')
    capsys.readouterr()
    vendored = json.loads((plain / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    assert rc == 0 and 'source_commit' in vendored and vendored['source_commit'] is None
    assert all('source_commit' not in entry for entry in vendored['assets']), vendored['assets']
    print('A6 submodule', manifest['source_commit'], 'vendor', vendored['source_commit'])


# ── A7：可解析的 JSON ⛔ 不等於有效 manifest ──────────────────────────────────────
def broken_shapes(healthy):
    """六種結構異常輸入（`core/adopt.md` §2 的結構宣告必須使它們**全部**無效）。"""
    def mutate(fn):
        value = json.loads(json.dumps(healthy))
        fn(value)
        return value
    return {
        'assets_null_entry': mutate(lambda m: m.__setitem__('assets', [None])),
        'assets_not_a_list': mutate(lambda m: m.__setitem__('assets', {})),
        'entry_missing_key': mutate(lambda m: m['assets'][0].pop('pin')),
        'entry_extra_key': mutate(lambda m: m['assets'][0].update(extra='x')),
        'path_not_a_string': mutate(lambda m: m['assets'][0].update(path=7)),
        'top_missing_schema': mutate(lambda m: m.pop('schema')),
        # 第七種（方案 A）：某項的 `path` 等於控制檔路徑 ⇒ 結構宣告的 `control-path` 列命中
        'control_path_entry': mutate(lambda m: m['assets'].append(_adopt.asset_entry(
            _adopt.CONTROL_SET[0], _adopt.OWNERSHIPS[0], 'sha256:0', '0'))),
    }


def test_parseable_json_is_not_a_valid_manifest(tmp_path, env, capsys):
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='a7')
    for step in ('install', 'bootstrap'):
        assert run_step(consumer, step)[0] == 0
    capsys.readouterr()
    healthy = manifest_of(consumer)
    assert _adopt.defect_of(healthy) is None, healthy
    assert manifest_defects() == _adopt.DEFECTS, (manifest_defects(), _adopt.DEFECTS)
    recon, smoke = reconciliation_sources(), smoke_sources()
    consuming = ({name for name, ids in recon.items() if any(i.startswith('manifest.') for i in ids)}
                 | {name for name, ids in smoke.items() if 'manifest.file' in ids})
    assert consuming, (recon, smoke)
    baseline = {}
    for verb in ('preflight', 'smoke'):
        assert run_step(consumer, verb)[0] == 0
        baseline |= rows_of(capsys.readouterr().out, _adopt.PREFIX)
    reasons = set()
    for case, value in broken_shapes(healthy).items():
        write_manifest_file(consumer, value)
        assert _adopt.defect_of(value) in _adopt.DEFECTS, (case, _adopt.defect_of(value))
        assert _adopt.read_manifest(consumer)[0] is None, case
        seen = {}
        for verb in ('preflight', 'smoke', 'deactivate'):
            assert run_step(consumer, verb)[0] == 0, case      # ⛔ 無例外逸出、⛔ 不 raise
            out = capsys.readouterr().out
            seen |= rows_of(out, _adopt.PREFIX)
            reasons |= {line.split('・', 3)[3] for line in out.splitlines()
                        if line.startswith(f'{_adopt.STEP_PREFIX}・deactivate・{_adopt.MANIFEST_PATH}')}
            write_manifest_file(consumer, value)               # deactivate 之後放回同一份輸入
        # (d) 壞 manifest ⛔ 不得成為取得所有權的路徑：install 對每一個既有物走零寫入分支，
        # 且⛔ 不把任何既有路徑新登記為 `framework-managed`（否則重跑一次就把 consumer 的檔收編）。
        untouched = tree_digests(consumer)
        assert run_step(consumer, 'install')[0] == 0, case     # install 的沿用讀取也⛔ 不 raise
        capsys.readouterr()
        after_install = tree_digests(consumer)
        # 控制檔不可用是**前置條件**（§2）：install 對**全樹**零位元組寫入，含⛔ 不生成控制檔——
        # 壞 manifest ⛔ 不得成為取得所有權的路徑，也⛔ 不得成為覆寫採用者那份既有物的路徑。
        assert {p for p in set(untouched) | set(after_install)
                if untouched.get(p) != after_install.get(p)} == set(), case
        # ⛔ 不新登記任何既有路徑：全樹零寫入 ⇒ 控制檔位元組仍逐字等於本次注入的那一份輸入。
        assert manifest_of(consumer) == value, case
        write_manifest_file(consumer, value)
        for name in consuming:
            assert seen[name][0] != 'ok', (case, name, seen[name])
        for name, state in baseline.items():
            if name not in consuming:
                assert seen[name] == state, (case, name, seen[name], state)
        print('A7', case, 'defect', _adopt.defect_of(value), {n: seen[n][0] for n in sorted(seen)})
    assert len(reasons) == 1, reasons                           # 固定理由、⛔ 不隨輸入種類而異
    print('A7 fixed_reason', reasons, 'consuming', sorted(consuming))


def test_the_structural_declaration_rejects_every_listed_defect():
    """§2 結構宣告的每一個缺陷代號都要有一個會命中的輸入（宣告被寫弱即轉紅）。"""
    healthy = {'schema': _adopt.MANIFEST_SCHEMA, 'source_commit': None,
               'assets': [_adopt.asset_entry('a.txt', _adopt.OWNERSHIPS[0], 'sha256:0', '1')]}
    assert _adopt.defect_of(healthy) is None, healthy
    probes = {
        'top-keys': {**healthy, 'extra': 1},
        'schema-value': {**healthy, 'schema': 'nope'},
        'source-commit': {**healthy, 'source_commit': 'short'},
        'assets-type': {**healthy, 'assets': {}},
        'entry-type': {**healthy, 'assets': [None]},
        'entry-keys': {**healthy, 'assets': [{**healthy['assets'][0], 'x': 1}]},
        'entry-value': {**healthy, 'assets': [{**healthy['assets'][0], 'path': 7}]},
        'path-unique': {**healthy, 'assets': [healthy['assets'][0], dict(healthy['assets'][0])]},
        'control-path': {**healthy, 'assets': [_adopt.asset_entry(
            _adopt.CONTROL_SET[0], _adopt.OWNERSHIPS[0], 'sha256:0', '1')]},
    }
    assert tuple(probes) == manifest_defects(), (tuple(probes), manifest_defects())
    for tag, value in probes.items():
        assert _adopt.defect_of(value) == tag, (tag, _adopt.defect_of(value))
        print('DEFECT', tag, '->', _adopt.defect_of(value))


# ── 既有 consumer-owned 登記項⛔ 不覆寫、⛔ 不雙重登記（`core/adopt.md` §2 分支 ②）────
def test_install_never_overwrites_a_consumer_owned_entry(tmp_path, env, capsys):
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='a8')
    victim = _adopt.INSTALL_SET[0]
    (consumer / victim).parent.mkdir(parents=True, exist_ok=True)
    (consumer / victim).write_text('# consumer 自己的內容\n', encoding='utf-8')
    before = hashlib.sha256((consumer / victim).read_bytes()).hexdigest()
    entry = _adopt.asset_entry(victim, _adopt.OWNERSHIPS[1],
                               _adopt.digest_of((consumer / victim).read_bytes()), '0.0.0')
    write_manifest_file(consumer, {'schema': _adopt.MANIFEST_SCHEMA, 'source_commit': None,
                                   'assets': [entry]})
    rc, _ = run_step(consumer, 'install')
    out = capsys.readouterr().out
    assert rc == 0, out
    after = hashlib.sha256((consumer / victim).read_bytes()).hexdigest()
    assert after == before, (before, after)
    matched = [e for e in manifest_of(consumer)['assets'] if e['path'] == victim]
    assert len(matched) == 1, matched
    assert matched[0] == entry, (matched[0], entry)             # 登記項逐鍵不變
    explained = [line for line in out.splitlines()
                 if _adopt.PENDING_MARK in line and f'target={victim}' in line]
    assert len(explained) == 1, out                             # 印一項未完成項、⛔ 不重複
    print('KEPT_OWNED', victim, before[:12], explained)


# ── A15：`pin` 逐項等於版本值唯一居所 ────────────────────────────────────────────
def test_pin_equals_the_single_version_home(tmp_path, env, capsys):
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env, name='a15')
    run_step(consumer, 'install')
    capsys.readouterr()
    version = tomllib.loads((rules / _adopt.VERSION_HOME).read_text(encoding='utf-8'))['project']['version']
    assert isinstance(version, str) and version, version
    managed = _adopt.managed_entries(manifest_of(consumer))
    assert managed, manifest_of(consumer)
    assert {e['pin'] for e in managed} == {version}, ({e['pin'] for e in managed}, version)
    homes = [_adopt.VERSION_HOME] if VERSION_DECLARATION.search(
        (ROOT / _adopt.VERSION_HOME).read_text(encoding='utf-8')) else []
    for part in RULE_DIRS:
        for path in sorted((ROOT / part).rglob('*.md')):
            if VERSION_DECLARATION.search(path.read_text(encoding='utf-8')):
                homes.append(path.relative_to(ROOT).as_posix())
    assert homes == [_adopt.VERSION_HOME], homes
    print('A15 version', version, 'homes', homes, 'managed', len(managed))


def test_the_pin_comparison_is_effective(tmp_path, env, capsys):
    """負控（必須會響）：改掉 rules source 的版本值後，manifest 既有的 `pin` 就不再等於現行版本值。"""
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env, name='a15-neg')
    run_step(consumer, 'install')
    capsys.readouterr()
    before = {e['pin'] for e in manifest_of(consumer)['assets']}
    path = rules / _adopt.VERSION_HOME
    path.write_text(path.read_text(encoding='utf-8').replace(
        'version = "', 'version = "9.', 1), encoding='utf-8')
    now, _ = _adopt.framework_version(rules)
    assert now not in before, (now, before)
    print('NEGATIVE_CONTROL version_changed', sorted(before), '->', now)


@pytest.mark.parametrize('case,mutate,expected', [
    ('mixed_pin', lambda m: m['assets'][0].update(pin='0.0.1'), 'fail'),
    ('empty_pin', lambda m: m['assets'][0].update(pin=''), 'unknown'),
])
def test_pins_of_aggregation_rules(tmp_path, env, capsys, case, mutate, expected):
    """core/adopt.md §2 的彙整規則：基數 >1 ⇒ fail；`pin` 非非空字串 ⇒ unknown。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name=f'a15-{case}')
    run_step(consumer, 'install')
    capsys.readouterr()
    manifest = manifest_of(consumer)
    assert manifest['assets'][0]['ownership'] == _adopt.OWNERSHIPS[0], manifest['assets'][0]
    assert _adopt.pins_of(manifest)[1] == 'ok'
    mutate(manifest)
    value, status, reason = _adopt.pins_of(manifest)
    assert status == expected and value is None, (case, status, value)
    assert 'Error' not in reason and 'Traceback' not in reason, reason
    print('PINS_OF', case, status, reason)


def test_pins_of_without_a_manifest_is_unknown():
    assert _adopt.pins_of(None) == (None, 'unknown', _adopt.NO_MANIFEST)
    print('PINS_OF no_manifest unknown', _adopt.NO_MANIFEST)


def test_the_gitlink_path_is_the_declared_value(tmp_path, env, capsys):
    """`rules.path` 宣告值本身就是 gitlink 路徑（`core/adopt.md` §1）；⛔ 不重新推導。"""
    consumer, _, _, installed, _ = adopted_consumer(tmp_path, env, name='a15-path')
    config = json.loads((consumer / '.wf/modules.json').read_text(encoding='utf-8'))
    assert config['rules']['path'] == RULES_PATH
    run_step(consumer, 'install')
    capsys.readouterr()
    assert manifest_of(consumer)['source_commit'] == installed
    print('GITLINK_PATH', RULES_PATH, installed)
