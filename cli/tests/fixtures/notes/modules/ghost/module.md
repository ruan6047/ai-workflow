---
name: ghost
when: adds.notes 宣告了 §2 沒有的 id 的樣本
non_scope: ⛔ 不是真模組
last_confirmed: 2026-09-08
---

# 模組 ghost（fixture）

## 0 · 宣告區塊

```yaml wf-module
{
  "name": "ghost",
  "enable_when": "專案 .wf/modules.json 列出",
  "enable_if": {"kind": "project_module_listed"},
  "fact_source": "modules.json",
  "adds": {"fields": [], "stages": [], "enums": {"states": []},
           "transitions": {"add": [], "remove": []},
           "flags": [], "notes": ["F-ghost-01", "F-ghost-02"], "handoff_sections": []},
  "project_inputs": [],
  "params": {}
}
```

## 2 · 注意事項

- F-ghost-01：只有這條真的在 §2。
