# ai-workflow 藍圖

> 需求方 2026-08-12 裁定的目標排序與卡片分級。**本檔是「為什麼做這張卡」的唯一來源**；
> 卡片本身寫「怎麼做」。開新卡前先在此找到它服務哪個目標——找不到就不該開。

## 0. 目標排序

需求方 2026-08-12 逐字裁定：

> 應該是**可稽核的內容**跟**防止低級事故**為主，其他是有最好但非必要。

| 序 | 目標 | 判準 |
|---:|---|---|
| 1 | **防止低級事故** | 有機械執行者會擋下它。沒有執行者的偵測器**不算**達成 |
| 2 | **可稽核的內容** | 事後能從留痕重建「做了什麼、依據是什麼」。**不含身分**，見 §1 |
| 3 | 其他治理精緻化 | 有最好，非必要。降級為 Backlog，有餘力再做 |

### 開卡前的檢查

1. 它服務哪一個目標？講不出來就不開。
2. 目標 1 的卡：**執行者是誰？** 答案若是「靠人記得」，它其實是目標 3。
3. 目標 3 的卡：**現在有人因它受害嗎？** 沒有就進 Backlog，不排程。

## 1. 已裁定的結構性限制：身分不可稽核

**本 repo 的人類、PM、每個執行者、每個查核者共用同一個 GitHub 帳號 `ruan6047`。**

推論（2026-08-12 裁定）：

- **所有以 GitHub 身分為據的授權檢查，永久是 `structurally-vacuous`。** 這不是缺陷待修，是結構事實。
- 正確處置是**把空虛性導出到事件流**，讓它機器可讀——**不是**寫一個看起來有檢查、實際恆真的條文。
  既有前例：`templates/review-escalation.md` §5 第 7 款的 `authorization_binding`。
- **不再逐卡重新發明。** 任何卡遇到「想驗證身分」時，引用本節即可。

### 為什麼不解決它

給每個 agent 獨立 GitHub 帳號／token 是為了治理去改基礎設施，成本遠高於它擋下的事故。
**需求方裁定不做。**

### 受影響且據此收斂的卡

`WF-22-CLI4`（#9）、`WF-AMEND-AUTHZ-BINDING1`（#62）、`WF-ESCALATION-RESOLUTION-GAP1`（#39）的授權款。

## 2. 唯一的執行面：CI

**2026-08-12 之前本 repo 完全沒有 CI**（`.github/` 不存在）。canonical 多處寫「守衛必紅」，
而那些守衛不存在——例如 `AI_WORKFLOW.md:221` 的 commit trailer 守衛，實測零命中。

**後果當日實現**：連續合併三張卡、每次只跑 `git merge-tree` 確認文字無衝突並在分支自己的基線上跑測試，
從未在合併後的結果上跑過；`WF-CLEANUP-GUARD1` 的基線早於能力旗標改必填的那次合併，
於是它自己的工作樹 388 passed 為真、併進 main 卻 14 個 error。

**裁定**：

- **`DEV-AIWF-MINIMAL-CI1`（#48）是唯一會真的擋人的東西**，優先度最高。
- 其餘全是**偵測器**（`doctor`、對帳器、枚舉器）。偵測器讓缺失可被列舉，**不阻止任何人 push**。
- **偵測器的卡不得宣稱「已預防」**——`WF-WORKTREE-REPO-OWNERSHIP1`（#57）的 R1-01 正是因此被判 blocking。
- 需要牙齒的偵測器，**排在 #48 之後**。

## 3. 現行排程

### 必要（依序）

| 序 | 卡 | 服務目標 | 為什麼是前提 |
|---:|---|---|---|
| 1 | `WF-RESOURCE-BLOCK-ANCHOR1`（#43） | 1 | 資源宣告哨兵可被 decoy 劫持則互斥檢查失效 |
| 2 | `WF-RESOURCE-WRITESET1`（#24） | 1 | 多 agent 併行的安全前提；沒閉合則併行本身不安全 |
| 3 | `DEV-AIWF-MINIMAL-CI1`（#48） | 1 | 唯一執行面，其後所有偵測器靠它才有牙齒 |
| 4 | `DEV-COMMIT-TRAILER-GUARD1`（#63） | 2 | 內容可稽核的直接載體；亦統一分岔的根因家族名 |
| 5 | `WF-WORKTREE-REPO-OWNERSHIP1`（#57） | 1 | 兩個真實漂移已在磁碟上，`doctor` 看不見 |

### 降級為 Backlog（有餘力再做）

`WF-EVENT-MARKER-V2-SCOPE1`（#35）、`WF-CARD-FIELD-CORRECTION1`（#37）、
`WF-DISPATCH-PRECHECK1`（#38）、`WF-ESCALATION-RESOLUTION-GAP1`（#39）、
`WF-EVENT-IDEMPOTENCY1-ADAPT-STALE1`（#41）、`WF-CONTROL-PLANE-TYPE-REGISTRY1`（#42）、
`WF-RECONCILE-CLEANUP-GUARD1`（#45）、`WF-24-EVIDENCE-STRENGTH1`（#11）、
`WF-ORCHESTRATION-RECONCILE1`（#16）、`WF-MARKER-SCOPE-CLEARANCE1`（#30）、
`OPS-MIG1-CLAIMS-BACKFILL1`（#31）、`WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1`（#52）、
`WF-CLI-RESUME1`（#54）、`WF-CLI-MERGE1`（#55）、`WF-CLI-EPOCH-ANCHOR1`（#56）、
`WF-EVENT-TYPE-REGISTRY-RECONCILE1`（#58）、`DEV-CLI-VERB-WIRING1`（#60）、
`WF-AMEND-AUTHZ-BINDING1`（#62）

**降級不是關閉。** 它們載有真實 finding 的紀錄，關掉會讓那些發現消失；降級可逆，關閉不可逆。

**#42／#58 特別說明**：它們解決「兩份事件型別語彙互不知情」，而該分歧**今天 0 寫入端 0 讀取端、
不可能造成錯誤裁決**（#58 執行者自己的論證）。這是「有最好」的典型。

## 4. 驗收政策（2026-08-12 裁定）

> 已做完的項目如果大項目沒問題先驗收，後續細節轉成卡片之後進行。

**大項目通過即可驗收**，不因細節 finding 而整張退回。細節轉為 Backlog 卡。

### 判準

| 情況 | 處置 |
|---|---|
| `core_pain_resolved: no` | **退回**。核心痛點未消不適用本政策 |
| `core_pain_resolved: yes` ＋ blocking 全屬細節 | **驗收**，細節開 Backlog 卡 |
| blocking 指向**會造成低級事故**的缺陷 | **退回**，不論核心痛點判定 |
| blocking 指向身分不可稽核 | 引用 §1，**不構成退回理由** |

**「細節」的判準不是嚴重度標籤，是後果**：它會不會讓某人合併壞碼、改錯檔、或讓留痕重建不出來。
會 → 不是細節。

### 這條政策改變了什麼

先前每一個 blocking 都讓卡再走一輪，於是查核越認真、輪次越多、卡越開越多。
2026-08-12 當日開 20 張、結 4 張——**發散**。本政策是收斂機制。

## 5. 本檔的維護

- 開卡時在此確認它服務哪個目標；找不到就不開。
- 降級或升級卡片時更新 §3。
- **需求方裁定的目標排序（§0）只有需求方能改。**
