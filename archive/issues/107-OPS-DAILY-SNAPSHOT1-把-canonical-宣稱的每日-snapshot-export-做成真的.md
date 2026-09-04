# #107 OPS-DAILY-SNAPSHOT1 把 canonical 宣稱的每日 snapshot export 做成真的
- state: closed  created: 2026-08-18T21:48:12Z  closed: 2026-08-19T05:38:14Z
- url: https://github.com/ruan6047/ai-workflow/issues/107
- comments: 6

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 經濟型；答案唯一：wfcli snapshot 已存在（snapshot_cmd.py 寫 snapshot.json+SNAPSHOT.md），缺的只是排程與 commit 落點；沿用本機既有每日 launchd 鏈模式）　查核：待指派（建議 主力型；查核重點是證據不是碼：排程真的在跑的證明必須是連續日曆日的產物，不得人工聲明——本 repo 有排程宣稱與現實脫節的前科（週跑 plist 刻意不裝、snapshot 15 天零產出））
- Initiative：—　spec 基線：ai-workflow ae8f74162797e2eed7180a1cd1ed6692fab3b6d3 的 AI_WORKFLOW.md:138/:164；C 輪對帳報告（2026-08-19）
- DB：db_scope=none
- 服務的原始目標：事件流的離線稽核副本要真的每天存在，否則 canonical 必須改口承認沒有

## 簡介
<!-- card-brief:begin -->
把 `wfcli snapshot` 掛上每日排程、產物 commit 進 `snapshots/`——canonical `AI_WORKFLOW.md:138`／`:164` 逐字宣稱這是「用 Issues 當事件流」的全部補償控制，而實測整條事件流 15 天沒有任何離線稽核副本。**適用時機**：要對事件流做離線稽核、或要判斷某個「排程在跑」的宣稱是否與現實脫節時。⛔ 非射程：不改事件流本身的寫入通道、也不改 `wfcli snapshot` 的實作（`snapshot_cmd.py` 已存在，本卡缺的只是排程與 commit 落點）；不得以單次手跑或人工聲明代替「連續兩個日曆日兩筆 commit」的證據。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：AI_WORKFLOW.md:138 逐字「因其非嚴格不可覆寫，必須以每日 snapshot export 回 git 建立離線稽核副本」、:164 同義——這是「用 Issues 當事件流」的全部補償控制。實測（2026-08-19）：兩 repo 追蹤檔零 snapshot 產物、.github/workflows 無 schedule、cpbl docs/control-plane 末次 commit 2026-08-04（cutover 當日）。整條事件流 15 天沒有任何離線稽核副本，而 canonical 讀起來像它有

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:snapshots/",
    "file:scripts/daily_snapshot.sh"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 每日一次 wfcli snapshot，產物（snapshot.json＋SNAPSHOT.md）commit 進本 repo snapshots/ 目錄（檔名含日期或以覆寫+git 歷史留版本，擇一寫死）。排程掛本機既有每日 launchd 鏈（與 cpbl 10:10 爬蟲鏈同模式）或獨立 plist，擇一寫死並留安裝受據
- [ ] ⚠️ 「排程在跑」的證據＝連續兩個日曆日的兩筆 commit（不同日期、內容反映當日板面），不得以單次手跑或人工聲明代替。推翻條件：兩筆 commit 時間戳同日，或第二筆是手動補跑
- [ ] canonical 宣稱與實作對齊：AI_WORKFLOW.md:138/:164 的措辭若與實際落點/頻率不同，同 PR 更正文件；不得留下第二個「文件說有、機器上沒有」

## 驗證

- [ ] launchctl 註冊受據＋第一筆真實產物的 commit；snapshot 消耗 **6 個 GraphQL requests/次**（實測；隨卡數成長，list_items 每 50 張多一頁），於卡面記錄。⚠️ 卡面原寫「2 點/日」為 coordinator 開卡時的錯誤估計，依 R1-03（attribution: coordinator）更正——執行者與 PM 各自獨立以 gh api rate_limit 前後差實測皆得 6
## Log

- 2026-08-19T05:48:11+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-19T11:03:21+08:00 assign by wf-cli → owner Claude Fable 5@Claude Code 子agent；分支worktree claude/daily-snapshot-107 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/daily-snapshot-107；交付狀態 🔨執行中；實際能力層級 高階型（偏離卡面建議 經濟型；偏離理由：卡面建議經濟型；向上偏離：繼承本會話子代理模型 Claude Fable 5（MODEL_ROUTING L3 等價）；為單張卡另起低階模型的協調成本高於能力差價，射程不因層級擴大。）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-19T11:32:07+08:00 handoff by wf-cli → owner 待指派；iteration 0；SHA f04c29251b179c958fe7cf654a95fbecfccc6dff；證據 執行交付（2026-08-19）：分支 claude/daily-snapshot-107（三 commit），恰兩檔＝資源宣告（scripts/daily_snapshot.sh +342、snapshots/README.md +67），worktree 保留。PM 複驗三項全部重現：origin/snapshots 孤兒分支存在 @ 8fda3e0（README＋snapshots/2026-08-19/{snapshot.json,SNAPSHOT.md}）、launchctl list 有 com.wf.daily-snapshot、⚠️ **wfcli snapshot 一次實測消耗 6 個 graphql requests 不是卡面寫的 2 點**（PM 自跑 rate_limit 前後差確認）——卡面數字錯，屬 coordinator，待裁決後 amend。⚠️ 驗收條 2 **明確未成立且執行者未以單次手跑充數**：現況只有 1 筆產物且 trigger 標為 launchd-selftest（kickstart 觸發非日曆觸發，字串刻意區分）。執行者給了可證偽的預先登記：merge 後第二天與第三天 10:40±數分應各出現一筆 trigger: launchd 的 commit、目錄名為當日日期；出現 trigger: manual、兩筆同日或目錄跳號即判排程沒跑。⚠️ 驗收條 3 未執行，卡在授權（AI_WORKFLOW.md 不在資源宣告內，執行者未動），且它揭露一層更嚴重的差距：wfcli snapshot 匯出的是**看板當前狀態**（13 個凍結欄位＋卡面資源宣告），**不含 Issue timeline 上的 lifecycle event 留言**——被事後編輯或刪除的結構化 comment 這份快照偵測不到，而 canonical :138 逐字要的是「事件流」的離線稽核副本。本卡只做到「狀態面」那一半，執行者已寫進 README 與 commit 訊息未包裝成已解決。⚠️ 查核第一題：**落點是孤兒分支 snapshots 而非 main，是執行者自主決定且卡面沒預期**。理由是 ruleset 20768920 對 default branch 要求 status check、strict=true、bypass_actors 空，無人值守直推過不去；allow_auto_merge=false 故走 PR 需機器自行 merge（治理違規）。⚠️ 該前提**未實測**（實測需往 main 推一筆，派工明令不碰 main），旁證只有 ruleset 設定值＋生效後 main 每筆 commit 都掛得到 PR。此決定與『新開遠端分支不在 file:snapshots/ 字面內』的寫入集問題，請一併裁決。其他自報：10:40 日曆觸發本身未驗（只驗 kickstart）、睡眠/關機補跑未驗、跨日產生不同目錄是用 date shim 模擬非真跨日、snapshots 分支未來可能被 cleanup 誤判為可清理的孤兒分支。驗證：trailer 守衛實測有跑到（doctor --commit-trailers 違規 0/合規 3）、pytest 1009 passed、escalation replay 65/65。。
- 2026-08-19T12:25:23+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 Google DeepMind Antigravity；core_pain_resolved yes；self_run 6 項；findings 3 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt OPS-DAILY-SNAPSHOT1-e0-f04c29251b179c958fe7cf654a95fbecfccc6dff。
- 2026-08-19T12:29:50+08:00 amend by wf-cli（op 7f45ceb2）→ 驗證：原值「[ ] launchctl 註冊受據＋第一筆真實產物的 commit；snapshot 消耗 GraphQL 2 點/日，於卡面記錄」→ 新值「launchctl 註冊受據＋第一筆真實產物的 commit；snapshot 消耗 **6 個 GraphQL requests/次**（實測；隨卡數成長，list_items 每 50 張多一頁），於卡面記錄。⚠️ 卡面原寫「2 點/日」為 coordinator 開卡時的錯誤估計，依 R1-03（attribution: coordinator）更正——執行者與 PM 各自獨立以 gh api rate_limit 前後差實測皆得 6」；理由 依 R1 裁決 finding OPS-DAILY-SNAPSHOT1-R1-03（severity info，attribution: coordinator）執行 disposition：卡面驗證項的 GraphQL 成本由「2 點/日」更正為實測「6 requests/次」。該數字是我開卡時憑印象寫的估計而非量測，執行者於 snapshots/README.md:66 記載實測值、PM 亦獨立以 gh api rate_limit 前後差複驗得 6，兩者一致。⚠️ 這是我今日第五次同族錯誤（對工具行為以未經量測的單一印象下定論），與 item-list 不含 body、技能欄、標題全形冒號、cleanup catch-22 機制歸因同形。其餘驗證項未變。。
- 2026-08-19T12:30:44+08:00 handoff by wf-cli → owner Claude Fable 5@Claude Code 子agent；iteration 1；SHA f04c29251b179c958fe7cf654a95fbecfccc6dff；證據 R1 REQUEST_CHANGES 後交回執行者（2026-08-19）：唯一 blocking 是 R1-01（attribution: executor）——scripts/daily_snapshot.sh 內緊鄰全形括號的未加花括號變數展開，在 set -uo pipefail 下觸發 unbound variable。受影響 5 行：231／245／263／270／336，⚠️ 其中 4 行在 die() 錯誤回報路徑上，即錯誤處理本身會二次崩潰。⭐ PM 補正機制敘述並已寫進裁決：查核者原寫「全形括號在 bash 3.2 下為合法識別符字元」，PM 第一次重現失敗（rc=0，因 PM shell 的 LANG/LC_ALL 皆 unset 等同 C locale），逐 locale 實測後確認為 **locale 依賴**——LC_ALL=C rc=0、LC_ALL=zh_TW.UTF-8 與 en_US.UTF-8 皆 rc=127。本機 shebang #!/usr/bin/env bash 解析至 /bin/bash 3.2.57，機器上無其他 bash。此缺陷與 docs/ROADMAP.md:144-148 記錄的 locale 陷阱同族。非 blocking 兩條由 PM 承接：R1-03（GraphQL 成本 2→6）已於 op 7f45ceb2 amend 完成；R1-02（canonical 邊界）另處理。。
- 2026-08-19T12:44:25+08:00 handoff by wf-cli → owner 待指派；iteration 1；SHA b03f4e441c27d429ea82aae22dd8857d5d1e18fb；證據 R1-01 閉環交付（2026-08-19）：commit b03f4e4 快進於 f04c292，兩檔（daily_snapshot.sh +32/-6、snapshots/README.md +39）皆在資源宣告內，trailer 4 行，worktree 保留。⭐ 執行者把問題的形狀改對了：查核者與 PM 都把它敘述成「全形括號」，執行者逐一實測 0x80–0xFF 全部 128 個 byte，**65 個**會被 bash 3.2 在 UTF-8 locale 下吃進變數名（涵蓋 0xC2–0xEF 全部 CJK/全形 lead byte）——**這不是全形括號的個案，是任何中文字**。PM 獨立複驗確認： 緊鄰「（」「本」「，」「。」四者全部 CRASH。判準因此由「5 行的位置表」改為封閉集合 regex（未加花括號的具名展開緊鄰任何 byte ≥ 0x80），掃描器命中 7 處比查核者列的 5 行多兩處（第 65 行在 quoted heredoc 內屬惰性、第 231 行同行兩處），全部修掉；同行的  後接 ASCII 空白未動（正確）。PM 複驗：全檔掃描 0 處、植入壞形變異報 1 處（守衛非零資訊）。取證：修前 zh_TW.UTF-8 下 5 條全紅且離開碼由 69/75/78/79 退化成 1；修後三 locale（zh_TW/en_US/C）各 5/5 PASS、離開碼回復。⭐ 執行者另發現附帶損害並取證：二次崩潰時 write_status 不執行 → last-status.json 整份不存在，最需要診斷的那一刻沒有任何紀錄。locale 固定與否選「不固定」，理由是固定 C 等於把地雷埋回驗不出來的一側（即 ROADMAP 那段「把偵測器調成永遠不會響」）。⚠️ 執行者自報三項要 R2 注意：(a) **此缺陷族 CI 抓不到且現在仍抓不到**——CI 已釘 LC_ALL=C.UTF-8（故任務書引用的 ROADMAP:144-148 已被該 workflow env 取代），但 grep 全庫 py 檔對 daily_snapshot 零命中、pytest testpaths 只收 cli/tests，沒有任何 CI 步驟執行這支腳本；守衛與煙霧測試目前只有文件無機器執行，修不了是因為新增測試檔超出資源宣告；(b) 煙霧測試採等價機制（跑一次取證＋可重現程序寫進 README），harness 留在 scratchpad 不隨 commit 進 repo，R2 需照 README 表格重建；(c) rc 與 PM 敘述不符——PM 記 rc=127、執行者實測一律 rc=1，呼叫方式不同所致，未追。另：執行者自陳寫註解時把原形寫進去被守衛當場抓到，反證守衛有效。R2 範圍依 review-prompt §6 只做 R1-01 閉環＋回歸不倒退：全檔掃描=0、變異=1、三 locale 煙霧 5/5、pytest 1009 不倒退。。
- 2026-08-19T13:14:16+08:00 review by wf-cli → APPROVE（✅通過）；查核者 Google DeepMind Antigravity；core_pain_resolved yes；self_run 5 項；findings 1 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt OPS-DAILY-SNAPSHOT1-e0-b03f4e441c27d429ea82aae22dd8857d5d1e18fb。
- 2026-08-19T13:38:02+08:00 handoff by wf-cli → owner —（已合併）；iteration 1；SHA ae863062c06401c81661674f7cca657ac9612816；證據 release（2026-08-19）：R1 REQUEST_CHANGES → R2 APPROVE（Google DeepMind Antigravity，跨家族）後合併。被審 b03f4e4 rebase 至 2da0edc 上為 ae86306，內容保真＝diff 中只有 cleanup.py／test_cleanup.py／doctor.py／test_doctor.py／ROADMAP（rebase 帶進的 #106／#109／#110），**被審的 daily_snapshot.sh 與 snapshots/README.md 不在 diff 中即逐位元未動**；PR #113 兩 check 皆 pass 後 squash merge → main ddb78cc。⭐ merge 後在**合併結果的 blob 上**重跑守衛：perl 掃描命中 0 處（期望 0），腳本 362 行落地，launchd 指向的 /Users/ruanruan/Dev/ai-workflow/scripts/daily_snapshot.sh 現已存在（-rwxr-xr-x）。⚠️ **驗收條 2 的時鐘自本次 merge 開始走**：可證偽的預先登記為「2026-08-20 與 08-21 的 10:40±數分，origin/snapshots 應各出現一筆 trigger: launchd 的 commit，目錄名分別為當日日期」；出現 trigger: manual、兩筆同日、或目錄跳號即判排程沒跑。⚠️ 已知未涵蓋（R2 查核者判定執行者恪守資源宣告界線正確、屬獨立治理卡）：CI 無任何步驟執行此腳本，守衛與煙霧測試只有文件、無機器執行。⚠️ 本輪無 wf-review-receipt:v1 收據，留痕見 issuecomment-5337720319，機制缺口承接卡 #111。；收尾清理：已清除 worktree；遠端分支 本來就不存在；本地分支 依授權保留（未刪除）。
- 2026-08-26T14:16:50+08:00 amend by wf-cli（op 8c009ffb）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:46322d4452906bde78d34e51f2131ae0ad3a92a0abbdf72abb21145fbe5f7c68 (642 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第二批（20 張純隨機）：依 canonical §6.3 回填簡介；文字經 A5 守衛（分行字元＋1012B 上限）預先拒收檢查。


## Comment 5336995878 · 2026-08-19T03:04:47Z

## 派工包：`OPS-DAILY-SNAPSHOT1`（2026-08-19）

**基線** `4e6925e9fbdfd5c3ad715c63d2cb801cee63900a`（origin/main）
**分支／worktree** `claude/daily-snapshot-107` @ `/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/daily-snapshot-107`
**射程**：資源宣告是 `file:snapshots/` 與 `file:scripts/daily_snapshot.sh`。⚠️ 若實作需要改 `AI_WORKFLOW.md`（驗收條 3 的文件對齊），**先回報 PM 補宣告再動**——不得自行擴大寫入集。

### 事實（PM 已驗，別重查）

`wfcli snapshot` 已存在且會寫 `snapshot.json`＋`SNAPSHOT.md`（`snapshot_cmd.py:43-44`）。缺的是**排程與 commit 落點**。實測 2026-08-19：兩 repo 追蹤檔零 snapshot 產物（`git ls-files | grep -i snapshot` 命中全是原始碼或無關領域）、`.github/workflows/` 只有 `ci.yml` 無 schedule、cpbl `docs/control-plane/` 末次 commit 2026-08-04。

### 特別注意

- 驗收條 2 是**時間性證據**：連續兩個**日曆日**的兩筆 commit。你今天做不完這一條——**照實交付「已安裝、待第二日產物」並在報告寫明哪一條尚未成立**，不得以單次手跑充數（本專案有「排程宣稱與現實脫節」的前科：週跑 plist 刻意不裝、snapshot 15 天零產出）。
- 排程掛法：本機既有每日 launchd 鏈（cpbl 10:10 爬蟲鏈同模式）或獨立 plist，**擇一寫死**並留安裝受據（`launchctl list | grep` 之類）。
- `snapshots/` 目錄的檔名策略（含日期 vs 覆寫+git 歷史）也要**擇一寫死**，不要留兩種可能。

### 交付紀律（三張共通）

- ⚠️ 報告中凡「實測／窮舉／全庫／逐字／唯一／零命中」，同句數字與列舉必須附指令＋原始輸出，否則寫「未驗」。
- commit 帶 trailer 四件套（Requested-by: ruan6047／Planned-by: Claude Fable 5@Claude Code (PM)／Implemented-by: 你的 claim 身分／Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>）。⚠️ trailer 守衛在「分支無新 commit」時 skip——**先 commit 再跑 pytest**，否則它整場沉睡（本專案已踩過一次）。
- Conventional Commits；push 分支，**不碰 main、不 merge、不跑任何 wfcli 動詞**；worktree 保留給查核者。
- 報告必含：逐條驗收狀態與證據、**沒驗到的／未證實假設／失敗或不如預期**（不得省略）、受 5xx／配額影響項目（標 UNKNOWN，不得寫成 0 或不存在）。
- 工具坑：`gh project item-list --format json` 的中文欄位名首位元組壞成 U+FFFD（用 endswith 後綴比對）；**body 在 `content.body`**（不必走 REST）。ai-workflow 卡面標題是半形空格、cpbl 混用全形冒號。`## Log` 有資源宣告哨兵歷史回音，判定用 `wf_cli.resources.parse_block` 不要 grep。


## Comment 5337326614 · 2026-08-19T03:55:53Z

# 跨家族查核委託（一）：ai-workflow 兩張治理卡（2026-08-19）

你無 wfcli 寫入通道——產出文字裁決＋findings，由需求方轉貼、PM 轉錄。全程唯讀，收尾回報兩棵真樹 `git status --porcelain -uno` 為空。

⚠️ **本委託的特殊之處：兩張卡的卡面前提都被執行者實測推翻，而 PM 已複驗確認執行者正確、PM 錯。** 所以你的第一判準不是「有沒有照卡面做」，而是「**在前提被推翻之後，交付的東西是不是對的**」。

## 環境

```
ai-workflow origin/main   4dd9d325f00050a7c056964ca93e31aeb1bedb86
#106 worktree             /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/cleanup-submodule-106
     分支/SHA             claude/cleanup-submodule-aware-106 @ c81886865d8ead489124558cdccc163b9a2e7539（基線 4e6925e）
#107 worktree             /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/daily-snapshot-107
     分支/SHA             claude/daily-snapshot-107 @ f04c29251b179c958fe7cf654a95fbecfccc6dff（三 commit）
另有 orphan 分支          origin/snapshots @ 8fda3e03019083185edc600e672a59ee769a3cf2（#107 的產物落點）
相關 PR                   #110（ROADMAP 更正，因 #106 的推翻而發）
```

進駐第一件事：`git rev-parse HEAD` 對 source_sha、工作區乾淨；不同即 review-invalid。

---

## 標的一：`#106 WF-CLEANUP-SUBMODULE-AWARE1`

改動恰兩檔＝資源宣告（`cleanup.py` +197、`test_cleanup.py` +300，既有測試刪除 0 行）。

### ⭐ 第一判準（具否決權）

卡面核心痛點（PM 寫的）：「git `validate_no_submodules` 判準是『index 含 gitlink 且路徑存在為目錄』——**空目錄也算**，故對**任何** cpbl worktree 構造性失敗」。

**執行者實測推翻，PM 複驗確認（git 2.50.1 Apple Git-155）**：空 gitlink 目錄 `worktree remove` rc=0 移得掉、不需 `--force`；真正 blocker 是 `<worktree gitdir>/modules` 存在（曾初始化 submodule）。

你要裁的第一題：**推翻本身對不對**（自己重跑那格），以及**推翻之後這張卡還該不該存在**。執行者主張價值轉向為「(a) 正確偵測真 blocker 並給人工路徑；(b) 補上 git 看不見的靜默刪除防線」。

### 要驗的

1. **推翻的六格行為表**——執行者列了六種 gitlink 目錄狀態 × `git status` × `worktree remove` 的結果。**至少親跑「空目錄可移除」與「rmdir 後樹轉髒改以另一理由拒絕」兩格**（後者是「卡面處方無出口」的關鍵）。用 disposable worktree，收尾清乾淨。
2. ⭐ **反向的新洞**（PM 已複驗，你獨立重跑）：gitlink 目錄有檔案但 submodule 未初始化時，`git status --porcelain --ignore-submodules=none` 報空、`worktree remove` rc=0 **連同內容一起刪**。判這是否構成 canonical「禁止靜默刪除工作內容」的實質違反、以及新守衛是否真的擋得住。
3. **驗收條 1 的偏離**（執行者自己指出的施力點）：卡面要「移除前安全處理空的 submodule 目錄」，交付是「測量後**刻意不動**」。PM **未修改驗收條**（事後改驗收條配合交付＝搬門柱）。判此偏離可否接受。
4. **「比 git 嚴一格」是新擋點**：非空即擋，會擋下 git 本來會放行的「非空但未初始化」。方向保守但確為新增，判可否接受。
5. **五個變異注入**是否各由指名測試接住——親跑至少兩個。
6. `pytest 1017 passed`（基線 1009+8）、既有測試零修改、`_execute_closeout` 一行未改。

### 執行者自報、需你判分量的四項

- 收尾 disposable worktree 時 `submodule deinit` 寫到**共享** `.git/config`，一度弄壞 cpbl 主 checkout 的 submodule 註冊；已修復並自報。PM 複驗現況 `f207d2e`／20 entries／status 乾淨。但執行者自陳無法證明 `submodule.active` key 動手前是否存在（未事先備份 config）。
- **git 版本只驗 2.50.1 一個**；執行者主張若某版本真的拒絕空目錄則無可實作的解（rmdir → 樹轉髒 → 改以另一理由拒絕），並寫了 `test_git_itself_refuses_removal_only_for_an_initialized_submodule` 讓判準一變即轉紅並指名理由。判這個處置是否足夠。
- **未讀 git C 原始碼**，機制解釋（`.git` 可否解析為 git dir）**未經原始碼驗證**；實作只依賴行為表。
- 已初始化路徑的行為由**拋 `CleanupGuardError`** 改為 **`detect_only`**——兩者都 fail-closed，但呼叫端錯誤處理路徑不同，執行者只讀碼未實跑。
- `Implemented-by` trailer 與卡面 owner 不逐字相同（執行者實為 Opus 5，已在 trailer 內註明），主動揭露。

---

## 標的二：`#107 OPS-DAILY-SNAPSHOT1`

改動恰兩檔＝資源宣告（`scripts/daily_snapshot.sh` +342、`snapshots/README.md` +67）。

### ⭐ 第一判準

核心痛點：canonical `AI_WORKFLOW.md:138` 逐字「必須以每日 snapshot export 回 git 建立離線稽核副本」，而實測零產物、零排程 15 天。

**執行者揭露一個 PM 開卡時不知道的差距**：`wfcli snapshot` 匯出的是**看板當前狀態**（13 個凍結欄位＋卡面資源宣告），**不含 Issue timeline 上的 lifecycle event 留言**——被事後編輯或刪除的結構化 comment，這份快照**偵測不到**。而 `:138` 要的是「**事件流**」的副本。

你要裁：**做到「狀態面那一半」算不算痛點已消？** 執行者未包裝成已解決，寫進了 README 與 commit 訊息，但 canonical 本文仍讀起來像它有。

### 要驗的

1. ⭐ **落點是孤兒分支 `snapshots` 而非 main，是執行者自主決定、卡面沒預期。** 理由：ruleset 20768920 對 default branch 要求 status check、`strict=true`、`bypass_actors` 空，無人值守直推過不去；`allow_auto_merge=false` 故走 PR 需機器自行 merge（治理違規）。⚠️ **該前提未實測**（實測需往 main 推一筆，派工明令不碰 main），旁證只有 ruleset 設定值＋生效後 main 每筆 commit 都掛得到 PR。**判此決定可否接受**；另判「新開一條遠端分支」是否逸出 `file:snapshots/` 的宣告字面。
2. **驗收條 2 明確未成立**：只有 1 筆產物且 `trigger: launchd-selftest`（kickstart 非日曆觸發，字串刻意區分）。執行者給了可證偽的預先登記：merge 後第二、三天 10:40±數分應各出現一筆 `trigger: launchd`、目錄名為當日日期；出現 `trigger: manual`、兩筆同日或目錄跳號即判排程沒跑。**判這個「時鐘從 merge 開始走」的安排可否接受**，或應退回要求先取得兩日產物。
3. **驗收條 3 未執行**，卡在授權（`AI_WORKFLOW.md` 不在資源宣告內）。判該補宣告重做，或另開卡。
4. ⚠️ **PM 卡面的 GraphQL 成本數字錯**：卡面寫「2 點/日」，PM 自跑 `gh api rate_limit` 前後差實測 **6 requests/次**（隨卡數成長，`list_items` 每 50 張多一頁）。屬 coordinator，待裁後 amend。
5. 執行者自報未驗：10:40 日曆觸發本身（只驗 kickstart）、睡眠/關機補跑、跨日產生不同目錄是用 `date` shim **模擬**非真跨日、`snapshots` 分支未來可能被 cleanup 誤判為可清理的孤兒分支。
6. `trailer 守衛實測有跑到`（`doctor --commit-trailers` 違規 0／合規 3）、`pytest 1009 passed`、escalation replay 65/65。

---

## 回報格式（兩張分開）

每張：裁決 `APPROVE`／`REQUEST_CHANGES`＋`core_pain_resolved: yes|no`＋理由。
findings 用結構化欄位：`finding_id`／`severity: critical|major|minor|info`／`blocking`／`finding_class: implementation|authoritative-artifact|governance|coordination|environment`／`attribution: executor|planner|coordinator|reviewer|external`／`root_cause_id`／`evidence`（附指令與原始輸出）／`disposition`。
⚠️ 請**只用上列列舉值**——前兩次轉錄都因用了列舉外的詞而需 PM 映射。
`self_run` 必填（無 self_run 的 APPROVE 無效）。⭐ 沒驗到的不得省略；5xx/空回應標 UNKNOWN。報告不得含 wfcli 查核事件 marker 前綴字面。


## Comment 5337516585 · 2026-08-19T04:25:25Z

<!-- wf-review-event:v1 card_id=OPS-DAILY-SNAPSHOT1 source_sha=f04c29251b179c958fe7cf654a95fbecfccc6dff attempt_id=OPS-DAILY-SNAPSHOT1-e0-f04c29251b179c958fe7cf654a95fbecfccc6dff -->
## 查核裁決：REQUEST_CHANGES

- 卡：`OPS-DAILY-SNAPSHOT1`　attempt_id：`OPS-DAILY-SNAPSHOT1-e0-f04c29251b179c958fe7cf654a95fbecfccc6dff`
- 查核者：Google DeepMind Antigravity　escalation_epoch：0
- source_sha：`f04c29251b179c958fe7cf654a95fbecfccc6dff`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-19T12:25:23+08:00

### self_run（查核者實跑）

- `bash scripts/daily_snapshot.sh --check`
  - [snapshot] 159 張卡 → /var/folders/.../snapshot.json, SNAPSHOT.md；[check] 遠端可達、snapshot 可產生（159 張卡）；接著 scripts/daily_snapshot.sh: line 270: OUT_TMP: unbound variable，rc=1。改為 ${OUT_TMP} 後可正常輸出且 rc=0
- `cd .../daily-snapshot-107/cli && uv run wfcli doctor --commit-trailers --commit-range 4e6925e..HEAD ..`
  - 違規 0／合規 3／無所要求 0（共 3 筆）
- `cd .../daily-snapshot-107/cli && uv run pytest`
  - 1009 passed in 54.14s
- `uv run pytest tests/test_validation.py`
  - 100 passed in 1.24s（含 65 項 escalation replay）
- `產物分支驗證 origin/snapshots @ 8fda3e0`
  - 含 snapshots/2026-08-19/snapshot.json 與 SNAPSHOT.md，commit 具備 trigger: launchd-selftest、cards: 159、wfcli-source: 576df981
- `PM 補跑：逐 locale 重現 line 270 崩潰`
  - LC_ALL=C rc=0；LC_ALL=zh_TW.UTF-8 rc=127 unbound variable；LC_ALL=en_US.UTF-8 rc=127 同上——確認為 locale 依賴的真缺陷

### findings（3，其中 blocking 1）

- **OPS-DAILY-SNAPSHOT1-R1-01**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`unbraced-variable-expansion-unicode-parenthesis`
  - evidence：查核者原編號 FINDING-107-1。scripts/daily_snapshot.sh:48 啟用 set -uo pipefail；未加花括號的變數展開緊鄰全形括號時，變數名解析吃進該多位元組字元而觸發 unbound variable。受影響行：231 `找不到 $tool（PATH=$PATH）`、245 `$LOCK_DIR（確認沒有殘留後手動 rmdir）`、263 `wfcli snapshot 失敗（rc=$SNAPSHOT_RC）`、270 `產物暫存於 $OUT_TMP（本次結束即刪）`、336 `push 失敗（commit $COMMIT_SHA 留在本機 $CLONE_DIR）`。⚠️ PM 補正機制敘述：查核者原寫「全形括號在 bash 3.2 下為合法識別符字元」，實測為 **locale 依賴**——LC_ALL=C 不觸發、UTF-8 locale（zh_TW／en_US 皆試）觸發 rc=127。多數受影響行位於 die() 錯誤回報路徑，即錯誤處理本身會二次崩潰。
  - disposition：將 scripts/daily_snapshot.sh 內緊鄰全形括號的變數統一加上花括號 ${VAR}。⚠️ PM 追加：修好後須在 UTF-8 locale 下實跑取證（LC_ALL=C 驗不出來），並考慮於腳本開頭固定 locale 或加一支涵蓋 die() 路徑的煙霧測試——受影響行多在錯誤路徑，正常流程測不到。
- **OPS-DAILY-SNAPSHOT1-R1-02**　severity=minor　blocking=false　class=authoritative-artifact　attribution=planner　root_cause_id=`canonical-scope-gap-state-vs-event-stream`
  - evidence：查核者原編號 FINDING-107-2。AI_WORKFLOW.md:138 寫明「必須以每日 snapshot export 回 git 建立離線稽核副本」，實際 wfcli snapshot 僅涵蓋 Project 狀態面（13 個欄位與資源宣告），不含 Issue timeline 結構化留言。驗收條 3 因卡片資源宣告未包含 AI_WORKFLOW.md 而未被執行者修改（遵守資源隔離界線）。比對 AI_WORKFLOW.md:138、snapshots/README.md:46-55 及 commit 576df981。
  - disposition：由 PM 另開治理文件卡，或補宣告資源修訂 AI_WORKFLOW.md §4.1/§4.3，將「狀態面快照已落孤兒分支」與「事件流留言離線副本尚待後續架構」兩者邊界於 canonical 寫明。
- **OPS-DAILY-SNAPSHOT1-R1-03**　severity=info　blocking=false　class=coordination　attribution=coordinator　root_cause_id=`graphql-cost-estimation-mismatch`
  - evidence：查核者原編號 FINDING-107-3。原卡面描述估計「2 點/日」，實測每次 snapshot 消耗 6 個 GraphQL requests（每 50 張卡分頁增長 1 request）。執行者已於 snapshots/README.md:66 記載實測數據。PM 亦獨立以 gh api rate_limit 前後差實測得 6。
  - disposition：由 coordinator 於卡面 amend 實測 6 requests/次 之成本基線。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: OPS-DAILY-SNAPSHOT1-e0-f04c29251b179c958fe7cf654a95fbecfccc6dff
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待指派
findings:
  - finding_id: OPS-DAILY-SNAPSHOT1-R1-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: unbraced-variable-expansion-unicode-parenthesis
    counting_eligible: true
  - finding_id: OPS-DAILY-SNAPSHOT1-R1-02
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: authoritative-artifact
    attribution: planner
    root_cause_id: canonical-scope-gap-state-vs-event-stream
    counting_eligible: false
  - finding_id: OPS-DAILY-SNAPSHOT1-R1-03
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: coordination
    attribution: coordinator
    root_cause_id: graphql-cost-estimation-mismatch
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5337638274 · 2026-08-19T04:44:32Z

# R2 查核委託：`OPS-DAILY-SNAPSHOT1` @ `b03f4e441c27d429ea82aae22dd8857d5d1e18fb`（2026-08-19）

R2 只做兩件：**R1-01 閉環＋回歸不倒退**。不重跑 R1 已通過項、不擴審。全程唯讀。

## 要驗的四項（執行者自己開的清單，PM 已全數複驗過，你可質疑方法）

1. **全檔掃描 = 0**：`perl -ne '$n++ while /\$[A-Za-z_][A-Za-z0-9_]*[\x80-\xFF]/g; END{printf "%d\n", $n||0}' scripts/daily_snapshot.sh`
2. **變異檢驗 = 1**：植入一行 `echo "壞形 $FOO（測試）"` 後重跑掃描器
3. **三 locale 煙霧 5/5**：`zh_TW.UTF-8` / `en_US.UTF-8` / `C`，五條 die() 路徑各自印出訊息且離開碼為 69/75/78/0/79。⚠️ **harness 不在 repo 內**（超出資源宣告），須照 `snapshots/README.md` 的表格重建
4. **pytest 1009 不倒退**

## ⭐ 形狀變更是否正確（本輪主要裁決題）

R1 的 finding 敘述是「全形括號」，執行者實測 0x80–0xFF 全部 128 個 byte 後改判為「**任何 byte ≥ 0x80**」（65 個命中，涵蓋 CJK/全形 lead byte），判準因此由「5 行的位置表」改為封閉集合 regex。**PM 已獨立複驗**：`$V` 緊鄰 `（`、`本`、`，`、`。` 四者全部 CRASH。

判：(a) 這個一般化是否正確；(b) 掃描器命中 7 處而 R1 只列 5 行的差異（第 65 行 quoted heredoc 內屬惰性、第 231 行同行兩處）是否處理得當；(c) 同行 `$COMMIT_SHA` 後接 ASCII 空白**未動**是否正確。

## ⚠️ 執行者自報、你要判分量的三項

1. **此缺陷族 CI 抓不到，且現在仍然抓不到。** CI 已釘 `LC_ALL: C.UTF-8`（故 R1 委託引用的 `ROADMAP:144-148` 已被該 workflow env 取代——這點值得你複驗）；但 `grep -rc daily_snapshot --include='*.py'` → 0、pytest `testpaths=["tests"]` 只收 `cli/tests/`，**沒有任何 CI 步驟執行這支腳本**。守衛與煙霧測試目前只有文件、無機器執行。執行者主張修不了是因為新增測試檔超出資源宣告（只有 `scripts/daily_snapshot.sh` + `snapshots/README.md`）。**判這個界線是否成立**，或該補宣告／另開卡。
2. **煙霧測試採「等價機制」而非註冊測試**（跑一次取證＋可重現程序寫進 README，harness 留 scratchpad）。判可否接受。
3. **rc 不符**：PM R1 委託記 `rc=127`，執行者實測一律 `rc=1`（bash 3.2 non-interactive `set -u` 中止），呼叫方式不同所致，執行者未追。判是否需要追。

## 回報格式

裁決 `APPROVE`／`REQUEST_CHANGES`＋`core_pain_resolved`＋理由；findings 結構化欄位——⚠️ **`severity` 只能用 `critical|major|minor|info`、`finding_class` 只能用 `implementation|authoritative-artifact|governance|coordination|environment`、`attribution` 只能用 `executor|planner|coordinator|reviewer|external`**（前三次轉錄都因用了列舉外的詞而需 PM 映射）；`self_run` 必填。⭐ 沒驗到的不得省略；5xx/空回應標 UNKNOWN。報告不得含 wfcli 查核事件 marker 前綴字面。


## Comment 5337720319 · 2026-08-19T04:57:56Z

## ⚠️ 留痕補正：本輪裁決無 `wf-review-receipt:v1` 收據（2026-08-19，PM）

`templates/dispatch-package.md:55` 逐字要求「查核者先在被審 Issue conversation 或 PR review body 留 `wf-review-receipt:v1`（`card_id`、完整 `source_sha`、查核報告 UTF-8 `report_sha256`）」，且「PM 僅能逐字轉錄與收據 hash 相符的報告……**不能以 `--reviewer` 自由字串代替收據**」。

**本卡的 review 事件不符合這條紀律**，據實記錄：

- 本卡收據數 **0**（`gh api .../comments --jq "[.[]|select(.body|test(\"wf-review-receipt\"))]|length"`）。
- `--reviewer` 欄是 PM 打的自由字串，**非可驗證身分**。查核者的實際身分由需求方口頭轉述，機械上無從驗證。
- `wfcli doctor --review-channel` 對本卡回報 `[recorded]`（三面一致）——⚠️ **它驗的是事件／Log／Project 三面是否一致，而三面都是 PM 寫的，自然一致；收據缺席它看不見。**

**不追溯本筆裁決**，理由三項：(1) 裁決的實質內容經 PM 逐項獨立複驗（非僅信任查核者），複驗指令與輸出見本卡 review 事件的 self_run 與 PM 補正段；(2) 收據機制假設查核者能寫 GitHub，而跨家族查核者**沒有寫入通道**（既有事實），故該紀律在現行「需求方轉貼」通道上**構造上無法遵守**；(3) 追溯需重跑查核，成本遠高於風險。

機制缺口另開卡處理（承接卡見 ai-workflow）。本帖僅為留痕，不改變本卡狀態。

## Comment 5337827427 · 2026-08-19T05:14:17Z

<!-- wf-review-event:v1 card_id=OPS-DAILY-SNAPSHOT1 source_sha=b03f4e441c27d429ea82aae22dd8857d5d1e18fb attempt_id=OPS-DAILY-SNAPSHOT1-e0-b03f4e441c27d429ea82aae22dd8857d5d1e18fb -->
## 查核裁決：APPROVE

- 卡：`OPS-DAILY-SNAPSHOT1`　attempt_id：`OPS-DAILY-SNAPSHOT1-e0-b03f4e441c27d429ea82aae22dd8857d5d1e18fb`
- 查核者：Google DeepMind Antigravity　escalation_epoch：0
- source_sha：`b03f4e441c27d429ea82aae22dd8857d5d1e18fb`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-19T13:14:16+08:00

### self_run（查核者實跑）

- `perl -ne '$n++ while /\$[A-Za-z_][A-Za-z0-9_]*[\x80-\xFF]/g; END{printf "%d\n", $n||0}' scripts/daily_snapshot.sh`
  - 0
- `變異注入：植入 echo "壞形 $FOO（測試）" 後重跑掃描`
  - 1（接住）
- `自建獨立 bare repo 與 mock uv，跑 3 locale × 5 路徑的煙霧矩陣（15 組）`
  - zh_TW.UTF-8／en_US.UTF-8／C 三者各 5/5：Case1 Missing gh rc=69、Case2 Lock held rc=75、Case3 Snapshot fail rc=78、Case4 --check ok rc=0、Case5 Push fail rc=79；15 組全部 Msg Matched=True 且 Status Written=True
- `cd .../daily-snapshot-107/cli && uv run pytest`
  - 1009 passed in 54.77s
- `進駐校驗 git rev-parse HEAD 對 source_sha、git status --porcelain -uno`
  - HEAD=b03f4e4 對齊；工作區乾淨

### findings（1，其中 blocking 0）

- **OPS-DAILY-SNAPSHOT1-R2-01**　severity=info　blocking=false　class=implementation　attribution=executor　root_cause_id=`unbraced-variable-expansion-unicode-parenthesis`
  - evidence：查核者原編號 FINDING-107-1-VERIFIED。全檔掃描 0、變異注入 1、三 locale 15/15 煙霧全綠（離開碼與訊息與狀態檔三者皆吻合）。⚠️ 查核者的 15 組矩陣比執行者交付時的 5/5×3 更完整——它另外驗了每組的 Msg Matched 與 Status Written 兩個維度，涵蓋執行者發現的「二次崩潰時 write_status 不執行、last-status.json 整份不存在」那個附帶損害。
  - disposition：R1-01 缺陷已完整修復並經多環境驗證，確認結案。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: OPS-DAILY-SNAPSHOT1-e0-b03f4e441c27d429ea82aae22dd8857d5d1e18fb
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待指派
findings:
  - finding_id: OPS-DAILY-SNAPSHOT1-R2-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: implementation
    attribution: executor
    root_cause_id: unbraced-variable-expansion-unicode-parenthesis
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。
