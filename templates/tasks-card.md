# <卡ID> <功能名>  〔T0/T1/T2/T3/T4；🔴紅線 / ⚪一般〕

- 需求：<GitHub 帳號>　規劃：<模型@工具 / 帳號>　分支：`ai/<模型或工具>/<卡ID>`
- 執行：<模型@工具>　查核：<模型@工具>（須 ≠ 執行）
- worktree：`../<repo>-<卡族ID>`（**僅 A 類**；B/C 類填 `—不適用`。結案時必須已移除—canonical §2）
- Initiative：<父卡 ID／—>　spec 基線：<版本／—>　iteration：<0 起算>
- 作業狀態：owner <actor>；最後交接 <ISO 8601>；阻塞：<原因／等待對象／解除條件／—>
- DB：<`db_scope`／namespace／resource claims；無影響填 `none`—canonical §4.2>
- 部署：<是/否>　環境：<staging/production/—>　PR：<#/URL>　Merge SHA：<SHA/—>
- 範圍：見 [`<spec 檔>`](../<spec 檔>) §<X>（T3/T4 必填）／或於此簡述（T0–T2）
- Discovery：<brief 路徑／人類確認者與時間／T0–T2 可填—>
- 交付／部署狀態住 [`../TASKS.md`](../TASKS.md) Ledger

## Log

- <ISO 8601> handoff by <actor> → owner <actor>；iteration <n>；SHA <sha>；證據 <連結>。
- <ISO 8601> review by <actor> → approve/request-changes；finding <severity｜證據｜處置>；source SHA <sha>。
- <ISO 8601> blocked/escalated by <actor> → <原因；等待對象；解除條件／決策>。
