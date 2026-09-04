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

