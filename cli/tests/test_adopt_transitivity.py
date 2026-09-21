"""WF-015：登記的**轉移性質**、單一 `path` 文法，與 deactivate 刪除面的三條收窄。
消費 core/adopt.md §2（控制檔具名宣告、結構宣告、轉移性質）／§5（刪除面恰兩類）。

**⛔ 不以「`assets` 與已落地物雙向一一對應」斷言**：「已落地物」是樹上不可觀察的歷史事實，以它定義
另一側會使等式退化為恆真（卡面 V12 逐字）。本檔一律以**每次執行前後可測**的性質斷言：
新增集合 ＝ 本次落地／建立集合，且本次之前既有且合結構宣告的登記項逐字保留。

本檔刻意**⛔ 不 import 方案 A 新增的常數**（`CONTROL_SET`／`control_unusable`），只用 `MANIFEST_PATH`
與 `json`：四條回歸斷言因此可以原樣對缺陷版 `d0e6eb698b8492d3c5fe9d848f2f3703aab7cb33` 執行並轉紅
（F-執行-02）。⛔ 不得推出「新契約⛔ 無新常數」——V10 的獨立下界另住 `test_adoption_contract.py`。
掃描面＝合成 consumer 樹（`core/adopt.md` §0）；明示排除 `.git/`。
"""
import json
from pathlib import Path

import pytest

from wf.gh.writes import MUTATIONS
from wf.verbs import _adopt
from wf.verbs.main import main
from .fakes import FakeGhClient
from .test_adopt_gitlink import adopted_consumer
from .test_adopt_manifest import write_manifest_file
from .test_context_roots import git_env

UNREBUILT = 'docs/consumer-note.md'      # bootstrap 本次⛔ 不會重建的 consumer-owned 路徑
EDITED_SUFFIX = b'\n# consumer edited\n'


@pytest.fixture
def env(tmp_path):
    return git_env(tmp_path)


def step(consumer, name, capsys):
    client = FakeGhClient()
    rc = main(['--project-root', str(consumer), 'snapshot', '--adopt', name],
              client=client, root=None, env={})
    out = capsys.readouterr().out
    assert [call for call in client.calls if call[0] in MUTATIONS] == [], client.calls
    return rc, out


def manifest_of(consumer):
    return json.loads((Path(consumer) / _adopt.MANIFEST_PATH).read_text(encoding='utf-8'))


def entries(consumer):
    """{path: 逐字的那一項}——「逐字保留」比的是整項，⛔ 不只比 `path`。"""
    return {entry['path']: entry for entry in manifest_of(consumer)['assets']}


def landed(out, name):
    """本次走分支 ① 落地（或本次建立／沿用）的路徑集合，自**本次執行的 stdout** 取得。
    ⛔ 不以樹上「檔案存在」反推——那是歷史事實，用它定義另一側會讓等式恆真。"""
    marks = {'install': ('已落地',), 'bootstrap': ('建立', '沿用')}[name]
    return {line.split('・')[2] for line in out.splitlines()
            if line.startswith(f'{_adopt.STEP_PREFIX}・{name}・') and line.split('・')[-1] in marks}


def owned_of(mapping, ownership):
    return {path for path, entry in mapping.items() if entry['ownership'] == ownership}


# ── V12 ①：install 的轉移性質（序 1 `R7.1-1` ＝ 序 2 `R5.2-3`）───────────────────────
def test_install_rerun_preserves_every_prior_entry(tmp_path, env, capsys):
    """同一棵樹連跑兩次 install：第二次⛔ 無任何路徑落地 ⇒ 新增集合為空，且第一次的全部登記項逐字保留。
    缺陷版把既有 `framework-managed` 項整批丟掉再重建，第二次就只剩控制檔自己那一項。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='transitive-install')
    rc, out = step(consumer, 'install', capsys)
    assert rc == 0, out
    first, first_landed = entries(consumer), landed(out, 'install')
    assert owned_of(first, _adopt.OWNERSHIPS[0]) == first_landed, (first, first_landed)
    assert first_landed == set(_adopt.INSTALL_SET), sorted(first_landed ^ set(_adopt.INSTALL_SET))
    rc, out = step(consumer, 'install', capsys)
    assert rc == 0, out
    second, second_landed = entries(consumer), landed(out, 'install')
    assert second_landed == set(), sorted(second_landed)        # 路徑已有既有物 ⇒ 分支 ②
    added = owned_of(second, _adopt.OWNERSHIPS[0]) - owned_of(first, _adopt.OWNERSHIPS[0])
    # 本行右側逐字是卡面的右側（`second_landed`），但本起點下兩側都是空集 ⇒ 本行⛔ 未把等式撐開。
    # 序 2 `R6.2-1` 另指出的 install 反例起點（合法 `framework-managed` 登記在案、樹上該檔缺席 ⇒
    # 分支 ① 重新落地並以現行 `pin` 重新登記）本檔刻意**⛔ 不建**：該起點下卡面「本次之前既有…一律
    # 逐字保留」與 A3① 逐字「`pin` 與版本值居所逐字相同」在同一項上互斥（實測舊 pin 必被現行 pin 取代），
    # 建了只會把規格矛盾寫進測試。同上停下上呈、由需求方裁定 A2 保留面的例外後再補。
    assert added == second_landed, sorted(added ^ second_landed)
    for path, entry in first.items():                           # 逐字保留：比整項、⛔ 不只比 path
        assert second.get(path) == entry, (path, entry, second.get(path))
    print('TRANSITIVE install first', sorted(first), 'second', sorted(second))


# ── V12 ②：bootstrap 的鏡像轉移性質（同一根因；新 A2 逐字「`bootstrap` 同此」）──────────
def test_bootstrap_rerun_preserves_every_prior_entry(tmp_path, env, capsys):
    """起點含一個本次⛔ 不會重建的 `consumer-owned` 項。缺陷版的 `step_bootstrap` 只留
    `framework-managed` 與 legacy，該項在第二次 bootstrap 後消失。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='transitive-bootstrap')
    assert step(consumer, 'install', capsys)[0] == 0
    assert step(consumer, 'bootstrap', capsys)[0] == 0
    stale = manifest_of(consumer)
    stale['assets'].append(_adopt.asset_entry(UNREBUILT, _adopt.OWNERSHIPS[1], 'sha256:0', '0.0.0'))
    stale['assets'].sort(key=lambda entry: entry['path'])
    write_manifest_file(consumer, stale)
    before = entries(consumer)
    assert UNREBUILT in before, sorted(before)
    rc, out = step(consumer, 'bootstrap', capsys)
    assert rc == 0, out
    after, built = entries(consumer), landed(out, 'bootstrap')
    assert UNREBUILT not in built, built                         # 本次確實⛔ 未重建它 ⇒ 判準有分辨力
    added = owned_of(after, _adopt.OWNERSHIPS[1]) - owned_of(before, _adopt.OWNERSHIPS[1])
    # ⚠ 本行右側是 `built - owned_of(before, …)`，**⛔ 不是卡面 A2／V12② 的右側**——卡面逐字是
    # 「本次建立**或沿用**的骨架路徑集合」＝ `built` 本身。序 2 `WF-015-R6.2-1` 指的就是這一行。
    # 本輪（iteration 6）實測：第二次 bootstrap 的 `built` 為 9 項，而「新增」在**兩種**執行前後可測
    # 的口徑下都是空集（α path 口徑＝路徑差集；β entry 口徑＝整項有變或新出現者）——因為 A5① 逐字
    # 要求第二次全樹位元組冪等 ⇒ 沿用項一個位元組都⛔ 不會動。**「沿用」在左側⛔ 無任何可測對應物**，
    # 故卡面等式在本起點⛔ 不可能成立：這是 A2 與 A5① 的**規格層互斥**、⛔ 不是實作缺口。
    # `acceptance`／`verification` 是規格欄（`core/card-schema.md` §1），執行者⛔ 不得自行改，故本輪
    # **停下上呈**：⛔ 不改本行斷言、⛔ 不改條文、⛔ 不以改過的右側充當原文成立。
    # **⛔ 不得把本行的綠燈讀成卡面等式成立**（`roles/reviewer.md` §4 `F-查核者-04`）：它只證「本次
    # 新增的⛔ 非既有 `consumer-owned` 項恰是本次建立者」，是卡面等式的一個**真子命題**。
    # 需求方裁定＋PM 落欄後，本行須改回逐字的卡面右側。
    assert added == built - owned_of(before, _adopt.OWNERSHIPS[1]), (sorted(added), sorted(built))
    assert after.get(UNREBUILT) == before[UNREBUILT], (before[UNREBUILT], after.get(UNREBUILT))
    for path, entry in before.items():
        if path not in built:                                    # 本次重建者會帶新 digest／pin
            assert after.get(path) == entry, (path, entry, after.get(path))
    print('TRANSITIVE bootstrap built', sorted(built), 'kept', sorted(set(after) - built))


# ── V12 ③：鍵封閉、`path` 兩兩相異、單一整檔文法、⛔ 無控制檔自身登記項 ────────────────
def test_entry_keys_and_the_single_path_grammar(tmp_path, env, capsys):
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='grammar')
    for name in ('install', 'bootstrap'):
        assert step(consumer, name, capsys)[0] == 0
    assets = manifest_of(consumer)['assets']
    paths = [entry['path'] for entry in assets]
    assert assets, '空 manifest ⛔ 不滿足本條'
    for entry in assets:
        assert len(entry) == 4 and {'path', 'ownership'} <= set(entry), entry
    assert len(set(paths)) == len(paths), paths
    assert all('#' not in path for path in paths), paths
    assert _adopt.MANIFEST_PATH not in paths, paths              # 方案 A：控制檔⛔ 不自登記
    print('GRAMMAR paths', sorted(paths))


# ── V12 負控（甲）：`path` 含 `#` 的項被歸為 legacy，deactivate ⛔ 不處置它 ───────────────
def test_a_hash_path_is_legacy_and_deactivate_leaves_it_alone(tmp_path, env, capsys):
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='legacy-semantics')
    assert step(consumer, 'install', capsys)[0] == 0
    carrier = 'consumer-own.yml'
    (Path(consumer) / carrier).write_text('name: consumer\n', encoding='utf-8')
    value = manifest_of(consumer)
    value['assets'].append(_adopt.asset_entry(
        f'{carrier}#secret-scan', _adopt.OWNERSHIPS[0], 'sha256:0', '0.0.0'))
    value['assets'].sort(key=lambda entry: entry['path'])
    write_manifest_file(consumer, value)
    # 採用的語意是 (b)：結構宣告⛔ 不以 `#` 判不合法，該項被歸為 legacy 且 CLI 零處置。
    assert _adopt.defect_of(value) is None, _adopt.defect_of(value)
    rc, out = step(consumer, 'deactivate', capsys)
    assert rc == 0, out
    assert (Path(consumer) / carrier).read_text(encoding='utf-8') == 'name: consumer\n'
    assert [line for line in out.splitlines() if f'{carrier}#secret-scan' in line
            and _adopt.LEGACY_KEPT in line], out
    print('LEGACY_SEMANTICS b listed_not_processed', carrier)


# ── V12 負控（乙）：`path` 等於控制檔路徑 ⇒ 整份 manifest 不可用、該次 install 全樹零寫入 ──
def test_a_self_registering_control_file_makes_the_manifest_unusable(tmp_path, env, capsys):
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='control-path')
    assert step(consumer, 'install', capsys)[0] == 0
    value = manifest_of(consumer)
    value['assets'].append(_adopt.asset_entry(
        _adopt.MANIFEST_PATH, _adopt.OWNERSHIPS[0], 'sha256:0', '0.0.0'))
    value['assets'].sort(key=lambda entry: entry['path'])
    write_manifest_file(consumer, value)
    assert _adopt.read_manifest(consumer)[0] is None, value      # 判為不可用（`control-path`）
    before = tree_digests(consumer)
    rc, out = step(consumer, 'install', capsys)
    assert rc == 0, out                                          # ⛔ 不 raise、回固定理由續跑
    assert tree_digests(consumer) == before, 'install 對全樹零位元組寫入'
    assert manifest_of(consumer) == value, '控制檔位元組逐字不變'
    print('CONTROL_PATH unusable zero_write', len(before))


def tree_digests(root):
    """全樹 (路徑 → 內容摘要)；明示排除 `.git/`。⛔ 不比對 mtime。"""
    root = Path(root)
    return {path.relative_to(root).as_posix(): _adopt.digest_of(path.read_bytes())
            for path in sorted(root.rglob('*'))
            if path.is_file() and '.git' not in path.relative_to(root).parts}


# ── 回歸：既有控制檔⛔ 不被覆寫、⛔ 不取得所有權（序 2 `R5.2-2`）────────────────────────
def test_install_never_overwrites_an_existing_control_file(tmp_path, env, capsys):
    """起點＝控制檔路徑上已有一份採用者自己的 JSON（本例逐字把控制檔登記成 `consumer-owned`）。
    缺陷版把它覆寫並把該路徑改登記為 `framework-managed`；新契約下它命中 `control-path`
    而整份不可用 ⇒ 落進前置條件、全樹零寫入。兩種判準下**位元組不變**都是必要條件。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='owned-control')
    value = {'schema': _adopt.MANIFEST_SCHEMA, 'source_commit': None,
             'assets': [_adopt.asset_entry(_adopt.MANIFEST_PATH, _adopt.OWNERSHIPS[1],
                                           'sha256:0', '0.0.0')]}
    write_manifest_file(consumer, value)
    raw = (Path(consumer) / _adopt.MANIFEST_PATH).read_bytes()
    rc, out = step(consumer, 'install', capsys)
    assert rc == 0, out
    assert (Path(consumer) / _adopt.MANIFEST_PATH).read_bytes() == raw, out
    print('OWNED_CONTROL bytes_unchanged', len(raw))


# ── 回歸：deactivate ⛔ 不刪採用者改過的框架檔（裁定第 4 項、新 A7 ①）─────────────────
def test_deactivate_keeps_a_framework_file_the_adopter_edited(tmp_path, env, capsys):
    """正負控同棵樹：一個資產改過位元組（摘要⛔ 不符）⇒ 保留並指向退場節；另一個⛔ 未改 ⇒ 被移除。
    缺陷版逐字 `gone = target.is_file(); if gone: target.unlink()`，刪前⛔ 無摘要比對 ⇒ 兩個都刪。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='edited-asset')
    for name in ('install', 'bootstrap'):
        assert step(consumer, name, capsys)[0] == 0
    edited, intact = _adopt.INSTALL_SET[0], _adopt.INSTALL_SET[1]
    path = Path(consumer) / edited
    path.write_bytes(path.read_bytes() + EDITED_SUFFIX)
    body = path.read_bytes()
    rc, out = step(consumer, 'deactivate', capsys)
    assert rc == 0, out
    assert path.read_bytes() == body, out                        # 採用者改過的框架檔位元組不變
    assert not (Path(consumer) / intact).exists(), out           # 正控：摘要相符者確實被移除
    pointed = [line for line in out.splitlines() if edited in line and _adopt.EXIT_SECTION in line]
    assert pointed, out                                          # 印一行並指向 `ADOPTION.md` §5
    print('EDITED_ASSET kept', edited, 'removed', intact, 'line', pointed)


# ── 回歸：legacy 承載檔⛔ 不被整檔登記項旁路刪除（序 2 `R5.2-4`）────────────────────────
def test_deactivate_keeps_a_carrier_that_is_also_a_whole_file_entry(tmp_path, env, capsys):
    """同一個承載檔同時被一個整檔 `framework-managed` 項與一個 legacy 項指到。
    缺陷版先對整檔項 `unlink()`、之後才列 legacy 說明 ⇒ 保留面被旁路刪除。"""
    consumer, _, _, _, _ = adopted_consumer(tmp_path, env, name='legacy-collision')
    assert step(consumer, 'install', capsys)[0] == 0
    carrier = _adopt.INSTALL_SET[0]
    body = (Path(consumer) / carrier).read_bytes()
    value = manifest_of(consumer)
    value['assets'].append(_adopt.asset_entry(
        f'{carrier}#secret-scan', _adopt.OWNERSHIPS[0], 'sha256:0', '0.0.0'))
    value['assets'].sort(key=lambda entry: entry['path'])
    write_manifest_file(consumer, value)
    assert _adopt.defect_of(value) is None, value                 # `path` 仍兩兩相異、結構有效
    rc, out = step(consumer, 'deactivate', capsys)
    assert rc == 0, out
    assert (Path(consumer) / carrier).read_bytes() == body, out   # 承載檔位元組逐一不變
    assert [line for line in out.splitlines() if carrier in line and _adopt.EXIT_SECTION in line], out
    print('LEGACY_COLLISION carrier_kept', carrier)
