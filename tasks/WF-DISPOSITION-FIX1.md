# WF-DISPOSITION-FIX1 已登記的發現與排隊中的工作用同一個物件、動詞與清單，且預設視圖上完全一樣　〔T2〕

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
- 執行：Claude Opus 5@Claude Code　查核：待指派
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：看板上的數字要等於真實的待辦，且發現與工作要分得出來
- owner、worktree、iteration、交付／部署狀態、最後交接、資源宣告與 Log
  current-state 見對應 GitHub Issue／Project item（卡ID：WF-DISPOSITION-FIX1），不重複於此檔。

## 核心痛點

- **痛點**：gh issue list 顯示 26、GitHub 首頁顯示 26，只有打開 Project 讀交付狀態欄才看得出 21 張是 Backlog——看到的數字是 26，真實待辦接近 0

## 驗收條件

- [ ] git grep 決策佇列 = 0；保留的每一處佇列字樣須為否定語且說明理由
- [ ] templates/project-stub.md 的改動能被採用專案讀懂——它是傳遞介面，失真會複製到每個採用專案而採用專案不會知道自己收到的是失真版本。交付須貼出改動後全文
- [ ] BUGS.md 廢止後，四處引用全為公告而非路由
- [ ] registered-finding 的漂移自承須按 canonical 既有格式寫入：它是交付狀態欄的投影、兩者可漂移、偵測該漂移的 #65 已規格化但尚未執行——不得寫得像已經有守衛

## 驗證

- [ ] 該 repo 既有測試（cli/ pytest 879 passed）＋ CI 綠於交付 SHA
