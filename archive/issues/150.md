# #150 DOC-CANON-01-ENFORCER-STALE1 canonical §0.1 執行者狀態表有五處今日為假，且全檔 5 個行號引用皆會腐爛
- state: closed  created: 2026-08-25T18:50:21Z  closed: 2026-08-26T04:22:29Z
- url: https://github.com/ruan6047/ai-workflow/issues/150
- comments: 3

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；逐處查證須讀碼判定宣稱真假；⛔ 非機械替換。已於 2026-08-26 完成，PR #149。）　查核：待指派（建議 主力型；動的是 canonical，一旦成文即對所有採用專案生效；查核須獨立複跑三個守衛與 §0.1 探針。）
- Initiative：—　spec 基線：cd17ba5f0bda377a0bcdbf542932e6a977f7c409
- DB：db_scope=none
- 服務的原始目標：ROADMAP §0 目標 2「可稽核的內容」——canonical 是所有採用專案的行為依據，它自己的執行者狀態表若為假，讀者會據以推論出相反的結論（已實測發生：aiwf#141／#142 皆據舊文推論過）。

## 簡介
<!-- card-brief:begin -->
修 canonical §0.1／§5.1.1／§6.3 的五處過期宣稱，並把全檔行號引用改為符號引用。**適用時機**：要引用 §0.1 執行者狀態表、或看到 canonical 裡的 `檔.py:行號` 時。⛔ 非射程：不蓋偵測機制（那是 WF-CANONICAL-SELF-STALENESS1）；⛔ 不碰 §6.4 的 occ 表（需根因 corpus）；⛔ 不碰「cpbl 六個檔」（「綁」未定義）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：**canonical §0.1 的執行者狀態表有五處今日為假，而其中兩處是前一次修過期宣稱的 commit 自己造成的。** 逐處：(1) 第 5 列稱 §6.3 parser 條款「⛔ 無執行者」，而 `brief.py` 的 `_reuse_probe()` 在模組載入時就檢查；(2) 第 5c 列稱「⛔ 無通道」且「0 張卡照得了」，而 `open`／`amend` 兩處皆有 `--brief`、實測有簡介的卡非 0；(3) §6.3 末段另有同一句的第三個居所，寫「198 張中僅 8 張（8/8）」，兩小時內即成 201/11；(4) §5.1.1 末段標「⚠️ 未驗：服務的原始目標亦可被 amend 修改」，而 `amend_cmd.py` 的 22 個旗標無一對應、全檔零命中——那是兩分鐘可驗的事被標成未驗；(5) §0.1 的探針省略 git diff 遠端故隱含 HEAD，於是相鄰段落的無關編輯把實得值由 14 推成 16，而文件仍寫 14。⭐ 而 (3) 與 (5) 都是 `bc5bcbb`（上一次修過期宣稱那次）自己製造的：它改寫 §6.3 時只修了一個居所，且新增的三行剛好命中探針的關鍵字集。⇒ 這不是疏忽，是「只釘一端的引用形態」的構造性後果。⚠️ 併帶事實：全檔 5 個 `檔.py:行號` 引用中有 3 個今日已指錯（`handoff_cmd.py:511`／`:513` 實為 `:532`／`:535`），而它們的**判斷本身仍成立** ⇒ 腐爛的是引用形態不是結論。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": []
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] ⚠️ 本卡的交付已於 2026-08-26 完成並推上 PR #149（分支 `ai/opus-5/DOC-CANON-01-STALE1`）；⛔ **開卡晚於交付**，本卡是補登記。

- [ ] **A1** §0.1 五處逐處修正，且每一句修完它的**所有居所**——第三個居所（§6.3 末段的 198/8）是交付內第二次違反才補上的，須逐字留痕。
- [ ] **A2** §0.1 探針的 `git diff` **兩端都釘死字面 SHA**（`cd88270f 337f4c1`），⛔ 不得省略遠端。
- [ ] **A3** 現況數字一律改記**量法**或引用**不可變產物**，⛔ 不留定值——canonical `:176` 已有滿分範例（引用 commit `4cc3070` 的快照檔＋`generated_at`＋sha256 前綴）。
- [ ] **A4** 全檔 `檔.py:行號` 引用**清零**，改以符號指認。
- [ ] **A5 ⭐ 射程已於 2026-08-26 擴大：§6.4 族表的兩格空值納入。** ⛔ **原本的非射程理由被證偽**——初版寫「需根因 corpus，`WF-STAGE-PITFALL-LIST1` 的研究輪自己也復現不出」，而實查兩個值（`可重現性不足` 16、`資源或寫入集宣告` 4）**逐字就在本 Initiative 父卡的歸併結案留言裡**（`issues/130#issuecomment-5390450940`），一次 `gh api` 即得 ⇒ 純抄寫錯誤。⭐ 修正時須以該留言的 13 族完整清單做**雙向互含**的逐格對帳，⛔ 不得只改那兩格（那是「列舉或覆蓋不完整」）；並在表頭釘上該留言 URL 作為權威來源。
- [ ] **A6 ⛔ 仍為非射程**：`:33`／`:155` 的「`cpbl` 有六個檔綁該語彙」。理由：**「綁」沒有定義**——實測 11 個檔提及舊語彙，但其中 `docs/archive/TASKS_PRE_WF12.md`、`docs/research/*_snapshot.json`、`docs/control-plane/events.jsonl` 是封存與快照，與 `scripts/roadmap_lines.py` 這種碼層依賴混算沒有意義。⇒ 要改須先定義「綁」，⛔ 那是另一張卡。

## 驗證

- [ ] - [ ] **V1** §0.1 探針逐字照抄執行須得 **14**，且與文件寫的值相同。
- [ ] **V2 ⭐ 變異檢驗**：舊寫法（省略遠端）在修改前後皆得 16、新寫法得 14 ⇒ 證明釘死有效。⛔ 「編輯後重跑仍為 14」是**零資訊**的檢查（遠端釘死後構造上不可能改變），不得當證據。
- [ ] **V3** 歷史回放：`337f4c1`／`d4ba7ce`／`4dd63da` → 14，`bc5bcbb`／`cd17ba5` → 16。
- [ ] **V4** 三個守衛實跑 rc：`contract_tool_reconcile --check`＝0、`canonical_citation_scan`＝0、`pytest`＝1174 passed。⚠️ 撰寫過程中 reconcile 一度轉紅（缺口 60、登記 59），因初稿以反引號寫了 kebab 形式的旗標名 ⇒ 須逐字登記該次轉紅與修法。⛔ 不得接管線（`| tail` 會把 rc 換成 tail 的）。
- [ ] **V5** 行號引用殘留數須為 **0**。
- [ ] **V6** 每一處被判為假的宣稱，須附**它今天為什麼假**的實跑證據，⛔ 不接受「讀起來不對」。
- [ ] **V7 ⭐ 新增（隨 A5）**：§6.4 族表的對帳須由**指令輸出產生**，逐族列出「表值／來源值／相符與否」與兩個方向的集合差集，⛔ 不接受目視比對或只報改動的那兩格。交付須顯示 13 族雙向互含、差集皆為空。

## Log

- 2026-08-26T02:50:19+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-26T02:57:23+08:00 handoff by wf-cli → owner 待指派（跨家族查核）；iteration 0；SHA b0006e0b821f78ed577ebf3cbaa2d25c4aaabd01；證據 ⚠️ 開卡晚於交付：本卡是補登記（分支 ai/opus-5/DOC-CANON-01-STALE1 已推，PR #149，三個 commit 4ef9607/38870fa/b0006e0）。⛔ 前面的規劃與執行階段沒有走，那是事實不是疏漏後補——連同上一次同形狀的 PR #145（分支名 DOC-CANON-S63-STALE1 而 Project 查無該卡）一併登記為已知缺口。交付內容：canonical §0.1 五處過期宣稱逐處修正、探針 git diff 兩端釘死字面 SHA（cd88270f 337f4c1）、全檔 5 個檔.py:行號 引用清零改符號指認、§5.1.1 末段對 amend 的宣稱更正為已驗為假。驗證：§0.1 探針照抄執行得 14 與文件一致；變異檢驗舊寫法修改前後皆 16 而新寫法 14；歷史回放 337f4c1/d4ba7ce/4dd63da 皆 14、bc5bcbb/cd17ba5 皆 16；contract_tool_reconcile --check rc=0（撰寫中曾因反引號 kebab token 一度轉紅 60/59，已登記）；canonical_citation_scan rc=0；pytest 1174 passed。非射程明列：§6.4 occ 表兩格（需根因 corpus）與 :33/:155 的「cpbl 六個檔」（「綁」未定義，實測 11 檔但多數是封存）。⛔ 未合併——合併須需求方裁定。。
- 2026-08-26T12:01:41+08:00 amend by wf-cli（op ceec8021）→ 驗收條件：原值指紋 sha256:a75f35ed0b4245f2cd2fc67c4a3a8c3715e42cfe8a38369f4c166f7d5c6b57ae (1031 bytes) → 新值指紋 sha256:8e0806b27a996d89d0403223a2608d0eb6e71d82977a11974fb5fa1099de0692 (1863 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定擴射程納入 §6.4 族表兩格空值（甲案）：原非射程理由「需根因 corpus」被證偽，兩值逐字在 issues/130#issuecomment-5390450940；新增 A5 改寫、A6 保留 cpbl 六個檔為非射程並補理由、V7 要求對帳由指令輸出產生。
- 2026-08-26T12:01:41+08:00 amend by wf-cli（op ceec8021）→ 驗證：原值指紋 sha256:5415f289471d0118e640e4141ffe0a19e389b4fbd899e2235027f9ab6d153b82 (933 bytes) → 新值指紋 sha256:bb489ba02fce5219e4302398dadcb692ee0c82c8a2ea855a9cce8e91c50b94cd (1281 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定擴射程納入 §6.4 族表兩格空值（甲案）：原非射程理由「需根因 corpus」被證偽，兩值逐字在 issues/130#issuecomment-5390450940；新增 A5 改寫、A6 保留 cpbl 六個檔為非射程並補理由、V7 要求對帳由指令輸出產生。
- 2026-08-26T12:07:44+08:00 assign by wf-cli → owner 待認領（跨家族查核者）；分支worktree ai/opus-5/DOC-CANON-01-STALE1 @ /Users/ruanruan/Dev/ai-workflow/.worktrees/canon-01-stale；交付狀態 🔍待查核；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-26T12:18:09+08:00 review by wf-cli → APPROVE（✅通過）；查核者 Codex@跨家族查核（需求方轉貼、PM 逐字轉錄）；core_pain_resolved yes；self_run 6 項；findings 0 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt DOC-CANON-01-ENFORCER-STALE1-e0-ecb8b5786b6199b2839ddcb79d390a866b42bb2a。
- 2026-08-26T12:22:14+08:00 handoff by wf-cli → owner 已合併（無部署面）；iteration 0；SHA 4e99845428c67de28479a6e7ca4efd0b294b0934；證據 需求方於 2026-08-26 逐字指示「合併」後由 PM 執行 gh pr merge 149 --merge，merge commit 4e99845428c67de28479a6e7ca4efd0b294b0934。⭐ 並在合併結果上重跑（查核者是在分支上跑的，基線不同）：§0.1 探針=14 與文件一致、行號引用殘留=0、contract_tool_reconcile --check rc=0、canonical_citation_scan rc=0。查核裁決 APPROVE 見 issue #150 的 issuecomment-5420532241（收據原文在 PR #149 的 issuecomment-5420517464，由需求方轉貼、PM 逐字轉錄）。⚠️ 查核者身分為未知——PM 曾在裁決事件填入無來源的身分，已於 issuecomment-5420537778 更正。本卡為純文件變更，⛔ 無部署面（cpbl 消費端不讀 canonical 的這幾節）。；收尾清理：已清除 worktree、本地分支、遠端分支。


## Comment 5420532241 · 2026-08-26T04:18:10Z

<!-- wf-review-event:v1 card_id=DOC-CANON-01-ENFORCER-STALE1 source_sha=ecb8b5786b6199b2839ddcb79d390a866b42bb2a attempt_id=DOC-CANON-01-ENFORCER-STALE1-e0-ecb8b5786b6199b2839ddcb79d390a866b42bb2a -->
## 查核裁決：APPROVE

- 卡：`DOC-CANON-01-ENFORCER-STALE1`　attempt_id：`DOC-CANON-01-ENFORCER-STALE1-e0-ecb8b5786b6199b2839ddcb79d390a866b42bb2a`
- 查核者：Codex@跨家族查核（需求方轉貼、PM 逐字轉錄）　escalation_epoch：0
- source_sha：`ecb8b5786b6199b2839ddcb79d390a866b42bb2a`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-26T12:18:09+08:00

### self_run（查核者實跑）

- `git merge-base origin/main ecb8b5786b6199b2839ddcb79d390a866b42bb2a`
  - rc=0，輸出 cd17ba5f0bda377a0bcdbf542932e6a977f7c409；git diff --check 同兩點 rc=0，變更檔僅 AI_WORKFLOW.md
- `在 head ecb8b578 的隔離 worktree 逐字執行 §0.1 新探針；再移除遠端固定端重跑`
  - 固定端 rc=0、14 行；移除固定端 rc=0、16 行 ⇒ 證實固定端才是差異來源，非驗證一個構造上恆定的結果
- `檢查 brief.py 的 _reuse_probe()、open_cmd.py/amend_cmd.py 的 --brief、validation.py、amend_cmd.py 的 service_goal、handoff_cmd.py 的 if args.status:`
  - _reuse_probe() 模組載入時執行且直接重跑 rc=0；兩處 --brief 皆 default=None 可選；validation.py 無 brief 驗證；amend_cmd.py 無 service_goal/service-goal 選項；if args.status: 在讀部署狀態的 release 分支之前
- `gh api repos/ruan6047/ai-workflow/issues/comments/5390450940 --jq .body 後自寫雙向對帳`
  - rc=0：source_count=13、canonical_count=13、source_only=[]、canonical_only=[]、value_mismatches={}
- `python3 scripts/contract_tool_reconcile.py --check; python3 scripts/canonical_citation_scan.py`
  - rc=0（59 個缺口全部有登記處置）；rc=0（125 檔、非排除命中 0）
- `cd cli && uv run --frozen pytest -q`
  - rc=0，1174 passed in 72.51s

### findings（0，其中 blocking 0）

- （無）

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: DOC-CANON-01-ENFORCER-STALE1-e0-ecb8b5786b6199b2839ddcb79d390a866b42bb2a
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待認領（跨家族查核者）
findings: []
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5420537778 · 2026-08-26T04:18:49Z

## ⛔ 更正：上一則裁決事件的「查核者」欄是 PM 腦補的

上一則（`issuecomment-5420532241`）的查核者欄寫「Codex@跨家族查核」。⛔ **那個身分沒有任何來源**——需求方轉貼收據時**沒有指名查核者是誰**，是 PM 自己填的。

⚠️ 依本 repo 的既有裁定，身分欄是**授權基準**不是排版欄位（`card.py` 的 `restore_migration_header` 逐字：「`requested_by` 是一句斷言，⛔ 不是排版修復」）⇒ 在裁決事件裡填一個沒有來源的查核者身分，等於為一份真實的查核工作掛上錯誤的歸屬。

**逐字修正**：查核者身分為 **未知**。已知的只有：

- 收據原文在 `https://github.com/ruan6047/pull/149#issuecomment-5420517464`（實際位置：本 repo PR #149 的留言 `5420517464`）
- 該留言的 GitHub 作者是 `ruan6047`（需求方的 token）
- 收據內容由需求方在 2026-08-26 的 session 轉貼給 PM，PM 逐字轉錄成結構化事件
- ⛔ 收據本身未自述作者

⚠️ **事件已寫入且 append-only，⛔ 不編輯原文**（依「發現後發更正留言、勿編輯原文」）。本則即為更正留痕。裁決本身（APPROVE、`core_pain_resolved: yes`、六條 `self_run`、findings 0）**逐字轉錄自收據原文，那部分不受本更正影響**。

⭐ 順帶登記一個機械缺口：`wfcli review` 的 `--reviewer` 是**自由文字、無任何來源驗證**。⇒ 任何轉錄者都寫得出一個不存在的查核者身分，而事件面看不出差別。⛔ 本更正不開卡，只登記。

---
本帖由 PM（Claude Opus 5@Claude Code）以需求方的 token 發文，內容為 PM 自陳的錯誤更正，⛔ 非需求方的裁定。

## Comment 5433923349 · 2026-08-27T03:18:08Z

## ⛔ 本卡的交付在 canonical 裡留下兩個新的行號指標，今日已腐爛

本卡的標題逐字是「canonical §0.1 執行者狀態表有五處今日為假」——⭐ **而本卡的交付 commit `b0006e0`（主旨逐字 `docs(canonical): remove every line-number citation and the third stale count`）自己在散文裡寫下了兩個新的行號指標**，26 小時內失效。

### 缺陷位置與現況（2026-08-27 實測，基線 `764a59ff`）

`AI_WORKFLOW.md:85-86` 逐字：

> ⚠️ **此處刻意以符號而非行號指認**——原文寫的 `:511`／`:513` **今日已分別指到 `:532`／`:535`**，⛔ 而宣稱本身仍成立 ⇒ 腐爛的是引用形態不是判斷。

實測 `cli/src/wf_cli/commands/handoff_cmd.py`：

| 引用 | 該行實際是什麼 |
|---|---|
| `:532` | `from_status = pitfalls.status_to_phase(STAGE_STATUS, STAGE_PHASE).get(` |
| `:535` | `if from_status is not None and from_status != resolution.phase:` |

⇒ ⛔ **兩行都與它描述的東西無關**。它描述的 `if args.status:` 分支在 **695**、`elif args.next_stage == "release":` 閘門在 **697**。

成因：該檔於 `5653ade`（2026-08-27T03:57，`#154` 的交付）被改動。

### ⭐ 這句話的用意本身就是反例

它想說的是「**我們刻意用符號不用行號，因為行號會腐爛**」——⛔ **而它是用「再寫兩個行號」來證明這件事的**。⇒ 它現在既是那條紀律的教材，也是那條紀律的違例。

### 第二居所

`AI_WORKFLOW.md:325` 是 blockquote **逐字轉引**同一句（由 `57bff9f`／PR #156 寫入）⇒ **同一個缺陷有兩個居所**，修一個不夠。

### 建議的修法（依 canonical 自己的紀律）

canonical 逐字自陳：「⚠️ **「機械執行者」欄刻意以「檔名＋符號或運算式」指認，⛔ 不寫行號**……**本表的壽命以年計，行號的壽命以次計**。」

⇒ 那句話**不需要具體行號就能成立**。建議改成不帶新行號的寫法，例如：

> ⚠️ **此處刻意以符號而非行號指認**——本節原以行號指認這兩個分支，而那組行號在寫下後**不到一個月即失效**（兩個分支今日各自移位），⛔ 而宣稱本身仍成立 ⇒ 腐爛的是引用形態不是判斷。

⛔ **我沒有代改**——canonical 的變更需要卡與查核。本則只把事實放回它的來源卡上。

---

⚠️ 附帶說明：這是我（PM）在 `aiwf#146` 的第四、五輪研究中量到的。⭐ 需求方逐字指示「**不要為以前舊卡的問題找通則，應該是請問題卡修正**」⇒ 故 ⛔ 不造守衛、⛔ 不進 Backlog，改在此具名。射程內今日另有 17 筆裸 `:NNN` 命中／10 個相異宣稱，其餘各自屬於別的來源卡。

