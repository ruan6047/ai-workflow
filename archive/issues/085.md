# #85 DEV-REVIEW-PARSER-QUOTED-SCALAR1 查核報告解析器：引號純量內的引號字元不應整份拒收
- state: closed  created: 2026-08-13T08:32:17Z  closed: 2026-08-13T09:09:09Z
- url: https://github.com/ruan6047/ai-workflow/issues/85
- comments: 2

## Body

- 需求：ruan6047　規劃：—
- 執行：待指派　查核：待指派
- Initiative：—　spec 基線：docs/ROADMAP.md（origin/main 71df1570b7ddefbbbf101f8e8b1b053e5fe82cd7）§0 目標 1「防止低級事故」——執行者是解析器本身。
- DB：db_scope=none
- 服務的原始目標：查核者能用自然的指令字串寫 self_run，而 PM 永遠不需要動查核者的原文。

## 簡介
<!-- card-brief:begin -->
🛑 已停止（No-Go）：原擬窄修 cli/src/wf_cli/review.py 的引號子規則，讓查核者能在 self_run 的 command 值裡寫巢狀引號而不被整份拒收——#128 就是因此把 PM 推去改查核者的報告原文，而報告全文正是收據雜湊的對象。2026-08-18 需求方裁定 No-Go：卡面兩句前提（「以 regex 拒絕合法巢狀引號是工具缺陷」與「格式在 review-prompt.md §5 的子集內」）經實測皆不成立。適用時機：wfcli review 因引號整份拒收、或要查該 No-Go 的依據與被推翻的前提時。⛔ 非射程：兩半射程已轉 #66 與 #86；不引入 PyYAML 或任何第三方 runtime 相依、不改用寬鬆解析；本 Issue 的 stateReason 為 COMPLETED 與 No-Go 矛盾，刻意不修（無機器消費者）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：查核者在 command 值裡寫了合法的巢狀引號（gh ... | grep "handoff by wf-cli"），wfcli review 整份拒收：『第 8 行引號結束後仍有內容，無法判定值的範圍』。後果不是少一則裁決，而是**把 PM 推去改查核者的報告原文**：2026-08-13 的 #128 就是需求方授權 PM 做引號正規化才過關，而報告全文正是收據雜湊的對象，改一個字元就讓收據對不上。查核結論本身完全正確、格式也在 review-prompt.md §5 的子集內，卡住的純粹是解析器對引號的處理。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/review.py",
    "file:cli/tests/test_review.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 雙引號純量內出現引號字元不再整份拒收：至少支援 (a) 單引號純量、(b) 雙引號純量內以既有引號規則正確找到結束引號。以 #128 的實際字串 gh issue view 128 --json body -q .body | grep 'handoff by wf-cli' 及其雙引號版本各一則測試
- [ ] ⚠️ 不得引入 PyYAML 或任何第三方 runtime 相依，也不得改用寬鬆解析：review.py 的 module docstring 已明文裁決『寬鬆解析與 fail-closed 互斥』（YAML 1.1 把 yes 讀成布林、重複鍵靜默取最後一個）。本卡只修引號子規則，語法之外一律拒絕的立場不變
- [ ] 既有拒收行為全數保留：anchor／alias／flow mapping／巢狀序列／tab 縮排／重複鍵、writer-only 欄位（accepted／status／counts_toward_escalation）、第一行非頂層 key: value

## 驗證

- [ ] cli/tests/test_review.py 補正例與反例；uv run pytest（cli/）不退步
- [ ] 以 #128 R1 那份被拒收的報告原文重跑，確認可解析且結論與當時經 PM 正規化後的版本一致
- [ ] 留一則說明：查核者 GPT-5@Codex 2026-08-13 建議『改用真正的 YAML parser』與本模組既有裁決衝突，本卡採窄修法；若需求方要推翻該裁決須另卡處理
## Log

- 2026-08-13T16:32:15+08:00 open by —；owner 待指派；iteration 0。
- 2026-08-18T19:49:30+08:00 handoff by wf-cli → owner —（已停止）；iteration 0；SHA f207d2ecf80556d6b90beeb0438bf648288a5fd9；證據 收尾補帳（2026-08-18）：Issue 已於 2026-08-13 關閉而交付狀態停在 📥Backlog，本次補終態。決策與原因（AI_WORKFLOW.md:18 要求）：需求方裁定 No-Go，理由逐字見 issuecomment-5278319558——「本卡由 PM 依查核者 GPT-5@Codex 於 2026-08-13 Q3 的回覆撰寫，其中『以 regex 拒絕合法的巢狀引號是工具缺陷』與卡面『格式也在 review-prompt.md §5 的子集內』兩句皆不成立」，前提經實測推翻，兩半射程轉 #66 與 #86。⚠️ 附記一項不修正的不一致：本 Issue 的 stateReason 是 COMPLETED，與 No-Go 的實質矛盾。不改的理由是 stateReason 無任何機器消費者（wfcli 全域不讀它，cpbl 的腳本讀的是交付狀態），而改它需 reopen 再 close、多兩筆 timeline 事件。矛盾記於此處而非修欄位。。
- 2026-08-26T21:04:54+08:00 amend by wf-cli（op 3b927a38）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:3b92b172453fbfbf45b0755b4a13869109d2965c3e4d7b1e572469b68755f559 (801 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5278319558 · 2026-08-13T09:09:07Z

## 關卡（No-Go）：核心痛點的前提經實測推翻

本卡由 PM 依查核者 GPT-5@Codex 於 2026-08-13 Q3 的回覆撰寫，其中「以 regex 拒絕**合法的**巢狀引號是工具缺陷」與卡面「格式也在 `review-prompt.md` §5 的子集內」兩句**皆不成立**。執行前先驗，三種寫法對照（PyYAML 僅作證據，本 repo 不引入該相依）：

| 寫法 | PyYAML | wfcli 解析器 |
|---|---|---|
| `"… grep "handoff by wf-cli"；x"`（#128 原文形態） | 拒收（ParserError） | 拒收（引號結束後仍有內容） |
| `'… grep "handoff by wf-cli"；x'`（單引號純量） | 接受 | 接受 |
| `"… grep \\"handoff by wf-cli\\"；x"`（反斜線跳脫） | 接受 | 接受 |

也就是說：`wfcli` 的行為與真正的 YAML parser 完全一致，#128 那份報告在任何 YAML parser 下都不合法，**拒收是正確行為**。原驗收第一項（雙引號純量內找到結束引號）只能靠讓解析器比 YAML 更寬鬆去猜歧義輸入才能達成，與 `review.py` module docstring 的 fail-closed 裁決直接相衝；第二項（單引號純量）今日已滿足。

剩餘可實作範圍只有「錯誤訊息帶修法指引」，兩半各有更好的歸屬，故不留在本卡：

- **範本要寫引號規則** → #66 WF-DISPATCH-FROM-HANDOFF1。派審詞若由 handoff 生成，警告自動隨附，不需要有人記得手抄（#124 派審詞那段引號警告就是 PM 手動補的）。
- **「PM 看到拒收不該去改查核者原文」** → #86 WF-REVIEW-RECEIPT-WRITEBACK1。#128 的真正根因不是解析器，是 PM 手上握著那些位元組又有動機改它；修錯誤訊息只是在錯的路口立更好的路標，#86 是把路口拆掉。

不走 amend 改核心痛點的理由：#37 WF-CARD-FIELD-CORRECTION1 記載 PM 上次繞過該缺口被判 critical blocking（attribution=coordinator）；照規矩走則須需求方裁定留言 ＋ `--ruling-url`，而 #62 WF-AMEND-AUTHZ-BINDING1 已證明該 author 檢查在本 repo 恆真、從未區辨過任何東西。為一段錯誤訊息跑一次雙方都知道是形式的治理程序，成本高於收益。

需求方 2026-08-13 裁定關卡。執行 worktree 零改動，一併回收。

## Comment 5278319818 · 2026-08-13T09:09:08Z

見上一則：前提經實測推翻，兩半射程轉 #66 與 #86，需求方裁定 No-Go。
