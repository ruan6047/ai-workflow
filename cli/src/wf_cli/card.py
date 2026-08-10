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

from .resources import ResourceDeclaration, render_block, try_parse_block

TIERS = ("T0", "T1", "T2", "T3", "T4")

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
        if self.chain_depth > CHAIN_DEPTH_HARD_CAP:
            # 與 validation.validate_chain_depth 相同的機械紅線，這裡是繞過 CLI
            # 直接建構 Card（測試／未來呼叫端）時的防線；CLI 路徑應該在到達這裡
            # 之前就已經被 validate_chain_depth 攔下並回報 ValidationError。
            raise ValueError(chain_depth_violation_message(self.chain_depth))

    @property
    def branch_worktree(self) -> str:
        return format_branch_worktree(self.branch, self.worktree)


def render_spec_markdown(c: Card) -> str:
    """git spec 檔骨架（寫入目標 repo ``tasks/<CARD_ID>.md``）。"""
    acceptance = "\n".join(f"- [ ] {line}" for line in c.acceptance)
    verification = "\n".join(f"- [ ] {line}" for line in c.verification)
    return f"""# {c.card_id} {c.feature}　〔{c.tier}〕

- 需求：{c.requested_by}　規劃：{c.planned_by}
- 執行：{c.executor}　查核：{c.reviewer}
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
- 執行：{c.executor}　查核：{c.reviewer}
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


# 已知事故形態（ai-workflow#17，2026-08-10）：卡面 Log 標題連同其前後空行被整段
# 寫成字面跳脫。修復只認這一個精確 token，並且只替換它。
_CORRUPTED_LOG_TOKEN = "\\n## Log\\n\\n"
_REPAIRED_LOG_TOKEN = "\n\n## Log\n\n"


def repair_body_layout(body: str) -> tuple[str, str]:
    """修復 ai-workflow#17 那個精確的 Log 標題損壞；回傳 (修復後 body, 原 body)。

    這是 ``split_at_log`` fail-closed 之後唯一的出路：排版壞掉的卡若不能用 amend
    修，使用者就只能退回 ``gh issue edit``——工具在最需要它的時候不能用。

    **本函式只做一件事：把首個 ``\\n## Log\\n\\n``（字面）換成真正的標題與空行，
    其餘每一個字元逐位元不動。** 兩次查核打穿了比這更寬鬆的做法，兩次都是同一個
    錯誤——以為限縮了範圍，實際仍在做無差別替換：

    - 第一版對整份 body 替換所有字面 ``\\n``，並以「剝掉空白後相同」當內容不變的
      證明。該證明預先把字面 ``\\n`` 從比較基準刪掉，等於把破壞藏進證明裡；JSON
      字串裡的 ``{"note": "a\\nb"}`` 因此被改壞而檢查不出來。
    - 第二版限縮了**起點**（只動 ``\\n## Log`` 之後），卻仍對整個尾段無差別替換。
      實測兩個破口：#17 自己的 Log 敘述中含合法的字面 ``\\n``（那行正在描述「把
      字面 ``\\n`` 還原」），會被一併改掉；fenced code block 內的 ``\\n## Log``
      會被誤認為 Log 起點，修復後在程式碼圍籬裡生出一個標題。

    因此現在不再有「範圍」的概念，只有一次定點替換。不符這個精確事故形態就拒絕，
    不試著猜測其他損壞怎麼修。
    """
    occurrences = body.count(_CORRUPTED_LOG_TOKEN)
    if occurrences == 0:
        raise AmendError(
            "body 內找不到 `\\n## Log\\n\\n`（字面）。本模式只修復這一個精確的已知"
            "事故形態，其他排版損壞不在範圍內"
        )
    if occurrences > 1:
        raise AmendError(
            f"`\\n## Log\\n\\n`（字面）出現 {occurrences} 次，不符已知事故形態；"
            "無法判斷哪一個才是真正的 Log 標題，拒絕"
        )

    idx = body.index(_CORRUPTED_LOG_TOKEN)
    if body.count("```", 0, idx) % 2 == 1:
        raise AmendError(
            "損壞標記位於 fenced code block 內，那是內容不是標題；拒絕"
        )

    # 真實事故中，token 取代的是「上一段內容」與 Log 標題之間的空行，因此它必定
    # 緊接在內容文字之後。若它那一行在它之前只有空白，代表它處在縮排式程式碼區塊
    # 一類的內容脈絡裡——那是內容不是標題。
    line_start = body.rfind("\n", 0, idx) + 1
    prefix = body[line_start:idx]
    if idx != 0 and not prefix.strip():
        raise AmendError(
            f"損壞標記所在行在它之前只有空白（{prefix!r}），像是縮排式程式碼區塊裡的"
            "內容而非 Log 標題；拒絕"
        )

    repaired = body[:idx] + _REPAIRED_LOG_TOKEN + body[idx + len(_CORRUPTED_LOG_TOKEN) :]
    _, log_tail = split_at_log(repaired)  # 修不好就讓它在這裡失敗，不寫出半修好的 body

    # 對**結果**的結構不變量，而不是對輸入做 Markdown 語境分析。
    #
    # 上面的 ``` 計數只擋得住反引號圍籬；`~~~` 圍籬、四空白縮排區塊、行內碼裡的
    # 同一個 token 它都看不見。自我對抗測試證實：當 body 剛好沒有真正的 Log 標題
    # 時（那些情形不會被「兩個 ## Log」的檢查攔下），修復會在圍籬或行內碼中間生出
    # 一個標題。想靠列舉語境把它補完是追不完的——這已經是同一類錯誤第三次。
    #
    # 改為驗結果：真實卡片的 Log 區段永遠只有標題、空行、以及 `- ` 開頭的條目
    # （``append_log_line`` 是唯一寫入者）。修完不符這個形狀，就代表切點落錯位置。
    stray = [
        line
        for line in log_tail.splitlines()[1:]
        if line.strip() and not line.startswith("- ")
    ]
    if stray:
        raise AmendError(
            "修復後的 Log 區段含非條目內容（例如圍籬、行內碼或其他章節殘留）："
            f"{stray[0]!r}；判定切點落在內容中而非真正的 Log 標題，拒絕"
        )

    before_decl = try_parse_block(body)
    if before_decl is not None:
        after_decl = try_parse_block(repaired)
        if after_decl is None or (
            after_decl.db_scope,
            after_decl.resources,
        ) != (before_decl.db_scope, before_decl.resources):
            raise AmendError("修復會改變資源宣告的解析結果，拒絕")
    return repaired, body


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


__all__ = [
    "CHAIN_DEPTH_HARD_CAP",
    "TIERS",
    "AmendError",
    "Card",
    "amend_acceptance",
    "amend_resource_block",
    "amend_spec_baseline",
    "amend_verification",
    "append_log_line",
    "chain_depth_violation_message",
    "format_branch_worktree",
    "now_iso8601",
    "parse_branch_worktree",
    "render_issue_body",
    "render_spec_markdown",
    "repair_body_layout",
    "split_at_log",
]
