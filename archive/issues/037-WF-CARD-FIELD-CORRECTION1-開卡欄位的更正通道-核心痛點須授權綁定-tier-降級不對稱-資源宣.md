# #37 WF-CARD-FIELD-CORRECTION1 開卡欄位的更正通道：核心痛點須授權綁定、tier 降級不對稱、資源宣告雙面同步
- state: closed  created: 2026-08-12T02:07:07Z  closed: 2026-08-17T13:12:56Z
- url: https://github.com/ruan6047/ai-workflow/issues/37
- comments: 6

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：Claude Opus 5@Claude Code（子 agent）（建議 主力型；動唯一寫入通道並為一個具否決權的欄位新增授權模型；需逐一權衡哪些欄位該有更正路徑、哪些不該，推理鏈中等但錯了會傷治理面）　查核：跨家族查核（待需求方指派）（建議 主力型；紅線卡須跨模型家族；查核重點在授權綁定是否可機械核對、以及「可更正」會不會讓失敗中的卡改寫自己的及格線）
- Initiative：—　spec 基線：承接 ai-workflow#12（WF-CLI-TIER-MUTATION1，🏁完成）驗收第 3 條的殘餘射程。#12 的原標題所述 tier 更正能力已由 #19 交付，其標題因 wfcli amend 無 --feature 而無法更正，需求方 2026-08-12 裁定結案並以本卡承接——**本卡的存在本身即「feature 不補」那條裁定的代價**。射程依據為 #12 於 2026-08-12 的評估（issuecomment 見該卡）：五個殘餘欄位分為「筆誤更正／紅線閘門開關／問題重界定／純描述」四類，需求方裁定補前三項中的核心痛點（帶授權綁定）、tier 降級不對稱、resources 雙面同步；服務的原始目標、鏈深、feature 不補，理由須寫入交付物。授權模型對齊 templates/review-escalation.md §4 (a′)（需求方平台身分，非自述）。
- DB：db_scope=none
- 服務的原始目標：讓「開卡時標錯或需重界定的欄位」有一條合規、可稽核、且不會被用來規避閘門的更正路徑；不必在違規與死結之間二選一。

## 簡介
<!-- card-brief:begin -->
為開卡時標錯或需重界定的欄位建立帶授權綁定的更正路徑——核心痛點具否決權卻改不了，曾迫使 PM 改由驗收條文吸收並自記「繞過而非修好」，隨即被跨家族查核判 critical blocking；但也不能用自由文字旗標補，否則失敗中的卡能靠改寫自己的問題陳述而通過。另修 card.py:534 _ROUTING_PARSE_RE 的往返缺陷（名字含全形括號時 open 寫得出、assign 讀不回），交付保留字元清單、寫入端拒收與讀寫往返測試。**適用時機**：要更正已開卡的核心痛點、tier 或 resources 時；或執行者名含全形括號而 assign 判 CAPABILITY_BASELINE_AMBIGUOUS 時。⛔ 非射程：服務的原始目標、鏈深、feature 三個欄位不補更正路徑（承接 aiwf#12 殘餘射程時的需求方裁定）；不得使既有 18 張永久 absent 卡翻成 ambiguous 或 matched（會改動 aiwf#21 R4-002 的既成狀態）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：開卡時設定的欄位有一部分沒有更正路徑，而其中 **核心痛點具否決權**（review-prompt.md §2：痛點未消即 REQUEST_CHANGES，即使驗收清單全過）。缺口的後果不是不便：2026-08-12 需求方裁定縮小 WF-CLEANUP-GUARD1（T4）射程時，核心痛點改不了，PM 只能改由驗收條文的判準去吸收並自記「繞過而非修好」，跨家族查核者隨即把它判為 critical blocking（R4-001，attribution=coordinator）。但缺口也不能用一個自由文字旗標補——那會讓一張正在失敗的卡靠改寫自己的問題陳述而通過。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/amend_cmd.py",
    "file:cli/src/wf_cli/card.py",
    "file:cli/tests/test_amend.py",
    "file:cli/src/wf_cli/commands/open_cmd.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] （2026-08-12 追加）修正 WF-CLI-ROUTING-TIER1（#21，已 🏁完成、APPROVE 0 finding、已併入 main）的往返缺陷。card.py:534 的 _ROUTING_PARSE_RE 以 (?P<executor>[^（]*)（建議 錨定，遇到名字本身含全形括號即在第一個括號停住：open 寫得出、assign 讀不回，同一張卡的同一行被兩支給出不一致解讀。PM 已二分實證（名字含全形括號→CAPABILITY_BASELINE_AMBIGUOUS、拿掉→matched），並於本卡的 assign 事件記下真因。修法歸本卡的理由是 card.py 正是本卡寫入集，另開卡會被本卡宣告擋住排隊。
- [ ] （2026-08-12 追加）本卡的修法須同時交付格式設計的三件事，不得只補一條正則：(a) 保留字元清單——宣告全形左右括號、全形分號、全形空格在路由行中承擔結構，因而不得出現在執行者／查核者名的值裡；(b) 寫入端拒收——open 在寫入時即拒收含保留字元的名，不得靜默接受一個自己讀不回的值；(c) 讀寫往返測試——open 寫得出的路由行，assign 與 compare_capability_to_card 必須讀得回，且語料須含真實使用過的名字（形如「Claude Opus 5@Claude Code（子 agent）」）。第 (c) 條是機械的：不需要人判斷格式寫得夠不夠清楚，跑一次往返就知道。

## 驗證

- [ ] （追加）往返修法不得使既有 18 張永久 absent 卡由 absent 變成 ambiguous 或 matched——那會改變 WF-CLI-ROUTING-TIER1 R4-002 需求方裁定的既成狀態。須有測試釘住。
## Log

- 2026-08-12T10:07:05+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-12T10:27:19+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；分支worktree claude/WF-CARD-FIELD-CORRECTION1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-card-field-correction1；交付狀態 🚧進行中；實際能力層級 主力型（卡面建議無法解析：候選路由行不符合 templates/tasks-card.md 第 4 行格式（如全形／半形空白錯置、缺分號或括號、理由為空、查核段缺失、混入零寬字元）；理由：⚠️ 本理由不是真的偏離——實際層級與卡面建議都是主力型，是 WF-CLI-ROUTING-TIER1（#21，已 🏁完成、APPROVE 0 finding、已併入 main）的往返缺陷使 assign 讀不回 open 寫下的建議。根因：card.py:534 的 _ROUTING_PARSE_RE 以 (?P<executor>[^（]*)（建議 錨定，遇到名字本身含全形括號即在第一個括號停住。本卡的執行者名為「Claude Opus 5@Claude Code（子 agent）」、查核者名為「跨家族查核（待需求方指派）」，兩者都含全形括號，故 compare_capability_to_card 判 ambiguous。PM 已二分實證：同一路由行把名字裡的全形括號拿掉即 matched，保留即 ambiguous。方向是 fail-closed（不會誤放行），但它讓 open 與 assign 對同一張卡的同一行給出不一致的解讀，且 open 未在寫入時拒收會導致此結果的名字。修法落在 card.py——該檔正是本卡的寫入集，射程歸屬待需求方裁定。）。
- 2026-08-12T10:34:12+08:00 amend by wf-cli（op 90847da5）→ 驗收條件：原值「[ ] 核心痛點更正須帶授權綁定：--core-pain 必須併 --ruling-url <本卡留言 URL>，取該留言的 GitHub comment author 逐字比對卡面「需求：」欄，不符即 fail-closed；並排除 author 等於當前 owner（對齊 review-escalation.md §4 第 3 款）。不得與其他欄位旗標同一次調用，使 op id 與一次治理裁定 1:1。；[ ] 「需求：」欄的解析器須寫成可被外部匯入的具名函式並於 docstring 標明共用意圖——#12 的評估已指出它會被本卡與 #9 的 checkpoint writer 同時需要，各實作一份即 drift。；[ ] --tier 降級不對稱：現行 amend --tier 對升降級完全對稱、無額外要求，而 T4→T2 會繞過跨家族查核與 sign-off。降級須有額外要求，其形狀由執行者論證——不得直接套用核心痛點那一套，須說明「紅線閘門被打開時誰負責」如何對應。；[ ] --resources 雙面同步：現行 amend 只寫 body 不寫 Project 欄位（amend_cmd.py 全檔僅 :392 一處 set_field_value 且只給級別）。實測後果：PM 本輪四次收窄全部只落 body，其中 WF-CLEANUP-GUARD1 的 Project 欄位比 body 窄——看板顯示它只佔一份文件，實際持有 cleanup.py／doctor.py／handoff_cmd.py 等八個檔，屬 fail-open 方向。該反向案例須寫入測試或註解作為此條的必要性證據。；[ ] 服務的原始目標、鏈深、feature 三項裁定不補，其理由須寫入交付物（文件或碼註解）而非只留在報告：服務的原始目標是鏈級欄位、單卡改會與同鏈去同步，其變更本質是 baseline-cascade 的 invalidated；降鏈深即規避 canonical §3.3 的強制整鏈重審；feature 零機械後果且實作須動 project.py（逸出寫入集）。；[ ] 須指名一個本卡無法關閉的缺口：review 事件不快照它所依據的核心痛點原文，故即使加上授權綁定，歷史上的 core_pain_resolved 仍不可回溯解讀。修法在 review.py（#9 領地），本卡只指名不代做。」→ 新值「（2026-08-12 追加）修正 WF-CLI-ROUTING-TIER1（#21，已 🏁完成、APPROVE 0 finding、已併入 main）的往返缺陷。card.py:534 的 _ROUTING_PARSE_RE 以 (?P<executor>[^（]*)（建議 錨定，遇到名字本身含全形括號即在第一個括號停住：open 寫得出、assign 讀不回，同一張卡的同一行被兩支給出不一致解讀。PM 已二分實證（名字含全形括號→CAPABILITY_BASELINE_AMBIGUOUS、拿掉→matched），並於本卡的 assign 事件記下真因。修法歸本卡的理由是 card.py 正是本卡寫入集，另開卡會被本卡宣告擋住排隊。；（2026-08-12 追加）本卡的修法須同時交付格式設計的三件事，不得只補一條正則：(a) 保留字元清單——宣告全形左右括號、全形分號、全形空格在路由行中承擔結構，因而不得出現在執行者／查核者名的值裡；(b) 寫入端拒收——open 在寫入時即拒收含保留字元的名，不得靜默接受一個自己讀不回的值；(c) 讀寫往返測試——open 寫得出的路由行，assign 與 compare_capability_to_card 必須讀得回，且語料須含真實使用過的名字（形如「Claude Opus 5@Claude Code（子 agent）」）。第 (c) 條是機械的：不需要人判斷格式寫得夠不夠清楚，跑一次往返就知道。」；理由 需求方 2026-08-12 裁定四點依 PM 建議，其一為：把 #21 的路由行往返缺陷納入本卡（card.py 已在本卡寫入集，另開卡會被擋住排隊），並要求修法同時交付格式設計三件事。背景：需求方問「是不是在設計文件時就規定包含符號跟格式，驗收生成時就比較不容易出現格式錯誤」。PM 查證後的精確答案是：格式其實已經規定了（templates/tasks-card.md:4 逐字寫出分隔符），缺的不是文件詳盡度，而是「宣告哪些字元是保留字」與「寫入端拒收含保留字的值」。本卡因此成為該規則的第一個實作先例，通用規則另行 amend 進 #35。。
- 2026-08-12T10:34:12+08:00 amend by wf-cli（op 90847da5）→ 驗證：原值「[ ] 授權綁定的突變驗證：拿掉 author 比對後必須有測試轉紅，且轉紅的理由須為「授權沒被檢查」而非其他。；[ ] 雙面同步須以 mocked runner 驗證 body 與 Project 欄位皆被寫入，並含一條「只寫其中一面即失敗」的反向測試。；[ ] 不得拿真實卡片測試新旗標；全部驗證走 mocked runner 或密封探針（tests/test_amend.py 已有現成模式）。；[ ] 動 Projects v2 欄位須走 updateProjectV2ItemFieldValue，並在測試中釘住「不得觸及欄位定義」——本專案曾因 updateProjectV2Field 重生選項 ID 導致 56 張卡狀態被清空。」→ 新值「（追加）往返修法不得使既有 18 張永久 absent 卡由 absent 變成 ambiguous 或 matched——那會改變 WF-CLI-ROUTING-TIER1 R4-002 需求方裁定的既成狀態。須有測試釘住。」；理由 需求方 2026-08-12 裁定四點依 PM 建議，其一為：把 #21 的路由行往返缺陷納入本卡（card.py 已在本卡寫入集，另開卡會被擋住排隊），並要求修法同時交付格式設計三件事。背景：需求方問「是不是在設計文件時就規定包含符號跟格式，驗收生成時就比較不容易出現格式錯誤」。PM 查證後的精確答案是：格式其實已經規定了（templates/tasks-card.md:4 逐字寫出分隔符），缺的不是文件詳盡度，而是「宣告哪些字元是保留字」與「寫入端拒收含保留字的值」。本卡因此成為該規則的第一個實作先例，通用規則另行 amend 進 #35。。
- 2026-08-12T11:23:05+08:00 amend by wf-cli（op f9df9cb6）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/commands/amend_cmd.py", "file:cli/src/wf_cli/card.py", "file:cli/tests/test_amend.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/commands/amend_cmd.py、file:cli/src/wf_cli/card.py、file:cli/tests/test_amend.py、file:cli/src/wf_cli/commands/open_cmd.py」；理由 需求方 2026-08-12 批准擴充：加入 cli/src/wf_cli/commands/open_cmd.py。執行者於 7bb76aa 交付後回報，寫入端拒收本身完全落在 card.py 的 Card.__post_init__（Card 建構早於任何 GitHub 寫入，故 open 是 fail-closed、不留半寫狀態，已有以 graphql_calls 計數證明的測試），理由側因 open_cmd 已呼叫 validate_capability_routing 而完整；但名字側逸出——cli.py 的 KNOWN_ERRORS 不收 ValueError，名字被擋時吐 traceback 而非「[open] 拒絕：」＋ rc 2。修法為在 open_cmd 既有前置檢查旁多呼叫 validate_routing_names，2 行。批准理由：一個以 stack trace 收場的 fail-closed 不算乾淨拒絕，而本卡存在的理由正是建立乾淨的寫入端拒收。open_cmd.py 經查目前無任何活卡宣告。執行者未自行擴張也未繞道（明確拒絕以可選參數留下「沒傳就不檢查」的靜默洞），現況已由 test_open_refuses_an_unreadable_name_before_touching_github 釘住。。
- 2026-08-12T12:01:53+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA d232faec632dd762ec2e4c0a93997adb834bb7df；證據 R1：三個 commit。bc86876 前的 7bb76aa 交付卡面前五條驗收（--core-pain 帶授權綁定、--tier 降級不對稱、--resources 雙面同步、Initiative、需求方欄解析器具名共用）；bc86876 補 open_cmd.py 的名字側前置檢查（需求方 2026-08-12 批准擴充寫入集，op f9df9cb6）；d232fae 逐處以原文重核卡號與裁定引用並更正六處。

逐欄位保留字元實測（6 欄位 × 4 結構字元 = 24 格，非照卡面裁定照禁）：名字段四個字元全部使解析失配故四個全禁；理由段全形括號與分號實測往返成立、只有全形空格失配故只禁全形空格——禁括號會當場擋掉 #38 那條合法規劃理由；層級段不設清單，保護是封閉語彙 CAPABILITY_TIERS，該段是唯一會靜默錯讀的格子（含全形分號會讀成截斷後的前半段而非失配），已有獨立測試釘住。不對稱的理由已寫成 card.py 內的警告，防後人讀成漏寫。

全卡實測 39 份真實 body：absent 34/ambiguous 4/matched 1 → absent 34/ambiguous 3/matched 2，唯一變動是 #38 由 ambiguous 轉 matched，absent 全體零變動。PM 已以不同語料（--state all 全體，分母 21）獨立重跑，delta 精確重現。

d232fae 的六處更正中兩處源頭是 PM：(1) R4-002 的裁定被 PM 在派工詞與裁定留言中由「A 或（附條件的）B」的選言強化成「不新增遷移入口」的禁令，執行者照抄進 test_amend.py:1696——PM 已發前向更正 issuecomment-5262064584，attribution=coordinator；(2)「assign 硬拒 #38」的轉述，執行者查 Log 後更正為落 ambiguous、要求填偏離理由後放行，代價是留下一筆不實的「卡面建議無法解析」而非停機。另四處是執行者自己的：#14 是 PR 不是卡片、本卡寫入集已由三檔變四檔、理由側 docstring 引用了自己上一輪已失效的交付狀態、#11 仍 🚧進行中故只可引用其形態不可援引為已上線 canonical 條款。

pytest 437(基線)→552，ruff 9→9（PM 於基線 6e6e8ab 另開工作樹實測對照組）。d232fae 本輪 git diff -U0 | grep -E "^[+-]\s*(assert |rc = |with pytest)" 回傳空，機械證明只動陳述未動斷言。十個突變全 KILLED，含 M10（拿掉 open_cmd 前置檢查）轉紅理由逐字為「名字未被乾淨拒絕，以 ValueError 收場」。寫入集實際觸及正好四檔，marker 字面 0 處。

執行者自陳未關缺口：突變 harness 在 scratchpad 不在 repo 故查核者無法重跑；39 份 body 全卡掃描是一次性腳本非常駐測試；18 張 absent 的語料是真實路由行而非真實 body 逐位元組重放（真正的機械保證來自 absent 判定與路由行內容無關那條）；層級段字元類調整無獨立突變殺手故不宣稱它修了什麼。需求方已裁定 #35／#37 自身的 ambiguous 不修只記錄（留痕 issuecomment-5261934855，其理由段已由 issuecomment-5262064584 更正）。。
- 2026-08-12T12:23:39+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5262192569 多行格式合規，PM 依其取材規則回讀重算 report_sha256=53d2e963… 一次相符，範圍含兩個 delimiter 正如規則所述。⚠️ 該收據留言 created 04:13:51Z 與 updated 04:14:32Z 相差 41 秒即曾被編輯，PM 無法取得編輯前內容；雜湊以現行 body 重算相符。PM 僅自報告全文中截出結構化區塊，未改任何字元）；core_pain_resolved yes；self_run 6 項；findings 0 項（blocking 0）；attempt WF-CARD-FIELD-CORRECTION1-e0-d232faec632dd762ec2e4c0a93997adb834bb7df。
- 2026-08-12T12:25:46+08:00 handoff by wf-cli → owner —（結案）；iteration 0；SHA d232faec632dd762ec2e4c0a93997adb834bb7df；證據 跨家族查核（GPT-5@Codex 子代理）於 d232fae 判 APPROVE、core_pain_resolved=yes、findings 0、self_run 6 項。收據 issuecomment-5262192569 合規，PM 回讀重算 report_sha256=53d2e963… 一次相符（範圍含兩個 delimiter，正如其規則所述）。⚠️ 該收據留言曾被編輯（created 04:13:51Z / updated 04:14:32Z 相差 41 秒），PM 無法取得編輯前內容，雜湊以現行 body 重算相符——此為本專案已知的「author 不可變、body 可變」弱點的一次實例，非本卡缺陷。

查核者獨立以自己的語料（29 張非 PR body）重跑能力比對得 absent 21/ambiguous 3/deviated 2/matched 3，確認 #38 為 matched、#35 與 #37 仍 ambiguous；並自行取 #21 的 R4-002 原始 disposition 比對，確認 d232fae 的選言更正準確、未再強化為禁令。其唯一 scope_outside 是查核環境的 ruff 無法啟動，非被審實作 finding。

以 PR #44 併入 main，merge commit 20f2ea3fd34cd7f45b8fb87871288e25c753fe60。刻意不 rebase（git merge-tree 實測無衝突），已於併後驗證 git merge-base --is-ancestor d232fae origin/main 成立，被審 SHA 保持可達。

本卡交付使 wfcli amend --core-pain 上線，直接解除 WF-CLEANUP-GUARD1（#25）R4-001 的阻塞——該 finding 的唯一閉合路徑是需求方裁定的出路 (a)，以唯一寫入通道正式更正核心痛點。。
- 2026-08-12T23:11:03+08:00 handoff by wf-cli → owner 待指派；iteration 1；SHA ba4755f4f2e33436d8128a9d68498250540f0cbb；證據 依 docs/ROADMAP.md §0／§3 降級：本卡屬目標 3（治理精緻化），非「防止低級事故」或「可稽核的內容」。需求方 2026-08-12 裁定降級為 Backlog、有餘力再做。⚠️ 降級不是關閉——本卡載有真實 finding 的紀錄，關閉會讓那些發現消失；降級可逆。。
- 2026-08-16T10:38:37+08:00 handoff by wf-cli → owner —（已結案）；iteration 0；SHA d232faec632dd762ec2e4c0a93997adb834bb7df；證據 還原終態（需求方 2026-08-16 裁定；PM 手動執行）。

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

⚠️ 本則不改變本卡的技術結論：跨家族查核的 APPROVE、findings 0、以及交付 SHA 皆維持原值，本次只還原被誤傷的狀態與 iteration。。
- 2026-08-26T22:02:11+08:00 amend by wf-cli（op 6f418d8d）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:627d356a39b7bd9d3413a44ef3e7a19402cfd2c094bb9245926bed484ba70da1 (955 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5261934855 · 2026-08-12T03:30:15Z

## 需求方裁定：陳舊路由行不修，記錄即可

`WF-CARD-FIELD-CORRECTION1` 於 `7bb76aa` 的全卡實測（39 份真實 body）結果：

```
修改前：absent 34 / ambiguous 4 / matched 1
修改後：absent 34 / ambiguous 3 / matched 2
狀態有變的卡：#38  ambiguous → matched   ← 只有這一張
absent 34 張修改後不再是 absent：無
```

殘留三張 `ambiguous`：

| 卡 | 成因 | 是否本卡造成 |
|---|---|---|
| #15 | body 的 `## Log` 排版本就損壞 | 否，`WF-CLI-ROUTING-TIER1`（#21）當時已在案 |
| **#35** | 執行者名含全形括號 | 否，PM 開卡時寫入 |
| **#37** | 同上 | 否，PM 開卡時寫入 |

**需求方 2026-08-12 裁定：不修，記錄即可。**

理由有二。其一，修法需要一個路由欄位的 `amend` 入口，而 #21 的 R4-002 已裁定「不新增遷移入口」——要修得先推翻該裁定。其二，兩張卡都已指派完畢，`assign` 已用 `--capability-deviation-reason` 走過（#38 那次的 deviation 記錄逐字載明了根因），往後成本趨近零。

**執行者刻意不把它們放行成 `matched` 的判斷被採納。** 放行會讓一個從未解析成功的建議冒充「比對過且相符」——那比 `ambiguous` 更糟，因為 `ambiguous` 至少會逼出一則具名的 deviation 理由。

寫入端拒收只防新的，不追溯修既有的；這條界線是刻意的。

## Comment 5262064584 · 2026-08-12T03:51:56Z

## PM 更正：我把 R4-002 的裁定強化成了禁令

本卡稍早的[裁定留言](https://github.com/ruan6047/ai-workflow/issues/37#issuecomment-5261934855)寫著：

> 修法需要一個路由欄位的 `amend` 入口，而 #21 的 R4-002 已裁定「不新增遷移入口」——要修得先推翻該裁定。

**「已裁定不新增遷移入口」與「要修得先推翻該裁定」兩句都是錯的。** R4-002 的需求方裁定原文（逐字）：

> 既有卡永久以 absent 派工，**或**提供具四項路由值、原值 Log 與審核界線的遷移路徑；先完成選擇及測試再合併。

那是**帶條件的選言**，不是禁令。遷移路徑**被允許**，代價是三個條件：四項路由值、原值 Log、審核界線，且須先完成選擇與測試才可合併。

### 這是哪一種錯

`WF-24-EVIDENCE-STRENGTH1`（#11）驗收 (d) 條「轉述授權」逐字禁止的形態：**引用裁決或規則時不得強化其約束力，或改變其所述事實的狀態**。我把「A 或（附條件的）B」轉述成「只能 A」，強化了約束力。

`attribution: coordinator`。發現於 2026-08-12 第二輪 PM 跨卡對帳，發現方式是逐項以被引裁決的**原文**核對本卡交付物的轉述——那正是本輪新增進 `WF-DISPATCH-PRECHECK1`（#38）驗收的那條要求（卡號指向須以被指卡的卡面原文核對，不得只核卡號存在）。**第一輪只核了卡號存在與檔案歸屬，沒核裁定內容，所以漏掉。**

### 已擴散到哪裡

`cli/tests/test_amend.py:1695-1696` 的註解逐字寫著「R4-002 的需求方裁定是『既有卡永久以 absent 派工、不補標記、**不新增遷移入口**』」——執行者從我的派工詞與裁定留言繼承了這個錯誤轉述。**已要求原執行者更正該註解。**

### 什麼**沒有**因此改變

- **測試本身正確**：18 張永久 absent 的斷言不受影響。裁定的第一支確實被選了，本卡的修法確實不得動搖那個既成狀態。錯的只是**陳述理由時把「被選中的一支」寫成「唯一合法的一支」**。
- **本卡先前「陳舊路由行不修，記錄即可」的裁定仍然成立**，但理由要改：不是因為「修法被禁止」，而是因為**需求方選擇不付那三個條件的代價**，且兩張卡都已指派完畢、`assign` 已以具名 deviation 走過，往後成本趨近零。

未追溯編輯任何既有留言；本則為前向更正。

## Comment 5262154367 · 2026-08-12T04:07:22Z

## 派審：#37 `WF-CARD-FIELD-CORRECTION1` R1

⚠️ 審核對象 **`ruan6047/ai-workflow#37`**，不是 `cpbl-analytics#37`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-card-field-correction1
分支：claude/WF-CARD-FIELD-CORRECTION1
被審 SHA：d232faec632dd762ec2e4c0a93997adb834bb7df
基線：6e6e8abd650c76fa6a2173f5dff35f99038ca1e0（= merge-base origin/main d232fae，已驗為祖先）
iteration：0（首輪）
```

> **`origin/main` 現為 `3e47838`，不是基線。** PM 已跑機械前置：SHA／基線／祖先／工作區乾淨／已推送／該 SHA 尚無 review event，全數通過。對不上就回報 `review-invalid`，不要自行繞過。

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-card-field-correction1
git rev-parse HEAD && git status --short
git merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD && echo 基線成立
git log --oneline 6e6e8ab..HEAD        # 三個 commit：7bb76aa / bc86876 / d232fae
cd cli && uv run pytest -q             # 基線 437 → 本版 552
```

### 一、它沒有照需求方的裁定照禁，請判斷這是對的還是逾越

需求方原裁定要求宣告全形括號、分號、空格為保留字元。執行者**逐欄位實測 6 欄位 × 4 結構字元 = 24 格**後分成三類：

- **名字段**（`executor`／`reviewer`）：四個字元全部使解析失配 → 四個全禁
- **理由段**：全形括號與分號**實測往返成立**，只有全形空格失配 → **只禁全形空格**
- **層級段**：不設清單，保護是封閉語彙 `CAPABILITY_TIERS`

理由是：禁括號會當場擋掉 #38 那條合法規劃理由（中文散文本來就大量用全形括號），等於用一個新缺陷換掉舊缺陷。

**請攻擊**：(a) 那 24 格實測本身可信嗎，還是有格子沒真的跑？(b) 層級段是**唯一會靜默錯讀**的格子（含全形分號會讀成截斷後的前半段而非失配）——封閉語彙那條保證真的擋得住嗎？(c) 執行者自陳層級段的字元類調整 `[^；）]+ → [^；　]+` **找不到獨立突變殺手**，故不宣稱它修了什麼——這個誠實是否恰當，還是那處改動根本不該進來？

### 二、寫入端拒收落在兩層，請判斷分工是否成立

拒收在 `Card.__post_init__`（早於任何 GitHub 寫入，繞過 CLI 直接建 Card 同樣擋得住）；訊息品質在 `open_cmd.py` 的前置檢查（給 `[open] 拒絕：` ＋ rc 2 而非 traceback）。舊測試 `test_open_refuses_an_unreadable_name_before_touching_github` 未刪且改成兩段，第二段**刻意 monkeypatch 停用前置檢查**證明 model 層防線獨立成立。

`open_cmd.py` 是需求方 2026-08-12 批准的寫入集擴充（op `f9df9cb6`），執行者原本明確拒絕以可選參數留「沒傳就不檢查」的靜默洞。

### 三、六處引用更正，其中兩處源頭是 Coordinator

`d232fae` 逐處以**原文**重核卡號與裁定引用並更正六處：

| 處 | 更正內容 | 源頭 |
|---|---|---|
| R4-002 的裁定 | 原寫「不新增遷移入口」；原文是「既有卡永久以 absent 派工，**或**提供具四項路由值、原值 Log 與審核界線的遷移路徑」——**選言而非禁令** | **PM** |
| `assign 硬拒 #38` | 實際是落 `ambiguous`、要求填偏離理由後**放行**；代價是留下一筆不實的「卡面建議無法解析」而非停機 | **PM** |
| `#14 無此行故 18 張` | #14 是 PR 不是卡片 | 執行者 |
| 本卡寫入集「三個檔」 | 已變四個檔 | 執行者 |
| 理由側 docstring | 引用了自己上一輪已失效的交付狀態 | 執行者 |
| `#11 驗收 (d)` | #11 仍 🚧進行中，只可引用其形態、不可援引為已上線 canonical | 執行者 |

第一處 PM 已發前向更正（`issuecomment-5262064584`，`attribution=coordinator`）。

**請判斷**：(a) 更正後的轉述是否準確——**請自己 `gh` 取原文比對，不要接受本派審詞的轉述**；(b) 更正痕跡留在檔內（不是靜默改掉）是否恰當；(c) 還有沒有漏掉的同型引用。

### 四、承重宣稱：全卡實測

執行者報 39 份真實 body：`absent 34/ambiguous 4/matched 1` → `absent 34/ambiguous 3/matched 2`，**唯一變動是 #38 由 ambiguous 轉 matched**。

PM 以**不同語料**（`--state all` 全體，分母 21）獨立重跑，**delta 精確重現**：只有 #38 變動、absent 全體逐張零變動。兩份語料分母不同（39 vs 21）但承重的不變量一致。

**請自己再跑一次，用你自己的語料。** 這是本卡最承重的宣稱，而執行者自陳它是一次性腳本、不是常駐測試。

### 五、已知殘留（PM 自審已找到，不必重複發現，可判斷處置是否恰當）

1. **突變 harness 在 scratchpad 不在 repo**——你無法重跑那十條突變。執行者三輪都自陳此缺口未解，且列出了每條突變的單點字串替換以便手動重現。
2. **18 張 absent 的語料是真實路由行放進標準舊卡 body，不是真實 body 逐位元組重放**。真正的機械保證來自 `test_absent_verdict_does_not_depend_on_routing_line_content_at_all`（absent 在到達解析器之前就決定了）。
3. **#35／#37 自身的路由行仍 ambiguous**，需求方裁定不修只記錄（留痕 `issuecomment-5261934855`，其理由段已由 `issuecomment-5262064584` 更正）。執行者刻意不放行成 matched——「讓一個從未解析成功的建議冒充比對過且相符」比 ambiguous 更糟。
4. **保留字元清單只落在 `card.py`，未進 `templates/tasks-card.md`**；通用規則走 #35，本卡是實作先例。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**——散文引用與 code fence 示範都一樣。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. 首輪無前輪 finding，**但請明確寫出「首輪，無前輪 accepted blocking finding」**而非略過該節。
2. **五個 schema 欄位自己填**（`severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id`）。
3. **留收據**：`wf-review-receipt:v1` **多行格式**（`card_id:` 與 `source_sha:` **各自獨立成行**，單行 `key=value` 形式 `doctor` 認不得），**把被雜湊的報告全文放進同一則留言**並寫死取材規則（起點、終點、編碼、換行、是否 strip、排除範圍）。⚠️ **取材規則若在散文裡提到起訖 delimiter 的字面，請說清楚是「規則之後的下一個」**——PM 上一次回讀時第一次就錨到規則散文內的同名字面而失敗。

**YAML 限制**（解析器是自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、值含 ` #` 須整個值加引號。非 schema 的頂層鍵會被容忍。


## Comment 5262192569 · 2026-08-12T04:13:51Z

<!-- wf-review-receipt:v1
card_id: WF-CARD-FIELD-CORRECTION1
source_sha: d232faec632dd762ec2e4c0a93997adb834bb7df
report_sha256: 53d2e963c4a7e64f4e853a0d17343cf040a399fa86d1c18828f813bf26a96be1
-->

取材規則：起點為本規則之後下一個報告起始分隔行首字元；終點為後續報告結束分隔行的末字元；UTF-8、LF、無 strip；排除 receipt HTML 註解與此取材規則行。

--- report-begin ---
core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "git rev-parse HEAD && git status --short && git merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD"
    observed: "HEAD=d232faec632dd762ec2e4c0a93997adb834bb7df；工作區乾淨；基線祖先檢查 exit 0。"
  - command: "git diff --check 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 d232faec632dd762ec2e4c0a93997adb834bb7df"
    observed: "無 whitespace error；遠端 claude/WF-CARD-FIELD-CORRECTION1 包含被審 SHA。"
  - command: "cd cli && uv run pytest -q"
    observed: "552 passed in 5.52s。"
  - command: "cd cli && uv run python -c '逐欄位 6×4 路由字元探針'"
    observed: "名字段 8 格全失配；理由段僅 U+3000 失配、其餘 6 格逐字往返；層級段含 U+FF1B 讀成截斷前半段，現行封閉 CAPABILITY_TIERS 不含四個結構字元。"
  - command: "cd cli && gh api repos/ruan6047/ai-workflow/issues?state=all&per_page=100 --paginate | uv run python -c 'compare_capability_to_card 全體非 PR body'"
    observed: "獨立現況語料共 29 張：absent 21、ambiguous 3、deviated 2、matched 3；#38 為 matched，#35 與 #37 仍 ambiguous，符合不追溯放行的界線。"
  - command: "gh api repos/ruan6047/ai-workflow/issues/21/comments?per_page=100 --paginate"
    observed: "R4-002 原始 disposition 為『既有卡永久以 absent 派工，或提供具四項路由值、原值 Log 與審核界線的遷移路徑；先完成選擇及測試再合併』；d232fae 的選言更正準確，未再強化為禁令。"
first_round_prior_findings: "首輪，無前輪 accepted blocking finding。"
findings: []
scope_outside_findings:
  - topic: "ruff 執行環境"
    observation: "cd cli && uv run ruff check 無法啟動，原因為 uv 環境找不到 ruff executable；此為環境限制，未構成被審實作 finding。"
--- report-end ---

## Comment 5262253337 · 2026-08-12T04:23:40Z

<!-- wf-review-event:v1 card_id=WF-CARD-FIELD-CORRECTION1 source_sha=d232faec632dd762ec2e4c0a93997adb834bb7df attempt_id=WF-CARD-FIELD-CORRECTION1-e0-d232faec632dd762ec2e4c0a93997adb834bb7df -->
## 查核裁決：APPROVE

- 卡：`WF-CARD-FIELD-CORRECTION1`　attempt_id：`WF-CARD-FIELD-CORRECTION1-e0-d232faec632dd762ec2e4c0a93997adb834bb7df`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5262192569 多行格式合規，PM 依其取材規則回讀重算 report_sha256=53d2e963… 一次相符，範圍含兩個 delimiter 正如規則所述。⚠️ 該收據留言 created 04:13:51Z 與 updated 04:14:32Z 相差 41 秒即曾被編輯，PM 無法取得編輯前內容；雜湊以現行 body 重算相符。PM 僅自報告全文中截出結構化區塊，未改任何字元）　escalation_epoch：0
- source_sha：`d232faec632dd762ec2e4c0a93997adb834bb7df`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-12T12:23:39+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git status --short && git merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD`
  - HEAD=d232faec632dd762ec2e4c0a93997adb834bb7df；工作區乾淨；基線祖先檢查 exit 0。
- `git diff --check 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 d232faec632dd762ec2e4c0a93997adb834bb7df`
  - 無 whitespace error；遠端 claude/WF-CARD-FIELD-CORRECTION1 包含被審 SHA。
- `cd cli && uv run pytest -q`
  - 552 passed in 5.52s。
- `cd cli && uv run python -c '逐欄位 6×4 路由字元探針'`
  - 名字段 8 格全失配；理由段僅 U+3000 失配、其餘 6 格逐字往返；層級段含 U+FF1B 讀成截斷前半段，現行封閉 CAPABILITY_TIERS 不含四個結構字元。
- `cd cli && gh api repos/ruan6047/ai-workflow/issues?state=all&per_page=100 --paginate | uv run python -c 'compare_capability_to_card 全體非 PR body'`
  - 獨立現況語料共 29 張：absent 21、ambiguous 3、deviated 2、matched 3；#38 為 matched，#35 與 #37 仍 ambiguous，符合不追溯放行的界線。
- `gh api repos/ruan6047/ai-workflow/issues/21/comments?per_page=100 --paginate`
  - R4-002 原始 disposition 為『既有卡永久以 absent 派工，或提供具四項路由值、原值 Log 與審核界線的遷移路徑；先完成選擇及測試再合併』；d232fae 的選言更正準確，未再強化為禁令。

### findings（0，其中 blocking 0）

- （無）

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5316525215 · 2026-08-17T13:12:55Z

交付狀態已於 `handoff --next-stage release` 寫成 `🏁完成`，但本卡免部署、沒有走 deploy-state 那條會把 Projects Status 帶到 Done 的路徑，Issue 因此停在 OPEN。這是已登記缺口 ruan6047/ai-workflow#84 的實例，依該卡卡面所述的現行 workaround 由 PM 手動關閉。本次收斂共四張：#35 #37 #41 #63。
