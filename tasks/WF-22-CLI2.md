# WF-22-CLI2 鏈深與 iteration 的寫入路徑〔T2；🟡流程〕

- 需求：ruan6047（2026-08-04 批准「cutover 後立刻開」——CLI1 查核 F1 追卡）　規劃：Claude Fable 5@Claude Code（PM 祕書）
- 執行：待指派（建議 L2）　查核：待指派（新 context；≠ 執行）
- Initiative：WF-22　spec 基線：決議 v1　db_scope: none
- 服務的原始目標：決議 5（鏈式停損）與退回計數的機械欄位不得恆為虛設 0
- 分支：本 repo `ai/<執行者>/WF-22-CLI2`

## 核心痛點（CLI1 查核 F1）

`chain_depth` 與 `iteration` 兩個凍結欄位在五指令中沒有任何寫入路徑（底層 `set_field_value` 能寫，組裝層沒接）：停損深度上限（原始目標下 ≤2 層）與退回遞增（REQUEST_CHANGES → iteration+1）無法機械落地。

## 範圍

1. `open --chain-depth N`（預設 0）；N>2 時硬拒（決議 5 硬上限，拒絕訊息引整鏈重審協定）。
2. iteration 遞增接點：由需求方裁決掛在何處——候選 (a) `handoff --next-stage implementation`（查核退回語意）自動 +1；(b) 顯式 `--iteration N`。**執行者開工前先向 PM 提交一頁建議，需求方拍板後實作**（不得自行選）。
3. 回歸測試補齊兩欄位的寫入與拒絕路徑。

## 驗收

- [ ] `open --chain-depth 3` 被拒且訊息含停損協定引用；`0-2` 正確寫入欄位。
- [ ] iteration 遞增路徑依需求方拍板實作，附正反向測試。
- [ ] `uv run pytest` 全綠（含既有 98）。

## Log

- 2026-08-04 register by Claude Fable 5@Claude Code（PM 祕書，依需求方批准）；📥Backlog。來源：WF-22-CLI1 查核 F1。
