---
name: snapshot
when: 狀態面在 GitHub 上：每日離線稽核副本
non_scope: ⛔ 不寫 snapshot 動詞的語意（住 core/verbs.md）
last_confirmed: 2026-09-05
---

# 模組 snapshot

## 0 · 宣告區塊

唯一啟用條件＝`enable_when`（一個 predicate；事實來源＝`fact_source`）；未啟用時下列每一項都不存在。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "snapshot",
  "enable_when": "專案 .wf/modules.json 列出",
  "fact_source": "modules.json",
  "adds": {
    "fields": [],
    "stages": [],
    "states": [],
    "transitions": {
      "add": [],
      "remove": []
    },
    "flags": [],
    "notes": [],
    "handoff_sections": []
  },
  "project_inputs": [],
  "params": {
    "schedule": "daily"
  }
}
```

## 1 · 條文

- 待第 4b 步回填（2026-09-05）；來源列＝00 §六；02#53；04#122。

## 2 · 注意事項

- 待第 4b 步回填（2026-09-05）；id 形狀 `F-snapshot-NN`。
