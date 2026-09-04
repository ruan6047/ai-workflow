"""釘住 `R3-001`，以及 `R2-003` 那一半屬於 artifact 的修補（`WF-REDESIGN-W3`）。

## `R3-001` —— 同一則訊息自我矛盾

`render_conflict_refusal()` 的開頭逐字寫著「⛔ 這裡刻意不給一行可照貼的重跑指令……
給一行填空樣板只會被照貼，寫進一筆無意義的資源宣告」，而函式**尾端**的
`lines.append` 又 append 了正是那一行：

    wfcli amend {card_id} --resources file:收窄後的路徑 --reason '…'

成因（⛔ 不美化）：R2 那一輪只換掉了 `lines = [...]` 這個**頭**，⛔ 沒讀完函式尾巴。

## 為什麼 R2 的測試沒抓到——**兩條都名不副實**

查核者逐字：

1. `test_r2_fixes` 的 `..._carries_a_human_fill_slot` 宣稱「沒有任何指令行含人工
   填空」，實際只檢查 `placeholder_lines`，而該欄**只認角括號樣式** ⇒ 中文
   `file:收窄後的路徑` 進不去。（⚠️ 那條測試 2026-09-03 已隨擷取器一起刪除；
   ⛔ 此處⛔ 不寫行號——它已經漂過一次了。）
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


#: 測試側的**嚴格**填空判準：一條指令行扣掉 f-string 欄位之後還剩 CJK ⇒ 可疑。
#:
#: ⚠️ 它比 artifact 的判準 (iii) **嚴格**，且會誤中真的值 ⇒ ⛔ 不能無差別套到全語料，
#: 只套在**本輪明文修過的那幾則**上（那幾則的指令行構造上⛔ 不該有任何中文）。
_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def _fill_slots(command_line: str) -> str:
    """扣掉執行期會被代入真值的部分，回傳剩下的可疑字元。"""
    stripped = command_line.replace("{…}", "")
    return "".join(_CJK.findall(stripped)) + "".join(re.findall(r"<[^<>\n]{1,60}>", stripped))


#: 可整行複製的指令行的首 token（封閉集合，規劃階段規格裁定 17）。
_RUNNABLE_HEADS = ("wfcli", "git", "gh")


def _command_lines(text: str) -> list[str]:
    """從**真的訊息輸出**撈出可整行複製的指令行。

    ⚠️ **2026-09-03 改為就地實作**：原本呼叫 `rejection_inventory._command_lines`，
    那支已隨 artifact 砍成純清單而移除。⭐ 這裡讀的是
    `render_conflict_refusal()` 的**實際回傳字串**，⛔ 不是任何 AST 重建。
    """
    return [
        line for line in (raw.strip().strip("`") for raw in text.splitlines())
        if line.startswith(_RUNNABLE_HEADS)
    ]


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
        for line in _command_lines(text)
        if _fill_slots(line)
    }
    assert offenders == {}, offenders


def test_the_final_output_still_offers_at_least_one_runnable_command():
    """⛔ 刪掉填空⛔ 不等於刪掉補救——訊息仍要給得出可跑的東西。"""
    conflicts = detailed_conflicts(
        _decl("file:cli/src/"), "OTHER-CARD", _decl("file:cli/src/wf_cli/doctor.py")
    )
    lines = _command_lines(render_conflict_refusal("MY-CARD", conflicts))
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


# ==================== (3) ⚠️ 一條**已刪除**的檢查，⛔ 無承接者

# ⛔ 這裡原本有 `test_no_command_line_in_the_corpus_carries_a_cjk_written_value`：
# 它對本輪改過的六則訊息（`assign_cmd:246`／`:420`／`checkpoint_cmd:231`／`:301`／
# `open_cmd:573`／`review_cmd:201`）逐條檢查指令行**⛔ 不含中文填空**。
#
# ⚠️ **2026-09-03 刪除，且⛔ 沒有承接者。** 它唯一的機制是 artifact 的
# `mechanical.command_lines`，而 artifact 已依需求方裁定砍成純清單
# （逐字「有疑慮的機械產生資訊寧願不要」）。
#
# ⛔ **⛔ 不改寫成「直接 grep 原始碼」**：那會誤中**真的**中文值——同一個檔裡就有
# `--reason '修復資源宣告區塊的排版'`，那是一句寫好的理由、⛔ 不是佔位。機械上
# **⛔ 沒有規則**分得開「描述要填什麼」與「就是那個值」。
#
# ⇒ **中文填空這一面現在⛔ 無機械檢查。** `render_conflict_refusal` 那一則由本檔
# 上方的可證偽 ③ 斷言涵蓋；**其餘五則⛔ 無涵蓋**，只剩 PM／查核者的人工判斷。
# ⛔ 不得由「`<…>` 那條還在」推出「填空這一面守住了」——那兩者是不同的樣式。
