# 新框架骨架（2026-09-04）

> 自舉第二份文件（決策 10）。用途：定下**目錄、每個檔的固定節與行數上限、狀態機、卡面 schema、動詞、交接文件、模組宣告格式、命名規則**，讓之後「填規則」時每個檔的密度一致、每條空洞有落點。
> 輸入：`REBUILD-DECISIONS-2026-09-04.md`、`extract/00-consolidated.md`、`extract/07-conflicts.md`。引用格式沿用 `01#19`、`H7`、`S4`、`K2`、`C3`。
> ⛔ 本檔不寫規則正文；規則正文在「填規則」步驟寫進各檔。本檔經 Codex 跨實體審＋需求方 sign-off 後生效。

## 一 · 目錄樹

```
README.md                  L0 入口：一分鐘心智模型＋查詢指令；⛔ 不列會變的東西（04#158）
ADOPTION.md                L1 導入：新專案接上框架的步驟；來源舊 ADOPTION 五行
.github/ISSUE_TEMPLATE/
  list-intake.yml          待審清單收件表單：預填一個 `json wf-intake` 區塊，四欄 source／observation／dedupe（關鍵字＋命中號）／repo；`open` 只讀該區塊（決策 1），散文欄給人看
core/                      定義檔（C8）。只放定義與機械語意，⛔ 不放理由
  state-machine.md         階段、核心狀態值域、核心轉移表、模組 delta 合成規則
  tiers.md                 T0–T4 表、紅線域、能力層級判準、單向門、缺陷級別套用
  card-schema.md           卡面 fenced JSON 欄位集（JSON Schema 逐字）
  verbs.md                 七動詞：open / move / edit / notes / brief / review / snapshot
  handoff.md               三份交接文件的段落表＋交回單 JSON schema
  naming.md                卡ID、分支、檔名、留言標頭的命名規則
  params.md                設計值參數表（§十二），一列一參數：名、種子值、用在哪
  platform.md              平台委託五條 P1–P5（§三）：每條＝規則一句＋執行 artifact（ruleset 項目或 CI job 檔名）；ruleset 與 CI 只是它的執行面
  glossary.md              通用語言（Ubiquitous Language）：每個詞一行——詞、一句定義、⛔ 不是什麼、禁用同義詞；消費者＝規則檔、CLI enum、審核提示（§十八）
stages/                    一階段一檔；研究、部署、維護三個可跳過的階段住模組
  requirement.md  planning.md  implementation.md  review.md  closeout.md
roles/                     一角色一檔＋共用一檔
  requester.md  pm.md  executor.md  reviewer.md  conduct-common.md
modules/                   每模組一目錄；module.md 開頭是宣告區塊（§九）
  research/  resource-lock/  escalation/  deploy/  maintenance/
  pitfalls-13/  identity/  snapshot/  db-contract/  initiative/  stat-redline/
cli/                       新 CLI（名稱 `wf`，與凍結的 `wfcli` 區分）
archive/                   舊 canonical、stage-rules、templates、docs、cli、issues；唯讀
docs/research/             決策紀錄、萃取、骨架（本檔）
```

採用專案側（不在本 repo）：
```
.wf/modules.json           schema＝{modules: [{name, params}], merge_method: squash|merge（C3）, areas: [卡ID 前綴枚舉]（§十）}
.wf/stages/<階段>.md        專案層注意事項 P-<階段>-NN（只能加）
.wf/tiers.md               專案層加嚴（只能往上綁）
.wf/contracts/             模組要求的專案填空（DATABASE_CONTRACT 等）；CLI 只讀其中 `json wf-contract` 區塊（`side_effects` 陣列＝副作用入口）
```

## 二 · 每個檔的固定節與行數上限

密度不均是上一版的病（01 空洞、03 空洞）。每種檔固定節次、固定上限（上限＝天花板，不是配額）。理由與來歷的形狀＝`→ archive/…` 連結（決策 9）；萃取稿 `docs/research/extract/` 是填規則的輸入，填完後整目錄移入 `archive/research/`，規則正文⛔ 不引用它。

| 檔種 | 固定節（順序不可換） | 上限 |
|---|---|---|
| 階段檔 | 1 目標與產出 · 2 進入／離開條件 · 3 狀態 delta（引用 core） · 4 階段內迴圈（①–⑤ 在本階段的形狀） · 5 各角色做／⛔ 不做 · 6 注意事項 `F-<階段>-NN` | 60 行 |
| 角色檔 | 1 職責 · 2 紅線 · 3 動作前自檢 · 4 注意事項 `F-<角色>-NN` | 60 行 |
| conduct-common.md | 1 操作紀律（實跑、fetch、不截斷、rc、負控、逐字、多居所、驗原件） · 2 書寫紀律（數字帶日期、不寫行號、引用逐字） | 40 行 |
| core 各檔 | 依檔（§三–§八、§十八） | 120 行 |
| module.md | 0 宣告區塊（§九） · 1 條文 · 2 該模組加的注意事項 | 80 行 |
| README | 1 心智模型（≤12 行） · 2 角色一句話 · 3 查詢指令 | 40 行 |
| ADOPTION | 1 repo 前置（ruleset、merge_method） · 2 `.wf/modules.json` 種子 · 3 Project 五欄 · 4 第一張卡 | 60 行 |

**每個規則檔、模組檔、core 檔統一 frontmatter 四欄**（沿舊 stage-rules 與卡片簡介的 skill 式檔頭，決策 9）：`name`、`when`（適用時機一句）、`non_scope`（⛔ 不是什麼一句）、`last_confirmed`（日期，§十一 規則文件自身過期）。`brief` 每段首行 `[來源: …]` 印該檔 `name`＋`when`；`notes` 印清單時同。

規則條文的形狀：一條＝一句祈使句、無理由子句；一條可含以分號接的條件、例外、指向子句，⛔ 不接第二條獨立規則（需求方 2026-09-05 甲案）；符號集＝⚠️／⭐／⛔；數字帶日期。書寫紀律的條文住 `roles/conduct-common.md` §書寫。

## 三 · 核心迴圈與角色（定案摘要）

**第零條（README 心智模型第一行）**：CLI 提供資訊清單，AI 判斷；CLI 只確認清單有沒有填，⛔ 不做內容判讀。舊 ROADMAP 目標 1「有機械執行者擋下才算達成」廢止。目標的排序與關係住決策紀錄第零條，本檔不重述。

硬擋現況（決策紀錄「硬擋收縮」；重判歷史與降級理由見 `REBUILD-SKELETON-REVIEW-LOG.md`）。P1–P5 的條文居所＝`core/platform.md`，GitHub ruleset 與 CI job 為其執行 artifact 並在檔內指回；D1–D4 的條文居所＝`core/verbs.md` §寫入契約：

| # | 硬擋 | 執行者 |
|---|---|---|
| P1 | main ruleset 禁改史禁刪 | GitHub ruleset |
| P2 | T2 以上走分支＋獨立查核；執行者不 merge | ruleset required check＋PR |
| P3 | 合併方式＝專案層 `merge_method`，由平台設定強制 | repo 設定＋ruleset（C3） |
| P4 | secrets 不進 git | CI secret scanner（補充裁定 H4） |
| P5 | commit trailer 鍵與連續區塊 | CI |
| D1 | 轉移在合成表內；終態無出邊；無自由文字狀態 | CLI `move` |
| D2 | `open` 只從清單項或撤銷卡（§十八），兩者皆不在板上 | CLI `open` |
| D3 | JSON 合法、鍵集合封閉；`card_id`／`source_issue` 建卡後不可改；解析失敗整卡拒；寫後回讀 | CLI 全動詞 |
| D4 | `--source-sha` 在遠端存在；`--ruling` URL 存在；`parent` 指到板上存在的卡 | CLI `move`／`edit`／`open`；URL 存在但無 `wf-return`／`wf-ruling` 區塊＝印 |

判準：**CLI 拒的範圍＝「寫壞資料」與「指向不存在的東西」（＝決策紀錄的資料有效性、寫入順序、平台委託三類）；其餘＝印，交 AI 或人判。** 降為印的比對：HEAD 與 `source_sha`、`merge-tree` 衝突、交回單欄位一致性、鏈深、終態前 PR 與分支狀態、裁定留言作者；降為注意事項的：一人一角、跨家族。

- 四角色：需求方、PM、執行者、查核者（決策 5）。第二 PM、人工查核不存在（C4）。
- 每階段五步：① `notes` 印一份清單（四個來源：框架核心 → 已啟用模組 → 專案層 → 卡面，決策 11 逐字順序）② PM `brief` 派 ③ 交回 ④ PM 對完整性＋判 R1 R2 ⑤ `move`（S8、S9）。
- 查核者判 R3 R4；查核者的裁決同時覆蓋派工單（attribution: coordinator／planner）（C4）。
- 裁決與裁定＝GitHub 留言，誰貼都可以；`--ruling` 的收法見 §七 `move`（C12–C14）。

## 四 · `core/state-machine.md` 的內容

**階段**：需求 → 研究* → 規劃* → 執行 → 審核 → 部署* → 維護* → 結案。星號＝可跳過；研究、部署、維護是卡級模組（唯一啟用條件＝該卡 `stage_plan` 含該階段；事實來源＝卡面 JSON），未啟用時該卡的階段序列裡沒有它（S3、C6）；規劃的跳過由級別決定（T0／T1），仍是核心。

**核心狀態值**（C6）：待辦／進行中／待確認／完成／退回＋正交 阻塞。階段 delta 可加可減：結案階段加 停止（終態，S6）、減 待辦／進行中；完成 只在結案有值（`only_in_stage`；填規則第 1 步為可達性驗收所定）。模組可加：`research` 加 不可判定；`escalation` 加 升級；`maintenance` 加 運行中。模組加狀態時，其 `transitions.add` 必同時給進邊與至少一條可達結案的出邊；三個模組的 delta 釘死如下（條文住各模組 `module.md`）：

| 模組 | add（from → to；條件） |
|---|---|
| research | 研究／待確認 → 研究／不可判定（交回單 verdict＝不可判定）；研究／不可判定 → 需求／待辦（重述問題）；研究／不可判定 → 結案／待確認（以不可判定作結案報告） |
| escalation | 任一階段（結案除外）／退回 → 同階段／升級（同 iteration 第 N 次退回，N＝`modules.json` 該模組 `params.escalate_after`，種子 3）；升級 → 同階段／進行中（換人或換級再派，`--ruling` 缺即印）；升級 → 結案／待確認（需求方裁定收尾） |
| maintenance | 維護／待辦 → 維護／運行中（上線）；維護／運行中 → 維護／進行中（事件處理）；維護／運行中 → 結案／待確認（結束維護） |


**核心轉移表**（每列＝一條允許的邊；`move` 只接受表內轉移，D1）：

| from | to | 條件 |
|---|---|---|
| 需求／待確認 | 研究或規劃或執行／待辦 | 依階段計畫的下一階段；T2+ 而 `stage_plan` 缺規劃＝印（S3，PM 判） |
| 需求／待確認 | 清單（撤銷） | 卡ID 保留、iteration 延續（S6、C5）；無 `--ruling` 印提示；JSON 留在 issue body |
| 撤銷卡（不在板、帶 `wf-card`） | 需求／待辦 | `open` 復板，沿用 `card_id`／`iteration`（§十八） |
| 任一階段（結案除外）／待辦 | 同階段／進行中 | 派工 |
| 任一階段（結案除外）／進行中 | 同階段／待確認 | 交回 |
| 任一階段（結案除外）／待確認 | 下一階段／待辦 | ⑤ 過；審核階段 `--ruling` 種類＝`wf-return`（缺即印）；下一階段為結案時走「最後一個階段」列 |
| 任一階段／待確認 | 同階段／退回 | ⑤ 不過（R2–R4）；審核階段 `--ruling` 種類＝`wf-return`，結案階段＝`wf-ruling`（缺即印） |
| 任一階段／待確認 | 規劃或需求／退回 | ⑤ R1 不過（S10）；`stage_plan` 含規劃→規劃／退回，否則→需求／退回（合成表按該卡 `stage_plan` 展開，不存在的階段沒有邊） |
| 任一階段（結案除外）／退回 | 同階段／進行中 | 再派；進執行時 iteration +1、`source_sha` 清為 null（S7）；同一 iteration 第 3 次退回的預設處置＝換人，需求方可否決（PM 減重 4）；條文住 `roles/pm.md` §4 |
| 任一非終態（待辦／進行中／待確認／退回） | 阻塞 | 寫 `blocked.from`；`--ruling` 種類＝`wf-ruling` kind=block，缺留言或缺鍵皆印 |
| 阻塞 | from（必為非終態） | 解除 |
| 最後一個階段／待確認 | 結案／待確認 | 結案報告 |
| 結案／退回 | 結案／待確認 | 補驗後重交結案報告 |
| 結案／待確認 | 完成 或 停止（結案階段 delta） | 完成：印 PR 與分支狀態；停止：`--ruling` 種類＝`wf-ruling` kind=stop（缺留言或缺鍵皆印）；兩者皆封存 |

**模組 delta 格式**：模組宣告區塊裡 `transitions.add` 與 `transitions.remove` 各列若干 `{from, to, condition}`，可帶機械鍵 `if`（`plan_has:<階段>`／`plan_lacks:<階段>`，展開時裁邊）；合成＝核心 ∪ add − remove；CI 跑可達性測試（01#57 保留為測試要求），測試矩陣隨被測物累加：第 1 步只有「無模組」；第 4 步每個帶 delta 的模組進 repo 的同一 PR 加「該模組單獨啟用」，最後一個模組的 PR 再加「全部啟用」；每個案例涵蓋 `stage_plan` 的全部合法值；測試斷言兩件：每個非終態有出邊且可達結案；完成與停止的出邊集合為空。

## 五 · `core/tiers.md` 的內容

固定節與各節來源（條文在填規則時寫）：
- §級別表：五列 × 四欄——級別／最低閘門（直推、分支、查核、跨家族或 sign-off）／規劃階段是否必跑／查核者獨立性（來源 01#66–68）。
- §判準：三軸（敏感面／可復原性／影響面）與合成方式（來源 03#44）。
- §紅線域：清單（來源 01#64、02#63）；`db_scope` 與 T4 的連動（C9）；T4 查核的獨立性條件（注意事項）。
- §單向門：升與降的形狀（來源 03#31、C12）。
- §缺陷套用表（來源 03#45）。
- §能力層級：三值與判準（來源 03#49）。
- §專案層：加嚴介面（來源 03#48；數字未定，tier-rules §四）。

## 六 · `core/card-schema.md` 的內容

卡面＝Issue body 的一個 fenced JSON 區塊（`json wf-card`）＋人讀散文段。CLI 只讀寫 JSON（決策 1）；讀留言時只讀三種 fenced JSON 區塊（`json wf-return`、`json wf-ruling`、`json wf-note`），散文與首行不在讀取範圍；CLI 自己寫的留言（`wf:move`／`wf:edit`／`wf:reject`）是純散文、只寫不讀；`wf:log` 人貼（§十），iteration 住卡面 JSON；退回次數不由核心 CLI 數（escalation 模組的事）。

| 欄 | 型別 | 誰填 | 何時必填（`open` 印缺欄） | 誰讀 |
|---|---|---|---|---|
| schema_version | int | CLI | 建卡 | CLI |
| card_id | string | CLI 配（naming；建後不可改） | 建卡 | 全部 |
| source_issue | int | CLI（建後不可改） | 建卡 | CLI |
| feature | string | PM | 建卡 | brief |
| core_pain | string | CLI 從清單 issue 的 `wf-intake` 逐字帶入 | 建卡 | 所有交接文件 |
| non_scope | string[] | PM | 建卡 | brief、R2 |
| stage_plan | enum[]（8 階段名逐字；必為 §四階段序列的子序列、不重複；必含 需求、執行、審核、結案；不合＝D3 拒） | PM | 建卡 | move |
| acceptance | string[] ≥1 | PM | 離開規劃前 | brief、R3 |
| verification | {item, who}[] | PM | 離開規劃前 | brief |
| list_convergence | int[]（清單 issue 號） | PM | 建卡 | 結案核對 |
| service_goal | string | 需求方 | 建卡 | R1 |
| parent | card_id | PM（`open --parent` 或 `edit --set parent=`；兩者皆算鏈深並印） | 有父卡時 | 鏈深（印）、initiative 模組 |
| blocked | {from: 狀態, ruling: 留言 URL} 或 null | CLI（`move --to 阻塞` 寫，解除時清 null） | — | brief、Project 狀態欄 |
| grilling | 留言 URL 或 null（T4 質詢紀錄所在的 `wf:log` 留言；00 §四「T4 卡附 grilling 質詢紀錄」） | PM（`edit --set grilling=`） | T4 離開規劃前（缺＝`move` 印） | brief、裁定單 |
| tier | enum T0–T4 | PM | 建卡 | move、tiers |
| tier_basis | {sensitive: enum[], recoverable: enum, blast: enum}（值域見表下） | PM 或執行 AI 選值 | 建卡 | 印；stat-redline 模組看 `statistics ∈ sensitive` |
| exec_capability / review_capability | enum＋reason | PM | 建卡 | brief |
| db_scope | enum none/read/write/schema/data-migration | PM | 建卡 | tiers |
| resources | string[]（文法住 db-contract／resource-lock） | PM | 建卡 | resource-lock 模組 |
| when | string（卡片簡介的「適用時機」一句；非射程已在 `non_scope`） | PM | 建卡 | 清單搜尋、派工單卡與身分段 |
| spec_version | int | CLI（`edit` 改 `acceptance`／`verification`／`non_scope`／`resources` 任一欄時自動 +1，C11） | — | 派工單、initiative |
| owner | {role: enum（requester／pm／executor／reviewer）, actor: string} | CLI（move `--actor`） | — | brief、Project owner 欄 |
| branch | string | CLI（move 到進行中時寫） | — | brief、D4 |
| source_sha | string（40 hex）或 null；恆屬當前 `iteration`（`move` 進執行時 iteration +1 並清為 null） | CLI（`move --source-sha` 於交回時寫；須在遠端存在，D4）；`edit` 可改（C11） | 交回時 | `brief --for reviewer`／`review`（比對並印）、裁定單 |
| iteration | int | CLI | — | brief |
| notes | {id: `T-<階段>-NN`, text, origin: 留言 URL}[]（卡面 `notes` 欄，T- 加嚴層級） | 任何有 shell 的角色經 `edit --set notes+=`，來源為 `wf:note` 留言（§十二） | 否 | notes、brief |

模組 `adds.fields` 的型別唯一居所＝`core/card-schema.md` 的 `$defs/module_fields/<模組名>`，啟用時併入 properties（填規則第 1 步定）。`tier_basis` 值域：sensitive 多選＝public_contract／security／payment／data_write／migration／production／rules／statistics（＝`core/tiers.md` §紅線域）；recoverable＝reversible／rollback_only／irreversible；blast＝file／module／repo／cross_repo。

未定義鍵 ⇒ fail-closed（D3）。`schema_version` 的升版判準與舊版卡遷移方式住 `core/card-schema.md` §版本（來源：P1-30；形狀＝升版觸發條件一句、遷移路徑一句）。Project 欄位只放 `階段`、`狀態`、`級別`、`owner`（TEXT，`role:actor`）、`卡ID` 五個投影欄，全由 CLI 回寫；逐欄 `max_bytes` 與寫入順序見 §十一（05 新洞）。

## 七 · `core/verbs.md` 的內容

| 動詞 | 輸入 | 硬擋（rc≠0 並寫一則拒收留言，C13） | 印（rc=0） | 寫 |
|---|---|---|---|---|
| `open <issue> [--parent <card_id>]` | 清單 issue 號；父卡 ID（PM 的結構化輸入，⛔ 不在 intake 四欄）。issue body 已有 `wf-card` 區塊＝撤銷卡復板：沿用 `card_id`／`iteration` | 不是清單項也不是撤銷卡、已在板上、JSON 鍵不合法、`--parent` 不存在（D2、D3、D4；全部在首次遠端寫入前） | 缺欄清單（§六必填時點＝建卡的欄）、鏈深（沿父鏈算，>2 印「上限 2」）、清單留言數與未讀警示（K7） | 建卡 JSON、加進 Project、配卡ID |
| `move <card> --to <階段/狀態> [--actor A] [--source-sha SHA] [--ruling URL]` | 目標、（派工與派審時）actor、（交回時）source_sha、裁定 URL | 卡面 JSON 解析失敗、轉移不在合成表內、終態出邊、`--source-sha` 不在遠端、已給的 `--ruling` URL 不存在（D3、D1、D4） | 進終態前 PR 與分支狀態（印）、缺 `--ruling`（撤銷、阻塞、停止、級別下修）、裁定留言無 `wf-return`／`wf-ruling` 區塊、裁定留言作者 login、`wf-ruling` 依 kind 的必要鍵缺（block 四鍵、stop 三鍵，§八）、離開規劃時 `acceptance` 或 `verification` 為空、T4 而 `grilling` 為 null | Project 欄、JSON owner／branch／iteration／source_sha（進執行時 iteration +1 且 source_sha=null；交回時寫 `--source-sha`）、轉移記錄留言（純散文） |
| `edit <card> --set <欄>=<值> [--ruling URL]` | 欄與值 | JSON 不合法、改 `card_id` 或 `source_issue`、`--set parent=` 指到不存在的卡、`--set source_sha=` 不在遠端、已給的 `--ruling` URL 不存在（D3、D4、C11）；鏈深沿父鏈算後只印 | 無裁定連結、審核期修改 | JSON；`edit` 留言；規格欄（C11 四欄）變動時 spec_version +1；審核期另貼 `edit during review` 留言（C11） |
| `notes <card> [--stage]` | — | 卡面 JSON 解析失敗（D3） | 一份編號清單，四個來源（框架核心 F- → 已啟用模組 F- → 專案層 P- → 卡面 `notes` 欄 T-，決策 11 順序）＋ pitfalls-13 樣板（若啟用） | 無 |
| `brief <card> --for executor\|reviewer\|closeout` | 角色 | 卡面 JSON 解析失敗（D3） | `--for reviewer`：分支 HEAD ≠ `source_sha`、`source_sha` 未 push、`merge-tree` 有衝突（印）；`--for closeout`：merge SHA 是否 main 祖先、CI 狀態；缺人填段；每段來源標記帶該檔 `last_confirmed` | 無（stdout；PM 貼進留言）。每段首行 `[來源: <來源>/<檔>#<節> · confirmed <日期>]` |
| `review <card> --file <交回單.json> --role executor\|reviewer` | 本機交回單 JSON | schema 不合法（D3） | 交回單欄位不一致（PM 判）、缺段（未驗清單、self_run、注意事項回應） | 以 `json wf-return` 區塊貼成該卡一則留言，⛔ 不動狀態、⛔ 不另產生其他留言 |
| `snapshot` | — | 任一卡 JSON 解析失敗（D3） | — | 本機 JSON＋Markdown |

`core/verbs.md` 另有固定節「寫入契約」，內容來源＝K2（檢查先於首次遠端寫入、寫後回讀）、K3／C13（拒收留痕）、決策 1（只讀 fenced JSON）、第零條（不產生統計數字）；條文在填規則步驟寫，本檔只定節名與來源。

## 八 · `core/handoff.md` 的內容（04 §範本欄位）

| 文件 | 誰→誰 | CLI 填 | 人填 |
|---|---|---|---|
| 派工單（每段首行 `[來源: …]`，決策 11） | PM→執行者或查核者 | 卡與身分、核心痛點、驗收逐條、非射程、merge-base SHA、前輪 findings、能力層級建議、注意事項編號清單、副作用入口清單 | 寫入授權、唯讀範圍、實際模型與偏離理由、未驗項（三分類）、本文件落差 |
| 交回單 | 執行者或查核者→PM | 卡與身分、AC 條文、commit 清單、改動面、finding_id | self_run、逐 AC 做法／證據／falsifier、失誤登記或 findings 八欄、**未驗清單（三分類：驗不了／沒去驗／刻意不驗，各附原因）**、注意事項回應、範圍外發現、`review_result`／`core_pain_resolved`（查核者） |
| 裁定單 | PM→需求方 | 事件序（以 `wf-return` 留言的時間序推，CLI 不讀散文留言）、各輪退回理由與 findings（讀 `wf-return`）、merge SHA、CI、四停下條件前三項 | 類別（升級／停止／撤銷／級別變更／結案確認／其他）、四選一各值證據、復活條件、翻案把手、被繞過的閘門 |

交回單各段的必填性依級別分兩檔：T0／T1 只要 `self_run` 與逐 AC 證據；T2 以上全段（形狀，流程順暢；來源 03#24、決策第零條三目標）。`brief --for executor` 與 `--for reviewer` 同時印一份交回單 JSON 樣板（id、AC 條文、注意事項 id 預填），人只填判斷欄。

交回單 JSON schema＝舊 review-prompt §5 加 `role` 欄與 `unverified: [{item, kind, reason}]`（`kind` 封閉值域 `cannot`／`skipped`／`deferred`，`reason` 非空）；同一 schema 執行者與查核者共用。**注意事項回應的三值唯一定義居所＝本檔**：`note_responses: [{id, value, text}]`，`value` 封閉值域 `followed`／`not_applicable`／`found`（人讀顯示 已遵循／不適用／發現），`not_applicable` 與 `found` 的 `text` 非空；§十二與各階段檔只引用不複製；CLI 只查 id 是否覆蓋 `notes` 印出的清單、value 在值域、text 非空，⛔ 不判內容。

`wf-ruling` JSON schema（唯一居所＝本檔）：`{kind, reason, waiting_on?, unblock_condition?, revive_condition?, reversal_handle?}`；`kind` 封閉值域 `block`／`stop`／`withdraw`／`tier_change`／`signoff`／`other`；依 kind 的必要鍵：block＝reason、waiting_on、unblock_condition（加 CLI 寫的 `blocked.from` 共四欄）；stop＝reason、revive_condition、reversal_handle（三欄）；其餘 kind 只要 reason。CLI 只驗鍵存在與型別（缺＝印），內容交人判。裁定單的「復活條件」「翻案把手」即 stop 的後兩鍵。

留言的形狀＝append-only 事件（一事件一則、無可編輯日誌留言；來源：決議 §五、P1-33），條文住 `core/verbs.md` §寫入契約。派工單完整性由收件的查核者判（C4）；裁定單完整性由需求方 ④ 判。

## 九 · 模組宣告格式與清單

每個 `modules/<name>/module.md` 開頭一個 `yaml wf-module` 區塊：

```yaml
name: resource-lock
enable_when: 派工當下板上狀態＝進行中且 owner 不同的卡 ≥1 張  # 決策 6「同時 ≥2 執行者」；事實來源＝Project 投影欄
adds:
  fields: [worktree, lease_expires_at]
  stages: []
  states: []
  transitions: {add: [], remove: []}
  flags: []            # 模組只能宣告旗標；動詞集合固定於 core/verbs.md（決議 §七：動詞新增須需求方裁定）
  notes: [F-resource-01, F-resource-02]
  handoff_sections: [資源宣告逐條]
project_inputs: [.wf/contracts/CONTROL_PLANE.md]
```

`.wf/modules.json` 列啟用的模組名與參數；`notes`／`brief`／`move` 依它合成清單、段落、轉移表與狀態值域。模組未啟用＝上面每一項都不存在。

| 模組 | 唯一啟用條件（一個 predicate） | 事實來源 | 收的萃取列 |
|---|---|---|---|
| research | 卡的 `stage_plan` 含研究 | 卡面 JSON | 03#50–60 |
| deploy | 卡的 `stage_plan` 含部署 | 卡面 JSON | 00 §六 |
| maintenance | 卡的 `stage_plan` 含維護（PM 何時該列維護，例如交付物是排程、爬蟲、告警，是 `stages/requirement.md` 的注意事項，⛔ 不是條件） | 卡面 JSON | 00 §六 |
| initiative | 卡的 `parent` 非空 | 卡面 JSON | 02#10、04#44 117–120 |
| stat-redline | `statistics ∈ tier_basis.sensitive`（集合成員比對，值域封閉） | 卡面 JSON | 04#135–138、03#57 |
| escalation | 專案 `.wf/modules.json` 列出（計數由 `move` 在該 iteration 內做） | modules.json | 00 §六；05 空洞 7 |
| resource-lock | 同時 ≥2 執行者：`move` 派工當下，板上狀態＝進行中且 `owner.actor` 與本卡不同的卡 ≥1 張（決策 6） | Project 投影欄 狀態＋owner（`modules.json` 只放參數，如 lease TTL，⛔ 不是條件） | 00 §六 |
| pitfalls-13 | 專案 `.wf/modules.json` 列出 | modules.json | 00 §六 |
| identity | 專案 `.wf/modules.json` 列出（多實體共用同一帳號時該列） | modules.json | 00 §六 |
| snapshot | 專案 `.wf/modules.json` 列出（狀態面在 GitHub 時該列） | modules.json | 00 §六 |
| db-contract | 專案 `.wf/modules.json` 列出（有 DB 時該列）；已啟用而 `.wf/contracts/DATABASE_CONTRACT.md` 不存在＝模組自己的資料完整性提示（`notes` 印，模組行為） | modules.json | 02#45–50、04#129–132 |

合成語意：卡級模組看卡面欄；`resource-lock` 看 Project 投影欄；其餘專案層模組看 `modules.json`，每個模組恰一個 predicate。`modules.json` 對 `resource-lock` 只提供參數。括號內的「該列」是給 PM 的判斷依據，⛔ 不是機械條件。


## 十 · `core/naming.md` 的內容（新；舊規則只有四條，00 空洞 9）

- 卡ID 形狀：`<AREA>-<NNN>`；AREA＝專案層封閉枚舉（aiwf 種子：WF、CLI、DOC、OPS）；NNN＝`open` 依 repo 遞增；語意 slug 的位置＝issue 標題（需求方 2026-09-04 裁定不進卡ID）。修復卡形狀 `<原卡>-FIX<n>`。
- 分支：`wf/<card_id>`；由 `move` 到進行中時寫回卡面。
- 留言的形狀：CLI 寫的留言（`wf:move`／`wf:edit`／`wf:reject`）＝純散文，只寫不讀；人貼的 `wf:note`／`wf:verdict`／`wf:ruling`＝首行給人讀＋一個 `json wf-note`／`wf-return`／`wf-ruling` 區塊給 CLI 讀（決策 1；乙案：CLI 只讀這三種）；人貼的 `wf:log`＝純散文（研究與量測全文），任何角色用 `gh` 直接貼，CLI 不寫不讀，只在 `grilling` 等欄以 URL 指向它（單一寫入通道管的是卡面 JSON 與 Project 欄；需求方 2026-09-04 甲案裁定）；裁決與裁定由人貼，首行 `wf:verdict`／`wf:ruling` 只給人讀，CLI 的判定輸入是留言內的 `json wf-return`／`json wf-ruling` 區塊；PM 代貼需求方裁定時，留言首行固定 `代貼裁定・授權來源：<session 或留言 URL>`（C12）；PM 代貼查核者裁決時同形：首行 `代貼裁決・來源：<模型名>@<工具名>・被審 SHA：<sha>`，第二行起才是查核者原文（需求方 2026-09-04 裁定；CLI 不讀首行，只讀 `json wf-return`）。研究與量測全文的落點＝`wf:log` 留言；卡面 JSON 放判準與指向（K8、K9；需求方裁定，核心留言規則不是模組）。
- 規則檔：kebab-case、無日期；研究與紀錄檔：`docs/research/<YYYY-MM-DD>-<slug>.md`。
- 專案層檔的位置＝`.wf/`。

## 十一 · 空洞落點（00 §十的 20 項）

| 空洞 | 落點 |
|---|---|
| 部署、維護 0 條 | 模組 `deploy`、`maintenance`（來源 ADOPTION 五行、01#45 49 60–62 73；其餘節留空標「待實例」） |
| H17 狀態面不可用時的暫停 | `roles/conduct-common.md` §1 操作紀律（唯一居所；00 §二 H17） |
| 缺陷路徑 | 橫切：三條核心各一落點——無專屬卡種 → `core/card-schema.md`（單一形狀）；留痕走狀態面、不另開 log → `core/verbs.md` §寫入契約；未開卡走 commit trailer 下限 → `roles/conduct-common.md` §2。FIX 後綴屬命名洞 → `core/naming.md`。其餘分住 requirement／planning／implementation（03 §缺陷路徑） |
| 需求方角色薄 | `roles/requester.md` §1（來源 03#133 38 66 81 84 137、01#3 4、02#5 68） |
| 待審清單無形狀 | 形狀＝`.github/ISSUE_TEMPLATE/list-intake.yml` 的 `json wf-intake` 四欄（§一）；schema 住 `core/card-schema.md` §intake；讀它的動詞＝`open`（§七）；動詞集合固定於 §七 |
| 交付報告 schema 散 | `core/handoff.md` |
| 一卡一分支無明文 | `core/naming.md`＋`core/verbs.md` move |
| 資源宣告寫法 | `core/card-schema.md` resources 欄；文法在 db-contract／resource-lock |
| 退回上一階段的條件 | `core/state-machine.md` 轉移表 R1 列＋`stages/review.md` §2 進入／離開條件 |
| 命名與目錄 | `core/naming.md` |
| 研究階段討論回合出口 | `modules/research/module.md` §1（來源 03#52） |
| 停止裁定由誰 | `roles/requester.md` §1（來源 03 空洞）；`move` 的 `--ruling` 形狀見 §七 |
| 設計閘（Design gate）記錄位 | `stages/planning.md` §1（來源 01#90、02#4）；欄位＝`verification` |
| 規則文件自身過期 | 資料＝規則檔 frontmatter `last_confirmed`（§二）；印＝`brief` 來源標記（§七）；參數＝`rule_confirm_days`（§十二）；確認者落點 `roles/requester.md` §1 |
| 查核者資訊邊界 | `roles/reviewer.md` §1（來源 02#966–968、04#41） |
| 常態誰 merge | `stages/closeout.md` §4（來源 03#93） |
| Log 移留言 | 核心留言標頭 `wf:log`（§十），人貼、CLI 不寫不讀，不是模組 |
| 升級梯 JSON 形狀 | 模組 `escalation` 宣告 `fields: [escalation_count]`；未啟用時同一 iteration 第 3 次退回預設＝換人、需求方可否決（PM 減重 4），條文落點 `roles/pm.md` §4 |
| 專案層級別數字 | `core/tiers.md` §專案層（形狀：文字加嚴介面；數字未定，沿 tier-rules §四） |
| 簡介必填時點 | `core/card-schema.md`：建卡即必填（印） |
| 必填欄集中 | `core/card-schema.md` |

05 揭露的三個新洞：封存與釘死路徑守衛互斥 → `stages/closeout.md` §2；Project TEXT 上限 → `core/card-schema.md` §投影欄逐欄標 `max_bytes`（`owner`、`卡ID` 為 TEXT 欄，上限 1024 bytes UTF-8；`階段`、`狀態`、`級別` 為單選欄無此限）；多欄寫入順序契約 → `core/verbs.md` §寫入契約（順序＝卡面 JSON → 五個投影欄 → 回讀；中途失敗的表示＝一則 `wf:reject` 留言＋下一次動詞先對帳）；升級計數誰數 → escalation 模組由 `move` 數。

## 十二 · 注意事項的生命週期（只定資料、參數、管道、落點）

**資料形狀**：三個加嚴層級 F-（框架）／P-（專案）／T-（卡面 `notes` 欄）；每條 `{id, text, origin, last_cited}`；合成形狀＝三個加嚴層級單向累加、不覆寫、無豁免鍵（B1；「只能加嚴」的條文住 `roles/pm.md` §4 與 `core/verbs.md` §notes）；輸出永遠是單一份清單、一套三值（§八）。

**參數**（皆設計值，住 `core/params.md`，填規則時可調）：

| 參數 | 種子值 | 用在 |
|---|---|---|
| promote_threshold | 3 張卡 | T- → P- 的提案門檻 |
| retire_threshold | 20 張結案卡 | `last_cited` 過期即候選退場 |
| guard_review_period | 20 張結案卡 | 需求方定期回看的週期（零拒收硬擋、正式化候選、規則檔過期三類合併） |
| rule_confirm_days | 90 天 | `brief` 來源標記把過期規則檔標出來（§十一） |

**管道**（框架提供，判斷不在框架）：`wf:note` 留言（任何角色可貼；內容＝一個 `json wf-note {text, origin}` 區塊，首行 `wf:note` 只給人讀；候選的形狀＝一則 `wf:note` 留言，`origin`＝來源 finding 的留言 URL；誰在何時貼的條文住 `roles/conduct-common.md` §2 書寫紀律）→ `notes` 只讀 `wf-note` 區塊印候選 → `snapshot` 匯出全部候選與 `last_cited`。

**落點**（條文在填規則時寫）：

| 事 | 落點 | 來源 |
|---|---|---|
| 正式化（提案三格：條文、來源、處理手段；確認者需求方） | `roles/requester.md` §1；提案形狀 `stages/requirement.md` §2 | 需求方 2026-09-04 |
| 升遷 T-→P-→F-（同義判定、誰提誰點頭） | `roles/pm.md` §4 | 決議 §八 |
| 退場（過期候選的處置） | `roles/pm.md` §4 | PM 減重 5 |
| 守衛化的唯一入口與預設值 | `core/tiers.md` §紅線；`roles/requester.md` §1 | 需求方 2026-09-04 |
| 零拒收硬擋的回看、注意事項正式化候選、規則檔 `last_confirmed` 過期 | 合成一次「需求方定期回看」，形狀＝一份回看清單（週期參數 `guard_review_period`）＋一則裁定留言；落點 `roles/pm.md` §4＋`roles/requester.md` §1 | C13、PM 減重 4、自審角度一 |
| 回應三值與 `notes` 欄 schema | `core/handoff.md`、`core/card-schema.md` | §八、§六 |

## 十三 · 填規則的順序與停損

順序（每步一個 PR；執行＝PM，查核＝Codex 跨實體，sign-off＝需求方；CLI 那步例外：執行者另派、PM 不兼）。每步完成點＝跨實體審 APPROVE＋需求方 sign-off，下一步才開。PR 粒度：0、1、2、3、4a、5、6、7 各一 PR；4b 每模組一 PR，第 4 步在全部 4b PR 完成後才算完成：
0. **封存**（需求方 2026-09-04 裁定必為第一步）：舊 canonical、stage-rules、templates、tier-rules、MODEL_ROUTING、ADOPTION、docs 設計文件、舊 `cli/` 與其測試、舊 `scripts/` 掃描器整包移入 `archive/rules-2026-09/`；`archive/issues/` 重新納入 git。新 CI 在本步只剩兩個 job：secret scanner（P4）、commit trailer 檢查（P5）；⛔ 不再有掃描 docs 的 job；⛔ 不預先加沒有被測物的空 job。其餘兩個 job 隨被測物同一 PR 進場：轉移表可達性（§四）在第 1 步 `core/state-machine.md` 的 PR、新 CLI 測試在第 6 步。CI 最終形狀＝四個 job。三個入口檔已先清成 stub。
1. `core/` 九檔，`glossary.md` 最先（其他檔的每個詞都要能在表內找到）；`state-machine.md` 進 repo 的同一 PR 加轉移表可達性 job
2. `roles/conduct-common.md` → 四角色檔
3. 五階段檔（研究住模組）
4. `modules/` 分兩段：4a 每模組宣告區塊（§九清單全部，條文可先空），帶 `transitions` delta 的模組同 PR 加該模組的可達性案例（§四）；4b 條文回填，一模組一 PR，§十一有來源條文的模組全部回填後本步才算完成；`deploy`／`maintenance` 留「待實例」標記帶日期，第一張實例卡出現時回填（§十一）。⛔ 不另記總數
5. README、ADOPTION 重寫
6. 新 CLI `wf`（另一張 T3 卡；同 PR 加新 CLI 測試 job）。形狀：三個目錄 `gh/`（GitHub 讀寫 adapter，唯一有網路的層）、`compose/`（notes／brief 的 DI 合成，只讀檔與 JSON）、`verbs/`（七個入口）。schema 的唯一居所＝`core/card-schema.md` 與 `core/handoff.md` 內的 fenced `json schema` 區塊，CLI 執行期直接讀取（決策 11：規則不住進程式碼），⛔ 不另存副本。測試策略：`gh/` 用錄放的 fake（fixture 為真實 API 回應）；`verbs/` 測轉移表與 D1–D4（schema 由 `core/` 讀入）；`compose/` 測輸出含每段來源標記；⛔ 不測內容判斷（沒有）。src 上限 3,000 行（不含測試）。
7. aiwf 新 Project：五個欄位（階段＝單選 8 值、狀態＝單選 6 核心值＋結案 delta「停止」＋已啟用模組的值、級別＝單選 5 值、owner＝TEXT、卡ID＝TEXT）、兩個 view（活卡依階段分組、全部）、⛔ 不用 GitHub 內建 workflow 自動化；repo 端：ruleset 加 `required_linear_history`、關閉 merge 與 rebase 按鈕、`.wf/modules.json` 種子（modules: []、merge_method: squash、areas: [WF, CLI, DOC, OPS]）；舊卡關閉＋移出 #4；本步驟全部動作可逆（關閉 issue、移出 Project、封存皆可逆；無硬刪）。

停損：任一檔超過 §二上限 ⇒ 停下拆；`cli/src` 超過 3,000 行 ⇒ 停下重看分桶；第 6 步超過 3 輪查核 ⇒ 需求方裁定是否縮射程。三個數字都是設計值。

## 十四 · 本檔的驗收條件（什麼結果會推翻它）

1. `extract/00-consolidated.md` §十的 20 項空洞與 §八的 3 項新洞，每項在 §十一都有一個落點；缺一即不過。
2. `00-consolidated.md` §二–§六每一列「留」的規則，都能對到 §一目錄樹裡恰一個檔；對不到即不過。
3. §四轉移表每個非終態都有出邊，完成與停止出邊為空，每個階段都能到結案；手驗，Codex 複驗。
4. 本檔不含任何一句祈使句形式的規則正文（只含形狀）；含即不過。
5. §三硬擋表（P1–P5、D1–D4）與 §七每一列硬擋一致：硬擋只落在「寫壞資料」與「指向不存在」兩類；不一致即不過。

## 十五 · 原未定五題（需求方 2026-09-04 裁定）

- 卡ID `<AREA>-<NNN>` 不帶 slug（§十）。
- 新 CLI 名 `wf`（§一）。
- 研究與量測全文的落點＝`wf:log` 留言（核心留言標頭，人貼，§十）；`log-comments` 模組取消（§十一）。
- Project 投影欄五個（§六）。
- 同一 iteration 第 3 次退回的預設處置＝換人，已進 §四與 §十一。
- PM 代貼**裁決**沿用 C12 首行標記，並加被審 SHA（§十；需求方 2026-09-04 裁定，第二十一輪 R1-01）。


## 十六 · 審核修改紀錄

逐輪處置移至 `REBUILD-SKELETON-REVIEW-LOG.md`（需求方 2026-09-04 乙案：骨架只留形狀）。

## 十七 · 對 #177 規劃審 38 個 P1 finding 的自審

已對照並修正 6 處：狀態值域一處兩答（P1-11／34）、硬擋計數三居所（P1-23／38）、CLI 讀留言的範圍（P1-27）、schema 升版規則（P1-30）、留言併發（P1-33）、填規則各步 owner 與本檔驗收條件（P1-14／22／35）。未套用：producer 可重現（P1-29／32／37）——本檔無 artifact。

## 十八 · `core/glossary.md` 的內容（通用語言；需求方 2026-09-04 提議）

每列＝一個詞。四欄：詞 · 一句定義 · ⛔ 不是什麼 · 禁用同義詞。⛔ 不放理由。消費者三個：CLI enum 與 Project 選項名（取「詞」欄字面）、規則檔正文、審核提示。「禁用同義詞」只收會被當成同一概念的專名（舊制術語、英文名、別檔文件名），⛔ 不收日常詞；日常詞的多義靠「⛔ 不是什麼」欄（需求方 2026-09-05 甲案；量測：舊清單 199 條中 54 條日常詞在 core 正文命中 111 次、真違規 4 次）。違規判定條文住 `roles/conduct-common.md` §2。約束邊界：詞表管中文正文用詞；schema 鍵名（§六英文識別字，如 `spec_version`、`stage_plan`）與 GitHub 平台詞（issue、PR、Project、ruleset、comment）不入表、不受禁用同義詞約束，中文正文指涉它們時用表內對應詞。種子（填規則時逐列補定義）：

| 詞 | 涵蓋 | 禁用同義詞 |
|---|---|---|
| 卡、清單項、撤銷卡 | 卡＝在板 issue；清單項＝不在板且無 `wf-card` 區塊的 issue（無卡ID）；撤銷卡＝不在板但帶 `wf-card` 區塊的 issue（保留卡ID，`open` 可復板） | Backlog、task |
| 階段（8） | 需求…結案 | phase、gate |
| 狀態（核心 5＋阻塞；模組加值） | 待辦…退回、阻塞、停止、升級、不可判定、運行中 | 交付狀態、部署狀態、Status |
| 轉移、轉移記錄 | `move` 的一次寫入與其留言 | event、handoff |
| iteration | 卡進入執行階段的次數 | 輪次、round |
| 查核輪 R1–R4 | 前提／射程／內容／影響面 | 輪次、pass |
| 注意事項、加嚴層級 F-／P-／T- | 一份清單、四個來源 | 踩坑清冊、層（作為來源） |
| 硬擋、印、語意 | 機械側三類行為 | 守衛、閘門、偵測器、拒收（作為類別名） |
| 模組、啟用條件 | opt-in 機制與其條件 | plugin、功能旗標 |
| 裁定、裁決 | 需求方的決定／查核者的結論，皆為留言 | sign-off（除 T4 外） |
| 派工單、交回單、裁定單 | 三份交接文件 | 派工包、派審詞、交付報告、結案報告、狀態變更裁定單 |
| 需求方、PM、執行者、查核者 | 四角色 | 祕書、Coordinator、第二 PM、人工查核、規劃者 |
| 實體、家族 | 跑角色的 session／模型家族 | instance |
| 級別 T0–T4、能力層級 | 風險軸／模型能力軸 | tier（中文語境） |
| 紅線 | 至少 T3 的變更域 | 高風險 |
| 核心痛點、驗收條件、非射程、服務的原始目標 | 卡面四個判準欄 | scope、AC |
| 待審清單 | 不在板、無 `wf-card` 區塊、帶 `wf-intake` 的 issue 集合；`open` 的唯一入口 | backlog、inbox、待辦池 |
| 規格、規格欄 | 卡面會使 `spec_version` +1 的四欄：`acceptance`／`verification`／`non_scope`／`resources`（C11）；核心痛點另受裁定連結約束，不在此列 | 需求文件、spec |
| 資料有效性、平台委託 | 硬擋的兩類來源：D1–D4／P1–P5 | guard |
| 完整性 | 必要欄或必要段齊不齊；CLI 只驗齊不齊，齊了對不對交人判 | 正確性 |
| finding | 查核者交回單裡一條有 id、severity、blocking、attribution 的問題 | issue（與 GitHub issue 衝突）、缺陷（作為 finding 的同義）、bug |
| 缺陷 | 已交付或已進 main 的行為錯誤；走一般階段，不配專屬卡種（§五 缺陷套用表、§十一 缺陷路徑） | bug（作為卡種）、BUG- 前綴 |
| 合成表 | 核心轉移表 ∪ 已啟用模組 add − remove，再按該卡 `stage_plan` 展開 | 狀態表、workflow 圖 |
| 模組 delta | 模組宣告區塊裡對狀態值域、轉移、欄位、注意事項的增減 | patch |
| 設計閘（Design gate） | 規劃階段離開前 `verification` 欄填齊的檢查點；正式中文詞＝設計閘 | 設計審、design review |
| 驗證項目 | 卡面 `verification`：每條 {item, who}，說「怎麼證明驗收條件成立、誰證」；驗收條件說「什麼算過」；`self_run` 是交回單裡真的跑了什麼 | 測試計畫、驗證方式 |
| 清單收斂宣告 | 一張卡吸收哪些清單項：卡面 `source_issue`＋收件表單 `dedupe` 欄 | 合併宣告 |
| 封存、撤銷、停止 | 三個離開動作 | — |
| 留言標頭 wf:* | CLI 與人留言的首行 | marker、事件型別 |
| 來源（四個）：core／module／project／card | 清單與交接文件的合成來源 | 層（作為來源）、layer |
| 七動詞 open／move／edit／notes／brief／review／snapshot | CLI 的全部入口 | amend、改卡、handoff、assign、pitfalls、踩坑、verdict（作為動詞） |
| 未驗清單三分類 cannot／skipped／deferred | 驗不了／沒去驗／刻意不驗 | 未驗（裸列）、TODO |
| 回應三值 followed／not_applicable／found | 已遵循／不適用／發現 | 已檢查、已遵守、N/A |
| 投影欄（5）：階段／狀態／級別／owner／卡ID | Project 上由 CLI 回寫的欄 | 看板欄位、Ledger 欄 |
| db_scope | 卡對資料庫的變更範圍 enum none／read／write／schema／data-migration；後兩者連動 T4 | db_permission、資料庫權限 |
| trailer | commit 訊息末端連續的結構化標籤區塊（Requested-by、Planned-by、Implemented-by、Reviewed-by） | footer、git-tag |
| falsifier | 交回單逐條 AC 的證偽條件 | 反測（保留給統計紅線模組的對抗性反測）、反向案例 |
| sign-off | 需求方對 T4 卡的最終授權裁定 | approve |
| self_run | 交回單內實跑指令與原始輸出 | 本地測試、手動驗證 |
| attribution | finding 責任歸屬 enum executor／coordinator／planner／reviewer／external | 責任方、責任者 |
| 狀態面 | 卡當下的階段＋狀態＋阻塞，唯一居所＝issue body JSON 與 Project 投影欄 | 看板狀態、board |
| 階段計畫 | 卡面 `stage_plan`：這張卡要走的階段子集（研究／部署／維護為模組選配） | pipeline |
| 終態 | 出邊為空的狀態：完成、停止 | closed、done |
| 父卡、鏈深 | `parent` 指到的卡；沿父鏈算的層數（>2 只印） | 母卡、子卡、family、epic |
| 資源宣告 | 卡面 `resources` 欄的字串陣列；文法住 db-contract／resource-lock 模組 | — |
| owner | 卡當下的 {role, actor}，由 `move --actor` 寫 | 負責人、assignee |
| 失誤登記 | 交回單裡執行者自報的錯誤與修正（非查核者 finding） | 錯誤清單、bug list |
| 復活條件 | 裁定單裡停止或撤銷後可重開的條件 | 重啟條件、reopen |
| 翻案把手 | 裁定單裡推翻本次裁定所需的證據種類 | appeal |
| 三軸 | 級別判準的三個軸：敏感面／可復原性／影響面＝`tier_basis` 的 sensitive／recoverable／blast（來源 tier-rules L58–60） | 風險軸 |
| 分支 | 卡面 `branch`：該卡工作所在的 git 分支名 | feature |
| SHA 四種：被審／來源／合併基底／合併 | 被審＝代貼裁決首行所記、查核者讀到的 commit；來源＝卡面 `source_sha`，交回時的分支頭；合併基底＝派工單的 merge-base；合併＝結案時 main 上的 merge commit | 目標 SHA、HEAD（作為名詞） |
| 獨立查核 | 查核者實體不同於本 iteration 執行者實體（P2） | 第二雙眼、peer review |
| 拒收（事件） | CLI rc≠0 並寫一則 `wf:reject` 留言的那次事件；作為硬擋類別名仍禁用 | reject（作為類別名） |
| 寫壞資料、指向不存在 | CLI 拒收的僅有兩類：D1／D3 與 D2／D4 | 驗證失敗、invalid |
| 質詢（grilling） | T4 卡離開規劃前需求方與 PM 逐題定案的對話紀錄，落 `wf:log`，卡面 `grilling` 指向 | code review |
| 單向門 | 級別只升不降的門檻：降級需裁定（`core/tiers.md` §單向門） | 不可逆、one-way |
| 合併方式 | 專案層 `merge_method`，由平台強制 | merge 策略、合併策略 |
| 寫入契約 | `core/verbs.md` 的固定節：檢查先於首次遠端寫入、寫後回讀、拒收留痕 | 寫入規則、transaction |
| 副作用入口 | 派工單列的、改動會外溢的檔或設定清單 | blast list |
| 退回理由 | 裁定單裡每輪退回引用的 `wf-return` finding | 駁回原因、reject reason |

## 未驗

- 目錄樹與節次是設計，未經任何試填；行數上限是估計。
- 轉移表未跑可達性檢查；模組 delta 格式未實作。
- 卡面 schema 的欄位集由 00 §四 open 段推得，未與 cpbl 現有 118 張卡的欄位對照。
- PM 每卡的 CLI 呼叫次數（約 8–10）與舊制相近；本輪省的是每次呼叫的旗標數、拒絕迴圈與手抄信封，⛔ 未量測。
