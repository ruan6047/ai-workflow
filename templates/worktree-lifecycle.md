# Worktree Lifecycle Runbook

> 此範本承載 canonical §2 第 5 點的操作細節。每個專案在 Runbook 填入實際路徑與 adapter 命令。

1. Coordinator 原子 claim 成功後才建立 `../<repo>-<卡族ID>` 與 `ai/<model@tool>/<卡ID>`。
2. 同一卡族（原卡與 `<原卡>-FIX<n>`）共用一個 worktree；修復時在其中切新分支，不另開目錄。
3. 交接前驗證：`git status` 乾淨、`HEAD` 等於已推送分支尖端；adapter 記錄 source SHA 後才可轉 `🔍待查核`。審核者不改 source branch，並在 PR／event 留 findings；若驗證命令會改動 tracked file，必須在 disposable verification worktree／container 執行。此審查沙箱無 claim、無 branch owner、用完即移除，不算卡族的執行 worktree。
4. merge 者負責收尾：先離開 worktree，合併並推送 main；卡族全數結案後才依序移除 worktree、刪本地分支、刪遠端分支。
5. claim、handoff、merge、release 後，以 `git worktree list` 對帳活卡族；不符即停止並修正 Log。

> 禁止從仍被 worktree checkout 的分支先刪 branch；禁止在 worktree 內移除自身目錄。
