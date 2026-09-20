"""WF-015：`snapshot --adopt smoke` 的兩類分項、逐項取源表與 `managed-assets` 的雙向判準。
消費 core/adopt.md §3（五個 step、smoke 的類別／取源表）／§2（框架資產表、應安裝集合）。

**翻面的口徑＝整列（項名・狀態・理由）改變**（`core/adopt.md` §3 逐字）：（乙）類的狀態恆為
`unknown`，只以狀態比會讓它永不翻面，那會把「一律 unknown」誤讀成「⛔ 不消費任何取源」。

檢查項母體由 `wf.verbs._adopt.SMOKE_ITEMS`、應安裝集合由 `_adopt.INSTALL_SET` `import` 枚舉、
⛔ 不重打清單（F-執行者-04）；取源 → 消費項的映射由解析 `core/adopt.md` §3 的表格取得、⛔ 不重打。
掃描面＝合成 consumer 樹（`core/adopt.md` §0）；另明示排除真 GitHub——遠端權限與 Project 建板是
`core/adopt.md` §4 的人工步驟，⛔ 不進本母體。
"""
import json
from pathlib import Path

import pytest

from wf.gh.writes import MUTATIONS
from wf.verbs import _adopt, _adopt_reconcile
from wf.verbs.main import main
from .fakes import FakeGhClient
from .test_adopt_gitlink import adopted_consumer
from .test_adoption_contract import smoke_categories, smoke_sources
from .test_context_roots import git_env


@pytest.fixture
def env(tmp_path):
    return git_env(tmp_path)


def statuses(out):
    return {line.split('・', 3)[1]: line.split('・', 3)[2] for line in out.splitlines()
            if line.startswith(_adopt.PREFIX + '・')}


def rows(out):
    """{項名: (狀態, 理由)}——翻面比的是整列，⛔ 不只比狀態。"""
    return {line.split('・', 3)[1]: tuple(line.split('・', 3)[2:]) for line in out.splitlines()
            if line.startswith(_adopt.PREFIX + '・')}


def adopted(tmp_path, env, capsys, name):
    """install ＋ bootstrap 都跑過的合成 consumer 樹。"""
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env, name=name)
    for step in ('install', 'bootstrap'):
        assert main(['--project-root', str(consumer), 'snapshot', '--adopt', step],
                    client=FakeGhClient(), root=None, env={}) == 0
    capsys.readouterr()
    return consumer, rules


def smoke(consumer, capsys):
    client = FakeGhClient()
    rc = main(['--project-root', str(consumer), 'snapshot', '--adopt', 'smoke'],
              client=client, root=None, env={})
    out = capsys.readouterr().out
    return rc, statuses(out), client, rows(out)


def edit_manifest(consumer, mutate):
    path = consumer / _adopt.MANIFEST_PATH
    manifest = json.loads(path.read_text(encoding='utf-8'))
    mutate(manifest)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


def drop_entry(manifest, path):
    manifest['assets'] = [e for e in manifest['assets'] if e['path'] != path]


# ── 每個取源各一種只破壞它的變異；⛔ 不在同一次變異裡動兩個取源 ──────────────────────
def break_manifest_file(consumer, rules, monkeypatch):
    edit_manifest(consumer, lambda m: m.update(schema='not-the-schema'))


def break_tree_assets(consumer, rules, monkeypatch):
    path = consumer / _adopt.INSTALL_SET[0]
    path.write_text(path.read_text(encoding='utf-8') + '\n# 被改過\n', encoding='utf-8')


def break_rules_version(consumer, rules, monkeypatch):
    path = Path(rules) / _adopt.VERSION_HOME
    path.write_text(path.read_text(encoding='utf-8').replace('version = "', 'version = "9.', 1),
                    encoding='utf-8')


def break_config_file(consumer, rules, monkeypatch):
    path = consumer / _adopt.CONFIG_PATH
    config = json.loads(path.read_text(encoding='utf-8'))
    config['areas'] = []
    path.write_text(json.dumps(config, ensure_ascii=False), encoding='utf-8')


def break_rules_stages(consumer, rules, monkeypatch):
    """階段枚舉取源：只把該取源的讀取函式換掉，樹上其餘位元組逐一不動。"""
    monkeypatch.setattr(_adopt_reconcile, 'stages_of', lambda rules: ())


def break_tree_stages(consumer, rules, monkeypatch):
    sorted((consumer / _adopt.STAGE_DIR).glob('*.md'))[0].unlink()


def break_manifest_field(consumer, rules, monkeypatch):
    """第二種粒度：結構仍有效，只把某一項的某一欄值改成⛔ 不正確的值（`pin` 漂掉）。
    ⛔ 不得以「整份 schema 失效」一種粒度代表整個取源——那會把檔案級依賴表偷偷升成
    「任意破壞皆全翻」的承諾（序 2 `R5.2-6` 的量測）。"""
    edit_manifest(consumer, lambda m: m['assets'][0].update(pin='9.9.9'))


def break_tree_asset_missing(consumer, rules, monkeypatch):
    (consumer / _adopt.INSTALL_SET[0]).unlink()


# 變異形狀清單住**本檔**、⛔ 不住 `core/adopt.md`（卡面 A6 ②：規則本體是採用規則的居所、
# ⛔ 不是測試矩陣的居所）。`manifest.file` 至少兩種粒度；`tree.assets` 恰兩種——「目標路徑上有
# ⛔ 非框架落地的既有物」**⛔ 不進本清單**：要讓路徑未登記必須同時改 manifest，那就⛔ 非「只施加
# 單一取源」，它是**另一個基線**、由 `STATES['occupied_unregistered']` 承接。
BREAKAGE = {
    'manifest.file': (break_manifest_file, break_manifest_field),
    'tree.assets': (break_tree_assets, break_tree_asset_missing),
    'rules.version': (break_rules_version,),
    'config.file': (break_config_file,),
    'rules.stages': (break_rules_stages,),
    'tree.stages': (break_tree_stages,),
}


def test_the_source_table_vocabulary_is_closed_and_every_source_is_consumed():
    table = smoke_sources()
    assert set(table) == set(_adopt.SMOKE_ITEMS), sorted(set(table) ^ set(_adopt.SMOKE_ITEMS))
    vocabulary = {source for ids in table.values() for source in ids}
    assert vocabulary == set(BREAKAGE), sorted(vocabulary ^ set(BREAKAGE))
    for source in vocabulary:
        assert [item for item, ids in table.items() if source in ids], source
    print('SMOKE_SOURCES', table, 'vocabulary', sorted(vocabulary))


def test_each_item_flips_exactly_for_its_declared_sources(tmp_path, env, capsys, monkeypatch):
    table, categories = smoke_sources(), smoke_categories()
    healthy_tree, _ = adopted(tmp_path, env, capsys, 'smoke-ok')
    rc, healthy, client, healthy_rows = smoke(healthy_tree, capsys)
    assert rc == 0 and list(healthy) == list(_adopt.SMOKE_ITEMS), list(healthy)
    assert set(categories) == set(_adopt.SMOKE_ITEMS), sorted(set(categories) ^ set(_adopt.SMOKE_ITEMS))
    ai = {item for item, mark in categories.items() if mark == '乙'}
    assert ai == set(_adopt.SMOKE_AI_ITEMS), sorted(ai ^ set(_adopt.SMOKE_AI_ITEMS))
    assert {healthy[item] for item in ai} == {'unknown'}, healthy   # （乙）類一律 unknown
    assert {healthy[item] for item in set(_adopt.SMOKE_ITEMS) - ai} == {'ok'}, healthy
    for item in ai:                                                # 並印出所需的證據種類
        assert _adopt.AI_EVIDENCE in healthy_rows[item][1], (item, healthy_rows[item])
    assert [call for call in client.calls if call[0] in MUTATIONS] == [], client.calls
    print('SMOKE healthy', healthy, 'ai_items', sorted(ai))
    # **基線先釘死**：健康合成樹的（甲）類五項全部⛔ 非 `unknown`。（乙）類在此⛔ 不進基線斷言——
    # `core/adopt.md` §3 逐字要求它們**一律標 `unknown`**，把它們算進「七項全部⛔ 非 unknown」
    # 在任何實作下都不可能成立。該落差已隨本輪交回單上呈需求方裁定，⛔ 不在本檔自行調和。
    assert {healthy[item] for item in set(_adopt.SMOKE_ITEMS) - ai} == {'ok'}, healthy
    reached = set()
    for source, shapes in BREAKAGE.items():
        declared = {item for item, ids in table.items() if source in ids}
        flipped_by_source = set()
        for shape in shapes:
            with monkeypatch.context() as patch:
                consumer, rules = adopted(
                    tmp_path, env, capsys, f'smoke-{source.replace(".", "-")}-{shape.__name__}')
                shape(consumer, rules, patch)
                rc, broken, client, broken_rows = smoke(consumer, capsys)
            assert rc == 0, (source, broken)
            flipped = {item for item in _adopt.SMOKE_ITEMS if broken_rows[item] != healthy_rows[item]}
            # **上界（∀ 形狀）**：⛔ 不得有宣告外的項翻面。某項與基線逐字相同是正確結果、⛔ 不是缺陷，
            # 故這裡是 ⊆ 而⛔ 不是 ==；「一次變異翻兩項以上」也⛔ 不構成推翻。
            assert flipped <= declared, (source, shape.__name__, sorted(flipped - declared))
            flipped_by_source |= flipped
            assert all(status in _adopt.STATUSES for status in broken.values()), broken
            assert {broken[item] for item in ai} == {'unknown'}, (source, broken)
            assert [call for call in client.calls if call[0] in MUTATIONS] == [], client.calls
            print('SMOKE source', source, 'shape', shape.__name__, 'flipped', sorted(flipped),
                  'declared', sorted(declared), 'statuses', broken)
        # **下界（∀ 宣告邊，∃ 形狀）**：⛔ 不得有只寫在表上、任何形狀都翻不動的邊。
        assert flipped_by_source == declared, (source, sorted(flipped_by_source ^ declared))
        reached |= declared
    assert reached == set(_adopt.SMOKE_ITEMS), sorted(reached ^ set(_adopt.SMOKE_ITEMS))
    assert len(BREAKAGE['manifest.file']) >= 2 and len(BREAKAGE['tree.assets']) == 2, BREAKAGE


# ── `managed-assets` 是雙向判準，母體＝§2 資產表宣告的目標路徑集合（整檔）──────────────
def drift(consumer):
    """摘要漂移：樹上檔案改一個位元組，manifest ⛔ 不動。"""
    path = consumer / _adopt.INSTALL_SET[0]
    path.write_bytes(path.read_bytes() + b'\n')


def occupied_unregistered(consumer):
    """（甲-c）：目標路徑上有⛔ 非框架落地的既有物、且⛔ 無 `framework-managed` 登記。
    這是**另一個基線**、⛔ 不是 `tree.assets` 的變異——要讓路徑未登記必須同時改 manifest。"""
    edit_manifest(consumer, lambda m: drop_entry(m, _adopt.INSTALL_SET[0]))
    (consumer / _adopt.INSTALL_SET[0]).write_text('採用者自己的內容\n', encoding='utf-8')


# §3 的全函數恰三種情形；五種合成狀態逐一釘死該項的狀態值（卡面 V18 ②）。
STATES = {
    'complete': (lambda c: None, 'ok'),
    'file_missing_entry_kept': (lambda c: (c / _adopt.INSTALL_SET[0]).unlink(), 'fail'),
    'file_missing_entry_dropped': (lambda c: ((c / _adopt.INSTALL_SET[0]).unlink(),
                                              edit_manifest(c, lambda m: drop_entry(
                                                  m, _adopt.INSTALL_SET[0]))), 'fail'),
    'digest_drift': (drift, 'fail'),
    'occupied_unregistered': (occupied_unregistered, 'unknown'),
}


def member_lines(out):
    """`managed-assets` 印 1＋|母體| 行（成員行在前、狀態行在後）；本函式只取成員行。"""
    prefix = f'{_adopt.PREFIX}・{_adopt.SMOKE_ITEMS[1]}・'
    return [line for line in out.splitlines() if line.startswith(prefix)][:-1]


@pytest.mark.parametrize('state', list(STATES))
def test_managed_assets_is_a_total_function_over_the_declared_targets(tmp_path, env, capsys, state):
    """母體＝§2 資產表宣告的目標路徑集合，**⛔ 不因任何樹的狀態而收窄**：五種狀態下成員行數恆等於
    母體基數，⛔ 不得以縮母體換取該列標 `ok`。"""
    consumer, _ = adopted(tmp_path, env, capsys, f'total-{state}')
    manifest = json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    registered = {e['path'] for e in _adopt.managed_entries(manifest)}
    assert set(_adopt.INSTALL_SET) <= registered, sorted(set(_adopt.INSTALL_SET) - registered)
    assert all('#' not in path for path in _adopt.INSTALL_SET), _adopt.INSTALL_SET
    mutate, expected = STATES[state]
    mutate(consumer)
    client = FakeGhClient()
    rc = main(['--project-root', str(consumer), 'snapshot', '--adopt', 'smoke'],
              client=client, root=None, env={})
    out = capsys.readouterr().out
    assert rc == 0 and statuses(out)[_adopt.SMOKE_ITEMS[1]] == expected, (state, out)
    members = member_lines(out)
    assert len(members) == len(_adopt.INSTALL_SET), (state, members)   # 全函數：逐一成員各一行
    for path in _adopt.INSTALL_SET:
        assert [line for line in members if path in line], (state, path, members)
    if state == 'occupied_unregistered':
        hit = [line for line in members if _adopt_reconcile.UNREGISTERED_OCCUPANT in line]
        assert len(hit) == 1, (hit, members)                           # 該行逐字印那句
        jobs = [name for asset in _adopt.ASSETS if asset.target == _adopt.INSTALL_SET[0]
                for name in asset.content]
        assert jobs, _adopt.ASSETS
        for job in jobs:
            assert job not in hit[0], (job, hit[0])   # 本列⛔ 不自印 job 名
        # 必要內容識別只有一個居所＝（乙）類 `pending-integration`：它**必須**印得出來，
        # 否則「⛔ 不重印」會退化成「兩列都⛔ 不印」而那個識別就⛔ 無居所。
        home, = [line for line in out.splitlines()
                 if line.startswith(f'{_adopt.PREFIX}・{_adopt.SMOKE_ITEMS[5]}・')]
        for job in jobs:
            assert job in home, (job, home)
    print('TOTAL_FUNCTION', state, expected, 'members', members)


def test_the_population_is_not_narrowed_by_an_empty_tree(tmp_path, env, capsys):
    """空母體負控（堵住「以已登記者定義母體」的恆真漏洞）：manifest 缺席、兩個目標路徑皆⛔ 不存在
    ⇒ 該列⛔ 非 `ok`，且成員行數仍等於母體基數。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='empty-population')
    assert not (consumer / _adopt.MANIFEST_PATH).exists()
    for path in _adopt.INSTALL_SET:
        assert not (consumer / path).exists(), path
    client = FakeGhClient()
    rc = main(['--project-root', str(consumer), 'snapshot', '--adopt', 'smoke'],
              client=client, root=None, env={})
    out = capsys.readouterr().out
    assert rc == 0 and statuses(out)[_adopt.SMOKE_ITEMS[1]] != 'ok', out
    assert len(member_lines(out)) == len(_adopt.INSTALL_SET), out
    print('EMPTY_POPULATION', statuses(out)[_adopt.SMOKE_ITEMS[1]], member_lines(out))


def test_adopt_manifest_checks_existence_and_structure_only(tmp_path, env, capsys):
    """方案 A：`adopt-manifest` 的語意恰為「存在且合 §2 結構宣告 ⇒ `ok`，否則⛔ 非 `ok`」，
    且⛔ 無任何自指摘要比對——`self_digest` 已退休、控制檔⛔ 不自登記。"""
    consumer, _ = adopted(tmp_path, env, capsys, 'manifest-row')
    rc, found, _, _ = smoke(consumer, capsys)
    assert rc == 0 and found[_adopt.SMOKE_ITEMS[0]] == 'ok', found
    assert not hasattr(_adopt, 'self_digest') and not hasattr(_adopt_reconcile, 'self_digest')
    # 改掉任一項的 `digest` 但結構仍有效 ⇒ 本項仍 `ok`（它⛔ 不比對內容摘要，那是 managed-assets 的事）
    edit_manifest(consumer, lambda m: m['assets'][0].update(digest='sha256:0'))
    rc, drifted, _, _ = smoke(consumer, capsys)
    assert rc == 0 and drifted[_adopt.SMOKE_ITEMS[0]] == 'ok', drifted
    edit_manifest(consumer, lambda m: m.update(schema='nope'))       # 負控：結構失效 ⇒ ⛔ 非 ok
    rc, broken, _, _ = smoke(consumer, capsys)
    assert rc == 0 and broken[_adopt.SMOKE_ITEMS[0]] != 'ok', broken
    print('ADOPT_MANIFEST ok/digest_drift/structure_broken',
          found[_adopt.SMOKE_ITEMS[0]], drifted[_adopt.SMOKE_ITEMS[0]], broken[_adopt.SMOKE_ITEMS[0]])


def test_managed_assets_is_not_ok_without_a_manifest(tmp_path, env, capsys):
    """manifest 不存在的樹由結構宣告那條承接：本列只被要求⛔ 不得標 `ok`（⛔ 不重複要求 `fail`）。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='bidir-bare')
    rc, found, _, _ = smoke(consumer, capsys)
    assert rc == 0 and found[_adopt.SMOKE_ITEMS[1]] != 'ok', found
    assert found[_adopt.SMOKE_ITEMS[0]] == 'unknown' and found[_adopt.SMOKE_ITEMS[2]] == 'unknown', found
    assert found[_adopt.SMOKE_ITEMS[4]] == 'fail', found        # 尚未 bootstrap ⇒ 階段骨架缺
    print('NO_MANIFEST', found)
