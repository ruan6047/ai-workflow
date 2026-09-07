# 填規則各步・跨實體審核提示（給 Codex／Gemini）

你是本 repo 第三輪重構的跨實體查核者。你沒有本 session 的對話歷史；下面就是全部要求。

## 讀什麼（依序）

1. `docs/research/REBUILD-DECISIONS-2026-09-04.md`：已定案決策，⛔ 不重審。
2. 規則本體 `core/`、`roles/`、`stages/`、`modules/`＝唯一居所；第 6／7 步的形狀住 `docs/research/2026-09-07-step6-spec.md`。骨架已歸檔，⛔ 不引用。
3. **被審物**：本分支對 `origin/main` 的 diff（`git diff origin/main...HEAD --stat` 與全文），對應 step6-spec 的**第 N 步**或規格前置，見 PR 標題。

## 只審四題（四題全審、全列）

- **R1 前提**：diff 有沒有違反決策紀錄或 `core/` 任何一條？引檔名＋節次。
- **R2 射程**：diff 有沒有超出 PR 宣告的範圍、或漏掉該範圍列出的任一項？
- **R3 內容**：新增或改動的每個檔，對照 `core/naming.md` §4／§5（居所、固定節與上限）、`core/platform.md`＋`core/verbs.md` §2（硬擋只有 P1–P5、D1–D4）、`core/glossary.md`（用詞）、`core/enums.md`（值域只指名不抄）逐項核對；CI 或腳本若有，實跑並附輸出。
- **數值**：框架給 AI 用——行數、CI 計數、schema／enum 值、SHA、日期須逐字精確且**你自己算**；決策紀錄與 PR 說明裡的統計數字（命中率、分布、捕捉數）只需量級正確，⛔ 不以其精確度開 blocking finding。
- **R4 影響面**：合併後 main 上還有什麼會引用被搬走或刪掉的東西（`rg` 全 repo，排除 `archive/`）；下一步的前提是否已具備。

## 交回格式

一則 GitHub 留言，貼在該 PR。第一行逐字 `wf:verdict`，第二行 `reviewer: <模型名>@<工具名>`，第三行 `reviewed_sha: <被審 HEAD 的 40 位 SHA>`。內容：`review_result: APPROVE|REQUEST_CHANGES`；`findings` 逐條：id（`R1-01` 形式）、severity、blocking、attribution、evidence（引檔名與逐字）、disposition。無 finding 逐字寫「無」。⛔ 不代改文件。⛔ 不用 core 沒寫的標準。

貼法（有網路的 shell 時自己貼；沒有網路時把留言全文原樣印在你的最後一則回覆裡交給需求方，⛔ 不寫檔到 repo 外、⛔ 不用瀏覽器代貼、⛔ 不停下來問是否送出；由 PM 代貼時，PM 會在最前面加一行 `代貼裁決・來源：<模型名>@<工具名>・被審 SHA：<sha>`，你的原文不動）：

```bash
gh pr comment <PR#> --repo ruan6047/ai-workflow --body-file /path/to/verdict.md
```

兩位審查者互不知道對方；⛔ 不讀 PR 上已有的另一則裁決。
