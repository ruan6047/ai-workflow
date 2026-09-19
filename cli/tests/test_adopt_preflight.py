"""WF-015 A7 與 A5 後半（四列對帳的十一種形狀狀態矩陣）。消費 core/adopt.md §1、core/verbs.md §2、
core/modules.md §5。

零遠端寫入以 `cli/tests/fakes.py` 既有的序列記錄能力驗（⛔ 不改該檔、⛔ 不另起一套替身）；mutation
原語集合由 `wf.gh.writes.MUTATIONS` 枚舉、⛔ 不重打。項名清單由 `wf.verbs._adopt.item_names()` 取得。
"""
import json
from pathlib import Path
import shutil

import pytest

from wf.gh.writes import MUTATIONS
from wf.verbs import _adopt
from wf.verbs.main import main
from .fakes import FakeGhClient
from .test_adopt_gitlink import RULES_PATH, adopted_consumer, framework_tree
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


# ── A7：五個 step 零遠端 mutation；preflight 逐項 ──────────────────────────────────
def test_every_step_writes_nothing_remote_and_preflight_is_itemised(tmp_path, env, capsys):
    consumer, _, _, _ = installed_consumer(tmp_path, env, capsys, 'a7')
    for step in _adopt.STEPS:
        client = FakeGhClient()
        rc = main(['--project-root', str(consumer), 'snapshot', '--adopt', step],
                  client=client, root=None, env={})
        out = capsys.readouterr().out
        mutations = [call for call in client.calls if call[0] in MUTATIONS]
        assert rc == 0 and mutations == [], (step, rc, mutations)
        print('STEP', step, 'rc', rc, 'mutations', len(mutations))
    rc, out, _ = preflight(consumer, capsys)
    rows = rows_of(out)
    assert list(rows) == list(_adopt.item_names()), (list(rows), list(_adopt.item_names()))
    assert all(status in _adopt.STATUSES for status, _ in rows.values()), rows
    assert len(rows) >= 3 + len(FOUR)
    for name, (status, reason) in rows.items():
        assert 'Error' not in reason and 'Traceback' not in reason, (name, reason)
        print('PREFLIGHT', name, status, reason)


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


def test_each_module_validation_line_gets_its_own_row(tmp_path, env, capsys):
    """A7 逐字「`ModuleValidation` 的每一條 `lines` 各有一列」；純計算層直接驅動（preflight 可達時
    該清單必為空——不空的話 bootstrap 早已 raise，見下一條的三個失敗分支）。"""
    consumer, rules, _, _ = installed_consumer(tmp_path, env, capsys, 'a7lines')
    config = json.loads((consumer / '.wf/modules.json').read_text(encoding='utf-8'))
    lines = ('ghost: 未知模組名', 'escalation: params.x 型別不符')
    rows = _adopt.preflight_rows(consumer, _adopt.rules_of(rules), config, module_lines=lines)
    names = [row.name for row in rows]
    assert names == list(_adopt.item_names(lines)), names
    assert [row.status for row in rows if row.name in lines] == ['fail', 'fail']
    print('MODULE_ROWS', [ (r.name, r.status) for r in rows if r.name in lines ])


# ── A7 追加（G1 取乙）：三個 bootstrap 失敗分支的項名集合與 preflight 逐字相等 ─────────
def broken_trees(tmp_path, env):
    """三種 bootstrap 失敗形狀，各回 (名稱, project_root, 該分支既有輸出的判準)。"""
    bad_config = tmp_path / 'bad-config'
    (bad_config / '.wf').mkdir(parents=True)
    (bad_config / '.wf/modules.json').write_text('{壞', encoding='utf-8')
    no_core = tmp_path / 'no-core'
    (no_core / '.wf').mkdir(parents=True)
    (no_core / 'rules').mkdir()
    (no_core / '.wf/modules.json').write_text(json.dumps(
        {'modules': [], 'areas': ['APP'], 'project': None, 'rules': {'path': 'rules'}}), encoding='utf-8')
    bad_module = tmp_path / 'bad-module'
    bad_module.mkdir()
    framework_tree(bad_module)
    (bad_module / '.wf').mkdir()
    (bad_module / '.wf/modules.json').write_text(json.dumps(
        {'modules': [{'name': 'ghost'}], 'areas': ['APP'], 'project': None}), encoding='utf-8')
    return (('ProjectConfigError', bad_config), ('ContextError', no_core),
            ('ModuleValidationError', bad_module))


def test_bootstrap_failure_branches_print_the_same_item_names(tmp_path, env, capsys):
    consumer, _, _, _ = installed_consumer(tmp_path, env, capsys, 'a7same')
    _, healthy, _ = preflight(consumer, capsys)
    expected = names_of(healthy)
    assert expected == list(_adopt.item_names()), expected
    for branch, root in broken_trees(tmp_path, env):
        client = FakeGhClient()
        rc = main(['--project-root', str(root), 'snapshot', '--adopt', 'preflight'],
                  client=client, root=None, env={})
        captured = capsys.readouterr()
        assert rc == 1, (branch, rc)
        assert names_of(captured.out) == expected, (branch, names_of(captured.out))
        rows = rows_of(captured.out)
        assert {status for status, _ in rows.values()} == {'unknown'}, (branch, rows)
        for name, (_, reason) in rows.items():
            assert 'Error' not in reason and 'Traceback' not in reason, (branch, name, reason)
        assert [call for call in client.calls if call[0] in MUTATIONS] == [], (branch, client.calls)
        if branch == 'ModuleValidationError':  # 既有的逐條 stdout ⛔ 不被改變、⛔ 不折疊
            module_lines = [line for line in captured.out.splitlines()
                            if line.startswith('模組宣告或設定不可用・')]
            assert module_lines and any("'ghost': 未知模組名" in line for line in module_lines), module_lines
            print('MODULE_STDOUT_UNCHANGED', module_lines)
        print('BRANCH', branch, 'names', names_of(captured.out))


def test_the_item_name_constant_is_the_single_home(tmp_path, env, capsys, monkeypatch):
    """負控（必須會響）：兩側都必須真的讀那一份常數、⛔ 不是各自寫死。兩種變異各打一側：
    ① 刪掉四列中任一列 ⇒ **失敗分支**（走 `print_unavailable`，只消費項名清單）的輸出必須少一項，
       與未改時的 preflight 基線比對轉紅。
    ② 把任一列改名 ⇒ **preflight 成功路徑**的輸出必須跟著改名（`reconcile` 以位置消費該常數，
       故此側用改名而⛔ 不用刪除——刪除會讓被測函式自己 IndexError，那測到的是崩潰、⛔ 不是接線）。"""
    consumer, _, _, _ = installed_consumer(tmp_path, env, capsys, 'a7const')
    _, healthy, _ = preflight(consumer, capsys)
    baseline = names_of(healthy)
    _, root = broken_trees(tmp_path, env)[0]
    for victim in FOUR:
        monkeypatch.setattr(_adopt, 'RECONCILIATION_ITEMS', tuple(n for n in FOUR if n != victim))
        assert victim not in _adopt.item_names()
        main(['--project-root', str(root), 'snapshot', '--adopt', 'preflight'],
             client=FakeGhClient(), root=None, env={})
        shrunk = names_of(capsys.readouterr().out)
        assert shrunk != baseline and victim not in shrunk, (victim, shrunk)
        renamed = tuple(f'{n}-變異' if n == victim else n for n in FOUR)
        monkeypatch.setattr(_adopt, 'RECONCILIATION_ITEMS', renamed)
        _, patched, _ = preflight(consumer, capsys)
        got = names_of(patched)
        assert got != baseline and f'{victim}-變異' in got and victim not in got, (victim, got)
        print('NEGATIVE_CONTROL dropped/renamed', victim, '->', shrunk, got)
    monkeypatch.undo()
    _, restored, _ = preflight(consumer, capsys)
    assert names_of(restored) == baseline, names_of(restored)


# ── A5 後半：四列對帳的十一種形狀 ─────────────────────────────────────────────────
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
    # A5 falsifier ②：同版本不同 SHA ⇒ 版本列 ok 而 commit 列 fail（只比版本值的做法會被打穿）
    assert matrix['same_version_different_sha'][FOUR[0]] == 'ok'
    assert matrix['same_version_different_sha'][FOUR[1]] == 'fail'
    assert matrix['staged_only'][FOUR[2]] == 'fail'
    assert matrix['dirty_checkout'][FOUR[3]] == 'fail'
    # A5 falsifier ③：未初始化 ⇒ 簽出列必須 unknown（naive 讀法會讀到 superproject 自己的 HEAD）
    assert matrix['uninitialised'][FOUR[3]] == 'unknown'
    assert matrix['mixed_pin'][FOUR[0]] == 'fail' and matrix['missing_pin'][FOUR[0]] == 'unknown'
    assert matrix['no_source_commit'][FOUR[1]] == 'unknown'
    assert matrix['no_manifest'][FOUR[0]] == matrix['no_manifest'][FOUR[1]] == 'unknown'
    # A5 falsifier ④：vendor 複製形狀 ⇒ 三個 gitlink 列全 unknown，版本列仍可判
    for name in ('not_a_submodule', 'non_git_worktree'):
        assert [matrix[name][item] for item in FOUR[1:]] == ['unknown'] * 3, matrix[name]
        assert matrix[name][FOUR[0]] == 'ok', matrix[name]
    print('MATRIX', json.dumps(matrix, ensure_ascii=False, indent=2))


def test_exactly_one_row_flips_when_the_source_commit_is_changed(tmp_path, env, capsys):
    """A5 負控（必須會響）：把 manifest 頂層 `source_commit` 改成另一個 40 碼值後，
    `framework-commit` 必須由 ok 轉 fail，其餘三列不變（列與列須獨立）。"""
    consumer, _, _, _ = installed_consumer(tmp_path, env, capsys, 'flip')
    _, before, _ = preflight(consumer, capsys)
    base = {item: rows_of(before)[item][0] for item in FOUR}
    assert base == {item: 'ok' for item in FOUR}, base
    edit_manifest(consumer, lambda m: m.update(source_commit='0' * 40))
    _, after, _ = preflight(consumer, capsys)
    now = {item: rows_of(after)[item][0] for item in FOUR}
    assert now[FOUR[1]] == 'fail', now
    assert {item: now[item] for item in FOUR if item != FOUR[1]} == \
           {item: base[item] for item in FOUR if item != FOUR[1]}, (base, now)
    print('FLIP', base, '->', now)


def test_the_pin_is_never_compared_against_a_gitlink_sha(tmp_path, env, capsys):
    """A5 falsifier ①：逐列印出兩個輸入，⛔ 不以關鍵字命中判——`framework-version` 的兩個輸入都不是
    40 碼 SHA；`framework-commit`／`gitlink-*` 的兩個輸入都不是版本字串。"""
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
