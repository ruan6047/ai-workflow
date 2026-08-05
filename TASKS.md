# 任務看板 (Task Board) — ai-workflow

> 本 repo 自身的任務（工作流演進）。規則見 [`AI_WORKFLOW.md`](AI_WORKFLOW.md)。git 是程式碼／文件事實來源；control-plane event log 是作業狀態事實來源；本檔是其人類可讀的 Ledger 投影。
> 交付與部署狀態見 canonical §0。
> **一卡一檔**（canonical §6）：本檔＝**Ledger 索引 only**（常駐輕量），由 event log 產生 current-state；卡片明細一卡一檔於 [`tasks/<卡ID>.md`](tasks/)，按需載入、卡檔不重複狀態。結案卡 `git mv` 進 [`archive/`](archive/)（見 [`archive/TASKS_ARCHIVE.md`](archive/TASKS_ARCHIVE.md)）。

---

## Ledger 總表（活卡）

| 卡ID | Initiative | 級別 | 功能 | owner | 分支／worktree | iteration | 交付狀態 | 部署狀態 | 最後交接 |
|---|---|---|---|---|---|---|---|---|---|
| [WF-22](tasks/WF-22.md) | WF-22 | T3 | 新治理落地（Initiative 父卡；13 項決議） | ruan6047（決策）＋PM 祕書（寫入） | — | 0 | 🚧進行中 | —不適用 | 2026-08-04T20:16:50+08:00 |
| [WF-22-CLI2](tasks/WF-22-CLI2.md) | WF-22 | T2 | 鏈深與 iteration 的寫入路徑（CLI1 查核 F1 追卡） | Claude Sonnet 5@Claude Code | `ai/claude-sonnet-5/WF-22-CLI2 @ .claude/worktrees/wf-22-cli2-execution` | 0 | 🚧進行中 | —不適用 | 2026-08-05T10:30:00+08:00 |
| [INIT-AIWF-PRODUCT1](tasks/INIT-AIWF-PRODUCT1.md) | INIT-AIWF-PRODUCT1 | T4 | ai-workflow 產品化（占位；60 天 dogfood＝Discovery） | ruan6047（動工 Gate） | — | 0 | 💡需求 | —不適用 | 2026-08-04T20:16:50+08:00 |

## 依賴註記（相關卡）

> 規劃／大卡分切時據此判定連動範圍（取代逐卡 `[[]]`；結案卡見 archive）。

- `WF-22` 基線＝cpbl-analytics `docs/research/WORKFLOW-REVIEW-2026-08-04.md`（913223e）；**Wave 1 已完結（2026-08-04）**：`WF-22-CLI1` 與 cpbl `OPS-STATE-PLANE-MIG1` 皆 🏁；**cutover 已宣告**（cpbl 終筆 `8271d7c`），Issues＋Project #4 為唯一狀態面、wfcli 唯一寫入通道。追卡 `WF-22-CLI2` 在 Backlog。Wave 2 canonical 文本子卡屆時開，不預開。
- `INIT-AIWF-PRODUCT1` 的 Discovery＝WF-22 落地後 60 天 dogfood（至約 2026-10-03）；動工 Gate：商業評估 grilling＋需求方核可。
- （WF-21 已結案 🏁 b113617；review preflight／escalation 契約已入 canonical §3／§4.1／§5 與 templates/review-escalation.md；cpbl adapter 於 cpbl-analytics#40 同步採用）

---

_結案卡明細 → [`archive/tasks/`](archive/tasks/)；封存 Ledger → [`archive/TASKS_ARCHIVE.md`](archive/TASKS_ARCHIVE.md)。_
