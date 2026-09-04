# #84 DEV-RELEASE-STATUS-DONE1 release 同步 Projects Status=Done，免部署卡不再需要人工關 Issue
- state: open  created: 2026-08-13T08:20:58Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/84
- comments: 5

## Body

- 需求：ruan6047　規劃：—
- 執行：待指派　查核：待指派
- Initiative：—　spec 基線：docs/ROADMAP.md（origin/main 71df1570b7ddefbbbf101f8e8b1b053e5fe82cd7）§0 目標 1「防止低級事故」；§0 開卡前檢查第 2 問的答案是機械執行者本身——修法就在 release 動詞內，不是再加一個偵測器。
- DB：db_scope=none
- 服務的原始目標：讓「卡結案」與「看板 Status／Issue 關閉」是同一個動作的結果，不靠人記得補。

## 簡介
<!-- card-brief:begin -->
讓 handoff --next-stage release 在寫下交付狀態 🏁完成 的同時，一併把 Projects 的 Status 設為 Done——免部署卡沒有 deploy-state 那條路徑，Status 停在 Todo／In Progress、Issue 永遠開著（#124 靠人工補關）；並補兩個同根因守衛：降級路徑撞終態集合須拒絕（#35／#37／#41 曾被批次 handoff 降回待指派躺四天）、--source-sha 未經驗證時至少警告。適用時機：卡結案了但看板與 Issue 沒收斂、或 handoff 寫下的狀態與現實對不上時。⛔ 非射程：既有 release 閘門一字不動（需部署卡非 ✅已驗證 仍須拒絕且拒絕時不先寫 Status）；implementation／review 兩個 next-stage 不得動 Status；修法集中在 cli/src/wf_cli/commands/handoff_cmd.py，刻意不拆卡。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：handoff --next-stage release 只寫交付狀態 🏁完成，從不碰 Projects 的內建 Status。需部署卡剛好被 deploy-state 帶到 Done（✅已驗證 → Status=Done）而由 Projects 自動關閉 Issue；免部署卡沒有那條路徑，Status 停在 Todo／In Progress，Issue 永遠開著。2026-08-13 實測三卡對照：#125 與 #128 走部署路徑，release 後 Issue 自動關閉（timeline closed by ruan6047 07:10Z）；#124 TIME-TEST-CLOCK-INJECT1 免部署（只動測試與 CI），release 寫了 🏁完成、Issue 仍 OPEN，最後由 PM 手動 gh issue close 補上。也就是說『卡結案了沒有』在看板上有兩種相反的呈現，取決於一個與結案無關的屬性（有沒有部署），而收斂靠人記得。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/handoff_cmd.py",
    "file:cli/tests/test_commands_mocked.py",
    "file:cli/src/wf_cli/git_ops.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] handoff --next-stage release 在寫入交付狀態 🏁完成的同時，一併把 Projects 的 Status 設為 Done；寫法比照 deploy_state_cmd 既有作法（先檢查 fields[Status].options 含該選項，再走 update_item_field_value）;既有的 release 閘門一字不動：需部署卡在部署狀態非 ✅已驗證／—不適用 時仍須拒絕（canonical §0），且拒絕時不得先寫 Status;與 deploy-state 的既有 Status 寫入不得互相打架：需部署卡先被 deploy-state 帶到 Done、再 release 時重複寫 Done 必須是無害冪等;release 以外的 next-stage（implementation／review）不得動 Status，維持現行行為;⭐【2026-08-16 擴編・終態守衛】handoff 的降級路徑須檢查現行交付狀態是否落在終態集合；是則拒絕，除非帶顯式反轉旗標＋理由。2026-08-12 實測三張已 APPROVE 並結案的卡（#35／#37／#41）被同一筆批次 handoff ba4755f4 降回待指派並把 iteration 由 0 改為 1，在 Backlog 躺了四天。cleanup.classify_state 已有 illegal_terminal_before_cleanup 的同型判定可複用;⭐【2026-08-16 擴編・SHA 驗證】--source-sha 未經驗證時至少警告；若能在本機解析到 repo 則預設驗證。⚠️ --repo-path 是選用旗標而它是唯一會驗證 SHA 存在的東西——只在人記得帶時生效的檢查，對「人忘記」這個失效模式沒有作用。PM 於 2026-08-16 寫入一個不存在的 40 碼 SHA（前 7 碼取自 git log --oneline、後 33 碼自行編造），同 session 內第二次；前一次因帶了 --repo-path 而被拒收。須說明「無法解析 repo」時的行為，且不得因此靜默放行;⚠️ 三項共用一個根因——handoff 寫下的狀態沒有任何東西檢查它是否對應現實：事件說 🏁完成而看板仍 Todo、事件說待指派而卡已結案、事件說交付在某 SHA 而該物件不存在。修法皆落在 handoff_cmd.py，拆卡會讓同一個檔被改三次、三輪查核;變異檢驗：三項各自須有「拿掉守衛就轉紅」的證明。終態守衛那條須以真實的降級序列重放（#35／#37／#41 的時序已完整留在各卡 Log）

## 驗證

- [ ] cli/tests 補測試覆蓋兩條路徑：免部署卡 release → Status=Done；需部署卡未 ✅已驗證 → 拒絕且 Status 未被寫
- [ ] 以 2026-08-13 的 #124（免部署，曾需人工關）與 #125／#128（需部署，自動關）為對照，說明修正後兩者收斂為同一行為
- [ ] uv run pytest（cli/）不退步
## Log

- 2026-08-13T16:20:56+08:00 open by —；owner 待指派；iteration 0。
- 2026-08-16T11:26:07+08:00 amend by wf-cli（op f25e0daa）→ 驗收條件：原值「[ ] handoff --next-stage release 在寫入交付狀態 🏁完成的同時，一併把 Projects 的 Status 設為 Done；寫法比照 deploy_state_cmd 既有作法（先檢查 fields["Status"].options 含該選項，再走 update_item_field_value），不新增欄位定義；[ ] 既有的 release 閘門一字不動：需部署卡在部署狀態非 ✅已驗證／—不適用 時仍須拒絕（canonical §0），且拒絕時不得先寫 Status；[ ] 與 deploy-state 的既有 Status 寫入不得互相打架：需部署卡先被 deploy-state 帶到 Done、再 release 時重複寫 Done 必須是無害冪等；[ ] release 以外的 next-stage（implementation／review）不得動 Status，維持現行行為」→ 新值「handoff --next-stage release 在寫入交付狀態 🏁完成的同時，一併把 Projects 的 Status 設為 Done；寫法比照 deploy_state_cmd 既有作法（先檢查 fields[Status].options 含該選項，再走 update_item_field_value）;既有的 release 閘門一字不動：需部署卡在部署狀態非 ✅已驗證／—不適用 時仍須拒絕（canonical §0），且拒絕時不得先寫 Status;與 deploy-state 的既有 Status 寫入不得互相打架：需部署卡先被 deploy-state 帶到 Done、再 release 時重複寫 Done 必須是無害冪等;release 以外的 next-stage（implementation／review）不得動 Status，維持現行行為;⭐【2026-08-16 擴編・終態守衛】handoff 的降級路徑須檢查現行交付狀態是否落在終態集合；是則拒絕，除非帶顯式反轉旗標＋理由。2026-08-12 實測三張已 APPROVE 並結案的卡（#35／#37／#41）被同一筆批次 handoff ba4755f4 降回待指派並把 iteration 由 0 改為 1，在 Backlog 躺了四天。cleanup.classify_state 已有 illegal_terminal_before_cleanup 的同型判定可複用;⭐【2026-08-16 擴編・SHA 驗證】--source-sha 未經驗證時至少警告；若能在本機解析到 repo 則預設驗證。⚠️ --repo-path 是選用旗標而它是唯一會驗證 SHA 存在的東西——只在人記得帶時生效的檢查，對「人忘記」這個失效模式沒有作用。PM 於 2026-08-16 寫入一個不存在的 40 碼 SHA（前 7 碼取自 git log --oneline、後 33 碼自行編造），同 session 內第二次；前一次因帶了 --repo-path 而被拒收。須說明「無法解析 repo」時的行為，且不得因此靜默放行;⚠️ 三項共用一個根因——handoff 寫下的狀態沒有任何東西檢查它是否對應現實：事件說 🏁完成而看板仍 Todo、事件說待指派而卡已結案、事件說交付在某 SHA 而該物件不存在。修法皆落在 handoff_cmd.py，拆卡會讓同一個檔被改三次、三輪查核;變異檢驗：三項各自須有「拿掉守衛就轉紅」的證明。終態守衛那條須以真實的降級序列重放（#35／#37／#41 的時序已完整留在各卡 Log）」；理由 需求方 2026-08-16 裁定射程擴為 handoff 的三個「寫入未經驗證的狀態」缺陷（裁定全文見 issuecomment-5305522558）。三者同檔同根因，拆卡不划算。同時補記本卡痛點的第二筆可驗證實例：#63 於 2026-08-13 APPROVE 且碼進 main，Issue 至今 OPEN，因為沒有人跑 release、也沒有任何東西提醒該跑。資源宣告加入 git_ops.py（SHA 驗證可能需要）。。
- 2026-08-16T11:26:07+08:00 amend by wf-cli（op f25e0daa）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/commands/handoff_cmd.py", "file:cli/tests/test_commands_mocked.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/commands/handoff_cmd.py、file:cli/tests/test_commands_mocked.py、file:cli/src/wf_cli/git_ops.py」；理由 需求方 2026-08-16 裁定射程擴為 handoff 的三個「寫入未經驗證的狀態」缺陷（裁定全文見 issuecomment-5305522558）。三者同檔同根因，拆卡不划算。同時補記本卡痛點的第二筆可驗證實例：#63 於 2026-08-13 APPROVE 且碼進 main，Issue 至今 OPEN，因為沒有人跑 release、也沒有任何東西提醒該跑。資源宣告加入 git_ops.py（SHA 驗證可能需要）。。
- 2026-08-26T21:02:54+08:00 amend by wf-cli（op 12234abc）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:31161abd1318fefeeccd573d1f5679e033806b24d09b15bb27a33242a720d6b5 (805 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。
- 2026-08-29T14:50:05+08:00 handoff by wf-cli → owner —；iteration 0；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 停卡裁定：https://github.com/ruan6047/ai-workflow/issues/84#issuecomment-5460904264 （內建 Status 已退出 view 並將退位，本卡前提被推翻）。


## Comment 5305522558 · 2026-08-16T03:25:26Z

## 需求方裁定：射程擴為 `handoff` 的三個「寫入未經驗證的狀態」缺陷（2026-08-16）

需求方 2026-08-16 裁定把本卡射程由「release 同步 Status」擴為**同一個檔的三件事**。三者共用一個根因：

> **`handoff` 寫下的狀態，沒有任何東西檢查它是否對應現實。**

### 一、原射程：release 不寫 Projects Status（不變）

痛點與四條驗收條件維持原狀。

**新增實例（本日實測）**：`#63 DEV-COMMIT-TRAILER-GUARD1` 於 2026-08-13 06:11 APPROVE、06:18 碼進 main（`d0397e0cbefd7a0e88de7ddfd3fa789dd7dcd5cc`，squash merge），**ROADMAP 記為 ✅已合併，而 Issue 至今 OPEN**——因為沒有人跑 release，也沒有任何東西提醒該跑。這是繼 `#124` 之後可驗證的**第二筆**。

### 二、⭐ 新增：`handoff` 可以把已達終態的卡降級，無守衛

**2026-08-12 實測，三張卡被同一筆批次 handoff（`ba4755f4`）誤傷：**

```
#37  12:23:39 APPROVE → 12:25:46 結案(iteration 0) → 23:11:03 降回 待指派(iteration 1)
#41  17:00:35 APPROVE → 17:15:32 結案(iteration 0) → 23:11:23 降回 待指派(iteration 1)
#35  16:59:52 APPROVE → 17:15:11 結案(iteration 0) → 23:10:41 降回 待指派(iteration 1)
```

三份降級的證據欄**逐字完全相同**（批次模板），其理由為「降級不是關閉——本卡載有真實 finding 的紀錄，**關閉會讓那些發現消失**」——**那句話預設發現尚未交付**，而這三張都已 APPROVE 並結案。**理由本身證明了執行時不知道它們的狀態。**

三張已於 2026-08-16 依需求方裁定還原終態，`iteration` 釘回 0。

**要求**：`handoff` 的降級路徑須檢查現行交付狀態是否落在終態集合；是則拒絕，除非帶顯式反轉旗標＋理由。`cleanup.classify_state` 已有 `illegal_terminal_before_cleanup` 的同型判定可複用。

### 三、⭐ 新增：`--source-sha` 在無 `--repo-path` 時接受任意 40 字元字串

**2026-08-16 PM 實犯，同一 session 內第二次：**

```
寫入  d0397e0be5b0ad0b3c19c7b1e5ac9e0c9e9cb0e1   ← 前 7 碼取自 git log --oneline，後 33 碼 PM 自行編造
實際  d0397e0cbefd7a0e88de7ddfd3fa789dd7dcd5cc
git cat-file -e <寫入的> → 失敗，該物件不存在
```

前一次是 `cpbl-analytics #120` 的 release，**同樣以補零湊足 40 碼；那次因帶了 `--repo-path` 而被當場拒收**。本次沒帶，於是沒有東西擋。

⚠️ **`--repo-path` 是選用旗標，而它是唯一會驗證 SHA 存在的東西。** 一個只在人記得帶的時候才生效的檢查，對「人忘記」這個失效模式沒有作用——而事件 log 是 append-only，錯誤的 SHA 無法移除，只能以後續事件覆蓋更正。

**要求**：`--source-sha` 未經驗證時至少警告；若能在本機解析到 repo（多數情形可）則預設驗證。**須說明「無法解析 repo」時的行為，且不得因此靜默放行。**

### 為什麼三件合一張

它們是同一個函式、同一個根因的三個面：

| | 事件說 | 現實 |
|---|---|---|
| 一 | 交付狀態 `🏁完成` | 看板 Status 仍 Todo、Issue 仍開著 |
| 二 | 卡是 `待指派`／`iteration 1` | 卡已 APPROVE 並結案、從未回來第二輪 |
| 三 | 交付在某 40 碼 SHA | 該物件不存在 |

**三者都是「事件 log 記了一件不為真的事」**，而三者的修法都落在 `handoff_cmd.py`。拆成三張會讓同一個檔被改三次、三輪查核。

### 資源宣告（擴編後，以本則為準）

```
db_scope=none
file:cli/src/wf_cli/commands/handoff_cmd.py
file:cli/tests/test_commands_mocked.py
file:cli/src/wf_cli/git_ops.py          ← SHA 驗證可能需要
```

⚠️ 若實作需要射程外的檔（例如 `cleanup.py` 的終態集合），**停下來回報，不要自行擴編**。


## Comment 5366333932 · 2026-08-21T07:01:54Z

## 卡面更正（需求方 2026-08-21 裁定）：缺陷 1 已不重現，派工前必須先改寫

PM 代擬代貼。需求方 2026-08-21 裁定本卡**先改寫再排程**，`#91` 維持 Backlog。

### ⭐ 缺陷 1「免部署卡 release 後 Issue 永遠開著，PM 手動補關」——**今天不重現**

本卡的招牌宣稱，PM 以七張卡實測，**七次全部不成立**：

| 卡 | 部署狀態 | 交付狀態 | Project Status | Issue |
|---|---|---|---|---|
| `cpbl#154 #155 #156 #159 #134 #157` | —不適用 | 🏁完成 | **Done** | **CLOSED** |
| **`cpbl#124`**（本卡自己引用的證據） | —不適用 | 🏁完成 | **Done** | **CLOSED** |

**機制**（`cleanup.py:1743-1746`）：

```python
if effect_writer is not None and mid.cleanup_done:
    if mid.issue_open:
        effect_writer.close_issue(target)
```

`--cleanup` 完成 → **wfcli 關 Issue** → GitHub 內建自動化「Issue 關閉 → Status=Done」。

⚠️ **卡面的機制描述是對的**（`handoff_cmd.py` 對 `fields["Status"]` 命中 0），**但結論錯了**：Status 不是 handoff 寫的，是 Issue 一關就被自動化設的。**真正的斷點在 `--cleanup` 的破壞性守衛拒收的那一刻**，不是 release 本身。

**對照組**：`cpbl#79`／`#81` 因卡在部署閘門而未 release ⇒ 未 cleanup ⇒ Issue 未關 ⇒ **Status = Todo**，`#80`（正常 release）則是 Done。

⚠️ **且本卡修完也不會解開 `cpbl#79`／`#81`**：本卡射程是**免部署卡**，那兩張是**需部署卡**卡在「部署 ✅已驗證 前不得 release」，而那是需求方 2026-08-18 明著接受的狀態（不造假的事件序）。**兩件事根因不同，不要在本卡順手處理。**

### ✅ 缺陷 2「handoff 可把終態卡降級，無守衛」——**成立，且完全沒守衛**

`TERMINAL_STATUSES` 在 `handoff_cmd.py:85` import，**全檔唯一使用點是 `:493`**，而那是餵給 cleanup 守衛的參數（`terminal_status_written=...`），**不是降級前的檢查**。`run()`（`:309` 起）的前置檢查只有：source_sha 格式、`--cleanup` 旗標配對、`--repo-path` 條件式 SHA 存在、release 的部署狀態閘門——**沒有任何一條看現行交付狀態是不是終態**。

已實現後果：`ai-workflow#35`／`#37`／`#41` 被同一筆批次 handoff（`ba4755f4`）從已結案降回待指派、iteration 0→1，在 Backlog 躺四天。

**⇒ 這是本卡改寫後的主體。**

### ⚠️ 缺陷 3「`--source-sha` 不驗證」——**成立，但比卡面窄**

`:311 validate_source_sha` 只驗 40 碼 hex 格式；真實存在檢查在 `:326 if args.repo_path:` → `git_ops.commit_exists`。

⚠️ **但 `:319-322` 強制 `--cleanup` 必須帶 `--repo-path`** ⇒ **release 路徑其實驗得到**。缺口只在**非 release 的 handoff**（assign／implementation／review 階段未帶 `--repo-path` 時）。2026-08-16 PM 寫入編造 40 碼 SHA 那次正是這條。

**⇒ 射程須縮到「非 release 路徑」，不要寫成全域缺陷。**

### 改寫後的卡面應該是

**核心痛點**：`handoff` 可以把終態卡降級回待指派而沒有任何守衛；且非 release 路徑的 `--source-sha` 只驗格式不驗存在。

**非目標（明列，否則執行者會做白工）**：
- ⛔ **不做「release 同步 Projects Status=Done」**——GitHub 內建自動化在 Issue 關閉時已提供，實測七次成立。
- ⛔ 不處理 `cpbl#79`／`#81` 那類需部署卡的 release 閘門——不同根因，且 2026-08-18 已明著接受。

### 派工前的既有障礙（未解，記錄）

⚠️ 本卡與 `#91` 同在 `cli/tests/test_commands_mocked.py` 的宣告 clique（六張卡宣告同一檔：`#57`／`#66`／`#84`／`#86`／`#91`／`#105`）。今天不響是因為 21 張全部 `owner=待指派`，`assign_cmd.py:227-230` 的 `find_conflicts` 對未認領的卡 `continue`。**一旦開始派工，本卡與 `#91` 不能並行。**


## Comment 5366510968 · 2026-08-21T07:19:37Z

## ⚠️ 更正前一則改寫，並補一個新缺陷（2026-08-21）

PM 代擬代貼。**本則推翻同日稍早那則改寫留言的第一節。**

### 一、我上一則說「缺陷 1 今天不重現」——**錯了，我只取了會通過的樣本**

前一則以七張卡（`cpbl#154 #155 #156 #159 #134 #157` ＋ `#124`）為據，宣稱免部署卡 release 後 Issue 會正常關閉。**那七張全都跑過 `--cleanup`**。母體不是那樣。

**全盤掃描（2026-08-21）：**

| | |
|---|---|
| open issues 合計 | **73**（cpbl-analytics 52 ＋ ai-workflow 21） |
| 其中「交付狀態已是終態」但 Issue 仍 OPEN | **20（27%）** |
| ├ `📦已合併` | 5：`cpbl#79 #81 #90 #96 #98` |
| ├ **`🏁完成`** | **11**：`cpbl#99 #101 #103 #106 #107 #112 #113 #116 #120 #123 #141` |
| └ `🛑已停止` | 4：`cpbl#115 #135 #158`、`ai-workflow#45` |

⚠️ `cpbl#113` 更是 `Status=In Progress`。

**⇒ 真正非終態的 open 只有 53。看板上 27% 的「活卡」是假的。**

⚠️ 這是 `verification-sample-must-be-a-passing-one` 那個形狀：**隨手取的樣本恰好都在成功路徑上**。前一則的結論作廢，缺陷 1 **成立**。

### 二、但機制不是卡面寫的那樣

卡面說「release 只寫交付狀態，**從不碰 Projects Status**」。機制描述對（`handoff_cmd.py` 對 `fields["Status"]` 命中 0），**推論錯**。

實際鏈路：**`--cleanup` 完成 → `cleanup.py:1745 effect_writer.close_issue(target)` → GitHub 內建自動化「Issue 關閉 → Status=Done」**。

量測佐證：

```
#123（🏁完成 + OPEN）body 內「收尾清理」→ 0 次
#141（🏁完成 + OPEN）                    → 0 次
#157（今日，CLOSED，Status=Done）        → 1 次
```

**⇒ 正確的痛點敘述是：「release 不關 Issue；只有 `--cleanup` 會，而 `--cleanup` 經常沒跑或跑不了。」** 跑不了的原因至少三種：`:319-322` 強制要 `--repo-path`、要真的有 worktree／分支可清、守衛可拒收。

### 三、⭐ 新缺陷：`NO_CLEANUP_WARNING` 是靜態字串，分類錯誤，且勸退唯一有效的補救

`handoff_cmd.py:95-102`：

```python
#: 不帶 ``--cleanup`` 的 release 會造出「終態已寫、清理未做」的組合。這不是猜測，
#: 是 `cleanup.classify_state` 對該組合的分類名稱。
NO_CLEANUP_WARNING = (
    "…而終態已經寫下去了——依 WF_CLEANUP_GUARD1 的分類，這是 illegal_terminal_before_cleanup。"
    "守衛不自動修復非法態，事後再補 --cleanup 會被擋，屆時只能人工收尾。"
)
```

**「這不是猜測」——是猜測。** 該字串是常數，**不觀測任何狀態**就印出來。

`cleanup.py:1312-1325` 的 `classify_state` 是全函數（`test_cleanup.py::test_classification_is_total` 窮舉 32 格）：

```python
if not obs.cleanup_done:
    if obs.effect_started: return "illegal_terminal_before_cleanup"
    return "cleanup_in_progress"
if obs.effect_done:    return "completed"
if obs.effect_started: return "effect_in_progress"
return "cleanup_done_effect_pending"
```

而 `cleanup_done`（`:1274-1287`）＝**授權範圍內的 worktree／本地分支／遠端分支皆不存在**。

⭐ **對「從未派工、沒有 worktree 也沒有分支」的卡，三者本來就都不存在 ⇒ `cleanup_done = True` ⇒ 走不到 illegal 分支。** 其真實分類是 **`effect_in_progress`**，而：

```python
LEGAL_STATES = frozenset({"cleanup_in_progress", "cleanup_done_effect_pending",
                          "effect_in_progress", "completed"})   # cleanup.py:1307-1309
```

**`effect_in_progress` 在合法集合裡。**

**所以那句警示錯兩次：**

1. **分類錯**：宣告 illegal，實際 legal。
2. ⭐ **補救方向有害**：拒收路徑（`:1600`）只在 `classify_state(before) == "illegal_terminal_before_cleanup"` 時觸發。這類卡不落在那一格，**重跑一次 `--cleanup` 不會被擋**——它會通過、發現沒東西可清、然後執行 `close_issue`。**警示卻告訴你補救無效。**

### 四、活體標本：`ai-workflow#45`（今日產生，可重現）

2026-08-21 15:04，PM 對從未派工的 `#45` 下 `handoff --next-stage release --status 🛑已停止`（無 `--cleanup`），逐字收到上述警示。現況：

```
交付狀態 = 🛑已停止   Issue = OPEN   Status = Todo   分支worktree = —
```

依 `classify_state` 應為 `effect_in_progress`（legal），警示卻說 illegal 且不可補救。**它是那 20 張裡最新的一張，且成因與其餘同族。**

⚠️ 同一次操作 PM 還漏帶 `--iteration 0`，iteration 被自動遞增 0→1（謊稱本卡曾被退回），已於 15:07 以第二則 handoff 釘回 0。**那也是本卡缺陷 2 家族的一次真實命中**——只是方向相反（自動遞增而非降級），可一併納入射程考慮。

### 五、改寫後的卡面建議

**核心痛點**（取代原文）：`release` 寫下終態但不關 Issue，而唯一會關的 `--cleanup` 經常沒跑或跑不了，於是狀態面上 27% 的 open issue 是終態卡；同時 `handoff` 對終態卡的降級無守衛、非 release 路徑的 `--source-sha` 只驗格式。

**驗收條建議加一條可量的**：`(終態交付狀態 ∧ Issue OPEN)` 的卡數由 **20 降為 0**，且新增一次 release 後不再產生。

**新增射程**：`NO_CLEANUP_WARNING` 須改為**觀測後才下分類**，或降級為「本次未清理」的中性陳述；現行文字在勸退有效補救。

**非目標（維持）**：⛔ 不做「release 直接寫 Projects Status」——Status 由 Issue 關閉觸發的內建自動化提供，實測成立。⛔ 不處理 `cpbl#79`／`#81` 那類需部署卡的 release 閘門（不同根因，2026-08-18 已明著接受）。

### ⚠️ 未查證（明列）

1. **那 20 張逐張的真實分類沒有量**——有多少是 `effect_in_progress`（重跑 `--cleanup` 即可救）、多少是 `illegal_terminal_before_cleanup`（worktree／分支仍在、真卡住），取決於各自資源現況。逐張量需要跑破壞性指令，PM 未在無需求方在場時執行。
2. **「重跑 `--cleanup` 會成功」是讀碼推論，未實測。** 依 `:1600` 的條件與 `classify_state` 的全函數性質應成立，但沒有跑過一次。
3. `cpbl#79`／`#81` 的 OPEN 是需求方 2026-08-18 明文接受的狀態，**不應計入「該修的 20 張」**——實際待修上限是 18。


## Comment 5368611854 · 2026-08-21T10:23:25Z

## ⭐ 新缺陷（2026-08-21 實測產生）：`release --cleanup` 對「終態已寫」的卡**回報失敗但副作用已落地**

PM 代擬代貼。本則是今日實際跑 12 張假活卡收尾時撞出來的，**不是讀碼推論**。

### 現象

對 8 張**交付狀態已是 `🏁完成`** 的假活卡跑 `handoff --next-stage release --status 🏁完成 --cleanup`，全部印出：

```
[handoff] 拒絕：第 4 步的寫入順序異常（終態不是最後一步）
  - 其後義務（不寫狀態面、不阻擋 release）：第 5、6、7 步仍待完成
```

**但事後查證，八張 Issue 全部 CLOSED、Project `Status` 全部 `Done`、交付狀態全部 `🏁完成`。**

```
#103 CLOSED  #106 CLOSED  #107 CLOSED  #112 CLOSED
#113 CLOSED  #120 CLOSED  #123 CLOSED  #141 CLOSED
```

⭐ **指令回報拒絕，效果已經落地。**

### 成因（讀碼確認）

`cli/src/wf_cli/cleanup.py:1743-1749`：

```python
if effect_writer is not None and mid.cleanup_done:
    if mid.issue_open:
        effect_writer.close_issue(target)              # ← 執行了
    if not mid.terminal_status_written:
        effect_writer.write_release_terminal(...)      # ← 跳過（終態早就寫過）
```

`cli/src/wf_cli/commands/handoff_cmd.py:518`：

```python
if writer.calls and writer.calls[-1] != "write_release_terminal":
    print("[handoff] 拒絕：第 4 步的寫入順序異常（終態不是最後一步）", file=sys.stderr)
```

⭐ **對終態已寫的卡，`write_release_terminal` 不會被呼叫**，於是 `writer.calls == ["close_issue"]`，`calls[-1] != "write_release_terminal"` 成立 → 判為順序異常。

**那個檢查假設「最後一次寫入必定是終態寫入」。對「終態已寫、只需關 Issue」的卡，該假設不成立。**

### 對照組（同一批，同一次操作）

`#96`／`#98` 的交付狀態是 **`📦已合併`**——⚠️ 而 `📦已合併` **不在** `TERMINAL_STATUSES`（`assign_cmd.py:89` = `{"🏁完成", "🛑已停止"}`）內，故 `terminal_status_written=False` → `write_release_terminal` **有**被呼叫 → `calls[-1]` 正確 → **兩張都正常回報 `已交接`**。

**所以這個缺陷只打在「交付狀態已是 `🏁完成`／`🛑已停止` 而 Issue 仍開著」的卡上——而那正是本 repo 今天要收的那一族。**

### 為什麼這比看起來嚴重

1. **回報失敗但副作用落地**，是「失敗留下像成功的產物」的反面——**成功留下像失敗的回報**。腳本化收尾會判為失敗並重試；重試在本例是冪等的（Issue 已關），但**操作者會以為沒收到，而實際上收到了**。
2. ⚠️ **它讓「12 張收乾淨了」這件事必須靠事後逐張查 Issue state 才確認得了**，指令本身的回報不可信。今天 PM 就是這樣發現的。
3. **它與本卡缺陷 1 是同一條鏈的兩端**：缺陷 1 讓 Issue 關不掉（`--cleanup` 沒跑），這一條讓「補跑 `--cleanup`」的回報不可信。

### 建議的處置（不是裁定）

`handoff_cmd.py:518` 的判準應改為「**已呼叫的寫入中，若含 `write_release_terminal` 則它必須是最後一個**」，而不是「最後一個必須是 `write_release_terminal`」。⭐ 這樣：
- 終態未寫的卡：`calls == ["close_issue", "write_release_terminal"]` → 通過（與現行相同）
- 終態已寫的卡：`calls == ["close_issue"]` → 通過（現行誤判）
- 真正的順序異常：`calls == ["write_release_terminal", "close_issue"]` → 仍被擋

### ⚠️ 未查證

1. **未實測修法**——上述判準是讀碼推導，PM 未改碼也未跑。
2. **未窮舉 `writer.calls` 的其他可能組合**（例如 `cleanup_done=True` 但 `issue_open=False` 時 `calls` 為空——此時 `if writer.calls` 短路，不觸發檢查；PM 沒有構造該情形驗證）。
3. **未查證這個缺陷是否曾在今日之前咬過人**——今天是本 repo 第一次批次補跑 `--cleanup`。


## Comment 5460904264 · 2026-08-29T06:49:42Z

## 停卡裁定

**決策**：停止。

**原因**：本卡痛點逐字為「`handoff --next-stage release` 只寫交付狀態 🏁完成，從不碰 Projects 的內建 Status」。該前提已被 2026-08-29 的定案推翻——內建 `Status` 已從 Project #4 兩個 view 的可見欄位移除，且依同日定案將隨部署狀態一併退位為記錄、不再作為狀態載體。⇒ 讓 release 去同步一個正在退位的欄位，方向相反。

**可證偽的復活條件**：內建 `Status` 被保留為狀態載體（而非退位為記錄），或它重新出現在看板 view 的可見欄位中。

**未涵蓋**：本卡附帶提到的「免部署卡不再需要人工關 Issue」不屬本卡痛點——關閉 Issue 由 Project 的 `Auto-close issue` workflow 負責，與本卡無關。若該需求仍在，須另行登記。

**裁定者**：需求方 ruan6047，2026-08-29 本 session 對話中確認射程為 ai-workflow repo 的卡。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

