# #133 OPS-PROJECT-ARCHIVE-TERMINAL1 終態卡自動封存：把 archiveProjectV2Item 從條文變成可重跑的機械步驟
- state: open  created: 2026-08-24T12:46:51Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/133
- comments: 4

## Body

- 需求：—　規劃：—
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；單一 GraphQL mutation 加一支冪等腳本；風險在批次與可逆性判斷，不在演算法。）　查核：待指派（建議 主力型；不動 canonical、不動狀態機語意；查核重點是冪等性、可逆性與封存後 wfcli 讀取行為是否改變。）
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：目標 2 可稽核的內容：活卡視圖必須能一眼看出「現在有什麼在跑」，而不是靠人在 188 張裡挑出 61 張。

## 簡介
<!-- card-brief:begin -->
寫一支冪等腳本以 archiveProjectV2Item 把終態卡移出 Project 4 的活卡視圖——2026-08-24 實測 188 個 item 有 127 個是終態（104 🏁完成／23 🛑已停止）、isArchived 全為 false，即 aiwf#130 canonical §0.1 的規則從未被執行過一次，真正的活卡只有 61 張。適用時機：要判「現在有什麼在跑」卻每看三張要跳過兩張時；或要動 cli/src/wf_cli/project.py 的 list_items 讀取路徑時。⛔ 非射程：Discovery 未答「封存後 wfcli 還讀不讀得到那張卡」之前不得批次執行；封存判準須直接 import assign_cmd.TERMINAL_STATUSES 不自行複製字面；維護卡不封存（維護階段屬 aiwf#130 的 S3，今日尚無，須寫成前向相容）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：Project 4 的活卡視圖有 68% 是噪音：2026-08-24 實測 188 個 item 中 127 個是終態（104 個 🏁完成、23 個 🛑已停止）卻仍留在視圖裡，真正的活卡只有 61 張。⇒ 需求方要判「現在有什麼在跑」時，每看三張要跳過兩張，而那正是他逐字表達的「常常超出我掌握」的一個具體成因。⛔ 缺的不是規則——aiwf#130 的 canonical §0.1 已定義「終態卡以 archiveProjectV2Item 移出活卡視圖」且含「⛔ 維護卡不封存」的例外——缺的是機械執行者：今天 188 張的 isArchived 全部為 false，即該規則從未被執行過一次。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/project.py",
    "file:scripts/archive_terminal_items.py",
    "file:cli/tests/test_project_archive.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] ⭐ Discovery 先答一題：**封存後 wfcli 還讀不讀得到那張卡**。今天驗不了——188 張的 isArchived 全為 false，⛔ 沒有已封存樣本。實驗法：挑一張 🛑已停止 的卡封存 → 重跑 project.list_items 與 GraphQL isArchived 查詢 → 記錄它有沒有出現在結果裡 → 立即 unarchive 還原。⛔ 未答此題不得批次執行。
- [ ] 依上題答案決定是否需要調整 project.list_items：若封存後仍在 items 連線內，則 assign 的資源互斥檢查與 doctor 行為不變、無需改碼；若不在，須先確認哪些讀取路徑會失去資料並在本卡處理，⛔ 不得先封存再說。
- [ ] 封存判準為**逐字比對 assign_cmd.TERMINAL_STATUSES**（目前 `🏁完成`、`🛑已停止`），直接 import 該常數，⛔ 不得自行複製字面——複製會與該常數漂移。
- [ ] ⛔ 排除維護卡：canonical §0.1 定義「維護卡不封存」。⚠️ 今日尚無維護階段（屬 aiwf#130 的 S3），故本卡須寫成**前向相容**：以「交付狀態在終態集合內」為封存條件，並在碼與測試中逐字標明維護階段落地後須加上排除條件，⛔ 不得假裝今天已排除。
- [ ] 冪等：同一份輸入重跑第二次不改變任何 item 的 isArchived，且輸出可辨識「本次封存 N 張、已是封存狀態 M 張」。
- [ ] 可逆：提供 unarchive 路徑（unarchiveProjectV2Item）並**實際對至少一張卡跑通一次還原**，⛔ 不得只宣稱可逆。
- [ ] 批次與速率：記錄實跑 127 張時的 GraphQL 呼叫數、耗時與是否遇到 rate limit；若需分批，分批大小須有實測依據，⛔ 不得憑空定。
- [ ] ⭐ 效果可量：執行後重跑本卡核心痛點的量測，活卡視圖 item 數應自 188 降至 61（或執行當下的對應值）。報告須附執行前後兩次量測的原始輸出，⛔ 不接受只寫結論。
- [ ] 回歸：uv lock --check、pytest、replay_escalation_rules、canonical_citation_scan 四項全綠；另跑 wfcli doctor 確認 worktree／孤兒分支／lease 三節的結果與封存前一致。
- [ ] 依 docs/ROADMAP.md §6「開卡時在此確認它服務哪個目標」，於 §3 登記本卡並註明服務目標 2；⚠️ 排進「必要」或「降級 Backlog」由需求方裁定，執行者⛔不得自行決定。

## 驗證

- [ ] Discovery 那題的實驗留痕：封存前後的 isArchived 查詢輸出、list_items 是否仍含該卡、還原後的再次查詢，三段原始輸出全附。
- [ ] 冪等證明：連跑兩次的完整輸出並列，第二次的「本次封存」計數須為 0。
- [ ] 可逆證明：unarchive 實跑一次的輸出，以及該卡 isArchived 回到 false 的查詢結果。
- [ ] ⛔ 執行前後的活卡視圖量測兩份原始輸出（非結論），且兩份的量測指令逐字相同。
- [ ] ⚠️ 未驗清單須依 canonical §6.4.2 的形狀要求：每一項標明驗不了的原因（缺什麼、要等什麼、需要誰），標不出原因者代表驗得了、不得列入。
## Log

- 2026-08-24T20:46:49+08:00 open by —；owner 待指派；iteration 0。
- 2026-08-24T20:48:37+08:00 amend by wf-cli（op 78bed157）→ 驗收條件：原值「[ ] TODO：填入可獨立驗證的條件」→ 新值「⭐ Discovery 先答一題：**封存後 wfcli 還讀不讀得到那張卡**。今天驗不了——188 張的 isArchived 全為 false，⛔ 沒有已封存樣本。實驗法：挑一張 🛑已停止 的卡封存 → 重跑 project.list_items 與 GraphQL isArchived 查詢 → 記錄它有沒有出現在結果裡 → 立即 unarchive 還原。⛔ 未答此題不得批次執行。；依上題答案決定是否需要調整 project.list_items：若封存後仍在 items 連線內，則 assign 的資源互斥檢查與 doctor 行為不變、無需改碼；若不在，須先確認哪些讀取路徑會失去資料並在本卡處理，⛔ 不得先封存再說。；封存判準為**逐字比對 assign_cmd.TERMINAL_STATUSES**（目前 `🏁完成`、`🛑已停止`），直接 import 該常數，⛔ 不得自行複製字面——複製會與該常數漂移。；⛔ 排除維護卡：canonical §0.1 定義「維護卡不封存」。⚠️ 今日尚無維護階段（屬 aiwf#130 的 S3），故本卡須寫成**前向相容**：以「交付狀態在終態集合內」為封存條件，並在碼與測試中逐字標明維護階段落地後須加上排除條件，⛔ 不得假裝今天已排除。；冪等：同一份輸入重跑第二次不改變任何 item 的 isArchived，且輸出可辨識「本次封存 N 張、已是封存狀態 M 張」。；可逆：提供 unarchive 路徑（unarchiveProjectV2Item）並**實際對至少一張卡跑通一次還原**，⛔ 不得只宣稱可逆。；批次與速率：記錄實跑 127 張時的 GraphQL 呼叫數、耗時與是否遇到 rate limit；若需分批，分批大小須有實測依據，⛔ 不得憑空定。；⭐ 效果可量：執行後重跑本卡核心痛點的量測，活卡視圖 item 數應自 188 降至 61（或執行當下的對應值）。報告須附執行前後兩次量測的原始輸出，⛔ 不接受只寫結論。；回歸：uv lock --check、pytest、replay_escalation_rules、canonical_citation_scan 四項全綠；另跑 wfcli doctor 確認 worktree／孤兒分支／lease 三節的結果與封存前一致。；依 docs/ROADMAP.md §6「開卡時在此確認它服務哪個目標」，於 §3 登記本卡並註明服務目標 2；⚠️ 排進「必要」或「降級 Backlog」由需求方裁定，執行者⛔不得自行決定。」；理由 開卡時一併填實驗收與驗證，⛔ 不留 TODO 佔位符——依 aiwf#130 新增的 canonical §6.4.1（驗收條件須於離開規劃前填實），且 aiwf#129 的 R1-002 正是打在該規則尚未寫下來的時候。。
- 2026-08-24T20:48:37+08:00 amend by wf-cli（op 78bed157）→ 驗證：原值「[ ] TODO：填入驗證指令與證據要求」→ 新值「Discovery 那題的實驗留痕：封存前後的 isArchived 查詢輸出、list_items 是否仍含該卡、還原後的再次查詢，三段原始輸出全附。；冪等證明：連跑兩次的完整輸出並列，第二次的「本次封存」計數須為 0。；可逆證明：unarchive 實跑一次的輸出，以及該卡 isArchived 回到 false 的查詢結果。；⛔ 執行前後的活卡視圖量測兩份原始輸出（非結論），且兩份的量測指令逐字相同。；⚠️ 未驗清單須依 canonical §6.4.2 的形狀要求：每一項標明驗不了的原因（缺什麼、要等什麼、需要誰），標不出原因者代表驗得了、不得列入。」；理由 開卡時一併填實驗收與驗證，⛔ 不留 TODO 佔位符——依 aiwf#130 新增的 canonical §6.4.1（驗收條件須於離開規劃前填實），且 aiwf#129 的 R1-002 正是打在該規則尚未寫下來的時候。。
- 2026-08-24T20:53:09+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree ai/opus-5/OPS-PROJECT-ARCHIVE-TERMINAL1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/project-archive-terminal1；交付狀態 🔨執行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-24T22:11:19+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (PM)；iteration 0；SHA cd88270f10d634e1e4f5c12bd6ac6a3e6b89f57f；證據 退回規劃：核心痛點的依據已被推翻（issuecomment-5396410525），須重寫後才可再進 Backlog 排隊。依 canonical §3.1，T2 進 Backlog 的狀態前提是 🧭規劃中。。
- 2026-08-24T22:11:45+08:00 handoff by wf-cli → owner 排隊中：待需求方排程；iteration 0；SHA cd88270f10d634e1e4f5c12bd6ac6a3e6b89f57f；證據 需求方 2026-08-24 裁定降級（issuecomment-5396410525）：核心痛點依據「活卡視圖 68% 是噪音」已被推翻——跨六天版控快照顯示該比例自 56% 單調升到 67% 而「真正在動」始終 0 至 5 張 ⇒ 衡量的是專案活了多久不是缺陷；封存 126 張只把 188 降到 62 而需被看見的是 3 至 11 張 ⇒ 屬檢視與過濾問題，已以零程式碼的新檢視「需要我看的」解決（實測 11／189，未動 View 1、可撤）。⚠️ 降級不是關閉；重啟前須先重寫核心痛點。⚠️ 本卡曾以 project.py 實際擋住 S1 派工。worktree 已移除、本地分支已刪（零 commit）。。
- 2026-08-24T22:16:52+08:00 handoff by wf-cli → owner 待指派；iteration 0；SHA cd88270f10d634e1e4f5c12bd6ac6a3e6b89f57f；證據 owner 自「排隊中：待需求方排程」改為「待指派」。理由：排隊中不在 card.py:237 的佔位前綴集合（待指派／待建立／待認領／—）內，⇒ 降級後的本卡仍參與 assign 的資源互斥比對並實際擋住 WF-CARD-BRIEF-AND-TWO-AXIS-WRITE1 對 file:cli/src/wf_cli/project.py 的派工。⭐ 降級卡不該再持有資源鎖，改用真正的佔位值釋放。⚠️ 這暴露一個形狀：「排隊中：…」被廣泛用作 owner 卻不被判為未認領，本 repo 另有 aiwf#122 與 #128 同樣情形；⛔ 是否收進佔位前綴集合屬另卡射程，本次不改碼。。
- 2026-08-26T21:43:30+08:00 amend by wf-cli（op bf5ca4d9）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:e855e57641889d8caab4cddf7343977682b7a47c4864f3d6a5ff2e2836b4208c (751 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。
- 2026-08-29T15:00:19+08:00 handoff by wf-cli → owner 待指派；iteration 0；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 阻塞登記（來源狀態 📥Backlog）：https://github.com/ruan6047/ai-workflow/issues/133 之阻塞留言。解除條件＝待審清單機制上線。。


## Comment 5396410525 · 2026-08-24T14:10:11Z

## 需求方裁定（2026-08-24）：本卡降級 Backlog

⚠️ **本則由 PM 逐字轉錄需求方的裁定**（同一平台身分，逐字揭露）。

### 依據：本卡的核心痛點建立在一個沒有意義的比例上

本卡開卡時的核心痛點寫「Project 4 的活卡視圖有 68% 是噪音」。⛔ 該依據已於同日被推翻：

**一、比例本身無意義。** 跨六天版控快照（`snapshots/2026-08-19` 至 `2026-08-24`）：

| 日期 | 總 | 終態 | 比例 | 真正在動 |
|---|---|---|---|---|
| 08-19 | 159 | 89 | 56% | 5 |
| 08-22 | 177 | 114 | 64% | 2 |
| 08-24 | 188 | 126 | 67% | 3 |

⇒ 比例**單調上升而「真正在動」不動** ⇒ 它衡量的是專案活了多久，不是任何缺陷；
它會趨近 100%，而那代表做完的事變多。

**二、封存解決的比例太小。** 同一份快照：封存 126 張只把 188 降到 62，而需要被看見的是
3 至 11 張 ⇒ 那是**檢視與過濾**的問題。

**三、⭐ 已由零程式碼的方式解決。** 2026-08-24 於 Project 4 新建檢視「需要我看的」
（`PVTV_lAHOAvJcys4BfXPrzgLaWBo`），filter 為
`-交付狀態:"🏁完成","🛑已停止","💡需求","📥Backlog"`，實測顯示 **11 張／共 189 張**。
⛔ 未動既有的 `View 1`，`deleteProjectV2View` 隨時可撤。⭐ 採**排除法**而非列舉：
新增的狀態值會自動出現，⛔ 不會被靜默隱藏。

### 降級不是關閉

封存本身仍有價值（終態卡長期堆積會讓任何全量查詢變慢、也讓 `list_items` 每次多讀）。
⚠️ 依 `docs/ROADMAP.md` §3 逐字「**降級不是關閉**。它們載有真實 finding 的紀錄，關掉會讓
那些發現消失；降級可逆，關閉不可逆」。

### ⚠️ 一併記錄：本卡曾實際擋住另一張卡

本卡宣告 `file:cli/src/wf_cli/project.py` 且狀態為 `🔨執行中`（已認領）⇒ 依
`assign_cmd` 的互斥檢查會**硬擋** S1（wfcli 寫入端與簡介欄位）的派工。⭐ **這是本專案
資源互斥第一次真的咬到**——先前量測顯示 24 張 OPEN 卡中只有 3 張參與比對、零衝突，
因為未認領的卡不參與。降級後 owner 回到未認領 ⇒ 不再擋。

### ⛔ 本卡的核心痛點需重寫後才可重啟

現行核心痛點的第一句即為已被推翻的 68% 論述。⇒ 日後若重啟本卡，**須先重寫核心痛點**
（可用的方向是終態卡堆積對查詢成本的影響，⚠️ 而該影響**尚未量測**），
⛔ 不得沿用「活卡視圖有 68% 是噪音」。


## Comment 5460928769 · 2026-08-29T06:55:56Z

## 阻塞登記

**狀態**：⏸阻塞。**來源狀態：📥Backlog**（解除時回到此狀態）。

**阻塞原因**：需求方於 2026-08-29 決定，在階段狀態重整（8 階段 × 10 狀態、待審清單、CLI 射程收斂）定案並落地前，暫停所有 ai-workflow 流程卡，避免它們與重構討論互相干擾。

**可證偽的解除條件**：待審清單機制上線（label ＋ issue template ＋ 可見分組）。屆時本卡改列為清單參考項，或依當時前提是否仍成立重新排程。

**本次未做**：核心痛點、驗收條件、射程一律未動。`iteration` 未遞增。`階段` 欄未寫入。本登記僅改交付狀態與 owner。

**已知的射程重疊**（供解除時參考，非本次裁定）：#66／#38 的實質可能由「七份交接文件格式」承接；#128 可能由「待審清單收件條件三·查重留痕」＋`open --from-issue` 承接；#11 的證據紀律已部分寫入 PM 準則但痛點（靠人記得）未消失。⛔ 上述皆未經裁定，解除時須逐張重驗。

**裁定者**：需求方 ruan6047，2026-08-29 本 session 對話中指示「把目前所有 WF 卡片暫停，避免干擾目前重構討論」。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。


## Comment 5492897117 · 2026-09-01T10:59:01Z

量測更新：痛點仍在，且母體變大（2026-09-01，PM 留痕）

本卡痛點的量測基準為 2026-08-24 的「188 個 item／127 個終態／isArchived 全 false」。今日（2026-09-01，相隔 8 天）以 `wf_cli.project.list_items` 與 GraphQL `isArchived` 分頁全查重跑同一量法：

- items 總數 **215**（+27）
- 交付狀態分佈：127 🏁完成／33 🛑已停止／31 💡需求／17 ⏸阻塞／4 📦已合併／3 📥Backlog
- 終態卡（🏁完成＋🛑已停止）＝ **160**（8 天前為 127，+33）
- `isArchived=true` ＝ **0**（全 215 個 item 分頁查完，⛔ 非取樣）

⇒ 本卡痛點⛔ 未緩解，且終態卡以每天約 4 張的速度累積。

**新增的一個具體阻塞事例**：`WF-REDESIGN-W2A`（#219）今日走完結案階段 ④（需求方確認結案報告），第 ⑤ 步「完成＋封存」因本卡尚無機械執行者而**無法完成**——需求方 2026-09-01 裁定該卡停在 🏁完成、⛔ 不單獨封存，理由是單張封存會製造一個未受本卡驗收條件 1（「封存後 wfcli 還讀不讀得到那張卡」的 Discovery）覆蓋的既成樣本。留痕見 #219。

**⚠️ 本卡目前可能推不動**：卡面首行為「需求：—　規劃：—」，需求方欄為空。⛔ PM 不代填（`stage-rules/pm-conduct.md` 不代填條款），此處僅標明供需求方處置。

**PM 未驗**：本卡驗收條件 1 的 Discovery 問題（封存後 `list_items` 是否仍讀得到）今日**未做實驗**——依本卡逐字「⛔ 未答此題不得批次執行」，PM ⛔ 不自行製造已封存樣本。


## Comment 5492995721 · 2026-09-01T11:07:13Z

更正前一則的「可能推不動」（2026-09-01，PM）

前一則留言我寫本卡「目前可能推不動」，措辭過寬。實查碼面後，射程比那句窄，逐項如下（⛔ 不改前一則原文，以本則更正）：

**需求方欄實際卡住的是哪條路徑**：`需求：` 欄的唯一消費者是 `cli/src/wf_cli/commands/amend_cmd.py` 的 `_authorize_by_requester_ruling`——`amend --ruling-url` 會取該裁定留言的 GitHub comment author，**逐字**比對卡面「需求：」欄；取不到 author、URL 指向他卡、或該欄無法解析，一律 **fail-closed**。`assign`／`handoff`／`review` 的碼中查無對該欄的引用。

⇒ 本卡**可以**派工、交接、查核；⛔ 卡住的是「需要引用需求方裁定的修訂」（例如改射程／改驗收時走 `--ruling-url` 授權）。

**補填此欄有沒有 writer**：`wfcli amend` 唯一能寫該欄的旗標是 `--header-requested-by`，而它只在 `--restore-migration-header` 下有效——該路徑逐字限定為「為 **2026-08-04 遷移卡**補回標頭」，且要求取值自「cutover 前一版的原始卡面」。本卡 2026-08-24 建立，⛔ 不屬該母體、⛔ 無前一版可取 ⇒ **對本卡而言無 writer**。

⇒ 若日後真的需要需求方裁定授權的修訂，處置是停卡重開（帶需求方欄），⛔ 不是補填。

**PM 未驗**：`--restore-migration-header` 對非遷移卡是否真的會拒（我讀的是旗標說明與 `--reason` 要求，**未實跑**）；以及 `review` 階段的痛點比對是否另有讀取該欄的路徑（grep 未命中，但⛔ 關鍵字沒命中不等於不存在）。

