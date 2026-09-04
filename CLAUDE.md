# CLAUDE.md — ai-workflow（重構中）

> 本 repo 正在第三輪重構（2026-09-04 起）。舊制規則、範本、設計文件與舊 CLI 全部封存在 `archive/rules-2026-09/`（唯讀，僅供對照）；舊 `wfcli` 凍結不再改。

## 現在以什麼為準

1. `docs/research/REBUILD-DECISIONS-2026-09-04.md`：決策紀錄與**第零條**——CLI 提供資訊清單，AI 判斷；CLI 只確認清單有沒有填，⛔ 不做內容判讀。
2. `docs/research/REBUILD-SKELETON-2026-09-04.md`：新框架骨架（目錄、狀態機、卡面 schema、七動詞、交接文件、模組、命名）。
3. `docs/research/extract/`：舊規則萃取與 14 條衝突的量測與裁定。

新規則本體（`core/`、`stages/`、`roles/`、`modules/`）依骨架 §十三 的順序逐步填入；未填入前⛔ 不得引用 archive 內任何條文為判準。

- 永遠使用繁體中文；commit 訊息末尾帶 `Co-Authored-By`。
- 本輪重構自舉期間不開卡；文件走 Codex／Gemini 跨實體審＋需求方 sign-off。
