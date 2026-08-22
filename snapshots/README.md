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

`snapshots` 分支根目錄也有一份 `README.md`，那是**分支建立當下複製過去的**，方便直接
checkout 該分支的人。它不會自動跟著更新——**權威版本是 `main` 上的本檔**。

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
canonical `AI_WORKFLOW.md` §4.1「必須以**每日 snapshot export 回 git** 建立離線稽核副本」
想要的是「事件流」的離線副本，本目錄目前只完成了「狀態面」那一半；事件本文的離線副本
尚未有任何實作。這一段落差已回報，未包裝成已解決。

## 維運

```bash
scripts/daily_snapshot.sh --check       # 唯讀自我檢查（驗工具、憑證、真的跑一次 snapshot）
scripts/daily_snapshot.sh --install     # 安裝／重裝 launchd 排程（冪等）
launchctl print gui/$(id -u)/com.wf.daily-snapshot
cat ~/.local/state/wf-daily-snapshot/last-status.json     # 最近一次結果
ls -t ~/.local/state/wf-daily-snapshot/logs | head        # 完整輸出（留最近 30 份）
```

## ⚠️ 改 `daily_snapshot.sh` 之前：中文訊息 ＋ `set -u` 的 locale 地雷

腳本開啟 `set -uo pipefail`，而它的訊息幾乎全是中文。未加花括號的 `$VAR` 若**緊鄰非
ASCII 字元**（全形括號、中文字、`／`、`·`…），bash 3.2 在 **UTF-8 locale** 下會把該字元
的 lead byte 吃進變數名，於是 `set -u` 判定 unbound variable 並中止。

**這條在 C locale 下驗不出來**（`LANG`／`LC_ALL` 未設時就是 C，launchd 也是 C），
所以「本機跑過沒事」不構成證據——同族陷阱見 `docs/ROADMAP.md`「runner 不是 UTF-8」。
2026-08-19 實測：`0x80`–`0xFF` 共 **65** 個 byte 會被吃進變數名，涵蓋全部 CJK／全形的
lead byte（`0xC2`–`0xEF`）；`$?`／`$1`／`$#` 這類單字元特殊參數不受影響。

**不變式：具名變數展開一律寫 `${VAR}`。** 守衛（期望輸出 `0`，非 0 即回歸）：

```bash
perl -ne '$n++ while /\$[A-Za-z_][A-Za-z0-9_]*[\x80-\xFF]/g;
          END{printf "%d\n", $n||0}' scripts/daily_snapshot.sh
```

### 錯誤路徑煙霧測試（不打網路、不打 GitHub API）

受害的訊息多半在 `die()` 上，**正常流程測不到**——錯誤處理自己二次崩潰時，離開碼會從
設計值退化成 `1`，而且 `write_status` 不會執行，`last-status.json` 整份不見。所以驗收
必須**在 UTF-8 locale 下逐條把錯誤路徑逼出來**。腳本自帶兩個測試接縫讓這件事不需要
碰 GitHub：`WF_SNAPSHOT_REMOTE` 指向本機 bare repo、`WF_SNAPSHOT_STATE_DIR` 指向暫存目錄；
`wfcli` 則用一支排在 `PATH` 最前面的假 `uv` 攔掉（GraphQL request 數 = 0）。

| 逼出的路徑 | 手法 | 期望 |
|---|---|---|
| 缺工具 | `PATH` 只留 coreutils，抽掉 `git`／`uv`／`gh` | `exit 69`，印出 `找不到 git（PATH=…）` |
| 鎖被佔用 | 先 `mkdir $STATE_DIR/run.lock` | `exit 75`，印出鎖路徑 |
| snapshot 失敗 | 假 `uv` 直接 `exit 3` | `exit 78`，印出 `（rc=3）` |
| `--check` 成功 | 假 `uv` 寫出假產物後 `exit 0` | `exit 0`，印出 `產物暫存於 …` |
| push 失敗 | bare repo `chmod -R a-w` | `exit 79`，印出 commit SHA 與 clone 路徑 |

每條都要確認**離開碼是上表的值而不是 `1`**，且 `last-status.json` 有被寫出來——退化成
`1` 正是二次崩潰的指紋。

## 成本

每次執行對 GitHub GraphQL 的成本是 **6 個 request**（2026-08-19 實測，連續三次皆 6；
成本隨卡數成長，`list_items` 每 50 張卡多一頁）。
