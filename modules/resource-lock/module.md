---
name: resource-lock
when: 同時有兩個以上執行者：派工當下板上有其他進行中的卡
non_scope: ⛔ 不寫 DB 契約（住 modules/db-contract）
last_confirmed: 2026-09-05
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
    "states": [],
    "transitions": {
      "add": [],
      "remove": []
    },
    "flags": [],
    "notes": [],
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

- 待第 4b 步回填（2026-09-05）；來源列＝00 §六；02#31–32 42 44；04#110–116 125–130。

## 2 · 注意事項

- 待第 4b 步回填（2026-09-05）；id 形狀 `F-resource-lock-NN`。
