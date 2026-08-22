# 任務看板 (Task Board) — <專案名>

> 進度追蹤。規則見 canonical [`~/Dev/ai-workflow/AI_WORKFLOW.md`](../../ai-workflow/AI_WORKFLOW.md)（本專案 stub：[`AI_WORKFLOW.md`](AI_WORKFLOW.md)）。
> git 是程式碼／文件事實來源；control-plane event log 是作業狀態事實來源；本檔是人類可讀的 Ledger 投影。
> ⚠️ **已 cutover 到 Issues／Projects 狀態面的專案**（canonical §4.3）：本檔於 cutover 當下**封存唯讀、不再重建**。**沒有任何指令會重新產生它**——`wfcli snapshot` 寫的是 `snapshot.json` 與 `SNAPSHOT.md`，不是本檔。現況一律以 Issues／Project 欄位為準。
> 交付：`💡需求 → 🔬研究中 → 🧭規劃中 → 📥Backlog → 🔨執行中 → 🔍待查核 → ✅通過 → 📦已合併 → 🏁完成`／`↩退回`／`⏸阻塞`／`🚨已升級`／`🛑已停止`。**廢止的歷史值**（新寫入不得用）：`🚧進行中`、`⏳待執行`。
> 部署狀態見 canonical §0。
> **一卡一檔**（canonical §6）：本檔＝**Ledger 索引 only**（常駐輕量），由 event log 產生 current-state；卡片明細一卡一檔於 `tasks/<卡ID>.md`（範本 [`tasks-card.md`](tasks-card.md)），按需載入。結案卡 `git mv` 進 `archive/tasks/`、Ledger 列抄到 `archive/TASKS_ARCHIVE.md`。

---

## Ledger 總表（活卡）

| 卡ID | Initiative | 級別 | 功能 | owner | 分支／worktree | iteration | 交付狀態 | 部署狀態 | 最後交接 |
|---|---|---|---|---|---|---|---|---|---|
| _（新任務加一列；卡明細由 [`tasks-card.md`](tasks-card.md) 建 `tasks/<卡ID>.md`）_ | | | | | | | | | |

## 依賴註記（相關卡）

> 規劃／大卡分切時據此判定連動範圍。

- _（例：WF-X ← 依賴 WF-Y；WF-Z 與 WF-X 同動 §N）_
