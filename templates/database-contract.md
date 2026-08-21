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

⚠️ **`schema` 與 `table` 是字面關鍵字，不是佔位符。** 只有 `<environment>` 與
`<table-name>` 要換成你的值。整個 schema 的鎖逐字就是 `db:production:schema`——
**不要**把 `schema` 換成 schema 的名字。文法在 `cli/src/wf_cli/resources.py`
（`db:[^:]+:(schema|table:.+)`），換掉會被 `ResourceDeclarationError` 拒收。

⚠️ 注意上面 yaml 區塊**第一行**的 `db_scope` 也有一個 `schema`，那是**另一回事**
（宣告這張卡對資料庫的動作幅度），與資源 token 裡的字面關鍵字無關。兩種身分在同
一個區塊內相隔三行，是這個誤讀最容易發生的地方。

這條寫在這裡是因為它**已經發生過**：採用專案 cpbl-analytics 的
`docs/DATABASE_CONTRACT.md` 把它寫成 `db:<environment>:cpbl`（`cpbl` 是該專案的
schema 名），**5 行、6 處**全部不合法（`:20` 一行有兩處；⚠️ `ai-workflow#87` 卡面另列 `:38`，那是散文裡的 `db:*` 萬用字元，不是同一個病）。⚠️ **失效方向是靜默的**——照著寫的人要嘛貼進卡面被
拒收、要嘛寫進 spec 檔而永遠沒有人檢查。

⚠️ **`db:<env>:schema` 不支配 `db:<env>:table:<name>`。** 互斥判定是
`find_conflicts` 的完全字串比對，所以宣告整個 schema **不會**擋住另一張只宣告
個別表的卡。這與「schema 是全域互斥鎖」的直覺相反：兩張卡可以同時動同一張表而
不被判為衝突。要真的互斥，兩邊必須宣告**同一個字串**。

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
