# 第三輪重構決策紀錄（2026-09-04）

> 需求方（ruan6047）與 PM（Claude Fable 5.1@Claude Code）grilling 逐題定案。
> ⛔ 非生效條文。它是「萃取」與「骨架」兩份文件的輸入。
> 依決策 10，本紀錄與萃取、骨架兩份文件不開卡；Codex 跨實體審一次，需求方 sign-off 後 merge。

## 起點

三條診斷成立，證據在 repo 自己身上（量測基準 `d729830`，2026-09-04）：

- 機械判了不該判的：cli/src 20,255 行對規則本體 3,778 行；拒絕點約 212 個（regex 估計）。W3′ 為收斂而開，src 反而 +15.3%。
- 該機械化的傳遞是手工的：沒有動詞在進入階段時印注意事項；五份交接文件信封手抄；254 次裁決由 PM 代錄。
- 自己造數字再修量測器：8 支掃描腳本 5,967 行＋測試 8,121 行；規劃審 #203–#211 九個 PR 修散文數字掃描器；W3′ 七輪有三輪修量測器。

## 第零條・框架精神（需求方 2026-09-04 定，取代 ROADMAP §0 目標 1）

**CLI 提供資訊清單，AI 判斷。CLI 只確認清單有沒有填，⛔ 不做內容判讀。**

- 舊判準「防止低級事故，判準是有機械執行者擋下」有問題：它把「機械執行者越多越好」合理化，前兩輪 CLI 就是這樣長大的。
- 機械層只剩三種：印清單、確認有沒有填、資料有效性（JSON 合法、轉移在表內、SHA 存在）。平台層（ruleset、CI）擋不可逆事故。
- 判斷（對不對、該不該、算不算敷衍、要不要成為規則）一律由人或執行的 AI 做；AI 可列，正式化須人確認並附處理手段；守衛預設不做。
- 三目標並列：可稽核、防低級事故、流程順暢；前兩項不得以犧牲第三項達成（沿 #177 brief「服務的原始目標」；PM 2026-09-04 補寫，需求方 sign-off 時確認）。

### 第零條之下廢止或改寫的舊條文（需求方 2026-09-04 點名清查）

偏移兩種：把判斷推回機械（「沒有執行者就不算」）、把形式檢查當內容檢查（「格數不符＝退回」）。

| 條文 | 在哪 | 處置 |
|---|---|---|
| 目標 1 判準「有機械執行者擋下才算；偵測器不算」 | ROADMAP §0 | 廢止 |
| 開卡檢查 2「執行者是誰？靠人記得就是目標 3」 | ROADMAP §0 | 改「資訊在哪裡印、誰判」 |
| 「資料不完整即退回」 | ROADMAP §1 | 改「印缺欄，收件方判」 |
| 「唯一的執行面：CI」「需要牙齒的偵測器等的是 ruleset」 | ROADMAP §2 | 留「偵測器不得宣稱已預防」，其餘刪 |
| 七處「這一條沒有機械執行者」 | ROADMAP §1.5 §3 §3.5 | 刪；沒有執行者是常態 |
| 「§6 文字不改，恢復 merge 即重新生效」 | ROADMAP §3.5 | 刪休眠條款；C3 改 ruleset |
| 「修法草案在 #16 C28」錨點 | ROADMAP §3.6 | 移 archive |
| 驗收政策表「blocking 全屬細節 → 驗收」 | ROADMAP §4 | C2 取代 |
| 「程式碼與文件衝突時以程式碼為準」 | canonical 檔頭 | 改「卡面與 core/ 定義為準；碼實作它們」 |
| 踩坑清冊「CLI 驗非空」「格數不符＝退回」 | canonical §6.4、stage-rules §6 | 改印，回應由查核者看 |
| 「先證工具會響」「敘述不承載現況數字」 | pm-conduct §四 | 紀律留 common.md，⛔ 配掃描器 |
| 「指不出執行者的規則寫成約定，不得寫成強制」 | handoff-contract §3.2 | 改「規則一律是約定；硬擋只限不可逆與平台層」 |
| 「不得寫恆真的身分驗證條文」 | ROADMAP §1 | 留，進 common.md |
| finding 處置順序、不因 finding 存在就開卡 | ROADMAP §5 | 留，進 requester.md |

## 決策

| # | 題 | 定案 | 一句理由 |
|---|---|---|---|
| 1 | 新 CLI 靠什麼不再長回去 | **結構**：完全不讀卡面散文，只讀寫 fenced JSON 與 Project 欄位，沒有 markdown parser | 讀不到的判不了；前兩輪長出來的 card.py／brief.py／card_face.py／resources.py 全是散文解析 |
| 2 | 服務誰 | **通用框架**，但通用性落在擴充點與啟用條件，不落在預建機制 | 需求方裁定 |
| 3 | PM 判不判內容 | **PM 判 R1 前提與 R2 射程；查核者判 R3 內容與 R4 影響面** | 分離效力來自實體不是判準（#165 實證）；09-01 收件初審已是這方向 |
| 4 | 通用怎麼表達 | **最小核心＋模組（opt-in）**：模組各帶啟用條件，條件不成立就不存在 | 兩個 repo、同時 1 張卡在動；opt-out 等於為零使用者付全額維護 |
| 5 | 核心含什麼 | 見下節 | — |
| 6 | 資源／分支／工作區 | 資源**宣告**核心欄位；資源**互斥檢查**模組（啟用條件：同時 ≥2 執行者）；一卡一分支核心；worktree 模組 | 互斥實測 13 對只攔 1 對；分支是 PR 與 merge 的載體 |
| 7 | 舊看板 | **aiwf 開新 Project；#4 留給 cpbl 不動**；舊 wfcli 凍結不再改 | 非終態 55 張沒有一張在流動，搬 0 張比搬 55 張安全 |
| 8 | aiwf 舊卡 | **截取價值後關閉＋移出 Project**，⛔ 不硬刪 issue；舊資料整包封存；卡號規則重頭開始 | docs 引用跟著 issue 號碼；硬刪由需求方在 UI 自行決定 |
| 9 | 規則本體 | **重寫**。先萃取舊規則、先定骨架再填規則、一階段一檔一角色一檔、每條規則一句「做什麼」，理由與來歷用連結指 archive | 密度一致；角色只讀自己那份；規則不再帶事故史 |
| 10 | 自舉 | 萃取與骨架兩份文件**不開卡**：各一分支，Codex 審一次，需求方 sign-off 後 merge。授權⛔ 不涵蓋 CLI 碼、⛔ 不涵蓋刪卡 | 兩份產出是文件，舊 CLI 的閘門對它們不承重 |
| 11 | 文件與 CLI 分工 | 獨立文件是事實來源；`brief` 只組合不創作，DI 順序＝框架核心 → 已啟用模組 → 專案層 → 卡面，累加不覆寫，每段標來源 | 同一條只准住一處；規則不得住進程式碼 |
| 12 | 缺陷路徑 | 舊版寫得薄且不在階段計畫值域；骨架階段決定它是階段還是流程 | 需求方點名 |

## 核心（決策 5，需求方確認）

1. 看板＋卡＋待審清單（issue 在不在板上）
2. 單一寫入通道：`open` / `move` / `notes` / `brief` / `snapshot`；其後需求方裁定加入 `edit`（補充裁定 B3）與 `review`（C14），共七動詞
3. 階段計畫＋轉移表（開卡宣告要跑哪些階段，`move` 驗轉移合法）
4. 級別 T0–T4＋能力層級，紅線跨實體查核
5. 四個角色：需求方、PM、執行者、查核者
6. PM 判 R1 R2，查核者判 R3 R4；交付報告含 self_run 與未驗清單
7. 注意事項單一份清單（含退場規則），一套三值；由四個來源合成（決策 11）
8. 資源宣告欄位；一卡一分支

## 模組（各帶啟用條件，條件由骨架文件寫）

資源互斥與 worktree 註冊、升級梯、Log 移留言、部署階段、維護階段、13 族踩坑清冊、身分自述、每日快照。

## PM 減重（決策 3 的配套，需求方確認方向）

1. 查核者拿工具，`brief --for reviewer` 產派審詞、`review` 由查核者自己寫回，PM 不再代錄
2. PM 正式判 R1 R2
3. 第二 PM 角色刪除（＝查核者套在 PM 產出上）
4. 需求方裁定點改預設值＋否決（同一 iteration 內第三次退回預設升級①換人；T4 sign-off 保留）
5. 注意事項加退場規則（連續 N 張卡未被 finding 引用即退休）

## 補充裁定（2026-09-04，萃取後）

- 萃取稿不經 Codex 審；需求方掃 `extract/00-check.md` 兩張單並裁 H4（CI 必備 secret scanner）、B1（DI 累加規則留、reader 段砍）、B3（加 `edit` 動詞）。
- 衝突 C1–C14 依 `extract/07-conflicts.md` 三輪研究後的建議全部採納。要點：PM 判 R1；open blocking 或 core_pain no ⇒ 退回；aiwf ruleset 加線性歷史、只留 squash；不設第二 PM，查核者查 PM 產出；撤銷＝`move --to 清單`；核心狀態值只留通用 5＋阻塞；加 `conduct-common.md`；加 `core/` 定義層；`db_scope` 核心欄、紅線住 tiers；`edit` 全 JSON 欄可改、留言留痕、審核期另貼留言；裁決與裁定＝留言，動詞收 `--ruling URL`；硬擋拒收寫一行留言。
- 骨架文件才走 Codex 審＋需求方 sign-off。
- **第零條與 C10 的關係**（需求方 2026-09-04 定第零條後、PM 據以重判、Codex R1-01 要求回寫）：第零條取代 C10「20 條」的計數；硬擋只落在資料有效性、寫入順序、平台委託三類，逐條重判表以骨架 §三為唯一清單。需求方 2026-09-04 確認。

- **骨架 §十五未定題（需求方 2026-09-04 裁定，採 Gemini 審查答案）**：卡ID `<AREA>-<NNN>` 不帶 slug；新 CLI 名 `wf`；研究與量測全文一律進留言（不是模組，是核心留言規則）；Project 投影欄五個（階段、狀態、級別、owner、卡ID）。

- **封存是正式開始的第一步**（需求方 2026-09-04）：舊規則檔、舊 CLI 與測試、舊掃描器一起移入 archive，CI 同步換新；自舉期間只清空三個入口檔、其餘加凍結標頭（乙案，避免改凍結中的測試）。

- **量詞統一**（需求方 2026-09-04；同日乙案修訂）：「單一份清單」講輸出（執行者只收到一份、一套三值）；「四個來源」講合成（框架核心、已啟用模組、專案層、卡面，逐段標來源）。「層」⛔ 禁用於清單的輸出與來源計數（「單層」「三層」「四層」一律改掉）；架構詞「核心／專案層／卡面」與加嚴層級 F-／P-／T- 照用。

- **硬擋收縮（需求方 2026-09-04 乙案，審核 19 輪後）**：硬擋只留「寫壞資料」的守門——JSON 合法、轉移在表內、終態無出邊、SHA 在遠端、裁定 URL 存在、鏈深與 open 入口，加平台委託五條，共 11。H5 一人一角、H6 跨家族、H13 裁決一致性、K10 merge-tree、KR 作者比對一律降為印，判斷交 PM 與查核者。需求方同日指示「先自審、⛔ 不再擴 CLI」後，PM 自審再收：H5 H6 因核心 CLI 不留 `roles` 資料而降為 PM 注意事項（不印）；砍 `roles`／`counters`／`modules`／`origin` 欄、`--family`、`.wf/actors.json`；`review` 不自動產生 note；`snapshot` 不讀規則檔。需求方再指示「寧願把資訊交給 AI 判斷，比硬寫 CLI 高效且有品質，前提是資訊要足」：H8 與鏈深上限亦降為印，硬擋 9（平台 5＋CLI 4）。需求方 2026-09-04 sign-off 確認。CLI 只讀三種留言區塊（wf-return、wf-ruling、wf-note），其餘留言純散文只寫不讀。

- **代貼裁決標記**（需求方 2026-09-04）：PM 代貼查核者裁決時沿用 C12 的首行標記形式：`代貼裁決・來源：<模型名>@<工具名>・被審 SHA：<sha>`，第二行起為查核者原文，一字不改。理由與 C12 相同：讀者一眼分得出誰判的；加 SHA 是因本輪兩次貼到過期裁決。CLI 不讀首行。

- **`wf:log` 由人貼**（需求方 2026-09-04 甲案）：研究與量測全文＝任何角色用 `gh` 直接貼的 `wf:log` 純散文留言；CLI 不寫不讀，只在卡面欄（如 `grilling`）以 URL 指向。單一寫入通道（決策 5）管的是卡面 JSON 與 Project 欄；⛔ 不為此加第八動詞或旗標。
- **骨架 sign-off**（需求方 2026-09-04）：Codex 第三十三輪（e3f8401）與 Gemini 第五輪（3d10bf8）APPROVE 後，需求方確認硬擋收縮段、三目標段、「設計閘」為 Design gate 正式中文詞、三個模組狀態的 delta、`wf-ruling` 六個 kind、`blocked`／`grilling` 兩欄。骨架定版＝PR #245 合併 SHA。

- **三軸名與禁用詞**（需求方 2026-09-05 甲案）：骨架 §五 的軸名「敏感面／影響面」保留（來歷 tier-rules L58、L60）；§十八 的禁用詞改為限定形「敏感（作為紅線的同義）」「影響面（作為副作用入口的同義）」，並加「三軸」列。⛔ 不改軸名。
- **缺陷一詞**（需求方 2026-09-05）：骨架 §五「缺陷套用表」、§十一「缺陷路徑」用「缺陷」指行為錯誤；§十八 finding 列的禁用詞改為限定形「缺陷（作為 finding 的同義）」，並加「缺陷」列。與三軸名同一處理。
- **owner 投影格式**（需求方 2026-09-05 甲案）：Project owner 欄＝`role:actor`；舊快照的 actor 字串本身含 `@`（如 `Claude Fable 5@Claude Code`），故不用 `@` 分隔。

- **詞表禁用同義詞的收錄判準**（需求方 2026-09-05 甲案）：只收會被當成同一概念的專名（舊制術語、英文名、別檔文件名），⛔ 不收日常詞；日常詞多義用「⛔ 不是什麼」欄。依據：DDD 通用語言是「一個概念一個名字」的共用語言，不是禁字表；量測 199 條中 54 條日常詞在 core 正文命中 111 次、真違規 4 次（誤報率 96.4%），跨實體審因用詞開的 5 條 finding 無一是專名同義。「輪」「人」隨此案不再禁。
- **骨架形狀補記**（需求方 2026-09-05）：第 1 步填規則時為通過可達性驗收與封閉 schema 所定的四個形狀回寫骨架：階段 delta 可減、`only_in_stage`；轉移 `if` 機械鍵；模組欄型別住 `card-schema.md` `$defs/module_fields`；`.wf/contracts` 的 `json wf-contract` 區塊。`tasks/_smoke/` 兩個舊 CLI 煙霧檔一併封存。

- **條文形狀的分號**（需求方 2026-09-05 甲案）：「一條＝一句祈使句」指一條規則一個句子；分號接的條件、例外、指向子句屬同一條，⛔ 不接第二條獨立規則。量測：stages 64 條帶分號者 12 條為真雙規則，全拆會使三個階段檔破 60 行、F- 條目 49→82。roles 與 core 的既有分號寫法照此讀。
- **統計結果解讀通則的居所**（需求方 2026-09-06 甲案）：04#138「第 7、9、10 條適用所有研究結論，不限紅線卡」與決策 4「條件不成立就不存在」衝突；裁定三條通則落 `roles/executor.md` §4（執行者下結論、查核者判紅線與反測結果時皆適用，查核者檔以指向句引用）；`modules/stat-redline` 第 4b 回填時保留紅線卡的具體化版本並指向；骨架 §九 表下同步註記。
- **模組注意事項 id 與宣告對帳**（需求方 2026-09-06 授權 PM 裁定）：模組注意事項 id 依 `core/naming.md` 為 `F-<模組名>-NN`，骨架 §九範例 `F-resource-01` 為筆誤，改為 `F-resource-lock-01`；`adds.notes` 與 §2 條列的 id 集合、順序、前綴由 reachability job 對帳（只比 id，⛔ 不讀條文內容；量測：#261 帶 `notes: []` 通過跨實體審與 sign-off）。
- **詞表限定字樣第二次清理**（需求方 2026-09-06 授權 PM 裁定，四輪研究）：與三軸名、缺陷同一處理，⛔ 不刪條目、⛔ 不改 pitfalls-13 的族名與三值字面。守衛、閘門加「作為硬擋的同義」；已檢查加「作為回應三值的第一值」並新增「13 族三值」列反向禁用 followed／not_applicable／found；不可逆加「作為單向門的同義」；踩坑加「作為動詞名」、踩坑清冊加「作為注意事項的同義」；scope 加「作為驗收條件的同義」；invalid 加「作為拒收類別名」；正確性加「作為完整性的同義」。骨架 §四與 research §0 的「結案報告」改為詞表字面「裁定單」。量測（2026-09-06；語料＝core／roles／stages／modules 全部 .md 含 frontmatter、排除 glossary 自身；禁用詞取 main 4763eaf 起的詞表、剝去限定後的純中文詞）：62 個純中文禁用詞命中 72 次，65 次落在已帶限定的條目且皆合法，7 次落在無限定條目、詞＝不可逆／已檢查／正確性／踩坑／踩坑清冊。
- **模組段合成進交回單**（需求方 2026-09-06 裁定，研究四輪）：`core/handoff.md` 加 `$defs/module_return_sections/<模組名>`，型別居所在 core、宣告留模組（與 `card-schema` `$defs/module_fields` 同型）；派工單與裁定單的模組段歸屬住 `json wf-module-sections`；段名逐字＝模組 `adds.handoff_sections`，由 reachability job 對帳字串集合與歸屬（同一段名⛔ 不同時在交回單與派工單／裁定單），⛔ 不讀內容；佔位模組（deploy、maintenance、pitfalls-13、identity）的段型別先給 string，4b 回填時可改。
- **`move` 的模組通道**（需求方 2026-09-06 裁定）：`core/verbs.md` `move` 的印欄與寫欄各開「已啟用模組宣告」一項（落實骨架 §九「計數由 `move` 在該 iteration 內做」與 §十一「escalation 模組由 `move` 數」）；宣告形狀＝模組 §0 `adds.counters`（`move --to */退回` +1）與 `adds.move_prints`（識別字，語意住模組 §1），骨架 §九 範例同步補記；模組欄只由該模組條文指定的動詞寫。
- **finding 八欄→九欄**（需求方 2026-09-06 裁定）：加必填 `status` enum open／resolved／withdrawn（舊制 04#99 的狀態欄，落 core 而非 escalation 模組，因 `roles/reviewer.md`、`stages/closeout.md`、`core/handoff.md` §3 三條核心條文已引用）；⛔ 不加 `accepted`（其 writer 是內容判讀）。骨架 §八「findings 八欄」同步改九欄。
- **4b 得補該模組條文所引用的 `params` 鍵與種子值**（需求方 2026-09-06 裁定，研究四輪）：射程收在條文回填的因果鏈內，⛔ 不泛化為「4b 得補任何 4a 宣告缺口」；先例＝#263 補 `adds.notes`、#271 補 `counters`／`move_prints`。值的居所仍為專案 `.wf/modules.json`（`core/params.md` non_scope），§0 只放鍵與種子，與骨架 §五「N＝`params.escalate_after`，種子 3」同形。骨架 §九 範例同步補記 `params` 與 `fact_source` 兩鍵（4a 起已在用、§九從未收錄）。
- **全域審查的修正得跨步一個 PR**（需求方 2026-09-06 裁定）：一次跨實體全域審查所產出的同一類缺陷（單一居所、管道閉合、佔位字面），得合為一個 PR 處理，⛔ 不受骨架 §十三「每步一個 PR」的粒度限制；限定條件＝該步已完成、修正不新增規則、PR 說明逐條列出來源 finding。逐步回填仍照原粒度。
- **squash 訊息的居所＝第 6 步 CLI，⛔ 不另立條文**（需求方 2026-09-07 裁定甲案）：萃取 04#145／00 H3 已裁「repo 設定只允許 squash；訊息由 CLI 組」，合併方式那半已落 P3，訊息那半屬第 6 步；PM 一度把它寫成 `stages/closeout.md` 條文並記為「萃取遺漏」，兩者皆誤，已撤。2026-09-06 main 連 15 次 `commit-trailer` 紅的根因＝平台預設 squash 把多則訊息串接、`Co-Authored-By` 被空行切散而違反 P5；歸屬 coordinator、`finding_class` coordination，規則與 CI 皆無誤；歷史⛔ 不追溯改寫（P1）。CLI 完成前 PM 手動 merge 的訊息無執行者＝已知漏洞，⛔ 不以條文或權宜指令代替，落點見骨架 §十三 第 6 步與 `core/platform.md` P5 的備註。
- **T4 查核＝兩位不同家族各一則裁決＋需求方 sign-off**（需求方 2026-09-07 裁定甲案）：原「跨家族查核或 sign-off」的選言改為合取；量詞只住 `core/tiers.md` §1 級別表，`roles/pm.md` F-PM-02 只留獨立性、`stages/review.md` §2 與 `stages/closeout.md` §4 只指向。T3 維持一輪不同實體，⛔ 不加碼。逐字查證後只有 finding id 撞號是真缺口（`core/naming.md` 原形狀只帶 iteration，兩位查核者各自續號會覆蓋彼此的 `status`），加查核序鍵；finding id 改由交回單作者填、`review` ⛔ 不編只印撞號（需求方 2026-09-07 甲″案，四輪研究）——鑑別位只能人給（`wf-return` 四鍵全同、`owner` 單值且派第二位時無第二次 `move`），但純由 PM 填而無人驗會讓裁定單「同 `finding_id` 最後一則」抹掉前一則的 open blocking finding（實跑證）；自填 id 與 `root_cause_id` 同形、`wf-return` schema 一字不動，唯一性是字面比對非內容判讀，且落在印而非硬擋（`roles/requester.md`「⛔ 不擴 CLI 硬擋」）；`owner` 單值與「一張卡一則 `wf-return`」經查皆非缺口，⛔ 不改。前一輪工作流曾把「審核階段重審被記成退回」判為既有缺陷，經逐字查證推翻——`stages/review.md` §2 與萃取 03#135 顯示三次退回觸發升級即設計本意。
- **詞表第三次清理＝刪日常詞，⛔ 不建索引表**（需求方 2026-09-07 裁定）：量測顯示禁用欄有四個機械可證的缺陷（`bug`／`層`／`輪次` 被多列登記且限定不一致、`Backlog`／`backlog` 未併列）。原提案是建「以字為索引的查閱表」，經檢視為過度設計——它服務的是一個沒人跑、且 `roles/conduct-common.md` §2 逐字「⛔ 不擋」的全語料掃描；那四個缺陷不需要索引表就抓得到。正解是回到 2026-09-05 甲案的判準逐字「⛔ 不收日常詞；日常詞的多義靠『⛔ 不是什麼』欄」：`層`（三列）、`輪次`（三列）、`回合`（一列）是日常詞，刪出禁用欄、改由「不是什麼」欄承載；`bug` 與 `Backlog` 是舊制專名該收但各只收一次。2026-09-05 那次清理只掃了正文的日常詞命中，沒查「同字被多列登記」，故未清乾淨。原併案的 `glossary_check.py` CI 對帳已撤（需求方 2026-09-07 甲案）：Codex 判「掛進既有 required job 仍構成新的平台委託」——阻擋條件實際增加三條而 `core/platform.md` 無對應 P6，PM 原本「沒新增 required check 就不是新委託」的推理錯在把判準放在 job 名稱而非能不能擋 merge；且照同日新立的 F-查核者-06 自量，該檢查的母體是一次（四個缺陷本次找到、修完即無）。⛔ 不做，缺陷靠查核者讀 §十八 時發現。
- **`core/handoff.md` 拆為四檔**（需求方 2026-09-07 裁定，骨架 §十三停損「任一檔超過 §二上限 ⇒ 停下拆」）：原檔 120／120 到頂而後續裁定（Project 座標居所、`wf-contract` schema）仍要往 core 加東西。拆法依三份交接文件的作者邊界：`core/handoff.md` 留共通規則與入口（14 行）、`core/dispatch.md` 派工單（35）、`core/return.md` 交回單與 `wf-return` schema（63）、`core/ruling.md` 裁定單與 `wf-ruling` schema（30）。⛔ 不調 §二 上限——上限是設計值，調高等於放棄該停損訊號。骨架 §一 目錄樹、§八 標題、§十二 兩處、§十三 第 6 步 schema 居所句同步；`reachability.py` 的段名對帳改讀兩檔。
- **自舉期文件 PR 的查核家數**（需求方 2026-09-07 裁定）：CLAUDE.md 逐字「文件走 Codex／Gemini 跨實體審」＝至少一家；是否加第二家由 PM 依改動觸及的居所判——動 schema、狀態機、硬擋、詞表結構者兩家，其餘一家。⛔ 不進級別表：級別表依風險分流，改動大小是另一個軸，且大小不可機械判定。
- **finding 的處置前先量母體**（需求方 2026-09-07 裁定）：`roles/reviewer.md` 加 F-查核者-06——寫 `disposition` 前先量被修對象的母體（活的消費者、語料出現次數、失效模式發生過幾次），母體為零時逐字寫「記為已知漏洞」或「待實例」，⛔ 不寫修法。成因＝本輪五個實例：詞表「加嚴層級」列的正名在全語料出現 0 次卻擋掉 34 次命中；誤判率量的是一個沒人跑且 `roles/conduct-common.md` §2 逐字「⛔ 不擋」的掃描；「審核階段重審被記成退回」經查是升級梯的設計本意；執行者無網路出口母體零實例而查核者那條是實測驅動；為 deploy／maintenance 兩個「待實例」模組先立法。五個裡四個已做才回撤。現有條文不涵蓋：`stages/planning.md` F-規劃-03 管規劃時的驗證項目、`roles/pm.md` F-PM-11 管要不要拆卡，皆非 finding 的處置面。PM 側⛔ 不另立，R2 射程本就由 PM 判，本條給的是可拒的依據。
- **「對帳」不入詞表；補的是不等時的結果**（需求方 2026-09-07 裁定甲案）：原案是把「對帳」收進 `core/glossary.md`，經量測判為過度設計——該詞在活規則出現六次（`core/verbs.md`、`core/dispatch.md`、`modules/db-contract`、`modules/snapshot` 兩次、`roles/pm.md` F-PM-08），四種意思都是日常的「兩份記錄比對」，零失效實例，與已撤的詞表索引表同形。真正的洞在 `core/verbs.md` §2 原第 33 行：「下一次動詞先對帳」寫了義務卻沒說不等時怎樣，而硬擋歸屬是 D1–D4 的事、居所在 core，⛔ 不得推給第 6 步實作者定。裁定＝以卡面 JSON 重寫該欄後續跑並印重寫了哪幾欄，⛔ 不拒收：JSON 是源、五欄是導出（`core/card-schema.md` §5 逐字「Project 只放五欄，全由 CLI 回寫」；`roles/conduct-common.md` §1 禁 UI 手改投影欄），重寫是機械操作非內容判讀（第零條）；拒收會把卡鎖死而唯一的人工修法正好被紀律禁止，無復原路徑。印哪幾欄被重寫是為了留痕——若不等的成因是有人手改投影欄，靜默重寫會抹掉證據。機制面（單筆點讀、重試策略）仍屬第 6 步，本裁定⛔ 不寫。原第 33 行同時裝了三條獨立規則，拆成兩條順帶修好骨架 §二甲案的形狀。
- **硬擋類 finding 加問「有沒有別的路能發現」**（需求方 2026-09-07 裁定）：`roles/reviewer.md` §3 原本只問「防誰」，答得出就留；但一個阻擋可以完全正確、也確實有被測物，卻仍然不值得加。既有條文已涵蓋兩半——`roles/requester.md` §1 是硬擋新增的唯一入口（判準 recoverable≠irreversible），回看清單的「零拒收硬擋」是退場機制——缺的是查核者側的提問。分水嶺逐字＝替代偵測路徑：`glossary_check.py` 的四個缺陷人讀 §十八 就看得到，故該砍（2026-09-07 已撤）；#283 的進阻塞邊漏模組狀態展開後有 384 個不可達節點，跨 23 個 commit、5 次跨實體審無人發現，人審實測不是替代路徑，故該留。少了這問兩案分不開。⛔ 不另立 F-查核者-07——§3 那行就是居所，擴一句即可。
- **進阻塞邊的 `from` 改記法 `<非終態>`，正向可達落印⛔ 不落擋**（PM 2026-09-07 依骨架 §四逐字裁定）：骨架 §四逐字「任一非終態」，core `**/待辦|進行中|待確認|退回` 的四值枚舉是括號註解外洩成機械記法，漏掉三個模組狀態（`升級`／`運行中`／`不可判定`）。實測：`aa54f4a`（2026-09-06 第 4a 步）起 128 個合成表中有 92 個帶不可達節點、合計 384 個，9 種形狀全部是 `<階段>/阻塞←<模組狀態>`，核心節點一個都沒有；`universe()` 與解除出邊早已為模組狀態造了阻塞節點，只有進邊沒跟上，反向可達斷言因此照樣印「失敗 0」。期間 23 個 commit（其中 5 個動 `core/state-machine.md` 或 `reachability.py`）全數跨實體審過、無人發現。改記法後 384 全數歸零、原兩項斷言零回歸。正向可達採「印」而非「擋」：`core/platform.md` 逐字「新增平台委託須需求方裁定」，而 2026-09-07 已裁 Codex 的判準＝能不能擋 merge；印不擋 merge 故不構成新委託，且形狀與第零條「CLI 提供資訊清單，AI 判斷」同。Codex R1-01 判本 PR 的 `selftest_blocked_from_covers_module_states` 帶了對正式表的第二合取，會讓「印不擋」的宣稱與實際不符（`reachability` 是 required check，selftest rc≠0 就擋 merge），該判成立，已改為純負控。19 個系統性突變（逐條刪邊、逐條拿掉 `if`、加孤立狀態）實測：main check 捕捉 9、印捕捉 10（其中 5 個 main 抓不到）、該第二合取捕捉 9 而**唯一捕捉 0**——印完全覆蓋它，移除零偵測損失；把正式表改回枚舉時印仍報 384。負控本身的居所＝`roles/conduct-common.md` §1 逐字「附負控輸出」，⛔ 不是新增平台委託。第 2 輪 Codex 再抓一條同源的：PM 把 `ok3`／`ok7` 的預期字串改成「不可達結案」，而該分類取決於正式表有沒有 `<非終態>`，表一改回枚舉這兩個負控就 FAIL、`--selftest` rc=1，正向可達仍間接擋 merge。密封探針複現（正式 check rc=0、印 384、selftest rc=1），改為只驗 `check()` 有沒有捕捉到該節點、⛔ 不釘死診斷分類；修後同探針得 selftest rc=0，而把 `check()` 打壞成永遠回空時 selftest 仍 rc=1。通則＝負控驗的是偵測器有沒有響，⛔ 不驗它響成哪一種診斷；釘死診斷字串會把正式表的性質偷渡成阻擋條件。同一輪量測順帶暴露兩個既有缺口，⛔ 不在本 PR 處理（R2 射程）：`selftest_r1_return_target_unique` 對正式表有 3 個唯一捕捉但 §5 未宣告；`selftest_module_state_in_universe` 唯一捕捉 0，與 main check 完全冗餘。副作用逐字記錄：`**/<非終態>` 讓值域內每個非終態都帶進阻塞出邊，故「無出邊」不再對值域狀態成立（負控 `孤立`／`孤模` 改判「不可達結案」），該分支仍活於阻塞節點與清單（砍解除邊 14 條、砍清單出邊 1 條，實測）。
- **`reachability` job 的斷言集合補宣告**（需求方 2026-09-07 裁定）：§5 逐字只宣告「斷言兩件」，但該 job 實際會讓 rc≠0 的來源有七類——兩件之外還有 `adds.notes` 對帳（`9a3b23a`）、`adds.handoff_sections` 對帳（`90e7ecc`；含段名集合、歸屬、孤兒模組名）、`adds.counters ⊆ adds.fields`（`90e7ecc`）、`--selftest` 的負控（20 條斷言、9 組；PM 前版寫 19 條 8 組是照抄 Gemini 第 1 輪的數字未自數、漏了 `selftest_module_state_without_exit`，Codex 第 2 輪抓出）、以及 `--selftest` 對正式表的兩個正控（`selftest_r1_return_target_unique` 自 `4763eaf` 第 1 步起、`selftest_module_state_in_universe` 自 `aa54f4a` 第 4a 步起）。七類中只有 `handoff_sections` 的段名規則有規則檔居所（`core/dispatch.md`），且該處只寫「CI 對帳」、未宣告會擋。PM 第一版只列五類、漏了 `handoff_sections` 與 `counters ⊆ fields`——第二個是 PM 讀 `check_module_sections()` 時只看函式名沒逐行讀，被 Codex #287 R1-01 抓出（PM 自己在派審題裡問了「有沒有第六個來源」，答案是有兩個）。本次只補宣告、⛔ 不增減任何阻擋——阻擋早已存在，缺的是 `core/state-machine.md` §5 這個居所的準確性（決策 11 單一居所）。量測（#283 的 19 個系統性突變）：`r1_return_target_unique` 有 3 個唯一捕捉（刪 `**/待確認→規劃/退回`、刪 `**/待確認→需求/退回`、拿掉 `if plan_lacks:規劃`），`main` check 全抓不到，價值成立；`module_state_in_universe` 唯一捕捉 0、與 `main` check 完全冗餘，但依 F-查核者-06 其修法的母體是零、且退場機制已存在（`roles/requester.md` §1 回看清單的「零拒收硬擋」），故⛔ 不在本次刪除，交回看清單處理。
- **core 檔行數上限 120→150，停損機制不動**（需求方 2026-09-07 裁定；取代同日稍早「120 維持不調」）：需求方問 120 的來源，查證＝骨架 §十四逐字「行數上限是估計」、`7f11b34` 一次進 repo、萃取稿無舊檔行數量測、決策紀錄無理由——是 PM 估的比例（core＝階段／角色 60 的兩倍），需求方 sign-off 的是整份骨架不是這個數。量測（2026-09-07）：逼近上限的全是 schema／表格檔——`card-schema.md` 115（#288 後 118）其中 fenced 66、`glossary.md` 97 其中表格 85、`research/module.md` 81 其中 fenced 44（純多行陣列排版，壓行即 74）；core 散文最多 57 行（`tiers.md`）、模組最多 41。天花板當初瞄準散文密度，被 schema 撐爆是它沒預想的形狀。需求方裁：機制維持（超過即停下拆）、數字改 150——+25%，`card-schema` 118 仍在視線內、訊號還活著；模組 80 不動。另裁：fenced 區塊不計入（改計法）比改數字更對症，但屬改規則意義、本次不採。
- **刪規則檔檔尾的檔級 `→ archive` 連結，條級連結保留**（需求方 2026-09-07 裁甲）：需求方疑慮＝`roles/pm.md` 檔尾連到 `archive/issues/039.md`（1,474 行舊卡，萃取只取 2 條），pm.md 是高頻核心檔、怕干擾。量測：規則檔共指向 20 份 archive issue，平均 1,210 行、最大 5,265 行；連結全是檔級（pm.md 12 條 F-PM 沒有一條標到哪一段）；沒有任何一處標「來歷⛔ 不是判準」（禁令只在 CLAUDE.md）；本輪 23 份跨實體裁決提到 archive/ 22 次、20 次是「排除／未引用」例行語、當依據 0 次。決策 9「理由的形狀＝連結」保留，但形狀改為條級（釘在該條規則後，如 `core/verbs.md` §2「檢查先於首次遠端寫入（→ #023…）」、`core/state-machine.md` §2）；刪 roles 5 檔 6 行（四角色檔各 1、`conduct-common.md` 2）、stages 5 檔 5 行、modules 9 檔 9 行（deploy／maintenance 原無），共 19 檔 20 行（子項由 `git diff --numstat` 算，Gemini #291 R3-01 抓出 PM 初版子項筆誤）；`core/tiers.md` 指向舊規則 §0 級別表者為特定節、保留。乙（保留＋加「⛔ 不是判準」警語）只加警語、干擾源仍在，不採。PM 初報「15 行 12 檔」是 `grep -c` 只看前 12 檔的誤數，實為 20 行 19 檔。
- **值域獨立檔、骨架歸檔、數值 AI 自己算**（需求方 2026-09-07 裁甲，一包三件；另兩則原則同日）：成因＝同日 7 次「第二居所沒同步」全在值域副本上——量測（PM 以「一行內同時出現 ≥3 個值」計，量級）：階段 8 值被逐字抄約 24 處、11 檔（骨架 8 處）；核心狀態約 10 處、7 檔；級別 6 處；`sensitive` 6 處（`tiers.md` 4）。① `core/enums.md` 一個 `json wf-enums` 區塊＝所有封閉值域的唯一居所（stages／states_core／state_blocked／states_terminal／tiers／roles／sensitive／recoverable／blast／capability_levels／db_scope），每鍵一個 `{"enum": […]}` 可直接當 schema 片段；`core/card-schema.md` 的 inline enum 全改 `$ref` `wf-enums#/<鍵>`（CLI 合成時先具體化）；`core/state-machine.md` 區塊移除 `stages`／`states`／`terminal`、只留轉移與 delta，`reachability.py` `load()` 改自 enums 合成（基底 states＝states_core＋`only_in_stage` 有登記的終態＋阻塞，`停止` 仍由結案 delta 加）；`glossary.md`／`tiers.md`／`ADOPTION.md`／`README.md` 的抄值改指名。需求方補兩點：模組擴充值域只能加值、⛔ 不改基底，今只有 `states` 有實例，其他鍵第一個實例出現再開、⛔ 不預開；詞表配套＝enums 只放字面，核心值的定義住 `glossary.md`、模組加的值住該模組 §1，詞表每個值域鍵一列⛔ 不逐值列。已知殘留：`card-schema.md` `notes.id` 的 pattern `^T-(需求|…)-[0-9]{2}$` 是正則、不能 `$ref`，與 `stages` 是同步點，階段值變動時同 PR 改。② 骨架 `docs/research/REBUILD-SKELETON-2026-09-04.md` 與其審核提示、審核紀錄（`REBUILD-SKELETON-REVIEW-PROMPT.md`、`REBUILD-SKELETON-REVIEW-LOG.md`，用途已完成）一併移至 `archive/research/`（Codex #292 第 3 輪 R4-01：審核提示第 9 行仍以舊路徑為被審物，是活的消費者），core 為唯一居所（乙案：現在退場，非第 7 步後）；第 6／7 步逐字與停損抽成 `docs/research/2026-09-07-step6-spec.md`（第 7 步完成後歸檔）；固定節與行數上限表移 `core/naming.md` §5；`CLAUDE.md`／`AGENTS.md`／審查提示／CI 註解同步。萃取稿⛔ 不動（不在本包）。③ 原則：框架給 AI 用，數值由 AI 自己算、審核時尤其要自己算；只有行數、CI 計數、schema／enum 值、SHA、日期須逐字精確，決策紀錄與 PR 說明的統計數字只需量級、查核者⛔ 不以其精確度開 blocking finding——寫進審查提示與 `CLAUDE.md`，⛔ 不進規則檔。研究資料結構後需求方再裁（2026-09-07「ＯＫ」）：模組擴充值域的宣告鍵採通用形 `adds.enums.<鍵>`，原本直接掛在 `adds` 下的 `states` 改為 `adds.enums.states`（11 個 yaml、`reachability.py`、`card-schema` §1 (a) 同步）——理由＝第 6 步 S03 即將照此形狀寫程式，改在程式前是 11 行 yaml、改在程式後是程式＋yaml＋遷移；每鍵 `{"enum": […]}` 不帶值上 metadata，定義住詞表或模組 §1，Project 選項＝同一次合成的輸出。凍結中的 #288／#289 待本 PR 合併後 rebase：#288 的 `stage`／`state` 改 `$ref`、#289 的骨架 diff 整段消失。
- **第 6 步規格前置（A）：卡面加 `stage`／`state`、模組欄不隨停用失效、模組宣告加 `enable_if`**（需求方 2026-09-07 全甲；astra `gpt-6-astra` 拆片前的現況分析 B01／B06／B08，PM 逐項對原文核實後提三選項各二，需求方全選 astra 的 ①）：B01＝`wf-card` 逐字只有 `stage_plan`、無當下階段／狀態鍵，而 #285 合的 `core/verbs.md` §2「以卡面 JSON 重寫五欄投影」對階段／狀態兩欄無源，且 `move` 驗 D1 須知卡在哪；甲＝加兩鍵、`schema_version` 1→2、1→2 遷移唯一一次以 Project 投影回填，之後 JSON 為源（乙＝兩欄改由 Project 持有，等於開第二事實來源，違決策 11 與詞表「投影欄不是事實來源」）。B06＝`card-schema` §1 (b) 只併已啟用模組的欄，模組因別卡變動而停用（resource-lock）或欄清空（initiative `parent`）後既有模組欄撞 `additionalProperties: false` 被 D3 拒；甲＝併全部宣告模組的欄、結構合法性不隨啟用變（最寬鬆，改嚴是加法）。B08＝11 個 `enable_when` 全是散文，CLI 只能寫死模組名分支（規則進程式碼，違決策 11）；甲＝宣告加 `enable_if`，`kind` 封閉五值恰涵蓋 11 個模組（PM 逐條數：`.wf/modules.json` 列出 ×5、`stage_plan` 含 ×3、欄非空 ×1、欄含值 ×1、跨卡板查 ×1），與狀態機 `if`／`condition` 同型，⛔ 不是規則引擎（乙＝給既有字串定文法＝解析中文）。動詞契約那半（`move` 寫目標 `stage`／`state` 進卡面再回寫投影、`edit` ⛔ 改這兩鍵）住 `core/verbs.md`，與 #289 同列衝突，故落在 #289（Codex #288 第 3 輪 R1-01）。本 PR 新增處的 core 來歷字樣依既有形式只留「需求方 2026-09-07 裁定」、⛔ 不寫 PR 號／astra／B 編號（Codex #289 第 2 輪 R3-01；`core/glossary.md` 既有的「需求方 2026-09-05 甲案」是 main 上先例、不在本 PR 射程）。副作用：`core/card-schema.md` 118 行，core 上限已由 #290 改為 150（需求方 2026-09-07，取代同日稍早「120 維持」）；後續若超過 150 即須拆（骨架 §十三「超過」才觸發）。
- **第 6 步規格前置（B）：`open --area`、執行者首行 `wf:return`、`review` 的 `source_sha` 三種取源、`wf-contract` schema、`snapshot` 對帳例外、`brief --for closeout` 印 squash 訊息、`--actor role:actor`**（需求方 2026-09-07；B02／B03／B04 為需求方裁甲，B05／B07／B09／B10 為 PM 依 astra 的 ① 預設、在本 PR 內裁；B11 修復卡輸入判待實例、⛔ 不寫）：B02＝`naming.md` §1 AREA 取自 `areas` 封閉枚舉而 `open` 無輸入、`wf-intake` 無 `area` 鍵，aiwf 種子四值無法猜；甲＝`open --area`，`areas` 只有一值時隱含；缺而多值或不在枚舉＝無法組合法卡ID，落 D3（乙＝提案者在 `wf-intake` 填，讓提案者裁他不該裁的）。B03＝`naming.md` §3 只有查核者的 `wf:verdict`，`review --role executor` 首行無合法值；甲＝新首行 `wf:return`（乙＝共用 `wf:verdict`，與詞表「裁決＝查核者結論」衝突）。B04＝`wf-return` 要 40 碼 `source_sha` 必填，但 `stages/implementation.md` §4 執行者 `review` 在 PM `move --source-sha` 之前，卡面仍 null；甲＝依 role 取源，需求方要求照 astra 寫清三種情況：reviewer＝卡面 `source_sha`（null 即 D3）；executor＝卡面 `branch` 的遠端分支頭、⛔ 不用本機分支頭、⛔ 不用 null 或全零；`branch` null、遠端無該分支或遠端 ref 解析不出 40 碼 SHA＝D4；本機分支頭 ≠ 遠端頭只印、本機 git 取不到印「未能比對本機分支頭」rc=0（後兩種為 Codex #289 R2-01 補，共五種）。與 `roles/executor.md` §3「交回單的來源 SHA 用交回當下的分支頭」一致，只是機械化。B05＝`dispatch.md` 副作用入口讀 `wf-contract` 的 `side_effects` 而骨架 §十三居所清單無它；預設＝schema 住 `dispatch.md`、`{side_effects: string[]}` 封閉鍵、區塊存在但不合 schema＝印不採用、⛔ 不擋（Codex #289 R1-01：同一事件標 D3 又「並印」機械結果不唯一；`brief` 無寫入故落印）。B07＝`snapshot` §1「唯讀⛔ 不寫回」與 `verbs.md` §2「下一次動詞先對帳…重寫」字面衝突；預設＝`snapshot` 例外只印不重寫，schema 仍從 core 讀做 D3、⛔ 不做 §3 合成（決策紀錄「硬擋收縮」的「`snapshot` 不讀規則檔」指條文合成，schema 區塊除外）。B09＝骨架 §十三第 6 步要 CLI 組 squash 訊息但七動詞無接點；預設＝`brief --for closeout` 另印，本文＝被審 SHA＋本 iteration 每則 `wf:verdict` 作者與 `review_result`，trailer 鍵取 P5 允許集合、值全取字面：Requested-by／Planned-by／Implemented-by 取 `brief` 三個同名旗標（卡面無字面來源——`owner` 每次派工被覆寫、`wf:move` 留言 CLI 不讀）、Reviewed-by 原擬取代貼首行的來源字串，Codex #289 第 2 輪 R1-01 判違反決策 1／骨架 §六／`verbs.md` §2「首行不讀」，改為第四個旗標 `--reviewed-by`（可重複、每位一行）、缺旗標取每則 `wf:verdict` 留言作者，CLI 首行維持不讀（PM 依既有邊界改、⛔ 未開讀首行的例外；需求方原裁「trailer 照你那樣寫」的旗標形式不變）。core 內來歷字樣依既有形式只留「需求方 2026-09-07 裁定」、⛔ 不寫 PR 號／astra／B 編號（Codex R3-01）。B01 的動詞契約半邊落本 PR：`move` 先寫卡面 `stage`／`state` 再回寫五欄、`edit` ⛔ 改這兩鍵（D1，只由 `move` 寫）（Codex #288 第 3 輪 R1-01）；缺者印、⛔ 不自動 merge——這是 P5 已知漏洞（2026-09-06 起）的執行者。B10＝`owner` 必填 role＋actor 而 `move` 只收 actor；預設＝`--actor <role>:<actor>`（與 §5 投影同形），role 不在四值＝D3；`owner` 只在派工邊寫、缺則保留並印、其他邊不動。
- **投影欄對照表入 `card-schema` §5 區塊；`--ruling URL` 解析住 `gh/`**（需求方 2026-09-08 裁甲，PM 三輪研究後）：S02 查核指出 §5 五欄名只在散文、S02 測試以 regex 抓散文取欄名。量測：對照的活消費者 4 處（§5、詞表「投影欄」列、ADOPTION §3、`verbs` §2）＋即將 2 處（S05 寫五欄、第 7 步建欄）；沒有機讀居所時 S05 只能寫死欄名或解析散文，皆違決策 1／11。乙（塞 `enums.md`）不對——是欄名↔鍵的對照非值集合；塞 schema 當 `x-` 註記會撞 S03 的關鍵字覆蓋測試。落點＝§5 加 fenced `json wf-projection`，每欄一個物件 `{key, max_bytes?}`——S05 執行者上呈指出 `max_bytes`（owner／卡ID 1024）只在 §5 散文、D3 無法機讀，與欄名同類缺口，故同一區塊承載投影欄的全部機讀事實（card-schema 125／150）。密封試出排序坑：`compose` 對 `json wf-*` 命名空間的未知標籤是中止（S03 依前片 finding 所做，正確），本 PR 合併後分支 rebase 前 `cli-tests` 會紅——解法是排序不是改設計：S05 以「分支頭＋cherry-pick 本 commit」為基線、第一件事加標籤，S05 收了再 rebase。`--ruling URL`：規則只說「URL 存在」（D4）、未定形式；⛔ 不加規則——接受 issue 留言 URL（`…/issues/<n>#issuecomment-<id>`），解析不出＝指向不存在＝D4；解析住 `gh/`（`comment_from_url`），URL 形式是平台知識、`gh/` 是唯一該懂平台的層；消費者＝`verbs.md` 三個印＋D4。

- **第 6 步無卡進行、T3 要求由 PR＋跨實體審承載**（需求方 2026-09-08 裁定；矛盾清單 C13）：`CLAUDE.md`「自舉期間不開卡」、決策 10「授權⛔ 不涵蓋 CLI 碼」、`docs/research/2026-09-07-step6-spec.md`「另一張 T3 卡」三處不合；裁＝第 6 步無卡進行（含 CLI），T3 級別表要求的分支＋獨立查核＋required check 由 PR＋Codex／Gemini 跨實體審承載，finding id 形狀暫用片號。
- **第 6 步停損 3 輪已越；不縮射程，CLI 暫停派新片至規則側文件 PR 合併**（需求方 2026-09-08 裁定；矛盾清單 C14）：step6-spec 停損「第 6 步超過 3 輪查核 ⇒ 需求方裁定是否縮射程」已被 d-S05b／S09b／S14b／S10b 四輪修補片越過而無裁定；裁＝不縮射程，CLI 暫停派新片至本文件 PR（六條裁定＋28 條矛盾的規則側改動）合併；⛔ 不動停損數字。

- **自舉期 PM 兼執行者的例外授權；D2 登記追認納入 #301 射程**（需求方 2026-09-09 裁定）：gpt-6-astra 審 #301 時開兩條 governance——① PM 拿執行者交回的產出自己動手改了三個 commit（`3752c92`／`a646853`／`149ff35`），違反 `roles/pm.md` §2 逐字「⛔ 不代填、⛔ 不代修、⛔ 不代寫他人產出或判定；列出問題交還產出者，只修自己的產出物」與同節「T0／T1 可兼執行者；T2 以上⛔ 不兼」，且逐字指出「補外部查核不等於補角色授權」；② 該三個 commit 之一另改了 `docs/research/REBUILD-DECISIONS-2026-09-04.md`，超出 PM 自己寫的「只授權兩個檔」射程。兩條裁定皆採甲：既成變更就地認可，⛔ 不重做——重做要重跑三輪自審的全部負控而結果相同，成本不成比例。**授權射程限自舉期（`CLAUDE.md`「本輪重構自舉期間不開卡」）**：自舉結束後 `pm.md` §2 兩條完全回復，⛔ 不延伸到第一張真實卡之後、⛔ 不視為對 §2 的永久豁免。本次的實際教訓寫進 PM 記憶：收到查核 finding 時，⛔ 不因「反正後面還有兩家審」就自己動手修執行者的產出。

## 回看清單（2026-09-08）

登記於此、⛔ 不開 PR；依 `roles/requester.md` §1 定期回看時一併議（四類：零拒收硬擋、正式化候選、設計缺陷、`last_confirmed` 過期）。2026-09-09 更正：原括號「不改變 CLI 實作的 finding 進回看」被當成收件條件是誤讀——現有條目 9 條中 4 條逐字要改 CLI（六條 #1「CLI 下次動時移除」、#4d「（CLI 動）」、#6②「CLI 改動，依停損進回看」、C09「待 CLI 側改印」）；該句禁的是**當場開 PR**，⛔ 不是排除會改 CLI 的 finding。升成設計缺陷的三項門檻住 `roles/pm.md` §3。

- 六條 #1：`move` 印「`wf-ruling` 依 kind 的必要鍵缺」的鍵集合以 regex 讀 `core/ruling.md` 散文（`_ruling_prints`）；散文改寫即靜默失印、⛔ 不寫壞資料。清單已在 `roles/requester.md` §3 與 `core/ruling.md`；CLI 下次動時移除。
- 六條 #3：`*/升級→same/進行中` 不是派工邊，`--actor` 靜默不寫 `owner`（測試釘住的刻意實作）；換人走先 `edit` 後 `move`（`modules/escalation/module.md` §1）。第二個模組出現再派邊時再議 `adds` 的派工邊宣告。
- 六條 #4d：`notes` 以 `modules/pitfalls-13/module.md` §1 第 2、3 條的反引號字串與位置取族名，位置索引脆（已加讀取點註記）；正解＝族名進 §0 宣告＋`notes` 改讀宣告（CLI 動）。
- 六條 #5 同步點清單（規則側字面 → CLI 檔；字面變動時同 PR 改；⛔ 不加對帳測試，測試＝第三居所）：規格欄四名（`core/card-schema.md` §2）→ `edit`；階段名 需求／規劃／執行／審核（`core/enums.md`）→ `edit`、`move`、`move_modules`；`owner` 投影 `role:actor` 的分隔（`core/card-schema.md` §5）→ `move`、`move_modules`、`notes`、`brief`、`_write`；`schema_version` 1→2 回填（`core/card-schema.md` §6）→ `_write`；`notes.id` pattern 與 `stages`（2026-09-07 已登記）。
- 六條 #6：① `edit --set parent=` 排除 isArchived 而 `open` 的 parent 不排除，同一條 D4 兩個答案——待實例（終態卡可否當父卡未裁）；② `core/verbs.md` move 寫格「進終態即關 issue 並封存」的「封存」半邊 CLI 未實作（全 src 無 archive 呼叫，isArchived 只能來自 UI 手動）——CLI 改動，依停損進回看。
- C20（待實例）：maintenance §0 從 `維護/進行中` 沒有邊回 `維護/運行中`，一次事件即逼出維護；補邊要改狀態機 from／to（兩家族），等第一張維護卡。
- C25（待需求方裁）：`core/ruling.md` 類別欄（升級／停止／撤銷／級別變更／結案確認／其他）與 `wf-ruling.kind`（block／stop／withdraw／tier_change／signoff／other）無對照；升級、結案確認對應哪個 kind、阻塞要不要有類別，屬內容裁定。
- C09：`adds.counters` 列的欄由 `edit` 改時的字面結果＝印「模組欄由 `move` 寫」（規則句已補）；d-S07 的 D3 硬擋與「宣告即擋」待 CLI 側改印。
- **設計缺陷 D1（2026-09-09 登記）：`wf:reject` 留痕綁在 `rc≠0`，而非綁在「被拒的那一次寫入」。**`core/glossary.md`「拒收｜一次硬擋與其 `wf:reject` 留言」、`core/verbs.md` §2「每次拒收寫一則」、§1 表頭「硬擋（rc≠0，寫 `wf:reject`）」三處把「資料無效」推導成「不能繼續＋rc≠0＋在被讀的卡上留言」。§2 給 D1–D4 的正當性是「硬擋只落在寫壞資料」＝守遠端不被寫壞，但 D3 後半「解析失敗整卡拒」是讀側條件；寫入動詞兩者重合，純讀動詞的讀側 D3 沒有寫入要保護，留痕反而成為該動詞唯一的遠端寫入。判準（`roles/pm.md` §3）本案成立——**必要項**活消費者：`snapshot.py`／`edit.py`／`review.py` 皆第 6 步已合併；**擇一項**受害點 ≥2（`snapshot` 壞卡→`snapshot.py` `if bad: return SnapshotResult(1, …)`；`edit --set owner=` 修既有過長值→`edit.py` 對舊卡 `reconcile_projection` 而 `_write.reconcile` 以 `check=True` 驗舊值 `max_bytes` 即 D3，修復被修復前的資料擋住）、（例外數＝3：§1 該列的 §3 合成例外、§2 對帳例外、#299 的 D3 例外——2026-09-09 依 Gemini 複審裁定**不當判準**：例外數量量的是規則成熟度、不是缺陷性，一條例外多的成熟規則會把任何單一動詞的操作違規誤放成設計缺陷；此處只作事實記錄，判準只用受害點。）另一受害點：`review` 交回單 schema 不過時 CLI 以查核者身分貼 `wf:reject`，撞 `roles/reviewer.md` §2「裁決留言以外⛔ 不寫任何東西」。正解＝把「驗證失敗」與「失敗處置」拆開（schema 說什麼不合法，動詞契約說停到哪、輸出什麼、往遠端寫什麼），並一併裁清留痕的作者、目標與角色授權。載體＝自舉結束後一張 T4 卡（`core/tiers.md` §3 `rules`），規則與 CLI 同 PR、⛔ 不再製造契約落差窗口。⛔ 不因已登記而免修（`roles/conduct-common.md` §1）。
- **仍有效未承接（2026-09-09 舊卡退場時登記，關閉留言已指向本清單）**：[#227](https://github.com/ruan6047/ai-workflow/issues/227) main push 的 commit trailer 可解析性守衛（與 P5 的 UI 合併路徑漏洞同源——`squash_merge_commit_message=COMMIT_MESSAGES`，PM 忘了貼 `brief --for closeout` 的訊息時平台照樣拼接多則 commit 訊息）；[#242](https://github.com/ruan6047/ai-workflow/issues/242) `cli/src/wf/verbs/main.py` 只接 `ProjectConfigError` 與 `OSError`，其餘例外仍以 traceback 收場。兩張已 `not planned` 關閉、body 與留言原地保留；⛔ 不因關閉而視為已解決（`roles/conduct-common.md` §1）。
- **設計缺陷 D2（2026-09-09 登記）：模組啟用判定讀的是尚未驗過的卡面——`core/card-schema.md` §1 把「驗」放在「合成」之後，而合成 (a) 又必須先讀卡面。**該條逐字「合成（D3 用合成後的 schema 驗）：…(a) 把**已啟用**模組宣告的 `adds.enums.states` 併入 `$defs/nonterminal` 的 enum；(b) 把**全部**宣告模組的 `$defs/module_fields/<模組名>` 併入 `wf-card.properties`…；**然後再驗**」構成一個環：驗卡面要合成後的 schema → (a) 要知道哪些模組已啟用 → 已啟用要讀卡面 `stage_plan` ← 正是還沒驗的欄（(b) 是卡面無關的，環只在 (a)）。`modules/{deploy,research,maintenance}/module.md` §0 逐字 `"enable_if": {"kind": "stage_plan_has", "stage": "…"}` 三個模組觸發它，而規則沒說合成階段讀到型別不符的卡面時落哪一格硬擋。判準（`roles/pm.md` §3）本案成立——**必要項**活消費者：`cli/src/wf/compose/enable.py:is_enabled`（逐字 `return condition["stage"] in card.get("stage_plan", [])`）、`cli/src/wf/compose/schema.py:compose_schema`、`cli/src/wf/verbs/_common.py:enabled_modules`，皆第 6 步已合併；**擇一項**受害點 ≥2 個不同動詞——`notes`（規則逐字 `core/verbs.md` §1 notes 列硬擋欄「卡面 JSON 解析失敗（D3）」；符號 `notes.py` 的 `enabled_modules` 呼叫）、`brief`（§1 brief 列同欄同字）、`review`（§1 review 列寫欄「⛔ 不動狀態、⛔ 不另產生其他留言」）三處的 `enabled_modules(…)` 都落在 `block_object` 的 `except` 之外、`check_card` 之前，卡面只過「是物件」；實測 `stage_plan` 為 `None` 或 `5` 時 `TypeError: argument of type 'int' is not a container or iterable` 未攔截，整支動詞死在 D1–D4 之外，`review` 連 `wf:verdict` 都產不出。另兩個消費點 `move.py`／`open.py` 靠 `except (ValueError, TypeError, KeyError)` 落 D3，但留言本文是 Python 內部字串（實測「拒收・D3・'int' object is not iterable」），非 §2 D3 逐字「JSON 合法、鍵集合封閉」指認得出的原因；`snapshot.py` 已於 #301 在動詞內兜住、根因未動。與 D1 是**兩條**：D1 管 D3 成立後的留痕處置，本條管 D3 成立**之前**的消費窗口——決定性檢驗＝完整實施 D1 的正解，本條一行都不會好。正解＝給 §1 的合成順序加**兩段驗證**：先用不含模組 enum 擴充的基底 schema 驗（`stage_plan` 型別在此已可判），過了才讀它算啟用、再合成、再驗模組層；或明定啟用判定只讀卡面的一個先驗子集，子集外的欄⛔ 不得驅動合成。載體＝自舉結束後一張 T4 卡（`core/tiers.md` §3 `rules`），規則與 CLI 同 PR、⛔ 不再製造契約落差窗口。⛔ 不因已登記而免修（`roles/conduct-common.md` §1）。
- **回看（2026-09-09 登記）：`modules/{deploy,maintenance}/module.md` §2 的 `- 待實例（2026-09-05 起）：` 那個括號是機器語意，⛔ 不得當出處標記清掉。**`.github/scripts/reachability.py` 的 `NOTE_ID = re.compile(r"^- ([^：\s]+)：", re.M)` ——括號在時 `- 待實例（2026-09-05 起）：` 因含空白而整條抓不到；括號一刪 `- 待實例：` 就被當成 id，`adds.notes` 對帳立刻 rc=1（逐字 `⛔ adds.notes 對帳：deploy: adds.notes=[] ≠ §2 條列=['待實例']`、`id 待實例 不是 F-deploy-NN 形狀`，deploy 與 maintenance 各兩條、失敗 4）。**而 879 個 pytest 案例與 `reachability --selftest` 對這個破壞全綠**——只有 `reachability` 主跑守得住。收施工痕跡時已踩過一次（當場抓到並還原）；下一輪清同類痕跡最可能再踩。登記於此⛔ 不加對帳測試（測試＝第三居所）。
- **回看（2026-09-09 登記，PR #303 三家審的非阻擋項）**：① **`WF_OFFLINE`／`WF_LIVE` 的離線與線上開關只有讀取端在 repo 內**（`cli/tests/conftest.py` 逐字 `if os.environ.get('WF_OFFLINE') != '1': return`；`.github/workflows/ci.yml` 的 `cli-tests` job 對 `WF_OFFLINE` 零消費——該 job 的兩個 run 步驟逐字為 `- run: python -m pip install -e "cli[dev]"` 與 `- run: python -m pytest cli/tests -q`，無任何設定端），設定端在人的 shell 裡。實測舊名 `WF_S05_OFFLINE=1` 護欄**完全不武裝、零訊息、rc=0**；新名才印 `OFFLINE_NETWORK_DENIED negative control passed`。修法兩件：`conftest.py` 在未設變數時印一行「離線護欄未武裝」把靜默變可見；CI 落一個設 `WF_OFFLINE=1` 的 job 把另一端拉進 repo，之後改名就是原子的。`WF_LIVE` 同構，另其 skip 理由逐字 `reason='需明確啟用線上唯讀驗證'` 不含變數名，操作者分不出是打錯名字還是本來就該跳。
② **同步點清單漏列兩個階段名字面的消費點**：現行逐字只列「階段名 需求／規劃／執行／審核（`core/enums.md`）→ `edit`、`move`、`move_modules`」，而 `cli/src/wf/verbs/review.py` 有 `stages.index('執行')`、`notes.py` 有 `if stage == '執行'`。查核者以突變實測：把 `core/verbs.md` §1 review 列裡 `review.py` 檔頭所指的兩件刪掉，879 測全綠、`reachability` 與 `--selftest` 皆 rc=0——**居所引用腐爛零機械保障**。⛔ 不加對帳測試（測試＝第三居所），補進同步點清單即可。
③ `cli/src/wf/verbs/snapshot.py` 的 `壞區塊只記錄，⛔ 不擋（派工單 §5）` 把居所引用直接刪掉未改指，與 `review.py` 改指 `core/verbs.md` 兩套標準；真居所在 `core/verbs.md` §2「`snapshot` 例外＝⛔ 不拒、依 §1 記入本機輸出並續跑」。
④ `review.py` 檔頭「規劃前 main 回退」比其所指規則窄一階：規則逐字是「卡在**執行階段以後**…（D4）」，碼側 `stages[stages.index('執行'):]`，回退區含 `規劃`。此措辭在 `021802d` 即存在，非本片引入。
⑤ `core/platform.md` 的 `last_confirmed: 2026-09-05` 早於檔內 `（2026-09-06 起）` 的內容；非本片引入，歸回看清單的「`last_confirmed` 過期」類。
⑥ `cli/tests/fixtures/s05/` 目錄名可被「只改一端」的改名靜默摘掉秘密掃描覆蓋：查核者實測改名並只同步 `FIXTURES` 一端後全套仍 879 綠，但同一次輸出的 `SECRET_SCANNED_FILES` 由 17 掉到 13，無任何斷言在乎；非本片引入。修法＝`test_gh_scope.py` 的 `assert paths` 改成逐目錄斷言，或目錄清單改由列舉 `cli/tests/fixtures/` 產生。
⑦ `test_gh_scope.py` 的 docstring 守衛只覆蓋五檔白名單；本片改動的 docstring 只有 1 處落在守衛內（`compose/project_config.py`），且 `compose/project_config.py` 的 `§` 出現次數由 2 降為 1、餘裕歸零。修法＝白名單改 `rglob('*.py')` 全掃。
- **回看（2026-09-09 登記）**：「同對象例外堆疊」這個訊號在規則側沒有任何鉤子了。框架為自己設的三個機械訊號（`core/naming.md` §5 行數上限、2026-09-05 分號裁定、`reachability` job）在「例外堆疊」這個方向上全是關的——例外是接在既有行尾的分號子句，行數抓不到、分號裁定明文允許「條件、例外、指向子句」、reachability 不讀 §2 條文一個字。判準已按 Gemini 複審只留受害點，故此訊號目前只靠 PM 人工數。第一次撞到「規則沒壞但例外多到讀不懂」時再議。
- **回看（2026-09-09 登記）：`core/platform.md:20` 的 P5 漏洞條目內容過時，且刪不掉座標。**逐字為`- ⚠️ P5 的已知漏洞（2026-09-06 起）：合併訊息由平台預設組時 trailer 會被空行切散，本檔擋不到；訊息組法的居所＝新 CLI（`docs/research/2026-09-07-step6-spec.md` 第 6 步），該步完成前無執行者。`兩個問題疊在同一行：① `第 6 步` 是建造過程座標（需求方 2026-09-09 裁定要清），但刪掉它，後半句的 `該步` 就沒有先行詞；② 「該步完成前無執行者」現在已不成立——CLI 已在 repo 內，`cli/src/wf/verbs/closeout.py:125 def squash(ctx)` 就是那個執行者（入口＝`brief --for closeout`，見 `core/verbs.md` §1 brief 列；`cli/src/wf/verbs/brief.py:279` 逐字 `for line in closeout.squash(ctx):`）。所以這不是施工痕跡而是**內容過時**，要改寫條文語意，PR #303 的射程（只刪不加、零行為改動）蓋不到。另外 `docs/research/2026-09-07-step6-spec.md` 本身依前面條目「第 7 步完成後歸檔」，屆時這個路徑引用會腐爛——同一行上有三件事要一起改，載體＝第 7 步收尾宣告之後的一片，同時處理居所改指與「無執行者」的更新。⛔ 不在 #303 內改（改了就不是零行為改動）。
## 第 7 步收尾宣告（2026-09-09）

第 7 步＝aiwf 接上自己的框架。宣告當下逐項回讀驗過，**數字全部是 2026-09-09 在 `ab78685` 實測**，⛔ 不引用任何先前輪次的轉述：

| 項 | 規格逐字（`archive/research/2026-09-07-step6-spec.md` 第 7 條） | 回讀 |
|---|---|---|
| Project 五欄 | 欄名、型別與選項集逐字依 `ADOPTION.md` §3 | `aiwf 任務看板`；階段 8 值、狀態 9 值、級別 5 值、owner／卡ID 為 TEXT |
| 狀態 9 值的推導 | `states_core`＋`state_blocked`＋`states_terminal`＋全部**卡級**模組的 `adds.enums.states`＋`modules` 列出的**專案級**模組的 | 4＋1＋2＝7 基底，加卡級 `research` 的 `不可判定`、`maintenance` 的 `運行中` ＝ **9**。`escalation` 的 `升級` ⛔ 不進——它 `enable_if.kind` 逐字為 `project_module_listed`，而 `.wf/modules.json` 的 `modules` 是空陣列 |
| 兩個 view | 活卡依階段分組、全部 | `活卡 [BOARD_LAYOUT] filter=-狀態:完成,停止 group=階段`／`全部 [TABLE_LAYOUT] filter 與 group 皆空` |
| ⛔ 不用內建 workflow | — | 6 條全部 `enabled=false` |
| ruleset | 加 `required_linear_history` | `20768920 main must be green active`，rules＝`deletion non_fast_forward required_linear_history required_status_checks` |
| 關閉 merge 與 rebase 按鈕 | — | `squash=true, merge=false, rebase=false` |
| `.wf/modules.json` 種子 | `modules: []`、`merge_method: squash`、`areas: [WF, CLI, DOC, OPS]` | 逐字相同，另有 `project: {owner: ruan6047, number: 8}` |
| 舊卡關閉＋移出 #4 | — | repo open issue ＝ **0**；Project #8 items ＝ **0**；Project #4 內**未關閉**的 ai-workflow 卡 ＝ **0**（分頁掃完 187 個 item：cpbl-analytics 118＋ai-workflow **69**，69 張全部 `CLOSED`、`isArchived=false`）。⚠️ 前一版寫「Project #4 內的 ai-workflow 卡 ＝ 0」是錯的——PM 量的是 repo 的 open issue 數卻標成 Project 內的卡數。**需求方 2026-09-10 裁定：已關閉的 69 張留在 #4 當歷史、⛔ 不移出**，故規格「舊卡關閉＋移出 #4」的後半只對當初移出的 30 張成立 |
| 全部動作可逆 | 關閉 issue、移出 Project、封存皆可逆；無硬刪 | 成立；99 張的 item_id 與欄位值存在 PM 暫存的 `p4-aiwf-recovery.json`，已交需求方留存（30 張已移出、69 張依 2026-09-10 裁定留存，合計 99） |

配套：`archive/research/2026-09-07-step6-spec.md` 依其第 1 行「第 7 步完成後歸檔」歸檔，指向它的 8 處活引用同 PR 改指 `core/`（⛔ 不改指 `archive/`——那等於宣告程式在消費凍結文件）。

**⛔ 本宣告不宣稱重構完成。** 尚未落地、已登記回看的：設計缺陷 D1（拒收留痕綁 rc≠0）、D2（模組啟用判定讀尚未驗過的卡面）、「引用必須可解析」那條規則與其 CI 檢查、`cli/tests` 的查核輪引用、`aiwf` 硬編兩處。`CLAUDE.md`／`AGENTS.md` 的重構期敘述**已於本片落地**（需求方 2026-09-09 裁定重構期結束）。需求方 2026-09-10 另裁：Project #4 內已關閉的 69 張舊卡留存為歷史。**重構期結束是操作模式的切換，⛔ 不等於上列五項已解決**——它們改成用真實卡跑，仍在回看清單上。

**自舉期例外授權自此失效。** 回看清單裡「自舉期 PM 兼執行者的例外授權」逐字把射程錨在 `CLAUDE.md`「本輪重構自舉期間不開卡」那句上；該句已隨重構期結束刪除（本片），故需求方 2026-09-09 裁定的重構期結束＝該項所稱的「自舉結束」，例外自此失效，`roles/pm.md` §2 兩條（⛔ 不代填／代修／代寫他人產出、T2 以上⛔ 不兼執行者）完全回復。

- **回看（2026-09-10 登記，第一張真實卡 `WF-001` 走完需求階段後的五項）**：七動詞全部在真機跑過一遍（`open`／`brief`／`edit`／`move`／`notes`／`review`／`snapshot`），以下是這一圈暴露的、⛔ 尚未處理的：
  - **① CLI 效能：每個動詞都全掃 repo 的所有 issue，且零快取。** 實測 `wf notes WF-001 --stage 需求` ＝ **9.1 秒**，拆解為 4 次 `repos/…/issues?state=all&per_page=100&page=1..4`（**307 張 issue**）＝ 4.2 秒 ＋ 6 次 GraphQL（Project 的 id／欄位分頁／items 分頁）＝ 3.9 秒 ＋ issue 與留言各 1 次；`load_blocks`（讀 34 個規則檔並解析全部區塊）＝ **0.00 秒**，本機完全不是瓶頸。全掃的唯一用途是把卡 ID 對回 issue 號（`cli/src/wf/verbs/_common.py` 的 `card_number` → `repo_cards`）。**母體組成**：308 筆中 **PR 194（63%）、真 issue 114**——`_common.py` 逐字 `client.issues(state='all')` 打的 `/repos/…/issues` 會連 PR 一起回，而 PR 不可能有 `wf-card` 區塊，這 63% 是純浪費。**成長**：一張卡＝一個 issue、其工作 ≥1 個 PR，且 `state='all'` 使關閉的卡永不離開分母 ⇒ 母體約為**卡數的 3 倍**；300 張卡時約 900 筆＝9 頁＝**每次動詞約 10 秒**。所以這是**常態、⛔ 不是框架建造期特有**，且只增不減。**繞法（現在就能用）**：`card_number` 逐字「卡 ID 或 issue 號」，直接給 issue 號會跳過全掃——實測 `notes 306` ＝ 5.2 秒，省 40%。**兩個用途要分開修**：`card_number`（卡 ID → issue 號）可改查 Project 的 `卡ID` 投影欄、⛔ 不需全掃；`open` 的發號（`max(serials, default=0) + 1`）需要**歷來最大序號、關閉的卡也算**——卡進終態會封存，`board_items(..., include_archived=True)` 拿得到，但**⛔ 未確認封存項是否永久保留**，未確認前 ⛔ 不給修法。另 `client.project()` 的三次 GraphQL 可併成一次。屬效能缺陷、⛔ 不是正確性缺陷，但**會擋住日常使用**，⛔ 不是可以無限期拖的小事。
  - **② 交接文件的來源標記印出解析不到的路徑。** `brief`／`notes` 每段首行印 `[來源: core/core/dispatch.md · …]`、`[來源: core/stages/requirement.md#6 · …]`——**這些路徑都不存在**。成因是 `cli/src/wf/verbs/notes.py` 的 `f'[來源: {origin}/{relative}'`：前一段是**居所類別**（core｜module｜project｜card）不是路徑，後一段才是路徑。是設計、`cli/tests/test_brief_sections.py` 也釘住了，但讀者（AI 或人）會照著開檔然後失敗；而且 `cli/src/wf/compose/blocks.py` 的 `source_line` 還有**另一種不帶 origin 的格式**並存。與本紀錄自己登記的「引用必須指向解析得到的居所」對不上。修法方向＝兩種格式收斂成一種，且路徑段要能直接開。
  - **③ 派工單的「寫入授權、唯讀範圍」永遠是「（人填）」。** 第一張卡實際遇到：`.wf/stages/<階段>.md` 的 writer 歸屬有分歧——`roles/pm.md` F-PM-12 把「維護」寫在 PM 名下，而同檔 §2 逐字「T2 以上⛔ 不兼」執行者。派工單有這一段但 CLI ⛔ 不填，所以每張 T2 以上的卡都會撞。要嘛規則側寫死歸屬，要嘛那段改成 CLI 從卡面 `resources` 推。
  - **④ 執行者的 finding id `<查核序>` 對執行者無定義來源。** `core/naming.md` §4 逐字 `<card_id>-R<iteration>.<查核序>-<序>`，查核序取派工單的同名段，但 `core/dispatch.md` 逐字 `--for executor` ⛔ 不印該段。`WF-001` 的執行者一律填 0，那是它自己選的預設、⛔ 不是規則給的。
  - **⑤ `WF-001-R0.0-4` 由開它的執行者自行推翻**（它拿 GitHub 的 UTC 時戳去對 body 散文的台北日期；實測 `date -u`＝2026-09-09T19:30:49Z 而 `date`＝2026-09-10 03:30:49 CST）。留言 append-only ⛔ 不可編輯，下一輪的 `wf-return` 要依 `core/return.md` 的跨 iteration 閉環把它列為 `status: withdrawn`。
- **回看（2026-09-10 登記，需求方裁定「等目前四張做完再開卡處理」）：兩件規則層的形狀問題，⛔ 皆非 bug。**① **卡ID 的序號是全 repo 遞增，⛔ 不是每個 area 各自算。** `core/naming.md` §1 逐字「NNN＝`open` 依 repo 遞增，三位數起，只增不重用」，`cli/src/wf/verbs/open.py` 的發號取全部 `card_id` 的最大序號 +1——**實作與規則一致**。實例：第一批四張卡發成 `WF-002`／`CLI-003`／`OPS-004`／`CLI-005`（issue #311–#314），⛔ 不是各 area 從 001 起。需求方 2026-09-10 表示希望改成各 area 獨立計算，那是**改規則**。⚠️ 改時要一併處理：`CLI-003`／`OPS-004`／`CLI-005` 已逐字寫進卡面與 Project 的卡ID 投影欄，而同條規則逐字「只增不重用」——要嘛新規則只管之後、既有號不動，要嘛改號並同時處理與「只增不重用」的牴觸。載體＝T4（改 `core/naming.md`）。

  **2026-09-10 需求方追加裁定（逐字「不同 area 獨立計算 這個等目前這張卡完成後先處理 並修正不同 area的卡的ＩＤ」、「我認為這不是先規則 卡ID而是解釋方式不同」）**：⚠️ **PM 上面把它寫成「改規則」是錯的判性**——需求方裁定這是**解釋歧義**、⛔ 不是規則錯。`core/naming.md:12` 逐字只寫「NNN＝`open` 依 repo 遞增」，「依 repo」界定的是**範圍不跨 repo**，全句 ⛔ 未說序號池跨 area 共用；per-area 與全域兩種讀法都容得下，所以規則是**歧義**、CLI 在 `open.py:87-88`（`serials` 收**全部** `card_id` 而 ⛔ 不篩 `area`）逕自選了一種讀法且無留痕。據此改判：`CLI-003`／`OPS-004`／`CLI-005`／`WF-006`／`WF-007` 是**發錯的號**、⛔ 不是合法發出的號，故與「只增不重用」**沒有牴觸**（該條保護的是已合法發出的號）；(a) 那一項作廢。① 補明 `naming.md` §1 的歧義為各 area 獨立；② **既有卡 ID 要修正**、⛔ 不是只管之後；③ 時序＝**WF-002 完成後立刻做**，排在 CLI-003／OPS-004／CLI-005 之前（原裁定「等四張做完」由此覆寫，此條 ⛔ 不再有效）。
  改號後的對照（現況 → 各 area 獨立、依 `open` 先後）：`WF-001`(#306) 不動、`WF-002`(#311) 不動、`CLI-003`(#312)→`CLI-001`、`OPS-004`(#313)→`OPS-001`、`CLI-005`(#314)→`CLI-002`、`WF-006`(#316)→`WF-003`、`WF-007`(#317)→`WF-004`。**7 張中 5 張要改。**
  ⚠️ 該卡必須一併處理的三件：~~(a) 與「只增不重用」的牴觸~~（依需求方 2026-09-10 的解釋歧義裁定作廢，見上）；(b) 寫入面 ≥3 處要同步：卡面 `card_id`、Project 的卡ID 投影欄、`stages/*.md` 與留言裡的逐字引用；(c) 分支名 `wf/<card_id>`（`core/naming.md` §2）——已存在的分支要不要改名，改名會斷已推的 ref；(d) `open.py:87-88` 目前取全部 `card_id` 最大序號 +1（逐字 `serials = [int(key.split('-')[1]) for key in cards if re.fullmatch(...)]`，⛔ 不篩 area），改成 per-area 只需加 area 前綴篩選，但 ⚠️ 仍要 `include_archived=True` 才拿得到已封存卡的號，而**⛔ 未確認封存項是否永久保留**（同 ① 的未確認項）。
  級別 ⚠️ 仍是 T4：`core/tiers.md` §3 的 `rules` 判準看**改哪個檔**、⛔ 不看改動是澄清還是改義，而本卡要動 `core/naming.md`。
② **`edit` 一次只吃一個 `--set`，填一張卡的建卡必填要 12 次呼叫。** `core/verbs.md` §1 edit 列逐字 `edit <card> --set <欄>=<值> [--ruling URL]`（單數 `<欄>`），寫欄逐字「`wf:edit` 留言（**欄**、原值 hash → 新值 hash）」也是單欄——**一次一欄是規則描述的形狀，⛔ 不是實作偷懶**。實測代價：填 WF-002 的 12 欄花 **12 次呼叫、約 3.5 分鐘、12 則 `wf:edit` 留言**，每次都重抓 Project（3 次 GraphQL）＋issue＋留言。改成可重複的 `--set` 或批次形式能壓成 1 次呼叫、1 則留言，但要同時改動詞表與寫欄（留言得記多欄的 hash 轉移）。載體＝T4。與已登記的 CLI 效能條（每動詞全掃 issue）同族但不同因：那條是母體過大，這條是呼叫次數過多。
- **回看（2026-09-10 登記，PM 於 WF-002 需求階段實際撞到）：`move --source-sha` 在非執行階段的交回邊被靜默丟棄。** `core/state-machine.md` 逐字 `{"from": "*/進行中", "to": "same/待確認", "condition": "交回；寫 --source-sha"}`，而同檔逐字定義 `*`＝「該卡階段計畫內任一非結案階段」——規則要求**每個階段**的交回邊都寫 `source_sha`。`cli/src/wf/verbs/move.py:176-177` 逐字 `if from_node == '執行/進行中' and to_node == '執行/待確認': updated['source_sha'] = source_sha`，**只寫執行階段那一條邊**。實測：`wf move 311 --to 需求/待確認 --source-sha e03e410b9509309e5ec7f61ef889d5d0cba20e58`，rc=0、印只有「T4 而 grilling 空」、卡面 `source_sha` 事後仍為 `null`——**⛔ 無任何印說輸入被丟棄**。`move.py:147-148` 還先驗過該 SHA 在遠端（`commit_exists`，不在即 D4），也就是輸入被驗過、才被丟掉。⚠️ CLI 的收窄**可能是對的**（需求階段無分支、無碼，`source_sha` 對審核階段的被審 SHA 才有意義；B04 已裁 `review --role executor` 由分支頭取源），但那是**規則沒說的收窄**，且⛔ 無印、⛔ 無符號處註記——屬「靜默吞掉已驗過的輸入」。**⛔ 不開卡**（依需求方 2026-09-10 逐字「目前清單是有碰到問題的 之後有碰到問題有需要可以再加」，本條進清單）；載體待定：要嘛補規則明寫收窄、要嘛 CLI 補印。與 D1／D2（#316／#317）**不同族**——那兩條管硬擋的留痕與消費順序，本條管非硬擋路徑上被丟棄的輸入。

- **回看（2026-09-10 登記，一輪內在 WF-002／WF-008 上實際撞到的十二件）。全部 ⛔ 不開卡**，依需求方 2026-09-10 逐字「目前清單是有碰到問題的 之後有碰到問題有需要可以再加」。

  1. **`tiers.md` §3 的 `rules` 判準只看「改哪個檔」，無法區分「補明歧義」與「改寫語意」。** §3 逐字「含 migration、`rules`、statistics ⇒ T4」與逐字「`rules`＝改 `core/naming.md` §4 的規則檔」；§2 逐字「⛔ 不以估時、檔案數、工作量、當下額度定級或降級」把「改動很小」也堵掉 ⇒ 唯一出口是 §4 的需求方 `--ruling` kind=tier_change，**每一次澄清型改動都要需求方裁一次**。實例＝`WF-008`（#320）機械 T4、需求方裁降 T3（`issuecomment-5612175160`），底線 T3 ⛔ 非 T2（`data_write`）。⚠️ **⛔ 不主張是缺陷**——規則檔就是該難改；登記的是「判準無法區分兩種風險不同的改動，且 ⛔ 無條文承認這個區分」。
  2. **注意事項清單在同一輪內會變。** `modules/resource-lock/module.md` §0 逐字 `"enable_if": {"kind": "other_actor_card_in_state", "state": "進行中", "min": 1}`，`fact_source` 逐字「Project 投影欄 狀態＋owner」⇒ 啟用取決於**板上別張卡**。實測序列：PM 量 `notes 311 --stage 研究`＝**15 條** → PM 派 WF-008 到 `需求/進行中`（不同 owner）→ 執行者提交前重讀＝**19 條**。**PM 派另一張卡就改掉了進行中那一輪的清單，而派工單裡 PM 寫的 15 已過期**；執行者是自己重讀才沒中槍、⛔ 不是框架擋住的。⚠️ ⛔ 不主張是缺陷（`enable_when` 逐字就是「派工當下」）；登記兩個沒有條文承認的後果：(a) 派工單的條數 ⛔ 無穩定性保證而 `brief` ⛔ 不標示可變；(b) `note_responses` 的覆蓋完整性 **⛔ 無判準時點**（交回當下？派工當下？）。
  3. **`core/naming.md:12` 同一句「三位數起」是第二處歧義**（001 起 vs ≥3 位數）。反例＝`WF-000`(#295)，卡面逐字 `{"schema_version": 2, "card_id": "WF-000", …}`，`re.fullmatch` 過。需求方 2026-09-10 裁定 ⛔ 不進 `WF-008` 射程（`issuecomment-5613411580`），故登記於此。
  4. **`sensitive`(8 值)／`recoverable`(3 值)／`blast`(4 值) 全部 ⛔ 無逐值定義居所。** `core/enums.md` 逐字「`glossary.md` 每個值域鍵一列、⛔ 不逐值列」，而 `core/tiers.md` §3 只定義了 `rules` 一值。⇒ **每張卡的 `tier_basis` 都是在無判準下填的，而它直接決定級別。** 實例：`WF-008` 的 `sensitive` 該不該含 `migration` 無從判，而後果是 T4；`recoverable="reversible"` 對「留言 append-only 使舊卡ID 引用不可改」算不算不可回復也無從判。**這是比多數已登記項更上游的缺口。**
  5. **`missing_fields` 結構上抓不到模組欄。** `cli/src/wf/verbs/_common.py` 的 `missing_fields` 只取 `core/card-schema.md` §2「必填時點＝建卡」那些列 ⇒ 模組 `adds.fields`（如 `resource-lock` 的 `worktree`／`lease_expires_at`）**永遠不進缺欄清單**。實例：`WF-008` 啟用 `resource-lock` 後兩欄皆缺、違 `module.md` §1 逐字「認領時把實際 worktree 路徑與分支寫回卡面」，`open`／`move` 皆 ⛔ 未印，由執行者人工抓到。
  6. **`resources` 的文法住在一個「條件啟用」的模組裡。** `core/card-schema.md` 逐字只有 `{"type": "array", "items": {"type": "string"}}`，⛔ 無形式規定；文法在 `modules/resource-lock/module.md` §1 逐字「資源宣告逐條寫 `file:<路徑>`／`port:<n>`／`container:<name>`／`db:…`」。⇒ **同一個欄的合法形式取決於板上有沒有別張進行中的卡。** 實例：`WF-008` 的 `remote:issue-body:`／`remote:issue-comments:`／`remote:project-field:` 三種前綴 ⛔ 不在該文法內（PM 自創），而交集判定逐字「完全字串比對」故無害。
  7. **`brief` ⛔ 不承載唯讀邊界。** `brief --for executor` 的「寫入授權、唯讀範圍」段逐字印「（人填）」＝空 ⇒ **禁跑哪些動詞、能改哪些檔，完全靠派工訊息傳**。執行者逐字：「如果我只看 `brief` 就開工，我不知道禁跑 `open`／`move`／`edit`／`snapshot`」。同段另兩件：`brief` ⛔ 不印卡面 JSON 全文（要查核卡面得另跑 `gh issue view`）；「驗收條件」印「無」但交回單仍要 `acceptance` 段，⛔ 無提示告訴執行者需求階段填 `[]` 是對的。
  8. **`findings` 該由誰填 ⛔ 無明文。** `core/return.md` 段落表把 `findings` 歸「查核者」，但 `core/naming.md` §4 逐字「finding id…由**該則交回單的作者**填」。實測兩張卡的執行者選了相反做法且**兩種都過 CLI**：#311 的執行者填 `findings: []` 而把 finding id 埋進 `note_responses` 文字；#320 的執行者填 `findings` 陣列。機讀性差一個量級。
  9. **「實體」的定義套在子代理上判不出來。** `core/glossary.md:46` 逐字「實體｜跑角色的一個 **session**｜不是帳號」。子代理：獨立 context、⛔ 不繼承 PM 對話歷史 ⇒ 像一個 session；共用同一工作目錄、同一 `gh` 憑證、同一模型、且由 PM 撰寫的提示詞界定它看什麼 ⇒ 像同一 session 的一部分。**執行者身分不致命，審核階段會撞上**——T2+ 逐字要「查核者實體 ≠ 執行者實體」，查核者若也是子代理則判不出。疊上 `tiers.md` §6 的「跨家族」更糟（子代理與 PM 同家族）。另 `resource-lock/module.md` §1 逐字「一卡一 worktree 一 session，靠註冊查重」在共用目錄下**假設就不成立**。
  10. **`core/naming.md:16` 逐字「aiwf 種子 areas：WF、CLI、DOC、OPS」把專案層的值寫進框架規則檔**，與同檔 `:12` 逐字「AREA＝專案層 `.wf/modules.json` 的 `areas` 封閉枚舉」構成第二事實來源（目前兩處相同）。per-area 發號會讓「areas 的權威在哪」更要緊。
  11. ~~**`wf edit` 的成功回饋不可靠。**~~ **⚠️ 2026-09-10 同日更正，判性錯了、⛔ 不是缺陷。** 實測探針（對不存在的 issue，⛔ 無遠端寫入）：`wf edit 999999 --set 'feature={"a":1,,}'` 先印「無裁定連結」，接著 `Traceback`，rc=1。⇒ **「無裁定連結」是早印的，失敗訊息追加在它之後、rc≠0；CLI 的回饋 ⛔ 不是不可靠。** 真正根因是 **PM 用 `2>&1 | tr '\n' ' '` 把多行輸出壓成一行後只讀開頭**，把兩次 D3 拒收讀成成功（#320 的 `5613415447`／`5613415658` 逐字「拒收・D3・Expecting ',' delimiter: line 1 column 336 (char 335)」與「…column 337」），並在卡上留下兩則永久拒收。⇒ 本條改為**紀律**：⛔ 不得壓平多行輸出後只讀開頭；判斷成敗一律回讀遠端。⚠️ 但同一探針揭出**一件真缺陷**：`wf edit` 對不存在的 issue 吐 **traceback** 而 ⛔ 不是乾淨錯誤（`KNOWN_ERRORS` 未涵蓋）。
  12. **`core/return.md` 不足以自驗交回單。** #320 的執行者達成「交回單 schema 試錯 0 次」，代價是**先讀懂 CLI 原始碼**——自己 import `compose_schema('wf-return', ['resource-lock'])`、複製 `review._missing` 的邏輯自檢缺段、複製 `_hints` 的 regex 自檢 `note_responses` 覆蓋。它逐字：「這是唯一能不拿遠端試錯的辦法，但它要求執行者先讀懂 CLI 原始碼」。⇒ 不讀原始碼的執行者只能拿遠端試錯，而每次拒收都在卡上留一則永久 `wf:reject`。

- **回看（2026-09-10 第二批，`WF-005`／原 `WF-008` 執行與審核階段實際撞到的七件）。全部 ⛔ 不開卡，除第 ⑥ 件另議。**

  1. **`notes` 被歸為「唯讀動詞」，但它會寫 Project 投影欄、也會貼永久 `wf:reject`。** `core/verbs.md` 的分類與 PM 派工紀律（「唯讀動詞：`> /dev/null 2>&1; echo $?`」）都把它當純讀。實測卡面壞掉時 `wf notes 320` 是 **rc=1 且 stdout/stderr 全空 0 bytes**，遠端卻留一則永久拒收；「零輸出＋rc=1」逼人重跑，每次重跑再留一則（本卡實際發生三次）。⇒ **紀律改為「rc≠0 一律先回讀遠端、⛔ 不重跑」，⛔ 不按動詞分類**（執行者建議，PM 採納）。
  2. **`cli/src/wf/verbs/_write.py` 的 `reject` 只 `post_comment`、⛔ 不 `report`** ⇒ 拒收有遠端留言卻 ⛔ 無本機輸出，即上一條的成因。⚠️ **與設計缺陷 D1（issue #316，改號後卡 ID 為 `WF-003`）同族**——D1 管「留痕綁在 rc≠0 而非綁在被拒的寫入」，本條是同一條 `reject` 路徑的**輸出側**。⇒ **併入 `WF-003` 的卡面，⛔ 不另開卡。**
  3. **finding id 綁 `card_id`，而 `card_id` 可被改號。** `core/naming.md` §4 逐字 `<card_id>-R<iteration>.<查核序>-<序>`；`WF-005` 的 `card_id` 在同一輪內由 `WF-008` 改成 `WF-005` ⇒ 同卡 finding 橫跨兩前綴，`review` 的撞號檢查只做字串比對、⛔ 不要求前綴等於卡面 `card_id`，機器不擋、人讀會混。⛔ 無條文。
  4. **`F-執行-04` 在唯讀輪次上 ⛔ 不可能滿足。** 該條要求「產生工具與 artifact 同一 commit」，而研究／規劃／審核輪次的派工寫入授權為**無** ⇒ 執行者只能判 `found` 而 ⛔ 不是 `followed`。`WF-005` 的執行者實際遇到並如實記錄。
  5. **`wf edit` 對不存在的 issue 吐 traceback**（見上方第 11 件的更正）。
  6. **⚠️「擋錯了地方」——本條 PM 判達到開卡等級，⛔ 不只是登記，但需求方尚未表態故 ⛔ 不擴射程。** `WF-005` 執行者逐字：「被擋的是不可能成功的操作，沒被擋的是會毀資料的操作。」框架把 `wf edit --set card_id=` 防得很死（`edit.py` 專屬拒收 ＋ `_write.py` 的 `prepare_card` 被三個動詞共用 ＋ 每試一次留永久拒收），卻讓一條**原始 GitHub API PATCH** 直通卡面：⛔ 無備份、⛔ 無 dry-run、⛔ 無強制回讀比對、⛔ 無 D1–D4、⛔ 無投影回寫。實例＝PM 派工單的錯指令 `gh api -X PATCH … -f body=@<檔>`（`-f`／`--raw-field` **⛔ 不展開 `@file`**）把 15443 字元的卡面換成 174 字元的字面路徑字串，而 **HTTP 200 OK、`gh` rc=0、零失敗訊號**。正確形式＝`--input <JSON 檔>`。⇒ 建議（執行者提，PM 同意）：改號已發生一次、未來還會有，把這條路**收進 CLI**，例如 `edit --set card_id= --ruling <URL>` 開一個帶裁定的例外出口，⛔ 不要繼續用「禁止＋個案繞過」處理。
  7. **正面證據，一併記錄：`_write.py` 的 `reconcile_projection` 是本輪唯一不需執行者操心的機制。** 改完 issue body 隨便跑個唯讀動詞就把 Project 五欄補齊、**冪等**、6/6 行為一致、任一中斷點可續跑。⚠️ 但它同時是第 1 件的成因——同一個副作用讓「唯讀」這個詞在框架內不成立。

- **PM 在 `WF-005` 一輪內的四個錯（紀錄，⛔ 不是缺陷）**：① 派工單寫 `-f body=@<檔>` ⇒ 毀卡面、三則永久拒收（#320 的 `5614298078`／`5614302755`／`5614309495`）；② 壓平多行輸出只讀開頭 ⇒ 兩則永久拒收（見第 11 件更正）；③ 把 D3 豁免錨在 `issuecomment-5613411580`，該則全文 ⛔ 無「豁免」二字，實際依據在 issue #320 本文——**同型假錨的第 N 次**；④ 前一天登記「注意事項清單同一輪內會漂移」，隔天自己把 `WF-002` 移到 `執行/待辦`，使 `WF-005` 的 `notes` 由 24 掉到 20。

- **回看（2026-09-10 第三批）：三輪研究的結論，以及一件該開卡的。** 研究全程唯讀、六隻代理（4 Claude 子代理、`gpt-6-astra`、`gemini-3.8-flash-high`）分三輪跑，原始報告在 session scratchpad，⛔ 未進 repo。

  **① 起點：`roles/conduct-common.md` 的操作紀律構造上進不了 `wf notes` 的清單。** 三重卡死（實測）：該檔只有 `## 1`／`## 2` **沒有 §4**；`notes.py` 逐字 `if role is None or Path(relative).stem == role` 而 `conduct-common` 不在 `core/enums.md` 的 roles 四值內；`grep -cE '^- [FPT]-'` ＝ **0**（22 條全無 id）。⚠️ **決定性實測**：在副本上把它改成 `## 4` ＋ 22 條 `F-common-NN` 而 ⛔ 不動 CLI，`執行/executor` 仍是 16 條、**一條沒進** ⇒ 任何讓它進清單的方案**都必須改 `cli/src/wf/verbs/notes.py`**。

  **② 這不是疏漏，是「殘餘桶沒有出口」。** `core/platform.md` 逐字「平台擋不到的（UI 手改投影欄、T2 以上直推 main）＝紀律，**住 `roles/conduct-common.md` §1**」、同檔「哪些必須出現＝約定，**住 §2**，CI ⛔ 不驗」、`core/glossary.md`「違規判定條文**住 §2**」——框架**已經在做機械／非機械分流**，該檔就是分流後的殘餘桶，只是沒人接它到清單上。⚠️ 而 `docs/research/extract/07-conflicts.md` §C7 逐字「加一份 `conduct-common.md`…，**`brief` 對每個角色都注入**」已被 `REBUILD-DECISIONS` 逐字「C1–C14…**全部採納**」裁定採納——「加一份檔」做了，「注入」沒做，**⛔ 找不到任何反向裁定**。

  **③ C7 的成因逐字**：「05 反覆失誤表前六名（**行號腐爛 11 卡、驗證器出錯 11、宣稱超過證據 10、多居所只修一處 10、逐字轉錄失敗 7、shell 吃字 6**）全部是三角色都犯的操作失誤」。⚠️ **PM 於 2026-09-10 一天內逐條踩了上面每一項**，被六隻不同的執行者／查核者各自抓出來。

  **④ 「145 行」那件結案為「⛔ 不必處理」。** 「像注意事項的條文」全樹嚴口徑 244 行、進不了清單 **161 行**（⚠️ 該數是**下界**，嚴口徑要求含 `⛔` 或義務詞，而「`rc=0` 不等於成功」那條不含 ⇒ 真值 161–342）。其中 **145 行（90%）是刻意設計**（`core/naming.md` §5 的固定節表）。實際損害＝105 件 finding／mistake 裡只有 **7 件（6.7%）**根因落在那 145 行，其中 **6 件施為者是 PM 或需求方**（兩者本來就各有清單）、查核者 **0 件**。⚠️ 反證：**進了清單的條目照樣被違反**至少 3 件——`WF-003-R0.1-4` 逐字「resource-lock 已啟用（**notes 印出 F-resource-lock-01～04**）」而卡面仍缺 `worktree`。⚠️ 今天破壞最大的那件（`gh api -f body=@檔` 毀掉 #320 卡面、三則永久拒收）**在 145 行裡 ⛔ 找不到任何一條涵蓋它**。

  **⑤ ~~「加進清單」買不到遵守~~ ⚠️ 2026-09-10 同日由 `gpt-6-astra`（跨家族第四輪）推翻，PM 已逐項復驗，本條改寫。**

  **原文的三個宣稱全部超過資料能支持的範圍：**

  1. **「實質率由 8% 走到 57%，變數只有『被退回一次』」——⛔ 不成立，而且那不是退回。** astra 查原始留言的階段轉移是 `規劃/進行中 → 規劃/待確認 → 執行/待辦 → 執行/進行中`，而 `core/verbs.md` move 列逐字「**不論來源**，進入執行／進行中即 `iteration` +1 且 `source_sha`=null」⇒ **`iteration` +1 ⛔ 不等於被退回**。PM 復驗：57% 那份（`#311` 的 `issuecomment-5615841349`）`card_id=WF-002`、`role=executor`、`iteration=1`，**作者是 Claude 子代理、⛔ 不是 astra**。⇒ 該比較**同時改變了作者、階段、工作內容、派工內容、清單項目與分母**，⛔ 不是「同一張卡同一份清單」的對照。

  2. **「清單長度零解釋力」——超譯。** 資料只支持「**未識別出清單長度的因果效果**」（N=7、p=0.42）。⚠️ `modules/research/module.md` F-research-01 逐字「不顯著⇒**不可判定**」——不可判定 ⛔ 不等於零效果，而 PM 把它寫成了零效果。

  3. **「實質率」這個指標本身量的是標點、⛔ 不是證據。** astra 用控制樣本證明，PM 逐字復驗：`已完成檢查` ⇒ 判**空洞**；**同一句加一對反引號** ⇒ 判**實質**；而一句真正描述具體比對的散文「已直接比對 wf-card.core_pain 與 wf-intake.observation 相等；不更動原文。」⇒ 判**空洞**。⇒ **加反引號就能提高分數而 ⛔ 未增加任何檢查。** 另 astra 原判準把「含數字」另列，本紀錄的 6%／8%／15% 只算 `STRICT` 命中；**若數字也算，同三份是 50%／66.67%／70%**。

  ⇒ **「加進清單買不到遵守」目前 ⛔ 無證據支持，也 ⛔ 無證據推翻。** 可保留的只有：`conduct-common` 的 22 條本來就在規則樹裡、PM 讀得到，而 PM 於 2026-09-10 被六隻代理各自抓到違反其中 12 條、合計 34 次——**那是一個實例、⛔ 不是量化結論**。

  ⚠️ astra 同時反駁了另一個方向的過度推論：原紀錄據此暗示 astra 那三份「真的沒做那些檢查」——**原執行紀錄反駁了它**（需求輪有 `core_pain_equals_intake: True` 與 `build_return.py` 的成功執行紀錄、研究輪有 `measure_research.py` 的母體與抽樣輸出及未知鍵負控、規劃輪有 `build_plan.py` 與交叉表重算）。astra 自陳的實際缺點是「**把部分回應寫成宣告，⛔ 未逐項連到可核對證據**」，且「**⛔ 不能以判準粗糙替設計錯誤開脫**」——它的研究與規劃推論後來確實被兩家查核者打穿。


  **⑥ 機械檢查比清單有效兩個數量級。** 一支 10 行正則檢查器對 `conduct-common` §2 逐字「文件與碼的引用⛔ 不寫行號」掃 13 份交回單 ⇒ **163 個命中**（扣掉可能是合法逐字轉錄的 68 個仍有 **95** 個），**偽陽基線 ＝ 0**（同一支掃 34 個規則檔零命中）。而該條今天**自陳只抓到 1 次** ⇒ **自陳只抓到實際違反的 1/95 ～ 1/163**。⚠️ 但 hook／CI **⛔ 無掛勾點**：13 份交回單裡 **10 份完全不產生 commit**，163 個命中**全在 issue 留言、一個都不在 commit 裡**。檢查器要有效必須掛在**交回單入口**（`wf review`）。⚠️ PM 判「形狀正則 ⛔ 不是第零條說的內容判讀，與現行 D3 的 schema 驗證同類」——**此為 PM 判斷，⛔ 未經第二人複核**。

  **⑦ 需求方 2026-09-10 的「權重／情境化」猜想（逐字「如果清單裡配置權重或者增加情境 似 skill 的文本架構」）：結案為「已實現一半、另一半不值」。**
  - **情境化已實現**：條文本來就自帶 `when:`，寫成句首散文——`F-執行者-08/-09/-11` 逐字「**下研究或資料結論時**」、`F-需求-02/-03` 逐字「**開卡前**」、`F-resource-lock-02` 逐字「**派工前**」。而這批正是 `not_applicable` 率最高的（`F-執行者-10` **13/13**、`F-resource-lock-03` **9/9**）⇒ 執行者確實讀懂並照判。88 條 `not_applicable` 逐條歸類：**46.6% 屬「條文已自帶明示前提」**。⇒ 加 `when:` 欄位「**判不會更準，也不會更快**」，印／讀／寫三個成本都不動。
  - ~~**權重零效應**~~ ⚠️ **同日由 astra 推翻為超譯，改寫**：資料顯示的是「**在本母體的位置變異範圍內（絕對位置只在 3–4 個值間移動）⛔ 未觀察到位置效應**」，⛔ 不是「零效應」，也 ⛔ 不能推出「重排不會改變任何一條的答案」。同理第三輪的「加 `when:` **判不會更準也不會更快**」亦為超譯——資料只支持「⛔ 未觀察到差異」。⚠️ F-research-01 逐字「不顯著⇒不可判定」。**配權重三條路全堵死（寫條目上＝T4／PM 每卡配＝PM 做內容判讀／專案層配撞 `core/verbs.md` §3「只能加嚴」）這一段 ⛔ 不受影響，它是規則推論、⛔ 不是統計推論。**
  - **`not_applicable` 真值 ＝ 27.2%**（原 30.2%，扣掉 6 條「CLI 根本沒印卻超集回答」與 5 條「標不適用但實質已執行」）。其中 **CLI 從卡面事實判得了的只有 4.9%**、角色歸屬就能解決的 3.9%、**只有 AI 判得了的 18.4%（＝現況）** ⇒ 一個 T4 規則改動換 4.9% 的印量，**不值**。

  **⑧ ⚠️ 條目層級的 CLI 判 ⛔ 不做，但理由 ⛔ 不是 PM 先前說的那個。** PM 曾判「會繼承 `WF-004` 的靜默翻面缺陷」——**實測推翻**：會讓 `stat-redline` 翻面的卡面形狀恰好就是 D3 會擋掉的形狀（`tier_basis` 退化成字串 ⇒ rc=1、拒收逐字「/tier_basis: 不符合 type」），而 `notes.py` 的 `enabled_modules` 之後**緊接 `check_card`** ⇒ 在 `notes`／`brief` 上「紅線模組被靜默關掉」**目前不可達**。真正的理由是**粒度**：模組層級一次進出 3–4 條是**看得見的區塊**（今天兩次都被執行者接住並查出根因），條目層級一條消失**⛔ 無任何輸出、⛔ 無計數差** ⇒ **同一個錯誤失去可偵測性，這是缺陷修好後也不會消失的性質**。

  **⑨ ⚠️ 唯一該開卡的：模組 `adds.notes` ⛔ 無角色維度。** 根因實測：`notes.py` 逐字 `_file_notes(root, relative, '2', 'module')`——**模組 §2 完全沒有角色參數**，角色過濾只存在於 `roles/*.md` 那一支；而 `adds.notes` 是純字串陣列（`["F-resource-lock-01", …]`）**⛔ 無角色欄**。後果：`F-resource-lock-02` 逐字「**派工前**對照 `git worktree list`…只列進**派工單**」＝**PM 的動作**，卻印進執行者清單（9 次出現、5 次標不適用）；`-03` 同型 9/9。**兩條合計 14 條（88 條 `not_applicable` 的 15.9%）。零條件機制、零權重，修的是真錯。**

- **PM 的操作改動（2026-09-10，⛔ 不是規則改動、⛔ 不是卡）**：派工單的「寫入授權、唯讀範圍」人填段改為**機械從規則檔抽出全文貼上**（`roles/<role>.md` §2＋§3、`conduct-common.md` §1＋§2），**⛔ 不挑選、⛔ 不手抄**。⚠️ 起因：PM 先前手抄的涵蓋率量得為 **36%**（22 條抄了 8 條），而手抄本身正是 `conduct-common` §2 逐字「引用逐字⛔ 不節略」要擋的失效模式。體積：executor 35 條／4.9KB、reviewer 34／4.9KB、pm 39／5.9KB、requester 28／4.1KB。⚠️ 它在**人填段、⛔ 不在清單** ⇒ ⛔ 無 `note_responses` 覆蓋要求，**只買到「執行者看得到全部 22 條」，⛔ 不買遵守**（見 ⑤）。

- **回看（2026-09-10 第四批）：六件操作面與機制面的實測發現，全部 ⛔ 不開卡。**

  1. **PM 給所有 Claude 子代理用同一個 `actor` 字串，使 `resource-lock` 對它們互相看不見。** `modules/resource-lock/module.md` §0 逐字 `"enable_if": {"kind": "other_actor_card_in_state", "state": "進行中", "min": 1}`，判定看 `owner.actor` **不同**才算 other actor。實測：`OPS-001` 的執行者提交前重跑 `notes` 得 20 條而非派工單寫的 24，原因是板上另一張進行中的 `WF-002` 的 `owner.actor` 與它**同為 `claude-opus-5-subagent`** ⇒ 模組停用。⚠️ **這是 PM 的操作錯誤、⛔ 不是 CLI 缺陷。** 改法：actor 帶卡號（`claude-opus-5-sub-<card_id>`）。改後立即生效——派 `WF-004` 時印出與 `WF-003` 在 `notes.py`／`brief.py`／`review.py` 三處的真實交集，先前同 actor 時 `resource-lock` **完全看不到**。

  2. **`move` 的資源交集會把卡跟自己算成交集。** `move_modules.py` 的 `resources_intersection` docstring 逐字「owner 非 null 而 `owner.actor` 與本卡**不同**的卡」——排除條件是 **actor 而非卡號**；而 `owner` 正是派工邊才寫的 ⇒ 算交集時板上讀到的還是**上一輪的 owner** ⇒ 自我命中。實測兩次：`move 311 --to 執行/進行中` 印「… ↔ WF-002」（本卡即 WF-002）、`move 313 --to 規劃/進行中` 四項全部 `↔ OPS-001`。⚠️ 行為無害（只是印），但**使交集印失真**。

  3. **`strict_required_status_checks_policy=true` ＋ `required_linear_history` ⇒ 裁決永遠不涵蓋真正落到 main 的東西。** 前者要求分支先追上 base 才能合，後者禁 merge commit ⇒ **只能 rebase**；而 rebase 改寫 SHA ⇒ 查核者綁定的被審 SHA 失效。`WF-005` 實測：`gh pr merge --squash` rc=1 逐字「the head branch is not up to date with the base branch」，rebase 後 head 由 `b82f4e7` 變 `199354c`，查核者逐字警告「**本裁決不涵蓋新 SHA**」並要求重新確認。⚠️ 該卡靠「rebase 後的 tree 等於查核者第一輪隔離驗過的 merge-tree（`51ce493c…`）」＋第三輪窄複驗（`range-diff` 三個 commit 全 `=`、`cmp rc=0 / 0 bytes`）繞過，**下一張若 rebase 有衝突就繞不過**。與 `OPS-001` 同族（規則與平台落差）。

  4. **`brief` 的「前輪 findings」段 ⛔ 不讀執行者的 finding。** `brief.py` 的前輪列逐字「同 iteration 內時間序最後一則 **`role=reviewer`** 的 `wf-return`」⇒ 執行者交回單裡的 finding **完全不進派工單**，`brief` 印「無前輪」。實測 `WF-005` 進執行階段時前兩輪共 11 條 finding，`brief` 仍印「無前輪」；`WF-002` 進審核時前三輪的 finding 同樣不印。⇒ **每一輪的執行者都必須人工去讀留言**，而派工單字面會誤導他以為沒有前輪。

  5. **代貼裁決的路徑產不出機讀裁決。** `gemini-3.8-flash-high` 交的是純文字，PM 依 `core/naming.md` §3 逐字「代貼裁決・來源：`<模型名>@<工具名>`・被審 SHA：`<sha>`」代貼（`#311` 的 `issuecomment-5616759931`）——**但 ⛔ 無 `json wf-return` 區塊** ⇒ `move` 會印「裁定留言無 `wf-return`／`wf-ruling` 區塊」，T4 的「兩則裁決」在機讀上只算得到另一則。⚠️ 而 Gemini 是本專案目前唯一的第三家族來源。

  6. **`cli/tests/test_project_stage_skeleton.py` 釘住了 repo 的空白。** 該檔 docstring 逐字「⛔ 不斷言本 repo 缺任何東西」，而 `test_skeleton_has_no_frontmatter_and_stays_empty` 實際上把交付檔複製進合成樹後斷言它是空的 ⇒ **`.wf/stages/*.md` 一填第一批 `P-` 條目就會紅**。實測：把 `conduct-common` 的條文抄成 `P-` 的變體跑 `cli/tests` 得 **`2 failed, 891 passed`**。⚠️ 該測試是 PM 於 `WF-001` 建的，形態同已登記的「測試別釘 repo 的空白」。

  7. **PM 差點開一條假 finding：`edit --set notes+=` 其實有實作。** PM `grep '+='` 只命中 `spec_version += 1`，據以判定「規則指定的語法 CLI 沒實作」；實際 `edit.py` 逐字 `if key == 'notes+': key = 'notes'; value = current[key] + [value]`。⚠️ 根因是 `roles/conduct-common.md` §1 逐字「**實跑，⛔ 不讀碼推論**」——PM 用錯的 grep 形狀推論，⛔ 未實跑。

- **回看（2026-09-10 第五批）：跨家族第四輪對前三輪的四項修正（`gpt-6-astra`，全程唯讀）。**

  ⚠️ **⑤ 與 ⑦ 的改寫見上，此處記其餘兩項與方法論教訓。**

  1. **「設計者＝查核者、只隔幾輪」的效力被限縮。** astra 今天在 `WF-002` 的裁決裡逐字「**我不維持前三輪歸納為已證根因**」，推翻了它自己在研究與規劃階段提的核心設計，該卡因而退回規劃。⚠️ **但 ⛔ 不得據此推論「隔輪重審有效」**——astra 逐字指出「查核派工單**直接要求攻擊前輪歸納、許可句及影響面**，因此 ⛔ 不能把改善全歸因於隔輪或換角色」。⇒ 可保留的四條：清單 ⛔ 不能**保證**遵守與設計正確，但**尚未證明**它不能改善任何一項；換角色**有機會**改變反證方向，而**模型家族名稱 ⛔ 不能代替證據獨立性**；作者與查核者沿用同一錯誤判準時，**再多輪也可能共同放行**；查核者的發現**仍須核實**——兩家裁決對 #22／#32 存在分歧，**⛔ 不能以共同退回替所有細部論證背書**。

  2. **「查核者的攻擊清單」⛔ 不得從「自陳不足」推成「執行者不必收到」。** astra（今天同時當過 `WF-002` 的執行者與查核者）判：可作**試驗方案**，保留同一規則來源、讓執行者仍收到適用紀律、查核者另取反證問題與所需證據；⚠️ **執行者若失去動作前提醒，查核只能在交付後發現部分問題**，對已發生的覆寫、越權或證據遺失尤其如此。有效性應比較**被獨立確認的漏失、誤報、返工與成本**，⛔ 不是 `found` 數或文字標記率。

  3. **⚠️ 方法論教訓（PM 自陳）：PM 把「不顯著」寫成了「零」，把「一個實例」寫成了「量化結論」，並且是在同一天內就 commit 進判準檔。** 三處超譯（⑤ 的兩處、⑦ 的一處）全部由**跨家族**查核抓到，⛔ 不是 PM 自己發現的。⇒ 這正是 `roles/conduct-common.md` §2 逐字「數字帶日期或指令；⛔ 不寫現況數字」與 §1「引用零命中、零失敗或做複驗前，先用會響的樣本證明工具有效，附負控輸出」要擋的——**PM 的「實質率」判準從未做過負控**，而 astra 一做（加反引號）就翻。

  4. **astra 自陳的偏誤**（逐字）：「我同屬被批評的模型家族，可能偏向強調指標缺陷；所以我同時承認回應追溯不足與設計推論失敗。」⚠️ 本紀錄採信它的**事實查證**（階段轉移、作者身分、控制樣本），⛔ 不因該偏誤折扣；其**評價性結論**（如「不能以判準粗糙替設計錯誤開脫」）與它自己的立場一致、⛔ 不另行加權。

**兩件目前都⛔ 無受害者**——卡ID 能用、12 次只是慢。原裁定「等第一批四張卡（#311–#314）做完再開卡處理」**已於 2026-09-10 被需求方覆寫**：卡ID 那件改為 **WF-002 完成後立刻開卡**並修正既有卡 ID（見上），`edit` 單欄那件仍留在第一批之後。
- **工具故障修復的有限例外（需求方 2026-09-10 裁定開）**：`wf open` 開新卡穩定失敗（2/2），而規則說工作走卡、走卡要先 `open`——**框架修不了自己的 blocking CLI bug**。自舉期那條例外**⛔ 不能沿用**：它逐字寫著「授權⛔ 不涵蓋 CLI 碼」，且已隨重構期結束失效。故另開一條，射程逐字如下，⛔ 不得外推：
  - **啟用條件三件全中**：①必要的 CLI 前置功能故障（沒有它就走不了卡）；②已有可重現證據；③沒有正常可行路徑。
  - **範圍只含**：恢復該功能、其回歸測試、以及必要的恢復作業（把故障留下的半寫狀態收乾淨）。
  - **⛔ 不豁免**：分支、獨立查核、平台 required check。例外只免「先開卡」，⛔ 不免其他任何一項。
  - **功能恢復即失效**，之後回到走卡。
  - **⛔ 不回填虛構歷史**：⛔ 不得為了讓流程好看而手寫卡面 JSON 假裝卡存在；恢復作業要補連結實際紀錄。
  本次啟用的證據＝issue #306 上兩則逐字 `拒收・D3・not enough values to unpack (expected 1, got 0)` 的 `wf:reject` 留言，與 `cli/src/wf/verbs/_write.py` 的 `projection_values`（逐字 `item, = (item for item in project['items'] if item['id'] == item_id)`）。⚠️ 本條初版釘的是行號 `_write.py:45`，而修那個 bug 的 PR #307 自己把那行推走了（head 的 `:45` 已是別的東西）——與稍早收過三次的假錨同型，第四次。已改成符號引用，合乎本紀錄自己登記的「引用必須指向解析得到的居所」。
- **回看（2026-09-10 登記，第一次真實使用就撞到）：`core/tiers.md` §1 的「T0／T1 直推 main」被第 7 步自己設的 ruleset 擋掉。**實測：main 上一個純文件的 T0 更正 `git push origin main` 逐字回 `! [remote rejected] main -> main (push declined due to repository rule violations)`。成因＝ruleset `20768920 main must be green` 帶 `required_status_checks`，直推沒有 PR 就沒有 check 可過，一律擋。所以規則側寫的「T0／T1 直推 main」在 aiwf 這個 repo 上**無法執行**，每一張 T0／T1 也得開 PR。兩條路擇一，交需求方裁：(a) 改 `core/tiers.md` §1，承認有 required check 的 repo 上 T0／T1 也走 PR（只是免查核者）；(b) 改 ruleset，讓 T0／T1 有繞道（例如 bypass actor），但那會讓「main must be green」出現破口。⚠️ 這是第 7 步（框架接自己）第一次真實使用就暴露的規則↔平台矛盾，正是自舉要驗的東西。
- **回看（2026-09-09 登記，需求方停損）：施工痕跡要靠「引用必須可解析」這條規則收，⛔ 不靠正則清單。**PR #303 用九輪、17 個 commit 換到 73 檔 **+212／−203＝淨增 9 行**，其中 16 個 commit 是收 finding；（⚠️ 本條初版寫「+210／−203＝淨減 7 行」錯兩處：210 是收尾前的中途量測，且 210−203 是淨**增** 7、⛔ 不是淨減。合併後 `git diff --shortstat 021802d ab78685` 與 PR API 皆為 `+212/-203`。這正是本條在講的同一種錯——在寫「⛔ 不得再寫完整性宣稱」的那一句旁邊，自己把數字寫錯。）六個「母體的洞」全是由查核者想出新正則才發現（大小寫敏感、`_` 不構成 `\b` 邊界、路徑清單漏 `.github`、`--include` 漏 `.json`、批次條號 `六條裁定 #6`／`第 8 條`／`第 9 條探針`、代名詞 `本步`／`本片`）。**根因＝需求是語意的（讀者查不查得到出處），檢查是機械的（正則），兩者不可能收斂**；而且規則側現在**沒有任何一條**要求「註解／docstring 的引用必須指向 repo 內解析得到的居所」——唯一相近的 `roles/pm.md` §3「`cli/src` 指得出符號」只用於判設計缺陷，不是通則。所以清的是症狀，下一輪建造會照樣長出新的片號與批次條號。**正解**＝在 `roles/conduct-common.md` §2 或 `core/naming.md` 加一條：引用必須指向 repo 內解析得到的居所（檔＋節，或明確標為外部可查的 URL／issue），配一個 CI 檢查解析不到就 rc≠0；判準因此從「像不像片號」變成「這個引用解析得到嗎」，那才是機械可判的，且能擋住復發。載體＝自舉結束後一張 T4 卡（`core/tiers.md` §3 `rules`，規則與 CLI 同 PR）。⚠️ 在那之前，**任何人 ⛔ 不得再寫「清盡」「零殘留」這類完整性宣稱**，只能寫「這道指令在這些路徑下命中 N」。
- **回看（2026-09-09 登記，PR #303 宣告「另一片」的收尾痕跡）**：PR #303 的「⛔ 不做」節列了五類刻意不清的施工痕跡，第六輪查核者 grep 證明其中三類**在本清單零命中**（`查核輪引用` 0、`C0N` 0、`cpbl-analytics#98` 0；負控：同檔「回看」11 命中），「已登記」是假的。現逐條登記，數字皆為 2026-09-09 `b60f93f` 實測：① **`cli/tests` 的查核輪引用**——`驗收 <N>` 67 行 11 檔、`FINAL` 59 行 7 檔（`FINAL-` 41 行）、實體名（`astra`／`gemini`／`Codex`／`子代理`）9 行 4 檔。這批是查核輪的驗收項編號與跨實體審查來歷，要逐條讀語意才分得出哪些是編號、哪些是句子的一部分，性質與任務號／片號的機械刪除不同，故與 #303 分片。⛔ 不與 `C<NN>`／`S<NN>` 混為一談——後者已於 `3481caa`／`6f2a4f9`／`25a3962`／`54de772` 清過四輪。⛔ **不寫「清盡」**——需求方 2026-09-09 停損（見下一條）：這個判準是語意的（讀者查不查得到出處），而檢查是正則的，兩者不可能收斂，九輪下來每輪都有人想出新正則再找到一批。現況只能這樣說：`grep -rniE '(^|[^0-9a-z])[sc][0-9]{2}([^0-9a-z]|$)|_[sc][0-9]{2}([^0-9a-z]|$)' core roles stages modules cli .github ADOPTION.md README.md` ＝ **21 命中，全部在 `cli/tests`**，分三類：① 5 行在 `test_gh_scope.py:53`／`test_gh_write_recording.py:19/89/94/95`——`s05` 識別字、目錄路徑與被烘進 request payload 的大寫 `S05` 字串；② 15 行在 `fixtures/s05/*.json`——錄放帶，`write_restore.json` 錄的是遠端 issue #295 的 body 本身；③ 1 行在 `fixtures/gh/ancestor.json`——compare API 錄下的 commit patch，內含 `3481caa` 後來刪掉的那個 `（C11）`。②③ 改它等於把錄音改成偽造。**這道指令零命中只證明這道指令沒找到東西，⛔ 不是完整性證明。**
② **`modules/stat-redline/module.md:67` 的 `cpbl-analytics#98`**——F-stat-redline-03 的例子出處，是外部 repo 的 issue，讀者查得到，與查不到出處的派工單引用不同類；要不要清由需求方定期回看時裁。③ **`core/platform.md:16`／`core/naming.md:15` 的 `aiwf` 硬編**——`aiwf 只留 squash`、`aiwf 種子 areas`，框架要給別的 repo 用時這兩處得改成專案層設定的引用；載體＝第一張真實卡跑完、確認 `.wf/` 的形狀後的一片。④ **`CLAUDE.md` 5 處、`AGENTS.md` 7 處的重構期敘述**——「本 repo 正在第三輪重構」「⛔ 不得引用 archive」之類，重構宣告結束時才能改，⛔ 不在重構期間先改（改了就自相矛盾）。**2026-09-09 需求方裁定重構期結束，已落地（PR #304）。**⑤ **規則檔條級的 `archive/issues/*` 連結 2 處**——需求方 2026-09-07 已裁「檔級刪、條級留」，本項只是備忘，⛔ 不重開該裁定。
- **回看（2026-09-09 登記，PR #301 末輪兩家審的三條非阻擋項）**：① `cli/src/wf/verbs/snapshot.py` 的 `_encodable` 往返宣稱過度承諾——孤立代理碼點 2,048 個全部往返等值（astra 窮舉實測 `ALL_SINGLE_SURROGATES_ROUNDTRIP True 2048`），但相鄰高低代理**配對**（如 `'\ud800\udc00'`）轉義後經 `json.loads` 會合成單一碼點、不等值（實測 `ROUNDTRIP … False`）；未證明正常 GitHub 輸入可觸發，屬措辭而非行為，宣稱要限定為「孤立代理碼點」並明載配對的合併限制。② `cli/tests/test_snapshot_verb.py` 的 `LONE_SURROGATE = '\ud800'` 只覆蓋高代理——astra 把正則縮成 `[\ud800-\udbff]` 砍掉全部低代理後 40 項全過，是真的覆蓋洞；該參數化成 `\ud800`／`\udc00`／`\udfff` 並同驗落檔往返與印出邊界。③ **其他六個動詞的拒收留言編碼邊界**：`open`／`move`／`edit`／`notes`／`brief`／`review` 遇同類碼點時 `_write.reject` → `client.post_comment` → `gh/client.py::_request` 一律拋 `UnicodeEncodeError`、拒收留言送不出（astra 六個動詞逐一實測，逐字 `open UnicodeEncodeError reject_payload=…` 等六行），共同違背 `core/verbs.md` §2「每次拒收寫一則 `wf:reject` 留言」。
  ⚠️ ③ 該不該進**設計缺陷類**，暴露 `roles/pm.md` §3 判準的一處歧義，一併交定期回看裁：判準逐字是「受害點 ≥2 個不同動詞**或消費點**」。按「動詞」數＝6，過門檻；按「消費點」數＝**1**（六個動詞共用同一條 `reject → post_comment → _request` 路徑，修一處即全好），不過門檻。判準當初的推導目的是分辨「設計錯」與「這一處寫錯」，而本案是後者——PM 傾向**判為一般缺陷、⛔ 不進設計缺陷類**，修法＝在 `_write.reject` 或 `gh/` 的序列化邊界做與 `snapshot._encodable` 同形的處理。但判準字面兩讀皆通，故⛔ 不自行裁定。與 [D1]／[D2] 的差別：那兩條的受害點是**不同路徑上的不同錯**，本條是同一條路徑的同一個缺口出現在六個入口。
- **不一致（2026-09-09 登記）**：`core/glossary.md`「狀態面」逐字不含留言，`core/verbs.md` §2「（卡面 JSON 與留言）」是孤例；`cli/tests/test_snapshot_verb.py` 的 `assert_read_only()` 其 `WRITES` 漏列 `post_comment`。
- 缺 `--ruling` 的印：`core/verbs.md` move 印格所列各案在 CLI；第六案 結案/待確認→結案/退回 走清單（`stages/closeout.md` §4）；是否全收斂一併議。

## 待骨架文件決定（本紀錄⛔ 不裁）

模組管理形狀（每模組宣告：加的欄位／加的階段或狀態 delta／加的動詞或旗標／加的注意事項／啟用條件；專案層一份 modules 清單）、缺陷路徑位置、Log 居所、新 CLI 測試策略、這輪重構的停損條件、卡面 JSON 欄位集。

## 事實（2026-09-04 量到的）

- Project #4「cpbl-analytics 任務看板」217 張、29 欄；`交付狀態` 仍 15 值；`階段` 欄 217 張全空。
- 快照 2026-09-03 10:41：🏁完成 128／🛑已停止 34／💡需求 30／⏸阻塞 17／📦已合併 4／📥Backlog 3／↩退回 1。非終態 55 張＝cpbl 38＋aiwf 17。
- `gh project item-list` 的自訂欄位在本機回傳全空，可靠來源是 `origin/snapshots`。

## 卡ID 改號紀錄（2026-09-10 生效）

本節新增、⛔ 不改本檔既有任何一行；`:196`／`:198`／`:199` 是裁定當時的紀錄，逐字保留。

**逐字更正 `:199`**：該行末逐字「**7 張中 5 張要改**」有三個錯數字——① 漏了本卡自己（`WF-008`(#320)→`WF-005`），② 「7 張」不是發號池母體，實測母體＝**9 個帶 `wf-card` 區塊的 issue**（多出 `WF-000`(#295) 與 `WF-008`(#320)），③ 故實際要改的是 **6 個號、⛔ 不是 5 個**。改號執行當下（2026-09-10）以 `cli/src/wf/verbs/_common.py` 的 `repo_cards`（逐字 `client.issues(state='all')`）實測，`skipped` 為空。

改號映射（6 項，皆只改卡面 `json wf-card` 區塊內 `card_id` 的值，Project 的卡ID 投影欄由唯讀動詞的 `reconcile_projection` 對帳補上）：

| issue | 舊卡ID | 新卡ID |
|---|---|---|
| #312 | `CLI-003` | `CLI-001` |
| #313 | `OPS-004` | `OPS-001` |
| #314 | `CLI-005` | `CLI-002` |
| #316 | `WF-006` | `WF-003` |
| #317 | `WF-007` | `WF-004` |
| #320 | `WF-008` | `WF-005` |

⛔ 不動：`WF-000`(#295)、`WF-001`(#306)、`WF-002`(#311)。`WF-000` 留在發號池內——移出會使序號回退成已用過的號，牴觸 `core/naming.md` §1 逐字「只增不重用」。

改號後 per-area 的已用最大序號＝WF 5、CLI 2、OPS 1、DOC 0，據此的下一號＝`WF-006`、`CLI-003`、`OPS-002`、`DOC-001`。⚠️ `CLI-003`／`OPS-004`／`CLI-005`／`WF-006`／`WF-007`／`WF-008` 這六個舊號**將被重新發出並指到別張卡**；既有留言 append-only（`core/verbs.md` §2）⇒ 舊號的逐字引用一律**依當時值**解讀，各該卡上另有一則 `wf:log` 記映射。

依據（皆在 `ruan6047/ai-workflow`）：

- 改號授權與「與『只增不重用』沒有牴觸」＝需求方 2026-09-10 裁定，逐字「發錯的號 ⛔ 不是『已合法發出的號』，該條保護的是後者」，載於 <https://github.com/ruan6047/ai-workflow/issues/320> 本文「已裁定，⛔ 不用再議」段。
- 級別由 T4 降 T3＝<https://github.com/ruan6047/ai-workflow/issues/320#issuecomment-5612175160>（`kind=tier_change`）。
- `WF-000` 留在池內、⛔ 不碰「三位數起」第二處歧義＝<https://github.com/ruan6047/ai-workflow/issues/320#issuecomment-5613411580>。
- 改號步序（`move` → 改卡面 → 唯讀動詞對帳 → `edit --set branch=`）與歷史檔處置＝<https://github.com/ruan6047/ai-workflow/issues/320#issuecomment-5613923646>。

## 研究輪次的量測紀律（PM 三次自錯，2026-09-10 至 11）

第五至八輪的跨模型研究裡，PM 的量測被抓到**三次錯誤，且是同一個形狀：判準比被量測的目標寬**。

| # | PM 用的判準 | 正確的判準 | 造成的偏差 | 誰抓到 |
|---|---|---|---|---|
| 1 | 留言**首行** | `core/verbs.md` §2 列的三種區塊 | 裁定記 3 則，實際 **17** 則 | Gemini（要 PM 跑指令追問而炸出） |
| 2 | `contains("json wf-ruling")` 子字串 | 某一行**逐字等於** ` ```json wf-ruling ` | `wf-ruling` 19→**17**、`wf-return` 19→**20**；PM 據此宣稱的「`wf:return` 首行裝 `wf-ruling` 2 則」與「`wf:log` 首行裝 `wf-return` 1 則」**兩格根本不存在** | Gemini 指令 → PM 複驗 |
| 3 | 有 ` ```json wf-note ` 圍欄就算讀得到 | CLI 的 `wf.gh.writes.block_value` 回傳值 | `wf-note` 記 3 則可讀，實際 **0 則**（那 3 則各含 3–4 個區塊，`block_span` 逐字 `if len(spans) != 1 ... raise CardBodyError`） | Claude 子代理（第八輪） |

**紀律**：分類與計數的判準要與**被分類物的定義**同源。留言類型的定義住 `core/verbs.md` §2 ⇒ 分類就用 CLI 自己的解析器，⛔ 不用首行、⛔ 不用子字串、⛔ 不用「圍欄在不在」。

⚠️ 第 1 項的諷刺要記下來：`core/verbs.md` §2 逐字「CLI 只讀三種留言區塊：`wf-return`、`wf-ruling`、`wf-note`；**散文與首行不讀**」——PM 用了 CLI 自己明文不讀的東西當分類鍵。

⚠️ 第 1 項**第七輪的 Claude 子代理同犯**（它把那 14 則記成「中文散文、人產的」，而那個首行是 `core/naming.md` §3 首行表最後一列逐字列著的代貼格式）。兩家同錯 ⇒ 是材料的錯，⛔ 不是某一家的錯。

⚠️ 第 2 項的後果不只是數字：PM 把**兩格不存在的現象**寫進派工單、標成「已複驗的事實」，拿去問兩家。Gemini 對那兩格的歸因因此作廢；Claude 子代理自己驗掉了。**餵給查核者的「已驗事實」若是假的，那一格的答案無論對錯都不計分。**

## 兩個 85% 是不同的東西（2026-09-11）

8 張卡、273 則留言的母體上，有兩個都接近 85% 的比例，**分子與分母都不同，⛔ 不可互相引用**：

| 名目 | 集合定義 | 值 |
|---|---|---|
| CLI **產**的 | 首行 ∈ {`wf:edit`, `wf:move`, `wf:reject`, `wf:return`, `wf:verdict`} | 232／273＝**85.0%** |
| CLI **讀不到**的 | 三種區塊皆無 | 233／273＝**85.3%**（另有 3 則區塊在而解析丟錯，計入則 236／273＝**86.4%**） |

有用的是集合關係，⛔ 不是那兩個比例：

```
P（CLI 產）= 232        R（CLI 讀得到）= 37
P∩R = 20               P\R = 212   ← CLI 寫了自己讀不回
R\P = 17               兩者皆非 = 24
人寫 = 41              其中 CLI 讀得到 17、讀不到 24
```

⇒ **那 17 則 CLI 讀得到的人寫留言全部是「裁定」**（14 則代貼裁定 + 3 則 `wf:ruling`）。
⇒ 人→CLI 的方向上，框架實際只跑通了「需求方裁定」一條線。

⚠️ `P\R` 那 212 則（`wf:edit` 143、`wf:move` 54、`wf:reject` 15）在 `core/naming.md` §3 的「CLI 讀」欄**逐字都是「否」**——它們從設計上就不是 CLI 的輸入。

⚠️⚠️ **本段原本接著寫「⛔ 不得用『CLI 讀不回自己寫的』去論證框架失敗，那等於要求 CLI 回頭消費自己寫的散文，正是第零條禁止的內容判讀」。後半句在 2026-09-11 的第九輪被量測推翻，已刪除。** 見下節「第九輪：212 則稽核留痕的量測」。

## 「印出未寫入的旗標」涵蓋不了 `--set`（2026-09-11）

第七輪一份研究提出的最小動作是「動詞收到但沒寫進狀態面的旗標，一律印『`<旗標>` 未寫入：`<理由>`』，⛔ 不擋」，並逐字宣稱它「同時涵蓋已登記的 `move --source-sha` 靜默丟棄與 `edit` 兩個 `--set` 靜默覆蓋」。

**後半不成立。** 隔離副本實跑 argparse 這一層：

```
repo 現況（--set 無 action）  → args.assignment = 'b=2'
負控：action="append"        → args.assignment = ['a=1', 'b=2']
```

`edit.run` 的宣告逐字 `('--set', {'required': True, 'dest': 'assignment'})`。第一個 `--set` 的值在 `parse_args` 回傳**之前**就已經不存在，`edit()` 的簽章只收單一 `assignment` 字串 ⇒ **動詞層⛔ 無任何管道得知曾有第二個 `--set`**，「動詞收到」這個前提對這一例不成立。

⇒ 順序推論：**把 `--set` 改成可重複，是「印出未寫入旗標」能覆蓋這一例的前置條件，⛔ 不是兩個平行的選項。**
⚠️ 兩案都動 `core/verbs.md`（§1 動詞表或 §2 寫入契約）⇒ 依 `core/tiers.md` §3「含 rules ⇒ T4」**同級**，級別 ⛔ 不構成排序理由。

⚠️ `move --source-sha` 那一例**確實被涵蓋**（該旗標是單值、確實抵達動詞層），且嚴重度低一級：`core/verbs.md` §1 `move` 寫格逐字只說「交回時寫 `--source-sha`」⇒ 其他邊丟棄是條文預期的，欠的只是一行告知。

## 第七輪第四家（astra）回來後的兩處更正（2026-09-11）

第六輪有三條判在三家之間收斂。第七輪派了一份**⛔ 不含 PM 任何結論**的乾淨題目給 `gpt-6-astra`（跨家族），它的答案讓其中兩條要改。

⚠️ **先講它的量測邊界**：它的 `gh api` 全程連線失敗——七張卡共十四次讀取嘗試全部 `rc=1`、stdout 空，stderr 逐字 `error connecting to api.github.com`。它因此把七卡摩擦整題判**不可判定**，逐卡列「本文不可得／留言不可得／因果未知」，並逐字寫「API 連線失敗是本次研究環境限制，⛔ 不列入七卡的框架摩擦」，改以 288 項離線測試與隔離副本探針作答其餘題。**它對平台側的判定也因此不可判定。**

### 更正一・「三目標⛔ 不可機械化」的措辭寫得太寬

原記法是「三目標⛔ 不可機械化」。astra 逐字：

> 沒有可把整句直接判真假的通用機械判準；**但「因此任何部分都不可機械化」也不成立**。

它列出可機械驗的局部條件：**資料能否解析、識別來源是否存在、狀態是否有到終態的路、記錄是否可連回某次交付、已授權的讀取是否觸發遠端寫入**（居所分別在 `core/verbs.md` §2、`core/state-machine.md` §5、`core/return.md` 與相應 CLI／測試）。

⇒ **正確措辭**：整句不可機械化；**局部可觀測條件可以機械量，但那些是觀測量、⛔ 不是三目標的總裁判**。

⚠️ 這與第六、七輪三家的論證**⛔ 不衝突**——它們證的是「整句不可機械化」（第零條自相矛盾論證＋三目標三詞在規則本體零命中，附兩個負控），**⛔ 沒有證「任何部分都不可」**。是 PM 記錄時把前者寫成了後者。**這是 PM 的記錄錯誤，⛔ 不是研究結論改變。**

astra 另指出現行可承接三目標判斷的位置：`stages/requirement.md` §6 F-需求-03、`roles/pm.md` §3、`roles/requester.md` §1 的回看清單、`core/params.md` 的 `guard_review_period`；並逐字提醒「**現行回看清單的四類⛔ 不是『順暢已達標』的充要條件，週期尚未到也⛔ 不能倒推出中途摩擦不存在**」。

### 更正二・「平台層擋不可逆事故過度樂觀」的診斷換掉

第六輪三家講的成因是「平台擋不到 raw REST 抹卡面」。第八輪的唯讀量測換掉了這個診斷：

```
gh api repos/:o/:r/rulesets/20768920 --jq '[.rules[].type]'
["required_status_checks","deletion","non_fast_forward","required_linear_history"]
```

**ruleset ⛔ 無 `pull_request` 規則——平台⛔ 不要求 PR、也⛔ 不禁止直推。**
`gh api repos/:o/:r/rules/branches/main` 回同樣四項（負控：不存在的分支回 `[]`）。
`gh api 'repos/:o/:r/rulesets/rule-suites?ref=refs/heads/main'`：**15 筆推送評估紀錄、2 筆 `result=fail`**，兩筆都是 `required_status_checks` FAIL、actor `ruan6047`。

⇒ 擋下的⛔ 不是「直推」這個動作，是「**推一個 required check 還沒綠的 commit**」。
⇒ 真正的矛盾是「**required check 對所有級別一律適用**」撞上 `core/tiers.md` §1 給 T0／T1 的逐字「跳過」。

**連帶：`core/platform.md` P2 的 artifact 欄有兩處錯。**
一、逐字寫「…`reachability`**＋PR**」，那個「＋PR」在平台上不存在。
二、同一檔往下四行的註記逐字「平台擋不到的（UI 手改投影欄、**T2 以上直推 main**）＝紀律」——**與 P2 那一格不能同真**。量測裁定：註記那句對，P2 的 artifact 欄錯。
三、`cli-tests` 已是 required check，但 `core/ roles/ stages/ modules/` 全 grep **零命中**（負控：`reachability` 命中兩檔）。

⇒ **這改變 #313（OPS-001）的修法**：⛔ 不是去「拿掉 PR 要求」（那個要求根本不存在）。

### 第四家對「三目標」那句本身的判

astra 逐字：「**缺觀測與反事實，尚未能證明過度樂觀，更不能說已被推翻**」，並把該句判為**不可判定**。
⇒ 四家對第零條第四子句的分佈＝**不可判定 3、過度樂觀 1**；唯一判「過度樂觀」的那家是**唯一無法實跑、無遠端存取**的一家。**收斂在不可判定。**

### ⚠️ 這四輪研究最該記下的一件事

表面上是四家八份，實際上——**只有 Claude 一家同時具備「能實跑」與「遠端 API 可用」**（astra 遠端全掛、Gemini 兩樣都無）。
⇒ **任何依賴狀態面數字的結論，實質上只有一家在量。**
`core/tiers.md` §1 對 T4 逐字要求「兩位查核者彼此不同家族」——**這四輪⛔ 沒有任何一件狀態面發現滿足過這個條件。**

⚠️ 六份回報**全部主動自陳自己⛔ 不獨立**，⛔ 沒有一份主張自己是。其中 astra 逐字「本份是獨立重做局部量測與有限分析，**⛔ 不自稱全盲獨立實地研究**」，且自陳讀過本決策紀錄自身的回看自陳 ⇒ **⛔ 非全盲**。

## 第九輪：212 則稽核留痕的量測（2026-09-11）

需求方 2026-09-11 逐字「233/273 送研究」。本輪派工逐字寫死成敗判準：「**要的⛔ 不是意見，是一個能分辨的量測**」，⛔ 不接受沒有新量測的第三個意見。三家：`claude-opus-5` 子代理（能實跑）、`gpt-6-astra`（能實跑）、Gemini（⛔ 無 repo 存取，本輪改派「設計要跑什麼」）。

### 更正一・上一節那句後半是**假兩難**，已刪

原句逐字「要它們讀得回來＝要 CLI 回頭消費自己寫的散文＝第零條禁止的內容判讀」。

**反例就在同一份資料裡**：`P∩R = 20`（`wf:return` 15 + `wf:verdict` 5）由 `review` 動詞產（`core/verbs.md` §1 review 寫格逐字「貼一則留言…帶 `json wf-return`」），`move` 的硬擋與 `snapshot` 的 `last_cited` 都讀得回它們的區塊，而讀的過程**只認鍵不判值**。

⇒ **「CLI 讀得回自己寫的」與「CLI 做內容判讀」是正交的**；現行實作已經做了 20 次前者、0 次後者。第三條路是「CLI 寫**結構化區塊**、讀的時候只認鍵」——這套框架本來就在用。
⚠️ 前半句（那 212 則設計上不是 CLI 的輸入）仍成立，⛔ 未被推翻。

### 更正二・212 ≠ 233，⛔ 不可外推

`gpt-6-astra` 逐字：「233 則無區塊與 212 則指定稽核產物也不是同一集合；本輪對 212 的結果⛔ 不可外推成全部 233 的判決。」**PM 先前的交叉表混用過這兩個數。**

### 量到的（PM 已逐條複驗）

**一・`wf:edit` 的 hash 是 `sha256(json.dumps(值))`，對封閉值域可逆。**
```
$ printf 'null' | shasum -a 256   →  74234e98afe7498f…   ← 留言裡 tier 的原值 hash 逐字相同
```
對 `core/enums.md` 的封閉值域建彩虹表，129 個相異 hash 破 7 個（`null`、`""`、`[]`、`"T2"`、`"T3"`、`"T4"`、`"none"`）。
⇒ **稽核軌跡在它最不需要的地方自足（enum 欄），在它最該有用的地方不可逆（散文欄）。**
⇒ ⚠️ 附帶且未登記過的性質：**任何拿得到留言的人，都能把封閉值域欄的歷史值還原出來。**

**二・GitHub 原生 `userContentEdits` 已經免費提供了 197 則的全部資訊。**
逐卡版本數（PM 複驗逐字吻合）：#306 34、#311 35、#312 14、#313 30、#314 14、#316 24、#317 24、#320 48。
- 284 個 `wf:edit` hash 在原生史字典下 **284/284＝100.0%** 反推成功
- 54 則 `wf:move` 的轉移 **54/54＝100.0%** 可從原生史的 `stage`／`state` 序列逐字重建
- 現值／其他留言／repo HEAD／git 全歷史（1077 commit、2560 blob、131,831 行）四道都撈不到的 **23 個 distinct 被覆蓋值，只有原生史還留著**
⇒ `wf:edit` 143 + `wf:move` 54 ＝ **197 則的資訊是零邊際的**，而原生史是嚴格更強的一方（明文、帶編輯者、帶時間戳、零額外成本）。
⚠️ **反面**：`wf:reject` 15 則⛔ 不可與另外 197 則同批處置——拒收＝寫入沒發生 ⇒ issue 原生史**結構上⛔ 不可能有**對應版本。

⚠️⚠️ **本段原本逐字寫「`wf:reject` 15 則的資訊是唯一的」。那是全稱句，2026-09-11 被第十輪推翻，已改寫。** 逐字的推翻與正確的判準見下節「第十、十一輪」。

**三・下游引用：1/212，而可讀留言是 22/38。**
偵測器＝在語料中找 `issuecomment-<id>`；語料為全 repo 122 個 issue 的 body ＋ 1292 則留言 ＋ 8 卡全部歷史 body 版本 ＋ `git log --all` 全文 ＋ repo 全檔，共 4,420,965 字元。
負控雙向（PM 複驗）：真 id `issuecomment-5613425092` 回 2 命中；假 id `issuecomment-999999999999` 回 0。
- 可讀留言（`wf:return`／`wf:verdict`／`wf:ruling`／代貼裁定）**22/38＝57.9%** 被引用
- 那 212 則 **1/212＝0.47%**。差 123 倍。
另一組獨立負控（129 個 hash 對 `git log --all`／`docs/ core/ roles/ stages/`／全 repo 的 `wf:log` 與 `wf-ruling` 三道）**全部 0 命中**（負控：同管線對 HEAD 短 SHA 命中）。

**四・那唯一 1 則引用⛔ 不是「只能當時間戳」。**
`claude-opus-5` 判它「引用的是時間戳、值本身是從卡面讀的」；`gpt-6-astra` 判它「引用⛔ 不是任意貼號，hash 提供對外部候選值的驗證」。**PM 實跑，astra 對**：
```
留言裡的新值 hash              = 89a8d42b891a87cb460de9cb1341718584eb602c97f35e77a8aa8120fd709f3b
sha256(json(引用者聲稱的路徑)) = 89a8d42b891a87cb460de9cb1341718584eb602c97f35e77a8aa8120fd709f3b   相符
負控 · 錯誤候選                                                                              ⛔ 不符
```
⚠️ 但 astra 同時收窄：兩則引用**相隔 17 秒、該欄文字相同** ⇒ 只算**一個獨特被引目標／一種用途，⛔ 不能算兩個獨立成功案例**。

**五・`wf:edit` 是接得起來的承諾鏈，⛔ 不是「墓碑」。**
同卡同欄的鏈段 30 段、斷點 **0**；每條鏈的最後一個 `new_hash` 錨回卡面現值 **112/112**（負控：人造斷點回報 `[1]`、連續序列回報 `[]`）。
⇒ **Gemini 第八輪「單向墓碑日誌」的措辭被推翻。**

**六・`edit` 收得到 `--ruling`，但裁定⛔ 不進留言。**
`cli/src/wf/verbs/edit.py` 的 `post_comment` 逐字只寫 `f'{key}、{old_hash} → {new_hash}'`。6 次 `tier` 變更，「依哪一則裁定」**6/6 由該載體答不出**。

**七・框架自己⛔ 沒有把它們當稽核軌跡。**
`稽核軌跡` 在 `core/ roles/ stages/ modules/ docs/` 命中 **0 行**——**這個詞是本輪爭點的一方自己造的**。
`core/glossary.md` 逐字：「轉移記錄＝該次寫入的 `wf:move` 留言 | **不是事件流**」。
框架唯一具名的稽核機制 `snapshot`，在 `core/verbs.md` §1 逐字「⛔ 不寫狀態面」，其留言迴圈只取 `wf-note` 與 `wf-return`。

### 兩家的判與它們的分歧

| | 判 | 核心理由 |
|---|---|---|
| `claude-opus-5` | **197 則反證、15 則支持** | 197 則是 0 邊際卻佔 77.4% 版面 ⇒ 逐字違反第零條「前兩項不得以犧牲第三項達成」 |
| `gpt-6-astra` | **整體不可判定** | X3 **不可識別**：兩個世界產生完全相同的保存物 |

astra 的論證逐字（⚠️ 它明寫「**⛔ 不是『材料不足』即停止**」）：

> **世界 A**：執行者依靠該留痕消除一個錯誤。**世界 B**：執行者從卡面早已知道答案，引用只是沿用文字。
> 兩個世界都會產生本輪同樣的 273 則留言、同樣的兩個引用、同樣的工作樹雜湊、同樣的 tier 事件與提交訊息。**對這些保存物的任何確定性重新計算，兩個世界都會得到相同輸出。**

⇒ **這⛔ 不是「再量一次就好」，是「純讀取永遠分不開」。** 要分開只能做新的對照觀測（astra 的 R4：離線遮蔽對照試驗，它自算 T4、`sensitive=[statistics]`，本輪只提案未執行）。

### ⚠️ 本輪最該記的一件：登記會污染後續研究

`claude-opus-5` 子代理在自評裡逐字揭露：

> **更強的引導⛔ 不在派工單而在 repo**：`docs/research/REBUILD-DECISIONS-2026-09-04.md` 已逐字寫著「⛔ 不得用『CLI 讀不回自己寫的』去論…」，而 `CLAUDE.md` 逐字要求以該檔為準——**甲的結論已被寫進我被要求遵守的判準檔**。我量完才發現。

⇒ **「登記到決策紀錄」這個動作本身，第一次被證明會成為下一輪研究的引導。**
⇒ **紀律**：登記一條**研究結論**時，要與登記一條**裁定**分開標記。裁定是判準，研究結論⛔ 不是——後者進來的時候要標明它是「某輪某家的判，⛔ 未經跨家族覆核」，⛔ 不得讓後續輪次把它當成必須遵守的前提。本節之前的每一節都⛔ 沒有做這個區分。

## 第十、十一輪（2026-09-11）：留痕的判準、PM 的兩次代決定、以及兩條不動 append-only 的路

⚠️ **本節是研究結論與 PM 自錯的登記，⛔ 不是裁定。** 依上一節新立的紀律，後續輪次⛔ 不得把本節內容當成必須遵守的前提。

---

### 甲 · PM 的兩次錯，性質與前五次不同

前五次全部是**判準比目標寬**（首行當分類鍵、子字串當區塊測試、丟錯的區塊算成讀得到、裸數字當引用判準、「原生史沒有」寫成「唯一」）。這兩次⛔ 不是。

**甲1 · PM 替需求方換了判準，然後照自己的判準擴大射程。**

需求方 2026-09-11 逐字：「**我說的修改只有雜湊等不用留中間值的部分用編輯的 其他一樣留言**」。

PM 派出的第十一輪派工單逐字寫的候選分組：

| | 需求方逐字 | PM 派出去的 | 判 |
|---|---|---|---|
| `wf:edit`（hash 對） | 改編輯 | 改編輯 | 射程內 |
| `wf:move`（`<from> → <to>`） | — | 加進可編輯組 | ⚠️ **PM 擴的** |
| `wf:reject` | — | 開成問號問三家 | ⚠️ **PM 擴的** |
| 其餘 | 一樣留言 | 維持 append-only | 射程內 |

需求方的判準逐字是「**不用留中間值的部分**」。`wf:edit` 的中間態＝被覆蓋掉的舊值的雜湊；`wf:move` 的本文是 `<from> → <to>`，**⛔ 不是雜湊**，每一則是**一個獨立的轉移事件**，⛔ 不是被取代的舊值。
⇒ PM 把它放進去用的是**另一個**理由（第九輪量到它相對原生史零邊際）。**那是「資訊冗餘」，⛔ 不是「中間值沒意義」。PM 混用了兩個判準。**

⇒ **前五次錯的是量測；這一次錯的是代決定。** `roles/requester.md` §2 逐字「⛔ 不代填表單、⛔ 不代寫規格、⛔ 不代改執行者的產出」——精神相同：**PM ⛔ 不得替需求方換判準。**
需求方 2026-09-11 逐字「Ａ」裁定：⛔ 不追回、⛔ 不重派；`wf:edit` 那一格照常採計，`wf:move` 那一格降級為「研究另外提出的延伸，⛔ 不是需求方提的」。

**甲2 · PM 在兩份派工單裡都把「143」寫成單卡。**

逐字寫的是「把**一張卡**的 143 則 `wf:edit` 壓成一則」。實測逐卡：

```
#306 19  #311 18  #312 11  #313 23  #314 11  #316 17  #317 17  #320 27   合計 143
```

**143 是八卡合計，單卡最多 27。** 後果：一家的失敗模式分析（143 次 PATCH 撞 rate limit／lost update）建立在錯誤前提上。

---

### 乙 · 拆 append-only 的判準：三家收斂

三家各自給出不同表述，**切出同一條線**：

| 家 | 判準逐字 |
|---|---|
| Gemini | 衍生鏡像投影 vs 不可逆治理事件 |
| `gpt-6-astra` | 這段內容承擔哪一種證據責任；**容器可編輯、事件不可回寫** |
| `claude-opus-5` | 這則留言是不是**該事件的唯一 append-only 存放處** |

**PM 給的四個候選判準，三家獨立否決了同樣的兩個：**

| 候選 | 為什麼不行 | 誰驗的 |
|---|---|---|
| 誰寫的（人／CLI） | `wf:return`／`wf:verdict` **是 CLI 寫的**（`review.py` 逐字 `post_comment(number, 'wf:return' if role == 'executor' else 'wf:verdict', body)`）⇒ 會讓交回單與裁決可覆蓋 | PM 已複驗 |
| CLI 讀不讀 | `core/naming.md` §3 對 `wf:move`／`wf:edit`／`wf:reject`／`wf:log` **四個逐字都是「否」**⇒ 同一格四個值一樣，生不出三分法；且 `wf:log` 承載已被推翻的主張（`WF-001-R0.0-4`），讀不到仍要保留 | PM 已複驗 |

⚠️ `gpt-6-astra` 另指出 PM 一直用的那個理由不足：**「能重建狀態，⛔ 不等於能重建操作嘗試、拒收原因、當時引用與判斷。可取回也⛔ 不等於能防止改寫。」**

### 丙 · `wf:reject` 維持 append-only，但理由要換（3/3）

原登記的理由「資訊唯一」已被推翻（見本節開頭的就地更正）。實測：

| 量 | `gpt-6-astra` | `claude-opus-5` |
|---|---|---|
| 完整第二行在別處逐字出現 | 8/15 | 8/15 |
| 原因部分在別處出現 | 9/15 | 10/15（母體多含 repo 檔） |
| 在該家母體裡找不到第二份 | — | **7/15** |

**正確的三個理由（⛔ 與文字唯一性無關）：**
1. **結構**：`core/verbs.md` §2 逐字「檢查先於首次遠端寫入」⇒ 拒收發生在第一次寫之前，issue body 無新版本、Project 無值變動、git 無 commit ⇒ **那則 `wf:reject` 是唯一落地的東西**。
2. **邏輯架構**：累積表是**卡面成功落盤後的投影**；把「失敗的攔截」寫進去，等於要求 CLI 在一個狀態未更新的失敗路徑上去修改成功狀態的對帳表。
3. **流程訊號**：15 則只有 **10 種**不同的第二行，重複來自**同一個錯連續踩兩三次**——合併會抹掉這個訊號。

### 丁 · 壓成一則買到的是「則數」，⛔ 不是「閱讀量」（PM 已複驗）

八卡 274 則留言本文合計 **528,369 字元**：

| 首行 | 則數 | 字元 | 佔比 |
|---|---:|---:|---:|
| `wf:return` | 15 | 358,603 | **67.87%** |
| `wf:verdict` | 5 | 61,412 | 11.62% |
| `wf:log` | 19 | 38,951 | 7.37% |
| 其他（代貼等） | 15 | 30,784 | 5.83% |
| **`wf:edit`** | **143** | **21,355** | **4.04%** |
| `wf:note` | 5 | 10,866 | 2.06% |
| `wf:ruling` | 3 | 4,571 | 0.87% |
| `wf:move` | 54 | 1,207 | 0.23% |
| `wf:reject` | 15 | 620 | 0.12% |

⇒ **143 則 `wf:edit` 壓成 1 則，最多省 4.04% 的閱讀字元。真正的閱讀負擔是 15 則 `wf:return` 的 67.87%。**
⚠️ 這也收窄了先前登記的「212 則佔 77.4% 版面」：**那是則數佔比**，位元組佔比只有 3.07%～4.4%（兩家分母不同）。`gpt-6-astra` 逐字：「**77.66% 與 3.07% 都只能描述載體，⛔ 不能拿其中較合意的一個當作流程是否順暢的答案。**」

### 戊 · 副本上實作提案後量到的三件（`claude-opus-5`，PM 複驗其中兩件）

1. **⚠️ CLI 會改寫人的留言。** 人先貼一則首行是 `wf:edit` 的手寫筆記，跑一次 `edit` ⇒ `HIJACKED: True`，被 PATCH 的是那則人寫的留言。**這正是 append-only 要防的事，而且是 CLI 自己做的。**
2. **⚠️ 893 條測試全綠是假綠。** 提案版跑出 `893 passed, 1 skipped`，與未改版一模一樣——**沒有任何一條既有測試在同一張卡上跑第二次 `edit`**，PATCH 那條路零覆蓋。⇒ 驗收條件須逐字寫死「既有 893 條全綠⛔ 不構成驗收證據」。
3. **⚠️ 地基靠的是未寫進契約的行為。** GraphQL schema 內省（PM 已複驗逐字）：
   - `diff`：**"A summary of the changes for this edit"** ——官方說是「摘要」，實際回的是**整份本文**
   - `deletedAt`：`"Identifies the date and time when the object was deleted."`
   - `deletedBy`：`"The actor who deleted this content"` ⇒ **平台自己把這個保存處模型成可刪的**

### 己 · 兩條⛔ 不動 append-only 的路（PM 已複驗）

**路 A ·『`edit --set` 可重複』。** `wf:edit` 連續兩則間隔中位數 **10 秒**、p75 = 22 秒；60 秒窗聚類 **143 則 → 31 叢**：

```
#306 [11,1,4,2,1]   #311 [12,1,3,1,1]   #312 [10,1]   #313 [12,4,2,5]
#314 [10,1]         #316 [1,10,1,5]     #317 [1,10,1,5]   #320 [11,10,3,1,2]
```
⇒ **建卡時是一口氣把十幾個欄逐欄 `edit` 出來的。** 一次呼叫寫一次卡面、貼**一則多列**的 `wf:edit` ⇒ 143→31，**那一則仍是 POST，append-only 完全不動**。
⚠️ 這與本紀錄已登記的「`--set` 改 `append` 是『印出未寫入旗標』的前置條件」是**同一件事**。

**路 E ·『`minimizeComment` 摺疊』。** PM 複驗：
```
Mutation 有 ["minimizeComment","unminimizeComment"]；分類值域含 OUTDATED、RESOLVED
#320：68/68 viewerCanMinimize = true，已摺疊 0
```
摺疊**⛔ 不改本文、⛔ 不產生修訂、⛔ 不動 append-only**。
⚠️ 前十輪三家、需求方、派工單**都沒提過這條路**。

**五條路的可見留言數**（母體 274）：

| 路 | 可見留言 | 動 append-only | 要新寫入原語 |
|---|---:|---|---|
| 現狀 | 274 | — | — |
| **A** `--set` 可重複 | **162**（−40.9%） | **否** | 否 |
| B 累積表（只 `edit`） | 139 | 是 | 是 |
| C 累積表（`edit`＋`move`） | 93（−66.1%） | 是 | 是 |
| D 全刪 197 | 77 | 是（不可逆） | 否 |
| **E** 摺疊 212 則 | 展開 **62** | **否** | 是（只摺疊） |

⇒ **C 相對 A 的邊際＝69 則（佔 274 的 25.2%）**，那是「值不值得付戊列的代價」的全部標的。

### 庚 · 尚未收斂的一件

**`WF-007` 的 (a) 類候選題（答案只在 212 則裡）提不提得出來，兩家判準不同：**

- `claude-opus-5`：**提得出來**——#311 的四則拒收，逐則洩漏量測 **0/4**。
- `gpt-6-astra`：**提不出來**——它逐字：「#311 的 D1 事故被總結過，但把它改問『某一秒究竟拒了哪條邊』會是**我替實驗新增細節**，故不湊數。」

⇒ **分歧在「什麼算真的發生過」**：一家算「這個問題在歷史上被關心過」，一家要「這個**具體問法**在歷史上被問過」。**這直接決定 `WF-007` 有沒有 (a) 類題可用，需求方要裁。**

### 辛 · 三家對先後的判（3/3）

**`WF-007` 先跑，再動 `core/verbs.md`。** 理由一致：`core/verbs.md` 是 T4 且**不可逆**（留言一旦 PATCH，被覆蓋的中間態只剩修訂史 ⇒ `recoverable` 應記 `rollback_only`、⛔ 不是 `reversible`）；`WF-007` 是離線雙盲、**完全可逆**。
⚠️ `claude-opus-5` 另指出第二層：先改生產會讓試驗結論搬不回去——試驗比的是「143 則 vs 0 則」，上線後生產是「1 則表」，**那是沒被測過的第三種呈現**。
⇒ 建議把 C 與 E **離線渲染**成 `WF-007` 的第三、第四臂（零遠端寫入、零 CLI 改動，落在 `#330` 現有 `non_scope` 的「只產離線資料」內）。

## PM 的第七次同型失誤（2026-09-11）：沒讀就斷言別人錯，且是轉貼⛔ 未自己查

⚠️ **本節是 PM 自錯的登記，⛔ 不是裁定。**

### 做了什麼

第八輪的 `claude-opus-5` 子代理量到 ruleset 20768920 逐字**無 `pull_request` 規則**，並判「這改變 #313 的修法」。PM 複驗了 ruleset（那部分對），**⛔ 沒有回頭讀 #313 的卡面**，就在該卡貼了一則 `wf:log`（`issues/313#issuecomment-5624019590`），逐字寫：

> 本卡標題是「T0／T1 直推 main 與 ruleset 的衝突」。**衝突是真的，但成因跟本卡目前的敘述不一樣**，修法因此不同。

並給了「兩條可能的路」。

### 為什麼錯

#313 的 `core_pain` 全文逐字：

> 成因＝第 7 步自己設的 ruleset 20768920「main must be green」帶 required_status_checks（**實測 rules 為 required_status_checks／deletion／non_fast_forward／required_linear_history，bypass_actors 為空陣列，conditions 含 ~DEFAULT_BRANCH**），直推沒有 PR 就沒有 check 可過。…**兩條路擇一：(a) 改規則，承認有 required check 的 repo 上 T0／T1 也走 PR、只是免查核者；(b) 改 ruleset 開繞道（bypass actor），但會讓「main must be green」出現破口。**

⇒ **該卡從一開始就列對了四條 rule types、⛔ 從未主張 ruleset 要求 PR。** 而它的 `feature` 逐字已經選了 (a)。
⇒ **PM 給的「兩條可能的路」逐字就是卡面已經寫著的 (a)(b)，而且卡面已經選完了。**
⇒ PM 攻的是**一個那張卡沒有主張過的東西**。

### 仍然成立的兩塊（⛔ 不隨誤判一起收回）

1. `rule-suites?ref=refs/heads/main` 回 **15 筆推送評估紀錄、2 筆 `result=fail`**（皆 `required_status_checks` FAIL、actor `ruan6047`）——這是 #313 `core_pain` 沒有的**平台側實證**，反而**支持**它逐字的「直推沒有 PR 就沒有 check 可過」。
2. `core/platform.md` P2 的三處錯（artifact 欄的「＋PR」在平台上不存在；與同檔往下四行的註記「平台擋不到的（…T2 以上直推 main）」不能同真；`cli-tests` 已是第四個 required check 但 `core/ roles/ stages/ modules/` 全 grep 零命中，負控 `reachability` 命中兩檔）。
⚠️ 但第 2 塊**⛔ 不是 #313 的射程**——PM 先前說「要不要併進 #313 留給需求方裁」，**那個問法本身建立在誤判上**。P2 與 #313 選的 (a) 路線無關，應另開卡。

### #313 真正卡住的地方（與 PM 貼的完全無關）

`acceptance` 與 `verification` **都是空陣列**（`core/verbs.md` §1 `move` 逐字「離開規劃時 `acceptance` 或 `verification` 空」會印），另有 **14 條 finding** 未處置（兩份 `role=executor` 交回單，8 + 6 條）。

### 這一次跟前六次的差別

| 次 | 形狀 |
|---|---|
| 1–5 | **判準比目標寬**（首行當分類鍵、子字串當區塊測試、丟錯的區塊算成讀得到、裸數字當引用判準、「原生史沒有」寫成「唯一」） |
| 6 | **替需求方換判準後擴大射程** |
| **7** | **沒讀就斷言別人錯，且是轉貼子代理的判斷⛔ 未自己查** |

⚠️ **PM 對三家的操作紀律逐字要求「實跑，⛔ 不讀碼推論」。這一次 PM 自己沒做。**

⇒ **應落的紀律**：PM 轉述任何一家研究者對**某張卡**的判斷之前，必須先逐字讀該卡的卡面，並在轉述時標明「我讀過卡面／我沒讀」。研究者說的是「框架的某個理解錯了」，⛔ 不等於「那張卡錯了」——研究者通常⛔ 看不到卡面。

## 回看清單補兩條（2026-09-11，收 `WF-002` 交回單時實測）

⚠️ **本節是實測登記，⛔ 不是裁定。** 兩條都是**印、⛔ 不是擋**（`rc=0`），⛔ 未擋住任何寫入。

### 一 · `review` 的撞號偵測器對「跨 iteration 閉環」誤報

`wf review 311 --file <交回單> --role executor` 逐字印了五行：

```
finding_id 撞號：WF-002-R1.2-1
finding_id 撞號：WF-002-R1.2-2
finding_id 撞號：WF-002-R1.2-3
finding_id 撞號：WF-002-R1.2-4
finding_id 撞號：WF-002-R1.2-5
```

**五則全是假陽性。** `core/return.md` 逐字：

> 跨 iteration 閉環：本卡已有前一則 `wf:verdict` 時，`wf-return` **逐條重列前輪 finding 的原 `finding_id` 與新 `status`**；新 finding 由作者編新 id，⛔ 不重用既有 id。

⇒ **重列原 id 正是規則要求的行為。** 而同檔另一處逐字「`finding_id` 由作者依 `core/naming.md` §4 填，`review` ⛔ 不編、**只印撞號**」。

⇒ **偵測器分不出「重列前輪 finding」與「重用既有 id 開新 finding」。** 前者合規、後者違規，兩者在狀態面的形狀是「id 與既有 `wf-return` 相同」——一模一樣。
⚠️ 可分辨的形狀確實存在（重列的那則會帶新 `status`，且前一則是 `wf:verdict`、本則是 `wf:return`），但**現行偵測器⛔ 沒有用它**。

⇒ **後果**：執行者照規則做，卻每則都收到一行警示。⚠️ 更糟的方向是反的——**真正的違規（重用既有 id 開新 finding）會被混在一堆假陽性裡**，讀的人分不出來。

### 二 · 收 `role=executor` 的交回單要在**該卡的工作樹**裡跑

同一次 `review` 另印兩行：

```
未能比對本機分支頭
未能取得 git 附錄
```

成因：PM 在 `wf-framework-lightweight-ed47aa`（當時在 `main`）跑 `review`，而該卡的分支是 `wf/WF-002`、產出物在 `wf-WF-002` 那棵樹。

`core/verbs.md` §1 `review` 寫格逐字：「`source_sha` 依 role 取源…executor＝卡面 `branch` 在遠端的分支頭…**本機分支頭 ≠ 遠端頭時印、本機 git 狀態取不到時印「未能比對本機分支頭」（rc=0）**」，另「散文段附 `git log` 的 commit 清單與 `git diff --stat` 的改動面」。

⚠️ **⛔ 不影響已落地的內容**——`source_sha` 是 CLI 自己從卡面取的（`63a5532`，正確）。**失去的是散文段的 git 附錄**（commit 清單與改動面），那一段這次是空的。

⇒ **應落的紀律**：跑 `wf review <card> --role executor` 時，工作目錄要在該卡 `branch` 對應的工作樹裡。⚠️ 這一條在 `core/verbs.md` §1 與 `roles/pm.md` 都**⛔ 沒有寫**，目前只靠 PM 記得。

## 回看清單補三條（2026-09-11）：「全部查核者 APPROVE 才算完成」的三個缺口

⚠️ **本節是實測登記，⛔ 不是裁定。** 需求方 2026-09-11 逐字「**以後多方查核的時候 要等全部ＡＩ都認可報告才能算完成**」。

**該規則⛔ 不需要新增——已經存在。** `stages/review.md` §2 逐字：

> T4 收足 `core/tiers.md` §1 所定則數且**全部 APPROVE 才離開**；任一 REQUEST_CHANGES 依上一條分流。

需求方的這句話與現行條文一致。**但同一次查核發現三個讓它在實作上兌現不了的缺口**，全部登記於此，⛔ 不開卡（需求方 2026-09-11 逐字「Ａ」）。

### 缺口一 · 那句只寫了 T4，T2／T3 ⛔ 沒有對應條文

`stages/review.md` §2 逐字只涵蓋 T4。`core/tiers.md` §1 對 T2／T3 只寫「查核者獨立性＝不同實體」，**⛔ 未寫則數**，也⛔ 未寫「全部 APPROVE」。
⇒ T2／T3 收到一則 APPROVE 一則 REQUEST_CHANGES 時**⛔ 無條文可依**。

### 缺口二 · 機讀上根本數不到「全部」

`WF-002`（#311）iteration 1 的實況（PM 已複驗）：

| 查核者 | 家族 | 形式 |
|---|---|---|
| `gemini-3.8-flash-high@agy 1.2.0` | Google | PM 代貼（`issuecomment-5616759931`）⚠️ **⛔ 無 `json wf-return` 區塊** |
| `gpt-6-astra` | OpenAI | 機讀 `wf:verdict`（`issuecomment-5619185766`） |

`core/verbs.md` §2 逐字「CLI 只讀三種留言區塊：`wf-return`、`wf-ruling`、`wf-note`；**散文與首行不讀**」
⇒ **機讀只數得到一則裁決。**

- 若無區塊那則是 **APPROVE** ⇒ CLI 看不到它，「收足則數」永遠不成立。
- 若無區塊那則是 **REQUEST_CHANGES** ⇒ **「任一 REQUEST_CHANGES」這條漏掉它**，卡可能被判過。

⚠️ 本次兩則都是 REQUEST_CHANGES，結果碰巧正確——**那是運氣，⛔ 不是機制。**

### 缺口三 · 「全部」的分母⛔ 沒有定義，也沒有印項

`core/verbs.md` §1 `move` 的印項逐字含「裁定留言無 `wf-return`／`wf-ruling` 區塊」「裁定留言作者」「裁定留言不在本卡」，**但⛔ 沒有「已收 N 則／應收 M 則」這個印項**。
⇒ 「收足則數」要 PM 自己數，而數的依據是留言——正是缺口二會漏的地方。
⇒ **三個缺口串起來**：條文寫了「全部 APPROVE」，但 CLI ⛔ 不知道分母、⛔ 數不到分子、且 T2／T3 連條文都沒有。

### ⛔ 未開卡的理由

三件都落在 `WF-002`（#311）核心痛點的同一族——該卡 `core_pain` 逐字「同一個動作或欄位的執行者被寫在兩處而不一致」。
但 #311 現行射程是收 `R1.2-1`～`-4`，**擴射程會讓一張已退回一次、程序又被撤銷一次的卡更難收斂**；且 `OPS-002`（#334）正在處理「規則寫的與實況不符」的同一族。
⇒ 需求方裁定：**登記，⛔ 不動任何卡**，等 #311 與 #334 落地再一起看。

⚠️ 三件都是**印、⛔ 不是擋**層級的缺口，⛔ 未擋住任何寫入，也⛔ 未造成已知的錯誤放行。

## 回看清單補五條（2026-09-11，跑 `WF-002` 一整輪實測到）

⚠️ **本節是實測登記，⛔ 不是裁定。** 三條由執行者（`claude-opus-5` 子代理）實測、兩條由 PM 實測；**全部⛔ 未經跨家族覆核**（`gpt-6-astra` 當日第三次撞額度）。

### 一 · `--source-sha` 在非交回邊被靜默丟棄

`cli/src/wf/verbs/move.py` 逐字：

```python
if from_node == '執行/進行中' and to_node == '執行/待確認':
    updated['source_sha'] = source_sha
```

⇒ **只有 `執行/進行中 → 執行/待確認` 這一條邊才寫。** 其他邊收到 `--source-sha` 會**吃掉、⛔ 不寫、⛔ 不印**、rc=0。
`core/verbs.md` §1 `move` 寫格逐字也只說「…**交回時**寫 `--source-sha`」。

PM 實測踩到：在 `規劃/進行中 → 規劃/待確認` 傳 `--source-sha 7eca267…`，卡面 `source_sha` 維持舊值，**零印項**。PM 一度誤判成「被 `move` 打回」——**事實是從來沒寫進去過**。
⚠️ 唯一會響的是 D4（`source_sha` 不在遠端），而該值**在**遠端 ⇒ **驗過了、然後丟掉了**。

⇒ **這是已登記的「動詞收到但沒寫進狀態面的旗標，一律印」的第三個同型實例**（前兩個＝`edit` 的第二個 `--set`、`move --source-sha` 在非執行邊）。`CLI-003`（#332）是它的前置條件卡。

### 二 · `core/card-schema.md` §2「誰填」表的粒度不夠

該表把 `stage`／`state`／`owner`／`branch`／`source_sha`／`blocked` **放同一列**，逐字「CLI（`move`；…；`owner` 在 escalation 換人時由 PM `edit`，`modules/escalation` §1）」。

但這六個欄在 `core/verbs.md` §1 的可編輯性**完全不同**：

| 欄 | `edit` 硬擋欄逐字 | `edit.py` |
|---|---|---|
| `stage`／`state` | 逐字列出「只由 `move` 寫，D1」 | 專屬 `refuse('D1', …)` |
| `card_id`／`source_issue` | 逐字列出「建卡後不可改」 | 專屬 `refuse('D3', …)` |
| **`source_sha`** | 逐字列出「**`--set source_sha=` 不在遠端**」⇒ **明文把 `edit --set source_sha=` 當合法用法** | 專屬 D4 分支 |
| **`owner`** | **⛔ 完全沒提** | **⛔ 沒有任何專屬分支** |

⇒ 同一格裡，`source_sha` 是**明文允許 `edit`**、`owner` 是**兩處都沉默**。
⇒ PM 據此判：`owner` ⛔ 不用 `edit`（走四步邊補正）、`source_sha` 用 `edit` 補正（D4 把關；負控：傳 `deadbeef…` 得 rc=1）。
⚠️ **負控只驗到「會擋」，⛔ 未驗到擋它的是不是 D4**——印的是「無裁定連結」而非「拒收・D4・…」。

### 三 · `review` 的撞號假陽性隨 finding 數**線性成長**

先前已登記「`review` 對跨 iteration 閉環誤報撞號」。本輪量到嚴重度比預估高：

```
執行者重列 5 條 finding  → 撞號 5 則
執行者重列 11 條 finding → 撞號 11 則
```

`core/return.md` 逐字要求「逐條重列前輪 finding 的原 `finding_id` 與新 `status`」⇒ **卡愈久、finding 愈多，假陽性愈多**，而真正的違規（重用既有 id 開新 finding）被埋在裡面。

### 四 · `snapshot` 對壞掉的 `wf-return` JSON **完全靜默**（執行者實測）

`cli/src/wf/verbs/snapshot.py` 的留言迴圈逐字 `_, responses, _ = _block(...)`——**把解析失敗的原因丟掉**。
執行者真跑 `snapshot()`：對含壞 JSON 的 `#311`，**印項 0 行、輸出檔不含該留言號**。

⚠️ 對照 `core/verbs.md` §1 `snapshot` 列逐字「卡面 JSON 解析失敗或不合 schema 的 issue 號與原因…**⛔ 不從盤點母體排除**」——**那一條管的是卡面，⛔ 不管留言**。⇒ 留言層的壞 JSON 在離線稽核副本裡**無聲消失**。

### 五 · `move --ruling <壞 JSON 的留言 URL>` 的訊息與事實不符（執行者實測）

該留言**有** `wf-return` 圍欄、只是 JSON 壞掉。但 `move` 印的是：

```
裁定留言無 wf-return／wf-ruling 區塊
缺 wf-return 區塊
```

**兩句都與事實不符。** 成因：`comment_blocks` 把壞 JSON 壓成 `(False, None)`，**「沒有區塊」與「區塊在但壞」變成同一個回傳值**。

⇒ 與第三條同族：**偵測器把兩種不同的情形壓成同一個訊號**，而讀的人分不出來。

---

### ⚠️ 本輪 PM 的自錯（第 9–13 次，形狀與前八次同族）

| # | 錯 | 誰抓到 |
|---|---|---|
| 9 | 把 `roles/requester.md` §2 的「⛔ 不代改執行者的產出」冒充成 `roles/pm.md` §2，已散進本卡裁定與 `main` | `gpt-6-astra` |
| 10 | 派工單釘「⛔ 不 push」，抵觸 `roles/executor.md` §1「推分支到 origin」 | 執行者（`WF-002-R1.2-7`） |
| 11 | 引 `stages/implementation.md` §2 的「分支未 push 則走阻塞」時**漏掉前提「執行者失聯時」** | `gpt-6-astra` |
| 12 | 派工單缺材料（要研究者排除四案卻⛔ 沒附四案原文），同時又禁止它讀舊產出 | `gpt-6-astra` |
| 13 | 數「帶 `wf-return` 的留言」用**子字串**當判準得 9 則，**嚴格行首比對是 7 則** | 執行者 |

⚠️ 另有一件⛔ 未列入計數但同型：PM 在派工單逐字寫「**你的 r2 那份有這兩個鍵，r3 掉了**」——實測 **r2 與 r3 都沒有**，PM 憑印象寫的。執行者逐字回應：「**成因更正⛔ 不減輕我的責任**——漏段兩輪是我的產出問題，已進 `mistakes`。」

⇒ **第 13 次特別值得記**：它發生在 PM **剛把「判準比目標寬」那條登記進 `main` 之後**。**登記⛔ 不等於不再犯。**
