---
name: return
when: 寫或讀交回單與 `wf-return` 區塊時（執行者交回、查核者貼裁決）
non_scope: ⛔ 不寫交接文件的共通規則（住 core/handoff.md）；⛔ 不寫怎麼判交回單對不對（住 roles/pm.md、roles/reviewer.md）；⛔ 不寫卡面欄（住 core/card-schema.md）
last_confirmed: 2026-09-07
---

# 交回單（執行者或查核者 → PM；`review --file`）

| 段 | 誰填 | 內容 |
|---|---|---|
| 卡與身分 | CLI | 同派工單；另列 `source_sha`、commit 清單（`git log`）、改動面（`git diff --stat` 每檔一列）、`finding_id` 由作者依 `core/naming.md` §4 填 |
| self_run | 人 | 實跑的指令、rc、原始輸出 |
| 逐條驗收 | 人 | 每條 `acceptance`：做法／證據／falsifier，⛔ 不合併 |
| 失誤登記 | 執行者 | 逐項：失誤／何時／影響／補救；無則逐字「無」 |
| findings | 查核者 | 九欄逐條（schema）；無則逐字「無」 |
| 模組段 | 人 | 已啟用模組的交回單段（schema `$defs/module_return_sections`）；鍵名為英文識別字，段名住 `label` |
| 未驗清單 | 人 | 每項 `{item, kind, reason}`；kind＝cannot／skipped／deferred；reason 非空 |
| 注意事項回應 | 人 | 對 `notes` 印出的每個 id 一條 `{id, value, text}`；value＝followed／not_applicable／found；後兩者 text 非空 |
| 射程外發現 | 人 | 逐項；無則「無」 |
| 裁決 | 查核者 | `review_result`、`core_pain_resolved`、一句話理由 |

必填性依級別：T0／T1 只要 `self_run` 與逐條驗收；T2 以上全段。缺段一律由 `review` 依卡面 `tier` 印，⛔ 不進 schema；schema 只管結構，`required` 只列 `review` 自己補的欄。`review` 先補 `card_id`／`iteration`／`role`／`source_sha`（`finding_id` 由作者依 `core/naming.md` §4 填，`review` ⛔ 不編、只印撞號），再把已啟用模組的 `$defs/module_return_sections/<模組名>` 併入 `properties`（型別唯一居所＝本檔，與 `core/card-schema.md` §1 合成同型），再驗 schema；模組段缺時依 `label` 印。

```json schema
{"$id": "wf-return", "type": "object", "additionalProperties": false,
 "required": ["card_id", "iteration", "role", "source_sha"],
 "properties": {
  "card_id": {"type": "string"}, "iteration": {"type": "integer"}, "role": {"enum": ["executor", "reviewer"]},
  "source_sha": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
  "self_run": {"type": "array", "items": {"type": "object", "required": ["command", "rc", "observed"], "additionalProperties": false,
               "properties": {"command": {"type": "string"}, "rc": {"type": "integer"}, "observed": {"type": "string"}}}},
  "acceptance": {"type": "array", "items": {"type": "object", "required": ["text", "method", "evidence", "falsifier"], "additionalProperties": false,
                 "properties": {"text": {"type": "string"}, "method": {"type": "string"}, "evidence": {"type": "string"}, "falsifier": {"type": "string"}}}},
  "mistakes": {"type": "array", "items": {"type": "object", "required": ["what", "when", "impact", "fix"], "additionalProperties": false,
               "properties": {"what": {"type": "string"}, "when": {"type": "string"}, "impact": {"type": "string"}, "fix": {"type": "string"}}}},
  "findings": {"type": "array", "items": {"type": "object", "additionalProperties": false,
               "required": ["finding_id", "severity", "blocking", "status", "finding_class", "attribution", "root_cause_id", "evidence", "disposition"],
               "properties": {"finding_id": {"type": "string"}, "severity": {"enum": ["critical", "major", "minor", "info"]}, "blocking": {"type": "boolean"}, "status": {"enum": ["open", "resolved", "withdrawn"]},
                              "finding_class": {"enum": ["implementation", "authoritative-artifact", "governance", "coordination", "environment"]},
                              "attribution": {"enum": ["executor", "planner", "coordinator", "reviewer", "external"]},
                              "root_cause_id": {"type": "string"}, "evidence": {"type": "string"}, "disposition": {"type": "string"}}}},
  "unverified": {"type": "array", "items": {"type": "object", "required": ["item", "kind", "reason"], "additionalProperties": false,
                 "properties": {"item": {"type": "string"}, "kind": {"enum": ["cannot", "skipped", "deferred"]}, "reason": {"type": "string"}}}},
  "note_responses": {"type": "array", "items": {"type": "object", "required": ["id", "value"], "additionalProperties": false,
                     "properties": {"id": {"type": "string"}, "value": {"enum": ["followed", "not_applicable", "found"]}, "text": {"type": "string"}}}},
  "out_of_scope": {"type": "array", "items": {"type": "string"}},
  "review_result": {"enum": ["APPROVE", "REQUEST_CHANGES"]},
  "core_pain_resolved": {"enum": ["yes", "no"]},
  "reason": {"type": "string"}},
 "$defs": {"module_return_sections": {
   "research": {"measurement": {"label": "量測紀錄（可重跑）", "type": "string"}, "conclusion": {"label": "結論", "type": "object", "required": ["verdict"], "additionalProperties": false, "properties": {"verdict": {"enum": ["可判定", "不可判定"]}, "text": {"type": "string"}}}},
   "stat-redline": {"redlines": {"label": "紅線區塊（本卡的窗口與門檻）", "type": "array", "items": {"type": "string"}},
                    "adversarial_tests": {"label": "對抗性反測表（≥3 角度，各寫支持／推翻／未能檢定）", "type": "array", "items": {"type": "object", "required": ["angle", "result"], "additionalProperties": false, "properties": {"angle": {"type": "string"}, "result": {"enum": ["支持", "推翻", "未能檢定", "不適用"]}, "text": {"type": "string"}}}}},
   "pitfalls-13": {"pitfall_families": {"label": "13 族踩坑清冊（每族恰一行，已檢查／不適用／發現）", "type": "string"}},
   "db-contract": {"db_contract": {"label": "DB 契約段（namespace、lock、備份、回滾、驗證命令）", "type": "string"}},
   "deploy": {"deploy_facts": {"label": "部署事實（環境／時間／SHA／驗證）", "type": "string"}},
   "maintenance": {"run_status": {"label": "運行狀態（活著的證據）", "type": "string"}}}}}
```

一則留言只有一個 `wf-return` 區塊。缺段（`review` 印，⛔ 不是 D3）：全級別＝`self_run`、`acceptance`；T2 以上另＝`unverified`、`note_responses`、`out_of_scope`（空陣列＝逐字「無」）；`role=reviewer` 另＝`review_result`、`core_pain_resolved`、`findings`；`role=executor` 另＝`mistakes`；已啟用模組的交回單段不分級別。CLI 只印 id 未覆蓋 `notes` 清單、`not_applicable`／`found` 而 text 空、`unverified.reason` 空、模組段內 `不適用`／`發現` 而 text 空、交回單欄位不一致（`review_result` 對 `findings`，PM 判），⛔ 不判內容。

跨 iteration 閉環：本卡已有前一則 `wf:verdict` 時，`wf-return` 逐條重列前輪 finding 的原 `finding_id` 與新 `status`；新 finding 由作者編新 id，⛔ 不重用既有 id。
