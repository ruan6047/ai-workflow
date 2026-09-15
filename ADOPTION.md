# ADOPTION — 新專案接上框架

## 1 · repo 前置

- 建 ruleset：main 禁刪、禁改史、`required_linear_history`，bypass 清空（`core/platform.md` P1）。
- required status checks 至少 `secret-scan`、`commit-trailer`（P4、P5）；有可達性檢查的專案加 `reachability`。
- 合併方式只留一種按鈕，值同時寫進 `.wf/modules.json` 的 `merge_method`（P3）。
- 複製 `secret-scan` 與 `commit-trailer` 兩個 job 與 `.github/scripts/trailer_check.py`；`reachability` 檢查的是本 repo 的規則檔，採用專案⛔ 不複製。
- 本框架唯一支援的 Python 版本是 3.14；複製上一條的 job 時須一併帶走該 job 的 `actions/setup-python` 步驟（`python-version: "3.14"`），否則下游會跑到 runner 內建的未釘選 `python3`。
- commit trailer 鍵集合與必填時機依 `roles/conduct-common.md` §2。

## 2 · `.wf/modules.json` 種子

```json
{"modules": [],
 "merge_method": "squash",
 "areas": ["WF", "CLI", "DOC", "OPS"],
 "project": null,
 "rules": null,
 "remote": null}
```

- `modules` 只列 `scope=project` 的模組（該值住各 `modules/<name>/module.md` §0，⛔ 不在本檔重列名單）；`scope=card` 的模組看卡面，⛔ 不列。列名是 `scope=project` 啟用的必要條件，`enable_if` 仍須成立（`core/modules.md`）。
- 加入帶 `adds.enums.states` 的專案級模組時，同一 PR 補狀態欄選項。
- `params` 的鍵與種子值抄該模組 `module.md` §0；本專案實際採用的值住本檔。`modules[]` 受封閉驗證：未知模組名、重複模組名、未知 `params` 鍵、`params` 型別不符種子，四類皆拒（`core/modules.md`）。
- `areas` 是卡ID 前綴枚舉（`core/naming.md` §1）。
- `project` 是 CLI 定位板的唯一居所（owner 字串＋number 整數）；缺它動詞不寫投影欄、只印「無 Project 設定」。種子填 `null`，§3 的 Project 建好後回填 `{"owner": …, "number": …}`。
- 有資料庫才建 `.wf/contracts/DATABASE_CONTRACT.md`；同時 ≥2 執行者才建 `.wf/contracts/CONTROL_PLANE.md`。
- `rules` 是 rules source（`core/`、`roles/`、`stages/`、`modules/` 四個規則目錄）的唯一居所：`null`＝規則就在 project_root；`{"path": …}` 相對 project_root（⛔ 不相對 `.wf`）。本檔⛔ 不指定 canonical install mode（submodule、package、vendor 都只要該路徑可讀）。
- `remote` 是 git remote 的名稱（⛔ 不是 URL）：CLI 依 ①`--remote` ②本鍵 ③current branch 的 upstream ④唯一 remote 決定 repository；多個 remote 只在 API stable ID 相同時合併，否則 fail-loud、⛔ 不猜 origin。`GH_REPO` 不在這條序列內：本機身分缺席時成唯一候選，存在時只作核對。
- project_root／rules_root 分工：`.wf/`、snapshot 輸出、本機 git 工作樹一律相對 project_root；規則資產一律相對 rules root。三個全域旗標只認動詞之前：`wf [--project-root <p>] [--rules-root <p>] [--remote <name>] <verb> …`，旗標值相對 invocation cwd，並各自勝過同名設定鍵。

## 3 · Project 五欄

- 階段（單選）、狀態（單選）、級別（單選）、owner（TEXT，`role:actor`）、卡ID（TEXT）。
- 值域逐字取 `core/enums.md`（階段 `stages`、級別 `tiers`）與各模組 `module.md` §0（`adds.enums.states`）。狀態＝`states_core`＋`state_blocked`＋`states_terminal`＋**全部** `maturity=ready` 模組的 `adds.enums.states`（`scope=card` 者逐卡啟用、`scope=project` 者另需列入 `modules`；非 `ready` 的模組⛔ 不貢獻狀態），選項缺一個就讓一條合法轉移變成 D3 拒收，故建板時一次備齊；Project 備妥選項⛔ 不等於模組已啟用。
- 兩個 view（活卡依階段分組、全部）：建 view 與 filter 可走 `createProjectV2View`／`updateProjectV2View`；依階段分組與內建 workflow 停用⛔ 無 API 輸入（查法＝introspect `ProjectV2ViewConfigurationInput` 只有 `visibleFieldIds`、Mutation 無 `updateProjectV2Workflow`），UI 手做後以 `projectV2.views{filter groupByFields}` 與 `workflows{enabled}` 回讀比對，⛔ 不憑截圖。
- 五欄全由 CLI 回寫；⛔ 不用 GitHub 內建自動化、⛔ 不在 UI 手改（`roles/conduct-common.md` §1）。

## 4 · 第一張卡

- 提案者在 issue 貼一個 `json wf-intake` 區塊（`core/card-schema.md` §3）；需求方只決定升不升級為卡。
- PM 跑 `open` 上板，之後走 `stages/requirement.md`；T0／T1 跳過規劃階段（`core/tiers.md` §1）。
- 第一張卡先把本專案的 P- 注意事項與 `.wf/stages/<階段>.md` 建起來。
