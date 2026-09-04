# #177 WF-REDESIGN1 工作流框架重整：8 階段 × 10 狀態、清單制、四波五卡施工（Initiative 父卡）
- state: open  created: 2026-08-30T13:24:11Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/177
- comments: 25

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 高階型；Initiative 父卡的規劃與協調屬架構層；子卡含 W2A canonical T4 紅線，取風險最高者）　查核：待指派（建議 高階型；波 2 為 canonical 紅線改版，查核須跨模型家族或需求方 sign-off——獨立性要求疊加於層級之上；本卡總驗收對照服務目標三項）
- Initiative：WF-REDESIGN　spec 基線：ai-workflow 7d798062b9b37be3ab98d1de58ceebaf42bdcc2e（決議＋brief＋wave-specs＋baseline-universe＋prose-number-inventory；審核輪次見卡留言）
- DB：db_scope=none
- 服務的原始目標：可稽核＋防低級事故＋流程順暢——三者並列，前兩項不得以犧牲第三項的方式達成

## 簡介
<!-- card-brief:begin -->
適用時機：工作流重整**四波五卡**施工（W0→W1→W2A→W2B→W3′，全 aiwf、零不可逆）的 Initiative 父卡；所有波卡以本卡為錨、spec 基線填本卡版本。⛔ 非射程：不自產任何程式碼或條文變更（歸波卡）；⛔ 不碰 cpbl（乙′ 解耦——看板切換、cutover 不可逆段與 cpbl 移植歸切換 Initiative，本卡結案含其清單項建立）；不新增 wfcli 動詞。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：需求方原文（session cc0a7952，2026-08-29）：「可以幫我用fable5 健檢整個ｗｆ流程 這個框架 明明是為了流程順暢 現在卻卡了一個月」「現在是不是又無限開卡了」「目前框架內ＣＬＩ有點過量尤其是很多不該由ＣＬＩ處理的都變成由ＣＬＩ處裡」。量化：開卡 5.2 張/日＞推進 3.9 次/日、在動卡恆 0–5 張、APPROVE 105:REQUEST_CHANGES 150

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": []
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 四波五卡（WF-REDESIGN-W0／W1／W2A／W2B／W3）全數誕生於本卡規劃階段並各自結案；中途追加子卡須升級裁定留痕
- [ ] 本 Initiative 交付＝框架就緒⛔ 不切換（零不可逆、零 cpbl 接觸）；結案條件含切換 Initiative 之清單項建立完成（交棒留痕，內容依決議 §十之二）
- [ ] 本卡⛔ 不自產碼與條文；⛔ 不宣告 file 資源；子卡在飛期間父卡停『執行／進行中』追蹤
- [ ] 硬依賴鏈 W0→W1→W2A→W2B→W3′ 被遵守（前張終態才可開下張）

## 驗證

- [ ] 對照 discovery brief 的待驗證假設逐項有處置留痕（驗證／降級／延後）
- [ ] 回顧移交切換 Initiative（觸發＝cutover 後第 30 張常態卡；fail-safe 2026-10-31 未開切換亦強制檢討）——本卡結案報告載明移交

## Log

- 2026-08-30T21:24:09+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-30T22:26:35+08:00 amend by wf-cli（op f0425f2b）→ 驗收條件：原值「[ ] 五張波卡（波 0–4）全部誕生於本卡規劃階段並各自結案；中途追加子卡須升級裁定留痕；[ ] 60 天回顧點對服務目標三項各有前後對照量測（開卡速率／推進速率／CLI 拒收點數與行數）；[ ] 本卡⛔ 不自產碼與條文；⛔ 不宣告 file 資源；子卡在飛期間父卡停『執行／進行中』追蹤；[ ] 波間依賴序被遵守：波 1 結案後才開波 2；波 3 六步停機程序含 snapshot 前置」→ 新值「五波六卡（WF-REDESIGN-W0／W1／W2A／W2B／W3／W4）全數誕生於本卡規劃階段並各自結案；中途追加子卡須升級裁定留痕；回顧觸發＝cutover 後第 30 張常態卡（⛔ 非 WF-Initiative）結案；fail-safe＝2026-10-31 前未 cutover 則強制檢討；三項指標對照預先登記之基線；本卡⛔ 不自產碼與條文；⛔ 不宣告 file 資源；子卡在飛期間父卡停『執行／進行中』追蹤；硬依賴鏈 W1→W2A→W2B→W3 被遵守（前張終態才可開下張）；波 3 六步停機含 snapshot 前置」（⚠️ 全文：totalCount=0（首寫，平台無前一版））；理由 P1-01（六卡列名）與 P1-03（硬依賴鏈）修正；回顧錨點依 Q4 定案改為樣本觸發＋fail-safe（原 60 天字樣過期）。裁決：https://github.com/ruan6047/ai-workflow/issues/177#issuecomment-5469108595。
- 2026-08-30T22:39:16+08:00 amend by wf-cli（op bbe23367）→ spec 基線：原值指紋 sha256:f65e17bbfffe33584b08e6435577bc61dbceddbf971ca2e5f2960481cc7ac5aa (122 bytes) → 新值指紋 sha256:d408764b764c3278e4ccaeac7877b3991fac02e55ef62f5b7dee405d9405add3 (120 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 P1-05：spec 基線由 cd053af bump 至含全部修正的 main SHA。裁決：issuecomment-5469298925。
- 2026-08-30T22:39:38+08:00 amend by wf-cli（op 20e1b590）→ 驗收條件：原值指紋 sha256:224af4507c1c5f6871525218026c9fab06d29b2c499cc13aeff1dc6f12795b1a (584 bytes) → 新值指紋 sha256:87803327ceddb6e426be9a53877542aab3117bbdad4fd5ea0f5297820d57a3f1 (627 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 P1-06：驗證欄 60 天字樣改樣本觸發；P1-08：A4 改引停機序唯一定義。裁決：issuecomment-5469298925。
- 2026-08-30T22:39:38+08:00 amend by wf-cli（op 20e1b590）→ 驗證：原值指紋 sha256:e1e435ecbce62166214d085230add8c5d0811b299fb39d9fcc4cc78802d82a8d (176 bytes) → 新值指紋 sha256:3fc902010b50381ccb8ea201ee087d0a54e8292143f32174a996909728f7fe27 (193 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 P1-06：驗證欄 60 天字樣改樣本觸發；P1-08：A4 改引停機序唯一定義。裁決：issuecomment-5469298925。
- 2026-08-30T22:52:41+08:00 amend by wf-cli（op 8f0bbbd1）→ spec 基線：原值指紋 sha256:d408764b764c3278e4ccaeac7877b3991fac02e55ef62f5b7dee405d9405add3 (120 bytes) → 新值指紋 sha256:19d8af25da738cb4bf5dc1143124a76f97072ba69d2489b37b1a933666d9a16c (120 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R3 P1-04 續：YAML 修正後基線 bump 至含該修正的 main SHA。裁決：issuecomment-5469364619。
- 2026-08-30T23:17:44+08:00 amend by wf-cli（op cba68057）→ spec 基線：原值指紋 sha256:19d8af25da738cb4bf5dc1143124a76f97072ba69d2489b37b1a933666d9a16c (120 bytes) → 新值指紋 sha256:e5f7441a6e39e84371acf91683fa569f1c2911e59411127c3c96708c913b5e8c (120 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R4 P1-11~20 處置後基線 bump。裁決：issuecomment-5469449938。
- 2026-08-30T23:18:09+08:00 amend by wf-cli（op 7c38044d）→ 驗收條件：原值指紋 sha256:43d07506ba36dfa63c7aed5fd328a41aa836764a56fa5862a679ea48e5596ab8 (643 bytes) → 新值指紋 sha256:57e8c07454be5fd81bdabced059a611688d0e26b5f5e4d96ef250f6e8093e3f3 (651 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 P1-12：A4 依賴鏈改全長並納入 P1-20 前置。裁決：issuecomment-5469449938。
- 2026-08-31T00:39:16+08:00 amend by wf-cli（op a7a76097）→ 驗收條件：原值指紋 sha256:fc15ba140a5ec564ded804318ea5a53808f171e006611c63bca55e40227e34c7 (667 bytes) → 新值指紋 sha256:bd846ba4659110dfe7528d82831c3bbea7bfa1ddd65db94d8bf39d611fbed6cc (548 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 乙′ 解耦（需求方 2026-08-30 裁定）：六卡改五卡、cutover 與回顧移交切換 Initiative、停機序引用自本卡驗收移除。裁決：issuecomment-5469611932。
- 2026-08-31T00:39:16+08:00 amend by wf-cli（op a7a76097）→ 驗證：原值指紋 sha256:2ad3cb0a49d6a54497a3f51118462c479f0bf22770298777aa2e26d4824fbce8 (201 bytes) → 新值指紋 sha256:7a9be5f6a7cd563723e408f7c1844ee53ae61c01c7eb04ad94d354a1209415e9 (256 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 乙′ 解耦（需求方 2026-08-30 裁定）：六卡改五卡、cutover 與回顧移交切換 Initiative、停機序引用自本卡驗收移除。裁決：issuecomment-5469611932。
- 2026-08-31T00:39:42+08:00 amend by wf-cli（op 5da08483）→ spec 基線：原值指紋 sha256:e5f7441a6e39e84371acf91683fa569f1c2911e59411127c3c96708c913b5e8c (120 bytes) → 新值指紋 sha256:970df1703ea0d34029fb38309ced95cc4fa2cfcb62d2ba5a698515957f64dec9 (129 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R5 處置後基線 bump。裁決：issuecomment-5469611932。
- 2026-08-31T10:40:33+08:00 amend by wf-cli（op abc8e405）→ spec 基線：原值指紋 sha256:970df1703ea0d34029fb38309ced95cc4fa2cfcb62d2ba5a698515957f64dec9 (129 bytes) → 新值指紋 sha256:a69f9d1f908abaee2784bd06c9c852f133d47c69b7f7f758a0b61cf7ed05edf4 (118 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R6 五筆處置後基線 bump。裁決：issuecomment-5470031961。
- 2026-08-31T10:41:14+08:00 amend by wf-cli（op 5d911bac）→ 簡介：原值指紋 sha256:b0708803d4354a23d037ff9137b4c7e4a4350b066d98eaaab6af68b4b5895c1b (289 bytes) → 新值指紋 sha256:52f98e2aa39c20d3552431e0a14dce8cb623599283c1e1d2b8e859044bb29731 (441 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 P1-23：簡介現值同步四波五卡與乙′ 解耦。裁決：issuecomment-5470031961。
- 2026-08-31T10:52:09+08:00 amend by wf-cli（op 517cd7e9）→ spec 基線：原值指紋 sha256:a69f9d1f908abaee2784bd06c9c852f133d47c69b7f7f758a0b61cf7ed05edf4 (118 bytes) → 新值指紋 sha256:7dd0a587755b2051a19f91073af7514425bcd65a31f8e0ff256280cfc966d561 (118 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R7 兩筆處置後基線 bump（單次 amend——合併紀律生效）。裁決：issuecomment-5473075216。
- 2026-08-31T11:15:44+08:00 amend by wf-cli（op 97765c9e）→ spec 基線：原值指紋 sha256:7dd0a587755b2051a19f91073af7514425bcd65a31f8e0ff256280cfc966d561 (118 bytes) → 新值指紋 sha256:348f2499d85a84a4688dff2c86d65dbd313e465a8063cb83b23d0035be2a331a (138 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R8 八筆＋佇列處置後基線 bump（單次 amend）。裁決：issuecomment-5473179838。
- 2026-08-31T11:45:27+08:00 amend by wf-cli（op 05291fb8）→ spec 基線：原值指紋 sha256:348f2499d85a84a4688dff2c86d65dbd313e465a8063cb83b23d0035be2a331a (138 bytes) → 新值指紋 sha256:9d4ee4e67167eb6041ad85b291655ad44d064707b81c779272fddf6ab27d9b40 (145 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R9 八筆處置後基線 bump（單次 amend）。裁決：issuecomment-5473325618。
- 2026-08-31T12:01:53+08:00 amend by wf-cli（op f596a336）→ spec 基線：原值指紋 sha256:9d4ee4e67167eb6041ad85b291655ad44d064707b81c779272fddf6ab27d9b40 (145 bytes) → 新值指紋 sha256:00ee5d3e890b8c7059828ad4f5a23a982d90f5164913a90dac0057c03116e293 (132 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R10 五筆處置後基線 bump（單次 amend）。裁決：issuecomment-5473503726。
- 2026-08-31T12:17:10+08:00 amend by wf-cli（op d86de234）→ spec 基線：原值指紋 sha256:00ee5d3e890b8c7059828ad4f5a23a982d90f5164913a90dac0057c03116e293 (132 bytes) → 新值指紋 sha256:b45f2887ddbad718baa7f55ad9bc9ca34cdf8216298a80525be9024d2461378b (135 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R11 三筆反例處置後基線 bump（單次 amend）。裁決：issuecomment-5473595529。
- 2026-08-31T12:29:45+08:00 amend by wf-cli（op 355e05d4）→ spec 基線：原值指紋 sha256:b45f2887ddbad718baa7f55ad9bc9ca34cdf8216298a80525be9024d2461378b (135 bytes) → 新值指紋 sha256:92ea3a114a2a8e892712d3661ec838a9f5d669fe97dbbc3d261b67665992fd21 (135 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R12 唯一 blocking 處置後基線 bump（單次 amend）。裁決：issuecomment-5473680383。
- 2026-08-31T13:26:46+08:00 amend by wf-cli（op 92b1f905）→ spec 基線：原值指紋 sha256:92ea3a114a2a8e892712d3661ec838a9f5d669fe97dbbc3d261b67665992fd21 (135 bytes) → 新值指紋 sha256:2cf6f104e84602ad3fe7c6b7fa05753ad8e21461c3d68793a4a9b9a0cc6aa033 (135 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 自審兩筆修正後基線 bump；R13 派審撤回換版。。
- 2026-08-31T13:29:54+08:00 amend by wf-cli（op c45023b6）→ spec 基線：原值指紋 sha256:2cf6f104e84602ad3fe7c6b7fa05753ad8e21461c3d68793a4a9b9a0cc6aa033 (135 bytes) → 新值指紋 sha256:451e67fcc35775528b3b124b01a37a563e04902a2ea960c765e204d366fa8b86 (135 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 自審第二批（AC 排序）後基線 bump。。
- 2026-08-31T13:38:58+08:00 amend by wf-cli（op d6938499）→ spec 基線：原值指紋 sha256:451e67fcc35775528b3b124b01a37a563e04902a2ea960c765e204d366fa8b86 (135 bytes) → 新值指紋 sha256:7c7688bd7d85a4cfccc8c3090153b2b5b375e422b70f5c38833c5c70349dd2d6 (135 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 自審第三批（SA12 標記移除寫入權）後基線 bump。。
- 2026-08-31T13:43:15+08:00 amend by wf-cli（op f4eb8783）→ spec 基線：原值指紋 sha256:7c7688bd7d85a4cfccc8c3090153b2b5b375e422b70f5c38833c5c70349dd2d6 (135 bytes) → 新值指紋 sha256:926e39fb9dbbb6244b541c1bc8d3b6760ec6f8f931ff1fb72e363e361fc314ea (135 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 自審第四批（痛點日期戳＋W3′ 簡稱宣告）後基線 bump。。
- 2026-08-31T13:49:28+08:00 amend by wf-cli（op 0b3b5799）→ spec 基線：原值指紋 sha256:926e39fb9dbbb6244b541c1bc8d3b6760ec6f8f931ff1fb72e363e361fc314ea (135 bytes) → 新值指紋 sha256:88e043c5b264e6893b98e8ac5e99bdaa6efaeb12b3b08c180db8c315655803ed (135 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 自審批五（§八總數去數字化／brief 補三未驗項／w2b 資源修剪）後基線 bump；批六零筆依停止規則收束。。
- 2026-08-31T13:55:53+08:00 amend by wf-cli（op 5b5b4170）→ spec 基線：原值指紋 sha256:88e043c5b264e6893b98e8ac5e99bdaa6efaeb12b3b08c180db8c315655803ed (135 bytes) → 新值指紋 sha256:b10f1ab83425f58ae07731455592bf00aed3a9042253aacff32d6a22695dd9c0 (135 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 批七（敘述不承載現況數：下界誠實化／88.6% 除汙／回顧指標 regime-neutral）後基線 bump。。
- 2026-08-31T14:01:00+08:00 amend by wf-cli（op e8575b4f）→ spec 基線：原值指紋 sha256:b10f1ab83425f58ae07731455592bf00aed3a9042253aacff32d6a22695dd9c0 (135 bytes) → 新值指紋 sha256:a690e2008618bddf10ebe4937c7ce782b5c4820e762ab9f4de8341261096c403 (135 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 批八（§七日期戳＋N=30 依據重述）與批九（list-items 裸數收束）後基線 bump（單次 amend 涵蓋兩批）。。
- 2026-08-31T14:07:27+08:00 amend by wf-cli（op dd9a042e）→ spec 基線：原值指紋 sha256:a690e2008618bddf10ebe4937c7ce782b5c4820e762ab9f4de8341261096c403 (135 bytes) → 新值指紋 sha256:e9ae1cf47688a4636f017d131832065595669d956253263027d5817aeaab272c (142 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 meta 輪（指標② 基線預登）後基線 bump。。
- 2026-08-31T14:27:05+08:00 amend by wf-cli（op b0b75a07）→ spec 基線：原值指紋 sha256:e9ae1cf47688a4636f017d131832065595669d956253263027d5817aeaab272c (142 bytes) → 新值指紋 sha256:6640ae4c08286f957eed853c54d91adf7cb11166e8064a3b5723fb263d657bd8 (140 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R13 裁決（comment 5473769284，REQUEST_CHANGES）唯一 blocking P1-33 journal 邊界已依處置修入 w3.md（PR #201）後基線 bump。
- 2026-08-31T14:37:32+08:00 amend by wf-cli（op e434d28b）→ spec 基線：原值指紋 sha256:6640ae4c08286f957eed853c54d91adf7cb11166e8064a3b5723fb263d657bd8 (140 bytes) → 新值指紋 sha256:04dac1f93b5c8047f6cbd4efaf3cd4a0f16987677c0fedee11815f45589696ba (175 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 停止自審判準由對話落 repo（PR #202）後基線 bump；R14 派審詞同步至此 SHA。
- 2026-08-31T16:31:10+08:00 amend by wf-cli（op b17f325c）→ spec 基線：原值指紋 sha256:04dac1f93b5c8047f6cbd4efaf3cd4a0f16987677c0fedee11815f45589696ba (175 bytes) → 新值指紋 sha256:068564474d50de155aee934635d8d3c0621c6cb6698f8cf53e7efb3f6a1d8311 (157 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R14 P1-38 依處置修入（PR #203：15 處補日期、148 行 hash 釘住分類、掃描器+負控測試）後基線 bump；基線敘述同步移除會漂的輪次計數（P1-38 同族）。
- 2026-08-31T17:09:20+08:00 amend by wf-cli（op edb4ffee）→ spec 基線：原值指紋 sha256:068564474d50de155aee934635d8d3c0621c6cb6698f8cf53e7efb3f6a1d8311 (157 bytes) → 新值指紋 sha256:8ae9fd966a4a68ae53a0694d10af0ecb7ef4f056db42dfab1a92946d00515f7e (157 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R15 P1-38 延續依處置修入（PR #204：detector-escape 六反例釘死、(c) 收緊、白名單回歸兩類＋128 條逐筆 rationale、ID_PATS 45 條成對測試）後基線 bump。
- 2026-08-31T21:18:07+08:00 amend by wf-cli（op 2fa4889c）→ spec 基線：原值指紋 sha256:8ae9fd966a4a68ae53a0694d10af0ecb7ef4f056db42dfab1a92946d00515f7e (157 bytes) → 新值指紋 sha256:41cb9af5f30defb5286a6c002be9f91aa19d092268596133c34934857d40a2d7 (157 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 P1-38 同根因第三輪升級，需求方裁定乙（fence 狀態機＋逐 token claims）；PR #205 落地後基線 bump（裁定轉錄見卡留言）。
- 2026-08-31T22:09:41+08:00 amend by wf-cli（op 393a066e）→ spec 基線：原值指紋 sha256:41cb9af5f30defb5286a6c002be9f91aa19d092268596133c34934857d40a2d7 (157 bytes) → 新值指紋 sha256:8187e6361223f54e160bf4cf07c5d669f73bd674bfb9915dc5bc142466c05bb9 (157 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R17 四缺口依處置修入（PR #206：occurrence 綁定＋scanner 內 schema 驗證＋dead/JSON 失敗輸出＋四列錯例）後基線 bump。
- 2026-08-31T22:29:00+08:00 amend by wf-cli（op 6fa90a67）→ spec 基線：原值指紋 sha256:8187e6361223f54e160bf4cf07c5d669f73bd674bfb9915dc5bc142466c05bb9 (157 bytes) → 新值指紋 sha256:c10519c242c6a44e6eec2cac1eb9805360667c8ae3ebc179e1d64920b24cc2d6 (157 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R18 兩缺口依處置修入（PR #207：load 期 identity 驗證＋重複鍵 fail-closed＋三層評估分義）後基線 bump。
- 2026-08-31T22:55:40+08:00 amend by wf-cli（op 13388a73）→ spec 基線：原值指紋 sha256:c10519c242c6a44e6eec2cac1eb9805360667c8ae3ebc179e1d64920b24cc2d6 (157 bytes) → 新值指紋 sha256:4a2861bbf8df5ed3e709b620fa8ccf0528f72f54208b0a1d389ac109f560f4d1 (157 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R19 判準二義依處置修入（PR #208：單一 red predicate＋三處同步＋自審四批修 5 筆錯誤路徑）後基線 bump。
- 2026-08-31T23:04:12+08:00 amend by wf-cli（op fe64b48a）→ spec 基線：原值指紋 sha256:4a2861bbf8df5ed3e709b620fa8ccf0528f72f54208b0a1d389ac109f560f4d1 (157 bytes) → 新值指紋 sha256:583c5219e2385b66020cccaec423001c03c7f1282de0d825852a4a909409e7e7 (157 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 派審前研究批（PR #209：rationale 引句錨定測試＋6 筆修正＋UnicodeDecodeError 路徑）後基線 bump；R20 派審詞同步。
- 2026-08-31T23:26:43+08:00 amend by wf-cli（op 7d842b2b）→ spec 基線：原值指紋 sha256:583c5219e2385b66020cccaec423001c03c7f1282de0d825852a4a909409e7e7 (157 bytes) → 新值指紋 sha256:b427c8a511911d7d56b591b6c32f681416ead40aa95e8c06d1d5296e337142f6 (157 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R20 唯一 blocking（非六檔否定式 claim）依處置修入（PR #210）後基線 bump。
- 2026-08-31T23:41:06+08:00 amend by wf-cli（op 0540892c）→ spec 基線：原值指紋 sha256:b427c8a511911d7d56b591b6c32f681416ead40aa95e8c06d1d5296e337142f6 (157 bytes) → 新值指紋 sha256:6e2c2a5680a52eddeb61c3c3797c18562254b8c19fe4c0d19de9bebe9b56bae8 (157 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 R21 唯一 blocking（黃金值回歸測試）依處置修入（PR #211，變異自證）後基線 bump。
- 2026-08-31T23:52:16+08:00 amend by wf-cli（op b92ccea6）→ spec 基線：原值指紋 sha256:6e2c2a5680a52eddeb61c3c3797c18562254b8c19fe4c0d19de9bebe9b56bae8 (157 bytes) → 新值指紋 sha256:36e5f195bced3bac106681b98143a4ff3b3ac29127dfe7eb55ae3f62eac6ae76 (157 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 規劃審 R22 APPROVE（P1-38 關閉）於 b5dd912；其後落需求方核定之 A＋B 預防條文（PR #212，pm/executor-conduct 各一行，Codex 審後追加、需求方直裁內容）——規劃 Gate 請對本 SHA 裁定。
- 2026-09-01T02:49:41+08:00 amend by wf-cli（op 1eb573ce）→ routing 行：原值指紋 sha256:f3f749fa9d12df00f9034a6296bac40f7789b99e5286eea4c3ba5763f0acc0c6 (404 bytes) → 新值指紋 sha256:e651f5f7b54cdac5ba12c20465cc240817c5105fc9d05d25db1c51d0316eaebb (116 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-REDESIGN-W1 驗收 5b：以 amend 的 feature／routing 通道同步父卡三欄——功能欄殘留「五波施工」（Initiative 已於 P1 收斂為四波五卡），routing 的執行側理由引用「不可逆狀態遷移（波 3）」而該不可逆段已歸切換 Initiative、⛔ 不在本 Initiative 射程。
- 2026-09-01T02:49:41+08:00 amend by wf-cli（op 1eb573ce）→ 功能：原值「工作流框架重整：8 階段 × 10 狀態、清單制、五波施工（Initiative 父卡）」→ 新值「工作流框架重整：8 階段 × 10 狀態、清單制、四波五卡施工（Initiative 父卡）」（⚠️ 全文：舊值來源非 body，平台版本救不回）；理由 WF-REDESIGN-W1 驗收 5b：以 amend 的 feature／routing 通道同步父卡三欄——功能欄殘留「五波施工」（Initiative 已於 P1 收斂為四波五卡），routing 的執行側理由引用「不可逆狀態遷移（波 3）」而該不可逆段已歸切換 Initiative、⛔ 不在本 Initiative 射程。
- 2026-09-02T18:28:17+08:00 amend by wf-cli（op 70dcc44a）→ spec 基線：原值指紋 sha256:36e5f195bced3bac106681b98143a4ff3b3ac29127dfe7eb55ae3f62eac6ae76 (157 bytes) → 新值指紋 sha256:e2571d04f0012e86b9972ca1cd591bd6ab8d8045ea4c63a436d61f434f95e531 (52 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 2026-09-02 基線變更（scope 級 cascade，templates/baseline-cascade.md §2-3）：觸發卡 WF-REDESIGN-W3（#221）。變更摘要＝discovery brief 拆卡定稿表的 W3′ 第一項「Log→留言（7 persistent sinks＝open 1＋append 6）」移出 W3′ 射程、延後至清單項 #238；連帶 brief 三條待驗證假設（epoch＋dual reader 部署可行性／journal 多 session 同時 retry 同 op／reader 按 op id 去重＋corruption gate）之處置由「W3′ 執行期」改為「延後至 #238」。受影響卡與級別：#221 scope（驗收 7→8 條，另納入需求方 2026-09-01 三則射程追加）；#214／#217／#219／#220 none（皆終態，依 baseline-cascade「已合併卡不回改」）。核可者＝需求方 ruan6047（2026-09-02，裁定留痕 issuecomment-5508136680）。基線 93bb8c08→7d798062（含 W2A／W2B 全部已合併內容）。⚠️ 卡面無「基線變更紀錄」章節、amend 亦無新增章節旗標 ⇒ 本紀錄落 Log 與該留言。。
- 2026-09-02T18:28:56+08:00 amend by wf-cli（op 6b5ae6e3）→ spec 基線：原值指紋 sha256:e2571d04f0012e86b9972ca1cd591bd6ab8d8045ea4c63a436d61f434f95e531 (52 bytes) → 新值指紋 sha256:e517add516dacfa5e31adc4e54047cdb8af40c4c188aec90f7379172b3b4d10d (157 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 更正前一次 amend（op 70dcc44a）的疏失：該次 bump 只寫 SHA，遺失了原值尾隨的括號附註「（決議＋brief＋wave-specs＋baseline-universe＋prose-number-inventory；審核輪次見卡留言）」——那段標示基線涵蓋哪些 artifact，⛔ 非可省略的裝飾。本次補回，SHA 維持 7d798062。⚠️ 基線變更的實質內容（scope 級 cascade、觸發卡、受影響卡與級別、核可者）見前一次 amend 的 Log 行與 issuecomment-5508136680，本次⛔ 不重複。。
- 2026-09-03T20:14:31+08:00 handoff by wf-cli → owner claude-fable-5@Claude Code (PM)；iteration 0；SHA aab7bf0918708f8280f8cd7472d070a8e5116628；階段 需求；踩坑回應 8 族（已檢查 2／不適用 0／發現 6）；注意事項回應 15 條（已遵循 8／不適用 2／發現 5）；證據 四波五卡全數結案（W0/W1/W2A/W2B/W3 皆 🏁完成；W3 最終 R7 APPROVE／findings 0）。AC2 的 ruan6047/ai-workflow#222 已建立。⭐ T4 停下條件 4 成立，需求方已作出明確人工 sign-off（原話「T4 結案 sign-off，照做」），⛔ 非 PM 直行。⚠️ 八條 brief 假設無一為已驗證：延後 5、降級 2（#2 LOC 方向與估計相反、#3 PM 對照觀察資料負面）、對沖已落地但原假設未驗 1。⚠️ AC3 逐字要求父卡停執行／進行中追蹤，而 43 條 Log 全為 amend 42＋open、handoff 命中 0、全程停在 💡需求 ⇒ AC3 未被遵守，PM ⛔ 不回填。⚠️ F-需求 15 條中 5 條為「發現」：01/02（⛔ 無法確認由清單項升級、無原文可比對）、04（⛔ 無查重留痕）、12（⛔ 無第二 PM 的 ④ 留痕）、15（⛔ 未逐字核對節名）——皆如實登記、⛔ 不補寫。⚠️ branch/worktree 皆 None ⇒ ⛔ 不帶 --repo-path 與 --cleanup。⚠️ 封存同 #221：wfcli ⛔ 無封存動詞 ⇒ ⛔ 不封存。；⚠️ 未帶 --cleanup 且未帶 --repo-path，收尾清理未執行（worktree、本地分支、遠端分支皆未處理），狀態面已寫終態。


## Comment 5469108595 · 2026-08-30T13:57:11Z

# WF-REDESIGN1 規劃階段跨家族查核裁決

- 被審 SHA：`8291d02a9dbdc5e89d531e2267cff2b70d87e8d6`
- 裁決：**REQUEST_CHANGES；R1 不過，依有序閘門停止，不進 R2–R4**
- 查核者身分自述：Codex（OpenAI），session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-30T21:57:11+08:00`

## R1 前提：不過

1. **W0：過。** `conduct×3＋intake`、T1、PM 可兼，與決議 §十一致。
2. **W1：內容前提過。** 清單、`open --from-issue`、封直接建 issue／DraftIssue、表單與 `--needs-deploy` 移除，均可回到決議 §一、§四、§十。
3. **W2A：核心前提過。** canonical §0／§1 改寫、§1／§2 前移、尚未 cutover 標記與 T4 跨家族查核，均與決議一致。
4. **W2B：不過。** 決議把整個波 2（canonical＋stage-rules＋範本）定為 T4；spec 卻在未附需求方降級裁定下改成 T2／主力型查核，違反決議 §四的「降須需求方裁定留痕」，也未依 canonical §0 前言取風險、影響範圍與可逆性最高者。
5. **W3：不過。** spec 有 snapshot 與拋棄式 project 兩項本地前置，但沒有把 `W2B 完成` 寫成 cutover 的硬前置；因此文件化依賴只到 `W1 → W2A → W2B`，沒有封住 `W2B → W3`。
6. **W4：不過。** 決議取代清單把兩 repo 的 `TASKS.md` 入口改查詢指令排在波 2，W4 驗收卻把 cpbl `docs/TASKS.md` 墓碑與路由修正排到波 4；同一取代項有相衝的生效波。
7. **五波配置／六卡：不過。** 六份 spec 明確定義 `W0/W1/W2A/W2B/W3/W4` 六張卡；#177 驗收仍寫「五張波卡（波 0–4）全部誕生並各自結案」。它允許漏掉 2A 或 2B 仍字面達標，父卡驗收無法封閉涵蓋六份規劃產出物。
8. **取代清單封閉性：不過。** 若逐列要求可追溯到具名驗收，至少以下項目沒有單一、明文 owner：`MODEL_ROUTING.md ×2` 的 claim 字樣只出現在 W2B 資源、未進驗收；`部署狀態`／`DEPLOYMENT_TRANSITIONS`、內建 `Status`／`deploy_state`、Backlog 映射與 `open --spec-dir` 移除只被 W3 的「160 處遷移」概括，沒有逐項驗收；兩 repo `TASKS.md` 又有前述波次衝突。這不符合決議 §一「封閉列舉」的施工可追溯性。

### R1 可重現證據

- 決議取代清單與波次：[`WORKFLOW-REDESIGN-2026-08-30.md` §一](https://github.com/ruan6047/ai-workflow/blob/8291d02a9dbdc5e89d531e2267cff2b70d87e8d6/docs/research/WORKFLOW-REDESIGN-2026-08-30.md#L7-L20)
- 單向級別門與最高風險原則：[`WORKFLOW-REDESIGN-2026-08-30.md` §四](https://github.com/ruan6047/ai-workflow/blob/8291d02a9dbdc5e89d531e2267cff2b70d87e8d6/docs/research/WORKFLOW-REDESIGN-2026-08-30.md#L35-L40)；[`AI_WORKFLOW.md` §0 前言](https://github.com/ruan6047/ai-workflow/blob/8291d02a9dbdc5e89d531e2267cff2b70d87e8d6/AI_WORKFLOW.md#L13-L30)
- 五波配置與停機前置：[`WORKFLOW-REDESIGN-2026-08-30.md` §十](https://github.com/ruan6047/ai-workflow/blob/8291d02a9dbdc5e89d531e2267cff2b70d87e8d6/docs/research/WORKFLOW-REDESIGN-2026-08-30.md#L75-L78)
- W2B 的 T2／能力宣告：[`w2b.md`](https://github.com/ruan6047/ai-workflow/blob/8291d02a9dbdc5e89d531e2267cff2b70d87e8d6/docs/research/drafts/wave-specs/w2b.md#L7-L18)
- W3 前置與停機序：[`w3.md`](https://github.com/ruan6047/ai-workflow/blob/8291d02a9dbdc5e89d531e2267cff2b70d87e8d6/docs/research/drafts/wave-specs/w3.md#L12-L21)
- W4 的 cpbl `TASKS.md` 處置：[`w4.md`](https://github.com/ruan6047/ai-workflow/blob/8291d02a9dbdc5e89d531e2267cff2b70d87e8d6/docs/research/drafts/wave-specs/w4.md#L14-L18)
- 父卡字面驗收：#177 現行卡面「五張波卡（波 0–4）全部誕生於本卡規劃階段並各自結案」。

## R2 射程：不過（未審）

R1 未過，依指定順序閘門未進入 R2；沒有對六份非射程、資源宣告交集或 W0／W2B 的刻意 `file:stage-rules/` 重疊作裁定。

## R3 內容：不過（未審）

R1 未過，未逐條裁定驗收條件的痛點追溯、非零資訊與基線 SHA。此處不得解讀為已證實 R3 缺陷。

## R4 影響面：不過（未審）

R1 未過，未進入 DraftIssue 既有流程、`CONTRACT_TOOL_RECONCILE` 守衛或波 3 回滾路徑的實作影響查核。此處不得解讀為已證實 R4 缺陷。

## Findings

### WF-REDESIGN1-P1-01

- severity: major
- blocking: true
- evidence: `w0.md`、`w1.md`、`w2a.md`、`w2b.md`、`w3.md`、`w4.md` 共六個 card；#177 驗收只要求五張波卡。
- disposition: 把父卡驗收改成「五波、六張子卡（W0/W1/W2A/W2B/W3/W4）全數誕生並結案」，並明列六個 ID；不得用「波 0–4」代替卡數。

### WF-REDESIGN1-P1-02

- severity: major
- blocking: true
- evidence: 決議 §十將波 2 全體定為 T4；W2B 第 7、12 行宣告 T2、執行／查核皆主力型，未附降級裁定。
- disposition: W2B 依既有決議恢復 T4 與相應跨家族／人工 sign-off；若要拆分後降級，先取得需求方對 W2B 的具名降級裁定，逐答風險、影響範圍、可逆性三子問，再重推能力層級。

### WF-REDESIGN1-P1-03

- severity: major
- blocking: true
- evidence: W2B 標題只宣告依賴 2A；W3 第 14 行前置只含 snapshot 與拋棄式 project 測試，未要求 W2B 已完成；list-items 只保證波 1 上線後建項，不保證 W2B 終態後才可執行 W3。
- disposition: 在卡面與 spec 明列硬依賴 `W1 完成 → W2A 完成 → W2B 完成 → W3 可開始`；W3 的不可逆前置另保留 snapshot 補欄、當場產物驗證與拋棄式 project 實測。

### WF-REDESIGN1-P1-04

- severity: major
- blocking: true
- evidence: 決議 §一是封閉取代清單，但六份 spec 無逐列 owner；其中兩 repo `TASKS.md` 的生效波在決議（波 2）與 W4（波 4）直接相衝，其餘數項只有資源名或「160 處」集合描述，沒有具名驗收。
- disposition: 在六份 spec 上方或父卡新增「取代清單 10 列 → 唯一 wave/card → 驗收編號 → 生效時點」矩陣；每列只准一個 owner。先裁定 cpbl `TASKS.md` 是波 2 還是波 4，再同步決議、父卡與 spec。

## 級別與能力層級推導

- 已能裁定：W2B 的 T2／主力型推導不成立，原因見 P1-02。
- 未予完整裁定：W0、W1、W2A、W3、W4 的逐卡最高者推導因 R1 gate 停止；不得把未列 finding 解讀為通過。

## PM 已知未驗項（逐字保留；本輪仍未驗）

- 波 3 的「160 處」「157 張」是 2026-08-29/30 的量測，執行時須重量
- 波 4 的 cpbl CLAUDE.md 錨點字串已知會漂（cpbl#176 撤回案：錨點沒中）
- w2b 資源宣告與 w0 都含 file:stage-rules/——**刻意**：依賴序保證不同時在飛，但 assign 交集檢查會擋，屆時 w0 應已終態
- 六份 spec 皆未經任何人試讀執行——你是第一個讀者

## 重審入口

修正 P1-01～P1-04 後，從 R1 全表重跑；R1 過才進 R2，後續不得沿用本輪「未審」為任何通過證據。


## Comment 5469298925 · 2026-08-30T14:35:07Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（第二輪）

- 被審 SHA：`9d85928b9ee628decd3aa560f5d28251902d3ccf`
- 前輪：issuecomment-5469108595
- 裁決：**REQUEST_CHANGES；R1 全表仍不過，依有序閘門停止，不進 R2–R4**
- 查核者身分自述：Codex（OpenAI），session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-30T22:35:07+08:00`

## 前輪 findings 重驗

1. **WF-REDESIGN1-P1-01：已解。** #177 已逐字列出五波六卡的六個 ID；決議 §十亦改成「五波六卡」。
2. **WF-REDESIGN1-P1-02：已解。** 需求方丙案已把規則制定完整移入 W2A；W2A 為 T4／跨家族，W2B 僅留機械配套並重新給出 T2 依據。此輪接受該切分，不視為降級。
3. **WF-REDESIGN1-P1-03：已解。** 決議 §十、#177 與 W3 前置均已明列 `W1 → W2A → W2B → W3`，且 W3 指明 W2B 終態是不可逆動作前置。
4. **WF-REDESIGN1-P1-04：未全解。** 14 列矩陣本身已做到每列單一 owner／已完成，但 wave spec 對矩陣的承接仍不封閉，詳見 finding。

## R1 前提：不過

### 上游基線

- **不過。** 被審物與本輪修正位於 `9d85928`，但 #177 的 `spec 基線` 仍是 `cd053af`；`list-items.md` 的四項共同出處也仍釘 `cd053af`。該 SHA 不含五波六卡、14 列矩陣、W2A/W2B 重切與完整硬依賴鏈，故依卡面開子卡會合法地引用修正前前提。
- **不過。** brief 明載「spec 基線＝合入本檔的 main commit SHA」，但父卡未 bump；這不是歷史註記，因父卡簡介又要求所有波卡以本卡為錨。

### 六份 spec 與決議逐份對照

1. **W0：過。** 四份 conduct/intake 的 move、T1、PM 可兼均與決議一致；規則類紅線另以需求方本 session sign-off 滿足，已明文。
2. **W1：不過。** 驗收 5 要在 W1 把撤銷程序寫進 `stage-rules/requirement`「生效版」，但該檔目前仍在 drafts，且 W2A 驗收 6 才負責把其所屬八份 stage-rules move 成生效版。硬依賴又要求 W1 終態後才能開 W2A，故現序列下 W1 的該項沒有可寫的生效目的地。
3. **W2A：不過。** 驗收 3 仍寫「取代清單所列舊文刪除」，字面涵蓋 14 列；但矩陣只把第 1、3 列交給 W2A，其他列屬 W1/W3/W4 或已完成。這重新造成 W2A 與其他 owner 搶同一取代項；若原意僅限 canonical 舊文，驗收必須列出矩陣 row ID，不能靠推測限縮。
4. **W2B：過。** 痛點、非射程、資源與三條驗收均已排除 stage-rules/tier-rules 規則制定；T2／主力型與目前機械配套射程一致。
5. **W3：不過。** 完整硬依賴已補；但父卡與 brief 仍稱「六步停機」，W3 驗收明稱七步，而 brief／決議的箭頭串實際列出 snapshot 前置再加七個停機動作。驗收母體數量沒有單一答案。
6. **W4：不過。** 14 列矩陣的 cpbl owner 已對齊；但「36 張逐卡狀態操作＋57 份 spec 封存＋28 筆資源宣告處置＋刪有值 Project 欄位」是跨 repo／跨系統的大範圍遷移，且欄位刪除只能靠 snapshot 重建，不能由 `git revert` 回復。依 canonical §0「取風險、影響範圍與可逆性最高者」，T2 局部修正不成立，至少 T3；能力層級須隨 tier 重推。

### brief 與父卡

- **不過。** 父卡驗收已把回顧改成 cutover 後第 30 張常態卡結案、附 2026-10-31 fail-safe；父卡驗證仍寫「60 天回顧報告」，brief 的存活反駁也仍寫「60 天回顧驗」。同一驗證時點有兩套前提。
- **不過。** brief 拆卡仍只寫「波 1 完成後才開波 2」，且把 L0／五份範本與 canonical 合在一張 T4 波 2；這不是現行 W2A(T4)／W2B(T2) 與完整硬依賴鏈的描述。brief 是本題明列的上游依據，不能以決議已更新代替同步。

### 取代清單 14 列

- **矩陣本身：過。** 14 列皆只有一個 active owner，已完成列明示 SHA，cpbl `TASKS.md` 已唯一歸 W4。
- **spec 承接：不過。** W2A 驗收 3 有前述越界；W3 仍以「160 處遷移」概括矩陣第 7、10、13、14 列，驗收未逐列指名。矩陣有 owner 不等於 owner 的卡有可驗收交付。

### 級別與能力層級

- W0：過（T1；使用者 sign-off 補足規則類紅線）。
- W1：過（T3／主力型），但 W1 驗收 5 的時序另不過。
- W2A：過（T4／高階型／跨家族）。
- W2B：過（T2／主力型），接受丙案切分。
- W3：過（T3+／高階型／跨家族建議）；其不可逆與唯一 writer 影響已反映加嚴。
- W4：不過；大範圍且不能以 Git 單獨回滾，T2／標準查核低估影響範圍與可逆性。

## R2 射程：不過（未審）

R1 未過，依指定順序閘門未進入 R2；前輪「未審」沒有沿用，也沒有對非射程縫隙、重疊或資源交集作裁定。

## R3 內容：不過（未審）

R1 未過，未執行各 spec 驗收條件的痛點追溯、非零資訊與固定基線查核；PM 揭露的 R3 未驗項仍保持未驗。

## R4 影響面：不過（未審）

R1 未過，未讀取 DraftIssue 既有流程、`CONTRACT_TOOL_RECONCILE` 守衛或 W3 snapshot／回滾實作；不得把本輪未列 finding 解讀為 R4 通過。

## Findings

### WF-REDESIGN1-P1-04（前輪 finding 延續）

- severity: major
- blocking: true
- evidence: 決議矩陣第 11–24 行只把 rows 1/3 交 W2A；`w2a.md:17` 卻要求刪除「取代清單所列舊文」而未限 row，W3 的 rows 7/10/13/14 也未進具名驗收。
- disposition: 每張 spec 增加 `replacement_rows` 並讓驗收逐 row 對應；W2A 驗收 3 限為 rows 1/3。W3 對 rows 7/10/13/14 各有至少一條能判 pass/fail 的驗收，不得只寫「160 處」。

### WF-REDESIGN1-P1-05

- severity: major
- blocking: true
- evidence: #177 現行 `spec 基線` 與 `list-items.md:6` 均為 `cd053af`；`git show cd053af:docs/research/WORKFLOW-REDESIGN-2026-08-30.md` 對「五波六卡／W2A／W2B／14 列／硬依賴鏈」皆零命中，而本輪被審 SHA 是 `9d85928`。
- disposition: 以允許的 amend 通道把父卡 spec 基線 bump 到包含本輪所有修正的 main SHA，並同步 list-items 出處；在新 SHA 上重跑六卡、依賴與矩陣檢查。

### WF-REDESIGN1-P1-06

- severity: major
- blocking: true
- evidence: #177 驗收採「第 30 張常態卡＋2026-10-31 fail-safe」，但其驗證仍寫「60 天回顧」；brief 第 31 行亦為 60 天，第 41–49 行仍是修正前的波 2 合併表與短依賴。
- disposition: 先裁定唯一回顧觸發，再同步父卡驗收／驗證、brief 與決議；brief 拆卡改為五波六卡並逐字列完整硬依賴與 W2A/W2B 級別。

### WF-REDESIGN1-P1-07

- severity: major
- blocking: true
- evidence: `w1.md:19` 要寫 `stage-rules/requirement` 生效版；該檔現位於 `docs/research/drafts/stage-rules/requirement.md`，而 `w2a.md:20` 才負責將八份 stage-rules move 生效；硬依賴禁止 W2A 先於 W1。
- disposition: 將撤銷程序的規則制定移入 W2A，或明確把 `requirement.md` 納入 W0 的先行生效集合並同步資源與驗收；不能保留目前不可能滿足的順序。

### WF-REDESIGN1-P1-08

- severity: major
- blocking: true
- evidence: #177 與 brief 稱「六步」；`w3.md:18` 稱七步；`w3.md:14-15` 的形狀是三項前置後，再執行 freeze／rename／migration／options／archive／reconcile／unfreeze 七步。
- disposition: 將 snapshot 等前置與停機步驟分開編號，於決議、brief、父卡、W3 使用同一個步驟數與逐項名稱；父卡驗收以名稱而非未定義的「六步」驗。

### WF-REDESIGN1-P1-09

- severity: major
- blocking: true
- evidence: `w4.md:12` 只以「可逆」推 T2；同檔第 15–18 行實際涵蓋 36 卡、57 spec、28 筆資源宣告與有值 Project 欄位刪除，跨 repo 且欄位刪除不能由 git revert 回復。
- disposition: 依 canonical §0 最高者原則升至至少 T3，重推執行／查核能力；若仍主張 T2，須逐答風險、影響範圍、可逆性，並證明 Project 狀態可由既定機制完整重建，而非只宣稱有 snapshot。

### WF-REDESIGN1-P1-10

- severity: minor
- blocking: false
- evidence: `3a90e3b` 與 `9d85928` 的 commit time 均為 2026-08-30 +08:00；決議第 7、81 行與 `pm-conduct.md:25` 卻把本輪修訂／失誤登記標成 2026-08-31。
- disposition: 改成實際 2026-08-30，或若日期採另一時區，明列時區與可重現來源。

## PM 自審未驗項（逐字保留）

⛔ 自審沒跑的：各 spec 驗收條件的零資訊檢驗（R3 層次）、W2A 千行級審查面的內部一致性——留給你。

本輪因 R1 gate 停止，上述兩項仍未驗；不得以本留言替代其後 R3／W2A 實作審查。

## 重審入口

修正仍開啟的 P1-04 與 P1-05～P1-09（P1-10 可同批修）後，更新父卡 spec 基線，再從 R1 全表重跑；R1 過才進 R2。


## Comment 5469364619 · 2026-08-30T14:46:53Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（第三輪）

- 被審 SHA：`1ccd8f48d1baa2090249315eb14316f9e1b32afc`
- 前兩輪：issuecomment-5469108595、issuecomment-5469298925
- 裁決：**REQUEST_CHANGES；R1 全表仍不過，依有序閘門停止，不進 R2–R4**
- 查核者身分自述：Codex（OpenAI），session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-30T22:46:53+08:00`

## 前輪 findings 重驗

1. **P1-04：未全解，仍 blocking。** 六檔都有 `replacement_rows` 字面，owner 集合與逐 row 驗收亦已補；但 W0／W2B 的 frontmatter 不是合法 YAML，故這兩份 spec 的 `replacement_rows`、`card`、`status` 整段皆不可解析。
2. **P1-05：已解。** #177 spec 基線已與被審 SHA 完全一致；list-items 不再另釘 SHA。
3. **P1-06：已解。** brief、父卡驗收與驗證均採第 30 張常態卡／2026-10-31 fail-safe；拆卡表已為五波六卡與完整依賴鏈。
4. **P1-07：已解。** W1 只寫收件模板操作註記；撤銷規則條文化明確歸 W2A，沒有先行生效 stage-rule。
5. **P1-08：已解。** 決議 §十是前置三項＋停機七步的唯一定義；brief、W3、父卡皆改引用。
6. **P1-09：已解。** W4 已升 T3，風險／影響範圍／可逆性與能力層級均重推。
7. **P1-10：已解。** 指定範圍內 `2026-08-31` 殘留為 0。

## R1 前提：不過

### 六份 spec 全表

1. **W0：不過。** 內容前提、T1 與使用者 sign-off 均對齊；但第 4 行的 `replacement_rows: []（生效之 conduct 不在取代清單）` 使 YAML frontmatter 解析失敗。
2. **W1：過。** `replacement_rows` 為 `[12]` 且是陣列；內容與依賴修正一致。
3. **W2A：過。** `replacement_rows` 為 `[1, 3]`；驗收只處理 rows 1/3，撤銷規則與 T4 射程一致。
4. **W2B：不過。** 內容前提與 T2 切分已對齊；但第 4 行的 `replacement_rows: []（機械配套，無取代列）` 同樣使整段 frontmatter 解析失敗。
5. **W3：過。** `replacement_rows` 為 `[2, 4, 7, 10, 13, 14]`；逐 row 判準、硬依賴與停機序引用均對齊決議。
6. **W4：過。** `replacement_rows` 為 `[6, 9, 11]`；T3 與能力推導成立。

### 可重現機械證據

執行：

```bash
ruby -ryaml -e 'Dir["docs/research/drafts/wave-specs/w*.md"].sort.each { |f| y=File.read(f).split("---",3)[1]; begin; v=YAML.safe_load(y); puts "#{File.basename(f)} OK #{v["replacement_rows"].inspect} #{v["replacement_rows"].class}"; rescue => e; puts "#{File.basename(f)} FAIL #{e.class}: #{e.message.lines.first.strip}"; end }'
```

被審 SHA 實得：W0／W2B 為 `Psych::SyntaxError`；其餘四檔皆為 `Array`。因此 PM 自審的「replacement_rows 6/6」只證明字面存在，沒有證明 frontmatter 可解析或欄位型別正確。

### 其他 R1 項

- 父卡基線、五波六卡、硬依賴、回顧觸發、停機序、14 列 owner 矩陣：過。
- 級別與能力：W0／W1／W2A／W2B／W3／W4 均過；W0／W2B 的內容裁定不因 frontmatter finding 改變。
- replacement row 集合：四份可解析 spec 與兩個「意圖為空」的 spec 在文字上無重疊並涵蓋 active rows；但在兩份 YAML 修正前，不能宣稱六份 metadata 全過。

## R2 射程：不過（未審）

R1 未過，依指定順序閘門未進入 R2；未對非射程縫隙、重疊或資源互斥作裁定。

## R3 內容：不過（未審）

R1 未過，未執行驗收條件的痛點追溯、零資訊與固定基線查核；PM 揭露的 R3 未驗項仍保持未驗。

## R4 影響面：不過（未審）

R1 未過，未讀取 DraftIssue、`CONTRACT_TOOL_RECONCILE` 或 snapshot／cutover 實作；前兩輪未審結果未沿用。

## Finding

### WF-REDESIGN1-P1-04（前輪 finding 延續）

- severity: major
- blocking: true
- evidence: `w0.md:4` 與 `w2b.md:4` 在 YAML 值後直接接全形括號說明；Ruby Psych `YAML.safe_load` 對兩檔均回 `Psych::SyntaxError`，其餘四檔可解析且 `replacement_rows` 型別為 Array。
- disposition: 改為合法 YAML，例如 `replacement_rows: [] # 說明`，或把說明移出 frontmatter。重跑 parser，驗收必須同時滿足：六檔 0 parse error、六個 `card`／`status` 可讀、六個 `replacement_rows` 皆為 Array、active rows 1–4／6–7／9–14 恰好各出現一次、completed rows 5/8 出現零次。

## PM 自審未驗項（逐字保留）

⛔ 自審仍沒跑的：R3 層次的零資訊檢驗、W2A 審查面內部一致性——續留給你。

本輪因 R1 gate 停止，上述兩項仍未驗；不得以本留言替代後續 R3／W2A 實作審查。

## 重審入口

只需修正 P1-04 的兩個 frontmatter 並更新父卡 spec 基線，即可再從 R1 全表重跑；R1 過後才進 R2–R4。


## Comment 5469449938 · 2026-08-30T15:03:53Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（第四輪）

- 被審 SHA：`688bf87141030af0428600e4ee522d244d86b078`
- 前三輪：issuecomment-5469108595、issuecomment-5469298925、issuecomment-5469364619
- 裁決：**REQUEST_CHANGES；R1 過，已續跑 R2–R4；R2、R3、R4 不過**
- 查核者身分自述：Codex（OpenAI），session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-30T23:03:53+08:00`

## 前輪 findings 重驗

- **P1-04：已解。** 六份 frontmatter 均可由 Ruby Psych `YAML.safe_load` 解析；`card`／`status` 可讀、`replacement_rows` 均為 Array。active rows 1–4／6–7／9–14 恰各一 owner；completed rows 5／8 為 0 owner。
- **P1-05～P1-10：維持已解。** 父卡 spec 基線已等於本輪 SHA；回顧觸發、五波六卡、硬依賴文字、撤銷歸屬、停機序唯一定義、W4 T3 文字與日期修正均仍一致。

## R1 前提：過

### 六份 spec 全表

1. **W0：過。** `replacement_rows=[]`；四份 conduct／intake 生效的內容與決議 §十相符。
2. **W1：過。** owner row 12；清單、`open --from-issue`、封直接 Issue／DraftIssue 與 fenced JSON 對齊決議 §四／§十。
3. **W2A：過。** owner rows 1／3；canonical、八份 stage-rules、tier-rules 與撤銷規則同輪 T4，符合 P1-02／P1-07。
4. **W2B：過。** `replacement_rows=[]`；只留機械配套，明列 W2A 終態前置，未夾帶規則制定。
5. **W3：過。** owner rows 2／4／7／10／13／14；W2B 終態、snapshot 與拋棄式 Project 為不可逆前置，停機序只引用決議 §十。
6. **W4：過。** owner rows 6／9／11；cpbl 移植內容與決議 owner 矩陣一致。

### 其餘 R1 項

- 五波六卡、14 列唯一 owner 矩陣、`W1→W2A→W2B→W3` 明文鏈、回顧樣本觸發與 fail-safe、停機序引用：均過。
- 本節只判「是否忠實承載上游決議」。級別是否符合 canonical 的最高者原則另於下方專項判定；因此 W0／W2B 雖與決議文字一致，仍可能在 canonical 查核失敗。

## R2 射程與資源：不過

1. **W0／W2A 有真實 write-set 重疊，卻沒有可執行的終態依賴。** 兩卡都宣告 `file:stage-rules/` 與 `file:docs/research/drafts/stage-rules/`；以現行 `find_conflicts` 實跑得到兩項衝突。決議的粗體硬依賴鏈從 W1 起，不含 W0；父卡又要求六卡都在規劃階段誕生，故只靠波次敘事不能保證 assign 時 W0 已終態。
2. **W4 缺 W3 終態前置。** W4 要把舊卡升到新語彙並刪 Project 欄位，語意上必須在 W3 cutover 後；但 spec、決議硬依賴鏈與父卡驗收都沒有 `W3→W4`。
3. **跨 repo／Project 寫入集沒有被有效宣告。** W3 驗證明列 cpbl `origin/main` 9 檔 PR，但資源只有 ai-workflow 的 `cli/src`、`cli/tests`、`scripts`。W4 的 `Project #4 欄位操作` 不符合現行資源 grammar；用 `ResourceDeclaration` 實跑即拒收。`file:docs/（cpbl）` 也未以工具能辨識的 repo 邊界表達。
4. **決議 §十二的 CLI 工作有事沒人做。** `find_conflicts` 的 DB alias 正規化與 `file:` 路徑前綴包含（含測試）未出現在任何卡的驗收。現行 `resources.py` 仍逐字寫「完全相同字串才算撞」，實作也是 set intersection；W3 雖廣抓 `cli/src/`，驗收沒有承接這兩項，不能由目錄資源反推出工作 owner。

## R3 內容：不過

逐條先以「哪個結果會推翻」判斷資訊量：

| spec | 驗收逐條結果 |
|---|---|
| W0 | **1 過**：缺任一具名檔、來源仍存在或仍有 draft 標記即推翻。**2 過**：除 frontmatter／警語外任一 byte 改變即推翻。 |
| W1 | **1 過**：五欄缺任一欄即推翻。**2 部分不過**：舊建立分支仍可呼叫即推翻，但既有 DraftIssue 如何處置／相容未定。**3 過**：三組任一不在 fenced JSON 即推翻。**4 過**：零 acceptance 可開卡或旗標仍在即推翻。**5 過**：W1 若讓 stage-rule 生效即推翻。 |
| W2A | **1–3 過**：角色數／順序、8×10、rows 1／3 都有封閉反例。**4 不過**：「新規則文脈」沒有機械邊界；同一污染字面可被任意判成舊文脈。**5 不過**：「移除或改可驗形式」沒有定義何謂可驗、也沒有失敗 oracle。**6 過**：八檔、move、引用與 tier-rules 都可計數／diff。 |
| W2B | **1 不過**：五份輸出沒有列檔名；現 repo 已有 `dispatch-package.md`、`review-prompt.md`，故「無範本」與「既有但不合新信封」未區分。**2 過**：入口指向可由連結與段落檢查推翻。**3 不過**：痛點寫舊模板 6 檔，驗收只列 5 檔，集合不封閉；CI 綠亦未證明契約語意保留。 |
| W3 | **1 不過**：`sys.exit(1)` 只推翻「誤報完整成功」，推不翻前半段已造成不可逆 partial write。**1b 過**：六 row 各有明確 0／逐字／不存在 oracle。**2 部分過**：末行不變量可判，但 5 個 writer 未具名。**3 不過**：已要求凍結前重量，驗收卻仍硬寫 157。**4 過**：PM 手寫留言可直接查。驗證的 211 列與 cpbl 9 檔都未給凍結時重新導出的封閉集合。 |
| W4 | **1 不過**：36 張不是版控 artifact，且「判準逐張可複驗」未列每類 oracle。**2 不過**：36／13／15 是可漂的 Project 現況，沒有重量與同源 artifact；57 個 git 檔可由 SHA 固定。**3 過**：三個具名檔可判，但已知 CLAUDE 錨點必須以語意／連結測試取代脆弱字串。**4 不過**：snapshot 先行只能證明有對帳資料，不能證明欄位可恢復。 |

### 守衛與基線實跑

- 在被審 SHA：`contract_tool_reconcile.py --check` rc=0（59 gaps），專測 **33 passed**；canonical citation 專測 **16 passed**。
- 但 W2A／W2B 沒有把此 SHA、預期 delta、執行者與「在合併結果上跑」寫進驗收。修改測試／處置表後的綠燈可與保留契約、刪掉契約兩種世界同時成立，屬零資訊。
- W3 現場已有 212 items＝211 Issues＋1 DraftIssue；所以「211 列」只是本輪快照，不是未來 W3 的固定母體。W0–W2B 落地後它必然還會變。

## R4 影響面：不過

1. **波 1／DraftIssue：不過。** 現行 `open_cmd.py` 仍有 Issue／DraftIssue 兩建立分支；Project 現存 1 張 DraftIssue 探針且沒有卡ID。`snapshot.build_rows` 對無卡ID item 直接跳過；review／deploy／checkpoint 等命令又只接受 Issue。W1 只說移除建立分支，未決定該 item 是封存、轉 Issue、保留探針，亦未聲明 legacy 讀取相容要保留多久。
2. **波 2B／CONTRACT_TOOL_RECONCILE：不過。** 守衛的契約母體是所有 `templates/*.md`；W2B 同時刪／改舊模板並新增五份模板。`--check` 能抓未登記的新／舊 gap，卻不能判斷「某契約符號消失」是合法取代還是把契約刪掉；現 spec 沒有 old→new symbol／guard mapping，也沒要求在 W2A＋W2B 合併結果上跑固定基線比較。
3. **波 3／停機回滾：不過，且為本輪最高風險。** canonical 只把 snapshot 定義為離線稽核與事後對帳；現 `state-snapshot/v1` 只輸出有卡ID的 card projection，沒有 Project item ID、field ID、option ID／名稱、view/filter 定義，也沒有 restore／bulk unarchive 指令。W3 只要求再加「階段／簡介／規格節」，仍補不出刪 option、改 view、封存 157 張後的逆操作。抽 1 張 unarchive 只證明單筆可逆，不證明 157 張與欄位 schema 可回復；任一步失敗後 `sys.exit(1)` 更不會撤銷已完成 mutation。故「snapshot＝唯一回滾通道」的前置不足。

## 級別與能力層級專項：不過

| spec | 判定 |
|---|---|
| W0 | **不成立。** spec 自己承認四檔是規則類、三份含紅線與授權；canonical §0 規定 public contract 至少 T3、紅線一律 T4。使用者 sign-off 是 T4 的審核／授權滿足方式，不會把 change tier 降成 T1。`MODEL_ROUTING.md` 亦要求「語意會改變規則時升級」，所以經濟型執行不成立。 |
| W1 | **成立。** 唯一寫入通道 public contract ⇒ T3；主力型執行＋獨立主力查核合理。 |
| W2A | **成立。** canonical／規則本體紅線 ⇒ T4；高階型＋跨家族合理。 |
| W2B | **不成立。** 新增五份 handoff 介面並改既有 contract templates，仍是 public contract；「內容已確認／機械配套」只降低不確定性，不消除影響面，依 §0 至少 T3。主力型可保留，但須套 T3 閘門與獨立查核。 |
| W3 | **成立。** 唯一寫入通道與不可逆 Project migration 至少 T3；T3+、高階型與跨家族建議符合最高者原則。 |
| W4 | **成立。** 跨 repo、Project 欄位值刪除不可 git revert，T3 與主力型＋獨立查核成立。 |

## Findings

### WF-REDESIGN1-P1-11

- severity: major
- blocking: true
- evidence: `AI_WORKFLOW.md:20-28` 規定 public contract 至少 T3、紅線 T4；`w0.md:15` 自認規則／紅線卻判 T1，`w2b.md:18-20` 新增／改寫 handoff contract templates 卻判 T2。
- disposition: W0 依紅線重推 T4、能力升高階型並保留使用者 sign-off／跨家族閘；W2B 至少升 T3。決議、brief、spec、父卡涉及級別與配置處同步更新。

### WF-REDESIGN1-P1-12

- severity: major
- blocking: true
- evidence: `w0.md:16` 與 `w2a.md:14` 兩個 file 資源逐字重疊；現行 `find_conflicts` 實跑回傳兩項衝突。決議 `:81` 的硬依賴不含 W0 與 W4，W4 spec 亦未要求 W3 終態。
- disposition: 把可執行依賴補成至少 `W0→W1→W2A→W2B→W3→W4`，或另給能被 assign 檢查的等價終態閘；父卡與六卡同步。

### WF-REDESIGN1-P1-13

- severity: major
- blocking: true
- evidence: `w3.md:24` 寫 cpbl 9 檔 PR，但 `w3.md:14` 無 cpbl 資源；`w4.md:14` 的 `Project #4 欄位操作` 經現行 `ResourceDeclaration` 實跑為格式錯誤，且 cpbl file claim 沒有可辨識 repo 邊界。
- disposition: 以現行工具可接受且能表達 source repo 的形狀完整宣告兩 repo write-set；Project 寫入若 grammar 刻意不擴，則用硬依賴／全域 Project lease 的受支援方案，並把機械檢查方法寫入驗收。

### WF-REDESIGN1-P1-14

- severity: major
- blocking: true
- evidence: 決議 §十二 `:92,95` 要求 alias normalization、prefix containment 與測試；六份 spec 無對應 acceptance。現 `resources.py:292-311` 仍是 exact set intersection，且 alias tests 為 0 的決議前提尚未轉成交付條件。
- disposition: 指定唯一 owner（最自然是 W3 或另經需求方裁定），列出兩項行為與正反例測試；更新 replacement／scope 對照，避免只靠 `file:cli/src/` 暗示。

### WF-REDESIGN1-P1-15

- severity: major
- blocking: true
- evidence: `w2b.md:12` 宣稱舊模板群 6 檔，`:20` 只列 5；`:18` 的五份新範本不列檔名，而現 repo 已存在 dispatch-package 與 review-prompt，故 create／rewrite 集合不可判。
- disposition: 列出六個舊檔與五個目標檔的封閉 mapping（remove／rewrite／replace），逐檔定義存在性、內容來源與 falsifier；修正「無範本」為可由現況證成的精確落差。

### WF-REDESIGN1-P1-16

- severity: major
- blocking: true
- evidence: `w2a.md:19` 的「新規則文脈」及 `:20` 的「改可驗形式」都沒有可執行 predicate；任意結果可由人工改標籤判過。
- disposition: 把文脈邊界改成明列 path／section／diff range，把三個腐爛自述列成封閉集合；每條寫 exact command、預期輸出與反例。

### WF-REDESIGN1-P1-17

- severity: major
- blocking: true
- evidence: W3 只承諾重量 160／157，驗證仍硬釘 211／9；W4 的 36／13／15 來自可變 Project，未附 versioned artifact。W2A／W2B guard 亦未釘 baseline SHA、預期 delta、runner 與 merge-result 時點。
- disposition: 每波開卡時把前張終態 SHA／Project snapshot hash 寫成字面基線；所有動態集合由同一次 artifact 產生，驗收引用 artifact 而非舊數字。guard 明列本輪基線（目前為 `688bf871...` 的 59 gaps／33 tests／16 citation tests）、允許 delta，並指定在 PR merge result 上跑。

### WF-REDESIGN1-P1-18

- severity: medium
- blocking: true
- evidence: Project 實查有 1 DraftIssue、無卡ID；`snapshot.py:50-52` 會跳過它，review／deploy／checkpoint 只收 Issue。W1 沒有既有資料處置與 legacy reader 退場條件。
- disposition: W1 前置列明該探針的唯一處置（封存／轉 Issue／經需求方裁定保留），並規定 DraftIssue 讀相容要保留到何種「零存量」證據後才可移除；測試 creation closed 與 legacy read 兩軸。

### WF-REDESIGN1-P1-19

- severity: major
- blocking: true
- evidence: `contract_tool_reconcile.py:92-115` 從全部 templates 導出 universe；`:1407-1426` 的 check 只比 actual vs registered。它能偵測集合改變，不能證明被刪 contract 已由新 template 等價承接；W2B 無 symbol mapping／merge-result guard。
- disposition: W2B 產出 old→new contract symbol 與 guard coverage 對照；先跑固定基線，再在 W2A＋W2B 合併結果跑 `--check` 與 33-test suite，任何消失／新增逐項對 disposition，不得只改 §6 讓綠燈恢復。

### WF-REDESIGN1-P1-20

- severity: critical
- blocking: true
- evidence: canonical `AI_WORKFLOW.md:649` 只稱 snapshot 為稽核／對帳；`snapshot.py:24-45,47-88` schema 無 item ID、field／option／view schema，且跳過無卡ID item；W3 前置只追加階段／簡介／規格節。repo 無 Project restore／bulk unarchive 實作，W3 僅抽 1 張驗證。
- disposition: 在任何不可逆步驟前，定義並於拋棄式 Project 實跑完整 restore rehearsal：snapshot 至少涵蓋受影響 item IDs、field／option IDs 與名稱、各 item 值、view/filter 與封存集合；提供逐步 inverse／forward-repair 指令、每步 checkpoint 與 read-back oracle。若平台刪 option 本質無法原樣復原，須明說不是 rollback，改成經需求方核可的 forward-repair 計畫與停機停損點；未實證前不得進步驟②以後。

## self_run

- `git rev-parse HEAD`、`origin/main`：均為被審完整 SHA；worktree clean。
- Ruby Psych：六份 YAML 0 parse error，六個 `replacement_rows` 均為 Array。
- `find_conflicts(W0,W2A)`：回傳兩個重疊 file claim；W4 Project claim 以現行 grammar 實跑拒收。
- Project #4 唯讀實查：212 items＝211 Issues＋1 DraftIssue。
- reconcile `--check` rc=0（59）；專測 33 passed；citation 專測 16 passed。
- 逐行讀取 `open_cmd.py`、`resources.py`、`snapshot.py`、reconcile script 與六份 spec；未執行任何寫入型 wfcli。

## 重審入口

先處理 P1-11～P1-20。下一輪仍從 R1 全表重跑；R1 過後依序複驗 R2 資源／依賴、R3 封閉 oracle／基線、R4 三個指定影響面。P1-20 的 restore rehearsal 是波 3 不可逆操作的硬前置，不能以「snapshot 已存在」替代。


## Comment 5469611932 · 2026-08-30T15:35:25Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（第五輪）

- 被審 SHA：`f24a7c7cb60d0b41c880f379bb0ae3840f65f771`
- 前四輪：issuecomment-5469108595、issuecomment-5469298925、issuecomment-5469364619、issuecomment-5469449938
- 裁決：**REQUEST_CHANGES；R1 過；R2、R3、R4 不過**
- 查核者身分自述：Codex（OpenAI），session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-30T23:35:25+08:00`

## 前輪 findings 閉環總覽

- **P1-12：已解。** 硬依賴已為全長 `W0→W1→W2A→W2B→W3→W4`；W0／W2A 逐檔宣告零逐字重疊。
- **P1-19：已解。** W2B 已要求 old→new contract symbol／guard coverage 對照、在 W2A＋W2B 合併結果上跑，且禁止只改登記恢復綠燈。
- **P1-11、P1-13～P1-18、P1-20：未解。** 詳見 findings。
- **新增 P1-21、P1-22。** 分別是遺漏 CI workflow write-set，以及仍存在的非零資訊驗收缺口。

## R1 前提：過

本輪依請求沿用第四輪 R1 的通過結論，並做回歸檢查：HEAD 與 `origin/main` 均為被審完整 SHA、worktree clean；六份 frontmatter 均可由 Ruby Psych 解析，`replacement_rows` 分別為 `[]／[12]／[1,3]／[]／[2,4,7,10,13,14]／[6,9,11]`；父卡基線等於本 SHA，父卡與決議均有全長硬依賴。未發現取代 owner 或波序回歸。

P1-20 的決議／spec 回滾語意衝突不改判 R1；它是「現行系統是否能安全施工」的 R4 阻斷，列於下方。

## R2 射程與資源：不過

1. **W0／W2A 舊重疊已解。** 逐檔宣告沒有相同字串，全長硬依賴也補齊。
2. **新舊語意不同合理，但缺 bootstrap／cutover 路徑。** 決議 §十二授權的是同 repo 內的 path-prefix containment；沒有授權把 `file:` 從 repo-relative path 改成跨 repo namespace。現行 `WF_RESOURCE_WRITESET1 §3.1` 明定它是「卡所屬 repo 根」的相對路徑，`registry.py` 則要求跨 repo 工作在目標 repo 開連結卡。W3／W4 新增 `file:cpbl-analytics/...` 慣例後，沒有說明它何時生效、舊卡如何遷移、W3 自己在新 matcher 上線前靠什麼取得互斥。實跑舊 matcher，該字串對 cpbl 卡的真 `file:scripts/...`／`file:docs/...` claim 都回傳 `[]`；這個結果本身是預期的舊行為，阻斷點是施工計畫沒有跨過這段過渡期。
3. **Project 寫入互斥仍無效。** `W3→W4` 只能排除這兩張波卡彼此並行，不能推出 W4 寫 board 時「沒有其他卡」；任一非本 Initiative 的 assign／amend／狀態寫入仍可並行。若刻意不擴 resource grammar，仍須有全 Project freeze／lease 或可機械驗的 no-other-writer gate。
4. **W2B 的派審舊檔無 owner。** 痛點明列現有「派審詞」為舊形狀，但 mapping 新建 `templates/review-dispatch.md`，既不移除也不改寫現存 `templates/review-prompt.md`。施工後會同時留下舊入口與新入口。
5. **DB alias registry 有事沒人做且順序倒置。** W2A 把 `local|prod` 與 alias 表「移交 DATABASE_CONTRACT」，卻不宣告／修改該檔；W4 雖廣稱 cpbl docs，驗收只要求 13 個現存宣告正規化，未要求更新 `docs/DATABASE_CONTRACT.md`。現 cpbl 契約仍使用 `production`。W3 又先於 W4 實作「已登記別名」比對，沒有可讀的 registry owner／格式／載入路徑。
6. **W3 承諾 CI job，write-set 未含 workflow。** 資源只有 `cli/src/`、`cli/tests/`、`scripts/` 與無效的跨 repo 字串；沒有 `.github/workflows/`，故「doctor 抽出＋CI job」的寫入有事卻未鎖。

## R3 內容與非零資訊：不過

以下逐條先列 falsifier（什麼結果會推翻），再判定規格是否真的封閉它。

| spec | 驗收逐條結果 |
|---|---|
| W0 | **1 過**：任一具名檔未 move、來源仍在或 draft 警語仍在即推翻。**2 過**：除 frontmatter／警語外任一內容改變即推翻。另有級別行自相矛盾，見專項。 |
| W1 | **1 過**：五條件缺欄即推翻。**2 過**：舊直建分支仍可用、或拒絕訊息無可跑補救即推翻。**3 過**：三組資料任一不在 fenced JSON 即推翻。**4 過**：零 acceptance 可開卡或旗標仍存在即推翻。**5 過**：W1 若先行生效 stage-rule 或新增動詞即推翻。DraftIssue 退場證據另於 R4 不過。 |
| W2A | **1 過**：角色集合／順序不符即推翻。**2 過**：不是 8×10、缺 delta 或缺 cutover 標記即推翻。**3 過**：rows 1／3 任一舊文殘留，或動到其他 owner row 即推翻。**4 不過**：命令 grep 整份 diff，合法刪除舊污染字面的 `-` 行也會命中，故按規格完成反而必紅；`<污染符>` 與「新規則文脈」也未展開成可直接執行的封閉命令。**5 不過**：宣稱附三條命令，只給兩條；「含總行數的自我描述」沒有第三個 predicate／command。**6 部分過**：八檔 move、引用與 tier-rules 可判；DATABASE_CONTRACT 移交沒有 owner／目標格式，該子句不可驗。 |
| W2B | **1 不過**：`review-prompt.md` 不在 old→new mapping；而「檔案存在＋四段標題」只能推翻空殼不存在，不能推翻舊入口仍被讀。**2 過**：P1-19 的 symbol mapping、合併結果 guard 與逐項 disposition 已可推翻只改登記。**3 過**：AGENTS／README 未指向指定 L0 即推翻。**4 不過**：依賴未封閉的 AC1；舊 `review-prompt.md` 留存時仍可能判五檔 mapping 完成。 |
| W3 | **1 過（限宣告語意）**：七步缺留痕、任一步失敗仍宣稱完整即推翻；它不證明 rollback，該點列 R4。**1a 不過**：正反例有寫，但跨 repo 前綴與現行 repo-relative 契約相反，alias registry 又不存在。**1b 過**：六 row 都有 0／逐字／不存在等 oracle。**2 不過**：「5 寫入點」未具名，任何五處都可自稱全集。**3 不過**：前置要求開卡時重量，驗收仍固定寫 157。**4 過**：本卡轉移若不是 PM 固定留言即推翻。驗證仍固定 211 列與 cpbl 9 檔，也違反同一次 artifact 基線。 |
| W4 | **1 不過**：「判準逐張可複驗」未列三種 disposition 各自的輸入／oracle；同一張卡可被任意歸類仍自稱可複驗。**2 不過**：引言要求 artifact 重量，條文仍固定 57／13／15。**3 過**：三個具名文件的目標結果可由語意／連結測試推翻；執行不得依已知會漂的單一錨點。**4 過（限刪除結果）**：欄位仍存在或 snapshot 未先產生即推翻；snapshot 是否足以復原屬 R4。驗證的「僅剩真活卡」沒有「真活卡」封閉判準，仍為零資訊。 |

### 基線與守衛實跑

- 父卡 spec 基線已正確釘本 SHA。
- 被審 SHA 的 reconcile `--check` rc=0，輸出 59 gaps 全有 disposition；專測 33 passed；canonical citation 專測 16 passed。
- P1-17 仍未閉環：W3 說驗收引用重測 artifact，卻在 AC／驗證寫死 157／211／9；W4 同樣在 AC 寫死 36／57／13／15。這些不是說明句中的歷史量測，而是實際 pass/fail 字面。

## R4 現行系統影響：不過

1. **波 1 封 DraftIssue：不過。** W1 已明知現行 `snapshot.build_rows` 跳過無卡ID item，卻把「一次 snapshot 證明」列為讀相容退場證據；`snapshot.py:50-52` 的實作因此能在 DraftIssue 仍存在時產生表面上的零存量。需指定 raw Project item-list artifact／查詢作為零存量 oracle，或先擴 snapshot 使其含無卡ID item；需求方一句裁定只能決定探針命運，不能修補錯誤證據。
2. **波 2B CONTRACT_TOOL_RECONCILE：不過。** P1-19 本身已解，但 W2A 的污染 grep 會把合法刪除判紅，W2B mapping 又漏掉 `review-prompt.md`。因此 W2A＋W2B 合併結果仍可能同時出現「守衛無法按規格通過」與「舊派審 contract 留存」；必須先修 AC4 與 closed mapping，P1-19 才能在施工時發揮效力。
3. **波 3 停機／回復：不過，仍為最高風險。** W3 新增完整 restore rehearsal、inverse command、read-back oracle、forward-repair 與停損核可，方向正確；但決議 §十的「唯一定義」仍只列舊三前置，且下一行仍宣稱「回滾唯一通道＝每日 snapshot」。這與 W3 明文「步④起不是 rollback」及新增 rehearsal 相衝突。父卡引用 P1-20 不能消除上游唯一定義的矛盾。應把決議同步為同一份前置與 rollback／forward-repair 邊界，再讓 brief、父卡、spec 只引用它。
4. **W4 board 欄位刪除：不過。** snapshot 先行只保證有對帳材料；W4 自己也承認不是自動重建。沒有全 Project writer freeze／lease 時，重量、snapshot、逐卡處置與刪欄之間可被其他卡寫入，rehearsal 的 read-back oracle也失去共同切點。

## 級別與能力層級：不過

| spec | 判定 |
|---|---|
| W0 | **不過。** T4 重推正確，但同一行先寫「執行 主力型」又寫「能力：執行 經濟型」；階段計畫仍寫「T1 跳過研究／規劃」。實際建議與所適用閘門無唯一答案。 |
| W1 | **過。** 唯一寫入通道 public contract ⇒ T3；主力型執行＋獨立主力查核成立。 |
| W2A | **過。** 規則紅線 ⇒ T4；高階型＋跨家族成立。 |
| W2B | **過。** contract templates 是 public contract ⇒ T3；主力型＋獨立查核成立。重複寫一次能力不影響語意。 |
| W3 | **過。** 不可逆 Project migration＋唯一寫入通道大改 ⇒ 至少 T3；T3+、高階型、跨家族符合最高者原則。 |
| W4 | **過。** 跨 repo、Project 欄位刪除且不可 git revert ⇒ T3；主力型＋獨立查核成立。 |

## Findings

### WF-REDESIGN1-P1-11

- severity: major
- blocking: true
- evidence: `w0.md:14-15` 同時保留「T1 跳過」及互斥的主力型／經濟型執行建議；canonical §0 要求最高風險與 T4 閘門。
- disposition: W0 刪除 T1 殘文；只保留一個實際執行能力建議與理由，並明確說明既有需求方 sign-off 滿足哪一個 T4 Gate、哪些獨立查核仍須跑。

### WF-REDESIGN1-P1-13

- severity: major
- blocking: true
- evidence: 決議 §十二只指定 path prefix containment，未定義 repo-qualified key；`WF_RESOURCE_WRITESET1:128,138` 仍定義 repo-relative path，`registry.py:546-574` 仍要求跨 repo 另開連結卡。W3 未列新舊 matcher 的生效點與自舉保護；W4 的硬依賴也未排除 Initiative 外 board writer。
- disposition: 二選一並把過渡寫入 spec。**A（建議）**：維持 ownership contract，把 cpbl 相容改動拆成 cpbl 連結卡，雙向釘 Issue／SHA，各卡使用各自 repo-relative claim；該卡須在 W3 cutover 前終態。**B**：若需求方要單一卡跨 repo，W3 正式把 key 升為 `(repo, path)`，補 repo slug 來源、legacy migration、unknown repo fail-closed 與跨 repo tests；W3 自舉期間以全域 freeze／人工 lease 保護。兩案都須另為 Project 寫入設全域 freeze／lease，不得以波卡序列代替。

### WF-REDESIGN1-P1-14

- severity: major
- blocking: true
- evidence: W3 AC1a 沒有定義 repo boundary，且依賴不存在的「已登記別名」來源；W2A 不改 DATABASE_CONTRACT，W4 又晚於 W3且未驗收該契約。現 cpbl `docs/DATABASE_CONTRACT.md` 仍宣告 `production`。
- disposition: 先指定 alias registry 的唯一 owner、檔案、schema、載入失敗行為與施工順序；`file:` prefix tests 需納入同 repo、不同 repo、component boundary、case／normalization 與 unknown repo fail-closed，並與既有 writeset 契約一致。

### WF-REDESIGN1-P1-15

- severity: major
- blocking: true
- evidence: `w2b.md:12` 把現有派審詞列為舊形狀；`:18` 卻只新建 `review-dispatch.md`，完全未處置現存 `templates/review-prompt.md`。
- disposition: 把 `review-prompt.md` 納入封閉 old→new mapping，明定 remove／rename／rewrite、所有 inbound link 轉向與「舊入口零引用」oracle；不要只驗五個新檔存在。

### WF-REDESIGN1-P1-16

- severity: major
- blocking: true
- evidence: W2A AC4 對整份 diff grep；被刪舊字面仍出現在 `-` 行，完成取代會被判紅。AC5 宣稱三條命令卻只列兩條，第三項沒有 executable predicate。
- disposition: AC4 改驗 post-image，或只掃 added lines 並排除 diff header；逐符展開 exact commands 與唯一豁免。AC5 補第三條能辨認「總行數自述」的命令、預期輸出與反例。

### WF-REDESIGN1-P1-17

- severity: major
- blocking: true
- evidence: `w3.md:19`、`w4.md:16` 宣稱開卡重測；但 W3 AC3／驗證仍固定 157／211／9，W4 AC1／2 仍固定 36／57／13／15。
- disposition: 歷史量測只能留在痛點且標日期；所有 AC 改引用同一個 versioned artifact 的集合／count 欄位，開卡時釘 artifact hash、Project snapshot hash 與前卡終態 SHA。

### WF-REDESIGN1-P1-18

- severity: major
- blocking: true
- evidence: W1 `:15` 同時承認 snapshot 跳過無卡ID DraftIssue，卻要求 snapshot 證明零存量；`snapshot.py:50-52` 可重現該假陰性。
- disposition: 退場 oracle 改為涵蓋所有 Project items 的 raw inventory artifact，或先擴 snapshot；明列 content type／item ID／card ID 三欄與 expected zero，再保留 creation-closed、legacy-readable 兩軸測試。

### WF-REDESIGN1-P1-20

- severity: critical
- blocking: true
- evidence: `w3.md:15-18` 已改成 rehearsal＋forward-repair；決議 §十 `:82-83` 仍把舊三項稱唯一定義並把 daily snapshot 稱唯一 rollback，兩者不能同時成立。
- disposition: 在決議的唯一停機定義內合併 P1-20 全文，明切可逆步驟、不可逆邊界、forward-repair 與停損；父卡／brief／W3 只引用同一來源。拋棄式 Project rehearsal 的 artifact 未出現前不得開放步②。

### WF-REDESIGN1-P1-21

- severity: major
- blocking: true
- evidence: W3 `:21` 要新增 CI job，`:14` 的資源宣告沒有任何 `.github/workflows/` path。
- disposition: 指名實際 workflow 檔並納入 W3 write-set；若不修改 workflow，則把「CI job」改成既有 job 的具名 command／step 並證明無檔案寫入。

### WF-REDESIGN1-P1-22

- severity: major
- blocking: true
- evidence: W3 AC2 只稱「5 寫入點」未列集合；W4 AC1 沒有三類逐卡 disposition oracle，驗證「真活卡」也未定義母體／predicate。任意五處、任意分類結果均可自述通過。
- disposition: W3 封閉列出五個 writer symbol／path 並以 inventory test 證明全集；W4 對升級／退回清單／結案補完逐類列必要輸入與 falsifier，活卡視圖引用同一 snapshot 的明確 predicate。

## self_run

- `git rev-parse HEAD`／`origin/main`：均為被審完整 SHA；worktree clean。
- Ruby Psych：六份 YAML 均可解析，六個 `replacement_rows` 均為 Array。
- 現行 `find_conflicts`：兩組跨 repo 前綴對真 cpbl repo-relative claim 均回傳 `[]`。
- reconcile `--check` rc=0（59 gaps）；專測 33 passed；citation 專測 16 passed。
- 唯讀核對父卡 #177、決議、brief、六份 spec、writeset 契約、`resources.py`、`registry.py`、`snapshot.py` 與 cpbl 現行契約；未執行任何寫入型 wfcli。

## 重審入口

先處理未解的 P1-11、P1-13～P1-18、P1-20～P1-22。下輪可維持 R1 回歸檢查後，依序重驗 R2 的 repo／Project 互斥與完整 write-set、R3 的 exact predicate／同源 artifact、R4 的 DraftIssue 零存量與波 3 rehearsal 唯一定義。


## Comment 5470031961 · 2026-08-30T16:57:14Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（第六輪）

- 被審 SHA：`0ddccf2c7852b478a815a720f46628a46c1fce5b`
- 前五輪：issuecomment-5469108595、issuecomment-5469298925、issuecomment-5469364619、issuecomment-5469449938、issuecomment-5469611932
- 裁決：**REQUEST_CHANGES；R1 全表不過，依有序閘門停止，不進 R2–R4**
- 查核者身分自述：Codex（OpenAI），session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T00:57:14+08:00`

## R5 findings 在 R1 可判範圍的重驗

- **P1-13：已解（R1 射程）。** 五份現行 spec 均無 cpbl claim；W3′ 明列零 cpbl 接觸，跨 repo 工作已移出本 Initiative。
- **P1-11：未解。** W0 已刪 T1 殘文並補 sign-off Gate／獨立查核，但同一行仍同時宣告「唯一執行能力＝主力型」與「能力：執行 經濟型」。
- **P1-14：未全解。** W3′ 已承接 prefix、alias registry 與五類測試，但漏掉決議 §十二同樣指定 W3 唯一 owner 的 conflict candidate 母體變更。
- **P1-15～P1-22 其餘項**：可看到對應文字修正已進入被審 SHA；因 R1 gate 未過，本輪不對其 R2／R3／R4 實質效力背書，也不沿用第五輪未解判定。

## R1 前提：不過

### 結構總表

| 來源 | 結果 | 證據 |
|---|---|---|
| 被審版本／父卡基線 | **過** | HEAD、`origin/main`、父卡 spec 基線均為完整被審 SHA；worktree clean。 |
| 四波五卡／硬依賴 | **部分過** | 父卡驗收、決議 §十、brief 拆卡表均有 `W0→W1→W2A→W2B→W3′`；五份 spec 存在且 w4.md 已刪。但父卡 title／routing／簡介、決議檔頭／§十標題、brief frontmatter 仍宣稱五波或本卡含不可逆波 3。 |
| 零 cpbl／零不可逆 | **部分過** | 五份 spec 資源 0 個跨 repo claim，W3′ 非射程也明列零 cpbl／零看板 mutation；但父卡 routing 仍說子卡含「不可逆狀態遷移（波 3）」，與現行驗收直接衝突。 |
| 14-row 唯一 owner | **不過** | 決議 row 10 owner＝切換 Initiative，W3′ metadata／AC 卻 owner row 10；決議 row 13 owner＝W3，W3′ metadata 不含 row 13且非射程不做，§十之二又把內建 Status writer 移除交給切換 Initiative。 |
| 切換 Initiative 邊界 | **不過** | W1／W2A／brief／list-items／決議未定區仍把狀態切換稱「波 3」；W3 清單觀察句仍以 15 值看板與 157 終態卡為主，兩項明屬切換 Initiative。 |
| 級別／能力 | **不過** | W1／W2A／W2B／W3′ 的 tier 推導與新邊界一致；W0 T4 正確，但實際執行能力有主力型／經濟型兩個互斥答案。 |

### 五份 spec 全表

1. **W0：不過。** `replacement_rows=[]`、T4、sign-off Gate 與獨立搬移查核均對齊；但 `w0.md:15` 先稱唯一建議為主力型，下一句又稱執行經濟型，派工無唯一值。
2. **W1：不過。** owner row 12 與清單／open 射程正確；`w1.md:11` 仍把狀態語彙歸「波 3」，而新 W3′ 明文不切換。這會讓讀者把非射程錯派回本 Initiative。
3. **W2A：不過。** owner rows 1／3 正確；但 `w2a.md:11,17` 仍寫「波 3」／`cutover＝波 3`，與同檔 `:21` 的「切換於切換 Initiative」互相矛盾。過渡 canonical 的 cutover anchor 因此有兩個答案。
4. **W2B：過（R1）。** 無 replacement row；contract templates／L0／舊模板清理與 W2A 終態前置對齊新四波配置。其逐條 oracle 留待 R3。
5. **W3′：不過。** 內容大致是可逆 CLI 內改；但 `replacement_rows=[10]`／AC2 與決議 row 10 owner 衝突，決議 row 13 又沒有由本 spec 承接；另漏掉決議 §十二要求 W3 實作的 candidate 母體「有分支或 worktree」。

### 其他上游／父卡不一致

- 父卡現行 title 與簡介仍寫「五波施工」；routing 仍以「不可逆狀態遷移（波 3）」推導能力。Log 裡的歷史舊文不列 finding，但 title、routing、簡介是現值，必須同步。
- 決議 `:5` 仍寫「生效走五波施工卡」，§十標題仍是「五波實施」；§十三仍寫舊卡歸波 4、廢止值隨波 3 消滅。
- brief frontmatter description 仍是五波；待驗假設仍稱刪 option 實測為波 3 前置。
- `list-items.md` 的 W3 觀察句仍是「15 值單欄＋157 張終態卡」；真正 W3′ 痛點應是 Log、fenced JSON、doctor、拒絕訊息、resource matcher 與 snapshot。依目前文字升級清單項會把 cutover 工作重新帶回 W3′。

### 取代 owner 的可重現對照

- 五份 frontmatter 均可由 Ruby Psych 解析：W0 `[]`、W1 `[12]`、W2A `[1,3]`、W2B `[]`、W3′ `[10]`。
- 決議表卻是 row 10＝切換 Initiative、row 13＝W3；§十之二 item 5 又把內建 Status writer 移除交給切換 Initiative。
- 因此不是「新 Initiative 尚未有 spec，所以 rows 未覆蓋」；而是同一 row 10 被兩個 owner 宣稱、row 13 在決議內部也有兩個歸屬答案。

## R2 射程與資源：不過（未審）

R1 未過，依指定順序未進入非射程縫隙、資源互斥與切換 Initiative 清單項 ownership 查核。P1-13 的「本 Initiative 五份 spec 無 cpbl claim」只是一項 R1 事實，不等同 R2 全過。

## R3 內容：不過（未審）

R1 未過，未逐條執行 falsifier、W2A post-image command、W2B mapping、W3′ 六 writer inventory 與動態 artifact 基線。本輪不得用於替代 PM 明列的「R3 零資訊／W2A 內部一致性」未驗項。

## R4 影響面：不過（未審）

R1 未過，未裁定 W1 raw inventory、W2B reconcile、W3′ reader compatibility 或 §十之二切換 seed／rehearsal 粒度。停機步序移交是否足夠須在 owner matrix 與 cutover anchor 唯一後再審；本輪沒有背書。

## Findings

### WF-REDESIGN1-P1-11（延續）

- severity: major
- blocking: true
- evidence: `w0.md:15` 先逐字寫「唯一執行能力建議＝主力型」，同一行後段又寫「能力：執行 經濟型」。
- disposition: 保留一個答案。依本行既有推導，最小修正是刪除過期的「能力：執行 經濟型」子句，並把查核能力／獨立性各自只寫一次；決議、brief、父卡若承載能力值亦同步。

### WF-REDESIGN1-P1-14（延續）

- severity: major
- blocking: true
- evidence: 決議 `:63,107` 明定 conflict candidate 母體由 29% 改為「有分支或 worktree」且唯一 owner＝W3；`w3.md:17-22` 只有六個 Log writer、reader、doctor、拒絕訊息、prefix／alias、snapshot，沒有 candidate selection 的 AC 或測試。
- disposition: W3′ 增列「候選卡集合＝有 branch 或 worktree」的 old→new 行為、正反例與 inventory test；不要把 path-prefix test 當成已涵蓋候選母體，兩者是不同層。

### WF-REDESIGN1-P1-23

- severity: major
- blocking: true
- evidence: 父卡 title／routing／簡介仍為五波且含不可逆波 3；決議 `:5,79`、brief `:4` 亦仍是五波，與各自現行「四波五卡、零不可逆」段落衝突。
- disposition: 只改現值、不改歷史 Log：父卡 title、routing、簡介；決議檔頭與 §十標題；brief frontmatter description 全部同步為四波五卡、W3′ 可逆 CLI 內改。能力理由改由 W2A T4 紅線支撐，不再引用已移出的不可逆 cutover。

### WF-REDESIGN1-P1-24

- severity: critical
- blocking: true
- evidence: 決議 row 10＝切換 Initiative，但 W3′ metadata／AC2＝row 10；決議 row 13＝W3，但 W3′ 不承接，§十之二 item 5 又＝切換 Initiative。唯一 owner 矩陣已失去唯一性與可執行性。
- disposition: 按現有安全邊界，建議 row 10 改 owner＝W3′（純 CLI 移除，可 git revert），row 13 改 owner＝切換 Initiative（與 Status／部署欄退位同切換）；同步決議 §一、§十／§十之二、W3′ frontmatter／AC、brief 與父卡。若需求方另選 owner，也必須讓每 row 恰一 owner且 spec 驗收一致。

### WF-REDESIGN1-P1-25

- severity: major
- blocking: true
- evidence: `w1.md:11`、`w2a.md:11,17`、brief `:35`、決議 `:112` 仍把 cutover 稱波 3；`list-items.md:10` 又把 15 值看板與 157 終態卡列為 W3 觀察句，直接違反 W3′ 零看板變更非射程。
- disposition: 所有現值中的狀態切換 anchor 統一改「切換 Initiative」；W3′ 清單觀察句只保留本卡可解的 Log／parser／doctor／拒絕訊息／resource matcher／snapshot 落差。歷史 Log 不回寫。

## self_run

- `git rev-parse HEAD`／`origin/main`：均為被審完整 SHA；worktree clean。
- Ruby Psych：五份 spec 0 parse error，`replacement_rows` 均為 Array。
- `rg`：五份現行 spec 的跨 repo claim 0；完整依賴鏈在決議、brief、父卡各一處。
- owner 對照：逐字核對決議 rows 1–14、五份 frontmatter 與 W3′ AC；確認 row 10／13 衝突。
- 唯讀讀取父卡 #177 現行 title／routing／簡介／驗收／驗證；未執行任何寫入型 wfcli。

## 重審入口

先修 P1-11、P1-14、P1-23～P1-25並 bump 父卡基線。下一輪仍從 R1 全表重跑；需同時滿足：四波五卡現值零舊拓樸、row 10／13 各唯一 owner、所有 cutover anchor 唯一指向切換 Initiative、W3′ 清單觀察句不含看板 mutation。R1 過後才進 R2–R4，屆時再判 §十之二 seed 粒度是否足夠。


## Comment 5473075216 · 2026-08-31T02:48:26Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（第七輪）

- 被審 SHA：`b4979c6ef05099b19cfc1fb7eeaa957bac24c1b6`
- 前六輪：issuecomment-5469108595、issuecomment-5469298925、issuecomment-5469364619、issuecomment-5469449938、issuecomment-5469611932、issuecomment-5470031961
- 裁決：**REQUEST_CHANGES；R1 仍不過，依有序閘門停止，不進 R2–R4**
- 查核者身分自述：Codex（OpenAI），session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T10:48:26+08:00`

## 第六輪 findings 重驗

- **P1-11：已解。** W0 tier＝T4；執行建議只剩主力型；查核路由只剩需求方 sign-off，並另列搬移完整性檢查。
- **P1-14：已解（R1 內容承接）。** W3′ AC5 已把 candidate 母體、path-prefix、DB alias 三項分開，母體含 old→new、正反例及差集 inventory test。
- **P1-24：已解。** row 10＝W3′，row 13＝切換 Initiative；五份 frontmatter 與決議矩陣一致。
- **P1-25：已解。** W3′ 清單觀察句已只列 CLI 內部落差，不再含看板切換／157 張封存。
- **P1-23：未全解。** repo 內主要拓樸與父卡 title／簡介已同步；父卡現行 routing 仍引用已移出的不可逆波 3，另四份 W0 來源草稿的未生效警語仍寫五波施工。

## R1 前提：不過

### 已通過部分

1. **版本與基線：過。** HEAD、`origin/main`、父卡 spec 基線均為完整被審 SHA；worktree clean。
2. **四波五卡與依賴：過。** 決議、brief、父卡驗收／簡介及五份 spec 均為 `W0→W1→W2A→W2B→W3′`；w4.md 不存在。
3. **14-row owner matrix：過。** 五份 metadata 可由 Ruby Psych 解析，rows 分別 `[]／[12]／[1,3]／[]／[10]`；rows 2／4／6／7／9／11／13／14 唯一歸切換 Initiative，rows 5／8 已完成。
4. **五份 spec 前提：過。** W0、W1、W2A、W2B、W3′ 各自的射程、依賴與 tier 已對齊決議；現行五份 spec 有 0 個 cpbl claim、0 個不可逆看板動作。
5. **父卡 title／簡介：過。** Issue title 與簡介已是四波五卡、零不可逆、零 cpbl。

### 仍阻斷部分

1. **父卡 active routing 仍是舊前提。** 現行 header 仍逐字宣稱「子卡含 canonical 紅線改版（波 2）與不可逆狀態遷移（波 3），取風險最高者」。但本輪決議、父卡驗收與 W3′ 都明定本 Initiative 零不可逆、cutover 歸切換 Initiative。高階型結果可由 W2A T4 支撐，不代表錯誤理由可保留。
2. **Project 重複欄位已知但尚無 owner。** 唯讀實查 Project #4：Issue `content.title` 已是四波五卡；Project item 的 `title` 投影與 `功能` 仍是五波施工。父卡、W1、§十之二均沒有一條 AC 承接它；「W1 或切換 Initiative 處理」仍是候選，不是唯一 owner 與 pass/fail。
3. **四份 W0 來源草稿仍寫五波。** `pm-conduct.md`、`executor-conduct.md`、`reviewer-conduct.md`、`list-intake-requirements.md` 的未生效警語仍稱五波施工。W0 AC 會移除警語，因此不另開 finding；但它們仍是 P1-23 所稱「現值全數同步」的反例，最小修正是現在同步為四波五卡，避免 W0 開工前誤讀。

## 級別與能力層級（R1 可判部分）

- W0 T4／主力執行／需求方 sign-off：成立。
- W1 T3／主力執行＋獨立主力查核：成立。
- W2A T4／高階執行＋跨家族高階查核：成立。
- W2B T3／主力執行＋獨立主力查核：成立。
- W3′ T3／主力執行＋獨立主力查核：成立。
- 父卡建議高階型仍成立，但理由應改為 Initiative 架構協調＋W2A canonical T4 紅線，不得再引用不在本卡的不可逆 cutover。

## R2 射程與資源：不過（未審）

R1 未過，未進入資源 prefix 交集、W2B／W3′ 依賴釋放或切換清單項 ownership 的完整裁定。不得把「五份 spec 無 cpbl claim」解讀為 R2 全過。

## R3 內容：不過（未審）

R1 未過，未執行 W2A post-image 命令、逐條 falsifier、W3′ six-writer inventory 或動態 artifact 基線。PM 所列 R3／W2A 未驗項保持未驗。

## R4 影響面：不過（未審）

R1 未過，未裁定 W1 raw inventory、W2B reconcile、W3′ reader compatibility 或切換 Initiative seed／rehearsal。前輪未解結果不沿用。

## Findings

### WF-REDESIGN1-P1-23（延續）

- severity: major
- blocking: true
- evidence: 父卡現行 routing 仍以「不可逆狀態遷移（波 3）」說明能力；決議 §十、父卡簡介／驗收與 W3′ 均明定零不可逆、cutover 歸切換 Initiative。四份 W0 來源草稿的未生效警語亦仍稱五波施工。
- disposition: 父卡 routing 改成「高階型：Initiative 架構協調＋W2A canonical T4 紅線」；查核理由保留跨家族／sign-off。四份 W0 草稿警語同步四波五卡，或在 W0 spec 明確把該四行列為 move 前必刪的封閉集合。

### WF-REDESIGN1-P1-26

- severity: major
- blocking: true
- evidence: `gh project item-list 4` 對 #177 回傳 Issue content title＝四波五卡，但 Project item `title` 與 `功能` 仍＝五波施工；現有五卡與切換 seed 均無 owner／退場 oracle。平台沒有由 `wfcli amend` 更新這些重複欄位的通道。
- disposition: **歸 W1，⛔ 不等切換 Initiative。** 理由：這是 open／card metadata 的雙事實來源缺陷，不是 cutover schema migration；拖到切換會讓整個本 Initiative 期間持續顯示錯誤前提。W1 增列既有 `amend` 動詞的 feature／routing 更新能力（⛔ 非新增動詞）、補 `amend_cmd.py`／Project 欄位 write-set 與 round-trip test；用該通道把 #177 routing、Project item title／功能同步。退場 oracle＝Issue title、Project item title、功能三者均含「四波五卡」且零「五波施工」，routing 零不可逆波 3 字樣。

## self_run

- `git rev-parse HEAD`／`origin/main`：均為被審完整 SHA；worktree clean。
- Ruby Psych：五份 spec 0 parse error，五個 `replacement_rows` 均為 Array。
- `rg`：五份現行 spec 跨 repo claim＝0；owner matrix row 10／13 與 metadata 一致。
- 父卡唯讀：Issue title／簡介／基線已同步；active routing 仍舊。
- Project #4 唯讀：#177 `content.title` 已新，Project item title／功能仍舊。
- 未執行任何寫入型 wfcli，未修改 repo／看板。

## 重審入口

處理 P1-23 與 P1-26並 bump 父卡基線。下一輪 R1 只需核：active routing 零不可逆舊前提；W1 明列 metadata amend owner、write-set 與三欄退場 oracle；Project 現值若尚未更新可保留為 W1 待做，但不得再無 owner。R1 過後才進 R2–R4。


## Comment 5473179838 · 2026-08-31T03:05:43Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（第八輪）

- 被審 SHA：`07db6e634ec7b99f0c72b8843a4d82e948ae8c28`
- 前七輪：issuecomment-5469108595、issuecomment-5469298925、issuecomment-5469364619、issuecomment-5469449938、issuecomment-5469611932、issuecomment-5470031961、issuecomment-5473075216
- 裁決：**REQUEST_CHANGES；R1 過，已依序完成 R2–R4；R2、R3、R4 不過**
- 查核者身分自述：Codex（OpenAI），session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T11:05:43+08:00`

## 前輪 findings 重驗

- **P1-23：已解。** 四份 conduct 草稿橫幅已同步四波五卡；repo 內現行規劃來源不再殘留五波施工拓樸。父卡 routing 尚有舊句，但已由 P1-26 唯一承接，不再把「尚未施工」誤判為「無 owner」。
- **P1-26：已解（規劃 ownership）。** W1 AC5b 已列唯一 owner、既有 `amend` 增量通道、Issue title／Project item title／`功能`／routing 四個 write target、round-trip test 與三欄＋routing 退場 oracle。**不要求在 W1 前另以 `gh issue edit` 直改**；那會繞過本案正要補出的通道。現行舊值只代表 AC 尚未執行，不是 R1 前提再度失配。

## R1 前提：過

1. **版本／基線：過。** HEAD、`origin/main`、父卡 spec 基線均為完整被審 SHA；worktree clean。五份 frontmatter 均可由 Ruby Psych 解析，`replacement_rows` 都是 Array。
2. **四波五卡／硬依賴：過。** 決議、brief、父卡與五份 spec 一致為 `W0→W1→W2A→W2B→W3′`；前張終態才可開下張。
3. **取代矩陣：過。** 五份 metadata 為 `[]／[12]／[1,3]／[]／[10]`，與 14-row 唯一 owner 矩陣一致；cutover／cpbl rows 唯一歸切換 Initiative。
4. **W0：過。** conduct/intake move、T4、需求方 sign-off 與獨立完整性查核一致。
5. **W1：過。** 清單、唯一 `--from-issue`、DraftIssue 處置、表單、P1-26 metadata amend 均有 owner；不先行生效 stage rule。
6. **W2A：過。** canonical＋八份 stage-rules＋tier-rules 同輪 T4，且只承接 rows 1／3；看板切換明確移出。
7. **W2B：過。** 只承接 contract templates／L0／舊模板清理，W2A 終態為前置；規則制定未回流。
8. **W3′：過。** 只承接 aiwf 可逆 CLI 內改與 row 10；零看板 schema mutation、零 cpbl claim；W2B 終態為前置。
9. **切換邊界：過。** §十之二只作後續 Initiative seed；本 Initiative 不取得 cutover 授權。

### 級別與能力層級

- W0：T4／主力型執行／需求方 sign-off，成立；conduct 是規則紅線，最高者是風險。
- W1：T3／主力型＋獨立查核，成立；唯一寫入通道是 public contract。
- W2A：T4／高階型＋跨家族查核，成立；canonical 與規則紅線取最高者。
- W2B：T3／主力型＋獨立查核，成立；contract templates 是 public contract。
- W3′：T3／主力型＋獨立查核，級別結果成立；但「全部可 git revert」的回復敘述不完整，見 R4／P1-33。
- 父卡高階型成立，理由只能是 Initiative 架構協調＋W2A T4，不再引用已移出的不可逆 cutover。

## R2 射程與資源：不過

### 非 finding 的合理重疊

- 現行逐字 matcher 會看到 W1／W3′ 同宣告 `file:cli/tests/`。
- 依 W3′ 目標的 component-prefix matcher，另會看到 W1／W2B 的 tests、W1／W3′ 的 `cli/src`＋tests、W2B／W3′ 的 templates＋tests 相交。
- **以上都不是 finding**：每一對均被完整硬依賴鏈隔開，前卡已終態才開後卡，資源已釋放。這正是「取代現有機制時有衝突，但以序列化＋明確交接處理」的合理情形。W0 與 W2A 的逐檔 claim 也已無交集。

### Blocking 缺口

1. **切換 Initiative 清單項沒有人建立。** 父卡結案要求該清單項已建立，決議 §十之二只列 scope seed；`list-items.md` 卻明定本 Initiative 只建立 W2A／W2B／W3′ 三項，並把切換項寫成「屆時建立」。父卡又明定自己不做機械工作。結果是「有結案條件、無唯一執行卡」。見 P1-27。
2. **W2B→W3′ 的 doctor contract 沒有交接。** W2B 會新立／改寫 dispatch contract，現行 AGENTS、dispatch-package、handoff-contract 與 consumer-conformance 都直接要求 `wfcli doctor`；W3′ AC3 卻允許「移除或轉薄」，且 W3′ write-set 不含這些消費端。硬依賴只避免同時改檔，不能讓已發布 contract 自動相容。見 P1-28。

## R3 內容與非零資訊：不過

以下每條先列能推翻它的結果，再裁定規劃是否把該結果機械化。

### W0

1. **AC1 過。** 推翻＝任一來源檔仍存在、目的檔缺席、或目的檔仍帶 draft 警語；路徑集合與零雙居所已封閉。
2. **AC2 過。** 推翻＝move 前後除 frontmatter／警語外有內容差異；`git log --follow`＋diff 足以判定。

### W1

1. **前置不過。** 推翻＝raw inventory 少任一 Project item／三欄，或 DraftIssue count 非 0 卻移除讀相容。字面 oracle 正確，但沒有指定 W1 當下可跑的 query／producer、artifact 路徑與 hash；W3′ AC6 又把自己的後置產物稱為 W1 資料源，與硬依賴時序相反。見 P1-29。
2. **AC1 過。** 推翻＝五條件有任一未成獨立欄，或三格身分不完整。
3. **AC2 過。** 推翻＝任一直接建 issue／DraftIssue 路徑仍成功，或拒絕訊息的補救命令跑不通。
4. **AC3 不過。** 推翻＝JSON 缺任一欄、重複／畸形 payload 被接受、writer 與 reader round-trip 不同。spec 只寫「fenced JSON」，沒有 schema version、唯一 sentinel／定位、鍵名、型別、重複區塊與 malformed 的 fail-closed 行為；W3′ 又要接手同一格式，兩卡沒有可驗的 interface handoff。見 P1-30。
5. **AC4 過。** 推翻＝零 acceptance 仍開得成，或 `--needs-deploy` 仍可用。
6. **AC5b 過（規劃層）。** 推翻＝Issue title／Project item title／`功能` 任一不含四波五卡或仍含五波施工，或 routing 仍含不可逆字樣；round-trip 與 oracle 已列。
7. **AC5 過。** 推翻＝W1 使撤銷 stage-rule 提前生效，或收件模板缺操作註記。

### W2A

1. **AC1 過。** 推翻＝角色非 6、名稱不符、或 §1／§2 未在 §0 前。
2. **AC2 過。** 推翻＝不是 8×10、不是 delta 制、或缺「尚未切換／切換 Initiative」標記。
3. **AC3 過。** 推翻＝rows 1／3 任一舊文仍在，或誤動其他 owner row。
4. **AC4 不過。** 推翻＝任一污染符出現在非核准語境。現有 raw `grep -Fc` 卻要求全數 0，同條又允許逐處豁免；只要豁免真的存在，raw 輸出就不可能是 0。決議 §二另有「新規則文脈／角色表文脈」限定，raw grep 沒有編碼語境。`grep` 零命中的 rc=1 也未與輸出 0 分別定義。見 P1-31。
5. **AC5 不過。** 推翻＝三種腐爛自述在非核准位置殘留；但第三條同時要求 raw count 0、又允許表格合法數據逐處豁免，仍是互斥 oracle。見 P1-31。
6. **AC7 過。** 推翻＝八份 stage-rules 任一缺橫幅或數量不等於 8。
7. **AC6 過。** 推翻＝任一規則檔未 move、引用未對齊、tier-rules 未上線，或缺跨家族＋需求方 sign-off。

### W2B

1. **AC1 過。** 推翻＝封閉 mapping 任一舊入口仍被引用、任一新檔缺四段信封、或 review-prompt 未保留 schema 分工。
2. **AC2 不過。** 推翻＝W2A＋W2B merge result 的 contract universe delta 有任何一項無 disposition。方向正確，但比較基線沒釘：本 SHA 實跑為 59 gaps／guard rc=0、專測 33 passed；spec 沒保存 baseline universe 的排序集合或 hash，施工時無法判斷「消失／新增」相對哪一版。見 P1-32。
3. **AC3 過。** 推翻＝AGENTS／README 任一未導向 canonical 前兩節＋心智模型，或仍指向易漂活卡入口。
4. **AC4 過。** 推翻＝封閉五檔未按 mapping 處置或 CI 紅。

### W3′

1. **AC1 不過。** 推翻＝任一持久化 Log writer 未改留言，或 inventory 多／少一處。現況其實有六個持久化 `append_log_line` 呼叫點，另有 `open` 在 `render_issue_body` 直接產生初始 Log；此外 doctor 還有第七個非持久化 probe 呼叫。以「append_log_line 呼叫點全集＝六處」為 predicate，會同時漏掉 open writer、又被 doctor probe 推翻。固定留言的唯一識別、併發 append、容量上限與 rollback 也未定。見 P1-33。
2. **AC2 不過。** 推翻＝新舊任一路徑讀值不同、畸形／重複 JSON 未 fail closed、或 `--spec-dir` 尚存。雙讀與 row 10 有方向，但 fenced JSON interface 未定，與 W1 AC3 同一缺口。見 P1-30。
3. **AC3 不過。** 推翻＝任一現行 `wfcli doctor` consumer 在 W3′ 後失效。`移除或轉薄` 讓兩個外部結果都可自稱通過，卻只有薄殼能在現有 write-set 下維持 public contract。見 P1-28。
4. **AC4 過。** 推翻＝開卡 artifact 中任一可補救拒絕訊息仍無可跑命令，或不可補者未呈需求方；動態全集與同源 artifact 已要求開卡時釘字面。
5. **AC5 不過。** 推翻＝同 repo 真正祖先／子孫未相交，或不同 component 被誤殺，或同一實體路徑因大小寫／Unicode 形式漏判。現行已核准 writeset contract 明定 component sequence＋NFC＋casefold；W3′ 卻把「大小寫不正規化即不命中」列為正向測試，直接反向。別名表載入失敗又與未登記同樣按字面放行，會在已知 alias 無法載入時 fail-open。見 P1-34。
6. **AC6 不過。** 推翻＝raw inventory 少 item／content type／item ID／卡ID 任一欄。欄位形狀足夠，但把後置 W3′ 產物稱為前置 W1 oracle 的資料源，時序不可執行；見 P1-29。

### 基線總結

- 父卡 spec baseline 已釘完整 SHA；W3′ 動態數字、前張終態 SHA 與 artifact hash 的開卡時釘值規則成立。
- W2B contract universe 尚缺基線集合/hash；W1 raw inventory 尚缺當下 producer/hash；W2A grep 不是可接受豁免的機械 oracle。故不能以「開卡時再量」概括通過。

## R4 現行系統影響：不過

1. **W1 封 DraftIssue：條件式過。** 唯讀 inventory 現值為 212 items，其中 1 個 DraftIssue，與 spec 痛點一致。先由需求方裁定該 item，再封 creation；只有 raw count=0 才移除 legacy read，且 creation-closed／legacy-readable 分軸測試——這個處理順序不會因「取代舊路」本身被判衝突。未過的是 raw artifact 的可執行來源／基線，見 P1-29。
2. **W2B 動守衛：條件式過。** 要求在 W2A＋W2B merge result 跑 guard、逐項處置 universe delta、不得只改登記，能防止「修表讓綠」。本 SHA 自跑 guard rc=0（59 gaps）、專測 33 passed、citation 專測 16 passed；但缺 baseline universe，仍由 P1-32 阻斷。
3. **W3′ doctor：不過。** 現行 AGENTS 與多份 active contract 直接呼叫 `wfcli doctor`；若採 AC 允許的「移除」，W2B 剛發布的 contract 當場失效。最小安全路徑是保留相同 CLI 的薄相容 facade，內部委派 scripts／CI。見 P1-28。
4. **W3′ Log→留言 rollback：不過。** merge 後一旦有新事件只寫留言，單純 git revert 會恢復只讀 body 的舊 reader，使 revert 後看不到這段新事件；外部留言也不會被 git revert 撤回。因此「全部可 git revert」不足。需 rollout epoch／雙寫或可重放 backfill／回退 oracle，並定義固定留言唯一性與容量處置。見 P1-33。
5. **resource matcher：不過。** 大小寫不正規化會在目前 macOS case-insensitive 實體檔案上漏撞；alias registry 讀取失敗按字面放行也會漏已知 alias。見 P1-34。
6. **snapshot／cutover：邊界過、交棒不過。** §十之二已正確寫明 snapshot 只是對帳投影，不是 rollback；restore rehearsal、逐步 inverse、read-back oracle、刪 option 後只准 forward-repair 與需求方停損點，作為後續 Initiative 的 seed 粒度足夠。它**不是可直接執行的停機 spec**，後續開卡仍須展開正式步序。當前阻斷是 seed 尚未成為有五欄、唯一 owner、可查重的清單項，見 P1-27。

## Findings

### WF-REDESIGN1-P1-27

- severity: major
- blocking: true
- evidence: 父卡驗收與決議 §十之二要求本 Initiative 結案前建立切換 Initiative 清單項；`list-items.md:4-11` 只定義 W2A／W2B／W3′ 三項並稱切換項「屆時建立」；決議 `:94` 又禁止父卡做機械工作。
- disposition: 指定唯一 owner。最小方案是 W1 在清單機制上線後，同批建立 W2A／W2B／W3′／切換 Initiative 四個清單項；在 `list-items.md` 補切換項的出處、觀察句、查重、repo、提案者身分與 §十之二 scope link，W1 AC／父卡驗收以 issue URL＋不在 Project 為 oracle。W3′ 仍只實際升級前三項，不把 cutover 拉回本 Initiative。

### WF-REDESIGN1-P1-28

- severity: major
- blocking: true
- evidence: W2B `w2b.md:18-22` 要發布新 dispatch contract；現行 `AGENTS.md:21-27`、`templates/dispatch-package.md`、`templates/handoff-contract.md`、`docs/CONSUMER_CONFORMANCE.md` 均直接消費 `wfcli doctor`。W3′ `w3.md:19` 卻允許「移除或轉薄」，write-set 不含所有消費端。
- disposition: 在本 Initiative 固定選「轉薄」：保留 `wfcli doctor` 的名稱、旗標、rc 與輸出契約，委派至抽出的 scripts；加現行指令與新 CI job 的等價／round-trip 測試。若要完全移除，另擴 W3′ write-set、封閉列出全部 consumer、提供替代命令與遷移期，不得用二選一 AC。

### WF-REDESIGN1-P1-29

- severity: major
- blocking: true
- evidence: W1 `w1.md:15` 在 W1 開工／退場需要 raw inventory；W3′ `w3.md:22` 才實作同 artifact 並稱其為 W1 資料源，但硬依賴要求 W1 終態早於 W3′。W1 未列可於當下獨立產生 artifact 的 exact query、檔名或 hash。
- disposition: 把一次性唯讀 GraphQL inventory producer 放進 W1 前置並列 exact command、query version、排序規則、artifact path/hash、抓取 timestamp、三欄與 expected DraftIssue count；W3′ AC6 只承接「把既有 W1 artifact schema 產品化進 snapshot」，不得稱後置產物是先前 Gate 的來源。或調整卡序，但不得保留反向依賴。

### WF-REDESIGN1-P1-30

- severity: major
- blocking: true
- evidence: W1 `w1.md:19` 與 W3′ `w3.md:18` 都只寫 fenced JSON，未定同一 payload 的 schema version、sentinel、keys/types、唯一性、malformed／duplicate 行為與兩卡交接；現行卡面已另有 resource-claims fenced JSON，不能用「找到一個 JSON fence」作定位。
- disposition: 指定單一 schema owner（建議 W1 建 v1、W3′只擴充／消費），列完整 JSON schema＋專用 sentinel、版本升級規則與唯一區塊；tests 至少釘 writer→reader round-trip、legacy fallback、兩個同類區塊、malformed、unknown version、與既有資源 JSON 共存。

### WF-REDESIGN1-P1-31

- severity: major
- blocking: true
- evidence: W2A `w2a.md:19-20` 的 raw grep 預期 0，同時又允許取代引文／合法表格數據逐處豁免；決議 §二另限定數個 token 只在特定文脈算污染。raw count 無法同時表達 0 與豁免，零命中還會回 rc=1。
- disposition: 改成 allowlist-aware checker：逐命中輸出 file／line／context，核准例外以 versioned manifest 精確列 file＋穩定 anchor＋token，`unapproved_count=0` 才過；另有 injected negative control 證 checker 會紅。stdout、stderr、rc 分開釘。AC4／AC5 共用同一判準，不准靠交付報告人工扣數後自稱 raw grep=0。

### WF-REDESIGN1-P1-32

- severity: major
- blocking: true
- evidence: W2B `w2b.md:19` 要對 universe 消失／新增逐項 disposition，卻未指定比較基線。本 SHA 自跑 `contract_tool_reconcile.py --check` 為 rc=0、59 gaps，專測 33 passed；這些集合未被 artifact/hash 保存。
- disposition: 以本 spec baseline SHA 產生排序後 baseline universe artifact 並釘 SHA256；W2B 在 W2A＋W2B merge result 產生同 schema artifact，做 old/new set diff，每個 removed／added／changed symbol 均須 disposition；guard 與專測再對 merge result 執行。count 可作摘要，集合/hash 才是基線。

### WF-REDESIGN1-P1-33

- severity: major
- blocking: true
- evidence: W3′ `w3.md:17` 宣稱 `append_log_line` 呼叫點全集為六處。實碼另有 `doctor.py:2301` 的第七個非持久化 probe；`card.py:491-493` 的 open 初始 Log 又完全不經 `append_log_line`。因此 syntactic callsite inventory 會多一，persistent-writer inventory 會漏 open。新事件只存留言後，git revert 也無法讓舊 body reader看見它們。
- disposition: inventory predicate 改為「所有持久化 Log writer sink」而非函式名，封閉納入 open＋六個 append writer並排除具名 probe；每一 writer 都測只寫同一固定留言。定義 comment identity、exactly-one、併發 compare/read-back、容量 rollover。部署採 epoch＋雙讀，並提供回退時把 epoch 後留言事件重放回 body（或保留相容 reader）的可跑 rehearsal；rollback oracle 必證事件數／hash 不少一筆。

### WF-REDESIGN1-P1-34

- severity: major
- blocking: true
- evidence: `docs/WF_RESOURCE_WRITESET1.md:76-110` 已定 component sequence、NFC、casefold 與 prefix；W3′ `w3.md:21` 卻要求「大小寫不正規化即不命中」。同條又讓 alias registry 載入失敗按字面放行，會把「已知 alias 暫時讀不到」當成「不是 alias」。
- disposition: file matcher 直接引用既有 `K(r)`：去空／`.` component、NFC、casefold、component-prefix，保留 `templates` vs `templates2` 負例與大小寫／NFC 正例。DB alias 的「未登記」可按字面＋警示；**registry 載入失敗須 fail closed 拒絕 assign**，不得與未登記合併處置。測試分開釘 registered、unregistered、load-error 三格。

## self_run

- `git rev-parse HEAD`／`origin/main`：均為被審完整 SHA；worktree clean。
- Ruby Psych：五份 YAML 0 parse error；`replacement_rows` 全為 Array。
- 資源對照：現行 exact 1 組；目標 component-prefix 5 組 path pair，全部跨硬依賴序列，無同時飛行必要。
- Project #4 唯讀 inventory：212 items＝211 Issue＋1 DraftIssue；未用會跳過無卡ID者的 snapshot 代證。
- Log writer 實碼窮舉：六個持久化 `append_log_line` callsites＋一個 doctor probe＋一個 open 直接 writer。
- active doctor consumer：AGENTS、dispatch-package、handoff-contract、consumer-conformance 等均有命中。
- `contract_tool_reconcile.py --check` rc=0（59 gaps）；reconcile 專測 33 passed；canonical citation 專測 16 passed。
- 全程唯讀；未執行任何寫入型 wfcli，未修改 repo、未合併、未動 Project 欄位。

## 重審入口

先處理 P1-27～P1-34。下一輪 R1 可只做回歸；R2 需看到切換清單項唯一 owner／五欄內容與 doctor 相容交接；R3 需重跑每條 exact falsifier；R4 需實證 Log 留言 rollout／backout 與 alias load-error fail-closed。現有路徑相交不需消滅，只需維持目前的終態序列化。


## Comment 5473325618 · 2026-08-31T03:27:54Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（第九輪）

- 被審 SHA：`ce45a80f9dfe89d38e53d25a0b012e7bc8956003`
- 前八輪：issuecomment-5469108595、issuecomment-5469298925、issuecomment-5469364619、issuecomment-5469449938、issuecomment-5469611932、issuecomment-5470031961、issuecomment-5473075216、issuecomment-5473179838
- 裁決：**REQUEST_CHANGES；R1 通過結論維持，R2、R3、R4 不過**
- 查核者身分自述：Codex（OpenAI），session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T11:27:54+08:00`

## R1 回歸：維持過

- HEAD、`origin/main`、父卡 spec 基線均為完整被審 SHA；worktree clean。
- 五份 wave spec＋list-items frontmatter 均可由 Ruby Psych 解析；replacement rows 未漂移。
- 四波五卡、唯一 owner matrix、硬依賴與 tier 未被本輪修正破壞。
- 父卡 routing／重複欄位的現行舊值仍由 W1 P1-26 唯一承接；本輪不要求通道外先改。

## 第八輪 findings 重驗

- **P1-27：未全解。** W1 AC1b 已明列四清單項同批建立，五欄與 Project 排除 oracle 也已補；但 oracle 把「只升級前三項」的 actor 寫成 W3′，與 W1 驗證實際升級 W2A、各卡開工再升級自己的流程衝突。
- **P1-28：已解。** W3′ 已唯一選定薄相容 facade；`wfcli doctor` 名稱／旗標／rc／輸出契約保留，抽出腳本與 CI job 另做等價 round-trip。
- **P1-29：未全解。** 已把 producer 時序移到 W1，但所稱 exact command 仍不是可重現 producer。
- **P1-30：未全解。** 已指定 W1 為 v1 owner與六類測試，但 schema／sentinel／升版規則仍交給執行者現場發明。
- **P1-31：未全解。** AC4 已改 allowlist-aware；AC5 舊 raw-zero oracle與未宣告的 versioned manifest 仍在。
- **P1-32：未全解。** artifact 與 hash 真實存在、語意集合也正確；但所列 producer 無法重現該 byte hash，set identity 也未定。
- **P1-33：未全解。** 七個持久化 writer predicate 已修正；固定可編輯留言的 concurrency／rollover／回退仍無成立機制。
- **P1-34：未解。** 同一條 AC 前半已修正，後半仍逐字保留被撤回的 fail-open 與 case-sensitive 測試，形成雙答案。

## R2 射程與資源：不過

1. **既有非射程與跨波資源：過。** component-prefix 下仍有 W1↔W2B、W1↔W3′、W2B↔W3′ 的 tests／CLI／templates 路徑相交；全部由前張終態序列化，屬合理的 replacement 交接，不是 finding。
2. **P1-27 清單項 creation：部分過；升級 actor 不過。** W1 建四項與 Project 排除已封閉；但 `list-items.md:12` 寫成「W3′ 只實際升級前三項」，字面把 W2A／W2B 的升級也交給最後一張卡，與 W1 驗證及逐卡開工時序衝突。見 P1-27。
3. **P1-28 doctor contract 交接：過。** W2B 發布 contract、W3′ 保留薄 facade，順序與 write-set 可共存。
4. **P1-31 allowlist 資源：不過。** W2A 要新增「versioned manifest」，卻沒給 path；逐檔 write-set 也沒有可容納新 manifest 的宣告。拋棄式 checker 可在暫存區，versioned manifest 不可無居所。見 P1-31。
5. **新 §三之二 ownership：不過。** 決議新增「三層逐條清冊」後，W2A 只承接 stage-rules 編號；CLI 印出完整清單、③ 回應格式／template、④ 格數與值域對照、L0 措辭均沒有具名 wave AC。現行只有 family-level pitfalls gate，不是逐條注意事項。見 P1-35。

## R3 內容與非零資訊：不過

每條先列推翻條件，再列裁定。

### W0

- **AC1–2 過。** 推翻＝來源殘留／目的缺檔／內容出現非 frontmatter＋警語差異；move、零雙居所與 diff predicate 未變。

### W1

1. **前置不過。** 推翻＝artifact 不是 Project 全 items、缺 type／item ID／卡ID、或 count 非 0 卻移除 legacy read。`gh api graphql` 裸命令實跑 rc=0 但輸出整份 schema introspection，不是 Project inventory；spec 沒有 query、project/field ID、pagination loop、JSON schema與實際輸出 pipeline。見 P1-29。
2. **AC1 過。** 推翻＝收件五條件任一未成欄。
3. **AC1b 部分過。** 推翻＝四 URL 任一缺席或任一進入 Project #4；creation oracle 足夠，但共同 oracle 的升級 actor 錯置，見 P1-27。
4. **AC2 過。** 推翻＝直接 issue／DraftIssue 路徑仍成功，或補救命令不可跑。
5. **AC3 不過。** 推翻＝writer／reader 對同一 payload 不同判、畸形／重複／未知版未拒、或誤吃 resource JSON。測試類別正確，但 spec 未寫 sentinel literal、schema_version 值、三個 key 的實際名稱／型別／required／additional-properties 規則；W3′ 又引用「W1 定義之升版規則」，W1 沒有該規則。見 P1-30。
6. **AC4、AC5、AC5b 過。** 推翻分別為空 acceptance／舊旗標仍可用、撤銷規則提前生效、或三欄＋routing oracle 不成立；判準足夠。

### W2A

1. **AC1–3 過。** 推翻＝角色／順序、8×10＋delta＋未切換標記、rows 1／3 任一不符。
2. **AC4 不過。** 推翻＝任何非 allowlist 命中未使 checker 紅。新 predicate 正確，但 manifest 無 path/write-set，故不可執行。見 P1-31。
3. **AC5 不過。** AC4 明說 AC5 改用 checker；AC5 下一行仍要求三條 raw `grep -c` 預期 0，並同時允許表格豁免。兩個 oracle仍互斥。見 P1-31。
4. **AC6b 不過。** 推翻＝逐條清冊任一 runtime／template 消費端缺席；本 AC 只編號 stage-rules，未封閉 §三之二的其他 writer。見 P1-35。
5. **AC6、AC7 過。** 推翻＝規則檔 move／引用／sign-off 或八橫幅任一不成立。

### W2B

1. **AC1、AC3、AC4 過。** 推翻＝mapping／新信封／L0／封閉五檔或 CI 任一不符。
2. **AC2 不過。** 推翻＝baseline artifact 不能由宣告 producer逐 byte 重現，或同一 symbol 的 change 被 diff 漏掉。入庫檔 SHA 確為 `558c6ffe…`、86／54，且與現行輸出語意相等；但 spec 所列 `--format json` 直接輸出 SHA 是 `d01d02cc…`，byte compare 不同。它缺 canonicalization pipeline，亦未定 symbol identity（建議 `(kind,name)`）與 changed 的 canonical row 比法。見 P1-32。

### W3′

1. **AC1 不過。** 七 writer＋doctor probe 排除已正確。推翻＝並行 append 遺失任一事件、rollover 破壞 exactly-one、或 rollback 少一筆。GitHub comment update 沒有 compare-version 欄位；read-back 不是 compare-and-swap，存在兩 writer 各自讀回成功、最後一寫仍覆掉另一事件的 interleaving。卷二又會產生第二留言，與未限定 scope 的 exactly-one 衝突。見 P1-33。
2. **AC2 不過。** 推翻＝新舊讀路徑不等價或版本界線不定；它依賴尚未實際定義的 W1 v1 schema。見 P1-30。
3. **AC3 過。** 推翻＝薄 facade 的名稱／旗標／rc／輸出任一漂移，或 CI path 不等價；已具 round-trip。
4. **AC4 過。** 推翻＝開卡 artifact 中仍有可補拒絕訊息無 runnable remedy，或不可補者未上呈。
5. **AC5 不過。** 同一行先要求 NFC＋casefold＋component-prefix與 registry load fail-loud，後面又寫「載入失敗或未登記＝按字面」及「大小寫不正規化即不命中」。任一實作者選其中一半都能聲稱照 spec。見 P1-34。
6. **AC6 不過（受前置阻斷）。** schema 產品化的時序已正確，但 W1 raw artifact schema 尚未定義，無法判定「同 schema」。見 P1-29。

## R4 現行系統影響：不過

1. **DraftIssue 封路：條件式不過。** 現況仍是 212 items＝211 Issue＋1 DraftIssue；先裁定、creation closed、count=0 才退 legacy read 的順序安全。阻斷只在 producer 不是 exact/reproducible，不能拿錯資料宣告零存量。見 P1-29。
2. **W2B reconcile：條件式不過。** 54 與前輪 59 的差異接受為樹漂移；artifact 正是解法。當前缺口是 byte producer與 diff identity，不是 count。見 P1-32。
3. **doctor 抽出：過。** 薄 facade 消除了既有 AGENTS／template／consumer 斷裂；不得在執行期再改選移除。
4. **Log→留言：不過。** REST update 只收新 body；live GraphQL `UpdateIssueCommentInput` 也只有 `id`、`body`、`clientMutationId`，沒有 expected version。官方 REST 文件同樣未提供 compare token：[Update an issue comment](https://docs.github.com/en/rest/issues/comments#update-an-issue-comment)。因此 read-back 只能偵測部分 race，不能保證不 lost update。回退 rehearsal也未明訂必須在 writer epoch 啟用前先過。見 P1-33。
5. **resource matcher：不過。** casefold／NFC 與 load-error fail-closed 的正確方向已寫入，但同一 AC 的舊尾句仍授權 case-sensitive／load-error fail-open，現行 macOS 路徑與 DB alias 都會有漏撞方向。見 P1-34。
6. **切換 Initiative 交棒：部分過。** §十之二仍只作 seed，不授權現在 cutover，snapshot 仍明列不是 rollback；但前三項的升級 actor 需由 P1-27 更正。
7. **注意事項清冊啟用序：不過。** W2A 會先讓逐條 SOP 規則生效，CLI 支援若推定歸最後的 W3′，中間 W2B／W3′ 本身會在工具尚不會印／驗逐條清冊時受新規則約束；硬依賴在此放大空窗而非修復。見 P1-35。

## Findings

### WF-REDESIGN1-P1-27（延續）

- severity: major
- blocking: true
- evidence: `list-items.md:12` 的共同 oracle 寫「W3′ 只實際升級前三項」；但 W1 `w1.md:24` 明訂以本機制實際升級 W2A，header 又說各項在各自開工時升級。W3′ 不可能在最後才替已結案的 W2A／W2B 升級。
- disposition: 把 actor 改成「本 Initiative 只升級前三項」並逐項釘時點：W2A由W1驗證時升級；W2B於W2A終態後開工時升級；W3′於W2B終態後開工時升級；切換項維持list item且不進Project。四URL creation oracle保留。

### WF-REDESIGN1-P1-29（延續）

- severity: major
- blocking: true
- evidence: `w1.md:15` 把 bare `gh api graphql` 稱 exact command；實跑 rc=0 但回傳 GraphQL schema introspection，不含 Project items。query／variables／pagination／field lookup／輸出 schema 均只存在散文。
- disposition: 在 W1 spec 寫入真正可直接貼上執行的完整 producer（含 owner/project resolve、project ID、卡ID field ID、`pageInfo.endCursor` loop、Issue與DraftIssue union、排序與輸出）；JSON root 內放 query/schema version、source timestamp／project ID，另釘 exact SHA pipeline。以有效樣本＋DraftIssue負控實跑，不能只列命令名稱。

### WF-REDESIGN1-P1-30（延續）

- severity: major
- blocking: true
- evidence: `w1.md:20` 只要求未命名的「專用 sentinel」「keys/types 封閉定義」；沒有 literal sentinel、JSON instance/schema，也沒有升版規則。`w3.md:18` 卻引用不存在的 W1 升版規則。
- disposition: 規劃內直接列 v1 的 begin/end sentinel literal與完整 JSON Schema（`schema_version` const、三 key 的名稱／type／required、additionalProperties policy）；列 v1 reader 對 future version 的 fail-closed／migration規則。W3′只引用該具名 schema，六類 tests 保留。

### WF-REDESIGN1-P1-31（延續）

- severity: major
- blocking: true
- evidence: `w2a.md:19` 要 versioned manifest 但未命名 path、W2A 逐檔 resources 無該檔；`:20` 仍寫 raw grep count=0＋合法豁免，與上一行 `unapproved_count==0` 衝突。
- disposition: 指定 manifest 的 repo path並加入 W2A resource claim；AC5 三個 token改為 checker input，不再宣告 raw count=0。manifest逐 hit綁 token＋file＋穩定 anchor；negative control 在 temp fixture／worktree copy 執行，不污染 merge result。唯一 pass criterion只留 `unapproved_count==0`，stdout／stderr／rc分釘。

### WF-REDESIGN1-P1-32（延續）

- severity: major
- blocking: true
- evidence: artifact byte hash為 `558c6ffe…`；同 SHA 依 spec 命令重跑輸出 hash為 `d01d02cc…`、`cmp` 不同，但 parsed JSON相等且 canonical semantic hash同為 `d09f96bc…`。目前 hash不能由所列 producer重現。
- disposition: 二選一釘死：(A) 列 exact serialization/canonicalization pipeline並以它重生 artifact byte；或 (B) 明定 canonical JSON semantic hash演算法並改釘該 hash。set diff另定 identity=`(kind,name)`、added/removed依 key、changed＝同 key canonical row不同；baseline與merge artifact都帶source SHA與generator version。

### WF-REDESIGN1-P1-33（延續）

- severity: critical
- blocking: true
- evidence: `w3.md:17` 以「compare-and-append read-back」處理同一可編輯留言，但 REST/GraphQL update沒有expected-version/CAS輸入。反例 interleaving：A/B同讀v0；A寫v0+a並讀回成功；B再寫v0+b並讀回成功；final遺失a。rollover「卷二」同時使未限定的 exactly-one 失真。
- disposition: 先做 spike並選可證明的模型：若維持一則固定留言，就必須有可跨程序序列化的單一 writer/lease，並在無法取得時 fail closed；若平台沒有該原語，回需求方裁定改成 append-only 一事件一留言＋固定索引。定義 exactly-one 是每卡、每 epoch還是每 volume；rehearsal必在 writer epoch 啟用前通過，rollback必以事件ID集合＋內容hash證明不少一筆，不能只靠讀回剛寫的body。

### WF-REDESIGN1-P1-34（延續）

- severity: major
- blocking: true
- evidence: `w3.md:21` 同一 AC 同時寫「載入失敗 fail-loud／NFC＋casefold」與「載入失敗按字面／大小寫不正規化即不命中」。兩組結果互斥。
- disposition: 刪除舊尾句與舊 case-sensitive test。封閉三格：registered alias正規化命中；unregistered按字面＋warning；registry load/parse error在所有遠端寫入前拒絕 assign。file tests釘component boundary、NFC等價、casefold等價及真正非前綴負控。

### WF-REDESIGN1-P1-35

- severity: major
- blocking: true
- evidence: 決議 `:79-81` 新增逐條注意事項清冊、CLI列印、③回應、④格數/value檢查、PM產出與L0措辭；wave specs只有W2A AC6b承接編號。現行 `pitfalls.py`／43 tests是family-level roster，沒有逐條 note ID。W2B templates與W3 CLI均無對應AC；而「§三之二」heading實際放在§九之下。
- disposition: 先把決議 heading移到§三後並固定真正 anchor。指定端到端 owner與啟用順序：建議W2A同卡承接編號＋`pitfalls`逐條 roster／handoff gate（補CLI resources與tests，讓規則與writer同時生效）；W2B承接dispatch/delivery/report templates與L0措辭。若不願擴W2A，新增硬依賴前置卡，並在CLI落地前把條文標成「目標、尚未生效」；不得讓W2A先啟用無writer規則。

## self_run

- HEAD／origin/main／父卡基線皆為`ce45a80f…`；worktree clean。
- Ruby Psych：五份 wave spec＋list-items 0 parse error。
- `baseline-universe.json`：sha256 `558c6ffe…`、86 symbols／54 gaps；現行命令輸出語意相等但byte hash `d01d02cc…`。
- `gh api graphql`裸命令：rc=0，輸出schema introspection，非raw inventory。
- Project #4：212 items＝211 Issue＋1 DraftIssue；DraftIssue無卡ID仍被本次inventory看見。
- GraphQL live introspection：`UpdateIssueCommentInput`只有`clientMutationId`、`id`、`body`。
- reconcile專測33 passed；canonical citation專測16 passed；現行pitfalls專測43 passed（family-level基線）。
- component-prefix資源交集只出現在硬依賴分隔的wave pair；未發現需同飛的重疊。
- 全程唯讀；未執行寫入型wfcli、未修改repo、未合併、未動Project欄位。

## 重審入口

先處理P1-27、P1-29～P1-35；P1-28不必重做。下一輪R2只需回歸清單升級actor、manifest resource與§三之二owner；R3重跑exact producer/schema/oracle；R4須看到comment concurrency spike裁定、writer-epoch前rehearsal與matcher單一答案。54與59的count差異本身不再是finding。


## Comment 5473503726 · 2026-08-31T03:57:46Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（第十輪）

- 被審 SHA：`69457afaa79e48aec092c72cf3f00101900b1530`
- 前九輪：issuecomment-5469108595、issuecomment-5469298925、issuecomment-5469364619、issuecomment-5469449938、issuecomment-5469611932、issuecomment-5470031961、issuecomment-5473075216、issuecomment-5473179838、issuecomment-5473325618
- 裁決：**REQUEST_CHANGES；R1 通過結論維持，R2、R3、R4 不過**
- 查核者身分自述：Codex（OpenAI），session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T11:57:35+08:00`

## R1 前提回歸：過

1. HEAD、`origin/main`、父卡 spec 基線均為完整被審 SHA；worktree clean。
2. 五份 wave spec＋list-items frontmatter 均可由 Ruby Psych 解析；replacement rows 維持 W1=[12]、W2A=[1,3]、W3′=[10]，W0／W2B=[]。
3. 四波五卡、唯一 owner matrix、硬依賴 `W0→W1→W2A→W2B→W3′`、零 cpbl／零 cutover 與 T4／T3 級別均未漂移。
4. P1-27 的 actor／時點已一致：本 Initiative 升級前三項，W2A 在 W1 驗證時、W2B／W3′各在前張終態後開工時；切換項留清單且不進 Project。
5. brief 仍寫「Log→留言（6 寫入點）」而 W3′ 已封閉為 7 個 persistent sink；W3′ 的 `open 1＋append 6` 定義足以避免本輪前提失焦，故列非 blocking 文件漂移 P1-36，不推翻 R1。

## 第九輪 findings 重驗

- **P1-27：已解。** actor、四 URL oracle 與逐項升級時點一致。
- **P1-29：核心已解。** producer 原樣貼上實跑 rc=0，抓得 212 items＝211 Issue＋1 DraftIssue，root／排序／分頁／活負控均成立；「sha256 另檔」措辭與實際只印 stdout 的小落差另列 P1-37。
- **P1-30：未全解。** sentinel、欄名與範例已釘；但所稱 schema 仍是帶型別註記的 JSON instance，不是能交給 validator 的完整 JSON Schema。
- **P1-31：已解。** manifest path、write-set、唯一 pass criterion、fixture 負控與 AC5 共用 checker 已一致。
- **P1-32：已解。** canonicalization、identity、meta 與 hash 均可重建；實跑得到指定 `c1a1279324f2b5f40421eaa0408314a1afadae2c374c0c98782f66510af4bb68`。
- **P1-33：未全解。** append-only 方向消除了固定留言 lost update，但「實體每事件恰一則」與「讀端遇重複去重」仍互斥，rollback 也未釘 reader-first／writer-switch 的先後閘。
- **P1-34：已解。** file matcher 與 DB alias 三格皆為單一答案，load／parse error 在遠端寫入前 fail-loud。
- **P1-35：未全解。** 條文／機制／兩份範本已有 owner，但 PM 派審詞、結案報告與 L0 指定措辭仍未落到具名 AC；W3′ gate 也未逐字封閉這兩類 PM 產出。

## R2 射程與資源：不過

1. **各卡非射程：過。** W0 conduct、W1 intake/open、W2A rules、W2B templates/L0、W3′ CLI 的邊界清楚；cutover、Project 欄位與 cpbl 全移交切換 Initiative。
2. **資源交集：過。** component-prefix 下仍有 W1↔W2B 的 `cli/tests`、W1↔W3′ 的 `cli/src`／`cli/tests`、W2B↔W3′ 的 `templates`／reconcile test 交集；全部由硬依賴終態序列化。這些是 replacement 交接，不是要求消滅的衝突。
3. **P1-27 清單項：過。** 四項 creation、三項 upgrade、切換項不升級均有唯一 actor 與時點。
4. **P1-31 manifest：過。** `scripts/pollution-allowlist.json` 與 checker 均已進 W2A write-set，沒有無主資源。
5. **P1-35 端到端 owner：不過。** 決議 §三之二要求 PM 派審詞／結案報告同罩，並指定 L0 逐字措辭；W2B AC0 只列派工包／交付報告，AC3 也只寫一般 L0 入口。W3′ AC6b 的「handoff gate」未明列 PM 兩類產出。因此仍有要求存在但沒有可判 owner／oracle 的縫隙。見 P1-35。

## R3 內容、非零資訊與基線：不過

每組先列推翻條件，再列裁定。

### W0

- **AC1–2：過。** 推翻＝來源仍在、目的缺檔、雙居所，或 move 前後有 frontmatter／警語以外的內容差異；現有 move＋diff＋`git log --follow` oracle 足夠。

### W1

- **前置：過。** 推翻＝查詢漏 Project item、漏 DraftIssue、分頁不全、排序不定或 artifact 非零卻移除 legacy reader；producer 實跑涵蓋 212 items 且含活 DraftIssue 負控。hash「另檔」文字小落差見 P1-37。
- **AC1、1b、2：過。** 推翻＝五條件缺欄、四 URL 任一不存在／進 Project、舊建卡路徑仍通或補救命令不可跑。
- **AC3：不過。** 推翻＝兩個實作者對 missing nested key、nested extra key、空陣列或未知值作出不同判定。`w1.md:33-40` 的 code block 是範例 instance；沒有 `type/properties/items/required/const/enum` 等 JSON Schema keyword，也未封閉巢狀 object 的 additional-properties policy。見 P1-30。
- **AC4、5、5b：過。** 推翻＝空 acceptance／舊旗標仍可用、撤銷規則提前生效，或 title／Project title／功能／routing round-trip 不成立；判準足夠。

### W2A

- **AC1–3、6、7：過。** 推翻＝角色／節序、8×10＋delta＋未切換標記、rows 1／3、move／引用／sign-off、八份過渡橫幅任一不符。
- **AC4–5：過。** 推翻＝任何未核准 token 未增加 `unapproved_count`、負控不紅，或人工扣數仍能過；manifest、fixture 與唯一判準已封閉。
- **AC6b：本卡局部過、端到端不過。** W2A 已把規則標成 W3′ 前不生效；但完整消費面仍受 P1-35 阻斷。

### W2B

- **AC0：不過。** 推翻＝§三之二要求的任一 PM 產出沒有清冊欄；目前只釘派工包／交付報告，漏派審詞／結案報告。見 P1-35。
- **AC1、3、4：過。** 推翻＝舊→新 mapping、五份新範本、review-prompt 分工、L0 或封閉五檔任一不成立。
- **AC2：過。** 推翻＝artifact byte hash不能重建，或同 key row change 被漏；實跑 raw producer後依 `(kind,name)` 排序、meta 與 canonical dump 可逐 byte 重建 `c1a127…`，identity／changed 規則已釘。

### W3′

- **AC1：不過。** 推翻＝retry／並行造成兩則相同 op id、同 op id 不同 hash無裁定，或 rollback 後舊 reader看不到 epoch 後事件。新增留言 API 沒有 server-side idempotency／conditional-create 欄；body 冪等鍵只能讓讀端做 logical dedupe，不能保證實體 comment count 恰一。見 P1-33。
- **AC2：不過（受 P1-30 阻斷）。** sentinel 與版本界線已定，但「消費 W1 schema」仍沒有可執行 schema 作共同 oracle。
- **AC3–5、6：過。** 推翻＝doctor facade 漂 contract、拒絕訊息無 runnable remedy、matcher 四類測試／alias 三格任一不成立，或 snapshot schema 不承接 W1 raw inventory；判準足夠。
- **AC6b：不過。** 推翻＝PM 派審／結案輸出繞過逐條 gate或 L0 沒有指定措辭；現文只寫一般 handoff gate，未封閉全部消費面。見 P1-35。

## R4 現行系統影響：不過

1. **W1 封 DraftIssue：過。** 唯一 DraftIssue 先經需求方裁定；creation closure 與 legacy read retirement 分軸；只有 raw artifact 證 count=0 才退 reader。實跑 producer看得到該負控，沒有「查不到所以當零」的路徑。
2. **W2B CONTRACT_TOOL_RECONCILE：過。** baseline 是集合／hash而非可漂 count；merge result 要做 added／removed／changed 逐 symbol disposition，再跑 `--check` 與 33 專測，不能只改登記。
3. **doctor 抽出：過。** 保留名稱、旗標、rc、輸出，reader-facing contract 不斷；新 CI job 有等價 round-trip。
4. **Log→留言 rollout／backout：不過。** 一事件一留言已避免固定 comment 的覆寫遺失，但 physical exactly-once 無平台原語；且「epoch＋雙讀」沒有明定先上 dual reader、rehearsal 通過後才切 writer。若整個 W3′ git revert，舊 reader仍不讀 epoch 後留言。見 P1-33。
5. **resource matcher：過。** component boundary／NFC／casefold／非前綴負控與 registered／unregistered／load-error 三格已封閉；錯誤發生在任何遠端 assign 寫入前。
6. **逐條清冊啟用序：不過。** W2A 的 inactive marker已封住「規則先上、writer未上」；但 W3′ 啟用時尚缺 PM 派審／結案與 L0 的完整 gate/oracle。見 P1-35。
7. **cutover／cpbl：過。** 本 Initiative 無 Project 語彙切換、無 cpbl write-set；snapshot仍只作對帳，不冒充 rollback。切換 Initiative 清單項已在 W1 同批建立且不會回流本 Initiative。

## 級別與能力層級推導：過

- **W0 T4：成立。** conduct 是規則紅線；即使可 git revert，仍按最高風險軸取 T4。主力型執行＋需求方 sign-off／獨立搬移完整性查核成立。
- **W1 T3：成立。** 改唯一寫入通道與 card contract，public contract 至少 T3；主力型執行＋獨立實證查核成立。
- **W2A T4：成立。** canonical／stage-rules 是明文紅線；高階型＋跨家族與需求方 sign-off成立。
- **W2B T3：成立。** contract templates／L0 是 public contract；主力型＋獨立查核成立。
- **W3′ T3：成立。** 唯一寫入通道、audit event、schema reader與資源互斥行為均為 public contract；可回復性不把它降到 T2，主力型＋獨立查核成立。

## Findings

### WF-REDESIGN1-P1-30（延續）

- severity: major
- blocking: true
- evidence: `w1.md:33-40` 宣稱完整 schema，但 code block只有一個範例 JSON object；例如無法機械判定 `stage_plan` item 缺 `goal`、`tier_basis` 多未知 key、空 `list_convergence`、或 `schema_version` 型別錯誤是否拒收。
- disposition: 直接內嵌或具名引用一份真正的 JSON Schema（建議 draft 2020-12）：root `required` 應明列 `schema_version`＋三 payload keys，`schema_version.const="1"`；所有巢狀 object 逐層列 `type/properties/required/additionalProperties`；array 列 `items`，stage／claim 用 enum，並裁定空陣列與重複 stage／issue 的規則。writer／reader tests 對同一 schema validator 跑正負 fixture，W3′只消費該 schema。

### WF-REDESIGN1-P1-33（延續）

- severity: critical
- blocking: true
- evidence: `w3.md:17` 同時宣稱「每事件恰一則」與「讀端以冪等鍵去重重複」。GitHub live GraphQL `AddCommentInput` 只有 `clientMutationId/subjectId/body`，REST create comment也沒有 documented idempotency key或 conditional create；兩 writer同時查無 op id後都 POST、或成功回應遺失後 retry，均可產兩則實體留言。若同 op id 出現不同 hash，現 spec亦無 fail rule。官方 endpoint：https://docs.github.com/en/rest/issues/comments#create-an-issue-comment
- disposition: 接受平台實際能保證的形狀：**實體 delivery＝at-least-once；邏輯事件＝exactly-once**。op id 必在邏輯操作開始時產生並跨 retry 重用；writer於 retry 前重掃；reader按 op id分組，同 hash collapse＋warning，不同 hash視為 corruption並 fail-closed；索引只由 canonical deduped event set重建。部署釘兩階段：先上 dual reader並完成 backout rehearsal，再切 writer epoch；回退只關新 writer且保留 dual reader，或明列把 epoch 後事件 materialize 回 body 的可跑步驟。若需求方堅持「實體恰一則」，則需另加跨程序 single-writer／lease，無 lease即拒寫，不能靠讀端去重宣稱達標。

### WF-REDESIGN1-P1-35（延續）

- severity: major
- blocking: true
- evidence: 決議 §三之二明定「PM 產出（派審詞／結案報告）同罩」及 L0 指定句；`w2b.md:18` 只要求派工包／交付報告，`:21` 未釘指定 L0 句；`w3.md:25` 只寫一般 handoff gate，沒有列 PM 兩類輸出及其拒收 oracle。
- disposition: W2B AC0 擴成實際四類輸出面：dispatch package、delivery report、review dispatch、closeout report（若結案沿用某既有檔，逐字指定該 mapping），全含編號三值清冊；AC3 釘決議的 L0 字句。W3′ AC6b 明列 gate 消費者與 pass/fail：ID 集合須與本次 CLI 印出的三層集合相等；缺／多 ID、值域外、`不適用`缺原因、`發現`缺處置均拒收；PM 派審與結案輸出也走同一 validator。保留 W2A 的未生效 marker，直到這些 tests 全綠才啟用。

### WF-REDESIGN1-P1-36

- severity: minor
- blocking: false
- evidence: brief 拆卡表仍寫 W3′「Log→留言（6 寫入點）」；`w3.md:17` 的 persistent sink封閉全集是 open初始Log＋六 append＝7。
- disposition: brief 改成「7 persistent sinks（open 1＋append 6）」或移除數字並引用 W3′ inventory；避免下一次派工沿 brief 少算 open。

### WF-REDESIGN1-P1-37

- severity: minor
- blocking: false
- evidence: `w1.md:15` 說 sha256「另檔」，但貼上即跑命令的 `shasum -a 256 "$OUT"` 只輸出 stdout，沒有建立 sidecar。
- disposition: 二選一釘死：改文為「hash stdout逐字釘入卡面」，或命令用 `shasum -a 256 "$OUT" | tee "$OUT.sha256"` 並把 sidecar納入交付 oracle。

## self_run

- HEAD／origin/main／父卡基線皆為完整 `69457af…`；worktree clean；diff check綠。
- Ruby Psych：五份 wave spec＋list-items 0 parse error。
- W1 exact producer rc=0：212 rows＝211 Issue＋1 DraftIssue；分頁、item-id排序與 root metadata成立。
- baseline artifact：86 symbols／54 gaps；raw command輸出經宣告 canonicalization＋meta重建後 byte hash為 `c1a127…`。
- live GraphQL introspection：`AddCommentInput` 無 idempotency／expected-version欄；只有 `clientMutationId`、`subjectId`、`body`。
- reconcile／canonical citation／現行 pitfalls tests 合跑：92 passed；其中 reconcile 33、citation 16，pitfalls仍是執行前 family-level baseline。
- component-prefix資源交集只存在於硬依賴分隔的 wave pair；未發現需要同時飛的搶檔。
- 全程唯讀；未執行寫入型 wfcli、未修改 repo、未合併、未動 Project 欄位。

## 重審入口

先處理 blocking 的 P1-30、P1-33、P1-35；P1-36／P1-37 可同批但不單獨阻擋。下一輪 R1只做回歸；R2只需重驗清冊四類輸出 owner，R3重驗真正 JSON Schema與 checklist validator，R4重驗 logical exactly-once＋reader-first writer-switch／backout rehearsal。P1-27、P1-29、P1-31、P1-32、P1-34無需重做。


## Comment 5473595529 · 2026-08-31T04:11:54Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（第十一輪）

- 被審 SHA：`f7149d249acffbf141a39c172b6e6ad9a703ef2c`
- 前十輪：issuecomment-5469108595、issuecomment-5469298925、issuecomment-5469364619、issuecomment-5469449938、issuecomment-5469611932、issuecomment-5470031961、issuecomment-5473075216、issuecomment-5473179838、issuecomment-5473325618、issuecomment-5473503726
- 裁決：**REQUEST_CHANGES；R1 通過結論維持，R2 過，R3、R4 不過**
- 查核者身分自述：Codex（OpenAI），session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T12:11:41+08:00`

## R1 前提回歸：過

1. HEAD、`origin/main`、父卡 spec 基線均為完整被審 SHA；worktree clean。
2. 五份 wave spec＋list-items frontmatter 均可由 Ruby Psych 解析；replacement rows 維持 W1=[12]、W2A=[1,3]、W3′=[10]，W0／W2B=[]。
3. 四波五卡、唯一 owner matrix、硬依賴 `W0→W1→W2A→W2B→W3′`、零 cpbl／零 cutover 與 T4／T3 級別未漂移。
4. brief 已同步為 7 persistent sinks＝open 1＋append 6；P1-36 的前提落差消失。

## 第十輪 findings 重驗

- **P1-30：未全解。** 真正的 draft 2020-12 schema、root／nested required、const、enum、additionalProperties與重複值附加規則均已補；但 `issue_url` pattern 仍接受 repo 首頁等非 issue URL。
- **P1-33：未全解。** 保證已正確改為 physical at-least-once／logical exactly-once，dedupe／corruption／索引與 reader-first順序也已補；但 retry identity 未跨程序故障邊界釘死，writer-switch亦未形成可單獨回退的具體發布單元。
- **P1-35：未全解。** 四類輸出、closeout template、L0指定句與 PM 共用 validator已補；但 validator只要求 ID「集合」相等，重複同一 ID 不會造成缺／多 ID，仍可違反決議的格數不變量。
- **P1-36：已解。** brief 已明列 open 1＋append 6。
- **P1-37：已解。** exact producer 實跑建立 `$OUT.sha256` sidecar，內容與 stdout一致。

## R2 射程、owner 與資源：過

1. **非射程：過。** W0 conduct、W1 intake/open、W2A rules、W2B templates/L0、W3′ CLI 邊界未漂移；cutover、Project欄位與cpbl仍全歸切換 Initiative。
2. **P1-35 owner：過。** W2A擁有 inactive條文與編號；W2B AC0／AC3擁有四類輸出範本、closeout report與L0句；W3′ AC6b擁有列印、roster、validator與啟用 gate。沒有「有要求無 owner」的縫隙。
3. **component-prefix資源交集：過。** W1↔W2B 的 `cli/tests`、W1↔W3′ 的 `cli/src`／`cli/tests`、W2A↔W3′ 的 `scripts`、W2B↔W3′ 的 `templates`／reconcile test均有交集；全部由前張終態才開後張的硬依賴序列化，屬 replacement交接而非搶同一執行期。
4. **新 closeout file：過。** `templates/` broad claim涵蓋 `templates/closeout-report.md`；其新增 contract symbol另由W2B AC2的added-set disposition承接。

## R3 內容、非零資訊與基線：不過

每組先列推翻條件，再列裁定。

### W0

- **AC1–2：過。** 推翻＝來源仍在、目的缺檔、雙居所，或move前後有frontmatter／警語以外差異；move＋diff＋`git log --follow` oracle足夠。

### W1

- **前置：過。** 推翻＝漏Project item／DraftIssue、分頁不全、排序不定或sidecar缺席；exact producer實跑rc=0，212 rows＝211 Issue＋1 DraftIssue，並生成可核hash sidecar。
- **AC1、1b、2：過。** 推翻＝五條件缺欄、四URL任一不存在／進Project、舊建卡路徑仍通或補救命令不可跑。
- **AC3：不過。** schema本體已通過Draft202012 metaschema與正負fixture；但推翻條件「非issue URL仍通」成立。實跑 `https://github.com/ruan6047/ai-workflow` 可通過目前 `^https://github\.com/` pattern，故 `list_convergence.issue_url` 可不指向任何清單項。見P1-30。
- **AC4、5、5b：過。** 推翻＝空acceptance／舊旗標仍可用、撤銷規則提前生效，或title／Project title／功能／routing round-trip不成立；判準足夠。

### W2A

- **AC1–7：過。** 角色／節序、8×10＋delta＋未切換標記、rows 1／3、allowlist checker、三個腐爛自述、清冊inactive標記、八份橫幅、move／引用／sign-off均有可判oracle；P1-31 manifest與checker write-set仍完整。

### W2B

- **AC0：過。** 四類輸出面與closeout七段報告有具名檔、清冊欄與存在性falsifier。
- **AC1、3、4：過。** 舊→新mapping、新範本、review-prompt分工、L0指定句與封閉五檔均可判。
- **AC2：過。** baseline artifact仍為86 symbols／54 gaps、hash `c1a127…`；identity與canonical row diff已釘。現行`--check` rc=0（59個已登記缺口）不冒充baseline count，merge result仍須逐symbol disposition。

### W3′

- **AC1：不過。** 同程序內retry可重用op id；但推翻條件「POST成功後程序中止，再啟命令仍被識別為同一邏輯事件」未被封住。現行起點只有amend在每次invocation重新產生8位op id；spec未定immutable event envelope何時持久化／如何傳入下一次invocation，也未要求payload／timestamp／hash跨retry凍結。另「關新writer保留dual reader」未指定feature flag或獨立commit/release boundary；整批revert仍會一併移除dual reader。見P1-33。
- **AC2：不過（受P1-30阻斷）。** sentinel、版本與結構schema均成立；但reader共用的URL語意validator仍接受非issue URL。
- **AC3–5、6：過。** doctor薄facade、拒絕訊息、resource matcher三行為與snapshot承接均有唯一oracle。
- **AC6b：不過。** 推翻條件「清冊多一個重複ID仍通過」成立：required IDs `{A,B}`、rows `[A,A,B]` 的set仍等於`{A,B}`，且不屬缺ID／多ID值。決議§三之二要求格數不符即退回，現五fixture未涵蓋duplicate row。見P1-35。

## R4 現行系統影響：不過

1. **W1封DraftIssue：過。** producer仍看得到唯一活負控；先裁定、封creation、inventory為0才退legacy reader的順序安全。
2. **W2B CONTRACT_TOOL_RECONCILE：過。** baseline集合／hash與merge-result added／removed／changed disposition未漂移；33專測及`--check`仍是合併結果gate。
3. **doctor抽出：過。** 名稱、旗標、rc、輸出與consumer-facing contract保留，CI job有等價round-trip。
4. **Log→留言 rollout/backout：不過。** at-least-once模型方向正確，且same-id same-hash與corruption已封閉；但process-death後的retry token沒有可恢復通道，可能以新op id重送同一邏輯事件。兩階段只有順序，沒有可單獨關writer而保留reader的實作邊界；materialize分支又寫「依明列步驟」但沒有列步驟。見P1-33。
5. **resource matcher：過。** component boundary／NFC／casefold／非前綴負控與registered／unregistered／load-error三格維持單一答案，遠端寫入前fail-loud。
6. **逐條清冊啟用：不過。** owner與啟用時點已正確；但set equality漏duplicate row，使「每條恰一格」無法保證，PM派審／結案同樣受影響。見P1-35。
7. **cutover／cpbl：過。** 本Initiative仍無Project語彙切換、無cpbl write-set；snapshot不冒充rollback，切換清單項不回流本Initiative。

## 級別與能力層級推導：過

- **W0 T4：成立。** conduct是規則紅線；可逆性不能壓過最高風險軸。主力型執行＋需求方sign-off／獨立完整性查核成立。
- **W1 T3：成立。** 唯一寫入通道與card contract是public contract；主力型＋獨立實證成立。
- **W2A T4：成立。** canonical／stage-rules是明文紅線；高階型＋跨家族與需求方sign-off成立。
- **W2B T3：成立。** templates／L0含public contract；主力型＋獨立查核成立。
- **W3′ T3：成立。** audit event、schema reader、resource互斥與唯一寫入通道均是public contract；可回復性不構成降至T2的理由，主力型＋獨立查核成立。

## Findings

### WF-REDESIGN1-P1-30（延續）

- severity: major
- blocking: true
- evidence: `w1.md:49-52` 對 `issue_url` 只要求字串以 `https://github.com/` 開頭；Draft202012Validator實跑顯示repo首頁 `https://github.com/ruan6047/ai-workflow` 合法。該值不是issue URL，不能證明清單收斂到哪個list item。
- disposition: 把pattern釘到實際issue路徑，例如 `^https://github\.com/[^/]+/[^/]+/issues/[1-9][0-9]*$`；若允許trailing slash、query或comment fragment，先逐項裁定再寫入pattern。補repo首頁、issues列表頁、PR URL、零／負issue number四類拒收fixture；有效issue URL與允許的fragment另作正例。

### WF-REDESIGN1-P1-33（延續）

- severity: major
- blocking: true
- evidence: `w3.md:17` 要求op id跨retry重用，但沒有定義跨process retry如何取得同一id／同一event hash；現行`amend_cmd.py:939`每次invocation重新執行`uuid.uuid4().hex[:8]`。反例：POST已建立留言、response遺失後程序退出；使用者重跑命令產生新op id，reader會把它視為第二個合法邏輯事件。該行又允許「關writer保留reader」或materialize，但沒有feature flag／獨立release boundary，所稱明列materialize步驟實際不存在。
- disposition: 在第一次遠端寫入前凍結immutable event envelope（至少card id、128-bit UUID op id、event payload、timestamp、hash），並選一個跨process恢復通道：例如新增既有動詞旗標`--op-id`／`--event-envelope`，先把token印出並讓失敗訊息給可跑retry命令；或建立可恢復pending journal。測試必模擬「server已create、client timeout、process restart、同token重跑」，並證logical event仍一筆；同op id重算出不同hash必紅。部署兩階段須是獨立可回退commit/release或明文feature flag：phase 2關閉後phase 1 dual reader仍在。materialize若保留為第二路，須真的列出command／順序／read-back oracle；否則刪除該未定分支。

### WF-REDESIGN1-P1-35（延續）

- severity: major
- blocking: true
- evidence: 決議§三之二要求「格數不符＝退回」；`w3.md:25` 改用ID set相等並列缺／多ID，但set會消去duplicate。`expected={A,B}`、responses=`[A,A,B]`同時滿足set equality且沒有額外ID值，卻有三格對兩條注意事項。
- disposition: validator改驗bijection而非只驗set：每個expected ID恰一列、每列ID必屬expected、`len(rows)==len(expected)`，duplicate ID獨立拒收；保留missing／unexpected／值域／原因／處置五格，新增duplicate fixture成第六格。PM派審與結案輸出同跑此cardinality oracle，tests全綠後才解除W2A inactive標記。

## self_run

- HEAD／origin/main／父卡基線皆為完整`f7149d2…`；worktree clean；diff check綠。
- Ruby Psych：五份wave spec＋list-items 0 parse error。
- W1 schema：`json.loads`及Draft202012 metaschema通過；valid-min通過，missing root／bad version／bad stage／empty stage／nested extra均拒收；repo首頁反例仍通過。
- W1 exact producer rc=0：212 rows＝211 Issue＋1 DraftIssue；sidecar建立且hash與stdout一致。
- baseline artifact hash=`c1a127…`、86／54；現行reconcile `--check` rc=0（59個已登記缺口）。
- reconcile／canonical citation／現行pitfalls tests合跑：92 passed。
- component-prefix交集只存在於硬依賴分隔的wave pair；未發現需同時飛的搶檔。
- 全程唯讀；未執行寫入型wfcli、未修改repo、未合併、未動Project欄位。

## 重審入口

先處理blocking的P1-30、P1-33、P1-35。下一輪R1只做回歸、R2只需確認新增flag／journal或release boundary的資源owner；R3重驗issue URL負例、跨process retry與duplicate roster fixture；R4重驗reader-first後writer可單獨回退。P1-36、P1-37無需重做。


## Comment 5473680383 · 2026-08-31T04:22:10Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（第十二輪）

- 被審 SHA：`4d0785c4dcb5bc08fb74392cbf1d88ffeed94953`
- 前十一輪迄：issuecomment-5473595529
- 裁決：**REQUEST_CHANGES；R1、R2 通過結論維持，R3、R4 不過**
- 查核者身分自述：Codex（OpenAI），session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T12:22:00+08:00`

## R1 前提回歸：過

- HEAD、`origin/main`、父卡 spec 基線均為完整被審 SHA；worktree clean。
- 五份 wave spec＋list-items frontmatter可解析，replacement rows、四波五卡、唯一owner、硬依賴與級別未漂移。

## R2 射程、owner與資源回歸：過

- 非射程與切換 Initiative 邊界未漂移；本 Initiative仍零cpbl、零Project語彙切換。
- P1-33新增既有動詞旗標、CLI reader/writer與tests均落在W3′的`cli/src/`、`cli/tests/` broad claim；沒有新增無主write-set。
- 既有component-prefix交集仍全由`W0→W1→W2A→W2B→W3′`終態序列化。

## 第十一輪 findings 重驗

- **P1-30：已解。** schema pattern已釘唯一issue URL正規形；repo首頁、issues列表、PR、0／負數、trailing slash、query、fragment均拒收，合法`/issues/177`通過。
- **P1-33：未全解。** immutable envelope欄位、128-bit op id、重啟測試、兩階段commit／flag與materialize刪除都已補；但跨程序retry實際只攜帶`--op-id`，未攜帶或恢復原timestamp／payload／hash，無法保證重建同一envelope。hash canonicalization與feature flag literal也未釘。
- **P1-35：已解。** 比對已由set改為逐格序列與格數不變量；duplicate ID是獨立第六種拒收並與PM兩類輸出共用validator。

## R3 內容、非零資訊與基線：不過

每組先列推翻條件，再列裁定。

### W0

- **AC1–2：過。** 推翻＝來源殘留、目的缺檔、雙居所或move前後有非frontmatter／警語差異；既有oracle足夠。

### W1

- **前置與AC1、1b、2、4、5、5b：過。** exact producer本輪再跑rc=0，212 rows＝211 Issue＋1 DraftIssue且sidecar存在；其餘收件、清單、唯一開卡路徑、acceptance、撤銷與round-trip判準未漂移。
- **AC3：過。** Draft202012 metaschema通過；四負一正與額外trailing slash／query／fragment fixture均符合唯一正規形。writer／reader共用validator、nested required與duplicate附加規則仍封閉。

### W2A

- **AC1–7：過。** 角色／節序、8×10＋delta、rows 1／3、allowlist checker、腐爛自述、inactive清冊、八橫幅、move／引用／sign-off的falsifier未漂移；W2A內部未見新矛盾。

### W2B

- **AC0–4：過。** 四類清冊範本、closeout、mapping、baseline set/hash、L0指定句與CI oracle未漂移；artifact hash仍為`c1a127…`，現行reconcile `--check` rc=0。

### W3′

- **AC1：不過。** 推翻條件「ambiguous create後第一次重掃暫時看不到comment，重啟retry仍建立same-id／same-hash duplicate」未被封住。spec凍結的envelope含timestamp／payload／hash，但retry命令只帶op id；第二程序無來源可重建第一次的timestamp與hash。若重算，之後reader會看到same id／different hash並依spec fail-closed，而不是logical collapse。另event hash的演算法／欄位domain／canonical bytes未定，所稱「明文feature flag」也沒有literal、default與off時writer行為。見P1-33。
- **AC2–6：過。** card schema、doctor facade、拒絕訊息、resource matcher與snapshot判準未漂移。
- **AC6b：過。** 逐格序列相等＋cardinality會拒`[A,A,B]`對`[A,B]`；missing／unexpected／duplicate／值域／原因／處置六類均有fixture，PM派審與結案走同validator。

## R4 現行系統影響：不過

1. **DraftIssue封路：過。** 先裁定、封creation、inventory為0才退legacy reader；活負控仍可見。
2. **CONTRACT_TOOL_RECONCILE：過。** baseline集合／hash與merge-result逐symbol disposition未漂移；count只作摘要。
3. **doctor抽出：過。** 薄facade保留consumer contract與等價round-trip。
4. **Log→留言rollout／backout：不過。** phase順序與「關phase 2保留phase 1」方向正確；但`--op-id`不是完整retry envelope，visibility lag反例會把at-least-once duplicate變成corruption。feature flag未命名，未釘off＝legacy body writer仍啟用／dual reader仍啟用，故rollback read/write路徑還不能直接執行。見P1-33。
5. **resource matcher：過。** component／NFC／casefold與alias三格仍為單一答案，遠端寫入前fail-loud。
6. **逐條清冊：過。** owner、validator、格數、duplicate與啟用時點已封閉。
7. **cutover／cpbl：過。** 解耦與snapshot非rollback定位未漂移。

## 級別與能力層級推導：過

- W0／W2A的T4紅線與W1／W2B／W3′的T3 public-contract推導均仍依「風險、影響範圍、可逆性取最高者」；能力層級與獨立／跨家族要求未變，全部成立。

## Findings

### WF-REDESIGN1-P1-33（延續）

- severity: major
- blocking: true
- evidence: `w3.md:17` 定義第一次嘗試凍結`card id＋op id＋payload＋timestamp＋hash`，跨程序retry卻只傳`--op-id`。反例：attempt A以`(id=X,t=T1,p=P,h=H1)`成功create但response遺失；restart後第一次list因visibility lag回空，attempt B只有X，重算成`T2/H2`並create；稍後reader見同X、H1≠H2，依同一AC判corruption。此結果不滿足「at-least-once physical／exactly-once logical」。同條未定hash是SHA-256或其他算法、hash涵蓋哪些欄與canonical serialization；「明文feature flag」也沒有實際名稱／default／off-state oracle。
- disposition: 二選一使完整envelope跨程序可恢復：（A）retry token改攜帶versioned canonical envelope（例如`--event-envelope <base64url-json>`或`--event-file`），包含原timestamp／payload／hash；（B）第一次remote write前把envelope持久化到可由op id讀回的pending store，成功read-back後才清。`--op-id`可保留作lookup key，但不能是唯一資料。另釘`event-v1` canonicalization：建議SHA-256 over UTF-8 canonical JSON、sorted keys、固定separators、明列hash排除自身且timestamp是否納入；writer／reader共用。新增visibility-lag fixture：ambiguous create後第一次重掃回空、第二次create仍須same hash，最後collapse成一個logical event。feature flag給literal與狀態表：phase 1 default off＝legacy body writer on＋dual reader on；phase 2 on＝comment writer on＋body writer frozen；rollback off後恢復legacy writer且dual reader不退。兩commit SHA與不得squash／可單獨revert oracle一併釘入。

## self_run

- HEAD／origin/main／父卡基線皆為完整`4d0785c…`；worktree clean；diff check綠。
- Ruby Psych：五份wave spec＋list-items 0 parse error。
- W1 schema：Draft202012 metaschema通過；repo首頁／issues列表／PR／0／負數／trailing slash／query／fragment拒收，`/issues/177`通過。
- W1 exact producer：rc=0，212 rows＝211 Issue＋1 DraftIssue，sidecar建立。
- baseline artifact hash=`c1a127…`；reconcile `--check` rc=0（59個已登記缺口）。
- reconcile／canonical citation／現行pitfalls tests合跑：92 passed。
- 全程唯讀；未執行寫入型wfcli、未修改repo、未合併、未動Project欄位。

## 重審入口

只需處理P1-33。下一輪R1／R2做回歸，R3重驗canonical envelope與visibility-lag fixture，R4重驗具名flag的off/on read-write矩陣及phase 2可單獨回退；P1-30、P1-35無需重做。


## Comment 5473769284 · 2026-08-31T04:34:35Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（第十三輪）

- 被審 SHA：`c2282c332999388c61eb296c9da3f08a77b79f63`
- 前十二輪迄：issuecomment-5473680383
- 裁決：**REQUEST_CHANGES；R1 通過，R2 因本輪新增journal資源回歸不過，R3、R4不過**
- 查核者身分自述：Codex（OpenAI），session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T12:34:23+08:00`

## R1 前提回歸：過

- HEAD、`origin/main`、父卡spec基線均為完整被審SHA；worktree clean。
- 五份wave spec＋list-items frontmatter可解析；replacement rows、四波五卡、唯一owner matrix、硬依賴與tier未漂移。

## R2 射程、owner與資源回歸：不過

1. **既有邊界：過。** 本Initiative仍零cpbl、零Project語彙切換；原component-prefix交集均由硬依賴終態序列化。
2. **新journal owner：部分過。** journal writer／reader／tests屬W3′ `cli/src/`與`cli/tests/`，沒有跨wave owner衝突。
3. **`.gitignore` write-set：不過。** `w3.md:17` 新增`<repo>/.wf-pending/`且宣稱gitignored；現行`.gitignore`只有`.DS_Store`、`__pycache__/`、`*.py[cod]`，W3′資源亦沒有`file:.gitignore`。因此執行者若照spec讓目錄真正ignored，必寫一個未宣告資源。這是c2282c3新引入的R2輸入，不是推翻上一SHA的既有R2判斷。見P1-33。

## 第十二輪唯一finding重驗

- **P1-33：未全解。** 前輪的visibility-lag反例已解：完整凍結envelope落journal、retry整份重用，最多產same-id／same-hash實體重複；canonical-v1 hash與feature flag四格也已釘。剩餘缺口轉到journal本身：gitignore資源未宣告，且這個遠端事件的權威retry輸入沒有closed schema、原子落盤、hash／card／op／verb綁定回驗與path confinement。

## R3 內容、非零資訊與基線：不過

每組先列推翻條件，再列裁定。

### W0

- **AC1–2：過。** 推翻＝來源殘留、目的缺檔、雙居所或move內容漂移；既有oracle未變。

### W1

- **前置與AC1–5b：過。** raw inventory、唯一開卡、真JSON Schema、issue URL正規形、acceptance、撤銷與round-trip判準未漂移；P1-30維持已解。

### W2A

- **AC1–7：過。** 角色／節序、8×10、replacement rows、allowlist checker、清冊inactive標記、橫幅、move／引用／sign-off均無新矛盾。

### W2B

- **AC0–4：過。** 四類範本、mapping、baseline set/hash、L0與CI oracle未漂移。

### W3′

- **AC1：不過。** 分散式語意本身已成立，但journal是`--event-envelope`直接讀入並驅動遠端寫入的本機資料邊界。現文未要求：(a) 首次remote write前已完成原子／耐久publish；(b) retry載入時closed schema與canonical hash重算一致；(c) envelope card id／op id／verb／payload與本次命令綁定；(d) path必須resolve於同repo `.wf-pending/`、regular file且拒symlink；(e) 只有remote read-back確認same id／same hash後才刪。反例＝journal被截斷、被換檔或指向repo外JSON時，實作者可選擇照送、重建或崩潰，spec沒有唯一結果。見P1-33。
- **AC2–6b：過。** schema、doctor、拒絕訊息、resource matcher、snapshot與逐格清冊判準未漂移；P1-35維持已解。

## R4 現行系統影響：不過

1. **DraftIssue封路：過。** 先裁定、封creation、inventory為0才退legacy reader；活負控仍可見。
2. **CONTRACT_TOOL_RECONCILE：過。** baseline set/hash與merge-result逐symbol disposition未漂移。
3. **doctor抽出：過。** 薄facade與等價round-trip未漂移。
4. **Log→留言rollout／backout：不過。** `WF_COMMENT_READER`／`WF_COMMENT_WRITER`四格已封閉，off/on非法拒啟動，phase 2關閉可保留dual reader；多session同op最壞為same-hash重複亦可接受。但journal若非原子、遭tamper／symlink替換或在remote確認前被刪，可能送出錯誤payload或失去可重試證據；目前沒有fail-closed oracle。見P1-33。
5. **resource matcher、逐條清冊、cutover／cpbl：過。** 既有R4結論未漂移。

## 級別與能力層級推導：過

- W0／W2A T4與W1／W2B／W3′ T3仍依最高風險軸成立；能力層級、獨立查核與跨家族要求未變。

## Findings

### WF-REDESIGN1-P1-33（延續）

- severity: major
- blocking: true
- evidence: `w3.md:15`的W3′資源不含`.gitignore`，`:17`卻新增並宣稱gitignored的`.wf-pending/`。現行`.gitignore`沒有該pattern。相同行把`--event-envelope <journal路徑>`變成remote writer輸入，但只規定「整份重用」與hash產生法，未規定load時schema／hash／command binding驗證、atomic publish、path confinement或刪除read-back gate。
- disposition: (1) W3′ resources加入`file:.gitignore`，AC明列新增`/.wf-pending/`並以`git check-ignore -q .wf-pending/probe.json`為oracle；若不改versioned `.gitignore`，就刪除「gitignored」主張並另選有owner的機制。(2) journal定義closed `event-v1` schema（version、card id、verb、128-bit op id、payload、timestamp、hash，逐層additionalProperties=false）；首次遠端呼叫前以same-directory temp＋fsync＋no-clobber atomic publish，既有同op檔只接受byte/hash等價，異值fail-closed。(3) retry先resolve path並要求位於目前repo的`.wf-pending/`、檔名等於op id、regular non-symlink；解析schema、重算canonical-v1 SHA-256、核對card／verb／命令payload，任一不符在remote write前拒絕；不要讓任意外部JSON成為事件注入通道。(4) journal只在remote read-back證same op id＋same hash後刪除；unlink對多session的ENOENT採冪等成功。fixtures至少含partial JSON、hash tamper、same-op different payload、wrong card／verb、outside path、symlink、既有different journal，以及create成功但delete前crash。

## self_run

- HEAD／origin/main／父卡基線皆為完整`c2282c3…`；worktree clean；diff check綠。
- Ruby Psych：五份wave spec＋list-items 0 parse error。
- 現行`.gitignore` 3條，`.wf-pending/`零命中；W3′resource claim無`.gitignore`。
- baseline artifact hash=`c1a127…`；reconcile `--check` rc=0（59個已登記缺口）。
- reconcile／canonical citation／現行pitfalls tests合跑：92 passed。
- `materialize`於W3′零命中，未定回退分支確已刪。
- 全程唯讀；未執行寫入型wfcli、未修改repo、未合併、未動Project欄位。

## 重審入口

只需處理P1-33的journal邊界。下一輪R1做回歸；R2重驗`.gitignore` owner；R3重驗journal closed schema／atomicity／tamper fixtures；R4重驗remote read-back後刪除與path fail-closed。P1-30、P1-35無需重做。


## Comment 5475669034 · 2026-08-31T08:16:47Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（第十四輪）

- 被審 SHA：`24a6c8da15273011163362ce6369a64633584b5d`
- 承接：issuecomment-5473769284
- 裁決：**REQUEST_CHANGES；R1、R2、R4 通過，R3 不過**
- 查核者身分自述：Codex（OpenAI 家族），實際模型：**GPT-5**，session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T16:15:30+08:00`

## R1 前提回歸：過

1. HEAD、`origin/main`、父卡 spec 基線均為完整被審 SHA；worktree clean；`c2282c3..24a6c8d` 恰為派審揭露的 11 commits，`git diff --check` 無輸出。
2. 決議仍為 14 列唯一 owner；五份 wave spec 的 `replacement_rows` 分別為 W0 `[]`、W1 `[12]`、W2A `[1,3]`、W2B `[]`、W3′ `[10]`，與矩陣一致。
3. 四波五卡、硬依賴 `W0→W1→W2A→W2B→W3′`、全 aiwf／零不可逆／零 cpbl 接觸均未漂移；切換與 cpbl 仍歸切換 Initiative。
4. 本段 delta 的固定留言殘句、AC 次序、W3′ stage-rules 單行寫入權、量測日期、W3′ 簡稱、回顧基線與自審停止判準均未造成取代清單、owner、依賴或 tier 回歸。

## R2 射程、owner 與資源：過

1. **P1-33 `.gitignore` owner 已解。** W3′ 資源明列 `file:.gitignore`，AC 明列將 `/.wf-pending/` 加入並以 `git check-ignore -q .wf-pending/probe.json` 驗收。現行命令回 `rc=1` 是施工前基線，不是 AC 現在應通過；關鍵是未來寫入已由 W3′ 宣告。
2. W3′ journal writer／reader／tests 仍落在 `cli/src/`、`cli/tests/`；`.gitignore` 沒有第二 owner。
3. W3′ 新增 `file:stage-rules/` 只允許移除 §三之二 dormant marker 的單行 delta；雖與 W0／W2A 的 stage-rules 路徑有前綴交集，硬依賴終態序列化且 owner／允許 delta 已封閉，沒有同時在飛的資源競逐。

## R3 內容、非零資訊與基線：不過

### P1-33 重驗：過，前輪 finding 已解

推翻條件＝截斷／竄改／repo 外或 symlink journal 能在未拒絕下觸發遠端寫入；既有同 op 異內容可覆蓋；首次遠端呼叫早於 journal 原子發佈；或 remote 未 read-back same op id＋same hash 就刪 journal。

現規格已封閉上述反例：

- `event-v1` 列出 version／card／verb／128-bit UUID op id／payload／凍結 timestamp／hash，逐層 `additionalProperties=false`；canonical-v1 與 SHA-256 重算規則具名。
- 首次遠端呼叫前，以同目錄 temp＋fsync＋no-clobber rename 發佈；既有同 op 檔僅接受 byte／hash 等價，異值 fail-closed。
- retry 先做 repo 內 path confinement、檔名與 op id、regular non-symlink、schema、hash、card／verb／payload 綁定；全過才可碰遠端。
- 八個 fixture 的結果可由上述守衛唯一推出：七類 tamper／boundary 反例 fail-closed，create 成功但 delete 前 crash 走 same-hash 冪等收斂。

### 新增量測紀律回歸：不過

推翻條件＝99e0abc 新增的「快照數須標日期、移入 artifact，或屬三類白名單」在本次規劃產出中仍存在反例。

反例存在：

- `docs/research/drafts/stage-rules/pm-conduct.md:87` 新增禁止規則，但同檔 `:92` 仍寫「實測 #177 十二條 amend 中六條…」，沒有日期、artifact 或白名單分類；目前 #177 body 已有 **28** 條 `amend by wf-cli`，所以這不是抽象疑慮，而是已漂移的第二事實來源。
- 同檔 `:112` 的「11 個動詞／其餘 9 個」是可隨 CLI 改變的現況 inventory，未標日期、未指 artifact，也不是設計封閉集合。
- `docs/research/WORKFLOW-REDESIGN-2026-08-30.md:119` 的「144 餘 118／63 條／26 張」仍以未定年現況數住在「未定／未查」敘述；未落入三類白名單。

因此 PM 自審所載的裸現況數終掃 `0 命中` 是掃描器假陰性，不能推翻上列逐行反例。P1-30、P1-35 依重審入口未重做；前輪已通過的其餘 AC 未見本段 delta 回歸。

## R4 現行系統影響與回退：過

1. **Log→留言 rollout／backout：過。** `WF_COMMENT_READER`／`WF_COMMENT_WRITER` 四格封閉；off/on 非法拒啟動；phase 1、phase 2 為獨立可回退 commit，關 writer 後 dual reader 保留。
2. **journal 證據生命週期：過。** journal 僅在 remote read-back 證 same op id＋same hash 後刪除；delete 前 crash 保留可重試證據；併發 unlink 的 ENOENT 為冪等成功。
3. **輸入邊界：過。** repo 外 path、symlink、schema／hash／命令綁定不符均在任何 remote write 前 fail-closed，任意外部 JSON 不再是事件注入通道。
4. DraftIssue 封路、CONTRACT_TOOL_RECONCILE merge-result 守衛、doctor 薄 facade 與切換 Initiative 的 restore rehearsal／forward-repair 邊界均未被本段 delta 改壞。

## 級別與能力層級：過

W0／W2A 取規則紅線最高軸為 T4；W1／W2B／W3′ 取 public contract 最高軸為 T3。可逆性沒有被拿來抵銷較高的風險／影響範圍；主力型、獨立查核、W2A 跨家族與需求方閘門仍一致。

## Findings

### WF-REDESIGN1-P1-33（延續，已解）

- severity: major
- blocking: false
- evidence: `w3.md:15,17` 已加入 `.gitignore` owner／oracle、closed event-v1、寫前原子發佈、path／schema／hash／command binding gate、八類 fixtures，以及 read-back 後刪除。
- disposition: **resolved**；本輪沒有新增 journal 要求。

### WF-REDESIGN1-P1-38（新增）

- severity: major
- blocking: true
- evidence: `pm-conduct.md:87` 的新規則與同檔 `:92`、`:112` 及決議 `:119` 互相矛盾；其中「#177 十二條 amend」已被目前 28 條 amend 實際推翻。自審的零命中掃描漏掉中文數字與「未查」段。
- disposition: 對**決議＋brief＋wave specs＋本次將生效的 conduct＋父卡現值**做一次封閉 inventory；每個敘述數字逐項標成 `(a)` 日期化歷史、`(b)` 三類白名單及其理由、或 `(c)` 搬入具 hash artifact 並改寫成量法＋指向。至少修正上述三個反例；掃描須同時涵蓋阿拉伯與中文數字，並放一個未標日期的負控，唯一判準為 `unclassified_count==0`。不要只把目前命中的三行加入排除清單。

## self_run

- `git rev-parse HEAD`／`origin/main` → `24a6c8da15273011163362ce6369a64633584b5d`
- Ruby Psych 解析五份 wave spec＋list-items → 6/6 可解析；14-row matrix → ids 1–14 完整
- baseline artifact SHA-256 → `c1a1279324f2b5f40421eaa0408314a1afadae2c374c0c98782f66510af4bb68`
- reconcile `--check` → `59 個缺口全部有登記處置，判定一致`
- canonical citation＋contract reconcile＋pitfalls → `92 passed in 1.89s`
- `gh issue view ... | rg -c "amend by wf-cli"` → `28`
- 全程唯讀；未執行寫入型 wfcli、未改 repo、未合併、未動 Project 欄位。

## 重審入口

P1-33 已關閉，不必再重做。下一輪只需 R1 回歸新增 delta，R3 重驗 P1-38 的數字 inventory／分類／負控；若未觸及其他 owner 或執行語意，R2、R4 可沿用本輪通過結果。


## Comment 5476075199 · 2026-08-31T08:56:09Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（R15）

- 被審 SHA：`112532f5f0b34f9a2cecd13796520f153816b0bc`
- 承接：issuecomment-5475669034
- 裁決：**REQUEST_CHANGES；R1 通過，R3 不過；R2、R4 沿用 R14 通過結果**
- 查核者身分自述：Codex（OpenAI 家族），實際模型：**GPT-5**，session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T16:53:00+08:00`

## R1 前提回歸：過

1. HEAD、`origin/main`、父卡 spec 基線均為完整被審 SHA；worktree clean。
2. `24a6c8d..112532f5` 恰一個 commit `112532f`；`git diff --check` 無輸出。
3. 14-row 唯一 owner matrix、五份 wave spec 的 replacement rows、四波五卡、硬依賴 `W0→W1→W2A→W2B→W3′`、tier 與全 aiwf／零不可逆／零 cpbl 邊界均未漂移。
4. 三個 R14 點名反例已日期化；同族數字修訂沒有改變取代清單、owner 或 AC 語意。父卡基線敘述也已改為「審核輪次見卡留言」。

## R2 射程與資源：過（沿用 R14）

本 delta 新增 `scripts/prose_number_scan.py`、其測試與 inventory，沒有改 wave resource claims、互斥語意或執行中 owner；W3′ 既有 `file:scripts/`、`file:cli/tests/` 前綴亦未被拿來主張本次常設守衛是波卡施工成果。R14 的 `.gitignore` owner 結論不變。

## R3 數字 inventory、分類與負控：不過

### 已通過的部分

- 三個點名反例均已修：`pm-conduct.md` 的 amend 統計與動詞盤點已標 `2026-08-30`；決議「未定／未查」段已標同日快照。
- inventory 有 148 entries／148 unique keys；行文 SHA-1 drift 與 dead-entry gate 可運作。
- 原有兩型負控（裸阿拉伯數字、中文「十二條／六條」）確實轉紅；既有 8 專測與全套測試皆綠。

### 推翻條件與結果

推翻條件＝存在一行未標日期的現況數，掃描器仍不產生 `unclassified`；或 inventory 以原規範三類之外的理由把可漂數字判綠。

兩者都可重現：

1. **ID 剝除／Markdown 處理仍有假陰性。** 對目前 scanner 輸入下列六行，輸出只留下 `.json` 那一行；其餘五行完全沒有 row：
   - ``目前有 `42` 張卡。``：`_strip_ids` 把整個 inline-code span 刪掉。
   - `## 目前有 43 張卡`：所有 heading 無條件跳過。
   - `目前有 1234567 張卡。`：`[0-9a-f]{7,40}` 把純十進位數誤當 SHA。
   - `目前有 123456789012 張卡。`：同上。
   - `目前三人正在執行。`：中文量詞表不含「人」。
2. **artifact 判定過寬。** `inventory.json 目前有 44 張卡。` 被判為 class `c / artifact-pinned`；僅出現任意 `.json` 路徑並不等於「量法＋已釘 hash artifact」。因此 `unclassified_count==0` 仍可是假安心。
3. **inventory 擴張了需求方規範。** `pm-conduct.md` 只允許 `(a)` 日期化歷史、`(b)` 閾值／裁定值與不變量／封閉集合、`(c)` 已釘 artifact。inventory 卻在 class `(b)` 下另立 `environment-fact`、`historical-event-count`、`code-or-pattern-constant` 三種可免日期／artifact 的 reason，沒有需求方裁定支撐。
   - `pm-conduct.md:111` 的「兩個 repo／一個 token」被列 `environment-fact`；repo 與 token 配置可變，不是設計不變量。
   - 決議 `:56` 的「P1-33 十二輪定稿」與 `pm-conduct.md:92` 的「八輪漏掉」被列 `historical-event-count`；歷史數照原規範應日期化，而不是新增免日期白名單。
   - `design-closed-set` 亦有錯例：brief 的需求方原話「卡了一個月」被當成設計封閉集合，實際是帶日期來源的歷史引文。
4. `test_inventory_entries_all_carry_known_reason` 只驗 reason 字串出現在 inventory 自己宣告的集合，不能驗證該集合符合 `pm-conduct`，也不能驗逐條理由正確。故 `total=211 / unclassified=0 / dead_entries=0` 只證內部自洽，未證規範正確性。

父卡 `--file` 重跑得到 37 rows、其中 5 unclassified；這五項人工分類為模型／wave／設計封閉集合可成立，本輪不另列父卡 finding。但 `--file` 是資訊性且不套 inventory，不能補足上述常設守衛缺口。

## R4 現行系統影響：過（沿用 R14）

本 delta 未觸及 journal、remote write、feature flags、DraftIssue、CONTRACT_TOOL_RECONCILE、doctor rollout 或 cutover 回退語意。P1-33 維持已關閉；R14 的 read-back 後刪除、path fail-closed 與雙階段回退結論不變。

## 級別與能力層級：過

本 delta 沒有改各 wave 的風險／影響範圍／可逆性。W0／W2A T4，W1／W2B／W3′ T3，以及 W2A 跨家族查核要求仍符合最高軸原則。

## Findings

### WF-REDESIGN1-P1-38（延續）

- severity: major
- blocking: true
- evidence: `scripts/prose_number_scan.py:69` 以任意 `.json` 當 artifact；`:73` 的 SHA regex 會吃掉 7–40 位純十進位數；`:119` 刪除整段 inline code；`:132` 跳過全部 heading；`:111–136` 的中文量詞偵測漏「人」。上述對抗輸入可重現五個漏報與一個錯誤 class-c。inventory `_meta.classes` 又新增原規範不存在的 `environment-fact`／`historical-event-count`／`code-or-pattern-constant` reasons，且已有逐行錯分實例。
- disposition:
  1. 白名單語意回到 `pm-conduct` 三形態：class `(b)` 只能是 threshold／ruling 或 invariant／design-closed-set；歷史事件必走日期化 `(a)`，可變環境事實必走 `(a)` 或具 hash／量法的 `(c)`。程式碼區塊若非 prose，應由 Markdown tokenization 排除，⛔ 另造白名單類。
  2. `ARTIFACT_SIGNAL` 不得因單獨 `.json` 或一段 12–64 位 hex-like 字串就判 `(c)`；須證 artifact 指向與 hash／量法的組合，或明文 `artifact 重量／重列` 契約。
  3. 對 `ID_PATS` 逐條做「真識別子應剝除＋相鄰同形量測不得剝除」成對測試；至少加入 inline-code 數字、數字 heading、7 位與 12 位十進位計數、中文「三人」，以及 `.json` 同行裸現況數負控。不要以再加 broad regex 修 broad regex。
  4. 重新核 148 entries；每筆要有能說明該行為何屬規範白名單的 line-specific rationale，不能只以 inventory 自己宣告的五個 reason 名稱自證。唯一判準仍為 `unclassified_count==0 && dead_entries==0`，但須在上述對抗 suite 先證 scanner 不會漏報後才有資訊量。

## self_run

- HEAD／origin/main／父卡基線 → `112532f5f0b34f9a2cecd13796520f153816b0bc`
- frontmatter → 6/6 可解析；owner matrix → 14 rows、ids 1–14
- `python3 scripts/prose_number_scan.py` → `{"total": 211, "unclassified": 0, "dead_entries": 0}`
- inventory → 148 entries、148 unique；reason 分布：111 design-closed-set／20 threshold-ruling／12 code-or-pattern-constant／3 environment-fact／2 historical-event-count
- `pytest tests/test_prose_number_scan.py -q` → `8 passed`
- `pytest -q` → `1487 passed, 1 skipped in 57.98s`
- `uv run ruff ...` → 無法啟動：環境未安裝 `ruff`；未拿此結果判被審變更失敗
- baseline artifact SHA-256 → `c1a1279324f2b5f40421eaa0408314a1afadae2c374c0c98782f66510af4bb68`
- 全程唯讀；未執行寫入型 wfcli、未改 repo、未合併、未動 Project 欄位。

## 重審入口

下一輪只需 R1 回歸新增 delta，R3 重驗 P1-38 的 detector escape suite、三類白名單對齊與 inventory 逐條理由。P1-33 不重開；若仍未觸及 owner／執行語意，R2、R4可沿用本輪結果。


## Comment 5478699816 · 2026-08-31T12:58:00Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（R16）

- 被審 SHA：`78841697b61a485c15fdc764055428a6dda83968`
- 承接：issuecomment-5476075199
- 裁決：**REQUEST_CHANGES；R1 通過，R3 不過；R2、R4 沿用 R15/R14 通過結果**
- 查核者身分自述：Codex（OpenAI 家族），實際模型：**GPT-5**，session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T20:58:00+08:00`

## R1 前提回歸：過

1. HEAD、`origin/main` 與父卡 spec 基線均為完整被審 SHA；worktree clean。
2. `112532f5..7884169` 恰一個 commit；`git diff --check` 無輸出。delta 為 7 檔、+526/-343，與揭露相符。
3. 決議、brief 與 stage-rules 的同族修改是日期化與量測紀律收束；未改四波五卡、14-row owner matrix、硬依賴鏈、全 aiwf／零不可逆／零 cpbl 邊界、各 wave 的 replacement rows 或 tier。
4. R15 點名的六種逃逸形狀、三個自造 reason 與過寬 class-c 判定均已按原 disposition 處置；本輪失敗是後述新的、可重現之 fence 邊界與逐 token 理由缺口，不是沿用舊結果。

## R2 射程與資源：過（沿用）

本 delta 未改 wave resource claims、owner 或互斥語意；新增／修改的 standing scanner、inventory 與測試仍落在既有工具治理面。R14 的 `.gitignore` owner 與 R15 的射程結論不變。

## R3 零資訊、基線與 P1-38：不過

### 已通過的部分

- class `(b)` reason 已由測試字面鎖為 `threshold-ruling`／`design-closed-set`；inventory 實際只用這兩值。
- class `(c)` 已收緊為明文重量契約，或 artifact 檔名與含 a-f 的 hash 同行；單獨 `.json`、單獨 hash 均會轉紅。
- R15 的 inline code、數字 heading、7/12 位十進位、中文「三人」、裸 `.json` 六個反例均已成測試；45 條 `ID_PATS` 有等長代表表與相鄰 `42 張卡` 負控。
- 現有 corpus 得 `total=202 / unclassified=0 / dead_entries=0`；20 個專測與全套 1499 tests 均綠。

### 推翻條件與結果

推翻條件仍是：存在未日期化的現況數，scanner 卻不產 `unclassified`；或 inventory 的 rationale 沒有解釋該列實際被放行的數字。

兩者均可重現：

1. **fenced code parser 仍製造 rc=0 假陰性。** `scripts/prose_number_scan.py:163-171` 對任何以三個以上反引號或波浪號開頭的行一律翻轉單一 boolean，沒有記住 opener 的字元與長度。輸入「四反引號 markdown opener → 內文一行三反引號 → 四反引號 closer → `目前有 42 張卡。`」是合法 Markdown；目前實跑卻回 `rc=0 / unclassified_count=0`。同一句不包 fence 時回 `rc=1 / unclassified_count=1`。原因是內層三反引號被誤當 close，真正四反引號 close 又被誤當 open，後續正文遭整段跳過。現有 detector-escape suite 沒有 fence 長度／種類成對負控。
2. **128 筆 rationale 並非逐數字完整。** scanner 在 `:197-198` 把同列所有 tokens 放進一個 row，inventory 卻只給整列一個 reason／rationale，而測試 `test_inventory_entries_carry_line_specific_rationale` 只驗非空、非 reason 原字與長度，未驗每個 token 的語意都被說明。實際錯例：
   - 決議 `:74` 的 tokens 為 `[15, 1, 2, 三, 一]`，inventory `:116-120` 只解釋 `驗收 ≥1`，未解釋清冊 15、第三張、鏈深 ≤2、三子問等其餘候選。
   - `stage-rules/implementation.md:17` 的 tokens 為 `[13, 三, 一]`，inventory `:312-316` 寫「三層／兩層」，不但漏掉 `13 族清冊`，理由中的「兩層」也不在原列。
   - `wave-specs/w3.md:26` 的 tokens 為 `[三, 六]`，inventory `:893-897` 只說 DI 三層／兩層，未說明行內明列的六種拒收，且「兩層」同樣不在原列。

因此 `unclassified_count==0 && dead_entries==0` 仍只證「每個候選行有一個可用條目」，未證「每個候選數字符合三形態」。這正是本卡 R3 要求的非零資訊缺口。

## R4 現行系統影響：過（沿用）

本 delta 未觸及 journal、remote write、read-back 刪除、path confinement、feature flags、DraftIssue、CONTRACT_TOOL_RECONCILE、doctor rollout 或 cutover／回退語意。P1-33 不重開；R14 已通過的回退結論不變。

## 級別與能力層級：過

本 delta 未改各 wave 的風險、影響範圍或可逆性。W0／W2A T4，W1／W2B／W3′ T3，以及 W2A 跨家族查核要求，仍符合 canonical §0「取最高軸」原則。

## Findings

### WF-REDESIGN1-P1-38（延續；同 root cause 第三輪）

- severity: major
- blocking: true
- evidence: `scripts/prose_number_scan.py:163-171` 的 boolean fence toggler 可由合法四反引號外層＋內層三反引號重現 `42 張卡` 漏掃且 rc=0；inventory 又以一個 line-level rationale 放行整列 tokens，至少有決議 `:74`、implementation `:17`、w3 `:26` 三筆理由未覆蓋實際 token，現有測試只驗 rationale 形式存在。
- disposition:
  1. fence 狀態須記錄 opener 字元與長度；只有同字元且長度不短於 opener、符合 closing-fence 形狀的行可關閉。加入「四反引號外層含三反引號內文，close 後的 42 張卡必轉紅」及反引號／波浪號不得互關的成對測試。不要再以 broad toggle 補單一案例。
  2. inventory 分類單位改為逐候選 token／occurrence 的 `claims`（或等價封閉結構），每一 claim 自帶 reason＋rationale；scanner 應驗證偵測 token multiset 與 claims 一一覆蓋，漏一、多一、同 token 不同語意未分開均轉紅。若保留 line-level entry，至少也必須有機讀的 token coverage，而非自由文字長度門檻。
  3. 依新結構重核全部 128 筆，先修上述三個已證錯例，再以 `unclassified==0 / dead_entries==0 / uncovered_claims==0 / extra_claims==0` 作唯一判準。
  4. 這是 P1-38 同 root cause 的第三輪（R14 初見、R15 延續、R16 再現）。依決議「同根因第三輪停手」規則，**不得再直接派 R17 修補**；請升級需求方裁定 scanner 是否採真正 Markdown tokenizer／parser，以及 inventory 採 token-level schema 或撤回此常設守衛。裁定後另開新的、有邊界的處置入口。

## self_run

- HEAD／origin/main／父卡基線 → `78841697b61a485c15fdc764055428a6dda83968`
- commit count → 1；`git diff --check` → 無輸出；worktree clean
- `python3 scripts/prose_number_scan.py` → `{"total": 202, "unclassified": 0, "dead_entries": 0}`
- `pytest tests/test_prose_number_scan.py -q` → `20 passed`
- `pytest -q` → `1499 passed, 1 skipped in 262.26s`
- fence 反例 → wrapped `rc=0 / unclassified_count=0`；ordinary line `rc=1 / unclassified_count=1`
- 父卡現值 `--file` → 38 rows、5 unclassified；與 PM 揭露的五列相符，本輪未另列父卡 finding
- 全程唯讀；未改 repo、未合併、未動 Project、未執行寫入型 `wfcli`。

## 重審入口

本 finding 已達同 root cause 第三輪，沒有直接 R17 入口。下一步是需求方升級裁定上述 parser 與分類單位；裁定後再依新邊界決定是否重審 R1/R3。P1-33、R2、R4不重開。


## Comment 5478936102 · 2026-08-31T13:17:54Z

## P1-38 升級裁定轉錄（同根因第三輪，R16 裁決指定升級）

- 需求方裁定：**乙——自寫 CommonMark fence 子集狀態機＋inventory 改逐 token claims**（四選一之乙；甲＝引入 Markdown parser 套件、丙＝降宣稱至行級、丁＝撤回常設守衛，均未採）。
- 裁定時間：2026-08-31；轉錄來源：需求方於 Claude Code session `cc0a7952-07a5-4978-8d03-8b5f48fbc690` 之選項裁定（升級單全文由 PM 以附檔交付需求方）。本留言為 PM 代為轉錄，author 即需求方本人 token。
- 據此開啟有邊界的處置入口：fence opener 字元＋長度追蹤（closer 同字元且不短於 opener、反引號波浪號不互關）＋claims 逐 token（reason∈pm-conduct (b) 兩類＋line-specific rationale）＋判準四項全零（unclassified／dead_entries／uncovered_claims／extra_claims）。


## Comment 5479405576 · 2026-08-31T13:56:42Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（R17）

- 被審 SHA：`cfd0a32de9e170fbdfae391b7c30c54b9dd29fd9`
- 承接：issuecomment-5478699816；升級裁定：issuecomment-5478936102（乙）
- 裁決：**REQUEST_CHANGES；R1 通過，R3 不過；P1-33、R2、R4不重開**
- 查核者身分自述：Codex（OpenAI 家族），實際模型：**GPT-5**，session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T21:56:42+08:00`

## R1 前提回歸：過

1. HEAD、`origin/main` 與父卡 spec 基線均為完整被審 SHA；worktree clean。
2. `7884169..cfd0a32` 恰一個 commit `cfd0a32`；改檔僅 scanner、專測、inventory 三檔，與揭露一致；`git diff --check` 無輸出。
3. delta 沒有觸及決議、brief、wave specs、owner matrix、replacement rows、硬依賴鏈、tier 或 aiwf／cpbl 邊界；R1 無回歸。
4. 需求方的乙裁定有獨立留言留痕；本輪是升級後的新邊界，⛔ 沿用「第三輪不可再補」作形式否決。

## R2：不重開

本 delta 沒有改 owner、resource claims 或互斥語意；沿用 R16 通過結果。

## R3 fence escape／claims 覆蓋／三錯例：不過

### fence 子集：過

- `scripts/prose_number_scan.py:168-197` 已以 opener 字元＋長度取代 boolean toggle；closer 要求同字元、不短於 opener、且無 info string。
- R16 的四反引號外層＋三反引號內文反例現回 `unclassified`；短 closer、不互關、帶 info string 非 closer、較長 closer、三空白縮排 closer 與普通 fence 排除均實跑符合裁定。
- 本結論只覆蓋需求方裁定的 CommonMark fence 子集；未以子集外形狀否決。

### token 數量覆蓋：過

- inventory 為 128 unique entries／208 claims；現行 corpus 的偵測 token multiset 與 claims multiset 相等。
- 漏 token、幽靈 claim、相同 token 需要相同數量 claims 的 fixtures 皆會轉紅；四個輸出計數目前均為零。

### claim 語意與閉合契約：不過

推翻條件＝任一 claim 沒有綁到實際 occurrence 的正確語意，或 claim 缺／違反 `token + 兩值 reason + line-specific rationale` 仍能被主 scanner 判綠。

兩者均可重現：

1. **multiset 只證數量，沒有分開同 token 的不同語意。** `scan_file` 在 `:221-227` 只比較排序後 token 字串；沒有 occurrence、位置或 context 綁定。因此複製同一理由兩次也會綠。現行 inventory 已有實例：
   - 決議 `:43` 的兩個「三」分別是「三層編號清單」與「三值」，但 inventory `:177-188` 兩份 claim 都寫成「三值」。
   - `wave-specs/w1.md:58` 的兩個「三」分別是 CLI 增量「三層評估」與退場 oracle「三欄」，inventory `:1576-1587` 卻兩份都寫成 DI 注入三層；同列第二個「五」是被禁止的舊字樣「五波施工」，`：1595-1602` 又把兩個「五」都解釋成現行「四波五卡」。
   - R16 點名的 `stage-rules/implementation.md:17` 尚未完整修好：`13` 與「三層」已有正確 claim，但 token「一」實際來自「上一輪」，inventory `:683-699` 的 rationale 卻引用不含該 occurrence 的「規格＋三層注意事項＋13」。三筆點名錯例因此只有決議 `:74` 與 w3 `:26` 完整關閉。
2. **另有現況數被錯列設計封閉集合。** `wave-specs/w2b.md:19` 的 `6` 是「碼引用 6 處不動」的現況引用數，會隨程式碼漂移；inventory `:1789-1806` 把它與「新五檔／四段標題」一併以 mapping 枚舉理由標為 `design-closed-set`。這不符合 pm-conduct：應日期化或由 artifact／量法承載。
3. **主 scanner 沒驗 claim schema。** 對 `目前有 42 張卡。` 注入 `{token:"42", reason:"environment-fact", rationale:""}`，`scan_file` 仍回 class `b`；因為 `:221-225` 只讀 token。reason 白名單與 rationale 非空目前僅由 pytest 對「當下 inventory」檢查，`python3 scripts/prose_number_scan.py` 自身仍可對違約 inventory 輸出四零假綠。
4. **新 schema 的失敗輸出有回歸。** 模擬一筆 dead entry 時，`main` 在 `:298-299` 仍讀已不存在的 top-level `e["reason"]`，實跑為 `KeyError 'reason'`，沒有契約化 dead-entry 證據。另 `--json` 在 claims mismatch 時雖 rc=1，`:292-294` 卻只輸出空的 `unclassified`／`dead_entries`，完全省略 `uncovered_claims`、`extra_claims` 與 mismatch 證據。

所以 `total=202 / 四項全零` 與 1507 tests 全綠，只證目前 token 數量自洽，尚未證逐 token claim 的內容正確及守衛失敗時可稽核。

## R4：不重開

本 delta 未觸及 journal、remote write、read-back、path confinement、feature flags、DraftIssue、CONTRACT_TOOL_RECONCILE 或 cutover／回退語意；P1-33 維持關閉。

## 級別與能力層級：無回歸

本 delta 未改風險、影響範圍或可逆性；既有 W0／W2A T4、W1／W2B／W3′ T3 與跨家族查核要求不變。

## Findings

### WF-REDESIGN1-P1-38（升級後有邊界入口延續）

- severity: major
- blocking: true
- evidence: fence 狀態機與 token multiset 已達裁定，但 scanner 只比較 token 字串，非法 reason＋空 rationale 仍回 class `b`；現行 inventory 有同 token 不同語意複製同 rationale、implementation 點名錯例未完全修正，以及 `w2b.md:19` 的可漂 `6 處` 被誤列設計集合。dead-entry 路徑另會 `KeyError`，JSON mismatch 輸出缺證據。
- disposition:
  1. claim 必須綁 occurrence，而非只綁 token 字串：加入 occurrence ordinal、span 或穩定 context，scanner 機械驗每個偵測 occurrence 恰有一個 claim。相同 token、不同 occurrence 可有相同理由，但測試須另有「兩個 8、兩份相同 rationale 仍不足以解釋兩種語意」的反例，避免只驗數量。
  2. 在主 scanner 載入邊界驗 closed claim schema：entry／claim 封閉 keys、token 型別、reason 必屬兩值、rationale 非空且至少綁定該 occurrence；任一違約須 fail-closed 並留下可讀與 JSON 證據，不能只靠 pytest 檢查當下檔案。
  3. 重核 208 claims，至少修正決議 `:43`、w1 `:58`、implementation `:17`、w2b `:19`；其餘同 token 重複 claims 逐列判斷是同義引用還是不同語意。可漂 `碼引用 6 處` 改日期化或 artifact／量法，⛔ 以 `design-closed-set` 留下。
  4. 修正 dead-entry 的舊 schema 存取；`--json` 必須輸出 claims mismatch 的四項計數與逐列證據。加入 dead entry、非法 reason、空 rationale、同 token 同理由錯綁、JSON mismatch 五類 regression tests。

## self_run

- HEAD／origin/main／父卡基線 → `cfd0a32de9e170fbdfae391b7c30c54b9dd29fd9`
- commit count → 1；改檔 → 3；`git diff --check` → 無輸出；worktree clean
- `python3 scripts/prose_number_scan.py` → `{"total":202,"unclassified":0,"dead_entries":0,"uncovered_claims":0,"extra_claims":0}`
- inventory → 128 entries／128 unique keys／208 claims；reason 分布 177 design-closed-set／31 threshold-ruling
- `pytest tests/test_prose_number_scan.py -q` → `28 passed`
- `pytest -q` → `1507 passed, 1 skipped in 67.50s`
- fence 額外對抗：R16 exact、longer closer、info-string 後正確 close、異字元後正確 close、三空白 closer → close 後的 `42` 均為 `unclassified`
- 非法 claim schema 反例 → class `b`；dead-entry 反例 → `KeyError 'reason'`；JSON mismatch 反例 → rc=1 但 body 僅兩個空清單
- 全程唯讀；未改 repo、未合併、未動 Project、未執行寫入型 `wfcli`。

## 重審入口

下一輪僅需 R1 回歸新增 delta，R3 重驗 occurrence-bound claims、上述四列 inventory、closed schema 與 dead／JSON 失敗輸出。fence 子集已通過，若未修改不必重做；P1-33、R2、R4不重開。


## Comment 5479722248 · 2026-08-31T14:21:46Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（R18）

- 被審 SHA：`7c06996dcab96abab1840d2e5b3b215e91d24786`
- 承接：issuecomment-5479405576
- 裁決：**REQUEST_CHANGES；R1 通過，R3 不過；fence、P1-33、R2、R4不重開**
- 查核者身分自述：Codex（OpenAI 家族），實際模型：**GPT-5**，session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T22:21:46+08:00`

## R1 前提回歸：過

1. HEAD、`origin/main` 與父卡 spec 基線均為完整被審 SHA；worktree clean。
2. `cfd0a32..7c06996` 恰一個 commit；改檔為 scanner／tests／inventory／w2b.md 四檔，與揭露一致；`git diff --check` 無輸出。
3. w2b 唯一文書修改只把「碼引用 6 處」釘為 `2026-08-30` 量測；未改四波五卡、owner、replacement rows、硬依賴鏈、tier 或 aiwf／cpbl 邊界。

## R2：不重開

本 delta 沒有改 owner、resource claims 或互斥語意；沿用既有通過結果。

## R3 occurrence claims／closed schema／失敗輸出：不過

### 已通過的部分

- occurrence 綁定已落地：scanner 以 `(occurrence, token)` 對集與 claim 數量共同判斷；兩個相同 token 都綁 occurrence 0 的反例會轉紅，分綁 0／1 才過。
- claim 層 exact keys、非法 reason、空 rationale、extra key、負 occurrence 與空 token 已有 scanner 內檢查；R17 的 `environment-fact`＋空 rationale 反例現為 `invalid-claims`。
- dead-entry 的既有正常形狀已不再讀 top-level reason；JSON 模式現含六類逐列證據與 counts，R17 兩個輸出回歸均已修正。
- 決議 `:43` 的「三層／三值」、w1 `:58` 的「三欄」與兩個「五」、implementation `:17` 的「上一輪」、w3 `:26`，以及 w2b `:19` 日期化均已分 occurrence 處理。
- inventory 為 127 entries／205 claims；現行 corpus 六項計數皆為零；34 專測與 1513 全套 tests 均綠。

### 推翻條件與結果

推翻條件＝closed entry schema 任一缺欄仍能判綠／崩潰而非產生 `invalid-claims` 證據，或逐 occurrence rationale 仍錯指另一套語意。

兩者都可重現：

1. **entry schema 尚未 closed。** `_ENTRY_KEYS` 在 `scripts/prose_number_scan.py:237` 定義 `path／line_sha1／excerpt／claims`，但 `_entry_schema_errors` 的 `:241-250` 只驗 extra keys，沒有驗 missing keys，也沒有驗 entry 欄位型別。
   - 移除 `excerpt` 的 entry：`schema_errors=[]`，對「信封固定為 8 欄」仍回 class `b`。
   - 移除 `path` 或 `line_sha1`：`load_inventory` 在 `:267-270` 的 dict comprehension 直接 `KeyError`，沒有 `invalid-claims` 的人讀／JSON 證據。
   這推翻了「entry／claim 鍵封閉，任一違約皆 fail-closed 並留下證據」；目前只閉合 claim，尚未閉合 entry。
2. **兩筆 occurrence 已綁定，但 rationale 仍綁錯語意。** brief `:47` 與 `wave-specs/w1.md:58` 的「三層評估」都引用決議 §七的 CLI 增量原則；該節明列的是旗標／欄位／資訊輸出三層。inventory `:647` 與 `:1746` 卻仍解釋為 §八的 DI 注入層級「任務→專案→框架」。occurrence 編號正確，但 line-specific rationale 錯誤，因此 205 claims 的逐筆語意尚未全過。

本輪未以 CommonMark 子集外形狀、occurrence 跨 regex 版本耦合或已揭露的 W3′ 執行期風險否決。

## R4：不重開

本 delta 未觸及 journal、remote write、read-back、path confinement、DraftIssue、CONTRACT_TOOL_RECONCILE 或 cutover／回退；P1-33維持關閉。

## 級別與能力層級：無回歸

本 delta 未改風險、影響範圍或可逆性；既有 W0／W2A T4、W1／W2B／W3′ T3 與跨家族查核要求不變。

## Findings

### WF-REDESIGN1-P1-38（升級後入口延續）

- severity: major
- blocking: true
- evidence: occurrence、claim schema 與正常 dead／JSON 路徑已修，但 entry 缺 `excerpt` 仍 class `b`，缺 `path`／`line_sha1` 直接 KeyError；brief `:47` 與 w1 `:58` 的 CLI 增量三層又仍被錯解為 DI 三層。
- disposition:
  1. 在 `load_inventory` 建 map 前逐 raw entry 驗 `set(entry) == _ENTRY_KEYS`，並驗 `path`／`line_sha1`／`excerpt` 型別與 SHA-1 形狀；缺 identity 的 entry 也必須以 inventory-level invalid evidence 回報，不能先索引而崩潰。重複 `(path,line_sha1)` 同樣 fail-closed，避免 dict comprehension 靜默覆蓋。
  2. `invalid_entries` 納入上述無法綁到 corpus row 的 load-time 錯誤；人讀與 `--json` 都輸出。加入缺 excerpt、缺 path、缺 line_sha1、錯型別、duplicate key 五類 regression tests。
  3. 修正 brief `:47` 與 w1 `:58` occurrence 0 的 rationale：須對應決議 §七的 CLI 增量三層（旗標／欄位／資訊輸出），⛔ 再引用 DI 任務／專案／框架。其餘五筆 DI rationale 已逐列核對，對應的確是注意事項注入層級，可保留。

## self_run

- HEAD／origin/main／父卡基線 → `7c06996dcab96abab1840d2e5b3b215e91d24786`
- commit count → 1；改檔 → 4；`git diff --check` → 無輸出；worktree clean
- `python3 scripts/prose_number_scan.py` → `{"total":202,"unclassified":0,"dead_entries":0,"invalid_entries":0,"uncovered_claims":0,"extra_claims":0}`
- inventory → 127 entries／127 unique keys／205 claims
- `pytest tests/test_prose_number_scan.py -q` → `34 passed`
- `pytest -q` → `1513 passed, 1 skipped in 63.61s`
- 缺 `excerpt` 反例 → schema errors 空、class `b`；缺 `path`／`line_sha1` → 各為 `KeyError`
- 四列 occurrence 與 w2b 日期化逐筆核對；DI rationale 共七筆，其中 brief／w1 兩筆語意不符
- 全程唯讀；未改 repo、未合併、未動 Project、未執行寫入型 `wfcli`。

## 重審入口

下一輪只需 R1 回歸新增 delta，R3 重驗 entry-level closed schema 的五類失敗、兩筆「三層評估」rationale 與 JSON／人讀證據。Occurrence 配對、其餘 inventory、fence、P1-33、R2、R4不重開。


## Comment 5480014000 · 2026-08-31T14:45:04Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（R19）

- 被審 SHA：`a4862e45f09a4395657ec0acfb0e3b267dc42eac`
- 承接：issuecomment-5479722248
- 裁決：**REQUEST_CHANGES；R1 通過，R3 不過；P1-33、occurrence 綁定、fence、R2、R4 不重開**
- 查核者身分自述：Codex（OpenAI 家族），實際模型：**GPT-5**，session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T22:45:04+08:00`

## R1 前提回歸：過

1. HEAD、`origin/main` 與父卡 spec 基線均為完整被審 SHA；worktree clean。
2. `7c06996..a4862e4` 恰一個 commit；改檔為 scanner／tests／inventory 三檔，與揭露一致；`git diff --check` 無輸出。
3. delta 沒有改四波五卡、owner、replacement rows、硬依賴鏈、tier 或 aiwf／cpbl 邊界。inventory 只改 entry schema 說明與兩筆 rationale，未引入新的規劃前提。

## R2：不重開

本 delta 未改 owner、resource claims 或互斥語意；沿用 R18 通過結果。

## R3 load identity／regressions／rationale：不過

### 已通過的部分

- `load_inventory` 已在建 map 前驗 entry exact keys、`path`／`line_sha1`／`excerpt`、claims，並以 entry index 留下 load-level invalid evidence；重複 `(path,line_sha1)` 不再靜默覆蓋。
- 缺 excerpt、缺 path、缺 line_sha1、非 hex SHA-1、duplicate identity 五類 regression tests 均存在。另以非字典 entry、整數 SHA-1、entry extra key 對抗探測，人讀與 JSON 模式皆 `rc=1` 且有逐項證據。
- brief 與 w1 的 occurrence 0 rationale 已改為決議 §七 CLI 增量三層評估，沒有再錯綁 DI；其餘五筆 DI rationale 仍各自位於 DI 語境。
- inventory 為 127 entries／205 claims／127 unique identities，全部行文 hash 仍存活；現行 corpus 的 scanner 輸出為零缺口。

### 推翻條件與結果

推翻條件＝本輪新增的 load error 或既有 claims mismatch 可以讓文件宣告的「唯一判準」全零，或 corpus 守衛測試未斷言實際 red predicate 的全部維度。

兩者都可重現：

1. `scripts/prose_number_scan.py:41-42` 仍宣告唯一判準只有 `unclassified／dead_entries／uncovered_claims／extra_claims` 四項全零；但實際 `main` 在 `:378-379` 另以 `invalid_entries` 與整體 `claims_mismatch` 判紅。這形成兩套互斥的 pass/fail 定義。
2. 缺 `excerpt` 的 load-invalid entry 配一行日期化語料時，文件四項全部為零，`invalid_entries=1`。也就是依文字 oracle 會過，實際 CLI 會紅。
3. 同一 `(occurrence,token)` 重複兩個完整 claim 時，文件四項仍全部為零，`claims_mismatch=1`；`uncovered_claims` 與 `extra_claims` 都是零。這不是重開 occurrence 配對，而是證明四項投影不足以代表實際 mismatch predicate。
4. `cli/tests/test_prose_number_scan.py:379-388` 的 corpus 不變量只斷言上述舊四項，沒有斷言 `invalid_entries` 或 `claims_mismatch`；因此第 2、3 類壞 inventory 可讓這支整體 corpus test 綠。一般輸出 `scripts/prose_number_scan.py:371-376` 也未列 `claims_mismatch` count。

因此，本輪指定的 load 行為已修好，但 R3 要求的可證偽基線仍未釘成單一判準；P1-38 尚不能關閉。

## R4：不重開

本 delta 未觸及 journal、remote write、read-back、path confinement、DraftIssue、CONTRACT_TOOL_RECONCILE 或 cutover／回退；P1-33 維持關閉。

## 級別與能力層級：無回歸

本 delta 未改風險、影響範圍或可逆性；既有 W0／W2A T4、W1／W2B／W3′ T3 與跨家族查核要求不變。

## Findings

### WF-REDESIGN1-P1-38（延續）

- severity: major
- blocking: true
- evidence: load validation 與兩筆 rationale 已修；但 module contract 的舊四項 oracle、`test_corpus_is_fully_classified` 的四項斷言、human summary 與 `main` 的實際 red predicate 不一致。兩個對抗例均可在舊四項全零時分別留下 `invalid_entries=1` 或 `claims_mismatch=1`。
- disposition:
  1. 把 pass/fail 定義收斂成一個共用 predicate，至少明列並判定 `unclassified=0`、`dead_entries=0`、`invalid_entries=0`、`claims_mismatch=0`；`uncovered_claims`／`extra_claims` 可保留為 mismatch 的診斷投影，但不得取代整體 mismatch。
  2. 同步 module doc 的「唯一判準」、human summary 與 `test_corpus_is_fully_classified`，避免三處再各自漂移；測試必直接斷言 `invalid_entries` 與 `claims_mismatch`。
  3. 加兩個 regression：load-invalid 但舊四項全零必紅；duplicate identical occurrence pair 使 uncovered／extra 皆零但 `claims_mismatch=1` 必紅，且 human／JSON summary 都能看見該 count。

## self_run

- HEAD／origin/main／父卡基線 → `a4862e45f09a4395657ec0acfb0e3b267dc42eac`
- commit count → 1；改檔 → 3；`git diff --check` → 無輸出；worktree clean
- `python3 scripts/prose_number_scan.py` → `{"total":202,"unclassified":0,"dead_entries":0,"invalid_entries":0,"uncovered_claims":0,"extra_claims":0}`
- inventory → 127 entries／127 unique identities／205 claims／all hashes live
- `pytest tests/test_prose_number_scan.py -q` → `39 passed in 1.05s`
- `pytest -q` → `1518 passed, 1 skipped in 67.53s`
- load 對抗探測 → 缺三 identity 欄、整數 SHA-1、extra key、非字典 entry、duplicate identity 均 human／JSON `rc=1` 且有 evidence
- oracle 反例一 → 舊四項全零、`invalid_entries=1`；反例二 → 舊四項全零、`claims_mismatch=1`
- 附加 Ruff 檢查未執行：此專案 uv 環境未安裝 `ruff`；非本派審指定判準，未以此下結論。
- 全程唯讀；未改 repo、未合併、未動 Project、未執行寫入型 `wfcli`。

## 重審入口

下一輪只需 R1 回歸新增 delta，R3 重驗單一 pass/fail predicate、corpus test 與 human／JSON counts 的一致性，以及上述兩個反例。已修好的 load schema 五類、兩筆 rationale、occurrence 配對本體、fence、P1-33、R2、R4 不重開。


## Comment 5480471072 · 2026-08-31T15:21:37Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（R20）

- 被審 SHA：`c1e22683d6b085a54aaf63cf391907ee6a811bc9`
- 承接：issuecomment-5480014000
- 裁決：**REQUEST_CHANGES；R1 通過，R3 不過；P1-33、occurrence／load／fence、R2、R4 不重開**
- 查核者身分自述：Codex（OpenAI 家族），實際模型：**GPT-5**，session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T23:21:37+08:00`

## R1 前提回歸：過

1. HEAD、`origin/main` 與父卡 spec 基線均為完整被審 SHA；worktree clean。
2. `a4862e4..c1e2268` 實測恰 **2 個 commits**（`63e388e`／`c1e2268`）；改檔為 scanner／tests／inventory 三檔，與本派審 delta 主段揭露一致；`git diff --check` 無輸出。重審入口末句的「1-commit delta」與 Git 事實矛盾，依前段完整揭露與實測兩個 commits 審查，屬信封尾端筆誤，不影響被審物識別。
3. delta 沒有改四波五卡、owner、replacement rows、硬依賴鏈、tier 或 aiwf／cpbl 邊界。

## R2：不重開

本 delta 未改 owner、resource claims 或互斥語意；沿用 R19 通過結果。

## R3 單一 predicate／兩反例／rationale：不過

### 已通過的部分

- `RED_KEYS=(unclassified, dead_entries, invalid_entries, claims_mismatch)` 與 `is_red()` 已成為實際單一判準；module doc、main、human summary 與 corpus test 對齊。`uncovered_claims`／`extra_claims` 只作診斷投影，不再冒充完整 mismatch 判準。
- R19 反例一重跑：舊四項全零而 `invalid_entries=1` 時，JSON `rc=1`。反例二重跑：duplicate identical occurrence pair 使兩投影全零而 `claims_mismatch=1` 時，人讀與 JSON 均 `rc=1` 且都看得到該 count。
- inventory 缺檔／壞 JSON、file mode 讀取錯誤、UnicodeDecodeError 與 bool occurrence 均已有可讀 fail-closed 覆蓋；本輪未以這些附加改善否決。
- rationale 引句錨定測試可抓「引句不在被釘原行」；本 commit 修的六筆形式脫鉤均已對回原行。127 entries／205 claims／127 unique identities 全部 hash 存活；31 個 threshold-ruling claims 逐列對照未見錯綁；六筆無引句的注意事項括號數也各自與實際清冊條數一致。

### 推翻條件與結果

推翻條件＝任一現行 claim 的 line-specific rationale 雖通過文字錨定，卻把被否定的數字說成目前枚舉基數。

此條件可在現值重現：

- `docs/research/drafts/wave-specs/w2b.md:12` 明列「封閉五檔」及五個成員，並逐字寫 `P1-15 更正：⛔ 非六檔`。因此 token `六` 是被否定的舊數值，**不是**該段枚舉基數。
- 對應 inventory `docs/research/drafts/prose-number-inventory.json:2023` 卻寫：`「六」＝該段枚舉之基數（行內列明成員）`。真正由行內成員支持的基數是前一個 occurrence 的「五檔」。
- `test_rationale_quotes_anchor_to_the_pinned_line` 仍會綠，因為它只證明引句「六」存在於原行；它不、也不應被誤讀為已驗證 rationale 的語意方向。這正是派審詞列為「刻意不驗、交由查核者」的 205 claims 語意查核所抓到的現值反例。

因此，R19 的單一 predicate blocking 已實質關閉；R3 仍因一筆當前白名單理由與原句相反而不過，P1-38 尚不能關閉。

## R4：不重開

本 delta 未觸及 journal、remote write、read-back、path confinement、DraftIssue、CONTRACT_TOOL_RECONCILE 或 cutover／回退；P1-33 維持關閉。

## 級別與能力層級：無回歸

本 delta 未改風險、影響範圍或可逆性；既有 W0／W2A T4、W1／W2B／W3′ T3 與跨家族查核要求不變。

## Findings

### WF-REDESIGN1-P1-38（延續）

- severity: major
- blocking: true
- evidence: `w2b.md:12` 的封閉集合明列五個成員並否定六檔；inventory `:2023` 卻把 occurrence 4 的「六」稱為該段枚舉基數。引句錨定通過只證字面存在，無法推翻此語意矛盾。
- disposition:
  1. 首選：從現行設計句移除 `P1-15 更正：⛔ 非六檔`，將歷史更正只留在既有 issue／Log 留痕；重生該 entry 的 hash 與 claims，讓現行 spec 只承載封閉五檔。
  2. 若需求方決定保留負例，則 occurrence 4 rationale 必須改成例如：`「非六檔」＝封閉五檔集合對舊六檔說法的否定式負例，⛔ 非目前枚舉基數`；不得沿用「六＝枚舉基數」。這仍可歸 `design-closed-set`，不需擴張 reason 白名單。
  3. 針對所選處置加精確 regression：移除方案驗該 entry 不再有 token 六；保留方案驗該 claim 明示否定式負例且不得含「六＝枚舉基數」。不要求把一般語意理解錯誤地塞進 broad regex。

## self_run

- HEAD／origin/main／父卡基線 → `c1e22683d6b085a54aaf63cf391907ee6a811bc9`
- commit count → 2；改檔 → 3；`git diff --check` → 無輸出；worktree clean
- `python3 scripts/prose_number_scan.py` → `{"total":202,"unclassified":0,"dead_entries":0,"invalid_entries":0,"claims_mismatch":0,"uncovered_claims":0,"extra_claims":0}`
- inventory → 127 entries／127 unique identities／205 claims／all hashes live；117 unique rationale groups 逐來源行對照
- `pytest tests/test_prose_number_scan.py -q` → `48 passed in 1.10s`
- `pytest -q` → `1527 passed, 1 skipped in 66.96s`
- R19 load-invalid 反例 → `rc=1, invalid_entries=1`；duplicate pair 反例 → human／JSON 均 `rc=1, claims_mismatch=1` 且兩投影為零
- threshold-ruling 31 claims、六筆無引句括號數及本輪六筆引句修正逐列對照；另抓到 w2b occurrence 4 的「六＝枚舉基數」與原行 `非六檔` 相反
- 全程唯讀；未改 repo、未合併、未動 Project、未執行寫入型 `wfcli`。

## 重審入口

下一輪只需 R1 回歸新增 delta，R3 重驗 w2b `:12` occurrence 4 的選定處置與精確 regression。單一 predicate、R19 兩反例、其餘 204 claims、occurrence／load／fence、P1-33、R2、R4 不重開。


## Comment 5480637139 · 2026-08-31T15:35:12Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（R21）

- 被審 SHA：`f277b2f7ff1b66d0b4d2e2009c4c807abe2251fd`
- 承接：issuecomment-5480471072
- 裁決：**REQUEST_CHANGES；R1 通過，R3 不過；P1-33、單一 predicate、兩反例、occurrence／load／fence、R2、R4 不重開**
- 查核者身分自述：Codex（OpenAI 家族），實際模型：**GPT-5**，session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T23:35:12+08:00`

## R1 前提回歸：過

1. HEAD、`origin/main` 與父卡 spec 基線均為完整被審 SHA；worktree clean。
2. `c1e2268..f277b2f` 恰一個 commit；僅修改 `prose-number-inventory.json` 一檔的一筆 rationale，與揭露一致；`git diff --check` 無輸出。
3. delta 未改四波五卡、owner、replacement rows、硬依賴鏈、tier、aiwf／cpbl 邊界或 scanner 行為。

## R2：不重開

本 delta 未改 owner、resource claims 或互斥語意；沿用 R20 通過結果。

## R3 唯一 claim：不過

### 已通過的內容修正

- `w2b.md:12` 的 occurrence 4 仍是 token `六`、reason `design-closed-set`；新 rationale `「⛔ 非六檔」＝P1-15 更正的否定式陳述——排除錯誤基數，正值＝行內枚舉的封閉五檔` 與原句方向一致。
- 此分類沒有增加新的 reason：它表達封閉五檔集合對錯誤六檔基數的排除，仍屬設計封閉集合的負例。
- 同形核對未發現另一筆把否定數值當正基數；既有「第四張／第四輪」也已明示為否定式門檻。
- 現行 scanner 六項缺口全零；48 專測與 1527 全套 tests 均綠。

### 推翻條件與結果

R20 disposition 3 的推翻條件＝把該 claim 改回舊錯值 `「六」＝該段枚舉之基數（行內列明成員）` 時，新增的精確 regression 必須轉紅；既有一般引句錨定不得被當成這支 regression。

此條件未滿足：本輪 delta 沒有修改 tests。以記憶體副本把唯一 claim 改回 R20 舊錯值後實跑：

- `_entry_schema_errors` → `[]`
- 引句錨定 → `true`（原行確實含「六」）
- `scan_file` 對 w2b `:12` → class `b`

也就是目前所有既有守衛仍無法區分「六是被否定的錯誤基數」與「六是枚舉基數」；本輪只修了資料現值，沒有加入 R20 明列、且會在修正前失敗的 regression。內容已正確，但 P1-38 的防復發證據仍未完成。

## R4：不重開

本 delta 未觸及 journal、remote write、read-back、path confinement、DraftIssue、CONTRACT_TOOL_RECONCILE 或 cutover／回退；P1-33 維持關閉。

## 級別與能力層級：無回歸

本 delta 未改風險、影響範圍或可逆性；既有 W0／W2A T4、W1／W2B／W3′ T3 與跨家族查核要求不變。

## Findings

### WF-REDESIGN1-P1-38（延續）

- severity: moderate
- blocking: true
- evidence: 現值 rationale 已修正，但 delta 無 regression；將 claim 暫改回前輪錯值後，closed schema、引句錨定與 scanner classification 仍全部通過。這直接推翻 R20 disposition 3 要求的「舊錯值必紅」。
- disposition:
  1. 不需再改 inventory 或 production scanner；在 `cli/tests/test_prose_number_scan.py` 加一支針對此已知語意的精確 regression。
  2. 測試定位 w2b `:12` 的 occurrence 4，至少驗 `token=六`、`reason=design-closed-set`、rationale 明示 `⛔ 非六檔`／`否定式`／`排除錯誤基數`／正值為封閉五檔，且不得把六稱為目前枚舉基數。
  3. 同一測試或 helper 加 negative control：輸入前輪舊 rationale `「六」＝該段枚舉之基數（行內列明成員）` 必失敗。這是已知 bug 的定點回歸，⛔ 不需擴成 broad 語意 regex。

## self_run

- HEAD／origin/main／父卡基線 → `f277b2f7ff1b66d0b4d2e2009c4c807abe2251fd`
- commit count → 1；改檔 → 1；diff → 1 insertion／1 deletion；`git diff --check` → 無輸出；worktree clean
- target claim → token `六`／occurrence 4／reason `design-closed-set`／新否定式 rationale 與 w2b 原句一致
- `python3 scripts/prose_number_scan.py` → `{"total":202,"unclassified":0,"dead_entries":0,"invalid_entries":0,"claims_mismatch":0,"uncovered_claims":0,"extra_claims":0}`
- `pytest tests/test_prose_number_scan.py -q` → `48 passed in 1.05s`
- `pytest -q` → `1527 passed, 1 skipped in 59.74s`
- 舊 rationale 記憶體反例 → `schema_errors=[]`、anchor `true`、scanner class `b`
- 全程唯讀；未改 repo、未合併、未動 Project、未執行寫入型 `wfcli`。

## 重審入口

下一輪只需 R1 回歸新增 test delta，R3 重驗這一支精確 regression 的正例與舊 rationale 負控。inventory 現值、其餘 204 claims、單一 predicate、R19 兩反例、occurrence／load／fence、P1-33、R2、R4 不重開。


## Comment 5480809304 · 2026-08-31T15:48:38Z

# WF-REDESIGN1 規劃階段跨家族查核裁決（R22）

- 被審 SHA：`b5dd91249473700e8ef6e7c725588b3241a81f31`
- 承接：issuecomment-5480637139
- 裁決：**APPROVE（規劃審通過）；R1、R3 通過，P1-38 關閉；P1-33、R2、R4 不重開**
- 查核者身分自述：Codex（OpenAI 家族），實際模型：**GPT-5**，session `01a052f2-4564-7dd1-8a6c-bf46423a8c58`
- 該則 timestamp：`2026-08-31T23:48:38+08:00`

## R1 前提回歸：過

1. HEAD、`origin/main` 與父卡 spec 基線均為完整被審 SHA；worktree clean。
2. `f277b2f..b5dd912` 恰一個 commit；只修改 `cli/tests/test_prose_number_scan.py` 一檔、增加一支測試，inventory 與 scanner 均未改；與揭露一致，`git diff --check` 無輸出。
3. delta 未改四波五卡、owner、replacement rows、硬依賴鏈、tier、aiwf／cpbl 邊界或任何 production 行為。

## R2：不重開

本 delta 未改 owner、resource claims 或互斥語意；沿用既有通過結果。

## R3 精確 regression：過

1. `test_w2b_six_claim_is_pinned_to_negation_form` 由含 `⛔ 非六檔` 的現行原句反查 SHA，再以 path＋line hash 定位 inventory entry，沒有依賴會漂的行號。
2. 正例要求該 entry 恰一筆 token `六` claim，且 rationale 同時含 `非六檔` 與 `否定式`；現行否定式 rationale 通過。
3. 負控使用 R21 變異的原始舊錯值 `「六」＝該段枚舉之基數（行內列明成員）`，明確斷言不得通過同一 predicate。
4. 獨立變異重跑：現值正例通過；將暫存 inventory 的該 claim 改回舊錯值後，同一測試拋 `AssertionError`。這證明新增測試會在修正前失敗，⛔ 非只驗現值綠燈。
5. scanner 六項缺口全零；49 專測與 1528 全套 tests 均綠。R21 唯一 blocking 已有可重跑防復發證據，P1-38 可關閉。

## R4：不重開

本 delta 未觸及 journal、remote write、read-back、path confinement、DraftIssue、CONTRACT_TOOL_RECONCILE 或 cutover／回退；P1-33 維持關閉。

## 級別與能力層級：無回歸

本 delta 未改風險、影響範圍或可逆性；既有 W0／W2A T4、W1／W2B／W3′ T3 與跨家族查核要求不變。

## Findings

### WF-REDESIGN1-P1-38（關閉）

- severity: moderate（歷史）
- blocking: false
- evidence: inventory 現值已在 R21 修成否定式；本輪新增定點 regression，現值通過、R20/R21 舊錯 rationale 變異確實失敗；scanner、專測與全套 tests 全綠。
- disposition: **resolved／closed**。沒有新增 finding，無後續修正入口。

## self_run

- HEAD／origin/main／父卡基線 → `b5dd91249473700e8ef6e7c725588b3241a81f31`
- commit count → 1；改檔 → 1（tests only）；新增 → 19 lines；`git diff --check` → 無輸出；worktree clean
- inventory 未改 → 127 entries／205 claims
- 現值正例 → passed
- 暫存 inventory 改回舊 rationale → `AssertionError`，failed as required；還原後現值仍 passed
- `python3 scripts/prose_number_scan.py` → `{"total":202,"unclassified":0,"dead_entries":0,"invalid_entries":0,"claims_mismatch":0,"uncovered_claims":0,"extra_claims":0}`
- `pytest tests/test_prose_number_scan.py -q` → `49 passed in 0.09s`
- `pytest -q` → `1528 passed, 1 skipped in 69.75s`
- 全程唯讀；未改 repo、未合併、未動 Project、未執行寫入型 `wfcli`。

## 結論

R22 重審入口的正例、舊值負控與 mutation proof 均成立；前輪唯一 blocking 已關閉。被審規劃產出物於本 SHA **通過規劃審**。


## Comment 5511640720 · 2026-09-02T15:00:46Z

## PM 量測登記 · 指標③ 與痛點③ 方向相反（2026-09-02）

**轉錄來源自述**：本則由 PM session `cc0a7952-07a5-4978-8d03-8b5f48fbc690` 撰寫；GitHub token 為 `ruan6047`。⚠️ **本則⛔ 非裁定、⛔ 非查核 finding**——是 PM 對本 Initiative 預登指標的量測登記，供結案與回顧採用。方向由需求方於同 session 逐字指出（「目前感覺是好像有點偏離目標」），量測由 PM 執行。

### 一 · 量測（三元組：量測日 2026-09-02／量法＝`cli/src/**/*.py` 行數，與 discovery brief 指標③ 同一量法／機制齡＝基線登記於 2026-08-30）

| 時點 | `cli/src` 行數 | 對基線 |
|---|---:|---:|
| discovery brief 預登基線（2026-08-30） | **17,194** | — |
| `WF-REDESIGN-W3` 開工前（`7d79806`） | **18,413** | +1,219（+7.1%） |
| `WF-REDESIGN-W3` 交付後（`4a8113eb`） | **19,828** | **+2,634（+15.3%）** |

**歸屬**：+1,219 全部來自單一 commit `f656a678…`＝**W1（`ruan6047/ai-workflow#217`）**（PM 以 `git log $BASE..HEAD -- cli/src` 逐 commit 量，W2A／W2B 對 `cli/src` **零淨增**）；+1,415 來自 W3′（逐 AC：AC7 +143／AC5 +385／AC6+AC8 +481／AC1 +167／AC3-FIX +163／AC2(doctor) +6／AC3-INV 0）。

⚠️ 指標③ 的另一半「拒收點數」**⛔ 不可重現**：基線登記為 144，PM 以 4 種關鍵字變體在 2026-08-30 當日 commit 上重量得 88／317／229／88，⛔ 無一為 144。可重現的代理（`return <非零>`）為 88（08-30）→ 95（09-02 開工前）。

### 二 · 與痛點③ 的關係

父卡核心痛點逐字含需求方 2026-08-29 原話第三句：「**目前框架內ＣＬＩ有點過量尤其是很多不該由ＣＬＩ處理的都變成由ＣＬＩ處裡**」。

⇒ **指標③ 與該痛點方向相反，且差距為 +15.3%。**

### 三 · 成因（PM 分析，⛔ 非裁定）

四波五卡的內容本質上皆為**新增機制**：W0 conduct 生效／W1 收件閘＋開卡表單／W2A canonical＋stage-rules／W2B 交接範本／W3′ CLI 內部改造。

**唯一以「減」為目標的是 W3′ 的 AC3，而其天花板已實測**：`doctor.py` 全檔 3,039 行中 **1,524 行不是函式**；43 個模組層函式經三道判準（跨模組相依／全域狀態／反方向常數共用）只抽得出 **6 個／127 行**；委派層本身 105 行 ⇒ 淨減 **33 行（−1.1%）**，且**執行時邊界⛔ 未改變**（`importlib` 載回，那些行照樣被載入執行）。

⇒ ⛔ **不宣稱這是任何一張子卡的執行失誤**——五張卡的每一條驗收皆有需求方或 canonical 的明文指名。這是**拆卡定稿時的結構性事實**。

### 四 · 需求方 2026-09-02 另給出的方向（供回顧採用）

需求方逐字：「第一當任務完成到狀態完成時。由ＣＬＩ提供對應的樣板　由ＡＩ提交報告。ＣＬＩ檢查欄位是否有填。如果沒填完整退回　確認有填後　將報告轉交給下一位執行者　繼續處理。第二件事　處理ＧＩＴＨＵＢ相關的操作。第三件事情是　提供一些必要資訊但**不涉及文本辨識**」

PM 量測（2026-09-02，量法＝對 `cli/src/**/*.py` 剝註解行後計四個 pattern：`\.splitlines\(`／`` ``` ``／`startswith\(\s*["']#`／`re\.(search|match|findall|finditer|compile)\(`）：**自寫文本解析 154 處**；前五檔 `card.py` 40／`review.py` 34／`doctor.py` 27／`resources.py` 13／`cleanup.py` 7 佔 **121/154（79%）**，共 **8,948 行 ＝ `cli/src` 的 48.6%**。

⚠️ ⛔ 不宣稱那 8,948 行全是文本辨識——解析處數是**代理指標**，⛔ 非該行為的行數；亦⛔ 未區分「解析卡面（無可避免）」與「反推狀態（可用結構化欄位取代）」。

⇒ 詳見 `ruan6047/ai-workflow#221` 的 `issuecomment-5511128295`。

### 五 · 處置建議（PM 提，⛔ 未執行）

本卡驗證逐字已有「**回顧移交切換 Initiative（觸發＝cutover 後第 30 張常態卡；fail-safe 2026-10-31）**」，而**指標③ 正是回顧要對照的三指標之一** ⇒ 本項為回顧的輸入，⛔ 不需在任何子卡內解決。

⚠️ 併記一項需求方應知的連帶：切換 Initiative 的內容（36 張舊卡逐張處置／57 份 spec 檔封存／13 個 `db:` 宣告正規化／15 張 write+ 補宣告，數字取自決議 `:97`）同樣以**新增工作**為主，⛔ 非減 CLI ⇒ 若指標③ 是回顧的紅線，該波的方向須先裁定。


## Comment 5525594219 · 2026-09-03T12:16:15Z

**轉錄來源自述**：本則由 PM session `cc0a7952-07a5-4978-8d03-8b5f48fbc690` 撰寫；GitHub token 為 `ruan6047`。⚠️ **需求方已就本卡（T4）作出明確人工 sign-off**（原話逐字：「T4 結案 sign-off，照做」）——停下條件 4「T4 紅線卡人工 sign-off 不可省略」因此**由需求方本人解除，⛔ 非 PM 直行**。報告全文由 PM 起草、需求方 sign-off，⛔ 非需求方自撰。

## 結案報告 · `WF-REDESIGN1`（Initiative 父卡，2026-09-03）

⚠️ **本卡級別 T4 ⇒ 停下條件 4 成立：「T4 紅線卡——人工 sign-off ⛔ 不可省略」。PM 直行授權⛔ 不適用。** 本則為 sign-off 前的呈報；**⛔ 未經需求方 sign-off 前，PM ⛔ 不跑任何 handoff。**

### 信封一 · 卡與身分
卡ID `WF-REDESIGN1`（`ruan6047/ai-workflow#177`）　級別 **T4**　Initiative —（本卡即父卡）　階段 **需求**　輪次 **0**　交付狀態 `💡需求`　部署狀態 `—不適用`　`branch`／`worktree` **皆 `None`**
from `claude-fable-5@Claude Code (PM)` → to `ruan6047`

### 信封二 · 身分自述
GitHub 帳號 `ruan6047`　session ID `cc0a7952-07a5-4978-8d03-8b5f48fbc690`　訊息定位 ⚠️ **未取**（本 session 取不到自己的 `uuid`）⇒ **驗不了，⛔ 不編造**

### 信封三 · 機械指令
| # | 指令 | rc | 觀察到的輸出 |
|---|---|---:|---|
| 1 | `wfcli snapshot`（Initiative 過濾） | 0 | W0／W1／W2A／W2B／W3 **五張全 `🏁完成`**；父卡 `💡需求` |
| 2 | `gh issue view 177 --json body`（Log 解析） | 0 | 43 條 Log：**`amend` 42 筆＋`open`；`handoff` 命中 0** |
| 3 | `gh issue view 222 --json state` | 0 | `[OPEN] [清單] 切換 Initiative` ⇒ AC2 的清單項**已建立** |
| 4 | `handoff … --next-stage release`（零寫入探針） | 2 | 階段欄逐字「需求」⇒ 8 族清冊；**⛔ 無前身交付狀態閘門擋 release** |
| 5 | `snapshot` 欄位檢查 | 0 | 含 `spec_text`／`spec_version`／`phase`／`brief` ⇒ 假設 4 的對沖已落地 |

### 信封四 · 已知未驗項
| # | 未驗項 | 分類 | 原因 |
|---|---|---|---|
| 1 | 觀察者效應是否成立 | **刻意不驗** | 構造上無法量測；回顧點已釘死觸發條件 |
| 2 | 「§0 重寫會變短」「card.py 砍半」 | **沒去驗** | ⛔ 未逐項對照該兩處；只有全域 LOC 反向證據 |
| 3 | userContentEdits 的**保存期** | **驗不了** | 平台未文件化；只做了對沖 |
| 4 | 三條 journal／epoch 假設 | **沒去驗** | 隨 AC1 拆出至 `#238`（OPEN），**⛔ 未 spike** |
| 5 | 五張子卡的守衛全量複跑 | **沒去驗** | PM 全程只複跑 pytest 與抽驗，其餘為執行者與查核者自述 |
| 6 | 本報告的訊息 `uuid` | **驗不了** | 同信封二 |

---

### ⭐ 驗證欄 · discovery brief 八條待驗證假設的逐項處置

| # | 假設（brief 逐字） | 處置 | 依據 |
|---|---|---|---|
| 1 | 觀察者效應無法量測——結案報告閘是對它的下注，回顧點驗 | **延後**（觸發已釘死：cutover 後第 30 張常態卡結案；fail-safe `2026-10-31`） | 本 Initiative 期間結案報告閘**實跑 5 次**（W0–W3）⇒ **注已下、⛔ 效果未量** |
| 2 | 「§0 重寫會變短」是推測；「card.py 砍半」是估計 | ⚠️ **降級**——⛔ 不宣稱成立 | W3 實測 `cli/src` **17,194 → 19,828（+15.3%）**、`doctor.py` **3,039 → 3,006（−1.1%）** ⇒ **方向與估計相反或遠低**。⛔ 未逐項對照 §0 與 `card.py` 本身 |
| 3 | PM 對照能否穩定抓住值域錯誤——無基線，施工期觀察 | ⚠️ **降級**——施工期已結束，**觀察資料是負面的** | W3 一卡內 PM 即：逐則裁定被推翻 **10/13**／59 列對帳誤判 1 則／用 AST 衍生欄位畫自己的母體邊界／**三次讀截斷視圖就下結論**。⇒ **⛔ 不得宣稱 PM 對照穩定** |
| 4 | userContentEdits 長期保存未文件化——每日 snapshot 補規格節為對沖 | **對沖已落地**；原假設**仍未驗** | W3 AC5 交付後 `snapshot` 含 `spec_text`／`spec_version`／`phase`／`brief`（PM 實測欄位存在）。⚠️ 保存期本身**⛔ 仍驗不了** |
| 5 | 刪「有值」SINGLE_SELECT 的行為未實測——切換 Initiative 前置拋棄式 project 實測 | **延後至 `#222`** | `[OPEN] [清單] 切換 Initiative` 已建立 |
| 6 | epoch＋dual reader 的部署可行性——W3′ 執行期 spike | ⭐ **延後至 `#238`，⛔ 未 spike** | AC1（persistent Log writer sink）經需求方 `2026-09-02` 裁定**拆出本卡射程** ⇒ 綁在 AC1 上的 spike 隨之未做 |
| 7 | journal 多 session 同時 retry 同 op 的行為——未 spike | **同 6，延後至 `#238`** | 同上 |
| 8 | reader 按 op id 去重＋corruption gate 的實作可行性——W3′ 執行期第一步 | **同 6，延後至 `#238`** | 同上 |

⚠️ **6／7／8 三條的處置是「延後」⛔ 不是「已驗證」**——它們原本掛在 W3′ 執行期，而 W3′ 的 AC1 被裁定拆走，**三條 spike 因此一條都沒做**。

---

### 1 · 痛點 → 處置
父卡痛點＝框架重整。**四波五卡全數結案**（W0／W1／W2A／W2B／W3 皆 `🏁完成`）。⚠️ **本 Initiative 交付＝框架就緒，⛔ 不切換**——看板語彙切換歸 `#222`。

### 2 · 裁決摘要（blocking 清零）
父卡本身**⛔ 無查核輪**（T4 但從未進審核階段）。子卡最終裁決：W0／W1／W2A／W2B **皆已結案**；W3 **R7 `APPROVE`／`core_pain_resolved: yes`／findings 0**。⇒ **父卡層級⛔ 無 blocking finding**。

### 3 · merge SHA ＋ CI 指標
父卡 AC3 逐字「⛔ 不自產碼與條文」⇒ **本卡⛔ 無自己的 merge SHA**。子卡最後一顆：W3 的 `aab7bf0918708f8280f8cd7472d070a8e5116628`（PR `#241` MERGED，`tests` 綠於合併結果）。

### 4 · 四道停下條件逐項
| # | 條件 | 本卡狀況 |
|---|---|---|
| 1 | blocking 未 resolved | **未成立** |
| 2 | CI 非綠或狀態不符 | **未成立**（本卡無碼；子卡 CI 綠） |
| 3 | 分支 BEHIND 且衝突 | **未成立**（`branch`／`worktree` 皆 `None`） |
| 4 | **T4 紅線卡** | ⛔ **成立**——**人工 sign-off 不可省略。本報告即為 sign-off 前的呈報。** |

### 5 · 失誤登記與未驗清單（逐字轉錄）
⭐ **父卡層級的失誤，逐字**：

> **父卡的階段軸全程未動。** 43 條 Log 全為 `amend`（42 筆）＋ `open`，`handoff` **命中 0**，交付狀態自開卡至今為 `💡需求`、iteration `0.0`。而本卡 **AC3 逐字要求「子卡在飛期間父卡停『執行／進行中』追蹤」** ⇒ **卡面要求執行／進行中，實際停在需求。** 五張子卡跨四天、七輪查核、20 個 commit 的整段期間，**父卡狀態面⛔ 未反映任何一件事**。

⇒ ⚠️ **這是 AC3 未被遵守的實例**，⛔ 不是紀錄疏漏。**PM ⛔ 不事後補一個當時沒發生的狀態轉移**（與 W3 的 R3 那件同一條線：⛔ 不回填）。

子卡層級的失誤登記（執行者 18 條 #30–#47、PM 12 條）**逐字轉錄於 `#221` 的結案報告** `issuecomment-5525404365` §5，⛔ 本則不重述。

### 6 · 清單收斂核對
本 Initiative 期間建立且**⛔ 全部未關**：`#222`（切換 Initiative，AC2 指名）／`#238`（persistent Log writer sink，承接假設 6/7/8）／`#239`（`assign --status` 無 choices）／`#240`（write-set 與記錄檔分離）／`#242`（`BriefError` 不在 `KNOWN_ERRORS`，條件 2 待第二 PM Codex 裁決）。
⇒ **逐項留著的理由**：`#222` 是 AC2 的交棒對象、**本 Initiative 刻意⛔ 不切換**；其餘四項皆為施工期撞到的獨立缺陷，⛔ 無一被本 Initiative 涵蓋。

### 7 · 翻案把手
父卡**⛔ 無自己的碼** ⇒ ⛔ 無 `git revert` 對象。實質翻案＝revert 五張子卡各自的 merge SHA（W3 為 `git revert -m 1 aab7bf09…`）。
⚠️ **不可逆動作已發生於子卡層級**：五張子卡的 Issue 皆已 CLOSED、分支與 worktree 已刪。⇒ **碼可 revert，帳面須人工復原。** 裁決層面走 `review-correction`。

### 8 · 注意事項回應清冊（`P-結案-01`–`06`）
| 編號 | 回應 |
|---|---|
| `P-結案-01` 信封四段齊全 | 已遵循 |
| `P-結案-02` 未驗項已三分類編號化 | 已遵循 |
| `P-結案-03` 七段齊全且在一屏內 | **發現：七段齊全，⛔ 不在一屏內**——八條假設逐項處置為驗證欄硬要求，與「一屏」衝突；PM 選擇完整。如判違約請退回並指定取捨 |
| `P-結案-04` 失誤登記與未驗清單為逐字轉錄 | 已遵循 |
| `P-結案-05` 清單收斂已逐項核對 | 已遵循 |
| `P-結案-06` 翻案把手跑得出來 | **發現：本卡無自己的碼 ⇒ 無 revert 對象**；實質把手在子卡層級且帳面須人工復原，已於 §7 列出 |

---

## ⛔ PM 需要你做的一件事

**對 `WF-REDESIGN1`（T4）的結案做人工 sign-off。**

sign-off 後 PM 會跑：`wfcli handoff WF-REDESIGN1 --next-stage release`（**⛔ 不帶 `--repo-path`、⛔ 不帶 `--cleanup`**——`branch`／`worktree` 皆 `None`，帶了會被 `handoff_cmd:1153` 拒）。該路徑會把「**收尾清理未執行**」寫進卡上留痕，**那是設計好的分支、⛔ 不是繞過**。

⚠️ 封存同 `#221`：**`wfcli` ⛔ 無封存動詞** ⇒ **⛔ 不封存**，理由見 `#221` 的 `issuecomment-5525444997`。


---

## ⚠️ sign-off 後的執行結果（PM 補記）

`wfcli handoff WF-REDESIGN1 --next-stage release` **rc=0**，狀態 → **`🏁完成`**。
- 踩坑族清冊（離開「需求」，8 族）：已檢查 2／**發現 6**
- 注意事項回應清冊（離開「需求」，15 條）：已遵循 8／不適用 2／**發現 5**

⚠️ **CLI 印出的警示，逐字保留、⛔ 不略過**：

> 未帶 `--cleanup` 的 release 只寫狀態面。worktree 與分支（權威清單 `templates/worktree-lifecycle.md` 第 2 步）不會被清理，而終態已經寫下去了——依 `WF_CLEANUP_GUARD1` 的分類，**這是 `illegal_terminal_before_cleanup`**。守衛不自動修復非法態，**事後再補 `--cleanup` 會被擋**，屆時只能人工收尾。

⇒ 本卡因此處於**守衛分類上的非法終態**。⚠️ 但本卡 `branch`／`worktree` **皆 `None`** ⇒ **⛔ 沒有任何殘留物可清**——該分類是**形狀上的**，⛔ 不是真有未清理的 worktree 或分支。**⛔ 不得由「rc=0」推出這個警示不存在。**

### `F-需求-01`–`15` 的五條「發現」（逐字）

| 條 | 回應逐字 |
|---|---|
| `F-需求-01` | 發現：卡面 open 行為「2026-08-30T21:24:09+08:00 open by Claude Opus 5@Claude Code (PM)」，⛔ 未載 `--from-issue` 來源；本卡開卡早於 W1 交付「清單項升級為唯一路徑」⇒ PM ⛔ 無法從卡面確認它由清單項升級。處置：如實登記，⛔ 不宣稱已遵循 |
| `F-需求-02` | 發現：同 01，⛔ 無可指的清單項原文可比對是否逐字沿用。處置：如實登記 |
| `F-需求-04` | 發現：卡面與 Log ⛔ 無查重關鍵字留痕。處置：如實登記，⛔ 不補寫 |
| `F-需求-12` | 發現：本卡表單由 PM 寫，而卡面與 Log ⛔ 無第二 PM（canonical `AI_WORKFLOW.md:14` 明定為 Codex）的 ④ 檢查留痕。處置：如實登記 |
| `F-需求-15` | 發現：卡面階段計畫的 stage 值以 JSON 承載，PM 對本卡的 grep 未取到節名對照；⛔ 未逐字核對節名＝階段名。處置：如實登記，⛔ 不宣稱已核對 |

⚠️ **五條皆為開卡當時（2026-08-30，另一個 PM session）就未做的事** ⇒ **PM ⛔ 不補寫**——補寫即回填，與本報告 §5 對 AC3 的處置同一條線。

## 四波五卡 Initiative 最終帳面

| 卡 | 狀態 | 封存 |
|---|---|---|
| `WF-REDESIGN-W0` | 🏁完成 | ⛔ 未封存 |
| `WF-REDESIGN-W1` | 🏁完成 | ⛔ 未封存 |
| `WF-REDESIGN-W2A` | 🏁完成 | ⛔ 未封存 |
| `WF-REDESIGN-W2B` | 🏁完成 | ⛔ 未封存 |
| `WF-REDESIGN-W3` | 🏁完成 | ⛔ 未封存 |
| **`WF-REDESIGN1`（父卡）** | **🏁完成** | ⛔ 未封存 |

⚠️ **全部未封存**：`wfcli` 的 11 個動詞⛔ 無封存，`archiveProjectV2Item` 在 `cli/src` **0 命中** ⇒ 照 `closeout.md` 做封存必須繞過唯一寫入通道、踩 `cli/README.md` 紅線 1。需求方裁定⛔ 不封存，理由見 `#221` 的 `issuecomment-5525444997`。

