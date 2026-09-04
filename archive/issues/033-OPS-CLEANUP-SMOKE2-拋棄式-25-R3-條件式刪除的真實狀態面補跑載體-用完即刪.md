# #33 OPS-CLEANUP-SMOKE2 【拋棄式】#25 R3 條件式刪除的真實狀態面補跑載體，用完即刪
- state: closed  created: 2026-08-11T22:47:32Z  closed: 2026-08-11T22:49:53Z
- url: https://github.com/ruan6047/ai-workflow/issues/33
- comments: 0

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
- 執行：待指派　查核：待指派
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：讓 T4 的 sign-off 對應到本輪實際交付的碼，而不是上一輪的碼。

## 簡介
<!-- card-brief:begin -->
已完成：當一張拋棄式煙霧測試靶卡，讓 ai-workflow#25 R3 的「--force-with-lease 條件式遠端刪除」對真實 GitHub 走完一次成功刪除——先前那次真實狀態面實跑用的是 R2 的碼（b1273ab），R3 的租約路徑只在本機 bare repo 與測試中驗過。適用時機：要查 R3 租約刪除路徑是否曾在真實 GitHub 驗過時；或要找「開一張無交付價值的卡專門驗 release --cleanup」的前例時。⛔ 非射程：本卡無任何交付價值、不承載結論，唯一用途是被 release --cleanup 收掉；不改 cleanup 實作本身（屬 ai-workflow#25），成功路徑與租約拒絕路徑的觀察結果貼回 #25。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：#25 R3 把遠端刪除改為 --force-with-lease 條件式刪除，但該修法只在本機 bare repo 與測試中驗過；先前那次真實狀態面實跑用的是 R2 的碼（b1273ab），本輪的租約路徑從未對真實 GitHub 走完一次成功刪除。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:tasks/_smoke/OPS-CLEANUP-SMOKE2.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 本卡無任何交付價值；唯一用途是被 R3 的 release --cleanup 收掉。

## 驗證

- [ ] 成功路徑與租約拒絕路徑各觀察一次，結果貼回 #25。
## Log

- 2026-08-12T06:47:31+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-12T06:48:27+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code (PM)；分支worktree claude/OPS-CLEANUP-SMOKE2 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/ops-cleanup-smoke2；交付狀態 🚧進行中。
- 2026-08-12T06:49:38+08:00 handoff by wf-cli → owner 已收尾；iteration 0；SHA 701747e19761f6d543aa51ff90883f7d2ed2271a；證據 #25 R3 條件式刪除的真實 GitHub 補跑：成功路徑；收尾清理已完成（worktree 與本地／遠端分支皆已不存在）。
- 2026-08-26T21:39:31+08:00 amend by wf-cli（op d52e2572）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:8984742516e0c1a4dc2e3334da38b54336740113b7007f6cb03a1574b385dcc4 (692 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。

