"""GitHub Projects v2 adapter：欄位建立／讀取／寫入、item 建立與批次讀取。

型別對照表凍結自 ``OPS-STATE-PLANE-MIG1`` Task 1（見
``docs/research/OPS-STATE-PLANE-MIG1_field_mapping.md``）＋需求方裁決：

- 最後交接：TEXT（完整 ISO-8601，字典序即時序；不用 DATE，因其 API 層靜默截斷時分秒）
- 資源宣告：TEXT（人類可讀摘要）＋ body fenced JSON 區塊（機器解析，見 resources.py）
- 其餘：TEXT／NUMBER／SINGLE_SELECT

欄位查詢**不會**回報 TEXT/NUMBER/DATE 的實際資料型別（三者的 GraphQL
``__typename`` 皆是通用的 ``ProjectV2Field``，見手動驗證紀錄）；
因此欄位的「寫入時該用哪個 gh flag」由本模組的 ``FIELD_SPECS``（我方定義並建立的
凍結 schema）決定，不做執行期型別 introspection——欄位查詢只用來
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
    #: roadmap_lines.gate_of 對未知狀態 fail closed（`raise CheckFailed`）⇒ 切換那一刻會停
    #: 的，是「**讀活看板、且把交付狀態餵進 gate_of**」的消費者。⚠️ **此處刻意記判準、
    #: ⛔ 不記支數**——支數隨腳本增刪而變，判準不會。依判準逐支查證（cpbl 基線釘死為字面
    #: `3b470d70`，2026-08-28 實跑）：roadmap_lines.py 讀 `gh project item-list` 的活看板
    #: ⇒ 命中；state_plane_migrate.py 讀 `git_show(DEFAULT_BASELINE_REF, "docs/TASKS.md")`，
    #: 那是 2026-08-04 起封存唯讀的凍結檔 ⇒ 看板語彙切換碰不到它；workflow_ledger.py --check
    #: 今天就已 rc=1（2026-08-15 需求方裁定停用，⛔ 與 gate_of 無關）⇒ ⛔ 不得記為「被切換
    #: 停掉的」。本句何時再變假：新增任何讀活看板並經 gate_of 的消費者，或
    #: DEFAULT_BASELINE_REF 由凍結 ref 改指活看板。
    #: ⇒ 本欄位有兩個 writer：open_cmd 無條件寫「需求」（不在任何 if 之下），
    #: handoff --next-stage 依 STAGE_PHASE 的六個鍵寫；⛔ assign 不寫它（該分歧的警示就地
    #: 記在 handoff_cmd._pitfall_gate）。⚠️ **此處刻意記 writer 的符號、⛔ 不記「今天有幾張
    #: 卡有值」**——覆蓋率每跑一次 handoff 就變，而 writer 集合只隨這三個符號的增刪而變，
    #: 且每個都 grep 得到唯一命中。本句何時再變假：STAGE_PHASE 增刪鍵、assign 開始寫本欄、
    #: 或 open 不再無條件寫「需求」。
    #: ⚠️ 而**交付狀態仍同時承載階段與狀態**：其選項域裡 💡需求／🔬研究中／🧭規劃中 是階段
    #: 詞、🔍待查核／✅通過 是狀態詞，兩軸尚未分家。本句何時再變假：本檔 FIELD_SPECS
    #: 的「交付狀態」選項元組移除階段詞——而下一格 ensure_fields 的註記正說明了那為什麼
    #: 不是改一行就做得到的事。
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
    #: 卡**內容**（Issue／DraftIssue）的建立時刻，GitHub 回的是 UTC（``...Z``）。
    #:
    #: ⚠️ 取的是 ``content.createdAt`` 而**不是** ``ProjectV2Item.createdAt``（item 進看板
    #: 那一刻）。兩者實測差距 ≤ 3 秒（全 203 筆，content 恆 ≤ item，無反向），⇒ 選它不是
    #: 為了精度，而是為了**方向**：消費端 `doctor.predates_rule` 用它答「這張卡早於規則
    #: 嗎」，估得太晚會把卡推進「晚於規則卻不合規」＝對寫入端的指控。content 是兩者中
    #: 較早的那個，⇒ 錯的方向落在無指控的那一側。
    #:
    #: ⛔ 這**不是**「工作發生的時刻」：2026-08-04 狀態面遷移的卡，其 Issue 建立於遷移
    #: 當天而非當初開卡時。該限制由 `doctor.CREATED_AT_TRUSTED_FROM` 施加，⛔ 不在此處
    #: 預先過濾——本模組只負責忠實回報來源值。
    created_at: str | None = None
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


#: 欄位定義查詢。``node(id:)`` 而**不是** ``user(login:).projectV2(number:)``：後者要求
#: 呼叫端先知道擁有者是 user 還是 organization（兩個不同的 root field），而 node id 是
#: 不透明的、對兩者同形——代價是要先有 project id（見 ``list_fields`` 的 ``project_id``）。
#: ⛔ 本字串內不得出現 "mutation" 字樣：測試的寫入偵測代理
#: （``tests/test_commands_mocked.py`` 的 ``_RecordingRunner.mutations``）以
#: ``"mutation" in query`` 判定一次 GraphQL 呼叫是不是寫入，寫進註解會讓這支唯讀查詢
#: 被記成寫入，把「拒絕路徑零寫入」那批斷言變成假紅。
_LIST_FIELDS_QUERY = """
query($projectId: ID!, $after: String) {
  node(id: $projectId) {
    ... on ProjectV2 {
      fields(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          __typename
          ... on ProjectV2FieldCommon { id name }
          ... on ProjectV2SingleSelectField { options { id name } }
        }
      }
    }
  }
}
"""


def _field_metas(raw_fields: list[dict[str, Any]]) -> dict[str, FieldMeta]:
    """把「欄位定義的原始列表」轉成 ``name -> FieldMeta``。

    每一筆的形狀是 ``{"id", "name", "type"}``（＋single select 才有的 ``"options"``），
    也就是 ``gh project field-list --format json`` 的 ``fields`` 元素形狀。⭐ 刻意獨立成
    一支：等價性論證因此只需要證明**輸入的原始列表**相同，不必主張兩條解析路徑等價。
    """
    out: dict[str, FieldMeta] = {}
    for f in raw_fields:
        name = f["name"]
        spec = FIELD_SPECS.get(name)
        # Project 內建 Status 不在我方凍結 custom-field schema，卻同樣是 single
        # select。保留 GitHub 回傳的型別，才能以 item-value 寫入安全地寫它，
        # 而不是把內建欄位誤當 TEXT 或嘗試建立同名 custom field。
        ftype: FieldType = (
            spec[0]
            if spec
            else "SINGLE_SELECT" if f.get("type") == "ProjectV2SingleSelectField" else "TEXT"
        )
        options = {o["name"]: o["id"] for o in f.get("options", [])}
        out[name] = FieldMeta(id=f["id"], name=name, type=ftype, options=options)
    return out


def _fetch_field_nodes(runner: GhRunner, project_id: str) -> list[dict[str, Any]]:
    """以原生 GraphQL 取回全部欄位定義，正規化成 ``field-list`` 的元素形狀。

    分頁：``fields`` 單頁上限 100，超過時 ``pageInfo.hasNextPage`` 為真、以
    ``endCursor`` 續取。⚠️ 真實環境測不到這條——本 repo 的 Project #4 只有 29 欄，
    要造一個 >100 欄的 Project 才會踩到；故分頁由 ``tests/test_project_mocked.py`` 的
    兩頁 stub 驗證，⛔ 未在真實 API 上跑過。
    """
    nodes: list[dict[str, Any]] = []
    after: str | None = None
    while True:
        variables = {"projectId": project_id}
        if after:
            # ⚠️ 只在有 cursor 時才帶：``GhRunner.graphql`` 一律以 ``-f`` 傳字串，
            # 空字串會變成 ``after: ""`` 而不是 ``null``（同 list_items 的既有作法）。
            variables["after"] = after
        result = runner.graphql(_LIST_FIELDS_QUERY, **variables)
        page = ((result.get("data") or {}).get("node") or {}).get("fields", {})
        for raw in page.get("nodes", []):
            entry: dict[str, Any] = {
                "id": raw["id"],
                "name": raw["name"],
                # ``__typename`` 就是 gh 在 ``field-list --format json`` 的 ``type`` 欄
                # 填的那個字串（2026-08-26 對 Project #4 全 29 欄逐位元核對過）。
                "type": raw["__typename"],
            }
            if raw.get("options"):
                entry["options"] = raw["options"]
            nodes.append(entry)
        page_info = page.get("pageInfo", {})
        if page_info.get("hasNextPage"):
            after = page_info.get("endCursor")
        else:
            break
    return nodes


def list_fields(
    runner: GhRunner, owner: str, number: int, project_id: str | None = None
) -> dict[str, FieldMeta]:
    """讀 project 的欄位定義（name -> FieldMeta）。

    **刻意不用 ``gh project field-list``**，理由是成本、不是正確性：

    - **等價性（已證）**：2026-08-26 對真實 Project #4 同時取兩邊，把 gh 的
      ``fields`` 元素與本查詢正規化後的元素做**順序敏感、含 option id 與 option 順序**
      的逐位元比對 ⇒ 全等（29 欄 × (id, name, type) ＋ 38 個 option 的 (id, name)）。
      複驗方式：``gh project field-list 4 --owner ruan6047 --format json -L 100`` 與
      ``gh api graphql`` 跑 ``_LIST_FIELDS_QUERY``，兩份輸出比對。
    - **成本（已量）**：舊路徑 **102 點／4.45 秒**，本路徑 ``project view`` 2 點
      ＋ 本查詢 1 點 ＝ **3 點／約 1.9 秒**。102 點與 Project 規模無關——同日對
      **0 個 item** 的拋棄式 Project 量到的也是 102 點（對照：203 個 item 的 #4 同樣
      102 點）⇒ 它是 gh CLI 查詢組裝的結構常數。⛔ 更細的根因（gh 把 ``firstItems``
      寫死）取自卡面 A7 的引述，**未**由本卡讀 gh 原始碼複驗。
    - ⛔ **不得由上述推出「對 organization 擁有的 Project 也等價」**：量測環境
      （``ruan6047``）名下沒有 organization，``gh`` 實測回 ``organization: null``，
      **無樣本可驗**。已知的形狀差異只在「怎麼拿到 project id」那一步（``gh project
      view`` 對兩者都可用），而本查詢從 node id 出發、對 owner 型別不敏感——但那是
      推論，⛔ 不是量測。

    ``project_id`` 省略時內部 ``resolve_project``，讓既有呼叫點一行不改。
    ⚠️ 這使 ``deploy-declare``／``deploy-state``／``amend`` 每次多發一次
    ``gh project view``（2 點）——它們在上一行已經 resolve 過，卻無法把 id 傳進來。
    這是**刻意付的**：本卡的射程明文禁止改 ``ensure_fields`` 以外的呼叫點
    （驗收 A4／A8）。⛔ 不得由此推出「多這一次呼叫是必要的」——它純粹是射程邊界，
    把 ``project_id=project.id`` 補進那三個呼叫點即可消除。
    """
    if project_id is None:
        project_id = resolve_project(runner, owner, number).id
    return _field_metas(_fetch_field_nodes(runner, project_id))


def ensure_fields(runner: GhRunner, owner: str, number: int) -> dict[str, FieldMeta]:
    """冪等：缺哪個凍結欄位就建哪個，已存在的原樣保留（含既有 option id）。"""
    project_id = resolve_project(runner, owner, number).id
    existing = list_fields(runner, owner, number, project_id=project_id)
    created = False
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
        created = True
    if not created:
        # ⭐ **刻意如此**：一個欄位都沒建時直接回傳第一次查詢的結果，不再查第二次。
        #
        # 為什麼安全：`created` 為假 ⇒ 上面的迴圈一次 `field-create` 都沒送出 ⇒
        # 在第一次查詢與這個 return 之間，**本函式對遠端沒有任何寫入**，重查只會
        # 拿到同一份東西。（成本，2026-08-26 對 Project #4 實測：舊路徑一次
        # `gh project field-list` 是 102 點／4.45 秒，`ensure_fields` 因此固定付兩次；
        # 換成原生查詢＋本分支後，零建立整支 **3 點／約 1.9 秒**，連續三次量測皆 3 點。）
        #
        # ⛔ **不得由這個分支推出「ensure_fields 對併發是安全的」**：本函式沒有任何
        # project 層的鎖，另一個 process 仍可能在兩次查詢之間動欄位。但那在舊碼下
        # 同樣沒有保證——舊碼的第二次查詢只是「另一個時刻的快照」，不是防線；讀到
        # 哪一版取決於時序。真正的缺口與該用什麼鎖，見
        # `docs/WF_EVENT_IDEMPOTENCY1.md` §7.1／§2.2，⛔ 本卡不處理。
        return existing
    # 有建立時才重查：`field-create` 的回傳沒有被解析併入（那是被否決的 C3 方案），
    # 故新欄位的 id／option id 只能靠重讀取得。
    return list_fields(runner, owner, number, project_id=project_id)


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
            ... on DraftIssue { id title body createdAt }
            ... on Issue { title body number url state createdAt }
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
                    #: ⚠️ 兩個 content 片段都要 `createdAt`，⛔ 不能只掛在 `Issue` 上——
                    #: 看板現存 1 張 DraftIssue，只掛 Issue 會讓它靜默回 None 而落
                    #: `undecidable`，看起來與「這張卡真的判不出時刻」一模一樣。
                    created_at=content.get("createdAt"),
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
