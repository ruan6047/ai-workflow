# #7 WF-22-CANON1 Wave 2：13 決議＋實戰教訓寫入 canonical 正文（WF-22 子卡）
- state: closed  created: 2026-08-05T10:08:11Z  closed: 2026-08-05T14:34:22Z
- url: https://github.com/ruan6047/ai-workflow/issues/7
- comments: 5

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
- 執行：待指派　查核：待指派
- Initiative：WF-22　spec 基線：父卡 WF-22（tasks/WF-22.md）＋cpbl docs/research/WORKFLOW-REVIEW-2026-08-04.md（a8f6f4c）
- DB：db_scope=none
- 服務的原始目標：治理規則單一事實來源——任何家族任何專案的 AI читая canonical 即可正確運作

## 簡介
<!-- card-brief:begin -->
把 2026-08-04 工作流總檢討的 13 項決議與其後兩天的實戰修訂寫成 canonical AI_WORKFLOW.md v2 正文——治理層級、一根問題一張卡、開卡三條件、資源交集＋lease、三級閘門、鏈式停損、查核第一判準、狀態面＋wfcli、worktree 註冊、多專案層——另成文派工包標準條款與跨家族查核範式，並依 OPS-CODE-BRANCH-PROTECT1 實證修掉 §2.2 與 §0 的自相矛盾。**適用時機**：要查某條治理規則的成文出處與裁決來源時；或新專案要接 canonical、需知道 v2 涵蓋哪些條款時。⛔ 非射程：不新增規則、只成文既有裁決，新增裁量須標記交需求方；規則的機械強制不在本卡——review 寫入通道屬 WF-22-CLI3（aiwf#8）、escalation 計數屬 WF-22-CLI4（aiwf#9）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：13 項決議與兩天實戰修訂（派工條款、查核範式、資源護欄語意、收尾檢查表）散在 cpbl 決議文件、Issues 留言與 PM session 記憶——新 session/新專案無 canonical 正文可循，且 §2.2 與 §0 已知自相矛盾

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:AI_WORKFLOW.md",
    "file:templates/",
    "file:tasks/WF-22-CANON1.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 13 項決議全數成文入 canonical（治理/一根問題一張卡/開卡三條件/資源交集+lease/三級閘門/鏈式停損/查核第一判準/狀態面+wfcli/worktree 註冊/多專案層），逐條可追溯到決議文件
- [ ] 派工包標準條款成文（含 trailer 連續區塊、停等背景禁令、update-branch 禁令、詭異數據人工判讀+新聞通道、spawn_task 禁令）
- [ ] 跨家族查核範式成文：結構化輸出+self_run 必填、R2 收斂範圍、跨 repo 證據=絕對路徑+釘SHA+碼段摘錄、查核環境紅線模板
- [ ] §2.2 與 §0 矛盾修正：依 OPS-CODE-BRANCH-PROTECT1 實證改寫（rulesets history-guard 為標準、required checks 不適用直推流）
- [ ] 營運教訓成文：merge 後資源宣告釋放與板狀態收尾檢查表（📦已合併仍佔活卡）、消費者盤點含 shell stdout 用點、完整性宣稱自動化產生
- [ ] cpbl 端 stub（docs/AI_WORKFLOW.md）與 templates/ 同步校讀，無殘留舊制敘述

## 驗證

- [ ] 查核＝逐條決議溯源比對＋與現行實務（Issues #83/#90-93 留痕）零矛盾；不新增規則、只成文既有裁決——新增裁量須標記交需求方
## Log

- 2026-08-05T18:08:09+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-05T18:09:04+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree ai/opus-5/WF-22-CANON1 @ .claude/worktrees/wf-22-canon1-execution；交付狀態 🚧進行中。
- 2026-08-05T21:59:02+08:00 handoff by wf-cli → owner Codex（跨家族查核）；iteration 0；SHA c853ed930210e5b1825091000bd2385f04f15b83；證據 canonical v2 全交付：27 項溯源全命中＋雙層樹機械驗證＋116 tests；詳 Issue #7。
- 2026-08-05T22:22:43+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（執行者）；iteration 1；SHA c853ed930210e5b1825091000bd2385f04f15b83；證據 Codex R1：1 major（四約束無源）→需求方追認為正式裁決（#7 留言）；補源頭引用即可。
- 2026-08-05T22:28:35+08:00 handoff by wf-cli → owner Codex（跨家族查核 R2）；iteration 1；SHA 4cb279c51aa6eec5812a7e05d7a57b0ee0e52d78；證據 R1-01 修復：條文不動＋溯源補 #7 追認；單行 diff；詳 #7 修復留言。
- 2026-08-05T22:34:32+08:00 handoff by wf-cli → owner ruan6047；iteration 1；SHA 4cb279c51aa6eec5812a7e05d7a57b0ee0e52d78；證據 merged d99a8ad＋#7 closed；canonical v2 生效。
- 2026-08-26T21:54:46+08:00 amend by wf-cli（op 9c5bb134）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:dc211e6c5ce762c24ad6d6efbb9efde95cd49fc8e781a9ca0d4c93c28ee26fe3 (821 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5192617303 · 2026-08-05T13:51:02Z

## 需求方裁決（2026-08-05，PM 落帳）

交付 `2033807` 的 10 項待裁決結果：
- **1/2/5/7（推論型四項）**：全部照執行者處理確認——決議 9/10/12 留父卡不入通則；Coordinator＝PM 祕書同一角色；core_pain_resolved:no→attribution:planner；required checks 條件式措辭。
- **3 snapshot 頻率**：每日通則，維持現寫。
- **4 §4.2/§4.4**：維持共存（資源互斥層 vs DB 契約層，scope 不同）。
- **6 wfcli review 子命令**：核准開卡（WF-22-CLI3，Backlog 排程後執行）。
- **8 Log 段**：狀態面以 Issue/wfcli 事件為準，卡檔留白正確。
- **9/10 ADOPTION/README**：**擴寫入集退執行者補**（含 README 範本樹既有 7 檔缺口一併補）。
- **cpbl stub 五點**：待決（merge 授權時併決）。

執行者續作 ADOPTION/README 後送跨家族查核。

## Comment 5192710001 · 2026-08-05T13:58:52Z

## 交付定稿（2026-08-05）

最終 SHA `c853ed930210e5b1825091000bd2385f04f15b83`（五 commit：新範本→canonical 正文→templates 同步→ADOPTION＋範本樹→root 樹；基準 21746ee，歷史無改寫）。cli 116 tests 綠、相對連結 0 破損、trailers 全解析。

- canonical 169→260 行：13 決議＋六條派工條款＋查核範式＋資源宣告生命週期＋結案七步＋§2.2 依 #83 改寫；27 項溯源檢查指令產生全命中。
- templates 新 2 改 8；ADOPTION §4 補派工/派審引用；README root 13＋templates 18 雙層樹機械驗證（set+order equal、雙向差集空）。
- 一項自行判斷入 commit body：README 自列（「雙向差集為空」標準的必然結果）——交查核者確認。
- 維持待決：cpbl stub 五點（merge 授權時需求方併決）。

狀態：🔍待查核。

## Comment 5192994482 · 2026-08-05T14:22:32Z

## 🔍 跨家族查核 R1（Codex）：REQUEST_CHANGES（2026-08-05）＋需求方追認裁決

- core_pain_resolved: yes。逐段正反向溯源：其餘全部規範可對回 13 決議／#7 已核推論／#83／#90-93 留痕；§2.2 舊禁句 0 命中；雙層樹、連結、116 tests、五 commit trailers 全複驗通過。
- **CANON1-R1-01（major，blocking）**：新聞佐證通道的四約束（僅定性／官方數值權威／URL＋日期／第三方泛化）於 AI_WORKFLOW.md:230、dispatch-package.md:32、project-stub.md:28 無書面裁決源頭——實為 PM 對需求方口頭裁定的操作化，僅存 session 記憶。**反向溯源機制首次命中真實無源條文。**

**⚖️ 需求方追認裁決（2026-08-05）**：四約束**追認為正式裁決**（實戰已驗證：連段語意翻案即依此邊界執行——媒體報導佐證定性、官方紀錄榜裁定數值）。本留言即權威源頭。

處置：退回 implementation（iteration+1）——條文保留，補源頭引用（本留言）至溯源鏈；modifications 極小。

## Comment 5193062981 · 2026-08-05T14:28:25Z

## 🔧 R1 修復交付（2026-08-05，執行者）

最終 SHA `4cb279c51aa6eec5812a7e05d7a57b0ee0e52d78`（單 commit、`git diff --numstat`＝AI_WORKFLOW.md 1/1）。

- **CANON1-R1-01 修法**：條文一字不動（三處內容雜湊 pre==post 機械證明），canonical 第 5 行基線註記補溯源——四約束源頭＝本 Issue 2026-08-05 需求方追認留言（明注不在 2026-08-04 決議文件內），實戰依據 cpbl #90/#89。溯源檢查 27→29 項、命中 28（唯一 MISS 為刪除句的期望值）。
- 自我更正：初版誤加 `Reviewed-by: Codex`（修復 commit 尚未受審），推送前 --amend 移除，remote 無誤植版本。
- cli 116 tests 綠、trailer 四行全解析。

狀態：🔍待查核（R2，範圍＝R1-01 閉環）。

## Comment 5193134609 · 2026-08-05T14:34:20Z

## ✅ 已 merge 結案（2026-08-05，需求方授權）

canonical v2 merge `d99a8ad`（Reviewed-by: Codex）；cli 116 tests 複驗綠；worktree 與分支已清理。cpbl stub 五點由 PM 直修＋submodule 同步（需求方裁決）。Wave 2 完結，WF-22 父卡同步更新。
