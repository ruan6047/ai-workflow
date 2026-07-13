# 任務看板 (Task Board) — ai-workflow

> 本 repo 自身的任務（工作流演進）。規則見 [`AI_WORKFLOW.md`](AI_WORKFLOW.md)。**git commit trailer 為單一事實來源**。
> 交付：`💡需求 → 📥Backlog → ⏳待執行 → 🔨執行中 → 🔍待查核 → ✅通過 → 📦已合併 → 🏁完成`／`↩退回`；部署狀態獨立，見 canonical §3.2。
> **一卡一檔**（canonical §6.3/§6.4）：本檔＝**Ledger 索引 only**（常駐輕量），**狀態只住此表**；卡片明細一卡一檔於 [`tasks/<卡ID>.md`](tasks/)，按需載入、卡檔不重複狀態。結案卡 `git mv` 進 [`archive/`](archive/)（見 [`archive/TASKS_ARCHIVE.md`](archive/TASKS_ARCHIVE.md)）。

---

## Ledger 總表（活卡）

| 卡ID | 功能 | 需求 | 執行(model@tool) | 查核(model@tool) | 分支 | 紅線 | 交付狀態 | 部署狀態 |
|---|---|---|---|---|---|---|---|---|
| _（無活卡）_ | | | | | | | | |

## 依賴註記（相關卡）

> 規劃／大卡分切時據此判定連動範圍（取代逐卡 `[[]]`；結案卡見 archive）。

- _（無活卡）_

---

_結案卡明細 → [`archive/tasks/`](archive/tasks/)；封存 Ledger → [`archive/TASKS_ARCHIVE.md`](archive/TASKS_ARCHIVE.md)。_
