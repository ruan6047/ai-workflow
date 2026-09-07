---
name: resource-lock
when: 同時有兩個以上執行者：派工當下板上有其他進行中的卡
non_scope: ⛔ 不寫 DB 契約（住 modules/db-contract）
last_confirmed: 2026-09-06
---

# 模組 resource-lock

## 0 · 宣告區塊

唯一啟用條件＝`enable_when`（一個 predicate；事實來源＝`fact_source`）；未啟用時下列每一項都不存在。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "resource-lock",
  "enable_when": "派工當下板上狀態＝進行中且 owner.actor 與本卡不同的卡 ≥1 張",
  "fact_source": "Project 投影欄 狀態＋owner",
  "adds": {
    "fields": [
      "worktree",
      "lease_expires_at"
    ],
    "stages": [],
    "enums": {"states": []},
    "transitions": {
      "add": [],
      "remove": []
    },
    "flags": [],
    "counters": [],
    "move_prints": ["resources_intersection"],
    "notes": ["F-resource-lock-01", "F-resource-lock-02", "F-resource-lock-03", "F-resource-lock-04"],
    "handoff_sections": [
      "資源宣告逐條",
      "寫入集交集"
    ]
  },
  "project_inputs": [
    ".wf/contracts/CONTROL_PLANE.md"
  ],
  "params": {
    "lease_ttl_hours": 24
  }
}
```

## 1 · 條文

- 派工（`move` 到進行中）時印本卡 `resources` 與現役卡 `resources` 的交集（§0 交接段「寫入集交集」）；有交集由 PM 判排隊或並行，⛔ 不自動擋。
- 交集判定＝完全字串比對；`db:<env>:schema` 不支配 `db:<env>:table:<name>`，db 文法住 `modules/db-contract`。
- 資源宣告逐條寫 `file:<路徑>`／`port:<n>`／`container:<name>`／`db:…`，含交付必要的重現工具；現役卡的定義依 `stages/closeout.md` F-結案-03，釋放時點依 F-結案-02。
- 認領時把實際 worktree 路徑與分支寫回卡面 `worktree`、`branch`；一卡一 worktree 一 session，靠註冊查重。
- `lease_expires_at`＝認領時刻＋`params.lease_ttl_hours`。
- lease 以 `edit --set lease_expires_at=` 續約；派工單與交回單引用有效 lease，過期⛔ 不接受。
- 破壞性入口（build／rebuild／migration）由專案在 `.wf/contracts/CONTROL_PLANE.md` 列出；啟動前確認本卡 lease 有效，無效⛔ 不跑。
- 資料庫視為共享可變基礎設施，寫入隔離並序列化；口頭協調、Markdown、聊天訊息⛔ 不構成鎖。
- 本機資源工具只建立、釋放資源並回報；⛔ 不寫狀態面，狀態只由 `move` 寫。
- 執行者的 Edit／Write／server 路徑指向 worktree，⛔ 不指 main checkout。
- 交回前把 cwd 移出 worktree；merge 者先離開 worktree。
- ⛔ 不在 worktree 內移除自身目錄。
- ⛔ 不從仍被 checkout 的分支刪 branch。
- 同卡族共用 worktree，修復卡切新分支⛔ 不另開目錄；卡族全結案後才移除 worktree 與分支。
- 驗證命令會改 tracked file 時在拋棄式 worktree 執行；查核沙箱無 lease、無 owner。

## 2 · 注意事項

- F-resource-lock-01：worktree 與分支採註冊制，沒寫回卡面才算違規；命名對不上⛔ 不算。
- F-resource-lock-02：派工前對照 `git worktree list` 與現役卡的 `worktree` 欄，孤兒目錄、死路徑、殘留 lease 只列進派工單；⛔ 不自動清理，清理在結案批次做。
- F-resource-lock-03：回收到期 worktree 前先檢查未提交變更；⛔ 不靜默刪除工作內容。
- F-resource-lock-04：worktree 內 submodule 目錄空是預期，需要時明確初始化；「檔案不在我的樹裡」⛔ 不構成 finding。
