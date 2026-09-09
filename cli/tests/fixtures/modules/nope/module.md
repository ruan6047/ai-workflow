---
name: nope
when: 測試替身：宣告了註冊表沒有的計數與印項 id
non_scope: ⛔ 不是框架模組，⛔ 不進 modules/
last_confirmed: 2026-09-08
---

# 模組 nope（測試替身）

## 0 · 宣告區塊

```yaml wf-module
{
  "name": "nope",
  "enable_when": "測試指定",
  "enable_if": {"kind": "project_module_listed"},
  "fact_source": "modules.json",
  "adds": {
    "fields": [],
    "stages": [],
    "enums": {"states": []},
    "transitions": {"add": [], "remove": []},
    "flags": [],
    "counters": ["nope_count"],
    "move_prints": ["nope"],
    "notes": [],
    "handoff_sections": []
  },
  "project_inputs": [],
  "params": {}
}
```
