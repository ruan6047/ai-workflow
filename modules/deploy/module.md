---
name: deploy
when: 卡的階段計畫含部署
non_scope: ⛔ 不寫維護（住 modules/maintenance）
last_confirmed: 2026-09-05
---

# 模組 deploy

## 0 · 宣告區塊

唯一啟用條件＝`enable_when`（一個 predicate；事實來源＝`fact_source`）；未啟用時下列每一項都不存在。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "deploy",
  "enable_when": "卡面 stage_plan 含 部署",
  "fact_source": "卡面 JSON",
  "adds": {
    "fields": [],
    "stages": [
      "部署"
    ],
    "states": [],
    "transitions": {
      "add": [],
      "remove": []
    },
    "flags": [],
    "notes": [],
    "handoff_sections": [
      "部署事實（環境／時間／SHA／驗證）"
    ]
  },
  "project_inputs": [
    ".wf/contracts/DEPLOYMENT.md"
  ],
  "params": {}
}
```

## 1 · 條文

- 待第 4b 步回填（2026-09-05）；來源列＝00 §六；01#60–62；03#142–143。

## 2 · 注意事項

- 待第 4b 步回填（2026-09-05）；id 形狀 `F-deploy-NN`。
