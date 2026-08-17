# 契約↔工具對帳表（WF-REVIEW-INVALID-TRACE1）

> 契約文件宣告了一批**事件型別／交付狀態／卡面欄位**，寫入通道 `wfcli` 只實作了一部分，
> 兩者從來沒有對過帳——於是缺口是**撞出來的，不是找出來的**。2026-08-16 一天內踩到五個，
> 全部靠實際操作失敗才發現。本檔把「有幾個洞」變成可重跑的機械輸出。

**本檔不實作任何一項修補。** 第一交付物是這張表；補哪些、哪些寫成已知限制、哪些從契約
移除，由需求方依本表決定要不要開卡、開幾張。

## 1. 怎麼重跑

```bash
python3 scripts/contract_tool_reconcile.py              # Markdown 對帳表
python3 scripts/contract_tool_reconcile.py --gaps-only  # 只列缺口
python3 scripts/contract_tool_reconcile.py --format json
python3 scripts/contract_tool_reconcile.py --check      # 與本檔 §6 的登記逐項對帳
```

測試在 `cli/tests/test_contract_tool_reconcile.py`（`cd cli && uv run pytest
tests/test_contract_tool_reconcile.py`）。

## 2. universe 是掃出來的，不是登記的

契約側的符號集合**由掃描文件導出**，`scripts/contract_tool_reconcile.py` 裡沒有任何
「已知事件清單」常數。三條語法規則：

- **事件型別**＝契約文件裡反引號包住的 kebab-case token。canonical §4.1 的 lifecycle
  event envelope 有 `type` 欄，而文件中每個被當成事件名的東西都寫成這個形狀。判準是**詞法**
  而不是語意——語意判準需要一份「哪些是事件」的人維護清單，那正是本卡要消滅的東西。
- **交付狀態**＝emoji ＋ 緊接的非空白 token。emoji 以 Unicode 區段界定，不列舉具體 emoji。
- **卡面欄位**＝`templates/*card*.md` 標頭條列的 `- <名稱>：`／`　<名稱>：` 與 `## <名稱>`
  章節標題。

射程用 glob（`templates/*.md`）而不是列檔名：新增一份範本自動進射程。

規則刻意**過度抽取**：`data-migration`（`db_scope` 值）、`ubuntu-latest`（ROADMAP 裡的
CI runner）這類非事件符號也會進表。多抽一列的代價是表上多一行；漏抽一個的代價是那個洞繼續
看不見。過抽的項目多半有讀取者、因此不會被判成缺口，真正沒有實作的才會浮出來（§6 逐項標了
哪些是過抽）。

### 2.1 為什麼工具側不用 `grep`

`review-invalid` 這個字串**確實出現在** `cli/src/wf_cli/commands/review_cmd.py`——出現在
一個 `print()` 的引數裡。任何「grep 命中就算有實作」的判定都會把它判成已實作，而那正是本卡
要抓的反面。

判定走 `ast` ＋ `tokenize`，把每一次字面出現分類成 comment／docstring／診斷輸出／散文引述／
讀取／詞彙表／寫入，**只有真正流進遠端寫入呼叫的才算 writer**。呼叫圖的節點是「模組.函式」
而非裸函式名；裸名版本讓 `gh.execute` 裡的 `subprocess.run` 連到了 `assign_cmd.run`，於是
`amend_cmd → … → find_conflicts` 憑空可達——**已知缺口 #4 剛好被這條假邊藏住**。

### 2.2 三個判定各自的反證條件

每條檢查都要答得出「什麼結果會讓它不成立」，否則它不是檢查。

| 判定 | 什麼結果會讓它不成立 | 釘住它的測試 |
|---|---|---|
| universe 由文件導出 | 在契約文件新增一個 kebab 符號後重跑，它沒有進表 | `test_new_symbol_in_canonical_appears_without_touching_the_tool`（含反方向：刪掉就該消失） |
| writer 判定量的是位置不是字串存在 | 把符號從 `print()` 搬到寫入路徑上，判定沒有翻面（或搬回去仍判成 writer） | `test_symbol_only_inside_print_is_not_a_writer` ＋ `test_same_symbol_becomes_a_writer_when_it_reaches_the_state_plane` |
| amend 可改性讀的是碼 | 新增一個 `amend_*` 函式並 import 之後，欄位仍判成「改不動」 | `test_adding_an_amend_function_flips_amendability` |
| 狀態的「專責動詞」軸有鑑別力 | 某狀態加上動詞之後判定沒有翻面 | `test_status_with_a_verb_is_not_a_gap` |
| 守衛覆蓋有鑑別力 | 接上守衛之後缺口沒有消失 | `test_calling_the_guard_clears_the_gap` |
| `--check` 不讀時鐘 | 不動任何碼與文件，兩次重跑一次綠一次紅 | `test_check_does_not_read_the_clock` ＋ `test_reconciler_source_contains_no_clock_calls` |
| 守衛覆蓋缺口也在 ratchet 內 | 接上守衛使缺口消失後 `--check` 仍是綠的 | `test_guard_gaps_are_covered_by_check` |
| 表不是空的／不是全紅 | 三個 kind 有任一個沒有任何 `ok` 或沒有任何缺口 | `test_live_table_is_not_vacuous` |

### 2.3 為什麼 §6 的處置表不是第二份人維護清單

處置表能做的只有**承認**缺口，不能**消除**缺口。`--check` 三個方向都會紅：

1. 有缺口而未登記處置 → 紅（契約長出新東西沒人處置時的可見失敗）；
2. 登記了一個已不存在的缺口 → 紅（缺口被補掉時強制回來更新本檔）；
3. 同一符號的判定變了 → 紅。

所以**刪掉一列不會讓檢查變綠**——刪掉即變成第 1 種。universe 本身仍完全由 §2 的掃描決定，
本檔碰不到它。

### 2.4 變異檢驗（實跑，非宣稱）

以下四個變異各自套用在乾淨樹上、跑 `cd cli && uv run pytest
tests/test_contract_tool_reconcile.py`、記錄紅綠、還原。基準是 33 passed。

| 變異 | 改法 | 結果 |
|---|---|---|
| **M1** universe 改成人登記的清單 | `build_universe` 直接回傳一個寫死的四元素列表 | **15 failed**，含驗收條 5 的主檢 `test_new_symbol_in_canonical_appears_without_touching_the_tool`，以及正控組 3 與 5 |
| **M2** `print()` 引數也算 writer（＝退回 grep 語意） | `_syntactic_role` 對 `DIAGNOSTIC_CALLS` 回 `ROLE_OTHER` | **3 failed**：`test_symbol_only_inside_print_is_not_a_writer`、正控組 1、`--check` |
| **M3** 呼叫圖恢復「同名全集」退路 | `resolve` 末行改回 `by_name.get(name, set())` | **2 failed**：`test_unresolvable_calls_do_not_create_call_graph_edges`、**正控組 4** |
| **M4** 從 §6 處置表刪掉一列 | 刪 `event/review-invalid` 那一行 | `--check` 退出碼 1，訊息「缺口未登記處置：event/review-invalid」；**1 failed** |

⚠️ **M3 順帶抓到一個真的洞。** 它讓正控組 4（`amend` 繞過 `find_conflicts`）整個消失，
而當時的 `--check` **仍然是綠的**——因為第一版只把符號列納入 ratchet，守衛覆蓋缺口完全
不在比對範圍內。**沒被 ratchet 蓋住的檢查等於沒有檢查。** 已修：守衛缺口以
`guard/<寫入入口>→<資料模組>` 為鍵一併登記，並補 `test_guard_gaps_are_covered_by_check`。
這一項是變異檢驗自己找出來的，不是設計時想到的。

## 3. 五個已知實例（正控組）

這五個是 2026-08-16 撞出來的。它們全部出現在表中，判定如下——**五個都在，才證明對帳器在量
東西**。逐項的自動斷言見 `test_control_1..5`。

1. **`review-invalid`** → `mention-only`、writer 0。字面出現在
   `commands/review_cmd.py:218` 的 `print()`、`:214` 的註解、`:1` 的 docstring 與
   `validation.py:52` 的訊息常數。**契約 §1 把它列在「結果／事件」欄，機器偵測得到
   （`validation.review_invalid_reasons`），偵測完只印 stderr 然後 `return 4`。**
2. **`preflight-failed`** → `mention-only`、writer 0、`相關動詞=無`。整個 `cli/src` 只有
   `review.py:627` 的一行 `#` 註解。連偵測都沒有。
3. **`⏸阻塞`** → `read-only`、`Project 選項=是`、`專責動詞=否`。字面只在
   `project.py:41` 的 `FIELD_SPECS` 列舉裡；`amend_cmd.py:463` 的 docstring 與
   `review_cmd.py:296` 的註解都只是提及。契約 §1 另有 `status-change → ⏸阻塞` 這個事件名，
   工具側**連字面都沒有**（判定 `absent`）。
4. **`amend --resources` 不跑資源互斥檢查** → 守衛覆蓋缺口。
   `commands/amend_cmd.py` import 了 `resources.render_block`（因此寫得動資源宣告），
   而它的呼叫圖**到不了** `resources.find_conflicts`。後果是先 assign 小射程、再 amend
   擴大即可繞過派工閘門建立的不變量。
5. **卡面「需求：」欄改不動** → `card_field/需求`，備註 `open 渲染=是；amend 可改=否；
   ⚠️ 開卡寫得進、開卡後改不動；⚠️ amend 讀它當判準卻改不動它`。錨點常數
   `card._REQUESTED_BY_RE` 存在，但只被讀取器 `parse_requested_by` 引用，沒有任何
   `amend_*` 函式碰它。而 `--core-pain` 的授權比對正是拿 `--ruling-url` 的 GitHub comment
   author 去比這一欄——**該欄為 `—` 的卡因此永遠無法 `amend --core-pain`，且無法補救**。

## 4. 本次新發現（先前未踩到）

驗收條 3 要求對帳結果須含先前未踩到的條目。以下全部是本次掃出來、不在那五個已知實例裡的。

### 4.1 交付狀態：狀態表列了選項，卻沒有**專責動詞**（5 項新增）

已知的只有 `⏸阻塞`。實際同形狀的還有 **`⏳待執行`、`💡需求`、`🔨執行中`、`🚨已升級`、
`📦已合併`**——六個都只出現在 `project.FIELD_SPECS` 的列舉裡，沒有任何命令以它為自己的
語意結果。

> ⚠️ **措辭更正（本卡自己犯的一次過度宣稱）。** 本節初稿寫的是「沒有任何動詞轉得進去」，
> 那是**錯的**。`assign_cmd.py` 的 `--status` 是自由文字旗標（只有 `default` 與 `help`，
> **沒有 `choices`**），而 `project.set_field_value` 只檢查該值是不是 Project 上既有的
> 選項。因此 `wfcli assign --status ⏸阻塞` **寫得進去**。正確的說法是「沒有**專責**動詞」。
> 對帳器現在把這類逃生口用 `ungated_status_flags` 機械列在報告開頭，不靠散文記得。

`--status` 自由文字本身就是一個新發現的治理缺口：**`assign` 可以把卡直接推到
`🚨已升級` 或 `📦已合併`，而不經過契約規定的任何前提**（escalation checkpoint、merge 收尾）。
契約把大量條件寫在 `review-escalation.md` §4，而寫入面完全不驗。

兩個特別要緊的狀態：

- **`🚨已升級`**：canonical §5 與 `review-escalation.md` §4 花了大量篇幅規定「何時轉
  `🚨已升級`」，卻**沒有任何命令以它為語意結果**。`checkpoint_cmd` 有 `escalate` 決定值
  （`CHECKPOINT_DECISIONS`），但它寫的是 checkpoint 留言，不改交付狀態——所以「該不該升級」
  的判斷與「卡真的變成已升級」之間沒有機械連線，中間靠人打 `assign --status`。
- **`📦已合併`**：canonical §4.4 明訂「現役的定義含 `📦已合併`」「停在 `📦已合併` 不收尾
  ＝假活卡」。工具**讀**它（`doctor.py:1269` 的比對）卻沒有專責寫入動詞。實務上這個狀態
  是怎麼被設定的（`assign --status`？看板 UI？），**工具帳上分不出來**；若是後者即違反
  §4.3「唯一寫入通道」紅線。**需求方裁定。**

### 4.2 卡面欄位：開卡寫得進、開卡後改不動（4 項新增）

已知的只有 `需求`。同形狀的還有 **`規劃`、`執行`、`查核`、`DB`、`服務的原始目標`**——
`render_issue_body`／`format_routing_line` 都渲染它們，`amend` 一個都改不動。

`規劃` 與 `需求` 一樣被 amend 讀作判準（`parse_requested_by`），因此同時掛著
「⚠️ amend 讀它當判準卻改不動它」——**開卡時打錯就永久錯**。

### 4.3 卡面欄位：契約宣告了，工具完全不渲染（19 項）

| 範本 | 欄位 |
|---|---|
| `tasks-card.md` | `部署`、`環境`、`PR`、`Merge SHA`、`範圍`、`Discovery`、`Design` |
| `initiative-card.md` | `目標`、`非目標`、`里程碑`、`依賴與子卡`、`基線變更紀錄`、`決策與風險` |
| `bug-card.md` | `重現`、`預期 vs 實際`、`環境`、`根因`、`修復`、`回歸測試` |

`wfcli open` 只渲染 `tasks-card.md` 的前半段欄位。**`initiative-card.md` 與 `bug-card.md`
的卡面在工具側整份不存在**——canonical §3 要求大型工作以 Initiative 父卡管理、bug 依
`bug-workflow.md` 處理，而那兩種卡沒有任何機械支援。

### 4.4 事件：契約要求、無 writer（6 項新增）

- **`escalation-epoch-change`**（canonical §4.1／§3：epoch 只能由需求方核可的此事件逐一
  推進）。`commands/checkpoint_cmd.py:264` 的訊息**自陳**「該 writer 尚未實作」——碼裡知道，
  契約與狀態面上看不到。
- **`handoff-accepted`**（canonical §4.1：receiver 驗證後才可追加此事件並取得所有權；
  §5 的 preflight `event-verified` 依據也綁在它上面）。`wfcli handoff` 只寫交接、不寫承接，
  於是 `review.py:PREFLIGHT_BASES` 的 `event-verified` 在本 repo **結構上不可達**——那個
  已被文件化的「不可達」，根因就是這一項沒有 writer。
- **`review-correction`**（`review-escalation.md` §2：finding 結構化狀態衝突須以此事件裁決；
  §4 的六格處置也引用它）。無 writer ⇒ 衝突無法閉合 ⇒ §2 的 fail loud 一旦觸發就無出口。
- **`review-marker-clearance`**（§1 第五層次「留痕解析停機」的唯一解除表示法）。
  `doctor.py:517` **偵測得到**停機，但沒有任何解除 writer。`review.py:1239` 自己寫著
  checkpoint 的機械推導「被 `review-marker-clearance` 的留痕解析停機（解除表示法未定義）
  擋住」。
- **`baseline-change-request`**（`baseline-cascade.md` §1 凍結步驟要求在卡 Log 與 lifecycle
  event 留此事件）。工具側完全不存在。
- **`forged-rejected`／`malformed-ignored`／`reissue-required`／`repaired-verified`**
  （`handoff-contract.md` §3.1.4 的四個 clearance 分類）。四個都 `absent`；它們是上一項
  `review-marker-clearance` 的取值，同族一起缺。

### 4.5 命名漂移：能力有，契約名進不了狀態面（2 項）

- **`escalation-checkpoint`**：`wfcli checkpoint` 動詞存在且會寫留言，但留言標題是
  `## Escalation checkpoint：<card>`、區塊鍵是 `CHECKPOINT_BLOCK_KEY`，**從不吐出契約那串
  kebab 字面**。所以符號層判定是 `mention-only`，而備註 `相關動詞=checkpoint` 標出它與
  `preflight-failed`（`相關動詞=無`）**不是同一種缺口**。
- **`contract-baseline`**：writer 存在（`checkpoint_cmd`），讀取端以 `BASELINE_BLOCK_KEY`
  ＋ `## Contract baseline：` 標題辨識，不比對該字面，因此判定 `write-only`。這是字面層的
  事實，能力層有讀者。

⚠️ 這兩項是本表**最容易被誤讀成大洞**的兩列。它們是命名不一致，不是功能缺席。

### 4.6 守衛覆蓋：另外兩個入口（1 真陽性 ＋ 1 待判）

| 寫入入口 | 資料模組 | 用到的 serializer | 未跑的守衛 | 評估 |
|---|---|---|---|---|
| `commands/amend_cmd.py` | `resources` | `render_block` | `find_conflicts` | 已知缺口 #4，真陽性 |
| `card.py` | `resources` | `render_block` | `find_conflicts` | **新發現**：`render_issue_body` 在開卡時就渲染資源宣告區塊，而 `open` 路徑不做任何互斥比對。派工閘門只擋 `assign`，開卡不擋 |
| `commands/assign_cmd.py` | `card` | `format_branch_worktree` | `validate_capability_routing` 等 | **候選，需人判**：配對是模組粒度，`card.py` 的 serializer 與 routing 驗證器被混在一起，很可能是偽陽性 |

## 5. 已知限制（對帳器本身的）

誠實列出，不假裝機械判定是全知的。

- **呼叫圖解析不到的呼叫不連邊。** 少一條邊只會讓工具少判一些「有實作」，方向是**多報
  缺口**。因此本表的缺口是**下界**不是上界——但同時代表少數 `absent`／`mention-only` 可能
  是解析不到造成的，逐項處置時仍須人讀一次碼。
- **`gh` 的寫入型子命令集合是本腳本唯一的外部種子**（`MUTATING_GH_SUBCOMMANDS`）。它是
  `gh` CLI 的通用語彙、不是本 repo 的清單，且擴充它只會讓更多東西被判成 writer。
- **writer 量的是「這個符號進不進得了狀態面」，不是「有沒有一個該型別的合格事件」。**
  §4.5 的兩項就是這個精度限制的直接後果。
- **短的通用中文標籤會跨脈絡碰撞。** `card_field` 的 `目標`／`需求方`／`範圍`／`Log` 四列，
  命中的多半不是 initiative 卡面上的那個欄位，而是碼裡別處同名的字串。§6 把它們標為過抽。
- **守衛覆蓋以模組為粒度配對** serializer 與 guard，同一模組裡不相干的兩者會被湊成一對
  （§4.6 第三列即是）。
- **第一版曾漏掃兩個欄位**：`spec 基線` 與 `Merge SHA` 含內部空白，而欄位名的字元類把 `\s`
  排掉了，兩者靜默不進表。已修（欄位名容許內含空白）。⚠️ 這正是驗收條 5 警告的那個失敗
  形狀，而它是在寫本檔、逐列核對「契約明列的必填欄怎麼不在表上」時才發現的——**機械窮舉
  不保證規則本身是對的**。
- **第一版的 ratchet 漏了守衛覆蓋缺口**：`--check` 只比對符號列，於是 M3 變異讓正控組 4
  整個消失時它仍是綠的。已修（§2.4）。同一個教訓的第二次：**規則與檢查本身都要被變異
  檢驗打一次，不能只驗被檢查的對象**。

## 6. 缺口登記與處置

`--check` 逐項比對這個區塊。**登記＝承認缺口，不是消除缺口**（理由見 §2.3）。

處置語彙：`補寫入者`｜`補讀取者`｜`已知限制`｜`從契約移除`｜`過抽`｜`待需求方裁定`。
以下按族給處置建議；**本卡不實作任何一項**。

| 族 | 成員 | 建議處置 |
|---|---|---|
| §3 五個已知實例 | `review-invalid`、`preflight-failed`、`status-change`、amend 繞過 `find_conflicts`、`需求` 欄 | `補寫入者`（`review-invalid` 工程量最小：偵測已在，只差留痕）。`amend` 那項是**閘門繞過**，風險高於留痕缺失，建議單獨開卡 |
| §4.1 狀態無專責動詞 | `⏸阻塞`、`⏳待執行`、`💡需求`、`🔨執行中`、`🚨已升級`、`📦已合併`，以及 `assign --status` 自由文字逃生口 | `🚨已升級` `補寫入者`；`📦已合併` `待需求方裁定`（先釐清現況是怎麼設定的）；其餘 `待需求方裁定`（補動詞或從狀態表移除）。**`--status` 該不該收斂成 `choices` 是獨立一問**——它現在讓所有前提都可繞過 |
| §4.1 規劃期兩個狀態（2026-08-18 新增） | `🔬研究中`、`🧭規劃中` | `已知限制`：**刻意無專責動詞**。兩者都在授權執行之前，由需求方以 `assign --status`／`handoff --status` 顯式寫入；規劃期的推進判準是人的判斷（Discovery 釐清完了沒、Design 收斂了沒），不是機器可導出的條件，補動詞只會造出一個「呼叫它就代表過關」的空洞閘門 |
| §4.2 開卡後改不動 | `規劃`、`執行`、`查核`、`DB`、`服務的原始目標` | `補寫入者`（`規劃` 優先：它與 `需求` 同樣被讀作授權判準） |
| §4.3 完全不渲染 | tasks-card 7 項＋initiative-card 6 項＋bug-card 6 項 | `待需求方裁定`：`從契約移除`（承認這些是手填欄位）或補 `wfcli open --kind initiative/bug`。**不建議逐欄補**——19 個欄位逐欄開卡正是本卡要消滅的「修實例不修形狀」 |
| §4.4 事件無 writer | `escalation-epoch-change`、`handoff-accepted`、`review-correction`、`review-marker-clearance`、`baseline-change-request`、四個 clearance 分類 | `補寫入者`。`handoff-accepted` 優先——`event-verified` preflight 依據的不可達性以它為根因 |
| §4.5 命名漂移 | `escalation-checkpoint`、`contract-baseline` | `已知限制`（或統一契約名與碼內錨點名，屬低風險整理） |
| §4.6 守衛覆蓋 | `card.py` → `find_conflicts` | `待需求方裁定`：開卡時是否應做互斥比對（現況只有 assign 擋） |
| 過抽（非契約符號） | `cpbl-analytics`（採用專案的 repo 名，寫在範本的警示句裡）、`ubuntu-latest`、`update-branch`、`🔴紅線`、`⚪一般`、`→merge`、`→查核前`、`↔執行者`、`card_field` 的 `Log`／`目標`／`需求方`／`範圍` | `過抽`：抽取規則的已知代價，不須處置 |
| 列舉值非事件 | `data-migration`、`authoritative-artifact`、`change-executor` | `過抽`：皆有讀取者，判定為 `read-only` 屬正常 |
| 刻意 fail-closed | `spec-narrowed`、`instruction-omitted` | `已知限制`：`checkpoint_cmd` 明寫「保留旗標，一律拒收」，兩個 defer cause 在本 repo 皆不可用 |

<!-- reconcile-dispositions:begin -->
```json
{
  "gaps": {
    "card_field/Design": "mention-only",
    "card_field/Discovery": "mention-only",
    "card_field/Log": "write-only",
    "card_field/Merge SHA": "absent",
    "card_field/PR": "mention-only",
    "card_field/依賴與子卡": "absent",
    "card_field/修復": "mention-only",
    "card_field/回歸測試": "absent",
    "card_field/基線變更紀錄": "absent",
    "card_field/根因": "mention-only",
    "card_field/決策與風險": "absent",
    "card_field/環境": "mention-only",
    "card_field/目標": "write-only",
    "card_field/範圍": "read-only",
    "card_field/部署": "mention-only",
    "card_field/里程碑": "absent",
    "card_field/重現": "mention-only",
    "card_field/需求方": "write-only",
    "card_field/非目標": "absent",
    "card_field/預期 vs 實際": "absent",
    "delivery_status/→merge": "absent",
    "delivery_status/→查核前": "absent",
    "delivery_status/↔執行者": "absent",
    "delivery_status/⏳待執行": "read-only",
    "delivery_status/⏸阻塞": "read-only",
    "delivery_status/⚪一般": "absent",
    "delivery_status/📦已合併": "read-only",
    "delivery_status/🔨執行中": "read-only",
    "delivery_status/🔴紅線": "absent",
    "delivery_status/🚨已升級": "read-only",
    "event/authoritative-artifact": "read-only",
    "event/baseline-change-request": "absent",
    "event/change-executor": "read-only",
    "event/contract-baseline": "write-only",
    "event/data-migration": "read-only",
    "event/escalation-checkpoint": "mention-only",
    "event/escalation-epoch-change": "mention-only",
    "event/forged-rejected": "absent",
    "event/handoff-accepted": "mention-only",
    "event/instruction-omitted": "mention-only",
    "event/malformed-ignored": "absent",
    "event/preflight-failed": "mention-only",
    "event/reissue-required": "absent",
    "event/repaired-verified": "absent",
    "event/review-correction": "mention-only",
    "event/review-invalid": "mention-only",
    "event/review-marker-clearance": "mention-only",
    "event/spec-narrowed": "mention-only",
    "event/status-change": "absent",
    "event/cpbl-analytics": "mention-only",
    "event/ubuntu-latest": "absent",
    "event/update-branch": "absent",
    "guard/cli/src/wf_cli/card.py→resources": "find_conflicts",
    "guard/cli/src/wf_cli/commands/amend_cmd.py→resources": "find_conflicts",
    "guard/cli/src/wf_cli/commands/assign_cmd.py→card": "validate_capability_routing／validate_routing_field／validate_routing_names"
  }
}
```
<!-- reconcile-dispositions:end -->

## 7. 對帳表（快照）

⚠️ 以下是機械輸出的快照，**不要手改**；要改的是碼或契約文件，然後重跑
`python3 scripts/contract_tool_reconcile.py`。機器守住的是 §6 的缺口集合，不是本節的排版。

- 契約側符號總數：**79**（由掃描文件導出，非人工登記）
- 判定為缺口：**52**
- 守衛覆蓋缺口：**3**
- ⚠️ 自由文字狀態旗標（可繞過所有契約前提直接設定任一已宣告狀態）：`assign_cmd.py --status（預設 🚧進行中，無 choices）`

### 事件型別（22）

| 符號 | 判定 | 契約出處 | 寫入者 | 讀取者 | 備註 |
|---|---|---|---|---|---|
| `authoritative-artifact` | read-only | `templates/review-escalation.md:39`<br>`templates/review-escalation.md:54`<br>`templates/review-escalation.md:176` | — | `cli/src/wf_cli/review.py:40`<br>`cli/src/wf_cli/review.py:590` | 相關動詞=無 |
| `baseline-change-request` | absent | `templates/baseline-cascade.md:12` | — | — | 相關動詞=無 |
| `change-executor` | read-only | `templates/review-escalation.md:67` | — | `cli/src/wf_cli/review.py:586` | 相關動詞=無 |
| `contract-baseline` | write-only | `templates/review-escalation.md:97`<br>`templates/review-escalation.md:274`<br>`templates/review-escalation.md:276` | `cli/src/wf_cli/commands/checkpoint_cmd.py:281` | — | 相關動詞=無 |
| `data-migration` | read-only | `AI_WORKFLOW.md:122`<br>`AI_WORKFLOW.md:154` | — | `cli/src/wf_cli/commands/open_cmd.py:81`<br>`cli/src/wf_cli/resources.py:39` | 相關動詞=無 |
| `escalation-checkpoint` | mention-only | `templates/review-escalation.md:46`<br>`templates/review-escalation.md:61`<br>`templates/review-escalation.md:149`<br>…共 5 | — | — | 相關動詞=checkpoint |
| `escalation-epoch-change` | mention-only | `AI_WORKFLOW.md:141`<br>`templates/review-escalation.md:157`<br>`templates/review-escalation.md:159`<br>…共 4 | — | — | 相關動詞=無 |
| `forged-rejected` | absent | `templates/handoff-contract.md:129`<br>`templates/handoff-contract.md:233`<br>`templates/review-escalation.md:115`<br>…共 8 | — | — | 相關動詞=無 |
| `handoff-accepted` | mention-only | `AI_WORKFLOW.md:142`<br>`templates/control-plane-contract.md:58`<br>`templates/handoff-contract.md:9`<br>…共 6 | — | — | 相關動詞=handoff |
| `instruction-omitted` | mention-only | `templates/review-escalation.md:104`<br>`templates/review-escalation.md:108`<br>`templates/review-escalation.md:117`<br>…共 9 | — | — | 相關動詞=無 |
| `malformed-ignored` | absent | `templates/handoff-contract.md:130`<br>`templates/handoff-contract.md:233`<br>`templates/review-escalation.md:236`<br>…共 6 | — | — | 相關動詞=無 |
| `preflight-failed` | mention-only | `AI_WORKFLOW.md:103`<br>`templates/review-escalation.md:9`<br>`templates/review-escalation.md:15`<br>…共 4 | — | — | 相關動詞=無 |
| `reissue-required` | absent | `templates/handoff-contract.md:129`<br>`templates/handoff-contract.md:132`<br>`templates/review-escalation.md:244`<br>…共 7 | — | — | 相關動詞=無 |
| `repaired-verified` | absent | `templates/handoff-contract.md:127`<br>`templates/handoff-contract.md:130`<br>`templates/handoff-contract.md:131`<br>…共 6 | — | — | 相關動詞=無 |
| `review-correction` | mention-only | `AI_WORKFLOW.md:104`<br>`AI_WORKFLOW.md:141`<br>`templates/review-escalation.md:44`<br>…共 10 | — | — | 相關動詞=review |
| `review-invalid` | mention-only | `AI_WORKFLOW.md:103`<br>`AI_WORKFLOW.md:202`<br>`templates/review-escalation.md:11`<br>…共 8 | — | — | 相關動詞=review |
| `review-marker-clearance` | mention-only | `templates/handoff-contract.md:125`<br>`templates/review-escalation.md:13`<br>`templates/review-escalation.md:19`<br>…共 5 | — | — | 相關動詞=review |
| `spec-narrowed` | mention-only | `templates/review-escalation.md:103`<br>`templates/review-escalation.md:117`<br>`templates/review-escalation.md:118`<br>…共 9 | — | — | 相關動詞=無 |
| `status-change` | absent | `templates/review-escalation.md:10`<br>`templates/review-escalation.md:15` | — | — | 相關動詞=無 |
| `ubuntu-latest` | absent | `docs/ROADMAP.md:152` | — | — | 相關動詞=無 |
| `update-branch` | absent | `docs/ROADMAP.md:135` | — | — | 相關動詞=無 |
| `structurally-vacuous` | ok | `docs/ROADMAP.md:33`<br>`docs/ROADMAP.md:59`<br>`docs/ROADMAP.md:293` | `cli/src/wf_cli/validation.py:480`<br>`cli/src/wf_cli/validation.py:483`<br>`cli/src/wf_cli/validation.py:486` | `cli/src/wf_cli/review.py:618` | 相關動詞=無 |

### 交付狀態（23）

| 符號 | 判定 | 契約出處 | 寫入者 | 讀取者 | 備註 |
|---|---|---|---|---|---|
| `→merge` | absent | `AI_WORKFLOW.md:56` | — | — | Project 選項=否；專責動詞=否 |
| `→查核前` | absent | `AI_WORKFLOW.md:56` | — | — | Project 選項=否；專責動詞=否 |
| `↔執行者` | absent | `AI_WORKFLOW.md:49` | — | — | Project 選項=否；專責動詞=否 |
| `⏳待執行` | read-only | `AI_WORKFLOW.md:18`<br>`templates/TASKS.md:6` | — | `cli/src/wf_cli/project.py:39` | Project 選項=是；專責動詞=否；⚠️ 沒有專責動詞；只有自由文字旗標寫得進去（見報告的「自由文字狀態旗標」） |
| `⏸阻塞` | read-only | `AI_WORKFLOW.md:18`<br>`AI_WORKFLOW.md:103`<br>`AI_WORKFLOW.md:191`<br>…共 11 | — | `cli/src/wf_cli/project.py:41` | Project 選項=是；專責動詞=否；⚠️ 沒有專責動詞；只有自由文字旗標寫得進去（見報告的「自由文字狀態旗標」） |
| `⚪一般` | absent | `templates/bug-card.md:1`<br>`templates/tasks-card.md:1` | — | — | Project 選項=否；專責動詞=否 |
| `💡需求` | read-only | `AI_WORKFLOW.md:18`<br>`templates/TASKS.md:6` | — | `cli/src/wf_cli/project.py:39` | Project 選項=是；專責動詞=否；⚠️ 沒有專責動詞；只有自由文字旗標寫得進去（見報告的「自由文字狀態旗標」） |
| `📦已合併` | read-only | `AI_WORKFLOW.md:18`<br>`AI_WORKFLOW.md:171`<br>`templates/TASKS.md:6`<br>…共 7 | — | `cli/src/wf_cli/doctor.py:1269`<br>`cli/src/wf_cli/project.py:40` | Project 選項=是；專責動詞=否；⚠️ 沒有專責動詞；只有自由文字旗標寫得進去（見報告的「自由文字狀態旗標」） |
| `🔨執行中` | read-only | `AI_WORKFLOW.md:18`<br>`templates/TASKS.md:6`<br>`templates/review-escalation.md:9`<br>…共 4 | — | `cli/src/wf_cli/project.py:39` | Project 選項=是；專責動詞=否；⚠️ 沒有專責動詞；只有自由文字旗標寫得進去（見報告的「自由文字狀態旗標」） |
| `🔴紅線` | absent | `templates/bug-card.md:1`<br>`templates/tasks-card.md:1` | — | — | Project 選項=否；專責動詞=否 |
| `🚨已升級` | read-only | `AI_WORKFLOW.md:18`<br>`AI_WORKFLOW.md:104`<br>`AI_WORKFLOW.md:191`<br>…共 9 | — | `cli/src/wf_cli/project.py:41` | Project 選項=是；專責動詞=否；⚠️ 沒有專責動詞；只有自由文字旗標寫得進去（見報告的「自由文字狀態旗標」） |
| `↩退回` | ok | `AI_WORKFLOW.md:18`<br>`templates/TASKS.md:6`<br>`templates/review-escalation.md:12` | `cli/src/wf_cli/review.py:64` | `cli/src/wf_cli/project.py:41`<br>`cli/src/wf_cli/review.py:64` | Project 選項=是；專責動詞=是 |
| `⏳部署中` | ok | `AI_WORKFLOW.md:18` | `cli/src/wf_cli/commands/deploy_state_cmd.py:28`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:29`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:39` | `cli/src/wf_cli/commands/deploy_state_cmd.py:28`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:29`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:39`<br>…共 4 | Project 選項=是；專責動詞=是 |
| `⏸未部署` | ok | `AI_WORKFLOW.md:18` | `cli/src/wf_cli/commands/deploy_declare_cmd.py:27`<br>`cli/src/wf_cli/commands/deploy_declare_cmd.py:35`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:27`<br>…共 5 | `cli/src/wf_cli/commands/deploy_state_cmd.py:27`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:37`<br>`cli/src/wf_cli/project.py:46` | Project 選項=是；專責動詞=是 |
| `✅已部署` | ok | `AI_WORKFLOW.md:18` | `cli/src/wf_cli/commands/deploy_state_cmd.py:29`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:30`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:40` | `cli/src/wf_cli/commands/deploy_state_cmd.py:29`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:30`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:40`<br>…共 4 | Project 選項=是；專責動詞=是 |
| `✅已驗證` | ok | `AI_WORKFLOW.md:18`<br>`templates/worktree-lifecycle.md:15` | `cli/src/wf_cli/commands/deploy_state_cmd.py:31`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:42`<br>`cli/src/wf_cli/commands/handoff_cmd.py:349` | `cli/src/wf_cli/commands/deploy_state_cmd.py:31`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:42`<br>`cli/src/wf_cli/commands/handoff_cmd.py:349`<br>…共 4 | Project 選項=是；專責動詞=是 |
| `✅通過` | ok | `AI_WORKFLOW.md:18`<br>`templates/TASKS.md:6`<br>`templates/review-escalation.md:12` | `cli/src/wf_cli/review.py:64` | `cli/src/wf_cli/project.py:40`<br>`cli/src/wf_cli/review.py:64` | Project 選項=是；專責動詞=是 |
| `🏁完成` | ok | `AI_WORKFLOW.md:18`<br>`templates/TASKS.md:6`<br>`templates/project-stub.md:25`<br>…共 5 | `cli/src/wf_cli/commands/assign_cmd.py:89`<br>`cli/src/wf_cli/commands/handoff_cmd.py:356` | `cli/src/wf_cli/commands/assign_cmd.py:89`<br>`cli/src/wf_cli/project.py:40` | Project 選項=是；專責動詞=是 |
| `📥Backlog` | ok | `AI_WORKFLOW.md:18`<br>`AI_WORKFLOW.md:113`<br>`templates/TASKS.md:6` | `cli/src/wf_cli/card.py:295` | `cli/src/wf_cli/project.py:39` | Project 選項=是；專責動詞=是 |
| `🔍待查核` | ok | `AI_WORKFLOW.md:18`<br>`templates/TASKS.md:6`<br>`templates/handoff-contract.md:154`<br>…共 6 | `cli/src/wf_cli/commands/handoff_cmd.py:89`<br>`cli/src/wf_cli/commands/review_cmd.py:104` | `cli/src/wf_cli/commands/handoff_cmd.py:89`<br>`cli/src/wf_cli/project.py:40` | Project 選項=是；專責動詞=是 |
| `🚀待部署` | ok | `AI_WORKFLOW.md:18` | `cli/src/wf_cli/commands/deploy_state_cmd.py:27`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:28`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:38` | `cli/src/wf_cli/commands/deploy_state_cmd.py:27`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:28`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:38`<br>…共 4 | Project 選項=是；專責動詞=是 |
| `🛑已停止` | ok | `AI_WORKFLOW.md:18`<br>`templates/TASKS.md:6`<br>`templates/baseline-cascade.md:20` | `cli/src/wf_cli/commands/assign_cmd.py:89` | `cli/src/wf_cli/commands/assign_cmd.py:89`<br>`cli/src/wf_cli/project.py:41` | Project 選項=是；專責動詞=是 |
| `🧪驗證中` | ok | `AI_WORKFLOW.md:18` | `cli/src/wf_cli/commands/deploy_state_cmd.py:30`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:31`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:41` | `cli/src/wf_cli/commands/deploy_state_cmd.py:30`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:31`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:41`<br>…共 4 | Project 選項=是；專責動詞=是 |

### 卡面欄位（34）

| 符號 | 判定 | 契約出處 | 寫入者 | 讀取者 | 備註 |
|---|---|---|---|---|---|
| `Design` | absent | `templates/initiative-card.md:4`<br>`templates/tasks-card.md:11` | — | — | open 渲染=否；amend 可改=否 |
| `Discovery` | absent | `templates/initiative-card.md:4`<br>`templates/tasks-card.md:10` | — | — | open 渲染=否；amend 可改=否 |
| `Log` | write-only | `templates/bug-card.md:11`<br>`templates/tasks-card.md:38` | `cli/src/wf_cli/card.py:428` | — | open 渲染=是；amend 可改=否；⚠️ 開卡寫得進、開卡後改不動；⚠️ amend 讀它當判準卻改不動它 |
| `Merge SHA` | absent | `templates/tasks-card.md:8` | — | — | open 渲染=否；amend 可改=否 |
| `PR` | mention-only | `templates/tasks-card.md:8` | — | — | open 渲染=否；amend 可改=否 |
| `依賴與子卡` | absent | `templates/initiative-card.md:8` | — | — | open 渲染=否；amend 可改=否 |
| `修復` | mention-only | `templates/bug-card.md:6` | — | — | open 渲染=否；amend 可改=否 |
| `回歸測試` | absent | `templates/bug-card.md:6` | — | — | open 渲染=否；amend 可改=否 |
| `基線變更紀錄` | absent | `templates/initiative-card.md:18` | — | — | open 渲染=否；amend 可改=否 |
| `根因` | mention-only | `templates/bug-card.md:5` | — | — | open 渲染=否；amend 可改=否 |
| `決策與風險` | absent | `templates/initiative-card.md:22` | — | — | open 渲染=否；amend 可改=否 |
| `環境` | mention-only | `templates/bug-card.md:3`<br>`templates/tasks-card.md:8` | — | — | open 渲染=否；amend 可改=否 |
| `目標` | write-only | `templates/initiative-card.md:5` | `cli/src/wf_cli/cleanup.py:801`<br>`cli/src/wf_cli/cleanup.py:826`<br>`cli/src/wf_cli/registry.py:856`<br>…共 4 | — | open 渲染=否；amend 可改=否 |
| `範圍` | read-only | `templates/tasks-card.md:9` | — | `cli/src/wf_cli/doctor.py:770` | open 渲染=否；amend 可改=否 |
| `部署` | mention-only | `templates/tasks-card.md:8` | — | — | open 渲染=否；amend 可改=否 |
| `里程碑` | absent | `templates/initiative-card.md:6` | — | — | open 渲染=否；amend 可改=否 |
| `重現` | mention-only | `templates/bug-card.md:3` | — | — | open 渲染=否；amend 可改=否 |
| `需求方` | write-only | `templates/initiative-card.md:3` | `cli/src/wf_cli/validation.py:324`<br>`cli/src/wf_cli/validation.py:331` | — | open 渲染=否；amend 可改=否 |
| `非目標` | absent | `templates/initiative-card.md:5` | — | — | open 渲染=否；amend 可改=否 |
| `預期 vs 實際` | absent | `templates/bug-card.md:4` | — | — | open 渲染=否；amend 可改=否 |
| `DB` | ok | `templates/tasks-card.md:6` | `cli/src/wf_cli/card.py:385`<br>`cli/src/wf_cli/card.py:412` | `cli/src/wf_cli/card.py:902` | open 渲染=是；amend 可改=否；⚠️ 開卡寫得進、開卡後改不動 |
| `Initiative` | ok | `templates/bug-card.md:8`<br>`templates/tasks-card.md:5` | `cli/src/wf_cli/card.py:384`<br>`cli/src/wf_cli/card.py:411`<br>`cli/src/wf_cli/card.py:578`<br>…共 6 | `cli/src/wf_cli/card.py:470`<br>`cli/src/wf_cli/card.py:901`<br>`cli/src/wf_cli/commands/amend_cmd.py:738`<br>…共 9 | open 渲染=是；amend 可改=是 |
| `owner` | ok | `templates/initiative-card.md:3` | `cli/src/wf_cli/card.py:387`<br>`cli/src/wf_cli/card.py:432`<br>`cli/src/wf_cli/cleanup.py:863`<br>…共 11 | `cli/src/wf_cli/commands/amend_cmd.py:538`<br>`cli/src/wf_cli/commands/assign_cmd.py:253`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py:44`<br>…共 15 | open 渲染=否；amend 可改=否 |
| `spec 基線` | ok | `templates/initiative-card.md:4`<br>`templates/tasks-card.md:5` | `cli/src/wf_cli/card.py:385`<br>`cli/src/wf_cli/card.py:412`<br>`cli/src/wf_cli/card.py:578`<br>…共 6 | `cli/src/wf_cli/card.py:470`<br>`cli/src/wf_cli/commands/amend_cmd.py:735` | open 渲染=是；amend 可改=是 |
| `分支` | ok | `templates/bug-card.md:7` | `cli/src/wf_cli/commands/assign_cmd.py:258` | `cli/src/wf_cli/commands/assign_cmd.py:254`<br>`cli/src/wf_cli/commands/open_cmd.py:228`<br>`cli/src/wf_cli/project.py:34`<br>…共 7 | open 渲染=否；amend 可改=否 |
| `執行` | ok | `templates/bug-card.md:7`<br>`templates/tasks-card.md:4` | `cli/src/wf_cli/card.py:369` | `cli/src/wf_cli/card.py:214`<br>`cli/src/wf_cli/card.py:830`<br>`cli/src/wf_cli/card.py:844`<br>…共 4 | open 渲染=是；amend 可改=否；⚠️ 開卡寫得進、開卡後改不動 |
| `服務的原始目標` | ok | `templates/tasks-card.md:7` | `cli/src/wf_cli/card.py:386`<br>`cli/src/wf_cli/card.py:413` | `cli/src/wf_cli/card.py:903`<br>`cli/src/wf_cli/commands/open_cmd.py:233`<br>`cli/src/wf_cli/project.py:49`<br>…共 6 | open 渲染=是；amend 可改=否；⚠️ 開卡寫得進、開卡後改不動 |
| `查核` | ok | `templates/bug-card.md:7`<br>`templates/tasks-card.md:4` | `cli/src/wf_cli/card.py:371` | `cli/src/wf_cli/card.py:215`<br>`cli/src/wf_cli/card.py:831`<br>`cli/src/wf_cli/card.py:845` | open 渲染=是；amend 可改=否；⚠️ 開卡寫得進、開卡後改不動 |
| `核心痛點` | ok | `templates/tasks-card.md:16` | `cli/src/wf_cli/card.py:389`<br>`cli/src/wf_cli/card.py:414`<br>`cli/src/wf_cli/resources.py:192` | `cli/src/wf_cli/commands/amend_cmd.py:742` | open 渲染=是；amend 可改=是 |
| `規劃` | ok | `templates/tasks-card.md:3` | `cli/src/wf_cli/card.py:383`<br>`cli/src/wf_cli/card.py:410`<br>`cli/src/wf_cli/card.py:703` | `cli/src/wf_cli/card.py:473` | open 渲染=是；amend 可改=否；⚠️ 開卡寫得進、開卡後改不動；⚠️ amend 讀它當判準卻改不動它 |
| `資源宣告` | ok | `templates/tasks-card.md:20` | `cli/src/wf_cli/commands/amend_cmd.py:763`<br>`cli/src/wf_cli/resources.py:213`<br>`cli/src/wf_cli/resources.py:215` | `cli/src/wf_cli/commands/amend_cmd.py:767`<br>`cli/src/wf_cli/commands/amend_cmd.py:768`<br>`cli/src/wf_cli/commands/amend_cmd.py:774`<br>…共 9 | open 渲染=是；amend 可改=是 |
| `需求` | ok | `templates/bug-card.md:7`<br>`templates/tasks-card.md:3` | `cli/src/wf_cli/card.py:381`<br>`cli/src/wf_cli/card.py:410`<br>`cli/src/wf_cli/card.py:703`<br>…共 5 | `cli/src/wf_cli/card.py:473`<br>`cli/src/wf_cli/card.py:900`<br>`cli/src/wf_cli/project.py:39` | open 渲染=是；amend 可改=否；⚠️ 開卡寫得進、開卡後改不動；⚠️ amend 讀它當判準卻改不動它 |
| `驗收條件` | ok | `templates/tasks-card.md:30` | `cli/src/wf_cli/card.py:393`<br>`cli/src/wf_cli/card.py:420`<br>`cli/src/wf_cli/resources.py:192` | `cli/src/wf_cli/commands/amend_cmd.py:747` | open 渲染=是；amend 可改=是 |
| `驗證` | ok | `templates/tasks-card.md:34` | `cli/src/wf_cli/card.py:397`<br>`cli/src/wf_cli/card.py:424` | `cli/src/wf_cli/commands/amend_cmd.py:752` | open 渲染=是；amend 可改=是 |

### 守衛覆蓋缺口（3）

| 寫入入口 | 資料模組 | 用到的 serializer | 未跑的守衛 |
|---|---|---|---|
| `cli/src/wf_cli/card.py` | `resources` | `render_block` | `find_conflicts` |
| `cli/src/wf_cli/commands/amend_cmd.py` | `resources` | `render_block` | `find_conflicts` |
| `cli/src/wf_cli/commands/assign_cmd.py` | `card` | `format_branch_worktree` | `validate_capability_routing／validate_routing_field／validate_routing_names` |

