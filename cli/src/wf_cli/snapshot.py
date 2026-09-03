"""snapshot：狀態面快照 export 回 git（JSON＋人類可讀 Ledger 渲染）。

讀 GitHub Project 全部 items，把凍結欄位 + body 內解析出的資源宣告與規格節，
渲染成：(1) 給程式讀的 JSON、(2) 給人看的 Markdown Ledger 表格。輸出寫到哪個
檔案由呼叫端（commands/snapshot_cmd.py）決定，這裡只負責渲染字串，不碰檔案系統，
方便單元測試。

## 2026-09-02 補欄（`WF-REDESIGN-W3` 驗收 5）

**一律 additive，⛔ 不改任何既有 root 鍵名或 row 欄名。**

- root 新增 `project_id`；`query_version` **以既有 `schema` 承載**（⛔ 不另立鍵）。
  依據：canonical 有三處拿 `generated_at` 當基準——〈狀態〉「年齡以該快照的
  generated_at 為基準」、〈終態卡的封存〉與〈為什麼不下放〉各引一份快照的
  `generated_at` 值——而 `AI_WORKFLOW.md` **⛔ 不在本卡 write-set**；
  `schema`／`cards` 另有 `test_commands_mocked.py` 斷言。
- row 新增 `item_id`（W1 `inv-v1` artifact 的主鍵）、`phase`（階段）、`brief`（簡介）、
  `spec_version`／`spec_text`（規格節，走 `card_spec` 的 `card-spec:v1` 哨兵）。

⭐ **這是把 W1 既有 raw-inventory artifact（`query_version=inv-v1`）的 schema
產品化進 snapshot**：`inv-v1` 的 row 三欄是 `item_id`／`content_type`／`card_id`，
補上 `item_id` 後 snapshot 涵蓋它的全部三欄；root 的 `project_id` 同理。

⛔ **不得稱本卡的後置產物為 W1 Gate 的來源**——`inv-v1` 的 producer 是 **W1 前置**的
一次性唯讀查詢（`archive/wave-specs/w1.md:15`），時序上早於本卡；本卡做的是把它的
形狀**產品化**，⛔ 不是取代它、也⛔ 不能回頭當它的證據。

⚠️ **排序⛔ 未改**：`inv-v1` 依 `item_id` 排，本模組仍依 `card_id` 排。改排序會
動到 `SNAPSHOT.md` 的每一行，而卡面只要求**補欄**。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from .card import now_iso8601, parse_branch_worktree
from .card_spec import try_parse_block as try_parse_spec_block
from .project import ItemSnapshot
from .resources import try_parse_block

#: ⚠️ 2026-09-02 新增「階段」一欄（`WF-REDESIGN-W3` 驗收 5）。它是 `FIELD_SPECS`
#: 裡的凍結欄位、而 Ledger 表格的職責就是鏡射看板欄位 ⇒ 它該在這裡。
#: ⛔ **「簡介」與「規格節」刻意⛔ 不進表格**：兩者都是長文，塞進 13 欄寬的表格會
#: 讓整份 `SNAPSHOT.md` 不可讀。它們只進 JSON——那是機器消費的那一面。
#: ⚠️ 這一句是**本卡的裁斷**，卡面逐字只說「snapshot 補欄（階段／簡介／規格節）」，
#: ⛔ 未指明兩種輸出各補哪些。
LEDGER_COLUMNS = [
    "卡ID", "Initiative", "級別", "功能", "owner", "分支worktree", "iteration",
    "交付狀態", "部署狀態", "階段", "最後交接", "服務的原始目標", "鏈深", "資源宣告",
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
    #: ---- 以下為 2026-09-02 additive 新增（`WF-REDESIGN-W3` 驗收 5）----
    #: Project item 的節點 ID。⭐ W1 `inv-v1` artifact 的**主鍵**；補上它之後
    #: snapshot 涵蓋 `inv-v1` 的全部三欄（`item_id`／`content_type`／`card_id`）。
    item_id: str | None = None
    #: 階段（canonical §0.1 兩軸狀態模型的第一軸）。⚠️ 與 `delivery_status` 是**兩件事**。
    phase: str | None = None
    #: 簡介。取 **Project 欄位**——它是 body 哨兵區塊的**恆等導出**（`brief.py:19`）。
    #: ⛔ 不在此重跑 body 解析：兩居所不一致時該由 `doctor` 報漂移，⛔ 不由 snapshot
    #: 自己選一邊而把漂移抹平。
    brief: str | None = None
    #: 規格**內容**版本。走 `card_spec` 的 `card-spec:v1` 哨兵；缺區塊回 None
    #: （今日 217 張裡 216 張都是這個形狀，⛔ 不是異常）。
    spec_version: int | None = None
    #: 規格節全文，markdown 原樣。⛔ 未結構化。
    spec_text: str | None = None


def build_rows(items: list[ItemSnapshot]) -> list[SnapshotRow]:
    rows: list[SnapshotRow] = []
    for item in items:
        card_id = item.fields.get("卡ID")
        if not card_id:
            continue  # 還沒寫入卡ID的 item（例如剛 item-create、尚未跑過 open 完整流程）不列入快照
        branch, worktree = parse_branch_worktree(item.fields.get("分支worktree") or "—")
        decl = try_parse_block(item.body)
        spec = try_parse_spec_block(item.body)
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
                item_id=item.item_id,
                phase=item.fields.get("階段"),
                brief=item.fields.get("簡介"),
                spec_version=spec.spec_version if spec else None,
                spec_text=spec.text if spec else None,
            )
        )
    rows.sort(key=lambda r: r.card_id)
    return rows


def render_json(
    rows: list[SnapshotRow],
    generated_at: str | None = None,
    project_id: str | None = None,
) -> str:
    """渲染機器消費的那一面。

    ⛔ **既有三個 root 鍵名一字不動**（`generated_at`／`schema`／`cards`）：
    canonical 三處拿 `generated_at` 當基準（〈狀態〉／〈終態卡的封存〉／
    〈為什麼不下放〉），而 `AI_WORKFLOW.md` ⛔ 不在本卡 write-set；
    `schema`／`cards` 有測試斷言。新鍵只能是 additive。

    ⚠️ `project_id` 預設 `None` 是刻意的：`render_json` 是**純渲染**、⛔ 不打 API，
    而 project id 只有呼叫端拿得到。⛔ 不在此處自己去查——那會讓本模組從純函式
    變成會發遠端呼叫的東西。
    """
    payload = {
        "generated_at": generated_at or now_iso8601(),
        "schema": "wf-cli/state-snapshot/v1",
        # ⭐ additive：W1 `inv-v1` artifact 的 root 欄之一。
        # ⚠️ `query_version` **以既有 `schema` 承載**，⛔ 不另立鍵（規格逐字）。
        "project_id": project_id,
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
            r.phase or "—",
            r.last_handoff or "—", r.service_goal or "—",
            str(int(r.chain_depth)) if r.chain_depth is not None else "0",
            res_summary,
        ]
        lines.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
    lines.append("")
    return "\n".join(lines)


__all__ = ["LEDGER_COLUMNS", "SnapshotRow", "build_rows", "render_json", "render_markdown"]
