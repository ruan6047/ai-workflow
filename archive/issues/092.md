# #92 WF-AMEND-RESOURCE-CONFLICT1 amend 擴大資源宣告時不跑互斥檢查，assign 建立的不變量可被事後打破
- state: closed  created: 2026-08-16T04:38:43Z  closed: 2026-08-17T03:24:57Z
- url: https://github.com/ruan6047/ai-workflow/issues/92
- comments: 2

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；改動面小（把既有的 find_conflicts 接到 amend 的寫入路徑）但要判斷的東西不小：amend 的比對基準該是新宣告全集還是新增的差集、對已派工卡與未派工卡是否同一判準、以及被擋下時的補救路徑（縮小宣告？先釋放？）。經濟型容易直接複製 assign 的迴圈而忽略 amend 的語意不同——assign 是進場，amend 是進場後改邊界。）　查核：待指派（建議 主力型；唯讀不變量的補強，行為改變侷限在一個動詞的拒絕路徑，風險不高。但查核重點在【新的檢查會不會製造假保證】——本 repo 近期反覆踩到的形狀是接了線卻在真實操作順序下不可能開火（見 WF-WORKTREE-REPO-OWNERSHIP1 的軸 B）。須實測一次真的擴大宣告到活卡領土並確認被擋。跨家族非必要。）
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：資源互斥是本專案避免兩個 agent 同時改同一個檔的唯一機制。它現在只在一個時點成立（assign 當下），而不是一個持續為真的不變量——這使『兩張活卡不會撞』從機制退化為慣例。

## 簡介
<!-- card-brief:begin -->
已停止並併入 aiwf#94（契約↔工具全量對帳），核心痛點逐字保留為該卡核心痛點第 (4) 條。原要處理的是：open／assign／amend 三個動詞都會寫資源宣告，但全 repo 只有 assign_cmd.py:127 呼叫 find_conflicts，amend_cmd.py:629 直接寫入而不比對交集——於是 assign 進場時建立的「本卡資源與所有活卡不相交」可被事後打破，一張執行中的卡能把宣告擴大到另一張活卡的領土而沒有任何東西擋。**適用時機**：要查 amend --resources 為何不跑資源互斥檢查、或該議題現在歸哪張卡時。⛔ 非射程：本卡不再執行任何修法，實作歸 ai-workflow#94，併卡裁定見 issuecomment-5311411440；open --resources 不檢查的洞不在原射程（未認領卡被 is_owner_assigned 過濾，危害較低）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：三個動詞會寫資源宣告——open（--resources）、assign、amend（--resources）——但全 repo 只有一處呼叫互斥檢查：assign_cmd.py:127 的 find_conflicts。amend_cmd.py 只 import parse_block／render_block（:195），在 :629 直接 amend_resource_block(body, render_block(decl)) 寫入，中間沒有任何交集比對。⚠️ 這不是「少檢查一次」，是【assign 建立的不變量可以被事後打破】：assign 在進場時保證「本卡的資源與所有活卡不相交」，而 amend 讓一張已派工、執行中的卡把宣告擴大到另一張活卡的領土，沒有任何東西擋。assign 的迴圈只在 assign 當下跑一次，之後不再重掃。實例：2026-08-16 PM 為 WF-AMEND-AUTHZ-BINDING1（#62）把宣告由兩檔擴為四檔（新增 file:cli/src/wf_cli/doctor.py、file:cli/tests/test_doctor.py，op d5438683），指令直接成功；PM 是在事後手動查 #63／#65／#30 三張同樣宣告 doctor.py 的卡全為「執行：待指派」、且宣告持有者 WF-CLEANUP-GUARD1（#25）已 CLOSED，才知道沒撞到——不是工具告訴他沒撞。若那三張其中一張正在執行中，這筆 amend 一樣會成功。⚠️ open 也不檢查，但那條的危害較低：新開的卡尚未認領，assign 的 is_owner_assigned 過濾使它不計入活卡；真正的洞在 amend。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/amend_cmd.py",
    "file:cli/tests/test_amend.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] amend --resources 在新宣告與任一活卡（非終態且已認領）相交時 fail-closed 拒絕，錯誤訊息指名相交的卡與相交的資源，語彙與 assign 的拒絕訊息一致。
- [ ] 比對基準須明確裁定並寫進 help：是拿新宣告的全集比對，還是只比對新增的差集。⚠️ 兩者不等價——若用全集，一張卡把自己原有的宣告 amend 成同樣內容也會被自己以外的重疊擋下；若用差集，縮小宣告的 amend 不受影響但擴大時只檢查新增部分。選哪個要有理由，不得預設。
- [ ] 檢查須對「已派工卡」與「未派工卡」給出明確且有理由的差別待遇（或明確裁定不分）。assign 現行以 is_owner_assigned 過濾未認領卡，amend 是否沿用同一判準須明寫。
- [ ] 被擋下時的補救路徑須寫進錯誤訊息：縮小宣告、等對方結案、或由需求方裁定覆寫。不得只說「拒絕」而不說怎麼繼續。

## 驗證

- [ ] 端到端實測：造一張已認領的活卡持有某檔，再對另一張卡 amend 擴大到該檔，確認被擋；縮小宣告的 amend 確認不被擋。兩者都要真跑 CLI 而非只跑單元測試。
- [ ] 變異檢驗：拿掉新加的檢查，上述端到端測試須轉紅。
- [ ] 回歸：既有 amend 測試全綠，且既有卡片的宣告不因新檢查而回溯違規（新檢查只作用在新的 amend，不重掃歷史）。
## Log

- 2026-08-16T12:38:42+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-18T19:50:19+08:00 handoff by wf-cli → owner —（已停止）；iteration 0；SHA f207d2ecf80556d6b90beeb0438bf648288a5fd9；證據 收尾補帳（2026-08-18）：Issue 已於 2026-08-17 關閉（NOT_PLANNED）而交付狀態停在 📥Backlog，本次補終態。決策與原因：併入 #94（家族卡：契約↔工具全量對帳），裁定見 issuecomment-5311411440。⚠️ 本卡的核心痛點逐字保留於 #94 的核心痛點第 (4) 條（amend --resources 不跑資源互斥檢查），不因併卡而遺失。。
- 2026-08-26T21:58:07+08:00 amend by wf-cli（op ef5d7a49）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:93f3e693e1f8b96741566ba2c5f7d46409f25130de1363253a7f92ece5b43550 (844 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5311411440 · 2026-08-17T03:24:56Z

併入 **#94 **（已改為家族卡：契約↔工具全量對帳，裁定見 #94 的 `issuecomment-5311397884`）。

⚠️ 本卡的核心痛點**逐字保留**於 #94 的核心痛點第 (4) 條，不因併卡而遺失：`amend --resources` 不跑資源互斥檢查（`amend_cmd.py` 只 import `parse_block`／`render_block`，全 repo 僅 `assign_cmd.py:127` 呼叫 `find_conflicts`），後果是**先 assign 小射程、再 amend 擴大即可繞過派工閘門建立的不變量**。

關閉理由是它與 #94、#95 是同一個根因被開成三張卡——**契約宣告了、寫入通道沒實作、從未對過帳**。需求方裁定改以家族卡一次對帳，而不是逐個補洞。

## Comment 5311415849 · 2026-08-17T03:25:45Z

訂正上一則：卡號被 shell 反引號吃掉了。併入的是 **#94 WF-REVIEW-INVALID-TRACE1**。
