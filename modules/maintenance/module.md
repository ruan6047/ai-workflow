---
name: maintenance
when: 卡的階段計畫含維護：交付物是排程、爬蟲、告警等外部觸發
non_scope: ⛔ 不寫部署（住 modules/deploy）
last_confirmed: 2026-09-05
---

# 模組 maintenance

## 0 · 宣告區塊

啟用真相與自動能力的規則住 `core/modules.md`：`scope` 決定啟用（`enable_when` 是同義散文、只給人讀；事實來源＝`fact_source`），`maturity` 決定自動能力，封閉鍵集合與值域皆在該檔；未啟用時下列每一項都不存在，唯 `fields` 的結構合法性例外（`core/card-schema.md` §1 (b)）；已啟用但非 `ready` 時只有 `core/modules.md` §3 的自動能力七項不生效，`adds.notes` ⛔ 不在七項內、§2 條文照常進 notes 合成（`core/verbs.md` §3 ④）。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "maintenance",
  "enable_when": "卡面 stage_plan 含 維護",
  "enable_if": {"kind": "stage_plan_has", "stage": "維護"},
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
  "project_inputs": [],
  "params": {}
}
```

## 1 · 條文

- 待實例（2026-09-05 起）：第一張實例卡出現時回填；來源列＝00 §六；01#45 49 73；03#144。

## 2 · 注意事項

- 待實例（2026-09-05 起）：第一張實例卡出現時回填；id 形狀 `F-maintenance-NN`。
