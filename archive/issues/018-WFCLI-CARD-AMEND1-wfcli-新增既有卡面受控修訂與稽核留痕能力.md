# #18 WFCLI-CARD-AMEND1 wfcli 新增既有卡面受控修訂與稽核留痕能力
- state: closed  created: 2026-08-10T10:31:21Z  closed: 2026-08-10T10:32:44Z
- url: https://github.com/ruan6047/ai-workflow/issues/18
- comments: 1

## Body

- 需求：ruan6047　規劃：GPT-5@Codex
- 執行：待指派　查核：獨立校讀
- Initiative：—　spec 基線：需求方 2026-08-10 對 ai-workflow#17 的 break-glass 裁決；canonical AI_WORKFLOW.md §4.3 單一寫入通道；ai-workflow#12 僅處理 tier 更正。
- DB：db_scope=none
- 服務的原始目標：讓需求方已核可的既有卡面修訂能透過 wfcli 完成，保留可驗證的前後版本與裁決依據，且不改變未授權的 Project 或 lifecycle 狀態。

## 核心痛點

- **痛點**：wfcli 沒有既有真實 Issue 卡面的受控修訂命令，導致必要的格式或基線修正只能直接 gh issue edit，繞過單一寫入通道、缺少機械驗證與不可覆寫的修訂稽核。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/cli.py",
    "file:cli/src/wf_cli/commands/amend_card_cmd.py",
    "file:cli/src/wf_cli/project.py",
    "file:cli/tests/test_commands_mocked.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 提供 wfcli amend-card；真實 Issue 卡只能透過此命令改 body，draft Issue 路徑亦明確處理，不得要求手動 Project UI 或直接 gh issue edit。
- [ ] 每次修訂必填需求方裁決 URL 與理由，並在 Issue timeline 追加 append-only 紀錄：card_id、操作者、修訂前後 SHA-256、變更範圍與時間。
- [ ] 命令須先讀取現行 body、驗證固定章節與 resource-claims JSON；輸入基於舊版本失效時 fail closed，不得覆蓋併發修訂。
- [ ] 修訂 body 不得改變 Project 欄位或 lifecycle 狀態；若要做狀態轉換仍只能走既有 assign、handoff、review、deploy 命令。
- [ ] 新增命令的單元測試涵蓋成功、缺裁決依據、資源宣告失效、舊 body 版本衝突及遠端部分失敗；既有測試不得退步。

## 驗證

- [ ] 於 throwaway 真實 repo Issue 驗證 timeline 稽核紀錄、前後 body digest 與 Project 欄位完全不變，測後清除或還原測試卡。
- [ ] 執行 cli 全套測試，並以獨立查核重算 timeline 的前後 SHA-256 與變更範圍。

## Log

- 2026-08-10T18:31:20+08:00 open by GPT-5@Codex；owner 待指派；iteration 0。


## Comment 5239000874 · 2026-08-10T10:32:44Z

依需求方 2026-08-10 裁決：撤回本次由 GPT-5@Codex 建立的 WFCLI-CARD-AMEND1，交回原先執行者處理。未實作、未認領、未改動任何程式碼。
