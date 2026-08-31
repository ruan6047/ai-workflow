---
name: stage-review
status: draft-pending-initiative
description: 審核階段：產出可稽核的裁決。本階段的執行者＝查核者。
---
> ⛔ **草稿·未生效**。生效走 WORKFLOW-REDESIGN-2026-08-30 施工卡（四波五卡）；在此之前⛔ 不得作為現行規則引用。

# 審核階段

## 1 核心目標
產出物＝結構化裁決（review_result＋core_pain_resolved＋self_run＋findings）。進入＝執行 ④ 過。離開＝APPROVE → 直行合併（丙 授權、四停下條件）；REQUEST_CHANGES → 執行／退回。

## 2 狀態與轉移
通用 7。「退回無效」⛔ 非本階段狀態——是升級裁定第 ④ 值。

## 3 階段內流程
② PM 派審詞（信封：merge-base 基線釘死、前輪 findings＋root_cause_id、模型／家族行、PM 已知未驗項）。③ 查核者裁決，有通道者自己寫回。④ PM 對裁決完整性（段落＋身分自述）。⑤ 依裁決路由。⭐ 同 root_cause 第三輪 ⇒ ⛔ 不派第四輪，直接升級。

## 4 各角色
| 角色 | 做 | ⛔ 不做 |
|---|---|---|
| 查核者（＝本階段執行者） | self_run 實跑；findings；寫回；身分自述 | 不代改；不裁研究結論真值；不用卡面沒有的標準 |
| PM | ② 派審詞；④ 完整性；直行收尾（四停下條件內） | 不判裁決對錯；不代轉錄 |
| 需求方 | 升級裁定；T4 sign-off | — |

## 5 注意事項（9）
1. 基線＝merge-base 算出並釘死字面，⛔ 不抄 origin/main
2. 轉手 finding 等於背書——先驗 artifact 是誰寫的＋機制有沒有 writer
3. self_run 實跑；rc 分開取⛔ 不接管線
4. core_pain_resolved 第一判準、具否決權
5. 證據逐字轉錄⛔ 不摘要⛔ 不加緩和語
6. ⛔ 不代改
7. root_cause_id 對照前輪（派審詞必列）；同根因第三輪 ⇒ 升級
8. 守衛在合併結果上跑
9. 裁決含身分自述（session ID＋訊息定位）；有通道者自己寫回
