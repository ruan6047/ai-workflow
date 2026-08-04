"""snapshot：狀態面快照 export 回 git（JSON＋人類可讀 Ledger 渲染）。

讀 GitHub Project 全部 items，把 13 個凍結欄位 + body 內解析出的資源宣告，
渲染成：(1) 給程式讀的 JSON、(2) 給人看的 Markdown Ledger 表格。輸出寫到哪個
檔案由呼叫端（commands/snapshot_cmd.py）決定，這裡只負責渲染字串，不碰檔案系統，
方便單元測試。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from .card import now_iso8601, parse_branch_worktree
from .project import ItemSnapshot
from .resources import try_parse_block

LEDGER_COLUMNS = [
    "卡ID", "Initiative", "級別", "功能", "owner", "分支worktree", "iteration",
    "交付狀態", "部署狀態", "最後交接", "服務的原始目標", "鏈深", "資源宣告",
]


@dataclass
class SnapshotRow:
    card_id: str
    initiative: str | None
    tier: str | None
    feature: str | None
    owner: str | None
    branch: str | None
    worktree: str | None
    iteration: float | None
    delivery_status: str | None
    deployment_status: str | None
    last_handoff: str | None
    service_goal: str | None
    chain_depth: float | None
    resource_summary: str | None
    resource_db_scope: str | None
    resources: list[str]
    issue_number: int | None
    issue_url: str | None
    content_type: str


def build_rows(items: list[ItemSnapshot]) -> list[SnapshotRow]:
    rows: list[SnapshotRow] = []
    for item in items:
        card_id = item.fields.get("卡ID")
        if not card_id:
            continue  # 還沒寫入卡ID的 item（例如剛 item-create、尚未跑過 open 完整流程）不列入快照
        branch, worktree = parse_branch_worktree(item.fields.get("分支worktree") or "—")
        decl = try_parse_block(item.body)
        rows.append(
            SnapshotRow(
                card_id=card_id,
                initiative=item.fields.get("Initiative"),
                tier=item.fields.get("級別"),
                feature=item.fields.get("功能"),
                owner=item.fields.get("owner"),
                branch=branch,
                worktree=worktree,
                iteration=item.fields.get("iteration"),
                delivery_status=item.fields.get("交付狀態"),
                deployment_status=item.fields.get("部署狀態"),
                last_handoff=item.fields.get("最後交接"),
                service_goal=item.fields.get("服務的原始目標"),
                chain_depth=item.fields.get("鏈深"),
                resource_summary=item.fields.get("資源宣告"),
                resource_db_scope=decl.db_scope if decl else None,
                resources=decl.resources if decl else [],
                issue_number=item.issue_number,
                issue_url=item.issue_url,
                content_type=item.content_type,
            )
        )
    rows.sort(key=lambda r: r.card_id)
    return rows


def render_json(rows: list[SnapshotRow], generated_at: str | None = None) -> str:
    payload = {
        "generated_at": generated_at or now_iso8601(),
        "schema": "wf-cli/state-snapshot/v1",
        "cards": [asdict(r) for r in rows],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_markdown(rows: list[SnapshotRow], generated_at: str | None = None) -> str:
    ts = generated_at or now_iso8601()
    note = f"> 產生時間：{ts}；由 `wfcli snapshot` 從 GitHub Project 匯出，非人工維護，改動請重跑指令而非手改本檔。"
    lines = [
        "# 狀態面快照（wf-cli snapshot）",
        "",
        note,
        "",
        "| " + " | ".join(LEDGER_COLUMNS) + " |",
        "|" + "---|" * len(LEDGER_COLUMNS),
    ]
    for r in rows:
        bw = f"`{r.branch} @ {r.worktree}`" if r.branch else "—"
        res_summary = r.resource_summary or (
            f"db_scope={r.resource_db_scope}" if r.resource_db_scope else "—"
        )
        cells = [
            r.card_id, r.initiative or "—", r.tier or "—", r.feature or "—",
            r.owner or "待指派", bw,
            str(int(r.iteration)) if r.iteration is not None else "0",
            r.delivery_status or "—", r.deployment_status or "—不適用",
            r.last_handoff or "—", r.service_goal or "—",
            str(int(r.chain_depth)) if r.chain_depth is not None else "0",
            res_summary,
        ]
        lines.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
    lines.append("")
    return "\n".join(lines)


__all__ = ["LEDGER_COLUMNS", "SnapshotRow", "build_rows", "render_json", "render_markdown"]
