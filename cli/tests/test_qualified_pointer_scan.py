"""``scripts/qualified_pointer_scan.py`` 的測試（守衛的守衛）。

分兩組，**兩組都必要**（形狀照抄 ``test_canonical_citation_scan.py``，⛔ 不發明新的）：

- **合成輸入**：釘住判準本身。判準要能對「我完全控制內容的一行字」給出可預測的
  答案，否則它量到的只是巧合。變異檢驗全部在這一組。
- **真實 repo**：全 ``git ls-files`` 掃描必須零紅。這一組才是守衛的正題。

⭐⭐ **本檔存在的最重要理由：今天真實 repo 的正確結果就是 0 紅，而「跑了是綠的」
是零資訊。** 因此本檔刻意包含兩條會在守衛失效時轉紅的測試：

- ``test_every_exemption_is_load_bearing``：豁免簿的條目沒擋到東西就是死條目。
- ``test_removing_the_core_judgement_turns_the_real_corpus_red``：把核心裁決換成恆
  ``ok``，真實語料上必須有東西轉紅。⛔ 若不會紅，這支守衛就是零資訊檢查。

⚠️ **本檔自己也在射程內**（它是被追蹤檔）。凡是要造出「路徑 ＋ 冒號 ＋ 行號」的
樣本，一律走 ``qps.pointer_token()`` 拼接，⛔ 不得寫字面——寫字面會被掃描器抓到
自己身上，而那些檔並不存在（會變成一筆 F1 紅）。
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts" / "qualified_pointer_scan.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("qualified_pointer_scan", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


qps = _load_module()


# --------------------------------------------------------------------------
# 合成目標樹。⚠️ 兩個同名的 ``__init__`` 是**刻意**的：F4（目標不唯一）要有真實
# 形狀的樣本，而同名檔正是本 repo 真的會出現的那一種。
# --------------------------------------------------------------------------
_TREE: dict[str, list[str]] = {
    "src/alpha.py": ["第一行", "", "第三行", "第四行"],
    "docs/beta.md": ["# beta", "內文"],
    "pkg/__init__.py": ["x = 1"],
    "pkg/sub/__init__.py": ["y = 2"],
}
_EXTS = qps.tracked_extensions(_TREE)


def _line(prefix: str, path: str, lineno: int, suffix: str = "") -> str:
    """把一個合格指標包進一句散文裡。⛔ 字面永遠不出現在原始碼。"""
    return f"{prefix}{qps.pointer_token(path, lineno)}{suffix}"


# ==========================================================================
# 判準的鑑別力（合成輸入）
# ==========================================================================


def test_tracked_extensions_are_derived_from_the_tree_not_handpicked():
    """副檔名宇宙由檔案清單導出。⭐ 新增一種副檔名不需要有人記得改任何常數。"""
    assert _EXTS == frozenset({"py", "md"})
    assert qps.tracked_extensions(["a/b.RST", "c.py"]) == frozenset({"rst", "py"})


def test_adjacent_path_and_line_number_is_a_qualified_pointer():
    """k=0 的正題：路徑與行號相鄰才算數。"""
    hits, rejected = qps.find_pointers(_line("見 ", "src/alpha.py", 3, " 那一行"), _EXTS)
    assert rejected == ()
    assert [(h.path, h.lineno) for h in hits] == [("src/alpha.py", 3)]


def test_a_gap_between_path_and_number_is_not_a_pointer():
    """⭐⭐ **k=0 的純度就靠這條。**

    這一行是本 repo 真實存在的資源宣告形狀（``resources.py`` 與 ``test_resources.py``
    都有）。回看窗 k=1 會把它綁成「那個 ``.py`` 檔的第 8080 行」——**同一個字串裡兩個
    不相干的冒號值**，那是實測 k=1 誤綁的主要來源。k=0 看不到它，這是刻意的。

    ⚠️ 這一行可以寫字面：``port`` 前面沒有點號、``.py`` 後面緊接的是引號，
    構造上不可能符合合格指標的形態。**若哪天它開始命中，就是形態被放寬了，本測試轉紅。**
    """
    line = '{"db_scope": "none", "resources": ["file:a.py", "port:8080"]}'
    hits, rejected = qps.find_pointers(line, _EXTS)
    assert hits == ()
    assert rejected == ()
    # 對照組：同一句話裡真的把路徑與行號寫在一起，就必須命中。差別只有「相鄰」。
    adjacent = line.replace('"file:a.py"', '"file:' + qps.pointer_token("a.py", 8080) + '"')
    assert [h.lineno for h in qps.find_pointers(adjacent, _EXTS)[0]] == [8080]


def test_iso_timestamps_are_not_pointers():
    """留痕行的時、分、秒不是行號。剪的是**整段** ISO 時戳，位移以等長空白補回。"""
    line = "- 2026-08-27T13:10:16+08:00 amend by wf-cli（op 617f33d0）"
    assert qps.find_pointers(line, _EXTS) == ((), ())


def test_the_extension_must_exist_in_this_repo_and_the_drop_is_reported():
    """f-string 的格式規格長得像指標。**擋掉它的是副檔名宇宙，⛔ 不是 regex。**

    ⚠️ 而且擋掉之後**要被報出來**：靜默丟棄會讓「本腳本放掉了什麼」變成看不見的量。
    """
    line = "print(f'{" + qps.pointer_token("sys.maxunicode", 4) + "X}')"
    hits, rejected = qps.find_pointers(line, _EXTS)
    assert hits == ()
    assert [ext for _token, ext in rejected] == ["maxunicode"]


@pytest.mark.parametrize(
    "path, lineno, verdict",
    [
        ("src/alpha.py", 3, qps.VERDICT_OK),
        ("alpha.py", 3, qps.VERDICT_OK),  # 只寫檔名，沿元件邊界唯一命中
        ("src/alpha.py", 2, qps.VERDICT_EMPTY_TARGET),
        ("src/alpha.py", 99, qps.VERDICT_OUT_OF_RANGE),
        ("src/alpha.py", 0, qps.VERDICT_OUT_OF_RANGE),
        ("src/missing.py", 1, qps.VERDICT_UNRESOLVABLE),
        ("__init__.py", 1, qps.VERDICT_AMBIGUOUS),
    ],
)
def test_every_failure_mode_gets_its_own_verdict(path, lineno, verdict):
    """五種裁決各要有一個會落在它身上的樣本。⛔ 沒有「看不懂所以跳過」這條路。"""
    (pointer,) = qps.find_pointers(_line("見 ", path, lineno), _EXTS)[0]
    finding = qps.judge("some/prose.md", 7, pointer, _TREE)
    assert finding.verdict == verdict
    assert finding.verdict in qps.VERDICTS


def test_exact_path_wins_over_a_suffix_match():
    """完整路徑優先。⛔ 不做模糊比對——猜錯等於製造假綠。"""
    assert qps.resolve_path("pkg/sub/__init__.py", tuple(_TREE)) == ("pkg/sub/__init__.py",)
    assert set(qps.resolve_path("__init__.py", tuple(_TREE))) == {
        "pkg/__init__.py",
        "pkg/sub/__init__.py",
    }


def test_scan_text_reports_where_the_pointer_lives():
    """紅要能被人拿去修：來源檔、來源行號、token、目標都要在。"""
    text = "沒事的一行\n" + _line("見 ", "src/alpha.py", 2) + "\n"
    findings, _ = qps.scan_text("prose.md", text, _TREE, _EXTS)
    (finding,) = findings
    assert (finding.source, finding.source_lineno, finding.verdict) == (
        "prose.md", 2, qps.VERDICT_EMPTY_TARGET,
    )
    assert finding.target == "src/alpha.py"


# ==========================================================================
# 豁免登記簿：鍵不含行號、死條目轉紅、格式壞掉就炸
# ==========================================================================


_LONG_REASON = "理由夠長夠長夠長夠長夠長夠長夠長夠長夠長夠長夠長夠長夠長夠長夠長夠長"
_SOME_TOKEN = qps.pointer_token("x.md", 1)


@pytest.mark.parametrize(
    "bad",
    [
        {"不是元組": _LONG_REASON},
        {("a.md", "不是 sha256", _SOME_TOKEN): _LONG_REASON},
        {("a.md", "0" * 64, "這不是一個指標"): _LONG_REASON},
        {("a.md", "0" * 64, _SOME_TOKEN): "太短"},
        {("a.md", "0" * 64): _LONG_REASON},
    ],
)
def test_the_exemption_registry_fails_closed_on_a_malformed_entry(bad):
    """⭐ V10 的第五種：登記簿解析失敗**一律紅**，⛔ 不靜默略過。

    本腳本的登記簿是模組內的 dict ⇒ 構造上沒有「檔案不見了」這種狀態，能壞的只有
    內容；壞掉就拋錯，而 ``scan_repo`` 進門第一件事就是叫它。
    """
    with pytest.raises(ValueError):
        qps.validate_exemptions(bad)


def test_the_real_registry_is_wellformed():
    assert qps.validate_exemptions(qps.EXEMPTIONS) is None


def _synthetic_tree_with_one_bad_pointer(root: Path, prose: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "src" / "real.py").write_text("x = 1\n", encoding="utf-8")
    (root / "PROSE.md").write_text(prose, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)


def test_an_exemption_survives_the_source_line_moving(tmp_path, monkeypatch):
    """⭐⭐ **V9 的 T2 自我指涉陷阱**：登記簿的鍵**不得含來源行號**。

    用行號當鍵，等於在治行號腐爛的腳本裡再種一份行號——而它失效的方向是**靜默
    放行**，最壞的那一種。本測試把同一句話往下推五行再掃一次：鍵是
    ``(來源檔, sha256(該行文字), token)``，所以照樣命中。
    """
    bad = _line("見 ", "src/gone.py", 5)
    prose_line = "本段刻意指向不存在的檔：" + bad
    key = qps.exemption_key("PROSE.md", prose_line, qps.pointer_token("src/gone.py", 5))
    monkeypatch.setitem(
        qps.__dict__, "EXEMPTIONS",
        {key: "合成豁免項（僅供本測試）：用來證明鍵對來源行號的位移免疫，同時讓理由欄的長度下限一併受檢。"},
    )

    _synthetic_tree_with_one_bad_pointer(tmp_path, prose_line + "\n")
    first = qps.scan_repo(tmp_path)
    assert [f.verdict for f in first.exempted] == [qps.VERDICT_UNRESOLVABLE]
    assert first.blocking == () and first.dead_exemptions == ()

    # 同一句話往下推五行——只有行號變了。
    (tmp_path / "PROSE.md").write_text("\n" * 5 + prose_line + "\n", encoding="utf-8")
    moved = qps.scan_repo(tmp_path)
    assert [f.source_lineno for f in moved.exempted] == [6]
    assert moved.blocking == () and moved.dead_exemptions == ()


def test_an_exemption_dies_when_the_source_line_text_changes(tmp_path, monkeypatch):
    """反方向：行的**文字**被改動，豁免就該失效並要求重新裁決。

    ⛔ 這正是「該行 ``git diff`` 為空」那種判準做不到的事——整檔有別的改動時行號會
    位移，那個檢查在此是零資訊（本 repo 的同族守衛已被打穿兩次）。
    """
    bad = _line("見 ", "src/gone.py", 5)
    original = "本段刻意指向不存在的檔：" + bad
    key = qps.exemption_key("PROSE.md", original, qps.pointer_token("src/gone.py", 5))
    monkeypatch.setitem(
        qps.__dict__, "EXEMPTIONS",
        {key: "合成豁免項（僅供本測試）：用來證明來源行的文字被改動之後，這個條目會自動變成死條目而轉紅。"},
    )

    _synthetic_tree_with_one_bad_pointer(tmp_path, "（改寫過的前綴）" + bad + "\n")
    report = qps.scan_repo(tmp_path)
    assert [f.verdict for f in report.blocking] == [qps.VERDICT_UNRESOLVABLE]
    assert report.dead_exemptions == (key,)
    assert qps.main(["--root", str(tmp_path)]) == 1


# ==========================================================================
# 開放集合：新增的檔會不會自動納管
# ==========================================================================


def test_a_newly_added_file_is_scanned_and_flagged(tmp_path):
    """⭐ 開放集合的正題：**沒有人把新檔加進任何清單**，它仍然被掃到。"""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "real.py").write_text("x = 1\n", encoding="utf-8")
    newcomer = tmp_path / "docs" / "BRAND_NEW.md"
    newcomer.parent.mkdir(parents=True)
    newcomer.write_text("# 新檔\n\n" + _line("見 ", "src/real.py", 900) + "\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)

    report = qps.scan_repo(tmp_path)
    assert report.unreadable == ()
    assert [(f.source, f.source_lineno, f.verdict) for f in report.blocking] == [
        ("docs/BRAND_NEW.md", 3, qps.VERDICT_OUT_OF_RANGE)
    ]


def test_a_file_that_cannot_be_decoded_is_reported_not_silently_skipped(tmp_path):
    """讀不到的被追蹤檔要**列進 ``unreadable``**，⛔ 不靜默略過。

    真實 repo 今天一個都沒有（``test_repo_wide_scan_finds_no_broken_qualified_pointers``
    斷言它是空的）⇒ 那條斷言在真實語料上**永遠不會被觸發**。本測試用合成樹補上這條
    路徑的鑑別力：若哪天有人把 ``unreadable`` 改成 ``continue`` 就算了，這裡會轉紅。
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "real.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "BLOB.md").write_bytes(b"\xff\xfe\x00\x01 not utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)

    report = qps.scan_repo(tmp_path)
    assert report.unreadable == ("BLOB.md",)
    # 讀不到的那一份仍然計進「掃描檔案數」——⛔ 不得讓它從分母裡消失。
    assert report.scanned_files == len(qps.tracked_files(tmp_path)) == 2


def test_the_cli_exits_nonzero_when_a_tracked_file_could_not_be_read(
    tmp_path, capsys, monkeypatch
):
    """⭐ **「掃不到」與「掃過而乾淨」的退出碼必須不同**（`aiwf#146` R1-003）。

    原本 ``unreadable`` 只由真實樹測試斷言為空，而 ``main()`` 不看它 ⇒ CLI 會逐字印出
    「讀不到，未掃描」**卻回 0**。人手執行因此拿到一個綠燈，而那個綠燈蓋住的是**射程
    缺口**：那幾份檔根本沒被掃過。

    ⚠️ **本測試是差分的，這樣才殺得掉變異。** 兩棵樹只差一份讀不到的檔：對照組必須
    rc=0、實驗組必須 rc=1。並先斷言實驗組的 ``blocking`` 與 ``dead_exemptions`` 都是空的
    ⇒ **rc=1 的唯一來源只可能是 ``unreadable``**。若有人把 ``report.unreadable`` 從
    ``main()`` 的退出碼運算式裡拿掉，本測試立刻轉紅。
    """
    # ⚠️ 合成樹上真實的豁免簿必然全是死條目（它們指的是本 repo 的檔）⇒ 那會讓 rc=1
    # 有第二個來源、差分因此測不出東西。清空它，讓 ``unreadable`` 是唯一的變因。
    monkeypatch.setitem(qps.__dict__, "EXEMPTIONS", {})
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "real.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)

    # 對照組：同一棵樹，沒有讀不到的檔。
    assert qps.main(["--root", str(tmp_path)]) == 0
    capsys.readouterr()

    # 實驗組：只多一份被追蹤但不是 UTF-8 的檔。
    (tmp_path / "BLOB.md").write_bytes(b"\xff\xfe\x00\x01 not utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)

    report = qps.scan_repo(tmp_path)
    assert report.blocking == () and report.dead_exemptions == ()
    assert report.unreadable == ("BLOB.md",)

    assert qps.main(["--root", str(tmp_path)]) == 1
    assert "BLOB.md" in capsys.readouterr().out


def test_untracked_files_are_out_of_scope(tmp_path):
    """明說射程邊界：``git ls-files`` 看不到未追蹤檔，所以掃描器也看不到。

    這是**已知的驗不到**，不是 bug；寫成測試是為了讓它不能被誤以為有涵蓋。
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "real.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    (tmp_path / "UNTRACKED.md").write_text(_line("見 ", "src/real.py", 900), encoding="utf-8")

    assert qps.scan_repo(tmp_path).blocking == ()


# ==========================================================================
# 真實 repo：守衛的正題
# ==========================================================================


def test_repo_wide_scan_finds_no_broken_qualified_pointers():
    """⭐ 全 ``git ls-files`` 掃描：指名來源檔的行號必須還指得到非空的東西。

    ⚠️ **驗不到什麼**（模組 docstring 有完整清單，這裡只點最重要的一條）：
    **⛔ 沒有做「目標內容變了」的偵測。** 漂移之後恰好落在另一行非空內容上的，
    本守衛全綠 ⇒ 它報出來的紅數是**下界**，⛔ 不是當日漂移總量。
    """
    report = qps.scan_repo(_REPO_ROOT)
    assert report.unreadable == (), f"這些被追蹤檔讀不到，未經掃描：{report.unreadable}"
    assert not report.blocking, "指名來源檔的行號指不到東西了：\n" + "\n".join(
        f.render() for f in report.blocking
    )


def test_every_exemption_points_at_a_real_source_file_and_explains_itself():
    """豁免項必須指到實際存在的來源檔，並附**為什麼**——只列路徑不算。"""
    for (source, _digest, _token), reason in qps.EXEMPTIONS.items():
        assert (_REPO_ROOT / source).is_file(), f"豁免項的來源檔 {source} 不存在，應刪除"
        assert len(reason) >= 40, f"豁免項 {source} 的理由過短，看不出為什麼不該納管"


def test_every_exemption_is_load_bearing():
    """⭐ **豁免簿不是垃圾桶**：沒有實際擋下裁決的條目是死條目，必須刪掉。

    ⚠️ 這條同時是 ratchet 的第二向（「登記了但已不存在」）。若被豁免的那一行被修好、
    或那個 token 消失，本測試會紅並指名該刪哪一項——豁免簿因此不會默默長大。
    """
    dead = qps.scan_repo(_REPO_ROOT).dead_exemptions
    assert not dead, f"這些豁免項已無命中，是死條目，請刪除：{[k[0] + ' / ' + k[2] for k in dead]}"


def test_the_two_intentional_placeholders_are_exempted_not_missed():
    """⭐ 證明那兩筆今天是**被明文豁免**的，⛔ 不是被漏掉的。

    做法是關掉豁免重掃：它們必須立刻變成紅。若判準根本沒看到它們，這裡會是空的。
    """
    unexempted = qps.scan_repo(_REPO_ROOT, apply_exemptions=False).blocking
    assert {(f.source, f.token) for f in unexempted} == {
        ("scripts/canonical_citation_scan.py", qps.pointer_token("templates/foo.md", 12)),
        ("scripts/canonical_citation_scan.py", qps.pointer_token("templates/bar.md", 9)),
    }
    assert {f.verdict for f in unexempted} == {qps.VERDICT_UNRESOLVABLE}


def test_removing_the_core_judgement_turns_the_real_corpus_red(monkeypatch):
    """⭐⭐ **本檔最重要的一條：證明今天的全綠不是零資訊。**

    今天真實 repo 的正確結果就是 0 紅，所以「跑起來是綠的」本身不證明守衛在工作。
    把核心裁決換成恆 ``ok``（＝拿掉判定），真實語料上必須有東西轉紅——這裡轉紅的是
    兩個豁免條目：它們不再擋下任何東西，於是變成死條目。

    ⛔ 若這條在變異後仍然全綠，代表本守衛對現有語料沒有鑑別力，整支要重做。
    """
    monkeypatch.setattr(
        qps, "judge",
        lambda source, lineno, pointer, tree: qps.Finding(
            source, lineno, pointer.token, qps.VERDICT_OK
        ),
    )
    mutated = qps.scan_repo(_REPO_ROOT)
    assert mutated.blocking == ()
    assert len(mutated.dead_exemptions) == len(qps.EXEMPTIONS) >= 1
    assert qps.main(["--root", str(_REPO_ROOT)]) == 1


def test_bare_colon_numbers_in_canonical_are_structurally_out_of_scope():
    """⭐ V11 的第二處特例化：canonical 裡那段**歷史引文**不得被報紅。

    ``AI_WORKFLOW.md`` 有一段逐字記著「原文寫的某兩個行號今日已分別指到另外兩個」，
    那四個數字**就是論證本身**。它們是不帶路徑的裸「冒號 ＋ 數字」⇒ 在 k=0 的形態下
    **構造上不是合格指標**，本守衛看不到它們。

    ⚠️ 這是**判準性的**，⛔ 不是運氣：下面直接對那幾行跑 ``find_pointers``，要求零命中。
    若哪天有人給形態加上回看窗，這條會立刻轉紅並逼出重新裁決。

    ⚠️ 錨點是那句話的逐字片段，⛔ 不是行號（用行號會犯本守衛正在治的病）。若該句被
    改寫，本測試會因為找不到錨點而紅——那時要重新確認守衛仍然看不到它。
    """
    text = (_REPO_ROOT / "AI_WORKFLOW.md").read_text(encoding="utf-8")
    anchored = [line for line in text.splitlines() if "今日已分別指到" in line]
    assert anchored, "找不到 V11 特例化的錨點句，須重新確認守衛對那段歷史引文的行為"
    exts = qps.tracked_extensions(qps.tracked_files(_REPO_ROOT))
    for line in anchored:
        assert qps.find_pointers(line, exts) == ((), ()), line


# ==========================================================================
# ``--census``：k=0 放掉的那一族有多大，以及 k=1 為什麼不採用
# ==========================================================================


def test_the_census_states_how_big_the_released_family_is():
    """⭐ 誠實邊界要**有數字**：k=0 放掉的那一族今天有多少個，⛔ 不得只說「有一些」。"""
    data = qps.census(_REPO_ROOT)
    assert data.qualified > 0
    assert data.released > 0
    assert data.colon_numbers == data.qualified + data.released
    assert 0 < data.k0_coverage < 1


def test_the_k1_lookback_window_binds_things_k0_does_not():
    """k=1 的新增綁定與 k=0 的命中**不相交**，且今天真的存在——對照組不是空的。

    ⛔ 若這裡是空的，「k=0 比 k=1 乾淨」就成了無法反駁的宣稱；有樣本才有得比。
    每一筆的原文都由 ``--census`` 印出來供人逐筆裁決是不是誤綁。
    """
    data = qps.census(_REPO_ROOT)
    assert data.k1_extra, "k=1 對照組是空的，這個比較變成零資訊"
    assert data.k1_coverage > data.k0_coverage
    exts = qps.tracked_extensions(qps.tracked_files(_REPO_ROOT))
    for _rel, _lineno, _previous, token, _text in data.k1_extra:
        assert qps.find_pointers(token, exts) == ((), ())


# ==========================================================================
# 當指令跑
# ==========================================================================


def test_cli_exits_nonzero_when_something_is_wrong(tmp_path, capsys):
    """守衛要能當指令跑：有紅就非零離開，否則掛不進任何閘門。"""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "real.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "BAD.md").write_text(_line("見 ", "src/real.py", 900), encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)

    assert qps.main(["--root", str(tmp_path)]) == 1
    assert "BAD.md" in capsys.readouterr().out


def test_cli_exits_zero_on_the_real_repo(capsys):
    """同一支指令對真實 repo 必須是 0——測試與人手動跑的是同一份判準。"""
    assert qps.main(["--root", str(_REPO_ROOT)]) == 0
    capsys.readouterr()


def test_census_mode_runs_and_exits_zero(capsys):
    """``--census`` 是量測模式，⛔ 不是閘門：永遠回 0，但必須印出那一族的大小。"""
    assert qps.main(["--root", str(_REPO_ROOT), "--census"]) == 0
    out = capsys.readouterr().out
    assert "k=0 放掉的一族" in out
    assert "一無所知" in out
