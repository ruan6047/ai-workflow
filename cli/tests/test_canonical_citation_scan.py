"""``scripts/canonical_citation_scan.py`` 的測試。

分兩組，**兩組都必要**：

- **合成輸入**：釘住判準本身。判準要能對「我完全控制內容的一行字」給出可預測的
  答案，否則它量到的只是巧合。變異檢驗全部在這一組——把判準改壞，對應測試必紅。
- **真實 repo**：全 ``git ls-files`` 掃描必須零命中。這一組才是守衛的正題；合成組
  只證明判準有鑑別力，不證明 repo 現在是乾淨的。

⚠️ **本檔自己也在射程內**（它是被追蹤檔）。因此凡是要造出「長成行號」的樣本，
一律**用字串拼接**、不得寫字面值——寫字面值會被掃描器抓到自己身上。這不是假設：
``test_doctor.py`` 的舊註解正是因為寫了字面例子而在本輪轉紅。
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts" / "canonical_citation_scan.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("canonical_citation_scan", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


ccs = _load_module()


# --------------------------------------------------------------------------
# 合成輸入用的零件。⚠️ 下面四行**刻意不提及** canonical 檔名，也不含冒號數字：
# 它們是用來「組裝」壞樣本的原料，本身必須是乾淨的。
# --------------------------------------------------------------------------
_N = "220"
_OTHER_N = "9"
_SECTION = "6"
_COLON = ":"

#: 組裝出來的壞樣本。實際內容長成「檔名 ＋ 冒號 ＋ 行號」，但**原始碼裡看不到**
#: 那個形態，所以掃描器掃本檔時不會命中自己。
_BAD_CANONICAL_REF = f"見 `{ccs.CANONICAL_FILENAME}{_COLON}{_N}` 的那條規則"
#: 節次夾行號：R4 用鬆散時戳過濾時被吃掉的那種形態。**單獨抽成常數**是為了讓對照組
#: 能用字串剪除產生，差異因此是機器保證的「只差這一段」，不是人眼比對兩個字面值。
_SECTION_LINE_REF = f" §{_SECTION}{_COLON}{_N}"
_BAD_SECTION_REF = f"見 `{ccs.CANONICAL_FILENAME}`{_SECTION_LINE_REF} 那條"
#: 連檔名都沒有，只在 `canonical` 一詞後面接冒號行號。
_BAD_BARE_REF = f"canonical{_COLON}{_N} 想要的離線稽核副本"
#: 指名了**別的**來源檔的行號。它不是 canonical 的引用，故不在射程。
_QUALIFIED_OTHER = f"canonical 的實作見 `project.py{_COLON}{_OTHER_N}`"
#: 事件留痕行：冒號數字全部來自 ISO 時戳。
_TIMESTAMP_LINE = (
    "- 2026-07-17T18:40:00+08:00 handoff by ruan6047；證據：需求方指示上修 canonical"
)
#: 單獨一枚完整 ISO 時戳，供「時戳與行號同行」的差分樣本組裝用。
_ISO_STAMP = "2026-07-30T18:51:22+08:00"


# ==========================================================================
# 判準的鑑別力（合成輸入）
# ==========================================================================


@pytest.mark.parametrize(
    "line, expected",
    [
        (_BAD_CANONICAL_REF, (ccs.KIND_CANONICAL,)),
        (_BAD_SECTION_REF, (ccs.KIND_BARE,)),
        (_BAD_BARE_REF, (ccs.KIND_BARE,)),
    ],
)
def test_each_line_number_shape_is_flagged(line, expected):
    """三種寫法都要命中——判準不追寫法，所以三種都被同一組規則接住。

    ⚠️ 落在**哪一條**規則不是隨意的：``_BAD_SECTION_REF`` 的冒號夾在節次後面、不是
    緊接檔名，所以它走的是「剪除後仍有冒號數字」那條，不是「檔名加冒號行號」。
    兩條規則的分工在這裡被釘死——把 ``_CANONICAL_LINE_REF`` 放寬成允許檔名與冒號
    之間有其他字元，本測試會轉紅。
    """
    assert ccs.line_offence_kinds(line) == expected


def test_iso_stripping_does_not_swallow_a_section_line_ref():
    """⭐ R4 的實際踩坑：鬆散的時戳過濾會吃掉節次夾行號，讓真缺陷變成零命中。

    ⚠️ **只斷言「這行有命中」殺不掉那個變異，所以本測試是差分的。** 把
    ``_ISO_TIMESTAMP`` 放寬成「一到兩位數字、冒號、兩位數字」時，節次夾行號的確被吃
    掉了，但同一行的時戳也只被剪掉半截，剩下的秒數自己就是一段冒號數字，命中照樣
    成立。本測試的舊版就是這樣：docstring 逐字宣稱該變異會讓它轉紅，``#120`` R6 的
    跨家族查核者實跑後記錄它仍然全綠（``#124``）。

    差分的做法是先斷言**把節次夾行號剪掉、其餘一字不動**的同一行必須零命中——證明
    時戳（含任何殘骸）不供給命中——再斷言把它加回去必須且只能命中無主行號。兩個放寬
    方向因此都逃不掉：只吃時分的版本被第一個斷言擋下（殘骸自成命中），連秒一起吃的
    版本把時戳剪乾淨、卻吃掉節次夾行號，被第二個斷言擋下。若 ``_SECTION_LINE_REF``
    哪天對不上樣本、剪除變成空操作，對照組會拿到與主樣本相同的字串而轉紅，不會默默
    退化成零資訊的檢查。
    """
    with_ref = f"{_BAD_SECTION_REF}（{_ISO_STAMP} 記錄）"
    without_ref = with_ref.replace(_SECTION_LINE_REF, "")

    assert ccs.line_offence_kinds(without_ref) == ()
    assert ccs.line_offence_kinds(with_ref) == (ccs.KIND_BARE,)


def test_pure_timestamps_are_not_flagged():
    """事件留痕行的時、分、秒不是行號。全 repo 實測有四行純粹因時戳而誤判。"""
    assert ccs.line_offence_kinds(_TIMESTAMP_LINE) == ()


def test_qualified_refs_to_other_source_files_are_out_of_scope():
    """指名別的來源檔的行號同樣會腐爛，但那不是本掃描器的射程——明說，不假裝有管。"""
    assert ccs.line_offence_kinds(_QUALIFIED_OTHER) == ()


def test_lines_that_never_mention_canonical_are_ignored():
    """沒點名 canonical 就不判。否則整個 repo 的每個 ``檔名:行`` 都會進來。"""
    assert ccs.line_offence_kinds(f"見 `project.py{_COLON}{_OTHER_N}` 的欄位定義") == ()


def test_scan_text_reports_path_and_line_number():
    """命中要能被人拿去修：路徑、行號、種類、原文都要在。"""
    text = "第一行沒事\n" + _BAD_BARE_REF + "\n"
    (offence,) = ccs.scan_text("some/file.md", text)
    assert (offence.path, offence.lineno, offence.kind) == ("some/file.md", 2, ccs.KIND_BARE)
    assert offence.excluded_by is None


# ==========================================================================
# 開放集合：新增的檔會不會自動納管
# ==========================================================================


def test_a_newly_added_file_is_scanned_and_flagged(tmp_path):
    """⭐ 這是「開放集合」的正題：**沒有人把新檔加進任何清單**，它仍然被掃到。

    做法是造一棵真的 git repo（掃描器的射程＝``git ls-files``），加一個帶行號引用
    的新檔，然後掃。舊的白名單形狀在這裡會綠——那正是它漏掉
    ``scripts/daily_snapshot.sh`` 的原因。
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    newcomer = tmp_path / "docs" / "BRAND_NEW.md"
    newcomer.parent.mkdir(parents=True)
    newcomer.write_text(f"# 新檔\n\n{_BAD_CANONICAL_REF}\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)

    offences, unreadable = ccs.scan_repo(tmp_path)
    assert unreadable == []
    assert [(o.path, o.lineno, o.kind) for o in offences] == [
        ("docs/BRAND_NEW.md", 3, ccs.KIND_CANONICAL)
    ]


def test_untracked_files_are_out_of_scope(tmp_path):
    """明說射程邊界：``git ls-files`` 看不到未追蹤檔，所以掃描器也看不到。

    這是**已知的驗不到**，不是 bug；寫成測試是為了讓它不能被誤以為有涵蓋。
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "UNTRACKED.md").write_text(_BAD_CANONICAL_REF, encoding="utf-8")

    offences, _ = ccs.scan_repo(tmp_path)
    assert offences == []


# ==========================================================================
# 排除集：不得是垃圾桶
# ==========================================================================


def test_excluded_paths_are_not_flagged(tmp_path):
    """反方向：排除集內的檔即使有命中也不轉紅。

    ⚠️ 用**同一份壞內容**放在被排除的路徑上，確保差別只來自排除集本身，不是內容。
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    excluded_rel = next(iter(ccs.EXCLUSIONS))
    target = tmp_path / excluded_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_BAD_CANONICAL_REF, encoding="utf-8")
    # 對照組：同樣內容放在沒被排除的路徑上，必須命中。
    (tmp_path / "NOT_EXCLUDED.md").write_text(_BAD_CANONICAL_REF, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)

    offences, _ = ccs.scan_repo(tmp_path)
    assert [o.path for o in offences] == ["NOT_EXCLUDED.md"]


def test_every_exclusion_points_at_a_real_file_and_explains_itself():
    """排除項必須指到實際存在的檔，並附**為什麼**——只列路徑不算。"""
    for rel, reason in ccs.EXCLUSIONS.items():
        assert (_REPO_ROOT / rel).is_file(), f"排除項 {rel} 指到不存在的檔，應刪除"
        assert len(reason) >= 40, f"排除項 {rel} 的理由過短，看不出為什麼不該納管"


def test_every_exclusion_is_load_bearing():
    """⭐ **排除集不是垃圾桶**：沒有實際命中的排除項是死條目，必須刪掉。

    做法是關掉排除、重掃，看每個排除項是不是真的擋下了東西。若某個檔已經被修好、
    或已不存在該形態的引用，這條會紅並指名該刪哪一項——排除集因此不會默默長大。
    """
    all_offences, _ = ccs.scan_repo(_REPO_ROOT, apply_exclusions=False)
    suppressed = {o.path for o in all_offences if o.excluded_by is not None}
    dead = set(ccs.EXCLUSIONS) - suppressed
    assert not dead, f"這些排除項已無命中，是死條目，請刪除：{sorted(dead)}"


# ==========================================================================
# 真實 repo：守衛的正題
# ==========================================================================


def test_repo_wide_scan_finds_no_line_numbered_canonical_citations():
    """⭐ 全 ``git ls-files`` 掃描：引用 canonical 只准「節次 ＋ 條文原文片段」。

    ⚠️ **驗不到什麼**（模組 docstring 有完整清單，這裡只點最重要的兩條）：

    - **只驗形態，不驗指得對不對**。節次寫錯、片段根本不存在於 canonical，照樣全綠。
      散文片段的逐字性**沒有守衛**——那需要先有一個機器可辨識的引用語法，本輪沒做。
    - **條文語意被改寫而片段字串沒動時不會響**。比對的是字串在不在。
    """
    offences, unreadable = ccs.scan_repo(_REPO_ROOT)
    assert unreadable == [], f"這些被追蹤檔讀不到，未經掃描：{unreadable}"
    assert not offences, "引用 canonical 不得帶行號（canonical 插行會讓行號靜默失準）：\n" + "\n".join(
        o.render() for o in offences
    )


def test_cli_exits_nonzero_when_something_is_wrong(tmp_path, capsys):
    """守衛要能當指令跑：有命中就非零離開，否則掛不進 CI。"""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "BAD.md").write_text(_BAD_CANONICAL_REF, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)

    assert ccs.main(["--root", str(tmp_path)]) == 1
    assert "BAD.md" in capsys.readouterr().out


def test_cli_exits_zero_on_the_real_repo(capsys):
    """同一支指令對真實 repo 必須是 0——測試與人手動跑的是同一份判準。"""
    assert ccs.main(["--root", str(_REPO_ROOT)]) == 0
    capsys.readouterr()
