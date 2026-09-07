---
name: pitfalls-13
when: 專案啟用 13 族踩坑清冊
non_scope: ⛔ 不寫核心注意事項（住 core/verbs.md §3）
last_confirmed: 2026-09-06
---

# 模組 pitfalls-13

## 0 · 宣告區塊

唯一啟用條件＝`enable_when`（一個 predicate；事實來源＝`fact_source`）；未啟用時下列每一項都不存在。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "pitfalls-13",
  "enable_when": "專案 .wf/modules.json 列出",
  "fact_source": "modules.json",
  "adds": {
    "fields": [],
    "stages": [],
    "states": [],
    "transitions": {
      "add": [],
      "remove": []
    },
    "flags": [],
    "notes": ["F-pitfalls-13-01"],
    "handoff_sections": [
      "13 族踩坑清冊（每族恰一行，已檢查／不適用／發現）"
    ]
  },
  "project_inputs": [],
  "params": {}
}
```

## 1 · 條文

- `notes` 在編號清單後附 13 族樣板（§0 交接段），分兩層印：全階段層每階段都印，執行層只在執行階段加印。
- 把 `宣稱超過證據`、`列舉或覆蓋不完整` 與尚無實測階段的 `交付未落地或未接線`、`文件與現實漂移`、`狀態轉移或生命週期`、`可重現性不足`、`並發或時序不安全`、`資源或寫入集宣告` 列在全階段層。
- 把 `守衛涵蓋不足或可被繞過`、`身分或歸屬對應錯誤`、`程序或規格照字面不成立`、`留痕失真或遺失`、`解析或正規化錯誤` 列在執行層。
- 族名以 archive/issues/130 結案留言的 13 個字串為準；⛔ 不改字、⛔ 不自造族。
- 無實測階段的族留在全階段層；下放到某階段須需求方裁定。
- 在交回單的 13 族段每族寫恰一行，值只取 `已檢查`／`不適用`／`發現` 之一。
- 離開階段前交齊交回單的 13 族段（`core/return.md` `$defs/module_return_sections`）；`review` 印缺段，⛔ 不判內容。
- 13 族三值與回應三值（followed／not_applicable／found）⛔ 不互代。
- 新族只由 finding 的 `root_cause_id` 歸併、或需求階段由需求方與 PM 供給並指名維護者；⛔ 不由執行者自增。
- 同一 repo 既有解法的索引由 PM 寫進專案層 `.wf/stages/<階段>.md`，隨 P- 注意事項印（`core/verbs.md` §3）；⛔ 不由 CLI 產生。
- ⛔ 不設每階段族數上限。

## 2 · 注意事項

- F-pitfalls-13-01：`已檢查` 裸寫，說明進 evidence；⛔ 不升成 `發現`、⛔ 不加敘述。
