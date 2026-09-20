"""WF-015：`snapshot --adopt deactivate` 的保留面、刪除面與 `ADOPTION.md` 的退場節。
消費 core/adopt.md §2（所有權分類、單一 `path` 文法、legacy 判定）／§5（deactivate／remove 邊界）。

所有權分類由 `wf.verbs._adopt.OWNERSHIPS` `import` 取得、⛔ 不重打；mutation 原語集合由
`wf.gh.writes.MUTATIONS` 枚舉。掃描面＝合成 consumer 樹（`core/adopt.md` §0）；明示排除 `.git/`。
全樹差異只有一類：`framework-managed` 的**整檔**登記路徑消失。legacy 登記項與其承載檔、越界登記項、
符號連結與完全未登記的路徑一律位元組不變——CLI ⛔ 不對採用者既有檔案做任何內容移除或改寫。
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
from .test_adopt_manifest import write_manifest_file
from .test_adoption_contract import sections
from .test_compose_schema import ROOT
from .test_context_roots import git_env

EXIT_CATEGORIES = ('由 CLI 移除者', '由 AI 依證據處理者', '一律保留者')
ALWAYS_KEPT = ('Issue', '留言', 'Project 資料', 'ruleset', _adopt.OWNERSHIPS[1])
LEGACY_CARRIER = '.github/workflows/consumer.yml'
LEGACY_PATH = f'{LEGACY_CARRIER}#secret-scan'
CARRIER_BODY = """name: consumer own
on:
  push:

jobs:
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
"""


@pytest.fixture
def env(tmp_path):
    return git_env(tmp_path)


def digests(root):
    """全樹 (路徑 → 內容摘要或連結目標)；明示排除 `.git/`。⛔ 不比對 mtime。"""
    root, found = Path(root), {}
    for path in sorted(Path(root).rglob('*')):
        relative = path.relative_to(root)
        if '.git' in relative.parts:
            continue
        if path.is_symlink():
            found[relative.as_posix()] = 'symlink:' + str(Path(path).readlink())
        elif path.is_file():
            found[relative.as_posix()] = _adopt.digest_of(path.read_bytes())
    return found


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


def whole_file_managed(manifest):
    return {entry['path'] for entry in _adopt.managed_entries(manifest)}


def test_removal_is_classified_by_ownership_and_granularity(tmp_path, env, capsys):
    """整檔 `framework-managed` 項的路徑消失；`consumer-owned` 與未登記路徑逐一不變、⛔ 無第四類。"""
    consumer, _ = adopted(tmp_path, env, capsys, 'ownership')
    manifest = json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    managed, owned = whole_file_managed(manifest), {
        e['path'] for e in _adopt.entries_of(manifest, _adopt.OWNERSHIPS[1])}
    assert managed and owned and _adopt.CONFIG_PATH in owned, (sorted(managed), sorted(owned))
    assert any(path.startswith(_adopt.STAGE_DIR) for path in owned), sorted(owned)
    assert set(_adopt.INSTALL_SET) <= managed, (sorted(managed), list(_adopt.INSTALL_SET))
    before = digests(consumer)
    rc, out, client = deactivate(consumer, capsys)
    after = digests(consumer)
    assert rc == 0, out
    gone = {path for path in before if path not in after}
    # 差異恰兩類（`core/adopt.md` §5）：（一）摘要相符的 framework-managed 整檔登記路徑；
    # （二）控制檔集合（具名承接、⛔ 非經登記移除——方案 A 下它⛔ 不自登記）。
    expected = managed | set(_adopt.CONTROL_SET)
    assert gone == expected, sorted(gone ^ expected)
    assert not (set(_adopt.CONTROL_SET) & managed), sorted(managed)
    assert not [path for path in after if after[path] != before.get(path)], sorted(after)
    assert not (consumer / _adopt.MANIFEST_PATH).parent.exists()  # 清空後的 .wf/adopt 一併移除
    assert (consumer / _adopt.CONFIG_PATH).is_file() and (consumer / _adopt.STAGE_DIR).is_dir()
    assert [call for call in client.calls if call[0] in MUTATIONS] == [], client.calls
    print('DEACTIVATE gone', sorted(gone), 'kept', len(after))


def preserved_tree(tmp_path, env, capsys, name):
    """一棵含全部保留面起點的合成樹：legacy 項與其承載檔、樹內符號連結、未登記路徑、
    三種越界登記項，外加一個**一般整檔登記項**當正控（它必須真的被移除）。"""
    consumer, _ = adopted(tmp_path, env, capsys, name)
    (consumer / LEGACY_CARRIER).parent.mkdir(parents=True, exist_ok=True)
    (consumer / LEGACY_CARRIER).write_text(CARRIER_BODY, encoding='utf-8')
    outside = tmp_path / f'outside-{name}'
    outside.mkdir(exist_ok=True)
    victim = outside / 'secret.txt'
    victim.write_text('consumer 根之外的檔\n', encoding='utf-8')
    (consumer / 'link').symlink_to(outside, target_is_directory=True)
    (consumer / 'own.txt').write_text('完全未登記\n', encoding='utf-8')
    (consumer / 'linked.yml').symlink_to(consumer / LEGACY_CARRIER)
    manifest = json.loads((consumer / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    manifest['assets'] = [*manifest['assets'], *(
        _adopt.asset_entry(path, _adopt.OWNERSHIPS[0], 'sha256:0', '0.0.0') for path in (
            LEGACY_PATH, 'linked.yml', f'../{outside.name}/{victim.name}', str(victim),
            f'link/{victim.name}'))]
    write_manifest_file(consumer, manifest)
    return consumer, manifest, victim


def test_the_preserved_surface_survives_and_the_plain_entry_does_not(tmp_path, env, capsys):
    """legacy 項與其承載檔、樹內符號連結與其指向物、越界三形狀、未登記路徑一律不變；
    正控＝一般整檔登記項確實被移除（⇒ 本判準⛔ 非恆零刪除）。"""
    consumer, _, victim = preserved_tree(tmp_path, env, capsys, 'preserve')
    control = _adopt.INSTALL_SET[0]
    keep = {LEGACY_CARRIER, 'own.txt', 'linked.yml', 'link'}
    before = digests(consumer)
    assert (consumer / control).is_file(), control
    rc, out, client = deactivate(consumer, capsys)
    after = digests(consumer)
    assert rc == 0, out
    assert not (consumer / control).exists(), control            # 正控：確有刪除
    for path in keep:
        assert after.get(path) == before.get(path), (path, before.get(path), after.get(path))
    assert victim.is_file() and victim.read_text(encoding='utf-8') == 'consumer 根之外的檔\n'
    assert (consumer / LEGACY_CARRIER).read_text(encoding='utf-8') == CARRIER_BODY
    listed = [line for line in out.splitlines() if _adopt.LEGACY_KEPT in line]
    assert [line for line in listed if LEGACY_PATH in line], out
    assert all(_adopt.EXIT_SECTION in line for line in listed), listed
    assert [line for line in out.splitlines() if _adopt.OUTSIDE_ROOT in line], out
    assert [line for line in out.splitlines() if _adopt.SYMLINK_PATH in line], out
    assert [call for call in client.calls if call[0] in MUTATIONS] == [], client.calls
    print('PRESERVED', sorted(keep), 'legacy_lines', listed, 'control_removed', control)


def test_the_boundary_is_decided_only_by_the_ownership_field(tmp_path, env, capsys):
    """負控（必須會響）：把一個 consumer 自有檔改標成 framework-managed 後它必須被移除
    （⇒ 判準真的是 `ownership` 欄，⛔ 不是路徑前綴、⛔ 不是副檔名）。"""
    consumer, _ = adopted(tmp_path, env, capsys, 'ownership-neg')
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


# ── 刪除面封閉在 project_root 之內 ───────────────────────────────────────────────
def test_the_confinement_check_has_a_negative_control(tmp_path, env):
    """負控（必須會響）：root 之內的一般相對路徑必須被判為可刪，否則本判準恆為真、零資訊。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='confine-neg')
    inside = _adopt.INSTALL_SET[0]
    assert _adopt.confined(consumer, inside) is not None, inside
    assert _adopt.confined(consumer, '..') is None
    print('NEGATIVE_CONTROL confined inside', inside, '-> deletable')


def test_the_boundary_has_a_named_home_in_the_rules_body():
    """該邊界在規則本體解析得到一個居所（同 step 的居所解析法，⛔ 不用字面 grep）。"""
    rules = FilesystemRulesSource(ROOT, Provenance('cli', '--rules-root'))
    homes = [(path, heading) for path in rules.iter_assets('core/*.md')
             for heading, body in sections(rules.read_text(path))
             if 'deactivate' in heading and _adopt.OWNERSHIPS[1] in body]
    assert len(homes) == 1, homes
    path, heading = homes[0]
    parts = dict(sections(rules.read_text(path)))
    body = parts[heading]
    assert '逐一相等' in body and _adopt.OWNERSHIPS[0] in body, body
    registry, = [head for head in parts if 'manifest' in head]  # manifest 的唯一居所另有一節
    assert _adopt.MANIFEST_PATH in parts[registry], parts[registry]
    print('DEACTIVATE_HOME', f'{path}#{heading}', 'MANIFEST_HOME', f'{path}#{registry}')


def test_the_exit_section_lists_three_categories():
    """`ADOPTION.md` 有一個具名的退場節，逐字分三類；「一律保留者」列出五種一律保留的對象。"""
    adoption = dict(sections((ROOT / 'ADOPTION.md').read_text(encoding='utf-8')))
    heading, = [head for head in adoption if head.endswith('退場')]
    body = adoption[heading]
    for label in EXIT_CATEGORIES:
        assert f'**{label}**' in body, (label, body)
    kept = [line for line in body.splitlines() if line.startswith(f'- **{EXIT_CATEGORIES[2]}**')]
    assert len(kept) == 1, kept
    for token in ALWAYS_KEPT:
        assert token in kept[0], (token, kept[0])
    number = heading.split(' ')[0]
    assert _adopt.EXIT_SECTION.endswith(f'§{number}'), (heading, _adopt.EXIT_SECTION)
    print('EXIT_SECTION', f'ADOPTION.md#{heading}', 'categories', list(EXIT_CATEGORIES))
