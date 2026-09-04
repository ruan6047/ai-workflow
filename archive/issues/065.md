# #65 DEV-STATE-FACE-DRIFT-GUARD1 Project 交付狀態與 Log 最後一筆事件推導出的狀態可以不一致，而沒有任何東西會發現
- state: closed  created: 2026-08-12T15:00:32Z  closed: 2026-08-19T03:23:09Z
- url: https://github.com/ruan6047/ai-workflow/issues/65
- comments: 4

## Body

- 需求：—　規劃：—
<!-- wf-routing:v1 -->
- 執行：待指派（建議 經濟型；純比對：讀 Project 交付狀態、讀 Log 最後一筆事件、依動詞推導應有狀態、不符即報。難點只在推導表要窮舉（handoff 的三個 next-stage、review 的兩種結論、assign、amend 不改狀態），推理鏈短。）　查核：待指派（建議 經濟型；唯讀偵測器，不改任何狀態；查核重點在推導表是否窮舉、以及 false negative（有漂移卻不報）而非 false positive。跨家族非必要。）
- Initiative：—　spec 基線：docs/ROADMAP.md（main d735cad）§0 目標 1「防止低級事故」與 §5「finding 的處置」。需求方 2026-08-12 於總結後裁定執行本項與 WF-DISPATCH-FROM-HANDOFF1，判準是兩者最小、機械可判、且各自消滅一個當日重複發生的錯誤。ROADMAP §3 須同步登記。
- DB：db_scope=none
- 服務的原始目標：讓看板失真在下一次 doctor 就被發現，而不是等人問起

## 簡介
<!-- card-brief:begin -->
在 cli/src/wf_cli/doctor.py 加一條唯讀稽核 audit_state_face_drift：由 Log 最後一筆 lifecycle 事件推導該卡應有的交付狀態，與 Project 欄位不符即報，六格 handoff 推導表釘寫入端常數、表外組合一律 fail-closed 落「不判定」。**適用時機**：懷疑看板交付狀態與真實不符、要機械列舉漂移時；或要理解 live run 為何 74% 落在「不判定」（handoff Log 行不含 stage／status，20+ 筆零例外）時。⛔ 非射程：偵測不等於強制——doctor 唯讀，擋不住漏跑 handoff，強制面承接者是 CI（ai-workflow#48）；未接線 wfcli doctor（doctor_cmd.py 不在資源宣告內）；讓 handoff Log 行自帶 stage／status 屬寫入端另一張卡。⚠️ 對母卡痛點原形 #38／#47／#52／#57 零鑑別力且是結構性的：事件缺席時 Log 與欄位一起過期、彼此一致。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：2026-08-12 當日 PM 漏跑 wfcli handoff 四次，狀態面因此與真實不符且無人發現：#38 已宣告退回而狀態面停在待查核、#47 的碼早已在 main 而狀態面停在進行中（Log 最後一筆是當日下午的 assign，合併從未留痕）、#52 與 #57 執行者已交回而卡未推進。四筆全部是需求方問「目前其他項目有處理嗎我沒看到子代理在運行」才浮出來——也就是說在一個有四處失真的看板上做了數小時的調度決策。這是機械可判的：Log 最後一筆事件的動詞與參數足以推導出該卡此刻應有的交付狀態，與 Project 欄位比對即可。今天沒有任何東西做這件事。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/doctor.py",
    "file:cli/tests/test_doctor.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] doctor 新增一條唯讀檢查：由 Log 最後一筆 lifecycle 事件推導該卡應有的交付狀態，與 Project 欄位不符即報。⚠️ 推導表須窮舉並附輸出：handoff 的三個 next-stage、review 的 APPROVE／REQUEST_CHANGES、assign、amend（不改狀態）各自對應什麼。推導不出來的組合須明確落在「不判定」而非默認通過。
- [ ] ⚠️ 以當日四筆真實漂移回放證明有鑑別力：#38、#47、#52、#57 在各自漂移時點的 Log 與 Project 狀態。若無法取得歷史快照，須構造等價 fixture 並說明其忠實性。不得只證明「檢查會跑」。
- [ ] ⚠️ 偵測不等於強制。doctor 唯讀，它讓漂移可被列舉、不阻止任何人漏跑 handoff。交付報告須明列擋不住什麼，並指名強制面承接者（CI，#48）。不得宣稱「已預防」——WF-WORKTREE-REPO-OWNERSHIP1（#57）R1-01 正是因此被判 blocking。

## 驗證

- [ ] cd cli && uv run pytest -q 不得退化（基線自己跑）。
- [ ] 對現行 Project #4 全部未結案卡實跑並貼出輸出；凡寫下數字須附指令。
- [ ] 以突變注入證明有鑑別力：把推導表某一格改錯、或讓不一致回傳通過，測試須轉紅並附輸出。
## Log

- 2026-08-12T23:00:31+08:00 open by —；owner 待指派；iteration 0。
- 2026-08-19T05:50:22+08:00 assign by wf-cli → owner Claude Fable 5@Claude Code 子agent；分支worktree claude/state-face-drift-guard-65 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/state-face-drift-guard-65；交付狀態 🔨執行中；實際能力層級 高階型（偏離卡面建議 經濟型；偏離理由：卡面建議經濟型（純比對、推理鏈短），向上偏離理由：執行者為本會話子代理，繼承現行模型 Claude Fable 5（MODEL_ROUTING L3 等價）；且推導表在 PR #102 後由三個 next-stage 擴為六個、handoff Log 行可能不含 stage/status 資訊——邊界判定比開卡時多，另起經濟型模型的協調成本高於能力差價。射程不因高層級而擴大。）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-19T07:53:54+08:00 handoff by wf-cli → owner 待指派；iteration 0；SHA e5e2a267c49379efb149518dc0275074edf0034b；證據 執行交付（2026-08-19）：分支 claude/state-face-drift-guard-65（單一 commit e5e2a26 疊在 ae8f741），恰兩檔＝資源宣告（doctor.py +337、test_doctor.py +333），worktree 保留給查核者。PM 複驗：pytest 1037 passed（基線 1009，+28 全為新測試零舊測試改動）、contract_tool_reconcile --check exit=0、trailer 四件套齊。⭐ 執行者最重要的誠實發現：本軸對母卡痛點的四筆原形（#38/#47/#52/#57）**零鑑別力且是結構性的**——那四筆的失真形態是「該發生的事件沒寫」，事件缺席時 Log 與欄位一起過期、彼此一致，Log→欄位這條軸構造上看不見；卡面「Log 最後一筆事件足以推導應有狀態」的前提被實測推翻（handoff Log 行不含 next-stage 也不含 --status，20+ 筆零例外）。鑑別力正面證明改由等價形承擔：review 轉錄後欄位未跟上（half-write）→drift、欄位被手搬而無事件→drift，突變注入三例全紅還原回綠。live run 82 張未結案卡：一致 21／漂移 0／不判定 61（74%，主因 handoff_status_not_in_log 60）。⚠️ 執行中一次失誤已自癒如實揭露：突變測試 git checkout 還原時把未 commit 的實作退回基線，自 scratchpad 重建並全套重測後才 commit。⚠️ 未接線 CLI（doctor_cmd 不在宣告內），接線屬後續。查核重點建議：(a) 四筆原形零鑑別力是否構成對卡面預期的偏離而需需求方裁定——執行者判為「實測推翻前提」而非實作缺陷，已寫進測試 docstring；(b) 74% 不判定的正解在寫入端讓 handoff Log 行自帶 stage/status（首寫自描述），屬另一張卡，本卡唯讀不做——此射程劃界是否可接受；(c) doctor 實質讀 contract-baseline/checkpoint 事件但 scanner 看不見常數引用，CONTRACT_TOOL_RECONCILE.md:293 的 write-only 登記「scanner 視角為真、實質已過期」，處置表更新歸該檔持有者。。
- 2026-08-19T11:10:40+08:00 review by wf-cli → APPROVE（✅通過）；查核者 Google DeepMind Antigravity；core_pain_resolved yes；self_run 9 項；findings 2 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt DEV-STATE-FACE-DRIFT-GUARD1-e0-e5e2a267c49379efb149518dc0275074edf0034b。
- 2026-08-19T11:22:57+08:00 handoff by wf-cli → owner —（已合併）；iteration 0；SHA 2adcffac98264636c7a4c0cb219df2c51e2ff4d1；證據 release（2026-08-19）：R1 APPROVE（Google DeepMind Antigravity，跨家族）後合併。⚠️ ai-workflow 的 ruleset 20768920「main must be green」為 active、required check=tests、bypass_actors=0，故走 PR 不可直推：被審 e5e2a26 rebase 至 4e6925e 上為 2adcffa（內容保真：git diff e5e2a26 2adcffa 恰為 #108 帶進的 docs/ROADMAP.md，被審兩檔逐位元未動；trailer 4 行），PR #109 兩個 check 皆 pass 後 squash merge。merge 後驗：doctor.py 的 audit_state_face_drift 已在 origin/main。交付內容：唯讀漂移稽核純函式，六格 handoff 表釘寫入端常數、表外值一律 fail-closed undecidable、三重突變注入紅綠、live run 159 張 0 false drift。查核者 2 findings 皆 info／非 blocking：對帳器 AST 跨模組常數盲區（external）、handoff Log 格式缺交付狀態欄致 74% 不判定（planner，屬寫入端另一張卡）。⚠️ 已知未接線：doctor_cmd.py 不在本卡資源宣告內，wfcli doctor 尚無旗標觸發此檢查，接線屬後續卡。；收尾清理：已清除 worktree；遠端分支 本來就不存在；本地分支 依授權保留（未刪除）。
- 2026-08-26T21:10:55+08:00 amend by wf-cli（op 79a7796f）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:73b6b2775028e318d15aa9ef5c3d2f4a4fd101da14d561eb792e74b8038d5366 (897 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5334492654 · 2026-08-18T21:51:04Z

## 派工包：`DEV-STATE-FACE-DRIFT-GUARD1`（2026-08-19）

**基線**：`ae8f74162797e2eed7180a1cd1ed6692fab3b6d3`（origin/main，分支自此建出）
**分支／worktree**：`claude/state-face-drift-guard-65` @ `/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/state-face-drift-guard-65`
**能力層級**：高階型（偏離建議經濟型，理由見 claim 事件）
**契約**：卡面 3 條驗收＋3 條驗證。

### ⚠️ 卡面過期處，以機器現實為準（開卡於 2026-08-12，PR #102 於 08-18 落地）

1. 驗收條 1 寫「handoff 的三個 next-stage」——現行是**六個**（`handoff_cmd.py:87-95` 的 `STAGE_STATUS`：requirement→💡需求、research→🔬研究中、planning→🧭規劃中、implementation→🔨執行中、review→🔍待查核、release→🏁完成）。「窮舉」的要求管轄「三個」的字面：推導表必須蓋六個。
2. 推導表另須涵蓋：`review`（APPROVE→✅通過／REQUEST_CHANGES→↩退回）、`assign`（預設 🔨執行中，⚠️ `--status` 是無 choices 自由文字）、`amend`（不改狀態）、`open`（初始狀態）。
3. ⚠️ **handoff 與 assign 都有 `--status` 覆寫**（自由文字）。Log 行未必含 stage 或 status——**先實測 Log 行的實際欄位**（讀真卡的 `## Log`，如 cpbl#139/#149 有今日完整生命週期），推導不出來的組合依卡面明確落「不判定」，並在報告量化「不判定」佔比。
4. 已知的真實漂移樣本可當鑑別力素材：`#85` closed/completed 卻 🛑已停止、`#12` closed/not_planned 卻 🏁完成（A 輪盤點 2026-08-19 實測）——這兩筆是 stateReason 軸，若你的檢查軸是 Log→交付狀態，說明它們在不在射程，不在就明列。

### 射程（硬邊界）

只准改 `cli/src/wf_cli/doctor.py` 與 `cli/tests/test_doctor.py`（＝資源宣告）。**doctor 唯讀**——不得加任何寫入、不得改其他動詞。驗收條 3 的紀律照卡面：不得宣稱「已預防」，報告明列擋不住什麼並指名強制面承接者。

### 工具事實（省你踩坑）

- `gh project item-list --format json`：中文欄位名首位元組壞成 U+FFFD（用 endswith 後綴比對）；**body 在 `content.body`（156/156 有值），不必走 REST**。
- 卡面標題格式：ai-workflow 是 `CARD-ID 說明`（半形空格）；cpbl 混用全形冒號。
- `## Log` 有資源宣告哨兵歷史回音；切 Log 用獨立標題行判定。
- worktree 內 `uv run` 自動 sync venv。

### 交付紀律

- ⚠️ 報告中凡「實測／窮舉／全庫／逐字／唯一／零命中」，同句數字與列舉必須附指令＋原始輸出，否則寫「未驗」。
- commit 帶 trailer 四件套（參照 cpbl `374be1b` 同形：Requested-by ruan6047／Planned-by Claude Fable 5@Claude Code (PM)／Implemented-by 你的 claim 身分／Co-Authored-By）。commit 後跑一次完整 `uv run pytest -q` 確認（基線 1009 passed）。
- Conventional Commits；push 分支不碰 main；worktree 保留給查核者。
- 報告必含：逐條驗收狀態與證據、突變注入的紅綠輸出、**沒驗到的／未證實假設／失敗或不如預期**（不得省略）、5xx/空回應標 UNKNOWN。
- 不跑任何 wfcli 寫入動詞；讀行為用 `--help` 或讀碼。


## Comment 5335725270 · 2026-08-18T23:54:38Z

# 跨家族查核委託：`ai-workflow#65 DEV-STATE-FACE-DRIFT-GUARD1` @ `e5e2a267c49379efb149518dc0275074edf0034b`（2026-08-19）

你是跨家族查核者，無 wfcli 寫入通道——產出文字裁決＋findings，由需求方轉貼、PM 轉錄。全程唯讀；收尾回報兩棵真樹 `git status --porcelain -uno` 為空。

## 環境

```
worktree（進駐唯讀）  /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/state-face-drift-guard-65
被審分支             claude/state-face-drift-guard-65（單一 commit e5e2a26 疊在 ae8f741）
改動                 cli/src/wf_cli/doctor.py +337、cli/tests/test_doctor.py +333（恰＝資源宣告）
契約                 卡面 3 條驗收＋3 條驗證＋派工包 issuecomment-5334492654（含卡面過期修正：next-stage 三→六）
```

進駐第一件事：`git rev-parse HEAD` 與 source_sha 逐字相同、工作區乾淨；不同即 review-invalid。

## 第一判準（具否決權）

核心痛點是「看板失真無人發現」。⭐ **執行者自己交出了最重要的反面事實**：本軸對母卡痛點的四筆原形（#38/#47/#52/#57，全是「該發生的事件沒寫」型）**零鑑別力且結構性**——事件缺席時 Log 與欄位一起過期、彼此一致。卡面「Log 最後一筆事件足以推導應有狀態」的前提被實測推翻（handoff Log 行不含 next-stage/--status，執行者稱 20+ 筆零例外——**抽真卡複驗這句**）。

你要裁的第一題：**痛點算不算已消？** 本軸抓得到的是「事件已寫而面沒跟上」與「面被手搬」兩型（等價形 fixture 證明），抓不到的是「事件沒寫」型（正是 08-12 那四筆）。執行者的處置是據實揭露＋指名寫入端修法屬另一張卡。判：這是「誠實的部分交付」還是「痛點未消 → REQUEST_CHANGES（spec 缺陷，attribution: planner）」。

## 要驗的

1. **推導表窮舉性**：`test_drift_handoff_table_is_exhaustive_and_pinned_to_writer` 斷言 `set(表)==set(STAGE_STATUS)|{"release"}`——親跑；並驗六格值逐格釘 writer 常數（同一性非複本）。
2. **不判定不默認通過**：8 個參數化案例 verdict 恆 undecidable——親跑；再自己構造一個表外狀態值攻擊。
3. **突變注入**：三例（表格改錯 ×2、比對恆真）紅→還原綠——親跑至少 M3（6 測試轉紅那個）。
4. **live run 數字**：82 張、一致 21／漂移 0／不判定 61（74%）——可用執行者的驅動方式重跑或抽查。⚠️ `gh project item-list` 中文欄位名首位元組壞成 U+FFFD（endswith 比對）；body 在 `content.body`。
5. **fixture 忠實性**（驗收 2 的回放）：Log append-only 論證＋逐字取自真卡——抽 #47 一筆對原卡。
6. **pytest 1037 passed／reconcile --check exit=0**——PM 已在 worktree 複驗過，可質疑方法。
7. ⚠️ **執行者自報的失誤**：突變測試時 `git checkout --` 把未 commit 實作退回基線、自 scratchpad 重建。驗最終 commit 完整性（測試全過即可，重點是有無重建遺漏的形狀——如 docstring 引用了不存在的東西）。
8. ⚠️ **scanner 盲區自報**：doctor 實質讀 contract-baseline/checkpoint 事件（經 `_TRANSPARENT_EVENT_PREFIXES` 常數），`CONTRACT_TOOL_RECONCILE.md:293` 的 write-only 登記實質已過期而 `--check` 看不見。判這個「為了不弄紅別人的檔而繞開 scanner」的處置可否接受，或該列 finding（該檔不在本卡資源宣告內）。

## 回報格式

裁決 `APPROVE`／`REQUEST_CHANGES`＋理由；findings 結構化欄位（finding_id／severity: critical|major|minor|info／blocking／finding_class／attribution／root_cause_id／evidence 附指令與輸出／disposition）；`core_pain_resolved` 你的第一題答案；`self_run` 至少含親跑的測試與突變；⭐ 沒驗到的不得省略；5xx/空回應標 UNKNOWN。報告不得含 wfcli 查核事件 marker 前綴字面。


## Comment 5337032145 · 2026-08-19T03:10:42Z

<!-- wf-review-event:v1 card_id=DEV-STATE-FACE-DRIFT-GUARD1 source_sha=e5e2a267c49379efb149518dc0275074edf0034b attempt_id=DEV-STATE-FACE-DRIFT-GUARD1-e0-e5e2a267c49379efb149518dc0275074edf0034b -->
## 查核裁決：APPROVE

- 卡：`DEV-STATE-FACE-DRIFT-GUARD1`　attempt_id：`DEV-STATE-FACE-DRIFT-GUARD1-e0-e5e2a267c49379efb149518dc0275074edf0034b`
- 查核者：Google DeepMind Antigravity　escalation_epoch：0
- source_sha：`e5e2a267c49379efb149518dc0275074edf0034b`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-19T11:10:40+08:00

### self_run（查核者實跑）

- `uv run pytest tests/test_doctor.py -k "handoff_table_is_exhaustive or review_table_is_pinned or open_initial_status_is_pinned" -v`
  - 3 passed in 0.03s；六格 handoff 表逐格等於 handoff_cmd.STAGE_STATUS（第六格 release 釘寫入端字面 🏁完成）、review 表逐字鏡射 review.STATUS_BY_RESULT、open 初始釘 Card.delivery_status 預設且斷言 open_cmd 無 --status 旋鈕
- `uv run pytest tests/test_doctor.py -k test_drift_handoff_is_undecidable_never_default_pass -v`
  - 8 passed in 0.02s（六個 stage 對應狀態＋🛑已停止／🚨已升級）
- `查核者主動構造表外狀態攻擊：['🛸外星狀態','未知狀態','','⏸阻塞','📦已合併','任意自訂值',' ','NULL','12345']`
  - 全數 verdict==undecidable、rule==handoff_status_not_in_log、expected_status is None——無任何 default pass
- `突變注入三組（M1 planning 格改 🔨執行中／M2 APPROVE 格改 🏁完成／M3 doctor.py:1405 比對式改 if True）`
  - M1 handoff 表測試轉紅（assert '🔨執行中' == '🧭規劃中'）；M2 review 表測試轉紅（Differing items {'APPROVE': '🏁完成'}）；M3 恰 6 個測試轉紅（open/assign/review 三個 drift 案例＋兩個等價形＋render）。git checkout -- 還原後 28/28 全綠
- `gh project item-list 4 --limit 200 批次跑 audit_state_face_drift`
  - 159 張：consistent 20／drift 0／undecidable 139（handoff_status_not_in_log 126、no_log_section 12、log_section_ambiguous 1）。執行者報的 82 張／21／0／61 是未結案卡子集，分母擴大後仍維持 0 false drift
- `抽查線上 483 筆真實 handoff 留痕的欄位組成`
  - 僅含 owner／iteration／SHA／證據，從不攜帶 --next-stage 或交付狀態（僅偶見於自由文字證據段）
- `gh issue view 47 原卡 Log 對照 fixture`
  - 2026-08-12 21:14 補跑前確實僅 13:47 open 與 13:50 assign（交付狀態 🚧進行中），狀態欄 🚧進行中——fixture 忠實
- `cd cli && uv run pytest；uv run python scripts/contract_tool_reconcile.py --check`
  - 1037 passed in 59.39s 全綠；reconcile exit=0（54 個缺口全部有登記處置）
- `AST 解析＋docstring 符號逐一查驗（HANDOFF_STAGE_EXPECTED_STATUS/REVIEW_RESULT_EXPECTED_STATUS/OPEN_INITIAL_STATUS/_TRANSPARENT_EVENT_PREFIXES/RULE_*/UNDECIDABLE_*/StateFaceDriftFinding/parse_log_events/derive_expected_status/audit_state_face_drift/render_state_face_drift）`
  - 無語法錯誤、全數存在且型別標註完整、無重建遺漏形狀

### findings（2，其中 blocking 0）

- **DEV-STATE-FACE-DRIFT-GUARD1-R1-01**　severity=info　blocking=false　class=implementation　attribution=external　root_cause_id=`reconcile-cross-module-constant-ast-blind-spot`
  - evidence：查核者原編號 FINDING-65-01；原 finding_class 用詞 observability-gap、原 attribution 用詞 tooling-limitation（schema 列舉皆無此值，轉錄映射為 implementation／external，原詞保留於此）。指令 grep -n BASELINE_LOG_TAG cli/src/wf_cli/doctor.py → 1205: BASELINE_LOG_TAG,。doctor.py 使用 review.py 匯入之常數，使 contract_tool_reconcile.py 未將其計入 event/contract-baseline 的 AST reader，CONTRACT_TOOL_RECONCILE.md:293 維持 write-only。
  - disposition：處置可接受。doctor.py 遵循 DRY 重用常數，且 CONTRACT_TOOL_RECONCILE.md 不在本卡資源宣告內。建議後續由對帳器增強卡統一升級 AST 常數追蹤能力。
- **DEV-STATE-FACE-DRIFT-GUARD1-R1-02**　severity=info　blocking=false　class=implementation　attribution=planner　root_cause_id=`handoff-log-format-omits-status-field`
  - evidence：查核者原編號 FINDING-65-02；原 finding_class 用詞 design-gap（映射為 implementation，原詞保留於此）。指令 grep -A 5 'def write_status_face' cli/src/wf_cli/commands/handoff_cmd.py → append_card_log(f"handoff by wf-cli → owner {args.to}；iteration {new_iteration}；SHA {args.source_sha}；證據 {args.evidence}{cleanup_note}。")。handoff Log 格式缺交付狀態欄位，導致所有以 handoff 結尾的卡在推導時必定落入 undecidable。
  - disposition：不阻擋本卡交付。此屬 handoff_cmd 寫入端格式修訂，屬寫入端治理卡射程。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: DEV-STATE-FACE-DRIFT-GUARD1-e0-e5e2a267c49379efb149518dc0275074edf0034b
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待指派
findings:
  - finding_id: DEV-STATE-FACE-DRIFT-GUARD1-R1-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: implementation
    attribution: external
    root_cause_id: reconcile-cross-module-constant-ast-blind-spot
    counting_eligible: false
  - finding_id: DEV-STATE-FACE-DRIFT-GUARD1-R1-02
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: implementation
    attribution: planner
    root_cause_id: handoff-log-format-omits-status-field
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5337720455 · 2026-08-19T04:57:58Z

## ⚠️ 留痕補正：本輪裁決無 `wf-review-receipt:v1` 收據（2026-08-19，PM）

`templates/dispatch-package.md:55` 逐字要求「查核者先在被審 Issue conversation 或 PR review body 留 `wf-review-receipt:v1`（`card_id`、完整 `source_sha`、查核報告 UTF-8 `report_sha256`）」，且「PM 僅能逐字轉錄與收據 hash 相符的報告……**不能以 `--reviewer` 自由字串代替收據**」。

**本卡的 review 事件不符合這條紀律**，據實記錄：

- 本卡收據數 **0**（`gh api .../comments --jq "[.[]|select(.body|test(\"wf-review-receipt\"))]|length"`）。
- `--reviewer` 欄是 PM 打的自由字串，**非可驗證身分**。查核者的實際身分由需求方口頭轉述，機械上無從驗證。
- `wfcli doctor --review-channel` 對本卡回報 `[recorded]`（三面一致）——⚠️ **它驗的是事件／Log／Project 三面是否一致，而三面都是 PM 寫的，自然一致；收據缺席它看不見。**

**不追溯本筆裁決**，理由三項：(1) 裁決的實質內容經 PM 逐項獨立複驗（非僅信任查核者），複驗指令與輸出見本卡 review 事件的 self_run 與 PM 補正段；(2) 收據機制假設查核者能寫 GitHub，而跨家族查核者**沒有寫入通道**（既有事實），故該紀律在現行「需求方轉貼」通道上**構造上無法遵守**；(3) 追溯需重跑查核，成本遠高於風險。

機制缺口另開卡處理（承接卡見 ai-workflow）。本帖僅為留痕，不改變本卡狀態。
