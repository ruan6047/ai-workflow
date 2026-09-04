# #53 DEV-CLI-VERB-REGISTRY1 每個新動詞都要在 cli.py 改兩處，使新動詞卡彼此互相衝突
- state: closed  created: 2026-08-12T09:38:40Z  closed: 2026-08-12T11:15:14Z
- url: https://github.com/ruan6047/ai-workflow/issues/53
- comments: 3

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code PM
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；純結構重構但踩在所有動詞的註冊路徑上，須證明動詞集合、help 順序與錯誤處理逐一不變；推理鏈中等。）　查核：待指派（建議 主力型；本卡改的是所有 CLI 入口的共用點，查核重點在「不變」的證明是否窮盡而非抽樣；建議跨家族。）
- Initiative：—　spec 基線：WF-22-CLI4（#9）的執行者於 2026-08-12 回覆 PM 的 cli.py 查詢時主動提出，並指名這是排序事實而非其要求。需求方同日裁定開卡，且該卡應排在 WF-ORCHESTRATION-RECONCILE1（#16）§9 的 B／E／K 三張新動詞卡之前。
- DB：db_scope=none
- 服務的原始目標：讓新增一個 CLI 動詞不需要與其他新動詞卡爭奪同一個檔案區塊

## 簡介
<!-- card-brief:begin -->
🏁 已完成：把 wfcli 的動詞註冊清單從 cli.py 的兩處改動（import 與 add_parser）搬成 cli/src/wf_cli/commands/__init__.py 的顯式 tuple、cli.py 改為迭代它，使每張新動詞卡只需 append 一行，解掉 #54／#55／#56 三張新動詞卡彼此的寫入集互斥。適用時機：要新增 CLI 動詞、或要看動詞集合／--help 順序／引數集合／KNOWN_ERRORS 退出碼的窮舉不變性證明時。⛔ 非射程：刻意不採 pkgutil 自動探索（顯式封閉集合、fail-closed 優先於便利）；刻意不凍結 --help 黃金順序；三個動詞的實際接線屬 DEV-CLI-VERB-WIRING1（#60）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：現況每個新動詞都要在 cli.py 改**兩處**（import 區塊與 add_parser 呼叫清單）。後果是 WF-ORCHESTRATION-RECONCILE1（#16）§9 的三張未動衍生卡——B（wfcli resume）、E（wfcli merge）、K（epoch-anchor）——**彼此互相衝突**，不只是與既有卡衝突。寫入集互斥會把它們序列化，而那三張正是今天兩個代價實例（main 轉紅、API 配額耗盡於 handoff 中途）所指向的能力缺口。#9 的執行者實測後指出：把註冊清單移到 commands/__init__.py（目前 0 行）成為一個顯式 tuple、cli.py 改為迭代它，則每張新動詞卡只需 **append 一行**，而 append 是最容易合併的形狀。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/cli.py",
    "file:cli/src/wf_cli/commands/__init__.py",
    "file:cli/tests/test_cli_registry.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 把動詞註冊清單移到 commands/__init__.py 的**顯式 tuple**，cli.py 改為迭代它。**刻意不採 pkgutil 自動探索**——理由由 #9 執行者提出且需求方採納：那會讓註冊集合變成隱式且開放，與本 repo 一貫的「顯式、封閉鍵集合、fail-closed」紀律相反（同 marker 鍵集合封閉的理由），且 help 的動詞順序會變成檔案系統順序。用便利換掉可稽核性在這個 repo 裡是錯的方向。若執行者認為該裁定有誤，須論證後才可偏離。
- [ ] 證明重構前後**動詞集合逐字相同、help 輸出順序相同、每個動詞的引數集合相同**。這是本卡唯一的實質風險——它碰所有 CLI 入口。證明須為窮舉而非抽樣：以程式列舉重構前後的 subparser 名稱與各自的 required／optional 引數集合，逐一比對。
- [ ] 證明錯誤處理路徑不變：cli.py 現有的 KNOWN_ERRORS 對應關係與退出碼在重構後逐一相同。
- [ ] 新增測試釘住「註冊清單是顯式的」：若有人改成動態探索或漏註冊一個既有模組，測試須轉紅。

## 驗證

- [ ] pytest 不得退化（基線自己跑，不要抄卡面數字）。ruff 只修自己引入的。
- [ ] 動詞集合／help 順序／引數集合／錯誤處理四項的不變性各附指令輸出，且為窮舉。
- [ ] ⚠️ 合併順序：WF-22-CLI4（#9）的分支仍含四行 cli.py 改動（checkpoint_cmd 的 import 與註冊），且需求方已裁定 #9 通過查核後延後合併。本卡須明列與 #9 的合併重疊怎麼處理，並在交付報告說明先合併哪一張的後果差異。
- [ ] 凡寫下「不變／相同／窮舉」須附指令輸出；沒有機械執行者的寫成約定。
## Log

- 2026-08-12T17:38:38+08:00 open by Claude Opus 5@Claude Code PM；owner 待指派；iteration 0。
- 2026-08-12T17:44:57+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code 子agent；分支worktree claude/DEV-CLI-VERB-REGISTRY1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/dev-cli-verb-registry1；交付狀態 🚧進行中；實際能力層級 主力型（與卡面建議 主力型 相符）。
- 2026-08-12T18:10:52+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA a7e5e21993828fad016673d9cf81619e0535b599；證據 R1：註冊清單移到 commands/__init__.py 的顯式 tuple、cli.py 改為迭代。寫入集三檔 330+/20-。

⚠️ **一項須查核者裁定的偏離**：tuple 元素是**模組名字串**不是 import 進來的模組物件。理由是模組物件版**實測會炸**——環是既有的（cleanup.py:80 反向 import commands.assign_cmd.TERMINAL_STATUSES、doctor.py:17 import cleanup，**PM 已獨立確認兩行都在**），eager 版讓 commands/__init__ 一被觸及就 import 全部動詞模組，於是「先 import cleanup」撞環。**最危險的是它是潛伏的：eager 版跑完整測試套件 658 passed 全綠**，因為 cli.py 當入口時剛好不觸發那條冷啟動路徑；執行者是以 24 個模組逐一冷啟動子行程窮舉才抓到 cleanup／doctor 兩項紅。修環要動 assign_cmd.py／cleanup.py（寫入集外），故改字串版，打錯字不在 import 期爆的代價由檔案系統窮舉雙向比對補回（M4 實證轉紅）。

四項不變性以逐位元組相同證明（非抽樣）：dump parser 全部可觀測表面——9 動詞 × 每個 action 的 class/dest/option_strings/required/nargs/const/default/type/choices/metavar/help，加頂層與每動詞的 --help 全文、func 綁定、以及 9 動詞 × 9 例外類別實跑 main() 的退出碼矩陣——重構前後 diff 為空、sha256 相同。**PM 以自己寫的 dump 腳本獨立重現：62,056 bytes、sha 4623a0e4… 前後一致。** 注意原 help 順序**非字母序**（import 區塊是字母序但呼叫順序不是），tuple 保的是呼叫順序。

九個突變逐一注入驗證會轉紅（對照組 43 passed，工作樹已還原）：M1 改回 eager import → 9 紅含冷啟動哨兵；M2 改成 pkgutil → 2 紅；M3 漏註冊 → 1 紅；M4 打錯字 → 5 紅；M5 重複一筆 → 4 紅；M6 只註冊前 3 項 → 3 紅；M7 移除一個 KNOWN_ERRORS → 1 紅；M8 退出碼 2→1 → 7 紅；M9 KeyboardInterrupt 130→1 → 1 紅。**PM 已獨立注入 M3（刪 snapshot_cmd 註冊行）驗證 test_registry_matches_command_modules_on_disk 轉紅。**

驗證：pytest 基線 658 → **701**（+43，零退化）；**PM 另實測 merge(origin/main e8a638c, 本分支) → 701 passed**；ruff 在其三檔 All checks passed（PM 已複驗）；marker 字面 0。

與 #9 的合併順序，執行者以**實體化衝突樹**驗證（git archive 到 scratch，不碰 git 狀態）：**兩序皆在 cli.py 文字衝突**（PM 已複驗雙向 merge-tree 各 2 處，無法迴避——#9 改的正是本卡刪掉的兩個區塊），差別在解完之後。先本卡：解衝突取本卡側、丟棄 #9 的 4 行，在 __init__.py **append 一行**，實測 **793 passed** 且 --help 動詞順序與 #9 原分支**逐字相同**；#9 另外 7 個檔完全不衝突。先 #9：補那行的責任落到本卡分支，**本卡通過查核後還得再改一次、受審 SHA 失效**。**它建議先合本卡**，並實測「只解文字衝突而忘記 append 那行」是 **fail-closed 不是靜默壞掉**（13 紅，含 #9 自己的 11 個測試）。

⚠️ 它另發現 #9 的 checkpoint_cmd 一個模組註冊**兩個**動詞（checkpoint ＋ contract-baseline，func 名為 run_checkpoint／run_contract_baseline 非 run）。它第一版測試釘了「剛好一個動詞」與「func 必須叫 run」，**那會讓 #9 合併時無謂轉紅**；已放寬為「至少一個動詞」＋「每個動詞派到自己模組」，help 順序比對改攤平保序。**#9 的寫入集一個字沒動。**

執行者自陳六項無機械執行者，第 1 項最該被打：**現行 9 個動詞的 help 順序本身沒有任何測試釘住**——快照 diff 只證明「本 commit 沒改變它」，測試釘的是「help 順序 = tuple 順序」這個相對不變性；有人重排 tuple，--help 就跟著變而全綠。它明說這是**刻意取捨**（凍結黃金順序會讓每張新動詞卡都得編輯 test_cli_registry.py，正好重建本卡要消除的衝突點）。另五項：「每張新卡只需 append 一行」只在 #9 一個真實實例上機械證明過（793 passed），對 #54／#55／#56 是結構推論；committed 測試的錯誤路徑用合成 parser，真實 parser 的 9×9 矩陣在快照 artifact 不在測試套件；AST 檢查只擋它列舉過的動態化形狀；ruff 在無設定檔的 ambient 規則集下跑（repo 另有 15 項既有 findings 不在其檔內，依卡面未動）；「先合本卡代價較小」的後半段是流程推論非機械證明。。
- 2026-08-12T18:44:23+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5265468601，PM 回讀重算 report_sha256=e4cee5df… 一次相符。⚠️ 該收據留言曾被編輯（created≠updated），PM 無法取得編輯前內容，雜湊以現行 body 重算相符）；core_pain_resolved yes；self_run 6 項；findings 1 項（blocking 0）；attempt DEV-CLI-VERB-REGISTRY1-e0-a7e5e21993828fad016673d9cf81619e0535b599。
- 2026-08-12T19:15:00+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code PM；iteration 0；SHA e1b33d8984425901de400afeb227d5df67d07212；證據 查核 APPROVE（GPT-5@Codex 子代理，0 blocking）；PR #59 已合併，main e8a638c → e1b33d8；PM 於 main 的乾淨 archive 上實測 701 passed（非分支自測，對齊 2026-08-12 main 變紅事故的教訓）。需求方 2026-08-12 裁定走 --cleanup。⚠️ 首次嘗試被守衛擋下：PM 在 PR #59 body 寫了 Closes #53，合併時 GitHub 自動關閉 Issue，於是第 4 步的效果早於第 1-3 步發生，classify_state 判 illegal_terminal_before_cleanup、mode=detect_only、狀態面一個字都沒寫。PM 已 reopen Issue 還原至 cleanup_in_progress 後重跑。這是該守衛在真實生產路徑上的第一次使用，且第一次就抓到協調者的順序錯誤。；收尾清理已完成（worktree 與本地／遠端分支皆已不存在）。
- 2026-08-26T20:57:37+08:00 amend by wf-cli（op a0bbabb9）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:86607bc9a8a7b0f285925849dd40229bc818302fe1dc0d714b24c95b27b01c97 (651 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5265328327 · 2026-08-12T10:11:49Z

## 派審：#53 `DEV-CLI-VERB-REGISTRY1` R1

⚠️ 審核對象 **`ruan6047/ai-workflow#53`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/dev-cli-verb-registry1
分支：claude/DEV-CLI-VERB-REGISTRY1　　被審 SHA：a7e5e21993828fad016673d9cf81619e0535b599
基線：e8a638c40f1028b6b85f6c59fd12ee9c1e85582d（PM 已重算並驗為祖先）　　iteration：0（首輪）
寫入集：cli/src/wf_cli/cli.py、cli/src/wf_cli/commands/__init__.py、cli/tests/test_cli_registry.py
```

> **本則為權威。** `origin/main` 現為 `e8a638c`。**PM 已實測 merge(origin/main, 本分支) → 701 passed 全綠。**

### ⚠️ 一項須你裁定的偏離

卡面裁定「顯式 tuple、不採 pkgutil」，直覺寫法是 tuple 裡放 import 進來的**模組物件**。執行者改用**模組名字串**，理由是模組物件版**實測會炸**：

```
import wf_cli.cleanup → ImportError: cannot import name 'SUBSEQUENT_OBLIGATION_STEPS'
                        from partially initialized module 'wf_cli.cleanup'
```

環是**既有的**：`cleanup.py:80` 反向 import `commands.assign_cmd.TERMINAL_STATUSES`、`doctor.py:17` import `cleanup`——**PM 已獨立確認兩行都在**。eager 版讓 `commands/__init__` 一被觸及就 import 全部動詞模組，於是「先 import cleanup」撞環。

**最危險的是它是潛伏的**：eager 版跑完整測試套件 **658 passed 全綠**，因為 `cli.py` 當入口時剛好不觸發那條冷啟動路徑。執行者是以 **24 個模組逐一冷啟動子行程窮舉**才抓到 `cleanup`／`doctor` 兩項紅。

修環要動 `assign_cmd.py`／`cleanup.py`（**寫入集外**），故改字串版；打錯字不在 import 期爆的代價由**檔案系統窮舉雙向比對**補回。

**請判斷**：(a) 這個偏離正當嗎，還是應該擴充宣告去修環？(b) 字串版的代價（打錯字晚一步才發現）真的被補回了嗎？

### 一、四項不變性：逐位元組相同，不是抽樣

執行者 dump 了 parser 的**全部可觀測表面**——9 動詞 × 每個 action 的 `class`／`dest`／`option_strings`／`required`／`nargs`／`const`／`default`／`type`／`choices`／`metavar`／`help`，加頂層與每動詞的 `--help` 全文、`func` 綁定、以及 **9 動詞 × 9 例外類別實跑 `main()` 的退出碼矩陣**——重構前後 `diff` 為空、sha256 相同。

**PM 以自己寫的 dump 腳本獨立重現：62,056 bytes、sha `4623a0e4…` 前後一致。**

⚠️ 注意原 help 順序**非字母序**（import 區塊是字母序但呼叫順序不是），tuple 保的是**呼叫順序**。

**請自己再 dump 一次比對。**

### 二、九個突變，執行者逐一注入驗證會轉紅

M1 改回 eager import → **9 紅**（含冷啟動哨兵）｜M2 改成 `pkgutil` → 2 紅｜M3 漏註冊 → 1 紅｜M4 打錯字 → 5 紅｜M5 重複一筆 → 4 紅｜M6 只註冊前 3 項 → 3 紅｜M7 移除一個 `KNOWN_ERRORS` → 1 紅｜M8 退出碼 2→1 → 7 紅｜M9 `KeyboardInterrupt` 130→1 → 1 紅。

**PM 已獨立注入 M3**（刪 `snapshot_cmd` 註冊行）驗證 `test_registry_matches_command_modules_on_disk` 轉紅。

### 三、與 #9 的合併順序，它做了實體化驗證

**兩序皆在 `cli.py` 文字衝突**（PM 已複驗雙向 `merge-tree` 各 2 處，無法迴避——#9 改的正是本卡刪掉的兩個區塊），差別在解完之後：

| 順序 | 代價 |
|---|---|
| **先本卡** | 解衝突取本卡側、丟棄 #9 的 4 行，在 `__init__.py` **append 一行**。實測 **793 passed**，`--help` 動詞順序與 #9 原分支**逐字相同** |
| 先 #9 | 補那行的責任落到本卡分支，**本卡通過查核後還得再改一次、受審 SHA 失效** |

它並實測「**只解文字衝突而忘記 append 那行**」是 **fail-closed 不是靜默壞掉**（13 紅，含 #9 自己的 11 個測試）。

⚠️ **需求方已裁定 #9 通過查核後延後合併**（因為 #9 的修法會使 `wfcli review` 在 preflight event writer 落地前寫不進任何裁決）。**請判斷本卡的合併順序建議在該裁定下是否仍成立。**

### 四、它主動避免讓 #9 無謂轉紅

它發現 #9 的 `checkpoint_cmd` 一個模組註冊**兩個**動詞（`checkpoint` ＋ `contract-baseline`，func 名為 `run_checkpoint`／`run_contract_baseline` **非 `run`**）。它第一版測試釘了「剛好一個動詞」與「func 必須叫 `run`」，**那會讓 #9 合併時無謂轉紅**；已放寬為「至少一個動詞」＋「每個動詞派到自己模組」。**#9 的寫入集一個字沒動。**

**請判斷放寬後的測試是否還擋得住它該擋的**。

### 五、執行者自陳六項無機械執行者，第 1 項最該打

> **現行 9 個動詞的 help 順序本身沒有任何測試釘住。** 快照 diff 只證明「本 commit 沒改變它」，測試釘的是「help 順序 = tuple 順序」這個**相對**不變性。有人重排 tuple，`--help` 就跟著變而全綠。

它明說這是**刻意取捨**：凍結的黃金順序清單會讓每張新動詞卡都得編輯 `test_cli_registry.py`，**正好重建本卡要消除的衝突點**。**請判斷這個取捨對不對。**

其餘五項：「每張新卡只需 append 一行」只在 #9 一個真實實例上機械證明過，對 #54／#55／#56 是**結構推論不是證據**；committed 測試的錯誤路徑用**合成 parser**，真實 parser 的 9×9 矩陣在快照 artifact **不在測試套件裡**；AST 檢查只擋它列舉過的動態化形狀；ruff 在**無設定檔的 ambient 規則集**下跑（repo 另有 15 項既有 findings 不在其檔內，依卡面未動）；「先合本卡代價較小」的後半段是**流程推論非機械證明**。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5265468601 · 2026-08-12T10:25:38Z

<!-- wf-review-receipt:v1
card_id: DEV-CLI-VERB-REGISTRY1
source_sha: a7e5e21993828fad016673d9cf81619e0535b599
report_sha256: e4cee5df0c43dd5b7333a09f0ddd15def67043cf9f5ea939d9d0b98df5c25c50
-->
取材規則：起點是本規則之後的下一個 `core_pain_resolved: yes` 行，終點是本留言 EOF；編碼 UTF-8；換行 LF；不 strip；排除上方 receipt HTML comment 與本取材規則行。
core_pain_resolved: yes
review_result: APPROVE
prior_accepted_blocking_findings:
  - status: "首輪，無前輪 accepted blocking finding"
    evidence: "Issue #53 派審詞指定 iteration 0，且 Issue 歷史沒有前輪 accepted blocking finding。"
self_run:
  - command: "git rev-parse a7e5e21993828fad016673d9cf81619e0535b599; git merge-base --is-ancestor e8a638c40f1028b6b85f6c59fd12ee9c1e85582d a7e5e21993828fad016673d9cf81619e0535b599"
    observed: "source SHA 完整相符；被審 commit 的唯一 parent 是 e8a638c40f1028b6b85f6c59fd12ee9c1e85582d；基線為祖先；相對基線僅三個宣告寫入檔。"
  - command: "PYTHONPATH=src /Users/ruanruan/Dev/ai-workflow/cli/.venv/bin/python -m pytest -q"
    observed: "在 source SHA 的 git archive 拋棄式目錄執行，701 passed in 40.50s。"
  - command: "uvx ruff check src/wf_cli/cli.py src/wf_cli/commands/__init__.py tests/test_cli_registry.py"
    observed: "在 source SHA 的 git archive 拋棄式目錄執行，All checks passed。"
  - command: "parser dump：對 e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 與 a7e5e21993828fad016673d9cf81619e0535b599 各自 archive，以同一獨立 Python 探針列舉 verbs、每個 argparse action 全欄位、top level 與逐 verb help、func、9 x 9 例外退出矩陣，再 cmp 與 sha256"
    observed: "兩份均 58383 bytes；sha256 均為 cebcf30a3c60d610fe952667a0fc7e27adfb025345f8dae5e66fb40d436791d5；cmp 相同。"
  - command: "PYTHONPATH=src Python 子行程逐一 import wf_cli 下 rglob 得出的每個模組"
    observed: "24 個模組，0 failures；字串 tuple 避免 eager import 循環。檔案系統與 COMMAND_MODULES 雙向比對及 43 個 registry tests 均通過，故模組名字串的拼字延遲風險已被機械補回。"
  - command: "git merge-base a7e5e21993828fad016673d9cf81619e0535b599 04c8e6211576e786a01afaae69cfb5fbe756bbe1; git merge-tree <merge-base> a7e5e21993828fad016673d9cf81619e0535b599 04c8e6211576e786a01afaae69cfb5fbe756bbe1"
    observed: "共同基線為 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0；cli.py 有兩段文字衝突。先合本卡的建議仍成立為後續整合順序，但受需求方已裁定 #9 通過查核後延後合併所約束；本卡可先合，#9 解除延後後須在 main 上解衝突並 append checkpoint_cmd。"
findings:
  - finding_id: "DEV-CLI-VERB-REGISTRY1-R1-001"
    severity: info
    blocking: false
    finding_class: governance
    attribution: planner
    root_cause_id: "unknown-DEV-CLI-VERB-REGISTRY1-R1-001"
    evidence: "現行 9 個動詞的黃金 help 順序未被絕對清單釘住；測試釘的是 help 順序等於顯式 tuple 順序。"
    disposition: "已裁定為可接受取捨：本次 dump 已證明既有順序不變，後續新增動詞只需 append，刻意調整既有順序仍應由其變更卡承擔審查，不在本卡建立新的共享衝突點。"

## Comment 5265654784 · 2026-08-12T10:44:24Z

<!-- wf-review-event:v1 card_id=DEV-CLI-VERB-REGISTRY1 source_sha=a7e5e21993828fad016673d9cf81619e0535b599 attempt_id=DEV-CLI-VERB-REGISTRY1-e0-a7e5e21993828fad016673d9cf81619e0535b599 -->
## 查核裁決：APPROVE

- 卡：`DEV-CLI-VERB-REGISTRY1`　attempt_id：`DEV-CLI-VERB-REGISTRY1-e0-a7e5e21993828fad016673d9cf81619e0535b599`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5265468601，PM 回讀重算 report_sha256=e4cee5df… 一次相符。⚠️ 該收據留言曾被編輯（created≠updated），PM 無法取得編輯前內容，雜湊以現行 body 重算相符）　escalation_epoch：0
- source_sha：`a7e5e21993828fad016673d9cf81619e0535b599`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-12T18:44:23+08:00

### self_run（查核者實跑）

- `git rev-parse a7e5e21993828fad016673d9cf81619e0535b599; git merge-base --is-ancestor e8a638c40f1028b6b85f6c59fd12ee9c1e85582d a7e5e21993828fad016673d9cf81619e0535b599`
  - source SHA 完整相符；被審 commit 的唯一 parent 是 e8a638c40f1028b6b85f6c59fd12ee9c1e85582d；基線為祖先；相對基線僅三個宣告寫入檔。
- `PYTHONPATH=src /Users/ruanruan/Dev/ai-workflow/cli/.venv/bin/python -m pytest -q`
  - 在 source SHA 的 git archive 拋棄式目錄執行，701 passed in 40.50s。
- `uvx ruff check src/wf_cli/cli.py src/wf_cli/commands/__init__.py tests/test_cli_registry.py`
  - 在 source SHA 的 git archive 拋棄式目錄執行，All checks passed。
- `parser dump：對 e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 與 a7e5e21993828fad016673d9cf81619e0535b599 各自 archive，以同一獨立 Python 探針列舉 verbs、每個 argparse action 全欄位、top level 與逐 verb help、func、9 x 9 例外退出矩陣，再 cmp 與 sha256`
  - 兩份均 58383 bytes；sha256 均為 cebcf30a3c60d610fe952667a0fc7e27adfb025345f8dae5e66fb40d436791d5；cmp 相同。
- `PYTHONPATH=src Python 子行程逐一 import wf_cli 下 rglob 得出的每個模組`
  - 24 個模組，0 failures；字串 tuple 避免 eager import 循環。檔案系統與 COMMAND_MODULES 雙向比對及 43 個 registry tests 均通過，故模組名字串的拼字延遲風險已被機械補回。
- `git merge-base a7e5e21993828fad016673d9cf81619e0535b599 04c8e6211576e786a01afaae69cfb5fbe756bbe1; git merge-tree <merge-base> a7e5e21993828fad016673d9cf81619e0535b599 04c8e6211576e786a01afaae69cfb5fbe756bbe1`
  - 共同基線為 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0；cli.py 有兩段文字衝突。先合本卡的建議仍成立為後續整合順序，但受需求方已裁定 #9 通過查核後延後合併所約束；本卡可先合，#9 解除延後後須在 main 上解衝突並 append checkpoint_cmd。

### findings（1，其中 blocking 0）

- **DEV-CLI-VERB-REGISTRY1-R1-001**　severity=info　blocking=false　class=governance　attribution=planner　root_cause_id=`unknown-DEV-CLI-VERB-REGISTRY1-R1-001`
  - evidence：現行 9 個動詞的黃金 help 順序未被絕對清單釘住；測試釘的是 help 順序等於顯式 tuple 順序。
  - disposition：已裁定為可接受取捨：本次 dump 已證明既有順序不變，後續新增動詞只需 append，刻意調整既有順序仍應由其變更卡承擔審查，不在本卡建立新的共享衝突點。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。
