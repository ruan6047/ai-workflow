# #9 WF-22-CLI4 wfcli escalation 帳承接（accepted 標記／attempt 去重／checkpoint 計數）
- state: closed  created: 2026-08-06T02:58:28Z  closed: 2026-08-13T08:11:44Z
- url: https://github.com/ruan6047/ai-workflow/issues/9
- comments: 24

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
- 執行：待指派　查核：待指派
- Initiative：WF-22　spec 基線：canonical v2 §5＋templates/review-escalation.md §3＋WF-22-CLI3 交付（f180659+）
- DB：db_scope=none
- 服務的原始目標：查核升級協定全鏈機械化——計數、去重、checkpoint 觸發不靠人記

## 簡介
<!-- card-brief:begin -->
把查核升級協定的最後一環機械化：accepted 標記的寫入通道（lifecycle writer 語意）、attempt_id 去重、counts_toward_escalation 推導與 checkpoint 觸發警示，另在 review event 的結構化區塊記下該 attempt 當下的 owner，並誠實標註它取自 Project current-state 快照、不是 attempt 的固有屬性。**適用時機**：要查退回次數怎麼計、怎麼去重、checkpoint 何時觸發時；或要核對 #39 §5 第 3 款的 continued_owner 能不能在事件流上對得起來時。⛔ 非射程：不補查核輸出契約本身的欄位驗證（屬 WF-22-CLI3／aiwf#8）；不做事件 marker 的格式遷移（屬 WF-EVENT-MARKER-V2-SCOPE1／aiwf#35）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：escalation 計數（第三次可計退回進 checkpoint）依賴人工盯帳——review 子命令刻意不半套實作（accepted 屬 lifecycle writer 職權），機械強制缺最後一環

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/review.py",
    "file:cli/src/wf_cli/validation.py",
    "file:cli/src/wf_cli/commands/review_cmd.py",
    "file:cli/src/wf_cli/commands/checkpoint_cmd.py",
    "file:cli/tests/test_review.py",
    "file:cli/tests/test_validation.py",
    "file:cli/tests/test_checkpoint.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] accepted 標記寫入通道（lifecycle writer 語意）；attempt_id 去重；counts_toward_escalation 推導與 checkpoint 觸發警示
- [ ] （2026-08-12 追加，純新增欄位，不動核心痛點）review event 的結構化區塊須記下該 attempt 當下的 owner。理由：WF-ESCALATION-RESOLUTION-GAP1（#39）於 41a9f41 定稿的 §5 第 3 款雙相 continued_owner，其後半「該 checkpoint 之後、本 epoch 內的任一 attempt，其 owner 必須逐字等於最後一則有效 resolution 的 continued_owner」今天在事件流上核對不了——owner 是 Project 的 current-state 欄位，而 review event 沒有記錄它。不補的話那一款是一條永遠沒有執行者的契約規則，正是本 repo 已被打過四次的 claim-exceeds-evidence 形狀。時機取捨已核實：該結構化區塊是本卡本輪剛引入、目前零消費者，現在加成本接近零，之後加即為格式遷移（WF-EVENT-MARKER-V2-SCOPE1 #35 的主題）。本項由執行者於交回時主動指名、刻意不自行擴張射程，需求方 2026-08-12 裁定收進本卡。
- [ ] （同上追加）owner 欄的來源與可信度須誠實標註：它取自 Project 的 current-state 欄位，故記下的是「寫入裁決當下的 owner」而非「該 attempt 全程的 owner」。若兩者可能不同，須說明差異何時會發生、以及第 3 款的核對在該情形下會給出什麼答案。不得把 current-state 的快照寫成 attempt 的固有屬性。

## 驗證

- [ ] cli 測試覆蓋計數／去重／checkpoint 樣本
## Log

- 2026-08-06T10:58:27+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-12T00:14:43+08:00 amend by wf-cli（op 09a1052d）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/review.py、file:cli/src/wf_cli/validation.py、file:cli/src/wf_cli/commands/review_cmd.py、file:cli/src/wf_cli/commands/checkpoint_cmd.py、file:cli/src/wf_cli/cli.py、file:cli/tests/test_review.py、file:cli/tests/test_validation.py、file:cli/tests/test_checkpoint.py」；理由 需求方 2026-08-12 裁定收窄過寬的目錄級宣告。本卡原宣告整個 cli/，在階層路徑包含語意下與 WF-CLI-ROUTING-TIER1 與 WF-CLEANUP-GUARD1 的每一個檔案相交，兩張現役卡因此在本卡一旦派工時全數動不了。依卡面驗收（accepted 標記寫入通道、attempt_id 去重、counts_toward_escalation 推導與 checkpoint 觸發警示）收窄為實際寫入子樹，含新增的 checkpoint writer 動詞與其測試。此收窄與 #24 的裁定不衝突：#24 護的是「我會在這裡新增檔案」的目錄宣告，不是大於實際工作的宣告。⚠️ 仍存在的相交需明示，不以收窄掩蓋：cli/tests/test_review.py 與 WF-CLI-ROUTING-TIER1 相交；cli/src/wf_cli/cli.py 與後續新增動詞的卡（marker 判準收窄＋clearance 表示法）相交。兩者皆為真實的寫入集重疊，須以先後派工解決，不得以縮小宣告規避。。
- 2026-08-12T10:17:26+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；分支worktree claude/WF-22-CLI4 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4；交付狀態 🚧進行中；實際能力層級 主力型（卡面無建議層級：卡面標頭區沒有獨立成行的 <!-- wf-routing:v1 --> 宣告：本卡開立於規劃期路由必填之前；理由：卡面第 4 行為舊制格式，同上無建議層級可比對。派主力型的依據：本卡要在唯一寫入通道實作 checkpoint writer 與 escalation 帳的機械推導，須逐條對照 review-escalation.md §3／§4 的判準且錯了會污染升級帳；推理鏈中等偏長但無需前沿能力。）。
- 2026-08-12T11:25:29+08:00 handoff by wf-cli → owner 跨家族查核（escalation 帳承接，判定執行者是否連續失敗的機制本體）；iteration 0；SHA 2ba565a880e571fb9ee5aea3ca114e8b62acdc2f；證據 R1（切片 A）：四項落地——(1) accepted 預設 true 免旗標，--mark-not-accepted FINDING_ID=理由 才標 false、理由必填、marked_by 取自 gh api user；刻意不綁 review-escalation.md §4 (a′) 的 defer 身分規則（失效方向不同：defer 危險在被嘉惠方自己裁定，accepted 危險在被標成 false）。(2) attempt_id 去重 validation.check_attempt_not_duplicated，擋在任何遠端寫入前，訊息指名 doctor.py:409-415 的永久隔離。(3) counts 推導依 §3 算出後寫進留言 fenced 區塊與 Log 行，新增 wfcli contract-baseline one-shot 事件（同 Issue 第二則 fail loud）；缺 counts 事實的既有 attempt 判「未知」→ 閘門拒絕，不推定為不計數。(4) checkpoint 漏建閘門 validation.check_checkpoint_gate 落在 wfcli review 寫入前，上一個可計數 attempt 序位 ≥3 卻無對應 checkpoint 即 exit 2，判準為兩面一致（留言區塊 ＋ Log 同行索引）。

事件承載走 (B)：fenced 區塊 ＋ Log 索引行、不發新 marker，gh issue comment 的 stdout（新留言 URL）已接起來逐字寫進 Log 行。明確不走 (A) 新 marker 前綴——在 #30 設計宣告行三分類、#35 設計版本升級策略的當下先立第三套文法，正是 #35 開卡要制止的形態。checkpoint writer 拒收 escalation_resolution（指名等待 WF-ESCALATION-RESOLUTION-GAP1 #39）與 deferred_findings（§4 兩個 cause 今天都不可用）。未追溯補建或改寫 PM 那七則 checkpoint。

驗證：pytest 437 → 503 全綠；ruff 9 → 9，全部既有、0 新增。突變 28 個全數 KILLED、0 存活，突變前 baseline 503 綠已先確認故 KILLED 判定有效。全部走 mocked runner（EventGhRunner = FakeGhRunner ＋ 留言讀回／每則留言 URL／gh api user，寫在 tests/test_checkpoint.py，因 fake_gh.py 不在寫入集），未碰任何真實卡片。

⚠️ 執行者主動揭露一項方法論修正：第一次跑突變時 M27 回報的 killer 是錯的（指到 M26 的測試），根因是 CPython 的 .pyc 失效判準為「來源 mtime 秒數 ＋ 大小」，突變檔在同一秒內被寫兩次會讓 pytest 執行到上一個突變的位元碼。已加逐次清 __pycache__ ＋ PYTHONDONTWRITEBYTECODE=1 重跑，M27 才指到正確測試。採信第二次結果，第一次那份不可靠。

切片 B 不做的界線：checkpoint 歷史推導需跨 attempt 的 open set 與根因 occurrence，而契約明定留痕解析停機是解析層 gate 且優先於語意層；CONSUMER_CONFORMANCE.md 落差 7 記錄該停機在本 repo 無解除路徑，並實測 #15／#17／#21 三張裁決完整的卡全部因派審留言引用 event marker 前綴而被隔離。嚴格實作的歷史推導對今天多數真實卡應該拒絕動作。需 #30 定出解除表示法並有 writer 才能做；證據面續走留言（守契約），不走 Issue body 的 ## Log。

執行者自陳八項無機械執行者的宣稱，其中三項最該被打：(1) §3 第 1 款「preflight 已通過且 review 有效」由「有一則 review event 存在」承擔，本 CLI 沒有任何東西證實 preflight 真的跑過，可機械判定的只有「APPROVE 未附 self_run」；邊界外有人略過 preflight 直接下裁決，counts 仍會算成 true/false 而無人知情。(2) marked_by 不得等於卡面 owner 的檢查今天恆真——本 repo 只有 ruan6047 一個人類 GitHub 帳號，owner 欄裝的是自由文字，兩者不在同一命名空間；這是 fail-closed 落差，應登記進 CONSUMER_CONFORMANCE.md（該檔不在寫入集，只指名未代改）。(3) 「條件成立時 checkpoint_decision 只能是 escalate」沒有機械執行者，wfcli checkpoint 照收操作者給的 decision 與 unique_attempt_count，只在 stdout 印出「未由事件流機械推導」——屬切片 B。

可用性代價（執行者要求說在前面）：cutover 後若有讀不懂的留痕，wfcli review 會直接拒寫；既有在飛的卡若已有前輪 attempt 或被隔離的留言，第一次用新版時會被擋，處置是先跑一次 wfcli contract-baseline。沒有前輪 attempt 的第一輪查核不受影響。

後續卡建議（未自行擴張宣告）：project.add_issue_comment 應回傳留言 URL；doctor._ATTEMPT_RE 與 review.parse_attempt_id 是同一條契約的兩份實作待合併；checkpoint 閘門前移到 handoff --next-stage review（handoff_cmd.py 不在宣告內）。。
- 2026-08-12T11:49:07+08:00 amend by wf-cli（op 736ef45e）→ 驗收條件：原值「[ ] accepted 標記寫入通道（lifecycle writer 語意）；attempt_id 去重；counts_toward_escalation 推導與 checkpoint 觸發警示」→ 新值「accepted 標記寫入通道（lifecycle writer 語意）；attempt_id 去重；counts_toward_escalation 推導與 checkpoint 觸發警示；（2026-08-12 追加，純新增欄位，不動核心痛點）review event 的結構化區塊須記下該 attempt 當下的 owner。理由：WF-ESCALATION-RESOLUTION-GAP1（#39）於 41a9f41 定稿的 §5 第 3 款雙相 continued_owner，其後半「該 checkpoint 之後、本 epoch 內的任一 attempt，其 owner 必須逐字等於最後一則有效 resolution 的 continued_owner」今天在事件流上核對不了——owner 是 Project 的 current-state 欄位，而 review event 沒有記錄它。不補的話那一款是一條永遠沒有執行者的契約規則，正是本 repo 已被打過四次的 claim-exceeds-evidence 形狀。時機取捨已核實：該結構化區塊是本卡本輪剛引入、目前零消費者，現在加成本接近零，之後加即為格式遷移（WF-EVENT-MARKER-V2-SCOPE1 #35 的主題）。本項由執行者於交回時主動指名、刻意不自行擴張射程，需求方 2026-08-12 裁定收進本卡。；（同上追加）owner 欄的來源與可信度須誠實標註：它取自 Project 的 current-state 欄位，故記下的是「寫入裁決當下的 owner」而非「該 attempt 全程的 owner」。若兩者可能不同，須說明差異何時會發生、以及第 3 款的核對在該情形下會給出什麼答案。不得把 current-state 的快照寫成 attempt 的固有屬性。」；理由 需求方 2026-08-12 裁定：收進本卡。執行者於 22148dc 交回時主動指名此介面缺口並刻意不自行擴張射程，判斷正確。PM 的裁定理由：不收的話 #39 §5 第 3 款是一條永遠沒有執行者的規則；而本項與 WF-24-EVIDENCE-STRENGTH1（#11）那次被推翻的擴充在性質上不同——那次的前提是假的（所引事故成因經逐字核對後不成立），本次前提可驗（review event 確實無 owner 欄、該條款確實無從執行），且為純新增欄位、不觸及核心痛點，故不重演「用 amend 驗收去擴寫痛點射程」那個被判過 critical blocking 的形態。。
- 2026-08-12T12:02:58+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA 78d406438682e13f3f2a558af12b378d1c52746f；證據 R1（切片 A）：三個 commit。2ba565a 四項落地；22148dc 訊息更正 ＋ accepted_marking_binding；78d4064 owner 時點快照（需求方 2026-08-12 追加驗收，op 736ef45e）。

四項：(1) accepted 預設 true 免旗標，--mark-not-accepted FINDING_ID=理由 才標 false、理由必填、marked_by 取自 gh api user；刻意不綁 §4 (a′) 的 defer 身分規則，因失效方向不同——defer 危險在被嘉惠方自己裁定，accepted 危險在被標成 false。(2) attempt_id 去重擋在任何遠端寫入前，訊息指名 doctor.py:409-415 的永久隔離。(3) counts 推導 ＋ contract-baseline one-shot；缺 counts 事實的既有 attempt 判未知即拒絕，不推定為不計數。(4) checkpoint 漏建閘門落在 wfcli review 寫入前。事件承載走留言 fenced 區塊 ＋ Log 索引行、不發新 marker（明確不在 #30／#35 設計文法的當下先立第三套）。

⚠️ 需求方追加的 owner 欄，執行者推翻了 PM 裁定時的主要理由。PM 的隱含推論是「補上欄位 ⇒ #39 §5 第 3 款就有執行者」；執行者查碼證明 handoff_cmd.py:136 會把 owner 欄設成 --to，而派審走 --next-stage review --to <查核者>、裁決在其後才寫，故快照裝的是查核者不是產出 source_sha 的執行者。已釘成測試跑完整「執行者A → 查核者B → 裁決」並斷言區塊內是查核者B、執行者A 根本不出現。結論：該欄以目前來源不足以直接支撐 §5 第 3 款，照用會系統性誤報而非漏報。執行者如實寫下未包裝成能用（派工詞明文允許此結論）。PM 已發前向更正 issuecomment-5262093113，attribution=coordinator。該欄仍保留，理由改為執行者列的三件：把否則不可回復的事實釘在 append-only 平面（owner 欄每次 handoff 被覆寫、Log 躺在會被整份覆寫的 body 裡）；使該款從「沒有左運算元」變成「有左運算元但語意需消歧義」；鍵名 owner_field_at_verdict_write 而非 owner，把誤用擋在讀的人面前。要真正支撐該款需 handoff 在 implementation→review 這一跳寫出帶 source_sha ＋ 當時 owner 的結構化事件，handoff_cmd.py 不在寫入集故未擴張、列為後續卡前置。

對 #39 三項介面的相容性判定：(1) 半相容——「不因裁定而改寫」已有三道機械執行者，但「機械導出」未實作（--decision 與 --unique-attempt-count 由操作者提供，只在 stdout 印「未由事件流機械推導」），屬切片 B 被 #30 擋住，請如實記為未涵蓋不要因前半句被滿足就當整項相容。(2) 未涵蓋，且其第 6 款與切片 B 同一個 blocker（carried-forward 三項比對要的正是跨 attempt carry set 與根因 occurrence 推導）；fresh-ruling 那一半可先落地。(3) 對本卡不適用，但同型問題判斷該做並已做 accepted_marking_binding（substantive|structurally-vacuous|not-applicable，呼叫端無法塞值），刻意不共用 #39 的鍵名以免兩套不同導出規則長成同一個名字。

驗證：pytest 437(基線)→511，ruff 9→9（PM 在基線 6e6e8ab 另開工作樹實測對照）。突變 35 個全 KILLED，baseline 綠先確認，harness 含 __pycache__ 清除 ＋ PYTHONDONTWRITEBYTECODE=1。⚠️ 執行者於第一輪主動揭露一項方法論修正：M27 首次回報的 killer 是錯的（指到 M26 的測試），根因是 CPython 的 .pyc 失效判準為「來源 mtime 秒數 ＋ 大小」，同一秒內寫兩次會執行到上一個突變的位元碼；採信第二次結果。全部走 mocked runner，未碰真實卡片。寫入集實際觸及八檔零逸出，marker 字面 0 處。

切片 B 不做的界線：checkpoint 歷史推導需跨 attempt 的 open set 與根因 occurrence，而契約明定留痕解析停機是解析層 gate 且優先於語意層；CONSUMER_CONFORMANCE.md 落差 7 記錄該停機無解除路徑，並實測 #15／#17／#21 三張裁決完整的卡全部因派審留言引用 marker 前綴而被隔離。需 #30 定出解除表示法並有 writer。

執行者自陳八項無機械執行者，三項最該打：§3 第 1 款「preflight 已通過且 review 有效」由「有一則 review event 存在」承擔，本 CLI 沒有東西證實 preflight 真的跑過；marked_by 不得等於卡面 owner 的檢查今天恆真（本 repo 只有一個人類 GitHub 帳號，owner 欄裝的是自由文字，兩者不在同一命名空間），應登記進 CONSUMER_CONFORMANCE.md（該檔不在寫入集故只指名未代改）；「條件成立時 checkpoint_decision 只能是 escalate」沒有機械執行者。可用性代價：cutover 後既有在飛卡若已有前輪 attempt 或被隔離留言，第一次用新版會被擋，處置是先跑 wfcli contract-baseline。。
- 2026-08-12T12:24:15+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5262195265 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=063d607f… 一次相符。PM 的轉錄調整：self_run 與其餘序列原為零縮排，解析器要求 2 空格縮排，已補縮排；字串內容逐字未變）；core_pain_resolved no；self_run 3 項；findings 1 項（blocking 1）；attempt WF-22-CLI4-e0-78d406438682e13f3f2a558af12b378d1c52746f。
- 2026-08-12T12:29:09+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 1；SHA 78d406438682e13f3f2a558af12b378d1c52746f；證據 R1-01（major，blocking，implementation，attribution=executor，root_cause_id=unproven-preflight-counting）：review_cmd.py 的 run() 未讀取或驗證 preflight event／證據，卻呼叫 render_verdict_comment() 而不傳 preflight_passed；review.py 將該參數預設為 true 並寫入結構化帳。查核者自跑重現：對一個 executor/implementation/accepted blocking finding 的 REQUEST_CHANGES 報告，未提供任何 preflight 證據仍輸出 preflight_passed: true 與 counts_toward_escalation: true。templates/review-escalation.md §3 第 1 款要求 preflight 已通過且 review 有效才可計數。

disposition：在 lifecycle writer 建立可機械驗證的 preflight 依據；依據不可得時拒絕建立可計數 review 或明確記為不可計數，並補回歸測試。

⚠️ 這正是執行者自己在交付報告中自陳的第一項「沒有機械執行者的宣稱」——查核者把那句自陳變成了可執行的重現。自陳有價值，但自陳不等於處置。

查核者另於 scope_outside 確認兩件：切片 B 的跨 attempt open set／根因 occurrence 歷史推導依解析停機 blocker 未納入本輪 finding；owner_field_at_verdict_write 經 handoff_cmd.py 與 test_owner_snapshot_records_the_reviewer_not_the_executor_under_the_dispatch_convention 證實是裁決時的查核者快照，不足以直接執行 #39 §5 第 3 款，鍵名與散文已誠實防止誤用、保留作 append-only 時點事實合理，但不得宣稱已補足該條款的 owner 證據。。
- 2026-08-12T12:43:18+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 1；SHA 779e5755c49382522ae1551ab576334604fd14f0；證據 R2：R1-01（major，blocking，executor，unproven-preflight-counting）已處置。執行者不爭辯且自陳查核者比它自己講得更準——它的自陳是「第 1 款沒有機械執行者」，查核者指出的是「沒有執行者卻以事實的語氣寫下它的結論」：render_verdict_comment 把 preflight_passed 預設成 true 寫進結構化帳，那不是缺一道閘門，是往 append-only 事件流裡寫一件沒有任何東西證實過的事。歸屬 executor 接受，預設值是它選的。

設計裁量取「拒絕」而非「記為不可計數」，兩個理由：後者是洗白路徑（本該計數的 attempt 只要宣稱拿不到依據就能不進帳，而逃生口開在被約束那一方手上等於沒有約束）；且契約 §1 已明定 preflight 未通過須寫 preflight-failed 且不得建立 review event，故「沒有依據卻要下裁決」本來就不是合法狀態，拒絕它不是新增嚴格度。

PM 曾特別警告若依據對所有卡皆不可得會把 escalation 帳整個關掉。執行者查證後結論與該擔心不同且我已複驗其形狀：閘門只在第 2～4 款已成立時才要求依據，APPROVE 與只含 governance／coordination／environment 或非 executor 歸屬 finding 的 REQUEST_CHANGES 其 counts 因第 2～4 款自身即為 false，與 preflight 無關、照常寫入；被擋下的恰是「這一輪要記在執行者帳上」的那些。M40（把閘門擴及所有裁決）打死 14 個測試，該癱瘓路徑有測試守著。

三件落地：PreflightAttestation（basis ∈ writer-attested | not-established），無依據時區塊寫 preflight_passed: unknown 而非 true，具結須附非空檢查摘要＋取自 gh api user 的具結者身分；derive_counts_toward_escalation 第 1 款只認 preflight.passed，「有一則 review event 存在即蘊含第 1 款」已從碼裡刪除；check_preflight_established 於第 2～4 款成立卻無依據時 exit 2，純檢查、擺在任何遠端呼叫之前，--validate-only 只警示不擋但明說實寫會被拒。

依指示停下回報的部分：機器可驗證的 preflight 依據需自事件流讀 handoff-accepted 或等價事件，其 writer 是 handoff_cmd.py 或新事件型別，皆不在本卡寫入集，未自行擴張。故本輪依據強度如實命名為 writer-attested——它是具結不是機器驗證。

自陳 vs 處置的帳（PM 要求的區分）：本輪關掉第 1 款 preflight；其餘六項仍為自陳並逐項附「為什麼可以留著」，判準是「能在本卡寫入集內關掉的，自陳就不是合格終點」——preflight 屬這類，上一輪停在自陳是失分點，其餘每一項的執行者都落在別人的寫入集或別張卡。

基線自行實測未抄舊數字：merge-base 6e6e8ab 為 437/ruff 9；origin/main 20f2ea3 為 552/ruff 9（未併入本分支）；本分支 511 → 525，ruff 9 → 9。兩個基線各以一次性 detached worktree 實跑後移除，未碰既有 worktree。突變 40 個全 KILLED，baseline 525 先綠。⚠️ 執行者順帶修好一個因重構而失效的舊突變 M04（錨點在 counts 推導拆分後不存在、harness 判 SKIP），改綁新形狀後重新 KILLED，並記下「錨點失效的突變等於沒測，這種 SKIP 不能當成通過」。寫入集不變（八檔，本輪動六檔），marker 字面 0 處。。
- 2026-08-12T13:19:40+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5262575326 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=3f167ac6… 一次相符。本輪四份裁決皆無需 PM 作任何格式調整——區塊零散文、序列已縮排、無 code fence）；core_pain_resolved no；self_run 4 項；findings 1 項（blocking 1）；attempt WF-22-CLI4-e0-779e5755c49382522ae1551ab576334604fd14f0。
- 2026-08-12T13:27:20+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 2；SHA 779e5755c49382522ae1551ab576334604fd14f0；證據 ⚠️ R1-01 判「仍開啟」，且新的 R2-01 沿用同一個 root_cause_id: unproven-preflight-counting——同家族已跨兩個 attempt。下一輪若再出現即第三次、門檻成立；依 review-escalation.md:61，第三個可計數 attempt 出現前 PM 須先建 escalation checkpoint。

R2-01（major，blocking，implementation，executor）：review_cmd.py 將 --preflight-passed 的任意非空值包成 basis=writer-attested；validation.validate_preflight_attestation 只做非空檢查；PreflightAttestation.passed 只檢查 basis。查核者隔離重現：以「任意未驗證字串」作摘要，對 executor/implementation/accepted/blocking finding 仍導出 counts=True。故雖不再預設 true，仍可把未經驗證的具結當成第 1 款已成立。

R1-01 的閉環評語（查核者原文）：「R1 的無依據 true 已不再是預設值，缺 --preflight-passed 的可計數裁決會被拒；但 --preflight-passed 只驗非空摘要，任意字串即可使同一類裁決計數為 true，未建立 R1 disposition 要求的可機械驗證 preflight 依據。」

disposition：在 lifecycle writer 只接受可從 append-only 事件流重建並逐字驗證的 preflight 依據（例如受管轄的 handoff-accepted 或等價事件連同 source_sha、檢查結果與摘要）；缺少該事件時拒絕可計數裁決。**若此 writer 不在本卡寫入集，應維持拒絕並把機械事件 writer 交由具該寫入集的卡承接，而不是以 writer-attested 作為計數依據。**

查核者另註明它未採信本卡宣稱的 40 條突變 harness——它跑的 replay_escalation_rules.py 是 escalation-resolution 規則回放、不是該 harness。scope_outside 兩項：owner_field_at_verdict_write 命名與說明誠實且不足以支撐 #39 continued_owner 比對，未納入 finding；切片 B 的跨 attempt open-set、根因 occurrence 與 checkpoint decision 機械導出仍受既有解析停機限制。。
- 2026-08-12T16:15:50+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 2；SHA 1194d5e4c2ad52455c1b2cea83416d4b8036cf66；證據 R3：R2-01（unproven-preflight-counting，同家族第二次）已處置，執行者不辯解。上一輪它把「預設 true」換成「具結 true」，而具結只驗非空字串——病灶沒關、只是換了入口。

它否決了 disposition 的兩支與 PM 提的中間形狀，取第三個形狀：writer-attested 從列舉刪除、--preflight-passed 旗標一併刪除，合法依據只剩 event-verified；counts_toward_escalation 改三值，第 2～4 款成立而第 1 款依據不可得時記 unavailable。理由逐字：「寫 true 是偽造，寫 false 是洗白——兩者是同一種病的兩個方向」；對 PM 中間形狀（保留 writer-attested 但標記為不可計數）的否決理由是「它讓一個未驗證的具結做實事卻宣稱不算數，而且把上一輪自己拒絕過的洗白路徑放回來——半個依據不該有半個效力」。

PM 已獨立驗證三項：uv run pytest -k mutated → 6 passed（見下）；grep 確認 src/ 內 writer-attested 只剩兩行說明它被移除的註解、旗標不存在，故 counts=true 在本 CLI 結構上不可達；counts 三值已落地。全套 526 passed，ruff 9→9。

⚠️ 最重要的改變：三輪未關的證據可見性缺口這輪關掉了。前三輪的突變 harness 在 scratchpad，查核者跑不到，執行者自陳「自陳大於證據正是打了我三輪的同一個病」。本輪把六條最吃重的 fail-closed 判準搬進 cli/tests/test_validation.py，在 src 的臨時複本上改壞原始碼、以子行程驗證判準不成立，每個探針先斷言 wf_cli.__file__ 落在複本裡（避免以為測到突變版其實載到原版），基線探針必須先過否則 KILLED 無效。**查核者跑 uv run pytest -k mutated 就能自己重現**，PM 已實跑得 6 passed / 520 deselected。repo 外 harness 另 35 條全 KILLED；原 M36–M40 針對的碼本輪已移除，已從 harness 刪除並由 repo 內那六條取代（錨點失效的突變等於沒測）。

代價執行者如實算：本 repo 今天沒有任何 preflight 事件，故每一則本會計數的裁決都是 unavailable——escalation 自動計數在承接卡落地前不可用，**包括本卡自己的三振門檻**。counted_attempts 為空不代表執行者沒有累計，該事實同時寫進事件流散文、wfcli review 每次的 stdout 警告，並提供 escalation_account_unavailable() 讓消費者拿得到那些 attempt。閘門本身未壞：測試注入帶 event-verified 依據的三個 attempt，驗證第四輪仍因缺 checkpoint 被拒、建了 checkpoint 後放行。

承接卡需要什麼（未自行擴張宣告）：event-verified 需 handoff --next-stage review 或等價動詞寫出受管轄的 preflight pass event，帶 source_sha、檢查結果與摘要，落在 append-only 留言平面；writer 是 handoff_cmd.py 或新事件型別，都不在本卡寫入集。該卡落地後本 CLI 只需讓 PreflightBasis(basis="event-verified", source_event=...) 由事件流讀出，derive_counts_toward_escalation 不需再改。

寫入集八檔零逸出，marker 字面 0 處。。
- 2026-08-12T16:59:30+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5264397039 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=ffb5e00e… 一次相符。本批六份收據皆採內容錨定或分隔行，各自規則不同，PM 逐份照其規則計算、無需任何格式調整）；core_pain_resolved no；self_run 3 項；findings 1 項（blocking 1）；attempt WF-22-CLI4-e0-1194d5e4c2ad52455c1b2cea83416d4b8036cf66。
- 2026-08-12T17:08:00+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 3；SHA 1194d5e4c2ad52455c1b2cea83416d4b8036cf66；證據 ⚠️ R3-01（major，blocking，executor，unproven-preflight-counting）——**同家族第三次，第一條件成立**。checkpoint 判 escalate（issuecomment-5264628916），需求方裁定維持同執行者（同日留言），但明示本裁定不是說前三輪沒問題。

R1-01 與 R2-01 皆判 resolved：PREFLIGHT_BASES 僅剩 event-verified 與 not-established，src 內無 CLI 輸入路徑可產生 counts=true，test_no_cli_input_can_produce_a_counting_verdict_today 與 test_preflight_basis_has_no_writer_attested_option_any_more 皆通過。查核者亦獨立實跑 pytest -k mutated 得 6 passed。

R3-01 的實質：review-escalation.md §1 規定 preflight 缺口**不得建立 review event**，§5 將 preflight_passed 與 counts_toward_escalation 定為**布林**欄位。現行實作對缺 event-verified 依據**仍寫入 review event**，且輸出 preflight_passed=unknown、counts_toward_escalation=unavailable——**既不符既有 schema，也讓可計數退回與第三次 checkpoint 仍只能人工盯帳**。

disposition：在 review_cmd 的**任何遠端寫入前**，缺少可從 append-only preflight event 驗證的依據時 **fail closed、不建立 review event**；**不得以 unknown 或 unavailable 擴充既有布林 schema**。受管轄 preflight event writer 應由具 handoff 寫入集的承接卡完成。

⚠️ 三輪的形狀（需求方要求轉達）：預設 true → 具結 true → unavailable 三值，**三次都停在「換一個值」而沒有動「要不要寫」**。前三輪的規格是把值改對，**本輪的規格是缺依據時不要寫**。若這輪仍以調整值或擴充 schema 回應，將是第四次同家族。。
- 2026-08-12T17:34:17+08:00 amend by wf-cli（op b357343c）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/review.py", "file:cli/src/wf_cli/validation.py", "file:cli/src/wf_cli/commands/review_cmd.py", "file:cli/src/wf_cli/commands/checkpoint_cmd.py", "file:cli/src/wf_cli/cli.py", "file:cli/tests/test_review.py", "file:cli/tests/test_validation.py", "file:cli/tests/test_checkpoint.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/review.py、file:cli/src/wf_cli/validation.py、file:cli/src/wf_cli/commands/review_cmd.py、file:cli/src/wf_cli/commands/checkpoint_cmd.py、file:cli/tests/test_review.py、file:cli/tests/test_validation.py、file:cli/tests/test_checkpoint.py」；理由 PM 於 2026-08-12 查詢執行者是否仍需 cli.py，執行者答覆不需要並同意退出。其依據為實測而非印象：git diff 6e6e8ab..HEAD -- cli/src/wf_cli/cli.py 顯示全部改動就是 2ba565a 的四行（checkpoint_cmd 的 import ＋ 註冊呼叫 ＋ 兩行註解），工作樹零待提交；R3-01 的修法完全落在 review.py／validation.py／review_cmd.py 與三個測試檔。 執行者主動指名唯一殘餘風險並接受其成本：若後續查核者反對 checkpoint_cmd 一個模組掛兩個動詞（checkpoint 與 contract-baseline）的安排、要求拆成獨立模組，修它會同時需要 cli.py ＋ 一個新檔；它評估機率低（理由已寫在模組 docstring、前輪查核未提出異議），並明說「接受真的發生時由 PM 重新擴充的成本——那比三張卡卡在我這裡便宜得多」。 它另主動查證一個相關點確認不需要 cli.py：本輪在 review.py 新增兩處 ValueError 不變式，而 cli.py 的 KNOWN_ERRORS 未涵蓋裸 ValueError；若查核者認為該被優雅捕捉，正解是在 review.py 改拋 ValidationError 而非動 cli.py。其立場是不該捕捉——不變式違反屬程式錯誤，traceback 比客氣的錯誤訊息更該出現。 退出目的：cli.py 是 WF-ORCHESTRATION-RECONCILE1（#16）§9 三張未動衍生卡（B 首寫自描述與 wfcli resume、E wfcli merge 動詞、K epoch-anchor 動詞）的共同瓶頸，每個新動詞都須改該檔。需求方 2026-08-12 裁定先開卡、#16 續審排後面，判準是清單被執行才是價值所在，而清單躺著沒做正是當日兩個代價實例（main 轉紅、API 配額耗盡於 handoff 中途）的成因。。
- 2026-08-12T17:37:35+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 3；SHA 04c8e6211576e786a01afaae69cfb5fbe756bbe1；證據 R4：R3-01 已處置，且執行者**撤回了上一輪反對「維持拒絕」的理由**，依據是重讀契約而非被說服：§5:168 的 preflight_passed 是**字面 true** 不是 <boolean>——對照同區塊的 escalation_epoch: <integer>、counts_toward_escalation: <boolean derived from §3> 即知那不是型別佔位。**斷不出 true 的事件不是合格的 review event**，故 unknown／unavailable 從一開始就不是比較誠實的值，是擴充了一個不該被擴充的欄位。它並自己推翻「拒絕等於把真實發生的查核抹掉」——查核仍留在 handoff-contract.md §3.1.2 的收據與報告全文（那正是為「查核者無法執行 wfcli」設計的證據面），被拒的只有狀態面的裁決事件，而狀態面本來就要求 preflight 已通過。

落地四件：寫入前閘門 check_preflight_event_present（缺依據 → exit 2，一則留言不寫、交付狀態與 body 均不動）；新增 preflight_basis_from_body 讀取器（adapter 側只讀不寫，四項逐字比對，source_sha 給出免時鐘新鮮性）；counts_toward_escalation 回到布林、三值列舉整組移除、讀取側對擴充值一律判讀不懂；無依據時整個帳區塊不渲染（省略＝不作任何宣稱）。

⚠️ 代價比上一輪大得多且執行者明說：本 repo 沒有 preflight event writer，故在承接卡落地前 wfcli review **寫不進任何裁決**，不只是可計數的那些。替代路徑：查核證據走 §3.1.2 收據、格式自檢走 --validate-only（不受閘門影響）。讀取器已備妥，承接卡讓該事件存在後整條鏈自動生效、本檔不需再改。**需求方已據此裁定本卡通過查核後延後合併**（同日留言），該裁定針對合併時機而非交付物評價。

⚠️ 一個受寫入集約束的設計決定，執行者主動報備：render_verdict_comment 在無依據時選擇**省略帳區塊**而非拋錯，因為 test_doctor.py（**不在其寫入集**）會不帶 preflight 呼叫它，硬性拒絕會逼它改該檔。省略是安全的——缺帳區塊的事件會被 build_issue_event_history 判為未知、閘門照樣 fail-closed；真正的拒絕在 review_cmd 與兩道內部不變式上。

驗證：基線自跑 merge-base 6e6e8ab = 437／ruff 9；本分支 526 → **528** 全綠、ruff **9**、repo 內突變 **8 條全 KILLED**（uv run pytest -k mutated 查核者可自行重現，PM 已實跑得 8 passed）。寫入集本輪動六檔，marker 字面 0 處。

⚠️ 宣告變更：PM 於本輪後將 cli.py 退出本卡宣告（op b357343c），依據是執行者實測答覆其全部 cli.py 改動就是 2ba565a 的四行且不會再寫。**但分支歷史仍含那四行、合併時會落地**——退出解開的是宣告鎖，不是合併重疊；後合併的一方要處理。詳見 issuecomment-5264959552。

⚠️ 對 #35 的表態（執行者主動，未改碼）：同意 #35 判定 _yaml_scalar → _parse_yaml_subset 的摺疊是**正規化不是逃逸**且**該改的是規則**，理由是其用法只送單行 token（id、列舉值、URL）、摺疊對它們是恆等，真正的多行值走區塊純量不經該函式。#35 已 APPROVE 併入 e8a638c，故它請求以 #35 為準；若本輪查核者仍持不同判定，它請求由需求方裁定歸屬而非在本卡再開一套規則。。
- 2026-08-12T19:17:59+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 3；SHA 9c8036329821fe1fdaf38b648edf6a529c36e139；證據 R4（改基線重做）：因 DEV-CLI-VERB-REGISTRY1（#53）合併進 main（e1b33d8），本分支 cli.py 產生文字衝突，非查核退回、R4 裁決尚未作出。執行者以 merge 而非 rebase 處理（04c8e621 已推送，rebase 需 force-push、撞紅線），merge commit 9c80363 的 parents = 04c8e621 + e1b33d8。cli.py 兩個 hunk 皆取 main 側，解完與 origin/main 的 cli.py byte-identical；其餘 7 檔對 04c8e621 逐檔零變動。pytest 793 passed（與 #53 執行者在拋棄式衝突樹上的數字完全相同）；test_cli_registry.py 44 passed 零摩擦、未動該檔。PM 已複驗 merge-base = e1b33d8 且對 main merge-tree CLEAN。⚠️ 執行者主要發現：本卡不能只 append 一行——checkpoint_cmd 原排在 review_cmd 之後，append 到 tuple 尾端會把兩個動詞排到 snapshot 後而改動既有 help 順序，實際須插在 review_cmd 後才能維持 --help 全文逐字相同；這是「每張新卡只需 append 一行」推論的第一個真實實例，結論為部分反證（機制無缺陷，是那句話比實際契約窄）。⚠️ 另指名不代修：本 repo 沒有 ruff 依賴也沒有 ruff 設定或 CI（uv run ruff check 直接 Failed to spawn），執行者改用 uvx ruff；test_checkpoint.py:6 的 I001 為本分支自帶既有噪音、未修。。
- 2026-08-12T20:53:24+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5266894010 未經編輯，PM 依其取材規則（delimiter「被雜湊的報告全文開始/結束」、strip 前後換行）回讀重算 report_sha256=7ad9317f… 相符。⚠️ 首次寫入嘗試遇 GitHub 504 Gateway Timeout 中斷於 field-list 階段，PM 回讀確認未產生任何留言或欄位變更後重試；core_pain_resolved no；self_run 4 項；findings 1 項（blocking 1）；attempt WF-22-CLI4-e0-9c8036329821fe1fdaf38b648edf6a529c36e139。
- 2026-08-12T21:37:12+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 4；SHA 9c8036329821fe1fdaf38b648edf6a529c36e139；證據 R4-01（major, blocking, implementation, attribution=executor, root_cause_id=unproven-preflight-counting）：preflight_basis_from_body 把任意符合四個文字欄位（wf_preflight_pass v1／card_id／source_sha／preflight_passed true）的 Issue 留言判為 event-verified，即使 event_url 缺失，check_preflight_event_present 隨即通過。查核者在被審 SHA 的隔離 archive 內以任意 YAML body 直接餵入該函式重現。前輪 R1-01 與 R2-01 皆判 resolved；R3-01 判 still_open 並為本輪 R4-01 的直接延續。。
- 2026-08-13T06:25:32+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 4；SHA 3918fe82873877a4b811c7ee47905881954c0127；證據 R5：R4-01（preflight_basis_from_body 把任意符合四個文字欄位的 Issue 留言當成 event-verified）已處置。⚠️ 執行者第一版採「恆拒」（刪除讀取器、require_preflight_basis 無條件拋錯），論證是補 event_id/type/actor/occurred_at 只是把洞往後推一格、而本 repo 唯一可能的通道訊號是留言 author 但人類與每個 AI agent 共用同一個 GitHub 帳號故無鑑別力。PM 複驗該論證成立，但需求方不接受恆拒的代價——wfcli review 從此寫不出任何裁決，等於狀態面上「已查核」與「未查核」再次無法區分，而那正是已結案的 WF-25-REVIEW-WRITE-CHANNEL1（#13）當初要解決的問題。裁定改走「保留寫入、把恆虛性導出到事件」，比照 review-escalation.md §5 第 7 款的 authorization_binding 形態。本 SHA 為該裁定後的第二版。實寫路徑【實測通了】：在交付 SHA 的隔離 archive 內跑真正的 wfcli review、刻意不 patch derive_preflight_basis（先斷言它是 src 真身）只換 GitHub 傳輸層 → exit 0、交付狀態欄翻為 ↩退回、留言數 1。事件上導出 preflight_basis_binding: structurally-unavailable 與 escalation_account: not-asserted，而 preflight_passed 與 counts_toward_escalation 兩個鍵都不出現——不寫 true（偽造）、不寫 false（洗白）、不擴充成三值。derive_preflight_basis_binding 由 writer 加蓋，新增 WRITER_STAMPED_KEYS，提交面含該三鍵一律拒收即使值恰好等於導出值。⚠️ 額外必須做的一件：讀取側新增「讀得懂但未斷言」一態，否則第一則裁決會讓第二則被「帳可重建」閘門擋住；已釘成 test_a_second_review_is_not_blocked_by_the_first_unasserted_one。窮舉測試全保留、判準改為「一律導出 structurally-unavailable 且沒有任何輸入能把它變成 event-verified」：三種留言形狀擺上 timeline 裁決照寫但導出值不動；AST 掃 src/wf_cli 證明無處建構 event-verified；窮舉 review 每個吃 body 的公開函式證明無一回傳 PreflightBasis。突變 8→12 全 KILLED，逐條確認死因是 AssertionError 非 import/syntax；其中一條初版存活（被別的守衛順手擋掉非目標判準），執行者自己抓到並改寫探針使其真正隔離——那是它自己抓到的一次假 KILLED。數字 812 passed（main 基線 701、前一版 793），ruff 23 與 main 逐行相同 0 新增。trailer 的事實錯誤已改（前一版誤寫 Planned-by: Claude Fable 5，實為 Opus 5）。PM 自審：遠端 tip 相符、對 main merge-tree CLEAN、trailer 3/3。⚠️ 執行者自陳六項，第 3 項最該看：導出 structurally-unavailable 沒有讓授權變得可驗證，只是讓它的不可驗證變成機器可讀；承接卡要交的「可驗證格式」在單帳號結構下可能同樣無解，若承接卡只是補欄位則本檔應維持該導出值——它明說沒有證明它可解。第 2 項：「帳被斷言」那一半仍只能跑在模擬世界（event-verified 結構上不可達），那正是「不可達」本身的證據。⚠️ 環境已變：main 現為 d0397e0（#48／#63 已合併），repo 已套用 required_status_checks ruleset（bypass_actors 0、strict true）；本卡的 PR 會被閘門實際擋一次。。
- 2026-08-13T07:03:37+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5273767470。三項前輪 accepted blocking 皆判 resolved。scope_outside 三項未入區塊、保存於收據雜湊範圍內；core_pain_resolved yes；self_run 4 項；findings 0 項（blocking 0）；attempt WF-22-CLI4-e0-3918fe82873877a4b811c7ee47905881954c0127。
- 2026-08-13T16:11:31+08:00 handoff by wf-cli → owner ruan6047；iteration 4；SHA 3918fe82873877a4b811c7ee47905881954c0127；證據 跨家族查核（GPT-5@Codex）APPROVE，需求方授權後以 squash 合併入 main = 10de6f1（PR #82）。merge body 未含 Closes 以免自動關 Issue 觸發 illegal_terminal_before_cleanup。合併前已核對分支 head 等於受審 SHA 3918fe82873877a4b811c7ee47905881954c0127，無查核後追加的碼；因 ruleset strict 要求與 base 同步，合併前以 update-branch 併入 main（僅同步、無新內容）。首次收尾被 merge_verified_remote 擋下（update-branch 產生的遠端 commit 未在本地物件庫，守衛刻意不代為 fetch），零動作未寫狀態面，fetch 後重跑。；收尾清理：已清除 worktree；本地分支、遠端分支 依授權保留（未刪除）。
- 2026-08-26T21:56:06+08:00 amend by wf-cli（op e25619e4）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:0040df7f2318974aeabba828191cdf1abdaa28fcfe90687109bb113582f5bcb8 (715 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5262093113 · 2026-08-12T03:56:58Z

## PM 更正：我裁定收進 owner 欄時的主要理由被執行者推翻

本卡 2026-08-12 的 amend（op `736ef45e`）理由欄寫著：

> 不收的話 #39 §5 第 3 款是一條永遠沒有執行者的規則……本次前提可驗（review event 確實無 owner 欄、該條款確實無從執行）。

**前半句對，後半句的推論錯了。** 我當時的隱含推論是「補上 owner 欄 ⇒ 該款就有執行者」，而執行者於 `78d4064` 查碼後證明那一步不成立。

### 執行者查到什麼

`handoff_cmd.py:136` 的 `set_field_value(..., fields["owner"], args.to)` 會把 owner 欄設成 `--to`。而派審走的是 `handoff --next-stage review --to <查核者>`，**裁決在那之後才寫**。所以這個快照在正常流程下裝的是**查核者**，不是產出 `source_sha` 的執行者。

已釘成測試 `test_owner_snapshot_records_the_reviewer_not_the_executor_under_the_dispatch_convention`：跑完「執行者A → 查核者B → 裁決」全程，斷言區塊裡是 `查核者B`、且 `執行者A` 根本不出現。

### 後果

§5 第 3 款會拿**查核者**去比對 `continued_owner`（＝下一輪的執行者），兩者本來就不該相等 → **每一個 attempt 都被判 fail-closed**。是系統性誤報，不是漏報。

**所以這一欄以目前的來源不足以直接支撐 §5 第 3 款。** 執行者如實寫下這個結論而未包裝成能用，這正是派工詞明文允許的合法結論，判斷正確。

### 那這一欄還該不該留

**該留，但理由要換成執行者列的三件，不是我原本寫的那件：**

1. 它把一個**否則不可回復**的事實釘在 append-only 平面上——owner 欄每次 handoff 都被覆寫，Log 行雖有紀錄但躺在會被整份覆寫的 body 裡。
2. 它讓 §5 第 3 款從「**沒有左運算元**」變成「**有一個左運算元、但語意需先消歧義**」——那是可以往下接的狀態。
3. 鍵名（`owner_field_at_verdict_write` 而非 `owner`）與留言散文把誤用擋在讀的人面前。

### 要真正支撐該款，缺的是什麼

需要「產出 `source_sha` 的執行者」進入事件流，而它今天只存在於 `handoff --next-stage implementation` 當下的 owner 欄。正解是 handoff 在 implementation→review 這一跳寫出帶 `source_sha` ＋ 當時 owner 的結構化事件。`handoff_cmd.py` 不在本卡寫入集，執行者未為它擴張宣告（正確），列為 `escalation-resolution` writer 那張卡的前置。

### 這對 #39 的意思

`WF-ESCALATION-RESOLUTION-GAP1`（#39）的 §5 第 3 款**後半今天仍無執行者**，且本卡的追加**沒有改變這件事**。該事實須寫進 #39 的派審詞，不得讓查核者以為 #9 補了欄位就等於該款可執行。

`attribution: coordinator`。未追溯編輯既有留言；本則為前向更正。

## Comment 5262154717 · 2026-08-12T04:07:26Z

## 派審：#9 `WF-22-CLI4` R1（切片 A）

⚠️ 審核對象 **`ruan6047/ai-workflow#9`**，不是 `cpbl-analytics#9`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4
分支：claude/WF-22-CLI4
被審 SHA：78d406438682e13f3f2a558af12b378d1c52746f
基線：6e6e8abd650c76fa6a2173f5dff35f99038ca1e0（已驗為祖先）
iteration：0（首輪）
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4
git log --oneline 6e6e8ab..HEAD     # 2ba565a 切片A四項 / 22148dc 訊息更正+綁定 / 78d4064 owner快照
cd cli && uv run pytest -q          # 基線 437 → 本版 511
```

> **本卡刻意只做切片 A。** 切片 B（checkpoint 的歷史推導）被 #30 擋住，理由見第五節。**請判斷那條界線是否誠實，而不是把未做的部分算成缺陷。**

### 一、執行者推翻了 Coordinator 的追加理由，請判斷該更正是否正確

需求方追加了一條驗收：review event 記下該 attempt 當下的 owner。**PM 的裁定理由是「補上欄位 ⇒ #39 §5 第 3 款就有執行者」。**

執行者查碼後證明**那一步不成立**：`handoff_cmd.py:136` 會把 owner 欄設成 `--to`，而派審走 `handoff --next-stage review --to <查核者>`、**裁決在其後才寫**。所以快照裝的是**查核者**，不是產出 `source_sha` 的執行者。已釘成測試 `test_owner_snapshot_records_the_reviewer_not_the_executor_under_the_dispatch_convention`，跑完整「執行者A → 查核者B → 裁決」並斷言區塊內是 `查核者B`、`執行者A` 根本不出現。

**結論：該欄以目前來源不足以直接支撐 §5 第 3 款，照用會系統性誤報而非漏報。** 執行者如實寫下未包裝成能用。PM 已發前向更正（`issuecomment-5262093113`，`attribution=coordinator`）。

該欄仍保留，理由改為三件較小但真實的：把否則不可回復的事實釘在 append-only 平面（owner 欄每次 handoff 被覆寫、Log 躺在會被整份覆寫的 body 裡）；使該款從「沒有左運算元」變成「有左運算元但語意需消歧義」；鍵名 **`owner_field_at_verdict_write`** 而非 `owner`，把誤用擋在讀的人面前。

**請判斷**：(a) 這個更正正確且完整嗎——**請自己讀 `handoff_cmd.py` 驗**；(b) 保留該欄的三個新理由是否足以支撐它存在，還是應該整個拿掉？(c) 鍵名的區分（時點快照 vs 固有屬性）是命名潔癖還是真的擋住了誤用？

### 二、`accepted` 的授權模型刻意不對稱，請判斷

`accepted` 預設 `true` 免旗標；要標 `false` 或事後降級才須顯式旗標 ＋ 非空理由 ＋ `marked_by`（取自 `gh api user`）。

**刻意不綁 `review-escalation.md` §4 (a′) 的 defer 身分規則**，理由是失效方向不同：defer 的危險是**被嘉惠方自己裁定**；`accepted` 的危險是**被標成 false**（把 finding 移出 open set，同時抹掉它對 carry、對根因 occurrence、對 attempt 計數的貢獻）。標成 true 是保守方向。

執行者另自行判斷「該做」並實作了 **`accepted_marking_binding`**（`substantive | structurally-vacuous | not-applicable`，由 `derive_accepted_marking_binding` 導出、呼叫端**沒有可以塞值的參數**），理由是 `marked_by` 不得等於 owner 的檢查在本 repo 恆真——本 repo 只有一個人類 GitHub 帳號，owner 欄裝的是「Claude Opus 5@Claude Code（子 agent）」這類自由文字，**兩者不在同一命名空間**。

**它刻意不共用 #39 的 `authorization_binding` 鍵名**：同一個述詞套在另一組角色上，共用鍵名會讓兩套不同的導出規則長成同一個名字。**請判斷這個區分是否成立。**

### 三、事件承載走 (B)，明確不發新 marker

fenced 結構化區塊 ＋ Log 索引行，`gh issue comment` 的 stdout（新留言 URL）已接起來逐字寫進 Log 行。

**明確不走新 marker 前綴**（技術上今天可行——`doctor.py:187` 的管轄判準是 body 是否含既有 marker 前綴，新前綴完全不進 `inspect_event_marker`），理由是那會在 #30 設計宣告行三分類、#35 設計版本升級策略的當下**先斬後奏地立下第三套 marker 文法**。(B) 之後追加 marker 不會使既有事件失效；(A) 之後若定出不同文法，已寫下的就是需要遷移的歷史。

**請判斷這個可逆性論證是否成立**，以及「兩面一致（留言區塊 ＋ Log 同行索引）」作為 checkpoint 識別是否夠——執行者自陳它把偽造面從一則留言擴大到兩處，**但不杜絕偽造**。

### 四、方法論事故，執行者主動揭露

第一輪跑突變時 **M27 回報的 killer 是錯的**（指到 M26 的測試）。根因：CPython 的 `.pyc` 失效判準是「來源 mtime **秒數** ＋ 大小」，突變檔在同一秒內被寫兩次會讓 pytest 執行到**上一個突變的位元碼**。已加逐次清 `__pycache__` ＋ `PYTHONDONTWRITEBYTECODE=1` 重跑，M27 才指到正確測試。**採信第二次結果，第一次那份不可靠。**

**請判斷**：這個修正之後的 35 條突變全 KILLED 可信嗎？有沒有其他條也受同一個假象污染而未被發現？

### 五、切片 B 的界線

checkpoint 歷史推導需跨 attempt 的 open set 與根因 occurrence，而契約明定**留痕解析停機是解析層 gate 且優先於語意層**——讀不出 marker 就談不上算帳。`docs/CONSUMER_CONFORMANCE.md` 落差 7 記錄該停機無解除路徑，並實測 **#15／#17／#21 三張裁決完整的卡全部因派審留言引用 marker 前綴而被隔離**。嚴格實作的歷史推導對今天多數真實卡**應該拒絕動作**。需 #30 定出解除表示法並有 writer。

證據面續走**留言**（守契約），不走 Issue body 的 `## Log`（current-state 平面、每次 `set_item_body` 全量覆寫）。

### 六、對 #39 三項介面的相容性判定，請覆核

1. **半相容**——「不因裁定而改寫」已有三道機械執行者；但「機械導出」**未實作**（`--decision` 與 `--unique-attempt-count` 由操作者提供，只在 stdout 印「未由事件流機械推導」）。**請如實記為未涵蓋，不要因前半句被滿足就當整項相容。**
2. **未涵蓋**，且其第 6 款與切片 B **同一個 blocker**；`fresh-ruling` 那一半可先落地。
3. 對本卡不適用，但同型問題已做（見第二節）。

### 七、已知殘留（PM 自審已找到，可判斷處置是否恰當）

執行者自陳八項無機械執行者，**三項最該打**：

1. **§3 第 1 款「preflight 已通過且 review 有效」由「有一則 review event 存在」承擔**——本 CLI 沒有任何東西證實 preflight 真的跑過；可機械判定的只有「APPROVE 未附 `self_run`」。邊界外：有人略過 preflight 直接下裁決，counts 仍會算成 true/false 而無人知情。
2. **`marked_by` 不得等於卡面 owner 的檢查今天恆真**（見第二節）。應登記進 `CONSUMER_CONFORMANCE.md`，該檔不在寫入集故只指名未代改。
3. **「條件成立時 `checkpoint_decision` 只能是 escalate」沒有機械執行者**——屬切片 B。

**可用性代價**（執行者要求說在前面）：cutover 後既有在飛卡若已有前輪 attempt 或被隔離留言，第一次用新版會被擋，處置是先跑一次 `wfcli contract-baseline`（那本身就是「人裁定」的留痕）。沒有前輪 attempt 的第一輪查核不受影響。

**未追溯補建或改寫 PM 那七則 checkpoint。**

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 破壞性驗證在拋棄式目錄做，不要在被審 worktree 內 `checkout`／`reset`／`stash`。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴，命中即**永久隔離整張卡**。本卡會讓你大量引用事件內容——用 `gh api` 讀進來處理即可，不要把前綴字面寫進報告。發文前 `grep`。

### 輸出

依 `templates/review-prompt.md` §5。**三項強制**：首輪無前輪 finding 但**須明確寫出該節**；**五個 schema 欄位自己填**；**留收據**（多行格式、報告全文同帖、取材規則寫死，並說清楚起訖 delimiter 是「規則之後的下一個」）。

**YAML 限制**：不支援 `>`（用 `|`）、不支援裸字串序列、不支援頂層鍵＋巢狀 mapping、值含 ` #` 須加引號。


## Comment 5262195265 · 2026-08-12T04:14:17Z

<!-- wf-review-receipt:v1
card_id: WF-22-CLI4
source_sha: 78d406438682e13f3f2a558af12b378d1c52746f
report_sha256: 063d607fee2e3d3159233894d85295182fd2cbbacbd50b761a0bcbb6008bac27
-->

取材規則：取材範圍是本規則之後的下一個「--- 被雜湊的報告全文開始 ---」整行之後的第一個字元，至下一個「--- 被雜湊的報告全文結束 ---」整行之前的最後一個字元；UTF-8、LF、沒有 strip；排除 receipt 區塊、此取材規則與兩個 delimiter。
--- 被雜湊的報告全文開始 ---
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
- command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4 rev-parse HEAD; git status --porcelain; git merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 78d406438682e13f3f2a558af12b378d1c52746f"
  observed: "HEAD 為 78d406438682e13f3f2a558af12b378d1c52746f；status 無輸出；基線祖先檢查 exit 0。"
- command: "cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4/cli && PYTHONDONTWRITEBYTECODE=1 uv run pytest -q"
  observed: "511 passed in 3.92s。"
- command: "cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4/cli && PYTHONDONTWRITEBYTECODE=1 uv run python - <<'PY' ... render_verdict_comment(...) ... PY"
  observed: "對一個 executor/implementation/accepted blocking finding 的 REQUEST_CHANGES 報告，未提供任何 preflight 證據仍輸出 preflight_passed: true 與 counts_toward_escalation: true。"
findings:
- finding_id: "WF-22-CLI4-R1-01"
  severity: major
  blocking: true
  finding_class: implementation
  attribution: executor
  root_cause_id: "unproven-preflight-counting"
  evidence: "cli/src/wf_cli/commands/review_cmd.py 的 run() 未讀取或驗證 preflight event／證據，卻呼叫 render_verdict_comment() 而不傳 preflight_passed；cli/src/wf_cli/review.py 將該參數預設為 true 並寫入結構化帳。上述自跑重現確認合法輸入可得到 true 計數。templates/review-escalation.md §3 第 1 款要求 preflight 已通過且 review 有效才可計數。"
  disposition: "在 lifecycle writer 建立可機械驗證的 preflight 依據；依據不可得時拒絕建立可計數 review 或明確記為不可計數，並補回歸測試。"
first_round:
- note: "首輪，無前輪 accepted blocking finding。"
out_of_scope_findings:
- note: "切片 B 的跨 attempt open set／root-cause occurrence 歷史推導，依派審詞所述解析停機 blocker，未納入本輪 finding。"
- note: "owner_field_at_verdict_write 經 handoff_cmd.py 與 test_owner_snapshot_records_the_reviewer_not_the_executor_under_the_dispatch_convention 證實是裁決時的查核者快照，不足以直接執行 #39 §5 第 3 款；鍵名與散文已誠實防止誤用，保留作 append-only 時點事實合理，但不得宣稱已補足該條款的 owner 證據。"
--- 被雜湊的報告全文結束 ---

## Comment 5262256980 · 2026-08-12T04:24:17Z

<!-- wf-review-event:v1 card_id=WF-22-CLI4 source_sha=78d406438682e13f3f2a558af12b378d1c52746f attempt_id=WF-22-CLI4-e0-78d406438682e13f3f2a558af12b378d1c52746f -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-22-CLI4`　attempt_id：`WF-22-CLI4-e0-78d406438682e13f3f2a558af12b378d1c52746f`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5262195265 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=063d607f… 一次相符。PM 的轉錄調整：self_run 與其餘序列原為零縮排，解析器要求 2 空格縮排，已補縮排；字串內容逐字未變）　escalation_epoch：0
- source_sha：`78d406438682e13f3f2a558af12b378d1c52746f`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T12:24:15+08:00

### self_run（查核者實跑）

- `git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4 rev-parse HEAD; git status --porcelain; git merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 78d406438682e13f3f2a558af12b378d1c52746f`
  - HEAD 為 78d406438682e13f3f2a558af12b378d1c52746f；status 無輸出；基線祖先檢查 exit 0。
- `cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4/cli && PYTHONDONTWRITEBYTECODE=1 uv run pytest -q`
  - 511 passed in 3.92s。
- `cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4/cli && PYTHONDONTWRITEBYTECODE=1 uv run python - <<'PY' ... render_verdict_comment(...) ... PY`
  - 對一個 executor/implementation/accepted blocking finding 的 REQUEST_CHANGES 報告，未提供任何 preflight 證據仍輸出 preflight_passed: true 與 counts_toward_escalation: true。

### findings（1，其中 blocking 1）

- **WF-22-CLI4-R1-01**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`unproven-preflight-counting`
  - evidence：cli/src/wf_cli/commands/review_cmd.py 的 run() 未讀取或驗證 preflight event／證據，卻呼叫 render_verdict_comment() 而不傳 preflight_passed；cli/src/wf_cli/review.py 將該參數預設為 true 並寫入結構化帳。上述自跑重現確認合法輸入可得到 true 計數。templates/review-escalation.md §3 第 1 款要求 preflight 已通過且 review 有效才可計數。
  - disposition：在 lifecycle writer 建立可機械驗證的 preflight 依據；依據不可得時拒絕建立可計數 review 或明確記為不可計數，並補回歸測試。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5262453594 · 2026-08-12T04:55:49Z

## 派審：#9 `WF-22-CLI4` R2

⚠️ 審核對象 **`ruan6047/ai-workflow#9`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4
分支：claude/WF-22-CLI4　　被審 SHA：779e5755c49382522ae1551ab576334604fd14f0
基線：6e6e8abd650c76fa6a2173f5dff35f99038ca1e0（= merge-base origin/main 779e575，已驗為祖先）
iteration：1
```

> **本則為權威。** 任何摘要表格、協調者提示詞或轉述若與本則衝突，一律以本則為準；**值解不開時先回對本則，不要直接停手**。（`origin/main` 現為 `20f2ea3`，不是基線——merge-base 是分叉點，main 前進不會移動它。）

### 一、複驗 R1-01：執行者取「拒絕」而非「記為不可計數」

你的 finding 是對的，執行者不爭辯，並自陳你講得比它的自陳更準：它自陳「第 1 款沒有機械執行者」，你指出的是**沒有執行者卻以事實的語氣寫下它的結論**——往 append-only 事件流裡寫一件沒有任何東西證實過的事。

它取 disposition 的第一支，理由兩個：**後者是洗白路徑**（本該計數的 attempt 只要宣稱拿不到依據就能不進帳，逃生口開在被約束那一方手上等於沒有約束）；且**契約 §1 已明定** preflight 未通過須寫 `preflight-failed` 且不得建立 review event，故「沒有依據卻要下裁決」本來就不是合法狀態。

**PM 曾警告這可能把 escalation 帳整個關掉**，執行者查證後結論相反：閘門**只在第 2～4 款已成立時**才要求依據；`APPROVE` 與只含 governance／coordination／environment 或非 executor 歸屬 finding 的 `REQUEST_CHANGES`，其 counts 因第 2～4 款自身即為 `false`，照常寫入。`M40`（把閘門擴及所有裁決）打死 14 個測試。

**請攻擊**：(a) 那個「只在第 2～4 款成立時才要求」的界線真的擋住癱瘓路徑嗎，還是有你能構造的組合會全面停機？(b) `writer-attested` 這個依據強度——它是**具結不是機器驗證**，執行者如實命名了；具結者身分取自 `gh api user`，而本 repo 只有一個人類帳號。那個具結買到了什麼？

### 二、依指示停下回報的部分，請判斷劃界是否恰當

機器可驗證的 preflight 依據需自事件流讀 `handoff-accepted` 或等價事件，其 writer 是 `handoff_cmd.py` 或新事件型別——**都不在本卡寫入集，執行者未自行擴張**。

### 三、自陳 vs 處置的帳

執行者依 PM 要求寫出區分，**判準是「能在本卡寫入集內關掉的，自陳就不是合格終點」**。本輪關掉 preflight（它承認上一輪停在自陳是失分點）；其餘六項仍為自陳並逐項附「為什麼可以留著」，理由都是執行者落在別人的寫入集或別張卡。

**請判斷那個判準本身是否成立**，以及六項裡有沒有哪一項其實今天就關得掉。

### 四、一個可能污染證據的方法論事故

執行者順帶修好一個**因重構而錨點失效、被 harness 判 SKIP 的舊突變**（`M04`），並記下「**錨點失效的突變等於沒測，這種 SKIP 不能當成通過**」。它上一輪另揭露過 `.pyc` mtime 秒級失效導致 `M27` 誤判（已加清 cache ＋ `PYTHONDONTWRITEBYTECODE=1`）。

**請判斷 40 個突變全 KILLED 是否可信**——有沒有其他條也受同類假象污染而未被發現？

### 五、門檻提醒

本卡 iteration 1，這是**第二個**可計數 attempt，未達 checkpoint 門檻。R1-01 的家族名是 `unproven-preflight-counting`；若你判定它仍開啟，**請沿用該家族名**。

### 六、已知殘留（PM 自審已找到，可判斷處置是否恰當）

`owner_field_at_verdict_write` 經執行者查碼證實裝的是**查核者**而非產出 `source_sha` 的執行者（`handoff --next-stage review --to <查核者>` 先設 owner 欄、裁決在其後才寫），**不足以直接支撐 #39 §5 第 3 款**；你上一輪已於 scope_outside 確認該處置合理。切片 B 仍被 #30 的解析停機擋住。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**（`resolved`／`withdrawn`／仍開啟）並附證據。
2. **五個 schema 欄位自己填**。`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` **多行格式**（`card_id:` 與 `source_sha:` **各自獨立成行**，單行 `key=value` 形式 `doctor` 認不得），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍。**規則若提到起訖 delimiter 的字面，請說清楚是「本規則之後的下一個」。**

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、值含 ` #` 須整個值加引號、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**。非 schema 的頂層鍵會被容忍。


## Comment 5262575326 · 2026-08-12T05:11:40Z

<!-- wf-review-receipt:v1
card_id: WF-22-CLI4
source_sha: 779e5755c49382522ae1551ab576334604fd14f0
report_sha256: 3f167ac693f87b00a72fcd72a9bff561c9e27f10cb6832544fe917c1ce4362bc
-->

取材規則：取材範圍從本規則之後的下一個「--- 被雜湊的報告全文開始 ---」整行之後的第一個字元起，至下一個「--- 被雜湊的報告全文結束 ---」整行之前的最後一個字元止；UTF-8、LF、沒有 strip；排除 receipt 區塊、此取材規則與兩個 delimiter。
--- 被雜湊的報告全文開始 ---
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git rev-parse HEAD; git status --porcelain; git merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD"
    observed: "HEAD=779e5755c49382522ae1551ab576334604fd14f0；工作區乾淨；基線祖先檢查 exit 0；origin/claude/WF-22-CLI4 包含此 SHA。"
  - command: "git archive 779e5755c49382522ae1551ab576334604fd14f0 | tar -x -C /tmp/wf9-r2 && cd /tmp/wf9-r2/cli && PYTHONDONTWRITEBYTECODE=1 uv run pytest -q"
    observed: "525 passed。"
  - command: "git archive 779e5755c49382522ae1551ab576334604fd14f0 | tar -x -C /tmp/wf9-preflight && cd /tmp/wf9-preflight/cli && PYTHONDONTWRITEBYTECODE=1 uv run python -c '<建構 executor implementation accepted blocking finding；以任意摘要建立 writer-attested PreflightAttestation；輸出 derive_counts_toward_escalation>'"
    observed: "validate_preflight_attestation 接受任意未驗證字串；derive_counts_toward_escalation 輸出 True。"
  - command: "cd /tmp/wf9-r2 && PYTHONDONTWRITEBYTECODE=1 python3 scripts/replay_escalation_rules.py"
    observed: "65/65 通過；此腳本是 escalation-resolution 規則回放，非本卡宣稱的 40 條突變 harness，未用來採信該突變聲稱。"
prior_accepted_blocking_findings:
  - finding_id: "WF-22-CLI4-R1-01"
    status: "仍開啟"
    evidence: "R1 的無依據 true 已不再是預設值，缺 --preflight-passed 的可計數裁決會被拒；但 --preflight-passed 只驗非空摘要，任意字串即可使同一類裁決計數為 true，未建立 R1 disposition 要求的可機械驗證 preflight 依據。"
findings:
  - finding_id: "WF-22-CLI4-R2-01"
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: unproven-preflight-counting
    evidence: "cli/src/wf_cli/commands/review_cmd.py 將 --preflight-passed 的任意非空值包成 basis=writer-attested；validation.validate_preflight_attestation 只做非空檢查；PreflightAttestation.passed 只檢查 basis。隔離重現以『任意未驗證字串』作摘要，對 executor/implementation/accepted/blocking finding 仍導出 counts=True。故雖不再預設 true，仍可把未經驗證的具結當成第 1 款已成立，R1-01 的根因未關閉。"
    disposition: "在 lifecycle writer 只接受可從 append-only 事件流重建並逐字驗證的 preflight 依據，例如受管轄的 handoff-accepted 或等價事件連同 source_sha、檢查結果與摘要；缺少該事件時拒絕可計數裁決。若此 writer 不在本卡寫入集，應維持拒絕並把機械事件 writer 交由具該寫入集的卡承接，而不是以 writer-attested 作為計數依據。"
scope_outside_findings:
  - note: "owner_field_at_verdict_write 是裁決時的查核者快照而非 source_sha 執行者；目前命名與說明誠實，且不足以支撐 #39 continued_owner 比對，未納入本輪 finding。"
  - note: "切片 B 的跨 attempt open-set、根因 occurrence 與 checkpoint decision 機械導出仍受既有解析停機限制；本輪未擴大 finding。"
--- 被雜湊的報告全文結束 ---


## Comment 5262665534 · 2026-08-12T05:19:41Z

<!-- wf-review-event:v1 card_id=WF-22-CLI4 source_sha=779e5755c49382522ae1551ab576334604fd14f0 attempt_id=WF-22-CLI4-e0-779e5755c49382522ae1551ab576334604fd14f0 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-22-CLI4`　attempt_id：`WF-22-CLI4-e0-779e5755c49382522ae1551ab576334604fd14f0`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5262575326 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=3f167ac6… 一次相符。本輪四份裁決皆無需 PM 作任何格式調整——區塊零散文、序列已縮排、無 code fence）　escalation_epoch：0
- source_sha：`779e5755c49382522ae1551ab576334604fd14f0`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T13:19:40+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git status --porcelain; git merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD`
  - HEAD=779e5755c49382522ae1551ab576334604fd14f0；工作區乾淨；基線祖先檢查 exit 0；origin/claude/WF-22-CLI4 包含此 SHA。
- `git archive 779e5755c49382522ae1551ab576334604fd14f0 | tar -x -C /tmp/wf9-r2 && cd /tmp/wf9-r2/cli && PYTHONDONTWRITEBYTECODE=1 uv run pytest -q`
  - 525 passed。
- `git archive 779e5755c49382522ae1551ab576334604fd14f0 | tar -x -C /tmp/wf9-preflight && cd /tmp/wf9-preflight/cli && PYTHONDONTWRITEBYTECODE=1 uv run python -c '<建構 executor implementation accepted blocking finding；以任意摘要建立 writer-attested PreflightAttestation；輸出 derive_counts_toward_escalation>'`
  - validate_preflight_attestation 接受任意未驗證字串；derive_counts_toward_escalation 輸出 True。
- `cd /tmp/wf9-r2 && PYTHONDONTWRITEBYTECODE=1 python3 scripts/replay_escalation_rules.py`
  - 65/65 通過；此腳本是 escalation-resolution 規則回放，非本卡宣稱的 40 條突變 harness，未用來採信該突變聲稱。

### findings（1，其中 blocking 1）

- **WF-22-CLI4-R2-01**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`unproven-preflight-counting`
  - evidence：cli/src/wf_cli/commands/review_cmd.py 將 --preflight-passed 的任意非空值包成 basis=writer-attested；validation.validate_preflight_attestation 只做非空檢查；PreflightAttestation.passed 只檢查 basis。隔離重現以『任意未驗證字串』作摘要，對 executor/implementation/accepted/blocking finding 仍導出 counts=True。故雖不再預設 true，仍可把未經驗證的具結當成第 1 款已成立，R1-01 的根因未關閉。
  - disposition：在 lifecycle writer 只接受可從 append-only 事件流重建並逐字驗證的 preflight 依據，例如受管轄的 handoff-accepted 或等價事件連同 source_sha、檢查結果與摘要；缺少該事件時拒絕可計數裁決。若此 writer 不在本卡寫入集，應維持拒絕並把機械事件 writer 交由具該寫入集的卡承接，而不是以 writer-attested 作為計數依據。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5264293600 · 2026-08-12T08:29:35Z

## 派審：#9 `WF-22-CLI4` R3

⚠️ 審核對象 **`ruan6047/ai-workflow#9`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4
分支：claude/WF-22-CLI4　　被審 SHA：1194d5e4c2ad52455c1b2cea83416d4b8036cf66
基線：6e6e8abd650c76fa6a2173f5dff35f99038ca1e0（PM 已重算並驗為祖先）　　iteration：1
```

> **本則為權威**；摘要表格與轉述若衝突以本則為準，**值解不開時先回對本則，不要直接停手**。`origin/main` 現為 `02b5d9a`——merge-base 是分叉點，main 前進不會移動它。**PM 已實測 merge(origin/main, 本分支) → 747 passed 全綠。**

### ⚠️ 門檻：2/3，你這一輪可能觸發

| attempt | finding | `root_cause_id` |
|---|---|---|
| `78d4064` | R1-01 | `unproven-preflight-counting` |
| `779e575` | R2-01 | **同一個** |

`1194d5e` 是**第三個**可計數 attempt。**若你再次產出同家族 finding，第一條件成立、下一輪強制 escalate。請沿用該家族名，不要另起新名。**

**PM 未建 checkpoint，理由須讓你知道**：§5 的 `unique_attempt_count` 必填且要求 `>= 3`，而已落地的 attempt 是 2。硬建會寫出一則違反 schema 的 checkpoint——那正是 #39 抓到 PM 過去七則裡兩則犯的錯。`:61` 的「第三個可計數 attempt 出現**時**先建立」在「出現」指派審前還是裁決落地後之間有歧義，**而消解那個歧義正是 #39 的內容**。PM 不為了看起來合規而製造一則不合規的留痕。**你可以判這個決定是錯的**——那是正當 finding。

### 一、複驗 R2-01：執行者取了第三個形狀

它不辯解，並自陳上一輪「把預設 `true` 換成具結 `true`，而具結只驗非空字串——病灶沒關、只是換了入口」。

它**否決了 disposition 的兩支與 PM 提的中間形狀**，取第三個：`writer-attested` **從列舉刪除**、`--preflight-passed` 旗標**一併刪除**，合法依據只剩 `event-verified`；`counts_toward_escalation` **改三值**，第 2～4 款成立而第 1 款依據不可得時記 **`unavailable`**。

理由逐字：「寫 `true` 是偽造，寫 `false` 是洗白——**兩者是同一種病的兩個方向**」；對 PM 中間形狀（保留 `writer-attested` 但標記為不可計數）的否決是「它讓一個未驗證的具結**做實事**卻宣稱不算數，而且把上一輪自己拒絕過的洗白路徑放回來——**半個依據不該有半個效力**」。

**請攻擊**：(a) 三值真的比兩值誠實嗎，還是把判斷推給了消費者？(b) `counts=true` 宣稱在本 CLI **結構上不可達**——PM 已 grep 確認 `src/` 內 `writer-attested` 只剩兩行說明它被移除的註解、旗標不存在。**請你自己驗，並找有沒有其他路徑能寫出 `true`。**

### 二、三輪未關的證據可見性缺口，這輪關掉了——請驗它是不是真的

前三輪的突變 harness 在 scratchpad，你跑不到。執行者自陳「**自陳大於證據正是打了我三輪的同一個病**」。

本輪把**六條最吃重的 fail-closed 判準搬進 `cli/tests/test_validation.py`**：在 `src` 的臨時複本上改壞原始碼、以子行程驗證判準不成立。每個探針**先斷言 `wf_cli.__file__` 落在複本裡**（避免「以為測到突變版、其實載到原版」），基線探針必須先過否則 KILLED 判定無效。

**`uv run pytest -k mutated` 你就能自己重現。** PM 已實跑得 `6 passed / 520 deselected`。

repo 外 harness 另 35 條全 KILLED；原 M36–M40 針對的碼本輪已移除，**已從 harness 刪除並由 repo 內那六條取代**（錨點失效的突變等於沒測）。

**請攻擊**：那六條真的是「最吃重的」嗎，還是挑了好做的？子行程隔離有沒有漏洞？

### 三、代價，執行者如實算了

**本 repo 今天沒有任何 preflight 事件，故每一則本會計數的裁決都是 `unavailable`——escalation 自動計數在承接卡落地前不可用，包括本卡自己的三振門檻。** `counted_attempts` 為空**不代表執行者沒有累計**，該事實同時寫進事件流散文、`wfcli review` 每次的 stdout 警告，並提供 `escalation_account_unavailable()` 讓消費者拿得到那些 attempt。

閘門本身未壞：測試注入帶 `event-verified` 依據的三個 attempt，驗證第四輪仍因缺 checkpoint 被拒、建了 checkpoint 後放行。

**請判斷**：這個代價可接受嗎？「讀取側的誤讀是這輪唯一剩下的風險，我用可讀的事實去堵它，而不是用一個好看的數字」——這句話買到了什麼？

### 四、承接卡（未自行擴張宣告）

`event-verified` 需 `handoff --next-stage review` 或等價動詞寫出受管轄的 preflight pass event，帶 `source_sha`、檢查結果與摘要，落在 append-only 留言平面。writer 是 `handoff_cmd.py` 或新事件型別，**都不在本卡寫入集**。

### 五、跨卡：#35 判你的 payload 有兩格不合格

`WF-EVENT-MARKER-V2-SCOPE1`（#35，同批送審）實測本卡 `_yaml_scalar` → `_parse_yaml_subset` 的 14 個值，發現**換行與連續空白被靜默摺疊**——「那是**正規化不是逃逸**，寫入端靜默寫出一個與輸入不同的值」。它據此把自己的規則二改為**明文禁止以正規化代替拒收**，並判定「**規則過嚴、該改的是規則**」而非本卡該改。

附帶警告：含三反引號的值今天不破壞區塊**只是因為摺疊把它拉回同一行**，修掉摺疊會讓這保護一起消失。

**PM 已核實那兩支函式確在 `review.py`（本卡寫入集）。請判斷這是否構成本卡的 finding，還是屬 #35 的射程。**

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5264397039 · 2026-08-12T08:39:39Z

<!-- wf-review-receipt:v1
card_id: WF-22-CLI4
source_sha: 1194d5e4c2ad52455c1b2cea83416d4b8036cf66
report_sha256: ffb5e00eac618da193c798d88226617abaf0508b68d13d3ae1440ae824acb4b1
-->

取材規則：取材範圍從本規則之後的下一個「--- 被雜湊的報告全文開始 ---」整行之後的第一個字元起，至下一個「--- 被雜湊的報告全文結束 ---」整行之前的最後一個字元止；UTF-8、LF、沒有 strip；排除 receipt 區塊、此取材規則與兩個 delimiter。
--- 被雜湊的報告全文開始 ---
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4 rev-parse HEAD; git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4 status --porcelain; git -C /Users/ruanruan/Dev/ai-workflow merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 1194d5e4c2ad52455c1b2cea83416d4b8036cf66"
    observed: "HEAD=1194d5e4c2ad52455c1b2cea83416d4b8036cf66；工作區乾淨；基線祖先檢查 exit 0。"
  - command: "git archive 1194d5e4c2ad52455c1b2cea83416d4b8036cf66 | tar -x -C /tmp/aiwf9-review.Fdo4Zh; cd /tmp/aiwf9-review.Fdo4Zh/cli && PYTHONDONTWRITEBYTECODE=1 uv run pytest -q && PYTHONDONTWRITEBYTECODE=1 uv run pytest -k mutated -q"
    observed: "526 passed；突變探針 6 passed、520 deselected。"
  - command: "cd /tmp/aiwf9-review.Fdo4Zh/cli && PYTHONDONTWRITEBYTECODE=1 uv run python -c '<建構 executor implementation accepted blocking finding 並呼叫 derive_counts_toward_escalation 及 render_escalation_facts_block>'"
    observed: "沒有 event-verified preflight 時輸出 counts_toward_escalation=unavailable 與 preflight_passed=unknown。"
prior_accepted_blocking_findings:
  - finding_id: "WF-22-CLI4-R1-01"
    status: "resolved"
    evidence: "R3 原始碼已移除 writer-attested 與 --preflight-passed；src 內無 CLI 輸入路徑可產生 counts_toward_escalation=true，test_no_cli_input_can_produce_a_counting_verdict_today 亦覆蓋此點。"
  - finding_id: "WF-22-CLI4-R2-01"
    status: "resolved"
    evidence: "PREFLIGHT_BASES 僅剩 event-verified 與 not-established；test_preflight_basis_has_no_writer_attested_option_any_more 通過，任意具結不再能導出 true。"
findings:
  - finding_id: "WF-22-CLI4-R3-01"
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: unproven-preflight-counting
    evidence: "templates/review-escalation.md §1 規定 preflight 缺口不得建立 review event，§5 將 preflight_passed 與 counts_toward_escalation 定為布林欄位；目前 review.py 對缺 event-verified 依據仍寫入 review event，且實跑輸出 preflight_passed=unknown、counts_toward_escalation=unavailable。這既不符合既有 schema，也讓本 repo 的可計數退回與第三次 checkpoint 仍只能人工盯帳。"
    disposition: "在 review_cmd 的任何遠端寫入前，缺少可從 append-only preflight event 驗證的依據時 fail closed，不建立 review event；不得以 unknown 或 unavailable 擴充既有布林 schema。受管轄 preflight event writer 應由具 handoff 寫入集的承接卡完成。"
--- 被雜湊的報告全文結束 ---


## Comment 5264596823 · 2026-08-12T08:59:32Z

<!-- wf-review-event:v1 card_id=WF-22-CLI4 source_sha=1194d5e4c2ad52455c1b2cea83416d4b8036cf66 attempt_id=WF-22-CLI4-e0-1194d5e4c2ad52455c1b2cea83416d4b8036cf66 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-22-CLI4`　attempt_id：`WF-22-CLI4-e0-1194d5e4c2ad52455c1b2cea83416d4b8036cf66`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5264397039 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=ffb5e00e… 一次相符。本批六份收據皆採內容錨定或分隔行，各自規則不同，PM 逐份照其規則計算、無需任何格式調整）　escalation_epoch：0
- source_sha：`1194d5e4c2ad52455c1b2cea83416d4b8036cf66`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T16:59:30+08:00

### self_run（查核者實跑）

- `git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4 rev-parse HEAD; git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4 status --porcelain; git -C /Users/ruanruan/Dev/ai-workflow merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 1194d5e4c2ad52455c1b2cea83416d4b8036cf66`
  - HEAD=1194d5e4c2ad52455c1b2cea83416d4b8036cf66；工作區乾淨；基線祖先檢查 exit 0。
- `git archive 1194d5e4c2ad52455c1b2cea83416d4b8036cf66 | tar -x -C /tmp/aiwf9-review.Fdo4Zh; cd /tmp/aiwf9-review.Fdo4Zh/cli && PYTHONDONTWRITEBYTECODE=1 uv run pytest -q && PYTHONDONTWRITEBYTECODE=1 uv run pytest -k mutated -q`
  - 526 passed；突變探針 6 passed、520 deselected。
- `cd /tmp/aiwf9-review.Fdo4Zh/cli && PYTHONDONTWRITEBYTECODE=1 uv run python -c '<建構 executor implementation accepted blocking finding 並呼叫 derive_counts_toward_escalation 及 render_escalation_facts_block>'`
  - 沒有 event-verified preflight 時輸出 counts_toward_escalation=unavailable 與 preflight_passed=unknown。

### findings（1，其中 blocking 1）

- **WF-22-CLI4-R3-01**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`unproven-preflight-counting`
  - evidence：templates/review-escalation.md §1 規定 preflight 缺口不得建立 review event，§5 將 preflight_passed 與 counts_toward_escalation 定為布林欄位；目前 review.py 對缺 event-verified 依據仍寫入 review event，且實跑輸出 preflight_passed=unknown、counts_toward_escalation=unavailable。這既不符合既有 schema，也讓本 repo 的可計數退回與第三次 checkpoint 仍只能人工盯帳。
  - disposition：在 review_cmd 的任何遠端寫入前，缺少可從 append-only preflight event 驗證的依據時 fail closed，不建立 review event；不得以 unknown 或 unavailable 擴充既有布林 schema。受管轄 preflight event writer 應由具 handoff 寫入集的承接卡完成。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5264628916 · 2026-08-12T09:02:50Z

## escalation-checkpoint（第四個可計數 attempt 前）

```yaml
escalation_epoch: 0
trigger_attempt_id: WF-22-CLI4-e0-1194d5e4c2ad52455c1b2cea83416d4b8036cf66
unique_attempt_count: 3
checkpoint_decision: escalate
checkpoint_rationale: |
  第一條件成立。根因家族 unproven-preflight-counting 跨三個 unique attempt：
  78d4064（R1-01）、779e575（R2-01）、1194d5e（R3-01）。依 review-escalation.md §4，
  條件成立時 checkpoint_decision 只能是 escalate。

  數字由指令輸出產生：以 gh 取三則 review event 原文、正則抽 finding_id 與
  root_cause_id 後計 unique attempt 集合，非人工清點。

  第二條件不成立：R1-01 與 R2-01 皆由本輪查核者判 resolved 並附證據
  （PREFLIGHT_BASES 僅剩 event-verified 與 not-established；src 內無 CLI 輸入
  路徑可產生 counts_toward_escalation=true），無前輪 accepted blocking finding
  未被表態。
```

### 這是本卡第一則 checkpoint，而它本該更早出現

依 `review-escalation.md:61`，第三個及其後每個可計數 attempt 出現時應先建立 checkpoint。**本卡第三個 attempt（`1194d5e`）出現前，PM 未建。** 這是 PM 的合規缺口，`attribution: coordinator`，**不追溯補建**（需求方 2026-08-12 明示不補歷史紀錄）。

PM 當時在派審詞裡說明了不建的理由——§5 的 `unique_attempt_count` 必填且要求 `>= 3`，而當時已落地的 attempt 是 2，硬建會寫出一則違反 schema 的 checkpoint。**該理由今天仍成立，但它暴露的是條文的歧義而不是免責**：`:61` 的「第三個可計數 attempt **出現時**先建立」在「出現」指派審前還是裁決落地後之間沒有定義，而 §5 的 `>= 3` 只在後一種讀法下自洽。**兩處條文互相牽制，PM 選了不寫不實資料那一邊。** 消解該歧義屬 `WF-ESCALATION-RESOLUTION-GAP1`（#39）的設計空間。

### 病灶的形狀：三次都是同一件事，而且每次修法都只換入口

| attempt | 當時的機制 | 為什麼沒關掉 |
|---|---|---|
| `78d4064` | `preflight_passed` **預設 `true`** | 往 append-only 事件流寫一件沒有任何東西證實過的事 |
| `779e575` | 改為 **`writer-attested` 具結** | 具結只驗**非空字串**，任意未驗證字串仍導出 `counts=true` |
| `1194d5e` | 移除具結，改 **`unavailable` 三值** | 查核者判它**擴充了 §5 的布林 schema**，且缺依據時**仍建立 review event** |

執行者三輪的自我修正方向是對的（每一輪都比前一輪誠實），**但三次都停在「換一個值」而沒有動「要不要寫」**。本輪查核者的 disposition 正是指向那一點：「**在 `review_cmd` 的任何遠端寫入前，缺少可從 append-only preflight event 驗證的依據時 fail closed，不建立 review event**」。

### 需求方須裁定

第一條件成立，依 §4 本則判 `escalate`。**「escalate 之後維持同執行者還是換人」在契約裡今天仍無事件表示法**（#39 設計中、本批 APPROVE 但尚未合併），故需求方的裁定須另以留言為之，並在 #39 落地後補寫為正式的 `escalation-resolution` 事件。

判斷所需的兩件事實，PM 一併列出而不代為裁定：

1. **真正的修法需要一個不在本卡寫入集的 writer**（`handoff_cmd.py` 或新事件型別）。三輪都撞同一堵牆，而執行者三次都正確地停下回報、未自行擴張宣告。
2. **本輪執行者關掉了三輪未關的證據可見性缺口**——六條 fail-closed 判準搬進 `test_validation.py`，查核者跑 `uv run pytest -k mutated` 可自行重現（PM 與本輪查核者各自實跑得 6 passed）。那是它自己指名的病（「自陳大於證據正是打了我三輪的同一個病」）並且真的治了。

在事件流上，這張卡從本則起是**升級中**。

## Comment 5264676725 · 2026-08-12T09:07:44Z

## 需求方裁定：升級後維持同執行者

同日的 escalation-checkpoint（`issuecomment-5264628916`）依 §4 判 `escalate`——`unproven-preflight-counting` 跨三個 unique attempt（`78d4064` R1-01、`779e575` R2-01、`1194d5e` R3-01），第一條件成立時 `checkpoint_decision` 只能是該值。

**需求方 2026-08-12 裁定：維持同執行者。**

### 判準

**三次撞的是同一堵牆，而那堵牆不在執行者的寫入集內。** 真正的修法需要一個受管轄的 preflight event writer，其落點是 `handoff_cmd.py` 或新事件型別——**都不在本卡宣告內**。執行者三輪**都正確地停下回報、未自行擴張宣告**，那是應該的行為而不是失敗。

**而本輪它關掉了三輪未關的另一件事**：六條 fail-closed 判準搬進 `cli/tests/test_validation.py`，查核者跑 `uv run pytest -k mutated` 可自行重現——PM 與本輪查核者**各自獨立實跑**皆得 6 passed。那是它自己指名的病（「自陳大於證據正是打了我三輪的同一個病」）並且真的治了。同輪它也讓 R1-01 與 R2-01 雙雙被判 `resolved`。

**但這個裁定不是說前三輪沒問題。** 三次的修法都停在「換一個值」（預設 `true` → 具結 `true` → `unavailable`）而沒有動「**要不要寫**」——那是執行者的判斷失誤，重複了三次。本輪 disposition 已明確指向該點。

### 這一輪的期待因此不同

前三輪的規格是「把值改對」，**本輪的規格是「缺依據時不要寫」**。若這一輪仍以調整值或擴充 schema 的方式回應，那將是第四次同家族，需求方會重新評估本裁定。

### 這則裁定今天沒有正式的事件表示法

§4 規定條件成立時只能 `escalate`，而 `escalation-epoch-change` 的理由只有 `replan` 與 `change-executor`——**「維持同執行者」在契約裡沒有表示法**。`WF-ESCALATION-RESOLUTION-GAP1`（#39）已設計 `escalation-resolution` 獨立事件型別補此缺口，**本批查核 APPROVE 但尚未合併**。

**故本則是散文留痕，不是事件。** #39 落地後應補寫為正式事件（`resolution_basis: fresh-ruling`、`continued_owner` 為當前執行者、`resolved_by: ruan6047`、`authorization_binding: structurally-vacuous`）。在那之前，事件流上這張卡仍是**升級中**——本則不改變那個事實，只記錄需求方對它的處置。

## Comment 5264781873 · 2026-08-12T09:18:03Z

## PM 更正：#39 從未被 APPROVE

本卡同日的[需求方裁定留言](https://github.com/ruan6047/ai-workflow/issues/9#issuecomment-5264676725)寫著：

> `WF-ESCALATION-RESOLUTION-GAP1`（#39）已設計 `escalation-resolution` 獨立事件型別補此缺口，**本批查核 APPROVE 但尚未合併**。

**「本批查核 APPROVE」是錯的。** 實況：

- #39 的交付狀態為 **🔍待查核**，iteration 1；
- 其 `b039c0b`（R1-001 的修法）**沒有任何 review event**——`gh issue view 39 --json comments | grep -c "source_sha=b039c0b…"` 回 **0**；
- 該卡唯一一次查核是 R1，結果是 **REQUEST_CHANGES**（`core_pain_resolved: yes` 但 1 blocking）。PM 應是把那次的 `core_pain_resolved: yes` 誤記成 APPROVE。

`attribution: coordinator`。未追溯編輯原留言；本則為前向更正。

### 對本卡裁定的影響：無

「維持同執行者」的裁定依據是三次撞的是同一堵牆而那堵牆不在執行者寫入集內、以及本輪關掉了證據可見性缺口——**兩者都與 #39 的查核狀態無關**。

**受影響的是那句話的後半**：「#39 落地後應補寫為正式 `escalation-resolution` 事件」仍然成立，但**落地的時程比 PM 當時暗示的遠**——它還要先通過查核、可能還有修法輪次，然後才合併。在那之前，本裁定與 #25 的同型裁定都只是散文留痕。

## Comment 5264959552 · 2026-08-12T09:35:23Z

## PM 記錄：`cli.py` 退出宣告的一個殘餘

執行者答覆不需要 `cli.py` 後，PM 已將它退出本卡宣告（op `b357343c`）。**但退出宣告不等於分支不碰它。**

實測：`git diff --name-only 6e6e8ab..04c8e62 -- cli/src/wf_cli/cli.py` 仍回 1 檔——`2ba565a` 的那四行（`checkpoint_cmd` 的 import ＋ 註冊呼叫 ＋ 兩行註解）留在分支歷史裡，合併時會落地。

**兩者的區別要講清楚：**

- **宣告**管的是「**我還會寫哪些檔**」。執行者確認不會再寫 `cli.py`，所以退出是準確的。
- **分支內容**是既成事實。`WF-ORCHESTRATION-RECONCILE1`（#16）§9 的 B／E／K 三張新動詞卡現在**可以宣告** `cli.py` 了，但它們的分支與本卡的分支**都會改到同一個檔**——那是**合併順序的相依**，不是宣告衝突。

**後合併的一方要處理重疊。** 三張新卡各自要加自己的 import 與註冊呼叫，git 多半能乾淨合併（不同行），但若行相鄰就會衝突。

### 執行者提出的正解，PM 認為對

> 建議把註冊清單移到 `commands/__init__.py`（目前 0 行）成為一個顯式 tuple，`cli.py` 改為迭代它。之後每張新動詞卡只需在 `__init__.py` 追加一行 ＋ 自己的新檔，衝突面從「改兩個區塊」降為「**append 一行**」，而 append 是最容易合併的形狀。

它並**刻意不建議 `pkgutil` 自動探索**：「那會讓註冊集合變成隱式且開放——與本 repo 一貫的『顯式、封閉鍵集合、fail-closed』紀律相反（同 marker 鍵集合封閉的理由），且 help 的動詞順序會變成檔案系統順序。**用便利換掉可稽核性，在這個 repo 裡是錯的方向。**」

**排程事實**（執行者指名，非其要求）：該重構本身需要 `cli.py` ＋ `commands/__init__.py`，**應排在 B／E／K 之前**；若不做，那三張必須序列化派工。

PM 尚未就此開卡，留給需求方裁定。

## Comment 5264978555 · 2026-08-12T09:37:20Z

## 需求方裁定：本卡通過查核後**延後合併**

執行者於 `04c8e62` 的修法會使 `wfcli review` 在 preflight event writer 落地前**寫不進任何裁決**——不只是可計數的那些。執行者已如實算出這個代價並提供替代路徑（查核證據走 `handoff-contract.md` §3.1.2 的收據與報告全文、格式自檢走 `--validate-only`），**但「把裁決寫進狀態面」這件事會停**。

**需求方 2026-08-12 裁定：本卡通過查核後先不合併**，等在飛卡（#38／#39／#42／#48 及其後續）的裁決都轉錄完成，再併它，並同時開 preflight event writer 的承接卡。

### 判準

轉錄裁決是本專案今天唯一把跨家族查核結果寫進狀態面的路徑。先合併會讓**所有在飛卡的裁決無處可寫**，而那些卡的查核已經在進行中——等於用一張卡的正確性換掉其餘全部卡的可稽核性。

**這不是對修法的保留。** 執行者撤回上一輪反對「維持拒絕」的理由，其依據 PM 認為成立且比預期硬：§5:168 的 `preflight_passed` 是**字面 `true`** 而非 `<boolean>`（對照同區塊的 `escalation_epoch: <integer>`、`counts_toward_escalation: <boolean derived from §3>` 即知那不是型別佔位），**斷不出 `true` 的事件不是合格的 review event**。所以 `unknown`／`unavailable` 從一開始就不是「比較誠實的值」，是擴充了一個不該被擴充的欄位。

延後的是**合併時機**，不是對交付物的評價。

### 這也使一件事變成前置而非後續

**preflight event writer 的承接卡從「之後再說」變成「#9 合併的前置」。** 它需要 `handoff_cmd.py` 或新事件型別，不在本卡寫入集；執行者三輪都正確地停下回報未自行擴張。PM 將在本卡通過查核後開該卡，並把兩者的順序寫進卡面。

## Comment 5265392417 · 2026-08-12T10:17:57Z

<!-- wf-review-receipt:v1
card_id: WF-22-CLI4
source_sha: 1194d5e4c2ad52455c1b2cea83416d4b8036cf66
report_sha256: 7002695fa48b1c312e085501891b7baa27c741b93551f65b3a84315a61c86cd8
-->

取材規則：取材範圍從本規則之後的下一個「--- 被雜湊的報告全文開始 ---」整行之後的第一個字元起，至下一個「--- 被雜湊的報告全文結束 ---」整行之前的最後一個字元止；UTF-8、LF、沒有 strip；排除 receipt 區塊、此取材規則與兩個 delimiter。
--- 被雜湊的報告全文開始 ---
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C /Users/ruanruan/Dev/ai-workflow rev-parse 1194d5e4c2ad52455c1b2cea83416d4b8036cf66; git -C /Users/ruanruan/Dev/ai-workflow merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 1194d5e4c2ad52455c1b2cea83416d4b8036cf66"
    observed: "被審 SHA 存在；基線祖先檢查 exit 0。"
  - command: "git archive 1194d5e4c2ad52455c1b2cea83416d4b8036cf66 | tar -x -C /tmp/aiwf-wf22.JOYmwj; cd /tmp/aiwf-wf22.JOYmwj/cli && PYTHONDONTWRITEBYTECODE=1 uv run pytest -q && PYTHONDONTWRITEBYTECODE=1 uv run pytest -k mutated -q"
    observed: "526 passed；突變探針 6 passed、520 deselected。"
  - command: "cd /tmp/aiwf-wf22.JOYmwj/cli && PYTHONDONTWRITEBYTECODE=1 uv run python -c '<以 executor implementation accepted blocking finding 呼叫 derive_counts_toward_escalation 與 render_escalation_facts_block>'"
    observed: "無 event-verified preflight 依據時推導 unavailable，渲染 preflight_passed=unknown 與 counts_toward_escalation=unavailable。"
prior_accepted_blocking_findings:
  - finding_id: "WF-22-CLI4-R1-01"
    status: "resolved"
    evidence: "PREFLIGHT_BASES 已移除 writer-attested，且可計數裁決不再由任意具結產生 true。"
  - finding_id: "WF-22-CLI4-R2-01"
    status: "resolved"
    evidence: "src 內僅保留 writer-attested 已移除的說明；--preflight-passed 不存在，六條 repo 內突變探針通過。"
findings:
  - finding_id: "WF-22-CLI4-R3-01"
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: unproven-preflight-counting
    evidence: "templates/review-escalation.md 的 event schema 將 preflight_passed 寫成字面 true，counts_toward_escalation 為 boolean；1194d5e 仍在缺 event-verified 依據時寫入 review event，實測渲染 unknown 與 unavailable。review-escalation.md §1 又規定 preflight 缺口不得建立 review event。"
    disposition: "在 review_cmd 的任何遠端寫入前，缺少可從 append-only preflight event 驗證的依據時 fail closed，不建立 review event；不得以 unknown 或 unavailable 擴充既有欄位。受管轄 preflight event writer 應由具 handoff 寫入集的承接卡完成。"
--- 被雜湊的報告全文結束 ---

## Comment 5265662315 · 2026-08-12T10:45:11Z

## ⚠️ PM 更正：本卡上一則派審詞的 SHA 是舊的，本輪裁決不予轉錄

**這是 Coordinator 的錯誤，重複了三次（本卡、#38、#42）。**

執行者交回修法後，PM 執行了 `wfcli handoff`（設定狀態面 SHA），**但沒有補發新的派審詞**。Issue 上最後一則「## 派審：」仍載著前一輪的 SHA。

實測：

```
本卡最後一則派審詞　被審 SHA：1194d5e4c2ad52455c1b2cea83416d4b8036cf66
實際 handoff／worktree HEAD：04c8e6211576e786a01afaae69cfb5fbe756bbe1
```

### 而 PM 同時指定了錯的來源當權威

PM 給協調者的提示詞表格列的是 **`04c8e6211576e786a01afaae69cfb5fbe756bbe1`（正確）**，但同一份提示詞逐字寫著「**權威在 Issue 上，取最後一則派審詞**」。

**兩個來源不一致，而 PM 指定了錯的那個。**

⚠️ **這正是 `WF-DISPATCH-PRECHECK1`（#38）那張卡的主題**——它的 §1「權威來源只有一個」就是為了治這個病，而 PM 在派它去審的過程中犯了同一個病。

`attribution: coordinator`。

### 本輪裁決不予轉錄的理由

查核者的 `self_run` 逐字為 `git archive 1194d5e4c2ad52455c1b2cea83416d4b8036cf66 | tar -x …`——**它查核的是上一輪的交付**，不是 `04c8e62`。

`04c8e62` 才是 R3-01 的修法所在：它移除了 `writer-attested`／`--preflight-passed`、把 `counts_toward_escalation` 改回布林、加了 `check_preflight_event_present` 寫入前閘門。**查核者沒有看到那些改動**，其 R3-01「仍在缺依據時寫入 review event」描述的是 `1194d5e` 的狀態。

**故本輪裁決不寫入本卡的 review event。** 這不是對查核者的保留——它依 PM 指定的權威來源行事，且其對 `1194d5e` 的判定正確。**責任全在 PM。**

### escalation 帳的影響

本輪**不計為可計數 attempt**（`review-escalation.md` §1：無效查核不得建立 review event）。同日 checkpoint（`issuecomment-5264628916`）判定的三次同家族**維持不變**，需求方「維持同執行者」的裁定亦不受影響。

### 下一步

PM 將補發對齊 `04c8e62` 的派審詞。**執行者無須任何動作**——交付物本身未被評價。


## Comment 5265672616 · 2026-08-12T10:46:14Z

## 派審：#9 `WF-22-CLI4` R4（補發，對齊實際交付 SHA）

⚠️ 審核對象 **`ruan6047/ai-workflow#9`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4
分支：claude/WF-22-CLI4　　被審 SHA：04c8e6211576e786a01afaae69cfb5fbe756bbe1
基線：6e6e8abd650c76fa6a2173f5dff35f99038ca1e0（PM 已重算並驗為祖先）　　iteration：3
```

> ⚠️ **權威來源的更正（PM 上一輪犯的錯）**：本則派審詞與 Issue Log 上最後一筆 `handoff` 事件的 `SHA` **必須一致**。上一輪 PM 做了 handoff 卻沒補發派審詞，導致兩者不符——一位查核者因此審了舊產物，另一位正確地拒審。**若你發現本則所載 SHA 與最後一筆 handoff 事件的 SHA 不符，以 handoff 事件為準並回報該不符**（那是 PM 的錯，不是你的判斷失誤）。

> **上一輪的裁決不予採計**：那一輪查核者依 PM 指定的權威來源審了 `1194d5e`（前一輪交付），其判定對該 SHA 正確但不適用於 `04c8e62`。**該輪不計為可計數 attempt**，詳見 `issuecomment-5265662315`。

`origin/main` 現為 `e8a638c`。**PM 已實測 merge(origin/main, 本分支) 全綠。**

### ⚠️ 門檻已成立，且本輪規格與前三輪不同

`unproven-preflight-counting` 跨**三個** unique attempt（`78d4064`／`779e575`／`1194d5e`），checkpoint 判 `escalate`（`issuecomment-5264628916`），需求方裁定**維持同執行者**，判準是「三次撞的是同一堵牆，而那堵牆不在執行者寫入集內」。

**但需求方明示該裁定不是說前三輪沒問題**：三次修法都停在「換一個值」（預設 `true` → 具結 `true` → `unavailable`）而**沒有動「要不要寫」**。

**前三輪的規格是「把值改對」，本輪的規格是「缺依據時不要寫」。**

### 一、執行者撤回了自己上一輪的反對，依據是重讀契約

它上一輪反對「維持拒絕」，理由是「拒絕等於把真實發生的查核從狀態面抹掉」。**本輪它撤回該理由**：

> §5:168 的 `preflight_passed` 是**字面 `true`** 不是 `<boolean>`——對照同區塊的 `escalation_epoch: <integer>`、`counts_toward_escalation: <boolean derived from §3>` 即知那不是型別佔位。**斷不出 `true` 的事件不是合格的 review event。**

並自己推翻另一半：查核仍留在 `handoff-contract.md` §3.1.2 的收據與報告全文（**那正是為「查核者無法執行 `wfcli`」設計的證據面**），被拒的只有**狀態面的裁決事件**，而狀態面本來就要求 preflight 已通過。

**所以 `unknown`／`unavailable` 從一開始就不是「比較誠實的值」，是擴充了一個不該被擴充的欄位。**

**請攻擊**：(a) 這個重讀成立嗎——**請自己讀 §5:168 與同區塊的型別佔位對照**；(b) 「收據是為查核者無法執行 wfcli 設計的證據面」這個論證，足以支撐「拒絕寫入不抹掉查核」嗎？

### 二、落地四件

寫入前閘門 `check_preflight_event_present`（缺依據 → exit 2，**一則留言不寫、交付狀態與 body 均不動**）；新增 `preflight_basis_from_body` 讀取器（adapter 側只讀不寫，四項逐字比對，`source_sha` 給出免時鐘新鮮性）；`counts_toward_escalation` **回到布林、三值列舉整組移除**、讀取側對擴充值一律判讀不懂；**無依據時整個帳區塊不渲染**（省略＝不作任何宣稱）。

### 三、⚠️ 代價比上一輪大得多，執行者明說

**本 repo 沒有 preflight event writer，故在承接卡落地前 `wfcli review` 寫不進任何裁決——不只是可計數的那些。**

替代路徑：查核證據走 §3.1.2 收據、格式自檢走 `--validate-only`（不受閘門影響）。讀取器已備妥，承接卡讓該事件存在後整條鏈自動生效、本檔不需再改。

**需求方已據此裁定本卡通過查核後延後合併**（`issuecomment-5264978555`）——該裁定針對**合併時機**而非交付物評價。

**請判斷這個代價可接受嗎**，以及「延後合併」是否是正確的處置。

### 四、一個受寫入集約束的設計決定，執行者主動報備

`render_verdict_comment` 在無依據時**選擇省略帳區塊而非拋錯**，因為 `test_doctor.py`（**不在其寫入集**）會不帶 preflight 呼叫它，硬性拒絕會逼它改該檔。它論證省略是安全的——缺帳區塊的事件會被 `build_issue_event_history` 判為未知、閘門照樣 fail-closed；真正的拒絕在 `review_cmd` 與兩道內部不變式上。

**請判斷這個妥協是否留下了洞。**

### 五、驗證

基線自跑 merge-base `6e6e8ab` = 437／ruff 9；本分支 526 → **528** 全綠、ruff **9**、**repo 內突變 8 條全 KILLED**（`uv run pytest -k mutated` 你可自行重現）。寫入集本輪動六檔，marker 字面 0。

⚠️ **宣告變更**：PM 已將 `cli.py` 退出本卡宣告（op `b357343c`），依據是執行者實測答覆其全部 `cli.py` 改動就是 `2ba565a` 的四行且不會再寫。**但分支歷史仍含那四行、合併時會落地**——退出解開的是宣告鎖，不是合併重疊。`DEV-CLI-VERB-REGISTRY1`（#53，**本批已 APPROVE**）與本卡在 `cli.py` 上雙向衝突，其查核者確認「本卡可先合，#9 解除延後後須在 main 上解衝突並 append `checkpoint_cmd`」。

### 六、對 #35 的表態（執行者主動，未改碼）

同意 #35 判定其 `_yaml_scalar` → `_parse_yaml_subset` 的摺疊是**正規化不是逃逸**且**該改的是規則**，理由是其用法只送單行 token、摺疊對它們是恆等，真正的多行值走區塊純量不經該函式。#35 已 APPROVE 併入 `e8a638c`。**若你持不同判定，它請求由需求方裁定歸屬而非在本卡再開一套規則。**

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5265793325 · 2026-08-12T10:58:52Z

## ⛔ PM 暫停本輪派審：#53 已合併，本分支與 `main` 產生文字衝突

`DEV-CLI-VERB-REGISTRY1`（#53）已於本日合併，`origin/main` 由 `e8a638c` 前進至 `e1b33d8`。

我剛以 `git merge-tree --write-tree e1b33d8 04c8e621…` 實測，結果為 **CONFLICT (content): `cli/src/wf_cli/cli.py`**。本分支那四行 `checkpoint_cmd` 的 import 與註冊，其落腳的兩個區塊在 main 上**已不存在**——註冊清單改成了 `commands/__init__.py` 的顯式 tuple。

**因此上一則派審詞（`issuecomment-5265672616`，SHA `04c8e621…`）作廢，請勿依它進行查核。** 拿去審會得到一個合併不進 main 的產物，而那正是本專案 8/12 讓 main 變紅的形狀。

### 這不是退回，是前置變更

R4 的裁決尚未作出，本輪不計 iteration、不寫 review event。需要的是**在新基線上重做一次交付**：

- 解 `cli.py` 衝突取 main 側（丟棄那 4 行）
- 在 `cli/src/wf_cli/commands/__init__.py` 的 tuple **append 一行** `"checkpoint_cmd"`
- 其餘 7 個檔與 main 零衝突（PM 已驗）

#53 的執行者已在拋棄式衝突樹上把這條路徑跑完，得 **793 passed**，且 `--help` 的動詞順序與本分支原本的輸出**逐字相同**。它並實測「只解文字衝突而忘了 append 那行」是 **fail-closed（13 紅，含本卡自己的 11 個測試）**，不是靜默壞掉。

另一件 #53 執行者發現、與本卡直接相關的事：**`checkpoint_cmd` 一個模組註冊了兩個動詞**（`checkpoint` 與 `contract-baseline`，函式名為 `run_checkpoint`／`run_contract_baseline` 而非 `run`）。它第一版測試釘死了「剛好一個動詞」與「func 必須叫 `run``」，那會讓本卡合併時無謂轉紅；**已在 #53 交付前放寬為「至少一個動詞」＋「每個動詞派到自己模組」**。本卡的寫入集一個字沒被動到。

### 待需求方裁定

重做交付後受審 SHA 會變，等於本卡再走一輪查核。是否現在派執行者處理，PM 不自行決定。


## Comment 5265981027 · 2026-08-12T11:18:48Z

## 派審：#9 `WF-22-CLI4` R4（改基線重做後補發，取代 `issuecomment-5265672616`）

⚠️ 審核對象 **`ruan6047/ai-workflow#9`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-22-cli4
分支：claude/WF-22-CLI4　　被審 SHA：9c8036329821fe1fdaf38b648edf6a529c36e139
基線：e1b33d8984425901de400afeb227d5df67d07212（PM 已重算並驗為祖先）　　iteration：3
```

> **權威來源**：本則與本 Issue Log 最後一筆 `handoff` 事件的 `SHA` **必須一致**。不符時**以 handoff 事件為準並回報該不符**。
>
> **本卡本日有兩則作廢的派審詞**：`issuecomment-5265672616`（SHA `04c8e621`）因 #53 合併而作廢，PM 已於 `issuecomment-5265793325` 貼出暫停；更早一則所載 SHA 亦為舊值。**只認上面這個 SHA。**

### 零、本輪不是查核退回，R4 的裁決尚未作出

`DEV-CLI-VERB-REGISTRY1`（#53）本日合併，把 9 個動詞的註冊清單從 `cli.py` 的兩處編輯收斂成 `commands/__init__.py` 的顯式 tuple。本分支那四行 `checkpoint_cmd` 註冊的落腳區塊因此消失，`merge-tree` 對新 main 為 CONFLICT。R4 因此重做交付，**上一輪未寫 review event、不計 iteration**。

**執行者以 merge 而非 rebase 處理**：`04c8e621` 已推送，rebase 會改寫已推送 commit 並需要 force-push。`9c80363` 的 parents = `04c8e621` + `e1b33d8`。

**PM 已複驗**：`merge-base(origin/main, 9c80363)` = `e1b33d8`（即現行 main）；對 main `merge-tree` **CLEAN**；遠端分支 tip 與被審 SHA 一致；push 為非 force（`04c8e62..9c80363`）。

執行者宣稱：`cli.py` 兩個 hunk 皆取 main 側，解完與 `origin/main:cli/src/wf_cli/cli.py` **byte-identical**；其餘 7 檔對 `04c8e621` 逐檔 `git diff --quiet` 零變動。**這兩項請自行複驗**，它們決定了「本輪只做基線遷移、未夾帶實質改動」這個宣稱成不成立。

驗證：`pytest` **793 passed**（與 #53 執行者在拋棄式衝突樹上預測的數字完全相同）；`test_cli_registry.py` 44 passed，放寬後的四項對本卡兩個動詞零摩擦、**未動該檔一個字**。

### 零之二、執行者部分反證了 #53 的一個承重宣稱，請一併裁決

#53 的核心賣點是「每張新動詞卡只需 **append 一行**」。**本卡是那個結構推論的第一個真實實例，而執行者的結論是它比實際契約窄：**

```
基線 (04c8e62)            : [… handoff, review, checkpoint, contract-baseline, doctor, snapshot]
本次（插在 review_cmd 後）: [… handoff, review, checkpoint, contract-baseline, doctor, snapshot]  MATCH
若 append 到 tuple 尾端   : [… handoff, review, doctor, snapshot, checkpoint, contract-baseline]  MISMATCH（index 7 起）
```

故實際改的是**插在 `review_cmd` 之後**，理由是本卡的驗收要求 `--help` 逐字相同，而 `checkpoint` 有語意上的歸屬位置（escalation 帳緊鄰查核裁決）。執行者主張**機制本身無缺陷**（不論 append 或插入都只動 tuple 一處，不會回到共改 `cli.py` 兩處的舊衝突形狀），窄的是那句話。

**請裁示**：(a) 這個插入是否確實維持 `--help` **全文** byte-identical，還是只有動詞順序相同？(b) 「機制無缺陷、只是措辭窄」這個區分成立嗎——若三張後續動詞卡都需要插入而非 append，#53 宣稱消除的衝突是否真的被消除了？

### 零之三、執行者指名未修的兩件事

1. **本 repo 沒有 ruff 這個依賴，也沒有任何 ruff 設定或 CI**。`uv run ruff check` 直接 `Failed to spawn: ruff`，執行者改用 `uvx ruff`（0.16.2 預設規則）。無 `ruff.toml`／`[tool.ruff]`／`.github/`。**意謂本 repo 所有卡面的「push 前跑 ruff」目前沒有可執行的定義。**
2. `cli/tests/test_checkpoint.py:6:1 I001` 為**本分支自帶**（非合併解法造成）；同規則在 main 上已有 12 筆，判為既有噪音未修。

### 一、執行者撤回了自己上一輪的反對，依據是重讀契約

它上一輪反對「維持拒絕」，理由是「拒絕等於把真實發生的查核從狀態面抹掉」。**本輪它撤回該理由**：

> §5:168 的 `preflight_passed` 是**字面 `true`** 不是 `<boolean>`——對照同區塊的 `escalation_epoch: <integer>`、`counts_toward_escalation: <boolean derived from §3>` 即知那不是型別佔位。**斷不出 `true` 的事件不是合格的 review event。**

並自己推翻另一半：查核仍留在 `handoff-contract.md` §3.1.2 的收據與報告全文（**那正是為「查核者無法執行 `wfcli`」設計的證據面**），被拒的只有**狀態面的裁決事件**，而狀態面本來就要求 preflight 已通過。

**所以 `unknown`／`unavailable` 從一開始就不是「比較誠實的值」，是擴充了一個不該被擴充的欄位。**

**請攻擊**：(a) 這個重讀成立嗎——**請自己讀 §5:168 與同區塊的型別佔位對照**；(b) 「收據是為查核者無法執行 wfcli 設計的證據面」這個論證，足以支撐「拒絕寫入不抹掉查核」嗎？

### 二、落地四件

寫入前閘門 `check_preflight_event_present`（缺依據 → exit 2，**一則留言不寫、交付狀態與 body 均不動**）；新增 `preflight_basis_from_body` 讀取器（adapter 側只讀不寫，四項逐字比對，`source_sha` 給出免時鐘新鮮性）；`counts_toward_escalation` **回到布林、三值列舉整組移除**、讀取側對擴充值一律判讀不懂；**無依據時整個帳區塊不渲染**（省略＝不作任何宣稱）。

### 三、⚠️ 代價比上一輪大得多，執行者明說

**本 repo 沒有 preflight event writer，故在承接卡落地前 `wfcli review` 寫不進任何裁決——不只是可計數的那些。**

替代路徑：查核證據走 §3.1.2 收據、格式自檢走 `--validate-only`（不受閘門影響）。讀取器已備妥，承接卡讓該事件存在後整條鏈自動生效、本檔不需再改。

**需求方已據此裁定本卡通過查核後延後合併**（`issuecomment-5264978555`）——該裁定針對**合併時機**而非交付物評價。

**請判斷這個代價可接受嗎**，以及「延後合併」是否是正確的處置。

### 四、一個受寫入集約束的設計決定，執行者主動報備

`render_verdict_comment` 在無依據時**選擇省略帳區塊而非拋錯**，因為 `test_doctor.py`（**不在其寫入集**）會不帶 preflight 呼叫它，硬性拒絕會逼它改該檔。它論證省略是安全的——缺帳區塊的事件會被 `build_issue_event_history` 判為未知、閘門照樣 fail-closed；真正的拒絕在 `review_cmd` 與兩道內部不變式上。

**請判斷這個妥協是否留下了洞。**

### 五、驗證

基線自跑 merge-base `6e6e8ab` = 437／ruff 9；本分支 526 → **528** 全綠、ruff **9**、**repo 內突變 8 條全 KILLED**（`uv run pytest -k mutated` 你可自行重現）。寫入集本輪動六檔，marker 字面 0。

⚠️ **宣告變更**：PM 已將 `cli.py` 退出本卡宣告（op `b357343c`），依據是執行者實測答覆其全部 `cli.py` 改動就是 `2ba565a` 的四行且不會再寫。**但分支歷史仍含那四行、合併時會落地**——退出解開的是宣告鎖，不是合併重疊。`DEV-CLI-VERB-REGISTRY1`（#53，**本批已 APPROVE**）與本卡在 `cli.py` 上雙向衝突，其查核者確認「本卡可先合，#9 解除延後後須在 main 上解衝突並 append `checkpoint_cmd`」。

### 六、對 #35 的表態（執行者主動，未改碼）

同意 #35 判定其 `_yaml_scalar` → `_parse_yaml_subset` 的摺疊是**正規化不是逃逸**且**該改的是規則**，理由是其用法只送單行 token、摺疊對它們是恆等，真正的多行值走區塊純量不經該函式。#35 已 APPROVE 併入 `e8a638c`。**若你持不同判定，它請求由需求方裁定歸屬而非在本卡再開一套規則。**

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5266894010 · 2026-08-12T12:36:52Z

<!-- wf-review-receipt:v1
card_id: WF-22-CLI4
source_sha: 9c8036329821fe1fdaf38b648edf6a529c36e139
report_sha256: 7ad9317f344130125497e3c211bd6a9e60b06868007244e9721993d5817256bb
-->

取材規則：起點是本規則之後的下一個「--- 被雜湊的報告全文開始 ---」整行之後的第一個字元；終點是下一個「--- 被雜湊的報告全文結束 ---」整行之前的最後一個字元。UTF-8、LF、沒有 strip；排除 receipt 區塊、此取材規則與兩個 delimiter。

--- 被雜湊的報告全文開始 ---
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "gh issue view 9 --repo ruan6047/ai-workflow --json body -q .body | grep handoff | tail -1; git rev-parse HEAD; git merge-base --is-ancestor e1b33d8984425901de400afeb227d5df67d07212 HEAD"
    observed: "最後 handoff SHA 與 HEAD 均為 9c8036329821fe1fdaf38b648edf6a529c36e139；fork point 祖先檢查 exit 0。"
  - command: "git archive 9c8036329821fe1fdaf38b648edf6a529c36e139 | tar -x -C /tmp/aiwf9-r4test.KRkJnh; cd /tmp/aiwf9-r4test.KRkJnh/cli && PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -k mutated"
    observed: "8 passed，785 deselected；隔離式 archive 樹。"
  - command: "cd /tmp/aiwf9-r4.59ayrR/cli && PYTHONDONTWRITEBYTECODE=1 uv run python -c preflight_basis_from_body_probe"
    observed: "僅含 wf_preflight_pass v1、card_id、source_sha、preflight_passed true 的任意 YAML 留言被解析為 PreflightBasis(basis=event-verified, source_event=(URL 未提供))，check_preflight_event_present 通過。"
  - command: "git archive 04c8e6211576e786a01afaae69cfb5fbe756bbe1 cli | tar -x -C disposable-tree; cmp --help-output"
    observed: "04c8e621 與 9c803632 的 CLI help 全文 cmp exit 0；checkpoint_cmd 插在 review_cmd 後維持既有順序。"
prior_accepted_blocking_findings:
  - finding_id: "WF-22-CLI4-R1-01"
    status: "resolved"
    evidence: "已移除無依據預設 true；PREFLIGHT_BASES 僅保留 event-verified 與 not-established，且 8 條 repo 內突變測試通過。"
  - finding_id: "WF-22-CLI4-R2-01"
    status: "resolved"
    evidence: "writer-attested 與 CLI 輸入路徑已移除；任意具結不再是合法 basis。"
  - finding_id: "WF-22-CLI4-R3-01"
    status: "still_open"
    evidence: "check_preflight_event_present 已在遠端寫入前拒絕缺依據，但 preflight_basis_from_body 將任意符合四個文字欄位的 Issue 留言視為 event-verified，未確認 handoff-accepted 或等價 lifecycle event 的 event_id、actor、occurred_at、type 或受保護索引。"
findings:
  - finding_id: "WF-22-CLI4-R4-01"
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: "unproven-preflight-counting"
    evidence: "在 source SHA 的隔離 archive 中，直接把任意 YAML body 傳給 preflight_basis_from_body：wf_preflight_pass v1、card_id WF-22-CLI4、該 source_sha、preflight_passed true。函式回傳 event-verified，即使 event_url 缺失；check_preflight_event_present 隨即通過。這不是 templates/review-escalation.md §5 所要求的 handoff-accepted 或等價 preflight pass lifecycle event，也不符合 canonical §4.1 要求的 event_id、type、actor、occurred_at 與 append-only lifecycle writer。"
    disposition: "讀取器必須只採信可驗證為受管轄 handoff-accepted 或已定義等價 lifecycle event 的來源，並驗證其必要事件身分與 source_sha；在該 event writer 和其可驗證格式落地前維持拒絕寫入。補測試證明任意一般 Issue 留言、缺 event_url 或缺 lifecycle event 身分的四欄 YAML 一律不能建立 preflight basis。"
out_of_scope_findings:
  - note: "R4 基線遷移本身保持 CLI help 全文相同；checkpoint_cmd 的插入而非 tuple 尾端 append 證實 help 順序契約，但未造成此卡新增 blocking finding。"
  - note: "本 repo 未設定可由 uv run 執行的 ruff 與 test_checkpoint.py 的既有 I001 屬環境或既有噪音；不納入本輪 finding。"
--- 被雜湊的報告全文結束 ---

## Comment 5267067602 · 2026-08-12T12:53:25Z

<!-- wf-review-event:v1 card_id=WF-22-CLI4 source_sha=9c8036329821fe1fdaf38b648edf6a529c36e139 attempt_id=WF-22-CLI4-e0-9c8036329821fe1fdaf38b648edf6a529c36e139 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-22-CLI4`　attempt_id：`WF-22-CLI4-e0-9c8036329821fe1fdaf38b648edf6a529c36e139`
- 查核者：GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5266894010 未經編輯，PM 依其取材規則（delimiter「被雜湊的報告全文開始/結束」、strip 前後換行）回讀重算 report_sha256=7ad9317f… 相符。⚠️ 首次寫入嘗試遇 GitHub 504 Gateway Timeout 中斷於 field-list 階段，PM 回讀確認未產生任何留言或欄位變更後重試　escalation_epoch：0
- source_sha：`9c8036329821fe1fdaf38b648edf6a529c36e139`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T20:53:24+08:00

### self_run（查核者實跑）

- `gh issue view 9 --repo ruan6047/ai-workflow --json body -q .body | grep handoff | tail -1; git rev-parse HEAD; git merge-base --is-ancestor e1b33d8984425901de400afeb227d5df67d07212 HEAD`
  - 最後 handoff SHA 與 HEAD 均為 9c8036329821fe1fdaf38b648edf6a529c36e139；fork point 祖先檢查 exit 0。
- `git archive 9c8036329821fe1fdaf38b648edf6a529c36e139 | tar -x -C /tmp/aiwf9-r4test.KRkJnh; cd /tmp/aiwf9-r4test.KRkJnh/cli && PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -k mutated`
  - 8 passed，785 deselected；隔離式 archive 樹。
- `cd /tmp/aiwf9-r4.59ayrR/cli && PYTHONDONTWRITEBYTECODE=1 uv run python -c preflight_basis_from_body_probe`
  - 僅含 wf_preflight_pass v1、card_id、source_sha、preflight_passed true 的任意 YAML 留言被解析為 PreflightBasis(basis=event-verified, source_event=(URL 未提供))，check_preflight_event_present 通過。
- `git archive 04c8e6211576e786a01afaae69cfb5fbe756bbe1 cli | tar -x -C disposable-tree; cmp --help-output`
  - 04c8e621 與 9c803632 的 CLI help 全文 cmp exit 0；checkpoint_cmd 插在 review_cmd 後維持既有順序。

### findings（1，其中 blocking 1）

- **WF-22-CLI4-R4-01**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`unproven-preflight-counting`
  - evidence：在 source SHA 的隔離 archive 中，直接把任意 YAML body 傳給 preflight_basis_from_body：wf_preflight_pass v1、card_id WF-22-CLI4、該 source_sha、preflight_passed true。函式回傳 event-verified，即使 event_url 缺失；check_preflight_event_present 隨即通過。這不是 templates/review-escalation.md §5 所要求的 handoff-accepted 或等價 preflight pass lifecycle event，也不符合 canonical §4.1 要求的 event_id、type、actor、occurred_at 與 append-only lifecycle writer。
  - disposition：讀取器必須只採信可驗證為受管轄 handoff-accepted 或已定義等價 lifecycle event 的來源，並驗證其必要事件身分與 source_sha；在該 event writer 和其可驗證格式落地前維持拒絕寫入。補測試證明任意一般 Issue 留言、缺 event_url 或缺 lifecycle event 身分的四欄 YAML 一律不能建立 preflight basis。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5273767470 · 2026-08-12T22:59:54Z

<!-- wf-review-receipt:v1
card_id: WF-22-CLI4
source_sha: 3918fe82873877a4b811c7ee47905881954c0127
report_sha256: 145092feb425525bc5bfcd17bb60b55fb9546528487aa708aca3d43c5984277d
-->

取材規則：取材範圍自本規則之後的下一個「--- 被雜湊的報告全文開始 ---」整行之後的第一個字元起，至下一個「--- 被雜湊的報告全文結束 ---」整行之前的最後一個字元止；UTF-8、LF、沒有 strip；排除 receipt 區塊、此取材規則與兩個 delimiter。
--- 被雜湊的報告全文開始 ---
core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "git rev-parse HEAD; git merge-base --is-ancestor e1b33d8984425901de400afeb227d5df67d07212 HEAD"
    observed: "HEAD=3918fe82873877a4b811c7ee47905881954c0127；基線祖先檢查 exit 0；Issue Log 最後 handoff SHA 相同。"
  - command: "git archive 3918fe82873877a4b811c7ee47905881954c0127 | tar -x -C /tmp/aiworkflow-review9.dHyjBT; cd /tmp/aiworkflow-review9.dHyjBT/cli; uv run pytest -q"
    observed: "以四組測試檔分批完成 812 passed：257 + 374 + 81 + 100。"
  - command: "cd /tmp/aiworkflow-review9.dHyjBT/cli; uv run pytest -q -k mutated; uv run pytest -q tests/test_review.py tests/test_checkpoint.py"
    observed: "突變測試 12 passed、800 deselected；review/checkpoint 測試 81 passed。"
  - command: "git diff --check e1b33d8984425901de400afeb227d5df67d07212..3918fe82873877a4b811c7ee47905881954c0127; rg -n 'derive_preflight_basis|event-verified|structurally-unavailable|WRITER_STAMPED_KEYS' cli/src/wf_cli cli/tests"
    observed: "無 whitespace error；production 導出器不讀 Issue 留言，writer 加蓋鍵在提交面拒收，且測試窮舉確認 source 內無 event-verified 建構路徑。"
prior_accepted_blocking_findings:
  - finding_id: "WF-22-CLI4-R1-01"
    status: "resolved"
    evidence: "已移除預設與 writer-attested 計數路徑；derive_counts_toward_escalation 在未建立 preflight 時拋錯，render_escalation_facts_block 亦拒絕未建立依據卻帶 counts。"
  - finding_id: "WF-22-CLI4-R2-01"
    status: "resolved"
    evidence: "PREFLIGHT_BASES 僅含 event-verified 與 not-established；test_preflight_basis_has_no_writer_attested_option_any_more 及 12 條突變測試通過。"
  - finding_id: "WF-22-CLI4-R3-01"
    status: "resolved"
    evidence: "不再把 unknown 或 unavailable 寫入既有布林欄位；缺依據時不寫 preflight_passed 或 counts_toward_escalation，而由 writer 加蓋 structurally-unavailable 與 not-asserted。此處置符合需求方在 origin/main docs/ROADMAP.md §1、§3、§4 對宣告完整性與本卡驗收的裁定。"
findings: []
scope_outside_findings:
  - note: "事件仍缺 review-escalation.md §5:168 的 preflight_passed true，已由 ROADMAP §3 明定為不使留痕無法重建的已知細節；本輪不把它擴大為 blocking finding。"
  - note: "受管轄 preflight pass event writer 與可驗證格式不在本卡寫入集；在單一 GitHub 帳號結構下，承接卡若只新增自述欄位仍不足以把 binding 改為 event-verified。"
  - note: "owner_field_at_verdict_write 是裁決時的 Project owner 欄快照，不是 source_sha 執行者身分；現有命名與說明未把它誤宣稱為授權證據。"
--- 被雜湊的報告全文結束 ---


## Comment 5273798774 · 2026-08-12T23:03:38Z

<!-- wf-review-event:v1 card_id=WF-22-CLI4 source_sha=3918fe82873877a4b811c7ee47905881954c0127 attempt_id=WF-22-CLI4-e0-3918fe82873877a4b811c7ee47905881954c0127 -->
## 查核裁決：APPROVE

- 卡：`WF-22-CLI4`　attempt_id：`WF-22-CLI4-e0-3918fe82873877a4b811c7ee47905881954c0127`
- 查核者：GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5273767470。三項前輪 accepted blocking 皆判 resolved。scope_outside 三項未入區塊、保存於收據雜湊範圍內　escalation_epoch：0
- source_sha：`3918fe82873877a4b811c7ee47905881954c0127`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-13T07:03:37+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git merge-base --is-ancestor e1b33d8984425901de400afeb227d5df67d07212 HEAD`
  - HEAD=3918fe82873877a4b811c7ee47905881954c0127；基線祖先檢查 exit 0；Issue Log 最後 handoff SHA 相同。
- `git archive 3918fe82 | tar -x -C /tmp/aiworkflow-review9.dHyjBT; cd cli; uv run pytest -q`
  - 以四組測試檔分批完成 812 passed：257 + 374 + 81 + 100。
- `uv run pytest -q -k mutated; uv run pytest -q tests/test_review.py tests/test_checkpoint.py`
  - 突變測試 12 passed、800 deselected；review/checkpoint 測試 81 passed。
- `git diff --check e1b33d8..3918fe8; rg -n 'derive_preflight_basis|event-verified|structurally-unavailable|WRITER_STAMPED_KEYS' cli/src/wf_cli cli/tests`
  - 無 whitespace error；production 導出器不讀 Issue 留言，writer 加蓋鍵在提交面拒收，且測試窮舉確認 source 內無 event-verified 建構路徑。

### findings（0，其中 blocking 0）

- （無）

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。
