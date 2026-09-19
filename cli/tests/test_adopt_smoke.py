"""WF-015 A29 與 A30：`snapshot --adopt smoke` 的逐項取源表與 `managed-assets` 的雙向判準。
消費 core/adopt.md §3（五個 step、smoke 取源表）／§2（片段資產判定、應安裝集合）。

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
from .test_adoption_contract import smoke_sources
from .test_context_roots import git_env


@pytest.fixture
def env(tmp_path):
    return git_env(tmp_path)


def statuses(out):
    return {line.split('・', 3)[1]: line.split('・', 3)[2] for line in out.splitlines()
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
    return rc, statuses(capsys.readouterr().out), client


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
    path = consumer / _adopt.MANAGED_ASSETS[0]
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


BREAKAGE = {'manifest.file': break_manifest_file, 'tree.assets': break_tree_assets,
            'rules.version': break_rules_version, 'config.file': break_config_file,
            'rules.stages': break_rules_stages, 'tree.stages': break_tree_stages}


def test_the_source_table_vocabulary_is_closed_and_every_source_is_consumed():
    table = smoke_sources()
    assert set(table) == set(_adopt.SMOKE_ITEMS), sorted(set(table) ^ set(_adopt.SMOKE_ITEMS))
    vocabulary = {source for ids in table.values() for source in ids}
    assert vocabulary == set(BREAKAGE), sorted(vocabulary ^ set(BREAKAGE))
    for source in vocabulary:
        assert [item for item, ids in table.items() if source in ids], source
    print('SMOKE_SOURCES', table, 'vocabulary', sorted(vocabulary))


def test_each_item_flips_exactly_for_its_declared_sources(tmp_path, env, capsys, monkeypatch):
    table = smoke_sources()
    healthy_tree, _ = adopted(tmp_path, env, capsys, 'smoke-ok')
    rc, healthy, client = smoke(healthy_tree, capsys)
    assert rc == 0 and list(healthy) == list(_adopt.SMOKE_ITEMS), list(healthy)
    assert len(_adopt.SMOKE_ITEMS) == 5 and set(healthy.values()) == {'ok'}, healthy
    assert [call for call in client.calls if call[0] in MUTATIONS] == [], client.calls
    print('SMOKE healthy', healthy)
    for source, sabotage in BREAKAGE.items():
        with monkeypatch.context() as patch:
            consumer, rules = adopted(tmp_path, env, capsys, f'smoke-{source.replace(".", "-")}')
            sabotage(consumer, rules, patch)
            rc, broken, client = smoke(consumer, capsys)
        assert rc == 0, (source, broken)
        flipped = {item for item in _adopt.SMOKE_ITEMS if broken[item] != healthy[item]}
        declared = {item for item, ids in table.items() if source in ids}
        assert flipped == declared, (source, sorted(flipped), sorted(declared))
        assert all(status in _adopt.STATUSES for status in broken.values()), broken
        assert [call for call in client.calls if call[0] in MUTATIONS] == [], (source, client.calls)
        print('SMOKE source', source, 'flipped', sorted(flipped), 'declared', sorted(declared),
              'statuses', broken)


# ── A30：`managed-assets` 是雙向判準，母體同時含整檔資產與片段資產 ──────────────────
def fragment_free(consumer):
    """把承載檔內的框架片段移掉（樹上缺席），⛔ 不動 manifest。"""
    path = consumer / _adopt.CARRIER
    path.write_text(_adopt.remove_jobs(path.read_text(encoding='utf-8'), [_adopt.FRAGMENTS[0]]),
                    encoding='utf-8')


STATES = {
    'complete': lambda c: None,
    'file_missing_entry_kept': lambda c: (c / _adopt.MANAGED_ASSETS[0]).unlink(),
    'file_missing_entry_dropped': lambda c: ((c / _adopt.MANAGED_ASSETS[0]).unlink(),
                                             edit_manifest(c, lambda m: drop_entry(
                                                 m, _adopt.MANAGED_ASSETS[0]))),
    'fragment_missing_entry_dropped': lambda c: (fragment_free(c),
                                                 edit_manifest(c, lambda m: drop_entry(
                                                     m, f'{_adopt.CARRIER}#{_adopt.FRAGMENTS[0]}'))),
}


@pytest.mark.parametrize('state', list(STATES))
def test_managed_assets_is_bidirectional_over_files_and_fragments(tmp_path, env, capsys, state):
    consumer, _ = adopted(tmp_path, env, capsys, f'a30-{state}')
    manifest = json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    registered = {e['path'] for e in _adopt.entries_of(manifest, _adopt.OWNERSHIPS[0])}
    assert set(_adopt.INSTALL_SET) <= registered, sorted(set(_adopt.INSTALL_SET) - registered)
    assert any(_adopt.fragment_of(p) for p in _adopt.INSTALL_SET), _adopt.INSTALL_SET
    STATES[state](consumer)
    rc, rows, _ = smoke(consumer, capsys)
    expected = 'ok' if state == 'complete' else 'fail'
    assert rc == 0 and rows[_adopt.SMOKE_ITEMS[1]] == expected, (state, rows)
    print('A30', state, rows[_adopt.SMOKE_ITEMS[1]], 'install_set', list(_adopt.INSTALL_SET))


def test_managed_assets_is_not_ok_without_a_manifest(tmp_path, env, capsys):
    """manifest 不存在的樹由 A7 承接：本列只被要求⛔ 不得標 `ok`（⛔ 不重複要求 `fail`）。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='a30-bare')
    rc, rows, _ = smoke(consumer, capsys)
    assert rc == 0 and rows[_adopt.SMOKE_ITEMS[1]] != 'ok', rows
    assert rows[_adopt.SMOKE_ITEMS[0]] == 'unknown' and rows[_adopt.SMOKE_ITEMS[2]] == 'unknown', rows
    assert rows[_adopt.SMOKE_ITEMS[4]] == 'fail', rows        # 尚未 bootstrap ⇒ 階段骨架缺
    print('A30 no_manifest', rows)
