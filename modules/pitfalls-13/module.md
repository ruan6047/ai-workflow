---
name: pitfalls-13
when: 專案啟用 13 族踩坑清冊
non_scope: ⛔ 不寫核心注意事項（住 core/verbs.md §3）
last_confirmed: 2026-09-05
---

# 模組 pitfalls-13

## 0 · 宣告區塊

唯一啟用條件＝`enable_when`（一個 predicate；事實來源＝`fact_source`）；未啟用時下列每一項都不存在。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "pitfalls-13",
  "enable_when": "專案 .wf/modules.json 列出",
  "fact_source": "modules.json",
  "adds": {
    "fields": [],
    "stages": [],
    "states": [],
    "transitions": {
      "add": [],
      "remove": []
    },
    "flags": [],
    "notes": [],
    "handoff_sections": [
      "13 族踩坑清冊（每族恰一行，已檢查／不適用／發現）"
    ]
  },
  "project_inputs": [],
  "params": {}
}
```

## 1 · 條文

- 待第 4b 步回填（2026-09-05）；來源列＝00 §六；02#100–104；03#138；04#17。

## 2 · 注意事項

- 待第 4b 步回填（2026-09-05）；id 形狀 `F-pitfalls-13-NN`。
