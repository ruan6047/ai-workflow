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


__all__ = [
    "CHAIN_DEPTH_HARD_CAP",
    "TIERS",
    "Card",
    "append_log_line",
    "chain_depth_violation_message",
    "format_branch_worktree",
    "now_iso8601",
    "parse_branch_worktree",
    "render_issue_body",
    "render_spec_markdown",
]
