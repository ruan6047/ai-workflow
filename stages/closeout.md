---
name: closeout
when: 卡在結案階段：合併、收尾、裁定單、封存、停止
non_scope: ⛔ 不寫裁定單欄位（住 core/handoff.md §3）；⛔ 不寫部署與維護（住模組）
last_confirmed: 2026-09-05
---

# 結案階段

## 1 · 目標與產出

- 交出 main 上的合併 SHA、CI 綠、裁定單（結案確認類）、終態（完成或停止）＋封存。
- ⛔ 不把合併當結案。
- 每次結案都做封存。

## 2 · 進入／離開條件

- 從最後一個階段待確認經 ⑤ 過後進入（`core/state-machine.md`）；研究模組的不可判定亦可進入。
- 從結案／待確認 `move` 到完成（印 PR 與分支狀態）或停止（`--ruling` kind=stop）才離開；兩者皆封存，⛔ 無出邊。
- 搬檔進 `archive/` 前先改指向它的檢查或測試，同一 PR 進場；⛔ 不留一個會 `FileNotFoundError` 的檢查。
- 停止後要復活就開新卡；撤銷⛔ 不在本階段做（需求階段）。

## 3 · 狀態 delta

- 結案階段加終態 停止；結案階段無 待辦、進行中。

## 4 · 階段內迴圈

- ① `notes --stage 結案` ② PM `brief --for closeout` 組裁定單 CLI 段 ③ PM 填人填段、需求方讀 ④ 需求方確認或退回補驗 ⑤ `move` 到完成或停止。
- 常態由 PM merge：APPROVE＋裁決完整時直行 merge→收尾；四停下條件任一成立即停下請示需求方：blocking 未 resolved、CI 非綠或 merge 後狀態不符、分支落後且衝突、T4。
- 合併方式依專案層 `merge_method`（`core/platform.md` P3）；⛔ 不用 `gh pr update-branch`，分支更新走本地 rebase。
- PR body ⛔ 不寫 `Closes #N`；只由 `move` 到終態關 issue。
- 清單收斂核對：`list_convergence` 逐項確認真解決才關。
- 分支在終態刪除；保留要寫明理由進卡面。
- 事後查核（碼已進 main 才審）只當違規補救，⛔ 不當正常路徑。
- 事後查核發現缺陷時，是否回退 main 交需求方裁定；修復卡用 `<原卡>-FIX<n>`。

## 5 · 各角色做／⛔ 不做

- PM：merge、收尾、組裁定單、封存；⛔ 不裁定停止。
- 需求方：讀裁定單、確認或退回、裁停止；⛔ 不代改。
- 執行者：不在本階段。
- 查核者：不在本階段。

## 6 · 注意事項

- F-結案-01：進入完成前印的 merge SHA 是否 main 祖先、CI 狀態，紅即停。
- F-結案-02：終態才釋放宣告的資源。
- F-結案-03：進 main 未結案的卡仍算現役。

→ [archive/rules-2026-09/stage-rules/closeout.md](../archive/rules-2026-09/stage-rules/closeout.md)、[archive/rules-2026-09/templates/closeout-report.md](../archive/rules-2026-09/templates/closeout-report.md)、[archive/issues/025.md](../archive/issues/025.md)、[archive/issues/220.md](../archive/issues/220.md)
