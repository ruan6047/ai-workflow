# 新專案採用指南 (Adoption)

讓一個 `~/Dev/<專案>` 納入本 AI 協作治理，基本三步；有部署或資料庫者再接對應契約：

## 1. 放工作流 stub
複製 [`templates/project-stub.md`](templates/project-stub.md) → `<專案>/docs/AI_WORKFLOW.md`。
（stub 指向本 canonical + 核心鐵律速查；**不複製全文**，規則只有一個家。）

## 2. 起任務看板（一卡一檔）
複製 [`templates/TASKS.md`](templates/TASKS.md) → `<專案>/docs/TASKS.md`（Ledger 索引 only），把 `<專案名>` 換掉；
每張卡由 [`templates/tasks-card.md`](templates/tasks-card.md) 建 `<專案>/docs/tasks/<卡ID>.md`（結案卡 `git mv` 進 `docs/archive/tasks/`）。T3/T4 另由 [`templates/discovery-brief.md`](templates/discovery-brief.md) 建 Discovery brief；使用者可見的 T3/T4 再建 [`templates/design-brief.md`](templates/design-brief.md)，純技術卡則記錄 Design Gate `N/A` 的理由；研究不確定性時使用 [`templates/research-plan.md`](templates/research-plan.md)。大型工作由 [`templates/initiative-card.md`](templates/initiative-card.md) 建 Initiative 父卡，先定 spec 基線與依賴圖再開子卡。
此後該專案所有任務卡／log 都住這裡（**不集中到本 repo**）。event log 保存狀態歷史，Ledger 是 current-state projection（見 canonical §6）。
另起一份 `<專案>/docs/BUGS.md`（快線 bug 滾動 log，見 canonical §3；bug 卡範本 [`templates/bug-card.md`](templates/bug-card.md)）。

## 3. CLAUDE.md 加指引
在 `<專案>/CLAUDE.md` 頂部加一行：
```
> 多 AI 協作前先讀 docs/AI_WORKFLOW.md（stub → canonical ~/Dev/ai-workflow）；任務看板 docs/TASKS.md。
```

## 4. 接 control-plane adapter（多 writer／共享資源時必需）

從 [`templates/control-plane-contract.md`](templates/control-plane-contract.md) 建立 `<專案>/docs/CONTROL_PLANE_CONTRACT.md`，在專案 Runbook 定義 canonical §4.1 的 adapter：remote coordination（GitHub 為預設實作）處理跨人 task、review、lease、CI；local resource lock 處理 worktree、port、container 與未提交變更。event log 是作業狀態事實來源，應產生含 owner、branch、worktree、iteration 與最後交接時間的 Ledger 投影；不得只以看板文字或聊天訊息協調。依團隊人類審查量能設定 agent 與 review queue 的 WIP limit。

## 5. 接資料庫契約（有資料庫才需要）

從 [`templates/database-contract.md`](templates/database-contract.md) 建立 `<專案>/docs/DATABASE_CONTRACT.md`，填入該專案的 DB 引擎、migration 工具與 runner、環境 namespace、資源 lock、備份／回滾及驗證命令。Runbook 以此文件為 DB 操作事實；canonical 只提供 §4.2 的共同不變量。

## 6. 接部署狀態 adapter（有部署才需要）

在專案 Runbook／`DEPLOYMENT.md` 定義部署契約：目標環境、main source SHA、觸發方式、驗證、回滾、狀態回報與 owner。部署平台與 job 由專案自行選擇；共同要求只有：

- GitHub PR merge 後自動記錄 `📦已合併`、PR URL 與 merge SHA。
- `deploy → verify → update-task-status` 在同一 workflow 執行鏈回報結果。
- 需部署的卡只有 `✅已驗證` 才能 `🏁完成`；失敗或回滾不得封存。

## 完成後
- 該專案即受本機制管理：人工派工、按 T0–T4 分級的分支／驗證、實作/審核分離、只有 main 已審核可部署、交付／部署分軌留痕、commit trailer 留痕。
- 規則有更新 → **只改本 repo `AI_WORKFLOW.md`**；各專案 stub 指針不變、無需同步。

## 已採用專案
- `cpbl-analytics`（submodule of PersonalWebsite）
- `PersonalWebsite`（主站）
