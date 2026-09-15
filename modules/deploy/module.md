---
name: deploy
when: 卡的階段計畫含部署
non_scope: ⛔ 不寫維護（住 modules/maintenance）
last_confirmed: 2026-09-05
---

# 模組 deploy

## 0 · 宣告區塊

啟用真相與自動能力的規則住 `core/modules.md`：`scope` 決定啟用（`enable_when` 是同義散文、只給人讀；事實來源＝`fact_source`），`maturity` 決定自動能力，封閉鍵集合與值域皆在該檔；未啟用或非 `ready` 時下列每一項都不存在，唯 `fields` 的結構合法性例外（`core/card-schema.md` §1 (b)）。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "deploy",
  "enable_when": "卡面 stage_plan 含 部署",
  "enable_if": {"kind": "stage_plan_has", "stage": "部署"},
  "fact_source": "卡面 JSON",
  "scope": "card",
  "maturity": "unavailable",
  "adds": {
    "fields": [],
    "stages": [],
    "enums": {"states": []},
    "transitions": {
      "add": [],
      "remove": []
    },
    "flags": [],
    "notes": [],
    "handoff_sections": []
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
