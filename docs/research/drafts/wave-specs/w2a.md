---
card: WF-REDESIGN-W2A
status: draft-pending-initiative
---
> ⛔ 草稿·規劃產出物。各波開卡時逐字搬進卡面（甲′：規格住卡面＋spec_version）；本檔屆時封存。spec_version: 1

# W2A · 規則面整套：canonical 本體＋stage-rules 生效＋tier-rules（T4 紅線）

**痛點（落差）**：canonical §0（505 行，54%）描述的 15 值單欄序列已被決議 8×10 取代但未改寫；§1 角色表 7 角色含三個已裁撤角色；必讀的 §1/§2（34 行）埋在 §0 之後。
**⛔ 非射程**：不動範本／L0／舊模板清理（W2B）；不切換看板實際語彙（波 3——§0 新文帶「尚未切換」標記，沿 §0.1 先例）；不動 cpbl。
**階段計畫**：需求 → 規劃 → 執行 → 審核 → 結案。
**級別依據**：改規則＝AGENTS.md 明文紅線 ⇒ T4。執行 高階型（架構層，AGENTS 路由 Opus／Fable）／查核 高階型＋**跨家族（Codex）**——需求方 2026-08-30 裁定；結案報告閘另經需求方。db-scope none。
**資源**：file:AI_WORKFLOW.md、file:stage-rules/、file:docs/research/drafts/stage-rules/（來源，move）、file:tier-rules.md
**驗收**：
1. §1 換 6 角色表（需求方／人工查核／PM／第二 PM／執行者／查核者）；§1／§2 移至 §0 前
2. §0 重寫為 8 階段 × 10 狀態＋轉移 delta 制，全節帶「本節定義目標狀態，尚未切換；cutover＝波 3」標記
3. 取代清單所列舊文**刪除**（⛔ 不留屍體；歷史在 git）
4. 決議紀錄 §二 污染符對 diff 逐字 grep 零命中（新規則文脈）；canonical 行號引用守衛綠
5. 檔頭「短版」等腐爛自述移除或改可驗形式
6. ⭐（丙修訂）8 份 stage-rules 以 move 生效、節號引用對齊新 canonical；tier-rules 框架層檔上線（環境枚舉與別名表移交 DATABASE_CONTRACT）——規則類整套與 canonical 同一輪跨家族審；stage-rules 內容之紅線滿足另含需求方本 session 逐條確認（§八）
**驗證**：跨家族裁決含身分自述；test_canonical_citation_scan 綠；⭐ 對照決議紀錄逐節核對（查核者實跑取代清單全表）。
