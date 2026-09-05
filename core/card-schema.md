---
name: card-schema
when: 寫或讀卡面 JSON、清單項 JSON、`wf:note` JSON、Project 投影欄時讀
non_scope: ⛔ 不寫欄位該填什麼內容（住 stages/requirement.md、planning.md）；⛔ 不寫交回單與裁定（住 core/handoff.md）
last_confirmed: 2026-09-05
---

# 卡面 schema

卡面＝issue body 的一個 `json wf-card` 區塊＋人讀散文段。CLI 只讀寫 JSON；未定義鍵 ⇒ 整卡拒（D3）。schema 的唯一居所＝本檔的 `json schema` 區塊，CLI 執行期直接讀。

## 1 · `wf-card`

```json schema
{"$id": "wf-card", "type": "object", "additionalProperties": false,
 "required": ["schema_version", "card_id", "source_issue", "feature", "core_pain", "non_scope", "stage_plan",
              "list_convergence", "service_goal", "tier", "tier_basis", "exec_capability", "review_capability",
              "db_scope", "resources", "when", "spec_version", "iteration", "acceptance", "verification",
              "parent", "blocked", "grilling", "owner", "branch", "source_sha", "notes"],
 "properties": {
  "schema_version": {"type": "integer", "const": 1},
  "card_id": {"type": "string", "pattern": "^[A-Z]+-[0-9]{3,}(-FIX[1-9][0-9]*)?$"},
  "source_issue": {"type": "integer"},
  "feature": {"type": "string"},
  "core_pain": {"type": "string"},
  "non_scope": {"type": "array", "items": {"type": "string"}},
  "stage_plan": {"type": "array", "items": {"enum": ["需求", "研究", "規劃", "執行", "審核", "部署", "維護", "結案"]}, "uniqueItems": true},
  "acceptance": {"type": "array", "items": {"type": "string"}},
  "verification": {"type": "array", "items": {"type": "object", "required": ["item", "who"], "additionalProperties": false,
                    "properties": {"item": {"type": "string"}, "who": {"type": "string"}}}},
  "list_convergence": {"type": "array", "items": {"type": "integer"}},
  "service_goal": {"type": "string"},
  "parent": {"type": ["string", "null"]},
  "blocked": {"type": ["object", "null"], "required": ["from", "ruling"], "additionalProperties": false,
              "properties": {"from": {"$ref": "#/$defs/nonterminal"}, "ruling": {"type": "string", "format": "uri"}}},
  "grilling": {"type": ["string", "null"], "format": "uri"},
  "tier": {"enum": ["T0", "T1", "T2", "T3", "T4", null]},
  "tier_basis": {"type": ["object", "null"], "required": ["sensitive", "recoverable", "blast"], "additionalProperties": false,
    "properties": {
      "sensitive": {"type": "array", "uniqueItems": true, "items": {"enum": ["public_contract", "security", "payment", "data_write", "migration", "production", "rules", "statistics"]}},
      "recoverable": {"enum": ["reversible", "rollback_only", "irreversible"]},
      "blast": {"enum": ["file", "module", "repo", "cross_repo"]}}},
  "exec_capability": {"$ref": "#/$defs/capability"},
  "review_capability": {"$ref": "#/$defs/capability"},
  "db_scope": {"enum": ["none", "read", "write", "schema", "data-migration", null]},
  "resources": {"type": "array", "items": {"type": "string"}},
  "when": {"type": "string"},
  "spec_version": {"type": "integer", "minimum": 1},
  "owner": {"type": ["object", "null"], "required": ["role", "actor"], "additionalProperties": false,
            "properties": {"role": {"enum": ["requester", "pm", "executor", "reviewer"]}, "actor": {"type": "string"}}},
  "branch": {"type": ["string", "null"]},
  "source_sha": {"type": ["string", "null"], "pattern": "^[0-9a-f]{40}$"},
  "iteration": {"type": "integer", "minimum": 0},
  "notes": {"type": "array", "items": {"type": "object", "required": ["id", "text", "origin"], "additionalProperties": false,
            "properties": {"id": {"type": "string", "pattern": "^T-(需求|研究|規劃|執行|審核|部署|維護|結案)-[0-9]{2}$"}, "text": {"type": "string"}, "origin": {"type": "string", "format": "uri"}}}}
 },
 "$defs": {"capability": {"type": ["object", "null"], "required": ["level", "reason"], "additionalProperties": false,
           "properties": {"level": {"enum": ["經濟型", "主力型", "高階型"]}, "reason": {"type": "string"}}},
          "nonterminal": {"enum": ["待辦", "進行中", "待確認", "退回"]},
          "module_fields": {
            "resource-lock": {"worktree": {"type": ["string", "null"]}, "lease_expires_at": {"type": ["string", "null"], "format": "date-time"}},
            "escalation": {"escalation_count": {"type": "integer", "minimum": 0}},
            "initiative": {"parent_spec_version": {"type": ["integer", "null"], "minimum": 1}},
            "db-contract": {"db_namespace": {"type": ["string", "null"]}, "migration_phase": {"enum": ["expand", "migrate", "contract", null]}}}}}
```

合成（D3 用合成後的 schema 驗）：CLI 讀本檔 schema 後，(a) 把已啟用模組宣告的 `adds.states` 併入 `$defs/nonterminal` 的 enum；(b) 把 `$defs/module_fields/<模組名>` 併入 `wf-card.properties`（模組 `adds.fields` 的型別唯一居所＝本檔）；然後再驗。schema 只管結構；完整性（欄位有沒有填）由 `open`／`move` 印，⛔ 不是 D3。`open` 寫入的初值：CLI 欄填值、`spec_version`=1、`iteration`=0；字串欄＝空字串、陣列欄＝空陣列、enum 與物件欄（`tier`、`tier_basis`、`exec_capability`、`review_capability`、`db_scope`）與 `parent`／`blocked`／`grilling`／`owner`／`branch`／`source_sha`＝null。缺陷卡用同一 `wf-card` 形狀，⛔ 無專屬卡種。schema 以外的結構約束（D3，CLI 驗）：`stage_plan` 非空時須為 `core/state-machine.md` 階段序的子序列且含需求／執行／審核／結案（空＝未填，印）；`card_id`／`source_issue` 建卡後不可改；`parent` 指到板上存在的卡（D4）。

## 2 · 誰填、何時必填、誰讀

| 欄 | 誰填 | 必填時點（`open`／`move` 印缺欄） | 誰讀 |
|---|---|---|---|
| schema_version、card_id、source_issue、spec_version、iteration | CLI | 建卡 | CLI |
| core_pain | CLI 從清單項 `wf-intake.observation` 逐字帶入 | 建卡 | 所有交接文件 |
| feature、non_scope、stage_plan、list_convergence、tier、tier_basis、exec_capability、review_capability、db_scope、resources、when | PM | 建卡 | brief、tiers、模組 |
| service_goal | 需求方 | 建卡 | R1 |
| acceptance（≥1）、verification（≥1） | PM | 離開規劃前 | brief、R3 |
| grilling | PM（`edit`） | T4 離開規劃前 | brief、裁定單 |
| parent | PM（`open --parent`／`edit`） | 有父卡時 | 鏈深（印）、initiative |
| owner、branch、source_sha、blocked | CLI（`move`） | — | brief、Project、D4 |
| notes | 任何角色經 `edit --set notes+=`，來源＝`wf:note` 留言；`last_cited` 不存卡面，由 `snapshot` 推得 | — | notes、brief |

規格欄＝acceptance／verification／non_scope／resources；`edit` 改任一欄 ⇒ `spec_version` +1（C11）。

## 3 · 清單項 `wf-intake`

```json schema
{"$id": "wf-intake", "type": "object", "additionalProperties": false,
 "required": ["source", "observation", "dedupe", "repo"],
 "properties": {
  "source": {"type": "string"},
  "observation": {"type": "string"},
  "dedupe": {"type": "object", "required": ["keywords", "hits"], "additionalProperties": false,
             "properties": {"keywords": {"type": "array", "items": {"type": "string"}}, "hits": {"type": "array", "items": {"type": "integer"}}}},
  "repo": {"type": "string"}}}
```

`open` 只讀此區塊；schema 只管四鍵的結構；空值＝未填，`open` 印缺欄清單，處置由收件方判。

## 4 · `wf-note`

```json schema
{"$id": "wf-note", "type": "object", "additionalProperties": false, "required": ["text", "origin"],
 "properties": {"text": {"type": "string", "minLength": 1}, "origin": {"type": "string", "format": "uri"}}}
```

## 5 · 投影欄

Project 只放五欄，全由 CLI 回寫：階段（單選 8 值）、狀態（單選：核心 5＋阻塞＋停止＋已啟用模組值）、級別（單選 5 值）、owner（TEXT，`role:actor`，需求方 2026-09-05 裁定）、卡ID（TEXT）。`max_bytes`：owner 1024、卡ID 1024（UTF-8，2026-09-04 種子）；超過＝寫壞資料，D3（`core/verbs.md` §2）。null 的 enum 欄投影＝單選欄清空。寫入順序住 `core/verbs.md` §寫入契約。

## 6 · schema_version

- `schema_version` 升版觸發＝任一鍵新增、刪除、改型別或改值域；只加值域內的值不升版。
- 遷移路徑＝任一寫入動詞讀到舊版卡時先升版再寫，寫後回讀；⛔ 不就地改舊卡的其他欄、⛔ 不加旗標。2026-09-05 只有 `schema_version` 1。
