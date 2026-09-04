# #60 DEV-CLI-VERB-WIRING1 三張新動詞卡都刻意不碰註冊點，於是沒有人擁有把動詞接上線這件事
- state: open  created: 2026-08-12T11:16:58Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/60
- comments: 2

## Body

- 需求：—　規劃：—
<!-- wf-routing:v1 -->
- 執行：待指派（建議 經濟型；改動是在 commands/__init__.py 的 tuple 加三行並確認 --help 順序；風險低、推理鏈短。但須逐一驗證三個動詞真的可從 CLI 呼叫，不能只看測試綠。）　查核：待指派（建議 主力型；本卡碰的是所有 CLI 入口的共用註冊點，且要判定「插入位置」而非單純 append；查核重點在三個動詞的接線是否各自實際可呼叫、以及既有 9 個動詞的 help 順序是否逐字未變。建議跨家族。）
- Initiative：—　spec 基線：DEV-CLI-VERB-REGISTRY1（#53）已於 2026-08-12 合併（main e1b33d8），註冊清單為 cli/src/wf_cli/commands/__init__.py 的顯式 tuple（元素是模組名字串）。需求方 2026-08-12 裁定開接線卡而非讓某一張新動詞卡擴張寫入集。
- DB：db_scope=none
- 服務的原始目標：讓 #54／#55／#56 交付的三個動詞真的可以從 CLI 呼叫

## 簡介
<!-- card-brief:begin -->
把 #54 resume／#55 merge／#56 epoch-anchor 三個動詞模組登記進 cli/src/wf_cli/commands/__init__.py 的 tuple，逐一裁定插入位置並實跑 --help 與一次最小呼叫，證明它們真的可從 CLI 觸發——測試綠不算數。適用時機：交付了動詞模組卻沒有註冊點、或 wfcli 少了某個應該存在的動詞時；或要查為何接線獨立開卡、而不是讓其中一張動詞卡擴張寫入集時。⛔ 非射程：不修改 #54／#55／#56 交付的任何檔案，模組介面不符時指名而不代修；⚠️ 不得預設 append 到 tuple 尾端——#9 已實證那會改動既有 9 個動詞的 --help 順序。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：WF-CLI-RESUME1（#54）、WF-CLI-MERGE1（#55）、WF-CLI-EPOCH-ANCHOR1（#56）三張卡的資源宣告都刻意排除動詞註冊點，各自只交付模組本體與測試，並在卡面要求交付報告「指名由誰註冊」。但那個被指名的對象不存在——沒有任何一張卡的寫入集包含 commands/__init__.py。照現況跑完會得到三個模組、三份測試、零個可用的動詞。讓其中一張擴張寫入集去收尾，等於把 DEV-CLI-VERB-REGISTRY1（#53）剛消除的序列化重新裝回去。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/__init__.py",
    "file:cli/tests/test_cli_registry.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 把 #54／#55／#56 交付的三個動詞模組登記進 commands/__init__.py 的 tuple。本卡不修改那三張卡交付的任何檔案；若某個模組因介面不符而無法登記，指名而不代修。
- [ ] ⚠️ 不得預設 append 到 tuple 尾端。WF-22-CLI4（#9）已實證這句話比實際契約窄：它的 checkpoint_cmd 原本排在 review_cmd 之後，append 到尾端會把兩個動詞排到 snapshot 之後而改動既有 help 順序，實際須插在 review_cmd 後才能維持 --help 全文逐字相同。本卡須為三個動詞各自裁定位置並說明理由，且證明既有動詞的相對順序未變。
- [ ] 逐一實跑三個新動詞的 --help 與一次最小呼叫，證明它們真的可從 CLI 觸發。測試綠不算數——#53 已實證 eager import 版跑完整套件 658 全綠卻在冷啟動路徑上炸。
- [ ] 本卡開工的前置是 #54／#55／#56 至少一張已合併進 main。未合併的動詞不得先行登記——登記一個不存在的模組會讓 test_registry_matches_command_modules_on_disk 轉紅（#53 的 M3／M4 突變已證實該測試有鑑別力）。

## 驗證

- [ ] cd cli && uv run pytest -q 不得退化（基線自己跑，不要抄卡面數字）。
- [ ] wfcli --help 的既有 9 個動詞順序與登記前逐字比對，附指令輸出。
- [ ] 三個新動詞各自 wfcli <verb> --help 實跑 exit 0，附輸出。
- [ ] 凡寫下「不變／相同／窮舉」須附指令輸出；沒有機械執行者的寫成約定。
## Log

- 2026-08-12T19:16:57+08:00 open by —；owner 待指派；iteration 0。
- 2026-08-26T20:58:19+08:00 amend by wf-cli（op c7ec560f）→ 簡介：原值「（原本沒有）」→ 新值「把 #54 resume／#55 merge／#56 epoch-anchor 三個動詞模組登記進 cli/src/wf_cli/commands/__init__.py 的 tuple，逐一裁定插入位置並實跑 --help 與一次最小呼叫，證明它們真的可從 CLI 觸發——測試綠不算數。適用時機：交付了動詞模組卻沒有註冊點、或 wfcli 少了某個應該存在的動詞時；或要查為何接線獨立開卡、而不是讓其中一張動詞卡擴張寫入集時。⛔ 非射程：不修改 #54／#55／#56 交付的任何檔案，模組介面不符時指名而不代修；⚠️ 不得預設 append 到 tuple 尾端——#9 已實證那會改動既有 9 個動詞的 --help 順序。」（⚠️ 全文：totalCount=0（首寫，平台無前一版））；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。
- 2026-08-29T14:37:32+08:00 handoff by wf-cli → owner —；iteration 0；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 停卡裁定：https://github.com/ruan6047/ai-workflow/issues/60#issuecomment-5460849727 （需求方 2026-08-29 定案「不擴 CLI」，本卡前提被推翻）。


## Comment 5305473064 · 2026-08-16T03:12:38Z

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


## Comment 5460849727 · 2026-08-29T06:36:19Z

## 停卡裁定

**決策**：停止。

**原因**：需求方於 2026-08-29 定案「不應該再擴 CLI，太大了」，並將 CLI 射程收斂為「提供資料／確認執行者是否有填／GitHub 機械操作」，明確排除新增流程動詞。本卡的核心痛點建立在「這個生命週期步驟缺一個 wfcli 動詞」之上，該前提已被推翻。

**可證偽的復活條件**：下列任一成立時重開本卡 —— (a) 2026-08-29 的階段狀態重整未落地；(b)「不擴 CLI」的定案被需求方推翻。

**裁定者**：需求方 ruan6047，於本 session 對話中逐項確認（先 7 張，經 PM 更正射程後為 5 張：#54 #55 #56 #60 #115）。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

**未被本裁定涵蓋**：`WF-REVIEW-SERVICE-GOAL1`（#137）與 `DEV-RELEASE-STATUS-DONE1`（#84）原在候選內，經複查前提仍部分成立，已撤出、維持 Backlog。

