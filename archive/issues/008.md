# #8 WF-22-CLI3 wfcli review 子命令：self_run/core_pain_resolved 機械強制
- state: closed  created: 2026-08-05T13:51:14Z  closed: 2026-08-06T03:19:35Z
- url: https://github.com/ruan6047/ai-workflow/issues/8
- comments: 4

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
- 執行：待指派　查核：待指派
- Initiative：WF-22　spec 基線：canonical v2 §5.2＋templates/review-prompt.md（WF-22-CANON1 交付）
- DB：db_scope=none
- 服務的原始目標：查核契約機械強制——不合格式的裁決在寫入通道就被拒

## 簡介
<!-- card-brief:begin -->
新增 wfcli review 子命令，把查核輸出契約（review_result、findings schema、self_run 非空、core_pain_resolved）從紙面規則變成寫入通道上的硬拒，並與 handoff 整合使裁決落 Issue 留言＋看板狀態轉換——不合格式的裁決寫不進去，不再靠人工核對。**適用時機**：要改 review 事件的結構化欄位或其驗證器時；或要查「自由文字 REJECT 為什麼會 fail」的實作依據時。⛔ 非射程：刻意不實作 accepted 標記、attempt_id 去重、counts_toward_escalation 推導與 checkpoint 觸發——那屬 lifecycle writer 職權，由 WF-22-CLI4（aiwf#9）承接，本卡不做半套。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：查核輸出契約（self_run 必填、無 self_run 的 APPROVE 無效）只有紙面規則，wfcli 無 review 子命令可機械擋——依賴人工核對

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] wfcli review 子命令：驗結構化欄位（review_result/findings schema/self_run 非空/core_pain_resolved），不合即拒
- [ ] 與 handoff 整合：review 裁決落 Issue 留言＋板狀態轉換

## 驗證

- [ ] cli 測試套件覆蓋合格/不合格樣本
## Log

- 2026-08-05T21:51:12+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-06T02:10:19+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree ai/opus-5/WF-22-CLI3 @ .claude/worktrees/wf-22-cli3-execution；交付狀態 🚧進行中。
- 2026-08-06T02:35:22+08:00 handoff by wf-cli → owner Codex（跨家族查核）；iteration 0；SHA f180659d41fe2daf7f359883281d6d116857e8b0；證據 review 子命令＋164 tests；八項邊界裁量已標記待需求方；詳 #8 交付留言。
- 2026-08-06T11:02:51+08:00 handoff by wf-cli → owner Codex（跨家族查核 R2）；iteration 0；SHA 0c3a427c6bee87c3d3252f445d23ca1e88f8a3bb；證據 R1 minor＋兩硬拒裁決實作；170 tests；詳 #8 留言。
- 2026-08-06T11:19:45+08:00 handoff by wf-cli → owner ruan6047；iteration 0；SHA 0c3a427c6bee87c3d3252f445d23ca1e88f8a3bb；證據 merged＋#8 closed；review 驗證器生效。
- 2026-08-26T21:55:27+08:00 amend by wf-cli（op 9cef2599）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:52661bca4da7d568f58ea0ce7d3ad29492550bd4c8f95b86a8865c329ef4e42f (678 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5195763517 · 2026-08-05T18:35:10Z

## 交付（2026-08-05 晚，執行者 Claude Opus 5）

最終 SHA `f180659d41fe2daf7f359883281d6d116857e8b0`。`cd cli && uv run pytest` 116→164 全綠（新增 48）、ruff 乾淨、寫入面全在 `file:cli/`。

- **契約驗證 fail-closed**：review_result 封閉列舉／core_pain_resolved 必填／self_run 逐項非空／findings 八欄＋finding_id 去重；**無 self_run 的 APPROVE exit 4**（訊息引 canonical §5.2，零遠端寫入）；`core_pain_resolved: no` 不得 APPROVE（第一判準否決權）；writer-only 欄位警示忽略。退出碼分級 2/3/4（4＝review-invalid 依 §1 留 🔍待查核不計 iteration，刻意什麼都不寫）。
- **handoff 整合**：留言（含 attempt_id）→板狀態 ✅通過／↩退回→body Log 一行；**iteration/owner/交接一律不碰**（遞增唯一點仍是 handoff --next-stage implementation，有測試鎖住）。
- **八項待需求方裁決**（詳交付報告與 cli/README 設計取捨節）：(1) APPROVE 含 blocking finding 警示 vs 硬拒；(2) REQUEST_CHANGES 空 findings 警示 vs 硬拒；(3) 非 🔍待查核下裁決不擋；(4) findings 鍵須顯式；(5) escalation 帳（accepted/去重/checkpoint）另卡與否；(6) 行內註解邊界（片語＋' #' 拒收防截斷）；(7) 自寫受限 YAML 子集（fail-closed vs 寬鬆解析互斥）；(8) --reviewer 自陳、跨家族獨立性留治理層。

狀態：🔍待查核（R1）。八項裁決不阻塞查核——查核以現行為準，裁決後若改硬拒屬小 follow-up。

## Comment 5199870336 · 2026-08-06T02:58:17Z

## ⚖️ 八項邊界裁決（2026-08-06，需求方）

- **改硬拒（2）**：APPROVE 含 blocking finding；REQUEST_CHANGES 空 findings——併本輪實作後小 R2。
- **維持現行（5）**：非 🔍待查核裁決警示不擋；findings 鍵須顯式；行內註解寧拒不截；受限 YAML 子集；--reviewer 自陳（跨家族獨立性留治理層）。
- **另開卡（1）**：escalation 帳（accepted／attempt 去重／checkpoint）→ WF-22-CLI4 進 Backlog。

R1 APPROVE 成立；CLI3-R1-01（README 162→164）併本輪修。

## Comment 5199897902 · 2026-08-06T03:02:42Z

## 🔧 裁決實作交付（2026-08-06，執行者）

最終 SHA `0c3a427c6bee87c3d3252f445d23ca1e88f8a3bb`（ba4e513 之上單批：README 4 檔 diff 155+/17−）。

- **兩條硬拒**（併入 validation 同一 fail-closed 路徑，exit 2、訊息各引 2026-08-06 裁決＋#8）：APPROVE 含 blocking finding；REQUEST_CHANGES 零 finding（**顯式 `findings: []` 不豁免**）。實跑證據齊。
- 實作判斷：兩條僅在 findings 解析乾淨時才判（訊息隔離，防止缺欄與衍生矛盾同時轟炸誤導），有測試鎖住。
- README：exit 2 說明、設計取捨節帶裁決日期＋連結；測試數活引用寫法經本輪驗證有效（+6 測試零漂移）。
- 164→170 全綠、ruff 乾淨、trailers 連續區塊。

狀態：🔍待查核（小 R2：兩硬拒行為＋README 一致性＋CLI3-R1-01 閉環）。

## Comment 5199996734 · 2026-08-06T03:19:34Z

## ✅ 已 merge 結案（2026-08-06，需求方授權）

merge `aa959f9`（Reviewed-by: Codex）；main 複驗 170 tests 綠；worktree 與分支已清理。**自此查核裁決入帳一律先過 `wfcli review` 驗證器**；escalation 帳最後一環在 WF-22-CLI4（#9）Backlog。
