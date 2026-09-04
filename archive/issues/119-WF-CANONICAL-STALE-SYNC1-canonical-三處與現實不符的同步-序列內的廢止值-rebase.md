# #119 WF-CANONICAL-STALE-SYNC1 canonical 三處與現實不符的同步：序列內的廢止值、rebase 狹義例外、Reviewed-by 的不適用值域
- state: closed  created: 2026-08-21T14:02:21Z  closed: 2026-08-21T15:46:32Z
- url: https://github.com/ruan6047/ai-workflow/issues/119
- comments: 1

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 經濟型；純文件同步，三處的正確內容已由 2026-08-21 的研究取證（該行的實測出現次數、CONTRACT_TOOL_RECONCILE.md:427 的 read-only 登記、#39 的需求方裁定原文、doctor.py 的 trailer_keys 實作）。難點在第二、三處的措辭要精確到「例外的適用條件可被人判定」而不是留下一個模糊的逃生口。）　查核：待指派（建議 經濟型；判準是三處改後是否逐字為真、以及第二處的例外條文是否明確標注它沒有機械執行者。非紅線卡、純文件、無碼變更。⚠️ 但本檔是跨專案 canonical，採用專案以 stub 指向它，查核者須確認改動不會讓採用專案的既有流程失效。）
- Initiative：—　spec 基線：2026-08-21 的三項實查：AI_WORKFLOW.md:18 的 ⏳待執行 出現 2 次、docs/CONTRACT_TOOL_RECONCILE.md:427 的 read-only 登記、ai-workflow#39 issuecomment-5367447565 的需求方前向裁定、cli/src/wf_cli/doctor.py:789-790 與 :915
- DB：db_scope=none
- 服務的原始目標：canonical 說的規則，要跟實際在跑的規則是同一條

## 簡介
<!-- card-brief:begin -->
修 canonical AI_WORKFLOW.md 三處與現實不符之處：:18 的狀態序列移除同一句話內已被廢止的 ⏳待執行（templates/TASKS.md:6 印同一條序列須同步）、:229 §6.1 第 3 款補上 2026-08-21 裁定的 rebase 狹義例外並明文標注它沒有機械執行者、:216-219 的 Reviewed-by 值域補上「不適用」形態並明記守衛只驗鍵不驗值（doctor.py:789-790 的 trailer_keys 只回鍵）。**適用時機**：要引用 canonical 的交付狀態序列、分支更新禁令或 merge trailer 值域時。⛔ 非射程：不改任何規則的實質內容——只把 aiwf#39 issuecomment-5367447565 的既有裁定搬進 canonical，搬運中不得擴大或縮小；不動 cli/ 任何碼；不動採用專案 cpbl-analytics 的過期陳述（另有 cpbl#162）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：canonical `AI_WORKFLOW.md` 有三處與現實不符，其中一處**同一句話內部自相矛盾**。

**第一處（句內矛盾）**：`:18` 的交付狀態序列印著 `… → 📥Backlog → ⏳待執行 → 🔨執行中 → …`，**緊接著同一句**寫「**廢止的歷史值**（向後相容，已寫的卡留著，**新寫入不得用**）：`🚧進行中`、**`⏳待執行`**」。⭐ **`⏳待執行` 同時在現行序列與廢止清單裡**——實測該行出現 2 次。

矛盾是 `ae8f741`（`#102 WF-STATUS-VOCAB-ALIGN1`，2026-08-18）造成的：它加入了廢止條款與三個前授權階段，**但沒有把被廢止的值從同一句印的序列裡拿掉**。

⚠️ **後果**：讀者看到的「正規流程」包含一個不得寫入的狀態。實測全 173 張卡中 `⏳待執行` **0 張**——`docs/CONTRACT_TOOL_RECONCILE.md:427` 記著它是 `read-only`、來源只有 `AI_WORKFLOW.md:18` 與 `templates/TASKS.md:6` 兩份**印序列的文件**、**從來沒有 writer**。⇒ 它只存在於那條箭頭裡，沒有任何動詞能寫它，也沒有任何一張卡曾經是它。

**第二處**：`:229` §6.1 第 3 款寫「分支更新禁 `gh pr update-branch`…**一律本地 rebase ＋ `git push --force-with-lease`**」。需求方 2026-08-21 已就 `ai-workflow#39` 裁定一條**狹義例外**（rebase 會使 main 已合併的碼所引用的 SHA 失效、或會把早於 `TRAILER_GUARD_EPOCH` 的 commit 推過界線而翻成無法修的違規時，不要求 rebase），⚠️ **但該例外目前只存在於 `#39` 的 issue 留言（issuecomment-5367447565）**。**任何只讀 canonical 的人會看到與該次交付相反的規則。**

**第三處**：`:216-219` 寫 merge commit「另必加 `Reviewed-by: <GitHub 帳號／模型@工具>`」。同一份 2026-08-21 裁定授權了 `Reviewed-by: —（基線更新 merge，無查核對象）` 這個「不適用」標記，⚠️ **它不在該值域內**，而 `doctor.py:789-790` 的 `trailer_keys()` 只回鍵、`:915` 的 `missing` 只比對鍵，**守衛從不驗值，所以不會抓到**。

⭐ 三處的共同性質：**canonical 說的與現實／既有裁定不同，而沒有任何機制會發現**。第一處更嚴重——它不需要外部事實就能判定為矛盾，**同一句話讀兩次就看得出來**。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:AI_WORKFLOW.md",
    "file:templates/TASKS.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] ⭐ :18 的序列移除 ⏳待執行，並保留廢止清單。⚠️ templates/TASKS.md:6 印同一條序列，須同步——⛔ 只改一處會讓兩份文件不一致，那是本卡在修的同一種病。交付須以指令輸出證明兩份文件的序列逐字相同。
- [ ] ⭐ :229 §6.1 第 3 款補上 2026-08-21 裁定的狹義例外，含三項：適用條件（兩項須同時成立：rebase 會使 main 已合併的碼所引用的 SHA 失效；或會把早於 TRAILER_GUARD_EPOCH 的 commit 推過界線而翻成無法修的違規）、該例外不免除任何 trailer、⭐ **明文標注它沒有機械執行者**（依 doctor.py:863-867，「基線更新 merge」不是可從 commit 自身導出的形狀，故它是派工包層的約定，由撰寫者判定、查核者複核）。⛔ 不得宣稱它已機械化。
- [ ] ⭐ :216-219 的 Reviewed-by 值域補上「不適用」形態，載明其唯一合法用法是基線更新 merge 這類無查核對象的 merge_clean，並⚠️ 明記守衛只驗鍵存在不驗值（doctor.py:789-790 的 trailer_keys 只回鍵、:915 的 missing 只比對鍵），故該值域是約定不是機械保證。
- [ ] ⛔ 非目標——不改任何規則的實質內容。本卡只讓 canonical 記載的與既有裁定／既有實作一致；⚠️ 第二、三處的實質裁定已於 2026-08-21 做過，本卡是把它從 issue 留言搬進 canonical，不得在搬運過程中擴大或縮小它。交付須貼出裁定原文與新條文的逐句對照。
- [ ] ⛔ 非目標——不動 cli/ 任何碼；不動採用專案 cpbl-analytics 的任何檔（該 repo 的過期陳述另有其卡 cpbl#162）；不新增或移除任何交付狀態。
- [ ] 既有 cd cli && uv run --frozen pytest -q 不得因本卡而失效；scripts/contract_tool_reconcile.py --check 須維持 exit 0。⚠️ 後者特別重要——本卡動的是契約文件，新增或移除任何反引號包住的 kebab-case 符號都會改變對帳器的 universe。

## 驗證

- [ ] ⭐ 三處改後逐字為真的取證：:18 附「⏳待執行 在該行出現 0 次」的指令輸出並附 TASKS.md 同步後的逐字比對；:229 與 :216-219 各附裁定原文與新條文的逐句對照。
- [ ] ⭐ 對帳器不受影響：python3 scripts/contract_tool_reconcile.py --check 貼真實 exit code（應為 0）。⚠️ 量 exit code 不要接管線。⚠️ 若缺口數變動，須逐一說明是哪個符號、為什麼。
- [ ] cd cli && uv run --frozen pytest -q 貼末行並與改動前並列。
- [ ] ⚠️ 報告須明列沒驗到什麼。至少包含：本卡不改採用專案的 stub，故 cpbl-analytics 讀到的仍是本檔——改動生效與否取決於該 repo 的 submodule 指標何時更新，本卡不處理那一步。
## Log

- 2026-08-21T22:02:19+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-21T22:03:36+08:00 handoff by wf-cli → owner ruan6047（Design Gate）；iteration 0；SHA 2ae1ff0be3ae78f38392b81e1c5b3fe9409c79b8；證據 ⚠️ 更正 open 的預設落點，非交付：wfcli open 預設寫 📥Backlog，違反規劃閘門（cpbl ROADMAP §2.0／canonical AI_WORKFLOW.md:113）。⭐ 這正是 ai-workflow#118 正在修的那個缺陷，本卡因此也中了——同族第十一、十二次。⚠️ source_sha 為當下 origin/main，非本卡交付。⚠️ --iteration 釘住原值 0。。
- 2026-08-21T22:16:43+08:00 handoff by wf-cli → owner ruan6047；iteration 0；SHA 2ae1ff0be3ae78f38392b81e1c5b3fe9409c79b8；證據 規劃 Gate 通過（需求方 2026-08-21）。Discovery 與 Design 皆已於當日完成並固化進卡面驗收條——三處各有實查取證：:18 的 ⏳待執行 實測在該行出現 2 次（序列與廢止清單各一）且 docs/CONTRACT_TOOL_RECONCILE.md:427 記它為 read-only／無 writer；:229 的例外原文在 ai-workflow#39 issuecomment-5367447565；:216-219 的值域問題附 doctor.py:789-790 與 :915（守衛只驗鍵不驗值）。Plan：三處同一份 canonical，templates/TASKS.md:6 印同一條序列須同步。⚠️ --iteration 釘住 0。。
- 2026-08-21T22:17:44+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code（子代理）；分支worktree claude/WF-CANONICAL-STALE-SYNC1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-canonical-stale-sync1；交付狀態 🔨執行中；實際能力層級 經濟型（與卡面建議 經濟型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-21T22:40:43+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 0；SHA 66c8aa38ac8b990f4e2bc1782978ad15a13f480a；證據 交付 66c8aa3（基線 2ae1ff0b），寫入僅 AI_WORKFLOW.md + templates/TASKS.md，2 files 4+/4-。PM 獨立複驗：行數 260→260 未變、:18 序列內 ⏳待執行 0 次而廢止清單保留 1 次（卡面驗證條與驗收條 1 互斥，執行者兩個讀法都取證，PM 確認以驗收條為準）、:220/:221/:222 三行與 HEAD~1 逐字相同（diff exit=0）。執行者回報 reconcile exit=0 缺口 58→58、pytest 1052 passed、doctor trailer 違規 0，PM 未複跑。兩項要查核者裁決：(1) 裁定原文的「對 b6900c6 不追溯適用」刻意未搬入通則，理由是一次性專案決定；(2) 執行者順帶發現既存漂移 doctor.py:694/:866 引用 AI_WORKFLOW.md:222 但該行為空行（實際在 :216）、ROADMAP.md:120 引用 :221 但規則在 :220，PM 已 grep 複驗屬實，皆在寫入集外未動。注意第二三處構造上無機械執行者，故「doctor 沒抓到」在此不是證據。。
- 2026-08-21T23:11:09+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex（需求方轉貼；無 GitHub 收據留言，PM 逐字轉錄）；core_pain_resolved yes；self_run 8 項；findings 1 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-CANONICAL-STALE-SYNC1-e0-66c8aa38ac8b990f4e2bc1782978ad15a13f480a。
- 2026-08-21T23:46:15+08:00 handoff by wf-cli → owner —；iteration 0；SHA 66c8aa38ac8b990f4e2bc1782978ad15a13f480a；證據 需求方授權合併，PR #121 以 merge commit b2a6d54 落 main（四個 trailer 齊全含 Reviewed-by: GPT-5@Codex）。免部署純文件卡故 release 即 🏁完成。R1-001（既存行號漂移 doctor.py:694／:866 → 空行 :222、ROADMAP.md:120 → :221）為非阻擋 minor，查核者裁定另建獨立文件卡，未於本卡處理。；收尾清理：已清除 worktree、本地分支、遠端分支。
- 2026-08-26T22:00:48+08:00 amend by wf-cli（op ce7f8aaf）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:6da059a1b174caacc3d7770d88a506ca1e6f73e0e159889d6d99bd0d0bd134cf (806 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5371702435 · 2026-08-21T15:11:10Z

<!-- wf-review-event:v1 card_id=WF-CANONICAL-STALE-SYNC1 source_sha=66c8aa38ac8b990f4e2bc1782978ad15a13f480a attempt_id=WF-CANONICAL-STALE-SYNC1-e0-66c8aa38ac8b990f4e2bc1782978ad15a13f480a -->
## 查核裁決：APPROVE

- 卡：`WF-CANONICAL-STALE-SYNC1`　attempt_id：`WF-CANONICAL-STALE-SYNC1-e0-66c8aa38ac8b990f4e2bc1782978ad15a13f480a`
- 查核者：GPT-5@Codex（需求方轉貼；無 GitHub 收據留言，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`66c8aa38ac8b990f4e2bc1782978ad15a13f480a`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-21T23:11:09+08:00

### self_run（查核者實跑）

- `git diff --name-only 2ae1ff0b..66c8aa38ac8b990f4e2bc1782978ad15a13f480a`
  - 僅 AI_WORKFLOW.md、templates/TASKS.md；worktree 乾淨
- `兩檔主箭頭狀態序列逐字比對；:18 與 templates/TASKS.md:6 的 ⏳待執行 計數`
  - 兩份序列逐字相同；序列內 ⏳待執行 均為 0；廢止清單各保留 1 次
- `wc -l AI_WORKFLOW.md（基線 vs 交付）；diff 220-222 行`
  - 260 → 260；220-222 與基線逐字相同
- `基線與交付各自清點 AI_WORKFLOW.md 行號引用`
  - 兩側皆 10 處，均未位移
- `scripts/contract_tool_reconcile.py --check（基線與交付各自直接執行，未接管線）`
  - 皆 exit 0，皆 58 個缺口
- `pytest`
  - 1052 passed in 63.16s
- `git interpret-trailers --parse`
  - 三個 trailer 齊全、位於末端且連續無空行
- `檢視 cpbl-analytics docs/AI_WORKFLOW.md:11 stub`
  - 僅指向 canonical，未複製本次條文；本提交未改應用程式碼或設定

### findings（1，其中 blocking 0）

- **WF-CANONICAL-STALE-SYNC1-R1-001**　severity=minor　blocking=false　class=authoritative-artifact　attribution=external　root_cause_id=`canonical-line-ref-rot`
  - evidence：doctor.py:694 與 :866 引用 AI_WORKFLOW.md:222，該行為空行，實際規則在 :216；docs/ROADMAP.md:120 引用 :221，規則在 :220。既存漂移，非本提交造成，且在宣告寫入集外。
  - disposition：由需求方另建獨立純文件卡修正。本卡刻意維持行號不位移，於本卡修改反而違反本卡射程與驗收設計。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-CANONICAL-STALE-SYNC1-e0-66c8aa38ac8b990f4e2bc1782978ad15a13f480a
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（待指派）
findings:
  - finding_id: WF-CANONICAL-STALE-SYNC1-R1-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: authoritative-artifact
    attribution: external
    root_cause_id: canonical-line-ref-rot
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。
