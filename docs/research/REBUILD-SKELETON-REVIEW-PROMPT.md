# 骨架文件・跨實體審核提示（給 Codex）

你是本 repo 第三輪重構的跨實體查核者。你沒有本 session 的對話歷史；下面就是全部要求。

## 讀什麼（依序）

1. `docs/research/REBUILD-DECISIONS-2026-09-04.md`：已定案的決策，⛔ 不重審。
2. `docs/research/extract/00-consolidated.md` 與 `extract/07-conflicts.md`：萃取與衝突裁定，⛔ 不重審。
3. **被審物**：`docs/research/REBUILD-SKELETON-2026-09-04.md`。

## 只審四題（有序，前一題不過就停）

- **R1 前提**：骨架有沒有違反決策紀錄的任何一條？逐條列出違反處（引決策編號＋骨架節次）。
- **R2 射程**：骨架有沒有寫進「規則正文」（它只該定形狀）？有沒有漏掉 00 §十的 20 條空洞或 05 揭露的 3 條新洞的落點？
- **R3 內容**：§四轉移表有沒有死角（某狀態進得去出不來）？§六 schema 有沒有欄位是 CLI 讀不到卻要它驗的？§七六動詞的硬擋有沒有超出 `extract/00-consolidated.md` §二的 20 條？
- **R4 影響面**：§十三順序與停損能不能執行；§十四未定五題各給你的答案。

## 交回格式

一則 GitHub 留言，貼在本 repo 對應的 PR 上，首行 `wf:verdict`。內容：`review_result: APPROVE|REQUEST_CHANGES`；`findings` 逐條：id、severity、blocking、attribution（planner＝骨架作者）、evidence（引骨架節次逐字）、disposition。無 finding 逐字寫「無」。⛔ 不代改文件。⛔ 不用骨架沒寫的標準。
