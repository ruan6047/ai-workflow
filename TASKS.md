# 任務看板 (Task Board) — ai-workflow

> 本 repo 自身的任務（工作流演進）。規則見 [`AI_WORKFLOW.md`](AI_WORKFLOW.md)。**git commit trailer 為單一事實來源**。
> 狀態：`💡需求 → 📥Backlog(待規劃) → ⏳待執行 → 🔨執行中 → 🔍待查核 → ✅通過 → 🏁完成`／`↩退回`
> **card-per-file**（canonical §6.4）：本檔只留 Ledger 索引（常駐、輕量）；每卡完整內容（log／相關任務）住 [`tasks/<卡ID>.md`](tasks/)，**按需讀取**、免整板常駐。完成卡留在 `tasks/`，不再另封存。

---

## Ledger 總表

| 卡ID | 功能 | 需求 | 規劃 | 執行(model@tool) | 查核(model@tool) | 分支 | 紅線 | 狀態 | 卡片 |
|---|---|---|---|---|---|---|---|---|---|
| WF-1 | 建立中央治理 repo + 規則抽出 | ruan6047 | ruan6047+Claude-Opus | Claude-Opus-4.8@ClaudeCode | ruan6047 (sign-off) | main(初建,bootstrap) | 🔴 | 🏁完成 | [WF-1](tasks/WF-1.md) |
| WF-2 | §7.1「spec 文件 vs 看板」分工規則 + checklist 去重 | ruan6047 | ruan6047+Claude-Opus | Claude-Opus-4.8@ClaudeCode | ruan6047 (sign-off) | main(直接,bootstrap) | 🔴 | 🏁完成 | [WF-2](tasks/WF-2.md) |
| WF-3 | §0 總覽（一圖流）+ §0.1 任務類型與適用流程矩陣 | ruan6047 | ruan6047+Claude-Opus | Claude-Opus-4.8@ClaudeCode | ruan6047 (sign-off) | main(直接,bootstrap) | 🔴 | 🏁完成 | [WF-3](tasks/WF-3.md) |
| WF-4 | §9 通用工程紅線（防幻覺/究責/安全，上收自 projectARG）| ruan6047 | ruan6047+Claude-Opus | Claude-Opus-4.8@ClaudeCode | ruan6047 (sign-off) | main(直接,bootstrap) | 🔴 | 🏁完成 | [WF-4](tasks/WF-4.md) |
| WF-5 | §6 身分寫法：人一律用 GitHub 帳號、禁泛稱「使用者」 | ruan6047 | ruan6047+Claude-Opus | Claude-Opus-4.8@ClaudeCode | ruan6047 (sign-off) | main(直接) | ⚪ | 🏁完成 | [WF-5](tasks/WF-5.md) |
| WF-6 | §2 拆出「需求」階段（三→四階段）：企劃提需求可暫不規劃 + §0/§1/§7 同步 | ruan6047 | ruan6047+Claude-Opus | Claude-Opus-4.8@ClaudeCode | ruan6047 (sign-off) | ai/…/WF-6 (PR#1) | 🔴 | 🏁完成 | [WF-6](tasks/WF-6.md) |
| WF-7 | 任務卡拆獨立檔（card-per-file）+ §7 加「相關任務」欄 | ruan6047 | ruan6047+Claude-Opus | Claude-Opus-4.8@ClaudeCode | ruan6047 (sign-off) | ai/…/WF-7 (直接 merge) | 🔴 | 🏁完成 | [WF-7](tasks/WF-7.md) |

---

## 進行中／待辦卡

_（無）_

> 完整卡片（含 log、相關任務）一律在 [`tasks/`](tasks/)；本表只反映狀態索引。
