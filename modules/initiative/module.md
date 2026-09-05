---
name: initiative
when: 卡有父卡：子切片、基線遞變、父卡持 spec 基線
non_scope: ⛔ 不寫鏈深（住 core/verbs.md）
last_confirmed: 2026-09-05
---

# 模組 initiative

## 0 · 宣告區塊

唯一啟用條件＝`enable_when`（一個 predicate；事實來源＝`fact_source`）；未啟用時下列每一項都不存在。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "initiative",
  "enable_when": "卡面 parent 非空",
  "fact_source": "卡面 JSON",
  "adds": {
    "fields": [
      "parent_spec_version"
    ],
    "stages": [],
    "states": [],
    "transitions": {
      "add": [],
      "remove": []
    },
    "flags": [],
    "notes": [],
    "handoff_sections": [
      "spec 基線（父卡 spec_version 與本卡登記版本）"
    ]
  },
  "project_inputs": [],
  "params": {}
}
```

## 1 · 條文

- 待第 4b 步回填（2026-09-05）；來源列＝02#10；04#44 117–120。

## 2 · 注意事項

- 待第 4b 步回填（2026-09-05）；id 形狀 `F-initiative-NN`。
