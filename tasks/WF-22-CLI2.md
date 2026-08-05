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
2. iteration 遞增接點：**需求方 2026-08-05 已拍板＝(a)**——`handoff --next-stage implementation`（查核退回語意）**自動 +1**，另留顯式 `--iteration N` 覆寫供異常修正（覆寫時輸出警示與理由要求）。與契約「有效實質退回遞增 iteration」語意一致。執行者依此實作，不再中停請示。
3. 回歸測試補齊兩欄位的寫入與拒絕路徑。

## 驗收

- [ ] `open --chain-depth 3` 被拒且訊息含停損協定引用；`0-2` 正確寫入欄位。
- [ ] iteration 遞增路徑依需求方拍板實作，附正反向測試。
- [ ] `uv run pytest` 全綠（含既有 98）。

## Log

- 2026-08-04 register by Claude Fable 5@Claude Code（PM 祕書，依需求方批准）；📥Backlog。來源：WF-22-CLI1 查核 F1。

## Log

- 2026-08-05 執行完成（d68ae41，Sonnet）：chain-depth 硬拒＋iteration 自動遞增/覆寫，18 新測試。
- 2026-08-05 查核 APPROVE（Sonnet 新 context，零阻塞）：對抗驗證含剝離 gh 的真實 CLI 執行與繞過 CLI 直建 Card；F1（低）＝執行者跳過真實 Project 演練的裁量理由未留痕——**理由經查核者拆解 gh 呼叫組裝碼判定成立**（三個子操作皆為 CLI1 已實跑過的呼叫形狀），依處置於此補痕；首次真實 handoff 退回發生時視為事後驗證。F2（低）＝chain-depth/iteration 無下界檢查（負值靜默接受）——記 CLI 待辦，未來順手補。
