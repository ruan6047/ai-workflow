---
name: dispatch
when: PM 組派工單，或執行者與查核者讀派工單時
non_scope: ⛔ 不寫交接文件的共通規則（住 core/handoff.md）；⛔ 不寫交回單（住 core/return.md）；⛔ 不寫裁定單（住 core/ruling.md）
last_confirmed: 2026-09-07
---

# 派工單（PM → 執行者或查核者；`brief --for executor|reviewer`）

| 段 | 誰填 | 內容 |
|---|---|---|
| 卡與身分 | CLI | 卡ID、issue、級別、階段、iteration、父卡、`when`、`from`／`to` 角色 |
| 核心痛點 | CLI | `core_pain` 逐字 |
| 驗收條件 | CLI | `acceptance` 逐條，一條一列，⛔ 不改寫不合併 |
| 非射程 | CLI | `non_scope` 逐條 |
| 基線 | CLI | 合併基底 SHA（merge-base，釘死字面）；`--for reviewer` 另列被審分支與 `source_sha` |
| 前輪 findings | CLI | 上一輪 `wf-return` 的 findings 逐條；無則逐字「無前輪」 |
| 能力層級建議 | CLI | 卡面 `exec_capability` 或 `review_capability` 的層級與理由 |
| 實際模型 | 人 | 實際跑的模型名＋偏離理由；與建議相符時逐字「相符」 |
| 注意事項 | CLI | `notes` 的編號清單全文 |
| 副作用入口 | CLI | 專案層 `.wf/contracts/*.md` 內 `json wf-contract` 區塊的 `side_effects` 陣列逐條；無區塊印「專案層未宣告」 |
| 寫入授權、唯讀範圍 | 人（PM） | 逐條列出；其餘唯讀 |
| 未驗項 | 人（PM） | PM 已知未驗，三分類各附原因 |
| 本文件落差 | 人（PM） | 無則逐字「無」 |
| 查核序 | 人（PM） | 本 iteration 內這是第幾份派審單，從 1 起；`--for executor` 不印 |
| 模組段 | 依模組條文 | 已啟用模組宣告的派工單段（下方 `wf-module-sections.brief`），段名逐字＝該模組 `adds.handoff_sections`；無則不印 |

模組段歸屬（段名逐字＝各模組 `adds.handoff_sections`；CI 對帳字串集合，⛔ 不讀內容）：

```json wf-module-sections
{"brief": {"resource-lock": ["資源宣告逐條", "寫入集交集"], "initiative": ["規格基線（父卡 spec_version 與本卡登記版本）"], "identity": ["身分三格（GitHub 帳號／session ID／訊息定位）"]},
 "closeout": {"escalation": ["升級單（三次退回逐字理由、四選一各值證據）"], "identity": ["身分三格（GitHub 帳號／session ID／訊息定位）"]}}
```

`brief` 同時印一份交回單 JSON 樣板：`card_id`、`iteration`、`role`、`acceptance` 條文、`note_responses` 的 id 預填；其餘由作者填。
