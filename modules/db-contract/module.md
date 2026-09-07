---
name: db-contract
when: 專案有資料庫：db_scope 為 write／schema／data-migration 的卡
non_scope: ⛔ 不寫紅線級別（住 core/tiers.md §3）
last_confirmed: 2026-09-06
---

# 模組 db-contract

## 0 · 宣告區塊

啟用條件＝`enable_if`（CLI 判啟用的唯一依據；`enable_when` 是同義散文、只給人讀；事實來源＝`fact_source`）；未啟用時下列每一項都不存在，唯 `fields` 的結構合法性例外（`core/card-schema.md` §1 (b)，需求方 2026-09-07 裁定）。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "db-contract",
  "enable_when": "專案 .wf/modules.json 列出",
  "enable_if": {"kind": "project_module_listed"},
  "fact_source": "modules.json",
  "adds": {
    "fields": [
      "db_namespace",
      "migration_phase"
    ],
    "stages": [],
    "enums": {"states": []},
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

- 專案以範本建立 `.wf/contracts/DATABASE_CONTRACT.md`（§0 `project_inputs`）：引擎、migration 工具、runner、環境 namespace、lock、備份、回滾與驗證命令、哪些表要宣告；⛔ 不填 secret、連線字串與 production 憑證。
- `db_scope` 為 write／schema／data-migration 的卡填 `db_namespace`（§0 欄）；`db_scope` 的值域與必填住 `core/card-schema.md`。
- `db_scope ∈ {schema, data-migration}` 時另填 `migration_phase`（§0 欄）與卡面 `resources` 欄的 `db:` 資源（環境寫在 `<env>`）；級別依 `core/tiers.md` §3。
- `db:` 資源文法＝`db:<env>:schema`／`db:<env>:table:<name>`，`schema`、`table` 是字面關鍵字，只換 `<env>` 與 `<name>`；交集比對住 `modules/resource-lock`。
- `<env>` 只用契約檔枚舉的環境正名（種子 local／test／staging／production），契約檔附別名表；卡面與資源宣告⛔ 不用別名。
- 寫入或測試 DB 的卡用以卡ID 隔離的 namespace（DB、container、cache、queue、port 同理）。
- 共用可寫的 dev／test DB 在契約檔列 owner、lock 與清理方式。
- 同一 `<env, schema>` 最多一個 migration writer。
- 同表的資料 migration 亦鎖，同時只有一張卡寫。
- schema 卡依契約檔 migration lane 的順序 merge；⛔ 不平行產生互相依賴的 migration。
- schema 演進採 expand → migrate → contract，`migration_phase` 記本卡所在段。
- 無法回滾的 DDL、刪欄／表與大量轉換各自獨立一張卡。
- 資料 migration 寫成可重跑、可續跑、受批次限制。
- production 寫入憑證只給受保護的 CI／CD runner；runner 在 main 的 source SHA 取得 lane lock 後才跑 migration，並回報 migration ID、時間、結果與證據。
- 交回單的 DB 契約段列 rehearsal、復原方案、對帳與 smoke test 的指令與結果。
- 無法回滾的 DB 操作執行前取得需求方一則 `wf:ruling`（kind=other，reason 寫操作、執行者與方式）；⛔ 不以 T4 sign-off 代替。

## 2 · 注意事項

- F-db-contract-01：宣告整個 schema ⛔ 不會擋住只宣告個別表的卡；判定語意住 `modules/resource-lock`。
- F-db-contract-02：`db_scope` 的 `schema` 值與資源 token 的 `schema` 關鍵字是兩回事；⛔ 不把關鍵字換成 schema 名。
- F-db-contract-03：PM 派工前確認 `.wf/contracts/DATABASE_CONTRACT.md` 存在；不存在時寫進派工單未驗項，⛔ 不擋。
