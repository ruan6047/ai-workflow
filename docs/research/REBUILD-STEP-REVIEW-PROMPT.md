# 填規則各步・跨實體審核提示（給 Codex／Gemini）

你是本 repo 第三輪重構的跨實體查核者。你沒有本 session 的對話歷史；下面就是全部要求。

## 讀什麼（依序）

1. `docs/research/REBUILD-DECISIONS-2026-09-04.md`：已定案決策，⛔ 不重審。
2. `docs/research/REBUILD-SKELETON-2026-09-04.md`：骨架（已 APPROVE 並 sign-off），本步的形狀規格；⛔ 不重審骨架本身。
3. **被審物**：本分支對 `origin/main` 的 diff（`git diff origin/main...HEAD --stat` 與全文），對應骨架 §十三 的**第 N 步**，N 見 PR 標題。

## 只審四題（四題全審、全列）

- **R1 前提**：diff 有沒有違反決策紀錄或骨架任何一條？引編號＋節次。
- **R2 射程**：diff 有沒有超出第 N 步在 §十三 的範圍、或漏掉該步列出的任一項？
- **R3 內容**：新增或改動的每個檔，對照 §一（居所）、§二（固定節與上限）、§三（硬擋）、§十八（用詞）逐項核對；CI 或腳本若有，實跑並附輸出。
- **R4 影響面**：合併後 main 上還有什麼會引用被搬走或刪掉的東西（`rg` 全 repo，排除 `archive/`）；下一步的前提是否已具備。

## 交回格式

一則 GitHub 留言，貼在該 PR。第一行逐字 `wf:verdict`，第二行 `reviewer: <模型名>@<工具名>`，第三行 `reviewed_sha: <被審 HEAD 的 40 位 SHA>`。內容：`review_result: APPROVE|REQUEST_CHANGES`；`findings` 逐條：id（`R1-01` 形式）、severity、blocking、attribution、evidence（引檔名與逐字）、disposition。無 finding 逐字寫「無」。⛔ 不代改文件。⛔ 不用骨架沒寫的標準。

貼法（有 shell 時自己貼；沒有就把留言全文交給需求方貼；由 PM 代貼時，PM 會在最前面加一行 `代貼裁決・來源：<模型名>@<工具名>・被審 SHA：<sha>`，你的原文不動）：

```bash
gh pr comment <PR#> --repo ruan6047/ai-workflow --body-file /path/to/verdict.md
```

兩位審查者互不知道對方；⛔ 不讀 PR 上已有的另一則裁決。
