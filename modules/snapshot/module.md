---
name: snapshot
when: 狀態面在 GitHub 上：每日離線稽核副本
non_scope: ⛔ 不寫 snapshot 動詞的語意（住 core/verbs.md）
last_confirmed: 2026-09-06
---

# 模組 snapshot

## 0 · 宣告區塊

啟用條件＝`enable_if`（CLI 判啟用的唯一依據；`enable_when` 是同義散文、只給人讀；事實來源＝`fact_source`）；未啟用時下列每一項都不存在，唯 `fields` 的結構合法性例外（`core/card-schema.md` §1 (b)）。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "snapshot",
  "enable_when": "專案 .wf/modules.json 列出",
  "enable_if": {"kind": "project_module_listed"},
  "fact_source": "modules.json",
  "adds": {
    "fields": [],
    "stages": [],
    "enums": {"states": []},
    "transitions": {
      "add": [],
      "remove": []
    },
    "flags": [],
    "notes": ["F-snapshot-01"],
    "handoff_sections": []
  },
  "project_inputs": [],
  "params": {
    "schedule": "daily",
    "branch": "snapshots"
  }
}
```

## 1 · 條文

- PM 每 `params.schedule`（種子 daily）跑一次 `snapshot`。
- 跑完把輸出 commit 到本 repo 的 `params.branch`（種子 `snapshots`）作離線稽核副本。
- 事後對帳與盤點分母以快照分支為準。
- 對狀態面只做唯讀存取；⛔ 不寫回。

## 2 · 注意事項

- F-snapshot-01：對帳⛔ 不以 `gh project item-list` 的即時輸出為準。
