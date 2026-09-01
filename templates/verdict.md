# 裁決範本 (Verdict)

> 承載 `stage-rules/review.md` §3 的 ③ 與 `stage-rules/reviewer-conduct.md` 一。這是**人讀的裁決全文**範本。
> ⚠️ **與 [`review-prompt.md`](review-prompt.md) 的分工**：那份是 `wfcli review` 寫入前解析的**結構化輸出 schema**（機器面，欄位與列舉由它定義）；本份是**人讀範本**（把同一次裁決寫成收件者讀得懂的文件）。schema 欄位的權威居所在那邊，⛔ 本檔不重複定義、⛔ 不自創欄位。兩者**同一次裁決的兩種呈現**，⛔ 不是兩次裁決。
> 信封四段的權威定義在 [`handoff-contract.md`](handoff-contract.md) §3.3，⛔ 本檔不重寫定義。
> ⚠️ 看板值仍為舊語彙（15 值），對照見決議 §一；切換於切換 Initiative。

## 信封一 · 卡與身分

- 卡ID／Issue：`<CARD_ID>`（`<owner/repo>#<n>`）　級別：`<T0–T4>`　Initiative：`<父卡／—>`
- spec 基線：`<spec_version>`　階段：`審核`　輪次：`R<n>`　escalation epoch：`<e<N>>`
- from：`<查核者 模型@工具／人工>`　to：`<PM 帳號>`
- 被審分支：`<branch>`　`source_sha`：`<完整 40 碼；已核對等於 git rev-parse HEAD>`
- 基線（merge-base，取自派審詞的釘死字面）：`<完整 40 碼>`
- 核心痛點（卡面原文逐字）：`<原文>`
- 模型：實際 `<模型@工具>`　卡面建議 `<經濟型／主力型／高階型>`　偏離理由 `<相符時填「相符」；另註明與執行者是否同家族>`

## 信封二 · 身分自述

- 查核者 GitHub 帳號：`<帳號>`
- session ID：`<Claude：~/.claude/projects/<cwd>/<id>.jsonl 的 <id>；Codex：rollout-<時間>-<id>.jsonl 的 <id>>`
- 該則訊息定位：`<Claude：訊息 uuid；Codex：該則 timestamp>`
- ⭐ 缺這三格＝PM 的 ④「裁決完整性」不過，退回補。⚠️ 這是自述，但它**指向一份本機 transcript**，而 transcript 裡的模型欄是 harness 寫的——造假仍可能，但造假會被抓到。

## 信封三 · 機械指令

> `self_run`：查核者**自己實跑**的指令與觀察，⛔ 不只讀碼、⛔ 不轉抄執行者的輸出。rc 分開取、⛔ 不接管線。

| # | 指令 | rc | 觀察到的輸出（原始，⛔ 不摘要） |
|---|---|---|---|
| 1 | `<指令逐字>` | `<rc>` | `<數字／關鍵行>` |

- ⚠️ 守衛在**合併結果**上跑，⛔ 不在分支頭上。
- ⚠️ **沒有 `self_run` 的 `APPROVE` 無效**——記 `review-invalid`，不計 iteration。

## 信封四 · 已知未驗項

> 查核者自己沒驗到的，逐項＋各自原因，三分類擇一。⛔ 不因「執行者說他驗過了」而略去。

| # | 未驗項 | 分類 | 原因 |
|---|---|---|---|
| 1 | `<項目>` | `驗不了`／`沒去驗`／`刻意不驗` | `<原因>` |

---

## 1. 第一判準（具否決權）

- `core_pain_resolved`：`yes` ／ `no`
- 證據：`<逐字；⛔ 不摘要>`
- ⚠️ 痛點未消 ⇒ 一律 `REQUEST_CHANGES`，**即使驗收清單全過**，並指出清單與痛點脫節之處（`attribution: planner`）。

## 2. 結論

- `review_result`：`APPROVE` ／ `REQUEST_CHANGES`
- 一句話理由：`<與 findings 語意一致；不一致時 wfcli review 會擋下>`

## 3. 逐項驗收清單

| AC | 判定 | 證據（逐字轉錄，⛔ 不摘要⛔ 不加緩和語） |
|---|---|---|
| `<AC 條文逐字>` | `過`／`不過` | `<指令＋輸出>` |

## 4. Findings

> 欄位與列舉的權威居所＝[`review-prompt.md`](review-prompt.md) §5（八欄全必填）與 [`review-escalation.md`](review-escalation.md) §2。無 finding 時逐字寫「無」，⛔ 不留空。

### `<CARD_ID>`-R`<n>`-`<序>`

- severity：`<critical｜major｜minor｜info>`　blocking：`<true｜false>`
- finding_class：`<implementation｜authoritative-artifact｜governance｜coordination｜environment>`
- attribution：`<executor｜planner｜coordinator｜reviewer｜external>`
- root_cause_id：`<穩定根因家族字串；沿用派審詞所列前輪的同一字串>`
- evidence：`<可重現的重現方式或來源>`
- disposition：`<要求的修法或決策>`

⭐ **同 `root_cause_id` 第三輪**：寫明並建議升級，⛔ 不再開新輪。

## 5. 高階型研究卡的對抗性反測

> ≥3 個**不同族**角度（時間外／母體外／洩漏探針／重抽／規則邊界）。角度不適用寫 `不適用：<原因>`，⛔ 不硬湊。⛔ 不裁結論真值——只驗量測可重跑。

| 角度 | 結果 |
|---|---|
| `<角度>` | `支持`／`推翻`／`未能檢定`／`不適用：<原因>` |

- ⛔ 非高階型研究卡時逐字寫「不適用：本卡非高階型研究卡」，⛔ 不刪本節。

## 6. 範圍外發現

> ⛔ 不擴大 finding 集合、⛔ 不開卡、⛔ 不代改。本節交 PM 轉需求方裁決。

- `<逐條；無則逐字寫「無」>`

## 7. 寫回

- 有寫入通道者自己寫回：先 `wfcli review --validate-only` 自檢，過了再正式寫。
- 無通道者交 PM 轉錄；轉錄時 PM ⛔ 不判裁決對錯，只對「該有的段落有沒有」。
- ⚠️ 收據（`wf-review-receipt:v1`）是**選配**：有 GitHub 寫入通道時可自行留一則，PM 轉錄前重算 hash 並在 evidence 引用其 URL。無收據時查核者身分只有自由文字，任何依賴「誰查核的」做判斷的流程不得單獨採信。
- ⛔ 正文不得出現事件 marker 前綴的完整字面（doctor 全文子字串比對，出現即隔離整卡）。
