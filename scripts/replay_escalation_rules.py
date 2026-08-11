#!/usr/bin/env python3
"""驗證 review-escalation.md §4／§5 末段的 checkpoint 判定。

執行（repo 根目錄，無第三方相依、不連網）：

    python3 scripts/replay_escalation_rules.py
    uv run --no-project python scripts/replay_escalation_rules.py

結束碼 0 表示全部斷言通過。

四個部分：

  A. **分類器投影空間**的分割證明：列舉 `classify()` 全部宣告值域（含逐項展開的
     defer 必要條件），證明每個輸入恰好落一格。**這不是全函數證明**——涵蓋界線
     見下方「A 的宣稱界線」，程式執行時也會原樣印出。
  B. 事件層 replay 引擎：以事件流（attempt／review-correction／epoch-change／
     escalation-checkpoint）驅動，六格全部由引擎走出，不是手搓的 dict。
  C. ai-workflow#16 的 R1→R8 **忠實**回放（legacy）。
  D. 構造情境：deferred 出口、清償、連續 defer、carry 成員資格、epoch 邊界、
     條件1 可失效性。全部明確標示為構造。

--------------------------------------------------------------------------
A 的宣稱界線（R2-003）
--------------------------------------------------------------------------
A 段列舉的是 **`classify()` 這個函式的輸入空間**：finding 的五個結構化欄位、
「本輪是否明列仍 open」、以及 defer 是否成立所需的七個布林條件。它證明的是
**分類器對其宣告值域是一個分割**，僅此而已。

它**不**涵蓋（這些改由 B～D 的事件層測試或明確聲明未涵蓋處理）：

  1. finding 是否屬於本 checkpoint 的 carry set（→ D「carry 成員資格」）
  2. epoch 邊界對計數／carry／prev_deferred 的重置（→ D「epoch 邊界」）
  3. review-correction 相對 checkpoint 的**位置**（→ B 六格情境以事件順序驅動）
  4. 同一 finding 的**衝突事件**與 §2 的待裁決 gate ——**未涵蓋**。本引擎不模擬
     衝突偵測，也不模擬同 SHA 多 reviewer 合併後的 fail loud。任何「本腳本證明
     §2 衝突處理正確」的宣稱都是假的。
  5. 留痕解析停機（§1／§5 `review-marker-clearance`）——**未涵蓋**。

--------------------------------------------------------------------------
C 的資料來源與轉錄聲明
--------------------------------------------------------------------------
`EVENTS_16` 轉錄自 ruan6047/ai-workflow#16 的 checkpoint 留言，可原樣取回核對：

    gh api repos/ruan6047/ai-workflow/issues/comments/<id> -q .body

    5248541311  第三個可計數 attempt 前：R1 六項、R2 兩項；R1-001/003/004/005
                由 R2 明列閉環；**R1-002／R1-006 未被標 resolved／withdrawn，
                而是以更窄的殘留形式（R2-001／R2-002）再次出現**。
    5248549305  需求方裁定（R3 規格收窄；未宣告任何 deferred）。
    5248657740  第四個可計數 attempt 前：R3 明文未逐條重驗 R1／R2；R3-001 新提。
    5248665281  需求方裁定（R4）。**deferred_findings 只列兩筆**：
                  - WF-ORCHESTRATION-RECONCILE1-R2-001
                  - WF-ORCHESTRATION-RECONCILE1-R2-002
                本腳本 `DEFER_DECLARED_AT_C_R3` 逐字對應這兩筆，不多不少。
    5248812931  第五個可計數 attempt 前：R4 判 9/10 resolved，剩 R4-001。
    5248823019  需求方裁定（R5）。
    5248904826  第六個可計數 attempt 前：R5 ＝ 新 1 ＋ **再開 1（R4-001）**，
                以新 id R5-001 表示；另有 R5-002。
    5249003956  第七個可計數 attempt 前：R6 ＝ 新 1（R6-001）＋ 再開 2
                （R5-001／R5-002）。
    5249157515  第八個可計數 attempt 前：R7 ＝ 新 1（R7-001）＋ 再開 3。
    5249245451  第九個可計數 attempt 前：R8 的**事實部分**——R8-001 為新根因；
                R5-001／R5-002／R7-001 判 transferred 並降為 info／blocking=false；
                R6-001 判 resolved。
    5249247912  ⚠️ 撤回上則的 escalation_resolution／decided_by（執行者擅填）。
    5249260224  需求方**實際**裁定（取代被撤回的欄位）。

轉錄判斷（逐項可查）：
  1. 「再開」一律編碼為該輪明列 `open`（＝「仍開啟」格），fail-closed 方向。
  2. R7 的三項再開轉錄為 R5-001／R5-002／R6-001（留言只給計數 3）。
  3. R8 的 `transferred` 不是 §2 的三個 status 值，**不**為它新增狀態；以結構化
     `blocking=False` 走分類器（§5 末段）。

⚠️ **#16 是 legacy 事件流，不符合新契約的穩定 `finding_id` 要求。** 它至少有三處
換號重開：R1-002→R2-001、R1-006→R2-002、R4-001→R5-001。依修訂後 §4「六格的前提
是穩定 finding_id」，換號重開**不構成對舊 id 的任何處置**，故忠實回放必然 fail
closed。本腳本**不**做任何「舊 id 已被接續故不套用六格」的正規化——那會讓後續
明列表態被壓掉（見 D 的「舊 id 再度明列」探針）。

依 §4 末段／§5 末段的 `contract-baseline` cutover，cutover 前的歷史事件維持原貌、
**不得反向套進六格**。因此 C 段是**診斷性的 what-if**，用來顯示新契約在該形狀的
事件流上會怎麼判，**不是**主張 #16 應被重新裁決。
"""

from __future__ import annotations

import itertools
import sys

# --------------------------------------------------------------------------
# 共用常數
# --------------------------------------------------------------------------

RC_MARKER = "marker-scope-narrows-away-safety-signal"
RC_PR = "universal-pr-ci-conflicts-with-canonical-classification"
RC_GEN = "incomplete-custom-classification-overrides-canonical"
RC_SPLIT = "split-composite-transition-without-intermediate-state"

STATUSES = ("open", "resolved", "withdrawn")
FINDING_CLASSES = ("implementation", "authoritative-artifact",
                   "governance", "coordination", "environment")
ATTRIBUTIONS = ("executor", "planner", "coordinator", "reviewer", "external")
ELIGIBLE_CLASSES = ("implementation", "authoritative-artifact")  # §3 第 3 款
DEFER_CAUSES = ("spec-narrowed", "instruction-omitted")          # §4 第 4 款

CELLS = ("resolved", "withdrawn", "已非有效 open finding", "仍開啟", "deferred", "未提及")
TRIGGERING = ("仍開啟", "未提及")
SETTLED = ("resolved", "withdrawn", "已非有效 open finding", "仍開啟")

# §4 單筆 defer 的必要條件，逐項具名（缺一即該筆無效）。
DEFER_CONDITIONS = (
    "in_carry",            # 1. finding 存在且屬本 checkpoint 的 carry set
    "by_requester",        # 2. deferred_by 逐字等於卡面「需求：」帳號
    "not_self_interested",  # 3. deferred_by 不是 owner，也不是本 epoch 任一 reviewer
    "cause_declared",      # 4a. defer_cause 取值於列舉
    "reason_nonempty",     # 4b. defer_reason 非空
    "ruling_url",          # 5. defer_ruling_url 非空
    "not_consecutive",     # §4「不得連續 defer」
)


def new_finding(**kw) -> dict:
    return {"status": "open", "accepted": True, "blocking": True,
            "finding_class": "implementation", "attribution": "executor", **kw}


def eligible(f: dict) -> bool:
    """§3 第 3～4 款。"""
    return f["finding_class"] in ELIGIBLE_CLASSES and f["attribution"] == "executor"


def valid_open(f: dict) -> bool:
    """§4「有效 open finding」。"""
    return f["status"] == "open" and f["accepted"] and f["blocking"] and eligible(f)


def classify(f: dict, *, mentioned_open: bool, defer_ok: bool) -> str:
    """§4 六格分類器。f 為該 finding 在 checkpoint 評估時點的狀態。"""
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


# 六個獨立述詞，逐字對應 §4 的表格與其優先序句。
PREDICATES = {
    "resolved": lambda f, m, d: f["status"] == "resolved",
    "withdrawn": lambda f, m, d: f["status"] == "withdrawn",
    "已非有效 open finding": lambda f, m, d: f["status"] == "open" and not valid_open(f),
    "仍開啟": lambda f, m, d: valid_open(f) and m,
    "deferred": lambda f, m, d: valid_open(f) and not m and d,
    "未提及": lambda f, m, d: valid_open(f) and not m and not d,
}


# ==========================================================================
# A. 分類器投影空間的分割（**不是**全函數證明；界線見檔頭）
# ==========================================================================

A_NOT_COVERED = [
    "carry set 成員資格（由 D 的事件層測試涵蓋）",
    "epoch 邊界的計數／carry／prev_deferred 重置（由 D 涵蓋）",
    "review-correction 相對 checkpoint 的位置（由 B 的事件順序涵蓋）",
    "同一 finding 的衝突事件與 §2 待裁決 gate —— 未涵蓋",
    "同 SHA 多 reviewer 合併後的 fail loud —— 未涵蓋",
    "留痕解析停機（§1／§5 review-marker-clearance）—— 未涵蓋",
]


def enumerate_classifier_domain():
    """列舉 classify() 宣告值域的每一點，回傳 (總數, 問題清單, 每格命中數)。"""
    problems: list[str] = []
    hit_count = {c: 0 for c in CELLS}
    total = 0
    cond_axes = list(itertools.product((True, False), repeat=len(DEFER_CONDITIONS)))
    for st, acc, blk, cls, attr, mentioned, declared in itertools.product(
        STATUSES, (True, False), (True, False), FINDING_CLASSES, ATTRIBUTIONS,
        (True, False), (True, False),
    ):
        f = {"status": st, "accepted": acc, "blocking": blk,
             "finding_class": cls, "attribution": attr}
        for bits in cond_axes:
            total += 1
            conds = dict(zip(DEFER_CONDITIONS, bits))
            defer_ok = declared and all(conds.values())
            hits = [n for n, p in PREDICATES.items() if p(f, mentioned, defer_ok)]
            if len(hits) != 1:
                problems.append(f"{f} mentioned={mentioned} defer_ok={defer_ok} → 命中 {hits}")
                continue
            got = classify(f, mentioned_open=mentioned, defer_ok=defer_ok)
            if got != hits[0]:
                problems.append(f"{f} → 分類器 {got} ≠ 述詞 {hits[0]}")
                continue
            hit_count[got] += 1
    return total, problems, hit_count


def prove_each_defer_condition_necessary():
    """逐項證明 DEFER_CONDITIONS 每一款都是必要條件。

    對每一個「若非該款則 defer 成立」的輸入，單獨把該款翻成 False，
    分類結果必須由 deferred 變為未提及；其餘六款不動。
    """
    base = new_finding()
    results = {}
    for i, cond in enumerate(DEFER_CONDITIONS):
        all_true = {c: True for c in DEFER_CONDITIONS}
        ok = classify(base, mentioned_open=False,
                      defer_ok=all(all_true.values())) == "deferred"
        flipped = dict(all_true, **{cond: False})
        broken = classify(base, mentioned_open=False,
                          defer_ok=all(flipped.values())) == "未提及"
        results[cond] = ok and broken
    return results


# ==========================================================================
# B. 事件層 replay 引擎
# ==========================================================================
#
# 事件種類：
#   attempt   {label, new:{fid:(rc, overrides)}, updates:{fid: partial}, counted}
#   correction{updates:{fid: partial}}            # review-correction
#   epoch     {}                                   # escalation-epoch-change
#   checkpoint{deferred:[{finding_id, defer_reason, deferred_by,
#                         defer_ruling_url, defer_cause}]}
#
# updates 中 {"status": "open"} 表示「本輪明列該 finding 仍開啟」。

CTX = {"requester": "ruan6047", "owner": "executor-agent", "reviewers": ("reviewer-x",)}


def A(label, new=None, updates=None, counted=True):
    return {"kind": "attempt", "label": label, "new": new or {},
            "updates": updates or {}, "counted": counted}


def CORR(updates):
    return {"kind": "correction", "updates": updates}


def EPOCH():
    return {"kind": "epoch"}


def CP(deferred=None):
    return {"kind": "checkpoint", "deferred": deferred or []}


def defer_entry(fid, *, by=None, reason="規格收窄", url="https://example/ruling",
                cause="spec-narrowed"):
    return {"finding_id": fid, "deferred_by": by or CTX["requester"],
            "defer_reason": reason, "defer_ruling_url": url, "defer_cause": cause}


class Checkpoint:
    __slots__ = ("trigger", "count", "epoch", "cond1_rcs", "cells",
                 "overdue", "cond2", "forced", "inert_defers")

    def __init__(self, trigger, count, epoch, cond1_rcs, cells, overdue, cond2, inert):
        self.trigger, self.count, self.epoch = trigger, count, epoch
        self.cond1_rcs, self.cells, self.overdue, self.cond2 = cond1_rcs, cells, overdue, cond2
        self.inert_defers = inert
        self.forced = bool(cond1_rcs) or cond2


def _defer_conditions(entry, fid, carry, prev_deferred, ctx):
    return {
        "in_carry": fid in carry,
        "by_requester": bool(ctx["requester"]) and entry.get("deferred_by") == ctx["requester"],
        "not_self_interested": (entry.get("deferred_by") != ctx["owner"]
                                and entry.get("deferred_by") not in ctx["reviewers"]),
        "cause_declared": entry.get("defer_cause") in DEFER_CAUSES,
        "reason_nonempty": bool((entry.get("defer_reason") or "").strip()),
        "ruling_url": bool((entry.get("defer_ruling_url") or "").strip()),
        "not_consecutive": fid not in prev_deferred,
    }


def replay(events, *, defeasible_cond1=True, allow_defer=True, ctx=None):
    """走一遍事件流，回傳 {trigger_label: Checkpoint} 與結構性問題清單。"""
    ctx = ctx or CTX
    state: dict[str, dict] = {}
    rc_of: dict[str, str] = {}
    epoch_of: dict[str, int] = {}
    occurrences: dict[tuple[int, str], set[str]] = {}
    snapshot: dict[str, set[str]] = {}
    mentioned: dict[str, set[str]] = {}
    structural: list[str] = []

    epoch = 0
    counted: list[str] = []
    prev_deferred: list[str] = []
    last_label: str | None = None
    cps: dict[str, Checkpoint] = {}
    pending_cp = 0  # 本 epoch 尚欠幾個 checkpoint

    def apply(updates, label):
        for fid, upd in updates.items():
            if fid not in state:
                structural.append(f"{label}: 更新不存在的 finding {fid}")
                continue
            state[fid] = {**state[fid], **upd}
            if upd.get("status") == "open" and label:
                mentioned.setdefault(label, set()).add(fid)

    for ev in events:
        kind = ev["kind"]

        if kind == "attempt":
            label = ev["label"]
            last_label = label
            apply(ev["updates"], label)
            for fid, (rc, over) in ev["new"].items():
                if fid in state:
                    structural.append(f"{label}: finding_id {fid} 重複提出")
                state[fid] = new_finding(**over)
                rc_of[fid] = rc
                epoch_of[fid] = epoch
                occurrences.setdefault((epoch, rc), set()).add(label)
            # carry 成員身分固定於本 attempt 的裁決落地當下（§4）。
            snapshot[label] = {f for f, s in state.items() if valid_open(s)}
            if ev.get("counted", True):
                counted.append(label)
                if len(counted) >= 3:
                    pending_cp += 1

        elif kind == "correction":
            apply(ev["updates"], last_label)

        elif kind == "epoch":
            if pending_cp:
                structural.append(f"epoch {epoch}: 換 epoch 前尚欠 {pending_cp} 個 checkpoint")
            epoch += 1
            counted = []
            prev_deferred = []
            pending_cp = 0

        elif kind == "checkpoint":
            if len(counted) < 3:
                structural.append(f"checkpoint 建立於第 {len(counted)} 個可計數 attempt（<3）")
                continue
            trigger = counted[-1]
            carry = snapshot[counted[-2]]
            entries = {e["finding_id"]: e for e in ev["deferred"]} if allow_defer else {}

            cells: dict[str, str] = {}
            for fid in sorted(carry):
                entry = entries.get(fid)
                ok = False
                if entry is not None:
                    ok = all(_defer_conditions(entry, fid, carry, prev_deferred, ctx).values())
                cells[fid] = classify(
                    state[fid],
                    mentioned_open=fid in mentioned.get(trigger, set()),
                    defer_ok=ok,
                )
            # §4：對不在 carry set 的 finding 的 defer 宣告是無作用的冗贅，
            # 不使本 checkpoint 無效。
            inert = sorted(set(entries) - set(carry))

            overdue = [f for f in prev_deferred if cells.get(f) not in SETTLED]

            seen = set(counted)
            alive = {rc_of[f] for f, s in state.items()
                     if valid_open(s) and epoch_of[f] == epoch}
            cond1 = sorted(rc for (e, rc), labs in occurrences.items()
                           if e == epoch and len(labs & seen) >= 3
                           and (not defeasible_cond1 or rc in alive))
            cond2 = any(c in TRIGGERING for c in cells.values()) or bool(overdue)

            cps[trigger] = Checkpoint(trigger, len(counted), epoch,
                                      cond1, cells, overdue, cond2, inert)
            prev_deferred = [f for f, c in cells.items() if c == "deferred"]
            pending_cp = max(0, pending_cp - 1)

        else:  # pragma: no cover
            structural.append(f"未知事件種類 {kind}")

    if pending_cp:
        structural.append(f"事件流結束時尚欠 {pending_cp} 個 checkpoint")
    return cps, structural


def render(title, cps, only=None):
    print(f"\n===== {title} =====")
    for key, cp in cps.items():
        if only and key not in only:
            continue
        c1 = f"TRUE  {cp.cond1_rcs}" if cp.cond1_rcs else "false"
        print(f"C@{cp.trigger}  (epoch={cp.epoch}, unique_attempt_count={cp.count})")
        print(f"    條件1 累計×3 ∧ 存活 : {c1}")
        print(f"    carry 六格分類      : {cp.cells or '{}'}")
        print(f"    逾期未清償          : {cp.overdue or '—'}")
        if cp.inert_defers:
            print(f"    無作用的 defer 宣告 : {cp.inert_defers}")
        print(f"    條件2               : {'TRUE' if cp.cond2 else 'false'}")
        print(f"    => 強制為: {'escalate' if cp.forced else '不強制（continue/replan 皆合法）'}")


# ==========================================================================
# C. #16 忠實回放（legacy；不做任何 id 正規化）
# ==========================================================================

# 5248665281 逐字：只有兩筆。
DEFER_AT_C_R3 = [
    defer_entry("R2-001", reason="R3 依需求方裁定改為窄規格，明文不逐條複驗",
                url="https://github.com/ruan6047/ai-workflow/issues/16#issuecomment-5248665281"),
    defer_entry("R2-002", reason="R3 依需求方裁定改為窄規格，明文不逐條複驗",
                url="https://github.com/ruan6047/ai-workflow/issues/16#issuecomment-5248665281"),
]

EVENTS_16 = [
    A("R1", new={"R1-001": ("rc-r1-001", {}), "R1-002": (RC_MARKER, {}),
                 "R1-003": ("rc-r1-003", {}), "R1-004": ("rc-r1-004", {}),
                 "R1-005": ("rc-r1-005", {}), "R1-006": (RC_PR, {})}),
    # R2：四項閉環；R1-002／R1-006 未被處置，以新 id 更窄地再次提出。
    A("R2", new={"R2-001": (RC_MARKER, {}), "R2-002": (RC_PR, {})},
      updates={"R1-001": {"status": "resolved"}, "R1-003": {"status": "resolved"},
               "R1-004": {"status": "resolved"}, "R1-005": {"status": "resolved"}}),
    # R3：窄規格，對前輪 finding 零處置。
    A("R3", new={"R3-001": (RC_GEN, {})}),
    CP(deferred=DEFER_AT_C_R3),
    A("R4", new={"R4-001": (RC_GEN, {})},
      updates={"R1-002": {"status": "resolved"}, "R1-006": {"status": "resolved"},
               "R2-001": {"status": "resolved"}, "R2-002": {"status": "resolved"},
               "R3-001": {"status": "resolved"}}),
    CP(),
    # R5：新 1（R5-002）＋ 再開 1（R4-001，以新 id R5-001 表示）。
    A("R5", new={"R5-001": (RC_GEN, {}), "R5-002": (RC_GEN, {})}),
    CP(),
    A("R6", new={"R6-001": (RC_GEN, {})},
      updates={"R5-001": {"status": "open"}, "R5-002": {"status": "open"}}),
    CP(),
    A("R7", new={"R7-001": (RC_GEN, {})},
      updates={"R5-001": {"status": "open"}, "R5-002": {"status": "open"},
               "R6-001": {"status": "open"}}),
    CP(),
    A("R8", new={"R8-001": (RC_SPLIT, {})},
      updates={"R5-001": {"blocking": False}, "R5-002": {"blocking": False},
               "R7-001": {"blocking": False}, "R6-001": {"status": "resolved"}}),
    CP(),
]


def events_16_with_probe():
    """【構造探針】R7 再度明列 R4-001 仍 open。

    用途：證明本引擎沒有任何「舊 id 已被接續」的正規化捷徑——舊 id 的後續明列
    表態必須被原樣處理（§4「六格的前提是穩定 finding_id」）。
    """
    out = []
    for ev in EVENTS_16:
        if ev["kind"] == "attempt" and ev["label"] == "R7":
            ev = dict(ev, updates=dict(ev["updates"], **{"R4-001": {"status": "open"}}))
        out.append(ev)
    return out


# ==========================================================================
# D. 構造情境（#16 未發生，逐一標示）
# ==========================================================================

def six_cell_stream():
    """【構造】一個 checkpoint 同時走出全部六格，且全部經由事件層引擎。

    F_WD 由 review-correction 標 withdrawn；F_ACC 由 review-correction 撤銷採認
    （status 仍 open）；F_DEG 由 trigger attempt 的 review 降為 blocking=false。
    """
    return [
        A("A1", new={f: (f"rc-{f}", {}) for f in
                     ("F_RES", "F_WD", "F_DEG", "F_ACC", "F_OPEN", "F_DEF", "F_SIL")}),
        A("A2", new={"A2-001": ("rc-a2", {})}),
        A("A3", new={"A3-001": ("rc-a3", {})},
          updates={"F_RES": {"status": "resolved"},
                   "F_DEG": {"blocking": False},
                   "F_OPEN": {"status": "open"},
                   "A2-001": {"status": "resolved"}}),
        CORR({"F_WD": {"status": "withdrawn"}}),
        CORR({"F_ACC": {"accepted": False}}),
        CP(deferred=[defer_entry("F_DEF")]),
    ]


def defer_stream(defer_ids, *, cause="spec-narrowed", by=None, drop_field=None):
    """【構造】三項 carry 全部合法 deferred → 不強制；少一筆即強制。"""
    entries = []
    for fid in defer_ids:
        e = defer_entry(fid, by=by, cause=cause)
        if drop_field:
            e[drop_field] = ""
        entries.append(e)
    return [
        A("B0", new={"B0-001": ("rc-b0", {})}),
        A("B1", new={"B-001": ("rc-b1", {}), "B-002": ("rc-b2", {}), "B-003": ("rc-b3", {})},
          updates={"B0-001": {"status": "resolved"}}),
        A("B3", new={"B3-001": ("rc-b5", {})}),
        CP(deferred=entries),
    ]


def repay_stream(second_cp_deferred, *, settle):
    """【構造】清償上限：C 宣告 defer，C′ 必須逐項表態，否則逾期。"""
    updates = {"C-001": {"status": "resolved"}} if settle else {}
    return [
        A("C1", new={"C-001": ("rc-c1", {}), "C-002": ("rc-c2", {})}),
        A("C2", new={"C2-001": ("rc-c2b", {})}),
        A("C3", new={"C3-001": ("rc-c3", {})},
          updates={"C-002": {"status": "resolved"}, "C2-001": {"status": "resolved"}}),
        CP(deferred=[defer_entry("C-001")]),
        A("C4", new={"C4-001": ("rc-c4", {})}, updates={**updates,
                                                        "C3-001": {"status": "resolved"}}),
        CP(deferred=second_cp_deferred),
    ]


def epoch_stream():
    """【構造】epoch 邊界：計數、carry、prev_deferred 全部重置。"""
    return [
        A("E1", new={"E-001": (RC_GEN, {})}),
        A("E2", new={"E-002": (RC_GEN, {})}, updates={"E-001": {"status": "resolved"}}),
        A("E3", new={"E-003": (RC_GEN, {})}, updates={"E-002": {"status": "resolved"}}),
        # E-001 早已離開 open set（不在 carry）→ 無作用的冗贅；
        # E-002 在 carry 但本輪已 resolved → 依 §4 優先序取 resolved，defer 宣告不生效。
        CP(deferred=[defer_entry("E-001"), defer_entry("E-002")]),
        EPOCH(),
        A("F1", new={"F-001": ("rc-f1", {})}, updates={"E-003": {"status": "resolved"}}),
        A("F2", new={"F-002": ("rc-f2", {})}, updates={"F-001": {"status": "resolved"}}),
        A("F3", new={"F-003": ("rc-f3", {})}, updates={"F-002": {"status": "resolved"}}),
        CP(),
    ]


def cond1_stream(*, revive):
    """【構造】條件1 的可失效性：累計滿三後停止 → 失效；重新產出 → 立刻恢復。"""
    tail_new = {"G-005": (RC_GEN if revive else "rc-new", {})}
    return [
        A("G1", new={"G-001": (RC_GEN, {})}),
        A("G2", new={"G-002": (RC_GEN, {})}, updates={"G-001": {"status": "resolved"}}),
        A("G3", new={"G-003": (RC_GEN, {})}, updates={"G-002": {"status": "resolved"}}),
        CP(),
        A("G4", new={"G-004": ("rc-other", {})}, updates={"G-003": {"status": "resolved"}}),
        CP(),
        A("G5", new=tail_new, updates={"G-004": {"status": "resolved"}}),
        CP(),
    ]


def stable_id_repair_of_16():
    """【構造】#16 的**最小合法改寫**：把三處換號重開改成穩定 id 的表示法。

    substance 完全保留（同樣的輪次、同樣的再開、同樣的 transferred 處置），只把
    「以新 id 重新提出」改為「明列同一 finding 仍 open」。這是唯一能讓 #16 的實質
    走完新契約的方式，也是本卡兩項驗證條文在**合法事件流**上的證據。
    """
    defer = [defer_entry(
        "R1-002", reason="R3 依需求方裁定改為窄規格，明文不逐條複驗",
        url="https://github.com/ruan6047/ai-workflow/issues/16#issuecomment-5248665281"),
        defer_entry(
        "R1-006", reason="R3 依需求方裁定改為窄規格，明文不逐條複驗",
        url="https://github.com/ruan6047/ai-workflow/issues/16#issuecomment-5248665281")]
    return [
        A("R1", new={"R1-001": ("rc-r1-001", {}), "R1-002": (RC_MARKER, {}),
                     "R1-003": ("rc-r1-003", {}), "R1-004": ("rc-r1-004", {}),
                     "R1-005": ("rc-r1-005", {}), "R1-006": (RC_PR, {})}),
        # R2：四項閉環；R1-002／R1-006 以**同一 id** 明列仍開啟（原為換號重開）。
        A("R2", updates={"R1-001": {"status": "resolved"}, "R1-003": {"status": "resolved"},
                         "R1-004": {"status": "resolved"}, "R1-005": {"status": "resolved"},
                         "R1-002": {"status": "open"}, "R1-006": {"status": "open"}}),
        A("R3", new={"R3-001": (RC_GEN, {})}),
        CP(deferred=defer),
        A("R4", new={"R4-001": (RC_GEN, {})},
          updates={"R1-002": {"status": "resolved"}, "R1-006": {"status": "resolved"},
                   "R3-001": {"status": "resolved"}}),
        CP(),
        # R5：新 1（R5-002）＋ 再開 1，後者以**同一 id** R4-001 表示。
        A("R5", new={"R5-002": (RC_GEN, {})}, updates={"R4-001": {"status": "open"}}),
        CP(),
        A("R6", new={"R6-001": (RC_GEN, {})},
          updates={"R4-001": {"status": "open"}, "R5-002": {"status": "open"}}),
        CP(),
        A("R7", new={"R7-001": (RC_GEN, {})},
          updates={"R4-001": {"status": "open"}, "R5-002": {"status": "open"},
                   "R6-001": {"status": "open"}}),
        CP(),
        A("R8", new={"R8-001": (RC_SPLIT, {})},
          updates={"R4-001": {"blocking": False}, "R5-002": {"blocking": False},
                   "R7-001": {"blocking": False}, "R6-001": {"status": "resolved"}}),
        CP(),
    ]


# ==========================================================================
# main
# ==========================================================================

def main() -> int:
    checks: list[tuple[str, bool]] = []

    # ---- A ---------------------------------------------------------------
    total, problems, hit_count = enumerate_classifier_domain()
    print("===== A. 分類器投影空間的分割（非全函數證明）=====")
    print(f"  列舉點數（classify() 宣告值域）：{total}")
    print(f"  每點恰好命中一格且與分類器一致：{'是' if not problems else '否'}")
    print(f"  各格命中點數：{hit_count}")
    print("  本段**不**涵蓋：")
    for item in A_NOT_COVERED:
        print(f"    - {item}")
    for p in problems[:5]:
        print(f"    ✗ {p}")
    checks.append((f"分類器在其宣告值域上是分割：{total} 點各恰好落一格且與述詞一致",
                   not problems))
    checks.append(("六格皆為可達（列舉中每格至少一點）",
                   all(v > 0 for v in hit_count.values())))

    necessity = prove_each_defer_condition_necessary()
    print("\n  defer 必要條件逐項驗證（單獨翻假即 deferred → 未提及）：")
    for cond, ok in necessity.items():
        print(f"    [{'PASS' if ok else 'FAIL'}] {cond}")
    checks.append((f"defer 的 {len(DEFER_CONDITIONS)} 款必要條件逐項獨立驗證通過",
                   all(necessity.values())))

    # ---- B：六格由事件層引擎走出 --------------------------------------------
    six, st_six = replay(six_cell_stream())
    render("B. 六格全部由事件層引擎走出【構造】", six)
    expect_cells = {
        "F_RES": "resolved", "F_WD": "withdrawn", "F_DEG": "已非有效 open finding",
        "F_ACC": "已非有效 open finding", "F_OPEN": "仍開啟",
        "F_DEF": "deferred", "F_SIL": "未提及",
    }
    six_ok = all(six["A3"].cells.get(k) == v for k, v in expect_cells.items())
    checks += [
        ("六格全部由事件層引擎走出（含 review-correction → withdrawn 與 accepted=false）",
         six_ok and not st_six),
        ("六格情境覆蓋全部 6 格，無遺漏",
         set(six["A3"].cells.values()) == set(CELLS)),
        ("trigger attempt 自己提出的 finding（A3-001）不屬 carry set",
         "A3-001" not in six["A3"].cells),
    ]

    # ---- C：#16 忠實回放 ---------------------------------------------------
    literal, st_lit = replay(EVENTS_16, defeasible_cond1=False, allow_defer=False)
    revised, st_rev = replay(EVENTS_16, defeasible_cond1=True, allow_defer=True)
    render("C. #16 忠實回放【legacy】—— 現行條文（純累計；無 deferred 出口）", literal)
    render("C. #16 忠實回放【legacy】—— 修訂後條文（存活判準＋deferred 出口）", revised)
    print("\n  結構性問題：", st_lit or "—")

    checks += [
        ("#16 忠實回放無結構性問題", not st_lit and not st_rev),
        ("C@R3：現行條文強制 escalate（前輪 finding 全無表態）",
         literal["R3"].forced and literal["R3"].cond2 and not literal["R3"].cond1_rcs),
        ("C@R3：修訂後**仍**強制 escalate —— 需求方實際只 defer 了 R2-001／R2-002，"
         "而 R1-002／R1-006 因換號重開未被處置，落「未提及」",
         revised["R3"].forced
         and revised["R3"].cells["R2-001"] == "deferred"
         and revised["R3"].cells["R2-002"] == "deferred"
         and revised["R3"].cells["R1-002"] == "未提及"
         and revised["R3"].cells["R1-006"] == "未提及"),
        ("C@R3 的 deferred 集合逐字等於 5248665281 的兩筆，未被補造",
         [e["finding_id"] for e in DEFER_AT_C_R3] == ["R2-001", "R2-002"]),
        ("C@R4：C@R3 的兩筆 deferred 已由 R4 全數 resolved，無逾期",
         not revised["R4"].overdue and not revised["R4"].forced),
        ("R5–R7：條件1 成立（同根因跨三個以上可計數 attempt 且仍存活）",
         all(RC_GEN in revised[k].cond1_rcs for k in ("R5", "R6", "R7"))),
        ("C@R8：忠實回放下條件1 **仍**成立 —— R4-001 從未被處置，故該根因仍存活；"
         "這是換號重開的直接後果，不是判準失效",
         RC_GEN in revised["R8"].cond1_rcs and RC_GEN in literal["R8"].cond1_rcs),
        ("C@R8：忠實回放下 R4-001 落「未提及」而 fail-closed",
         revised["R8"].cells.get("R4-001") == "未提及"),
        ("R4-001 在任何 checkpoint 都未被記為 resolved／withdrawn（接續 ≠ 閉合）",
         all(cp.cells.get("R4-001") not in ("resolved", "withdrawn")
             for cp in revised.values())),
    ]

    # 探針：舊 id 的後續明列表態必須被原樣處理（R2-002）
    probe, _ = replay(events_16_with_probe(), defeasible_cond1=True, allow_defer=True)
    render("C. 探針【構造】：R7 再度明列 R4-001 仍 open", probe, only={"R7"})
    checks += [
        ("探針：R7 再度明列 R4-001 時，引擎輸出「仍開啟」而非把它壓掉",
         probe["R7"].cells.get("R4-001") == "仍開啟"),
        ("探針：R4-001 在**每一個** checkpoint 的 carry 分類都有輸出，不會消失",
         all("R4-001" in cp.cells for k, cp in probe.items() if k in ("R5", "R6", "R7", "R8"))),
    ]

    # ---- D：deferred 出口與敏感度 ------------------------------------------
    all_ids = ["B-001", "B-002", "B-003"]
    full, _ = replay(defer_stream(all_ids))
    minus_one, _ = replay(defer_stream(all_ids[:-1]))
    bad_by, _ = replay(defer_stream(all_ids, by=CTX["owner"]))
    bad_url, _ = replay(defer_stream(all_ids, drop_field="defer_ruling_url"))
    omitted, _ = replay(defer_stream(all_ids, cause="instruction-omitted"))
    bad_cause, _ = replay(defer_stream(all_ids, cause="executor-was-busy"))
    render("D. deferred 出口【構造】：三項 carry 全部合法 defer", full, only={"B3"})
    render("D. 敏感度【構造】：少 defer 一筆（B-003）", minus_one, only={"B3"})
    checks += [
        ("deferred 出口成立：全部 carry 合法 defer 時不強制 escalate",
         not full["B3"].forced and set(full["B3"].cells.values()) == {"deferred"}),
        ("敏感度：少一筆 defer 即強制 escalate，且該筆落「未提及」",
         minus_one["B3"].forced and minus_one["B3"].cells["B-003"] == "未提及"),
        ("身分把關：deferred_by 等於 owner 時全部失效並強制 escalate",
         bad_by["B3"].forced and set(bad_by["B3"].cells.values()) == {"未提及"}),
        ("缺 defer_ruling_url 時該筆失效並強制 escalate",
         bad_url["B3"].forced and set(bad_url["B3"].cells.values()) == {"未提及"}),
        ("新增的 instruction-omitted 成因可用：查核指示缺漏亦可 defer",
         not omitted["B3"].forced and set(omitted["B3"].cells.values()) == {"deferred"}),
        ("列舉外的 defer_cause 一律失效（不得自創成因）",
         bad_cause["B3"].forced and set(bad_cause["B3"].cells.values()) == {"未提及"}),
    ]

    settled, _ = replay(repay_stream([], settle=True))
    silent, _ = replay(repay_stream([], settle=False))
    redefer, _ = replay(repay_stream([defer_entry("C-001")], settle=False))
    render("D. 清償【構造】：C′ 給出 resolved", settled, only={"C4"})
    render("D. 逾期【構造】：C′ 對 deferred 集合保持沉默", silent, only={"C4"})
    render("D. 連續 defer【構造】：C′ 對同一筆再 defer 一次", redefer, only={"C4"})
    checks += [
        ("清償：C′ 明列 resolved 即無逾期、不強制",
         not settled["C4"].overdue and not settled["C4"].forced),
        ("逾期：C′ 沉默即列入逾期並強制 escalate",
         silent["C4"].overdue == ["C-001"] and silent["C4"].forced),
        ("不得連續 defer：C′ 再 defer 同一筆判為無效、落「未提及」且列入逾期",
         redefer["C4"].cells["C-001"] == "未提及"
         and redefer["C4"].overdue == ["C-001"] and redefer["C4"].forced),
    ]

    ep, st_ep = replay(epoch_stream())
    render("D. epoch 邊界【構造】", ep)
    checks += [
        ("epoch 邊界：新 epoch 從零計數，舊 epoch 的 occurrence 不跨界（條件1 不成立）",
         not ep["F3"].cond1_rcs and RC_GEN in ep["E3"].cond1_rcs),
        ("epoch 邊界：舊 epoch 的 deferred 不延續為新 epoch 的逾期",
         not ep["F3"].overdue),
        ("對不在 carry set 的 finding 宣告 defer 只是無作用的冗贅，不使 checkpoint 無效",
         ep["E3"].inert_defers == ["E-001"] and not st_ep),
        ("優先序：已離開 open set 者即使被宣告 defer，仍取 resolved 格",
         ep["E3"].cells["E-002"] == "resolved"),
    ]

    stopped, _ = replay(cond1_stream(revive=False))
    revived, _ = replay(cond1_stream(revive=True))
    stopped_literal, _ = replay(cond1_stream(revive=False), defeasible_cond1=False)
    render("D. 條件1 可失效【構造】：根因停止產出", stopped)
    render("D. 條件1 可失效【構造】：根因重新產出", revived, only={"G5"})
    checks += [
        ("條件1：累計滿三且仍存活時成立（C@G3）", RC_GEN in stopped["G3"].cond1_rcs),
        ("條件1：根因停止產出有效 open finding 後失效（C@G4／C@G5）",
         not stopped["G4"].cond1_rcs and not stopped["G5"].cond1_rcs),
        ("條件1：現行字面（純累計）在同一事件流上永久閂住，對照組確認差異",
         RC_GEN in stopped_literal["G4"].cond1_rcs
         and RC_GEN in stopped_literal["G5"].cond1_rcs),
        ("條件1：根因重新產出即立刻恢復，不需重新累積三次",
         RC_GEN in revived["G5"].cond1_rcs),
    ]

    # ---- D：#16 的穩定 id 最小改寫 ------------------------------------------
    fix, st_fix = replay(stable_id_repair_of_16())
    fix_lit, _ = replay(stable_id_repair_of_16(), defeasible_cond1=False, allow_defer=False)
    render("D. #16 的穩定 id 最小改寫【構造】（substance 不變，只改表示法）", fix)
    checks += [
        ("改寫流無結構性問題", not st_fix),
        ("改寫流 C@R3：現行條文強制 escalate", fix_lit["R3"].forced),
        ("改寫流 C@R3：修訂後 deferred 出口成立，不再強制 escalate",
         not fix["R3"].forced and set(fix["R3"].cells.values()) == {"deferred"}),
        ("改寫流 R5–R7：條件1 仍成立", all(RC_GEN in fix[k].cond1_rcs
                                          for k in ("R5", "R6", "R7"))),
        ("改寫流 C@R8：修訂後條件1 不再成立（前七例根因已無有效 open finding）",
         not fix["R8"].cond1_rcs and RC_GEN in fix_lit["R8"].cond1_rcs),
        ("改寫流 C@R8：修訂後兩條件皆不成立，不再被強制 escalate",
         not fix["R8"].forced and fix_lit["R8"].forced),
        ("改寫流 C@R8：transferred 三項以 blocking=false 落「已非有效 open finding」",
         all(fix["R8"].cells[f] == "已非有效 open finding"
             for f in ("R4-001", "R5-002", "R7-001"))),
    ]

    # ---- 正交性 ------------------------------------------------------------
    only_c1, _ = replay(EVENTS_16, defeasible_cond1=True, allow_defer=False)
    only_c2, _ = replay(EVENTS_16, defeasible_cond1=False, allow_defer=True)
    fix_c1, _ = replay(stable_id_repair_of_16(), defeasible_cond1=True, allow_defer=False)
    fix_c2, _ = replay(stable_id_repair_of_16(), defeasible_cond1=False, allow_defer=True)
    checks += [
        ("正交性 1：deferred 出口不改變任何 checkpoint 的條件1 判定",
         all(only_c1[k].cond1_rcs == revised[k].cond1_rcs for k in revised)
         and all(literal[k].cond1_rcs == only_c2[k].cond1_rcs for k in revised)
         and all(fix_c1[k].cond1_rcs == fix[k].cond1_rcs for k in fix)),
        ("正交性 2：條件1 的存活判準不改變任何 checkpoint 的條件2 判定",
         all(literal[k].cond2 == only_c1[k].cond2 for k in revised)
         and all(only_c2[k].cond2 == revised[k].cond2 for k in revised)
         and all(fix_c2[k].cond2 == fix[k].cond2 for k in fix)),
        ("兩條件各自獨立充分：改寫流 C@R5–R7 僅憑條件1 即強制 escalate",
         all(fix_c1[k].forced for k in ("R5", "R6", "R7"))),
    ]

    # ---- 結論摘要 ----------------------------------------------------------
    print("\n===== 結論摘要（供查核者對照卡面驗證條文）=====")
    print("  1. #16 的**忠實**事件流在修訂後條文下 C@R3 仍強制 escalate。原因不是 deferred")
    print("     出口失效，而是需求方實際只 defer 了兩筆（5248665281），而 carry set 有四筆：")
    print("     R1-002／R1-006 在 R2 被換號為 R2-001／R2-002 重新提出，依 §4「六格的前提是")
    print("     穩定 finding_id」不構成處置，故落「未提及」。腳本**不**補造第三、四筆 defer。")
    print("  2. 同理，#16 忠實流在 C@R8 的條件1 仍為 TRUE：R4-001 自 R5 起被換號為 R5-001，")
    print("     從未被任何一輪處置，故該根因始終有有效 open finding。這是換號重開的後果，")
    print("     不是存活判準失效。")
    print("  3. 卡面兩項驗證條文（deferred 出口在 R4 前生效；條件1 在 R8 失效）成立於")
    print("     『#16 的穩定 id 最小改寫』——substance 完全相同、只把三處換號改成明列同一")
    print("     finding 仍開啟。見上方 D 段。改寫流已標示為構造，不冒充事實。")
    print("  4. #16 為 cutover 前的 legacy 事件流；依 §4／§5 末段不得反向套進六格。C 段是")
    print("     診斷性 what-if，不主張 #16 應被重新裁決。")

    # ---- 斷言彙總 ----------------------------------------------------------
    print("\n===== 斷言 =====")
    failed = sum(not ok for _, ok in checks)
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"\n{len(checks) - failed}/{len(checks)} 通過")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
