"""WF-015 A8（非阻擋切片 S5）：`snapshot --adopt deactivate` 只移除 manifest 內分類為
framework-managed 的項，對 consumer-owned 的 `.wf/` 零刪除、零改寫，且對遠端零 mutation。
消費 core/adopt.md §2（所有權分類）／§5（deactivate／remove 邊界）。

所有權分類由 `wf.verbs._adopt.OWNERSHIPS` `import` 取得、⛔ 不重打；mutation 原語集合由
`wf.gh.writes.MUTATIONS` 枚舉。掃描面＝合成 consumer 樹；明示排除 `.git/`。
"""
import json
from pathlib import Path

import pytest

from wf.context import FilesystemRulesSource, Provenance
from wf.gh.writes import MUTATIONS
from wf.verbs import _adopt
from wf.verbs.main import main
from .fakes import FakeGhClient
from .test_adopt_gitlink import adopted_consumer
from .test_adoption_contract import sections
from .test_compose_schema import ROOT
from .test_context_roots import git_env


@pytest.fixture
def env(tmp_path):
    return git_env(tmp_path)


def digests(root):
    root = Path(root)
    return {path.relative_to(root).as_posix(): _adopt.digest_of(path.read_bytes())
            for path in sorted(root.rglob('*'))
            if path.is_file() and '.git' not in path.relative_to(root).parts}


def adopted(tmp_path, env, capsys, name):
    consumer, rules, _, _, _ = adopted_consumer(tmp_path, env, name=name)
    (consumer / 'src').mkdir(exist_ok=True)
    (consumer / 'src/app.py').write_text('print("consumer")\n', encoding='utf-8')
    for step in ('install', 'bootstrap'):
        assert main(['--project-root', str(consumer), 'snapshot', '--adopt', step],
                    client=FakeGhClient(), root=None, env={}) == 0
    capsys.readouterr()
    return consumer, rules


def deactivate(consumer, capsys):
    client = FakeGhClient()
    rc = main(['--project-root', str(consumer), 'snapshot', '--adopt', 'deactivate'],
              client=client, root=None, env={})
    return rc, capsys.readouterr().out, client


def test_deactivate_removes_only_managed_assets(tmp_path, env, capsys):
    consumer, _ = adopted(tmp_path, env, capsys, 'off')
    manifest = json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    managed = {e['path'] for e in manifest['assets'] if e['ownership'] == _adopt.OWNERSHIPS[0]}
    owned = {e['path'] for e in manifest['assets'] if e['ownership'] == _adopt.OWNERSHIPS[1]}
    assert managed and owned and _adopt.CONFIG_PATH in owned, (sorted(managed), sorted(owned))
    assert any(path.startswith(_adopt.STAGE_DIR) for path in owned), sorted(owned)
    before = digests(consumer)
    rc, out, client = deactivate(consumer, capsys)
    after = digests(consumer)
    assert rc == 0, out
    assert set(before) - set(after) == managed, sorted(set(before) - set(after))
    assert set(after) - set(before) == set(), sorted(set(after) - set(before))
    for path in set(after):  # 留下來的每一個檔逐字未被改寫
        assert after[path] == before[path], path
    assert not (consumer / _adopt.MANIFEST_PATH).parent.exists()  # 清空後的 .wf/adopt 一併移除
    assert (consumer / _adopt.CONFIG_PATH).is_file() and (consumer / _adopt.STAGE_DIR).is_dir()
    assert [call for call in client.calls if call[0] in MUTATIONS] == [], client.calls
    print('DEACTIVATE removed', sorted(managed), 'kept', len(after), 'mutations', 0)
    print('DEACTIVATE stdout', [line for line in out.splitlines() if line.startswith(_adopt.STEP_PREFIX)])


def test_the_boundary_is_decided_only_by_the_ownership_field(tmp_path, env, capsys):
    """負控（必須會響）：把一個 consumer 自有檔改標成 framework-managed 後它必須被移除
    （⇒ 判準真的是 `ownership` 欄，⛔ 不是路徑前綴、⛔ 不是副檔名）。"""
    consumer, _ = adopted(tmp_path, env, capsys, 'off-neg')
    path = consumer / _adopt.MANIFEST_PATH
    manifest = json.loads(path.read_text(encoding='utf-8'))
    victim, = [e for e in manifest['assets'] if e['path'] == _adopt.CONFIG_PATH]
    victim['ownership'] = _adopt.OWNERSHIPS[0]
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert (consumer / _adopt.CONFIG_PATH).is_file()
    rc, out, _ = deactivate(consumer, capsys)
    assert rc == 0 and not (consumer / _adopt.CONFIG_PATH).exists(), out
    print('NEGATIVE_CONTROL relabelled', _adopt.CONFIG_PATH, '-> removed')


def test_deactivate_without_a_manifest_deletes_nothing(tmp_path, env, capsys):
    """未登記的路徑⛔ 不在射程內：manifest 缺席時該次執行零刪除並印一行說明。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='off-bare')
    before = digests(consumer)
    rc, out, client = deactivate(consumer, capsys)
    assert rc == 0 and digests(consumer) == before
    assert any(_adopt.NO_MANIFEST in line for line in out.splitlines()), out
    assert [call for call in client.calls if call[0] in MUTATIONS] == [], client.calls
    print('DEACTIVATE no_manifest zero_deletion', len(before))


def test_the_boundary_has_a_named_home_in_the_rules_body():
    """A8 後半：該邊界在規則本體解析得到一個居所（同 A1 的居所解析法，⛔ 不用字面 grep）。"""
    rules = FilesystemRulesSource(ROOT, Provenance('cli', '--rules-root'))
    homes = [(path, heading) for path in rules.iter_assets('core/*.md')
             for heading, body in sections(rules.read_text(path))
             if 'deactivate' in heading and _adopt.OWNERSHIPS[1] in body]
    assert len(homes) == 1, homes
    path, heading = homes[0]
    parts = dict(sections(rules.read_text(path)))
    body = parts[heading]
    assert '零刪除、零改寫' in body and _adopt.OWNERSHIPS[0] in body, body
    registry, = [h for h in parts if 'manifest' in h]  # manifest 的唯一居所另有一節
    assert _adopt.MANIFEST_PATH in parts[registry], parts[registry]
    print('DEACTIVATE_HOME', f'{path}#{heading}', 'MANIFEST_HOME', f'{path}#{registry}')
