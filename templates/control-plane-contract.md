# Control-plane Contract — <專案名>

> 共同不變量見 canonical `AI_WORKFLOW.md` §4.1、§4.3、§4.4。本檔定義該專案如何把協作狀態與本機資源鎖分離；不得填入 token、secret 或使用者個資。

## 1. Adapter 邊界

| 範圍 | 實作 | 事實來源／用途 |
|---|---|---|
| Remote coordination（GitHub 預設） | <Issue／Project #<n>／Actions workflow> | 唯一 lifecycle writer：跨人 task、review、lease、CI 與協作事件 |
| **狀態寫入通道** | <祕書 CLI 指令；canonical §4.3 要求唯一通道> | 繞過它的狀態寫入（含看板 UI 手改欄位）即違規 |
| Local resource | <原子目錄鎖／OS lock／container runtime> | worktree、port、container、未提交變更的暫時互斥；只回報 telemetry，不改 card state |
| Event store | <Issue timeline ＋結構化 comment／受保護 Git history／外部 append-only store> | 事件歷史；採 Issue timeline 時必須有定期 snapshot export 作離線稽核副本 |
| Ledger projection | <產生方式與位置；cutover 後＝snapshot 產生，不手改> | 活卡 current-state 顯示；不得手改 |
| **封存的舊狀態面** | <舊 event log／Ledger 路徑與終筆 SHA；已 cutover 才填> | 唯讀，不得再追加或重建 |

## 2. Event schema 與狀態

```yaml
event_id: <UUID/monotonic ID>
card_id: <CARD_ID>
type: migration-baseline | claim | handoff | handoff-accepted | contract-baseline | baseline-change-request | preflight-failed | review | review-invalid | review-correction | review-marker-clearance | escalation-epoch-change | escalation-checkpoint | escalation-resolution | status-change | correction | merge | release
actor: <GitHub account / model@tool>
occurred_at: <ISO 8601>
state_version: <strictly increasing integer>
iteration: <integer>
source_sha: <required for review/handoff/merge/release>
evidence: <PR, CI, test or decision link>
```

review preflight／退回／升級另依 [`review-escalation.md`](review-escalation.md) 實作
`attempt_id`、`escalation_epoch`、結構化 findings 與 `counts_toward_escalation`；不得把所有
`REJECT` event 直接視為一次升級計數。專案可擴充 event type，但必須文件化狀態轉移，
不得將未識別 type 默默當成 review attempt。

local telemetry 另以同一 envelope 記錄 `resource-acquired | resource-released`，但必填 `lifecycle: false`、`claim_event_id`，且不得填 `state_version` 或改 card state。

列出允許的狀態轉移、Gate／preflight 退回、`⏸阻塞` 的 TTL、escalation checkpoint 與
`🚨已升級` 的決策 owner：

<專案實作>

### 2.1 定義出處登記表

上方列舉只登記**名稱**；每個 type 的必填欄位與狀態轉移由其**定義出處**承載，本檔不複述。
登記新 type 時一併登記其定義出處，無定義出處者不列入列舉——**這是約定，不是機械強制**：
本 repo 無 CI，且無任何程式讀取本列舉（`grep -rn "control-plane-contract" cli/ scripts/` 零命中），
故其執行者是本檔管轄者與該次變更的查核者。

| type | 定義出處 |
|---|---|
| `migration-baseline` | `MIGRATION.md` §1 第 3 點；該事件即該卡的 `state_version: 1` |
| `handoff`、`handoff-accepted` | [`handoff-contract.md`](handoff-contract.md) |
| `baseline-change-request` | [`baseline-cascade.md`](baseline-cascade.md)〈程序〉第 1 點「凍結」 |
| `review-invalid`、`review-correction`、`escalation-epoch-change`、`escalation-checkpoint`、`contract-baseline`、`preflight-failed`、`status-change` | [`review-escalation.md`](review-escalation.md) |
| `review-marker-clearance` | [`review-escalation.md`](review-escalation.md) §5「`review-marker-clearance` 解除 §1 的留痕解析停機，必填：」 |
| `release` | [`worktree-lifecycle.md`](worktree-lifecycle.md) |
| `escalation-resolution` | **provisional，見 §2.2** |
| `claim`、`review`、`correction`、`merge` | 無專屬定義檔；語意見本檔第 3–5 節與 canonical `AI_WORKFLOW.md` §4.1／§4.3，狀態轉移由採用專案在上方〈專案實作〉補齊 |

### 2.2 Provisional 登記

定義出處尚未併入本 repo `main` 的 type 以 **provisional** 登記，並釘住相依 SHA 使其可稽核。
provisional 期間 consumer 對該 type 的處置：視為**已登記但無本地定義**——依上方規則不得當成
review attempt，且不得依其欄位做任何裁決，只能記錄並 fail-closed。

| type | 相依 | 釘住 SHA | 該 SHA 內的定義位置 | 釘住時狀態 |
|---|---|---|---|---|
| `escalation-resolution` | `ruan6047/ai-workflow` #39，分支 `claude/WF-ESCALATION-RESOLUTION-GAP1` | `b039c0b08113382566d9b687087dea1f08f3915c` | `templates/review-escalation.md` §5 | 🔍待查核；最近一次查核 REQUEST_CHANGES |

對帳命令（任何人可重跑，輸出即判準，不依賴任何人的記憶）：

```bash
# 釘住的定義仍在（預期非空）
git show b039c0b:templates/review-escalation.md | grep -c '^`escalation-resolution` 解除'
# 是否已落地 main（0 = 尚未落地；非 0 = 落地對帳已到期）
git show origin/main:templates/review-escalation.md | grep -c '^`escalation-resolution` 解除'
```

**落地對帳**：相依卡併入 `main` 時以三款結算，全成立才將該列移出本節並轉為正式登記；
任一不成立即自上方列舉移除該 token。(1) `main` 的定義出處存在名稱**逐位元組等於**該 token
的定義；(2) 其必填欄位集合與釘住 SHA 相同，或差異隨同一次變更一併登記；(3) 本節對應列同時
刪除，不留孤兒 pin。相依卡被否決或改名時第 (1) 款即不成立。**本節是約定，其執行者是相依卡的
merge 授權者與本檔管轄者**；上面第二道命令回傳非 `0` 是它到期的可觀測訊號。

採用專案複製本範本時連同本節複製，該 token 在該專案同樣是 provisional，待上游結算後隨範本轉正。

**已知分歧（未在此裁定）**：`docs/WF_EVENT_MARKER_V2.md` §3.2 的 `event` 封閉語彙是**第二份**
事件型別登記。該表有而上方列舉無者為 `assign`、`amend`、`deployment-declaration`、
`deployment-status-change`；反向差集不必然是分歧，因該表只涵蓋具留言 marker 的子集。
兩份登記之間今天沒有任何對帳機制。孰為權威、CLI 動詞是否為事件型別、部署事件是否受本
envelope 管轄，皆逸出本檔。

## 3. Claim、lease 與 WIP

- claim command／workflow：<命令或 URL>
- concurrency key：<repository + card/resource key>
- lease TTL／續約：<時間與命令>
- 到期回收：<未提交變更檢查、通知與人工介入>
- WIP limit：agent <n>；review queue <n>；超過時 <行為>
- **派工前資源交集比對**：<命令；比對本卡寫入集 × 現役卡寫入集，撞則排隊。現役含 `📦已合併` 未收尾者—canonical §4.4>
- **破壞性 CLI（啟動須驗 lease，無 lease 拒跑）**：<入口清單>
- **當前仍有副作用的 CLI 入口（查核／探索禁跑）**：<入口清單／無—canonical §6.1 第 6 條>
- **worktree 註冊**：<認領時把實際路徑＋分支寫回卡的命令>；派工前必跑的 `doctor` 對帳：<命令>

## 4. Handoff 與 optional tmux adapter

- Handoff contract：從 [`handoff-contract.md`](handoff-contract.md) 建立 `<專案>/docs/HANDOFF_CONTRACT.md`；T2 以上或 owner 變更必填。
- Receiver 驗證：<驗證完整 SHA、baseline、lease、證據的 command／workflow>
- Receiver 接受事件：<`handoff-accepted` writer 與權限>
- tmux：<不用／僅 session launcher／僅 wake-up；不得作為遠端狀態來源>
- Local runtime：<路徑；必須在 `.gitignore`；清理／重啟程序>

## 5. 權限與事故處理

- GitHub Actions token／App 權限：<最小 permissions>
- 外部協作者可做／不可做：<claim、review、merge、release>
- GitHub 不可用時：<停止 claim／本機鎖的限制／恢復程序>
- 對帳：<claim、handoff、merge、release 後的檢查命令>
