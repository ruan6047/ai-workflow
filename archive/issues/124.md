# #124 DEV-ISO-MUTATION-TEST-CLAIM1 回歸測試宣稱能殺掉一個它殺不掉的變異，而它就在證明守衛有牙齒的測試檔裡
- state: closed  created: 2026-08-22T05:11:13Z  closed: 2026-08-22T07:31:03Z
- url: https://github.com/ruan6047/ai-workflow/issues/124
- comments: 1

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 經濟型；改動極小（一條測試的樣本行與 docstring），根因已由跨家族查核者實測定位。難點只有一處：要真的實跑變異證明轉紅，而不是改完宣稱「現在應該會紅了」——本卡整個存在的理由就是有人做過後者。）　查核：待指派（建議 經濟型；判準是查核者自己重跑那個變異看它是否真的轉紅、以及 docstring 的宣稱與行為是否一致。非紅線卡、無 DB、無碼行為變更（只動測試）。⚠️ 查核者須確認修法沒有讓 test_pure_timestamps_are_not_flagged 失去獨立鑑別力。）
- Initiative：—　spec 基線：ai-workflow#120 R6 裁決的 WF-BACKLOG-STAGE1-R6-001（minor、非阻擋），查核者於 2026-08-22 重跑 M4 實測該測試仍通過；PM 已複驗該 docstring 的宣稱文字與樣本行構造 @ ai-workflow main 2dcab60
- DB：db_scope=none
- 服務的原始目標：測試宣稱殺得掉的變異，要真的殺得掉——否則綠燈是在說謊

## 簡介
<!-- card-brief:begin -->
🏁 已完成：修掉 cli/tests/test_canonical_citation_scan.py 裡 test_iso_stripping_does_not_swallow_a_section_line_ref 的假宣稱——docstring 說放寬 _ISO_TIMESTAMP 會讓它轉紅，實測不轉紅（樣本行同時含節次夾行號與完整 ISO 時戳，前者被吃掉後後者自己產生 KIND_BARE、掩蓋漏報）；改樣本行並實跑變異證明雙向轉紅／轉綠。適用時機：要改動 ISO 剪除規則、或懷疑某條回歸測試的綠燈其實在說謊時。⛔ 非射程：只修測試不修被測物，不放寬 _ISO_TIMESTAMP 本身；不得刪除 cli/tests/test_canonical_citation_scan.py 的 test_pure_timestamps_are_not_flagged（驗的是相反方向）；未做全面 mutation testing。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：- **痛點**：一條測試的 docstring 做了**可證偽的宣稱，而那個宣稱是假的** —— 而它就在專門用來證明守衛有牙齒的測試檔裡。

`cli/tests/test_canonical_citation_scan.py` 的 `test_iso_stripping_does_not_swallow_a_section_line_ref` docstring 逐字：

> 若有人把 `_ISO_TIMESTAMP` 放寬成「一到兩位數字、冒號、兩位數字」，**本測試轉紅**。

⭐ **實測它不轉紅。** `ai-workflow#120` R6 的跨家族查核者在重跑 M4（放寬 ISO 剪除）時逐字記錄：

> `test_iso_stripping_does_not_swallow_a_section_line_ref` 在 M4 仍通過：鬆散剪除已吃掉 `§6:220`，但**同一行剩下的 ISO 時間片段仍產生冒號數字命中**，掩蓋了漏報。

根因是樣本行的構造：

```python
line = f"{_BAD_SECTION_REF}（2026-07-30T18:51:22+08:00 記錄）"
assert ccs.KIND_BARE in ccs.line_offence_kinds(line)
```

節次夾行號**和**完整 ISO 時戳在同一行。放寬剪除後前者被吃掉，但後者自己就產生 `KIND_BARE`，斷言照樣成立。

⚠️ **守衛本身沒壞** —— M4 最終被其他測試（裸節次形態與純時戳測試）擋下，查核者據此判本項 minor、非阻擋。壞的是這條測試**宣稱自己能殺掉一個它殺不掉的變異**。

⭐ **為什麼這比「沒有測試」更糟**：它是那個檔案裡唯一針對 R4 實際踩過的坑寫的回歸測試（docstring 逐字「⭐ R4 的實際踩坑」）。有人日後改 `_ISO_TIMESTAMP` 時會看到它綠著，並據此相信那個坑已經被守住。

ⓘ 來源：`ai-workflow#120` R6 裁決的 `WF-BACKLOG-STAGE1-R6-001`（minor、非阻擋、attribution=executor），處置逐字「建議後續改成不含 ISO 的節次引用，或先斷言 ISO 已完整剔除」。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/tests/test_canonical_citation_scan.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 1. 該測試在「`_ISO_TIMESTAMP` 被放寬成一到兩位數字、冒號、兩位數字」這個變異下**實際轉紅**。
2. ⭐ **必須實跑該變異證明轉紅**，⛔ 不得只靠改寫樣本行後宣稱「現在應該會紅了」。
3. docstring 與實際行為一致：它宣稱能殺掉的變異，就是它真的殺得掉的那一個。
4. ⛔ 不得放寬或改動 `_ISO_TIMESTAMP` 本身——本卡修的是**測試**，不是被測物。
5. ⛔ 不得刪除 `test_pure_timestamps_are_not_flagged`——那條驗的是相反方向（純時戳不得誤判），兩條合起來才是完整判準。

## 驗證

- [ ] - ⭐ **變異檢驗兩方向**：(i) 放寬 `_ISO_TIMESTAMP` → 本測試須轉紅；(ii) 還原 → 須轉綠。還原後驗 sha256 逐位元相同、`git status` 乾淨
- ⚠️ **同時確認 `test_pure_timestamps_are_not_flagged` 在方向 (i) 下的行為**，並說明它是否也該轉紅——⛔ 若兩條在同一變異下行為相同，代表其中一條沒有獨立鑑別力，須說明
- `pytest`：釘死基線為當時的 `origin/main`，**自己實跑取得**，⛔ 不抄任何人給的數字
- `python3 scripts/canonical_citation_scan.py` exit 0、命中 0
- CI：⚠️ 用 `--commit <交付 SHA>` 鎖 SHA，⛔ 不得看最近一筆
## Log

- 2026-08-22T13:11:12+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-22T13:12:00+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (PM)；iteration 0；SHA 2dcab601c0c9e0500524a717697208bc117d9f5a；證據 規劃期。痛點與根因已由 ai-workflow#120 R6 的跨家族查核者實測定位（重跑 M4 時該測試仍通過），PM 已複驗 docstring 宣稱文字與樣本行構造。射程單一檔案、無設計替代方案需要質詢。。
- 2026-08-22T13:12:23+08:00 handoff by wf-cli → owner 待指派；iteration 0；SHA 2dcab601c0c9e0500524a717697208bc117d9f5a；證據 規劃 Gate 通過（需求方 2026-08-22）。T2，經受檢查的 backlog 轉換入池。。
- 2026-08-22T13:12:48+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code（子代理）；分支worktree claude/DEV-ISO-MUTATION-TEST-CLAIM1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/iso-mutation-claim1；交付狀態 🔨執行中；實際能力層級 經濟型（與卡面建議 經濟型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-22T13:34:04+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 0；SHA f4ab2eff2f19622afe072f23896c2109f1c8c739；證據 交付 f4ab2eff（基線 2dcab60，進駐時與交付後各 fetch 一次確認 origin/main 仍是它）。單檔 23 insertions 7 deletions，scripts/canonical_citation_scan.py 全程未改（sha256 854ed3af 開頭，交付後 cmp 對 pristine 副本逐位元相同）。

⭐ 執行者先重現了缺陷才動手，實跑輸出：在未改動的基線測試碼上把 _ISO_TIMESTAMP 放寬成 docstring 逐字點名的那個變異，該測試 PASSED；整檔 4 紅 12 綠而紅的全是別的測試。機制 dump 顯示節次夾行號 §6:220 已被吃成 §0，但時戳只被剪掉時分、留下 :22 自成一個無主行號命中，舊斷言被殘骸餵飽。查核者的描述完全屬實。

修法不是換樣本而是改成差分：line_offence_kinds 只回種類 tuple 不回命中位置，故單一斷言在構造上就殺不掉這個變異。新形狀是把 _SECTION_LINE_REF 抽成常數、對照組以字串剪除產生，斷言 without_ref 為空 tuple 而 with_ref 恰為 (KIND_BARE,)。剪除若哪天變成空操作，對照組會拿到與主樣本相同的字串而轉紅。

三個變異方向實跑（釘死交付 SHA）：loose 兩紅、loose_sec 一紅一綠、disabled 兩紅；還原後 sha256 相同、cmp 逐位元相同、git status 空、目標檔 16 passed、全 suite 1080 passed。

⭐ 對 test_pure_timestamps_are_not_flagged 的觀察：它在方向 (i) 下也轉紅而且應該轉紅，但 loose_sec 把兩者分開了（連秒一起吃時純時戳測試綠、本測試紅），故兩條各有獨立鑑別力、不存在其中一條可刪。

⚠️ 執行者主動挑明兩點：其一，在方向 (i) 下讓本測試轉紅的是對照組那一句，主斷言仍被 :22 殘骸餵飽而通過，這是介面限制的必然不是漏改；要真正關掉得讓 line_offence_kinds 回傳命中位置，那是動被測物、本卡射程外。其二，對照組的性質確實與 test_pure_timestamps_are_not_flagged 重疊，它存在的理由不是抓新的變異類別，而是讓主斷言不再是零資訊的檢查。

⭐ 執行者推翻了卡面一項宣稱：PM 卡面寫「它是那個檔案裡唯一針對 R4 實際踩坑寫的回歸測試」，實測 test_each_line_number_shape_is_flagged 在 loose 與 loose_sec 兩個變異下都會紅——R4 的坑一直有第二道守衛。卡面說法在意圖上成立、機械上不成立；不影響本卡該修（假宣稱本身就是缺陷）但影響嚴重度判讀。歸屬 coordinator。

執行者另查證同族風險未擴散：同檔 test_each_line_number_shape_is_flagged 的 docstring 也宣稱放寬 _CANONICAL_LINE_REF 會轉紅，實跑該變異確認確實轉紅、claim 屬實，故假宣稱是孤例不是這個檔案的通病。

範圍外發現（執行者不自行處置）：scripts/canonical_citation_scan.py 模組 docstring 第 55 至 57 行寫「這條性質由 test_iso_stripping_does_not_swallow_a_section_line_ref 釘住」，該句在基線上是假的、在交付後才變真；執行者未改該檔（寫入集外）。

執行者自陳未驗到：只變異了 _ISO_TIMESTAMP 一個常數三個變體，_QUALIFIED_REF 與 _BARE_LINE_REF 與 _MENTIONS 完全沒變異、沒做全面 mutation testing；沒有讀 ai-workflow#120 R6 的原始留言，寫進 docstring 的查核者記錄是轉述派工包（但自己獨立重現了該現象）；CI 綠的是 tests (branch head)，依本 repo ci.yml 設計它永遠不是 required check，本卡沒開 PR 故合併結果從未被 CI 測過，正是該 repo 自己記載的 2026-08-12 事故形狀。CI run 32554379304 以 --commit f4ab2eff 鎖定、conclusion success、五步驟全綠。。
- 2026-08-22T14:52:31+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex（需求方轉貼；無 GitHub 收據留言，PM 逐字轉錄）；core_pain_resolved yes；self_run 9 項；findings 3 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt DEV-ISO-MUTATION-TEST-CLAIM1-e0-f4ab2eff2f19622afe072f23896c2109f1c8c739。
- 2026-08-22T15:30:49+08:00 handoff by wf-cli → owner —；iteration 0；SHA f4ab2eff2f19622afe072f23896c2109f1c8c739；證據 需求方 2026-08-22 授權合併。PR 126 以 merge commit 238ef94 落 main，四個 trailer 齊全含 Reviewed-by: GPT-5@Codex。⭐ R1-002 的證據缺口已由本次 PR 補上：查核者判「push 事件的 CI 不代表合併樹」為非阻擋但屬證據缺口，開 PR 後 ruleset 要求的 tests check（merge ref 那支）實測 SUCCESS，tests (branch head) 亦 SUCCESS，該項由推論轉為觀測。免部署卡故 release 即終態。

未處理的非阻擋 finding：R1-001（卡面「它是那個檔案裡唯一針對 R4 實際踩坑寫的回歸測試」機械上不成立，test_each_line_number_shape_is_flagged 在 loose 與 loose_sec 兩個變異下都紅，attribution coordinator，影響嚴重度判讀但不影響本修正）、R1-003（loose 下由對照組而非主斷言失敗屬介面限制之必然、對照組與純時戳測試在 loose 有重疊、掃描器模組 docstring 的現在式敘述在交付後已為真，三項皆判可接受）。；收尾清理：已清除 worktree、本地分支、遠端分支。
- 2026-08-26T21:00:55+08:00 amend by wf-cli（op 6958b13e）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:71ed542580a03d20253251c883920b61dec45ae8be901e115794c72e13902ba3 (732 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5378724041 · 2026-08-22T06:52:32Z

<!-- wf-review-event:v1 card_id=DEV-ISO-MUTATION-TEST-CLAIM1 source_sha=f4ab2eff2f19622afe072f23896c2109f1c8c739 attempt_id=DEV-ISO-MUTATION-TEST-CLAIM1-e0-f4ab2eff2f19622afe072f23896c2109f1c8c739 -->
## 查核裁決：APPROVE

- 卡：`DEV-ISO-MUTATION-TEST-CLAIM1`　attempt_id：`DEV-ISO-MUTATION-TEST-CLAIM1-e0-f4ab2eff2f19622afe072f23896c2109f1c8c739`
- 查核者：GPT-5@Codex（需求方轉貼；無 GitHub 收據留言，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`f4ab2eff2f19622afe072f23896c2109f1c8c739`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-22T14:52:31+08:00

### self_run（查核者實跑）

- `進駐核對 HEAD 與工作區`
  - HEAD 完整相符 f4ab2eff2f19622afe072f23896c2109f1c8c739；交付 worktree 乾淨
- `git diff --name-only 檢視寫入集`
  - 僅改 cli/tests/test_canonical_citation_scan.py
- `cmp 交付檔與基線的 canonical_citation_scan.py`
  - 相同，SHA-256 為 854ed3af187b177600eb699c60474bcc6ca4de6ffb9ad453ef0c2463ba804f32，_ISO_TIMESTAMP 未改
- `在基線測試碼上加 loose 變異重現`
  - 確為 4 failed 12 passed，目標測試仍通過；機制自行重現：節次夾行號被吃成 §0，時戳留下冒號二二，故舊斷言被殘骸餵飽
- `交付版跑三個變異方向並還原`
  - loose 紅在對照組斷言、純時戳測試亦紅；loose_sec 紅在 with_ref 斷言、純時戳測試綠；disabled 紅在對照組斷言、純時戳測試亦紅。還原後三個隔離副本皆同一 SHA、乾淨
- `交付版跑目標檔測試與掃描器`
  - 該檔 16 passed；掃描器 123 檔、0 非排除命中
- `驗證卡面「唯一 R4 回歸測試」的宣稱`
  - 機械上不成立。test_each_line_number_shape_is_flagged 在 loose 與 loose_sec 都紅
- `驗證同檔 _CANONICAL_LINE_REF 的同族宣稱`
  - 成立；放寬成容許檔名與冒號間任意字元後，該參數化測試紅
- `讀取 ai-workflow issue 120 的原始 R6 記錄`
  - 內容與 docstring 的歷史敘述及本次重現一致（issuecomment-5377836938）

### findings（3，其中 blocking 0）

- **DEV-ISO-MUTATION-TEST-CLAIM1-R1-001**　severity=minor　blocking=false　class=governance　attribution=coordinator　root_cause_id=`card-claim-mechanically-false`
  - evidence：卡面寫「它是那個檔案裡唯一針對 R4 實際踩坑寫的回歸測試」，機械上不成立：test_each_line_number_shape_is_flagged 在 loose 與 loose_sec 兩個變異下都紅，R4 的坑一直有第二道守衛。
  - disposition：嚴重度應為 minor，不影響本修正。卡面宣稱在意圖上成立、機械上不成立。
- **DEV-ISO-MUTATION-TEST-CLAIM1-R1-002**　severity=minor　blocking=false　class=environment　attribution=external　root_cause_id=`unproven-pr-merge-ref-path`
  - evidence：run 32554379304 的確鎖定交付 SHA 且成功，但事件是 push、job 名稱為 tests (branch head)，它不能代表未來合併樹。
  - disposition：構成非阻擋的 CI 證據缺口。合併前應由 PR 的 merge ref 補足。
- **DEV-ISO-MUTATION-TEST-CLAIM1-R1-003**　severity=info　blocking=false　class=implementation　attribution=external　root_cause_id=`interface-limits-accepted`
  - evidence：loose 下由對照組失敗而非主斷言失敗，是回傳介面沒有位置資訊的結果；對照組與純時戳測試在 loose 有重疊。掃描器模組 docstring 對「由此測試釘住」的現在式敘述在交付後已為真。
  - disposition：兩項皆接受。要求改被測物以回傳命中位置屬範圍外；loose_sec 的一紅一綠已實證兩測試獨立性；無需為歷史基線的失真擴大本卡寫入集。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: DEV-ISO-MUTATION-TEST-CLAIM1-e0-f4ab2eff2f19622afe072f23896c2109f1c8c739
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（待指派）
findings:
  - finding_id: DEV-ISO-MUTATION-TEST-CLAIM1-R1-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: governance
    attribution: coordinator
    root_cause_id: card-claim-mechanically-false
    counting_eligible: false
  - finding_id: DEV-ISO-MUTATION-TEST-CLAIM1-R1-002
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: environment
    attribution: external
    root_cause_id: unproven-pr-merge-ref-path
    counting_eligible: false
  - finding_id: DEV-ISO-MUTATION-TEST-CLAIM1-R1-003
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: implementation
    attribution: external
    root_cause_id: interface-limits-accepted
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。
