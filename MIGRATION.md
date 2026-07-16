# 舊版工作流升級指南 (Migration Guide)

本指南將採用舊版「線性 Ledger／卡片 log／四個 commit trailer」的專案升級至目前的變更分級、Discovery／Design Gate 與聯邦式 control-plane 契約。**不要重寫歷史 commit 或封存卡；升級只建立新的基線事件。**

## 適用版本與目標

| 舊版特徵 | 升級後 |
|---|---|
| 狀態直接手改在 `TASKS.md` | append-only event log 產生 Ledger current-state projection |
| 所有變更走同一流程 | T0–T4 按風險選閘門 |
| 大卡只要求 spec | Discovery → Design（適用時）→ Plan Gate |
| 單一 worktree 規則 | 執行 worktree + 不持有 claim 的 disposable verification sandbox |
| 四個 trailer 都在每筆 commit | T0/T1：Requested + Implemented；T2+：再加 Planned；核可／merge：再加 Reviewed |

## 0. 升級前凍結與備份

1. 由 Coordinator 暫停新的 claim、merge、migration 與 deployment。
2. 確認所有 active branch 都已推送；記錄目前 `git worktree list`、活卡 Ledger、container／port 與 DB lease。
3. 建立一個可回退 tag，例如 `workflow-pre-wf15-<date>`；不 force-push、rebase 或改寫既有卡片／log。
4. 若已有多 writer，先指定升級 owner，並在 control-plane 尚未啟用前使用唯一人工 Coordinator。

## 1. 安裝新文件，不搬移歷史

1. 將新 canonical stub、`TASKS.md`、`tasks-card.md`、`bug-card.md`、`discovery-brief.md`、`design-brief.md`、`research-plan.md` 與 `control-plane-contract.md` 放入專案文件目錄。
2. 保留舊卡片與 `BUGS.md` 原文；不要為了新格式補寫舊事件。
3. 對每張活卡建立一次 `migration-baseline` lifecycle event：記錄舊狀態、owner、branch、worktree、已知 iteration、source SHA 與建立時間；此 event 成為 `state_version: 1`。
4. 從 baseline event 產生新的 Ledger。若新／舊 Ledger 不一致，停止 claim，先由 Coordinator 對帳。

## 2. 分類活卡並設定過渡規則

| 活卡情況 | 升級動作 |
|---|---|
| 已在 `🔍待查核` | 保留原 source SHA；建立 review event 後再進新流程 |
| 已在 `🔨執行中` | 建 baseline，套用 tier；未完成部分照新規則交接 |
| 已合併／部署中 | 不重開 Discovery／Design；僅建立部署事件與驗證證據 |
| 原因不明／依賴失效 | 標為 `⏸阻塞`，記錄 owner、解除條件與 TTL |
| 需求／設計已改變 | 回 Initiative，建立新的 Discovery／Design 基線；不要直接改子卡範圍 |

既有 commit 的四個 trailer 視為有效歷史，不回填或改寫。新 commit 從升級後開始套用目前 trailer 規則。

## 3. 建立 adapter 與資源鎖

1. 以 `CONTROL_PLANE_CONTRACT.md` 選定 remote coordination adapter（GitHub 為預設）與 event store。
2. 指定唯一 lifecycle writer；GitHub Project／Issue 僅做協作 UI，不可單獨作為不可覆寫歷史。
3. 實作 local resource lock：worktree、port、container、cache、queue 與 DB namespace。
4. 設定 claim concurrency key、lease TTL、逾期回收、agent／review WIP limit 與外部協作者權限。
5. 先以一張非紅線測試卡演練：claim → handoff → review → merge → release → Ledger projection。

## 4. 啟用新 Gate 與任務格式

- 新開的使用者可見 T3/T4 卡：Discovery Brief → Design Brief → Plan／spec。
- 純技術 T3/T4：Discovery 後在卡片記錄 Design Gate `N/A` 理由，再進 Plan。
- T1 僅限非執行期文案；任何 versioned source／設定變更至少 T2。
- 大型 Initiative 先建立依賴圖與 spec 基線；中途變更先更新父卡並重新核可，再調整子卡。

## 5. 驗證與回滾

升級完成前，Coordinator 必須確認：

- 每張活卡恰有一個最新 lifecycle state，且 Ledger 可由 event log 重建。
- 每個 active claim 的 branch、worktree、lease 與共享資源 lock 一致。
- review event 具固定 source SHA、finding 與處置。
- 既有 CI／部署仍可從 main source SHA 回報結果。

若驗證失敗：停止新 claim，保留 event store 與舊 Ledger，恢復 `workflow-pre-wf15-<date>` tag 對應的文件規則；**不得刪除已產生事件**。修正 adapter 後，以新的 `migration-baseline` event 再次對帳。

## 6. 建議過渡期

前 2 週或前 10 張完成卡採人工 Coordinator shadow mode：adapter 產生 event 與 Ledger，但由人比對後才允許狀態轉換。回顧 claim 衝突、審查等待、lease 過期與重建 Ledger 的結果，再取消人工比對。
