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
  "card_id": {"type": "string", "pattern": "^[A-Z]+-[0-9]{3,}(-FIX[0-9]+)?$"},
  "source_issue": {"type": "integer"},
  "feature": {"type": "string", "minLength": 1},
  "core_pain": {"type": "string", "minLength": 1},
  "non_scope": {"type": "array", "items": {"type": "string"}, "minItems": 1},
  "stage_plan": {"type": "array", "items": {"enum": ["需求", "研究", "規劃", "執行", "審核", "部署", "維護", "結案"]}, "uniqueItems": true},
  "acceptance": {"type": "array", "items": {"type": "string"}},
  "verification": {"type": "array", "items": {"type": "object", "required": ["item", "who"], "additionalProperties": false,
                    "properties": {"item": {"type": "string"}, "who": {"enum": ["executor", "reviewer", "requester", "ci"]}}}},
  "list_convergence": {"type": "array", "items": {"type": "integer"}},
  "service_goal": {"type": "string", "minLength": 1},
  "parent": {"type": ["string", "null"]},
  "blocked": {"type": ["object", "null"], "required": ["from", "ruling"], "additionalProperties": false,
              "properties": {"from": {"$ref": "#/$defs/nonterminal"}, "ruling": {"type": "string", "format": "uri"}}},
  "grilling": {"type": ["string", "null"], "format": "uri"},
  "tier": {"enum": ["T0", "T1", "T2", "T3", "T4"]},
  "tier_basis": {"type": "object", "required": ["sensitive", "recoverable", "blast"], "additionalProperties": false,
    "properties": {
      "sensitive": {"type": "array", "uniqueItems": true, "items": {"enum": ["public_contract", "security", "payment", "data_write", "migration", "production", "rules", "statistics"]}},
      "recoverable": {"enum": ["reversible", "rollback_only", "irreversible"]},
      "blast": {"enum": ["file", "module", "repo", "cross_repo"]}}},
  "exec_capability": {"$ref": "#/$defs/capability"},
  "review_capability": {"$ref": "#/$defs/capability"},
  "db_scope": {"enum": ["none", "read", "write", "schema", "data-migration"]},
  "resources": {"type": "array", "items": {"type": "string"}},
  "when": {"type": "string", "minLength": 1},
  "spec_version": {"type": "integer", "minimum": 1},
  "owner": {"type": ["object", "null"], "required": ["role", "actor"], "additionalProperties": false,
            "properties": {"role": {"enum": ["requester", "pm", "executor", "reviewer"]}, "actor": {"type": "string", "minLength": 1}}},
  "branch": {"type": ["string", "null"]},
  "source_sha": {"type": ["string", "null"], "pattern": "^[0-9a-f]{40}$"},
  "iteration": {"type": "integer", "minimum": 0},
  "notes": {"type": "array", "items": {"type": "object", "required": ["id", "text", "origin"], "additionalProperties": false,
            "properties": {"id": {"type": "string", "pattern": "^T-(需求|研究|規劃|執行|審核|部署|維護|結案)-[0-9]{2}$"}, "text": {"type": "string", "minLength": 1}, "origin": {"type": "string", "format": "uri"}}}}
 },
 "$defs": {"capability": {"type": "object", "required": ["level", "reason"], "additionalProperties": false,
           "properties": {"level": {"enum": ["經濟型", "主力型", "高階型"]}, "reason": {"type": "string", "minLength": 1}}},
          "nonterminal": {"enum": ["待辦", "進行中", "待確認", "退回"]}}}
```

合成（D3 用合成後的 schema 驗）：CLI 讀本檔 schema 後，把已啟用模組宣告的 `adds.states` 併入 `$defs/nonterminal` 的 enum 再驗；未啟用模組的值因此仍拒。schema 以外的結構約束（D3，CLI 驗）：`stage_plan` 為 `core/state-machine.md` 階段序的子序列且含需求／執行／審核／結案；`card_id`／`source_issue` 建卡後不可改；`parent` 指到板上存在的卡（D4）。

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
| notes | 任何角色經 `edit --set notes+=`，來源＝`wf:note` 留言 | — | notes、brief |

規格欄＝acceptance／verification／non_scope／resources；`edit` 改任一欄 ⇒ `spec_version` +1（C11）。

## 3 · 清單項 `wf-intake`

```json schema
{"$id": "wf-intake", "type": "object", "additionalProperties": false,
 "required": ["source", "observation", "dedupe", "repo"],
 "properties": {
  "source": {"type": "string", "minLength": 1},
  "observation": {"type": "string", "minLength": 1},
  "dedupe": {"type": "object", "required": ["keywords", "hits"], "additionalProperties": false,
             "properties": {"keywords": {"type": "array", "items": {"type": "string"}, "minItems": 1}, "hits": {"type": "array", "items": {"type": "integer"}}}},
  "repo": {"type": "string", "minLength": 1}}}
```

`open` 只讀此區塊；缺欄印缺欄清單，處置由收件方判。

## 4 · `wf-note`

```json schema
{"$id": "wf-note", "type": "object", "additionalProperties": false, "required": ["text", "origin"],
 "properties": {"text": {"type": "string", "minLength": 1}, "origin": {"type": "string", "format": "uri"}}}
```

## 5 · 投影欄

Project 只放五欄，全由 CLI 回寫：階段（單選 8 值）、狀態（單選：核心 5＋阻塞＋停止＋已啟用模組值）、級別（單選 5 值）、owner（TEXT，`role@actor`）、卡ID（TEXT）。TEXT 欄上限 1024 bytes UTF-8；超過即 D3 拒。寫入順序住 `core/verbs.md` §寫入契約。

## 6 · 版本

- `schema_version` 升版觸發＝任一鍵新增、刪除、改型別或改值域；只加值域內的值不升版。
- 遷移路徑＝任一寫入動詞讀到舊版卡時先升版再寫，寫後回讀；⛔ 不就地改舊卡的其他欄、⛔ 不加旗標。2026-09-05 只有版本 1。
