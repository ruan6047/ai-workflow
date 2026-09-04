# #54 WF-CLI-RESUME1 首寫自描述改造與 wfcli resume：限流或中斷後沒有可恢復狀態
- state: open  created: 2026-08-12T09:40:13Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/54
- comments: 3

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code PM
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；須改造既有承接動詞的首寫順序使其自描述，並設計純讀 GitHub 的恢復；踩在狀態面寫入路徑上，推理鏈中等偏長。）　查核：待指派（建議 主力型；紅線：改的是狀態面首寫順序，錯了會在中斷時留下不可辨識的半完成寫入；須跨家族。）
- Initiative：—　spec 基線：自 WF-ORCHESTRATION-RECONCILE1（#16）§9 衍生卡切出。該清單自 2026-08-11 提出後從未開卡；需求方 2026-08-12 盤點後裁定「先開卡、#16 續審排後面」，判準是清單被執行才是 #16 的價值，而清單躺著沒做正是當日兩個代價實例（main 轉紅、API 配額耗盡於 handoff 中途）的成因。 #16 §9 衍生卡 B：§4.2–§4.4；handoff／assign 首寫重構；deploy-* 先稽核；恢復純讀 GitHub。相依 #23（已併入 main）。
- DB：db_scope=none
- 服務的原始目標：讓 GitHub 限流或中斷之後，狀態面能被純讀 GitHub 重建而不需要人去猜寫到哪

## 簡介
<!-- card-brief:begin -->
改造 handoff 使首寫自描述（第一個遠端寫入即帶足以辨識「這是誰、為了什麼、寫到哪」的載荷），並實作純讀 GitHub 的 resume，讓限流或中斷後的狀態面可機械重建而不必靠人猜寫到哪。**適用時機**：wfcli 寫到一半中斷（GraphQL 配額耗盡、HTTP 403 rate limit）而狀態面停在不確定位置時；或要查「首寫為何不能是 owner 欄」的判準時。⛔ 非射程：assign_cmd.py 已依需求方裁定移入 WF-WORKTREE-REPO-OWNERSHIP1（aiwf#57）寫入集，本卡不得逕行宣告；動詞註冊不在寫入集（DEV-CLI-VERB-REGISTRY1／aiwf#53）；本機不得成為第二狀態面。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：#16 的核心痛點逐字寫著「GitHub 限流或中斷後沒有可恢復狀態，導致卡片／看板／main 長期漂移」。2026-08-12 該情境**實際發生**：PM 在一次 handoff 寫到一半時 GraphQL 配額耗盡（該 session 已用 4919／5000），指令中途失敗，狀態面停在不確定的位置。當時是靠人重試補上的。

而 #23 已判定 handoff 的**首寫不自描述**：其效果順序是 owner 欄 → 交付狀態 → 最後交接 → iteration → Issue body Log，**首寫是 owner 欄位、非載荷可攜**，故從事件流上認不出是誰寫的、寫到哪。中斷後沒有任何機械手段能重建。

本卡要讓承接動詞的首寫自描述，並提供純讀 GitHub 的 resume。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/handoff_cmd.py",
    "file:cli/src/wf_cli/commands/resume_cmd.py",
    "file:cli/tests/test_resume.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 改造 handoff 與 assign 使**首寫自描述**——第一個遠端寫入必須帶足以辨識「這是誰、為了什麼、寫到哪」的載荷。#23 於已併入 main 的交付中已釘出判準，須逐條對照而非自訂。
- [ ] 設計並實作 resume：**純讀 GitHub**，本機不得成為第二狀態面。中斷後重跑須收斂到同一結果，且須能分辨「已寫入」與「未寫入」而非重寫。
- [ ] 以真實中斷情境驗證，不得只有合成 fixture。至少涵蓋：首寫成功但後續失敗、首寫失敗、以及配額耗盡（HTTP 403 rate limit）三種。
- [ ] ⚠️ **動詞註冊不在本卡寫入集。** 每個新動詞都要在共用註冊點登記，而該點正由 DEV-CLI-VERB-REGISTRY1（#53）重構為顯式 tuple。若三張新動詞卡各自宣告該檔會再度互相序列化，故本卡**只交付模組本體與其測試，動詞未被註冊即無法從 CLI 呼叫**。這是刻意的：交付報告須明列「本動詞尚未接線」並指名由誰註冊，不得為了看起來完整而擴張宣告。

## 驗證

- [ ] pytest 不得退化（基線自己跑）。三種中斷情境各附紅→綠證據。
- [ ] 證明本機未成為第二狀態面：列出 resume 讀取的全部來源，逐一確認皆為 GitHub。
- [ ] 凡寫下「可恢復／不會重寫／收斂」須指出執行者所在的檔與行與作用域邊界；沒有機械執行者的寫成約定。
## Log

- 2026-08-12T17:40:11+08:00 open by Claude Opus 5@Claude Code PM；owner 待指派；iteration 0。
- 2026-08-12T20:11:33+08:00 amend by wf-cli（op dc04bcd5）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/commands/handoff_cmd.py", "file:cli/src/wf_cli/commands/assign_cmd.py", "file:cli/src/wf_cli/commands/resume_cmd.py", "file:cli/tests/test_resume.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/commands/handoff_cmd.py、file:cli/src/wf_cli/commands/resume_cmd.py、file:cli/tests/test_resume.py」；理由 需求方 2026-08-12 裁定（#57 issuecomment-5266614483）：cli/src/wf_cli/commands/assign_cmd.py 移入 WF-WORKTREE-REPO-OWNERSHIP1（#57）寫入集，本卡一併撤下該檔宣告。理由採納 #57 執行者的論證——本卡驗收條全是首寫自描述與 resume，跨 repo 歸屬閘門塞進來是範圍外擴張，依 §6.1 第 1 條本卡執行者正確做法是寫報告回祕書而非順手做；留著宣告只會讓這件事變成沒有任何一張卡的驗收條在管。互斥不成立的依據是 assign_cmd.py:118-124 與其模組 docstring 逐字裁定「未認領的卡其資源宣告不保留資源」，而本卡現為 owner 待指派。⚠️ 本卡日後若確實需要改 assign 的首寫順序，須與 #57 協調而非逕行宣告。。
- 2026-08-26T22:06:47+08:00 amend by wf-cli（op cb85ba5c）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:007bf327100cb163dc5d7acb698d34f1baa77d3612bac3c20e5b4212c95dddba (678 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。
- 2026-08-29T14:36:40+08:00 handoff by wf-cli → owner —；iteration 0；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 停卡裁定：https://github.com/ruan6047/ai-workflow/issues/54#issuecomment-5460849402 （需求方 2026-08-29 定案「不擴 CLI」，本卡前提被推翻）。


## Comment 5305472871 · 2026-08-16T03:12:34Z

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


## Comment 5399813721 · 2026-08-24T18:49:28Z

## 同一事故的第二個實例（2026-08-25，來自 aiwf#134 的執行過程）

⚠️ **⛔ 只補實例，不改卡面、不動排程。** 本卡仍在 📥Backlog（需求方 2026-08-12／13 裁定降級）。

### 事故

`aiwf#134` 送 R5 時的 `wfcli handoff` **跑了三次才成功**：

1. **GitHub 504 Gateway Timeout**，打在 `gh project item-edit` 中間 ⇒ 卡面落入**半寫入**
2. 重跑時 **GraphQL 配額耗盡**（剩 4／5000）
3. 配額重置後第三次成功並修復

**半寫入的實測狀態**（第一次失敗後唯讀核對）：

| 欄位 | 值 | 判讀 |
|---|---|---|
| `owner` | `跨家族查核（待指派）` | ✅ 已寫入 |
| `交付狀態` | `🔨執行中` | ⛔ **沒跟上** |
| `最後交接` | 舊值 | ⛔ 沒跟上 |
| Issue body Log | **無該筆** | ⛔ 沒寫 |

⭐ **與本卡核心痛點逐字記載的 2026-08-12 事故形狀完全相同**：
「PM 在一次 handoff 寫到一半時 GraphQL 配額耗盡…指令中途失敗，狀態面停在不確定的位置。
**當時是靠人重試補上的**。」⇒ 本次也是靠人重試補上的。

⚠️ 而本卡逐字指出的成因在本次同樣成立：
「handoff 的效果順序是 **owner 欄 → 交付狀態 → 最後交接 → iteration → Issue body Log**，
**首寫是 owner 欄位、非載荷可攜**，故從事件流上認不出是誰寫的、寫到哪。」

⇒ 本次半寫入的**唯一**辨識方式是人工比對 owner 與交付狀態不一致；⛔ 沒有任何機械手段
會告訴你「有一筆 handoff 寫到一半」。

### ⚠️ 一個新的觀察：`wfcli` 是唯一寫入通道 ⇒ 它自己會製造看板失真

canonical §4.3 逐字「**唯一寫入通道＝祕書 CLI**…繞過它的狀態寫入即違規」。
⇒ 那使本缺陷的性質不只是「不方便」——**唯一被允許的寫入路徑本身會產生不一致狀態**。

⚠️ `aiwf#65 DEV-STATE-FACE-DRIFT-GUARD1`（CLOSED）偵測得到該不一致（Log 最後一筆推導出的
狀態 vs Project 欄位），⛔ 但**偵測不等於防止**，且本次 Log 根本沒寫入 ⇒ 該偵測器在這個
失敗模式下**無從比對**——它需要 Log 有那一筆才能推導。

### ⛔ 一併留痕：跨家族查核者判「需另開卡」，而本卡已存在

`aiwf#134` 的 R5 查核者逐字：「這是需要另卡處理的真正控制平面原子性缺陷」。
⚠️ 他沒有指向本卡——⭐ 因為**他看不到其他卡**（無 `wfcli`、無 Project 讀取權、
看不到其他卡），而那正是 `aiwf#130` 核心痛點第三段記載的結構限制。
⇒ ⛔ **PM 未依該 disposition 開新卡**，改補在此。


## Comment 5460849402 · 2026-08-29T06:36:15Z

## 停卡裁定

**決策**：停止。

**原因**：需求方於 2026-08-29 定案「不應該再擴 CLI，太大了」，並將 CLI 射程收斂為「提供資料／確認執行者是否有填／GitHub 機械操作」，明確排除新增流程動詞。本卡的核心痛點建立在「這個生命週期步驟缺一個 wfcli 動詞」之上，該前提已被推翻。

**可證偽的復活條件**：下列任一成立時重開本卡 —— (a) 2026-08-29 的階段狀態重整未落地；(b)「不擴 CLI」的定案被需求方推翻。

**裁定者**：需求方 ruan6047，於本 session 對話中逐項確認（先 7 張，經 PM 更正射程後為 5 張：#54 #55 #56 #60 #115）。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

**未被本裁定涵蓋**：`WF-REVIEW-SERVICE-GOAL1`（#137）與 `DEV-RELEASE-STATUS-DONE1`（#84）原在候選內，經複查前提仍部分成立，已撤出、維持 Backlog。
