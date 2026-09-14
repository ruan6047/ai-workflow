---
name: scoped
when: adds.notes 帶 roles 維度的樣本：缺席＝全角色、列名者只給該角色
non_scope: ⛔ 不是真模組
last_confirmed: 2026-09-08
---

# 模組 scoped（fixture）

## 0 · 宣告區塊

```yaml wf-module
{
  "name": "scoped",
  "enable_when": "專案 .wf/modules.json 列出",
  "enable_if": {"kind": "project_module_listed"},
  "fact_source": "modules.json",
  "adds": {"fields": [], "stages": [], "enums": {"states": []},
           "transitions": {"add": [], "remove": []},
           "flags": [],
           "notes": [{"id": "F-scoped-01"},
                     {"id": "F-scoped-02", "roles": ["reviewer"]},
                     {"id": "F-scoped-03", "roles": ["executor", "pm"]}],
           "handoff_sections": []},
  "project_inputs": [],
  "params": {}
}
```

## 2 · 注意事項

- F-scoped-01：roles 缺席，全角色都看得到。
- F-scoped-02：只給 reviewer。
- F-scoped-03：只給 executor 與 pm。
