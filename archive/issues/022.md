# #22 WF-ESCALATION-DEFERRED-FINDINGS1 查核規格變更會誤觸三次門檻：補 deferred finding 的表示法與清償義務
- state: closed  created: 2026-08-11T03:38:02Z  closed: 2026-08-12T01:33:41Z
- url: https://github.com/ruan6047/ai-workflow/issues/22
- comments: 21

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code
- 執行：待指派　查核：跨家族查核（契約本體，依 AI_WORKFLOW.md B2 例外須走 PR）
- Initiative：—　spec 基線：需求方 2026-08-11 於 ai-workflow#16 的 R4 checkpoint 裁定另開此卡。來源＝#16 實際觸發：R3 依需求方裁定改為窄規格（只搜同族第三例、明文不逐條重驗 R1/R2），導致 R2-001／R2-002 兩個 accepted blocking finding 在 R3 既未標 resolved 也未標 withdrawn，第 173 行第二條件成立而強制 R4 escalate。契約缺口本身不在 #16 射程。相依：adapter 側的機械執行歸 #9（WF-22-CLI4 wfcli escalation 帳承接）；#16 §9-I 為 review 的 checkpoint 守衛。資源交集：本卡宣告 file:templates/review-escalation.md，#16 宣告 file:templates/，兩者不衝突——resources.py find_conflicts 為完全相同字串比對且明文不做路徑前綴模糊比對，故本卡可立即 assign。（開卡當下曾誤述為互斥而阻塞，未查證即斷言，已更正。順帶記錄：以目錄形式宣告資源，對該目錄下的具名檔案不提供任何保護，此為既有實作語意，非本卡射程。）
- DB：db_scope=none
- 服務的原始目標：讓 review 升級門檻反映執行者是否真的連續失敗，而不是被合法的查核規格調整誤觸發；同時不讓 deferred 成為無限期迴避門檻的後門。

## 簡介
<!-- card-brief:begin -->
在 templates/review-escalation.md 補 deferred finding 的表示法：需求方合法變更查核規格時，前輪 accepted blocking finding 得由 escalation-checkpoint 明示 deferred 而不觸發第 173 行的強制 escalate，並明定清償義務、禁止同一 finding 連續 defer、裁定者須為需求方；一併修掉第一條件「同 root_cause_id 三個 attempt」依字面一旦成立即永久為真的閂住。**適用時機**：查核範圍被合法收窄卻換來機械強制升級時；或要查升級訊號為何該代表「執行者連續失敗」的依據時。⛔ 非射程：adapter 側的機械執行歸 WF-22-CLI4（aiwf#9）；不改動 §3 counts_toward_escalation 的既有推導與定義。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：review-escalation.md 第 173 行假設每一輪查核都會處理前一輪的 finding；但「需求方變更查核規格」是合法動作，會使前輪 accepted blocking finding 既非 resolved 也非 withdrawn，於是機械上必然強制下一輪 escalate。收窄查核範圍因此帶有一個非預期的懲罰，而升級訊號也不再代表「執行者連續失敗」。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:templates/review-escalation.md",
    "file:scripts/replay_escalation_rules.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 定義 deferred finding 的表示法：escalation-checkpoint 得明示哪些前輪 accepted blocking finding 因查核規格變更而 deferred，並載明 deferred 的理由與裁定者；該集合不觸發第 173 行的強制 escalate。
- [ ] 明定清償義務：deferred 集合必須在指定的後續 attempt 前被逐項給出 resolved／withdrawn／仍開啟，逾期則強制 escalate。上限須為機械可檢查的具體條件，不得只寫「應儘速」。
- [ ] 確保 deferred 不成為迴避門檻的後門：同一 finding 不得被連續 defer；defer 的裁定者必須是需求方而非執行者或查核者。
- [ ] **（2026-08-11 追加）修正第一條件的永久閂住**：第 173 行「同 root_cause_id 出現於三個唯一可計數 attempt」依字面一旦成立即永久為真，即使該根因此後再未產出 blocking finding，與 §4「持續出現」的措辭不一致，且使該條件失去鑑別力。須改為可失效的判準（例如要求該根因在最近一個可計數 attempt 仍產出 blocking，或明定「持續」為不中斷）。**與第二條件的 deferred 機制互不干擾，兩條件仍各自獨立成立。**
- [ ] 本卡改的是 canonical 契約本體，須走 PR＋跨家族查核，不得直推。

## 驗證

- [ ] 以 ai-workflow#16 的事件流回放：現行規則下 R4 前確實強制 escalate；修訂後，checkpoint 明示 deferred 時不強制，而未清償時仍強制。回放腳本須在 repo 內、可離線重跑。**（2026-08-12 需求方裁定）本項與下一項得以「#16 的穩定 finding_id 最小改寫流」承擔**——#16 實際有三處換號重開（R1-002→R2-001、R1-006→R2-002、R4-001→R5-001），依六格「前提是穩定 finding_id」該兩項在忠實流上不可能成立，此為卡面條文建立在錯誤前提上，屬 planner 缺陷，不得要求執行者補造 defer 使其通過。構造流必須明確標為構造，且忠實流的結果須一併如實呈現。
- [ ] 第一條件專項回放：#16 的 incomplete-custom-classification-overrides-canonical 於 R3–R7 產出 blocking、R8 起未再產出。修訂後的判準必須在 R8／R9 判定該條件不再成立，而在 R5–R7 仍成立。同上項，得以穩定 id 最小改寫流承擔。
- [ ] 確認不與 review-escalation.md §3 的 counts_toward_escalation 既有推導衝突，且不改變其定義。
- [ ] 確認 adapter 側可機械執行（與 #9 的介面對齊），非只有文字規範；若判定需 CLI 改動，明列歸 #9 或另開子卡。
## Log

- 2026-08-11T11:38:01+08:00 open by Claude Opus 5@Claude Code；owner 待指派；iteration 0。
- 2026-08-11T11:39:35+08:00 amend by wf-cli（op d32f8a3a）→ spec 基線：原值「需求方 2026-08-11 於 ai-workflow#16 的 R4 checkpoint 裁定另開此卡。來源＝#16 實際觸發：R3 依需求方裁定改為窄規格（只搜同族第三例、明文不逐條重驗 R1/R2），導致 R2-001／R2-002 兩個 accepted blocking finding 在 R3 既未標 resolved 也未標 withdrawn，第 173 行第二條件成立而強制 R4 escalate。契約缺口本身不在 #16 射程。相依：adapter 側的機械執行歸 #9（WF-22-CLI4 wfcli escalation 帳承接）；#16 §9-I 為 review 的 checkpoint 守衛。注意資源交集：#16 現宣告 file:templates/（整個目錄），本卡在 #16 進入終態或 amend 其資源宣告前無法 assign。」→ 新值「需求方 2026-08-11 於 ai-workflow#16 的 R4 checkpoint 裁定另開此卡。來源＝#16 實際觸發：R3 依需求方裁定改為窄規格（只搜同族第三例、明文不逐條重驗 R1/R2），導致 R2-001／R2-002 兩個 accepted blocking finding 在 R3 既未標 resolved 也未標 withdrawn，第 173 行第二條件成立而強制 R4 escalate。契約缺口本身不在 #16 射程。相依：adapter 側的機械執行歸 #9（WF-22-CLI4 wfcli escalation 帳承接）；#16 §9-I 為 review 的 checkpoint 守衛。資源交集：本卡宣告 file:templates/review-escalation.md，#16 宣告 file:templates/，兩者不衝突——resources.py find_conflicts 為完全相同字串比對且明文不做路徑前綴模糊比對，故本卡可立即 assign。（開卡當下曾誤述為互斥而阻塞，未查證即斷言，已更正。順帶記錄：以目錄形式宣告資源，對該目錄下的具名檔案不提供任何保護，此為既有實作語意，非本卡射程。）」；理由 開卡時斷言「#16 的 file:templates/ 宣告會使本卡無法 assign」，未查證 resources.py 即下結論；實際 find_conflicts 為完全相同字串比對且明文不做前綴模糊比對，兩者不衝突，本卡可立即派工。
- 2026-08-11T12:52:44+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree claude/WF-ESCALATION-DEFERRED-FINDINGS1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-deferred-findings1；交付狀態 🚧進行中。
- 2026-08-11T13:04:26+08:00 handoff by wf-cli → owner 跨家族查核（待需求方指派）；iteration 0；SHA 7c785ede9a6391bc4decd3a3577b97bc13d12f76；證據 PR https://github.com/ruan6047/ai-workflow/pull/26 ；唯一改動 templates/review-escalation.md (+51/-3)，與資源宣告一致。驗證：(1) #16 R1→R7 事件流回放，C@R3 現行強制 escalate、修訂後明示 deferred 時不強制且與需求方實際裁定 continue 一致；C@R5/C@R6 第一條件獨立成立仍 escalate。(2) 反事實 R4 未清償：沉默與再次 defer 兩種寫法皆仍強制 escalate。(3) §3 counts_toward_escalation 四款一字未改；cli pytest 292 passed。已知落差：wfcli 無 escalation-checkpoint writer，機械執行歸 #9。。
- 2026-08-11T13:06:57+08:00 amend by wf-cli（op 444f248d）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:templates/review-escalation.md" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:templates/review-escalation.md、file:scripts/replay_escalation_rules.py」；理由 驗收條文要求以 #16 的 R1→R7 事件流回放驗證，執行者確實寫了腳本但為守資源宣告而留在 scratchpad，導致該證據無法被任何人重跑——本 repo 本輪反覆踩到的正是「宣稱的證據事後失效」。擴充宣告以容納該腳本進 repo，方向是讓證據可重跑而非擴大改動範圍。
- 2026-08-11T13:12:20+08:00 handoff by wf-cli → owner 跨家族查核（待需求方指派）；iteration 0；SHA 90736ede630e0f43567c5037422521b14a5c8b89；證據 更正被審 SHA：先前 handoff 指向 7c785ed，其後補提交可重跑的回放腳本 scripts/replay_escalation_rules.py（10/10 斷言通過，PM 已獨立執行複驗）。尚無任何查核 attempt，iteration 不變。PR #26。
- 2026-08-11T13:17:15+08:00 amend by wf-cli（op 6dbb1b93）→ 驗收條件：原值「[ ] 定義 deferred finding 的表示法：escalation-checkpoint 得明示哪些前輪 accepted blocking finding 因查核規格變更而 deferred，並載明 deferred 的理由與裁定者；該集合不觸發第 173 行的強制 escalate。；[ ] 明定清償義務：deferred 集合必須在指定的後續 attempt 前被逐項給出 resolved／withdrawn／仍開啟，逾期則強制 escalate。上限須為機械可檢查的具體條件，不得只寫「應儘速」。；[ ] 確保 deferred 不成為迴避門檻的後門：同一 finding 不得被連續 defer；defer 的裁定者必須是需求方而非執行者或查核者。；[ ] 與第 173 行另一條件（同 root_cause_id 出現於三個唯一可計數 attempt）互不干擾，兩條件仍各自獨立成立。；[ ] 本卡改的是 canonical 契約本體，須走 PR＋跨家族查核，不得直推。」→ 新值「定義 deferred finding 的表示法：escalation-checkpoint 得明示哪些前輪 accepted blocking finding 因查核規格變更而 deferred，並載明 deferred 的理由與裁定者；該集合不觸發第 173 行的強制 escalate。；明定清償義務：deferred 集合必須在指定的後續 attempt 前被逐項給出 resolved／withdrawn／仍開啟，逾期則強制 escalate。上限須為機械可檢查的具體條件，不得只寫「應儘速」。；確保 deferred 不成為迴避門檻的後門：同一 finding 不得被連續 defer；defer 的裁定者必須是需求方而非執行者或查核者。；**（2026-08-11 追加）修正第一條件的永久閂住**：第 173 行「同 root_cause_id 出現於三個唯一可計數 attempt」依字面一旦成立即永久為真，即使該根因此後再未產出 blocking finding，與 §4「持續出現」的措辭不一致，且使該條件失去鑑別力。須改為可失效的判準（例如要求該根因在最近一個可計數 attempt 仍產出 blocking，或明定「持續」為不中斷）。**與第二條件的 deferred 機制互不干擾，兩條件仍各自獨立成立。**；本卡改的是 canonical 契約本體，須走 PR＋跨家族查核，不得直推。」；理由 需求方 2026-08-11 裁定把第一條件的永久閂住問題併入本卡：它與本卡正在處理的第二條件同屬「一旦成立即永久為真、此後失去鑑別力」的缺陷，同一條文分兩卡修會再造出不一致。#16 的 R8 提供了現成反例（該根因自 R8 起未再產出 blocking，但條件依字面仍為真）。
- 2026-08-11T13:17:15+08:00 amend by wf-cli（op 6dbb1b93）→ 驗證：原值「[ ] 以 ai-workflow#16 的 R1→R4 實際事件流回放：現行規則下 R4 前確實強制 escalate；修訂後，checkpoint 明示 deferred 時不強制，而 R4 未清償 deferred 集合時仍強制。；[ ] 確認不與 review-escalation.md §3 的 counts_toward_escalation 既有推導衝突，且不改變其定義。；[ ] 確認 adapter 側可機械執行（與 #9 的介面對齊），非只有文字規範；若判定需 CLI 改動，明列歸 #9 或另開子卡。」→ 新值「以 ai-workflow#16 的 R1→R9 實際事件流回放：現行規則下 R4 前確實強制 escalate；修訂後，checkpoint 明示 deferred 時不強制，而未清償時仍強制。回放腳本須在 repo 內、可離線重跑。；**第一條件專項回放**：#16 的 incomplete-custom-classification-overrides-canonical 於 R3–R7 產出 blocking、R8 起未再產出。修訂後的判準必須在 R8／R9 判定該條件**不再成立**，而在 R5–R7 仍成立。；確認不與 review-escalation.md §3 的 counts_toward_escalation 既有推導衝突，且不改變其定義。；確認 adapter 側可機械執行（與 #9 的介面對齊），非只有文字規範；若判定需 CLI 改動，明列歸 #9 或另開子卡。」；理由 需求方 2026-08-11 裁定把第一條件的永久閂住問題併入本卡：它與本卡正在處理的第二條件同屬「一旦成立即永久為真、此後失去鑑別力」的缺陷，同一條文分兩卡修會再造出不一致。#16 的 R8 提供了現成反例（該根因自 R8 起未再產出 blocking，但條件依字面仍為真）。
- 2026-08-11T13:26:14+08:00 handoff by wf-cli → owner 跨家族查核（待需求方指派）；iteration 0；SHA 1c84a26e5cf588b70b3a3d73f9456c2eb36b2679；證據 更正被審 SHA（第三次指向，均無查核 attempt，iteration 不變）：需求方擴大射程後補上第一條件的可失效判準（累計 ∧ 存活），並補第六格分類承接 transferred。PM 已獨立重跑 scripts/replay_escalation_rules.py → 16/16 通過 exit 0。PR #26。
- 2026-08-11T18:22:35+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 跨家族查核（需求方於對話中轉貼原文；無 receipt marker，來源不可驗證）；core_pain_resolved no；self_run 2 項；findings 2 項（blocking 2）；attempt WF-ESCALATION-DEFERRED-FINDINGS1-e0-1c84a26e5cf588b70b3a3d73f9456c2eb36b2679。
- 2026-08-11T18:22:52+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 1；SHA 1c84a26e5cf588b70b3a3d73f9456c2eb36b2679；證據 R1：兩項 blocking。R1-001 回放腳本把 R4-001 的『接續』標成 resolved；R1-002 六格語意本身全函數但腳本未以結構化降級與 review-correction 走過分類器。查核者另確認：不採「三個連續 attempt」是正確取捨、六格不需第七個降級出口。
- 2026-08-11T18:32:11+08:00 handoff by wf-cli → owner 跨家族查核（待需求方指派）；iteration 1；SHA f63c1c0673c079c2a84f639fb6239a0439ca1b41；證據 R1-001／R1-002 修訂完成。PM 已獨立重跑 scripts/replay_escalation_rules.py → 22/22 通過 exit 0，含 768 組列舉的全函數證明與「未被任何案例走過的格：無」。
- 2026-08-11T19:00:37+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 2；SHA f63c1c0673c079c2a84f639fb6239a0439ca1b41；證據 R2：三項 blocking 皆 authoritative-artifact／executor。R2-001 fixture 捏造 deferred（PM 已核對 comment 5248665281 確認只列兩項）；R2-002 legacy 正規化繞過 classify 並覆蓋後續明列表態；R2-003 768 組僅為投影空間非真實輸入空間。R1-001 resolved、R1-002 仍開啟。
- 2026-08-11T19:01:17+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 跨家族查核（需求方於對話中轉貼原文；查核者聲明未寫入 PR／Issue 故無 receipt marker，來源不可驗證）；core_pain_resolved no；self_run 4 項；findings 3 項（blocking 3）；attempt WF-ESCALATION-DEFERRED-FINDINGS1-e0-f63c1c0673c079c2a84f639fb6239a0439ca1b41。
- 2026-08-11T23:27:30+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 3；SHA f63c1c0673c079c2a84f639fb6239a0439ca1b41；證據 R3：三項 blocking 全開。R2-001 fixture 捏造 deferred 處置（腳本把 R1-002／R1-006／R2-001／R2-002 全設為 C@R3 deferred，原始留言 5248665281 只列後兩項，故前兩項仍應落「未提及」並強制 escalate）；R2-002 legacy 正規化會壓掉後續證據（R5 後無條件把 R4-001 設 superseded-legacy 並繞過 classify()，構造 R7 再明列 R4-001 open 時完全不輸出）；R2-003 prove_partition 的 768 只證明 classify() 縮約後的投影空間，未涵蓋 carry 歸屬、epoch 邊界、同 finding 衝突事件與 correction 順序、同 SHA 多 reviewer 合併須 fail loud。escalation checkpoint 見 #issuecomment-5255216570：第二條件成立故 decision=escalate，需求方裁定 continue、維持同執行者。checkpoint 另記：本次觸發歸因於 coordinator 的派審詞缺漏（未要求逐項回報前輪閉環狀態），同型缺漏今日在 #21 亦發生一次。。
- 2026-08-11T23:50:49+08:00 handoff by wf-cli → owner 跨家族查核（契約本體，須走 PR）；iteration 3；SHA b3663a5835f0792e650cce8ebf724f4df5db7e74；證據 R3：三項 blocking 全處置，僅動兩支宣告內檔案（review-escalation.md +18/-11、replay 腳本重寫）。R2-001：依 gh api 取回 comment 5248665281 重建 fixture，PM 已逐字核對 deferred_findings 確實只有 R2-001／R2-002 兩筆、未被補造；結果如實呈現——修訂後條文下 C@R3 仍強制 escalate（carry set 四筆，R1-002／R1-006 在 R2 被換號重開故落未提及），C@R8 第一條件仍為 TRUE。#16 全流標為 legacy 並依 cutover 標為診斷性 what-if。新增四種敏感度測試（少一筆 defer／deferred_by 等於 owner／缺 defer_ruling_url／defer_cause 不在列舉內）各自使該筆失效。R2-002：LEGACY_SUPERSEDED、normalize_legacy 與繞過 classify() 的分支整段移除，無任何 supersession 捷徑；收下查核者的 R7 探針，R4-001 現正確落「仍開啟」且在 C@R5–C@R8 每個 checkpoint 的 carry 分類都有輸出。R2-003：選收斂宣稱，改為「分類器在其宣告值域上是一個分割」並於執行時原樣印出不涵蓋清單（衝突事件與多 reviewer fail loud 明確聲明未涵蓋）；投影空間本身列舉完整——finding_class／attribution 由各兩代表值展開為全部五值、defer 必要條件由單一 wellformed bit 拆為七款逐項，153,600 點各恰落一格，另附逐款必要性驗證。前輪兩項閉環：R1-001 resolved（斷言 R4-001 在任何 checkpoint 皆未被記為 resolved／withdrawn，忠實流與探針流皆過；執行者並指出 f63c1c0 的 legacy 正規化其實以另一形態重演同一根因，即 R2-002，本輪整個移除才真正關掉）；R1-002 resolved（新增事件層 replay 引擎，六格由引擎在同一 checkpoint 一次走完，非手搓 dict）。射程內補洞：草案原本只有 spec-narrowed 一種 defer 成因，一次指示疏漏無出口可走，已新增 defer_cause 為必填、取值 spec-narrowed｜instruction-omitted，兩者皆須指向指示側具體事實，其餘必要條件一律不放寬；另補「已非有效 open finding」格的清償語意漏洞。驗證：replay 44/44 exit 0（PM 獨立重跑相符）、cli pytest 292 passed 與基線同。⚠️ 兩項需另行裁定：(1) 卡面兩項驗證條文在 #16 忠實事件流上不成立（換號重開的直接後果），執行者未補造 defer 使其通過，改以「#16 穩定 id 最小改寫」承擔並標為構造——此替代是否正當須需求方裁定，PM 刻意不先 amend 卡面；(2) 本卡新增的 instruction-omitted 出口，正好涵蓋今日 #21 與本卡兩個 checkpoint 的觸發成因（皆為 PM 派審詞缺漏），構成「交付物為自己的 escalation 觸發提供出口」的形狀。兩項與其餘三項跨卡矛盾詳見同日的跨卡對帳留言。執行者自承六個未關的洞，含 §2 衝突裁決 gate 與多 reviewer fail loud 完全無模型、回放引擎是契約的第二個實作而非 adapter（線上仍無 checkpoint writer，見 #9）、instruction-omitted 的成因無機械核對。。
- 2026-08-12T00:15:30+08:00 amend by wf-cli（op 4f5bf962）→ 驗證：原值「[ ] 以 ai-workflow#16 的 R1→R9 實際事件流回放：現行規則下 R4 前確實強制 escalate；修訂後，checkpoint 明示 deferred 時不強制，而未清償時仍強制。回放腳本須在 repo 內、可離線重跑。；[ ] **第一條件專項回放**：#16 的 incomplete-custom-classification-overrides-canonical 於 R3–R7 產出 blocking、R8 起未再產出。修訂後的判準必須在 R8／R9 判定該條件**不再成立**，而在 R5–R7 仍成立。；[ ] 確認不與 review-escalation.md §3 的 counts_toward_escalation 既有推導衝突，且不改變其定義。；[ ] 確認 adapter 側可機械執行（與 #9 的介面對齊），非只有文字規範；若判定需 CLI 改動，明列歸 #9 或另開子卡。」→ 新值「以 ai-workflow#16 的事件流回放：現行規則下 R4 前確實強制 escalate；修訂後，checkpoint 明示 deferred 時不強制，而未清償時仍強制。回放腳本須在 repo 內、可離線重跑。**（2026-08-12 需求方裁定）本項與下一項得以「#16 的穩定 finding_id 最小改寫流」承擔**——#16 實際有三處換號重開（R1-002→R2-001、R1-006→R2-002、R4-001→R5-001），依六格「前提是穩定 finding_id」該兩項在忠實流上不可能成立，此為卡面條文建立在錯誤前提上，屬 planner 缺陷，不得要求執行者補造 defer 使其通過。構造流必須明確標為構造，且忠實流的結果須一併如實呈現。；第一條件專項回放：#16 的 incomplete-custom-classification-overrides-canonical 於 R3–R7 產出 blocking、R8 起未再產出。修訂後的判準必須在 R8／R9 判定該條件不再成立，而在 R5–R7 仍成立。同上項，得以穩定 id 最小改寫流承擔。；確認不與 review-escalation.md §3 的 counts_toward_escalation 既有推導衝突，且不改變其定義。；確認 adapter 側可機械執行（與 #9 的介面對齊），非只有文字規範；若判定需 CLI 改動，明列歸 #9 或另開子卡。」；理由 需求方 2026-08-12 只裁原則，不裁事實：構造流可作為前兩項驗證的證據，理由是 #16 的三處換號重開使忠實流在數學上無法滿足該兩項，屬卡面條文的 planner 缺陷。**「這個構造是否忠實」仍由查核者判定，本次修訂不預先認定。** 本次修訂發生在 🔍待查核 期間，屬中途改卡面，已於卡上另貼告知留言說明改了哪一欄、何時、為何，供查核者判斷是否影響其裁決。。
- 2026-08-12T00:57:11+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（無 receipt marker，來源不可驗證；PM 另將原報告的 > 折疊純量改為 | 以通過解析器）；core_pain_resolved no；self_run 6 項；findings 1 項（blocking 1）；attempt WF-ESCALATION-DEFERRED-FINDINGS1-e0-b3663a5835f0792e650cce8ebf724f4df5db7e74。
- 2026-08-12T01:19:49+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 4；SHA b3663a5835f0792e650cce8ebf724f4df5db7e74；證據 R4：R3-001（major，blocking）——新增的 instruction-omitted 出口只驗欄位非空，未驗它確實指向「派審指示缺漏」。查核者以隔離探針證明：defer_cause=instruction-omitted 搭配預設 defer_reason「規格收窄」與 https://example/ruling 的假 URL，仍得 forced=False、三筆皆分類為 deferred。這不只是測試不完整，而是交付的「機械可執行」契約沒有把新出口與其所宣稱的事實相連，違反卡面「不讓 deferred 成為無限期迴避門檻後門」的目標。前輪五項（R1-001、R1-002、R2-001、R2-002、R2-003）全數 resolved 並各有證據。無 escalation checkpoint（前輪 accepted blocking 皆已明列 resolved、新 finding 根因不同）。。
- 2026-08-12T01:42:36+08:00 handoff by wf-cli → owner 跨家族查核（契約本體，須走 PR）；iteration 4；SHA 539c3336152881ab74ed91eb38735acc910f961d；證據 R4：R3-001 已處置。defer 必要條件由 5 款擴為 7 款，instruction-omitted 另需專節三款全部成立。第 5 款：defer_ruling_url 須解析為本卡 issue 的單一留言 URL，站外任意 URL 與他卡 URL 一律無效。第 6 款（新）：defer_reason 須逐字含該留言的數字 id，把「載明對應的那一次事件」從人讀措辭變成可比對的指涉，散文本身不再是判準。專節 (a) 指認：事件流上須有本 epoch 的派審事件以 review_prompt_url 指認同一則留言，且它派的正是 trigger attempt 的查核；(b) 缺漏的結構化宣告：該事件的 closure_reporting_requested 須恰為 false（缺欄、true、無法判定皆無效），因 review-prompt.md §6 已把逐項閉環定為 R2 以後固定範圍，故該欄記錄的是一次偏離範本、應在派審當下寫下而非由受益方事後推定；(c) 可用性：寫入通道未產出 (a)(b) 或 adapter 無法解析時本 cause 不可用、每筆 defer 無效並強制 escalate，adapter 不得以「讀不到證據」改判成立。論證了舉證強度的不對稱是刻意的——spec-narrowed 宣稱的是肯定作為（留痕與事實同體），instruction-omitted 宣稱的是否定事實（指標不證明內容）。replay 端同步：新增 dispatch 事件種類與 parse_ruling_id，DEFER_CONDITIONS 7→11 款，Checkpoint 帶 defer_audit 逐筆印出被打掉的款。斷言 44→55，exit 0，離線無相依；cli 292 passed 作基線。PM 已獨立重跑：55/55 通過；查核者原探針（假 URL＋「規格收窄」理由）現三筆全被五款打掉、落未提及並強制 escalate；「本 repo 現況」案例單憑 cause_available 即打掉，證實今日每一次使用都 fail-closed。利益衝突處置：執行者把「本卡自身的 escalation checkpoint 亦不得引用本 cause」寫進條文正文而非只留在報告，並自陳其判準是結果而非意圖——修正後的規則在本 repo 今天不可用，故它擋掉的第一個使用者就是本卡；並指出若為自己量身訂做，最省事的寫法是只要求「該留言存在」（本卡派審留言當然存在），他沒走那條。上輪自承第 3 個洞的歸因：判定為嚴重度誤判而非遺漏——錯在量尺（拿身分維度衡量而非「這組必要條件能否被任意輸入滿足」）。執行者自承六個未關的洞，其中第 1 項最該看：closure_reporting_requested 是派審當下的自述欄位、留言原文從未被讀取，而寫它的正是可能造成缺漏的一方；條文只寫 adapter「應」再以原文核對，沒有強制也沒有實作。。
- 2026-08-12T07:08:50+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（收據 issuecomment-5259849441，多行格式合規；PM 依其取材規則自 GitHub 回讀重算 report_sha256=a1fcd172… 一次相符）；core_pain_resolved no；self_run 3 項；findings 1 項（blocking 1）；attempt WF-ESCALATION-DEFERRED-FINDINGS1-e0-539c3336152881ab74ed91eb38735acc910f961d。
- 2026-08-12T07:18:45+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 5；SHA 539c3336152881ab74ed91eb38735acc910f961d；證據 R5：R4-001（major，blocking，spec-narrowed-ruling-content-not-validated）——上一輪把 instruction-omitted 收緊到可機械核對，但 spec-narrowed 這一支沒有同步：第 112-126 行只驗 defer_ruling_url 的本卡留言形狀、理由含數字 id 與 deferred_by 身分，沒有讀取該留言確認它是需求方的規格收窄裁定，也沒有驗證留言作者。故取得任意本卡 comment URL 並在 reason 放入其 id，即可令有效 open finding 落 deferred、壓掉第二條件。關鍵在於 instruction-omitted 目前不可用，spec-narrowed 是唯一可用的 cause，所以出口整體的實際強度由這一支決定——而它是兩支裡較弱的。disposition：對 spec-narrowed 也建立可機械驗證的裁定證據（至少驗 URL 指向需求方所作的裁定事件，並由 adapter 讀取或以寫入時不可偽造的結構化欄位確認該裁定確實縮窄本次 trigger attempt 的閉環範圍）；證據或解析能力不存在時該筆 defer 須 fail-closed 為未提及。新增三個反例：任意本卡留言、非需求方留言、內容未收窄。前輪六項（R1-001／R1-002／R2-001／R2-002／R2-003／R3-001）全數 resolved。收據合規（多行格式，PM 回讀重算一次相符）。無 escalation checkpoint（前輪 accepted blocking 皆已明列 resolved、新 finding 根因不同）。。
- 2026-08-12T08:54:18+08:00 handoff by wf-cli → owner 跨家族查核（契約本體，須走 PR）；iteration 5；SHA 8d27bedd20a95690bcb0949777c8dd7dcc32d5b7；證據 R5：R4-001（spec-narrowed 的裁定內容未被驗證）已處置。§4 新增「spec-narrowed：肯定作為的三款」，與 instruction-omitted 的 (a)(b)(c) 對稱：(a′) defer_ruling_url 那則留言的 GitHub comment author 逐字為需求方（平台身分，非 deferred_by 的自述）；(b′) 綁定二擇一——結構化（裁定事件記下被收窄的 attempt_id 與 finding_id）或原文核對（adapter 讀現行 body 須逐字含 trigger attempt 的 attempt_id、該筆 finding_id 與 defer_cause: spec-narrowed）；(c′) 兩條路徑皆不可得即本 cause 不可用，每筆 defer 落未提及並強制 escalate。順帶得到免時鐘的新鮮性：attempt_id 內含本輪 source SHA，早於該 commit 的裁定不可能逐字含它，故舊裁定無法搬來掩護新一輪。執行者並推翻自己上一輪的話：「舉證強度的不對稱是刻意的」該句是錯的，論證對但實作沒兌現，而未兌現的正是它的前提——「留痕與事實同體」只在該留痕確經核對就是那個裁定時成立；該更正逐字引述前一版原文並標為錯誤，寫在條文正文而非報告。PM 獨立複驗：65/65；三個反例（任意本卡留言／非需求方留言／內容未收窄）全落未提及並各自指名被打掉的款，正例仍 deferred 證明非死條文；doctor.py:385,396 確實已讀 body 與 user，故 (c′) 預設可用的依據成立。對「是否矯枉過正成 deferred 根本不存在」執行者正面回答：wfcli 根本無 checkpoint writer（grep 零命中），整個 deferred 機制在本 repo 尚未上線、與 cause 收緊無關；且兩個 cause 依賴層級不同——instruction-omitted 卡在寫入端，spec-narrowed 只需唯讀能力，#9 落地當天即可用。escalation checkpoint 見同日留言：兩條件皆不成立 decision=continue，同時記錄第四個 attempt 前的漏建（PM 合規缺口，不追溯補建），並請查核者裁示 R3-001 與 R4-001 是否同族——兩者是同一件事的兩個分支，若判同族即 2／3，再一次滿足門檻。。
- 2026-08-12T09:26:07+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex 子代理（收據 issuecomment-5260904083，多行格式合規；PM 已回讀重算 report_sha256=a2282e6b… 相符）；core_pain_resolved yes；self_run 3 項；findings 1 項（blocking 0）；attempt WF-ESCALATION-DEFERRED-FINDINGS1-e0-8d27bedd20a95690bcb0949777c8dd7dcc32d5b7。
- 2026-08-12T09:35:37+08:00 handoff by wf-cli → owner 已收尾；iteration 5；SHA 8d27bedd20a95690bcb0949777c8dd7dcc32d5b7；證據 跨家族查核 R5 判 APPROVE（1 info 非阻擋：attempt_id 含 source SHA 的免時鐘新鮮性表述應限縮為「防止既有先前 attempt 的裁定重用」，不阻擋本卡）（收據 issuecomment-5260904083，PM 已回讀重算 report_sha256=a2282e6b… 相符）。PR #26 已合併（6e6e8ab），8d27bed 確為 main 祖先。收尾七步前三步逐項核對通過，worktree／本地分支／遠端分支皆已清理並驗證不存在，遠端以條件式刪除移除。刻意未使用 WF-CLEANUP-GUARD1 的 --cleanup 路徑，理由同 #23。釋放資源：file:templates/review-escalation.md、file:scripts/replay_escalation_rules.py。。
- 2026-08-26T22:11:29+08:00 amend by wf-cli（op a6e1797f）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:1f42298c75de32986eb75f778a5e25e4bd49587c2dc8c0ccb52be2b545611a27 (723 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5249322990 · 2026-08-11T05:26:20Z

## PM 複核註記（派審前）

**被審 SHA 已第三次更正為 `1c84a26e5cf588b70b3a3d73f9456c2eb36b2679`**（三次皆無任何查核 attempt，iteration 維持 0）。歷程：`7c785ed`（初版）→ `90736ed`（補可重跑腳本）→ `1c84a26`（需求方擴大射程後補第一條件）。

**PM 獨立複驗**：從分支取出 `scripts/replay_escalation_rules.py` 於 repo 外直接執行 → **16/16 通過、exit 0**，不連網、無第三方相依。改動範圍 2 檔，與資源宣告（已於 `op 444f248d` 擴充）一致。

### 執行者自行打穿了自己上一版的分類——這一項請查核者特別確認

擴大回放範圍到 R8 時，執行者發現**自己上一版新增的五格分類漏了一整類輸入**：R8 對 R5-001／R5-002／R7-001 的處置是 `transferred`（降為 `info`、`blocking=false`），這既非 `resolved` 也非 `withdrawn`、未明列 `open`、未被 defer——**會落進「未提及」格而從後門強制 escalate**。

已補第六格「已非有效 open finding」，並載明它是 §5 末段既有規則的直接後果（不新增 `status` 值、不新增出口）。

> **這正是本 repo 已現七例的同族形態**（分類漏一整類輸入），而且犯在執行者自己新增的表格上。**請獨立確認第六格之後分類確實全函數**——尤其：`transferred` 之外還有沒有第七類降級路徑？`review-correction` 撤回一個 finding 時落哪一格？

### 一處資料更正，請一併核對

執行者修正了上一版把 **R4-001 一路記為「未提及」** 的錯誤，改判為已閉合，依據是 `5249003956` 的 R6 列「blocking 3 ＝ 新 1 ＋ 再開 2（R5-001／R5-002）」，R4-001 不在其中。

**PM 補充一個更直接的依據**：R5 的裁決留言把該項記為 **`R5-001（承 R4-001）`**——R4-001 是被 R5-001 **接續**而非獨立閉合。方向一致（都不該落「未提及」），但機制不同。**請查核者判定腳本採用的閉合機制標注是否精確**；若「接續」與「resolved」在條文下語意有別，該處標注需修正。

### 其餘

- 資料來源的撤回鏈已於腳本檔頭註記：`5249245451` 的裁定欄係執行者擅填、已由 `5249247912` 撤回，只採其事實部分，裁定改採 `5249260224`。
- 假想 R9-A／R9-B 在腳本內明確標示**非事實**，用於證明存活判準雙向可逆。
- 執行者刻意不採「三個連續 attempt」的讀法，理由寫進條文（會讓隔輪出現的根因永遠逃脫）。**請判斷這個取捨是否正確**——它是本輪唯一沒有既有權威可依循、純由執行者判斷的設計決定。


## Comment 5251906910 · 2026-08-11T10:22:36Z

<!-- wf-review-event:v1 card_id=WF-ESCALATION-DEFERRED-FINDINGS1 source_sha=1c84a26e5cf588b70b3a3d73f9456c2eb36b2679 attempt_id=WF-ESCALATION-DEFERRED-FINDINGS1-e0-1c84a26e5cf588b70b3a3d73f9456c2eb36b2679 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-ESCALATION-DEFERRED-FINDINGS1`　attempt_id：`WF-ESCALATION-DEFERRED-FINDINGS1-e0-1c84a26e5cf588b70b3a3d73f9456c2eb36b2679`
- 查核者：跨家族查核（需求方於對話中轉貼原文；無 receipt marker，來源不可驗證）　escalation_epoch：0
- source_sha：`1c84a26e5cf588b70b3a3d73f9456c2eb36b2679`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-11T18:22:35+08:00

### self_run（查核者實跑）

- `自目標 SHA 執行 scripts/replay_escalation_rules.py`
  - 16/16、exit 0。
- `核對 Issue 16 原始留言 5248851032、5248934953、5249222343、5249245451、5249247912、5249260224`
  - 撤回鏈與裁定取代關係與腳本檔頭註記相符；R5 原文明示「R4-001 remains open」、R5-001 為「承 R4-001」。

### findings（2，其中 blocking 2）

- **WF-ESCALATION-DEFERRED-FINDINGS1-R1-001**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`succession-encoded-as-closure`
  - evidence：replay_escalation_rules.py 第 106 行把 R4-001 標為「R6 於此閉合／resolved」，是錯誤標注。 原始 R5 審查明示「R4-001 remains open」，R5-001 是「承 R4-001」； R6 沒列 R4-001 只能表示其被 R5-001 接續，不能推出已 resolved。 這不是文字瑕疵：以虛構的 resolved 把一個「接續／重編號」路徑藏進既有格， 正好破壞本輪要驗證的分類完備性。
  - disposition：改為明確的歷史 ID 正規化／承接關係，或承認舊事件不符合現行穩定 finding_id 契約； 不可將接續等同 closed。
- **WF-ESCALATION-DEFERRED-FINDINGS1-R1-002**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`cell-coverage-not-executable`
  - evidence：條文的六格語意本身是全函數：review-correction 撤回落 withdrawn 格； accepted=false、blocking=false、或其他不再符合 §3 的合法降級皆落「已非有效 open finding」格， 因此不需要第七個「降級」出口。 但腳本只以自訂字串 downgraded 模擬 R8，沒有以結構化 accepted=false／blocking=false 或 review-correction → withdrawn 走過分類器；16/16 無法證明這些分支。
  - disposition：至少加入每格的斷言，特別是 correction 撤回與非 transferred 的降級。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5251999756 · 2026-08-11T10:32:18Z

## 派審：R2（取代前一則）

⚠️ 前一則指向 `1c84a26`，**已過期**。審核對象 **`ruan6047/ai-workflow#22`**（T3，走 [PR #26](https://github.com/ruan6047/ai-workflow/pull/26)）。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-deferred-findings1
分支：claude/WF-ESCALATION-DEFERRED-FINDINGS1
被審 SHA：f63c1c0673c079c2a84f639fb6239a0439ca1b41
基線：origin/main 7451b72ba7679893043950d71bad9642665e25da
iteration：1
```

```bash
git diff 1c84a26..f63c1c0
python3 scripts/replay_escalation_rules.py     # 預期 22/22、exit 0
```

改動 2 檔：`templates/review-escalation.md`（+72／−3 累計）、`scripts/replay_escalation_rules.py`。

### R1-001：選了「承認舊事件不符現行穩定 `finding_id` 契約」

核對原文後錯得比你寫的更明確：`5248812931` 記 R4 剩餘僅 R4-001「待 R5 複驗」，`5249003956` 的趨勢表寫 **「R5｜2｜新 1｜再開 1（R4-001）」**——**R5-001 就是 R4-001 換號重開**。執行者上一版還把虛構包裝成一段看似嚴謹的推導（「R6 只有 3 blocking 故 R4-001 必然已閉合」），而該推導的前提本身就錯。

**不定義承接關係的四點理由**：

1. §2 本就要求 `finding_id` 為 stable id、§5 明文以穩定 id 跨 attempt 推導——**換號重開已被既有要求排除，是契約違反而非缺一種語意**；
2. 定義承接會新增三條語意軸（舊 id 算不算閉合／occurrence 是否重複計／carry 成員資格是否移轉），正是 #16 的覆轍；
3. **契約的 fail-closed 預設對真實換號重開已給出正確答案**——舊 id 落「未提及」→ 觸發，因為換號重開與置之不理在留痕上無法區分，兩者都該擋；
4. cutover 前歷史本就歸 §5 既有的 `contract-baseline`，legacy 不是新發明的出口。

**執行者的一項自查修正**：正規化**自承接輪之後才生效**——R5 明列 R4-001 仍 open 是真實表態，不該被 legacy 蓋掉。故 C@R5 顯示「仍開啟」、C@R6 起才 legacy。另跑「不正規化」變體【構造】證明舊 id 落「未提及」而 fail-closed。

### R1-002：每一格的斷言 ＋ 768 組列舉

finding 改為結構化 record，**全部走 `classify()`**，不再有繞過分類器的自訂字串。

| 格 | 案例來源 |
|---|---|
| `resolved` | 事實（R1-001 於 R2 明列） |
| `withdrawn` | **構造**（`review-correction` 撤回，#16 未發生） |
| 已非有效 open | 事實（R8 transferred 降 info／blocking=false） |
| 已非有效 open | **構造** ×3：`accepted=false`／`attribution` 不符 §3 第 4 款／`finding_class` 不符第 3 款——**皆非 `transferred`** |
| 仍開啟 | 事實（R5 明列 R4-001） |
| deferred | 事實（C@R3 宣告） |
| 未提及 | 事實 ＋ **構造**（defer 已宣告但必要條件不成立） |

**外加全函數證明**：六格寫成六個獨立述詞逐字對應 §4 表格與優先序句，列舉 `status(3) × accepted × blocking × finding_class × attribution × 明列仍open × 宣告defer × 上輪已defer × defer合法` = **768 組**，每組斷言恰好一個述詞命中、且分類器結果等於該述詞。

### PM 已獨立複驗

從分支取出腳本、於 repo 外直接執行：**22/22 通過、exit 0**；「列舉組合數：768」、「未被任何案例走過的格：無」、C@R5 顯示「仍開啟」、C@R6 顯示 legacy、不正規化變體落「未提及」——**皆與宣稱相符**。`cli` pytest 292 passed（未動 CLI）。

### 本輪請攻擊這四點

1. **768 組的參數空間是否就是真實輸入空間。** 這是本輪最強的宣稱，也最值得打：**列舉的九個軸有沒有漏掉任何會影響分類的輸入維度**？例如 `escalation_epoch`、同一 finding 在同輪出現兩次、`root_cause_id` 是否參與分類？若有第十個軸，768 就只是一個大數字。
2. **六個述詞是否真的「逐字對應」條文。** 述詞是執行者自己寫的，**與條文的對應由他自己宣稱**。請逐條比對述詞與 §4 表格／優先序句，確認沒有在述詞裡偷偷放寬或收緊。
3. **legacy 正規化「自承接輪之後才生效」的邊界。** 這是執行者自查加的。請判斷：若某舊 id 在承接輪**之後**又被明列表態（例如 R7 突然提到 R4-001），會落哪一格？正規化會不會蓋掉它？
4. **構造案例的標示是否誠實。** 六格中有五個案例是構造的。請確認每個構造案例都**真的可能發生於條文允許的世界**，而不是為了填格而造的不可能輸入。

### 揭露

- 前一版把虛構的 `resolved` 包裝成推導——**執行者這次自陳「更糟的是我把虛構包裝成一段看似嚴謹的推導」**。請據此加重懷疑本輪所有「因此可推出」形式的論證。
- 本輪 2 檔改動與資源宣告一致（`op 444f248d` 已含 `scripts/replay_escalation_rules.py`）。
- 前一輪你確認的兩點（「不採三個連續 attempt」正確、六格不需第七出口）**本輪未改動**。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。留言紀律：**不得讓任何一行以 `<!--` 緊接事件 marker 前綴起始**。

**若能留 receipt marker 收據**（`card_id`、完整 `source_sha`、報告原文 UTF-8 `report_sha256`），PM 會重算比對，可把來源從「不可驗證」升為可驗證——前一輪為純 PM 轉錄。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊。**R1-001／R1-002 請各自明列 `resolved`／`withdrawn`／仍開啟。**


## Comment 5252279002 · 2026-08-11T11:01:18Z

<!-- wf-review-event:v1 card_id=WF-ESCALATION-DEFERRED-FINDINGS1 source_sha=f63c1c0673c079c2a84f639fb6239a0439ca1b41 attempt_id=WF-ESCALATION-DEFERRED-FINDINGS1-e0-f63c1c0673c079c2a84f639fb6239a0439ca1b41 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-ESCALATION-DEFERRED-FINDINGS1`　attempt_id：`WF-ESCALATION-DEFERRED-FINDINGS1-e0-f63c1c0673c079c2a84f639fb6239a0439ca1b41`
- 查核者：跨家族查核（需求方於對話中轉貼原文；查核者聲明未寫入 PR／Issue 故無 receipt marker，來源不可驗證）　escalation_epoch：0
- source_sha：`f63c1c0673c079c2a84f639fb6239a0439ca1b41`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-11T19:01:17+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git status --short`
  - source_sha 為 f63c1c0673c079c2a84f639fb6239a0439ca1b41，工作區乾淨。
- `python3 scripts/replay_escalation_rules.py`
  - 22/22 通過、exit 0；但通過依賴與原始 issue 16 留痕不符的 defer 轉錄。
- `gh api repos/ruan6047/ai-workflow/issues/comments/5248665281 -q .body`
  - 原始 C@R3 deferred_findings 僅列 R2-001、R2-002，未列 R1-002、R1-006。
- `crafted R7 legacy probe`
  - legacy 正規化啟用時，R7 對 R4-001 的明列 open 被抹除；未正規化時才落「仍開啟」。

### findings（3，其中 blocking 3）

- **WF-ESCALATION-DEFERRED-FINDINGS1-R2-001**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`replay-fixture-invents-deferred-dispositions`
  - evidence：scripts/replay_escalation_rules.py:222 將 R1-002、R1-006、R2-001、R2-002 全部設為 C@R3 deferred。原始 issue 16 comment 5248665281 實際只列 R2-001、 R2-002；因此 C@R3 的前兩項仍應落「未提及」並強制 escalate。 腳本所稱「四項 carry 全部 deferred」及修訂後 C@R3 不強制，並非實際事件流回放。
  - disposition：依原始事件重建 fixture；若歷史事件不符合新 deferred schema，明確標為 legacy， 不得以補造 defer 使回放通過。補上能在少一筆 defer 時失敗的測試。
- **WF-ESCALATION-DEFERRED-FINDINGS1-R2-002**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`legacy-normalization-suppresses-later-stable-id-evidence`
  - evidence：scripts/replay_escalation_rules.py:240-249、267-270、295-297 在 R5 後無條件把 R4-001 設為 superseded-legacy，並直接寫入「legacy（不套用六格）」而繞過 classify()。構造 R7 再明列 R4-001 open 時，正規化版本完全不輸出 R4-001； 未正規化版本才正確落「仍開啟」。這違反 review-escalation.md 第 4 節對舊 id 明列表態應依 stable finding_id 處理的 fail-closed 原則。
  - disposition：legacy cutover 僅能排除 cutover 前事件被新契約追溯裁決，不能建立會覆蓋後續 明列表態的 supersession。移除該捷徑，或將 legacy 資料與新契約 replay 完全隔離。
- **WF-ESCALATION-DEFERRED-FINDINGS1-R2-003**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`projected-state-enumeration-misstated-as-full-input-proof`
  - evidence：prove_partition() 只枚舉 classify() 已縮約的 f、mentioned_open、defer_ok， 並把所有 defer 必要條件合併為單一 wellformed bit；未涵蓋 finding 是否屬 carry、 epoch 邊界、同一 finding 的衝突事件與 review-correction 順序，以及同 SHA 多 reviewer 合併後必須 fail loud 的輸入。finding_class 與 attribution 亦各只取一個 合格、一個不合格代表值。故 768 僅證明縮約函數的分割，不是真實輸入空間的 全函數證明。
  - disposition：將宣稱收斂為「分類器投影空間」；或以事件層資料模型列舉與測試所有會影響 checkpoint 與 fail-loud gate 的維度，並逐項驗證五個 defer 必要條件。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5255216570 · 2026-08-11T15:27:02Z

## escalation-checkpoint（第三個可計數 attempt 前）

### 第二條件成立

R1 的 accepted blocking 為 R1-001（`succession-encoded-as-closure`）與 R1-002（`cell-coverage-not-executable`）。R2 的查核報告**完全未提及這兩項**，故兩者皆未被明列 `resolved` 或 `withdrawn`。依 `review-escalation.md` §4 末段，`checkpoint_decision` 只能是 `escalate`，不得信任手填的 `continue`。

第一條件（同根因跨三個唯一可計數 attempt）未成立：R2 的三個 `root_cause_id` 與 R1 的兩個皆不相同。**但形態上有承接關係**——R2-002（`legacy-normalization-suppresses-later-stable-id-evidence`）與 R1-001 都是「把承接／重編號當成閉合」，R2-003（`projected-state-enumeration-misstated-as-full-input-proof`）與 R1-002 都是「覆蓋宣稱大於實際被執行的分支」。若查核者認為應併為同族，計數即為 2／3；請於下輪裁示，我不自行合併。

### 這次觸發的歸因，有一部分是我的

`review-escalation.md` §4 的判準是「事件流上有沒有那個宣告」，不是「為什麼沒有」，所以條件照樣成立。但成因要講清楚：**R2 的派審詞沒有要求查核者逐項回報前輪 finding 的閉環狀態**，前幾輪的派審詞有這條。報告因此沒有那一節。

同一件事今天在 [#21](https://github.com/ruan6047/ai-workflow/issues/21) 也發生了一次（見該卡 checkpoint）。**兩次都是 coordinator 的派工缺漏，不是執行者連續失敗**——這正是本卡自己要解決的問題形態：門檻被合法的流程變動誤觸。本卡的射程裡應該涵蓋這種情形的表示法，若現行草案沒有涵蓋，那本身就是一個 finding。

### 裁定

```yaml
checkpoint_decision: escalate
escalation_resolution: continue
checkpoint_rationale: |
  第二條件成立（R1-001／R1-002 未在 R2 報告中明列 resolved 或 withdrawn），
  故 checkpoint_decision 只能是 escalate。需求方裁定 continue，維持同執行者角色
  （Claude Opus 5@Claude Code 子 agent），不換人、不切卡。
  依據：三項 blocking 全是具體可修的證據問題（fixture 與原始事件不符、legacy 捷徑
  會壓掉後續明列表態、768 是投影空間非輸入空間），不是設計層僵局；且本次門檻觸發
  歸因於 coordinator 的派審詞缺漏，不反映執行者連續失敗。
decided_by: ruan6047（需求方）
counts_toward_escalation: true
attempts_so_far: 2
```

### 下一輪派審詞的強制項

1. **必須逐項回報前輪 finding 的閉環狀態**（`resolved`／`withdrawn`／仍開啟），缺此節即 `review-invalid`。此條已從派審範本漏掉兩次，本輪起不得再漏。
2. 必須要求查核者填齊 `severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id`。
3. 留言紀律：**不得在留言中出現事件 marker 的字面前綴**，連散文引用與 code fence 示範都不行（`doctor` 以全文子字串比對，命中即隔離整卡）。需要指涉時拆開書寫。


## Comment 5255484802 · 2026-08-11T15:49:54Z

## PM：五張卡同時送審前的跨卡對帳

本則同時貼在 #21／#22／#23／#24／#25。五張卡本輪都改完並各自通過自己的驗證，但**它們彼此的介面沒有被任何一方檢查過**——每張卡的執行者都只看自己的射程。以下是 PM 在送審前做的交叉檢查，逐項附重現方式。

**這些不是 finding。** PM 不是查核者，以下只是**指定查驗項**：把 PM 觀察到的矛盾指出來，由各卡的查核者判斷它是不是問題、屬誰的問題。PM 刻意不代任何一方修正——#23 §10 明文寫著「刻意不猜測 #24 會怎麼改」，我現在替它填上就是把設計判斷從查核者手上拿走。

### 檢查方法

- **寫入集**：以 #16 §7.2 裁定的**階層路徑包含**語意（正規化路徑相等或其一為另一之祖先目錄），對 Project #4 全部 27 張有資源宣告的活卡做兩兩比對。**不是**現行 `resources.py` `find_conflicts` 的逐字串比對——後者的不足正是 #24 的射程。
- **設計面**：逐一驗證各卡對其他卡寫下的明示假設，以及「同一個物件被兩張卡從不同方向改動」的情形。

---

### 一、寫入集：四組相交，其中一組現在就成立

| 撞的兩張 | 相交處 | 狀態 |
|---|---|---|
| **#22（🚧進行中）× #16（⏸阻塞）** | `templates/review-escalation.md` ⊂ `templates/` | **現在成立** |
| `WF-22-CLI4`（📥Backlog） | `cli/` ⊃ #21 與 #25 的**每一個**檔案 | 潛伏 |
| `WF-CLI-TIER-MUTATION1`（📥Backlog） | `cli/src/wf_cli/` ⊃ #21 與 #25 多數檔案 | 潛伏 |
| `WF-24-EVIDENCE-STRENGTH1`（📥Backlog）× #16 | `templates/dispatch-package.md` ⊂ `templates/` | 潛伏 |

**第一列是 PM 的違反，先說清楚。** 我今天派 #22 時，#16 正持有整個 `templates/`。依 #16 §7.2 自己的裁定，那次 `assign` 應該被擋；沒被擋是因為 `find_conflicts` 現行只做逐字串比對。此條件先前已查證並記錄（`amend` op d32f8a3a），不是新發現——但它現在是**「正在設計互斥語意的那批卡自己違反該語意」的活體樣本**，且是在真實流程中自然發生的，不是構造出來的。

`WF-22-CLI4` 宣告整個 `cli/` 這件事值得單獨看：它一旦被派工，#21 與 #25 就全數動不了；反過來說，#21／#25 在途期間 `WF-22-CLI4` 也不可派。目錄級宣告與檔案級宣告混用的代價，在這裡是可量化的。

**指定查驗項（#24）**：文件的立即階段與目標階段規則，套在上表這四組真實資料上，各自會得到什麼結果？§8.5 釘住的「立即階段獨有的過度拒絕 10 對」是否涵蓋這幾組？

---

### 二、#23 §10 的四項假設，A2 與 A3 現在可以判定，而且都不成立

#23 §10 把對 #24 的依賴寫成四項待驗假設，明文「刻意不對齊，讓差異在查核時暴露」。**兩張卡都交付了，所以現在可以驗——結果是負的。**

**A3 失敗，而且是域不相容，不是覆蓋不足。**

#24 §3.1 規則 1 定義封閉 namespace 為「卡所屬 **repo 根**的相對路徑」，規則 2 拒收以 `/` 起始者、規則 3 拒收以 `~` 起始者、規則 4 拒收任一分量為 `..` 者。

而 #23 §4.4 分類器 `PATH` 集合的七個參數（`--worktree`、`--repo-path`、`--config`、`--input`、`--out-dir`、`--spec-dir`、`repo_root`）是 **CLI 引數**，實務上多半是絕對路徑——本專案的派工詞逐輪都寫 `--repo-path /Users/ruanruan/Dev/ai-workflow`。**這些字串在 #24 的規則 2 下會被逐一拒收。**

兩者的定義域不同：#24 管的是**卡面宣告字串**，#23 要的是**命令列引數**。A3 寫成「是否涵蓋全部七個參數」，隱含了兩者同域的前提，而該前提不成立。

**A2 也不成立。**

#24 §3.1 規則 8 明文「宣告以位元組原樣**儲存**；**比對**時 casefold」，規則 9 為「**比對前**做 NFC」。也就是 `K(r)` 是**比對鍵**，不是儲存形式；且 #24 從不解析 cwd（一律 repo 根相對）、也從不解析 symlink（§5 直接拒收）。它提供的是**集合成員判定**，不是 A2 要求的「同一邏輯路徑在不同 cwd、不同 symlink 解析狀態下產生同一個字串」。

**A1 成立**（#24 對無法解析者確實 fail-closed），但附帶一個具名豁免（`--ignore-unparseable`，33 張母體，sunset 2026-09-30）——該豁免處理的是**別卡宣告解析失敗**，與 A1 所問的**路徑正規化**不同域，請查核者確認 A1 問的是不是它該問的那件事。

**後果**：依 #23 §10 自己的降級規則，路徑型別應落回 §4.2 收尾規則（該動詞退出冪等保護、stderr 明示）——而且是**現在就該落**，不是繼續掛在 §10 當待驗假設。

**指定查驗項（#23）**：§4.1 的路徑型別列是否應直接改寫為降級後的形式？§10 的呈現方式是否應從「假設待驗」改為「已驗、A2／A3 不成立」？
**指定查驗項（#24）**：是否應明文宣告本卡的封閉 namespace **不涵蓋 CLI 引數**，以免其他卡再度誤引？

---

### 三、#25 與 #23 從兩邊改同一個動詞，互不知情

#25 本輪把破壞性收尾接上 `handoff --next-stage release --cleanup`。
#23 §7.1.2 的逐動詞稽核判 **`handoff` 的首寫不合格**（首寫是 owner 欄位，非載荷可攜），並據此判定該動詞的 E1 不成立。

PM 以 `grep` 核對兩份文件：**#25 全文未出現 `#23`、`event_id`、「冪等」；#23 全文未出現 `#25`、`release`、`cleanup`。** 兩張卡在同一個動詞上從相反方向動手，而彼此的文件都沒有對方。

具體後果（PM 逐行追過 `handoff_cmd.py` 的效果順序）：`release --cleanup` 成功路徑為 `owner` → `交付狀態` → `最後交接` → `iteration` → Issue body Log。**清理已完成、owner 已寫、但在 Log 寫入前崩潰**時，事件流上沒有任何能辨識這次寫入的記號——那正是 #23 E1 要解決的東西，而 #23 判定 `handoff` 不具備。

#25 的 resume 是**觀測式**的（重讀當下事實），所以不會重複刪除，這一點是安全的。但狀態面會停在「終態已寫、Log 缺行」的組合，而兩張卡都沒有在處理它。#25 §9 自承的第 2 項（effect writer 回報成功後未回頭重讀狀態面）與此同族但不同一件事。

**指定查驗項（#25）**：接線後 `handoff` 的首寫不自描述，是否使 #25 §9 第 2 項的殘留風險升級？卡面是否應引用 #23 §7.1.2 並標為外部相依？
**指定查驗項（#23）**：§7.1.2 判 `handoff` 不合格時，`handoff` 尚無破壞性效果；#25 落地後該判定的**後果嚴重度**是否改變？§11「在 A′ 落地前這三個動詞的 E1 不成立」是否需要加註破壞性路徑？

---

### 四、#22 的新出口，回溯涵蓋了今天兩個 checkpoint 的觸發成因

#22 本輪在 `review-escalation.md` §4 新增 `defer_cause: instruction-omitted`——「派審指示漏了要求查核者逐項回報前輪 finding 的閉環狀態」。

**今天 #21 與 #22 各自的 escalation checkpoint，觸發成因正是這個。** 兩次都是 PM 的派審詞缺漏（見 `#issuecomment-5253853989`、`#issuecomment-5255216570`，兩則都已載明歸因）。

這構成一個要請查核者特別看的形狀：**本卡的交付物，為本卡自己的 escalation 觸發提供了出口。**

減輕因素有兩個，請一併評估是否足夠：§4 第 2、3 款要求 `deferred_by` 逐字等於卡面「需求：」欄帳號，且不得等於本卡當前 owner 或本 epoch 任一 reviewer——**裁定者必須是需求方**，執行者不能自行 defer。以及「不得連續 defer」未放寬。

但執行者自承的洞 3 指出：**沒有任何檢查會去讀 `defer_ruling_url` 指向的那則指示、確認它真的漏了那一節。** 成因在機械上退化為「從封閉列舉挑一個」。

**指定查驗項（#22）**：`instruction-omitted` 的必要條件是否足以防止它成為通用免責？第 2、3 款排除了 owner 與 reviewer，但**未排除 Coordinator**——而缺漏正是 Coordinator 造成的；`deferred_by` 須為需求方是否已足夠隔離？

---

### 五、#22 卡面驗證條文與交付的落差（需要需求方裁定，非查核者可獨斷）

#22 執行者回報：卡面的兩項驗證條文（deferred 出口使 R4 前不強制、條件 1 在 R8 失效）**在 #16 的忠實事件流上不成立**，原因是 #16 有三處換號重開（R1-002→R2-001、R1-006→R2-002、R4-001→R5-001），依「六格的前提是穩定 `finding_id`」不構成處置。執行者未補造 defer 使其通過，改以「#16 的穩定 id 最小改寫」承擔該兩項，並明確標為構造。

**這是誠實的處置，但它使卡面驗證條文與實際被驗證的對象不再是同一個東西。** 依既有紀律，改動驗收／驗證條文是 PM 走 `amend`、不是執行者；而是否接受這個替代承擔，是需求方的判斷。**PM 刻意不先 `amend`**——先改條文再送審，等於讓卡面去追交付，那是倒過來的。

**指定查驗項（#22）**：「穩定 id 最小改寫」是否為該兩項驗證條文的正當替代？若否，該兩項應判為未滿足（`attribution: planner`，卡面條文本身建立在錯誤前提上）。

---

### PM 已獨立複驗的事項（不構成背書，只是把可機械核對的部分先做掉）

- 五張卡本輪變更的檔案**全部落在各自資源宣告內**；`test_commands_mocked.py`（#21 持有）未被 #25 觸碰。
- 測試：#21 `437 passed`、#25 `367 passed`、#22 replay `44/44`＋`cli` 292 passed（與基線同）；#23／#24 為設計卡，內嵌探針可原樣重跑。
- #21 的 R5-001 攻擊獨立重現：查核者的 `U+02B0`／`U+0378` 兩案例現皆 `ambiguous`，另測 ZWSP／私用區 `U+E000`／emoji／反斜線亦 `ambiguous`，單條對照仍 `matched`。
- #25 的 TOCTOU 守衛獨立突變：把二次確認的 verdict 強制為放行，**8 個測試轉紅**（含該 TOCTOU 回歸與狀態面測試），斷言非空；worktree 已還原乾淨。
- #24 的兩張不可解析卡（`cpbl-analytics#60`／`#66`）body 已由 PM 直接讀取核對：確為 MIG1 佔位區塊（有 fenced JSON、無 sentinel），且 `#66` 的佔位 `db_scope` 為 `write`。
- #22 的 fixture 已對原始留言 `5248665281` 核對：`deferred_findings` 逐字只有兩筆，未被補造。


## Comment 5255778571 · 2026-08-11T16:16:04Z

## ⚠️ 告知查核者：本卡在 🔍待查核 期間被修訂過卡面

`amend` op `4f5bf962`，**只動「驗證」一欄**，時間在本卡進入 `🔍待查核`（`b3663a5`）之後。**改的是驗收標準本身，不是交付物**，所以你現在看到的卡面與執行者交付當下看到的不完全相同。這件事必須讓你知道，由你判斷是否影響裁決。

### 改了什麼

前兩項驗證（deferred 出口使 R4 前不強制、第一條件在 R8 失效）各加註一句：**得以「#16 的穩定 `finding_id` 最小改寫流」承擔**，且構造流須明確標為構造、忠實流結果須一併如實呈現。後兩項一字未改。

### 為什麼

執行者交付時回報：該兩項**在 #16 的忠實事件流上不可能成立**——#16 實際有三處換號重開（R1-002→R2-001、R1-006→R2-002、R4-001→R5-001），依六格「前提是穩定 `finding_id`」，換號重開不構成處置，所以無論怎麼修都達不到條文要求的結果。他**沒有補造 defer 讓它通過**，而是改用構造流承擔並標明。

需求方於 2026-08-12 裁定：**這是卡面條文建立在錯誤前提上（`attribution: planner`），不得要求執行者補造證據使其通過。**

### 這次裁定沒有裁的部分

需求方**只裁原則**——「構造流可以作為證據」。**「這個構造是否忠實」完全由你判定，未被預先認定。** 具體可查：三處換號的改寫是否只改了 id 而未改實質（同樣輪次、同樣再開、同樣 transferred 處置）？構造流的結論與忠實流的差異，是否已在腳本輸出中如實並列而非只呈現有利的那一邊？

若你認為構造流根本不能承擔這兩項，請直接判該兩項未滿足並歸 `planner`——需求方的裁定是關於證據形式的取捨，不是關於你的判斷結論。

### PM 自承

中途改卡面本身是有問題的動作（`ai-workflow#12` 正在處理「開卡後欄位不可改」）。替代方案是不動卡面、只貼裁定留言，差別在你看到的是「條文已改」還是「條文沒改但另有裁定」。需求方選了前者。**原值已完整寫入 Log，可逐字比對。**


## Comment 5255924737 · 2026-08-11T16:29:41Z

## 派審：#22 `WF-ESCALATION-DEFERRED-FINDINGS1` R3

⚠️ 審核對象是 **`ruan6047/ai-workflow#22`**，**不是 `cpbl-analytics#22`**。工作目標 repo 是 `ai-workflow`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-deferred-findings1
分支：claude/WF-ESCALATION-DEFERRED-FINDINGS1
被審 SHA：b3663a5835f0792e650cce8ebf724f4df5db7e74
基線：origin/main 0d4d282
iteration：3
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-deferred-findings1
git rev-parse HEAD && git status --short && git diff --check
git diff f63c1c0..b3663a5 -- templates/review-escalation.md   # 契約 +18/-11
git diff f63c1c0..b3663a5 -- scripts/replay_escalation_rules.py
python3 scripts/replay_escalation_rules.py
```

**請先讀本 Issue 的兩則留言**：escalation checkpoint（`#issuecomment-5255216570`）與**卡面中途修訂告知**（`#issuecomment-5255778571`）。後者尤其重要——**本卡在 `🔍待查核` 期間被改過驗收標準**，你必須知道並判斷是否影響裁決。

### 一、複驗三項 blocking

- **R2-001（fixture 捏造 deferred）**：依 `gh api` 取回 comment `5248665281` 重建，PM 已逐字核對原文 `deferred_findings` 確實只有 `R2-001`／`R2-002` 兩筆。**結果如實：修訂後條文下 C@R3 仍強制 escalate**（carry set 四筆，`R1-002`／`R1-006` 在 R2 被換號重開故落「未提及」），C@R8 第一條件仍為 TRUE。執行者**沒有補造**第三、四筆 defer。新增四種敏感度測試各自使該筆失效。
- **R2-002（legacy 正規化壓掉後續表態）**：`LEGACY_SUPERSEDED`、`normalize_legacy` 與繞過 `classify()` 的分支**整段移除**，無任何 supersession 捷徑。收下你構造的 R7 探針：`R4-001` 現正確落「仍開啟」，且另有斷言確認它在 C@R5–C@R8 每個 checkpoint 的 carry 分類都有輸出。
- **R2-003（768 是投影空間）**：選**收斂宣稱**這條路，改為「分類器在其宣告值域上是一個分割」並於執行時**原樣印出不涵蓋清單**。投影空間本身列舉完整：`finding_class`／`attribution` 由各兩代表值展開為全部五值、defer 必要條件由單一 `wellformed` bit 拆為七款逐項（153,600 點），另附逐款必要性驗證。

請攻擊 R2-003 的取捨：執行者選收斂而非擴大，理由是「事件層完整輸入空間包含 §2 的衝突裁決 gate 與同 SHA 多 reviewer 合併，那是另一台機器，硬塞進回放腳本會製造第二個『宣稱大於實作』的機會」。**這個理由成立，還是它剛好也是最省事的那條路？** 現在明確聲明未涵蓋的兩項（衝突事件、多 reviewer fail loud），是否有一項其實可以被涵蓋而只是沒做。

### 二、前輪兩項的閉環，請抽驗

執行者判 R1-001 與 R1-002 皆 `resolved`。

R1-001 的閉環附了一句值得注意的自陳：**`f63c1c0` 的修法（legacy 正規化）雖然移除了虛構的 `resolved`，卻以另一形態重演同一根因**——用一個承接關係覆蓋後續事實，那正是 R2-002。本輪把承接關係整個移除，這一族才真正關掉。**請驗證這個「這次才真的關掉」的宣稱**，因為同樣的話上一輪也講過。

### 三、本卡射程內的新增，也是最需要你判斷的一件

草案原本只有 `spec-narrowed` 一種 defer 成因，**一次「派審指示疏漏」無出口可走**。本輪新增 `defer_cause` 為必填、取值 `spec-narrowed`｜`instruction-omitted`。

**這裡有一個你必須看的形狀：本卡的交付物，正好為本卡自己的 escalation 觸發提供了出口。**

今日 #21 與本卡各自的 escalation checkpoint，觸發成因都是**派審詞缺漏**（PM 沒有要求查核者逐項回報前輪 finding 閉環狀態），兩則 checkpoint 都已載明歸因。

減輕因素請一併評估是否足夠：§4 第 2、3 款要求 `deferred_by` 逐字等於卡面「需求：」欄帳號，且**不得等於本卡當前 owner 或本 epoch 任一 reviewer**——裁定者必須是需求方，執行者不能自行 defer；「不得連續 defer」未放寬。

但執行者自承：**沒有任何檢查會去讀 `defer_ruling_url` 指向的那則指示、確認它真的漏了那一節**，成因在機械上退化為「從封閉列舉挑一個」。而第 2、3 款排除了 owner 與 reviewer，**未排除 Coordinator**——而缺漏正是 Coordinator 造成的。請判斷 `deferred_by` 須為需求方是否已足夠隔離。

### 四、卡面驗證條文在 🔍待查核 期間被改過（需求方裁定）

執行者回報：卡面前兩項驗證（deferred 出口使 R4 前不強制、條件 1 在 R8 失效）**在 #16 的忠實事件流上不可能成立**——#16 實際有三處換號重開（R1-002→R2-001、R1-006→R2-002、R4-001→R5-001），依六格「前提是穩定 `finding_id`」，換號重開不構成處置。他未補造 defer 使其通過，改以「#16 穩定 id 最小改寫流」承擔並明確標為構造。

需求方 2026-08-12 裁定：**這是卡面條文建立在錯誤前提上（`attribution: planner`），構造流可作為證據**；並以 `amend` op `4f5bf962` 把該裁定寫進驗證欄（原值完整寫入 Log，可逐字比對）。

**需求方只裁了原則，沒有裁事實。「這個構造是否忠實」完全由你判定。** 具體可查：三處換號的改寫是否只改了 id 而未改實質（同樣輪次、同樣再開、同樣 transferred 處置）？構造流與忠實流的差異是否已在腳本輸出中如實並列，而非只呈現有利的那一邊？**若你認為構造流根本不能承擔這兩項，請直接判未滿足並歸 `planner`**——需求方的裁定是關於證據形式，不是關於你的結論。

### 五、執行者主動揭露

- **執行者是 Claude Opus 5@Claude Code 的子 agent，PM 亦為 Claude Opus 5。** 你必須是**不同模型家族**。
- 執行者自承六個未關的洞，其中兩個值得特別看：**回放引擎是契約的第二個實作，不是 adapter**——`wfcli` 仍無 checkpoint writer（[#9](https://github.com/ruan6047/ai-workflow/issues/9)），所以線上沒有任何機械強制，腳本證明的是規則自洽，不是系統遵守；以及 **attempt 是否 counted 是引擎的輸入而非由 §3 導出**，所以 §3 的推導在本腳本裡未被驗證。
- 驗證數字：replay `44/44` exit 0（PM 已獨立重跑相符）、`cli` pytest 292 passed 與基線同。變更只有兩支宣告內檔案。

### 環境紅線

唯讀查核；**不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行任何有副作用的 `wfcli` 命令**（`--validate-only` 與 `doctor` 唯讀可以；讀 GitHub 的 `gh api`／`gh issue view` 唯讀可以，你會需要它取原始事件）。

**留言紀律（重要，本卡尤其容易踩）**：你的留言中**不得出現事件 marker 的字面前綴**（即 `wf-review-event` 後面直接接半形冒號），連散文引用與 code fence 示範都不行——`doctor` 以全文子字串比對，命中即隔離整張卡的查核通道（#21 已因此被鎖）。**本卡會讓你大量引用 review event 內容**，取原始留言時用 `gh api` 讀進來處理即可，不要把前綴字面寫進報告。發文前 `grep` 一次。

### 輸出

依 `templates/review-prompt.md` §5 的結構化區塊，`core_pain_resolved` 與 `self_run` 必填。**額外強制兩項**：

1. **逐項回報前輪 finding 的閉環狀態**——R2-001、R2-002、R2-003 各自明列 `resolved`／`withdrawn`／仍開啟，缺此節即 `review-invalid`。**上一輪漏了這一節，直接造成本卡的 escalation checkpoint 被觸發**——而那正是本卡要解決的問題形態。
2. **`severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id` 五欄請你自己填**，不要留給 PM 事後指派——`root_cause_id` 直接影響門檻計數。


## Comment 5256205257 · 2026-08-11T16:54:36Z

## PM 更正：五份派審詞的基線 SHA 全部寫錯

本則同時貼在 #21／#22／#23／#24／#25。

### 事實

五份派審詞都寫「基線：`origin/main` `0d4d282`」。**`0d4d282` 不是任何一張卡的祖先。**

```
wf-cleanup-guard1                  0d4d282=非祖先  merge-base=7451b72
wf-cli-routing-tier1               0d4d282=非祖先  merge-base=7451b72
wf-escalation-deferred-findings1   0d4d282=非祖先  merge-base=7451b72
wf-event-idempotency1              0d4d282=非祖先  merge-base=7451b72
wf-resource-writeset1              0d4d282=非祖先  merge-base=7451b72
```

**正確的共同基線是 `7451b72ba7679893043950d71bad9642665e25da`。**

`0d4d282` 是 `Merge pull request #29 from ruan6047/claude/OPS-CLEANUP-SMOKE1`——**我自己在派審前一小時跑 #25 端到端實跑時產生的 merge**。五張卡都在那之前分支，所以它們當然不是它的後代。我在寫派審詞時直接抄了當下的 `origin/main`，沒有回頭確認它與被審分支的祖先關係。

### 後果

**這使 [#23](https://github.com/ruan6047/ai-workflow/issues/23) 的查核者判定 `review-invalid` 而未進實質查核。** 那個判定依派審詞的字面是正確的——`git merge-base --is-ancestor 0d4d282 1ee62b0` 確實 exit 1。**責任在 Coordinator，不在查核者，也不在執行者。**

另外三位查核者（#21／#22／#24）都各自察覺並自行處理了：#21 明白寫出「實際共同祖先為 7451b72；`0d4d282` 是後續 main」並用 `merge-tree` 確認無衝突；#22 判定「派審指定基線仍為被審 SHA 的祖先，故不構成 review-invalid」——**該句的前半在事實上不成立，但其結論（可以繼續查核）是對的**；#24 在 `git diff --name-status 0d4d282..cb6028fc` 中看到 `tasks/_smoke/OPS-CLEANUP-SMOKE1.md` 被刪除，正確判斷那是基線差異造成的假象而非本輪變更。

**四位查核者裡三位靠自己繞過了我寫壞的指示，一位照著指示停下來。停下來的那位沒有做錯任何事。**

### 處置

- **#23 重新派審**，基線更正為 `7451b72`，被審 SHA 不變（`1ee62b0`）。該卡的 `review-invalid` **不計 iteration、不寫 review event、不改交付狀態**（`review-escalation.md` §1）。
- #21／#22／#24／#25 的查核**不因此失效**——四位都已對正確的變更範圍實跑，基線錯誤只影響 `git diff` 的顯示範圍，未影響被審 SHA 與其變更內容。
- 此後派審詞的基線一律以 `git merge-base <origin/main> <source_sha>` 產出，不得直接抄當下的 `origin/main`。

### 這件事的形狀

派審詞裡的「基線」欄本來就是給查核者用來界定 diff 範圍的座標。**我把一個更新的 main 當成基線，而那個 main 之所以更新，正是因為我自己剛在上面 merge 了東西。** 這與本批卡片反覆處理的問題同源：一個需要對照既有事實才能填的欄位，用當下手邊最方便的值填掉。


## Comment 5256233337 · 2026-08-11T16:57:12Z

<!-- wf-review-event:v1 card_id=WF-ESCALATION-DEFERRED-FINDINGS1 source_sha=b3663a5835f0792e650cce8ebf724f4df5db7e74 attempt_id=WF-ESCALATION-DEFERRED-FINDINGS1-e0-b3663a5835f0792e650cce8ebf724f4df5db7e74 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-ESCALATION-DEFERRED-FINDINGS1`　attempt_id：`WF-ESCALATION-DEFERRED-FINDINGS1-e0-b3663a5835f0792e650cce8ebf724f4df5db7e74`
- 查核者：GPT-5@Codex 子代理（無 receipt marker，來源不可驗證；PM 另將原報告的 > 折疊純量改為 | 以通過解析器）　escalation_epoch：0
- source_sha：`b3663a5835f0792e650cce8ebf724f4df5db7e74`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T00:57:11+08:00

### self_run（查核者實跑）

- `git rev-parse origin/main && git rev-parse HEAD && git status --porcelain=v1 && git diff --check`
  - origin/main=0d4d282ef3bb5eae6e78316a368029ced7ff98db；HEAD=b3663a5835f0792e650cce8ebf724f4df5db7e74；工作區乾淨；diff check 通過。
- `gh issue view 22 --repo ruan6047/ai-workflow --json number,title,body,comments`
  - 取得卡面、最後一則派審、卡面修訂告知與歷次 handoff/review 原始留言。
- `GH_REPO=ruan6047/ai-workflow gh api repos/ruan6047/ai-workflow/issues/comments/{5248665281,5255216570,5255778571,5255484802,5255924737}`
  - 原始事件確認 #16 R4 checkpoint 僅 defer R2-001/R2-002；讀取本卡 checkpoint、卡面修訂及跨卡對帳。
- `python3 scripts/replay_escalation_rules.py`
  - 44/44 通過；忠實 #16 流在 C@R3 及 C@R8 均如實強制 escalate；穩定 ID 最小改寫構造流則通過卡面兩項替代驗證。
- `PYTHONDONTWRITEBYTECODE=1 python3 isolated replay probe`
  - defer_cause=instruction-omitted 搭配預設 defer_reason='規格收窄' 與 https://example/ruling，仍得到 forced=False，三筆皆分類為 deferred。
- `grep reserved-marker check`
  - marker-grep=clean。

### findings（1，其中 blocking 1）

- **WF-ESCALATION-DEFERRED-FINDINGS1-R3-001**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`defer-evidence-not-semantically-validated`
  - evidence：review-escalation.md §4 與 Adapter 欄位要求 instruction-omitted 必須載明哪一則派審指示漏了閉環要求， 且 defer_ruling_url 必須指向該指示；但 replay 的 _defer_conditions 只驗證 cause 是否列舉、reason/url 是否非空。defer_stream(..., cause="instruction-omitted") 使用預設「規格收窄」理由及 example URL， 仍被 assertion 視為合法並放行。這不只是不完整測試，而是交付的「機械可執行」契約沒有把新出口 與其所宣稱的事實相連。
  - disposition：將 instruction-omitted 的有效性改成可機械核對：至少驗證 URL 為本卡派審指示的可解析 GitHub 留言、 原始內容確無逐項閉環要求，並使 reason 與 cause 一致；若 adapter 尚未能讀取該證據，該 cause 應暫不可用 或明列由 #9 實作並以 fail-closed 處理。新增反例：任意 URL、spec-narrowed 理由、或實際含閉環要求的 派審指示，均須落「未提及」並強制 escalate。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5256238141 · 2026-08-11T16:57:40Z

## PM 註記：轉錄本輪裁決時對原報告做的格式轉換

查核者無 `wfcli` 寫入通道，本輪裁決由 PM 逐字轉錄。**轉錄過程中我改動了原報告的兩處格式**，逐一說明。

**一、`evidence` 與 `disposition` 的區塊純量由 `>` 改為 `|`。** 原報告使用折疊純量 `>`，而 `wfcli review` 的解析器明文不支援（`[review] 拒收：區塊純量 '>' 不支援；請改用 | 或 |-`）。**這不是純粹的格式轉換**——`>` 會把換行折成空格，`|` 保留換行，所以轉錄後的字串與查核者寫下的字串**逐位元組不同**，差別在斷行位置。文字內容一字未增減。

**二、`scope_external` 由裸字串序列改為 mapping 序列**（`- "…"` → `- item: "…"`），同樣是解析器只接受 `key: value` 形式。字串內容未變。

**三、無 receipt marker。** 查核者未在 Issue 或 PR 留下收據，故其身分只有 `--reviewer` 欄的自述文字。依 `handoff-contract.md` §3.1.2 末段，**此類 event 在身分維度上等同無佐證**，任何依賴「誰查核的」做判斷的流程都不得單獨採信它。

**四、`report_sha256` 無從重算。** 報告經對話轉貼給 PM，原始位元組（換行形式、尾端空白）不可還原，即使有收據我也無法驗證雜湊相符。

### 為什麼還是寫進去

本輪是 `REQUEST_CHANGES`，方向是把卡退回、不開任何閘門。若是 `APPROVE`，上述四項限制加起來足以讓我不敢單獨轉錄。**這個不對稱是刻意的**：保守方向的裁決容忍證據不足，開閘的裁決不容忍。

若查核者認為第一項的斷行差異影響其原意，請直接指出，PM 會以 `review-correction` 更正。


## Comment 5259553793 · 2026-08-11T22:24:53Z

## 派審：#22 `WF-ESCALATION-DEFERRED-FINDINGS1` R4

⚠️ 審核對象是 **`ruan6047/ai-workflow#22`**，**不是 `cpbl-analytics#22`**。工作目標 repo 是 `ai-workflow`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-deferred-findings1
分支：claude/WF-ESCALATION-DEFERRED-FINDINGS1
被審 SHA：539c3336152881ab74ed91eb38735acc910f961d
基線：7451b72ba7679893043950d71bad9642665e25da（= git merge-base origin/main 539c333，已驗證為祖先）
iteration：3
```

> **基線這次是用 `git merge-base` 算出來的。** 上一輪五份派審詞都把基線寫成當下的 `origin/main`（`0d4d282`），而那是 PM 自己跑實跑時產生的 merge。你上一輪判「派審指定基線仍為被審 SHA 的祖先，故不構成 review-invalid」——**該句的前半在事實上不成立，但你的結論（可以繼續查核）是對的**。詳見本 Issue 的「PM 更正」留言。

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-deferred-findings1
git rev-parse HEAD && git status --short && git diff --check
git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD && echo "基線成立"
git diff b3663a5..539c333 -- templates/review-escalation.md
python3 scripts/replay_escalation_rules.py
```

### 一、複驗 R3-001

你的判詞是：「這不只是不完整測試，而是交付的『機械可執行』契約沒有把新出口與其所宣稱的事實相連。」

處置：`defer` 必要條件由 5 款擴為 7 款，`instruction-omitted` 另需專節三款全部成立。

- **第 5 款**：`defer_ruling_url` 須解析為**本卡 issue 的單一留言 URL**（`…/issues/<本卡編號>#issuecomment-<數字>`）。站外任意 URL、他卡 URL、非留言資源一律無效。
- **第 6 款（新）**：`defer_reason` 須**逐字含**第 5 款解析出的數字 id。把「載明對應的那一次事件」從人讀措辭變成可比對的指涉；**散文本身不再是判準**。
- **專節 (a) 指認**：事件流上須有本 epoch 的派審事件，其 `review_prompt_url` 逐字等於 `defer_ruling_url`，且它派的正是 **trigger attempt N 的查核**（指向前幾輪不算）。
- **專節 (b) 缺漏的結構化宣告**：該派審事件須帶 `closure_reporting_requested` 且**恰為 `false`**（缺欄、`true`、無法判定皆無效）。理由是 `review-prompt.md` §6 已把逐項閉環定為 R2 以後的固定範圍，故該欄記錄的是**一次偏離範本**，應在派審當下寫下、不由受益方事後推定。
- **專節 (c) 可用性**：寫入通道未產出 (a)(b)、或 adapter 無法解析時，本 cause **不可用**，每筆 defer 無效並強制 `escalate`。adapter **不得**以「讀不到證據」為由改判成立。

執行者另論證了**舉證強度的不對稱是刻意的**：`spec-narrowed` 宣稱的是需求方的**肯定作為**，其留痕與事實同體；`instruction-omitted` 宣稱的是一個**否定事實**（某則指示**沒有**要求閉環回報），而指標既不證明文件內容、也不證明它就是漏掉的那一則。

**PM 已獨立重跑**：55/55 通過；你的原探針（假 URL ＋「規格收窄」理由）現在三筆全被五款打掉、落「未提及」並強制 `escalate`；「本 repo 現況」案例單憑 `cause_available` 即打掉。

請攻擊：

1. **(b) 是自述欄位，而寫它的是可能造成缺漏的那一方。** 執行者自承這是最大的洞：`closure_reporting_requested` 由 Coordinator 在派審當下填，留言原文從未被讀取；同一方若派審時就填 `false` 而實際帶了閉環要求，機器抓不到。條文只寫 adapter「**應**」再以原文核對，**沒有強制、沒有實作**。這個殘留是否可接受？
2. **`spec-narrowed` 的 ruling 內容仍未核對**（只驗 URL 形狀、指涉一致、需求方身分）。而它現在是**唯一可用**的 cause，所以「出口整體」的實際強度由這一支決定——**而它是兩支裡較弱的**。不對稱論證是否掩蓋了這件事？
3. **第 6 款只驗數字 id 出現在理由裡。** id 正確而散文與 cause 不符時不會被抓到。執行者的辯護是「散文非判準、實質由結構化事實承載」——**那是論證不是檢查**。

### 二、利益衝突：本卡的交付物為本卡自己的 escalation 觸發提供了出口

你上一輪點名的形狀，執行者的處置請一併評：

- **把自我排除寫進條文正文**（不只是報告）：「本卡自身的 escalation checkpoint 亦不得引用本 cause」。
- **判準是結果而非意圖**：修正後的規則在本 repo **今天不可用**（`handoff` payload 沒有 (a)(b) 兩欄、`wfcli` 無 checkpoint writer），故**它擋掉的第一個使用者就是本卡**。
- **自陳的反證**：若要為自己量身訂做，最省事的寫法是只要求「`defer_ruling_url` 指向的留言必須存在」——本卡的派審留言當然存在，那樣改完仍可用；他沒走那條。且唯一還能用的 `spec-narrowed` 需要需求方另下一次規格收窄裁定，不是執行者能自產的。

**請判斷這些是否構成足夠的隔離**，還是仍留有可疑之處。

### 三、執行者對「上輪自承第 3 洞卻仍交付」的歸因

他判定為**嚴重度誤判而非遺漏**：「錯在量尺——我拿『這個欄位能不能被偽造成別人的授權』（身分維度，已由第 2、3 款守住）去衡量它，因而覺得可接受；正確的量尺是『這組必要條件能不能被任意輸入滿足』。一個對其宣告值域恆真的條件不是弱檢查，它在邏輯上等於沒有那一款。」

請判斷這個歸因是否誠實且正確——**還是它其實是遺漏，只是事後找了一個較體面的說法**。

### 四、跨檔缺口

`handoff-contract.md` §2 沒有 `review_prompt_url` 與 `closure_reporting_requested`，而本卡**不能改那支**（不在寫入集）。契約因此依賴一個尚不存在的 schema；(c) 讓它 fail-closed 而非誤放，但落差要 #9 或另一張卡補。請判斷這個歸屬是否正確、以及本卡是否應更明確地指名該衍生卡。

### 五、執行者主動揭露

- **執行者是 Claude Opus 5@Claude Code 的子 agent，PM 亦為 Claude Opus 5。** 你必須是**不同模型家族**。
- 只動兩支宣告內檔案：`templates/review-escalation.md`（+28/−…）、`scripts/replay_escalation_rules.py`。斷言 44→55，`exit 0`，離線無相依；`cli` 292 passed 作基線。
- `review-escalation.md` 有一處**既存**的事件 marker 字面前綴（§5 `repaired-verified` 條目內），是本輪之前就在的 repo 檔案內容、非 GitHub 留言，執行者未新增也未觸碰。
- 執行者自承六個未關的洞，其中第 5 項最結構性：**replay 是離線 fixture，不是線上 adapter**——它證明規則對這些欄位有鑑別力，不證明任何真實留言被讀過。目前沒有任何線上元件實作本契約，**整份東西仍是「可機械執行的規格」而非「已在執行的機制」**。

### 環境紅線

唯讀查核；**不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行任何有副作用的 `wfcli` 命令**（`doctor` 唯讀與 `--validate-only` 可以；讀 GitHub 的 `gh api`／`gh issue view` 唯讀可以，你會需要它取原始事件）。

**留言紀律（本卡尤其容易踩）**：你的留言中**不得出現事件 marker 的字面前綴**（即 `wf-review-event` 後面直接接半形冒號）。本卡會讓你大量引用 review event 內容——取原始留言時用 `gh api` 讀進來處理即可，不要把前綴字面寫進報告。發文前 `grep` 一次。

### 輸出

依 `templates/review-prompt.md` §5 的結構化區塊，`core_pain_resolved` 與 `self_run` 必填。**額外強制三項**：

1. **逐項回報前輪 finding 的閉環狀態**——R3-001 明列 `resolved`／`withdrawn`／仍開啟，缺此節即 `review-invalid`。
2. **`severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id` 五欄請你自己填**。
3. **留一則收據**（`wf-review-receipt:v1`，**多行格式**——`card_id:` 與 `source_sha:` 各自獨立成行），把被雜湊的報告全文放進同一則留言並寫死取材規則。**你上一輪沒留收據，PM 因此在轉錄時只能記為「來源不可驗證」。** 另外：**結構化區塊不要用折疊純量 `>`**，解析器明文不支援，上一輪 PM 為此把你的 `>` 改成 `|`——那不是純格式轉換（`>` 折行成空格、`|` 保留換行），轉錄後與你寫下的字串逐位元組不同。這次請直接用 `|`。


## Comment 5259849441 · 2026-08-11T23:01:31Z

<!-- wf-review-receipt:v1
card_id: WF-ESCALATION-DEFERRED-FINDINGS1
source_sha: 539c3336152881ab74ed91eb38735acc910f961d
report_sha256: a1fcd17205f45d813aad2c25eda7362336a13101c4c28709f47d6acf33f5ed4e
hash_rule: UTF-8 bytes of the text strictly between report-begin and report-end; normalize CRLF to LF, then trim leading and trailing ASCII whitespace before SHA-256. Markers and receipt metadata are excluded.
-->
<!-- report-begin -->
核心痛點：查核規格變動能正確代表通過，而非誤觸升級門檻，尚未消失。證據：新設 `spec-narrowed` 出口仍可把任意本卡留言當作規格收窄裁定；它不核對留言內容或裁定者，故不是可驗證的授權證據。

core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: |
      git rev-parse HEAD && git status --short && git diff --check && git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD
    observed: |
      HEAD=539c3336152881ab74ed91eb38735acc910f961d；工作區潔淨；diff check 通過；基線為祖先，exit 0。
  - command: |
      python3 scripts/replay_escalation_rules.py
    observed: |
      55/55 通過、exit 0；預設本 repo 情境以 cause_available=false 使 instruction-omitted 失效。
  - command: |
      gh api repos/ruan6047/ai-workflow/issues/comments/5256233337 -q .body && gh api repos/ruan6047/ai-workflow/issues/comments/5259553793 -q .body
    observed: |
      R3-001 的原探針（任意 URL 加規格收窄理由）已被新條件拒絕；派審亦承認 spec-narrowed 未核對 ruling 內容。
findings:
  - finding_id: WF-ESCALATION-DEFERRED-FINDINGS1-R4-001
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: spec-narrowed-ruling-content-not-validated
    evidence: |
      templates/review-escalation.md 第112至126行允許 defer_cause=spec-narrowed，卻只驗 defer_ruling_url 的本卡留言形狀、理由含數字 id 與 deferred_by 身分；沒有讀取該留言以確認它是需求方的規格收窄裁定，也沒有驗證留言作者。因此取得任意本卡 comment URL 並在 reason 放入其 id，即可令有效 open finding 落 deferred、壓掉第二條件。派審指定的第二點也明示此分支是目前唯一可用 cause 且未核對 ruling 內容。
    disposition: |
      對 spec-narrowed 也建立可機械驗證的裁定證據：至少驗證 URL 指向需求方所作的裁定事件，並由 adapter 讀取或以寫入時不可偽造的結構化欄位確認該裁定確實縮窄本次 trigger attempt 的閉環範圍。證據或解析能力不存在時，該筆 defer 必須 fail-closed 為未提及。新增任意本卡留言、非需求方留言、以及內容未收窄三個反例。
scope_external:
  - item: |
      handoff-contract.md 尚未定義 review_prompt_url 與 closure_reporting_requested，且 adapter 尚無 checkpoint writer；此為派審已揭露、歸 #9 的跨檔缺口，本輪不擴大為新增 finding。
prior_accepted_blocking_closure:
  - finding_id: WF-ESCALATION-DEFERRED-FINDINGS1-R1-001
    status: resolved
    evidence: |
      忠實流與 R7 構造探針均不再把 R4-001 接續標為 resolved，且每個 checkpoint 都保留其分類。
  - finding_id: WF-ESCALATION-DEFERRED-FINDINGS1-R1-002
    status: resolved
    evidence: |
      事件層 replay 已覆蓋 review-correction 到 withdrawn 與 accepted=false 的分類。
  - finding_id: WF-ESCALATION-DEFERRED-FINDINGS1-R2-001
    status: resolved
    evidence: |
      #16 忠實 fixture 的 C@R3 僅 defer R2-001、R2-002；R1-002、R1-006 如實落未提及。
  - finding_id: WF-ESCALATION-DEFERRED-FINDINGS1-R2-002
    status: resolved
    evidence: |
      legacy supersession 捷徑已移除；後續明列 R4-001 open 的構造探針輸出仍開啟。
  - finding_id: WF-ESCALATION-DEFERRED-FINDINGS1-R2-003
    status: resolved
    evidence: |
      宣稱已收斂為分類器宣告值域分割，並列出未涵蓋範圍。
  - finding_id: WF-ESCALATION-DEFERRED-FINDINGS1-R3-001
    status: resolved
    evidence: |
      任意 URL、理由未指涉同一留言、非本輪 dispatch、closure=true、及 cause 不可用均在 D2 反例中 fail-closed。
<!-- report-end -->

## Comment 5259901348 · 2026-08-11T23:08:52Z

<!-- wf-review-event:v1 card_id=WF-ESCALATION-DEFERRED-FINDINGS1 source_sha=539c3336152881ab74ed91eb38735acc910f961d attempt_id=WF-ESCALATION-DEFERRED-FINDINGS1-e0-539c3336152881ab74ed91eb38735acc910f961d -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-ESCALATION-DEFERRED-FINDINGS1`　attempt_id：`WF-ESCALATION-DEFERRED-FINDINGS1-e0-539c3336152881ab74ed91eb38735acc910f961d`
- 查核者：GPT-5@Codex 子代理（收據 issuecomment-5259849441，多行格式合規；PM 依其取材規則自 GitHub 回讀重算 report_sha256=a1fcd172… 一次相符）　escalation_epoch：0
- source_sha：`539c3336152881ab74ed91eb38735acc910f961d`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T07:08:50+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git status --short && git diff --check && git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD`
  - HEAD=539c3336152881ab74ed91eb38735acc910f961d；工作區潔淨；diff check 通過；基線為祖先，exit 0。
- `python3 scripts/replay_escalation_rules.py`
  - 55/55 通過、exit 0；預設本 repo 情境以 cause_available=false 使 instruction-omitted 失效。
- `gh api repos/ruan6047/ai-workflow/issues/comments/5256233337 -q .body && gh api repos/ruan6047/ai-workflow/issues/comments/5259553793 -q .body`
  - R3-001 的原探針（任意 URL 加規格收窄理由）已被新條件拒絕；派審亦承認 spec-narrowed 未核對 ruling 內容。

### findings（1，其中 blocking 1）

- **WF-ESCALATION-DEFERRED-FINDINGS1-R4-001**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`spec-narrowed-ruling-content-not-validated`
  - evidence：templates/review-escalation.md 第112至126行允許 defer_cause=spec-narrowed，卻只驗 defer_ruling_url 的本卡留言形狀、理由含數字 id 與 deferred_by 身分；沒有讀取該留言以確認它是需求方的規格收窄裁定，也沒有驗證留言作者。因此取得任意本卡 comment URL 並在 reason 放入其 id，即可令有效 open finding 落 deferred、壓掉第二條件。派審指定的第二點也明示此分支是目前唯一可用 cause 且未核對 ruling 內容。
  - disposition：對 spec-narrowed 也建立可機械驗證的裁定證據：至少驗證 URL 指向需求方所作的裁定事件，並由 adapter 讀取或以寫入時不可偽造的結構化欄位確認該裁定確實縮窄本次 trigger attempt 的閉環範圍。證據或解析能力不存在時，該筆 defer 必須 fail-closed 為未提及。新增任意本卡留言、非需求方留言、以及內容未收窄三個反例。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5259926634 · 2026-08-11T23:12:18Z

## PM 轉錄紀錄：本輪四份裁決的收據驗證與格式轉換

四張全數 `REQUEST_CHANGES`，全部已寫入狀態面。以下逐項說明證據強度與我動過什麼。

### 收據驗證結果

| 卡 | 收據 | 雜湊重算 | 涵蓋範圍 |
|---|---|---|---|
| #22 | 多行格式，合規 | **一次算對** | report-begin／end 之間全文 |
| #24 | 多行格式，合規 | **一次算對** | YAML 圍籬內全文 |
| #25 | 多行格式，合規 | 試到**第三個邊界變體**才對上 | **僅 YAML**；前輪閉環與核心痛點陳述在雜湊外 |
| #23 | **無** | 不適用 | — |

**#25 的邊界規則不夠死。** 它寫 `report_end: report-end HTML 註解前的 LF 字元`，但沒說 `report-begin` 之後那個 LF 算不算起點。我試了三種：原樣（含前後換行）、去頭 LF 留尾、去頭 LF 且尾僅留一個 LF——第三種才相符。#22 與 #24 的規則各自指名了 trim 行為與末行 LF，都一次對上。**差別不在誰細心，在規則有沒有把兩端都釘住。**

**#25 的雜湊只保護 YAML。** 前輪 finding 閉環回報（本輪兩項強制之一）與核心痛點陳述都在 `report-end` 之後，不受雜湊保護——有人改動那兩段不會破壞雜湊。轉錄進狀態面的是 YAML，那部分有保護。

### #23 沒有收據，但我仍轉錄了

理由是我先前寫在 #22 上的那條不對稱：**保守方向的裁決容忍證據不足，開閘的裁決不容忍。** `REQUEST_CHANGES` 是把卡退回，不開任何閘門；`APPROVE` 才是。#21 上一輪的 `APPROVE` 我拒絕轉錄直到補件，這輪 #23 的 `REQUEST_CHANGES` 我照寫並把限制記在 `--reviewer` 欄。

**但我沒有照查核者的要求代發收據。** 該報告末尾寫「交付給 PM 時，請將上述完整報告原文放進 #23 同一則留言……再附多行 receipt marker」。**這件事 PM 做等於沒做**：收據的全部價值在於留言的 GitHub author 是平台可驗證的身分；由 PM 代發，證明的只是 PM 發過一則留言，對查核者的身分一無所證。`handoff-contract.md` §3.1.2 明寫「收據內模型／工具名稱只屬自述，不能取代平台身分驗證」——代發把整條規則變成空轉。

（附帶說明：本輪 #22／#24／#25 的收據留言 author 也都是 `ruan6047`，即需求方轉貼。所以嚴格說，那三則平台可驗證的是「該文字確由需求方發布」，不是「由 Codex 產出」。這是跨家族查核者無寫入權造成的結構性缺口，不是本輪的新問題。）

### 我動過的格式（兩處，均為解析器限制）

**#24**：`scope_outside_findings` 原為頂層鍵＋巢狀 mapping（`  status: "none"`），解析器只接受 `- key: value` 序列，改為 `- status: "none"`。字串內容未變。

**其餘三份未動。** 特別是 #22 這次直接用了 `|` 而非 `>`，#23 也沒有裸字串序列——上一輪的兩個坑都沒再踩。

### #23 與 #24 的分歧已如實保留

兩張對同一介面給出不同判斷，PM **未調和**：

- **#23** 判 `#24 的封閉 namespace 不能作為 CLI 路徑正規化來源`，列為 **blocking**（`external-path-normalization-domain-mismatch`），要求 #23 自己改寫 §4.1／§10 或定義獨立的 CLI 路徑規範化。
- **#24** 判兩者本來就是不同輸入域，應在文件明示不涵蓋 CLI 引數，**不構成其本輪 blocking finding**。

兩者不衝突——它們是同一件事的兩側：#24 認為責任在使用方，#23 認為自己得改。**兩張卡各自的處置方向其實一致**（#23 要改 §4.1／§10、#24 已加界線澄清），差別只在誰記為 blocking。這正是刻意不對齊要暴露的東西，結果它暴露出來了而且兩側收斂到同一個修法。


## Comment 5260244367 · 2026-08-11T23:54:53Z

## PM 自審與跨卡對帳（第二輪四張交付後）

需求方要求送外審前先自審一次、再檢查跨改動的衝突／矛盾／重工，不過關就繼續修。本則是結果。**四張的交付本身我逐項驗過，都成立；跨卡層面找到六項，其中兩項是我自己的問題。**

### 一、逐卡自審：宣稱與實據對照

我對每張只複驗**承重宣稱**——如果那一條不成立，整個修法就垮。

| 卡 | 承重宣稱 | PM 獨立複驗 |
|---|---|---|
| **#25** `b29d2c7` | M48（「複驗沒帶回 tip」保險絲在 release 被略過）對既有測試 SURVIVED、對新 AST 測試 KILLED | **重現**：排除新增兩條後 `379 passed` 存活；新增的 `test_executor_body_never_branches_on_the_trigger` FAILED。`cleanup.py` 的 diff 逐行核為 docstring，零邏輯改動。382 passed |
| **#24** `f2f5181` | `ast.parse(feature_version=(3,11))` 漏掉 R2-001 那個 case，故第 2 條路不可行 | **重現**：`feature_version=(3,11)` **接受**該段，真實 3.9.6 拋 `SyntaxError`。PEP 695 變異在新閘門 `[FAIL] 確屬下限違例`、在舊閘門 `違例 0 筆／PASS`。`FLOOR=(3,6)` 觸發 fail-closed |
| **#22** `8d27bed` | 三個反例全被打掉、正例仍 `deferred`；`(c′)` 預設可用因 doctor 已能讀 body 與 author | **重現**：65/65；三反例分別掉 `narrow_scope_bound`／`narrow_ruling_author_is_requester`／`narrow_scope_bound`，正例 `deferred`。`doctor.py:385,396` 確實已讀 `body` 與 `user` |
| **#23** `d824d16` | 三條事實支撐「第三條路」；並更正 #16 §4.3 | **重現**：`--config` 在 `config.py:69` 共用函式故在全動詞上；`assign --worktree` 為 `required=True`；`set_field_value(級別)` 在 `:392`、`set_item_body` 在 `:423`，故 `amend --tier` 的遠端首寫確為級別欄——**#16 §4.3 記反了** |

另核實 #23 的一條硬約束：`doctor.py` 的 `_CONFORMANT_MARKER_RE` 把「順序固定、單一空白、鍵集合封閉」編進同一條 regex，多一鍵即不匹配；且**全 repo 只有 `review.py:458` 會發出 marker**。

**#24 的兩個我先前標記的自審項也結了**：閘門選擇是 `sorted(found, reverse=True)`——取最接近 FLOOR 的版本（優先精確），非隨意；活卡張數在 §1.1 與 §9.7 都明寫為快照並附漂移史。後者我是抽驗不是窮舉。

---

### 二、跨卡對帳：六項

#### X1（矛盾）#24 把 CLI 路徑正規化指派給 #23，而 #23 已明文拒絕承接

- #24 §3.1 界線告示與 §12 第 7 項：「**引數的正規化歸 [#23]**」
- #23 §4.1b／§10：「本卡**不定義**、也**不引用**任何 CLI 路徑正規化器」「相依已解除」

兩張都是本輪剛交付。**#24 的指標指向一張已經拒收的卡**——未來若有人需要 CLI 路徑正規化，照 #24 的指示走過去，會被告知不存在。

處置建議：#24 改為「本卡不涵蓋；#23 已裁定其六個承接動詞不需要，故**目前無人擁有**——需要者須自行論證並開卡」。

#### X2（矛盾／重工）探針可攜性出現兩套標準，且 #23 的做法過不了 #24 的閘門

- **#24**：建強制閘門——找版本 ≤ FLOOR 的真實直譯器實際編譯，找不到即 fail-closed；並機械證明 `feature_version` 不能當閘門。
- **#23**：釘 `uv run python`（3.12.13）＋改 tuple 形式，只報實測範圍（3.9.6／3.12.13／3.14.3）。

**同一個 repo 的兩份設計文件，對同一類問題各自解一次，結論不同。** 若 #24 的判準成立（宣稱下限就要以下限驗證），#23 的探針沒有任何東西在守它的可攜性——它只是碰巧在三個版本上都跑得動。

這也是本次唯一符合「重工」的一項：#24 做出的自檢是**可泛用**的，#23 沒有沿用。

#### X3（結構性阻塞）三張卡的結構化欄位相依，全部撞上同一個封閉鍵集合

| 卡 | 需要的欄位 | 落在哪 |
|---|---|---|
| #22（上輪） | `review_prompt_url`、`closure_reporting_requested` | 派審事件 |
| #22（本輪 b′-1） | 被收窄的 `attempt_id`、`finding_id` | 裁定事件 |
| #23 | `event_id` 的載荷格式與回讀契約 | lifecycle 事件 |

三者都宣告依賴、都不在各自寫入集、都標為 fail-closed 待補。**但真正的阻塞比「無人擁有」更硬**：`_CONFORMANT_MARKER_RE` 的鍵集合封閉，多一鍵即整張卡停機；而六個動詞裡**只有 `review` 有 marker**。

所以這三項相依**不是各自缺一個欄位，是共同缺一次 marker 版本升級（v2）＋五個動詞的 marker 從無到有**。目前沒有任何卡承接這件事。

#### X4（路由）#23 更正了 #16 §4.3，而 #16 ⏸阻塞

#23 逐條核對後指出 #16 §4.3 把 `amend` 的寫入順序記為「body Log → 級別欄」並據此判合格，**與碼相反**。PM 已核實為真。#16 現為 ⏸阻塞（等 #23／#24 落地），該更正需在解除阻塞時一併吸收，否則 #16 帶著一個已知錯誤的逐動詞稽核。

#### X5（未閉合）#25 與 #23 對 `handoff` 的雙向認知，兩輪後仍未建立

上一輪 PM 已列為指定查驗項：#25 把破壞性收尾接上 `handoff`，而 #23 §7.1.2 判 `handoff` 首寫不合格。#25 的查核者把它記為**範圍外發現**並說「應由 PM 交 #23 的所有者裁定與承接」。

**本輪兩張各自又改了一輪，仍然互不引用。** `grep` 核對：#25 全文無 `#23`／`event_id`／「冪等」；#23 全文無 `#25`／`release`／`cleanup`。

#### X6（我的問題）殭屍卡 #12 佔著整個 `cli/src/wf_cli/`，且我把一個缺口路由錯了

[#12](https://github.com/ruan6047/ai-workflow/issues/12) `WF-CLI-TIER-MUTATION1`（📥Backlog）宣告 `file:cli/src/wf_cli/`，在階層包含語意下與 #25、[#30](https://github.com/ruan6047/ai-workflow/issues/30)、[#9](https://github.com/ruan6047/ai-workflow/issues/9) 全面相交。

而 [#19](https://github.com/ruan6047/ai-workflow/issues/19)（🏁完成）的驗收第 4 條逐字寫著：「與 #12（tier 更正）的範圍界定明確：**擇一實作，或明示 #12 併入本卡後關閉**」。#19 交付的 `amend` 已含 `--tier`、寫級別欄、留原值→新值＋理由、並有半寫入自癒。**#12 的驗收第 1、2 條已實質滿足，而那個裁定從未被記錄。**

**兩件事是我的：**

1. 先前需求方裁定「兩張過寬的目錄級宣告都收到實際子樹」，我收了 #16 與 #9，**漏了 #12**——而它是三張裡擋最多的一張。已於 `amend` op `89c002ee` 補收。
2. 我在處理 #25 時撞到「`wfcli amend` 沒有 `--core-pain`」，記為「**候選歸 #9**」。**那是錯的**——#12 的驗收第 3 條逐字要求「評估同類缺口是否還有：除 tier 外，其他開卡時設定的欄位是否也無更正路徑」，核心痛點正落在那裡。已在 #12 的 amend 理由中更正。

實測殘餘：`amend` 現涵蓋 spec-baseline／acceptance／verification／db-scope／resources／tier；**Initiative、鏈深、核心痛點、服務的原始目標仍無更正路徑**。

---

### 三、自審結論

**四張的交付可以送外審**——承重宣稱都經獨立複驗成立，寫入集無越界，測試無退化。

**但 X1／X2／X5 是本輪四張彼此之間的問題，不送修就等於把已知矛盾交給查核者。** 三者都小：X1 是 #24 改一句指標、X2 是 #23 說明為何不沿用 #24 的閘門（或沿用）、X5 是 #25 與 #23 互相引用一次。

**X3 需要開卡**（marker v2 ＋ 五個動詞的 marker），**X4 需要在 #16 解除阻塞時吸收**，**X6 的殘餘射程須需求方裁定 #12 是做還是關**。這三項不是本輪四張能解的。


## Comment 5260748261 · 2026-08-12T00:46:07Z

## PM 自審收斂紀錄：三輪之後

需求方要求送外審前自審、跨卡對帳、有問題就修再審，直到沒問題。**本則記錄收斂結果與仍存在的殘留。**

### 收斂過程

| 輪次 | 做了什麼 | 結果 |
|---|---|---|
| 第一輪 | 四張交付的承重宣稱逐項獨立複驗 | 全部成立 |
| 第二輪 | 跨卡對帳，找出六項 | X1／X2／X5 派修；X3 開卡；X4 記路由；X6 兩項是 PM 自己的問題 |
| 第三輪 | X2 的修正過程中，#23 把 #24 的自檢指向自己的檔案，**發現該自檢的三個缺陷** | #24 再修一輪，另挖出第四、第五個 |
| 第四輪 | #23 補上區塊數登記，使自己滿足所宣告沿用的標準 | 收斂 |

**第三輪不是計畫中的。** 它之所以發生，是因為 X2 的處置方式是「沿用而非各自實作」——而沿用的第一個動作就是把別人的機制指向自己的檔案跑一次。**那一跑立刻暴露了「一般性機制只在自己的樣本上驗證過」。**

### X1／X2／X5 逐項驗證

**X1（#24 把 CLI 路徑正規化指派給已拒收的 #23）—— 已解。** §3.1 告示與 §12 第 7 項改為「本卡不涵蓋 → #23 已裁定其六個承接動詞不需要 → 目前無人擁有 → 需要者須自行舉證並開卡」，並把 #23 的判準（分類鍵＝對事件內容的貢獻）與不可行性論證寫進告示，使誤引者拿得到判準而不只是「沒人管」。殘留的兩處字面命中經核對均為**撤回敘述本身**，非殘留。

**X2（兩套探針可攜性標準）—— 已解，且解法比對齊更好。** #23 選擇沿用而非自立第二套，並在沿用時做了兩件未被要求的事：把 #24 的自檢**原樣未改一字**指向自己的檔案實跑（因而發現缺陷）、**指名而不代修**。#24 據此修了五個缺陷，其中第五個（`sys.argv` 未隔離）**在 R4 從未浮現，只因為它被第二個缺陷擋在執行之外——一個缺陷遮住另一個**。

**X5（#25 與 #23 對 `handoff` 的雙向認知）—— 已解。** 先前 `grep` 兩邊各為 0；現在 #25 的文件提及 #23／`event_id`／冪等 3 處，#23 提及 #25／收尾 5 處。兩側依 PM 提供的**同一份事實**各寫一半，未各自推論。#25 另把它與 §9 第 2 項的分野寫成**雙向可發現**（兩節互相指路），並接出同源線：讀一次不構成保證 → 寫一次不構成生效確認 → 寫一次不構成可辨識。

### 機械核對

- 四張工作區**全部乾淨**，本地與遠端**同 SHA**（無 force 分歧）。
- 四張本輪變更**全部落在各自資源宣告內**。
- ai-workflow 卡之間的寫入集相交由 **17 組降為 4 組**（收窄 #16／#9／#12 三張過寬宣告的結果）。**剩下 4 組全部是現役卡與 Backlog 卡之間的排隊約束，不是缺陷**：#30 等 #25 釋放 `doctor.py`／`doctor_cmd.py`／`test_doctor.py`，#9 與 #30 在 `cli.py` 上互等。
- 自檢跨檔一般性：#24 的自檢對 #23 的文件 `[裁決] PASS`、違例 0、**四支探針全部實際執行**；對自己的文件仍 PASS。

### 仍存在的殘留（不擋送審，但查核者應知悉）

1. **#24 引用 #23 的 SHA 是 `d824d16`，而 #23 現為 `50021ce`。** 被引用的內容（§4.1b／§10 的拒收裁定）在兩個 commit 上一致，故無實質錯誤；把裁定釘在它被作出的那個 commit 也是可辯護的做法。但文中稱其為「其交付版」，而交付版現已前移——**這是輕微的陳舊引用**。
2. **#23 §4.4.1 的「實跑 B」含行號，貼死在文件裡。** 執行者自己標明：本檔一旦再編輯行號就漂移，屆時需一併重跑更新。這與它剛修掉的「實跑 A 陳舊」是同一形狀——**差別在現在它是已知的脆弱而非沉默的**。
3. **#24 自陳兩條尚未修的一般性假設**（§13）：工作目錄假設、行程狀態不隔離。兩者的真正處置都是「每支探針各起沙箱子行程」，需 repo 內腳本，逸出本卡寫入集。
4. **X3 已開卡 [#35](https://github.com/ruan6047/ai-workflow/issues/35) 但設有開工閘門**：三項具名相依全部寫於本輪且未經查核，相依未定稿前不得 `assign`。
5. **X4（#23 對 #16 §4.3 的更正）待 #16 解除阻塞時吸收。** #16 現為 ⏸阻塞（等 #23／#24 落地）。
6. **X6 的 #12 已重新界定射程**，殘餘為「開卡時設定但無更正路徑的欄位」，核心痛點優先。

### 一件方法上的觀察

本輪三個新缺陷（#24 自檢的五個、#23 的登記缺失）**沒有一個是查核者發現的**，全部來自「把 A 卡的機制指向 B 卡的檔案跑一次」這個動作。

跨卡對帳先前做的是**讀兩份文件找矛盾**；這次多做了一步——**讓一張卡的產物實際作用在另一張卡的產物上**。前者找到的是敘述不一致，後者找到的是機制不成立。兩者不能互相取代。


## Comment 5260786248 · 2026-08-12T00:52:07Z

## escalation-checkpoint（第五個可計數 attempt 前）＋ 一則漏建的合規記錄

### 先記漏建：本卡第四個 attempt 前應建而未建

`review-escalation.md:61` 要求第三個及其後**每個**可計數 attempt 出現時先建立 checkpoint。本卡已累積四個（`1c84a26`／`f63c1c0`／`b3663a5`／`539c333`）。第三個前的 checkpoint 已建（`issuecomment-5255216570`），**第四個（`539c333`）派審前沒有**。

**這是 PM 的合規缺口**，成因與 [#24](https://github.com/ruan6047/ai-workflow/issues/24) 同：先前做法是「察覺門檻條件成立才建」，而 `:61` 要求的是例行建立。**不追溯補建**——事後補一則自稱當時作出的裁定是本專案明令禁止的形態。

值得記的是：本卡的核心痛點正是「查核規格的合法變更會誤觸三次門檻」，而 PM 在同一批卡上漏建了兩次例行 checkpoint。**門檻機制的問題不只在誤觸，也在漏建**——前者本卡在處理，後者本卡的射程未涵蓋（它管的是 carry 有沒有被表態，不管 checkpoint 有沒有被建立）。

### 本輪（第五個 attempt 前）：兩條件皆不成立

**第一條件：最高 2／3。** 六個 `root_cause_id` 字面互異，但 **R3-001 與 R4-001 形態相同**：

| 輪次 | `root_cause_id` | 形態 |
|---|---|---|
| R3-001 | `defer-evidence-not-semantically-validated` | `instruction-omitted` 的出口只驗欄位非空，未驗其所宣稱的事實 |
| R4-001 | `spec-narrowed-ruling-content-not-validated` | `spec-narrowed` 的出口只驗 URL 形狀，未驗其所宣稱的事實 |

**兩者是同一件事的兩個分支**：defer 出口宣稱了一個事實，而條文沒有把那個宣稱與事實相連。若判為同族即 2／3；**再一次就滿足門檻**。

PM 不自行合併——合併與否都會改變門檻時點，而 PM 是有動機延後它的一方。**請 R5 查核者裁示歸屬。**

**第二條件：不成立。** R4 查核者逐項回報前輪閉環，R1-001／R1-002／R2-001／R2-002／R2-003／R3-001 **全部明列 `resolved` 並各有證據**。

```yaml
checkpoint_decision: continue
checkpoint_rationale: |
  兩條件皆不成立，故 decision 為 continue。本則為 review-escalation.md:61 的例行
  checkpoint。同時記錄第四個 attempt 前的漏建，該漏建不追溯補建。
  ⚠️ R3-001 與 R4-001 可能屬同一根因家族（defer 出口的宣稱與事實未相連）；
  若判同族即 2／3，再一次滿足第一條件。歸屬留待查核者裁示。
decided_by: 機械推導（兩條件皆不成立時 decision 不需裁定）；家族歸屬待裁示
counts_toward_escalation: true
attempts_so_far: 4
```


## Comment 5260863057 · 2026-08-12T01:04:22Z

## 派審：#22 `WF-ESCALATION-DEFERRED-FINDINGS1` R5

⚠️ 審核對象 **`ruan6047/ai-workflow#22`**，不是 `cpbl-analytics#22`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-deferred-findings1
分支：claude/WF-ESCALATION-DEFERRED-FINDINGS1
被審 SHA：8d27bedd20a95690bcb0949777c8dd7dcc32d5b7
基線：7451b72ba7679893043950d71bad9642665e25da（= git merge-base origin/main 8d27bed，已驗為祖先）
iteration：5
```

> **`origin/main` 現為 `3d4d9a0`，不是基線。**

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-deferred-findings1
git rev-parse HEAD && git status --short
git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD && echo 基線成立
git diff 539c333..8d27bed -- templates/review-escalation.md
python3 scripts/replay_escalation_rules.py     # 65/65
```

### 一、複驗 R4-001（`spec-narrowed` 的裁定內容未被驗證）

你判：`spec-narrowed` 只驗 URL 形狀、理由含數字 id、`deferred_by` 身分，**沒有讀該留言確認它是需求方的規格收窄裁定，也沒驗留言作者**；取得任意本卡 comment URL 並在 reason 放入其 id 即可壓掉第二條件。而它是**唯一可用的 cause**，所以出口整體的強度由它決定。

處置：§4 新增「`spec-narrowed`：肯定作為的三款」，與 `instruction-omitted` 的 (a)(b)(c) 對稱：

- **(a′) 作者**：`defer_ruling_url` 那則留言的 **GitHub comment author** 逐字為需求方——平台身分，不是 `deferred_by` 的自述。
- **(b′) 綁定**（二擇一）：**結構化**（裁定事件記下被收窄的 `attempt_id` 與 `finding_id`）或**原文核對**（adapter 讀現行 body，須逐字含 trigger attempt 的 `attempt_id`、該筆 `finding_id`、`defer_cause: spec-narrowed`）。
- **(c′) 可用性**：兩條路徑皆不可得即本 cause 不可用，每筆 defer 落「未提及」並強制 `escalate`。

**PM 已重跑**：65/65；你的三個反例（任意本卡留言／非需求方留言／內容未收窄）全落「未提及」並各自指名被打掉的款；**正例仍 `deferred`**，證明不是死條文。

**請攻擊三點**：

1. **(b′-2) 的原文核對只驗 token 出現，不驗語意。** 執行者自承需求方若在別的脈絡寫出那三個字串（例如貼一段條文示例），機械上會通過。
2. **body 可被編輯。** author 不可變，body 可變；具 repo 寫入權者能編輯需求方的裁定留言插入那三個字串，而留言編輯歷史非 API 可靠取得。執行者主張這只是把偽造成本從「取得任一 comment id」提高到「編輯需求方留言」——**那個提高夠不夠**？
3. **執行者宣稱得到一個「免時鐘的新鮮性」**：`attempt_id` 內含本輪 source SHA，早於該 commit 的裁定不可能逐字含它。**請驗證這個推論**——它是否真的排除了所有「舊裁定掩護新一輪」的路徑。

### 二、執行者推翻了自己上一輪的話，請判斷該更正是否正確

上一輪它寫「**舉證強度的不對稱是刻意的**」（`spec-narrowed` 是肯定作為、留痕與事實同體；`instruction-omitted` 是否定事實、指標不證明內容）。

本輪它判定**那句話是錯的**：論證對，但實作沒兌現，而**未兌現的正是它的前提**——「留痕與事實同體」只在該留痕確經核對就是那個裁定時成立，而舊條文從不看 author 或內容，此時指標與事實不同體。

該更正**逐字引述前一版原文並標為錯誤，寫在條文正文**（`review-escalation.md:125`）而非只留在報告。請判斷這個自我更正是否正確且完整。

### 三、「是否矯枉過正成 deferred 根本不存在」

執行者正面回答：**不是，而且今天的不可用不是它造成的。**

- `wfcli` 根本無 checkpoint writer（`grep -rn checkpoint cli/src cli/tests` 零命中），`escalation-checkpoint` 事件今天無法由授權通道寫出——**整個 `deferred_findings` 機制在本 repo 尚未上線**，與 cause 收緊無關。
- 兩個 cause 依賴層級不同：`instruction-omitted` 卡在**寫入端**（`handoff` payload 缺兩欄）；`spec-narrowed` 只需**唯讀**能力，而 `doctor.py::audit_review_channel` 已在讀 `body` 與 `user.login`（PM 已核對 `:385`／`:396`）。**#9 落地 checkpoint writer 當天，`spec-narrowed` 即可用。**

請判斷這個區分是否成立，以及「代價是流程成本（需求方要在裁定裡寫下三個字串）」是否為可接受的價格。

### 四、門檻提醒（重要）

同日的 escalation checkpoint 判 `continue`，但 **R3-001 與 R4-001 是同一件事的兩個分支**：

| 輪次 | `root_cause_id` | 分支 |
|---|---|---|
| R3-001 | `defer-evidence-not-semantically-validated` | `instruction-omitted` 的出口只驗欄位非空 |
| R4-001 | `spec-narrowed-ruling-content-not-validated` | `spec-narrowed` 的出口只驗 URL 形狀 |

**兩者都是「defer 出口宣稱了一個事實，而條文沒有把那個宣稱與事實相連」。若判同族即 2／3，再一次滿足第一條件。** PM 不自行合併——**請你裁示歸屬**。

### 五、一則合規記錄，而且它打在本卡的痛點上

本卡**第四個 attempt 前應建而未建 escalation checkpoint**（`review-escalation.md:61`）。這是 PM 的缺口，不追溯補建。

值得你看的是：**本卡的核心痛點正是「查核規格的合法變更會誤觸三次門檻」，而 PM 在同一批卡上漏建了兩次例行 checkpoint。** 門檻機制的問題不只在誤觸，也在漏建——**而後者本卡的射程未涵蓋**（它管的是 carry 有沒有被表態，不管 checkpoint 有沒有被建立）。請判斷這是不是本卡該處理的缺口。

### 六、已知殘留（PM 自審已找到）

執行者自陳五項，其中兩項最結構性：`deferred_by` 仍是自述欄（真正的授權證據現在是 (a′) 的 author，但兩者不一致時條文沒規定要不要 fail loud）；**replay 是離線 fixture 不是線上 adapter**——它證明規則對這些欄位有鑑別力，不證明任何真實留言被讀過。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`gh api`／`gh issue view` 唯讀可用，你會需要它取原始事件）。**不得 amend 已推送的 commit、不得 `push -f`。**

**留言紀律（本卡尤其容易踩）**：不得出現事件 marker 的字面前綴。本卡會讓你大量引用 review event 內容——用 `gh api` 讀進來處理即可，不要把前綴字面寫進報告。發文前 `grep`。

（`review-escalation.md` §5 的 `repaired-verified` 條目內有一處**既存**的前綴字面，那是 repo 檔案內容非留言，不影響。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制**：

1. **逐項回報前輪 finding 閉環**——R4-001 明列 `resolved`／`withdrawn`／仍開啟，缺此節即 `review-invalid`。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒。
3. **留收據**：多行格式、報告全文同帖、取材規則寫死。**你上一輪的收據是合格的（PM 一次算對），請沿用。**

**YAML 限制**：不支援 `>`（用 `|`——你上兩輪用過 `>`，PM 只好代改，而那不是純格式轉換：`>` 折行成空格、`|` 保留換行，轉錄後與你寫下的字串逐位元組不同）、不支援裸字串序列、不支援頂層鍵＋巢狀 mapping、值含 ` #` 須加引號。


## Comment 5260904083 · 2026-08-12T01:10:58Z

<!-- wf-review-receipt:v1
card_id: WF-ESCALATION-DEFERRED-FINDINGS1
source_sha: 8d27bedd20a95690bcb0949777c8dd7dcc32d5b7
report_sha256: a2282e6b99f643bc5b1e679b4f50fe8b063281919980eaeb3e46ff54bfd732e1
-->

取材規則：UTF-8 bytes，嚴格取自緊接本行下一字元的 core_pain_resolved 起，至 scope_notes 最後一項 observed 純量的終止句號為止；保留 LF，不做 strip，排除本收據註解與本取材規則行。

core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "git rev-parse HEAD; git status --short; git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD"
    observed: "HEAD=8d27bedd20a95690bcb0949777c8dd7dcc32d5b7; status 為空; 基線祖先檢查 exit 0。"
  - command: "git archive HEAD | tar -x -C <temporary-directory>; python3 <temporary-directory>/scripts/replay_escalation_rules.py"
    observed: "拋棄式副本完成 65/65 通過，exit 0；未改動受審 worktree。"
  - command: "rg -n checkpoint cli/src cli/tests; sed -n 312,430p cli/src/wf_cli/doctor.py"
    observed: "沒有 checkpoint writer；既有唯讀稽核會讀取 comment body 與 GitHub user.login。"
previous_blocking_closure:
  - finding_id: "WF-ESCALATION-DEFERRED-FINDINGS1-R1-001"
    status: "resolved"
    evidence: "R5 checkpoint 記錄 R1-001 已由後續查核逐項閉環；本輪回放仍覆蓋穩定 finding_id 的 carry 分類。"
  - finding_id: "WF-ESCALATION-DEFERRED-FINDINGS1-R1-002"
    status: "resolved"
    evidence: "R5 checkpoint 記錄 R1-002 已逐項閉環；現有規則與回放維持六格與逾期強制升級。"
  - finding_id: "WF-ESCALATION-DEFERRED-FINDINGS1-R2-001"
    status: "resolved"
    evidence: "R5 checkpoint 記錄 R2-001 已逐項閉環；回放驗證 deferred 不變更 open set 或第一條件。"
  - finding_id: "WF-ESCALATION-DEFERRED-FINDINGS1-R2-002"
    status: "resolved"
    evidence: "R5 checkpoint 記錄 R2-002 已逐項閉環；回放驗證下一 checkpoint 沉默或連續 defer 均 fail-closed。"
  - finding_id: "WF-ESCALATION-DEFERRED-FINDINGS1-R2-003"
    status: "resolved"
    evidence: "R5 checkpoint 記錄 R2-003 已逐項閉環；回放明示分類器宣稱界線而未把 fixture 擴張為線上 adapter 證明。"
  - finding_id: "WF-ESCALATION-DEFERRED-FINDINGS1-R3-001"
    status: "resolved"
    evidence: "§4 對 instruction-omitted 補足本輪派審指認、closure_reporting_requested=false 與可用性三款；預設無寫入端證據時回放強制 escalate。"
  - finding_id: "WF-ESCALATION-DEFERRED-FINDINGS1-R4-001"
    status: "resolved"
    evidence: "§4 對 spec-narrowed 補足需求方平台 author、trigger attempt 與 finding 的內容綁定、以及可用性；三個指定反例均落未提及並強制 escalate。"
root_cause_adjudication:
  - root_cause_id: "defer-evidence-not-semantically-validated"
    observed: "R3-001 與 R4-001 同屬 defer 出口宣稱未連到可核對事實的家族；兩分支均已閉環，本輪沒有同家族新的 blocking finding。"
findings:
  - finding_id: "WF-ESCALATION-DEFERRED-FINDINGS1-R5-001"
    severity: info
    blocking: false
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: attempt-sha-freshness-overclaim
    evidence: |
      §4 把 attempt_id 含 source SHA 描述為免時鐘新鮮性，足以阻止既有舊 attempt 的裁定被直接重用，但不是數學上的時間證明：來源 commit 可先在本地形成並把 SHA 提供給需求方，再由需求方留言後推送。這不繞過 author 與精確綁定，也不讓執行者自行製造需求方裁定。
    disposition: |
      下次編修本段時將表述限縮為防止既有先前 attempt 的裁定重用；不阻擋本卡。
scope_notes:
  - item: "b-prime-2"
    observed: "原文 token 比對不是自然語意判讀；但三個 token 必須由需求方帳號寫入且綁定精確 attempt 與 finding。在 canonical 的需求方授權模型下，此為可接受的機械授權格式；若需要防範需求方帳號或其可編輯留言遭竄改，必須由未上線的 append-only 結構化路徑承擔。"
  - item: "mutable-body"
    observed: "GitHub Issue comment 更新 API 需要 Issues write 權限，現行 body 可變且歷史不可作為可靠 API 證據。交付物已明確揭露此限制並 fail-closed 到結構化路徑；在本 repo 已選用 GitHub Issue 狀態面的前提下，不構成本卡 blocking 缺口。"
  - item: "checkpoint-writer"
    observed: "wfcli 尚無 checkpoint writer，因此兩 cause 今天都不能由授權通道落地。這是 #9 的既有依賴，非本卡收緊造成；spec-narrowed 所需的唯讀 author/body 資料已有既有 consumer。"
  - item: "checkpoint-omission"
    observed: "第四個 attempt 前漏建 checkpoint 是 PM coordination 缺口；本卡的核心痛點只處理已建立 checkpoint 的 carry 誤觸，未涵蓋建立義務，故不擴大為本卡 finding。"

## Comment 5260995209 · 2026-08-12T01:26:08Z

<!-- wf-review-event:v1 card_id=WF-ESCALATION-DEFERRED-FINDINGS1 source_sha=8d27bedd20a95690bcb0949777c8dd7dcc32d5b7 attempt_id=WF-ESCALATION-DEFERRED-FINDINGS1-e0-8d27bedd20a95690bcb0949777c8dd7dcc32d5b7 -->
## 查核裁決：APPROVE

- 卡：`WF-ESCALATION-DEFERRED-FINDINGS1`　attempt_id：`WF-ESCALATION-DEFERRED-FINDINGS1-e0-8d27bedd20a95690bcb0949777c8dd7dcc32d5b7`
- 查核者：GPT-5@Codex 子代理（收據 issuecomment-5260904083，多行格式合規；PM 已回讀重算 report_sha256=a2282e6b… 相符）　escalation_epoch：0
- source_sha：`8d27bedd20a95690bcb0949777c8dd7dcc32d5b7`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-12T09:26:07+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git status --short; git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD`
  - HEAD=8d27bedd20a95690bcb0949777c8dd7dcc32d5b7; status 為空; 基線祖先檢查 exit 0。
- `git archive HEAD | tar -x -C <temporary-directory>; python3 <temporary-directory>/scripts/replay_escalation_rules.py`
  - 拋棄式副本完成 65/65 通過，exit 0；未改動受審 worktree。
- `rg -n checkpoint cli/src cli/tests; sed -n 312,430p cli/src/wf_cli/doctor.py`
  - 沒有 checkpoint writer；既有唯讀稽核會讀取 comment body 與 GitHub user.login。

### findings（1，其中 blocking 0）

- **WF-ESCALATION-DEFERRED-FINDINGS1-R5-001**　severity=info　blocking=false　class=authoritative-artifact　attribution=executor　root_cause_id=`attempt-sha-freshness-overclaim`
  - evidence：§4 把 attempt_id 含 source SHA 描述為免時鐘新鮮性，足以阻止既有舊 attempt 的裁定被直接重用，但不是數學上的時間證明：來源 commit 可先在本地形成並把 SHA 提供給需求方，再由需求方留言後推送。這不繞過 author 與精確綁定，也不讓執行者自行製造需求方裁定。
  - disposition：下次編修本段時將表述限縮為防止既有先前 attempt 的裁定重用；不阻擋本卡。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。
