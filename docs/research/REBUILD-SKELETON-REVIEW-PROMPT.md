# 骨架文件・跨實體審核提示（給 Codex）

你是本 repo 第三輪重構的跨實體查核者。你沒有本 session 的對話歷史；下面就是全部要求。

## 讀什麼（依序）

1. `docs/research/REBUILD-DECISIONS-2026-09-04.md`：已定案的決策，⛔ 不重審。
2. `docs/research/extract/00-consolidated.md` 與 `extract/07-conflicts.md`：萃取與衝突裁定，⛔ 不重審。
3. **被審物**：`docs/research/REBUILD-SKELETON-2026-09-04.md`。

## 只審四題（有序，前一題不過就停）

- **R1 前提**：骨架有沒有違反決策紀錄的任何一條？逐條列出違反處（引決策編號＋骨架節次）。
- **R2 射程**：骨架有沒有寫進「規則正文」（它只該定形狀）？有沒有漏掉 00 §十的 20 項空洞或 05 揭露的 3 項新洞的落點？
- **R3 內容**：§四轉移表有沒有死角（某狀態進得去出不來）？§六 schema 有沒有欄位是 CLI 讀不到卻要它驗的？§七的七個動詞的硬擋有沒有超出 §三硬擋表（P1–P5、D1–D4）、或落在「寫壞資料」「指向不存在」兩類之外？
- **R4 影響面**：§十三順序與停損能不能執行；§十四的 5 條驗收條件你各自實測結果；§十五五題已裁定，只驗骨架有沒有照做；§十八詞表你認為缺哪些詞。

## 交回格式

一則 GitHub 留言，貼在 PR #245。第一行逐字 `wf:verdict`，第二行 `reviewer: <模型名>@<工具名>`（例如 `gpt-5@Codex`、`gemini-2.5-pro@Gemini CLI`）。內容：`review_result: APPROVE|REQUEST_CHANGES`；`findings` 逐條：id（`R1-01` 形式）、severity、blocking、attribution（planner＝骨架作者）、evidence（引骨架節次逐字）、disposition。無 finding 逐字寫「無」。⛔ 不代改文件。⛔ 不用骨架沒寫的標準。

貼法（有 shell 時自己貼；沒有就把留言全文交給需求方貼）：

```bash
gh pr comment 245 --repo ruan6047/ai-workflow --body-file /path/to/verdict.md
```

兩位審查者互不知道對方；⛔ 不讀 PR 上已有的另一則裁決。
