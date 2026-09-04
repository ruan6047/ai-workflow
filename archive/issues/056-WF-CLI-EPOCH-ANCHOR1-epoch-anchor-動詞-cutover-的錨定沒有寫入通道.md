# #56 WF-CLI-EPOCH-ANCHOR1 epoch-anchor 動詞：cutover 的錨定沒有寫入通道
- state: open  created: 2026-08-12T09:42:13Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/56
- comments: 2

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code PM
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；須設計 quiescent 前置檢查與三種在途狀態的拒收，且該動詞是 one-shot、錯了不可重來；推理鏈中等。）　查核：待指派（建議 主力型；紅線：one-shot 且指派 state_version，寫錯無法重來；須跨家族。）
- Initiative：—　spec 基線：自 WF-ORCHESTRATION-RECONCILE1（#16）§9 衍生卡切出。該清單自 2026-08-11 提出後從未開卡；需求方 2026-08-12 盤點後裁定「先開卡、#16 續審排後面」，判準是清單被執行才是 #16 的價值。 #16 §9 衍生卡 K：§10.2、§10.3 第 4 步；含 quiescent 前置檢查與三種在途狀態拒收。相依 #23（已併入 main）。
- DB：db_scope=none
- 服務的原始目標：讓 cutover 這個逐卡 one-shot 的錨定有可稽核的寫入通道

## 簡介
<!-- card-brief:begin -->
設計並實作 epoch-anchor 動詞——cutover 的錨定動作，逐卡 one-shot、指派 state_version=1，含 quiescent 前置檢查與三種在途狀態的拒收——並裁定它與 migration-baseline 是同一機制的兩個名字還是兩個機制。**適用時機**：要動 cutover 或 state_version 錨定，而該機制今天只存在於 issue 正文、不受版控時；或 WF-CONTROL-PLANE-TYPE-REGISTRY1（aiwf#42）的 type 登記被「來源不可稽核」擋住時。⛔ 非射程：動詞註冊不在寫入集——共用註冊點由 DEV-CLI-VERB-REGISTRY1（aiwf#53）重構，本卡只交付模組本體與測試，未接線即無法從 CLI 呼叫；不補 doctor 的 contract-baseline 判定（該分類軸已於 aiwf#38 移除）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：epoch-anchor 是 cutover 機制的錨定動作——逐卡 one-shot、指派 state_version = 1，用來劃出「此後的事件受新契約管轄」的界線。今天它**沒有寫入通道**：本體只存在於 issue #16 的正文（OPEN、設計中），而 issue body 可改且不受版控。

WF-CONTROL-PLANE-TYPE-REGISTRY1（#42）的執行者因此拒絕把 epoch-anchor 登記進 control-plane 的 type 列舉，理由是「登記它會讓 main 指向一個不可稽核的來源」——**該理由成立，而本卡就是要消除它**。

同時 WF-DISPATCH-PRECHECK1（#38）本輪查核發現：doctor 提及 contract-baseline **0 次**，故查核者今天連「有沒有 cutover」都無法機械判定。cutover 相關的分類軸因此在該卡被整個移除。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/epoch_anchor_cmd.py",
    "file:cli/tests/test_epoch_anchor.py",
    "file:docs/WF_CLI_EPOCH_ANCHOR1.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 設計並實作 epoch-anchor 動詞，含 quiescent 前置檢查與**三種在途狀態的拒收**（#16 §10.3 第 4 步已列，須逐條對照而非自訂）。one-shot 的機械保證須說明其作用域——單一 Issue 內、跨卡、還是全 Project。
- [ ] 裁定 epoch-anchor 與 migration-baseline 的關係。兩者都被描述為「逐卡 one-shot、指派 state_version = 1」（MIGRATION.md 與 WF_EVENT_IDEMPOTENCY1.md），**是同一機制兩個名字還是兩個機制，文本判不出來**——#42 的執行者因此拒絕單獨登記其中一個（「等於替另一個判死」）。本卡須裁定並使該裁定可稽核。
- [ ] 交付後須使 epoch-anchor 成為受版控的可稽核來源，讓 #42 的登記阻塞解除。交付報告須指名該解除的條件是否已滿足。
- [ ] ⚠️ **動詞註冊不在本卡寫入集。** 共用註冊點正由 DEV-CLI-VERB-REGISTRY1（#53）重構；本卡只交付模組本體與測試，**動詞未被註冊即無法從 CLI 呼叫**。交付報告須明列「本動詞尚未接線」並指名由誰註冊，不得為了看起來完整而擴張宣告。

## 驗證

- [ ] one-shot 保證須以構造反例驗證：同一標的第二次呼叫必須被拒，且拒絕理由可機械判讀。
- [ ] 三種在途狀態的拒收各附紅→綠證據。
- [ ] pytest 不得退化（基線自己跑）。凡寫下「不可重來／必被拒」須指出執行者所在的檔與行與作用域邊界。
## Log

- 2026-08-12T17:42:12+08:00 open by Claude Opus 5@Claude Code PM；owner 待指派；iteration 0。
- 2026-08-26T22:05:30+08:00 amend by wf-cli（op 63632619）→ 簡介：原值「（原本沒有）」→ 新值「設計並實作 epoch-anchor 動詞——cutover 的錨定動作，逐卡 one-shot、指派 state_version=1，含 quiescent 前置檢查與三種在途狀態的拒收——並裁定它與 migration-baseline 是同一機制的兩個名字還是兩個機制。**適用時機**：要動 cutover 或 state_version 錨定，而該機制今天只存在於 issue 正文、不受版控時；或 WF-CONTROL-PLANE-TYPE-REGISTRY1（aiwf#42）的 type 登記被「來源不可稽核」擋住時。⛔ 非射程：動詞註冊不在寫入集——共用註冊點由 DEV-CLI-VERB-REGISTRY1（aiwf#53）重構，本卡只交付模組本體與測試，未接線即無法從 CLI 呼叫；不補 doctor 的 contract-baseline 判定（該分類軸已於 aiwf#38 移除）。」（⚠️ 全文：totalCount=0（首寫，平台無前一版））；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。
- 2026-08-29T14:37:14+08:00 handoff by wf-cli → owner —；iteration 0；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 停卡裁定：https://github.com/ruan6047/ai-workflow/issues/56#issuecomment-5460849598 （需求方 2026-08-29 定案「不擴 CLI」，本卡前提被推翻）。


## Comment 5305472995 · 2026-08-16T03:12:37Z

## 需求方裁定：本組四張整組不做，觸發條件明示（2026-08-16）

`#54 CLI-RESUME1`／`#55 CLI-MERGE1`／`#56 CLI-EPOCH-ANCHOR1`／`#60 DEV-CLI-VERB-WIRING1` 於 2026-08-16 由需求方裁定**整組不做**。本則同時貼於四張卡，任一張都能單獨讀懂。

### 為什麼是整組

`#53` 為消除序列化把動詞註冊點獨立出來，代價是**每個新動詞卡都不含接線**，而接線卡（`#60`）以「至少一張已合併」為前提。**四張互相扣住，單獨做任何一張產出為零。**

`ROADMAP §3.6` 批二已這樣分組（「單獨做任何一張都划不來」）。

### ⭐ 但這一組今天比 ROADMAP 寫的時候小，而 ROADMAP 沒回頭改

| 卡 | 原痛點 | 2026-08-16 實況 |
|---|---|---|
| `#55` | 未在合併後結果上測 → main 轉紅 | ⭐ **已被 repo ruleset 關閉**。`gh api` 實測：`id=20768920`、`enforcement=active`、`strict=true`（強制分支先追平 base）、`bypass_actors=0`、required check `tests`、`~DEFAULT_BRANCH`。**殘餘只剩 merge 事件留痕**（`merge` 在型別列舉內但無 writer） |
| `#56` | cutover 錨定沒有寫入通道 | **半邊已關**：`contract-baseline` 已上線（`checkpoint_cmd.py:118`）。`WF_EVENT_IDEMPOTENCY1.md:51` 已裁定 epoch-anchor（序號劃界）≠ contract-baseline（寫入守衛劃界）。**殘餘只剩 epoch-anchor vs migration-baseline 的裁定**；`state_version` 在 `cli/src` 命中 **0** |
| `#54` | resume 不存在 | 不變。`resume_cmd.py` 不存在，handoff 首寫順序未改 |
| `#60` | 接線 | 不變，且前置未成立。驗證條「既有 9 個動詞」已過期——今為 **10 模組／11 動詞**（`checkpoint_cmd` 註冊兩個），該模組於 `87ccdbc`（08-13 07:10）進註冊表，**晚於本卡建立**（08-12 19:16） |

⚠️ **`ROADMAP.md:133-137` 自己記了 ruleset 這件事，但 `§3.6` 批二仍把 `#55` 列為待做——同一份文件內未對帳。** 這是 `#89 WF-BASELINE-UPSTREAM-TRIGGER1` 要治的那個病的又一個實例。

### 判準：沒有任何已實現後果

與同批其他卡對照——`#62` 已實現 10 筆事件／8 張卡、`#31` 的互斥檢查對 21 張 OPEN 卡整組 fail-open。**本組四張今天沒有任何人受害**：`state_version` 零消費、merge 留痕沒有讀者、resume 沒有實例、接線的前置不成立。

依 `ROADMAP §5`「**不得因為 finding 存在就開卡。finding 是觀察，不是任務。**」——它們已經是卡了，最誠實的處置是**標清楚觸發條件然後不碰**。

### 觸發條件（逐張）

| 卡 | 觸發條件 | 誰會發現 |
|---|---|---|
| `#56` | `state_version` 出現第一個消費者 | ⭐ **`#88` 的 doc↔code 對帳器**——`state_version` 零命中會被它報出來。這是本組唯一有自動觸發器的一張 |
| `#55` | 有人需要從 merge 事件回推歷史，而發現 `merge` 型別沒有 writer | ⚠️ **靠人注意到** |
| `#54` | 中斷的 handoff 實際發生且造成損害 | ⚠️ **靠人注意到** |
| `#60` | `#54`／`#55`／`#56` 任一落地 | 機械可判（模組存在與否） |

⚠️ **必須誠實講的一點**：把觸發條件寫在卡面上，**對 `#55` 與 `#54` 而言接近於沒寫**——沒有人會逐張翻 Backlog。它們的觸發器是「人注意到」，而本專案已多次證明那不算機制。

**這是這個裁定的已知弱點，不是被忽略的地方。** 若日後 `#88` 的對帳器能擴到「型別列舉中無 writer 的項目」，`#55` 就會取得自動觸發器；那時再回頭。

### 本裁定不改變的事

四張**皆維持 OPEN 且維持 `📥Backlog`**。降級不是關閉——它們載有真實 finding 的紀錄。⚠️ 但與 2026-08-12 那批降級不同：**這四張從未達到終態**，故本次是合法降級而非誤傷（對照 `#35`／`#37`／`#41` 於 2026-08-16 的還原）。


## Comment 5460849598 · 2026-08-29T06:36:18Z

## 停卡裁定

**決策**：停止。

**原因**：需求方於 2026-08-29 定案「不應該再擴 CLI，太大了」，並將 CLI 射程收斂為「提供資料／確認執行者是否有填／GitHub 機械操作」，明確排除新增流程動詞。本卡的核心痛點建立在「這個生命週期步驟缺一個 wfcli 動詞」之上，該前提已被推翻。

**可證偽的復活條件**：下列任一成立時重開本卡 —— (a) 2026-08-29 的階段狀態重整未落地；(b)「不擴 CLI」的定案被需求方推翻。

**裁定者**：需求方 ruan6047，於本 session 對話中逐項確認（先 7 張，經 PM 更正射程後為 5 張：#54 #55 #56 #60 #115）。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

**未被本裁定涵蓋**：`WF-REVIEW-SERVICE-GOAL1`（#137）與 `DEV-RELEASE-STATUS-DONE1`（#84）原在候選內，經複查前提仍部分成立，已撤出、維持 Backlog。

