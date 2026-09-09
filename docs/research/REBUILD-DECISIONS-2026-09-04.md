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
- **回看（2026-09-09 登記）**：「同對象例外堆疊」這個訊號在規則側沒有任何鉤子了。框架為自己設的三個機械訊號（`core/naming.md` §5 行數上限、2026-09-05 分號裁定、`reachability` job）在「例外堆疊」這個方向上全是關的——例外是接在既有行尾的分號子句，行數抓不到、分號裁定明文允許「條件、例外、指向子句」、reachability 不讀 §2 條文一個字。判準已按 Gemini 複審只留受害點，故此訊號目前只靠 PM 人工數。第一次撞到「規則沒壞但例外多到讀不懂」時再議。
- **不一致（2026-09-09 登記）**：`core/glossary.md`「狀態面」逐字不含留言，`core/verbs.md` §2「（卡面 JSON 與留言）」是孤例；`cli/tests/test_snapshot_verb.py` 的 `assert_read_only()` 其 `WRITES` 漏列 `post_comment`。
- 缺 `--ruling` 的印：`core/verbs.md` move 印格所列各案在 CLI；第六案 結案/待確認→結案/退回 走清單（`stages/closeout.md` §4）；是否全收斂一併議。
## 待骨架文件決定（本紀錄⛔ 不裁）

模組管理形狀（每模組宣告：加的欄位／加的階段或狀態 delta／加的動詞或旗標／加的注意事項／啟用條件；專案層一份 modules 清單）、缺陷路徑位置、Log 居所、新 CLI 測試策略、這輪重構的停損條件、卡面 JSON 欄位集。

## 事實（2026-09-04 量到的）

- Project #4「cpbl-analytics 任務看板」217 張、29 欄；`交付狀態` 仍 15 值；`階段` 欄 217 張全空。
- 快照 2026-09-03 10:41：🏁完成 128／🛑已停止 34／💡需求 30／⏸阻塞 17／📦已合併 4／📥Backlog 3／↩退回 1。非終態 55 張＝cpbl 38＋aiwf 17。
- `gh project item-list` 的自訂欄位在本機回傳全空，可靠來源是 `origin/snapshots`。
