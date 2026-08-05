# Worktree Lifecycle Runbook

> 此範本承載 canonical §2 第 5 點的操作細節。每個專案在 Runbook 填入實際路徑與 adapter 命令。

1. **註冊制，不是命名慣例**（canonical §4.5）：worktree 路徑與分支名由實際建立者決定（harness 自產名亦可）。Coordinator／祕書原子 claim 成功後建立 worktree，並把**實際路徑＋分支**寫回卡面；一卡一 worktree 靠**註冊查重**。`ai/<model@tool>/<卡ID>` 與 `../<repo>-<卡族ID>` 仍是建議寫法，但**對不上不算違規，沒登記才算**。
   - **派工前必跑 `doctor` 對帳**：孤兒 worktree、死路徑、submodule 未初始化、殘留 lease 一次列出。它是唯讀報告，不自動清理。
   - `git worktree add` **不帶 submodule 內容**：新 worktree 內 submodule 目錄為空是預期，不是缺陷；需要其內容時明確初始化。
2. 同一卡族（原卡與 `<原卡>-FIX<n>`）共用一個 worktree；修復時在其中切新分支，不另開目錄。
3. 交接前驗證：`git status` 乾淨、`HEAD` 等於已推送分支尖端；adapter 記錄 source SHA 後才可轉 `🔍待查核`。審核者不改 source branch，並在 PR／event 留 findings；若驗證命令會改動 tracked file，必須在 disposable verification worktree／container 執行。此審查沙箱無 claim、無 branch owner、用完即移除，不算卡族的執行 worktree。
4. merge 者負責收尾：先離開 worktree，合併並推送 main；卡族全數結案後才依序移除 worktree、刪本地分支、刪遠端分支。
5. **收尾＝走完結案清單，不只清 worktree**（WF-18；實務曾三次停在 `📦已合併` 留下假活卡。`📦已合併` 仍算現役、仍佔資源交集檢查，canonical §4.4）：
   1. **merge → main 複驗**（lint／測試在 main 上重跑一次）**→ push**；
   2. **worktree 與分支清理**：先離開 worktree，再移除目錄、刪本地分支、刪遠端分支；
   3. **資源宣告釋放**：merge 後該卡 `file:` 資源即釋放（改宣告，或直接走完本清單把板狀態收掉）；仍待部署驗證的卡只保留部署面資源；
   4. **狀態面收尾**：Issue 留結案留言並關閉；以祕書 CLI 寫 `release` 事件，**終態**交付狀態落地（免部署卡 `🏁完成`；需部署卡 `✅已驗證` 後才 release）；
   5. 卡檔封存（`git mv` 進 archive＋索引列。注意：`git mv` 只暫存移動當下的 staged blob，先前未 add 的編輯會留在工作樹——先 commit 內容再 mv，或 mv 後重新 `git add`）；
   6. 同一變更重建 Ledger 投影（採 Issues 狀態面的專案＝重跑 snapshot，不手改）；
   7. 對帳三件套：Ledger／看板不再列該卡為現役、`git worktree list`、lease 目錄清單。
   代 Coordinator 結案的查核者同樣適用；無法完成任一項時，明確交回 Coordinator，不得默默留在中間態。
6. claim、handoff、merge、release 後，以 `git worktree list` 對帳活卡族；不符即停止並修正 Log。

> 禁止從仍被 worktree checkout 的分支先刪 branch；禁止在 worktree 內移除自身目錄。
