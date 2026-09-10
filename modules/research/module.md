---
name: research
when: 卡的階段計畫含研究：量測、下結論、或判不可判定
non_scope: ⛔ 不寫統計紅線（住 modules/stat-redline）；⛔ 不寫規劃階段（住 stages/planning.md）
last_confirmed: 2026-09-05
---

# 模組 research

## 0 · 宣告區塊

啟用條件＝`enable_if`（CLI 判啟用的唯一依據；`enable_when` 是同義散文、只給人讀；事實來源＝`fact_source`）；未啟用時下列每一項都不存在，唯 `fields` 的結構合法性例外（`core/card-schema.md` §1 (b)）。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "research",
  "enable_when": "卡面 stage_plan 含 研究",
  "enable_if": {"kind": "stage_plan_has", "stage": "研究"},
  "fact_source": "卡面 JSON",
  "adds": {
    "fields": [],
    "stages": ["研究"],
    "enums": {"states": ["不可判定"]},
    "transitions": {
      "add": [
        {
          "from": "研究/待確認",
          "to": "研究/不可判定",
          "condition": "交回單 verdict＝不可判定"
        },
        {
          "from": "研究/不可判定",
          "to": "需求/待辦",
          "condition": "重述問題"
        },
        {
          "from": "研究/不可判定",
          "to": "結案/待確認",
          "condition": "以不可判定寫裁定單"
        }
      ],
      "remove": []
    },
    "flags": [],
    "notes": ["F-research-01", "F-research-02", "F-research-03", "F-research-04"],
    "handoff_sections": ["量測紀錄（可重跑）", "結論"]
  },
  "project_inputs": [],
  "params": {}
}
```

## 1 · 條文

- 交出可判定結論或不可判定：交回單加「量測紀錄（可重跑）」「結論」兩段（§0）；結論段起首逐字 verdict＝可判定 或 verdict＝不可判定。
- 從需求階段離開後進入本階段。
- 需求方收口「夠了：可判定」時 `move` 到規劃／待辦；`stage_plan` 無規劃則到執行／待辦。
- 交回單 verdict＝不可判定且需求方收口「夠了：不可判定」時 `move` 到研究／不可判定；再由需求方選重述問題或以不可判定結案（§0 轉移）。
- ① `notes --stage 研究` ② PM `brief --for executor`，派工單附該卡與相關卡的既有留言 ③ 執行者 `review --file --role executor` 交回 ④ PM 判缺段與 R1 R2 ⑤ 討論回合：需求方提問、執行者答，每輪一則留言；需求方以一則留言收口，逐字「夠了：可判定」「夠了：不可判定」「再量：<問題>」三種之一 ⑥ 查核者 `self_run` 重跑量測、貼裁決 ⑦ PM `move`。
- 「再量」→ 退回同階段再派（`core/state-machine.md` §3）；⛔ 不在討論留言裡改核心痛點。
- 高階型研究卡在 `self_run` 列出可重跑全部量測的指令；對抗性反測表只在 stat-redline 啟用時要求（住 `modules/stat-redline/module.md`）。
- 需求方：提問、判夠了嗎、選不可判定的出口；⛔ 不要求附行動建議。
- PM：派工與派審都附該卡全部既有留言並寫明資料截止點、截止後新增的相關留言補派、判交回單完整性與 R1 R2、`move`；⛔ 不判結論對錯。
- 執行者：量測、下結論、誠實標不可判定；⛔ 不把不顯著寫成否定、⛔ 不代規劃寫規格。
- 查核者：用交回的指令重跑、只驗可重跑；⛔ 不裁結論真值。

## 2 · 注意事項

- F-research-01：不顯著⇒不可判定；不可判定的結論⛔ 不得被後續卡引為反證或否定證據。
- F-research-02：研究卡是討論形狀，⛔ 不是送審形狀；量測紀錄段寫指令、環境、母體大小、掃描數與輸出檔路徑。
- F-research-03：研究執行者研究前先讀該卡全部留言，⛔ 不只讀派工單；查核者依派工單附入的留言與截止點讀（§1），⛔ 不自行擴讀。
- F-research-04：量測或設計前先搜既有解法（論文／GitHub／官方文件），列出搜過什麼與沒找到什麼。
