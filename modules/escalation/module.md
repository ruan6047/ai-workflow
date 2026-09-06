---
name: escalation
when: 專案啟用升級梯：同一 iteration 反覆退回時
non_scope: ⛔ 不寫第 3 次退回的預設處置（住 roles/pm.md F-PM-01）
last_confirmed: 2026-09-06
---

# 模組 escalation

## 0 · 宣告區塊

唯一啟用條件＝`enable_when`（一個 predicate；事實來源＝`fact_source`）；未啟用時下列每一項都不存在。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "escalation",
  "enable_when": "專案 .wf/modules.json 列出",
  "fact_source": "modules.json",
  "adds": {
    "fields": ["escalation_count"],
    "stages": [],
    "states": ["升級"],
    "transitions": {
      "add": [
        {
          "from": "*/退回",
          "to": "same/升級",
          "condition": "同 iteration 第 N 次退回，N＝params.escalate_after"
        },
        {
          "from": "*/升級",
          "to": "same/進行中",
          "condition": "換人或換級再派；--ruling 缺即印"
        },
        {
          "from": "*/升級",
          "to": "結案/待確認",
          "condition": "需求方裁定收尾"
        }
      ],
      "remove": []
    },
    "flags": [],
    "counters": ["escalation_count"],
    "move_prints": ["escalation_threshold"],
    "notes": ["F-escalation-01", "F-escalation-02", "F-escalation-03", "F-escalation-04"],
    "handoff_sections": ["升級單（三次退回逐字理由、四選一各值證據）"]
  },
  "project_inputs": [],
  "params": {
    "escalate_after": 3
  }
}
```

## 1 · 條文

- `escalation_count`＝本 iteration 內 `move --to */退回` 的次數，由 `move` 累加；進執行階段（iteration +1）與 升級 → 進行中 時歸零，⛔ 不由人手改。
- 轉退回依核心轉移表（⑤ 不過）；規劃錯誤前提走 R1 不過的核心路徑，等待外部條件走阻塞，同 SHA 重複查核不收。
- `escalation_count` 達 `params.escalate_after`（種子 3）時 `move` 印「達升級門檻」；PM 組裁定單（升級類）後 `move --to <同階段>/升級`。
- 裁定單（升級類，`core/ruling.md`）由 PM 組，§0 宣告的交接段填：每次退回的 `wf-return` 留言 URL、blocking finding 的 `finding_class` 與 `root_cause_id`、逐字理由、核心痛點原文、四選一各值「若成立會是什麼證據」。
- 需求方以一則 `wf:ruling` 四選一裁定（換人／退回上一階段／停止／退回無效）；「改規格」⛔ 不是合法值，改規格走 R1 不過的核心路徑（`stage_plan` 含規劃→規劃／退回，否則→需求／退回）。
- 換人或換級（能力層級升一級）時 PM `move --ruling <URL> --to <同階段>/進行中` 再派；退回無效亦回進行中，由執行者原樣交回再審。
- 退回上一階段時 PM 先 `move --ruling <URL>` 回進行中，執行者交回後 PM 以 R1 不過走核心轉移表退回規劃或需求。
- 停止時 `move --ruling <URL> --to 結案/待確認`，再依結案階段走停止。
- PM：計數以 `move` 為準、組裁定單、落裁定；⛔ 不裁定、⛔ 不手改 `escalation_count`。
- 需求方：四選一裁定；⛔ 不代組裁定單。

## 2 · 注意事項

- F-escalation-01：純 governance／coordination／environment finding 造成的退回照核心表轉、照 `move` 計數；裁定單逐次標 `finding_class`，供需求方裁「退回無效」。
- F-escalation-02：達門檻⛔ 不按整數自動升級；裁定單組好才 `move` 到升級。
- F-escalation-03：裁定單只寫事實與各值證據，⛔ 不含建議、⛔ 不代需求方選值。
- F-escalation-04：裁定單的各次退回理由逐字轉錄自 `wf-return`，⛔ 不摘要。
