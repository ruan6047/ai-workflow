# ai-workflow — 跨專案 AI 協作治理 (Governance)

多 AI／多模型協作的**中央治理專案**。規則只有一個家：本 repo。各專案採用後，只在自己 repo 放**指向本檔的 stub**與**自己的任務看板**；部署平台由各專案自訂，依 canonical contract 回報狀態。

## 這是什麼／不是什麼
- **是**：規則的單一權威來源（who plans / implements / reviews、分支制、部署閘門、獨立性紅線、留痕格式）。
- **不是**：任務集中地。**各專案的任務 log 住各專案自己的 `docs/TASKS.md`**。

## 結構
```
ai-workflow/
├── AI_WORKFLOW.md   # ★ CANONICAL 規則（唯一權威）
├── ADOPTION.md      # 新專案如何採用（3 步）
├── TASKS.md         # 本 repo 自身的任務看板（工作流演進；自我治理 dogfood）
├── CLAUDE.md        # 本 repo 的 AI 運行準則
└── templates/
    ├── project-stub.md   # 丟進各專案 docs/AI_WORKFLOW.md 的 stub
    ├── TASKS.md          # 各專案任務看板範本
    ├── discovery-brief.md # 需求發現與人類確認範本
    ├── research-plan.md   # 研究假設、證據與限制範本
    ├── design-brief.md    # 使用流程、狀態與可用性驗收範本
    └── initiative-card.md # 大型工作的 spec 基線與依賴範本
```

## 快速上手
新專案採用 → 見 [`ADOPTION.md`](ADOPTION.md)。核心規則 → 見 [`AI_WORKFLOW.md`](AI_WORKFLOW.md)。

## 自我治理 (dogfooding)
本 repo 也**受自己的機制管理**：改規則＝開分支 `ai/<模型>/<卡ID>` → 獨立審核 → merge main；卡片 log 見 [`TASKS.md`](TASKS.md)。
