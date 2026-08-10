# Review Preflight 與 Escalation Contract

> 承載 canonical §3／§5 的操作語意。目標是把便宜、可機械發現的流程錯誤擋在正式查核前，同時保留對實作與權威交付物的嚴格審核。

## 1. 三個不同層次

| 層次 | 結果／事件 | 卡片狀態 | iteration | 計入 escalation |
|---|---|---|---:|---:|
| 送審前檢查 | `preflight-failed` | 留在 `🔨執行中` | 不增加 | 否 |
| 外部阻塞 | `status-change` → `⏸阻塞` | `⏸阻塞` | 不增加 | 否 |
| 無效查核 | `review-invalid` | 交接仍有效時留在 `🔍待查核`；否則依原因回 `🔨執行中` 或 `⏸阻塞` | 不增加 | 否 |
| 實質查核 | `APPROVE`／`REQUEST_CHANGES` | `✅通過`／`↩退回` | 後者增加 | 依 §3 |
| 留痕解析停機 | 停機本身無觸發事件；解除寫 `review-marker-clearance` | 停機期間不變；解除後依 §5 的 `clearance_decision` | 不增加 | 否 |

Preflight 至少驗證：卡面必填欄位與 spec 基線、Gate／依賴狀態、handoff 與 branch tip 的 source SHA 同一性、分支已推送、工作區乾淨、必要測試／證據存在、commit trailer，以及規定在跨家族查核前完成的人工檢查。可由 sender／Coordinator 修正的交付缺口寫 `preflight-failed`；等待權限、上游卡、服務或 sign-off 等外部條件時改寫 `status-change` 並轉 `⏸阻塞`。兩者都不得建立 `review` event 或派 reviewer。

`review-invalid` 適用於未依順序進行的查核、查核環境受污染、reviewer 獨立性不符、查核了非 handoff 指定的 artifact、**`APPROVE` 未附 `self_run`**（canonical §5.2：沒有自跑證據的通過不是查核），或同一 reviewer 對同一 SHA 重複回報而沒有新的必要查核範圍。T4 跨家族／人工 sign-off 等規定的多 reviewer 查核仍然有效，但同一 SHA 只彙總為一個 attempt。無效查核中有參考價值的觀察可留在 evidence，但不得當成 accepted finding，該事件本身也不形成 escalation attempt。

**留痕解析停機**是前四個層次之外的另一種東西：它不是對查核品質的判斷，而是**消費者讀不懂留痕**。當 timeline 出現受 `handoff-contract.md` §3.1 管轄卻不合格的 review marker（未知版本、缺欄、多出未定義鍵、欄位錯序、三欄不自洽），或同一 `attempt_id` 的多則事件語意衝突時，消費者必須停止該卡的自動裁決判定，不得跳過該則留言後照常放行——讀不懂的那則可能正是撤銷或降級裁決。停機不改卡片狀態、不建立 attempt、不計 iteration、不消耗 escalation 額度；它只是宣告「在人看過之前，機器不再自行下結論」。解除依 §5 的 `review-marker-clearance`。

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

Reviewer 提交報告，由 lifecycle writer 在寫入 `review` event 前依可重現證據標記 `accepted`；reviewer 不得自行決定是否消耗 escalation 額度。新採認的 blocking finding 以 `open` 開始；後續有效 review（無論是否計數）或明示 `review-correction` event 都可用同一 `finding_id` 帶回 `resolved`／`withdrawn`，adapter 必須先更新實際 open set 再判斷下一個可計數 attempt 是否承接未閉合 finding。若事後翻案，以 `review-correction` 追加新 disposition，不回寫舊 event。`root_cause_id=unknown` 不得跨 finding 當成相同根因。

同一 attempt 的多 reviewer 可補充不同 finding；若同一 `finding_id` 的 `status`、`accepted`、分類、歸屬或根因互相衝突，adapter 必須將該 finding 標為待裁決、不套用任一衝突值，並要求下一筆相關 lifecycle event 為 Coordinator／需求方的 `review-correction`。事件流結束或出現其他事件而仍未裁決時才 fail loud；追加合法 correction 後完整 replay 必須恢復通過，不得因 append-only 歷史中保留衝突事件而永久失效，也不得依事件或陣列順序覆寫。若某 correction 同時使第三個 attempt 恢復計數而建立 pending checkpoint，仍須先允許後續 `review-correction` 清完既有衝突，再要求下一筆為 `escalation-checkpoint`；兩個 gate 不得互相鎖死。留痕解析停機（§1、§5 `review-marker-clearance`）是**解析層**的第三個 gate，且**優先於**本節的語意層裁決：讀不出 marker 就談不上 finding 是否衝突。三個 gate 同樣不得互相鎖死——replay 必須允許依序追加 `review-marker-clearance`、`review-correction`、`escalation-checkpoint`，不得要求下一筆事件同時滿足兩種 gate。

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

需求方核可重規劃或更換執行者時，以 `escalation-epoch-change` 明示授權並將 `escalation_epoch` 逐一遞增；新 epoch 從零計數，舊 events 保留，不回寫或刪除。review 自行填入較大 epoch 不構成授權，adapter 必須拒絕 epoch 跳號、倒退或未經授權的切換。

## 5. Adapter 必填欄位

`handoff-accepted` 或等價 preflight pass event 應記 `preflight_passed=true` 與檢查摘要。`review` event 另記：

```yaml
attempt_id: <card>-e<epoch>-<full source sha>
escalation_epoch: <integer, default 0>
preflight_passed: true
core_pain_resolved: yes | no
review_result: APPROVE | REQUEST_CHANGES
self_run: [<{command, observed} 逐項；不得為空>]
findings: [<structured finding>]
counts_toward_escalation: <boolean derived from §3>
```

`core_pain_resolved` 與 `self_run` 依 canonical §5.1／§5.2 必填：`core_pain_resolved: no` 時 `review_result` 只能是 `REQUEST_CHANGES`（第一判準具否決權），且該 finding 的 `attribution` 記 `planner`、`finding_class` 記 `authoritative-artifact`——驗收清單與痛點脫節是 spec 缺陷，不消耗 executor 的 escalation 額度。`self_run` 為空的 `APPROVE` 一律寫 `review-invalid`，不建立 attempt。

`preflight-failed` 必填 `preflight_passed=false` 與非空 `failure_reasons`；
`review-invalid` 必填布林型別的 `preflight_passed` 實際值與非空 `invalid_reasons`。
`review-correction` 必填 `escalation_epoch`、既存的 `target_attempt_id` 與非空 `finding_updates`；每個 update 使用 §2 完整 finding schema，且 `finding_id` 必須已存在於 target attempt。此專用 type 不得與其他 lifecycle correction 混用。`status=withdrawn`、`accepted=false`，或仍為 open 但已不符合 §3 可計數 finding 的條件，都表示該 finding 不再是有效 open finding；adapter 必須將它移出 open set，並移除其對 unresolved carry、repeated root cause，以及「只由該 finding 支撐」之 target attempt 計數的貢獻。`status=resolved` 且採認未撤銷只表示已修正，不得洗掉先前真實 carry。若 correction 重診斷 `root_cause_id`，同一穩定 `finding_id` 在該 epoch 全部 attempt 的既有 occurrence 一併遷移至新根因。合法 correction 必須能在 append-only replay 中解除它所裁決的 pending conflict。
`escalation-epoch-change` 必填：

```yaml
from_escalation_epoch: <current integer>
to_escalation_epoch: <current + 1>
epoch_change_reason: replan | change-executor
requester_approved: true
```

`escalation-checkpoint` 必填：

```yaml
escalation_epoch: <integer>
trigger_attempt_id: <the third-or-later unique counted attempt>
unique_attempt_count: <deduplicated count in this epoch; >= 3>
checkpoint_decision: continue | replan | change-executor | escalate
checkpoint_rationale: <root-cause repetition, closure trend, or requester ruling>
```

`review-marker-clearance` 解除 §1 的留痕解析停機，必填：

```yaml
quarantined_comment_id: <GitHub comment 數值 ID；跨編輯穩定>
quarantined_comment_url: <該留言 URL>
quarantined_comment_author: <該留言的 GitHub author 帳號>
quarantined_body_sha256: <停機當下 comment body 原文 UTF-8 SHA-256>
quarantine_reason: unknown-version | missing-field | unknown-key | field-order | field-inconsistent | duplicate-conflict | edited-after-clearance
clearance_decision: malformed-ignored | superseded | forged-rejected | reissue-required | repaired-verified
superseding_attempt_id: <clearance_decision=superseded 時必填，且須為既存 attempt>
repaired_body_sha256: <clearance_decision=repaired-verified 時必填；修復後 body 原文 UTF-8 SHA-256>
clearance_authority: coordinator | requester
requester_decision_url: <clearance_authority=requester 時必填；需求方本人帳號所留裁定的留言 URL>
cleared_by: <GitHub account>
clearance_rationale: <非空>
```

此專用 type 不得與其他 lifecycle correction 混用，也不得用來變更 finding、attempt 或 epoch。它不建立 attempt、不計 iteration、不消耗 escalation 額度——停機是留痕缺陷，不是執行者的交付失敗。

**停機狀態由現行內容導出，不由簿記推定。** 定義「**已涵蓋**」＝ timeline 上存在針對該 `comment_id` 的有效 clearance，其 `quarantined_body_sha256` 或 `repaired_body_sha256` 等於該留言**現行** body 的 SHA-256。則：

> 一則留言處於停機狀態，當且僅當
> **（其現行 body 含受管轄但不合格的 marker　或　該 `comment_id` 曾被隔離）**
> **且　其現行 body 未被涵蓋。**

兩個子句缺一不可，這是本規則唯一不會產生死鎖的形狀。前括號決定「要不要人看」，後半決定「是否已經看過**這一份**內容」。若只用前括號，一則以 `malformed-ignored` 解除、內容未改的壞留言會因為 body 永遠不合格而永遠停機；若只用後半，從未被隔離的留言會因為沒有 clearance 而全部停機。

「曾被隔離」這一支保住了「解除的是這一份被人看過的內容，不是這個留言位置」——GitHub comment 可被編輯，隔離後的任何改動都必須再經人看過。但它**不得**造成無法解除：**任何** hash 變動都有對應的可發 clearance 路徑，adapter 不得以「現行 body 已合格、無壞內容可隔離」為由拒收 clearance。三種情形分別是：

- 編輯後 body **已合格**：前括號由「曾被隔離」滿足，且新 hash 未被涵蓋，故仍停機。以 `quarantine_reason: edited-after-clearance` ＋ `clearance_decision: repaired-verified` 解除，`repaired_body_sha256` 填修復後的 hash。**此路徑不要求現行 body 不合格，故恆可發**——這是消除死鎖的關鍵。
- 編輯後 body 仍不合格（或換成另一種不合格）：前括號由 marker 不合格滿足，依實際 `quarantine_reason` 對新 hash 另發 clearance。
- 從未被隔離的留言遭編輯：前括號兩支皆不成立，不停機。

adapter 實作本規則後，可窮舉的狀態組合是 **12 個**（現行 body 不合格 × 曾隔離 × 已涵蓋 × author 是否為授權 writer，扣除「未曾隔離卻已涵蓋」等不可達組合），其中 **6 個為停機**，且每一個都至少有一條可發的解除路徑並在發出後解除。非 writer author 的留言恆可走 `forged-rejected`／`reissue-required`（前者需需求方授權），因此嚴格的分類限制不會造成無路可解。任何實作若出現第 13 種狀態，或某個停機狀態無路可解，即是偏離本契約。

**已知限制**：若壞 marker 在**任何** clearance 被寫下之前就被編輯成合格內容，停機會靜默解除且事件流不留紀錄——消費者是唯讀的，系統對「曾經壞過但沒人記錄」沒有記憶，GitHub 的留言編輯歷史也非 API 可靠取得。此情形不會產生錯誤的裁決（合格 marker 仍須通過 `handoff-contract.md` §3.1.3 的三面一致才算裁決），但會失去一次竄改訊號。要消除它需要消費者在偵測到停機時即寫入紀錄，那是寫入端變更，不在本節範圍。

**修復方式有優先序。** 首選是**不編輯**：以正規寫入通道另發合法事件，再以 `superseded` 解除。編輯原留言會湮滅被隔離的原文，僅在無法重發時使用，且 `clearance_rationale` 必須載編輯前原文或其 hash，否則被解除的內容不可稽核。

**解除範圍以留言為單位**：timeline 上有多則不合格 marker 就需要多則 clearance，不得以一則概括。

各 `clearance_decision` 的語意與後續狀態：

- `malformed-ignored`：確認該留言是壞掉的 marker、不是裁決。消費者忽略它，恢復對該卡的自動判定。
- `superseded`：該留言已由另一則合法事件取代，須以 `superseding_attempt_id` 指向既存 attempt。恢復判定並以該 attempt 為準。
- `forged-rejected`：判定為冒充裁決。**強制 `clearance_authority: requester`**——偽造狀態面事件是安全事件，不由 Coordinator 單獨結案；消費者忽略該留言，並須另行記錄處置。
- `reissue-required`：留痕不足以裁決，須重新以正規寫入通道產生事件。解除停機，但**不得**因此判定該卡已有裁決；卡回 `🔍待查核`。
- `repaired-verified`：隔離後留言遭編輯，且修復後內容已經人核對。解除僅對 `repaired_body_sha256` 有效；再次編輯即再次停機。**adapter 必須另行驗證兩件事，缺一即 clearance 無效、停機維持**：(i) 該留言的**現行** body 確實已是合格 marker，或已完全不含 `wf-review-event:` 前綴；(ii) timeline 上該 `comment_id` 已有前一筆有效 clearance——`repaired-verified` 是「修復」，不是首次隔離的處置。少了 (i)，壞 marker 只要被改成**另一個**壞 marker 就能藉本出口涵蓋新 hash 而解除停機，繞過所有分類限制；這個出口是為了消除死鎖，不是為了提供無條件解鎖。

**分類界線必須可機械核對，不得靠自述降類。** 採用專案須依 `handoff-contract.md` §5 宣告被授權的 review event writer 帳號集合。adapter 比對 `quarantined_comment_author`：

- author **不在**該集合，且該留言（隔離當下**或**現行）含形式合格的 marker 或裁決標題 → **不得**使用 `malformed-ignored`，**也不得**使用 `repaired-verified`；只能是 `forged-rejected` 或 `reissue-required`。外人寫出看起來像裁決的東西，不是「寫壞了」；也不容許外人自行編輯自己的留言後以「已修復」洗白。
- author 在該集合內（自家 writer 自己寫壞）→ 可用 `malformed-ignored` 或 `repaired-verified`。
- 分類與 author 事實不符的 clearance **無效**，停機維持。

**requester 授權必須有可核對證據，且必須綁定到這一次解除。** `clearance_authority: requester` 必填 `requester_decision_url`。adapter 必須實際讀取該 URL 並逐項驗證，任一不符即 clearance 無效、停機維持：

1. **author**：該裁定留言的 GitHub author 等於卡面「需求」欄所載帳號。不得採信 `cleared_by` 或 `clearance_rationale` 的自述。
2. **同卡**：該裁定留言位於**本卡**的 Issue／PR，不接受其他卡或其他 repo 的 URL。
3. **綁定**：裁定內文必須明列本次解除的 `quarantined_comment_id`、對應的 body hash（`quarantined_body_sha256`，或 `repaired-verified` 時的 `repaired_body_sha256`），以及所授權的 `clearance_decision` 值。

第 3 條是**防重放**的關鍵，而且它不需要時鐘：body hash 在停機成立前並不存在，因此需求方任何既有的無關留言都不可能含有該 hash。以「裁定時間須晚於停機」來擋重放會引入時區與編輯時間的判定問題，那屬時間語意契約的範圍，本節刻意不走那條路。

這與 `handoff-contract.md` §3.1.2 收據同源：**帳號是平台事實，欄位值只是自述**。（§4 `escalation-epoch-change` 的 `requester_approved: true` 仍是自述型欄位；本節刻意不沿用該弱模式，是否追溯補強屬另案，不在此處變更。）

**append-only 不因解除而破例**：不得刪除被停機的留言，也不得回寫既有事件。完整 replay 必須能僅憑事件流重建每一次停機與其解除。

新增此 type 屬契約變更，適用範圍依本節末段的 `contract-baseline` cutover 機制；cutover 前的歷史事件維持原貌，不追溯要求補發 clearance。

`counts_toward_escalation` 是 adapter 依結構化欄位算出的投影，不得由 reviewer 以自由文字自行宣告。若同 SHA 有多個有效 reviewer 報告，adapter 先合併 findings 再計算一次；相同 `finding_id` 的衝突分類須由 Coordinator／需求方裁定，不得用陣列順序覆寫。cutover 前歷史事件維持原貌；採用專案以獨立 `contract-baseline` event 指定新契約開始時間，該 marker 為 one-shot cutover：不得附在 review 等其他事件上，啟用後再次出現必須 fail loud。
adapter 亦須以穩定 `finding_id`／`root_cause_id` 跨 attempt 推導 checkpoint：同根因出現於三個唯一可計數 attempt，或前一 attempt 的 accepted blocking finding 未在下一 attempt 明列 `resolved`／`withdrawn` 時，`checkpoint_decision` 只能是 `escalate`，不得信任手填的 `continue`。
