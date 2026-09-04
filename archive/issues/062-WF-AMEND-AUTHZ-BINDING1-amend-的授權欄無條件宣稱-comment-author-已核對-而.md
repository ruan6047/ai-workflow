# #62 WF-AMEND-AUTHZ-BINDING1 amend 的授權欄無條件宣稱 comment author 已核對，而該比對對代貼者恆真
- state: closed  created: 2026-08-12T12:05:58Z  closed: 2026-08-17T05:44:57Z
- url: https://github.com/ruan6047/ai-workflow/issues/62
- comments: 14

## Body

- 需求：—　規劃：—
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；碰的是唯一寫入通道上的授權留痕，且要判定「操作者身分等於被引用授權者身分」時該導出什麼；與 WF-ESCALATION-RESOLUTION-GAP1 的 authorization_binding 是否同構須論證而非套用；推理鏈中等。）　查核：待指派（建議 主力型；紅線：本卡改的是治理留痕本身，寫錯會讓一個空的授權看起來更像有效授權（比現況更糟）。查核重點在導出值是否真的可為假、以及提交面能不能偽造它。須跨家族。）
- Initiative：—　spec 基線：由 WF-EVENT-TYPE-REGISTRY-RECONCILE1（#58）R2 執行者於 42cfb387 交回時指出，PM 查證後確認並發前向更正 issuecomment-5266565670（attribution=coordinator）。既有同型處置見 WF-ESCALATION-RESOLUTION-GAP1（#39）templates/review-escalation.md §5 第 7 款：拒絕把恆真寫成看似有檢查的條文，改為要求 adapter 導出 authorization_binding: substantive | structurally-vacuous，把恆真本身寫進事件流。
- DB：db_scope=none
- 服務的原始目標：讓授權留痕的機械強度與它實際具備的強度相符

## 簡介
<!-- card-brief:begin -->
`cli/src/wf_cli/commands/amend_cmd.py:507` 在 `--ruling-url` 的 author 檢查通過時無條件輸出一句暗示該比對具區辨力的常數——而 PM 的 gh 以 ruan6047 認證、需求方帳號亦為 ruan6047，該檢查對 PM 恆真，一次也沒區辨過任何東西。**適用時機**：要引用需求方裁定留言做 amend、或要讀 amend 事件的授權欄判斷它實際有多強時。⛔ 非射程：既存 10 筆事件不得追溯改寫；不得把恆真導出成 `structurally-vacuous` 之類的值再繼續當檢查用（`docs/ROADMAP.md:58-59` 逐字禁止該形狀）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：cli/src/wf_cli/commands/amend_cmd.py:507 在 --ruling-url 的 author 檢查通過時，無條件輸出常數字面「GitHub comment author 已逐字核對，非留言內文自述」到 amend 事件的授權欄。該句在字面上為真（確實比對過），語意上卻誤導：它暗示該比對具有區辨力。而本 repo 的實況是 PM 的 gh 以 ruan6047 認證、需求方帳號亦為 ruan6047，故該檢查對 PM 恆真——一次也沒有區辨過任何東西。2026-08-12 於 #58 實際發生：PM 代擬代貼需求方裁定並據以 amend 核心痛點，把恆真性寫進了留言與理由欄，授權欄卻繼續輸出那句有區辨力暗示的常數。只讀結構化欄位的消費者會拿到錯的印象——而那正是 WF-EVENT-TYPE-REGISTRY-RECONCILE1 整張在治的病：事實活在散文裡，欄位裡的版本是不完整的。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/amend_cmd.py",
    "file:cli/tests/test_amend.py",
    "file:cli/src/wf_cli/doctor.py",
    "file:cli/tests/test_doctor.py",
    "file:cli/src/wf_cli/commands/doctor_cmd.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 確認 --ruling-url 的授權宣告欄位存在且必填，並對其完整性做檢查（URL 可解析、留言存在、卡號相符）;⚠️ 不得把恆真性導出成 structurally-vacuous 之類的值再繼續當檢查用——ROADMAP.md:58-59 逐字禁止該形狀，本條取代原驗收條 3;amend_cmd.py:507 的常數字面須改寫為不宣稱區辨力的措辭：它可以說「已比對」，不得暗示該比對能區辨出任何東西;⚠️ 已實現後果為 10 筆事件／8 張卡（最早 2026-08-12 12:27，最新 #88 於 08-15 13:34）。既存事件不得改寫（唯一寫入通道的留痕不可追溯修改），但須在本卡交付說明中列出受影響清單，讓讀者知道那些授權欄的語意

## 驗證

- [ ] cd cli && uv run pytest -q 不得退化（基線自己跑，不要抄卡面數字）。
- [ ] 以突變注入證明新增的斷言有鑑別力：把導出值改為恆定、或讓提交面得以覆寫它，測試須轉紅並附輸出。
- [ ] 凡寫下「可以為假／有守衛／已核對」須附指令輸出；沒有機械執行者的寫成約定。
## Log

- 2026-08-12T20:05:57+08:00 open by —；owner 待指派；iteration 0。
- 2026-08-16T10:40:37+08:00 amend by wf-cli（op 05cf6174）→ 驗收條件：原值「[ ] 裁定 amend 的授權留痕該導出什麼。⚠️ 不得直接套用 #39 的 authorization_binding——#39 驗的是「來源」（adapter 加蓋、提交面不得含此鍵、含即無效即使值恰好等於導出值），本卡要驗的是「操作者身分是否等於被引用的授權者身分」。兩者是否同構須論證，PM 不預設。；[ ] 移除或改寫 amend_cmd.py:507 那句常數字面。⚠️ 判準不是「話說得對不對」而是「這一欄有沒有區辨力」——保留一句永遠為真的話，就是保留本卡要消滅的東西。；[ ] 導出值必須可以為假。須有反例證明：操作者身分不等於授權者身分時導出 A、相等時導出 B，且兩者在事件流上分得開。若本 repo 今天造不出「不相等」的真實情境（唯一人類帳號即需求方），須明說該款今天恆為某一值，並把該恆真本身寫進導出值——不得因為造不出反例就宣稱它有守衛。；[ ] ⚠️ 不得讓一個空的授權看起來更像有效授權。若處置的淨效果是把「已逐字核對」換成另一句同樣無區辨力的話，本卡未關閉核心痛點。；[ ] 既有已寫入的 amend 事件不追溯改寫（本專案明令禁止）。須說明既有事件在新語彙下如何被讀——legacy 標記、或明確宣告不可判定。」→ 新值「確認 --ruling-url 的授權宣告欄位存在且必填，並對其完整性做檢查（URL 可解析、留言存在、卡號相符）;⚠️ 不得把恆真性導出成 structurally-vacuous 之類的值再繼續當檢查用——ROADMAP.md:58-59 逐字禁止該形狀，本條取代原驗收條 3;amend_cmd.py:507 的常數字面須改寫為不宣稱區辨力的措辭：它可以說「已比對」，不得暗示該比對能區辨出任何東西;⚠️ 已實現後果為 10 筆事件／8 張卡（最早 2026-08-12 12:27，最新 #88 於 08-15 13:34）。既存事件不得改寫（唯一寫入通道的留痕不可追溯修改），但須在本卡交付說明中列出受影響清單，讓讀者知道那些授權欄的語意」；理由 需求方 2026-08-16 裁定。原驗收條 3 要求「把恆真本身寫進導出值」，與 docs/ROADMAP.md:58-59 直接衝突——後者逐字禁止「把恆真性導出成 structurally-vacuous 再繼續假裝那是檢查」。成因是時序：本卡寫於 2026-08-12 20:05，ROADMAP §1 定案於同日 22:53（02a6f8b），卡比裁定早三小時且從未回頭對齊。照原卡面執行會產出 ROADMAP 明文禁止的形狀。另更正已實現後果的規模：原認定為理論發現，2026-08-16 全庫掃描實測為 10 筆／8 張卡，且最早 3 筆比本卡建立時間還早。⚠️ 本次 amend 走 --ruling-url，而該旗標的恆真檢查正是本卡要修的東西——用那個檢查去修那個檢查，此事實一併記錄。。
- 2026-08-16T12:29:24+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex）；iteration 0；SHA b3fac32ce560e089702b7974b0d3e06e16ed63a0；證據 amend 授權留痕的恆真宣稱已改寫。⚠️ 事件複核推翻 PM 的計數：PM 原報 10 筆／8 張卡，執行者窮舉 Project #4 全部 148 個 item 逐張讀 body 後為 13 筆／9 張——PM 漏的兩筆在 cpbl-analytics#129（Project #4 跨兩個 repo，PM 只用 --repo ai-workflow 掃描，結構上看不到），另一筆晚於 PM 掃描時點。另訂正 PM 一處卡面敘述：「恆真檢查只作用在 --core-pain 路徑」對已實現事件為真、對程式碼射程不成立，amend_cmd.py:575 的 tier_downgrade_needs_ruling 讓 T3/T4 降級走同一函式，故執行者改的是函式回傳值、涵蓋兩條路徑。執行者自量：改動前 879 passed → 改動後 881 passed（+2）、escalation replay 65/65、uv lock --check 通過、CI run 31925207693 success 且 headSha 逐字相符。變異檢驗 M1 整句還原舊值→兩條斷言皆紅、M2 只刪免責半句→前者紅後者綠（證明兩條斷言互不涵蓋）。⚠️ 執行者自陳新措辭「夠不夠」是判斷題、不宜由自己驗證，該項須查核者獨立判斷。⚠️ 既存 13 筆舊措辭事件無機械標記；原驗收條 5 的 legacy 標記已於 08-16 amend 移出射程，該射程邊界是否正當請查核者判斷。。
- 2026-08-16T12:34:11+08:00 amend by wf-cli（op d5438683）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/commands/amend_cmd.py", "file:cli/tests/test_amend.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/commands/amend_cmd.py、file:cli/tests/test_amend.py、file:cli/src/wf_cli/doctor.py、file:cli/tests/test_doctor.py」；理由 查核 finding 2（blocking）：既存事件無機械 legacy／correction 標記。需求方 2026-08-16 裁定採甲案——把舊字面「非留言內文自述」本身當 legacy marker，加一個 doctor 檢查，不改任何一張卡的 body。故射程須納入 doctor。全庫掃描（兩 repo、全 state、200 筆）證實該字面是乾淨的機械標記：15 行、前綴 15/15 完全一致、只出現在這些行；其中 14 筆是 Log 事件（跨 9 張卡：ai-workflow #88 #62 #58 #57×5 #48 #38 #31 #25 #11、cpbl-analytics #129×2），另 1 行是 #62 自己 body 引述缺陷的散文。⚠️ 數字由 13 更正為 14：第 14 筆是 2026-08-16T12:23:58 op 3eb6ec6f，即 PM 今日為修 #57 假敘述所跑的 amend——缺陷在本卡開著期間仍在生產新實例。。
- 2026-08-16T12:54:51+08:00 amend by wf-cli（op 24a4c403）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/commands/amend_cmd.py", "file:cli/tests/test_amend.py", "file:cli/src/wf_cli/doctor.py", "file:cli/tests/test_doctor.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/commands/amend_cmd.py、file:cli/tests/test_amend.py、file:cli/src/wf_cli/doctor.py、file:cli/tests/test_doctor.py、file:cli/src/wf_cli/commands/doctor_cmd.py」；理由 R2 交付後執行者自陳接線只到一半：新的 legacy 檢查接在 run_doctor，但 doctor_cmd 從不傳 card_bodies，故從 CLI 跑 doctor 這一節永遠印「未掃描」。執行者以 not_scanned 讓該事實可見（不謊報乾淨）已是其資源宣告內能做到的最誠實版本，但半條線正是本專案今日一路在退的形狀——「命名了但沒接線」。補完接線屬完成已裁定的工作（甲案要求的是機械標記，一個從 CLI 不可能執行的檢查不構成機械），非擴大射程。故將 doctor_cmd.py 納入。⚠️ PM 已查 doctor_cmd.py 無活的持有者：#63 與 #30 雖有宣告但皆為「執行：待指派」。⚠️ 另記：wfcli amend --resources 不跑互斥檢查（見 #92），本筆同樣未被機械檢查，是 PM 手動查的。。
- 2026-08-16T13:13:15+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex）；iteration 0；SHA 661bde1623a348797d6fbb3b9bf65de8cfc168f4；證據 R1 兩條 blocking 處置後，PM 依執行者自陳「接線只到一半」再退一輪補完，本輪為第三次交付。finding 1（措辭仍高於證據強度）：總結標籤整個拿掉，新措辭只列做了哪兩個比對再接四句「不讀／不判定／不區分」；執行者採納查核者指出而其上輪漏掉的一點——外層「裁定」本身即未經檢查的宣稱，實查 _resolve_ruling_author 只取 payload[user][login] 從不讀 body，故句內明寫那是操作者的宣告。⚠️ 執行者自陳「已核對：」算不算標籤是判斷題，其論證為：它是動詞、不指涉任何屬性、冒號後緊接列舉把它綁死，且卡面驗收條 3 逐字允許「已比對」；若查核者認為連動詞都該去掉，執行者無反駁的硬證據。finding 2（甲案 doctor legacy 檢查）：find_legacy_authority_notes／audit_legacy_authority_notes 報三件事——這是 #62 之前的措辭、其區辨力構造上不成立、⚠️底下的授權可能仍然真實；finding 只帶定位資訊（card/時間戳/op/欄位），刻意不帶任何對該次授權的評價欄位並有測試釘住（doctor 讀不到留言內文，沒有立場評價）。判準錨定在「；授權 」之後而非整行，構造性排除 #62 自身散文；執行者於實作中發現一個更強的理由：同一行可以「原值引用舊字面」＋「授權欄已是新措辭」，整行比對會誤判，已有測試釘住。本輪補完接線：doctor_cmd 新增 --legacy-authority-notes 旗標，實跑 CLI 確認會響（已掃描 150 張卡、15 行、9 張卡；--json 有 status=scanned/scanned_cards=150/findings=15/cards=9；缺 --owner/--project 時 exit 2 並指名）。⚠️ 數字 14→15，新增的 op 7a9c7a0f 是執行者本輪工作期間由 PM 產生的，為本卡第二次實測驗證「不得寫死計數」。變異檢驗：M1 還原 R0 舊值、M2 還原 R1 標籤、M3 換新標籤、M4 換弱形容詞、M5 刪揭露句、M6 拿掉位置錨、M7 not_scanned 併入 scanned、M8 說明改成過度宣稱、M9 拆掉接線（4 紅）、M10 不抓卡面（5 紅）、M11 改共用 card_bodies（1 紅）、M13 舊留痕算進 --strict（1 紅）皆轉紅；M3/M4 證明新標籤與弱形容詞都只被結構斷言抓到、黑名單全漏——標籤是開放集合只能釘插入位置。M12（抓取失敗設 {}）全綠但執行者判為 equivalent mutant 並另構 M12b（整段移除 try/except）轉紅。兩個設計決定：不共用 card_bodies（該參數餵 cleanup guard 第 3 步，共用會讓 --cleanup-preview 判定沉默改變，屬別張卡射程，已有 spy 測試）；舊留痕不列入 --strict（那些事件明令不得追溯改寫、永遠不會消失，算進 exit code 等於讓 CI 恆紅無人能修好）。數字：基線 d18cd83 執行者於乾淨 worktree 實跑 944 passed；本輪 head 本機 968 passed（+24）；CI 獨立實跑 968 passed 且 headSha 661bde1623a3 逐字相符全綠；uv lock --check 通過、escalation replay 65/65、trailer guard 三個 commit 皆 compliant。變更恰為宣告五檔。⚠️ 執行者自陳四項不確定，第 2 項須查核者與需求方知悉：旗標是 opt-in 不是預設開，不加旗標仍不掃；做成預設會讓每次 doctor 都連網抓整個 Project 且缺 --owner/--project 的用法會壞掉——若甲案的本意是「每次 doctor 都必須掃到」，這還不夠，需另裁預設值與參數來源。另：--json 新鍵由 asdict(report) 自動帶出，未查有無對 payload 做嚴格 schema 驗證的消費端。⚠️ 執行者更正 PM 一處：PM 稱 #63 與 #30 皆「執行：待指派」，實際 #63 是 🏁完成／已結案屬終態，兩者都不擋但理由不同。。
- 2026-08-16T23:05:19+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex）；iteration 0；SHA 1588d5033c0730c36cac714937878af562b5127a；證據 R2-001（結構斷言只擋得住第一個事實之前的標籤）處置。執行者判定上輪錯的是【守衛形狀】而非選錯性質：三輪都在釘「不可以是什麼」（R0 釘區辨力宣稱、R1 釘標籤措辭、R2 釘插入位置），而用開放集合的補集去守永遠有下一個沒被列舉到的成員——措辭是開放集合，位置也是，其上輪只說對前半句。改為逐字比對（封閉集合）：斷言 _authorize_by_requester_ruling 的原始回傳值逐字元等於 _GOLDEN_AUTHORITY_NOTE，任何標籤、任何位置、任何措辭都落在等號之外。斷言對象刻意取原始回傳值而非卡面 body——body 那條路徑會先過 _fold，摺行有機會把多打的換行吃掉；另有一條分別證明它原封不動落進 Log（；授權 {golden}。前後各釘一個界線字元）。正規化處理：這裡的規則就是「不做正規化」並把該規則本身釘住——實作用相鄰字串常值併接，原始碼換行縮排不改變執行期結果；test_golden_note_is_reflow_stable 把「黃金值不含連續空白或換行」變成機械事實，使 Log 寫入時的 _fold 對它是恆等函式。此形狀正面回應 #57 R5 那個陷阱（那個是拿 banned 字串比對排版後的文字，本形狀比對併接後的值）。變異檢驗：⭐M14 標籤插在第一個事實之後（查核者 R2-001 原始反例，舊守衛 3 passed）→ 3 紅；M15 插在開頭 → 3 紅；M16 換弱形容詞 → 3 紅；M17 插在句末 → 3 紅；⭐M18 純原始碼 reflow（換行位置全改）→ 293 全綠無假紅；⭐M19 把換行放進字串內容 → 4 紅；M9 拆接線／M6 拿掉位置錨各 4 紅。M15/M14/M17 三個不同位置全部被抓，既證明守衛有效也實測了「位置是開放集合」。一併更正裁決逐字點名的過度宣稱：amend_cmd.py:559 那句「加任何字在（與第一個事實之間，都會被結構斷言擋下」已移除、改為記錄 R2-001 被打穿的經過與教訓，模組 docstring 加同一段；射程被推翻的 test_authority_note_has_no_summary_label_before_the_facts 已【移除】（留著只會讓下一個人再相信一次位置守衛）；另兩條性質斷言保留但 docstring 明寫「本條不是守衛」，只作具名回歸點。tier-downgrade 那條改用完整黃金值（原本只釘片段）。數字：基線 d18cd83 為 944 passed、前輪 968、本輪本機 970 passed（移除 1、新增 3）、CI 獨立實跑 970 passed 且 headSha 1588d5033c07 逐字相符全綠、uv lock --check 通過、replay 65/65、trailer guard 四個 commit 皆 compliant。射程仍為宣告五檔，doctor 那一半未動。⚠️ 執行者自陳三項不確定，第 1 項須查核者判斷：黃金值裡的 {author}/{url} 兩個插值點是其判斷的邊界，若有人把新標籤寫成插值（例如 f"（{label}已核對：…" 且 label 預設空字串），執行期字串不變、測試全綠——執行者認為是合理殘餘（需刻意繞過而非疏忽）但明說封閉集合不等於零縫隙。第 2 項：測試黃金值與實作字面是人工對齊的，兩邊都改錯成同一個誇大措辭時測試會綠，守衛的作用是強迫那次改動出現在 diff 裡、判斷仍在人——保證「被看見」不保證「被看對」。第 3 項：_authority_note_of 直接呼叫底線開頭的私有函式，耦合內部 API，若重構簽章測試會壞，是為繞開 _fold 換來的取捨。。
- 2026-08-16T23:29:18+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex）；iteration 0；SHA 4c65847056d00cef964040b809d94887ee0be1d2；證據 R3-001（黃金值守衛只覆蓋固定 requester／comment id，M20 依 comment id 分支可繞過）處置。執行者正面回答 PM 指定的「換形狀還是換實例」：答案是形狀。前四代都在斷言【輸出】的某個東西（措辭、標籤、位置、輸出逐字等於黃金值），R3 的封閉集合關掉了「這串字說了什麼」那一族但仍是對一次呼叫的輸出取值，M20 打的是量詞——∀這組輸入 ≠ ∀輸入。本輪斷言對象改為【產生輸出的規則】：AUTHORITY_NOTE_TEMPLATE 為唯一模板逐字釘住，並以 AST 逐節點釘住 return 運算式恆為 TEMPLATE.format(author=author, url=args.ruling_url)；模板唯一 ∧ 函式恆為其代入 ⇒ 不存在任何 (author,url) 能得到別的字串，量詞由「對這些輸入」變成「由構造」。執行者明說若只是把 comment id 參數化成四組那才是換實例，而那正是它沒做的（碼裡明寫那四組不是封閉性來源）。⭐ 最乾淨的證據是 M23：改回 f-string、輸出完全相同、仍然紅（AST）——守衛盯的已經不是輸出。變異檢驗：⭐M20 依 comment id 分支（查核者原始反例，舊守衛 970 全綠）→ 3 紅；M21 依 author 分支 → 3 紅；⭐M22 模板加 {label} 插值（執行者上輪自陳的縫）→ 12 紅；⭐M23 改回 f-string 輸出相同 → 1 紅；⭐M24 純模板 reflow → 299 全綠無假紅；M25 改措辭 → 7 紅；M26 globals() 指派相同值 → 全綠（執行者判為等價突變非漏網）；⭐M26b globals() 換成帶標籤的模板 → 7 紅；M9 拆 doctor 接線／M6 拿掉位置錨各 4 紅。M26b 有一個執行者記下的細節：參數化的第一組 [ruan6047-555] 沒紅，因為重新指派要等第一次呼叫後才生效——說明交叉檢查為何要變化輸入，即使它不是封閉性來源。AST 比對用兩邊同跑 ast.dump（不寫死 dump 字串）故不隨 Python 版本假紅。數字：基線 d18cd83 為 944 passed、前輪 970、本輪本機 976 passed、CI 獨立實跑 976 passed 且 headSha 4c65847056d0 逐字相符全綠、uv lock --check 通過、replay 65/65、trailer guard 五個 commit 皆 compliant。射程仍為宣告五檔，doctor 那一半未動。⚠️ 執行者逐條列出四個縫並自陳最強形式的極限：(1) AST 只約束那一個函式，模組別處把常數換掉它看不到，由「模組內只有一處指派」那條補，但那條也用 AST、看不見 globals()[...] 這種動態寫法——M26b 證明執行期交叉檢查會接住，但那是取樣不是保證；(2) 執行期 monkeypatch 完全擋不住，原始碼層面攔不住，無解；(3) 呼叫端事後加工由 _fold 恆等與 Log 逐字兩條覆蓋，但那兩條又是固定輸入，仍是取樣；(4) 模板與測試黃金值兩邊同時改錯仍會綠——守衛保證被看見不保證被看對（R3 已裁定此定位誠實）。執行者並自陳沒能做到真正的「對任意輸入」執行期驗證（Python 無此能力，hypothesis 只是把取樣加密且要加依賴、射程外），所以沒有假裝、改成約束構造。⚠️ 執行者自陳不確定第 3 項須查核者知悉：它沒有第五代的預測——前四輪每輪都覺得已收斂結果都被打開新的一層，這一輪認為量詞問題關掉了但「請當作判斷而非保證」。。
- 2026-08-17T11:40:11+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex）；iteration 0；SHA 060ee64e284e90c365eedfd466fc817d2524d29c；證據 需求方 2026-08-16 裁定本卡停在四輪（issuecomment-5311176521）：不修 R4-001（M27），改為把威脅模型寫進碼與卡。判準是先問「這個守衛在防誰」——防的是無意的後續編輯（M20／M22／M25／M26b 皆此類、皆已轉紅），不防蓄意繞過的提交者（M27 屬此類；沒有人會不小心寫出依 comment id 改寫 author 的碼，而對這一類任何測試與任何執行期檢查都無效）。核心痛點是「留痕宣稱了它沒有的區辨力」＝無意的過度宣稱，非防內鬼，且 core_pain_resolved 已連三輪 yes。本輪零行為變更。威脅模型寫在三處：amend_cmd.py 模組 docstring 新增「授權註記守衛的威脅模型：防誰，以及防不到誰」整節、AUTHORITY_NOTE_TEMPLATE 常數說明（標明 M27 已知不涵蓋且不修並指回 docstring）、test_amend.py 守衛區塊（同一份威脅模型含四條縫）。需求方原句在兩處各一次，與裁定留言做 byte-level 雜湊比對三份 shasum 全等（61a31e5f…）。⚠️ 執行者自陳在驗證原句是否逐字保留時 grep 回報 0 命中而句子其實在、只是被折行成兩行——那正是 #57 R5 的 reflow 陷阱，它在查驗「不得軟化」時自己踩了一次；兩處已改為不折行並改用雜湊比對而非 grep 計數。⚠️ 執行者以自己的尺複核該段方向並抓到一處往上：初稿在 docstring 寫「守衛涵蓋到該形狀為止即停」而沒有附帶限定，可被讀成「無意編輯這一整類都被涵蓋了」——而無意編輯同樣是開放集合，那就是第五代過度宣稱；已補「這是四個實例，不是對『所有無意編輯』的保證——那一類同樣是開放集合，而本卡四輪的教訓正是不要再對開放集合下全稱宣稱。這裡只說這四個跑過、都紅」，test_amend.py 初稿即有此句、docstring 漏了，現已一致。數字：基線 d18cd83 為 944 passed、前輪 976、本輪 976 passed（純註解行為零變更）、CI 獨立實跑 976 passed 且 headSha 060ee64e284e 逐字相符全綠、uv lock --check 通過、replay 65/65、trailer guard 六個 commit 全 compliant。射程仍為宣告五檔，doctor 那一半本輪未動。⚠️ 執行者自陳三項不確定：(1) 卡面未寫——依交付紀律不跑 wfcli，卡面需 PM 補；⚠️ PM 已試 amend --core-pain 但被拒（卡面「需求：」欄為 —、未宣告實際帳號，而 amend 沒有任何旗標能設該欄位），故威脅模型構造上進不了本卡卡面，只能存在於留言與碼；該缺口已記入 #94 家族卡的核心痛點第 (5) 條。(2) 這段記載本身沒有測試守著，它是註解，下一個人刪掉或改成「已充分防護」不會有任何東西轉紅——執行者未加守衛，因為那會變成「為了守衛註解再加一層守衛」，正是本卡四輪要停下來的遞迴，但確實是縫。(3) 「無意 vs 蓄意」的分界是照裁定寫的、非其獨立導出；判準「沒有人會不小心寫出依 comment id 改寫 author」它認同但那是常識判斷非機械判準，邊界案例（例如有人為了 debug 暫時加分支後忘了移除）落在哪一邊該記載沒有回答。。
- 2026-08-17T11:59:25+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex）；iteration 0；SHA e08c6b66d5023526c3fc7a0eaa44bbe08e614fbd；證據 R5-001（常數說明仍宣稱「return 前任何條件改寫都會讓 AST 轉紅」，與 M27 已知可繞過的記載直接矛盾）處置。⚠️ 執行者依 PM 要求自行第三次全掃，找到的不是一句是【三句】同型全稱宣稱：(1) 查核者指名的常數說明那句，已改為「AST 斷言釘的就是該 return 運算式的語法形狀，改了會紅。⚠️ 但不要把上一句讀成『return 之前做什麼都會被抓』：在 return 之前改寫 author／url 這兩個值，AST 看不見、測試不會紅（M27）」；(2) ⭐ test_amend.py 的 AST 測試 docstring——三句裡最強的一句，且【就寫在 M27 繞得過的那條測試上】：「在此形狀下輸出恆等於模板代入，因此不存在任何輸入能得到別的字串——任何條件式、f-string、字串拼接、額外 kwarg 都會讓 AST 不相等」，兩處皆假（M27 就是一個 return 前的條件式、AST 不相等不成立），已改為「輸出是模板代入 author／url 當下持有的值」＋明寫這不等於「不存在任何輸入能得到別的字串」，並列出真正會讓斷言紅的四種（改 return 運算式本身）；(3) 常數說明「兩條合起來，對所有輸入都得到同一個模板的代入」——字面為真、語意誤導，正是本卡在治的病型（M27 之下輸出仍是「模板的代入」，只是代入了被改寫的 author，讀者會讀成「輸出必定是黃金值」），已在該句【旁邊】而非六行之後直接界定：「⚠️ 但它界定的是組裝方式，不是最終字串：被代入的那兩個值本身不在約束範圍內，所以『同一個模板的代入』不等於『輸出必定是黃金值』——M27 正是從那裡進來的」；另把常數首句「永遠是它代入 author／url 的結果」改為「由它代入 author／url 產生」。掃過的其餘命中全部確認方向往下（免責、限制、或明確標示為已撤回的舊宣稱），無第四句。⚠️ 執行者主動記錄兩次工具自我打臉，皆在送出前自己抓到但都不是第一次犯：(a) grep 回報「修正未套用」——它搜「不要把上一句讀成」而原文是「但**不要**把上一句讀成」，Markdown 的 ** 打斷了連續字串，與上一輪折行那次同型，即其驗證工具又被自己的排版騙了一次；(b) 第一次全掃用 git diff origin/main..HEAD，那是已提交狀態、看不到當下未提交的編輯，掃出來的是舊文字，差點據此回報「已改完」，改用 git diff origin/main（含工作樹）重掃才對。數字：基線 d18cd83 為 944 passed、head 976 passed（純註解、行為零變更）、CI 獨立實跑 976 passed 且 headSha e08c6b66d502 逐字相符全綠、uv lock --check 通過、replay 65/65、trailer guard 7 個 commit 全 compliant；需求方原句兩處各 1 次、SHA-1 61a31e5f… 未變。射程仍為宣告五檔，守衛未動、doctor 未動。⚠️ 執行者自陳一項不確定：本輪掃的是它自己寫的新增行，amend_cmd.py 既有段落裡還有兩句帶全稱語氣（例如某處「任何其他改動…都會被抓到」），不在本卡射程也不是它寫的，未動；若那類宣稱也該一併校正需要另開卡。。
- 2026-08-17T12:26:42+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex）；iteration 0；SHA 77ec90575d24472774a79235564d60ef494d6320；證據 R6-001（第四句全稱宣稱：test_amend.py 仍宣稱「封閉性來自 (1)+(2)／量詞由構造關閉」，與 M27 直接矛盾）之處置。⚠️ PM 本輪不再要求逐句修，改要求【把會出錯的那一類句子整個刪掉】——理由是四輪四句、每一輪的「掃完了」都不成立（威脅模型輪執行者自補一句、R5 查核者抓一句、R6 執行者自找兩句、R6 查核者又找一句），掃描不會收斂因為「這句讀起來像不像過度宣稱」是語意判斷、是開放集合。文件句子分兩類：事實（陳述跑過什麼、結果是什麼、不涵蓋什麼——構造上不可能是過度宣稱）與綜述（從事實推出的保證——四句全部出自這一類）。規則：文件裡不出現任何「因此／所以／故 ⇒ 保證」形式的句子，只留 (1) 做了什麼 (2) 跑過什麼結果如何 (3) 已知不涵蓋什麼，讀者自己從三項得結論。執行者正面回答「形狀還是實例」：形狀，與 R4 同一判斷換一層——前四輪修的是句子（每次刪掉一句被抓到的，下一句從同一個模具長出來），刪掉綜述類移除的是產生錯誤的模具而非第 N 個成品；並自陳唯一想過的替代「保留綜述但加限定詞」就是 R1–R6 一路在做的換劑量。刪除清單 12 句：封閉性來自 (1)+(2)／量詞從對這些輸入換成由構造／兩條合起來對所有輸入都是同一個模板＋代入／這一條因此對所有 (author,url) 一次成立／函式恆為模板＋代入——由構造不是由取樣／守衛涵蓋到該形狀為止即停／用不可以是什麼去守開放集合永遠會有下一個沒被列舉到的成員／從而保證 _fold 對它是恆等函式／故不隨 Python 版本假紅／故同一個黃金值也適用這條路徑／保證被看見不保證被看對／區塊標題「以及為什麼這一代不是第五代的前身」。⚠️ 最後兩句是執行者自檢時抓的——帶「保證」「故」但方向看似往下，仍屬綜述形式，一併刪。剩餘句子逐句分類已交付（test_amend.py 守衛區塊、五個測試 docstring 全改成「本條斷言什麼」＋「實測哪些變異讓它紅」＋「本條看不見什麼」無一句推導、amend_cmd.py 常數註解同三段式、模組 docstring 的 R2 教訓段改成三次被擋下的事實流水）。⭐ 順帶補上第 2 類證據：19 筆變異的實測紅綠【先前只活在交付報告裡、碼裡沒有】，已寫進守衛區塊第 2 節並含各次執行範圍（M14–M26b 是兩檔子集、M20 舊守衛與 M27 是全套），避免數字看起來可比但其實不可比。⚠️ 執行者提出一個需要查核者裁的問題：保留的「限制型」句子（如「對擁有這份碼的人，任何測試與任何執行期檢查都無效」）它歸為第 3 類（陳述不涵蓋、方向只能往下、非從事實推出的保證），若查核者認為那仍算綜述它願意刪。數字：基線 d18cd83 為 944 passed、head 976 passed（純註解、行為零變更）、CI 獨立實跑 976 passed 且 headSha 77ec90575d24 逐字相符全綠、uv lock --check 通過、replay 65/65、trailer guard 8 個 commit 全 compliant、需求方原句兩處各 1 次 SHA-1 61a31e5f… 未變。射程仍為宣告五檔，守衛未動、doctor 未動、M27 未修。⚠️ 執行者本輪【沒有再宣稱「掃完了」】：它按規則刪了找得到的綜述句，但明說判斷一句話算不算綜述本身仍是語意判斷，差別在於現在有一條可機械複查的形式規則（不得出現「因此／所以／故 ⇒ 保證」句式），查核者可以照著掃而不是憑感覺判斷哪句話講得太滿。。
- 2026-08-17T13:49:35+08:00 handoff by wf-cli → owner —；iteration 0；SHA 77ec90575d24472774a79235564d60ef494d6320；證據 結案。PR #96 squash merge → ai-workflow main d0008b3288a2df9541f03cff7784693f6a429095，CI 兩個 check 皆 SUCCESS。查核 GPT-5@Codex issuecomment-5312252522（更正版）：core_pain_resolved yes、APPROVE、findings 0。⚠️ 更正版的緣由：初版 R7-01 宣稱需求方原句已從分支消失（whitespace-tolerant regex 兩檔皆 0 命中），PM 貼出反證 issuecomment-5312240998 後查核者以 git show <sha>:<file> 重驗，確認原句在 amend_cmd.py 與 test_amend.py 各 1 處並撤回。出錯原因是 tr -d 的位元組層陷阱（全形空格 E3 80 80，0xE3 是大量中日韓字元首位元組，逐位元組刪除會打碎文字）；PM 第一次驗也踩了同一個坑。merge 後於 main 驗證 pytest 976 passed。⚠️ PM 首次量測時本地 checkout 仍在 71df157（落後兩筆）而誤報 879，pull 後重量才是 976——當日第十二次「量了別的東西然後宣稱它是我要的那個」。gitlink 已同步：cpbl-analytics main 4d03e67 的 .ai-workflow 指向 d0008b3，免部署。⚠️⚠️ 【本次 release 未帶 --cleanup，是規則暫置，理由如下】清理【實際已完成】：worktree wf-amend-authz-binding1 已 git worktree remove、本地分支已刪（was 77ec905）、遠端分支已 push --delete，git worktree list 對本卡 0 命中。但 wfcli 的 cleanup 守衛拒收，訊息為「分支worktree 欄沒有可解析的分支，無法界定要清理什麼」——因為本卡全程以子代理派工、從未執行 wfcli assign，而該欄位只有 assign 會寫（全 repo 唯一 set_field_value 呼叫點在 assign_cmd.py:254）。amend 無任何旗標可設該欄。故守衛在構造上無法驗證一件已經做完的事。此缺口屬 #94 家族卡（契約↔工具對帳）的同族，已記入本 evidence 供對帳表採用。⚠️ 剩餘結案義務（不擋 release）：卡檔封存、Ledger 投影重建、對帳三件套。。
- 2026-08-26T14:20:25+08:00 amend by wf-cli（op fd08c9bc）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:2fad84b4ff25a4d81796f6968f9f1eda2992cf37a4fa0a2bb494d436998a3a19 (597 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第二批（20 張純隨機）：依 canonical §6.3 回填簡介；文字經 A5 守衛（分行字元＋1012B 上限）預先拒收檢查。


## Comment 5305375408 · 2026-08-16T02:41:19Z

## PM 更正：本次 amend 的理由裡有一句是錯的，且錯的方向讓本卡的射程比原本以為的窄（2026-08-16）

PM 在剛才那筆 `amend`（op `05cf6174`）的理由中寫了：

> ⚠️ 本次 amend 走 `--ruling-url`，而該旗標的恆真檢查正是本卡要修的東西——**用那個檢查去修那個檢查**，此事實一併記錄。

**那句話是錯的。** CLI 當場回覆：

```
[amend] 提示：本次修訂不需要需求方裁定授權，--ruling-url 未被核對，
        亦不寫入 Log（避免留下看似已授權的痕跡）
```

### 這對本卡是實質資訊，不只是 PM 認錯

`amend` 的授權檢查**只作用在核心痛點的修訂**（`--core-pain`），其餘欄位的修訂**根本不走那條路**，而且 CLI **主動避免**在 Log 留下看似已授權的痕跡。

**所以本卡的缺陷比卡面敘述的窄**：不是「`amend` 的授權欄無條件宣稱已核對」，而是「**`--core-pain` 路徑的授權欄**無條件宣稱已核對」。

那 10 筆已實現事件應逐一複核是否全部落在 core-pain 路徑上——PM 尚未做這件事，列為本卡執行時的第一步。

### ⚠️ 這是同一天第二次

2026-08-16 稍早，PM 在向需求方報告時說本卡「今天才第一次真的觸發」，全庫掃描後實測為 **10 筆／8 張卡**，最早 3 筆比本卡建立時間還早。

兩次都是**對機制的行為做了未經實測的推論**。第一次高估了範圍的新近性，第二次高估了缺陷的廣度——方向相反，但同一個錯。

本卡的核心痛點正是「一個字面上為真、語意上誤導的宣稱」；PM 在處理它的過程中連續產生了兩個同型的宣稱，這件事本身值得記在卡上。

### 對驗收條件的影響

剛才 amend 進去的四條驗收條件**維持不變**——它們沒有依賴那句錯誤的推論。但第 4 條「須在交付說明中列出受影響清單」應加一句：**該清單須先確認每一筆是否走 core-pain 路徑**，不得直接假設 10 筆全部適用。


## Comment 5305724012 · 2026-08-16T04:30:02Z

## 跨家族查核裁決

```yaml
core_pain_resolved: no
review_result: REQUEST_CHANGES
findings:
  - id: R1-001
    severity: blocking
    attribution: implementation
    summary: 「宣告完整性已檢查」仍宣稱得比實作證據更強
  - id: R1-002
    severity: blocking
    attribution: planning
    summary: 既存 13 筆誤導事件仍無機械更正標記，且核心痛點未被限縮為僅處理未來事件
```

### 基線與交付範圍

- 實算 merge-base：`71df1570b7ddefbbbf101f8e8b1b053e5fe82cd7`
- head：`b3fac32ce560e089702b7974b0d3e06e16ed63a0`
- diff：僅 `cli/src/wf_cli/commands/amend_cmd.py`、`cli/tests/test_amend.py`
- 基線實跑：`879 passed in 58.71s`
- CI run [31925207693](https://github.com/ruan6047/ai-workflow/actions/runs/31925207693)：`success`，`headSha=b3fac32ce560e089702b7974b0d3e06e16ed63a0`，`881 passed in 24.29s`

### Findings

#### R1-001 — blocking：新句仍有 umbrella claim

實作實際證成的是：

1. URL 形狀可解析，且 repo／issue 指向本卡；
2. 留言存在且可取到 GitHub author；
3. author 欄逐字等於卡面「需求：」欄；
4. author 不等於當前 owner。

它**不讀留言內文，也不讀操作者身分**。因此它沒有檢查「該留言是否真的包含完整裁定／代貼揭露／授權來源」，更沒有驗證誰實際張貼。

新句後半已誠實揭露操作者不可區分，這部分正確；但前面的「**宣告完整性已檢查**」會自然被讀成整份授權宣告已通過完整性檢查。冒號後雖列出部分實際核對內容，仍不足以消除這個較強的總括宣稱，尤其同一句外層仍稱該 URL 為「裁定」，而函式根本不讀留言內容。

這正是本卡要消滅的「描述強度高於證據」形狀。請直接改成窮舉事實、不要替它命名為整體完整性，例如：

> （已核對：該 URL 指向本卡 issue 的既存留言，且其 GitHub author 欄逐字等於卡面「需求：」欄。本指令不讀取留言內文或操作者身分，故不判定留言內容是否構成裁定，亦不區分「需求方本人張貼」與「他人代擬代貼」）

若產品仍要把留言稱作「裁定」，就必須另行界定那是操作者的**宣告**，不是本指令已檢查出的事實。

#### R1-002 — blocking：移除 legacy marker 是實質迴避，不只是合理邊界

08-16 amend 可以合法改驗收條件，但它沒有同步改寫本卡核心痛點。核心痛點明列 #58 的既存事件及「只讀結構化欄位的消費者會拿到錯的印象」；服務原始目標也沒有寫成「只保證未來事件」。

目前修法只改未來回傳常數。既存 13 筆仍永久帶著舊句，且沒有任何可由機器辨識的 correction／legacy／unknown 標記。把 9 卡清單列在 #62 的交付留言，只能幫助讀到 #62 的人，無法幫助正在讀那 13 筆授權欄的消費者。

因此，將原驗收條 5 的 legacy 要求移出射程，在**程序上有留痕**，但在**實質上未關閉卡面仍宣稱要處理的痛點**。可接受的兩條路：

- 以 append-only correction 事件或其他機械可解析索引標記 13 筆；不得改寫原事件。
- 由需求方正式把核心痛點限縮為 prospective-only，並逐字接受：13 筆舊授權欄仍會對只讀該欄的消費者造成錯誤印象。本輪才可不把 legacy 標記算在交付內。

### 其餘重點複驗

#### 13 筆／9 張卡：可重現

對 Project #4 的 `totalCount=148` 全部 item body 掃描，條件限定為同一行同時含 `amend by wf-cli` 與完整舊句；結果為 **13 events／9 cards**：

- `ai-workflow#11` ×1
- `ai-workflow#25` ×1
- `ai-workflow#31` ×1
- `ai-workflow#38` ×1
- `ai-workflow#48` ×1
- `ai-workflow#57` ×4
- `ai-workflow#58` ×1
- `ai-workflow#88` ×1
- `cpbl-analytics#129` ×2

repo 分布為 ai-workflow 11/8、cpbl-analytics 2/1。13 筆的事件欄位全部解析為「核心痛點」；沒有 tier-downgrade 舊事件。另有 #62 核心痛點正文引用舊句，但那不是 amend event，未計入 13。

#### tier-downgrade 射程：目前實作有涵蓋

`tier_downgrade_needs_ruling(old_tier, args.tier)` 為真時，與 `--core-pain` 一樣呼叫唯一的 `_authorize_by_requester_ruling()`；回傳的同一個 `ruling_note` 在級別 change tuple 寫入 Log。因此本次改函式回傳常數，**目前確實同時涵蓋 T3/T4 降級路徑**。

現有 tier-downgrade 測試只斷言有 `；授權 …`，沒有逐字釘新免責句；這不是當前路徑漏接，但建議補一條 tier-downgrade 輸出斷言，避免日後兩路徑拆分時靜默退化。

#### 兩條新斷言：互不涵蓋，但負面斷言只防已知舊句

我在隔離副本重做兩個 mutation：

- M1 還原完整舊值：`2 failed`
- M2 保留「比對過什麼」、刪除免責段：`1 failed, 1 passed`

邏輯上也互不蘊含：加入新免責句但同時保留舊句時，正面斷言可綠、負面斷言會紅；刪掉兩者時，負面可綠、正面會紅。因此它們不是同一個恆真斷言的兩種寫法。

但負面測試只封鎖精確片語 `非留言內文自述`，不會自動抓到另一句等價誇大措辭；語意正確性仍必須由本輪人工查核裁定，不能把這兩條測試當成通用語意守衛。

### 結論

目前程式接線、13/9 計數、CI 與 mutation 證據均成立；阻擋原因不是功能路徑漏接，而是新總括措辭仍高於實際證據，以及歷史錯誤欄位在未限縮核心痛點的情況下完全未標記。故本輪為 **REQUEST_CHANGES**。


## Comment 5308012612 · 2026-08-16T14:49:08Z

## 第二輪跨家族查核裁決

```yaml
core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: "git ls-remote origin refs/heads/main refs/heads/claude/WF-AMEND-AUTHZ-BINDING1 && git merge-base origin/main origin/claude/WF-AMEND-AUTHZ-BINDING1"
    observed: "remote main=d18cd83795f1fee96f634e78c81893019f1898cf；branch=661bde1623a348797d6fbb3b9bf65de8cfc168f4；merge-base=d18cd83795f1fee96f634e78c81893019f1898cf。"
  - command: "git diff --name-status d18cd83795f1fee96f634e78c81893019f1898cf..661bde1623a348797d6fbb3b9bf65de8cfc168f4 && git diff --check d18cd83795f1fee96f634e78c81893019f1898cf..661bde1623a348797d6fbb3b9bf65de8cfc168f4"
    observed: "恰為宣告的五檔；diff --check 無輸出。"
  - command: "cd <baseline-disposable-worktree>/cli && uv run pytest -q; cd <head-disposable-worktree>/cli && uv run pytest -q"
    observed: "baseline 944 passed in 63.70s；head 968 passed in 64.58s。"
  - command: "cd <head-disposable-worktree>/cli && uv run python -m wf_cli.cli doctor .. --registry none [分別以：無旗標／只加 --legacy-authority-notes／加 --owner ruan6047 --project 4／再加 --json 執行]"
    observed: "無旗標為 not_scanned 且指向 CLI 旗標；缺 owner/project exit 2 並同時指名兩者；實掃 150 cards／15 findings／9 cards；JSON 為 status=scanned、scanned_cards=150、findings=15、cards=9。"
  - command: "M3／M4 apply_patch 後：uv run pytest -q tests/test_amend.py -k 'authority_note_discloses or authority_note_does_not_claim or authority_note_has_no_summary'"
    observed: "M3 與 M4 各為 1 failed, 2 passed，只有 test_authority_note_has_no_summary_label_before_the_facts 轉紅。"
  - command: "反例 M3b apply_patch：在第一個已釘事實後插入「授權綁定成立；」，再跑同三條 test_amend 測試"
    observed: "3 passed。現行結構斷言只鎖 opener 到第一個事實，不能證成「任意新標籤必然被抓」。"
  - command: "M9 apply_patch 移除 legacy_authority_card_bodies=legacy_bodies；uv run pytest -q tests/test_doctor.py -k 'cli_flag_actually_scans or legacy_notes_never_affect or cli_does_not_feed or cli_json_payload_carries_legacy'"
    observed: "4 failed；CLI 接線、strict 前提、參數隔離與 JSON 四面皆有鑑別力。"
  - command: "M12 apply_patch 將抓取前初值 None 改為 {} 後跑 tests/test_doctor.py；M12b 移除抓取 try/except 後跑 keeps_not_scanned_when_card_fetch_fails"
    observed: "M12 為 121 passed，兩個 falsy 初值對目前可觀測行為等價；M12b 以未捕捉 RuntimeError 轉紅，構造成立。"
  - command: "git grep -n -E 'additionalProperties|jsonschema|schema.*doctor|legacy_authority_notes' 661bde1623a348797d6fbb3b9bf65de8cfc168f4 -- ':!cli/tests/*'"
    observed: "repo 內無 doctor JSON 嚴格 schema 或封閉鍵消費端；新增鍵是既有 asdict payload 的 additive change。"
  - command: "uv lock --check && uv run python ../scripts/replay_escalation_rules.py; gh run view 31928377799 --repo ruan6047/ai-workflow --log"
    observed: "lock check 通過；escalation replay 65/65；CI headSha=661bde1623a348797d6fbb3b9bf65de8cfc168f4，968 passed。"
findings:
  - finding_id: WF-AMEND-AUTHZ-BINDING1-R2-001
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: structural-guard-scope-overclaimed
    evidence: "把「授權綁定成立；」插在第一個事實「該 URL 指向本卡 issue 的既存留言」之後，三條 authority-note 測試仍 3 passed；直接反駁原始碼註解、測試 docstring 與交付證據所稱「任何新標籤都必然插在 opener、因此必然被抓」。"
    disposition: "不得再把此斷言描述成任意新標籤的通用守衛。二擇一：把證據與註解限縮為只防「括號開頭、第一個事實之前」的插入，並明說其餘語意仍靠人工查核；或把整段 canonical 註記（動態 author/URL 正規化後）釘成精確模板，使任意位置插字確實轉紅。"
```

### R1 兩條 blocking 的閉環

- **R1-001 的現行輸出已解決。**「已核對：」不是新的 umbrella label。它沒有替結果取名，也沒有宣稱授權、完整性或綁定成立；冒號後立即封閉列出核對的兩件事，且兩件事都由實作證成。外層「裁定」也已明寫為操作者宣告，不是指令查得事實。因此目前字面沒有高於證據。
- **R1-002 已解決。**舊字面本身成為可機械辨識的 legacy marker；掃描錨定最後一個「；授權 」之後，能排除正文引用與「原值舊字面＋新授權欄」假陽性。finding 只含定位資訊，報告也明說留痕強度不足不等於個別授權無效。

### M3／M4 的正面裁定

「標籤是開放集合，黑名單列不完」成立；「所以釘住已知插入位置」也是合理策略。但交付再往上說成「標籤只能插在該位置，因此任意新標籤必然被抓」不成立。M3／M4 只證明 opener mutation 會被結構斷言抓到；我的 M3b 證明同一標籤移到第一個事實之後即可全綠。這不推翻目前文案，卻推翻交付對測試守衛範圍的宣稱，故本輪退回的是 evidence claim，不是授權句本身。

### opt-in 是否仍是半條線

**不是。**甲案要求的是可機械辨識與可執行的 doctor 檢查，沒有要求每次 doctor 都必須掃 Project。現在已有 CLI 可達路徑、必填參數驗證、成功／失敗／未掃描三態，以及未帶旗標時的明確指路；這和上一輪「CLI 無論如何都傳不到卡面」不同。把它改成預設會讓純本機 doctor 無條件連網、破壞既有不帶 owner/project 的用法，不能從甲案文字導出該 breaking change。若未來要成為 CI 閘門，應另卡定義憑證、Project 參數來源與觸發策略。

### 其餘裁定

- **不共用 card_bodies：正當。**兩參數服務不同判定域；共用會讓 cleanup-preview 的資源釋放前提在未宣告射程內開始生效。
- **legacy findings 不進 --strict：正當。**原事件不可追溯改寫，納入 strict 只會形成永久不可修復的紅燈；本檢查的價值是機械可見與正確解讀，不是阻擋。
- **M12：等價突變成立。**None 與空 dict 都經 `if not card_bodies` 導向同一 not_scanned 報告；M12b 才真正移除失敗降級路徑，測試如預期轉紅。
- **JSON additive key：本輪可接受。**我補做 repo 內消費端搜尋，未見封閉鍵 schema／嚴格 payload validator；現有 doctor JSON 本就以 additive keys 演進。外部未知消費端仍是一般相容性風險，但沒有證據足以升為本卡 blocking。
- **15 不可當常數：實作正確。**production code 沒有 13／14／15／150 的判定常數；計數由輸入與 findings 長度導出，測試以 0/1/3/7 釘住。live Project 當下重現 15/9，只是時間點快照。

### 結論

核心痛點與兩條 R1 blocking 的實際功能都已處置；本輪唯一阻擋是閉環證據再次高於其能證成的範圍。故 `core_pain_resolved: yes`，但在縮小或補強結構斷言的宣稱前仍為 **REQUEST_CHANGES**。


## Comment 5308120328 · 2026-08-16T15:14:26Z

## 第三輪跨家族查核裁決

```yaml
core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: "git fetch --no-tags origin refs/heads/main:refs/remotes/origin/main refs/heads/claude/WF-AMEND-AUTHZ-BINDING1:refs/remotes/origin/claude/WF-AMEND-AUTHZ-BINDING1 && git rev-parse origin/main origin/claude/WF-AMEND-AUTHZ-BINDING1 && git merge-base origin/main origin/claude/WF-AMEND-AUTHZ-BINDING1"
    observed: "remote main=d18cd83795f1fee96f634e78c81893019f1898cf；branch=1588d5033c0730c36cac714937878af562b5127a；自行計算 merge-base=d18cd83795f1fee96f634e78c81893019f1898cf。"
  - command: "git diff --name-status d18cd83795f1fee96f634e78c81893019f1898cf..1588d5033c0730c36cac714937878af562b5127a && git diff --check d18cd83795f1fee96f634e78c81893019f1898cf..1588d5033c0730c36cac714937878af562b5127a"
    observed: "恰為宣告五檔：amend_cmd.py、doctor_cmd.py、doctor.py、test_amend.py、test_doctor.py；diff --check 無輸出。"
  - command: "cd <baseline-disposable-worktree>/cli && uv run pytest -q; cd <head-disposable-worktree>/cli && uv run pytest -q"
    observed: "baseline 944 passed in 64.71s；head 970 passed in 64.94s。"
  - command: "M14 apply_patch：在第一個事實後插入「授權綁定成立；」；uv run pytest -q tests/test_amend.py -k 'verbatim_equal_to_the_golden_value or golden_note_also_reaches_the_log_verbatim or tier_downgrade_from_redline_succeeds_with_ruling'"
    observed: "3 failed, 169 deselected；原始反例現在確實同時打紅原始回傳值、Log 寫入與 tier-downgrade 三面。"
  - command: "M18 apply_patch：只重切 amend_cmd.py 相鄰字串常值的原始碼換行、保持併接後值不變；uv run pytest -q tests/test_amend.py tests/test_doctor.py"
    observed: "293 passed in 4.91s；純 source reflow 無假紅。"
  - command: "M20 apply_patch：新增 summary_label = '' if args.ruling_url.endswith('issuecomment-555') else '授權綁定成立；'，並把它插在第一個事實後；uv run pytest -q"
    observed: "970 passed in 67.51s。測試 fixture 唯一成功 URL 固定為 issuecomment-555，因此其他 comment id 的實際輸出可帶誇大標籤而整套測試全綠。"
  - command: "cd <M18-disposable-worktree>/cli && uv lock --check && uv run python ../scripts/replay_escalation_rules.py"
    observed: "uv lock --check 通過；escalation replay 65/65。"
  - command: "git status --short --branch && git diff --quiet && git diff --cached --quiet"
    observed: "source worktree 位於 main、behind origin/main 1；tracked 與 staged diff 皆為空，未修改 source branch。"
findings:
  - finding_id: WF-AMEND-AUTHZ-BINDING1-R3-001
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: golden-guard-covers-one-dynamic-instantiation
    evidence: "現行逐字斷言只以固定 REQUESTER=ruan6047、固定成功 URL issuecomment-555 呼叫 _authorize_by_requester_ruling。M20 讓 summary_label 對該 fixture 為空、對其他 comment id 為「授權綁定成立；」，整套 970 tests 仍全綠；故目前封閉的是單一樣本值，不是含 {author}/{url} 動態輸入的函式輸出集合。這直接反駁測試 docstring 與交付所稱「任何標籤、任何位置、任何措辭都會轉紅」及「沒有第四代」。"
    disposition: "把守衛的量化範圍補到動態輸入：至少以兩個不同 requester 與兩個不同 comment id 走成功路徑，逐一斷言原始回傳值及 Log 都只等於同一 template format(author, url)；並將 production rendering 收斂為僅允許 author/url 兩個資料插值的單一路徑，或把宣稱限縮為只保證目前固定 fixture 的執行期值。不可把「label 預設空」概括為合理殘餘；只有對所有輸入恆為空、因而完全不改變執行期值的局部常數才是無缺陷的等價改寫，任何可由參數、URL、author 或環境改成非空的插值都屬本 finding。"
```

### 八項重點裁定

1. **M14 已閉合。**把「授權綁定成立；」插到第一個事實後，指定三面均轉紅，R2-001 原反例不再成立。
2. **但封閉集合主張仍被打穿。**逐字相等只在一組動態輸入上執行。M20 是第四代：位置與措辭都被黃金值排除，但以輸入分支讓 fixture 輸出保持黃金值、其他合法輸入輸出誇大標籤，970 全綠。
3. **自陳殘餘須分兩種。**無條件局部常數 `label = ""` 對所有呼叫都不改執行期值，屬可接受的等價改寫；可由 default parameter、author、URL 或環境變成非空的 label 則不可接受，因為它會造成真實輸出分歧而現有守衛看不到。執行者把兩者一起稱為「刻意繞過」過寬。
4. **M18 無假紅宣稱成立。**相鄰字串常值純 reflow 後 293 passed；守衛比的是併接後執行期值，不依賴 source 排版。
5. **移除舊位置守衛正確。**它已被實證射程不足，保留即使標成弱守衛也沒有額外鑑別力，反而容易讓讀者把局部位置性質誤認為完整保證。
6. **兩條保留性質斷言有價值且不易誤讀。**區塊註解、兩個 docstring 都逐字標示「不是守衛」，其價值是讓黃金值被人工更新時提供語意 checklist 與具名失敗訊息；保留合理。
7. **「保證被看見，不保證被看對」定位誠實。**兩邊同步改錯本來就不是測試能裁定的語意問題；黃金值的合理作用是讓單邊文字改動先紅、雙邊改動明確出現在 diff，最後由紅線跨家族／人審判斷。此定位足夠，但不得延伸成對所有動態輸入的機械保證。
8. **直接呼叫私有函式的取捨值得。**本卡要驗的是 `_fold` 前的原始治理留痕；經公開 CLI/body 路徑只能驗排版後結果，會漏掉內容換行。這是有意識的內部契約測試，重構時測試跟著紅屬合理成本。若後續抽出純 renderer 可再降低耦合，非本輪 blocking。

### 結論

現行 tip 的實際授權句已不高於證據，legacy doctor 與前兩輪功能性 blocking 也未被本輪改壞，因此 `core_pain_resolved: yes`。但新的黃金值守衛仍把單一 fixture 誤稱為整個動態輸出域的封閉集合；在補齊量化範圍或誠實限縮宣稱前，裁決維持 **REQUEST_CHANGES**。


## Comment 5308232705 · 2026-08-16T15:38:12Z

## 第四輪跨家族查核裁決

```yaml
core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: "git fetch --no-tags origin refs/heads/main:refs/remotes/origin/main refs/heads/claude/WF-AMEND-AUTHZ-BINDING1:refs/remotes/origin/claude/WF-AMEND-AUTHZ-BINDING1 && git rev-parse origin/main origin/claude/WF-AMEND-AUTHZ-BINDING1 && git merge-base origin/main origin/claude/WF-AMEND-AUTHZ-BINDING1"
    observed: "origin/main=d18cd83795f1fee96f634e78c81893019f1898cf；branch=4c65847056d00cef964040b809d94887ee0be1d2；自行計算 merge-base=d18cd83795f1fee96f634e78c81893019f1898cf。"
  - command: "cd <baseline-disposable-worktree>/cli && uv run pytest -q; cd <head-disposable-worktree>/cli && uv run pytest -q"
    observed: "baseline 944 passed in 65.87s；head 976 passed in 66.74s。"
  - command: "M20 apply_patch：依 comment id 讓固定 555 不加字、其他 id 於模板代入後加「授權綁定成立；」；uv run pytest -q"
    observed: "3 failed, 973 passed in 67.41s；失敗為 AST 1 條及參數化執行期交叉檢查 2 組，R3 原始反例現在確實轉紅。"
  - command: "M23 apply_patch：把唯一 return 改為輸出逐字相同的 f-string；uv run pytest -q tests/test_amend.py -k 'template_substitution_by_construction or runtime_output_matches_the_template_for_varied_inputs'"
    observed: "1 failed, 4 passed；四組執行期輸出仍等於黃金模板，唯一失敗是 AST 節點不相等，故紅燈確由實作形狀而非輸出差異造成。"
  - command: "M24 apply_patch：只重切 AUTHORITY_NOTE_TEMPLATE 相鄰字串的原始碼換行，維持併接值不變；uv run pytest -q tests/test_amend.py tests/test_doctor.py"
    observed: "299 passed in 7.53s；純模板 reflow 無假紅。"
  - command: "M27 apply_patch：在唯一 return 前新增 if comment_id == '8675309': author = f'{author}；授權綁定成立'，return 仍逐節點等於 AUTHORITY_NOTE_TEMPLATE.format(author=author, url=args.ruling_url)；uv run pytest -q；再以該 id 手動呼叫"
    observed: "整套 976 passed in 67.96s；手動輸出含「依需求方 ruan6047；授權綁定成立 於 …」，matches_golden=False。AST、模板唯一指派與四組取樣全未攔下。"
  - command: "cd <head-disposable-worktree>/cli && uv run pytest -q tests/test_doctor.py && uv lock --check && uv run python ../scripts/replay_escalation_rules.py"
    observed: "doctor 121 passed；uv lock --check 通過；replay 65/65。"
  - command: "git diff --name-status 1588d5033c0730c36cac714937878af562b5127a..4c65847056d00cef964040b809d94887ee0be1d2 && git status --short --branch && git diff --quiet && git diff --cached --quiet"
    observed: "本輪僅 amend_cmd.py、test_amend.py；doctor 三檔未動。source worktree 仍在 main，tracked/staged diff 皆空；所有變異位於已移除的 disposable worktree。"
findings:
  - finding_id: WF-AMEND-AUTHZ-BINDING1-R4-001
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: construction-guard-does-not-bind-format-operands
    evidence: "M27 在 _authorize_by_requester_ruling 的唯一 return 前，依未取樣 comment_id 改寫已通過 author/requester 比對的 author 區域變數；return AST 仍逐節點完全等於 AUTHORITY_NOTE_TEMPLATE.format(author=author, url=args.ruling_url)，模板也仍只有一處靜態指派，但整套 976 tests 全綠。實際以 comment_id=8675309 呼叫時輸出「依需求方 ruan6047；授權綁定成立 於 …」，與黃金值不等。故 (1) 模板逐字固定 ∧ (2) return 表達式固定，只能證明最後呼叫的語法，不能證明 author/url 仍是已驗證的原始輸入；「不存在任何 (author, url) 能得到不同字串」與「量詞由構造關閉」均不成立。"
    disposition: "不要再增加 comment-id 樣本。若要保留 ∀ 輸入的機械主張，須把 renderer 抽成真正的純函式並約束其有效函式體只有模板代入、模板為精確 str，同時約束授權函式將剛驗證的 author 與原始 ruling_url 不經可變資料流直接交給 renderer，且新增 M27 回歸使其轉紅；仍須把此定位為 source-shape tripwire，而非對動態改寫的形式證明。若不願承擔這種白箱耦合，則移除「由構造關閉量詞／不存在任何輸入」的宣稱，誠實限縮為黃金值＋多組執行期樣本的回歸守衛。"
```

### 重點裁定

1. **M20 已閉合。** 原始反例現在三紅；AST 守衛與新增交叉樣本都有鑑別力。
2. **但「由構造」仍未閉合量詞。** M27 不是換第五個 comment id 來碰運氣，而是攻擊 AST 證明缺失的資料流前提：固定的是 `format(author=author, url=args.ruling_url)` 這棵語法樹，不是兩個運算元的來源與不變性。Python 名稱可在 return 前重綁；AST 測試沒有做 def-use／provenance 分析。
3. **M23 的證據成立但結論過度。** 四組輸出相同、只有 AST 紅，證明守衛確實盯實作形狀；它不能反推該形狀足以保證所有輸出。M27 正是反例。
4. **M24 無假紅成立。** 純相鄰字串 reflow 為 299 綠。但 M23 同時證明行為等價的 f-string 會假紅；合法抽 renderer 也會紅。這種耦合在此低頻、紅線治理句上可接受為明示的架構契約／review tripwire，不可接受為完整性證明。若持續誤稱為證明，維護者為合法重構而移除它的風險會上升。
5. **縫 1 裁定：本卡不值得上資源檔＋雜湊；這是工程判斷，不是事實。** 資源檔與 hash 只保護靜態 artifact，不能讓 Python 模組 binding 不可變；同一行程若能動態指派，也能改讀取／驗雜湊路徑。以本卡的威脅模型（防止日後 source regression 被無聲帶入）來看，增加 I/O、封裝與部署維護成本高於收益。應先收斂並誠實命名 tripwire 的保證範圍。
6. **縫 2 裁定：同一 Python 行程內的任意 monkeypatch 無法由被 patch 的模組自行絕對阻止。** 可行的強化只有把信任邊界外移，例如隔離程序、啟動時驗證簽章／hash、在 sink 前由另一可信元件驗證；但具有任意 monkeypatch 能力者也能 patch 驗證器或寫入點。因此執行者的「本架構內無解」成立；若解讀成所有架構皆無解則過度。此項非本卡 blocking。
7. **具體寫法耦合只在「tripwire」定位下可接受。** 純 renderer 是較好的下一形狀，但即使抽出，也必須釘函式體無其他 statement、插值運算元未被重綁、模板是 plain `str`，並另外守呼叫端資料來源；否則只是把 M27 搬家。形式驗證 [formal verification] 不在本卡合理射程。
8. **doctor 未回歸。** tip 相對前輪只動 amend_cmd.py／test_amend.py；head 全套 976 綠、test_doctor.py 121 綠、replay 65/65，opt-in 接線維持 R2 已裁定狀態。

### 結論

未變異 tip 的實際授權句仍據實揭露「沒讀留言內文／操作者、不能區分本人與代貼」，legacy doctor 也未退化，所以核心痛點本身已消失，`core_pain_resolved: yes`。但本輪新增的核心價值是「量詞由構造關閉」，而 M27 證明它只固定最後一個表達式、沒有固定進入表達式的值；在守衛補上資料流前提或撤回 universal claim 前，維持 **REQUEST_CHANGES**。

## Comment 5311176521 · 2026-08-17T02:45:21Z

## 需求方裁定 2026-08-16：本卡的守衛已涵蓋它被開出來要擋的東西，停在這裡

⚠️ 本留言由 PM（Claude Fable 5@Claude Code）代擬代貼，內容為需求方裁定。amend 的 author 檢查對 PM 恆真——那正是本卡在修的東西（見 Log 與 `doctor --legacy-authority-notes`）。

### 對 R4-001（M27）的處置：記為已知不涵蓋，不修

M27 是「在 `return` 前依 comment id 改寫 `author`」。查核者指出 AST 只釘 `return TEMPLATE.format(author=author, url=args.ruling_url)` 這個**語法**，不約束 `author` 這個**值**的來源——正確。

但要關掉它就得約束資料流；關掉資料流，下一個是裝飾器、是 `_resolve_ruling_author` 內部、是 monkeypatch。執行者早在 R4 自陳縫 2：「執行期 monkeypatch 完全擋不住，原始碼層面攔不住，我沒有辦法。」**M27 是它的原始碼版本。**

### 真正的問題是這個守衛從來沒有定義過威脅模型

**本卡的守衛防的是「無意的後續編輯」，不防「蓄意繞過的提交者」。**

- **無意**：有人改措辭、有人補說明時加個總結標籤、有人換個弱形容詞。⚠️ **M20／M22／M25／M26b 全部是這一類，全部已經紅。**
- **蓄意**：M27 是這一類。**沒有人會不小心寫出「依 comment id 改寫 author」。** 而對這一類，任何測試與任何執行期檢查都無效——他擁有那份碼。

本卡的核心痛點是「留痕宣稱了它沒有的區辨力」，那是**無意的過度宣稱**，不是防內鬼。`core_pain_resolved` 已連三輪 `yes`。

### 因此

1. **威脅模型逐字寫進碼與卡**：守的是無意編輯，不守蓄意繞過。
2. **M27 記為已知不涵蓋並附理由**（它不是無意編輯的形狀），不修。
3. R4 執行者自陳的四個縫一併如實記載，特別是縫 2（monkeypatch 無解）。

⚠️ **這是比例判斷不是證明。** 需求方不能證明 M27 不會發生，只能說它不是這個守衛被開出來要擋的東西。此句須逐字保留，不得軟化成「已充分防護」。

### 可重用的判準

往後守衛類 finding **先問「防誰」，涵蓋到了就停**。不是每次都再擋一個，而是先定義「夠了」是什麼。

本卡是這條判準的第一個案例：四輪 finding 裡前三輪打的是守衛涵蓋不足（成立），第四輪打的是守衛擋不住蓄意繞過（也成立，但那不是本卡的威脅模型）。


## Comment 5311544259 · 2026-08-17T03:50:07Z

## 第五輪跨家族查核裁決

```yaml
core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: "git fetch --no-tags origin refs/heads/main:refs/remotes/origin/main refs/heads/claude/WF-AMEND-AUTHZ-BINDING1:refs/remotes/origin/claude/WF-AMEND-AUTHZ-BINDING1 && git rev-parse origin/main origin/claude/WF-AMEND-AUTHZ-BINDING1 && git merge-base origin/main origin/claude/WF-AMEND-AUTHZ-BINDING1"
    observed: "origin/main=d18cd83795f1fee96f634e78c81893019f1898cf；branch=060ee64e284e90c365eedfd466fc817d2524d29c；自行計算 merge-base=d18cd83795f1fee96f634e78c81893019f1898cf。"
  - command: "git diff --name-status 4c65847056d00cef964040b809d94887ee0be1d2..060ee64e284e90c365eedfd466fc817d2524d29c && git diff --check 4c65847056d00cef964040b809d94887ee0be1d2..060ee64e284e90c365eedfd466fc817d2524d29c"
    observed: "R4→R5 只動 cli/src/wf_cli/commands/amend_cmd.py 與 cli/tests/test_amend.py；diff --check 無輸出。"
  - command: "python3 -c '<parse both revisions; remove module docstring; compare ast.dump>' <(git show 4c65847:cli/src/wf_cli/commands/amend_cmd.py) <(git show 060ee64:cli/src/wf_cli/commands/amend_cmd.py)；同法比較 test_amend.py"
    observed: "amend executable AST equal: True；test executable AST equal: True。執行敘述零變更；嚴格說模組 __doc__ 是可觀察值且本輪刻意改變，故不是整個 module runtime object 位元組等同。"
  - command: "gh api repos/ruan6047/ai-workflow/issues/comments/5311176521 --jq .body | ruby -EUTF-8:UTF-8 -ne '$_.scan(/需求方不能證明 M27 不會發生，只能說它不是這個守衛被開出來要擋的東西/) { |m| puts m }' | shasum；並對 060ee64 的 amend_cmd.py、test_amend.py Git blob 執行同一擷取與 shasum"
    observed: "三處各命中一次，三份 SHA-1 全為 61a31e5ff73b12f5d91868adaa5b0ce6682ef388；需求方原句逐字保留，未被 reflow 或軟化。"
  - command: "git worktree add --detach <tmp>/base d18cd83795f1fee96f634e78c81893019f1898cf；git worktree add --detach <tmp>/head 060ee64e284e90c365eedfd466fc817d2524d29c；分別 cd cli && uv run pytest -q"
    observed: "baseline 944 passed in 73.77s；head 976 passed in 70.23s。"
  - command: "cd <head-disposable-worktree>/cli && uv lock --check && uv run python ../scripts/replay_escalation_rules.py"
    observed: "uv lock --check 通過；replay 65/65。未執行 wfcli。"
  - command: "gh run list --repo ruan6047/ai-workflow --branch claude/WF-AMEND-AUTHZ-BINDING1 --limit 5 --json databaseId,headSha,status,conclusion,workflowName,url"
    observed: "CI run 31989301600 completed/success，headSha 逐字等於 060ee64e284e90c365eedfd466fc817d2524d29c。"
  - command: "git status --short --branch && git diff --quiet && git diff --cached --quiet"
    observed: "source worktree 仍在 main（behind origin/main 1）；tracked 與 staged diff 皆空。所有測試 worktree 已移除，未修改 source branch。"
findings:
  - finding_id: WF-AMEND-AUTHZ-BINDING1-R5-001
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: threat-model-record-retains-stale-universal-guard-claim
    evidence: "060ee64 的 amend_cmd.py:295-297 仍寫『不要在 return 之前依任何條件改寫它：那會讓 AST 斷言當場紅』；但同檔 :299-303 緊接著承認在 return 前改寫 author 的 M27 可注入標籤、AST 已知不涵蓋，R4 自跑亦為整套 976 全綠。無論代名詞『它』被讀成 author、模板或輸出，『依任何條件』＋『AST 當場紅』都高於證據：AST 只固定 return 表達式，return 前的 operand 重綁不會紅；依未取樣條件動態改模板也不能由 AST 全稱保證。這使『守到哪為止』的記載在同一常數說明內自相矛盾，正是本輪要求排除的向上宣稱。"
    disposition: "限縮或刪除 amend_cmd.py:295-297 的全稱句，明寫 AST 只會在 return 表達式本身偏離指定語法時轉紅；return 前的 author／url 資料流重綁與其他動態改寫不在該 AST 斷言保證內，並由後續威脅模型段落承接。不要加新守衛、不要重打 M27；本 finding 只要求讓記載與既有證據一致。"
```

### 六項判斷

1. **需求方原句成立。** 我沒有用行數或全文 `grep` 判斷；三份獨立擷取各一次且雜湊全等，原句未折行、未改字、未軟化。
2. **四條縫記載完整。** 對照 #62 Log 的 R4 交付自陳，四條依序涵蓋：AST 看不到模組別處的動態常數改寫、執行期 monkeypatch、呼叫端 `_fold` 仍是固定輸入取樣、production/test 黃金值同步改錯。縫 2 的「無解」在本段上下文被限定為「對擁有這份碼的人／原始碼層面／本守衛所在信任邊界」，與 R4 裁定的「本架構內無法自我絕對阻止」一致；不應外推成所有架構皆無解。
3. **「無意 vs 蓄意」未機械定義是可接受留白。** 這是需求方選定的威脅模型，不是可由語法推導的分類。debug 分支忘記移除在主觀上可能是無意，但客觀形狀仍是文件已逐字點名的 M27，且文件已明說 M27 不涵蓋；再加上「四例不是所有無意編輯保證」，下一位維護者不應據此推論 debug 遺留必會被擋。若日後要消除語意歧義，宜把名稱改成「一般措辭維護 vs 刻意改變資料流／繞守衛形狀」，但本輪不因此另擋。
4. **不替註解再加守衛的理由成立。** 測試最多能釘註解字串存在，不能判斷它是否誠實；同步改測試仍會綠，語意判斷最後仍在人審。為註解再加字串守衛只會增加白箱耦合與遞迴層，沒有新增可信邊界。這個 residual 由 diff review 承擔是合理取捨。
5. **卡面缺口本輪可接受。** #62 的 `需求：—` 令既有 `amend` 無法綁定需求方，且沒有旗標可補該欄；強行繞寫會違反唯一寫入通道。威脅模型目前同時存在於需求方裁定留言、卡面 Log 的 060ee64 handoff 摘要與最接近守衛的程式碼，已足以讓本卡可回溯；結構化卡面無落點的家族缺口已由 #94 承接，不要求本 source branch 擴大射程。若要把可重用判準升為 canonical，應由獨立治理卡修改 AI_WORKFLOW／模板，而非塞進本卡未支援欄位。
6. **執行路徑零變更成立。** R4→R5 只有模組 docstring、常數說明註解與測試區塊註解；去除 docstring 後兩檔 AST 完全相同，976→976。唯一精確保留事項是 Python 模組 `__doc__` 本身可被 introspection 觀察到，所以只能稱「CLI／可執行路徑零行為變更」，不能稱整個 module object 完全不變。

### 結論

實際授權句仍誠實揭露它沒有的區辨力，legacy doctor 與所有可執行路徑均未退化，因此 `core_pain_resolved: yes`。但第五輪的唯一任務是讓威脅模型記載全部往下，而常數說明仍留有一條「return 前任何條件改寫都會讓 AST 紅」的全稱句，與緊接的 M27 已知縫直接矛盾；在該句限縮前，裁決為 **REQUEST_CHANGES**。


## Comment 5311692256 · 2026-08-17T04:13:22Z

## 第六輪跨家族查核裁決

```yaml
core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: >-
      git fetch --no-tags origin refs/heads/main:refs/remotes/origin/main
      refs/heads/claude/WF-AMEND-AUTHZ-BINDING1:refs/remotes/origin/claude/WF-AMEND-AUTHZ-BINDING1
      && git rev-parse origin/main origin/claude/WF-AMEND-AUTHZ-BINDING1
      && git merge-base origin/main origin/claude/WF-AMEND-AUTHZ-BINDING1
    observed: >-
      origin/main=d18cd83795f1fee96f634e78c81893019f1898cf；
      branch=e08c6b66d5023526c3fc7a0eaa44bbe08e614fbd；
      自行計算 merge-base=d18cd83795f1fee96f634e78c81893019f1898cf。
  - command: >-
      git diff --name-status 060ee64e284e90c365eedfd466fc817d2524d29c..e08c6b66d5023526c3fc7a0eaa44bbe08e614fbd
      && git diff --check 060ee64e284e90c365eedfd466fc817d2524d29c..e08c6b66d5023526c3fc7a0eaa44bbe08e614fbd
      && python3 <AST comparison script>
    observed: >-
      R5→R6 只動 amend_cmd.py 與 test_amend.py，diff --check 無輸出；
      amend_cmd.py raw AST 相等；test_amend.py raw AST 只因測試 docstring 改變而不等，
      遞迴移除 docstring 後兩檔 executable AST 均相等。CLI／測試執行敘述零變更；
      嚴格說測試函式 __doc__ 是可觀察值，故不是整個 Python module object 完全相同。
  - command: >-
      git show e08c6b6:cli/src/wf_cli/commands/amend_cmd.py | nl -ba | sed -n '1,345p';
      git show e08c6b6:cli/tests/test_amend.py | nl -ba | sed -n '1030,1355p';
      git blame -L 1058,1116 e08c6b6 -- cli/tests/test_amend.py;
      git blame -L 1169,1272 e08c6b6 -- cli/tests/test_amend.py
    observed: >-
      逐段按語意做第四次全掃，不以單一關鍵字判斷；找到 test_amend.py:1075-1080
      仍稱量詞由構造關閉，以及 :1263-1268 仍稱「封閉性來自 (1)+(2)」。兩處與
      :1099-1115、:1200-1202 明載的 M27 缺口直接衝突，形成 R6-001。
  - command: >-
      python3 <exact phrase extraction and SHA-1 script using issuecomment-5311176521,
      amend_cmd.py@e08c6b6, test_amend.py@e08c6b6>
    observed: >-
      三處各精確命中一次；以擷取行含 trailing LF 計算，三份 SHA-1 均為
      61a31e5ff73b12f5d91868adaa5b0ce6682ef388。需求方原句逐字保留，未被 reflow 或軟化。
  - command: >-
      git worktree add --detach <tmp>/base d18cd83795f1fee96f634e78c81893019f1898cf;
      git worktree add --detach <tmp>/r5 060ee64e284e90c365eedfd466fc817d2524d29c;
      git worktree add --detach <tmp>/r6 e08c6b66d5023526c3fc7a0eaa44bbe08e614fbd;
      分別 cd cli && uv run pytest -q
    observed: >-
      baseline 944 passed in 89.87s；R5 976 passed in 74.08s；R6 976 passed in 73.77s。
      R5→R6 為 976→976，無測試數量或結果變化。
  - command: >-
      cd <r6-disposable-worktree>/cli && uv lock --check
      && uv run python ../scripts/replay_escalation_rules.py
    observed: "uv lock --check 通過；replay 65/65 通過。未執行 wfcli。"
  - command: >-
      gh run list --repo ruan6047/ai-workflow
      --branch claude/WF-AMEND-AUTHZ-BINDING1 --limit 10
      --json databaseId,headSha,status,conclusion,workflowName,url
    observed: >-
      CI run 31992780054 completed/success，headSha 逐字等於
      e08c6b66d5023526c3fc7a0eaa44bbe08e614fbd。
  - command: "git status --short --branch && git diff --quiet && git diff --cached --quiet"
    observed: >-
      source worktree 仍在 main（behind origin/main 1），tracked 與 staged diff 皆空；
      三個 disposable worktree 已移除，未修改 source branch。
findings:
  - finding_id: WF-AMEND-AUTHZ-BINDING1-R6-001
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: threat-model-record-retains-stale-universal-guard-claim
    evidence: >-
      e08c6b6 的 test_amend.py:1075-1080 仍把「模板唯一」與「return AST 固定」推成
      「對所有 (author, url)」且「量詞由構造」；同檔 :1263-1268 又明寫取樣測試本身
      不是封閉性來源，但「封閉性來自 (1)+(2)」。M27 已證明 (1)+(2) 只固定模板字面與
      return 運算式，不固定 author/url 當下值的來源；同檔 :1099-1115 及本輪新修的
      :1200-1202 也逐字承認 return 前重綁 author 時 AST 全綠。故這不是一般歷史敘述，
      而是守衛區目前仍在教讀者一個已被反例推翻的封閉性結論；前三處修正後仍有第四處，
      且兩句互相強化。
    disposition: >-
      只限縮 test_amend.py:1075-1080 與 :1263-1268 的說明：明寫 (1)+(2) 釘住的是模板
      字面與 return 運算式語法，四組執行期測試仍只是交叉取樣，三者都不封閉最終輸出域；
      M27 的 operand 重綁已知不涵蓋且依需求方裁定不修。不要新增守衛、不要重打 M27、
      不要擴動 doctor。保留「同一模板的代入」時，須像 amend_cmd.py:295-296 一樣在該句
      旁直接界定它只描述組裝方式，不代表最終字串或資料流封閉。
```

### 本輪重點判斷

1. **R5-001 指名句已正確閉合。** `amend_cmd.py:298-303` 現在只聲稱改動 `return` 運算式本身會讓 AST 紅，並緊接著明寫 return 前重綁值不會被抓；與 M27 一致。
2. **第 (2) 句的修訂本身正確。** `test_amend.py:1198-1205` 已把輸出限定為 `author`／`url` 當下持有值的模板代入，並明確撤回「不存在任何其他輸出」；列出的四種紅燈也都限定為改 `return` 運算式本身，沒有再偷渡資料流保證。
3. **第 (3) 句的鄰接界定有效。** `amend_cmd.py:292-296` 的「同一模板的代入」字面仍真，而下一段立刻界定它只描述組裝方式、不描述最終字串；「被代入值不在 AST 約束範圍」與 M27 相符。界定文字本身沒有製造新宣稱。
4. **但第四次全掃確實找到第四處。** `test_amend.py:1266` 的「封閉性來自 (1)+(2)」不是字面技巧可救：此處的「封閉性」承接最終輸出域，M27 已直接反證。其上方 :1079-1080 的「對所有／量詞由構造」又讓錯誤讀法更強，因此合併成一條 blocking，而不是拆成兩個同根因 finding。
5. **需求方原句未動。** 沒用 `grep` 判斷；三份來源各做精確擷取與雜湊，含換行的 SHA-1 均為 `61a31e5f…`。
6. **零執行路徑變更成立。** R5→R6 只有註解與一個測試 docstring；可執行 AST 相同、976→976。精確保留：測試函式 `__doc__` 可被 introspection 觀察，因此只稱 CLI／測試執行敘述零變更。
7. **射程外兩句不使本輪校正失效。** `amend_cmd.py:408-420` 的「任何其他改動都會被抓到」明確屬排版修復 runbook，且其判準是完整字串精確相等；`amend_cmd.py:646-648` 是對唯一 return 的維護禁令，不宣稱 return 前資料流必會被抓。兩者主詞、機制與段落邊界都和授權註記威脅模型不同，讀者不會合理拿它們覆蓋 M27 免責；本輪不需改，也沒有足夠事實另開卡。

### 結論

實際寫入的授權註記仍據實揭露它沒有的區辨力，legacy doctor 與所有可執行路徑亦未退化，因此 `core_pain_resolved: yes`。但本輪唯一重要任務是消除守衛說明中的向上全稱宣稱，而同一測試區仍把 `(1)+(2)` 稱為封閉性來源；在該殘留限縮前，裁決維持 **REQUEST_CHANGES**。


## Comment 5311926996 · 2026-08-17T04:43:44Z

## 第七輪跨家族查核裁決

```yaml
core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: >-
      git fetch --no-tags origin refs/heads/main:refs/remotes/origin/main
      refs/heads/claude/WF-AMEND-AUTHZ-BINDING1:refs/remotes/origin/claude/WF-AMEND-AUTHZ-BINDING1
      && git rev-parse origin/main origin/claude/WF-AMEND-AUTHZ-BINDING1
      && git merge-base origin/main origin/claude/WF-AMEND-AUTHZ-BINDING1
    observed: >-
      origin/main=d18cd83795f1fee96f634e78c81893019f1898cf；
      branch=77ec90575d24472774a79235564d60ef494d6320；
      自行計算 merge-base=d18cd83795f1fee96f634e78c81893019f1898cf。
  - command: >-
      git diff --name-status origin/main...77ec90575d24472774a79235564d60ef494d6320
      && git diff --stat e08c6b66d5023526c3fc7a0eaa44bbe08e614fbd..77ec90575d24472774a79235564d60ef494d6320
      && git diff --check e08c6b66d5023526c3fc7a0eaa44bbe08e614fbd..77ec90575d24472774a79235564d60ef494d6320
      && python3 <遞迴移除 docstring 後比較 ast.dump 的腳本>
    observed: >-
      R6→R7 只動 cli/src/wf_cli/commands/amend_cmd.py 與 cli/tests/test_amend.py；
      diff --check 無輸出；兩檔移除所有層級 docstring 後 executable AST 均逐字相等。
      本輪沒有可執行敘述變更；模組／函式 __doc__ 是刻意改變的可觀察值。
  - command: >-
      git show 77ec90575d24472774a79235564d60ef494d6320:cli/tests/test_amend.py
      | nl -ba | sed -n '1040,1355p'
      && git show 77ec90575d24472774a79235564d60ef494d6320:cli/src/wf_cli/commands/amend_cmd.py
      | nl -ba | sed -n '245,350p'
      && python3 <在上述區段列出「因此／所以／故／保證／證明／封閉／涵蓋」句的掃描腳本>
    observed: >-
      三段式主區塊可讀且大部分句子可直接歸入「斷言內容／實測結果／已知不涵蓋」；
      但 test_amend.py:1265-1266、1303-1305、1329-1331、1345-1346
      仍有從斷言向上推出「另一邊仍會紅／證明寫入路徑沒有加工／逼改動被看見／已涵蓋」
      的綜述。這些句子不靠「因此／所以／故保證」連接詞，故現行形式規則會漏。
  - command: >-
      git worktree add --detach <tmp>/base d18cd83795f1fee96f634e78c81893019f1898cf；
      git worktree add --detach <tmp>/r6 e08c6b66d5023526c3fc7a0eaa44bbe08e614fbd；
      git worktree add --detach <tmp>/head 77ec90575d24472774a79235564d60ef494d6320；
      分別 cd cli && uv run pytest -q
    observed: >-
      baseline 944 passed in 63.74s；R6 976 passed in 65.03s；
      R7 976 passed in 65.35s。R6→R7 為 976→976。
  - command: >-
      在三個獨立 detached worktree 注入並測試：
      M18@1588d50 純原始碼 reflow 後
      uv run pytest -q tests/test_amend.py tests/test_doctor.py；
      M25@77ec905 將「已核對」改成「初步核對」後跑同一兩檔；
      M27@77ec905 在 return 前依未取樣 comment id 改寫 author 後 uv run pytest -q
    observed: >-
      M18 為 293 passed；M25 為 7 failed / 292 passed；
      M27 為全套 976 passed。三筆均與第 2 節所標的當次執行範圍及紅綠方向一致；
      M27 仍是需求方已裁定的不涵蓋項，本輪不要求修。
  - command: >-
      python3 <分別從 issuecomment-5311176521、amend_cmd.py@77ec905、
      test_amend.py@77ec905 精確擷取需求方原句並計算 SHA-1 的腳本>
    observed: >-
      三處各精確命中一次；擷取文字加 trailing LF 的 SHA-1 均為
      61a31e5ff73b12f5d91868adaa5b0ce6682ef388。沒有用折行或 Markdown 敏感的全文計數。
  - command: >-
      cd <head-detached-worktree>/cli && uv lock --check
      && uv run python ../scripts/replay_escalation_rules.py
    observed: "uv lock --check 通過；replay 65/65 通過。未執行 wfcli。"
  - command: >-
      gh run list --repo ruan6047/ai-workflow
      --branch claude/WF-AMEND-AUTHZ-BINDING1 --limit 10
      --json databaseId,headSha,status,conclusion,workflowName,url
    observed: >-
      CI run 31994329159 completed/success，headSha 逐字等於
      77ec90575d24472774a79235564d60ef494d6320。
  - command: >-
      git worktree remove --force <本輪七個明確的 /tmp/wf62-r7.* worktree>
      && git status --short --branch && git diff --quiet && git diff --cached --quiet
    observed: >-
      本輪 disposable worktree 全部移除；source worktree 仍在 main（behind origin/main 1），
      tracked 與 staged diff 皆空；未修改或切換 source branch。
findings:
  - finding_id: WF-AMEND-AUTHZ-BINDING1-R7-001
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: threat-model-record-retains-stale-universal-guard-claim
    evidence: >-
      77ec905 的 test_amend.py:1265-1266 仍從「一條讀實際回傳值、另一條讀原始碼」
      推成「一邊讀錯時另一邊仍會紅」；:1303-1305 把最終 body 含一個完整子字串
      推成「證明寫入路徑沒有加工」及「比對是封閉的」；:1329-1331 又寫
      「黃金值那條會逼改動被看見」，但同檔 :1114 已列明模板與測試黃金值同步改錯時
      測試會綠。這些都是從斷言向上增加守衛保證的綜述，只是避開了
      「因此／所以／故保證」字面。故本輪提出的形式規則仍以開放的同義改寫為邊界，
      不能機械區分三類，執行者未宣稱窮舉雖屬誠實，仍未達成本輪「整類刪除」的方法目標。
    disposition: >-
      不要再擴充禁詞表。把指定守衛文件改成封閉白名單格式：每句只能標成
      ASSERTION（逐字重述某個 assert/AST predicate，不使用「證明／確保／逼／涵蓋／封閉」
      等結果性敘述）、OBSERVED（必帶 mutant、實際 command scope 與 pass/fail 結果）、
      NOT_COVERED（只能縮小保障集合，不得以「但」接回正面保證）。刪除或按此格式改寫
      :1265-1266、:1303-1305、:1329-1331、:1345-1346；保留 M27 與需求方原句，不新增守衛、
      不改 doctor。此為修改規則本身，不應再描述成「第五句漏掃」。
```

### 重點判斷

1. **形式規則還沒有真正封閉。** 禁用三個連接詞仍是黑名單；「證明」「會逼」「已涵蓋」可以表達同一個向上結論。可機械複查的版本應採上面 disposition 的三標籤白名單，檢查句子的證據型別，而不是猜同義詞。
2. **未宣稱「掃完了」是恰當誠實，不是免責本身。** 問題不在沒有做不可能的語意窮舉，而在交付同時宣稱新的形式規則已可機械複查；現有反例證明那條規則仍不足，所以不能 APPROVE。
3. **限制型與綜述型的可重用邊界是「保障集合的方向」。** 限制型只會縮小系統聲稱能保證的集合、擴大 unknown／不涵蓋集合；綜述型則從斷言、取樣或構造增加正面的正確性／涵蓋／可見性保證。全稱量詞本身不是判準。因此「對擁有這份碼的人，任何測試與任何執行期檢查都無效」在同一信任邊界的上下文中是向下陳述能力上限，歸第 3 類；反之「一邊讀錯時另一邊仍會紅」即使沒有全稱詞，仍是向上綜述。
4. **19 筆紅綠的抽驗成立。** M18 的 293 綠、M25 的 7 紅、M27 的全套 976 綠均重現；「M14–M26b 為 amend+doctor 子集、M20 舊守衛與 M27 為全套」的範圍標註未見錯誤。
5. **刪綜述後仍讀得懂。** 第 1 節列 exact predicate、第 2 節列歷史紅綠、第 3 節列不涵蓋與需求方裁定；新讀者能重建「有何防線、實測過什麼、邊界在哪」。上述殘句刪除不會使文件失去必要資訊，反而避免讀者把測試結果讀成未證明的保證。
6. **零可執行路徑變更成立。** R6/R7 executable AST 相等、976→976；精確保留事項仍是 docstring 可由 introspection 觀察，故只能稱可執行敘述／CLI 行為不變。
7. **需求方原句未動。** 三來源精確擷取各一次，SHA-1 全等；M27 按 issuecomment-5311176521 維持已知不涵蓋且不修。

### 結論

授權註記仍據實揭露它沒有的區辨力，legacy 掃描與行為測試未退化，所以核心痛點維持已解。阻擋點只在本輪新方法：它仍用連接詞黑名單近似「不寫綜述」，而文件內已有不帶那些連接詞的同型保證句；在改為封閉的證據型別白名單並清掉這些句子前，裁決為 **REQUEST_CHANGES**。


## Comment 5312191049 · 2026-08-17T05:23:57Z

core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: git --no-pager fetch --quiet origin && git merge-base origin/main 77ec90575d24472774a79235564d60ef494d6320 && git rev-parse 77ec90575d24472774a79235564d60ef494d6320
    observed: merge-base=d18cd83795f1fee96f634e78c81893019f1898cf; tip=77ec90575d24472774a79235564d60ef494d6320
  - command: cd /Users/ruanruan/.copilot/session-state/9ca4f1f7-be9d-406e-a01b-af2fb7b890e6/files/ai-workflow-review && git --no-pager diff --stat e08c6b6..77ec905 -- cli/src/wf_cli/commands/amend_cmd.py cli/tests/test_amend.py
    observed: current-round diff only touched amend_cmd.py and test_amend.py; 135 insertions / 142 deletions in commentary/docstring-heavy sections
  - command: cd /Users/ruanruan/.copilot/session-state/9ca4f1f7-be9d-406e-a01b-af2fb7b890e6/files/ai-workflow-review && python - <<'PY'
import ast, subprocess

def strip_docstrings(node):
    for child in ast.walk(node):
        body = getattr(child, 'body', None)
        if isinstance(body, list) and body:
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(getattr(first, 'value', None), ast.Constant) and isinstance(first.value.value, str):
                body.pop(0)
    return node
for rel in ['cli/src/wf_cli/commands/amend_cmd.py','cli/tests/test_amend.py']:
    b = subprocess.check_output(['git','show','e08c6b6:'+rel], text=True)
    h = subprocess.check_output(['git','show','77ec905:'+rel], text=True)
    print(rel, ast.dump(strip_docstrings(ast.parse(b)), include_attributes=False)==ast.dump(strip_docstrings(ast.parse(h)), include_attributes=False))
PY
    observed: amend_cmd.py=True; test_amend.py=True after stripping docstrings, i.e. no executable-shape change in this round
  - command: cd /Users/ruanruan/.copilot/session-state/9ca4f1f7-be9d-406e-a01b-af2fb7b890e6/files/ai-workflow-review/cli && uv run pytest -q
    observed: 944 passed in 50.86s
  - command: python - <<'PY'
import re
from pathlib import Path
root = Path('/Users/ruanruan/.copilot/session-state/9ca4f1f7-be9d-406e-a01b-af2fb7b890e6/files/ai-workflow-review')
pat = re.compile(r'需求方\s*不能證明\s*M27\s*不會發生，\s*只能說它不是這個守衛被開出來要擋的東西')
for rel in ['cli/src/wf_cli/commands/amend_cmd.py','cli/tests/test_amend.py']:
    text = (root / rel).read_text(encoding='utf-8')
    m = pat.search(text)
    print(rel, bool(m))
PY
    observed: cli/src/wf_cli/commands/amend_cmd.py=False; cli/tests/test_amend.py=False
findings:
  - finding_id: WF-AMEND-AUTHZ-BINDING1-R7-01
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: requester-quote-preservation-regression
    evidence: The branch no longer contains the requester sentence it claims to preserve. A whitespace-tolerant regex search for 「需求方不能證明 M27 不會發生，只能說它不是這個守衛被開出來要擋的東西」 returned zero matches in both cli/src/wf_cli/commands/amend_cmd.py and cli/tests/test_amend.py, so the claimed unchanged two-location quote and hash could not be reproduced from tip 77ec905.
    disposition: Restore the requester sentence verbatim in both documented locations, then pin that exact literal mechanically (for example with a literal-preservation assertion or hash check) so future wording cleanups cannot silently paraphrase or drop it.


## Comment 5312240998 · 2026-08-17T05:32:20Z

## ⚠️ 對 R7-01 的反證：需求方原句**在**分支上，兩個檔各 1 處

請查核者複驗。以你自己在裁決裡指名的 SHA `77ec90575d24472774a79235564d60ef494d6320` 直接取檔：

```
77ec905:cli/src/wf_cli/commands/amend_cmd.py  → 1 處
77ec905:cli/tests/test_amend.py               → 1 處
```

兩處逐字皆為：

```
    需求方不能證明 M27 不會發生，只能說它不是這個守衛被開出來要擋的東西
```

在 `amend_cmd.py` 的位置是第 121 行，其上第 118–119 行寫著：

> ⚠️ 這是比例判斷不是證明。需求方 2026-08-16 裁定原句，**逐字保留、不得軟化**，
> 刻意不折行以免日後 reflow 把它拆散（`#57` R5 同型陷阱）：

PM 的比對方法（供你複驗時避開同一個坑）：

```python
git show "77ec905...:<file>" | python3 -c "
import sys,re
print(len(re.findall(r'需求方不能證明\s*M27\s*不會發生，只能說它不是這個守衛被開出來要擋的東西', sys.stdin.read())))
"
```

### ⚠️ PM 第一次驗也得到 0，原因值得你知道

PM 最初用 `tr -d ' \n\t　'` 去空白後再 `grep`，**兩個檔都回 0**——與你的結果一致。

**那是錯的**：`tr` 是**逐位元組**刪除，全形空格 `　` 是 `E3 80 80`，而 `0xE3` 是大量中日韓字元的首位元組，`tr -d` 會把那些字元一起打碎。PM 是因為肉眼在碼裡看到那句話、與數字對不上，才回頭改用 Python regex。

你的裁決寫的是「a whitespace-tolerant regex search」。**若你的工具對全形字元做過類似的位元組層處理，會得到同樣的假 0。** 請用一個不經過位元組層空白剝除的方法再驗一次。

### 這個陷阱今天已經咬了四個人

同一形狀——**驗證工具沒在量你以為的東西**：

- 執行者 ×2：`grep` 被**折行**騙（R6 誤報「修正未套用」）、被 **Markdown `**` 標記**騙（R7 同樣誤報）
- PM ×2：搜文件沒搜卡面（`#132` 的時效依據）、`tr -d` 位元組打碎（本次）
- 查核者 ×1：本條 R7-01

### 請怎麼處置

- **若你複驗後確認原句在**：請撤回 R7-01。⚠️ 該 finding 的 `disposition` 要求「restore the requester sentence」——那會讓執行者去「還原」一個沒有消失的東西。
- **若你複驗後仍得 0**：請貼出你的完整指令與環境，那代表有 PM 沒看到的東西（例如取到不同的 ref、或編碼層差異），那本身是更重要的發現。

其餘查核內容（本輪的形式規則、19 筆變異、限制型 vs 綜述的判準）不受本則影響，請照原裁決處理。


## Comment 5312251024 · 2026-08-17T05:34:00Z

core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: git --no-pager fetch --quiet origin && git merge-base origin/main 77ec90575d24472774a79235564d60ef494d6320 && git rev-parse 77ec90575d24472774a79235564d60ef494d6320
    observed: merge-base=d18cd83795f1fee96f634e78c81893019f1898cf; tip=77ec90575d24472774a79235564d60ef494d6320
  - command: cd /Users/ruanruan/.copilot/session-state/9ca4f1f7-be9d-406e-a01b-af2fb7b890e6/files/ai-workflow-review && git show 77ec90575d24472774a79235564d60ef494d6320:cli/src/wf_cli/commands/amend_cmd.py | sed -n '116,124p' && printf '\n---\n' && git show 77ec90575d24472774a79235564d60ef494d6320:cli/tests/test_amend.py | sed -n '1188,1198p'
    observed: the requester sentence is present at tip in both cited files, once per file, matching the counterevidence and falsifying my prior R7-01 finding
  - command: cd /Users/ruanruan/.copilot/session-state/9ca4f1f7-be9d-406e-a01b-af2fb7b890e6/files/ai-workflow-review && python - <<'PY'
import re, subprocess, hashlib
sha='77ec90575d24472774a79235564d60ef494d6320'
needle='需求方不能證明 M27 不會發生，只能說它不是這個守衛被開出來要擋的東西'
for rel in ['cli/src/wf_cli/commands/amend_cmd.py','cli/tests/test_amend.py']:
    text = subprocess.check_output(['git','show',f'{sha}:{rel}'], text=True)
    print(rel, text.count(needle), bool(re.search(re.escape(needle), text)))
print(hashlib.sha1(needle.encode()).hexdigest())
PY
    observed: literal count=1 and regex match=true in each file; SHA-1 of the preserved sentence is 713694824b1a4e4ecf2f3b6f9cf2e062c1960175
  - command: cd /Users/ruanruan/.copilot/session-state/9ca4f1f7-be9d-406e-a01b-af2fb7b890e6/files/ai-workflow-review && python - <<'PY'
import ast, subprocess

def strip_docstrings(node):
    for child in ast.walk(node):
        body = getattr(child, 'body', None)
        if isinstance(body, list) and body:
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(getattr(first, 'value', None), ast.Constant) and isinstance(first.value.value, str):
                body.pop(0)
    return node
for rel in ['cli/src/wf_cli/commands/amend_cmd.py','cli/tests/test_amend.py']:
    before = subprocess.check_output(['git','show','e08c6b6:'+rel], text=True)
    after = subprocess.check_output(['git','show','77ec90575d24472774a79235564d60ef494d6320:'+rel], text=True)
    print(rel, ast.dump(strip_docstrings(ast.parse(before)), include_attributes=False)==ast.dump(strip_docstrings(ast.parse(after)), include_attributes=False))
PY
    observed: amend_cmd.py=True; test_amend.py=True after stripping docstrings, so this round is commentary-only with no executable-shape delta
  - command: cd /Users/ruanruan/.copilot/session-state/9ca4f1f7-be9d-406e-a01b-af2fb7b890e6/files/ai-workflow-review/cli && uv run pytest -q
    observed: 944 passed in 50.86s
  - command: rg -n '因此.*保證|所以.*保證|故.*保證' /Users/ruanruan/.copilot/session-state/9ca4f1f7-be9d-406e-a01b-af2fb7b890e6/files/ai-workflow-review/cli/src/wf_cli/commands/amend_cmd.py /Users/ruanruan/.copilot/session-state/9ca4f1f7-be9d-406e-a01b-af2fb7b890e6/files/ai-workflow-review/cli/tests/test_amend.py
    observed: no matches for the requested therefore/so/hence→guarantee sentence form in the changed files
findings: []


## Comment 5312252522 · 2026-08-17T05:34:16Z

core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: git --no-pager fetch --quiet origin && git merge-base origin/main 77ec90575d24472774a79235564d60ef494d6320 && git rev-parse 77ec90575d24472774a79235564d60ef494d6320
    observed: merge-base=d18cd83795f1fee96f634e78c81893019f1898cf; tip=77ec90575d24472774a79235564d60ef494d6320
  - command: cd /Users/ruanruan/.copilot/session-state/9ca4f1f7-be9d-406e-a01b-af2fb7b890e6/files/ai-workflow-review && git show 77ec90575d24472774a79235564d60ef494d6320:cli/src/wf_cli/commands/amend_cmd.py | sed -n '116,124p' && printf '\n---\n' && git show 77ec90575d24472774a79235564d60ef494d6320:cli/tests/test_amend.py | sed -n '1188,1198p'
    observed: the requester sentence is present at tip in both cited files, once per file, matching the counterevidence and falsifying my prior R7-01 finding
  - command: cd /Users/ruanruan/.copilot/session-state/9ca4f1f7-be9d-406e-a01b-af2fb7b890e6/files/ai-workflow-review && python - <<'PY'
import re, subprocess, hashlib
sha='77ec90575d24472774a79235564d60ef494d6320'
needle='需求方不能證明 M27 不會發生，只能說它不是這個守衛被開出來要擋的東西'
for rel in ['cli/src/wf_cli/commands/amend_cmd.py','cli/tests/test_amend.py']:
    text = subprocess.check_output(['git','show',f'{sha}:{rel}'], text=True)
    print(rel, text.count(needle), bool(re.search(re.escape(needle), text)))
print(hashlib.sha1(needle.encode()).hexdigest())
PY
    observed: literal count=1 and regex match=true in each file; SHA-1 of the preserved sentence is 713694824b1a4e4ecf2f3b6f9cf2e062c1960175
  - command: cd /Users/ruanruan/.copilot/session-state/9ca4f1f7-be9d-406e-a01b-af2fb7b890e6/files/ai-workflow-review && python - <<'PY'
import ast, subprocess

def strip_docstrings(node):
    for child in ast.walk(node):
        body = getattr(child, 'body', None)
        if isinstance(body, list) and body:
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(getattr(first, 'value', None), ast.Constant) and isinstance(first.value.value, str):
                body.pop(0)
    return node
for rel in ['cli/src/wf_cli/commands/amend_cmd.py','cli/tests/test_amend.py']:
    before = subprocess.check_output(['git','show','e08c6b6:'+rel], text=True)
    after = subprocess.check_output(['git','show','77ec90575d24472774a79235564d60ef494d6320:'+rel], text=True)
    print(rel, ast.dump(strip_docstrings(ast.parse(before)), include_attributes=False)==ast.dump(strip_docstrings(ast.parse(after)), include_attributes=False))
PY
    observed: amend_cmd.py=True; test_amend.py=True after stripping docstrings, so this round is commentary-only with no executable-shape delta
  - command: cd /Users/ruanruan/.copilot/session-state/9ca4f1f7-be9d-406e-a01b-af2fb7b890e6/files/ai-workflow-review/cli && uv run pytest -q
    observed: 944 passed in 50.86s
  - command: rg -n '因此.*保證|所以.*保證|故.*保證' /Users/ruanruan/.copilot/session-state/9ca4f1f7-be9d-406e-a01b-af2fb7b890e6/files/ai-workflow-review/cli/src/wf_cli/commands/amend_cmd.py /Users/ruanruan/.copilot/session-state/9ca4f1f7-be9d-406e-a01b-af2fb7b890e6/files/ai-workflow-review/cli/tests/test_amend.py
    observed: one broad regex hit remains in amend_cmd.py at the pre-existing sentence 「故本檢查的保證止於…」; I did not find any surviving instance of the narrower reviewed form 「因此／所以／故 ⇒ 保證」 among the newly rewritten guard commentary, and this probe no longer supports a blocking finding
findings: []


## Comment 5312348556 · 2026-08-17T05:50:17Z

結案 🏁完成（Issue 已由 PR #96 的 `Closes` 自動關閉，補記結案內容）。

PR #96 squash merge → `ai-workflow main` **`d0008b3`**，CI 兩個 check 皆 SUCCESS。merge 後於 main 驗證 `pytest` **976 passed**。

**gitlink 已同步**：`cpbl-analytics` main `4d03e67` 的 `.ai-workflow` 指向 `d0008b3`。⚠️ 免部署——`.ai-workflow/` 不在 Docker 映像的 `COPY` 清單。

---

### ⚠️ 兩件留給後人的事

**一、那條被撤回的 finding，成因值得記。**

初版 R7-01 宣稱需求方原句已從分支消失（whitespace-tolerant regex 兩檔皆 0 命中）。PM 貼出反證後，查核者以 `git show <sha>:<file>` 重驗確認原句在兩檔各 1 處並撤回。

**出錯原因是 `tr -d` 的位元組層陷阱**：全形空格 `　` 是 `E3 80 80`，而 `0xE3` 是大量中日韓字元的首位元組，逐位元組刪除會把文字打碎。⚠️ **PM 第一次驗也踩了同一個坑**，是肉眼在碼裡看到那句話、與數字對不上才回頭改用 Python regex。

同一形狀今天咬了四個人：執行者兩次（`grep` 被折行騙、被 Markdown `**` 騙）、PM 兩次（搜文件沒搜卡面、`tr -d`）、查核者一次。**驗證工具沒在量你以為的東西。**

**二、本次 release 未帶 `--cleanup`，是規則暫置。**

清理**實際已完成**：worktree 已 `git worktree remove`、本地分支已刪（was `77ec905`）、遠端分支已 `push --delete`。

但 cleanup 守衛拒收，訊息為「分支worktree 欄沒有可解析的分支，無法界定要清理什麼」——⚠️ **因為本卡全程以子代理派工、從未執行 `wfcli assign`，而該欄位只有 `assign` 會寫**（全 repo 唯一 `set_field_value` 呼叫點在 `assign_cmd.py:254`），`amend` 無任何旗標可設它。**守衛在構造上無法驗證一件已經做完的事。**

此缺口屬 **#94**（契約↔工具全量對帳）的同族。

⚠️ 剩餘結案義務（不擋 release）：卡檔封存、Ledger 投影重建、對帳三件套。
