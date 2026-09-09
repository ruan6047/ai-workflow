# AGENTS.md — ai-workflow

> 舊制規則、範本、設計文件與舊 CLI 凍結；舊入口文件全文在 `archive/rules-2026-09/`（唯讀，僅供對照）。

## 現在以什麼為準

1. `docs/research/REBUILD-DECISIONS-2026-09-04.md`：決策紀錄與**第零條**——CLI 提供資訊清單，AI 判斷；CLI 只確認清單有沒有填，⛔ 不做內容判讀。
2. 規則本體 `core/`、`roles/`、`stages/`、`modules/`＝唯一居所（骨架與第 6／7 步的形狀已歸檔至 `archive/research/`，⛔ 不引為判準）。
3. `docs/research/extract/`：舊規則萃取與 14 條衝突的量測與裁定。
4. 舊 commit trailer 三條（Requested-by／Planned-by／Implemented-by）與 `Reviewed-by` 的說明見 `archive/rules-2026-09/AGENTS.md`；凍結中的 `doctor.py` 仍以本行為錨。

⛔ 不得引用 archive 內任何條文為判準。框架給 AI 用：數值由 AI 自己算，審核時尤其要自己算，⛔ 不以文件裡的統計數字為權威。

## 舊根因家族對照（隨舊 CLI 封存）

下列字串留作人讀對照，全表見 `archive/rules-2026-09/AGENTS.md`。⛔ 無機械錨——`test_agents_md_records_the_canonical_root_cause_id` 讀的是 `archive/rules-2026-09/AGENTS.md`（該測試住 `archive/rules-2026-09/cli/tests/test_doctor.py`，`parents[2]` 解析到 `archive/rules-2026-09`），且 CI 只跑 `cli/tests`、⛔ 不跑 archive：

`commit-trailer-required-but-missing`；曾用名：`governance-provenance-trailer-omission`、`unknown-DEV-AIWF-MINIMAL-CI1-R2-002`
舊 trailer 檢查器只是偵測器，不在 push 也不在 merge 路徑上（原文在 `archive/rules-2026-09/AGENTS.md`；ROADMAP 已隨舊 CLI 封存於 `archive/rules-2026-09/docs/ROADMAP.md`）。
