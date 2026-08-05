# 查核詞範本 (Review Prompt)

> 承載 canonical `AI_WORKFLOW.md` §5.1／§5.2。祕書派審時以此組裝。紅線卡的查核者必須**跨模型家族或人工**（canonical §5）；同家族不同工具不算獨立。查核者**不得代改 source branch**。

## 1. 進駐位置與基準 SHA 核對

- 進駐 worktree：`<絕對路徑>`（**唯讀查核**）
- 被審分支：`<branch>`　`source_sha`：`<完整 40 碼 SHA>`
- **進駐後第一件事**：核對 `git rev-parse HEAD` 與 handoff 指定的 `source_sha` 完全相同、工作區乾淨。不同即停，回報 `review-invalid`，不進實質查核。
- 卡與基線：`<CARD_ID>`（`<owner/repo>#<n>`）；spec 基線 `<版本>`——與父卡當前版本不一致即退回。

## 2. 第一判準（具否決權）

先答：**核心痛點「`<卡面痛點原文>`」是否已消失？證據是什麼？**

- 痛點未消 → `REQUEST_CHANGES`，**即使驗收清單全過**；並指出清單與痛點脫節之處（spec 缺陷，`attribution: planner`）。

## 3. 逐項驗收清單

- [ ] `<卡面驗收條件逐條抄入，一條一列；不得摘要合併>`

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
