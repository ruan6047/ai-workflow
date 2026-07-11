# WF-9 BUG 處理線（快線/慢線）+ bug 卡範本 + BUGS.md  〔🔴紅線：改 canonical §2.1〕

- 需求：ruan6047　規劃：ruan6047 + Claude-Opus-4.8@ClaudeCode　分支：`ai/Claude-Opus-4.8@ClaudeCode/WF-9`
- 執行：Claude-Opus-4.8@ClaudeCode　查核：ruan6047（sign-off，紅線人審；執行者不自審）
- 範圍：於此簡述（無獨立 spec）——
  - canonical §2.1 新增「BUG 處理線」：快線（根因已知＋局部 → 免開卡、`fix/<slug>`、先紅後綠回歸測試 → 審核一次 → merge、痕跡＝trailer + BUGS.md 一行）／慢線（開 bug 卡走完整四階段）
  - 原則：**分支＋審核不可省，只省規劃＋開卡**；回歸測試＝修復的一部分（承 §9.3）
  - 新增 `templates/bug-card.md`（bug 卡範本）、`BUGS.md`（快線滾動 log）；§0.1 A 列加指標；ADOPTION 補 BUGS.md
- 狀態：見 [`../TASKS.md`](../TASKS.md) Ledger

## Log
- 07-11 需求 by ruan6047：現行一卡一檔處理 bug 覺得麻煩，問建議
- 07-11 規劃 by ruan6047 + Claude-Opus-4.8@ClaudeCode：拆「安全成本(不砍)vs簿記成本(可砍)」；選項確認——快線仍強制一次審核、痕跡走 BUGS.md rolling log、落實為 WF-9
- 07-11 執行 by Claude-Opus-4.8@ClaudeCode：canonical §2.1 + §0.1 指標；新增 templates/bug-card.md、BUGS.md；ADOPTION 補
