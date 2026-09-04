---
name: naming
when: 配卡ID、開分支、命名檔案、寫留言首行時讀
non_scope: ⛔ 不寫留言內容的規則（住 core/verbs.md、core/handoff.md）
last_confirmed: 2026-09-05
---

# 命名

## 1 · 卡ID

- 形狀 `<AREA>-<NNN>`；AREA＝專案層 `.wf/modules.json` 的 `areas` 封閉枚舉；NNN＝`open` 依 repo 遞增，三位起、不補零上限。
- 標題 slug 只放 issue 標題；⛔ 不進卡ID。
- 修復卡 `<原卡>-FIX<n>`，n 從 1 起；只在碼已進 main 的事後查核時開。
- aiwf 種子 areas：WF、CLI、DOC、OPS。

## 2 · 分支

- 一卡一分支，名 `wf/<card_id>`；`move` 到執行／進行中時寫回 `branch`。
- 修復卡用自己的分支；⛔ 不共用原卡分支。

## 3 · 留言首行

| 首行 | 誰寫 | CLI 讀 |
|---|---|---|
| `wf:move`、`wf:edit`、`wf:reject` | CLI，純散文 | 否 |
| `wf:note` | 任何角色；帶 `json wf-note` | 只讀區塊 |
| `wf:verdict` | 查核者；帶 `json wf-return` | 只讀區塊 |
| `wf:ruling` | 需求方；帶 `json wf-ruling` | 只讀區塊 |
| `wf:log` | 任何角色；純散文，研究與量測全文 | 否 |
| `代貼裁定・授權來源：<…>`、`代貼裁決・來源：<…>・被審 SHA：<…>` | PM 代貼時取代首行；原文從第二行起 | 否 |

## 4 · 檔案

- 規則檔：kebab-case、無日期；`core/`、`stages/`、`roles/`、`modules/<name>/module.md`。
- 研究與紀錄檔：`docs/research/<YYYY-MM-DD>-<slug>.md`。
- 專案層檔一律住 `.wf/`：`modules.json`、`tiers.md`、`stages/<階段>.md`、`contracts/`。
- 注意事項 id：`F-<階段或角色>-NN`（框架）、`P-<階段>-NN`（專案）、`T-<階段>-NN`（卡面）。
- finding id：`<card_id>-R<iteration>-<序>`，由 `review` 編。
