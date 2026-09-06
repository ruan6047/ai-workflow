---
name: identity
when: 多實體共用同一 GitHub 帳號
non_scope: ⛔ 不寫代貼標記（住 core/naming.md §3）
last_confirmed: 2026-09-06
---

# 模組 identity

## 0 · 宣告區塊

唯一啟用條件＝`enable_when`（一個 predicate；事實來源＝`fact_source`）；未啟用時下列每一項都不存在。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "identity",
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
    "notes": ["F-identity-01"],
    "handoff_sections": [
      "身分三格（GitHub 帳號／session ID／訊息定位）"
    ]
  },
  "project_inputs": [],
  "params": {}
}
```

## 1 · 條文

- 派工單與裁定單的撰寫者在「身分三格」段（§0 交接段，`brief` 印缺段）填 GitHub 帳號、session ID（transcript 檔名的 id）、該則訊息定位（uuid 或 timestamp）。
- 交回單、裁決與清單提案的撰寫者在留言散文段填同三格；PM 判有沒有填，⛔ 不核對。
- 三格內⛔ 不填模型名、⛔ 不填 AI 工具；模型名住派工單「實際模型」段與代貼首行（`core/naming.md` §3）。
- 核對由需求方在本機 transcript 做。

## 2 · 注意事項

- F-identity-01：換實體接手時三格重填；⛔ 不沿用前一實體的 session ID。

→ [archive/rules-2026-09/templates/dispatch-package.md](../../archive/rules-2026-09/templates/dispatch-package.md)、[archive/rules-2026-09/templates/verdict.md](../../archive/rules-2026-09/templates/verdict.md)、[archive/rules-2026-09/AI_WORKFLOW.md](../../archive/rules-2026-09/AI_WORKFLOW.md)
