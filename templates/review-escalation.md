# Review Preflight 與 Escalation Contract

> 承載 canonical §3／§5 的操作語意。目標是把便宜、可機械發現的流程錯誤擋在正式查核前，同時保留對實作與權威交付物的嚴格審核。

## 1. 三個不同層次

| 層次 | 結果／事件 | 卡片狀態 | iteration | 計入 escalation |
|---|---|---|---:|---:|
| 送審前檢查 | `preflight-failed` | 留在 `🔨執行中` | 不增加 | 否 |
| 外部阻塞 | `status-change` → `⏸阻塞` | `⏸阻塞` | 不增加 | 否 |
| 無效查核 | `review-invalid` | 交接仍有效時留在 `🔍待查核`；否則依原因回 `🔨執行中` 或 `⏸阻塞` | 不增加 | 否 |
| 實質查核 | `APPROVE`／`REQUEST_CHANGES` | `✅通過`／`↩退回` | 後者增加 | 依 §3 |

Preflight 至少驗證：卡面必填欄位與 spec 基線、Gate／依賴狀態、handoff 與 branch tip 的 source SHA 同一性、分支已推送、工作區乾淨、必要測試／證據存在、commit trailer，以及規定在跨家族查核前完成的人工檢查。可由 sender／Coordinator 修正的交付缺口寫 `preflight-failed`；等待權限、上游卡、服務或 sign-off 等外部條件時改寫 `status-change` 並轉 `⏸阻塞`。兩者都不得建立 `review` event 或派 reviewer。

`review-invalid` 適用於未依順序進行的查核、查核環境受污染、reviewer 獨立性不符、查核了非 handoff 指定的 artifact，或同一 reviewer 對同一 SHA 重複回報而沒有新的必要查核範圍。T4 跨家族／人工 sign-off 等規定的多 reviewer 查核仍然有效，但同一 SHA 只彙總為一個 attempt。無效查核中有參考價值的觀察可留在 evidence，但不得當成 accepted finding，該事件本身也不形成 escalation attempt。

## 2. Finding 分類

每個 finding 必填：

```yaml
finding_id: <stable id>
severity: critical | major | minor | info
blocking: true | false
accepted: true | false
status: open | resolved | withdrawn
finding_class: implementation | authoritative-artifact | governance | coordination | environment
attribution: executor | planner | coordinator | reviewer | external
root_cause_id: <stable causal family; unknown must be unique per finding>
evidence: <reproduction or source>
disposition: <required fix or decision>
```

- `implementation`：程式、設定、migration、生成器或可執行行為錯誤。
- `authoritative-artifact`：本卡交付的 spec、統計結論、API 契約或安全宣稱有實質錯誤。文件不因副檔名而自動豁免。
- `governance`：卡面 metadata、章節名、baseline 欄、trailer、事件 envelope 等流程留痕。
- `coordination`：錯誤派工、查核順序、lease／handoff 管理或 Coordinator 指示造成的缺陷。
- `environment`：外部依賴、服務、權限或測試環境尚未具備，且不是交付物本身造成。

Reviewer 提交報告，由 lifecycle writer 在寫入 `review` event 前依可重現證據標記 `accepted`；reviewer 不得自行決定是否消耗 escalation 額度。新採認的 blocking finding 以 `open` 開始；後續 attempt 必須用同一 `finding_id` 帶回 `resolved` 或 `withdrawn`，否則視為未閉合。若事後翻案，以 correction event 追加新 disposition，不回寫舊 event。`root_cause_id=unknown` 不得跨 finding 當成相同根因。

## 3. 可計數的退回

一個 review attempt 以 `(card_id, escalation_epoch, source_sha)` 唯一識別；同一 SHA 的多位 reviewer findings 合併處理，最多計一次。只有同時符合以下條件才令 `counts_toward_escalation=true`：

1. preflight 已通過且 review 有效；
2. 結論為 `REQUEST_CHANGES`；
3. 至少一個 `accepted=true` 且 `status=open` 的 blocking finding 屬 `implementation` 或 `authoritative-artifact`；
4. 該 finding 的 `attribution=executor`；包含「executor 在已核可基線內自行改變交付語意」且有明確證據的情形。

純 `governance`／`coordination`／`environment` finding、planner／Coordinator 提供的錯誤前提、等待外部 sign-off／lease／上游卡，以及重複同 SHA review 均不得消耗 executor escalation 額度。它們仍須修正與留痕，不代表可以合併。

## 4. 三次門檻

第三個及其後每個可計數 attempt 出現時先建立 `escalation-checkpoint`，不得只按整數直接寫 `🚨已升級`。`accepted` 表示 finding 已由 Coordinator／需求方依可重現證據採認，且未被後續 correction 撤銷：

- 任一相同 `root_cause_id` 在三個不同 attempt 持續出現，或上一輪 accepted blocking finding 在下一輪未處理：轉 `🚨已升級`。
- findings 為不同根因、前輪均已閉合且 severity／剩餘範圍持續收斂：維持原 owner，交由 Coordinator 記錄「續修／重規劃」決定；只有需求方選擇升級才轉 `🚨已升級`。
- Critical finding 可立即 fail-closed 或暫停高風險操作，但不因 severity 單獨推定 executor 已連續失敗三次。

需求方核可重規劃或更換執行者時遞增 `escalation_epoch`，新 epoch 從零計數；舊 events 保留，不回寫或刪除。

## 5. Adapter 必填欄位

`handoff-accepted` 或等價 preflight pass event 應記 `preflight_passed=true` 與檢查摘要。`review` event 另記：

```yaml
attempt_id: <card>-e<epoch>-<full source sha>
escalation_epoch: <integer, default 0>
preflight_passed: true
review_result: APPROVE | REQUEST_CHANGES
findings: [<structured finding>]
counts_toward_escalation: <boolean derived from §3>
```

`preflight-failed` 必填 `preflight_passed=false` 與非空 `failure_reasons`；
`review-invalid` 必填 `preflight_passed` 的實際值與非空 `invalid_reasons`。
`escalation-checkpoint` 必填：

```yaml
escalation_epoch: <integer>
trigger_attempt_id: <the third-or-later unique counted attempt>
unique_attempt_count: <deduplicated count in this epoch; >= 3>
checkpoint_decision: continue | replan | change-executor | escalate
checkpoint_rationale: <root-cause repetition, closure trend, or requester ruling>
```

`counts_toward_escalation` 是 adapter 依結構化欄位算出的投影，不得由 reviewer 以自由文字自行宣告。若同 SHA 有多個有效 reviewer 報告，adapter 先合併 findings 再計算一次；相同 `finding_id` 的衝突分類須由 Coordinator／需求方裁定，不得用陣列順序覆寫。cutover 前歷史事件維持原貌；採用專案以 baseline event 指定新契約開始時間。
adapter 亦須以穩定 `finding_id`／`root_cause_id` 跨 attempt 推導 checkpoint：同根因出現於三個唯一可計數 attempt，或前一 attempt 的 accepted blocking finding 未在下一 attempt 明列 `resolved`／`withdrawn` 時，`checkpoint_decision` 只能是 `escalate`，不得信任手填的 `continue`。
