---
name: stat-redline
when: 卡面 tier_basis.sensitive 含 statistics：統計／ML／資料正確性
non_scope: ⛔ 不寫研究階段本身（住 modules/research）
last_confirmed: 2026-09-05
---

# 模組 stat-redline

## 0 · 宣告區塊

唯一啟用條件＝`enable_when`（一個 predicate；事實來源＝`fact_source`）；未啟用時下列每一項都不存在。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "stat-redline",
  "enable_when": "statistics ∈ 卡面 tier_basis.sensitive",
  "fact_source": "卡面 JSON",
  "adds": {
    "fields": [],
    "stages": [],
    "states": [],
    "transitions": {
      "add": [],
      "remove": []
    },
    "flags": [],
    "notes": [],
    "handoff_sections": [
      "紅線區塊（本卡的窗口與門檻）",
      "對抗性反測表（≥3 角度，各寫支持／推翻／未能檢定）"
    ]
  },
  "project_inputs": [],
  "params": {}
}
```

## 1 · 條文

- 待第 4b 步回填（2026-09-05）；來源列＝04#135–138；03#57；02#66。

## 2 · 注意事項

- 待第 4b 步回填（2026-09-05）；id 形狀 `F-stat-redline-NN`。
