# AGENTS.md — ai-workflow

本 repo 只有 vNext：套件 `ai-workflow-vnext`（CLI `wfx`，原始碼 `vnext/cli/`），規則樹 `vnext/cli/src/wfx/rules/`，
需求基準 `docs/research/VNEXT-REQUIREMENTS-2026-09-21.md`，本 repo 專案層 `vnext/.wf/`。安裝、版本、文件見 `README.md`。

## 工作流程（wfx）

- 入口：`wfx/docs/ADOPTION.md` §1 的獨立 venv（預設 `$HOME/.venvs/wfx`，可換成實際位置；下行命令要跟著改）；以絕對路徑直接呼叫，⛔ 不依賴 PATH。
- 有卡：直接回該卡對話與任務專案經理 [Project Manager, PM] 續談；在本 repo 根目錄執行（`--project-root vnext` 指本 repo 的專案層 `vnext/.wf/` 所在目錄）
  `"$HOME/.venvs/wfx/bin/wfx" --project-root vnext brief --task <issue> --role <受派角色> --stage <當前階段>`，照輸出接手。
- 有卡但任務角色不明：先讀該卡正式來源，再請本卡 PM 補足派工；⛔ 不重新回入口排隊。
- 沒有卡：把目標、問題、證據與已做的修改交共同入口；共同協調查重、指派任務 PM，由被指派的 PM 開卡並分流到各卡對話。入口⛔ 不完成需求討論。
- 續談出現第二個主要成果：回共同入口查重，拆成相連任務；方向改動：在原卡停止目前階段、退回需求，由需求方裁定。
- ⛔ 不自行開卡、⛔ 不寫流程欄位。依據：每卡當值與寫入範圍（`wfx/rules/core/independence.md` §1）、共同協調（`wfx/rules/PM-coordination.md`）、開卡與關卡（`wfx/rules/core/github.md` §5）。

## 本 repo 補充

- 永遠使用繁體中文。
- commit trailer 與機密掃描的依據：`vnext/.wf/repo-guards.md`（brief 會自動注入）。
- 舊制（舊 `wf` CLI、舊規則四目錄、`archive/`、舊研究）已於 #417 刪除；對照用 `git show a1ea86f:<path>`，⛔ 不引為判準。
  舊卡依 #417 裁定改照 vNext（[Q6](https://github.com/ruan6047/ai-workflow/issues/417#issuecomment-6059993575)）。
