---
name: repo-guards
when: 為 ai-workflow 寫 commit、改 CI 或 ruleset、判斷一條守門保護什麼時讀
last_confirmed: 2026-10-08
---

# ai-workflow 的 repo 守門依據

本檔是**專案層補充**（boundaries.md §3），只寫本 repo 的守門；⛔ 不隨套件發給採用者。平台層（ruleset、CI）擋不可逆事故，其餘交人或 AI 判斷。

## 1 · secret-scan

- 保護：機密不進 git。執行 artifact＝`.github/workflows/ci.yml` 的 `secret-scan` job（gitleaks，掃 PR 或 push 範圍的 commit）。

## 2 · commit-trailer

- 保護：commit 的來源可追溯。執行 artifact＝`ci.yml` 的 `commit-trailer` job（`.github/scripts/trailer_check.py`）。
- CI 只驗兩件事：鍵在允許集合內；trailer 是訊息末端的連續單一區塊。merge 與 squash commit 一樣受驗。
- 允許集合（不分大小寫）：`Requested-by`（需求方）、`Planned-by`（規劃者）、`Implemented-by`（執行者）、`Reviewed-by`（審核者）、`Co-Authored-By`（協作署名）。
- CI ⛔ 不驗哪些鍵必須出現，本檔也⛔ 不設必填義務。
- 已知漏洞：平台預設組出的 squash 訊息會用空行拆散 trailer，所以合併訊息由 PM 自己組。

## 3 · 預設分支的穩定身分

- P1：預設分支 ruleset 的規則型別 `deletion`、`non_fast_forward`、`required_linear_history`，bypass 為空。
- P3：repo 只開 squash 合併。

當下值（required check 集合、ruleset id、action 版本）⛔ 不寫在本檔，用唯讀查法現查：
`gh api repos/ruan6047/ai-workflow/rules/branches/main`、`gh api repos/ruan6047/ai-workflow --jq '{allow_merge_commit,allow_squash_merge,allow_rebase_merge}'`。
