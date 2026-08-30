---
card: WF-REDESIGN-W2B
status: draft-pending-initiative
replacement_rows: []（機械配套，無取代列）
---
> ⛔ 草稿·規劃產出物。各波開卡時逐字搬進卡面（甲′：規格住卡面＋spec_version）；本檔屆時封存。spec_version: 1

# W2B · 機械配套（T2，依賴 W2A；⛔ 不含規則制定）

**痛點（落差）**：五份交接文件無範本；L0 入口未成形；被守衛釘住的舊模板群（tasks-card 等 6 檔）仍會被誤讀為現行。（stage-rules 與 tier-rules 依 P1-02 丙移入 W2A——規則類⛔ 不在本卡。）
**⛔ 非射程**：不動 canonical 本體（2a 已完）；不動 CLI 碼（波 3）。
**階段計畫**：需求 → 執行 → 審核 → 結案（內容已確認，跳過研究／規劃）。
**級別依據**：僅機械配套（範本新檔／指向修正／清理）＋守衛測試同步；⛔ 不制定任何規則 ⇒ T2 成立（P1-02 丙：規則類已移 W2A，⛔ 非降級）。硬依賴：W2A 終態後才可開工。執行 主力型／查核 主力型。db-scope none。
**資源**：file:templates/、file:AGENTS.md、file:README.md、file:MODEL_ROUTING.md、file:docs/CONTRACT_TOOL_RECONCILE.md、file:cli/tests/test_contract_tool_reconcile.py
**驗收**：
1. 五份交接文件範本（信封＋payload）上線
2. L0 成形：AGENTS／README 指向「canonical 前兩節＋專案心智模型，其餘用查的」
3. 舊模板群（tasks-card、bug-card、bug-workflow、initiative-card、templates/TASKS.md）移除或改寫，CONTRACT_TOOL_RECONCILE 與其測試同步——CI 全綠
**驗證**：pytest 全綠；污染符 grep 零命中；派工包範本可實際產出一份（對波 3 的派工試打）。
