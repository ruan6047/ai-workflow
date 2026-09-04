# #73 DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1 #47 的核心痛點只成立一半：main 回綠已證，同類事故會不會被機械擋下未證
- state: closed  created: 2026-08-12T22:31:08Z  closed: 2026-08-13T08:12:21Z
- url: https://github.com/ruan6047/ai-workflow/issues/73
- comments: 4

## Body

- 需求：—　規劃：—
<!-- wf-routing:v1 -->
- 執行：待指派（建議 經濟型；閘門已存在（#48 合併＋ruleset 生效），本卡是取證不是建設：造一個同類失敗、證明它在今天的閘門下合併不了。推理鏈短，難點只在「同類」的判準要能從 8/12 事故導出而非另造一個容易紅的例子。）　查核：待指派（建議 主力型；紅線：本卡的產出是「閘門有效」的證據，寫鬆了會讓一個未經證實的保護被當成已證實。查核重點在該證據是否真的重現 8/12 的形狀（分支自測綠、合併結果紅），而非任意紅色案例。建議跨家族。）
- Initiative：—　spec 基線：docs/ROADMAP.md（main 5ac61d2）§0 目標 1、§2 執行面、§5 finding 處置。#47 的 R1-001 disposition 逐字要求開本卡、不得回退 main，並由需求方裁定是否併入或明確依賴 #48。需求方 2026-08-13 裁定開卡。⚠️ 依 ROADMAP §5，開卡是需求方的排程判斷而非 disposition 直接決定——本卡的開立是需求方裁定的結果，不是因為查核者要求。
- DB：db_scope=none
- 服務的原始目標：把「同類事故會被機械擋下」從設定面推論變成實測證據

## 簡介
<!-- card-brief:begin -->
🏁 已完成：取證卡而非建設卡——造一個重現 2026-08-12 形狀的失敗（分支自測綠、merge-tree 判 CLEAN、合併結果才紅），並繞過 gh 直打 REST 取得伺服器端證據 HTTP 405 Required status check tests is failing，補上此 repo 至今缺的那一格「紅色 tests 直接擋下合併」（#61 關閉時是 DIRTY 不是 BLOCKED，只有設定面證據）。適用時機：要查閘門是不是真的有牙齒、或要引用「設定面證據 vs 直接證據」界線時。⛔ 非射程：不改 repo settings、不停用 ruleset 20768920；#47 的 R1-002（adfcbce 缺 trailer）不在射程，只在 docs/DEV_MAIN_RED_CAPABILITY_FLAGS1_FIX1.md 記為不可補正；未動 cli/、templates/、.github/ 下任何檔案。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：DEV-MAIN-RED-CAPABILITY-FLAGS1（#47）的核心痛點有兩段：main 回到綠燈、以及下次同型事故由機械攔下。查核者 R1-001 判定只成立第一段——被審 SHA 的 source tree 沒有 .github 路徑，本卡寫入也只有 fixture，沒有把完整測試接為合併前自動閘門；修補可在人為執行 pytest 時抓到同類漏旗標，卻不能防止未跑測試的合併。⚠️ 那個判定作出時閘門確實不存在；2026-08-13 之後不同：DEV-AIWF-MINIMAL-CI1（#48）已合併（CI 取合併結果）、required_status_checks ruleset 已套用生效（id 20768920、bypass_actors 0、strict true）。所以本卡不是建設而是【取證】：證明 8/12 那個形狀今天真的過不了閘門。⚠️ 缺的證據是特定的一種——閘門在 PR #71 上運作過（BEHIND → update-branch → CLEAN），但那是 strict 政策擋落後分支；「紅色 tests 直接擋下合併」至今【沒有直接證據】，#61 關閉時是 DIRTY 非 BLOCKED，接受的是設定面證據（見 docs/ROADMAP.md §2）。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:docs/DEV_MAIN_RED_CAPABILITY_FLAGS1_FIX1.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] ⚠️ 造一個【重現 8/12 形狀】的失敗並證明它今天過不了閘門。判準不是「任意紅色案例」——8/12 的形狀是：分支在自己的基線上測試為綠、併進 main 後才紅（語意衝突，git merge-tree 抓不到）。須說明你造的案例為何屬同一形狀。
- [ ] ⚠️ 取得【紅色 tests 直接擋下合併】的直接證據——mergeStateStatus 為 BLOCKED 或 gh pr merge 被拒的實際輸出。這是本 repo 至今缺的那一格：#61 關閉時是 DIRTY（衝突）不是 BLOCKED，故只有設定面證據。若你判定該證據在不破壞 main 的前提下取不到，明說並論證，不得以設定面證據替代後宣稱已證。
- [ ] 使用拋棄式 PR 與分支，取證後不合併地關閉、並清理分支。⚠️ 不得改 repo settings、不得刪除或停用 ruleset（id 20768920）——若取證需要暫時調整閘門，那本身就是證據不成立的訊號，改為論證為何取不到。
- [ ] #47 的 R1-002（adfcbce 缺三件式 trailer）【不在本卡射程】：該 commit 已在 main，補 trailer 只能改寫已推送歷史而本專案明令禁止。本卡只需在文件中記錄該缺口為不可補正的既成事實，不得宣稱已處理。DEV-COMMIT-TRAILER-GUARD1（#63）的檢查器已於 main 上線，可用它列出該筆。

## 驗證

- [ ] 凡寫下「會擋下」須附 CI run URL 與 gh pr view 的實際輸出；沒有直接證據的部分明列為未證。
- [ ] 確認未改動 cli/、templates/、.github/ 下任何檔案——本卡只新增設計與取證文件。
- [ ] 確認 ruleset id 20768920 在取證前後內容未變（gh api 回讀比對）。
## Log

- 2026-08-13T06:31:07+08:00 open by —；owner 待指派；iteration 0。
- 2026-08-13T06:34:07+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code 子agent；分支worktree claude/DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/dev-main-red-capability-flags1-fix1；交付狀態 🚧進行中；實際能力層級 經濟型（與卡面建議 經濟型 相符）。
- 2026-08-13T07:05:07+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA 97e9e7b53fb0cbc993e9140e2be333533798e005；證據 R1：⚠️ 補跑漏掉的 handoff——PM 於 assign 後直接派執行者、交回後未跑本指令卻把本卡列進協調者提示詞，查核者依契約查不到權威來源而判 review-invalid（DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1-R0-01，attribution=coordinator），該判定完全正確、本輪不計 attempt、查核者無過失，前向更正見 issuecomment。這是 PM 同期第五次漏跑 handoff。交付內容：取到了缺的那一格——繞過 gh 直打 REST endpoint 得 HTTP 405 Repository rule violations found / Required status check tests is failing，是伺服器端證據而非客戶端。它自己排除兩個會讓證據作廢的陷阱：先 update-branch 消掉 BEHIND（否則擋你的是 strict 不是紅叉，那是 PR #71 那種證據）、判定 gh pr merge 被拒不夠（客戶端讀 mergeStateStatus 自己不送出，依 ROADMAP §2 同一把尺是偵測器不是執行者）。同形狀論證：不模擬 8/12 而以同一機制重跑——基線同取 7451b72、merge-base --is-ancestor 26a0149 7451b72 為否、碰撞 main 上不存在的新增檔、缺同樣四個能力旗標、失敗同落 setup 期而非斷言期、argparse 訊息逐字相同；測試主題刻意與旗標無關（若寫成正面測那條剛改掉的契約，紅是同義反覆）。三段實測：分支基線 294 passed／merge-tree 對 main exit 0（舊判準今天依然放行）／合併結果 2 failed 726 passed；CI required run 自證 checked-out=58a9fef 是 merge commit 而非 head。PM 自審複驗：ruleset 20768920 逐欄與套用時相同、origin/main 仍 5ac61d2、PR #74 state=CLOSED mergedAt=null、worktree 數回到 21、寫入集單一 docs 檔、trailer 3/3、對 main merge-tree CLEAN。⚠️ 執行者自陳五項證明不了的，第 3、5 最該看：CI 上沒拿到「分支頭綠 vs 合併結果紅」的同時對照（push run 未出現、成因未查明、它不臆測，分支頭為綠只有本機證據）；ruleset 不在版控裡，被停用時 repo 內無任何偵測器會響，而該文件會繼續讀起來像已經安全。#47 的 R1-002 記為不可補正的既成事實、未宣稱處理。它並刻意未改 ROADMAP §2 的「未取得直接證據」限度——依 §5 那是需求方的排程判斷。。
- 2026-08-13T07:12:11+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5273867194 未經編輯，PM 依其取材規則（core_pain_resolved 起至 EOF）回讀重算相符。⚠️ 前一輪同一 SHA 曾判 review-invalid（handoff-authority-absent，attribution=coordinator）——成因是 PM 漏跑 handoff、卻把本卡列進協調者提示詞；該輪不計 attempt、查核者無過失，前向更正見 issuecomment-5273807501；core_pain_resolved yes；self_run 5 項；findings 0 項（blocking 0）；attempt DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1-e0-97e9e7b53fb0cbc993e9140e2be333533798e005。
- 2026-08-13T16:12:08+08:00 handoff by wf-cli → owner ruan6047；iteration 0；SHA 97e9e7b53fb0cbc993e9140e2be333533798e005；證據 跨家族查核（GPT-5@Codex）APPROVE，需求方授權後以 squash 合併入 main = 71df157（PR #83）。merge body 未含 Closes 以免自動關 Issue 觸發 illegal_terminal_before_cleanup。合併前已核對分支 head 等於受審 SHA 97e9e7b53fb0cbc993e9140e2be333533798e005，無查核後追加的碼；因 ruleset strict 要求與 base 同步，合併前以 update-branch 併入 main（僅同步、無新內容）。首次收尾被 merge_verified_remote 擋下（update-branch 產生的遠端 commit 未在本地物件庫，守衛刻意不代為 fetch），零動作未寫狀態面，fetch 後重跑。；收尾清理：已清除 worktree；本地分支、遠端分支 依授權保留（未刪除）。
- 2026-08-26T21:02:15+08:00 amend by wf-cli（op 198a873b）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:e9cfd8acbd51516a7a11e5f7ab1837b61c6bf220af1f092c7ace5e299586b0f2 (763 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5273741922 · 2026-08-12T22:56:55Z

<!-- wf-review-receipt:v1
card_id: DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1
source_sha: 97e9e7b53fb0cbc993e9140e2be333533798e005
report_sha256: 05284e5bca30e9cd912afc4401caf7279d439b5530f138eec62b01e7d1dde875
-->

取材規則：從本規則之後的下一個 'review_status:' 開始，到檔案結尾最後一個 LF 為止；UTF-8、LF、未 strip、不排除任何段落。

review_status: review-invalid
preflight_passed: false
invalid_reasons:
  - reason: "Issue #73 body contains no 'handoff by wf-cli' event; therefore no authoritative handoff SHA exists to authenticate this review target."
self_run:
  - command: "gh issue view 73 --repo ruan6047/ai-workflow --json body -q .body | grep 'handoff by wf-cli' | tail -1"
    observed: "no output; the authoritative handoff event required before review is absent"
  - command: "git rev-parse HEAD && git merge-base --is-ancestor 5ac61d2e32cb75c058a6f6bce797e67cf1e8491e HEAD"
    observed: "HEAD is 97e9e7b53fb0cbc993e9140e2be333533798e005; baseline ancestry exit status is 0, but this cannot substitute for a handoff authority"
previous_round_accepted_blocking_findings:
  - status: "首輪，無前輪 accepted blocking finding。"
    evidence: "Issue #73 Log has only open and assign entries; it has no prior review or handoff event."
findings:
  - finding_id: "DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1-R0-01"
    severity: major
    blocking: true
    finding_class: coordination
    attribution: coordinator
    root_cause_id: handoff-authority-absent
    evidence: "The mandated authority query against ruan6047/ai-workflow Issue #73 returns no last 'handoff by wf-cli' line, while the local worktree merely has HEAD 97e9e7b53fb0cbc993e9140e2be333533798e005."
    disposition: "Append a valid handoff event naming the intended full source SHA, then commission a fresh cross-family review; do not treat this invalid review as an accepted finding or an iteration."
out_of_scope_findings:
  - status: "none"
    evidence: "Stopped before substantive source, CI, PR, or ruleset verification because the required handoff authority is absent."


## Comment 5273807501 · 2026-08-12T23:04:50Z

## PM 認錯：#73 從來沒有 handoff 事件，查核者的 `review-invalid` 完全正確

`DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1-R0-01`（major、blocking、coordination、`attribution: coordinator`、`root_cause_id: handoff-authority-absent`）**成立**。PM 已複驗本卡 Log：

```
06:31:07  open by —；owner 待指派；iteration 0
06:34:07  assign by wf-cli → owner Claude Opus 5@Claude Code 子agent
（沒有 handoff）
```

PM `assign` 之後直接派了執行者，執行者交回後 **PM 沒有跑 `wfcli handoff --next-stage review`**，卻把本卡列進了給協調者的提示詞。**查核者依契約查權威來源、查不到、停手——那正是本 repo 花了整天在建立的行為。**

### 這是同一個錯的第五次

2026-08-12 至 13 之間，PM 漏跑 `handoff` 共五次：#38（宣告退回未寫事件）、#47（合併未留痕）、#52 與 #57（交回後未推進）、以及本卡。

**前四次都只讓狀態面失真；這一次讓一位查核者白跑一輪。** 而且它是最該被抓到的一次——PM 在同一份提示詞裡逐字寫著「權威是 Log 上最後一筆 `handoff` 事件的 SHA」，然後給了一張沒有那筆事件的卡。

### 處置

- **本輪不計為可計數 attempt**，`iteration` 不遞增。
- **執行者的交付未被實質查核**，`97e9e7b` 的內容一個字都還沒被檢驗過。
- PM 補跑 `handoff`，另發派審詞，重新委派查核。**查核者無過失。**

### PM 已獨立複驗的部分（供下一位查核者參考，仍為待查驗項）

執行者宣稱它未動閘門、未合併、已清理。**PM 回讀確認**：ruleset `20768920` 逐欄與套用時相同（`bypass_actors: 0`／`strict: true`／`checks: [tests]`／`enforcement: active`）；`origin/main` 仍為 `5ac61d2` 未前進；PR #74 `state=CLOSED`、`mergedAt=null`；`git worktree list` 回到 21。

**這些是 PM 的複驗，不是查核。實質內容仍待審。**

### 一項與本卡直接相關的機械缺口

`DEV-STATE-FACE-DRIFT-GUARD1`（#65，已開卡未派）要做的正是「由 Log 最後一筆事件推導應有狀態、與 Project 欄位比對」。**若它已落地，本次漏跑會在 `doctor` 上當場現形**——但它今天還在 Backlog，所以這一次仍然是靠一位查核者發現的。


## Comment 5273867194 · 2026-08-12T23:10:40Z

<!-- wf-review-receipt:v1
card_id: DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1
source_sha: 97e9e7b53fb0cbc993e9140e2be333533798e005
report_sha256: f46d83f7f66ea22d29e1b8ea052a435146b5b9a979c59518cda0fde761d261b3
-->

取材規則：從本規則之後的下一個 'core_pain_resolved:' 開始，到檔案結尾最後一個 LF 為止；UTF-8、LF、未 strip、不排除任何段落。

core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "git rev-parse HEAD; git merge-base --is-ancestor 5ac61d2e32cb75c058a6f6bce797e67cf1e8491e HEAD"
    observed: "HEAD=97e9e7b53fb0cbc993e9140e2be333533798e005；Issue Log 最後 handoff SHA 相同；基線祖先檢查 exit 0。"
  - command: "git diff --check 5ac61d2e32cb75c058a6f6bce797e67cf1e8491e..97e9e7b53fb0cbc993e9140e2be333533798e005; git diff --name-status 5ac61d2e32cb75c058a6f6bce797e67cf1e8491e..97e9e7b53fb0cbc993e9140e2be333533798e005"
    observed: "無 whitespace error；唯一變更為 docs/DEV_MAIN_RED_CAPABILITY_FLAGS1_FIX1.md，未改 cli/、templates/ 或 .github/。"
  - command: "git archive 78d3f805e4fa788ea71c4091caf7291e4a04cda4 | tar -x -C <temporary>/base; cd <temporary>/base/cli; uv run --frozen pytest -q"
    observed: "拋棄式副本重跑 294 passed，確認陳舊分支基線為綠。"
  - command: "git archive 34d0e6a383549a19e6b9eda9f9c179851cb2965d | tar -x -C <temporary>/merge; cd <temporary>/merge/cli; uv run --frozen pytest -q tests/test_gate_evidence_fix1.py"
    observed: "拋棄式合併提交重跑 2 failed；兩項皆於 setup 期以 SystemExit: 2 失敗，訊息逐字列出 --exec-capability、--exec-capability-reason、--review-capability、--review-capability-reason。"
  - command: "gh run view 31648039425 --repo ruan6047/ai-workflow --log; gh api repos/ruan6047/ai-workflow/rulesets/20768920"
    observed: "required CI run 的 checked-out=58a9fef16fbd71b1d6213a98f37a2b1b6edb015c，subject 明示 merge 34d0e6a 至 5ac61d2e；CI 為 2 failed、726 passed。現行 ruleset 20768920 為 active、bypass_actors=[]、strict=true，required check 為 tests。"
previous_round_accepted_blocking_findings:
  - status: "首輪，無前輪 accepted blocking finding。"
    evidence: "先前 R0-01 是因 handoff 缺失而 review-invalid；Issue Log 已補入 2026-08-13T07:05:07+08:00 handoff，該無效查核不計 attempt，非 accepted blocking finding。"
findings: []
scope_outside_findings:
  - note: "文件已明確保留 ruleset 非版控且無消失偵測器、UI／bypass 未實測、及未取得 CI 分支頭綠與合併結果紅的同時對照等限制；這些未被誤宣稱為本卡已證，且不擴入 finding 集合。"


## Comment 5273879331 · 2026-08-12T23:12:12Z

<!-- wf-review-event:v1 card_id=DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1 source_sha=97e9e7b53fb0cbc993e9140e2be333533798e005 attempt_id=DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1-e0-97e9e7b53fb0cbc993e9140e2be333533798e005 -->
## 查核裁決：APPROVE

- 卡：`DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1`　attempt_id：`DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1-e0-97e9e7b53fb0cbc993e9140e2be333533798e005`
- 查核者：GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5273867194 未經編輯，PM 依其取材規則（core_pain_resolved 起至 EOF）回讀重算相符。⚠️ 前一輪同一 SHA 曾判 review-invalid（handoff-authority-absent，attribution=coordinator）——成因是 PM 漏跑 handoff、卻把本卡列進協調者提示詞；該輪不計 attempt、查核者無過失，前向更正見 issuecomment-5273807501　escalation_epoch：0
- source_sha：`97e9e7b53fb0cbc993e9140e2be333533798e005`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-13T07:12:11+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git merge-base --is-ancestor 5ac61d2e32cb75c058a6f6bce797e67cf1e8491e HEAD`
  - HEAD=97e9e7b53fb0cbc993e9140e2be333533798e005；Issue Log 最後 handoff SHA 相同；基線祖先檢查 exit 0。
- `git diff --check 5ac61d2e32cb75c058a6f6bce797e67cf1e8491e..97e9e7b53fb0cbc993e9140e2be333533798e005; git diff --name-status 5ac61d2e32cb75c058a6f6bce797e67cf1e8491e..97e9e7b53fb0cbc993e9140e2be333533798e005`
  - 無 whitespace error；唯一變更為 docs/DEV_MAIN_RED_CAPABILITY_FLAGS1_FIX1.md，未改 cli/、templates/ 或 .github/。
- `git archive 78d3f805e4fa788ea71c4091caf7291e4a04cda4 | tar -x -C <temporary>/base; cd <temporary>/base/cli; uv run --frozen pytest -q`
  - 拋棄式副本重跑 294 passed，確認陳舊分支基線為綠。
- `git archive 34d0e6a383549a19e6b9eda9f9c179851cb2965d | tar -x -C <temporary>/merge; cd <temporary>/merge/cli; uv run --frozen pytest -q tests/test_gate_evidence_fix1.py`
  - 拋棄式合併提交重跑 2 failed；兩項皆於 setup 期以 SystemExit: 2 失敗，訊息逐字列出 --exec-capability、--exec-capability-reason、--review-capability、--review-capability-reason。
- `gh run view 31648039425 --repo ruan6047/ai-workflow --log; gh api repos/ruan6047/ai-workflow/rulesets/20768920`
  - required CI run 的 checked-out=58a9fef16fbd71b1d6213a98f37a2b1b6edb015c，subject 明示 merge 34d0e6a 至 5ac61d2e；CI 為 2 failed、726 passed。現行 ruleset 20768920 為 active、bypass_actors=[]、strict=true，required check 為 tests。

### findings（0，其中 blocking 0）

- （無）

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。
