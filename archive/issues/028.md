# #28 OPS-CLEANUP-SMOKE1 【拋棄式】#25 release --cleanup 端到端實跑載體，用完即刪
- state: closed  created: 2026-08-11T16:11:17Z  closed: 2026-08-11T16:22:28Z
- url: https://github.com/ruan6047/ai-workflow/issues/28
- comments: 0

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
- 執行：待指派　查核：待指派
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：提供一個沒有任何價值的真實卡片，讓破壞性收尾路徑可以在真實狀態面上被觀察一次；若有 bug，毀掉的是本卡自己的 worktree。

## 簡介
<!-- card-brief:begin -->
一張刻意沒有任何交付價值的真實卡，唯一用途是讓 `#25` 的 `release --cleanup` 破壞性收尾路徑（關 Issue、寫終態、刪遠端分支）在真實 Project／Issue 上被觀察一次；若有 bug，毀掉的是本卡自己的 worktree。**適用時機**：盤點卡片母體時看到它而困惑它為何存在；或要對狀態面的破壞性路徑取證而需要一個可犧牲的靶時。⛔ 非射程：本卡不交付任何功能、也不驗 `release --cleanup` 本身的實作（那屬 `#25`），⛔ 不得被當成 `docs/` 或程式碼的先例引用。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：#25 的 release --cleanup 只對『真 git ＋假 GitHub』跑過，從未對真實 Project／Issue 執行；而它會關 Issue、寫終態、刪遠端分支。T4 卡面要求最高風險項由需求方 sign-off，而 sign-off 需要觀察而非文件。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:tasks/_smoke/OPS-CLEANUP-SMOKE1.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 本卡無任何交付價值；唯一用途是被 release --cleanup 收掉。

## 驗證

- [ ] 拒絕路徑與成功路徑各觀察一次，結果貼回 #25。
## Log

- 2026-08-12T00:11:15+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-12T00:12:05+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code (PM)；分支worktree claude/OPS-CLEANUP-SMOKE1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/ops-cleanup-smoke1；交付狀態 🚧進行中。
- 2026-08-12T00:22:12+08:00 handoff by wf-cli → owner 已收尾；iteration 0；SHA 485163f0db174316bd58aa92b6f2ad169c477ccf；證據 #25 端到端實跑：成功路徑（需求方 2026-08-12 裁定 T4 sign-off 須建立在觀察上）；收尾清理已完成（worktree 與本地／遠端分支皆已不存在）。
- 2026-08-26T14:15:20+08:00 amend by wf-cli（op 4b0f5e8c）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:fdad387a6474675023a32b34b0d6e3f2b895cd0b5e60da73b250273dad7b02c1 (589 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第二批（20 張純隨機）：依 canonical §6.3 回填簡介；文字經 A5 守衛（分行字元＋1012B 上限）預先拒收檢查。

