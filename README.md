# ai-workflow

多 AI 協作的任務治理框架：規則住這個 repo，卡與看板住各專案的 GitHub issue 與 Project。

## 1 · vNext

- 定位：可固定版本安裝的**試用基準**，⛔ 不宣稱全面穩定，⛔ 無自動升級。版本 `0.2.4`（唯一居所＝`vnext/cli/pyproject.toml`）。
- 範圍：舊制已於 #417 移除，舊卡改照 vNext（[Q6](https://github.com/ruan6047/ai-workflow/issues/417#issuecomment-6059993575)）。
- 內容：套件 `ai-workflow-vnext`、CLI `wfx`，動詞只有 `brief`／`facts`／`write`；規則樹隨套件出貨（`vnext/cli/src/wfx/rules/`：`core/`、`roles/`、`stages/`、選用文件模組 `modules/tdd/`）。
- 環境：Python **3.14**（`requires-python >=3.14`），`git` 與 `gh` 另行安裝。
- 安裝：取得對應版本的 wheel 後 `python -m pip install ai_workflow_vnext-0.2.4-py3-none-any.whl`；固定版本的 wheel 以 tag＋GitHub Release 附件發布，尚未發布前可自行 `python -m build --wheel --outdir <repo 外的目錄> vnext/cli`。
- 選用 TDD 文件模組：專案 `.wf/config.json` 加 `"modules": ["tdd"]`，只有 `執行`、`審核` 兩個階段有文件。**尚無真實專案啟用案例**，只經 CI 測試驗證；⛔ 不據此宣稱其他模組類型已驗證。
- 文件：CLI 契約 `vnext/cli/README.md`；採用流程（安裝、版本確認、升級、回退、移除）`vnext/cli/src/wfx/docs/ADOPTION.md`；需求邊界 `docs/research/VNEXT-REQUIREMENTS-2026-09-21.md`。

## 2 · 本 repo 的 CI 與守門

- CI job：`vnext-tests`（`.github/workflows/vnext.yml`）、`commit-trailer`、`secret-scan`（`.github/workflows/ci.yml`）。
- 兩個守門的依據：`vnext/.wf/repo-guards.md`。
- 哪些 job 是 main 的 required check 屬當下值，⛔ 不登記在本檔，用 `gh api repos/ruan6047/ai-workflow/rules/branches/main` 現查。

## 3 · 舊制對照

- 舊制（舊 `wf` CLI、舊規則與封存內容、舊研究）已於 #417 刪除，最後版本 `a1ea86f`。
- 對照用 `git show a1ea86f:<path>`；⛔ 不引為判準。
