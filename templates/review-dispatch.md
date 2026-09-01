# 派審詞範本 (Review Dispatch)

> 承載 `stage-rules/review.md` §3 的 ②。PM 派審時以此組裝。查核者**可能來自另一個實體**——[`stage-rules/reviewer-conduct.md`](../stage-rules/reviewer-conduct.md) 與本份派審詞**就是全部要求**，沒寫的慣例⛔ 不存在：2026-08-29 換一個實體來查核，派審詞明文要求的 session ID 當場就掉了。
> 紅線卡的查核者必須**跨模型家族或人工**（canonical §5）；同家族不同工具不算獨立。查核者**不得代改 source branch**。
> 信封四段的權威定義在 [`handoff-contract.md`](handoff-contract.md) §3.3，⛔ 本檔不重寫定義。
> ⚠️ 看板值仍為舊語彙（15 值），對照見決議 §一；切換於切換 Initiative。

## 信封一 · 卡與身分

- 卡ID／Issue：`<CARD_ID>`（`<owner/repo>#<n>`）　級別：`<T0–T4>`　Initiative：`<父卡／—>`
- spec 基線：`<spec_version>`——與父卡當前版本不一致即退回
- 階段：`審核`　輪次（iteration）：`R<n>`　escalation epoch：`<e<N>>`
- from：`<PM 帳號>`　to：`<查核者 模型@工具／人工>`
- 核心痛點（第一判準的錨，卡面原文逐字）：`<原文>`
- 模型：實際 `<查核者 模型@工具>`　卡面建議 `<經濟型／主力型／高階型>`　偏離理由 `<相符時填「相符」；另註明與執行者是否同家族>`

## 信封二 · 身分自述

- 派審者 GitHub 帳號：`<帳號>`
- session ID：`<Claude：~/.claude/projects/<cwd>/<id>.jsonl 的 <id>；Codex：rollout-<時間>-<id>.jsonl 的 <id>>`
- 該則訊息定位：`<Claude：訊息 uuid；Codex：該則 timestamp>`
- ⭐ **裁決必須回填查核者自己的這三格**——`author` 恆為同一個 GitHub 帳號，這是唯一可核對的身分訊號。

## 信封三 · 機械指令

- 進駐 worktree：`<絕對路徑>`（**唯讀查核**）　被審分支：`<branch>`
- `source_sha`：`<完整 40 碼>`
- **基線 SHA（merge-base，釘死字面）**：`<完整 40 碼>`——⛔ 不自己抄 `origin/main`，⛔ 不動態算
- **進駐後第一件事**：核對 `git rev-parse HEAD` 與 `source_sha` 完全相同、工作區乾淨。不同即停，回報 `review-invalid`，⛔ 不進實質查核。
- 守衛在**合併結果**上跑，⛔ 不在分支頭上：

  ```bash
  git merge-base <branch> origin/main   # 應等於上面釘死的基線 SHA
  ```

- 驗證指令逐條（rc 分開取、⛔ 不接管線）：`<指令；標註 worktree／容器／環境變數>`

## 信封四 · 已知未驗項

> **PM 自己**送審前還沒驗的東西，逐項＋各自原因，三分類擇一。⛔ 不裸列——連續八輪裸列正是 2026-08-31 修正的對象。PM 交任何規劃產出物給查核者前，先以同一份 R1–R4 表自審至少一輪，自審紀錄附進本節。

| # | 未驗項 | 分類 | 原因 |
|---|---|---|---|
| 1 | `<項目>` | `驗不了`／`沒去驗`／`刻意不驗` | `<刻意不驗須寫「委給查核者」及理由>` |

---

## 1. 第一判準（具否決權）

先答：**核心痛點「`<信封一的痛點原文>`」是否已消失？證據是什麼？**

- 痛點未消 → `REQUEST_CHANGES`，**即使驗收清單全過**；並指出清單與痛點脫節之處（spec 缺陷，`attribution: planner`）。

## 2. 逐項驗收清單

- [ ] `<卡面驗收條件逐條抄入，一條一列；⛔ 不摘要合併>`

## 3. 前輪 findings（必列）

> ⛔ 不得省略。同 `root_cause_id` 第三輪 ⇒ 查核者寫明並建議升級，PM ⛔ 不派第四輪。R1 時逐字寫「無前輪」。

| finding_id | severity | blocking | root_cause_id | 前輪處置 | 本輪應閉環驗證 |
|---|---|---|---|---|---|
| `<CARD_ID>-R<n>-<序>` | `<critical/major/minor/info>` | `<true/false>` | `<穩定根因家族字串>` | `<accepted/…>` | `<是/否>` |

- `closure_reporting_requested`：`<true／false>`——[`review-prompt.md`](review-prompt.md) §6 已把「前輪 finding 逐項閉環驗證」定為 R2 以後的固定範圍，故填 `false` 記錄的是一次**偏離範本**，須在派審當下寫下（見 [`review-escalation.md`](review-escalation.md)）。

## 4. 環境紅線

- DB 一律唯讀（除非卡面明示）；**不得真跑爬蟲、訓練或資料重建類 CLI**。需要驗證 CLI 行為時走密封探針或容器。
- ⛔ 不改 source branch、⛔ 不代改。驗證命令若會改動 tracked file，於 disposable 驗證 worktree／容器內執行（[`worktree-lifecycle.md`](worktree-lifecycle.md) §3）。
- **跨 repo 證據**：以絕對路徑 ＋ 釘住的 SHA ＋ 碼段摘錄對帳。worktree 內 submodule 目錄為空是預期（canonical §4.5）——「檔案不在我的樹裡」不構成 finding。
- 範圍外發現寫進裁決的獨立一節交 PM，⛔ 不自行擴大 finding 集合、⛔ 不開卡。
- ⛔ **正文不得出現事件 marker 前綴字面**（doctor 全文子字串比對，出現即隔離整卡）——要提及就拆開書寫。

## 5. 要交回什麼

- 結構化區塊：依 [`review-prompt.md`](review-prompt.md) §5 的 schema，**`wfcli review` 以它為寫入前的機械閘門**。
- 人讀裁決全文：依 [`verdict.md`](verdict.md) 組裝（含信封四段與身分自述）。
- 有寫入通道者**自己寫回**（先跑 `wfcli review --validate-only` 自檢）；⛔ 無通道者交 PM 轉錄，PM ⛔ 不代判裁決對錯。
- ⚠️ **沒有 `self_run` 的 `APPROVE` 無效**——記 `review-invalid`，不計 iteration。

## 6. R2 以後的範圍

R2 只做兩件：**R1 finding 逐項閉環驗證** ＋ **回歸不倒退**。⛔ 不重跑 R1 已通過項、⛔ 不擴審新範圍——擴審會讓 iteration 無法收斂，也讓 escalation 計數失義。

## 7. 注意事項回應清冊（PM 自產出物）

> PM 自產出物同罩**注意事項回應清冊**（`stage-rules/pm-conduct.md` 四的「檢核清冊」即本欄）。發出前**逐條編號**回應，三值＝`已遵循`／`不適用：<原因>`／`發現：<處置>`；⛔ 不得只有執行者有清冊而 PM 沒有。

| 編號 | 回應（三值擇一） |
|---|---|
| `P-派審-01` 信封四段齊全 | `已遵循`／`不適用：<原因>`／`發現：<處置>` |
| `P-派審-02` 未驗項已三分類編號化 | 同上 |
| `P-派審-03` 前輪 findings 逐筆列出且帶 `root_cause_id` | 同上 |
| `P-派審-04` 基線為 merge-base 且釘死字面 | 同上 |
| `P-派審-05` 模型／家族行已填、獨立性已判 | 同上 |
