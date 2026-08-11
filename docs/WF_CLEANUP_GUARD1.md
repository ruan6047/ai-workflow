# WF-CLEANUP-GUARD1：破壞性收尾操作的守衛

> 卡：[ruan6047/ai-workflow#25](https://github.com/ruan6047/ai-workflow/issues/25)（T4 紅線）
> 切自 [#16](https://github.com/ruan6047/ai-workflow/issues/16)。#16 §2.3 明文把**整個收尾轉換**交給本卡，並刻意不描述它的任何性質；本文件與 `cli/src/wf_cli/cleanup.py` 是該轉換的唯一描述處。
> 實作：`cli/src/wf_cli/cleanup.py`　接線：`wfcli handoff --next-stage release --cleanup`　偵測面：`wfcli doctor --cleanup-preview`　測試：`cli/tests/test_cleanup.py`、`cli/tests/test_release_cleanup.py`

## 0. 要解的事

canonical `AI_WORKFLOW.md:146` 已經寫了：「回收前先檢查未提交變更，**禁止靜默刪除工作內容**。」

問題不在規則缺失，在於**沒有任何東西在執行它**。`reconcile --apply` 與 `release` 的收尾會移除 worktree、刪本地與遠端分支；一個無人看管的批次修復可以刪掉別人尚未提交的工作，而現況只有一句散文擋在前面。本卡把那句話變成呼叫點上的機械守衛。

> **現況先講清楚，免得這份文件被讀成「已經解決了」**：本輪只把 `release` 接上守衛，**`reconcile` 側尚未受保護**（該子命令目前根本不存在，見 §4.1）。核心痛點只解決了一半。

## 1. 權威來源（引用，不重述）

本卡刻意不建立第二套說法。四個既有權威直接引用：

- **刪除順序與收尾清單**：`templates/worktree-lifecycle.md` 第 11 行（第 5 點）的七步清單。`cleanup.py` 只記「第幾步扮演什麼角色」（`STEP_ROLES`），不複製步驟內容。`test_destructive_order_matches_authority` 直接解析該檔並比對順序——權威檔一旦改動而本模組沒跟上，測試就轉紅，而不是靜靜地帶著過期副本繼續跑。
- **終態列舉**：`commands/assign_cmd.TERMINAL_STATUSES`，直接 import。
- **lease 語意**：`registry.RegisteredCard.owner_assigned()`。
- **worktree 分類**：`doctor.WorktreeClass` 是既有權威，其軸是「這個 worktree 對得上哪張卡」。本卡的 `GuardCheck` 是**另一條軸**：「刪掉它會不會毀掉工作內容」。兩者不互相覆蓋。

## 2. 三段分離：前置條件、效果、後續義務

七步清單的角色**不是「全部都是前置」**。那會構成循環——第 4 步正是 release 自己的效果，若列為前置，release 永遠發動不了。

| 步 | 角色 | 對守衛的意義 |
|---|---|---|
| 1 merge 複驗＋push | 前置條件 | 守衛檢查（本地與遠端各自驗祖先關係） |
| 2 worktree 與分支清理 | 前置條件 | 守衛檢查，且**本卡就是執行它的人** |
| 3 資源宣告釋放 | 前置條件 | 守衛檢查（非 `file:` 資源不因 merge 自動釋放） |
| 4 Issue 關閉＋release 事件＋終態落地 | **效果本身** | **守衛不得檢查**（`CHECK_STEP_REF` 的值域不含 4） |
| 5 卡檔封存 | 其後義務 | 不寫狀態面，**未完成不阻擋 release** |
| 6 Ledger 投影重建 | 其後義務 | 同上 |
| 7 對帳三件套 | 其後義務 | 同上 |

「終態寫入是**狀態面序列**的最後一步，不是整份清單的最後一步」：第 1–3 步完成後才寫 🏁完成／關閉 Issue，其後仍有第 5–7 步，但那三步不寫狀態面，故不衝突。程式裡這件事表現為 `remaining_status_face_steps()` 的值域只有 `{2, 4}`，而 `outstanding_obligations` 恆為 `(5, 6, 7)` 且從不影響 `mode`。

## 3. 前提：枚舉、三值、fail-closed

十項前提逐條列舉於 `CHECK_IDS`，涵蓋卡面驗收第 1 條的四類（無未提交變更／無 active lease／未被佔用／分支已合併）：

| check_id | 步 | 判準 |
|---|---|---|
| `merge_verified_local` | 1 | `merge-base --is-ancestor <branch> main`；分支不存在＝無可刪對象，pass |
| `merge_verified_remote` | 1 | 以 `ls-remote` 取遠端兩端 SHA 後比對祖先；本地物件庫沒有該 commit 則 unobservable（守衛不代為 fetch） |
| `no_uncommitted_changes` | 2 | worktree 內 `status --porcelain` 空（含未追蹤檔） |
| `no_stash` | 2 | stash 訊息解析出的分支不得等於待刪分支；**訊息解析不出來即 unobservable** |
| `no_locked_worktree` | 2 | porcelain 的 `locked` 位 |
| `not_self_cwd` | 2 | 本 process 的 cwd 不在待刪 worktree 內 |
| `not_occupied_by_process` | 2 | `lsof -d cwd` 全機掃描；lsof 不可用即 unobservable |
| `not_primary_worktree` | 2 | 目標非 repo 主工作樹 |
| `no_foreign_active_lease` | 2 | **別張**活卡不得持有同一分支／worktree 的有效 lease |
| `resources_released` | 3 | 宣告內不得殘留 `port:`／`container:`／`db:`（這些不因 merge 自動釋放） |

**三值而非布林**：`pass` / `fail` / `unobservable`。`aggregate_mode()` 只有全部 `pass` 才 `proceed`，`fail` 與 `unobservable` **同等阻擋**。

> 「探不到」不等於「沒事」。把 unobservable 當成 pass 是本卡要消滅的 fail-open——lsof 不在、ls-remote 連不上、stash 訊息看不懂，全都導向拒絕。突變體 M02／M10 就是把這條規則反過來，兩個都被測試殺掉。

任一不成立即降**純偵測**：回報全部阻擋原因（不是第一個），不執行任何刪除。

### 3.1 為什麼 `no_foreign_active_lease` 要排除目標卡自己

目標卡的 lease 正是本轉換要釋放的東西。把它算進來，守衛就永遠不可能通過——這是與第 4 步同型的循環，只是換一個地方發生。

### 3.2 遠端刪除前的二次確認（R1-001）

前提檢查通過與 `git push --delete` 送出之間**隔著一段時間**——本機 worktree 移除與本地分支刪除就發生在其中。查核者 R1-001 指出的正是這個窗：

> 守衛確認遠端 `feature` 已併入 `main` → 本機 worktree 與 local branch 清理完成 → **另一個 clone 把新提交 push 到同一個遠端 `feature`** → 執行器仍跑 `git push origin --delete feature`，新提交就沒了。

舊實作在此只重新確認「遠端分支還在」。分支確實還在，但它指的已經是別人的新工作。**這是本模組唯一會真的毀掉他人已提交內容的路徑**，因此 `recheck_remote_branch()` 在按下刪除鍵前重讀三件事，缺一即拒：

1. 遠端 branch 與 main 的**當下** SHA（同一次 `ls-remote`，兩端同一次觀測，不再開第二個窗）；
2. branch tip 的 commit object 在**本地物件庫可觀測**（觀測不到＝本機沒見過的新提交；守衛不代為 fetch，也不對看不見的東西做祖先判斷）；
3. `merge-base --is-ancestor <tip> <遠端 main tip>` 仍成立。

回傳的是與前提檢查同一型的 `GuardCheck`，因此「驗不過或觀測不到就降 `detect_only`、不刪」在這裡與前提檢查是同一條規則，不是另立的例外。

**拒絕之後這一次 run 叫什麼**：`CloseoutResult.mode` 因此有第三個值 `aborted`。一個已經移除了 worktree 的 run 自稱「純偵測」是不誠實的，所以不併進 `detect_only`；呼叫端只需記住**只有 `applied` 代表轉換完成**。效果（第 4 步）一併扣住，狀態停在合法的 `cleanup_in_progress`，重跑會重新觀測——此時前提檢查會看到未併入的遠端 tip，直接純偵測，不會「第二次就刪掉」。

## 4. 唯一機械 executor

`release` 與 `reconcile --apply` 白名單第 2 條呼叫的是同一個 `execute_closeout_transition()`，共用同一個 `evaluate_cleanup_guard()`。

**「reconcile 側前提不得放寬」不靠紀律維持**：`evaluate_cleanup_guard()` 的簽章裡根本沒有 `trigger` 參數，也沒有任何 `force` 參數——依觸發者放寬前提這件事在型別層就寫不出來。`trigger` 只進結果紀錄。

`doctor --cleanup-preview` 是同一份守衛的**唯讀偵測面**，因此「doctor 說可以」與「executor 願意做」不可能各說各話。doctor 本身永不刪除任何東西。

### 4.1 接線現況：release 已接，**reconcile 尚未受保護**

查核者 R1-002 指出 `execute_closeout_transition()` 寫好了卻沒有任何呼叫點，因此核心痛點未消。需求方 2026-08-11 裁定本輪的接線射程為**只接 `release`**：

- `reconcile` 子命令**目前完全不存在**（`cli/src/wf_cli/cli.py` 註冊的只有 open／assign／amend／deploy-declare／deploy-state／handoff／review／doctor／snapshot），且其 `--apply` 白名單第 2 條在 #16 §5.2 標記為 **reserved pending #25**——本卡若須先建出 reconcile，兩張卡會互相等待。
- `release` 是**現在就有人在用**的路徑（`handoff --next-stage release`），接上守衛立即有價值。

所以現況必須照實說：

| 觸發者 | 是否已接上守衛 | 歸屬 |
|---|---|---|
| `handoff --next-stage release --cleanup` | ✅ 本輪接上 | 本卡 |
| `reconcile --apply` 白名單第 2 條 | ❌ **尚未受保護**（指令尚不存在） | #16 §9 的 G 卡 |

**核心痛點只解決了一半**：一個無人看管的批次修復仍然沒有被本卡擋住——因為那個批次修復本身還沒被寫出來。本卡確保的是「當它被寫出來時，只能用這一份守衛」，而不是「它現在已經被守住了」。

### 4.2 `--cleanup` 為何是選配而非預設

接線改變了一個現行指令的行為，而 `release` 目前的使用者預期是「只改狀態」。定案：**清理需顯式帶 `--cleanup`，預設不發動**。理由：

1. 把預設改成會刪 worktree 與遠端分支，等於讓一個既有指令在沒人要求的情況下開始刪東西——從使用者視角看，那正是 `AI_WORKFLOW.md:146`「禁止靜默刪除工作內容」要消滅的形態。守衛擋得住「前提不成立時誤刪」，擋不住「使用者根本沒想刪」。
2. 兩種預設的錯誤代價不對稱：漏清理可以再跑一次補；刪錯了沒有補救。預設值取代價可回復的那一邊。
3. `--cleanup` 需搭配 `--repo-path`，因此無法被設定檔或環境變數「不小心變成預設」。

**不提供 `--main-ref`／`--remote`**：它們是能讓祖先檢查名存實亡的旋鈕（把 `main_ref` 指向待刪分支自己，`merge-base --is-ancestor` 必然通過）。doctor 的同名旗標無妨，因為 doctor 唯讀；破壞性路徑上不開這個口。

**預設值的代價也要講明**，否則「安全的預設」會變成默許一個已知錯誤：不帶 `--cleanup` 的 release 會在清理完成前寫入終態，依 `classify_state()` 的分類即 `illegal_terminal_before_cleanup`；守衛不自動修復非法態，所以事後再補 `--cleanup` 會被擋。該路徑因此印出警示（`NO_CLEANUP_WARNING`），`test_cleanup_after_a_status_only_release_is_refused_as_illegal` 把這個代價釘成可執行的事實。

### 4.3 帶 `--cleanup` 時的寫入順序與失敗停點

狀態面的四個欄位寫入與 body Log 附加，全部包進 `CloseoutEffectWriter`；**何時寫由 executor 決定**，它只在重新觀測到清理確實完成後才呼叫。因此「終態先於清理」在這條路徑上寫不出來，不是靠呼叫端自律。

清理中途失敗時，`release` 的狀態面**停在原處、一個字都沒寫**：

| 情境 | `mode` | 交付狀態 | Issue | 本機資源 | exit code |
|---|---|---|---|---|---|
| 前提不成立 | `detect_only` | 維持 `📦已合併` | 維持開啟 | 完全未動 | 5 |
| 遠端刪除前複驗不通過 | `aborted` | 維持 `📦已合併` | 維持開啟 | worktree／本地分支已刪（合法暫時態） | 5 |
| 清理回報成功但實際未完成 | `applied` 但效果被扣住 | 維持 `📦已合併` | 維持開啟 | 部分完成 | 5 |
| 全部完成 | `applied` | `🏁完成` | 已關閉 | 全清 | 0 |

上表三種失敗停點都落在 `LEGAL_STATES` 內，續作只需重跑同一條指令——它重新觀測當下事實，不依賴任何「做到哪」的本機紀錄。

**唯一的例外是進場時狀態就已非法**（`illegal_terminal_before_cleanup`，典型成因是先跑過不帶 `--cleanup` 的 release）：executor 同樣是 `detect_only`、不動手，但那個狀態本身不合法，重跑幾次都一樣，須人工處理。守衛的職責是不把它變得更糟，不是替人修。

Issue 開關狀態讀不到時**fail closed**（exit 5，不動手）：猜「已關」會讓收尾自稱 `completed` 卻留著開著的 Issue，猜「開著」則會對已關的 Issue 再關一次。兩個都不做。

## 5. `--force` 為何是「不可用」而非「不建議」

`_forbid_force()` 掛在本模組**唯一的 git 執行入口** `_run()` 上，任何帶 `--force*`／`-f`／`-D`／`-M` 的 git 呼叫在送進 subprocess 之前就丟 `CleanupGuardError`。換掉 runner 也繞不過（檢查在 runner 之前）。刪本地分支固定用 `-d` 而非 `-D`：git 自己對未合併分支的拒絕，是守衛之外的第二道防線。

驗證不只看文件：測試逐一比對**實際送出的 argv**，並掃描整個 argparse 樹確認沒有任何子指令暴露 `--force`。

> 需要強制的情境，就是需要人判斷的定義。

## 6. 合法的暫時中間態與觀測式續作

執行期一定有中間態——本卡明定可中斷與續作，宣稱「沒有中間態」是錯的。合法性由 `classify_state()` 定義，它是五個可觀測布林（worktree／本地分支／遠端分支／終態已寫／Issue 仍開）上的**全函數**：32 種組合每一種落在且僅落在一格，**沒有「其餘」**。

| 分類 | 合法 | 意義 |
|---|---|---|
| `cleanup_in_progress` | ✅ | 本機資源部分完成，遠端仍非終態 |
| `cleanup_done_effect_pending` | ✅ | 第 1–3 步完成，第 4 步未發動 |
| `effect_in_progress` | ✅ | 第 4 步的兩次寫入完成其一 |
| `completed` | ✅ | 轉換完成（第 5–7 步另計） |
| `illegal_terminal_before_cleanup` | ❌ | 終態已寫／Issue 已關，但清理未完成 |

非法態**不自動修復**：executor 直接回純偵測並要求人判斷。

**續作是觀測式的**：`observe()` 只讀當下事實，本機不存在任何「做到哪」的紀錄（呼應 #16 §4.2 的本機零狀態）。每個破壞性動作**執行前重讀**，已不存在就跳過——重跑不會重複刪除。效果（第 4 步）只在清理**確實**完成後才發動；遠端回報刪除成功但分支還在時（受保護分支、鏡像同步、最終一致），效果會被扣住，狀態停在合法的 `cleanup_in_progress`。

## 7. 驗證

`cli/tests/test_cleanup.py`（57 例）＋ `cli/tests/test_release_cleanup.py`（13 例）＋ `cli/tests/test_doctor.py` 的預覽段。全部在 pytest `tmp_path` 沙箱 repo 內操作真實 git worktree、真實 bare remote，不碰任何實際專案。

- **五種危險情境全數拒絕**，且每一條都以 `assert_work_intact()` 核對**拒絕後工作內容仍完整存在**——檔案內容、本地分支、遠端分支、stash 逐項驗，不是只驗回傳碼。
- **故障注入**：`step_hook` 在六個步驟間隙各丟一次例外，續作後必須到達 `completed`，中斷當下必須落在合法態，且每個破壞性 argv 在兩次執行加總後最多出現一次。
- **循環前置專項**：`CHECK_STEP_REF` 的值域不含 4；守衛簽章不含 `remote_facts`；Issue 開著且非終態時 release 照樣通過；`outstanding_obligations` 不影響 `mode`。
- **正向對照**：前提全成立時真的清乾淨（沒有它，拒絕測試可能是空頭支票）。

### 7.1 R1-001 的回歸測試怎麼構造

`test_remote_delete_refused_when_tip_moved_after_the_guard_passed` 把查核者描述的序列原樣搬進沙箱：另建一個 clone（＝「另一台機器」，與本 repo 只共用 bare remote），用 `step_hook` 在 **`after_delete_local_branch` 這個時點**——也就是守衛早已通過、本機清理剛做完的那一刻——從該 clone 提交並 push 一個新 commit。

斷言不是只看回傳碼：

- 遠端刪除被拒（`mode="aborted"`、`actions_aborted=("delete_remote_branch",)`），且拒絕理由指名 `remote_tip_still_merged`，證明是**刪除前的二次確認**擋下的，不是前提檢查碰巧擋住；
- 新提交仍在遠端——**重新 clone 一份把檔案內容讀出來**，而不是相信本機的 ref；
- 效果被扣住：狀態面沒寫、Issue 沒關，狀態停在合法的 `cleanup_in_progress`；
- 重跑一次也不會刪：前提複驗此時看到未併入的遠端 tip，直接純偵測，內容再驗一次仍在。

參數化成兩個分支覆蓋二次確認的兩種拒絕理由：新提交**不在**本地物件庫時是 `unobservable`；先 `git fetch` 讓本機看得見它之後則是 `merge-base` 不成立的 `fail`。沒有後半，只要有人在別處先 fetch 過，守衛就會退回舊行為而測試不知情。

### 7.2 R1-002 的接線怎麼證明

`test_release_cleanup.py` 證明的是「那條路徑真的經過那個 executor」：

- 放行案例斷言**真實副作用**（worktree 目錄消失、本地與遠端分支消失、Issue 被關、交付狀態變 `🏁完成`）——這些只有真跑過 executor 才會發生；
- 另以 spy 攔截 `handoff_cmd.execute_closeout_transition`（**委派給真函式**，不是替身）確認它被呼叫且 `trigger="release"`；
- **順序斷言不靠讀程式碼**：`test_terminal_status_is_written_only_after_the_branch_is_gone` 在每次欄位寫入的當下記錄「待刪分支還在不在」，斷言終態寫入時分支已不存在；
- 失敗停點逐一驗：前提不成立、遠端複驗中止、Issue 狀態讀不到、卡沒有註冊分支，四種情境都斷言**狀態面一個字都沒寫**且工作內容完整。

### 7.3 真資料實跑（與它的界線）

合成 fixture 全綠而真資料漏抓，在本 repo 發生過（#17 → #20）。因此另做真資料唯讀實跑：

- `wfcli doctor <repo> --cleanup-preview` 在 `ai-workflow` 與 `cpbl-analytics` 兩個實際 repo 上跑完、唯讀、無副作用。
- 直接對兩個**實際在途 worktree**（`WF-CLI-ROUTING-TIER1`、本卡自己）評估十項前提：兩者皆正確判 `detect_only`（未併入 main；本卡那個另有未提交變更、且正是本 process 的 cwd，`not_self_cwd` 與 `not_occupied_by_process` 雙雙 fail），`lsof` 真的掃了 438 個 process cwd。
- `recheck_remote_branch()` 也對同兩條真實遠端分支唯讀跑過：皆正確 `refuse`（tip 不是遠端 main 的祖先）。

**界線要講清楚**：

- 兩個 repo 目前都沒有 `📦已合併` 的活卡，所以預覽段輸出零列——**守衛在真實收尾情境下的完整放行路徑尚未在真資料上跑過**，那部分的證據全部來自沙箱 repo（真 git、真 remote，但非真卡）。
- `--registry` 只支援 `tasks-md`／`none`；已 cutover 到 GitHub Issues 的專案，其活卡讀不進 doctor 預覽（`registry.py` 未改動）。`release --cleanup` 這條路徑不受此限：它就地把 Project items 轉成 `RegisteredCard`（`handoff_cmd.registry_from_items`）。
- `release --cleanup` 尚未對真實 Project／Issue 實跑過——它會關 Issue 與寫終態，屬 T4 不可逆操作，**須需求方 sign-off 後才做**。目前證據全來自真 git ＋ 假 GitHub（`ReleaseGhRunner`）。

### 7.4 突變測試

32 個突變體逐一把守衛關掉重跑，**32/32 被殺**（第二輪；第一輪 28/32）。

**上一輪的 M19（效果不再要求清理已完成）本輪確認仍被殺**——那條規則的覆蓋沒有在改動中被沖掉，這是查核者特別指定要複驗的同型突變。R1-001 與 R1-002 各自新增的規則也全數被殺：

- M22 二次確認退回「只看分支還在」（＝修復前的行為）→ KILLED
- M23 二次確認不看 tip 可觀測性 → KILLED
- M24 二次確認不重驗祖先 → KILLED
- M25 `refuse` 仍照刪 → KILLED
- M26 中止仍回報 `applied` → KILLED
- M27 `--cleanup` 被忽略（＝接線消失）→ KILLED
- M28 狀態面先寫再清理 → KILLED
- M29／M32 守衛擋下或清理未真正完成仍回 0 → KILLED
- M31 `--cleanup` 不再要求 `--repo-path` → KILLED
- M33 未帶 `--cleanup` 的 release 不再示警 → KILLED

**第一輪的 4 個存活體暴露了真實缺口，全部補上測試後轉紅**：

| 存活體 | 缺口 | 補上的案例 |
|---|---|---|
| M04 stash 訊息解析不出時放行 | 沒有任何案例覆蓋「歸屬不明的 stash」 | `test_stash_with_an_unparseable_message_is_unobservable` |
| M15 遠端 commit 觀測不到仍比對 | 前提檢查的 `cat-file` 可觀測性沒被驗過 | `test_remote_commit_missing_from_the_local_object_store_is_unobservable` |
| M30 Issue 狀態讀不到時猜「開著」 | 原測試只驗 exit code 5，而拔掉該分支後**碰巧**也回 5 | 改斷言「executor 根本沒被啟動」 |
| M32 清理未真正完成仍回 0 | CLI 這一層沒有對應案例（只有 executor 層有） | `test_release_fails_when_cleanup_reported_success_but_did_not_complete` |

> M30 是最值得記的一個：測試本來就是綠的，而且斷言的正是想要的行為——它只是**因為錯誤的理由而綠**。exit code 相同不代表路徑相同，突變測試是唯一把這件事指出來的東西。

## 8. 本卡不做的事

- **不執行第 5–7 步**（卡檔封存／Ledger 投影／對帳三件套）：它們不寫狀態面，也不在本卡資源宣告內。
- **不接 `reconcile --apply`**：該子命令尚不存在，其接線屬 #16 §9 的 G 卡（見 §4.1）。**reconcile 側因此尚未受守衛保護**。
- **不新增 `wfcli release` 子命令**：release 是 `handoff --next-stage release` 的既有階段，本輪只改它的行為，不註冊新指令（`cli.py` 未改動）。
- **不代為 fetch**：遠端 commit 不在本地物件庫時回 unobservable 並拒絕，不靜默改動本機 ref。
- **不解 `open` 的建立型半寫入**（#16 §4.5 明示缺口），與本卡無關。

## 9. 已知仍未關的洞

誠實列出，供查核者與後續卡接手：

1. **reconcile 側完全沒有守衛**（§4.1）。核心痛點——「無人看管的批次修復刪掉別人的工作」——只在 release 這一半被關上。
2. **effect writer 回報成功不等於狀態面真的變了**。executor 在 writer 回傳後即認定第 4 步完成（`RemoteCardFacts(True, False)`），而不是回頭重讀 GitHub。這與 `push --delete` 回 0 卻沒刪掉是同一類問題——後者已被 `cleanup_done` 複驗接住，前者沒有。修法是給 executor 一個「重讀狀態面」的可注入讀取器，本輪未做。
3. **`--cleanup` 不是預設**，所以既有的 status-only release 仍會持續造出 `illegal_terminal_before_cleanup`（§4.2）。這是刻意的取捨，代價以警示與測試釘住，但洞還在。
4. **`release --cleanup` 未對真實 Project／Issue 實跑**（§7.3）。T4 最高風險項須需求方 sign-off。
5. **二次確認只覆蓋遠端分支刪除**。worktree 移除與本地分支刪除靠 git 自己的拒絕（`worktree remove` 不加 `--force` 會拒絕髒工作樹，`branch -d` 會拒絕未合併分支）當第二道防線，本模組沒有再加一層自己的複驗。
6. **`no_stash` 只認得 git 預設的 stash 訊息格式**。使用者自訂訊息的 stash 會被判 `unobservable`（fail closed，安全），但實務上會變成擋住合法收尾的雜訊。
7. **第 4 步的「Issue 留結案留言」未實作**。`worktree-lifecycle.md` 第 11 行第 4 點寫的是「留結案留言**並**關閉」；本輪只關閉，留痕仍走既有的 body `## Log` append（與其餘 wfcli 指令一致）。差在留言是外部可見的收據，body Log 不是——這條差異刻意列出來，不當成已完成。
