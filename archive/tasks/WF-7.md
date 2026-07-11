# WF-7 任務卡拆獨立檔（card-per-file）+ §7 加「相關任務」欄  〔🔴紅線：改看板結構＋canonical §7/§6.4〕

- 需求：ruan6047　規劃：ruan6047 + Claude-Opus-4.8@ClaudeCode　分支：`ai/Claude-Opus-4.8@ClaudeCode/WF-7`（直接 merge main）
- 執行：Claude-Opus-4.8@ClaudeCode　查核：ruan6047（sign-off，紅線人審；執行者不自審）
- 範圍：`TASKS.md` → 純 Ledger 索引；每卡移入 `tasks/<卡ID>.md`；§7 加「相關任務」欄、§6.4 改 card-per-file；templates 同步
- 狀態：見 [`../TASKS_ARCHIVE.md`](../TASKS_ARCHIVE.md)（已封存 🏁，1a0bcb4／merge 9adb60b）
- 註：本卡的「相關任務」欄與「完成卡不封存」設計於 WF-8 修訂——相關性移至 Ledger 依賴註記、恢復 git mv 封存

## Log
- 07-11 需求 by ruan6047：每張卡拆成獨立檔，避免 AI 常駐讀整板浪費算力；卡內標註相關任務供大卡分切／規劃判定關聯
- 07-11 執行 by Claude-Opus-4.8@ClaudeCode：TASKS.md 拆 Ledger 索引 + tasks/*.md；§7/§6.4 + templates 同步
- 07-11 查核 by ruan6047 → ✅ sign-off → 直接 merge main → 🏁完成
