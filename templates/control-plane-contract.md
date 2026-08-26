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
type: claim | handoff | handoff-accepted | contract-baseline | preflight-failed | review | review-invalid | review-correction | escalation-epoch-change | escalation-checkpoint | status-change | correction | merge | release
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

**允許的狀態轉移、Gate／preflight 退回、`⏸阻塞` 的 TTL、escalation checkpoint 與
`🚨已升級` 的決策 owner，規則本體在 canonical
[`~/Dev/ai-workflow/AI_WORKFLOW.md` §0.2「允許的狀態轉移」](../../ai-workflow/AI_WORKFLOW.md)。**
⛔ **本檔不放本體、不複製全文**，只做兩件事：指向該節，並宣告本專案與該節的差異。每條差異
必須指名它由**哪一行程式或哪一位角色**執行：

<專案差異；⛔ 不得留空、⛔ 不得留本佔位符原樣——無差異時逐字寫「無差異」>

> (a) **這個位置刻意保留，但它裝的是差異宣告、⛔ 不是規則本體。** 保留的理由：刪掉等於宣稱
> 「專案不可能有差異」，那是假的——部署軸適不適用、哪些 CLI 入口有副作用、維護階段用不用
> 得到，逐專案都不同（canonical `AI_WORKFLOW.md` §7 的委派表列的正是這幾項）。差異宣告保留
> 了表達力，又不要求任何人憑空重寫一整張表。
> (b) **規則本體刻意不在本檔**，⛔ 不是遺漏、⛔ 也不是還沒寫。為什麼：`ADOPTION.md` 第 4 步
> 逐字要求「從 `templates/control-plane-contract.md` **建立**
> `<專案>/docs/CONTROL_PLANE_CONTRACT.md`」——那是**建立一份實體檔**，不是連結（實測
> cpbl-analytics 的 `docs/CONTROL_PLANE_CONTRACT.md` 為 220 行的獨立檔、開頭是它自己的標題與
> 內文，@ `3b470d70`）。⇒ 規則本體放在本檔，等於**每採用一個專案就多印一份會各自漂移的
> 權威**，而那正是這條規則要治的病。⚠️ 同一份 `ADOPTION.md` 對派工／派審那批範本另寫「使用
> 時組裝，**不複製進專案 repo**」⇒ repo 自己就把範本分成「會被複製」與「不會被複製」兩類，
> 而**本檔屬會被複製的那一類**。禁令出處兩處，⚠️ **措辭不同故分開引**：canonical §7 逐字
> 「專案只保留指向本檔的 stub，**不複製全文**」；`AGENTS.md` 逐字「各專案只放指向本檔的
> stub、**不複製全文**」。
> (c) ⛔ **不得由此推出**三件事。其一，「專案可以在這裡改寫 canonical §0.2 的任何一列」
> ——差異宣告的作用是**記下不一致並指名執行者**，不是就地立法；改本體要回 canonical 改。
> 其二，「不放本體＝本檔對狀態轉移沒有話語權」——差異宣告就是話語權，只是它產出的是**揭露**
> 不是**規則**。其三，「本欄留空＝沒有差異」——見下方不留空的理由。
>
> ⛔ **不留空的理由**是形狀性的，不是禮貌：空白與「還沒想過」在事後長得一模一樣，而這兩者
> 的處置完全不同（同一形狀的既有判例見 `cli/src/wf_cli/commands/handoff_cmd.py` 的
> `PHASE_UNDECIDABLE_MARK`：「⛔ 不留白：留白與『這個欄位還沒上線』在事後長得一模一樣」）。

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
