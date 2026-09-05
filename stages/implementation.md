---
name: implementation
when: 卡在執行階段：派工、實作、交回交回單
non_scope: ⛔ 不寫執行者的跨階段紀律（住 roles/executor.md、roles/conduct-common.md）；⛔ 不寫交回單欄位（住 core/handoff.md §2）
last_confirmed: 2026-09-05
---

# 執行階段

## 1 · 目標與產出

- 交出分支上的來源 SHA＋交回單（`json wf-return`，`role=executor`）＋自測證據。
- 只推 commit 沒交回單時留在進行中，⛔ 不轉待確認。

## 2 · 進入／離開條件

- 從規劃階段離開後進入（T0／T1 由需求直通）；`move` 到進行中時 iteration +1、清 `source_sha`、寫 `branch`。
- 交回單經 `review` 貼出、PM 判完整性與 R1 R2 過才離開 → 審核階段待辦。
- 執行者失聯時把卡留在進行中；PM `move` 到待確認再退回、再派（iteration +1），或另派一實體以 `role=executor` 交回，`mistakes` 每則 `what` 起首逐字「非本人自評」；分支未 push 則走阻塞（`wf-ruling` kind=block）。

## 3 · 狀態 delta

- 無。

## 4 · 階段內迴圈

- ① `notes --stage 執行` ② PM `brief --for executor`，人填段寫寫入授權、唯讀範圍、實際模型 ③ 執行者推分支、`review --file --role executor` 貼交回單 ④ PM 判缺段、格數、值域與 R1 R2 ⑤ PM `move --source-sha` 到待確認，再 `move` 到下一階段或退回。
- 交回單的來源 SHA 用交回當下的分支頭；交回後再 commit 就再交一次。
- 修缺陷先看回歸測試紅，再修綠。
- 分支更新走本地 rebase＋`--force-with-lease`（已被引用的 SHA 除外，`roles/executor.md` §2）。

## 5 · 各角色做／⛔ 不做

- 執行者：實作、自測、自評、交回；⛔ 不 merge、⛔ 不自審。
- PM：組派工單、判交回單完整性；⛔ 不判碼對錯、⛔ 不代寫執行者自評。
- 需求方：裁授權缺口；⛔ 不代改分支。
- 查核者：不在本階段。

## 6 · 注意事項

- F-執行-01：一個 commit 做一件事；⛔ 不混入無關重構或依賴升級。
- F-執行-02：宣稱可防回歸的測試先對缺陷版本跑紅。
- F-執行-03：新 worktree 先建全套測試基線。
- F-執行-04：每筆驗證標註環境。
- F-執行-05：讓 artifact 在交付 SHA 可重現：產生工具與 artifact 同一 commit；自指命中明列，⛔ 不偷偷排除。
- F-執行-06：交回前對照 `git diff --name-status` 修正資源宣告的漏列交付檔、宣告過寬、不存在路徑。

→ [archive/rules-2026-09/stage-rules/implementation.md](../archive/rules-2026-09/stage-rules/implementation.md)、[archive/rules-2026-09/templates/delivery-report.md](../archive/rules-2026-09/templates/delivery-report.md)、[archive/issues/219.md](../archive/issues/219.md)
