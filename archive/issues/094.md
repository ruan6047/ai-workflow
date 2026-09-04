# #94 WF-REVIEW-INVALID-TRACE1 review-invalid 被機械偵測到卻不留痕：拒收只印 stderr、Log 一行都沒有
- state: closed  created: 2026-08-16T14:44:37Z  closed: 2026-08-17T12:53:32Z
- url: https://github.com/ruan6047/ai-workflow/issues/94
- comments: 5

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；接線本身不難（card.append_log_line 就在 card.py:439），但要判斷的東西不小：review-invalid 依 §1 不計 iteration、不建立 attempt、不改卡片狀態，所以它寫的必須是一個「有留痕但不影響任何計數」的事件——寫錯會污染 escalation 帳。另須決定拒收時是否同時在 Issue 留言（讓查核者看得到自己被拒與原因），以及重複拒收要不要去重。經濟型容易直接複製 review 事件的寫法而讓它意外計入 attempt。）　查核：待指派（建議 主力型；唯讀留痕的補強，但錯了會直接污染 escalation 計數這條治理骨幹。查核重點在【新事件是否真的不計入任何計數】——須實測連續多次拒收後 iteration、attempt、escalation 三者皆不動；以及【新事件會不會反過來變成一個沒有讀者的欄位】，本 repo 近期反覆踩到的正是這族。跨家族非必要。）
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：留痕要能回答『這張卡卡在哪一關』。目前 Log 只記得住成功的路徑，失敗與阻塞路徑一律沉默，於是流程健康度無法從狀態面讀出來，只能靠人記得。

## 簡介
<!-- card-brief:begin -->
用可重跑的 scripts/contract_tool_reconcile.py 窮舉 canonical AI_WORKFLOW.md、templates/*.md、docs/ROADMAP.md 命名的每一個事件型別／交付狀態／卡面欄位，機械標出有無寫入者與讀取者及命中行號，把「契約宣告了但 wfcli 沒實作」的缺口從撞出來變成掃出來。**適用時機**：要確認某個事件型別或卡面欄位到底有沒有寫入者；或想從狀態面讀出「這張卡卡在哪一關」而 Log 只記得住成功路徑時。⛔ 非射程：對帳先於修補，本卡不補 docs/CONTRACT_TOOL_RECONCILE.md 登記的任何一處——交付後 review-invalid、preflight-failed、⏸阻塞 仍無寫入者；--check 守的是缺口登記漂移不是缺口清償，52 個缺口全未處置它仍 exit 0。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：契約文件宣告了一批事件型別／交付狀態／卡面欄位，而寫入通道（wfcli）只實作了一部分，兩者從來沒有對過帳——於是缺口是【撞出來的，不是找出來的】。2026-08-16 一天內踩到五個，全部靠實際操作失敗才發現：(1) review-invalid 被 templates/review-escalation.md §1 的表格列在「結果／事件」欄，而 review_cmd.py:216-221 偵測到之後只 print 到 stderr 然後 return 4，沒有事件、沒有留言、Log 一行都沒有；(2) preflight-failed 在 cli/src 只出現在 review.py:627 的註解，無寫入者；(3) status-change → ⏸阻塞 沒有專責動詞，⏸阻塞 雖在 project.py:41 的狀態表裡但 amend_cmd.py:351 明寫「轉 ⏸阻塞 是 lifecycle 決定……不由一個 [amend] 決定」；(4) amend --resources 不跑資源互斥檢查，amend_cmd.py 只 import parse_block／render_block，全 repo 僅 assign_cmd.py:127 呼叫 find_conflicts，後果是先 assign 小射程再 amend 擴大即可繞過派工閘門建立的不變量（原 #92 的核心痛點，逐字保留於此，不得因併卡而遺失）；(5) 卡面「需求：」欄為 — 的卡永遠無法 amend --core-pain，而 amend 沒有任何旗標能設該欄位（#62 於 2026-08-16 實測，該卡的威脅模型因此只能寫在留言與碼裡、進不了卡面）。§1 的五個層次裡機器只寫得出兩個（APPROVE／REQUEST_CHANGES 與 review-marker-clearance），而 card.append_log_line() 就在 card.py:439——不是做不到，是沒接。⚠️ 後果不是漏幾筆流水帳：【「卡沒往前走」這件事在工具帳上不可見】。看板與 Log 只記錄成功的那條路，於是一張卡可以被反覆拒收而完全沒有訊號，也無法回答「這張卡到底卡在哪一關」。2026-08-16 的 #57 就是活例——分支已合併進 main（PR #93、d18cd83），而卡上看不到任何查核或合併紀錄，只有 PM 自己寫的自陳留言。【射程，需求方 2026-08-16 裁定 issuecomment-5311397884】窮舉契約文件（canonical AI_WORKFLOW.md、templates/*.md、docs/ROADMAP.md）命名的每一個事件型別／交付狀態／卡面欄位，機械檢查它有沒有寫入者與讀取者，產出對帳表。⚠️【對帳先於修補】本卡的第一交付物是那張表，不是任何一處的修法——先知道有幾個洞，再決定補哪些、哪些寫成已知限制。⚠️ 本卡取代 #92 與 #95，並須把還沒踩到的那些一次找出來，而不是繼續等著踩。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:scripts/contract_tool_reconcile.py",
    "file:cli/tests/test_contract_tool_reconcile.py",
    "file:docs/CONTRACT_TOOL_RECONCILE.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 產出契約↔工具對帳表：窮舉 canonical AI_WORKFLOW.md、templates/*.md、docs/ROADMAP.md 命名的每一個事件型別／交付狀態／卡面欄位，逐項標明有無寫入者、有無讀取者、以及命中的檔案與行號。⚠️ 窮舉須可重跑，不得是人工清單——那正是本卡要消滅的形狀。
- [ ] 五個已知實例必須全部出現在表中且判定正確（review-invalid、preflight-failed、⏸阻塞、amend 不跑 find_conflicts、需求欄為 — 時無法 amend）。⚠️ 這是對帳器的正控組：五個都在才證明它在量東西。
- [ ] ⚠️ 對帳結果須含「本次新發現、先前未踩到」的條目。若一個都沒有，須說明對帳範圍為何等於已知集合——那通常表示窮舉不完整。
- [ ] 每個缺口逐項給處置建議（補寫入者／補讀取者／改寫成已知限制／從契約移除），但【本卡不實作任何一項修補】。修補由需求方依對帳表決定要不要開卡、開幾張。
- [ ] ⚠️ 對帳器本身不得成為新的人維護清單：契約側的 universe 必須由掃描文件導出，不得由人登記；漏掃一項的後果必須是可見失敗而非靜默通過。此點須有變異檢驗。

## 驗證

- [ ] 以五個已知實例作正控組逐一驗證對帳器：review-invalid、preflight-failed、⏸阻塞、amend 到不了 find_conflicts、需求欄 amend 改不動。五個都在表中且判定正確才算對帳器在量東西。
- [ ] 變異檢驗：讓契約側 universe 改由人登記 → 對應測試轉紅（驗收條 5 的主檢）；把 print() 引數也算 writer → 正控組 1 轉紅；呼叫圖恢復同名全集退路 → 正控組 4 轉紅。
- [ ] 對帳器兩次執行輸出逐位相同（不含時戳）；--check 對三個漂移方向（出現未登記缺口／登記了已不存在的缺口／同一符號判定變了）皆會紅。⚠️ 明確不涵蓋：--check【不】因缺口長期未處置而紅——它守的是缺口登記漂移不是缺口清償（查核者 2026-08-17 明確裁定），實測 52 個缺口全未處置時 --check 仍為 exit 0。
- [ ] ⚠️ 本卡不驗證『留痕能回答這張卡卡在哪一關』——那是服務的原始目標，而本卡射程為對帳先於修補、明訂不實作任何修補。交付後 review-invalid／preflight-failed／⏸阻塞 仍無寫入者，該目標一分未進。此限度須逐字寫進交付物，不得以『已對帳』暗示已改善。
## Log

- 2026-08-16T22:44:36+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-17T11:23:56+08:00 amend by wf-cli（op b307203c）→ 核心痛點：原值「templates/review-escalation.md §1 的表格把 review-invalid 列在「結果／事件」欄——契約說它是事件。但 cli/src/wf_cli/commands/review_cmd.py:216-221 偵測到之後只 print 到 stderr 然後 return 4：沒有事件、沒有留言、Log 一行都沒有。⚠️ 已實現的後果：2026-08-16 WF-WORKTREE-REPO-OWNERSHIP1（#57）的跨家族 APPROVE 因缺 self_run 被拒收，該次拒收在卡上完全不存在——卡的 Log 最後一筆是 12:40:13 的 amend，交付狀態仍是 🔍待查核 iteration 5，而分支其實已經合併進 main（PR #93、d18cd83）。任何人事後看這張卡，看不到「有一份裁決來過而且被拒了」。⚠️ 這不是漏一筆流水帳：它使「卡沒往前走」這件事在工具帳上不可見。看板與 Log 只記錄成功的那條路，於是一張卡可以被反覆拒收而完全沒有訊號，也無法回答「這張卡到底卡在哪一關」。機制就在手邊未接：card.append_log_line() 在 card.py:439。⚠️ 【同族但不在本卡射程，須另裁是否開卡】§1 的五個層次裡另有兩個同樣沒有寫入者，且比 review-invalid 更難——它們連機械偵測都沒有：(1) preflight-failed 在 cli/src 只出現在 review.py:627 的註解；(2) status-change → ⏸阻塞 沒有專責動詞，⏸阻塞 雖在 project.py:41 的狀態表裡，但 amend_cmd.py:351 明寫「轉 ⏸阻塞 是 lifecycle 決定……不由一個 [amend] 決定」。五個層次機器只寫得出兩個（實質查核的 APPROVE/REQUEST_CHANGES 與 review-marker-clearance）。本卡刻意只處理已被機械偵測、卻沒有寫入的那一個——那兩個要的是新偵測＋新動詞，屬不同工程量級。此段記在這裡是為了不讓它被遺忘，不是承諾。」→ 新值「契約文件宣告了一批事件型別／交付狀態／卡面欄位，而寫入通道（wfcli）只實作了一部分，兩者從來沒有對過帳——於是缺口是【撞出來的，不是找出來的】。2026-08-16 一天內踩到五個，全部靠實際操作失敗才發現：(1) review-invalid 被 templates/review-escalation.md §1 的表格列在「結果／事件」欄，而 review_cmd.py:216-221 偵測到之後只 print 到 stderr 然後 return 4，沒有事件、沒有留言、Log 一行都沒有；(2) preflight-failed 在 cli/src 只出現在 review.py:627 的註解，無寫入者；(3) status-change → ⏸阻塞 沒有專責動詞，⏸阻塞 雖在 project.py:41 的狀態表裡但 amend_cmd.py:351 明寫「轉 ⏸阻塞 是 lifecycle 決定……不由一個 [amend] 決定」；(4) amend --resources 不跑資源互斥檢查，amend_cmd.py 只 import parse_block／render_block，全 repo 僅 assign_cmd.py:127 呼叫 find_conflicts，後果是先 assign 小射程再 amend 擴大即可繞過派工閘門建立的不變量（原 #92 的核心痛點，逐字保留於此，不得因併卡而遺失）；(5) 卡面「需求：」欄為 — 的卡永遠無法 amend --core-pain，而 amend 沒有任何旗標能設該欄位（#62 於 2026-08-16 實測，該卡的威脅模型因此只能寫在留言與碼裡、進不了卡面）。§1 的五個層次裡機器只寫得出兩個（APPROVE／REQUEST_CHANGES 與 review-marker-clearance），而 card.append_log_line() 就在 card.py:439——不是做不到，是沒接。⚠️ 後果不是漏幾筆流水帳：【「卡沒往前走」這件事在工具帳上不可見】。看板與 Log 只記錄成功的那條路，於是一張卡可以被反覆拒收而完全沒有訊號，也無法回答「這張卡到底卡在哪一關」。2026-08-16 的 #57 就是活例——分支已合併進 main（PR #93、d18cd83），而卡上看不到任何查核或合併紀錄，只有 PM 自己寫的自陳留言。【射程，需求方 2026-08-16 裁定 issuecomment-5311397884】窮舉契約文件（canonical AI_WORKFLOW.md、templates/*.md、docs/ROADMAP.md）命名的每一個事件型別／交付狀態／卡面欄位，機械檢查它有沒有寫入者與讀取者，產出對帳表。⚠️【對帳先於修補】本卡的第一交付物是那張表，不是任何一處的修法——先知道有幾個洞，再決定補哪些、哪些寫成已知限制。⚠️ 本卡取代 #92 與 #95，並須把還沒踩到的那些一次找出來，而不是繼續等著踩。」；理由 需求方 2026-08-16 裁定本卡改為家族卡。原因：#92／#94／#95 是同一個根因（契約宣告了、寫入通道沒實作、從未對過帳）被 PM 開成三張卡，正是 PM 整天在打三個執行者的「修實例不修形狀」。今日踩到的五個實例全部是撞出來的不是找出來的，故射程改為全量對帳、對帳先於修補。#92 併入本卡（其核心痛點逐字保留為對帳表已知條目），#95 關閉。；授權 依需求方 ruan6047 於 https://github.com/ruan6047/ai-workflow/issues/94#issuecomment-5311397884 的裁定（GitHub comment author 已逐字核對，非留言內文自述）。
- 2026-08-17T11:24:47+08:00 amend by wf-cli（op c4eb8ccc）→ 驗收條件：原值「[ ] review 拒收（review-invalid）時在卡的 Log 留下一筆事件，內容至少含：被審 SHA、reviewer、拒收理由（機械判定的那條）、時間戳。⚠️ 該事件不得改變交付狀態、不得增加 iteration、不得建立 attempt、不得計入 escalation——依 §1 表格逐格對照。；[ ] 以實測證明上一條的『不得』全部成立：連續拒收 N 次後，iteration、attempt 計數、escalation 額度三者的值與拒收前逐位相同。不得只以單元測試斷言，須跑真實或高擬真的完整路徑。；[ ] 裁定並實作『查核者看不看得到自己被拒』：目前拒收只印在 PM 的 stderr，跨家族查核者沒有 wfcli 也讀不到。若決定不在 Issue 留言，須寫明理由與替代通知路徑，不得預設沉默。；[ ] ⚠️ 新事件不得成為沒有讀者的欄位。須指出至少一個實際會讀它的消費者（doctor、snapshot、或看板投影），並證明它讀得到。若當下沒有消費者，本卡須明說這是半條線並提出承接卡，不得以『之後會有人讀』收尾。」→ 新值「產出契約↔工具對帳表：窮舉 canonical AI_WORKFLOW.md、templates/*.md、docs/ROADMAP.md 命名的每一個事件型別／交付狀態／卡面欄位，逐項標明有無寫入者、有無讀取者、以及命中的檔案與行號。⚠️ 窮舉須可重跑，不得是人工清單——那正是本卡要消滅的形狀。；五個已知實例必須全部出現在表中且判定正確（review-invalid、preflight-failed、⏸阻塞、amend 不跑 find_conflicts、需求欄為 — 時無法 amend）。⚠️ 這是對帳器的正控組：五個都在才證明它在量東西。；⚠️ 對帳結果須含「本次新發現、先前未踩到」的條目。若一個都沒有，須說明對帳範圍為何等於已知集合——那通常表示窮舉不完整。；每個缺口逐項給處置建議（補寫入者／補讀取者／改寫成已知限制／從契約移除），但【本卡不實作任何一項修補】。修補由需求方依對帳表決定要不要開卡、開幾張。；⚠️ 對帳器本身不得成為新的人維護清單：契約側的 universe 必須由掃描文件導出，不得由人登記；漏掃一項的後果必須是可見失敗而非靜默通過。此點須有變異檢驗。」；理由 配合核心痛點改為家族卡（對帳先於修補）同步改寫驗收條件：第一交付物是對帳表而非任何修法。。
- 2026-08-17T18:42:33+08:00 amend by wf-cli（op 0325d700）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/commands/review_cmd.py", "file:cli/tests/test_review.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:scripts/contract_tool_reconcile.py、file:cli/tests/test_contract_tool_reconcile.py、file:docs/CONTRACT_TOOL_RECONCILE.md」；理由 需求方 2026-08-16 已把本卡由「補 review-invalid 的留痕」改為家族卡「契約↔工具全量對帳」（op 見 Log），但資源宣告仍停在原窄射程（review_cmd.py／test_review.py）。本卡第一交付物是【對帳表】不是任何修法，故寫入集應為對帳器與其輸出，不含被對帳的碼。原兩檔移出：本卡明訂不實作任何修補，不會動 review_cmd.py。⚠️ 路徑依 repo 現有慣例（scripts/replay_escalation_rules.py 為既有先例、測試在 cli/tests/、文件在 docs/）；執行者若判斷別的落點更好，回報理由由 PM amend，不得逕自逸出宣告。。
- 2026-08-17T18:43:23+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree claude/WF-REVIEW-INVALID-TRACE1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-review-invalid-trace1；交付狀態 🚧進行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-17T20:14:58+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex）；iteration 0；SHA 01fb578a8a1fa7a2bb8922f3183f48ec5cb95e58；證據 家族卡首輪交付：契約↔工具全量對帳表。第一交付物是表不是修法（卡面明訂本卡不實作任何修補）。執行者自量：基準 origin/main d0008b3288a2df9541f03cff7784693f6a429095、commit 後樹乾淨（git status --short 空）、1009 passed（基準 976，新增 33）。寫入集三檔與宣告完全一致未逸出。【對帳結果】79 個契約側符號、52 個符號缺口、3 個守衛覆蓋缺口；universe 由三條語法規則掃文件導出（反引號 kebab token／emoji＋token／範本標頭條列與章節標題），工具側判定走 AST＋tokenize、呼叫圖節點為「模組.函式」。【五個正控組全部命中且判定正確】review-invalid→mention-only writer 0；preflight-failed→mention-only 相關動詞無；⏸阻塞→read-only／Project 選項是／專責動詞否，status-change→absent；amend_cmd.py import render_block 卻到不了 find_conflicts→守衛覆蓋缺口；需求→open 渲染是／amend 可改否（amend 讀它當判準卻改不動它）。【新發現】狀態無專責動詞另有 5 個（⏳待執行、💡需求、🔨執行中、🚨已升級、📦已合併）——🚨已升級 是 canonical §5 著墨最多的轉換卻無專責寫入者；⚠️ assign --status 是自由文字旗標（無 choices），可繞過契約所有前提直接把卡推到 🚨已升級／📦已合併；卡面欄位開卡後改不動另有 5 個（規劃、執行、查核、DB、服務的原始目標），其中規劃與需求同樣被讀作授權判準；19 個卡面欄位工具完全不渲染，initiative-card.md 與 bug-card.md 的卡面在工具側整份不存在；事件無 writer 另有 6 項（escalation-epoch-change 碼裡自陳未實作、handoff-accepted 為 event-verified preflight 不可達的根因、review-correction、review-marker-clearance、baseline-change-request、四個 clearance 分類）；另立「命名漂移」族（escalation-checkpoint／contract-baseline 動詞存在只是不吐契約字面，與「連動詞都沒有」不同，不分開就是過度宣稱）；守衛覆蓋新發現 card.py→open 路徑渲染資源宣告卻不做互斥比對。【變異檢驗四條實跑，基準 33 passed】M1 universe 改人登記清單→15 failed 含驗收條 5 主檢；M2 print() 引數也算 writer→3 failed 含正控組 1；M3 呼叫圖恢復同名全集退路→2 failed 含正控組 4；M4 刪掉一列處置登記→--check exit 1。⭐ M3 順帶抓到一個真的洞：正控組 4 消失時 --check 仍綠（第一版只把符號列納入 ratchet），已修為 guard/<入口>→<模組> 一併登記並補 test_guard_gaps_are_covered_by_check——執行者明說「這一項是變異檢驗自己找出來的，不是設計時想到的」。⚠️ 執行者主動回報自己兩個錯：(1) 欄位名字元類把 \s 排掉，spec 基線 與 Merge SHA 靜默不進表——正是本卡要消滅的形狀，逐列核對時才發現；(2) 備註原寫「沒有任何動詞轉得進去」為過度宣稱（assign --status 無 choices 實際寫得進去），已改為「沒有專責動詞」並加 ungated_status_flags 機械列出逃生口。⚠️ 執行者自陳八項不確定，重點：assign_cmd.py→card 那列守衛缺口很可能是偽陽性（配對是模組粒度）已標「候選需人判」；📦已合併 實務上怎麼被設定的工具帳上分不出來（assign --status？看板 UI？後者即違反唯一寫入通道紅線，需求方裁定）；呼叫圖解析不到就不連邊，方向是多報缺口但少數 absent／mention-only 可能是解析失敗；事件只有字面軸（狀態另有資料驅動軸），若某事件型別由變數組出後寫入會漏判；card_field 的 目標／需求方／範圍／Log 判為短標籤跨脈絡碰撞（過抽）但未逐個驗證；§7 的表是快照無機器守衛，--check 只守缺口集合；emoji 字元類用固定 Unicode 區段，區段外會漏；卡面「驗證」欄仍停在改版前的窄射程（卡面自身不一致，執行者未動）。⚠️ PM 記事：PM 於派工後、交付前在 issuecomment-5315518506 預先登記一個可證偽預測（對帳表應找到「source SHA 的存在性驗證是選填或不存在」），實測【未命中】——但查證後認定該條不在工具宣告的兩軸內（非符號、非「入口→資料模組」配對，而是「旗標是選填的」），故為 PM 把預測寫錯形狀而非驗收條 3 的反例；已於 issuecomment-5315879091 照實記載。該事留下一個請查核者裁定的問題：「契約要求 X 而驗證 X 的機制是選填或不存在」這一族與表上其他條目同源卻落在兩軸之外，該擴軸還是該在文件明寫此類不在射程。。
- 2026-08-17T20:55:28+08:00 amend by wf-cli（op 2a3767e0）→ 驗證：原值「[ ] 以 #57 於 2026-08-16 的真實拒收情境重放一次，確認新版會留痕，且留痕內容足以讓事後讀卡的人知道『有一份裁決來過、被拒、原因是什麼』。；[ ] 變異檢驗：拿掉留痕寫入 → 對應測試轉紅；把新事件誤接成會增加 iteration 或 attempt → 對應測試轉紅。；[ ] 回歸：既有 review 測試全綠；正常 APPROVE／REQUEST_CHANGES 路徑的事件內容與計數不受影響。」→ 新值「以五個已知實例作正控組逐一驗證對帳器：review-invalid、preflight-failed、⏸阻塞、amend 到不了 find_conflicts、需求欄 amend 改不動。五個都在表中且判定正確才算對帳器在量東西。；變異檢驗：讓契約側 universe 改由人登記 → 對應測試轉紅（驗收條 5 的主檢）；把 print() 引數也算 writer → 正控組 1 轉紅；呼叫圖恢復同名全集退路 → 正控組 4 轉紅。；對帳器兩次執行輸出逐位相同（不含時戳）；--check 對三個漂移方向（出現未登記缺口／登記了已不存在的缺口／同一符號判定變了）皆會紅。⚠️ 明確不涵蓋：--check【不】因缺口長期未處置而紅——它守的是缺口登記漂移不是缺口清償（查核者 2026-08-17 明確裁定），實測 52 個缺口全未處置時 --check 仍為 exit 0。；⚠️ 本卡不驗證『留痕能回答這張卡卡在哪一關』——那是服務的原始目標，而本卡射程為對帳先於修補、明訂不實作任何修補。交付後 review-invalid／preflight-failed／⏸阻塞 仍無寫入者，該目標一分未進。此限度須逐字寫進交付物，不得以『已對帳』暗示已改善。」；理由 跨家族查核 2026-08-17（issuecomment-5316277478）第三條裁定：卡面驗證欄與射程說明的同步責任在 planner/PM 而不在 source branch。本欄仍停在 2026-08-16 改版【之前】的窄射程（補 review-invalid 的留痕），而該日需求方已把本卡改為家族卡「契約↔工具全量對帳」並明訂不實作任何修補——三條驗證全部對應一個不存在的交付物。此為 PM 開卡後 amend 核心痛點與驗收條件時漏改驗證欄所致，非執行者責任。本次改為與現行射程一致。。
- 2026-08-17T20:57:54+08:00 handoff by wf-cli → owner —；iteration 0；SHA 01fb578a8a1fa7a2bb8922f3183f48ec5cb95e58；證據 結案。PR #97 squash merge → ai-workflow main 6561e04，CI 兩個 check 皆 SUCCESS。merge 後於 main 驗證 pytest 1009 passed。查核 GPT-5@Codex issuecomment-5316277478：core_pain_resolved yes、APPROVE，並明確裁定三件事：(1) assign --status 的繞過形狀成立且【比一般表列缺口更重】；(2) --check 守的是缺口登記漂移【不是缺口清償】；(3) 卡面驗證欄與射程說明的同步責任在 planner/PM 而不在 source branch。⚠️ 第 3 條 PM 已執行（op 2a3767e0）：驗證欄原文仍停在 2026-08-16 改版【之前】的窄射程，三條驗證全部對應一個不存在的交付物——那是 PM 當時 amend 核心痛點與驗收條件卻漏改驗證欄所致、非執行者責任；已改為與現行射程一致並新增第四條明確記載本卡【不】驗證服務的原始目標。【交付】79 個契約側符號、52 個符號缺口、3 個守衛覆蓋缺口；五個正控組全數命中；新發現含 assign --status 自由文字旗標、狀態無專責動詞另 5 個（🚨已升級 是 canonical §5 著墨最多的轉換卻無專責寫入者）、卡面欄位開卡後改不動另 5 個、19 個卡面欄位工具完全不渲染、事件無 writer 另 6 項（含 handoff-accepted 為 event-verified preflight 不可達的根因）。變異檢驗四條，M3 順帶抓到一個真的洞（正控組 4 消失時 --check 仍綠），執行者明說那是變異檢驗自己找出來的、不是設計時想到的。執行者主動回報自己兩個錯：欄位名字元類把 \s 排掉使 spec 基線 與 Merge SHA 靜默不進表（正是本卡要消滅的形狀）、以及「沒有任何動詞轉得進去」為過度宣稱（已改為「沒有專責動詞」並加 ungated_status_flags）。⚠️⚠️【本卡明確未達成的】服務的原始目標「留痕要能回答這張卡卡在哪一關」【一分未進】——交付後 review-invalid／preflight-failed／⏸阻塞 仍無寫入者。那是需求方裁定的射程（對帳先於修補）不是疏漏，但須記明：52 個缺口的承接點是「需求方依對帳表決定要不要開卡」，而 PM 實測 --check 在 52 個缺口全未處置時仍為 exit 0——【沒有任何機械的東西會讓它們再被看見】。⚠️ PM 自審記事：本卡派審詞歷四版，前三版把 core_pain_resolved 只寫在 schema 當格式要求而【沒有問它】，第一判準是需求方提醒後才補上。清理已完成：worktree 已移除（內容僅 scripts/__pycache__/，已依 canonical 檢查確認非工作內容）、本地分支已刪（was 01fb578）、遠端分支已刪，git worktree list 對本卡 0 命中。；收尾清理：worktree、本地分支、遠端分支 本來就不存在。
- 2026-08-26T22:22:30+08:00 amend by wf-cli（op 52b0a353）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:e2a183eab5f082996194d2a85a245988cb129d2b4d206030f61f938026b996b0 (779 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5311397884 · 2026-08-17T03:22:23Z

## 需求方裁定 2026-08-16：本卡改為家族卡——契約↔工具全量對帳；#92、#95 關閉

⚠️ 本留言由 PM（Claude Fable 5@Claude Code）代擬代貼，內容為需求方裁定。

### 為什麼改

2026-08-16 一天內 PM 開了 8 張卡、關 1 張，其中**六張是執行既有卡時撞出來的**，不是規劃出來的。而 `#92`（`amend` 不跑互斥檢查）、`#94`（`review-invalid` 不留痕）、`#95`（schema 無法表達合併適用性）**根本是同一個病**：**契約文件宣告了一堆東西，寫入通道只實作了一部分，而從來沒有人對過帳。**

⚠️ **PM 把同一個根因開成三張卡，正是它整天在打三個執行者的那件事——修實例不修形狀。**

今天踩到的五個實例全部是**撞出來的、不是找出來的**：

- `review-invalid` 被 §1 列在「結果／事件」欄，`review_cmd.py:216-221` 只 `print` 到 stderr 然後 `return 4`，Log 一行都沒有
- `preflight-failed` 在 `cli/src` 只出現在 `review.py:627` 的註解
- `status-change` → `⏸阻塞` 沒有專責動詞；`⏸阻塞` 在 `project.py:41` 的狀態表裡，但 `amend_cmd.py:351` 明寫「轉 ⏸阻塞 是 lifecycle 決定……不由一個 [amend] 決定」
- `amend --resources` 不跑 `find_conflicts`（全 repo 僅 `assign_cmd.py:127` 呼叫）
- 卡面 `需求：—` 的卡**永遠無法** `amend --core-pain`，而 `amend` 沒有任何旗標能設那個欄位（`#62` 實測）

**五個層次的事件型別，機器只寫得出兩個**（`APPROVE`／`REQUEST_CHANGES` 與 `review-marker-clearance`）。而 `card.append_log_line()` 就在 `card.py:439`——不是做不到，是沒接。

### 因此

本卡射程由「補 `review-invalid` 的留痕」擴為**契約↔工具全量對帳**：窮舉契約文件（canonical `AI_WORKFLOW.md`、`templates/*.md`、`docs/ROADMAP.md`）命名的每一個**事件型別／交付狀態／卡面欄位**，機械檢查它有沒有**寫入者**與**讀取者**，產出對帳表。

⚠️ **對帳先於修補**。本卡的第一交付物是那張表，不是任何一處的修法。先知道有幾個洞，再決定補哪些、哪些寫成已知限制。

⚠️ **這一張同時退掉 `#92` 與 `#95`**，並且把**還沒踩到的**那些一次找出來，而不是繼續等著踩。

### `#92`、`#95` 的處置

- **`#92 WF-AMEND-RESOURCE-CONFLICT1`** → 關閉，併入本卡。其核心痛點（`amend` 可事後擴大宣告、繞過 `assign` 建立的不變量）逐字保留為本卡對帳表的**已知條目之一**，不得因併卡而遺失。
- **`#95 WF-REVIEW-MERGE-SUITABILITY1`** → 關閉。它服務的不是 ROADMAP 的兩個目標（可稽核／防低級事故），而是讓某一類一年可能出現一次的查核意見記得進去。⚠️ 需求方裁定：**不值得為它改查核契約的第一判準**。`#57` 的處置（丙案：不當查核記）已證明那類意見有可用的落點。


## Comment 5315513884 · 2026-08-17T11:36:42Z

## ⚠️ 預先登記一個可證偽預測（對帳器的窮舉性檢驗）

**時間**：2026-08-17，執行者已派工、對帳表尚未交付。

PM 今日在別的卡上實測到一個缺口，**刻意不告訴執行者**——因為對帳表若真的窮舉，它應該自己找得到。**這則留言是為了讓「PM 早就知道」不能事後宣稱。**

### 預測

對帳表應該找到這一條：

> **契約要求  為完整 40 字元 hex，而寫入通道對它的存在性驗證是不完整的。**
>
> -  的存在性驗證靠 ，而該旗標是**選填**（）——省略即無驗證
> -  **完全沒有 **，亦即沒有任何存在性驗證
> - 格式驗證擋不住：一個編造的 40 字元 hex **格式完全合法**

### 已實現的傷害（供對帳表引用，但不要靠它才找到）

PM 於 2026-08-16／17 共**四次**在  上捏造 （把短 SHA 補成不存在的 40 字元）。四次皆被  擋下——**因為那四次剛好都帶了該旗標**。⚠️ 而更早有一次 PM 省略該旗標，**編造的 SHA 真的寫進了  的 release 事件**，事後才以更正事件補救。

### 判定規則

- **對帳表含此條** → 窮舉性得到一次真實驗證
- **對帳表不含此條** → 那是驗收條 3（「須含本次新發現」）與驗收條 1（窮舉須可重跑）的**具體反例**，不是小疏漏——請執行者說明它的掃描為何看不見「契約要求 X、而驗證 X 的機制是選填或不存在」這一類

⚠️ **此則不構成派工變更**，執行者不必為它調整方向；它只是把一個本來就該被掃到的東西先寫在紙上。

## Comment 5315518506 · 2026-08-17T11:37:12Z

## ⚠️ 更正上一則：反引號被 shell 吃掉，內容殘缺

`issuecomment-5315513884` 的技術詞被 zsh 當成命令替換執行掉了（PM 用 heredoc 時未加引號界定符）。以下是完整版，**時間仍以那一則為準（2026-08-17，執行者已派工、對帳表尚未交付）**。

---

## 預先登記一個可證偽預測（對帳器的窮舉性檢驗）

PM 今日在別的卡上實測到一個缺口，**刻意不告訴執行者**——因為對帳表若真的窮舉，它應該自己找得到。**這則留言是為了讓「PM 早就知道」不能事後宣稱。**

### 預測

對帳表應該找到這一條：

> **契約要求 `source SHA` 為完整 40 字元 hex，而寫入通道對它的存在性驗證是不完整的。**
>
> - `handoff --source-sha` 的存在性驗證靠 `--repo-path`，而該旗標是**選填**（help 顯示為 `[--repo-path REPO_PATH]`）——省略即無驗證
> - `review --source-sha` **完全沒有 `--repo-path`**，亦即沒有任何存在性驗證
> - 格式驗證擋不住：一個編造的 40 字元 hex **格式完全合法**

### 已實現的傷害（供對帳表引用，但不要靠它才找到）

PM 於 2026-08-16／17 共**四次**在 `handoff` 上捏造 `source_sha`（把短 SHA 補成不存在的 40 字元）。四次皆被 `--repo-path` 擋下——**因為那四次剛好都帶了該旗標**。⚠️ 而更早有一次 PM 省略該旗標，**編造的 SHA 真的寫進了 `#63` 的 release 事件**，事後才以更正事件補救。

### 判定規則

- **對帳表含此條** → 窮舉性得到一次真實驗證
- **對帳表不含此條** → 那是驗收條 3（「須含本次新發現」）與驗收條 1（窮舉須可重跑）的**具體反例**，不是小疏漏——請執行者說明它的掃描為何看不見「契約要求 X、而驗證 X 的機制是選填或不存在」這一類

⚠️ **此則不構成派工變更**，執行者不必為它調整方向；它只是把一個本來就該被掃到的東西先寫在紙上。

⚠️ **PM 記事**：本則的前一版因反引號未跳脫而殘缺，這是 PM 今日第二次犯同一個 shell 引號錯誤（前一次在 `#92` 的關閉留言，卡號被吃掉）。


## Comment 5315879091 · 2026-08-17T12:13:51Z

## 預測結果：**未命中，但責任在 PM 不在工具**

`issuecomment-5315518506` 預先登記的預測是：對帳表應該找到「契約要求 `source SHA` 為完整 40 字元 hex，而 `handoff` 的存在性驗證靠選填的 `--repo-path`、`review` 完全沒有」。

**實測**（對 `01fb578` 的 `docs/CONTRACT_TOOL_RECONCILE.md`，430 行）：

```
正控組  review-invalid          → 6 個命中（確認文件確實在講缺口）
預測    repo-path / repo_path   → 0
        source-sha / source_sha → 0
```

### ⚠️ 但按預先登記的判定規則之前，先查它在不在射程內——結果是不在

工具宣告兩條軸：

- **符號軸**：事件型別／交付狀態／卡面欄位，由三條語法規則掃文件導出
- **守衛覆蓋軸**：`guard/<寫入入口>→<資料模組>`（本次三個缺口皆此形狀：`card.py→resources`、`amend_cmd.py→resources`、`assign_cmd.py→card`）

PM 預測的那條**兩軸皆不涵蓋**：它不是符號，也不是「入口 import 了資料模組卻到不了守衛函式」的配對——它是**一個旗標是選填的**。

**所以這不是驗收條 3 的反例，是 PM 把預測寫錯了形狀。** ⚠️ PM 今日整天在要求執行者「先確認工具真的在量你以為的東西」，而自己在下這個預測時沒有先確認對帳器的軸涵不涵蓋它。

### 但它留下一個該問的問題

「契約要求 X，而**驗證 X 的機制是選填或不存在**」——這一族與表上其他條目同源（都是「宣告了但機器沒接住」），卻落在兩軸之外。

**這不是缺陷，是射程邊界；但邊界該被寫下來**，否則讀這張表的人會以為「表上沒有＝沒有缺口」。已列入查核重點請查核者裁定：是該擴軸，還是該在文件裡明寫此類不在射程。

### 已實現的傷害（原樣保留，供日後引用）

PM 於 2026-08-16／17 共四次在 `handoff` 上捏造 `source_sha`，四次皆被 `--repo-path` 擋下——因為那四次剛好都帶了該旗標。更早有一次省略該旗標，編造的 SHA 真的寫進了 `#63` 的 release 事件。


## Comment 5316277478 · 2026-08-17T12:50:14Z

```yaml
core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: gh api repos/ruan6047/ai-workflow/compare/main...claude/WF-REVIEW-INVALID-TRACE1 --jq '.merge_base_commit.sha, (.files[].filename)'
    observed: merge base = d0008b3288a2df9541f03cff7784693f6a429095；變更檔僅 scripts/contract_tool_reconcile.py、docs/CONTRACT_TOOL_RECONCILE.md、cli/tests/test_contract_tool_reconcile.py。
  - command: python3 scripts/contract_tool_reconcile.py --format json | python3 -c 'import sys, json; d=json.load(sys.stdin); print(d["symbol_count"], d["gap_count"], len(d["guard_gaps"]), d["ungated_status_flags"])'
    observed: 79 個契約側符號、52 個符號缺口、3 個守衛缺口；ungated_status_flags 只有 assign_cmd.py --status（預設 🚧進行中，無 choices）。
  - command: python3 scripts/contract_tool_reconcile.py --check
    observed: exit 0；輸出「[reconcile] OK：55 個缺口全部有登記處置，判定一致。」
  - command: cd cli && uv run pytest tests/test_contract_tool_reconcile.py -q
    observed: 33 passed。
  - command: |-
      python3 - <<'PY2'
      from pathlib import Path
      import re
      root = Path('.')
      for path in sorted((root / 'cli/src/wf_cli/commands').glob('*.py')):
          if '📦已合併' in path.read_text(encoding='utf-8'):
              print('MERGED_LITERAL', path)
      inscope = []
      kebab = re.compile(r'`([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`')
      for p in [root / 'AI_WORKFLOW.md', root / 'docs/ROADMAP.md', *sorted((root / 'templates').glob('*.md'))]:
          inscope += kebab.findall(p.read_text(encoding='utf-8'))
      print('INSCOPE_HAS_PROBE_BLOCKS', 'probe-blocks' in inscope)
      name_re = re.compile(r'^_?(validate|check|verify|find_conflicts|assert)')
      for p in sorted((root / 'cli/src/wf_cli').rglob('*.py')):
          for line in p.read_text(encoding='utf-8').splitlines():
              m = re.match(r'def\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*\\(', line)
              if m:
                  name = m.group(1)
                  if any(tok in name for tok in ('forbid', 'ensure', 'requires', 'required', 'refuse')) and not name_re.match(name):
                      print('GUARDISH_MISS', p, name)
      PY2
    observed: 指令層沒有任何命令寫出 literal `📦已合併`（只在 doctor_cmd.py 讀它）；`probe-blocks` 不在本工具的 in-scope universe；`_GUARD_NAME` 會漏 `_forbid_force`、`required_trailers`、`ensure_fields` 這類 guard-ish 名稱。
findings:
  - finding_id: WF-REVIEW-INVALID-TRACE1-R1-01
    severity: info
    blocking: false
    finding_class: authoritative-artifact
    attribution: planner
    root_cause_id: core-pain-vs-service-goal-split
    evidence: 卡面「核心痛點」寫的是「契約↔工具從來沒有對過帳」；本交付已機械產出 79/52/3，且五個正控組都命中。卡面「服務的原始目標」寫的是「失敗與阻塞路徑要能回答卡在哪一關」；本卡明文不實作任何修補，所以那一欄仍然零進度。
    disposition: 這輪 core_pain_resolved 應對核心痛點欄判 yes，不應拿本卡刻意排除的服務目標欄否掉整張交付；若需求方要驗「卡在哪一關」是否可見，應在後續修補卡另判。
  - finding_id: WF-REVIEW-INVALID-TRACE1-R1-02
    severity: info
    blocking: false
    finding_class: authoritative-artifact
    attribution: planner
    root_cause_id: drift-check-without-freshness
    evidence: `python3 scripts/contract_tool_reconcile.py --check` 在 52 個既知符號缺口＋3 個守衛缺口全部仍未處置時照樣是綠的；它守的是「實際缺口集合 ↔ §6 登記處置」是否漂移，不守缺口有沒有被消化。`docs/CONTRACT_TOOL_RECONCILE.md` §2.3/§6 也只宣告 missing/stale/changed 三個紅向。
    disposition: 這是本卡「對帳先於修補」的刻意上限，不是執行者漏做；若需求方要缺口重新浮現，需另立承接機制（例如待辦化或複查時點），而不是把這個要求追溯回本卡。
  - finding_id: WF-REVIEW-INVALID-TRACE1-R1-03
    severity: major
    blocking: false
    finding_class: governance
    attribution: external
    root_cause_id: ungated-status-transition
    evidence: PM 對 `assign --status` 的形狀判斷成立：assign_cmd.py 的 `--status` 無 `choices`，args.status 直送 `set_field_value`，而 project.py 只把它限制在 Project 已宣告的 SINGLE_SELECT 選項內；因此它不是「任意字串寫入」，而是「可直接跳到合法但有前提的狀態」。我另外查了命令層，沒有任何專責 writer 會把 `🚨已升級` 或 `📦已合併` 寫進狀態面；未知值會在 client side 被 `set_field_value`/`test_set_field_value_rejects_unknown_single_select_option` 擋下，所以 PM 沒驗到的「Projects API 對非法 SINGLE_SELECT 的實際拒絕」在 wfcli 路徑上目前不可觀測。
    disposition: 這是 repo 級治理缺口，而且嚴重度高於表上的一般 read-only 狀態列；但本卡的工作是把它找出來，不是當場修掉它。需求方應把它視為高優先 follow-up，而不是回頭否定這張對帳卡。
  - finding_id: WF-REVIEW-INVALID-TRACE1-R1-04
    severity: minor
    blocking: false
    finding_class: authoritative-artifact
    attribution: planner
    root_cause_id: scope-and-guard-axis-communication
    evidence: 本工具的射程其實已寫得很明確：canonical + templates + ROADMAP；因此 `WF_*.md`/`DEV_*.md` 的 `probe-blocks` 族與「契約要求 X、但驗證 X 的旗標是選填或不存在」那一族，本來就不在這次兩軸（符號字面 / writer→guard 配對）內。另一路的 guard 軸確實仍有手寫命名假設：`_GUARD_NAME` 會漏 `_forbid_force`、`required_trailers`、`ensure_fields`，但目前 3 個實報 guard gap 不靠這些漏名函式成立；`assign_cmd.py→card` 也已在文件中正確標成 candidate 而非既成缺口。卡面「驗證」欄仍停在改版前的 #57 重放，這是卡面自身未同步。
    disposition: 不需要因這些說明層問題退回執行者；若需求方要避免讀者誤解成「表上沒有＝完全沒洞」，應由 PM/planner amend 卡面與文件措辭，並把 `assign_cmd.py→card` 維持在候選待裁，不要把它當成交付缺陷。
```

