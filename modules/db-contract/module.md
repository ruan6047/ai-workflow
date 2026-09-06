---
name: db-contract
when: 專案有資料庫：db_scope 為 write／schema／data-migration 的卡
non_scope: ⛔ 不寫紅線級別（住 core/tiers.md §3）
last_confirmed: 2026-09-06
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
    "notes": ["F-db-contract-01", "F-db-contract-02", "F-db-contract-03"],
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

- 專案以範本建立 `.wf/contracts/DATABASE_CONTRACT.md`（§0 `project_inputs`）：引擎、migration 工具、runner、環境 namespace、lock、備份、回滾與驗證命令、哪些表要宣告；⛔ 不填 secret 與連線字串。
- 碰 DB 的卡填 `db_scope`（核心欄）與 `db_namespace`（§0 欄）。
- `db_scope ∈ {schema, data-migration}` 時另填 `migration_phase`（§0 欄）、環境與 `db:` 資源；級別依 `core/tiers.md` §3。
- `db:` 資源文法＝`db:<env>:schema`／`db:<env>:table:<name>`，`schema`、`table` 是字面關鍵字，只換 `<env>` 與 `<name>`；交集比對住 `modules/resource-lock`。
- 寫入或測試 DB 的卡用以卡ID 隔離的 namespace（DB、container、cache、queue、port 同理）；共用可寫 dev／test DB 須有 owner、lock 與清理方式。
- 同一 `<env, schema>` 最多一個 migration writer；同表資料 migration 亦鎖；schema 卡依序 merge，⛔ 不平行產生互相依賴的 migration。
- schema 演進採 expand → migrate → contract，`migration_phase` 記本卡所在段。
- 無法回滾的 DDL、刪欄／表與大量轉換各自獨立一張卡。
- 資料 migration 寫成可重跑、可續跑、受批次限制。
- 交回單的 DB 契約段列 rehearsal、復原方案、對帳與 smoke test 的指令與結果。
- 無法回滾的 DB 操作執行前取得需求方一則 `wf:ruling`（kind=other，reason 寫操作、執行者與方式）；⛔ 不以 T4 sign-off 代替。

## 2 · 注意事項

- F-db-contract-01：`db:<env>:schema` 不支配 `db:<env>:table:<name>`；要互斥就宣告同一字串。
- F-db-contract-02：`db_scope` 的 `schema` 值與資源 token 的 `schema` 關鍵字是兩回事；⛔ 不把關鍵字換成 schema 名。
- F-db-contract-03：已啟用而 `.wf/contracts/DATABASE_CONTRACT.md` 不存在時 `notes` 印資料完整性提示；⛔ 不擋。

→ [archive/rules-2026-09/templates/database-contract.md](../../archive/rules-2026-09/templates/database-contract.md)、[archive/rules-2026-09/AI_WORKFLOW.md](../../archive/rules-2026-09/AI_WORKFLOW.md)
