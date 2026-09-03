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


# ---- (7) `<…>` 佔位禁令：全語料掃描 ＋ **明文 allowlist ＋ 負向 fixture** ----
#
# ⚠️ **本節 2026-09-03 recovered（`R5-002`）。** 它一度被移除，理由是「原始碼層的掃描
# 在構造上做不到」——**那個結論是錯的**。查核者逐字：「**四個合法命中⛔ 不代表掃描
# 構造上做不到**」，處置是 **allowlist ＋ 負向 fixture**：既有命中**逐筆核准**、
# **任何新增命中必須轉紅**。
# ⭐ 為什麼那個反駁成立：它把**開放集合換成封閉集合**。要判「這一行是碼還是散文」
# 需要 AST（本卡已依裁定刪除）；但要判「這一行**在不在那四筆逐字黃金值裡**」
# **⛔ 不需要分辨任何東西**。⛔ 執行者與 PM 都沒想到，查核者想到了。

#: 指令佔位樣式。``<…>`` 之間⛔ 不含換行與 ``>``。
_ANGLE_SLOT_RE = re.compile(r"<[^<>\n]{1,60}>")

#: 可整行複製的指令行的首 token（封閉集合，規劃階段規格裁定 17）。
_RUNNABLE_HEADS = ("wfcli", "git", "gh")

#: ⭐ **逐筆核准的既有命中**，鍵是 ``(檔名, 該行的逐字內容)``。
#:
#: ⚠️ **鍵刻意⛔ 不含行號**：行號會漂（本卡已因此腐爛過三條 docs 指標）。用**逐字
#: 黃金值**當鍵 ⇒ 那一行只要被改動一個字，它就從 allowlist 掉出來、必須重新核准。
#:
#: ⚠️ **核准的是「這一行不是拒絕訊息裡的指令」，⛔ 不是「這個佔位沒問題」。**
#: 四筆各自的理由寫在 value 裡，⛔ 不得只寫「已知」。
_APPROVED_ANGLE_SLOT_HITS: dict[tuple[str, str], str] = {
    (
        "card.py",
        "git spec 檔骨架（寫入目標 repo ``tasks/<CARD_ID>.md``）。",
    ): "`render_spec_markdown` 的 docstring 第一句；首詞剛好是 `git` ⇒ 純散文，⛔ 非指令行",
    (
        "amend_cmd.py",
        "gh issue view <N> --repo <owner/repo> --json body --jq .body > /tmp/body.md",
    ): "docstring 裡**寫給人看的手動 runbook**；`<N>`／`<owner/repo>` 在那裡是正確寫法",
    (
        "amend_cmd.py",
        "wfcli amend {card_id} --repo <owner/repo> --reason 驗證排版 --dry-run "
        "--spec-baseline '<現值>",
    ): "同一段手動 runbook 的第二行；`<owner/repo>`／`<現值>` 要人代入，那是 runbook 的用途",
    (
        "amend_cmd.py",
        "gh project item-edit --id <DI_…> --title`，是另一條 ID 命名空間",
    ): "訊息裡用反引號**提到**一條指令（散文提及）⇒ ⛔ 不是給人整行貼上去跑的",
}


def _peel(raw: str) -> str:
    """把一行原始碼剝到「它印出來時長什麼樣」——**反覆**剝空白與引號直到不再變。

    ⚠️ **⛔ 不得寫成一次性的 `.strip().strip('"')`**：訊息的真實形狀是
    ``    "    wfcli amend … "``——**引號內側還有縮排**。剝一次只會剝掉外層引號，
    留下的 ``    wfcli …`` 因為前導空白而**不以 runnable head 起首** ⇒ 整條檢查對
    **最該抓的那個形狀**視而不見。
    ⭐ 這個洞是 2026-09-03 寫負向 fixture 時**當場量到**的（第一版探針沒轉紅），
    ⛔ 不是事後推理出來的。
    """
    line = raw
    while True:
        peeled = line.strip().strip('"').strip("'").strip("`")
        if peeled == line:
            return peeled
        line = peeled


def _angle_slot_hits(root: Path) -> list[tuple[str, int, str]]:
    """全語料掃描：行首是三個 runnable head 之一、且含 ``<…>`` 的行。

    ⚠️ **能力上界，明說**：它看的是**原始碼的行**，⛔ 不是執行期輸出。被字串拼接
    切斷的指令、以及執行期才組出來的那些，本檢查**看不到**。
    ⛔ 這是「是否有」層級的檢查，⛔ 不是完備性保證。
    """
    hits: list[tuple[str, int, str]] = []
    for path in sorted(root.rglob("*.py")):
        if path.name in ri.OUT_OF_SCOPE_FILES:
            continue
        for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = _peel(raw)
            if line.startswith(_RUNNABLE_HEADS) and _ANGLE_SLOT_RE.search(line):
                hits.append((path.name, lineno, line))
    return hits


def test_no_unapproved_angle_bracket_slot_in_any_command_line():
    """⭐ **承重**：任何**新增**的 `<…>` 指令佔位必須轉紅（`R5-002`）。

    `intake.py` 逐字禁止 `<在此填寫>` 這種**指令**佔位；本卡的失誤 #41 也是這一條
    抓到的（首版把填空改成 `<…>` 放進指令行，該測試立刻轉紅）。
    """
    unapproved = [
        (name, lineno, line)
        for name, lineno, line in _angle_slot_hits(_SRC)
        if (name, line) not in _APPROVED_ANGLE_SLOT_HITS
    ]
    assert unapproved == [], unapproved


def test_every_approved_entry_still_matches_a_real_line():
    """⛔ allowlist 自己⛔ 不得腐爛：核准了卻已不存在的項目一律轉紅。

    ⭐ 方向刻意與上一條**相反**——上一條擋「多出來的」，這一條擋「留下來的死條目」。
    ⛔ 少了這一條，allowlist 會變成一份只進不出的清單。
    """
    live = {(name, line) for name, _lineno, line in _angle_slot_hits(_SRC)}
    stale = sorted(set(_APPROVED_ANGLE_SLOT_HITS) - live)
    assert stale == [], stale


def test_every_approved_entry_carries_a_reason():
    """⛔ 核准必須說得出理由——`已知`／空字串⛔ 不算。"""
    for key, reason in _APPROVED_ANGLE_SLOT_HITS.items():
        assert len(reason) >= 20, (key, reason)


def test_the_scan_actually_fires_on_a_new_hit(tmp_path):
    """⭐ **負向 fixture**（裁定逐字要求）：注入一行新的佔位指令，掃描必須抓到。

    ⛔ 少了這一條，上面那三條全部可能是**零資訊的**——一個永遠掃不到東西的掃描
    也會讓 `unapproved == []` 成立。
    """
    src = tmp_path / "wf_cli"
    src.mkdir()
    # ⚠️ 刻意寫成**訊息的真實形狀**：指令自成一行、**且在引號內側還有縮排**。
    # 第一版 fixture 沒有那層縮排 ⇒ 它通過了，而真語料裡的形狀會被漏掉。
    (src / "probe.py").write_text(
        'def f():\n'
        '    print(\n'
        '        "[x] 拒絕：改用\\n"\n'
        '        "    wfcli amend <卡ID> --reason foo",\n'
        '    )\n',
        encoding="utf-8",
    )
    hits = _angle_slot_hits(tmp_path)
    assert len(hits) == 1, hits
    assert hits[0][0] == "probe.py"
    assert "<卡ID>" in hits[0][2]
    assert (hits[0][0], hits[0][2]) not in _APPROVED_ANGLE_SLOT_HITS


def test_out_of_scope_files_are_skipped_by_the_scan():
    """兩支 deploy 動詞檔是卡面逐字排除的射程外 ⇒ 掃描⛔ 不看它們。"""
    assert all(name not in ri.OUT_OF_SCOPE_FILES for name, _l, _t in _angle_slot_hits(_SRC))


# ---- (7) ⚠️ 原「第四／五／六個 artifact 缺陷」那一組已隨擷取器一起刪除 ----
