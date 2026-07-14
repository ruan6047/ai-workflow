# 任務看板 (Task Board) — <專案名>

> 進度追蹤。規則見 canonical [`~/Dev/ai-workflow/AI_WORKFLOW.md`](../../ai-workflow/AI_WORKFLOW.md)（本專案 stub：[`AI_WORKFLOW.md`](AI_WORKFLOW.md)）。
> **git commit trailer 為單一事實來源**，本檔為人類可讀總覽；衝突以 git 為準。
> 交付：`💡需求 → 📥Backlog → ⏳待執行 → 🔨執行中 → 🔍待查核 → ✅通過 → 📦已合併 → 🏁完成`／`↩退回`。
> 部署：`—不適用`，或 `⏸未部署 → 🚀待部署 → ⏳部署中 → ✅已部署 → 🧪驗證中 → ✅已驗證`；失敗為 `❌部署失敗`／`⏪已回滾`。詳見 canonical §3.2。
> **一卡一檔**（canonical §6.3/§6.4）：本檔＝**Ledger 索引 only**（常駐輕量），**狀態只住此表**；卡片明細一卡一檔於 `tasks/<卡ID>.md`（範本 [`tasks-card.md`](tasks-card.md)），按需載入。結案卡 `git mv` 進 `archive/tasks/`、Ledger 列抄到 `archive/TASKS_ARCHIVE.md`。

---

## Ledger 總表（活卡）

| 卡ID | 功能 | 需求 | 執行(model@tool) | 查核(model@tool) | 分支 | 紅線 | 交付狀態 | 部署狀態 |
|---|---|---|---|---|---|---|---|---|
| _（新任務加一列；卡明細由 [`tasks-card.md`](tasks-card.md) 建 `tasks/<卡ID>.md`）_ | | | | | | | | |

## 依賴註記（相關卡）

> 規劃／大卡分切時據此判定連動範圍。

- _（例：WF-X ← 依賴 WF-Y；WF-Z 與 WF-X 同動 §N）_
