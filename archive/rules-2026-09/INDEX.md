# archive/rules-2026-09 · 封存索引（第三輪重構第 0 步，2026-09-04）

唯讀。⛔ 不得引用此處任何條文為判準（CLAUDE.md）。新規則本體依 `docs/research/REBUILD-SKELETON-2026-09-04.md` §十三 逐步填入。

| 原路徑 | 現路徑 | 內容 |
|---|---|---|
| `README.md`、`AGENTS.md`、`CLAUDE.md` | 同名 | 三個入口檔的舊全文（入口已先清成 stub） |
| `AI_WORKFLOW.md` | 同名 | 舊 canonical 規則 |
| `stage-rules/`、`templates/`、`tier-rules.md`、`MODEL_ROUTING.md`、`ADOPTION.md` | 同名 | 舊階段規則、範本、級別、模型路由、導入 |
| `docs/*.md`（10 份設計文件） | `docs/` | 舊設計與裁定文件 |
| `cli/` | `cli/` | 舊 `wfcli` 與其測試；凍結不再改 |
| `scripts/` | `scripts/` | 舊掃描器與工具；CI 不再跑 |
| `archive/issues/`（原未納入 git） | `../issues/` | aiwf 112 張舊 issue 匯出，本步起納入 git |
| `snapshots/` | `snapshots/` | 舊每日快照的維運說明；產生者 `scripts/daily_snapshot.sh` 已在本目錄，launchd `com.wf.daily-snapshot` 需在本機卸載（需求方） |

| `tasks/`（5 份舊卡規格） | `../tasks/` | 與既有 `archive/tasks/` 同族；需求方 2026-09-05 裁定封存 |

| `docs/research/WORKFLOW-REDESIGN-2026-08-30.md`、`docs/research/drafts/` | `../research/` | 上一輪重構的決議紀錄與草稿；引用舊 CLI 與舊規則路徑（第 1 步審核 R4-01） |

未搬：`docs/research/REBUILD-*.md`、`docs/research/extract/`（本輪骨架與萃取，仍在用；萃取填完後整目錄移入 `archive/research/`）。
