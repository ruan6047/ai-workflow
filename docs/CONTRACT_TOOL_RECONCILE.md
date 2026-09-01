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
   `project.FIELD_SPECS` 的列舉裡；`amend_cmd._escalate_layout_failure` 的 docstring
   （逐字「轉 ⏸阻塞 是 lifecycle 決定」）與 `review_cmd.run` 的註解都只是提及。契約 §1 另有 `status-change → ⏸阻塞` 這個事件名，
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

#### 4.1.1 `📥Backlog` 的專責動詞（`WF-BACKLOG-STAGE1`，2026-08-21）

`📥Backlog` 在本節初版**沒有**被列進「無專責動詞」那一族，因為當時它判 `ok`。但那個
`ok` 是**意外**：唯二的 writer 是 `wfcli open` 的 dataclass 預設（`card.py` 當時的
`delivery_status` 預設字面；⚠️ 該字面已於 `#118` 之後消失，見下方引用區塊）與
`doctor.py` 的鏡射常數，**沒有任何動詞以「進待辦池」為自己的語意結果**。
`ai-workflow#118` 把 open 預設改成 `💡需求`（正確——規劃閘門在開卡之後才跑）時，這一格
當場翻成 `read-only`，該卡的 R1 因此判 `R1-002`（major／blocking）：
**「`assign --status`／`handoff --status` 都是自由文字逃生口，不能取代具名、受前提檢查的
狀態轉換。」**

處置：`handoff --next-stage backlog`（`commands/handoff_cmd.py` 的 `STAGE_STATUS`）。
**它帶前提檢查**——**T2 以上**的卡，當下的交付狀態必須是 `🧭規劃中`，不符即拒絕並回退出碼
4，形狀與 `release` 讀部署狀態相同；**T0／T1 直通、不做檢查**。

⚠️ **規則本體在 canonical `AI_WORKFLOW.md` §3.1**（「進 `📥Backlog` 的狀態前提依級別分流」），
本工具只是它的執行者。這一點是 R1 退回後補的：初版把依據掛在 §0 的狀態序列上，而 §0 只說
順序、沒說前提，等於**工具執行了 canonical 沒說的規則**——那正是本卡要治的病。級別分流由
需求方 2026-08-21 就 `WF-BACKLOG-STAGE1-R1-001` 裁定（T2 以上課前提／T0／T1 直通／級別讀不
到照 T2 以上處理）。

⚠️ **這個檢查有多強，逐條寫明**（免得下一個讀表的人把它讀成比實際強）：

- 它證明的是「狀態面說這張卡來自規劃階段」，**不是「規劃真的做過」**——`🧭規劃中`
  本身也寫得進自由文字旗標。門檻由「沒有」升到「至少得先移動到規劃」，不是升到不可偽造。
- **T0／T1 這條路上一個檢查都沒有。** 那不是漏做，是 §3.1 的表沒有這兩級的列；但也因此，
  「這個動詞成功了」對 T0／T1 不蘊含任何規劃事實。
- 它**管不住級別本身**：級別是 `amend --tier` 可改的欄位，改成 T1 就繞開了這道閘門。
- canonical §3.1 T3 列的「需求方批註放行後才進 `📥Backlog`」**仍然無執行者**。本 repo 全部
  角色共用同一個 GitHub 帳號，`docs/ROADMAP.md` §1 明文禁止把這種恆真條文寫成看似在檢查的
  欄位，故**刻意不實作**。
- `--status` 仍然繞得過（給了它整條前提鏈都不跑），與 `release` 同形。**`--status` 該不該
  收斂成 `choices` 是本節上方已登記的獨立一問**，該卡未處理。

> 本節不改處置 JSON：`📥Backlog` 在本 repo 現行 `origin/main`（`b2a6d54`）上判 `ok`、
> 本來就不是缺口，登記表裡沒有它。這一格的意義在 #118 合併後才會顯現——屆時
> `card.py` 那個預設 writer 消失，而 `handoff_cmd.py` 的這一格讓它**不會**掉回 `read-only`。
>
> **上述預測已兌現、且已實測**（`WF-OPEN-INITIAL-STATUS1` R2，2026-08-22）。`open` 的
> 預設改成 `💡需求` 之後，`card.py` 與 `doctor.py` 的兩處字面確實消失，而本節下方的產生
> 輸出表顯示 `📥Backlog` **仍判 `ok`**、writer 由 `handoff_cmd.py` 承接——所以它沒有進
> §4.1 那一族，處置 JSON 也不需要新增它。⚠️ 這裡記一筆反向的事：該卡 R1 是在本節寫成
> **之前**的基線上做的，當時把 `delivery_status/📥Backlog` 登記成 `read-only`；對齊新
> `origin/main` 後 `--check` 以「登記了已不存在的缺口」轉紅，該列已於 R2 移除。**乾淨的
> 文字合併沒有攔下這個語意衝突，攔下它的是 `--check` 的第 2 個方向**——這正是 §2.3 說
> 「不能靠刪一列讓檢查變綠」的那條 ratchet 在反方向上也有效的實例。

### 4.2 卡面欄位：開卡寫得進、開卡後改不動（4 項新增）

已知的只有 `需求`。同形狀的還有 **`規劃`、`執行`、`查核`、`DB`、`服務的原始目標`**——
`render_issue_body`／`format_routing_line` 都渲染它們，`amend` 一個都改不動。

`規劃` 與 `需求` 一樣被 amend 讀作判準（`parse_requested_by`），因此同時掛著
「⚠️ amend 讀它當判準卻改不動它」——**開卡時打錯就永久錯**。

### 4.3 卡面欄位：契約宣告了，工具完全不渲染（19 項）

> ⚠️ **本節記的是 `WF-REDESIGN-W2B` 之前的狀態，保留作為歷史。** 該卡把下表三份範本整份
> 移除（對照與 falsifier 見 [`../templates/template-migration-map.md`](../templates/template-migration-map.md)），
> ⇒ 下列 19 個欄位連同其餘 `card_field` 符號**整類離開契約 universe**，本節所述的缺口
> 因此不再出現在對帳表上。
>
> ⛔ **不得把「不在表上了」讀成「已修復」。** 兩者的差別是可觀察的：修復會讓判定從
> `absent` 翻成 `ok`（符號還在、多了 writer）；離開 universe 是符號本身消失（表上查無此列）。
> 本次是後者——工具側的渲染能力**一行都沒有增加**。
>
> ⭐ **這是對帳器的盲區，⛔ 不是「卡面欄位契約消失了」。**（本段 `WF-REDESIGN-W2B` 交付後自我更正；
> 首版寫成「本 repo 沒有任何卡面欄位契約」，那是錯的。）契約仍在，只是搬到了本對帳器**看不到**的地方：
> `cli/src/wf_cli/card_face.py` 的 `card-face-form:v1` 已實作並在跑，卡面 body 逐張帶
> `resource-claims`／`card-face-form:v1`／`card-brief`／`wf-routing:v1` 四個標記。
> 而 `CARD_TEMPLATE_GLOB` 只看 `templates/*card*.md` ⇒ 該 glob 今天匹配零個檔，於是
> `card_field` 整類從表上消失。
>
> ⇒ **可觀察的後果**：本對帳器現在對「卡面欄位」這一軸**沒有覆蓋**，而它**不會因此轉紅**
> ——`--check` 只比對「缺口有沒有登記」，一個不存在的 kind 沒有缺口可登記。這正是
> `cli/tests/test_contract_tool_reconcile.py` 那條 ratchet 存在的理由：任何 `*card*.md`
> 回歸即轉紅，逼下一張卡重建正控組。⛔ 不得把 ratchet 綠燈讀成「覆蓋還在」。
> `WF-REDESIGN-W3` 的 AC2 逐字是「只擴充／消費 W1 的 v1 schema」——要恢復覆蓋，
> 該做的是把 universe 的來源從範本 glob 改到那份 schema，而**那屬對帳器本身的變更**（`scripts/`），
> ⛔ 不在 `WF-REDESIGN-W2B` 的寫入集內。

<!-- w2b-historical:begin -->
| 範本（`WF-REDESIGN-W2B` 已移除） | 欄位 |
|---|---|
| `tasks-card.md` | `部署`、`環境`、`PR`、`Merge SHA`、`範圍`、`Discovery`、`Design` |
| `initiative-card.md` | `目標`、`非目標`、`里程碑`、`依賴與子卡`、`基線變更紀錄`、`決策與風險` |
| `bug-card.md` | `重現`、`預期 vs 實際`、`環境`、`根因`、`修復`、`回歸測試` |

當時的判定是：`wfcli open` 只渲染 `tasks-card.md` 的前半段欄位；**`initiative-card.md` 與
`bug-card.md` 的卡面在工具側整份不存在**——canonical §3 要求大型工作以 Initiative 父卡
管理、bug 依 `bug-workflow.md` 處理，而那兩種卡沒有任何機械支援。⇒ `WF-REDESIGN-W2B`
的處置是**移除那三份範本**（父卡模型移入 `stage-rules/`、缺陷改走待審清單＋一般卡），
⛔ 不是補 19 個欄位的 writer——「19 個欄位逐欄開卡」正是本卡一開始要消滅的「修實例不修形狀」。
<!-- w2b-historical:end -->

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

### 4.7 後續卡新增的契約符號（`WF-ESCALATION-RESOLUTION-GAP1`，4 項）

⚠️ **這四項不屬於 2026-08-16 那次盤點。** 本對帳器由 `#97`（`6561e04`）帶入 main 的時點
**晚於** `WF-ESCALATION-RESOLUTION-GAP1` 分支的最後一輪查核（2026-08-12），所以該卡在
`templates/review-escalation.md` §4／§5 引入的契約符號，**三輪跨家族查核都不可能看見**——
直到 `#116` 讓 CI 第一次在**合併結果**（`refs/pull/N/merge`）上跑，`--check` 才在合併**前**
把它們撞出來。這正是 §2.3 那三個方向要買的東西：契約長出新符號而無人處置時的可見失敗。

- **`escalation-resolution`**（`review-escalation.md` §4「`escalate` 之後的第三種結果」與
  §5 的 schema 定義的新事件型別）→ `mention-only`，**writer 0**。四處字面全是提及：
  `cli/src/wf_cli/validation.py:771`（docstring）、`:827`（拒收訊息常數）、
  `cli/src/wf_cli/commands/checkpoint_cmd.py:261`（`print()`）、
  `cli/src/wf_cli/review.py:614`（註解）。
  **這一項不必倚賴對帳器的解析，碼自己講得更明白**：`checkpoint_cmd.py:261` 的訊息逐字寫著
  「該 writer 尚未實作（WF-22-CLI4 切片 A 之外），在它落地前，裁定只能以人讀留言存在，
  事件流上該區間仍是升級中」，`validation.py:827` 亦同。契約已裁定升級狀態**只能**由本事件
  解除，而今天沒有任何通道寫得出這則事件。
  ⚠️ **對帳器少看到一處，但方向是低估、不是高估。** `commands/checkpoint_cmd.py:104` 還有
  第五處字面——argparse 的 `--escalation-resolution`，help 逐字寫著「（保留旗標，一律拒收）」。
  對帳器沒把它列進來的原因見 §5 末條。**補上這一處不改變任何判定**：那是刻意 fail-closed 的
  拒收面（與 §6 表列的 `spec-narrowed`／`instruction-omitted` 同族），不是 writer；writer 仍是 0。
  記在這裡是因為它讓缺口的性質更精確：**不是沒人想到，是想到了而且明著擋住**——
  契約先落地、寫入面暫以拒收佔位，等 writer 那張卡。
  判定與 §4.4 的 `review-correction` 相同（`mention-only`、writer —），處置一致；但**兩者在
  `相關動詞` 這一軸上不同**，依 §4.5 立下的分辨法不是同一種缺口：`review-correction` 是
  `相關動詞=review`（動詞在，只是不吐該字面），本項是 **`相關動詞=無`**——連一個沾得上邊的
  動詞都沒有，與 `preflight-failed` 同格。這一軸不影響處置（都是 `補寫入者`），影響的是工程量：
  前者近似留痕缺失，本項要從零長出一個寫入通道。
- **`fresh-ruling`／`carried-forward`**（§5 `resolution_basis` 的兩個取值）→ 皆 `absent`。
- **`continue-same-executor`**（§5 `resolution` 的唯一合法值）→ `absent`。

後三項是第一項的**取值**，同族一起缺，與 §4.4 末條的四個 clearance 分類
（`forged-rejected` 等，同為 `review-marker-clearance` 的取值、同為 `absent`）**是同一形狀**，
故不另立處置：writer 落地時它們會一起消失，`--check` 的第 2 個方向（登記了已不存在的缺口）
會強制回來更新本檔。

**射程界線（本檔只登記，不修補）。** 依 §2.3 與本節開頭的「本檔不實作任何一項修補」，此處
只承認缺口。`escalation-resolution` 的 writer 屬 `WF-22-CLI4` 射程，補在哪一張卡由需求方裁定。

⚠️ **同一節裡有一項看起來已實作，其實是字面碰撞，一併記下以免誤讀。**
`structurally-vacuous`（§4／§5 `authorization_binding` 的取值之一）判定 `ok`、writer 在
`cli/src/wf_cli/validation.py:480`／`:483`／`:486`——**但那不是本節的 writer**。
`cli/src/wf_cli/review.py:614` 的註解逐字聲明「⚠️ 這**不是** #39 的那個欄位」：那三行導出的是
**accepted 標記**的授權綁定（`ACCEPTED_MARKING_BINDINGS`），是同一個述詞套在另一組角色上，
刻意不共用鍵名，只是**恰好共用取值字面**。所以 `escalation-resolution` 的 `authorization_binding`
同樣沒有 writer，只是符號層看不出來——抽取規則是**詞法**的，同字面不同欄位會被併成一列
（§5 已知限制的具體實例）。本列因此既不是缺口，**也不構成本節已實作的證據**。

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
- **`--<kebab>` 形態的 argparse 旗標字面落在盲區**（實測：
  `_contains_symbol("--escalation-resolution", "escalation-resolution")` 回 `False`）。
  成因是 `_WORDISH` 含 `-`，於是前綴 `--` 算「詞內字元」、詞界不成立。
  ⚠️ **這不是可以單獨拿掉的 bug**：那條詞界正是用來擋 `deployment-status-change` 誤命中
  `status-change`（見該函式 docstring），拿掉它會讓已知缺口 `status-change` 假性變綠。
  兩者是同一條規則的兩面，要改得先想清楚怎麼同時保住那個反例。
  本檔記錄的實例是 mention 而非 writer（`commands/checkpoint_cmd.py:104` 是 argparse 宣告，
  不在任何遠端寫入路徑上），故未影響本次判定；但**盲區對 write 角色一樣成立**——若日後有
  寫入路徑以 `--` 前綴形態帶出符號，會被同樣漏判，那個方向就不再是低估。實例見 §4.7。

## 6. 缺口登記與處置

`--check` 逐項比對這個區塊。**登記＝承認缺口，不是消除缺口**（理由見 §2.3）。

處置語彙：`補寫入者`｜`補讀取者`｜`已知限制`｜`從契約移除`｜`過抽`｜`待需求方裁定`。
以下按族給處置建議；**本卡不實作任何一項**。

> ⚠️ **`WF-REDESIGN-W2B` 之後，下表有四族的成員已整批離開 universe**（成因＝三份卡面範本被移除，
> 逐符號處置見 §7.1）。⛔ 下表**保留原樣**——它記的是「當時判了什麼、建議怎麼處置」，
> 那份判斷本身沒有失效；⛔ 不得就地改寫成「已解決」。對照如下：
>
> | 下表的族 | 現況 |
> |---|---|
> | §3 五個已知實例 之 `需求` 欄 | 符號已離開 universe；其餘四項不受影響，仍是缺口 |
> | §4.2 開卡後改不動（`規劃`／`執行`／`查核`／`DB`／`服務的原始目標`） | 五個符號全部離開 universe |
> | §4.3 完全不渲染（19 項） | 全部離開 universe |
> | 過抽 之 `🔴紅線`／`⚪一般`／`card_field` 的 `目標`／`需求方`／`範圍` | 離開 universe；同列其餘成員不受影響 |
>
> ⛔ **「離開 universe」⛔ 不等於「已修復」**：修復會讓判定從 `absent` 翻成 `ok`；
> 這次是符號本身消失。工具側的渲染能力一行都沒有增加。

| 族 | 成員 | 建議處置 |
|---|---|---|
| §3 五個已知實例 | `review-invalid`、`preflight-failed`、`status-change`、amend 繞過 `find_conflicts`、`需求` 欄 | `補寫入者`（`review-invalid` 工程量最小：偵測已在，只差留痕）。`amend` 那項是**閘門繞過**，風險高於留痕缺失，建議單獨開卡 |
| §4.1 狀態無專責動詞 | `⏸阻塞`、`⏳待執行`、`💡需求`、`🔨執行中`、`🚨已升級`、`📦已合併`，以及 `assign --status` 自由文字逃生口。⛔ **`📥Backlog` 不在本族**——理由見 §4.1.1，`WF-BACKLOG-STAGE1` 已補上 `handoff --next-stage backlog` | `🚨已升級` `補寫入者`；`📦已合併` `待需求方裁定`（先釐清現況是怎麼設定的）；其餘 `待需求方裁定`（補動詞或從狀態表移除）。**`--status` 該不該收斂成 `choices` 是獨立一問**——它現在讓所有前提都可繞過 |
| §4.2 開卡後改不動 | `規劃`、`執行`、`查核`、`DB`、`服務的原始目標` | `補寫入者`（`規劃` 優先：它與 `需求` 同樣被讀作授權判準） |
| §4.3 完全不渲染 | tasks-card 7 項＋initiative-card 6 項＋bug-card 6 項 | `待需求方裁定`：`從契約移除`（承認這些是手填欄位）或補 `wfcli open --kind initiative/bug`。**不建議逐欄補**——19 個欄位逐欄開卡正是本卡要消滅的「修實例不修形狀」 |
| §4.4 事件無 writer | `escalation-epoch-change`、`handoff-accepted`、`review-correction`、`review-marker-clearance`、`baseline-change-request`、四個 clearance 分類 | `補寫入者`。`handoff-accepted` 優先——`event-verified` preflight 依據的不可達性以它為根因 |
| §4.5 命名漂移 | `escalation-checkpoint`、`contract-baseline` | `已知限制`（或統一契約名與碼內錨點名，屬低風險整理） |
| §4.6 守衛覆蓋 | `card.py` → `find_conflicts` | `待需求方裁定`：開卡時是否應做互斥比對（現況只有 assign 擋） |
| §4.7 事件無 writer（後續卡新增） | `escalation-resolution`，及其取值 `fresh-ruling`／`carried-forward`／`continue-same-executor` | `補寫入者`。**writer 今天不存在**——`commands/checkpoint_cmd.py:261` 與 `validation.py:827` 兩處自陳「尚未實作」，故三個取值同族一起缺，writer 落地時一併消失。補在 `WF-22-CLI4` 或另開卡由需求方裁定。⚠️ 同節的 `structurally-vacuous` 判 `ok` 是**字面碰撞**（見 §4.7 末段），不是本節已實作的證據 |
| 過抽（非契約符號） | `ubuntu-latest`、`update-branch`、`🔴紅線`、`⚪一般`、`→merge`、`→查核前`、`↔執行者`、`card_field` 的 `Log`／`目標`／`需求方`／`範圍` | `過抽`：抽取規則的已知代價，不須處置 |

⚠️ **`card_field/Log` 於 2026-08-25 由 `write-only` 變成不再是缺口，已自處置表移除。**
⛔ **那不代表 Log 真的取得了讀取者**——判定是 `writers and readers → ok`，而新的「reader」是
`WF-CARD-BODY-BUDGET1` 在 `amend_cmd._largest_field_hint` 裡以 `body.partition("\n## Log")`
切出 Log 區段來估算大小。⇒ 那是**本節所述過抽的又一個實例**：命中的是碼裡的同名字面，
⛔ 不是 initiative 卡面上的那個 `Log` 欄位。移除該列只是讓表與機械導出的結果一致，
⛔ 不得讀成「該缺口已被修復」。

| 列舉值非事件 | `data-migration`、`authoritative-artifact`、`change-executor` | `過抽`：皆有讀取者，判定為 `read-only` 屬正常 |
| 刻意 fail-closed | `spec-narrowed`、`instruction-omitted` | `已知限制`：`checkpoint_cmd` 明寫「保留旗標，一律拒收」，兩個 defer cause 在本 repo 皆不可用 |

<!-- reconcile-dispositions:begin -->
```json
{
  "gaps": {
    "delivery_status/→merge": "absent",
    "delivery_status/→查核前": "absent",
    "delivery_status/↔執行者": "absent",
    "delivery_status/⏳待執行": "read-only",
    "delivery_status/⏸阻塞": "read-only",
    "delivery_status/📦已合併": "read-only",
    "delivery_status/🚧進行中": "read-only",
    "delivery_status/🚨已升級": "read-only",
    "event/authoritative-artifact": "read-only",
    "event/baseline-change-request": "absent",
    "event/carried-forward": "absent",
    "event/change-executor": "read-only",
    "event/continue-same-executor": "absent",
    "event/contract-baseline": "write-only",
    "event/data-migration": "read-only",
    "event/escalation-checkpoint": "mention-only",
    "event/escalation-epoch-change": "mention-only",
    "event/escalation-resolution": "mention-only",
    "event/forged-rejected": "absent",
    "event/fresh-ruling": "absent",
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
    "event/ubuntu-latest": "absent",
    "event/update-branch": "absent",
    "guard/cli/src/wf_cli/card.py→brief": "validate_shape",
    "guard/cli/src/wf_cli/card.py→card_face": "_assert_schema_is_understood／_validate_against／validate／validate_issue_url",
    "guard/cli/src/wf_cli/card.py→resources": "find_conflicts",
    "guard/cli/src/wf_cli/commands/amend_cmd.py→brief": "validate_shape",
    "guard/cli/src/wf_cli/commands/amend_cmd.py→card_face": "_assert_schema_is_understood／_validate_against／validate／validate_issue_url",
    "guard/cli/src/wf_cli/commands/amend_cmd.py→resources": "find_conflicts",
    "guard/cli/src/wf_cli/commands/assign_cmd.py→card": "validate_capability_routing／validate_routing_field／validate_routing_names"
  }
}
```
<!-- reconcile-dispositions:end -->

> ⚠️ 以下是 `python3 scripts/contract_tool_reconcile.py` 的**產生輸出**，非手寫；要核對就重跑該指令逐字比對，區塊邊界是下方兩個 `reconcile-generated` marker。
> ⛔ **表中的錨點刻意不寫行號**（`路徑::符號名`／`路徑 §節標題`）。行號的壽命以「下一次合併」計：`aiwf#141` 一輪交付（分支 `ef21098`）實測就把本表 9 個行號錨點指到空行、另外 8 個碰巧修好，**淨值 +1 掩蓋了 17 筆變動**。⛔ 不得由此推出錨點永不失準——符號改名一樣會爛，差別是 `grep` 那時回 0 命中（看得出來），爛掉的行號回的是別人的內容（看不出來）。
> 錨點漂移不是缺口變化——判定是否變了以 `--check` 的第 3 個方向為準。

<!-- reconcile-generated:begin -->
- 契約側符號總數：**50**（由掃描文件導出，非人工登記）
- 判定為缺口：**33**
- 守衛覆蓋缺口：**7**
- ⚠️ 自由文字狀態旗標（可繞過所有契約前提直接設定任一已宣告狀態）：`assign_cmd.py --status（預設 🔨執行中，無 choices）`

### 事件型別（26）

| 符號 | 判定 | 契約出處 | 寫入者 | 讀取者 | 備註 |
|---|---|---|---|---|---|
| `authoritative-artifact` | read-only | `templates/review-dispatch.md §3. 前輪 findings（必列）`<br>`templates/review-escalation.md §2. Finding 分類`<br>`templates/review-escalation.md §3. 可計數的退回`<br>…共 6 | — | `cli/src/wf_cli/review.py::FINDING_CLASSES`<br>`cli/src/wf_cli/review.py::COUNTING_FINDING_CLASSES` | 相關動詞=無 |
| `baseline-change-request` | absent | `templates/baseline-cascade.md §程序` | — | — | 相關動詞=無 |
| `carried-forward` | absent | `templates/review-escalation.md §4. 三次門檻`<br>`templates/review-escalation.md §5. Adapter 必填欄位` | — | — | 相關動詞=無 |
| `change-executor` | read-only | `templates/review-escalation.md §4. 三次門檻`<br>`templates/review-escalation.md §5. Adapter 必填欄位` | — | `cli/src/wf_cli/review.py::CHECKPOINT_DECISIONS` | 相關動詞=無 |
| `continue-same-executor` | absent | `templates/review-escalation.md §5. Adapter 必填欄位` | — | — | 相關動詞=無 |
| `contract-baseline` | write-only | `templates/review-escalation.md §4. 三次門檻`<br>`templates/review-escalation.md §5. Adapter 必填欄位` | `cli/src/wf_cli/commands/checkpoint_cmd.py::run_contract_baseline` | — | 相關動詞=無 |
| `data-migration` | read-only | `AI_WORKFLOW.md §3.2 卡範圍與開卡條件`<br>`AI_WORKFLOW.md §4.2 Database Contract` | — | `cli/src/wf_cli/commands/open_cmd.py::add_parser`<br>`cli/src/wf_cli/resources.py::DB_SCOPES` | 相關動詞=無 |
| `escalation-checkpoint` | mention-only | `templates/review-dispatch.md §3. 前輪 findings（必列）`<br>`templates/review-escalation.md §2. Finding 分類`<br>`templates/review-escalation.md §4. 三次門檻`<br>…共 6 | — | — | 相關動詞=checkpoint |
| `escalation-epoch-change` | mention-only | `AI_WORKFLOW.md §4.1 Control-plane Contract`<br>`templates/review-escalation.md §4. 三次門檻`<br>`templates/review-escalation.md §5. Adapter 必填欄位` | — | — | 相關動詞=無 |
| `escalation-resolution` | mention-only | `AI_WORKFLOW.md §0.2 允許的狀態轉移（canonical 本體；採用專案**引用不複製**）`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移`<br>`` AI_WORKFLOW.md §表五：`🚨已升級` 的決策 owner ``<br>…共 5 | — | — | 相關動詞=無 |
| `forged-rejected` | absent | `templates/handoff-contract.md §3.1.4 未知版本、缺欄與 fail-closed`<br>`templates/handoff-contract.md §5. 專案實作`<br>`templates/review-escalation.md §4. 三次門檻`<br>…共 4 | — | — | 相關動詞=無 |
| `fresh-ruling` | absent | `templates/review-escalation.md §4. 三次門檻` | — | — | 相關動詞=無 |
| `handoff-accepted` | mention-only | `AI_WORKFLOW.md §0.2 允許的狀態轉移（canonical 本體；採用專案**引用不複製**）`<br>`AI_WORKFLOW.md §4.1 Control-plane Contract`<br>`templates/control-plane-contract.md §4. Handoff 與 optional tmux adapter`<br>…共 7 | — | — | 相關動詞=handoff |
| `instruction-omitted` | mention-only | `templates/review-escalation.md §4. 三次門檻`<br>`templates/review-escalation.md §5. Adapter 必填欄位` | — | — | 相關動詞=無 |
| `malformed-ignored` | absent | `templates/handoff-contract.md §3.1.4 未知版本、缺欄與 fail-closed`<br>`templates/handoff-contract.md §5. 專案實作`<br>`templates/review-escalation.md §5. Adapter 必填欄位` | — | — | 相關動詞=無 |
| `preflight-failed` | mention-only | `AI_WORKFLOW.md §0.2 允許的狀態轉移（canonical 本體；採用專案**引用不複製**）`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移`<br>`AI_WORKFLOW.md §表二：Gate／preflight 退回`<br>…共 6 | — | — | 相關動詞=無 |
| `reissue-required` | absent | `templates/handoff-contract.md §3.1.4 未知版本、缺欄與 fail-closed`<br>`templates/review-escalation.md §5. Adapter 必填欄位` | — | — | 相關動詞=無 |
| `repaired-verified` | absent | `templates/handoff-contract.md §3.1.4 未知版本、缺欄與 fail-closed`<br>`templates/review-escalation.md §5. Adapter 必填欄位` | — | — | 相關動詞=無 |
| `review-correction` | mention-only | `AI_WORKFLOW.md §3. 任務流程`<br>`AI_WORKFLOW.md §4.1 Control-plane Contract`<br>`templates/closeout-report.md §7. 翻案把手`<br>…共 6 | — | — | 相關動詞=review |
| `review-invalid` | mention-only | `AI_WORKFLOW.md §3. 任務流程`<br>`AI_WORKFLOW.md §5.2 跨家族查核範式`<br>`templates/review-dispatch.md §信封三 · 機械指令`<br>…共 9 | — | — | 相關動詞=review |
| `review-marker-clearance` | mention-only | `templates/handoff-contract.md §3.1.4 未知版本、缺欄與 fail-closed`<br>`templates/review-escalation.md §1. 三個不同層次`<br>`templates/review-escalation.md §2. Finding 分類`<br>…共 4 | — | — | 相關動詞=review |
| `spec-narrowed` | mention-only | `templates/review-escalation.md §4. 三次門檻`<br>`templates/review-escalation.md §5. Adapter 必填欄位` | — | — | 相關動詞=無 |
| `status-change` | absent | `templates/review-escalation.md §1. 三個不同層次` | — | — | 相關動詞=無 |
| `ubuntu-latest` | absent | `docs/ROADMAP.md §⚠️ 一個被實測推翻的前提：runner 不是 UTF-8` | — | — | 相關動詞=無 |
| `update-branch` | absent | `docs/ROADMAP.md §2. 唯一的執行面：CI` | — | — | 相關動詞=無 |
| `structurally-vacuous` | ok | `templates/review-escalation.md §4. 三次門檻`<br>`templates/review-escalation.md §5. Adapter 必填欄位`<br>`docs/ROADMAP.md §1. 身分：記錄宣告，不追求驗證`<br>…共 5 | `cli/src/wf_cli/validation.py::derive_accepted_marking_binding` | `cli/src/wf_cli/review.py::ACCEPTED_MARKING_BINDINGS` | 相關動詞=無 |

### 交付狀態（24）

| 符號 | 判定 | 契約出處 | 寫入者 | 讀取者 | 備註 |
|---|---|---|---|---|---|
| `→merge` | absent | `AI_WORKFLOW.md §2. 不可違反的規則` | — | — | Project 選項=否；專責動詞=否 |
| `→查核前` | absent | `AI_WORKFLOW.md §2. 不可違反的規則` | — | — | Project 選項=否；專責動詞=否 |
| `↔執行者` | absent | `AI_WORKFLOW.md §1.1 治理模型：決策與機械寫入分離` | — | — | Project 選項=否；專責動詞=否 |
| `⏳待執行` | read-only | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移`<br>`` AI_WORKFLOW.md §表七：條文 ↔ `handoff_cmd.py` 的落差登記 `` | — | `cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=否；⚠️ 沒有專責動詞；只有自由文字旗標寫得進去（見報告的「自由文字狀態旗標」） |
| `⏸阻塞` | read-only | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束`<br>`AI_WORKFLOW.md §為什麼不下放（直接回應「一個看板服務兩個 repo」）`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移`<br>…共 13 | — | `cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=否；⚠️ 沒有專責動詞；只有自由文字旗標寫得進去（見報告的「自由文字狀態旗標」） |
| `📦已合併` | read-only | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束`<br>`AI_WORKFLOW.md §狀態`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移`<br>…共 9 | — | `cli/src/wf_cli/doctor.py::run_doctor`<br>`cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=否；⚠️ 沒有專責動詞；只有自由文字旗標寫得進去（見報告的「自由文字狀態旗標」） |
| `🚧進行中` | read-only | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移`<br>`` AI_WORKFLOW.md §表七：條文 ↔ `handoff_cmd.py` 的落差登記 `` | — | `cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=否；⚠️ 沒有專責動詞；只有自由文字旗標寫得進去（見報告的「自由文字狀態旗標」） |
| `🚨已升級` | read-only | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移`<br>`AI_WORKFLOW.md §表四：escalation checkpoint`<br>…共 9 | — | `cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=否；⚠️ 沒有專責動詞；只有自由文字旗標寫得進去（見報告的「自由文字狀態旗標」） |
| `↩退回` | ok | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束`<br>`AI_WORKFLOW.md §為什麼要兩軸`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移`<br>…共 6 | `cli/src/wf_cli/doctor.py::REVIEW_RESULT_EXPECTED_STATUS`<br>`cli/src/wf_cli/review.py::STATUS_BY_RESULT` | `cli/src/wf_cli/doctor.py::REVIEW_RESULT_EXPECTED_STATUS`<br>`cli/src/wf_cli/project.py::FIELD_SPECS`<br>`cli/src/wf_cli/review.py::STATUS_BY_RESULT` | Project 選項=是；專責動詞=是 |
| `⏳部署中` | ok | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束` | `cli/src/wf_cli/commands/deploy_state_cmd.py::DEPLOYMENT_TRANSITIONS`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py::PROJECT_STATUS_BY_DEPLOYMENT_STATUS` | `cli/src/wf_cli/commands/deploy_state_cmd.py::DEPLOYMENT_TRANSITIONS`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py::PROJECT_STATUS_BY_DEPLOYMENT_STATUS`<br>`cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=是 |
| `⏸未部署` | ok | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束` | `cli/src/wf_cli/commands/deploy_declare_cmd.py::DECLARATION_TARGET`<br>`cli/src/wf_cli/commands/deploy_declare_cmd.py::add_parser`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py::DEPLOYMENT_TRANSITIONS`<br>…共 5 | `cli/src/wf_cli/commands/deploy_state_cmd.py::DEPLOYMENT_TRANSITIONS`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py::PROJECT_STATUS_BY_DEPLOYMENT_STATUS`<br>`cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=是 |
| `✅已部署` | ok | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束` | `cli/src/wf_cli/commands/deploy_state_cmd.py::DEPLOYMENT_TRANSITIONS`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py::PROJECT_STATUS_BY_DEPLOYMENT_STATUS` | `cli/src/wf_cli/commands/deploy_state_cmd.py::DEPLOYMENT_TRANSITIONS`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py::PROJECT_STATUS_BY_DEPLOYMENT_STATUS`<br>`cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=是 |
| `✅已驗證` | ok | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移`<br>`templates/worktree-lifecycle.md §Worktree Lifecycle Runbook` | `cli/src/wf_cli/commands/deploy_state_cmd.py::DEPLOYMENT_TRANSITIONS`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py::PROJECT_STATUS_BY_DEPLOYMENT_STATUS`<br>`cli/src/wf_cli/commands/handoff_cmd.py::run` | `cli/src/wf_cli/commands/deploy_state_cmd.py::DEPLOYMENT_TRANSITIONS`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py::PROJECT_STATUS_BY_DEPLOYMENT_STATUS`<br>`cli/src/wf_cli/commands/handoff_cmd.py::run`<br>…共 4 | Project 選項=是；專責動詞=是 |
| `✅通過` | ok | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移`<br>`` AI_WORKFLOW.md §表七：條文 ↔ `handoff_cmd.py` 的落差登記 ``<br>…共 4 | `cli/src/wf_cli/doctor.py::REVIEW_RESULT_EXPECTED_STATUS`<br>`cli/src/wf_cli/review.py::STATUS_BY_RESULT` | `cli/src/wf_cli/doctor.py::REVIEW_RESULT_EXPECTED_STATUS`<br>`cli/src/wf_cli/project.py::FIELD_SPECS`<br>`cli/src/wf_cli/review.py::STATUS_BY_RESULT` | Project 選項=是；專責動詞=是 |
| `🏁完成` | ok | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移`<br>`AI_WORKFLOW.md §表六：規劃期須納入的三項，各自的落點與「今天有沒有執行者」`<br>…共 7 | `cli/src/wf_cli/commands/assign_cmd.py::TERMINAL_STATUSES`<br>`cli/src/wf_cli/commands/handoff_cmd.py::run`<br>`cli/src/wf_cli/doctor.py::HANDOFF_STAGE_EXPECTED_STATUS` | `cli/src/wf_cli/commands/assign_cmd.py::TERMINAL_STATUSES`<br>`cli/src/wf_cli/doctor.py::HANDOFF_STAGE_EXPECTED_STATUS`<br>`cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=是 |
| `💡需求` | ok | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移` | `cli/src/wf_cli/card.py::Card`<br>`cli/src/wf_cli/commands/handoff_cmd.py::STAGE_STATUS`<br>`cli/src/wf_cli/doctor.py::HANDOFF_STAGE_EXPECTED_STATUS`<br>…共 4 | `cli/src/wf_cli/commands/handoff_cmd.py::STAGE_STATUS`<br>`cli/src/wf_cli/doctor.py::HANDOFF_STAGE_EXPECTED_STATUS`<br>`cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=是 |
| `📥Backlog` | ok | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束`<br>`AI_WORKFLOW.md §為什麼要兩軸`<br>`AI_WORKFLOW.md §⛔ 非射程（WF-STAGE-STATE-TWO-AXIS1）`<br>…共 9 | `cli/src/wf_cli/commands/handoff_cmd.py::STAGE_STATUS`<br>`cli/src/wf_cli/doctor.py::HANDOFF_STAGE_EXPECTED_STATUS`<br>`cli/src/wf_cli/doctor.py::CONFORMANCE_KNOWN_GAP` | `cli/src/wf_cli/commands/handoff_cmd.py::STAGE_STATUS`<br>`cli/src/wf_cli/doctor.py::HANDOFF_STAGE_EXPECTED_STATUS`<br>`cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=是 |
| `🔍待查核` | ok | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移`<br>`templates/handoff-contract.md §3.1.6 轉錄與 doctor 判定`<br>…共 6 | `cli/src/wf_cli/commands/handoff_cmd.py::STAGE_STATUS`<br>`cli/src/wf_cli/commands/review_cmd.py::AWAITING_REVIEW_STATUS`<br>`cli/src/wf_cli/doctor.py::HANDOFF_STAGE_EXPECTED_STATUS` | `cli/src/wf_cli/commands/handoff_cmd.py::STAGE_STATUS`<br>`cli/src/wf_cli/doctor.py::HANDOFF_STAGE_EXPECTED_STATUS`<br>`cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=是 |
| `🔨執行中` | ok | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移`<br>`AI_WORKFLOW.md §表六：規劃期須納入的三項，各自的落點與「今天有沒有執行者」`<br>…共 6 | `cli/src/wf_cli/commands/assign_cmd.py::add_parser`<br>`cli/src/wf_cli/commands/handoff_cmd.py::STAGE_STATUS`<br>`cli/src/wf_cli/doctor.py::HANDOFF_STAGE_EXPECTED_STATUS` | `cli/src/wf_cli/commands/handoff_cmd.py::STAGE_STATUS`<br>`cli/src/wf_cli/doctor.py::HANDOFF_STAGE_EXPECTED_STATUS`<br>`cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=是 |
| `🔬研究中` | ok | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束`<br>`AI_WORKFLOW.md §為什麼要兩軸`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移`<br>…共 4 | `cli/src/wf_cli/commands/handoff_cmd.py::STAGE_STATUS`<br>`cli/src/wf_cli/doctor.py::HANDOFF_STAGE_EXPECTED_STATUS` | `cli/src/wf_cli/commands/handoff_cmd.py::STAGE_STATUS`<br>`cli/src/wf_cli/doctor.py::HANDOFF_STAGE_EXPECTED_STATUS`<br>`cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=是 |
| `🚀待部署` | ok | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束` | `cli/src/wf_cli/commands/deploy_state_cmd.py::DEPLOYMENT_TRANSITIONS`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py::PROJECT_STATUS_BY_DEPLOYMENT_STATUS` | `cli/src/wf_cli/commands/deploy_state_cmd.py::DEPLOYMENT_TRANSITIONS`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py::PROJECT_STATUS_BY_DEPLOYMENT_STATUS`<br>`cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=是 |
| `🛑已停止` | ok | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移`<br>`` AI_WORKFLOW.md §表七：條文 ↔ `handoff_cmd.py` 的落差登記 ``<br>…共 4 | `cli/src/wf_cli/commands/assign_cmd.py::TERMINAL_STATUSES` | `cli/src/wf_cli/commands/assign_cmd.py::TERMINAL_STATUSES`<br>`cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=是 |
| `🧪驗證中` | ok | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束` | `cli/src/wf_cli/commands/deploy_state_cmd.py::DEPLOYMENT_TRANSITIONS`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py::PROJECT_STATUS_BY_DEPLOYMENT_STATUS` | `cli/src/wf_cli/commands/deploy_state_cmd.py::DEPLOYMENT_TRANSITIONS`<br>`cli/src/wf_cli/commands/deploy_state_cmd.py::PROJECT_STATUS_BY_DEPLOYMENT_STATUS`<br>`cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=是 |
| `🧭規劃中` | ok | `AI_WORKFLOW.md §切換前的現行看板語彙與仍有效的約束`<br>`AI_WORKFLOW.md §表一：交付狀態的允許轉移`<br>`AI_WORKFLOW.md §表六：規劃期須納入的三項，各自的落點與「今天有沒有執行者」`<br>…共 4 | `cli/src/wf_cli/commands/handoff_cmd.py::STAGE_STATUS`<br>`cli/src/wf_cli/doctor.py::HANDOFF_STAGE_EXPECTED_STATUS` | `cli/src/wf_cli/commands/handoff_cmd.py::STAGE_STATUS`<br>`cli/src/wf_cli/doctor.py::HANDOFF_STAGE_EXPECTED_STATUS`<br>`cli/src/wf_cli/project.py::FIELD_SPECS` | Project 選項=是；專責動詞=是 |

### 守衛覆蓋缺口（7）

| 寫入入口 | 資料模組 | 用到的 serializer | 未跑的守衛 |
|---|---|---|---|
| `cli/src/wf_cli/card.py` | `brief` | `render_block` | `validate_shape` |
| `cli/src/wf_cli/card.py` | `card_face` | `render_block` | `_assert_schema_is_understood／_validate_against／validate／validate_issue_url` |
| `cli/src/wf_cli/card.py` | `resources` | `render_block` | `find_conflicts` |
| `cli/src/wf_cli/commands/amend_cmd.py` | `brief` | `render_block` | `validate_shape` |
| `cli/src/wf_cli/commands/amend_cmd.py` | `card_face` | `render_block` | `_assert_schema_is_understood／_validate_against／validate／validate_issue_url` |
| `cli/src/wf_cli/commands/amend_cmd.py` | `resources` | `render_block` | `find_conflicts` |
| `cli/src/wf_cli/commands/assign_cmd.py` | `card` | `format_branch_worktree` | `validate_capability_routing／validate_routing_field／validate_routing_names` |
<!-- reconcile-generated:end -->

## 7. `WF-REDESIGN-W2B` 的基線 set diff 與逐項處置

卡面 AC2：以**已釘死的基線 artifact** 與 W2A＋W2B 的 merge result 做 set diff，
**每個 removed／added／changed symbol 逐項 disposition**。⛔ count 只作摘要——集合與 hash 才是基線。

**diff identity ＝ `(kind, name)`**：added／removed 依 key；changed ＝同 key 的 canonical row 不同。

### 7.0 怎麼重跑（本節三個機械區塊都由此產生，⛔ 非手寫）

```python
# 基線 artifact 的身分：全檔位元組即 canonical 序列化，⇒ 兩者 sha256 相同
import hashlib, json, subprocess, sys
raw = open("docs/research/drafts/wave-specs/baseline-universe.json", "rb").read()
assert hashlib.sha256(raw).hexdigest() == \
    "c1a1279324f2b5f40421eaa0408314a1afadae2c374c0c98782f66510af4bb68"
base = json.loads(raw.decode("utf-8"))

# merge result 的同 schema artifact
cur = json.loads(subprocess.run(
    [sys.executable, "scripts/contract_tool_reconcile.py", "--format", "json"],
    capture_output=True, text=True, check=True).stdout)

def rows_sha(rows):                       # rows 依 (kind,name) 排序後 canonical 序列化
    s = sorted(rows, key=lambda r: (r["kind"], r["name"]))
    blob = json.dumps(s, ensure_ascii=False, sort_keys=True, separators=(",", ": "))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()

B = {(r["kind"], r["name"]): r for r in base["rows"]}
C = {(r["kind"], r["name"]): r for r in cur["rows"]}
removed, added = sorted(set(B) - set(C)), sorted(set(C) - set(B))
```

⚠️ **`rows` 的 hash 與全檔 hash 是兩個不同的量。** 基線 artifact 帶 `_meta`（載 source SHA
與 generator 版本），故全檔 hash 含 `_meta`；`rows` hash 不含。**跨 HEAD 比對用 `rows` hash**
——`_meta.source_sha` 每次產生都不同，用全檔 hash 比等於保證永遠不相等。

<!-- w2b-setdiff:begin -->

- 基線 artifact：`docs/research/drafts/wave-specs/baseline-universe.json`（`_meta.source_sha` = `ce45a80f9dfe89d38e53d25a0b012e7bc8956003`）
- 基線全文 sha256（＝卡面 AC2 釘死值）：`c1a1279324f2b5f40421eaa0408314a1afadae2c374c0c98782f66510af4bb68`
- 基線 rows canonical sha256：`d13ba6c04f5954295c705f515dbc1f242bd513d00da2eb708777b940c98d45cc`
- **本次 merge result rows canonical sha256：`117793f8cab5955bb414782e0b9b37816b1d2d976656cd07c97ca19c3460d73f`**
- 摘要（⛔ 非基線，集合與 hash 才是）：基線 rows 86 → 本次 50；removed 36／added 0／changed 25；缺口 54 → 33；守衛缺口 5 → 7

### 7.1 removed（36）——符號離開 universe

| kind | 符號 | 基線判定 | 基線出處檔 | 處置 |
|---|---|---|---|---|
| `card_field` | `DB` | `ok` | `templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `Design` | `absent` | `templates/initiative-card.md`<br>`templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `Discovery` | `absent` | `templates/initiative-card.md`<br>`templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `Initiative` | `ok` | `templates/bug-card.md`<br>`templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `Log` | `ok` | `templates/bug-card.md`<br>`templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `Merge SHA` | `absent` | `templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `PR` | `mention-only` | `templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `owner` | `ok` | `templates/initiative-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `spec 基線` | `ok` | `templates/initiative-card.md`<br>`templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `依賴與子卡` | `absent` | `templates/initiative-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `修復` | `mention-only` | `templates/bug-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `分支` | `ok` | `templates/bug-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `回歸測試` | `absent` | `templates/bug-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `執行` | `ok` | `templates/bug-card.md`<br>`templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `基線變更紀錄` | `absent` | `templates/initiative-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `服務的原始目標` | `ok` | `templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `查核` | `ok` | `templates/bug-card.md`<br>`templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `核心痛點` | `ok` | `templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `根因` | `mention-only` | `templates/bug-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `決策與風險` | `absent` | `templates/initiative-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `環境` | `mention-only` | `templates/bug-card.md`<br>`templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `目標` | `write-only` | `templates/initiative-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `範圍` | `read-only` | `templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `規劃` | `ok` | `templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `資源宣告` | `ok` | `templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `部署` | `read-only` | `templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `里程碑` | `absent` | `templates/initiative-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `重現` | `mention-only` | `templates/bug-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `需求` | `ok` | `templates/bug-card.md`<br>`templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `需求方` | `write-only` | `templates/initiative-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `非目標` | `absent` | `templates/initiative-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `預期 vs 實際` | `absent` | `templates/bug-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `驗收條件` | `ok` | `templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `驗證` | `ok` | `templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `delivery_status` | `⚪一般` | `absent` | `templates/bug-card.md`<br>`templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `delivery_status` | `🔴紅線` | `absent` | `templates/bug-card.md`<br>`templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |

### 7.2 added（0）——新符號進 universe

（無。本卡新增的六份範本刻意不引入新的契約符號：反引號 kebab 一律沿用既有符號，emoji 後一律留空白以免被抽成交付狀態。）

### 7.3 changed（25）——同 key、canonical row 不同

| kind | 符號 | 變動欄 | 判定 基線 → 本次 | 處置 |
|---|---|---|---|---|
| `delivery_status` | `↩退回` | `doc_hits` | `ok` → `ok` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `⏳待執行` | `doc_hits` | `read-only` → `read-only` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `⏳部署中` | `doc_hits` | `ok` → `ok` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `⏸未部署` | `doc_hits`、`mentions` | `ok` → `ok` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `⏸阻塞` | `doc_hits` | `read-only` → `read-only` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `✅已部署` | `doc_hits` | `ok` → `ok` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `✅已驗證` | `doc_hits`、`mentions` | `ok` → `ok` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `✅通過` | `doc_hits` | `ok` → `ok` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `🏁完成` | `doc_hits` | `ok` → `ok` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `💡需求` | `doc_hits` | `ok` → `ok` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `📥Backlog` | `doc_hits` | `ok` → `ok` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `📦已合併` | `doc_hits` | `read-only` → `read-only` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `🔍待查核` | `doc_hits` | `ok` → `ok` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `🔨執行中` | `doc_hits` | `ok` → `ok` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `🔬研究中` | `doc_hits` | `ok` → `ok` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `🚀待部署` | `doc_hits` | `ok` → `ok` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `🚧進行中` | `doc_hits` | `read-only` → `read-only` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `🚨已升級` | `doc_hits` | `read-only` → `read-only` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `🛑已停止` | `doc_hits` | `ok` → `ok` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `🧪驗證中` | `doc_hits` | `ok` → `ok` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `delivery_status` | `🧭規劃中` | `doc_hits` | `ok` → `ok` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `event` | `authoritative-artifact` | `doc_hits` | `read-only` → `read-only` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `event` | `escalation-checkpoint` | `doc_hits` | `mention-only` → `mention-only` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `event` | `review-correction` | `doc_hits` | `mention-only` → `mention-only` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |
| `event` | `review-invalid` | `doc_hits` | `mention-only` → `mention-only` | `錨點漂移`：判定未變（`--check` 第 3 個方向不響） |

<!-- w2b-setdiff:end -->
