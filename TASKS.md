# 任務看板 (Task Board) — ai-workflow

> 本 repo 自身的任務（工作流演進）。規則見 [`AI_WORKFLOW.md`](AI_WORKFLOW.md)。git 是程式碼／文件事實來源；control-plane event log 是作業狀態事實來源；本檔是其人類可讀的 Ledger 投影。
> 交付與部署狀態見 canonical §0。
> **一卡一檔**（canonical §6）：本檔＝**Ledger 索引 only**（常駐輕量），由 event log 產生 current-state；卡片明細一卡一檔於 [`tasks/<卡ID>.md`](tasks/)，按需載入、卡檔不重複狀態。結案卡 `git mv` 進 [`archive/`](archive/)（見 [`archive/TASKS_ARCHIVE.md`](archive/TASKS_ARCHIVE.md)）。

---

## Ledger 總表（活卡）

| 卡ID | Initiative | 級別 | 功能 | owner | 分支／worktree | iteration | 交付狀態 | 部署狀態 | 最後交接 |
|---|---|---|---|---|---|---|---|---|---|
| WF-21 | — | T4 🔴規則 | 審核退回分流與升級計數去誤觸發 | 待指派（跨家族查核或 ruan6047 sign-off） | `ai/gpt-5@codex/WF-21`／目前 checkout | 0 | 🔍待查核 | —不適用 | 2026-07-30T18:51:22+08:00 |

## 依賴註記（相關卡）

> 規劃／大卡分切時據此判定連動範圍（取代逐卡 `[[]]`；結案卡見 archive）。

- WF-21：改動 canonical 審核／升級語意；採用專案 adapter 須同步支援結構化 finding 與 preflight。

---

_結案卡明細 → [`archive/tasks/`](archive/tasks/)；封存 Ledger → [`archive/TASKS_ARCHIVE.md`](archive/TASKS_ARCHIVE.md)。_
