---
name: platform
when: 設定 repo、改 ruleset、改 CI、判一條硬擋是不是平台委託時讀
non_scope: ⛔ 不寫 CLI 側硬擋 D1–D4（住 core/verbs.md §2）；⛔ 不寫怎麼操作 GitHub UI
last_confirmed: 2026-09-05
---

# 平台委託 P1–P5

每條＝規則一句＋執行 artifact。ruleset 與 CI 只是執行面；改 artifact 前先改本檔。

| # | 規則 | 執行 artifact | 2026-09-05 現況 |
|---|---|---|---|
| P1 | main 禁改史、禁刪 | ruleset 20768920：`deletion`、`non_fast_forward`、`required_linear_history`，bypass 清空 | ⚠️ 未設；第 7 步 |
| P2 | T2 以上走分支＋獨立查核；執行者不 merge | ruleset 20768920：required status checks `secret-scan`、`commit-trailer`＋PR | required checks 已設 `secret-scan`、`commit-trailer`（2026-09-05）；`reachability` 是否列入待需求方裁定 |
| P3 | 合併方式＝專案層 `merge_method`，由平台強制 | repo 設定：aiwf 只留 squash，關 merge 與 rebase 按鈕 | ⚠️ 三者皆開；第 7 步 |
| P4 | secrets 不進 git | CI job `secret-scan`（`.github/workflows/ci.yml`，gitleaks v3.0.0） | 已在 |
| P5 | commit trailer 鍵在允許集合且為末端連續單一區塊 | CI job `commit-trailer`（`.github/scripts/trailer_check.py`） | 已在 |

- P5 允許集合＝Requested-by、Planned-by、Implemented-by、Reviewed-by、Co-Authored-By；哪些必須出現＝約定，住 `roles/conduct-common.md` §2，CI ⛔ 不驗。
- P2 的獨立性判定（不同實體、跨家族）是 PM 注意事項，⛔ 不機械化。
- 平台擋不到的（UI 手改欄位、直推 main 的 T0／T1）＝紀律，住 `roles/conduct-common.md` §1。
- 新增平台委託須需求方裁定；⛔ 不加沒有被測物的 CI job。
