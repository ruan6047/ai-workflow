# DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1：閘門取證

> 本檔是 `DEV-MAIN-RED-CAPABILITY-FLAGS1`（#47）核心痛點第二段的**取證紀錄**，不是建設卡的設計文件。
> 服務 `docs/ROADMAP.md` §0 目標 1（防止低級事故）。**唯一的問題**是：
> 2026-08-12 那個形狀的事故，今天會不會被機械擋下。

## 0. 一句話結論

**會。而且是伺服器端擋的，不是客戶端禮貌性拒絕。**

實測輸出（`gh api -X PUT .../pulls/74/merge`，2026-08-13）：

```
HTTP/2.0 405 Method Not Allowed
{"message":"Repository rule violations found\n\nRequired status check \"tests\" is failing.\n\n", ... ,"status":"405"}
```

這一格正是本 repo 至今缺的：`#61` 關閉時是 `DIRTY`（文字衝突），`#71` 上運作的是 `strict`
擋落後分支，**兩者都不是「紅色 `tests` 直接擋下合併」**。ROADMAP §2 先前記載的是設定面證據；
本檔以實測取代之。

⚠️ **取證範圍僅止於此。** §5 逐條列出本次**沒有**證明的東西，其中有一條是實質殘留風險。

## 1. 為什麼「任意紅色案例」不算數

2026-08-12 的事故形狀，逐字定義：

> **分支在自己的基線上測試為綠、併進 main 之後才紅。**

難點不在「讓 CI 變紅」——那太容易了，隨便寫一個壞測試就成。難點在於**綠與紅同時為真**：
分支自測是誠實的綠，合併結果是誠實的紅，而當時的放行判準（`git merge-tree` 文字比對）
看不出兩者的差別。

原始事故的解剖（見 `adfcbce` 的 commit 訊息）：

| 元件 | 8/12 事故 |
|---|---|
| 收緊要求的 main commit | `26a0149`（`open` 四個能力旗標改必填）、`d81d604`（`assign --actual-capability`） |
| 陳舊基線 | `#25` 的分支基線 `7451b72`；`git merge-base --is-ancestor 26a0149 7451b72` 為**否** |
| 碰撞的檔案 | `cli/tests/test_release_cleanup.py`（由 `#25` 的 `b1273ab` **新建**） |
| 為何自測綠 | 該檔從未見過那些必填旗標 |
| 為何 merge-tree 沒抓到 | 兩邊改**不同檔案**，文字比對無衝突 |
| 合併後的症狀 | 644 passed / **14 errors**，全部是 fixture setup 期的 argparse 必填旗標缺漏 |

## 2. 本次造的案例：同一形狀的論證

**不是模擬，是用同一個機制重跑一次。** 逐項對位：

| 元件 | 8/12 事故 | 本次取證 | 同否 |
|---|---|---|---|
| 收緊要求的 main commit | `26a0149` | **同一個** `26a0149` | ✅ 同一 |
| 分支基線 | `7451b72` | **同一個** `7451b72` | ✅ 同一 |
| `merge-base --is-ancestor 26a0149 <基線>` | 否 | **否**（實跑） | ✅ 同一 |
| 碰撞檔案 | 新建檔 `test_release_cleanup.py` | 新建檔 `test_gate_evidence_fix1.py` | ✅ 同型（皆為 main 上不存在的新增檔） |
| 缺的旗標 | `--exec-capability` 等四個 | **同樣那四個** | ✅ 同一 |
| 失敗發生的時機 | fixture／setup 期，非斷言期 | setup 期 `SystemExit: 2`，非斷言期 | ✅ 同型 |
| 失敗訊息 | `error: the following arguments are required: --exec-capability, ...` | **逐字相同** | ✅ 同一 |

### 2.1 刻意的設計：主題與旗標無關

本檔的兩個測試在驗**「`open` 把資源宣告寫進 Issue body」**與**「級別落在 Ledger 欄位」**——
與能力層級旗標毫無關係。旗標只出現在 `_open_argv()` 這個 setup 輔助函式裡。

**這一點是刻意的，也是「同形狀」的關鍵。** 若寫成「斷言 `open` 不帶旗標也能解析成功」，
那是正面測試那條剛被改掉的契約——它會紅是**同義反覆**，不是陳舊基線的碰撞。
真實事故裡碰撞永遠是**附帶的**：測試根本不知道有這個契約存在，只是照它基線上的呼叫慣例寫。

### 2.2 「分支自測綠」是實跑的，不是宣稱

在基線 `7451b72` 的工作樹上：

```
$ uv run --frozen pytest -q
294 passed in 3.88s

$ uv run --frozen pytest -v tests/test_gate_evidence_fix1.py
tests/test_gate_evidence_fix1.py::test_open_writes_the_resource_claim_block_into_the_issue_body PASSED
tests/test_gate_evidence_fix1.py::test_open_records_the_tier_on_the_ledger_item PASSED
2 passed in 0.02s
```

### 2.3 舊判準（`git merge-tree`）依然放行

```
$ git merge-tree --write-tree 78d3f80 origin/main
e17f4b31dc2f7299212199d7ce408942474576e5
exit=0   ← 0 = 無衝突
```

合併結果與 `origin/main` 的差異，恰為一個新增檔：

```
$ git diff --stat origin/main e17f4b3
 cli/tests/test_gate_evidence_fix1.py | 83 ++++++++++++++++++++++++++++++++++++
 1 file changed, 83 insertions(+)
```

**這就是 8/12 當天放行的那個判準，今天對同一形狀依然放行。** 它不是被修好的，
是被一個站在它後面的閘門攔下的。

### 2.4 合併結果紅（本機先驗，CI 獨立複驗）

以 `git commit-tree` 實體化合併結果後實跑：

```
2 failed, 726 passed in 70.97s
FAILED tests/test_gate_evidence_fix1.py::test_open_writes_the_resource_claim_block_into_the_issue_body
FAILED tests/test_gate_evidence_fix1.py::test_open_records_the_tier_on_the_ledger_item
E   SystemExit: 2
wfcli open: error: the following arguments are required: --exec-capability,
    --exec-capability-reason, --review-capability, --review-capability-reason
```

## 3. 閘門實測

拋棄式 PR **#74**（`throwaway/gate-evidence-fix1` → `main`），非 draft。

### 3.1 CI 測的確實是合併結果，不是分支頭

required check `tests` 的 run log 自證：

```
event          = pull_request
checked-out    = 58a9fef16fbd71b1d6213a98f37a2b1b6edb015c   ← merge commit
```

而 PR 的 head 是 `34d0e6a`。**兩者不同，正是 `ci.yml` 註解宣稱的那件事。**
同一 SHA 上的另一支 run 名為 `tests (branch head)`（run `31648036917`），
與 required 的名字不同——`ci.yml` 的命名表達式如設計般運作，required check 不會撞名。

| run | 事件 | 名稱 | 受測的樹 | 結論 |
|---|---|---|---|---|
| [`31647977751`](https://github.com/ruan6047/ai-workflow/actions/runs/31647977751) | `pull_request` | `tests` | 合併結果（head `78d3f80`） | **failure** |
| [`31648036917`](https://github.com/ruan6047/ai-workflow/actions/runs/31648036917) | `push` | `tests (branch head)` | 分支頭 `34d0e6a` | failure |
| [`31648039425`](https://github.com/ruan6047/ai-workflow/actions/runs/31648039425) | `pull_request` | `tests` | 合併結果 `58a9fef` | **failure**（2 failed / 726 passed） |

### 3.2 `BEHIND` 會遮住 `BLOCKED`——這一點必須先排除

**第一次觀測（分支落後 main 84 個 commit）：**

```json
{ "mergeStateStatus": "BEHIND", "mergeable": "MERGEABLE",
  "statusCheckRollup": [ { "name": "tests", "conclusion": "FAILURE" } ] }
```

⚠️ **required check 已經是紅的，`mergeStateStatus` 卻回報 `BEHIND`。**
`BEHIND` 是 `strict` 政策的訊號，**不是紅叉的訊號**——這正是 `#71` 取得的那種證據，
也正是為什麼 `#71` 不足以證明本卡要證的事。若停在這裡就宣稱「紅叉擋下合併」，
那是把兩個不同的阻擋原因混為一談。

**故必須先讓分支追上 main**（`gh pr update-branch`），把 `strict` 這個變因消掉，
使**唯一**剩下的阻擋原因是紅色的 `tests`。

### 3.3 排除 `strict` 之後：`BLOCKED`

```json
{ "number": 74, "state": "OPEN", "isDraft": false,
  "baseRefName": "main", "headRefOid": "34d0e6a383549a19e6b9eda9f9c179851cb2965d",
  "mergeable": "MERGEABLE",
  "mergeStateStatus": "BLOCKED",
  "statusCheckRollup": [
    { "name": "tests (branch head)", "status": "COMPLETED", "conclusion": "FAILURE" },
    { "name": "tests",               "status": "COMPLETED", "conclusion": "FAILURE" }
  ] }
```

三個條件同時成立，才使這筆觀測有意義：

- `mergeable: MERGEABLE` → **沒有文字衝突**（與 `#61` 的 `DIRTY` 決定性地不同）
- 分支已追上 main → **不是 `BEHIND`**（與 `#71` 決定性地不同）
- required `tests` 為 `COMPLETED` / `FAILURE` → **不是 pending**

∴ `BLOCKED` 的成因只能是紅色的 required check。

### 3.4 兩層拒絕：客戶端與伺服器端

**第一層（`gh` 客戶端）：**

```
$ gh pr merge 74 --squash --subject "..." --body ""
X Pull request ruan6047/ai-workflow#74 is not mergeable: the base branch policy prohibits the merge.
To have the pull request merged after all the requirements have been met, add the `--auto` flag.
To use administrator privileges to immediately merge the pull request, add the `--admin` flag.
exit=1
```

⚠️ **這一層還不夠。** `gh` 是讀了 `mergeStateStatus` 之後自己不送出——依 ROADMAP §2
「偵測不等於強制」的同一把尺，**這是客戶端的偵測器，不是伺服器的執行者**。
就此收手會犯本卡要糾正的那個錯誤的鏡像版本。

**第二層（GitHub 伺服器）：** 直接繞過 `gh` 的判斷打 REST merge endpoint。

送出前先回讀確認無 bypass 路徑（`bypass_actors: []`、`current_user_can_bypass: "never"`、
`enforcement: "active"`、`mergeStateStatus: BLOCKED`），再送：

```
$ gh api -X PUT repos/ruan6047/ai-workflow/pulls/74/merge \
      -f merge_method=squash -f sha=34d0e6a...

HTTP/2.0 405 Method Not Allowed
{"message":"Repository rule violations found\n\nRequired status check \"tests\" is failing.\n\n",
 "documentation_url":"https://docs.github.com/rest/pulls/pulls#merge-a-pull-request","status":"405"}
exit=1
```

**伺服器逐字說出了阻擋原因，且該原因就是紅色的 `tests`。** 這是本卡要補的那一格。

### 3.5 main 未被動過

```
origin/main 取證前 = 5ac61d2e32cb75c058a6f6bce797e67cf1e8491e
origin/main 取證後 = 5ac61d2e32cb75c058a6f6bce797e67cf1e8491e   ✅
PR #74: state=OPEN→CLOSED, mergedAt=null, mergeCommit=null, autoMergeRequest=null
```

**未使用 `--admin`，未使用 `--auto`**（後者會排隊等條件滿足後自動合併，是一顆定時炸彈）。

### 3.6 未動閘門

取證前後以 `gh api` 回讀 ruleset `20768920`，**位元組完全相同**：

```
$ diff ruleset-before.json ruleset-after.json     ← 無輸出
$ shasum -a 256 ruleset-before.json ruleset-after.json
de7f5689ddb17ea50dd709d2cd2bde09b359bc56992663865502bc676682e148  ruleset-before.json
de7f5689ddb17ea50dd709d2cd2bde09b359bc56992663865502bc676682e148  ruleset-after.json
```

內容：`enforcement: active`／`~DEFAULT_BRANCH`／`bypass_actors: []`／
`strict_required_status_checks_policy: true`／required check `tests`（`integration_id 15368`）。

### 3.7 拋棄式資源已清理

PR #74 不合併地關閉；遠端分支已刪；本機分支 `throwaway/gate-evidence-fix1` 已 `-D`；
兩個取證用 worktree 已 `worktree remove --force`；`fetch --prune` 後
worktree／本機分支／遠端分支三面查詢 `throwaway` 皆無輸出；worktree 總數回到取證前的 21。

## 4. R1-002：不可補正的既成事實

`#47` 的 `R1-002` 指出 `adfcbce` 缺三件式 trailer。**本卡未處理，也不可能處理。**

`adfcbce` 已在 main 上，補 trailer 只能改寫已推送歷史，而本專案明令禁止。
**這是永久的既成缺口，記錄於此，不宣稱已修復。**

`DEV-COMMIT-TRAILER-GUARD1`（#63）的唯讀檢查器已於 main 上線，可機械列出該筆：

```
$ wfcli doctor .. --commit-trailers --commit-range "adfcbce~1..adfcbce" --trailer-epoch none
- 統計：違規 1／界線前（不判違規）0／合規 0／無所要求 0（共 1 筆）
- [違規／implementation] adfcbce0c952 2026-08-12T14:02:07+08:00
    test(cli): supply the capability routing flags the release-cleanup fixture never saw
  - 缺 Requested-by／Implemented-by。
```

⚠️ 注意 `--trailer-epoch none`：`adfcbce`（2026-08-12）早於預設界線
`2026-08-13T00:00:00+08:00`，**預設參數下它不計違規**。上面要傳 `none` 才看得到它，
這件事本身就說明該缺口是被界線刻意豁免的既成歷史，而非待辦。

## 5. 本卡**沒有**證明的東西

> 這一節與 §0 同等重要。ROADMAP §2 的紀律在本卡反過來用：要證的正是強制，
> 故凡未實測者一律列在這裡，**不得以設定面推論頂替**。

1. **未證明網頁 UI 的合併按鈕也被擋。** 只實測了 REST endpoint 與 `gh`。
   兩者共用伺服器端的 ruleset 檢查是合理推論，**但推論不是實測**。
2. **未證明對具 bypass 權限者的行為。** `bypass_actors: []` 使這種人今天不存在，
   但那是**設定面**事實；一旦有人被加進去，本檔的結論不自動延伸。
3. **未取得「分支頭 run 為綠、合併結果 run 為紅」在 CI 上的同時對照。**
   `78d3f80` 上只產生了 `pull_request` run，`push` run 未出現
   （`gh api .../actions/runs?head_sha=78d3f80` 只回一筆）。**成因未查明，本檔不臆測。**
   分支頭為綠的證據因此只有**本機**的 294 passed，而非 CI 上的。
   ——這與 8/12 事故裡「綠」的取得方式相同（`#25` 自己的工作樹），故不影響形狀論證，
   但它確實不是 CI 側的證據。
4. **未證明閘門能擋下「測試抓不到的」陳舊基線碰撞。** 本次擋下的因果鏈是
   *語意衝突 → 測試紅 → check 紅 → 合併被擋*。**第一個箭頭不是機械保證的**：
   若某個陳舊基線碰撞沒有任何測試覆蓋，整條鏈從第一步就斷了，閘門不會響。
   閘門保護的上界是測試套件的覆蓋範圍。
5. **⚠️ 殘留風險：ruleset 不在版控裡，且沒有任何東西會發現它消失。**
   它是 repo setting，不是檔案（ROADMAP §2 已載明它不在資源模型的值域裡）。
   本檔證明的是**2026-08-13 這一刻**閘門有效；若日後有人停用或改動 `20768920`，
   **repo 內沒有任何偵測器會響**，而本檔會繼續讀起來像是「已經安全了」。
   本卡不解決這一條，只把它記為已知缺口。

## 6. 對 ROADMAP §2 的影響

§2 現行文字記載：

> 故**未取得「紅色 check 直接擋下合併」的直接證據**，取而代之的是設定面證據。需求方裁定接受。

**該限度已於 2026-08-13 解除**，證據見本檔 §3.3–§3.4。
是否據此更新 §2 的文字，屬需求方的排程判斷——依 ROADMAP §5，
**本檔只提供證據，不自行改動 §2，也不因為取得證據就開新卡。**
