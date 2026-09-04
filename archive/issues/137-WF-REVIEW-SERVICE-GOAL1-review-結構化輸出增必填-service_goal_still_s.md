# #137 WF-REVIEW-SERVICE-GOAL1 review 結構化輸出增必填 service_goal_still_served（aiwf#130 子卡 S7a）
- state: open  created: 2026-08-25T02:22:46Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/137
- comments: 19

## Body

- 需求：ruan6047　規劃：—
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；動 review 的結構化輸出契約；schema 改動會影響所有後續查核事件的解析，且 383 筆既有事件不得因新欄位而失效。）　查核：待指派（建議 高階型；本卡改的是查核自身的契約，⛔ 執行者無法自證；且須以真實既有事件驗證向後相容。）
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：目標 2 可稽核的內容：卡是否仍服務其原始目標、是否仍合乎現行規範，必須是查核留痕上讀得出來的答案，而不是靠查核者當下想不想得到。

## 簡介
<!-- card-brief:begin -->
做什麼：把 canonical §5.1.1 的「服務的原始目標是否仍被服務」從條文變成 review 結構化輸出的必填欄位，並讓拒收訊息自己說明新契約。適用時機：查核者要對照交付與原始目標、或要判斷一張卡做完之後還值不值得繼續投入時。⛔ 非射程：不做 doctor 事後重驗（屬 S7b）；不改 core_pain_resolved 的否決權語意；不回填既有卡簡介（屬 S5）；不切換狀態語彙（屬 S2／S3）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：canonical §5.1.1 在 main 生效（d4ba7ce5）而**沒有實作**：實測 templates/review-prompt.md 與 templates/review-escalation.md 含 service_goal_still_served 皆 0 命中。⇒ 卡有兩個目標欄位而 review 現行只查一個——核心痛點由 core_pain_resolved 檢查且具否決權（validation.py:268：no 配 APPROVE 機械拒收）；服務的原始目標在 review 實作中零命中，只被寫、被存、被顯示，⛔ 從未被拿來對照交付。⭐ 而兩者的差別是**結構性的，不是統計上的**：核心痛點可被 amend（197 張母體中 16 張改過、累計 28 次），而服務的原始目標**開卡後沒有任何寫入通道**——amend_cmd.py:211–217 逐字「不補」（理由：它是鏈級欄位，變更本質是 baseline-cascade 的 invalidated 而非欄位編輯），且 amend 全史只寫過 7 種欄位 ⇒ 「被 amend 0 張」是**算術必然，⛔ 不是觀測**。⇒ 現行查的是會漂移的那個欄位，不查那個構造上不會漂移的。實證見 cpbl#166：兩欄分別是「cpbl main 沒有 required status check」與「測試要在碼進 main 之前跑」，原始目標在 ruleset 上線那一刻即達成，而後續十輪查的是被 amend 修改過的核心痛點。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:AI_WORKFLOW.md",
    "file:templates/review-prompt.md",
    "file:templates/review-escalation.md",
    "file:cli/src/wf_cli/review.py",
    "file:cli/src/wf_cli/validation.py",
    "file:cli/src/wf_cli/card.py",
    "file:cli/src/wf_cli/commands/review_cmd.py",
    "file:cli/tests/test_review.py",
    "file:cli/tests/test_review_service_goal.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] review 的結構化輸出新增 service_goal_still_served，值域**恰為** yes／no／unsure（canonical §5.1.1 逐字），與 core_pain_resolved 並列。⭐ **需求方 2026-08-25 裁定（丙′）**：`no` 具否決權（no 配 APPROVE 硬拒，比照 validation.py:268）；`unsure` **不擋**。⚠️ 契約層判準集中在 cli/src/wf_cli/validation.py，⛔ 不在 review.py。
- [ ] 填 no 或 unsure 時**須說明交付與原始目標的落差**（canonical §5.1.1 逐字），欄名 service_goal_gap，機械必填（空字串即拒）。
- [ ] ⭐ `unsure` 的語意須逐字定義並寫進 templates/review-prompt.md §2：它是「**查核者判不出來**」，⛔ **不是**「卡的目標欄未填」。⚠️ 依據是三層房規（動作不可逆→擋／判不出來指出被判定對象自己有缺陷→擋／指出判定者侷限→放行），導出自 35 個三值以上值域中**開了 10 個**、其餘 25 個依名稱判為非判定。⛔ 交付須逐字寫出該覆蓋率，不得寫成「全表窮舉」。
- [ ] ⭐ CLI 須自行偵測 placeholder 目標：卡面「服務的原始目標」逐字等於「未填寫（本卡於新制欄位定案前建立，2026-08-04）」時，於寫入的事件中**另記為卡面缺陷**（修法歸 baseline-cascade 的 invalidated，amend_cmd.py:211–217 逐字），⛔ 不得被 unsure 蓋掉。⚠️ 該字串須放具名常數並附母體數（197 張中 37 張命中、23 張 OPEN、⛔ 無其他變體或空值）；未驗清單須載明「日後若出現第二種寫法會靜默漏掉」。⚠️ 時序：契約驗證全在遠端呼叫之前（review_cmd.py:206–224）⇒ 本偵測只能在讀卡之後，是**寫入時的警示**，⛔ 不是拒收條件。
- [ ] ⭐ 解析器落點：body 為權威，於 cli/src/wf_cli/card.py 的 parse_requested_by（:743）旁新增 parse_service_goal(body)。⛔ **必須照抄 parse_requested_by 的形狀**——:758 逐字警告「Log 內含字面的『- 需求：』，不切掉就會把歷史當成現況讀」，而服務的原始目標同樣會出現在 Log 的 amend 行裡。⛔ 不採「直接讀 Project fields」的替代方案：那驗的是投影不是權威，且會讓 aiwf#138 各自再寫一份解析。
- [ ] ⛔ 新欄位**只在提交面**必填。須以碼證明契約鏈（parse_structured_block、review_invalid_reasons、validate_review_report）在本卡交付後**仍然只有 review_cmd.py 一個非測試呼叫端**。⚠️ 既有 204 則事件的相容性屬 aiwf#138 射程。
- [ ] ⭐ 事件寫出**兩處都要**：(G1) review.py:485–486 的散文行加 service_goal_still_served，no 時追加否決權註記；(G2) **review.py:983 的 wf_escalation_facts 結構化區塊**在 core_pain_resolved 之後加該鍵，no／unsure 時另加 service_goal_gap；(G3) placeholder 命中時於同區塊加 service_goal_field_placeholder。⛔ **不得升 BLOCK_VERSION**——讀回端 review.py:1091 是「!= BLOCK_VERSION: return None」，一升版 204 則既有事件全部變讀不懂；不升版是安全的（讀回端全走具名 data.get，⛔ 不拒未知鍵）。⚠️ 只寫散文行 = 機器讀不到，aiwf#138 掃不到。
- [ ] ⭐ service_goal_gap 含斷行字元時於**契約層**（提交面）拒收，⛔ 不摺疊。⚠️ 理由已實測收窄：YAML 路徑寫不出多行（解析器逐字「區塊內不得混入散文」直接拒），⇒ **唯一入口是 ```json 路徑**（JSON 的 \n 合法），而實跑證明 _yaml_scalar 的「" ".join(str(value).split())」會**靜默摺疊**。依 aiwf#35 規則二「禁止以正規化代替拒收」。⚠️ 判準須涵蓋 str.splitlines() 認得的全集，⛔ 不得只認 \n。
- [ ] ⭐ 拒收訊息須**可整段轉貼給查核者**：含欄位名、值域三值、no／unsure 的說明要求、canonical §5.1.1 引用。⛔ **不放 effective_from**（review.py:1261 唯一出現且只寫不讀；三個拒收出口全在遠端呼叫之前 ⇒ 只能硬編、必與 cutover 事件漂移）。⛔ 也**不必**叮嚀「說明須單行」——實測七種真實散文形狀（含全形／半形冒號、file:line、引號、反引號、括號）皆逐字通過，查核者不需要學任何跳脫。⚠️ 條文須載明：查核者看不到該訊息（無 wfcli，aiwf#13），送達靠 PM 轉述且其忠實度構造上不可觀測（dispatch-package.md:53）⇒ 真正的修法是 aiwf#66，⛔ 不在本卡射程。
- [ ] ⭐ 更正兩處誤述：(a) 本卡核心痛點原把「服務的原始目標被 amend 過 0 張」寫成量化支持，而 amend_cmd.py:211–217 逐字「不補」⇒ 0 是唯一可能值（已於 op 064ccb28 改述，本條保留為交付時的對照）；(b) 更正 AI_WORKFLOW.md §5.1.1 的未驗條款——它逐字宣稱「亦可被 amend 修改（amend_cmd.py 有一處）」，而該處是「刻意不支援」的說明。
- [ ] ⭐ cutover 事件的 contract 欄須參數化：review.py:1260 寫死 templates/review-escalation.md，而偵測器 body_has_contract_baseline（review.py:1180）只讀鍵名與版本、⛔ 不讀該值 ⇒ 留痕分不出兩次 cutover 各換了什麼。
- [ ] 回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）；replay_escalation_rules 與 canonical_citation_scan 維持綠。
- [ ] ⚠️ 交付時須附「PM 單方面決定清冊」，逐一標明哪些形狀或判準由執行者提出而非 canonical 明文或需求方裁定。

## 驗證

- [ ] 值域封閉性：以 yes／no／unsure 之外的值各跑一次，附 rc 與 stderr 原文，證明皆被拒。⛔ 只驗合法值會過是零資訊。
- [ ] ⭐ 否決語意的**兩側**負控：`no` 配 APPROVE 須被拒（附 rc 與 stderr 原文）；`unsure` 配 APPROVE 須**通過**（附 rc）。⛔ 只驗一側是零資訊——擋得住不證明放得行。
- [ ] 說明必填的負控：填 no 但說明為空、填 unsure 但說明為空，各跑一次證明被拒。
- [ ] ⭐ 斷行拒收須**兩條路徑各跑一次**：YAML 區塊寫多行，證明被解析器擋（附 stderr 原文）；```json 區塊帶 \n，證明被契約層擋（附 rc 與 stderr）。⛔ 只驗一條是零資訊。並附**正向對照**：七種真實散文形狀（含全形／半形冒號、file:line、引號、反引號、括號）逐字往返相同。
- [ ] ⛔ 呼叫端唯一性的**變異檢驗**：先證明現況三個函式各恰一個非測試呼叫端（附 grep 指令與原文），再刻意加第二個呼叫端，證明檢查會轉紅。⚠️ 只跑前半是零資訊。
- [ ] ⭐ facts 區塊的**往返**：新欄位寫進 wf_escalation_facts 後，以現行讀回路徑（review.py:1088 起）解析同一則事件，證明讀得回且逐字相同；再取至少 3 則**真實既有**事件（無新欄位）證明仍解析成功。⛔ 只驗新事件是零資訊。
- [ ] ⭐ placeholder 偵測：取那 23 張 OPEN 卡中至少 3 張**真實既有卡**實跑，證明事件中另記為卡面缺陷；再取一張目標正常的真實卡，證明**不誤報**。⛔ 不接受自造樣本。⚠️ 並證明 parse_service_goal 對 Log 內含該欄位字面的卡不會把歷史讀成現況（取一張確實 amend 過該類欄位的真實卡）。
- [ ] ⭐ 拒收訊息內容逐字驗證：附缺欄位時的 stderr 全文，逐項對照驗收第 9 條的四個元素，並證明其中**不含** effective_from；⛔ 不接受「訊息有寫」的自述。
- [ ] ⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因（缺什麼、要等什麼、需要誰）；⛔ 標不出原因者代表驗得了、不得列入。

## Log

- 2026-08-25T10:22:45+08:00 open by —；owner 待指派；iteration 0。
- 2026-08-25T10:29:28+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree ai/opus-5/WF-REVIEW-SERVICE-GOAL1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/review-service-goal1；交付狀態 🔬研究中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-25T10:30:18+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 0；SHA d4ba7ce5f3fa526fc3a7aa0ebbeee3c926e5eb28；證據 拆卡後進研究階段（需求方 2026-08-25 裁定拆卡，來源卡 aiwf#136 已 🛑已停止）。承接留痕見 issuecomment-5404265605：#136 的十一輪研究中與本卡射程相關的四則已逐條連結。本階段要收斂的是 S7a 專屬的三個未決設計題（否決權、向後相容分流界線、拒收訊息形狀），⛔ 不重跑 #136 已完成的量測。基準 origin/main = d4ba7ce5（已 fetch 核對，local main 同值）。。
- 2026-08-25T10:37:28+08:00 amend by wf-cli（op d203faf9）→ 驗收條件：原值「[ ] review 的結構化輸出新增 service_goal_still_served，值域**恰為** yes／no／unsure（canonical §5.1.1 逐字），與 core_pain_resolved 並列。⛔ 不改後者的否決權語意——§5.1.1 只說「並列」，未賦予新欄位否決權；賦不賦由本卡規劃提案、需求方裁定。⚠️ 契約層判準集中在 cli/src/wf_cli/validation.py（core_pain_resolved 於 :258–:270），⛔ 不在 review.py。；[ ] 填 no 或 unsure 時**須說明交付與原始目標的落差**（canonical §5.1.1 逐字），且該說明為機械必填（空字串即拒）。；[ ] ⛔ **向後相容**：既有 review 事件沒有該欄位，⛔ 不得因新欄位而解析失敗或被判 review-invalid。⚠️ 須以真實既有事件實測——本 repo 已累積 383 筆 finding、42 張卡有 review 事件；分流依據比照既有的 TRAILER_GUARD_EPOCH 日期界線。；[ ] templates/review-prompt.md §5 的 YAML 區塊同步新增該欄位並說明填法；§2 第一判準段落同步；templates/review-escalation.md §2 的 schema 同步。；[ ] ⭐ **拒收訊息須自帶教學**：缺該欄位時 stderr 須含欄位名、值域、no／unsure 的附帶要求，以及本次 cutover 的 effective_from。⇒ 理由：跨家族查核者沒有 wfcli（aiwf#13），跑不了 --validate-only；而派審詞在設計上不留痕——templates/dispatch-package.md:53 逐字「本節撤除紀律後沒有補上任何機器面保證」⇒ 任何押在派審詞上的送達路徑，其失效**構造上不可觀測**。；[ ] ⭐ cutover 事件的 contract 欄須參數化：實測 review.py:1260 寫死 templates/review-escalation.md，而偵測器 body_has_contract_baseline（review.py:1180）只讀鍵名與版本、⛔ 不讀該值 ⇒ 現行留痕分不出兩次 cutover 各換了什麼。本卡既要改 review-prompt.md，須讓該欄反映實際契約。；[ ] ⭐ 補上 §5.1.1 自標的未驗項並寫進條文或卡面：開卡前實測 195 張卡中「服務的原始目標」被 amend **0 張**、「核心痛點」**15 張** ⇒ 該不對稱有量化支持。⚠️ 若日後有人 amend 前者，該支持即失效，須有機制發現。；[ ] 回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）；replay_escalation_rules 與 canonical_citation_scan 維持綠。；[ ] ⚠️ 交付時須附「PM 單方面決定清冊」，逐一標明哪些形狀或判準由執行者提出而非 canonical 明文或需求方裁定。」→ 新值「review 的結構化輸出新增 service_goal_still_served，值域**恰為** yes／no／unsure（canonical §5.1.1 逐字），與 core_pain_resolved 並列。⛔ 不改後者的否決權語意——§5.1.1 只說「並列」，未賦予新欄位否決權；賦不賦由本卡規劃提案、需求方裁定。⚠️ 契約層判準集中在 cli/src/wf_cli/validation.py（core_pain_resolved 於 :258–:270），⛔ 不在 review.py。；填 no 或 unsure 時**須說明交付與原始目標的落差**（canonical §5.1.1 逐字），且該說明為機械必填（空字串即拒）。；⛔ 新欄位**只在提交面**必填。須以碼證明契約鏈（parse_structured_block、review_invalid_reasons、validate_review_report）在本卡交付後**仍然只有 review_cmd.py 一個非測試呼叫端** ⇒ 若日後有人把它接到既有事件上，該檢查會轉紅。⚠️ 既有 204 則事件的相容性屬 aiwf#138 射程，本卡不處理，須在條文中指名。；templates/review-prompt.md §5 的 YAML 區塊同步新增該欄位並說明填法；§2 第一判準段落同步；templates/review-escalation.md §2 的 schema 同步。；⭐ **拒收訊息須自帶教學**：缺該欄位時 stderr 須含欄位名、值域、no／unsure 的附帶要求，以及本次 cutover 的 effective_from。⇒ 理由：跨家族查核者沒有 wfcli（aiwf#13），跑不了 --validate-only；而派審詞在設計上不留痕——templates/dispatch-package.md:53 逐字「本節撤除紀律後沒有補上任何機器面保證」⇒ 任何押在派審詞上的送達路徑，其失效**構造上不可觀測**。⚠️ 既有房規（validation.py:258–272）是單行「欄位 必填：一句話（canonical 引用）」且**沒有任何一則帶 cutover 日期** ⇒ 本條是新形狀，須列入 PM 單方面決定清冊。；⭐ cutover 事件的 contract 欄須參數化：實測 review.py:1260 寫死 templates/review-escalation.md，而偵測器 body_has_contract_baseline（review.py:1180）只讀鍵名與版本、⛔ 不讀該值 ⇒ 現行留痕分不出兩次 cutover 各換了什麼。本卡既要改 review-prompt.md，須讓該欄反映實際契約。；⭐ 補上 §5.1.1 自標的未驗項並寫進條文或卡面：開卡前實測 195 張卡中「服務的原始目標」被 amend **0 張**、「核心痛點」**15 張** ⇒ 該不對稱有量化支持。⚠️ 若日後有人 amend 前者，該支持即失效，須有機制發現。；回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）；replay_escalation_rules 與 canonical_citation_scan 維持綠。；⚠️ 交付時須附「PM 單方面決定清冊」，逐一標明哪些形狀或判準由執行者提出而非 canonical 明文或需求方裁定。」；理由 研究第二輪推翻了本卡驗收第 3 條與驗證第 2 條所依據的前提（留痕 issuecomment-5404332084）。原條文承接自 aiwf#136 第三輪的「383 筆既有事件會全部 review-invalid、須比照 TRAILER_GUARD_EPOCH 日期分流」，而實測整條解析＋驗證鏈（parse_structured_block:422／review_invalid_reasons:159／validate_review_report:240）各恰有一個非測試呼叫端且全在 review_cmd.py 的提交路徑上，⛔ 沒有任何路徑重讀既有留言（doctor.py 對該三個名字 0 命中；replay 腳本走自建案例）。⇒ 原條文構造上不會失敗，是零資訊檢查。改寫為「呼叫端唯一性」，該版本說得出什麼結果會推翻它（多一個呼叫端即紅）。同時把既有 204 則事件的相容性明確劃給 aiwf#138，並把第 5 條的新形狀（拒收訊息帶 effective_from）與既有房規的差異寫進條文，供 PM 單方面決定清冊引用。。
- 2026-08-25T10:37:28+08:00 amend by wf-cli（op d203faf9）→ 驗證：原值「[ ] 值域封閉性：以 yes／no／unsure 之外的值各跑一次，附 rc 與 stderr 原文，證明皆被拒。⛔ 只驗合法值會過是零資訊。；[ ] ⛔ 向後相容的**變異檢驗**：取至少 3 筆**真實既有** review 事件（無該欄位）跑解析，證明不失敗；再刻意移除相容處理，證明它會轉紅。⚠️ 只跑前半是零資訊。；[ ] 說明必填的負控：填 no 但說明為空、填 unsure 但說明為空，各跑一次證明被拒。；[ ] ⭐ 拒收訊息內容逐字驗證：附缺欄位時的 stderr 全文，逐項對照驗收第 5 條要求的四個元素；⛔ 不接受「訊息有寫」的自述。；[ ] ⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因（缺什麼、要等什麼、需要誰）；⛔ 標不出原因者代表驗得了、不得列入。」→ 新值「值域封閉性：以 yes／no／unsure 之外的值各跑一次，附 rc 與 stderr 原文，證明皆被拒。⛔ 只驗合法值會過是零資訊。；⛔ 呼叫端唯一性的**變異檢驗**：先證明現況三個函式各恰一個非測試呼叫端（附 grep 指令與原文），再刻意加第二個呼叫端，證明檢查會轉紅。⚠️ 只跑前半是零資訊。；說明必填的負控：填 no 但說明為空、填 unsure 但說明為空，各跑一次證明被拒。；⭐ 拒收訊息內容逐字驗證：附缺欄位時的 stderr 全文，逐項對照驗收第 5 條要求的四個元素；⛔ 不接受「訊息有寫」的自述。；⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因（缺什麼、要等什麼、需要誰）；⛔ 標不出原因者代表驗得了、不得列入。」；理由 研究第二輪推翻了本卡驗收第 3 條與驗證第 2 條所依據的前提（留痕 issuecomment-5404332084）。原條文承接自 aiwf#136 第三輪的「383 筆既有事件會全部 review-invalid、須比照 TRAILER_GUARD_EPOCH 日期分流」，而實測整條解析＋驗證鏈（parse_structured_block:422／review_invalid_reasons:159／validate_review_report:240）各恰有一個非測試呼叫端且全在 review_cmd.py 的提交路徑上，⛔ 沒有任何路徑重讀既有留言（doctor.py 對該三個名字 0 命中；replay 腳本走自建案例）。⇒ 原條文構造上不會失敗，是零資訊檢查。改寫為「呼叫端唯一性」，該版本說得出什麼結果會推翻它（多一個呼叫端即紅）。同時把既有 204 則事件的相容性明確劃給 aiwf#138，並把第 5 條的新形狀（拒收訊息帶 effective_from）與既有房規的差異寫進條文，供 PM 單方面決定清冊引用。。
- 2026-08-25T10:52:14+08:00 amend by wf-cli（op 5a2de697）→ 驗收條件：原值「[ ] review 的結構化輸出新增 service_goal_still_served，值域**恰為** yes／no／unsure（canonical §5.1.1 逐字），與 core_pain_resolved 並列。⛔ 不改後者的否決權語意——§5.1.1 只說「並列」，未賦予新欄位否決權；賦不賦由本卡規劃提案、需求方裁定。⚠️ 契約層判準集中在 cli/src/wf_cli/validation.py（core_pain_resolved 於 :258–:270），⛔ 不在 review.py。；[ ] 填 no 或 unsure 時**須說明交付與原始目標的落差**（canonical §5.1.1 逐字），且該說明為機械必填（空字串即拒）。；[ ] ⛔ 新欄位**只在提交面**必填。須以碼證明契約鏈（parse_structured_block、review_invalid_reasons、validate_review_report）在本卡交付後**仍然只有 review_cmd.py 一個非測試呼叫端** ⇒ 若日後有人把它接到既有事件上，該檢查會轉紅。⚠️ 既有 204 則事件的相容性屬 aiwf#138 射程，本卡不處理，須在條文中指名。；[ ] templates/review-prompt.md §5 的 YAML 區塊同步新增該欄位並說明填法；§2 第一判準段落同步；templates/review-escalation.md §2 的 schema 同步。；[ ] ⭐ **拒收訊息須自帶教學**：缺該欄位時 stderr 須含欄位名、值域、no／unsure 的附帶要求，以及本次 cutover 的 effective_from。⇒ 理由：跨家族查核者沒有 wfcli（aiwf#13），跑不了 --validate-only；而派審詞在設計上不留痕——templates/dispatch-package.md:53 逐字「本節撤除紀律後沒有補上任何機器面保證」⇒ 任何押在派審詞上的送達路徑，其失效**構造上不可觀測**。⚠️ 既有房規（validation.py:258–272）是單行「欄位 必填：一句話（canonical 引用）」且**沒有任何一則帶 cutover 日期** ⇒ 本條是新形狀，須列入 PM 單方面決定清冊。；[ ] ⭐ cutover 事件的 contract 欄須參數化：實測 review.py:1260 寫死 templates/review-escalation.md，而偵測器 body_has_contract_baseline（review.py:1180）只讀鍵名與版本、⛔ 不讀該值 ⇒ 現行留痕分不出兩次 cutover 各換了什麼。本卡既要改 review-prompt.md，須讓該欄反映實際契約。；[ ] ⭐ 補上 §5.1.1 自標的未驗項並寫進條文或卡面：開卡前實測 195 張卡中「服務的原始目標」被 amend **0 張**、「核心痛點」**15 張** ⇒ 該不對稱有量化支持。⚠️ 若日後有人 amend 前者，該支持即失效，須有機制發現。；[ ] 回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）；replay_escalation_rules 與 canonical_citation_scan 維持綠。；[ ] ⚠️ 交付時須附「PM 單方面決定清冊」，逐一標明哪些形狀或判準由執行者提出而非 canonical 明文或需求方裁定。」→ 新值「review 的結構化輸出新增 service_goal_still_served，值域**恰為** yes／no／unsure（canonical §5.1.1 逐字），與 core_pain_resolved 並列。⭐ **需求方 2026-08-25 裁定（丙′）**：`no` 具否決權（no 配 APPROVE 硬拒，比照 validation.py:268 對 core_pain_resolved 的處置）；`unsure` **不擋**。⚠️ 契約層判準集中在 cli/src/wf_cli/validation.py，⛔ 不在 review.py。；填 no 或 unsure 時**須說明交付與原始目標的落差**（canonical §5.1.1 逐字），且該說明為機械必填（空字串即拒）。；⭐ `unsure` 的語意須逐字定義並寫進 templates/review-prompt.md §2：它是「**查核者判不出來**」，⛔ **不是**「卡的目標欄未填」——後者由 CLI 自行偵測（見下一條）。⚠️ 依據是三層房規（動作不可逆→擋／判不出來指出被判定對象自己有缺陷→擋／指出判定者侷限→放行），導出自 35 個三值以上值域中**開了 10 個**、其餘 25 個依名稱判為非判定。⛔ 交付須逐字寫出該覆蓋率，不得寫成「全表窮舉」。；⭐ CLI 須自行偵測 placeholder 目標：卡面「服務的原始目標」逐字等於「未填寫（本卡於新制欄位定案前建立，2026-08-04）」時，於寫入的事件中**另記為卡面缺陷**（其修法歸 baseline-cascade 的 invalidated，amend_cmd.py:211–217 逐字），⛔ 不得被 unsure 蓋掉。⚠️ 該字串須放具名常數並附母體數（實測 197 張中 37 張命中、其中 23 張 OPEN、⛔ 無任何其他變體或空值），且須於未驗清單載明「日後若出現第二種寫法會靜默漏掉」。⚠️ 時序限制：契約驗證全在遠端呼叫之前（review_cmd.py:206–224）⇒ 本偵測只能在讀卡之後，是**寫入時的警示**，⛔ 不是拒收條件。；⛔ 新欄位**只在提交面**必填。須以碼證明契約鏈（parse_structured_block、review_invalid_reasons、validate_review_report）在本卡交付後**仍然只有 review_cmd.py 一個非測試呼叫端** ⇒ 若日後有人把它接到既有事件上，該檢查會轉紅。⚠️ 既有 204 則事件的相容性屬 aiwf#138 射程，本卡不處理，須在條文中指名。；templates/review-prompt.md §5 的 YAML 區塊同步新增該欄位並說明填法；§2 第一判準段落同步（含 no 擋、unsure 不擋的裁定）；templates/review-escalation.md §2 的 schema 同步。；⭐ 拒收訊息須**可整段轉貼給查核者**：含欄位名、值域三值、no／unsure 的說明要求，以及 canonical §5.1.1 引用。⛔ **不放 effective_from**——review.py:1261 是全 CLI 唯一出現處且只寫不讀，而三個拒收出口全在遠端呼叫之前 ⇒ 只能硬編，必然與 cutover 事件漂移。⚠️ 沿用既有房規形狀（validation.py:258–272 的單行「欄位 必填：一句話（canonical 引用）」）。⚠️ 條文須載明：查核者看不到該訊息（他沒有 wfcli，aiwf#13），送達靠 PM 轉述，其忠實度**構造上不可觀測**（dispatch-package.md:53）⇒ 真正的修法是 aiwf#66，⛔ 不在本卡射程，不得讓人以為本卡解決了送達問題。；⭐ 更正兩處誤述：(a) 本卡核心痛點把「服務的原始目標被 amend 過 0 張」寫成**量化支持**，而 amend_cmd.py:211–217 逐字「不補」⇒ **0 是唯一可能的值**，須改述為結構性事實（該欄開卡後無寫入通道，故不漂移是構造保證）；(b) 更正 AI_WORKFLOW.md §5.1.1 的未驗條款——它逐字宣稱「服務的原始目標亦可被 amend 修改（amend_cmd.py 有一處）」，而該處是「刻意不支援」的說明，⛔ 不是實作。⚠️ 核心痛點側改附本卡自量的實測：197 張母體中核心痛點被 amend 16 張（累計 28 次），且 amend 全史只寫過 7 種欄位。；⭐ cutover 事件的 contract 欄須參數化：實測 review.py:1260 寫死 templates/review-escalation.md，而偵測器 body_has_contract_baseline（review.py:1180）只讀鍵名與版本、⛔ 不讀該值 ⇒ 現行留痕分不出兩次 cutover 各換了什麼。本卡既要改 review-prompt.md，須讓該欄反映實際契約。；回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）；replay_escalation_rules 與 canonical_citation_scan 維持綠。；⚠️ 交付時須附「PM 單方面決定清冊」，逐一標明哪些形狀或判準由執行者提出而非 canonical 明文或需求方裁定。」；理由 需求方 2026-08-25 裁定採丙′：no 擋、unsure 不擋（說明機械必填）、外加 CLI 自行偵測 placeholder 目標。依據為研究第五至七輪（issuecomment-5404384908／5404398512／5404407396）：以 AST 形狀搜尋窮舉出 35 個三值以上值域，開其中 10 個導出三層房規（不可逆→擋／對象有缺陷→擋／判定者侷限→放行），而 unsure 一個值同時裝了第 2 層與第 3 層 ⇒ 須把「卡面目標未填」從 unsure 裡拆出來由 CLI 自判。同時依第三輪（issuecomment-5404365885）新增更正條：amend_cmd.py:211–217 逐字「不補」⇒「被 amend 0 張」是算術必然非觀測，且 canonical §5.1.1 的未驗條款宣稱的 amend 路徑不存在。依第四輪（issuecomment-5404373350）移除 effective_from 要求：review.py:1261 是唯一出現處且只寫不讀，三個拒收出口全在遠端呼叫之前。資源宣告新增 AI_WORKFLOW.md（更正 §5.1.1）、review_cmd.py（placeholder 偵測與拒收訊息）、test_review.py（回歸）。⚠️ 核心痛點本身的改述無法在本次執行：--core-pain 須併 --ruling-url，待需求方於本 issue 留下裁定留言後另行 amend。。
- 2026-08-25T10:52:14+08:00 amend by wf-cli（op 5a2de697）→ 驗證：原值「[ ] 值域封閉性：以 yes／no／unsure 之外的值各跑一次，附 rc 與 stderr 原文，證明皆被拒。⛔ 只驗合法值會過是零資訊。；[ ] ⛔ 呼叫端唯一性的**變異檢驗**：先證明現況三個函式各恰一個非測試呼叫端（附 grep 指令與原文），再刻意加第二個呼叫端，證明檢查會轉紅。⚠️ 只跑前半是零資訊。；[ ] 說明必填的負控：填 no 但說明為空、填 unsure 但說明為空，各跑一次證明被拒。；[ ] ⭐ 拒收訊息內容逐字驗證：附缺欄位時的 stderr 全文，逐項對照驗收第 5 條要求的四個元素；⛔ 不接受「訊息有寫」的自述。；[ ] ⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因（缺什麼、要等什麼、需要誰）；⛔ 標不出原因者代表驗得了、不得列入。」→ 新值「值域封閉性：以 yes／no／unsure 之外的值各跑一次，附 rc 與 stderr 原文，證明皆被拒。⛔ 只驗合法值會過是零資訊。；⭐ 否決語意的**兩側**負控：`no` 配 APPROVE 須被拒（附 rc 與 stderr 原文）；`unsure` 配 APPROVE 須**通過**（附 rc）。⛔ 只驗一側是零資訊——擋得住不證明放得行。；說明必填的負控：填 no 但說明為空、填 unsure 但說明為空，各跑一次證明被拒。；⛔ 呼叫端唯一性的**變異檢驗**：先證明現況三個函式各恰一個非測試呼叫端（附 grep 指令與原文），再刻意加第二個呼叫端，證明檢查會轉紅。⚠️ 只跑前半是零資訊。；⭐ placeholder 偵測：取那 23 張 OPEN 卡中至少 3 張**真實既有卡**實跑，證明事件中另記為卡面缺陷；再取一張目標正常的真實卡，證明**不誤報**。⛔ 不接受自造樣本。；⭐ 拒收訊息內容逐字驗證：附缺欄位時的 stderr 全文，逐項對照驗收第 7 條的四個元素，並證明其中**不含** effective_from；⛔ 不接受「訊息有寫」的自述。；⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因（缺什麼、要等什麼、需要誰）；⛔ 標不出原因者代表驗得了、不得列入。」；理由 需求方 2026-08-25 裁定採丙′：no 擋、unsure 不擋（說明機械必填）、外加 CLI 自行偵測 placeholder 目標。依據為研究第五至七輪（issuecomment-5404384908／5404398512／5404407396）：以 AST 形狀搜尋窮舉出 35 個三值以上值域，開其中 10 個導出三層房規（不可逆→擋／對象有缺陷→擋／判定者侷限→放行），而 unsure 一個值同時裝了第 2 層與第 3 層 ⇒ 須把「卡面目標未填」從 unsure 裡拆出來由 CLI 自判。同時依第三輪（issuecomment-5404365885）新增更正條：amend_cmd.py:211–217 逐字「不補」⇒「被 amend 0 張」是算術必然非觀測，且 canonical §5.1.1 的未驗條款宣稱的 amend 路徑不存在。依第四輪（issuecomment-5404373350）移除 effective_from 要求：review.py:1261 是唯一出現處且只寫不讀，三個拒收出口全在遠端呼叫之前。資源宣告新增 AI_WORKFLOW.md（更正 §5.1.1）、review_cmd.py（placeholder 偵測與拒收訊息）、test_review.py（回歸）。⚠️ 核心痛點本身的改述無法在本次執行：--core-pain 須併 --ruling-url，待需求方於本 issue 留下裁定留言後另行 amend。。
- 2026-08-25T10:52:14+08:00 amend by wf-cli（op 5a2de697）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:templates/review-prompt.md", "file:templates/review-escalation.md", "file:cli/src/wf_cli/review.py", "file:cli/src/wf_cli/validation.py", "file:cli/tests/test_review_service_goal.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:AI_WORKFLOW.md、file:templates/review-prompt.md、file:templates/review-escalation.md、file:cli/src/wf_cli/review.py、file:cli/src/wf_cli/validation.py、file:cli/src/wf_cli/commands/review_cmd.py、file:cli/tests/test_review.py、file:cli/tests/test_review_service_goal.py」；理由 需求方 2026-08-25 裁定採丙′：no 擋、unsure 不擋（說明機械必填）、外加 CLI 自行偵測 placeholder 目標。依據為研究第五至七輪（issuecomment-5404384908／5404398512／5404407396）：以 AST 形狀搜尋窮舉出 35 個三值以上值域，開其中 10 個導出三層房規（不可逆→擋／對象有缺陷→擋／判定者侷限→放行），而 unsure 一個值同時裝了第 2 層與第 3 層 ⇒ 須把「卡面目標未填」從 unsure 裡拆出來由 CLI 自判。同時依第三輪（issuecomment-5404365885）新增更正條：amend_cmd.py:211–217 逐字「不補」⇒「被 amend 0 張」是算術必然非觀測，且 canonical §5.1.1 的未驗條款宣稱的 amend 路徑不存在。依第四輪（issuecomment-5404373350）移除 effective_from 要求：review.py:1261 是唯一出現處且只寫不讀，三個拒收出口全在遠端呼叫之前。資源宣告新增 AI_WORKFLOW.md（更正 §5.1.1）、review_cmd.py（placeholder 偵測與拒收訊息）、test_review.py（回歸）。⚠️ 核心痛點本身的改述無法在本次執行：--core-pain 須併 --ruling-url，待需求方於本 issue 留下裁定留言後另行 amend。。
- 2026-08-25T10:55:27+08:00 amend by wf-cli（op 064ccb28）→ 核心痛點：原值「canonical §5.1.1 在 main 生效（d4ba7ce5）而**沒有實作**：實測 templates/review-prompt.md 與 templates/review-escalation.md 含 service_goal_still_served 皆 0 命中。⇒ 卡有兩個目標欄位而 review 現行只查一個——核心痛點由 core_pain_resolved 檢查且具否決權（validation.py:268 逐字：no 配 APPROVE 機械拒收）；服務的原始目標在 review 實作中零命中，只被寫、被存、被顯示，⛔ 從未被拿來對照交付。⭐ 而該不對稱有量化支持（開卡前實測）：195 張卡中「服務的原始目標」被 amend 過 0 張、「核心痛點」15 張 ⇒ 現行查的是會漂移的那個欄位，不查不會漂移的那個。實證見 cpbl#166：兩欄分別是「cpbl main 沒有 required status check」與「測試要在碼進 main 之前跑」，原始目標在 ruleset 上線那一刻即達成，而後續十輪查的是被 amend 修改過的核心痛點。」→ 新值「canonical §5.1.1 在 main 生效（d4ba7ce5）而**沒有實作**：實測 templates/review-prompt.md 與 templates/review-escalation.md 含 service_goal_still_served 皆 0 命中。⇒ 卡有兩個目標欄位而 review 現行只查一個——核心痛點由 core_pain_resolved 檢查且具否決權（validation.py:268：no 配 APPROVE 機械拒收）；服務的原始目標在 review 實作中零命中，只被寫、被存、被顯示，⛔ 從未被拿來對照交付。⭐ 而兩者的差別是**結構性的，不是統計上的**：核心痛點可被 amend（197 張母體中 16 張改過、累計 28 次），而服務的原始目標**開卡後沒有任何寫入通道**——amend_cmd.py:211–217 逐字「不補」（理由：它是鏈級欄位，變更本質是 baseline-cascade 的 invalidated 而非欄位編輯），且 amend 全史只寫過 7 種欄位 ⇒ 「被 amend 0 張」是**算術必然，⛔ 不是觀測**。⇒ 現行查的是會漂移的那個欄位，不查那個構造上不會漂移的。實證見 cpbl#166：兩欄分別是「cpbl main 沒有 required status check」與「測試要在碼進 main 之前跑」，原始目標在 ruleset 上線那一刻即達成，而後續十輪查的是被 amend 修改過的核心痛點。」；理由 依需求方 2026-08-25 裁定第二項授權更正（issuecomment-5404453207）。原文把「服務的原始目標被 amend 過 0 張」寫成量化支持，而研究第三輪（issuecomment-5404365885）查出：amend_cmd.py:211–217 逐字「不補」，該欄開卡後無任何寫入通道，寫入端只有 open_cmd.py ⇒ 0 是唯一可能的值，讀成「我們觀察到 0」是誤導。改述為結構性事實，並附核心痛點側的自量實測（197 張母體中 16 張被 amend、累計 28 次；amend 全史只寫過 7 種欄位）。⭐ 論點本身因此變強：不漂移是構造保證而非運氣。；授權 依需求方 ruan6047 於 https://github.com/ruan6047/ai-workflow/issues/137#issuecomment-5404453207 的裁定（已核對：該 URL 指向本卡 issue 的既存留言，且其 GitHub author 欄逐字等於卡面「需求：」欄。本指令不讀取留言內文或操作者身分，故不判定留言內容是否構成裁定——上句「裁定」是操作者的宣告，不是本指令查得的事實——亦不區分「需求方本人張貼」與「他人代擬代貼」）。
- 2026-08-25T10:56:27+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (PM)；iteration 0；SHA d4ba7ce5f3fa526fc3a7aa0ebbeee3c926e5eb28；證據 研究七輪完成，需求方已裁定丙′（issuecomment-5404453207），卡面三次 amend 已反映（op d203faf9 驗收＋驗證、op 5a2de697 驗收＋驗證＋資源、op 064ccb28 核心痛點）。七輪留痕：issuecomment-5404310059（否決權：197 張母體、23 張 OPEN 卡目標欄為 placeholder、4 組共用目標全為切片兄弟）、5404332084（⛔ 推翻 aiwf#136 第三輪：契約鏈三函式各恰一個非測試呼叫端，既有事件不會被重讀，原驗收第 3 條構造上不會失敗）、5404365885（⛔ canonical §5.1.1 未驗條款事實錯誤：amend_cmd.py:211–217 逐字不補 ⇒ 被 amend 0 張是算術必然；核心痛點側自量 16 張／amend 全史 7 種欄位）、5404373350（⛔ effective_from 拿不到：review.py:1261 唯一出現且只寫不讀，三個拒收出口全在遠端呼叫之前；且該訊息讀者是 PM 不是查核者）、5404384908（三值房規兩前例與 2026-08-13 裁定）、5404398512（AST 形狀搜尋 35 個值域、三層判準、unsure 同時裝第 2／3 層）、5404407396（placeholder 只有一種寫法：37 張逐字同串、23 張 OPEN、無其他變體；無第四條規則）。資源互斥於 amend 後手動重查（amend 不跑該閘門）：與非終態且 owner 非佔位的活卡交集 0 筆；⚠️ aiwf#138 同宣告 validation.py 但 owner 為待指派故不持鎖，其 assign 時必然序列化，S7a 先。基準 origin/main = d4ba7ce5（已 fetch 核對）。。
- 2026-08-25T11:16:31+08:00 amend by wf-cli（op 02b0220e）→ 驗收條件：原值「[ ] review 的結構化輸出新增 service_goal_still_served，值域**恰為** yes／no／unsure（canonical §5.1.1 逐字），與 core_pain_resolved 並列。⭐ **需求方 2026-08-25 裁定（丙′）**：`no` 具否決權（no 配 APPROVE 硬拒，比照 validation.py:268 對 core_pain_resolved 的處置）；`unsure` **不擋**。⚠️ 契約層判準集中在 cli/src/wf_cli/validation.py，⛔ 不在 review.py。；[ ] 填 no 或 unsure 時**須說明交付與原始目標的落差**（canonical §5.1.1 逐字），且該說明為機械必填（空字串即拒）。；[ ] ⭐ `unsure` 的語意須逐字定義並寫進 templates/review-prompt.md §2：它是「**查核者判不出來**」，⛔ **不是**「卡的目標欄未填」——後者由 CLI 自行偵測（見下一條）。⚠️ 依據是三層房規（動作不可逆→擋／判不出來指出被判定對象自己有缺陷→擋／指出判定者侷限→放行），導出自 35 個三值以上值域中**開了 10 個**、其餘 25 個依名稱判為非判定。⛔ 交付須逐字寫出該覆蓋率，不得寫成「全表窮舉」。；[ ] ⭐ CLI 須自行偵測 placeholder 目標：卡面「服務的原始目標」逐字等於「未填寫（本卡於新制欄位定案前建立，2026-08-04）」時，於寫入的事件中**另記為卡面缺陷**（其修法歸 baseline-cascade 的 invalidated，amend_cmd.py:211–217 逐字），⛔ 不得被 unsure 蓋掉。⚠️ 該字串須放具名常數並附母體數（實測 197 張中 37 張命中、其中 23 張 OPEN、⛔ 無任何其他變體或空值），且須於未驗清單載明「日後若出現第二種寫法會靜默漏掉」。⚠️ 時序限制：契約驗證全在遠端呼叫之前（review_cmd.py:206–224）⇒ 本偵測只能在讀卡之後，是**寫入時的警示**，⛔ 不是拒收條件。；[ ] ⛔ 新欄位**只在提交面**必填。須以碼證明契約鏈（parse_structured_block、review_invalid_reasons、validate_review_report）在本卡交付後**仍然只有 review_cmd.py 一個非測試呼叫端** ⇒ 若日後有人把它接到既有事件上，該檢查會轉紅。⚠️ 既有 204 則事件的相容性屬 aiwf#138 射程，本卡不處理，須在條文中指名。；[ ] templates/review-prompt.md §5 的 YAML 區塊同步新增該欄位並說明填法；§2 第一判準段落同步（含 no 擋、unsure 不擋的裁定）；templates/review-escalation.md §2 的 schema 同步。；[ ] ⭐ 拒收訊息須**可整段轉貼給查核者**：含欄位名、值域三值、no／unsure 的說明要求，以及 canonical §5.1.1 引用。⛔ **不放 effective_from**——review.py:1261 是全 CLI 唯一出現處且只寫不讀，而三個拒收出口全在遠端呼叫之前 ⇒ 只能硬編，必然與 cutover 事件漂移。⚠️ 沿用既有房規形狀（validation.py:258–272 的單行「欄位 必填：一句話（canonical 引用）」）。⚠️ 條文須載明：查核者看不到該訊息（他沒有 wfcli，aiwf#13），送達靠 PM 轉述，其忠實度**構造上不可觀測**（dispatch-package.md:53）⇒ 真正的修法是 aiwf#66，⛔ 不在本卡射程，不得讓人以為本卡解決了送達問題。；[ ] ⭐ 更正兩處誤述：(a) 本卡核心痛點把「服務的原始目標被 amend 過 0 張」寫成**量化支持**，而 amend_cmd.py:211–217 逐字「不補」⇒ **0 是唯一可能的值**，須改述為結構性事實（該欄開卡後無寫入通道，故不漂移是構造保證）；(b) 更正 AI_WORKFLOW.md §5.1.1 的未驗條款——它逐字宣稱「服務的原始目標亦可被 amend 修改（amend_cmd.py 有一處）」，而該處是「刻意不支援」的說明，⛔ 不是實作。⚠️ 核心痛點側改附本卡自量的實測：197 張母體中核心痛點被 amend 16 張（累計 28 次），且 amend 全史只寫過 7 種欄位。；[ ] ⭐ cutover 事件的 contract 欄須參數化：實測 review.py:1260 寫死 templates/review-escalation.md，而偵測器 body_has_contract_baseline（review.py:1180）只讀鍵名與版本、⛔ 不讀該值 ⇒ 現行留痕分不出兩次 cutover 各換了什麼。本卡既要改 review-prompt.md，須讓該欄反映實際契約。；[ ] 回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）；replay_escalation_rules 與 canonical_citation_scan 維持綠。；[ ] ⚠️ 交付時須附「PM 單方面決定清冊」，逐一標明哪些形狀或判準由執行者提出而非 canonical 明文或需求方裁定。」→ 新值「review 的結構化輸出新增 service_goal_still_served，值域**恰為** yes／no／unsure（canonical §5.1.1 逐字），與 core_pain_resolved 並列。⭐ **需求方 2026-08-25 裁定（丙′）**：`no` 具否決權（no 配 APPROVE 硬拒，比照 validation.py:268）；`unsure` **不擋**。⚠️ 契約層判準集中在 cli/src/wf_cli/validation.py，⛔ 不在 review.py。；填 no 或 unsure 時**須說明交付與原始目標的落差**（canonical §5.1.1 逐字），欄名 service_goal_gap，機械必填（空字串即拒）。；⭐ `unsure` 的語意須逐字定義並寫進 templates/review-prompt.md §2：它是「**查核者判不出來**」，⛔ **不是**「卡的目標欄未填」。⚠️ 依據是三層房規（動作不可逆→擋／判不出來指出被判定對象自己有缺陷→擋／指出判定者侷限→放行），導出自 35 個三值以上值域中**開了 10 個**、其餘 25 個依名稱判為非判定。⛔ 交付須逐字寫出該覆蓋率，不得寫成「全表窮舉」。；⭐ CLI 須自行偵測 placeholder 目標：卡面「服務的原始目標」逐字等於「未填寫（本卡於新制欄位定案前建立，2026-08-04）」時，於寫入的事件中**另記為卡面缺陷**（修法歸 baseline-cascade 的 invalidated，amend_cmd.py:211–217 逐字），⛔ 不得被 unsure 蓋掉。⚠️ 該字串須放具名常數並附母體數（197 張中 37 張命中、23 張 OPEN、⛔ 無其他變體或空值）；未驗清單須載明「日後若出現第二種寫法會靜默漏掉」。⚠️ 時序：契約驗證全在遠端呼叫之前（review_cmd.py:206–224）⇒ 本偵測只能在讀卡之後，是**寫入時的警示**，⛔ 不是拒收條件。；⭐ 解析器落點：body 為權威，於 cli/src/wf_cli/card.py 的 parse_requested_by（:743）旁新增 parse_service_goal(body)。⛔ **必須照抄 parse_requested_by 的形狀**——:758 逐字警告「Log 內含字面的『- 需求：』，不切掉就會把歷史當成現況讀」，而服務的原始目標同樣會出現在 Log 的 amend 行裡。⛔ 不採「直接讀 Project fields」的替代方案：那驗的是投影不是權威，且會讓 aiwf#138 各自再寫一份解析。；⛔ 新欄位**只在提交面**必填。須以碼證明契約鏈（parse_structured_block、review_invalid_reasons、validate_review_report）在本卡交付後**仍然只有 review_cmd.py 一個非測試呼叫端**。⚠️ 既有 204 則事件的相容性屬 aiwf#138 射程。；⭐ 事件寫出**兩處都要**：(G1) review.py:485–486 的散文行加 service_goal_still_served，no 時追加否決權註記；(G2) **review.py:983 的 wf_escalation_facts 結構化區塊**在 core_pain_resolved 之後加該鍵，no／unsure 時另加 service_goal_gap；(G3) placeholder 命中時於同區塊加 service_goal_field_placeholder。⛔ **不得升 BLOCK_VERSION**——讀回端 review.py:1091 是「!= BLOCK_VERSION: return None」，一升版 204 則既有事件全部變讀不懂；不升版是安全的（讀回端全走具名 data.get，⛔ 不拒未知鍵）。⚠️ 只寫散文行 = 機器讀不到，aiwf#138 掃不到。；⭐ service_goal_gap 含斷行字元時於**契約層**（提交面）拒收，⛔ 不摺疊。⚠️ 理由已實測收窄：YAML 路徑寫不出多行（解析器逐字「區塊內不得混入散文」直接拒），⇒ **唯一入口是 ```json 路徑**（JSON 的 \n 合法），而實跑證明 _yaml_scalar 的「" ".join(str(value).split())」會**靜默摺疊**。依 aiwf#35 規則二「禁止以正規化代替拒收」。⚠️ 判準須涵蓋 str.splitlines() 認得的全集，⛔ 不得只認 \n。；⭐ 拒收訊息須**可整段轉貼給查核者**：含欄位名、值域三值、no／unsure 的說明要求、canonical §5.1.1 引用。⛔ **不放 effective_from**（review.py:1261 唯一出現且只寫不讀；三個拒收出口全在遠端呼叫之前 ⇒ 只能硬編、必與 cutover 事件漂移）。⛔ 也**不必**叮嚀「說明須單行」——實測七種真實散文形狀（含全形／半形冒號、file:line、引號、反引號、括號）皆逐字通過，查核者不需要學任何跳脫。⚠️ 條文須載明：查核者看不到該訊息（無 wfcli，aiwf#13），送達靠 PM 轉述且其忠實度構造上不可觀測（dispatch-package.md:53）⇒ 真正的修法是 aiwf#66，⛔ 不在本卡射程。；⭐ 更正兩處誤述：(a) 本卡核心痛點原把「服務的原始目標被 amend 過 0 張」寫成量化支持，而 amend_cmd.py:211–217 逐字「不補」⇒ 0 是唯一可能值（已於 op 064ccb28 改述，本條保留為交付時的對照）；(b) 更正 AI_WORKFLOW.md §5.1.1 的未驗條款——它逐字宣稱「亦可被 amend 修改（amend_cmd.py 有一處）」，而該處是「刻意不支援」的說明。；⭐ cutover 事件的 contract 欄須參數化：review.py:1260 寫死 templates/review-escalation.md，而偵測器 body_has_contract_baseline（review.py:1180）只讀鍵名與版本、⛔ 不讀該值 ⇒ 留痕分不出兩次 cutover 各換了什麼。；回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）；replay_escalation_rules 與 canonical_citation_scan 維持綠。；⚠️ 交付時須附「PM 單方面決定清冊」，逐一標明哪些形狀或判準由執行者提出而非 canonical 明文或需求方裁定。」；理由 需求方 2026-08-25 裁定甲，一併把規劃期第八至十輪的實測寫進卡面。資源宣告補上 cli/src/wf_cli/card.py——落點 E 要在該檔新增 parse_service_goal，那是寫入而原宣告漏了（issuecomment-5404548830；實查宣告該檔的 4 張卡活卡交集 0，但 aiwf#105 在 Backlog，開工前須再查）。新增／改寫四條：事件寫出兩處且不得升 BLOCK_VERSION（issuecomment-5404509503：core_pain_resolved 於 review.py:485 與 :983 各一處，讀回端 :1091 一升版即讓 204 則既有事件變讀不懂）；斷行拒收理由收窄為只擋 json 路徑（issuecomment-5404569405：實跑證明 YAML 路徑寫不出多行、七種真實散文形狀逐字通過，而 json 的 \n 合法且 _yaml_scalar 會靜默摺疊）；拒收訊息不必叮嚀單行；解析器落點明列 body 為權威並禁用讀 Project fields 的替代方案。驗證新增 facts 區塊往返與斷行兩條路徑各驗一次。。
- 2026-08-25T11:16:31+08:00 amend by wf-cli（op 02b0220e）→ 驗證：原值「[ ] 值域封閉性：以 yes／no／unsure 之外的值各跑一次，附 rc 與 stderr 原文，證明皆被拒。⛔ 只驗合法值會過是零資訊。；[ ] ⭐ 否決語意的**兩側**負控：`no` 配 APPROVE 須被拒（附 rc 與 stderr 原文）；`unsure` 配 APPROVE 須**通過**（附 rc）。⛔ 只驗一側是零資訊——擋得住不證明放得行。；[ ] 說明必填的負控：填 no 但說明為空、填 unsure 但說明為空，各跑一次證明被拒。；[ ] ⛔ 呼叫端唯一性的**變異檢驗**：先證明現況三個函式各恰一個非測試呼叫端（附 grep 指令與原文），再刻意加第二個呼叫端，證明檢查會轉紅。⚠️ 只跑前半是零資訊。；[ ] ⭐ placeholder 偵測：取那 23 張 OPEN 卡中至少 3 張**真實既有卡**實跑，證明事件中另記為卡面缺陷；再取一張目標正常的真實卡，證明**不誤報**。⛔ 不接受自造樣本。；[ ] ⭐ 拒收訊息內容逐字驗證：附缺欄位時的 stderr 全文，逐項對照驗收第 7 條的四個元素，並證明其中**不含** effective_from；⛔ 不接受「訊息有寫」的自述。；[ ] ⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因（缺什麼、要等什麼、需要誰）；⛔ 標不出原因者代表驗得了、不得列入。」→ 新值「值域封閉性：以 yes／no／unsure 之外的值各跑一次，附 rc 與 stderr 原文，證明皆被拒。⛔ 只驗合法值會過是零資訊。；⭐ 否決語意的**兩側**負控：`no` 配 APPROVE 須被拒（附 rc 與 stderr 原文）；`unsure` 配 APPROVE 須**通過**（附 rc）。⛔ 只驗一側是零資訊——擋得住不證明放得行。；說明必填的負控：填 no 但說明為空、填 unsure 但說明為空，各跑一次證明被拒。；⭐ 斷行拒收須**兩條路徑各跑一次**：YAML 區塊寫多行，證明被解析器擋（附 stderr 原文）；```json 區塊帶 \n，證明被契約層擋（附 rc 與 stderr）。⛔ 只驗一條是零資訊。並附**正向對照**：七種真實散文形狀（含全形／半形冒號、file:line、引號、反引號、括號）逐字往返相同。；⛔ 呼叫端唯一性的**變異檢驗**：先證明現況三個函式各恰一個非測試呼叫端（附 grep 指令與原文），再刻意加第二個呼叫端，證明檢查會轉紅。⚠️ 只跑前半是零資訊。；⭐ facts 區塊的**往返**：新欄位寫進 wf_escalation_facts 後，以現行讀回路徑（review.py:1088 起）解析同一則事件，證明讀得回且逐字相同；再取至少 3 則**真實既有**事件（無新欄位）證明仍解析成功。⛔ 只驗新事件是零資訊。；⭐ placeholder 偵測：取那 23 張 OPEN 卡中至少 3 張**真實既有卡**實跑，證明事件中另記為卡面缺陷；再取一張目標正常的真實卡，證明**不誤報**。⛔ 不接受自造樣本。⚠️ 並證明 parse_service_goal 對 Log 內含該欄位字面的卡不會把歷史讀成現況（取一張確實 amend 過該類欄位的真實卡）。；⭐ 拒收訊息內容逐字驗證：附缺欄位時的 stderr 全文，逐項對照驗收第 9 條的四個元素，並證明其中**不含** effective_from；⛔ 不接受「訊息有寫」的自述。；⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因（缺什麼、要等什麼、需要誰）；⛔ 標不出原因者代表驗得了、不得列入。」；理由 需求方 2026-08-25 裁定甲，一併把規劃期第八至十輪的實測寫進卡面。資源宣告補上 cli/src/wf_cli/card.py——落點 E 要在該檔新增 parse_service_goal，那是寫入而原宣告漏了（issuecomment-5404548830；實查宣告該檔的 4 張卡活卡交集 0，但 aiwf#105 在 Backlog，開工前須再查）。新增／改寫四條：事件寫出兩處且不得升 BLOCK_VERSION（issuecomment-5404509503：core_pain_resolved 於 review.py:485 與 :983 各一處，讀回端 :1091 一升版即讓 204 則既有事件變讀不懂）；斷行拒收理由收窄為只擋 json 路徑（issuecomment-5404569405：實跑證明 YAML 路徑寫不出多行、七種真實散文形狀逐字通過，而 json 的 \n 合法且 _yaml_scalar 會靜默摺疊）；拒收訊息不必叮嚀單行；解析器落點明列 body 為權威並禁用讀 Project fields 的替代方案。驗證新增 facts 區塊往返與斷行兩條路徑各驗一次。。
- 2026-08-25T11:16:31+08:00 amend by wf-cli（op 02b0220e）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:AI_WORKFLOW.md", "file:templates/review-prompt.md", "file:templates/review-escalation.md", "file:cli/src/wf_cli/review.py", "file:cli/src/wf_cli/validation.py", "file:cli/src/wf_cli/commands/review_cmd.py", "file:cli/tests/test_review.py", "file:cli/tests/test_review_service_goal.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:AI_WORKFLOW.md、file:templates/review-prompt.md、file:templates/review-escalation.md、file:cli/src/wf_cli/review.py、file:cli/src/wf_cli/validation.py、file:cli/src/wf_cli/card.py、file:cli/src/wf_cli/commands/review_cmd.py、file:cli/tests/test_review.py、file:cli/tests/test_review_service_goal.py」；理由 需求方 2026-08-25 裁定甲，一併把規劃期第八至十輪的實測寫進卡面。資源宣告補上 cli/src/wf_cli/card.py——落點 E 要在該檔新增 parse_service_goal，那是寫入而原宣告漏了（issuecomment-5404548830；實查宣告該檔的 4 張卡活卡交集 0，但 aiwf#105 在 Backlog，開工前須再查）。新增／改寫四條：事件寫出兩處且不得升 BLOCK_VERSION（issuecomment-5404509503：core_pain_resolved 於 review.py:485 與 :983 各一處，讀回端 :1091 一升版即讓 204 則既有事件變讀不懂）；斷行拒收理由收窄為只擋 json 路徑（issuecomment-5404569405：實跑證明 YAML 路徑寫不出多行、七種真實散文形狀逐字通過，而 json 的 \n 合法且 _yaml_scalar 會靜默摺疊）；拒收訊息不必叮嚀單行；解析器落點明列 body 為權威並禁用讀 Project fields 的替代方案。驗證新增 facts 區塊往返與斷行兩條路徑各驗一次。。
- 2026-08-25T11:21:40+08:00 handoff by wf-cli → owner 待認領；iteration 0；SHA d4ba7ce5f3fa526fc3a7aa0ebbeee3c926e5eb28；證據 T3 規劃閘門通過：需求方 2026-08-25 批註放行（issuecomment 見本卡 timeline 之「T3 規劃閘門」留言）。核心痛點三問已於規劃交付 issuecomment-5404503895 §3 答覆，成功判準為四個可執行指令。規劃期共十一輪，末三輪為 issuecomment-5404548830（doctor 讀卡路徑在 doctor_cmd.py；本卡資源補 card.py）、5404558339（三組既有切片卡實測 §3.2(3)，cpbl#100／#147 屬承接非切片故非反例）、5404569405（實跑解析器：七種真實散文形狀逐字通過、多行已被解析器拒、json 路徑會夾帶換行且 _yaml_scalar 靜默摺疊）、5404609166（⛔ 更正：PM 先前三次資源盤點的 parser 漏掉每張卡第一個資源，數字錯但結論存活；wfcli 守衛讀 body 故不受影響）。卡面 amend 五次：d203faf9／5a2de697／064ccb28（核心痛點，附需求方裁定 URL）／02b0220e。資源互斥以修正後 parser 重查：與 aiwf#138 交集為空、與活卡交集 0 筆。⚠️ 開工前須再查 aiwf#105（📥Backlog／待指派）是否已被派出——它同樣宣告 cli/src/wf_cli/card.py。基準 origin/main = d4ba7ce5。。
- 2026-08-29T15:01:34+08:00 handoff by wf-cli → owner 待指派；iteration 0；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 規劃；踩坑回應 8 族（已檢查 3／不適用 3／發現 2）；證據 阻塞登記（來源狀態 📥Backlog）：https://github.com/ruan6047/ai-workflow/issues/137 之阻塞留言。解除條件＝待審清單機制上線。踩坑清冊兩則發現的完整說明見該留言與清冊各該列。。


## Comment 5404265605 · 2026-08-25T02:26:31Z

## 承接自 aiwf#136（已停止）：既有研究留痕

本卡是 aiwf#136 依需求方 2026-08-25 拆卡裁定分出的 **S7a**。⛔ 不要從零重研究——
#136 已累積十一輪，與本卡直接相關的是：

- [否決權：107 張卡的配對量測](https://github.com/ruan6047/ai-workflow/issues/136#issuecomment-5400086603)　⇒ no 配 APPROVE 僅 1 筆，且該筆繞過 wfcli review。**決定新欄位要不要否決權時的唯一實測依據。**
- [向後相容：383 筆既有事件的分流](https://github.com/ruan6047/ai-workflow/issues/136#issuecomment-5400122894)　⇒ 新欄位設必填會讓既有事件全部 review-invalid，須比照 TRAILER_GUARD_EPOCH 的日期界線。
- [拒收訊息是唯一必經路徑](https://github.com/ruan6047/ai-workflow/issues/136#issuecomment-5404142574)　⇒ --validate-only 對跨家族查核者走不通。
- [⭐ 更正＋派審詞在設計上不留痕](https://github.com/ruan6047/ai-workflow/issues/136#issuecomment-5404179008)　⇒ **驗收第 5 條的由來**：查核契約不對稱，輸出面（review-prompt.md §5）被 review.py 嚴格解析，輸入面（§1–§4 與 dispatch-package.md）零程式消費。

⚠️ 兩點與 #136 卡面不同，⛔ 別照抄：

1. **資源宣告多了 cli/src/wf_cli/validation.py**。#136 漏了它——契約層必填欄實際在 validation.py（core_pain_resolved 於 :258–:270），⛔ 不在 review.py。
2. **卡面「需求：」欄已填 ruan6047**（#136 是「—」，導致該卡的痛點在機械上永遠改不了，card.py:775）。


## Comment 5404310059 · 2026-08-25T02:32:55Z

## 研究交付（第一輪，2026-08-25）：否決權該不該給

**結論先講：⛔ 不該給否決權。** 兩條互相獨立的證據，任一條單獨成立就足以否決。

### 母體與方法

- 母體：兩 repo 全部 Issue（`gh issue list --state all --limit 400`），取卡面 `## Log` **之前**的 `- 服務的原始目標：` 行 ⇒ **197 張**有該欄（aiwf 77／cpbl 120）。⛔ 切掉 Log 是為了不把歷史當現況讀。
- ⚠️ 197 是「有該欄的卡」，⛔ 不是全部卡；沒有該欄的舊卡不在本輪射程。

### 證據一：23 張 **OPEN** 卡的目標逐字是「未填寫」

| 分類 | 張數 | 佔 197 |
|---|---|---|
| placeholder「未填寫（本卡於新制欄位定案前建立，2026-08-04）」 | **37** | 19% |
| ↳ 其中仍 OPEN（還會被查核到） | **23** | — |
| 真的填了目標 | 160 | 81% |

那 23 張：`cpbl#50 #53 #54 #57 #60 #61 #62 #63 #64 #65 #66 #67 #68 #69 #70 #71 #73 #74 #75 #76 #77 #79 #82`

⇒ 這些卡的原始目標**字面上就是「未填寫」**。`service_goal_still_served` 對它們只可能是 `unsure`。
⛔ 若 `unsure` 也阻擋 ⇒ **23 張活卡當場鎖死**；若只有 `no` 阻擋，那 `unsure` 就成了免死金牌，
否決權形同虛設。⇒ **兩種設法都壞**。

### 證據二：目標一旦被共用，**4/4 都是切片兄弟組**

160 張真填目標的卡裡，被 2 張以上共用的有 **4 組 / 9 張（5.6%）**：

- `aiwf#136` `#137` `#138` — 今天的拆卡（§5.1.1 ／ §5.1.2）
- `aiwf#124` `#125` — 一個變異實例 ／ 121 個散文宣稱的稽核
- `cpbl#144` `#145` — SMOKE1 ／ SMOKE2
- `cpbl#100` `#147` — WP 揭露同步 ／ 改由單一來源產生

⇒ 共用**只發生在切片場景**，而切片卡在構造上**只服務目標的一部分**。
⭐ 給否決權 = 每一張切片卡都該被否決。**本卡自己就是實例**：`#137` 的目標涵蓋
§5.1.1 與 §5.1.2，而本卡只做前者。

### ⇒ 建議的設計

`service_goal_still_served` 是**必填但不阻擋**：值域 yes／no／unsure，
填 no 或 unsure 時說明為機械必填（驗收第 2 條）。⛔ 不進 `review_result` 的合法性判斷。
⇒ 它的價值在**留痕可被事後掃描**（那正是 `aiwf#138` 要做的），不在當下擋人。

⚠️ 這與 `core_pain_resolved` 的不對稱是**刻意的**，理由寫進條文：核心痛點是這張卡自己的，
服務的原始目標是**整根鏈**的（chain root）⇒ 前者可由單卡消滅，後者不能。

### 另外兩題的事實（本輪只取事實，不下結論）

**Q2 向後相容分流**：`TRAILER_GUARD_EPOCH = "2026-08-13T00:00:00+08:00"`（`doctor.py:828`），
`doctor_cmd.py:66` 逐字「傳 none 則全範圍一律判定」。
⛔ **S7a 不能沿用該常數**：`doctor.py:37` 逐字 `from .review import ...` ⇒ review 是下層，
反向 import 會成環。⇒ S7a 須自己的 epoch 常數，或把該常數下沉——⚠️ 而 `doctor.py` 是
`aiwf#138` 的宣告資源，下沉屬跨卡改動。**這是規劃階段要裁的。**

**Q3 拒收訊息形狀**：既有房規（`validation.py:258–272`）是
`<欄位> 必填：<一句話> （<canonical 引用>）`，單行、短。
⚠️ **既有訊息沒有任何一則帶 cutover 日期** ⇒ 驗收第 5 條要求的 `effective_from`
是**新形狀**，須列入 PM 單方面決定清冊。

### ⚠️ 本輪未驗

- **`unsure` 在既有 review 事件裡的實際使用率**：⛔ 未查。⚠️ 依既有紀律本項**不進推理鏈**——
  上面兩條證據都不依賴它。
- **那 23 張 placeholder 卡是否真的還會被查核**（可能多數已實質停擺）：⛔ 未查。
  ⚠️ 但即使只剩 1 張會被查核，證據一的結構問題仍成立。


## Comment 5404332084 · 2026-08-25T02:36:06Z

## 研究交付（第二輪，2026-08-25）：⛔ 推翻承接自 aiwf#136 第三輪的向後相容前提

### 被推翻的是什麼

`aiwf#136` [第三輪](https://github.com/ruan6047/ai-workflow/issues/136#issuecomment-5400122894)結論：
「新欄位設必填**即使 383 筆既有事件全部 review-invalid**，須比照 TRAILER_GUARD_EPOCH 的日期分流」。
⇒ 本卡驗收第 3 條就是照它寫的。

**⛔ 那個前提不成立。既有事件不會變成 review-invalid，因為沒有任何路徑會再讀它們。**

### 證據：整條解析＋驗證鏈只有一個呼叫端

全 repo grep（`--include='*.py'`，排除 `.venv` 與 `cli/tests/`）：

| 函式 | 定義 | **非測試呼叫端** |
|---|---|---|
| `parse_structured_block` | `review.py:422` | `review_cmd.py:209` |
| `review_invalid_reasons` | `validation.py:159` | `review_cmd.py:216` |
| `validate_review_report` | `validation.py:240` | `review_cmd.py:224` |

三者**各自恰好一個**，且都在 `review_cmd.py` 的同一段——也就是**提交當下、對正在被提交的那份文字**。
⛔ 沒有任何一處對 GitHub 上已存的留言重跑。

補強（避免「grep 沒中就當不存在」）：`doctor.py` 對 `parse_structured_block`、
`FINDING_KEYS`、`find_block_by_key` 三個名字**全部 0 命中**；`doctor.py:37` 只 import
`BASELINE_LOG_TAG`／`CHECKPOINT_LOG_TAG`／`STATUS_BY_RESULT`（Log 標籤與狀態對照，非契約驗證）。
`scripts/replay_escalation_rules.py` 走的是自建案例（`sha_stub`／`attempt_uid`／`new_finding`），
⛔ 不讀既有留言。

### ⇒ 驗收第 3 條現在是**構造上不會失敗**的檢查

它要求「既有 review 事件不得因新欄位而解析失敗或被判 review-invalid」——
而既有事件根本不進解析器。⇒ ⛔ 它必然通過，證不了任何事。**須改寫。**

### 順帶：Q2 的「日期 epoch」是問錯題，而正解早已裁定

`aiwf#35 WF-EVENT-MARKER-V2-SCOPE1`（已 CLOSED）的 R1 裁定逐字：

> v2 只加兩鍵…**其餘語意欄位一律進 payload**——…牆的成因不是 v1 少幾個欄位，是識別符與
> 語意欄位擠在同一個封閉鍵集合裡，**分開後往後加欄位不再需要升版本**。

⇒ `service_goal_still_served` 是語意欄位 ⇒ 進 payload（fenced 區塊）⇒ **不需要升 marker 版本、也不需要 epoch**。

⚠️ 且 payload 側本來就容忍未知鍵：`validation.py:187` 逐字
`missing = [k for k in FINDING_KEYS if ...]` —— 只查**必填**，⛔ 不拒未知鍵。

⚠️ 但 `#35` 的 v2 **只有設計、沒有實作**：實際事件 marker 仍是 v1、`BLOCK_VERSION = "v1"`
（`review.py:593`），該卡自陳 `serialize_v2()` 只存在探針進程內。⇒ 本卡**不依賴** v2 落地，
但也⛔ 不得宣稱 v2 已可用。

### ⭐ 真正的向後相容風險在 aiwf#138，不在本卡

既有事件唯一會被重讀的場合，是 `#138`（S7b）要新增的**事後重驗**。
量測：兩 repo 全部 Issue 留言中，含以 `review_result:` 開頭之行者 **204 則**
（aiwf 136／cpbl 68），區間 **2026-08-10 → 2026-08-24**。
⚠️ 204 是**上界**——該 pattern 也會命中範本引用與查核者報告原文貼文，⛔ 未逐則人工分辨。
⇒ 那 204 則全部沒有新欄位。**S7b 設計掃描面時要處理的是這批，本卡不處理。**

### ⇒ 建議的驗收第 3 條改寫

把「既有事件不得 review-invalid」換成**會失敗的版本**：

> ⛔ 新欄位**只在提交面**必填。須以碼證明契約鏈（`parse_structured_block`／
> `review_invalid_reasons`／`validate_review_report`）在本卡交付後**仍然只有
> `review_cmd.py` 一個非測試呼叫端**；⇒ 若有人日後把它接到既有事件上，該檢查會轉紅。
> ⚠️ 並在條文中指名：既有 204 則事件的相容性屬 `aiwf#138` 射程。

⇒ 這個版本說得出「什麼結果會推翻它」（多一個呼叫端就紅），⛔ 原版說不出。

### ⚠️ 本輪未驗

- **204 則裡實際由 `wfcli review` 寫入的有幾則**：⛔ 未分辨（需逐則看留言 author 與 marker）。
  ⚠️ 不進推理鏈——上面的結論只依賴「呼叫端恰好一個」，與該批數量無關。
- **`#35` 標題所稱「v1 鍵集合封閉」的封閉性是否也及於 payload 鍵**：本輪依 R1 裁定原文
  判為「不及於」（語意欄位進 payload），⛔ 未讀 `_CONFORMANT_MARKER_RE` 本體確認。
  ⚠️ 這一項**有進推理鏈**——若判斷有誤，Q2 的結論要重來。規劃階段須先關掉它。


## Comment 5404365885 · 2026-08-25T02:41:06Z

## 研究交付（第三輪，2026-08-25）：⛔ canonical §5.1.1 自己的未驗條款事實錯誤，而本卡的「量化支持」是算術必然

前兩輪我都在轉述 §5.1.1。**本輪讀原文**（`AI_WORKFLOW.md:365–381`），查出三件。

### 一、§5.1.1 的未驗條款寫錯了

原文逐字：

> ⚠️ 未驗：`服務的原始目標` **亦可被 `amend` 修改**（`amend_cmd.py` 有一處）。若它同樣漂移，
> 檢查它一樣擋不住——本卡未查該欄的歷史 amend 次數，⇒ 該檢查的有效性未經證實。

**⛔ 沒有那條路徑。** `amend_cmd.py` 對該欄唯一的一處是 `:212`，內容逐字是：

> - **服務的原始目標**：**不補**。它是**鏈級**欄位（canonical §3.3「這根鏈最終要解的…

⇒ 那一處是「刻意不支援」的說明，⛔ 不是實作。全 CLI grep `service_goal`：
寫入端只有 `open_cmd.py`（`:171`／`:221`／`:278`）；其餘全是讀（`card.py` 渲染、
`project.py` 欄位映射、`snapshot.py` 投影、`validation.py:108` 只驗非空）。
⇒ **開卡之後沒有任何動詞改得了它。**

### 二、⇒「被 amend 過 0 張」是算術必然，不是觀測

本輪獨立重量（母體＝兩 repo 全部 Issue 中有該欄者，掃 `## Log` 內
`amend by wf-cli（op …）→ <欄位>：` 行）：

- 母體 **197 張**
- 「amend → 服務的原始目標」：**0 張**
- 「amend → 核心痛點」：**16 張**（累計 28 次）

⭐ 而 amend 全史寫過的欄位**只有 7 種**：驗收條件 77／資源宣告 63／驗證 48／核心痛點 28／
spec 基線 10／級別 2／Initiative 1。⇒ 服務的原始目標不在其中，**構造上不可能在其中**。

⛔ **本卡核心痛點與驗收第 7 條把它寫成「量化支持」是誤導**——它讀起來像「我們觀察到 0」，
而正確陳述是「**0 是唯一可能的值**」。⚠️ 這正是既有紀律裡「構造上不會失敗的檢查」那一族。

⚠️ 順帶：`aiwf#136` 開卡時記的是「15 張」，本輪量到 **16 張**。⛔ 未追差異來源
（母體切法或 pattern 不同）；本輪一律用自己量的 16 並附方法。

### 三、⭐ 但論點變強，不是變弱

§5.1.1 的主張是「檢查了會漂移的欄位，沒檢查不會漂移的那個」。
⇒ 不漂移現在是**構造保證**而非運氣 ⇒ 主張**更成立**。
⚠️ 該改的是**呈現方式**：從「量化支持」改成「結構性事實」，並回頭**更正 §5.1.1 的未驗條款**
（它宣稱的懷疑理由不存在）。

### 四、⭐⭐ 這對否決權的影響是決定性的

第一輪的證據一是「23 張 OPEN 卡的目標逐字是『未填寫（本卡於新制欄位定案前建立，2026-08-04）』」。
當時我以為那是「需要先做一次遷移」。

**⛔ 不是。沒有遷移通道。** 既然 `open` 之後無任何動詞寫得了該欄，那 23 張卡
**永遠**答不出 `yes`。⇒ 給否決權 = 永久鎖死 23 張活卡，且**修法不在本卡射程內**
（要先有人做出 `--service-goal` 寫入通道，那是另一張卡）。

### 五、文本上也不支持給否決權

§5.1.1 逐字：「與 `core_pain_resolved` **並列**」。
⚠️ 而條文對第一判準明寫「**具否決權**」，對新欄位**一個字都沒寫**。
⇒ 「並列」＝並排列出，⛔ 不蘊含同等強制力。

⚠️ 但原文另有一句「**值域語意與填答者比照第一判準**」，而
`CORE_PAIN_VALUES = ("yes", "no")`（`review.py:36`）——**第一判準沒有 `unsure`**。
⇒ 「比照」在值域這一點上**無法照抄**，`unsure` 是 review 契約裡前所未有的第三值。
**它的語意須由本卡自己定義並寫進條文**，⛔ 不能靠「比照」帶過。

### ⇒ 本輪建議的卡面改動（待需求方裁定否決權後一併 amend）

1. 核心痛點與驗收第 7 條：把「0 張 vs 15 張」的**量化支持**改述為
   「**該欄開卡後無寫入通道**（`amend_cmd.py:212` 逐字不補），故不漂移是構造保證」，
   並附本輪的 16 張／7 種欄位對照作為**核心痛點側**的實測。
2. 新增驗收：**更正 canonical §5.1.1 的未驗條款**（它宣稱的 amend 路徑不存在）。
   ⚠️ 這會動 `AI_WORKFLOW.md`，⛔ 不在本卡現行資源宣告內，須先 amend 資源。
3. 新增驗收：**`unsure` 的語意須逐字定義**（何時該填、與 `no` 的分界、說明要求是否相同）。

### ⚠️ 本輪未驗

- **15 vs 16 的差異來源**：⛔ 未追。⚠️ 不進推理鏈——兩個數都遠大於 0，結論只依賴「核心痛點會被 amend、服務的原始目標不會」。
- **是否有非 wfcli 的路徑改過該欄**（有人直接編輯 Issue body）：⛔ 未查。⚠️ 若有，卡面現值仍會與 Project 欄位不同步；但那屬 `aiwf#138` 的事後掃描射程。


## Comment 5404373350 · 2026-08-25T02:42:13Z

## 研究交付（第四輪，2026-08-25）：⛔ 驗收第 5 條的 `effective_from` 拿不到，而且它的讀者不是查核者

### 一、`effective_from` 在全 CLI 只出現一次，而且是**只寫不讀**

```
cli/src/wf_cli/review.py:1261:  f"effective_from: {_yaml_scalar(timestamp)}",
```

⇒ 全 repo 就這一處。它把 cutover 當下的 `timestamp` **寫進**區塊，
⛔ **沒有任何一行把它讀回來。**

### 二、而拒收時**不可能**去卡上讀它

`review_cmd.py` 的 docstring 逐字：

> **驗證全部在任何遠端呼叫之前**：不合格式一律 fail closed，不寫任何遠端狀態
> （**連讀 project 都不做**，除了 `--validate-only` 本來就不碰網路）

碼序也對得上（`:206`–`:224`）：`_read_input` → `parse_structured_block` →
`review_invalid_reasons`（`:216`，return 4）→ `validate_review_report`（`:224`，return 2）。
⇒ 三個拒收出口**全在遠端呼叫之前**。

⇒ 若要在訊息裡放 `effective_from`，只能寫成**碼內硬編常數**。
⚠️ 而 cutover 事件的值是執行當下的 `now`，⇒ 兩者只能靠「先跑 cutover、再改常數、再發版」
勉強對齊，中間必然有一段**碼與事實不符**的窗口。**那是自造漂移。**

### 三、⭐ 更根本的問題：那則訊息的讀者不是查核者

跨家族查核者沒有 `wfcli`（`templates/dispatch-package.md:53` 逐字「它沒有 GitHub 寫入通道…
**貼不了收據**」）。⇒ **跑 `wfcli review` 的是 PM**，被拒收的訊息**印在 PM 的終端**。

⇒ 鏈條實際是：查核者寫報告 → PM 跑 `wfcli review` → 拒收 → **PM 回去跟查核者要那個欄位**。

⭐ 這改變了該條驗收的目標：
- **強制力**本來就成立——沒填就寫不進去，⛔ 這不需要訊息寫得好。
- 訊息要優化的是**PM 轉述的忠實度**，⇒ 它該是**可以整段貼給查核者的文字**，
  ⛔ 不是給工程師看的診斷輸出。

⚠️ 我在第二輪與驗收第 5 條把它寫成「讓查核者自己學會」——**那是錯的**，查核者看不到它。

### ⇒ 建議改寫驗收第 5 條

> ⭐ 拒收訊息須**可整段轉貼給查核者**：含欄位名、值域三值、`no`／`unsure` 的說明要求，
> 以及 canonical §5.1.1 的引用（⛔ **不放 `effective_from`**——`review.py:1261` 是唯一
> 出現處且只寫不讀，而拒收發生在任何遠端呼叫之前 ⇒ 只能硬編，必然與 cutover 事件漂移）。
> ⚠️ 沿用既有房規（`validation.py:258–272`）的形狀：`<欄位> 必填：<一句話>（<canonical 引用>）`。

⇒ 這樣它**不新增形狀**（第一輪查到既有訊息沒有任何一則帶 cutover 日期），
也就不必進 PM 單方面決定清冊。

### ⭐ 附帶：這條路徑無法被觀測的部分仍然存在

PM 是否忠實轉述那則訊息，⛔ 沒有機器可檢查的東西（同 `dispatch-package.md:53` 的自陳）。
⇒ 本卡能做到的上限是「**讓那則訊息值得被整段貼**」，⛔ 不是「保證它被貼」。
⚠️ 真正的修法是 `aiwf#66`（派審詞由 handoff 產生），**不在本卡射程**——須寫進條文，
⛔ 不得讓人以為本卡把送達問題解決了。

### ⚠️ 本輪未驗

- **PM 實際轉述拒收訊息的次數與忠實度**：⛔ 構造上不可觀測（無留痕），⚠️ 依 §6.4.2 這是
  **unobservable 不是未查**。上面的結論不依賴它——只依賴「查核者看不到該訊息」這個
  已由 `dispatch-package.md:53` 逐字支持的事實。
- **`--validate-only` 是否真的零網路**：docstring 如此宣稱且碼序相符，⛔ 本輪未實跑
  （會需要真的送一份載荷）。⚠️ 若它其實碰網路，結論不變——查核者沒有 wfcli，跑不了它。


## Comment 5404384908 · 2026-08-25T02:44:00Z

## 研究交付（第五輪，2026-08-25）：`unsure` 該不該擋，房規已經有答案——而且不是我第一輪講的那個理由

第三輪指出 `CORE_PAIN_VALUES = ("yes", "no")`（`review.py:36`），`unsure` 是 review 契約裡
前所未有的第三值，⇒ canonical 說的「值域語意比照第一判準」在這一點上照抄不了。
**本輪去找房裡既有的三值前例。找到兩條，而且預設相反。**

### 前例甲：`cleanup.py` —— 判不出來 **等同阻擋**

- `:394`　`"unobservable": frozenset()`（零授權動作）
- `:402` 逐字：「只有全部 `pass` 才 proceed；`fail` 與 **`unobservable` 同等阻擋**」
- `:519` 逐字：「`unobservable`：判不出來。與 `diverged` **同樣阻擋**」

### 前例乙：`registry.py` —— 判不出來 **一律放行**

`LOCAL_OBSERVATION_ACTIONS`（`:722`）全表 8 格，**只有一格 `refuse`**，而註解逐字要求
那一格必須是「**實際觀測到的矛盾**」。所有「判不出來」的碼——`expected_repo_unknown`、
`observed_repo_unidentifiable`、`target_absent`、`target_not_in_repo`——**全部 `pass`**。

⚠️ 而它帶著裁定原文（`:719–721`）：

> `nesting_conflict` 刻意只 `warn`：它的全部證據是…推測。
> **上一版讓這種推測擋人，被需求方 2026-08-13 推翻——推測可以說「這裡看起來不對」，
> 不可以當判定。**

### ⇒ 區分兩條前例的原則

| | `cleanup` | `registry` |
|---|---|---|
| 被閘門擋住的動作 | **不可逆**（刪分支、移 worktree） | 可逆（登記一筆 worktree） |
| 判定的依據 | 實際觀測（merge proof） | **推測** |
| 判不出來時 | 阻擋 | 放行／警示 |

⇒ **判準是兩問：擋住的是不是不可逆的事？依據是觀測還是推測？**

**套到 `service_goal_still_served`**：
- 擋住的是一次 `APPROVE` ⇒ **可逆**（重審即可，`REQUEST_CHANGES` 後走 handoff 遞增 iteration）。
- 「交付還服不服務原始目標」是**對齊性的判斷** ⇒ 推測，⛔ 不是觀測。

⇒ **依需求方 2026-08-13 自己立的原則，`unsure` 不該擋。**
⭐ 這比我第一輪的理由（23 張卡答不出 yes）**強**——那是資料現況，這是既有裁定。

### ⭐ ⇒ 因此浮出第三個選項，比原本的「給／不給」都準

**`no` 擋、`unsure` 不擋（警示 ＋ 說明必填）。**

- `no` ＝ 查核者**實際判定**交付沒服務原始目標 ⇒ 那是判定不是推測 ⇒ 比照 `cleanup` 擋。
- `unsure` ＝ 判不出來 ⇒ 比照 `registry` 放行，但**說明機械必填**（canonical §5.1.1 已要求），
  且留痕交給 `aiwf#138` 事後掃描。

⚠️ 風險：`unsure` 成為逃生門。⇒ 緩解有兩層——說明必填（空字串即拒），
以及 S7b 的掃描會把 `unsure` 的累積量變成看得見的數字。⛔ 本卡不假裝解決該風險。

### ⚠️ 那 23 張卡的正解不是「補欄位」，而且這是既有裁定

第三輪我說「沒有遷移通道」。本輪讀到那是**刻意的**。`amend_cmd.py:211–217` 逐字：

> **服務的原始目標**：不補。它是**鏈級**欄位（canonical §3.3…），是鏈式停損兩問的錨。
> **單卡改會與同鏈其他卡去同步，而 CLI 沒有鏈的視野。** 它的變更本質是
> `baseline-cascade.md` 的 `invalidated`（**退回 Gate 或由需求方裁定停止**），不是欄位編輯。

⇒ ⛔ 「先做一個 `--service-goal` 寫入通道再給否決權」**不是單純的另一張卡，是要推翻這條裁定**。
⇒ 那 23 張「未填寫」卡的合規修法是走 cascade（退回 Gate 或裁定停止），
**每張都要需求方經手**。⚠️ 若採「`unsure` 也擋」，那 23 張在走完 cascade 前一律過不了查核。

### ⇒ 更新後的建議

| | 甲（原建議） | **丙（本輪新增，改推這個）** | 乙 |
|---|---|---|---|
| `no` | 不擋 | **擋** | 擋 |
| `unsure` | 不擋 | **不擋（警示＋說明必填）** | 擋 |
| 與 2026-08-13 裁定 | 相符 | **相符** | ⛔ 抵觸（推測當判定） |
| 那 23 張卡 | 不受影響 | 不受影響 | 全部需先走 cascade |

⭐ **改推丙**：甲讓一個**實際判定為 no** 的查核仍可 APPROVE，那與 `cleanup` 的前例不一致
且無理由；丙兩邊都對得上房規。

### ⚠️ 本輪未驗

- **`unsure` 被當逃生門的實際比率**：⛔ 構造上量不到（欄位還不存在）。
  ⚠️ 依 §6.4.2 這是「要等什麼」——等本卡上線後由 `aiwf#138` 的掃描產生第一批數字。
- **兩條前例是否還有第三條**：本輪 grep `unobservable｜UNDECIDABLE｜unknown` 命中 20 行、
  收斂到 `cleanup` 與 `registry` 兩處。⛔ 未窮舉全部三值判斷（可能有不用這些字面的）。
  ⚠️ 這**有進推理鏈**——若存在第三條且與上述原則相反，本輪的判準要重審。


## Comment 5404398512 · 2026-08-25T02:46:00Z

## 研究交付（第六輪，2026-08-25）：關掉第五輪自標的推理鏈缺口——而它推翻了第五輪的判準

第五輪我標「⛔ 未窮舉全部三值判斷（可能有不用這些字面的）。⚠️ 這**有進推理鏈**」。
⭐ 而用關鍵字找「不含該關鍵字的前例」在構造上必然落空 ⇒ **改用形狀搜尋**：
AST 掃 `cli/src/wf_cli/**.py`，取所有 `Literal[...]` 與三元素以上的字串 tuple 常數。

**母體：35 個三值以上值域**（⛔ 第五輪說的「兩處」是錯的）。其中帶「判不出來」成員的
逐一開來看：

| 值域 | 判不出來的成員 | 處置 |
|---|---|---|
| `cleanup.py:279` `free/occupied/unobservable` | `unobservable` | **阻擋** |
| `cleanup.py:328` `pass/fail/unobservable` | `unobservable` | **阻擋** |
| `cleanup.py:520` merge proof | `unobservable` | **阻擋** |
| `registry.py:494` 軸A 歸屬 | `card_repo_undeterminable`、`declared_repo_unparseable` | **阻擋** |
| `registry.py:704` 軸B 本機觀測 | `expected_repo_unknown` 等四個 | **放行** |
| `doctor.py:96` review 事件狀態 | `unobservable` | 只記錄 |
| `doctor.py:111` `identity_basis` | `not_applicable` | 只記錄 |
| `doctor.py:1423` `DriftVerdict` | `undecidable` | 只記錄 |

⚠️ ⛔ **未逐一開的**：其餘 27 個值域多為「種類列舉」而非「判定」（如 `TIERS`、
`SEVERITIES`、`FINDING_CLASSES`），本輪以名稱與定義行判斷其不含「判不出來」語意，
⛔ 未逐個讀上下文。

### ⇒ 判準比第五輪講的複雜：是**三層**，不是一問

⭐ 關鍵是 `registry.py` **同一個檔裡兩條相反的規則**，而它自己寫出了差別：
軸A 是「可攜。**純字串比對**」，軸B 是「機器局部。只說**這台機器現在看到什麼**」。

1. **被擋住的動作不可逆 → 判不出來一律阻擋。**（`cleanup`；裁定原文「噪音比不可逆的資料遺失便宜」）
2. 動作可逆，但「判不出來」指出的是**被判定對象自己有缺陷** → 阻擋。
   （`registry` 軸A：卡的宣告解析不出來，那是卡的問題）
3. 動作可逆，且「判不出來」指出的是**判定者的侷限** → 放行／警示／只記錄。
   （`registry` 軸B、`doctor` 全部三個；後者是唯讀工具）

### ⭐⭐ ⇒ 問題在 `unsure` 這一個值**同時裝了第 2 層和第 3 層**

- 那 23 張卡的目標欄逐字是「未填寫（本卡於新制欄位定案前建立，2026-08-04）」
  ⇒ 查核者填 `unsure` 是因為**卡自己有缺陷** ⇒ 依第 2 層該擋。
- 一般卡上查核者填 `unsure`，是因為**他判不出對齊與否** ⇒ 依第 3 層不該擋。

⇒ **同一個值，房規要求相反的處置。** ⛔ 這不是「選擋或不擋」，是**值域設計有問題**。

### ⇒ 修法：把「卡自己有缺陷」從 `unsure` 裡拿出來，由 CLI 自己判

`wfcli review` 寫入前本來就要讀卡（寫 Log 行）⇒ **它看得到目標欄的值**。
⇒ 讓 CLI 自己偵測 placeholder（逐字比對那串 2026-08-04 的文字），
並在事件裡記成**與 `unsure` 不同的處置**——「本卡的原始目標欄未填，
查核者無從對照」⇒ 那是卡的缺陷，歸 cascade（`amend_cmd.py:211–217` 逐字：
變更本質是 `baseline-cascade.md` 的 `invalidated`），⛔ 不是查核者的答案。

⚠️ 時序限制（第四輪已證）：契約驗證全在遠端呼叫**之前**，⇒ 該偵測**只能放在讀卡之後**，
故它是**寫入時的警示**，⛔ 不能是拒收條件。

### ⇒ 建議（取代第五輪的丙）

**丙′**：`no` 擋（實際判定，比照第一判準與第 2 層）；`unsure` 不擋但說明機械必填（第 3 層）；
**外加** CLI 自行偵測 placeholder 目標並在事件中另記，⇒ 那 23 張卡的問題**不會被 `unsure` 蓋掉**。

⭐ 這樣三層房規在本卡上**全部對得上**，⛔ 不需要為本卡破例。

### ⚠️ 本輪未驗

- **27 個未逐一開的值域裡是否藏著第四條規則**：⛔ 未讀上下文，只依名稱判斷。
  ⚠️ 這**有進推理鏈**（三層判準宣稱是全表導出的）。⇒ 規劃階段若要把三層寫進條文，
  須先逐一開完；若只用來支持本卡的取捨，現有 8 個已足。
- **placeholder 字串是否只有那一種寫法**：本輪只比對了 2026-08-04 那串逐字文字。
  ⛔ 未查是否還有其他「等同未填」的寫法（如空白、`—`）。⚠️ 實作前必須查——
  只認一種寫法會漏，那是既有紀律裡「只認一種變體」的同族。


## Comment 5404407396 · 2026-08-25T02:47:25Z

## 研究交付（第七輪，2026-08-25）：關掉第六輪自標的兩個推理鏈缺口

### 缺口一：placeholder 目標是不是只有一種寫法 ⇒ **是，只有一種**

方法：取 197 張卡的目標欄全值，以 `未填|待填|待定|TODO|^—$|^-$|^$|不適用|N/?A`
**外加「長度 ≤ 6 字」**兩條篩選（後者是為了抓不含關鍵字的短敷衍值）。

命中 40 張，逐一看：

- **37 張**逐字同一串：`未填寫（本卡於新制欄位定案前建立，2026-08-04）`，⭐ 全在 cpbl，
  其中 **23 張 OPEN**（與第一輪的 23 張逐張相符）。
- 另 3 張是**誤命中**：`ai#95`／`ai#38`／`cpbl#135` 的目標是正常散文，只是內文含「未…」字樣。
- ⛔ **沒有任何空值、`—`、`TBD` 或其他變體。** 最短的真實目標是 8 字（`cpbl#146`「狀態寫入通道可用」）。

⇒ 第六輪建議的「CLI 自行偵測 placeholder」**可以逐字比對實作**，⛔ 不需要模糊比對。
⚠️ 但實作須把該字串放進**具名常數並附本輪母體數**，⇒ 日後若出現第二種寫法，
檢查會靜默漏掉——那一點須寫進未驗清單，⛔ 不能假裝已窮盡未來。

### 缺口二：其餘 27 個值域裡有沒有第四條規則 ⇒ **沒有**

第六輪只開了 8 個。本輪把剩下 27 個裡**名稱上可能是「判定」而非「種類列舉」**的兩個開來看：

- `cleanup.py:1136` `RemoteDeleteVerdict = delete/absent/refuse`
  ——註解逐字：「`absent` **不是放行也不是拒絕**：遠端分支已不存在，本來就無事可做」
  ⇒ 那是「無事可做」，⛔ 不是「判不出來」。不構成第四條。
- `doctor.py:61` `SubmoduleFinding.status = ok/uninitialized/out_of_sync`
  ⇒ 唯讀回報，且三個成員都是**確定的觀測結果**，無「判不出來」成員。不構成第四條。

其餘 25 個依定義行判為種類／欄位名／字元集列舉（`TIERS`、`SEVERITIES`、`FINDING_CLASSES`、
`ATTRIBUTIONS`、`FINDING_KEYS`、`CHECKPOINT_DECISIONS`、`ROUTING_*` 等），⛔ 未逐個讀上下文。

⇒ **第六輪的三層判準維持成立**，其導出母體是 35 個值域中**開了 10 個**、
其餘 25 個依名稱判為非判定。⚠️ 這個覆蓋率須逐字寫進交付，⛔ 不得寫成「全表窮舉」。

### ⇒ 研究階段的結論收斂為

1. **否決權**：採丙′——`no` 擋、`unsure` 不擋但說明機械必填、外加 CLI 自行偵測 placeholder 目標。
   （依據：第五／六輪的三層房規；第一／三輪的 23 張卡；§5.1.1 對新欄位未寫「具否決權」。）
2. **向後相容**：⛔ 不需要日期 epoch（第二輪：契約鏈三個函式各恰一個非測試呼叫端，全在提交路徑）。
3. **拒收訊息**：⛔ 不放 `effective_from`（第四輪：唯一出現處只寫不讀，且拒收在遠端呼叫之前）；
   改為可整段轉貼給查核者的文字 ＋ canonical 引用，沿用既有房規形狀。
4. **卡面須更正**：核心痛點與驗收第 7 條的「量化支持」改述為結構性事實
   （第三輪：`amend_cmd.py:211–217` 逐字「不補」⇒ 0 是唯一可能值）；
   並更正 canonical §5.1.1 的未驗條款（它宣稱的 amend 路徑不存在）。

⇒ **待需求方裁定第 1 項後即可離開研究階段。** 第 2–4 項是事實導出，⛔ 不需裁定，
但第 4 項會動 `AI_WORKFLOW.md`，須先 amend 資源宣告。


## Comment 5404453207 · 2026-08-25T02:54:47Z

## 裁定（需求方，2026-08-25）

本則由 PM 依需求方於本次 session 的口頭裁定「好」逐字轉錄寫入，⚠️ 帳號為需求方本人的 token。

**一、`service_goal_still_served` 的否決語意採丙′**

- `no` **具否決權**：`no` 配 `APPROVE` 硬拒，比照 `validation.py:268` 對 `core_pain_resolved` 的處置。
- `unsure` **不擋**，但說明機械必填（空字串即拒）。
- 外加：**CLI 自行偵測 placeholder 目標**，把「卡面目標未填」從 `unsure` 裡拆出來，另記為卡面缺陷。

依據為研究第五至七輪：以 AST 形狀搜尋窮舉 35 個三值以上值域、開其中 10 個導出三層房規
（動作不可逆→擋／判不出來指出被判定對象自己有缺陷→擋／指出判定者侷限→放行），
而 `unsure` 一個值同時裝了第 2 層與第 3 層。

**二、授權更正核心痛點**

把「服務的原始目標被 `amend` 過 0 張」的**量化支持**改述為**結構性事實**：
`amend_cmd.py:211–217` 逐字「不補」，該欄開卡後無任何寫入通道，⇒ 0 是唯一可能的值，
⛔ 不是觀測結果。核心痛點側改附實測：197 張母體中核心痛點被 amend **16 張**（累計 28 次），
且 `amend` 全史只寫過 **7 種**欄位。


## Comment 5404503895 · 2026-08-25T03:02:26Z

## 規劃交付（2026-08-25）

### 一、實作落點（檔:行 → 改什麼）

| # | 落點 | 動作 |
|---|---|---|
| A | `review.py:36` `CORE_PAIN_VALUES` 旁 | 新增 `SERVICE_GOAL_VALUES = ("yes","no","unsure")`。⚠️ 與第一判準**刻意不同值域**，須就地註解說明（§5.1.1 說「值域語意比照第一判準」，而第一判準沒有 `unsure`） |
| B | `review.py:103–118` `ReviewReport` | 加 `service_goal_still_served: str` 與 `service_goal_gap: str`。⛔ **不給預設值**——唯一建構點是 `validation.py:363` 的 kwargs 建構，不給預設值可讓漏填當場爆，⛔ 不靜默成空字串 |
| C | `validation.py:272` 之後（`core_pain_resolved` 檢查尾端） | 四段檢查：必填／值域封閉／`no` 配 `APPROVE` 硬拒／`no`＋`unsure` 時 `service_goal_gap` 非空 |
| D | `validation.py:363` | 組裝時傳入兩個新欄 |
| E | `card.py:743` `parse_requested_by` 旁 | 新增 `parse_service_goal(body)`。⭐ **照抄 `parse_requested_by` 的形狀**：`:758` 逐字警告「Log 內含字面的『- 需求：』，不切掉就會把歷史當成現況讀」——⚠️ 服務的原始目標**同樣**會出現在 Log 的 amend 行裡，同一個陷阱 |
| F | `review_cmd.py:317` 附近（`item.body` 已可用處，即 `check_checkpoint_gate(..., card_body=item.body)` 那一行的鄰近） | placeholder 偵測：`parse_service_goal(item.body)` 逐字等於常數時，印警示並把該事實傳進事件呈現。⚠️ 時序上這裡**已過遠端呼叫**，故只能是警示，⛔ 不是拒收 |
| G | `review.py` 的 `render_verdict_comment`（`:530` 附近） | 事件加一行 `- service_goal_still_served：**<值>**`，比照現行 `- core_pain_resolved：**yes**` 的呈現；placeholder 命中時另加一行 |
| H | `templates/review-prompt.md` §2／§5 | §2 加第二判準段落（含 `no` 擋、`unsure` 不擋的裁定）；§5 YAML 區塊加兩鍵與註解 |
| I | `templates/review-escalation.md` §2 | schema 同步 |
| J | `AI_WORKFLOW.md:377–380` | 更正 §5.1.1 未驗條款（它宣稱的 `amend` 路徑不存在） |
| K | `review.py:1259–1261` | cutover 事件的 `contract` 欄參數化 |

### 二、PM 單方面決定清冊（草稿，交付時須完整）

1. **說明欄的鍵名 `service_goal_gap`** —— canonical 只說「須說明」，⛔ 沒給鍵名。
2. **拒收訊息四行而非一行** —— 既有房規（`validation.py:258–272`）全是單行。
   偏離理由：該訊息的讀者是 PM，要能整段轉貼給沒有 `wfcli` 的查核者。
3. **`ReviewReport` 兩個新欄不給預設值** —— 房內其他欄有給（`writer_only_keys=()`）。
4. **placeholder 偵測讀 body 而非 Project 欄位** —— 依 body 為權威、Project 為導出的既有慣例。
5. **`SERVICE_GOAL_VALUES` 不與 `CORE_PAIN_VALUES` 合併** —— 值域確實不同。

### 三、T3 規劃閘門：核心痛點三問（canonical §3.1）

- **痛點是什麼**：卡有兩個目標欄位，review 只查會漂移的那個（核心痛點，197 張中 16 張被 amend），
  不查構造上不會漂移的那個（服務的原始目標，開卡後無寫入通道）。
- **成功怎麼觀察**：`wfcli review` 對缺該欄的載荷 rc≠0；對 `no`＋`APPROVE` rc≠0；
  對 `unsure`＋`APPROVE` rc=0；對那 23 張 placeholder 卡實跑，事件中出現卡面缺陷另記。
  ⇒ **四個都是可執行指令，⛔ 不是主觀判斷。**
- **最大的未驗證前提**：**新欄位會被認真填**。⛔ 機械上只能保證「有填且值合法且非空說明」，
  ⚠️ 保證不了填的是真話。⇒ 該前提的**觀測要等 `aiwf#138` 的事後掃描**產生第一批分佈，
  ⛔ 本卡不得宣稱已解決。

### 四、前提清單與實查證據（canonical §3.1，T2 以上義務）

| 前提 | 證據 | 狀態 |
|---|---|---|
| 契約鏈只有一個非測試呼叫端 | `parse_structured_block`→`review_cmd.py:209`／`review_invalid_reasons`→`:216`／`validate_review_report`→`:224`；`doctor.py` 對三者 0 命中 | ✅ 實查 |
| `item.body` 在寫入前可用 | `review_cmd.py` 已以 `card_body=item.body` 傳給 `check_checkpoint_gate` | ✅ 實查 |
| placeholder 只有一種寫法 | 197 張全值掃描，37 張逐字同串、無空值／`—`／`TBD` | ✅ 實查 |
| body 解析須切掉 Log | `card.py:758` 逐字（`parse_requested_by` 的既有陷阱） | ✅ 實查 |
| 基準 | `origin/main` = `d4ba7ce5f3fa526fc3a7aa0ebbeee3c926e5eb28`（fetch 後核對，local main 同值） | ✅ 實查 |
| **`render_verdict_comment` 的實際函式名與簽章** | ⛔ **未查**——只由事件輸出反推 | ⚠️ **標為未驗，⛔ 不設為硬前置** |
| **`ReviewReport` 是否有其他建構點** | 只查了 `validation.py:363`，⛔ 未窮舉 | ⚠️ **標為未驗** |

### 五、⚠️ 規劃期查出的治理問題：拆卡可能牴觸 canonical §3.2

§3.2 逐字：

> **開新卡僅限三情形**：(1) 需要不同能力域的執行者；(2) 紅線隔離（`schema`／`data-migration`）；
> (3) 可真平行（**寫入集不相交**）。三者皆不成立時，正解是**擴充現卡授權，不是開卡**。

`aiwf#136` 拆成 `#137`／`#138` 時：(1) 兩張都是主力型 ⇒ 不成立；(2) 兩張 `db_scope=none` ⇒ 不成立；
(3) ⚠️ **`#138` 宣告了 `cli/src/wf_cli/validation.py`，與 `#137` 相交** ⇒ 表面上也不成立。
⇒ ⛔ **表面上三者皆不成立，拆卡不合 §3.2。⚠️ 我在執行拆卡前沒有查這條。**

**⭐ 但它可修，而且修法是對的**：資源宣告的定義是**寫入集**（`dispatch-package.md` §1 逐字
「資源宣告（**寫入集**）」）。而 `#138` 對 `validation.py` 的需求是**呼叫** `validate_open_fields`
（`:88`），⛔ 不是修改它——研究第一輪已實測它「可對既有卡重跑」，無須改寫。

⇒ **建議：amend `#138`，把 `cli/src/wf_cli/validation.py` 移出資源宣告。**
之後兩張卡的寫入集為 `{AI_WORKFLOW.md, templates/*, review.py, validation.py, review_cmd.py, tests/test_review*.py}`
與 `{doctor.py, doctor_cmd.py, test_doctor.py}` ⇒ **不相交** ⇒ §3.2(3) 成立，拆卡合規，
且兩張**可真平行**（不再需要序列化，先前卡上寫的「S7a 先」隨之作廢，須一併更正）。

⚠️ 風險：若 S7b 執行中發現**必須**改 `validation.py`，依 §3.2 是「授權缺口」⇒
**停、寫阻塞發現、由需求方裁決**，⛔ 執行者不得自行擴權。這一條須寫進 `#138` 卡面。

### ⚠️ 本次規劃未驗

- **`render_verdict_comment` 的名稱與簽章**：⛔ 未讀。⚠️ 依 §3.1 標示且**不設為硬前置**——
  落點 G 的形狀可能要調整，但不影響 A–F 與 H–K。
- **`ReviewReport` 是否只有一個建構點**：⛔ 未窮舉。⚠️ 若有第二個，落點 B「不給預設值」的決定要重審。
- **`#138` 移除 `validation.py` 後是否真的不需要改它**：依研究第一輪的實測推論，
  ⛔ 未在 `doctor` 側寫過原型驗證。⚠️ 這是上面「風險」那段存在的原因。


## Comment 5404509503 · 2026-08-25T03:03:19Z

## 規劃補正（2026-08-25）：關掉兩個未驗項，其中一個改了落點

### 未驗項一 ⇒ 關閉，但**落點 G 原本寫少了一處**

`render_verdict_comment` 確實存在（`review.py:446`）。⛔ 但 `core_pain_resolved` 在該模組有**兩處**寫出：

| 位置 | 形式 | 消費者 |
|---|---|---|
| `review.py:485–486` | 散文行 `- core_pain_resolved：**yes**`（`no` 時追加「第一判準具否決權」） | 人讀 |
| `review.py:983` | **`wf_escalation_facts` 結構化區塊**內的 `core_pain_resolved: <值>` | **機器讀** |

⭐ 後者才是 `aiwf#138` 事後掃描的載體 ⇒ **新欄位必須兩處都寫**，⛔ 只寫散文行等於留痕上機器讀不到。
⇒ **落點 G 修正為 G1（`:485` 散文）＋ G2（`:983` facts 區塊，緊接 `core_pain_resolved` 那一行）。**

**且 ⛔ 不得升 `BLOCK_VERSION`**：讀回端 `review.py:1091` 逐字
`if str(data.get(FACTS_BLOCK_KEY)).strip() != BLOCK_VERSION: return None`
⇒ 一升版，**204 則既有事件全部變成讀不懂**。而不升版是安全的——讀回端全走
`data.get(<具名鍵>)`，⛔ 不拒未知鍵。⇒ 與 `aiwf#35` 的裁定一致（語意欄位進 payload、不需升版）。

⚠️ 反過來記一筆：`review.py:1096` 逐字「`unknown`／`unavailable` 這類擴充值一律視為讀不懂…
**不得以新值擴充既有布林 schema**」——那是對 `counts_toward_escalation` 說的。
⇒ 新增**新鍵**可以，⛔ 對**既有鍵**加值不行。本卡是前者。

### 未驗項二 ⇒ 關閉

`ReviewReport(` 全 repo 非測試建構點：**只有 `validation.py:363` 一個**。
⇒ 落點 B「兩個新欄不給預設值」的決定成立，⛔ 不會打到別的建構點。

### ⇒ 更新後的落點 G

| # | 落點 | 動作 |
|---|---|---|
| G1 | `review.py:485–486` | 散文行加 `- service_goal_still_served：**<值>**`；`no` 時追加「第二判準具否決權（需求方 2026-08-25 裁定）」 |
| G2 | `review.py:983` | facts 區塊在 `core_pain_resolved` 之後加 `service_goal_still_served: <值>`；`no`／`unsure` 時另加 `service_goal_gap: <_yaml_scalar(值)>`。⛔ **不升 `BLOCK_VERSION`** |
| G3 | 同區塊 | placeholder 命中時加 `service_goal_field_placeholder: true`，⇒ 讓 `aiwf#138` 掃得到「卡面缺陷」而非誤讀成查核者判不出來 |

### ⚠️ 本次補正新增的未驗

- **`service_goal_gap` 若含換行或連續空白，`_yaml_scalar` 會不會摺疊**：`aiwf#35` 的 R1 證據逐字
  記載 checkpoint payload 有此缺陷（「換行與連續空白被靜默摺疊，那是正規化不是逃逸」）。
  ⛔ 本次未驗 `_yaml_scalar` 對本卡的說明欄是否同樣摺疊。
  ⚠️ **這會影響交付正確性**（說明被摺疊等於部分遺失）⇒ 實作前必查，且須有往返測試。


## Comment 5404514819 · 2026-08-25T03:04:08Z

## 規劃補正之二：`_yaml_scalar` 的摺疊缺陷對本卡成立，且修法已被 `aiwf#35` 訂死

### 實測

`review.py` 的 `_yaml_scalar` 第一行處理逐字：

```python
text = " ".join(str(value).split())
```

無參數 `str.split()` 以**任意空白（含換行）**切分並丟掉空段 ⇒ 換行與連續空白被
**靜默摺疊成單一空格**。⚠️ 這正是 `aiwf#35` R1 證據逐字記載的那一格：
「換行與連續空白被靜默摺疊，**那是正規化不是逃逸**」。

⇒ `service_goal_gap` 是散文說明，⛔ 一旦查核者分行書寫，存進事件的值與他寫的**不逐字相同**。
⚠️ 而 `core_pain_resolved` 撞不到這個坑，因為它的值只有 `yes`／`no`。

### ⇒ 修法不是我選的，是 `aiwf#35` 已立的規則

該卡在 `templates/handoff-contract.md` 立下的規則二逐字：
**寫入端拒收**，且「**明文禁止以正規化代替拒收**」。

⇒ **落點 C 追加一段**：`service_goal_gap` 含換行時，在**契約層（提交面）直接拒收**，
⛔ 不摺疊、⛔ 不靜默通過。理由與位置：契約層在遠端呼叫之前（`review_cmd.py:206–224`），
是唯一能「拒收」而非「已寫壞才發現」的地方。

⇒ **拒收訊息（落點 E）追加一句**：說明須寫成**單行**，含換行會被拒——
⚠️ 這一句必須在**第一次**拒收時就出現（連同缺欄位那則一起），⛔ 不能等查核者踩到才說。

⇒ **驗證追加一項**：往返測試——寫得出的值，`_parse_yaml_subset` 讀得回且**逐字相同**；
語料須含真實使用過的說明文字。⭐ 這是 `aiwf#35` 規則三的機械形式，本卡照用，⛔ 不自創。

### ⚠️ 附帶記一筆（⛔ 不在本卡射程）

`_yaml_scalar` 的摺疊是**全域**的，本卡只在自己的新欄位上加寫入端拒收，
⛔ **沒有修掉其他使用者**（`attempt_id`、`owner_field_at_verdict_write`、`preflight_summary` 等）。
⚠️ `aiwf#35` R1 另附警告逐字：「含三反引號的值今天不破壞區塊**只是因為摺疊把它拉回同一行**，
修掉摺疊會讓這保護一起消失」⇒ **全域修它是有代價的動作，須另卡**。本卡不碰。


## Comment 5404548830 · 2026-08-25T03:09:20Z

## 研究交付（規劃期第八輪，2026-08-25）：⛔ 更正我上一則的斷言，並抓到本卡自己資源宣告的漏洞

### 一、⛔ 更正：`doctor` 讀得到卡，只是不在 `doctor.py`

我在上一輪推論時一度斷言「`doctor.py` 對 `list_items` 零命中 ⇒ doctor 讀不到卡」。
**錯的。** 路徑在 `doctor_cmd.py`：

- `:20` `from ..project import find_item_by_card_id, list_items, resolve_project`
- `:169–170` `proj = resolve_project(...)` ／ `snapshots = list_items(...)`
- `:221–222` 同上加 `find_item_by_card_id`

⇒ 分層是**`doctor.py` 純判定（不碰 gh）、`doctor_cmd.py` 做 I/O 並餵進去**。
⚠️ 我只 grep 了判定層就下結論，那是同一個形狀的錯誤（grep 範圍不等於系統範圍）。

### 二、⇒ 甲（`#138` 移除 `validation.py`）**驗證成立**，不再只是推論

`validate_open_fields`（`validation.py:88–119`）是**純函式**：keyword-only 七參數、
無 I/O、只 `raise ValidationError`。⇒ `doctor_cmd.py` 拿 `list_items` 回來的
`ItemSnapshot`（`project.py:112`，帶 `fields: dict`）就能直接餵它，
⛔ **不需要改 `validation.py` 一個字**。

⇒ `#138` 寫入集＝`{doctor.py, doctor_cmd.py, test_doctor.py}`。

### 三、⛔ 但本卡（`#137`）自己的資源宣告漏了 `cli/src/wf_cli/card.py`

規劃落點 **E** 要在 `card.py:743` 的 `parse_requested_by` 旁新增 `parse_service_goal(body)`
——**那是寫入**，而本卡現行資源宣告**沒有 `card.py`**。⚠️ 是我寫落點時漏掉的。

**兩個子選項：**

| | **E1（建議）** | E2 |
|---|---|---|
| 做法 | 在 `card.py` 加 `parse_service_goal(body)`，body 為權威 | 直接讀 `item.fields["服務的原始目標"]`，不動 `card.py` |
| 正確性 | ⭐ body 是權威、Project 欄位是導出（沿用簡介欄的既有裁定） | ⚠️ 驗的是**投影**不是權威；兩居所漂移時會誤判 |
| 寫入集 | 多一個 `card.py` | 不變 |
| 對 `#138` | ⭐ `#138` 也要讀服務的原始目標，可**呼叫**同一支（讀，不破壞不相交） | `#138` 各自讀 fields，兩邊各寫一份解析 |

⭐ **選 E1**：E2 會讓兩張卡各自寫一份「怎麼讀這個欄位」，而那正是既有紀律裡
「同一條判準只能有一份實作」的反面。

### 四、`card.py` 的互斥實查

宣告 `card.py` 的卡共 4 張：`WF-CLI-CARD-AMEND1`（🏁完成）、`WF-CARD-FIELD-CORRECTION1`（🏁完成）、
`WF-CARD-BRIEF-AND-TWO-AXIS-WRITE1`（🏁完成）、**`aiwf#105 WF-RESOURCE-HEADING-SUFFIX1`（📥Backlog／待指派）**。

⇒ **活卡交集 0 張**（`#105` 的 owner 是佔位，構造上不持鎖）。
⚠️ 但 `#105` 一旦被 assign 就會與本卡序列化。⚠️ 且 `#105` 至今 OPEN——
它正是「遷移卡標題帶後綴使 `amend` 對它們 0/33 全失敗」那張。⇒ **開工前須確認它沒被派出去。**

### ⇒ 對 §3.2 的最終答案

補上 `card.py` 之後：

- `#137` 寫入集：`{AI_WORKFLOW.md, templates/review-prompt.md, templates/review-escalation.md,
  review.py, validation.py, review_cmd.py, card.py, tests/test_review*.py}`
- `#138` 寫入集：`{doctor.py, doctor_cmd.py, test_doctor.py}`

⇒ **不相交** ⇒ §3.2(3)「可真平行」成立 ⇒ 拆卡合規。

### ⚠️ 但「可真平行」還有一個內容相依，⛔ 不是寫入集能表達的

`#138` 現行驗收第 5 條寫著「S7a 已合併時須把 `service_goal_still_served` 納入檢查面；
尚未合併時須明列為已知缺口」。⇒ 寫入集不相交，但**檢查面的內容取決於 `#137` 有沒有先到**。

⚠️ §3.2(3) 的字面只說「寫入集不相交」，⛔ 沒說內容相依。
⇒ 我判定拆卡合規是**依字面**；⭐ 若需求方認為「可真平行」該包含內容相依，
那 `#138` 就該等 `#137`，而先前卡上寫的「S7a 先」不作廢。**這一點請裁。**

### ⚠️ 本輪未驗

- **`#105` 是否會在本卡開工期間被派出**：⛔ 不可預測。⚠️ 處置是「開工前查一次」，
  ⛔ 不是現在能關掉的。
- **`ItemSnapshot.fields` 是否對全部 197 張卡都有齊那 7 個值**：⛔ 未查。
  ⚠️ 這**只影響 `#138`**（它要餵 `validate_open_fields`），不影響本卡。


## Comment 5404558339 · 2026-08-25T03:10:50Z

## 研究交付（規劃期第九輪，2026-08-25）：拿既有切片卡實測 §3.2(3)，⛔ 沒有反例

上一輪我把「可真平行是否包含內容相依」留給需求方裁。**本輪先去看這個專案實際上怎麼做的。**

### 母體：三組已知的切片兄弟卡（由共用「服務的原始目標」識別，見第一輪）

| 組 | 寫入集交集 | 關係 |
|---|---|---|
| `aiwf#124` ／ `#125` | **0**（`test_canonical_citation_scan.py` vs `docs/ROADMAP.md`） | 切片：一個實例 ／ 121 個宣稱的稽核 |
| `cpbl#144` ／ `#145` | **0**（兩張皆無資源宣告） | 序列：SMOKE1 → SMOKE2，assign 差 5 分鐘 |
| `cpbl#100` ／ `#147` | ⭐ **3 個**（`recap.py`、`test_recap_wp_contract.py`、`methodology-content.ts`） | **⚠️ 看似反例** |

### ⇒ `cpbl#100`／`#147` **不是**反例

`#147` 卡面 `spec 基線` 逐字：「**#100 WP-DISCLOSURE-SYNC1 的交付**（含四項 2026-08-15 裁定）」。

⇒ 它是**承接卡**（建立在前一張已交付的基線上），⛔ 不是同時進行的切片。
時序也吻合：`#100` assign 08-15 12:58、結案 08-18 19:45；`#147` 於 08-16 開卡、
**至今未 assign**（owner 仍 待指派）。⇒ 兩張從未同時持鎖。

⭐ **⇒ 承接與切片是兩種不同關係，canonical 用兩個不同機制表達：**
- **承接** → `spec 基線` 指向前卡交付（`baseline-cascade`）。寫入集**可以**相交，
  因為時序上不重疊，而 `assign` 的互斥閘門本來就會強制這一點。
- **切片** → §3.2 的三情形，其中 (3) 要求寫入集不相交。

⇒ `#137`／`#138` 是**切片**（同時從 `#136` 分出、無先後基線關係）⇒ 適用 (3) ⇒
補上 `card.py` 後兩者不相交 ⇒ **合規。⛔ 本輪找不到反例。**

⚠️ 覆蓋率誠實聲明：母體是**三組**，由「共用服務的原始目標」這一條線索識別
（第一輪：160 張真填目標的卡中僅 4 組共用，其一是本次拆卡）。
⛔ 不排除存在以其他方式構成的切片組而未被此線索抓到。

### ⇒ 內容相依那一題，本輪自己有答案了，⛔ 不必勞煩裁定

`#138` 驗收第 5 條現行寫法是：「S7a 已合併時納入檢查面；**尚未合併時須明列為已知缺口**」。
⇒ 那讓 `#138` **兩種情況都做得完** ⇒ 它對 `#137` **沒有硬相依** ⇒ 真的可以平行。

⭐ 判準因此清楚：**若一張卡非得等另一張交付才做得下去，正確的表達是 `spec 基線`
（像 `cpbl#147` 那樣），⛔ 不是靠資源鎖去排序。** `#138` 不需要那個宣告。

⇒ **建議維持甲，且順帶更正 `#138` 卡上「S7a 先」那句**——那句是我開卡時
依錯誤的資源交集寫的，移除 `validation.py` 後它不成立。

### ⚠️ 本輪未驗

- **`aiwf#125` 的執行期是否真的與 `#124` 重疊**：`#125` 的 Log **沒有 assign 行**
  ⇒ ⛔ 無法從留痕建立它的執行窗，我原本想拿它當「真平行過」的實證，**收回**。
  ⚠️ 不進推理鏈——本輪結論只依賴「`cpbl#100`／`#147` 是承接不是切片」，那有卡面逐字證據。
- **是否存在不共用服務目標的切片組**：⛔ 未查（缺識別線索）。⚠️ 影響的是覆蓋率宣稱，
  ⛔ 不影響「找到的三組裡沒有反例」這句。


## Comment 5404569405 · 2026-08-25T03:12:34Z

## 研究交付（規劃期第十輪，2026-08-25）：實跑解析器——查核者寫得出來，但 JSON 路徑有洞

⛔ 前面幾輪都是讀碼推論。**本輪實跑真的 `parse_structured_block`。**

### 一、YAML 路徑：七種真實散文形狀**全部逐字通過**

以查核者實際會寫的語氣構造，未經任何跳脫直接放進 `service_goal_gap:`：

| 樣本 | 結果 |
|---|---|
| 純中文散文 | ✅ 解析成功、逐字相同 |
| 含**全形冒號**「落差：交付只做了…」 | ✅ |
| 含**半形冒號**「落差: validation.py:258 只加了一半」 | ✅ |
| 含**檔名行號**「見 validation.py:258-270 與 review.py:983」 | ✅ |
| 含**引號**「查核者說「這不算…」」 | ✅ |
| 含**反引號** | ✅ |
| 含逗號、全形括號、`§`、`#` | ✅ |
| **多行** | ⛔ **已被既有解析器拒收**：「第 5 行不是可解析的頂層 `key: value`…（區塊內不得混入散文）」 |

⇒ ⭐ 查核者**不需要學任何跳脫規則**，寫散文就好。
⇒ ⭐ 而多行**本來就進不來** ⇒ 我在規劃補正二寫的「契約層加拒收」**在 YAML 路徑上是多餘的**。

### 二、⛔ 但 JSON 路徑會夾帶換行，而且**實測**會被靜默摺疊

`parse_structured_block` 同時吃 ```json。JSON 的 `"a\nb"` 是合法的單行值。實跑：

```
JSON 路徑解析：成功
  讀回逐字相同 = True  '第一行落差\n第二行補充\n\n第三段'
  經 _yaml_scalar 渲染後 = '"第一行落差 第二行補充 第三段"'
```

⇒ **換行與空行被靜默吃掉。** ⭐ 這是**執行結果，⛔ 不是我讀碼推論的**。

⇒ **規劃補正二的拒收仍然需要，但理由要改窄**：不是「散文會被摺疊」（YAML 路徑進不來），
而是「**JSON 路徑是唯一能把換行送進來的入口**」。⇒ 契約層（`validation.py`）對
`service_goal_gap` 含 `\n` 一律拒收，⛔ 不摺疊——依 `aiwf#35` 規則二「禁止以正規化代替拒收」。

⚠️ 我的探針自己有個 bug：往返驗證那段構造的區塊少了 `review_result`，⇒ 被
`extract_structured_block` 拒收而 traceback。**摺疊的結論不依賴那段**——
渲染輸出本身已經證明。

### 三、⚠️ 同一個洞今天就存在於三個既有欄位（⛔ 不在本卡射程）

走 `_yaml_scalar` 的自由文字欄：`accepted_reason`（`:1011`）、`rationale`（`:1263`）、
`preflight_summary`（`:993`）。⇒ 它們今天就承受同樣的摺疊。

⭐ 而 finding 的 `evidence` 與 `disposition` **不在** facts 區塊裡（`:1007–1017` 只寫
`finding_id`／`accepted`／`accepted_marked_by`／`accepted_reason`／`blocking`／
`root_cause_id`／`counting_eligible`）⇒ 那兩欄不受影響。

⚠️ 本卡只在自己的新欄位加寫入端拒收，⛔ 不修那三個——`aiwf#35` R1 已警告
「含三反引號的值今天不破壞區塊**只是因為摺疊把它拉回同一行**，修掉摺疊會讓這保護一起消失」
⇒ 全域修它是有代價的動作，須另卡。

### ⇒ 驗收與驗證的最終措辭調整

- 驗收（拒收訊息）：⛔ **不必**寫「說明須單行」給查核者——YAML 路徑他寫不出多行。
  改為只在**契約層**擋 JSON 路徑的 `\n`，訊息指名該路徑。
- 驗證追加：**兩條路徑各跑一次**——YAML 多行證明被解析器擋（附 stderr 原文）；
  JSON 帶 `\n` 證明被契約層擋（附 rc 與 stderr）。⛔ 只驗一條是零資訊。

### ⚠️ 本輪未驗

- **JSON 路徑實際被使用的比率**：⛔ 未查。⚠️ 不進推理鏈——它可達就要擋，
  與有沒有人用無關。
- **`\r`、` ` 等其他斷行字元**：⛔ 只測了 `\n`。⚠️ 實作時的拒收判準須涵蓋
  Python `str.splitlines()` 認得的全集，⛔ 不能只認 `\n`——那正是「只認一種變體」的同族。


## Comment 5404609166 · 2026-08-25T03:18:43Z

## 研究交付（規劃期第十一輪，2026-08-25）：⛔ 我前面三次資源盤點的數字是錯的（結論存活，數字不對）

### 我的 parser 錯在哪

Project 的「資源宣告」欄實際值形如：

```
db_scope=none；file:cli/src/wf_cli/doctor.py、file:cli/src/wf_cli/commands/doctor_cmd.py、file:cli/tests/test_doctor.py
```

我用 `value.split("、")` 再 filter `startswith("file:")`。⇒ **第一段是
`db_scope=none；file:cli/src/wf_cli/doctor.py`，不以 `file:` 開頭 ⇒ 被自己丟掉。**
⇒ **每一張卡的第一個資源都被我漏掉。**

改成直接抓全部 `file:` token（`re.findall(r'file:([^、；\s]+)')`）後：

| 我先前報的 | 實際 |
|---|---|
| `#137` 資源 8 個（漏 `AI_WORKFLOW.md`） | **9 個** |
| `#138` 資源 2 個（漏 `doctor.py`） | **3 個** |
| 宣告 `card.py` 的卡 **4 張** | **7 張**（多出 `WF-CLI-ROUTING-TIER1`、`WF-OPEN-INITIAL-STATUS1`、本卡，皆 🏁完成或本卡自己） |

### ⇒ 三個結論**全部存活**，但那是運氣，⛔ 不是方法對

1. `#137` ∩ `#138` = **空** ⇒ §3.2(3) 成立 ✅（修正後重算，仍空）
2. 與 `#137` 有交集的活卡（非終態、owner 非佔位）= **0** ✅
3. `card.py` 的活卡競爭者仍只有 `aiwf#105`（📥Backlog／待指派，構造上不持鎖） ✅

⚠️ 存活的原因是漏掉的那些恰好都是終態卡或本卡自己。⛔ **換一組資料就會給錯答案。**

### ⭐ 但 `wfcli` 的守衛**沒有**這個問題

`assign_cmd.py:179` `mine = parse_block(item.body)`、`:231` `other_decl = try_parse_block(other.body)`
⇒ 它讀的是**卡面 body 的 JSON 區塊**（`resources.py:51–52` 的 `resource-claims` 哨兵），
⛔ 不是 Project 的攤平字串。⇒ **這個 bug 只有我犯。**

### ⚠️ ⇒ 導出一條可重複踩的陷阱

Project 的「資源宣告」欄是一個**有損攤平**：它把 `db_scope` 與 `file:` 清單塞進同一個
以 `；`／`、` 混合分隔的字串，⛔ **而沒有任何程式讀它**（全 CLI 對該欄只寫不讀，
同 `effective_from` 的形狀）。

⇒ 它是人（與臨時腳本）最容易伸手拿的那一面，⛔ 卻不是權威。
⭐ **任何資源稽核都必須讀 body 的 JSON 區塊**，⛔ 不得讀 Project 欄位。
⚠️ 這一條建議寫進 `aiwf#138`——它的事後掃描如果從 Project 欄位讀資源宣告，
會複製我這個錯誤，而它的母體是**全部既有卡**（不是這次恰好安全的那幾張）。

### ⚠️ 本輪未驗

- **Project 欄位除了分隔符之外還漏不漏東西**（例如 `db:` 資源、含 `、` 的路徑）：⛔ 未查。
  ⚠️ 不進推理鏈——結論是「一律讀 body」，那與它還漏什麼無關。
- **是否還有其他「只寫不讀的攤平欄位」**：⛔ 未窮舉。⚠️ 已知兩個（資源宣告、`effective_from`），
  形狀相同 ⇒ 可能是通例而非個案，值得另卡查，⛔ 不在本卡射程。


## Comment 5404625955 · 2026-08-25T03:21:23Z

## T3 規劃閘門：需求方批註放行（2026-08-25）

本則由 PM 依需求方於本次 session 的口頭裁定「放行」逐字轉錄寫入，⚠️ 帳號為需求方本人的 token。

canonical §3.1 對 T3 要求「**核心痛點三問**非同步輕質詢：痛點是什麼／成功怎麼觀察／
最大的未驗證前提是什麼。**需求方批註放行後才進 `📥Backlog`**」。

三問已於[規劃交付](https://github.com/ruan6047/ai-workflow/issues/137#issuecomment-5404503895)第三節答覆：

- **痛點**：卡有兩個目標欄位，review 只查會漂移的那個（核心痛點，197 張中 16 張被 amend），
  不查構造上不會漂移的那個（服務的原始目標，開卡後無寫入通道）。
- **成功怎麼觀察**：四個可執行指令（缺欄位 rc≠0／`no`+APPROVE rc≠0／`unsure`+APPROVE rc=0／
  對 23 張 placeholder 卡實跑後事件中出現卡面缺陷另記），⛔ 非主觀判斷。
- **最大的未驗證前提**：新欄位會被認真填。⛔ 機械上只保證得了「有填、值合法、說明非空」，
  ⚠️ 保證不了填的是真話 ⇒ 觀測要等 `aiwf#138` 的事後掃描產生第一批分佈。

**⇒ 放行，進 `📥Backlog`。**

⚠️ 開工前須再查一次 `aiwf#105 WF-RESOURCE-HEADING-SUFFIX1`（📥Backlog／待指派）
是否已被派出——它同樣宣告 `cli/src/wf_cli/card.py`，一旦認領即與本卡序列化。


## Comment 5438029151 · 2026-08-27T11:00:30Z

## 需求方裁定：本卡轉 📥Backlog，射程併入 `aiwf#66`

**轉錄來源**：需求方 ruan6047 於 Claude Code 對話中的兩段回覆，逐字為 —— 「**ＯＫ但66這張卡是不是有點舊**」與（PM 提出甲乙兩案後）「**甲**」。
本則留言由 PM（Claude Opus 5@Claude Code）以需求方 token 代為張貼，⛔ 內容為逐字轉錄，⛔ 非 PM 自行決定。

PM 提出的兩案逐字為：

- 甲：先在 `#66` 卡上登記兩處前提失效，然後再把 `#137` 的問句登記為它的必含欄位
- 乙：`#137` 單純轉 Backlog，⛔ 不提 `#66`，等 `#66` 自己被重新規劃時再說

### 裁定內容

**採甲案。** 本卡轉 **📥Backlog、⛔ 不排程**；「查核者須回答服務的原始目標是否仍被服務」這一句，已登記為 `aiwf#66 WF-DISPATCH-FROM-HANDOFF1` 骨架的必含問句（`amend` op `b932354c`），並同時在該卡登記其兩處前提失效。

### 依據（三輪研究，⛔ 逐條可重跑；PM 已獨立複驗其中五處）

**(1) ⭐ 問題今天沒有被交到查核者手上。** `templates/review-prompt.md`／`AGENTS.md`／`CLAUDE.md` 對「服務的原始目標」`grep -c` **皆為 0**。canonical §5.1.1 定義了它，末句逐字「⚠️ ⛔ **本節只定義，實作屬子卡。**」

**(2) 24 則裁決 0 則套用。** `d4ba7ce5` 之後帶 marker 的裁決 **24 則／11 張卡**；以五個關鍵字掃全文 **23 則零命中**，唯一命中者非在套用該判準。那 11 張卡的目標欄**全部實填**（⛔ 無 placeholder）⇒ **都有真東西可對照而無人對照**。

**(3) ⛔ 改範本無效 —— 這推翻了研究第二輪自己的建議。** 95 份派審詞（30 張卡，`2026-08-10` → `2026-08-21`）對 `templates/review-prompt.md` 的逐字重疊率 **全部 0.0000**；§2 第一判準的強判準轉抄率 **0/95**。⇒ §2 已在範本裡兩週半、轉抄 0 次，那就是「改範本」的前導實驗，結果是否定的。⭐ 而 `aiwf#38` 的簡介**兩個月前已逐字裁定過同一件事**：「⛔ 不得把規則寫進 `templates/dispatch-package.md`（該檔只送被約束者本人、從不進 Issue 留痕）」。

**(4) ⛔ 不做 schema 必填欄位 —— 今天沒有消費者。** 三個 facts 讀取端（`escalation_facts_from_body`／`audit_conformance`／`audit_review_channel`）**皆無自動執行路徑**：`ai-workflow/.github/workflows/ci.yml` 全文三步（`uv lock --check`／`uv run --frozen pytest -q`／`scripts/replay_escalation_rules.py`），⛔ 零處呼叫 `wfcli doctor`、零處讀任何真實 Issue；`cpbl-analytics` 的 ci.yml 對 `wfcli|doctor|escalation|review` 零命中；兩 repo 非樣本 git hooks 0 個。且 `WF-POSTHOC-CONFORMANCE1` 已 🏁完成而其 `audit_conformance` ⛔ 不讀留言。⚠️ **說準一點**：收據不是沒有讀者——`escalation_facts_from_body` 被 `review_cmd.run()` 的 checkpoint 閘門在**下一次寫入路徑上**同步讀；真正的問題是**新欄位沒有任何閘門會消費它**。

**(5) ⛔ 不做 `no × APPROVE` 否決權。** `aiwf#57` 的 `issuecomment-5305745859` 是一則真實的 `core_pain_resolved: no` ＋ `review_result: APPROVE`（作者 `GPT-5.6@Codex`，帶 `merge_recommendation: approve_after_update_branch`，⛔ 無 `wf-review-event` marker，走的是 `wf-review-receipt:v1`）⇒ **唯一一次有人真的想要它，機械否決沒擋住——他改用自由文字繞過去了。** 且硬拒零寫入 ⇒ **正確運作時構造上不可觀測；只有在誤擋時才會被看見。**

**(6) ⭐⭐ 這個傷害既有機制已經抓到過，而且就抓在本卡的母卡上。** `root_cause_id` 全史 586 次／282 個相異值中有 `service-goal-misaligned-with-delivery-scope`，**2 個相異 finding（R1-001 與 R2-001）都在 `aiwf#130`**，皆 `severity=critical`／`blocking=true`／`class=governance`／`attribution=planner`。⇒ **用第一判準 ＋ 一個 governance 類自由文字 finding 就達到過，⛔ 不需要專用欄位。** ⇒ 真實形狀是「**該判準不被例行執行**」，⛔ 不是「不可執行」。

### ⛔ 不作廢的部分

三輪研究的量測全部保留，卡面 13 條驗收與 6 條驗證一字不刪。⭐ 特別是**卡面 13 條要更正的清單**（含 8 個失準的行號引用、`383` 是 finding 數不是事件數、`|`／`|-` 區塊純量使「唯一入口是 JSON」為假、`aiwf#138` 從未接受該指派、驗收 10(b) 已被 `38870fa` 做掉）——重新排程時可直接複驗，⛔ 不需重做。

### 重新排程的訊號（⛔ 條件，不是日期）

1. `aiwf#66` 落地後 **20 則以上**由骨架產生的派審詞中，含該問句者 **< 0.80** ⇒ 通道論被推翻，回頭考慮 schema 必填。
2. 出現 **≥1 則**「`APPROVE` 且事後證明原始目標未被服務、且查核者**未以任何 finding 通道表達**」的實例 ⇒ 本卡（去否決權版）立即排程。
3. 任何人為 `service_goal_still_served` 建立**自動執行的消費者**（CI／hook／排程）⇒ (4) 的降級解除。

⛔ 三個門檻皆於 2026-08-27 釘死，⛔ 不得事後訂。

### ⚠️ 誠實邊界

- **「11 個決定裡有幾個被實際損害」判不出來**，上界 10（＝APPROVE 則數）。⇒ 只證了傷害**存在**，⛔ 未證**幅度**。
- 上述派審詞量測為**關鍵字法**（三層搜過），⛔ 若今日派審詞改用完全不同措辭且無結構標記則量不到。
- 研究者自陳三項「**驗得了但沒做**」：`root_cause_id` 282 個相異值只逐一看了命中的 10 次；守衛命中只抽了 30/400+；`發現：` 格內容真假**構造上不可量測**（全文從不落任何遠端面）。


## Comment 5460928840 · 2026-08-29T06:55:58Z

## 阻塞登記

**狀態**：⏸阻塞。**來源狀態：📥Backlog**（解除時回到此狀態）。

**阻塞原因**：需求方於 2026-08-29 決定，在階段狀態重整（8 階段 × 10 狀態、待審清單、CLI 射程收斂）定案並落地前，暫停所有 ai-workflow 流程卡，避免它們與重構討論互相干擾。

**可證偽的解除條件**：待審清單機制上線（label ＋ issue template ＋ 可見分組）。屆時本卡改列為清單參考項，或依當時前提是否仍成立重新排程。

**本次未做**：核心痛點、驗收條件、射程一律未動。`iteration` 未遞增。`階段` 欄未寫入。本登記僅改交付狀態與 owner。

**已知的射程重疊**（供解除時參考，非本次裁定）：#66／#38 的實質可能由「七份交接文件格式」承接；#128 可能由「待審清單收件條件三·查重留痕」＋`open --from-issue` 承接；#11 的證據紀律已部分寫入 PM 準則但痛點（靠人記得）未消失。⛔ 上述皆未經裁定，解除時須逐張重驗。

**裁定者**：需求方 ruan6047，2026-08-29 本 session 對話中指示「把目前所有 WF 卡片暫停，避免干擾目前重構討論」。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

