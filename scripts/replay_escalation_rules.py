#!/usr/bin/env python3
"""回放 ai-workflow#16 的 R1→R8 事件流（外加兩個明確標示的假想 R9），比較
review-escalation.md 修訂前後 `escalation-checkpoint` 的強制升級判定。

執行（repo 根目錄，無第三方相依、不連網）：

    python3 scripts/replay_escalation_rules.py
    uv run --no-project python scripts/replay_escalation_rules.py

結束碼 0 表示全部斷言通過；非 0 表示條文與本腳本編碼的預期行為不一致。

本腳本涵蓋第 173 行的**兩個**條件，兩者都屬「一旦成立即永久為真」的同型缺陷：

    條件1  同 root_cause_id 累計出現於三個唯一可計數 attempt
           → 修訂：加上「在 trigger attempt 仍有有效 open finding」的存活判準
    條件2  前一 attempt 的 accepted blocking finding 未在下一 attempt 被處置
           → 修訂：加上需求方明示的 deferred_findings 出口 + 機械清償上限

--------------------------------------------------------------------------
資料來源與轉錄聲明
--------------------------------------------------------------------------
下方 ATTEMPTS／DEFERRED_DECLARED 是**人工轉錄**自 ruan6047/ai-workflow#16 的
checkpoint 留言中的逐輪 finding 表，非程式抓取。核對來源：

    gh api repos/ruan6047/ai-workflow/issues/comments/<id> -q .body

    5248541311  03:08:40Z  第三個可計數 attempt 前（R1／R2 的 finding 與根因表）
    5248549305  03:10:09Z  需求方裁定：continue，並把 R3 改為窄規格
    5248657740  03:30:33Z  第四個可計數 attempt 前（R3 明文未逐條重驗 R1／R2）
    5248665281  03:31:54Z  需求方裁定（R4）：deferred_findings 的原型出於此則
    5248812931  03:58:11Z  第五個可計數 attempt 前（R4 判 9/10 resolved）
    5248823019  03:59:29Z  需求方裁定（R5）
    5248904826  04:13:30Z  第六個可計數 attempt 前（條件1 首次成立：R3／R4／R5）
    5249003956  04:31:18Z  第七個可計數 attempt 前（條件1 擴大到四個 attempt）
    5249157515  04:58:13Z  第八個可計數 attempt 前（R7；escalate → replan，切出 #23/#24/#25）
    5249245451  05:13:21Z  第九個可計數 attempt 前（R8 的事實部分）
    5249247912  05:13:47Z  ⚠️ 撤回：上則的 escalation_resolution／decided_by 係執行者擅填
    5249260224  05:15:56Z  第九個可計數 attempt 前：需求方**實際**裁定（取代被撤回的欄位）

⚠️ **撤回鏈**：`5249245451` 的裁定欄（`escalation_resolution: continue`／
`decided_by: ruan6047`）已由 `5249247912` 撤回——需求方當時並未裁定，該欄係執行者
擅填。本腳本只採用 `5249245451` 的**事實部分**（R8 的 finding 組成與趨勢表，可由
timeline 獨立查證），裁定一律採 `5249260224` 的取代版本。

轉錄時的四點判斷，供查核者針對性攻擊：

  1. 各輪「再開」的 finding 一律編碼為該輪明列 `open`（＝§4 的「仍開啟」格）。
     留言只說「再開」，未逐字寫 status；此編碼落在 fail-closed 方向。
  2. **R4-001 於 R6 判 resolved 係推導而非明文**：`5249003956` 的 R6 列為
     「blocking 3 ＝ 新 1（R6-001）＋ 再開 2（R5-001／R5-002）」，R4-001 不在其中，
     故必然已於 R6 閉合，否則 R6 的 blocking 應為 4。
  3. R7 的三項「再開」轉錄為 R5-001／R5-002／R6-001（留言只給計數 3 未逐項列名）。
     改變這三個 id 不影響任何結論。
  4. **R8 對 R5-001／R5-002／R7-001 的處置是 `transferred`（→ #24／#23／#25），
     同時降為 `info`／`blocking=false`。** `transferred` 不是 §2 的三個 status 值之一，
     本腳本**不**為它新增狀態；依 §5 末段「仍為 open 但已不符合 §3 可計數 finding 的
     條件…adapter 必須將它移出 open set」，編碼為 `downgraded`（§4 表格第三格）。
     這是既有規則的套用，不是新分類。
"""

from __future__ import annotations

import sys

# --- 根因識別碼（逐字取自 #16 留言）------------------------------------------
RC_MARKER = "marker-scope-narrows-away-safety-signal"
RC_PR = "universal-pr-ci-conflicts-with-canonical-classification"
RC_GEN = "incomplete-custom-classification-overrides-canonical"
RC_SPLIT = "split-composite-transition-without-intermediate-state"

# 處置值：前三者使 finding 離開 open set，"open" 表示明列仍開啟。
CLOSING = ("resolved", "withdrawn", "downgraded")

# (label, 本輪新提出的 accepted blocking finding {id: root_cause}, 對先前 finding 的明示處置)
ATTEMPTS: list[tuple[str, dict[str, str], dict[str, str]]] = [
    (
        "R1",
        {
            "R1-001": "rc-r1-001",
            "R1-002": RC_MARKER,
            "R1-003": "rc-r1-003",
            "R1-004": "rc-r1-004",
            "R1-005": "rc-r1-005",
            "R1-006": RC_PR,
        },
        {},
    ),
    # R2：明列四項閉環；R1-002／R1-006 未閉合，以更窄的殘留形式再次出現。
    (
        "R2",
        {"R2-001": RC_MARKER, "R2-002": RC_PR},
        {"R1-001": "resolved", "R1-003": "resolved",
         "R1-004": "resolved", "R1-005": "resolved"},
    ),
    # R3：依需求方裁定改為窄規格，**明文不逐條重驗 R1／R2** → 對前輪 finding 零處置。
    # 這一格就是本卡條件2 痛點的來源。
    ("R3", {"R3-001": RC_GEN}, {}),
    # R4：規格改回全面複驗，十項中九項一次判 resolved。
    (
        "R4",
        {"R4-001": RC_GEN},
        {"R1-002": "resolved", "R1-006": "resolved", "R2-001": "resolved",
         "R2-002": "resolved", "R3-001": "resolved"},
    ),
    ("R5", {"R5-001": RC_GEN, "R5-002": RC_GEN}, {"R4-001": "open"}),
    # R6：R4-001 於此閉合（見轉錄聲明第 2 點的推導）。
    ("R6", {"R6-001": RC_GEN},
     {"R4-001": "resolved", "R5-001": "open", "R5-002": "open"}),
    ("R7", {"R7-001": RC_GEN},
     {"R5-001": "open", "R5-002": "open", "R6-001": "open"}),
    # R8：唯一 blocking 換了根因；前七例根因全數離開 open set。
    (
        "R8",
        {"R8-001": RC_SPLIT},
        {"R5-001": "downgraded", "R5-002": "downgraded",
         "R7-001": "downgraded", "R6-001": "resolved"},
    ),
]

# C@R3 的內容即需求方在 comment 5248665281 實際寫下的 deferred_findings，依修訂後
# §4「carry set ＝ 前一可計數 attempt 裁決當下的有效 open finding 全體」補齊
# R1-002／R1-006（該則留言只列了 R2-001／R2-002）。
DEFERRED_DECLARED: dict[str, list[str]] = {
    "R3": ["R1-002", "R1-006", "R2-001", "R2-002"],
}

# 假想 R9（**非事實**，R9 尚未查核）。用來證明存活判準是雙向的：根因停止後條件1
# 失效，重新產出 finding 後立即重新成立而不需重新累積三次。
HYPO_R9_STOPPED = ("R9", {"R9-001": "rc-r9-new"}, {"R8-001": "resolved"})
HYPO_R9_RETURNS = ("R9", {"R9-001": RC_GEN}, {"R8-001": "resolved"})


class Checkpoint:
    __slots__ = ("trigger", "count", "cond1_rcs", "cells", "overdue", "cond2", "forced")

    def __init__(self, trigger, count, cond1_rcs, cells, overdue, cond2):
        self.trigger, self.count = trigger, count
        self.cond1_rcs, self.cells, self.overdue, self.cond2 = cond1_rcs, cells, overdue, cond2
        self.forced = bool(cond1_rcs) or cond2


def replay(attempts, deferred_declared, *, defeasible_cond1: bool, allow_defer: bool):
    """依 review-escalation.md 第 173 行推導每個 checkpoint 的強制決定。

    defeasible_cond1=False → 條件1 現行字面（純累計，一旦成立即永久為真）
    defeasible_cond1=True  → 條件1 修訂後（累計 + 存活判準）
    allow_defer=False      → 條件2 現行（無 deferred_findings 出口）
    allow_defer=True       → 條件2 修訂後
    """
    open_after: dict[str, set[str]] = {}
    occurrences: dict[str, set[str]] = {}
    rc_of: dict[str, str] = {}
    live: set[str] = set()
    for label, new, disp in attempts:
        for fid, status in disp.items():
            if status in CLOSING:
                live.discard(fid)
        for fid, rc in new.items():
            live.add(fid)
            rc_of[fid] = rc
            occurrences.setdefault(rc, set()).add(label)
        open_after[label] = set(live)

    results: list[Checkpoint] = []
    prev_deferred: list[str] = []
    for i, (label, _new, disp) in enumerate(attempts):
        # §4：checkpoint 自第三個可計數 attempt 起建立，且建立於該 attempt 裁決落地之後。
        if i < 2:
            continue
        carry = open_after[attempts[i - 1][0]]        # 成員身分固定於前一個可計數 attempt
        declared = deferred_declared.get(label, []) if allow_defer else []

        cells: dict[str, str] = {}
        for fid in sorted(carry):
            status = disp.get(fid)
            if status in CLOSING:
                cells[fid] = status
            elif status == "open":
                cells[fid] = "仍開啟"
            elif fid in declared:
                # 「不得連續 defer」：同一 finding_id 出現於相鄰兩個 checkpoint 即失效。
                cells[fid] = "deferred(連續，無效)" if fid in prev_deferred else "deferred"
            else:
                cells[fid] = "未提及"

        overdue = [f for f in prev_deferred if disp.get(f) not in (*CLOSING, "open")]

        # --- 條件1 ---------------------------------------------------------
        seen = {a[0] for a in attempts[: i + 1]}
        alive_rcs = {rc_of[f] for f in open_after[label]}   # trigger attempt 裁決落地當下
        cond1_rcs = sorted(
            rc for rc, labels in occurrences.items()
            if len(labels & seen) >= 3 and (not defeasible_cond1 or rc in alive_rcs)
        )

        # --- 條件2 ---------------------------------------------------------
        triggering = [f for f, c in cells.items()
                      if c in ("仍開啟", "未提及", "deferred(連續，無效)")]
        cond2 = bool(triggering) or bool(overdue)

        results.append(Checkpoint(label, i + 1, cond1_rcs, cells, overdue, cond2))
        prev_deferred = [f for f, c in cells.items() if c == "deferred"]
    return {cp.trigger: cp for cp in results}


def render(title: str, checkpoints, only=None) -> None:
    print(f"\n===== {title} =====")
    for key, cp in checkpoints.items():
        if only and key not in only:
            continue
        c1 = f"TRUE  {cp.cond1_rcs}" if cp.cond1_rcs else "false"
        print(f"C@{cp.trigger}  (unique_attempt_count={cp.count})")
        print(f"    條件1 累計×3(+存活) : {c1}")
        print(f"    carry 六格分類      : {cp.cells or '{}'}")
        print(f"    逾期未清償          : {cp.overdue or '—'}")
        print(f"    條件2 carry         : {'TRUE' if cp.cond2 else 'false'}")
        print(f"    => 強制為: {'escalate' if cp.forced else '不強制（continue/replan 皆合法）'}")


def main() -> int:
    literal = replay(ATTEMPTS, DEFERRED_DECLARED, defeasible_cond1=False, allow_defer=False)
    revised = replay(ATTEMPTS, DEFERRED_DECLARED, defeasible_cond1=True, allow_defer=True)
    # 只改條件1／只改條件2 的兩個中間版本，用來機械證明兩條件互不干擾。
    only_c1 = replay(ATTEMPTS, DEFERRED_DECLARED, defeasible_cond1=True, allow_defer=False)
    only_c2 = replay(ATTEMPTS, DEFERRED_DECLARED, defeasible_cond1=False, allow_defer=True)

    render("現行條文（條件1 純累計；條件2 無 deferred 出口）", literal)
    render("修訂後條文（條件1 加存活判準；條件2 加 deferred 出口）", revised)

    # --- 反事實：R4 沿用窄規格，完全不處置被 defer 的那批 ----------------------
    cf_attempts = [(l, n, ({} if l == "R4" else d)) for l, n, d in ATTEMPTS]
    cf_silent = replay(cf_attempts, DEFERRED_DECLARED, defeasible_cond1=True, allow_defer=True)
    cf_decl = dict(DEFERRED_DECLARED, R4=list(DEFERRED_DECLARED["R3"]))
    cf_redefer = replay(cf_attempts, cf_decl, defeasible_cond1=True, allow_defer=True)
    render("反事實 (a)：C@R4 對 deferred 集合保持沉默", cf_silent, only={"R3", "R4"})
    render("反事實 (b)：C@R4 對同一批再 defer 一次", cf_redefer, only={"R3", "R4"})

    # --- 假想 R9（非事實）：存活判準是雙向的 ----------------------------------
    hypo_stop = replay(ATTEMPTS + [HYPO_R9_STOPPED], DEFERRED_DECLARED,
                       defeasible_cond1=True, allow_defer=True)
    hypo_back = replay(ATTEMPTS + [HYPO_R9_RETURNS], DEFERRED_DECLARED,
                       defeasible_cond1=True, allow_defer=True)
    hypo_back_literal = replay(ATTEMPTS + [HYPO_R9_RETURNS], DEFERRED_DECLARED,
                               defeasible_cond1=False, allow_defer=True)
    render("假想 R9-A【非事實】：七例根因未再出現", hypo_stop, only={"R9"})
    render("假想 R9-B【非事實】：七例根因重新產出 blocking", hypo_back, only={"R9"})

    checks: list[tuple[str, bool]] = [
        # --- 條件2（原射程）---------------------------------------------------
        ("現行條文下 C@R3 因前輪 finding 未被表態而強制 escalate",
         literal["R3"].forced and literal["R3"].cond2 and not literal["R3"].cond1_rcs),
        ("修訂後 C@R3 明示 deferred 時不再強制 escalate",
         not revised["R3"].forced),
        ("修訂後 C@R3 的四項 carry 全部落在 deferred 格",
         set(revised["R3"].cells.values()) == {"deferred"}),
        ("C@R4 清償完成：deferred 集合全數 resolved，無逾期",
         not revised["R4"].forced and not revised["R4"].overdue),
        ("反事實 (a)：C@R4 保持沉默仍強制 escalate，且四項列為逾期",
         cf_silent["R4"].forced and len(cf_silent["R4"].overdue) == 4),
        ("反事實 (b)：C@R4 再度 defer 判為無效，仍強制 escalate",
         cf_redefer["R4"].forced
         and any(c == "deferred(連續，無效)" for c in cf_redefer["R4"].cells.values())),
        # --- 條件1（新增射程）------------------------------------------------
        ("R5–R7：修訂後條件1 仍成立（根因當時仍存活）",
         all(RC_GEN in revised[k].cond1_rcs for k in ("R5", "R6", "R7"))),
        ("R8：現行字面下條件1 仍被閂住為 TRUE",
         RC_GEN in literal["R8"].cond1_rcs),
        ("R8：修訂後條件1 不再成立（七例根因已停止產出有效 open finding）",
         RC_GEN not in revised["R8"].cond1_rcs and not revised["R8"].cond1_rcs),
        ("R8：修訂後兩個條件皆不成立，checkpoint 不再被強制 escalate",
         not revised["R8"].forced and literal["R8"].forced),
        ("R8 的 transferred 三項依 §5 落在「已非有效 open finding」格，不觸發條件2",
         all(revised["R8"].cells[f] == "downgraded" for f in ("R5-001", "R5-002", "R7-001"))),
        ("假想 R9-A【非事實】：根因未再出現，條件1 持續不成立",
         RC_GEN not in hypo_stop["R9"].cond1_rcs),
        ("假想 R9-B【非事實】：根因重新出現即立刻重新成立，不需重新累積三次",
         RC_GEN in hypo_back["R9"].cond1_rcs
         and RC_GEN in hypo_back_literal["R9"].cond1_rcs),
        # --- 正交性：兩條件互不干擾（取代舊的「修訂前後完全相同」斷言）----------
        ("正交性 1：deferred_findings 不改變任何 checkpoint 的條件1 判定",
         all(only_c1[k].cond1_rcs == revised[k].cond1_rcs for k in revised)
         and all(literal[k].cond1_rcs == only_c2[k].cond1_rcs for k in revised)),
        ("正交性 2：條件1 的存活判準不改變任何 checkpoint 的條件2 判定",
         all(literal[k].cond2 == only_c1[k].cond2 for k in revised)
         and all(only_c2[k].cond2 == revised[k].cond2 for k in revised)),
        ("兩條件仍各自獨立充分：C@R5–R7 條件1 單獨即足以強制 escalate",
         all(replay(ATTEMPTS, {}, defeasible_cond1=True, allow_defer=False)[k].forced
             for k in ("R5", "R6", "R7"))),
    ]

    print("\n===== 斷言 =====")
    failed = sum(not ok for _, ok in checks)
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"\n{len(checks) - failed}/{len(checks)} 通過")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
