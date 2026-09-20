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
from .test_adopt_fragments import MERGE_BASE
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


# ══════════════════════════════════════════════════════════════════════════════
# WF-019：五個 step 串成一條流程之後才成立的四條（A1／A4 住本檔，A2／A3 住
# `cli/tests/test_adopt_local_only.py`）。消費 core/adopt.md §0／§3、core/verbs.md §2。
#
# 刻意⛔ 不改本檔既有的 WF-015 測試函式（A21／A25–A28）：卡面 `non_scope` 逐字「⛔ 不重新驗收
# WF-015 已通過的 28 條」。四條一律新增函式，函式名前綴 `test_wf019_`，⛔ 不與既有函式同名
# ——同名會讓後定義者靜默覆寫先定義者、把 WF-015 的測試刪掉。
#
# 四條的 harness 一律用**子行程**、⛔ 不得經 `capsys`：`capsys.readouterr()` 會取走先前列印，
# WF-015 執行輪有 12 條 `evidence` 因此⛔ 不完整（`--capture=tee-sys` 試過⛔ 無效）。
# ⛔ 不得推出「既有函式的 `capsys` 取法是缺陷」——那屬 WF-015 的射程，本卡只登記。
# ══════════════════════════════════════════════════════════════════════════════
WF019 = 'WF019 '  # 子行程回報行的前綴：與被測 stdout 區隔，父行程逐行濾掉後即為原件

# 負控①（計數器層）直呼的兩個 mutation 原語與其最小引數。刻意取兩個**不同**的原語：
# 只呼一個時「序列長度 >0」與「序列長度 ==1」⛔ 不可分辨。
WF019_RING = {'post_comment': dict(number=1, first_line='wf:note', body='WF-019 A1 負控'),
              'update_card_body': dict(number=1, card_json={'card_id': 'WF-019'})}


def wf019_mutations(names):
    """A1 抽出述詞的唯一居所：從呼叫名序列濾出 mutation 原語。母體 `wf.gh.writes.MUTATIONS`
    `import` 取、⛔ 不重打。正控與兩層負控共用同一個述詞——各寫一份的話，負控證明的是**另一個**
    述詞會響，對正控的零值零資訊（F-共用-05／F-執行者-04）。"""
    return [name for name in names if name in MUTATIONS]


def wf019_subprocess_main():
    """隔離子行程側：以 `cli/tests/fakes.py` 的替身跑一次總入口，rc 與呼叫名序列以 `WF019 `
    前綴行落 fd 1。⛔ 不另起一套替身——另起一套測到的是替身自己的行為。"""
    import json as _json
    import sys as _sys
    from wf.verbs.main import main as _main
    from .fakes import FakeGhClient as _Fake

    spec = _json.loads(_sys.argv[1])

    class _Recorder(_Fake):
        # `repo` 為 None＝⛔ 無替身身分回退：`main.candidates()` 在本機 remote 與 `GH_REPO` 皆缺席時
        # 會取 `client.repo`，替身自帶 repo 會把「⛔ 無身分」的正控救活。`FakeGhClient` 本身⛔ 不改。
        repo = spec['fake_repo']

    client = _Recorder()
    rc = _main(spec['argv'], client=client, root=None, env=spec['env'])
    for primitive in spec['ring']:  # 負控①：同一顆替身、同一次執行直呼 mutation 原語
        getattr(client, primitive)(**WF019_RING[primitive])
    print(WF019 + _json.dumps({'rc': rc, 'calls': [name for name, _ in client.calls]},
                              ensure_ascii=False))


WF019_DRIVER = ('import sys\n'
                'sys.path.insert(0, {tests!r})\n'
                'sys.path.insert(0, {src!r})\n'
                'from tests.test_adopt_preflight import wf019_subprocess_main\n'
                'wf019_subprocess_main()\n')


def wf019_run(root, argv, *, environ=None, fake_repo=None, ring=()):
    """父行程側：起一個隔離子行程跑 `main(argv, client=<記錄替身>, root=None, env=…)`。
    回 `(rc, 被測 stdout 原件, 呼叫名序列)`；stderr 依卡面掃描面明示排除。"""
    spec = {'argv': list(argv), 'env': {} if environ is None else dict(environ),
            'fake_repo': fake_repo, 'ring': list(ring)}
    script = WF019_DRIVER.format(tests=str(ROOT / 'cli'), src=str(ROOT / 'cli/src'))
    done = subprocess.run([sys.executable, '-c', script, json.dumps(spec, ensure_ascii=False)],
                          capture_output=True, text=True, cwd=str(root),
                          env={**os.environ, 'PYTHONPATH': '', 'LANG': 'C.UTF-8'})
    lines = done.stdout.splitlines()
    reports = [json.loads(line[len(WF019):]) for line in lines if line.startswith(WF019)]
    assert len(reports) == 1, (done.returncode, done.stdout, done.stderr)
    out = '\n'.join(line for line in lines if not line.startswith(WF019))
    return reports[0]['rc'], out, reports[0]['calls']


def wf019_local_tree(tmp_path, env, name):
    """WF-019 四條共用的合成 consumer 樹（canonical install mode，`core/adopt.md` §0）：
    ⛔ 無 git remote。建樹後**就地實測** `git -C <tree> remote` 的 stdout 為空字串，
    ⛔ 不以「應該沒有 remote」交付（F-共用-01）。"""
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env, name=name)
    remotes = subprocess.run(['git', '-C', str(consumer), 'remote'], capture_output=True, text=True)
    assert remotes.stdout.strip() == '', remotes.stdout
    return consumer, rules


def wf019_prefix_rows(out):
    """一份 stdout 內的採用診斷列。前綴由 `_adopt.PREFIX` import 取、⛔ 不重打。"""
    return [line for line in out.splitlines() if line.startswith(_adopt.PREFIX + '・')]


# ── WF-019 A1：五個 step 的 mutation 原語呼叫序列長度皆為 0 ───────────────────────
def test_wf019_every_step_has_a_zero_length_mutation_sequence(tmp_path, env):
    """WF-019 A1。母體＝`wf.gh.writes.MUTATIONS` × `wf.verbs._adopt.STEPS`，兩者皆 `import` 取、
    ⛔ 不重打。harness＝子行程驅動器，⛔ 不經 `capsys`。
    明示排除（卡面掃描面逐字）：`snapshot` ⛔ 不帶 `--adopt` 的既有盤點路徑⛔ 不進本條母體。"""
    assert MUTATIONS, MUTATIONS  # 反空母體：`MUTATIONS` 為空時「序列長度為 0」由空集合恆滿足
    assert _adopt.STEPS, _adopt.STEPS
    consumer, _ = wf019_local_tree(tmp_path, env, 'wf019-a1')
    for step in _adopt.STEPS:  # 順序即 STEPS 的宣告序＝install → preflight → bootstrap → smoke → deactivate
        rc, out, calls = wf019_run(consumer, ['--project-root', str(consumer),
                                              'snapshot', '--adopt', step])
        mutations = wf019_mutations(calls)
        assert rc == 0 and mutations == [], (step, rc, calls, out)
        print('WF019_A1_STEP', step, 'rc', rc, 'calls', json.dumps(calls),
              'mutations', json.dumps(mutations))
    print('WF019_A1_POPULATION steps', json.dumps(list(_adopt.STEPS)), len(_adopt.STEPS),
          '| MUTATIONS', json.dumps(list(MUTATIONS)), len(MUTATIONS))


def test_wf019_a1_recorder_rings_end_to_end_in_the_subprocess(tmp_path, env):
    """WF-019 A1 負控①（計數器層，必須會響）：同一個子行程驅動器、同一顆替身，在 `main()` 之後
    直呼兩個 mutation 原語，父行程解析回的序列長度須 >0。⛔ 不做這一層時 A1 的零值可能只是
    「替身沒在記錄」或「回報路徑壞掉」，零資訊（F-共用-05）。"""
    consumer, _ = wf019_local_tree(tmp_path, env, 'wf019-a1-ring')
    ring = sorted(WF019_RING)
    rc, _, calls = wf019_run(consumer, ['--project-root', str(consumer),
                                        'snapshot', '--adopt', 'preflight'], ring=ring)
    mutations = wf019_mutations(calls)
    assert rc == 0 and sorted(mutations) == ring and len(mutations) == len(WF019_RING), (rc, calls)
    print('WF019_A1_NEG_COUNTER MUTATION_SEQ_LEN', len(mutations),
          'RINGS', True, json.dumps(mutations))


def test_wf019_a1_recorder_rings_on_a_verb_that_writes(card, catalog):
    """WF-019 A1 負控②（動詞層，必須會響）：同一族替身（`cli/tests/fakes.py` 的 `FakeGhClient`
    子類，⛔ 不另起一套）跑一個會寫的既有動詞，**經同一個抽出述詞** `wf019_mutations` 數出來的
    序列長度須 >0。本檔既有的 `test_the_recording_fake_rings_on_a_verb_that_writes` 是 WF-015 的
    同形函式；本條刻意另寫，理由＝要響的是 **A1 自己那個述詞**，⛔ 不是另一份等價的濾式。"""
    from wf.verbs import edit as edit_module
    from .test_write_flow import simulated
    client = simulated(card, catalog)
    assert isinstance(client, FakeGhClient)
    assert edit_module.edit(1, ['feature="WF-019 A1 負控②"'], client=client, catalog=catalog).rc == 0
    mutations = wf019_mutations([name for name, _ in client.calls])
    assert mutations, client.calls
    print('WF019_A1_NEG_VERB MUTATION_SEQ_LEN', len(mutations), json.dumps(mutations))


# ── WF-019 A4：七動詞 × 三個 bootstrap 失敗分支＝21 格，⛔ 不收窄 ─────────────────
# 三種變異做在**被審碼的拋棄式副本**上，⛔ 不動工作樹。三者的紅法須互⛔ 不相同
# （F-共用-06 逐字「三處變異印同一則訊息時判變異沒生效」）：
#   M1 三個分支的守門全拿掉      ⇒ 子句 (a)(b) 皆 21/21 紅
#   M2 只拿掉 ModuleValidationError 那一支（單點變異） ⇒ 皆 7/21 紅
#   M3 改一行既有的**⛔ 非採用診斷**輸出 ⇒ (a) 0/21、(b) 7/21 紅 ＝ 子句 (b) ⛔ 非冗餘的證據
WF019_GUARD = '        if adopt_requested:\n            _adopt.print_scope(scope)\n'
WF019_UNGUARDED = '        _adopt.print_scope(scope)\n'
WF019_MODULE_LINES = "        for line in exc.lines:\n            print(f'模組宣告或設定不可用・{line}')\n"
WF019_NON_ADOPTION_LINE = "print(f'模組宣告或設定不可用・{line}')"
WF019_MUTANTS = {
    # (說明, [(原文, 變異後, 須命中次數)])
    'M1': ('三個分支的 `if adopt_requested:` 守門全拿掉',
           [(WF019_GUARD, WF019_UNGUARDED, 3)]),
    'M2': ('只拿掉 ModuleValidationError 那一支的守門（單點變異）',
           [(WF019_MODULE_LINES + WF019_GUARD, WF019_MODULE_LINES + WF019_UNGUARDED, 1)]),
    'M3': ('改一行既有的⛔ 非採用診斷輸出（措辭改一字）',
           [(WF019_NON_ADOPTION_LINE,
             WF019_NON_ADOPTION_LINE.replace('不可用・', '不可用（M3）・'), 1)]),
}


def wf019_mutant_src(tmp_path, label):
    """把被審側 `cli/src` 複製成拋棄式副本並套用文字變異；⛔ 不動工作樹、⛔ 不 checkout。
    每一則變異都先斷言命中次數——命中 0 次卻全綠＝變異沒生效，判測具無效（F-共用-06）。"""
    target = tmp_path / f'wf019-mutant-{label}'
    shutil.copytree(ROOT / 'cli/src', target)
    path = target / 'wf/verbs/main.py'
    text = path.read_text(encoding='utf-8')
    for old, new, times in WF019_MUTANTS[label][1]:
        assert text.count(old) == times, (label, times, text.count(old))
        text = text.replace(old, new)
    path.write_text(text, encoding='utf-8')
    return target


def wf019_a4_cells(tmp_path, env, src, base_out=None):
    """21 格的一次窮舉：回 `(格清單, {格: stdout}, 每格的採用診斷列數)`。
    七個動詞由 `wf.verbs.main.DISPATCH` 的鍵枚舉（`import` 取、⛔ 不重打）；三個分支由
    `broken_trees` 的三棵樹枚舉。`base_out` 給定時另回每格是否與基線逐字相同。"""
    branches = broken_trees(tmp_path, env)
    cells, out, rows, identical = [], {}, {}, {}
    for branch, root in branches:
        for verb in DISPATCH:
            cell = (branch, verb)
            cells.append(cell)
            out[cell] = run_isolated(src, root, ['--project-root', str(root), verb])
            rows[cell] = wf019_prefix_rows(out[cell])
            if base_out is not None:
                identical[cell] = out[cell] == base_out[cell]
    assert len(cells) == len(branches) * len(DISPATCH), (len(cells), len(branches), len(DISPATCH))
    return cells, out, rows, identical


def test_wf019_adoption_rows_print_only_on_the_adopt_entry_over_21_cells(tmp_path, env):
    """WF-019 A4 正控。母體＝七動詞 × 三分支＝21 格，⛔ 不收窄。基線以
    `git archive 372fe7f3bcdea7d7681910938387fd36a730c369` 展開的拋棄式副本取（⛔ 不 checkout、
    ⛔ 不建 worktree、⛔ 不動 stash），兩側各在隔離子行程內載自己的 `cli/src`。stdout 原件比對，
    stderr 依卡面掃描面明示排除；⛔ 不經 `capsys`。

    **反空集合下界**：21 格中兩側 stdout 皆 0 位元組的格，子句 (b) 會被「空 == 空」滿足。
    下界＝`len(DISPATCH)`（一整個分支的格數；規劃輪實測非空的恰是 ModuleValidationError 那一個
    分支的 7 格）。⛔ 不重打 7：下界由同一次執行的母體算出。"""
    base = base_source(tmp_path)
    _, base_out, base_rows, _ = wf019_a4_cells(tmp_path, env, base)
    cells, now_out, now_rows, identical = wf019_a4_cells(tmp_path, env, ROOT / 'cli/src', base_out)
    nonempty = [cell for cell in cells if base_out[cell] != '']
    floor = len(DISPATCH)
    for cell in cells:
        print('WF019_A4_CELL', cell[0], cell[1], '| prefix_rows', len(now_rows[cell]),
              '| base_bytes', len(base_out[cell].encode('utf-8')),
              '| now_bytes', len(now_out[cell].encode('utf-8')),
              '| identical', identical[cell])
    print('WF019_A4 TOTAL', len(cells), 'IDENTICAL', sum(identical.values()),
          'BASE_STDOUT_NONEMPTY', len(nonempty), 'FLOOR', floor,
          '| MERGE_BASE', MERGE_BASE, '| VERBS', json.dumps(sorted(DISPATCH)))
    assert [cell for cell in cells if now_rows[cell]] == [], \
        [(cell, now_rows[cell]) for cell in cells if now_rows[cell]]          # 子句 (a)
    assert [cell for cell in cells if not identical[cell]] == [], \
        [(cell, base_out[cell], now_out[cell]) for cell in cells if not identical[cell]]  # 子句 (b)
    assert len(nonempty) >= floor, (len(nonempty), floor, nonempty)           # 反空集合下界
    assert base_rows == {cell: [] for cell in cells}, base_rows  # 基線側⛔ 無採用診斷列（該概念尚未存在）


def test_wf019_a4_extractor_rings_on_the_adopt_entry(tmp_path, env):
    """WF-019 A4 提取器負控（必須會響）：同一棵壞樹上跑 `snapshot --adopt preflight`，以**同一個**
    提取器數採用診斷列，行數須等於 `len(_adopt.item_names())` 且 >0。⛔ 不做這一層時，A4 正控
    量到的「0 行」可能只是提取器壞掉，前面的 21 個 0 全部零資訊（F-共用-05）。"""
    expected = len(_adopt.item_names())
    assert expected, _adopt.item_names()
    for branch, root in broken_trees(tmp_path, env):
        out = run_isolated(ROOT / 'cli/src', root,
                           ['--project-root', str(root), 'snapshot', '--adopt', 'preflight'])
        printed = wf019_prefix_rows(out)
        assert len(printed) == expected, (branch, printed)
        print('WF019_A4_NEG_EXTRACTOR', branch, 'adopt_entry_prefix_rows', len(printed),
              'expected', expected, 'rings', True)


def test_wf019_a4_three_mutants_ring_in_three_different_ways(tmp_path, env):
    """WF-019 A4 變異負控（三者都必須會響，且紅法互⛔ 不相同）。
    ⛔ 不做 M3 時，子句 (b) 抓到的紅格與子句 (a) 完全重合、(b) 零資訊。"""
    base = base_source(tmp_path)
    _, base_out, _, _ = wf019_a4_cells(tmp_path, env, base)
    red = {}
    for label in sorted(WF019_MUTANTS):
        cells, out, rows, identical = wf019_a4_cells(
            tmp_path, env, wf019_mutant_src(tmp_path, label), base_out)
        clause_a = tuple(sorted(cell for cell in cells if rows[cell]))
        clause_b = tuple(sorted(cell for cell in cells if not identical[cell]))
        red[label] = (clause_a, clause_b)
        print('WF019_A4_MUTANT', label, WF019_MUTANTS[label][0],
              '| clause_a_red_cells', f'{len(clause_a)}/{len(cells)}',
              '| clause_b_red_cells', f'{len(clause_b)}/{len(cells)}',
              '|', json.dumps({'a': [list(c) for c in clause_a], 'b': [list(c) for c in clause_b]},
                              ensure_ascii=False))
        assert clause_a or clause_b, (label, '變異⛔ 未轉紅 ⇒ 判準對該變異無分辨力')
    total, floor = len(DISPATCH) * 3, len(DISPATCH)
    assert len(red['M1'][0]) == len(red['M1'][1]) == total, red['M1']
    assert len(red['M2'][0]) == len(red['M2'][1]) == floor, red['M2']
    assert len(red['M3'][0]) == 0 and len(red['M3'][1]) == floor, red['M3']  # (b) ⛔ 非冗餘
    labels = sorted(WF019_MUTANTS)
    for left in range(len(labels)):
        for right in range(left + 1, len(labels)):
            assert red[labels[left]] != red[labels[right]], (labels[left], labels[right])
    print('WF019_A4_MUTANTS_PAIRWISE_DISTINCT', json.dumps(
        {label: [len(red[label][0]), len(red[label][1])] for label in labels}))


# ── WF-019 `verification`：四條的測試函式⛔ 不得經 `capsys` 取本條 stdout ─────────
# 四條與其測試函式的對應表；`(相對路徑, 函式名)`。本表是該對應的唯一居所。
WF019_ACCEPTANCE_TESTS = {
    'A1': ('cli/tests/test_adopt_preflight.py',
           'test_wf019_every_step_has_a_zero_length_mutation_sequence'),
    'A2': ('cli/tests/test_adopt_local_only.py',
           'test_wf019_local_steps_land_and_reverse_in_one_ordered_run'),
    'A3': ('cli/tests/test_adopt_local_only.py',
           'test_wf019_preflight_and_smoke_degrade_on_their_own_population'),
    'A4': ('cli/tests/test_adopt_preflight.py',
           'test_wf019_adoption_rows_print_only_on_the_adopt_entry_over_21_cells'),
}
WF019_CAPSYS_CONTROL = ('cli/tests/test_adopt_preflight.py', 'test_every_step_writes_nothing_remote')


def wf019_top_level_defs(relative, name):
    """以 AST 取該檔內**模組層**同名函式的參數清單；回 `[參數名清單, …]`（每個同名定義一份）。
    回多於一份＝後定義者會靜默覆寫先定義者，本身就是缺陷（測試會被刪掉而全綠）。"""
    tree = ast.parse((ROOT / relative).read_text(encoding='utf-8'))
    return [[arg.arg for arg in node.args.args] for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]


def test_wf019_the_four_acceptance_tests_never_take_stdout_through_capsys():
    """WF-019 `verification`：四條的測試函式**參數清單⛔ 不含 `capsys`**，以 AST 判、
    ⛔ 不以關鍵字 grep 為證據（F-執行者-01）。

    負控（必須會響）：對本檔既有的 WF-015 函式 `test_every_step_writes_nothing_remote`
    （確實帶 `capsys`）跑**同一個**判定，須判為「帶」——否則掃描器無效、四個 False 零資訊
    （F-共用-05）。另斷言每個名字在其檔內恰一個模組層定義：同名會靜默覆寫。"""
    control = wf019_top_level_defs(*WF019_CAPSYS_CONTROL)
    assert len(control) == 1 and 'capsys' in control[0], control
    print('WF019_CAPSYS_NEG_CONTROL', WF019_CAPSYS_CONTROL[1], json.dumps(control[0]), 'rings', True)
    for label, (relative, name) in sorted(WF019_ACCEPTANCE_TESTS.items()):
        found = wf019_top_level_defs(relative, name)
        assert len(found) == 1, (label, relative, name, len(found))
        assert 'capsys' not in found[0], (label, name, found[0])
        print('WF019_CAPSYS', label, relative, name, 'params', json.dumps(found[0]))
