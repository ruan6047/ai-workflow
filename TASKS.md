# 任務看板 (Task Board) — ai-workflow

> 本 repo 自身的任務（工作流演進）。規則見 [`AI_WORKFLOW.md`](AI_WORKFLOW.md)。**git commit trailer 為單一事實來源**。
> 狀態：`📥Backlog → ⏳待執行 → 🔨執行中 → 🔍待查核 → ✅通過 → 🏁完成`／`↩退回`

---

## Ledger 總表

| 卡ID | 功能 | 需求 | 規劃 | 執行(model@tool) | 查核(model@tool) | 分支 | 紅線 | 狀態 |
|---|---|---|---|---|---|---|---|---|
| WF-1 | 建立中央治理 repo + 規則抽出 | 使用者 | 使用者+Claude-Opus | Claude-Opus-4.8@ClaudeCode | 使用者 (pending) | main(初建) | 🔴 | 🔍待查核 |
| WF-2 | §7.1「spec 文件 vs 看板」分工規則 + checklist 去重 | 使用者 | 使用者+Claude-Opus | Claude-Opus-4.8@ClaudeCode | 使用者 (pending) | main(直接) | 🔴 | 🔍待查核 |

---

## 進行中／待辦卡

### WF-1 建立中央治理 repo（規則從各專案抽出集中）  〔🔴紅線：影響全專案〕
- 需求提供方：使用者　規劃：使用者 + Claude-Opus　分支：（初建直接於 main，見下註）
- 執行：Claude-Opus-4.8@ClaudeCode　查核：**使用者（pending）**（規則屬紅線，需人審或跨家族）
- 狀態：🔍待查核　Commit：（本次初始 commit）
- Log：
  - 07-08 規劃 by 使用者（7 點指令）+ Claude-Opus（設計）
  - 07-08 執行 by Claude-Opus@ClaudeCode：建 canonical AI_WORKFLOW + templates + ADOPTION；cpbl/主站改 stub
  - ⚠️ 註：本 repo 首建於 main（尚無分支可開）——屬 bootstrap 例外；**後續規則變更一律走分支 + 獨立審核**
  - 待：使用者 sign-off（紅線）

### WF-2 §7.1「spec 文件 vs 看板」分工規則 + checklist 去重  〔🔴紅線：影響全專案〕
- 需求提供方：使用者　規劃：使用者 + Claude-Opus　分支：（直接於 main，bootstrap 期例外，同 WF-1）
- 執行：Claude-Opus-4.8@ClaudeCode　查核：**使用者（pending）**
- 狀態：🔍待查核　Commit：（本次 commit）
- Log：
  - 07-09 規劃 by 使用者（質疑「規劃文件該存 doc 還是塞看板」）+ Claude-Opus（釐清 spec/看板分工）
  - 07-09 執行 by Claude-Opus@ClaudeCode：canonical 補 §7.1；cpbl CHECKLIST 移除每項重複職責歸屬（留稽核發現）、狀態收斂至 TASKS.md
  - 待：使用者 sign-off

---

## 🏁 已完成

_（無）_
