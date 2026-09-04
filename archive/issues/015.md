# #15 WF-REVIEW-EVENT-MARKER-CONTRACT1 將 wf-review-event:v1 納入 handoff 契約
- state: closed  created: 2026-08-08T16:15:34Z  closed: 2026-08-10T11:04:37Z
- url: https://github.com/ruan6047/ai-workflow/issues/15
- comments: 9

## Body

- 需求：ruan6047　規劃：GPT-5@Codex
- 執行：待指派　查核：獨立校讀
- Initiative：—　spec 基線：ai-workflow commit 7c003b3：review.py 已輸出 wf-review-event:v1；templates/handoff-contract.md §3.1 僅定義 receipt。
- DB：db_scope=none
- 服務的原始目標：讓所有狀態面工具可依單一權威契約辨識 review event 與 review receipt，避免解析器各自猜測。

## 核心痛點

- **痛點**：wf-review-event:v1 已成為程式輸出的狀態面事件識別符，但 handoff 契約未定義其語法、欄位、版本化與 receipt 的關係；其他工具無可引用的權威規格。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:templates/handoff-contract.md",
    "file:docs/CONSUMER_CONFORMANCE.md",
    "file:templates/review-escalation.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] templates/handoff-contract.md §3.1 明確定義 wf-review-event:v1 的用途、完整 marker 語法與必填 card_id、source_sha、attempt_id。
- [ ] 明確說明 event 與 wf-review-receipt:v1 的角色差異、產生者與可作為狀態面裁決依據的條件。
- [ ] 定義未知版本或缺欄 marker 的 fail-closed 處理，不改變既有 legacy event 相容規則。

## 驗證

- [ ] 以 rg 核對 review.py 的 renderer 輸出與模板逐欄一致。
- [ ] 校讀確認只修改權威契約文件，不修改 CLI 行為或 Project 狀態。

## PM scope amendment（2026-08-10）

- 需求方裁決：將 `file:docs/CONSUMER_CONFORMANCE.md` 與 `file:templates/review-escalation.md` 納入本卡。
- 目的：針對 R1-002，在權威契約中完整定義 per-card halt 的可執行解除路徑；不得只登記後續缺口。
- 新增驗收：明定壞 marker 的唯一識別、可提出解除者、必填證據、裁定動作、重播／優先序，以及 consumer 如何解除 halt；以可重跑測試或探針證明。
- 邊界：不修改 CLI 行為或收據格式；若實作 consumer 才能滿足 R1-001／R1-003，須另開後續程式卡。
\n## Log

- 2026-08-09T00:15:32+08:00 open by GPT-5@Codex；owner 待指派；iteration 0。
- 2026-08-10T17:40:25+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 1；SHA e419ba8731c58d6dd3ab5c785c86a68c69d84d04；證據 需求方 2026-08-10 裁決：R1-002 不得僅登記，將 docs/CONSUMER_CONFORMANCE.md 與 templates/review-escalation.md 納入 scope，於本卡定義 per-card halt 的可執行解除路徑；R1-001／R1-003 的 consumer 程式實作仍脫鏈後續卡。。
- 2026-08-10T17:54:41+08:00 handoff by wf-cli → owner GPT-5@Codex（跨家族 R2 查核）；iteration 1；SHA 4c11819b0e7ac5bfae397742334624f3a5e34390；證據 R1-002 依需求方 scope amendment 已完成：新增 review-marker-clearance，定義 comment_id+body_sha256 雙欄識別、clearance 決策與授權、hash 變動重停機、forged-rejected 需求方授權、三層 gate 優先序與 replay 規則；同步修正 CONSUMER_CONFORMANCE 落差 7/8 路由。範圍僅 handoff-contract、review-escalation、CONSUMER_CONFORMANCE；cli 零改動；uv run pytest -q=185 passed。。
- 2026-08-10T18:14:03+08:00 handoff by wf-cli → owner 獨立校讀（須換模型家族）；iteration 1；SHA c29a4b37a3cb24122552eb704569cd81f8660e90；證據 分支 claude/WF-REVIEW-EVENT-MARKER-CONTRACT1 已 push；R2 兩項 blocking finding 已修（死鎖消除經六狀態窮舉驗證、偽造分類改為以 comment author 機械核對）；cli/ 零改動、185 passed。
- 2026-08-10T18:32:57+08:00 handoff by wf-cli → owner 獨立校讀（須換模型家族）；iteration 1；SHA d19aea5434be70987e7372591a8ed25f6b09ee43；證據 R3 兩項 blocking finding 已修：repaired-verified 補三道前提（現行 body 須合格／須有前一筆 clearance／author 分類限制涵蓋之）、requester 裁定改三項核對（author＋同卡＋內文綁 comment_id 與 body hash，以 hash 為 nonce 防重放、不引入時鐘）。加前提後重新窮舉：可達 12／停機 6／死鎖 0，契約狀態數字同步由 6/3 改為 12/6。另明文揭露一項自查限制（clearance 前即被編輯成合格內容會靜默解除）。cli/ 零改動、185 passed。
- 2026-08-10T18:48:43+08:00 handoff by wf-cli → owner 獨立校讀（須換模型家族）；iteration 1；SHA 07358d772146b63133fd16c2fe0d1d222dcd6677；證據 R4-001 已修：撤回 hash-as-nonce 防重放推理（內容由攻擊者撰寫故 hash 可預先計算），改為移除 forged-rejected 的自動解除能力，並刪除 clearance_authority／requester_decision_url／§5 需求方帳號欄；新增 incident_record_url 保住偽造訊號。淨刪除 +9 −16。重新窮舉（可解除路徑不計 forged-rejected）：可達 12／停機 6／死鎖 0。cli/ 零改動、185 passed。
- 2026-08-10T18:58:27+08:00 review by wf-cli → APPROVE（✅通過）；查核者 獨立校讀（GitHub author ruan6047 轉貼；模型／工具為自述）；core_pain_resolved yes；self_run 5 項；findings 0 項（blocking 0）；attempt WF-REVIEW-EVENT-MARKER-CONTRACT1-e0-07358d772146b63133fd16c2fe0d1d222dcd6677。
- 2026-08-10T19:18:00+08:00 tier correction by Claude Opus 5@Claude Code；Project 級別欄由 T1 改為 T3（本卡自始為 T3 設計／契約卡，中途並擴大 scope 納入紅線檔 review-escalation.md；開卡時填錯且 wfcli 開卡後無法更正）。以 Project GraphQL mutation 直接寫入，繞過 wfcli 唯一寫入通道——此缺口即 #12 的範圍（通用卡面修訂見 #19）。查核不受影響：五輪均按紅線標準跨模型家族進行。
- 2026-08-11T01:47:34+08:00 handoff by wf-cli → owner ruan6047；iteration 1；SHA dbfdb9c85fa92fff81efcc6b01a2a275f6378091；證據 已 APPROVE、已 merge 至 main dbfdb9c85fa92fff81efcc6b01a2a275f6378091、worktree 與分支已清、Issue 已關閉；本次補做 release 轉終態以釋放資源宣告（先前結案漏此步，導致 assign 將已完成卡誤判為活卡）。


## Comment 5238836386 · 2026-08-10T10:15:03Z

## 派審：R3 獨立校讀

⚠️ **審核對象是本卡 `ruan6047/ai-workflow#15`（Issue），不是 `ruan6047/cpbl-analytics#15`。**
後者是 2026-06 已合併的前端 PR「首頁對戰成績矩陣」，與本卡無關。R2 之前曾發生過一次審錯對象，故此處逐字標明。本卡是純文件治理，**零程式碼改動**。

### 進駐與身分核對

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-review-event-marker-contract1
分支：claude/WF-REVIEW-EVENT-MARKER-CONTRACT1
被審 SHA：c29a4b37a3cb24122552eb704569cd81f8660e90
基線：origin/main d9d17a6
iteration：1（R1、R2 皆 REQUEST_CHANGES，本輪為第三次查核）
```

第一步先核對，不符就停下回報，不要繼續：

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-review-event-marker-contract1
git rev-parse HEAD && git diff --name-only origin/main
```

預期 `c29a4b3…` 與三個檔案：`docs/CONSUMER_CONFORMANCE.md`、`templates/handoff-contract.md`、`templates/review-escalation.md`。**若出現 `web/` 或 `src/cpbl/` 底下的檔案，代表進錯 repo。**

### 本卡在做什麼

`wfcli review` 每次寫裁決留言都會輸出一個 `wf-review-event:v1` 標記，程式已在輸出、`doctor.py` 已在讀，但從未有文件定義過它。本卡把它寫成權威契約，並處理隨之而來的三件事：標明規則尚未生效、建立消費者落差登記、定義停機的解除路徑。

### 驗收條件

1. 卡面原三條驗收：§3.1 是否定義 `wf-review-event:v1` 的用途、完整 marker 語法與必填三欄；是否說明 event 與 receipt 的角色差異、產生者與可作為狀態面裁決的條件；是否定義未知版本與缺欄的 fail-closed 且不改變 legacy 相容規則。
2. PM 追加的驗收：per-card halt 的**壞 marker 識別／授權解除者／證據／裁定動作／重播與優先序／consumer 解鎖行為**是否逐項落地於 `review-escalation.md` §5。
3. R1 四項與 R2 兩項 finding 的處置是否成立。
4. 是否只改上列三檔，未動任何 CLI 行為與 Project 狀態。

### 必跑（`self_run` 需附實際輸出）

```bash
cd cli && uv run pytest -q          # 預期 185 passed
git status --porcelain cli/         # 預期空
```

另請逐字重跑 `docs/CONSUMER_CONFORMANCE.md` §1.2 內嵌的五案例探針（預期五種壞 marker 與對照組**全部**回 `recorded`，與落差登記一致——這是已登記的 fail-open，不是本輪新缺陷）。

### 請特別質疑這五點

1. **死鎖是否真的消除。** R2-001 指出編輯修復會造成無法解除的停機。修法是把停機改成合取式「（不合格 或 曾隔離）且 未涵蓋現行 hash」，並新增恆可發的 `edited-after-clearance` ＋ `repaired-verified` 出口。執行者宣稱以窮舉驗證：可達狀態六個、停機三個、死鎖零。**請自行重新窮舉，不要採信該結論**；特別檢查是否存在執行者未列舉的第七種可達狀態。
2. **偽造分類是否真的擋得住。** 界線是比對 `quarantined_comment_author` 是否在專案宣告的 writer 帳號集合內。請檢查：若專案未宣告該集合會怎樣（契約說一律 fail-closed，是否足夠）；`requester_decision_url` 的 author 比對能否被繞過。
3. **新 event type 是否必要。** `review-marker-clearance` 是否與既有 `review-correction`／`status-change` 語意重疊，本可沿用而不必新增。
4. **三個 gate 的優先序是否真的不互鎖**（`review-escalation.md` §2 末段），有無死鎖路徑。
5. **per-card halt 的可用性代價是否被低估**：任何有留言權限者貼一行壞 marker 即可凍結整張卡。

### 已知且刻意保留的落差（非本輪缺陷，勿重複開單）

`doctor.py` 目前對五種不合格 marker 全部回 `recorded`，§3.1.4／§3.1.5 在本 repo **尚未生效**。這是**刻意標記**的狀態，登記於 `docs/CONSUMER_CONFORMANCE.md`，consumer 修正歸 [#17](https://github.com/ruan6047/ai-workflow/issues/17)（依需求方裁決不併入本卡），語意比對的結構化承載設計歸 [#16](https://github.com/ruan6047/ai-workflow/issues/16)。請查核「標記是否誠實完整」，而非要求本卡修 consumer。

### 環境紅線與獨立性

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。執行者為 Claude Opus 5@Claude Code；本 repo 規則屬 🔴紅線，依 `CLAUDE.md` 查核**必須換模型家族或由需求方 sign-off**。

若你無法執行 `wfcli`，請依 `templates/handoff-contract.md` §3.1.2 在本 Issue 留一則 `wf-review-receipt:v1` 收據（`card_id`、完整 `source_sha`、查核報告原文 UTF-8 `report_sha256`），由 PM 對帳後轉錄；否則裁決會停在「已發生但不可觀測」。

**輸出**：依 `templates/review-prompt.md` §5 的結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5238926349 · 2026-08-10T10:24:42Z

<!-- wf-review-receipt:v1
card_id: WF-REVIEW-EVENT-MARKER-CONTRACT1
source_sha: c29a4b37a3cb24122552eb704569cd81f8660e90
report_sha256: b0f1837ee5b09d8f7fd1f415fa375d548002f6a74d8985cde007fcf5aaa27388
-->

core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git rev-parse HEAD && git diff --name-only origin/main"
    observed: "c29a4b37a3cb24122552eb704569cd81f8660e90；僅 docs/CONSUMER_CONFORMANCE.md、templates/handoff-contract.md、templates/review-escalation.md。"
  - command: "cd cli && uv run pytest -q"
    observed: "185 passed in 1.47s"
  - command: "docs/CONSUMER_CONFORMANCE.md §1.2 probe"
    observed: "五種不合格 marker 與對照組皆為 recorded；與已登記的 fail-open 落差一致。"
  - command: "git status --porcelain cli/"
    observed: "空。"
findings:
  - finding_id: "WF-REVIEW-EVENT-MARKER-CONTRACT1-R3-001"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: "repaired-clearance-semantic-bypass"
    evidence: "review-escalation.md §5 only requires repaired_body_sha256 for repaired-verified. It does not require the current body to be a legal marker, nor bind the decision to a genuine edit-repair transition. An external author can post bad X, receive a clearance, edit to bad Y, then a repaired-verified clearance covering Y; C=1 clears the halt despite Y remaining invalid. The author-classification rule prohibits only malformed-ignored, so it does not prevent this route."
    disposition: "Require adapter to re-parse the current body as legal before repaired-verified is valid, require edited-after-clearance plus a prior valid clearance for the same comment, and make violation fail closed."
  - finding_id: "WF-REVIEW-EVENT-MARKER-CONTRACT1-R3-002"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: "requester-decision-evidence-replay"
    evidence: "review-escalation.md §5 verifies only that requester_decision_url author equals the card requester. It does not require that decision to be on this card, identify quarantined_comment_id/body hash, or authorize forged-rejected. The requester's unrelated/old comment URL can therefore be replayed to clear any forged marker."
    disposition: "Require the cited decision to be on the same card and bind it to the clearance action plus quarantined_comment_id and current/isolated body hash; otherwise keep the halt."

## Comment 5239013086 · 2026-08-10T10:34:03Z

## 派審：R4 獨立校讀（取代前一則 R3 派審詞）

⚠️ **審核對象是本卡 `ruan6047/ai-workflow#15`（Issue），不是 `ruan6047/cpbl-analytics#15`。** 後者是 2026-06 已合併的前端 PR「首頁對戰成績矩陣」，與本卡無關；曾發生過一次審錯對象，故逐字標明。本卡是純文件治理，**零程式碼改動**。

### 進駐與身分核對

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-review-event-marker-contract1
分支：claude/WF-REVIEW-EVENT-MARKER-CONTRACT1
被審 SHA：d19aea5434be70987e7372591a8ed25f6b09ee43   ← 已非 R3 的 c29a4b3
基線：origin/main d9d17a6
iteration：1（R1／R2／R3 皆 REQUEST_CHANGES，本輪為第四次查核）
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-review-event-marker-contract1
git rev-parse HEAD && git diff --name-only origin/main
```

預期 `d19aea5…` 與三個檔案：`docs/CONSUMER_CONFORMANCE.md`、`templates/handoff-contract.md`、`templates/review-escalation.md`。**若出現 `web/` 或 `src/cpbl/` 底下的檔案，代表進錯 repo。**

### 本輪修了什麼（R3 兩項 blocking）

**R3-001 `repaired-verified` 繞過**：停機一旦「已涵蓋」即解除，而該 decision 原本只要求填 `repaired_body_sha256`，未要求現行 body 真的合格——壞 marker 改成另一個壞 marker 即可解鎖。補三道條件：現行 body 須確已合格（或完全不含 `wf-review-event:` 前綴）、該留言須已有前一筆有效 clearance、author 分類限制一併涵蓋 `repaired-verified`。

**R3-002 requester 裁定可重放**：原本只比對 author。改為三項核對——author 等於卡面需求方、裁定留言位於本卡、內文明列 `quarantined_comment_id` 與對應 body hash 及所授權的 decision。第三項刻意**不用時間先後**防重放，改以 hash 為 nonce（hash 在停機成立前並不存在），與時間語意契約保持正交。

### 本輪最需要打的一點

加入前提條件**本身就可能製造新的無路可解狀態**——R2 修死鎖、R3 修繞過，每一輪都在收緊，而收緊正是死鎖的來源。執行者宣稱重新窮舉（新增 author 維度）得到：**可達狀態 12、停機 6、死鎖 0**，並已把契約正文的狀態數字由 6/3 同步改為 12/6。

**請自行重建這個狀態空間，不要採信上述結論。** 具體請找：

1. 是否存在執行者未列舉的第 13 種可達狀態（例如把「內容是否看起來像裁決」獨立成第五個維度後）。
2. 非授權 writer 的留言在某些組合下，是否實際上只剩需要需求方授權的路徑，而需求方不可得時即等同無路可解——這是「形式上有路、實務上鎖死」。
3. 三道新前提彼此是否可能互相矛盾（例如要求「已有前一筆有效 clearance」，但前一筆因 hash 變動而失效時，該留言是否還算「已有」）。

### 其餘驗收

1. 卡面原三條：§3.1 是否定義 `wf-review-event:v1` 的用途、完整 marker 語法與必填三欄；是否說明 event 與 receipt 的角色差異、產生者與可作為狀態面裁決的條件；是否定義未知版本與缺欄的 fail-closed 且不改變 legacy 相容規則。
2. PM 追加的一條：per-card halt 的壞 marker 識別／授權解除者／證據／裁定動作／重播與優先序／consumer 解鎖行為，是否逐項落地於 `review-escalation.md` §5。
3. R1 四項、R2 兩項、R3 兩項 finding 的處置是否成立。
4. 是否只改上列三檔，未動任何 CLI 行為與 Project 狀態。
5. 契約正文所有量化宣稱（12／6／0）是否與可重跑證據一致。

### 必跑（`self_run` 需附實際輸出）

```bash
cd cli && uv run pytest -q          # 預期 185 passed
git status --porcelain cli/         # 預期空
```

另請逐字重跑 `docs/CONSUMER_CONFORMANCE.md` §1.2 內嵌的五案例探針（預期五種壞 marker 與對照組**全部**回 `recorded`——這是已登記的 fail-open，非本輪新缺陷）。

### 執行者主動揭露、非本輪缺陷

- `doctor.py` 目前對五種不合格 marker 全回 `recorded`，§3.1.4／§3.1.5 在本 repo **尚未生效**。這是刻意標記的狀態，登記於 `docs/CONSUMER_CONFORMANCE.md`；consumer 修正歸 [#17](https://github.com/ruan6047/ai-workflow/issues/17)（依需求方裁決不併入本卡），語意比對的結構化承載設計歸 [#16](https://github.com/ruan6047/ai-workflow/issues/16)。請查核「標記是否誠實完整」，而非要求本卡修 consumer。
- 壞 marker 若在**任何** clearance 寫下前就被編輯成合格內容，停機會靜默解除且不留紀錄。此限制由執行者自查發現並已明文寫入契約；請判斷該揭露是否足夠，或應升為 blocking。

### 環境紅線與獨立性

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。執行者為 Claude Opus 5@Claude Code；本 repo 規則屬 🔴紅線，查核**必須換模型家族或由需求方 sign-off**。

若你無法執行 `wfcli`，請依 `templates/handoff-contract.md` §3.1.2 在本 Issue 留一則 `wf-review-receipt:v1` 收據（`card_id`、完整 `source_sha`、查核報告原文 UTF-8 `report_sha256`），由 PM 對帳後轉錄；否則裁決會停在「已發生但不可觀測」。

**輸出**：依 `templates/review-prompt.md` §5 的結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5239039026 · 2026-08-10T10:36:52Z

<!-- wf-review-receipt:v1
card_id: WF-REVIEW-EVENT-MARKER-CONTRACT1
source_sha: d19aea5434be70987e7372591a8ed25f6b09ee43
report_sha256: dac8f768391d28054a621981caff4d00ecfd4dbcafe371fa7d4b96fc9d84872a
-->

core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git rev-parse HEAD && git diff --name-only origin/main"
    observed: "d19aea5434be70987e7372591a8ed25f6b09ee43；僅 docs/CONSUMER_CONFORMANCE.md、templates/handoff-contract.md、templates/review-escalation.md。"
  - command: "cd cli && uv run pytest -q"
    observed: "185 passed in 1.45s"
  - command: "docs/CONSUMER_CONFORMANCE.md §1.2 probe"
    observed: "五種不合格 marker 與對照組皆為 recorded；與已登記的 fail-open 落差一致。"
  - command: "git status --porcelain cli/"
    observed: "空。"
findings:
  - finding_id: "WF-REVIEW-EVENT-MARKER-CONTRACT1-R4-001"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: "requester-decision-preauthorization-replay"
    evidence: "The claim that the body hash cannot exist before halt is false. An attacker can create a harmless comment to obtain comment_id, choose a future bad body/hash, obtain a requester decision on this card binding that ID/hash/forged-rejected, then edit the same comment to the planned bad body. The old decision now passes author, same-card, ID, hash, and decision checks, so it clears the subsequent forged marker. No collision or timestamp ambiguity is required."
    disposition: "Do not treat a pre-computable body hash as a freshness nonce. Require an immutable, post-observation quarantine witness/nonce generated after the bad revision is observed, or retain a platform-verifiable ordering/revision proof; otherwise forged-rejected must remain halted for manual handling."

## Comment 5239153770 · 2026-08-10T10:49:47Z

## 派審：R5 獨立校讀（取代前一則 R4 派審詞）

⚠️ **審核對象是本卡 `ruan6047/ai-workflow#15`（Issue），不是 `ruan6047/cpbl-analytics#15`**（後者是 2026-06 已合併的前端 PR，曾發生過一次審錯對象）。本卡是純文件治理，**零程式碼改動**。

### 進駐與身分核對

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-review-event-marker-contract1
分支：claude/WF-REVIEW-EVENT-MARKER-CONTRACT1
被審 SHA：07358d772146b63133fd16c2fe0d1d222dcd6677   ← 已非 R4 的 d19aea5
基線：origin/main d9d17a6
iteration：1（R1–R4 皆 REQUEST_CHANGES，本輪為第五次查核）
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-review-event-marker-contract1
git rev-parse HEAD && git diff --name-only origin/main
```

預期 `07358d7…` 與三個檔案：`docs/CONSUMER_CONFORMANCE.md`、`templates/handoff-contract.md`、`templates/review-escalation.md`。**若出現 `web/` 或 `src/cpbl/` 底下的檔案，代表進錯 repo。**

### 本輪修了什麼（R4-001）

執行者的防重放推理被打穿且**已撤回**。原主張「body hash 在停機成立前不存在，故可作為 nonce、不需時鐘」是錯的：nonce 的要件是攻擊者無法預測，但被隔離的內容正是攻擊者所撰寫，他能預先算出自己的 hash。

修法**不是**補新鮮性證據，而是移除被保護的能力：

- `forged-rejected` **不再自動解除停機**，退化為記錄性判定；恢復另發 `reissue-required`。宣告與恢復拆成兩個動作。
- 刪除 `clearance_authority`、`requester_decision_url`，以及 `handoff-contract.md` §5 為其而設的需求方帳號宣告欄。
- 新增 `incident_record_url`：非授權 writer 作者且內容看似裁決時，無論用哪個 decision 都必須附冒充事件處置紀錄（依需求方裁決不封鎖降類路徑）。
- 錯誤設計與其被打穿的理由，保留在 §5 的「已撤回的設計」區塊。

本輪是 diff **淨刪除**（+9 −16）。

### 本輪最需要打的三點

1. **移除能力是否真的消掉了攻擊面，而不是把它推到別處。** 現在 `reissue-required` 成為所有停機的通用解除路徑，且只需 Coordinator。請檢查：這是否等於把原本要需求方把關的情境，整批降級為 Coordinator 可單獨處置？`incident_record_url` 是否足以補償，還是只是留痕而無實質約束？
2. **窮舉是否仍完整。** 執行者宣稱：可解除路徑不計 `forged-rejected` 後，可達狀態 12、停機 6、死鎖 0，非 writer 恆可走 `reissue-required`。**請自行重建狀態空間**，特別檢查「僅記錄不解除」的 decision 是否在某些組合下讓卡片實質卡死（形式上有路、實務上無人可走）。
3. **`forged-rejected` 與 `reissue-required` 的先後是否可被跳過。** 契約說宣告與恢復是兩個動作，但沒有規定必須先宣告才能恢復。是否應要求：一旦某留言曾被 `forged-rejected`，其後的解除必須附 `incident_record_url`？

### 其餘驗收

1. 卡面原三條：§3.1 是否定義 `wf-review-event:v1` 的用途、完整 marker 語法與必填三欄；是否說明 event 與 receipt 的角色差異、產生者與可作為狀態面裁決的條件；是否定義未知版本與缺欄的 fail-closed 且不改變 legacy 相容規則。
2. PM 追加的一條：per-card halt 的壞 marker 識別／授權解除者／證據／裁定動作／重播與優先序／consumer 解鎖行為，是否逐項落地於 `review-escalation.md` §5。
3. R1 四項、R2／R3／R4 各兩項與一項 finding 的處置是否成立。
4. 是否只改上列三檔，未動任何 CLI 行為與 Project 狀態。
5. 契約所有量化宣稱（12／6／0）與可重跑證據是否一致；已移除欄位在規範性文字中是否 0 殘留（撤回記錄區塊除外）。

### 必跑（`self_run` 需附實際輸出）

```bash
cd cli && uv run pytest -q          # 預期 185 passed
git status --porcelain cli/         # 預期空
```

另請逐字重跑 `docs/CONSUMER_CONFORMANCE.md` §1.2 內嵌的五案例探針（預期五種壞 marker 與對照組**全部**回 `recorded`——已登記的 fail-open，非本輪缺陷）。

### 給查核者的一個判斷請求（超出逐條驗收）

本卡已五輪查核，**五個 blocking finding 全部落在同一層**：clearance 的授權與解除設計。相對地，`handoff-contract.md` 的核心部分（marker 語法、必填三欄、三面一致、legacy 語法判準、fail-closed 作用域）自 R1 之後未再被打穿。

請一併判斷：clearance 機制的複雜度是否已超過它要解決的問題。若你認為是，執行者已備妥的替代方案是——**將 §3.1.4／§3.1.5 退回最保守版本（不合格即停機、只有 Coordinator 可解、不分類、不談語意等價），把 clearance 的分類與授權設計整包移交 [#16](https://github.com/ruan6047/ai-workflow/issues/16) 連同結構化承載一起做**。請明確表態支持或反對，這比再開一個同層 finding 更有價值。

### 執行者主動揭露、非本輪缺陷

- `doctor.py` 目前對五種不合格 marker 全回 `recorded`，§3.1.4／§3.1.5 在本 repo **尚未生效**。刻意標記，登記於 `docs/CONSUMER_CONFORMANCE.md`；consumer 修正歸 [#17](https://github.com/ruan6047/ai-workflow/issues/17)，語意比對的結構化承載設計歸 [#16](https://github.com/ruan6047/ai-workflow/issues/16)。請查核「標記是否誠實完整」，而非要求本卡修 consumer。
- 壞 marker 若在**任何** clearance 寫下前就被編輯成合格內容，停機會靜默解除且不留紀錄。執行者自查發現並已明文寫入契約。

### 環境紅線與獨立性

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。執行者為 Claude Opus 5@Claude Code；本 repo 規則屬 🔴紅線，查核**必須換模型家族或由需求方 sign-off**。

若你無法執行 `wfcli`，請依 `templates/handoff-contract.md` §3.1.2 在本 Issue 留一則 `wf-review-receipt:v1` 收據（`card_id`、完整 `source_sha`、查核報告原文 UTF-8 `report_sha256`），由 PM 對帳後轉錄。

**輸出**：依 `templates/review-prompt.md` §5 的結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5239185032 · 2026-08-10T10:53:19Z

<!-- wf-review-receipt:v1
card_id: WF-REVIEW-EVENT-MARKER-CONTRACT1
source_sha: 07358d772146b63133fd16c2fe0d1d222dcd6677
report_sha256: f65a23f420913a328576d08f3f56373ddb08a6d068924529a3c2f38fda8dff95
-->

core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "git rev-parse HEAD && git diff --name-only origin/main"
    observed: "07358d772146b63133fd16c2fe0d1d222dcd6677；僅 docs/CONSUMER_CONFORMANCE.md、templates/handoff-contract.md、templates/review-escalation.md。"
  - command: "cd cli && uv run pytest -q"
    observed: "185 passed in 1.50s"
  - command: "git status --porcelain cli/"
    observed: "空。"
  - command: "docs/CONSUMER_CONFORMANCE.md §1.2 probe"
    observed: "五種不合格 marker 與對照組皆為 recorded；與已登記 fail-open 落差一致。"
  - command: "rg clearance_authority/requester_decision_url templates"
    observed: "僅命中 review-escalation.md 的已撤回設計歷史記錄，無規範性殘留。"
findings: []

## Comment 5239210106 · 2026-08-10T10:56:05Z

<!-- wf-review-receipt:v1
card_id: WF-REVIEW-EVENT-MARKER-CONTRACT1
source_sha: 07358d772146b63133fd16c2fe0d1d222dcd6677
report_sha256: 3aaf4c23441ca722368337dbe9d0718ed3c2b5262eb68ee98c45536fe5517b21
-->

core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-review-event-marker-contract1 && git rev-parse HEAD"
    observed: "07358d772146b63133fd16c2fe0d1d222dcd6677"
  - command: "git diff --name-only origin/main"
    observed: "僅 docs/CONSUMER_CONFORMANCE.md、templates/handoff-contract.md、templates/review-escalation.md。"
  - command: "cd cli && uv run pytest -q"
    observed: "185 passed in 1.50s"
  - command: "git status --porcelain cli/"
    observed: "空。"
  - command: "docs/CONSUMER_CONFORMANCE.md §1.2 probe"
    observed: "五種不合格 marker 與對照組皆為 recorded；與已登記的 fail-open 落差一致。"
findings: []
reviewer_position: "反對把已通過的 R5 clearance 契約退回最保守版本。它保留 fail-closed 的核心性質，將 forged-rejected 降為純記錄並以 reissue-required 回到待查核，已移除重放自動解鎖面。現階段複雜度仍與可編輯 GitHub 留言、append-only 重播及不誤放行的需求相稱；#16 應承接結構化裁決承載與 consumer 實作，不宜重開同層設計。"

## Comment 5239231631 · 2026-08-10T10:58:28Z

<!-- wf-review-event:v1 card_id=WF-REVIEW-EVENT-MARKER-CONTRACT1 source_sha=07358d772146b63133fd16c2fe0d1d222dcd6677 attempt_id=WF-REVIEW-EVENT-MARKER-CONTRACT1-e0-07358d772146b63133fd16c2fe0d1d222dcd6677 -->
## 查核裁決：APPROVE

- 卡：`WF-REVIEW-EVENT-MARKER-CONTRACT1`　attempt_id：`WF-REVIEW-EVENT-MARKER-CONTRACT1-e0-07358d772146b63133fd16c2fe0d1d222dcd6677`
- 查核者：獨立校讀（GitHub author ruan6047 轉貼；模型／工具為自述）　escalation_epoch：0
- source_sha：`07358d772146b63133fd16c2fe0d1d222dcd6677`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-10T18:58:27+08:00

### self_run（查核者實跑）

- `cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-review-event-marker-contract1 && git rev-parse HEAD`
  - 07358d772146b63133fd16c2fe0d1d222dcd6677
- `git diff --name-only origin/main`
  - 僅 docs/CONSUMER_CONFORMANCE.md、templates/handoff-contract.md、templates/review-escalation.md。
- `cd cli && uv run pytest -q`
  - 185 passed in 1.50s
- `git status --porcelain cli/`
  - 空。
- `docs/CONSUMER_CONFORMANCE.md §1.2 probe`
  - 五種不合格 marker 與對照組皆為 recorded；與已登記的 fail-open 落差一致。

### findings（0，其中 blocking 0）

- （無）

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5239287453 · 2026-08-10T11:04:36Z

本卡已 APPROVE（R5，零 finding）並 merge 至 main `dbfdb9c85fa92fff81efcc6b01a2a275f6378091`。worktree 與本地／遠端分支均已移除，無殘留。

後續由 [#17](https://github.com/ruan6047/ai-workflow/issues/17)（doctor 落實 fail-closed，基線已指向本 merge SHA）與 [#16](https://github.com/ruan6047/ai-workflow/issues/16)（結構化裁決承載與狀態機）承接；契約明示尚未生效的落差登記於 `docs/CONSUMER_CONFORMANCE.md`。
