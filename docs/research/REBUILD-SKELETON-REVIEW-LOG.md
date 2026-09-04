# 骨架審核修改紀錄（自 REBUILD-SKELETON 拆出，2026-09-04）

乙案（需求方 2026-09-04）：硬擋收縮為 11 條，H5 H6 H13 K10 與 KR 的作者比對降為印；CLI 只讀三種留言區塊；本紀錄自骨架拆出。

## PM 自審（需求方 2026-09-04 指示：先自審幾輪、⛔ 不再擴 CLI）

用「印清單／確認有沒有填／GitHub 機械操作／資料有效性」四類過每個 CLI 表面：砍 `roles`、`counters`、`modules`、`origin`、`brief.non_scope`（欄 28→23）；砍 `--family`；砍 `.wf/actors.json`（KR 作者只印 login）；`move` 的印縮到四項，merge SHA 與 CI 狀態歸 `brief --for closeout`；`review` 不再自動產生 `wf-note`；`snapshot` 不讀規則檔，過期改由 `brief` 來源標記帶日期；H5 H6 從印再降為 PM 注意事項；第 3 次退回的預設處置改為 PM 條文，核心 CLI 不數。

## PM 自審第二輪（需求方：「寧願把資訊交給 AI 判斷，比硬寫 CLI 高效且有品質，前提是資訊要足」）

H8（進終態前 PR 與分支狀態）與 H9 的鏈深上限降為印；硬擋 11→9，判準收成一句「CLI 拒的只有寫壞資料與指向不存在的東西」。資訊面補：派審詞印本 iteration 執行者 actor，PM 判 H5 H6 有料。

## PM 自審第三輪（資訊要足）

逐角色核對 `brief` 給的資訊：執行者（規格、驗收、非射程、注意事項、前輪 findings、副作用入口）、查核者（merge-base、source_sha 與 HEAD 比對、前輪 findings、本 iteration 執行者 actor）、結案（merge SHA、CI、findings 狀態）、需求方裁定單（事件序改由 `wf-return` 時間序推，CLI 不讀散文留言）。§四結案列與 §八裁定單同步 H8 降印的字。

## Gemini 第四輪（被審 e3914d7，留言 5537422935）

- R1-01：§七 `edit` 硬擋殘留「鏈深 >2」（第二輪自審替換字串沒對上），改為只印。
- R1-02：§六 `notes` 欄註記「任務層注意事項」改「卡面 notes 欄，T- 加嚴層級」。

## 第二十輪（被審 babfec2，R1 過）

- R2-01：三目標句移出骨架 §三，寫入決策紀錄第零條（標需求方確認）。
- R2-02：§十一 三列（研究討論出口、查核者資訊邊界、常態 merge）只留落點與來源。

## PM 自審第四輪（需求方：自審到沒有疑慮再送審）

整篇重讀：H11 列與 §七 brief 的硬擋矛盾（比對改印）、§六 source_sha「須等於」改「比對並印」、§十 一句祈使句改落點句、§十四 AC1 量詞與 AC3 終態集合、§二 殘字 `common.md`、§三 判準句與 §六 讀取範圍句改陳述。機械檢查：量詞 0、file:line 0、殘字 0、節次齊全。第二批零實質，停止自審。

## PM 自審第五輪（換角度、查離題）

需求方負擔：出場點 10 個，比舊制多 3（正式化確認、規則檔過期、零拒收回看）→ 合成一次定期回看，共用 `guard_review_period`。執行者負擔：交回單段落必填性依級別分兩檔；`brief` 印預填樣板。PM 每卡 CLI 呼叫約 8–10 次，與舊制相近，減的是旗標、拒絕迴圈、手抄信封（記進未驗）。離題檢查：每節可對回決策、萃取或需求方指示，無多餘機制。

## 回顧：24 輪 41 條 finding 的歸因（需求方 2026-09-04 要求）

| 根因 | 條數 | 例 | 成因 |
|---|---|---|---|
| 兩居所不同步 | 11 | 硬擋計數多版並存、「十一個模組」、三層／四層、edit 殘留鏈深、K10／KR 未入 §三表、H3 與 §一 互打 | 字串替換改一處未重讀整篇；手寫總數 |
| 形狀與規則正文界線 | 12 | 「逐張遷」「守衛預設不做」「一則留言收口」「PM 直行」 | 寫「規則是什麼」而非「住哪、來源」；未用 AC4 自掃 |
| 在骨架裡重判決策 | 6 | C10 計數、「層」架構用法、不可判定、resource-lock 第二條件、三目標句 | 未先回決策紀錄改字 |
| 漏掉決策項 | 6 | 未驗清單、三值居所、notes 欄、review 動詞、每段標來源、「同輪」寫窄 | 送審前無「決策→節次」對照表 |
| 第零條未貫徹到資料來源 | 4 | tier_basis 自由文字、留言首行、--ruling 缺席硬擋、roles／actors | 加檢查前未問「讀哪個結構化欄位」 |
| 狀態機萬用字 | 2 | 任一狀態→阻塞、撤銷無回板 | 「任一」未逐狀態枚舉 |

結構性原因三個：送審前無對照表（涵蓋 25 條）；有序閘門一輪只抓一題（20 輪中 13 輪停在 R1）；改法是替換不是重讀（11 條）。
填規則各檔送審前固定三步：決策→節次對照表、整篇重讀、AC4 祈使句掃描——皆為印資訊給自己看，⛔ 不新增機制。

## 硬擋逐條重判表（自骨架 §三搬出，最終狀態＝cab1820）

| 舊編號 | 一句 | 重判 | 落點 |
|---|---|---|---|
| H1 | main ruleset 禁改史禁刪 | 平台委託 | ruleset |
| H2＋H15 | T2 以上走分支＋獨立查核；執行者不 merge | 平台委託 | ruleset required check＋PR |
| H3 | 合併方式由專案層 `merge_method` 決定並以平台設定強制（squash ⇒ ruleset `required_linear_history`＋關閉 merge／rebase；merge ⇒ 關閉 squash／rebase） | 平台委託（值歸專案層，C3） | repo 設定＋ruleset；aiwf 的 `.wf/modules.json` 選 squash |
| H4 | secrets 不進 git | 平台委託 | CI secret scanner（需求方裁定必備） |
| H12 | commit trailer 鍵與連續區塊 | 平台委託 | CI |
| H5 | 同卡同 iteration 一人一角 | **注意事項**（乙案；自審收縮） | `roles/pm.md` F-pm；CLI 無資料來源，不印 |
| H6 | T4 查核者家族≠執行者家族，或 sign-off 留言存在 | **注意事項**（乙案；自審收縮） | `roles/pm.md` F-pm＋`roles/requester.md`；CLI 不印 |
| H7 | 轉移在合成表內；終態無出邊；無自由文字狀態 | 資料有效性 | CLI `move` |
| H8 | 進終態前：以卡面 `branch` 查 GitHub（PR merged、分支存在）；封存本身可逆 | **印**（自審第二輪：資訊給 AI 判） | `move` 到終態時印 PR 與分支狀態，PM 判 |
| H9 | `open` 只從清單 issue；不在板上（建不出第二張） | 資料有效性 | CLI `open`；鏈深 >2 改為印（「鏈深 N，上限 2」），整鏈重審由 PM／需求方判 |
| H10 | JSON 合法、鍵集合封閉、解析失敗整卡拒、寫後回讀 | 資料有效性＋寫入順序 | CLI 全動詞 |
| H11＋K5 | 交回時 `--source-sha` 40 碼且在遠端存在（硬擋）；審核期間分支 HEAD 與卡面 `source_sha`、交回單 `source_sha` 與卡面值的比對（印，PM 判；K5） | 資料有效性（存在）＋印（比對） | CLI `move`（寫、存在檢查）、`brief --for reviewer`／`review`（比對並印） |
| K10 | 派審前分支與 main 的 `merge-tree` 有衝突 | **印**（乙案） | `brief --for reviewer` 印，PM 判 |
| KR（C12–C14） | 已給的 `--ruling` URL 存在且含 `wf-return` 或 `wf-ruling` 區塊 | 資料有效性（存在） | CLI `move`／`edit`；留言作者 login 只印出，是否是對的人由 PM 判（無名單檔） |
| H13 | 交回單欄位一致性（C2 三含意：RC 須 blocking 或 core_pain no；APPROVE 不得帶 blocking／core_pain no） | **印**（乙案） | `review` 印不一致警示，PM 判 |
| H14 | 查核唯讀、不代改 | **紀律** | `roles/reviewer.md`；分支變動由 H11 抓 |
| H16 | 事件只寫該卡 Issue | **語意** | `core/verbs.md` |
| H17 | 狀態面不可用時暫停 | **紀律** | `roles/conduct-common.md` |
| H18 | 結案四停下條件 | **降為印** | PM 判 |
| H19 | 禁 `gh pr update-branch` | **砍** | C3 |
| K4 | 守衛必須進 CI | **紀律** | `roles/conduct-common.md`：若有守衛則進 CI，⛔ 不是要有守衛 |

## 第二十四輪（被審 d1b2d31，留言 5540476391）

- R1-01：刪 §七 `brief --for reviewer` 印本 iteration 執行者 actor 的要求；一人一角與跨家族只留 PM 注意事項（§三已如此）。PM 要判時讀卡面 `owner` 與轉移記錄留言，兩者本來就有。

## 第二十三輪（被審 42211db，留言 5540360158）

- R4-01：第 0 步 CI 只留 secret scanner（P4）與 trailer 檢查（P5）；轉移表可達性 job 隨第 1 步 `core/state-machine.md` 同 PR、新 CLI 測試 job 隨第 6 步同 PR；⛔ 不預先加空 job（§十三）。順帶把 P5 的 CI job 補進形狀，先前三個 job 漏了它。
- R4-02：§十八補 6 列（狀態面、階段計畫、終態、父卡＋鏈深、資源宣告、owner）並寫約束邊界（schema 鍵名與平台詞不入表）。查核者列的「規格版本」「清單收斂」骨架未逐字使用（分別是 `spec_version` 鍵名與 `open` 動作），不另加列。

## 第二十二輪（被審 b1bd0a4，留言 5540084169）

- R3-01：砍 `source_sha_iteration`；`source_sha` 定為 string，恆屬當前 `iteration`：`move` 進執行時 iteration +1 並清為 null，交回時寫（§四、§六、§七）。少一個鍵而不是多一個。
- R3-02：`card_id`／`source_issue` 不可改列入 D3；`parent` 指到存在的卡列入 D4，`open` 納入 D4 動詞；§七 `open`／`edit` 改引 D2、D3、D4（§三、§七）。

## 第二十一輪（被審 2fcd298）

- R1-01：代貼標記回首行、限裁定；代貼裁決是否沿用列 §十五 待裁。
- R1-02：D4 只驗 URL 存在；缺區塊降印（§三、§七）。
- R1-03：schema 唯一居所＝`core/` 的 fenced 區塊，CLI 執行期直讀，砍 `schema/` 目錄（§十三）。

## 逐輪處置

第一輪（留言 5535340214）：
- R1-01：`停止` 移出核心值域，改為結案階段 delta（§四）。
- R1-02：`--ruling` 缺席一律印；只有已給但不存在或作者不符的 URL 才拒（§三、§四、§五、§七、§十一）。

第二輪（被審 d6a8caf）：
- R1-01：C10 計數被第零條取代一事補進決策紀錄「補充裁定」，骨架 §三改為引用它，不再自行重判。
- R1-02：H13 恢復為資料有效性硬擋，含 C2 三含意（§三）。先前降為印是把 JSON 欄位間一致性誤判成內容判讀。
- R1-03：注意事項回應三值的唯一居所定在 `core/handoff.md`，交回單 schema 引用（§八、§十二）。

需求方提議後補：§十八 `core/glossary.md` 通用語言，列為填規則第 1 步第一檔（fe71a05 後）。

PM 自審（4030fa3 後）：`wf:note` 與所有 CLI 寫的留言都帶 `json wf-<種類>` 區塊；`notes`／`snapshot` 只讀區塊；§六列出全部區塊標籤。

第十九輪（被審 9663880）：
- R1-01：留言種類改由 fenced 區塊標籤與欄位（`wf-return`.role／`wf-ruling`.kind）判定，首行 `wf:*` 只給人讀；§三、§四、§七、§十同步。

第十八輪（被審 42ca665）：
- R1-01：KR 分流——`wf:verdict` 對 reviewers 或該 iteration 的 reviewer.actor，`wf:ruling` 對 requesters；§三、§四、§七同步。

第十七輪（被審 cdf2ac5，R1 R2 過）：
- R3-01：§四加「清單（撤銷過的卡）→ 需求／待辦」邊，由 `open` 復板沿用 card_id／iteration。
- R3-02：`brief` 的 H11／K10 硬擋限定 `--for reviewer`；executor／closeout 無硬擋。
- R3-03：§三加 KR 列（`--ruling` 存在與作者比對），硬擋 15／CLI 10。

第十六輪（被審 1231d7b）：
- R1-02：`source_sha` 從 `edit` 例外移除（C11 只有兩個例外）；不可變改由審核期留言與 `brief` 重比守。
- R1-01：需求方裁乙案——「層」只禁用於清單輸出與來源計數，架構詞「專案層」照用；決策紀錄該句同日修訂。定義層／CLI 層／卡層／機械層四處順手改字。

PM 自審（b3ca6d6 後）：H8 的事實來源明寫為卡面 `branch`＋GitHub API（PR by head ref、merged、merge commit、分支存在），不另設 PR 欄。

第十五輪（被審 82727da，R1 R2 過）：
- R3-01：卡面加 `source_sha`（交回時由 `move --source-sha` 寫，同 iteration 不可變，`edit` 不可改）；H11＋K5 改為對此值比對。
- R3-02：專案層 `.wf/actors.json`（requesters、reviewers）成為裁定與 sign-off 的預期作者來源；`--ruling` 作者比對讀它。

第十四輪（被審 0d228f3，R1 R2 過）：
- R3-01：卡面加 `roles` append-only 陣列（iteration／role／actor／family／since），owner 為其投影；`move` 收 `--actor --family`；H5 H6 改讀 `roles`。
- R3-02：`open --parent` 成為結構化輸入，鏈深在首次寫入前驗；`edit --set parent=` 重驗。

PM 自審（f3140f3 後）：owner 補 `family` 封閉值域（H5、H6 的比對欄）；`move` 的「TODO」佔位符檢查改為存在性檢查。

第十三輪（被審 3ed83dc）：
- R1-01：`tier_basis` 三欄改封閉值域（sensitive 多選、recoverable、blast 各 enum）；stat-redline 條件改集合成員比對，CLI 不讀內容。

第十二輪（被審 17fd49c）：
- R1-01：§四「任一狀態 → 阻塞」改為任一非終態；可達性測試加「終態出邊為空」斷言。
- PM 自審：「任一階段」四列排除結案；補「結案／退回 → 結案／待確認」邊，使結案／退回有出邊。

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

