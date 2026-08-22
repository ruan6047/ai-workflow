# WF-CLEANUP-GUARD1：破壞性收尾操作的守衛

> 卡：[ruan6047/ai-workflow#25](https://github.com/ruan6047/ai-workflow/issues/25)（T4 紅線）
> 切自 [#16](https://github.com/ruan6047/ai-workflow/issues/16)。#16 §2.3 明文把**整個收尾轉換**交給本卡，並刻意不描述它的任何性質；本文件與 `cli/src/wf_cli/cleanup.py` 是該轉換的唯一描述處。
> 實作：`cli/src/wf_cli/cleanup.py`　接線：`wfcli handoff --next-stage release --cleanup`　偵測面：`wfcli doctor --cleanup-preview`　測試：`cli/tests/test_cleanup.py`、`cli/tests/test_release_cleanup.py`
>
> **⚠️ 射程：只有 `release`。`reconcile --apply` 這條路徑目前沒有任何守衛。** 依卡面驗收第 4 條（2026-08-12 `amend` op `3cd13f81` 正式縮小射程），本卡的實作射程限於 `release` 觸發路徑；`reconcile --apply` 白名單第 2 條的接線歸 #16 §9 的 G 卡。讀本文件時請把這件事一路帶著——見 §0 的現況段、§4.1 的接線表、§9 第 1 項。

## 0. 要解的事

canonical `AI_WORKFLOW.md` §4.1 已經寫了：「回收前先檢查未提交變更，**禁止靜默刪除工作內容**。」

問題不在規則缺失，在於**沒有任何東西在執行它**。`reconcile --apply` 與 `release` 的收尾會移除 worktree、刪本地與遠端分支；一個無人看管的批次修復可以刪掉別人尚未提交的工作，而現況只有一句散文擋在前面。本卡把那句話變成呼叫點上的機械守衛。

> **現況先講清楚，免得這份文件被讀成「已經解決了」**：上一段那個「無人看管的批次修復刪掉別人尚未提交的工作」，**在 `reconcile` 這一側仍然完全沒有東西擋著**。本輪只把 `release` 接上守衛。
>
> 這是卡面驗收第 4 條界定的射程，不是實作疏漏——但**射程縮小不改變事實**：核心痛點只關上一半，而且關上的不是原始敘述裡最危險的那一半（`release` 是操作者當場發動、有人在看；批次修復才是「無人看管」的那個）。詳見 §4.1 與 §9 第 1 項。

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

### 3.3 二次確認不夠：刪除必須是**條件式**的（R2-001）

上一輪把 §3.2 當成修好了。查核者 R2-001 用隔離實測證明沒有：

> 在拋棄式 repo 內用自訂 git runner，在 `recheck_remote_branch()` 回傳 `delete` **之後**、`git push --delete` 送出**之前**推入一筆新提交 → `mode=applied`、遠端分支被刪、新提交消失。

診斷很直白：**複驗是「讀」，刪除是「寫」，兩者之間沒有 compare-and-swap**。多讀一次只是把窗變窄，沒有把它關上。而既有的回歸測試一條都沒轉紅——`test_cleanup.py` 的注入點打在 `after_delete_local_branch`，那是「遠端刪除這一步開始之前」，注入的提交在複驗執行時就已存在，於是複驗自己就會拒絕。**那條測試驗的是複驗本身，不是複驗到刪除之間的時間差。**

修法照需求方裁定先試**條件式刪除**：複驗讀到的那個 tip 不是印出來就算，它原樣成為刪除指令的租約期望值。

```
recheck_remote_branch() → RemoteDeleteDecision(verdict="delete", expected_tip=<tip>)
                        → conditional_delete_args()
                        → git push --force-with-lease=refs/heads/<branch>:<tip> origin --delete <branch>
```

檢查與刪除自此是**同一個原子操作**，不是先後兩件事。`RemoteDeleteDecision` 把 tip 一起交出來就是為了讓「不用它」變成寫不出來的東西——遠端刪除只有 `conditional_delete_args()` 一條路，而它沒有期望 tip 就組不出指令（丟 `CleanupGuardError`，不退回無條件刪除）。

**為什麼 `--force-with-lease` 沒有牴觸「`--force` 不可用」**：它與其他 force 旗標**方向相反**。其他 force 說的是「不管遠端現在是什麼都照做」，它說的是「遠端不是我剛讀到的那個值就不要做」——正是原本缺的那個 CAS。`_forbid_force()` 因此只開一個**形狀完全固定**的窄口（`_LEASE_RE`），三個要求缺一不放行：

| 被擋掉的近似寫法 | 為什麼危險 |
|---|---|
| 裸 `--force-with-lease`（無 `=`） | 拿本機 remote-tracking ref 當期望值，那份 ref 可能是幾小時前 fetch 的 |
| `--force-with-lease=<短名>:<sha>` | 短名不會被 git 認成 lease 目標，租約**靜默失效** |
| `--force-with-lease=refs/heads/x:0000…` | 全零＝「期望此 ref 不存在」，刪既有分支時自相矛盾且 fail-open |
| `--force-with-lease=refs/heads/x:HEAD` | 期望值不是固定 SHA，會在送出當下才解析成任意值 |

**刪除被拒的處置與守衛其餘拒絕路徑同型**：不丟例外（呼叫端拿不到結構化理由）、不靜默略過（會讓 `applied` 說謊），而是記一筆具名的 `remote_delete_lease_refused`、降 `aborted`、效果扣住。**不重試，也不降級為無條件刪除**——重試只會在遠端真的變動時把工作刪掉。

**成敗判定只看 git 自己的 returncode**。`default_git_runner` 不經 shell、不接管線：`git push … | tail -3` 之後的 `$?` 是 `tail` 的結果，一個被 `(stale info)` 拒絕的 push 會看起來像成功。本 repo 已因這個形態出過一次事故（一個 review 被拒但後續指令照跑），所以它在 `default_git_runner` 的 docstring 裡被釘成不可改的約定。

## 4. 唯一機械 executor

收尾轉換只有一個機械 executor：`execute_closeout_transition()`。**目前呼叫它的只有 `release` 一條路徑**（§4.1）；`reconcile --apply` 白名單第 2 條被寫出來時**必須**呼叫同一個函式、共用同一個 `evaluate_cleanup_guard()`——那是本卡對後續卡的約束，**不是已經發生的事實**。

**「reconcile 側前提不得放寬」不靠紀律維持**：`evaluate_cleanup_guard()` 的簽章裡根本沒有 `trigger` 參數，也沒有任何 `force` 參數——依觸發者放寬前提這件事在型別層就寫不出來。真正做事的 `_execute_closeout()` 同樣收不到觸發者標籤（R4-002 的處置，§4.0）：標籤由外層的 `execute_closeout_transition()` 在它**回傳之後**才貼上。這句話買到的強度與它買不到的部分，§4.0 逐層寫明。

`doctor --cleanup-preview` 是同一份守衛的**唯讀偵測面**，因此「doctor 說可以」與「executor 願意做」不可能各說各話。doctor 本身永不刪除任何東西。

### 4.0 「不得分叉實作」買得到什麼強度（卡面驗收第 5 條）

縮小射程的**代價上限**由卡面釘死：允許少接一條路徑，**不允許把實作切成兩份**。條文要求 `execute_closeout_transition()` 不得因只接一條路徑而內含 release 專屬邏輯，後續接 reconcile 時只該新增呼叫點。

#### 上一版在這裡宣稱過「不能被繞過」，而那句話是錯的

R4-002（`major`，`executor-trigger-branch-regression-guard-bypass`）：查核者以

```python
if locals()["trig" + "ger"] == "rec" + "oncile":
```

在 `expected_tip` 為 `None` 的保險絲上依觸發者分叉，`test_executor_body_never_branches_on_the_trigger` 仍 1 passed；PM 獨立重現，**全套 382 passed 全綠**，兩層都沒抓到。

錯的不是「漏列一條規則」，是**用一條「不准這樣寫」的規則去承擔「寫不出來」的宣稱**。AST 規則只認得它列舉過的形狀：`ast.Name(trigger)` 認得，`locals()[…]` 不認得；完整字面常數認得，`"rec" + "oncile"` 不認得。再多列幾條也只是把繞過成本抬高——那是軍備競賽，而軍備競賽買不到「不能」這個字。

#### 所以本輪換路：把值移出 scope，而不是再多列幾條規則

disposition 給了兩條路（更完整的 AST／語意檢查；可驗證的資料流限制），**本輪選第二條**，理由三點：

1. 第一條的產出無論做到多細，能誠實宣稱的都只有「常見寫法會被擋」，而 §4.0 要承擔的是卡面「不得分叉」——**強度對不上就只能改宣稱**，那等於把問題留著。
2. 第二條治本：`trigger` 不在函式體的 scope 裡，動態名稱查表就查不到東西，不必逐一想像繞過寫法。
3. 代價可控——**呼叫端零改動**（見下）。

實作切法：

| 函式 | 職責 | 看得到 `trigger` 嗎 |
|---|---|---|
| `execute_closeout_transition()`（`cleanup.py`） | 貼標籤層：呼叫下面那支，拿到結果後 `replace(result, trigger=trigger)` | 看得到（**它就是邊界**） |
| `_execute_closeout()`（`cleanup.py`） | 真正的機械 executor：守衛、三個破壞性動作、第 4 步效果 | **看不到**——不是參數、不是自由變數、也沒有同名模組全域 |

代價兩項，都寫在這裡而不是留給查核者自己發現：`CloseoutResult.trigger` 的型別成為 `Trigger | None`（`None` 只在貼標籤前的那一瞬間存在），以及多一層函式呼叫。**公開簽章一字未改**，`handoff_cmd` 與既有測試的呼叫方式完全不變。

#### 買到了什麼、邊界在哪、邊界外會發生什麼

四層，每層都指名執行者與作用域。前三層是形狀面（不挑路徑，但挑手法），第四層是行為面（不挑手法，但挑路徑）——**兩邊的盲區互補，這正是為什麼不能只留一邊**。

| 層 | 執行者（檔案::測試） | 釘住什麼 | **邊界外會發生什麼** |
|---|---|---|---|
| T1 名稱面 | `cli/tests/test_cleanup.py::test_the_destructive_body_cannot_name_the_trigger` | CPython 的名稱只可能來自 `co_varnames`／`co_freevars`／`co_cellvars`／`co_names` 四張表與模組全域，`locals()`／`globals()`／`getattr()` 查的是同一批表。四張表（含所有巢狀 code object）與模組層都沒有 `trigger` ⇒ **按名字拿必然落空**。附帶一條允許清單：函式體只准 `LOAD_GLOBAL` 清單內那 19 個名字 | 允許清單只管**全域名稱**。屬性存取（`LOAD_ATTR`）與 `import` 不經 `LOAD_GLOBAL`，因此 `import sys` 之後走 `sys._getframe(1)` 這層攔不到 |
| T2 值面 | 同檔 `::test_the_destructive_body_frame_never_holds_a_trigger_value` | 換個名字夾帶也不行：在**每個步驟間隙**回頭探 `_execute_closeout` 的 frame，任何區域變數的值等於 `release`／`reconcile` 即轉紅 | 覆蓋範圍寫死為「區域變數本身 ＋ 三層以內的 tuple／list／set／dict 元素」。**藏進自訂物件屬性的夾帶不覆蓋**；取樣點只有 `step_hook` 的間隙（放行後 4 個），間隙之間讀了就用掉的值探不到 |
| T3 呼叫端 | 同檔 `::test_the_labelling_wrapper_is_pinned_to_call_and_relabel` | 貼標籤層是唯一還看得到 `trigger` 的地方，所以把它的位元碼符號集合釘死：`co_names` 恰為 `{_execute_closeout, replace}`、`co_varnames` 恰為參數列、常數只准是 `None` 與關鍵字名稱元組。政策查表要有 dict 常數、`locals()` 要有 `locals`、屬性分派要有屬性名——三者都會讓其中一張表長出新東西 | 釘的是符號不是語意。**用既有符號做的夾帶**（例如把 `trigger` 當成別的關鍵字引數傳下去）T3 不會紅——那是 T2 的守備範圍（M56 實證） |
| 行為面 | 同檔 `::test_a_recheck_that_reports_deletable_without_a_tip_stops_the_run`（M48 那條保險絲，兩個 trigger 各跑一次）等 | **不挑手法**：不管值是怎麼拿到的，只要分叉改變了行為，走過該路徑的測試就紅 | **只覆蓋跑過的路徑**。M48 正是死在這裡——那條保險絲一次都沒被行為測試走過，形狀面因此成了唯一防線 |

補上第四層的缺口是本輪的另一半工作：`::test_every_fuse_in_the_destructive_body_has_a_registered_behavioural_cover` 解析函式體，要求每一條 `raise CleanupGuardError` 都在登記表裡對到一個確實存在的行為測試。**它不驗那個測試是否真的走到該保險絲**（逐行追蹤的成本與誤判率不划算），它驗的是「有沒有人被迫想過這件事」——讓下一條保險絲不可能默默地只靠形狀面撐著。

#### 因此 §4.0 的宣稱逐字如下

> **可以宣稱（有機械執行者）**：破壞性函式體 `_execute_closeout()` **無法以名稱取得觸發者標籤**（T1，窮舉 CPython 名稱表），**也無法靠改名夾帶**（T2，值面探測）；唯一還看得見標籤的貼標籤層被符號集合釘死（T3）。三者的執行者都在 `cli/tests/test_cleanup.py`，作用域是 `cleanup.py` 的這兩支函式，**不及於其他模組**。
>
> **不可宣稱**：「依觸發者分叉不可能」。走呼叫堆疊讀外層 frame 仍然拿得到——**這不是保留意見，是實證**（下表 M55：形狀面三層全綠）。接住它的是行為面，而行為面只覆蓋跑過的路徑。
>
> **是約定不是強制**：「`reconcile` 將來必須呼叫同一個函式」（§4.1）沒有任何機械手段保證，本模組攔不住有人另寫一條刪除路徑。

#### 繞過嘗試的實例表：七個突變體，形狀面與行為面分開記

**每一格都是跑出來的**。注入前基線 388 passed（全綠，否則 KILLED 判定無效）；每個突變體單獨注入、跑完整套件、無條件還原。

| 突變體 | 手法 | T1 | T2 | T3 | 行為面 | 結果 |
|---|---|---|---|---|---|---|
| M50 | 查核者原句：`locals()["trig" + "ger"] == "rec" + "oncile"` | 🔴 | – | – | 🔴 ×2 | KILLED |
| M51 | 不碰觸發者，直接把 M48 那條保險絲拆掉 | 綠 | 綠 | 綠 | 🔴 ×2 ＋登記表 🔴 | KILLED |
| M52 | 改名夾帶（`mode_hint`），字串會被摺疊 | 🔴 | 🔴 | 綠 | 🔴 ×1 | KILLED |
| M53 | 走呼叫堆疊，字串會被摺疊 | 🔴 | 綠 | 綠 | 🔴 ×1 | KILLED |
| **M54** | **M50 的防摺疊版**：`locals().get("".join([...]))` | 🔴 允許清單指名 `locals` | 綠 | 綠 | 🔴 ×2 | KILLED |
| **M55** | **走呼叫堆疊的防摺疊版**：`sys._getframe(1).f_locals.get(…)` | **綠** | **綠** | **綠** | 🔴 ×1 | KILLED（**只有行為面接住**） |
| **M56** | **改名夾帶的防摺疊版** | 綠 | 🔴 指名 `mode_hint` | 綠 | 🔴 ×1 | KILLED |

三件必須說明白的事：

1. **M50／M52／M53 死在常數摺疊，那是絆線不是承重。** `"rec" + "oncile"` 會在**編譯期**被摺成 `'reconcile'`，因此落進 `co_consts` 被抓到；AST 抓不到只是因為 AST 在摺疊之前。但 `"".join(["rec", "oncile"])` 摺不掉——M54／M55／M56 就是為了拆掉這條運氣成分而做的。**承重的是 T1 的允許清單與 T2 的值面探測**，證據是 M54（T1 訊息逐字指名 `locals`）與 M56（T2 訊息逐字指名 `mode_hint`）。
2. **M54 的行為面兩個 trigger 都紅，這比「有紅」更重要。** 資料流限制之下 `locals().get("trigger")` 回 `None`，永遠不等於 `"reconcile"`——**那個分叉根本運作不起來**，於是保險絲對兩個 trigger 都被略過、兩個參數都轉紅。這是「值不在裡面」的直接後果，不是斷言碰巧成立。
3. **M55 是本節最誠實的一格。** 形狀面三層全部綠——資料流限制**沒有**擋住走呼叫堆疊。它之所以仍被殺，唯一原因是 M48 那條保險絲本輪有了行為覆蓋。上一輪若有這條行為測試，R4-002 當時就會被接住；反過來說，一條**沒有行為覆蓋**的新保險絲仍然可以用 M55 的手法分叉而不被任何一層抓到——登記表是為此而設，但登記表只保證有人想過，不保證覆蓋到位。

#### 為什麼「同一份實作」的行為等價比對仍然留著

`test_decision_identical_for_release_and_reconcile` 與 `test_swapping_the_trigger_changes_nothing_but_the_label` 沒有被上述改動取代。後者給兩個 trigger **各一個獨立沙箱 repo**，逐字比對送進 git runner 的 argv、effect writer 的呼叫序列與 `CloseoutResult` 的每個可觀測欄位（路徑與 SHA 正規化後），放行與拒絕兩條路徑都比。它們是行為面的主力：不挑手法，代價是只覆蓋跑過的情境。

**一個誠實的殘留**：`CloseoutEffectWriter` 的方法名叫 `write_release_terminal()`，字面帶著 release。那是**命名**不是分叉——它是注入進來的協定方法，第 4 步的終態寫入對兩個觸發者是同一件事，reconcile 接線時提供自己的實作即可，不需要複製或分叉 executor。本輪不改名：改名要動協定、呼叫點與既有測試，換不到任何行為保證。寫在這裡是為了讓查核者不必自己去確認它到底是名字還是分支。

### 4.1 接線現況：release 已接，**reconcile 尚未受保護**

查核者 R1-002 指出 `execute_closeout_transition()` 寫好了卻沒有任何呼叫點，因此核心痛點未消。

**射程的規範來源是卡面驗收第 4 條**（2026-08-12 `amend` op `3cd13f81`）：「本卡的實作射程限於 `release` 觸發路徑；`reconcile --apply` 白名單第 2 條的接線歸 #16 §9 的 G 卡。」該條同時作廢了先前「不得依觸發者切分實作範圍」的舊條文。

**這個引用基礎本身是修過的。** 縮小射程的裁定原本只存在於 checkpoint 留言與 handoff 證據，沒有寫進卡面規範欄位，於是 R3 查核者對著卡面正確判定驗收未達成（R3-001；attribution 事後更正為 `coordinator`）。本文件先前也照著同一個形態，把射程寫成「需求方某日的裁定」——**引用散文來源等於把那個病灶再複製一次**，所以本輪改為引用卡面條文本身。裁定的落點是規範欄位，不是留言。

條文之外，這個射程還有兩個事實支撐：

- `reconcile` 子命令**目前完全不存在**（`cli/src/wf_cli/cli.py` 註冊的只有 open／assign／amend／deploy-declare／deploy-state／handoff／review／doctor／snapshot），且其 `--apply` 白名單第 2 條在 #16 §5.2 標記為 **reserved pending #25**——本卡若須先建出 reconcile，兩張卡會互相等待。
- `release` 是**現在就有人在用**的路徑（`handoff --next-stage release`），接上守衛立即有價值。

所以現況必須照實說：

| 觸發者 | 是否已接上守衛 | 歸屬 |
|---|---|---|
| `handoff --next-stage release --cleanup` | ✅ 本輪接上 | 本卡 |
| `reconcile --apply` 白名單第 2 條 | ❌ **完全沒有守衛**（指令尚不存在；寫出來時也不會自動受保護，得由 G 卡自己接） | #16 §9 的 G 卡 |

**核心痛點只解決了一半，而且要說清楚是哪一半。** 痛點的原始敘述是「一個**無人看管的批次修復**可以刪掉別人尚未提交的工作」；本輪接上的 `release` 是操作者當場發動、有人盯著的那一條。批次修復那一條——痛點裡真正危險的主體——**尚未受任何守衛保護**。

本卡對它的保證也只到「當它被寫出來時，應該用這一份守衛」為止。那是**規範上的約束**（卡面驗收與本文件），不是機械保證：`execute_closeout_transition()` 沒有辦法阻止未來有人在 reconcile 裡另寫一條刪除路徑。§4.0 釘住的是「這份實作不會為了 release 而分叉」，不是「不會有人繞過它」。

### 4.2 `--cleanup` 為何是選配而非預設

接線改變了一個現行指令的行為，而 `release` 目前的使用者預期是「只改狀態」。定案：**清理需顯式帶 `--cleanup`，預設不發動**。理由：

1. 把預設改成會刪 worktree 與遠端分支，等於讓一個既有指令在沒人要求的情況下開始刪東西——從使用者視角看，那正是 `AI_WORKFLOW.md` §4.1「禁止靜默刪除工作內容」要消滅的形態。守衛擋得住「前提不成立時誤刪」，擋不住「使用者根本沒想刪」。
2. 兩種預設的錯誤代價不對稱：漏清理可以再跑一次補；刪錯了沒有補救。預設值取代價可回復的那一邊。
3. `--cleanup` 需搭配 `--repo-path`，因此無法被設定檔或環境變數「不小心變成預設」。

**不提供 `--main-ref`／`--remote`**：它們是能讓祖先檢查名存實亡的旋鈕（把 `main_ref` 指向待刪分支自己，`merge-base --is-ancestor` 必然通過）。doctor 的同名旗標無妨，因為 doctor 唯讀；破壞性路徑上不開這個口。

**預設值的代價也要講明**，否則「安全的預設」會變成默許一個已知錯誤：不帶 `--cleanup` 的 release 會在清理完成前寫入終態，依 `classify_state()` 的分類即 `illegal_terminal_before_cleanup`；守衛不自動修復非法態，所以事後再補 `--cleanup` 會被擋。該路徑因此印出警示（`NO_CLEANUP_WARNING`），`test_cleanup_after_a_status_only_release_is_refused_as_illegal` 把這個代價釘成可執行的事實。

### 4.3 帶 `--cleanup` 時的寫入順序與失敗停點

狀態面的四個欄位寫入與 body Log 附加，全部包進 `CloseoutEffectWriter`；**何時寫由 executor 決定**，它只在重新觀測到清理確實完成後才呼叫。因此「終態先於清理」在這條路徑上寫不出來，不是靠呼叫端自律。

**但「怎麼寫」不在本卡手上，而那條路徑的首寫不自描述。** `write_release_terminal` 最終落到 `commands/handoff_cmd.py` 的 `write_status_face()`，實際順序是 `owner` → `交付狀態` → `最後交接` → `iteration` → Issue body Log（`handoff_cmd.py:277`–`286`）。首寫是 owner 欄位——一個不帶載荷、看不出屬於哪一次收尾的寫入。本卡因此把不可逆的刪除接在一個首寫不可辨識的動詞上，這是外部相依造成的殘餘曝險，詳見 §9 第 10 項。

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

`cli/tests/test_cleanup.py`（71 例，57 → 68 → 71）＋ `cli/tests/test_release_cleanup.py`（14 例，13 → 14）＋ `cli/tests/test_doctor.py` 的預覽段。全部在 pytest `tmp_path` 沙箱 repo 內操作真實 git worktree、真實 bare remote，不碰任何實際專案。

`cd cli && uv run pytest -q`：**382 passed**（R2-001 修正前的基線 **367**，R3 交付 **379**，本輪為驗收第 5 條新增 3 例；無退化、無跳過）。

- **五種危險情境全數拒絕**，且每一條都以 `assert_work_intact()` 核對**拒絕後工作內容仍完整存在**——檔案內容、本地分支、遠端分支、stash 逐項驗，不是只驗回傳碼。
- **故障注入**：`step_hook` 在六個步驟間隙各丟一次例外，續作後必須到達 `completed`，中斷當下必須落在合法態，且每個破壞性 argv 在兩次執行加總後最多出現一次。
- **循環前置專項**：`CHECK_STEP_REF` 的值域不含 4；守衛簽章不含 `remote_facts`；Issue 開著且非終態時 release 照樣通過；`outstanding_obligations` 不影響 `mode`。
- **單一 executor 形狀**：AST 規則 ＋ 兩個獨立沙箱的行為等價比對 ＋ 七個分叉突變體（§4.0）。
- **正向對照**：前提全成立時真的清乾淨（沒有它，拒絕測試可能是空頭支票）。

### 7.1 R1-001 的回歸測試怎麼構造

`test_remote_delete_refused_when_tip_moved_after_the_guard_passed` 把查核者描述的序列原樣搬進沙箱：另建一個 clone（＝「另一台機器」，與本 repo 只共用 bare remote），用 `step_hook` 在 **`after_delete_local_branch` 這個時點**——也就是守衛早已通過、本機清理剛做完的那一刻——從該 clone 提交並 push 一個新 commit。

斷言不是只看回傳碼：

- 遠端刪除被拒（`mode="aborted"`、`actions_aborted=("delete_remote_branch",)`），且拒絕理由指名 `remote_tip_still_merged`，證明是**刪除前的二次確認**擋下的，不是前提檢查碰巧擋住；
- 新提交仍在遠端——**重新 clone 一份把檔案內容讀出來**，而不是相信本機的 ref；
- 效果被扣住：狀態面沒寫、Issue 沒關，狀態停在合法的 `cleanup_in_progress`；
- 重跑一次也不會刪：前提複驗此時看到未併入的遠端 tip，直接純偵測，內容再驗一次仍在。

參數化成兩個分支覆蓋二次確認的兩種拒絕理由：新提交**不在**本地物件庫時是 `unobservable`；先 `git fetch` 讓本機看得見它之後則是 `merge-base` 不成立的 `fail`。沒有後半，只要有人在別處先 fetch 過，守衛就會退回舊行為而測試不知情。

### 7.1.1 R2-001 的回歸測試：注入點差一步，覆蓋就差一整條

上一條測試**驗不到** R2-001，而且原因要講清楚，否則同型的假綠會再犯一次。`step_hook("after_delete_local_branch")` 的時點在「遠端刪除這一步開始之前」——注入的提交在複驗跑的時候已經存在，複驗會正確拒絕，測試因此綠。它證明的是「複驗會擋住它在自己執行前就看得到的變動」，而 R2-001 問的是「複驗**之後**才發生的變動」。

`test_remote_delete_refused_when_the_tip_moves_between_recheck_and_push` 改用 **runner 攔截**：`_run()` 先組好含租約的完整 argv、送進 runner，runner 才交給 subprocess。在 runner 裡注入，等於卡在「複驗已回傳可刪」與「git 真的被執行」之間，就是被打穿的那一段。

四條反假綠的設計：

1. **注入必須真的發生**（`assert state["injected"]`）。攔截述詞一旦與實際 argv 對不上，runner 會退化成透明代理而整條案例形同不存在。
2. **先斷言工作還在，再斷言記帳**。租約被拿掉時第一個轉紅的是「遠端分支連同新提交被刪掉了」，而不是某個欄位少一筆——前者說得出後果，後者只說得出帳不符。
3. **複驗這一筆必須是 `pass`**。這正是與 §7.1 的分野：擋下刪除的是租約，不是複驗；若複驗自己就擋住了，代表注入又跑到窗外去了。
4. **租約的期望值必須等於複驗讀到的 tip**，逐字比對送出的 argv。用一個當下重讀的值當租約，等於把 CAS 換回兩件事。

同一個窗在 CLI 層另有一條（`test_release_cleanup.py`），斷言 `rc == 5` 且狀態面一個字都沒寫。

所有比對 argv 的地方一律改用**述詞**而非固定前綴。這不是預防性潔癖：本輪加上租約旗標後，`argv[:3] == ["push", "origin", "--delete"]` 立刻一條都對不上，`test_release_fails_when_cleanup_reported_success_but_did_not_complete` 的假成功 runner 當場退化成透明代理——它是被實際跑出來抓到的，不是想出來的。

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

### 7.5 條件式刪除對真實 GitHub 的驗證：拒絕路徑已實證，接受路徑未實證

先講清楚證到哪裡。**拒絕路徑（＝真正承擔保證的那一半）已對真實 GitHub 實證**；**接受路徑只在本機 bare repo 實證**。

#### 對真實 GitHub 遠端（`github.com:ruan6047/ai-workflow.git`，SSH）

用 `--dry-run` 對真實遠端送一個**租約過期**的刪除（`--dry-run` 不送出任何更新；租約本身也是過期的，兩重保險），目標是本卡自己的分支：

```
git push --dry-run origin --force-with-lease=refs/heads/<本卡分支>:<過期SHA> --delete <本卡分支>
  → ! [rejected]  (delete) -> <本卡分支> (stale info)
  → git returncode 1；分支在 GitHub 上完好無損
  → GIT_TRACE_PACKET：客戶端只送出一個 flush（0000），一條更新指令都沒送
```

這證明的是：**GitHub 的 ref advertisement 會被租約檢查吃到，且過期租約在真實傳輸上確實被拒**。因為客戶端一條指令都沒送，這一層的保證完全不依賴 GitHub 做任何額外的事。

**沒有對真實 GitHub 做的是接受路徑**（租約相符 → 分支真的被刪）。那需要在真實遠端建一條拋棄式探針分支再刪掉；該次 `git push` 被執行環境的權限層擋下，未再嘗試繞道。

#### 本機拋棄式 bare repo（兩條路徑都有）

除了重現需求方的結果，另外用 `GIT_TRACE_PACKET` 把**線路上實際送了什麼**看出來：

| 觀測 | 結果 |
|---|---|
| 租約過期時（另一個 clone 已推入新提交） | `! [rejected] (delete) -> feature (stale info)`，git returncode **1**，遠端分支與新提交存活，重新 clone 讀得回內容 |
| 租約相符時 | `- [deleted] feature`，returncode **0** |
| 被拒那次的線路內容 | 客戶端在收到 ref advertisement 後，**只送出一個 flush（`0000`）——一條更新指令都沒送** |
| 被接受那次的線路內容 | `<old-oid> 0000…0000 refs/heads/feature`，刪除指令**帶著非零的 old-oid** |
| 無租約的普通刪除 | old-oid **相同**（取自同一次 advertisement） |

由此可以推出兩件事：

1. **租約檢查完全發生在客戶端**，比對的對象是伺服器在同一條連線裡剛送出的 ref advertisement，不是本機的 remote-tracking ref。上面對真實 GitHub 的那次 dry-run 直接證實了這一點在 GitHub 上成立（拒絕發生了，而且一條指令都沒送出）。
2. **客戶端只在 advertisement 與租約相符時才送出指令**，而送出的 old-oid 就是那個值。所以只要伺服器對 delete 指令做標準的 old-oid 交換檢查，我們的期望值就會被伺服器再驗一次。

**沒有證明的部分，逐條列出**：

- **接受路徑未對真實 GitHub 實跑**：租約相符時 GitHub 是否確實完成刪除。若 GitHub 對帶租約的 delete 另有自訂行為而拒絕，症狀是 `aborted` ＋ `rc=5` ＋ 遠端分支留著——雜訊，不是資料遺失，但會讓每次 `release --cleanup` 都停在最後一步。
- GitHub 的 receive-pack 是否對 delete 指令執行 old-oid CAS——本機 `git` 的 receive-pack 會（`ref_transaction_delete` 收 old_oid），GitHub 不是逐字的 stock git。這一條只有推定，且它只影響「GitHub advertise 之後到套用之前」那一段毫秒級的窗。
- GitHub 的 ref advertisement 是否恆為最新（而非來自落後的 replica）。若 advertisement 落後，租約會拿舊值比舊值而通過。這個殘餘風險**所有 `--force-with-lease` 的使用者都共有**，客戶端無法自行消除。

**這些殘餘風險不構成退回 fail-closed（不自動刪遠端分支）的理由**，因為失敗方向是安全的：

- 若 GitHub **忽略**租約，行為退化成本輪之前的無條件刪除——不比現況差，且窗仍比修改前窄（複驗仍在）。而真實遠端的 dry-run 已經證明它沒有被忽略。
- 若 GitHub **誤拒**合法的刪除，處置是 `aborted` ＋ 效果扣住 ＋ `rc=5`，遠端分支留著等人處理——雜訊，不是資料遺失。

因此保留條件式刪除，並把「接受路徑對真實 GitHub 首次實跑」列為未關的洞（§9 第 8 項）與 sign-off 條件，而不是宣稱整條路徑都已驗證。

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

**第三輪（R2-001）另跑 11 個突變體，11/11 被殺**：

| 突變體 | 內容 | 結果 |
|---|---|---|
| M34 | 拿掉租約，退回無條件刪除（＝被打穿的那個版本） | KILLED |
| M35 | `_forbid_force` 的阻擋整個失效 | KILLED |
| M36 | 反向過緊：連合法租約也擋（遠端刪除從此發不出去） | KILLED |
| M37 | 租約接受全零期望值 | KILLED |
| M38 | 租約接受短名 refspec | KILLED |
| M39 | 條件式刪除被拒仍當成功 | KILLED |
| M40 | 刪除被拒改丟例外而非降 `aborted` | KILLED |
| M41 | `worktree remove` 的失敗檢查失效 | KILLED（**第一輪存活**，見下） |
| M42 | 複驗不再交出 `expected_tip` | KILLED |
| M22 | 複驗退回「只看分支還在」（複驗本輪未退化） | KILLED |
| M19 | 效果不再要求清理已完成（指定複驗項） | KILLED |

三件比「11/11」本身更值得記的事：

1. **M34 對舊測試（§7.1）跑出 SURVIVED，對新測試（§7.1.1）跑出 KILLED。** 這是「注入點差一步、覆蓋就差一整條」的直接證據，不是論述。
2. **M36 是刻意加的反向突變體。** 只驗「非法 force 被擋」的話，把 `_forbid_force` 寫成全擋也會全綠——而那會讓遠端刪除永遠發不出去，是另一種靜默失效。一道防線要同時釘住「該擋的擋住」與「該過的過得去」。
3. **M41 兩次才殺掉，而第一次的「殺掉」是假的。** 拿掉 `worktree remove` 的失敗檢查之後，這條路徑照樣會丟 `CleanupGuardError`——只是晚一步，炸在 `branch -d`（分支還被 checkout 著）。只驗 `pytest.raises` 會因為錯誤的理由而綠，與 M30 同型。補上「停在哪一步」的斷言（沒有嘗試過 `branch -d`、沒有送出任何刪除 push）之後才真的殺掉。順帶補上了一個既有缺口：原本沒有任何案例讓 `worktree remove` **回非 0**（既有案例只覆蓋「回 0 卻沒做」）。

**第五輪（R4-002）另跑 7 個突變體，7/7 被殺，逐格結果與判讀見 §4.0 的實例表。** 這一輪與前四輪有一個方法上的差別，值得單獨記：**前三個突變體（M50／M52／M53）都死在「常數摺疊」這條運氣成分上**——`"rec" + "oncile"` 在編譯期被摺成 `'reconcile'`，於是被 `co_consts` 檢查抓到。若就此收工，交出的會是一份「看起來 3/3 KILLED」但承重點站在編譯器最佳化上的報告。因此另做了三個防摺疊版（M54／M55／M56），才看得出真正扛住的是哪一層——以及 **M55 那格形狀面三層全綠**，那是本輪最重要的一筆證據，不是瑕疵記錄。

## 8. 本卡不做的事

- **不執行第 5–7 步**（卡檔封存／Ledger 投影／對帳三件套）：它們不寫狀態面，也不在本卡資源宣告內。
- **不接 `reconcile --apply`**：卡面驗收第 4 條已把該接線劃出本卡射程，歸 #16 §9 的 G 卡（見 §4.1）；該子命令目前也尚不存在。**reconcile 側因此完全沒有守衛**——這是本卡最大的未關缺口，不是一句「不做的事」就能帶過的。
- **不新增 `wfcli release` 子命令**：release 是 `handoff --next-stage release` 的既有階段，本輪只改它的行為，不註冊新指令（`cli.py` 未改動）。
- **不代為 fetch**：遠端 commit 不在本地物件庫時回 unobservable 並拒絕，不靜默改動本機 ref。
- **不解 `open` 的建立型半寫入**（#16 §4.5 明示缺口），與本卡無關。
- **不改 `handoff` 的首寫載荷**：讓效果動詞的首寫自描述，歸 [#23](https://github.com/ruan6047/ai-workflow/issues/23) 的 A′ 實作卡。本卡在此只做一件事——把該相依與它造成的殘餘曝險寫進 §9 第 10 項，不自建第二套說法（§1）。

## 9. 已知仍未關的洞

誠實列出，供查核者與後續卡接手：

1. **reconcile 側完全沒有守衛**（§4.1）——**本卡最大的未關缺口，排第一不是排版順序**。核心痛點的原始敘述是「無人看管的批次修復刪掉別人的工作」，而被關上的是 `release`（操作者當場發動、有人在看）那一半；**無人看管的那一半原封不動**。卡面驗收第 4 條把該接線劃給 #16 §9 的 G 卡，所以這不是本卡的實作欠債；但缺口的存在與歸屬是兩件事，射程縮小不使它變小。本卡對它唯一的保證是規範上的「將來只能用這一份守衛」，沒有任何機械手段阻止有人另寫一條刪除路徑。
2. **effect writer 回報成功不等於狀態面真的變了**。executor 在 writer 回傳後即認定第 4 步完成（`RemoteCardFacts(True, False)`），而不是回頭重讀 GitHub。這與 `push --delete` 回 0 卻沒刪掉是同一類問題——後者已被 `cleanup_done` 複驗接住，前者沒有。修法是給 executor 一個「重讀狀態面」的可注入讀取器，本輪未做。**另見第 10 項**：那是同族的第三面，缺的是「認不認得出是誰寫的」而非「寫了有沒有生效」，兩條不可合併。
   > **本輪嚴重度上升，理由要記下來。** R2-001 證明的不是「複驗漏了一項」，而是「**讀一次不構成保證**」——讀與寫之間沒有 CAS 時，窗只會變窄不會關上。這條洞是同一個形狀在狀態面的翻版：writer 回傳成功只是一次寫入的回應，不是回頭讀到的事實，而 GitHub 側沒有 git 那種現成的 `--force-with-lease` 可用。git 這一側能修是因為傳輸協定本來就帶 old-oid 交換；狀態面要等價的保證，得自己做「讀取 → 帶條件寫入 → 重讀驗證」，成本高得多。**在那之前，這條洞不應再被描述為「與 §3.3 同類、已被同一招接住」。**
3. **`--cleanup` 不是預設**，所以既有的 status-only release 仍會持續造出 `illegal_terminal_before_cleanup`（§4.2）。這是刻意的取捨，代價以警示與測試釘住，但洞還在。
4. **`release --cleanup` 未對真實 Project／Issue 實跑**（§7.3）。T4 最高風險項須需求方 sign-off。
5. **條件式刪除只覆蓋遠端分支**。worktree 移除與本地分支刪除靠 git 自己的拒絕（`worktree remove` 不加 `--force` 會拒絕髒工作樹，`branch -d` 會拒絕未合併分支）當第二道防線，本模組沒有再加一層自己的複驗，也沒有等價的 CAS。可接受的理由是這兩者刪掉的是**本機**副本、且都有 reflog；遠端分支被刪則可能是唯一一份。
6. **`no_stash` 只認得 git 預設的 stash 訊息格式**。使用者自訂訊息的 stash 會被判 `unobservable`（fail closed，安全），但實務上會變成擋住合法收尾的雜訊。
7. **第 4 步的「Issue 留結案留言」未實作**。`worktree-lifecycle.md` 第 11 行第 4 點寫的是「留結案留言**並**關閉」；本輪只關閉，留痕仍走既有的 body `## Log` append（與其餘 wfcli 指令一致）。差在留言是外部可見的收據，body Log 不是——這條差異刻意列出來，不當成已完成。
8. **條件式刪除的「接受路徑」未對真實 GitHub 實跑**（§7.5）。拒絕路徑已對真實遠端實證（過期租約 → `(stale info)`、returncode 1、一條指令都沒送出）；**租約相符時 GitHub 是否確實完成刪除**只在本機 bare repo 證過，因為那需要在真實遠端建拋棄式探針分支，該次 push 被執行環境權限層擋下。失敗方向是雜訊而非資料遺失（`aborted` ＋ `rc=5` ＋ 分支留著），但第一次真跑 `release --cleanup` 時要盯著這一步。
9. **殘餘窗：GitHub 的 ref advertisement 到套用刪除之間**。租約檢查在客戶端對 advertisement 完成，這段窗由遠端自己的 ref transaction 負責，客戶端無法涵蓋。它是毫秒級、且與本卡修掉的「整段本機清理」不同量級，但它存在，且所有 `--force-with-lease` 的使用者共有。
10. **本卡接上的效果動詞，其首寫不自描述**（外部相依：[#23](https://github.com/ruan6047/ai-workflow/issues/23)）。`handoff --next-stage release --cleanup` 的效果寫入順序是 `owner` → `交付狀態` → `最後交接` → `iteration` → Issue body Log（§4.3）。[#23](https://github.com/ruan6047/ai-workflow/issues/23) §7.1.2 據此判 `handoff` 的首寫**不合格**——首寫是 owner 欄位，不帶可攜載荷——故該動詞的 E1（自描述首寫）**不成立**。本卡把**破壞性收尾**（移除 worktree、刪本地與遠端分支）接到了這個動詞上。
    **後果**：清理已完成、owner 已寫、Log 寫入前崩潰時，事件流上沒有任何可辨識該次寫入的記號。本卡的 resume 是**觀測式**的（§6），因此**不會重複刪除**——這一點不受影響；但狀態面會停在「終態已寫、Log 缺行」的組合，而該組合在事件流上認不出是哪一次收尾留下的。觀測式 resume 補償不了這件事：它讀的是資源事實（worktree／分支在不在），不是「誰寫了狀態面」。
    **歸屬**：修法在 `handoff` 首寫的載荷，屬 [#23](https://github.com/ruan6047/ai-workflow/issues/23) 的 A′ 實作卡。本卡不自行實作自描述首寫（那會在同一件事上造出第二套說法，違 §1），也不代它裁定。**但缺口的存在與歸屬是兩件事**（同第 1 項的判準）：一張 T4 卡把不可逆刪除接在一個首寫不自描述的動詞上，這件事屬於本卡的曝險面，該寫在卡的文件裡，而不是只活在兩位查核者的範圍外發現裡。
    > **與第 2 項同族，但不是同一件事，不要合併。** 第 2 項是「**寫了，但不知道有沒有生效**」——executor 在 writer 回傳後即認定第 4 步完成，沒回頭重讀，缺的是**結果確認**；本項是「**生效了，但事件流上認不出是誰寫的**」，缺的是**可辨識性**。兩者可同時發生，修法也落在不同人身上：第 2 項要給 executor 一個可注入的「重讀狀態面」讀取器（本卡射程內，本輪未做），本項要改的是被呼叫端的首寫載荷（本卡碰不到）。併成一條的代價是：其中一條被修掉時，另一條會被誤判為一併解決。
    >
    > 順同一條線看，這是同一形狀的**第三面**：R2-001 是「**讀一次不構成保證**」（§3.3），第 2 項是「**寫一次不構成生效確認**」，本項是「**寫一次不構成可辨識**」。三者都不是靠多做一次同樣的動作能關上的。
11. **形狀面擋不住走呼叫堆疊的分叉**（R4-002 的殘留，§4.0）。資料流限制讓破壞性函式體拿不到觸發者標籤——按名字拿不到（T1）、換名夾帶也拿不到（T2）——但 `import sys` 之後讀外層 frame 仍然拿得到。**這不是推測，是實證**：突變體 M55 讓形狀面三層全綠。目前接住它的只有行為面，而行為面**只覆蓋跑過的路徑**：一條新加的、沒有行為測試走過的保險絲，仍可用 M55 的手法分叉而不被任何一層抓到。保險絲登記表（`test_every_fuse_in_the_destructive_body_has_a_registered_behavioural_cover`）把「新保險絲必須登記一個行為測試」變成硬性，但它**只驗登記與該測試存在，不驗那個測試真的走到那條保險絲**。要真的關上這一條，得做逐行覆蓋度閘門（本卡未做，成本與誤判率須另評）。
12. **T2（值面探測）的取樣是離散的**（§4.0）。它只在 `step_hook` 的間隙（放行後 4 個點）回頭探 frame，且覆蓋範圍寫死為「區域變數本身 ＋ 三層以內的容器元素」。間隙之間讀了就用掉的值、以及藏進自訂物件屬性的夾帶，都探不到。M56 證明它對「多一個參數一路帶著」這種形態有效，那也正是它的形狀假設。
