# Database Contract — <專案名>

> 本檔是本專案資料庫操作的事實來源；通用不變量見 canonical `AI_WORKFLOW.md` §4.2。不得填入 secret、連線字串或 production 憑證。

## 1. 技術與責任邊界

| 項目 | 專案定義 |
|---|---|
| DB 引擎／版本 | <例如 PostgreSQL 16> |
| 存取層／migration 工具 | <例如 EF Core / Prisma / Flyway> |
| Migration runner | <受保護 CI workflow／job> |
| Control-plane adapter | <Coordinator／workflow；claim 與資源鎖位置> |
| 正式 DB 寫入者 | <只有 runner identity> |
| Secret 來源 | <Secret manager 名稱；不填值> |

## 2. 環境與 namespace

| 環境 | 用途 | 每卡隔離方式 | 寫入權限 | Migration lane／lock |
|---|---|---|---|---|
| local | 開發 | <DB/schema/instance，以 `CARD_ID` 命名> | <角色> | <lock> |
| test | 自動測試 | <隔離或序列化方式> | <角色> | <lock> |
| staging | 整合驗證 | <方式> | <runner> | `db:staging:schema` |
| production | 正式服務 | <受保護環境> | <runner only> | `db:production:schema` |

## 3. 任務宣告與鎖定

每張碰 DB 的卡必填：

```yaml
db_scope: none | read | write | schema | data-migration
db_namespace: <依 CARD_ID 的 namespace 或 —>
db_resources:
  - db:<environment>:schema
  - db:<environment>:table:<table-name>
migration_phase: none | expand | migrate | contract
```

列出互斥規則、lease TTL、續約與逾期回收程序：

<專案實作>

## 4. Migration 執行與驗證

| 階段 | 命令／workflow | 成功條件 | 失敗處理 |
|---|---|---|---|
| Fresh DB rehearsal | <命令> | <migration + test evidence> | <程序> |
| Staging | <workflow> | <對帳 + smoke test> | <rollback> |
| Production | <workflow> | <source SHA、migration ID、對帳> | <rollback/restore> |

資料 migration 另填：批次大小、速率限制、checkpoint、重跑 idempotency、前後筆數／checksum 對帳方式。

## 5. 回滾與緊急處理

- 備份／復原點：<何時建立、保存位置、復原責任者>
- Expand／migrate／contract 相容窗口：<版本或期間>
- 不可逆操作的人工 sign-off：<誰、如何記錄>
- 停止條件與 runbook：<連結>
