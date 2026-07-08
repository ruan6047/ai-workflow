# 新專案採用指南 (Adoption)

讓一個 `~/Dev/<專案>` 納入本 AI 協作治理，三步：

## 1. 放工作流 stub
複製 [`templates/project-stub.md`](templates/project-stub.md) → `<專案>/docs/AI_WORKFLOW.md`。
（stub 指向本 canonical + 核心鐵律速查；**不複製全文**，規則只有一個家。）

## 2. 起任務看板
複製 [`templates/TASKS.md`](templates/TASKS.md) → `<專案>/docs/TASKS.md`，把 `<專案名>` 換掉。
此後該專案所有任務卡／log 都住這裡（**不集中到本 repo**）。

## 3. CLAUDE.md 加指引
在 `<專案>/CLAUDE.md` 頂部加一行：
```
> 多 AI 協作前先讀 docs/AI_WORKFLOW.md（stub → canonical ~/Dev/ai-workflow）；任務看板 docs/TASKS.md。
```

## 完成後
- 該專案即受本機制管理：人工派工、分支制、實作/審核分離、只有 main 已審核可部署、commit trailer 留痕。
- 規則有更新 → **只改本 repo `AI_WORKFLOW.md`**；各專案 stub 指針不變、無需同步。

## 已採用專案
- `cpbl-analytics`（submodule of PersonalWebsite）
- `PersonalWebsite`（主站）
