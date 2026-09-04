# 新框架骨架（2026-09-04）

> 自舉第二份文件（決策 10）。用途：定下**目錄、每個檔的固定節與行數上限、狀態機、卡面 schema、動詞、交接文件、模組宣告格式、命名規則**，讓之後「填規則」時每個檔的密度一致、每條空洞有落點。
> 輸入：`REBUILD-DECISIONS-2026-09-04.md`、`extract/00-consolidated.md`、`extract/07-conflicts.md`。引用格式沿用 `01#19`、`H7`、`S4`、`K2`、`C3`。
> ⛔ 本檔不寫規則正文；規則正文在「填規則」步驟寫進各檔。本檔經 Codex 跨實體審＋需求方 sign-off 後生效。

## 一 · 目錄樹

```
README.md                  L0 入口：一分鐘心智模型＋查詢指令；⛔ 不列會變的東西（04#158）
.github/ISSUE_TEMPLATE/
  list-intake.yml          待審清單收件表單：預填一個 `json wf-intake` 區塊，四欄 source／observation／dedupe（關鍵字＋命中號）／repo；`open` 只讀該區塊（決策 1），散文欄給人看
core/                      定義層（C8）。只放定義與機械語意，⛔ 不放理由
  state-machine.md         階段、核心狀態值域、核心轉移表、模組 delta 合成規則
  tiers.md                 T0–T4 表、紅線域、能力層級判準、單向門、缺陷級別套用
  card-schema.md           卡面 fenced JSON 欄位集（JSON Schema 逐字）
  verbs.md                 七動詞：open / move / edit / notes / brief / review / snapshot
  handoff.md               三份交接文件的段落表＋交回單 JSON schema
  naming.md                卡ID、分支、檔名、留言標頭的命名規則
  params.md                設計值參數表（§十二），一列一參數：名、種子值、用在哪
  glossary.md              通用語言（Ubiquitous Language）：每個詞一行——詞、一句定義、⛔ 不是什麼、禁用同義詞；規則檔、CLI enum、審核提示只准用表內的詞（§十八）
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
.wf/modules.json           啟用的模組與參數（§九）＋專案層設定：`merge_method`（squash／merge；C3 裁定合併方式歸專案層）
.wf/stages/<階段>.md        專案層注意事項 P-<階段>-NN（只能加）
.wf/tiers.md               專案層加嚴（只能往上綁）
.wf/contracts/             模組要求的專案填空（DATABASE_CONTRACT 等）
```

## 二 · 每個檔的固定節與行數上限

密度不均是上一版的病（01 空洞、03 空洞）。每種檔固定節次、固定上限；寫不滿就留短，⛔ 不塞理由。理由與來歷一律寫成 `→ archive/…` 連結（決策 9）；萃取稿 `docs/research/extract/` 是填規則的輸入，填完後整目錄移入 `archive/research/`，規則正文⛔ 不引用它。

| 檔種 | 固定節（順序不可換） | 上限 |
|---|---|---|
| 階段檔 | 1 目標與產出 · 2 進入／離開條件 · 3 狀態 delta（引用 core） · 4 階段內迴圈（①–⑤ 在本階段的形狀） · 5 各角色做／⛔ 不做 · 6 注意事項 `F-<階段>-NN` | 60 行 |
| 角色檔 | 1 職責 · 2 紅線 · 3 動作前自檢 · 4 注意事項 `F-<角色>-NN` | 60 行 |
| conduct-common.md | 1 操作紀律（實跑、fetch、不截斷、rc、負控、逐字、多居所、驗原件） · 2 書寫紀律（數字帶日期、不寫行號、引用逐字） | 40 行 |
| core 各檔 | 依檔（§四–§八、§十八） | 120 行 |
| module.md | 0 宣告區塊（§九） · 1 條文 · 2 該模組加的注意事項 | 80 行 |
| README | 1 心智模型（≤12 行） · 2 角色一句話 · 3 查詢指令 | 40 行 |

**每個規則檔、模組檔、core 檔統一 frontmatter 四欄**（沿舊 stage-rules 與卡片簡介的 skill 式檔頭，決策 9）：`name`、`when`（適用時機一句）、`non_scope`（⛔ 不是什麼一句）、`last_confirmed`（日期，§十一 規則文件自身過期）。`brief` 每段首行 `[來源: …]` 印該檔 `name`＋`when`；`notes` 印清單時同。

每條規則一句祈使句，⛔ 不帶「因為」；⛔ 不出現 ⚠️／⭐／⛔ 以外的符號；⛔ 不寫現況數字（要寫就帶日期，`common.md` 書寫紀律）。

## 三 · 核心迴圈與角色（定案摘要）

**第零條（README 心智模型第一行）**：CLI 提供資訊清單，AI 判斷；CLI 只確認清單有沒有填，⛔ 不做內容判讀。舊 ROADMAP 目標 1「有機械執行者擋下才算達成」廢止。三目標並列：可稽核、防低級事故、**流程順暢**（前兩項不得以犧牲第三項達成；沿 #177 brief）。

決策紀錄「補充裁定」已載：第零條取代 C10 的 20 條計數，硬擋以本表為準。依第零條把 `extract/00-consolidated.md` §二的 19 條加 K4 K5 逐條重判如下。

| 舊編號 | 一句 | 重判 | 落點 |
|---|---|---|---|
| H1 | main ruleset 禁改史禁刪 | 平台委託 | ruleset |
| H2＋H15 | T2 以上走分支＋獨立查核；執行者不 merge | 平台委託 | ruleset required check＋PR |
| H3 | 合併方式由專案層 `merge_method` 決定並以平台設定強制（squash ⇒ ruleset `required_linear_history`＋關閉 merge／rebase；merge ⇒ 關閉 squash／rebase） | 平台委託（值歸專案層，C3） | repo 設定＋ruleset；aiwf 的 `.wf/modules.json` 選 squash |
| H4 | secrets 不進 git | 平台委託 | CI secret scanner（需求方裁定必備） |
| H12 | commit trailer 鍵與連續區塊 | 平台委託 | CI |
| H5 | 同卡同輪一人一角；執行者欄≠查核者欄 | 資料有效性 | CLI 比對兩欄相等 |
| H6 | T4 查核者家族≠執行者家族，或已給的 sign-off URL 存在且作者相符 | 資料有效性 | CLI 比對家族欄或驗已給的 URL；缺 URL 只印 |
| H7 | 轉移在合成表內；終態無出邊；無自由文字狀態 | 資料有效性 | CLI `move` |
| H8 | 進終態前分支已刪、PR 已合併（worktree 部分屬 resource-lock 模組） | 資料有效性（平台事實） | CLI `move` 讀 GitHub |
| H9 | `open` 只從清單 issue；不在板上；鏈深 ≤2 | 資料有效性 | CLI `open` |
| H10 | JSON 合法、鍵集合封閉、解析失敗整卡拒、寫後回讀 | 資料有效性＋寫入順序 | CLI 全動詞 |
| H11＋K5 | SHA 40 碼且在遠端；報告入口 SHA＝分支 head；被引用 SHA 不得改寫 | 資料有效性 | CLI `brief`／`move` |
| K10 | 派審前分支與 main 的 `merge-tree` 無衝突 | 資料有效性（git 事實） | CLI `brief --for reviewer` |
| H13 | 交回單欄位一致性（C2 三含意）：`REQUEST_CHANGES` 須有 `blocking: true` 或 `core_pain_resolved: no`，兩者皆無即拒收為無效裁決；`APPROVE` 不得有 `blocking: true` 或 `core_pain_resolved: no` | 資料有效性（JSON 欄位間一致） | CLI 讀交回單 JSON |
| H14 | 查核唯讀、不代改 | **紀律** | `roles/reviewer.md`；分支變動由 H11 抓 |
| H16 | 事件只寫該卡 Issue | **語意** | `core/verbs.md` |
| H17 | 狀態面不可用時暫停 | **紀律** | `roles/conduct-common.md` |
| H18 | 結案四停下條件 | **降為印** | PM 判 |
| H19 | 禁 `gh pr update-branch` | **砍** | C3 |
| K4 | 守衛必須進 CI | **紀律** | `roles/conduct-common.md`：若有守衛則進 CI，⛔ 不是要有守衛 |

硬擋淨數 **14**：平台委託 5、CLI 資料有效性 9。CLI 層的 9 條沒有一條讀散文，全部是欄位存在、相等、在表內、在遠端、可合併。

- 四角色：需求方、PM、執行者、查核者（決策 5）。第二 PM、人工查核不存在（C4）。
- 每階段五步：① `notes` 印一份清單（四個來源：框架核心 → 已啟用模組 → 專案層 → 卡面，決策 11 逐字順序）② PM `brief` 派 ③ 交回 ④ PM 對完整性＋判 R1 R2 ⑤ `move`（S8、S9）。
- 查核者判 R3 R4；查核者的裁決同時覆蓋派工單（attribution: coordinator／planner）（C4）。
- 裁決與裁定＝GitHub 留言；動詞只收 `--ruling <URL>`：缺即印，已給但不存在或作者不符才拒（C12–C14）。

## 四 · `core/state-machine.md` 的內容

**階段**：需求 → 研究* → 規劃* → 執行 → 審核 → 部署* → 維護* → 結案。星號＝可跳過；研究、部署、維護是卡層模組（唯一啟用條件＝該卡 `stage_plan` 含該階段；事實來源＝卡面 JSON），未啟用時該卡的階段序列裡沒有它（S3、C6）；規劃的跳過由級別決定（T0／T1），仍是核心。

**核心狀態值**（C6）：待辦／進行中／待確認／完成／退回＋正交 阻塞。階段 delta 可加：結案階段加 停止（終態，S6）。模組可加：`research` 加 不可判定；`escalation` 加 升級；`maintenance` 加 運行中。

**核心轉移表**（每列＝一條允許的邊；`move` 只接受表內轉移，H7）：

| from | to | 條件 |
|---|---|---|
| 需求／待確認 | 研究或規劃或執行／待辦 | 依階段計畫的下一階段；T2+ 不得跳過規劃（S3） |
| 需求／待確認 | 清單（撤銷） | 卡ID 保留、iteration 延續（S6、C5）；無 `--ruling` 印提示 |
| 任一階段／待辦 | 同階段／進行中 | 派工 |
| 任一階段／進行中 | 同階段／待確認 | 交回 |
| 任一階段／待確認 | 下一階段／待辦 | ⑤ 過 |
| 任一階段／待確認 | 同階段／退回 | ⑤ 不過（R2–R4） |
| 任一階段／待確認 | 規劃或需求／退回 | ⑤ R1 不過（S10） |
| 任一階段／退回 | 同階段／進行中 | 再派；進執行時 iteration +1（S7）。同卡同 iteration 累積第 3 次退回（不分階段、不要求連續）時 `move` 印「預設處置＝換執行者（升級①）；需求方可否決」（PM 減重 4）；escalation 模組未啟用時只印不擋 |
| 任一狀態 | 阻塞 | 記 from；無 `--ruling` 印提示 |
| 阻塞 | from | 解除 |
| 最後一個階段／待確認 | 結案／待確認 | 結案報告 |
| 結案／待確認 | 完成 或 停止（結案階段 delta） | 完成需 H8 收尾；停止無 `--ruling` 印提示；兩者皆封存 |

**模組 delta 格式**：模組宣告區塊裡 `transitions.add` 與 `transitions.remove` 各列若干 `{from, to, condition}`；合成＝核心 ∪ add − remove；CI 跑可達性測試（01#57 保留為測試要求）。

## 五 · `core/tiers.md` 的內容

固定節與各節來源（條文在填規則時寫）：
- §級別表：T0–T4 五列 × 最低閘門（來源 01#66–68）。
- §判準：三軸（敏感面／可復原性／影響面）與合成方式（來源 03#44）。
- §紅線域：清單（來源 01#64、02#63）；`db_scope` 與 T4 的連動（C9）；T4 查核的獨立性條件（H6）。
- §單向門：升與降的形狀（來源 03#31、C12）。
- §缺陷套用表（來源 03#45）。
- §能力層級：三值與判準（來源 03#49）。
- §專案層：加嚴介面（來源 03#48；數字未定，tier-rules §四）。

## 六 · `core/card-schema.md` 的內容

卡面＝Issue body 的一個 fenced JSON 區塊（`json wf-card`）＋人讀散文段。CLI 只讀寫 JSON（決策 1）；讀留言時同樣只讀 fenced JSON 區塊（`json wf-return`、`json wf-ruling`），散文一律不讀。

| 欄 | 型別 | 誰填 | 何時必填（`open` 印缺欄） | 誰讀 |
|---|---|---|---|---|
| schema_version | int | CLI | 建卡 | CLI |
| card_id | string | CLI 配（naming；建後不可改） | 建卡 | 全部 |
| source_issue | int | CLI（建後不可改） | 建卡 | CLI |
| feature | string | PM | 建卡 | brief |
| core_pain | string | CLI 從清單 issue 逐字帶入 | 建卡 | 所有交接文件 |
| origin | url | CLI 帶入 | 建卡 | brief |
| non_scope | string[] | PM | 建卡 | brief、R2 |
| stage_plan | enum[]（階段名逐字） | PM | 建卡 | move |
| acceptance | string[] ≥1 | PM | 離開規劃前 | brief、R3 |
| verification | {item, who}[] | PM | 離開規劃前 | brief |
| list_convergence | int[]（清單 issue 號） | PM | 建卡 | 結案核對 |
| service_goal | string | 需求方 | 建卡 | R1 |
| parent | card_id | PM | 有父卡時 | 鏈深、initiative 模組 |
| tier | enum T0–T4 | PM | 建卡 | move、tiers |
| tier_basis | {sensitive, recoverable, blast} | PM | 建卡 | 印 |
| exec_capability / review_capability | enum＋reason | PM | 建卡 | brief |
| db_scope | enum none/read/write/schema/data-migration | PM | 建卡 | tiers |
| resources | string[]（文法住 db-contract／resource-lock） | PM | 建卡 | resource-lock 模組 |
| brief | {when, non_scope}（卡片簡介，與規則檔 frontmatter 同形） | PM | 建卡 | 清單搜尋、`brief` 卡與身分段 |
| spec_version | int | CLI（edit 自動 +1） | — | 派工單、initiative |
| owner | {role, actor} | CLI（move） | — | brief |
| branch | string | CLI（move 到進行中時寫） | — | brief、H11 |
| iteration | int | CLI | — | brief |
| modules | string[]（此卡實際生效的模組） | CLI 由 `.wf/modules.json` 導出 | 建卡 | notes、brief |
| notes | {id: `T-<階段>-NN`, text, origin: 留言 URL}[]（任務層注意事項） | 任何有 shell 的角色經 `edit --set notes+=`，來源為 `wf:note` 留言（§十二） | 否 | notes、brief |

未定義鍵 ⇒ fail-closed（H10）。`schema_version` 的升版判準與舊版卡遷移方式住 `core/card-schema.md` §版本（來源：P1-30；形狀＝升版觸發條件一句、遷移路徑一句）。Project 欄位只放 `階段`、`狀態`、`級別`、`owner`、`卡ID` 五個投影欄，全由 CLI 回寫；逐欄 `max_bytes` 與寫入順序見 §十一（05 新洞）。

## 七 · `core/verbs.md` 的內容

| 動詞 | 輸入 | 硬擋（rc≠0 並寫一則拒收留言，C13） | 印（rc=0） | 寫 |
|---|---|---|---|---|
| `open <issue>` | 清單 issue 號 | 不是 issue、已在板上、鏈深 >2、JSON 鍵不合法（H9、H10） | 缺欄清單、清單留言數與未讀警示（K7） | 建卡 JSON、加進 Project、配卡ID |
| `move <card> --to <階段/狀態> [--ruling URL]` | 目標、裁定 URL | 轉移不在合成表內、終態出邊、進終態前收尾未完成、**已給的** `--ruling` URL 不存在或作者不符（H7、H8；資料有效性） | **缺 `--ruling`**（撤銷、阻塞、停止、級別下修；C12）、缺欄（阻塞四欄、停止三欄）、merge SHA 是否 main 祖先、CI 狀態、離開規劃時仍有 TODO | Project 欄、JSON owner／branch／iteration、轉移記錄留言（S5） |
| `edit <card> --set <欄>=<值> [--ruling URL]` | 欄與值 | JSON 不合法、改 `card_id` 或 `source_issue`（H10、C11） | 無裁定連結、審核期修改 | JSON；`edit` 留言；規格欄變動時 spec_version +1；審核期另貼 `edit during review` 留言（C11） |
| `notes <card> [--stage]` | — | — | 一份編號清單，四個來源（框架核心 F- → 已啟用模組 F- → 專案層 P- → 卡面 `notes` 欄 T-，決策 11 順序）＋ pitfalls-13 樣板（若啟用） | 無 |
| `brief <card> --for executor\|reviewer\|closeout` | 角色 | 分支 HEAD ≠ source_sha、SHA 未 push、`merge-tree` 有衝突（H11、K10） | 缺人填段的提示 | 無（輸出到 stdout；PM 貼進留言）。輸出形狀：每一段首行固定 `[來源: <來源>/<檔>#<節>]`，來源值域＝core／module:<名>／project／card（決策 11「每段標來源」） |
| `review <card> --file <交回單.json> --role executor\|reviewer` | 本機交回單 JSON | schema 不合法、H13 欄位不一致（資料有效性） | 缺段（未驗清單、self_run、注意事項回應） | 以 `json wf-return` 區塊貼成該卡一則留言，⛔ 不動狀態；有 shell 的查核者與執行者用它，沒 shell 者手貼同格式（C14） |
| `snapshot` | — | — | — | 本機 JSON＋Markdown |

`core/verbs.md` 另有固定節「寫入契約」，內容來源＝K2（檢查先於首次遠端寫入、寫後回讀）、K3／C13（拒收留痕）、決策 1（只讀 fenced JSON）、第零條（不產生統計數字）；條文在填規則步驟寫，本檔只定節名與來源。

## 八 · `core/handoff.md` 的內容（04 §範本欄位）

| 文件 | 誰→誰 | CLI 填 | 人填 |
|---|---|---|---|
| 派工單（每段首行 `[來源: …]`，決策 11） | PM→執行者或查核者 | 卡與身分、核心痛點、驗收逐條、非射程、merge-base SHA、前輪 findings、能力層級建議、注意事項編號清單、副作用入口清單 | 寫入授權、唯讀範圍、實際模型與偏離理由、未驗項（三分類）、本文件落差 |
| 交回單 | 執行者或查核者→PM | 卡與身分、AC 條文、commit 清單、改動面、finding_id | self_run、逐 AC 做法／證據／falsifier、失誤登記或 findings 八欄、**未驗清單（三分類：驗不了／沒去驗／刻意不驗，各附原因）**、注意事項回應、範圍外發現、`review_result`／`core_pain_resolved`（查核者） |
| 裁定單 | PM→需求方 | 事件序、退回理由、findings、merge SHA、CI、四停下條件前三項 | 類別（升級／停止／撤銷／級別變更／結案確認／其他）、四選一各值證據、復活條件、翻案把手、被繞過的閘門 |

交回單 JSON schema＝舊 review-prompt §5 加 `role` 欄與 `unverified: [{item, kind, reason}]`（`kind` 封閉值域 `cannot`／`skipped`／`deferred`，`reason` 非空）；同一 schema 執行者與查核者共用。**注意事項回應的三值唯一定義居所＝本檔**：`note_responses: [{id, value, text}]`，`value` 封閉值域 `followed`／`not_applicable`／`found`（人讀顯示 已遵循／不適用／發現），`not_applicable` 與 `found` 的 `text` 非空；§十二與各階段檔只引用不複製；CLI 只查 id 是否覆蓋 `notes` 印出的清單、value 在值域、text 非空，⛔ 不判內容。

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
| stat-redline | 卡的 `tier_basis.sensitive` 含統計／ML／資料正確性 | 卡面 JSON | 04#135–138、03#57 |
| escalation | 專案 `.wf/modules.json` 列出（計數由 `move` 在該 iteration 內做） | modules.json | 00 §六；05 空洞 7 |
| resource-lock | 同時 ≥2 執行者：`move` 派工當下，板上狀態＝進行中且 `owner.actor` 與本卡不同的卡 ≥1 張（決策 6） | Project 投影欄 狀態＋owner（`modules.json` 只放參數，如 lease TTL，⛔ 不是條件） | 00 §六 |
| pitfalls-13 | 專案 `.wf/modules.json` 列出 | modules.json | 00 §六 |
| identity | 專案 `.wf/modules.json` 列出（多實體共用同一帳號時該列） | modules.json | 00 §六 |
| snapshot | 專案 `.wf/modules.json` 列出（狀態面在 GitHub 時該列） | modules.json | 00 §六 |
| db-contract | 專案 `.wf/modules.json` 列出（有 DB 時該列）且 `.wf/contracts/DATABASE_CONTRACT.md` 存在（兩者 AND；缺契約檔＝未啟用，`notes` 印警示） | modules.json＋契約檔 | 02#45–50、04#129–132 |

合成語意：卡層模組看卡面欄；`resource-lock` 看 Project 投影欄；其餘專案層模組看 `modules.json`；`db-contract` 是唯一 AND。`modules.json` 對 `resource-lock` 只提供參數。括號內的「該列」是給 PM 的判斷依據，⛔ 不是機械條件。


## 十 · `core/naming.md` 的內容（新；舊規則只有四條，00 空洞 9）

- 卡ID 形狀：`<AREA>-<NNN>`；AREA＝專案層封閉枚舉（aiwf 種子：WF、CLI、DOC、OPS）；NNN＝`open` 依 repo 遞增；語意 slug 的位置＝issue 標題（需求方 2026-09-04 裁定不進卡ID）。修復卡形狀 `<原卡>-FIX<n>`。
- 分支：`wf/<card_id>`；由 `move` 到進行中時寫回卡面。
- 留言標頭：轉移記錄 `wf:move`、修訂 `wf:edit`、拒收 `wf:reject`、注意事項候選 `wf:note`、研究與量測全文 `wf:log`；裁決與裁定由人貼但首行固定 `wf:verdict`／`wf:ruling`；PM 代貼他人裁決或裁定時，末段固定一行 `代貼裁定・授權來源：<session 或留言 URL>`（C12）。研究與量測全文一律進 `wf:log` 留言，卡面 JSON 只放判準與指向（K8、K9；需求方裁定，核心規則不是模組）。
- 規則檔：kebab-case、無日期；研究與紀錄檔：`docs/research/<YYYY-MM-DD>-<slug>.md`。
- 專案層檔的位置＝`.wf/`。

## 十一 · 空洞落點（00 §十的 20 項）

| 空洞 | 落點 |
|---|---|
| 部署、維護 0 條 | 模組 `deploy`、`maintenance`；條文從 ADOPTION 五行與 01#45 49 60–62 73 起草，其餘留空標「待實例」 |
| 缺陷路徑 | 橫切：三條核心各一落點——無專屬卡種 → `core/card-schema.md`（單一形狀）；留痕走狀態面、不另開 log → `core/verbs.md` §寫入契約；未開卡走 commit trailer 下限 → `roles/conduct-common.md` §2。FIX 後綴屬命名洞 → `core/naming.md`。其餘分住 requirement／planning／implementation（03 §缺陷路徑） |
| 需求方角色薄 | `roles/requester.md`：裁升級、撤銷、停止、T4 sign-off、結案 ④、清單條件 2；每條一句 |
| 待審清單無形狀 | 形狀＝`.github/ISSUE_TEMPLATE/list-intake.yml` 的 `json wf-intake` 四欄（§一）；schema 逐字住 `core/card-schema.md` §intake；`open` 讀它並印缺欄；收件動詞⛔ 不加 |
| 交付報告 schema 散 | `core/handoff.md` |
| 一卡一分支無明文 | `core/naming.md`＋`core/verbs.md` move |
| 資源宣告寫法 | `core/card-schema.md` resources 欄；文法在 db-contract／resource-lock |
| 退回上一階段的條件 | `core/state-machine.md` 轉移表 R1 列＋`stages/review.md` §4 |
| 命名與目錄 | `core/naming.md` |
| 研究階段討論回合出口 | `modules/research/module.md` §1：討論以一則留言收口，`move` 收該 URL |
| 停止裁定由誰 | `roles/requester.md`；`move` 收 `--ruling`，缺即印 |
| Design gate 記錄位 | `stages/planning.md` §1：設計判斷寫進 verification 欄；N/A 寫理由 |
| 規則文件自身過期 | 生命週期落點：每個規則檔 frontmatter `last_confirmed: <日期>`；`snapshot` 印超過 90 天未確認的規則檔清單（印，不擋；90 是設計值）；確認者＝需求方，確認動作＝改日期一次 commit。引用寫法另住 `roles/conduct-common.md` §2 |
| 查核者資訊邊界 | `roles/reviewer.md` §1：只看派工單與分支；派工單就是全部 |
| 常態誰 merge | `stages/closeout.md` §4：PM 在四停下條件內直行（03#93） |
| Log 移留言 | 核心留言標頭 `wf:log`（§十），不是模組 |
| 升級梯 JSON 形狀 | 模組 `escalation` 宣告 `fields: [escalation_count]`，由 `move` 數；未啟用時第 3 次退回的預設處置住 `stages/review.md` §4 與 `roles/pm.md`（PM 減重 4） |
| 專案層級別數字 | `core/tiers.md` §專案層（形狀：文字加嚴介面；數字未定，沿 tier-rules §四） |
| 簡介必填時點 | `core/card-schema.md`：建卡即必填（印） |
| 必填欄集中 | `core/card-schema.md` |

05 揭露的三個新洞：封存與釘死路徑守衛互斥 → `stages/closeout.md` §2；Project TEXT 上限 → `core/card-schema.md` §投影欄逐欄標 `max_bytes`（`owner`、`卡ID` 為 TEXT 欄，上限 1024 bytes UTF-8；`階段`、`狀態`、`級別` 為單選欄無此限）；多欄寫入順序契約 → `core/verbs.md` §寫入契約（順序＝卡面 JSON → 五個投影欄 → 回讀；中途失敗的表示＝一則 `wf:reject` 留言＋下一次動詞先對帳）；升級計數誰數 → escalation 模組由 `move` 數。

## 十二 · 注意事項的生命週期（只定資料、參數、管道、落點）

**資料形狀**：三個加嚴層級 F-（框架）／P-（專案）／T-（卡面 `notes` 欄）；每條 `{id, text, origin, last_cited}`；輸出永遠是單一份清單、一套三值（§八）。

**參數**（皆設計值，住 `core/params.md`，填規則時可調）：

| 參數 | 種子值 | 用在 |
|---|---|---|
| promote_threshold | 3 張卡 | T- → P- 的提案門檻 |
| retire_threshold | 20 張結案卡 | `last_cited` 過期即候選退場 |
| guard_review_period | 20 張結案卡 | 零拒收硬擋的回看週期 |
| rule_confirm_days | 90 天 | 規則檔 `last_confirmed` 過期即印（§十一） |

**管道**（框架提供，判斷不在框架）：`wf:note` 留言（任何角色可貼；交回單 finding 標 `note: new` 時由 `review` 動詞產生同樣一則並附 origin）→ `notes` 印候選 → `snapshot` 匯出全部候選與 `last_cited`。

**落點**（條文在填規則時寫）：

| 事 | 落點 | 來源 |
|---|---|---|
| 正式化（提案三格：條文、來源、處理手段；確認者需求方） | `roles/requester.md` §1；提案形狀 `stages/requirement.md` §2 | 需求方 2026-09-04 |
| 升遷 T-→P-→F-（同義判定、誰提誰點頭） | `roles/pm.md` §4 | 決議 §八 |
| 退場（過期候選的處置） | `roles/pm.md` §4 | PM 減重 5 |
| 守衛化的唯一入口與預設值 | `core/tiers.md` §紅線；`roles/requester.md` §1 | 需求方 2026-09-04 |
| 零拒收硬擋的回看 | `roles/pm.md` §4 | C13 |
| 回應三值與 `notes` 欄 schema | `core/handoff.md`、`core/card-schema.md` | §八、§六 |

## 十三 · 填規則的順序與停損

順序（每步一個 PR；執行＝PM，查核＝Codex 跨實體，sign-off＝需求方；CLI 那步例外：執行者另派、PM 不兼）：
0. **封存**（需求方 2026-09-04 裁定必為第一步）：舊 canonical、stage-rules、templates、tier-rules、MODEL_ROUTING、ADOPTION、docs 設計文件、舊 `cli/` 與其測試、舊 `scripts/` 掃描器整包移入 `archive/rules-2026-09/`；CI 換成只跑新 CLI 測試的最小 workflow；`archive/issues/` 重新納入 git。三個入口檔已先清成 stub。
1. `core/` 八檔，`glossary.md` 最先（其他檔的每個詞都要能在表內找到）
2. `roles/conduct-common.md` → 四角色檔
3. 五階段檔（研究住模組）
4. `modules/` 逐一寫 §九清單所列每個模組的宣告區塊（條文可先空），⛔ 不另記總數
5. README、ADOPTION 重寫
6. 新 CLI `wf`（另一張 T3 卡；測試只測 GitHub 寫入與轉移表；fake gh 錄放）
7. aiwf 新 Project 建立、舊卡關閉＋移出、舊檔移 archive

停損：任一檔超過 §二上限 ⇒ 停下拆；`cli/src` 超過 3,000 行 ⇒ 停下重看分桶；第 6 步超過 3 輪查核 ⇒ 需求方裁定是否縮射程。三個數字都是設計值。

## 十四 · 本檔的驗收條件（什麼結果會推翻它）

1. `extract/00-consolidated.md` §十的 20 條空洞與 §八的 3 項新洞，每條在 §十一都有一個落點；缺一即不過。
2. `00-consolidated.md` §二–§六每一列「留」的規則，都能對到 §一目錄樹裡恰一個檔；對不到即不過。
3. §四轉移表每個狀態都有出邊（停止除外），每個階段都能到結案；手驗，Codex 複驗。
4. 本檔不含任何一句祈使句形式的規則正文（只含形狀）；含即不過。
5. §三第零條與 §七每一列硬擋一致：硬擋只落在資料有效性、寫入順序、平台委託三類；不一致即不過。

## 十五 · 原未定五題（需求方 2026-09-04 裁定）

- 卡ID `<AREA>-<NNN>` 不帶 slug（§十）。
- 新 CLI 名 `wf`（§一）。
- 研究與量測全文的落點＝`wf:log` 留言（核心留言標頭，§十）；`log-comments` 模組取消（§十一）。
- Project 投影欄五個（§六）。
- 第 3 次退回的預設處置已進 §四與 §十一。


## 十六 · Codex R1 裁決的處置

第一輪（留言 5535340214）：
- R1-01：`停止` 移出核心值域，改為結案階段 delta（§四）。
- R1-02：`--ruling` 缺席一律印；只有已給但不存在或作者不符的 URL 才拒（§三、§四、§五、§七、§十一）。

第二輪（被審 d6a8caf）：
- R1-01：C10 計數被第零條取代一事補進決策紀錄「補充裁定」，骨架 §三改為引用它，不再自行重判。
- R1-02：H13 恢復為資料有效性硬擋，含 C2 三含意（§三）。先前降為印是把 JSON 欄位間一致性誤判成內容判讀。
- R1-03：注意事項回應三值的唯一居所定在 `core/handoff.md`，交回單 schema 引用（§八、§十二）。

需求方提議後補：§十八 `core/glossary.md` 通用語言，列為填規則第 1 步第一檔（fe71a05 後）。

第十一輪（被審 cd45361，R1 過）：
- R2-01：§十二 整節改寫為資料形狀、參數表（`core/params.md`）、管道、落點四塊，條文全部移目標檔。

PM 自審（3e613ce 後）：§五 tiers 改為固定節＋來源；§十 卡ID、專案層位置、§十一 專案層級別、§十五 wf:log、§九 模組 verbs 欄六處改形狀。

第十輪（被審 cd09b1d，R1 過）：
- R2-01：§六 schema 升版、§八 留言不可變、§十二 退場、§十八 詞表違規四句改為形狀＋落點，條文移目標檔。

Gemini 第三輪（被審 4a09c8c）：APPROVE，findings 無；詞表補六列（db_scope、trailer、falsifier、sign-off、self_run、attribution）。

第九輪（被審 a8e1722）：
- R1-01：`resource-lock` 的 predicate 改為「派工當下板上進行中且 owner 不同的卡 ≥1 張」，事實來源＝Project 投影欄；`modules.json` 只放參數。

第八輪（被審 b378bfe）：
- R1-01：H3 改為「合併方式由專案層 `merge_method` 決定、平台設定強制」；aiwf 選 squash 是專案層值（C3）。
- R1-02：§九每模組唯一 predicate＋事實來源；maintenance 的「排程、爬蟲、告警」降為需求階段注意事項；db-contract 是唯一 AND。

Gemini 第二輪（被審 ce651ca，留言 5536360697）：
- R3-01：K10 補進 §三重判表，硬擋 14／CLI 9。
- R4-01：重複的 §十七 改為 §十八。
- R4-02：來源標記改 `<來源>`，不用「層」。
- 詞表補五列（來源、七動詞、未驗三分類、回應三值、投影欄）。

第七輪（被審 702daf7）：
- R1-01：§三 `notes` 改為一份清單、四個來源，逐字決策 11 順序。
- R1-02：`brief` 輸出每段首行 `[來源: …]`；派工單標同形（§七、§八）。
- R1-03：升級計數鍵改同卡同 iteration 累積，不分階段不要求連續（§四、§九）。

第六輪（被審 a5dbe68，R1 過、R2 五條）：
- R2-01：§七寫入契約與 §十二正式化／守衛化改為節名＋來源指向，條文移到目標檔。
- R2-02：缺陷路徑三條核心各給落點，FIX 後綴歸命名洞。
- R2-03：`.github/ISSUE_TEMPLATE/list-intake.yml` 進目錄樹，四欄改 `json wf-intake` 區塊，schema 住 card-schema §intake。
- R2-04：規則檔 `last_confirmed` frontmatter＋`snapshot` 印過期清單。
- R2-05：投影欄逐欄 `max_bytes`；多欄寫入順序契約住 verbs §寫入契約。

第五輪（被審 80e3c46）：
- R1-01：§二理由連結只指 `archive/`；萃取稿定位為輸入、填完移入 archive（決策 9）。
- R1-02：`edit` 硬擋加 `source_issue`；§六的兩欄標「建後不可改」（C11）。

第四輪（被審 61feebf）：
- R1-01：§六補 `notes` 欄；§七 `notes` 動詞改為四個來源。
- R1-02：§一、§七補第七動詞 `review`：驗交回單 schema 與 H13 一致性、貼成留言、不動狀態（C14）。
- R1-03：§十三第 4 步改逐名引用 §九，不記總數。

第三輪（被審 d8fc77b）：
- R1-01：交回單人填欄與 schema 補未驗清單三分類（§八）。
- R1-02：resource-lock 啟用條件收回決策 6「同時 ≥2 執行者」（§九）。
- R1-03：研究階段改為模組 `research`（與部署、維護同形），`不可判定` 隨它存在；C6 不動（§一、§四、§九、§十一、§十三）。

## 十七 · 對 #177 規劃審 38 個 P1 finding 的自審

已對照並修正 6 處：狀態值域一處兩答（P1-11／34）、硬擋計數三居所（P1-23／38）、CLI 讀留言的範圍（P1-27）、schema 升版規則（P1-30）、留言併發（P1-33）、填規則各步 owner 與本檔驗收條件（P1-14／22／35）。未套用：producer 可重現（P1-29／32／37）——本檔無 artifact。

## 十八 · `core/glossary.md` 的內容（通用語言；需求方 2026-09-04 提議）

每列＝一個詞。四欄：詞 · 一句定義 · ⛔ 不是什麼 · 禁用同義詞。⛔ 不放理由。消費者三個：CLI enum 與 Project 選項名（取「詞」欄字面）、規則檔正文、審核提示；禁用同義詞的違規判定條文住 `roles/conduct-common.md` §2。種子（填規則時逐列補定義）：

| 詞 | 涵蓋 | 禁用同義詞 |
|---|---|---|
| 卡、清單項 | 在板 issue／不在板 issue | Backlog、task、票 |
| 階段（8） | 需求…結案 | 站、phase、gate |
| 狀態（核心 5＋阻塞；模組加值） | 待辦…退回、阻塞、停止、升級、不可判定、運行中 | 交付狀態、部署狀態、Status |
| 轉移、轉移記錄 | `move` 的一次寫入與其留言 | 事件、event、handoff |
| iteration | 卡進入執行階段的次數 | 輪次、輪、round |
| 查核輪 R1–R4 | 前提／射程／內容／影響面 | 輪次、pass |
| 注意事項、加嚴層級 F-／P-／T- | 一份清單、四個來源 | 踩坑清冊、清單（作為注意事項的同義）、層（作為來源） |
| 硬擋、印、語意 | 機械層三類行為 | 守衛、閘門、偵測器、拒收（作為類別名） |
| 模組、啟用條件 | opt-in 機制與其條件 | 外掛、plugin、功能旗標 |
| 裁定、裁決 | 需求方的決定／查核者的結論，皆為留言 | 批准、核可、sign-off（除 T4 外） |
| 派工單、交回單、裁定單 | 三份交接文件 | 派工包、派審詞、交付報告、結案報告、狀態變更裁定單 |
| 需求方、PM、執行者、查核者 | 四角色 | 祕書、Coordinator、第二 PM、人工查核、規劃者 |
| 實體、家族 | 跑角色的 session／模型家族 | 帳號、人、instance |
| 級別 T0–T4、能力層級 | 風險軸／模型能力軸 | tier（中文語境）、難度、等級 |
| 紅線 | 至少 T3 的變更域 | 敏感、高風險 |
| 核心痛點、驗收條件、非射程、服務的原始目標 | 卡面四個判準欄 | 目標、需求、範圍、scope |
| 封存、撤銷、停止 | 三個離開動作 | 關閉、刪除、歸檔（作為封存以外的意思） |
| 留言標頭 wf:* | CLI 與人留言的首行 | marker、事件型別 |
| 來源（四個）：core／module／project／card | 清單與交接文件的合成來源 | 層（作為來源）、layer |
| 七動詞 open／move／edit／notes／brief／review／snapshot | CLI 的全部入口 | amend、改卡、handoff、assign、pitfalls、踩坑、verdict（作為動詞） |
| 未驗清單三分類 cannot／skipped／deferred | 驗不了／沒去驗／刻意不驗 | 未驗（裸列）、TODO |
| 回應三值 followed／not_applicable／found | 已遵循／不適用／發現 | 已檢查、已遵守、N/A |
| 投影欄（5）：階段／狀態／級別／owner／卡ID | Project 上由 CLI 回寫的欄 | 看板欄位、Ledger 欄 |
| db_scope | 卡對資料庫的變更範圍 enum none／read／write／schema／data-migration；後兩者連動 T4 | db_permission、資料庫權限 |
| trailer | commit 訊息末端連續的結構化標籤區塊（Requested-by、Planned-by、Implemented-by、Reviewed-by） | footer、git-tag |
| falsifier | 交回單逐條 AC 的證偽條件 | 反測（保留給統計紅線模組的對抗性反測）、反向案例 |
| sign-off | 需求方對 T4 卡的最終授權裁定 | approve、核准 |
| self_run | 交回單內實跑指令與原始輸出 | 本地測試、手動驗證 |
| attribution | finding 責任歸屬 enum executor／coordinator／planner／reviewer／external | 責任方、責任者 |

## 未驗

- 目錄樹與節次是設計，未經任何試填；行數上限是估計。
- 轉移表未跑可達性檢查；模組 delta 格式未實作。
- 卡面 schema 的欄位集由 00 §四 open 段推得，未與 cpbl 現有 118 張卡的欄位對照。
