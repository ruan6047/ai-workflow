---
name: params
when: 任何規則或 CLI 輸出引用一個設計值時，來這裡查現值
non_scope: ⛔ 不放模組參數（住專案 `.wf/modules.json` 的 `params`）；⛔ 不放理由
last_confirmed: 2026-09-05
---

# 設計值參數

皆為 2026-09-04 種子值，填規則時可調；改值＝改本檔一列。

| 參數 | 種子值 | 用在 |
|---|---|---|
| promote_threshold | 3 張卡 | 同一 T- 注意事項被 3 張卡引用即列為 P- 候選（`roles/pm.md` §4） |
| retire_threshold | 20 張結案卡 | 注意事項 `last_cited` 落後 20 張結案卡即列為退場候選（`roles/pm.md` §4） |
| guard_review_period | 20 張結案卡 | 需求方定期回看的週期（`roles/requester.md` §1） |
| rule_confirm_days | 90 天 | 規則檔 `last_confirmed` 超過即由 `brief` 標 ⚠️ 過期 |
