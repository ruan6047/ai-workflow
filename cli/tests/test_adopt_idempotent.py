"""WF-015 A19 與 A20：`snapshot --adopt bootstrap` 的冪等性，與種子 `rules` 鍵帶著當次解析到的
rules root。消費 core/adopt.md §3。

口徑＝路徑集合＋內容 SHA-256，⛔ 不比對 mtime；摘要函式與 manifest 的摘要同一居所（`_adopt.digest_of`，
`import` 使用、⛔ 不重打）。合成樹在 `tmp_path` 內（`core/adopt.md` §0 逐字「⛔ 不依賴本 repo 歷史存在」），明示排除本 repo
工作樹與 `.git/`。
"""
import json
from pathlib import Path
import shutil

import pytest

from wf.verbs import _adopt
from wf.verbs.main import main
from .fakes import FakeGhClient
from .test_adopt_gitlink import RULES_PATH, adopted_consumer
from .test_context_roots import git_env


@pytest.fixture
def env(tmp_path):
    return git_env(tmp_path)


def digests(root):
    """全樹 (路徑, 內容摘要)；明示排除 `.git/`。摘要走 `_adopt.digest_of`（同一居所）。"""
    root = Path(root)
    return {path.relative_to(root).as_posix(): _adopt.digest_of(path.read_bytes())
            for path in sorted(root.rglob('*'))
            if path.is_file() and '.git' not in path.relative_to(root).parts}


def bootstrap(root, capsys, *, rules_root=None):
    argv = ['--project-root', str(root)]
    argv += ['--rules-root', str(rules_root)] if rules_root is not None else []
    rc = main([*argv, 'snapshot', '--adopt', 'bootstrap'], client=FakeGhClient(), root=None, env={})
    return rc, capsys.readouterr().out


def test_bootstrap_twice_leaves_the_tree_unchanged(tmp_path, env, capsys):
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env, name='idem')
    rc1, first_out = bootstrap(consumer, capsys)
    first = digests(consumer)
    rc2, second_out = bootstrap(consumer, capsys)
    second = digests(consumer)
    assert rc1 == rc2 == 0, (rc1, rc2)
    assert set(first) == set(second), sorted(set(first) ^ set(second))
    differing = {path for path in first if first[path] != second[path]}
    assert differing == set(), sorted(differing)
    created = [line for line in first_out.splitlines() if line.endswith('・建立')]
    reused = [line for line in second_out.splitlines() if line.endswith('・沿用')]
    assert created and len(reused) == len(created) + first_out.count('・沿用')
    print('IDEMPOTENT paths', len(first), 'first_created', len(created), 'second_reused', len(reused))
    print('DIFF', sorted(differing))


def test_bootstrap_creates_the_seed_and_the_stage_skeleton_when_absent(tmp_path, env, capsys):
    """`.wf/modules.json` 缺席時由 `_adopt.SEED_HOME` 的機器可讀種子建立（⛔ 不在碼內重打種子）；
    `.wf/stages/<階段>.md` 對 `core/enums.md` 的每個階段各一。第二次連跑仍逐一相等。"""
    _, rules, _, _, _ = adopted_consumer(tmp_path, env, name='seed-src')
    bare = tmp_path / 'bare-consumer'
    bare.mkdir()
    rc1, out = bootstrap(bare, capsys, rules_root=rules)
    first = digests(bare)
    assert rc1 == 0, out
    seed = json.loads((rules / _adopt.SEED_HOME).read_text(encoding='utf-8'))
    assert json.loads((bare / '.wf/modules.json').read_text(encoding='utf-8')) == seed
    stages = _adopt.stages_of(_adopt.rules_of(rules))
    assert stages and all((bare / f'.wf/stages/{s}.md').is_file() for s in stages), stages
    rc2, _ = bootstrap(bare, capsys, rules_root=rules)
    assert rc2 == 0 and digests(bare) == first
    print('SEEDED', sorted(first), 'stages', list(stages))


def idempotent(first, second):
    """判準本體（兩個正控與兩步負控共用）：路徑集合相等且每個檔的內容摘要相等。"""
    return set(first) == set(second) and all(first[p] == second[p] for p in first)


def test_the_idempotence_check_is_effective(tmp_path, env, capsys, monkeypatch):
    """負控兩步、順序固定、⛔ 不得省略第①步（`core/adopt.md` §3 的冪等口徑只有摘要一個維度）：
    ① 造一個「路徑集合不變、第二次某檔內容確實不同」的樣本，判準必須判為⛔ 非冪等（偵測能力存在）；
    ② 再把摘要函式換成恆回同一常數，同一個樣本必須**改為**被判成冪等（偵測能力消失）。
    ⛔ 不得用「換成常數摘要後測試轉紅」當負控——常數摘要會讓⛔ 非冪等樣本被判成冪等、測試轉綠。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='idem-neg')
    counter = iter(range(1000))
    monkeypatch.setattr(_adopt, '_stage_stub', lambda stage: f'# {stage} 第 {next(counter)} 次\n')
    bootstrap(consumer, capsys)
    first = digests(consumer)
    (consumer / '.wf/stages').rename(consumer / '.wf/stages-gone')  # 讓第二次重新建立
    bootstrap(consumer, capsys)
    second = digests(consumer)
    shared = {p: (first[p], second[p]) for p in set(first) & set(second)}
    sample_first = {p: v[0] for p, v in shared.items()}
    sample_second = {p: v[1] for p, v in shared.items()}
    assert set(sample_first) == set(sample_second)                  # 路徑集合不變的樣本
    assert not idempotent(sample_first, sample_second), sorted(sample_first)   # 第①步
    print('NEGATIVE_CONTROL step1 detects content drift',
          sorted(p for p in sample_first if sample_first[p] != sample_second[p]))
    monkeypatch.setattr(_adopt, 'digest_of', lambda data: 'sha256:constant')
    blind_first = {p: _adopt.digest_of(b'') for p in sample_first}
    blind_second = {p: _adopt.digest_of(b'') for p in sample_second}
    assert idempotent(blind_first, blind_second), (blind_first, blind_second)  # 第②步
    print('NEGATIVE_CONTROL step2 constant digest hides the drift', _adopt.digest_of(b''))


def test_the_seed_carries_the_rules_root_it_was_resolved_with(tmp_path, env, capsys):
    """A20：bootstrap 寫進種子的 `rules` 值，使同一棵樹上⛔ 不帶任何全域旗標的 preflight 解析到
    與 bootstrap 當次逐字相同的 rules root。"""
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env, name='a20')
    (consumer / _adopt.CONFIG_PATH).unlink()                        # 讓 bootstrap 自己建種子
    rc, out = bootstrap(consumer, capsys, rules_root=rules)
    assert rc == 0, out
    seed = json.loads((consumer / _adopt.CONFIG_PATH).read_text(encoding='utf-8'))
    assert seed['rules'] == {'path': RULES_PATH}, seed
    rc = main(['--project-root', str(consumer), 'snapshot', '--adopt', 'preflight'],
              client=FakeGhClient(), root=None, env={})
    printed = capsys.readouterr().out
    assert rc == 0, printed
    roots, = [line for line in printed.splitlines()
              if line.startswith(f'{_adopt.PREFIX}・{_adopt.STATIC_IDENTITY_ITEMS[0]}・')]
    assert str(Path(rules).resolve()) in roots, (roots, rules)
    assert roots.split('・')[2] == 'ok', roots
    print('A20 seed_rules', seed['rules'], 'preflight_roots', roots)


def test_the_seed_rules_key_is_null_when_the_rules_are_the_project_root(tmp_path, env, capsys):
    """負控（必須會響）：規則就在 project_root 的樹上，種子的 `rules` 須仍為 `null`。"""
    _, rules, _, _, _ = adopted_consumer(tmp_path, env, name='a20-neg-src')
    here = tmp_path / 'a20-here'
    shutil.copytree(rules, here)
    rc, out = bootstrap(here, capsys)
    assert rc == 0, out
    seed = json.loads((here / _adopt.CONFIG_PATH).read_text(encoding='utf-8'))
    assert seed['rules'] is None, seed
    print('NEGATIVE_CONTROL rules_at_project_root seed_rules', seed['rules'])
