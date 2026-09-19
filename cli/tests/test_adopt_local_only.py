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
