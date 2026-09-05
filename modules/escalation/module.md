---
name: escalation
when: 專案啟用升級梯：同一 iteration 反覆退回時
non_scope: ⛔ 不寫第 3 次退回的預設處置（住 roles/pm.md F-PM-01）
last_confirmed: 2026-09-05
---

# 模組 escalation

## 0 · 宣告區塊

唯一啟用條件＝`enable_when`（一個 predicate；事實來源＝`fact_source`）；未啟用時下列每一項都不存在。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "escalation",
  "enable_when": "專案 .wf/modules.json 列出",
  "fact_source": "modules.json",
  "adds": {
    "fields": [
      "escalation_count"
    ],
    "stages": [],
    "states": [
      "升級"
    ],
    "transitions": {
      "add": [
        {
          "from": "*/退回",
          "to": "same/升級",
          "condition": "同 iteration 第 N 次退回，N＝params.escalate_after"
        },
        {
          "from": "*/升級",
          "to": "same/進行中",
          "condition": "換人或換級再派；--ruling 缺即印"
        },
        {
          "from": "*/升級",
          "to": "結案/待確認",
          "condition": "需求方裁定收尾"
        }
      ],
      "remove": []
    },
    "flags": [],
    "notes": [],
    "handoff_sections": [
      "升級單（三次退回逐字理由、四選一各值證據）"
    ]
  },
  "project_inputs": [],
  "params": {
    "escalate_after": 3
  }
}
```

## 1 · 條文

- 待第 4b 步回填（2026-09-05）；來源列＝00 §六；05 空洞 7；01#5 93–95。

## 2 · 注意事項

- 待第 4b 步回填（2026-09-05）；id 形狀 `F-escalation-NN`。
