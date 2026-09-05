---
name: review
when: 卡在審核階段：派審、查核、收裁決、決定過或退回
non_scope: ⛔ 不寫查核者的判準與紅線（住 roles/reviewer.md）；⛔ 不寫裁決 schema（住 core/handoff.md §2）
last_confirmed: 2026-09-05
---

# 審核階段

## 1 · 目標與產出

- 產出＝一則裁決留言（`wf:verdict`，`json wf-return`，`role=reviewer`）：`review_result`、`core_pain_resolved`、findings 八欄、`self_run`。
- 查核有序：R1 前提、R2 射程由 PM 在收件時判；R3 內容、R4 影響面由查核者判。

## 2 · 進入／離開條件

- 進入＝執行階段離開；派審前 `brief --for reviewer` 印分支頭、來源 SHA、`merge-tree` 三項，有紅即⛔ 不派。
- 離開＝APPROVE → 下一階段待辦（`move --ruling <裁決 URL>`）；REQUEST_CHANGES → 同階段退回再派執行者。
- 退回上一階段：R1 不過（上游產出失效、核心痛點與規格矛盾）→ 規劃／退回，階段計畫無規劃 → 需求／退回；R2–R4 不過 → 同階段退回。
- 同一 iteration 第 3 次退回的處置依 `roles/pm.md` F-PM-01。

## 3 · 狀態 delta

- 無。

## 4 · 階段內迴圈

- ① `notes --stage 審核` ② PM `brief --for reviewer`，人填段寫實際模型、已知未驗、本文件落差 ③ 查核者 `review --file --role reviewer` 貼裁決 ④ PM 判完整性與 `review_result` 對 findings 一致 ⑤ `move`。
- 派工單本身在被審範圍；查核者對派工錯記 `attribution` coordinator／planner。
- 送審後 PM `edit` 卡面先貼留言告知查核者（`core/verbs.md`）；改到規格欄＝退回規劃。
- 純文字交付只能關關於文字的痛點；痛點是關於世界的卡，`core_pain_resolved` 構造上答不成 yes。

## 5 · 各角色做／⛔ 不做

- 查核者：`self_run` 實跑、findings、自己貼裁決；⛔ 不代改分支、⛔ 不動狀態面。
- PM：派審、判裁決完整性；⛔ 不判裁決對錯、⛔ 不代轉錄內容。
- 需求方：T4 sign-off；升級四選一裁定。
- 執行者：收退回後修；⛔ 不自審。

## 6 · 注意事項

- F-審核-01：查核者的 `self_run` 與檢查在合併結果上跑，⛔ 不在分支頭上。
- F-審核-02：派審詞的基線、來源 SHA、iteration 一律由 `brief` 從狀態面產出；執行者再交回後必須重產，⛔ 不沿用上一輪。
- F-審核-03：無 `self_run` 的 APPROVE 無效；有 open blocking 或 `core_pain_resolved: no` 而 APPROVE 亦無效。

→ [archive/rules-2026-09/stage-rules/review.md](../archive/rules-2026-09/stage-rules/review.md)、[archive/rules-2026-09/templates/review-dispatch.md](../archive/rules-2026-09/templates/review-dispatch.md)、[archive/issues/130.md](../archive/issues/130.md)、[archive/issues/167.md](../archive/issues/167.md)
