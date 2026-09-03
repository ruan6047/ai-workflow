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
        assert (rows[0].line, rows[0].verb, rows[0].keyword) == (3, "amend", "拒絕")
    finally:
        (tmp / "probe.py").unlink(missing_ok=True)
        tmp.rmdir()


# ---- (2) ⚠️ 一整組**已刪除**的測試（原：裁定 17 三條機械必要條件的逐條正負例）----

# ⛔ 這一節原本有三條，全部驗**擷取器**：`test_three_mechanical_conditions`（9 個
# parametrize 正負例）、`test_runnable_heads_is_a_closed_set`、
# `test_mechanical_records_each_condition_separately`。
#
# ⚠️ **2026-09-03 全刪**：它們驗的對象（`Mechanical`／`_evaluate()`／`RUNNABLE_HEADS`）
# 已依需求方裁定移除——逐字「**如果有疑慮的機械產生資訊寧願不要 只需要確認該項目再
# 確認清單 交給ＡＩ處裡**」。⛔ 這些測試驗的是**擷取器**、⛔ 不是訊息本身，
# 對象不存在了 ⇒ 刪除，⛔ 不改成弱斷言。
#
# ⚠️ **⛔ 不得由此推出「那三條判準被否定了」**：它們是**判準的機械承載**被移除，
# 判準本身（訊息該給得出可跑的補救）改由 PM／AI 逐則裁定承載。


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


# ---- (6) 母體層次（需求方 2026-09-02 裁定：「≥37 則」已撤）----


def test_the_two_population_layers_are_nested_and_distinct():
    """全集 ⊇ 可動母體，且**兩者的定義不同**。

    ⚠️ **2026-09-03 由三層縮為兩層**：第三層「可補母體」（再扣註解與 docstring）
    倚賴 `kind`，而 `kind` 的 `docstring` 那一格要 parse AST ⇒ 落入需求方逐字要砍的
    「有疑慮的機械產生資訊」。⇒ `kind` 與該層一起移除。
    ⛔ **這⛔ 不代表 2026-09-02「註解與 docstring 不是訊息」的裁定失效**——它從
    「機械欄位」變成 **PM 逐則裁定裡的一行**（與「一則多態」的處理同構）。

    ⚠️ 卡面原本的「**≥37 則**」門檻已由需求方 2026-09-02 **撤除**。
    ⇒ 本檔⛔ 不斷言任何門檻數字，只釘**口徑**。
    """
    rows = ri.scan(_SRC)
    in_scope = [r for r in rows if r.in_scope]
    assert len(in_scope) < len(rows), "非射程扣除必須真的扣到東西，否則這層是零資訊的"
    # 全集的口徑**⛔ 不因分類而改**——它就是釘死的 grep。
    assert len(rows) == len(_grep_rows())


# ---- ⚠️ 全語料 `<…>` 掃描：**實測後⛔ 不採**，理由逐條在下 ----
#
# PM 於 2026-09-03 指定把 `test_the_remedy_commands_contain_no_placeholder_at_all`
# 改成「**直接 grep 原始碼**、⛔ 不經任何重建」。⭐ 方向是對的（那樣就沒有衍生欄位的
# 疑慮），但**實作出來之後量到它 100% 誤報**，⇒ ⛔ 不採，改由下面說的地方承接。
#
# 實測（`cli/src`，扣兩支非射程 deploy 檔，判準＝行首是 wfcli/git/gh 且含 `<…>`）：
# **4 命中，0 個是真的違規**——
#   card.py:470        `"""git spec 檔骨架（寫入目標 repo ``tasks/<CARD_ID>.md``）。"""`
#                      ⇒ docstring 第一個詞剛好是「git」，**純散文**
#   amend_cmd.py:693   `gh issue view <N> --repo <owner/repo> --json body --jq .body > …`
#   amend_cmd.py:706   `wfcli amend {card_id} --repo <owner/repo> … --spec-baseline '<現值>'`
#                      ⇒ 兩者都在 **docstring** 裡，是**寫給人看的手動 runbook**，
#                        `<N>`／`<owner/repo>` 在那裡是**正確**的寫法
#   amend_cmd.py:1114  訊息裡用反引號**提到** `gh project item-edit --id <DI_…>`
#                      ⇒ 「散文提及」，舊判準以行首排除，原始碼層排除不掉
#
# ⚠️ **根因**：要分辨「一行看起來像指令的字」到底是**訊息**、**docstring** 還是
# **散文提及**，需要 `kind`／AST——而那正是本輪依需求方裁定移除的東西。
# ⇒ 原始碼層的 `<…>` 掃描**在構造上做不到**，⛔ 不是實作沒寫好。
#
# ⇒ **`<…>` 禁令改由「訊息實際輸出」那一層承接**，⛔ 沒有消失：
#   `test_r2_fixes.test_that_refusal_carries_a_runnable_remedy`（真 stderr）
#   `test_r2_fixes.test_the_review_refusal_still_offers_a_runnable_command`（真 stderr）
#   `test_note_roster.test_the_refusal_message_carries_no_placeholder`（真 stderr）
#   `test_r3_fixes` 的可證偽 ③ 斷言（`render_conflict_refusal()` 的真回傳值）
# ⚠️ **射程明說**：那四處只涵蓋**它們各自觸發的那幾則**，⛔ 不是全語料。
#   ⇒ **全語料的 `<…>` 覆蓋⛔ 已失去**，⛔ 不得由「還有四處在守」推出「全都守住了」。



# ---- (7) ⚠️ 原「第四／五／六個 artifact 缺陷」那一組已隨擷取器一起刪除 ----
