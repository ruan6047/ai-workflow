# CLAUDE.md — ai-workflow（重構中）

> 本 repo 正在第三輪重構（2026-09-04 起）。舊制規則、範本、設計文件與舊 CLI 全部封存在 `archive/rules-2026-09/`（唯讀，僅供對照）；舊 `wfcli` 凍結不再改。

## 現在以什麼為準

1. `docs/research/REBUILD-DECISIONS-2026-09-04.md`：決策紀錄與**第零條**——CLI 提供資訊清單，AI 判斷；CLI 只確認清單有沒有填，⛔ 不做內容判讀。
2. 規則本體 `core/`、`roles/`、`stages/`、`modules/`＝唯一居所（骨架已於 2026-09-07 歸檔至 `archive/research/`；第 6／7 步的形狀住 `docs/research/2026-09-07-step6-spec.md`）。
3. `docs/research/extract/`：舊規則萃取與 14 條衝突的量測與裁定。

第 0–5 步已填完；⛔ 不得引用 archive 內任何條文為判準。框架給 AI 用：數值由 AI 自己算，審核時尤其要自己算，⛔ 不以文件裡的統計數字為權威。

- 永遠使用繁體中文；commit 訊息末尾帶 `Co-Authored-By`。
- 本輪重構自舉期間不開卡；文件走 Codex／Gemini 跨實體審＋需求方 sign-off。
