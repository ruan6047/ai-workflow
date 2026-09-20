"""WF-015 A16／A17／A21／A25／A26／A27／A28：`snapshot --adopt preflight` 的四列對帳、逐列取源、
單一項名常數、三個 bootstrap 失敗分支的逐項降級與輸出收斂，以及理由字串⛔ 不外洩例外類別名。
消費 core/adopt.md §1（對帳表與取源 ID 欄）／§2（`pin` 彙整母體）／§3（preflight 七項）、
core/verbs.md §2、core/modules.md §5。

零遠端寫入以 `cli/tests/fakes.py` 既有的序列記錄能力驗（⛔ 不改該檔、⛔ 不另起一套替身）；mutation
原語集合由 `wf.gh.writes.MUTATIONS` 枚舉、⛔ 不重打。項名清單由 `wf.verbs._adopt.item_names()` 取得；
取源 → 消費列的映射由解析 `core/adopt.md` §1 的表格取得、⛔ 不重打。
掃描面＝合成 consumer 樹（`core/adopt.md` §0）。
"""
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

import pytest

from wf.gh.writes import MUTATIONS
from wf.verbs import _adopt, _adopt_reconcile
from wf.verbs.main import DISPATCH, main
from .fakes import FakeGhClient
from .test_adopt_assets import MERGE_BASE
from .test_adopt_gitlink import RULES_PATH, adopted_consumer, framework_tree
from .test_adoption_contract import reconciliation_sources
from .test_compose_schema import ROOT, card, catalog  # noqa: F401（card／catalog 是 fixture）
from .test_context_roots import git, git_env

FOUR = _adopt.RECONCILIATION_ITEMS


@pytest.fixture
def env(tmp_path):
    return git_env(tmp_path)


def rows_of(out):
    """把 `採用診斷・<項名>・<狀態>・<理由>` 逐行解析回 {項名: (狀態, 理由)}；⛔ 不解析別的行。"""
    rows = {}
    for line in out.splitlines():
        if line.startswith(_adopt.PREFIX + '・'):
            _, name, status, reason = line.split('・', 3)
            rows[name] = (status, reason)
    return rows


def names_of(out):
    return [line.split('・', 3)[1] for line in out.splitlines()
            if line.startswith(_adopt.PREFIX + '・')]


def preflight(consumer, capsys, client=None):
    client = FakeGhClient() if client is None else client
    rc = main(['--project-root', str(consumer), 'snapshot', '--adopt', 'preflight'],
              client=client, root=None, env={})
    return rc, capsys.readouterr().out, client


def installed_consumer(tmp_path, env, capsys, name):
    consumer, rules, bare, installed, other = adopted_consumer(tmp_path, env, name=name)
    assert main(['--project-root', str(consumer), 'snapshot', '--adopt', 'install'],
                client=FakeGhClient(), root=None, env={}) == 0
    capsys.readouterr()
    return consumer, rules, installed, other


def edit_manifest(consumer, mutate):
    path = consumer / _adopt.MANIFEST_PATH
    manifest = json.loads(path.read_text(encoding='utf-8'))
    mutate(manifest)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


# ── A21：五個 step 零遠端 mutation ────────────────────────────────────────────────
def test_every_step_writes_nothing_remote(tmp_path, env, capsys):
    consumer, _, _, _ = installed_consumer(tmp_path, env, capsys, 'a21')
    for step in _adopt.STEPS:
        client = FakeGhClient()
        rc = main(['--project-root', str(consumer), 'snapshot', '--adopt', step],
                  client=client, root=None, env={})
        capsys.readouterr()
        mutations = [call for call in client.calls if call[0] in MUTATIONS]
        assert rc == 0 and mutations == [], (step, rc, mutations)
        print('STEP', step, 'rc', rc, 'mutations', len(mutations))
    assert MUTATIONS, MUTATIONS


def test_the_recording_fake_rings_on_a_verb_that_writes(card, catalog):
    """負控（必須會響）：同一族替身跑一個會寫的既有動詞，mutation 序列長度必須 >0。
    ⛔ 不另起一套替身：`ProjectionFake` 是 `cli/tests/fakes.py` 的 `FakeGhClient` 子類。"""
    from wf.verbs import edit as edit_module
    from .test_write_flow import simulated
    client = simulated(card, catalog)
    assert isinstance(client, FakeGhClient)
    assert edit_module.edit(1, ['feature="採用負控"'], client=client, catalog=catalog).rc == 0
    mutations = [name for name, _ in client.calls if name in MUTATIONS]
    assert mutations, client.calls
    print('NEGATIVE_CONTROL edit --set mutations', mutations)


# ── A25：項名清單恰七項、來源是單一常數、⛔ 不含資料相依的模組列 ──────────────────
def row_name_list_homes(names):
    """以 AST 找「元素全是列名的字面序列」＝列名清單的居所；⛔ 以整串比對，⛔ 不以單字 grep
    （`roots`、`repository` 這些字在 `gh/` 另有別的用途，逐字 grep 會把它們誤記成第二個居所）。"""
    homes = []
    for path in sorted((ROOT / 'cli/src/wf').rglob('*.py')):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if not isinstance(node, (ast.Tuple, ast.List)):
                continue
            values = [e.value for e in node.elts
                      if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            if len(values) > 1 and set(values) <= set(names):
                homes.append(path.relative_to(ROOT).as_posix())
                break
    return sorted(set(homes))


def test_the_item_name_constant_is_the_single_home(tmp_path, env, capsys):
    consumer, _, _, _ = installed_consumer(tmp_path, env, capsys, 'a25')
    rc, out, _ = preflight(consumer, capsys)
    assert rc == 0, out
    printed = names_of(out)
    assert printed == list(_adopt.item_names()), (printed, list(_adopt.item_names()))
    assert len(printed) == 7 and printed == [*_adopt.STATIC_IDENTITY_ITEMS, *FOUR], printed
    homes = row_name_list_homes(printed)
    assert homes == ['cli/src/wf/verbs/_adopt_reconcile.py'], homes
    assert row_name_list_homes(['no-such-row-name', 'another']) == []   # 偵測器⛔ 非恆真
    module_rows = [name for name in printed if '：' in name or '模組' in name]
    assert module_rows == [], module_rows
    print('A25 names', printed, 'homes', homes)


def test_the_item_name_constant_has_a_negative_control(tmp_path, env, capsys, monkeypatch):
    """負控（必須會響）：兩條路徑（preflight 成功路徑與 bootstrap 失敗分支）都必須真的讀那一份常數、
    ⛔ 不是各自寫死。變異＝把任一項改名，兩側的輸出都必須跟著改名。
    刻意用改名而⛔ 不用刪除：`reconcile` 以位置消費該常數，刪除會讓被測函式自己 IndexError，
    那測到的是崩潰、⛔ 不是接線。"""
    consumer, _, _, _ = installed_consumer(tmp_path, env, capsys, 'a25-neg')
    _, healthy, _ = preflight(consumer, capsys)
    baseline = names_of(healthy)
    _, bad_config = broken_trees(tmp_path, env)[0]
    for constant, items in (('RECONCILIATION_ITEMS', FOUR),
                            ('STATIC_IDENTITY_ITEMS', _adopt.STATIC_IDENTITY_ITEMS)):
        for victim in items:
            renamed = tuple(f'{n}-變異' if n == victim else n for n in items)
            monkeypatch.setattr(_adopt_reconcile, constant, renamed)
            assert f'{victim}-變異' in _adopt.item_names(), (constant, victim)
            _, patched, _ = preflight(consumer, capsys)
            got = names_of(patched)
            assert got != baseline and f'{victim}-變異' in got and victim not in got, (victim, got)
            main(['--project-root', str(bad_config), 'snapshot', '--adopt', 'preflight'],
                 client=FakeGhClient(), root=None, env={})
            branch = names_of(capsys.readouterr().out)
            assert branch == got, (victim, branch, got)
            monkeypatch.undo()
            print('NEGATIVE_CONTROL renamed', constant, victim, '-> preflight', got, 'branch', branch)
    _, restored, _ = preflight(consumer, capsys)
    assert names_of(restored) == baseline, names_of(restored)


# ── A16：`framework-version` 左側的彙整母體只含 framework-managed 項 ───────────────
def test_version_aggregation_ignores_consumer_owned_pins(tmp_path, env, capsys):
    consumer, _, _, _ = installed_consumer(tmp_path, env, capsys, 'a16')
    assert main(['--project-root', str(consumer), 'snapshot', '--adopt', 'bootstrap'],
                client=FakeGhClient(), root=None, env={}) == 0
    capsys.readouterr()
    owned = _adopt.entries_of(json.loads((consumer / _adopt.MANIFEST_PATH).read_text(
        encoding='utf-8')), _adopt.OWNERSHIPS[1])
    assert owned, 'consumer-owned 項為空 ⇒ 本條零資訊'

    def bump(manifest, ownership, value):
        for entry in manifest['assets']:
            if entry['ownership'] == ownership:
                entry['pin'] = value
                return
        raise AssertionError(ownership)

    edit_manifest(consumer, lambda m: bump(m, _adopt.OWNERSHIPS[1], '9.9.9'))
    _, out, _ = preflight(consumer, capsys)
    assert rows_of(out)[FOUR[0]][0] == 'ok', rows_of(out)[FOUR[0]]
    print('A16 consumer_owned_pin_ignored', rows_of(out)[FOUR[0]])
    edit_manifest(consumer, lambda m: bump(m, _adopt.OWNERSHIPS[0], '9.9.9'))
    _, negative, _ = preflight(consumer, capsys)
    assert rows_of(negative)[FOUR[0]][0] == 'fail', rows_of(negative)[FOUR[0]]
    print('NEGATIVE_CONTROL framework_managed_pin', rows_of(negative)[FOUR[0]])


# ── A17：每一列恰為自己宣告的取源翻面 ─────────────────────────────────────────────
def set_index_gitlink(consumer, sha, env):
    git(consumer, 'update-index', '--cacheinfo', f'160000,{sha},{RULES_PATH}', env=env)


def break_manifest_pin(consumer, rules, installed, other, env):
    edit_manifest(consumer, lambda m: m['assets'][0].update(pin='9.9.9'))


def break_rules_version(consumer, rules, installed, other, env):
    path = Path(rules) / _adopt.VERSION_HOME
    path.write_text(path.read_text(encoding='utf-8').replace('version = "', 'version = "9.', 1),
                    encoding='utf-8')


def break_manifest_source_commit(consumer, rules, installed, other, env):
    edit_manifest(consumer, lambda m: m.update(source_commit='0' * 40))


def break_gitlink_index(consumer, rules, installed, other, env):
    set_index_gitlink(consumer, other, env)


def break_gitlink_head(consumer, rules, installed, other, env):
    """只動 HEAD 側：先把索引側改成 other 並 commit，再把索引側改回 installed。"""
    set_index_gitlink(consumer, other, env)
    git(consumer, 'commit', '-q', '-m', 'bump gitlink', env=env)
    set_index_gitlink(consumer, installed, env)


def break_submodule_checkout(consumer, rules, installed, other, env):
    git(rules, 'checkout', '-q', other, env=env)


MUTATORS = {'manifest.pin': break_manifest_pin, 'rules.version': break_rules_version,
            'manifest.source_commit': break_manifest_source_commit,
            'gitlink.index': break_gitlink_index, 'gitlink.head': break_gitlink_head,
            'submodule.checkout': break_submodule_checkout}


def test_the_source_id_vocabulary_is_closed_and_every_source_is_consumed():
    table = reconciliation_sources()
    assert set(table) == set(FOUR), sorted(set(table) ^ set(FOUR))
    vocabulary = {source for ids in table.values() for source in ids}
    assert vocabulary == set(MUTATORS), sorted(vocabulary ^ set(MUTATORS))
    for row, ids in table.items():
        assert len(ids) == 2, (row, ids)          # 左右兩側各自標示
    for source in vocabulary:
        assert [row for row, ids in table.items() if source in ids], source
    print('RECONCILIATION_SOURCES', table, 'vocabulary', sorted(vocabulary))


def test_each_row_flips_exactly_for_its_declared_sources(tmp_path, env, capsys):
    table = reconciliation_sources()
    healthy_tree, _, _, _ = installed_consumer(tmp_path, env, capsys, 'a17-ok')
    _, out, _ = preflight(healthy_tree, capsys)
    healthy = {item: rows_of(out)[item][0] for item in FOUR}
    assert healthy == {item: 'ok' for item in FOUR}, healthy
    for source, mutate in MUTATORS.items():
        consumer, rules, installed, other = installed_consumer(
            tmp_path, env, capsys, f'a17-{source.replace(".", "-")}')
        mutate(consumer, rules, installed, other, env)
        _, broken, _ = preflight(consumer, capsys)
        got = {item: rows_of(broken)[item][0] for item in FOUR}
        flipped = {item for item in FOUR if got[item] != healthy[item]}
        declared = {row for row, ids in table.items() if source in ids}
        assert flipped == declared, (source, sorted(flipped), sorted(declared), got)
        print('A17 source', source, 'flipped', sorted(flipped), 'declared', sorted(declared), got)


def test_one_unavailable_source_does_not_make_another_row_unknown(tmp_path, env, capsys):
    """A17 末句：某一列的取源不可得⛔ 不得使另一列由可得變 `unknown`。"""
    consumer, _, _, _ = installed_consumer(tmp_path, env, capsys, 'a17-unknown')
    _, out, _ = preflight(consumer, capsys)
    healthy = {item: rows_of(out)[item][0] for item in FOUR}
    edit_manifest(consumer, lambda m: m.update(source_commit=None))  # 只讓該取源不可得
    _, broken, _ = preflight(consumer, capsys)
    got = {item: rows_of(broken)[item][0] for item in FOUR}
    assert got[FOUR[1]] == 'unknown', got
    assert {i: got[i] for i in FOUR if i != FOUR[1]} == {i: healthy[i] for i in FOUR if i != FOUR[1]}
    print('A17 no_contagion', healthy, '->', got)


# ── A26：三個 bootstrap 失敗分支逐項降級、⛔ 不連坐 ──────────────────────────────
def broken_trees(tmp_path, env):
    """三種 bootstrap 失敗形狀，各回 (分支名, project_root)。"""
    bad_config = tmp_path / 'bad-config'
    (bad_config / '.wf').mkdir(parents=True, exist_ok=True)
    (bad_config / '.wf/modules.json').write_text('{壞', encoding='utf-8')
    no_core = tmp_path / 'no-core'
    (no_core / '.wf').mkdir(parents=True, exist_ok=True)
    (no_core / 'rules').mkdir(exist_ok=True)
    (no_core / '.wf/modules.json').write_text(json.dumps(
        {'modules': [], 'areas': ['APP'], 'project': None, 'rules': {'path': 'rules'}}), encoding='utf-8')
    bad_module = tmp_path / 'bad-module'
    if not bad_module.exists():
        bad_module.mkdir()
        framework_tree(bad_module)
    (bad_module / '.wf').mkdir(exist_ok=True)
    (bad_module / '.wf/modules.json').write_text(json.dumps(
        {'modules': [{'name': 'ghost'}], 'areas': ['APP'], 'project': None}), encoding='utf-8')
    return (('ProjectConfigError', bad_config), ('ContextError', no_core),
            ('ModuleValidationError', bad_module))


def branch_rows(root, capsys, client=None):
    rc = main(['--project-root', str(root), 'snapshot', '--adopt', 'preflight'],
              client=FakeGhClient() if client is None else client, root=None, env={})
    captured = capsys.readouterr()
    return rc, rows_of(captured.out), captured


def test_failure_branches_print_the_same_item_names(tmp_path, env, capsys):
    consumer, _, _, _ = installed_consumer(tmp_path, env, capsys, 'a26-names')
    _, healthy, _ = preflight(consumer, capsys)
    expected = names_of(healthy)
    assert expected == list(_adopt.item_names()), expected
    for branch, root in broken_trees(tmp_path, env):
        client = FakeGhClient()
        rc, rows, captured = branch_rows(root, capsys, client)
        assert rc == 1, (branch, rc)
        assert list(rows) == expected, (branch, list(rows))
        assert {status for status, _ in rows.values()} <= set(_adopt.STATUSES), (branch, rows)
        assert [call for call in client.calls if call[0] in MUTATIONS] == [], (branch, client.calls)
        if branch == 'ModuleValidationError':  # 既有的逐條 stdout ⛔ 不被改變、⛔ 不折疊
            module_lines = [line for line in captured.out.splitlines()
                            if line.startswith('模組宣告或設定不可用・')]
            assert module_lines and any("'ghost': 未知模組名" in line for line in module_lines), module_lines
            print('MODULE_STDOUT_UNCHANGED', module_lines)
        print('BRANCH', branch, {name: rows[name][0] for name in rows})


def test_failure_branches_degrade_per_item_not_wholesale(tmp_path, env, capsys):
    """機械下界三條：① ModuleValidationError 分支的 `roots` ⛔ 非 `unknown`；② 同分支上，樹有結構
    有效的 manifest 時 `framework-version` ⛔ 非 `unknown`、⛔ 無 manifest 時**應**為 `unknown`；
    ③ ProjectConfigError 分支上兩項**應**為 `unknown`。"""
    branches = dict(broken_trees(tmp_path, env))
    module_tree = branches['ModuleValidationError']
    assert not (module_tree / _adopt.MANIFEST_PATH).exists()
    _, no_manifest, _ = branch_rows(module_tree, capsys)
    assert no_manifest[_adopt.STATIC_IDENTITY_ITEMS[0]][0] != 'unknown', no_manifest
    assert no_manifest[FOUR[0]][0] == 'unknown', no_manifest
    print('A26 module_branch_without_manifest', {k: v[0] for k, v in no_manifest.items()})
    version, _ = _adopt.framework_version(_adopt.rules_of(module_tree))
    assert version, module_tree
    entry = _adopt.asset_entry('x.txt', _adopt.OWNERSHIPS[0], 'sha256:0', version)
    _adopt.write_manifest(module_tree, [entry], None, version)
    stored = json.loads((module_tree / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    assert _adopt.defect_of(stored) is None, stored
    _, with_manifest, _ = branch_rows(module_tree, capsys)
    assert with_manifest[_adopt.STATIC_IDENTITY_ITEMS[0]][0] != 'unknown', with_manifest
    assert with_manifest[FOUR[0]][0] != 'unknown', with_manifest
    print('A26 module_branch_with_manifest', {k: v[0] for k, v in with_manifest.items()})
    _, config_rows, _ = branch_rows(branches['ProjectConfigError'], capsys)
    assert config_rows[_adopt.STATIC_IDENTITY_ITEMS[0]][0] == 'unknown', config_rows
    assert config_rows[FOUR[0]][0] == 'unknown', config_rows
    print('A26 config_branch', {k: v[0] for k, v in config_rows.items()})


# ── A27：採用診斷列只在採用入口印，其餘輸出與合併基底逐行相同 ────────────────────
def base_source(tmp_path):
    """以 `git archive <合併基底> cli/src` 取出拋棄式副本；物件取不到時**失敗並印出原因**，⛔ 不 skip。"""
    target = tmp_path / 'base-src'
    if target.exists():
        return target / 'cli/src'
    target.mkdir()
    archive = tmp_path / 'base.tar'
    with archive.open('wb') as handle:
        done = subprocess.run(['git', '-C', str(ROOT), 'archive', MERGE_BASE, 'cli/src'],
                              stdout=handle, stderr=subprocess.PIPE)
    assert done.returncode == 0, (MERGE_BASE, done.stderr.decode())
    with tarfile.open(archive) as tar:
        tar.extractall(target, filter='data')
    return target / 'cli/src'


def run_isolated(src, root, argv):
    """在隔離子行程內以指定的 `cli/src` 跑一次總入口；回 stdout（stderr 明示排除）。"""
    script = ('import sys, json\n'
              'sys.path.insert(0, sys.argv[1])\n'
              'from wf.verbs.main import main\n'
              'rc = main(json.loads(sys.argv[2]), client=None, root=None, env={})\n'
              'print("RC", rc, file=sys.stderr)\n')
    done = subprocess.run([sys.executable, '-c', script, str(src), json.dumps(argv)],
                          capture_output=True, text=True, cwd=str(root),
                          env={**os.environ, 'PYTHONPATH': '', 'LANG': 'C.UTF-8'})
    return done.stdout


def test_adoption_rows_print_only_on_the_adopt_entry(tmp_path, env, capsys):
    base, measured = base_source(tmp_path), ROOT / 'cli/src'
    for branch, root in broken_trees(tmp_path, env):
        for verb in DISPATCH:
            argv = ['--project-root', str(root), verb]
            now = run_isolated(measured, root, argv)
            assert [line for line in now.splitlines()
                    if line.startswith(_adopt.PREFIX + '・')] == [], (branch, verb, now)
            assert now == run_isolated(base, root, argv), (branch, verb, now)
        print('A27', branch, 'verbs', len(DISPATCH), 'zero_adoption_rows_and_stdout_parity')
        adopt_out = run_isolated(measured, root, ['--project-root', str(root), 'snapshot',
                                                  '--adopt', 'preflight'])
        printed = [line for line in adopt_out.splitlines() if line.startswith(_adopt.PREFIX + '・')]
        assert len(printed) == len(_adopt.item_names()), (branch, printed)
        print('A27', branch, 'adopt_entry_rows', len(printed))


# ── A28：理由字串⛔ 不含例外類別名 ────────────────────────────────────────────────
def collect_reasons(tmp_path, env, capsys):
    """十種以上不可得形狀的全部理由字串（preflight、smoke 與三個失敗分支）。"""
    reasons = []

    def sweep(root):
        for step in ('preflight', 'smoke'):
            main(['--project-root', str(root), 'snapshot', '--adopt', step],
                 client=FakeGhClient(), root=None, env={})
            reasons.extend(reason for _, reason in rows_of(capsys.readouterr().out).values())

    sweep(installed_consumer(tmp_path, env, capsys, 'a28')[0])
    for source, mutate in MUTATORS.items():
        tree, rules, installed, other = installed_consumer(
            tmp_path, env, capsys, f'a28-{source.replace(".", "-")}')
        mutate(tree, rules, installed, other, env)
        sweep(tree)
    gone = installed_consumer(tmp_path, env, capsys, 'a28-nomanifest')[0]
    (gone / _adopt.MANIFEST_PATH).unlink()
    sweep(gone)
    for _, root in broken_trees(tmp_path, env):
        reasons.extend(reason for _, reason in branch_rows(root, capsys)[1].values())
    return reasons


def test_reasons_never_leak_an_exception_class_name(tmp_path, env, capsys):
    reasons = collect_reasons(tmp_path, env, capsys)
    assert len(set(reasons)) >= 10, sorted(set(reasons))
    for reason in reasons:
        assert 'Error' not in reason and 'Traceback' not in reason, reason
    print('A28 reasons', len(reasons), 'distinct', len(set(reasons)))
    injected = _adopt.render([_adopt.Row(_adopt.STATIC_IDENTITY_ITEMS[0], 'unknown',
                                         f'{type(RuntimeError()).__name__}: 壞了')])
    assert any('Error' in line.split('・', 3)[3] for line in injected), injected
    print('NEGATIVE_CONTROL leaked_reason', injected)


# ── 四列對帳的十一種形狀 ─────────────────────────────────────────────────────────
def test_reconciliation_rows_are_same_granularity(tmp_path, env, capsys):
    matrix = {}

    def record(name, consumer):
        _, out, _ = preflight(consumer, capsys)
        rows = rows_of(out)
        matrix[name] = {item: rows[item][0] for item in FOUR}
        for item in FOUR:
            assert 'Error' not in rows[item][1] and 'Traceback' not in rows[item][1], rows[item]
        print('SHAPE', name, matrix[name], {i: rows[i][1] for i in FOUR})

    consistent, rules, installed, other = installed_consumer(tmp_path, env, capsys, 'm1')
    record('consistent', consistent)

    same_version, rules2, _, other2 = installed_consumer(tmp_path, env, capsys, 'm2')
    git(rules2, 'checkout', '-q', other2, env=env)          # 同版本不同 SHA：索引與 HEAD 都改
    git(same_version, 'add', RULES_PATH, env=env)
    git(same_version, 'commit', '-q', '-m', 'bump submodule', env=env)
    record('same_version_different_sha', same_version)

    staged, rules3, _, other3 = installed_consumer(tmp_path, env, capsys, 'm3')
    git(rules3, 'checkout', '-q', other3, env=env)
    git(staged, 'add', RULES_PATH, env=env)                 # 只暫存未 commit
    record('staged_only', staged)

    dirty, rules4, _, other4 = installed_consumer(tmp_path, env, capsys, 'm4')
    git(rules4, 'checkout', '-q', other4, env=env)          # dirty 簽出：兩個 gitlink 側都看不見
    record('dirty_checkout', dirty)

    source, _, _, _ = installed_consumer(tmp_path, env, capsys, 'm5')
    fresh = tmp_path / 'm5-fresh'
    git(tmp_path, '-c', 'protocol.file.allow=always', 'clone', '-q', str(source), str(fresh), env=env)
    shutil.copytree(source / _adopt.MANIFEST_PATH.rsplit('/', 1)[0], fresh / '.wf/adopt')
    record('uninitialised', fresh)

    for name, mutate in (('mixed_pin', lambda m: m['assets'][0].update(pin='0.0.1')),
                         ('missing_pin', lambda m: m['assets'][0].pop('pin')),
                         ('no_source_commit', lambda m: m.pop('source_commit'))):
        tree, _, _, _ = installed_consumer(tmp_path, env, capsys, f'm-{name}')
        edit_manifest(tree, mutate)
        record(name, tree)

    gone, _, _, _ = installed_consumer(tmp_path, env, capsys, 'm-nomanifest')
    (gone / _adopt.MANIFEST_PATH).unlink()
    record('no_manifest', gone)

    for name, as_git in (('not_a_submodule', True), ('non_git_worktree', False)):
        plain = tmp_path / name
        plain.mkdir()
        framework_tree(plain / 'rules')
        (plain / '.wf').mkdir()
        (plain / '.wf/modules.json').write_text(json.dumps(
            {'modules': [], 'areas': ['APP'], 'project': None, 'rules': {'path': 'rules'}}),
            encoding='utf-8')
        if as_git:
            git(plain, 'init', '-q', '-b', 'main', env=env)
        assert main(['--project-root', str(plain), 'snapshot', '--adopt', 'install'],
                    client=FakeGhClient(), root=None, env={}) == 0
        capsys.readouterr()
        record(name, plain)

    assert len(matrix) == 11, sorted(matrix)
    assert matrix['consistent'] == {item: 'ok' for item in FOUR}
    # 同版本不同 SHA ⇒ 版本列 ok 而 commit 列 fail（只比版本值的做法會被打穿）
    assert matrix['same_version_different_sha'][FOUR[0]] == 'ok'
    assert matrix['same_version_different_sha'][FOUR[1]] == 'fail'
    assert matrix['staged_only'][FOUR[2]] == 'fail'
    assert matrix['dirty_checkout'][FOUR[3]] == 'fail'
    # 未初始化 ⇒ 簽出列必須 unknown（naive 讀法會讀到 superproject 自己的 HEAD）
    assert matrix['uninitialised'][FOUR[3]] == 'unknown'
    assert matrix['mixed_pin'][FOUR[0]] == 'fail' and matrix['missing_pin'][FOUR[0]] == 'unknown'
    assert matrix['no_source_commit'][FOUR[1]] == 'unknown'
    assert matrix['no_manifest'][FOUR[0]] == matrix['no_manifest'][FOUR[1]] == 'unknown'
    # vendor 複製形狀 ⇒ 三個 gitlink 列全 unknown，版本列仍可判
    for name in ('not_a_submodule', 'non_git_worktree'):
        assert [matrix[name][item] for item in FOUR[1:]] == ['unknown'] * 3, matrix[name]
        assert matrix[name][FOUR[0]] == 'ok', matrix[name]
    print('MATRIX', json.dumps(matrix, ensure_ascii=False, indent=2))


def test_the_pin_is_never_compared_against_a_gitlink_sha(tmp_path, env, capsys):
    """逐列印出兩個輸入，⛔ 不以關鍵字命中判——`framework-version` 的兩個輸入都不是 40 碼 SHA；
    `framework-commit`／`gitlink-*` 的兩個輸入都不是版本字串。"""
    consumer, rules, installed, _ = installed_consumer(tmp_path, env, capsys, 'gran')
    version, _ = _adopt.framework_version(rules)
    _, out, _ = preflight(consumer, capsys)
    rows = rows_of(out)
    assert version in rows[FOUR[0]][1] and installed not in rows[FOUR[0]][1], rows[FOUR[0]]
    for item in FOUR[1:]:
        assert installed in rows[item][1] and version not in rows[item][1], (item, rows[item])
    assert _adopt.pins_of(json.loads(
        (consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8')))[0] == version
    assert version != installed and len(installed) == 40
    print('GRANULARITY version', version, 'commit', installed,
          {item: rows[item][1] for item in FOUR})
