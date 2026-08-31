---
card: WF-REDESIGN-W2A
status: draft-pending-initiative
replacement_rows: [1, 3]
---
> ⛔ 草稿·規劃產出物。各波開卡時逐字搬進卡面（甲′：規格住卡面＋spec_version）；本檔屆時封存。spec_version: 1

# W2A · 規則面整套：canonical 本體＋stage-rules 生效＋tier-rules（T4 紅線）

**痛點（落差）**：canonical §0（505 行，54%）描述的 15 值單欄序列已被決議 8×10 取代但未改寫；§1 角色表 7 角色含三個已裁撤角色；必讀的 §1/§2（34 行）埋在 §0 之後。
**⛔ 非射程**：不動範本／L0／舊模板清理（W2B）；不切換看板實際語彙（歸切換 Initiative——§0 新文帶「尚未切換」標記，沿 §0.1 先例）；不動 cpbl。
**階段計畫**：需求 → 規劃 → 執行 → 審核 → 結案。
**級別依據**：改規則＝AGENTS.md 明文紅線 ⇒ T4。執行 高階型（架構層，AGENTS 路由 Opus／Fable）／查核 高階型＋**跨家族（Codex）**——需求方 2026-08-30 裁定；結案報告閘另經需求方。db-scope none。
**資源**（逐檔）：file:AI_WORKFLOW.md、file:tier-rules.md、file:scripts/pollution-allowlist.json（P1-31 manifest）、file:scripts/pollution_check.py（拋棄式 checker）、file:stage-rules/requirement.md、file:stage-rules/research.md、file:stage-rules/planning.md、file:stage-rules/implementation.md、file:stage-rules/review.md、file:stage-rules/deploy.md、file:stage-rules/maintenance.md、file:stage-rules/closeout.md、file:docs/research/drafts/stage-rules/requirement.md、file:docs/research/drafts/stage-rules/research.md、file:docs/research/drafts/stage-rules/planning.md、file:docs/research/drafts/stage-rules/implementation.md、file:docs/research/drafts/stage-rules/review.md、file:docs/research/drafts/stage-rules/deploy.md、file:docs/research/drafts/stage-rules/maintenance.md、file:docs/research/drafts/stage-rules/closeout.md
**驗收**：
1. §1 換 6 角色表（需求方／人工查核／PM／第二 PM／執行者／查核者）；§1／§2 移至 §0 前
2. §0 重寫為 8 階段 × 10 狀態＋轉移 delta 制，全節帶「本節定義目標狀態，尚未切換；cutover＝切換 Initiative」標記
3. 取代清單 **rows 1、3** 的舊文刪除（⛔ 不留屍體；其餘列各歸其 owner 卡，⛔ 不在本卡動）
4. （P1-31 修訂：raw grep 無法同時表達 0 與豁免、零命中還 rc=1 ⇒ 改 **allowlist-aware checker**）拋棄式檢查腳本：對 post-image 逐符掃描、逐命中輸出 file／line／context；核准例外住 **versioned manifest＝`scripts/pollution-allowlist.json`**（逐 hit 綁 token＋file＋穩定 anchor）；唯一 pass criterion＝`unapproved_count==0`；**negative control 於 temp fixture／worktree 副本執行⛔ 不污染 merge result**；stdout／stderr／rc 分開釘。canonical 行號引用守衛綠
5. （P1-31 併判準）三個腐爛自述（「短版」／「最後核實：<日期>」／行數自述 `[0-9]{3,} ?行`）改為 **checker 的輸入 token**——⛔ 不另宣告 raw count=0；豁免同走 manifest，輸出與 AC4 同一份
6. ⭐（丙修訂）8 份 stage-rules 以 move 生效、節號引用對齊新 canonical；tier-rules 框架層檔上線（環境枚舉與別名表移交 DATABASE_CONTRACT）——規則類整套與 canonical 同一輪跨家族審；stage-rules 內容之紅線滿足另含需求方本 session 逐條確認（§八）
6b.（回應清冊）stage-rules 落檔時注意事項全編號化（F-<階段>-NN），**逐條清冊條文標「目標、尚未生效——機制生效於 W3′」**——決議 §三之二
7. （R3 過渡橫幅）8 份 stage-rules 檔頂各含一行「⚠️ 看板值仍為舊語彙（15 值），對照見決議 §一；切換於切換 Initiative」——`grep -l 舊語彙 stage-rules/*.md | wc -l` 預期 8
**驗證**：跨家族裁決含身分自述；test_canonical_citation_scan 綠；⭐ 對照決議紀錄逐節核對（查核者實跑取代清單全表）。
