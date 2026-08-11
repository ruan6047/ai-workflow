#!/usr/bin/env python3
"""驗證 review-escalation.md §4／第 173 行的 checkpoint 判定。

三個部分：

  A. 六格分類的**全函數證明**：以六個獨立述詞列舉整個輸入空間，證明每個輸入
     恰好落在一格（不多不少），且 replay 用的分類器與述詞一致。
  B. 每一格至少一個**走過分類器**的具名案例，事實案例與構造案例分別標示。
  C. ai-workflow#16 的 R1→R8 回放（外加兩個標示為非事實的假想 R9），比較修訂前後。

執行（repo 根目錄，無第三方相依、不連網）：

    python3 scripts/replay_escalation_rules.py
    uv run --no-project python scripts/replay_escalation_rules.py

結束碼 0 表示全部斷言通過。

--------------------------------------------------------------------------
資料來源與轉錄聲明
--------------------------------------------------------------------------
ATTEMPTS 是**人工轉錄**自 ruan6047/ai-workflow#16 的 checkpoint 留言，非程式抓取：

    gh api repos/ruan6047/ai-workflow/issues/comments/<id> -q .body

    5248541311  03:08:40Z  第三個可計數 attempt 前（R1／R2 的 finding 與根因表）
    5248549305  03:10:09Z  需求方裁定：continue，並把 R3 改為窄規格
    5248657740  03:30:33Z  第四個可計數 attempt 前（R3 明文未逐條重驗 R1／R2）
    5248665281  03:31:54Z  需求方裁定（R4）：deferred_findings 的原型出於此則
    5248812931  03:58:11Z  第五個可計數 attempt 前（R4 判 9/10 resolved；剩 R4-001）
    5248823019  03:59:29Z  需求方裁定（R5）
    5248904826  04:13:30Z  第六個可計數 attempt 前（條件1 首次成立：R3／R4／R5）
    5249003956  04:31:18Z  第七個可計數 attempt 前（趨勢表；R5 的「再開 1（R4-001）」）
    5249157515  04:58:13Z  第八個可計數 attempt 前（R7；escalate → replan）
    5249245451  05:13:21Z  第九個可計數 attempt 前（R8 的事實部分）
    5249247912  05:13:47Z  ⚠️ 撤回：上則的 escalation_resolution／decided_by 係執行者擅填
    5249260224  05:15:56Z  第九個可計數 attempt 前：需求方**實際**裁定（取代被撤回的欄位）

⚠️ **撤回鏈**：`5249245451` 的裁定欄已由 `5249247912` 撤回——需求方當時並未裁定。
本腳本只採用該則的**事實部分**（R8 的 finding 組成與趨勢表，可由 timeline 獨立
查證），裁定一律採 `5249260224` 的取代版本。

⚠️ **R4-001 是 legacy id，不是被閉合的 finding**（本腳本前一版在此處出錯，記為
「R6 判 resolved」，係虛構）。原文事實：
  - `5248812931`：R4 剩餘僅 R4-001，「本輪已修，待 R5 複驗」；
  - `5249003956` 趨勢表：「R5 | 2 | 新 1 | **再開 1（R4-001）**」。
即 **R5-001 是 R4-001 換號重開**，不是 R4-001 被獨立閉合。依修訂後 §4「六格的
前提是穩定 finding_id」，換號重開不構成對舊 id 的任何處置，且本契約刻意不定義
承接關係。#16 的這段 timeline 早於穩定 id 的執行，故本腳本將 R4-001 標為
**legacy 正規化**（與 R5-001 併為同一 finding），並另跑一個「不做正規化」的變體
證明契約在該情形下 fail-closed——兩者都不把接續當成 closed。

其餘轉錄判斷：
  1. 各輪「再開」一律編碼為該輪明列 `open`（＝「仍開啟」格），fail-closed 方向。
  2. R7 的三項「再開」轉錄為 R5-001／R5-002／R6-001（留言只給計數 3）。
  3. R8 對 R5-001／R5-002／R7-001 的處置為 `transferred`（→ #24／#23／#25）並降為
     `info`／`blocking=false`。`transferred` 不是 §2 的三個 status 值之一，本腳本
     **不**為它新增狀態，而是以結構化的 `blocking=False` 走分類器（§5 末段）。
"""

from __future__ import annotations

import itertools
import sys

RC_MARKER = "marker-scope-narrows-away-safety-signal"
RC_PR = "universal-pr-ci-conflicts-with-canonical-classification"
RC_GEN = "incomplete-custom-classification-overrides-canonical"
RC_SPLIT = "split-composite-transition-without-intermediate-state"

# §3 第 3～4 款：finding_class 須為 implementation／authoritative-artifact，
# 且 attribution 須為 executor。
ELIGIBLE_CLASSES = ("implementation", "authoritative-artifact")

CELLS = ("resolved", "withdrawn", "已非有效 open finding", "仍開啟", "deferred", "未提及")


# =========================================================================
# A. 六格分類：一個分類器 + 六個獨立述詞（全函數證明）
# =========================================================================

def eligible(f: dict) -> bool:
    """§3 第 3～4 款。"""
    return f["finding_class"] in ELIGIBLE_CLASSES and f["attribution"] == "executor"


def valid_open(f: dict) -> bool:
    """§4「有效 open finding」述詞。"""
    return f["status"] == "open" and f["accepted"] and f["blocking"] and eligible(f)


def classify(f: dict, *, mentioned_open: bool, defer_ok: bool) -> str:
    """replay 使用的分類器。f 為該 finding 在 checkpoint 評估時點的狀態。"""
    if f["status"] == "resolved":
        return "resolved"
    if f["status"] == "withdrawn":
        return "withdrawn"
    if not valid_open(f):
        return "已非有效 open finding"
    if mentioned_open:
        return "仍開啟"
    if defer_ok:
        return "deferred"
    return "未提及"


# 六個獨立述詞，逐字對應 §4 的表格與其優先序句。用於證明「恰好落在一格」。
PREDICATES = {
    "resolved": lambda f, m, d: f["status"] == "resolved",
    "withdrawn": lambda f, m, d: f["status"] == "withdrawn",
    "已非有效 open finding": lambda f, m, d: f["status"] == "open" and not valid_open(f),
    "仍開啟": lambda f, m, d: valid_open(f) and m,
    "deferred": lambda f, m, d: valid_open(f) and not m and d,
    "未提及": lambda f, m, d: valid_open(f) and not m and not d,
}

TRIGGERING = ("仍開啟", "未提及")


def prove_partition() -> tuple[int, list[str]]:
    """列舉整個輸入空間，證明六格是全函數（每個輸入恰好落在一格）。"""
    problems: list[str] = []
    total = 0
    axes = itertools.product(
        ("open", "resolved", "withdrawn"),          # status
        (True, False),                              # accepted
        (True, False),                              # blocking
        ("implementation", "governance"),           # finding_class（後者不符 §3 第 3 款）
        ("executor", "planner"),                    # attribution（後者不符 §3 第 4 款）
        (True, False),                              # 本輪明列仍 open
        (True, False),                              # checkpoint 宣告 defer
        (True, False),                              # 上一個 checkpoint 已 defer 過（連續）
        (True, False),                              # defer 各必要欄位齊備且身分合法
    )
    for st, acc, blk, cls, attr, mentioned, declared, prev_def, wellformed in axes:
        total += 1
        f = {"status": st, "accepted": acc, "blocking": blk,
             "finding_class": cls, "attribution": attr}
        # §4：連續 defer 或必要條件不成立者，該筆 defer 無效。
        defer_ok = declared and wellformed and not prev_def
        hits = [name for name, p in PREDICATES.items() if p(f, mentioned, defer_ok)]
        if len(hits) != 1:
            problems.append(f"{f} mentioned={mentioned} defer_ok={defer_ok} → 命中 {hits}")
            continue
        got = classify(f, mentioned_open=mentioned, defer_ok=defer_ok)
        if got != hits[0]:
            problems.append(f"{f} → 分類器 {got} ≠ 述詞 {hits[0]}")
    return total, problems


# --- B. 每一格的具名案例（皆走 classify()）---------------------------------
# kind：事實＝取自 #16 timeline；構造＝#16 未發生，明確標示以免混充事實。
BASE = {"status": "open", "accepted": True, "blocking": True,
        "finding_class": "implementation", "attribution": "executor"}


def _f(**kw) -> dict:
    return {**BASE, **kw}


CELL_CASES: list[tuple[str, str, str, dict, bool, bool]] = [
    # (期望格, kind, 說明, finding 狀態, mentioned_open, defer_ok)
    ("resolved", "事實", "R1-001 於 R2 明列 resolved（5248541311）",
     _f(status="resolved"), False, False),
    ("withdrawn", "構造", "review-correction 撤回採認並標 withdrawn（#16 未發生）",
     _f(status="withdrawn"), False, False),
    ("已非有效 open finding", "事實",
     "R8 對 R5-001 判 transferred，降為 info／blocking=false（5249245451）",
     _f(blocking=False), False, False),
    ("已非有效 open finding", "構造",
     "review-correction 將 accepted 改為 false，status 仍 open（非 transferred 降級）",
     _f(accepted=False), False, False),
    ("已非有效 open finding", "構造",
     "重診斷 attribution executor→planner，不再符合 §3 第 4 款（非 transferred 降級）",
     _f(attribution="planner"), False, False),
    ("已非有效 open finding", "構造",
     "重分類 finding_class→governance，不再符合 §3 第 3 款（非 transferred 降級）",
     _f(finding_class="governance"), False, False),
    ("仍開啟", "事實", "R5 明列 R4-001 仍 open（5248812931）", _f(), True, False),
    ("deferred", "事實", "C@R3 對 R2-001 的 deferred 宣告（5248665281）", _f(), False, True),
    ("未提及", "事實", "C@R3 現行條文下 R2-001 無任何表態（5248657740）", _f(), False, False),
    ("未提及", "構造", "defer 已宣告但必要條件不成立（身分不符／缺欄／連續 defer）",
     _f(), False, False),
]


# =========================================================================
# C. #16 回放
# =========================================================================
# 每個 attempt：(label, 新提出 {id: (root_cause, overrides)}, 對既有 finding 的更新)
# 更新值為 partial dict；{"status": "open"} 表示本輪明列仍開啟。
ATTEMPTS: list[tuple[str, dict, dict]] = [
    ("R1", {"R1-001": ("rc-r1-001", {}), "R1-002": (RC_MARKER, {}),
            "R1-003": ("rc-r1-003", {}), "R1-004": ("rc-r1-004", {}),
            "R1-005": ("rc-r1-005", {}), "R1-006": (RC_PR, {})}, {}),
    ("R2", {"R2-001": (RC_MARKER, {}), "R2-002": (RC_PR, {})},
     {"R1-001": {"status": "resolved"}, "R1-003": {"status": "resolved"},
      "R1-004": {"status": "resolved"}, "R1-005": {"status": "resolved"}}),
    # R3：依需求方裁定改為窄規格，明文不逐條重驗 R1／R2 → 對前輪 finding 零處置。
    ("R3", {"R3-001": (RC_GEN, {})}, {}),
    ("R4", {"R4-001": (RC_GEN, {})},
     {"R1-002": {"status": "resolved"}, "R1-006": {"status": "resolved"},
      "R2-001": {"status": "resolved"}, "R2-002": {"status": "resolved"},
      "R3-001": {"status": "resolved"}}),
    # R5：2 blocking ＝ 新 1（R5-002）＋ 再開 1（R4-001，換號為 R5-001）。
    ("R5", {"R5-001": (RC_GEN, {}), "R5-002": (RC_GEN, {})},
     {"R4-001": {"status": "open"}}),
    ("R6", {"R6-001": (RC_GEN, {})},
     {"R5-001": {"status": "open"}, "R5-002": {"status": "open"}}),
    ("R7", {"R7-001": (RC_GEN, {})},
     {"R5-001": {"status": "open"}, "R5-002": {"status": "open"},
      "R6-001": {"status": "open"}}),
    # R8：唯一 blocking 換了根因；前七例根因全數離開 open set。
    ("R8", {"R8-001": (RC_SPLIT, {})},
     {"R5-001": {"blocking": False}, "R5-002": {"blocking": False},
      "R7-001": {"blocking": False}, "R6-001": {"status": "resolved"}}),
]

# legacy 正規化：舊 id → 接續它的新 id。**不是閉合**，只是承認該段 timeline 不滿足
# 穩定 finding_id 契約，故兩個 id 指涉同一個 finding。來源見檔頭。
LEGACY_SUPERSEDED = {"R4-001": ("R5-001", "R5")}

DEFERRED_DECLARED = {"R3": ["R1-002", "R1-006", "R2-001", "R2-002"]}

HYPO_R9_STOPPED = ("R9", {"R9-001": ("rc-r9-new", {})}, {"R8-001": {"status": "resolved"}})
HYPO_R9_RETURNS = ("R9", {"R9-001": (RC_GEN, {})}, {"R8-001": {"status": "resolved"}})


class Checkpoint:
    __slots__ = ("trigger", "count", "cond1_rcs", "cells", "overdue", "cond2", "forced")

    def __init__(self, trigger, count, cond1_rcs, cells, overdue, cond2):
        self.trigger, self.count = trigger, count
        self.cond1_rcs, self.cells, self.overdue, self.cond2 = cond1_rcs, cells, overdue, cond2
        self.forced = bool(cond1_rcs) or cond2


def replay(attempts, deferred_declared, *, defeasible_cond1, allow_defer, normalize_legacy=True):
    order = [a[0] for a in attempts]

    def superseded_by(lab: str) -> list[str]:
        """在 lab 這一輪的裁決落地後，哪些舊 id 已被接續（故不再是獨立 finding）。

        承接發生在 `at` 那一輪，該輪的裁決本身仍是對舊 id 的真實表態（#16 的 R5
        明列 R4-001 仍 open），故正規化自 `at` 之**後**才生效，不回頭覆蓋該表態。
        """
        if not normalize_legacy:
            return []
        return [old for old, (_new_id, at) in LEGACY_SUPERSEDED.items()
                if at in order and order.index(lab) > order.index(at)]

    state: dict[str, dict] = {}
    rc_of: dict[str, str] = {}
    occurrences: dict[str, set[str]] = {}
    open_after: dict[str, set[str]] = {}
    mentioned_at: dict[str, set[str]] = {}

    for label, new, updates in attempts:
        for fid, upd in updates.items():
            if fid in state:
                state[fid].update(upd)
                if upd.get("status") == "open":
                    mentioned_at.setdefault(label, set()).add(fid)
        for fid, (rc, over) in new.items():
            state[fid] = _f(**over)
            rc_of[fid] = rc
            occurrences.setdefault(rc, set()).add(label)
        for old in superseded_by(label):
            if old in state:
                state[old] = {**state[old], "status": "superseded-legacy"}
        open_after[label] = {f for f, s in state.items() if valid_open(s)}

    results = []
    prev_deferred: list[str] = []
    for i, (label, _new, updates) in enumerate(attempts):
        if i < 2:
            continue
        carry = open_after[attempts[i - 1][0]]
        declared = deferred_declared.get(label, []) if allow_defer else []

        # 重放到 trigger attempt 裁決落地當下的狀態。
        snap: dict[str, dict] = {}
        for lab, new, upd in attempts[: i + 1]:
            for fid, u in upd.items():
                if fid in snap:
                    snap[fid].update(u)
            for fid, (rc, over) in new.items():
                snap[fid] = _f(**over)
            for old in superseded_by(lab):
                if old in snap:
                    snap[old] = {**snap[old], "status": "superseded-legacy"}

        cells: dict[str, str] = {}
        for fid in sorted(carry):
            f = snap[fid]
            if f["status"] == "superseded-legacy":
                cells[fid] = "legacy（不套用六格）"
                continue
            defer_ok = fid in declared and fid not in prev_deferred
            cells[fid] = classify(
                f, mentioned_open=fid in mentioned_at.get(label, set()), defer_ok=defer_ok)

        overdue = [f for f in prev_deferred
                   if cells.get(f) in ("deferred", "未提及", None)]

        seen = {a[0] for a in attempts[: i + 1]}
        alive = {rc_of[f] for f, s in snap.items() if valid_open(s)}
        cond1_rcs = sorted(rc for rc, labs in occurrences.items()
                           if len(labs & seen) >= 3 and (not defeasible_cond1 or rc in alive))
        cond2 = any(c in TRIGGERING for c in cells.values()) or bool(overdue)

        results.append(Checkpoint(label, i + 1, cond1_rcs, cells, overdue, cond2))
        prev_deferred = [f for f, c in cells.items() if c == "deferred"]
    return {cp.trigger: cp for cp in results}


def render(title, cps, only=None):
    print(f"\n===== {title} =====")
    for key, cp in cps.items():
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
    checks: list[tuple[str, bool]] = []

    # --- A. 全函數證明 -----------------------------------------------------
    total, problems = prove_partition()
    print("===== A. 六格全函數證明（列舉輸入空間）=====")
    print(f"  列舉組合數：{total}")
    print(f"  每個輸入恰好命中一格且與分類器一致：{'是' if not problems else '否'}")
    for p in problems[:5]:
        print(f"    ✗ {p}")
    checks.append((f"六格為全函數：{total} 個列舉輸入各恰好落在一格，且分類器與述詞一致",
                   not problems))

    # --- B. 每格具名案例 ---------------------------------------------------
    print("\n===== B. 每一格的具名案例（皆走分類器）=====")
    covered: dict[str, list[str]] = {}
    case_ok = True
    for expect, kind, desc, f, mentioned, defer_ok in CELL_CASES:
        got = classify(f, mentioned_open=mentioned, defer_ok=defer_ok)
        ok = got == expect
        case_ok &= ok
        covered.setdefault(expect, []).append(kind)
        print(f"  [{'PASS' if ok else 'FAIL'}] {expect:<22} ({kind}) {desc}")
    missing = [c for c in CELLS if c not in covered]
    print(f"  未被任何案例走過的格：{missing or '無'}")
    checks.append(("每一格都有走過分類器的具名案例且結果正確", case_ok and not missing))
    checks.append(("「已非有效 open finding」格含非 transferred 的降級分支（accepted=false／"
                   "attribution／finding_class 各一）",
                   sum(1 for e, k, *_ in CELL_CASES
                       if e == "已非有效 open finding" and k == "構造") >= 3))
    checks.append(("withdrawn 格由 review-correction 撤回案例走過（構造，#16 未發生）",
                   any(e == "withdrawn" for e, *_ in CELL_CASES)))

    # --- C. #16 回放 -------------------------------------------------------
    literal = replay(ATTEMPTS, DEFERRED_DECLARED, defeasible_cond1=False, allow_defer=False)
    revised = replay(ATTEMPTS, DEFERRED_DECLARED, defeasible_cond1=True, allow_defer=True)
    only_c1 = replay(ATTEMPTS, DEFERRED_DECLARED, defeasible_cond1=True, allow_defer=False)
    only_c2 = replay(ATTEMPTS, DEFERRED_DECLARED, defeasible_cond1=False, allow_defer=True)
    render("C. 現行條文（條件1 純累計；條件2 無 deferred 出口）", literal)
    render("C. 修訂後條文（條件1 加存活判準；條件2 加 deferred 出口）", revised)

    cf = [(l, n, ({} if l == "R4" else d)) for l, n, d in ATTEMPTS]
    cf_silent = replay(cf, DEFERRED_DECLARED, defeasible_cond1=True, allow_defer=True)
    cf_redefer = replay(cf, dict(DEFERRED_DECLARED, R4=list(DEFERRED_DECLARED["R3"])),
                        defeasible_cond1=True, allow_defer=True)
    render("反事實 (a)：C@R4 對 deferred 集合保持沉默", cf_silent, only={"R4"})
    render("反事實 (b)：C@R4 對同一批再 defer 一次", cf_redefer, only={"R4"})

    hypo_stop = replay(ATTEMPTS + [HYPO_R9_STOPPED], DEFERRED_DECLARED,
                       defeasible_cond1=True, allow_defer=True)
    hypo_back = replay(ATTEMPTS + [HYPO_R9_RETURNS], DEFERRED_DECLARED,
                       defeasible_cond1=True, allow_defer=True)
    render("假想 R9-A【非事實】：七例根因未再出現", hypo_stop, only={"R9"})
    render("假想 R9-B【非事實】：七例根因重新產出 blocking", hypo_back, only={"R9"})

    # legacy 未正規化的變體：R4-001 被當成獨立 id，換號重開不算處置 → fail-closed。
    naive = replay(ATTEMPTS, DEFERRED_DECLARED, defeasible_cond1=True,
                   allow_defer=True, normalize_legacy=False)
    render("legacy 未正規化【構造】：R4-001 視為獨立 id（換號重開≠處置）", naive,
           only={"R6", "R8"})

    checks += [
        ("現行條文下 C@R3 因前輪 finding 未被表態而強制 escalate",
         literal["R3"].forced and literal["R3"].cond2 and not literal["R3"].cond1_rcs),
        ("修訂後 C@R3 明示 deferred 時不再強制 escalate", not revised["R3"].forced),
        ("修訂後 C@R3 的四項 carry 全部落在 deferred 格",
         set(revised["R3"].cells.values()) == {"deferred"}),
        ("C@R4 清償完成：deferred 集合全數 resolved，無逾期",
         not revised["R4"].forced and not revised["R4"].overdue),
        ("反事實 (a)：C@R4 保持沉默仍強制 escalate，且四項列為逾期",
         cf_silent["R4"].forced and len(cf_silent["R4"].overdue) == 4),
        ("反事實 (b)：C@R4 再度 defer 判為無效，仍強制 escalate",
         cf_redefer["R4"].forced
         and all(c == "未提及" for f, c in cf_redefer["R4"].cells.items()
                 if f in DEFERRED_DECLARED["R3"])),
        ("R5–R7：修訂後條件1 仍成立（根因當時仍存活）",
         all(RC_GEN in revised[k].cond1_rcs for k in ("R5", "R6", "R7"))),
        ("R8：現行字面下條件1 仍被閂住為 TRUE", RC_GEN in literal["R8"].cond1_rcs),
        ("R8：修訂後條件1 不再成立（七例根因已停止產出有效 open finding）",
         not revised["R8"].cond1_rcs),
        ("R8：修訂後兩個條件皆不成立，checkpoint 不再被強制 escalate",
         not revised["R8"].forced and literal["R8"].forced),
        ("R8 的 transferred 三項以 blocking=false 走分類器，落「已非有效 open finding」格",
         all(revised["R8"].cells[f] == "已非有效 open finding"
             for f in ("R5-001", "R5-002", "R7-001"))),
        ("R4-001 未被記為 resolved／withdrawn（接續不等同閉合）",
         all(cp.cells.get("R4-001") not in ("resolved", "withdrawn")
             for cp in list(revised.values()) + list(naive.values()))),
        ("legacy 未正規化【構造】：換號重開使舊 id 落「未提及」而 fail-closed",
         naive["R6"].cells.get("R4-001") == "未提及" and naive["R6"].cond2
         and naive["R8"].forced),
        ("假想 R9-A【非事實】：根因未再出現，條件1 持續不成立",
         RC_GEN not in hypo_stop["R9"].cond1_rcs),
        ("假想 R9-B【非事實】：根因重新出現即立刻重新成立，不需重新累積三次",
         RC_GEN in hypo_back["R9"].cond1_rcs),
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
