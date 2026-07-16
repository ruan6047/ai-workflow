# Control-plane Contract — <專案名>

> 共同不變量見 canonical `AI_WORKFLOW.md` §4.1。本檔定義該專案如何把協作狀態與本機資源鎖分離；不得填入 token、secret 或使用者個資。

## 1. Adapter 邊界

| 範圍 | 實作 | 事實來源／用途 |
|---|---|---|
| Remote coordination（GitHub 預設） | <Issue／PR／Project／Actions workflow> | 唯一 lifecycle writer：跨人 task、review、lease、CI 與協作事件 |
| Local resource | <原子目錄鎖／OS lock／container runtime> | worktree、port、container、未提交變更的暫時互斥；只回報 telemetry，不改 card state |
| Event store | <受保護 Git history／外部 append-only store> | 不可覆寫事件歷史 |
| Ledger projection | <產生方式與位置> | 活卡 current-state 顯示；不得手改 |

## 2. Event schema 與狀態

```yaml
event_id: <UUID/monotonic ID>
card_id: <CARD_ID>
type: claim | handoff | review | status-change | merge | release
actor: <GitHub account / model@tool>
occurred_at: <ISO 8601>
state_version: <strictly increasing integer>
iteration: <integer>
source_sha: <required for review/handoff/merge/release>
evidence: <PR, CI, test or decision link>
```

local telemetry 另以同一 envelope 記錄 `resource-acquired | resource-released`，但必填 `lifecycle: false`、`claim_event_id`，且不得填 `state_version` 或改 card state。

列出允許的狀態轉移、Gate 退回、`⏸阻塞` 的 TTL 與 `🚨已升級` 的決策 owner：

<專案實作>

## 3. Claim、lease 與 WIP

- claim command／workflow：<命令或 URL>
- concurrency key：<repository + card/resource key>
- lease TTL／續約：<時間與命令>
- 到期回收：<未提交變更檢查、通知與人工介入>
- WIP limit：agent <n>；review queue <n>；超過時 <行為>

## 4. 權限與事故處理

- GitHub Actions token／App 權限：<最小 permissions>
- 外部協作者可做／不可做：<claim、review、merge、release>
- GitHub 不可用時：<停止 claim／本機鎖的限制／恢復程序>
- 對帳：<claim、handoff、merge、release 後的檢查命令>
