"""WF-015 A3：`snapshot --adopt bootstrap` 在同一棵合成樹上連跑兩次，樹的路徑集合與每個檔的內容
摘要逐一相等。消費 core/adopt.md §3。

口徑＝路徑集合＋內容 SHA-256，⛔ 不比對 mtime；摘要函式與 manifest 的摘要同一居所（`_adopt.digest_of`，
`import` 使用、⛔ 不重打）。合成樹在 `tmp_path` 內（F-規劃-09 逐字「測試⛔ 不依賴 repo 歷史存在；判準
在合成樹上驗」），明示排除本 repo 工作樹。
"""
import json
from pathlib import Path

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
    """`.wf/modules.json` 缺席時由 `ADOPTION.md` §2 的種子建立（⛔ 不在碼內重打種子）；
    `.wf/stages/<階段>.md` 對 `core/enums.md` 的每個階段各一。第二次連跑仍逐一相等。"""
    _, rules, _, _, _ = adopted_consumer(tmp_path, env, name='seed-src')
    bare = tmp_path / 'bare-consumer'
    bare.mkdir()
    rc1, out = bootstrap(bare, capsys, rules_root=rules)
    first = digests(bare)
    assert rc1 == 0, out
    seed = json.loads((rules / 'ADOPTION.md').read_text(encoding='utf-8')
                      .split('```json\n')[1].split('```')[0])
    assert json.loads((bare / '.wf/modules.json').read_text(encoding='utf-8')) == seed
    stages = _adopt._stages(_adopt.rules_of(rules))
    assert stages and all((bare / f'.wf/stages/{s}.md').is_file() for s in stages), stages
    rc2, _ = bootstrap(bare, capsys, rules_root=rules)
    assert rc2 == 0 and digests(bare) == first
    print('SEEDED', sorted(first), 'stages', list(stages))


def test_the_idempotence_check_is_effective(tmp_path, env, capsys, monkeypatch):
    """負控（必須會響）：讓 bootstrap 在產物內寫入一個每次都不同的欄位後，同一個判準必須轉紅；
    不轉即判「兩次都沒真的跑」或摘要恆等，測具無效（F-共用-06）。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='idem-neg')
    counter = iter(range(1000))
    monkeypatch.setattr(_adopt, '_stage_stub', lambda stage: f'# {stage} 第 {next(counter)} 次\n')
    bootstrap(consumer, capsys)
    first = digests(consumer)
    (consumer / '.wf/stages').rename(consumer / '.wf/stages-gone')  # 讓第二次重新建立
    bootstrap(consumer, capsys)
    second = digests(consumer)
    differing = {p for p in set(first) & set(second) if first[p] != second[p]}
    assert differing, (sorted(first), sorted(second))
    print('NEGATIVE_CONTROL timestamped_field differing', sorted(differing))
