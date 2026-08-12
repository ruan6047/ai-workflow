# 查核詞範本 (Review Prompt)

> 承載 canonical `AI_WORKFLOW.md` §5.1／§5.2。祕書派審時以此組裝。紅線卡的查核者必須**跨模型家族或人工**（canonical §5）；同家族不同工具不算獨立。查核者**不得代改 source branch**。

## 1. 進駐位置與基準 SHA 核對

- 進駐 worktree：`<絕對路徑>`（**唯讀查核**）
- 被審分支：`<branch>`　`source_sha`：`<完整 40 碼 SHA>`
- **進駐後第一件事**：核對 `git rev-parse HEAD` 與 handoff 指定的 `source_sha` 完全相同、工作區乾淨。不同即停，回報 `review-invalid`，不進實質查核。
- 卡與基線：`<CARD_ID>`（`<owner/repo>#<n>`）；spec 基線 `<版本>`——與父卡當前版本不一致即退回。
- **基線須自行驗為祖先**：派審詞給的「基線」是界定 diff 範圍的座標，由 Coordinator 手填、**送出前無任何前置檢查**。進駐後跑 `git merge-base --is-ancestor <基線> HEAD`；exit 非 0 即停，回報 `review-invalid`。判準本身是機械的（git 的 exit code），但**沒有東西強制查核者跑它**，故本條是**約定**；把結果寫進 §5 `self_run` 後，`self_run` 非空由 `cli/src/wf_cli/validation.py` 的 `validate_review_report` 強制（基線 `6e6e8ab` 時在 :261／:265）——**但那只強制「有寫東西」，不驗這個檢查真的跑過**。
  - 本條防的**不是** Coordinator 填錯（那在派審當下已成立，範本層擋不到），而是**查核者在未驗證的基線上做完整輪查核**。2026-08-11 同一個錯誤基線（`0d4d282`，非任何卡的祖先）送給四位查核者，四種處置：一位據此停手（正確）、一位寫下「基線仍為被審 SHA 的祖先」——**該斷言不成立**，只是結論恰好無害。無此條時「有沒有驗」不留痕，兩者在報告上無法區分。

## 2. 第一判準（具否決權）

先答：**核心痛點「`<卡面痛點原文>`」是否已消失？證據是什麼？**

- 痛點未消 → `REQUEST_CHANGES`，**即使驗收清單全過**；並指出清單與痛點脫節之處（spec 缺陷，`attribution: planner`）。

## 3. 逐項驗收清單

- [ ] `<卡面驗收條件逐條抄入，一條一列；不得摘要合併>`

## 3.1 前輪 finding 閉環回報（iteration ≥ 1 必填）

R1 之後的每一輪，報告須有本節，把上一輪每一筆 `accepted` 且 `blocking` 的 finding **逐列**列出。**一列一個 `finding_id`；不得合併、不得只寫「前輪均已處理」**：

| finding_id | 處置 | 證據 |
|---|---|---|
| `<卡ID>-R<n>-<序>` | `resolved`／`withdrawn`／仍 `open` | `<可重現的重現方式或來源>` |

- **逐列是判準的一部分，不是排版偏好**：[`review-escalation.md`](review-escalation.md) §4 逐 `finding_id` 推導 checkpoint 的格位，整體式結論映射不到任何一格，與未提及等價。
- 缺本節、或 carry set 中有 `finding_id` 未表態 → 查核者**自判** `review-invalid`，不進實質查核（處置同 §1）。
- **仍 `open` 是合法且常常正確的表態**，不是失敗；defer 延後的是評估而非結果（`review-escalation.md` §4）。把仍未解的寫成 `resolved` 才是失分。

**本節今天沒有機械執行者，故為約定而非強制。** `wfcli review` 的寫入前閘門（`cli/src/wf_cli/validation.py` 的 `validate_review_report`，基線 `6e6e8ab` 時在 :224，由 `commands/review_cmd.py:155` 呼叫；函式名才是穩定錨點，行號會隨在飛的卡位移）只驗 §5 區塊的欄位與列舉，**既不檢查本節是否存在，也不知道前輪的 carry set**。

**「iteration ≥ 1 未逐項指名前輪 accepted blocking finding 即拒寫」這個閘門目前無人承接**——請不要讀成某張卡的待辦而停止追問。`ai-workflow#9` **不涵蓋本節**：其驗收逐字為「accepted 標記寫入通道（lifecycle writer 語意）；attempt_id 去重；counts_toward_escalation 推導與 checkpoint 觸發警示」，其中第四項是 **checkpoint 漏建**閘門（上一個可計數 attempt 序位 ≥3 卻無對應 checkpoint 即 exit 2，`validation.check_checkpoint_gate`），輸入、判準與失敗模式都與「報告有沒有逐項指名前輪 finding」不同。

**被誰擋住**：該閘門的實作落點是 `review.py`／`validation.py`／`commands/review_cmd.py`，而這三個檔都在 #9 的資源宣告內，故 **#9 交付並釋出寫入集之前，任何承接卡都開不了**。需要它的人須自行舉證並開卡，不得假定已有人在做。

**條文有效的前提是它送到了能執行它的人手上——而送到了也不保證被執行。** 本檔的讀者是查核者，故本節在派審詞被組裝進去時即可被自查；`review-invalid` 曾被查核者依派審詞字面真的判出並停手，證明文字條款確實會被執行。但 2026-08-11 的兩次 checkpoint 觸發（#21 R5、#22 R2）是反面：兩份派審詞**都逐字寫了**該要求，缺的是報告那一側。**送達是必要條件，不是充分條件**——這正是機械閘門不可被本節取代的理由，而該閘門今天無人承接（見上）。

## 4. 環境紅線

- DB 一律唯讀（除非卡面明示）；**不得真跑爬蟲、訓練或資料重建類 CLI**。需要驗證 CLI 行為時走密封探針或容器。
- 不得改 source branch。驗證命令若會改動 tracked file，於 disposable 驗證 worktree／容器內執行（[`worktree-lifecycle.md`](worktree-lifecycle.md) §3）。
- **跨 repo 證據**：以絕對路徑 ＋ 釘住的 SHA ＋ 碼段摘錄對帳。worktree 內 submodule 目錄為空是預期（canonical §4.5）——「檔案不在我的樹裡」不構成 finding。
- 範圍外發現寫進報告的獨立一節交 PM，不自行擴大 finding 集合、不開卡。

## 5. 結構化輸出（必填）

```yaml
core_pain_resolved: yes | no       # 第一判準；no 一律 REQUEST_CHANGES
review_result: APPROVE | REQUEST_CHANGES
self_run:                          # 必填：查核者自己實際跑過的指令與觀察到的輸出
  - command: <指令>
    observed: <輸出摘要／數字>
findings:
  - finding_id: <卡ID>-R<n>-<序>
    severity: critical | major | minor | info
    blocking: true | false
    finding_class: implementation | authoritative-artifact | governance | coordination | environment
    attribution: executor | planner | coordinator | reviewer | external
    root_cause_id: <穩定根因家族；unknown 每個 finding 唯一>
    evidence: <可重現的重現方式或來源>
    disposition: <要求的修法或決策>
```

**沒有 `self_run` 的 `APPROVE` 無效**——記 `review-invalid`，不計 iteration（[`review-escalation.md`](review-escalation.md) §1）。完整 finding schema 與 `accepted`／`status` 的採認規則見同檔 §2。

## 6. R2 以後的範圍

R2 只做兩件：**R1 finding 逐項閉環驗證** ＋ **回歸不倒退**。不重跑 R1 已通過項、不擴審新範圍——擴審會讓 iteration 無法收斂，也讓 escalation 計數失義。

逐項閉環驗證要**寫成什麼形狀**見 §3.1（逐 `finding_id` 一列）。本節定範圍，§3.1 定回報格式；`review-escalation.md` §4 對 carry set 的推導同時依賴兩者。
