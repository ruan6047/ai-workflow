# 任務看板 (Task Board) — ai-workflow

> 本 repo 自身的任務（工作流演進）。規則見 [`AI_WORKFLOW.md`](AI_WORKFLOW.md)。**git commit trailer 為單一事實來源**。
> 交付：`💡需求 → 📥Backlog → ⏳待執行 → 🔨執行中 → 🔍待查核 → ✅通過 → 📦已合併 → 🏁完成`／`↩退回`；部署狀態獨立，見 canonical §3.2。
> **一卡一檔**（canonical §6.3/§6.4）：本檔＝**Ledger 索引 only**（常駐輕量），**狀態只住此表**；卡片明細一卡一檔於 [`tasks/<卡ID>.md`](tasks/)，按需載入、卡檔不重複狀態。結案卡 `git mv` 進 [`archive/`](archive/)（見 [`archive/TASKS_ARCHIVE.md`](archive/TASKS_ARCHIVE.md)）。

---

## Ledger 總表（活卡）

| 卡ID | 功能 | 需求 | 執行(model@tool) | 查核(model@tool) | 分支 | 紅線 | 交付狀態 | 部署狀態 |
|---|---|---|---|---|---|---|---|---|
| [WF-11](tasks/WF-11.md) | 退回／修復卡生命週期與 worktree 收尾 | ruan6047 | Opus-4.8@Claude Code | 待指派（**須換家族或 ruan6047 sign-off**） | `ai/opus-4.8/WF-11` | 🔴 | 🔍待查核 | —不適用 |

## 依賴註記（相關卡）

> 規劃／大卡分切時據此判定連動範圍（取代逐卡 `[[]]`；結案卡見 archive）。

- **WF-11**：無依賴。條文來源為 cpbl-analytics 2026-07-15 事故（RECORD-API1／RECORD-API1-FIX1）；**執行者即當事 AI**，查核獨立性尤其重要。

---

_結案卡明細 → [`archive/tasks/`](archive/tasks/)；封存 Ledger → [`archive/TASKS_ARCHIVE.md`](archive/TASKS_ARCHIVE.md)。_
