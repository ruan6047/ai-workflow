# WF-CLEANUP-GUARD1：破壞性收尾操作的守衛

> 卡：[ruan6047/ai-workflow#25](https://github.com/ruan6047/ai-workflow/issues/25)（T4 紅線）
> 切自 [#16](https://github.com/ruan6047/ai-workflow/issues/16)。#16 §2.3 明文把**整個收尾轉換**交給本卡，並刻意不描述它的任何性質；本文件與 `cli/src/wf_cli/cleanup.py` 是該轉換的唯一描述處。
> 實作：`cli/src/wf_cli/cleanup.py`　偵測面：`wfcli doctor --cleanup-preview`　測試：`cli/tests/test_cleanup.py`

## 0. 要解的事

canonical `AI_WORKFLOW.md:146` 已經寫了：「回收前先檢查未提交變更，**禁止靜默刪除工作內容**。」

問題不在規則缺失，在於**沒有任何東西在執行它**。`reconcile --apply` 與 `release` 的收尾會移除 worktree、刪本地與遠端分支；一個無人看管的批次修復可以刪掉別人尚未提交的工作，而現況只有一句散文擋在前面。本卡把那句話變成呼叫點上的機械守衛。

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

## 4. 唯一機械 executor

`release`（操作者當場發動）與 `reconcile --apply` 白名單第 2 條（批次）呼叫的是同一個 `execute_closeout_transition()`，共用同一個 `evaluate_cleanup_guard()`。

**「reconcile 側前提不得放寬」不靠紀律維持**：`evaluate_cleanup_guard()` 的簽章裡根本沒有 `trigger` 參數，也沒有任何 `force` 參數——依觸發者放寬前提這件事在型別層就寫不出來。`trigger` 只進結果紀錄。

`doctor --cleanup-preview` 是同一份守衛的**唯讀偵測面**，因此「doctor 說可以」與「executor 願意做」不可能各說各話。doctor 本身永不刪除任何東西。

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

`cli/tests/test_cleanup.py`（50 例）＋ `cli/tests/test_doctor.py` 的預覽段。全部在 pytest `tmp_path` 沙箱 repo 內操作真實 git worktree、真實 bare remote，不碰任何實際專案。

- **五種危險情境全數拒絕**，且每一條都以 `assert_work_intact()` 核對**拒絕後工作內容仍完整存在**——檔案內容、本地分支、遠端分支、stash 逐項驗，不是只驗回傳碼。
- **故障注入**：`step_hook` 在六個步驟間隙各丟一次例外，續作後必須到達 `completed`，中斷當下必須落在合法態，且每個破壞性 argv 在兩次執行加總後最多出現一次。
- **循環前置專項**：`CHECK_STEP_REF` 的值域不含 4；守衛簽章不含 `remote_facts`；Issue 開著且非終態時 release 照樣通過；`outstanding_obligations` 不影響 `mode`。
- **正向對照**：前提全成立時真的清乾淨（沒有它，拒絕測試可能是空頭支票）。

### 7.1 真資料實跑（與它的界線）

合成 fixture 全綠而真資料漏抓，在本 repo 發生過（#17 → #20）。因此另做真資料唯讀實跑：

- `wfcli doctor <repo> --cleanup-preview` 在 `ai-workflow` 與 `cpbl-analytics` 兩個實際 repo 上跑完、唯讀、無副作用。
- 直接對兩個**實際在途 worktree** 評估十項前提：兩者皆正確判 `detect_only`（未併入 main；其中一個另有 3 筆未提交變更），`lsof` 真的掃了 458 個 process cwd。

**界線要講清楚**：兩個 repo 目前都沒有 `📦已合併` 的活卡，所以預覽段輸出零列——**守衛在真實收尾情境下的完整放行路徑尚未在真資料上跑過**，那部分的證據全部來自沙箱 repo（真 git、真 remote，但非真卡）。另外 `--registry` 只支援 `tasks-md`／`none`；已 cutover 到 GitHub Issues 的專案，其活卡讀不進預覽（`registry.py` 不在本卡資源宣告內，接線屬後續卡）。

### 7.2 突變測試

21 個突變體逐一把守衛關掉重跑，**21/21 被殺**。首輪 M19（效果不再要求清理已完成）**存活**，暴露出真實缺口：沒有任何案例覆蓋「守衛放行但清理實際未完成」。補上 `test_effect_is_withheld_when_cleanup_did_not_actually_complete` 後轉為 KILLED。

> 這正是突變測試的用處——50 個測試全綠時，它是唯一告訴我「其中有一塊是空的」的東西。

## 8. 本卡不做的事

- **不執行第 5–7 步**（卡檔封存／Ledger 投影／對帳三件套）：它們不寫狀態面，也不在本卡資源宣告內。
- **不提供 `wfcli release` 指令**：第 4 步以 `CloseoutEffectWriter` 注入。指令本體屬 #16 §9-E；`reconcile --apply` 白名單第 2 條的接線屬 §9-G。本卡交付的是**它們必須共用的那份守衛與 executor**。
- **不代為 fetch**：遠端 commit 不在本地物件庫時回 unobservable 並拒絕，不靜默改動本機 ref。
- **不解 `open` 的建立型半寫入**（#16 §4.5 明示缺口），與本卡無關。
