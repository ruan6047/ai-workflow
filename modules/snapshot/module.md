---
name: snapshot
when: 狀態面在 GitHub 上：每日離線稽核副本
non_scope: ⛔ 不寫 snapshot 動詞的語意（住 core/verbs.md）
last_confirmed: 2026-09-06
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
    "notes": ["F-snapshot-01", "F-snapshot-02"],
    "handoff_sections": []
  },
  "project_inputs": [],
  "params": {
    "schedule": "daily"
  }
}
```

## 1 · 條文

- `snapshot` 依 `params.schedule`（種子 daily）由排程或 PM 手動跑，輸出本機 JSON＋Markdown（`core/verbs.md`），commit 到專案層指定的快照分支作離線稽核副本。
- 事後對帳、盤點分母與 `last_cited` 以快照分支為準；Issue timeline ⛔ 不當嚴格不可覆寫的 store。
- 快照只讀狀態面；⛔ 不寫回、⛔ 不改卡面。

## 2 · 注意事項

- F-snapshot-01：對帳⛔ 不以 `gh project item-list` 的即時輸出為準（自訂欄位可回空）。
- F-snapshot-02：快照 commit 訊息帶時間戳與卡數；⛔ 不手改快照檔。

→ [archive/rules-2026-09/templates/control-plane-contract.md](../../archive/rules-2026-09/templates/control-plane-contract.md)、[archive/rules-2026-09/AI_WORKFLOW.md](../../archive/rules-2026-09/AI_WORKFLOW.md)
