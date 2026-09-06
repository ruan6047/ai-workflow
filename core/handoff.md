---
name: handoff
when: 寫或讀任一份交接文件前，先讀本檔的共通規則
non_scope: ⛔ 不寫三份文件各自的段落表與 schema（住 core/dispatch.md、core/return.md、core/ruling.md）
last_confirmed: 2026-09-07
---

# 三份交接文件

每段首行 `[來源: <來源>/<檔>#<節> · <name>：<when> · confirmed <日期>]`（`name`、`when` 取該檔 frontmatter）。CLI 段由 `brief` 從卡面 JSON、Project 投影欄、git、規則檔組；人填段只由該角色本人填；缺段印。

- 派工單（PM → 執行者或查核者）住 `core/dispatch.md`。
- 交回單（執行者或查核者 → PM，帶 `wf-return`）住 `core/return.md`。
- 裁定單（PM → 需求方，帶 `wf-ruling`）住 `core/ruling.md`。
