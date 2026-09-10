# 責任衝突：36 組裁定紀錄與案例（`WF-002`）

> 卡＝`WF-002`／issue #311，T4，`iteration` 1，查核序 1。方法唯一居所＝`core/conflict-resolution.md`；本檔是**紀錄與案例**，⛔ 不是方法的第二份居所，也 ⛔ 不是責任的第二份真源。
> 母體＝不可變 artifact `docs/research/2026-09-10-responsibility-statements.md`（產生基線 `f70c7ef2b7903b2cddac0f9b90418413d830dc9e`），該檔檔頭逐字「**⛔ 覆蓋率未知。**」
> ⛔ **不宣稱 36 組是全樹同型的完整集合**；本檔只裁定該 artifact 已列的 36 組，⛔ 不得被引為「責任衝突已清盡」。

## 0 · 五個邊界定義的位置與核可狀態

五個共同缺口的答案＝`core/conflict-resolution.md` §1–§5，逐節對應：§1 責任動作四分（#1）／§2 適用期間（#2）／§3 內容所有權（#10）／§4 適用面與具名例外（#12）／§5 資訊範圍（#31）。

⚠️ **核可狀態＝未核可。** 質詢紀錄 `issuecomment-5613772414` Q3 定案逐字「五個邊界定義的**定稿要回到需求方核可**才算 AC2 達成，⛔ 不由 PM 代核」。本檔與 `core/conflict-resolution.md` 是**交付的定稿**，⛔ 不是已核可的通則；`last_confirmed: 2026-09-10` 是建檔日期，⛔ 不是需求方確認。

## 1 · 五個缺口的案例（AC2）

每例的欄位固定：正向情境／越界情境／誰能做什麼／何時／到哪裡為止／原文依據逐字。「未知」逐欄明列，⛔ 不把空值讀成「不限」。

### case_01_draft_transcribe — 起草／核可／轉錄／落欄的界線

| 欄 | 值 |
|---|---|
| 對象 | 卡面 `acceptance`、`verification` |
| 起草 | 執行者。`stages/planning.md` §5 逐字「執行者：起草規格、驗收條件、驗證項目」 |
| 核可 | 需求方。`roles/requester.md` §1 逐字「規劃階段核可取捨與驗收條件；⛔ 不寫規格」 |
| 轉錄 | 落欄者兼任，逐字搬運。`roles/conduct-common.md` §2 逐字「原文從第二行起一字不改」 |
| 落欄 | PM，以 `edit --ruling`。`roles/pm.md` §3 逐字「需求方裁定改到規格欄時以 `edit --ruling` 落卡面，⛔ 不只留在留言」 |
| 何時 | 規劃階段內；離開規劃前 `acceptance`／`verification` 非空（`core/card-schema.md` §2「離開規劃前」、`stages/planning.md` §2） |
| 到哪裡為止 | PM 的權止於逐字落欄：`roles/pm.md` §2 逐字「⛔ 不代填、⛔ 不代修、⛔ 不代寫他人產出或判定」。改內容 ⇒ 交還執行者重擬 |

- **正向**：執行者交 `acceptance` 建議稿 → 需求方以 `wf:ruling` 核可 → PM `edit --ruling` 逐字落欄。四個動作四個落點，⛔ 無「誰填」的猜測空間。
- **越界**：PM 覺得執行者的 AC3 太弱，自行改寫後落欄。⇒ 違 `roles/pm.md` §2（代寫他人產出），也違 `stages/planning.md` §5「⛔ 不改寫執行者起草的內容」。處置＝列出問題交還執行者。
- **越界二**：執行者自己 `edit` 規格欄。⇒ 違 `stages/planning.md` §5「⛔ 不落欄」。
- **未知（逐欄明列）**：需求方核可的**形狀**在規格欄以外未定——`roles/pm.md` §3 只寫「改到規格欄時」用 `edit --ruling`；核可留言的 kind 值域（`core/ruling.md` 六值）未指定哪一個對應「規格核可」。本輪判**資料不足**，⛔ 不自造值。

### case_02_initial_revision — 建卡初填 vs 規劃修訂的適用期間

| 期間 | 起草 | 核可 | 落欄 | 依據逐字 |
|---|---|---|---|---|
| 建卡初填 | PM | —（需求方判升級） | PM | `core/card-schema.md` §2「PM（建卡初填落欄…）｜建卡」 |
| 規劃首次起草 | 執行者 | 需求方 | PM | `stages/planning.md` §4「③ 執行者起草規格欄…需求方核可後由 PM 以 `edit --ruling` 落欄」 |
| 核可後落欄 | — | 已核可 | PM | 同上 |
| 執行期修訂 | 執行者提清單 | 需求方 | PM | `stages/planning.md` §1「執行與審核階段要改規格時先交回到待確認再退回本階段」 |

- **正向**：`non_scope` 建卡由 PM 填；規劃階段執行者提修訂稿、需求方核可、PM 落欄；執行階段發現要改 ⇒ 交回待確認、退回規劃再走一次。
- **越界**：執行階段執行者直接 `edit --set resources=` 補漏列的交付檔。⇒ 違 `stages/implementation.md` F-執行-05（現逐字「⛔ 不自行改 `resources`」）與 `stages/planning.md` §1。正解＝隨交回單交 PM。
- **⛔ 不得推論**：「必填時點＝建卡」⛔ 不推出 PM 在建卡後喪失落欄權，也 ⛔ 不推出 PM 是此後唯一起草者（`core/conflict-resolution.md` §2）。
- **未知**：`feature`、`when`、`tier_basis` 等非規格欄在規劃階段的修訂程序未定（它們不使 `spec_version` +1，故不受 `stages/planning.md` §1 拘束）。判**資料不足**，⛔ 不外推規格欄的程序。

### case_10_append_rewrite — 檔案／既有條目／新增條目的內容所有權

| 對象 | 誰能做什麼 | 依據逐字 |
|---|---|---|
| `.wf/stages/<階段>.md` 的**新增條目** | PM 得追加 | `roles/pm.md` F-PM-12「維護 `.wf/stages/<階段>.md` 與卡面 `notes` 只加條目」；`modules/pitfalls-13/module.md` §1「同一 repo 既有解法的索引由 PM 寫進專案層 `.wf/stages/<階段>.md`」 |
| 同檔的**既有條目** | 原起草者所有；PM ⛔ 不改 | `roles/pm.md` F-PM-12「⛔ 不刪、⛔ 不改寫、⛔ 不加豁免鍵」；§2「列出問題交還產出者，只修自己的產出物；所有權按條目、⛔ 不按檔案」 |
| **檔案本身** | ⛔ 無所有權 | `core/conflict-resolution.md` §3 |

- **正向**：執行者在 T2 卡建了 `.wf/stages/執行.md`；PM 後來追加一條既有解法索引。⇒ 合法，且 ⛔ 不因「檔案是執行者建的」而被擋。
- **越界**：PM 把執行者寫的既有條目改寫成自己的措辭。⇒ 違 F-PM-12「⛔ 不改寫」。
- **越界二**：執行者主張「這檔是我建的」而擋掉 PM 的追加。⇒ 違 `core/conflict-resolution.md` §3「最初建檔者 ⛔ 不因此取得後續全部條目的所有權」。
- **實撞紀錄**：本卡核心痛點逐字第 ③ 項就是這個誤讀（「`.wf/stages/` 由執行者建後 PM 能不能動」）。
- **未知**：**卡面 `notes` 欄條目的刪除**——F-PM-12 對 PM 逐字「⛔ 不刪」，但 `core/card-schema.md` §2 對其他角色未寫刪除權；`core/verbs.md` §3 逐字只寫「專案與卡面只能加嚴：⛔ 不得刪除或改寫上游條目」（管的是上游條目，不是自己那層）。判**資料不足**，⛔ 不給唯一答案。

### case_12_note_permission — 查核者角色 × 候選留言義務的權限交集

| 對象 | 查核者能不能寫 | 依據逐字 |
|---|---|---|
| 本卡 `wf:note` 候選留言 | **能**（具名例外） | `roles/conduct-common.md` §2「發現候選注意事項即在該卡貼一則 `wf:note`（`origin`＝來源 finding 留言 URL）；⛔ 不直接寫進規則檔」；`roles/reviewer.md` §2 現逐字「具名例外＝本卡 `wf:note` 候選留言」 |
| 卡面 `notes` 欄（`edit --set notes+=`） | **不能** | `core/card-schema.md` §2 notes 列現逐字「（查核者除外，`roles/reviewer.md` §2）」 |
| 其他留言、狀態面 | **不能** | `roles/reviewer.md` §2「⛔ 不動狀態面」 |

- **正向**：查核者在裁決中開 finding，同時貼一則 `wf:note`，`origin` 指向該 finding 留言 URL。候選由 PM 或執行者日後以 `edit --set notes+=` 進卡面。
- **越界**：查核者自己跑 `edit --set notes+=` 把候選推進卡面。⇒ 被 `core/card-schema.md` §2 就地擋下。
- ⚠️ **⛔ 不外推**：#12 給的是**留言權**；卡面 `notes` 欄是 #11，另裁、方向相反。留言權 ⛔ 不推出卡面權（`core/conflict-resolution.md` §4「具名例外只在其來源的適用面內有效」）。
- **反測（移除例外來源）**：刪掉 `roles/conduct-common.md` §2 的貼 `wf:note` 義務 ⇒ `roles/reviewer.md` §2 的具名例外失去來源 ⇒ 回落「裁決留言以外⛔ 不寫任何東西」。結果翻面，證明例外不是憑空自證。

### case_31_full_comments — 研究全留言義務 × 查核者資訊範圍的交集

| 角色 | 義務 | 依據逐字 |
|---|---|---|
| 研究執行者 | 自行讀該卡全部留言 | `modules/research/module.md` F-research-03 現逐字「研究執行者研究前先讀該卡全部留言，⛔ 不只讀派工單」 |
| PM（派工者） | 派工與派審都附全部既有留言＋寫明資料截止點；截止後新增的補派 | 同檔 §1 現逐字「PM：派工與派審都附該卡全部既有留言並寫明資料截止點、截止後新增的相關留言補派」 |
| 查核者 | 只讀派工單附入的留言 | `roles/reviewer.md` §1「只讀派工單給的東西；無看板讀取權、看不到其他卡」 |

- **正向**：PM 派審時附 29 則留言與截止點「2026-09-10T05:31Z」；查核者依此讀，⛔ 不自行去 issue 抓。
- **越界**：查核者為履行 F-research-03 自行去看板讀留言。⇒ 違 `roles/reviewer.md` §1。
- **缺留言的處置**：附不齊時查核者在交回單記未驗（`kind`＝cannot，`core/return.md` 未驗清單段），**⛔ 不判完成**。「沒看到就是沒有」⛔ 不成立（`core/conflict-resolution.md` §5；`roles/executor.md` F-執行者-06「證不出來⛔ 不寫成沒有」）。
- **未知**：截止點的**格式**與補派的**時限**未定。判**資料不足**，逐欄列出，⛔ 不自造。

## 2 · 處置方法的合成案例（AC3）

以下五例用**合成條款**，⛔ 不依賴 repo 歷史（`stages/planning.md` F-規劃-09）。條款以 α／β 標記，所在檔以 X／Y 標記。每例都做**位置與順序反測**：把 α 與 β 的所在目錄互換、把兩條的先後互換，結果必須不變（`core/conflict-resolution.md` §7）。

### case_disjoint — 適用面不相交

- α（檔 X）：「執行階段由執行者跑 `p`。」β（檔 Y）：「審核階段由查核者跑 `p`。」
- 五元組：角色不同、期間（階段）不同 ⇒ 未全重疊。
- **結果＝相容。** 兩邊原文都 ⛔ 不改。推翻情境：出現一個同時屬執行與審核的期間。
- **反測**：α 移到 `core/`、β 移到 `stages/`，或把 β 寫在 α 之前 ⇒ 仍是相容。目錄與順序 ⛔ 未進判準。

### case_named_exception — 具名例外接回

- α（檔 X）：「角色 R ⛔ 不寫對象 O。」β（檔 Y）：「角色 R 發現 c 時寫 O 的子類 O₁。」α 已就地寫「（具名例外＝β）」。
- **結果＝相容。** ⛔ 不改文；例外只在 O₁ 內有效，O∖O₁ 仍禁。
- **反測（移除例外來源）**：刪除 β ⇒ α 的具名例外失去來源 ⇒ 回落禁令，結果變成「R ⛔ 不寫 O₁」。
- **反測（刪掉 α 的具名標註但保留 β）**：⇒ 變成 case_cross_scope（真衝突），⛔ 不因「β 較窄」自動勝出。

### case_cross_scope — 已裁衝突：就地修被限制的那一條

- α（檔 X）：「角色 R ⛔ 不做動作 a。」β（檔 Y）：「角色 R 在情境 c 做動作 a。」五元組全重疊，兩條都是絕對句。
- **結果＝真衝突。** 有權者裁定後，在**被限制的 α** 就地寫具名例外並回指 β；⛔ 不動 β、⛔ 不建立 X 高於 Y 的優先序、⛔ 不新增硬擋。
- **反測**：把 α 放進 `core/`、β 放進 `modules/`，或反過來 ⇒ 修文落點不變（永遠改被限制的那一條）。若某次裁定的理由是「α 在 `core/`」，該裁定無效（`core/conflict-resolution.md` §7）。

### case_unknown_scope — 資料不足

- α（檔 X）：「對象 O 的維護由 R₁ 負責。」β（檔 Y）：「R₂ 得更新 O。」兩條皆未寫**期間**，且「維護」「更新」未分起草／轉錄。
- **結果＝資料不足（不可判定）。** 逐欄列缺：期間未知、動作分解未知。⛔ 不給唯一權限答案、⛔ 不把空白讀成「R₂ 不限時皆可」。
- **反測**：補上「β 只在核可後逐字同步」一句 ⇒ 立刻變成 case_disjoint（相容）。差別只在資料，⛔ 不在位置。

### case_exception_collision — 競爭例外

- α（檔 X）：「R ⛔ 不寫 O（具名例外＝β）。」β（檔 Y）：「R 在 c₁ 寫 O。」γ（檔 Z）：「R 在 c₂ ⛔ 不寫 O，此條無例外。」情境同時滿足 c₁ 與 c₂。
- **結果＝競爭例外 ⇒ 回各自來源比適用面。** β 的例外只覆蓋 c₁；γ 是獨立禁令，其適用面含 c₁∩c₂ 而未接回 β ⇒ 兩者相斥。
- **仍相斥 ⇒ 判資料不足並上呈裁定**，⛔ 不由執行者選一邊、⛔ 不以「γ 較新」或「γ 較具體」判贏。
- **反測**：移除 γ ⇒ 回到 case_named_exception（相容）；移除 β ⇒ 回到單純禁令。

## 3 · 36 組逐條裁定（AC1、AC4）

`prior`＝母體 artifact 的原判讀（逐字取自該檔「#／判讀」欄）；`result`＝本卡裁定，值域＝相容／真衝突／資料不足／競爭例外（`core/conflict-resolution.md` §6）。`edit` 空陣列＝原文未動。

```json wf-002-rulings
[
{"id":1,"prior":"張力","result":"真衝突","dim":"動作","edit":["stages/planning.md §4","stages/planning.md §5","core/card-schema.md §2"],"falsifier":"若相容，PM 在本卡質詢紀錄落 acceptance 時不必自陳利益衝突；issuecomment-5613772414 逐字自陳了。"},
{"id":2,"prior":"待釐清","result":"真衝突","dim":"動作＋期間","edit":["core/card-schema.md §2"],"falsifier":"兩條同時為真時，non_scope／resources 在規劃階段沒有合法修訂者：card-schema 指 PM 建卡、planning §1 只准在規劃改規格。"},
{"id":3,"prior":"張力","result":"真衝突","dim":"動作","edit":["stages/planning.md §4"],"falsifier":"需求方裁定改規格欄後，若 edit 者是執行者，roles/pm.md §3「以 edit --ruling 落卡面」就沒有執行者。"},
{"id":4,"prior":"待釐清","result":"真衝突","dim":"動作","edit":["stages/implementation.md §6"],"falsifier":"若 F-執行-05 是落欄，執行階段就會使 spec_version +1，繞過 stages/planning.md §1「只在本階段改規格」。"},
{"id":5,"prior":"張力","result":"真衝突","dim":"動作","edit":["stages/planning.md §6"],"falsifier":"planning §5「⛔ 不改核心痛點」與 F-規劃-07「更正痛點」對同一角色、同一階段、同一對象，兩條都是絕對句。"},
{"id":6,"prior":"張力","result":"真衝突","dim":"對象","edit":["roles/pm.md §1","roles/pm.md §2"],"falsifier":"§1 要求交付前自審、§2 禁檢查自己的產出；PM 無法同時遵守兩條。"},
{"id":7,"prior":"待釐清","result":"真衝突","dim":"動作","edit":["roles/pm.md §3"],"falsifier":"抽查一條 note_responses 的 text 是否指向該 note，若算內容判斷，§1「⛔ 不判內容對錯」使 §3 的初審不可執行。"},
{"id":8,"prior":"待釐清","result":"真衝突","dim":"動作","edit":["modules/initiative/module.md §1"],"falsifier":"影響級別「前提失效」必須讀技術依據才判得出，與 roles/pm.md §2「只判流程，⛔ 不判內容」相斥。"},
{"id":9,"prior":"待釐清","result":"真衝突","dim":"動作","edit":["modules/initiative/module.md §1"],"falsifier":"「更新」若含重新撰寫，直接違反 roles/pm.md §2「⛔ 不代寫他人產出或判定」。"},
{"id":10,"prior":"待釐清","result":"真衝突","dim":"所有權粒度","edit":["roles/pm.md §2"],"falsifier":"本卡核心痛點逐字第 ③ 項（.wf/stages/ 由執行者建後 PM 能不能動）是已發生的實撞。"},
{"id":11,"prior":"張力","result":"真衝突","dim":"對象","edit":["core/card-schema.md §2"],"falsifier":"查核者若能 edit --set notes+=，被審卡面在審核期間被查核者改動且進 brief，與 roles/reviewer.md §2「⛔ 不動狀態面」相斥。"},
{"id":12,"prior":"張力","result":"真衝突","dim":"對象","edit":["roles/reviewer.md §2"],"falsifier":"移除 roles/conduct-common.md §2 的貼 wf:note 義務，具名例外即失去來源、回落禁令（case_12_note_permission 反測）。"},
{"id":13,"prior":"張力","result":"真衝突","dim":"對象","edit":["roles/conduct-common.md §1"],"falsifier":"卡 owner 為執行者時，PM 跑 move 就是「非所有者動卡」，與 roles/pm.md §1「只有 PM 跑 move」相斥。"},
{"id":14,"prior":"張力","result":"真衝突","dim":"動作","edit":["stages/review.md §5"],"falsifier":"無網路的 shell 下 reviewer §3 指定 PM 代貼，而 review §5 禁 PM 代轉錄；裁決無法送達。"},
{"id":15,"prior":"相容","result":"相容","dim":"作者≠傳送者","edit":[],"falsifier":"PM 代貼時同時填人填段即違 core/handoff.md；但 roles/requester.md §2「⛔ 不代填表單」已擋，本輪找不到有效反例。"},
{"id":16,"prior":"待釐清","result":"真衝突","dim":"動作","edit":["core/return.md"],"falsifier":"執行者交回單重列 status: resolved 而查核者尚未確認時，同一 finding 出現兩個權威值。"},
{"id":17,"prior":"相容","result":"相容","dim":"具名轉介","edit":[],"falsifier":"escalation 未啟用且需求方否決換人時若無出口即相斥；F-PM-01 逐字「需求方可否決」已給出口。"},
{"id":18,"prior":"待釐清","result":"真衝突","dim":"動作","edit":["roles/pm.md §4"],"falsifier":"若 F- 條目可當常設授權，任一 F- 都能繞過 §2 的「未經需求方明確指示⛔ 不開卡」。"},
{"id":19,"prior":"張力","result":"真衝突","dim":"級別","edit":["roles/pm.md §4"],"falsifier":"T0 卡 PM 兼執行者時，F-PM-02「一人一角」與 §2「T0／T1 可兼執行者」直接相斥。"},
{"id":20,"prior":"相容","result":"相容","dim":"階段＋級別","edit":[],"falsifier":"若 T0／T1 的執行階段也有自審禁令即相斥；roles/executor.md §2 逐字「⛔ 不自審（T2 以上）」已帶級別限定。"},
{"id":21,"prior":"相容","result":"相容","dim":"具名例外","edit":[],"falsifier":"四停下條件之一成立卻仍直行 merge 即相斥；stages/closeout.md §4 已列四條並要求停下請示。"},
{"id":22,"prior":"相容","result":"相容","dim":"工具副作用","edit":[],"falsifier":"若封存另有一個人要跑的 Project 動作即相斥；core/glossary.md「封存、撤銷、停止」逐字已定義封存＝終態時關 issue。本卡核心痛點 ② 的實撞是詞義誤讀，處置＝conflict-resolution §1，⛔ 不改原文。"},
{"id":23,"prior":"相容","result":"相容","dim":"動作","edit":[],"falsifier":"若「派填表」被讀成執行者落欄即相斥；同檔 §5「⛔ 不落欄」已擋。措辭可再收斂，但無有效反例 ⇒ ⛔ 不改。"},
{"id":24,"prior":"相容","result":"相容","dim":"對象","edit":[],"falsifier":"若「代填」含填自己負責的欄即相斥；core/card-schema.md §2 逐字把 service_goal 指給需求方本人。"},
{"id":25,"prior":"相容","result":"相容","dim":"動作","edit":[],"falsifier":"若初判與最終否決是同一動作即相斥；roles/requester.md §1 逐字「PM 判 R1 後保留否決」已分開。"},
{"id":26,"prior":"相容","result":"相容","dim":"動作","edit":[],"falsifier":"若「做質詢」含登記 URL 即相斥；core/card-schema.md §2 grilling 列逐字「PM（edit）」只管落欄。"},
{"id":27,"prior":"相容","result":"相容","dim":"具名例外","edit":[],"falsifier":"escalation 換人邊若同時是派工邊即相斥；modules/escalation/module.md §1 逐字「此邊⛔ 不是派工邊，--actor 不寫 owner」。"},
{"id":28,"prior":"待釐清","result":"真衝突","dim":"動作＋工具副作用","edit":["modules/resource-lock/module.md §1"],"falsifier":"手改 branch 後 review 依卡面 branch 取遠端頭（core/verbs.md §1 review 列逐字「executor＝卡面 branch 在遠端的分支頭」），會取到未經 move 登記的分支。"},
{"id":29,"prior":"相容","result":"相容","dim":"上下游分工","edit":[],"falsifier":"若 snapshot 的檔案產生也算 PM 的動作即相斥；core/verbs.md §1 snapshot 列逐字把「本機 JSON＋Markdown」列在動詞的寫欄。"},
{"id":30,"prior":"待釐清","result":"真衝突","dim":"對象","edit":["modules/stat-redline/module.md §1"],"falsifier":"反測結果「推翻」若指整體結論，modules/research/module.md §1「⛔ 不裁結論真值」使查核者無法填該欄；兩模組可同時啟用。"},
{"id":31,"prior":"待釐清","result":"真衝突","dim":"資訊範圍","edit":["modules/research/module.md §1","modules/research/module.md §2"],"falsifier":"查核者依 F-research-03 去讀「該卡全部留言」即違反 roles/reviewer.md §1「只讀派工單給的東西；無看板讀取權」。"},
{"id":32,"prior":"相容","result":"相容","dim":"對象","edit":[],"falsifier":"若「不寫任何東西」含拋棄式 worktree 的檔案寫入即相斥；roles/reviewer.md §2 逐字「需驗證時走密封探針或容器」已具名例外。註：reviewer §2 因 #12／#34 改寫，改寫方向與本組的相容判讀一致並使其更明確，⛔ 不是為本組改文。"},
{"id":33,"prior":"相容","result":"相容","dim":"允許≠義務","edit":[],"falsifier":"T0 且 parent 非空的卡上 PM 兼執行者時，觸發者與評估者合於一人 ⇒ 適用面確實重疊；但 roles/pm.md §2「可兼」是允許句、⛔ 不是絕對句，PM 不兼即同時滿足兩條（conflict-resolution §4）。若哪天寫成「T0／T1 應由 PM 兼」即翻面成真衝突。"},
{"id":34,"prior":"張力","result":"真衝突","dim":"工具副作用","edit":["roles/reviewer.md §2"],"falsifier":"查核者跑被指派的 review 時若投影欄不等就會重寫；遵守指派即違反紅線，兩者不可同時滿足。"},
{"id":35,"prior":"張力","result":"真衝突","dim":"表與契約不一致","edit":["core/verbs.md §1"],"falsifier":"notes 的寫欄逐字「無」，但卡面壞掉時它 rc=1 且貼一則 wf:reject 留言（本卡派工單逐字紀錄）；寫欄與 §2 拒收留痕不一致。"},
{"id":36,"prior":"相容","result":"相容","dim":"動作","edit":[],"falsifier":"若執行者回報的 SHA 與 CLI 取的權威來源被要求相同即相斥；兩者不符時的處置＝揭露，⛔ 不互相冒充。"}
]
```

### 3.1 · 分類清單（由上方區塊導出，⛔ 不手打）

產生工具與 artifact 同一 commit：工具就在本檔內，讀的也是本檔（自指命中明列，⛔ 不偷偷排除，`stages/implementation.md` F-執行-04）。

```
$ python3 - <<'PY'
import json,re,pathlib
p=pathlib.Path('docs/research/2026-09-10-responsibility-cases.md')
b=re.search(r'```json wf-002-rulings\n(.*?)\n```',p.read_text(),re.S).group(1)
r=json.loads(b)
ids=[x['id'] for x in r]
print('母體筆數',len(r),'| 編號集合',ids==list(range(1,37)),'| 重號',len(ids)!=len(set(ids)))
for k in ('相容','真衝突','資料不足','競爭例外'):
    s=[x['id'] for x in r if x['result']==k]
    print(f'{k}: n={len(s)} ids={s}')
print('改了原文的組:',[x['id'] for x in r if x['edit']])
print('原文未動的組:',[x['id'] for x in r if not x['edit']])
print('重點保留樣本 #15/17/21/25/27/36 全部 edit 空:',all(not x['edit'] for x in r if x['id'] in (15,17,21,25,27,36)))
print('無 falsifier 的組:',[x['id'] for x in r if not x.get('falsifier')])
import collections
print('修文落點次數:',dict(collections.Counter(e for x in r for e in x['edit'])))
PY
```

實跑輸出（2026-09-10，本檔當次內容）：

```
母體筆數 36 | 編號集合 True | 重號 False
相容: n=14 ids=[15, 17, 20, 21, 22, 23, 24, 25, 26, 27, 29, 32, 33, 36]
真衝突: n=22 ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 19, 28, 30, 31, 34, 35]
資料不足: n=0 ids=[]
競爭例外: n=0 ids=[]
改了原文的組: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 19, 28, 30, 31, 34, 35]
原文未動的組: [15, 17, 20, 21, 22, 23, 24, 25, 26, 27, 29, 32, 33, 36]
重點保留樣本 #15/17/21/25/27/36 全部 edit 空: True
無 falsifier 的組: []
修文落點次數: {'stages/planning.md §4': 2, 'stages/planning.md §5': 1, 'core/card-schema.md §2': 3, 'stages/implementation.md §6': 1, 'stages/planning.md §6': 1, 'roles/pm.md §1': 1, 'roles/pm.md §2': 2, 'roles/pm.md §3': 1, 'modules/initiative/module.md §1': 2, 'roles/reviewer.md §2': 2, 'roles/conduct-common.md §1': 1, 'stages/review.md §5': 1, 'core/return.md': 1, 'roles/pm.md §4': 2, 'modules/resource-lock/module.md §1': 1, 'modules/stat-redline/module.md §1': 1, 'modules/research/module.md §1': 1, 'modules/research/module.md §2': 1, 'core/verbs.md §1': 1}
```

### 3.2 · 分列（AC4）

- **爭議消解數＝22**（真衝突，逐組有修文落點）。
- **相容保留數＝14**（原文未動；含 AC4 指名的重點保留樣本 6 組）。
- ⛔ **這 14 組（含那 6 組）⛔ 不算 14 個或 6 個修復**；它們是「不破壞現況」的驗證，⛔ 不是消解。研究階段抽樣的 12 組比例 ⛔ 不外推到 36（`modules/research/module.md` F-research-01）。
- ⚠️ **本輪的 22／14 切分與母體 artifact 的 22（張力 11＋待釐清 11）／14（相容）恰好重合。** 這是逐組獨立裁定後的**結果**、⛔ 不是把原判讀抄過來當輸入：#33 一度被判成真衝突（T0 且 `parent` 非空的卡上 PM 兼執行者時適用面確實重疊），最後因「允許句 ⛔ 不是絕對句」回到相容，理由逐字寫在該組 `falsifier`。⛔ 不宣稱「兩份判讀互為驗證」——`roles/pm.md` F-PM-09 逐字「兩份不同作者的自評⛔ 不混為一份」。

## 4 · 修文影響面（AC5）

被改的責任與其已辨識讀取端；⛔ 不另建中央責任表，答案仍住原條文。

| 被改的責任 | 修文落點 | 已辨識讀取端（同向與反向引用） |
|---|---|---|
| `acceptance`／`verification` 誰起草、誰核可、誰落欄（#1、#3） | `stages/planning.md` §4、§5；`core/card-schema.md` §2 | `core/dispatch.md`（派工單「驗收條件」段取 `acceptance`）／`stages/planning.md` §2 離開條件／`roles/pm.md` §3 `edit --ruling`／`core/return.md` 逐條驗收段。**AC5 推翻條件已檢**：`stages/planning.md` §4 已 ⛔ 不再要求執行者 `edit` 規格欄 |
| `non_scope`／`resources` 的期間（#2、#4） | `core/card-schema.md` §2；`stages/implementation.md` §6 | `core/card-schema.md` 規格欄定義／`stages/planning.md` §1／`modules/resource-lock/module.md` §1 資源宣告文法／`core/dispatch.md` 非射程段 |
| 核心痛點的更正路徑（#5） | `stages/planning.md` §6 | `stages/planning.md` §5「⛔ 不改核心痛點」／`roles/pm.md` §2「⛔ 不改需求方原文」／`core/card-schema.md` §2 core_pain 列 |
| PM 自審的效力（#6）、抽查的界線（#7） | `roles/pm.md` §1、§2、§3 | `roles/reviewer.md` §1（R3／R4 仍由查核者）／`core/tiers.md` §1 查核者獨立性欄 |
| PM 對子卡的影響判定與規格同步（#8、#9） | `modules/initiative/module.md` §1 | 同檔 F-initiative-02（級別仍由 PM 判）／`roles/pm.md` §2 |
| 內容所有權粒度（#10） | `roles/pm.md` §2 | 同檔 F-PM-12／`modules/pitfalls-13/module.md` §1／`core/verbs.md` §3「專案與卡面只能加嚴」 |
| 查核者的卡面 `notes` 權（#11）與留言權（#12） | `core/card-schema.md` §2；`roles/reviewer.md` §2 | `roles/conduct-common.md` §2（例外來源）／`core/verbs.md` §3 候選列印／`core/card-schema.md` §4 `wf-note` schema |
| `owner` 與 PM 操作權的分離（#13） | `roles/conduct-common.md` §1 | `roles/pm.md` §1／`core/glossary.md`「owner」「狀態面」 |
| PM 逐字代貼裁決（#14） | `stages/review.md` §5 | `roles/reviewer.md` §3／`core/naming.md` §3 首行表／`roles/conduct-common.md` §2 |
| finding `status` 的權威值（#16） | `core/return.md` | `core/glossary.md`「finding 狀態」／`roles/reviewer.md` §1／`core/verbs.md` §1 review 列撞號 |
| F-PM-11 的開卡授權（#18）、F-PM-02 的級別範圍（#19） | `roles/pm.md` §4 | `roles/pm.md` §2／`core/tiers.md` §1、§3 |
| `branch` 與 `worktree` 的登記者（#28） | `modules/resource-lock/module.md` §1 | `core/card-schema.md` §2（`branch`＝CLI 寫）／`core/naming.md` §2／`core/verbs.md` §1 review 列／同模組 F-resource-lock-01 |
| 反測「推翻」的對象（#30） | `modules/stat-redline/module.md` §1 | `modules/research/module.md` §1／`core/return.md` `$defs` 的 `adversarial_tests` |
| 研究全留言義務的履行者與供給者（#31） | `modules/research/module.md` §1、§2 | `roles/reviewer.md` §1／`core/dispatch.md`（派工單段）／`core/return.md` 未驗清單段 |
| 查核者跑 `review` 的工具副作用（#34） | `roles/reviewer.md` §2 | `core/verbs.md` §2 對帳條款／`stages/review.md` §4 |
| 動詞「寫」欄的讀法（#35） | `core/verbs.md` §1 表下 | `core/verbs.md` §2 拒收留痕與對帳／`core/card-schema.md` §5 投影欄 |
| 方法的入口與詞彙 | `roles/conduct-common.md` §1；`core/glossary.md` | `core/conflict-resolution.md` 全檔（唯一居所） |

**⛔ 不複製責任真源的自證**：`core/conflict-resolution.md` 的 `non_scope` 逐字「⛔ 不寫任何一項責任的答案（住各原條文）」；全檔無「誰填」對照表，每個具體答案都是回指原條文。

## 5 · 本檔的限制

- 36 組以外 ⛔ 不宣稱；覆蓋率沿用母體 artifact 的逐字「⛔ 覆蓋率未知」。
- 五個邊界定義**未經需求方核可**（§0）。核可前 ⛔ 不得引為既成通則。
- 修文只改規則文字，⛔ 未改 `cli/src`；規則文字與 CLI 實際行為是否一致本輪 ⛔ 未驗（承接卡見卡面 `non_scope`，卡ID 依 `issuecomment-5614447768` 的改號映射解讀）。
- 「相容」14 組是**本輪找不到有效反例**，⛔ 不是「證明不可能有反例」；查核者提出反例且成立時就地改判，依母體 artifact 逐字「⛔ 不算新增第 37 組、⛔ 不算擴射程」。
