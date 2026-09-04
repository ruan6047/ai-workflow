# WF-22-CLI4 wfcli escalation 帳承接（accepted 標記／attempt 去重／checkpoint 計數）　〔T2〕

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
- 執行：待指派　查核：待指派
- Initiative：WF-22　spec 基線：canonical v2 §5＋templates/review-escalation.md §3＋WF-22-CLI3 交付（f180659+）
- DB：db_scope=none
- 服務的原始目標：查核升級協定全鏈機械化——計數、去重、checkpoint 觸發不靠人記
- owner、worktree、iteration、交付／部署狀態、最後交接、資源宣告與 Log
  current-state 見對應 GitHub Issue／Project item（卡ID：WF-22-CLI4），不重複於此檔。

## 核心痛點

- **痛點**：escalation 計數（第三次可計退回進 checkpoint）依賴人工盯帳——review 子命令刻意不半套實作（accepted 屬 lifecycle writer 職權），機械強制缺最後一環

## 驗收條件

- [ ] accepted 標記寫入通道（lifecycle writer 語意）；attempt_id 去重；counts_toward_escalation 推導與 checkpoint 觸發警示

## 驗證

- [ ] cli 測試覆蓋計數／去重／checkpoint 樣本
