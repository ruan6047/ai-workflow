---
name: state-machine
when: 寫 `move`、寫模組 delta、判一張卡下一步能去哪時讀
non_scope: ⛔ 不寫誰該在什麼時候 move（住 roles/、stages/）；⛔ 不寫模組條文（住 modules/）
last_confirmed: 2026-09-05
---

# 狀態機

## 1 · 階段

八階段固定序：需求 → 研究 → 規劃 → 執行 → 審核 → 部署 → 維護 → 結案。研究、部署、維護是卡級模組，唯一啟用條件＝該卡 `stage_plan` 含該階段。規劃可跳過，由級別決定（T0／T1），仍是核心。`stage_plan` 必為此序的子序列、必含需求／執行／審核／結案（D3）。

## 2 · 狀態值域

核心：待辦／進行中／待確認／退回／完成，加正交的 阻塞。階段 delta：結案加 停止（終態）。模組 delta：research 加 不可判定、escalation 加 升級、maintenance 加 運行中。完成 只在結案階段有值（`only_in_stage`）；結案階段沒有 待辦、進行中（`states_remove`），入口＝結案／待確認。CLI 的 choices＝核心 ∪ 階段 delta ∪ 已啟用模組的值；未啟用的值寫不進去（→ [archive/rules-2026-09/AI_WORKFLOW.md §0.0 狀態值域](../archive/rules-2026-09/AI_WORKFLOW.md)；決策紀錄 C6）。

## 3 · 核心轉移表

唯一居所＝下方區塊；`move` 只接受合成表內的邊（D1）。`from`／`to` 的階段記法：`*`＝該卡階段計畫內任一非結案階段；`same`＝同階段；`next`＝階段計畫的下一階段（下一階段為結案時走 `last` 列）；`last`＝階段計畫內最後一個非結案階段；`清單`＝不在板。`state` 的 `<from>`＝進阻塞前的狀態，解除只回那一個狀態（每個非終態各有自己的阻塞節點）。`when` 是給 PM 讀的條件與印，⛔ 不是機械條件。

```json wf-state-machine
{
  "stages": ["需求", "研究", "規劃", "執行", "審核", "部署", "維護", "結案"],
  "required_stages": ["需求", "執行", "審核", "結案"],
  "states": ["待辦", "進行中", "待確認", "退回", "完成", "阻塞"],
  "only_in_stage": {"完成": "結案"},
  "stage_delta": {"結案": {"states_add": ["停止"], "states_remove": ["待辦", "進行中"]}},
  "terminal": ["完成", "停止"],
  "initial": "需求/待辦",
  "transitions": [
    {"from": "需求/待確認", "to": "next/待辦", "when": "⑤ 過；T2+ 而 stage_plan 缺規劃＝印"},
    {"from": "需求/待確認", "to": "清單", "when": "撤銷；卡ID 保留、iteration 延續；無 --ruling 印"},
    {"from": "清單", "to": "需求/待辦", "when": "open 復板；沿用 card_id／iteration"},
    {"from": "*/待辦", "to": "same/進行中", "when": "派工；進執行時 iteration +1、source_sha=null"},
    {"from": "*/進行中", "to": "same/待確認", "when": "交回；執行階段寫 --source-sha"},
    {"from": "*/待確認", "to": "next/待辦", "when": "⑤ 過；審核階段 --ruling 種類＝wf-return，缺即印"},
    {"from": "last/待確認", "to": "結案/待確認", "when": "裁定單（結案確認）"},
    {"from": "**/待確認", "to": "same/退回", "when": "⑤ 不過（R2–R4）；審核階段 wf-return、結案階段 wf-ruling，缺即印"},
    {"from": "**/待確認", "to": "規劃/退回", "when": "⑤ R1 不過且 stage_plan 含規劃"},
    {"from": "**/待確認", "to": "需求/退回", "when": "⑤ R1 不過且 stage_plan 缺規劃"},
    {"from": "*/退回", "to": "same/進行中", "when": "再派；進執行時 iteration +1、source_sha=null；同 iteration 第 3 次退回預設換人，需求方可否決"},
    {"from": "結案/退回", "to": "結案/待確認", "when": "補驗後重交裁定單"},
    {"from": "**/待辦|進行中|待確認|退回", "to": "same/阻塞", "when": "寫 blocked.from；--ruling 種類＝wf-ruling kind=block，缺留言或缺鍵皆印"},
    {"from": "**/阻塞", "to": "same/<from>", "when": "解除；清 blocked"},
    {"from": "結案/待確認", "to": "結案/完成", "when": "印 PR 與分支狀態；封存"},
    {"from": "結案/待確認", "to": "結案/停止", "when": "--ruling 種類＝wf-ruling kind=stop，缺留言或缺鍵皆印；封存"}
  ]
}
```

`**`＝該卡階段計畫內任一階段（含結案）。`同 iteration 第 3 次退回` 的處置條文住 `roles/pm.md` §4；escalation 模組啟用時由其 delta 接手。

## 4 · 模組 delta 合成

- 模組宣告區塊裡 `transitions.add` 與 `transitions.remove` 各列若干 `{from, to, when}`，記法同上。
- 合成表＝核心 ∪ add − remove，再按該卡 `stage_plan` 展開；不在計畫內的階段沒有邊。
- 模組加狀態時，其 add 必同時給進邊與至少一條可達結案的出邊。
- 三個模組的 delta 釘死於骨架 §四，條文住各自 `modules/<name>/module.md`。

## 5 · 可達性測試

CI job `reachability` 跑 `.github/scripts/reachability.py`，對每個合法 `stage_plan`（2026-09-05：16 種）斷言兩件：合成表定義集合內每個非終態有出邊且可達完成或停止；完成與停止出邊為空。矩陣隨被測物累加：本檔進 repo 時只測無模組；帶 delta 的模組進 repo 時同 PR 加該模組案例。
