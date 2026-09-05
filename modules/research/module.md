---
name: research
when: 卡的階段計畫含研究：量測、下結論、或判不可判定
non_scope: ⛔ 不寫統計紅線（住 modules/stat-redline）；⛔ 不寫規劃階段（住 stages/planning.md）
last_confirmed: 2026-09-05
---

# 模組 research

## 0 · 宣告區塊

唯一啟用條件＝`enable_when`（一個 predicate；事實來源＝`fact_source`）；未啟用時下列每一項都不存在。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "research",
  "enable_when": "卡面 stage_plan 含 研究",
  "fact_source": "卡面 JSON",
  "adds": {
    "fields": [],
    "stages": [
      "研究"
    ],
    "states": [
      "不可判定"
    ],
    "transitions": {
      "add": [
        {
          "from": "研究/待確認",
          "to": "研究/不可判定",
          "condition": "交回單 verdict＝不可判定"
        },
        {
          "from": "研究/不可判定",
          "to": "需求/待辦",
          "condition": "重述問題"
        },
        {
          "from": "研究/不可判定",
          "to": "結案/待確認",
          "condition": "以不可判定作結案報告"
        }
      ],
      "remove": []
    },
    "flags": [],
    "notes": [],
    "handoff_sections": [
      "量測紀錄（可重跑）",
      "結論"
    ]
  },
  "project_inputs": [],
  "params": {}
}
```

## 1 · 條文

- 待第 4b 步回填（2026-09-05）；來源列＝03#50–60。

## 2 · 注意事項

- 待第 4b 步回填（2026-09-05）；id 形狀 `F-research-NN`。
