---
name: closeout
when: 卡在結案階段：合併、收尾、裁定單、封存、停止
non_scope: ⛔ 不寫裁定單欄位（住 core/handoff.md §3）；⛔ 不寫部署與維護（住模組）
last_confirmed: 2026-09-05
---

# 結案階段

## 1 · 目標與產出

- 產出＝main 上的合併 SHA、CI 綠、裁定單（結案確認類）、終態（完成或停止）＋封存。
- 合併⛔ 不是結案；封存是結案的固定動作。

## 2 · 進入／離開條件

- 進入＝最後一個階段待確認經 ⑤ 過（`core/state-machine.md`）；研究模組的不可判定亦可進入。
- 離開＝結案／待確認 → 完成（`move` 印 PR 與分支狀態）或 停止（`--ruling` kind=stop）；兩者皆封存，⛔ 無出邊。
- 封存動作與釘死路徑的檢查互斥：搬檔進 `archive/` 前先改指向它的檢查或測試，同一 PR 進場；⛔ 不留一個會 `FileNotFoundError` 的檢查。
- 停止的復活＝開新卡；撤銷⛔ 不在本階段（需求階段）。

## 3 · 狀態 delta

- 結案階段加終態 停止；結案階段無 待辦、進行中。

## 4 · 階段內迴圈

- ① `notes --stage 結案` ② PM `brief --for closeout` 組裁定單 CLI 段 ③ PM 填人填段、需求方讀 ④ 需求方確認或退回補驗 ⑤ `move` 到完成或停止。
- 常態誰 merge：APPROVE＋裁決完整 ⇒ PM 直行 merge→收尾；四停下條件任一成立即停下請示需求方：blocking 未 resolved、CI 非綠或 merge 後狀態不符、分支落後且衝突、T4。
- 合併方式依專案層 `merge_method`（`core/platform.md` P3）；⛔ 不用 `gh pr update-branch`，分支更新走本地 rebase。
- PR body ⛔ 不寫 `Closes #N`；issue 關閉只由 `move` 到終態觸發。
- 清單收斂核對：`list_convergence` 逐項確認真解決才關；分支在終態刪除，保留要寫明理由進卡面。
- 事後查核（碼已進 main 才審）是違規補救，⛔ 不是正常路徑；是否回退 main 由需求方裁定；修復卡 `<原卡>-FIX<n>`。

## 5 · 各角色做／⛔ 不做

- PM：merge、收尾、組裁定單、封存；⛔ 不裁定停止。
- 需求方：讀裁定單、確認或退回、裁停止；⛔ 不代改。
- 執行者：不在本階段（代行 merge 只在需求方明確授權時，merge commit 帶 `Reviewed-by`）。
- 查核者：不在本階段。

## 6 · 注意事項

- F-結案-01：進入完成前印的 merge SHA 是否 main 祖先、CI 狀態，紅即停。
- F-結案-02：終態才釋放宣告的資源；進 main 未結案的卡仍算現役。
- F-結案-03：封存、收尾、合併前跑全套並用 repo 宣告的工具鏈。
- F-結案-04：翻案把手須可跑（`git revert <merge SHA>`）；寫不出即逐字「無把手」＋原因。

→ [archive/rules-2026-09/stage-rules/closeout.md](../archive/rules-2026-09/stage-rules/closeout.md)、[archive/rules-2026-09/templates/closeout-report.md](../archive/rules-2026-09/templates/closeout-report.md)、[archive/issues/025.md](../archive/issues/025.md)、[archive/issues/220.md](../archive/issues/220.md)
