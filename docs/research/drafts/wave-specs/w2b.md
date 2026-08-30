---
card: WF-REDESIGN-W2B
status: draft-pending-initiative
---
> ⛔ 草稿·規劃產出物。各波開卡時逐字搬進卡面（甲′：規格住卡面＋spec_version）；本檔屆時封存。spec_version: 1

# 波 2b · 規則面配套生效（T2，依賴 2a）

**痛點（落差）**：stage-rules 8 份仍 draft；五份交接文件無範本；分級表無檔；L0 入口未成形；被守衛釘住的舊模板群（tasks-card 等 6 檔）仍會被誤讀為現行。
**⛔ 非射程**：不動 canonical 本體（2a 已完）；不動 CLI 碼（波 3）。
**階段計畫**：需求 → 執行 → 審核 → 結案（內容已確認，跳過研究／規劃）。
**級別依據**：文件生效＋守衛測試同步（CONTRACT_TOOL_RECONCILE）⇒ T2。執行 主力型／查核 主力型。db-scope none。
**資源**：file:stage-rules/、file:templates/、file:AGENTS.md、file:README.md、file:MODEL_ROUTING.md、file:docs/CONTRACT_TOOL_RECONCILE.md、file:cli/tests/test_contract_tool_reconcile.py
**驗收**：
1. 8 份 stage-rules 移出 drafts/ 生效，節號引用對齊 2a 新 canonical
2. 五份交接文件範本（信封＋payload）與分級表兩層檔（框架 tier-rules；含環境枚舉 local|prod＋別名表移交 DATABASE_CONTRACT）上線
3. L0 成形：AGENTS／README 指向「canonical 前兩節＋專案心智模型，其餘用查的」
4. 舊模板群（tasks-card、bug-card、bug-workflow、initiative-card、templates/TASKS.md）移除或改寫，CONTRACT_TOOL_RECONCILE 與其測試同步——CI 全綠
**驗證**：pytest 全綠；污染符 grep 零命中；派工包範本可實際產出一份（對波 3 的派工試打）。
