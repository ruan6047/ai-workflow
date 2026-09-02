"""釘住拒絕訊息盤點的**口徑**（`WF-REDESIGN-W3` 驗收 4 的 artifact 產生器）。

本檔要擋的三件事：

1. **口徑漂離規格釘死的量法。** 卡面驗收 4 的量法逐字是
   ``grep -rnoE '\\[[a-z-]+\\] 拒[絕收]' --include='*.py' cli/src``，而分母 61 是建立在
   它的今日值 **73** 上。⇒ 盤點器的總數與逐檔分佈**必須與該 grep 逐位元相同**。
   ⚠️ 首版用 ``ast.walk`` 定位，因 ``JoinedStr`` 與其內部 ``Constant`` 被重複訪問而
   實測得 **109**（>73）——那個回歸由第一條測試擋住。
2. **三條機械必要條件被悄悄放寬。** 裁定 17 逐字三條（含指令／首 token ∈
   ``{wfcli,git,gh}``／⛔ 不含 ``<…>`` 佔位符），**同時成立**才算 pass。任一條被拿掉、
   或首 token 集合被擴張，第二組測試轉紅。
3. **非射程的兩支動詞檔被算進可動母體。** 卡面非射程逐字「⛔ 不動 ``deploy-state``／
   ``deploy-declare``」⇒ 它們**進全集、⛔ 不進可動母體**。

⛔ **本檔⛔ 不測「訊息有沒有跑得出的補救」**——那是內容判斷，決議 `:70` 逐字歸 PM。
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts" / "rejection_inventory.py"
_SRC = _REPO_ROOT / "cli" / "src"

_spec = importlib.util.spec_from_file_location("rejection_inventory", _SCRIPT)
assert _spec is not None and _spec.loader is not None
ri = importlib.util.module_from_spec(_spec)
sys.modules["rejection_inventory"] = ri
_spec.loader.exec_module(ri)


def _grep_rows() -> list[str]:
    """規格釘死的量法，**原樣跑**。⛔ 不在測試裡重寫一份等價實作（`F-執行-06`）。"""
    proc = subprocess.run(
        ["grep", "-rnoE", r"\[[a-z-]+\] 拒[絕收]", "--include=*.py", str(_SRC)],
        capture_output=True,
        text=True,
        check=False,
    )
    # grep 零命中回 1；本語料今日非零，零命中即語料出問題 ⇒ 讓它炸而不是靜默過。
    assert proc.returncode == 0, f"grep rc={proc.returncode}；語料可能有問題"
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


# ---- (1) 口徑：總數與逐檔必須與規格釘死的 grep 逐位元相同 ----


def test_total_matches_the_pinned_grep():
    """⭐ 承重：分母 61 建立在 grep 的 73 上，口徑不一致就整個垮掉。"""
    rows = ri.scan(_SRC)
    assert len(rows) == len(_grep_rows())


def test_per_file_matches_the_pinned_grep():
    """逐檔也要一致——只比總數會漏掉「某檔多算、另一檔少算」互相抵銷的情形。"""
    expected: dict[str, int] = {}
    for line in _grep_rows():
        path = line.split(":", 1)[0]
        expected[Path(path).name] = expected.get(Path(path).name, 0) + 1

    actual: dict[str, int] = {}
    for row in ri.scan(_SRC):
        actual[Path(row.file).name] = actual.get(Path(row.file).name, 0) + 1

    assert actual == expected


def test_locating_does_not_use_ast_walk_over_string_nodes():
    """回歸：首版以 ``ast.walk`` 走訪字串節點定位，f-string 被重複計數（109 > 73）。

    ⛔ 這裡⛔ 不斷言實作細節的字面，而是斷言**性質**：同一份語料裡，一則跨多行的
    f-string 拼接訊息**只能算一次**（每個關鍵字 occurrence 一次）。
    """
    sample = (
        "def f():\n"
        '    print(\n'
        '        f"[amend] 拒絕：第一段 {x}"\n'
        '        f"，第二段"\n'
        "    )\n"
        "    return 2\n"
    )
    tmp = _REPO_ROOT / "cli" / "tests" / "__inv_probe__"
    tmp.mkdir(exist_ok=True)
    try:
        (tmp / "probe.py").write_text(sample, encoding="utf-8")
        rows = ri.scan(tmp)
        assert len(rows) == 1, f"跨行 f-string 應只算一次，實得 {len(rows)}"
        # 片段必須含**第二段**——那正是「用 AST 取完整 statement」要換到的東西。
        assert "第二段" in rows[0].statement
    finally:
        (tmp / "probe.py").unlink(missing_ok=True)
        tmp.rmdir()


# ---- (2) 裁定 17 的三條機械必要條件：逐條正負例 ----


@pytest.mark.parametrize(
    "segment,expected",
    [
        # 三條全過
        ('print("[x] 拒絕：請改用 wfcli amend WF-1 --reason foo")', True),
        ('print("[x] 拒絕：請跑 git rev-parse HEAD")', True),
        ('print("[x] 拒絕：請跑 gh issue view 221")', True),
        # (i) 無指令
        ('print("[x] 拒絕：欄位不得為空")', False),
        # (ii) 首 token 不在封閉集合內
        ('print("[x] 拒絕：請跑 python foo.py")', False),
        ('print("[x] 拒絕：請跑 make check")', False),
        # (iii) 含佔位符
        ('print("[x] 拒絕：請改用 wfcli amend <卡ID> --reason foo")', False),
        ('print("[x] 拒絕：請跑 git show <SHA>")', False),
    ],
)
def test_three_mechanical_conditions(segment: str, expected: bool):
    assert ri._evaluate(segment).passes is expected


def test_runnable_heads_is_a_closed_set():
    """封閉值域只能由 owner 裁定擴張——owner 是規劃階段的規格（裁定 17）。"""
    assert ri.RUNNABLE_HEADS == ("wfcli", "git", "gh")


def test_mechanical_records_each_condition_separately():
    """⛔ 不得把三條併成一個布林——PM 判定時要看得出是哪一條沒過。"""
    m = ri._evaluate('print("[x] 拒絕：請改用 wfcli amend <卡ID>")')
    assert m.has_command is True
    assert m.head_ok is True
    assert m.no_placeholder is False
    assert m.passes is False


# ---- (3) 非射程：進全集、⛔ 不進可動母體 ----


def test_out_of_scope_files_are_counted_but_not_in_scope():
    rows = ri.scan(_SRC)
    deploy = [r for r in rows if Path(r.file).name in ri.OUT_OF_SCOPE_FILES]
    assert deploy, "語料裡應有 deploy-state／deploy-declare 的拒絕訊息"
    assert all(r.in_scope is False for r in deploy)

    summary = ri.summarise(rows)
    assert summary["in_scope"] + summary["out_of_scope"] == summary["total"]


def test_out_of_scope_set_matches_the_card_face():
    """卡面非射程逐字只點名這兩支動詞，⛔ 不得多列也⛔ 不得少列。"""
    assert ri.OUT_OF_SCOPE_FILES == frozenset(
        {"deploy_state_cmd.py", "deploy_declare_cmd.py"}
    )


# ---- (4) PM 判定欄位一律留空 ----


def test_pm_verdict_fields_are_never_filled_by_the_script():
    """⛔ 內容判斷不由機械代算（決議 `:70` 逐字「PM 判」）。"""
    rows = ri.scan(_SRC)
    assert all(r.pm_verdict == "" and r.pm_remedy == "" for r in rows)


# ---- (5) 負控：證明比對真的會響 ----


def test_negative_control_the_comparison_actually_fires():
    """`pm-conduct` 四逐字「引用 0 命中前先證工具會響」的同族紀律。

    ⛔ 不改語料，改**期望值**——把 grep 的結果人為加一筆，斷言比對轉紅。
    """
    rows = ri.scan(_SRC)
    inflated = len(_grep_rows()) + 1
    assert len(rows) != inflated, "比對若不會響，第一條測試就是零資訊"


def test_keyword_regex_is_the_card_face_literal():
    """關鍵字集⛔ 不得改寫——改了就不是同一個母體。"""
    assert ri.KEYWORD_RE.pattern == r"\[[a-z-]+\] 拒[絕收]"
    # 正控：該樣式確實命中今日語料
    assert re.search(ri.KEYWORD_RE, "print('[handoff] 拒絕：foo')")


# ---- (6) 卡面驗收 3 的門檻：**≥37 則**（2026-09-02 落地）----


def test_at_least_thirty_seven_in_scope_messages_carry_a_runnable_remedy():
    """卡面驗收 3 逐字「**≥37 則**拒絕訊息補『跑得出』補救」。

    ⚠️ **三件事必須一起讀，⛔ 不得只看這個數字：**

    1. **這是必要非充分。** 三條機械條件說的是「值得 PM 看」，⛔ 不是「補救跑得出
       來」。判定者是 PM（決議 `:70` 逐字）。
    2. **母體在本卡執行期間變大了**：開卡時全集 73／可動 61，本卡自己新增的拒收
       訊息（驗收 4／7／8 各帶新訊息）使它變成 77／65。門檻是**絕對數 37**，
       ⛔ 不是比例，故母體變大⛔ 不放寬要求。
    3. **可動母體裡有 7 則根本不是訊息**（5 則註解＋2 則 docstring，是**描述**訊息
       形狀的文字）——釘死的 grep 口徑把它們算了進來。真訊息 **58 則**。
       ⇒ 分母的性質與卡面寫下 61 時的假設不同，這一點已寫進交付報告。
    """
    rows = [r for r in ri.scan(_SRC) if r.in_scope]
    passing = [r for r in rows if r.mechanical.passes]
    assert len(passing) >= 37, (
        f"只有 {len(passing)} 則通過三條機械必要條件，卡面門檻是 ≥37"
    )


def test_the_remedy_commands_contain_no_placeholder_at_all():
    """裁定 17 第 (iii) 條的全域複查。

    ⚠️ ⛔ 不得用 `<在此填寫>` 這種**指令**佔位（`intake.py` 逐字）。訊息可以有
    **內容**佔位，但那必須寫在指令之外——本測試量的正是「指令本身」。
    """
    offenders = [
        (r.file, r.line, r.mechanical.command)
        for r in ri.scan(_SRC)
        if r.in_scope and r.mechanical.has_command and not r.mechanical.no_placeholder
    ]
    assert offenders == [], offenders
