# ai-workflow

多 AI 協作的任務治理框架：規則住這個 repo，卡與看板住各專案的 GitHub issue 與 Project。

> 本檔 §1–§3 描述舊制 `wf`。新任務可明確選用 vNext 試用基準，見 §4；兩者⛔ 不混用，也⛔ 不自動切換。

## 1 · 心智模型

- CLI 提供資訊清單，AI 判斷；CLI 只確認清單有沒有填，⛔ 不做內容判讀。
- 一張卡＝一個 issue；卡面＝issue body 裡一個 `json wf-card` 區塊；狀態面＝Project 五欄，全由 CLI 回寫。
- 八階段固定序住 `core/enums.md` `stages`；研究、部署、維護由卡面 `stage_plan` 決定存不存在。
- 每階段五步：① `notes` ② `brief` 派工 ③ 交回 ④ PM 判完整性與 R1 R2 ⑤ `move`。
- 四角色：需求方出題與裁定、PM 收送件、執行者做、查核者審。
- 硬擋只有九條：平台 P1–P5、CLI D1–D4；其餘一律印，交人或 AI 判。
- 一條規則只住一處；理由與來歷用連結指 `archive/`。
- 模組 opt-in：卡級看卡面欄，專案級看 `.wf/modules.json`；未啟用＝該模組的每一項都不存在。
- 注意事項一份清單四個來源（框架 F-、模組 F-、專案 P-、卡面 T-）：合成時單向累加、不覆寫、無豁免鍵；過期條目由需求方裁定退場。

## 2 · 角色一句話

- 需求方：決定做不做、裁定、sign-off；⛔ 不代填表單。
- PM：開卡、派工、派審、收件、`move`、組裁定單、維護注意事項；⛔ 不判內容對錯。
- 執行者：實作、量測、寫規格、交交回單；⛔ 不 merge、⛔ 不自審（T2 以上）。
- 查核者：判 R3 內容與 R4 影響面、`self_run` 實跑、貼裁決；⛔ 不代改分支。

## 3 · 查詢指令

- 讀規則的順序：`core/glossary.md` → `core/state-machine.md` → 你的角色檔 `roles/` → 當下階段檔 `stages/`。
- 新專案怎麼接：`ADOPTION.md`；五個 step 走 `wf snapshot --adopt <install|preflight|bootstrap|smoke|deactivate>`（`core/adopt.md`）。
- 執行環境：本框架唯一支援的 Python 版本是 3.14（`cli/pyproject.toml` 的 `requires-python` 逐字為 `>=3.14`；`.github/workflows/ci.yml` 裡每一個有 Python 消費點的 job 都以 `actions/setup-python` 釘 `"3.14"`）；⛔ 不承諾 3.11、3.12 或 3.13，⛔ 無以 Python 版本為維度的 CI 矩陣。
- 活卡與看板：`gh project list --owner <帳號>` 取板號，再 `gh project item-list <N> --owner <帳號>`。
- 平台硬擋現況：`gh api repos/<owner>/<repo>/rulesets`。
- 舊制規則與範本：`archive/rules-2026-09/`（唯讀，僅供對照）。

## 4 · vNext 試用基準（明確選用）

- 定位：可固定版本安裝的**試用基準**，⛔ 不宣稱全面穩定，⛔ 無自動升級。版本 `0.1.1`（唯一居所＝`vnext/cli/pyproject.toml`）。
- 範圍：選用 vNext 的新任務才適用。既有專案、舊卡與舊 `wf` ⛔ 不自動切換；舊卡照原流程完成，舊制內容維持封存對照。
- 內容：套件 `ai-workflow-vnext`、CLI `wfx`，動詞只有 `brief`／`facts`／`write`；規則樹隨套件出貨（`vnext/cli/src/wfx/rules/`：`core/`、`roles/`、`stages/`、選用文件模組 `modules/tdd/`）。
- 環境：Python **3.14**（`requires-python >=3.14`），`git` 與 `gh` 另行安裝。
- 安裝：取得對應版本的 wheel 後 `python -m pip install ai_workflow_vnext-0.1.1-py3-none-any.whl`；固定版本的 wheel 以 tag＋GitHub Release 附件發布，尚未發布前可自行 `python -m build --wheel --outdir <repo 外的目錄> vnext/cli`。
- 選用 TDD 文件模組：專案 `.wf/config.json` 加 `"modules": ["tdd"]`，只有 `執行`、`審核` 兩個階段有文件。**尚無真實專案啟用案例**，只經 CI 測試驗證；⛔ 不據此宣稱其他模組類型已驗證。
- 文件：CLI 契約 `vnext/cli/README.md`；採用流程（安裝、版本確認、升級、回退、移除）`vnext/cli/src/wfx/docs/ADOPTION.md`；需求邊界 `docs/research/VNEXT-REQUIREMENTS-2026-09-21.md`。
