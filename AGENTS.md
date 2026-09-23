# AGENTS.md — ai-workflow

## vNext 試用基準的適用範圍

`vnext/` 是明確選用的 vNext 試用基準（入口見 `README.md` §4），以 `docs/research/VNEXT-REQUIREMENTS-2026-09-21.md` 作為已核定的需求與流程邊界；規則本體住 `vnext/cli/src/wfx/rules/`。

- 明確選用 vNext 的任務使用該文件定義的五階段輕量流程；具體新規則尚未經需求方確認前，不得自行補成生效規則。
- 既有 `core/`、`roles/`、`stages/`、`modules/`、舊 CLI、舊卡片格式、tier、計數器與 trailer 規則只供歷史及重用評估，不得作為 vNext 的派工、退回或驗收判準。
- 不逐檔註解、搬移或修改既有規則來模擬 vNext；vNext 的成果放在 `vnext/`。
- 未選用 vNext 的任務與既有舊卡仍依下節的現行規則運作；vNext ⛔ 不自動切換任何專案、舊卡或版本。

> 舊制規則、範本、設計文件與舊 CLI 凍結；舊入口文件全文在 `archive/rules-2026-09/`（唯讀，僅供對照）。

## 現在以什麼為準

1. `docs/research/REBUILD-DECISIONS-2026-09-04.md`：決策紀錄與**第零條**——CLI 提供資訊清單，AI 判斷；CLI 只確認清單有沒有填，⛔ 不做內容判讀。
2. 規則本體 `core/`、`roles/`、`stages/`、`modules/`＝唯一居所（骨架與第 6／7 步的形狀已歸檔至 `archive/research/`，⛔ 不引為判準）。
3. `docs/research/extract/`：舊規則萃取與 14 條衝突的量測與裁定。
4. 舊 commit trailer 三條（Requested-by／Planned-by／Implemented-by）與 `Reviewed-by` 的說明見 `archive/rules-2026-09/AGENTS.md`。⛔ 無機械錨——舊 `doctor.py` 已隨舊 CLI 封存，CI 只跑 `cli/tests`。現行的 trailer 規則住 `core/platform.md` P5，檢查器＝`.github/scripts/trailer_check.py`。

⛔ 不得引用 archive 內任何條文為判準。框架給 AI 用：數值由 AI 自己算，審核時尤其要自己算，⛔ 不以文件裡的統計數字為權威。

## 舊根因家族對照（隨舊 CLI 封存）

下列字串留作人讀對照，全表見 `archive/rules-2026-09/AGENTS.md`。⛔ 無機械錨——`test_agents_md_records_the_canonical_root_cause_id` 讀的是 `archive/rules-2026-09/AGENTS.md`（該測試住 `archive/rules-2026-09/cli/tests/test_doctor.py`，`parents[2]` 解析到 `archive/rules-2026-09`），且 CI 只跑 `cli/tests`、⛔ 不跑 archive：

`commit-trailer-required-but-missing`；曾用名：`governance-provenance-trailer-omission`、`unknown-DEV-AIWF-MINIMAL-CI1-R2-002`
舊 trailer 檢查器只是偵測器，不在 push 也不在 merge 路徑上（原文在 `archive/rules-2026-09/AGENTS.md`；ROADMAP 已隨舊 CLI 封存於 `archive/rules-2026-09/docs/ROADMAP.md`）。
