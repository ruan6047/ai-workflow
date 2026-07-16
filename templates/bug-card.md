# BUG-<id> <一句話症狀> 〔T2/T3/T4；🔴紅線 / ⚪一般〕

- 重現：<步驟>　環境：<版本/資料/裝置>
- 預期 vs 實際：<expected> ／ <actual>
- 根因：<調查結論>（不明時先寫「調查中」，屬慢線）
- 修復：<做法>　回歸測試：<檔:test 名>（先紅後綠）
- 需求：<GitHub 帳號>　執行：<模型@工具>　查核：<模型@工具>（須 ≠ 執行）　分支：`ai/<模型@工具>/BUG-<id>`
- Initiative：<父卡／—>
- owner、worktree、iteration、最後交接、阻塞與 current-state 見 [`../TASKS.md`](../TASKS.md) Ledger；歷史寫入 adapter event log

## Log

- <ISO 8601> handoff by <actor> → owner <actor>；iteration <n>；SHA <sha>；證據 <連結>。
- <ISO 8601> review by <actor> → approve/request-changes；finding <severity｜證據｜處置>；source SHA <sha>。
- <ISO 8601> blocked/escalated by <actor> → <原因；等待對象；解除條件／決策>。
