# 查核詞範本 (Review Prompt)

> 承載 canonical `AI_WORKFLOW.md` §5.1／§5.2：查核詞必含四件——**進駐位置＋基準 SHA 核對**（§1）、**逐項驗收清單**（§3）、**環境紅線**（§4）、**結構化輸出要求**（§5）。紅線卡的查核者必須**跨模型家族或人工**（canonical §5）；同家族不同工具不算獨立。查核者**不得代改 source branch**。
>
> ⚠️ **本檔的重心是 §5 的結構化輸出契約**——`wfcli review` 以它為寫入前的機械閘門，`cli/src/wf_cli/review.py`、`validation.py`、`commands/review_cmd.py` 逐處引用 §5、`card.py` 與 `commands/amend_cmd.py` 引用 §2、[`review-escalation.md`](review-escalation.md) 引用 §6。⛔ **不得改動本檔的節次編號**：改一個號碼，上列每一處引用同時失準，而失準的方向是「指得到一個存在但講別的事的節」——⛔ 不會有任何東西轉紅。
>
> **三份檔的分工**（同一次審核的三個面，⛔ 不是三次審核）：
>
> | 檔 | 是什麼 | 誰寫 |
> |---|---|---|
> | [`review-dispatch.md`](review-dispatch.md) | **派審信封**：卡與身分、基線釘死、前輪 findings、PM 已知未驗項 | PM |
> | 本檔 §5 | **schema**：`wfcli review` 解析得回來的欄位與列舉 | 由本檔定義，查核者照填 |
> | [`verdict.md`](verdict.md) | **人讀範本**：把同一次裁決寫成收件者讀得懂的文件（含信封四段） | 查核者 |
>
> ⚠️ 看板值仍為舊語彙（15 值），對照見決議 §一；切換於切換 Initiative。

## 1. 進駐位置與基準 SHA 核對

- 進駐 worktree：`<絕對路徑>`（**唯讀查核**）
- 被審分支：`<branch>`　`source_sha`：`<完整 40 碼 SHA>`
- 基線（merge-base，取自派審詞的**釘死字面**）：`<完整 40 碼 SHA>`——⛔ 不自己抄 `origin/main`、⛔ 不動態算。
- **進駐後第一件事**：核對 `git rev-parse HEAD` 與 handoff 指定的 `source_sha` 完全相同、工作區乾淨。不同即停，回報 `review-invalid`，⛔ 不進實質查核。
- 卡與基線：`<CARD_ID>`（`<owner/repo>#<n>`）；spec 基線 `<spec_version>`——與父卡當前版本不一致即退回。
- ⭐ 本節各格的值由派審詞的信封一與信封三帶入，⛔ 不由查核者自行決定。

## 2. 第一判準（具否決權）

先答：**核心痛點「`<卡面痛點原文>`」是否已消失？證據是什麼？**

- 痛點未消 → `REQUEST_CHANGES`，**即使驗收清單全過**；並指出清單與痛點脫節之處（spec 缺陷，`attribution: planner`）。
- 這一問的機器面就是 §5 的 `core_pain_resolved`：`no` 一律 `REQUEST_CHANGES`。

## 3. 逐項驗收清單

- [ ] `<卡面驗收條件逐條抄入，一條一列；⛔ 不得摘要合併>`

⛔ **不用卡面沒有的標準**——用了即構成升級裁定第 ④ 值「退回無效」的事由。

## 4. 環境紅線

- DB 一律唯讀（除非卡面明示）；**不得真跑爬蟲、訓練或資料重建類 CLI**。需要驗證 CLI 行為時走密封探針或容器。
- 不得改 source branch。驗證命令若會改動 tracked file，於 disposable 驗證 worktree／容器內執行（[`worktree-lifecycle.md`](worktree-lifecycle.md) §3）。
- 守衛在**合併結果**上跑，⛔ 不在分支頭上。`self_run` 的 rc 分開取、⛔ 不接管線（`| tail` 會換掉 `$?`）。
- **跨 repo 證據**：以絕對路徑 ＋ 釘住的 SHA ＋ 碼段摘錄對帳。worktree 內 submodule 目錄為空是預期（canonical §4.5）——「檔案不在我的樹裡」不構成 finding。
- 範圍外發現寫進報告的獨立一節交 PM，不自行擴大 finding 集合、不開卡。
- ⛔ **正文不得出現事件 marker 前綴的完整字面**（doctor 全文子字串比對，出現即隔離整卡）——要提及就拆開書寫。

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

⚠️ **本區塊是機器面，⛔ 不是裁決全文。** `wfcli review` 只認這個固定子集（頂層純量、`- key: value` 清單項），語法之外一律拒絕；區塊內⛔ 不得混入散文，同一份報告內⛔ 不得出現兩個含 `review_result` 的區塊（把範本區塊與實際裁決一起貼是最常見的觸發方式）。人讀的段落寫進 [`verdict.md`](verdict.md) 的對應節，⛔ 不塞進本區塊。

## 6. R2 以後的範圍

R2 只做兩件：**R1 finding 逐項閉環驗證** ＋ **回歸不倒退**。不重跑 R1 已通過項、不擴審新範圍——擴審會讓 iteration 無法收斂，也讓 escalation 計數失義。

⭐ 派審詞若把 `closure_reporting_requested` 填成 `false`，記錄的就是一次**偏離本節**；那是一筆 `coordination` 事實，該在派審當下寫下，⛔ 不由受益方事後推定。
