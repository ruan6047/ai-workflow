---
name: naming
when: 配卡ID、開分支、命名檔案、寫留言首行時讀
non_scope: ⛔ 不寫留言內容的規則（住 core/verbs.md、core/return.md、core/ruling.md）
last_confirmed: 2026-09-07
---

# 命名

## 1 · 卡ID

- 形狀 `<AREA>-<NNN>`；AREA＝專案層 `.wf/modules.json` 的 `areas` 封閉枚舉；NNN＝`open` 依 repo 遞增，三位數起，只增不重用。
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
| `wf:return` | 執行者；帶 `json wf-return`（需求方 2026-09-07 裁定） | 只讀區塊 |
| `wf:ruling` | 需求方；帶 `json wf-ruling` | 只讀區塊 |
| `wf:log` | 任何角色；純散文，研究與量測全文 | 否 |
| `代貼裁定・授權來源：<…>`、`代貼裁決・來源：<…>・被審 SHA：<…>` | PM 代貼時取代首行；原文從第二行起 | 否 |

## 4 · 檔案

- 規則檔：kebab-case、無日期；`core/`、`stages/`、`roles/`、`modules/<name>/module.md`。
- 研究與紀錄檔：`docs/research/<YYYY-MM-DD>-<slug>.md`。
- 專案層檔一律住 `.wf/`：`modules.json`、`tiers.md`、`stages/<階段>.md`、`contracts/`。
- 注意事項 id：`F-<階段或角色>-NN`（框架）、`F-<模組名>-NN`（模組）、`P-<階段>-NN`（專案）、`T-<階段>-NN`（卡面）。
- finding id：`<card_id>-R<iteration>.<查核序>-<序>`，由該則交回單的作者填；查核序取派工單的同名段，`review` ⛔ 不編號。

## 5 · 規則檔的固定節與行數上限

上限＝天花板不是配額；超過即停下拆（需求方 2026-09-07 裁定；core 各檔 150 同日裁定）。

| 檔種 | 固定節（順序不可換） | 上限 |
|---|---|---|
| 階段檔 | 1 目標與產出 · 2 進入／離開條件 · 3 狀態 delta（引用 core） · 4 階段內迴圈（①–⑤ 在本階段的形狀） · 5 各角色做／⛔ 不做 · 6 注意事項 `F-<階段>-NN` | 60 行 |
| 角色檔 | 1 職責 · 2 紅線 · 3 動作前自檢 · 4 注意事項 `F-<角色>-NN` | 60 行 |
| conduct-common.md | 1 操作紀律（實跑、fetch、不截斷、rc、負控、逐字、多居所、驗原件） · 2 書寫紀律（數字帶日期、不寫行號、引用逐字） | 40 行 |
| core 各檔 | 依各檔自身定義 | 150 行（需求方 2026-09-07 裁定） |
| module.md | 0 宣告區塊（`yaml wf-module`） · 1 條文 · 2 該模組加的注意事項 | 80 行 |
| README | 1 心智模型（≤12 行） · 2 角色一句話 · 3 查詢指令 | 40 行 |
| ADOPTION | 1 repo 前置（ruleset、merge_method） · 2 `.wf/modules.json` 種子 · 3 Project 五欄 · 4 第一張卡 | 60 行 |

每個規則檔、模組檔、core 檔統一 frontmatter 四欄（沿舊 stage-rules 與卡片簡介的 skill 式檔頭，決策 9）：`name`、`when`（適用時機一句）、`non_scope`（⛔ 不是什麼一句）、`last_confirmed`（日期，規則文件自身過期；`rule_confirm_days` 見 `core/params.md`）。
