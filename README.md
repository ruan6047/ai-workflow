# `snapshots/` — 狀態面的每日離線稽核副本

`AI_WORKFLOW.md` §4.1／§4.3 說：事件載體是 Issue timeline ＋結構化 comment，**因其非嚴格
不可覆寫，必須以每日 snapshot export 回 git 建立離線稽核副本**。本目錄就是那句話的落點，
產生者是 [`scripts/daily_snapshot.sh`](../scripts/daily_snapshot.sh)（launchd `com.wf.daily-snapshot`，每日 10:40）。

## 產物在哪：`snapshots` 分支，不是 `main`

`main` 上的本目錄只有這份說明。**每日產物在本 repo 的 `snapshots` 孤兒分支**，路徑同名：

```
snapshots/YYYY-MM-DD/snapshot.json    # 給程式讀
snapshots/YYYY-MM-DD/SNAPSHOT.md      # 給人讀（Ledger 表格）
```

為什麼不落在 `main`：repo ruleset「main must be green」對 default branch 要求 status check
`tests`、`strict_required_status_checks_policy=true` 且沒有 bypass actor，**無人值守的
直接 push 進不去**；而 repo 的 `allow_auto_merge=false`，改走 PR 就必須由排程自己合併
PR——「機器自行 merge」在本專案的治理下是違規動作。孤兒分支同時換到三件事：與 `main`
的樹永不衝突、`[skip ci]` 不燒 CI、不會在 `wfcli doctor` 的 worktree 對帳裡長出孤兒
worktree（排程用獨立 clone，不用 `git worktree add`）。

## 怎麼稽核

```bash
git fetch origin snapshots
git log --format='%ad %s' --date=short origin/snapshots      # 每天一筆；缺哪天一眼看出來
git ls-tree --name-only origin/snapshots snapshots/          # 逐日目錄清單，缺漏＝那天沒跑
git show origin/snapshots:snapshots/2026-08-19/SNAPSHOT.md   # 取某一天的板面
```

**逐日目錄、不覆寫**，就是為了讓「哪天沒跑」不必翻 git log 就看得見——本目錄要解的病灶
正是「文件說有、機器上沒有」，偵測成本必須低到不會有人偷懶。

每一筆 commit 的訊息帶三個可稽核欄位：

```
trigger:       launchd＝排程跑的；manual＝人手動補跑的（兩者不可混為證據）
cards:         當日板面卡數
wfcli-source:  產生這份快照的 wfcli 原始碼 SHA
```

## ⚠️ 這份快照證明得了什麼、證明不了什麼

**證明得了**：某日某時，看板上有哪些卡、每張卡的 13 個凍結欄位與資源宣告長什麼樣。
拿它跟今天的 Project 對照，可以抓出「欄位被誰改過而沒有留事件」。

**證明不了**：`wfcli snapshot` 匯出的是**看板當前狀態**，**不含 Issue timeline 上的
lifecycle event 留言**。所以——**被事後編輯或刪除的結構化 comment，本快照偵測不到**。
canonical:138 想要的是「事件流」的離線副本，本目錄目前只完成了「狀態面」那一半；
事件本文的離線副本尚未有任何實作。這一段落差已回報，未包裝成已解決。

## 維運

```bash
scripts/daily_snapshot.sh --check       # 唯讀自我檢查（驗工具、憑證、真的跑一次 snapshot）
scripts/daily_snapshot.sh --install     # 安裝／重裝 launchd 排程（冪等）
launchctl print gui/$(id -u)/com.wf.daily-snapshot
cat ~/.local/state/wf-daily-snapshot/last-status.json     # 最近一次結果
ls -t ~/.local/state/wf-daily-snapshot/logs | head        # 完整輸出（留最近 30 份）
```

每次執行對 GitHub GraphQL 的成本是 **6 個 request**（2026-08-19 實測，連續三次皆 6；
成本隨卡數成長，`list_items` 每 50 張卡多一頁）。
