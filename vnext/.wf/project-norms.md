# ai-workflow 專案規範宣告

本 repo 的既有方向本體為 `docs/research/VNEXT-REQUIREMENTS-2026-09-21.md` §1「產品目標」，連同文件前言已生效增補及本次適用的責任邊界閱讀（§2「共通原則」、§5「角色與責任」、§7「偏移、根因與停止條件」、§10「規則與專案注入」、§11「CLI 與平台邊界」、§14「重建與採用」）；實際生效規則依 `vnext/cli/src/wfx/rules/`。這是方向短定位，不是下節專案規範宣告；四個品質目標的列項順序不代表需求方已裁定跨卡優先序。

需求方確認來源：2026-10-23 本次對話已核定的藍圖目標對齊方案；本定位不另定專案優先順位或任務進度。短定位及權威定義見 `vnext/cli/src/wfx/rules/core/boundaries.md` §3。

## 專案規範

- vnext/.wf/repo-guards.md：為本 repo 修改提交、持續整合 [Continuous Integration, CI] 或平台守門時對照其保護目的與既有檢查邊界；不新增必填尾註，不把提前預跑當既有 CI。
- vnext/.wf/model-policy.md：本 repo 派工與維護模型資料時，對照資料分層、unknown、已登記裁定及工具原樣呈現邊界。
