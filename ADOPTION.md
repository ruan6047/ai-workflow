# ADOPTION — 新專案接上框架

首次採用的必要配置項母體住 `core/adopt.md` §0（恰九項）。本檔逐項寫出**由誰填**與**何時填**；⛔ 不重列母體，也⛔ 不把任何一項的唯一居所放進 `notes` 合成輸出（`.wf/stages/<階段>.md` 的 `P-` 或卡面 `notes` 的 `T-`）。

## 1 · repo 前置

- `ruleset`：**採用專案的管理者**建，**第一次 push 到 main 之前**。main 禁刪、禁改史、`required_linear_history`，bypass 清空（`core/platform.md` P1）。
- `required-status-checks`：**採用專案的管理者**設，**第一張 PR 開出之前**。至少 `secret-scan`、`commit-trailer`（P4、P5）；有可達性檢查的專案加 `reachability`。
- 上面兩個 check 的來源資產由 `wf snapshot --adopt install` **整檔**落地並登記進 `.wf/adopt/manifest.json`（資產名、來源檔、目標路徑住 `core/adopt.md` §2 的框架資產表，本檔⛔ 不重列）。目標路徑上已有既有物時 CLI 對該路徑零寫入、只輸出一項未完成項；把那兩個 job 併進採用專案既有的 workflow 是**執行者 AI** 的工作，**install 之後、第一張 PR 之前**完成，由查核者核對結果。
- rules source 以 submodule 掛載時，落地的 job 其 `actions/checkout` 須帶 `submodules: true`，否則 runner 上取不到 rules root；該行正是來源資產與本 repo `ci.yml` 同名 job 之間**唯一**允許的差異（`core/adopt.md` §2）。
- 本框架唯一支援的 Python 版本是 3.14；帶 Python 消費點的 job 一併帶走該 job 的 `actions/setup-python` 步驟（`python-version: "3.14"`），否則下游會跑到 runner 內建的未釘選 `python3`。
- `reachability` 檢查的是本 repo 的規則檔，採用專案⛔ 不複製。
- commit trailer 鍵集合與必填時機依 `roles/conduct-common.md` §2。

## 2 · `.wf/modules.json`

種子的唯一機器可讀居所＝rules source 的 `.github/adopt/modules.seed.json`，由 `wf snapshot --adopt bootstrap` 自該檔落地；本檔只引用它、⛔ 不重打一份（CLI ⛔ 不以文件排版位置定位採用資料）。`.wf/modules.json` 已存在時該路徑位元組不變，CLI 只輸出一項未完成項。

- `areas`：**採用專案的需求方**填，**第一張卡 `open` 之前**（缺它配不出卡ID）。種子值是佔位；⛔ 不沿用 aiwf 自己的 `WF`、`CLI`、`DOC`、`OPS`（那四值住 `core/naming.md` §1，是本 repo 的值、⛔ 不是通用預設）。`areas` 是卡ID 前綴枚舉（`core/naming.md` §1）。
- `merge_method`：**採用專案的管理者**填，**與 §1 的 ruleset 同時**；值＝repo 只留的那一種合併按鈕（P3），兩處必須同值。
- `modules`：**採用專案的需求方**填，**第一張卡 `open` 之前**。只列 `scope=project` 的模組（該值住各 `modules/<name>/module.md` §0，⛔ 不在本檔重列名單）；`scope=card` 的模組看卡面、⛔ 不列。列名是啟用的必要條件，`enable_if` 仍須成立（`core/modules.md`）。`params` 的鍵與種子值抄該模組 `module.md` §0，本專案實際採用的值住 `.wf/modules.json`。加入帶 `adds.enums.states` 的專案級模組時，同一 PR 補狀態欄選項。`modules[]` 受封閉驗證：未知模組名、重複模組名、未知 `params` 鍵、`params` 型別不符種子，四類皆拒。
- `project`：**PM** 回填，**§3 的 Project 建好之後、第一張卡 `open` 之前**。它是 CLI 定位板的唯一居所（owner 字串＋number 整數）；缺它動詞不寫投影欄、只印「無 Project 設定」。種子值是 `null`。
- `rules`：**`bootstrap` 自動填**當次解析到的 rules root，時點＝**`git submodule add` 之後跑 `bootstrap` 那一刻**。`null`＝規則就在 project_root；`{"path": …}` 相對 project_root（⛔ 不相對 `.wf`）。canonical install mode 與四列對帳住 `core/adopt.md` §1，本檔⛔ 不重列。
- `remote`：**採用專案的管理者**填，**第一次跑會碰遠端的動詞之前**。值是 git remote 的名稱（⛔ 不是 URL）：CLI 依 ①`--remote` ②本鍵 ③current branch 的 upstream ④唯一 remote 決定 repository；多個 remote 只在 API stable ID 相同時合併，否則 fail-loud、⛔ 不猜 origin。`GH_REPO` 不在這條序列內：本機身分缺席時成唯一候選，存在時只作核對。
- 有資料庫才建 `.wf/contracts/DATABASE_CONTRACT.md`；同時 ≥2 執行者才建 `.wf/contracts/CONTROL_PLANE.md`。
- project_root／rules_root 分工：`.wf/`、snapshot 輸出、本機 git 工作樹一律相對 project_root；規則資產一律相對 rules root。三個全域旗標只認動詞之前：`wf [--project-root <p>] [--rules-root <p>] [--remote <name>] <verb> …`，旗標值相對 invocation cwd，並各自勝過同名設定鍵。

## 3 · Project 五欄

- `project-fields`：**PM** 建，**第一張卡 `open` 之前**。五欄＝階段（單選）、狀態（單選）、級別（單選）、owner（TEXT，`role:actor`）、卡ID（TEXT）。
- 值域逐字取 `core/enums.md`（階段 `stages`、級別 `tiers`）與各模組 `module.md` §0（`adds.enums.states`）。狀態＝`states_core`＋`state_blocked`＋`states_terminal`＋**全部** `maturity=ready` 模組的 `adds.enums.states`（`scope=card` 者逐卡啟用、`scope=project` 者另需列入 `modules`；非 `ready` 的模組⛔ 不貢獻狀態），選項缺一個就讓一條合法轉移變成 D3 拒收，故建板時一次備齊；Project 備妥選項⛔ 不等於模組已啟用。
- 兩個 view（活卡依階段分組、全部）：建 view 與 filter 可走 `createProjectV2View`／`updateProjectV2View`；依階段分組與內建 workflow 停用⛔ 無 API 輸入（查法＝introspect `ProjectV2ViewConfigurationInput` 只有 `visibleFieldIds`、Mutation 無 `updateProjectV2Workflow`），UI 手做後以 `projectV2.views{filter groupByFields}` 與 `workflows{enabled}` 回讀比對，⛔ 不憑截圖。
- 五欄全由 CLI 回寫；⛔ 不用 GitHub 內建自動化、⛔ 不在 UI 手改（`roles/conduct-common.md` §1）。

## 4 · 第一張卡

- 提案者在 issue 貼一個 `json wf-intake` 區塊（`core/card-schema.md` §3）；需求方只決定升不升級為卡。
- PM 跑 `open` 上板，之後走 `stages/requirement.md`；T0／T1 跳過規劃階段（`core/tiers.md` §1）。
- 第一張卡先把本專案的 P- 注意事項與 `.wf/stages/<階段>.md` 建起來。

## 5 · 退場

停用框架時 `wf snapshot --adopt deactivate` 只移除它有明確權限處置的資產。逐字分三類：

- **由 CLI 移除者**：manifest 內 `ownership`＝`framework-managed` 的**整檔**登記路徑，含 `.wf/adopt/manifest.json` 自己，與因此變空的 `.wf/adopt/` 目錄。
- **由 AI 依證據處理者**：由執行者 AI 整合進採用專案既有檔案的內容（例：併進既有 workflow 的 `secret-scan` 與 `commit-trailer` 兩個 job），以及 manifest 內 `path` 含 `#` 的 legacy 登記項與其承載檔。CLI 只逐項列出並指向本節，⛔ 不移除、⛔ 不改寫；移除與否由**採用專案的需求方**決定，由**執行者 AI** 依證據執行、查核者核對結果。
- **一律保留者**：Issue、留言、Project 資料、ruleset，與 `consumer-owned` 的 `.wf/`（含 `.wf/modules.json` 與 `.wf/stages/`）。專案歷史一律保留；停用框架⛔ 不等於刪除採用專案的任何紀錄。
