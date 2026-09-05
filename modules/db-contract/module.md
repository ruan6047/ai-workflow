---
name: db-contract
when: 專案有資料庫：db_scope 為 write／schema／data-migration 的卡
non_scope: ⛔ 不寫紅線級別（住 core/tiers.md §3）
last_confirmed: 2026-09-05
---

# 模組 db-contract

## 0 · 宣告區塊

唯一啟用條件＝`enable_when`（一個 predicate；事實來源＝`fact_source`）；未啟用時下列每一項都不存在。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "db-contract",
  "enable_when": "專案 .wf/modules.json 列出",
  "fact_source": "modules.json",
  "adds": {
    "fields": [
      "db_namespace",
      "migration_phase"
    ],
    "stages": [],
    "states": [],
    "transitions": {
      "add": [],
      "remove": []
    },
    "flags": [],
    "notes": [],
    "handoff_sections": [
      "DB 契約段（namespace、lock、備份、回滾、驗證命令）"
    ]
  },
  "project_inputs": [
    ".wf/contracts/DATABASE_CONTRACT.md"
  ],
  "params": {}
}
```

## 1 · 條文

- 待第 4b 步回填（2026-09-05）；來源列＝02#45–50；04#129–132。

## 2 · 注意事項

- 待第 4b 步回填（2026-09-05）；id 形狀 `F-db-contract-NN`。
