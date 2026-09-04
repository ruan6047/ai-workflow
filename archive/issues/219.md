# #219 WF-REDESIGN-W2A 規則面整套：canonical 本體＋stage-rules 生效＋tier-rules（四波五卡 W2A）
- state: closed  created: 2026-08-31T18:51:46Z  closed: 2026-09-01T10:37:07Z
- url: https://github.com/ruan6047/ai-workflow/issues/219
- comments: 15

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 高階型；架構層規則改版（canonical §0/§1 重寫＋8 份 SOP 生效），AGENTS 路由 Opus／Fable）　查核：待指派（建議 高階型；改規則＝AGENTS 明文紅線 T4；查核須跨家族（Codex，需求方 2026-08-30 裁定），獨立性要求疊加於層級之上；結案報告閘另經需求方）
- Initiative：WF-REDESIGN1　spec 基線：ai-workflow 93bb8c086f0cf8870537390511b5f0aa2d037c97
- DB：db_scope=none
- 服務的原始目標：可稽核＋防低級事故＋流程順暢——canonical 描述的狀態語彙與角色表已被決議取代但未改寫，讀者會把過時條文當現行（可稽核軸）

## 簡介
<!-- card-brief:begin -->
適用時機：四波五卡 W2A——規則面整套：canonical 本體改寫（§0 重寫為 8 階段×10 狀態、§1 換 6 角色表、§1/§2 前移）＋8 份 stage-rules SOP 以 move 生效＋tier-rules 框架層檔上線＋污染符 allowlist-aware checker。階段計畫：需求→規劃→執行→審核→結案。級別依據：改規則＝AGENTS.md 明文紅線 ⇒ T4；查核須跨家族（Codex，需求方 2026-08-30 裁定），結案報告閘另經需求方。spec_version: 2（甲′ 規格住卡面；來源 wave-specs/w2a.md 屆時封存，⚠️ 該檔自規劃 Gate 93bb8c0 起未變）。

⛔ 非射程：不動範本／L0／舊模板清理（W2B）；不切換看板實際語彙（歸切換 Initiative——§0 新文帶「尚未切換」標記，沿 §0.1 先例）；不動 cpbl。

**守衛跟隨（開卡時預先宣告，⛔ 非內容改動）**：8 份 SOP 由 `docs/research/drafts/stage-rules/` 搬到 `stage-rules/` 會斷開 `scripts/prose_number_scan.py` 的 corpus glob 與 `prose-number-inventory.json` 的 path 綁定（W0 已有先例：不同步即死條目、CI 紅）。故資源宣告含該二檔，執行時須同步改寫 inventory 之 path 並跑到七項計數全零。

**spec_version 2 修訂（需求方 2026-09-01 裁定，回應查核 R1-001／R1-002）**：AC3 措辭修訂為「刪除十五值**作為轉移規則的規範身分**；cutover 前**值域現況可保留**；同段其他仍有效約束（如「新寫入不得用」「不可覆寫 event」）**逐句標明效力與 owner**」——⛔ 不得以整段「非條文」覆蓋仍具強制力的句子。新增 AC8（§0.1 退役四步）與 AC9（§3 Gate 塊處置），⛔ 均不擴及 §3.1／§3.2／§3.3。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：canonical §0（505 行，54%）描述的 15 值單欄序列已被決議 8×10 取代但未改寫；§1 角色表 7 角色含三個已裁撤角色；必讀的 §1/§2（34 行）埋在 §0 之後。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:AI_WORKFLOW.md",
    "file:tier-rules.md",
    "file:scripts/pollution-allowlist.json",
    "file:scripts/pollution_check.py",
    "file:stage-rules/requirement.md",
    "file:stage-rules/research.md",
    "file:stage-rules/planning.md",
    "file:stage-rules/implementation.md",
    "file:stage-rules/review.md",
    "file:stage-rules/deploy.md",
    "file:stage-rules/maintenance.md",
    "file:stage-rules/closeout.md",
    "file:docs/research/drafts/stage-rules/requirement.md",
    "file:docs/research/drafts/stage-rules/research.md",
    "file:docs/research/drafts/stage-rules/planning.md",
    "file:docs/research/drafts/stage-rules/implementation.md",
    "file:docs/research/drafts/stage-rules/review.md",
    "file:docs/research/drafts/stage-rules/deploy.md",
    "file:docs/research/drafts/stage-rules/maintenance.md",
    "file:docs/research/drafts/stage-rules/closeout.md",
    "file:docs/research/drafts/prose-number-inventory.json",
    "file:scripts/prose_number_scan.py",
    "file:cli/tests/test_prose_number_scan.py",
    "file:cli/tests/test_pollution_check.py"
  ]
}
```
<!-- resource-claims:end -->

## 卡面表單
<!-- card-face-form:v1:begin -->
```json
{
  "list_convergence": [],
  "schema_version": "1",
  "stage_plan": [
    {
      "goal": "清單項 #219 升級為卡，規格逐字住卡面",
      "stage": "需求"
    },
    {
      "goal": "承接 Initiative 層規劃 Gate（93bb8c0），本卡不另產出",
      "stage": "規劃"
    },
    {
      "goal": "canonical §0/§1 改寫＋8 份 SOP move 生效＋tier-rules 上線＋污染符 checker",
      "stage": "執行"
    },
    {
      "goal": "跨家族（Codex）逐節對照決議紀錄；紅線滿足另含需求方逐條確認",
      "stage": "審核"
    },
    {
      "goal": "結案報告七段經需求方確認；規格封存＋守衛跟隨",
      "stage": "結案"
    }
  ],
  "tier_basis": {
    "blast_radius": "全 repo 所有在飛與未來卡；cpbl 側經 stub 讀 canonical 亦受影響",
    "recoverability": "可逆（git revert）；但錯誤條文在被 revert 前會被其他卡引為判準",
    "sensitive_surfaces": "canonical AI_WORKFLOW.md 本體與 8 份 stage-rules 生效條文——規則面即所有卡的判準來源"
  }
}
```
<!-- card-face-form:v1:end -->

## 驗收條件

- [ ] §1 換 6 角色表（需求方／人工查核／PM／第二 PM／執行者／查核者）；§1／§2 移至 §0 前
- [ ] §0 重寫為 8 階段 × 10 狀態＋轉移 delta 制，全節帶「本節定義目標狀態，尚未切換；cutover＝切換 Initiative」標記　⚠️ **2026-09-01 裁定**：本條「全節」與 AC3v2「⛔ 不得整段覆蓋仍具強制力的句子」字面衝突時**以 AC3v2 為準**——標記⛔ 不得覆蓋仍具強制力的句子（沿 canonical 既有先例：「尚未切換」標記明文不涵蓋變更級別段）
- [ ] 取代清單 rows 1、3 的舊文處置（**spec_version 2 修訂**）：刪除的是十五值**作為轉移規則的規範身分**；cutover 前**值域現況可保留**為敘述（row 2 歸切換 Initiative）；同段其他仍有效約束逐句標明效力與 owner；⛔ 不得以整段「非條文」覆蓋仍具強制力的句子；row 3（§1 角色表）舊文刪除⛔ 不留屍體
- [ ] （P1-31 修訂：raw grep 無法同時表達 0 與豁免、零命中還 rc=1 ⇒ 改 **allowlist-aware checker**）拋棄式檢查腳本：對 post-image 逐符掃描、逐命中輸出 file／line／context；核准例外住 **versioned manifest＝`scripts/pollution-allowlist.json`**（逐 hit 綁 token＋file＋穩定 anchor）；唯一 pass criterion＝`unapproved_count==0`；**negative control 於 temp fixture／worktree 副本執行⛔ 不污染 merge result**；stdout／stderr／rc 分開釘。canonical 行號引用守衛綠
- [ ] （P1-31 併判準）三個腐爛自述（「短版」／「最後核實：<日期>」／行數自述 `[0-9]{3,} ?行`）改為 **checker 的輸入 token**——⛔ 不另宣告 raw count=0；豁免同走 manifest，輸出與 AC4 同一份
- [ ] ⭐（丙修訂）8 份 stage-rules 以 move 生效、節號引用對齊新 canonical；tier-rules 框架層檔上線（環境枚舉與別名表移交 DATABASE_CONTRACT）——規則類整套與 canonical 同一輪跨家族審；stage-rules 內容之紅線滿足另含需求方本 session 逐條確認（§八）
- [ ] （回應清冊）stage-rules 落檔時注意事項全編號化（F-<階段>-NN），**逐條清冊條文標「目標、尚未生效——機制生效於 W3′」**——決議 §三之二
- [ ] （R3 過渡橫幅）8 份 stage-rules 檔頂各含一行「⚠️ 看板值仍為舊語彙（15 值），對照見決議 §一；切換於切換 Initiative」——`grep -l 舊語彙 stage-rules/*.md | wc -l` 預期 8
- [ ] （R1-002 裁定·§0.1 退役四步）①§0.1 加 superseded 標記並移除「本節定義目標狀態」自稱（退役後 canonical 內該宣告僅存 §0.0 一處）②「結案觸發＝最後一個適用階段進入完成」搬入 `stage-rules/closeout.md` 並改寫其進入子句，須涵蓋實測三條入邊：審核 APPROVE／研究 `不可判定 → 結案／完成`／維護 `運行中 → 結案／完成`③「為什麼要兩軸」⛔ 不搬（§0.0 已以「階段是有人做判斷的地方」與「專屬狀態判準＝會不會丟失行為差別」承載）④**§0.1 自身的執行者狀態表**（⚠️ 2026-09-01 更正：原寫「§0.2 D 表」係 PM 節次誤植；實查該表位於 §0.1 節內、§0.2 的 D1–D7 對 §0.1 零引用）之 5 列逐列補承接者（其中 2 列已有），⛔ 不只改指標
- [ ] （R1-002 裁定·§3 Gate 塊處置）只處置 §3 前言三條 Gate 定義（Discovery／Design／Plan）＋ mermaid 圖 ＋ `:34` 的 Coordinator 映射句（映射句與 §1「⛔ 不得自行推對應關係」二擇一，⛔ 不得並存）；⛔ **§3.1 規劃閘門三級制不得退役**（規劃深度政策，與 §0「變更級別」的最低閘門為兩回事，且「尚未切換」標記明文不涵蓋變更級別段）；⛔ §3.2／§3.3 一字不動（`--chain-depth` 正在消費）；外部指向（MODEL_ROUTING／ADOPTION／tasks/INIT-AIWF-PRODUCT1）⛔ 不在本卡射程，另登清單項

## 驗證

- [ ] 跨家族裁決含身分自述
- [ ] test_canonical_citation_scan 綠
- [ ] ⭐ 對照決議紀錄逐節核對（查核者實跑取代清單全表）
- [ ] prose_number_scan 七項計數全零（守衛跟隨搬移後）

## Log

- 2026-09-01T14:05:01+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-09-01T14:05:01+08:00 upgrade by wf-cli → 由待審清單項 https://github.com/ruan6047/ai-workflow/issues/219 升級；清單項原文 sha256:ad7f20bd25f4560096d48af75043859c19a4ab36c10ff49eb42670abd70da6fe（原文見平台 userContentEdits 前一版）。
- 2026-09-01T14:25:07+08:00 assign by wf-cli → owner session e34c8786-1249-41ff-ad3d-a8e31915dbfb@Claude Code（高階型）；分支worktree claude/wf-redesign-w2a-rules-0631e8 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-redesign-w2a-rules-0631e8；交付狀態 🔨執行中；實際能力層級 高階型（與卡面建議 高階型 相符；備註：符合卡面建議（高階型）；實際模型 claude-opus-5 由 transcript 機械核出（~/.claude/projects/-Users-ruanruan-Dev-ai-workflow--claude-worktrees-wf-redesign-w2a-rules-0631e8/e34c8786-....jsonl 之 model 欄，⛔ 非自述））；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-09-01T15:13:42+08:00 amend by wf-cli（op b01330f3）→ 資源宣告：原值指紋 sha256:ca07c5969a808aae0ba211e53265bd20051ab4536eb1a201df0aa7908959e59e (1038 bytes) → 新值指紋 sha256:727ac76d403f124041aacfbee6bec635fd72b65a43771aac66e2db11090f9bf4 (945 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 執行者依紅線上呈之越界一檔補宣告：cli/tests/test_prose_number_scan.py 與 scripts/prose_number_scan.py 由不變量 len(_ID_PAIR_TABLE)==len(ID_PATS) 機械綁定，⛔ 不可分改；⚠️ 資源整份取代，其餘 22 項逐字沿用。
- 2026-09-01T15:24:57+08:00 handoff by wf-cli → owner Codex@OpenAI（跨家族查核）；iteration 0；SHA 27ff0b2f28d4d26f48c640e056044222ea5e968e；階段 執行；踩坑回應 13 族（已檢查 12／不適用 0／發現 1）；證據 交付報告＝#219 issuecomment-5490217865（執行者本人貼，入口 SHA＝head）；PM 收件初審三項通過——獨立實跑 prose scan 204 七項全零／citation scan rc=0／AC7 oracle 8／pollution checker unapproved_count=0；四 commit trailers 各 4 欄；CI run 33480022207 success headSha 逐字相符；AC 著落可見（§1/§2 前移、6 角色表、尚未切換標記、stage-rules 12 檔、F- 編號化、未生效標記）。越界一檔已補宣告（op b01330f3）。三件上呈之 PM 處置：canonical §3 兩處無 owner→開清單項 #228（⛔ 不擴本卡射程）；AC3 降階不刪→交查核判內容；DI 專案層槽位→記入 #221 供 W3′ 開卡採用（⛔ 不動本卡）。
- 2026-09-01T15:40:47+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 Codex@OpenAI（gpt-5.6-sol，session 01a05bdd-5a42-7192-a956-a3e607a6f322）；core_pain_resolved no；self_run 8 項；findings 3 項（blocking 3）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-REDESIGN-W2A-e0-27ff0b2f28d4d26f48c640e056044222ea5e968e。
- 2026-09-01T16:45:42+08:00 amend by wf-cli（op 18acf402）→ 簡介：原值指紋 sha256:ef08776fd501a5da608e9ffd43298a165d6469424ac0d3180949435f740791bd (1220 bytes) → 新值指紋 sha256:f43bd077b73a577b30f6c09326e83c4c600cd8f6bf3d5966dc0ff7dd9d089f99 (1730 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方 2026-09-01 裁定（W2A R1 兩筆 planner finding 之處置，經 PM 十一批對抗研究後收斂，連兩批零實質）：①R1-001→AC3 措辭修訂（刪除的是規範身分、值域現況可留、其他約束逐句標效力與 owner）；②R1-002→納回本卡，新增 AC8（§0.1 退役四步）與 AC9（§3 Gate 塊處置），⛔ 不升級 #228 為前置卡；③spec_version 1→2。⚠️ 研究中撤銷的兩個候選發現：deploy／maintenance SOP 骨架空白屬決議 §十三「未定」已登記（非缺陷）；§3.1 不可退役（活政策）。⚠️ --acceptance 整份取代：原 8 條中僅第 3 條改寫，其餘 7 條逐字沿用。
- 2026-09-01T16:45:42+08:00 amend by wf-cli（op 18acf402）→ 驗收條件：原值指紋 sha256:eec84904253455c22407b96b34bd35de1c62613c209f041894a6671f671f7414 (1929 bytes) → 新值指紋 sha256:dc6e6d5b5bdc2dd1879cd5369ebb3a7777e7b9f3e43066c9c936bb97c692345d (3466 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方 2026-09-01 裁定（W2A R1 兩筆 planner finding 之處置，經 PM 十一批對抗研究後收斂，連兩批零實質）：①R1-001→AC3 措辭修訂（刪除的是規範身分、值域現況可留、其他約束逐句標效力與 owner）；②R1-002→納回本卡，新增 AC8（§0.1 退役四步）與 AC9（§3 Gate 塊處置），⛔ 不升級 #228 為前置卡；③spec_version 1→2。⚠️ 研究中撤銷的兩個候選發現：deploy／maintenance SOP 骨架空白屬決議 §十三「未定」已登記（非缺陷）；§3.1 不可退役（活政策）。⚠️ --acceptance 整份取代：原 8 條中僅第 3 條改寫，其餘 7 條逐字沿用。
- 2026-09-01T17:26:17+08:00 amend by wf-cli（op 60c63644）→ 驗收條件：原值指紋 sha256:5cf6aa590364884c7f7025fc7be1e8cd88b3e4d7322b5029fe575e0b4657d77f (3506 bytes) → 新值指紋 sha256:68e409a7d399bbe5b4cc734f3254ff667e8e7af5bbe9c7e61e9617c5fd586e55 (3917 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R1 修復後之兩項 planner 更正與一項資源補宣告（需求方 2026-09-01 裁定）：①AC8 第 4 步節次誤植更正——PM 原寫「§0.2 D 表」，實查該執行者狀態表位於 §0.1 節內（行序 §0.1 …表… §0.2），§0.2 的 D1–D7 對 §0.1 零引用；⇒ **執行者判斷正確、動對了表**，本次僅更正卡面措辭，⛔ 非要求重做。②AC2「全節帶標記」與 AC3v2 衝突 ⇒ 裁定以 AC3v2 為準（執行者已如此取捨）。③資源補宣告 cli/tests/test_pollution_check.py（本輪新增檔）。⚠️ --acceptance 與 --resources 皆整份取代，其餘逐字沿用。
- 2026-09-01T17:26:17+08:00 amend by wf-cli（op 60c63644）→ 資源宣告：原值指紋 sha256:11bedb61aed24485d90e33a2e73ef40bf0e970fcf62816be5af6c1f2ad07b0f8 (1082 bytes) → 新值指紋 sha256:7c559ac0f28e966b117b63d5da985288a46a87b3cdfe369dbc345abab14f3dd7 (986 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R1 修復後之兩項 planner 更正與一項資源補宣告（需求方 2026-09-01 裁定）：①AC8 第 4 步節次誤植更正——PM 原寫「§0.2 D 表」，實查該執行者狀態表位於 §0.1 節內（行序 §0.1 …表… §0.2），§0.2 的 D1–D7 對 §0.1 零引用；⇒ **執行者判斷正確、動對了表**，本次僅更正卡面措辭，⛔ 非要求重做。②AC2「全節帶標記」與 AC3v2 衝突 ⇒ 裁定以 AC3v2 為準（執行者已如此取捨）。③資源補宣告 cli/tests/test_pollution_check.py（本輪新增檔）。⚠️ --acceptance 與 --resources 皆整份取代，其餘逐字沿用。
- 2026-09-01T17:27:59+08:00 handoff by wf-cli → owner session e34c8786-1249-41ff-ad3d-a8e31915dbfb@Claude Code；iteration 1；SHA 27ff0b2f28d4d26f48c640e056044222ea5e968e；階段 審核；踩坑回應 8 族（已檢查 7／不適用 0／發現 1）；證據 R1 裁決 REQUEST_CHANGES（issuecomment-5490600491，core_pain_resolved=no，3 blocking）⇒ 退回執行者；本筆補記 審核→執行 之轉移。
- 2026-09-01T17:28:21+08:00 handoff by wf-cli → owner Codex@OpenAI（跨家族查核）；iteration 1；SHA 2bd2793a30ce73fe961165d8d97d11f6a63d9fcf；階段 執行；踩坑回應 13 族（已檢查 8／不適用 0／發現 5）；證據 R1 三筆處置完成：交付報告 v2＝issuecomment-5491714806（執行者本人貼，入口 SHA＝head）；PM 收件初審三項通過——獨立實跑 prose 206 七項全零／pollution 16 檔 188 命中自指 143 逐檔逐 token 列計 unapproved_count=0／AC7 oracle 8／六 commit trailers 各 4 欄／CI 33490886848 success headSha 逐字符合／closeout 進入子句已改三條入邊。PM 側裁定：AC2 與 AC3v2 衝突取 AC3v2、AC8 第 4 步節次誤植更正（op 60c63644，⛔ 非要求重做）、資源補宣告 test_pollution_check.py、兩件上呈併入清單項 #228。
- 2026-09-01T17:40:21+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 Codex@OpenAI（gpt-5.6-sol，session 01a05c4e-f0a8-7523-9dc0-30a53f5a07eb）；core_pain_resolved yes；self_run 11 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-REDESIGN-W2A-e0-2bd2793a30ce73fe961165d8d97d11f6a63d9fcf。
- 2026-09-01T17:56:28+08:00 handoff by wf-cli → owner session e34c8786-1249-41ff-ad3d-a8e31915dbfb@Claude Code；iteration 2；SHA 2bd2793a30ce73fe961165d8d97d11f6a63d9fcf；階段 審核；踩坑回應 8 族（已檢查 7／不適用 0／發現 1）；證據 R2 裁決 REQUEST_CHANGES（issuecomment-5492026410，唯一 blocking R2-001，attribution=planner）⇒ 退回；本筆補記 審核→執行 之轉移。
- 2026-09-01T17:56:48+08:00 handoff by wf-cli → owner Codex@OpenAI（跨家族查核）；iteration 2；SHA f61444c65a6d7433f16875d82c3077c7e70c58ac；階段 執行；踩坑回應 13 族（已檢查 11／不適用 0／發現 2）；證據 R2-001 落檔（一 commit 一行）：交付報告 v3＝issuecomment-5492155288（執行者本人貼，入口 SHA＝head）；PM 收件初審三項通過——diff 恰 1 檔 1 行、row #4 承接者已具名 WF-REDESIGN-W3′、grep 尚無具名卡 得 0、CI 33494224826 success headSha 逐字符、入口 SHA＝source_sha。⭐ PM 另複驗自身宣稱：handoff_cmd.py:701 的 if args.status 確為 if/elif 首分支，其後 elif release 才有部署狀態閘門 ⇒ 逃生門描述屬實。
- 2026-09-01T18:05:03+08:00 review by wf-cli → APPROVE（✅通過）；查核者 Codex@OpenAI（gpt-5.6-sol，session 01a05c4e-f0a8-7523-9dc0-30a53f5a07eb）；core_pain_resolved yes；self_run 11 項；findings 0 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-REDESIGN-W2A-e0-f61444c65a6d7433f16875d82c3077c7e70c58ac。
- 2026-09-01T18:36:56+08:00 handoff by wf-cli → owner ruan6047；iteration 2；SHA 950b3e278371e948900dd381cd7b4e595882c6b0；階段 審核；踩坑回應 8 族（已檢查 8／不適用 0／發現 0）；證據 R3 APPROVE（issuecomment-5492309835，findings 0，source_sha f61444c6）；PR #229 squash merge→main 950b3e2（⛔ 非 BEHIND，merge 內容＝審過 SHA）；main 實跑 prose 206 七項全零／pollution unapproved_count=0／AC7 oracle 8／pytest 1617 passed 1 skipped；⭐ 合併 commit 的 trailer 五欄經 interpret-trailers 全數解析（W1 兩種壞法皆已避開）；收尾清理：已清除 worktree；遠端分支 本來就不存在；本地分支 依授權保留（未刪除）。


## Comment 5488443753 · 2026-09-01T03:25:47Z

## 第二 PM 收件裁決

回應 `WF-REDESIGN-W1-R1-3`。⛔ 本裁決只判收件流程，不判提案內容是否正確或是否該做。

1. **出處可指：過**——已指向 `docs/research/WORKFLOW-REDESIGN-2026-08-30.md`，並以父卡 #177 spec 基線與不可變 git 物件 `93bb8c086f0cf8870537390511b5f0aa2d037c97` 提供可指定位；本裁決不核內容真偽。
2. **是觀察不是結論：退回**——「讀者仍會把 15 值序列與 7 角色表當現行」是未附量測的讀者反應推論，依條件 2 有未經量測的因果推論即退。
3. **查重留痕：過**——已逐字列出 `清單`／`W2A`／`W3`／`切換 Initiative` 四個搜尋關鍵字，並記錄命中 #217、#177、#213。
4. **屬哪個 repo：過**——已明示 repo 為 `ai-workflow`。

- **提案者身分三格：過**——GitHub 帳號、session ID、該則訊息定位三格皆有填；依收件規則與本次指示，⛔ 不核對真偽。

**總裁決：退回提案者補。** 任一項退回即退回；第二 PM 不代填。

裁決者身分自述：第二 PM；模型家族＝OpenAI GPT-5；實際模型＝gpt-5.6-sol；session ID＝01a05afc-e755-7840-a9ff-f1c74c3670e7。
timestamp：2026-09-01T11:25:45+08:00（Asia/Taipei）

## Comment 5488457014 · 2026-09-01T03:27:41Z

提案者補正（2026-09-01，回應第二 PM 收件裁決條件 2 退回）：觀察句改純可觀測——移除推論／因果／評價措辭，量測值保留並附量法。請第二 PM 複檢（可併入 W1 R2 同帖）。——提案者＝session cc0a7952@Claude Code

## Comment 5489178593 · 2026-09-01T05:06:09Z

## 第二 PM 收件複檢裁決

回應 `WF-REDESIGN-W1-R1-3`。⛔ 本裁決只判收件流程，不判提案內容是否正確或是否該做。

1. **出處可指：過**——已指向 `docs/research/WORKFLOW-REDESIGN-2026-08-30.md`，並以父卡 #177 spec 基線與不可變 git 物件 `93bb8c086f0cf8870537390511b5f0aa2d037c97` 提供可指定位；本裁決不核內容真偽。
2. **是觀察不是結論：過**——補正後只陳述條文語氣、15 值／7 角色表與過時標記缺席，原讀者反應推論已移除，未預設解法。
3. **查重留痕：過**——已逐字列出 `清單`／`W2A`／`W3`／`切換 Initiative` 四個搜尋關鍵字，並記錄命中 #217、#177、#213。
4. **屬哪個 repo：過**——已明示 repo 為 `ai-workflow`。

- **提案者身分三格：過**——GitHub 帳號、session ID、該則訊息定位三格皆有填；依收件規則與本次指示，⛔ 不核對真偽。

**總裁決：收件通過。** 四項皆過。

裁決者身分自述：第二 PM；模型家族＝OpenAI GPT-5；實際模型＝gpt-5.6-sol；session ID＝01a05afc-e755-7840-a9ff-f1c74c3670e7。
timestamp：2026-09-01T13:06:07+08:00（Asia/Taipei）

## Comment 5489644477 · 2026-09-01T06:05:53Z

open 寫入留痕（2026-09-01）：本卡由清單項 #219 經 `open --from-issue` **就地升級**（W1 新機制首次實戰＝W1 驗證項「W2A 的清單項用本機制實際升級一次」）。⚠️ Project 簡介 TEXT 欄因 1024-byte 上限拒收完整簡介（同 #217 先例），body 權威居所已完整寫入，PM 事後以導出摘要補該欄並註明非恆等——讀規格一律讀 body。

## Comment 5490217865 · 2026-09-01T07:06:30Z

## 交付報告 — WF-REDESIGN-W2A（執行階段 ③）

### 信封

| 欄 | 值 |
|---|---|
| 卡 | `WF-REDESIGN-W2A`（#219），Initiative `WF-REDESIGN1`（#177） |
| session ID | `e34c8786-1249-41ff-ad3d-a8e31915dbfb` |
| **實際模型／卡面建議層級／偏離** | `claude-opus-5`（Claude Opus 5@Claude Code）／建議 高階型／**偏離：無**（實際 高階型）。⚠️ 模型值為自述；機械來源＝`~/.claude/projects/-Users-ruanruan-Dev-ai-workflow--claude-worktrees-wf-redesign-w2a-rules-0631e8/e34c8786-1249-41ff-ad3d-a8e31915dbfb.jsonl` 的 `model` 欄，已由 PM 於 assign 時核出 |
| 分支 | `claude/wf-redesign-w2a-rules-0631e8` |
| worktree | `/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-redesign-w2a-rules-0631e8` |
| **給查核者的入口 SHA** | **`27ff0b2f28d4d26f48c640e056044222ea5e968e`** |
| merge-base（釘死字面） | `f656a678e540d4083740e0f30f1214e887e42c04`（＝推送當時的 `origin/main`） |
| spec 基線 | `93bb8c086f0cf8870537390511b5f0aa2d037c97`；`git diff 93bb8c08 HEAD -- docs/research/drafts/wave-specs/w2a.md` 空 |
| iteration | 0（第一輪） |

工作樹狀態的查詢方法（⛔ 不寫狀態）：`git -C <worktree> status --porcelain=v1`、`git rev-parse HEAD`。

---

### 一 · 做了什麼（四個 commit）

| SHA | 主旨 |
|---|---|
| `a08c57e57c30505e4d8f8a6152920e29c267237e` | `docs(canonical): swap in the six-role table and rewrite §0 to 8×10` |
| `0c555208a54795ab24cdd543d276c8d041f90504` | `docs(stage-rules): enact the eight stage files with numbered notes` |
| `bf4d5df641673bd9f6c567432d330a2b98094b1e` | `docs(tier-rules): land the framework-layer tier wiring` |
| `27ff0b2f28d4d26f48c640e056044222ea5e968e` | `feat(scripts): add the allowlist-aware pollution checker` |

**AC 逐條落點**

- **AC1**　`AI_WORKFLOW.md` §1 角色表 7 → 6（需求方／人工查核／PM／第二 PM／執行者／查核者），舊表整塊刪除；§1＋§1.1＋§2 整塊移到 §0 之前。移動後的節次順序：`## 1.`（第 7 行）→ `## 2.`（第 38 行）→ `## 0.`（第 53 行）→ `## 3.`（第 591 行）。檔案 947 → 989 行。
- **AC2**　新增 `### 0.0 階段與狀態（8 階段 × 10 狀態，轉移 delta 制）`，含 8 階段序列、10 狀態（通用 7 ＋ 專屬 3）、專屬狀態判準、`停止`／`阻塞` 語意、`stage_next[階段][狀態] = BASE | ADD & ~REMOVE`。節首帶標記「**本節定義目標狀態，尚未切換；cutover＝切換 Initiative**」，並逐字寫出該標記涵蓋 §0.0 全節、⛔ 不涵蓋 §0 的類型表與變更級別段。
- **AC3**　row 1（十五值單欄序列**條文**）與 row 3（§1 七角色表）的舊文已刪。⚠️ 十五值本身**保留**為「切換前的現行看板語彙（⛔ 非本節條文）」子節——理由見「四 · 單方面決定 1」。
- **AC4**　`scripts/pollution_check.py` ＋ `scripts/pollution-allowlist.json`。
- **AC5**　三個腐爛自述併為同一支 checker 的輸入 token；canonical 檔頭的「短版權威規則」→「權威規則」。
- **AC6**　八份 stage-rules 由 `docs/research/drafts/stage-rules/` `git mv` 到 `stage-rules/`；`tier-rules.md` 上線。
- **AC6b**　注意事項全編號化 `F-<階段>-NN`；新增「注意事項回應清冊」節，標「目標、尚未生效——機制生效於 W3′」。
- **AC7**　八份檔頂各一行過渡橫幅。

**AC6 的節號引用對齊（實查，⛔ 非推論）**：八份檔內**只有一處** canonical 節次引用——`stage-rules/research.md` 的 `F-研究-13`「引用照 canonical §6.1 四約束」。本卡⛔ 未重編節號 ⇒ 該引用不需改；`§6.1 派工包標準條款` 在新檔仍存在。查核指令：`grep -n '§' stage-rules/{requirement,research,planning,implementation,review,deploy,maintenance,closeout}.md`。

**F- 編號條數對照決議 §八**：需求 15／研究 14／規劃 8／執行 12／審核 9／結案 7；部署 0、維護 0（刻意留空，⛔ 無編號）。

**守衛跟隨（⛔ 機械跟隨、非內容改動）**
- `scripts/prose_number_scan.py`：`corpus_paths()` 的 `stage-rules` glob W0 已加，**本卡僅確認、⛔ 未改**；`drafts/stage-rules` 那條 glob **保留**且現在掃到零個檔，就地改寫註解說明為何刻意保留。ID_PATS 增一條 `F-[一-鿿]+-\d+`。
- `cli/tests/test_prose_number_scan.py`：`_ID_PAIR_TABLE` 補一列（`len(_ID_PAIR_TABLE) == len(ID_PATS)` 的不變量強制）。⚠️ 該檔**不在卡面資源宣告內**——見「三 · 13 族」第 8 項。
- `docs/research/drafts/prose-number-inventory.json`：27 筆改指新居所（其中 7 筆因項目行改編號而重算 `line_sha1`，claims 的 `(occurrence, token)` 對集未變）；新增 24 筆（橫幅「15 值」×8、清冊「三層」「三值」各 ×8）。條目總數 117 → 141。

---

### 二 · 驗證（全部實跑，stdout／stderr／rc 分開取）

| # | 指令 | rc | stdout（逐字） | stderr |
|---|---|---|---|---|
| 1 | `python3 scripts/prose_number_scan.py` | `0` | `{"total": 204, "unclassified": 0, "dead_entries": 0, "invalid_entries": 0, "claims_mismatch": 0, "uncovered_claims": 0, "extra_claims": 0}` | 空 |
| 2 | `python3 scripts/canonical_citation_scan.py` | `0` | `掃描檔案數：181` ／ `命中（不含排除）：0` ／ `排除集：0 項` | 空 |
| 3 | `python3 scripts/pollution_check.py` | `0` | `{"scanned_files": 13, "total_hits": 42, "unapproved_count": 0, "approved_entries": 42}` | 空 |
| 4 | `grep -l 舊語彙 stage-rules/*.md \| wc -l` | `0` | `8` | 空 |
| 5 | `cd cli && uv run pytest -q` | `0` | `1612 passed, 1 skipped in 62.41s (0:01:02)` | — |
| 6 | `python3 scripts/qualified_pointer_scan.py` | `0` | `紅（不含豁免）：0` | — |
| 7 | `python3 scripts/replay_escalation_rules.py` | `0` | — | — |
| 8 | `uv lock --check`（cli/） | `0` | `Resolved 7 packages` | — |

`test_canonical_citation_scan` 綠：含於第 5 項（`cli/tests/test_canonical_citation_scan.py`）；獨立守衛另見第 2 項。

**AC7 oracle**：`8`。⚠️ `stage-rules/*.md` 共 12 檔（8 階段檔 ＋ 4 份 W0 conduct），四份 conduct ⛔ 不含「舊語彙」故不計入——`8` 是「恰好八份階段檔命中」，⛔ 不是「目錄下全部檔案」。

**CI**：run `33480022207`、`conclusion=success`、`headSha=27ff0b2f28d4d26f48c640e056044222ea5e968e`——**與本報告「給查核者的入口 SHA」逐字相同**。查詢：`gh run list --repo ruan6047/ai-workflow --branch claude/wf-redesign-w2a-rules-0631e8 --json databaseId,status,conclusion,headSha`。⚠️ 該 run 是 **push 事件（分支頭）**，⛔ 不是合併結果；合併結果的 run 要開 PR 才會產生（CI 檔頭逐字說明兩者互補）。

**commit trailer**：`wfcli doctor . --registry none --commit-trailers --commit-range origin/main..HEAD` rc=0，逐字「統計：違規 0／界線前（不判違規）0／合規 4／無所要求 0（共 4 筆）」。四個 commit 各自 `git interpret-trailers --parse` 皆解得出 4 行（3 個身分欄 ＋ `Co-authored-by`）。

**AC4 負控（跑在 scratchpad 的 temp fixture，⛔ 未寫進會被合併的樹）**

- **NC1**（注入污染符）：`--root <tmp> --files probe.md`，fixture 內容為一行含 `📥Backlog` 與 `needs-deploy`。
  - rc = `1`
  - stdout（前兩行逐字）：`[unapproved] probe.md:1: [📥Backlog] sha1=7ec5f814412d | 本行刻意含污染符：📥Backlog 與 needs-deploy，供負控。` ／ 同行 `[needs-deploy]`；末行計數 `{"scanned_files": 1, "total_hits": 2, "unapproved_count": 2, "approved_entries": 42}`
  - stderr：空
- **NC2**（anchor 脫鉤）：把一條**已核准**的行改一個字元（`擠在一起` → `擠在一塊`）後掃該複本。
  - rc = `1`
  - stdout（逐字）：`[unapproved] AI_WORKFLOW.md:116: [📥Backlog] sha1=88a25d7e558e | 單欄把「階段」與「狀態」擠在一塊：…`；計數 `{"scanned_files": 1, "total_hits": 38, "unapproved_count": 1, "approved_entries": 42}`
  - stderr：空
  - ⇒ 改一個字元只讓**那一筆**脫鉤，其餘 37 筆仍核准 ⇒ anchor 是逐行綁的，⛔ 不是整檔放行。

**AC4 豁免清單分佈（42 筆，逐筆有 line-specific rationale）**：canonical §0.2 逐位元凍結的裁定原文、§0.1（決議 row 4，owner＝切換 Initiative）、§0.0 的現行看板語彙區塊（row 2／row 7）、§3／§4／§7 的既有條文、`control-plane-contract.md` 的**檔名**引用、inventory 逐字轉錄的 excerpt。⚠️ 其中一筆是 **finding ⛔ 不是乾淨例外**——見「五 · 上呈」第 1 項。

---

### 三 · 踩坑族清冊（`import wf_cli.pitfalls; roster_for('執行')`，13 族）

```
宣稱超過證據：已檢查
列舉或覆蓋不完整：發現：本人一度以 roster_for('🔨執行中')（傳交付狀態值而非階段名）取清冊，靜默得到 8 族；該函式對未知階段回空 tuple 而不丟例外（docstring 明載）。改以 roster_for('執行') 取得 13 族後重做本節。
交付未落地或未接線：已檢查
文件與現實漂移：發現：canonical §3 仍寫「偏離與理由記入 claim 事件」（該 event log 2026-08-04 已封存），且 §3 仍以本卡裁撤的四個角色名敘述 Gate 流程；兩者皆無取代清單列 ⇒ 無 owner。本卡⛔ 不自行改，已上呈（見五）。
狀態轉移或生命週期：已檢查
可重現性不足：已檢查
並發或時序不安全：已檢查
資源或寫入集宣告：發現：卡面資源宣告未含 cli/tests/test_prose_number_scan.py，而 test_id_pair_table_covers_every_pattern 以 len(_ID_PAIR_TABLE)==len(ID_PATS) 釘死 ⇒ 動 scripts/prose_number_scan.py 的 ID_PATS 必連動該測試檔，兩者機械上不可分。已動筆並登記為宣告缺口。
守衛涵蓋不足或可被繞過：發現：pollution checker 的 stale_entries（過期豁免條目）刻意⛔ 不進 rc——AC4 逐字寫死「唯一 pass criterion＝unapproved_count==0」，⛔ 不自行加判準；已在 docstring 標為已知缺口。另：checker 自我排除自身與 manifest 兩檔（token 字面定義住在裡面，掃自己會產生循環），排除集每次輸出逐檔印出。
身分或歸屬對應錯誤：發現：派工包要求 trailer「四欄」，本卡四個 commit 只有三個身分欄。理由見「四 · 單方面決定 5」。
程序或規格照字面不成立：發現：AC3「rows 1 舊文刪除⛔ 不留屍體」與「其餘列⛔ 不在本卡動」在字面上互斥——十五值序列同時是 row 1（條文）與 row 2（看板語彙）的載體。處置見「四 · 單方面決定 1」。
留痕失真或遺失：發現：八份 stage-rules 以 git mv 搬移，但因同 commit 內的內容變動幅度大，git show --stat 在預設相似度門檻下 0/8 顯示為 rename（-M40% 得 5/8、-M30% 得 8/8）。查核請用 git show --stat -M30% 0c55520。
解析或正規化錯誤：已檢查
```

---

### 四 · 單方面決定（逐項，⛔ 需要裁定的請直接推翻）

1. **十五值序列「降階」而非「刪除」。** 決議 §一 row 1 的被取代者逐字是「canonical §0 十五值單欄序列（**條文**）」，而 row 2「看板實際狀態語彙（15 值）」的 owner 是切換 Initiative、AC3 逐字「其餘列⛔ 不在本卡動」。⇒ 我把**條文身分**殺掉（不再寫成「交付狀態為 X → Y」），把**十五個值**保留成明標「⛔ 非本節條文」的現況記載。三個依據：(a) 若連值一起刪，新 §0.0 又標「尚未切換」，canonical 就會變成**沒有任何現行狀態語彙**；(b) §0.2 表七 D1 早已逐字裁定「§0 那一行是敘述順序，不是約束」——降階與該裁定同向；(c) 改動前 canonical 內部有 **11 行**引用該序列（`git show f656a67:AI_WORKFLOW.md | grep -nE '單欄序列|§0 序列|§0 那條序列|§0 那一行|canonical §0：|canonical §0 逐字|§0 給了一條|值域與序列由 §0'` 得 11，改動後同樣式仍得 11），其中多數落在 §0.2 那段**逐字寫明「本次搬遷⛔ 不改寫」**的凍結裁定原文裡，刪值即造成無法修補的懸空引用。
2. **§1／§2 移到 §0 前但⛔ 不重編節號。** 決議 §九 在描述移動後仍稱它們為「§1／§2」；且 canonical 之外引用這三個節號的行數，`git grep -nE '§[012]' -- . ':!AI_WORKFLOW.md' | wc -l` 當下得 **474**（⚠️ 該量法**含** `§0.1`／`§1.1`／`§2.x` 這類子節，是**上界⛔ 非精確計數**；重編節號會把它們全部打歪）。代價：標題順序讀起來是 1 → 2 → 0 → 3。
3. **新節號 `§0.0`。** AC2 要求「全節帶標記」，而 §0 同時裝著現行有效的類型表與級別表 ⇒ 需要一個可精確界定的邊界。⛔ 我沒有把標記掛在 `## 0.` 上（那會讓標記誤蓋類型表與級別表）。
4. **`tier-rules.md` ⛔ 不放級別表副本。** 決議 §四 說框架層＝canonical「變更級別」段，而那段本來就是表格。抄一份＝第二個會漂的居所。本檔提供接線（兩層 DI、只能加嚴、單向門、三子問、未定項），並就地留註解說明不得由「這裡沒有表」推出框架層沒定義。
5. **commit trailer 三欄，⛔ 非派工包要求的四欄。** canonical §6 逐字：T2 以上**實作 commit** 必加 `Requested-by`／`Planned-by`／`Implemented-by`；`Reviewed-by` 是 merge commit／PR 結案／B2 核可 commit 才另加。本卡四個 commit 都是分支上的實作 commit，且**查核尚未發生** ⇒ 填任何 `Reviewed-by` 值都是不實宣稱，而 canonical 明載守衛「只驗鍵存在、從不驗值」⇒ 誠實是唯一控制。canonical 給的「不適用」形態 `Reviewed-by: —（基線更新 merge，無查核對象）` 其**唯一合法用法**是基線更新 merge，不適用於此。⇒ 我選擇不填，並把偏離登記在這裡。**要我補請直說**，我會 amend。
6. **動了資源宣告外的 `cli/tests/test_prose_number_scan.py`。** 理由見「三 · 資源或寫入集宣告」。⛔ 不動它的替代方案是「不加 ID_PAT」，那會讓 `prose_number_scan` 對 8 份新檔的 F- 編號全部判 unclassified、七項計數非零。
7. **§1 的裁撤說明⛔ 不逐一列出四個舊角色名。** 其中 `Discovery lead` 是決議 §二 的污染符（角色表文脈），寫在角色表正下方會製造一筆我自己新造的豁免。改寫成「本表已裁撤的名稱」，讀者在 §3 讀得到那些名字。⚠️ 代價：§1 的註解比較不具體。

---

### 五 · 上呈需求方（無 owner、本卡⛔ 未動）

1. **canonical §3 的「記入 claim 事件」。** 決議 §一 row 5 只把 `MODEL_ROUTING.md` 的同句改掉（✅ 已完成 `9bb9cba`），canonical §3 的同義句**沒有任何一列涵蓋**。改它＝一條沒有 owner 的 T4 規則變更 ⇒ 我⛔ 不自行動筆，已在 allowlist 該筆的 `rationale` 逐字登記為 finding。**請指派 owner 卡。**
2. **canonical §3 仍以四個裁撤角色名敘述 Gate 流程。** 同上：取代清單⛔ 沒有「§3 角色名」這一列。我在 §1 逐字揭露了這個不一致，並寫明⛔ 不得由六角色表推出對應關係（決議 §六⛔ 未給映射）。**請指派 owner 卡**，或裁定沿用哪個對應。

---

### 六 · 失誤登記（逐項，⛔ 不摘要、⛔ 不加緩和語）

1. **cwd 未還原兩次。** 以 `cd cli && uv run pytest` 執行後 shell cwd 停在 `cli/`。後果：(a) `git grep -n 'LIFECYCLE' -- .` 回 0 命中，我當下**差點據此推論「本 repo 無 LIFECYCLE 慣例」**——實際上 4 個檔有；(b) `git add AI_WORKFLOW.md` 回 `fatal: pathspec 'AI_WORKFLOW.md' did not match any files`；同一批指令裡的 `git reset -q` 仍是 repo 全域生效，把已 stage 的全部內容退回索引（工作樹未動、無資料損失）。修正＝改用 `uv run --directory cli`，且每個 commit 前先 `cd` 回 worktree 根並 `pwd` 自證。
2. **管線吃掉 rc。** `... | tail -N; echo RC=${PIPESTATUS[0]}` 在複合指令中多次印出**空的 RC**。最終驗證段全部改成 stdout／stderr／rc 三者分開落檔再讀。
3. **`roster_for` 傳錯參數型別**，靜默得到 8 族而非 13。詳見「三」第 2 項。
4. **pollution checker 首版漏掉未追蹤檔。** `git diff --name-only` 看不見新增檔 ⇒ `tier-rules.md` 與 checker 自身在 `git add` 之前對它是隱形的。在寫 manifest **之前**發現並補上 `git ls-files --others --exclude-standard`，就地留註解。
5. **輔助腳本首版未註冊 `sys.modules`**，`dataclass` 在載入 `pollution_check` 時拋 `AttributeError: 'NoneType' object has no attribute '__dict__'`。第二版修正。
6. **新寫的 §0.0 有一個錯字**「等得得到的」，已修為「等得到的」。
7. **`git mv` 的 rename 在預設門檻下不顯示**（0/8）。詳見「三 · 留痕失真或遺失」。⛔ 我沒有為了讓它顯示而拆 commit——拆了會產生一個 `prose_number_scan` 紅的中間 commit。

---

### 七 · 未驗清單（逐項＋各自原因；三分類承接 canonical §6.4.2）

**驗不了**

1. 「本卡未在 canonical 造成任何懸空引用」——我只驗了**字面**引用（`§0`／`§1`／`§2` 與序列關鍵字的 grep）。⛔ 證不出不存在：以別的措辭指向被改動內容的散文（例如「上面那張表」）本量法搜不到。⇒ 這個宣稱的形狀是**下界**，⛔ 不是全稱。
2. 八份 stage-rules 的**內容正確性**（條文是否忠實於決議 §八／§三之二）。我驗的是條數與逐行搬遷；「條文語意是否等同決議」是內容判斷，機械上驗不了。

**沒去驗**

3. `templates/` 下五份交接範本是否需隨六角色表更新——W2B 射程，本卡未查、未量。
4. `cpbl-analytics` 側是否受本次 canonical 改寫影響——切換 Initiative 射程，本卡未開該 repo、未量。
5. `wfcli` 的能力層級／級別相關值域是否需隨 `tier-rules.md` 調整——W3′ 射程，未查。
6. `templates/database-contract.md` 是否已具備接收環境枚舉與別名表的位置——該檔**不在本卡資源宣告內**，我只在 `tier-rules.md` 做了移交聲明，⛔ 未對該檔動筆、⛔ 未查它現況是否已有 `local｜prod` 封閉枚舉。

**刻意不驗**

7. 跨家族裁決含身分自述——審核階段，⛔ 非執行者工作（派工包明文）。
8. pollution checker 的 pytest 覆蓋——AC⛔ 未要求，且該檔標為 `LIFECYCLE: disposable`；以實跑負控（NC1／NC2，逐條釘 stdout／stderr／rc）替代。**委給查核者判是否足夠。**
9. `stale_entries` ⛔ 不進 rc 的風險敞口有多大——AC4 把 pass criterion 寫死成單一判準，我⛔ 不自行加第二個。**委給查核者判 AC 本身是否該修。**
10. 「§3 的舊角色名與 claim 事件句該歸哪張卡」——那是需求方的裁定，⛔ 非我的判斷（見五）。

---

### 八 · 決議 §八「執行 12」逐條回應（三值＋evidence）

| # | 條 | 三值 | evidence |
|---|---|---|---|
| 1 | worktree 路徑紀律 | **發現：** | 見「六 · 失誤登記 1」。所有 Edit／Write／指令的目標路徑均在 `/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-redesign-w2a-rules-0631e8` 下；⛔ 未觸碰主 checkout |
| 2 | 逐檔 add、SHA 用 `rev-parse` | 已遵循 | 四次 commit 皆 `git add <具體路徑>`（⛔ 無 `git add docs/`）；本報告所有 SHA 取自 `git rev-parse` / `git log --format` / `gh --json`，⛔ 無一手打 |
| 3 | ⛔ 不截斷輸出 | **發現：** | 見「六 · 失誤登記 2」；最終驗證段（本報告「二」）全部 stdout／stderr／rc 分開 |
| 4 | `rc=0` ⛔ 不等於成功 | 已遵循 | 每個守衛都額外看被改變的狀態：prose 看七項 counts、pollution 看 `unapproved_count`／`total_hits`、AC7 看 oracle 值 `8`、pytest 看 `1612 passed` |
| 5 | 宣告成功前核那次執行的識別碼 | 已遵循 | CI run `databaseId=33480022207`、`headSha=27ff0b2f…`，與入口 SHA 逐字比對 |
| 6 | 驗證器 `import` ⛔ 不重打 | 已遵循 | inventory 重算與 allowlist 產生皆以 `importlib` 載入 `scripts/prose_number_scan.py` / `scripts/pollution_check.py` 後呼叫其 `_line_key` / `scan_paths` / `post_image_paths`；13 族由 `wf_cli.pitfalls.roster_for` 取 |
| 7 | 複驗用會通過的樣本 | 已遵循 | NC2 用真實 canonical 的複本（38 筆命中中 37 筆仍核准），⛔ 不是合成小樣本 |
| 8 | 算術上不可能的結果最先響 | 已遵循 | F- 編號條數逐階段對照決議 §八（15／14／8／12／9／7／0／0），編號產生器內以 `assert int(m.group(1)) == n_items` 逐行釘序 |
| 9 | 刻意行為就地留註解 | 已遵循 | 六處：`prose_number_scan` 的 drafts glob 零命中、ID_PAT 收窄且⛔ 不預開 P-／T-、checker 的自我排除與 `stale_entries` 不進 rc、`tier-rules` ⛔ 不放副本、§0.0 標記的涵蓋範圍、§1 裁撤名的三段式揭露 |
| 10 | 修過期引用最容易留下新的過期引用 | **發現：** | `prose_number_scan` 的舊註解「drafts/ 下仍有未生效的其餘 stage 檔（波 2 才搬）」正是**本卡讓它變假**的那一句；已改寫並寫明零命中是刻意、⛔ 不得判成死條目 |
| 11 | 交付物寫事實⛔ 不寫狀態 | 已遵循 | 本報告的 SHA／計數／rc 皆字面值；工作樹與推送狀態寫查詢指令（見信封末） |
| 12 | 失誤登記與未驗清單逐項⛔ 不摘要⛔ 不加緩和語 | 已遵循 | 「六」7 項、「七」10 項，逐項展開；⛔ 未寫「N 項」式摘要 |

---

### 九 · 給查核者的入口

```bash
git fetch origin && git checkout 27ff0b2f28d4d26f48c640e056044222ea5e968e
```

- 基線＝`f656a678e540d4083740e0f30f1214e887e42c04`（釘死字面；`pollution_check.py` 的 `BASE_SHA` 同值）。
- 八份檔的 move 請用 `git show --stat -M30% 0c555208a54795ab24cdd543d276c8d041f90504`（預設門檻下顯示為 delete+add，原因見「三 · 留痕失真或遺失」）。
- 守衛在**合併結果**上跑（`reviewer-conduct` 三 · 裁決紀律）：本報告的 CI run 是 **push 事件的分支頭**，⛔ 不是合併結果。


## Comment 5490422013 · 2026-09-01T07:25:39Z

⚠️ PM 更正（2026-09-01）：上一筆 handoff（執行→審核，SHA 27ff0b2f）所附的**踩坑族清冊回應貼錯檔**——寫入 Log 的是 `WF-REDESIGN-W1` 的清冊（其「發現」為 W1 的 R2-1 措辭超界），⛔ 非本卡內容。Log 為 append-only，⛔ 不改寫；本留言為更正居所。

**本卡（W2A）之真實清冊＝交付報告「三 · 踩坑族清冊」逐字**（執行者以 `import wf_cli.pitfalls; roster_for('執行')` 產生，13 族）：其中 **3 族為「發現」**——族 1 worktree 路徑紀律（見報告失誤 1）、族 3 ⛔ 不截斷輸出（見報告失誤 2）、族 10 修過期引用最易留新過期（prose_number_scan 舊註解）；其餘 10 族為「已遵循」，各附 evidence。⚠️ 逐字全文以報告該段為準，⛔ 不以本摘要取代。

失誤歸屬：PM（本人），root cause＝重用前一張卡的清冊檔而未重新產生。查核者請以本更正與報告該段為準。

## Comment 5490600491 · 2026-09-01T07:40:50Z

<!-- wf-review-event:v1 card_id=WF-REDESIGN-W2A source_sha=27ff0b2f28d4d26f48c640e056044222ea5e968e attempt_id=WF-REDESIGN-W2A-e0-27ff0b2f28d4d26f48c640e056044222ea5e968e -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-REDESIGN-W2A`　attempt_id：`WF-REDESIGN-W2A-e0-27ff0b2f28d4d26f48c640e056044222ea5e968e`
- 查核者：Codex@OpenAI（gpt-5.6-sol，session 01a05bdd-5a42-7192-a956-a3e607a6f322）　escalation_epoch：0
- source_sha：`27ff0b2f28d4d26f48c640e056044222ea5e968e`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-09-01T15:40:47+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git status --porcelain=v1`
  - HEAD=27ff0b2f28d4d26f48c640e056044222ea5e968e，工作樹無輸出、乾淨，與 handoff source_sha 相符。
- `git merge-base origin/main HEAD && git rev-parse origin/main`
  - 兩者皆為 f656a678e540d4083740e0f30f1214e887e42c04；origin/main 是被審分支直接祖先，故本次 HEAD 即目前可形成的合併結果。
- `uv run --directory cli pytest -q`
  - 1612 passed, 1 skipped in 249.10s，rc=0。
- `python3 scripts/prose_number_scan.py && python3 scripts/canonical_citation_scan.py && python3 scripts/pollution_check.py --json`
  - prose 七項皆 0、total=204；citation 命中 0、排除 0；pollution scanned_files=13、total_hits=42、unapproved_count=0、approved_entries=42、invalid/stale/unreadable 皆 0，三者 rc=0。
- `python3 scripts/pollution_check.py --files scripts/pollution_check.py scripts/pollution-allowlist.json --json`
  - rc=1；兩個預設自我排除檔實得 total_hits=115、unapproved_count=115，其中 checker 16、manifest 99。
- `git show --stat -M30% 0c555208a54795ab24cdd543d276c8d041f90504`
  - 八份 requirement/research/planning/implementation/review/deploy/maintenance/closeout 均顯示 rename，與執行者 8/8 宣稱相符。
- `git interpret-trailers --parse 對 a08c57e、0c55520、bf4d5df、27ff0b2 逐筆執行`
  - 四筆皆解析 Requested-by、Planned-by、Implemented-by、Co-authored-by；依 canonical §6，分支實作 commit 尚不要求 Reviewed-by，判讀合規。
- `對照 docs/research/WORKFLOW-REDESIGN-2026-08-30.md §一／§二／§三／§六／§八 與 AI_WORKFLOW.md、stage-rules 八檔、tier-rules.md`
  - AC1、AC6、AC6b、AC7 的結構與條數落點成立；但 §0.0 與仍標為目標狀態的 §0.1 互斥，§3 仍使用已撤角色且 §1 明示無 owner；決議 §二的 Discovery lead 未進 checker TOKENS。

### findings（3，其中 blocking 3）

- **WF-REDESIGN-W2A-R1-001**　severity=major　blocking=true　class=authoritative-artifact　attribution=planner　root_cause_id=`replacement-scope-textually-contradictory`
  - evidence：卡面 AC3 要求 rows 1、3 的舊文刪除且「不留屍體」，同時又禁止碰其餘 owner 列；決議 §一 row 1 指十五值序列的條文身分、row 2 則把實際 15 值交給切換 Initiative。AI_WORKFLOW.md:89-96 因而把 15 值改為現況敘述，這個降階本身合理、不是留屍體；但第 89 行的「非本節條文」涵蓋到第 96 行仍含「新寫入不得用」「不得人工改寫」「必填」「失敗不得結案」「release 必須」等仍具規範力的舊段，造成同一段同時宣告非條文又使用強制語氣。規格未界定應刪的是序列的規範身分、值本身，還是尾段其他現行約束，執行者無法只靠字面同時滿足兩側。
  - disposition：規劃者先修訂 AC3／取代清單措辭，明定「刪除十五值作為轉移規則的規範身分；cutover 前值域現況可保留；其他仍有效約束逐句標明效力與 owner」。再依修訂後邊界調整 §0.0 相容段，避免用整段「非條文」覆蓋仍有效的強制句。這是 planner finding，不歸責執行者選擇保留現況值。
- **WF-REDESIGN-W2A-R1-002**　severity=major　blocking=true　class=authoritative-artifact　attribution=planner　root_cause_id=`canonical-replacement-consumers-left-ownerless`
  - evidence：核心痛點尚未消失。AI_WORKFLOW.md:64-87 新增 8 階段×10 狀態；但 :108-172 的 §0.1 仍逐字自稱「本節定義目標狀態」，並定義 7 階段、另一套通用／專屬狀態與「維護永遠不結案」，與新 §0.0 及 stage-rules/maintenance.md:9 的「運行中 → 結案／完成」互斥，且沒有 superseded 標記。角色面亦同形：AI_WORKFLOW.md:21-27 明示 §3 的舊角色名沒有 owner、不得映射，然而 :593-625 仍以 Discovery lead、設計者、技術規劃者、Coordinator 指派 Gate 義務；其中 :34 又單獨把 Coordinator 映射回 PM，使「不得映射」本身也不一致。#228 只是一個通過收件流程後仍待需求裁決的清單項，沒有 owner，也不是本次 merge 的前置修復，因此揭露可防止靜默誤讀，卻不能讓 canonical 成為可執行且單義的權威規則。
  - disposition：規劃者須在 merge 前補齊 replacement owner：明確裁定 §0.1 是退役、歷史說明或仍有效相容規則，並消除與 §0.0／stage-rules 的互斥；同時裁定 §3 四個舊名的映射或重寫／退役該流程。可把 #228 升級為前置卡，或把修訂納回 W2A，但不能僅以「已登記待辦」放行 T4 canonical。修訂 spec_version 後再由執行者按新邊界實作。
- **WF-REDESIGN-W2A-R1-003**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`pollution-checker-coverage-below-ac4`
  - evidence：checker 未完整實作 AC4 的「對 post-image 逐符、逐 hit 掃描」。第一，決議 §二有 13 個污染符，含 Discovery lead（角色表文脈），但 scripts/pollution_check.py:86-104 註解誤稱 12 個且 TOKENS 完全漏掉 Discovery lead。第二，:83-84、:127-145 預設排除 checker 與 manifest；正常輸出只證明扣除兩檔後 13 檔 unapproved_count=0，直接指定兩檔重跑則出現 115 筆未核准命中。這不符合 canonical §6.2「工具或測試檔本身被自己掃到時，明確歸類為自指命中並可見列計」；列出檔名不等於列計命中。第三，:157-160 每個 token 每行只呼叫一次 rx.search，同一 token 在同一行重複仍只產一筆 Hit；以現有兩個排除檔逐 occurrence 對照，checker 檔實際 29 次只記 16 hit、manifest 實際 100 次只記 99 hit。因此 manifest 的 occurrences 實際綁「命中的行數」而非 AC 的逐 hit 數。
  - disposition：以決議 §二為單一來源補齊 Discovery lead；post-image 仍須涵蓋 checker 與 manifest，對定義性命中建立可見且列計的 self-reference 分類，不能從母體排除；掃描改以 finditer 或等價方式逐 occurrence 產生 Hit。新增三個負控／回歸測試：漏掉的 Discovery lead、兩個自指檔可見列計、同一 token 同行重複且 allowlist 配額不足時必紅。重產 manifest 與同源輸出後重送。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-REDESIGN-W2A-e0-27ff0b2f28d4d26f48c640e056044222ea5e968e
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: no
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: Codex@OpenAI（跨家族查核）
findings:
  - finding_id: WF-REDESIGN-W2A-R1-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: planner
    root_cause_id: replacement-scope-textually-contradictory
    counting_eligible: false
  - finding_id: WF-REDESIGN-W2A-R1-002
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: planner
    root_cause_id: canonical-replacement-consumers-left-ownerless
    counting_eligible: false
  - finding_id: WF-REDESIGN-W2A-R1-003
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: pollution-checker-coverage-below-ac4
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5491387728 · 2026-09-01T08:46:27Z

amend 寫入留痕（2026-09-01，op 18acf402）：body 權威居所已寫入（簡介 spec_version 2＋驗收 10 條）；Project 簡介 TEXT 欄因 1024-byte 上限拒收完整文字（同 #217 先例），PM 事後以導出摘要補該欄並註明非恆等——讀規格一律讀 body。

## Comment 5491714806 · 2026-09-01T09:14:49Z

## 交付報告 v2 — WF-REDESIGN-W2A（執行階段 ③，R1 退回後重送）

### 信封

| 欄 | 值 |
|---|---|
| 卡 | `WF-REDESIGN-W2A`（#219）；spec_version **2**（op `18acf402`，AC3 改寫＋新增 AC8／AC9） |
| session ID | `e34c8786-1249-41ff-ad3d-a8e31915dbfb` |
| **實際模型／卡面建議層級／偏離** | `claude-opus-5`（Claude Opus 5@Claude Code）／建議 高階型／**偏離：無**。⚠️ 模型值為自述；機械來源＝該 session 的 transcript `model` 欄，PM 於 assign 時已核 |
| 分支 | `claude/wf-redesign-w2a-rules-0631e8` |
| **給查核者的入口 SHA** | **`2bd2793a30ce73fe961165d8d97d11f6a63d9fcf`** |
| merge-base（釘死字面） | `f656a678e540d4083740e0f30f1214e887e42c04`（＝本次推送時的 `origin/main`，未前進） |
| 上一輪 attempt | `WF-REDESIGN-W2A-e0-27ff0b2f28d4d26f48c640e056044222ea5e968e`（REQUEST_CHANGES，3 blocking） |
| iteration | 1 |

工作樹與推送狀態的查詢方法（⛔ 不寫狀態）：`git -C <worktree> status --porcelain=v1`、`git rev-parse HEAD`、`git ls-remote origin claude/wf-redesign-w2a-rules-0631e8`。

---

### 一 · 本輪 commit（2 筆）

| SHA | 主旨 |
|---|---|
| `4a7dc268d4973500832e5865655fb493fe73753e` | `fix(w2a): close R1 — checker coverage, §0.1 retirement, §3 gate scoping` |
| `2bd2793a30ce73fe961165d8d97d11f6a63d9fcf` | `fix(tests): make the self-reference guard hermetic instead of git-dependent` |

⚠️ **第一筆刻意是單一 commit**，⛔ 不是混入無關改動：三筆 finding 的守衛狀態互相牽動——先改 canonical 則舊 manifest 的 anchor 全部脫鉤、先改 checker 則新 manifest 對不上舊 canonical ⇒ 任一種拆法都會留下一個 `pollution_check` 紅的中間 commit。理由逐字寫在 commit message 裡。

---

### 二 · R1-003（executor，`scripts/pollution_check.py`）逐條處置

**先複現，再修**（三條 evidence 我都在本機重跑得出來）：

| evidence | 我複現到的裸值 |
|---|---|
| 漏 `Discovery lead`、註解誤稱 12 個 | 決議 §二 反引號 token 實得 **13** 個；舊 `TOKENS` 的污染符部分只有 12，`Discovery lead` 不在其中 |
| 兩個自指檔預設排除 | `--files scripts/pollution_check.py scripts/pollution-allowlist.json` ⇒ `total_hits=115`、`unapproved_count=115`（checker **16**、manifest **99**） |
| 每行每 token 只 `search` 一次 | checker 檔 occurrence **29** vs 記錄 **16**；manifest occurrence **100** vs 記錄 **99** |

**處置**

1. **token 集合＝決議 §二 的單一來源。** `POLLUTION_TOKENS` 逐字照抄該行的順序與內容（13 個），`ROT_TOKENS` 另列 AC5 的 3 個，合計 `token_count=16`。⛔ 不只是補一個字串——`test_pollution_tokens_match_the_decision_record_verbatim` **解析決議 §二 那一行的反引號 token 並逐項比對順序**，⇒ 決議改了而 checker 沒跟就轉紅。並就地留註解：增刪 token 必須先改決議 §二。
2. **自指命中回到母體，可見且列計。** 刪掉 `SELF_EXCLUSIONS`，改成 `SELF_REFERENCE_PATHS` **分類鍵**：命中逐筆列印（`[self-reference] path:line:col …`）、**逐檔逐 token 列計**、計入 `total_hits`。承接 canonical §6.2 逐字「工具或測試檔本身被自己掃到時，明確歸類為**自指命中並可見列計**，不得偷偷排除」。
   - **成員三項**：checker、manifest、**它的測試檔**——判準逐字取 §6.2 的「**工具或測試檔**」，由測試釘死該 tuple。
   - **⛔ 為什麼不走 manifest**（就地留註解）：manifest 每開一筆條目就會自己寫下 `"token": …` 與 `"excerpt": …` 兩行、兩行都含該符 ⇒ 一筆豁免長出兩筆新自指命中，**不收斂**（每輪至少 ×2）。⇒ 用 manifest 表達自指是**構造上做不到**的。`entry_errors` 因此對自指路徑一律判 `invalid`。
   - ⛔ **不得讀成「self_reference 是豁免」**：它在母體內、每一筆都印得出來、逐檔逐 token 有數字；`unapproved_count` 不涵蓋它是因為它另有一條可稽核的可見通道。
3. **`finditer` 逐 occurrence。** `Hit` 增 `col` 欄以區分同行同 token 的多次命中；manifest 的 `occurrences` 現在綁的是 **occurrence 數**⛔ 不是行數。重產後：**42 條目涵蓋 45 個 occurrence**（其中 `部署狀態` 一筆 =2、`📥Backlog` 一筆 =3——這三個 occurrence 在舊版是看不見的）。
4. **測試 `cli/tests/test_pollution_check.py`：5 支**（AC 要求三個，涵蓋三條 evidence；`Discovery lead` 與自指各拆兩支，理由見下）——
   - `test_pollution_tokens_match_the_decision_record_verbatim`（單一來源綁定）
   - `test_discovery_lead_is_flagged_on_a_fixture`（負控：fixture 注入即紅）
   - `test_self_reference_files_are_not_filtered_out_of_the_population`（合成樹）
   - `test_self_reference_hits_are_visible_and_tallied`（真檔、⛔ 不碰 git）
   - `test_repeated_token_on_one_line_is_counted_per_occurrence`（配額 1 → 紅、配額 2 → 綠，rc 兩端都驗）

---

### 三 · R1-001（planner，AC3 spec_version 2）處置

原本一句「⛔ 非本節條文」蓋住整段，而那段裡有五類**仍在拘束人**的句子。現改為**逐句表**，
每一句標效力與 owner；§0.0 節首標記同步改寫成只涵蓋**目標模型**，並逐字寫明⛔ 不涵蓋這些句子：

| 句 | 效力 |
|---|---|
| a 值域與排列順序 | **敘述、⛔ 非約束**（§0.2 表七 D1 已裁定） |
| b `新寫入不得用`（`🚧進行中`／`⏳待執行`） | **現行有效** |
| c event log 與 Ledger 不得人工改寫 | **現行有效**，⛔ 不隨 cutover 退場 |
| d `🛑已停止` 必填決策與原因後封存 | **現行有效** |
| e 部署狀態值域 | 敘述 |
| f 失敗／回滾不得結案 | **現行有效** |
| g release 必以終態落地 | **現行有效** |
| h 結案清單指向範本 | **現行有效** |

owner／退場路徑逐列已填（row 2／row 7／§4.3／CLI 動詞卡）。⚠️ 這與 AC2 的「**全節**帶標記」字面衝突——AC3 v2 逐字禁止「以整段非條文覆蓋仍具強制力的句子」⇒ 我以較晚且較specific 的 AC3 v2 為準，並把涵蓋範圍逐字寫進標記本體。**若裁定 AC2 的「全節」優先，請退回。**

---

### 四 · R1-002（planner，AC8／AC9）處置

**AC8（四步）**

1. §0.1 加 **superseded** 標記；目標狀態自稱移除 ⇒ `grep -c '本節定義目標狀態' AI_WORKFLOW.md` 得 **1**（§0.0 節首）。⚠️ 該註解**刻意不把那句自稱的原文再抄一次**——初稿抄了，於是它自己讓「僅存一處」變假（grep 得 2）；就地留註解說明。並逐條列出與 §0.0 的三處差異（階段 7→8、`已合併` 不再是狀態、「維護永遠不結案」已被推翻）。
2. 「結案的觸發」段搬進 `stage-rules/closeout.md`，**⛔ 原處不留一份**；進入子句改寫為實測三條入邊：① 審核 `APPROVE` ② 研究 `不可判定 → 結案／完成` ③ 維護 `運行中 → 結案／完成`。舊文那句「宣告了維護階段的卡永遠不結案」與 ③ 互斥，已於 §0.1 就地寫明它**已被推翻**。
3. 「為什麼要兩軸」**⛔ 未搬**（依 AC8 第 3 步）。
4. 五列逐列補承接者：#1＝**切換 Initiative**（決議 §十之二 第 3 點）／#2 原有（子卡的 `open` 驗證）／#3＝**§0.0**／#3b 原有（查核者人工審）／#4＝**⛔ 尚無具名卡**。#4 誠實填「無」的理由見「七 · 程序或規格照字面不成立」。

**AC9（射程嚴格限縮）**

- 三條 Gate 定義的動作者改為**執行者**（依據＝八份 `stage-rules/` 的「各角色」表逐檔把該階段產出工作指給執行者），並就地留註解：⛔ **不得由此推出「舊名＝執行者」**——改的是誰做這件事，⛔ 不是宣告映射。
- mermaid `C[Coordinator 認領資源]` → `C[PM 認領資源]`。
- **「二擇一」我取 §1.1 的 `Coordinator` 映射句**（它是**既有** canonical 條文，⛔ 不是本卡新造的），因此 §1 表下那條籠統禁令「⛔ 不得自行推對應關係」**已廢**，改為**逐名處置**：`Coordinator`→PM（§1.1 有據）／`技術規劃者`→規劃階段內的執行者（`stage-rules/planning.md` 分角色表逐字「執行者（技術規劃者）」，⛔ 不得外推）／`設計者` 與 Discovery 階段的證據負責人→**決議 §六 ⛔ 無映射，本卡也⛔ 不造**。
- **⛔ §3.1／§3.2／§3.3 一字未動**——機械核對（取 `27ff0b2` 與 HEAD 的三節逐行比對）：`§3.1 逐行相同：True`／`§3.2 逐行相同：True`／`§3.3 逐行相同：True`。並在 §3 就地寫明 §3.1 是規劃深度政策⛔ 未退役。
- 外部指向（`MODEL_ROUTING`／`ADOPTION`／`tasks/INIT-AIWF-PRODUCT1`）⛔ 未動。

**裁撤四名在 canonical 的殘留（`grep -c`，逐名裸值）**：`Discovery lead` **0**／`設計者` **1**（只在 §1 逐名處置註解）／`技術規劃者` **3**（§1 註解 ×2 ＋ §3 Plan 條 ×1，皆為有據的映射說明）／`Coordinator` **4**（§1 註解 ×2、§1.1 映射句 ×1、**§5 升級計數段 ×1**）。⚠️ 最後那一處在 AC9 明文射程外，**未動**——見「八 · 上呈」。

---

### 五 · 驗證（全部實跑，stdout／stderr／rc 分開取）

| # | 指令 | rc | stdout（逐字） | stderr |
|---|---|---|---|---|
| 1 | `python3 scripts/prose_number_scan.py` | `0` | `{"total": 206, "unclassified": 0, "dead_entries": 0, "invalid_entries": 0, "claims_mismatch": 0, "uncovered_claims": 0, "extra_claims": 0}` | 空 |
| 2 | `python3 scripts/canonical_citation_scan.py` | `0` | `命中（不含排除）：0`／`排除集：0 項` | 空 |
| 3 | `python3 scripts/pollution_check.py` | `0` | `{"scanned_files": 16, "token_count": 16, "total_hits": 188, "self_reference_count": 143, "unapproved_count": 0, "approved_entries": 42}` | 空 |
| 4 | `grep -l 舊語彙 stage-rules/*.md \| wc -l` | `0` | `8` | 空 |
| 5 | `uv run --directory cli pytest -q` | `0` | `1617 passed, 1 skipped` | — |
| 6 | `python3 scripts/qualified_pointer_scan.py` | `0` | `紅（不含豁免）：0` | — |
| 7 | `python3 scripts/replay_escalation_rules.py` | `0` | — | — |
| 8 | `uv lock --directory cli --check` | `0` | — | — |

**AC4 負控（全部跑在 scratchpad 的 temp fixture／shallow clone，⛔ 未寫進會被合併的樹）**

- **NC1 · 注入三個污染符（含 R1-003 指名的 `Discovery lead`）**：rc = **1**；stdout 三行 `[unapproved] probe.md:1:9 [📥Backlog]`／`:1:18 [needs-deploy]`／`:1:33 [Discovery lead]`；計數 `{"total_hits": 3, "self_reference_count": 0, "unapproved_count": 3}`；stderr 空。
- **NC2 · anchor 脫鉤**（把一條已核准的行改一個字元）：rc = **1**；`[unapproved] AI_WORKFLOW.md:148:39 [📥Backlog] sha1=88a25d7e558e`；計數 `{"total_hits": 41, "unapproved_count": 1}` ⇒ 41 筆中只有那一筆脫鉤；stderr 空。
- **NC3 · 同行同 token 重複、manifest 無條目**：rc = **1**；`[unapproved] dup.md:1:5` 與 `dup.md:1:21` 兩筆（`col` 不同）；計數 `{"total_hits": 2, "unapproved_count": 2}`；stderr 空。⇒ 逐 occurrence 生效。
- **NC4 · shallow clone 負控**（見「六 · 失誤登記 1」）：`git clone --depth 1` 的樹上 `git cat-file -e f656a678…` rc=**1**；**舊版**測試 `1 failed, 3 passed`（錯誤與 CI 逐字相同：`CalledProcessError` on `git diff --name-only --diff-filter=d f656a678…`）；**新版** `5 passed`。

**CI（三次逐筆登記，⛔ 不只報綠的那次）**

| run | headSha | conclusion |
|---|---|---|
| `33480022207` | `27ff0b2f28d4d26f48c640e056044222ea5e968e`（R1 送審） | success |
| `33490469927` | `4a7dc268d4973500832e5865655fb493fe73753e`（本輪第一筆） | **failure** — 見「六 · 失誤登記 1」 |
| `33490886848` | `2bd2793a30ce73fe961165d8d97d11f6a63d9fcf`（**本次交回**） | success |

`33490886848` 的 `headSha` **與本報告「給查核者的入口 SHA」逐字相同**。查詢：
`gh run list --repo ruan6047/ai-workflow --branch claude/wf-redesign-w2a-rules-0631e8 --json databaseId,status,conclusion,headSha`。
⚠️ 三次都是 **push 事件（分支頭）**，⛔ 都不是合併結果。

**commit trailer**：`wfcli doctor . --registry none --commit-trailers --commit-range origin/main..HEAD` rc=0。四個身分欄的討論同上輪（`Reviewed-by` 依 canonical §6 不加在分支實作 commit 上；**上一輪查核者已逐字判讀「判讀合規」**）。

---

### 六 · 失誤登記（逐項，⛔ 不摘要、⛔ 不加緩和語）

1. **本機綠、CI 紅——我把守衛建在 repo 歷史上。** `test_self_reference_files_are_in_the_population_and_tallied` 對真 repo 呼叫 `post_image_paths(_REPO_ROOT, BASE_SHA)`；GitHub Actions 的 checkout 是 shallow（`fetch-depth` 預設 1），`git diff … f656a678…` 在那棵樹上直接 `CalledProcessError` ⇒ **CI run `33490469927` 在 `4a7dc26` 轉紅**。⚠️ 這是我上一輪報告裡自己寫過「查核者要在合併結果上跑」卻沒推廣到「測試不能假設歷史存在」。修法⛔ 不是吞例外、⛔ 不是改 CI 的 `fetch-depth`（⛔ 不在本卡射程），而是把該判準搬到合成樹上驗；並以 shallow clone 實跑負控證明舊版真的會紅、新版會綠。
2. **NC2 第一次跑時 rc 取錯。** 我寫成 `python3 … > o 2> e; echo "####"; echo "rc=$?"`，`$?` 取到中間那個 `echo` 的 **0**，於是一支**實際回 1** 的負控被印成 `rc=0`。當場察覺並改成先存 `NC2_RC=$?` 再印。⚠️ 這正是 `F-執行-03`／`F-執行-04`，而我上一輪才登記過同族。
3. **§0.1 的 superseded 註解初稿自我推翻。** 初稿把「本節定義目標狀態」那句原文抄進註解裡宣稱「僅存一處」，結果 grep 得 **2** ⇒ 宣稱當場為假。以 grep 抓到後改寫成不抄原文，並就地留註解說明為什麼不抄。
4. **`SELF_REFERENCE_PATHS` 初版只放兩檔。** 新測試檔一寫出來，manifest 產生器就拒絕分類（我放在產生器裡的「⛔ 不得以泛用理由充數」保險絲響了）。canonical §6.2 逐字含「**測試檔**」⇒ 改為三項並由測試釘死。
5. **輔助腳本的誤導輸出未修。** `mkallow.py`（scratchpad，⛔ 不在交付物內）的節次分類器對非 canonical 檔仍會算出一個 §，於是 UNHANDLED 診斷行印出無意義的節次。⛔ 未修，此處標明。

---

### 七 · 踩坑族清冊（`import wf_cli.pitfalls; roster_for('執行')`，13 族）

```
宣稱超過證據：已檢查
列舉或覆蓋不完整：發現：R1-003 就是這一族命中——決議 §二 13 個符我只實作 12 個。修法⛔ 不是補一個字串：token 集合改由測試對決議 §二 那一行逐字綁定（解析反引號 token 並比對順序），決議改了而 checker 沒跟就轉紅。
交付未落地或未接線：已檢查
文件與現實漂移：發現：(a) §0.1 逐字宣稱 §0「逐字載明它『仍算現役、仍佔資源交集檢查』」，而該字串在 §0 從來不存在——git show f656a67:AI_WORKFLOW.md | grep -c '仍算現役' 得 1（即只有 §0.1 自己那一處）⇒ 改動前就存在的懸空逐字引用，⛔ 非本輪造成、⛔ 不在任何 AC，未動。(b) canonical §5 升級計數段仍有一處 Coordinator，在 AC9 明文射程外，未動。兩者已上呈。
狀態轉移或生命週期：發現：改寫前 canonical §0.1 逐字「宣告了維護階段的卡永遠不結案」與 stage-rules/maintenance.md 的「運行中 → 結案／完成」互斥（R1-002 指名）。已於新居所 closeout.md 以實測三條入邊取代，並在 §0.1 就地寫明該宣告已被推翻。
可重現性不足：發現：見失誤登記 1——守衛建在 repo 歷史上，本機綠 CI 紅。已改成合成樹並以 shallow clone 負控實證。
並發或時序不安全：已檢查
資源或寫入集宣告：發現：本輪新增 cli/tests/test_pollution_check.py，⛔ 不在卡面資源宣告內（上一輪 op b01330f3 補的是 test_prose_number_scan.py）。AC 明文要求新增測試 ⇒ 已動筆並上呈補宣告。
守衛涵蓋不足或可被繞過：發現：(a) stale_entries 仍⛔ 不進 rc——AC4 逐字寫死單一判準，⛔ 不自行加第二個；已在 docstring 標為已知缺口。(b) 新增的 self_reference 分類是可見通道⛔ 不是豁免：三個成員由測試釘死、逐檔逐 token 列計、計入 total_hits，且 entry_errors 對自指路徑一律判 invalid；⛔ 不走 manifest 的理由（不收斂）就地留註解。是否仍構成可被濫用的通道，委給查核者判。
身分或歸屬對應錯誤：發現：AC9 的「二擇一」我取 §1.1 的 Coordinator 映射句、廢掉 §1 的籠統禁令 ⇒ canonical 現在對四個裁撤名是逐名處置（兩名有據、兩名明文無映射）。⛔ 不得讀成「四名都有映射」。
程序或規格照字面不成立：發現：AC8 第 4 步寫「§0.2 D 表引用 §0.1 的 5 列（#1／2／3／3b／4）」，但實查 §0.2 的 D 表（D1–D7）對 §0.1 零引用——grep -n '^| D[0-9].*§0\.1' AI_WORKFLOW.md 回 rc=1、零輸出；那五列在 §0.1 自己的「本卡條文的執行者狀態」表，且 AC 附註「其中 2 列已有」與該表 #2（子卡的 open 驗證）、#3b（查核者人工審）逐字相符。⇒ 我依 row ID 與該佐證判定 AC 的節次寫錯，動的是 §0.1 那張表、⛔ 未動 §0.2。若裁定我認錯了，請退回。另：#4 的承接者我填「⛔ 尚無具名卡」——收斂 --status 屬 CLI 動詞改造，而決議 §十 的 W3′ 清單⛔ 未列此項、§0.2 D4 只寫「已登記」⛔ 未指名卡號 ⇒ 填任何卡號都是憑空造。
留痕失真或遺失：發現：R1 處置為單一 commit（第一筆），理由逐字寫在 commit message——任一拆法都會留下守衛紅的中間 commit。第二筆是 CI 紅的修復，獨立成筆。
解析或正規化錯誤：已檢查
```

---

### 八 · 上呈需求方（無 owner／射程外，本卡⛔ 未動）

1. **canonical §3「記入 claim 事件」**（上輪已上呈，PM 開 #228）——本輪雖改寫了同一行的動作者，**該子句一字未動**，其 allowlist 條目的 finding rationale 保留。
2. **canonical §3 的裁撤角色名**——AC9 已納回本卡處置，本項結案。
3. **canonical §5 升級計數段仍有一處 `Coordinator`**——AC9 逐字只涵蓋 §3 前言三條 Gate 定義＋mermaid＋`:34` 映射句，該處在射程外。**請裁定歸誰。**
4. **§0.1 的懸空逐字引用**（「仍算現役、仍佔資源交集檢查」，改動前即存在）——⛔ 無 AC 涵蓋。§0.1 現已標 superseded／歷史說明，風險降低但字串仍在。**請裁定是否要開卡。**
5. **資源宣告補：`cli/tests/test_pollution_check.py`。**

---

### 九 · 未驗清單（逐項＋各自原因；三分類承接 canonical §6.4.2）

**驗不了**

1. 「canonical 內⛔ 無其他懸空引用」——我驗的是**字面** grep（節號、序列關鍵字、四個裁撤名），⛔ 證不出不存在：以別的措辭指向被改動內容的散文本量法搜不到。**這是下界。**
2. 八份 stage-rules 與新 §0.0／closeout 進入子句的**內容正確性**（是否忠實於決議 §三／§八）——條數與逐行搬遷我驗了，語意等價是內容判斷。
3. §0.1 標 superseded 後，repo 外的讀者（cpbl 等）是否仍會誤讀——本 repo 內無法驗。

**沒去驗**

4. `templates/` 五份交接範本是否需隨六角色表更新——W2B 射程。
5. `MODEL_ROUTING.md`／`ADOPTION.md`／`tasks/INIT-AIWF-PRODUCT1` 的外部指向——AC9 逐字排除，PM 另登清單項。
6. `cpbl-analytics` 側受本次改寫的影響——切換 Initiative 射程，未開該 repo。
7. #228 清單項的現況。
8. canonical §5 那一處 `Coordinator` 的影響面。

**刻意不驗**

9. 跨家族裁決含身分自述——審核階段，⛔ 非執行者工作。
10. `stale_entries` ⛔ 不進 rc 的敞口大小——AC4 把 pass criterion 寫死成單一判準，⛔ 不自行加第二個。**委給查核者判 AC 本身是否該修。**
11. `self_reference` 分類是否構成可濫用的通道——設計理由（不收斂）與成員判準（§6.2 的「工具或測試檔」）已就地寫明並由測試釘死。**委給查核者判。**
12. 「AC2 全節帶標記」與「AC3 v2 ⛔ 不得整段覆蓋」的字面衝突該怎麼收——我取後者並逐字寫出涵蓋範圍。**這是規格層裁定，⛔ 非我的判斷。**

---

### 十 · 決議 §八「執行 12」逐條回應（三值＋evidence）

| # | 條 | 三值 | evidence |
|---|---|---|---|
| 1 | worktree 路徑紀律 | 已遵循 | 本輪全程在 worktree 根執行；上一輪的 cwd 失誤已改用 `uv run --directory cli`，本輪⛔ 未再發生 |
| 2 | 逐檔 add、SHA 用 `rev-parse` | 已遵循 | 兩次 commit 前 `git add -A` 後逐項核 `git status --porcelain`；所有 SHA 取自 `rev-parse`／`gh --json`，⛔ 無一手打 |
| 3 | ⛔ 不截斷輸出 | **發現：** | 見失誤登記 2（NC2 的 rc 取到中間 `echo`）；已重跑，最終證據全部 stdout／stderr／rc 分開落檔 |
| 4 | `rc=0` ⛔ 不等於成功 | **發現：** | 同上——那次 `rc=0` 是假的。本輪所有守衛除 rc 外都另看被改變的狀態（counts JSON、oracle 值、pytest 通過數） |
| 5 | 宣告成功前核那次執行的識別碼 | 已遵循 | CI run `databaseId` 與 `headSha` 逐字比對；紅的那一次（`33490469927`）也逐字登記，⛔ 未略過 |
| 6 | 驗證器 `import` ⛔ 不重打 | 已遵循 | inventory 與 manifest 產生器皆 `importlib` 載入 `prose_number_scan` / `pollution_check` 後呼叫其函式；13 族由 `pitfalls.roster_for('執行')` 取；測試對決議 §二 是**解析**⛔ 不是抄一份 |
| 7 | 複驗要用會通過的樣本 | 已遵循 | NC2 用真實 canonical 複本（41 筆中 40 筆仍核准）；shallow 負控用真的 `--depth 1` clone，⛔ 不是模擬 |
| 8 | 算術上不可能的結果最先響 | 已遵循 | `29 vs 16`、`100 vs 99` 兩組先複現才動手；manifest 重產後 `42 條目 / 45 occurrence` 的差額逐筆對得上 |
| 9 | 刻意行為就地留註解 | 已遵循 | 五處：自指⛔ 不走 manifest 的不收斂證明、`SELF_REFERENCE_PATHS` 的成員判準、§0.1 註解為何不抄原文、§0.0 標記的涵蓋範圍、§3 動作者改寫⛔ 不得外推 |
| 10 | 修過期引用最容易留下新的過期引用 | **發現：** | 見失誤登記 3——修「§0.1 自稱過期」時，我的修法本身製造了第二處 |
| 11 | 交付物寫事實⛔ 不寫狀態 | 已遵循 | 本報告的 SHA／計數／rc 皆字面值；工作樹與推送狀態寫查詢指令 |
| 12 | 失誤登記與未驗清單逐項⛔ 不摘要 | 已遵循 | 「六」5 項、「九」12 項，逐項展開 |

---

### 十一 · 給查核者的入口

```bash
git fetch origin && git checkout 2bd2793a30ce73fe961165d8d97d11f6a63d9fcf
```

- 基線＝`f656a678e540d4083740e0f30f1214e887e42c04`（釘死字面；`pollution_check.py` 的 `BASE_SHA` 同值）。
- 八份檔的 move 在**第一輪**的 `0c555208a54795ab24cdd543d276c8d041f90504`，預設相似度門檻下顯示為 delete+add，請用 `git show --stat -M30% 0c55520`。
- ⚠️ `python3 scripts/pollution_check.py` **需要 `BASE_SHA` 在你的樹上**——shallow clone 會 `CalledProcessError` 並以 rc=2 印 `[checker-error]`（⛔ 不是靜默通過）。查核請用完整 clone，或用 `--files` 直接指定。


## Comment 5492026410 · 2026-09-01T09:40:25Z

<!-- wf-review-event:v1 card_id=WF-REDESIGN-W2A source_sha=2bd2793a30ce73fe961165d8d97d11f6a63d9fcf attempt_id=WF-REDESIGN-W2A-e0-2bd2793a30ce73fe961165d8d97d11f6a63d9fcf -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-REDESIGN-W2A`　attempt_id：`WF-REDESIGN-W2A-e0-2bd2793a30ce73fe961165d8d97d11f6a63d9fcf`
- 查核者：Codex@OpenAI（gpt-5.6-sol，session 01a05c4e-f0a8-7523-9dc0-30a53f5a07eb）　escalation_epoch：0
- source_sha：`2bd2793a30ce73fe961165d8d97d11f6a63d9fcf`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-09-01T17:40:21+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git status --porcelain=v1; git merge-base origin/main HEAD; git rev-parse origin/main`
  - HEAD=2bd2793a30ce73fe961165d8d97d11f6a63d9fcf；工作樹乾淨；merge-base 與 origin/main 均為 f656a678e540d4083740e0f30f1214e887e42c04，入口 SHA 綁定成立。
- `uv run --directory cli pytest -q`
  - 1617 passed, 1 skipped in 67.03s，rc=0。
- `python3 scripts/prose_number_scan.py`
  - total=206；unclassified/dead_entries/invalid_entries/claims_mismatch/uncovered_claims/extra_claims 七項全為 0，rc=0。
- `python3 scripts/pollution_check.py --json`
  - scanned_files=16、token_count=16、pollution_token_count=13、total_hits=188、self_reference_count=143、unapproved_count=0、approved_entries=42；invalid/stale/unreadable 皆空，rc=0。三個自指檔仍在 post-image 母體，143 筆逐 occurrence 列出並逐檔逐 token 計數，符合 canonical §6.2 的可見列計要求；分類不是從母體排除。
- `對 cli/tests/test_pollution_check.py 的 Discovery lead、同行重複與自指三組負控逐項實跑`
  - 決議 §二 13 個污染符與 POLLUTION_TOKENS 逐字同序；Discovery lead fixture 得 unapproved_count=1；同行兩次 needs-deploy 在配額 1 時紅、配額 2 時綠；SELF_REFERENCE_PATHS 恰為 checker、manifest、測試檔三項且全部進母體。
- `以臨時 bare origin 建立真正的 git clone --depth 1，分別檢出 4a7dc268d4973500832e5865655fb493fe73753e 與 2bd2793a30ce73fe961165d8d97d11f6a63d9fcf，執行 uv run --directory cli pytest -q tests/test_pollution_check.py`
  - 兩棵樹皆 rev-parse --is-shallow-repository=true 且 cat-file 基線 SHA rc=1；舊版 1 failed, 3 passed（CalledProcessError on git diff BASE），新版 5 passed。修法確實把測試判準搬到合成樹，未吞例外、未改 CI fetch-depth。
- `gh run view 33490469927 與 33490886848 --json event,headSha,conclusion,jobs`
  - 33490469927 是 push @ 4a7dc268、pytest failure；33490886848 是 push @ 2bd2793a、success，headSha 與本次 source_sha 完全相同。
- `rg/cmp 核對 AI_WORKFLOW.md §0.0、§0.1、§3 與 stage-rules/closeout.md`
  - §0.0 的尚未切換標記只涵蓋目標模型，明文排除現行有效強制句；舊值段逐句標效力與 owner，無整段覆蓋殘留。§0.1 有 superseded 標記且目標狀態自稱全檔僅 §0.0 一處；結案觸發只在 closeout 新居所，列審核／研究／維護三條入邊。§3.1、§3.2、§3.3 與 R1 source_sha 逐段相同，三條 Gate 動作者與 mermaid 已按 AC9 收斂。
- `rg '^| D[1-7].*§0\\.1' AI_WORKFLOW.md；讀取 AI_WORKFLOW.md §0.1 執行者狀態表 #1/#2/#3/#3b/#4`
  - §0.2 D1–D7 對 §0.1 零引用，PM 的節次更正成立；五列確在 §0.1。#1=切換 Initiative、#2=子卡 open 驗證、#3=§0.0、#3b=查核者人工審；#4 仍逐字為「承接者＝⛔ 尚無具名卡」。
- `git interpret-trailers --parse 逐筆核六個 commit；uv run wfcli doctor .. --registry none --commit-trailers --commit-range f656a678e540d4083740e0f30f1214e887e42c04..HEAD`
  - 六筆皆解析 Requested-by、Planned-by、Implemented-by、Co-authored-by；doctor 統計合規 6、違規 0。
- `python3 scripts/canonical_citation_scan.py；python3 scripts/qualified_pointer_scan.py；python3 scripts/replay_escalation_rules.py；uv lock --directory cli --check；grep -l 舊語彙 stage-rules/*.md | wc -l`
  - citation 命中 0／排除 0；qualified pointer 紅 0；escalation replay rc=0；lock check rc=0；過渡橫幅命中恰 8 檔。

### findings（1，其中 blocking 1）

- **WF-REDESIGN-W2A-R2-001**　severity=major　blocking=true　class=authoritative-artifact　attribution=planner　root_cause_id=`required-successor-left-unassigned`
  - evidence：卡面 AC8 第 4 步逐字要求 §0.1 執行者狀態表的 #1/#2/#3/#3b/#4「5 列逐列補承接者」。被審 AI_WORKFLOW.md:270-274 中前四列各有具體承接者，但 :274 的 #4 仍逐字寫「承接者＝⛔ 尚無具名卡」；這是沒有承接者的明示，不是完成承接。其理由同時確認決議 §十的 W3′ 清單未含此項、§0.2 D4 只寫已登記而未指名卡號；#228 的現行 body／追記也只承接 claim 事件、§3 裁撤角色、§5 Coordinator 與 §0.1 懸空引用，沒有承接本列。因此 AC8 的封閉五列仍缺一列，不能以「誠實揭露無 owner」等同「已補 owner」。
  - disposition：由需求方／規劃者先裁定 #4 的具名承接者並修訂卡面或既有承接卡，再把該具名 owner 回寫表列；若需求方真正要的是「允許無承接者、只須揭露」，則須明文修訂 AC8 第 4 步並說明為何「結案不可由角色直接設定」這項目標不需後續落地。執行者不得自行把它塞進 W3′、切換 Initiative 或 #228。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-REDESIGN-W2A-e0-2bd2793a30ce73fe961165d8d97d11f6a63d9fcf
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: Codex@OpenAI（跨家族查核）
findings:
  - finding_id: WF-REDESIGN-W2A-R2-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: planner
    root_cause_id: required-successor-left-unassigned
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5492155288 · 2026-09-01T09:51:17Z

## 交付報告 v3 — WF-REDESIGN-W2A（R2 退回後重送）

> **形式**：對 [v2 報告](https://github.com/ruan6047/ai-workflow/issues/219#issuecomment-5491714806) 的**追加更正段**。v2 的「三／四／五（除 CI 表）」等節⛔ 未失效、⛔ 不重貼；本段只載本輪的差異與重跑值。

### 信封（更正）

| 欄 | 值 |
|---|---|
| **給查核者的入口 SHA** | **`f61444c65a6d7433f16875d82c3077c7e70c58ac`** |
| 上一輪 attempt | `WF-REDESIGN-W2A-e0-2bd2793a30ce73fe961165d8d97d11f6a63d9fcf`（REQUEST_CHANGES，`core_pain_resolved=yes`，1 blocking） |
| iteration | 2 |
| session ID | `e34c8786-1249-41ff-ad3d-a8e31915dbfb` |
| **實際模型／卡面建議層級／偏離** | `claude-opus-5`（Claude Opus 5@Claude Code）／建議 高階型／**偏離：無** |
| merge-base（釘死字面） | `f656a678e540d4083740e0f30f1214e887e42c04`（`origin/main` 本輪未前進） |
| 分支 | `claude/wf-redesign-w2a-rules-0631e8` |

其餘信封欄逐字沿用 v2。工作樹與推送狀態的查詢方法（⛔ 不寫狀態）：`git -C <worktree> status --porcelain=v1`、`git rev-parse HEAD`、`git ls-remote origin claude/wf-redesign-w2a-rules-0631e8`。

---

### 一 · 本輪 commit（1 筆，1 行）

| SHA | 主旨 |
|---|---|
| `f61444c65a6d7433f16875d82c3077c7e70c58ac` | `docs(canonical): name W3′ as the successor for the closeout escape hatch` |

`git diff --stat 2bd2793 HEAD` ⇒ `AI_WORKFLOW.md | 2 +-`／`1 file changed, 1 insertion(+), 1 deletion(-)`。

---

### 二 · R2-001 處置

§0.1 執行者狀態表 **row #4**「§0.1 結案不可由角色直接設定」的承接者欄，由
「**承接者＝⛔ 尚無具名卡**」改為「**承接者＝`WF-REDESIGN-W3′`**（需求方 2026-09-01 裁定；
清單項 `ruan6047/ai-workflow#221`，開卡時列入射程）」。

⚠️ **這是照抄裁定，⛔ 不是我自行指派。** 查核裁決逐字寫「執行者不得自行把它塞進 W3′、
切換 Initiative 或 #228」——我上一輪也是因為這個理由才填「尚無具名卡」。本輪的差別是
**需求方已裁定**，且 PM 已在 #221 掛第三則開卡註記（`issuecomment-5492051143`）載明
W3′ 開卡時須列入射程、寫入面在 `cli/src/wf_cli/commands/handoff_cmd.py`。

理由一併寫進該列（⛔ 不只改指標）：逃生門 `handoff_cmd.py` 的 `if args.status:` 在 CLI
內部 ⇒ 屬 W3′ 面；且它是 `if`／`elif` 的**第一個**分支，走它就整個跳過前身狀態閘門 ⇒
**靜默繞過、人工審抓不到**，故⛔ 不適用「承接者＝查核者人工審」那種弱承接。並就地標明
這是**指向尚未開的卡**，形狀同本表第 1 列——未開卡承接是本表已接受的形狀。

**AC8 第 4 步的封閉五列，逐列具名（機械列出，⛔ 非人工聲明）**

```
  #1: 切換 Initiative
  #2: 子卡的 `open` 驗證
  #3: §0.0
  #3b: 查核者人工審
  #4: `WF-REDESIGN-W3′`
列數： 5
```

`grep -c '尚無具名卡' AI_WORKFLOW.md` ⇒ **0**。

**射程**：⛔ 未動 CLI、⛔ 未開卡、⛔ 未改卡面、⛔ 未動 #228 與 #221 的 body——本輪就這一列。

---

### 三 · 驗證（全部重跑，stdout／stderr／rc 分開取）

| # | 指令 | rc | stdout（逐字） | stderr |
|---|---|---|---|---|
| 1 | `python3 scripts/pollution_check.py` | `0` | `{"scanned_files": 16, "token_count": 16, "total_hits": 188, "self_reference_count": 143, "unapproved_count": 0, "approved_entries": 42}` | 空 |
| 2 | `python3 scripts/prose_number_scan.py` | `0` | `{"total": 206, "unclassified": 0, "dead_entries": 0, "invalid_entries": 0, "claims_mismatch": 0, "uncovered_claims": 0, "extra_claims": 0}` | 空 |
| 3 | `python3 scripts/canonical_citation_scan.py` | `0` | `命中（不含排除）：0` | — |
| 4 | `grep -l 舊語彙 stage-rules/*.md \| wc -l` | `0` | `8` | 空 |
| 5 | `uv run --directory cli pytest -q` | `0` | `1617 passed, 1 skipped in 65.68s` | — |
| 6 | `python3 scripts/qualified_pointer_scan.py` | `0` | — | — |
| 7 | `python3 scripts/replay_escalation_rules.py` | `0` | — | — |
| 8 | `uv lock --directory cli --check` | `0` | — | — |

**commit trailer**：`wfcli doctor . --registry none --commit-trailers --commit-range origin/main..HEAD` rc=0，逐字「統計：違規 0／界線前（不判違規）0／合規 **7**／無所要求 0（共 7 筆）」。

**AC4 負控**：本輪⛔ 未重跑——改動是 canonical 一行敘述，⛔ 未觸及 checker、manifest 或 token 集合（`git diff --stat` 只有 `AI_WORKFLOW.md`）。v2 的 NC1–NC4 逐字仍成立，⛔ 不重貼。⚠️ **這是「沒去驗」⛔ 不是「已驗」**——見「五 · 未驗清單」第 1 項。

**CI**：run `33494224826`、`conclusion=success`、`headSha=f61444c65a6d7433f16875d82c3077c7e70c58ac`
——**與本報告「給查核者的入口 SHA」逐字相同**。查詢：
`gh run list --repo ruan6047/ai-workflow --branch claude/wf-redesign-w2a-rules-0631e8 --json databaseId,status,conclusion,headSha`。
⚠️ 是 **push 事件（分支頭）**，⛔ 不是合併結果。本卡四次 CI 的完整清單（含 `33490469927` 那次
**failure**）見 v2 報告「五」。

---

### 四 · 踩坑族清冊（`import wf_cli.pitfalls; roster_for('執行')`，13 族）

```
宣稱超過證據：已檢查
列舉或覆蓋不完整：已檢查
交付未落地或未接線：已檢查
文件與現實漂移：已檢查
狀態轉移或生命週期：已檢查
可重現性不足：已檢查
並發或時序不安全：已檢查
資源或寫入集宣告：已檢查
守衛涵蓋不足或可被繞過：已檢查
身分或歸屬對應錯誤：發現：本列的承接者是**需求方裁定**⛔ 非我的判斷；上一輪我填「尚無具名卡」正是因為裁決禁止執行者自行指派。⇒ 這一行的歸屬是「照抄裁定」，若裁定本身被推翻，該列要跟著改，⛔ 不得引本表當作 W3′ 射程的獨立依據。
程序或規格照字面不成立：已檢查
留痕失真或遺失：已檢查
解析或正規化錯誤：已檢查
```

⚠️ v2 登記過而**本輪仍然成立**的三筆 finding（⛔ 不因為本輪沒重犯就消失）：
`stale_entries` 不進 rc（AC4 寫死單一判準）／§5 升級計數段仍有一處 `Coordinator`（AC9 射程外）／
§0.1 那處改動前就存在的懸空逐字引用。逐字見 v2 報告「七」與「八」。

---

### 五 · 未驗清單（本輪增量；v2 的 12 項⛔ 未失效）

**沒去驗**

1. **AC4 的四支負控本輪⛔ 未重跑。** 原因：本輪 diff 只有 `AI_WORKFLOW.md` 一行敘述，
   ⛔ 未觸及 checker／manifest／token 集合。⚠️ 我**沒有**驗「這一行不會影響負控結果」——
   只驗了 `pollution_check.py` 主跑仍 `unapproved_count=0`。
2. `#221` 開卡時是否真的把本項列入射程——那是未來的事，本卡⛔ 驗不到；PM 的留痕
   （`issuecomment-5492051143`）是**宣稱**⛔ 不是機制。
3. `handoff_cmd.py` 的 `if args.status:` 分支今日行為——我引用的是 §0.1 表列與 PM 註記的
   逐字描述，⛔ 本輪未自行讀碼複驗。

**刻意不驗**

4. 跨家族裁決含身分自述——審核階段，⛔ 非執行者工作。
5. 「未開卡承接」這個形狀本身合不合理——本表第 1 列已是先例、且裁定在先，⛔ 非我的判斷。

---

### 六 · 失誤登記（本輪）

**⛔ 無新增。** 本輪為單一行的照抄落檔，未發生新的失誤。
⚠️ v2 登記的 5 項（CI 紅／rc 取錯／自我推翻的註解／`SELF_REFERENCE_PATHS` 漏測試檔／
輔助腳本誤導輸出）**⛔ 不因為本輪乾淨而註銷**，逐字仍在 v2 報告「六」。

---

### 七 · 給查核者的入口

```bash
git fetch origin && git checkout f61444c65a6d7433f16875d82c3077c7e70c58ac
```

- 本輪 diff：`git diff 2bd2793 f61444c -- AI_WORKFLOW.md`（1 行）。
- 基線＝`f656a678e540d4083740e0f30f1214e887e42c04`（釘死字面；`pollution_check.py` 的 `BASE_SHA` 同值）。
- ⚠️ `python3 scripts/pollution_check.py` 需要 `BASE_SHA` 在你的樹上——shallow clone 會以
  rc=2 印 `[checker-error]`（⛔ 不是靜默通過）。請用完整 clone，或用 `--files` 直接指定。
- 八份 stage-rules 的 move 在 `0c555208a54795ab24cdd543d276c8d041f90504`，
  請用 `git show --stat -M30% 0c55520`（預設門檻下顯示為 delete+add）。


## Comment 5492309835 · 2026-09-01T10:05:06Z

<!-- wf-review-event:v1 card_id=WF-REDESIGN-W2A source_sha=f61444c65a6d7433f16875d82c3077c7e70c58ac attempt_id=WF-REDESIGN-W2A-e0-f61444c65a6d7433f16875d82c3077c7e70c58ac -->
## 查核裁決：APPROVE

- 卡：`WF-REDESIGN-W2A`　attempt_id：`WF-REDESIGN-W2A-e0-f61444c65a6d7433f16875d82c3077c7e70c58ac`
- 查核者：Codex@OpenAI（gpt-5.6-sol，session 01a05c4e-f0a8-7523-9dc0-30a53f5a07eb）　escalation_epoch：0
- source_sha：`f61444c65a6d7433f16875d82c3077c7e70c58ac`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-09-01T18:05:03+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git status --porcelain=v1; git merge-base origin/main HEAD; git rev-parse origin/main`
  - HEAD=f61444c65a6d7433f16875d82c3077c7e70c58ac；工作樹乾淨；merge-base 與 origin/main 均為 f656a678e540d4083740e0f30f1214e887e42c04，入口 SHA 綁定成立。
- `git diff --stat 2bd2793a30ce73fe961165d8d97d11f6a63d9fcf..HEAD; git diff --check f656a678e540d4083740e0f30f1214e887e42c04..HEAD`
  - R3 delta 恰為 AI_WORKFLOW.md 一檔 1 insertion/1 deletion，且 diff --check rc=0。唯一語意改動是 §0.1 執行者狀態表 row #4 的承接者由「尚無具名卡」改為 WF-REDESIGN-W3′。
- `gh api repos/ruan6047/ai-workflow/issues/221/comments；核對 issuecomment-5492051143 與 AI_WORKFLOW.md §0.1 row #4`
  - 需求方留言明確裁定承接者為 WF-REDESIGN-W3′，並要求 W3′ 開卡時追加此射程、具名寫入面 cli/src/wf_cli/commands/handoff_cmd.py；canonical row #4 如實引用該裁定與清單項。這同時具備 owner、落地時點與寫入面，不是「將來處理」的換句話揭露，R2-001 已閉環。該列只記錄裁定，W3′ 射程的獨立權威仍是需求方留言，未把執行者自述倒置成授權。
- `uv run --directory cli pytest -q`
  - 1617 passed, 1 skipped in 68.75s，rc=0。
- `AC4 四支負控（臨時 fixture、錨點漂移、focused tests、真正 git clone --depth 1）`
  - (1) 無 allowlist 的 📥Backlog／needs-deploy／Discovery lead 三筆皆逐 occurrence 報紅，rc=1；(2) 將已核准 control-plane 所在行做單字漂移後，該 occurrence 失配並報紅，rc=1；(3) uv run --directory cli pytest -q tests/test_pollution_check.py 為 5 passed；(4) 兩棵淺複製皆 is-shallow=true 且基線物件不存在，舊版 4a7dc268 為 1 failed, 3 passed（git diff BASE 拋 CalledProcessError），新版 f61444c 為 5 passed。修法確實使用合成樹，未吞例外、未改 CI checkout。
- `python3 scripts/prose_number_scan.py --json; python3 scripts/pollution_check.py --json`
  - prose total=206，七類異常全為 0，rc=0。pollution scanned_files=16、token_count=16、total_hits=188、self_reference_count=143、unapproved_count=0、approved_entries=42、stale_entries=0，rc=0；自指三檔仍在母體，143 筆逐 occurrence 可見列計，符合 canonical §6.2。
- `靜態核對卡面 spec_version 2 的 AC1–AC9 與 source tree`
  - AC1：章序 1→2→0→3 且角色表恰六列。AC2/AC3v2：§0.0 有 8 階段、10 狀態與 delta，未切換標記明文不涵蓋現行強制句；舊值域段逐句標示效力與 owner，無整段覆蓋殘留。AC6/6b/7：八份 stage-rules 齊備、舊草稿不存在、需求詞命中數依序 15/14/8/12/9/0/0/7、八檔皆有尚未生效標記與舊語彙過渡橫幅。AC8：§0.1 已標 superseded，理由仍留 canonical，closeout 以最後適用階段完成為入口並列審核／研究／維護三條入邊；五列承接者現為切換 Initiative／子卡 open 驗證／§0.0／查核者人工審／WF-REDESIGN-W3′。AC9：§3 Gate 動作者已收斂；§3.1/3.2/3.3 與 R1 source 逐段相同，限縮射程未越界。故 AC1–AC9 全數成立。
- `cmp/rg 核對 AI_WORKFLOW.md §3.1、§3.2、§3.3 與非射程殘留`
  - §3.1 明確不得退役且本輪未變，§3.2/§3.3 亦未動。v2 三筆非 blocking 觀察未被偽稱修復：stale_entries 不進 rc 是 AC4 明定的單一判準；§5 的 Coordinator 與 §0.1 改動前即存在的懸空逐字引用仍在、已由需求方併入 #228，均不擴張本卡射程。
- `gh run view 33494224826 --repo ruan6047/ai-workflow --json event,headSha,conclusion,jobs`
  - push run conclusion=success，headSha=f61444c65a6d7433f16875d82c3077c7e70c58ac；checkout、lock、pytest 與 escalation replay steps 均 success。
- `git interpret-trailers --parse 逐筆核七個 commit；uv run wfcli doctor .. --registry none --commit-trailers --commit-range f656a678e540d4083740e0f30f1214e887e42c04..HEAD --require-planned-by`
  - 七筆 commit 各可解析四個 trailer；doctor 統計合規 7、違規 0。
- `python3 scripts/canonical_citation_scan.py; python3 scripts/qualified_pointer_scan.py; python3 scripts/replay_escalation_rules.py; uv lock --directory cli --check; grep -l 舊語彙 stage-rules/*.md | wc -l`
  - canonical citation 命中 0／排除 0；qualified pointer 紅 0；escalation replay 114/114 通過；lock check rc=0；過渡橫幅命中恰 8 檔。

### findings（0，其中 blocking 0）

- （無）

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-REDESIGN-W2A-e0-f61444c65a6d7433f16875d82c3077c7e70c58ac
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: Codex@OpenAI（跨家族查核）
findings: []
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5492768223 · 2026-09-01T10:46:55Z

## 結案報告 — WF-REDESIGN-W2A（結案階段 ③，PM 呈）

⚠️ 本報告的第五段依 `stage-rules/closeout.md` §3／`pm-conduct.md` 對價條款須**逐字轉錄**未驗與失誤兩清單；該義務與「不超過一屏」在本卡字面衝突，我取逐字轉錄並在此標明取捨（⛔ 不以「N 項」摘要，[[evidence-must-transcribe-not-summarise]] 同族）。

### 一 · 痛點 → 處置

**痛點（卡面逐字）**：canonical §0（505 行，54%）描述的 15 值單欄序列已被決議 8×10 取代但未改寫；§1 角色表 7 角色含三個已裁撤角色；必讀的 §1/§2（34 行）埋在 §0 之後。

**處置**：§0 重寫為 8 階段×10 狀態＋轉移 delta 制（全節帶「尚未切換」標記，⛔ 不覆蓋仍具強制力的句子）；§1 換 6 角色表；§1/§2 前移至 §0 之前；§0.1 退役四步（AC8）；§3 Gate 塊處置（AC9，⛔ 不擴及 §3.1／§3.2／§3.3）；8 份 stage-rules 由 `docs/research/drafts/stage-rules/` move 至 `stage-rules/` 生效；tier-rules 框架層檔上線；污染符 allowlist-aware checker（`scripts/pollution_check.py`）。R3 裁決 `core_pain_resolved: yes`。

### 二 · 裁決摘要（blocking 清零）

| 輪 | source_sha | 結果 | findings | blocking |
|---|---|---|---|---|
| R1 | `27ff0b2f28d4d26f48c640e056044222ea5e968e` | REQUEST_CHANGES | W2A-R1-001／-002／-003 | true |
| R2 | `2bd2793a30ce73fe961165d8d97d11f6a63d9fcf` | REQUEST_CHANGES | W2A-R2-001 | true |
| R3 | `f61444c65a6d7433f16875d82c3077c7e70c58ac` | **APPROVE** | 無 | — |

查核者＝Codex@OpenAI（跨家族，需求方 2026-08-30 裁定）。R1-001／-002 屬 planner 歸因，經需求方裁定分別落為 AC3 spec_version 2 與新增 AC8／AC9；R1-003、R2-001 屬 executor 歸因，於 v2／v3 交付修畢。**R3 findings 為空陣列 ⇒ blocking 清零。**

### 三 · merge SHA ＋ CI 指標

- 本體：PR #229 squash → main **`950b3e278371e948900dd381cd7b4e595882c6b0`**（合併內容＝審過的 `f61444c6`，⛔ 非 BEHIND）。
- 合併後於 main 實跑：`prose_number_scan.py` total 206 七項全零／`pollution_check.py` `unapproved_count=0`／AC7 oracle 8／`pytest` **1617 passed, 1 skipped**。
- 合併 commit 的 trailer 五欄經 `git interpret-trailers --parse` 全數解析（W1 的兩種壞法皆已避開）。
- 收尾第 5 步（卡檔封存）：PR #230 rebase → main **`fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2`**；`tests` 與 `tests (branch head)` 皆 pass（57s／1m2s）；inventory 清 w2a 條目 6 筆（143→137），掃描 206→199 七項全零，`tests/test_prose_number_scan.py` 49 passed。
- release handoff：`rc=0`，狀態 🏁完成，cleanup `mode=applied`／已執行 `remove_worktree`／`delete_remote_branch` 本來就不存在／`delete_local_branch` 依授權保留（squash 合併，`cleanup.AUTHORITY_BY_PROOF`）。

### 四 · 四道停下條件逐項

1. **任何 blocking finding 未 resolved** — 不成立。R3 `findings: []`、`review_result: APPROVE`。
2. **CI 非綠，或 merge 後狀態不符預期** — 不成立。PR #229／#230 檢查皆 pass；merge 後以 `gh pr view --json state,mergedAt,mergeCommit` 與 `git rev-parse origin/main` 對照確認 main 真的前進（⛔ 不只看 rc=0）。
3. **分支 BEHIND 且 `gh pr update-branch` 產生衝突** — 不成立。#229 合併時非 BEHIND；#230 自 `950b3e2` 分出，無需 update-branch。
4. **T4 紅線卡 —— 人工 sign-off 不可省略** — **已取得，但留痕形式須注意**：需求方於 2026-09-01 對話中明示「好 merge」（#229）與「CI 綠了就 merge」（#230）。⚠️ **該授權只存在於對話，卡上無對應留言**；若要可稽核，需補一則需求方留痕留言。此處標明，⛔ 不自行代寫。

### 五 · 失誤登記與未驗清單（逐字轉錄）

#### 5.1 失誤登記 — v3「六」逐字

> **⛔ 無新增。** 本輪為單一行的照抄落檔，未發生新的失誤。
> ⚠️ v2 登記的 5 項（CI 紅／rc 取錯／自我推翻的註解／`SELF_REFERENCE_PATHS` 漏測試檔／輔助腳本誤導輸出）**⛔ 不因為本輪乾淨而註銷**，逐字仍在 v2 報告「六」。

#### 5.2 失誤登記 — v2「六」逐字（承前段之不註銷義務）

> 1. **本機綠、CI 紅——我把守衛建在 repo 歷史上。** `test_self_reference_files_are_in_the_population_and_tallied` 對真 repo 呼叫 `post_image_paths(_REPO_ROOT, BASE_SHA)`；GitHub Actions 的 checkout 是 shallow（`fetch-depth` 預設 1），`git diff … f656a678…` 在那棵樹上直接 `CalledProcessError` ⇒ **CI run `33490469927` 在 `4a7dc26` 轉紅**。⚠️ 這是我上一輪報告裡自己寫過「查核者要在合併結果上跑」卻沒推廣到「測試不能假設歷史存在」。修法⛔ 不是吞例外、⛔ 不是改 CI 的 `fetch-depth`（⛔ 不在本卡射程），而是把該判準搬到合成樹上驗；並以 shallow clone 實跑負控證明舊版真的會紅、新版會綠。
> 2. **NC2 第一次跑時 rc 取錯。** 我寫成 `python3 … > o 2> e; echo "####"; echo "rc=$?"`，`$?` 取到中間那個 `echo` 的 **0**，於是一支**實際回 1** 的負控被印成 `rc=0`。當場察覺並改成先存 `NC2_RC=$?` 再印。⚠️ 這正是 `F-執行-03`／`F-執行-04`，而我上一輪才登記過同族。
> 3. **§0.1 的 superseded 註解初稿自我推翻。** 初稿把「本節定義目標狀態」那句原文抄進註解裡宣稱「僅存一處」，結果 grep 得 **2** ⇒ 宣稱當場為假。以 grep 抓到後改寫成不抄原文，並就地留註解說明為什麼不抄。
> 4. **`SELF_REFERENCE_PATHS` 初版只放兩檔。** 新測試檔一寫出來，manifest 產生器就拒絕分類（我放在產生器裡的「⛔ 不得以泛用理由充數」保險絲響了）。canonical §6.2 逐字含「**測試檔**」⇒ 改為三項並由測試釘死。
> 5. **輔助腳本的誤導輸出未修。** `mkallow.py`（scratchpad，⛔ 不在交付物內）的節次分類器對非 canonical 檔仍會算出一個 §，於是 UNHANDLED 診斷行印出無意義的節次。⛔ 未修，此處標明。

#### 5.3 未驗清單 — v3「五」逐字（本輪增量；v2 的 12 項⛔ 未失效）

> **沒去驗**
> 1. **AC4 的四支負控本輪⛔ 未重跑。** 原因：本輪 diff 只有 `AI_WORKFLOW.md` 一行敘述，⛔ 未觸及 checker／manifest／token 集合。⚠️ 我**沒有**驗「這一行不會影響負控結果」——只驗了 `pollution_check.py` 主跑仍 `unapproved_count=0`。
> 2. `#221` 開卡時是否真的把本項列入射程——那是未來的事，本卡⛔ 驗不到；PM 的留痕（`issuecomment-5492051143`）是**宣稱**⛔ 不是機制。
> 3. `handoff_cmd.py` 的 `if args.status:` 分支今日行為——我引用的是 §0.1 表列與 PM 註記的逐字描述，⛔ 本輪未自行讀碼複驗。
>
> **刻意不驗**
> 4. 跨家族裁決含身分自述——審核階段，⛔ 非執行者工作。
> 5. 「未開卡承接」這個形狀本身合不合理——本表第 1 列已是先例、且裁定在先，⛔ 非我的判斷。

#### 5.4 未驗清單 — v2「九」逐字（12 項，⛔ 未失效）

> **驗不了**
> 1. 「canonical 內⛔ 無其他懸空引用」——我驗的是**字面** grep（節號、序列關鍵字、四個裁撤名），⛔ 證不出不存在：以別的措辭指向被改動內容的散文本量法搜不到。**這是下界。**
> 2. 八份 stage-rules 與新 §0.0／closeout 進入子句的**內容正確性**（是否忠實於決議 §三／§八）——條數與逐行搬遷我驗了，語意等價是內容判斷。
> 3. §0.1 標 superseded 後，repo 外的讀者（cpbl 等）是否仍會誤讀——本 repo 內無法驗。
>
> **沒去驗**
> 4. `templates/` 五份交接範本是否需隨六角色表更新——W2B 射程。
> 5. `MODEL_ROUTING.md`／`ADOPTION.md`／`tasks/INIT-AIWF-PRODUCT1` 的外部指向——AC9 逐字排除，PM 另登清單項。
> 6. `cpbl-analytics` 側受本次改寫的影響——切換 Initiative 射程，未開該 repo。
> 7. #228 清單項的現況。
> 8. canonical §5 那一處 `Coordinator` 的影響面。
>
> **刻意不驗**
> 9. 跨家族裁決含身分自述——審核階段，⛔ 非執行者工作。
> 10. `stale_entries` ⛔ 不進 rc 的敞口大小——AC4 把 pass criterion 寫死成單一判準，⛔ 不自行加第二個。**委給查核者判 AC 本身是否該修。**
> 11. `self_reference` 分類是否構成可濫用的通道——設計理由（不收斂）與成員判準（§6.2 的「工具或測試檔」）已就地寫明並由測試釘死。**委給查核者判。**
> 12. 「AC2 全節帶標記」與「AC3 v2 ⛔ 不得整段覆蓋」的字面衝突該怎麼收——我取後者並逐字寫出涵蓋範圍。**這是規格層裁定，⛔ 非我的判斷。**

#### 5.5 PM 側自身失誤（本階段新增）

> 1. **W2A release 第一次 handoff 實為 `rc=5` 被吃掉。** 指令尾接 `2>&1 | tail -4`，wfcli 的拒絕行走 stderr、併流後被推出截斷窗 ⇒ 我一度以為已寫入。以查卡 Log 察覺。實測基線：本 session wfcli 呼叫 1037 次、致命型 `2>&1|tail` 284 次（27%）。處置＝`~/.claude/settings.json` 已上 PreToolUse／Bash hook 機械阻擋該形狀（正例被擋、`> 檔 2>&1` 與單獨 `| tail` 兩負控通過）。
> 2. **封存 commit 直推 main 被 ruleset 擋（GH013，需 PR＋`tests`）。** 我先提交到 main 才發現，改以分支 `claude/archive-w2a-spec` + PR #230 走，並 `git reset --hard 950b3e2` 復原本地 main。⛔ 無殘留。

### 六 · 清單收斂核對

卡面表單 `list_convergence: []` ⇒ **本卡未宣告涵蓋任何清單項，故無項可關**（`F-結案-04`：真解決才關）。

在飛的後繼清單項（⛔ 非本卡涵蓋、⛔ 不在此關閉）：#220（W2B）、#221（W3′）、#213（守衛治理）、#227（main trailer 守衛缺口）、#228（取代清單覆蓋缺口）。其中 #221 承接 v2「九」第 5 項與 v3「五」第 2 項所指的外部指向與後繼射程。

### 七 · 翻案把手

- **revert**：`git revert 950b3e278371e948900dd381cd7b4e595882c6b0`（本體，squash 單 commit）；`git revert fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2`（封存，含 inventory 6 筆與 rename）。兩者皆須以 PR 走（main 有 ruleset），revert 後須重跑 `prose_number_scan.py --json` 確認七項全零。
- **review-correction**：對 R1／R2／R3 任一裁決有異議，以 `wfcli review` 新事件寫回，⚠️ **須有新的 `source_sha`**（同一 source_sha 第二則裁決會被 `marker_quarantined`）；卡面純修正輪沒有新 SHA 時走留言記錄，⛔ 不遞增 epoch。
- **卡本身**：#219 現為 CLOSED／🏁完成；封存（`archiveProjectV2Item`）**尚未執行**，待需求方 ④ 確認。⚠️ archived 項仍留在 items 連線，⛔ 不等於退出母體。

---

**④ 需求方**：請確認或退回補驗。確認後我執行 ⑤ 完成＋封存。


## Comment 5492843024 · 2026-09-01T10:54:08Z

需求方 ④ 確認留痕（2026-09-01，PM 轉錄）

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`；⚠️ 發文者身分**不等於**決策者身分。決策原文出自需求方於本機 Claude Code 對話中的訊息，逐字為：「確認W2A」（回應本卡上一則結案報告 `issuecomment-5492768223`）。該對話 transcript 於需求方本機可核。

⇒ 結案階段 ④ **確認**（⛔ 非退回補驗）。

---

**⑤ 完成＋封存的執行狀況：完成已達、封存⛔ 未執行，原因如下**

1. **終態**：本卡已於 release handoff 時進 🏁完成（`950b3e278371e948900dd381cd7b4e595882c6b0`），⛔ 無待補動作。
2. **封存無 writer**：`stage-rules/closeout.md` §1 指定產出物含「封存（`archiveProjectV2Item`）」，但 `wfcli` 的子指令集為 `open／assign／amend／deploy-declare／deploy-state／handoff／review／checkpoint／contract-baseline／doctor／snapshot`——**沒有封存指令**。而 `cli/README.md` 將本 CLI 定為狀態面唯一寫入通道。以 `gh api graphql archiveProjectV2Item` 直打會是繞過該通道的狀態面寫入，故 PM ⛔ 不自行執行，上呈需求方裁定。
3. **母體實查（2026-09-01）**：Project #4 共 **215** 個 items，`isArchived=true` 的有 **0** 個——含同樣已達 🏁完成 的 #214（W0）與 #217（W1）。⇒ 「結案要封存」這條規則**自訂立以來從未被執行過一次**；若只封存本卡，反而使三張同族卡狀態不一致。
4. ⚠️ 另注意：`archiveProjectV2Item` 後項目**仍留在 items 連線**（`isArchived=true` 但查詢照回，連線無 `includeArchived` 可濾）——封存⛔ 不等於退出母體，唯一退出手段是 `deleteProjectV2Item`。故此步的實際效果是「加一個旗標」，⛔ 不是「清出看板」。

**PM 未驗**：`archiveProjectV2Item` 對 Project #4 的實際行為未實跑（⛔ 不在無裁定下寫入）；上述第 4 點取自 W1 開卡時的實測留痕，⛔ 非本次重驗。


## Comment 5492896820 · 2026-09-01T10:59:00Z

封存步驟裁定（2026-09-01）

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`；⚠️ 發文者身分**不等於**決策者身分。需求方於本機 Claude Code 對話中逐字裁示：「原則上選乙 但幫我研究三輪 沒問題就裁定」。以下裁定由 PM 依該授權作出，研究三輪的量測逐項附上。

## 裁定：⑤ 的「封存」⛔ 不執行；⛔ 亦不開新清單項

**理由（研究三輪）**

**輪 1 — writer 是否真的不存在（碼面窮舉）**：`archiveProjectV2Item` 在非 archive／非 worktree 的 tracked 檔中僅出現 4 處，**全為散文**（`AI_WORKFLOW.md:83`、`AI_WORKFLOW.md:287`、`stage-rules/closeout.md:10`、決議紀錄），另 1 處為 inventory 的 excerpt 引句。`.py` 中出現 **0 次** ⇒ 無 writer，亦**無 reader**（`isArchived` 在碼中同樣 0 次）。

⚠️ **對 PM 前一則說法的更正**：我先前稱直打 GraphQL 會「違反 CLI 紅線」。紅線原文（`cli/README.md:4`）逐字為「**不經本 CLI 對 Ledger 欄位／資源宣告的狀態寫入即違規**（例如直接在 GitHub UI 手改 Project 欄位）」——其射程是 **Ledger 欄位／資源宣告**，而封存是 item 層旗標，**⛔ 不在該字面射程內**。所以「甲＝違規」是我說得太滿。真正的理由改為下面兩輪。

**輪 2 — 這是不是本卡的缺陷（母體量測，2026-09-01 實查）**：Project #4 共 **215** 個 items，交付狀態分佈 127 🏁完成／33 🛑已停止／31 💡需求／17 ⏸阻塞／4 📦已合併／3 📥Backlog ⇒ 終態卡 **160** 張，`isArchived=true` 者 **0** 張。⇒ 這不是 W2A 漏做一步，是一條**對 74% 的看板從未生效過**的規則。單獨封存本卡，只會讓 #214（W0）／#217（W1）與其餘 158 張更不一致。

**輪 3 — 查重（新母體：既有 issue）**：搜尋關鍵字 `封存`／`archive`／`archiveProjectV2Item`／`終態` ⇒ 命中 **#133 `OPS-PROJECT-ARCHIVE-TERMINAL1 終態卡自動封存：把 archiveProjectV2Item 從條文變成可重跑的機械步驟`**（2026-08-24 開，**OPEN**）。其痛點逐字已含「今天 188 張的 isArchived 全部為 false，即該規則從未被執行過一次」，資源宣告已含 `scripts/archive_terminal_items.py`。⇒ **登記用的卡已存在，再開一個是重複**（`stage-rules/list-intake-requirements.md` 查重條件）。⛔ 故不開新項，改為在此指向 #133。

## 效果

- 本卡（#219）停在 **🏁完成**，⛔ 未封存；封存待 #133 提供機械執行者後**與其餘 159 張終態卡一併處理**。
- #133 的驗收條件 1 逐字要求「Discovery 先答：封存後 wfcli 還讀不讀得到那張卡」，⛔ 未答不得批次執行 ⇒ 本卡若單獨封存，反而會製造一個未受該 Discovery 覆蓋的既成樣本。

## PM 未驗（逐項）

1. 「封存後項目仍留在 items 連線」——PM 記憶中有此結論，但**本輪未以已封存樣本複驗**；#133 逐字記載「今天驗不了——⛔ 沒有已封存樣本」。⇒ 此點在本裁定中**⛔ 不作為理由使用**，僅標明存疑。
2. `AI_WORKFLOW.md:287` 稱封存可「移出活卡視圖」——GitHub UI 的 view 過濾行為**未實測**。
3. #133 本身的推進條件未查（見下）。

## ⚠️ 給需求方的一個附帶發現

#133 的卡面首行為「需求：—　規劃：—」，即**需求方欄為空**。依 `stage-rules` 的開卡規則，需求方欄空的卡在後續 assign／痛點比對上會被硬拒 ⇒ #133 目前可能推不動。⛔ PM 不代填該欄（`pm-conduct` 不代填條款），此處只標明。

