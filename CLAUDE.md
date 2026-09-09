# CLAUDE.md — ai-workflow

> 舊制規則、範本、設計文件與舊 CLI 全部封存在 `archive/rules-2026-09/`（唯讀，僅供對照）；舊 `wfcli` 凍結不再改。

## 現在以什麼為準

1. `docs/research/REBUILD-DECISIONS-2026-09-04.md`：決策紀錄與**第零條**——CLI 提供資訊清單，AI 判斷；CLI 只確認清單有沒有填，⛔ 不做內容判讀。
2. 規則本體 `core/`、`roles/`、`stages/`、`modules/`＝唯一居所（骨架與第 6／7 步的形狀已歸檔至 `archive/research/`，⛔ 不引為判準）。
3. `docs/research/extract/`：舊規則萃取與 14 條衝突的量測與裁定。

⛔ 不得引用 archive 內任何條文為判準。框架給 AI 用：數值由 AI 自己算，審核時尤其要自己算，⛔ 不以文件裡的統計數字為權威。

- 永遠使用繁體中文；commit 訊息末尾帶 `Co-Authored-By`。
- 工作走卡：提案者貼 `json wf-intake`、需求方決定升不升級、PM `open` 上板（`ADOPTION.md` §4、`stages/requirement.md`）。查核依 `core/tiers.md` §1 的級別要求。
