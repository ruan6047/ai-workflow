# #13 WF-25-REVIEW-WRITE-CHANNEL1 跨家族查核者的裁決缺乏寫入通道，使「已查核」與「未查核」在狀態面上無法區分
- state: closed  created: 2026-08-08T15:26:37Z  closed: 2026-08-11T12:40:31Z
- url: https://github.com/ruan6047/ai-workflow/issues/13
- comments: 3

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
- 執行：待指派　查核：待指派
- Initiative：—　spec 基線：2026-08-08 #111/#112/#113 三張卡的實例；ai-workflow#12 為同族的欄位更正缺口
- DB：db_scope=none
- 服務的原始目標：查核是否發生必須在狀態面上可觀測，不能依賴人記得轉貼

## 簡介
<!-- card-brief:begin -->
跨家族查核者（GitHub Copilot 等工具內的模型）沒有 wfcli 這個唯一寫入通道，其裁決除非有人手動轉貼再逐字轉錄否則對狀態面完全不可見——做了查核與沒做查核在系統上長得一模一樣。**適用時機**：要派跨家族查核、或要判斷「PR 頁面 0 reviews」是不是等於查核未發生時。⛔ 非射程：不得把結論寫成「請大家記得轉貼」；開卡後欄位不可改的同族缺口屬 `aiwf#12`。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：wfcli 是狀態面唯一寫入通道，但實際執行查核的跨家族查核者（GitHub Copilot 等工具內的模型）沒有該通道。其裁決除非有人手動轉貼給 PM 再逐字轉錄，否則對狀態面完全不可見。2026-08-08 當日 #111/#112/#113 三張卡的查核全部發生過、全部未留痕；PM 甚至據此把「PR 頁面 0 reviews」誤讀為「查核未發生」並寫進兩張卡的 handoff evidence（已撤回）。也就是說：做了查核與沒做查核，在系統上長得一模一樣，而錯誤方向是把已查核誤判為未查核、或反之

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:docs/WF-25-REVIEW-WRITE-CHANNEL1.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 先判定問題形狀再談解法：列出目前所有實際在用的查核者及其可用的寫入能力（能不能跑 wfcli、能不能在 GitHub 上留言、能不能開 PR review），artifact 由實測產生而非推測
- [ ] 提出至少兩個候選方案並比較，不得只給一個：例如(a)查核者取得 wfcli 憑證(b)查核者以固定格式在 PR/Issue 留言、由 CI 或 wfcli 轉譯為 review 事件(c)PM 轉錄升為明文流程步驟並在 handoff 契約中要求註明轉錄來源。判準至少含：漏轉錄時的失效方向、是否需要跨工具憑證、以及查核者身分是否可被偽造
- [ ] 無論選哪案，都必須讓「查核已發生但未留痕」這個狀態可被 doctor 偵測出來——否則問題只是換位置
- [ ] 不得把結論寫成「請大家記得轉貼」：靠紀律的方案必須明講其失效模式與偵測手段，否則視為未解決

## 驗證

- [ ] 以 2026-08-08 的 #111/#112/#113 三筆真實案例回放所選方案，說明若當時已有此機制，各自會如何留痕
- [ ] wfcli 既有測試不得退步
## Log

- 2026-08-08T23:26:36+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-08T23:28:02+08:00 assign by wf-cli → owner GPT-5@Codex；分支worktree ai/gpt-5-codex/WF-25-REVIEW-WRITE-CHANNEL1 @ /Users/ruanruan/Dev/cpbl-analytics/.claude/worktrees/wf25-review-write-channel1-execution；交付狀態 🚧進行中。
- 2026-08-11T20:14:31+08:00 amend by wf-cli（op 1fa667aa）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/wfcli", "file:docs/handoff-contract.md", "file:templates/dispatch-package.md" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:docs/WF-25-REVIEW-WRITE-CHANNEL1.md」；理由 資源宣告有兩個不存在的路徑（file:cli/wfcli 實際為 cli/src/wf_cli/；file:docs/handoff-contract.md 實際在 templates/），且 file:templates/dispatch-package.md 的佔用已持續三天並與 #20 的實際寫入重疊。本卡自 2026-08-08 assign 後零事件、產出卻已在 main（97c0cfa），此為 PM 事實更正：宣告收斂為該卡實際交付的文件，釋放不該被佔用的共用範本。
- 2026-08-11T20:29:41+08:00 handoff by wf-cli → owner 跨家族查核（待需求方指派）；iteration 0；SHA 7451b72ba7679893043950d71bad9642665e25da；證據 事後補查核（需求方 2026-08-11 裁定）。本卡自 2026-08-08 assign 後零 lifecycle 事件，但交付物 docs/WF-25-REVIEW-WRITE-CHANNEL1.md 已於 97c0cfa 進入 main，其後另被 7c003b3 與 424c969 修改。被審對象為該文件在 origin/main 現況，非任何分支。資源宣告已由 PM 更正（op 1fa667aa），釋出兩個不存在路徑與被誤佔的 templates/dispatch-package.md。
- 2026-08-11T20:39:06+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 跨家族查核（需求方於對話中轉貼原文；查核者聲明受唯讀紅線限制未留 receipt marker，來源不可驗證）；core_pain_resolved no；self_run 5 項；findings 4 項（blocking 2）；attempt WF-25-REVIEW-WRITE-CHANNEL1-e0-7451b72ba7679893043950d71bad9642665e25da。
- 2026-08-11T20:39:39+08:00 handoff by wf-cli → owner ruan6047（需求方）；iteration 0；SHA 7451b72ba7679893043950d71bad9642665e25da；證據 需求方 2026-08-11 裁定停止。決策：不修正、不重新補查核、不回退 main。原因：(1) 事後補查核判定 REQUEST_CHANGES，核心建議（B 案：查核者留收據）未在實務落地——本 session 幾乎每輪退回 C 案純 PM 轉錄，故文件第 1 節的能力盤點與第 3/4 節的機制描述皆為未落地的假設；(2) canonical 第 5 節明定事後查核是違規補救、不得視同已通過正常閘門，本卡自 2026-08-08 assign 後零 review 事件而產出已在 main（97c0cfa），doctor 對該 SHA 回 unobservable；(3) 兩項程序瑕疵為不可逆歷史違規（跨 repo worktree 註冊、資源宣告含不存在路徑並錯佔 templates/dispatch-package.md），不得事後偽造註冊。交付物 docs/WF-25-REVIEW-WRITE-CHANNEL1.md 留在 main 不動，但自此不得被引用為已核可的權威描述。
- 2026-08-26T14:19:42+08:00 amend by wf-cli（op f5295404）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:f5c990bdac50b0d0ad4adc4cba811dd9c71b0628517737a8be516fe98b52048a (485 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第二批（20 張純隨機）：依 canonical §6.3 回填簡介；文字經 A5 守衛（分行字元＋1012B 上限）預先拒收檢查。


## Comment 5253177220 · 2026-08-11T12:30:41Z

## 派審：WF-25-REVIEW-WRITE-CHANNEL1（**事後補查核**）

審核對象 **`ruan6047/ai-workflow#13`**。⚠️ 不是 `cpbl-analytics#13`。

**本輪性質與其他卡不同：這是事後補查核，且第一要務是判定文件是否已過期。**

```
被審對象：docs/WF-25-REVIEW-WRITE-CHANNEL1.md 在 origin/main 的現況
被審 SHA：7451b72ba7679893043950d71bad9642665e25da（＝目前 main）
分支：無（產出早已在 main，本卡從未有執行分支）
iteration：0
```

```bash
cd /Users/ruanruan/Dev/ai-workflow && git fetch origin && git log --oneline origin/main -1
cat docs/WF-25-REVIEW-WRITE-CHANNEL1.md
git log --oneline --date=short --format="%h %ad %s" -- docs/WF-25-REVIEW-WRITE-CHANNEL1.md
```

### 為什麼是事後補查核

本卡 2026-08-08 `assign` 給 GPT-5@Codex 之後**零 lifecycle 事件**——無 handoff、無 review、無 release。但交付物**早已進入 main**：

| commit | 日期 | 說明 |
|---|---|---|
| `97c0cfa` | 08-08 | 首次加入該文件（`Implemented-by: GPT-5@Codex`，即卡上登記的執行者） |
| `7c003b3` | 08-09 | **由別張卡修改** |
| `424c969` | 08-11 | **由 #20 修改**（其 R1-002 指出該檔三處宣稱已過期） |

**產出在 main 上、卡從未推進、且已被兩張別的卡改過。** 諷刺的是，本卡的核心痛點正是「查核是否發生必須在狀態面上可觀測」——而它自己就是一個「已交付但狀態面上查不到查核」的實例。

### 一、第一要務：**判定文件是否已過期**（需求方指定）

該文件是 2026-08-08 對「當時 `wfcli` 能力」與「當時 `doctor` 行為」的盤點。**此後 #15／#17／#19／#20 皆已 merge**，能力面與行為面都變了。請逐項判定文件的宣稱在**今天**是否仍成立：

1. **§1 的能力盤點表**（`GPT-5@Codex` 已實測 `--validate-only`／`Claude@GitHub Copilot` 未能實測）——**今天還是這樣嗎？** 本 session 已有多輪查核者**明確聲明未執行 `wfcli`、未留 receipt**，該表是否需要更新？
2. **§3 的 `doctor` 五態表**（`recorded`／`half_written`／`marker_quarantined`／`receipt_untranscribed`／`unobservable`）——文件註明「本檔原記三種，#17 與 #20 各增一種」。**五態是今天的正確數字嗎？**
3. **§3 的 `wfcli doctor` 呼叫範例**——`--owner`／`--project` 自 #20 起必填。範例是否已同步？
4. **§4 的三案回放**（#111／#112／#113）與 **§5 的實作與驗證**——`audit_review_channel()` 的描述是否仍與 `cli/src/wf_cli/doctor.py` 現況相符？

> **這一項不是形式檢查。** 本 repo 反覆出現「文件內嵌的可執行宣稱在改動後開始說謊而沒人重跑」——#20 的 R1-002 就是抓到這份文件的三處。**請實際跑它記載的指令，不要只讀。**

### 二、卡面四條驗收（`gh issue view 13 --repo ruan6047/ai-workflow --json body -q .body`）

1. 先判定問題形狀再談解法：列出所有實際在用的查核者及其寫入能力，**artifact 由實測產生而非推測**；
2. 提出至少兩個候選方案並比較，判準含漏轉錄的失效方向、是否需跨工具憑證、身分是否可偽造；
3. **無論選哪案，「查核已發生但未留痕」必須可被 `doctor` 偵測**——否則問題只是換位置；
4. **不得把結論寫成「請大家記得轉貼」**：靠紀律的方案必須明講失效模式與偵測手段，否則視為未解決。

**請特別驗第 4 條**：文件選了 B 案（查核者留收據、PM 轉錄）並保留 C 案（純 PM 轉錄）為 fallback。**而本 session 的實況是幾乎每一輪都走 C 案**——查核者聲明不寫 Issue，PM 轉錄並標「來源不可驗證」。**這是否等於文件的建議在實務上沒有生效？若是，第 3、4 條是否仍算滿足？**

### 三、程序面的三個瑕疵，請一併裁定

1. **繞過查核閘門**：產出進了 main，狀態面上零 review 事件。`doctor --review-channel` 對本卡會回 `unobservable`。**這是否構成「不得補救即通過」的情形？**
2. **跨 repo 註冊**：卡面登記的 worktree 是 `/Users/ruanruan/Dev/**cpbl-analytics**/.claude/worktrees/wf25-review-write-channel1-execution`——**卡在 ai-workflow，worktree 在 cpbl-analytics**。該目錄現已不存在。這正是 ai-workflow#16 §8.3／§8.7 記載、#24 要用 `assign` 擋掉的形態。
3. **資源宣告有兩個不存在的路徑**：`file:cli/wfcli`（實際是 `cli/src/wf_cli/`）、`file:docs/handoff-contract.md`（實際在 `templates/`）；而真正存在的 `file:templates/dispatch-package.md` 被本卡佔了三天，期間 #20 在其上寫入。**已由 PM `amend` 更正（`op 1fa667aa`），宣告收斂為該卡實際交付的文件。** 請判定此更正是否恰當。

### PM 揭露

- **本卡從未被查核過**，故 PM 不以「補跑 release」處理（那是 WF-23 的作法，該卡有兩輪 APPROVE）。需求方裁定補查核。
- PM 未對文件內容做任何修改，僅更正資源宣告。
- **若你判定文件已過期到不堪用**，請直接說——需求方可選擇 `🛑已停止` 並記錄原因，而非強行讓一份過期文件通過。

### 環境紅線

唯讀查核；不得改動 main、不得 merge、不得改 Project 狀態。留言紀律：**不得讓任何一行以 `<!--` 緊接事件 marker 前綴起始**。

**若能留 receipt marker 收據**（`card_id`、完整 `source_sha`、報告原文 UTF-8 `report_sha256`），**請一併載明取材規則**（marker 在報告前或後、空白如何處理）——`handoff-contract.md` §3.1.2 未釘死版面，PM 曾為此逐一嘗試五種取材。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5253269041 · 2026-08-11T12:39:07Z

<!-- wf-review-event:v1 card_id=WF-25-REVIEW-WRITE-CHANNEL1 source_sha=7451b72ba7679893043950d71bad9642665e25da attempt_id=WF-25-REVIEW-WRITE-CHANNEL1-e0-7451b72ba7679893043950d71bad9642665e25da -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-25-REVIEW-WRITE-CHANNEL1`　attempt_id：`WF-25-REVIEW-WRITE-CHANNEL1-e0-7451b72ba7679893043950d71bad9642665e25da`
- 查核者：跨家族查核（需求方於對話中轉貼原文；查核者聲明受唯讀紅線限制未留 receipt marker，來源不可驗證）　escalation_epoch：0
- source_sha：`7451b72ba7679893043950d71bad9642665e25da`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-11T20:39:06+08:00

### self_run（查核者實跑）

- `git fetch origin && git log --oneline origin/main -1`
  - origin/main 與被審 SHA 均為 7451b72ba7679893043950d71bad9642665e25da，工作區乾淨。
- `cd cli && uv run pytest tests/test_doctor.py -q`
  - 70 passed。
- `wfcli doctor --review-channel --owner ruan6047 --project 4 --repo ruan6047/ai-workflow --issue-number 13 --card-id WF-25-REVIEW-WRITE-CHANNEL1 --strict`
  - review channel 回傳 unobservable；strict 非零結束。無 receipt、無 review event。
- `wfcli review WF-25-REVIEW-WRITE-CHANNEL1 --validate-only --reviewer GPT-5@Codex`
  - 驗證通過，且未寫入遠端狀態。
- `wfcli doctor --review-channel（省略 --owner、--project）`
  - exit 2，明確列出缺少 --owner, --project。

### findings（4，其中 blocking 2）

- **WF-25-REVIEW-WRITE-CHANNEL1-R0-001**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`review-channel-adoption-gap`
  - evidence：文件第 1 節是 2026-08-08 的快照；今日僅能重新證實 GPT-5@Codex 可跑 --validate-only，不能證實 Claude@GitHub Copilot 的能力。更關鍵的是，本卡本身 doctor 實測為 unobservable，而需求方揭露近期多輪實務走 C 案、未留 receipt。 B 案沒有成為實際可觀測通道。
  - disposition：更新第 1 節為具日期、repo 範圍與實測 artifact 的現況盤點；將 C 明確降為 「不滿足核心痛點、不得作為正常 fallback」的阻塞例外，並規定未有 receipt 不得把 PM 轉錄當成已驗證的跨家族查核。
- **WF-25-REVIEW-WRITE-CHANNEL1-R0-002**　severity=major　blocking=true　class=governance　attribution=coordinator　root_cause_id=`posthoc-review-gate-bypass`
  - evidence：13 的 Log 顯示 2026-08-08 assign 後直到本輪前沒有 review lifecycle event， 但文件已在 97c0cfa 進 main；本輪 doctor 對該 SHA 回 unobservable。 canonical 第 5 節明定事後查核是違規補救，不能把既有 main 產出視同已通過正常閘門。
  - disposition：不得以本次補查核直接洗平歷史違規或自動通過。需求方應在「修正後重新補查核」 與「已停止並記錄原因」間裁定；是否回退 main 仍屬需求方決定。
- **WF-25-REVIEW-WRITE-CHANNEL1-R0-003**　severity=major　blocking=false　class=governance　attribution=coordinator　root_cause_id=`cross-repo-worktree-registration`
  - evidence：13 記錄的 worktree 位於 cpbl-analytics，與 ai-workflow 卡及交付 repo 不一致； 該路徑目前不存在，ai-workflow 的 git worktree list 亦無此註冊。
  - disposition：保留為不可逆的歷史違規，不可事後偽造註冊。後續 assign 應由 24 的防線拒絕此形態。
- **WF-25-REVIEW-WRITE-CHANNEL1-R0-004**　severity=minor　blocking=false　class=authoritative-artifact　attribution=executor　root_cause_id=`replay-repository-ambiguity`
  - evidence：第 4 節的 111/112/113 未寫 repo；在 ai-workflow 查不到，實際位於 cpbl-analytics。 三案的歷史轉錄存在，但「若已有 B」屬反事實回放，並非 receipt 已實際存在的證據。
  - disposition：補上完整 repo 與 Issue URL，並將回放標為假設性驗證，不得表述為已落地的 receipt 機制。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5253285447 · 2026-08-11T12:40:29Z

## 🛑已停止（需求方 2026-08-11 裁定）

### 決策

**不修正、不重新補查核、不回退 main。** 卡片停止並封存。

### 原因

**一、核心建議未在實務落地。** 事後補查核判 `REQUEST_CHANGES`。文件選 B 案（查核者留固定收據、PM 轉錄）、C 案（純 PM 轉錄）僅為受控 fallback；**但實務上幾乎每一輪都走 C 案**——查核者聲明受唯讀紅線限制不寫 Issue，PM 轉錄並標「來源不可驗證」。查核者的結論：

> 文件不是完全不堪用，但它的核心建議未在實務落地；因此不能 APPROVE。

第 1 節的能力盤點（2026-08-08 快照）與第 3／4 節的機制描述，因此是**未落地的假設**而非現況。

**二、違規補救不得洗平為通過。** canonical `AI_WORKFLOW.md` §5 明定事後查核是違規補救、不是正常路徑。本卡自 2026-08-08 `assign` 後**零 review lifecycle 事件**，而產出已於 `97c0cfa` 進入 main；本輪 `doctor --review-channel` 對該 SHA 回 **`unobservable`**、`--strict` 非零結束。**不能以一次補查核把它視同已通過正常閘門。**

**三、兩項不可逆的歷史違規。**

- **跨 repo worktree 註冊**：卡在 ai-workflow，登記的 worktree 卻在 `cpbl-analytics`。該路徑已不存在。查核者裁定「**保留為不可逆的歷史違規，不可事後偽造註冊**」；後續同形態應由 [#24](https://github.com/ruan6047/ai-workflow/issues/24) 的 `assign` 防線拒絕。
- **資源宣告含兩個不存在的路徑**（`file:cli/wfcli`、`file:docs/handoff-contract.md`），而真正存在的 `file:templates/dispatch-package.md` 被本卡佔用三天、期間 #20 於其上寫入。PM 已 `amend` 更正（`op 1fa667aa`），**但查核者明確指出該更正「不會消除先前的資源／worktree 程序瑕疵」**。

### 交付物的處置

`docs/WF-25-REVIEW-WRITE-CHANNEL1.md` **留在 main 不動**（需求方裁定不回退）。

> **但自此不得被引用為已核可的權威描述。** 它是一份未經正常查核閘門而進入 main、且核心建議未落地的文件。若日後需要「跨家族查核者的寫入通道」的權威定義，應另開卡重新設計，而非引用本檔。

### 查核者確認仍正確的部分（供日後取用，非核可）

- §3 的 `doctor` **五態仍正確**，且第三面（Project 交付狀態）已實作。
- §3 的 `--owner`／`--project` 呼叫範例**已同步**（實跑確認）。
- §5 對 `audit_review_channel()` 的概述**仍大致相符**，測試未退步；但應補明「三面一致」才是 `recorded` 的**充分**條件。

### 未處理、明列於此

`R0-004`（minor，non-blocking）：§4 的 #111／#112／#113 未寫 repo，實際位於 cpbl-analytics；且「若已有 B」屬**反事實回放**，不是 receipt 已實際存在的證據。**本卡停止，故此項不修。**

### 一個仍然開著的問題

**B 案未落地這件事本身沒有被解決。** 本 session 的實況是查核者受「不得改 Project 狀態」的環境紅線限制而不留收據——**那條紅線與 B 案的前提直接衝突**。這是一個真實的設計缺口，但不屬於一張已停止的卡；需求方若要處理，應另開卡。

