# #115 WF-CLI-REVIEW-CORRECTION1 review-correction 動詞：查核者事後翻案在契約裡有定義，在工具裡沒有通道
- state: open  created: 2026-08-19T17:24:59Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/115
- comments: 3

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；契約已完整規定行為（review-escalation.md §2／§5、control-plane-contract.md §21、AI_WORKFLOW.md:104／:141），實作是把既有 review 事件寫入路徑分支出一個不消耗 attempt 額度、不回寫舊事件的 append 通道；難點在 replay 語意（追加 correction 後完整 replay 必須恢復通過）與三個 gate 不得互鎖，不在實作量。）　查核：待指派（建議 主力型；查核判準已由契約固定：追加 correction 後 replay 必須恢復通過、不得回寫舊 event、不得因 append-only 保留衝突事件而永久失效。查核者照契約條文逐條對即可。）
- Initiative：—　spec 基線：templates/review-escalation.md §2／§5＋templates/control-plane-contract.md:21＋AI_WORKFLOW.md:104／:141 現行版本；觸發實例 cpbl-analytics#152 issuecomment-5345595923
- DB：db_scope=none
- 服務的原始目標：查核者事後翻案要能寫進狀態面，而不是只能留在人讀的留言裡

## 簡介
<!-- card-brief:begin -->
實作 review-correction 動詞——契約完整規定、工具十一個動詞裡卻不存在的那一個，讓查核者事後翻案寫得進狀態面：不回寫舊 event、追加合法 correction 後完整 replay 須恢復通過、不自行消耗或退還 escalation 額度。**適用時機**：查核者收回自己的 APPROVE 而狀態面卡在一個已被收回的 ✅通過時；或同一 source_sha 想換人重審被去重閘門（attempt_id 不含查核者）拒絕時。⛔ 非射程：不自創語意，行為一律依 templates/review-escalation.md §2／§5 與 control-plane-contract.md 既有條文；不得只加動詞而不接註冊點——DEV-CLI-VERB-WIRING1（aiwf#60）已點名該根因，wfcli --help 須列得出它。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：canonical 完整規定了 review-correction：control-plane-contract.md:21 把它列進 type 列舉；review-escalation.md:44 明寫「若事後翻案，以 review-correction 追加新 disposition，不回寫舊 event」；:46 要求 adapter 在同一 finding_id 的分類／歸屬衝突時標為待裁決並「要求下一筆相關 lifecycle event 為 Coordinator／需求方的 review-correction」；AI_WORKFLOW.md:141 明寫它仍可閉合 finding。⚠️ 但 wfcli 十一個動詞裡沒有它，全 repo 唯一提及是 cli/src/wf_cli/validation.py:406 的一句**拒絕訊息**：「跨 attempt 的事後降級屬 review-correction，不是本指令的射程」——工具知道有這個機制、把使用者指向它，然後那個動詞不存在。實際撞上：2026-08-20 cpbl-analytics#152 的跨家族查核者自我更正，指出核心驗收要求它親手重放變異注入而它沒做，明言「我上一版的 APPROVE 不應原樣成立」。PM 嘗試以同一 source_sha 寫入 REQUEST_CHANGES 被去重閘門拒絕（attempt_id 只由 card+epoch+sha 組成，不含查核者，故換人重審同一 SHA 也不可表達）；唯一能碰 epoch 的 checkpoint 要求 --unique-attempt-count >= 3 而該卡只有 1。**結果是狀態面停在一個查核者已收回的 ✅通過，而沒有任何工具路徑能表達收回。**

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/review.py",
    "file:cli/src/wf_cli/cli.py",
    "file:cli/tests/test_review_correction.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] ⚠️ **不得只加動詞而不接註冊點**。DEV-CLI-VERB-WIRING1（#60）已點名根因：「三張新動詞卡都刻意不碰註冊點，於是沒有人擁有把動詞接上線這件事」——本卡若重蹈，等於再產一個規格有、工具沒有的動詞。驗收須包含：`wfcli --help` 列得出它、`wfcli review-correction --help` 可用、且有測試釘住註冊點。
- [ ] 行為依契約，不得自創語意：追加 correction **不回寫舊 event**；⭐ **追加合法 correction 後完整 replay 必須恢復通過**，不得因 append-only 歷史中保留衝突事件而永久失效，也不得依事件或陣列順序覆寫（review-escalation.md:46）。
- [ ] ⚠️ 三個 gate 不得互相鎖死（review-marker-clearance／review-correction／escalation-checkpoint）：replay 必須允許依序追加，不得要求下一筆事件同時滿足兩種 gate。此為契約明文，須有測試。
- [ ] 額度語意：review-correction 不得自行消耗或退還 escalation attempt 額度；它可用同一 finding_id 帶回 resolved／withdrawn（review-escalation.md:44）。⚠️ adapter 須先更新實際 open set 再判斷下一個可計數 attempt。
- [ ] ⭐ 以 cpbl-analytics#152 的實際情境為回放樣本：同一 source_sha 已有一則 APPROVE，查核者事後收回並改判 REQUEST_CHANGES（finding severity major／finding_class governance／attribution reviewer）。修完後該情境必須可寫入且 replay 通過。若做不到，照實說明卡在哪一條契約。

## 驗證

- [ ] 變異檢驗：在未實作前跑上述 #152 回放樣本 → 必須失敗（拒絕寫入）；實作後 → 通過。**兩個方向都要**，artifact 由指令輸出產生。⚠️ 不得只證明「實作後會過」。
- [ ] 註冊點測試：證明動詞真的接上線（`wfcli --help` 命中該子指令名、子指令可被呼叫），且該測試在移除註冊時會紅。
- [ ] 既有 cli 測試不得失效或被排除；貼實際末行。
## Log

- 2026-08-20T01:24:58+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-20T01:26:03+08:00 amend by wf-cli（op f4646d62）→ 驗收條件：原值「[ ] ⚠️ **不得只加動詞而不接註冊點**。DEV-CLI-VERB-WIRING1（#60）已點名根因：「三張新動詞卡都刻意不碰註冊點，於是沒有人擁有把動詞接上線這件事」——本卡若重蹈，等於再產一個規格有、工具沒有的動詞。驗收須包含： 列得出它、 可用、且有測試釘住註冊點。；[ ] 行為依契約，不得自創語意：追加 correction **不回寫舊 event**；⭐ **追加合法 correction 後完整 replay 必須恢復通過**，不得因 append-only 歷史中保留衝突事件而永久失效，也不得依事件或陣列順序覆寫（review-escalation.md:46）。；[ ] ⚠️ 三個 gate 不得互相鎖死（review-marker-clearance／review-correction／escalation-checkpoint）：replay 必須允許依序追加，不得要求下一筆事件同時滿足兩種 gate。此為契約明文，須有測試。；[ ] 額度語意：review-correction 不得自行消耗或退還 escalation attempt 額度；它可用同一 finding_id 帶回 resolved／withdrawn（review-escalation.md:44）。⚠️ adapter 須先更新實際 open set 再判斷下一個可計數 attempt。；[ ] ⭐ 以 cpbl-analytics#152 的實際情境為回放樣本：同一 source_sha 已有一則 APPROVE，查核者事後收回並改判 REQUEST_CHANGES（finding severity major／finding_class governance／attribution reviewer）。修完後該情境必須可寫入且 replay 通過。若做不到，照實說明卡在哪一條契約。」→ 新值「⚠️ **不得只加動詞而不接註冊點**。DEV-CLI-VERB-WIRING1（#60）已點名根因：「三張新動詞卡都刻意不碰註冊點，於是沒有人擁有把動詞接上線這件事」——本卡若重蹈，等於再產一個規格有、工具沒有的動詞。驗收須包含：`wfcli --help` 列得出它、`wfcli review-correction --help` 可用、且有測試釘住註冊點。；行為依契約，不得自創語意：追加 correction **不回寫舊 event**；⭐ **追加合法 correction 後完整 replay 必須恢復通過**，不得因 append-only 歷史中保留衝突事件而永久失效，也不得依事件或陣列順序覆寫（review-escalation.md:46）。；⚠️ 三個 gate 不得互相鎖死（review-marker-clearance／review-correction／escalation-checkpoint）：replay 必須允許依序追加，不得要求下一筆事件同時滿足兩種 gate。此為契約明文，須有測試。；額度語意：review-correction 不得自行消耗或退還 escalation attempt 額度；它可用同一 finding_id 帶回 resolved／withdrawn（review-escalation.md:44）。⚠️ adapter 須先更新實際 open set 再判斷下一個可計數 attempt。；⭐ 以 cpbl-analytics#152 的實際情境為回放樣本：同一 source_sha 已有一則 APPROVE，查核者事後收回並改判 REQUEST_CHANGES（finding severity major／finding_class governance／attribution reviewer）。修完後該情境必須可寫入且 replay 通過。若做不到，照實說明卡在哪一條契約。」；理由 修復開卡時被 shell 吃掉的三處反引號內容：PM 在 zsh 雙引號內使用反引號，被當成命令替換執行（輸出可見 command not found: wfcli ×3），導致驗收第 1 條與驗證第 2 條的指令名整段消失。本次以檔案傳參重寫，內容為原意。⚠️ 據實記錄此為 PM 的引號使用錯誤，非工具缺陷。。
- 2026-08-20T01:26:03+08:00 amend by wf-cli（op f4646d62）→ 驗證：原值「[ ] 變異檢驗：在未實作前跑上述 #152 回放樣本 → 必須失敗（拒絕寫入）；實作後 → 通過。**兩個方向都要**，artifact 由指令輸出產生。⚠️ 不得只證明「實作後會過」。；[ ] 註冊點測試：證明動詞真的接上線（ 命中、子指令可呼叫），且該測試在移除註冊時會紅。；[ ] 既有 cli 測試不得失效或被排除；貼實際末行。」→ 新值「變異檢驗：在未實作前跑上述 #152 回放樣本 → 必須失敗（拒絕寫入）；實作後 → 通過。**兩個方向都要**，artifact 由指令輸出產生。⚠️ 不得只證明「實作後會過」。；註冊點測試：證明動詞真的接上線（`wfcli --help` 命中該子指令名、子指令可被呼叫），且該測試在移除註冊時會紅。；既有 cli 測試不得失效或被排除；貼實際末行。」；理由 修復開卡時被 shell 吃掉的三處反引號內容：PM 在 zsh 雙引號內使用反引號，被當成命令替換執行（輸出可見 command not found: wfcli ×3），導致驗收第 1 條與驗證第 2 條的指令名整段消失。本次以檔案傳參重寫，內容為原意。⚠️ 據實記錄此為 PM 的引號使用錯誤，非工具缺陷。。
- 2026-08-26T22:07:26+08:00 amend by wf-cli（op 653869d3）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:45ec871748d8804f3dd63af623578371f58c521165263aa6588ad555ccd49ec8 (744 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。
- 2026-08-29T14:37:50+08:00 handoff by wf-cli → owner —；iteration 0；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 停卡裁定：https://github.com/ruan6047/ai-workflow/issues/115#issuecomment-5460849836 （需求方 2026-08-29 定案「不擴 CLI」，本卡前提被推翻）。


## Comment 5345743602 · 2026-08-19T17:32:27Z

## ⚠️ 派工前三問查證結果：本卡阻塞於 `#30`，卡面「只缺 CLI 入口」的框架是錯的

依 `docs/AI_WORKFLOW.md`〈派工前三問〉，PM 在 `assign` 前查證第 3 題。

**Q1 解法形狀？** 在 `wfcli` 加一個 `review-correction` 子指令，追加 correction 事件、不回寫舊 event、不消耗 attempt 額度，並接上註冊點。

**Q2 哪個假設錯了會整個不同？** 「`review-correction` 只缺 CLI 入口，replay／adapter 層已經認得這個型別」。若錯，工作量從「加一個子指令」變成別的東西。

**Q3 查證過還是猜的？** 開卡時是**猜的**。現已查證，**假設為假**。

### 查證結果

`cli/src/wf_cli/validation.py:668` 的 `check_attempt_not_duplicated` docstring 自述其存在理由：

> 必須擋在**寫入前**：`doctor.py:409-415` 對重複 `attempt_id` 判 `marker_quarantined`，而該隔離**沒有解除表示法（歸 #30）**，寫下去就是製造一個今天解不開的狀態。

⚠️ **`review-correction` 的本質就是在同一 attempt 上追加第二則事件**（`review-escalation.md:44`：「追加新 disposition，不回寫舊 event」）。而那正好會觸發上述無解除表示法的 `marker_quarantined`。

**先做動詞只會把卡片推進一個今天解不開的狀態，比現況更糟。**

### 因此

本卡阻塞於 **`#30 WF-MARKER-SCOPE-CLEARANCE1`**（「受管轄判準收窄為宣告行 ＋ **clearance 的留言平面表示法與 writer**」）。`#30` 提供 clearance 表示法之後，本卡才有安全的落地路徑。

⚠️ 卡面核心痛點段寫的「wfcli 十一個動詞裡沒有它」**仍然為真**，但那不是唯一的缺口，也不是最上游的缺口。**上游是隔離無法解除。** 卡面未修改，以本則留言記錄依賴關係與框架更正。

### 順帶：這是〈派工前三問〉第二次擋下錯誤框架

第一次是 `cpbl-analytics#153 DEV-COMPLETION-CONDITION-GUARD1`（Q3 答「猜的」→ 停在待派）。本次 Q3 查證後直接推翻 Q2 的假設。⭐ 兩次都發生在規則寫入 canon 的同一天（`c56e870`／`79879b7`），記錄於此以便日後檢核該規則是否持續咬合。

by Claude Opus 5@Claude Code (PM)


## Comment 5345827709 · 2026-08-19T17:40:28Z

## 已知延伸：部署面也需要同型的 correction（需求方 2026-08-20 裁定列管）

本卡處理的是 **review 面**「查核者事後翻案無表示法」。同一天發現**部署面有完全同型的缺口**，需求方裁定一併列管於此，避免遺忘。

### 部署面的實例

`cpbl-analytics#126 DAILY-MIXED-DAY-UX1` 的 Project 欄位 `部署狀態 = ✅已部署`，**但該卡從未部署**（碼在 main，生產站台需主站 submodule bump 才生效，該動作未執行）。全板 162 張卡只有它一張是這個值，且卡面 Log **無任何 deployment event**——該值是繞過 `wfcli` 寫入的。

兩個動詞都無法更正：

```
deploy-declare --decision needs-deploy
  → 拒絕：僅允許 —不適用 → ⏸未部署；目前部署狀態='✅已部署'
deploy-state --to 🚀待部署
  → 拒絕：非法部署轉換 '✅已部署' → '🚀待部署'；此狀態只允許下一步 '🧪驗證中'
```

### 為什麼是同型而不是同一件事

⚠️ **部署狀態機只准往前，設計上是對的**——該欄位記的是世界上發生過什麼；真部署了又出事，誠實紀錄是「已部署 → 回滾」。**缺的不是回退，是「更正一筆假紀錄」**，而那與 review 面「查核者收回自己的裁決」是同一個形狀：**append-only 的狀態面只實作了前進，沒實作追加更正。**

### 對本卡的意涵（不擴張射程）

⚠️ **本卡不要順手把部署面一起做。** 建議在設計 `review-correction` 時，把「correction 事件的通用形狀」與「review 專屬語意」分開，使部署面日後能沿用同一個機制而非另造一套。**若做不到一般化，照實說明為什麼**——那也是有用的結論，代表兩者確實需要各自的動詞。

實際是否開部署面的卡，待本卡做出形狀後再由需求方裁定。

by Claude Opus 5@Claude Code (PM)


## Comment 5460849836 · 2026-08-29T06:36:21Z

## 停卡裁定

**決策**：停止。

**原因**：需求方於 2026-08-29 定案「不應該再擴 CLI，太大了」，並將 CLI 射程收斂為「提供資料／確認執行者是否有填／GitHub 機械操作」，明確排除新增流程動詞。本卡的核心痛點建立在「這個生命週期步驟缺一個 wfcli 動詞」之上，該前提已被推翻。

**可證偽的復活條件**：下列任一成立時重開本卡 —— (a) 2026-08-29 的階段狀態重整未落地；(b)「不擴 CLI」的定案被需求方推翻。

**裁定者**：需求方 ruan6047，於本 session 對話中逐項確認（先 7 張，經 PM 更正射程後為 5 張：#54 #55 #56 #60 #115）。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

**未被本裁定涵蓋**：`WF-REVIEW-SERVICE-GOAL1`（#137）與 `DEV-RELEASE-STATUS-DONE1`（#84）原在候選內，經複查前提仍部分成立，已撤出、維持 Backlog。

