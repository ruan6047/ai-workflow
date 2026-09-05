---
name: maintenance
when: 卡的階段計畫含維護：交付物是排程、爬蟲、告警等外部觸發
non_scope: ⛔ 不寫部署（住 modules/deploy）
last_confirmed: 2026-09-05
---

# 模組 maintenance

## 0 · 宣告區塊

唯一啟用條件＝`enable_when`（一個 predicate；事實來源＝`fact_source`）；未啟用時下列每一項都不存在。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "maintenance",
  "enable_when": "卡面 stage_plan 含 維護",
  "fact_source": "卡面 JSON",
  "adds": {
    "fields": [],
    "stages": [
      "維護"
    ],
    "states": [
      "運行中"
    ],
    "transitions": {
      "add": [
        {
          "from": "維護/待辦",
          "to": "維護/運行中",
          "condition": "上線"
        },
        {
          "from": "維護/運行中",
          "to": "維護/進行中",
          "condition": "事件處理"
        },
        {
          "from": "維護/運行中",
          "to": "結案/待確認",
          "condition": "結束維護"
        }
      ],
      "remove": []
    },
    "flags": [],
    "notes": [],
    "handoff_sections": [
      "運行狀態（活著的證據）"
    ]
  },
  "project_inputs": [],
  "params": {}
}
```

## 1 · 條文

- 待第 4b 步回填（2026-09-05）；來源列＝00 §六；01#45 49 73；03#144。

## 2 · 注意事項

- 待第 4b 步回填（2026-09-05）；id 形狀 `F-maintenance-NN`。
