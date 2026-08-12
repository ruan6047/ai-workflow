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
  D2. `instruction-omitted` 的缺漏證據（§4 專節 (a)(b)(c)）：含 R3-001 隔離探針的
     逐字重跑與四種反例。全部明確標示為構造。
  D3. `spec-narrowed` 的裁定證據（§4 專節 (a′)(b′)(c′)）：R4-001 的三個指定反例
     （任意本卡留言／非需求方留言／內容未收窄）＋ 新鮮性與可用性反例。全部明確
     標示為構造。
  E. `escalation-resolution`（§4「`escalate` 之後的第三種結果」／§5 七款）：escalate
     之後需求方裁定維持同執行者的表示法。含重建命題的正例、`continued_owner` 缺項
     對照、owner 雙相檢查的**初稿對照組**、沿用的三項事實比對、連續沿用被拒，以及
     `authorization_binding` 三態。全部明確標示為構造。

--------------------------------------------------------------------------
E 的宣稱界線
--------------------------------------------------------------------------
E 段證明的是**規則對結構化欄位有鑑別力**，與 D2／D3 同一層級：裁定留言仍是
`COMMENT` fixture（`author` ＋ `body`），對應 adapter 以唯讀 API 取得的兩個欄位。

它**不**證明：某一則真實 GitHub 留言的現行原文已被讀取核對。

它也**不**能證明授權款有實質保證——恰恰相反，E6 是用來**證明它今天沒有**：
`derive_authorization_binding()` 在本 repo 的參數下恆回 `structurally-vacuous`
（需求方帳號同屬被授權 writer 集合，且執行者／查核者不是平台帳號）。該三態測試
的用途是把「這個檢查今天分不開任何兩方」變成一個會 FAIL 的斷言，而不是讓恆真
偽裝成通過。轉為 `substantive` 的條件同樣以斷言釘住（E6 第一例）。

E3 是**對照組驅動**的：同一條事件流分別以 `owner_check="two-phase"`（修訂後）與
`owner_check="draft-single-phase"`（初稿）跑。初稿把「`continued_owner` 逐字等於
下一個 attempt 的 owner」寫成單相檢查，而裁定寫入當下下一個 attempt 尚不存在，
故該款在初稿下**恆真**、違反宣告的 attempt 不會被擋——E3 直接斷言這個差異，
否則「已修正」只是一句寫下來的結論，沒有守衛。

--------------------------------------------------------------------------
A 的宣稱界線（R2-003）
--------------------------------------------------------------------------
A 段列舉的是 **`classify()` 這個函式的輸入空間**：finding 的五個結構化欄位、
「本輪是否明列仍 open」、以及 defer 是否成立所需的十一個布林條件。它證明的是
**分類器對其宣告值域是一個分割**，僅此而已。

它**不**涵蓋（這些改由 B～D2 的事件層測試或明確聲明未涵蓋處理）：

  1. finding 是否屬於本 checkpoint 的 carry set（→ D「carry 成員資格」）
  2. epoch 邊界對計數／carry／prev_deferred 的重置（→ D「epoch 邊界」）
  3. review-correction 相對 checkpoint 的**位置**（→ B 六格情境以事件順序驅動）
  4. 十四款 defer 條件各自的**真值如何從事件流算出**（→ D2／D3；A 段只把它們當
     自由布林軸，證明「缺一即不成立」）
  5. 同一 finding 的**衝突事件**與 §2 的待裁決 gate ——**未涵蓋**。本引擎不模擬
     衝突偵測，也不模擬同 SHA 多 reviewer 合併後的 fail loud。任何「本腳本證明
     §2 衝突處理正確」的宣稱都是假的。
  6. 留痕解析停機（§1／§5 `review-marker-clearance`）——**未涵蓋**。

--------------------------------------------------------------------------
D2 的宣稱界線（R3-001）
--------------------------------------------------------------------------
`instruction-omitted` 宣稱的是否定事實（某一則派審指示**沒有**要求逐項回報閉環）。
本腳本把該事實建模為事件流上的結構化欄位：派審事件的 `review_prompt_url` 與
`closure_reporting_requested`（§4 專節 (a)(b)）。因此 D2 證明的是**規則對這些欄位
有鑑別力**——欄位缺、值為 true、指向別輪、URL 不能解析為本卡留言、理由未指涉同一
則留痕，五者任一即該筆 defer 失效。

它**不**證明：某一則真實 GitHub 留言的原文已被讀取核對。本腳本不連網，dispatch
事件是 fixture。取得真實欄位是 adapter（ai-workflow#9）的義務；取不到時 §4 專節 (c)
要求 fail-closed，本腳本的**預設 `CTX` 即為該狀態**（`instruction_omitted_supported`
=False，對應本 repo 現況：`handoff` payload 尚無該兩欄、`wfcli` 尚無 checkpoint
writer）。正例必須明示改用 `CTX_SUPPORTED` 才跑得出來，且已標示為構造。

--------------------------------------------------------------------------
D3 的宣稱界線（R4-001）
--------------------------------------------------------------------------
前一版對 `spec-narrowed` 只驗「URL 解析為本卡留言 ＋ 理由含同一數字 id ＋
`deferred_by` 身分」，**不讀該留言**。因此取得任意本卡 comment id 即可讓有效 open
finding 落 `deferred`。前一版為此不對稱辯護的論證（「肯定作為的留痕與事實同體」）
本身不假，但「同體」只在**該留痕確經核對就是那個裁定**時成立，而當時沒有任何一款
在做這件核對——前提未兌現。§4 專節 (a′)(b′)(c′) 兌現它，本段建模之。

本腳本把裁定留言建模為事件流上的 `COMMENT` fixture（`author` ＋ `body`），對應
adapter 以唯讀 API 取得的兩個欄位。因此 D3 證明的是**規則對 author 與內容綁定有
鑑別力**：author 非需求方、body 未逐字含 trigger attempt 的 `attempt_id`／該筆
`finding_id`／`defer_cause: spec-narrowed`、綁定指向前一輪、或 adapter 無讀取能力，
任一即該筆 defer 失效。

它**不**證明：某一則真實 GitHub 留言的現行原文已被讀取。fixture 的 `body` 只建模
「可機械檢查的性質」，真實原文可由檔頭 C 段的 `gh api` 指令取回自行核對。

**`author` 與 `body` 的取得能力在本 repo 已存在**（`cli/src/wf_cli/doctor.py` 的
`audit_review_channel` 已在讀 comment body 與 `user.login`），故預設 `CTX` 的
`comment_read_supported=True`——`spec-narrowed` 的失效不是「能力不存在」，而是
「證據不成立」。缺的是 checkpoint writer 本身（#9），那使 `deferred_findings` 今天
**整個機制**都寫不出來，與本段收緊無關。

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

import hashlib
import itertools
import re
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

# 本卡（#16 事件流）所屬 issue；constructed 情境沿用同一 issue 只為 URL 形狀。
CARD_ISSUE_URL = "https://github.com/ruan6047/ai-workflow/issues/16"

# attempt_id 的形狀依 §5：<card>-e<epoch>-<full source sha>。本腳本以 label 的
# SHA-1 當 source sha 的替身（同為 40 hex），只為讓「裁定留言逐字含 attempt_id」
# 這個綁定可被真實地比對；替身不代表任何真實 commit。
CARD_ID = "WF-CARD"

# §4 (b′-2)：裁定留言必須逐字含此 token，才算宣告本筆的收窄。key 名沿用 §5 的
# deferred_findings schema，不另立新 marker（新 marker 的權威定義屬 handoff-contract）。
NARROW_TOKEN = "defer_cause: spec-narrowed"


def sha_stub(label: str) -> str:
    return hashlib.sha1(label.encode("utf-8")).hexdigest()


def attempt_uid(epoch: int, label: str) -> str:
    return f"{CARD_ID}-e{epoch}-{sha_stub(label)}"


def ruling_url(comment_id, issue_url=CARD_ISSUE_URL) -> str:
    return f"{issue_url}#issuecomment-{comment_id}"


def parse_ruling_id(url, issue_url) -> str | None:
    """§4 第 5 款：URL 必須解析為**本卡 issue** 的單一留言。"""
    m = re.fullmatch(re.escape(issue_url) + r"#issuecomment-(\d+)", (url or "").strip())
    return m.group(1) if m else None


# §4 單筆 defer 的必要條件，逐項具名（缺一即該筆無效）。
DEFER_CONDITIONS = (
    "in_carry",            # 1. finding 存在且屬本 checkpoint 的 carry set
    "by_requester",        # 2. deferred_by 逐字等於卡面「需求：」帳號
    "not_self_interested",  # 3. deferred_by 不是 owner，也不是本 epoch 任一 reviewer
    "cause_declared",      # 4a. defer_cause 取值於列舉
    "reason_nonempty",     # 4b. defer_reason 非空
    "ruling_url_on_card",  # 5. defer_ruling_url 解析為本卡 issue 的單一留言
    "reason_cites_ruling",  # 6. defer_reason 逐字含該留言的數字 id
    # 7 = §4「instruction-omitted：否定事實的三款」(a)(b)(c)，只對該 cause 生效。
    "omission_dispatch_identified",  # 7a. 派審事件以 review_prompt_url 指認同一則，且派的是 trigger attempt
    "omission_declared_false",       # 7b. 該派審事件的 closure_reporting_requested 恰為 false
    "cause_available",               # 7c. 寫入通道／adapter 具備 (a)(b) 能力，否則本 cause 不可用
    # 8 = §4「spec-narrowed：肯定作為的三款」(a′)(b′)(c′)，只對該 cause 生效。
    # 兩組的差別是**證據的形狀**（肯定作為要證明「這一則就是那個作為」；否定事實要
    # 證明「那一則少了某段內容」），不是強度：兩組都必須可機械核對、都 fail-closed。
    "narrow_ruling_author_is_requester",  # 8a′. 該留言的 GitHub author 逐字為需求方
    "narrow_scope_bound",                 # 8b′. 內容逐字綁定 trigger attempt_id ＋ 本筆 finding_id ＋ NARROW_TOKEN
    "narrow_cause_available",             # 8c′. 結構化欄位或留言讀取能力至少其一存在
    "not_consecutive",     # §4「不得連續 defer」
)

# --------------------------------------------------------------------------
# §5 `escalation-resolution` 的必要條件，逐項具名（缺一即該則無效、升級狀態維持）。
# --------------------------------------------------------------------------
RESOLUTION_VALUES = ("continue-same-executor",)          # §5 第 4 款：唯一合法值
RESOLUTION_BASES = ("fresh-ruling", "carried-forward")   # §4「沿用必須重新表態」

RESOLUTION_CONDITIONS = (
    # 1. checkpoint_ref 指向本 epoch 既存、且 checkpoint_decision=escalate 的 checkpoint
    "checkpoint_is_escalate",
    "trigger_matches",              # 1. trigger_attempt_id 與該 checkpoint 逐字相同
    "epoch_matches",                # 1. escalation_epoch 逐字相同
    "one_to_one",                   # 2. 一則 checkpoint 至多被一則有效 resolution 解除
    "owner_declared",               # 3（第一相）. continued_owner 非空
    "resolution_value",             # 4. resolution 取值於列舉
    # 5 = fresh-ruling 的裁定留痕，只對該 basis 生效。
    "resolved_by_is_requester",     # 5. resolved_by 逐字等於卡面「需求：」欄帳號
    "ruling_url_on_card",           # 5. resolution_ruling_url 解析為本卡單一留言
    "ruling_author_is_requester",   # 5. 該留言的 GitHub comment author 逐字為需求方
    "ruling_binds_trigger",         # 5. 現行 body 逐字含 trigger_attempt_id（免時鐘新鮮性）
    "ruling_is_standalone",         # 5. 該留言不是 checkpoint／review event 所在的那一則
    # 6 = carried-forward 的沿用款，只對該 basis 生效。
    "carried_from_is_fresh",        # 6. carried_from 只能指向 resolution_basis=fresh-ruling
    "carried_source_unused",        # 6. 一次裁定至多被援用一次
    "carried_by_recorded",          # 6. 實際寫下本事件的帳號必須記下（二手不得寫成一手）
    "carry_forcing_set_identical",  # 6. 兩則 checkpoint 的強制成因集合相同
    "carry_no_new_occurrence",      # 6. 第一條件根因的 occurrence 累計數相同
    "carry_cond2_subset",           # 6. 第二條件觸發集合為子集
    "auth_binding_derived",         # 7. authorization_binding 由 adapter 導出，不得手填
)

# GitHub login 的形狀。用來判定一個身分是不是**可逐字比對的平台帳號**——
# 執行者／查核者若是「<模型>@<工具>（子 agent）」這類自由文字即不是，
# §4 的授權款對它恆真（見 derive_authorization_binding）。
_ACCOUNT_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\Z")


def is_platform_account(s) -> bool:
    return bool(s) and bool(_ACCOUNT_RE.match(s))


def derive_authorization_binding(ctx) -> str:
    """§4 授權節：adapter 導出，不得手填。

    `substantive` 需三款同時成立；否則 `structurally-vacuous`。後者**不使事件無效**，
    它的作用是把「這個檢查在本專案恆真」寫進事件流，而不是讓恆真偽裝成通過。
    """
    requester = ctx["requester"]
    if not is_platform_account(requester):
        return "structurally-vacuous"
    if requester in tuple(ctx.get("writer_accounts") or ()):
        return "structurally-vacuous"
    if not (is_platform_account(ctx["owner"])
            and all(is_platform_account(r) for r in ctx["reviewers"])):
        return "structurally-vacuous"
    return "substantive"


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
    "十四款 defer 條件的真值如何從事件流算出（由 D2／D3 涵蓋；A 段視為自由布林軸）",
    "派審指示**留言原文**是否真的不含逐項閉環要求 —— 未涵蓋（以結構化欄位建模）",
    "某一則**真實** GitHub 留言的現行 author／body —— 未涵蓋（D3 以 fixture 建模；"
    "真實取值是 adapter 的義務，取不到時 §4 (c′) 要求 fail-closed）",
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
        # 述詞與分類器對同一 (f, mentioned, defer_ok) 是純函式，故先把兩個
        # defer_ok 值各算一次；下面仍**逐點**走完全部條件向量並逐點計數，
        # 只是不重複求值。這是消除重複計算，不是抽樣。
        verdict = {}
        for defer_ok in (True, False):
            hits = [n for n, p in PREDICATES.items() if p(f, mentioned, defer_ok)]
            if len(hits) != 1:
                verdict[defer_ok] = (None,
                                     f"{f} mentioned={mentioned} defer_ok={defer_ok} → 命中 {hits}")
                continue
            got = classify(f, mentioned_open=mentioned, defer_ok=defer_ok)
            verdict[defer_ok] = ((got, None) if got == hits[0]
                                 else (None, f"{f} → 分類器 {got} ≠ 述詞 {hits[0]}"))
        for bits in cond_axes:
            total += 1
            cell, problem = verdict[declared and all(bits)]
            if cell is None:
                problems.append(problem)
                continue
            hit_count[cell] += 1
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
#   dispatch  {for_attempt, url, closure_reporting_requested}   # 派審事件（handoff）
#   comment   {url, author, body, narrowed}       # adapter 唯讀取回的 GitHub 留言
#   checkpoint{deferred:[{finding_id, defer_reason, deferred_by,
#                         defer_ruling_url, defer_cause}]}
#
# updates 中 {"status": "open"} 表示「本輪明列該 finding 仍開啟」。
#
# ⚠️ **dispatch 事件在本腳本是 fixture**：它模擬 handoff-contract.md §2 的派審事件在
# 補上 `review_prompt_url`／`closure_reporting_requested` 後的形狀。本腳本因此證明的是
# **規則對這些欄位有鑑別力**，不是「某一則真實留言已被讀取核對」。取得真實欄位是
# adapter（ai-workflow#9）的義務；取不到時 §4 專節 (c) 要求 fail-closed，見
# `CTX` 的 `instruction_omitted_supported=False` 預設。

CTX = {
    "requester": "ruan6047",
    "owner": "executor-agent",
    "reviewers": ("reviewer-x",),
    "issue_url": CARD_ISSUE_URL,
    # 本 repo 現況：handoff payload 無 review_prompt_url／closure_reporting_requested，
    # wfcli 亦無 checkpoint writer（#9 未完成）→ instruction-omitted 不可用。
    "instruction_omitted_supported": False,
    # §4 (c′)：spec-narrowed 只需唯讀能力。本 repo 的 doctor --review-channel 已在讀
    # comment body 與 user.login（cli/src/wf_cli/doctor.py::audit_review_channel），
    # 故建模為 True——該 cause 的失效是「證據不成立」，不是「能力不存在」。
    "comment_read_supported": True,
    # (b′-1) 結構化路徑的 schema 歸 handoff-contract.md 管轄，目前尚未定義 → False。
    "spec_narrow_structured_supported": False,
    # handoff-contract.md §5 宣告的被授權 review event writer 帳號集合。本 repo 只有
    # 一個人類帳號，需求方同屬其中 → §4 授權款恆為 structurally-vacuous。
    "writer_accounts": ("ruan6047",),
}


def ctx_with(**kw) -> dict:
    return {**CTX, **kw}


# 【構造】假想已完成 #9、派審事件已帶兩欄的採用專案。
CTX_SUPPORTED = ctx_with(instruction_omitted_supported=True)
# 【構造】假想 (b′-1) 的結構化欄位已由 handoff-contract.md 定義並可解析。
CTX_STRUCTURED = ctx_with(spec_narrow_structured_supported=True)
# 【構造】adapter 既無結構化欄位、也讀不到留言 author／body → (c′) 本 cause 不可用。
CTX_NO_READ = ctx_with(comment_read_supported=False)


# 【構造】E 段用的採用專案：需求方與 writer 共用同一帳號、執行者與查核者是自由文字，
# 逐字對應本 repo 現況。E6 用它證明授權款今天恆為 structurally-vacuous。
E_OWNER = "Claude Opus 5@Claude Code（子 agent）"
E_REVIEWER = "Claude Sonnet 5@Claude Code（查核）"
CTX_E = ctx_with(owner=E_OWNER, reviewers=(E_REVIEWER,))
# 【構造】假想需求方帳號已與 writer 集合分離、且執行者／查核者已是平台帳號。
CTX_SEPARATED = ctx_with(requester="requester-acct", writer_accounts=("pm-bot",),
                         owner="executor-acct", reviewers=("reviewer-acct",))


def A(label, new=None, updates=None, counted=True, owner=None):
    """`owner` 只在 E 段使用；其餘段落留 None，不參與 §5 第 3 款第二相的比對。"""
    return {"kind": "attempt", "label": label, "new": new or {},
            "updates": updates or {}, "counted": counted, "owner": owner}


def CORR(updates):
    return {"kind": "correction", "updates": updates}


def EPOCH():
    return {"kind": "epoch"}


def CP(deferred=None):
    return {"kind": "checkpoint", "deferred": deferred or []}


def RES(res_id, checkpoint_trigger, *, owner=E_OWNER, basis="fresh-ruling",
        resolved_by=None, ruling_comment_id=None, ruling_url=None,
        carried_from=None, carried_by=None, resolution="continue-same-executor",
        drop=()):
    """`escalation-resolution` 事件（§5）。

    `checkpoint_trigger` 以被解除 checkpoint 的 trigger label 指涉（本引擎以 label
    當 checkpoint 的識別，等價於 §5 的 `checkpoint_ref` ＋ `trigger_attempt_id`）。
    `drop` 供反例：把指定欄位抹成 None，用來證明該欄是必要成分。
    """
    ev = {"kind": "resolution", "id": res_id,
          "checkpoint_trigger": checkpoint_trigger,
          "resolution": resolution, "continued_owner": owner,
          "resolution_basis": basis,
          "resolved_by": resolved_by if resolved_by is not None else CTX["requester"],
          "resolution_ruling_url": (
              ruling_url if ruling_url is not None
              else (ruling_comment_id and ruling_url_of(ruling_comment_id))),
          "carried_from": carried_from, "carried_by": carried_by}
    for k in drop:
        ev[k] = None
    return ev


def ruling_url_of(comment_id):
    return ruling_url(comment_id)


def DISPATCH(for_attempt, comment_id, *, closure_reporting_requested, url=None):
    """派審事件（handoff）。`closure_reporting_requested=False` 記錄一次偏離
    review-prompt.md §6（未把「前輪 finding 逐項閉環驗證」帶進派審指示）。"""
    return {"kind": "dispatch", "for_attempt": for_attempt,
            "url": url or ruling_url(comment_id),
            "closure_reporting_requested": closure_reporting_requested}


def COMMENT(comment_id, author, body, *, narrowed=None, issue_url=CARD_ISSUE_URL,
            verdict=False):
    """adapter 唯讀取回的一則 GitHub 留言（§4 (a′)(b′) 的證據來源）。

    `author` 對應 GitHub comment 的 `user.login`（平台身分，不可由內文自述取代）；
    `body` 對應現行原文；`narrowed` 是 (b′-1) 結構化路徑的假想欄位，只在
    `spec_narrow_structured_supported` 為真時被讀取。
    """
    return {"kind": "comment", "url": ruling_url(comment_id, issue_url),
            "author": author, "body": body, "narrowed": narrowed,
            # verdict=True 表示這一則就是 checkpoint／review event 所在的留言。
            # §5 第 5 款：裁定不得指向它（自我授權）。
            "verdict": verdict}


CONSTRUCTED_RULING_ID = "9000000001"   # 構造情境的規格變更裁定留言
CONSTRUCTED_DISPATCH_ID = "9000000042"  # 構造情境的派審指示留言


def narrowing_body(finding_ids, attempt_id, *, declare=True, prose=None):
    """【構造】需求方的規格收窄裁定留言原文。

    (b′-2) 要求逐字含三者：trigger attempt 的 attempt_id、該筆 finding_id、
    以及 NARROW_TOKEN。`declare=False` 產出「有提到這些 id 但沒有宣告收窄」的
    留言——那是 R4-001 指定的第三個反例（內容未收窄）。
    """
    lines = [prose or "## 需求方裁定：本輪改窄查核範圍，明文不逐條複驗前輪處置",
             f"適用 trigger attempt：{attempt_id}",
             ("本輪 deferred_findings（引用本裁定即以下列條目為準）："
              if declare else "涉及的 finding：")]
    for fid in finding_ids:
        lines.append(f"  - finding_id: {fid}")
        if declare:
            lines.append(f"    {NARROW_TOKEN}")
    return "\n".join(lines)


def narrowing_ruling(finding_ids, attempt_id, *, comment_id=CONSTRUCTED_RULING_ID,
                     author=None, declare=True, structured=False, prose=None):
    """【構造】把上述原文包成一則可被 adapter 取回的留言 fixture。"""
    who = author or CTX["requester"]
    return COMMENT(
        comment_id, who,
        narrowing_body(finding_ids, attempt_id, declare=declare, prose=prose),
        narrowed=({"attempt_id": attempt_id, "finding_ids": list(finding_ids),
                   "actor": who} if structured else None),
    )


def defer_entry(fid, *, by=None, reason=None, comment_id=CONSTRUCTED_RULING_ID,
                url=None, cause="spec-narrowed"):
    """預設理由逐字含 `comment_id`（§4 第 6 款），URL 預設為本卡該留言。"""
    cid = str(comment_id)
    return {
        "finding_id": fid,
        "deferred_by": by or CTX["requester"],
        "defer_reason": (reason if reason is not None
                         else f"需求方於 issuecomment-{cid} 裁定本輪改窄規格，明文不逐條複驗"),
        "defer_ruling_url": ruling_url(cid) if url is None else url,
        "defer_cause": cause,
    }


class Checkpoint:
    __slots__ = ("trigger", "count", "epoch", "cond1_rcs", "cells",
                 "overdue", "cond2", "forced", "inert_defers", "defer_audit",
                 "occ_counts", "triggering", "resolution", "resolution_audit")

    def __init__(self, trigger, count, epoch, cond1_rcs, cells, overdue, cond2,
                 inert, defer_audit, occ_counts=None, triggering=frozenset()):
        self.trigger, self.count, self.epoch = trigger, count, epoch
        self.cond1_rcs, self.cells, self.overdue, self.cond2 = cond1_rcs, cells, overdue, cond2
        self.inert_defers = inert
        self.defer_audit = defer_audit
        self.forced = bool(cond1_rcs) or cond2
        # §5 第 6 款的沿用比對面：本 checkpoint 評估時點的 occurrence 累計數，
        # 與落「仍開啟」／「未提及」格（含逾期）的 finding 集合。
        self.occ_counts = occ_counts or {}
        self.triggering = frozenset(triggering)
        self.resolution = None        # 解除本 checkpoint 的有效 escalation-resolution
        self.resolution_audit = {}    # {resolution_id: {款: bool}}

    def failed_conditions(self, fid):
        """該筆 defer 是被哪幾款打掉的（供查核者逐款對照 §4）。"""
        return [c for c, ok in self.defer_audit.get(fid, {}).items() if not ok]

    def failed_resolution_conditions(self, res_id):
        """該則 resolution 是被哪幾款打掉的（供查核者逐款對照 §5）。"""
        return [c for c, ok in self.resolution_audit.get(res_id, {}).items() if not ok]

    @property
    def forcing_signature(self):
        """§5 第 6 款「強制成因集合相同」：兩條件各自的成立情形 ＋ 條件1 的根因集合。"""
        return (frozenset(self.cond1_rcs), bool(self.cond2))


def _defer_conditions(entry, fid, carry, prev_deferred, ctx, dispatches, trigger,
                      epoch, comments, trigger_attempt_id):
    cause = entry.get("defer_cause")
    reason = (entry.get("defer_reason") or "").strip()
    url = (entry.get("defer_ruling_url") or "").strip()
    ruling_id = parse_ruling_id(url, ctx["issue_url"])
    is_omitted = cause == "instruction-omitted"
    is_narrowed = cause == "spec-narrowed"

    # §4 專節 (a)：由派審事件指認，不由 defer 自述。
    d = dispatches.get(url)
    identified = bool(d) and d["for_attempt"] == trigger and d["epoch"] == epoch

    # §4 專節 (a′)(b′)：裁定留言的 author 與內容綁定。
    # 讀不到留言（能力不存在，或該 URL 根本不對應任何留言）一律 fail-closed。
    readable = bool(ctx.get("comment_read_supported"))
    structured_ok = bool(ctx.get("spec_narrow_structured_supported"))
    c = comments.get(url) if readable else None
    st = (comments.get(url) or {}).get("narrowed") if structured_ok else None

    # (a′)：author 由平台身分取得——唯讀路徑取 comment author，結構化路徑取事件 actor。
    narrow_author = ((bool(c) and c.get("author") == ctx["requester"])
                     or (bool(st) and st.get("actor") == ctx["requester"]))
    # (b′-2)：現行 body 逐字含三者。
    bound_by_text = bool(c) and all(
        tok and tok in (c.get("body") or "")
        for tok in (trigger_attempt_id, fid, NARROW_TOKEN))
    # (b′-1)：結構化欄位逐字綁定同一 attempt 與同一 finding。
    bound_by_field = (bool(st) and st.get("attempt_id") == trigger_attempt_id
                      and fid in (st.get("finding_ids") or ()))

    return {
        "in_carry": fid in carry,
        "by_requester": bool(ctx["requester"]) and entry.get("deferred_by") == ctx["requester"],
        "not_self_interested": (entry.get("deferred_by") != ctx["owner"]
                                and entry.get("deferred_by") not in ctx["reviewers"]),
        "cause_declared": cause in DEFER_CAUSES,
        "reason_nonempty": bool(reason),
        "ruling_url_on_card": ruling_id is not None,
        "reason_cites_ruling": ruling_id is not None and ruling_id in reason,
        "omission_dispatch_identified": identified if is_omitted else True,
        # `is False` 而非 falsy：缺欄（None）與 true 一樣不成立。
        "omission_declared_false": (
            (identified and d.get("closure_reporting_requested") is False)
            if is_omitted else True),
        "cause_available": (bool(ctx.get("instruction_omitted_supported"))
                            if is_omitted else True),
        "narrow_ruling_author_is_requester": narrow_author if is_narrowed else True,
        "narrow_scope_bound": (bound_by_field or bound_by_text) if is_narrowed else True,
        "narrow_cause_available": (readable or structured_ok) if is_narrowed else True,
        "not_consecutive": fid not in prev_deferred,
    }


def _resolution_conditions(ev, cp, cps, ctx, comments, verdict_urls, used_sources,
                           resolutions, owner_check, next_owner_at_write, epoch):
    """§5 `escalation-resolution` 的七款，逐項具名。

    `next_owner_at_write` 是**初稿對照組**專用：初稿把第 3 款寫成單相的「逐字等於
    下一個 attempt 的 owner」，而裁定寫入當下下一個 attempt 尚不存在，故它在寫入
    當下恆真。修訂後改為雙相——寫入只驗非空，違反宣告時罰的是那個 attempt。
    """
    basis = ev.get("resolution_basis")
    is_fresh = basis == "fresh-ruling"
    is_carried = basis == "carried-forward"
    url = (ev.get("resolution_ruling_url") or "").strip()
    c = comments.get(url) if ctx.get("comment_read_supported") else None
    src = resolutions.get(ev.get("carried_from"))
    src_cp = cps.get(src["checkpoint_trigger"]) if src else None

    conds = {
        "checkpoint_is_escalate": bool(cp) and cp.forced,
        "trigger_matches": bool(cp) and cp.trigger == ev.get("checkpoint_trigger"),
        "epoch_matches": bool(cp) and cp.epoch == epoch,
        "one_to_one": bool(cp) and cp.resolution is None,
        "owner_declared": bool(ev.get("continued_owner")),
        "resolution_value": ev.get("resolution") in RESOLUTION_VALUES
        and basis in RESOLUTION_BASES,
        # 5：fresh-ruling 的裁定留痕。
        "resolved_by_is_requester": (ev.get("resolved_by") == ctx["requester"]
                                     if is_fresh else True),
        "ruling_url_on_card": (parse_ruling_id(url, ctx["issue_url"]) is not None
                               if is_fresh else True),
        "ruling_author_is_requester": (bool(c) and c.get("author") == ctx["requester"]
                                       if is_fresh else True),
        "ruling_binds_trigger": (
            bool(c) and bool(cp) and attempt_uid(cp.epoch, cp.trigger) in (c.get("body") or "")
            if is_fresh else True),
        # 裁定不得是 checkpoint／review event 所在的那一則——`decided_by` 寫在被
        # 裁定的文本自己裡面不構成裁定留痕。
        "ruling_is_standalone": (url not in verdict_urls if is_fresh else True),
        # 6：carried-forward 的沿用款。
        "carried_from_is_fresh": (bool(src) and src.get("resolution_basis") == "fresh-ruling"
                                  if is_carried else True),
        "carried_source_unused": (bool(src) and ev.get("carried_from") not in used_sources
                                  if is_carried else True),
        "carried_by_recorded": (bool(ev.get("carried_by")) if is_carried else True),
        "carry_forcing_set_identical": (
            bool(src_cp) and bool(cp) and src_cp.forcing_signature == cp.forcing_signature
            if is_carried else True),
        "carry_no_new_occurrence": (
            bool(src_cp) and bool(cp)
            and all(src_cp.occ_counts.get(rc) == cp.occ_counts.get(rc)
                    for rc in cp.cond1_rcs)
            if is_carried else True),
        "carry_cond2_subset": (
            bool(src_cp) and bool(cp) and cp.triggering <= src_cp.triggering
            if is_carried else True),
        "auth_binding_derived": derive_authorization_binding(ctx) in (
            "substantive", "structurally-vacuous"),
    }
    if owner_check == "draft-single-phase":
        # 初稿：把第 3 款寫成「逐字等於下一個 attempt 的 owner」，於寫入當下求值。
        conds["owner_declared"] = (
            next_owner_at_write is None
            or next_owner_at_write == ev.get("continued_owner"))
    return conds


def replay(events, *, defeasible_cond1=True, allow_defer=True, ctx=None,
           owner_check="two-phase"):
    """走一遍事件流，回傳 {trigger_label: Checkpoint} 與結構性問題清單。

    `owner_check` 只影響 §5 第 3 款的求值時點：`two-phase` 為修訂後條文，
    `draft-single-phase` 重現初稿（E3 的對照組）。
    """
    ctx = ctx or CTX
    state: dict[str, dict] = {}
    rc_of: dict[str, str] = {}
    epoch_of: dict[str, int] = {}
    occurrences: dict[tuple[int, str], set[str]] = {}
    snapshot: dict[str, set[str]] = {}
    mentioned: dict[str, set[str]] = {}
    dispatches: dict[str, dict] = {}
    comments: dict[str, dict] = {}
    attempt_ids: dict[str, str] = {}
    structural: list[str] = []

    epoch = 0
    counted: list[str] = []
    prev_deferred: list[str] = []
    last_label: str | None = None
    cps: dict[str, Checkpoint] = {}
    pending_cp = 0  # 本 epoch 尚欠幾個 checkpoint
    resolutions: dict[str, dict] = {}   # {resolution_id: event}
    used_sources: set[str] = set()      # 已被援用過的 fresh-ruling
    verdict_urls: set[str] = set()      # checkpoint／review event 所在的留言
    declared_owner: str | None = None   # §5 第 3 款第二相：本 epoch 的現行 owner 宣告

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
            attempt_ids[label] = attempt_uid(epoch, label)
            # §5 第 3 款第二相：有效裁定宣告 owner 後，本 epoch 後續 attempt 的 owner
            # 必須逐字相符；不等即**該 attempt** fail-closed（換人須先走
            # escalation-epoch-change 的 change-executor）。刻意不反過來追溯使該
            # resolution 無效——append-only 事件流不得因後來的事件回改既有判定。
            if (owner_check == "two-phase" and declared_owner is not None
                    and ev.get("owner") is not None and ev["owner"] != declared_owner):
                structural.append(
                    f"{label}: owner {ev['owner']!r} 違反 escalation-resolution 的宣告 "
                    f"{declared_owner!r}（§5 第 3 款第二相，該 attempt fail-closed）")
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

        elif kind == "dispatch":
            if ev["url"] in dispatches:
                structural.append(f"dispatch: review_prompt_url 重複 {ev['url']}")
            dispatches[ev["url"]] = {
                "for_attempt": ev["for_attempt"], "epoch": epoch,
                "closure_reporting_requested": ev["closure_reporting_requested"]}

        elif kind == "comment":
            if ev["url"] in comments:
                structural.append(f"comment: URL 重複 {ev['url']}")
            comments[ev["url"]] = {"author": ev["author"], "body": ev["body"],
                                   "narrowed": ev.get("narrowed")}
            if ev.get("verdict"):
                verdict_urls.add(ev["url"])

        elif kind == "correction":
            apply(ev["updates"], last_label)

        elif kind == "epoch":
            if pending_cp:
                structural.append(f"epoch {epoch}: 換 epoch 前尚欠 {pending_cp} 個 checkpoint")
            epoch += 1
            counted = []
            prev_deferred = []
            pending_cp = 0
            # 舊 epoch 的裁定不延續到新 epoch（§4 末段：新 epoch 從零計數）。
            declared_owner = None

        elif kind == "checkpoint":
            if len(counted) < 3:
                structural.append(f"checkpoint 建立於第 {len(counted)} 個可計數 attempt（<3）")
                continue
            trigger = counted[-1]
            carry = snapshot[counted[-2]]
            entries = {e["finding_id"]: e for e in ev["deferred"]} if allow_defer else {}

            cells: dict[str, str] = {}
            audit: dict[str, dict] = {}
            for fid in sorted(carry):
                entry = entries.get(fid)
                ok = False
                if entry is not None:
                    conds = _defer_conditions(entry, fid, carry, prev_deferred, ctx,
                                              dispatches, trigger, epoch, comments,
                                              attempt_ids[trigger])
                    audit[fid] = conds
                    ok = all(conds.values())
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

            occ_counts = {rc: len(labs & seen)
                          for (e, rc), labs in occurrences.items() if e == epoch}
            triggering = frozenset(
                [f for f, c in cells.items() if c in TRIGGERING] + list(overdue))
            cps[trigger] = Checkpoint(trigger, len(counted), epoch,
                                      cond1, cells, overdue, cond2, inert, audit,
                                      occ_counts, triggering)
            prev_deferred = [f for f, c in cells.items() if c == "deferred"]
            pending_cp = max(0, pending_cp - 1)

        elif kind == "resolution":
            cp = cps.get(ev.get("checkpoint_trigger"))
            # 初稿對照組：第 3 款於寫入當下對「下一個 attempt」求值。裁定寫入時它
            # 尚不存在，故 next_owner_at_write 為 None，該款恆真——這正是要證明的。
            nxt = None
            conds = _resolution_conditions(
                ev, cp, cps, ctx, comments, verdict_urls, used_sources,
                resolutions, owner_check, nxt, epoch)
            resolutions[ev["id"]] = ev
            if cp is not None:
                cp.resolution_audit[ev["id"]] = conds
            if all(conds.values()):
                cp.resolution = dict(
                    ev, authorization_binding=derive_authorization_binding(ctx))
                declared_owner = ev["continued_owner"]
                if ev.get("resolution_basis") == "carried-forward":
                    used_sources.add(ev["carried_from"])

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
        for fid in sorted(cp.defer_audit):
            bad = cp.failed_conditions(fid)
            if bad:
                print(f"    defer {fid} 被打掉的款 : {bad}")
        print(f"    條件2               : {'TRUE' if cp.cond2 else 'false'}")
        print(f"    => 強制為: {'escalate' if cp.forced else '不強制（continue/replan 皆合法）'}")


# ==========================================================================
# C. #16 忠實回放（legacy；不做任何 id 正規化）
# ==========================================================================

# 5248665281（需求方 R4 裁定）逐字：deferred 只有兩筆。
# `defer_ruling_url` 依 §4 第 5 款指向**規格變更裁定本身**＝ 5248549305（R3 收窄），
# 理由逐字含該 id（第 6 款）。5248665281 是宣告 deferred 的那一則，不是被指向的事實。
SPEC_NARROW_RULING_ID = "5248549305"
_R3_REASON = (f"R3 依需求方於 issuecomment-{SPEC_NARROW_RULING_ID} 的裁定改為窄規格，"
              "明文不逐條複驗")
DEFER_AT_C_R3 = [
    defer_entry("R2-001", reason=_R3_REASON, comment_id=SPEC_NARROW_RULING_ID),
    defer_entry("R2-002", reason=_R3_REASON, comment_id=SPEC_NARROW_RULING_ID),
]

# 5248549305 的 fixture。本腳本不連網，只建模該留言**可機械檢查的兩個性質**：
#   author  = ruan6047（需求方本人）→ §4 (a′) 成立；
#   body    不含 attempt_id／finding_id／NARROW_TOKEN 綁定 → §4 (b′) 不成立。
# 這不是猜測：cutover 前的裁定沒有理由帶這些欄位。原文可自行取回核對：
#   gh api repos/ruan6047/ai-workflow/issues/comments/5248549305 -q .body
LEGACY_R3_RULING = COMMENT(
    SPEC_NARROW_RULING_ID, "ruan6047",
    "【fixture】cutover 前的需求方裁定：改窄本輪查核範圍。原文不含 attempt_id、"
    "finding_id 或 defer_cause 綁定（該契約當時尚不存在）。",
)

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
    LEGACY_R3_RULING,
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
        narrowing_ruling(["F_DEF"], attempt_uid(0, "A3")),
        CP(deferred=[defer_entry("F_DEF")]),
    ]


_AUTO = object()


def defer_stream(defer_ids, *, cause="spec-narrowed", by=None, drop_field=None,
                 dispatch=None, ruling=_AUTO, **entry_kw):
    """【構造】三項 carry 全部合法 deferred → 不強制；少一筆即強制。

    `dispatch` 為選填的派審事件（§4 專節 (a)(b) 的證據）；不給即等同「事件流上
    沒有可指認的派審指示」，這正是本 repo 現況。

    `ruling` 為選填的裁定留言 fixture（§4 專節 (a′)(b′) 的證據）。預設 `_AUTO`：
    `spec-narrowed` 自動附一則**合法**裁定（需求方所寫、逐字綁定 trigger attempt
    與這幾筆 finding），使既有的正例仍然成立；傳 None 即等同「事件流上沒有可讀到
    的裁定留言」。
    """
    entries = []
    for fid in defer_ids:
        e = defer_entry(fid, by=by, cause=cause, **entry_kw)
        if drop_field:
            e[drop_field] = ""
        entries.append(e)
    if ruling is _AUTO:
        ruling = (narrowing_ruling(defer_ids, attempt_uid(0, "B3"))
                  if cause == "spec-narrowed" else None)
    return [
        A("B0", new={"B0-001": ("rc-b0", {})}),
        A("B1", new={"B-001": ("rc-b1", {}), "B-002": ("rc-b2", {}), "B-003": ("rc-b3", {})},
          updates={"B0-001": {"status": "resolved"}}),
        *([dispatch] if dispatch else []),
        *([ruling] if ruling else []),
        A("B3", new={"B3-001": ("rc-b5", {})}),
        CP(deferred=entries),
    ]


def omitted_stream(*, dispatch=True, closure_requested=False, for_attempt="B3",
                   url=None, reason=None, ids=("B-001", "B-002", "B-003")):
    """【構造】`instruction-omitted` 的證據軸：派審事件在／不在、是否宣告缺漏、
    是否指向本輪、URL／理由是否與該則留痕綁定。"""
    dsp = DISPATCH(for_attempt, CONSTRUCTED_DISPATCH_ID,
                   closure_reporting_requested=closure_requested) if dispatch else None
    return defer_stream(list(ids), cause="instruction-omitted", dispatch=dsp,
                        comment_id=CONSTRUCTED_DISPATCH_ID, url=url, reason=reason)


def narrowed_stream(*, ruling=_AUTO, ids=("B-001", "B-002", "B-003")):
    """【構造】`spec-narrowed` 的裁定證據軸：裁定留言在／不在、author 是誰、
    內容有沒有把收窄綁定到本輪與本筆。"""
    return defer_stream(list(ids), cause="spec-narrowed", ruling=ruling)


def arbitrary_card_comment(ids):
    """R4-001 反例 1：**任意本卡留言**。

    需求方本人寫的、與本輪無關的一則留言（例如跨卡對帳筆記）。前一版只要 URL 形狀
    對、理由含同一數字 id 就成立；(b′) 之後它不再成立。
    """
    return COMMENT(CONSTRUCTED_RULING_ID, CTX["requester"],
                   "## PM：五張卡同時送審前的跨卡對帳\n（與本輪查核範圍無關的一則留言）")


def non_requester_ruling(ids):
    """R4-001 反例 2：**非需求方留言**——內容完全合規，但 author 是執行者本人。"""
    return narrowing_ruling(ids, attempt_uid(0, "B3"), author=CTX["owner"])


def unnarrowed_ruling(ids):
    """R4-001 反例 3：**內容未收窄**——需求方所寫、也提到本輪 attempt 與這幾筆
    finding，但沒有宣告收窄（缺 NARROW_TOKEN）。例如「這幾筆請這輪一併修掉」。"""
    return narrowing_ruling(ids, attempt_uid(0, "B3"), declare=False,
                            prose="## 需求方：本輪請把下列 finding 一併修掉")


def stale_round_ruling(ids):
    """反例 4：需求方確實收窄過，但綁定的是**前一輪**的 attempt_id（免時鐘新鮮性）。"""
    return narrowing_ruling(ids, attempt_uid(0, "B1"))


def reviewer_probe_r3_001():
    """R3-001 的隔離探針，逐字重建查核者所用的輸入：

        defer_stream(..., cause="instruction-omitted") ＋ 預設 defer_reason「規格收窄」
        ＋ 假 URL https://example/ruling

    上一輪此輸入得 forced=False、三筆全 deferred；本輪必須全部落「未提及」。
    """
    return defer_stream(["B-001", "B-002", "B-003"], cause="instruction-omitted",
                        reason="規格收窄", url="https://example/ruling")


REPAY_SECOND_RULING_ID = "9000000003"   # C′ 的裁定留言（構造）


def repay_stream(second_cp_deferred, *, settle):
    """【構造】清償上限：C 宣告 defer，C′ 必須逐項表態，否則逾期。

    兩個 checkpoint 各附一則**合法**裁定留言，使「連續 defer」的失效只可能來自
    `not_consecutive` 一款，不會被 (a′)(b′) 順帶打掉而失去鑑別力。
    """
    updates = {"C-001": {"status": "resolved"}} if settle else {}
    return [
        A("C1", new={"C-001": ("rc-c1", {}), "C-002": ("rc-c2", {})}),
        A("C2", new={"C2-001": ("rc-c2b", {})}),
        A("C3", new={"C3-001": ("rc-c3", {})},
          updates={"C-002": {"status": "resolved"}, "C2-001": {"status": "resolved"}}),
        narrowing_ruling(["C-001"], attempt_uid(0, "C3")),
        CP(deferred=[defer_entry("C-001")]),
        A("C4", new={"C4-001": ("rc-c4", {})}, updates={**updates,
                                                        "C3-001": {"status": "resolved"}}),
        narrowing_ruling(["C-001"], attempt_uid(0, "C4"),
                         comment_id=REPAY_SECOND_RULING_ID),
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
        # 兩筆都附**合法**裁定，確保結論來自優先序而不是 defer 本身不成立。
        narrowing_ruling(["E-001", "E-002"], attempt_uid(0, "E3")),
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

    §4 (a′)(b′) 加入後，最小改寫還必須連**裁定留痕的形式**一併補上：真實的
    5248549305 不含 attempt_id／finding_id／NARROW_TOKEN 綁定（見 LEGACY_R3_RULING），
    故這裡改用一則構造的合規裁定，並明示標為構造，不冒充該真實留言的內容。
    """
    ruling_id = "9000000002"
    reason = (f"R3 依需求方於 issuecomment-{ruling_id} 的裁定改為窄規格，明文不逐條複驗")
    defer = [defer_entry("R1-002", reason=reason, comment_id=ruling_id),
             defer_entry("R1-006", reason=reason, comment_id=ruling_id)]
    return [
        A("R1", new={"R1-001": ("rc-r1-001", {}), "R1-002": (RC_MARKER, {}),
                     "R1-003": ("rc-r1-003", {}), "R1-004": ("rc-r1-004", {}),
                     "R1-005": ("rc-r1-005", {}), "R1-006": (RC_PR, {})}),
        # R2：四項閉環；R1-002／R1-006 以**同一 id** 明列仍開啟（原為換號重開）。
        A("R2", updates={"R1-001": {"status": "resolved"}, "R1-003": {"status": "resolved"},
                         "R1-004": {"status": "resolved"}, "R1-005": {"status": "resolved"},
                         "R1-002": {"status": "open"}, "R1-006": {"status": "open"}}),
        A("R3", new={"R3-001": (RC_GEN, {})}),
        narrowing_ruling(["R1-002", "R1-006"], attempt_uid(0, "R3"),
                         comment_id=ruling_id),
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
# E. escalation-resolution（§4「escalate 之後的第三種結果」／§5 七款）【構造】
# ==========================================================================

E_RC = "claim-exceeds-evidence"
E_RULING_ID = "9500000001"    # 需求方的裁定留言（獨立的一則）
E_VERDICT_ID = "9500000002"   # checkpoint 本文所在的留言（§5 第 5 款禁止指向它）

# E 段用不到、因而**未被任何案例打掉**的款次，明列以免「全部條件都驗過了」的
# 過度宣稱。這些款的鑑別力在本段未被證明。
E_NOT_EXERCISED = [
    "trigger_matches／epoch_matches（本引擎以 trigger label 定址，兩者恆與 checkpoint 同源）",
    "one_to_one（同一 checkpoint 的第二則 resolution —— 未涵蓋）",
    "resolution_value（列舉外的取值 —— 未涵蓋）",
    "carried_source_unused（同一 fresh-ruling 被兩則沿用 —— 未涵蓋）",
    "carried_by_recorded（缺 carried_by —— 未涵蓋）",
    "auth_binding_derived（導出值恆在列舉內，本段以 E6 直接驗導出函式）",
]


def e_ruling_body(trigger_label, *, epoch=0, bind=True):
    """【構造】需求方的裁定留言原文。

    §5 第 5 款要求現行 body 逐字含 trigger attempt 的 attempt_id——其中含本輪
    source SHA，故任何早於該 commit 的留言都不可能覆蓋本輪（免時鐘新鮮性）。
    `bind=False` 產出「有裁定語意但未綁定本輪」的留言，即該款的反例。
    """
    head = "需求方裁定：本輪維持同執行者，繼續下一輪修正，不換人、不切卡。"
    if not bind:
        return head
    return f"{head}\n適用 trigger attempt：{attempt_uid(epoch, trigger_label)}"


def _e_prefix(*, ruling_author=None, bind=True):
    """R1–R3 同根因三次 → CP1 依條件1 強制 escalate → 需求方裁定留言。"""
    return [
        A("R1", new={"F1": (E_RC, {})}, owner=E_OWNER),
        A("R2", new={"F2": (E_RC, {})}, owner=E_OWNER),
        A("R3", new={"F3": (E_RC, {})}, owner=E_OWNER),
        CP(),
        # checkpoint 本文所在的留言。它**逐字含** trigger_attempt_id（§5 的 checkpoint
        # 必填欄本來就有），且 author 同為需求方帳號——故 author 與綁定兩款對它都成立。
        # 這正是 ruling_is_standalone 必須單獨存在的理由：少了它，指向 checkpoint
        # 自己就能過關，而那就是既有七則留痕「decided_by 寫在被裁定的文本裡」的形態。
        COMMENT(E_VERDICT_ID, CTX["requester"],
                "## escalation-checkpoint\n"
                f"trigger_attempt_id: {attempt_uid(0, 'R3')}\n"
                "checkpoint_decision: escalate", verdict=True),
        COMMENT(E_RULING_ID, ruling_author or CTX["requester"],
                e_ruling_body("R3", bind=bind)),
    ]


def e_base_stream(*, ruling_author=None, bind=True, next_owner=E_OWNER,
                  ruling_comment_id=E_RULING_ID, drop=(), resolved_by=None):
    """E1–E3：條件成立 → escalate → 需求方 continue → 下一輪。"""
    return _e_prefix(ruling_author=ruling_author, bind=bind) + [
        RES("RES1", "R3", ruling_comment_id=ruling_comment_id, drop=drop,
            resolved_by=resolved_by),
        A("R4", owner=next_owner, counted=False),
    ]


# R4 對 carry 的三種表態，只差一處，用來逐款隔離 §5 第 6 款的三項比對。
_E_R4_UPDATES = {
    # 事實未變：F3 修好，F1／F2 明列仍開啟 → 觸發集合不變、無新 occurrence。
    "same": ({"F1": {"status": "open"}, "F2": {"status": "open"},
              "F3": {"status": "resolved"}}, {}),
    # 同家族再出現一次 → occurrence 由 3 變 4。
    "new-occurrence": ({"F1": {"status": "open"}, "F2": {"status": "open"},
                        "F3": {"status": "resolved"}}, {"F4": (E_RC, {})}),
    # F3 未被表態 → 觸發集合由 {F1,F2} 長成 {F1,F2,F3}，不再是子集。
    "cond2-grew": ({"F1": {"status": "open"}, "F2": {"status": "open"}}, {}),
}


def e_carry_stream(variant, *, extend_consecutive=False):
    """E4／E5：沿用（carried-forward）。"""
    updates, new = _E_R4_UPDATES[variant]
    ev = _e_prefix() + [
        RES("RES1", "R3", ruling_comment_id=E_RULING_ID),
        A("R4", new=new, updates=updates, owner=E_OWNER),
        CP(),
        RES("RES2", "R4", basis="carried-forward", carried_from="RES1",
            carried_by="pm-account"),
    ]
    if extend_consecutive:
        ev += [
            A("R5", updates={"F1": {"status": "open"}, "F2": {"status": "open"}},
              owner=E_OWNER),
            CP(),
            RES("RES3", "R5", basis="carried-forward", carried_from="RES2",
                carried_by="pm-account"),
        ]
    return ev


def render_resolution(title, cps, only=None):
    print(f"\n===== {title} =====")
    for key, cp in cps.items():
        if only and key not in only:
            continue
        print(f"C@{cp.trigger}  強制={'escalate' if cp.forced else '不強制'}  "
              f"occ={cp.occ_counts}  觸發集合={set(cp.triggering) or '∅'}")
        for rid in cp.resolution_audit:
            bad = cp.failed_resolution_conditions(rid)
            print(f"    resolution {rid}: {'VALID' if not bad else 'INVALID'}"
                  + (f"  被打掉的款={bad}" if bad else ""))
        r = cp.resolution
        if cp.forced:
            print("    => 重建：" + (
                f"已解除，該輪繼續；continued_owner={r['continued_owner']!r}、"
                f"resolved_by={r['resolved_by']!r}、"
                f"authorization_binding={r['authorization_binding']}"
                if r else "🚨已升級（尚無有效裁定）"))


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
        ("C@R3：修訂後**仍**強制 escalate —— carry 四筆全部落「未提及」："
         "R1-002／R1-006 因換號重開未被處置；R2-001／R2-002 雖被 defer，但 legacy "
         "裁定不含 §4 (b′) 綁定",
         revised["R3"].forced
         and set(revised["R3"].cells.values()) == {"未提及"}),
        ("C@R3：legacy 裁定的 author 核對**通過**（確為需求方），失效的只有內容綁定"
         "—— 證明 (a′) 與 (b′) 各自獨立，不是靠一個粗糙的總開關",
         revised["R3"].failed_conditions("R2-001") == ["narrow_scope_bound"]
         and revised["R3"].failed_conditions("R2-002") == ["narrow_scope_bound"]),
        ("C@R3 的 deferred 集合逐字等於 5248665281 的兩筆，未被補造",
         [e["finding_id"] for e in DEFER_AT_C_R3] == ["R2-001", "R2-002"]),
        ("C@R4：C@R3 無任何生效的 defer，故無清償對象；R4 逐項閉環後不強制",
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
    off_card, _ = replay(defer_stream(all_ids, url="https://example/ruling"))
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
        ("§4 第 5 款：URL 不能解析為本卡留言時失效（含站外任意 URL），"
         "且該 URL 也取不到任何裁定留言，(a′)(b′) 一併不成立",
         off_card["B3"].forced
         and off_card["B3"].failed_conditions("B-001") == [
             "ruling_url_on_card", "reason_cites_ruling",
             "narrow_ruling_author_is_requester", "narrow_scope_bound"]),
        ("列舉外的 defer_cause 一律失效（不得自創成因）",
         bad_cause["B3"].forced and set(bad_cause["B3"].cells.values()) == {"未提及"}),
    ]

    # ---- D2：instruction-omitted 的缺漏證據（R3-001）-------------------------
    #
    # 上一輪本 cause 只驗「欄位非空」，因而機械上恆真。以下每一條都以事件層
    # 引擎跑出，並印出被打掉的款次供逐款對照 §4 專節。
    probe, _ = replay(reviewer_probe_r3_001())              # 預設 ctx ＝本 repo 現況
    ok_omit, _ = replay(omitted_stream(), ctx=CTX_SUPPORTED)
    unsupported, _ = replay(omitted_stream())               # (c) 本 cause 不可用
    no_dispatch, _ = replay(omitted_stream(dispatch=False), ctx=CTX_SUPPORTED)
    any_url, _ = replay(omitted_stream(url="https://example/ruling"), ctx=CTX_SUPPORTED)
    bare_reason, _ = replay(omitted_stream(reason="規格收窄"), ctx=CTX_SUPPORTED)
    copied_reason, _ = replay(omitted_stream(
        reason=f"需求方於 issuecomment-{CONSTRUCTED_RULING_ID} 裁定本輪改窄規格，"
               "明文不逐條複驗"), ctx=CTX_SUPPORTED)
    asked_closure, _ = replay(omitted_stream(closure_requested=True), ctx=CTX_SUPPORTED)
    wrong_round, _ = replay(omitted_stream(for_attempt="B1"), ctx=CTX_SUPPORTED)

    render("D2. R3-001 隔離探針【構造】：查核者逐字輸入（假 URL ＋「規格收窄」理由）",
           probe, only={"B3"})
    render("D2. 反例【構造】：任意 URL", any_url, only={"B3"})
    render("D2. 反例【構造】：spec-narrowed 的理由配 instruction-omitted 的 cause",
           copied_reason, only={"B3"})
    render("D2. 反例【構造】：派審指示**確實含**逐項閉環要求", asked_closure, only={"B3"})
    render("D2. 本 repo 現況【構造】：寫入通道未產出缺漏證據 → 本 cause 不可用",
           unsupported, only={"B3"})
    render("D2. 正例【構造：假想已完成 #9】：派審事件指認本輪且宣告 closure_reporting_requested=false",
           ok_omit, only={"B3"})

    def _omit_fail(cps, cond):
        cp = cps["B3"]
        return (cp.forced and set(cp.cells.values()) == {"未提及"}
                and all(cond in cp.failed_conditions(f) for f in ("B-001", "B-002", "B-003")))

    checks += [
        ("R3-001 隔離探針：查核者逐字輸入現在全部落「未提及」並強制 escalate"
         "（上一輪為 forced=False、三筆全 deferred）",
         probe["B3"].forced and set(probe["B3"].cells.values()) == {"未提及"}),
        ("R3-001 探針被打掉的款包含 URL 綁定、理由指涉與全部三款缺漏證據",
         set(probe["B3"].failed_conditions("B-001")) == {
             "ruling_url_on_card", "reason_cites_ruling",
             "omission_dispatch_identified", "omission_declared_false",
             "cause_available"}),
        ("反例 1（任意 URL）：URL 不能解析為本卡留言即失效，且無從指認派審事件",
         _omit_fail(any_url, "ruling_url_on_card")
         and _omit_fail(any_url, "omission_dispatch_identified")),
        ("反例 2a（理由只泛稱「規格收窄」）：未指涉本次留痕即失效",
         _omit_fail(bare_reason, "reason_cites_ruling")),
        ("反例 2b（整段複製 spec-narrowed 的理由、指涉另一則留言）：同樣失效",
         _omit_fail(copied_reason, "reason_cites_ruling")),
        ("反例 3（派審指示確實含逐項閉環要求）：closure_reporting_requested=true 即失效；"
         "指認成立故只掉這一款",
         _omit_fail(asked_closure, "omission_declared_false")
         and asked_closure["B3"].failed_conditions("B-001") == ["omission_declared_false"]),
        ("缺漏證據不存在（事件流無派審事件）即 fail-closed，不得預設成立",
         _omit_fail(no_dispatch, "omission_dispatch_identified")),
        ("指認須為**本輪**：派審事件屬前一輪時失效",
         _omit_fail(wrong_round, "omission_dispatch_identified")),
        ("§4 專節 (c)：寫入通道未支援時本 cause 不可用——本 repo 現況即此格",
         _omit_fail(unsupported, "cause_available")),
        ("本 cause 並非死條文：派審事件指認本輪且宣告 closure_reporting_requested=false 時成立",
         not ok_omit["B3"].forced and set(ok_omit["B3"].cells.values()) == {"deferred"}),
        ("正例的成立**只**靠結構化事實：預設 ctx（本 repo）下同一事件流仍強制 escalate",
         replay(omitted_stream())[0]["B3"].forced),
    ]

    # ---- D3：spec-narrowed 的裁定證據（R4-001）------------------------------
    #
    # 上一版本 cause 完全不讀裁定留言，取得任意本卡 comment id 即可壓掉第二條件。
    # 以下三個反例是查核者指定的，另加新鮮性與可用性兩個。
    ok_narrow, _ = replay(narrowed_stream())
    ids3 = ["B-001", "B-002", "B-003"]
    no_ruling, _ = replay(narrowed_stream(ruling=None))
    arbitrary, _ = replay(narrowed_stream(ruling=arbitrary_card_comment(ids3)))
    non_requester, _ = replay(narrowed_stream(ruling=non_requester_ruling(ids3)))
    unnarrowed, _ = replay(narrowed_stream(ruling=unnarrowed_ruling(ids3)))
    stale, _ = replay(narrowed_stream(ruling=stale_round_ruling(ids3)))
    no_read, _ = replay(narrowed_stream(), ctx=CTX_NO_READ)
    structured, _ = replay(
        defer_stream(ids3, ruling=narrowing_ruling(
            ids3, attempt_uid(0, "B3"), declare=False, structured=True,
            prose="## 需求方裁定（內容承載於結構化欄位，body 不含綁定字串）")),
        ctx=CTX_STRUCTURED)

    render("D3. 正例【構造】：需求方所寫、逐字綁定本輪 attempt 與本筆 finding",
           ok_narrow, only={"B3"})
    render("D3. 反例 1【構造】：任意本卡留言（需求方寫的，但與本輪無關）",
           arbitrary, only={"B3"})
    render("D3. 反例 2【構造】：非需求方留言（內容合規，author 是執行者）",
           non_requester, only={"B3"})
    render("D3. 反例 3【構造】：內容未收窄（提到了 id，但沒有宣告收窄）",
           unnarrowed, only={"B3"})
    render("D3. 反例 4【構造】：裁定綁定的是前一輪的 attempt_id", stale, only={"B3"})
    render("D3. 反例 5【構造】：adapter 讀不到 author／body → 本 cause 不可用",
           no_read, only={"B3"})

    def _narrow_fail(cps, conds):
        """三筆全落「未提及」、強制 escalate，且失效款次逐字等於 conds。"""
        cp = cps["B3"]
        return (cp.forced and set(cp.cells.values()) == {"未提及"}
                and all(cp.failed_conditions(f) == list(conds) for f in ids3))

    checks += [
        ("D3 正例：需求方所寫且逐字綁定本輪 attempt＋本筆 finding＋收窄宣告時成立",
         not ok_narrow["B3"].forced
         and set(ok_narrow["B3"].cells.values()) == {"deferred"}),
        ("反例 1（任意本卡留言）：URL 形狀合格、理由含同一數字 id，仍因內容未綁定"
         "而全部落「未提及」並強制 escalate —— 這正是 R4-001 的攻擊路徑",
         _narrow_fail(arbitrary, ["narrow_scope_bound"])),
        ("反例 2（非需求方留言）：內容合規但 author 是 owner，(a′) 單獨即打掉該筆",
         _narrow_fail(non_requester, ["narrow_ruling_author_is_requester"])),
        ("反例 3（內容未收窄）：author 是需求方、也提到本輪 attempt 與這幾筆 finding，"
         "但缺收窄宣告 → 失效",
         _narrow_fail(unnarrowed, ["narrow_scope_bound"])),
        ("反例 4（綁定前一輪）：舊裁定無法被搬來掩護本輪（免時鐘的新鮮性）",
         _narrow_fail(stale, ["narrow_scope_bound"])),
        ("反例 5（無讀取能力）：(c′) 本 cause 不可用，且 (a′)(b′) 一併 fail-closed，"
         "adapter 不得以「讀不到」改判成立",
         _narrow_fail(no_read, ["narrow_ruling_author_is_requester",
                                "narrow_scope_bound", "narrow_cause_available"])),
        ("事件流上根本沒有可讀到的裁定留言時 fail-closed",
         _narrow_fail(no_ruling, ["narrow_ruling_author_is_requester",
                                  "narrow_scope_bound"])),
        ("(b′-1) 結構化路徑【構造：假想 schema 已由 handoff-contract.md 定義】："
         "body 不含綁定字串，但事件欄位綁定同一 attempt 與同一 finding 時成立",
         not structured["B3"].forced
         and set(structured["B3"].cells.values()) == {"deferred"}),
        ("同一結構化事件流在**預設** ctx（schema 未定義）下仍強制 escalate —— "
         "(b′-1) 不是免費出口",
         replay(defer_stream(ids3, ruling=narrowing_ruling(
             ids3, attempt_uid(0, "B3"), declare=False, structured=True)))[0]["B3"].forced),
    ]

    settled, _ = replay(repay_stream([], settle=True))
    silent, _ = replay(repay_stream([], settle=False))
    redefer, _ = replay(repay_stream(
        [defer_entry("C-001", comment_id=REPAY_SECOND_RULING_ID,
                     reason=f"需求方於 issuecomment-{REPAY_SECOND_RULING_ID} 再次裁定收窄")],
        settle=False))
    render("D. 清償【構造】：C′ 給出 resolved", settled, only={"C4"})
    render("D. 逾期【構造】：C′ 對 deferred 集合保持沉默", silent, only={"C4"})
    render("D. 連續 defer【構造】：C′ 對同一筆再 defer 一次", redefer, only={"C4"})
    checks += [
        ("清償：C′ 明列 resolved 即無逾期、不強制",
         not settled["C4"].overdue and not settled["C4"].forced),
        ("逾期：C′ 沉默即列入逾期並強制 escalate",
         silent["C4"].overdue == ["C-001"] and silent["C4"].forced),
        ("不得連續 defer：C′ 再 defer 同一筆判為無效、落「未提及」且列入逾期。"
         "C′ 另附一則合法裁定，故失效款次逐字只有 not_consecutive",
         redefer["C4"].cells["C-001"] == "未提及"
         and redefer["C4"].overdue == ["C-001"] and redefer["C4"].forced
         and redefer["C4"].failed_conditions("C-001") == ["not_consecutive"]),
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

    # ---- E：escalation-resolution ------------------------------------------
    e_ok, e_st = replay(e_base_stream(), ctx=CTX_E)
    render_resolution("E1. 正例：escalate → 需求方 continue → 下一輪【構造】",
                      e_ok, only={"R3"})
    r1 = e_ok["R3"].resolution
    checks += [
        ("E1：checkpoint 依條件1 強制 escalate，且該 escalate 被一則有效 "
         "escalation-resolution 解除",
         e_ok["R3"].forced and r1 is not None and not e_st),
        ("E1：僅憑事件流可重建『該輪維持同執行者』——continued_owner 為正面記錄的欄位，"
         "不由「沒有交接事件」反推",
         bool(r1) and r1["continued_owner"] == E_OWNER),
        ("E1：僅憑事件流可重建『是誰決定的』",
         bool(r1) and r1["resolved_by"] == CTX_E["requester"]),
        ("E1：authorization_binding 由 adapter 導出，且在本 repo 參數下如實記為 "
         "structurally-vacuous（不讓恆真偽裝成通過）",
         bool(r1) and r1["authorization_binding"] == "structurally-vacuous"),
    ]

    # E2：continued_owner 是表示法的必要成分
    e_noowner, _ = replay(e_base_stream(drop=("continued_owner",)), ctx=CTX_E)
    render_resolution("E2. 反例：拿掉 continued_owner【構造】", e_noowner, only={"R3"})
    checks += [
        ("E2：拿掉 continued_owner → 該則裁定無效，且失效的恰為 owner_declared 一款",
         e_noowner["R3"].failed_resolution_conditions("RES1") == ["owner_declared"]),
        ("E2：裁定無效時升級狀態維持，重建不出「維持同執行者」"
         "——證明該欄是表示法的必要成分，不是裝飾",
         e_noowner["R3"].forced and e_noowner["R3"].resolution is None),
    ]

    # E3：owner 雙相檢查，與**初稿**對照
    e_two, st_two = replay(e_base_stream(next_owner="另一個執行者"),
                           ctx=CTX_E, owner_check="two-phase")
    e_draft, st_draft = replay(e_base_stream(next_owner="另一個執行者"),
                               ctx=CTX_E, owner_check="draft-single-phase")
    _, st_two_ok = replay(e_base_stream(), ctx=CTX_E, owner_check="two-phase")
    print("\n===== E3. owner 雙相檢查 vs 初稿單相【構造】=====")
    print(f"  修訂後（two-phase）      structural：{st_two or '—'}")
    print(f"  初稿（draft-single-phase）structural：{st_draft or '—'}")
    checks += [
        ("E3：修訂後——違反 owner 宣告的那個 attempt fail-closed",
         len(st_two) == 1 and "違反 escalation-resolution 的宣告" in st_two[0]),
        ("E3：修訂後——裁定本身仍有效，不因後來的 attempt 回改既有判定（append-only）",
         e_two["R3"].resolution is not None
         and not e_two["R3"].failed_resolution_conditions("RES1")),
        ("E3：**初稿對照組**——單相寫法在裁定寫入當下恆真（下一個 attempt 尚不存在），"
         "同一條違規事件流完全不被擋；這證明雙相修正確實裝上了守衛，而不只是把結論寫下來",
         not st_draft and e_draft["R3"].resolution is not None),
        ("E3：對照組——owner 與宣告一致時不 fail-closed（守衛不誤傷）", not st_two_ok),
    ]

    # E4：fresh-ruling 的裁定留痕三款（今天確實會擋下東西的部分）
    e_author, _ = replay(e_base_stream(ruling_author="someone-else"), ctx=CTX_E)
    e_bind, _ = replay(e_base_stream(bind=False), ctx=CTX_E)
    e_self, _ = replay(e_base_stream(ruling_comment_id=E_VERDICT_ID), ctx=CTX_E)
    render_resolution("E4. 反例：裁定留痕不成立【構造】", e_self, only={"R3"})
    checks += [
        ("E4：裁定留言 author 非需求方 → 無效（平台身分，非內文自述）",
         e_author["R3"].failed_resolution_conditions("RES1")
         == ["ruling_author_is_requester"]),
        ("E4：裁定留言未逐字含本輪 trigger attempt_id → 無效（免時鐘新鮮性："
         "早於本輪 commit 的留言不可能含它）",
         e_bind["R3"].failed_resolution_conditions("RES1") == ["ruling_binds_trigger"]),
        ("E4：指向 checkpoint 本文所在的那一則留言 → 無效"
         "（decided_by 寫在被裁定的文本自己裡面不構成裁定留痕）",
         e_self["R3"].failed_resolution_conditions("RES1") == ["ruling_is_standalone"]),
    ]

    # E5：沿用的三項事實比對，逐款隔離
    e_same, st_same = replay(e_carry_stream("same"), ctx=CTX_E)
    e_occ, _ = replay(e_carry_stream("new-occurrence"), ctx=CTX_E)
    e_grew, _ = replay(e_carry_stream("cond2-grew"), ctx=CTX_E)
    render_resolution("E5. 沿用（carried-forward）【構造】", e_same, only={"R3", "R4"})
    r2 = e_same["R4"].resolution
    checks += [
        ("E5：事實未變 → 沿用有效，且二手事實不被寫成一手"
         "（carried_by 記寫入者、resolved_by 維持原裁定者）",
         bool(r2) and not st_same and r2["carried_by"] == "pm-account"
         and r2["resolved_by"] == CTX_E["requester"]),
        ("E5：同家族再出現一次 → 沿用無效，失效的恰為 occurrence 累計數一款",
         e_occ["R4"].failed_resolution_conditions("RES2") == ["carry_no_new_occurrence"]),
        ("E5：第二條件觸發集合長大 → 沿用無效，失效的恰為子集一款"
         "（occurrence 未變，故兩款確實各自獨立）",
         e_grew["R4"].failed_resolution_conditions("RES2") == ["carry_cond2_subset"]),
        ("E5：沿用無效時升級狀態維持，須另發 fresh-ruling",
         e_occ["R4"].forced and e_occ["R4"].resolution is None
         and e_grew["R4"].forced and e_grew["R4"].resolution is None),
    ]

    # E6：連續沿用被拒
    e_cons, _ = replay(e_carry_stream("same", extend_consecutive=True), ctx=CTX_E)
    render_resolution("E6. 連續沿用被拒【構造】", e_cons, only={"R5"})
    checks += [
        ("E6：連續沿用 → 無效，carried_from 只能指向 fresh-ruling"
         "（與「不得連續 defer」同型：連兩輪需求方沒有真正表態即須介入）",
         e_cons["R5"].failed_resolution_conditions("RES3") == ["carried_from_is_fresh"]),
        ("E6：第一次沿用仍有效——上限是「至多一次」，不是「不得沿用」",
         e_cons["R4"].resolution is not None),
    ]

    # E7：authorization_binding 三態與其失效條件
    print("\n===== E7. authorization_binding 三態【構造】=====")
    for name, c in (("本 repo 現況（CTX_E）", CTX_E),
                    ("需求方帳號脫離 writer 集合＋執行者為平台帳號", CTX_SEPARATED),
                    ("需求方分離但執行者仍是自由文字",
                     ctx_with(requester="requester-acct", writer_accounts=("pm-bot",),
                              owner=E_OWNER, reviewers=(E_REVIEWER,)))):
        print(f"  {name} → {derive_authorization_binding(c)}")
    checks += [
        ("E7：本 repo 參數下恆為 structurally-vacuous"
         "（需求方帳號同屬被授權 writer 集合，且執行者／查核者不是平台帳號）",
         derive_authorization_binding(CTX_E) == "structurally-vacuous"),
        ("E7：需求方帳號脫離 writer 集合且執行者／查核者為平台帳號 → substantive"
         "（失效條件之一，本款何時開始有鑑別力）",
         derive_authorization_binding(CTX_SEPARATED) == "substantive"),
        ("E7：只做到帳號分離、執行者仍是自由文字 → 仍 structurally-vacuous"
         "（兩個失效條件缺一不可）",
         derive_authorization_binding(
             ctx_with(requester="requester-acct", writer_accounts=("pm-bot",),
                      owner=E_OWNER, reviewers=(E_REVIEWER,))) == "structurally-vacuous"),
    ]
    print("\n  E 段**未**打掉的款次（其鑑別力在本段未被證明）：")
    for item in E_NOT_EXERCISED:
        print(f"    - {item}")

    # ---- 結論摘要 ----------------------------------------------------------
    print("\n===== 結論摘要（供查核者對照卡面驗證條文）=====")
    print("  1. #16 的**忠實**事件流在修訂後條文下 C@R3 仍強制 escalate，且有兩個各自獨立")
    print("     的原因：(i) 需求方實際只 defer 了兩筆（5248665281），而 carry set 有四筆——")
    print("     R1-002／R1-006 在 R2 被換號為 R2-001／R2-002 重新提出，依 §4「六格的前提是")
    print("     穩定 finding_id」不構成處置；(ii) 被 defer 的那兩筆，其 legacy 裁定留言")
    print("     （5248549305）不含 §4 (b′) 要求的 attempt_id／finding_id／收窄宣告綁定，故")
    print("     defer 本身也不成立。腳本**不**補造第三、四筆 defer，也不替 legacy 留言補造內容。")
    print("  2. 同理，#16 忠實流在 C@R8 的條件1 仍為 TRUE：R4-001 自 R5 起被換號為 R5-001，")
    print("     從未被任何一輪處置，故該根因始終有有效 open finding。這是換號重開的後果，")
    print("     不是存活判準失效。")
    print("  3. 卡面兩項驗證條文（deferred 出口在 R4 前生效；條件1 在 R8 失效）成立於")
    print("     『#16 的穩定 id 最小改寫』——substance 完全相同、只把三處換號改成明列同一")
    print("     finding 仍開啟。見上方 D 段。改寫流已標示為構造，不冒充事實。")
    print("  4. #16 為 cutover 前的 legacy 事件流；依 §4／§5 末段不得反向套進六格。C 段是")
    print("     診斷性 what-if，不主張 #16 應被重新裁決。")
    print("  5. `instruction-omitted` 在**本 repo 現況下不可用**：預設 CTX 的")
    print("     instruction_omitted_supported=False 對應 handoff payload 尚無")
    print("     review_prompt_url／closure_reporting_requested、wfcli 尚無 checkpoint")
    print("     writer（#9）。D2 的正例必須明示改用 CTX_SUPPORTED 才成立，且已標為構造。")
    print("     故本卡自身的 escalation checkpoint 亦不得引用本 cause。")
    print("  6. `spec-narrowed` 的依賴不同：它只要唯讀能力（留言 author＋body），本 repo 的")
    print("     doctor --review-channel 已在讀同樣的東西，故預設 CTX 的")
    print("     comment_read_supported=True——D3 的失效全部來自「證據不成立」，不是「能力")
    print("     不存在」。但 wfcli 尚無 checkpoint writer，`escalation-checkpoint` 事件今天")
    print("     根本寫不出來，故 deferred_findings 整個機制在本 repo 尚未上線；那是 #9 的")
    print("     缺口，不是本輪收緊造成的。本卡自身的 checkpoint 兩個 cause 都不得引用。")
    print("  7. E 段的 `escalation-resolution` 讓「條件成立 → escalate → 需求方裁定維持同")
    print("     執行者」可僅憑事件流重建：`continued_owner` 是**正面記錄**的欄位，不由")
    print("     「沒有交接事件」反推（E2 證明拿掉它就重建不出來）。E3 以初稿對照組證明")
    print("     第 3 款的雙相寫法確實裝上了守衛——初稿的單相寫法在裁定寫入當下恆真，")
    print("     同一條違規事件流完全不被擋。")
    print("  8. **E 段不證明授權款有實質保證，它證明的是相反的事**：E7 斷言")
    print("     `authorization_binding` 在本 repo 參數下恆為 `structurally-vacuous`——")
    print("     需求方帳號同屬被授權 writer 集合，且執行者／查核者不是平台帳號，故 §5")
    print("     第 5 款的 author 比對分不開任何兩方。今天確實會擋下東西的是留痕側三款")
    print("     （獨立留言、逐字綁定本輪 attempt_id、沿用上限），它們分開的是留痕不是人。")
    print("     轉為 `substantive` 的兩個失效條件同樣以斷言釘住。")
    print("  9. E 段仍是**規則層**的證明：`escalation-resolution` 今天沒有任何寫入端")
    print("     實作（`wfcli` 的 checkpoint writer 即 ai-workflow#9 未完成），故本段證明")
    print("     的是「規則對結構化欄位有鑑別力」，不是「系統已經照它運作」。")

    # ---- 斷言彙總 ----------------------------------------------------------
    print("\n===== 斷言 =====")
    failed = sum(not ok for _, ok in checks)
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"\n{len(checks) - failed}/{len(checks)} 通過")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
