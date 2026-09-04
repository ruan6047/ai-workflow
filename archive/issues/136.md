# #136 WF-REVIEW-SERVICE-GOAL-AND-CONFORMANCE1 review schema 增 service_goal_still_served ＋ doctor 事後重驗既有卡（aiwf#130 子卡 S7）
- state: open  created: 2026-08-24T18:59:14Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/136
- comments: 11

## Body

- 需求：—　規劃：—
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；動 review 的結構化輸出契約與 doctor 的掃描面；schema 改動會影響所有後續查核事件的解析，且既有事件不得因新欄位而失效。）　查核：待指派（建議 高階型；本卡改的是查核自身的契約，⛔ 執行者無法自證；且須驗證新欄位對既有 review 事件為向後相容。）
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：目標 2 可稽核的內容：卡是否仍服務其原始目標、是否仍合乎現行規範，必須是查核留痕上讀得出來的答案，而不是靠查核者當下想不想得到。

## 簡介
<!-- card-brief:begin -->
做什麼：把 canonical §5.1.1／§5.1.2 的兩個查核判準從條文變成 review schema 的必填欄位與 doctor 的事後檢查。適用時機：要判斷「一張卡還值不值得做」或「卡開完之後 canonical 改版了、它還合規嗎」時，先看這張卡有沒有落地。⛔ 非射程：不改 core_pain_resolved 的否決權語意；不回填既有卡的簡介（屬 S5）；不切換狀態語彙（屬 S2／S3）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：canonical §5.1.1 與 §5.1.2 定義的兩個查核判準在 main 生效（d4ba7ce5）而**兩者都沒有實作**：實測 templates/review-prompt.md 與 templates/review-escalation.md 含 service_goal_still_served 皆 0 命中，doctor 亦無事後重驗既有卡的通用路徑。⇒ 卡有兩個目標欄位而現行只查一個——核心痛點由 core_pain_resolved 檢查且具否決權；服務的原始目標在 review 的實作中零命中，只被寫、被存、被顯示，⛔ 從未被拿來對照交付。⭐ 而該不對稱有量化支持（本卡開卡前實測，補上 §5.1.1 自標的未驗項）：195 張卡中「服務的原始目標」被 amend 過 0 張，「核心痛點」15 張 ⇒ 現行查的是會漂移的那個欄位，不查不會漂移的那個。實證見 cpbl#166：兩欄分別是「cpbl main 沒有 required status check」與「測試要在碼進 main 之前跑」，原始目標在 ruleset 上線那一刻即達成，而後續十輪查的是被 amend 修改過的核心痛點。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:templates/review-prompt.md",
    "file:templates/review-escalation.md",
    "file:cli/src/wf_cli/review.py",
    "file:cli/src/wf_cli/doctor.py",
    "file:cli/src/wf_cli/commands/doctor_cmd.py",
    "file:cli/tests/test_review_service_goal.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] review 的結構化輸出新增 service_goal_still_served，值域**恰為** yes／no／unsure（canonical §5.1.1 逐字），與 core_pain_resolved 並列。⛔ 不改後者的否決權語意——§5.1.1 只說「並列」，未賦予新欄位否決權；賦不賦由本卡 Discovery 提案、需求方裁定。
- [ ] 填 no 或 unsure 時**須說明交付與原始目標的落差**（canonical §5.1.1 逐字），且該說明為機械必填（空字串即拒）。
- [ ] ⛔ **向後相容**：既有 review 事件沒有該欄位，⛔ 不得因新欄位而解析失敗或被判 review-invalid。⚠️ 須以真實既有事件實測——本 repo 已累積 383 筆 finding、42 張卡有 review 事件。
- [ ] templates/review-prompt.md §5 的 YAML 區塊同步新增該欄位並說明填法；templates/review-escalation.md §2 的 finding schema 同步。
- [ ] doctor 新增**通用**的事後重驗：對既有卡重跑現行的欄位與格式檢查並列出不合規者。⛔ 不自動修復（沿用 cleanup 的既有立場：守衛不代為修復非法態）。
- [ ] ⚠️ doctor 的事後重驗須**與既有的 legacy_authority_notes 合流或明確劃界**——canonical §5.1.2 逐字指出後者「證明該需求已出現過一次，但當時針對單一形態單獨做，不是通用機制」。⛔ 再做一個單一形態的掃描等於重犯。
- [ ] ⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。⚠️ 須以至少 3 張真實既有卡實測（含一張 2026-08-04 遷移卡——實測 61 張活卡中 24 張的 body 結構與範本不同）。
- [ ] ⭐ 補上 §5.1.1 自標的未驗項並寫進條文或卡面：本卡開卡前實測 195 張卡中「服務的原始目標」被 amend **0 張**、「核心痛點」**15 張** ⇒ 該不對稱有量化支持。⚠️ 若日後有人 amend 前者，該支持即失效，須有機制發現。
- [ ] 回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）；replay_escalation_rules 與 canonical_citation_scan 維持綠。
- [ ] ⚠️ 交付時須附「PM 單方面決定清冊」，逐一標明哪些形狀或判準由執行者提出而非 canonical 明文或需求方裁定。

## 驗證

- [ ] 值域封閉性：以 yes／no／unsure 之外的值各跑一次，附 rc 與 stderr 原文，證明皆被拒。⛔ 只驗合法值會過是零資訊。
- [ ] ⛔ 向後相容的**變異檢驗**：取至少 3 筆**真實既有** review 事件（無該欄位）跑解析，證明不失敗；再刻意移除相容處理，證明它會轉紅。⚠️ 只跑前半是零資訊。
- [ ] 說明必填的負控：填 no 但說明為空、填 unsure 但說明為空，各跑一次證明被拒。
- [ ] doctor 事後重驗：對至少 3 張真實既有卡（含一張 2026-08-04 遷移卡）實跑，附原始輸出；並證明它**不阻擋** amend／handoff（⛔ 若無 dry 路徑，明列原因與密封探針設計——⚠️ 注意 amend **有** --dry-run，handoff 沒有）。
- [ ] ⚠️ 與 legacy_authority_notes 的關係須以碼證明（指出合流點或劃界處的檔與行），⛔ 不接受「我劃了界」的自述。
- [ ] ⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因（缺什麼、要等什麼、需要誰）；⛔ 標不出原因者代表驗得了、不得列入。

## Log

- 2026-08-25T02:59:13+08:00 open by —；owner 待指派；iteration 0。
- 2026-08-25T03:01:51+08:00 amend by wf-cli（op a78e33c0）→ 驗收條件：原值「[ ] TODO：填入可獨立驗證的條件」→ 新值「review 的結構化輸出新增 service_goal_still_served，值域**恰為** yes／no／unsure（canonical §5.1.1 逐字），與 core_pain_resolved 並列。⛔ 不改後者的否決權語意——§5.1.1 只說「並列」，未賦予新欄位否決權；賦不賦由本卡 Discovery 提案、需求方裁定。；填 no 或 unsure 時**須說明交付與原始目標的落差**（canonical §5.1.1 逐字），且該說明為機械必填（空字串即拒）。；⛔ **向後相容**：既有 review 事件沒有該欄位，⛔ 不得因新欄位而解析失敗或被判 review-invalid。⚠️ 須以真實既有事件實測——本 repo 已累積 383 筆 finding、42 張卡有 review 事件。；templates/review-prompt.md §5 的 YAML 區塊同步新增該欄位並說明填法；templates/review-escalation.md §2 的 finding schema 同步。；doctor 新增**通用**的事後重驗：對既有卡重跑現行的欄位與格式檢查並列出不合規者。⛔ 不自動修復（沿用 cleanup 的既有立場：守衛不代為修復非法態）。；⚠️ doctor 的事後重驗須**與既有的 legacy_authority_notes 合流或明確劃界**——canonical §5.1.2 逐字指出後者「證明該需求已出現過一次，但當時針對單一形態單獨做，不是通用機制」。⛔ 再做一個單一形態的掃描等於重犯。；⛔ 事後重驗**非阻擋**：列出不合規者，⛔ 不得讓既有卡因 canonical 改版而無法 amend 或 handoff。⚠️ 須以至少 3 張真實既有卡實測（含一張 2026-08-04 遷移卡——實測 61 張活卡中 24 張的 body 結構與範本不同）。；⭐ 補上 §5.1.1 自標的未驗項並寫進條文或卡面：本卡開卡前實測 195 張卡中「服務的原始目標」被 amend **0 張**、「核心痛點」**15 張** ⇒ 該不對稱有量化支持。⚠️ 若日後有人 amend 前者，該支持即失效，須有機制發現。；回歸：cli 既有測試全過（交付時的基線數須逐字記錄，⛔ 不得只寫「全過」）；replay_escalation_rules 與 canonical_citation_scan 維持綠。；⚠️ 交付時須附「PM 單方面決定清冊」，逐一標明哪些形狀或判準由執行者提出而非 canonical 明文或需求方裁定。」；理由 開卡時一併填實驗收與驗證，⛔ 不留 TODO——依 canonical §6.4.1（驗收條件須於離開規劃前填實）。驗收第 8 條已把 §5.1.1 自標的未驗項補成實測值（195 張卡：服務的原始目標 amend 0 張 vs 核心痛點 15 張）。。
- 2026-08-25T03:01:51+08:00 amend by wf-cli（op a78e33c0）→ 驗證：原值「[ ] TODO：填入驗證指令與證據要求」→ 新值「值域封閉性：以 yes／no／unsure 之外的值各跑一次，附 rc 與 stderr 原文，證明皆被拒。⛔ 只驗合法值會過是零資訊。；⛔ 向後相容的**變異檢驗**：取至少 3 筆**真實既有** review 事件（無該欄位）跑解析，證明不失敗；再刻意移除相容處理，證明它會轉紅。⚠️ 只跑前半是零資訊。；說明必填的負控：填 no 但說明為空、填 unsure 但說明為空，各跑一次證明被拒。；doctor 事後重驗：對至少 3 張真實既有卡（含一張 2026-08-04 遷移卡）實跑，附原始輸出；並證明它**不阻擋** amend／handoff（⛔ 若無 dry 路徑，明列原因與密封探針設計——⚠️ 注意 amend **有** --dry-run，handoff 沒有）。；⚠️ 與 legacy_authority_notes 的關係須以碼證明（指出合流點或劃界處的檔與行），⛔ 不接受「我劃了界」的自述。；⚠️ 未驗清單依 canonical §6.4.2：每項標明驗不了的原因（缺什麼、要等什麼、需要誰）；⛔ 標不出原因者代表驗得了、不得列入。」；理由 開卡時一併填實驗收與驗證，⛔ 不留 TODO——依 canonical §6.4.1（驗收條件須於離開規劃前填實）。驗收第 8 條已把 §5.1.1 自標的未驗項補成實測值（195 張卡：服務的原始目標 amend 0 張 vs 核心痛點 15 張）。。
- 2026-08-25T03:09:09+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree ai/opus-5/WF-REVIEW-SERVICE-GOAL-AND-CONFORMANCE1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/review-service-goal1；交付狀態 🔬研究中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-25T03:18:43+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (PM)；iteration 0；SHA d4ba7ce5f3fa526fc3a7aa0ebbeee3c926e5eb28；證據 研究三輪交付完成：issuecomment-5400086603（否決權：107 張卡的配對量測，no×APPROVE 僅 1 筆且該筆繞過 wfcli review）、issuecomment-5400106397（合流：validate_open_fields 可對既有卡重跑，實測 161 張中 7 張不合規、全為 2026-08-04 遷移卡）、issuecomment-5400122894（向後相容：新欄位設必填即使 383 筆既有事件全部 review-invalid，須比照 TRAILER_GUARD_EPOCH 的日期分流）。進規劃定三個設計題。。
- 2026-08-25T10:25:28+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (PM)；iteration 0；SHA d4ba7ce5f3fa526fc3a7aa0ebbeee3c926e5eb28；證據 需求方 2026-08-25 裁定拆卡。本卡射程同時涵蓋 canonical §5.1.1（review schema）與 §5.1.2（doctor 事後重驗），已依裁定拆為 aiwf#137（S7a，WF-REVIEW-SERVICE-GOAL1）與 aiwf#138（S7b，WF-POSTHOC-CONFORMANCE1）。⛔ 不以 amend 就地縮小射程的機械理由：查核第一判準逐字比對「卡面痛點原文」（templates/review-prompt.md §2），且 core_pain_resolved=no 配 APPROVE 由 validation.py:268 硬拒 ⇒ 縮小射程而不改痛點原文，本卡構造上無法通過查核；而 amend --core-pain 須併 --ruling-url，其 GitHub comment author 須逐字等於卡面「需求：」欄，本卡該欄為「—」（card.py:775 拒絕以自述成立）⇒ 痛點原文在機械上改不了。⇒ 停本卡、由兩張新卡承接。研究留痕（十一輪）保留在本卡 comments，兩張新卡的痛點與驗收已引用其量測：issuecomment-5400086603（否決權配對量測）、issuecomment-5400106397（161 張中 7 張不合規）、issuecomment-5400122894（383 筆既有事件的向後相容分流）、issuecomment-5404142574（拒收訊息路徑）、issuecomment-5404179008（更正＋派審詞不留痕）。⚠️ 兩張新卡的「需求：」欄已填 ruan6047，⇒ 日後痛點更正不再被同一個機械理由卡死。。


## Comment 5399940219 · 2026-08-24T19:00:54Z

## ⚠️ 開卡當下即發現一個 aiwf#134 的缺陷（本卡是第一張有簡介的卡）

`wfcli open` 建立本卡時印出：

```
[open] 警示：剛建立的 item 在讀回時找不到，簡介欄位無法驗證。
⛔ 不視為成功——請以 `wfcli doctor` 確認雙居所是否一致。
```

**查證結果：是 GitHub 的傳播延遲，⛔ 不是雙居所漂移。**

- `gh issue view 136` 的 body：`card-brief:begin` 哨兵 **1 個** ✅
- 以 item id 直接 GraphQL 查：`簡介` 欄位**有值**且與 body 一致 ✅
- 數十秒後重跑 `gh project item-list`：`#136` **在列表裡**（191 個 item）✅

⇒ `aiwf#134` 的 `_verify_brief_field` 走 `list_items` 讀回，而**剛建立的 item 不會立刻
出現在 `project item-list` 的結果裡** ⇒ **每一張帶 `--brief` 的新卡都會誤報一次警示**。

### ⛔ 這是真缺陷，不是誤解

⚠️ 該警示的文案逐字寫「**⛔ 不視為成功**」——⇒ 它把一個**必然發生**的正常情形報成需要
人工處置的異常。⭐ 那正是 `aiwf#134` 自己在別處防的形狀：**構造上必然發生的告警＝零資訊**，
而它會訓練讀者忽略該行。

### 修法（⛔ 不在本卡射程，記於此）

`_verify_brief_field` 應對「item 讀不到」**重試數次再放棄**，或改以 item id 直接
GraphQL 查詢（本次查證用的就是那條路，⭐ 它立刻讀得到）。⚠️ 後者更對——
`list_items` 是全表掃描，而我們只要一個 item。

⚠️ **本卡的射程是 review schema 與 doctor 事後檢查**，⛔ 不含 `open` 的讀回路徑。
⇒ 交需求方裁定：另開卡、併入既有卡，或先記著。


## Comment 5400086603 · 2026-08-24T19:14:23Z

## 研究交付（第一輪，2026-08-25）：新欄位要不要有否決權

### 問題

canonical §5.1.1 逐字「review schema 增 `service_goal_still_served`（`yes` / `no` / `unsure`），
與 `core_pain_resolved` **並列**」。⛔ **「並列」沒有說它有沒有否決權**——本卡驗收第 1 條
已把該裁定標為 Discovery 提案、需求方裁定。

### 量測：第一判準的否決權在實務上成立嗎

掃兩 repo 全部卡的查核事件（**107 張卡有查核事件**），配對 `core_pain_resolved` 與
`review_result`：

| 配對 | 次數 |
|---|---|
| `no` × `REQUEST_CHANGES` | **70** |
| `no` × `APPROVE` | ⛔ **1** |
| `yes` × `APPROVE` | 72 |
| `yes` × `REQUEST_CHANGES` | 50 |

⇒ 否決權 **70/71 成立**，而那**唯一一筆例外**查得出來。

### ⭐ 唯一的例外是 `aiwf#57` R5，而它已經被立過案

`aiwf#57` 的 R5 裁決：`core_pain_resolved: no` ＋ `review_result: APPROVE`，
並多帶一個**非標準欄位** `merge_recommendation: approve_after_update_branch`。

⇒ 那正是 `aiwf#95 WF-REVIEW-MERGE-SUITABILITY1`「查核 schema 無法表達**建議合併但不驗收**，
該類意見因此記不進帳」立案的實例。其核心痛點逐字：

> `core_pain_resolved` 是第一判準且具否決權，**`validation.py:268-272` 硬擋**
> `core_pain_resolved=no` 併 `review_result=APPROVE`。**這條規則本身是對的**——查核講的是驗收。
> 但實務上存在另一類問題：「這個分支該不該合併」

**實測該硬擋仍在**（`validation.py:268-272`，逐字
「`core_pain_resolved=no` 時 `review_result` 只能是 `REQUEST_CHANGES`」）
⇒ ⭐ 那筆例外是**繞過 schema 寫進自由欄位**產生的，⛔ 不是硬擋失效。

⚠️ **而 `aiwf#95` 是 `🛑已停止`**（2026-08-18），其提議的欄位 grep **零命中**
⇒ 該表達缺口**至今未被填補**。

### ⇒ 對本卡的三個結論

**一、`service_goal_still_served` ⛔ 不應有否決權（提案，待需求方裁定）。**
依據：第一判準的否決權**已被硬擋機械執行**且 70/71 成立；再加一個具否決權的欄位，
唯一的效果是**多一條讓查核者繞去自由欄位的理由**——`aiwf#57` R5 就是這麼發生的。
⭐ 兩個否決權欄位並存時，「兩者衝突怎麼辦」是新的未定義狀態，⛔ canonical 沒說。

**二、⭐ 它的價值在「被迫回答」而非「能否決」。** §5.1.1 的實證是 `cpbl#166`——
原始目標在 ruleset 上線那刻即達成，而十輪查的是會漂移的核心痛點。⇒ 缺的是**有人問**，
⛔ 不是缺一票否決。

**三、⚠️ 但這使 `aiwf#95` 的缺口更該一併處理。** 若本卡加一個「無否決權的必答欄位」，
它與 `#95` 想要的「建議合併但不驗收」是**同一種東西**：**不進否決鏈的意見軸**。
⛔ 本卡不逕行併入（`#95` 已停止，重啟屬需求方裁定），但設計時須留下相容形狀。

### ⚠️ 本輪未驗（依 canonical §6.4.2 標明原因）

- **正規表示式抽取的漏報率**：配對是以 regex 從留言全文抽取，⛔ 未逐則人工核對。
  驗不了的原因：107 張卡的查核留言全文人工讀完成本過高；⭐ 但**方向不受影響**——
  漏報只會讓 `no × APPROVE` 更少，不會製造出更多例外。
- **`unsure` 的語意**：canonical 只給值域、⛔ 沒定義它與 `no` 在流程上的差別。
  驗不了的原因：無先例可查（該值域尚未存在），須由本卡 Design 提案、需求方裁定。


## Comment 5400106397 · 2026-08-24T19:16:11Z

## 研究交付（第二輪，2026-08-25）：事後重驗與 `legacy_authority_notes` 該合流還是劃界

### 兩者的形狀比對

| | `legacy_authority_notes`（既有） | §5.1.2 要的事後重驗 |
|---|---|---|
| 輸入 | 卡面字串 | 卡面字串 |
| 判準 | ⛔ **單一字面**（`LEGACY_AUTHORITY_NOTE_MARKER = "非留言內文自述"`，錨點 `_AUTHORITY_FIELD_ANCHOR = "；授權 "`）| **現行的欄位與格式檢查全套** |
| 產出 | `not_scanned` / findings | 同 |
| 是否阻擋 | ⛔ 否，唯讀 | ⛔ 否（§5.1.2 逐字「不自動修復」）|

⇒ **輸入、產出、非阻擋三者相同；差別只在判準的來源**——一個是寫死的字面，
另一個是「現行檢查」這個會隨 canonical 改版而變的集合。

### ⭐ 可行性實測：`validate_open_fields` 可以直接對既有卡重跑

`validation.py:88` 的 `validate_open_fields` 是**純函式、吃具名參數**（`card_id`／`feature`／
`tier`／`core_pain`／`service_goal`／`db_scope`／`resources`），⛔ 不碰網路、不依賴 open 的上下文
⇒ 只要能從既有卡面抽出那幾欄就能重跑。**實跑兩 repo 全部卡**：

```
可解析資源宣告的卡：161   （無法解析 35 張 ← 那是 aiwf#105 的射程，⛔ 非本卡）
  ✅ 通過現行檢查：154
  ⛔ 不合規：7   全部同一個原因：「核心痛點 必填」
     cpbl#83、#80、#79、#78、#58、#55、（第 7 張）
```

⭐ **這 7 張正是 2026-08-04 遷移卡的子集**——它們沒有 `## 核心痛點` 章節，
與 `aiwf#134` 的 V5 抓到的 24/61 同一個母體。⇒ **事後重驗一上線就會報出真東西，
⛔ 不是零命中的裝飾。**

### ⇒ 結論：**合流，⛔ 不劃界**

**一、判準來源改為「呼叫現行的 validate_* 函式」，⛔ 不再寫死字面。**
`legacy_authority_notes` 成為該框架下的**一個檢查項**，而非平行的第二個掃描器。
⭐ 依據：canonical §5.1.2 逐字「它證明『事後掃描既有卡的過期形態』這個需求**已經出現過
一次**，但當時針對單一形態單獨做，**不是通用機制**」——⇒ 條文自己說了那是要被通用化的東西。

**二、⛔ 再做一個單一形態的掃描等於重犯**（本卡驗收第 6 條已釘住這一點）。

**三、⚠️ 但合流有一個代價要先講**：`validate_open_fields` 的錯誤訊息是為**開卡當下**寫的
（「核心痛點 **必填**」）。對既有卡重跑時，該訊息會讓人以為那張卡開得不合法——
⛔ 實際上它開卡時是合法的，是**後來 canonical 變了**。⇒ 事後重驗的輸出必須區分
「開卡時就違規」與「開卡後規範改變」，⚠️ 而**現行的檢查函式無法提供那個資訊**
（它不知道規則何時生效）。

### ⚠️ 本輪未驗（依 canonical §6.4.2 標明原因）

- **那 7 張的第 7 張卡號**：⛔ 我的輸出只印了前 6 個。驗不了的原因：無——
  ⭐ **這是我沒印完，不是查不到**，執行階段補印即可。⚠️ 逐字記下以免被讀成「不可知」。
- **「開卡時就違規」vs「開卡後規範改變」如何區分**：⛔ 現行檢查函式不帶生效時點。
  驗不了的原因：需要一個規則生效時點的來源，而本 repo 只有 `TRAILER_GUARD_EPOCH`
  一個先例（committer date 分流）⇒ 是否比照屬 Design 提案，需求方裁定。
- **35 張無法解析資源宣告的卡**：屬 `aiwf#105`（OPEN）射程，⛔ 本卡不處理。
  ⚠️ 但事後重驗對它們會**整批失敗** ⇒ 兩卡的交付順序會互相影響，須留痕。


## Comment 5400122894 · 2026-08-24T19:17:44Z

## 研究交付（第三輪，2026-08-25）：新欄位對既有 review 事件的向後相容

### 實測四種情形（`validate_review_report` 純函式，⛔ 零 GitHub）

| | 輸入 | 結果 |
|---|---|---|
| **A** | 既有形狀（無新欄位） | ✅ 過 |
| **B** | 帶 `service_goal_still_served`（模擬未來 schema） | ✅ 過 ⇒ ⛔ **未知鍵被忽略、非封閉集合** |
| **C** | 帶 `merge_recommendation`（`aiwf#57` R5 用的那個非標準欄位） | ✅ 過 |
| **D** | 若新欄位設**必填** | ⛔ **既有事件全部 `review-invalid`** |

### ⭐ C 直接解釋了第一輪的那筆例外

第一輪查到唯一違反否決權的 `aiwf#57` R5（`core_pain_resolved: no` × `APPROVE`），
多帶了 `merge_recommendation: approve_after_update_branch`。

⇒ **解析器對未知鍵無檢查**（grep `unexpected`／`未知欄位`／`extra key` **零命中**）
⇒ 那筆事件當年就是這樣寫進去的：**硬擋擋住了 `no × APPROVE` 的組合嗎？沒有——
`validation.py:268-272` 的硬擋確實在**，⚠️ 所以那筆能寫進去代表它**繞過了 `wfcli review`**
（自由文字貼在留言裡），⛔ 不是通過了驗證。

⭐ **這是一個新發現，⛔ 且不在本卡射程**：查核事件可以不經 `wfcli review` 而以純文字
存在於留言中，⇒ 「所有裁決都受 schema 管轄」**不成立**。⚠️ 記於此交需求方裁定是否另卡。

### ⇒ 對本卡的設計結論

**一、新欄位⛔不得設為「缺即 invalid」的必填。** 依據是 D：既有事件（本 repo 已累積
**383 筆 finding、42 張卡有 review 事件**）全部沒有該欄位，設必填即整批失效——
而那些事件是 escalation 帳與 iteration 的來源。

**二、⭐ 正解是「新事件必填、既有事件豁免」，而豁免須有機械界線。**
本 repo 已有先例：`TRAILER_GUARD_EPOCH`（`doctor.py`）以 **committer date** 分流，
其 docstring 逐字說明為何用日期而非 SHA（「補 trailer 只能改寫已推送歷史，本專案明令禁止
⇒ 界線之前的 commit 產出的是沒有人被允許修的 finding，那是噪音不是 finding」）。
⇒ 建議比照：以**事件寫入時點**分流，界線之前不判 invalid、只在報告中標「該欄位不適用」。

⚠️ 但該先例自己逐字寫著「界線是**分流輔助，不是安全邊界**：`GIT_COMMITTER_DATE` 可任意
設定」。⇒ 本卡若比照，須同樣明說它擋不住什麼。

**三、⚠️ 未知鍵不受檢查這件事本身是把雙面刃。** 它使本卡的新欄位可以**先加進範本、
後加進驗證**（漸進上線），⛔ 但也代表任何人可以塞任意欄位而不被發現——`aiwf#57` R5 即是。
⇒ 本卡**不修**該缺口（⛔ 非射程），但設計時不得依賴「未知鍵會被擋」。

### ⚠️ 本輪未驗（依 canonical §6.4.2 標明原因）

- **`aiwf#57` R5 那筆究竟是繞過 `wfcli review` 還是當年驗證較寬**：⛔ 未查證。
  驗不了的原因：要判斷需回溯該事件寫入當時的 `validation.py` 版本，而
  `validation.py:268-272` 的硬擋是**哪一張卡加的**、何時生效，本輪未查。
  ⚠️ 兩種可能對本卡的結論**不影響**（都指向「未知鍵無檢查」），但對「所有裁決是否受
  schema 管轄」這個新發現**影響很大** ⇒ 若要另卡，須先查清。
- **383 筆 finding 的實際重跑**：⛔ 本輪只以構造的最小樣本測 A–D 四種形狀，
  ⛔ **未對真實的 383 筆逐一重跑**。驗不了的原因：無——⭐ **這是我沒做，不是做不到**；
  屬執行階段的驗收第 3 條（「須以真實既有事件實測」），逐字記下以免被讀成已驗。


## Comment 5400146514 · 2026-08-24T19:19:45Z

## ⛔ 更正第三輪的一個過度推論，並交付規劃（2026-08-25）

### 一、更正：`aiwf#57` R5 那筆**不是**繞過 schema 的查核事件

第三輪我寫「⭐ 這是一個新發現：查核事件可以不經 `wfcli review` 而以純文字存在於留言中
⇒『所有裁決都受 schema 管轄』**不成立**」。⛔ **過度推論，撤回。**

查證（規劃階段補查，正是第三輪自標的未驗項）：

| 事實 | 值 |
|---|---|
| 硬擋加入時點 | `f180659`，**2026-08-06**（`feat(cli): add wfcli review to enforce the review output contract`）|
| 那則留言的 marker | ⛔ **`wf-review-receipt:v1`，不是 `wf-review-event:v1`** |
| author | `ruan6047`　寫入 2026-08-16T04:37:13Z |
| 需求方當天的處置 | 2026-08-16T14:58:02Z 逐字「**採丙案——不把該輸出當查核記**，卡收回 📥Backlog」|

⇒ 它是**收據**不是裁決事件，而且需求方**當天就裁定它不算查核記**。
⭐ **schema 的管轄沒有破口** —— 我把一則被明確排除的收據當成了漏網的裁決。

⚠️ **這是本卡研究中的第二次過度推論**（第一次是第三輪把「未知鍵無檢查」推成「管轄不成立」，
即本則所更正者）。⭐ 兩次都是**看到一個異常就推出全稱結論**，⛔ 而正確做法是先查那個
異常的身分——本次查清只花了兩條指令。

### ⇒ 第一輪的量測要跟著修正

第一輪的配對表寫 `no × APPROVE = 1`。⇒ 該筆**應自母體剔除**（它不是查核事件）
⇒ **實際為 `no × APPROVE = 0`，否決權在查核事件上 71/71 機械成立、⛔ 零例外。**

⭐ 這**加強**第一輪的結論而非推翻它：既然否決權從無例外，再加第二個具否決權的欄位
更沒有必要。

### 二、規劃定案（三個設計題）

**設計題 1：`service_goal_still_served` ⛔ 無否決權，但為新事件必填。**
依據：否決權 71/71 已由硬擋機械保證；價值在「被迫回答」（§5.1.1 的實證是 `cpbl#166`
十輪查了會漂移的欄位）。⇒ 值 `no`／`unsure` 時**必附落差說明**，⛔ 但不改變
`review_result` 的合法組合。

**設計題 2：事後重驗與 `legacy_authority_notes` **合流**。**
判準來源改為呼叫現行的 `validate_*` 函式，`legacy_authority_notes` 降為其下的一個檢查項。
依據：canonical §5.1.2 逐字「當時針對單一形態單獨做，**不是通用機制**」；且實測
`validate_open_fields` 是純函式、可直接對既有卡重跑（161 張中 7 張不合規、全為遷移卡）。

**設計題 3：豁免界線用**事件寫入時點**分流，⛔ 不用「缺欄位即 invalid」。**
比照 `TRAILER_GUARD_EPOCH` 的既有先例（committer date）。⚠️ 且**須比照它一併寫明上限**——
該先例 docstring 逐字「界線是**分流輔助，不是安全邊界**：`GIT_COMMITTER_DATE` 可任意設定」。
⇒ 本卡的界線同樣擋不住刻意偽造的時點，⛔ 不得宣稱它是保證。

### ⚠️ 規劃階段仍未解（依 §6.4.2 標明原因）

- **「開卡時就違規」vs「開卡後規範改變」的區分**：⛔ 現行檢查函式不帶生效時點。
  驗不了的原因：需要每條規則的生效時點來源，而本 repo 只有一個先例（`TRAILER_GUARD_EPOCH`）
  ⇒ 是否為每條規則都建立時點屬**射程擴大**，⛔ 本卡不做；事後重驗的輸出改為
  **只列出不合規、不判定責任**。
- **383 筆既有事件的實際重跑**：屬執行階段（驗收第 3 條），⛔ 研究與規劃階段皆未做。
- **35 張無法解析資源宣告的卡**：屬 `aiwf#105`（OPEN）射程。⚠️ 事後重驗對它們會整批失敗
  ⇒ 兩卡交付順序互相影響，⛔ 本卡不處理但須在交付報告中逐字揭露。


## Comment 5400189309 · 2026-08-24T19:23:23Z

## 研究交付（第四、五輪，2026-08-25）：欄位會捕捉到東西嗎、查核者答得了嗎

⚠️ 這兩題**卡面驗收沒列**，是規劃定案後 PM 自問補查的——⭐ 因為前三輪都在答「怎麼做」，
⛔ 沒有一輪答「做了會不會有用」。

### 第四輪：它會捕捉到什麼（從既有 finding 反推）

母體：兩 repo 全部查核留言，**264 筆 finding**，其中 `attribution: planner` **32 筆**。
篩出與「射程／目標脫節」相關者：

| root_cause_id | 筆數 |
|---|---|
| `service-goal-misaligned-with-delivery-scope` | 2 |
| `marker-scope-narrows-away-safety-signal` | 2 |
| `core-pain-vs-service-goal-split` | 1 |
| `canonical-scope-gap-state-vs-event-stream` | 1 |
| `gate-scope-tier-unspecified` | 1 |
| `scope-and-guard-axis-communication` | 1 |
| `missing-platform-merge-gate` | 1 |
| `core-pain-not-mechanically-enforced` | 1 |

**合計 11 筆、跨 8 張卡**（`ai#16`／`#38`／`#48`／`#94`／`#107`／`#120`／`#130`、`cpbl#130`）。

⭐ 其中 **`core-pain-vs-service-goal-split`** 與 **`service-goal-misaligned-with-delivery-scope`**
是**逐字命中本欄位要處理的形態**——後者正是 `aiwf#130` R1-001／R2-001 的根因。

⇒ **欄位不是噪音**：它有 11 筆歷史實例，⛔ 不是「加了以後看看會不會有用」。

⚠️ 界限：篩選判準是 `root_cause_id` 或 finding 前 300 字含
`scope|goal|misalign|射程|目標` ⇒ **可能過抽也可能漏抽**，⛔ 未逐筆人工核對。
⭐ 但 11 > 0 這個結論對判準寬窄不敏感——即使只認前兩個逐字命中的 root_cause_id，仍有 3 筆。

### 第五輪：查核者答得了嗎（⛔ 這一題可能推翻整個設計）

`aiwf#130` 的核心痛點第三段逐字：「**查核者結構上判不了價值**：他無 `wfcli`、
無 Project 讀取權、看不到其他卡」。⇒ 若他答不了 `service_goal_still_served`，
本卡就是在造一個**必答但答不了**的欄位。

**查證兩件**：

**一、他讀得到那個欄位嗎。** ✅ 讀得到——`服務的原始目標` 在**卡面 body 第 6 行**
（`#136` 實測命中 5 次），⛔ **不需要 Project 讀取權**。

**二、他實際上答過嗎。** ✅ 答過——上述 11 筆中，`ai#130` 那筆的查核者逐字是
**`GPT-5@Codex`**、`attribution: planner`。⭐ 亦即他**已經在做這個判斷**，只是
schema 沒有欄位承接，只能寫進 finding 的自由文字。

⇒ **本欄位不是要求查核者做新的判斷，是把他已經在做的判斷變成必答且可統計。**

⚠️ **而 §130 核心痛點第三段仍然成立、⛔ 沒有被推翻**——它說的是「判不了**這張卡該不該
存在**」（要看其他卡），⛔ 不是「判不了**這次交付有沒有服務卡上寫的目標**」（只要讀卡面）。
⭐ 兩者不同，本卡只做後者。**前者仍無承接。**

### ⇒ 對規劃定案的影響

**⛔ 無變更。** 三項定案（無否決權、與 `legacy_authority_notes` 合流、事件時點分流）
不受這兩輪影響；⭐ 但第四輪為「無否決權」補上了一個更強的理由：11 筆歷史實例中
**沒有一筆**是「痛點已消但目標未達成」到需要否決的程度——它們全部**已經**以
`REQUEST_CHANGES` 結案（因為同輪還有別的 blocking）。
⇒ 給它否決權在這 11 筆上**不會改變任何結果**。

### ⚠️ 新增未驗（依 §6.4.2）

- **「11 筆全部已以 REQUEST_CHANGES 結案」未逐筆核對**：⛔ 我從「它們都在有 blocking
  finding 的輪次裡」推得，未逐筆查該輪的 `review_result`。驗不了的原因：無——
  ⭐ **這是我沒查，不是查不到**。⚠️ 若其中有一筆是 `APPROVE`，則「否決權不改變結果」
  這個理由就不成立，⇒ 執行前應補查。


## Comment 5404020456 · 2026-08-25T01:56:27Z

## 研究交付（第六輪，2026-08-25）：關掉自標的未驗項——⛔ 我推錯了，但結論更強

### 我在第五輪推的話

> 11 筆歷史實例中沒有一筆是「痛點已消但目標未達成」到需要否決的程度——它們全部**已經**
> 以 `REQUEST_CHANGES` 結案 ⇒ 給它否決權在這 11 筆上**不會改變任何結果**。

⚠️ 該句我當時逐字標了「這是我沒查，不是查不到」。**現在查了，⛔ 錯的。**

### 逐筆核對（8 筆可定位到裁決輪次）

| 卡 | root_cause | 該輪結果 | `core_pain` |
|---|---|---|---|
| `ai#16` ×2 | `marker-scope-narrows-away-safety-signal` | REQUEST_CHANGES | no |
| **`ai#94`** | **`core-pain-vs-service-goal-split`** | ⛔ **APPROVE** | yes |
| `ai#107` | `canonical-scope-gap-state-vs-event-stream` | REQUEST_CHANGES | yes |
| `ai#120` | `gate-scope-tier-unspecified` | REQUEST_CHANGES | yes |
| **`ai#120`** | **`guard-scope-limits-disclosed`** | ⛔ **APPROVE** | yes |
| `ai#130` ×2 | `service-goal-misaligned-with-delivery-scope` | REQUEST_CHANGES | no |

⇒ **8 筆中 2 筆在 `APPROVE` 的輪次裡**，⛔ 不是我說的「全部 REQUEST_CHANGES」。

### ⭐ 而 `ai#94` 那筆逐字說出了本卡的設計

該 finding（`blocking: false`、`attribution: planner`）的 disposition 逐字：

> 這輪 `core_pain_resolved` **應對核心痛點欄判 yes**，⛔ **不應拿本卡刻意排除的服務目標欄
> 否掉整張交付**；若需求方要驗「卡面兩欄是否分家」，應另立軸

⇒ ⭐ **2026-08-16 就有一位查核者，在沒有本欄位的情況下，自己推導出了「服務目標該是
另一條軸、且不該否決」的結論。** 而 canonical §5.1.1 是 2026-08-24 才寫的。

### ⇒ 對規劃定案的影響：⛔ 無變更，但理由要換掉

**原理由（第五輪）**：「給否決權不會改變任何結果」——⛔ **撤回，事實不成立**。

**新理由（更強）**：⭐ **給它否決權會改變結果，而那個改變是錯的。**
`ai#94` 那輪若本欄位有否決權，該筆 finding 就會把一張**核心痛點確實已消、且刻意排除服務
目標欄**的交付否掉——而當時的查核者已經逐字指出那樣做不對。

⇒ **「無否決權」不是因為它沒作用，是因為它的作用方向會錯。**

⚠️ 而 `guard-scope-limits-disclosed`（`ai#120`、APPROVE）是另一種：它記的是「守衛的限制
已揭露」——⭐ 那是**正面**的射程觀察，⛔ 本來就不該否決任何東西。
⇒ 這一筆說明本欄位的值域需要 `yes` 之外的**中性**選項，而 canonical 給的 `unsure`
正好承接它。**⭐ `unsure` 的語意由此得到第一個真實錨點**（第三輪標為「無先例可查」的那項）。

### ⚠️ 本輪的方法界限

- **母體從 11 筆降為 8 筆**：另 3 筆無法定位到具體裁決輪次（留言切分後找不到同則的
  `review_result`）。⛔ 未逐一人工核對。⚠️ 若那 3 筆中有更多 `APPROVE`，
  ⭐ **只會加強**新理由（更多「不該否決卻會被否決」的實例）。
- ⭐ **本輪本身即為「宣稱超過證據」的第四個實例**：第五輪那句話我標了未驗、也講了
  驗不了的原因是「我沒查」，⛔ 但仍把它寫進了推理鏈並用來支撐定案。
  ⇒ **標了未驗不等於可以拿來當理由用。** 這一條值得進 `aiwf#11`。


## Comment 5404049351 · 2026-08-25T02:00:00Z

## 研究交付（第七輪，2026-08-25）：豁免界線的機制**已經存在**，⛔ 不必新造

### 規劃定案原本說的

> 設計題 3：豁免界線用**事件寫入時點**分流，比照 `TRAILER_GUARD_EPOCH` 的既有先例。

⚠️ `TRAILER_GUARD_EPOCH` 是 **commit 的 committer date**，而 review 事件不是 commit
⇒ 「比照」需要一個對應物。⭐ 查證後發現：**對應物已經存在，而且正是為同一件事做的。**

### ⭐ `contract-baseline` cutover 機制

`review.py:1245` 的 `render_contract_baseline_comment` 渲染一則 `contract-baseline` 事件：

```yaml
wf_contract_baseline: v1
contract: templates/review-escalation.md
effective_from: <timestamp>
declared_by: <who>
rationale: <why>
```

其註解逐字：「此 marker 為 **one-shot cutover**（`review-escalation.md` §5）：
不得附在 review 或 handoff 事件上，啟用後再次出現必須 **fail loud**。
**本行之前的 attempt 依契約…**」

`review-escalation.md:341` 逐字：

> 新增此 type 屬**契約變更**，適用範圍依本節末段的 **`contract-baseline` cutover 機制**；
> **cutover 前的歷史事件**…

`:195` 另有：

> **cutover 前的既有留痕：標為 legacy，⛔ 不改寫、不追溯補建。**

### ⭐ 而它跑過兩次，⛔ 不是紙上機制

| 時間 | 卡 |
|---|---|
| 2026-08-13T09:07:51Z | `aiwf#57` |
| 2026-08-21T08:28:04Z | `aiwf#39` |

⇒ **契約變更的前後分流在本 repo 是既有、已驗證、且有兩個實例的路徑。**

### ⇒ 規劃定案第 3 項修正

**原**：「比照 `TRAILER_GUARD_EPOCH` 的日期分流」——⛔ 那是 commit 的機制，套到事件上要另造。

**改**：⭐ **直接沿用 `contract-baseline`**。本卡的 schema 變更即為一次契約變更
⇒ 交付時發一則 `contract-baseline` 事件，`effective_from` 之前的 review 事件依 `:195`
**標為 legacy、⛔ 不改寫、不追溯補建**，`service_goal_still_served` 對它們**不適用**而非 invalid。

⭐ **這比原方案好三點**：
1. ⛔ 不新造機制——避免 `aiwf#134` 已犯過的「再做一個單一形態的東西」
2. 它**已有 fail-loud 保護**（重複出現必須 fail loud），⛔ 而新造的日期常數沒有
3. 它要求 `declared_by` 與 `rationale` ⇒ **界線本身有留痕與具名**，
   ⚠️ 而 `TRAILER_GUARD_EPOCH` 只是一個寫死的常數字串

### ⚠️ 但要一併寫明它擋不住什麼

`TRAILER_GUARD_EPOCH` 的 docstring 逐字「界線是**分流輔助，不是安全邊界**」。
⭐ `contract-baseline` 好一些（有 `declared_by`、有 fail-loud），⛔ **但仍不是安全邊界**：
`effective_from` 是宣告值，發事件的人可以填任意時點。⇒ 本卡沿用它時**須同樣明說**。

### ⚠️ 本輪未驗（依 §6.4.2）

- **那兩次 cutover 的 `effective_from` 是否等於實際寫入時間**：⛔ 未比對。
  驗不了的原因：無——⭐ **我沒查**。⚠️ 依第十一筆的教訓（`aiwf#11`
  issuecomment-5404033287），**本項⛔不得進入推理鏈**：上面「它有留痕與具名所以較好」
  這句**不依賴**該比對，若日後發現兩者不符，只影響「它有多可靠」而不影響「它已存在且該沿用」。
- **`contract-baseline` 目前是否只綁 `review-escalation.md` 一份契約**：碼裡 `contract:`
  欄寫死該路徑。⇒ 本卡若要宣告 `review-prompt.md` 的變更，該欄需否參數化，
  ⛔ 本輪未查，屬執行階段。


## Comment 5404062444 · 2026-08-25T02:01:22Z

## 研究交付（第八輪，2026-08-25）：⛔ 本卡的兩半在碼上零交集，建議拆卡

⚠️ 這一題**卡面沒列、規劃也沒問**。⭐ 補查的理由：今晚 `aiwf#130`（五輪）與
`aiwf#134`（五輪）的 blocking 中，最貴的兩個都是**射程問題**
（`service-goal-misaligned-with-delivery-scope` ×2）⇒ 開工前該先驗射程。

### 兩半在碼上的關係

| | A 半：review schema | B 半：doctor 事後重驗 |
|---|---|---|
| canonical | §5.1.1 | §5.1.2 |
| 檔 | `review.py`、`validation.py`、`templates/review-prompt.md`、`templates/review-escalation.md` | `doctor.py`、`doctor_cmd.py`、`validation.py` |
| 交集 | \multicolumn ⇒ **只有 `validation.py`** | |

⛔ **而那個交集是假的**：實測 `doctor.py` 提及 `validation` **0 次**；
`doctor_cmd.py` 只 import 了 `ValidationError` 與 `validate_source_sha`
（⛔ 與本卡無關的兩個）。⇒ **兩半今天沒有任何共用碼路徑。**

⚠️ 它們唯一的連結是 **canonical 把 §5.1.1 與 §5.1.2 寫在相鄰位置**——⭐ 那是**文件的
排版**，⛔ 不是設計上的耦合。

### 資源交集也不同

| | 與哪些 OPEN 卡撞 |
|---|---|
| A 半 | `#115`（`review.py`）、`#86`／`#38`（`review-prompt.md`）|
| B 半 | `#30`（`doctor.py`＋`doctor_cmd.py`，**兩個都撞**）|

⇒ **⛔ 兩半的阻擋來源完全不同**：A 半卡在 review 家族的三張，B 半卡在 `#30` 一張。
合成一卡等於**把兩組不相干的阻擋綁在一起**——任一組被認領，整張卡就動不了。

### ⇒ 建議：拆成兩張

**`S7a` review schema**（§5.1.1）：`service_goal_still_served` 欄位、值域、必填規則、
`contract-baseline` cutover。⭐ **可獨立交付且立刻生效**——範本每次派審都被讀。

**`S7b` doctor 事後重驗**（§5.1.2）：與 `legacy_authority_notes` 合流。
⚠️ 依第二輪實測，它一上線就會報出 7 張不合規（全為 2026-08-04 遷移卡）
⇒ 也可獨立交付。

⛔ **不建議合做**的第三個理由：本卡的查核能力層級寫「高階型：本卡改的是查核自身的契約」
——⭐ 那句話**只對 A 半成立**。B 半改的是 `doctor` 的唯讀掃描，⛔ 不碰查核契約
⇒ 合成一卡會讓 B 半被過度規格化（多跑幾輪高階查核）。

### ⚠️ 但拆卡是射程變更，⛔ 需求方裁定

⛔ PM 不逕行拆。⚠️ 且拆卡有一個代價：`#130` 的切片計畫寫的是「S7」一張，
拆成兩張後**切片編號與計畫不一致** ⇒ 須在 `#130` 的計畫留言補記。

### ⚠️ 本輪未驗（依 §6.4.2）

- **`contract:` 欄位寫死 `templates/review-escalation.md`**（`review.py:1260`）
  ⇒ 若 A 半要宣告 `review-prompt.md` 的變更，該欄需參數化。⛔ 本輪未查它是否有其他呼叫端
  依賴該寫死值。驗不了的原因：無——**我沒查**。
  ⚠️ 依 `aiwf#11` issuecomment-5404033287 的第十一筆教訓，**本項⛔不進推理鏈**：
  上面的拆卡建議**不依賴**它（拆或不拆，該欄都要處理）。
- **`unsure` 的完整語意**：第六輪找到第一個錨點（`guard-scope-limits-disclosed`，
  正面的射程觀察），⛔ 但只有一個實例。⚠️ 不足以定義值域語意，屬 Design 提案。


## Comment 5404142574 · 2026-08-25T02:11:31Z

## 研究交付（第九、十輪，2026-08-25）

### 第九輪：關掉「`contract:` 寫死」那個自標的「我沒查」

第八輪我標了「⛔ 本輪未查它是否有其他呼叫端依賴該寫死值。驗不了的原因：無——我沒查」。
**查了。**

`review.py:1180` 的偵測器逐字：

```python
def body_has_contract_baseline(body: str) -> bool:
    data = find_block_by_key(body, BASELINE_BLOCK_KEY)   # "wf_contract_baseline"
    return data is not None and str(data.get(BASELINE_BLOCK_KEY)).strip() == BLOCK_VERSION
```

⇒ ⭐ **它只認鍵名與版本，⛔ 完全不讀 `contract:` 的值。** 全 repo 的其他引用
（`validation.py:526`／`:545`／`:730`、`test_doctor.py:1726`）也都只用鍵。

⇒ **該寫死值沒有任何消費端** ⇒ 參數化它是**零風險的純新增**，⛔ 不是我第八輪擔心的相容性題。
⚠️ 但反過來說：**它也不提供任何保護**——同一個 `wf_contract_baseline` 鍵無法區分
「這次 cutover 換的是哪一份契約」。⇒ 若本卡要宣告 `review-prompt.md` 的變更，
**必須參數化該欄，否則留痕上分不出兩次 cutover 各換了什麼。**

### 第十輪：⭐ 新欄位的上線路徑，可能是整個設計的死穴

**問題**：`service_goal_still_served` 設為新事件必填後，查核者怎麼**知道**要填？

**路徑一：`wfcli review --validate-only`**（`review_cmd.py:168`／`:247`）。
⛔ **走不通**——`aiwf#134` 的 R1 已確立、`aiwf#130` 核心痛點第一段逐字記載：
**跨家族查核者沒有 `wfcli` 寫入通道**。他跑不了 `--validate-only`。
⇒ 他第一次知道自己漏填，是 **PM 代跑 `wfcli review` 被拒**的時候——
⚠️ 那已經是報告寫完、貼回來之後。

**路徑二：派審詞範本**。`templates/review-prompt.md` 第 3 行逐字：
「**祕書派審時以此組裝**」。

⭐ **而那正是 `aiwf#66`／`aiwf#38` 立案的痛點**：
- `#66`：「派審詞由人手寫而 `handoff` 是另一個動作，於是**兩個來源必然漂移**」
- `#38`：「派審詞的正確性**今天完全依賴 Coordinator 手抄**，且無留痕可事後稽核」

⇒ ⛔ **本卡新欄位的上線，依賴一條已知會漂移、且有兩張 OPEN 卡在等修的人工路徑。**

### ⇒ 這對本卡的設計有具體後果

**一、⛔ 不能只改範本就當作上線。** 範本改了，而 PM 每次手組派審詞時可能漏帶那一段
——⚠️ **今晚就有實例**：`aiwf#134` 五輪派審詞全由我手寫，⭐ 而其中 R2 的派審詞
**漏了 R1-006 的 V5／A10 兩項要求**，直到查核者自己指出。

**二、⭐ 正解是讓拒收訊息自己教會查核者。** 缺欄位時 `wfcli review` 的 stderr
須逐字說明：欄位名、值域、`no`／`unsure` 要附什麼、以及**這是新契約**（附
`contract-baseline` 的 `effective_from`）。⇒ 那條訊息是**唯一必經**的路徑，
⛔ 不依賴 PM 記得。

**三、⚠️ 但它仍是「事後」**——查核者得先寫完整份報告才會撞到。
⭐ 真正的修法是 `#66`（派審詞由 `handoff` 產生），⛔ 不在本卡射程。
⇒ **本卡應在交付報告中逐字揭露：新欄位的上線在 `#66` 落地前，
其送達率等同於 PM 的手抄正確率。**

### ⚠️ 本輪未驗（依 §6.4.2）

- **PM 手抄漏帶的實際比率**：⛔ 未量測。⚠️ 依第十一筆教訓，**本項不進推理鏈**——
  上面的結論只依賴「存在漏帶實例」（`aiwf#134` R2 一例已足），⛔ 不依賴比率大小。
- **`--validate-only` 是否真的完全不碰網路**：`review_cmd.py:8` 的註解如此聲稱，
  ⛔ 本輪未實跑驗證。⚠️ 若它其實會碰網路，路徑一連 PM 代跑都可能受限；
  但那**不改變**結論（查核者本來就沒有通道）。


## Comment 5404179008 · 2026-08-25T02:15:40Z

## ⛔ 更正（前一則第十輪）＋ 第十一輪

### 更正：我把「交付漏帶」寫成了「派審詞漏帶」

前一則我寫「`aiwf#134` **R2 的派審詞**漏了 R1-006 的 V5／A10 兩項要求」。
⛔ **那句沒查證就寫了，而且錯的。** 查證後：

`aiwf#134` R2-002 的 evidence 逐字是「R1-006 的 **V5 與 A10 尚無可稽核交付物**：
Issue #134 **未附**三張既有卡（含終態）的 amend/handoff dry 路徑證據…」
⇒ 漏的是我**交付**時沒附證據，⛔ **不是派審詞漏寫要求**。

⭐ **而「派審詞當時到底有沒有寫」——查不到。** `aiwf#134` 五輪的 comments（714 行）
裡沒有任何一則派審詞留痕。⇒ 這一項依 §6.4.2 是 **unobservable，⛔ 不是「未查」**。

### ⇒ 第十一輪：查不到本身就是答案，而且比原本的證據強

`templates/dispatch-package.md:53–54` 逐字：

> 跨家族查核者…**貼不了收據**；…故**不要求查核者留收據**…
> ⚠️ **本節撤除紀律後沒有補上任何機器面保證**：PM 轉錄是否忠實於查核者原話，
> 在沒有收據的路徑上**完全沒有機器可檢查的東西**

（需求方 2026-08-19 裁定。）

⇒ 所以第十輪的結論**不需要**那個被我寫錯的實例。**真正的依據是機制本身**：
派審詞在設計上就不留痕 ⇒ 「PM 有沒有帶到某條要求」**構造上不可稽核**。

### ⭐ 更精確的形狀：查核契約是**不對稱**的

| | 消費者 | 機器保證 |
|---|---|---|
| `review-prompt.md` **§5**（查核者的**輸出**） | `review.py` 嚴格解析（`:1`／`:48` `FINDING_KEYS`／`validation.py`） | ✅ 有：不合格直接拒收 |
| `review-prompt.md` **§1–§4**（查核者的**輸入**） | ⛔ 無任何程式讀 | ⛔ 無 |
| `dispatch-package.md`（派工全份） | ⛔ 無任何程式讀（全 repo grep 零命中） | ⛔ 無 |

⇒ **輸出面加必填欄是廉價且可強制的；而「查核者為什麼知道要填」全在無保證的輸入面。**

### ⇒ 對本卡的最終設計主張（取代第十輪第二點的措辭）

**新欄位的強制力必須完全落在拒收訊息上，⛔ 一個字都不要押在派審詞上。**
拒收 stderr 須自帶：欄位名、值域、`no`／`unsure` 的附帶要求、以及
`contract-baseline` 的 `effective_from`（⇒ 查核者能自己判斷「這是新規則不是我漏看」）。

⭐ 理由不是「派審詞可能漏」（那是機率），而是「**派審詞漏沒漏在構造上量不到**」（那是設計）。
⇒ 任何依賴它的設計，其失效**無法被觀測到**——那正是 `aiwf#38` 立案的原話。

### ⚠️ 本輪未驗

- **`validation.py` 的頂層必填欄集合實際長怎樣**：本輪只確認 `review.py:4` 逐字宣告
  「必填欄、列舉值、`self_run` 非空、第一判準否決權**集中在 `validation.py`**」，
  ⛔ 未讀該集合本身。⇒ 實作時新欄位要加在哪一處**尚未定位**，需在規劃交付前補。

