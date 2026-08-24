"""GitHub Projects v2 adapter：欄位建立／讀取／寫入、item 建立與批次讀取。

型別對照表凍結自 ``OPS-STATE-PLANE-MIG1`` Task 1（見
``docs/research/OPS-STATE-PLANE-MIG1_field_mapping.md``）＋需求方裁決：

- 最後交接：TEXT（完整 ISO-8601，字典序即時序；不用 DATE，因其 API 層靜默截斷時分秒）
- 資源宣告：TEXT（人類可讀摘要）＋ body fenced JSON 區塊（機器解析，見 resources.py）
- 其餘：TEXT／NUMBER／SINGLE_SELECT

``gh project field-list`` 不會回報 TEXT/NUMBER/DATE 的實際資料型別（三者的
GraphQL ``__typename`` 皆是通用的 ``ProjectV2Field``，見手動驗證紀錄）；
因此欄位的「寫入時該用哪個 gh flag」由本模組的 ``FIELD_SPECS``（我方定義並建立的
凍結 schema）決定，不做執行期型別 introspection——field-list／GraphQL 查詢只用來
取得每個 project 實際的 field id／option id（這兩者會隨 project 而異，無法寫死）。
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dc_field
from typing import Any, Literal

from .gh import GhRunner

FieldType = Literal["TEXT", "NUMBER", "SINGLE_SELECT"]

# 凍結欄位 schema：name -> (type, options或None)。
FIELD_SPECS: dict[str, tuple[FieldType, tuple[str, ...] | None]] = {
    "卡ID": ("TEXT", None),
    "Initiative": ("TEXT", None),
    "級別": ("SINGLE_SELECT", ("T0", "T1", "T2", "T3", "T4")),
    "功能": ("TEXT", None),
    "owner": ("TEXT", None),
    "分支worktree": ("TEXT", None),
    "iteration": ("NUMBER", None),
    "交付狀態": (
        "SINGLE_SELECT",
        (
            "💡需求", "🔬研究中", "🧭規劃中", "📥Backlog", "⏳待執行", "🔨執行中", "🚧進行中",
            "🔍待查核", "✅通過", "📦已合併", "🏁完成",
            "↩退回", "⏸阻塞", "🚨已升級", "🛑已停止",
        ),
    ),
    "部署狀態": (
        "SINGLE_SELECT",
        ("—不適用", "⏸未部署", "🚀待部署", "⏳部署中", "✅已部署", "🧪驗證中", "✅已驗證"),
    ),
    "最後交接": ("TEXT", None),
    "服務的原始目標": ("TEXT", None),
    "鏈深": ("NUMBER", None),
    "資源宣告": ("TEXT", None),
    #: 卡片簡介（canonical §6.3）。TEXT，且是 body 哨兵區塊的**恆等導出**——
    #: 非摘要、非截斷。寫入順序 body 先、欄位後並讀回驗證（見 brief.drifted）。
    "簡介": ("TEXT", None),
    #: 階段（canonical §0.1 兩軸狀態模型的第一軸）。⚠️ **本卡只建欄位、不切換語彙**：
    #: §0.1 逐字「本節定義目標狀態，尚未切換；上方 §0 的單欄序列仍是現行實作」，
    #: 且切換須待 cpbl 相容層（子卡 S2）落地——cpbl 有六個檔綁狀態語彙，而
    #: roadmap_lines.gate_of 對未知狀態 fail closed，切換那一刻三支腳本會停。
    #: ⇒ 本欄位建立後暫時無人寫入，交付狀態仍承載階段與狀態兩者。
    "階段": (
        "SINGLE_SELECT",
        # ⛔ **恰好七個，與 canonical §0.1 逐字相同**（查核 R2-001）。
        # 「階段可選」以**欄位空值**表達，⛔ 不另造第八個哨兵值——SINGLE_SELECT 的選項
        # 建立後改不掉（ensure_fields 逐字「已存在的原樣保留，含既有 option id」），
        # 把無 canonical 依據的值凍結進真實狀態面是不可逆的。
        ("需求", "研究", "規劃", "執行", "審核", "部署", "維護"),
    ),
}

# card.py 的可變 Ledger 欄位對照到 FIELD_SPECS 的 key；set_card_fields 依此逐一寫入。
CARD_FIELD_MAP: dict[str, str] = {
    "card_id": "卡ID",
    "initiative": "Initiative",
    "tier": "級別",
    "feature": "功能",
    "owner": "owner",
    "branch_worktree": "分支worktree",
    "iteration": "iteration",
    "delivery_status": "交付狀態",
    "deployment_status": "部署狀態",
    "last_handoff": "最後交接",
    "service_goal": "服務的原始目標",
    "chain_depth": "鏈深",
    "resource_summary": "資源宣告",
    #: 簡介的 Project 欄位是 body 哨兵區塊的**恆等導出**（canonical §6.3）。
    #: ⚠️ 寫入順序 body 先、欄位後並讀回驗證——見 brief.drifted 與 doctor 的漂移偵測。
    "brief": "簡介",
}


class ProjectError(RuntimeError):
    pass


@dataclass
class FieldMeta:
    id: str
    name: str
    type: FieldType
    options: dict[str, str] = dc_field(default_factory=dict)  # option name -> option id


@dataclass
class ProjectMeta:
    id: str
    owner: str
    number: int
    url: str


@dataclass
class ItemSnapshot:
    item_id: str
    content_type: str  # "DraftIssue" | "Issue"
    title: str
    body: str
    issue_number: int | None = None
    issue_url: str | None = None
    content_id: str | None = None  # DraftIssue 自己的節點 ID（``DI_...``）；見 set_item_body
    fields: dict[str, Any] = dc_field(default_factory=dict)

    def text(self, name: str) -> str | None:
        val = self.fields.get(name)
        return val if isinstance(val, str) else None

    @property
    def card_id(self) -> str | None:
        return self.text("卡ID")

    @property
    def delivery_status(self) -> str | None:
        return self.text("交付狀態")

    @property
    def owner_field(self) -> str | None:
        return self.text("owner")

    @property
    def branch_worktree(self) -> str | None:
        return self.text("分支worktree")


def resolve_project(runner: GhRunner, owner: str, number: int) -> ProjectMeta:
    data = runner.run_json(["project", "view", str(number), "--owner", owner, "--format", "json"])
    if not data:
        raise ProjectError(f"找不到 project {owner}/{number}")
    return ProjectMeta(
        id=data["id"], owner=data["owner"]["login"], number=data["number"], url=data["url"]
    )


def list_fields(runner: GhRunner, owner: str, number: int) -> dict[str, FieldMeta]:
    data = runner.run_json(
        ["project", "field-list", str(number), "--owner", owner, "--format", "json", "-L", "100"]
    )
    out: dict[str, FieldMeta] = {}
    for f in (data or {}).get("fields", []):
        name = f["name"]
        spec = FIELD_SPECS.get(name)
        # Project 內建 Status 不在我方凍結 custom-field schema，卻同樣是 single
        # select。保留 GitHub 回傳的型別，才能以 item-value mutation 安全寫它，
        # 而不是把內建欄位誤當 TEXT 或嘗試建立同名 custom field。
        ftype: FieldType = (
            spec[0]
            if spec
            else "SINGLE_SELECT" if f.get("type") == "ProjectV2SingleSelectField" else "TEXT"
        )
        options = {o["name"]: o["id"] for o in f.get("options", [])}
        out[name] = FieldMeta(id=f["id"], name=name, type=ftype, options=options)
    return out


def ensure_fields(runner: GhRunner, owner: str, number: int) -> dict[str, FieldMeta]:
    """冪等：缺哪個凍結欄位就建哪個，已存在的原樣保留（含既有 option id）。"""
    existing = list_fields(runner, owner, number)
    for name, (ftype, options) in FIELD_SPECS.items():
        if name in existing:
            continue
        args = [
            "project", "field-create", str(number),
            "--owner", owner, "--name", name, "--data-type", ftype,
            "--format", "json",
        ]
        if ftype == "SINGLE_SELECT":
            assert options is not None
            args += ["--single-select-options", ",".join(options)]
        runner.execute(args)
    return list_fields(runner, owner, number)


def create_draft_item(runner: GhRunner, owner: str, number: int, title: str, body: str) -> str:
    data = runner.run_json(
        [
            "project", "item-create", str(number),
            "--owner", owner, "--title", title, "--body", body,
            "--format", "json",
        ]
    )
    return data["id"]


def create_repo_issue(runner: GhRunner, repo: str, title: str, body: str) -> tuple[int, str]:
    out = runner.execute(
        ["issue", "create", "--repo", repo, "--title", title, "--body", body]
    )
    url = out.strip().splitlines()[-1].strip()
    number = int(url.rstrip("/").rsplit("/", 1)[-1])
    return number, url


def add_issue_comment(runner: GhRunner, repo: str, issue_number: int, body: str) -> None:
    """在 Issue timeline 追加一則留言（canonical §4.3：事件＝Issue timeline ＋結構化 comment）。

    刻意走 ``gh issue comment`` 而非改 body：留言是 append-only 的事件流，body 是
    current-state；裁決全文屬前者。draft item 沒有 timeline，呼叫端須先擋掉
    （見 ``commands/review_cmd.py``）。
    """
    runner.execute(
        ["issue", "comment", str(issue_number), "--repo", repo, "--body", body]
    )


def add_item_to_project(runner: GhRunner, owner: str, number: int, issue_url: str) -> str:
    data = runner.run_json(
        ["project", "item-add", str(number), "--owner", owner, "--url", issue_url, "--format", "json"]
    )
    return data["id"]


def set_field_value(
    runner: GhRunner,
    project: ProjectMeta,
    item_id: str,
    field_meta: FieldMeta,
    value: Any,
) -> None:
    args = [
        "project", "item-edit",
        "--id", item_id,
        "--field-id", field_meta.id,
        "--project-id", project.id,
        "--format", "json",
    ]
    if field_meta.type == "TEXT":
        args += ["--text", str(value)]
    elif field_meta.type == "NUMBER":
        args += ["--number", str(value)]
    elif field_meta.type == "SINGLE_SELECT":
        option_id = field_meta.options.get(str(value))
        if option_id is None:
            raise ProjectError(
                f"欄位 {field_meta.name!r} 沒有選項 {value!r}；"
                f"現有選項：{sorted(field_meta.options)}"
            )
        args += ["--single-select-option-id", option_id]
    else:  # pragma: no cover - FIELD_SPECS 目前只用三種
        raise ProjectError(f"不支援的欄位型別 {field_meta.type}")
    runner.execute(args)


def update_item_field_value(
    runner: GhRunner,
    project: ProjectMeta,
    item_id: str,
    field_meta: FieldMeta,
    value: Any,
) -> None:
    """只以 ``updateProjectV2ItemFieldValue`` 更新一個 item 值。

    這條原生 GraphQL 路徑刻意不碰 Project 欄位定義；部署狀態命令必須同時改
    custom field 與內建 Status，不能透過 ``gh project field-*`` 或
    ``updateProjectV2Field`` 偷渡。每次 mutation 只帶一個 value，以符合 GitHub
    Projects v2 的 item-value API 與可稽核的最小寫入集。
    """
    if field_meta.type == "TEXT":
        query = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: String!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $projectId, itemId: $itemId, fieldId: $fieldId, value: {text: $value}
  }) { projectV2Item { id } }
}
"""
        mutation_value = str(value)
    elif field_meta.type == "NUMBER":
        query = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: Float!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $projectId, itemId: $itemId, fieldId: $fieldId, value: {number: $value}
  }) { projectV2Item { id } }
}
"""
        mutation_value = str(value)
    elif field_meta.type == "SINGLE_SELECT":
        option_id = field_meta.options.get(str(value))
        if option_id is None:
            raise ProjectError(
                f"欄位 {field_meta.name!r} 沒有選項 {value!r}；"
                f"現有選項：{sorted(field_meta.options)}"
            )
        query = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: String!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $projectId, itemId: $itemId, fieldId: $fieldId,
    value: {singleSelectOptionId: $value}
  }) { projectV2Item { id } }
}
"""
        mutation_value = option_id
    else:  # pragma: no cover - FieldType 已封閉
        raise ProjectError(f"不支援的欄位型別 {field_meta.type}")

    runner.graphql(
        query,
        projectId=project.id,
        itemId=item_id,
        fieldId=field_meta.id,
        value=mutation_value,
    )


def set_item_body(
    runner: GhRunner, content_type: str, content_id: str | None, project: ProjectMeta,
    repo: str | None, issue_number: int | None, body: str,
) -> None:
    """改 body：draft issue 與 repo issue 是兩條完全不同的路徑，不可混用 ID。

    踩雷紀錄（實跑對 throwaway test Project 才發現，本地 mock 測試沒測到這條路）：
    ``gh project item-edit --body`` 的 ``--id`` 必須是 **draft issue 內容本身**的
    節點 ID（``DI_`` 前綴），不是 ``ProjectV2Item`` 的 ``PVTI_`` 前綴 ID——後者只
    對 ``--field-id``＋``--single-select-option-id``／``--text``／``--number`` 這類
    「改欄位值」的呼叫有效，`gh` 對「改 body／title」與「改欄位值」用了兩種不同
    的 ID 命名空間卻共用同一個 ``--id`` 旗標，錯誤訊息才會指名 ``DI_`` 前綴。
    """
    if content_type == "DraftIssue":
        if not content_id:
            raise ProjectError("DraftIssue 改 body 需要 content_id（DI_ 前綴），呼叫端未提供")
        runner.execute(["project", "item-edit", "--id", content_id, "--body", body, "--format", "json"])
    else:
        if not repo or issue_number is None:
            raise ProjectError("real issue 需要 repo 與 issue_number 才能改 body")
        runner.execute(["issue", "edit", str(issue_number), "--repo", repo, "--body", body])


_LIST_ITEMS_QUERY = """
query($projectId: ID!, $after: String) {
  node(id: $projectId) {
    ... on ProjectV2 {
      items(first: 50, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          content {
            __typename
            ... on DraftIssue { id title body }
            ... on Issue { title body number url state }
          }
          fieldValues(first: 50) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldDateValue { date field { ... on ProjectV2FieldCommon { name } } }
            }
          }
        }
      }
    }
  }
}
"""


def list_items(runner: GhRunner, project: ProjectMeta) -> list[ItemSnapshot]:
    """批次讀取 project 全部 items（含 body 與所有欄位值）。

    刻意走原生 GraphQL 分頁查詢，不用 ``gh project item-list``——後者對中文欄位
    名稱的 JSON key 有編碼錯誤（見 OPS-STATE-PLANE-MIG1 Task 1「意外發現」）。
    """
    items: list[ItemSnapshot] = []
    after: str | None = None
    while True:
        variables = {"projectId": project.id}
        if after:
            variables["after"] = after
        result = runner.graphql(_LIST_ITEMS_QUERY, **variables)
        node = result.get("data", {}).get("node") or {}
        page = node.get("items", {})
        for raw in page.get("nodes", []):
            content = raw.get("content") or {}
            ctype = content.get("__typename", "DraftIssue")
            fields: dict[str, Any] = {}
            for fv in raw.get("fieldValues", {}).get("nodes", []):
                fname = (fv.get("field") or {}).get("name")
                if not fname:
                    continue
                if "text" in fv:
                    fields[fname] = fv["text"]
                elif "number" in fv:
                    fields[fname] = fv["number"]
                elif "name" in fv and fv.get("__typename") == "ProjectV2ItemFieldSingleSelectValue":
                    fields[fname] = fv["name"]
                elif "date" in fv:
                    fields[fname] = fv["date"]
            items.append(
                ItemSnapshot(
                    item_id=raw["id"],
                    content_type=ctype,
                    title=content.get("title", ""),
                    body=content.get("body") or "",
                    issue_number=content.get("number"),
                    issue_url=content.get("url"),
                    content_id=content.get("id") if ctype == "DraftIssue" else None,
                    fields=fields,
                )
            )
        page_info = page.get("pageInfo", {})
        if page_info.get("hasNextPage"):
            after = page_info.get("endCursor")
        else:
            break
    return items


def find_item_by_card_id(items: list[ItemSnapshot], card_id: str) -> ItemSnapshot | None:
    for item in items:
        if item.card_id == card_id:
            return item
    return None


__all__ = [
    "CARD_FIELD_MAP",
    "FIELD_SPECS",
    "FieldMeta",
    "ItemSnapshot",
    "ProjectError",
    "ProjectMeta",
    "add_issue_comment",
    "add_item_to_project",
    "create_draft_item",
    "create_repo_issue",
    "ensure_fields",
    "find_item_by_card_id",
    "list_fields",
    "list_items",
    "resolve_project",
    "set_field_value",
    "set_item_body",
    "update_item_field_value",
]
