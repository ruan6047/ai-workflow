---
name: deploy
when: 卡的階段計畫含部署
non_scope: ⛔ 不寫維護（住 modules/maintenance）
last_confirmed: 2026-09-05
---

# 模組 deploy

## 0 · 宣告區塊

啟用條件＝`enable_if`（CLI 判啟用的唯一依據；`enable_when` 是同義散文、只給人讀；事實來源＝`fact_source`）；未啟用時下列每一項都不存在，唯 `fields` 的結構合法性例外（`core/card-schema.md` §1 (b)，需求方 2026-09-07 甲案 B06）。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "deploy",
  "enable_when": "卡面 stage_plan 含 部署",
  "enable_if": {"kind": "stage_plan_has", "stage": "部署"},
  "fact_source": "卡面 JSON",
  "adds": {
    "fields": [],
    "stages": [
      "部署"
    ],
    "enums": {"states": []},
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

- 待實例（2026-09-05 起）：第一張實例卡出現時回填；來源列＝00 §六；01#60–62；03#142–143。

## 2 · 注意事項

- 待實例（2026-09-05 起）：第一張實例卡出現時回填；id 形狀 `F-deploy-NN`。
