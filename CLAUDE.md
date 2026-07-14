# CLAUDE.md — ai-workflow 專案 AI 運行準則

本 repo 是**跨專案 AI 協作治理的 canonical 來源**。它**受自己定義的機制管理**（dogfooding）。

> **規則本體＝ [`AI_WORKFLOW.md`](AI_WORKFLOW.md)**（唯一權威）。本 repo 的任務看板／log＝[`TASKS.md`](TASKS.md)。

## 在本 repo 工作時
- 改規則（`AI_WORKFLOW.md`）＝一張任務卡：**開分支 `ai/<模型@工具>/<卡ID>` → 獨立審核（≠ 執行者）→ merge main**。規則屬「錯了影響全專案」→ 視為 **🔴紅線**，審核**必換模型家族或使用者 sign-off**。
- 規則更新後**不需同步各專案**（各專案只放指向本檔的 stub、不複製全文）。
- commit 一律加 trailer：`Requested-by / Planned-by / Implemented-by / Reviewed-by`（見 AI_WORKFLOW §6）。

## 模型路由
完整分級見 `AI_WORKFLOW.md` §10。本 repo 幾乎全是文件治理：一般修訂用 L2；架構／改規則用 L3，只有多日或極難工作才升 L4；純機械文字可用 L1。規則正確性屬紅線，查核必換模型家族或由使用者 sign-off。
