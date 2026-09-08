---
name: state-machine
when: 寫 `move`、寫模組 delta、判一張卡下一步能去哪時讀
non_scope: ⛔ 不寫誰該在什麼時候 move（住 roles/、stages/）；⛔ 不寫模組條文（住 modules/）
last_confirmed: 2026-09-07
---

# 狀態機

## 1 · 階段

八階段固定序＝`core/enums.md` 的 `stages` 順序。研究、部署、維護是卡級模組，唯一啟用條件＝該卡 `stage_plan` 含該階段。規劃可跳過，由級別決定（T0／T1），仍是核心。`stage_plan` 非空時必為此序的子序列、必含需求／執行／審核／結案（D3）；空＝未填，展開時只有需求階段，`move` 印。

## 2 · 狀態值域

值住 `core/enums.md`：核心＝`states_core`＋`states_terminal` 的 完成，加正交的 `state_blocked`。階段 delta：結案加 停止（終態）。模組 delta：research 加 不可判定、escalation 加 升級、maintenance 加 運行中。完成 只在結案階段有值（`only_in_stage`）；結案階段沒有 待辦、進行中（`states_remove`），入口＝結案／待確認。CLI 的 choices＝核心 ∪ 階段 delta ∪ 已啟用模組的值；未啟用的值寫不進去（→ [archive/rules-2026-09/AI_WORKFLOW.md §0.0 狀態值域](../archive/rules-2026-09/AI_WORKFLOW.md)；決策紀錄 C6）。

## 3 · 核心轉移表

唯一居所＝下方區塊（階段與狀態值域住 `core/enums.md`，本區塊只放轉移與 delta）；`move` 只接受合成表內的邊（D1）。`from`／`to` 的階段記法：`*`＝該卡階段計畫內任一非結案階段；`same`＝同階段；`next`＝階段計畫的下一階段（下一階段為結案時走 `last` 列）；`last`＝階段計畫內最後一個非結案階段；`清單`＝不在板。`state` 的 `<非終態>`＝該階段值域內除終態與 阻塞 外的每個狀態，含模組加的狀態；`<from>`＝進阻塞前的狀態，解除只回那一個狀態（每個非終態各有自己的阻塞節點）。`if`＝機械條件，值域 `plan_has:<階段>`／`plan_lacks:<階段>`，展開時不成立的邊不進合成表（D1）；`condition`＝給 PM 讀的條件與印，⛔ 不是機械條件。

```json wf-state-machine
{
  "required_stages": ["需求", "執行", "審核", "結案"],
  "only_in_stage": {"完成": "結案"},
  "stage_delta": {"結案": {"states_add": ["停止"], "states_remove": ["待辦", "進行中"]}},
  "initial": "需求/待辦",
  "transitions": [
    {"from": "需求/待確認", "to": "next/待辦", "condition": "⑤ 過；T2+ 而 stage_plan 缺規劃＝印"},
    {"from": "需求/待確認", "to": "清單", "condition": "撤銷；卡ID 保留、iteration 延續；無 --ruling 印"},
    {"from": "清單", "to": "需求/待辦", "condition": "open 復板；沿用 card_id／iteration"},
    {"from": "*/待辦", "to": "same/進行中", "condition": "派工；進執行時 iteration +1、source_sha=null"},
    {"from": "*/進行中", "to": "same/待確認", "condition": "交回；寫 --source-sha"},
    {"from": "*/待確認", "to": "next/待辦", "condition": "⑤ 過；審核階段 --ruling 種類＝wf-return，缺即印"},
    {"from": "last/待確認", "to": "結案/待確認", "condition": "⑤ 過；--ruling＝wf-return，缺即印"},
    {"from": "**/待確認", "to": "same/退回", "condition": "⑤ 不過（R2–R4）；審核階段 wf-return，缺即印；結案階段 wf-ruling（stages/closeout.md §4）"},
    {"from": "**/待確認", "to": "規劃/退回", "if": "plan_has:規劃", "condition": "⑤ R1 不過"},
    {"from": "**/待確認", "to": "需求/退回", "if": "plan_lacks:規劃", "condition": "⑤ R1 不過"},
    {"from": "*/退回", "to": "same/進行中", "condition": "再派；進執行時 iteration +1、source_sha=null（執行階段每次再派為新 iteration，計數隨之歸零）；同 iteration 第 3 次退回預設換人，需求方可否決"},
    {"from": "結案/退回", "to": "結案/待確認", "condition": "補驗後重交裁定單"},
    {"from": "**/<非終態>", "to": "same/阻塞", "condition": "寫 blocked.from；--ruling 種類＝wf-ruling kind=block，缺留言或缺鍵皆印"},
    {"from": "**/阻塞", "to": "same/<from>", "condition": "解除；清 blocked"},
    {"from": "結案/待確認", "to": "結案/完成", "condition": "印 PR 與分支狀態；封存"},
    {"from": "結案/待確認", "to": "結案/停止", "condition": "--ruling 種類＝wf-ruling kind=stop，缺留言或缺鍵皆印；封存"}
  ]
}
```

`**`＝該卡階段計畫內任一階段（含結案）。`同 iteration 第 3 次退回` 的處置條文住 `roles/pm.md` §4；escalation 模組啟用時由其 delta 接手。

## 4 · 模組 delta 合成

- 模組宣告區塊裡 `transitions.add` 與 `transitions.remove` 各列若干 `{from, to, condition}`（可帶 `if`），記法同上。
- 合成表＝核心 ∪ add − remove，再按該卡 `stage_plan` 展開；不在計畫內的階段沒有邊。
- 模組加狀態時，其 add 必同時給進邊與至少一條可達結案的出邊。
- 三個模組的 delta 住各自 `modules/<name>/module.md` §0 宣告，條文住同檔 §1。

## 5 · 可達性測試

CI job `reachability` 跑 `.github/scripts/reachability.py`，對每個合法 `stage_plan`（2026-09-05：16 種）斷言兩件：合成表定義集合內每個非終態有出邊且可達完成或停止；完成與停止出邊為空。另印每個案例從 `initial` 正向走不到的節點，⛔ 不擋（2026-09-07 加，`**/<非終態>` 修好前為 384 個）。同 job 另有五個會讓 rc≠0 的來源，2026-09-07 補宣告、⛔ 不是新增：模組 `adds.notes` 與其 §2 條列 id 的對帳；模組 `adds.handoff_sections` 與交接文件段名的對帳（集合、歸屬、模組存在性；段名規則住 `core/dispatch.md`）；模組 `adds.counters` 每個欄都在 `adds.fields`；`--selftest` 的負控（`roles/conduct-common.md` §1「附負控輸出」）；`--selftest` 對正式表的兩個正控——R1 退回目標唯一（`stage_plan` 含規劃時只到 `規劃/退回`、缺規劃時只到 `需求/退回`）與 research 的 `不可判定` 進定義集合。矩陣隨被測物累加：本檔進 repo 時只測無模組；帶 delta 的模組進 repo 時同 PR 加該模組案例。
