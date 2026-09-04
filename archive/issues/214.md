# #214 WF-REDESIGN-W0 角色準則與收件條件生效（四波五卡 W0）
- state: open  created: 2026-08-31T15:55:49Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/214
- comments: 2

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；機械搬移四檔（git move＋frontmatter 與警語移除），零內容改動；⛔ PM 不可兼（W0 spec 明定））　查核：待指派（建議 經濟型；紅線審核滿足＝需求方逐條確認之使用者 sign-off（AGENTS 紅線選項，獨立性要求疊加於層級之上）；獨立 session 另跑 ④ 完整性機械檢查（git log --follow＋diff 證零內容改動））
- Initiative：WF-REDESIGN1　spec 基線：ai-workflow 93bb8c086f0cf8870537390511b5f0aa2d037c97
- DB：db_scope=none
- 服務的原始目標：可稽核＋防低級事故＋流程順暢——行為準則未生效使派工包無法引用（防低級事故軸）

## 簡介
<!-- card-brief:begin -->
適用時機：四波五卡 W0——將需求方已逐條確認的 pm-conduct／executor-conduct／reviewer-conduct／list-intake-requirements 以移動（⛔ 非複製）生效至 stage-rules/，draft 標記與警語移除、不留雙居所。階段計畫：需求→執行→審核→結案（跳過研究／規劃——內容已需求方逐條確認，二階段無新產出；⛔ 非 T1 直通）。級別依據（P1-11）：conduct 含紅線與授權＝規則本體，AGENTS 紅線適用 ⇒ T4；可逆（git revert）但風險軸取最高。spec_version: 1（甲′ 規格住卡面；來源 wave-specs/w0.md 屆時封存）。⛔ 非射程：不改四份檔的實質內容（已確認）；不動 canonical；不建清單機制（波 1）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：三份 conduct 與收件條件已經需求方逐條確認，但仍掛 draft-pending 隔離於 drafts/——派工包無從引用生效版。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:stage-rules/pm-conduct.md",
    "file:stage-rules/executor-conduct.md",
    "file:stage-rules/reviewer-conduct.md",
    "file:stage-rules/list-intake-requirements.md",
    "file:docs/research/drafts/stage-rules/pm-conduct.md",
    "file:docs/research/drafts/stage-rules/executor-conduct.md",
    "file:docs/research/drafts/stage-rules/reviewer-conduct.md",
    "file:docs/research/drafts/stage-rules/list-intake-requirements.md",
    "file:docs/research/drafts/prose-number-inventory.json",
    "file:scripts/prose_number_scan.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] pm-conduct／executor-conduct／reviewer-conduct／list-intake-requirements 四檔以移動（⛔ 非複製）落到 stage-rules/，draft 標記與警語移除——⛔ 不留雙居所
- [ ] 移動前後內容 diff 僅限 frontmatter 與警語（機械可驗）

## 驗證

- [ ] git log --follow 證明是 move
- [ ] git grep -l draft-pending -- stage-rules/ 零命中

## Log

- 2026-08-31T23:55:48+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-31T23:57:46+08:00 amend by wf-cli（op 076bd7aa）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:stage-rules/pm-conduct.md", "file:stage-rules/executor-conduct.md", "file:stage-rules/reviewer-conduct.md", "file:stage-rules/list-intake-requirements.md", "file:docs/research/drafts/stage-rules/pm-conduct.md", "file:docs/research/drafts/stage-rules/executor-conduct.md", "file:docs/research/drafts/stage-rules/reviewer-conduct.md", "file:docs/research/drafts/stage-rules/list-intake-requirements.md" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:stage-rules/pm-conduct.md、file:stage-rules/executor-conduct.md、file:stage-rules/reviewer-conduct.md、file:stage-rules/list-intake-requirements.md、file:docs/research/drafts/stage-rules/pm-conduct.md、file:docs/research/drafts/stage-rules/executor-conduct.md、file:docs/research/drafts/stage-rules/reviewer-conduct.md、file:docs/research/drafts/stage-rules/list-intake-requirements.md、file:docs/research/drafts/prose-number-inventory.json、file:scripts/prose_number_scan.py」（⚠️ 全文：totalCount=0（首寫，平台無前一版））；理由 開卡後 PM 前置檢查發現：搬移使 prose_number_scan corpus（drafts glob）與 inventory path 綁定斷鏈→死條目 CI 紅；補宣告守衛兩檔供「守衛跟隨搬移」機械同步（P1-38 守衛，2026-08-31 上線）——⛔ 非內容改動，AC 不變。
- 2026-09-01T00:27:25+08:00 assign by wf-cli → owner session 6059924c-0601-4d67-b53d-85d0f492794b@Claude Code（高階型）；分支worktree docs/w0-enact-conducts @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/w0-enact-conducts；交付狀態 🔨執行中；實際能力層級 高階型（偏離卡面建議 主力型；偏離理由：高於建議（主力型）：需求方指定之執行 session 即為高階型；機械搬移風險僅更低）；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 target_absent（機器局部，沉默不代表無誤）。
- 2026-09-01T00:31:50+08:00 assign by wf-cli → owner session 6059924c-0601-4d67-b53d-85d0f492794b@Claude Code（高階型）；分支worktree claude/WF-REDESIGN-W0 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-redesign-w0；交付狀態 🔨執行中；實際能力層級 高階型（偏離卡面建議 主力型；偏離理由：同前次登記（需求方核定高階型）；本次僅更正 branch/worktree 登記值向實際對齊（執行者實用 claude/WF-REDESIGN-W0＋wf-redesign-w0，前次為 PM 預規定值未被採用））；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-09-01T00:44:59+08:00 handoff by wf-cli → owner session 6059924c-0601-4d67-b53d-85d0f492794b@Claude Code；iteration 1；SHA 93bb8c086f0cf8870537390511b5f0aa2d037c97；階段 需求；踩坑回應 8 族（已檢查 7／不適用 0／發現 1）；證據 補記轉移：assign（2026-09-01）僅寫交付狀態未寫階段欄；實際執行已於本 handoff 前完成（af71697），本筆為階段欄留痕補位，⛔ 非重新開工。
- 2026-09-01T00:45:25+08:00 handoff by wf-cli → owner ruan6047（需求方 sign-off）＋獨立完整性 session@Claude Code；iteration 1；SHA af716979f81ff26d668e72f89d1d6e046b8da950；階段 執行；踩坑回應 13 族（已檢查 13／不適用 0／發現 0）；證據 執行者交付報告（session 6059924c，轉錄於 PM session）：AC1 move R092-098、AC2 每檔 3 刪 0 增；PR #215 CI tests pass（merge-result 4722228f）；踩坑 13 族逐條回應轉錄自執行者報告原文。
- 2026-09-01T00:46:06+08:00 review by wf-cli → APPROVE（✅通過）；查核者 ruan6047（需求方 sign-off，本 session 逐字轉錄）＋獨立完整性 session@Claude Code；core_pain_resolved yes；self_run 6 項；findings 0 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-REDESIGN-W0-e0-af716979f81ff26d668e72f89d1d6e046b8da950。
- 2026-09-01T00:47:25+08:00 handoff by wf-cli → owner ruan6047；iteration 1；SHA cc3330127fbf6da3aa57b85ee483d1e972761325；階段 審核；踩坑回應 8 族（已檢查 7／不適用 0／發現 1）；證據 PR #215 squash merge→main cc33301（scanner 200 全零、pytest 1528 綠於 main 實跑）；review APPROVE（sign-off＋獨立完整性，findings 空）；收尾 PR #216（w0.md 封存）→38c3afe。cleanup 由 AUTHORITY_BY_PROOF 內容證明阻擋（#216 使 main 的 inventory 前進於分支，構造上無法證內容在 main）——照兩分支契約以不帶 --repo-path 路徑 release，worktree 移除列其後義務由 PM 手動執行留痕；⚠️ 未帶 --cleanup 且未帶 --repo-path，收尾清理未執行（worktree、本地分支、遠端分支皆未處理），狀態面已寫終態。


## Comment 5481495375 · 2026-08-31T16:46:09Z

<!-- wf-review-event:v1 card_id=WF-REDESIGN-W0 source_sha=af716979f81ff26d668e72f89d1d6e046b8da950 attempt_id=WF-REDESIGN-W0-e0-af716979f81ff26d668e72f89d1d6e046b8da950 -->
## 查核裁決：APPROVE

- 卡：`WF-REDESIGN-W0`　attempt_id：`WF-REDESIGN-W0-e0-af716979f81ff26d668e72f89d1d6e046b8da950`
- 查核者：ruan6047（需求方 sign-off，本 session 逐字轉錄）＋獨立完整性 session@Claude Code　escalation_epoch：0
- source_sha：`af716979f81ff26d668e72f89d1d6e046b8da950`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-09-01T00:46:06+08:00

### self_run（查核者實跑）

- `git rev-parse origin/claude/WF-REDESIGN-W0`
  - af716979f81ff26d668e72f89d1d6e046b8da950（與交付宣稱逐字同）
- `git log --follow --name-status（四檔）`
  - R098/R093/R092/R097，皆自 docs/research/drafts/stage-rules/ 追溯至初始 A（bf267aaa）
- `git diff -M --numstat 93bb8c0..af71697 -- docs/research/drafts/stage-rules/ stage-rules/`
  - 四檔各 0 新增／3 刪除；刪除行逐字＝status 行＋警語 blockquote＋空行
- `git diff --stat 93bb8c0..af71697`
  - 恰 6 檔（4 rename＋scanner＋inventory），無其他檔
- `inventory 整檔深度比較（baseline 版僅改四檔 path 前綴後與 head 版比較）`
  - 位元等價 True；改動行 38 刪 38 增全為 path 欄；line_sha1 全未動
- `python3 scripts/prose_number_scan.py（於 af71697 detach worktree）`
  - total 200、七項計數全零、rc=0

### findings（0，其中 blocking 0）

- （無）

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-REDESIGN-W0-e0-af716979f81ff26d668e72f89d1d6e046b8da950
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: "ruan6047（需求方 sign-off）＋獨立完整性 session@Claude Code"
findings: []
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5481516664 · 2026-08-31T16:47:50Z

收尾留痕（PM 手動，其後義務完成）：worktree /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-redesign-w0 已以 git worktree remove 移除（移除前 status 乾淨）；分支 claude/WF-REDESIGN-W0 依 squash 慣例（cleanup.AUTHORITY_BY_PROOF）保留。cleanup 守衛阻擋原因＝PR #216 使 main 的 inventory 內容前進於分支，內容證明構造上不可成立——⛔ 非分支內容遺失。
