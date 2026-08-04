# WF-22-CLI1 祕書 CLI 最小集〔T3；🟡流程〕

- 需求：ruan6047（2026-08-04 Wave 1 派工批准：「批准兩張」）　規劃：Claude Fable 5@Claude Code（PM 祕書）
- 執行：待指派（建議 L2；gh CLI 包裝與 git 對帳，已知模式）　查核：待指派（新 context；≠ 執行）
- Initiative：WF-22　spec 基線：決議 v1　db_scope: none
- 服務的原始目標：決議 1「祕書單寫入通道」的機械化——儀式不再靠人肉紀律
- 分支：本 repo `ai/<執行者>/WF-22-CLI1`

## 核心痛點（三問，需求方已批）

- **痛點**：機械寫入無單一通道，儀式靠人肉紀律——結案債曾一次積 9 張、事件漏寫、worktree 孤兒無人發現。
- **成功怎麼觀察**：五指令在 cpbl-analytics 真跑通；`doctor` 列出現存已知 3 個孤兒 worktree（`gate3-shadow-obs`、`website-naming-homepage-redesign-88e250`、`adoring-taussig-0d71cb`）。
- **最大未驗證前提**：欄位寫入結構依 `OPS-STATE-PLANE-MIG1` Task 1 定案——該前提未凍結前，`assign`／`handoff` 只能做介面骨架。

## 範圍

本 repo 新增 `cli/`（Python + uv，與既有生態一致；跨專案以 `--repo`／設定檔指定目標）：

1. `open`：依範本開卡（Issue＋git spec 檔骨架；必填欄位機械檢查——核心痛點、服務的原始目標、tier、db_scope、資源宣告）。
2. `assign`：派工（寫 owner／worktree 註冊欄；寫入集交集檢查，撞則拒絕並列出衝突卡）。
3. `handoff`：交接（狀態轉換＋source SHA＋證據欄必填）。
4. `doctor`：對帳（`git worktree list` vs 卡註冊、submodule 未初始化、殘留 lease、孤兒分支、prunable worktree）。
5. `snapshot`：狀態面每日快照 export 回 git（JSON＋人類可讀 Ledger 渲染）。

## 依賴與順序

- `doctor`／`snapshot` 骨架不依賴 Issues 結構，可立即先行。
- `open`／`assign`／`handoff` 的欄位寫入待 `OPS-STATE-PLANE-MIG1` Task 1 結構凍結（阻塞發現協定：結構不足以表達時回報 PM，不得自行改結構）。

## 紅線

1. CLI 是唯一寫入通道的載體：文件必須明示「不經 CLI 的狀態寫入即違規」，但 CLI 本身不做權限強制（單機信任模型，由治理承擔）。
2. 不做 GUI、不做 webhook、不做常駐服務——最小集只有五指令。
3. 破壞性操作（lease 回收、worktree 清理）必須先列清單再執行，且未提交變更一律不刪（canonical §4.1 既有規則）。

## 驗收

- [ ] 五指令在 cpbl-analytics 實際跑通各一次，輸出入文件。
- [ ] `doctor` 於 cpbl 找出上列 3 個已知孤兒（紅→綠證據：先跑出 3 筆，清理批准後複跑歸零）。
- [ ] `snapshot` 輸出能重現遷移後狀態面的全部欄位。
- [ ] `uv run pytest`（本 repo 新增測試）通過。

## Log

- 2026-08-04 register by Claude Fable 5@Claude Code（PM 祕書，依需求方批准）；Backlog。
