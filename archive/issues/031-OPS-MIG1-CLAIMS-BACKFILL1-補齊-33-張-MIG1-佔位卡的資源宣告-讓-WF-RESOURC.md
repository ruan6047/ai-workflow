# #31 OPS-MIG1-CLAIMS-BACKFILL1 補齊 33 張 MIG1 佔位卡的資源宣告，讓 WF-RESOURCE-WRITESET1 的 sunset 有人負責
- state: closed  created: 2026-08-11T16:17:57Z  closed: 2026-08-18T15:21:44Z
- url: https://github.com/ruan6047/ai-workflow/issues/31
- comments: 5

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
- 執行：待指派　查核：待指派
- Initiative：—　spec 基線：WF-RESOURCE-WRITESET1 於 SHA cb6028fc9f704459fd68456491bbf7238f8e10be 的 §9.7b 探針輸出（96 item／解析失敗 33／帶 MIG1 marker 33／帶 sentinel 仍失敗 0／母體外 0）與其 E1–E3 豁免到期機制。母體為該卡釘住的 33 個 card id 字面常數清單。
- DB：db_scope=none
- 服務的原始目標：把那 33 張的寫入集從「未知」變成「已宣告」，使互斥檢查對全部現役卡成立，並讓 sunset 到期時母體為空。

## 簡介
<!-- card-brief:begin -->
已停止：原要把 33 張 MIG1 遷移卡無法解析的資源宣告補成正式宣告，使互斥檢查不再對它們靜默 fail-open（assign_cmd.py:123-131 走 skipped_unparseable→continue 且逐字印「不擋派工」）。交付 docs/reference/MIG1_CLAIMS_BACKFILL.md：21 張逐張處置（可判定 6／Initiative 3／射程未定 12）與可重跑探針。適用時機：要查 MIG1 卡的宣告為何仍解析失敗、或互斥檢查對它們是否有效時；或要引用「補齊輸入不改變判定缺陷」這個停卡理由時。⛔ 非射程：驗收條件 1 機械不可執行故 amend 實測 0/33，21 張的宣告一個字也沒寫進 GitHub；不修比對演算法本身（完全字串比對對現役比對集漏報 91%）；恢復條件三項見 ai-workflow#31 留言。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：33 張 MIG1 遷移卡的資源宣告至今無法解析，其中 21 張仍 OPEN 且全部在 cpbl-analytics。assign_cmd.py:123-131 對它們走 try_parse_block→None→skipped_unparseable→continue，stderr 逐字印「不擋派工」——互斥檢查今天就對這 21 張整組跳過，是靜默的 fail-open 而非排程好的停機

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:docs/reference/MIG1_CLAIMS_BACKFILL.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 逐張判定該卡實際的寫入集並以 wfcli amend 寫入正式宣告；不得為了讓解析通過而填入空陣列——「未正式宣告」與「無資源」是兩件事，這正是本卡要消除的混淆。
- [ ] 寫入集無法判定者（Backlog 中射程未定的卡）不得猜測，須明列並交需求方裁定射程或改狀態；不得以佔位值蒙混。
- [ ] 完成後重跑 WF-RESOURCE-WRITESET1 §9.7b 探針，解析失敗數須為 0，且該卡 E1 母體清單同步清空。
- [ ] 補宣告過程中新產生的寫入集相交須逐組列出並解決（先後派工或收窄），不得因為補了宣告反而製造新的互斥衝突而不自知。

## 驗證

- [ ] 探針輸出前後對照，由可重跑的 artifact 自動產生，不得人工聲明「全部補齊」。
- [ ] 抽驗至少 5 張已補宣告的卡：宣告內容與該卡實際會寫的檔案相符，非形式上填滿。
## Log

- 2026-08-12T00:17:56+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-16T10:42:56+08:00 amend by wf-cli（op acfa0916）→ 核心痛點：原值「OPS-STATE-PLANE-MIG1 遷移寫出自我標示為「未正式宣告」的資源宣告佔位區塊（有 fenced JSON、無 resource-claims sentinel），實測 Project #4 的 96 張卡中 33 張如此。WF-RESOURCE-WRITESET1 裁定未解析宣告一律 fail-closed，並設硬性 sunset 2026-09-30；到期後只要還有任何一張不可解析的活卡，任何卡都不能派工——那是全 Project 停機。需求方已接受硬截止，但會自動放寬的截止不是截止，沒人負責的硬截止則是排程好的停機。」→ 新值「33 張 MIG1 遷移卡的資源宣告至今無法解析，其中 21 張仍 OPEN 且全部在 cpbl-analytics。assign_cmd.py:123-131 對它們走 try_parse_block→None→skipped_unparseable→continue，stderr 逐字印「不擋派工」——互斥檢查今天就對這 21 張整組跳過，是靜默的 fail-open 而非排程好的停機」；理由 需求方 2026-08-16 裁定改寫（裁定全文見 issuecomment-5305378630）。原核心痛點把風險描述為「2026-09-30 的 UNPARSEABLE_EXEMPTION_SUNSET 到期後將一律拒絕、屆時派工停機」。實測推翻：該常數與 --ignore-unparseable 在 cli/src 命中皆為 0，只存在於 WF_RESOURCE_WRITESET1.md:493 的設計文件。排程好的停機不會發生，因為那個排程沒有實作。真實風險方向相反且是現在進行式——assign 對無法解析的宣告 fail-open，21 張 OPEN 卡的資源互斥檢查整組被跳過，跳過不報錯只印一行提示。原敘述會讓排序者以為還有到 9 月底的緩衝，實際上是現在就在漏而且安靜。用錯的理由排優先序會排錯。；授權 依需求方 ruan6047 於 https://github.com/ruan6047/ai-workflow/issues/31#issuecomment-5305378630 的裁定（GitHub comment author 已逐字核對，非留言內文自述）。
- 2026-08-18T20:51:26+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree claude/mig1-claims-backfill-31 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/mig1-claims-backfill-31；交付狀態 🔨執行中；實際能力層級 主力型（卡面無建議層級：卡面標頭區沒有獨立成行的 <!-- wf-routing:v1 --> 宣告：本卡開立於規劃期路由必填之前；理由：本卡開立於規劃期路由必填之前，卡面無 wf-routing 基線可比對，故無「偏離」可言，此處補記判定依據：依 MODEL_ROUTING「跨檔、不可逆或錯誤難察覺時升級」三項全中——(1) 跨檔跨 repo：要逐張判定 21 張 cpbl-analytics 卡的實際寫入集；(2) 不可逆：amend 寫入的 Log 行 append-only，判錯只能再 append 更正；(3) 錯誤難察覺：宣告填錯不會有任何機制發現，那正是本卡要消除的痛點。降級條款「答案唯一且可沿用既有模式」不成立。）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 target_absent（機器局部，沉默不代表無誤）。
- 2026-08-18T21:25:05+08:00 handoff by wf-cli → owner 待指派；iteration 0；SHA 6a910767bebfbb4cc1d70002b20e105f033055f2；證據 執行交付（2026-08-18）：分支 claude/mig1-claims-backfill-31，worktree 保留給查核者進駐。⚠️ 核心結論是驗收條件 1 在本卡基線上機械不可執行——33 張母體卡的標題逐字是「## 資源宣告（機器可讀；null／[] 代表未正式宣告，不代表無資源）」，而 _RESOURCE_HEADING 期望逐字「## 資源宣告」。PM 已獨立複驗 #66：parse_block 失敗、_locate_section 拋 AmendError「出現 0 次，必須恰好 1 次」，兩道門皆擋，amend 可達 0/33，故驗收條件 3（解析失敗數為 0、母體清空）未達成。交付物為 docs/reference/MIG1_CLAIMS_BACKFILL.md：21 張逐張處置（可判定 6／Initiative 3／射程未定 12）、可重跑探針、新產生互斥 1 組（ML-PA-SIM-CONTEXT1 × ML-PA-SIM-TEAM1 撞 file:src/cpbl/models/pa_sim.py，解為先後派工）。⚠️ 21 張的宣告一個字也沒寫進 GitHub，§3 的提案只在本機構造 ResourceDeclaration 跑過前綴檢查。執行者另列六項待需求方裁定與九項未驗，見交付報告。查核重點建議放在：(a) §1.4 三條出路的判斷是否窮盡；(b) 12 張判不定者是否真的判不定——執行者自陳只讀 docs/tasks/<CARD_ID>.md 未讀各卡引用的上游文件；(c) 驗證條 2「抽驗 5 張」只做到 spec×程式碼位置對帳，未達宣告×實際 diff 對帳強度。。
- 2026-08-18T23:21:36+08:00 handoff by wf-cli → owner —（已停止）；iteration 0；SHA 6a910767bebfbb4cc1d70002b20e105f033055f2；證據 停卡（2026-08-18）：逐條理由見 issuecomment-5330286630。決定性的是三條實測：(1) assign 的拒絕分支 append_log_line 命中 0，互斥擋下派工在構造上不留任何痕跡，故「它擋過嗎」無法從任何持久紀錄回答；配套 find_conflicts 於 9ef3154（08-04 22:53:12）上線而 events.jsonl 同日 23:47:31 封存，查事件檔落空是零資訊。(2) 本卡母體 21 張全為 💡需求＋Design Gate、零分支零 worktree，模擬灌入 spec 宣告後比對集不變、閘門行為一格不動。(3) 出貨的完全字串比對對現役比對集漏報 91%（逐字串 1 對 vs 階層包含 11 對），補齊輸入不改變判定缺陷。依 ROADMAP 目標排序判為目標 3，§3.6「只要沒有多 agent 並行就不痛」適用。⚠️ 但書：板上已有兩張子 agent owner 的卡，並行已開始（實測寫入集不相交）。交付物分支 claude/mig1-claims-backfill-31 保留不刪，其 21 張逐張判定、漏報 10 組的發現、可重跑探針三項獨立有效。恢復條件三項見留言。。
- 2026-08-26T21:42:51+08:00 amend by wf-cli（op 19a2aac9）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:ed42cfa16664642026c96a064f8c50b820d63f59acc54a37f2975fa5f56f7464 (797 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5305378630 · 2026-08-16T02:42:22Z

## 需求方裁定：核心痛點的風險方向寫反了，須改寫（2026-08-16）

需求方 2026-08-16 裁定改寫本卡核心痛點。以下為依據。

### 實測推翻原敘述

原核心痛點把風險描述為「`UNPARSEABLE_EXEMPTION_SUNSET` 2026-09-30 到期後將一律拒絕、屆時派工停機」。

**那兩個 token 在機器上不存在：**

```
$ git grep -c "UNPARSEABLE_EXEMPTION_SUNSET" cli/src/    → 0
$ git grep -c "ignore-unparseable"            cli/src/    → 0
```

它們只出現在 `docs/WF_RESOURCE_WRITESET1.md:493` 的設計文件裡。**排程好的停機不會發生，因為那個排程沒有實作。**

### 真實風險方向相反，而且是現在進行式

```
assign_cmd.py:123-131
    try_parse_block(...) → None
    → skipped_unparseable
    → continue
    stderr 逐字印「不擋派工」
```

**互斥檢查今天就對這批卡整組跳過。** 是靜默的 fail-**open**，不是排程好的 fail-closed。

### 母體複驗（147 個 Project item 逐張讀 body）

| | |
|---|---|
| 無法解析的宣告 | **33** 張 |
| 其中仍 OPEN | **21** 張 |
| 分布 | **100% 在 `cpbl-analytics`**——也就是有真實使用者、有生產資料庫的那個 repo |

### 為什麼這值得動卡面而不只是留言

原敘述會讓排序者以為「還有到 9 月底的緩衝」。實際上是「**現在就在漏，而且安靜**」。

**用錯的理由排優先序會排錯。** 2026-08-16 的 Backlog 重評把本卡列為建議先做的三張之一，但同時標明「卡面須先改寫，否則排序依據是假的」。

### 與 `#88` 的分工

本卡同時是「文件宣稱一個機制、機器上零實作、失效方向靜默」的一個實例。依同日重評的根因分組：

- **發現面**由 `#88 WF-DISPOSITION-FIX1` 承接（該卡射程已建議擴為一支可重跑的 doc↔code 對帳器，跑一次就會吐出本卡這一筆，見 `#88` 的 `issuecomment-5305364360`）
- **實作面**（21 張宣告補齊）**仍屬本卡**，對帳器不會替你補宣告

### 明列未證實

⚠️ 本裁定證明了 fail-open 的**機制存在**，但**沒有證據顯示曾發生實際的寫入集撞車**——靜默失效的本質就是不留痕，這一格無法窮舉。所以本卡的急迫度依據是「守衛對 21 張整組失效」，不是「已經撞過車」。


## Comment 5328422509 · 2026-08-18T12:52:24Z

## 派工包：`OPS-MIG1-CLAIMS-BACKFILL1`（2026-08-18）

**基線**：`ae8f74162797e2eed7180a1cd1ed6692fab3b6d3`（派工當下的 `origin/main`；分支尚未建立，故基線即 origin/main，非 merge-base）
**分支／worktree**：`claude/mig1-claims-backfill-31` @ `/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/mig1-claims-backfill-31`
**能力層級**：主力型（理由見 claim 事件）

### 母體：派工當下的實測名單

本次 `wfcli assign` 的 stderr 逐字印出了它——這 21 張就是今天真的從互斥檢查裡消失的活卡：

```
DEV-VERIFY-TM-ASSERTS1、INGEST-LIVE-RECONCILE1、INGEST-POSTGAME-FINALIZE1、
INIT-GAME-RECAP、INIT-OFFICIAL-DATA1、INIT-PRODUCT-UX、MATCHUP-DATA2、
ML-FIELD-LINEUP1、ML-FIELD-OAA-VAL1、ML-FIELD-OF1、ML-PA-SIM-CONTEXT1、
ML-PA-SIM-TEAM1、ML-PT3、ML-SIM2、OPS-BACKUP-DR1、OPS-POSTGAME-OBSERVE1、
OPS-REMOTE-CUTOVER1、OPS-REMOTE-PROBE1、OPS-REMOTE-ROUTE1、OPS-REMOTE-WORKER1、
UX-TEAM-FIELD-HIST1
```

全部在 `cpbl-analytics`、全部 `💡需求`、owner 全為 `ruan6047（Design Gate）`。⚠️ 注意 `is_owner_assigned("ruan6047（Design Gate）") == True`——機器認定它們「已認領」，所以它們**一直待在比對母體裡、又一直被跳過**。這是它們危險的原因，不是躺在 Backlog 沒人碰。

失敗原因逐張相同：body 內找不到獨立標題行 `## 資源宣告`（字樣出現在 Log 之前但不是獨立標題行，排版可能已被字面 `\n` 破壞）。

### ⚠️ 規劃期追加的硬約束（本卡開立時還不知道）

**環境名即將列舉化，而那是一道單向門。** `ai-workflow#87` 第四項已裁定 grammar 收斂為封閉集合 `local｜test｜staging｜production`。而 `amend_cmd.py:754` 的第一行是 `current = parse_block(item.body)`——**先解析現值再套用新值**。實測：現值非法時整個 amend 拋錯 `return 2`。

所以：

1. **補宣告時一律使用 `local｜test｜staging｜production`，嚴禁寫入 `db:dev:`**。寫了 `dev` 的那些卡，在列舉化落地後就再也無法經 `wfcli` 修復，而手改 Issue body 被 `cpbl-analytics/docs/AI_RUNBOOK.md:413` 禁止。
2. ⚠️ `cpbl` 的 `docs/DATABASE_CONTRACT.md` §2 只定義 `local / test / production` 三個環境，**沒有 `staging`**。上游列舉多一個 cpbl 沒有的環境——碰到需要第四個環境的卡，列出來交需求方裁定，不要自己選。
3. **`db:<env>:schema` 不支配 `db:<env>:table:<name>`**（`resources.py` `find_conflicts` 是完全字串比對）。宣告 schema 不會擋住宣告 table 的卡。驗收條第 4 項要你列出「補了宣告反而製造的新互斥」——判定時請用這條真實語意，不要假設 schema 涵蓋 table。

### 驗收與證據紀律

四條驗收條照卡面，額外三點：

- **驗證第 1 條的 artifact 必須可重跑**。「解析失敗數須為 0」要由腳本輸出，不接受人工聲明。本 repo 有前例：完整性宣稱只能由自動產生的證據支持。
- **不得為了讓解析通過而填空陣列**。「未正式宣告」與「無資源」是兩件事——這是卡面自己寫的紅線。
- **判不出寫入集的卡不要猜**，列出來交需求方裁定射程或改狀態。21 張全是 `💡需求`，射程未定是預期的，明列即可。

### 我沒驗到的

- 21 張的**實際**寫入集我一張都沒判——那正是本卡的工作。
- `is_owner_assigned("ruan6047（Design Gate）")` 為 True 是刻意慣例還是意外，我沒查它的治理語意。
- `#24 WF-RESOURCE-WRITESET1` §8.7／§8.8 設計的 `--ignore-unparseable` 與 `UNPARSEABLE_EXEMPTION_SUNSET` 在 `cli/src` 是**零實作**（只存在於設計文件）。本卡只補母體，**不實作拒絕**——升為拒絕是另一件事，不在本卡射程。


## Comment 5329900516 · 2026-08-18T14:50:26Z

# 派審詞（2026-08-18）— 標的兩件：`ai-workflow#31` 與 `cpbl-analytics#139`

> 這份是實際發給查核者的逐字內容，補存於此供稽核。⚠️ 查核者與執行者、規劃者**同家族**，
> 故其產出是**攻擊與證據**，不是裁決；正式的跨家族查核閘門仍未通過。

## 給查核者的紀律

產出是 findings 報告，不是裁決。**嚴禁**寫 APPROVE／REJECT 當結論、**嚴禁**跑 `wfcli` 任何動詞、
**嚴禁** `gh issue comment`／`gh issue edit`／commit／push／merge。全程唯讀，收尾時兩棵樹
`git status --porcelain -uno` 都要空並回報。基線自己 `git fetch` 再 `rev-parse`，不抄別人給的 SHA。

---

## 標的一：`ai-workflow#31`（已執行，`🔍待查核`）

分支 `claude/mig1-claims-backfill-31` @ `6a910767bebfbb4cc1d70002b20e105f033055f2`，
交付物 `docs/reference/MIG1_CLAIMS_BACKFILL.md`（481 行，單一檔案改動）。

**執行者的核心結論**：驗收條件 1 機械不可執行——33 張母體卡的標題逐字是
`## 資源宣告（機器可讀；…）`，而比對是逐字相等，故 `amend --resources` 可達 0/33。
**PM 已獨立複驗過這一條**，所以要查的不是它對不對，而是**它的後果與射程判斷對不對**。

要攻的七項：

1. ⭐ **12 張「射程未定」是真的判不定嗎。** 執行者自陳只讀 `docs/tasks/<CARD_ID>.md`，
   沒讀各卡引用的上游文件（`ops-remote-crawler-rollout.md`、`OFFICIAL_DATA_GAP1_RESULTS.md`、
   `ml-sim1-spec.md`…）。**逐張去讀**——若有哪張射程其實已寫死在上游，那是漏判。**這是最大的洞。**
2. **6 張「可判定」的證據強度。** 只做到 spec×程式碼位置對帳，未達「宣告 × 實際 diff 對帳」。
   `ML-PA-SIM-*` 只確認 `pa_sim.py` 存在、沒讀它。抽驗至少 3 張。
3. **3 張 Initiative 的處置是推論**（`db_scope: none` ＋ `file:docs/tasks/INIT-*.md`），
   canonical 對「治理寫入算不算資源」無明文，且三張 spec 檔自 2026-08-01 起無 commit。
4. **新產生的互斥 1 組**（`ML-PA-SIM-CONTEXT1` × `ML-PA-SIM-TEAM1` 撞 `file:src/cpbl/models/pa_sim.py`）
   ——驗真偽與有無漏組；另驗「契約謂詞 5 組／現役活卡 10 組」對 `find_conflicts`（完全字串比對）
   vs `WF_RESOURCE_WRITESET1` §2.2（前綴謂詞）落差的描述是否準確。
5. **`cpbl#66 ML-FIELD-OF1` 完全沒有 `## Log` 區段**，執行者沒追為什麼 08-13 批次 handoff 沒留痕。
6. **交付物本身**：有無過度宣稱；探針是否真的可重跑；BEFORE/AFTER `diff` 零輸出是否如其所說是預期而非疏漏。
7. **需求方已裁定走「甲」**（改 `wfcli` 定位規則，已開 `ai-workflow#105`）。驗這個後續是否正確涵蓋
   #31 的阻塞，以及 #31 接下來該退回重做、縮小驗收、還是阻塞等 #105。

---

## 標的二：`cpbl-analytics#139`（規劃期，`🧭規劃中`）

不是已執行的工作，是**規劃產物**：14 條驗收 ＋ 4 條驗證。

**來歷**（先讀，避免重跑）：原始射程重算報告（A1–A8／V1–V4）從未貼上卡、不可復原。
現行條文是 PM 綜合六輪研究後重寫的第二版；第一版（8 條）經一輪對抗式查核後
**兩條不成立、六條需改**（見 `issuecomment-5328547674`）。**第二版本身沒有被攻擊過。**

要攻的七項：

1. ⭐ **逐條先講出「什麼結果會推翻它」。** 構造上不會失敗＝零資訊；構造上不會通過＝噪音。
   上一輪就是用這個判準打掉兩條——其中一條是 PM 自己寫的 `git diff --quiet HEAD`，
   實測 commit 之後恆綠，比它取代的計數比對更弱。
2. **要讓每條變綠，最省力的做法是什麼，會不會破壞東西。** 已知破壞路徑五條：
   `sed -i` 打穿封存事件帳、刪 ROADMAP §2.0 整節、`gh issue edit` 抹掉 append-only Log、
   覆寫 research artifact、`amend --resources` 整份取代吃掉 `file:` 宣告。查有無第六條。
3. **條與條之間有無互相抵銷或重複。** 今日兩個前例：`ai-workflow#103` 死在驗收 5 與 9 互相抵銷（已撤卡）；
   #139 第一版的「封存區定義須寫死」自己沒寫死。
4. ⭐ **PM 的一個判斷要獨立檢查**：第一版把「封存」寫成「檔案路徑 vs issue 狀態」二選一，
   PM 改用機械判準「衝突檢查還讀不讀它」——實測 #53（`⏸阻塞`）與 #90（`📦已合併`）宣告仍被讀、
   #55／#88／#136 皆 `🏁完成` 屬 `TERMINAL_STATUSES` 故 assign 直接跳過。判此判準是否正確，
   以及「終態卡正規化屬檔案衛生零操作效果」是否成立（反面：終態卡可能被重開）。
5. ⭐ **#139 會不會跟 #31 一樣機械上做不到。** PM 已驗五張目標卡（#53/#55/#88/#90/#136）的
   `parse_block` 與 `_locate_section` 全部 `OK`——**複驗這一條**，並查有無別的機械阻塞。
6. **數字逐個複驗，不要抄**：`db:<env>:cpbl` 9 處跨三檔、`docs/tasks/` 6 處、ROADMAP §2.0 範圍 335–366、
   `not-asserted` 規則語句唯一但 token 6 處、993 行 capability matrix、`prod×5／dev×4`。
7. **4 條驗證夠不夠**，特別是「由查核者在合併結果上跑 merge-base diff」——它要求的是**查核者**跑而非交付者，判此安排可不可行。

---

## 已知會誤導查核者的東西（一併給了）

- ⚠️ `db:<env>:schema` **不支配** `db:<env>:table:<name>`（`find_conflicts` 是完全字串比對）。
- ⚠️ **關鍵字沒命中不是證據**。要證明某物不存在，去讀 config／呼叫圖／diff 的形狀。
- ⚠️ `amend_cmd.py:754` **先 `parse_block(現值)` 再套新值**，現值非法即整個 `return 2`。
- ⚠️ `docs/AI_RUNBOOK.md:414` 只規定 claim／handoff／review／merge／release 五個 lifecycle 動詞走 wfcli，
  **並未逐字禁止 `gh issue edit`**。派工包曾誤引為紅線（PM 的錯），別跟著錯。

## 回報格式要求

兩個標的分開。每個 finding 給：嚴重度／是否 blocking／逐字證據（實跑指令＋原始輸出）／建議處置。然後：
兩件各自最危險的一條與它會誘發什麼行為；應追加而現行沒有的條目；
⭐ **沒驗到的、未證實的假設、失敗或不如預期的結果**（不得省略）；
受 GitHub 配額／5xx 影響而未取得的項目（凡 5xx／空回應標 UNKNOWN，不得寫成 0 或「不存在」）。


## Comment 5330286630 · 2026-08-18T15:21:04Z

## 停卡：機制從未證明是承重的（2026-08-18）

本卡的核心痛點是「21 張活卡的資源互斥檢查被靜默跳過（fail-open）」。停卡的理由不是這件事不真，而是**它服務的機制沒有可證明的承載作用，而本卡做完不會改變任何行為**。

### 一、⭐ 互斥拒絕在構造上不留痕，所以「它擋過嗎」無法回答

`assign_cmd.py` 的拒絕分支逐字：

```python
if conflicts:
    print(f"[assign] 拒絕：{args.card_id} 的資源宣告與下列活卡衝突", file=sys.stderr)
    for cid, overlap in conflicts:
        print(f"  - {cid}：{', '.join(overlap)}", file=sys.stderr)
    return 4
```

**該區塊 `append_log_line` 命中 0。** 成功的 assign 會寫 Log，被擋的一個字都不寫——沒有事件、沒有欄位寫入、沒有留言。

配套事實：`find_conflicts` 於 `9ef3154`（2026-08-04 22:53:12 +0800）進 main，而 `docs/control-plane/events.jsonl` 在同日 23:47:31 封存——機制上線 **54 分鐘**後事件檔就凍結了。**查事件檔落空是零資訊，不是證據。**

分母：兩 repo 卡面 Log 裡 `assign by wf-cli` 共 **110 次**。110 次成功派工、0 次拒絕留痕。

⚠️ 據實說：這不是「從沒擋過」的證明，是六個面（events.jsonl／161 張卡面／891 則留言／git log／archive／本機兩棵樹）的空集合，加上「構造上不會留痕」這個機制事實。PM 與需求方的對話 transcript 不在任何 repo，若曾被擋而當場改宣告繞過且無人寫下，查不到。

### 二、本卡做完，閘門行為一格都不會變

那 21 張逐張核對：**全部 `💡需求` ＋ owner `ruan6047（Design Gate）`，沒有一張持有 `分支worktree`，沒有一張有分支。暴露面 0。**

而它們的 spec 檔幫不上忙：21 張裡 **0 張**的 `docs/tasks/*.md` 有可用的 `db_resources` 區塊，14 張連「資源」二字都沒有。模擬把 spec 宣告全部灌進去後重跑，比對集仍是原本那些，仍只有 `#95`×`#97` 那一對——而那兩張都是 `💡需求`／Design Gate，**沒人在做，是假互斥**。

### 三、今天的比對集：21 張，1 張在執行

```
gate1 非終態：70　gate2 且已認領：42　gate3 且可解析：21
比對集狀態分布：{'💡需求': 10, '📦已合併': 5, '⏸阻塞': 3, '✅通過': 1, '🔨執行中': 1, '🧭規劃中': 1}
```

`💡需求` 那 10 張全是 Design Gate 佔位。`is_owner_assigned` 把 `ruan6047（Design Gate）` 判為「已認領」，於是把沒有分支沒有 worktree 的卡放進了比對集——**這道閘門的行為與它自己的 docstring 不符**。

### 四、而出貨的判定漏掉 91% 的真實重疊

同一組比對集，把「完全字串相等」換成 `#16 §7.2`／`#24` 設計的階層路徑包含語意：逐字串 **1 對**、階層包含 **11 對**。目錄級宣告（`file:tests/`、`file:src/cpbl/models/`、`file:web/`）在完全字串比對下形同虛設。

**補齊輸入覆蓋不會改變這件事**——本卡補的是輸入，漏的是判定。

### 五、依 ROADMAP 判

ROADMAP 的目標排序逐字是「可稽核的內容 ＋ 防止低級事故為主，其他有最好但非必要」。依 §0 檢查與 §5 finding 分流第 1 步「它會不會**現在**就造成低級事故」：比對集裡的執行中卡近乎零、撞過的唯一一次（PM 自陳 `issuecomment-5255484548`，派 #22 時 #16 持有整個 `templates/`）沒有造成損害、需求方已於 `cpbl#130` 裁定災難鏈「從未發生」。→ **目標 3**，且 §3.6 批一的判準逐字適用：「只要沒有多 agent 並行就不痛」。

⚠️ 但書：板上已有兩張卡 owner 是子 agent（`#135`／`#140`），並行已經開始。實測兩張寫入集不相交，**故觸發條件尚未達成，但已不遠**。恢復條件見下。

### 交付物保留，不隨卡作廢

分支 `claude/mig1-claims-backfill-31` @ `6a910767bebfbb4cc1d70002b20e105f033055f2`（`docs/reference/MIG1_CLAIMS_BACKFILL.md`，481 行）**保留不刪**。其中三項與本卡去留無關、獨立有價值：

1. 21 張的逐張判定（可判定 6／Initiative 3／射程未定 12，逐張附「未定的是什麼」）
2. §5.3 的發現：`find_conflicts` 今天對現役可解析活卡就已漏報 10 組
3. 可重跑的母體探針（實測可原樣抽出、`ast.parse` 通過、端到端跑完）

### 恢復條件

任一成立即重開：(a) 比對集內同時出現兩張以上真正執行中且宣告相交的卡；(b) 判定語意由完全字串比對改為階層包含（屆時輸入覆蓋才開始有意義）；(c) 真的要動那 33 張卡。


## Comment 5330954365 · 2026-08-18T16:14:19Z

## 更正停卡理由：依跨家族查核裁決（2026-08-19）

跨家族查核對本卡裁決「**維持但條件**」——停卡成立，但**理由必須改寫**。原停卡留言（`issuecomment-5330286630`）與 handoff 證據中「機制沒有可證明的承載作用」這個論證有跳躍，本帖更正。⚠️ Log 是 append-only，原文不改寫，以本帖為準。

### 更正後的停卡理由（三條，取代原論證）

1. **補救路徑現不可行。** 本卡要補的 33 張卡，其 `amend --resources` 今天走不通——`parse_block` 先卡標題（`## 資源宣告（機器可讀；…）` 非獨立標題行），且**即使標題放寬後仍卡在缺哨兵**：實測 33 張的資源宣告區段內，`resource-claims` 的 begin/end 哨兵命中 **0/33**。
2. **歷史效益不可觀測。** `assign_cmd.py` 的拒絕分支只 `print` 到 stderr 並 `return 4`，該區塊 `append_log_line` 命中 0——互斥擋下派工在任何持久紀錄上不留痕。故「它擋過幾次」無法從歷史資料回答。
3. **效益尚未量測。** 目前沒有合成衝突測試、拒絕計數、誤拒率或真實並行時的衝突率。

### ⚠️ 明確撤回的說法

原論證由第 2 條推出「機制沒有可證明的承載作用」，並以此支撐停卡。**這個推論不成立**：

> 「未證明擋過」只能推出**歷史效益不可觀測**，不能推出**機制無價值**。預防性控制本來就可能很少觸發。

**本卡不再宣稱資源互斥機制無用。** 停卡的正當性完全落在第 1 條（路徑不可行）與第 3 條（效益未量測）——前者是機械事實，後者是待補的工作而非結論。

### 查核者指出的評估方式（記為後續，本卡不做）

合成衝突測試、拒絕計數、誤拒率、真實並行時的衝突率。⭐ 其中「拒絕計數」直接對應第 2 條的成因——`return 4` 那條路徑加一行留痕，「它擋過幾次」就從不可觀測變成可觀測。

### 不受影響的部分

交付物分支 `claude/mig1-claims-backfill-31` @ `6a910767bebfbb4cc1d70002b20e105f033055f2` 保留不刪；21 張的逐張判定、`find_conflicts` 對現役比對集漏報 10 組的發現、可重跑母體探針三項獨立有效；恢復條件三項不變。

### 一併更正的量測

原留言寫「今天的比對集：21 張，1 張在執行」。以 2026-08-19 完整母體重算（Project #4 快照 156 items、body 走 REST、parser SHA `ae8f74162797e2eed7180a1cd1ed6692fab3b6d3`）：

```
gate1 非終態                    : 70
gate2 且 is_owner_assigned      : 41
gate3 且 try_parse_block 可解析 : 20
分布：{'已合併': 5, '需求': 10, '阻塞': 3, '通過': 1, '規劃中': 1}
```

**20 張，0 張執行中。** 與 21 的差異是本卡停卡後掉出比對集。查核者已確認此重算正確。⚠️ 此數為時變量，引用時須連同快照、時點、parser SHA 與篩選條件一併釘住。

