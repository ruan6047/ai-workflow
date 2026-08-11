"""卡片模型：Card dataclass + 範本渲染（git spec 檔骨架／Issue body／Log 行）。

架構切分（呼應 canonical AI_WORKFLOW.md §6「git 是程式碼／文件事實來源；adapter
event log 是作業狀態事實來源」，遷移後把「adapter event log」實作換成 GitHub
Issue/Project）：

- **git spec 檔**（``tasks/<CARD_ID>.md``，寫回目標 repo 並由使用者自行 commit）：
  穩定的範圍／驗收／驗證內容，不重複會變動的 Ledger 欄位。
- **GitHub Issue／Project item**：owner／worktree／iteration／交付狀態／部署狀態／
  最後交接等會變動的 current-state，以及供機器解析的資源宣告區塊、可累積的 Log。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

from .resources import ResourceDeclaration, render_block

TIERS = ("T0", "T1", "T2", "T3", "T4")

# 能力層級語彙**不在這裡新創**：唯一權威是 repo 根目錄 ``MODEL_ROUTING.md`` 的
# 「預設能力等級」欄（第 7–10 列）。原文四列去掉修飾後恰好三級：
#
#   第 7 列「經濟型／deterministic automation」——「／deterministic automation」是
#       同一級的英文同義註解，不是第四級。
#   第 8 列「主力型」、第 10 列「主力型」——同一級。
#   第 9 列「高階型 + 跨家族 review」——「+ 跨家族 review」是**查核側的附加要求**
#       （templates/tasks-card.md 第 4 行同樣寫「紅線須跨家族或人工」），是能力層級
#       之上疊加的獨立性條件，不是第四級。
#
# 因此本枚舉照抄權威的三級，且刻意**封閉**：沒有「其他」「未定」逃生格。每個輸入
# 落在且僅落在一格——落不進去就是硬拒，不是歸進 fallback 桶。
CAPABILITY_TIERS = ("經濟型", "主力型", "高階型")

# 決議 5（鏈式停損協定，見 docs/research/WORKFLOW-REVIEW-2026-08-04.md）：
# 鏈深硬上限＝原始目標之下 2 層；超過強制整鏈重審，不得逕行加深。
CHAIN_DEPTH_HARD_CAP = 2

_BRANCH_WORKTREE_RE = re.compile(r"^\s*(?P<branch>\S+)\s*@\s*(?P<path>.+?)\s*$")


def chain_depth_violation_message(chain_depth: int) -> str:
    """決議 5 鏈式停損協定的拒絕訊息；CLI 層（ValidationError）與 model 層
    （Card.__post_init__ 的 ValueError）共用同一段文字，避免兩處措辭各自漂移。
    """
    return (
        f"鏈深 {chain_depth} 超過硬上限：原始目標之下最深 {CHAIN_DEPTH_HARD_CAP} 層；"
        "超過須整鏈重審，不得逕行加深——見決議 5（鏈式停損協定）"
    )


def capability_tier_violation_message(axis: str, value: str) -> str:
    """能力層級不在權威語彙內時的拒絕訊息；CLI 層與 model 層共用同一段文字。

    刻意在訊息裡點名「這不是 T0–T4」：``--tier``／``級別`` 是**風險級別**（另一條
    軸），兩者都叫「tier／層級」，是本卡要消除的命名碰撞的主要誤用來源。
    """
    return (
        f"{axis}能力層級必須是 {CAPABILITY_TIERS} 之一，收到 {value!r}"
        "——語彙出自 MODEL_ROUTING.md「預設能力等級」欄，不得自創；"
        f"注意這**不是** T0–T4 風險級別（那是另一條軸，欄位名「級別」／旗標 --tier）"
    )


def capability_reason_missing_message(axis: str) -> str:
    """缺理由時的拒絕訊息。

    **硬拒而非預設＋警示**，理由寫在這裡以便被擋的人直接看到取捨：能力層級可以有
    「常見值」，但 canonical AI_WORKFLOW.md §3 Plan 要的是「建議**反映任務風險**」。
    任何預設值都是在沒有讀過這張卡的風險的情況下先填一個答案，等於把「規劃者判斷」
    降級成「CLI 猜測」——而本卡的核心痛點正是「規則寫在範本裡、產生端靜默不符」。
    預設值只會把靜默不符換成靜默填錯，痛點沒消失。
    """
    return (
        f"{axis}能力層級的理由必填，且不得為空白"
        "——canonical AI_WORKFLOW.md §3 Plan：「Plan 產出必含建議執行／查核能力層級"
        "與理由」「建議反映任務風險，不得因當下額度預先降級」。"
        "此處硬拒不設預設值：預設值等於在未讀本卡風險的前提下代替規劃者作答"
    )


def validate_capability_routing(
    *,
    executor_capability: str,
    executor_capability_reason: str,
    reviewer_capability: str,
    reviewer_capability_reason: str,
) -> None:
    """規劃期路由的機械檢查（執行／查核各一層級＋一理由）；不合格一律 ``ValueError``。

    純函式、不碰網路，故 CLI 層（``commands/open_cmd.py``）與 model 層
    （``Card.__post_init__``）呼叫同一份，兩層不會 drift 出不一致的判準。
    """
    for axis, tier, reason in (
        ("執行", executor_capability, executor_capability_reason),
        ("查核", reviewer_capability, reviewer_capability_reason),
    ):
        if tier not in CAPABILITY_TIERS:
            raise ValueError(capability_tier_violation_message(axis, tier))
        if not reason or not reason.strip():
            raise ValueError(capability_reason_missing_message(axis))


def now_iso8601() -> str:
    """寫入當下的系統時鐘，本機時區，完整 ISO-8601（含時分秒與時區）。

    對齊需求方裁決：「最後交接＝TEXT 完整 ISO-8601 單欄（字典序即時序）」——
    字典序等於時序的前提是格式固定寬度、時區固定。刻意用 ``isoformat(timespec=
    "seconds")`` 而非 ``strftime("%z")``：後者的時區產出 ``+0800``（無冒號），
    與既有事件慣例（``occurred_at": "2026-08-04T21:48:37+08:00"``）及 OPS-STATE-
    PLANE-MIG1 實測值不一致，字典序比較時每字元對齊才可靠。
    """
    dt = datetime.now().astimezone()
    return dt.isoformat(timespec="seconds")


_OWNER_PLACEHOLDER_PREFIXES = ("待指派", "待建立", "待認領", "—")


def is_owner_assigned(owner: str | None) -> bool:
    """owner 欄是否已指向真正的執行者，而非「待指派／待建立／待認領／—」佔位字串。

    assign 的資源交集檢查與 doctor 的殘留 lease 檢查共用同一套「什麼算已認領」
    判準，避免兩處各自定義漂移出不一致的行為。
    """
    if not owner:
        return False
    return not owner.strip().startswith(_OWNER_PLACEHOLDER_PREFIXES)


def format_branch_worktree(branch: str | None, worktree: str | None) -> str:
    if not branch and not worktree:
        return "—"
    return f"{branch or '—'} @ {worktree or '—'}"


def parse_branch_worktree(value: str) -> tuple[str | None, str | None]:
    """解析 Ledger 慣例的複合字串 ``branch @ path``；``—`` 或空字串回傳 (None, None)。"""
    if not value or value.strip() in {"—", ""}:
        return None, None
    match = _BRANCH_WORKTREE_RE.match(value)
    if not match:
        return None, None
    return match.group("branch"), match.group("path")


@dataclass
class Card:
    card_id: str
    feature: str
    tier: str
    db_scope: str
    core_pain: str
    service_goal: str
    resources: ResourceDeclaration
    # 規劃期路由（無預設值＝建構 Card 就必須給）。刻意不設 default：範本第 4 行把
    # 這四項列為卡面欄位，而本卡的痛點就是「產生端可以不給也不報錯」。放在
    # dataclass 的必填區，等於連繞過 CLI 直接建 Card 都無法產出不符範本的卡。
    executor_capability: str
    executor_capability_reason: str
    reviewer_capability: str
    reviewer_capability_reason: str
    initiative: str | None = None
    requested_by: str = "—"
    planned_by: str = "—"
    executor: str = "待指派"
    reviewer: str = "待指派"
    spec_baseline: str = "—"
    acceptance: list[str] = field(default_factory=lambda: ["TODO：填入可獨立驗證的條件"])
    verification: list[str] = field(default_factory=lambda: ["TODO：填入驗證指令與證據要求"])
    owner: str = "待指派"
    branch: str | None = None
    worktree: str | None = None
    iteration: int = 0
    delivery_status: str = "📥Backlog"
    deployment_status: str = "—不適用"
    last_handoff: str = field(default_factory=now_iso8601)
    chain_depth: int = 0

    def __post_init__(self) -> None:
        if self.tier not in TIERS:
            raise ValueError(f"tier 必須是 {TIERS} 之一，收到 {self.tier!r}")
        if self.resources.db_scope != self.db_scope:
            # db_scope 是資源宣告的一部分，這裡保留獨立欄位方便 CLI 參數化，
            # 但兩者必須一致，不允許卡面文字與機器可讀宣告各說各話。
            raise ValueError(
                "db_scope 與資源宣告內的 db_scope 不一致："
                f"{self.db_scope!r} vs {self.resources.db_scope!r}"
            )
        validate_capability_routing(
            executor_capability=self.executor_capability,
            executor_capability_reason=self.executor_capability_reason,
            reviewer_capability=self.reviewer_capability,
            reviewer_capability_reason=self.reviewer_capability_reason,
        )
        if self.chain_depth > CHAIN_DEPTH_HARD_CAP:
            # 與 validation.validate_chain_depth 相同的機械紅線，這裡是繞過 CLI
            # 直接建構 Card（測試／未來呼叫端）時的防線；CLI 路徑應該在到達這裡
            # 之前就已經被 validate_chain_depth 攔下並回報 ValidationError。
            raise ValueError(chain_depth_violation_message(self.chain_depth))

    @property
    def branch_worktree(self) -> str:
        return format_branch_worktree(self.branch, self.worktree)


def format_routing_line(c: Card) -> str:
    """``templates/tasks-card.md`` 第 4 行（執行／查核＋建議能力層級＋理由）。

    抽成單一函式是因為 git spec 檔與 Issue body 兩個渲染路徑都要輸出它——兩處各自
    f-string 就會 drift，而範本一致性正是本欄位存在的理由。範本原文：

        - 執行：<模型@工具／待指派>（建議 <MODEL_ROUTING 能力層級>；<能力軸理由>）
          查核：<模型@工具／待指派>（<層級；紅線須跨家族或人工>；須 ≠ 執行）

    括號內第一段填層級、第二段填理由；「紅線須跨家族或人工」「須 ≠ 執行」是範本給
    規劃者的填寫指示（規則文字），不是要逐字複製進卡面的內容，故不渲染。
    """
    return (
        f"- 執行：{c.executor}"
        f"（建議 {c.executor_capability}；{c.executor_capability_reason}）"
        f"　查核：{c.reviewer}"
        f"（建議 {c.reviewer_capability}；{c.reviewer_capability_reason}）"
    )


def render_spec_markdown(c: Card) -> str:
    """git spec 檔骨架（寫入目標 repo ``tasks/<CARD_ID>.md``）。"""
    acceptance = "\n".join(f"- [ ] {line}" for line in c.acceptance)
    verification = "\n".join(f"- [ ] {line}" for line in c.verification)
    return f"""# {c.card_id} {c.feature}　〔{c.tier}〕

- 需求：{c.requested_by}　規劃：{c.planned_by}
{format_routing_line(c)}
- Initiative：{c.initiative or '—'}　spec 基線：{c.spec_baseline}
- DB：db_scope={c.db_scope}
- 服務的原始目標：{c.service_goal}
- owner、worktree、iteration、交付／部署狀態、最後交接、資源宣告與 Log
  current-state 見對應 GitHub Issue／Project item（卡ID：{c.card_id}），不重複於此檔。

## 核心痛點

- **痛點**：{c.core_pain}

## 驗收條件

{acceptance}

## 驗證

{verification}
"""


def render_issue_body(c: Card) -> str:
    """GitHub Issue／draft item body（含資源宣告 fenced JSON 區塊與 Log 章節）。"""
    acceptance = "\n".join(f"- [ ] {line}" for line in c.acceptance)
    verification = "\n".join(f"- [ ] {line}" for line in c.verification)
    resource_block = render_block(c.resources)
    return f"""- 需求：{c.requested_by}　規劃：{c.planned_by}
{format_routing_line(c)}
- Initiative：{c.initiative or '—'}　spec 基線：{c.spec_baseline}
- DB：db_scope={c.db_scope}
- 服務的原始目標：{c.service_goal}

## 核心痛點

- **痛點**：{c.core_pain}

{resource_block}

## 驗收條件

{acceptance}

## 驗證

{verification}

## Log

- {now_iso8601()} open by {c.planned_by}；owner {c.owner}；iteration {c.iteration}。
"""


_LOG_HEADING = "## Log"


def append_log_line(body: str, line: str) -> str:
    """在 body 的 ``## Log`` 區段末端附加一行；沒有該區段就新增一個到 body 尾端。

    這是 Issue／draft item body 版的 append-only 留痕，對齊
    ``templates/tasks-card.md`` 既有 Log 慣例（不可覆寫歷史，只能加行）。
    """
    entry = f"- {line}"
    if _LOG_HEADING in body:
        return body.rstrip("\n") + f"\n{entry}\n"
    return body.rstrip("\n") + f"\n\n{_LOG_HEADING}\n\n{entry}\n"


# --------------------------------------------------------------------------
# 開卡後的卡面修訂（WF-CLI-CARD-AMEND1）
# --------------------------------------------------------------------------
#
# 這些是純函式：吃 body 字串、回傳 (新 body, 被改欄位的原值)，不碰網路。原值一律
# 回傳而非丟棄，呼叫端才有東西寫進 Log——「不得無痕覆寫」是本能力的硬要求。
#
# 所有修訂**只作用於 ``## Log`` 之前的區段**。Log 是 append-only 留痕，修訂能力
# 不為自己破例；真要動 Log 的唯一合法方式是再 append 一行。


class AmendError(ValueError):
    """卡面修訂失敗：錨點缺失／不唯一／值未變更／目標落在 Log 區段。"""


_ACCEPTANCE_HEADING = "## 驗收條件"
_VERIFICATION_HEADING = "## 驗證"
_RESOURCE_HEADING = "## 資源宣告"
_SPEC_BASELINE_RE = re.compile(r"^- Initiative：(?P<init>.*)　spec 基線：(?P<base>.*)$")
_CHECKBOX_RE = re.compile(r"^- \[(?P<state>[ xX])\] (?P<text>.*)$")


def split_at_log(body: str) -> tuple[str, str]:
    """切成「Log 之前」與「``## Log`` 起的全部」。修訂只准動前者。

    刻意 fail closed：body 出現 ``## Log`` 字樣卻不是獨立標題行時直接拒絕。實務上
    這代表排版已被破壞（例如有人把換行寫成字面 ``\\n``），此時任何依標題定位的
    區段替換都可能誤動 Log。
    """
    lines = body.splitlines()
    idx = [i for i, line in enumerate(lines) if line.strip() == _LOG_HEADING]
    if len(idx) > 1:
        raise AmendError(f"body 內有 {len(idx)} 個 `## Log` 標題，無法安全定位修訂範圍")
    if not idx:
        if _LOG_HEADING in body:
            raise AmendError(
                "body 含 `## Log` 字樣但它不是獨立標題行（排版可能已被字面 \\n 破壞）；"
                "拒絕修訂，以免區段替換誤動 Log"
            )
        return body, ""
    return "\n".join(lines[: idx[0]]), "\n".join(lines[idx[0] :])


def _join(head: str, tail: str) -> str:
    return f"{head.rstrip()}\n\n{tail.strip()}\n" if tail else f"{head.rstrip()}\n"


def _locate_section(lines: list[str], heading: str) -> tuple[int, int]:
    """回傳該章節的 [起始標題列, 下一個 ``## `` 標題列或結尾)。標題須唯一。"""
    starts = [i for i, line in enumerate(lines) if line.strip() == heading]
    if len(starts) != 1:
        raise AmendError(
            f"章節 `{heading}` 在 Log 之前出現 {len(starts)} 次，必須恰好 1 次才能安全替換"
        )
    start = starts[0]
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            return start, j
    return start, len(lines)


def _read_checklist(lines: list[str]) -> list[tuple[str, str]]:
    """讀出 ``- [ ] text`` 形式的項目，保留勾選狀態。"""
    out: list[tuple[str, str]] = []
    for line in lines:
        m = _CHECKBOX_RE.match(line.strip())
        if m:
            out.append((m.group("state"), m.group("text")))
    return out


def _amend_checklist(
    body: str, heading: str, new_items: list[str], *, preserve_checked: bool = False
) -> tuple[str, str]:
    if not new_items or any(not item.strip() for item in new_items):
        raise AmendError(f"`{heading}` 的新內容不得為空，也不得含空白項目")
    head, tail = split_at_log(body)
    lines = head.splitlines()
    start, end = _locate_section(lines, heading)
    old = _read_checklist(lines[start + 1 : end])
    old_repr = "；".join(f"[{s}] {t}" for s, t in old) or "（原本無項目）"
    # 預設一律重設為未勾選：整份替換代表驗收語意已變動，此時「文字相同」不保證
    # 「仍然成立」——相鄰條件全改時，沿用勾選會把過期的完成證據當成現況。
    # 需要沿用時由呼叫端顯式指定，責任因此可歸屬。
    prior = {t: s for s, t in old} if preserve_checked else {}
    rendered = [f"- [{prior.get(item, ' ')}] {item}" for item in new_items]
    if rendered == [line.strip() for line in lines[start + 1 : end] if line.strip()]:
        raise AmendError(f"`{heading}` 的新內容與現值相同；拒絕寫入不實的修訂留痕")
    new_lines = lines[: start + 1] + ["", *rendered, ""] + lines[end:]
    return _join("\n".join(new_lines), tail), old_repr


def amend_acceptance(
    body: str, new_items: list[str], *, preserve_checked: bool = False
) -> tuple[str, str]:
    """整份替換「驗收條件」；回傳 (新 body, 原內容含勾選狀態)。"""
    return _amend_checklist(
        body, _ACCEPTANCE_HEADING, new_items, preserve_checked=preserve_checked
    )


def amend_verification(
    body: str, new_items: list[str], *, preserve_checked: bool = False
) -> tuple[str, str]:
    """整份替換「驗證」；回傳 (新 body, 原內容含勾選狀態)。"""
    return _amend_checklist(
        body, _VERIFICATION_HEADING, new_items, preserve_checked=preserve_checked
    )


def amend_spec_baseline(body: str, new_value: str) -> tuple[str, str]:
    """改 spec 基線（它內嵌在 Initiative 那一行）；回傳 (新 body, 原值)。"""
    if not new_value.strip():
        raise AmendError("spec 基線不得為空；無基線請明確填 `—`")
    head, tail = split_at_log(body)
    lines = head.splitlines()
    hits = [i for i, line in enumerate(lines) if _SPEC_BASELINE_RE.match(line)]
    if len(hits) != 1:
        raise AmendError(
            f"`- Initiative：…　spec 基線：…` 這一行在 Log 之前命中 {len(hits)} 次，必須恰好 1 次"
        )
    match = _SPEC_BASELINE_RE.match(lines[hits[0]])
    assert match is not None
    old = match.group("base")
    if old.strip() == new_value.strip():
        raise AmendError("spec 基線與現值相同；拒絕寫入不實的修訂留痕")
    lines[hits[0]] = f"- Initiative：{match.group('init')}　spec 基線：{new_value}"
    return _join("\n".join(lines), tail), old


def amend_resource_block(body: str, rendered_block: str) -> tuple[str, str]:
    """整份替換「資源宣告」章節；``rendered_block`` 須含標題（``resources.render_block``
    的輸出即是）。回傳 (新 body, 原章節原文)。
    """
    head, tail = split_at_log(body)
    lines = head.splitlines()
    start, end = _locate_section(lines, _RESOURCE_HEADING)
    old_repr = "\n".join(lines[start:end]).strip()
    new_lines = lines[:start] + rendered_block.splitlines() + [""] + lines[end:]
    candidate = _join("\n".join(new_lines), tail)
    if candidate == _join(head, tail):
        raise AmendError("資源宣告與現值相同；拒絕寫入不實的修訂留痕")
    return candidate, " ".join(old_repr.split())


# --------------------------------------------------------------------------
# 派工端：實際能力層級 vs 卡面建議（WF-CLI-ROUTING-TIER1 R1-001）
# --------------------------------------------------------------------------
#
# ``MODEL_ROUTING.md`` 第 14 行後半：「派工時可依可用性偏離建議，但實際模型與偏離
# 理由記入 claim 事件。」開卡端負責寫下建議，這一段負責在 assign 時把「實際」與
# 「建議」對起來。
#
# **卡面建議只存在於 Issue body**：``project.FIELD_SPECS`` 的 13 個凍結欄位沒有任何
# 一個放能力層級（2026-08-11 以 ``FIELD_SPECS``／``CARD_FIELD_MAP``／``open_cmd`` 的
# values dict 三處查證），所以解析 body 第 2 行是唯一路徑。這條路徑的脆弱性必須明講，
# 不能當成隱含前提：
#
#   1. 它依賴 ``format_routing_line`` 的輸出形狀。兩者同檔且有 round-trip 測試
#      （render → parse 讀回同一層級），改渲染而忘了改解析會當場紅。
#   2. 它依賴 body 沒有被人手改壞。因此**不猜**：定位不到、不唯一、或讀出來的層級
#      不在 MODEL_ROUTING 語彙內，一律歸 ``ambiguous`` 而不是「當作沒有建議」放行。
#   3. 只看 ``## Log`` 之前的區段（``split_at_log``）。Log 會引用被 amend 掉的舊值原文，
#      其中可能含字面的「- 執行：」——不切掉就會把歷史當成現況讀。
#
# 分類是**全函數**：任一 body ＋ 任一合法實際層級，恰好落在下列四格之一，沒有「其餘」。

CAPABILITY_MATCHED = "matched"
CAPABILITY_DEVIATED = "deviated"
CAPABILITY_BASELINE_ABSENT = "absent"
CAPABILITY_BASELINE_AMBIGUOUS = "ambiguous"

CAPABILITY_COMPARISON_OUTCOMES = (
    CAPABILITY_MATCHED,
    CAPABILITY_DEVIATED,
    CAPABILITY_BASELINE_ABSENT,
    CAPABILITY_BASELINE_AMBIGUOUS,
)

# 每一格的理由政策顯式列出，不留 ``else`` 預設值：新增結果態卻忘了決定政策時，
# ``requires_reason`` 會 KeyError 當場炸，而不是靜默沿用「不需要理由」。
#
# 為什麼 absent／ambiguous 也要理由（而不是比照 matched 放行）：這兩格代表**沒有可
# 比對的基線**，不是「比對過且相符」。當作相符放行等於用沉默宣稱一致性，正是本卡要
# 消滅的失敗形態。本檔既有慣例也支持這個方向——assign 對「目標卡自己」的資源宣告
# 解析失敗是 fail closed（見 commands/assign_cmd.py docstring），路由基線同樣長在
# 目標卡自己身上。代價只是操作者多打一個 --capability-deviation-reason。
_REASON_REQUIRED_BY_OUTCOME: dict[str, bool] = {
    CAPABILITY_MATCHED: False,
    CAPABILITY_DEVIATED: True,
    CAPABILITY_BASELINE_ABSENT: True,
    CAPABILITY_BASELINE_AMBIGUOUS: True,
}

_EXECUTOR_LINE_PREFIX = "- 執行："

# 解析用；與測試裡那支「範本合規 oracle」刻意分開兩份，round-trip 測試才不是套套邏輯。
_ROUTING_PARSE_RE = re.compile(
    r"^- 執行：(?P<executor>[^（]*)（建議 (?P<exec_tier>[^；）]+)；(?P<exec_reason>[^）]*)）"
    r"　查核：(?P<reviewer>[^（]*)（建議 (?P<rev_tier>[^；）]+)；(?P<rev_reason>[^）]*)）$"
)


@dataclass(frozen=True)
class CapabilityComparison:
    """實際能力層級與卡面建議的比對結果（四格全函數之一）。"""

    outcome: str
    actual: str
    suggested: str | None  # 只有 matched／deviated 讀得到建議值
    detail: str  # absent／ambiguous 的具體原因；其餘為空字串

    @property
    def requires_reason(self) -> bool:
        return _REASON_REQUIRED_BY_OUTCOME[self.outcome]

    def refusal_message(self) -> str:
        """缺理由時的拒絕訊息；固定引用 MODEL_ROUTING.md 第 14 行後半。"""
        citation = (
            "MODEL_ROUTING.md「路由決定於規劃期」：「派工時可依可用性偏離建議，"
            "但實際模型與偏離理由記入 claim 事件」"
        )
        if self.outcome == CAPABILITY_DEVIATED:
            why = f"實際能力層級 {self.actual} 偏離卡面建議 {self.suggested}"
        elif self.outcome == CAPABILITY_BASELINE_ABSENT:
            why = f"卡面沒有可比對的建議層級（{self.detail}）"
        elif self.outcome == CAPABILITY_BASELINE_AMBIGUOUS:
            why = f"卡面建議層級無法可靠解析（{self.detail}）"
        else:  # pragma: no cover - matched 不會走到這裡（requires_reason 為 False）
            raise ValueError(f"outcome {self.outcome!r} 不需要理由，不該產生拒絕訊息")
        return (
            f"{why}，必須以 --capability-deviation-reason 說明後才可派工——{citation}。"
            "無基線時同樣要求理由：沒有比對過的一致性不得以沉默宣稱"
        )

    def log_fragment(self, reason: str) -> str:
        """寫進 assign／claim 事件 Log 的片段；四格各自措辭，不共用模糊字串。

        關鍵是**不得把「無建議」寫成「偏離建議」**——那會產生不實留痕。
        """
        reason = (reason or "").strip()
        if self.outcome == CAPABILITY_MATCHED:
            base = f"實際能力層級 {self.actual}（與卡面建議 {self.suggested} 相符"
            # 相符時理由非必填；操作者若仍寫了就照錄，不靜默丟棄其輸入。
            return base + (f"；備註：{reason}）" if reason else "）")
        if self.outcome == CAPABILITY_DEVIATED:
            return (
                f"實際能力層級 {self.actual}"
                f"（偏離卡面建議 {self.suggested}；偏離理由：{reason}）"
            )
        if self.outcome == CAPABILITY_BASELINE_ABSENT:
            return (
                f"實際能力層級 {self.actual}"
                f"（卡面無建議層級：{self.detail}；理由：{reason}）"
            )
        if self.outcome == CAPABILITY_BASELINE_AMBIGUOUS:
            return (
                f"實際能力層級 {self.actual}"
                f"（卡面建議無法解析：{self.detail}；理由：{reason}）"
            )
        raise ValueError(f"未知的比對結果 {self.outcome!r}")  # pragma: no cover


def compare_capability_to_card(body: str, actual_capability: str) -> CapabilityComparison:
    """把「實際派到的能力層級」對上「卡面第 4 行的建議執行層級」。

    只比**執行**軸：assign 寫的是 owner（執行者）。查核者的建議層級留在卡面供派查核
    時使用，本函式不碰，以免用一個旗標同時宣稱兩件事。
    """
    if actual_capability not in CAPABILITY_TIERS:
        raise ValueError(capability_tier_violation_message("實際", actual_capability))

    try:
        head, _ = split_at_log(body)
    except AmendError as exc:
        return CapabilityComparison(
            CAPABILITY_BASELINE_AMBIGUOUS,
            actual_capability,
            None,
            f"卡面排版已損壞，無法安全定位 Log 之前的區段（{exc}）",
        )

    lines = [ln.rstrip() for ln in head.splitlines() if ln.startswith(_EXECUTOR_LINE_PREFIX)]
    if not lines:
        return CapabilityComparison(
            CAPABILITY_BASELINE_ABSENT,
            actual_capability,
            None,
            "卡面沒有「- 執行：」行",
        )
    if len(lines) > 1:
        return CapabilityComparison(
            CAPABILITY_BASELINE_AMBIGUOUS,
            actual_capability,
            None,
            f"卡面有 {len(lines)} 行「- 執行：」，無法判斷哪一行是規劃期建議",
        )

    match = _ROUTING_PARSE_RE.match(lines[0])
    if not match:
        return CapabilityComparison(
            CAPABILITY_BASELINE_ABSENT,
            actual_capability,
            None,
            "「- 執行：」行是規劃期路由必填之前的舊格式，沒有（建議 <層級>；<理由>）括號段",
        )

    suggested = match.group("exec_tier").strip()
    if suggested not in CAPABILITY_TIERS:
        return CapabilityComparison(
            CAPABILITY_BASELINE_AMBIGUOUS,
            actual_capability,
            None,
            f"卡面建議層級 {suggested!r} 不在 MODEL_ROUTING.md 語彙 {CAPABILITY_TIERS} 內",
        )

    outcome = (
        CAPABILITY_MATCHED if suggested == actual_capability else CAPABILITY_DEVIATED
    )
    return CapabilityComparison(outcome, actual_capability, suggested, "")


__all__ = [
    "CAPABILITY_BASELINE_ABSENT",
    "CAPABILITY_BASELINE_AMBIGUOUS",
    "CAPABILITY_COMPARISON_OUTCOMES",
    "CAPABILITY_DEVIATED",
    "CAPABILITY_MATCHED",
    "CAPABILITY_TIERS",
    "CHAIN_DEPTH_HARD_CAP",
    "TIERS",
    "AmendError",
    "CapabilityComparison",
    "Card",
    "amend_acceptance",
    "amend_resource_block",
    "amend_spec_baseline",
    "amend_verification",
    "append_log_line",
    "capability_reason_missing_message",
    "capability_tier_violation_message",
    "chain_depth_violation_message",
    "compare_capability_to_card",
    "format_branch_worktree",
    "format_routing_line",
    "now_iso8601",
    "parse_branch_worktree",
    "render_issue_body",
    "render_spec_markdown",
    "split_at_log",
    "validate_capability_routing",
]
