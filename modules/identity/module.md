---
name: identity
when: 多實體共用同一 GitHub 帳號
non_scope: ⛔ 不寫代貼標記（住 core/naming.md §3）
last_confirmed: 2026-09-05
---

# 模組 identity

## 0 · 宣告區塊

唯一啟用條件＝`enable_when`（一個 predicate；事實來源＝`fact_source`）；未啟用時下列每一項都不存在。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "identity",
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
      "身分三格（GitHub 帳號／session ID／訊息定位）"
    ]
  },
  "project_inputs": [],
  "params": {}
}
```

## 1 · 條文

- 待第 4b 步回填（2026-09-05）；來源列＝00 §六；01#97；03#134；04#6。

## 2 · 注意事項

- 待第 4b 步回填（2026-09-05）；id 形狀 `F-identity-NN`。
