# Handoff Contract — <專案名>

> 通用不變量見 canonical `AI_WORKFLOW.md` §4.1。此文件規範跨 writer 的 remote handoff；它不要求 tmux、daemon、Babashka 或本機 queue。

## 1. 不變量

- handoff 是 remote lifecycle event；聊天、PR 留言、tmux 訊息只可作通知，不可作狀態。
- sender 必須先 push `source_sha` 指向的 commit；`source_sha` 固定為完整 40 字元 SHA，不接受 branch name、短 SHA 或未提交工作區。
- receiver 驗證成功後才寫入 `handoff-accepted`；此事件才可轉移 owner。驗證失敗寫 `⏸阻塞` 或 findings，不得自行修正 sender 的內容。
- 每次 handoff 引用有效 `claim_event_id`；lease 過期、baseline 不一致或證據不足時不得接受。
- 本機 queue／`.swarmforge`／tmux runtime 必須 `.gitignore`；重啟時以 remote event 查詢未完成 handoff，不信任本機暫存狀態。

## 2. Handoff event payload

```yaml
event_id: <UUID>
type: handoff
card_id: <CARD_ID>
actor: <lifecycle event writer；通常等於 from>
from: <GitHub account / model@tool>
to: <role / GitHub account / model@tool>
next_stage: implementation | review | release
source_sha: <full-40-char-commit-sha>
branch: <pushed remote branch>
claim_event_id: <active claim event ID>
state_version: <strictly increasing integer>
iteration: <integer>
baseline: <spec/design baseline version or N/A>
evidence:
  - <test / CI / review / decision URL>
summary: <one-line change or request>
occurred_at: <write-time ISO 8601>
```

## 3. Receiver acceptance checklist

- [ ] `source_sha` 可從已推送的 remote ref 解析為 commit，且與 handoff payload 完全相符。
- [ ] card、iteration、next stage 與 `claim_event_id` 對應的有效 lease 一致。
- [ ] baseline 與卡片／Initiative 一致，或 handoff 明確標記為 blocked 並附基線變更事件。
- [ ] 所需 evidence 存在、可讀，且工作區／驗證環境符合任務要求。
- [ ] receiver 在 remote adapter 追加 `handoff-accepted`，記錄 `source_sha`、actor、時間與驗證證據；之後才開始工作。

## 4. Optional local tmux adapter

| 能力 | 可否使用 | 限制 |
|---|---|---|
| 對每個 worktree 開 session | ✅ | session 不代表 claim 或 owner |
| 收到 remote handoff 後喚醒 idle agent | ✅ | wake-up 可遺失；agent 仍需查 remote event |
| 本機 inbox/outbox | ✅ | 僅快取 remote event，不得成為跨機 queue 或唯一 audit trail |
| 直接改 Ledger／lease／state | ❌ | 只能由 remote coordination adapter 寫入 |

## 5. 專案實作

- Remote handoff writer／API：<GitHub Action、App 或其他受保護 adapter>
- SHA 驗證命令：<command>
- `handoff-accepted` writer 與授權：<identity／workflow>
- tmux launcher／wake-up：<可選 command；不用填—>
- Runtime 路徑與 `.gitignore`：<path>
- 失敗、重試與人工介入：<runbook link>
