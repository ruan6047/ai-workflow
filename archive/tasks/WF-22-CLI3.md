# WF-22-CLI3 wfcli review 子命令：self_run/core_pain_resolved 機械強制　〔T2〕

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
- 執行：待指派　查核：待指派
- Initiative：WF-22　spec 基線：canonical v2 §5.2＋templates/review-prompt.md（WF-22-CANON1 交付）
- DB：db_scope=none
- 服務的原始目標：查核契約機械強制——不合格式的裁決在寫入通道就被拒
- owner、worktree、iteration、交付／部署狀態、最後交接、資源宣告與 Log
  current-state 見對應 GitHub Issue／Project item（卡ID：WF-22-CLI3），不重複於此檔。

## 核心痛點

- **痛點**：查核輸出契約（self_run 必填、無 self_run 的 APPROVE 無效）只有紙面規則，wfcli 無 review 子命令可機械擋——依賴人工核對

## 驗收條件

- [ ] wfcli review 子命令：驗結構化欄位（review_result/findings schema/self_run 非空/core_pain_resolved），不合即拒
- [ ] 與 handoff 整合：review 裁決落 Issue 留言＋板狀態轉換

## 驗證

- [ ] cli 測試套件覆蓋合格/不合格樣本
