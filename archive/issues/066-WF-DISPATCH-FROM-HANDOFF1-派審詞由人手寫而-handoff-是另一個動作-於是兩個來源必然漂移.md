# #66 WF-DISPATCH-FROM-HANDOFF1 派審詞由人手寫而 handoff 是另一個動作，於是兩個來源必然漂移
- state: open  created: 2026-08-12T15:01:48Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/66
- comments: 3

## Body

- 需求：—　規劃：—
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；要決定派審詞骨架由誰產生、產生多少（機械欄位 vs 導讀散文的界線），且該骨架會成為所有後續查核的入口；踩在唯一寫入通道上，推理鏈中等。）　查核：待指派（建議 主力型；紅線：本卡改的是查核入口本身，寫錯會讓每一輪查核都拿到錯的 SHA。查核重點在「兩個來源變一個」是否真的成立，還是只是多了一個會漂移的來源。建議跨家族。）
- Initiative：—　spec 基線：docs/ROADMAP.md（main d735cad）§0 目標 2「可稽核的內容」與 §5。需求方 2026-08-12 於總結後裁定執行本項與 DEV-STATE-FACE-DRIFT-GUARD1。⚠️ 與 WF-DISPATCH-PRECHECK1（#38）的關係須由執行者裁定：#38 走的是「派審前置檢查」路線（查核者自檢派審詞），本卡走「同源產生」路線（讓不一致不可能發生）。兩者可能互斥、可能互補，執行者須論證，不得逕行假設。#38 現為進行中。
- DB：db_scope=none
- 服務的原始目標：讓派審詞的機械欄位與 handoff 事件同源，使兩者不可能不一致

## 簡介
<!-- card-brief:begin -->
讓 handoff --next-stage review 從【同一次事件】產生派審詞骨架並貼上 Issue，機械欄位（被審 SHA、以 merge-base 算出的基線、iteration、前輪 findings）由事件與卡面自動帶入而非 PM 手抄，使兩個來源變一個、不一致不可能發生。**適用時機**：派審詞與 handoff 事件對不上（審了舊產物、或貼了派審詞卻沒跑 handoff）時；或要停產 docs/tasks/ 卡檔前確認六條放行判準是否都滿足時。⛔ 非射程：與 WF-DISPATCH-PRECHECK1（aiwf#38）是取代還是互補由本卡執行者裁定，不得逕行假設；六條未全滿足前不得停止產生 docs/tasks/ 卡檔、不得整批刪除既有 stub。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：派審詞的機械欄位（被審 SHA、基線、iteration、worktree）今天由 PM 手寫，而 handoff 事件由 wfcli 寫——兩個來源，必然漂移。2026-08-12 當日發作三次：#9 與 #38 做了 handoff 卻沒補發派審詞，其中 #9 的查核者依指示審了舊產物、整輪作廢，#38 的查核者正確拒審並判 handoff-artifact-identity-mismatch（attribution=coordinator）；#42 貼了派審詞卻沒跑 handoff，Log 上最後一筆停在前一個 SHA。同日 PM 給 Codex 的協調者提示詞 SHA 全部正確，卻寫著「權威在 Issue 上」而 Issue 上那則是舊的——供了兩個來源並指定錯的那個為權威，這正是 WF-DISPATCH-PRECHECK1（#38）存在要治的病，而 PM 在派它去審的過程中示範了一次。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/handoff_cmd.py",
    "file:cli/tests/test_commands_mocked.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] handoff --next-stage review 產出派審詞骨架並貼上該 Issue，機械欄位（被審 SHA、基線、iteration、前輪 findings）由事件與卡面自動帶入，不由人手抄。
- [ ] 【放行判準 1／6】handoff --next-stage review 能從【同一次事件】產生派審詞——不是事後另跑一支讀別處的工具。⚠️ 現行 review_prompt.py 正是「另一支讀別處」而那個別處已封存，此條即為防止重演。
- [ ] 【放行判準 2／6】Issue-only 測試涵蓋完整鏈路 open → handoff → prompt → review → release。⚠️ 目前只有零星卡實測走過，而且靠 PM 手寫派審詞補洞，不構成涵蓋。
- [ ] 【放行判準 3／6】派審詞自動帶入 Issue body 的驗收／驗證／Gate 章節、source SHA、iteration 與【前輪 findings】。前輪 findings 這項尤其重要——手寫時最容易漏，而漏了會讓查核者重開已閉合的 finding。
- [ ] 【放行判準 4／6】cpbl-analytics 的 docs/ROADMAP.md:494 之 cancelled_with_report 條款改有新的 versioned 留存位置。⚠️ 現行條款要求「報告寫進 docs/tasks/<CARD_ID>.md（該檔開卡時已在 main）」，該前提在停止產生卡檔後不成立。
- [ ] 【放行判準 5／6】canonical 的「卡片一檔」、封存與索引契約同步改版。⚠️ 索引契約已實測漂移：cpbl-analytics 的 125 個 archive 檔中有 23 個沒有索引列。
- [ ] 【放行判準 6／6】所有 docs/tasks/ consumer 完成遷移或正式退役。已知四個：tests/test_task_card_sections.py（測試，略過已封存者）、scripts/review_prompt.py:120、scripts/state_plane_migrate.py:158（舊狀態面遷移工具、非新卡 consumer）、scripts/review_gate_inventory.py:52。⚠️ 此清單由 PM 調查、查核者複驗，但【未證明窮盡】。
- [ ] ⚠️【禁止項】在上述六條全部滿足前，不得停止產生 docs/tasks/ 卡檔、不得整批刪除既有 stub。後者已有實證反對：跨家族查核者逐檔對過 Issue，至少 8 檔含非 boilerplate、未逐字存在於 Issue body 的內容（DB 宣告、裁定紀錄、完整驗收條件）。
- [ ] **⚠️⚠️ 2026-08-27 前提失效登記（PM，⛔ 非新增射程）——本卡兩處前提今日為假，重新排程前必須先處置。** **(1) spec 基線行逐字「`#38` 現為進行中」⛔ 為假**：`WF-DISPATCH-PRECHECK1` 今日交付狀態為 **📥Backlog**，最後交接 `2026-08-13T00:24:01+08:00`（PM 以 `wf_cli.project.list_items` 讀，量在 `2026-08-27`）。⇒ 簡介與 spec 基線行把「與 `#38` 是取代還是互補」交給本卡執行者裁定，而該裁定的前提（對方在動）已不成立。**(2) ⭐⭐ 核心痛點的三個實例全部發生在 `2026-08-12` 一天（`#9`／`#38`／`#42`），而通道形狀今日已改變。** 實測（`aiwf#137` 第三輪，事前登記 `PREREG.md` sha256 `acf022c663b99f69e1576eb27d86ea951bd0cd790b38f16c267ffe0f929d0343`，⛔ 判準寫定於讀語料前）：留言含 `## 派審` 標題者全史 **95 則／30 張卡**，時間帶 `2026-08-10T10:15:03Z` → **`2026-08-21T12:16:04Z`**；**08-10／08-11／08-12 三天佔 89/95，08-21 之後為 0**，而同期（08-22 起）裁決事件仍有 **68 則**。近 11 張被查核的卡 `## 派審` 命中 **0**。⇒ **今天派審詞完全不落任何 repo 面，只存在於 session。** ⛔ 本卡治的是「派審詞與 handoff 事件**漂移**」（兩個來源不一致），⚠️ **而今日的病已經不是漂移，是派審詞根本不進 Issue** —— 同一條通道、⛔ 不同的病。重新排程時**核心痛點須重寫**，⛔ 不得沿用 08-12 的三個實例當現況依據。⚠️ 誠實邊界：上述量測為**關鍵字法**（三層：`## 派審` 標題／結構標記／最寬詞），⛔ 若今日派審詞改用完全不同措辭且無結構標記則量不到。**什麼會推翻本條**：找到任何一份 `2026-08-21` 之後、落在 repo 任何面的派審詞。
- [ ] **⭐⭐ 2026-08-27 需求方裁定：`WF-REVIEW-SERVICE-GOAL1`（`aiwf#137`／S7a）的射程併入本卡骨架，⛔ 不另行實作 schema 欄位。** 併入的是**一個必含問句**：派審詞骨架須逐字問查核者「**這張卡服務的原始目標（卡面「服務的原始目標」欄逐字內容）今天還被服務嗎**」，形狀比照 `templates/review-prompt.md` §2 第一判準把卡面痛點原文代入的做法。**依據（`aiwf#137` 三輪研究，⛔ 逐條可重跑）**：(a) canonical §5.1.1 已定義該判準為必答，而 `templates/review-prompt.md`／`AGENTS.md`／`CLAUDE.md` 對「服務的原始目標」`grep -c` **皆為 0** ⇒ **問題今天沒有被交到查核者手上**；(b) `d4ba7ce5` 之後 **24 則**帶 marker 的裁決、橫跨 **11 張卡**，以五個關鍵字掃全文 **23 則零命中** ⇒ **0 則實際套用過第二判準**，而那 11 張卡的目標欄**全部實填**（⛔ 無 placeholder）；(c) ⛔ **改範本無效**：§2 第一判準已在範本裡兩週半，95 份派審詞的逐字重疊率**全為 0.0000**、強判準轉抄率 **0/95** ⇒ 唯一送得到查核者的通道是**本卡要造的骨架**；(d) ⛔ **不做 schema 必填欄位**：三個 facts 讀取端（`escalation_facts_from_body`／`audit_conformance`／`audit_review_channel`）**皆無自動執行路徑**（兩 repo `ci.yml` 對 `wfcli|doctor` 零命中、非樣本 git hooks 0 個），且 `WF-POSTHOC-CONFORMANCE1` 已 🏁完成而其 `audit_conformance` ⛔ 不讀留言 ⇒ 欄位寫得進去今天沒有消費者；(e) ⛔ **不做 `no × APPROVE` 否決權**：`aiwf#57` 的 `issuecomment-5305745859` 是一則真實的 `core_pain_resolved: no` ＋ `review_result: APPROVE`（作者 `GPT-5.6@Codex`，⛔ 無 `wf-review-event` marker）⇒ **唯一一次有人想要它，機械否決沒擋住**；且硬拒零寫入 ⇒ 正確運作時構造上不可觀測。⚠️ **登記本條的理由是防止靜默消失**：`aiwf#38` 的簡介已逐字裁定過「⛔ 不得把規則寫進 `templates/dispatch-package.md`（該檔只送被約束者本人、從不進 Issue 留痕）」，而本卡卡面自陳「若本卡只做機械欄位同源，該層會靜默消失」。**什麼會推翻本條**：本卡落地後 **20 則以上**由骨架產生的派審詞中含該問句者 **< 0.80** ⇒ 通道論被推翻，回頭考慮 schema 必填（門檻於 2026-08-27 釘死，⛔ 不得事後訂）。

## 驗證

- [ ] cd cli && uv run pytest -q 不得退化（基線自己跑）。
- [ ] 以突變注入證明同源：改 handoff 輸入的 SHA，骨架的被審 SHA 須跟著變；把骨架改成從別處讀，測試須轉紅。附輸出。
- [ ] 凡寫下「不可能不一致」須指出執行者所在的檔與行；沒有機械執行者的寫成約定。

## Log

- 2026-08-12T23:01:47+08:00 open by —；owner 待指派；iteration 0。
- 2026-08-16T11:10:30+08:00 amend by wf-cli（op 21c34aa1）→ 驗收條件：原值「[ ] handoff --next-stage review 產出派審詞骨架並貼上該 Issue，機械欄位（被審 SHA、基線、iteration、分支與 worktree）全部取自本次 handoff 寫入的同一組值。⚠️ 判準是「同源」不是「一致」——若骨架的值來自另一次讀取，那只是多了一個會漂移的來源。須以突變證明：改動 handoff 的輸入，骨架跟著變。；[ ] ⚠️ 裁定導讀散文怎麼辦。派審詞今天含大量 PM 手寫的攻擊點與背景，那些無法機械產生。兩條路：骨架只含機械欄位、散文由 PM 追加為第二則留言（兩則留言的關係要成文）；或骨架留一個 PM 填的區塊。執行者須裁定並說明另一條為何不選。；[ ] ⚠️ 不得讓本卡自己成為新的漂移源。若 PM 仍可手寫覆蓋機械欄位，本卡未關閉核心痛點。若選擇禁止覆蓋，須說明異常修正時怎麼辦。；[ ] 與 WF-DISPATCH-PRECHECK1（#38）的關係須明確裁定：取代、互補、或兩者射程不同。不得默默並存讓後人猜。」→ 新值「handoff --next-stage review 產出派審詞骨架並貼上該 Issue，機械欄位（被審 SHA、基線、iteration、分支與 worktree）全部取自本次 handoff 寫入的同一組值。⚠️ 判準是「同源」不是「一致」——若骨架的值來自另一次讀取，那只是多了一個會漂移的來源。須以突變證明：改動 handoff 的輸入，骨架跟著變;⚠️ 基線須以 merge-base 算出而非取 origin/main 現況。承接 #38 驗收條 1 的裁定：在範本裡寫規則與現在手填的可靠度差別是零，正解是把值算出來（git_ops.is_ancestor 已存在，只差一個 merge_base()）。⚠️ 2026-08-11 五份派審詞的基線全抄成當下 origin/main；2026-08-15 PM 又把某未 merge 分支的中途測試數當 main 基準寫進兩份派工單——同一形狀四天內兩種抄法;⭐【承接 #38 驗收條 2 第 (1) 層，同源產生不蘊含它】templates/review-prompt.md 的前輪閉環回報須由散文升為必填小節（帶 finding_id 逐列），查核者收到即可自查缺節並自判 review-invalid。#38 自陳那是「唯一今天可動且送達對象正確的一層」。若本卡只做機械欄位同源，該層會靜默消失;⚠️ 裁定導讀散文怎麼辦。派審詞今天含大量 PM 手寫的攻擊點與背景，那些無法機械產生。兩條路：骨架只含機械欄位、散文由 PM 追加為第二則留言（兩則留言的關係要成文）；或骨架留一個 PM 填的區塊。執行者須裁定並說明另一條為何不選;⚠️ 不得讓本卡自己成為新的漂移源。若 PM 仍可手寫覆蓋機械欄位，本卡未關閉核心痛點。若選擇禁止覆蓋，須說明異常修正時怎麼辦;【與 #38 的關係・2026-08-16 需求方裁定】本卡承接 #38 的前瞻射程（上述兩條），但 #38 維持 OPEN——它在 iteration 5、有 3 輪 REQUEST_CHANGES findings 未閉合（2026-08-12 三次，查核者皆 GPT-5@Codex 子代理），其後被批次降級。⚠️ **本卡執行者須逐一列出那三輪的 findings，各自閉合或轉入本卡**，那是 #38 的解除條件；執行者本來就得讀那三輪才知道要建什麼。裁定全文見 issuecomment-5305463996;交付物本身須通過 WF-24-EVIDENCE-STRENGTH1（#11）的 (e) 與 (f)：凡寫下「必須／拒收／擋下／強制」等字眼，須指出執行者所在的檔與行，沒有機械執行者者一律寫成「約定」；凡宣稱「查不到／不存在」，須確認量測工具真的在量你以為的東西」；理由 需求方 2026-08-16 裁定本卡與 #38 的關係（本卡原驗收條 4 逐字要求「不得默默並存讓後人猜」）。裁定為：本卡承接 #38 的前瞻射程，但 #38 維持 OPEN 至其三輪未閉合 findings 結清。三項實質變更：(1) 把 #38 驗收條 1 的基線 merge-base 裁定寫進本卡；(2) ⭐ 把 #38 驗收條 2 第 (1) 層（review-prompt.md 前輪閉環必填小節）具名寫進本卡——同源產生不蘊含它，只做機械欄位同源會讓該層靜默消失；(3) 原驗收條 4「須裁定關係」改為裁定結果本身，並載明 #38 的解除條件與其執行者。另補 #11 的 (f)（量測工具作用域，2026-08-16 新增）至交付物自檢要求。。
- 2026-08-17T17:45:39+08:00 amend by wf-cli（op 0323049b）→ 驗收條件：原值「[ ] handoff --next-stage review 產出派審詞骨架並貼上該 Issue，機械欄位（被審 SHA、基線、iteration、分支與 worktree）全部取自本次 handoff 寫入的同一組值。⚠️ 判準是「同源」不是「一致」——若骨架的值來自另一次讀取，那只是多了一個會漂移的來源。須以突變證明：改動 handoff 的輸入，骨架跟著變;⚠️ 基線須以 merge-base 算出而非取 origin/main 現況。承接 #38 驗收條 1 的裁定：在範本裡寫規則與現在手填的可靠度差別是零，正解是把值算出來（git_ops.is_ancestor 已存在，只差一個 merge_base()）。⚠️ 2026-08-11 五份派審詞的基線全抄成當下 origin/main；2026-08-15 PM 又把某未 merge 分支的中途測試數當 main 基準寫進兩份派工單——同一形狀四天內兩種抄法;⭐【承接 #38 驗收條 2 第 (1) 層，同源產生不蘊含它】templates/review-prompt.md 的前輪閉環回報須由散文升為必填小節（帶 finding_id 逐列），查核者收到即可自查缺節並自判 review-invalid。#38 自陳那是「唯一今天可動且送達對象正確的一層」。若本卡只做機械欄位同源，該層會靜默消失;⚠️ 裁定導讀散文怎麼辦。派審詞今天含大量 PM 手寫的攻擊點與背景，那些無法機械產生。兩條路：骨架只含機械欄位、散文由 PM 追加為第二則留言（兩則留言的關係要成文）；或骨架留一個 PM 填的區塊。執行者須裁定並說明另一條為何不選;⚠️ 不得讓本卡自己成為新的漂移源。若 PM 仍可手寫覆蓋機械欄位，本卡未關閉核心痛點。若選擇禁止覆蓋，須說明異常修正時怎麼辦;【與 #38 的關係・2026-08-16 需求方裁定】本卡承接 #38 的前瞻射程（上述兩條），但 #38 維持 OPEN——它在 iteration 5、有 3 輪 REQUEST_CHANGES findings 未閉合（2026-08-12 三次，查核者皆 GPT-5@Codex 子代理），其後被批次降級。⚠️ **本卡執行者須逐一列出那三輪的 findings，各自閉合或轉入本卡**，那是 #38 的解除條件；執行者本來就得讀那三輪才知道要建什麼。裁定全文見 issuecomment-5305463996;交付物本身須通過 WF-24-EVIDENCE-STRENGTH1（#11）的 (e) 與 (f)：凡寫下「必須／拒收／擋下／強制」等字眼，須指出執行者所在的檔與行，沒有機械執行者者一律寫成「約定」；凡宣稱「查不到／不存在」，須確認量測工具真的在量你以為的東西」→ 新值「handoff --next-stage review 產出派審詞骨架並貼上該 Issue，機械欄位（被審 SHA、基線、iteration、前輪 findings）由事件與卡面自動帶入，不由人手抄。；【放行判準 1／6】handoff --next-stage review 能從【同一次事件】產生派審詞——不是事後另跑一支讀別處的工具。⚠️ 現行 review_prompt.py 正是「另一支讀別處」而那個別處已封存，此條即為防止重演。；【放行判準 2／6】Issue-only 測試涵蓋完整鏈路 open → handoff → prompt → review → release。⚠️ 目前只有零星卡實測走過，而且靠 PM 手寫派審詞補洞，不構成涵蓋。；【放行判準 3／6】派審詞自動帶入 Issue body 的驗收／驗證／Gate 章節、source SHA、iteration 與【前輪 findings】。前輪 findings 這項尤其重要——手寫時最容易漏，而漏了會讓查核者重開已閉合的 finding。；【放行判準 4／6】cpbl-analytics 的 docs/ROADMAP.md:494 之 cancelled_with_report 條款改有新的 versioned 留存位置。⚠️ 現行條款要求「報告寫進 docs/tasks/<CARD_ID>.md（該檔開卡時已在 main）」，該前提在停止產生卡檔後不成立。；【放行判準 5／6】canonical 的「卡片一檔」、封存與索引契約同步改版。⚠️ 索引契約已實測漂移：cpbl-analytics 的 125 個 archive 檔中有 23 個沒有索引列。；【放行判準 6／6】所有 docs/tasks/ consumer 完成遷移或正式退役。已知四個：tests/test_task_card_sections.py（測試，略過已封存者）、scripts/review_prompt.py:120、scripts/state_plane_migrate.py:158（舊狀態面遷移工具、非新卡 consumer）、scripts/review_gate_inventory.py:52。⚠️ 此清單由 PM 調查、查核者複驗，但【未證明窮盡】。；⚠️【禁止項】在上述六條全部滿足前，不得停止產生 docs/tasks/ 卡檔、不得整批刪除既有 stub。後者已有實證反對：跨家族查核者逐檔對過 Issue，至少 8 檔含非 boilerplate、未逐字存在於 Issue body 的內容（DB 宣告、裁定紀錄、完整驗收條件）。」；理由 需求方 2026-08-17 裁定（issuecomment-5314430685）：本卡承接「review_prompt.py 已與新狀態面斷線」的根治，並把跨家族查核者給的六條放行判準入驗收。觸發是 cpbl-analytics 的 scripts/review_prompt.py 標著 LIFECYCLE: standing 且 AI_RUNBOOK:433 逐字給指令，卻讀已於 2026-08-04（8271d7c）封存唯讀的 events.jsonl——對 cutover 後的卡誤報「查無任何 handoff event」。缺口從 cutover 到 2026-08-17 無人發現，因為期間沒有人跑過它。cpbl 端已止血（6d18c0c）。。
- 2026-08-26T22:09:29+08:00 amend by wf-cli（op 2b93ed9d）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:e7f83ba7a9011af7fd28e1d9c9a3c4674a928cbd45e3463e688e11910816893c (704 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。
- 2026-08-27T18:59:24+08:00 amend by wf-cli（op b932354c）→ 驗收條件：原值指紋 sha256:cefa94c491ecf851afb12249d3c645e5c1c0fc99e0f067194b1c61709d2983b7 (2168 bytes) → 新值指紋 sha256:6c0d59721bc7a64bead95df8149543fc59df3ff09ca7130818fd046d9ef2c6bd (6442 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 PM 登記兩處前提失效（#38 已非進行中而是 Backlog；核心痛點三實例全在 08-12 而派審詞通道形狀已變：95 則全落在 08-10..08-21、之後為 0），並依需求方裁定把 aiwf#137 的射程併入本卡骨架為一個必含問句（⛔ 不做 schema 欄位、⛔ 不做否決權，依據與翻盤門檻逐條寫入）。
- 2026-08-29T14:59:08+08:00 handoff by wf-cli → owner 待指派；iteration 0；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 阻塞登記（來源狀態 📥Backlog）：https://github.com/ruan6047/ai-workflow/issues/66 之阻塞留言。解除條件＝待審清單機制上線。。


## Comment 5305463996 · 2026-08-16T03:09:46Z

## 需求方裁定：本卡承接 `#38` 的前瞻射程，但 `#38` 維持 OPEN（2026-08-16）

本卡驗收條件 4 逐字要求「與 `WF-DISPATCH-PRECHECK1`（`#38`）的關係須明確裁定：取代、互補、或兩者射程不同。**不得默默並存讓後人猜**」。以下為裁定。

### 裁定：本卡承接 `#38` 的**前瞻射程**，`#38` 維持 OPEN 至其既有 findings 結清

**不是單純的「取代」**，理由在下面第三節。

### 一、`#38` 驗收條件 1 的正解就是本卡

`#38` 逐字：

> 裁定基線 SHA 的正解落在哪一層，並說明為何不是範本層。PM 的判斷是：在範本裡寫「基線須以 merge-base 產出」與現在寫「基線：<40 碼 SHA>」的可靠度差別是零，因為兩者都要人手填、都沒有東西會擋。**正解是把值算出來**——`git_ops.is_ancestor` 已存在，只差一個 `merge_base()`，而 **`handoff_cmd.py` 的 `--repo-path` 分支已…**

**它自己指向了 `handoff_cmd.py`。** 那就是本卡。

### 二、⚠️ 但 `#38` 有第二件實質工作，**同源產生不蘊含它**

`#38` 驗收條件 2 的第 (1) 層：`templates/review-prompt.md` **把前輪閉環回報由散文升為必填小節（帶 `finding_id` 逐列）**，查核者收到即可自查缺節並自判 `review-invalid`。`#38` 自陳那是「本卡唯一今天可動且送達對象正確的一層」。

**`handoff` 產出骨架不會自動要求查核者逐項回報前輪 finding。** 若本卡只做機械欄位同源，那一層會靜默消失。

**故本次 amend 把它具名寫進本卡驗收條件。**

### 三、為什麼 `#38` 不能今天關掉

**`#38` 在 iteration 5，有 3 輪 `REQUEST_CHANGES` 的 findings 未閉合**（2026-08-12 三次，查核者皆為 GPT-5@Codex 子代理，收據雜湊皆已核），其後於 08-13 00:24 被批次降級拉回 Backlog。

**它不是一張沒開工的卡。** 直接關閉會讓那三輪的 findings 消失。

⚠️ PM 尚未讀那三輪的內容，**判不出它們是否隨射程移轉而失效**。在讀之前判「失效」就是本專案反覆在犯的那個錯（宣稱超過證據）。

**`#38` 的解除條件**：那三輪的 findings 逐一列出，各自閉合或轉入本卡。**該列舉工作交給本卡的執行者**——它本來就得讀那三輪才知道要建什麼。

### 四、並存是明示的，不是默認的

本裁定滿足驗收條件 4 的「不得默默並存」：**並存是明示的、有理由、有解除條件、且解除的執行者已指名。**


## Comment 5314430685 · 2026-08-17T09:44:50Z

## 需求方裁定 2026-08-17：本卡承接 `review_prompt.py` 已與新狀態面斷線；六條放行判準入驗收

⚠️ 本留言由 PM（Claude Fable 5@Claude Code）代擬代貼，內容為需求方裁定。

### 觸發

`cpbl-analytics` 的 `scripts/review_prompt.py` 標著 `LIFECYCLE: standing · 常設工具——這就是給你跑的；不要刪`，`docs/AI_RUNBOOK.md:433` 逐字給指令。**它讀 `docs/control-plane/events.jsonl`，而該檔已於 2026-08-04（`8271d7c`）宣告封存唯讀**；此後的 handoff 由 `wfcli` 寫進 GitHub Issue，不進那個檔。

實測（跨家族查核者複驗）：

- `ML-UMP2`（cutover 前）→ 正常運作，正確拒絕並給出分辨指引
- `WP-DISCLOSURE-SYNC1`、`OPS-SCHEDULE-FAILURE-BLIND1`（cutover 後）→ **誤報「尚未交付查核——查無任何 handoff event」**

⚠️ **那是工具讀錯地方，不是卡沒交付。** 這個缺口從 cutover 到 2026-08-17 無人發現——因為期間沒有人跑過它。PM 於 2026-08-16 手寫了七份派審詞，**一次都沒跑它，而它自己沒察覺這件事有問題**。

cpbl 端已止血（`6d18c0c`：`AI_RUNBOOK` 標記僅服務 cutover 前的卡）。**根治歸本卡**——查核者指出本卡的核心痛點「handoff 與手寫派審詞雙來源必然漂移」正是這件事。

### 入驗收的六條放行判準

查核者給的，需求方採認。**「停止產生卡檔」在這六條全部滿足前不得執行**：

1. `handoff --next-stage review` 能從**同一次事件**產生派審詞
2. Issue-only 測試涵蓋 `open → handoff → prompt → review → release`
3. 派審詞自動帶入 Issue body 的驗收／驗證／Gate、`source SHA`、`iteration` 與**前輪 findings**
4. `cpbl-analytics` `docs/ROADMAP.md:494` 的 `cancelled_with_report` 改有新的 versioned 留存位置
5. canonical 的「卡片一檔」、封存與索引契約同步改版
6. 所有 `docs/tasks/` consumer 完成遷移或正式退役

### ⚠️ 已知的 consumer（四個，供第 6 條使用）

| consumer | LIFECYCLE | archive fallback |
|---|---|---|
| `tests/test_task_card_sections.py` | （測試） | 略過已封存者 |
| `scripts/review_prompt.py:120` | `standing` | 有 |
| `scripts/state_plane_migrate.py:158` | `ci_guard` | 有（但那是**舊狀態面遷移工具**，非新卡 consumer） |
| `scripts/review_gate_inventory.py:52` | `standing` | 有 |

### ⚠️ 併同記載的事實（PM 調查，查核者複驗後更正）

- `docs/tasks/` **仍在長**：以 cutover commit `8271d7c` 為 ancestry 邊界，其後新增 **29 檔、47 個相關 commits**，作者皆為 `ruan`。⚠️ PM 原報「24 檔」使用 `--since=2026-08-05`，而 Git 對省略時間的日期依**執行當下時間**解析、結果會漂移——查核者指出後改用穩定邊界。
- **不得整批刪除那些 stub**：查核者逐檔對過 Issue，**至少 8 檔含非 boilerplate、未逐字存在於 Issue body 的內容**（DB 宣告、裁定紀錄、完整驗收條件）。
- 封存索引契約已漂移：`docs/archive/TASKS_ARCHIVE.md` 自 cutover 後未再更新，**125 個 archive 檔中 23 個沒有索引列**。此項屬 `#94` 射程。


## Comment 5460928479 · 2026-08-29T06:55:51Z

## 阻塞登記

**狀態**：⏸阻塞。**來源狀態：📥Backlog**（解除時回到此狀態）。

**阻塞原因**：需求方於 2026-08-29 決定，在階段狀態重整（8 階段 × 10 狀態、待審清單、CLI 射程收斂）定案並落地前，暫停所有 ai-workflow 流程卡，避免它們與重構討論互相干擾。

**可證偽的解除條件**：待審清單機制上線（label ＋ issue template ＋ 可見分組）。屆時本卡改列為清單參考項，或依當時前提是否仍成立重新排程。

**本次未做**：核心痛點、驗收條件、射程一律未動。`iteration` 未遞增。`階段` 欄未寫入。本登記僅改交付狀態與 owner。

**已知的射程重疊**（供解除時參考，非本次裁定）：#66／#38 的實質可能由「七份交接文件格式」承接；#128 可能由「待審清單收件條件三·查重留痕」＋`open --from-issue` 承接；#11 的證據紀律已部分寫入 PM 準則但痛點（靠人記得）未消失。⛔ 上述皆未經裁定，解除時須逐張重驗。

**裁定者**：需求方 ruan6047，2026-08-29 本 session 對話中指示「把目前所有 WF 卡片暫停，避免干擾目前重構討論」。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

