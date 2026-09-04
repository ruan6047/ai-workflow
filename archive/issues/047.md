# #47 DEV-MAIN-RED-CAPABILITY-FLAGS1 main 為紅：test_release_cleanup.py 的 fixture 缺 open 的四個必填能力旗標
- state: closed  created: 2026-08-12T05:47:58Z  closed: 2026-08-18T21:49:19Z
- url: https://github.com/ruan6047/ai-workflow/issues/47
- comments: 3

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code PM
<!-- wf-routing:v1 -->
- 執行：待指派（建議 經濟型；單檔 fixture 補四個旗標，真因已由 PM 定位到具體錯誤訊息與引入 commit；推理鏈短。）　查核：待指派（建議 經濟型；低風險修復，查核只需確認 main 轉綠且未改動被測行為；不涉紅線。）
- Initiative：—　spec 基線：PM 於 2026-08-12 合併 WF-CLEANUP-GUARD1 後在 origin/main 5d22a7f 實跑發現。錯誤訊息逐字：argparse.ArgumentError: the following arguments are required: --exec-capability, --exec-capability-reason, --review-capability, --review-capability-reason。
- DB：db_scope=none
- 服務的原始目標：讓 main 回到綠燈，並讓下次同型事故被機械攔下而不是靠人記得

## 簡介
<!-- card-brief:begin -->
🛑 已停止：原為修 cli/tests/test_release_cleanup.py 的 fixture，補上 WF-CLI-ROUTING-TIER1（#21）改為必填的四個能力旗標，讓 2026-08-12 因陳舊基線語意衝突而轉紅的 origin/main（644 passed／14 errors）回綠；碼已在 main（adfcbce），事後查核兩條 blocking 分別由 ruleset 20768920 與 #73 結清，需求方 2026-08-19 裁定停卡。適用時機：要查「分支自己測是綠的、併進 main 才紅」這個形狀的原始事故與其處置時；或要引用 git merge-tree 是文字比對、抓不到語意衝突的實例時。⛔ 非射程：本卡不建立 CI（屬 DEV-AIWF-MINIMAL-CI1／#48）；adfcbce 缺三件式 trailer 記為不可補正的既成缺口，見 DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1（#73）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：origin/main 5d22a7f 實跑為 644 passed, 14 errors，全部在 cli/tests/test_release_cleanup.py。真因是陳舊基線的語意衝突：該檔的 fixture 呼叫 wfcli open 時未帶四個能力旗標，而那四個旗標由 WF-CLI-ROUTING-TIER1（#21）改為必填，且 #21 是在 7451b72 之後才併入——WF-CLEANUP-GUARD1（#25）的分支基線正是 7451b72，故它在自己的工作樹上 388 passed 是真的，測試從未見過那四個必填旗標。PM 合併時只做了兩件事：git merge-tree 確認文字無衝突、以及在分支自己的基線上跑測試，從未在合併後的結果上跑過一次。git merge-tree 抓不到語意衝突，而本 repo 沒有 CI（repo 根無 .github/），所以沒有任何東西會攔。attribution=coordinator。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/tests/test_release_cleanup.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 修好 fixture 使 origin/main 的測試全綠。修法須是補上那四個必填旗標，不得改動被測行為、不得放寬 open 的必填要求來遷就測試——後者會撤銷 #21 交付的閘門。
- [ ] 窮舉全 repo 是否還有其他呼叫 wfcli open 而未帶四旗標的地方（測試、腳本、文件內可執行區塊皆算），不得只修這一檔就宣稱處理完畢。窮舉須由指令輸出產生。
- [ ] 本卡不建立 CI——那由 DEV-AIWF-MINIMAL-CI1 承接。但須在交付報告指名：若沒有 CI，同型事故會再發生，且下一次未必像 fixture 這麼好修。

## 驗證

- [ ] 以乾淨的 git archive 取 origin/main 疊上本卡修法後實跑 pytest，貼出前後數字。基線自己跑，不要抄卡面數字。
- [ ] 證明修法未改動任何被測行為：diff 只動 fixture 的引數，不動斷言。以 git diff -U0 過濾 assert 行為空佐證。
- [ ] 窮舉輸出列出全部命中與各自處置。
## Log

- 2026-08-12T13:47:57+08:00 open by Claude Opus 5@Claude Code PM；owner 待指派；iteration 0。
- 2026-08-12T13:50:53+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code 子agent；分支worktree claude/DEV-MAIN-RED-CAPABILITY-FLAGS1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/dev-main-red-capability-flags1；交付狀態 🚧進行中；實際能力層級 經濟型（與卡面建議 經濟型 相符）。
- 2026-08-12T21:14:57+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA adfcbce0c9526f893f1e12abf3668366dc5fe50b；證據 ⚠️ 補記漏跑的事件。本卡的碼**早已在 main**（adfcbce 是 origin/main 祖先，PR #49 合併於 2026-08-12），但 Log 上最後一筆事件是同日 13:50:53 的 assign——合併從未留痕，狀態面因此停在 🚧進行中 直到需求方於同日詢問「其他項目有處理嗎」才發現。這是 PM 同日第四類漏跑 handoff 的一例（另：#38 宣告退回未寫事件、#42 貼派審詞未 handoff、#39 跳過 implementation handoff、#57／#52 交回後未推進）。合併當時需求方明確裁定「直接合併、事後補查核」，理由是 main 為紅（644 passed, 14 errors）阻塞全部並行卡；該裁定成立，但**其中的「事後補查核」至今未執行**。本次 handoff 即為把那筆欠下的查核放回佇列，不是宣稱已查核。被審內容：cli/tests/test_release_cleanup.py +12/-0，補上 WF-CLI-ROUTING-TIER1（#21）把四個能力旗標改為必填後、該 fixture 從未見過的旗標；零斷言變更。⚠️ 查核者須知本卡的特殊性：它已在 main，故本輪查核不是合併閘門而是事後稽核——若判 REQUEST_CHANGES，處置是開修復卡而非回退 main，該判斷請明講。。
- 2026-08-12T22:28:20+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5267830013 未經編輯，PM 依其 delimiter（report-begin/end、去前導 LF）回讀重算 report_sha256=d6389865… 相符；core_pain_resolved no；self_run 5 項；findings 2 項（blocking 2）；attempt DEV-MAIN-RED-CAPABILITY-FLAGS1-e0-adfcbce0c9526f893f1e12abf3668366dc5fe50b。
- 2026-08-12T22:37:50+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 1；SHA adfcbce0c9526f893f1e12abf3668366dc5fe50b；證據 兩項 blocking，皆 governance。R1-001（planner, missing-platform-merge-gate）：核心痛點兩段只成立一段——main 恢復綠已證（隔離 archive 基線 644 passed 14 errors → 被審 658 passed），但被審 SHA 無 .github 路徑、本卡寫入只有 fixture，未把測試接為合併前閘門。R1-002（executor, commit-trailer-required-but-missing）：三個必填 trailer 全缺，而碼已在 main、不得 amend 或回退。⚠️ 查核者的 disposition 逐字要求開 DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1 修復卡、不得回退 main，並由需求方裁定該卡是否併入或明確依賴 #48。⚠️ root_cause_id 分岔實況：本卡用 commit-trailer-required-but-missing、#52 用 governance-provenance-trailer-omission、#48 用佔位字串——同一缺陷四張卡三個名字，升級門檻數不到 3，已由 #63 承接統一。。
- 2026-08-17T21:35:05+08:00 handoff by wf-cli → owner —（降級 Backlog）；iteration 1；SHA 6561e04fe629e1915cbcfc5638f80c73054e67ae；證據 2026-08-17 PM 複驗：本卡 R1 兩條 blocking 的 disposition 皆為「需求方須開 DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1 修復卡」，而該卡即 #73，已於 2026-08-13T07:12 跨家族查核 APPROVE、core_pain_resolved=yes、CLOSED。R1-001（平台合併防線）由 ruleset 20768920（~DEFAULT_BRANCH、bypass_actors=0、strict=true、required check tests）於 2026-08-13 套用生效結清，限度見 ROADMAP.md:136-137（未取得紅色 check 直接擋下合併的直接證據，需求方裁定接受設定面證據）。R1-002（adfcbce 缺三件式 trailer）由 #73 判為不可補正的既成缺口，記於 docs/DEV_MAIN_RED_CAPABILITY_FLAGS1_FIX1.md:238-243，明載不宣稱已修復。本卡自 2026-08-12T22:37 handoff 回 implementation 後五日無人承接，實際已無可執行工作。依 ROADMAP.md §3「降級不是關閉——它們載有真實 finding 的紀錄，關掉會讓那些發現消失；降級可逆，關閉不可逆」，降級為 Backlog 而不關閉 Issue。⚠️ 顯式保留 iteration=1：本次無新 attempt，不得遞增。。
- 2026-08-19T05:49:12+08:00 handoff by wf-cli → owner —（已停止）；iteration 1；SHA ae8f74162797e2eed7180a1cd1ed6692fab3b6d3；證據 停卡（2026-08-19，需求方依 B 輪存廢研究裁定）：核心痛點「main 為紅」已消——本機同 SHA 實跑 cd cli && uv run pytest -q 得 1009 passed；修復卡 #73 已 APPROVE/CLOSED（2026-08-13）；ROADMAP 自陳本卡已無可執行工作且五日無人承接。ROADMAP §3「關閉不可逆」的前提經 B 輪實測推翻：closed issue 的 body 與留言全文保留、gh issue reopen 存在，關閉不滅證。⚠️ 據實記錄：ai-workflow main 於 2026-08-18T12:07Z 起有一筆紅 run（32135147377），根因是 setup-uv 基礎設施 flake 非碼缺陷（本機同 SHA 全綠），已於本日 rerun——該事件屬 #65 的射程（狀態面失真無人發現），不構成本卡復活理由。。
- 2026-08-26T21:01:34+08:00 amend by wf-cli（op 1715e9f9）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:5360b9db374762939e53b82a7d4800b0b1a251409c0a4b1a3c59cb4fce74d64b (776 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5267594976 · 2026-08-12T13:40:05Z

## 派審：#47 `DEV-MAIN-RED-CAPABILITY-FLAGS1` R1（⚠️ 事後稽核，非合併閘門）

⚠️ 審核對象 **`ruan6047/ai-workflow#47`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/dev-main-red-capability-flags1
分支：claude/DEV-MAIN-RED-CAPABILITY-FLAGS1　　被審 SHA：adfcbce0c9526f893f1e12abf3668366dc5fe50b
基線：5d22a7f3da57a3790179e999d9d28262fda4d19a　　iteration：0（首輪）
寫入集：cli/tests/test_release_cleanup.py 單檔（+12/-0，零刪除、零斷言變更）
```

> **權威來源**：本則與 Log 最後一筆 `handoff` 的 `SHA` 必須一致；不符時**以 handoff 事件為準並回報**。

### ⚠️ 這張卡的碼已經在 main 裡了，請先讀完這一節再開始

`adfcbce` **是 `origin/main` 的祖先**（PR #49，2026-08-12 合併）。**本輪查核不是合併閘門，是事後稽核。**

成因：2026-08-12 main 為紅（`644 passed, 14 errors`），阻塞全部並行卡。需求方當時明確裁定「**直接合併、事後補查核**」。合併做了，**而那筆「事後補查核」直到今天才被放回佇列**——Log 上最後一筆事件停在同日 13:50:53 的 `assign`，合併從未留痕，狀態面顯示 🚧進行中 直到需求方詢問「其他項目有處理嗎」才被發現。**這是 Coordinator 的漏，不是執行者的。**

**因此請明確裁示一件事**：若你判 REQUEST_CHANGES，處置是**開修復卡**而非回退 main。請在 disposition 裡把這一點講清楚，不要留給 PM 推測。

### 一、被審內容

main 變紅的機制：本卡的基線 `7451b72` 早於 `WF-CLI-ROUTING-TIER1`（#21）把四個能力旗標改為必填的那次合併。分支自己的工作樹 388 passed 為真，**併進 main 卻產生 14 個 error**——`git merge-tree` 是文字比對，抓不到這種語意衝突。

修法：`cli/tests/test_release_cleanup.py` **+12 行、0 刪除**，補上該 fixture 從未見過的四個能力旗標。**零斷言變更。**

**請攻擊**：(a) 12 行是不是最小修法，還是掩蓋了更深的問題（例如那個 fixture 本來就不該手工組旗標）？(b) `open` 的旗標補了，**`assign --actual-capability` 是否也在同一次 breaking change 的射程內**——PM 當時只講了 `open` 的部分，那是不完整的陳述。

### 二、這張卡的存在本身是一個代價實例，請一併判斷

它是 PM 連續合併三張卡、每次只跑 `git merge-tree` 確認文字無衝突並在**分支自己的基線**上跑測試、**從未在合併後的結果上跑過**所造成的。同一個檢查 `WF-RESOURCE-BLOCK-ANCHOR1` 的執行者自己做了（開臨時 worktree 試合併 `origin/main` 跑 562 passed），PM 沒做。

該缺口已由 `DEV-AIWF-MINIMAL-CI1`（#48）承接，**但 #48 至今未通過查核**（三項 blocking 開著，且卡在一個環：證明 CI 會擋人須先讓 CI 存在於 main）。

**請判斷**：本卡的 `core_pain_resolved` 只看「main 是否恢復綠」（`e1b33d8` 現為 701 passed），還是應把「同類事故會不會再發生」納入？**兩個方向都正當**，但本卡寫入集只有一個測試檔，射程判斷請明講。

### 三、環境事實

本卡的 commit **沒有** `AGENTS.md:10` 要求的三個 trailer——今日全批問題（今日落 main 的 31 筆帶 `Implemented-by` 者 0 筆），已由 `DEV-COMMIT-TRAILER-GUARD1`（#63）統一承接。**你可判定本卡是否同樣 blocking，但請注意本卡的碼已在 main、補 trailer 只能改寫已推送歷史，而本專案明令禁止。**

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5267830013 · 2026-08-12T13:59:52Z

<!-- wf-review-receipt:v1
card_id: DEV-MAIN-RED-CAPABILITY-FLAGS1
source_sha: adfcbce0c9526f893f1e12abf3668366dc5fe50b
report_sha256: d6389865526d35a534aa38192669ce3b0a428dff0dd9f95b169061d97d9708d6
-->

取材規則：被雜湊範圍從本規則之後的下一個 `--- report-begin ---` delimiter 後第一個 LF 後的第一個位元組起，到本規則之後的下一個 `--- report-end ---` delimiter 前一個 LF 為止；UTF-8、LF、未 strip；排除收據 HTML 註解、取材規則與兩個 delimiter。

--- report-begin ---
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "gh issue view 47 --repo ruan6047/ai-workflow --json body -q .body | grep 'handoff by wf-cli' | tail -1; git -C .claude/worktrees/dev-main-red-capability-flags1 rev-parse HEAD; git -C .claude/worktrees/dev-main-red-capability-flags1 merge-base --is-ancestor 5d22a7f3da57a3790179e999d9d28262fda4d19a HEAD"
    observed: "最後 handoff、被審 worktree HEAD 均為 adfcbce0c9526f893f1e12abf3668366dc5fe50b；指定 baseline 祖先檢查 exit 0。"
  - command: "git archive 5d22a7f3da57a3790179e999d9d28262fda4d19a | tar -x -C /tmp/aiwf47-base.FCGarY; cd /tmp/aiwf47-base.FCGarY/cli; PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest -q"
    observed: "僅在拋棄式 archive 執行；644 passed, 14 errors in 36.97s，14 個均在 tests/test_release_cleanup.py 的 fixture setup。"
  - command: "git archive adfcbce0c9526f893f1e12abf3668366dc5fe50b | tar -x -C /tmp/aiwf47-review.Abajh2; cd /tmp/aiwf47-review.Abajh2/cli; PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest -q"
    observed: "僅在拋棄式 archive 執行；658 passed in 44.08s。"
  - command: "git diff --check 5d22a7f3da57a3790179e999d9d28262fda4d19a adfcbce0c9526f893f1e12abf3668366dc5fe50b; git diff --unified=0 5d22a7f3da57a3790179e999d9d28262fda4d19a adfcbce0c9526f893f1e12abf3668366dc5fe50b -- cli/tests/test_release_cleanup.py; git show --format=%B --no-patch adfcbce0c9526f893f1e12abf3668366dc5fe50b | git interpret-trailers --parse"
    observed: "diff check 無輸出；唯一程式變更為四個 open routing flags 與一個 assign actual-capability，另有說明註解，未觸及 assert；可解析 trailer 僅為 Co-Authored-By。"
  - command: "git ls-tree -r --name-only adfcbce0c9526f893f1e12abf3668366dc5fe50b | rg '^\\.github/' || true; gh api repos/ruan6047/ai-workflow/actions/workflows"
    observed: "被審 source SHA 沒有 .github 路徑；目前 remote 有 active CI workflow，但它不是被審 SHA 的交付物，不能作為此卡當時已具機械合併防線的證據。"
first_round:
  - status: "首輪，無前輪 accepted blocking finding。"
findings:
  - finding_id: "DEV-MAIN-RED-CAPABILITY-FLAGS1-R1-001"
    severity: major
    blocking: true
    finding_class: governance
    attribution: planner
    root_cause_id: "missing-platform-merge-gate"
    evidence: "卡面核心痛點明定兩個結果：main 回到綠燈，以及下次同型事故由機械攔下。被審 SHA 的隔離式 pytest 已證明第一項，且其 source tree 沒有 .github 路徑；本卡寫入也只有 fixture，沒有將完整測試接為合併前自動閘門。故修補可在人為執行 pytest 時抓到同類漏旗標，卻不能防止未跑測試的合併。派審所指承接項 #48 並非被審 artifact，不能使本卡的兩段核心痛點都成立。"
    disposition: "需求方須開 DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1 修復卡，不得回退 main。修復卡須由需求方裁定是否併入或明確依賴 #48，並以已在 main 的 CI 與平台合併防線實測證明：同類 fixture 失敗會阻擋 merge，而非僅留下可手動執行的 pytest；完成前本事後稽核不得通過。"
  - finding_id: "DEV-MAIN-RED-CAPABILITY-FLAGS1-R1-002"
    severity: major
    blocking: true
    finding_class: governance
    attribution: executor
    root_cause_id: "commit-trailer-required-but-missing"
    evidence: "AGENTS.md:10 與 AI_WORKFLOW.md §6 要求 T2 以上實作 commit 末端連續帶 Requested-by、Planned-by、Implemented-by。被審程式 commit adfcbce0c9526f893f1e12abf3668366dc5fe50b 的 git interpret-trailers --parse 僅輸出 Co-Authored-By，三個必填 trailer 全缺。"
    disposition: "需求方須將此不可回寫的歷史缺口納入 DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1 修復卡處置，不得 amend 或回退 main。修復卡應以需求方的明示例外或等價權威紀錄處理既有 SHA，並驗證已承接的 commit trailer guard 能對後續 T2 以上實作阻擋同類缺失；在此前不可把此 SHA 宣稱為符合 §6。"
scope_outside:
  - note: "本地 uv 環境未安裝 ruff，uv run --frozen ruff check . 回報 Failed to spawn: ruff；pytest 已在相同拋棄式 archive 完整通過，未將工具缺失擴大為 finding。"
  - note: "merge 前未完成獨立查核與 lifecycle 留痕是 Coordinator 的已知程序缺口；本次受需求方明示為事後補救查核，未另擴大 finding 集合。"
--- report-end ---


## Comment 5268172292 · 2026-08-12T14:28:21Z

<!-- wf-review-event:v1 card_id=DEV-MAIN-RED-CAPABILITY-FLAGS1 source_sha=adfcbce0c9526f893f1e12abf3668366dc5fe50b attempt_id=DEV-MAIN-RED-CAPABILITY-FLAGS1-e0-adfcbce0c9526f893f1e12abf3668366dc5fe50b -->
## 查核裁決：REQUEST_CHANGES

- 卡：`DEV-MAIN-RED-CAPABILITY-FLAGS1`　attempt_id：`DEV-MAIN-RED-CAPABILITY-FLAGS1-e0-adfcbce0c9526f893f1e12abf3668366dc5fe50b`
- 查核者：GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5267830013 未經編輯，PM 依其 delimiter（report-begin/end、去前導 LF）回讀重算 report_sha256=d6389865… 相符　escalation_epoch：0
- source_sha：`adfcbce0c9526f893f1e12abf3668366dc5fe50b`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T22:28:20+08:00

### self_run（查核者實跑）

- `gh issue view 47 --repo ruan6047/ai-workflow --json body -q .body | grep 'handoff by wf-cli' | tail -1; git -C .claude/worktrees/dev-main-red-capability-flags1 rev-parse HEAD; git -C .claude/worktrees/dev-main-red-capability-flags1 merge-base --is-ancestor 5d22a7f3da57a3790179e999d9d28262fda4d19a HEAD`
  - 最後 handoff、被審 worktree HEAD 均為 adfcbce0c9526f893f1e12abf3668366dc5fe50b；指定 baseline 祖先檢查 exit 0。
- `git archive 5d22a7f3da57a3790179e999d9d28262fda4d19a | tar -x -C /tmp/aiwf47-base.FCGarY; cd /tmp/aiwf47-base.FCGarY/cli; PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest -q`
  - 僅在拋棄式 archive 執行；644 passed, 14 errors in 36.97s，14 個均在 tests/test_release_cleanup.py 的 fixture setup。
- `git archive adfcbce0c9526f893f1e12abf3668366dc5fe50b | tar -x -C /tmp/aiwf47-review.Abajh2; cd /tmp/aiwf47-review.Abajh2/cli; PYTHONDONTWRITEBYTECODE=1 uv run --frozen pytest -q`
  - 僅在拋棄式 archive 執行；658 passed in 44.08s。
- `git diff --check 5d22a7f3da57a3790179e999d9d28262fda4d19a adfcbce0c9526f893f1e12abf3668366dc5fe50b; git diff --unified=0 5d22a7f3da57a3790179e999d9d28262fda4d19a adfcbce0c9526f893f1e12abf3668366dc5fe50b -- cli/tests/test_release_cleanup.py; git show --format=%B --no-patch adfcbce0c9526f893f1e12abf3668366dc5fe50b | git interpret-trailers --parse`
  - diff check 無輸出；唯一程式變更為四個 open routing flags 與一個 assign actual-capability，另有說明註解，未觸及 assert；可解析 trailer 僅為 Co-Authored-By。
- `git ls-tree -r --name-only adfcbce0c9526f893f1e12abf3668366dc5fe50b | rg '^\.github/' || true; gh api repos/ruan6047/ai-workflow/actions/workflows`
  - 被審 source SHA 沒有 .github 路徑；目前 remote 有 active CI workflow，但它不是被審 SHA 的交付物，不能作為此卡當時已具機械合併防線的證據。

### findings（2，其中 blocking 2）

- **DEV-MAIN-RED-CAPABILITY-FLAGS1-R1-001**　severity=major　blocking=true　class=governance　attribution=planner　root_cause_id=`missing-platform-merge-gate`
  - evidence：卡面核心痛點明定兩個結果：main 回到綠燈，以及下次同型事故由機械攔下。被審 SHA 的隔離式 pytest 已證明第一項，且其 source tree 沒有 .github 路徑；本卡寫入也只有 fixture，沒有將完整測試接為合併前自動閘門。故修補可在人為執行 pytest 時抓到同類漏旗標，卻不能防止未跑測試的合併。派審所指承接項 #48 並非被審 artifact，不能使本卡的兩段核心痛點都成立。
  - disposition：需求方須開 DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1 修復卡，不得回退 main。修復卡須由需求方裁定是否併入或明確依賴 #48，並以已在 main 的 CI 與平台合併防線實測證明：同類 fixture 失敗會阻擋 merge，而非僅留下可手動執行的 pytest；完成前本事後稽核不得通過。
- **DEV-MAIN-RED-CAPABILITY-FLAGS1-R1-002**　severity=major　blocking=true　class=governance　attribution=executor　root_cause_id=`commit-trailer-required-but-missing`
  - evidence：AGENTS.md:10 與 AI_WORKFLOW.md §6 要求 T2 以上實作 commit 末端連續帶 Requested-by、Planned-by、Implemented-by。被審程式 commit adfcbce0c9526f893f1e12abf3668366dc5fe50b 的 git interpret-trailers --parse 僅輸出 Co-Authored-By，三個必填 trailer 全缺。
  - disposition：需求方須將此不可回寫的歷史缺口納入 DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1 修復卡處置，不得 amend 或回退 main。修復卡應以需求方的明示例外或等價權威紀錄處理既有 SHA，並驗證已承接的 commit trailer guard 能對後續 T2 以上實作阻擋同類缺失；在此前不可把此 SHA 宣稱為符合 §6。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。
