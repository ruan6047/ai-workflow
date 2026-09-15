---
name: modules
when: 新增模組、修改 `modules/*/module.md` §0 宣告、調整 `enable_if`，或專案編輯 `.wf/modules.json` 的 `modules[]` 時
non_scope: ⛔ 不寫各模組的條文（住該模組 §1）；⛔ 不寫值域字面（住 core/enums.md）；⛔ 不寫卡面欄型別（住 core/card-schema.md）
last_confirmed: 2026-09-15
---

# 模組宣告、啟用與可用性

## 1 · 宣告的封閉鍵集合

`modules/*/module.md` §0 `yaml wf-module` 的頂層鍵集合**恰為**九鍵：`name`、`enable_when`、`enable_if`、`fact_source`、`scope`、`maturity`、`adds`、`project_inputs`、`params`。缺鍵與未知鍵皆為宣告驗證失敗。

- `scope` 值域＝`core/enums.md` 的 `module_scope`；`maturity` 值域＝同檔的 `module_maturity`。值域外＝宣告驗證失敗。
- `adds` 的子鍵集合封閉：`fields`、`stages`、`enums`、`transitions`、`flags`、`notes`、`counters`、`move_prints`、`handoff_sections`；未知子鍵＝失敗。
- `enable_if.kind` 須在 CLI 已實作的 kind 封閉集內（不在＝失敗）；`enable_when` 是 `enable_if` 的同義散文、只給人讀，事實來源＝`fact_source`。
- `params` 是種子：鍵為字串、值為 JSON 純量（字串、整數、浮點、布林）。專案覆寫值的型別須與種子相同。

## 2 · 啟用真相唯一

- `scope=project` 啟用 ⟺ 名列 `.wf/modules.json` 的 `modules[].name` **且** `enable_if` 成立。
- `scope=card` 啟用 ⟺ `enable_if` 成立。
- 取得啟用集合只經單一啟用入口；⛔ 不在動詞層各自組合 `modules_list` 與 predicate。

## 3 · 自動能力只由 `maturity=ready` 貢獻

「自動能力組合」＝下列七項，只有 `maturity=ready` 且已啟用的模組貢獻：`adds.enums.states`、`adds.transitions`、`adds.counters`、`adds.move_prints`、`adds.handoff_sections`、`core/return.md` `$defs/module_return_sections`、`core/dispatch.md` `wf-module-sections`。

- `manual`／`experimental`／`unavailable` 的 `adds.fields` 仍依 `core/card-schema.md` §1 (b) 作結構合法性容器；⛔ 不算自動能力。
- `experimental` ⛔ 不新增任何 production 開關：其可測試性只指測試 fixture 可直接組合該宣告，正式寫入路徑⛔ 不啟用其自動能力。
- `adds.notes` ⛔ 不在七項內：已啟用模組的 §2 條文不分 `maturity` 皆進 notes 合成（`core/verbs.md` §3 ④）。

## 4 · `.wf/modules.json` 的 `modules[]` 封閉驗證

四類皆拒：未知模組名、重複模組名、未知 `params` 鍵、`params` 型別不符宣告種子。`areas`／`merge_method`／`project`／`rules`／`remote` 不在本節射程，驗證行為依 `ADOPTION.md` §2。

## 5 · `ModuleValidation`：唯一邊界、fail-closed

模組可用性結果只由單一 `ModuleValidation` 邊界定義並輸出；其他動詞只消費、⛔ 不重定義。

- 對 `maturity=ready` 的模組雙向核對宣告與 hook：宣告的 `adds.counters`／`adds.move_prints` id 在 production registry 缺實作、registry 有實作而無任何宣告、載入該 registry 發生 `ImportError`，三者皆為明確失敗。非 `ready` 模組不加入自動能力組合，其缺實作⛔ 不構成失敗。
- §1 的宣告驗證、§4 的 `.wf/modules.json` 驗證與本節的雙向核對，任一項不過時：該次指令 rc≠0、stdout 列出完整修正資訊（模組名、錯誤鍵、期望值域或型別）、且對 GitHub 與 Project 零寫入呼叫。
- 兩側錯誤在同一次執行中全部收齊並逐條回報，⛔ 不在第一條就停。
- 既有專案的無效 `.wf/modules.json` 自下一次相關指令起一律拒絕操作：⛔ 不提供舊行為回退、⛔ 不以旗標或環境變數放行。
