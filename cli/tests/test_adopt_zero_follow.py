"""WF-015：零跟隨判準**收斂成單一函式**（`_adopt.follows_symlink`，逐字路徑含 leaf 自身）後，三個
居所對同一形狀給**同一個**答案：落地面（`install` 的 `_occupied`）、登記面（`bootstrap` 的 `owned`）、
移除面（`deactivate` 的登記項迴圈與控制檔迴圈）。消費 core/adopt.md §2／§5、core/verbs.md §1
`snapshot` 列（硬擋欄＝「—」：rc 恆 0、⛔ 不 raise）。

本檔存在的理由是判準**曾經分居兩處**：登記面用裸 `is_file()`（跟隨 leaf 連結）、控制檔迴圈完全⛔ 無守門，
於是同一形狀在 `install` 是「零寫入」、在 `bootstrap` 是「沿用並登記」，而 `deactivate` 會刪到樹外。
⇒ 每個測試都同時對**兩個以上的居所**斷言同一形狀，⛔ 不逐動詞各測各的。

合成樹在 `tmp_path` 內（`core/adopt.md` §0 逐字「⛔ 不依賴本 repo 歷史存在」），明示排除 `.git/`。
摘要口徑走 `_adopt.digest_of`（`import` 使用、⛔ 不重打）。
"""
import json
from pathlib import Path

import pytest

from wf.verbs import _adopt
from wf.verbs.main import main
from .fakes import FakeGhClient
from .test_adopt_gitlink import adopted_consumer
from .test_context_roots import git_env


@pytest.fixture
def env(tmp_path):
    return git_env(tmp_path)


def snapshot_tree(root):
    """全樹 (路徑 → 內容摘要 或 `symlink:<目標>`)；明示排除 `.git/`。⛔ 不比對 mtime。"""
    root, found = Path(root), {}
    for path in sorted(Path(root).rglob('*')):
        relative = path.relative_to(root).as_posix()
        if '.git' in path.relative_to(root).parts:
            continue
        if path.is_symlink():
            found[relative] = 'symlink:' + str(Path(path).readlink())
        elif path.is_file():
            found[relative] = _adopt.digest_of(path.read_bytes())
        else:
            found[relative] = 'dir'
    return found


def step(root, name, capsys):
    rc = main(['--project-root', str(root), 'snapshot', '--adopt', name],
              client=FakeGhClient(), root=None, env={})
    return rc, capsys.readouterr().out


def owned_paths(root):
    manifest = json.loads((Path(root) / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))
    return manifest, {entry['path'] for entry in _adopt.entries_of(manifest, _adopt.OWNERSHIPS[1])}


# ── 判準本身：一個函式、四種命中形狀、三種負控 ────────────────────────────────────
def test_the_zero_follow_predicate_is_one_function_and_covers_the_leaf(tmp_path):
    """`follows_symlink` 是**唯一**的零跟隨判準：leaf 連結（活的與斷的）、父路徑連結皆命中；
    一般檔、目錄、⛔ 不存在的路徑皆⛔ 不命中。裸 `is_file()` 對「leaf 是活連結」給相反答案——
    本測試同時把那個相反答案釘住，故判準若退回 `is_file()` 本檔即轉紅。"""
    root = tmp_path / 'tree'
    (root / 'real').mkdir(parents=True)
    (root / 'real/file.txt').write_text('payload\n', encoding='utf-8')
    (root / 'plain.txt').write_text('plain\n', encoding='utf-8')
    (root / 'adir').mkdir()
    (root / 'live-link').symlink_to(root / 'real/file.txt')
    (root / 'dead-link').symlink_to(root / 'real/missing.txt')
    (root / 'dir-link').symlink_to(root / 'real')

    hits = {name: _adopt.follows_symlink(root, name)
            for name in ('live-link', 'dead-link', 'dir-link/file.txt',
                         'plain.txt', 'adir', 'absent.txt')}
    assert hits == {'live-link': True, 'dead-link': True, 'dir-link/file.txt': True,
                    'plain.txt': False, 'adir': False, 'absent.txt': False}, hits
    # 負控：裸 `is_file()` 對 live-link 回 True（＝跟隨了連結），那正是⛔ 不得用它判登記面的理由。
    assert (root / 'live-link').is_file() is True
    assert _adopt.digest_of((root / 'live-link').read_bytes()) == \
        _adopt.digest_of((root / 'real/file.txt').read_bytes())
    print('ZERO_FOLLOW hits', hits)


# ── 登記面與落地面：同一形狀，兩動詞同一答案 ──────────────────────────────────────
def test_bootstrap_does_not_register_a_leaf_symlink_and_agrees_with_install(tmp_path, env, capsys):
    """`.wf/modules.json` 與 `.wf/stages/<階段>.md` 是**指向樹內一般檔**的 leaf 符號連結時：
    `bootstrap` 零寫入、只交未完成項、**⛔ 不登記**，且⛔ 不對它印「沿用」；leaf 執行後仍是符號連結、
    指向物位元組不變。負控＝同一次執行裡留一個真的一般檔，它必須照樣「沿用」並登記。
    （A2 逐字「三條逐次可測、對 install 與 bootstrap 同形」：`install` 對同形狀的答案在下一個斷言。）"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='leaflink')
    # 指向物刻意是一份**合法**設定：⛔ 不讓「連結指向⛔ 不可解析的內容」變成本測試的真正起因——
    # 那會讓 CLI 在 context 層就失敗、根本走不到登記面，形狀也就沒被測到。
    pointee = consumer / 'pointee.json'
    pointee.write_text((consumer / _adopt.CONFIG_PATH).read_text(encoding='utf-8'), encoding='utf-8')
    pointee_digest = _adopt.digest_of(pointee.read_bytes())

    rc, _ = step(consumer, 'bootstrap', capsys)          # 先取得階段骨架路徑的封閉集合
    assert rc == 0
    _, first_owned = owned_paths(consumer)
    stages = sorted(path for path in first_owned if path.startswith(_adopt.STAGE_DIR))
    assert len(stages) >= 2, stages
    linked_stage, control_stage = stages[0], stages[1]

    # 重置登記面後植入形狀：兩個 leaf 連結（modules.json 與一個階段檔）＋一個留著的一般檔當負控。
    (consumer / _adopt.MANIFEST_PATH).unlink()
    for relative in (_adopt.CONFIG_PATH, linked_stage):
        (consumer / relative).unlink()
        (consumer / relative).symlink_to(pointee)

    rc, out = step(consumer, 'bootstrap', capsys)
    assert rc == 0, out
    manifest, owned = owned_paths(consumer)
    # ① ⛔ 不登記：兩個連結路徑都不在 consumer-owned 集合內。
    assert not ({_adopt.CONFIG_PATH, linked_stage} & owned), (sorted(owned), linked_stage)
    # ② 負控：同一次執行裡的一般檔照樣登記並印「沿用」——證明本次⛔ 不是整批⛔ 不登記。
    assert control_stage in owned, sorted(owned)
    assert f'{control_stage}・沿用' in out, out
    # ③ ⛔ 不得對連結路徑印「沿用」，且必須交未完成項。
    for relative in (_adopt.CONFIG_PATH, linked_stage):
        assert f'{relative}・沿用' not in out, (relative, out)
        assert f'{_adopt.PENDING_MARK}・source=' in out and relative in out, (relative, out)
    # ④ 零跟隨的直接證據：⛔ 無任一登記項的 digest 等於**指向物**內容的 sha256。
    assert not [entry for entry in manifest['assets'] if entry['digest'] == pointee_digest], manifest
    # ⑤ 零寫入：leaf 仍是符號連結、指向物位元組不變。
    for relative in (_adopt.CONFIG_PATH, linked_stage):
        assert (consumer / relative).is_symlink(), relative
    assert _adopt.digest_of(pointee.read_bytes()) == pointee_digest
    print('BOOTSTRAP leaf-link not registered', sorted(owned))


def test_install_gives_the_same_answer_as_bootstrap_on_a_leaf_symlink(tmp_path, env, capsys):
    """同一形狀（資產目標路徑是指向樹內一般檔的 leaf 連結）在 `install` 也是零寫入、⛔ 不登記。
    兩動詞的答案由**同一個** `follows_symlink` 給出 ⇒ ⛔ 不可能再出現「一邊零寫入、一邊沿用登記」。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='installlink')
    pointee = consumer / 'pointee.txt'
    pointee.write_text('pointee\n', encoding='utf-8')
    target = _adopt.INSTALL_SET[0]
    (consumer / target).parent.mkdir(parents=True, exist_ok=True)
    (consumer / target).symlink_to(pointee)
    before = snapshot_tree(consumer)

    rc, out = step(consumer, 'install', capsys)
    manifest, _ = owned_paths(consumer)
    assert rc == 0, out
    assert target not in {entry['path'] for entry in _adopt.managed_entries(manifest)}, manifest
    assert (consumer / target).is_symlink() and before[target] == snapshot_tree(consumer)[target]
    assert _adopt.follows_symlink(consumer, target) is True
    # 負控：同一次 install 的另一個資產目標是乾淨起點 ⇒ 它必須真的落地並登記。
    clean = _adopt.INSTALL_SET[1]
    assert clean in {entry['path'] for entry in _adopt.managed_entries(manifest)}, manifest
    print('INSTALL leaf-link skipped', target, 'landed', clean)


# ── 移除面：控制檔迴圈與登記項迴圈共用同一組守門 ──────────────────────────────────
def adopted(tmp_path, env, capsys, name):
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name=name)
    for name_ in ('install', 'bootstrap'):
        assert step(consumer, name_, capsys)[0] == 0
    return consumer


@pytest.mark.parametrize('shape', ('adopt-dir-link', 'adopt-dir-link-manifest-only',
                                   'wf-dir-link', 'manifest-leaf-link'))
def test_deactivate_never_deletes_outside_the_project_root_through_the_control_file(
        tmp_path, env, capsys, shape):
    """控制檔集合的移除面接上與登記項迴圈**同一組**守門（`confined` 封閉面＋`follows_symlink` 零跟隨）。
    四起點：`.wf/adopt` 連樹外目錄／該目錄內僅存 manifest／整個 `.wf` 連樹外／leaf manifest 連樹外。
    每一起點都斷言：rc=0、⛔ 不 raise（`core/verbs.md` §1 snapshot 硬擋欄逐字「—」）、**樹外全樹位元組
    逐一不變**、且控制檔那一行是 `OUTSIDE_ROOT` 或 `SYMLINK_PATH` 其中之一、⛔ 不是「已移除」。"""
    consumer = adopted(tmp_path, env, capsys, f'deact-{shape}')
    outside = tmp_path / f'outside-{shape}'
    outside.mkdir()
    (outside / 'consumer-private.txt').write_text('private\n', encoding='utf-8')
    control = consumer / _adopt.MANIFEST_PATH
    payload = control.read_text(encoding='utf-8')

    if shape == 'adopt-dir-link':
        (outside / 'manifest.json').write_text(payload, encoding='utf-8')
        control.unlink()
        control.parent.rmdir()
        control.parent.symlink_to(outside)
    elif shape == 'adopt-dir-link-manifest-only':
        (outside / 'consumer-private.txt').unlink()      # 樹外只剩 manifest ⇒ 刪完會觸發 rmdir
        (outside / 'manifest.json').write_text(payload, encoding='utf-8')
        control.unlink()
        control.parent.rmdir()
        control.parent.symlink_to(outside)
    elif shape == 'wf-dir-link':
        # 整棵 `.wf` 搬到樹外再以連結接回：內容**整份**搬過去（⛔ 不只搬 manifest），否則 CLI 會在
        # context 層因設定缺席而先失敗，形狀就沒被測到。
        (consumer / '.wf').rename(outside / 'wf')
        (consumer / '.wf').symlink_to(outside / 'wf')
    else:
        (outside / 'manifest.json').write_text(payload, encoding='utf-8')
        control.unlink()
        control.symlink_to(outside / 'manifest.json')

    before = snapshot_tree(outside)
    rc, out = step(consumer, 'deactivate', capsys)       # ⛔ 不得 raise：本層 rc 恆 0
    assert rc == 0, out
    assert snapshot_tree(outside) == before, (shape, before, snapshot_tree(outside))
    line = [text for text in out.splitlines() if text.endswith(
        f'{_adopt.MANIFEST_PATH}・{_adopt.OUTSIDE_ROOT}')
        or text.endswith(f'{_adopt.MANIFEST_PATH}・{_adopt.SYMLINK_PATH}')]
    assert line, out
    assert '已移除（控制檔具名承接）' not in out, out
    print('DEACTIVATE control guarded', shape, line)


def test_deactivate_does_not_claim_absent_when_the_registered_path_is_a_directory(
        tmp_path, env, capsys):
    """存在性判準住 `on_tree`：登記路徑被換成同名目錄時⛔ 不刪（框架只落整檔），且⛔ 不得印
    「已不在樹上」——那是⛔ 不成立的事實陳述。負控＝同一次執行裡另一個正常登記項必須真的「已移除」。"""
    consumer = adopted(tmp_path, env, capsys, 'deact-dir')
    victim, control = _adopt.INSTALL_SET[0], _adopt.INSTALL_SET[1]
    (consumer / victim).unlink()
    (consumer / victim).mkdir(parents=True)
    (consumer / victim / 'consumer-owned.txt').write_text('mine\n', encoding='utf-8')

    rc, out = step(consumer, 'deactivate', capsys)
    assert rc == 0, out
    assert f'{victim}・{_adopt.NOT_PLAIN_FILE}' in out, out
    assert f'{victim}・已不在樹上' not in out, out
    assert (consumer / victim / 'consumer-owned.txt').read_text(encoding='utf-8') == 'mine\n'
    assert f'{control}・已移除' in out, out          # 負控：正常項照樣移除
    print('DEACTIVATE directory-on-registered-path', victim)
