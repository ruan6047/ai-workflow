---
name: demo
when: 合成順序樣本的假模組
non_scope: ⛔ 不是真模組
last_confirmed: 2026-09-08
---

# 模組 demo（fixture）

## 0 · 宣告區塊

```yaml wf-module
{
  "name": "demo",
  "enable_when": "專案 .wf/modules.json 列出",
  "enable_if": {"kind": "project_module_listed"},
  "fact_source": "modules.json",
  "adds": {"fields": [], "stages": [], "enums": {"states": []},
           "transitions": {"add": [], "remove": []},
           "flags": [], "notes": ["F-demo-01"], "handoff_sections": []},
  "project_inputs": [],
  "params": {}
}
```

## 2 · 注意事項

- F-demo-01：模組條目。
