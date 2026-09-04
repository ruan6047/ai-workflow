---
name: handoff
when: 組派工單、寫交回單、寫裁定單、寫或讀 `wf-return`／`wf-ruling` 區塊時讀
non_scope: ⛔ 不寫怎麼判交回單對不對（住 roles/pm.md、roles/reviewer.md）；⛔ 不寫卡面欄（住 core/card-schema.md）
last_confirmed: 2026-09-05
---

# 三份交接文件

每段首行 `[來源: <來源>/<檔>#<節> · confirmed <日期>]`。CLI 段由 `brief` 從卡面 JSON、git、規則檔組；人填段只由該角色本人填；缺段印。

## 1 · 派工單（PM → 執行者或查核者；`brief --for executor|reviewer`）

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
| 副作用入口 | CLI | 專案層 `.wf/contracts/` 所列；缺檔印「專案層未宣告」 |
| 寫入授權、唯讀路徑 | 人（PM） | 逐條列出；其餘唯讀 |
| 未驗項 | 人（PM） | PM 已知未驗，三分類各附原因 |
| 本文件落差 | 人（PM） | 無則逐字「無」 |

`brief` 同時印一份交回單 JSON 樣板：`card_id`、`iteration`、`role`、`acceptance` 條文、`note_responses` 的 id 預填；人只填判斷欄。

## 2 · 交回單（執行者或查核者 → PM；`review --file`）

| 段 | 誰填 | 內容 |
|---|---|---|
| 卡與身分 | CLI | 同派工單；另列 `source_sha`、commit 清單（`git log`）、改動面（`git diff --stat` 每檔一列）、`finding_id`（`review` 依 `core/naming.md` 編） |
| self_run | 人 | 實跑的指令、rc、原始輸出；⛔ 不讀碼推論、⛔ 不轉抄他人輸出 |
| 逐條驗收 | 人 | 每條 `acceptance`：做法／證據／falsifier，⛔ 不合併 |
| 失誤登記 | 執行者 | 逐項：失誤／何時／影響／補救；無則逐字「無」 |
| findings | 查核者 | 八欄逐條（schema）；無則逐字「無」 |
| 未驗清單 | 人 | 每項 `{item, kind, reason}`；kind＝cannot／skipped／deferred；reason 非空 |
| 注意事項回應 | 人 | 對 `notes` 印出的每個 id 一條 `{id, value, text}`；value＝followed／not_applicable／found；後兩者 text 非空 |
| 射程外發現 | 人 | 只寫進本段交需求方；⛔ 不開卡、⛔ 不 spawn 背景任務；無則「無」 |
| 裁決 | 查核者 | `review_result`、`core_pain_resolved`、一句話理由 |

必填性依級別：T0／T1 只要 `self_run` 與逐條驗收（schema 的 `required`）；T2 以上全段，缺段由 `review` 依卡面 `tier` 印，⛔ 不進 schema。

```json schema
{"$id": "wf-return", "type": "object", "additionalProperties": false,
 "required": ["card_id", "iteration", "role", "source_sha", "self_run", "acceptance"],
 "properties": {
  "card_id": {"type": "string"}, "iteration": {"type": "integer"}, "role": {"enum": ["executor", "reviewer"]},
  "source_sha": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
  "self_run": {"type": "array", "minItems": 1, "items": {"type": "object", "required": ["command", "rc", "observed"], "additionalProperties": false,
               "properties": {"command": {"type": "string"}, "rc": {"type": "integer"}, "observed": {"type": "string", "minLength": 1}}}},
  "acceptance": {"type": "array", "items": {"type": "object", "required": ["text", "method", "evidence", "falsifier"], "additionalProperties": false,
                 "properties": {"text": {"type": "string"}, "method": {"type": "string"}, "evidence": {"type": "string"}, "falsifier": {"type": "string"}}}},
  "mistakes": {"type": "array", "items": {"type": "object", "required": ["what", "when", "impact", "fix"], "additionalProperties": false,
               "properties": {"what": {"type": "string"}, "when": {"type": "string"}, "impact": {"type": "string"}, "fix": {"type": "string"}}}},
  "findings": {"type": "array", "items": {"type": "object", "additionalProperties": false,
               "required": ["finding_id", "severity", "blocking", "finding_class", "attribution", "root_cause_id", "evidence", "disposition"],
               "properties": {"finding_id": {"type": "string"}, "severity": {"enum": ["critical", "major", "minor", "info"]}, "blocking": {"type": "boolean"},
                              "finding_class": {"enum": ["implementation", "authoritative-artifact", "governance", "coordination", "environment"]},
                              "attribution": {"enum": ["executor", "planner", "coordinator", "reviewer", "external"]},
                              "root_cause_id": {"type": "string"}, "evidence": {"type": "string"}, "disposition": {"type": "string"}}}},
  "unverified": {"type": "array", "items": {"type": "object", "required": ["item", "kind", "reason"], "additionalProperties": false,
                 "properties": {"item": {"type": "string"}, "kind": {"enum": ["cannot", "skipped", "deferred"]}, "reason": {"type": "string", "minLength": 1}}}},
  "note_responses": {"type": "array", "items": {"type": "object", "required": ["id", "value"], "additionalProperties": false,
                     "properties": {"id": {"type": "string"}, "value": {"enum": ["followed", "not_applicable", "found"]}, "text": {"type": "string"}}}},
  "out_of_scope": {"type": "array", "items": {"type": "string"}},
  "review_result": {"enum": ["APPROVE", "REQUEST_CHANGES"]},
  "core_pain_resolved": {"enum": ["yes", "no"]},
  "reason": {"type": "string"}}}
```

一則留言只有一個 `wf-return` 區塊。T2 以上：`unverified`、`note_responses`、`out_of_scope`（空陣列＝逐字「無」）必填；`role=reviewer` 另必填 `review_result`、`core_pain_resolved`、`findings`；`role=executor` 另必填 `mistakes`。以上皆由 `review` 印缺段。CLI 只驗 id 覆蓋、值在值域、text 非空，⛔ 不判內容。

## 3 · 裁定單（PM → 需求方；`brief --for closeout` 或人手組）

| 段 | 誰填 | 內容 |
|---|---|---|
| 留言時間序 | CLI | `wf-return` 留言的時間序、各輪退回理由與 findings |
| 現況 | CLI | merge SHA、CI 狀態、四停下條件前三項（blocking 未 resolved／CI 非綠／分支衝突） |
| 類別 | 人（PM） | 恰一個：升級／停止／撤銷／級別變更／結案確認／其他 |
| 各值證據 | 人（PM） | 四選一（換人／退回上一階段／停止／退回無效）各「若成立會是什麼證據」；只寫事實，⛔ 不含建議 |
| 復活條件、翻案把手 | 人（PM） | 停止類必填；翻案把手須可跑（`git revert <merge SHA>`），寫不出即逐字「無把手」＋原因 |
| 被繞過的要求 | 人（PM） | 級別下修類必填 |
| 裁定 | 需求方 | 一則 `wf:ruling` 留言，帶 `wf-ruling` 區塊 |

```json schema
{"$id": "wf-ruling", "type": "object", "additionalProperties": false, "required": ["kind", "reason"],
 "properties": {
  "kind": {"enum": ["block", "stop", "withdraw", "tier_change", "signoff", "other"]},
  "reason": {"type": "string", "minLength": 1},
  "waiting_on": {"type": "string"}, "unblock_condition": {"type": "string"},
  "revive_condition": {"type": "string"}, "reversal_handle": {"type": "string"}}}
```

依 kind 的必要鍵：block＝reason、waiting_on、unblock_condition（加 CLI 寫的 `blocked.from` 共四欄）；stop＝reason、revive_condition、reversal_handle；其餘只要 reason。CLI 只驗鍵存在與型別；缺＝印。PM 代貼裁定時首行 `代貼裁定・授權來源：<session 或留言 URL>`；代貼裁決時首行 `代貼裁決・來源：<模型名>@<工具名>・被審 SHA：<sha>`。
