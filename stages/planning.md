---
name: planning
when: 卡在規劃階段：寫規格、驗收條件、驗證項目，或父卡切子卡時
non_scope: ⛔ 不寫研究怎麼做（住 modules/research）；⛔ 不寫查核者怎麼審規格（住 roles/reviewer.md）
last_confirmed: 2026-09-05
---

# 規劃階段

## 1 · 目標與產出

- 產出＝規格（規格欄，`spec_version` 由 `edit` 自動 +1）、`acceptance` ≥1、`verification` 逐項指定誰跑、（父卡）帶 `parent` 的卡的切片與依賴序。
- 設計閘＝離開前 `verification` 填齊；純技術卡的設計判斷可寫「不適用」但 `verification` 項要寫理由。
- 規格只能在本階段改；執行與審核階段改規格＝退回本階段。

## 2 · 進入／離開條件

- 進入＝需求或研究階段離開；T0／T1 跳過本階段（`core/tiers.md` §1）。
- 離開＝PM 判 ④ 過：`move` 印的「`acceptance` 或 `verification` 空」為空；T4 另附質詢（`grilling`）。
- 退回本階段的入邊＝執行或審核階段 R1 不過（`core/state-machine.md`）。

## 3 · 狀態 delta

- 無。

## 4 · 階段內迴圈

- ① `notes --stage 規劃` ② PM 派執行者寫規格 ③ 交回卡面規格欄 ④ PM 有序判：R1 上游產出還有效嗎 → R2 射程對核心痛點 → 每條驗收條件可追溯回痛點、非零資訊、基線釘死 ⑤ `move`。
- 需求方裁定改到規格欄時，PM 以 `edit --ruling <URL>` 落卡面；只存在留言或對話的變更⛔ 不生效。
- 父卡基線變更：先更新父卡、標註受影響的帶 `parent` 的卡並重新核可，再繼續；⛔ 不只在下層卡內改方向。

## 5 · 各角色做／⛔ 不做

- 執行者：寫規格、驗收條件、驗證項目；⛔ 不改核心痛點、⛔ 不在未回寫下改已核可方向。
- PM：判 R1 R2 與驗收條件可追溯；⛔ 不判技術取捨。
- 需求方：核可取捨與驗收條件；T4 質詢；⛔ 不寫規格。
- 查核者：不在本階段。

## 6 · 注意事項

- F-規劃-01：⛔ 不拿全 repo 現況當本卡的標準；基線釘死 SHA 字面，⛔ 不動態算。
- F-規劃-02：每個檢查先寫出什麼結果會推翻它；零資訊的檢查⛔ 不列。
- F-規劃-03：驗收條件⛔ 不寫成自我指涉的字面 grep；指定掃描面並明示排除。
- F-規劃-04：間歇型缺陷預先登記可證偽預測；⛔ 不以「重跑幾次沒再現」結案。
- F-規劃-05：缺陷卡的驗證項目寫回歸測試檔與測試名，⛔ 不只寫「已加測試」。
- F-規劃-06：核心痛點的成功條件與裁定矛盾時更正痛點並逐字列排除與歸屬，⛔ 不縮射程。
- F-規劃-07：T2 以上的前提逐條附實查證據；未驗證前提標示且⛔ 不設為硬前置。
- F-規劃-08：測試⛔ 不依賴 repo 歷史存在；判準在合成樹上驗。

→ [archive/rules-2026-09/stage-rules/planning.md](../archive/rules-2026-09/stage-rules/planning.md)、[archive/rules-2026-09/templates/baseline-cascade.md](../archive/rules-2026-09/templates/baseline-cascade.md)、[archive/issues/088.md](../archive/issues/088.md)
