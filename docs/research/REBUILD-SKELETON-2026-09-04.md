# 新框架骨架（2026-09-04）

> 自舉第二份文件（決策 10）。用途：定下**目錄、每個檔的固定節與行數上限、狀態機、卡面 schema、動詞、交接文件、模組宣告格式、命名規則**，讓之後「填規則」時每個檔的密度一致、每條空洞有落點。
> 輸入：`REBUILD-DECISIONS-2026-09-04.md`、`extract/00-consolidated.md`、`extract/07-conflicts.md`。引用格式沿用 `01#19`、`H7`、`S4`、`K2`、`C3`。
> ⛔ 本檔不寫規則正文；規則正文在「填規則」步驟寫進各檔。本檔經 Codex 跨實體審＋需求方 sign-off 後生效。

## 一 · 目錄樹

```
README.md                  L0 入口：一分鐘心智模型＋查詢指令；⛔ 不列會變的東西（04#158）
core/                      定義層（C8）。只放定義與機械語意，⛔ 不放理由
  state-machine.md         階段、核心狀態值域、核心轉移表、模組 delta 合成規則
  tiers.md                 T0–T4 表、紅線域、能力層級判準、單向門、缺陷級別套用
  card-schema.md           卡面 fenced JSON 欄位集（JSON Schema 逐字）
  verbs.md                 六動詞：open / move / edit / notes / brief / snapshot
  handoff.md               三份交接文件的段落表＋交回單 JSON schema
  naming.md                卡ID、分支、檔名、留言標頭的命名規則
stages/                    一階段一檔；部署與維護住模組
  requirement.md  research.md  planning.md  implementation.md  review.md  closeout.md
roles/                     一角色一檔＋共用一檔
  requester.md  pm.md  executor.md  reviewer.md  common.md
modules/                   每模組一目錄；module.md 開頭是宣告區塊（§九）
  resource-lock/  escalation/  log-comments/  deploy/  maintenance/
  pitfalls-13/  identity/  snapshot/  db-contract/  initiative/  stat-redline/
cli/                       新 CLI（名稱 `wf`，與凍結的 `wfcli` 區分）
archive/                   舊 canonical、stage-rules、templates、docs、cli、issues；唯讀
docs/research/             決策紀錄、萃取、骨架（本檔）
```

採用專案側（不在本 repo）：
```
.wf/modules.json           啟用的模組與參數（§九）
.wf/stages/<階段>.md        專案層注意事項 P-<階段>-NN（只能加）
.wf/tiers.md               專案層加嚴（只能往上綁）
.wf/contracts/             模組要求的專案填空（DATABASE_CONTRACT 等）
```

## 二 · 每個檔的固定節與行數上限

密度不均是上一版的病（01 空洞、03 空洞）。每種檔固定節次、固定上限；寫不滿就留短，⛔ 不塞理由。理由一律寫成 `→ archive/…` 或 `→ extract/05#n` 連結。

| 檔種 | 固定節（順序不可換） | 上限 |
|---|---|---|
| 階段檔 | 1 目標與產出 · 2 進入／離開條件 · 3 狀態 delta（引用 core） · 4 站內迴圈（①–⑤ 在本站的形狀） · 5 各角色做／⛔ 不做 · 6 注意事項 `F-<階段>-NN` | 60 行 |
| 角色檔 | 1 職責 · 2 紅線 · 3 動作前自檢 · 4 注意事項 `F-<角色>-NN` | 60 行 |
| common.md | 1 操作紀律（實跑、fetch、不截斷、rc、負控、逐字、多居所、驗原件） · 2 書寫紀律（數字帶日期、不寫行號、引用逐字） | 40 行 |
| core 各檔 | 依檔（§四–§八） | 120 行 |
| module.md | 0 宣告區塊（§九） · 1 條文 · 2 該模組加的注意事項 | 80 行 |
| README | 1 心智模型（≤12 行） · 2 角色一句話 · 3 查詢指令 | 40 行 |

每條規則一句祈使句，⛔ 不帶「因為」；⛔ 不出現 ⚠️／⭐／⛔ 以外的符號；⛔ 不寫現況數字（要寫就帶日期，`common.md` 書寫紀律）。

## 三 · 核心迴圈與角色（定案摘要）

- 四角色：需求方、PM、執行者、查核者（決策 5）。第二 PM、人工查核不存在（C4）。
- 每階段五步：① `notes` 印三層清單 ② PM `brief` 派 ③ 交回 ④ PM 對完整性＋判 R1 R2 ⑤ `move`（S8、S9）。
- 查核者判 R3 R4；查核者的裁決同時覆蓋派工單（attribution: coordinator／planner）（C4）。
- 裁決與裁定＝GitHub 留言；動詞只收 `--ruling <URL>`（C12–C14）。

## 四 · `core/state-machine.md` 的內容

**階段**：需求 → 研究* → 規劃* → 執行 → 審核 → 部署* → 維護* → 結案。星號＝可跳過；部署、維護是模組，未啟用時階段計畫的值域裡沒有它（S3、C6）。

**核心狀態值**（C6）：待辦／進行中／待確認／完成／退回＋正交 阻塞。模組可加：`escalation` 加 升級；`research`（核心階段，但「不可判定」值歸研究站 delta）；`maintenance` 加 運行中；結案的 停止 是核心（終態，S6）。

**核心轉移表**（每列＝一條允許的邊；`move` 只接受表內轉移，H7）：

| from | to | 條件 |
|---|---|---|
| 需求／待確認 | 研究或規劃或執行／待辦 | 依階段計畫的下一站；T2+ 不得跳過規劃（S3） |
| 需求／待確認 | 清單（撤銷） | `--ruling`；卡ID 保留、iteration 延續（S6、C5） |
| 任一階段／待辦 | 同階段／進行中 | 派工 |
| 任一階段／進行中 | 同階段／待確認 | 交回 |
| 任一階段／待確認 | 下一站／待辦 | ⑤ 過 |
| 任一階段／待確認 | 同階段／退回 | ⑤ 不過（R2–R4） |
| 任一階段／待確認 | 規劃或需求／退回 | ⑤ R1 不過（S10） |
| 任一階段／退回 | 同階段／進行中 | 再派；進執行時 iteration +1（S7） |
| 任一狀態 | 阻塞 | `--ruling`；記 from |
| 阻塞 | from | 解除 |
| 最後一站／待確認 | 結案／待確認 | 結案報告 |
| 結案／待確認 | 完成 或 停止 | 完成需 H8 收尾；停止需 `--ruling`；兩者皆封存 |

**模組 delta 格式**：模組宣告區塊裡 `transitions.add` 與 `transitions.remove` 各列若干 `{from, to, condition}`；合成＝核心 ∪ add − remove；CI 跑可達性測試（01#57 保留為測試要求）。

## 五 · `core/tiers.md` 的內容

- T0–T4 表：各級最低閘門（01#66–68）。
- 判準：敏感面／可復原性／影響面取最高（03#44）；⛔ 不按難度、估時、檔案數。
- 紅線域：public contract、權限與安全、金流、資料寫入或 migration、production、規則本體；紅線至少 T3，`db_scope ∈ {schema, data-migration}` ⇒ T4（C9）；T4 查核跨家族或使用者 sign-off（H6）。
- 單向門：升自由，降須 `--ruling`（03#31）。
- 缺陷級別套用表（03#45）。
- 能力層級判準：經濟型／主力型／高階型（03#49）。
- 專案層只能加嚴（03#48）。

## 六 · `core/card-schema.md` 的內容

卡面＝Issue body 的一個 fenced JSON 區塊（`json wf-card`）＋人讀散文段。CLI 只讀寫 JSON（決策 1）。

| 欄 | 型別 | 誰填 | 何時必填（`open` 印缺欄） | 誰讀 |
|---|---|---|---|---|
| schema_version | int | CLI | 建卡 | CLI |
| card_id | string | CLI 配（naming） | 建卡 | 全部 |
| source_issue | int | CLI | 建卡 | CLI |
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
| brief | {when, non_scope} | PM | 建卡 | 清單搜尋 |
| spec_version | int | CLI（edit 自動 +1） | — | 派工單、initiative |
| owner | {role, actor} | CLI（move） | — | brief |
| branch | string | CLI（move 到進行中時寫） | — | brief、H11 |
| iteration | int | CLI | — | brief |
| modules | string[]（此卡實際生效的模組） | CLI 由 `.wf/modules.json` 導出 | 建卡 | notes、brief |

未定義鍵 ⇒ fail-closed（H10）。Project 欄位只放 `階段`、`狀態`、`級別`、`owner`、`卡ID` 五個投影欄，全由 CLI 回寫。

## 七 · `core/verbs.md` 的內容

| 動詞 | 輸入 | 硬擋（rc≠0 並寫一則拒收留言，C13） | 印（rc=0） | 寫 |
|---|---|---|---|---|
| `open <issue>` | 清單 issue 號 | 不是 issue、已在板上、鏈深 >2、JSON 鍵不合法（H9、H10） | 缺欄清單、清單留言數與未讀警示（K7） | 建卡 JSON、加進 Project、配卡ID |
| `move <card> --to <階段/狀態> [--ruling URL]` | 目標、裁定 URL | 轉移不在合成表內、終態出邊、進終態前收尾未完成、需裁定而 URL 不存在或作者不符（H7、H8、C12） | 缺欄（阻塞四欄、停止三欄）、merge SHA 是否 main 祖先、CI 狀態、級別下修無裁定、離開規劃時仍有 TODO | Project 欄、JSON owner／branch／iteration、轉移記錄留言（S5） |
| `edit <card> --set <欄>=<值> [--ruling URL]` | 欄與值 | JSON 不合法、改 card_id（H10） | 無裁定連結、審核期修改 | JSON；`edit` 留言；規格欄變動時 spec_version +1；審核期另貼 `edit during review` 留言（C11） |
| `notes <card> [--stage]` | — | — | 三層編號清單（core＋已啟用模組＋專案層＋卡面任務層）＋ pitfalls-13 樣板（若啟用） | 無 |
| `brief <card> --for executor\|reviewer\|closeout` | 角色 | 分支 HEAD ≠ source_sha、SHA 未 push、`merge-tree` 有衝突（H11、K10） | 缺人填段的提示 | 無（輸出到 stdout；PM 貼進留言） |
| `snapshot` | — | — | — | 本機 JSON＋Markdown |

實作規則（05 揭露、K2、K3）：所有檢查在第一次遠端寫入之前完成；每次寫入後回讀；拒收留痕一行；⛔ 不讀散文、⛔ 不產生任何統計數字進文件。

## 八 · `core/handoff.md` 的內容（04 §範本欄位）

| 文件 | 誰→誰 | CLI 填 | 人填 |
|---|---|---|---|
| 派工單 | PM→執行者或查核者 | 卡與身分、核心痛點、驗收逐條、非射程、merge-base SHA、前輪 findings、能力層級建議、注意事項編號清單、副作用入口清單 | 寫入授權、唯讀範圍、實際模型與偏離理由、未驗項（三分類）、本文件落差 |
| 交回單 | 執行者或查核者→PM | 卡與身分、AC 條文、commit 清單、改動面、finding_id | self_run、逐 AC 做法／證據／falsifier、失誤登記或 findings 八欄、注意事項回應、範圍外發現、`review_result`／`core_pain_resolved`（查核者） |
| 裁定單 | PM→需求方 | 事件序、退回理由、findings、merge SHA、CI、四停下條件前三項 | 類別（升級／停止／撤銷／級別變更／結案確認／其他）、四選一各值證據、復活條件、翻案把手、被繞過的閘門 |

交回單 JSON schema＝舊 review-prompt §5 加 `role` 欄；同一 schema 執行者與查核者共用。

## 九 · 模組宣告格式與清單

每個 `modules/<name>/module.md` 開頭一個 `yaml wf-module` 區塊：

```yaml
name: resource-lock
enable_when: 專案宣告同時有 ≥2 個執行者，或共享可寫資源
adds:
  fields: [worktree, lease_expires_at]
  stages: []
  states: []
  transitions: {add: [], remove: []}
  verbs: []            # 只能加旗標，⛔ 不能加動詞（動詞新增須需求方裁定）
  notes: [F-resource-01, F-resource-02]
  handoff_sections: [資源宣告逐條]
project_inputs: [.wf/contracts/CONTROL_PLANE.md]
```

`.wf/modules.json` 列啟用的模組名與參數；`notes`／`brief`／`move` 依它合成清單、段落、轉移表與狀態值域。模組未啟用＝上面每一項都不存在。

| 模組 | 啟用條件 | 收的萃取列 |
|---|---|---|
| resource-lock | 並行 ≥2 執行者或共享可寫資源 | 00 §六 |
| escalation | 同卡同輪退回達第 3 次（誰數：`move` 數同階段連續退回） | 00 §六；05 空洞 7 |
| log-comments | 卡面 body 超過閾值或研究卡 | K8、K9 |
| deploy | 階段計畫含部署 | 00 §六 |
| maintenance | 交付物為排程、爬蟲、告警 | 00 §六 |
| pitfalls-13 | 專案宣告 | 00 §六 |
| identity | 多實體共用同一帳號 | 00 §六 |
| snapshot | 狀態面在 GitHub | 00 §六 |
| db-contract | 專案有 DB | 02#45–50、04#129–132 |
| initiative | 卡有父卡 | 02#10、04#44 117–120 |
| stat-redline | 卡屬統計／ML／資料正確性 | 04#135–138、03#57 |

## 十 · `core/naming.md` 的內容（新；舊規則只有四條，00 空洞 9）

- 卡ID：`<AREA>-<NNN>`。AREA 是專案層封閉枚舉（aiwf 建議：WF、CLI、DOC、OPS）；NNN 由 `open` 依 repo 遞增配發，⛔ 不帶語意 slug（slug 住 issue 標題）。修復卡 `<原卡>-FIX<n>` 保留。
- 分支：`wf/<card_id>`；由 `move` 到進行中時寫回卡面。
- 留言標頭：轉移記錄 `wf:move`、修訂 `wf:edit`、拒收 `wf:reject`、裁決與裁定由人貼但首行固定 `wf:verdict`／`wf:ruling`。
- 規則檔：kebab-case、無日期；研究與紀錄檔：`docs/research/<YYYY-MM-DD>-<slug>.md`。
- 專案層檔一律在 `.wf/` 之下。

## 十一 · 空洞落點（00 §十的 20 條）

| 空洞 | 落點 |
|---|---|
| 部署、維護 0 條 | 模組 `deploy`、`maintenance`；條文從 ADOPTION 五行與 01#45 49 60–62 73 起草，其餘留空標「待實例」 |
| 缺陷路徑 | 橫切：三條核心進 `core/verbs.md`（無專屬卡種）與 `core/naming.md`（FIX 後綴）、`roles/common.md`（未開卡走 trailer）；其餘分住 requirement／planning／implementation（03 §缺陷路徑） |
| 需求方角色薄 | `roles/requester.md`：裁升級、撤銷、停止、T4 sign-off、結案 ④、清單條件 2；每條一句 |
| 待審清單無形狀 | `stages/requirement.md` §2 進入條件＋`core/verbs.md` open 的印；收件動詞⛔ 不加（清單項＝手建 issue，四欄由 issue template 承載） |
| 交付報告 schema 散 | `core/handoff.md` |
| 一卡一分支無明文 | `core/naming.md`＋`core/verbs.md` move |
| 資源宣告寫法 | `core/card-schema.md` resources 欄；文法在 db-contract／resource-lock |
| 退回上一站條件 | `core/state-machine.md` 轉移表 R1 列＋`stages/review.md` §4 |
| 命名與目錄 | `core/naming.md` |
| 研究站討論回合出口 | `stages/research.md` §4：討論以一則留言收口，`move` 收該 URL |
| 停止裁定由誰 | `roles/requester.md`；`move` 要 `--ruling` |
| Design gate 記錄位 | `stages/planning.md` §1：設計判斷寫進 verification 欄；N/A 寫理由 |
| 規則文件自身過期 | `roles/common.md` 書寫紀律「數字帶日期、不寫行號」；⛔ 不建掃描器 |
| 查核者資訊邊界 | `roles/reviewer.md` §1：只看派工單與分支；派工單就是全部 |
| 常態誰 merge | `stages/closeout.md` §4：PM 在四停下條件內直行（03#93） |
| Log 移留言 | 模組 `log-comments`＋核心留言標頭（§十） |
| 升級梯 JSON 形狀 | 模組 `escalation` 宣告 `fields: [escalation_count]`，由 `move` 數 |
| 專案層級別數字 | `core/tiers.md` §專案層：只能文字加嚴，數字⛔ 不開放 |
| 簡介必填時點 | `core/card-schema.md`：建卡即必填（印） |
| 必填欄集中 | `core/card-schema.md` |

05 揭露的三個新洞：封存與釘死路徑守衛互斥 → `stages/closeout.md` §2「封存前跑全套」；Project TEXT 1024 bytes → `core/card-schema.md` 註明投影欄只放五個短欄；升級計數誰數 → escalation 模組由 `move` 數。

## 十二 · 注意事項的生命週期

- 三層：框架 `F-<階段|角色>-NN`、專案 `P-`、任務 `T-`（卡面 JSON `notes` 欄）；累加不覆寫、只能加嚴（B1）。
- 來源：05 反覆失誤表（17 形狀）與 03 保留的 49 條是第一版母體。
- 退場：每條記 `last_cited`（最近一次在交回單 findings 的 `note_id` 被引用的卡）；連續 20 張結案卡未被引用 ⇒ 移到 `archive/notes/`。數字 20 是設計值，⛔ 不是量測值。
- 升遷：同一條在 3 張卡的 T- 出現 ⇒ P-；跨專案 ⇒ F-。判定是語意比對，由 PM 提、需求方點頭。

## 十三 · 填規則的順序與停損

順序（每步一個 PR，Codex 審）：
1. `core/` 六檔（定義層先定，其他檔才有東西可引）
2. `roles/common.md` → 四角色檔
3. 六階段檔
4. `modules/` 十一個宣告區塊（條文可先空）
5. README、ADOPTION 重寫
6. 新 CLI `wf`（另一張 T3 卡；測試只測 GitHub 寫入與轉移表；fake gh 錄放）
7. aiwf 新 Project 建立、舊卡關閉＋移出、舊檔移 archive

停損：任一檔超過 §二上限 ⇒ 停下拆；`cli/src` 超過 3,000 行 ⇒ 停下重看分桶；第 6 步超過 3 輪查核 ⇒ 需求方裁定是否縮射程。三個數字都是設計值。

## 十四 · 未定（Codex 審與 sign-off 時要答）

- 卡ID 是否採 `<AREA>-<NNN>` 而不帶 slug。
- 新 CLI 名稱 `wf`。
- `log-comments` 的啟用條件用 body 閾值還是一律啟用。
- 五個 Project 投影欄是否夠（view 只靠它們篩選）。
- `escalation` 未啟用時，同輪第 3 次退回的預設動作（決策「預設升級①換人、需求方否決」要住哪）。

## 未驗

- 目錄樹與節次是設計，未經任何試填；行數上限是估計。
- 轉移表未跑可達性檢查；模組 delta 格式未實作。
- 卡面 schema 的欄位集由 00 §四 open 段推得，未與 cpbl 現有 118 張卡的欄位對照。
