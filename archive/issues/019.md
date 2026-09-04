# #19 WF-CLI-CARD-AMEND1 wfcli 補上開卡後的通用卡面修訂能力
- state: closed  created: 2026-08-10T10:40:14Z  closed: 2026-08-10T16:37:11Z
- url: https://github.com/ruan6047/ai-workflow/issues/19
- comments: 10

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code
- 執行：待指派　查核：獨立校讀
- Initiative：—　spec 基線：需求方 2026-08-10 裁決（依 ai-workflow#17 卡面修復查核的兩項 governance finding）。#12 為相關但範圍不同的既有卡：其範圍僅 tier 更正，不涵蓋通用卡面修訂
- DB：db_scope=none
- 服務的原始目標：讓卡面修訂與其他 lifecycle 寫入走同一條可稽核通道，不必為了改一個欄位而繞過 wfcli。

## 簡介
<!-- card-brief:begin -->
新增 wfcli amend 動詞，讓開卡後修訂卡面欄位（spec 基線／驗收／驗證／資源宣告／級別）走唯一寫入通道而非繞道 gh issue edit，每次自動 append Log 並保留被改欄位原值。**適用時機**：要改已開卡的卡面欄位、在找合法寫入路徑時；或要查「卡面修訂留什麼痕、原值保不保留」的依據時。⛔ 非射程：既有 Log 條目一律拒改（append-only 不因本能力破例）；Log 排版損壞不提供自動修復路徑——--repair-log-layout 依需求方裁定移除，改走 cli/README.md 的八步人工 runbook ＋ amend --dry-run 驗證出口；tier 更正的舊卡 aiwf#12 已併入本卡後關閉，不另追蹤。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：wfcli 無法在開卡後修訂卡面欄位（spec 基線、驗收、驗證、資源宣告等），只有 open 時能設定。2026-08-10 #17 的 spec 基線更正與 Log 渲染修復因此被迫以 gh issue edit 直接寫入，繞過唯一寫入通道；查核並指出 #12 只涵蓋 tier，不能作為此缺口的追蹤卡，等於這個缺口目前無人追蹤，每次卡面更正都會再繞一次。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/",
    "file:cli/src/wf_cli/card.py",
    "file:cli/src/wf_cli/cli.py",
    "file:cli/README.md",
    "file:cli/tests/"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 提供開卡後修訂卡面欄位的指令，至少涵蓋 spec 基線、驗收條件、驗證項目、資源宣告
- [ ] 每次修訂自動 append Log 留痕，並記錄被修改欄位的原值；不得無痕覆寫
- [ ] 拒絕修改既有 Log 條目（append-only 不因本能力破例）
- [ ] 與 #12（tier 更正）的範圍界定明確：擇一實作，或明示 #12 併入本卡後關閉

## 驗證

- [ ] cli 測試涵蓋各欄位修訂路徑與 Log 留痕（含原值保留、拒改既有 Log）
- [ ] 以 #17 於 2026-08-10 的 spec 基線更新情境重放，證明無須 gh issue edit
- [ ] Log 排版修復依設計裁決不提供自動路徑，改以受控人工修復驗證：照 amend 印出的八步 runbook 走完，第 4 步驗證指令對正確修復印「必要條件通過」、對額外改動或多處候選標記印 NG，第 7 步 wfcli amend --dry-run 不再回報排版錯誤；並確認第 2 步的人工語意判斷與第 5 步的完整 diff 審閱皆已執行
## Log

- 2026-08-10T18:40:13+08:00 open by Claude Opus 5@Claude Code；owner 待指派；iteration 0。
- 2026-08-10T19:05:18+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree claude/WF-CLI-CARD-AMEND1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1；交付狀態 🚧進行中。
- 2026-08-10T19:12:52+08:00 amend by wf-cli → 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/commands/", "file:cli/src/wf_cli/card.py", "file:cli/tests/" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/commands/、file:cli/src/wf_cli/card.py、file:cli/src/wf_cli/cli.py、file:cli/README.md、file:cli/tests/」；理由 開卡時漏列：子指令註冊必動 cli.py，指令對照表必動 README.md（本卡執行中以本指令自我修訂，兼作 live smoke run）。
- 2026-08-10T19:14:45+08:00 handoff by wf-cli → owner 獨立校讀；iteration 0；SHA 72bab2dd8bcbd3040a128d55401483f67e6681f8；證據 新增 wfcli amend（spec 基線／驗收／驗證／資源宣告／級別），#12 併入；212 passed（185 baseline + 27 新增）；live smoke run 已以本指令修訂本卡自身資源宣告，原值完整入 Log。
- 2026-08-10T19:28:47+08:00 handoff by wf-cli → owner 獨立校讀；iteration 0；SHA 3fc771afd5defc26421df5af85047b6e2af9c2c9；證據 R1 四項 finding 全修：原值不再截斷、新增 --repair-log-layout 窄路修復（受「只准動空白」不變量約束）、級別讀回驗證＋顯式 --record-unlogged-change 補救半寫入、勾選狀態改為預設不沿用；另修一個自測抓到的偵測器格式 bug。227 passed（185 baseline + 42）。
- 2026-08-10T19:37:58+08:00 handoff by wf-cli → owner 獨立校讀；iteration 0；SHA 08e8b1776f0cb9f582f0060a63c6ab1f39e886e7；證據 R2 兩項 blocking 已修：修復範圍縮到 Log 區段（其前逐位元不變＋資源宣告解析結果須不變），撤回錯誤的『剝空白後相同』證明；新增寫入前重讀比對（exit 6）並三處明寫非原子 CAS 的殘餘競態；exit 5 改印可執行的三步驟恢復指令。232 passed（185 baseline + 47）。
- 2026-08-10T19:56:13+08:00 handoff by wf-cli → owner 獨立校讀；iteration 0；SHA 250d4cb2cd5a771405a75fc799e4375247a802b5；證據 依需求方裁決移除 --repair-log-layout 而非再次加固：三輪查核加一次自驗累計五個同類破口（皆為以論證代替保證）。淨刪除 -412/+85；split_at_log 的 fail-closed 保留不變。222 passed（185 baseline + 37）。
- 2026-08-10T19:59:37+08:00 handoff by wf-cli → owner 獨立校讀；iteration 0；SHA db2100d7e172c2d8ef809018d696e8bfc9ddb9f9；證據 依需求方裁決移除 --repair-log-layout（三輪查核＋一次自驗累計五個同類破口），並補上備案：排版損壞時印出六步人工程序＋amend --dry-run 機械驗證出口，README 收錄完整可貼指令。225 passed（185 baseline + 40）。
- 2026-08-10T20:03:04+08:00 handoff by wf-cli → owner 獨立校讀；iteration 0；SHA 2a742df5cbd61550a4c366e7aad0a240ee0745d2；證據 備案再補一層：新增 --escalate，排版損壞時在 Issue 留下含機器標記與 runbook 的求助留言（不碰 body、不改交付狀態、只對排版損壞生效）。227 passed（185 baseline + 42）。
- 2026-08-10T20:06:50+08:00 handoff by wf-cli → owner 獨立校讀；iteration 0；SHA ea74c6646f4a737c4d539de812a444de4ee74cc8；證據 自審抓到並修正兩個 --escalate 的真 bug（dry-run 仍寫入留言、留言失敗導致例外逸出蓋掉 runbook），並修正原測試以 if posted 兩路放行的假通過。229 passed（185 baseline + 44）。
- 2026-08-10T20:15:10+08:00 amend by wf-cli（op 62e3a5b6）→ 驗證：原值「[ ] cli 測試涵蓋各欄位修訂路徑與 Log 留痕（含原值保留、拒改既有 Log）；[ ] 以 #17 於 2026-08-10 的兩次實際修訂情境重放，證明全程無須 gh issue edit」→ 新值「cli 測試涵蓋各欄位修訂路徑與 Log 留痕（含原值保留、拒改既有 Log）；以 #17 於 2026-08-10 的 spec 基線更新情境重放，證明無須 gh issue edit；Log 排版修復依設計裁決不提供自動路徑，改以受控人工修復驗證：照 amend 印出的六步 runbook 走完，第 3 步驗證指令對正確修復印 OK、對額外改動印 NG，第 5 步 wfcli amend --dry-run 不再回報排版錯誤」；理由 依 R4 查核裁定：Log 排版修復已依設計裁決移除自動路徑，原條文的『兩次情境自動重放』無法成立；改為受控人工修復＋wfcli dry-run 驗證（查核者建議、需求方核可）。
- 2026-08-10T20:16:15+08:00 handoff by wf-cli → owner 獨立校讀；iteration 0；SHA 28200c54e7aee4d909d004cbea80b3722aa7296e；證據 R4 兩項 blocking 已修：runbook 第 1 步補建 orig 副本、第 3 步判準改為『恰好等於原文做一次目標替換』；驗證指令抽成單一常數供 stderr／README／測試共用並由測試實際執行。另依查核裁定以本卡工具自我修訂驗證條文（op 62e3a5b6）。233 passed（185 baseline + 48）。
- 2026-08-10T20:24:17+08:00 handoff by wf-cli → owner 獨立校讀；iteration 0；SHA cc8e20266848cd16214b3f8d821756cb66128d57；證據 R5-01 已修：撤回『機械證明修對了』的宣稱、強制候選 token 恰好一處、runbook 六步擴為八步（新增無法機械化的人工判斷與完整 diff 審閱）、第 7 步 --dry-run 加註界線。真實 #17 重驗：正確修復通過／順手改壞 NG／多 token 含 fence NG。237 passed（185 baseline + 52）。
- 2026-08-11T00:21:32+08:00 amend by wf-cli（op ed3b259b）→ 驗證：原值「[ ] cli 測試涵蓋各欄位修訂路徑與 Log 留痕（含原值保留、拒改既有 Log）；[ ] 以 #17 於 2026-08-10 的 spec 基線更新情境重放，證明無須 gh issue edit；[ ] Log 排版修復依設計裁決不提供自動路徑，改以受控人工修復驗證：照 amend 印出的六步 runbook 走完，第 3 步驗證指令對正確修復印 OK、對額外改動印 NG，第 5 步 wfcli amend --dry-run 不再回報排版錯誤」→ 新值「cli 測試涵蓋各欄位修訂路徑與 Log 留痕（含原值保留、拒改既有 Log）；以 #17 於 2026-08-10 的 spec 基線更新情境重放，證明無須 gh issue edit；Log 排版修復依設計裁決不提供自動路徑，改以受控人工修復驗證：照 amend 印出的八步 runbook 走完，第 4 步驗證指令對正確修復印「必要條件通過」、對額外改動或多處候選標記印 NG，第 7 步 wfcli amend --dry-run 不再回報排版錯誤；並確認第 2 步的人工語意判斷與第 5 步的完整 diff 審閱皆已執行」；理由 依 R6-01 查核裁定並經需求方核可：R5 將 runbook 由六步改為八步後卡面未同步，步號全部漂移；一併補上多處候選需印 NG、以及第 2 步人工語意判斷與第 5 步完整 diff 審閱亦須確認執行（那兩步是語意判斷的實際承載處）。
- 2026-08-11T00:23:43+08:00 handoff by wf-cli → owner 獨立校讀；iteration 0；SHA 0cd30aa7c50b23f0e65256536c89c89594d60e59；證據 R6-01 卡面驗證條文已依核可更新為八步／正確步號並補上多處候選 NG 與人工環節（op ed3b259b）；R6-02 README 殘留的「機械證明修好了」已改為「機械驗證必要條件」。另依需求方要求以八項機械對照重掃文件，補上三個未文件化旗標。237 passed。
- 2026-08-11T00:32:56+08:00 review by wf-cli → APPROVE（✅通過）；查核者 獨立校讀（GitHub author ruan6047 轉貼；模型／工具為自述）；core_pain_resolved yes；self_run 5 項；findings 1 項（blocking 0）；attempt WF-CLI-CARD-AMEND1-e0-0cd30aa7c50b23f0e65256536c89c89594d60e59。
- 2026-08-11T01:47:52+08:00 handoff by wf-cli → owner ruan6047；iteration 0；SHA 5d821e12fd0c71eaababc3dcf7fe408a49cc4d9d；證據 已 APPROVE、已 merge 至 main 5d821e12fd0c71eaababc3dcf7fe408a49cc4d9d、worktree 與分支已清、Issue 已關閉；本次補做 release 轉終態以釋放資源宣告（先前結案漏此步，導致 assign 將已完成卡誤判為活卡）。
- 2026-08-26T22:04:49+08:00 amend by wf-cli（op 2afe6536）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:3f14d503c47295d6da48d61e7622d3f8f929d220289e484f812dc228bb9cf25d (712 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5239399671 · 2026-08-10T11:15:50Z

## 派審：WF-CLI-CARD-AMEND1

⚠️ 審核對象是 **`ruan6047/ai-workflow#19`**（Issue）。本卡是 CLI 實作卡，**有程式碼改動**（與同 repo 的 #15 文件卡不同）。

### 進駐與身分核對

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1
分支：claude/WF-CLI-CARD-AMEND1
被審 SHA：72bab2dd8bcbd3040a128d55401483f67e6681f8
基線：origin/main dbfdb9c85fa92fff81efcc6b01a2a275f6378091
iteration：0（首次查核）
```

第一步先核對，不符就停下回報：

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1
git rev-parse HEAD && git diff --name-only origin/main
```

預期 `72bab2d…` 與五個檔案：`cli/README.md`、`cli/src/wf_cli/card.py`、`cli/src/wf_cli/cli.py`、`cli/src/wf_cli/commands/amend_cmd.py`、`cli/tests/test_amend.py`。

### 本卡在做什麼

`open` 之後卡面就凍住了，`wfcli` 沒有修訂入口。2026-08-10 一天內因此繞過唯一寫入通道四次（#15 的 tier 用 Project GraphQL mutation、#17 的 spec 基線與 Log 渲染修復用 `gh issue edit`）。本卡補上 `wfcli amend`，涵蓋 spec 基線／驗收條件／驗證項目／資源宣告／`級別`。

**`WF-CLI-TIER-MUTATION1`（#12）併入本卡**（驗收第 4 條允許「擇一實作或明示併入」）：級別是 Project SINGLE_SELECT 欄位、`set_field_value` 已支援，與 body 欄位放同一指令。#12 尚未關閉——執行者判斷應在本卡 merge 後才關，避免本卡被退回而 #12 已關。**請一併裁定這個時序是否恰當。**

### 必跑（`self_run` 需附實際輸出）

```bash
cd cli && uv run pytest -q          # 預期 212 passed（185 baseline + 27 新增）
```

`--dry-run` 不寫任何遠端狀態，可安全對真實卡驗證（下例對已結案的 #15 唯讀試算，請自行換卡）：

```bash
cd cli && uv run wfcli amend WF-CLI-CARD-AMEND1 \
  --owner ruan6047 --project 4 --repo ruan6047/ai-workflow \
  --reason "查核試算" --spec-baseline "查核用假值" --dry-run
```

### 逐項驗收

1. 指令是否涵蓋 spec 基線、驗收條件、驗證項目、資源宣告（卡面驗收第 1 條）。
2. 每次修訂是否 append Log 並記錄**原值**；是否真的不可能無痕覆寫（第 2 條）。
3. 是否拒絕修改既有 Log 條目（第 3 條）。
4. 與 #12 的範圍界定是否明確（第 4 條）。
5. 回歸測試是否涵蓋各欄位修訂路徑與 Log 留痕（驗證第 1 條）。
6. 是否能以 #17 於 2026-08-10 的兩次實際修訂情境重放、全程無須 `gh issue edit`（驗證第 2 條）。**這一條請實際重放，不要只看程式碼。**

### 請特別質疑這五點

1. **`_fold` 的截斷會不會讓「原值必留」跳票。** 原值超過 400 字時 Log 只留前 400 字加註記。這等於超長欄位的原值**無法完整還原**，與驗收第 2 條「記錄被修改欄位的原值」是否衝突？若衝突，正解是不截斷、還是把原值另存他處？
2. **勾選狀態沿用是否會誤導。** 清單整份取代時，文字未變的項目沿用原勾選狀態。反面風險：條件文字沒變但語意脈絡已變（例如相鄰條件全改），沿用勾選會讓人以為那項仍然通過。這個取捨對嗎？
3. **半寫入視窗。** body 先寫、Project `級別` 後寫，兩次遠端呼叫無交易性。若 body 寫成功而級別寫失敗，Log 會宣稱級別已改但實際沒改——這與 `handoff-contract.md` §3.1.3 剛定義的「三面一致」精神相反。是否應改為級別先寫、或加偵測？
4. **`split_at_log` 的 fail-closed 是否過嚴。** body 只要含 `## Log` 字樣而非獨立標題行就整個拒絕修訂。這會讓排版已壞的卡完全無法用 `amend` 修好，只能再繞 `gh issue edit`——工具在最需要它的情境反而不能用。這個取捨對嗎？
5. **自我修訂的獨立性。** 執行者用本指令修訂了本卡自己的資源宣告（補開卡時漏列的 `cli.py`、`README.md`），Log 見卡面 19:12:52 那筆。這既是 live smoke run 也是「改自己的驗收基準」。請判斷是否恰當，或應由他人執行。

### 執行者主動揭露

- 開卡時資源宣告漏列 `cli/src/wf_cli/cli.py`（子指令註冊必動）與 `cli/README.md`（指令對照表必動），已於執行中以本指令補上並留痕。
- `--dry-run` 實跑抓到一個措辭 bug（截斷註記對新值也寫「原值共 N 字」），已改為「全文共 N 字」；mocked 測試不會抓到這類問題。
- 本 repo 無 ruff 設定，`pytest` 即唯一機械閘門。

### 環境紅線與獨立性

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。執行者為 Claude Opus 5@Claude Code。依 `CLAUDE.md`，T2 CLI 卡查核不強制換模型家族，但**本卡動的是唯一寫入通道本身**，執行者建議仍由獨立查核者進行。

若你無法執行 `wfcli`，請依 `templates/handoff-contract.md` §3.1.2 在本 Issue 留一則 `wf-review-receipt:v1` 收據（`card_id`、完整 `source_sha`、查核報告原文 UTF-8 `report_sha256`），由 PM 對帳後轉錄。

**輸出**：依 `templates/review-prompt.md` §5 的結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5239531620 · 2026-08-10T11:29:54Z

## 派審：R2（取代前一則 R1 派審詞）

⚠️ 審核對象 **`ruan6047/ai-workflow#19`**。CLI 實作卡，有程式碼改動。

### 進駐與身分核對

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1
分支：claude/WF-CLI-CARD-AMEND1
被審 SHA：3fc771afd5defc26421df5af85047b6e2af9c2c9   ← 已非 R1 的 72bab2d
基線：origin/main dbfdb9c85fa92fff81efcc6b01a2a275f6378091
iteration：1
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1
git rev-parse HEAD && git diff --name-only origin/main
```

預期 `3fc771a…` 與五個檔案：`cli/README.md`、`cli/src/wf_cli/card.py`、`cli/src/wf_cli/cli.py`、`cli/src/wf_cli/commands/amend_cmd.py`、`cli/tests/test_amend.py`。

### R1 四項的處置

| finding | 處置 |
| --- | --- |
| R1-01 原值截斷 | Log 一律寫**完整原值不截斷**；另拆 `_short` 只給主控台。補超長 spec（800 字）與超長清單（500 字）回歸 |
| R1-02 排版壞掉無法修 | 新增 `--repair-log-layout`，須同時給 `--expect-body-sha256`、不得與其他旗標併用，並受「**只准動空白**」不變量約束；修復留下原 body 雜湊。測試直接重放 #17 實際損壞 |
| R1-03 半寫入 | 級別先寫並**讀回驗證**（不符回 exit 5）再寫 body；每次執行帶 `op` 識別碼；補救改為顯式 `--record-unlogged-change` |
| R1-04 勾選沿用 | 預設重設未勾選，`--preserve-checked` 才沿用 |

**一項與 disposition 的偏離，請重點裁定。** R1-03 的 disposition 要求「失敗後讀回驗證與可恢復的 partial 狀態／補償留痕，並在重試時偵測不一致」。執行者先實作了**自動**偵測（欄位已是目標值但 Log 沒記 → 判定半寫入並補記），自測後改掉：該條件同時符合「**開卡時就是這個值**」的正常 no-op，CLI 分不出兩者。自動補記會把正常 no-op 記成一筆不存在的變更——為了修不實留痕而製造另一種不實留痕。因此改為顯式 `--record-unlogged-change`，由操作者承擔判斷，並在拒絕 no-op 時提示該旗標。**請裁定這個偏離是否可接受，或應以其他方式達成自動偵測。**

### 必跑（`self_run` 需附實際輸出）

```bash
cd cli && uv run pytest -q          # 預期 227 passed（185 baseline + 42）
```

### 本輪請特別攻擊這四點

1. **「只准動空白」不變量是否真的擋得住內容竄改。** `repair_body_layout`（`card.py`）的判準是：把原 body 的字面 `\n` 刪除後剝掉所有空白，須與修復後剝掉空白逐字相同。請找反例——是否存在某種輸入，能通過此檢查卻實際改變語意（例如把兩個 token 黏成一個、或讓資源宣告 JSON 解析結果不同）。這是本輪最該打的一點。
2. **`--record-unlogged-change` 會不會變成繞過 no-op 檢查的後門。** 它只補留痕不改欄位，且欄位不符時拒絕（有測試）。但它允許在「欄位本來就是這個值」時寫下一筆「先前半寫入」的留痕——若操作者判斷錯誤或蓄意，Log 就會有一筆假的變更史。這個把判斷推給人的設計，是否比自動偵測更差？
3. **`--expect-body-sha256` 的防護強度。** 它證明操作者取得過某個 body 版本，但不防 TOCTOU：取 hash 之後、寫入之前 body 若被他人改動，指令會因 hash 不符而拒絕（安全）——請確認這條推論成立，特別是 `list_items` 讀取與 `set_item_body` 寫入之間有沒有可被利用的視窗。
4. **exit 5 的可恢復性。** 讀回驗證失敗時 body 未寫、欄位可能已改。此時卡處於「欄位改了、Log 沒記」狀態，而下一步正是 `--record-unlogged-change`。請確認這條恢復路徑在文件與 stderr 提示中足夠明確，不會讓操作者卡住。

### 其餘驗收（卡面條文）

1. 涵蓋 spec 基線、驗收條件、驗證項目、資源宣告。
2. 每次修訂 append Log 並記錄原值；不可能無痕覆寫。
3. 拒絕修改既有 Log 條目。
4. 與 #12 的範圍界定明確（#12 併入本卡，**待本卡 merge 後才關閉**——此時序請一併裁定）。
5. 回歸測試涵蓋各欄位修訂路徑與 Log 留痕。
6. **請實際重放** #17 於 2026-08-10 的兩次修訂情境（spec 基線更新、Log 排版修復），證明全程無須 `gh issue edit`。R1 只重放了前者，後者當時無路可走；本輪 `--repair-log-layout` 就是為它而生。

### 執行者主動揭露

- R1 的三項 blocking 都是執行者在 R1 派審詞裡自列的質疑點。知道有問題卻先交付、把判斷丟給查核者，是這輪該記下的失分；本輪不再有同類「已知但未修」的項目。
- 自測抓到一個真 bug：Log 行加入 `op` 識別碼後，`_tier_change_logged` 仍比對舊字面格式，偵測器認不出自己寫的紀錄，把真 no-op 誤判成半寫入。已改為逐行、不綁格式的判定。
- 本 repo 無 ruff 設定，`pytest` 即唯一機械閘門。

### 環境紅線與獨立性

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。執行者為 Claude Opus 5@Claude Code。T2 CLI 卡不強制換家族，但本卡動的是唯一寫入通道本身，建議獨立查核者。

無法執行 `wfcli` 時，請依 `templates/handoff-contract.md` §3.1.2 留 `wf-review-receipt:v1` 收據由 PM 轉錄。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5239616135 · 2026-08-10T11:38:57Z

## 派審：R3（取代前一則 R2 派審詞）

⚠️ 審核對象 **`ruan6047/ai-workflow#19`**。CLI 實作卡，有程式碼改動。

### 進駐與身分核對

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1
分支：claude/WF-CLI-CARD-AMEND1
被審 SHA：08e8b1776f0cb9f582f0060a63c6ab1f39e886e7   ← 已非 R2 的 3fc771a
基線：origin/main dbfdb9c85fa92fff81efcc6b01a2a275f6378091
iteration：1
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1
git rev-parse HEAD && git diff --name-only origin/main
```

預期 `08e8b17…` 與五個檔案：`cli/README.md`、`cli/src/wf_cli/card.py`、`cli/src/wf_cli/cli.py`、`cli/src/wf_cli/commands/amend_cmd.py`、`cli/tests/test_amend.py`。

### R2 三項的處置

**R2-01（修復破壞 JSON）** — 反例成立，執行者的「剝掉所有空白後相同」證明**已撤回**：它預先把字面 `\n` 從比較基準刪掉，等於把破壞藏進證明裡。改為範圍限縮——只動 `\n## Log` 起算的尾段，其前**逐位元不變**；Log 之前若也有字面 `\n` 直接拒絕（無法安全判斷是損壞還是 JSON 合法內容）。另加防線：原本可解析的資源宣告，修復後須解析成相同結果。查核者的反例已成為回歸測試。

**R2-02（TOCTOU）** — 推論更正並落地：新增寫入前重讀比對，被他人改動即以**退出碼 6** 中止而不覆寫。同時在 docstring、旗標說明、README 三處明寫這**不是**原子 compare-and-swap，重讀只把窗口從「整條指令執行期間」縮到「重讀與寫入之間」，不宣稱完全防護。

**R2-03（恢復指引不實）** — exit 5 改印可執行的三步驟恢復指令；README 增設 `amend` 專節，含恢復範例、併發界線、窄路修復三道防線，並標明 `--record-unlogged-change` 是操作者宣告而非系統證明。

### 必跑（`self_run` 需附實際輸出）

```bash
cd cli && uv run pytest -q          # 預期 232 passed（185 baseline + 47）
```

### 本輪請特別攻擊這四點

1. **範圍限縮是否真的窮盡了破壞面。** 現行判準：以 `body.find("\\n## Log")` 定位，其前逐位元不變、其前不得含字面 `\n`。請找反例——例如 `\n## Log` 字樣出現在 fenced code block 或 JSON 字串**內部**，導致切點落在錯誤位置；或 body 有多處 `\n## Log`；或 Log 區段內本身就含 JSON／code fence 而被破壞。前兩輪的教訓是執行者對自己的安全論證過度自信，請以反例而非閱讀為主。
2. **`try_parse_block` 防線的涵蓋範圍。** 它只保護資源宣告區塊。Log 區段內若有其他結構化內容（例如某次修訂把 JSON 原值寫進 Log），修復仍可能破壞它而無人偵測。這個殘餘風險可接受嗎？
3. **退出碼 6 的重讀是否真的有效。** 測試以 monkeypatch 模擬第二次讀取時 body 已被改動。請確認真實路徑上 `list_items` 的兩次呼叫確實各自打網路（沒有快取），否則這道檢查是假的。
4. **README 的併發聲明是否誠實且充分。** 執行者宣稱「重讀只縮小窗口、不消除競態」。請判斷這個表述是否足以讓使用者正確評估風險，或仍有誤導。

### 其餘驗收（卡面條文）

1. 涵蓋 spec 基線、驗收條件、驗證項目、資源宣告。
2. 每次修訂 append Log 並記錄完整原值；不可能無痕覆寫。
3. 拒絕修改既有 Log 條目。
4. 與 #12 範圍界定明確（R2 已裁定「#19 merge 後再關 #12」時序恰當）。
5. 回歸測試涵蓋各欄位修訂路徑與 Log 留痕。
6. **請實際重放** #17 於 2026-08-10 的兩次修訂情境（spec 基線更新、Log 排版修復），證明全程無須 `gh issue edit`。R1／R2 都只重放了前者。

### 執行者主動揭露

- R2 兩項 blocking 都是執行者在 R2 派審詞裡主動請查核者攻擊的點，兩個都被打穿。上一輪的反省是「已知問題應修完再送」，本輪的教訓不同：**對自己設計的安全論證過度自信**——「只准動空白」聽起來像不變量，實際上證的是別的東西。本輪的範圍限縮同樣是執行者自己的論證，請以同等力度質疑。
- 本 repo 無 ruff 設定，`pytest` 即唯一機械閘門。

### 環境紅線與獨立性

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。執行者為 Claude Opus 5@Claude Code。T2 CLI 卡不強制換家族，但本卡動的是唯一寫入通道本身，建議獨立查核者。

無法執行 `wfcli` 時，請依 `templates/handoff-contract.md` §3.1.2 留 `wf-review-receipt:v1` 收據由 PM 轉錄。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5239814470 · 2026-08-10T12:00:22Z

## 派審：R4（取代前一則 R3 派審詞）

⚠️ 審核對象 **`ruan6047/ai-workflow#19`**。CLI 實作卡。**本輪先刪後補**：移除 `--repair-log-layout`（−412／+85），再補上備案（+101）。

### 進駐與身分核對

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1
分支：claude/WF-CLI-CARD-AMEND1
被審 SHA：db2100d7e172c2d8ef809018d696e8bfc9ddb9f9   ← 已非 R3 的 08e8b17
基線：origin/main dbfdb9c85fa92fff81efcc6b01a2a275f6378091
iteration：1
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1
git rev-parse HEAD && git diff --name-only origin/main
```

預期 `db2100d…` 與五個檔案：`cli/README.md`、`cli/src/wf_cli/card.py`、`cli/src/wf_cli/cli.py`、`cli/src/wf_cli/commands/amend_cmd.py`、`cli/tests/test_amend.py`。

### 本輪做了什麼：移除 `--repair-log-layout`

R3-01 之後，執行者依需求方要求先自驗，又找到三個查核者未發現的破口（`~~~` 圍籬、四空白／Tab 縮排區塊、行內碼——在 body 剛好沒有真 Log 標題時全數失守，先前僅靠「兩個 `## Log`」那道下游檢查僥倖擋下）。

累計在同一個旗標上五個安全破口，全是同一類錯誤：**拿「聽起來像不變量」的論證當安全保證**。根因是想靠列舉 Markdown 語境判斷「這個 token 是內容還是損壞」，而語境是無界的。

需求方裁決移除而非再次加固。移除範圍：`--repair-log-layout`、`--expect-body-sha256`、`card.py::repair_body_layout` 與相關測試。**`split_at_log` 的 fail-closed 保留不變**——遇到排版損壞就拒絕修訂。

**需求方追加要求：機械修復可以放棄，但必須提供備案。** 因此另補一條出路，設計原則是不重新引入自動改寫（那正是五個破口的來源），改為「可執行的人工程序 ＋ 機械驗證出口」：`amend` 偵測到排版損壞時，除了拒絕，另在 stderr 印出六步程序並帶入實際卡號——取出 body → 人工只改換行 → 以「剝掉空白後逐字相同」比對確認未動非空白內容 → 寫回 → 以 `amend --dry-run` 機械驗證 Log 已可安全定位 → 留言記錄此次繞過。README 收錄完整可貼指令。

關鍵在第 3 步與第 5 步：前者讓「只動空白」由人**逐字驗證**而非由工具**宣稱**——同一條不變量，差別在誰來背書，而工具背書已被證明會失敗五次；後者讓「修好了」有機械判準，不靠目視。

### 必跑（`self_run` 需附實際輸出）

```bash
cd cli && uv run pytest -q          # 預期 225 passed（185 baseline + 40）
cd cli && uv run wfcli amend --help # 確認已無 --repair-log-layout / --expect-body-sha256
```

### 本輪請特別檢視這五點

1. **移除是否乾淨。** 請以 `rg` 全域搜尋 `repair`／`expect_body_sha256`／`repair_body_layout` 等殘留（README 有意保留一段移除理由的敘述，那是刻意的；程式碼與測試應為零）。並確認 `card.py` 沒有孤兒 import（`try_parse_block` 曾為修復而引入）。
2. **備案是否真的可執行。** 請**實際照著 stderr 印出的六步程序走一遍**（可用測試卡），特別是第 3 步的比對指令是否正確可貼、第 5 步的 `--dry-run` 是否真能區分「修好了」與「還沒修好」。若任一步在真實環境跑不通，這個備案就跟原本的「人工處理」一樣空泛。
3. **備案的風險轉移是否誠實。** 它把「只動空白」的驗證責任從工具移到人。請判斷：這是誠實的責任歸屬，還是只是把已知會失敗的檢查換個人做？
4. **切除是否傷到相鄰功能。** 執行者第一次切除時邊界抓錯，把 `amend_spec_baseline` 與 `amend_resource_block` 一併刪掉（`ImportError` 當場炸出，已還原並改用帶斷言的精準邊界）。請確認現行版本這兩個函式與其測試都完整，且 `amend` 的五類欄位修訂全部仍可用。
5. **README 的移除紀錄與備案是否誠實充分。** 它列出五個破口與移除理由，目的是防止日後有人再實作一次。請判斷該敘述是否足夠具體到能達成這個目的。

### 其餘驗收（卡面條文）

1. 涵蓋 spec 基線、驗收條件、驗證項目、資源宣告。
2. 每次修訂 append Log 並記錄完整原值；不可能無痕覆寫。
3. 拒絕修改既有 Log 條目。
4. 與 #12 範圍界定明確（R2 已裁定「#19 merge 後再關 #12」時序恰當）。
5. 回歸測試涵蓋各欄位修訂路徑與 Log 留痕。
6. **驗證第 2 條需重新裁定**：原文要求「以 #17 於 2026-08-10 的兩次實際修訂情境重放，證明全程無須 `gh issue edit`」。spec 基線更新那次可重放（前三輪均已驗證）；**Log 排版修復那次在移除後已無 CLI 自動路徑**，改由備案的人工程序涵蓋（第 5 步仍以 `wfcli` 驗證，不需 `gh issue edit` 以外的手動判斷）。請裁定此驗收條目應視為「以備案方式滿足」、「因設計裁決而部分不適用」，或需求方應正式修訂該條文。

### 執行者主動揭露

- R3 之後的三個破口是執行者自驗發現，非查核者指出；但前五個破口累計顯示執行者對自己的安全論證持續過度自信，本輪的移除決定正是基於此。
- 切除時曾誤刪相鄰的兩個 `amend_` 函式（已還原，並在腳本加入「移除範圍不得含其他 `amend_` 函式」的斷言，第二次即被該斷言擋下）。這與本卡主題同源：憑對結構的假設做整段替換很危險，要有機械檢查而非目視。
- 本 repo 無 ruff 設定，`pytest` 即唯一機械閘門。

### 環境紅線與獨立性

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。執行者為 Claude Opus 5@Claude Code。T2 CLI 卡不強制換家族，但本卡動的是唯一寫入通道本身，建議獨立查核者。

無法執行 `wfcli` 時，請依 `templates/handoff-contract.md` §3.1.2 留 `wf-review-receipt:v1` 收據由 PM 轉錄。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5239896656 · 2026-08-10T12:08:25Z

## 派審：WF-CLI-CARD-AMEND1（**本則取代先前所有派審詞**）

⚠️ 本 Issue 先前的派審詞指向 `72bab2d`／`3fc771a`／`08e8b17`／`db2100d`，**全部過期**。以本則為準。

⚠️ 審核對象 **`ruan6047/ai-workflow#19`**（Issue），CLI 實作卡。

### 進駐與身分核對

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1
分支：claude/WF-CLI-CARD-AMEND1
被審 SHA：ea74c6646f4a737c4d539de812a444de4ee74cc8
基線：origin/main dbfdb9c85fa92fff81efcc6b01a2a275f6378091
iteration：1
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1
git rev-parse HEAD && git diff --name-only origin/main
```

預期 `ea74c66…` 與五個檔案：`cli/README.md`、`cli/src/wf_cli/card.py`、`cli/src/wf_cli/cli.py`、`cli/src/wf_cli/commands/amend_cmd.py`、`cli/tests/test_amend.py`。

### 這張卡在做什麼

`open` 之後卡面就凍住了，`wfcli` 沒有修訂入口。2026-08-10 一天內因此繞過唯一寫入通道四次。本卡新增 `wfcli amend`，涵蓋 **spec 基線／驗收條件／驗證項目／資源宣告／`級別`**。`WF-CLI-TIER-MUTATION1`（#12）併入本卡（R2 已裁定「#19 merge 後再關 #12」時序恰當）。

### 三輪查核後的重大設計轉折

R1–R3 累計八項 finding。其中 `--repair-log-layout`（Log 排版損壞的自動修復）在三輪查核加一次自驗中被找到**五個安全破口**，全是同一類錯誤——拿「聽起來像不變量」的論證當安全保證。**需求方裁決移除該功能，不再加固**。

移除後需求方追加兩項要求，均已落地：

- **「機械不可行可以放棄，但要提供備案」** → 排版損壞時 stderr 印出六步人工程序，含以「剝掉空白後逐字相同」比對確認未動非空白內容，以及用 `amend --dry-run` 機械驗證修好了。關鍵是把「只動空白」的驗證從**工具宣稱**改為**人逐字驗證**——同一條不變量，差別在誰背書，而工具背書已被證明會失敗五次。
- **「機械檢查失效時能否跳提示要求人為或 AI 處理」** → 新增 `--escalate`，在 Issue 留下含 `<!-- wf-amend-blocked:v1 ... -->` 機器標記與完整 runbook 的求助留言。刻意不碰 body（body 已壞，再寫更危險）、不改交付狀態（lifecycle 決定屬 PM）、只對排版損壞生效。

### 必跑（`self_run` 需附實際輸出）

```bash
cd cli && uv run pytest -q          # 預期 229 passed（185 baseline + 44）
cd cli && uv run wfcli amend --help # 確認已無 --repair-log-layout / --expect-body-sha256
```

### 本輪請特別攻擊這五點

1. **備案是否真的可執行。** 請**實際照 stderr 印出的六步程序走一遍**（可用測試卡）：第 3 步的比對指令是否正確可貼、第 5 步的 `--dry-run` 是否真能區分「修好了」與「還沒修好」。任一步在真實環境跑不通，這個備案就跟原本的「人工處理」一樣空泛。
2. **`--escalate` 的界線劃分。** 它不改交付狀態，意味著卡面有留言但看板上該卡仍顯示正常，只有讀 Issue 的人會發現卡住。這個取捨對嗎，還是應該一併轉 `⏸阻塞`？另：重複執行會留下多則相同留言，未去重——是噪音還是「反覆嘗試」的有用證據？
3. **`wf-amend-blocked:v1` 標記是否該納入權威契約。** 它目前只是本指令自訂字串，未像 `wf-review-event:v1` 那樣寫進 `handoff-contract.md`。若未來有工具靠它對帳，是否該比照辦理？（本卡 scope 不含 `templates/`，故未動。）
4. **移除是否乾淨。** 請 `rg` 搜尋 `repair_body_layout`／`expect_body_sha256` 等殘留（README 有意保留一段移除理由的敘述，那是刻意的；程式碼與測試應為零），並確認 `card.py` 無孤兒 import。
5. **切除是否傷到相鄰功能。** 執行者第一次切除時邊界抓錯，把 `amend_spec_baseline` 與 `amend_resource_block` 一併刪掉（`ImportError` 當場炸出，已還原並改用帶斷言的精準邊界）。請確認這兩個函式與其測試完整，且五類欄位修訂全部仍可用。

### 執行者主動揭露（本輪自審發現，非查核者指出）

送審前依需求方要求自審，抓到兩個真 bug，均已修：

- **`--dry-run` 搭配 `--escalate` 會實際送出留言**。body 修訂的例外處理排在 dry-run 分支之前。`--dry-run` 承諾零遠端寫入，不因為「只是留言」而破例。
- **留言寫入失敗時例外逸出**，退出碼從 2 變 1，stack trace 還把 runbook 沖掉——使用者同時失去自動紀錄與人工出路。

更值得記的是：**第一次自審是假的**。探測用 DraftIssue 型別的卡，`_escalate_layout_failure` 在 draft 檢查就提早返回，兩個探測都「通過」卻沒走到留言路徑；換真 Issue 型別重測才浮出來。原本的 escalate 測試也寫成 `if posted: ... else: ...` 兩路都放行，等於測試本身也是假的——已改為強制 Issue 型別的 fixture 並斷言 `len(posted) == 1`。

**請把這件事當成查核重點之一**：本卡累計的失分模式是「執行者對自己的驗證過度自信」，包含驗證本身是否真的驗到。

### 其餘驗收（卡面條文）

1. 涵蓋 spec 基線、驗收條件、驗證項目、資源宣告。
2. 每次修訂 append Log 並記錄**完整原值**（不截斷）；不可能無痕覆寫。
3. 拒絕修改既有 Log 條目。
4. 與 #12 範圍界定明確。
5. 回歸測試涵蓋各欄位修訂路徑與 Log 留痕。
6. **驗證第 2 條需裁定**：原文要求「以 #17 於 2026-08-10 的兩次實際修訂情境重放，證明全程無須 `gh issue edit`」。spec 基線更新那次可重放；**Log 排版修復那次在移除後已無 CLI 自動路徑**，改由備案的人工程序涵蓋（第 5 步仍以 `wfcli` 驗證）。請裁定應視為「以備案方式滿足」、「因設計裁決而部分不適用」，或需求方應正式修訂該條文。

### 環境紅線與獨立性

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。執行者為 Claude Opus 5@Claude Code。T2 CLI 卡不強制換模型家族，但本卡動的是唯一寫入通道本身，建議獨立查核者。

無法執行 `wfcli` 時，請依 `templates/handoff-contract.md` §3.1.2 留 `wf-review-receipt:v1` 收據由 PM 轉錄。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5240026908 · 2026-08-10T12:17:16Z

## 派審：R5（**本則取代先前所有派審詞**）

⚠️ 本 Issue 先前的派審詞指向 `72bab2d`／`3fc771a`／`08e8b17`／`db2100d`／`ea74c66`，**全部過期**。以本則為準。

### 進駐與身分核對

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1
分支：claude/WF-CLI-CARD-AMEND1
被審 SHA：28200c54e7aee4d909d004cbea80b3722aa7296e
基線：origin/main dbfdb9c85fa92fff81efcc6b01a2a275f6378091
iteration：1
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1
git rev-parse HEAD && git diff --name-only origin/main
```

預期 `28200c5…` 與五個檔案：`cli/README.md`、`cli/src/wf_cli/card.py`、`cli/src/wf_cli/cli.py`、`cli/src/wf_cli/commands/amend_cmd.py`、`cli/tests/test_amend.py`。

### R4 兩項的處置

兩項病根相同：**執行者寫了 runbook 卻從沒真的跑過它**。

- **R4-01**（缺 `orig.md` 建立步驟）→ stderr 第 1 步補上 `cp /tmp/body.md /tmp/orig.md`。先前 README 版有 `cp`、stderr 版沒有，兩份不一致。
- **R4-02**（比對式誤判 #17 正確修復）→ 判準由「刪掉全文所有字面 `\n` 再比」改為「**修好的 body 必須恰好等於原文做一次目標替換後的結果**」。舊判準會把 Log 內文合法的字面 `\n` 一併刪除，使備案在它唯一的真實案例上失效。

**治本的部分**：驗證指令抽成 `_LAYOUT_VERIFY_SNIPPET` 單一常數，stderr、README、測試三處共用，且測試以 `subprocess` **實際執行它**。先前 runbook 只是字串，沒有任何東西保證它跑得動——這正是它能同時帶著兩個錯上線的原因。

### 卡面驗收條文已更新（依 R4 裁定）

查核者裁定「驗證第 2 條不能宣稱已滿足」，並建議正式改寫。已用**本卡做出來的 `wfcli amend`** 修訂（`op 62e3a5b6`，原條文完整保留於 Log）：原本一條拆為兩條，第 2 條保留可自動重放的 spec 基線更新，**新增第 3 條**要求以受控人工修復驗證 Log 排版損壞。請確認新條文是否確實可獨立執行驗證。

### 必跑（`self_run` 需附實際輸出）

```bash
cd cli && uv run pytest -q          # 預期 233 passed（185 baseline + 48）
```

並請**照卡面驗收第 3 條實際走一遍**：以 #17 的真實 body 重建損壞 → 依 stderr runbook 六步修復 → 第 3 步應印 `OK` → 額外改一個字應印 `NG` → 第 5 步 `--dry-run` 不再回報排版錯誤。

### 本輪請特別攻擊這四點

1. **新判準是否真的擋得住所有「額外改動」。** 現行判準是 `orig.replace(token, fixed, 1) == new`。請找反例：是否存在某種修改能通過它卻仍是實質竄改？特別注意 `replace(..., 1)` 只替換第一個出現位置——若 body 有多處該 token 會怎樣？
2. **驗證指令的可攜性。** 它是一行 `python3 -c '...'`，內含單引號與 `chr(92)` 等寫法以迴避跳脫。請在你的 shell（非 zsh／bash 亦可）實測貼上執行，確認不會因引號處理而失效。
3. **卡面驗收第 3 條是否可獨立執行。** 它引用「amend 印出的六步 runbook」——這是動態產生的文字。條文依賴一段會變動的輸出，是否構成可稽核的驗收？
4. **自我修訂的獨立性（第二次）。** 執行者用本卡的工具修訂了本卡自己的驗收條文。R1 曾就同類行為（修訂自己的資源宣告）詢問過，本次是依查核者建議所為。請確認這條「執行者改自己的驗收基準」的路徑是否需要額外約束。

### 執行者主動揭露

- R4 的兩項是同一個失分模式的第三次：**驗證本身不是真的驗證**。第一次是 R5 收據缺身分核對、第二次是自審用 DraftIssue 走不到目標路徑、這次是 runbook 從未被執行。本輪的治法是把「被印出來的東西」與「被測試執行的東西」綁成同一個常數。
- 本 repo 無 ruff 設定，`pytest` 即唯一機械閘門。

### 其餘驗收（卡面條文）

1. 涵蓋 spec 基線、驗收條件、驗證項目、資源宣告。
2. 每次修訂 append Log 並記錄**完整原值**（不截斷）；不可能無痕覆寫。
3. 拒絕修改既有 Log 條目。
4. 與 #12 範圍界定明確（R2 已裁定 merge 後再關 #12）。
5. 驗證條文三條，見上。

### 環境紅線與獨立性

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。執行者為 Claude Opus 5@Claude Code。T2 CLI 卡不強制換模型家族，但本卡動的是唯一寫入通道本身，建議獨立查核者。

無法執行 `wfcli` 時，請依 `templates/handoff-contract.md` §3.1.2 留 `wf-review-receipt:v1` 收據由 PM 轉錄。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5240165891 · 2026-08-10T12:25:16Z

## 派審：R6（**本則取代先前所有派審詞**）

⚠️ 先前派審詞指向 `72bab2d`／`3fc771a`／`08e8b17`／`db2100d`／`ea74c66`／`28200c5`，**全部過期**。

### 進駐與身分核對

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1
分支：claude/WF-CLI-CARD-AMEND1
被審 SHA：cc8e20266848cd16214b3f8d821756cb66128d57
基線：origin/main dbfdb9c85fa92fff81efcc6b01a2a275f6378091
iteration：1
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1
git rev-parse HEAD && git diff --name-only origin/main
```

預期 `cc8e202…` 與五個檔案：`cli/README.md`、`cli/src/wf_cli/card.py`、`cli/src/wf_cli/cli.py`、`cli/src/wf_cli/commands/amend_cmd.py`、`cli/tests/test_amend.py`。

### R5-01 的處置

查核者打穿兩處（多 token 只修第一個仍印 OK、code fence 內 token 被誤修後第 7 步假性通過）。**根因不是檢查寫錯，是宣稱寫錯**：執行者把「第一個字串被替換了」當成「那個字串是 Log 標題」的證明。後者需要 Markdown 語意判斷——而那正是前三輪已證明追不完、因此才移除自動修復的東西。移除功能之後，同樣的假設又以另一個形式回來了。

- 第 4 步改印「必要條件通過」並**自帶免責**：明說不是安全證明、無法判斷該標記是否真的是 Log 標題。
- **強制候選 token 恰好一處**，多處直接 NG 並要求人工逐一判斷。
- runbook 由六步擴為八步，新增第 2 步「人工判斷（無法機械化）」承載語意判斷、第 5 步「審閱完整 diff」。
- 第 7 步 `--dry-run` 加註界線：只證明找得到唯一一個 Log 標題，不證明它在對的位置，也不保證別處沒有殘留的字面 `\n`。

### 必跑（`self_run` 需附實際輸出）

```bash
cd cli && uv run pytest -q          # 預期 237 passed（185 baseline + 52）
```

並請照卡面驗收第 3 條實跑：以 #17 真實 body 重建損壞 → 依 stderr 八步走 → 第 4 步印「必要條件通過」→ 額外改字印 NG → 多 token 印 NG。

### 本輪請特別攻擊這三點

1. **現在還有沒有任何隱含的機械安全宣稱。** 這是本輪的核心問題。前五輪的失分全屬同一族——執行者判斷「這樣就安全了」而後被打穿，且移除自動修復後假設仍以新形式復發。請通讀 `_LAYOUT_VERIFY_SNIPPET`、`_LAYOUT_RUNBOOK`、README 的備案節與 `--escalate` 留言全文，找出任何**仍在暗示「照做就安全」**的措辭或結構。執行者宣稱本版沒有，但前五次也都這麼認為。
2. **「候選 token 恰好一處」是否為正確的守門條件。** 它把多 token 情形推給人工，但單一 token 仍可能位於 code fence 內而被誤修——此時第 4 步照樣印「必要條件通過」，只靠第 2 步的人工判斷與第 5 步的 diff 擋。這個責任分配對嗎？或者單一 token 也應該先做 fence 位置檢查？
3. **八步是否已經長到沒人會照做。** 備案的價值取決於實際被執行。若你認為八步過長、實務上會被跳過，請直接說——那比「步驟正確但沒人跑」更值得知道。

### 其餘驗收（卡面條文，驗證條文已依 R4 裁定更新）

1. 涵蓋 spec 基線、驗收條件、驗證項目、資源宣告。
2. 每次修訂 append Log 並記錄**完整原值**（不截斷）；不可能無痕覆寫。
3. 拒絕修改既有 Log 條目。
4. 與 #12 範圍界定明確（merge 後再關 #12）。
5. 驗證三條：cli 測試涵蓋各欄位修訂與 Log 留痕／#17 spec 基線更新情境重放／Log 排版修復以受控人工修復驗證。

### 執行者主動揭露

本卡累計六輪、`--repair-log-layout` 一條線就出了八個 finding，全部同族：**執行者對「這樣就安全了」的判斷不可靠**。本版把語意判斷明確標成「機器做不到、由人負責」，是六輪來第一次沒有隱含機械安全宣稱——但基於前五次也都自認收斂，這個自評不應被採信，請以反例檢驗。

### 環境紅線與獨立性

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。執行者為 Claude Opus 5@Claude Code。建議獨立查核者。

無法執行 `wfcli` 時，請依 `templates/handoff-contract.md` §3.1.2 留 `wf-review-receipt:v1` 收據由 PM 轉錄。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5242997361 · 2026-08-10T16:24:45Z

## 派審：R7（**本則取代先前所有派審詞**）

⚠️ 先前派審詞指向 `72bab2d`／`3fc771a`／`08e8b17`／`db2100d`／`ea74c66`／`28200c5`／`cc8e202`，**全部過期**。

### 進駐與身分核對

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1
分支：claude/WF-CLI-CARD-AMEND1
被審 SHA：0cd30aa7c50b23f0e65256536c89c89594d60e59
基線：origin/main dbfdb9c85fa92fff81efcc6b01a2a275f6378091
iteration：1
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-card-amend1
git rev-parse HEAD && git diff --name-only origin/main
```

預期 `0cd30aa…` 與五個檔案：`cli/README.md`、`cli/src/wf_cli/card.py`、`cli/src/wf_cli/cli.py`、`cli/src/wf_cli/commands/amend_cmd.py`、`cli/tests/test_amend.py`。

### R6 兩項的處置

- **R6-01（卡面步號漂移，blocking）** — 經需求方核可後以 `wfcli amend` 更新驗證第 3 條（`op ed3b259b`，原值完整保留於 Log）：六步→**八步**、驗證指令第 3 步→**第 4 步**、`--dry-run` 第 5 步→**第 7 步**。並補上兩項原本沒寫的要求：**多處候選標記須印 NG**、以及**第 2 步人工語意判斷與第 5 步完整 diff 審閱皆須確認執行**——那兩步是 R5 之後語意判斷的實際承載處，驗收沒提到等於沒驗到。
- **R6-02（README 殘留宣稱）** — 「核心設計是…能機械證明人工修好了」改為「只機械驗證必要條件；語意判斷留給人」，並明說工具能證明的是「只改了那一處」，不是「那一處是對的」。小節標題同步改為「機械驗證必要條件」。

### 需求方追加要求：全文件重掃

需求方要求「多檢查一遍文件有沒其他沒有修改到的地方」。**改用機械對照而非目視**（本卡的教訓正是目視不可靠），八項一致性檢查：runbook 步號連續、README 步號與之一致、卡面規範區步號、驗證指令三處同源、退出碼宣告涵蓋實際 `return`、所有旗標在 README 出現、指令數宣稱。

三項亮紅，兩項是檢查本身寫太粗（**假陽性**）：

- README 多出的 `# 1.` 是退出碼 5 的恢復步驟，獨立編號清單。
- 卡面仍含「六步」只出現在 **Log 歷史行**——append-only 保留原值是正確行為，規範區已全為八步。

**一項是真的**：`--verification`／`--resources`／`--db-scope` 三個旗標從未在 README 示範，已補上範例與「可同時給多個欄位；任一驗證失敗整批不寫」。

### 必跑（`self_run` 需附實際輸出）

```bash
cd cli && uv run pytest -q          # 預期 237 passed（185 baseline + 52）
```

並請照卡面驗收第 3 條（已更新為八步）實跑一次。

### 本輪請特別檢視這三點

1. **卡面與實作是否還有其他未對齊處。** 執行者的八項檢查是自己設計的，涵蓋範圍即是自己想得到的範圍——這正是漂移能連續兩輪逃過的原因。請獨立列出你認為應該檢查的一致性面向，特別是執行者**沒想到要檢查**的（例如 `--escalate` 留言內文與 runbook 是否同源、`AmendError` 訊息與文件用語是否一致、卡面驗收第 1／2 條是否也有漂移）。
2. **假陽性的判定是否正確。** 執行者把兩項紅燈判為假陽性並保留現狀。請獨立確認：卡面 Log 中的「六步」確實只在歷史行、且不會被任何消費者誤讀為現行要求。
3. **R6 判定 `core_pain_resolved: yes` 之後，剩餘工作是否只剩文件對齊。** 若你認為實質功能仍有缺口，請直接指出——連續兩輪只開文件級 finding，可能代表功能面已收斂，也可能代表查核重心偏移了。

### 其餘驗收（卡面條文）

1. 涵蓋 spec 基線、驗收條件、驗證項目、資源宣告。
2. 每次修訂 append Log 並記錄**完整原值**（不截斷）；不可能無痕覆寫。
3. 拒絕修改既有 Log 條目。
4. 與 #12 範圍界定明確（merge 後再關 #12）。
5. 驗證三條（第 3 條已更新為八步版）。

### 執行者主動揭露

- R6-01 是**執行者自己造成的漂移**：R4 之後改了卡面，R5 又把 runbook 由六步改為八步，卡面沒跟上。改卡與改實作是兩個動作，而沒有任何機械檢查綁住它們——本輪的八項對照是事後補的，仍屬人工設計。
- 本卡累計七輪。前五輪的 finding 集中在 `--repair-log-layout` 的安全論證，後兩輪轉為文件與卡面對齊。

### 環境紅線與獨立性

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。執行者為 Claude Opus 5@Claude Code。建議獨立查核者。

無法執行 `wfcli` 時，請依 `templates/handoff-contract.md` §3.1.2 留 `wf-review-receipt:v1` 收據由 PM 轉錄。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5243084413 · 2026-08-10T16:32:57Z

<!-- wf-review-event:v1 card_id=WF-CLI-CARD-AMEND1 source_sha=0cd30aa7c50b23f0e65256536c89c89594d60e59 attempt_id=WF-CLI-CARD-AMEND1-e0-0cd30aa7c50b23f0e65256536c89c89594d60e59 -->
## 查核裁決：APPROVE

- 卡：`WF-CLI-CARD-AMEND1`　attempt_id：`WF-CLI-CARD-AMEND1-e0-0cd30aa7c50b23f0e65256536c89c89594d60e59`
- 查核者：獨立校讀（GitHub author ruan6047 轉貼；模型／工具為自述）　escalation_epoch：0
- source_sha：`0cd30aa7c50b23f0e65256536c89c89594d60e59`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-11T00:32:56+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git diff --name-only origin/main`
  - SHA 為 0cd30aa7c50b23f0e65256536c89c89594d60e59；五個預期檔案；工作區乾淨。
- `cd cli && uv run pytest -q`
  - 237 passed in 1.69s。
- `以 #17 真實 body 重建損壞，執行八步 runbook 第 4 步`
  - 印出『必要條件通過』及『這不是安全證明』；完整 diff 僅含目標 Log 標題換行還原。
- `對重建的 body 額外修改一字後執行第 4 步`
  - 印出 NG：除了那一處之外還動到別的地方。
- `cd cli && uv run wfcli amend WF-REVIEW-EVENT-MARKER-ENFORCE1 ... --dry-run`
  - 第 7 步通過，未回報排版錯誤，且未寫入遠端。

### findings（1，其中 blocking 0）

- **WF-CLI-CARD-AMEND1-R7-01**　severity=minor　blocking=false　class=authoritative-artifact　attribution=executor　root_cause_id=`residual-internal-wording-drift`
  - evidence：cli/src/wf_cli/commands/amend_cmd.py:130-131 的內部註解仍稱『機械驗證修好了』；README 與實際 runbook 已正確限定為『機械驗證必要條件』。
  - disposition：非阻擋；建議同步為『機械驗證必要條件是否通過』，避免後續維護重新引入過度安全宣稱。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5243132362 · 2026-08-10T16:37:10Z

七輪獨立查核後 R7 `APPROVE`（`core_pain_resolved: yes`、零 blocking），已 merge 至 main `5d821e12fd0c71eaababc3dcf7fe408a49cc4d9d`。worktree 與本地／遠端分支均已移除，無殘留。

合併的分支尖端較被核可的 `0cd30aa` 多一個 commit `829ace8`：R7-01 指出的內部註解措辭同步（minor、非阻擋、查核者 disposition 明示建議、純註解行為零改動），依需求方裁決先修再 merge。

`WF-CLI-TIER-MUTATION1`（#12）已併入本卡實作，同步關閉。
