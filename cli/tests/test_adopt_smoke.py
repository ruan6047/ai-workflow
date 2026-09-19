"""WF-015 A6：`snapshot --adopt smoke` 在已完成 install 與 bootstrap 的合成 consumer 樹上逐項印出
最小端到端檢查，每項標 ok／fail／unknown；逐項破壞後恰該項翻面。消費 core/adopt.md §3。

檢查項母體由 `wf.verbs._adopt.SMOKE_ITEMS` `import` 枚舉、⛔ 不重打清單（F-執行者-04）。
掃描面＝合成 consumer 樹；明示排除真 GitHub（卡面 `non_scope` 第 6 條逐字「⛔ 不用測試 mutation 探測
GitHub 權限；不可證明者明列 unknown」）——遠端權限與 Project 建板是 `core/adopt.md` §4 的人工步驟，
⛔ 不進本母體。
"""
import json
from pathlib import Path

import pytest

from wf.gh.writes import MUTATIONS
from wf.verbs import _adopt
from wf.verbs.main import main
from .fakes import FakeGhClient
from .test_adopt_gitlink import adopted_consumer
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


def break_manifest_schema(consumer, rules):
    path = consumer / _adopt.MANIFEST_PATH
    manifest = json.loads(path.read_text(encoding='utf-8'))
    manifest['schema'] = 'not-the-schema'
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def break_managed_asset(consumer, rules):
    path = consumer / _adopt.MANAGED_ASSETS[0]
    path.write_text(path.read_text(encoding='utf-8') + '\n# 被改過\n', encoding='utf-8')


def break_version(consumer, rules):
    path = Path(rules) / _adopt.VERSION_HOME
    path.write_text(path.read_text(encoding='utf-8').replace('version = "', 'version = "9.', 1),
                    encoding='utf-8')


def break_config(consumer, rules):
    path = consumer / _adopt.CONFIG_PATH
    config = json.loads(path.read_text(encoding='utf-8'))
    config['areas'] = []
    path.write_text(json.dumps(config, ensure_ascii=False), encoding='utf-8')


def break_stage_notes(consumer, rules):
    victim = sorted((consumer / _adopt.STAGE_DIR).glob('*.md'))[0]
    victim.unlink()


BREAKAGE = dict(zip(_adopt.SMOKE_ITEMS, (break_manifest_schema, break_managed_asset,
                                         break_version, break_config, break_stage_notes)))


def test_smoke_reports_each_item_and_fails_loudly(tmp_path, env, capsys):
    assert set(BREAKAGE) == set(_adopt.SMOKE_ITEMS), sorted(set(BREAKAGE) ^ set(_adopt.SMOKE_ITEMS))
    healthy_tree, healthy_rules = adopted(tmp_path, env, capsys, 'smoke-ok')
    rc, healthy, client = smoke(healthy_tree, capsys)
    assert rc == 0 and list(healthy) == list(_adopt.SMOKE_ITEMS), list(healthy)
    assert len(_adopt.SMOKE_ITEMS) > 0
    # 負控：不做任何破壞時全部項須為 ok 或 unknown、⛔ 無 fail（有 fail 即判合成樹沒搭對）
    assert set(healthy.values()) <= {'ok', 'unknown'}, healthy
    assert set(healthy.values()) == {'ok'}, healthy
    assert [call for call in client.calls if call[0] in MUTATIONS] == [], client.calls
    print('SMOKE healthy', healthy)
    for item, sabotage in BREAKAGE.items():
        consumer, rules = adopted(tmp_path, env, capsys, f'smoke-{item}')
        sabotage(consumer, rules)
        rc, broken, client = smoke(consumer, capsys)
        assert rc == 0 and broken[item] in ('fail', 'unknown'), (item, broken)
        assert broken[item] != healthy[item], (item, broken[item], healthy[item])
        others = {name: status for name, status in broken.items() if name != item}
        assert others == {name: status for name, status in healthy.items() if name != item}, (item, broken)
        assert [call for call in client.calls if call[0] in MUTATIONS] == [], (item, client.calls)
        print('SMOKE broken', item, broken)


def test_smoke_items_are_unknown_when_the_tree_was_never_installed(tmp_path, env, capsys):
    """未 install ⇒ manifest 相關項一律 `unknown`、⛔ 不冒充 ok，也⛔ 不整體靜默通過。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='smoke-bare')
    rc, rows, _ = smoke(consumer, capsys)
    assert rc == 0 and rows[_adopt.SMOKE_ITEMS[0]] == 'unknown', rows
    assert rows[_adopt.SMOKE_ITEMS[1]] == 'unknown' and rows[_adopt.SMOKE_ITEMS[2]] == 'unknown', rows
    assert rows[_adopt.SMOKE_ITEMS[4]] == 'fail', rows  # 尚未 bootstrap ⇒ 階段骨架缺
    print('SMOKE never_installed', rows)
