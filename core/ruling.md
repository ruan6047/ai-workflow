---
name: ruling
when: PM 組裁定單、需求方寫或讀 `wf-ruling` 區塊時
non_scope: ⛔ 不寫交接文件的共通規則（住 core/handoff.md）；⛔ 不寫裁定該怎麼判（住 roles/requester.md）；⛔ 不寫結案流程（住 stages/closeout.md）
last_confirmed: 2026-09-07
---

# 裁定單（PM → 需求方；`brief --for closeout` 或人手組）

| 段 | 誰填 | 內容 |
|---|---|---|
| 留言時間序 | CLI | `wf-return` 留言的時間序、各輪退回理由與 findings |
| 現況 | CLI | merge SHA、CI 狀態、四停下條件前三項（同 `finding_id` 最後一則 `wf-return` 的 `status: open` 且 `blocking: true`／CI 非綠／分支衝突） |
| 模組段 | 人（PM） | 已啟用模組宣告的裁定單段（`core/dispatch.md` 的 `wf-module-sections.closeout`）；無則不印 |
| 類別 | 人（PM） | 恰一個：升級／停止／撤銷／級別變更／結案確認／其他 |
| 各值證據 | 人（PM） | 四選一（換人／退回上一階段／停止／退回無效）各「若成立會是什麼證據」；只寫事實，⛔ 不含建議 |
| 復活條件、翻案把手 | 人（PM） | 停止類必填；翻案把手須可跑（`git revert <merge SHA>`），寫不出即逐字「無把手」＋原因 |
| 被繞過的要求 | 人（PM） | 級別下修類必填 |
| 裁定 | 需求方 | 一則 `wf:ruling` 留言，帶 `wf-ruling` 區塊 |

```json schema
{"$id": "wf-ruling", "type": "object", "additionalProperties": false, "required": ["kind", "reason"],
 "properties": {
  "kind": {"enum": ["block", "stop", "withdraw", "tier_change", "signoff", "other"]},
  "reason": {"type": "string"},
  "waiting_on": {"type": "string"}, "unblock_condition": {"type": "string"},
  "revive_condition": {"type": "string"}, "reversal_handle": {"type": "string"}}}
```

依 kind 的必要鍵：block＝reason、waiting_on、unblock_condition（加 CLI 寫的 `blocked.from` 共四欄）；stop＝reason、revive_condition、reversal_handle；其餘只要 reason。CLI 只驗鍵存在與型別；缺＝印。PM 代貼裁定時首行 `代貼裁定・授權來源：<session 或留言 URL>`；代貼裁決時首行 `代貼裁決・來源：<模型名>@<工具名>・被審 SHA：<sha>`。
