#!/usr/bin/env python3
"""回放 ai-workflow#16 的 R1→R7 事件流，比較 review-escalation.md 修訂前後的
`escalation-checkpoint` 強制升級判定。

執行（repo 根目錄，無第三方相依、不連網）：

    python3 scripts/replay_escalation_rules.py
    uv run --no-project python scripts/replay_escalation_rules.py

結束碼 0 表示全部斷言通過；非 0 表示條文與本腳本編碼的預期行為不一致。

--------------------------------------------------------------------------
資料來源與轉錄聲明
--------------------------------------------------------------------------
下方 ATTEMPTS／DEFERRED 是**人工轉錄**自 ruan6047/ai-workflow#16 的八則
`escalation-checkpoint` 留言中的逐輪 finding 表，非程式抓取。要核對來源請直接讀
這些 comment（`gh api repos/ruan6047/ai-workflow/issues/comments/<id> -q .body`）：

    5248541311  2026-08-11T03:08:40Z  第三個可計數 attempt 前（R1/R2 的 finding 與根因表）
    5248549305  2026-08-11T03:10:09Z  需求方裁定：continue，並改變 R3 的查核規格（窄規格）
    5248657740  2026-08-11T03:30:33Z  第四個可計數 attempt 前（R3 明文未逐條重驗 R1/R2）
    5248665281  2026-08-11T03:31:54Z  需求方裁定（R4）：本卡 deferred_findings 的原型即出於此則
    5248812931  2026-08-11T03:58:11Z  第五個可計數 attempt 前（R4 判 9/10 resolved；讀法歧義首次寫下）
    5248823019  2026-08-11T03:59:29Z  需求方裁定（R5）
    5248904826  2026-08-11T04:13:30Z  第六個可計數 attempt 前（第一條件成立：R3/R4/R5 同根因）
    5249003956  2026-08-11T04:31:18Z  第七個可計數 attempt 前（第一條件擴大到四個 attempt）
    5249157515  2026-08-11T04:58:13Z  第八個可計數 attempt 前（R7；escalate → replan）

轉錄時的兩點判斷，供查核者針對性攻擊：
  1. 各輪「再開」的 finding 一律編碼為該輪明列 `open`（＝條文 §4 的「仍開啟」格）。
     留言只說「再開」，未逐字寫 status；此編碼落在 fail-closed 方向。
  2. R7 的三項「再開」轉錄為 R5-001／R5-002／R6-001。留言只給計數（3）未逐項列名，
     此為依前後文的推定；改變這三個 id 不影響任何結論，因為 C@R7 的兩個條件都已
     由其他證據獨立成立。
"""

from __future__ import annotations

import sys

# --- 根因識別碼（逐字取自 #16 留言）------------------------------------------
RC_MARKER = "marker-scope-narrows-away-safety-signal"
RC_PR = "universal-pr-ci-conflicts-with-canonical-classification"
RC_GEN = "incomplete-custom-classification-overrides-canonical"

# --- 逐輪可計數 attempt -------------------------------------------------------
# (label, 本輪新提出的 accepted blocking finding {finding_id: root_cause_id},
#         本輪對先前 finding 的明示處置 {finding_id: resolved|withdrawn|open})
ATTEMPTS: list[tuple[str, dict[str, str], dict[str, str]]] = [
    # R1：六項相異根因，其中 R1-002／R1-006 是後續兩個重複根因的首次出現。
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
        {
            "R1-001": "resolved",
            "R1-003": "resolved",
            "R1-004": "resolved",
            "R1-005": "resolved",
        },
    ),
    # R3：依需求方裁定改為窄規格，**明文不逐條重驗 R1／R2** → 對前輪 finding 零處置。
    # 這一格就是本卡的痛點來源。
    ("R3", {"R3-001": RC_GEN}, {}),
    # R4：規格改回全面複驗，十項中九項一次判 resolved。
    (
        "R4",
        {"R4-001": RC_GEN},
        {
            "R1-002": "resolved",
            "R1-006": "resolved",
            "R2-001": "resolved",
            "R2-002": "resolved",
            "R3-001": "resolved",
        },
    ),
    ("R5", {"R5-001": RC_GEN, "R5-002": RC_GEN}, {"R4-001": "open"}),
    ("R6", {"R6-001": RC_GEN}, {"R5-001": "open", "R5-002": "open"}),
    (
        "R7",
        {"R7-001": RC_GEN},
        {"R5-001": "open", "R5-002": "open", "R6-001": "open"},
    ),
]

# checkpoint 宣告的 deferred 集合，key = 該 checkpoint 的 trigger attempt。
# C@R3 的內容即需求方在 comment 5248665281 實際寫下的 deferred_findings，
# 依修訂後 §4「carry set ＝ 前一可計數 attempt 裁決當下的整個 open set」補齊
# R1-002／R1-006（該則留言只列了 R2-001／R2-002）。
DEFERRED_DECLARED: dict[str, list[str]] = {
    "R3": ["R1-002", "R1-006", "R2-001", "R2-002"],
}

CLOSED = ("resolved", "withdrawn")


class Checkpoint:
    __slots__ = ("trigger", "count", "cond1_rcs", "cells", "overdue", "cond2", "forced")

    def __init__(self, trigger, count, cond1_rcs, cells, overdue, cond2):
        self.trigger = trigger
        self.count = count
        self.cond1_rcs = cond1_rcs
        self.cells = cells
        self.overdue = overdue
        self.cond2 = cond2
        self.forced = bool(cond1_rcs) or cond2


def replay(attempts, deferred_declared, allow_defer: bool) -> list[Checkpoint]:
    """依 review-escalation.md 第 173 行推導每個 checkpoint 的強制決定。

    allow_defer=False  → 現行條文（沒有 deferred_findings 這個出口）
    allow_defer=True   → 修訂後條文
    """
    # 先掃一遍，取得每個 attempt 裁決落地當下的 open set 與根因 occurrence。
    open_after: dict[str, set[str]] = {}
    occurrences: dict[str, set[str]] = {}
    live: set[str] = set()
    for label, new, disp in attempts:
        for fid, status in disp.items():
            if status in CLOSED:
                live.discard(fid)
        for fid, rc in new.items():
            live.add(fid)
            occurrences.setdefault(rc, set()).add(label)
        open_after[label] = set(live)

    results: list[Checkpoint] = []
    prev_deferred: list[str] = []
    for i, (label, _new, disp) in enumerate(attempts):
        # §4：checkpoint 自第三個可計數 attempt 起建立，且建立於該 attempt 裁決落地之後。
        if i < 2:
            continue
        prev_label = attempts[i - 1][0]
        carry = open_after[prev_label]  # 成員身分固定於前一個可計數 attempt
        declared = deferred_declared.get(label, []) if allow_defer else []

        # §4 的五格分類：每個 carry 成員必落在且僅落在一格。
        cells: dict[str, str] = {}
        for fid in sorted(carry):
            status = disp.get(fid)
            if status in CLOSED:
                cells[fid] = status
            elif status == "open":
                cells[fid] = "仍開啟"
            elif fid in declared:
                # 「不得連續 defer」：同一 finding_id 出現於相鄰兩個 checkpoint 即失效。
                cells[fid] = "deferred(連續，無效)" if fid in prev_deferred else "deferred"
            else:
                cells[fid] = "未提及"

        # 清償義務：前一 checkpoint 的 deferred 成員，本輪須給出 resolved/withdrawn/仍開啟。
        overdue = [f for f in prev_deferred if disp.get(f) not in (*CLOSED, "open")]

        seen_so_far = {a[0] for a in attempts[: i + 1]}
        cond1_rcs = sorted(
            rc for rc, labels in occurrences.items() if len(labels & seen_so_far) >= 3
        )
        triggering = sorted(
            f for f, c in cells.items() if c in ("仍開啟", "未提及", "deferred(連續，無效)")
        )
        cond2 = bool(triggering) or bool(overdue)

        results.append(Checkpoint(label, i + 1, cond1_rcs, cells, overdue, cond2))
        prev_deferred = [f for f, c in cells.items() if c == "deferred"]
    return results


def render(title: str, checkpoints: list[Checkpoint]) -> None:
    print(f"\n===== {title} =====")
    for cp in checkpoints:
        c1 = f"TRUE  {cp.cond1_rcs}" if cp.cond1_rcs else "false"
        print(f"C@{cp.trigger}  (unique_attempt_count={cp.count})")
        print(f"    條件1 同根因×3 : {c1}")
        print(f"    carry 五格分類 : {cp.cells or '{}'}")
        print(f"    逾期未清償     : {cp.overdue or '—'}")
        print(f"    條件2 carry    : {'TRUE' if cp.cond2 else 'false'}")
        print(f"    => checkpoint_decision 強制為: "
              f"{'escalate' if cp.forced else '不強制（continue/replan 皆合法）'}")


def main() -> int:
    current = {cp.trigger: cp for cp in replay(ATTEMPTS, DEFERRED_DECLARED, allow_defer=False)}
    revised = {cp.trigger: cp for cp in replay(ATTEMPTS, DEFERRED_DECLARED, allow_defer=True)}

    render("現行條文（無 deferred_findings 出口）", list(current.values()))
    render("修訂後條文（C@R3 由需求方明示 deferred）", list(revised.values()))

    # --- 反事實：R4 沿用窄規格，完全不處置被 defer 的那批 ----------------------
    cf_attempts = [
        (label, new, ({} if label == "R4" else disp)) for label, new, disp in ATTEMPTS
    ]
    cf_silent = {
        cp.trigger: cp for cp in replay(cf_attempts, DEFERRED_DECLARED, allow_defer=True)
    }
    cf_redefer_decl = dict(DEFERRED_DECLARED)
    cf_redefer_decl["R4"] = list(DEFERRED_DECLARED["R3"])
    cf_redefer = {
        cp.trigger: cp for cp in replay(cf_attempts, cf_redefer_decl, allow_defer=True)
    }
    render("反事實 (a)：C@R4 對 deferred 集合保持沉默", [cf_silent["R3"], cf_silent["R4"]])
    render("反事實 (b)：C@R4 對同一批再 defer 一次", [cf_redefer["R3"], cf_redefer["R4"]])

    # --- 斷言：條文必須產生下列行為 -------------------------------------------
    checks: list[tuple[str, bool]] = [
        ("現行條文下 C@R3 因前輪 finding 未被表態而強制 escalate",
         current["R3"].forced and current["R3"].cond2 and not current["R3"].cond1_rcs),
        ("修訂後 C@R3 明示 deferred 時不再強制 escalate",
         not revised["R3"].forced),
        ("修訂後 C@R3 的四項 carry 全部落在 deferred 格",
         set(revised["R3"].cells.values()) == {"deferred"}),
        ("C@R4 清償完成：deferred 集合全數 resolved，無逾期",
         not revised["R4"].forced and not revised["R4"].overdue),
        ("C@R5 第一條件獨立成立（同根因跨三個唯一可計數 attempt）",
         RC_GEN in revised["R5"].cond1_rcs and revised["R5"].forced),
        ("C@R6 第一條件持續成立且不受 defer 影響",
         RC_GEN in revised["R6"].cond1_rcs and revised["R6"].forced),
        ("C@R7 第一條件持續成立（對應 #16 實際裁定 escalate → replan）",
         RC_GEN in revised["R7"].cond1_rcs and revised["R7"].forced),
        ("第一條件的判定在修訂前後完全相同（defer 與第一條件正交）",
         all(current[k].cond1_rcs == revised[k].cond1_rcs for k in current)),
        ("反事實 (a)：C@R4 保持沉默仍強制 escalate，且四項列為逾期",
         cf_silent["R4"].forced and len(cf_silent["R4"].overdue) == 4),
        ("反事實 (b)：C@R4 再度 defer 判為無效，仍強制 escalate",
         cf_redefer["R4"].forced
         and any(c == "deferred(連續，無效)" for c in cf_redefer["R4"].cells.values())),
    ]

    print("\n===== 斷言 =====")
    failed = 0
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        failed += not ok
    print(f"\n{len(checks) - failed}/{len(checks)} 通過")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
