# AGENTS.md — ai-workflow（重構中）

> 本 repo 正在第三輪重構（2026-09-04 起）。舊制規則、範本、設計文件與舊 CLI 凍結；舊入口文件全文在 `archive/rules-2026-09/`（唯讀，僅供對照）。

## 現在以什麼為準

1. `docs/research/REBUILD-DECISIONS-2026-09-04.md`：決策紀錄與**第零條**——CLI 提供資訊清單，AI 判斷；CLI 只確認清單有沒有填，⛔ 不做內容判讀。
2. `docs/research/REBUILD-SKELETON-2026-09-04.md`：新框架骨架（目錄、狀態機、卡面 schema、七動詞、交接文件、模組、命名）。
3. `docs/research/extract/`：舊規則萃取與 14 條衝突的量測與裁定。
4. 舊 commit trailer 三條（Requested-by／Planned-by／Implemented-by）與 `Reviewed-by` 的說明見 `archive/rules-2026-09/AGENTS.md`；凍結中的 `doctor.py` 仍以本行為錨。

新規則本體（`core/`、`stages/`、`roles/`、`modules/`）依骨架 §十三 的順序逐步填入；未填入前⛔ 不得引用 archive 內任何條文為判準。

## 舊根因家族對照（隨舊 CLI 封存）

下列字串由凍結中的測試 `test_agents_md_records_the_canonical_root_cause_id` 釘住，全表見 `archive/rules-2026-09/AGENTS.md`：

`commit-trailer-required-but-missing`；曾用名：`governance-provenance-trailer-omission`、`unknown-DEV-AIWF-MINIMAL-CI1-R2-002`
舊 trailer 檢查器只是偵測器，不在 push 也不在 merge 路徑上（原文在 `archive/rules-2026-09/AGENTS.md`；ROADMAP 仍以本行為錨）。
