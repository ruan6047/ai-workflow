"""WF-015 A22／A23／A24：五個 step 在⛔ 無 git remote、⛔ 無 `GH_REPO` 的合成樹上各自 rc=0 且逐項降級，
而 `wf.context.Context` 的公開契約與「讀 `context.repository` 的正式碼」零改動。
消費 core/adopt.md §0（合成 consumer 樹）／§3（五個 step、preflight 七項、smoke 五項）、
core/modules.md §5（fail-closed）。

兩個母體各自由 `import` 取得（`_adopt.item_names()` 與 `_adopt.SMOKE_ITEMS`）、⛔ 不重打。
**⛔ 無替身身分回退**：`main.candidates()` 在本機與 `GH_REPO` 皆缺席時會取 `client.repo`，替身自帶
repo 會讓正控被救活，故本檔的替身把 `repo` 覆寫成 `None`（`FakeGhClient` 本身⛔ 不改）。
"""
import ast
import json
from pathlib import Path
import subprocess

import pytest

from wf.context import public_contract
from wf.verbs import _adopt
from wf.verbs.main import main
from .fakes import FakeGhClient
from .test_adopt_fragments import MERGE_BASE, changed_files
from .test_adopt_gitlink import adopted_consumer, framework_tree
from .test_compose_schema import ROOT
from .test_context_roots import git_env

# 合併基底 372fe7f3bcdea7d7681910938387fd36a730c369 的 `public_contract()['Context']`。
# 此處**刻意**寫字面：被比對的是公開契約的凍結值、⛔ 不是實作常數的複製——重打本身就是判準。
BASE_CONTEXT_CONTRACT = {
    'project': 'ProjectRoot',
    'rules': 'RulesSource',
    'catalog': 'Catalog',
    'git': 'LocalGitFacts | None',
    'repository': 'RepositoryIdentity',
    'project_board': 'ProjectIdentity | None',
    'permissions': 'tuple[PermissionFact, ...]',
    'invocation_cwd': 'Resolved',
    'static_identity_verified': 'bool',
}


class NoIdentityFake(FakeGhClient):
    """⛔ 無身分回退的替身：`repo` 為 `None`，本機與 `GH_REPO` 都缺席時⛔ 不救活正控。"""
    repo = None


@pytest.fixture
def env(tmp_path):
    return git_env(tmp_path)


def run(root, step, capsys, environ=None):
    client = NoIdentityFake()
    rc = main(['--project-root', str(root), 'snapshot', '--adopt', step],
              client=client, root=None, env={} if environ is None else environ)
    return rc, capsys.readouterr().out, client


def rows_of(out):
    rows = {}
    for line in out.splitlines():
        if line.startswith(_adopt.PREFIX + '・'):
            _, name, status, reason = line.split('・', 3)
            rows[name] = status
    return rows


def local_tree(tmp_path, env, name):
    """⛔ 無 remote、⛔ 無 `GH_REPO` 的合成 consumer 樹（canonical install mode）。"""
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env, name=name)
    remotes = subprocess.run(['git', '-C', str(consumer), 'remote'], capture_output=True, text=True)
    assert remotes.stdout.strip() == '', remotes.stdout
    assert NoIdentityFake().repo is None
    return consumer, rules


# ── A22：三個純本機 step 依序各跑一次 ────────────────────────────────────────────
def test_local_steps_need_no_github_identity(tmp_path, env, capsys):
    consumer, _ = local_tree(tmp_path, env, 'a22')
    rc, out, _ = run(consumer, 'install', capsys)
    assert rc == 0, out
    assert (consumer / _adopt.MANIFEST_PATH).is_file(), out
    manifest = json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    managed = {e['path'] for e in _adopt.entries_of(manifest, _adopt.OWNERSHIPS[0])}
    for path in _adopt.INSTALL_SET:
        assert _adopt.asset_digest(consumer, path) is not None, (path, sorted(managed))
    print('A22 install', sorted(managed))
    rc, out, _ = run(consumer, 'bootstrap', capsys)
    assert rc == 0, out
    assert (consumer / _adopt.CONFIG_PATH).is_file(), out
    stages = _adopt.stages_of(_adopt.rules_of(consumer / 'vendor/wf'))
    assert stages and all((consumer / f'{_adopt.STAGE_DIR}/{s}.md').is_file() for s in stages), stages
    print('A22 bootstrap', len(stages), 'stage files')
    manifest = json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    whole = [e['path'] for e in _adopt.entries_of(manifest, _adopt.OWNERSHIPS[0])
             if _adopt.fragment_of(e['path']) is None]
    rc, out, _ = run(consumer, 'deactivate', capsys)
    assert rc == 0, out
    for path in whole:
        assert not (consumer / path).exists(), (path, out)
    print('A22 deactivate', whole)


# ── A23：preflight 與 smoke 各自對自己的母體逐項降級 ─────────────────────────────
def test_preflight_and_smoke_degrade_per_item_not_wholesale(tmp_path, env, capsys):
    consumer, _ = local_tree(tmp_path, env, 'a23')
    for step in ('install', 'bootstrap'):
        assert run(consumer, step, capsys)[0] == 0
    rc, out, _ = run(consumer, 'preflight', capsys)
    assert rc == 0, out
    pre = rows_of(out)
    assert list(pre) == list(_adopt.item_names()) and len(pre) == 7, list(pre)
    assert pre[_adopt.STATIC_IDENTITY_ITEMS[0]] != 'unknown', pre
    for item in _adopt.RECONCILIATION_ITEMS:
        assert pre[item] != 'unknown', (item, pre)          # 取源可得的對帳列⛔ 不得 unknown
    assert pre[_adopt.STATIC_IDENTITY_ITEMS[1]] == 'unknown', pre   # 身分缺席 ⇒ 該項 unknown
    print('A23 preflight_no_identity', pre)
    rc, out, _ = run(consumer, 'smoke', capsys)
    assert rc == 0, out
    smoke = rows_of(out)
    assert list(smoke) == list(_adopt.SMOKE_ITEMS) and len(smoke) == 5, list(smoke)
    assert 'unknown' not in smoke.values(), smoke
    print('A23 smoke_no_identity', smoke)
    # 反規避負控：補上可解析的本機身分後 `repository` 列必須由 unknown 轉為 ok／fail
    identified = FakeGhClient()
    rc = main(['--project-root', str(consumer), 'snapshot', '--adopt', 'preflight'],
              client=identified, root=None, env={'GH_REPO': 'owner/repo'})
    with_identity = rows_of(capsys.readouterr().out)
    assert rc == 0 and with_identity[_adopt.STATIC_IDENTITY_ITEMS[1]] != 'unknown', with_identity
    print('A23 with_GH_REPO', with_identity)
    # 母體負控：⛔ 未 install 的同形空樹上，smoke 的三項**應**為 unknown
    bare, _ = local_tree(tmp_path, env, 'a23-bare')
    rc, out, _ = run(bare, 'smoke', capsys)
    unknowns = [item for item, status in rows_of(out).items() if status == 'unknown']
    assert rc == 0 and set(unknowns) == set(_adopt.SMOKE_ITEMS[:3]), (unknowns, out)
    print('A23 bare_tree_unknowns', unknowns)


# ── A24：公開契約凍結、縮減路徑仍 fail-closed、唯讀端零改動 ──────────────────────
def test_the_public_context_contract_is_unchanged():
    now = public_contract()['Context']
    assert now == BASE_CONTEXT_CONTRACT, (now, BASE_CONTEXT_CONTRACT)
    print('A24 contract', json.dumps(now, ensure_ascii=False))


def reads_context_repository():
    """以 AST 取「正式碼內讀 `context.repository` 的檔案集合」；⛔ 不重打成字面清單。"""
    found = []
    for path in sorted((ROOT / 'cli/src/wf').rglob('*.py')):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if not (isinstance(node, ast.Attribute) and node.attr == 'repository'):
                continue
            base = node.value
            name = base.id if isinstance(base, ast.Name) else getattr(base, 'attr', None)
            if name == 'context':
                found.append(path.relative_to(ROOT).as_posix())
                break
    return sorted(set(found))


def test_the_context_repository_consumers_are_untouched():
    consumers = reads_context_repository()
    assert consumers, 'AST 掃描零命中 ⇒ 掃描器無效（F-共用-05）'
    changed = changed_files()
    assert changed, MERGE_BASE
    assert set(consumers) & set(changed) == set(), sorted(set(consumers) & set(changed))
    print('A24 consumers', consumers, 'changed', len(changed))


def test_the_adopt_path_is_still_fail_closed_on_invalid_modules(tmp_path, env, capsys):
    """縮減 bootstrap 仍 fail-closed：模組宣告無效時 `--adopt` 路徑 rc=1，且 stdout 仍逐條印完整修正資訊。"""
    root = tmp_path / 'a24-bad-module'
    root.mkdir()
    framework_tree(root)
    (root / '.wf').mkdir()
    (root / '.wf/modules.json').write_text(json.dumps(
        {'modules': [{'name': 'ghost'}], 'areas': ['APP'], 'project': None}), encoding='utf-8')
    rc, out, _ = run(root, 'preflight', capsys)
    assert rc == 1, out
    lines = [line for line in out.splitlines() if line.startswith('模組宣告或設定不可用・')]
    assert lines and any("'ghost': 未知模組名" in line for line in lines), out
    assert list(rows_of(out)) == list(_adopt.item_names()), out
    print('A24 fail_closed rc', rc, 'lines', lines)


def test_the_fail_closed_check_has_a_negative_control(tmp_path, env, capsys):
    """負控（必須會響）：同一棵樹把模組宣告改回合法後 rc=0，且⛔ 無那些修正資訊行。"""
    root = tmp_path / 'a24-good-module'
    root.mkdir()
    framework_tree(root)
    (root / '.wf').mkdir()
    (root / '.wf/modules.json').write_text(json.dumps(
        {'modules': [], 'areas': ['APP'], 'project': None}), encoding='utf-8')
    rc, out, _ = run(root, 'preflight', capsys)
    assert rc == 0, out
    assert [line for line in out.splitlines() if line.startswith('模組宣告或設定不可用・')] == [], out
    print('NEGATIVE_CONTROL valid_modules rc', rc)


# ══════════════════════════════════════════════════════════════════════════════
# WF-019 A2／A3：五個 step 串成一條流程之後才成立的兩條（A1／A4 住
# `cli/tests/test_adopt_preflight.py`）。消費 core/adopt.md §0／§3。
#
# 刻意⛔ 不改本檔既有的 WF-015 測試函式（A22／A23／A24）：卡面 `non_scope` 逐字「⛔ 不重新驗收
# WF-015 已通過的 28 條」。兩條一律新增函式、函式名前綴 `test_wf019_`，⛔ 不與既有函式同名。
# harness＝`test_adopt_preflight.wf019_run` 的子行程驅動器，⛔ 不得經 `capsys`（既有函式那一套
# 取法屬 WF-015 的射程，本卡只登記、⛔ 不動）。
# ══════════════════════════════════════════════════════════════════════════════
from .test_adopt_preflight import wf019_local_tree, wf019_mutations, wf019_run  # noqa: E402


def wf019_step_rows(out):
    """把 `採用・<step>・<對象>・<說明>` 逐行解析回 `[(step, 對象, 說明)]`；⛔ 不解析別的行。
    前綴由 `_adopt.STEP_PREFIX` import 取、⛔ 不重打。"""
    rows = []
    for line in out.splitlines():
        if line.startswith(_adopt.STEP_PREFIX + '・'):
            _, step, subject, note = line.split('・', 3)
            rows.append((step, subject, note))
    return rows


def wf019_status_rows(out):
    """把 `採用診斷・<項名>・<狀態>・<理由>` 逐行解析回 `{項名: (狀態, 理由)}`。判準只用**狀態**
    屬於 `ok`／`fail`／`unknown` 哪一類，⛔ 不比對理由字串的逐字內容。"""
    rows = {}
    for line in out.splitlines():
        if line.startswith(_adopt.PREFIX + '・'):
            _, name, status, reason = line.split('・', 3)
            rows[name] = (status, reason)
    return rows


# ── WF-019 A2：同一棵樹上有序三步，各自 rc=0 且逐步落地／逐步消失 ─────────────────
def test_wf019_local_steps_land_and_reverse_in_one_ordered_run(tmp_path, env):
    """WF-019 A2。母體釘死為**同一棵樹**上依 install → bootstrap → deactivate 的順序各執行一次
    （⛔ 不是三個獨立測試）。樹＝⛔ 無 git remote 的合成 consumer 樹；傳給 CLI 的 `env` ⛔ 不含
    `GH_REPO`，替身的 `repo` 為 None（⛔ 無身分回退）。三步各以一次子行程呼叫，⛔ 不經 `capsys`。"""
    consumer, _ = wf019_local_tree(tmp_path, env, 'wf019-a2')
    environ = {}
    assert 'GH_REPO' not in environ

    def step(name):
        rc, out, calls = wf019_run(consumer, ['--project-root', str(consumer), 'snapshot',
                                              '--adopt', name], environ=environ)
        print('WF019_A2_STEP', name, 'rc', rc, 'calls', json.dumps(calls),
              'rows', json.dumps(wf019_step_rows(out), ensure_ascii=False))
        return rc, out

    rc, out = step('install')
    assert rc == 0, out
    assert (consumer / _adopt.MANIFEST_PATH).is_file(), out
    for path in _adopt.INSTALL_SET:  # framework-managed 資產（整檔與片段）逐項在樹上
        assert _adopt.asset_digest(consumer, path) is not None, (path, out)
    manifest = json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    whole = sorted(e['path'] for e in _adopt.entries_of(manifest, _adopt.OWNERSHIPS[0])
                   if _adopt.fragment_of(e['path']) is None)
    # 負控 N2（反空集合，必須 >0）：集合為空時 deactivate 的「路徑消失」由空集合恆滿足、零資訊。
    assert whole, manifest
    print('WF019_A2_N2 WHOLE_FILE_ENTRIES', json.dumps(whole), 'CARDINALITY', len(whole),
          'NONEMPTY', True)

    rc, out = step('bootstrap')
    assert rc == 0, out
    assert (consumer / _adopt.CONFIG_PATH).is_file(), out
    stages = _adopt.stages_of(_adopt.rules_of(consumer / 'vendor/wf'))
    assert stages, consumer
    for stage in stages:  # 階段骨架：階段名由 rules source 枚舉、⛔ 不重打八個階段名
        assert (consumer / f'{_adopt.STAGE_DIR}/{stage}.md').is_file(), (stage, out)
    print('WF019_A2_BOOTSTRAP stages', len(stages), json.dumps(list(stages), ensure_ascii=False))

    rc, out = step('deactivate')
    assert rc == 0, out
    for path in whole:
        assert not (consumer / path).exists(), (path, out)
    # 負控 N3 用的「已移除」說明字串由**這一次執行自己**推得：取那些登記為整檔項、且這次之後
    # 確實⛔ 不在樹上的對象所帶的說明。⛔ 不重打實作字面。
    gone_notes = {note for _, subject, note in wf019_step_rows(out)
                  if subject in whole and not (consumer / subject).exists()}
    assert gone_notes, out
    print('WF019_A2_DEACTIVATE whole', json.dumps(whole), 'gone_notes',
          json.dumps(sorted(gone_notes), ensure_ascii=False))

    # 負控 N3（兩棵樹真的有差別，必須會響）：⛔ 未 install 的同形空樹上單跑 deactivate，
    # 其 stdout ⛔ 不得含任何「已移除」說明列。⛔ 不做這一層時正控的「路徑消失」零資訊。
    bare, _ = wf019_local_tree(tmp_path, env, 'wf019-a2-bare')
    rc, out, _ = wf019_run(bare, ['--project-root', str(bare), 'snapshot', '--adopt', 'deactivate'],
                           environ=environ)
    bare_rows = wf019_step_rows(out)
    assert rc == 0, out
    assert [row for row in bare_rows if row[2] in gone_notes] == [], bare_rows
    print('WF019_A2_N3 BARE deactivate rc', rc, 'rows',
          json.dumps(bare_rows, ensure_ascii=False))


def test_wf019_a2_identity_is_really_unavailable_on_that_tree(tmp_path, env):
    """WF-019 A2 負控 N1（必須會響）：同一棵樹、同一個 env 上跑 `snapshot`（**⛔ 不帶 `--adopt`**），
    rc 須 ≠0。⛔ 不做這一層時，三步的 rc=0 可能只是身分悄悄可得，正控零資訊（F-共用-05）。
    `snapshot` ⛔ 不帶 `--adopt` 的既有盤點路徑依卡面掃描面明示排除於 A1 之外；此處只作 A2 的負控。"""
    consumer, _ = wf019_local_tree(tmp_path, env, 'wf019-a2-n1')
    rc, out, calls = wf019_run(consumer, ['--project-root', str(consumer), 'snapshot'], environ={})
    assert rc != 0, (rc, out, calls)
    print('WF019_A2_N1 snapshot-without-adopt rc', rc, 'calls', json.dumps(calls))


# ── WF-019 A3：preflight 與 smoke 各自對自己的母體逐項降級 ───────────────────────
def test_wf019_preflight_and_smoke_degrade_on_their_own_population(tmp_path, env):
    """WF-019 A3。兩個母體各自 `import` 取、⛔ 不重打、⛔ 不互相冒充：preflight 的母體＝
    `_adopt.item_names()`（＝WF-015 改後 A22 釘住的那一個項名常數的唯一居所）、smoke 的母體＝
    `_adopt.SMOKE_ITEMS`。正控樹＝同一棵已依序跑完 `--adopt install` 與 `--adopt bootstrap` 的
    合成樹（⛔ 無 remote、env ⛔ 不含 `GH_REPO`）。兩個 step 各以一次子行程呼叫、⛔ 不經 `capsys`。

    **反規避負控⛔ 不得走真 `gh`**：`python -m wf.verbs.main` ＋ 真 `GH_REPO` 會對真 GitHub 發一次
    GraphQL 讀請求，而 `cli/tests/conftest.py` 的離線護欄在 `WF_OFFLINE=1` 時把 `gh` 擋成
    `OFFLINE_NETWORK_DENIED` ⇒ 走真 `gh` 的負控在離線 CI 上必然失敗。取法＝子行程驅動器注入
    `cli/tests/fakes.py` 的替身，其 `DEFAULTS['repository']` 對任何 slug 回同一顆 `R_FAKE`，
    身分因此可解析而⛔ 不碰網路。"""
    preflight_population, smoke_population = _adopt.item_names(), _adopt.SMOKE_ITEMS
    assert preflight_population and smoke_population
    assert set(preflight_population) & set(smoke_population) == set(), \
        (preflight_population, smoke_population)  # 兩個母體⛔ 不互相冒充
    print('WF019_A3_POPULATION preflight',
          json.dumps(list(preflight_population), ensure_ascii=False), len(preflight_population),
          '| smoke', json.dumps(list(smoke_population), ensure_ascii=False), len(smoke_population))

    consumer, _ = wf019_local_tree(tmp_path, env, 'wf019-a3')
    for step in ('install', 'bootstrap'):
        rc, out, _ = wf019_run(consumer, ['--project-root', str(consumer), 'snapshot',
                                          '--adopt', step], environ={})
        assert rc == 0, (step, out)

    rc, out, calls = wf019_run(consumer, ['--project-root', str(consumer), 'snapshot',
                                          '--adopt', 'preflight'], environ={})
    pre = wf019_status_rows(out)
    assert rc == 0, out
    assert list(pre) == list(preflight_population), list(pre)   # 母體恰等於那個常數，⛔ 不殘缺
    assert {status for status, _ in pre.values()} <= set(_adopt.STATUSES), pre
    assert pre[_adopt.STATIC_IDENTITY_ITEMS[0]][0] != 'unknown', pre        # `roots` 取源可得
    for item in _adopt.RECONCILIATION_ITEMS:
        assert pre[item][0] != 'unknown', (item, pre)                      # 四列對帳取源可得
    assert pre[_adopt.STATIC_IDENTITY_ITEMS[1]][0] == 'unknown', pre       # 身分缺席 ⇒ 該項 unknown
    print('WF019_A3_PREFLIGHT rc', rc, json.dumps(pre, ensure_ascii=False),
          '| calls', json.dumps(calls))

    rc, out, calls = wf019_run(consumer, ['--project-root', str(consumer), 'snapshot',
                                          '--adopt', 'smoke'], environ={})
    smoke = wf019_status_rows(out)
    assert rc == 0, out
    assert list(smoke) == list(smoke_population), list(smoke)
    assert [name for name, (status, _) in smoke.items() if status == 'unknown'] == [], smoke
    print('WF019_A3_SMOKE rc', rc, json.dumps(smoke, ensure_ascii=False),
          '| calls', json.dumps(calls))

    # 反規避負控（必須會響、且⛔ 不碰網路）：同一棵樹、同一個 harness 補上可解析的 `GH_REPO`
    # 之後重跑 preflight，`repository` 列須由 `unknown` 翻成 `ok`／`fail`；同一次執行的 mutation
    # 序列長度須仍為 0。替身的 `repo` 仍為 None ⇒ 身分只可能來自 `GH_REPO`，⛔ 不是替身自帶。
    rc, out, calls = wf019_run(consumer, ['--project-root', str(consumer), 'snapshot',
                                          '--adopt', 'preflight'], environ={'GH_REPO': 'acme/widgets'})
    identified = wf019_status_rows(out)
    item = _adopt.STATIC_IDENTITY_ITEMS[1]
    assert rc == 0 and identified[item][0] != 'unknown', (rc, identified)
    assert wf019_mutations(calls) == [], calls
    print('WF019_A3_NEG_ANTIEVASION', item, 'before', json.dumps(pre[item], ensure_ascii=False),
          'after', json.dumps(identified[item], ensure_ascii=False), '| calls', json.dumps(calls))


def test_wf019_a3_population_control_bare_tree_yields_unknowns(tmp_path, env):
    """WF-019 A3 母體負控（必須會響）：⛔ 未 install 的同形空樹上重跑 smoke，前三項**應**為
    `unknown`。本條⛔ 不是「無條件要求永不 unknown」；⛔ 不做這一層就無法區分「逐項降級」與
    「兩棵樹本來就沒差別」（F-共用-05）。"""
    bare, _ = wf019_local_tree(tmp_path, env, 'wf019-a3-bare')
    rc, out, _ = wf019_run(bare, ['--project-root', str(bare), 'snapshot', '--adopt', 'smoke'],
                           environ={})
    rows = wf019_status_rows(out)
    unknowns = [name for name, (status, _) in rows.items() if status == 'unknown']
    assert rc == 0, out
    assert set(unknowns) == set(_adopt.SMOKE_ITEMS[:3]), (unknowns, rows)
    print('WF019_A3_NEG_POPULATION BARE smoke rc', rc, 'UNKNOWN',
          json.dumps(unknowns, ensure_ascii=False), '|', json.dumps(rows, ensure_ascii=False))
