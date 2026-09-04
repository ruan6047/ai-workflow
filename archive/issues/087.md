# #87 資源與狀態詞彙：文件在用的 token 在機器上不存在，且失效方向是靜默
- state: closed  created: 2026-08-14T07:07:27Z  closed: 2026-08-19T03:01:56Z
- url: https://github.com/ruan6047/ai-workflow/issues/87
- comments: 7

## Body

## 症狀

三個在文件／慣例中使用的詞彙，在 `wfcli` 機械面不存在，且失效方向都是**靜默**：

1. **`db:<env>:cpbl`** —— `resources.py` 的 grammar 是 `db:[^:]+:(schema|table:.+)`，`cpbl` 這個 token 直接不合法。消費端 `cpbl-analytics` 的 `docs/DATABASE_CONTRACT.md` **通篇在用**（line 20/21/22/32/38/46）。照契約寫的人只有兩種下場：貼進卡面被 `ResourceDeclarationError` 擋下，或寫進 spec 檔而**永遠不被檢查**。
2. **`🧭規劃中`** —— 交付狀態欄無此選項，實測 `assign --status 🧭規劃中` 回「欄位 '交付狀態' 沒有選項」。消費端的 ROADMAP 把「`wfcli` 有 `🧭規劃中` 狀態」寫成 WF 能力恢復條件。**後果**：規劃 Gate 通過但 Plan 尚未完成的卡沒有狀態可表達，只能留在 `💡需求`，看起來像沒開始。
3. **`gate_evidence`** —— 慣例上要求「PM 更新 `gate_evidence`」，但整個 repo（含 cli 與 docs）零命中，沒有任何儲存。

## 環境名未受驗證造成的靜默不撞

grammar 對環境名不做驗證，而 `find_conflicts` 是 `set & set`（完全相同字串才算撞，`resources.py:130-150` 註解逐字如此）。消費端現行 17 筆 db token 有 **`prod`×5 / `production`×2 / `local`×8 / `dev`×2** 四種寫法。

於是兩張都宣告同一張生產表、只是一邊寫 `db:prod:table:X`、一邊寫 `db:production:table:X` 的卡，**不會被判為衝突，不報錯、不警告**。

附帶一個容易誤解的點：`db:<env>:schema` 對 `db:<env>:table:X` **沒有支配關係**（同樣是完全相同字串才算撞）。宣告 schema 不會擋住宣告個別表的卡。這與「schema 是全域互斥鎖」的直覺相反，值得在文件明說。

## 建議

grammar 與環境詞彙的裁定屬本 repo；消費端 `cpbl-analytics` 已開 `DEV-RESOURCE-VOCAB-ALIGN1`（[#139](https://github.com/ruan6047/cpbl-analytics/issues/139)）處理它自己的文件與卡面詞彙，**刻意不做成子卡**以免鏈深。

可考慮的方向（不預設答案）：環境名列舉化並拒收表列外的值；`db:<env>:cpbl` 要嘛納入 grammar、要嘛從契約文件移除；`🧭規劃中` 補進狀態欄或從文件移除；`gate_evidence` 補欄位或改為以留言留痕。

## 來源

`cpbl-analytics` [#136](https://github.com/ruan6047/cpbl-analytics/issues/136) 的 Design Gate finding 3／4／6，加上 PM 後續實測。相關既有 issue：#12（`open` 後欄位不可改）、#13（跨家族查核者無寫入通道）。


## Comment 5297569833 · 2026-08-14T19:57:00Z

## 追加同族實例：`open` 的預設狀態直接跨過規劃 Gate，失效率 4/4

本 issue 已收錄「`🧭規劃中` 狀態不存在」。**追加一項同根因的實例，因為它每天都在發生。**

### 症狀

`wfcli open` 的預設交付狀態是 `📥Backlog`。而消費端 `cpbl-analytics` 的 `docs/ROADMAP.md` §2.0 逐字規定：**規劃 Gate（Discovery → Design → Plan）未過，不得進 `📥Backlog`／不得認領。**

**所以每一次 `open` 都直接把卡放進一個它按規定還不該到的狀態。**

### 這不是「有時候會漏」，是從來沒有一次做對

2026-08-13 至 08-15，`cpbl-analytics` 開了 6 張卡：

| 卡 | 開卡即落 | 事後補救 |
|---|---|---|
| `#131 DATA-BOX-DEEP-SILENT-FAIL1` | `📥Backlog` | 退回 `💡需求` |
| `#132 OPS-SCHEDULE-FAILURE-BLIND1` | `📥Backlog` | 退回 `💡需求` |
| `#138 DATA-OFFICIAL-STATUS-TIEBREAK1` | `📥Backlog` | 退回 `💡需求` |
| `#139 DEV-RESOURCE-VOCAB-ALIGN1` | `📥Backlog` | 退回 `💡需求` |
| `#140 DOC-ENTRY-ROUTING1` | `📥Backlog` | 退回 `💡需求` |
| `#141 DEV-SCRIPT-INVENTORY1` | `📥Backlog` | 退回 `💡需求` |

**6/6。** 而且違規者是**寫下那條規則的同一個 PM**——`#130` 那張卡跑了七輪跨家族查核、把規則寫進權威文件並 merge 上線，**上線當天又犯了兩次**。

前四次已記入該專案 `docs/ROADMAP.md` §2.7 的實績格。

### 為什麼歸在本 issue 而不另開

同一個根因：**`wfcli` 沒有規劃階段的表示法。**

因為沒有 `🧭規劃中`，`open` 只能把卡放進 `📥Backlog`——那是它唯一能表達「已登記、尚未執行」的狀態。**兩個症狀是同一個缺口的正反面**：一個是狀態詞彙缺席，一個是預設值因此必然跨過閘門。

### 失效方向是靜默（與本 issue 其餘項一致）

`open` 成功、印出 issue 連結、沒有任何警示。**卡片就這樣待在 Backlog，直到有人（PM）記得回頭退。** 若 PM 沒記得，下一個人看到 `📥Backlog` 會合理認為它已過 Gate、可以認領——**而規劃階段從未發生過**。

### 可能的方向（不預設答案）

- `open` 支援 `--status`，讓呼叫端指定落點
- `open` 預設改為某個「未過閘門」的狀態
- 補上 `🧭規劃中`（本 issue 已收錄），`open` 預設落它

⚠️ **消費端的 PM checklist 不算解法**——實測 6/6 失效，且失效者知道規則存在。這正是「有義務但沒有守衛」的典型：規則被寫下來、成本沒付、然後被繞過。

### 來源

`cpbl-analytics` `#140` 的 Design Gate 質詢過程中量化。相關既有 issue：#12（`open` 後欄位不可改）、#13（跨家族查核者無寫入通道）。


## Comment 5300449936 · 2026-08-15T04:06:45Z

## 需求方裁定：本卡併入 `#88`，由該卡承接（2026-08-15）

需求方 2026-08-15 裁定 **`#87` 與 `#88` 合併成一張**，存續卡為 [`#88 WF-DISPOSITION-FIX1`](https://github.com/ruan6047/ai-workflow/issues/88)。

**理由**：兩張是同一個病的兩個症狀——**`wfcli` 的機械面與文件宣稱的能力不一致，而不一致的方向是靜默的**。本卡記的是 `db:<env>:cpbl`／`🧭規劃中`／`gate_evidence` 三個詞彙在機器上不存在；`#88` 記的是 `registered-finding` 被寫進文件卻從未建立、27 張 open 套用 0 張。`#88` 的 R1 查核者已正面判定它是本專案**第八個「命名了但沒接線」**。

而需求方對 `#88` 已裁的 **B 案**（`wfcli` 同時擁有 label 與交付狀態欄）把射程放進 `cli/`——**與本卡四項的修法落在同一個地方**，分開做會撞資源。

### 本卡內容已完整轉錄至 `#88`

見 `#88` 的 [issuecomment-5300448667](https://github.com/ruan6047/ai-workflow/issues/88#issuecomment-5300448667)，四項逐條帶過，含本卡指出的反直覺點（`db:<env>:schema` 對 `db:<env>:table:X` **沒有支配關係**）。

### 本卡**不關閉**

保留原文作為證據。本卡的價值不只在四個待修項，還在它**用實測數字記下了失效的形狀**——現行 17 筆 db token 有 `prod`×5／`production`×2／`local`×8／`dev`×2 四種寫法，而 `find_conflicts` 是 `set & set`。那份量測若隨關卡消失，下一輪就得重做。

⚠️ 本卡與 `#139`（`cpbl-analytics` 的 `DEV-RESOURCE-VOCAB-ALIGN1`）的分工不變：**grammar 與環境詞彙的裁定屬本 repo，消費端自己的文件與卡面詞彙屬 `#139`**。`#139` 目前 `⏸阻塞` 於本卡，阻塞對象隨本次合併改為 `#88`。


## Comment 5318153731 · 2026-08-17T17:23:41Z

## 需求方裁定：四項全數定案（2026-08-18）

需求方 2026-08-18 對本卡四項各下一句裁定。**本則是裁定，不是交付**——實作面各自的落點見末節。

### 一、`db:<env>:cpbl` → **消費端改用 `db:<env>:schema`；範本標明 `schema` 是字面關鍵字**

⭐ 診斷修正：這不是「grammar 太窄」，是**採用專案把字面關鍵字讀成了佔位符**。

```
ai-workflow  templates/database-contract.md:33   db:<environment>:schema   ← schema 是字面關鍵字
cpbl         docs/DATABASE_CONTRACT.md:32        db:<environment>:cpbl     ← 換成了 schema 名稱
```

裁定 `cpbl-analytics` 改用 `db:<env>:schema`，**grammar 不動**。理由：cpbl 只有一個 schema（`cpbl`），`db:production:schema` 語意無歧義，而 `db:<env>:schema:<name>` 今天沒有任何消費者。

⚠️ **但範本那一行必須標明 `schema` 是字面關鍵字**——這才是預防。不標，下一個採用專案會犯同樣的誤讀，**而且它不會知道自己讀錯了**（這正是 `#88` R1 finding ② 所說的「傳遞介面失真會複製到每個採用專案」）。

### 二、`🧭規劃中` → **補進狀態欄**

`ai-workflow` 全庫 0 命中；`cpbl-analytics` `docs/ROADMAP.md:322/326` 已把它寫進**正式生命週期圖**（`💡需求 → 🧭規劃中 → 📥Backlog`），`:335` 另有一節記載「不存在」的過渡做法與代價。

裁定**加入**而非從文件移除。理由：cpbl 已經把它當正式流程在用，移除是改流程、加入是補實作，後者誠實；且 cpbl 有 34 張卡停在 `💡需求`，分不出「沒開始」與「規劃中」。

實作面兩步：`cli/src/wf_cli/project.py:37-43` 的 SINGLE_SELECT 加一個值，**以及 GitHub Project #4 的欄位選項加一個**（後者是設定變更，須需求方手動執行；`wfcli` 寫不進不存在的選項）。

### 三、`gate_evidence` → **維持現狀，明寫為約定，不補欄位**

⚠️ 這一項**已經不是靜默的**。`cpbl-analytics` `docs/ROADMAP.md:361-362` 逐字寫著：

> ⚠️ `planning-started`／`cpbl-planning/v1`／`gate_evidence` 目前都只是本檔（與卡面留言）的約定

而本 repo 自己的規則就是「**沒有機械執行者的寫成約定**」（`AGENTS.md` 對 trailer 檢查器的同一條處置）。消費端已照做。補欄位是一個沒有消費者的功能。

### 四、環境名未受驗證 → **列舉化，拒收表列外的值**

裁定 grammar 對環境名採封閉集合（`local｜test｜staging｜production`，與 `templates/database-contract.md:22-23` 一致），表列外的值拒收。

理由：這是**開放集合 → 封閉集合**，是本專案先前唯一驗證有效的跳出法；且失效方向是靜默、對象是生產資料庫，兩個條件同時成立時便宜的做法不划算。

⚠️ **代價不掩飾**：列舉表硬編在 `resources.py`，採用專案若用別的環境名就得改。這是契約的本意，但它是代價。

### 五、附帶裁定：`schema` 不支配 `table`，須明寫

`db:<env>:schema` 對 `db:<env>:table:<name>` **沒有支配關係**（`find_conflicts` 是完全相同字串才算撞）。宣告整個 schema **不會**擋住宣告個別表的卡。這與「schema 是全域互斥鎖」的直覺相反，裁定在範本與 canonical 明寫。

---

## ⚠️ 裁定前的實測：第四項的危害成立，但**尚未發作**

兩 repo 全卡（含已關）的 `resource-claims` 區塊共 **19 筆 db token**，環境名分布 `local×8 / prod×5 / production×2 / dev×4`。

| token | 卡 | state |
|---|---|---|
| `db:prod:schema` | cpbl#136 | CLOSED |
| `db:prod:table:game_plate_appearances` | cpbl#88 | CLOSED |
| `db:prod:table:game_recap_builds` | cpbl#88 | CLOSED |
| `db:prod:table:game_schedule_status_revisions` | cpbl#136 | CLOSED |
| `db:prod:table:game_source_revisions` | cpbl#136 | CLOSED |
| `db:production:table:batter_re24` | cpbl#119 | **OPEN** |
| `db:production:table:pitcher_re24` | cpbl#119 | **OPEN** |

**尾綴零重疊 → 靜默不撞沒有真的發生過。** 所有 `prod` 都在已關的卡上，唯一開著的 `#119` 用 `production`。

兩點對卡面的更正：

1. 卡面寫 `dev×2`，**實為 4**（卡面只數活卡，本次數全部含已關）。
2. `db:prod:schema`（#136）與 `db:production:table:batter_re24`（#119）之間有**兩個獨立理由**不會被判衝突：環境名不同、且 schema 不支配 table。**只修其中一個不夠**——這是第四項與第五項必須一起裁的原因。

裁定不因此改變，但**急迫性下降**：這是防患，不是滅火。

---

## 實作面的落點（本則不指派）

| 項 | 改哪裡 | 誰 |
|---|---|---|
| 一 | `cpbl-analytics/docs/DATABASE_CONTRACT.md`（:20 :21 :22 :32 :46） | cpbl-analytics#139 |
| 一（預防） | `templates/database-contract.md:33` 標明字面關鍵字 | 本 repo |
| 二 | `cli/src/wf_cli/project.py:37-43` 加值 | 本 repo |
| 二 | **GitHub Project #4 欄位選項加值** | ⚠️ 設定變更，需求方手動 |
| 三 | 無（維持現狀） | — |
| 四 | `cli/src/wf_cli/resources.py:43-44` 環境名列舉化 | 本 repo |
| 四 | cpbl 現有 `prod`×5／`dev`×4 正規化 | cpbl-analytics#139 |
| 五 | 範本與 canonical 明寫 schema 不支配 table | 本 repo |

**`cpbl-analytics#139` 的阻塞至此解除**——它等的四項裁定已全部給出。

⚠️ 本則未處理的：`#87` 目前**不在 Project #4 板上**（`projectItems=[]`），而本 repo 沒有把既有 Issue 掛上看板的 `wfcli` 動詞。掛板方式待需求方裁定。


## Comment 5327573635 · 2026-08-18T11:35:09Z

## 狀態更新：四項裁定的落點（2026-08-18）

本卡的四項裁定已於 [issuecomment-5318153731](https://github.com/ruan6047/ai-workflow/issues/87#issuecomment-5318153731) 全部給出。**本卡因此不再「等裁定」，改為「等下游」。** 逐項落點：

| 項 | 內容 | 落點 | 狀態 |
|---|---|---|---|
| 一（消費端） | `cpbl-analytics/docs/DATABASE_CONTRACT.md` 改用 `db:<env>:schema` | `cpbl-analytics#139` | ⏳ 未做 |
| **一（預防面）** | 範本標明 `schema`／`table` 是字面關鍵字 | PR #100，squash `f207d2e` | ✅ **已落地** |
| 二 | `🧭規劃中` 補進狀態欄 | `WF-STATUS-VOCAB-ALIGN1`（#101） | 🔨 已開卡 |
| 三 | `gate_evidence` 維持現狀、明寫為約定 | — | ✅ **no-op**（消費端 `cpbl-analytics/docs/ROADMAP.md:361-362` 已自陳為約定） |
| 四 | 環境名列舉化 | 待 `#139` 之後 | ⏸ **阻塞於下游** |
| **五（附帶裁定）** | `db:<env>:schema` 不支配 `db:<env>:table:<name>` | PR #100，squash `f207d2e` | ✅ **已落地** |

### ⚠️ 第四項為什麼必須排在 `#139` 之後

環境名列舉化會讓表列外的值被 grammar 拒收，而實測有**兩張開著的卡**會因此變成非法宣告：

```
cpbl-analytics#90   db:dev:table:game_completion_evidence
cpbl-analytics#53   db:dev:table:pitch_tracking
```

`dev` 不在契約的環境列表（`local｜test｜staging｜production`）裡，正規化屬 `#139` 的射程。順序反了會打破那兩張卡。

### 二的射程說明

`#101` 只承接第二項，且**只做碼面與文件面的對齊**。⚠️ 線上 Project #4 的欄位選項已於 2026-08-18 由人工 GraphQL 從 13 補到 15（含 `🔬研究中`／`🧭規劃中`，152 個 item 逐一比對零掉值），所以那一步已完成、不在 `#101` 射程內。

另有一張 `WF-STATUS-VOCAB-GATE1`（尚未開卡，草稿已備）承接寫入面閘門（preflight、`assign --status` 收斂、iteration fail-loud），**不屬本卡射程**——它源自 `#88` 撤卡後的重做，與本卡只共用「狀態詞彙」這個主題。

### 本卡的結案條件

需求方裁定：`#139` 完成正規化後，第一項與第四項才可動。**在那之前本卡維持 OPEN，不得因「四項裁定已給出」而結案**——裁定是輸入，實作才是交付。


## Comment 5331408433 · 2026-08-18T16:55:49Z

## 順序約束補記：第四項列舉化是單向門，落地前有前置（2026-08-19，需求方裁定補記）

本帖依需求方 2026-08-19 裁示補記。此約束原載於 `cpbl-analytics#139` 的 14 條版驗收（「順序閘門」條），該卡於 2026-08-18 依研究裁定收斂射程時把對別卡的 amend 條款整批移出、交需求方單獨裁定——**移出後此約束不再有任何卡持有**，故補記於本卡（列舉化的實作落點）。

### 約束

**第四項（`resources.py:43-44` 環境名收斂為 `local｜test｜staging｜production`）不得在下列前置完成前合併：**

受影響的 9 個 db token（分布 `#53` dev×1／`#55` dev×2／`#88` prod×2／`#90` dev×1／`#136` prod×3，跨家族查核 2026-08-18 已獨立複驗此分布）必須先**處置完畢**——要嘛以 `wfcli amend` 正規化為封閉集合內的值，要嘛需求方明文裁定放棄修復並接受永久鎖死。**不得默認**。

### 機制（為什麼是單向門）

`amend_cmd.py:754` 資源路徑第一行是 `current = parse_block(item.body)`——**先解析現值再套用新值**，現值非法即整個 `return 2`、零寫入，且 `amend` 無 `--force`／`--repair` 繞道（已實測）。列舉化一落地，`db:dev:*`／`db:prod:*` 就成為非法現值，這 9 個 token **永久無法經唯一寫入通道修復**。

### 現況（處置尚未完成）

- 五張卡中依三道閘門實測，**今天只有 `#90` 的宣告仍被衝突檢查讀取**（`#53` owner=待指派 gate2 即跳過；`#55`／`#88`／`#136` 終態 gate1 即跳過）。但單向門不分讀不讀——終態卡可重開，屆時已修不動。
- 三張終態卡「要不要花 amend」需求方尚未裁定。
- ⚠️ 另一批 **33 張卡今天就已在門後**（標題帶後綴＋缺 `resource-claims` 哨兵，`amend` 現在就 `return 2`）——補救路徑是 `ai-workflow#105`（Backlog，三個恢復條件）。列舉化會對它們加**第二道鎖**。
- ⚠️ 附帶已知落差：封閉集合含 `staging` 而 cpbl `docs/DATABASE_CONTRACT.md` §2 只定義 `local/test/production`——收斂後 grammar 會接受一個 cpbl 契約未定義的環境名（反向缺陷，實作時須在文件明寫）。

### 解除條件

9 個 token 逐一取得「已正規化」或「需求方明文放棄」其一，且留痕可稽核（處置清單貼回本卡）。屆時本約束自動失效，第四項可逕行實作。


## Comment 5333509654 · 2026-08-18T20:12:19Z

## 解除條件已滿足：9 個 token 逐一處置完畢（2026-08-19，需求方裁定）

依 `issuecomment-5331408433` 的解除條件——「9 個 token 逐一取得『已正規化』或『需求方明文放棄』其一，且留痕可稽核」——本帖為處置清單與受據。**第四項（`resources.py:43-44` 環境名收斂為 `local｜test｜staging｜production`）的順序約束至此解除。**

### 逐 token 處置表

| # | 卡 | 狀態 | 原 token | 處置 | 受據 |
|---|---|---|---|---|---|
| 1 | `cpbl#53` | ⏸阻塞 | `db:dev:table:pitch_tracking` | **已正規化** → `db:local:table:pitch_tracking` | amend op `51e63ba6` |
| 2 | `cpbl#90` | 📦已合併 | `db:dev:table:game_completion_evidence` | **已正規化** → `db:local:table:game_completion_evidence` | amend op `6d433e43` |
| 3 | `cpbl#55` | 🏁完成 | `db:dev:table:game_plate_appearances` | **明文放棄** | 本帖 |
| 4 | `cpbl#55` | 🏁完成 | `db:dev:table:game_recap_builds` | **明文放棄** | 本帖 |
| 5 | `cpbl#88` | 🏁完成 | `db:prod:table:game_recap_builds` | **明文放棄** | 本帖 |
| 6 | `cpbl#88` | 🏁完成 | `db:prod:table:game_plate_appearances` | **明文放棄** | 本帖 |
| 7 | `cpbl#136` | 🏁完成 | `db:prod:schema` | **明文放棄** | 本帖 |
| 8 | `cpbl#136` | 🏁完成 | `db:prod:table:game_source_revisions` | **明文放棄** | 本帖 |
| 9 | `cpbl#136` | 🏁完成 | `db:prod:table:game_schedule_status_revisions` | **明文放棄** | 本帖 |

### 正規化的兩張：為什麼不可放棄

**不是選擇題**——兩張都有後續階段要走 `assign`／`amend`，而列舉化後 `assign_cmd.py:179` 與 `amend_cmd.py:754` 對目標卡都是**嚴格** `parse_block`，非法現值即 exit 2：

- `#90`：卡面載明 Phase 2（鏈端切換，等 G4 Phase B）動工時 PM 須 `amend --resources` 重宣告 file 資源並 `assign`。不先正規化，Phase 2 整個走不動。
- `#53`：⏸阻塞解除後要重新 `assign`，同一道門。

`#53` 裁定為**只 local、不加掛 production**：Phase B 驗收雖含生產同步與兩端對帳，但 `DATABASE_CONTRACT` §2 的 production 寫入權限欄是「受保護部署 runner only」、§5 明文生產憑證不提供給本機 AI session、卡面紅線 6 把生產寫入釘為「需求方親手執行」——生產面在契約上本就不是執行者的宣告面。⚠️ 已知代價：Phase B 期間若另有卡宣告同名 production token，完全字串比對不會攔（今日板上無此 token，實測 0 撞）。

⚠️ 先前「`#53` 的 `prod` 兩義、不得斷言本機」的顧慮**已解除**：`only_prod_pk` 的 `prod` 經定義句證實是「正式表 vs 單場 API」語意（`scripts/dryrun_game_tm_fullseason.py:117` 逐字「正式表有、單場 API 沒有的列」），該 dry-run 走 `cpbl.db.conn()` → `config.py:15` 預設 `localhost:5433`，與生產庫無關。

### 三張終態卡：放棄的依據與已接受的代價

裁定依據（皆為實測）：

- **重開基率≈0**：兩 repo 全史 `issues/events` 篩 `reopened` 各 1 筆，cpbl 那筆是拋棄式 smoke 卡（`#146`）。實質工作卡被重開的觀測次數為 0。
- **慣例是開後繼卡拿全新宣告**：`#88 INGEST-PA-DAILY1-FIX1` 即 `#55` 的後繼，兩卡宣告各自獨立、舊卡 token 合法與否不參與。
- **沒有任何掃描器會對終態卡的非法 token 報錯**：窮舉兩 repo 的 `parse_block`／`try_parse_block` 呼叫點——`assign_cmd.py:231` 的他卡掃描被 `TERMINAL_STATUSES` 先跳過；`snapshot.py:54` 掃全 item 但解析失敗即靜默降級為 `resources=[]`；`cleanup.py:881` 只對被 cleanup 的目標卡且今日恆走 `unobservable`；`cpbl` 的 `scripts/`／`src/` 零命中。CI 對 `snapshot`／`doctor`／`ledger` 亦零命中。

**已知悉並接受的殘餘代價**（三項）：

1. `snapshot` 對這三張卡的宣告欄從此顯示為空——**失真而非報錯**，且「無宣告」與「宣告非法」在該輸出中不可區分。
2. 若真被重開：`assign` 與 `amend` 雙鎖死。逃生門只剩人工直接編輯 issue body——機械上可行但違反 cutover 的「唯一寫入通道＝wfcli」，屆時需需求方明文例外。**「永久鎖死」的精確語意是「鎖死於 wfcli 通道」，不是不可能修。**
3. 歷史紀錄永久留著封閉集合外的 token；若未來有工具改成嚴格全掃，這 7 個會一次浮出。

### 複驗

```
#90  db_scope=write  file:0（期望 0）  db:['db:local:table:game_completion_evidence']  env 全在封閉集合=True
#53  db_scope=write  file:2（期望 2）  db:['db:local:table:pitch_tracking']            env 全在封閉集合=True
     file 宣告=['file:src/cpbl/ingest/run_refresh_recent.py', 'file:src/cpbl/ingest/cpbl_pitch_tracking.py']

全庫殘餘非法 env（兩 repo 全部非 PR issue）：7 個 —— 恰為上表明文放棄的 7 個，無遺漏、無多出
```

（`--resources` 是整份取代，`#53` 的兩個 `file:` 為逐字重打；amend 後已斷言兩者仍在。`#90` 的資源宣告區塊尾 HTML 註解會被整章節替換吃掉，已於 amend 前逐字轉錄至該卡 `issuecomment-5333464883` 保全。）

### 第四項的後續：解鎖但不排程

順序約束解除，第四項可逕行實作。**但依 ROADMAP 紀律不排程**：實測 `resources.py:43-44` 現值仍是 `db:[^:]+:(schema|table:.+)`，無任何分支／PR／認領在途——沒有人拿著寫好的 PR 在等門開。病灶（`prod` 與 `production` 拼法差異靜默不撞）仍在計息，但暴露窗已縮小：現行活卡的 `db:production:*` 只有 `#119` 兩枚，且 `cpbl#139`（今日結案）後新卡照 `DATABASE_CONTRACT` §2 只會寫 `local`／`test`／`production`。

本卡維持 OPEN 作為第四項的定錨點。實作卡待真有受害者或需求方另行裁示時再開。

### 未驗到的

- 兩次 amend 為真實寫入並已複驗結果；但 `amend` 對 **closed issue** 的機械可行性未實測（三張終態卡本次零寫入，故未觸及）。
- `#90` 的 5 場 evidence **資料列**如何到生產：卡面只寫表結構走部署批次，未載明資料列路徑——UNKNOWN，不影響本次 token 裁定。
- `cleanup.py` 的 `_check_resources` 對 `db:` token「不因 merge 自動釋放」意味 `#90` 即使正規化，將來 cleanup 該卡時仍會因 db token 在宣告內而 fail——既有設計，非本裁定新增。


## Comment 5336978414 · 2026-08-19T03:01:55Z

## 關閉（2026-08-19，需求方裁定）

本 issue 的四項裁定已全數了結：一（預防面 PR #100＋消費端 cpbl#139 已結案）、二（#101 已結案）、三（no-op）、四（前置 9 token 已於本 issue 2026-08-19 處置表完成處置、順序約束解除、依裁定不排程）。

**定錨點已搬入 ROADMAP §3.6「已解鎖但不排程」**（PR #108，merge 4e6925e9fbdfd5c3ad715c63d2cb801cee63900a）——後續引用一律指向該節；本 issue 內的量測、裁定留言與處置表受據保留不滅。本 issue 從來不是卡（無卡 ID、不在 Project #4 板上），關閉後不再佔「有事未了」的視覺位置。
