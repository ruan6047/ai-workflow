"""WF-015 A31 與 A32：`snapshot --adopt deactivate` 的三類差異判定與刪除面封閉。
消費 core/adopt.md §2（所有權分類、`path` 兩類文法、片段區間）／§5（deactivate／remove 邊界）。

所有權分類由 `wf.verbs._adopt.OWNERSHIPS` `import` 取得、⛔ 不重打；mutation 原語集合由
`wf.gh.writes.MUTATIONS` 枚舉。掃描面＝合成 consumer 樹（`core/adopt.md` §0）；明示排除 `.git/`。
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
from .test_adopt_fragments import CONSUMER_JOB, carrier_with
from .test_adopt_manifest import outside_fragments, write_manifest_file
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


def carrier_names(manifest):
    """{承載檔: [片段名…]}，由 manifest 的 framework-managed 片段項算出。"""
    found = {}
    for entry in _adopt.entries_of(manifest, _adopt.OWNERSHIPS[0]):
        pair = _adopt.fragment_of(entry['path'])
        if pair is not None:
            found.setdefault(pair[0], []).append(pair[1])
    return found


def classify(consumer, manifest, before, after, texts):
    """差異逐條歸入 core/adopt.md §5 的三類；回 {類別: [路徑…]}，⛔ 無法歸類者進 `第四類`。
    `texts`＝deactivate **之前**各承載檔的逐字內容：片段類要比的是「把片段區間切掉後的前像」與後像，
    ⛔ 不得拿後像自己跟自己比（那恆為真、零資訊）。"""
    managed = {e['path'] for e in _adopt.entries_of(manifest, _adopt.OWNERSHIPS[0])}
    whole = {p for p in managed if _adopt.fragment_of(p) is None}
    carriers = carrier_names(manifest)
    found = {'整檔': [], '片段': [], '未動': [], '第四類': []}
    for path in sorted(set(before) | set(after)):
        if before.get(path) == after.get(path):
            found['未動'].append(path)
        elif path in whole and path not in after:
            found['整檔'].append(path)
        elif path in carriers and path in after and path in before:
            expected = outside_fragments(texts[path], carriers[path])
            actual = (consumer / path).read_text(encoding='utf-8')
            found['片段' if expected == actual else '第四類'].append(path)
        else:
            found['第四類'].append(path)
    return found


def test_removal_is_classified_by_ownership_and_granularity(tmp_path, env, capsys):
    """A31：整檔項路徑消失、片段項只動片段區間、consumer-owned 與未登記路徑逐一不變、⛔ 無第四類。"""
    consumer, _ = adopted(tmp_path, env, capsys, 'a31')
    manifest = json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    managed = {e['path'] for e in _adopt.entries_of(manifest, _adopt.OWNERSHIPS[0])}
    owned = {e['path'] for e in _adopt.entries_of(manifest, _adopt.OWNERSHIPS[1])}
    assert managed and owned and _adopt.CONFIG_PATH in owned, (sorted(managed), sorted(owned))
    assert any(path.startswith(_adopt.STAGE_DIR) for path in owned), sorted(owned)
    assert any(_adopt.fragment_of(p) for p in managed), sorted(managed)   # 片段項確實在母體內
    before = digests(consumer)
    texts = {path: (consumer / path).read_text(encoding='utf-8') for path in carrier_names(manifest)}
    rc, out, client = deactivate(consumer, capsys)
    after = digests(consumer)
    assert rc == 0, out
    found = classify(consumer, manifest, before, after, texts)
    assert found['第四類'] == [], found
    whole = {p for p in managed if _adopt.fragment_of(p) is None}
    assert set(found['整檔']) == whole, (found['整檔'], sorted(whole))
    for path in owned | (set(before) - managed - whole):
        assert path in after and after[path] == before[path], path
    assert not (consumer / _adopt.MANIFEST_PATH).parent.exists()   # 清空後的 .wf/adopt 一併移除
    assert (consumer / _adopt.CONFIG_PATH).is_file() and (consumer / _adopt.STAGE_DIR).is_dir()
    assert [call for call in client.calls if call[0] in MUTATIONS] == [], client.calls
    print('A31 classes', {k: v for k, v in found.items() if k != '未動'}, '未動', len(found['未動']))


def test_fragment_removal_keeps_the_rest_of_the_carrier(tmp_path, env, capsys):
    """A31②：承載檔在 install 之前已存在時，deactivate 只動片段區間、其餘位元組逐一相等。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='a31-frag')
    before = carrier_with(consumer, CONSUMER_JOB)
    for step in ('install', 'bootstrap'):
        assert main(['--project-root', str(consumer), 'snapshot', '--adopt', step],
                    client=FakeGhClient(), root=None, env={}) == 0
    capsys.readouterr()
    landed = (consumer / _adopt.CARRIER).read_text(encoding='utf-8')
    assert set(_adopt.FRAGMENTS) <= set(_adopt.job_names(landed)), landed
    manifest = json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    assert _adopt.CARRIER in carrier_names(manifest), manifest
    assert _adopt.CARRIER not in {e['path'] for e in
                                  _adopt.entries_of(manifest, _adopt.OWNERSHIPS[0])
                                  if _adopt.fragment_of(e['path']) is None}
    tree_before, texts = digests(consumer), {_adopt.CARRIER: landed}
    rc, out, _ = deactivate(consumer, capsys)
    assert rc == 0, out
    found = classify(consumer, manifest, tree_before, digests(consumer), texts)
    assert found['第四類'] == [] and _adopt.CARRIER in found['片段'], found
    assert (consumer / _adopt.CARRIER).read_bytes() == before
    assert _adopt.job_names((consumer / _adopt.CARRIER).read_text(encoding='utf-8')) == ('mine',)
    print('A31 fragment_only', len(before), 'bytes restored')


def test_the_boundary_is_decided_only_by_the_ownership_field(tmp_path, env, capsys):
    """負控（必須會響）：把一個 consumer 自有檔改標成 framework-managed 後它必須被移除
    （⇒ 判準真的是 `ownership` 欄，⛔ 不是路徑前綴、⛔ 不是副檔名）。"""
    consumer, _ = adopted(tmp_path, env, capsys, 'a31-neg')
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


# ── A32：刪除面封閉在 project_root 之內 ──────────────────────────────────────────
def escape_shapes(tmp_path, consumer):
    """三種越界形狀：`..`、絕對路徑、父目錄符號連結。回 {案例: (登記值, 目標檔)}。"""
    outside = tmp_path / 'outside'
    outside.mkdir(exist_ok=True)
    victim = outside / 'secret.txt'
    victim.write_text('consumer 根之外的檔\n', encoding='utf-8')
    link = consumer / 'link'
    if not link.exists():
        link.symlink_to(outside, target_is_directory=True)
    return {'dotdot': (f'../{outside.name}/{victim.name}', victim),
            'absolute': (str(victim), victim),
            'symlink': (f'link/{victim.name}', victim)}


@pytest.mark.parametrize('case', ['dotdot', 'absolute', 'symlink'])
def test_deletion_is_confined_to_the_project_root(tmp_path, env, capsys, case):
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name=f'a32-{case}')
    declared, victim = escape_shapes(tmp_path, consumer)[case]
    write_manifest_file(consumer, {
        'schema': _adopt.MANIFEST_SCHEMA, 'source_commit': None,
        'assets': [_adopt.asset_entry(declared, _adopt.OWNERSHIPS[0], 'sha256:0', '1.0.0')]})
    rc, out, _ = deactivate(consumer, capsys)
    assert rc == 0, out
    assert victim.is_file(), (case, declared)                  # root 之外的檔仍在
    explained = [line for line in out.splitlines() if _adopt.OUTSIDE_ROOT in line]
    assert explained, (case, out)                              # 印一行說明
    assert _adopt.confined(consumer, declared) is None, (case, declared)
    print('A32', case, declared, explained)


def test_the_confinement_check_has_a_negative_control(tmp_path, env):
    """負控（必須會響）：root 之內的一般相對路徑必須被判為可刪，否則本判準恆為真、零資訊。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='a32-neg')
    inside = _adopt.MANAGED_ASSETS[0]
    assert _adopt.confined(consumer, inside) is not None, inside
    assert _adopt.confined(consumer, '..') is None
    print('NEGATIVE_CONTROL confined inside', inside, '-> deletable')


def test_the_boundary_has_a_named_home_in_the_rules_body():
    """該邊界在規則本體解析得到一個居所（同 A1 的居所解析法，⛔ 不用字面 grep）。"""
    rules = FilesystemRulesSource(ROOT, Provenance('cli', '--rules-root'))
    homes = [(path, heading) for path in rules.iter_assets('core/*.md')
             for heading, body in sections(rules.read_text(path))
             if 'deactivate' in heading and _adopt.OWNERSHIPS[1] in body]
    assert len(homes) == 1, homes
    path, heading = homes[0]
    parts = dict(sections(rules.read_text(path)))
    body = parts[heading]
    assert '零刪除、零改寫' in body and _adopt.OWNERSHIPS[0] in body, body
    registry, = [h for h in parts if h.endswith('manifest')]  # manifest 的唯一居所另有一節
    assert _adopt.MANIFEST_PATH in parts[registry], parts[registry]
    print('DEACTIVATE_HOME', f'{path}#{heading}', 'MANIFEST_HOME', f'{path}#{registry}')
