---
name: enums
when: 寫或讀任何封閉值域（階段、狀態、級別、角色、紅線三軸、能力層級、db_scope）、寫 schema 的 enum、CLI 合成 choices 時讀
non_scope: ⛔ 不寫值的語意（住各定義檔）；⛔ 不寫轉移（住 core/state-machine.md）；⛔ 不放模組加的值（住各模組 `adds.states`）
last_confirmed: 2026-09-07
---

# 值域

所有封閉值域的唯一居所＝下方區塊（需求方 2026-09-07 裁定）；schema 以 `$ref` 指向（`wf-enums#/<鍵>`），CLI 執行期直接讀，散文只指名⛔ 不抄值。每鍵一個 `{"enum": […]}`，可直接當 schema 片段。模組加的狀態由 `adds.states` 在合成時併進 `states_core`（`core/card-schema.md` §1）。新值或新鍵須需求方裁定。

```json wf-enums
{"$id": "wf-enums",
 "stages": {"enum": ["需求", "研究", "規劃", "執行", "審核", "部署", "維護", "結案"]},
 "states_core": {"enum": ["待辦", "進行中", "待確認", "退回"]},
 "state_blocked": {"enum": ["阻塞"]},
 "states_terminal": {"enum": ["完成", "停止"]},
 "tiers": {"enum": ["T0", "T1", "T2", "T3", "T4"]},
 "roles": {"enum": ["requester", "pm", "executor", "reviewer"]},
 "sensitive": {"enum": ["public_contract", "security", "payment", "data_write", "migration", "production", "rules", "statistics"]},
 "recoverable": {"enum": ["reversible", "rollback_only", "irreversible"]},
 "blast": {"enum": ["file", "module", "repo", "cross_repo"]},
 "capability_levels": {"enum": ["經濟型", "主力型", "高階型"]},
 "db_scope": {"enum": ["none", "read", "write", "schema", "data-migration"]}}
```

- 狀態全集＝`states_core` ∪ `state_blocked` ∪ `states_terminal` ∪ 已啟用模組的 `adds.enums.states`；`停止` 只在結案階段有值（`core/state-machine.md` §2）。
- 模組擴充值域：宣告鍵＝該模組 `adds.enums.<鍵>`（需求方 2026-09-07 裁定通用形），只能加值、⛔ 不改基底值；今只有 `states` 有實例。其他鍵第一次出現時同 PR 加合成與可達性案例；⛔ 不預開空鍵。
- 詞表配套：本檔只放字面。值若是需要定義的詞，核心值住 `core/glossary.md`、模組加的值住該模組 §1；`core/glossary.md` 每個值域鍵一列、⛔ 不逐值列（需求方 2026-09-07）。
- `db_scope` 為 null 時＝未填，`open` 印。
