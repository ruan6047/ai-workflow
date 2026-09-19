"""WF-015 A4 與 A5 前半。消費 core/adopt.md §1（版本值唯一居所）／§2（manifest 鍵集合、所有權、
`source_commit`、`pin` 彙整規則）。

合成 consumer 樹＝`test_adopt_gitlink.py` 的 `adopted_consumer`（canonical install mode：真 submodule）。
manifest 的鍵集合與所有權分類由 `wf.verbs._adopt` `import` 取得，⛔ 不重打（F-執行者-04）。
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
from .test_compose_schema import ROOT
from .test_context_roots import RULE_DIRS, git, git_env

VERSION_DECLARATION = re.compile(r'^\s*version\s*=', re.M)


def tree_digests(root):
    """全樹 (路徑, 內容摘要)；明示排除 `.git/`（A4 掃描面逐字）。⛔ 不比對 mtime。"""
    root = Path(root)
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob('*'))
            if path.is_file() and '.git' not in path.relative_to(root).parts}


def run_step(consumer, step, client=None):
    client = FakeGhClient() if client is None else client
    rc = main(['--project-root', str(consumer), 'snapshot', '--adopt', step],
              client=client, root=None, env={})
    return rc, client


def consumer_owned(consumer):
    """三個 consumer 自有檔，其中一個與某 framework-managed 路徑同名前綴（同目錄不同檔名）。"""
    files = {'.github/scripts/mine.py': '# 採用專案自己的腳本\n',
             'src/app.py': 'print("hi")\n', 'README.md': '# consumer\n'}
    for relative, text in files.items():
        (consumer / relative).parent.mkdir(parents=True, exist_ok=True)
        (consumer / relative).write_text(text, encoding='utf-8')
    return files


@pytest.fixture
def env(tmp_path):
    return git_env(tmp_path)


def test_install_registers_every_managed_asset_and_touches_nothing_else(tmp_path, env, capsys):
    consumer, rules, _, installed, _ = adopted_consumer(tmp_path, env)
    consumer_owned(consumer)
    before = tree_digests(consumer)
    rc, client = run_step(consumer, 'install')
    out = capsys.readouterr().out
    assert rc == 0, out
    after = tree_digests(consumer)
    manifest = json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    print('MANIFEST', json.dumps(manifest, ensure_ascii=False, indent=2))
    registered = {entry['path'] for entry in manifest['assets']}
    changed = {path for path in set(before) | set(after) if before.get(path) != after.get(path)}
    assert changed <= registered, sorted(changed - registered)          # 每個新增或被改寫的路徑都有登記
    assert registered <= set(after), sorted(registered - set(after))    # manifest 有項而樹上無該檔＝不成立
    for path in set(before) - registered:                               # 未登記的路徑逐一不變
        assert before[path] == after.get(path), path
    for entry in manifest['assets']:
        assert tuple(entry) == _adopt.ASSET_KEYS, entry                 # 每項恰四鍵、順序固定
        assert entry['ownership'] in _adopt.OWNERSHIPS, entry
    managed = {e['path'] for e in manifest['assets'] if e['ownership'] == _adopt.OWNERSHIPS[0]}
    assert managed == {*_adopt.MANAGED_ASSETS, _adopt.MANIFEST_PATH}, sorted(managed)
    assert manifest['source_commit'] == installed and len(installed) == 40
    assert [call for call in client.calls if call[0] in MUTATIONS] == [], client.calls
    print('INSTALL registered', sorted(registered), 'changed', sorted(changed),
          'source_commit', manifest['source_commit'])


def test_the_untouched_check_and_the_source_commit_have_negative_controls(tmp_path, env, capsys):
    """兩個負控（都必須會響）：① 樹上多一個未登記的路徑 ⇒ 不變式判準抓得到。
    ② rules root 換成非 submodule 的一般目錄 ⇒ `source_commit` 必須是 `null`；仍是 40 碼即判 install 在猜。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='c1')
    before = tree_digests(consumer)
    run_step(consumer, 'install')
    (consumer / 'stray.txt').write_text('未登記\n', encoding='utf-8')
    after = tree_digests(consumer)
    manifest = json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    registered = {entry['path'] for entry in manifest['assets']}
    changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
    assert not changed <= registered and 'stray.txt' in changed - registered
    print('NEGATIVE_CONTROL unregistered_path', sorted(changed - registered))
    plain = tmp_path / 'plain'
    plain.mkdir()
    framework_tree(plain / 'rules')
    (plain / '.wf').mkdir()
    (plain / '.wf/modules.json').write_text(json.dumps(
        {'modules': [], 'areas': ['APP'], 'project': None, 'rules': {'path': 'rules'}}), encoding='utf-8')
    git(plain, 'init', '-q', '-b', 'main', env=env)
    rc, _ = run_step(plain, 'install')
    capsys.readouterr()
    vendored = json.loads((plain / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    assert rc == 0 and vendored['source_commit'] is None, vendored['source_commit']
    assert 'source_commit' in vendored  # ⛔ 不省略該鍵
    print('NEGATIVE_CONTROL not_a_submodule source_commit', vendored['source_commit'])


def test_pin_comes_from_the_single_version_home(tmp_path, env, capsys):
    """A5 前半：`pin` 逐項等於 `cli/pyproject.toml` 的版本值，且掃描面內⛔ 無第二個版本值居所。"""
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env, name='c2')
    run_step(consumer, 'install')
    capsys.readouterr()
    version = tomllib.loads((rules / _adopt.VERSION_HOME).read_text(encoding='utf-8'))['project']['version']
    manifest = json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    pins = {entry['pin'] for entry in manifest['assets']}
    assert pins == {version}, (pins, version)
    print('PIN', sorted(pins), 'VERSION_HOME', _adopt.VERSION_HOME, '=', version)
    homes = [_adopt.VERSION_HOME] if VERSION_DECLARATION.search(
        (ROOT / _adopt.VERSION_HOME).read_text(encoding='utf-8')) else []
    for part in RULE_DIRS:
        for path in sorted((ROOT / part).rglob('*.md')):
            if VERSION_DECLARATION.search(path.read_text(encoding='utf-8')):
                homes.append(path.relative_to(ROOT).as_posix())
    assert homes == [_adopt.VERSION_HOME], homes  # 居所唯一
    print('VERSION_HOMES', homes)


def test_the_pin_comparison_is_effective(tmp_path, env, capsys):
    """負控（必須會響）：改掉 rules source 的版本值後，manifest 既有的 `pin` 就不再等於現行版本值。"""
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env, name='c3')
    run_step(consumer, 'install')
    capsys.readouterr()
    before = {e['pin'] for e in json.loads(
        (consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))['assets']}
    path = rules / _adopt.VERSION_HOME
    path.write_text(path.read_text(encoding='utf-8').replace(
        'version = "', 'version = "9.', 1), encoding='utf-8')
    now, _ = _adopt.framework_version(rules)
    assert now not in before, (now, before)
    print('NEGATIVE_CONTROL version_changed', sorted(before), '->', now)


@pytest.mark.parametrize('case,mutate,expected', [
    ('mixed_pin', lambda m: m['assets'][0].update(pin='0.0.1'), 'fail'),
    ('missing_pin', lambda m: m['assets'][0].update(pin=None), 'unknown'),
    ('empty_pin', lambda m: m['assets'][0].update(pin=''), 'unknown'),
])
def test_pins_of_aggregation_rules(tmp_path, env, capsys, case, mutate, expected):
    """core/adopt.md §2 的彙整規則：基數 >1 ⇒ fail；缺 `pin` 或非非空字串 ⇒ unknown。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name=f'c-{case}')
    run_step(consumer, 'install')
    capsys.readouterr()
    manifest = json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    assert _adopt.pins_of(manifest)[1] == 'ok'
    mutate(manifest)
    value, status, reason = _adopt.pins_of(manifest)
    assert status == expected and value is None, (case, status, value)
    assert 'Error' not in reason and 'Traceback' not in reason, reason
    print('PINS_OF', case, status, reason)


def test_pins_of_without_a_manifest_is_unknown():
    value, status, reason = _adopt.pins_of(None)
    assert (value, status, reason) == (None, 'unknown', _adopt.NO_MANIFEST)
    print('PINS_OF no_manifest', status, reason)
