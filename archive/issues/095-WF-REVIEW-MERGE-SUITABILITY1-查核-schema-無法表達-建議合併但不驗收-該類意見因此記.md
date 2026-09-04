# #95 WF-REVIEW-MERGE-SUITABILITY1 查核 schema 無法表達「建議合併但不驗收」，該類意見因此記不進帳
- state: closed  created: 2026-08-16T14:57:18Z  closed: 2026-08-17T03:24:59Z
- url: https://github.com/ruan6047/ai-workflow/issues/95
- comments: 1

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；改動面看似只是加欄位，但它動的是第一判準的否決規則（validation.py:268-272），而該規則是刻意的設計不是疏漏——要在不削弱「核心痛點未消不得驗收」的前提下，讓合併適用性成為可記錄的獨立軸。須判斷新軸要不要影響 iteration／attempt／escalation（依 §1 表格逐格對照），錯了會污染治理計數。經濟型容易直接放寬否決規則。）　查核：待指派（建議 高階型；本卡改的是查核契約本身的判準，錯誤會讓「驗收」這個概念鬆掉——那是整套流程的第一判準。查核重點在【新軸有沒有變成繞過第一判準的後門】：須實測一份 core_pain_resolved=no 的裁決不會因為新軸而在任何路徑上被當成通過。另須判斷新軸是否又是一個沒有讀者的欄位。跨家族。）
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：留痕要能承載實際會發生的問題類型。目前查核通道只認得「驗收」一種問句，於是任何不是驗收的專業意見都無處可放，只能以散文留在留言裡、機器讀不到，也無法被 doctor／snapshot／看板消費。

## 簡介
<!-- card-brief:begin -->
讓查核 schema 能表達「核心痛點未消、但這個分支建議合併」這條獨立軸，而不必謊報 `core_pain_resolved` 或 `review_result` 任一欄；並依 `templates/review-escalation.md` §1 的表格逐格裁定新軸對 iteration／attempt／escalation 的影響。**適用時機**：查核者要回答的其實是「該不該合併」而不是「驗收過不過」時；或要動第一判準的否決規則、需要知道邊界在哪時。⛔ 非射程：⛔ 不放寬第一判準——`cli/src/wf_cli/validation.py:268-272` 擋 `core_pain_resolved=no` 併 `APPROVE` 是刻意設計，新軸不得成為它的後門；⛔ 不追加沒有讀者的欄位（須指名實際消費者並證明讀得到）；⛔ 不重審 WF-WORKTREE-REPO-OWNERSHIP1——那張卡已依需求方 2026-08-16 丙案處置，本卡只拿它的原裁決文字當重放語料。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：查核 schema 只有一條軸：core_pain_resolved 是第一判準且具否決權，validation.py:268-272 硬擋 core_pain_resolved=no 併 review_result=APPROVE。這條規則本身是對的——查核講的是驗收。但實務上存在另一類問題：「這個分支該不該合併」，它與驗收無關，而現行 schema 沒有形狀承載它，於是這類意見寫出來就記不進帳。⚠️ 已實現案例：2026-08-16 WF-WORKTREE-REPO-OWNERSHIP1（#57）——卡已降 Backlog、核心痛點構造上不可達，PM 送出的問題是合併適用性而非驗收。跨家族查核者的回答在收據頭自寫 review_scope: merge-suitability-not-acceptance（一個 schema 不認識的欄位），裁決 core_pain_resolved: no + review_result: APPROVE + merge_recommendation: approve_after_update_branch。wfcli review 拒收：先因缺 self_run 提早返回，補上後仍有 core_pain_resolved=no 不允許 APPROVE、finding_class: test-adequacy 不在 FINDING_CLASSES、兩條 finding 缺 evidence 與 disposition。查核者拒絕貼一份明知仍無效的裁決，並指出改成 REQUEST_CHANGES 會扭曲原意且錯誤推進 iteration／卡片狀態（依 §1，REQUEST_CHANGES → ↩退回、iteration 增加、計入 escalation，對一張已合併的 Backlog 卡全是錯的）。⚠️ 需求方 2026-08-16 對 #57 裁定採丙案（不把該輸出當查核記、卡收回 Backlog），代價是查核者兩條 non-blocking finding 不入帳，其中 R5-01 無機械落點、已轉由 #91 承接。丙案解決了 #57，沒有解決這個形狀——下一次拿合併適用性去問查核者，會再撞一次。【本卡不是要放寬第一判準】它要的是讓合併適用性成為一條可記錄的獨立軸，且不得成為繞過第一判準的後門。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/validation.py",
    "file:cli/tests/test_validation.py",
    "file:templates/review-prompt.md",
    "file:templates/review-escalation.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] schema 能表達「核心痛點未消，但建議合併」而不需要謊報 core_pain_resolved 或 review_result 任一欄。形狀由執行者提案（新欄、新 review_result 列舉值、或獨立事件型別皆可），須在卡上說明為何選它。
- [ ] ⚠️ 新軸不得成為第一判準的後門：須以實測證明一份 core_pain_resolved=no 的裁決，在任何路徑上都不會被當成驗收通過（含 handoff 的下一階段推導、release 的終態閘門、doctor 的對帳）。
- [ ] 新軸對 iteration／attempt／escalation 的影響須依 review-escalation.md §1 的表格逐格裁定並實作，且以實測證明——不得只在文件寫「不影響」。
- [ ] ⚠️ 新軸須有讀者。須指出至少一個實際會消費它的地方並證明讀得到；若當下沒有，本卡須明說是半條線並提出承接卡，不得以「之後會有人讀」收尾。
- [ ] 以 #57 於 2026-08-16 的真實裁決重放：查核者原本寫出的內容（core_pain_resolved: no、建議合併、review_scope: merge-suitability-not-acceptance、兩條 non-blocking finding）在新 schema 下必須能完整落地，不需要刪改任何實質內容。

## 驗證

- [ ] 重放 #57 的原裁決文字，逐欄比對落地結果與原意是否一致。
- [ ] 變異檢驗：拿掉第一判準的否決規則 → 對應測試轉紅；讓新軸在任一路徑上被當成驗收 → 對應測試轉紅。
- [ ] 回歸：既有 review 測試全綠；現行 APPROVE／REQUEST_CHANGES 兩條路徑的行為與計數不受影響。
## Log

- 2026-08-16T22:57:17+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-18T19:50:41+08:00 handoff by wf-cli → owner —（已停止）；iteration 0；SHA f207d2ecf80556d6b90beeb0438bf648288a5fd9；證據 收尾補帳（2026-08-18）：Issue 已於 2026-08-17 關閉（NOT_PLANNED）而交付狀態停在 📥Backlog，本次補終態。決策與原因：需求方 2026-08-16 裁定關閉，理由逐字見 issuecomment-5311411634——本卡服務的不是 ROADMAP 的兩個目標（可稽核／防低級事故），而是讓某一類一年可能出現一次的查核意見記得進去，不值得為它改查核契約的第一判準。。
- 2026-08-26T12:33:50+08:00 amend by wf-cli（op 3c8eb0ea）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:e289cb780561552b1223ae62c6f7ee5e74c537ce9f85474c63c949628f6e2c59 (875 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 先導批 10 張：回填 canonical AI_WORKFLOW.md §6.3 的卡片簡介。⭐ 價值主張依卡面 A10：131 張終態卡上 assign_cmd 讓資源宣告結構性失明、root_cause_id 住在 review finding 裡，簡介是三個相關性機制裡唯一還能用的那個。⛔ 未改動任何其他欄位。A5 守衛已在呼叫前拒收 str.splitlines() 認得的全部分行字元（由該函式自身導出，非手打清單）。。


## Comment 5311411634 · 2026-08-17T03:24:58Z

需求方 2026-08-16 裁定關閉（見 #94 的 `issuecomment-5311397884`）。

理由：本卡服務的**不是** ROADMAP 的兩個目標（可稽核／防低級事故），而是讓某一類**一年可能出現一次**的查核意見記得進去。⚠️ **不值得為它改查核契約的第一判準**——`core_pain_resolved` 具否決權是刻意設計，在它上面加一條旁路的風險大於收益。

#57 的處置已證明那類意見有可用的落點：丙案（不把合併適用性意見當查核記、卡收回 Backlog、意見留為 Issue 留言）。若日後該情境再次發生且落點不夠用，屆時再議。
