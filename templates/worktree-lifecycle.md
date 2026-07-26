# Worktree Lifecycle Runbook

> 此範本承載 canonical §2 第 5 點的操作細節。每個專案在 Runbook 填入實際路徑與 adapter 命令。

1. Coordinator 原子 claim 成功後才建立 `../<repo>-<卡族ID>` 與 `ai/<model@tool>/<卡ID>`。
2. 同一卡族（原卡與 `<原卡>-FIX<n>`）共用一個 worktree；修復時在其中切新分支，不另開目錄。
3. 交接前驗證：`git status` 乾淨、`HEAD` 等於已推送分支尖端；adapter 記錄 source SHA 後才可轉 `🔍待查核`。審核者不改 source branch，並在 PR／event 留 findings；若驗證命令會改動 tracked file，必須在 disposable verification worktree／container 執行。此審查沙箱無 claim、無 branch owner、用完即移除，不算卡族的執行 worktree。
4. merge 者負責收尾：先離開 worktree，合併並推送 main；卡族全數結案後才依序移除 worktree、刪本地分支、刪遠端分支。
5. **收尾＝走完結案清單，不只清 worktree**（WF-18；實務曾三次停在 `📦已合併` 留下假活卡）：
   1. release 事件以**終態**交付狀態落地（免部署卡 `🏁完成`；需部署卡 `✅已驗證` 後才 release）；
   2. 卡檔封存（`git mv` 進 archive＋索引列。注意：`git mv` 只暫存移動當下的 staged blob，先前未 add 的編輯會留在工作樹——先 commit 內容再 mv，或 mv 後重新 `git add`）；
   3. 同一變更重建 Ledger；
   4. 釋放 local lease、刪分支；
   5. 對帳三件套：Ledger 不再列該卡、`git worktree list`、lease 目錄清單。
   代 Coordinator 結案的查核者同樣適用；無法完成任一項時，明確交回 Coordinator，不得默默留在中間態。
6. claim、handoff、merge、release 後，以 `git worktree list` 對帳活卡族；不符即停止並修正 Log。

> 禁止從仍被 worktree checkout 的分支先刪 branch；禁止在 worktree 內移除自身目錄。
