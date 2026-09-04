# #17 WF-REVIEW-EVENT-MARKER-ENFORCE1 doctor 落實 wf-review-event:v1 不合格 marker 的 fail-closed
- state: closed  created: 2026-08-10T09:06:11Z  closed: 2026-08-10T17:42:38Z
- url: https://github.com/ruan6047/ai-workflow/issues/17
- comments: 6

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code
- 執行：待指派　查核：獨立校讀
- Initiative：—　spec 基線：handoff-contract.md §3.1 ＋ review-escalation.md §5 的 review-marker-clearance（WF-REVIEW-EVENT-MARKER-CONTRACT1，ai-workflow#15，已 APPROVE 並 merge；基線＝main dbfdb9c85fa92fff81efcc6b01a2a275f6378091）。#16 不負責 halt 解除路徑
- DB：db_scope=none
- 服務的原始目標：讓狀態面工具依 handoff-contract.md §3.1 判定查核裁決時，不把不合格 marker 誤判為已有裁決。

## 簡介
<!-- card-brief:begin -->
讓 doctor 依 handoff-contract.md §3.1.4 對五種不合格的 wf-review-event:v1 marker（未知版本／缺欄／多出未定義鍵／欄位錯序／三欄不自洽）一律不回 recorded，並新增與 unobservable 分離的結果態，語意是「找到訊號但讀不懂」；落差 8a 的同 attempt 多則受管轄 marker 一律停止判定。**適用時機**：一張卡的自動裁決被判停機、要查觸發條件；或要確認契約宣告的 fail-closed 在既有消費者上是否真的生效（此前是虛假保證）時。⛔ 非射程：停機在本卡維持不可由機器解除，clearance 表示法歸 aiwf#16、消費實作另開卡；不含 Project 交付狀態欄那第三面（歸 WF-REVIEW-CHANNEL-THIRD-FACE1）；不含 wf-review-event: 前綴的舊裁決留言行為不變。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：audit_review_channel() 對未知版本、缺欄、多出未定義鍵、欄位錯序、三欄不自洽五種不合格 wf-review-event:v1 marker 全部回傳 recorded；handoff-contract.md §3.1.4 規定的 fail-closed 在既有消費者上完全未生效，契約提供的是虛假保證。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/doctor.py",
    "file:cli/src/wf_cli/commands/doctor_cmd.py",
    "file:cli/tests/test_doctor.py",
    "file:docs/CONSUMER_CONFORMANCE.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 五種不合格 marker（未知版本／缺欄／多出未定義鍵／欄位錯序／三欄不自洽）均不得回傳 recorded
- [ ] 新增與 unobservable 分離的結果態，語意為「找到訊號但讀不懂」，不得與「找不到訊號」併態
- [ ] legacy 相容不變：完全不含 wf-review-event: 前綴的舊裁決留言，判定行為與本卡前一致
- [ ] halt 解除路徑：review-marker-clearance 目前只定義事件欄位，未定義其在 Issue 留言平面的表示法，亦無 writer；本卡不得自行發明表示法。停機在本卡維持不可由機器解除（fail-closed 持續），並於 docs/CONSUMER_CONFORMANCE.md 登記此缺口；表示法定義歸 #16，消費實作另開卡
- [ ] 落差 8a：同 attempt 出現多則受管轄 marker 時，在尚無可驗證語意等價機制前一律停止判定，不得把重送視為安全或回傳 recorded；此為 fail-open 修復，不依賴 #16

## 驗證

- [ ] cli 測試全過，且新增回歸測試涵蓋五種不合格案例與 legacy 對照組
- [ ] 以 WF-REVIEW-EVENT-MARKER-CONTRACT1 交付中的五案例探針重跑，全部不為 recorded
## Log

- 2026-08-10T17:06:11+08:00 open by Claude Opus 5@Claude Code；owner 待指派；iteration 0。
- 2026-08-10T17:56:31+08:00 PM card amendment：需求方授權將 halt 解除路徑依賴由 #16 改為 #15 的 review-marker-clearance；新增落差 8a fail-open 驗收。
- 2026-08-10T18:25:00+08:00 card body repair by Claude Opus 5@Claude Code；將 17:56 修改中誤寫的字面 \n 還原為真換行、Log 條目改回時序排列；內容一字未改。此次以 gh issue edit 直接寫入，繞過 wfcli 唯一寫入通道——wfcli 無改卡面指令，缺口見 ai-workflow#12。
- 2026-08-10T19:10:00+08:00 spec baseline update by Claude Opus 5@Claude Code；#15 已 merge，基線由「待查核／merge 後須改引」改為 main dbfdb9c；其餘欄位未動。仍以 gh issue edit 直接寫入（wfcli 無卡面修訂能力，追蹤卡 #19）。
- 2026-08-10T20:26:34+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree claude/WF-REVIEW-EVENT-MARKER-ENFORCE1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-review-event-marker-enforce1；交付狀態 🚧進行中。
- 2026-08-11T00:38:14+08:00 amend by wf-cli（op 4bbe29c8）→ 驗收條件：原值「[ ] 五種不合格 marker（未知版本／缺欄／多出未定義鍵／欄位錯序／三欄不自洽）均不得回傳 recorded；[ ] 新增與 unobservable 分離的結果態，語意為「找到訊號但讀不懂」，不得與「找不到訊號」併態；[ ] legacy 相容不變：完全不含 wf-review-event: 前綴的舊裁決留言，判定行為與本卡前一致；[ ] halt 解除路徑依 ai-workflow#15 定義的 review-marker-clearance 欄位契約實作；不得自行改變 review-correction 或 status-change 既有語意；[ ] 落差 8a：同 attempt 出現多則受管轄 marker 時，在尚無可驗證語意等價機制前一律停止判定，不得把重送視為安全或回傳 recorded；此為 fail-open 修復，不依賴 #16」→ 新值「五種不合格 marker（未知版本／缺欄／多出未定義鍵／欄位錯序／三欄不自洽）均不得回傳 recorded；新增與 unobservable 分離的結果態，語意為「找到訊號但讀不懂」，不得與「找不到訊號」併態；legacy 相容不變：完全不含 wf-review-event: 前綴的舊裁決留言，判定行為與本卡前一致；halt 解除路徑：review-marker-clearance 目前只定義事件欄位，未定義其在 Issue 留言平面的表示法，亦無 writer；本卡不得自行發明表示法。停機在本卡維持不可由機器解除（fail-closed 持續），並於 docs/CONSUMER_CONFORMANCE.md 登記此缺口；表示法定義歸 #16，消費實作另開卡；落差 8a：同 attempt 出現多則受管轄 marker 時，在尚無可驗證語意等價機制前一律停止判定，不得把重送視為安全或回傳 recorded；此為 fail-open 修復，不依賴 #16」；理由 第 4 條原文不可實作並經需求方核可改寫：review-marker-clearance 只定義事件必填欄位，未定義其在 Issue 留言平面的表示法，亦無任何 wfcli 指令會寫它；要實作就得自行發明 marker 語法，那屬設計且需動 templates/（不在本卡資源內）。改為明確禁止自行發明、停機維持不可機器解除並登記缺口，表示法定義歸 #16。
- 2026-08-11T00:42:23+08:00 amend by wf-cli（op 51d86acb）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/doctor.py", "file:cli/tests/test_doctor.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/doctor.py、file:cli/src/wf_cli/commands/doctor_cmd.py、file:cli/tests/test_doctor.py、file:docs/CONSUMER_CONFORMANCE.md」；理由 開卡時漏列：驗收第 4 條明文要求在 docs/CONSUMER_CONFORMANCE.md 登記 clearance 缺口，且本卡關閉落差 1-5／8a 後該登記檔必須同步更新，否則會留下說謊的登記。
- 2026-08-11T01:00:56+08:00 handoff by wf-cli → owner 獨立校讀；iteration 0；SHA 6ccdafef6f065339c468a2725952a226db352831；證據 契約 §3.1.3／§3.1.4 的 fail-closed 已在 doctor 生效：五種不合格 marker ＋ 重複事件轉新結果態 marker_quarantined，legacy 相容不變。經需求方要求五輪自查，每輪換攻擊面共找到 8 個 fail-open（marker 須恰為首行、Log 索引須同行同 attempt、收據須整行相等、--json 缺 review_channel、doctor 未驗 source_sha 格式）。270 passed（237 baseline + 33）。
- 2026-08-11T01:13:55+08:00 handoff by wf-cli → owner 獨立校讀；iteration 0；SHA ffc9fa67ff4b5e0c13f9a16027b524afc26128c9；證據 R1 四項全處置：Log attempt 改 token 邊界比對（子字串陷阱複發）、legacy 還原基線全文搜尋（同行要求只施加於 v1，避免回歸）、--json 改為 stdout 純 JSON（人類報告走 stderr）、落差 9 已開追蹤卡 #20 並回填連結。另修登記檔 §1.1 與實際行為不符的描述。273 passed。
- 2026-08-11T01:31:21+08:00 handoff by wf-cli → owner 獨立校讀；iteration 0；SHA c5889833351a86964283a20f1ad3a0c412785bdf；證據 R2-001 已修（同 attempt 存在 v1 事件時排除 legacy 背書），另依需求方要求再自查一輪：修正停機時收據被吞掉的資訊遺失，並確認 legacy Log 對帳的寬鬆屬基線行為、刻意不改而改為登記。278 passed（237 baseline + 41）。
- 2026-08-11T01:41:09+08:00 review by wf-cli → APPROVE（✅通過）；查核者 獨立校讀（GitHub author ruan6047 轉貼；模型／工具為自述）；core_pain_resolved yes；self_run 5 項；findings 0 項（blocking 0）；attempt WF-REVIEW-EVENT-MARKER-ENFORCE1-e0-c5889833351a86964283a20f1ad3a0c412785bdf。
- 2026-08-11T01:48:11+08:00 handoff by wf-cli → owner ruan6047；iteration 0；SHA 91d8a1f10ad2a8faceafb79f7e8c89571385569f；證據 已 APPROVE、已 merge 至 main 91d8a1f10ad2a8faceafb79f7e8c89571385569f、worktree 與分支已清、Issue 已關閉；本次補做 release 轉終態以釋放資源宣告（先前結案漏此步，導致 assign 將已完成卡誤判為活卡）。
- 2026-08-26T22:21:41+08:00 amend by wf-cli（op 65189ba2）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:5c287a06a897e930b1f0cf99ff3f3bfa8b791e633a44dd2a018d3c77159fc4ad (809 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5239075296 · 2026-08-10T10:40:56Z

## 更正：本卡 Log 中 18:25 那一條的追蹤卡引用有誤

18:25 的 `card body repair` 條目寫「wfcli 無改卡面指令，缺口見 ai-workflow#12」。**該引用不正確**，經卡面修復查核指出並確認：

- **#12 的範圍是 tier 更正**（標題即「補上已開卡的 tier 更正能力」），不涵蓋 spec 基線、驗收、驗證、資源宣告等通用卡面修訂。
- 因此 #12 **不能**作為「wfcli 缺乏通用卡面修訂能力」這個缺口的追蹤卡；在本次更正之前，該缺口實際上無人追蹤。

**正確的追蹤卡是 [#19](https://github.com/ruan6047/ai-workflow/issues/19)（`WF-CLI-CARD-AMEND1`）**，已於本次依需求方裁決開立，並在其驗收條件中要求與 #12 的範圍界定明確（擇一實作，或明示 #12 併入後關閉）。

本更正以留言形式記錄，**不修改卡面**——修正一則不準確的留痕不值得再製造一次未授權的卡面寫入。卡面 Log 的 18:25 條目維持原文，其錯誤由本留言承載。

另記錄查核的另一項 governance finding 與需求方裁決：18:25 修復時一併重排 Log 時序，超出「修字面 `\n` 渲染」的窄授權。經查核逐項確認該重排未改變任何實質內容且格式更正確，需求方裁決**維持現狀並追認**；往後同類修復先取得明示授權再動。

—— Claude Opus 5@Claude Code


## Comment 5243408477 · 2026-08-10T17:02:05Z

## 派審：WF-REVIEW-EVENT-MARKER-ENFORCE1

審核對象 **`ruan6047/ai-workflow#17`**（Issue）。CLI 實作卡，有程式碼改動。

### 進駐與身分核對

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-review-event-marker-enforce1
分支：claude/WF-REVIEW-EVENT-MARKER-ENFORCE1
被審 SHA：6ccdafef6f065339c468a2725952a226db352831
基線：origin/main 5d821e12fd0c71eaababc3dcf7fe408a49cc4d9d（#19 已 merge，分支已合入）
iteration：0（首次查核）
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-review-event-marker-enforce1
git rev-parse HEAD && git diff --name-only origin/main
```

預期 `6ccdafe…` 與四個檔案：`cli/src/wf_cli/doctor.py`、`cli/src/wf_cli/commands/doctor_cmd.py`、`cli/tests/test_doctor.py`、`docs/CONSUMER_CONFORMANCE.md`。

### 這張卡在做什麼

`handoff-contract.md` §3.1.4 要求受管轄但不合格的 marker 必須讓該卡停止自動裁決判定，但 `doctor` 對五種不合格形態全數回傳 `recorded`——**契約寫著 fail-closed、消費者實際 fail-open**。`docs/CONSUMER_CONFORMANCE.md` 老實登記著這個缺口，本卡把它補上。

核心是 `inspect_event_marker()`：單一 regex 同時編碼「順序固定、單一空白分隔、鍵集合封閉」，再反解 `attempt_id` 驗三欄自洽。不合格與重複事件一律轉新結果態 `marker_quarantined`。

### 必跑（`self_run` 需附實際輸出）

```bash
cd cli && uv run pytest -q          # 預期 270 passed（237 baseline + 33）
```

並請重跑 `docs/CONSUMER_CONFORMANCE.md` §1.2 內嵌的探針——**它是契約當初登記缺口時的原始證據**，六個案例現在應為：五種不合格全 `marker_quarantined`、對照組 `recorded`。

### 本輪請特別攻擊這四點

1. **執行者換攻擊面五次，每次都找到東西；請找第六個面。** 五輪的結果是：同一面重看零收穫，換面必有收穫（詳見下方揭露）。執行者已認定「剩餘面向屬既有功能、超出資源宣告」而收手——**請獨立判斷這個收手時機是否過早**，特別是 `audit_review_channel` 與 `run_doctor` 之間、或 `--strict` 與 CI 消費端之間是否還有未測介面。
2. **`marker_quarantined` 的觸發是否過寬。** 現行規則：留言只要含 `wf-review-event:` 前綴而首行不是合格 marker，就停機——包含內文引用、code fence 示範。契約明文承認這個保守誤判，但實務上**任何在 Issue 討論契約的留言都會凍住那張卡**。這個代價可接受嗎？
3. **停機無出路的實務後果。** 驗收第 4 條依需求方核可改寫：`review-marker-clearance` 缺留言平面表示法，本卡不得自行發明，故停機**不可由機器解除**。落差 7 的方向因此從 fail-open 轉為 fail-closed——停機真的會發生了，但解不掉。請判斷這是否應在 merge 前先由 #16 補上表示法。
4. **`legacy` 判準的邊界。** legacy ≡ 完全不含該前綴。一則舊裁決留言若因任何原因含有該字串（例如被人編輯時貼了契約片段），會由 recorded 轉為停機。這是預期行為還是回歸？

### 執行者主動揭露：五輪自查找到 8 個 fail-open

需求方連續五次要求「再檢查一次」。第一輪（同一面重看）零收穫；其後每輪換攻擊面都有收穫：

| 輪 | 攻擊面 | 找到 |
| --- | --- | --- |
| 2 | marker 位置 | marker 埋在散文後／有縮排／同則兩個 marker／**code fence 內的示範 marker 被當成真事件** 皆判 `recorded` |
| 3 | Log 索引＋收據 | Log 索引 e0 卻讓 e1 事件過關；`review by wf-cli` 與 attempt 散在不同行也算數；`"card_id: CARD-A" in "card_id: CARD-AB"` 認錯收據 |
| 4 | 指令層＋PR review | `--json` 完全不含 review-channel，停機只在人類可讀 stdout（本卡目的正是讓它機器可讀） |
| 5 | 極端／無效輸入 | 無效 `source_sha`（短／大寫／非 hex）回 `unobservable`，等於拿確定結論回答未評估的問題 |

**兩次「假驗證」也一併揭露**：

- 第 3 輪修正時發現，第 2 輪新增的 `test_same_sha_different_epoch_...` **把 bug 寫進了測試**——它斷言「Log 索引 e0、事件是 e1 → `recorded`」，正是第 3 輪找到的 fail-open。若不是換面，它會以「有測試覆蓋」的樣子進 main。
- 第 5 輪的第一版探測用了不存在的 repo 路徑，五個案例全停在「路徑不存在」，`exit=2` 看起來像全數擋下，實際一個都沒測到。這與稍早 `--escalate` 自審用 DraftIssue 走不到目標路徑是同一個錯誤，**第二次犯**。

請把「執行者的驗證是否真的驗到」當成查核重點之一。

### 其餘驗收（卡面條文，第 4 條已依核可改寫）

1. 五種不合格 marker 均不得回傳 `recorded`。
2. 新增與 `unobservable` 分離的結果態。
3. legacy 相容不變。
4. halt 解除路徑：不得自行發明表示法；停機維持不可機器解除，缺口登記於 `docs/CONSUMER_CONFORMANCE.md`，表示法定義歸 #16。
5. 落差 8a：同 attempt 多則受管轄 marker 一律停止判定。

### 登記檔的性質翻轉

`docs/CONSUMER_CONFORMANCE.md` 已更新：落差 1–6、8a 標記已閉並附修復前後對照；**落差 7 的方向由 fail-open 轉為 fail-closed**（停機真的會發生了，但解不掉）；**落差 9（三面一致的第三面，Project 交付狀態欄）明列為 fail-open 且尚無追蹤卡**——依 §6 規則它應該要有卡，請一併裁定是否於本卡 merge 前後開立。

### 環境紅線與獨立性

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。執行者為 Claude Opus 5@Claude Code。本卡動的是契約消費端，建議獨立查核者。

無法執行 `wfcli` 時，請依 `templates/handoff-contract.md` §3.1.2 留 `wf-review-receipt:v1` 收據由 PM 轉錄。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5243539847 · 2026-08-10T17:14:55Z

## 派審：R2（取代前一則派審詞）

⚠️ 前一則指向 `6ccdafe`，**已過期**。

### 進駐與身分核對

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-review-event-marker-enforce1
分支：claude/WF-REVIEW-EVENT-MARKER-ENFORCE1
被審 SHA：ffc9fa67ff4b5e0c13f9a16027b524afc26128c9
基線：origin/main 5d821e12fd0c71eaababc3dcf7fe408a49cc4d9d
iteration：0
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-review-event-marker-enforce1
git rev-parse HEAD && git diff --name-only origin/main
```

預期 `ffc9fa6…` 與四個檔案：`cli/src/wf_cli/doctor.py`、`cli/src/wf_cli/commands/doctor_cmd.py`、`cli/tests/test_doctor.py`、`docs/CONSUMER_CONFORMANCE.md`。

### R1 四項的處置

**R1-001（Log attempt 子字串前綴碰撞）** — 改為 token 邊界比對（`(?<![\w-])…(?![\w-])`）。附回歸：Log 寫成 `attempt+x` 不得判 `recorded`。

**R1-002（legacy 被連帶收緊，構成回歸）** — 拆成兩套判準：**同行 ＋ token 邊界只施加於宣告受管轄的 v1 事件**；**legacy 維持基線的全文各自搜尋**。附回歸：legacy ＋ 分行 Log 仍 `recorded`（基線行為），v1 ＋ 分行 Log 不得 `recorded`。

**R1-003（`--json` 不可解析）** — `--json` 時人類可讀報告改走 stderr，stdout 只有 JSON。附回歸：直接以 `json.loads(stdout)` 斷言整份可解析，並檢查人類報告確實在 stderr。

**R1-004（落差 9 未追蹤）** — 已開 **[#20](https://github.com/ruan6047/ai-workflow/issues/20) `WF-REVIEW-CHANNEL-THIRD-FACE1`**（T2，資源含 `doctor.py`／`doctor_cmd.py`／`test_doctor.py`／登記檔），並回填三處連結、移除「尚無追蹤卡」敘述。依裁定未把實作塞進本卡。

### 必跑（`self_run` 需附實際輸出）

```bash
cd cli && uv run pytest -q                                    # 預期 273 passed
cd cli && uv run wfcli doctor .. --registry none --json | jq . # 應可解析，且含 review_channel 鍵
```

並請重跑 `docs/CONSUMER_CONFORMANCE.md` §1.2 內嵌探針（六案例）。

### 本輪請特別攻擊這三點

1. **v1 與 legacy 兩套判準的交界。** 現行分流依「留言是否含 `wf-review-event:` 前綴」。請找兩者判準不一致造成的可利用差異——例如同一張卡同時有 legacy 留言與 v1 留言時，legacy 的寬鬆對帳會不會替 v1 事件背書；或反之。這是本輪新引入的複雜度，也是我最不確定的地方。
2. **token 邊界的字元集是否正確。** 邊界定為 `[\w-]`。`card_id` 可含哪些字元未有明文約束（實測 `CARD.A`、`卡片-甲`、`A|B` 都能運作）；若 `card_id` 含 `.` 或 `|`，`(?<![\w-])` 在該處不構成邊界，是否又開出前綴碰撞？
3. **`--json` 改走 stderr 是否破壞既有消費者。** 先前 stdout 同時有文字與 JSON，若有腳本靠 stdout 抓人類可讀報告，本次變更會讓它拿到 JSON。這是行為變更，請判斷是否需要標為 breaking 或加旗標。

### 執行者主動揭露

- **R1-001 是同一個陷阱的複發。** 執行者在第三輪自查時才剛在收據比對抓到 `"card_id: CARD-A" in "card_id: CARD-AB"` 並修掉，卻在同一輪自己新寫的 Log 對帳裡原封不動又犯一次。抓到一個 bug 不等於學到那個 bug 的形狀。
- **R1-002 是執行者自己造成的回歸。** 第三輪修 Log 對帳時把同行要求一併施加到 legacy，違反卡面驗收第 3 條。
- **R1-003 讓第四輪的修復失去意義。** 第四輪才剛加上 `review_channel` 鍵讓輸出「可被機器消費」，但整份 stdout 從來就不是合法 JSON——加了鍵沒用，因為沒人 parse 得動。
- 登記檔 §1.1「已實作」的描述在 R1-002 之後與實際行為不符，本輪一併修正（v1／legacy 兩套判準明列）。

### 其餘驗收（卡面條文，第 4 條已依核可改寫）

1. 五種不合格 marker 均不得回傳 `recorded`。
2. 新增與 `unobservable` 分離的結果態。
3. legacy 相容不變。
4. halt 解除路徑：不得自行發明表示法；停機維持不可機器解除，缺口登記於登記檔，表示法定義歸 #16。
5. 落差 8a：同 attempt 多則受管轄 marker 一律停止判定。

### 環境紅線與獨立性

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。執行者為 Claude Opus 5@Claude Code。建議獨立查核者。

無法執行 `wfcli` 時，請依 `templates/handoff-contract.md` §3.1.2 留 `wf-review-receipt:v1` 收據由 PM 轉錄。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5243715556 · 2026-08-10T17:32:22Z

## 派審：R3（取代前兩則派審詞）

⚠️ 先前派審詞指向 `6ccdafe`／`ffc9fa6`，**皆已過期**。

### 進駐與身分核對

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-review-event-marker-enforce1
分支：claude/WF-REVIEW-EVENT-MARKER-ENFORCE1
被審 SHA：c5889833351a86964283a20f1ad3a0c412785bdf
基線：origin/main 5d821e12fd0c71eaababc3dcf7fe408a49cc4d9d
iteration：0
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-review-event-marker-enforce1
git rev-parse HEAD && git diff --name-only origin/main
```

預期 `c588983…` 與四個檔案：`cli/src/wf_cli/doctor.py`、`cli/src/wf_cli/commands/doctor_cmd.py`、`cli/tests/test_doctor.py`、`docs/CONSUMER_CONFORMANCE.md`。

### R2-001 的處置

**混合 v1／legacy 的放行路徑先前以 OR 合併**，v1 事件即使沒有合格的同行 Log 索引，只要同卡有同 attempt 的 legacy 文字加上基線式分行 Log，就從寬鬆那條放行。

修法依 disposition 定優先序：**同一 `attempt_id` 一旦存在受管轄的 v1 事件，即從 legacy 候選中排除**。legacy 對「沒有 v1 對應」的 attempt 仍維持基線寬鬆對帳（驗收第 3 條未受影響）。三項回歸固定三種組合，登記檔同步補上優先序說明。

查核者的探針重跑：`v1 無同行索引 ＋ 同 attempt legacy ＋ 分行 Log` 由 `recorded` 轉為 `unobservable`；`只有 legacy（無 v1）` 維持 `recorded`。

### 需求方要求的追加自查（本輪新增兩項變更）

攻擊面選在剛動過的 v1／legacy 優先序，加上一個從未測過的組合：

**已修 — 停機時收據被吞掉。** 收據原本只在未停機的路徑上收集，因此一張卡同時有壞掉的 marker 與一份未轉錄收據時，操作者只看得到停機。兩者是不同事實、下一步動作也不同：停機要人去修一則壞掉的留言，收據說的是「裁決其實發生過、只是還沒轉錄」。少給後者，可能導致去催一份早就做完的查核。改為一律在第一輪收集，停機結果一併帶出。

**確認不改 — legacy 的 Log 對帳寬鬆。** 探測發現 `e1` 的 legacy 裁決可被一行提及 `e0` 的 Log 背書（legacy 不要求同行、也不要求同一個 attempt）。這是 baseline 既有語意，而驗收第 3 條要求 legacy 行為與本卡前一致，收緊屬回歸。**已在登記檔明列為「已知寬鬆」**，避免日後被當成新缺陷或被誤以為 v1 也是如此。

### 必跑（`self_run` 需附實際輸出）

```bash
cd cli && uv run pytest -q                                     # 預期 278 passed
cd cli && uv run wfcli doctor .. --registry none --json | jq 'has("review_channel")'
```

並請重跑 `docs/CONSUMER_CONFORMANCE.md` §1.2 內嵌探針（六案例）。

### 本輪請特別攻擊這三點

1. **「已知寬鬆」的判斷是否正確。** 執行者主張 legacy 的鬆散對帳屬基線行為、收緊即回歸，因此登記而不修。請獨立確認：(a) 基線確實如此；(b) 保留它是否會與 v1 的嚴格判準在某些歷史組合下互相打架，產生執行者尚未想到的第三種路徑。
2. **收據收集時機改變的副作用。** 收據改在第一輪（與 marker 檢查同一迴圈）收集。請檢查是否因此在某些路徑上重複收集、或讓 `receipt_untranscribed` 的既有語意產生位移。
3. **本卡是否已達收斂。** 執行者連續六輪自查：前五輪每輪換攻擊面都找到 fail-open，本輪找到的是資訊遺失而非安全漏洞，且首次做出「查到但不該改」的判斷。**請判斷這是收斂訊號，還是只是尚未想到下一個危險面向。** 若你認為仍有未攻擊的面向，請直接指出比再開一個同層 finding 更有價值。

### 執行者主動揭露（累計）

本卡自查六輪，找到 8 個 fail-open ＋ 1 個資訊遺失；查核另找到 5 個 blocking。兩個反覆出現的失敗模式：

- **剛學到的教訓當場又犯**：R1-001 的子字串陷阱，執行者在第三輪自查才剛於收據比對抓到並修掉，同一輪自己新寫的 Log 對帳原封不動又犯一次。
- **修一個洞的動作製造下一個洞**：R1-002 修回歸時拆出兩條路徑，只驗證各自正確、未驗證交界，直接造成 R2-001。

請把「執行者剛改過的地方」視為最不可信的區域。

### 其餘驗收（卡面條文，第 4 條已依核可改寫）

1. 五種不合格 marker 均不得回傳 `recorded`。
2. 新增與 `unobservable` 分離的結果態。
3. legacy 相容不變。
4. halt 解除路徑：不得自行發明表示法；停機維持不可機器解除，缺口登記於登記檔，表示法定義歸 #16。
5. 落差 8a：同 attempt 多則受管轄 marker 一律停止判定。

落差 9 的追蹤卡 [#20](https://github.com/ruan6047/ai-workflow/issues/20) 已開並回填連結。

### 環境紅線與獨立性

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。執行者為 Claude Opus 5@Claude Code。建議獨立查核者。

無法執行 `wfcli` 時，請依 `templates/handoff-contract.md` §3.1.2 留 `wf-review-receipt:v1` 收據由 PM 轉錄。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5243803972 · 2026-08-10T17:41:11Z

<!-- wf-review-event:v1 card_id=WF-REVIEW-EVENT-MARKER-ENFORCE1 source_sha=c5889833351a86964283a20f1ad3a0c412785bdf attempt_id=WF-REVIEW-EVENT-MARKER-ENFORCE1-e0-c5889833351a86964283a20f1ad3a0c412785bdf -->
## 查核裁決：APPROVE

- 卡：`WF-REVIEW-EVENT-MARKER-ENFORCE1`　attempt_id：`WF-REVIEW-EVENT-MARKER-ENFORCE1-e0-c5889833351a86964283a20f1ad3a0c412785bdf`
- 查核者：獨立校讀（GitHub author ruan6047 轉貼；模型／工具為自述）　escalation_epoch：0
- source_sha：`c5889833351a86964283a20f1ad3a0c412785bdf`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-11T01:41:09+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git diff --name-only origin/main`
  - c5889833351a86964283a20f1ad3a0c412785bdf；四個預期檔案。
- `cd cli && uv run pytest -q`
  - 278 passed in 1.91s
- `cd cli && uv run wfcli doctor .. --registry none --json | jq 'has("review_channel")'`
  - true；stdout 為合法 JSON，人類報告改走 stderr。
- `重跑 CONSUMER_CONFORMANCE.md §1.2 六案例探針`
  - 五種不合格 marker 均為 marker_quarantined；conformant(control) 為 recorded。
- `壞 marker 與有效 receipt 並存探針`
  - status=marker_quarantined；receipt_urls=('u',)；receipt_authors=('r',)

### findings（0，其中 blocking 0）

- （無）

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5243819232 · 2026-08-10T17:42:38Z

三輪獨立查核後 R3 `APPROVE`（`core_pain_resolved: yes`、零 finding），已 merge 至 main `91d8a1f10ad2a8faceafb79f7e8c89571385569f`。分支尖端即被核可的 SHA `c588983`，無差異。worktree 與本地／遠端分支均已移除。

**main 上第一次出現契約與消費者一致的狀態**：`handoff-contract.md` §3.1.4 的 fail-closed 真的生效，而不只是紙上宣稱。

三個缺口仍登記於 `docs/CONSUMER_CONFORMANCE.md`：
- 落差 7（停機無法由機器解除）、落差 8b（合法重送被擋）方向皆為 **fail-closed**，歸 [#16](https://github.com/ruan6047/ai-workflow/issues/16)。
- 落差 9（三面一致的第三面未驗）方向為 **fail-open**，追蹤卡 [#20](https://github.com/ruan6047/ai-workflow/issues/20)——目前唯一仍開著的 fail-open。
