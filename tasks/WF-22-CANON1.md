# WF-22-CANON1 Wave 2：13 決議＋實戰教訓寫入 canonical 正文（WF-22 子卡）　〔T3〕

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
- 執行：待指派　查核：待指派
- Initiative：WF-22　spec 基線：父卡 WF-22（tasks/WF-22.md）＋cpbl docs/research/WORKFLOW-REVIEW-2026-08-04.md（a8f6f4c）
- DB：db_scope=none
- 服務的原始目標：治理規則單一事實來源——任何家族任何專案的 AI читая canonical 即可正確運作
- owner、worktree、iteration、交付／部署狀態、最後交接、資源宣告與 Log
  current-state 見對應 GitHub Issue／Project item（卡ID：WF-22-CANON1），不重複於此檔。

## 核心痛點

- **痛點**：13 項決議與兩天實戰修訂（派工條款、查核範式、資源護欄語意、收尾檢查表）散在 cpbl 決議文件、Issues 留言與 PM session 記憶——新 session/新專案無 canonical 正文可循，且 §2.2 與 §0 已知自相矛盾

## 驗收條件

- [ ] 13 項決議全數成文入 canonical（治理/一根問題一張卡/開卡三條件/資源交集+lease/三級閘門/鏈式停損/查核第一判準/狀態面+wfcli/worktree 註冊/多專案層），逐條可追溯到決議文件
- [ ] 派工包標準條款成文（含 trailer 連續區塊、停等背景禁令、update-branch 禁令、詭異數據人工判讀+新聞通道、spawn_task 禁令）
- [ ] 跨家族查核範式成文：結構化輸出+self_run 必填、R2 收斂範圍、跨 repo 證據=絕對路徑+釘SHA+碼段摘錄、查核環境紅線模板
- [ ] §2.2 與 §0 矛盾修正：依 OPS-CODE-BRANCH-PROTECT1 實證改寫（rulesets history-guard 為標準、required checks 不適用直推流）
- [ ] 營運教訓成文：merge 後資源宣告釋放與板狀態收尾檢查表（📦已合併仍佔活卡）、消費者盤點含 shell stdout 用點、完整性宣稱自動化產生
- [ ] cpbl 端 stub（docs/AI_WORKFLOW.md）與 templates/ 同步校讀，無殘留舊制敘述

## 驗證

- [ ] 查核＝逐條決議溯源比對＋與現行實務（Issues #83/#90-93 留痕）零矛盾；不新增規則、只成文既有裁決——新增裁量須標記交需求方
