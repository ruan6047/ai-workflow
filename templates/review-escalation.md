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

- 任一相同 `root_cause_id` 累計在三個不同可計數 attempt 產出 finding **且在 trigger attempt 仍存活**（見下方「第一條件的存活判準」），或上一輪未閉合的 accepted blocking finding 在下一輪未處理且未經需求方 defer（見下方「查核規格變更與 deferred finding」）：轉 `🚨已升級`。兩個條件各自獨立成立；存活判準只作用於前者，defer 只作用於後者。
- findings 為不同根因、前輪均已閉合且 severity／剩餘範圍持續收斂：維持原 owner，交由 Coordinator 記錄「續修／重規劃」決定；只有需求方選擇升級才轉 `🚨已升級`。
- Critical finding 可立即 fail-closed 或暫停高風險操作，但不因 severity 單獨推定 executor 已連續失敗三次。

**checkpoint 的評估時點。** `trigger_attempt_id` 必須是**已記錄且已依 §3 判定 `counts_toward_escalation=true`** 的 attempt——`unique_attempt_count >= 3` 本來就無法在第三個可計數 attempt 的裁決落地前算出。因此第二條件的比較對是「前一個可計數 attempt N-1」與「trigger attempt N」，兩者的裁決都已存在，**trigger attempt 自己提出的 finding 從不屬於 carry set**。若在 trigger attempt 的裁決落地前就建立 checkpoint，第二條件會因「下一輪尚未表態」而恆真，`continue`／`replan`／`change-executor` 三個分支永遠不可達，該條件退化為無鑑別力——那是誤讀，不是本契約。

**有效 open finding。** 本節兩個條件共用同一個述詞：一個 finding 為**有效 open finding**，當且僅當它 `accepted=true`、`blocking=true`、`status=open`，且符合 §3 第 3～4 款。依 §5 末段，`status=withdrawn`、`accepted=false`，以及**仍為 `open` 但已不再符合 §3 可計數條件者**（例如 severity／`blocking` 經合法裁決降級），一律不是有效 open finding，adapter 必須將它移出 open set。這是既有規則，本節只是把它命名以便引用。

**第一條件的存活判準。** 只數「累計出現於三個唯一可計數 attempt」會使第一條件**一旦成立即永久為真**：某根因即使此後再也不產出任何 blocking finding，其後每一個 checkpoint 仍被迫記 `escalate`，該條件隨即失去鑑別力——這與本節「持續出現」的措辭不符，也與第二條件原本的缺陷同型。故第一條件成立需**同時**滿足兩件事：

1. **累計**：該 `root_cause_id` 曾在本 epoch 三個以上唯一可計數 attempt 產出符合 §3 第 3～4 款的 accepted blocking finding；
2. **存活**：在 trigger attempt N 的裁決落地當下，該 `root_cause_id` **仍至少有一個有效 open finding**。

累計數**永不遞減**：閉合既有 finding 不會抹掉歷史 occurrence（§5 對 `status=resolved` 已明定「不得洗掉先前真實 carry」）。可失效的只有存活；根因一旦重新產出有效 open finding，第一條件**立即**重新成立，不需要重新累積三次。

刻意**不**採「三個**連續**可計數 attempt」的讀法：那會讓每隔一輪出現一次的根因永遠湊不滿連續三輪而完全逃脫升級，用一個更窄的判準換掉一個真實的訊號。本判準只移除「已經停止的根因仍永久閂住」這一種誤報，不放過任何仍在活動的重複根因。

存活判準與第二條件正交：它只作用於根因的 occurrence 計數，不改變任何 carry set 成員的處置格；`deferred_findings` 亦不改變存活判定——deferred finding 的 `status` 仍是 `open`、仍是有效 open finding，**故 defer 一個根因的 finding 不會使該根因失去存活**。

**carry set 的界定。** carry set ＝ attempt N-1 的裁決落地當下的**有效 open finding** 全體（**不限於 N-1 當輪新提出者**，未閉合者一路承接）。成員身分固定於 N-1，處置則依 checkpoint 事件在 replay 中的位置判定：所有排在該 checkpoint 之前的有效 review 與 `review-correction` 都已套用（§2 末段「先更新實際 open set 再判斷」）。

carry set 中每個 finding 在 trigger attempt N 只能落在下列**六格之一，且必落在一格**：

| carry 處置 | 表示法 | 對第二條件 |
|---|---|---|
| `resolved` | N 的 review，或排在本 checkpoint 之前的 `review-correction`，明列該 `finding_id` | 不觸發 |
| `withdrawn` | 同上 | 不觸發 |
| 已非有效 open finding | N 或先行 correction 使其 `accepted=false`，或合法降級至不符 §3 第 3～4 款（§5 末段） | 不觸發 |
| 仍開啟 | N 明列該 `finding_id` 仍 `open`，且仍是有效 open finding | **觸發** |
| deferred | 本 checkpoint 的 `deferred_findings` 明列，且該筆全部必要條件成立 | 不觸發 |
| 未提及 | 以上皆非（含 defer 因條件不成立而失效者） | **觸發** |

第三格是 §5 末段既有規則的直接後果，不是新增出口：finding 被合法降級或撤銷採認後即非有效 open finding，adapter 本就必須將它移出 open set，因此它不可能同時是「未被處置」。**降級的合法性由 §2／§5 管轄**（衝突分類須經 `review-correction` 裁定），本節不另設判準。

**六格的前提是穩定 `finding_id`。** §2 要求 `finding_id` 為 stable id，本節與 §5 的 checkpoint 推導都據此跨 attempt 對齊。因此**把同一缺陷以新的 `finding_id` 重新提出，不構成對舊 `finding_id` 的任何處置**：舊 id 未被明列閉合就仍在它自己的格內（通常是「未提及」）而觸發第二條件。這是刻意的 fail-closed——換號重開與置之不理在留痕上無法區分，而前者本身即違反穩定 id 的要求。本節**不**定義「接續／承接」關係：那會新增一條語意軸（舊 id 算不算閉合、occurrence 是否重複計、carry 成員資格是否移轉），而既有要求已經排除了產生該關係的動作。cutover 前不滿足穩定 `finding_id` 的歷史事件依 §5 末段的 `contract-baseline` 維持原貌，不得反向套進六格。

「未提及」是預設格：**沉默不等於 deferred**。任何無法落入前五格的輸入一律落在此格並強制 `escalate`，adapter 不得另設「其餘」處置。同一 finding 的證據同時指向多格時，依「已離開 open set 的三格（`resolved`／`withdrawn`／已非有效 open finding）」＞ 仍開啟 ＞ deferred 的優先序取單一格；對已離開 open set 之 finding 的 defer 宣告視為無作用的冗贅，不使該 checkpoint 無效。

**查核指示變動與 deferred finding。** 有兩種**指示側**的合法動作會使 carry set 中的 finding 在該輪既非 `resolved` 也非 `withdrawn`：

- **規格收窄**（`spec-narrowed`）：需求方裁定該輪只搜特定根因、明文不逐條複驗前輪處置。
- **指示缺漏**（`instruction-omitted`）：派審指示**漏了**要求查核者逐項回報前輪 finding 的閉環狀態，查核報告因而沒有那一節。

兩者的差別只在前者是刻意、後者是疏漏；對事件流的效果完全相同，而第二條件只看「事件流上有沒有那個宣告」，不看為什麼沒有。若無出口，一次收窄或一次漏寫就機械上必然強制下一輪升級——把 Coordinator／需求方側的動作誤讀成執行者連續失敗。依 §3，這兩種成因本身都屬 `coordination`，本就不消耗 executor 額度；但 §3 管的是 attempt 是否計數，第二條件管的是 carry 是否被處置，**兩者是不同的閘門**，故仍需在 checkpoint 上有一個明示出口。

本出口是**事後的表示法**，不是預防機制：要讓 `instruction-omitted` 不再發生，該做的是在派審指示裡固定要求查核者逐項回報前輪 accepted blocking finding 的閉環狀態——那屬派審／handoff 範本的管轄，不在本檔。也**不**因成因是疏漏而放寬任何一款必要條件，尤其是「不得連續 defer」：同一 finding 被漏問兩次，正是需求方必須介入的狀態。

出口是 checkpoint 的 `deferred_findings`：**它只宣告「本輪不要求對該 finding 表態」，不改變 finding 本身。** deferred finding 的 `status` 仍是 `open`、`accepted` 仍是 `true`，仍留在 open set，仍完整計入 §3 的 `counts_toward_escalation` 推導。§2 的 `status` 三值封閉，**不得**新增 `deferred` 值；defer 處置的是「本輪的複驗義務」，不是 finding 的狀態。要改變 finding 本身只能走 `review-correction`。

單筆 defer 的必要條件（缺一即該筆無效，對應 finding 退回「未提及」格）：

1. `finding_id` 已存在於本 epoch 某個 attempt，且確實屬於本 checkpoint 的 carry set；
2. `deferred_by` 逐字等於卡面 `需求：` 欄宣告的帳號（`wfcli open` 寫入的 `requested_by`）。該欄未宣告或無法解析時本出口不可用，adapter 一律 fail-closed——這與 §5 對 `forged-rejected` 分類界線的處理同向：無法機械核對的授權不得以自述成立；
3. `deferred_by` 不得逐字等於本卡當前 owner，也不得等於本 epoch 任一 review event 的 `reviewer`。同一帳號兼任需求方與執行者／查核者時本出口不可用——defer 的裁定者必須不是被 defer 所嘉惠的人；
4. `defer_cause` 取值於 `spec-narrowed`｜`instruction-omitted`（不得自創成因），且 `defer_reason` 非空並載明對應的那一次事件：`spec-narrowed` 載明是哪一次查核規格變更，`instruction-omitted` 載明是哪一次派審指示漏了要求表態。**兩種成因都必須指向指示側的具體事實**——執行者忙不過來、時間不夠、finding 太難，都不是本出口的成因；
5. `defer_ruling_url` 指向該事實的留痕：`spec-narrowed` 指向需求方的規格變更裁定，`instruction-omitted` 指向那一則缺漏的派審指示本身（缺漏可由該則留痕直接核對，不必另造證據）。此欄是稽核指標，**不**充當授權證據——授權由第 2、3 款的身分比對成立。（不重蹈 §5 末段已撤回設計的錯誤：當內容由受該裁定影響的一方撰寫時，指向該內容的指標既不證明它當時已存在，也不證明裁定者看過它。）

**清償上限是機械的，不是「應儘速」。** checkpoint C 的 `deferred_findings` 中每個 `finding_id`，必須在**本 epoch 下一個 `escalation-checkpoint` C′** 之時，已由 C′ 的 trigger attempt 給出 `resolved`、`withdrawn` 或明列仍 `open`；落入「已非有效 open finding」格（經合法降級或撤銷採認而離開 open set）同樣算清償——複驗義務的對象已不存在，再要求對它表態沒有意義。逾此即逾期，C′ 的 `checkpoint_decision` 只能是 `escalate`。上限之所以是機械的：第三個之後**每一個**可計數 attempt 都必建 checkpoint，故「下一個 checkpoint」等價於「下一個可計數 attempt」，不需要時鐘、不需要預先知道未來的 `attempt_id`。給出「仍 `open`」算清償了複驗義務，但它本身即第二條件的觸發格，仍然強制 `escalate`——defer 延後的是**評估**，不是**結果**。

**不得連續 defer。** 同一 `finding_id` 出現於 C 的 `deferred_findings` 後，不得再出現於 C′ 的 `deferred_findings`；出現即該筆無效並強制 `escalate`。連兩輪無人對同一 accepted blocking finding 表態，正是需求方必須介入的狀態，而介入正是 `escalate` 的語意。此規則同時封死交替 defer 的繞道：finding 要活過 C′ 只能靠 `resolved`／`withdrawn`／合法降級，而那三者都已使它離開 open set，不可能在 C″ 再被 defer。

**與第一條件正交。** defer 不新增也不刪除任何 `root_cause_id` 的 occurrence，僅使該 finding 在本輪不產生新 occurrence。同根因已跨三個唯一可計數 attempt 出現時第一條件獨立成立，`deferred_findings` 不能使其失效。

**沒有 C′ 時 defer 自然失效，不構成放行。** 若本 epoch 不再出現可計數 attempt（卡片通過、停止，或以 `escalation-epoch-change` 換 epoch），清償義務隨之無對象而消滅——但 deferred finding 仍是 open 的 accepted blocking finding，仍留在 open set。**defer 從不閉合 finding，也從不授權在其未閉合的情況下結案**；「open blocking finding 尚存時可否 `APPROVE`」由 §2／§3 與 canonical §5 管轄，不因本節而改變。epoch 遞增後舊 epoch 的 `deferred_findings` 不隨之延續：新 epoch 從零計數（§4 末段），其第一個 checkpoint 的 carry set 依新 epoch 的 attempt 重新界定。

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
trigger_attempt_id: <the third-or-later unique counted attempt；其 review 裁決須已記錄>
unique_attempt_count: <deduplicated count in this epoch; >= 3>
checkpoint_decision: continue | replan | change-executor | escalate
checkpoint_rationale: <root-cause repetition, closure trend, or requester ruling>
deferred_findings:          # 選填，預設空陣列；語意與必要條件見 §4
  - finding_id: <既存於本 epoch，且屬本 checkpoint carry set 的 finding>
    defer_cause: spec-narrowed | instruction-omitted
    defer_reason: <非空；載明哪一次規格變更或哪一則派審指示缺漏使該 finding 未被表態>
    deferred_by: <卡面「需求：」欄宣告的帳號>
    defer_ruling_url: <該規格變更裁定，或該則缺漏的派審指示本身的留痕 URL>
```

`deferred_findings` 只表達「本輪不要求對該 finding 表態」，不得用來變更 finding 的 `status`／`accepted`／分類／根因，也不得用來閉合 finding——那些只能走 `review-correction`。單筆缺欄、`defer_cause` 不在列舉內、身分不符（§4 第 2、3 款）、finding 不在 carry set，或違反「不得連續 defer」者，該筆無效，對應 finding 落回「未提及」格並強制 `escalate`；其餘筆數不受牽連。空陣列與省略本欄語意相同。**對不在 carry set 的 finding 所作的宣告是無作用的冗贅**（§4 末段），不使整個 checkpoint 無效。

`review-marker-clearance` 解除 §1 的留痕解析停機，必填：

```yaml
quarantined_comment_id: <GitHub comment 數值 ID；跨編輯穩定>
quarantined_comment_url: <該留言 URL>
quarantined_comment_author: <該留言的 GitHub author 帳號>
quarantined_body_sha256: <停機當下 comment body 原文 UTF-8 SHA-256>
quarantine_reason: unknown-version | missing-field | unknown-key | field-order | field-inconsistent | duplicate-conflict | edited-after-clearance
clearance_decision: malformed-ignored | superseded | repaired-verified | reissue-required | forged-rejected
superseding_attempt_id: <clearance_decision=superseded 時必填，且須為既存 attempt>
repaired_body_sha256: <clearance_decision=repaired-verified 時必填；修復後 body 原文 UTF-8 SHA-256>
incident_record_url: <quarantined_comment_author 不在授權 writer 集合且內容看似裁決時必填；記錄該冒充事件處置的留言 URL>
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

adapter 實作本規則後，可窮舉的狀態組合是 **12 個**（現行 body 不合格 × 曾隔離 × 已涵蓋 × author 是否為授權 writer，扣除「未曾隔離卻已涵蓋」等不可達組合），其中 **6 個為停機**，且每一個都至少有一條**可解除**的路徑並在發出後解除。計算可解除路徑時**不計入 `forged-rejected`**，它只記錄不解除。非 writer author 的留言恆可走 `reissue-required`（並須附 `incident_record_url`），因此嚴格的分類限制不會造成無路可解。任何實作若出現第 13 種狀態，或某個停機狀態無可解除路徑，即是偏離本契約。

**已知限制**：若壞 marker 在**任何** clearance 被寫下之前就被編輯成合格內容，停機會靜默解除且事件流不留紀錄——消費者是唯讀的，系統對「曾經壞過但沒人記錄」沒有記憶，GitHub 的留言編輯歷史也非 API 可靠取得。此情形不會產生錯誤的裁決（合格 marker 仍須通過 `handoff-contract.md` §3.1.3 的三面一致才算裁決），但會失去一次竄改訊號。要消除它需要消費者在偵測到停機時即寫入紀錄，那是寫入端變更，不在本節範圍。

**修復方式有優先序。** 首選是**不編輯**：以正規寫入通道另發合法事件，再以 `superseded` 解除。編輯原留言會湮滅被隔離的原文，僅在無法重發時使用，且 `clearance_rationale` 必須載編輯前原文或其 hash，否則被解除的內容不可稽核。

**解除範圍以留言為單位**：timeline 上有多則不合格 marker 就需要多則 clearance，不得以一則概括。

各 `clearance_decision` 的語意與後續狀態：

- `malformed-ignored`：確認該留言是壞掉的 marker、不是裁決。消費者忽略它，恢復對該卡的自動判定。
- `superseded`：該留言已由另一則合法事件取代，須以 `superseding_attempt_id` 指向既存 attempt。恢復判定並以該 attempt 為準。
- `forged-rejected`：判定該留言為冒充裁決。**它不解除停機**——偽造是安全事件，不該由任何機器判定自動放行。本 decision 只是把「這是冒充」這個判定寫進事件流；停機持續，直到另發一則能解除的 decision（通常是事件處置完成後的 `reissue-required`）。宣告與恢復是**兩個動作**，刻意不合併：合併就等於讓一則事件同時扮演告警與解除，而那正是可被重放攻擊的形狀。
- `reissue-required`：留痕不足以裁決，須重新以正規寫入通道產生事件。解除停機，但**不得**因此判定該卡已有裁決；卡回 `🔍待查核`。
- `repaired-verified`：隔離後留言遭編輯，且修復後內容已經人核對。解除僅對 `repaired_body_sha256` 有效；再次編輯即再次停機。**adapter 必須另行驗證兩件事，缺一即 clearance 無效、停機維持**：(i) 該留言的**現行** body 確實已是合格 marker，或已完全不含 `wf-review-event:` 前綴；(ii) timeline 上該 `comment_id` 已有前一筆有效 clearance——`repaired-verified` 是「修復」，不是首次隔離的處置。少了 (i)，壞 marker 只要被改成**另一個**壞 marker 就能藉本出口涵蓋新 hash 而解除停機，繞過所有分類限制；這個出口是為了消除死鎖，不是為了提供無條件解鎖。

**分類界線必須可機械核對，不得靠自述降類。** 採用專案須依 `handoff-contract.md` §5 宣告被授權的 review event writer 帳號集合。adapter 比對 `quarantined_comment_author`：

- author **不在**該集合，且該留言（隔離當下**或**現行）含形式合格的 marker 或裁決標題 → **不得**使用 `malformed-ignored`，**也不得**使用 `repaired-verified`；只能是 `forged-rejected` 或 `reissue-required`。外人寫出看起來像裁決的東西，不是「寫壞了」；也不容許外人自行編輯自己的留言後以「已修復」洗白。
- author 在該集合內（自家 writer 自己寫壞）→ 可用 `malformed-ignored` 或 `repaired-verified`。
- 分類與 author 事實不符的 clearance **無效**，停機維持。

**冒充事件必須留下處置紀錄。** 當 `quarantined_comment_author` 不在授權 writer 集合、且該留言（隔離當下或現行）含形式合格 marker 或裁決標題時，**無論使用哪一個 `clearance_decision`**，都必須填 `incident_record_url` 指向記錄該事件處置的留言。這條不封鎖任何解除路徑——Coordinator 仍可用 `reissue-required` 讓卡片繼續前進——但它確保「有人冒充過裁決」這個訊號不會因為換一個較溫和的 decision 而靜默消失。缺 `incident_record_url` 即 clearance 無效、停機維持。

> **已撤回的設計（保留記錄以免重蹈）**：先前版本要求 `clearance_authority: requester` ＋ `requester_decision_url`，並主張「body hash 在停機成立前並不存在，故可作為防重放 nonce、不需時鐘」。**該推理是錯的**：nonce 的要件是攻擊者無法預測，但被隔離的內容正是攻擊者所撰寫，他能預先算出自己的 hash。攻擊者可先建立無害留言取得 `comment_id`、選定未來的壞 body 並算出其 hash、取得需求方對該組 ID／hash 的裁定，再把同一留言編輯成預定的壞 body——舊裁定會通過 author、同卡、ID、hash 與 decision 的全部檢查。hash 綁定證明的是「這則裁定指涉這串位元組」，既不證明該內容當時已存在，也不證明裁定者看過它。
>
> 修法不是替該機制補上新鮮性證據，而是**移除它所保護的能力**：`forged-rejected` 不再自動解除停機，requester 授權路徑因此無用武之地，整個重放面隨之消失而非被修補。這也讓本節不需要引入時鐘或 revision 排序，與時間語意契約保持正交。

**append-only 不因解除而破例**：不得刪除被停機的留言，也不得回寫既有事件。完整 replay 必須能僅憑事件流重建每一次停機與其解除。

新增此 type 屬契約變更，適用範圍依本節末段的 `contract-baseline` cutover 機制；cutover 前的歷史事件維持原貌，不追溯要求補發 clearance。

`counts_toward_escalation` 是 adapter 依結構化欄位算出的投影，不得由 reviewer 以自由文字自行宣告。若同 SHA 有多個有效 reviewer 報告，adapter 先合併 findings 再計算一次；相同 `finding_id` 的衝突分類須由 Coordinator／需求方裁定，不得用陣列順序覆寫。cutover 前歷史事件維持原貌；採用專案以獨立 `contract-baseline` event 指定新契約開始時間，該 marker 為 one-shot cutover：不得附在 review 等其他事件上，啟用後再次出現必須 fail loud。
adapter 亦須以穩定 `finding_id`／`root_cause_id` 跨 attempt 推導 checkpoint。下列任一條件成立時，`checkpoint_decision` 只能是 `escalate`，不得信任手填的 `continue`；兩條件各自獨立成立，`deferred_findings` 只作用於第二條件：

1. 同一 `root_cause_id` **累計**出現於三個唯一可計數 attempt，**且**在 trigger attempt 的裁決落地當下仍至少有一個有效 open finding（§4「第一條件的存活判準」）。累計數永不遞減，可失效的只有存活；根因重新產出有效 open finding 時本條件立即重新成立，不需重新累積；
2. 本 checkpoint 的 carry set（§4：前一個可計數 attempt 裁決落地當下的有效 open finding 全體）中，有任一 finding 在 trigger attempt 落入 §4 的「仍開啟」或「未提及」格；或前一次 checkpoint 的 `deferred_findings` 有成員逾期未清償，或被連續第二次 defer。

carry set 的成員身分固定於前一個可計數 attempt，處置依 checkpoint 事件在 replay 中的位置計算（§2 末段）；trigger attempt 自己提出的 finding 不屬 carry set。第二條件的評估必須發生在 trigger attempt 的裁決已記錄之後，否則它恆真而失去鑑別力（§4「checkpoint 的評估時點」）。
