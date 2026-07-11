# WF-8 導入「一卡一檔」慣例（狀態單一來源＝Ledger、封存用 git mv）  〔🔴紅線：改 canonical §6.3/6.4/7/7.1〕

- 需求：ruan6047　規劃：ruan6047 + Claude-Opus-4.8@ClaudeCode　分支：`ai/Claude-Opus-4.8@ClaudeCode/WF-8`
- 執行：Claude-Opus-4.8@ClaudeCode　查核：ruan6047（sign-off，紅線人審；執行者不自審）
- 範圍：於此簡述（無獨立 spec；需求全文見本次派工訊息）——
  - `TASKS.md`＝Ledger 索引 only + 依賴註記；卡明細一卡一檔 `tasks/<卡ID>.md`（**卡檔不設狀態欄**，狀態住 Ledger）
  - 封存改回 `git mv → archive/tasks/` + 抽 Ledger 列到 `archive/TASKS_ARCHIVE.md`（修訂 WF-7「不封存」）
  - canonical §6.3/§6.4(+§6.4.1 遷移指南)/§7/§7.1 改寫；`templates/TASKS.md` 瘦身 + 新增 `templates/tasks-card.md`
- 狀態：見 [`../TASKS_ARCHIVE.md`](../TASKS_ARCHIVE.md)（已封存 🏁，merge a8bbbcc）

## Log
- 07-11 需求 by ruan6047：Log 累積使單檔 TASKS.md 膨脹（§6.4 反例）→ 導入一卡一檔：常駐只讀輕量 Ledger、卡明細按需載入
- 07-11 執行 by Claude-Opus-4.8@ClaudeCode：
  - WF-1~7 `git mv` 進 `archive/tasks/` 並正規化為新卡格式（去狀態欄、加範圍、狀態指標指向封存 Ledger）
  - 建 `archive/TASKS_ARCHIVE.md`（封存 Ledger）；`TASKS.md` 瘦身為活卡 Ledger + 依賴註記
  - canonical §6.3/§6.4/§6.4.1/§7/§7.1 改寫；templates 兩檔就位
  - 決策：相關性採 Ledger「依賴註記」（非卡內 `[[]]`）——WF-7 的卡內相關任務欄由本卡修訂（ruan6047「無方向、由執行者推薦」）
- 07-11 查核 by ruan6047 → ✅ sign-off（紅線人審）→ merge main（a8bbbcc）→ 🏁完成
