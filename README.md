# ai-workflow — 跨專案 AI 協作治理 (Governance)

多 AI／多模型協作的**中央治理專案**。規則只有一個家：本 repo。各專案採用後，只在自己 repo 放**指向本檔的 stub**與**自己的任務看板**；部署平台由各專案自訂，依 canonical contract 回報狀態。

## 這是什麼／不是什麼
- **是**：規則的單一權威來源（who plans / implements / reviews、分支制、部署閘門、獨立性紅線、留痕格式）。
- **不是**：任務集中地。**各專案的任務 log 住各專案自己的 `docs/TASKS.md`**。

## 結構
```
ai-workflow/           # 依檔名排序，與 `ls` 實況一致
├── ADOPTION.md      # 新專案如何採用（3 步）
├── AGENTS.md        # 本 repo 的 AI 運行準則（工具中立版）
├── AI_WORKFLOW.md   # ★ CANONICAL 規則（唯一權威）
├── CLAUDE.md        # 本 repo 的 AI 運行準則（Claude Code）
├── MIGRATION.md     # 舊版工作流專案的升級指南
├── MODEL_ROUTING.md # 模型路由範本（可替換操作知識，非流程鐵律）
├── README.md        # 本檔
├── TASKS.md         # 本 repo 自身的任務看板（工作流演進；自我治理 dogfood）
├── archive/         # 結案卡與 Ledger 封存
├── cli/             # wfcli——control plane 唯一寫入通道，見 canonical §4.3
├── tasks/           # 本 repo 的活卡（一卡一檔）
└── templates/            # 依檔名排序，與 `ls templates/` 實況一致
    ├── TASKS.md          # 各專案任務看板範本（Ledger 索引 only）
    ├── baseline-cascade.md # 基線變更的凍結、影響評估與傳播程序
    ├── bug-card.md       # 快線 bug 卡範本
    ├── bug-workflow.md   # bug 分級與處理流程
    ├── control-plane-contract.md # 協作狀態面與本機資源鎖契約範本
    ├── database-contract.md # DB 引擎、migration、namespace 與回滾契約範本
    ├── design-brief.md   # 使用流程、狀態與可用性驗收範本
    ├── discovery-brief.md # 需求發現、對抗式質詢與人類確認範本
    ├── dispatch-package.md # 派工包範本（canonical §6.1 六條標準條款）
    ├── handoff-contract.md # 已推送完整 SHA 的跨 writer handoff 契約範本
    ├── initiative-card.md # 大型工作的 spec 基線與依賴範本
    ├── project-stub.md   # 丟進各專案 docs/AI_WORKFLOW.md 的 stub
    ├── research-plan.md  # 研究假設、證據與限制範本
    ├── review-escalation.md # preflight／退回／升級的事件欄位契約
    ├── review-prompt.md  # 跨家族查核詞範本（canonical §5.1／§5.2）
    ├── statistical-redline.md # 統計／ML 與資料正確性紅線區塊範本
    ├── tasks-card.md     # 一卡一檔的任務卡範本
    └── worktree-lifecycle.md # worktree 註冊、交接與結案收尾清單
```

## 快速上手
新專案採用 → 見 [`ADOPTION.md`](ADOPTION.md)。核心規則 → 見 [`AI_WORKFLOW.md`](AI_WORKFLOW.md)。
舊版專案升級 → 見 [`MIGRATION.md`](MIGRATION.md)。

## 自我治理 (dogfooding)
本 repo 也**受自己的機制管理**：改規則＝開分支 `ai/<模型>/<卡ID>` → 獨立審核 → merge main；卡片 log 見 [`TASKS.md`](TASKS.md)。
