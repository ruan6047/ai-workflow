# #55 WF-CLI-MERGE1 wfcli merge 動詞與守衛：合併是唯一沒有動詞的生命週期步驟
- state: open  created: 2026-08-12T09:40:43Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/55
- comments: 2

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code PM
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；須裁定合併的前置守衛集合並與 canonical 的 PR 分類對齊；踩在不可逆步驟上，推理鏈中等。）　查核：待指派（建議 主力型；紅線：合併是不可逆且直接改動 main，守衛漏一項的後果是壞碼進 main；須跨家族。）
- Initiative：—　spec 基線：自 WF-ORCHESTRATION-RECONCILE1（#16）§9 衍生卡切出。該清單自 2026-08-11 提出後從未開卡；需求方 2026-08-12 盤點後裁定「先開卡、#16 續審排後面」，判準是清單被執行才是 #16 的價值，而清單躺著沒做正是當日兩個代價實例（main 轉紅、API 配額耗盡於 handoff 中途）的成因。 #16 §9 衍生卡 E：§2.1 merge 列、§6.3 sign-off、§6.4 PR 事件契約。無相依。
- DB：db_scope=none
- 服務的原始目標：讓合併這個不可逆步驟有與其他生命週期步驟同等的守衛與留痕

## 簡介
<!-- card-brief:begin -->
把 merge 這個生命週期裡唯一沒有動詞的步驟做成 wfcli 動詞：裁定前置守衛集合（至少須涵蓋「在合併後的結果上跑測試」而非只驗文字衝突與分支自身測試）、與 canonical 的 B1／B2／T0–T1 分類逐字對齊、並裁定後置狀態是否改用 📦已合併。**適用時機**：要合併卡而只有「協調者記得」在把關時；或要查 2026-08-12 連續三合致 main 轉紅（644 passed, 14 errors）的處置依據時。⛔ 非射程：CI 側歸 DEV-AIWF-MINIMAL-CI1（aiwf#48），其 rulesets 為空、今天不擋任何 merge；動詞註冊不在寫入集（DEV-CLI-VERB-REGISTRY1／aiwf#53）；不得靜默覆蓋 AI_WORKFLOW.md 既有的 PR 分類。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：合併是生命週期裡唯一沒有動詞的步驟——open／assign／amend／handoff／review／deploy-* 都有 wfcli 動詞與事件留痕，只有 merge 靠人跑 gh pr merge。後果在 2026-08-12 實現：PM 連續合併三張卡，每次只驗文字衝突與分支自身測試、**從未測合併後的結果**，導致 main 被弄紅（644 passed, 14 errors）。沒有動詞就沒有守衛，沒有守衛就只剩「協調者記得」。

DEV-AIWF-MINIMAL-CI1（#48）從 CI 側處理同一個問題，但其查核指出 CI 今天**不擋任何 merge**（rulesets 為空），提供的是強制產生的證據而非強制執行的閘門。本卡從動詞側補另一半。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/merge_cmd.py",
    "file:cli/tests/test_merge.py",
    "file:docs/WF_CLI_MERGE1.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 裁定合併的前置守衛集合，至少須涵蓋 2026-08-12 事故的形狀：**在合併後的結果上跑測試**，而非只驗文字衝突與分支自身測試。守衛清單須說明每一項擋的是什麼、以及擋不住什麼。
- [ ] 與 canonical AI_WORKFLOW.md 的 B1／B2／T0–T1 分類**逐字對齊**，不得靜默覆蓋。哪些卡須走 PR、哪些可直推，以既有分類為準。
- [ ] 合併後置狀態的裁定：#16 §9 衍生卡 G 提出 merge 後置應改為 📦已合併（該狀態值已存在於 FIELD_SPECS）。本卡須裁定是否採用，採用則須說明與既有 ✅通過／🏁完成 的關係。
- [ ] ⚠️ **動詞註冊不在本卡寫入集。** 每個新動詞都要在共用註冊點登記，而該點正由 DEV-CLI-VERB-REGISTRY1（#53）重構為顯式 tuple。若三張新動詞卡各自宣告該檔會再度互相序列化，故本卡**只交付模組本體與其測試，動詞未被註冊即無法從 CLI 呼叫**。這是刻意的：交付報告須明列「本動詞尚未接線」並指名由誰註冊，不得為了看起來完整而擴張宣告。

## 驗證

- [ ] 守衛集合須以 2026-08-12 的真實事故重放驗證：取當時的 base 與 head，證明本守衛會擋下該合併。只證明「守衛會跑」不算。
- [ ] pytest 不得退化（基線自己跑）。破壞性驗證只能在拋棄式臨時 repo 內做。
- [ ] 凡寫下「會擋下」須指出執行者所在的檔與行；沒有機械執行者的寫成約定。
## Log

- 2026-08-12T17:40:42+08:00 open by Claude Opus 5@Claude Code PM；owner 待指派；iteration 0。
- 2026-08-26T22:06:10+08:00 amend by wf-cli（op 719bffb2）→ 簡介：原值「（原本沒有）」→ 新值「把 merge 這個生命週期裡唯一沒有動詞的步驟做成 wfcli 動詞：裁定前置守衛集合（至少須涵蓋「在合併後的結果上跑測試」而非只驗文字衝突與分支自身測試）、與 canonical 的 B1／B2／T0–T1 分類逐字對齊、並裁定後置狀態是否改用 📦已合併。**適用時機**：要合併卡而只有「協調者記得」在把關時；或要查 2026-08-12 連續三合致 main 轉紅（644 passed, 14 errors）的處置依據時。⛔ 非射程：CI 側歸 DEV-AIWF-MINIMAL-CI1（aiwf#48），其 rulesets 為空、今天不擋任何 merge；動詞註冊不在寫入集（DEV-CLI-VERB-REGISTRY1／aiwf#53）；不得靜默覆蓋 AI_WORKFLOW.md 既有的 PR 分類。」（⚠️ 全文：totalCount=0（首寫，平台無前一版））；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。
- 2026-08-29T14:36:56+08:00 handoff by wf-cli → owner —；iteration 0；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 停卡裁定：https://github.com/ruan6047/ai-workflow/issues/55#issuecomment-5460849469 （需求方 2026-08-29 定案「不擴 CLI」，本卡前提被推翻）。


## Comment 5305472926 · 2026-08-16T03:12:35Z

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


## Comment 5460849469 · 2026-08-29T06:36:16Z

## 停卡裁定

**決策**：停止。

**原因**：需求方於 2026-08-29 定案「不應該再擴 CLI，太大了」，並將 CLI 射程收斂為「提供資料／確認執行者是否有填／GitHub 機械操作」，明確排除新增流程動詞。本卡的核心痛點建立在「這個生命週期步驟缺一個 wfcli 動詞」之上，該前提已被推翻。

**可證偽的復活條件**：下列任一成立時重開本卡 —— (a) 2026-08-29 的階段狀態重整未落地；(b)「不擴 CLI」的定案被需求方推翻。

**裁定者**：需求方 ruan6047，於本 session 對話中逐項確認（先 7 張，經 PM 更正射程後為 5 張：#54 #55 #56 #60 #115）。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

**未被本裁定涵蓋**：`WF-REVIEW-SERVICE-GOAL1`（#137）與 `DEV-RELEASE-STATUS-DONE1`（#84）原在候選內，經複查前提仍部分成立，已撤出、維持 Backlog。

