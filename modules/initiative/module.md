---
name: initiative
when: 卡有父卡：子切片、基線遞變、父卡持 規格基線
non_scope: ⛔ 不寫鏈深（住 core/verbs.md）
last_confirmed: 2026-09-06
---

# 模組 initiative

## 0 · 宣告區塊

啟用條件＝`enable_if`（CLI 判啟用的唯一依據；`enable_when` 是同義散文、只給人讀；事實來源＝`fact_source`）；未啟用時下列每一項都不存在，唯 `fields` 的結構合法性例外（`core/card-schema.md` §1 (b)）。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "initiative",
  "enable_when": "卡面 parent 非空",
  "enable_if": {"kind": "field_nonempty", "field": "parent"},
  "fact_source": "卡面 JSON",
  "adds": {
    "fields": [
      "parent_spec_version"
    ],
    "stages": [],
    "enums": {"states": []},
    "transitions": {
      "add": [],
      "remove": []
    },
    "flags": [],
    "counters": [],
    "move_prints": ["parent_spec_version_empty"],
    "notes": ["F-initiative-01", "F-initiative-02", "F-initiative-03"],
    "handoff_sections": [
      "規格基線（父卡 spec_version 與本卡登記版本）"
    ]
  },
  "project_inputs": [],
  "params": {}
}
```

## 1 · 條文

- 父卡保存目標、規格基線（規格欄與 `spec_version`）、依賴序、里程碑、決策與風險。
- 帶 `parent` 的卡採可獨立驗證的垂直切片。
- 帶 `parent` 的卡 `open --parent` 時由 `open` 登記 `parent_spec_version`＝父卡當時的 `spec_version`；空值由 `move` 印，⛔ 不派工。
- `brief` 在 §0 宣告的交接段印父卡 `spec_version` 與本卡 `parent_spec_version`；兩值不一致時查核者 REQUEST_CHANGES、PM 退回，⛔ 不以舊基線交付。
- 執行者發現交付須偏離已核可基線時凍結受影響部分並在卡上貼留言告知 PM；⛔ 不自行改基線後續作。
- PM 對照父卡依賴序逐張標受影響卡的影響級別（無影響／需改規格／前提失效／方向失效）並留痕；技術影響的事實依據由執行者提供，PM ⛔ 不自行判技術影響，級別仍由 PM 判（F-initiative-02）。
- 觸發者（執行者）、評估者（PM）、核可者（需求方）⛔ 不合於一人。
- 無影響不動；需改規格者更新該卡規格並重登 `parent_spec_version`；前提失效者轉阻塞，解除條件＝新基線核可；方向失效者交需求方裁停止或退回規劃／需求。
- 父卡規格由 `edit --ruling <核可裁定 URL>` 更新，`spec_version` +1；需求方核可前新基線⛔ 不生效。
- 核可後 PM 依核可裁定逐字同步待辦中受影響卡的規格與 `parent_spec_version`（⛔ 不自由改寫；需改寫者退回該卡規劃），並在進行中的受影響卡貼留言要執行者確認在途工作是否受波及。
- 已合併的卡⛔ 不回改；缺口另開帶 `parent` 的新卡。

## 2 · 注意事項

- F-initiative-01：基線變更紀錄＝父卡一則留言（日期、變更摘要、觸發卡、受影響卡與級別、核可裁定 URL）；⛔ 不用聊天或口頭共識代替。
- F-initiative-02：⛔ 不把方向失效降成需改規格以避免退回；級別由 PM 判並留痕，⛔ 不由觸發者自判。
- F-initiative-03：`parent_spec_version` 在建卡時填；⛔ 不留到派工。
