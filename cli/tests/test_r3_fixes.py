"""釘住 `R3-001`，以及 `R2-003` 那一半屬於 artifact 的修補（`WF-REDESIGN-W3`）。

## `R3-001` —— 同一則訊息自我矛盾

`render_conflict_refusal()` 的開頭逐字寫著「⛔ 這裡刻意不給一行可照貼的重跑指令……
給一行填空樣板只會被照貼，寫進一筆無意義的資源宣告」，而函式**尾端**的
`lines.append` 又 append 了正是那一行：

    wfcli amend {card_id} --resources file:收窄後的路徑 --reason '…'

成因（⛔ 不美化）：R2 那一輪只換掉了 `lines = [...]` 這個**頭**，⛔ 沒讀完函式尾巴。

## 為什麼 R2 的測試沒抓到——**兩條都名不副實**

查核者逐字：

1. `test_r2_fixes.py:392` 宣稱「沒有任何指令行含人工填空」，實際只檢查
   `placeholder_lines`，而該欄**只認角括號樣式** ⇒ 中文 `file:收窄後的路徑` 進不去。
2. 另一條只要求「以乾淨 command 開頭」⇒ 前面加 `wfcli amend --help` 就過。

⇒ disposition 逐字：「測試須檢查 `render_conflict_refusal()` 的**最終輸出及其中所有
指令行**，⛔ 不得只檢查第一個乾淨命令或角括號樣式。」本檔就是那一條。

## ⛔ 一個⛔ 不得由本檔綠燈推出的東西

本檔的 CJK 判準是**測試側**的嚴格檢查，⛔ **不是** artifact 的判準 (iii)。
artifact 側 `cjk_value_lines` 仍只是**候選清單**、⛔ 不進 `passes`——因為它會誤中
**真的值**（`--reason '修復資源宣告區塊的排版'`）。
⚠️ 「CJK 值該不該一律判成佔位」是**規格層**的問題，⛔ 不由執行者自行決定，已上呈。
⇒ ⛔ 不得把本檔讀成「判準 (iii) 已涵蓋中文填空」。
"""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
from pathlib import Path

import pytest

from wf_cli.commands.assign_cmd import render_conflict_refusal
from wf_cli.resources import ResourceDeclaration, detailed_conflicts

_REPO_ROOT = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location(
    "rejection_inventory", _REPO_ROOT / "scripts" / "rejection_inventory.py"
)
assert _spec is not None and _spec.loader is not None
ri = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("rejection_inventory", ri)
_spec.loader.exec_module(ri)

#: 測試側的**嚴格**填空判準：一條指令行扣掉 f-string 欄位之後還剩 CJK ⇒ 可疑。
#:
#: ⚠️ 它比 artifact 的判準 (iii) **嚴格**，且會誤中真的值 ⇒ ⛔ 不能無差別套到全語料，
#: 只套在**本輪明文修過的那幾則**上（那幾則的指令行構造上⛔ 不該有任何中文）。
_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def _fill_slots(command_line: str) -> str:
    """扣掉執行期會被代入真值的部分，回傳剩下的可疑字元。"""
    stripped = command_line.replace("{…}", "")
    return "".join(_CJK.findall(stripped)) + "".join(re.findall(r"<[^<>\n]{1,60}>", stripped))


def _decl(*resources: str) -> ResourceDeclaration:
    return ResourceDeclaration(db_scope="none", resources=list(resources))


# ================================ (1) R3-001：最終輸出的**每一條**指令行

@pytest.mark.parametrize(
    "mine,theirs",
    [
        ("file:cli/src/", "file:cli/src/wf_cli/doctor.py"),
        ("file:a", "file:a/b"),
        ("file:a/b.md", "file:a/b.md"),
        ("db:production:schema", "db:production:schema"),
    ],
)
def test_no_command_line_in_the_final_output_carries_a_fill_slot(mine, theirs):
    """⭐ **本檔的承重測試**（`R3-001` disposition 逐字）。

    量的是 `render_conflict_refusal()` 的**最終輸出**與**其中所有指令行**，
    ⛔ 不是第一條、⛔ 不是角括號樣式。修補前第二條指令行是
    `wfcli amend {…} --resources file:收窄後的路徑 …` ⇒ 這一條會紅。
    """
    conflicts = detailed_conflicts(_decl(mine), "OTHER-CARD", _decl(theirs))
    assert conflicts, "測試前提：這一對必須真的相交"
    text = render_conflict_refusal("MY-CARD", conflicts)

    offenders = {
        line: _fill_slots(line)
        for line in ri._command_lines(text)
        if _fill_slots(line)
    }
    assert offenders == {}, offenders


def test_the_final_output_still_offers_at_least_one_runnable_command():
    """⛔ 刪掉填空⛔ 不等於刪掉補救——訊息仍要給得出可跑的東西。"""
    conflicts = detailed_conflicts(
        _decl("file:cli/src/"), "OTHER-CARD", _decl("file:cli/src/wf_cli/doctor.py")
    )
    lines = ri._command_lines(render_conflict_refusal("MY-CARD", conflicts))
    assert lines == ["wfcli amend --help"], lines


def test_the_message_no_longer_contradicts_itself():
    """開頭宣告「⛔ 不給填空樣板」，⇒ 全文就**⛔ 不得**出現那個樣板的字面。"""
    conflicts = detailed_conflicts(_decl("file:a"), "OTHER", _decl("file:a/b"))
    text = render_conflict_refusal("MY-CARD", conflicts)
    assert "⛔ 這裡刻意**不給一行可照貼的重跑指令**" in text
    assert "file:收窄後的路徑" not in text, "宣告與內容自我矛盾"


def test_the_narrowing_direction_is_still_there_for_every_conflict():
    """要件 ③ **⛔ 未被拿掉**：每一則衝突各附一句收窄方向。"""
    conflicts = detailed_conflicts(
        _decl("file:a", "file:c"), "OTHER", _decl("file:a/b", "file:c/d")
    )
    assert len(conflicts) == 2
    text = render_conflict_refusal("MY-CARD", conflicts)
    assert text.count("收窄：") == 2


# ============ (2) R2-003 的 artifact 那一半：一則訊息 ≠ 一個 statement

def test_a_message_built_by_appends_is_read_whole():
    """⭐ **`R2-003` 的病灶**：舊版只取含關鍵字的**最近一個 statement**。

    ⇒ `lines = [...]` 之後的 `lines.append(...)` 完全看不見，而 `R3-001` 的填空
    指令正是 append 上去的。
    """
    src = (
        "def f(card_id):\n"
        "    lines = ['[assign] 拒絕：x\\n    wfcli amend --help']\n"
        "    lines.append('    wfcli amend C1 --resources file:收窄後的路徑')\n"
        "    return '\\n'.join(lines)\n"
    )
    tree = ast.parse(src)
    stmt = ri._enclosing_statement_at(tree, 2)
    parts = ri._message_statements(tree, stmt)
    assert len(parts) == 2, ast.dump(stmt)
    verdict = ri._evaluate("", 1, stmt, None, parts)
    assert verdict.command_lines == [
        "wfcli amend --help",
        "wfcli amend C1 --resources file:收窄後的路徑",
    ]


def test_a_plain_print_message_is_unchanged_by_the_accumulator_expansion():
    """⛔ 不得波及那 50 幾則 `print(...)` 形狀的訊息——它們沒有累加器。"""
    tree = ast.parse("def f():\n    print('[x] 拒絕：y\\n    wfcli x --help')\n")
    stmt = ri._enclosing_statement_at(tree, 2)
    assert ri._message_statements(tree, stmt) == [stmt]


def test_the_span_ceiling_is_per_statement_not_the_sum():
    """⚠️ 切界上限量的是「**一個** statement 被撐成整個函式」。

    一則訊息由多個 append 累加而成是**正常形狀**；把它們的行數加總去撞上限，會把
    合格的判成切界失敗。⇒ 上限逐條套在每個 statement 上。
    """
    body = "\n".join(f"    lines.append('    wfcli x{i} --help')" for i in range(30))
    tree = ast.parse(f"def f():\n    lines = ['[x] 拒絕：y']\n{body}\n")
    stmt = ri._enclosing_statement_at(tree, 2)
    parts = ri._message_statements(tree, stmt)
    assert len(parts) == 31
    span = max((n.end_lineno or n.lineno) - n.lineno + 1 for n in parts)
    assert span == 1
    assert ri._evaluate("", span, stmt, None, parts).boundary_ok is True


def test_the_artifact_now_exposes_every_command_line_for_the_pm_reconciliation():
    """`R2-003` disposition 逐字「artifact 或 PM 輸入必須涵蓋**完整實際輸出**」。

    ⇒ `command_lines` 是 PM 做 60 列逐列裁定時該看的欄；`command` 只是第一條。
    實測全語料**有 11 則的指令行超過一條** ⇒ 只看 `command` 會漏掉那 11 則的後半。
    """
    multi = [
        (r.file.split("/")[-1], r.line, r.mechanical.command_lines)
        for r in ri.scan(_REPO_ROOT / "cli" / "src")
        if r.in_scope and r.kind == "message" and len(r.mechanical.command_lines) > 1
    ]
    assert multi, "若這裡變成空的，代表 command_lines 又退回只記一條"
    for _file, _line, lines in multi:
        assert len(set(lines)) == len(lines), (_file, _line, lines)


# ==================== (3) 本輪明文修過的那幾則：整則⛔ 無中文填空

#: 本輪（R2＋R3）明文改過重跑形狀的訊息。⛔ 不是全語料——見模組 docstring 的上界。
_REWRITTEN = {
    ("assign_cmd.py", 246),
    ("assign_cmd.py", 420),
    ("checkpoint_cmd.py", 231),
    ("checkpoint_cmd.py", 301),
    ("open_cmd.py", 573),
    ("review_cmd.py", 201),
}


def test_no_command_line_in_the_corpus_carries_a_cjk_written_value():
    """本輪改過的六則，**每一條**指令行都⛔ 不得含中文填空或 `<…>`。

    ⚠️ 射程只有這六則，⛔ 不是全語料：全語料裡有**真的**中文值
    （`--reason '修復資源宣告區塊的排版'`），把它們一併判紅是把合格的算成不合格。
    ⇒ 這一條與 artifact 的判準 (iii) **刻意不同**，差別寫在模組 docstring。
    """
    rows = {
        (r.file.split("/")[-1], r.line): r
        for r in ri.scan(_REPO_ROOT / "cli" / "src")
        if r.in_scope and r.kind == "message"
    }
    missing = _REWRITTEN - set(rows)
    assert not missing, f"行號漂了，先更新 _REWRITTEN：{sorted(missing)}"
    offenders = {}
    for key in sorted(_REWRITTEN):
        for line in rows[key].mechanical.command_lines:
            if _fill_slots(line):
                offenders[f"{key[0]}:{key[1]}"] = line
    assert offenders == {}, offenders
