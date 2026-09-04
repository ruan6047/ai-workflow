# #35 WF-EVENT-MARKER-V2-SCOPE1 lifecycle 事件的 marker 覆蓋與版本升級：v1 鍵集合封閉，且六個動詞裡只有 review 有 marker
- state: closed  created: 2026-08-12T00:15:55Z  closed: 2026-08-17T13:12:53Z
- url: https://github.com/ruan6047/ai-workflow/issues/35
- comments: 7

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；契約本體設計，須逐條對照三張卡的具名相依並論證升版相容策略；推理鏈長但無需前沿能力）　查核：跨家族查核（契約本體，須走 PR）（建議 主力型；紅線卡須跨模型家族；查核重點在升版策略是否會使既有卡停機、以及三項相依是否真被承載而非以通用擴充點含混帶過）
- Initiative：—　spec 基線：自 2026-08-12 的 PM 跨卡對帳 X3 切出。三個具名相依：(1) WF-ESCALATION-DEFERRED-FINDINGS1 於 539c333 需派審事件帶 review_prompt_url 與 closure_reporting_requested；(2) 同卡於 8d27bed 的 (b′-1) 需裁定事件帶被收窄的 attempt_id 與 finding_id 集合；(3) WF-EVENT-IDEMPOTENCY1 於 e19be58 需 event_id 的載荷格式與回讀契約（其 §12 已把最小必要性質釘為 P1–P5：可枚舉／唯一歸屬／位元組穩定／不觸發既有隔離／可與 payload 分離）。硬約束由 #23 讀碼查出並經 PM 複驗：doctor.py 的 _CONFORMANT_MARKER_RE 鍵集合封閉，handoff-contract.md §3.1.3 明文「要擴充欄位必須升版本」。
- DB：db_scope=none
- 服務的原始目標：讓「事件要帶什麼結構化事實」這件事有一條可走的路，而不是每張卡各自宣告依賴後 fail-closed 等待。

## 簡介
<!-- card-brief:begin -->
裁定 lifecycle 事件 marker 要不要升 v2 與其相容策略（既有 v1 事件怎麼辦、cutover 如何不讓整批卡停機），裁定 open／assign／amend／handoff／deploy-declare／deploy-state 這六個今天完全不發 marker 的動詞要不要有識別符，並在 `templates/handoff-contract.md` 立下文字格式的三條設計規則。**適用時機**：某張卡要在 lifecycle 事件上帶新的結構化欄位，而 `doctor.py` 的 `_CONFORMANT_MARKER_RE` 因鍵集合封閉把整張卡隔離時；或要新增自訂文字格式時。⛔ 非射程：⛔ 不實作三張下游卡本身——WF-ESCALATION-DEFERRED-FINDINGS1 的事件欄位、WF-EVENT-IDEMPOTENCY1 的 `event_id` 回讀契約只作為承載力的構造案例；⛔ 不收窄受管轄判準，那是 WF-MARKER-SCOPE-CLEARANCE1。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：三張卡各自需要在 lifecycle 事件上帶結構化欄位，全部撞上同一堵牆：doctor 的 _CONFORMANT_MARKER_RE 把「順序固定、單一空白分隔、鍵集合封閉」編進同一條 regex，多一鍵即不匹配、整張卡停機；而六個承接動詞裡只有 review 會發出 marker（review.py:458），其餘五個根本沒有可搭載的識別符。三項相依因此不是各缺一個欄位，是共同缺一次版本升級與五個動詞的 marker 從無到有——而目前無卡承接。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:docs/WF_EVENT_MARKER_V2.md",
    "file:templates/handoff-contract.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 裁定 v1 是否升 v2，以及升版的相容策略：v1 與 v2 並存期間 doctor 的判定規則、既有 v1 事件是否需要遷移、cutover 如何避免整批卡停機。不得以「新事件用 v2」帶過而不說既有 v1 事件怎麼辦。
- [ ] 裁定另外五個動詞（open／assign／amend／handoff／deploy-declare／deploy-state）是否都需要 marker，或哪些不需要及理由。不需要也是合法結論，但須說明那些動詞的事件如何被唯一識別。
- [ ] 三項具名相依逐一對照：新 schema 是否足以承載，不足者明列。不得只設計一個通用擴充點就宣稱三者皆已解決。
- [ ] 與 WF-MARKER-SCOPE-CLEARANCE1（#30）的介面明確：#30 新增 clearance marker 型別並收窄受管轄判準，本卡改的是既有 event marker 的鍵集合與覆蓋面。兩者都動 doctor 的 marker 解析，須說明先後順序與共存規則。
- [ ] （2026-08-12 追加）本卡須在 templates/handoff-contract.md 立下「文字格式的設計規則」，並讓 v2 自身成為第一個遵守它的實例。規則三條：(1) 保留字元清單——任何新格式須明列哪些字元承擔結構（分隔、界定、跳脫），並宣告它們不得出現在值裡；(2) 寫入端拒收——產生該格式的動詞必須在寫入時拒收含保留字元的值，不得靜默寫出一個自己讀不回的字串；(3) 讀寫往返測試——寫得出的，解析器必須讀得回，語料須含真實使用過的值。
- [ ] （2026-08-12 追加）該規則不得只寫成散文期許。須逐一指名它今天約束的三個消費者：本卡的 marker v2 鍵集合、WF-MARKER-SCOPE-CLEARANCE1（#30）的 clearance marker 表示法、WF-ESCALATION-CHECKPOINT-WRITER1（#9）的 checkpoint payload。三者若有任一無法遵守，須說明是規則過嚴還是該格式有問題，不得略過。

## 驗證

- [ ] 以真實 timeline 的既有 v1 事件重放，證明升版策略不會使任何既有卡由 recorded 變成 marker_quarantined。
- [ ] 三項具名相依各以一個構造案例證明新 schema 承載得了；承載不了者明列為未解決，不得靜默略過。
- [ ] 鍵集合擴充後的解析器，須以窮舉或性質測試證明「多一鍵／少一鍵／錯序」的判定不退化為寬鬆。
- [ ] （2026-08-12 追加）v2 自身須通過它所立的三條規則：保留字元清單逐字寫出、marker 產生端對含保留字元的值拒收、往返測試以真實事件語料跑過。往返測試須為機械的——不需要人判斷格式寫得夠不夠清楚，跑一次就知道。
## Log

- 2026-08-12T08:15:53+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-12T10:35:23+08:00 amend by wf-cli（op c14b79e7）→ 驗收條件：原值「[ ] 裁定 v1 是否升 v2，以及升版的相容策略：v1 與 v2 並存期間 doctor 的判定規則、既有 v1 事件是否需要遷移、cutover 如何避免整批卡停機。不得以「新事件用 v2」帶過而不說既有 v1 事件怎麼辦。；[ ] 裁定另外五個動詞（open／assign／amend／handoff／deploy-declare／deploy-state）是否都需要 marker，或哪些不需要及理由。不需要也是合法結論，但須說明那些動詞的事件如何被唯一識別。；[ ] 三項具名相依逐一對照：新 schema 是否足以承載，不足者明列。不得只設計一個通用擴充點就宣稱三者皆已解決。；[ ] 與 WF-MARKER-SCOPE-CLEARANCE1（#30）的介面明確：#30 新增 clearance marker 型別並收窄受管轄判準，本卡改的是既有 event marker 的鍵集合與覆蓋面。兩者都動 doctor 的 marker 解析，須說明先後順序與共存規則。」→ 新值「裁定 v1 是否升 v2，以及升版的相容策略：v1 與 v2 並存期間 doctor 的判定規則、既有 v1 事件是否需要遷移、cutover 如何避免整批卡停機。不得以「新事件用 v2」帶過而不說既有 v1 事件怎麼辦。；裁定另外五個動詞（open／assign／amend／handoff／deploy-declare／deploy-state）是否都需要 marker，或哪些不需要及理由。不需要也是合法結論，但須說明那些動詞的事件如何被唯一識別。；三項具名相依逐一對照：新 schema 是否足以承載，不足者明列。不得只設計一個通用擴充點就宣稱三者皆已解決。；與 WF-MARKER-SCOPE-CLEARANCE1（#30）的介面明確：#30 新增 clearance marker 型別並收窄受管轄判準，本卡改的是既有 event marker 的鍵集合與覆蓋面。兩者都動 doctor 的 marker 解析，須說明先後順序與共存規則。；（2026-08-12 追加）本卡須在 templates/handoff-contract.md 立下「文字格式的設計規則」，並讓 v2 自身成為第一個遵守它的實例。規則三條：(1) 保留字元清單——任何新格式須明列哪些字元承擔結構（分隔、界定、跳脫），並宣告它們不得出現在值裡；(2) 寫入端拒收——產生該格式的動詞必須在寫入時拒收含保留字元的值，不得靜默寫出一個自己讀不回的字串；(3) 讀寫往返測試——寫得出的，解析器必須讀得回，語料須含真實使用過的值。；（2026-08-12 追加）該規則不得只寫成散文期許。須逐一指名它今天約束的三個消費者：本卡的 marker v2 鍵集合、WF-MARKER-SCOPE-CLEARANCE1（#30）的 clearance marker 表示法、WF-ESCALATION-CHECKPOINT-WRITER1（#9）的 checkpoint payload。三者若有任一無法遵守，須說明是規則過嚴還是該格式有問題，不得略過。」；理由 需求方 2026-08-12 指示「amend #35 把這條納進去」。背景：需求方問「是不是在設計文件時就規定包含符號跟格式，驗收生成時就比較不容易出現格式錯誤」。PM 查證後的答案是——格式其實已經規定了：templates/tasks-card.md:4 逐字寫出路由行的分隔符，但從未宣告那些字元是保留字，而 open 對名字沒有任何格式檢查，於是寫得出一個 card.py:534 的正則讀不回的值（#21 的往返缺陷，已納入 #37 修）。缺的不是文件詳盡度，是「宣告保留字元」＋「寫入端拒收」＋「往返測試」。本卡是承接處的理由：它正在設計新的 marker 文法、持有 handoff-contract.md（marker 語法的家）、且尚未開工，現在加零成本；而接下來 #30 與 #9 各要再設計一個新格式，若不現在立規則，三個月後會有三套各自帶歧義的文法且互相引用。。
- 2026-08-12T10:35:23+08:00 amend by wf-cli（op c14b79e7）→ 驗證：原值「[ ] 以真實 timeline 的既有 v1 事件重放，證明升版策略不會使任何既有卡由 recorded 變成 marker_quarantined。；[ ] 三項具名相依各以一個構造案例證明新 schema 承載得了；承載不了者明列為未解決，不得靜默略過。；[ ] 鍵集合擴充後的解析器，須以窮舉或性質測試證明「多一鍵／少一鍵／錯序」的判定不退化為寬鬆。」→ 新值「以真實 timeline 的既有 v1 事件重放，證明升版策略不會使任何既有卡由 recorded 變成 marker_quarantined。；三項具名相依各以一個構造案例證明新 schema 承載得了；承載不了者明列為未解決，不得靜默略過。；鍵集合擴充後的解析器，須以窮舉或性質測試證明「多一鍵／少一鍵／錯序」的判定不退化為寬鬆。；（2026-08-12 追加）v2 自身須通過它所立的三條規則：保留字元清單逐字寫出、marker 產生端對含保留字元的值拒收、往返測試以真實事件語料跑過。往返測試須為機械的——不需要人判斷格式寫得夠不夠清楚，跑一次就知道。」；理由 需求方 2026-08-12 指示「amend #35 把這條納進去」。背景：需求方問「是不是在設計文件時就規定包含符號跟格式，驗收生成時就比較不容易出現格式錯誤」。PM 查證後的答案是——格式其實已經規定了：templates/tasks-card.md:4 逐字寫出路由行的分隔符，但從未宣告那些字元是保留字，而 open 對名字沒有任何格式檢查，於是寫得出一個 card.py:534 的正則讀不回的值（#21 的往返缺陷，已納入 #37 修）。缺的不是文件詳盡度，是「宣告保留字元」＋「寫入端拒收」＋「往返測試」。本卡是承接處的理由：它正在設計新的 marker 文法、持有 handoff-contract.md（marker 語法的家）、且尚未開工，現在加零成本；而接下來 #30 與 #9 各要再設計一個新格式，若不現在立規則，三個月後會有三套各自帶歧義的文法且互相引用。。
- 2026-08-12T13:33:33+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code 子agent；分支worktree claude/WF-EVENT-MARKER-V2-SCOPE1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-marker-v2-scope1；交付狀態 🚧進行中；實際能力層級 主力型（卡面建議無法解析：候選路由行不符合 templates/tasks-card.md 第 4 行格式（如全形／半形空白錯置、缺分號或括號、理由為空、查核段缺失、混入零寬字元）；理由：非偏離：實際層級 主力型 與卡面建議 主力型 相符，但基線不可解析故無法機械比對。根因是本卡開立時 PM 把含全形括號的名字寫進路由行的執行者欄，而 card.py 的 _ROUTING_PARSE_RE 在第一個全形右括號就斷。該缺陷已由 WF-CARD-FIELD-CORRECTION1（#37）於 d232fae 修好並併入 main（20f2ea3），但寫入端拒收只防新的、不追溯修既有的；需求方 2026-08-12 裁定本卡與 #37 自身的陳舊路由行不修、記錄即可（留痕 issuecomment-5261934855，理由段經 issuecomment-5262064584 更正）。執行者刻意不把它們放行成 matched——那會讓一個從未解析成功的建議冒充「比對過且相符」。）。
- 2026-08-12T16:16:12+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA d44ec710cf5b58bef19a0316668310bee1ed0364；證據 R1：升 v2，v1 永久有效且不得遷移。v2 只加兩鍵（event 封閉語彙選定其餘鍵集合、event_id），選取判準是「不解析 payload 就必須知道」（後者是 #23 的 P5）。其餘語意欄位一律進 payload——這是對核心痛點的實質回答：牆的成因不是 v1 少幾個欄位，是識別符與語意欄位擠在同一個封閉鍵集合裡，分開後往後加欄位不再需要升版本。既有 49 則 v1 不遷移，三個理由任一即足夠：契約 §3.1.4 自己禁止回寫既有事件；批次編輯會讓全部歷史事件帶上平台 edited 標記、污染 clearance 與 (b′) 賴以判斷有無事後改寫的訊號；且無收益。

判定拆成兩階段且互不知道對方：階段一（受管轄判定）只看前綴位置不看版本——那是 #30 的射程，本卡一字不動；階段二（版本分派）只看版本與鍵不看行的位置。執行者明說這個切分是本卡能與 #30 並行不打架的唯一理由。cutover 順序釘死為讀取器先行且宣告為硬需求非最佳實務：探針 D8 拿現行 doctor 本人對一則合格 v2 marker 實跑，證明第一則 v2 事件會讓未升級的消費者當場停掉那張卡。

六個動詞（卡面寫「五個」卻列了六個，執行者已更正）：open 不需要（Issue number 即識別符、一卡恰一則），其餘五個都需要，載體一律留言不是 body。否決 body 平面的理由是實證：真實 timeline 上 9 則留言因內文引用前綴而凍住 4 張卡（#15/#17/#19/#21），全部是派審詞與 PM 註記。也不新增第二個前綴字面——那正是 #9 切片 A 拒絕過一次的形態，且前綴改名對既有消費者是 fail-open（回 unobservable 而非停機）；代價是前綴名字成為誤稱，明知而付。順帶查出 amend 的 op 不是識別符（uuid4().hex[:8]，不由意圖決定）、deploy-declare/deploy-state 的留言有結構外觀但零機器錨點。

三項具名相依：派審兩欄完整承載（本卡實際貢獻是「派審事件從 body 移到留言平面」的裁定——在此之前不是欄位沒定義而是沒有載體）；event_id 的 P1–P5 五條滿足但兩處誠實殘餘（P3 只在「消費者讀 API 原始 body」前提下成立、必須寫成前提不能寫成保證；cutover 前事件無 event_id）；(b′-1) 只承載 schema、仍不可用，且發現一個前提錯誤——(b′-1) 宣稱的 append-only 在 GitHub 留言載體上不成立，wfcli 寫的留言同樣可被有寫入權者編輯，該段條文自己在下一行承認卻只算在 (b′-2) 頭上。指名歸 review-escalation.md 的持有者，未代改。

三條格式規則的機械形式：序列化成功 ⟹ 解析成功且回傳逐字相同的值。三個消費者對照——v2 鍵集合遵守（走白名單），規則一在它身上被實測修正兩次（Python 的 $ 容許結尾換行使一格恆真；字母集不涵蓋跨欄位不變量，導致 review.card_id 尾綴 - 寫得出讀不回），故加寫「寫入端接受集 ⊆ 讀取端接受集」；#30 clearance 可遵守（前提是採 §4.3 裁定用同一套文法而非另立第四套）；**#9 checkpoint payload 判為規則過嚴、該改的是規則**——原措辭把保留字元寫成唯一解會擋掉中文散文必要的逃逸策略，改為逐欄位宣告處置三選一（保留／逃逸／不適用）；修正後 #9 仍有兩格真實不合格（實測其 _yaml_scalar → _parse_yaml_subset 14 個值）：換行與連續空白被靜默摺疊，那是正規化不是逃逸，故規則二明文禁止以正規化代替拒收。附帶警告：含三反引號的值今天不破壞區塊只是因為摺疊把它拉回同一行，修掉摺疊會讓這保護一起消失。

驗證：離線 961/961、--live 1237/1237。**PM 已自行抽出重跑得 961 格全通過。** A 組與 E 組 import 現行 doctor 本人（非複製判定），比對 49 則真實 marker 與 275 則真實留言原文，判定改變 0 則；B 組 686 格往返用真實 card_id/sha/attempt_id；C 組 70 格四分類矩陣，silent-misread 與 read-rejected 零格；D 組對少一鍵/多一鍵/錯序/雙空白窮舉所有位置全拒並含正向對照。

⚠️ 執行者自陳 8 條無機械執行者，最大的是結構性的：本卡寫入集不含 cli/，所以「寫入端拒收」本卡在物理上做不到；§6 立下的規則二對本卡自己是待兌現不是已兌現，serialize_v2() 只存在於探針進程內、wfcli 六個動詞沒有一處呼叫它。#37 是同一條規則已兌現的存在證明——路走得通，本卡沒有走完它的權限。另：探針沒有 CI 跑它（一份不跑的往返測試與沒有往返測試證據強度相同）。

⚠️ 留言紀律：設計文件為規範文法必然逐字含事件 marker 前綴（3 處：語法、鍵表、構造案例），handoff-contract.md §3.1.7 標題另 1 處。**那些是 repo 檔案不是留言，doctor 掃的是留言故不隔離**（review-escalation.md 早有先例）。執行者已在檔頭加警語禁止照貼進留言。查核者引用時務必拆開書寫。

寫入集兩檔零逸出，cli/ 一行未動。。
- 2026-08-12T16:59:52+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5264405562 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=881fb511… 一次相符。本批六份收據皆採內容錨定或分隔行，各自規則不同，PM 逐份照其規則計算、無需任何格式調整）；core_pain_resolved yes；self_run 5 項；findings 0 項（blocking 0）；attempt WF-EVENT-MARKER-V2-SCOPE1-e0-d44ec710cf5b58bef19a0316668310bee1ed0364。
- 2026-08-12T17:15:11+08:00 handoff by wf-cli → owner —（結案）；iteration 0；SHA d44ec710cf5b58bef19a0316668310bee1ed0364；證據 跨家族查核判 APPROVE、core_pain_resolved=yes、findings 0。收據 issuecomment-5264405562 未編輯，PM 回讀重算 report_sha256=881fb511… 一次相符。查核者以 --live 自行重跑得 1244/1244，49 則 v1 語料與 282 則真實留言重放判定改變 0；並獨立驗證 #9 的 _yaml_scalar 對換行與連續空白未逐字往返，確認「正規化而非逃逸」判定正確。其判詞：「契約明確將 v2 寫入端與讀取器實作列為尚未實作，未把探針證據誤稱為既成生產保證。」以 PR #50 併入 main（e8a638c），PM 已於併前實測 merge 結果 658 passed、併後驗證被審 SHA 仍為祖先。未兌現項（本卡寫入集不含 cli/ 故「寫入端拒收」物理上做不到、探針無 CI 跑）已由執行者自陳並經查核者接受。。
- 2026-08-12T23:10:41+08:00 handoff by wf-cli → owner 待指派；iteration 1；SHA ba4755f4f2e33436d8128a9d68498250540f0cbb；證據 依 docs/ROADMAP.md §0／§3 降級：本卡屬目標 3（治理精緻化），非「防止低級事故」或「可稽核的內容」。需求方 2026-08-12 裁定降級為 Backlog、有餘力再做。⚠️ 降級不是關閉——本卡載有真實 finding 的紀錄，關閉會讓那些發現消失；降級可逆。。
- 2026-08-16T10:39:49+08:00 handoff by wf-cli → owner —（已結案）；iteration 0；SHA d44ec710cf5b58bef19a0316668310bee1ed0364；證據 還原終態（需求方 2026-08-16 裁定；PM 手動執行）。

【本卡於 2026-08-12 已達終態，其後被批次降級誤傷】
原始時序：review APPROVE（跨家族 GPT-5@Codex）→ handoff owner —（結案）、iteration 0 → 六小時後被 handoff ba4755f4 降回 待指派／iteration 1。本卡自此在看板上被算成待辦四天。

【誤傷的證據來自那筆降級事件自己的文字】
三張受影響卡（#35／#37／#41）的降級證據欄**逐字完全相同**，是一份批次模板，其理由為：
「⚠️ 降級不是關閉——本卡載有真實 finding 的紀錄，**關閉會讓那些發現消失**；降級可逆。」
**那句話在邏輯上不適用於這三張**：它預設「發現尚未交付、關掉就會消失」，而這三張都已 APPROVE 並結案，發現早已交付完畢。理由本身證明了批次執行時不知道它們的狀態。
佐證二：三份文字逐字相同＝模板套用而非逐卡判斷。
佐證三：降級把 iteration 由 0 改為 1，謊稱本卡回來了第二輪——而它沒有回來。

【這正是 ROADMAP 自己記下卻沒擋住的錯】
docs/ROADMAP.md:161-166 逐字寫著：「⚠️ 本表前一版把 #43 與 #24 排成序 1、2…那是錯的，它們的碼在寫這份藍圖之前就已經在 main 了。PM 憑印象排程、沒有先查狀態…**排程前先查狀態，這一條沒有機械執行者**。」
而 :207-217 的降級清單就在四十行之後，把這三張已結案的卡列進「降級為 Backlog（有餘力再做）」。**同一份文件，上面記著教訓，下面就再犯三次。**

【根因與預防】
handoff 的降級路徑不檢查現行交付狀態是否為終態，故一次批次降級可以改寫已結案的卡。cleanup.classify_state 已有 illegal_terminal_before_cleanup 的同型判定可複用。已建議加終態守衛：現行狀態落在終態集合時拒絕降級，除非帶顯式反轉旗標＋理由。

【--iteration 0 的用途】
本次以 --iteration 0 釘回原值，撤銷那筆降級造成的錯誤遞增。若不釘，帳面會顯示本卡經歷過兩輪而事實上只有一輪——iteration 是查核升級判定的輸入，錯誤的值會影響往後的 escalation 計算。

⚠️ 本則不改變本卡的技術結論：跨家族查核的 APPROVE、findings 0、以及交付 SHA 皆維持原值，本次只還原被誤傷的狀態與 iteration。

【本卡特有：一個從未在射程內的殘餘，已於還原前指名承接者】
本卡的資源宣告只有兩個設計文件（設計面）。而 handoff-contract.md §3.1（2026-08-13 bump 帶入，+195 行）正式定義了 wf-review-event:v1 的 marker 契約——三欄必填、鍵集合封閉、順序固定、三欄自洽。
實測六個動詞的 marker 命中數皆為 0：handoff_cmd.py／assign_cmd.py／deploy_declare_cmd.py／deploy_state_cmd.py／open_cmd.py／snapshot_cmd.py。只有 review 有。
**該實作面從未在本卡射程內**，故還原本卡終態不會讓它消失——但若無人承接，它會隨本卡回到終態而失去去向。
**承接者已指名：#88 WF-DISPOSITION-FIX1**（issuecomment-5305364360）。該卡 2026-08-15 amend 後的核心痛點逐字為「wfcli 的機械面與文件宣稱的能力不一致，且失效方向一律靜默」，marker 缺口正是該形狀的實例；2026-08-16 的 Backlog 重評並已把 #88 認定為該根因群組的承接者。。
- 2026-08-26T12:35:17+08:00 amend by wf-cli（op 1752096d）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:88903addbd02089091e6ae2c171c5386dcc5d50d5d2ab7acf7521b14c5a5e856 (1025 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 先導批 10 張：回填 canonical AI_WORKFLOW.md §6.3 的卡片簡介。⭐ 價值主張依卡面 A10：131 張終態卡上 assign_cmd 讓資源宣告結構性失明、root_cause_id 住在 review finding 裡，簡介是三個相關性機制裡唯一還能用的那個。⛔ 未改動任何其他欄位。A5 守衛已在呼叫前拒收 str.splitlines() 認得的全部分行字元（由該函式自身導出，非手打清單）。。
- 2026-08-26T13:16:34+08:00 amend by wf-cli（op 4e23001a）→ 簡介：原值指紋 sha256:88903addbd02089091e6ae2c171c5386dcc5d50d5d2ab7acf7521b14c5a5e856 (1025 bytes) → 新值指紋 sha256:a26e7a6f9b832c48fb74db95a9dd73c9840f8dc550a9a7de4fa9385889f8c3f3 (819 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 收斂雙居所：前一次 amend（同批先導批）body 寫入成功但 Project「簡介」欄位寫入被 GraphQL 拒為 Column value must be a valid value for text column，CLI 卻回 rc=2 宣稱未寫入任何狀態 ⇒ 卡片落入 brief.drifted 的「body 有簡介、欄位是空的」。⭐ 實測夾出病灶：該欄位上限是 UTF-8 位元組不是字元——1,012 B／524 字元寫得進、1,025 B／531 字元與 1,045 B／439 字元皆被拒。本次把簡介壓到 1,024 B 以下並保留全部具名對象，兩居所同時收斂。⛔ 未改動任何其他欄位。。


## Comment 5260396516 · 2026-08-12T00:17:02Z

## PM：本卡先不派工，開工閘門在此

本卡自 2026-08-12 的跨卡對帳 X3 開出，但**不與當前批次（#22／#23／#24／#25）並行**。理由不是資源衝突——本卡只宣告設計文件與 `templates/handoff-contract.md`，與那四張的寫入集不相交——而是**輸入尚未定稿**。

### 三個具名相依全部寫於本輪、全部未經查核

| 相依 | 出處 | 狀態 |
|---|---|---|
| 派審事件帶 `review_prompt_url`／`closure_reporting_requested` | #22 上一輪 | 該輪已被 REQUEST_CHANGES 一次 |
| 裁定事件帶被收窄的 `attempt_id`／`finding_id` 集合 | #22 `8d27bed`（本輪剛寫） | **未經查核** |
| `event_id` 的載荷格式與回讀契約（P1–P5 最小必要性質） | #23 `e19be58`（本輪剛寫） | **未經查核** |

**若那兩張的本輪交付被退，本卡的設計基礎就移動了。** 現在動工等於對著一組隨時會變的需求做契約設計。

### 這個判斷有前例，而且是今天的

- **#25**：需求方裁定「只接 release」我只寫進 checkpoint 留言與 handoff 證據，沒寫進卡面規範欄位；查核者對著卡面判 critical，完全正確。**裁定沒定稿就當前提用，會付代價。**
- **#24**：上一版把「規則 B／C 找到 #16 × #22」寫成不變量，而那是線上當下狀態；PM 的一次 `amend` 就讓它消失。執行者自己判定「與 R2-001 同族——把會變的東西當證據」。

本卡若在相依未定稿時開工，會是同一形態的第三次。

### 開工閘門（三項皆須成立）

1. **#22 與 #23 的本輪交付通過跨家族查核**（`✅通過` 或更後段），使三項相依的欄位形狀定稿；
2. 依定稿內容**逐條核對本卡 spec 基線欄所記的三項相依是否仍然逐字成立**，不成立者先更正卡面；
3. 與 [#30](https://github.com/ruan6047/ai-workflow/issues/30) 的先後順序裁定——兩者都動 `doctor` 的 marker 解析，而 #30 另被 [#25](https://github.com/ruan6047/ai-workflow/issues/25) 的 `doctor.py` 佔用擋住。

**閘門未成立前不得 `assign`。** 若有人認為某一項可以先做，請先說明它不依賴那三項相依的哪一部分。


## Comment 5264317361 · 2026-08-12T08:32:01Z

## 派審：#35 `WF-EVENT-MARKER-V2-SCOPE1` R1

⚠️ 審核對象 **`ruan6047/ai-workflow#35`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-marker-v2-scope1
分支：claude/WF-EVENT-MARKER-V2-SCOPE1　　被審 SHA：d44ec710cf5b58bef19a0316668310bee1ed0364
基線：5d22a7f3da57a3790179e999d9d28262fda4d19a（PM 已重算並驗為祖先）　　iteration：0（首輪）
寫入集：docs/WF_EVENT_MARKER_V2.md、templates/handoff-contract.md
```

> **本則為權威。** `origin/main` 現為 `02b5d9a`。**PM 已實測 merge(origin/main, 本分支) → 658 passed 全綠。**

⚠️ **本卡的設計文件為規範文法，必然逐字含事件 marker 前綴（3 處：語法、鍵表、構造案例），`handoff-contract.md` §3.1.7 標題另 1 處。那些是 repo 檔案不是留言，`doctor` 掃的是留言故不隔離**（`review-escalation.md` 早有先例）。**但你在留言裡引用時務必拆開書寫**——執行者已在檔頭加警語。

### 一、升 v2、v1 永久有效且**不得**遷移

v2 只加兩鍵（`event` 封閉語彙選定其餘鍵集合、`event_id`），選取判準是「**不解析 payload 就必須知道**」。其餘語意欄位一律進 payload——這是對核心痛點的實質回答：**牆的成因不是 v1 少幾個欄位，是識別符與語意欄位擠在同一個封閉鍵集合裡**，分開後往後加欄位不再需要升版本。

既有 49 則 v1 **不遷移**，三個理由任一即足夠：契約 §3.1.4 自己禁止回寫既有事件；批次編輯會讓全部歷史事件帶上平台 `edited` 標記、**污染 clearance 與 (b′) 賴以判斷有無事後改寫的訊號**；且無收益。

判定拆兩階段且**互不知道對方**：階段一（受管轄判定）只看前綴位置不看版本——**那是 #30 的射程，本卡一字不動**；階段二（版本分派）只看版本與鍵不看行的位置。執行者明說這個切分是本卡能與 #30 並行不打架的唯一理由。

cutover 順序釘死為**讀取器先行**且宣告為硬需求非最佳實務：探針 D8 拿**現行 `doctor` 本人**對一則合格 v2 marker 實跑，證明第一則 v2 事件會讓未升級的消費者**當場停掉那張卡**。

**請攻擊**：(a)「不遷移」的三個理由各自獨立成立嗎？(b) 兩階段互不知道對方——真的能與 #30 並行嗎，還是只是把衝突推到 #30 落地那一刻？

### 二、六個動詞（卡面寫「五個」卻列了六個，執行者已更正）

`open` **不需要**（Issue number 即識別符、一卡恰一則）；其餘五個都需要，**載體一律留言不是 body**。

否決 body 平面的理由是實證：真實 timeline 上 **9 則留言因內文引用前綴而凍住 4 張卡**（#15/#17/#19/#21），全部是派審詞與 PM 註記——**也就是會把卡面貼進留言的那一類**。把前綴寫進 body 會讓這形態從偶發變系統性。

也**不新增第二個前綴字面**：那正是 #9 切片 A 拒絕過一次的形態；且前綴改名對既有消費者是 **fail-open** 方向（舊消費者看不見新事件 → 回 `unobservable` 而非停機）。**代價是前綴名字成為誤稱，明知而付。**

順帶查出：`amend` 的 `op` **不是識別符**（`uuid4().hex[:8]`，不由意圖決定）；`deploy-declare`／`deploy-state` 的留言**有結構外觀但零機器錨點**。

### 三、三項具名相依：一項完整、一項附條件、一項只承載 schema

1. **派審兩欄 — 完整承載。** 執行者指出本卡實際貢獻的是「派審事件從 body 移到留言平面」這個裁定；**在此之前不是欄位沒定義，是沒有載體**。
2. **`event_id` 的 P1–P5 — 五條滿足，兩處誠實殘餘。** P3 **只在「消費者讀 API 原始 body」的前提下成立，必須寫成前提不能寫成保證**；cutover 前的事件沒有 `event_id`。
3. **(b′-1) — 只承載 schema、仍不可用，且它發現一個前提錯誤**：**(b′-1) 宣稱的 append-only 在 GitHub 留言載體上不成立**——`wfcli` 寫的留言同樣可被有寫入權者編輯，**該段條文自己在下一行承認這件事卻只算在 (b′-2) 頭上**。指名歸 `review-escalation.md` 的持有者（**#39**，PM 已核實），未代改。

**請判斷第 3 項那個前提錯誤是否成立**——若成立，它影響的不只本卡。

### 四、格式規則三條 × 三個消費者：#9 那一格結論是「規則該改」

機械形式：**序列化成功 ⟹ 解析成功且回傳逐字相同的值。**

- **v2 鍵集合**：遵守，走白名單。規則一在它身上被**實測修正兩次**——Python 的 `$` 容許結尾換行使一格恆真；字母集不涵蓋跨欄位不變量，導致 `review.card_id` 尾綴 `-` 寫得出讀不回。故加寫「**寫入端接受集 ⊆ 讀取端接受集**」。
- **#30 clearance**：可遵守，前提是採 §4.3 裁定用同一套文法而非另立第四套。
- **#9 checkpoint payload**：**規則過嚴，該改的是規則。** 原措辭把保留字元寫成唯一解，會擋掉中文散文必要的逃逸策略；改為逐欄位宣告處置**三選一**（保留／逃逸／不適用）。修正後 #9 **仍有兩格真實不合格**（實測其 `_yaml_scalar` → `_parse_yaml_subset` 14 個值）：**換行與連續空白被靜默摺疊——那是正規化不是逃逸**。故規則二明文禁止以正規化代替拒收。附帶警告：**含三反引號的值今天不破壞區塊只是因為摺疊把它拉回同一行，修掉摺疊會讓這保護一起消失。**

**請攻擊**：規則被消費者實測後改了兩次——那是規則在自我修正，還是規則太弱以致遷就實作？

### 五、驗證

離線 **961/961**、`--live` **1237/1237**。**PM 已自行抽出重跑得 961 格全通過。**

A 組與 E 組 **`import` 現行 `doctor` 本人**（不是複製一份判定），比對 49 則真實 marker 與 **275 則真實留言原文**，**判定改變 0 則**。B 組 686 格往返用真實 `card_id`／sha／`attempt_id`。C 組 70 格四分類矩陣，`silent-misread` 與 `read-rejected` 零格。D 組對少一鍵／多一鍵／錯序／雙空白**窮舉所有位置**全拒，含正向對照。

**卡面要求你拿 `--live` 重跑，別只讀數字。**

### 六、執行者自陳的最大落差是結構性的

> 本卡寫入集不含 `cli/`，所以「**寫入端拒收**」這件事**本卡在物理上做不到**。§6 立下的規則二對本卡自己是**待兌現**不是已兌現；`serialize_v2()` 只存在於探針進程內，**wfcli 的六個動詞沒有一處呼叫它**。

它指出 #37 是同一條規則**已兌現**的存在證明——路走得通，本卡沒有走完它的權限。另：**探針沒有 CI 跑它**（一份不跑的往返測試與沒有往返測試證據強度相同）——#48 同批送審，可能改變這一點。

其餘四條（v2 是最後一次為加欄位而升版、既有 v1 不得遷移、clearance 用 v2 文法、載體一律留言）**全部是約定，沒有任何東西擋得住反例**。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5264397501 · 2026-08-12T08:39:42Z

core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: gh issue view 35 --repo ruan6047/ai-workflow --json comments
    observed: 斉二派 進審審譞詞，示嫪9e同켚名文点，訊仵纠0^A
  - command: git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-marker-v2-scope1 rev-parse HEAD
    observed: d44ec710cf5b58bef19a3166668310bee1ed0364 u�

## Comment 5264402379 · 2026-08-12T08:40:06Z

core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "gh issue view 35 --repo ruan6047/ai-workflow --json comments"
    observed: "已先讀取最後一則派審詞，並以其作為權威來源。"
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-marker-v2-scope1 rev-parse HEAD && git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-marker-v2-scope1 status --short"
    observed: "HEAD 為 d44ec710cf5b58bef19a0316668310bee1ed0364，工作樹乾淨；首輪，無前輪 accepted blocking finding。"
  - command: "WF_REPO=/tmp/aiwf35-review.uKuKqa python3 /tmp/wf_marker_v2_probe_35.py --live"
    observed: "PASS 1244/1244；49 則 v1 語料與 282 則真實留言重放的判定改變均為 0。"
  - command: "PYTHONPATH=/Users/ruanruan/Dev/ai-workflow/cli/src python3 -"
    observed: "#9 的 _yaml_scalar 經 _parse_yaml_subset 對換行與連續空白皆未逐字往返；設計文件正確判為正規化而非逃逸。"
  - command: "git diff --check 5d22a7f3da57a3790179e999d9d28262fda4d19a d44ec710cf5b58bef19a0316668310bee1ed0364"
    observed: "無空白錯誤；契約明確將 v2 寫入端與讀取器實作列為尚未實作，未把探針證據誤稱為既成生產保證。"
findings: []

## Comment 5264405562 · 2026-08-12T08:40:26Z

<!-- wf-review-receipt:v1
card_id: WF-EVENT-MARKER-V2-SCOPE1
source_sha: d44ec710cf5b58bef19a0316668310bee1ed0364
report_sha256: 881fb51137a8e840fafc8bd43ef6c47c29fbf8d062bddbe0fa9a04c291c8ea4b
-->
取材規則：起點為本規則之後的下一個 core_pain_resolved 行；終點為該 YAML 報告最後一行 findings: [] 的 LF 前；UTF-8；LF；strip: 否；排除本收據區塊、取材規則行與取材規則後的分隔空行。

core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "gh issue view 35 --repo ruan6047/ai-workflow --json comments"
    observed: "已先讀取最後一則派審詞，並以其作為權威來源。"
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-marker-v2-scope1 rev-parse HEAD && git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-marker-v2-scope1 status --short"
    observed: "HEAD 為 d44ec710cf5b58bef19a0316668310bee1ed0364，工作樹乾淨；首輪，無前輪 accepted blocking finding。"
  - command: "WF_REPO=/tmp/aiwf35-review.uKuKqa python3 /tmp/wf_marker_v2_probe_35.py --live"
    observed: "PASS 1244/1244；49 則 v1 語料與 282 則真實留言重放的判定改變均為 0。"
  - command: "PYTHONPATH=/Users/ruanruan/Dev/ai-workflow/cli/src python3 -"
    observed: "#9 的 _yaml_scalar 經 _parse_yaml_subset 對換行與連續空白皆未逐字往返；設計文件正確判為正規化而非逃逸。"
  - command: "git diff --check 5d22a7f3da57a3790179e999d9d28262fda4d19a d44ec710cf5b58bef19a0316668310bee1ed0364"
    observed: "無空白錯誤；契約明確將 v2 寫入端與讀取器實作列為尚未實作，未把探針證據誤稱為既成生產保證。"
findings: []

## Comment 5264600348 · 2026-08-12T08:59:54Z

<!-- wf-review-event:v1 card_id=WF-EVENT-MARKER-V2-SCOPE1 source_sha=d44ec710cf5b58bef19a0316668310bee1ed0364 attempt_id=WF-EVENT-MARKER-V2-SCOPE1-e0-d44ec710cf5b58bef19a0316668310bee1ed0364 -->
## 查核裁決：APPROVE

- 卡：`WF-EVENT-MARKER-V2-SCOPE1`　attempt_id：`WF-EVENT-MARKER-V2-SCOPE1-e0-d44ec710cf5b58bef19a0316668310bee1ed0364`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5264405562 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=881fb511… 一次相符。本批六份收據皆採內容錨定或分隔行，各自規則不同，PM 逐份照其規則計算、無需任何格式調整）　escalation_epoch：0
- source_sha：`d44ec710cf5b58bef19a0316668310bee1ed0364`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-12T16:59:52+08:00

### self_run（查核者實跑）

- `gh issue view 35 --repo ruan6047/ai-workflow --json comments`
  - 已先讀取最後一則派審詞，並以其作為權威來源。
- `git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-marker-v2-scope1 rev-parse HEAD && git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-marker-v2-scope1 status --short`
  - HEAD 為 d44ec710cf5b58bef19a0316668310bee1ed0364，工作樹乾淨；首輪，無前輪 accepted blocking finding。
- `WF_REPO=/tmp/aiwf35-review.uKuKqa python3 /tmp/wf_marker_v2_probe_35.py --live`
  - PASS 1244/1244；49 則 v1 語料與 282 則真實留言重放的判定改變均為 0。
- `PYTHONPATH=/Users/ruanruan/Dev/ai-workflow/cli/src python3 -`
  - #9 的 _yaml_scalar 經 _parse_yaml_subset 對換行與連續空白皆未逐字往返；設計文件正確判為正規化而非逃逸。
- `git diff --check 5d22a7f3da57a3790179e999d9d28262fda4d19a d44ec710cf5b58bef19a0316668310bee1ed0364`
  - 無空白錯誤；契約明確將 v2 寫入端與讀取器實作列為尚未實作，未把探針證據誤稱為既成生產保證。

### findings（0，其中 blocking 0）

- （無）

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5316524704 · 2026-08-17T13:12:52Z

交付狀態已於 `handoff --next-stage release` 寫成 `🏁完成`，但本卡免部署、沒有走 deploy-state 那條會把 Projects Status 帶到 Done 的路徑，Issue 因此停在 OPEN。這是已登記缺口 ruan6047/ai-workflow#84 的實例，依該卡卡面所述的現行 workaround 由 PM 手動關閉。本次收斂共四張：#35 #37 #41 #63。
