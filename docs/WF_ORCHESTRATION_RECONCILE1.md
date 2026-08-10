# WF-ORCHESTRATION-RECONCILE1：可恢復任務編排狀態機設計

> 卡：[ai-workflow#16](https://github.com/ruan6047/ai-workflow/issues/16)　基線：`origin/main` `91d8a1f10ad2a8faceafb79f7e8c89571385569f`
>
> 本檔是**設計**，不含實作。所有可執行變更由衍生實作卡承接（§9），契約修訂另走紅線 PR（§10）。

## 0. 這份設計要解什麼

卡面痛點：開卡、scope 變更、交付、審查、CI、merge、部署、release 分散在規則、人工記憶與不完整 CLI；GitHub 限流或中斷後沒有可恢復狀態，導致卡片／看板／main 長期漂移。

「沒有可恢復狀態」不是抽象風險。2026-08-11 一天之內，本 repo 自身發生四件可查證的漂移（§8），其中三件的成因完全相同：**規則寫在文件裡，而唯一寫入通道不執行它**。這與同期 #15／#17 處理的「契約寫著 fail-closed、消費者實際 fail-open」是同一個病，只是換了層面——那邊是消費端沒實作，這邊是編排端沒實作。

因此本設計的判準不是「規則是否完備」，而是**每一條規則是否有機械執行者**。設計文件裡任何一條「應該要…」若找不到對應的動詞、守衛或對帳項，它就不算設計完成。

---

## 1. 十一項 grilling 裁決（2026-08-11，需求方逐題裁定）

| # | 決策點 | 裁決 | 關鍵理由 |
|---|---|---|---|
| Q1 | 執行者模型 | **無常駐程序**：CLI 動詞＋可重放 outbox，惰性恢復 | daemon 必然持有記憶體狀態＝第二狀態面雛形，違反基線；且 daemon 需要監控 daemon |
| Q2 | reconcile 權限 | **分層**：預設純偵測，`--apply` 只做白名單內、基於完整重放的修復 | 純偵測不解痛點（漂移之所以長期，正因修復靠人記得）；純自動修會一刀撤掉剛立的 fail-closed |
| Q3 | 事件排序 | **顯式 `state_version`**（per-card 嚴格遞增） | 序號是計數不是時刻，與時間語意契約正交；平台序無法跨「留言／Log／欄位」三面 |
| Q4 | outbox 本質 | **預寫意圖日誌**（WAL），非死信箱 | 死信箱接得住「失敗」，接不住「程序被殺」——`review` 三步之間 crash 什麼都不留 |
| Q5 | 重複修的檢討機制 | **機械 checkpoint 入本卡**；跨卡根因回顧另開卡 | §3／§4 的升級門檻早已存在，但無執行者：#15/#19 超門檻零 checkpoint |
| Q6 | 狀態機基底 | **枚舉凍結＋平台導出閘門**：PR／CI／merge 是守衛不是欄位 | 每一份平台事實的複本都是未來的一個 `half_written` |
| Q7 | PR＋CI 邊界 | **全統一**（含治理 repo、含純文件卡）；no-squash | 治理 repo 的「文件」就是它的產品；混合制守不住（實證見 §8.4） |
| Q8 | 觸發收窄 × clearance | **位置性判準**（僅首行構成事件宣告）＋`wf-review-clearance:v1` 配套 | 收窄消滅的全是誤報；位置性判準根本不進「列舉 Markdown 語境」的賽局 |
| Q9 | 落差 8b | **body 結構化區塊**（機器權威／散文渲染） | 免 v1→v2 全域 cutover；缺區塊天然落保守側 |
| Q10 | worktree 歸屬 | **平台導出**（Issue URL × git commondir）＋`assign` 寫入時預防 | 兩邊平台都已知道，抄成欄位就是再造一面可分歧的複本 |
| Q11 | 落地邊界 | **事件 cutover**，歷史不追溯，混世代卡永久降級純偵測 | 回填違反 append-only；雙軌會重新引入分類靜默失效 |

---

## 2. 狀態機：轉換表

**狀態集合＝現有凍結枚舉**（`FIELD_SPECS` 的 `交付狀態` 13 值 ＋ 獨立的 `部署狀態` 7 值）。本設計**不新增任何狀態值**（Q6）。

PR 是否開啟、CI 是否綠、merge 是否進 main——這些**不設欄位**，而是轉換的**守衛條件** [guard]，由動詞與 reconcile 即時向平台讀取。

### 2.1 轉換表

| 動詞 | 前置狀態 | 守衛（全部須成立） | 後置狀態 | owner 變更 | 失敗態 |
|---|---|---|---|---|---|
| `open` | （無） | 必填欄機械檢查、鏈深 ≤ 2 | `📥Backlog` | → 待指派 | 拒絕建卡 |
| `amend` | 非終態 | `--reason` 非空；值確有變更；Log 錨點唯一 | 不變 | 不變 | 拒收，零寫入 |
| `assign` | `📥Backlog`／`↩退回` | 資源宣告無交集；**worktree commondir repo ＝ 卡 Issue repo**（Q10） | `🚧進行中` | → 執行者 | 拒絕派工 |
| `handoff --next-stage review` | `🚧進行中` | `source_sha` 為完整 40 hex 且已推送；證據非空 | `🔍待查核` | → 查核者 | 拒絕交接 |
| `review` | `🔍待查核` | 結構化輸出合契約；**第三個可計數 attempt 起須先有 `escalation-checkpoint`**（Q5） | `✅通過`／`↩退回` | 不變 | `review-invalid`（留原狀）／拒轉錄 |
| `handoff --next-stage implementation` | `↩退回` | 同 review 方向 | `🚧進行中` | → 執行者 | 拒絕交接 |
| **`merge`**（新） | `✅通過` | PR 存在且 mergeable；CI 全綠（有定義時）；**schema／migration／needs-deploy 另需 sign-off 事件**（Q7）；分支尖端 ＝ 被核可 `source_sha`（差異須顯式授權） | `✅通過`（不變） | 不變 | 拒絕 merge |
| **`release`**（既有語意擴充） | `✅通過` 且已 merge | merge commit 為 main 祖先；需部署卡須 `部署狀態＝✅已驗證` | `🏁完成` | → 需求方 | 拒絕 release |
| `deploy-declare`／`deploy-state` | 依既有契約 | 相鄰前進；不跳級 | 部署狀態推進 | 依既有 | 拒絕轉換 |

### 2.2 `release` 的後置動作＝cleanup（Q6）

**`✅通過` 不是終態。** 資源宣告只在 `🏁完成`／`🛑已停止` 釋放，因此 `release` 轉換**必須**內含 cleanup，且順序不可調換：

```
cd 出 worktree → 移除 worktree → 刪本地分支 → 刪遠端分支 → 關閉 Issue → 寫 🏁完成
```

cleanup 不是「善後」而是轉換的一部分——把它當成獨立的、可選的收尾，就會出現 §8.2 的事故。

---

## 3. 事件契約

### 3.1 `state_version`：排序權威（Q3）

每個 lifecycle 事件必帶 per-card 嚴格遞增整數。**這是計數不是時刻**，與時間語意契約（cpbl#123）正交。

- **取號**：讀該卡現有最大序號 +1。GitHub 無原子遞增，故取號是 read-modify-write。
- **撞號**（同卡同序號兩筆）→ 並行寫入的證據 → **fail-closed**：該卡降純偵測，人工裁定。
- **缺號**（序列有洞）→ 有事件遺失或未落地 → 同樣降級。
- **舊事件無序號** → legacy epoch，以 `contract-baseline` 劃界（Q11），不追溯。

> **誠實界線**：撞號可偵測、不可預防。緩解是單 writer 紀律＋撞號 fail-closed，與 `wfcli amend` 的「重讀比對縮窗、不宣稱 CAS」是同一誠實等級。

### 3.2 受管轄判準的收窄（Q8）— 契約修訂案

**現行**（`handoff-contract.md` §3.1.4）：留言**任何位置**出現事件 marker 前綴即受管轄。

**修訂為純位置性判準**：

> 一則留言**唯有其首行為事件 marker 形狀**（以 `<!-- ` 加事件 marker 前綴起始）時，才構成事件宣告並受本契約管轄。首行合格 → 事件；首行是 marker 形狀但不合規 → 停機。**其餘任何位置的前綴出現，包括完整 marker 形狀的行，一律視為散文**，不受管轄、不觸發停機。

**收窄後仍會停機的**（全是真訊號）：首行畸形 marker（renderer 故障、手寫事件、版本過渡）、同 attempt 跨留言重複（落差 8a 不受影響）。

**失去的**：「留言中段畸形 marker」的告警。實測零次，且採信路徑本來就只看首行——中段 marker 從來不可能被誤採信，故此告警無保護價值。

**連帶後果**：#15／#17 自動解凍，無需為歷史留言補 clearance；`templates/dispatch-package.md` 於 2026-08-11 加入的留言引用紀律**隨此修訂作廢**，必須同步移除，否則即為自產文件漂移。

### 3.3 `wf-review-clearance:v1`：停機解除的留言平面表示法（Q8）

落差 7 的根因是 `review-escalation.md` §5 定義了 clearance 的**欄位**，卻未定義它在 GitHub 留言平面**長什麼樣**，消費者無從辨識，亦無 writer。

比照事件的既有模式：

```
<!-- wf-review-clearance:v1 card_id=<CARD_ID> quarantined_comment_id=<id> state_version=<n> -->
## 停機解除：<clearance_decision>

（人類可讀敘述）

```yaml
（§5 全欄位：quarantined_comment_url、quarantined_comment_author、
  quarantined_body_sha256、quarantine_reason、clearance_decision、
  superseding_attempt_id／repaired_body_sha256、incident_record_url、
  cleared_by、clearance_rationale）
```
```

- **首行 marker 承載識別**（同 Q8 位置性判準）；**fenced 區塊承載全欄位**（同 Q9 模式）。
- writer：新 `wfcli` 動詞（實作卡 §9-C）。clearance 事件同樣帶 `state_version`。
- 消費端判定沿用 `review-escalation.md` §5 既有規則（雙欄相符、hash 變動即重新停機、`forged-rejected` 不自動解除等），本設計**不改其語意**，只補表示法。

### 3.4 裁決留言的結構化區塊（Q9，落差 8b）

`render_verdict_comment` 於散文後附 fenced YAML，承載 #15 Q9 已定的**語意比對基準**：

```yaml
state_version: <n>
review_result: APPROVE | REQUEST_CHANGES
core_pain_resolved: yes | no
delivery_status: ✅通過 | ↩退回
findings:
  - finding_id: <id>
    accepted: <bool>
    status: open | resolved | withdrawn
```

刻意**排除**寫入時間與 reviewer 自由文字（它們每次執行都不同，納入即無法比對）。

- **marker 三鍵不動**，不觸發 v1→v2 全域 cutover。
- 消費端：同 attempt 兩則事件的區塊語意相等 → 冪等重送，放行；不等或**任一缺區塊** → 維持停機。
- 歷史留言無區塊 → 天然落保守側，無需 cutover 儀式。
- **區塊為機器權威、散文為人類渲染**，兩者同源產出；不一致即為竄改證據 → 停機。

---

## 4. 預寫意圖日誌（WAL）與恢復（Q1／Q4）

### 4.1 為什麼是 WAL 而不是死信箱

`wfcli review` 是三次遠端寫入（Issue 留言 → Project 欄位 → body Log）。**若程序在兩步之間被殺**（斷電、Ctrl-C、OOM）而非拋出例外，死信箱式的 outbox 什麼都不會留下——半寫入無影無蹤，只能靠 #20 的 `half_written` 事後偵測，而偵測到之後仍需人判斷缺哪一步。

WAL 讓「做到哪」在 crash 的任何位置都留得下來。

### 4.2 規格

- **位置**：全機層級（如 `~/.config/wfcli/outbox.jsonl`），以 `(owner, project)` 分鍵。**不放 repo 內**——`release` 會移除 worktree，repo 內的 outbox 將隨之蒸發。
- **冪等鍵**：`(owner, project, card_id, state_version, verb, step)`。無時鐘成分（呼應 cpbl#123：idempotency key 不得取環境時鐘）。
- **流程**：動手前 append 意圖（含全部子步驟）→ 每步成功後標記解除 [discharge]。
- **恢復**：任何 `wfcli` 指令啟動時掃描未解除項；補送前**先讀 GitHub 驗證效果是否已存在**（依冪等鍵查同序號事件）——已存在即標解除（多一次 API 讀，不重複寫入），不存在才補送。
- **壓實**：已解除項定期清理。

### 4.3 明文限制

- **單機**：outbox 不跨機同步。多機工作時未決項留在原機。此為**接受的限制**，非待解問題；多機需求若成真另開卡。
- **惰性恢復的延遲**：一次寫入失敗後若直接關機，狀態面停在不一致，直到下次執行任何 `wfcli` 指令。這是 Q1 選擇無常駐程序的已知代價。

---

## 5. reconcile：分層權限（Q2）

### 5.1 預設純偵測

列出所有分歧＋每項的精確修復指令。零寫入。

### 5.2 `--apply` 白名單（**窮舉，白名單外一律 fail-closed**）

| # | 分歧形態 | 自動修復動作 | 前提 |
|---|---|---|---|
| 1 | WAL 有未解除項，GitHub 無對應事件 | 依冪等鍵補送 | 序號未撞 |
| 2 | WAL 有未解除項，GitHub 已有對應事件 | 標記解除（不寫 GitHub） | — |
| 3 | 完整重放後，`交付狀態` 落後事件流終態 | 補寫欄位至重放結果 | **重放結果唯一** |
| 4 | 卡已 merge 且 `✅通過`，但 worktree／分支殘留、Issue 未關 | 執行 §2.2 cleanup 序列 | merge commit 確為 main 祖先 |

**每筆修復 append Log 記原值**（沿用 `wfcli amend` 已確立的紀律）。

### 5.3 白名單外——一律純偵測，交人

停機（`marker_quarantined`）、裁決衝突、順序歧義、撞號／缺號、混世代卡、任何需要語意判斷者。

> **硬前提（Q2）**：白名單修復必須基於**完整 timeline 重放**，不是單點比對。「欄位 ≠ 最後一則裁決結論」不必然是半寫入——可能是裁決後又合法 handoff 回去了。單看最後一則裁決去「修」欄位，會把合法的後續狀態倒退回去。**排序不可靠的卡（撞號／缺號／legacy epoch）一律降回純偵測。**

---

## 6. PR＋CI 統一（Q7）

- **範圍**：所有卡、所有 repo、含純文件卡、含治理 repo 自身。
- **理由**：治理 repo 的「文件」就是它的產品——#15 一張純文件卡吃了五輪查核、打出八個破口，風險量級不輸程式碼。「純文件所以免 PR」在此是假分類。
- **merge 方式**：保留 merge commit（no-squash）。**squash 會改寫 SHA，`source_sha` 綁定的整套契約會斷**。
- **執行者**：需求方授權 → 執行者 `gh pr merge`。授權與 merge 都落在平台可查的物件上。
- **sign-off 守衛**：`db_scope ∈ {schema, data-migration}` 或 needs-deploy 卡，**CI 綠是必要非充分**，merge 前另需需求方 sign-off 事件。
- **ai-workflow 需補最小 CI**（現無 `.github/workflows/`）：至少跑 `cd cli && uv run pytest`。實作卡 §9-F。

---

## 7. worktree 對帳（Q10）

- **repo 歸屬純導出**：卡的 repo ← Issue URL；worktree 的 repo ← git `commondir`。兩者不合 → 跨 repo 建立，機械可偵測。
- **`assign` 寫入時預防**：`--worktree` 的 commondir repo ≠ 卡 Issue repo → **拒絕派工**。只偵測不預防的下場見 §8.3。
- **primary worktree** ← `git worktree list` 首項，分類為 primary，**永不列孤兒**（修正既有誤報）。
- **合法跨 repo 沙箱**：使用 detached worktree（沿用既有 `detached_sandbox` 分類），不走註冊制。
- **registry `github` 模式**：實作讀 Project 的 `分支worktree` 欄位。ai-workflow 自 08-04 cutover 後 `TASKS.md` 僅為封存投影，doctor 目前實際上無 registry 可讀。

---

## 8. 漂移回放

### 8.1 cpbl#119：碼已部署、資料未重建（deploy／release 斷鏈）

程式修復已部署，但 production 衍生資料尚未依新判準重建；線上數據仍含舊歸因。

**本設計的恢復路徑**：`release` 的守衛要求需部署卡達 `部署狀態＝✅已驗證`（§2.1）。資料重建屬部署驗證的一部分，未完成則卡無法進 `🏁完成`，資源不釋放、卡持續可見。斷鏈從「靠人記得」變成「狀態機擋著」。

### 8.2 ai-workflow：三張已 merge 卡漏跑 `release`，永久持有資源宣告（**本卡開卡當日實證**）

#15／#17／#19 已 merge 並關閉 Issue，但交付狀態停在 `✅通過`、owner 仍掛著。`assign` 的終態集合是 `{🏁完成, 🛑已停止}`，於是它們被算成活卡，**資源宣告永不釋放**——#20 派工當場被拒絕。

**恢復路徑**：§2.2 把 cleanup 納入 `release` 轉換（而非可選善後）；§5.2 白名單第 4 條讓 reconcile 能偵測並修復此形態。

### 8.3 ai-workflow：cpbl 卡的 worktree 建在 ai-workflow repo 內

`ai-workflow/.claude/worktrees/ingest-splits-pa-split1-iter2` 屬 cpbl 卡，至今仍殘留。

**恢復路徑**：§7 的 `assign` 寫入時預防（拒絕跨 repo 註冊）＋doctor 純導出偵測。

### 8.4 ai-workflow：既有 PR 實務被降級為直接 merge（**本卡開卡當日實證**）

歷史卡（#3–#14）皆走 PR；2026-08-11 的四張（#15／#17／#19／#20）全是直接 merge。**規則沒變，只是換了個執行者，實務就降級了**——這正是混合制／慣例制守不住的實證，也是 Q7 選擇全統一的直接依據。

**恢復路徑**：§6 全統一，merge 成為帶守衛的動詞而非自由操作。

### 8.5 ai-workflow：#15／#19 超過三次退回門檻，零 `escalation-checkpoint`（**本卡開卡當日實證**）

| 卡 | REQUEST_CHANGES 輪數 | checkpoint |
|---|---|---|
| #15 | 4 | 0 |
| #19 | 6 | 0 |

`review-escalation.md` §3／§4 的升級門檻**存在於契約已久**，但 `wfcli review` 不計數、不算 `counts_toward_escalation`、不在第三次 attempt 時要求 checkpoint。三方（執行者、PM、查核者）都沒記得。

**恢復路徑**：§2.1 把 checkpoint 列為 review 的機械守衛——第三個可計數 attempt 起拒絕轉錄，直到 checkpoint 事件存在。

### 8.6 cpbl#120：文件與權威來源矛盾（結案後文件漂移）

兩處仍宣稱「G4 觀測凍結中」，而權威來源載明已於 2026-08-03 提前收窗。#113 的執行者因此缺少對齊依據。

**本設計的邊界（誠實聲明）**：狀態機**不解決一般性文件漂移**。它能做的是讓「卡結案時其宣稱已過期」這一類在 cleanup 階段被看見（§2.2 的 Issue 關閉是轉換的一部分，關閉留言可承載後續指標）。**內容層面的正確性不在本卡射程內**——這是需要人或另一類工具的問題，列為非目標（§11）。

### 8.7 cpbl#116：碼已交付、卡從未推進、分支孤兒（**跨 repo 漂移**）

卡面痛點是「部署生命週期無法透過唯一寫入通道轉換」。查證現況，漂移比卡面描述更嚴重：

| 事實 | 狀態 |
|---|---|
| 卡：cpbl-analytics#116 | `OPEN`，執行欄仍為「待指派」 |
| 實作：`deploy-state`／`deploy-declare` | **早已在 ai-workflow `main`**（`cli.py` 已註冊兩個子指令） |
| 分支：`origin/codex/WFCLI-DEPLOY-STATE1` | **仍孤兒殘留於 ai-workflow** |

**碼交付了、分支沒清、卡從未推進。** 根因是卡與工作分屬兩個 repo：卡在 cpbl，實作在 ai-workflow，而兩端都沒有機制看見另一端——cpbl 的看板不知道碼已上線，ai-workflow 的 `doctor` 不知道那條分支對應哪張卡（其 registry 只讀本 repo 的 `TASKS.md`）。

**本設計的恢復路徑**（三處合力，缺一不可）：

1. **§7 repo 歸屬純導出**：卡的 repo ← Issue URL，worktree／分支的 repo ← git `commondir`。跨 repo 的卡–工作對應因此可被機械表達，而非靠人記得。
2. **§7 registry `github` 模式**：doctor 改讀 Project（跨 repo 的 Project item 同在一個看板），孤兒分支比對才有跨 repo 的卡註冊可查——現行 `tasks-md` 模式在 cutover 後根本無 registry 可讀，這正是它偵測不到的原因。
3. **§2.2 `release` 內含 cleanup**：分支刪除是轉換的一部分。碼進 main 而卡未走 `release`，狀態機即擋在 `✅通過` 前不放行，孤兒分支不會無聲累積。

> **邊界誠實聲明**：上述三項讓此形態**可偵測、可對帳**，但**無法阻止**「在 A repo 為 B repo 的卡做事」本身——那是人的操作選擇。§7 的 `assign` 預防只擋註冊制 worktree，直接在別的 repo 開分支手動做事仍在射程外。這是已知殘餘風險，不宣稱解決。

### 8.8 cpbl PR#122：已重新歸因，不作為本卡案例

CI 紅經 cpbl#123 查證為時間語意缺陷（測試 module import 取容器日、受測碼取台北日，UTC runner 上確定性地一天紅 8 小時），非編排漂移。為此症狀設計恢復路徑會針對一個即將不存在的東西。已由 `wfcli amend`（`op bb34736e`）自本卡驗證條文移除。

---

## 9. 衍生實作卡（建議，深度 1）

| # | 卡 | 範圍 | 依賴 |
|---|---|---|---|
| A | `state_version` 寫入與撞號偵測 | 所有 `wfcli` 寫入動詞取號；撞號／缺號 fail-closed | — |
| B | WAL outbox 與 `wfcli resume` | §4 全部 | A |
| C | `wf-review-clearance:v1` writer 與消費 | §3.3；解落差 7 | A |
| D | 裁決結構化區塊 | §3.4；解落差 8b；`render_verdict_comment` 改造 | A |
| E | `wfcli merge` 動詞與守衛 | §2.1 merge 列＋§6 sign-off | — |
| F | ai-workflow 最小 CI | §6；至少 `pytest` | — |
| G | `release` 內含 cleanup ＋ `reconcile --apply` 白名單 | §2.2、§5.2 | A、B |
| H | worktree repo 歸屬預防與 registry `github` 模式 | §7 | — |
| I | review 的 escalation 計數與 checkpoint 守衛 | §2.1、§8.5 | A |

**契約修訂 PR（非實作卡）**：§3.2 收窄 ＋ §3.3 clearance 表示法入 `handoff-contract.md`／`review-escalation.md`，走紅線 PR＋跨家族查核（Q7／§10）。

---

## 10. cutover 程序（Q11）

1. 契約修訂 PR 先行（§3.2／§3.3）——收窄落地後 #15／#17 自動解凍。
2. 實作卡 A（序號）落地。
3. 以既有 one-shot `contract-baseline` 事件劃線。**線後所有寫入**適用新制，不分新舊卡。
4. 線前歷史事件**不追溯**：無序號事件構成 legacy epoch，含其之卡永久降級純偵測（§5.3），直到自然結案。
5. 在途卡不中斷——其未來動作自動落入新制（下次 merge 開 PR 即可）。

**混世代卡**（線前開、線後仍活）的重放永遠是降級模式。可接受：它們終會結案，且降級是純偵測而非誤判。

---

## 11. 非目標

- **跨卡／執行內同族根因回顧**（Q5）：今天的「換攻擊面十二輪找到同族錯誤」屬品質回饋治理，另開卡。本卡只做同卡同 epoch 的機械 checkpoint。
- **多機 outbox 同步**（Q4／§4.3）。
- **receipt 的結構化承載**：本卡只補 clearance 與裁決區塊；receipt 的未知版本天然落 `unobservable`，方向已保守。
- **時間語意**：歸 cpbl#123。本設計刻意全程無時鐘（Q3／§4.2）。
- **一般性文件內容正確性**（§8.6）。
- **Project 內建 `Status` 欄位的語意**：沿用 `deploy-state` 既有映射，不在本卡重新定義。
