# #23 WF-EVENT-IDEMPOTENCY1 lifecycle 事件的排序與冪等：state_version 取號、決定性 event_id、resume 演算法
- state: closed  created: 2026-08-11T04:50:45Z  closed: 2026-08-12T01:35:56Z
- url: https://github.com/ruan6047/ai-workflow/issues/23
- comments: 19

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code
- 執行：待指派　查核：跨家族查核（契約本體，須走 PR）
- Initiative：—　spec 基線：自 ai-workflow#16 切出（需求方 2026-08-11 裁定縮小 #16 射程）。基準內容＝#16 設計文件 §3.1 於 SHA 2d361303ce438c6fecf475b2aaa1fcbc06518dc9 的狀態，該節已歷 R5／R6／R7 三輪跨家族查核（R5-002 連三輪未閉環）。#16 縮為框架卡後只保留「狀態機對本機制的假設」，機制本體歸本卡。相依：#16 §4 的自描述首寫以本卡的 event_id 為辨識基礎；#16 §5.2 白名單第 1 條依賴本卡的 resume 演算法。
- DB：db_scope=none
- 服務的原始目標：讓 lifecycle 事件在無本機狀態、無時鐘的前提下可排序、可重試、可重放，且任何無法安全判定的情形一律 fail-closed。

## 簡介
<!-- card-brief:begin -->
定義 lifecycle 事件在無本機狀態、無時鐘前提下可排序可重試可重放的機制：state_version 取號程序與三種異常（撞號／缺號／無序號）的 fail-closed 處置、由意圖決定性導出且不含鏈尖端不含時鐘的 event_id、逐型別不留「其餘」格的 args canonical bytes、純讀 GitHub 的 resume 與 --new-attempt salt 衝突 fail-loud。**適用時機**：寫入成功但回應遺失、重跑不確定會不會產生第二筆事件或誤判撞號時；或要查 event_id 材料為何刻意排除鏈尖端的依據時。⛔ 非射程：明示不承接 open（建立型半寫入無法由 event_id 解決，aiwf#16 R12-004）；跨主機只能偵測撞號不得宣稱預防；失敗注入矩陣在本卡定義、執行歸衍生實作卡。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：GitHub 寫入無原子遞增亦無 CAS；取號是 read-modify-write，且「寫入成功但回應遺失」會讓重試誤判撞號或寫出重複事件。canonical AI_WORKFLOW.md:141 已要求 event_id 與單調遞增的 state_version，但未定義取號程序、異常處置與重試辨識，故實務上兩者都不成立。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:docs/WF_EVENT_IDEMPOTENCY1.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 定義 state_version 取號程序與三種異常（撞號＝同號不同 event_id、缺號、無序號）的 fail-closed 處置；同號同 event_id 明確不是撞號。
- [ ] 撞號的同機並行以 (owner, project, card_id) 原子目錄鎖預防（canonical :148 明文允許）；跨主機無併發控制服務故僅能偵測，不得宣稱預防。
- [ ] event_id 由意圖決定性導出，材料為 owner／project／card_id／verb／args／attempt_salt；不含鏈尖端、不含時鐘、不含 state_version。須說明「以鏈尖端為材料」為何在回應遺失後恰好失效。
- [ ] 逐型別定義 args 的 canonical bytes，不留「其餘」格：自由文字（NFC＋LF＋去尾白）、枚舉（逐位元組取自 FIELD_SPECS，拒收 variation selector 與零寬字元）、路徑、SHA、整數布林、結構化輸入（先解析再以排序鍵無註解形式序列化，不對原始文字取雜湊）。無法歸類的新欄位在其規範化定義補上前，該動詞不得納入冪等鍵機制。
- [ ] 定義 resume 演算法（純讀 GitHub、無本機狀態）、already_exists 的可辨識退出碼與零狀態寫入、以及 --new-attempt <標籤> 的 salt 衝突 fail-loud。
- [ ] 明文記錄理論界線：本機零狀態下「重試」與「刻意重跑同一指令」原則上不可區分；需求方已裁定保留辨識重試、犧牲無聲重跑。

## 驗證

- [ ] 對每一個寫入邊界定義網路失敗注入的測試矩陣（請求送達且寫入成功但回應遺失，重跑後不得產生第二筆事件、不得判為撞號、且能正確補齊後續步驟），覆蓋 review／amend／handoff／assign／deploy-* 全部動詞。**矩陣在本卡定義，執行歸衍生實作卡**——本卡資源僅含設計文件，open_cmd.py 等由 ai-workflow#21 佔用中。
- [ ] emoji 枚舉專項須列入矩陣：交付狀態值含 U+FE0F 變體選擇符時必須被拒收，且不得因終端差異產生不同 event_id。
- [ ] 跨家族查核確認不與 canonical AI_WORKFLOW.md:141 的最小 schema 與 :148 的鎖規則衝突。
- [ ] **明示不承接 open**：ai-workflow#16 R12-004 已判定 open 的建立型半寫入無法由 event_id 解決（回應遺失後無法定位已建立的 Issue）。本卡不得宣稱涵蓋 open；若要解需另立 discover-before-create 的設計裁定。
## Log

- 2026-08-11T12:50:43+08:00 open by Claude Opus 5@Claude Code；owner 待指派；iteration 0。
- 2026-08-11T20:15:56+08:00 amend by wf-cli（op 13b3953f）→ 驗證：原值「[ ] 對每一個寫入邊界做網路失敗注入回歸測試：請求送達且寫入成功但回應遺失，重跑後不得產生第二筆事件、不得判為撞號、且能正確補齊未完成的後續步驟。須覆蓋 review／amend／handoff／assign／deploy-* 全部動詞。；[ ] emoji 枚舉專項：交付狀態值含 U+FE0F 變體選擇符時必須被拒收，且不得因終端差異產生不同 event_id。；[ ] 跨家族查核確認不與 canonical AI_WORKFLOW.md:141 的最小 schema 與 :148 的鎖規則衝突。」→ 新值「對每一個寫入邊界定義網路失敗注入的測試矩陣（請求送達且寫入成功但回應遺失，重跑後不得產生第二筆事件、不得判為撞號、且能正確補齊後續步驟），覆蓋 review／amend／handoff／assign／deploy-* 全部動詞。**矩陣在本卡定義，執行歸衍生實作卡**——本卡資源僅含設計文件，open_cmd.py 等由 ai-workflow#21 佔用中。；emoji 枚舉專項須列入矩陣：交付狀態值含 U+FE0F 變體選擇符時必須被拒收，且不得因終端差異產生不同 event_id。；跨家族查核確認不與 canonical AI_WORKFLOW.md:141 的最小 schema 與 :148 的鎖規則衝突。；**明示不承接 open**：ai-workflow#16 R12-004 已判定 open 的建立型半寫入無法由 event_id 解決（回應遺失後無法定位已建立的 Issue）。本卡不得宣稱涵蓋 open；若要解需另立 discover-before-create 的設計裁定。」；理由 本卡資源僅含自身設計文件，而原驗證條文要求實跑故障注入；且 open_cmd.py 由 #21 佔用。改為在本卡定義測試矩陣、執行歸衍生卡，並依 #16 R12-004 明示不承接 open。
- 2026-08-11T20:19:50+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree claude/WF-EVENT-IDEMPOTENCY1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1；交付狀態 🚧進行中。
- 2026-08-11T20:30:21+08:00 handoff by wf-cli → owner 跨家族查核（契約本體，須走 PR）；iteration 0；SHA ad8056faf2cd7260decb3a72e4f5cbab8bb04a3e；證據 docs/WF_EVENT_IDEMPOTENCY1.md（425 行）：state_version 五情形判準、event_id 決定性導出（含鏈尖端反例）、args 六型別 canonical bytes 全函數、resume 演算法＋退出碼 7、理論界線、24 注入點測試矩陣＋emoji M1-M5、canonical 相容性逐條核對、明示不承接 open。完備性證據：分類器對 106 個參數實跑未分類=0，附負向測試（移除登錄項→exit=1）證明檢查非恆真。設計期發現 handoff/assign --status 與 amend --db-scope 直接寫入 SINGLE_SELECT 卻無 choices，以 argparse 宣告為分類鍵會漏掉 emoji 拒收，已裁定分類鍵為目的地欄位。。
- 2026-08-11T21:20:38+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 跨家族查核（需求方於對話中轉貼原文；無 receipt marker，來源不可驗證）；core_pain_resolved no；self_run 3 項；findings 4 項（blocking 4）；attempt WF-EVENT-IDEMPOTENCY1-e0-ad8056faf2cd7260decb3a72e4f5cbab8bb04a3e。
- 2026-08-11T21:33:29+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 1；SHA ad8056faf2cd7260decb3a72e4f5cbab8bb04a3e；證據 R1：四項 blocking。R1-001 鎖內臨界區未閉合（允許鎖外判定後鎖內只重讀最大序號取號，兩程序同意圖可各寫一筆）；R1-002 --new-attempt 的 attempt_salt 未定義 canonical bytes 且未列入六型別；R1-003 stale lock 回收僅留 TTL 給實作卡，可奪走仍存活的鎖；R1-004 ensure_fields 非所有動詞共用之單一注入點，故寫入邊界的完整閉包宣稱不成立。首輪查核，無 escalation checkpoint。。
- 2026-08-11T22:03:31+08:00 handoff by wf-cli → owner 跨家族查核（契約本體，須走 PR）；iteration 1；SHA 1ee62b088dca5ef2c6d625e4eff6cfe6a2c9ec86；證據 R2：四項 blocking 全處置（文件 425→986 行，僅動 docs/WF_EVENT_IDEMPOTENCY1.md）。R1-001 臨界區改為固定五步並禁止跨鎖攜帶鎖外讀取結果，§5.1 演算法同步改寫（原本演算法與鎖各講一套，落差即缺陷），故障注入加 C1–C6。R1-002 attempt_salt 提升為第七型別，採禁止不安全輸入（^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$），空字串必須拒收係由長度前綴串接推導（空值與旗標缺席產生同一組位元組）。R1-003 設計層釘死不得僅以 TTL 奪鎖，僅同主機同開機且 pid 不存在或啟動時刻不符方可回收，跨主機一律 fail-closed。R1-004 讀碼確認且更嚴重：deploy-declare／deploy-state 完全不呼叫 ensure_fields，其內部對 13 個 FIELD_SPECS 逐一 field-create，天然冪等來自讀後跳過、並行下不成立且卡層鎖保護不到（它是專案層）；改由 AST 列舉器產生寫入邊界，A 類 23 個與 B 類 0–13 次分開建模，新增專案層鎖 L_project，不再宣稱固定注入點總數。修正中新發現並已裁定：首寫必須攜帶 event_id 否則 resume 會重新取號，逐動詞讀路徑判定 handoff／assign／amend --tier 三者不合格（amend --tier 為本輪新發現，#16 未區分該分支）。四支探針皆自文件原樣抽出重跑、輸出逐字相符。§10 明列對 #24 的四項外部相依假設並刻意不對齊。執行者自承八個未關的洞，其中最大者為 event_id 的載荷格式與回讀契約未定，以及 #16 設計文件不在本樹上故七處引用未逐條核對。。
- 2026-08-12T07:11:22+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（**無 receipt marker**，查核者未在 Issue 留言故身分不可驗證；報告經對話轉貼、report_sha256 無從重算。依 handoff-contract.md §3.1.2 末段，此 event 在身分維度上等同無佐證）；core_pain_resolved no；self_run 6 項；findings 2 項（blocking 1）；attempt WF-EVENT-IDEMPOTENCY1-e0-1ee62b088dca5ef2c6d625e4eff6cfe6a2c9ec86。
- 2026-08-12T07:19:27+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 2；SHA 1ee62b088dca5ef2c6d625e4eff6cfe6a2c9ec86；證據 R3：R2-001（major，blocking，external-path-normalization-domain-mismatch）——§4.1 把七個 CLI 路徑引數交給 #24 的封閉 namespace，§10 的 A2／A3 假設在兩張卡都交付後已可判定為不成立：資源宣告的 repo 根相對 namespace 與 CLI 引數的檔案系統路徑並非同一輸入域，而本卡也未提供自身的保守轉換定義。disposition：把 §4.1／§10 改為已驗的介面結論（路徑型別目前退出冪等保護並 stderr 明示），或在本卡定義獨立、全函數、可產生 canonical bytes 的 CLI 路徑規範化；不得再以 #24 的資源宣告比對語意作為 event_id 位元組來源。R2-002（minor，非阻擋，probe-runtime-version-unspecified）：§4.4 探針明示 python3，但本機 python3=3.9.6 時 isinstance(act, argparse._StoreTrueAction | argparse._StoreFalseAction) 直接 TypeError，uv run python=3.12.13 才通過；釘為 uv run python 或改用 3.9 相容的 tuple 形式。前輪四項（R1-001 至 R1-004）全數 resolved 並各有實跑證據。⚠️ 本輪查核者未留收據，裁決已轉錄但身分不可驗證（見同日 PM 轉錄紀錄）。⚠️ 跨卡分歧已如實保留：#24 的查核者從其側判定兩者本來就是不同輸入域、應明示不涵蓋 CLI 引數且不構成其 blocking finding，本卡查核者則判本卡須改；兩者的修法方向其實一致（本卡改 §4.1／§10、#24 加界線澄清），差別只在誰記為 blocking。無 escalation checkpoint（前輪 accepted blocking 皆已明列 resolved、新 finding 根因不同）。。
- 2026-08-12T08:55:18+08:00 handoff by wf-cli → owner 跨家族查核（契約本體，須走 PR）；iteration 2；SHA 50021ce8f3c1771e2fe6a312bf0552d172e1fd2c；證據 R3：R2-001 與 R2-002 已處置，另完成跨卡對帳 X2／X5，最後補上區塊數登記。R2-001（external-path-normalization-domain-mismatch）——查核者給的兩條路（降級／自訂正規化）執行者都沒選，選了第三條並附論證：降級會把卡打空（--config 在全部六個承接動詞上、assign --worktree 為 required，以引數面含路徑型別即退出保護實作則六個動詞全部永久退出，保護面歸零）；自訂正規化做不到（realpath 對不存在路徑無定義而 --out-dir 正是、大小寫與 NFC 敏感度是執行期檔案系統性質非設計期常數）。第三條是「路徑本身就是分類錯誤」——§4.3 早已立下「分類鍵是目的地不是宣告」，逐一追碼後六個動詞裡沒有任何引數需要檔案系統正規化，故本卡不定義也不引用任何 CLI 路徑正規化器，相依解除。連帶修掉一個獨立缺陷：§3.3 改以 resolve_target 解析後的三元組入鍵（原以原始旗標入鍵，--owner X 與 --config f 會產生同事件而異鍵）。PM 已核實三條承重事實：--config 在 config.py:69 的共用函式故在全動詞上、assign --worktree 為 required=True、set_field_value(級別) 在 amend_cmd.py:392 早於 set_item_body 的 :423 故 amend --tier 的遠端首寫確為級別欄——#16 §4.3 記反了，該更正待 #16 解除阻塞時吸收。R2-002 兩者都做（釘 uv run python 並改 tuple 形式），但 X2 之後撤除該處置改為沿用 #24 §9.9，理由是下限是繼承來的：§4.2 的型別閉包是無版本限定詞的全函數宣稱，而「能跑 wfcli」的範圍由 requires-python >=3.11 定義。沿用時把 #24 的自檢原樣未改一字指向本檔，因而發現該自檢兩個缺陷並指名而不代修——#24 已據此修畢五項。X5：§7.1.2a 記錄與 #25 的交互，判定 E1 對 handoff 本來就不成立、改變的是後果類別而非程度（從可由 resume 收斂變成不可逆效果已生效且無留痕），A′ 位階由「E1 的前置」升為「--cleanup 這條路徑能不能安全存在的前置」。50021ce 補上 probe-blocks 登記使本檔滿足所宣告沿用的標準，並把 §4.4.1 的陳舊輸出拆為歷史與現況兩段（執行者判定陳舊輸出是真的可重現性缺陷，非表面同步）。PM 複驗終態自檢：四支探針全部實際執行、違例 0、PASS。escalation checkpoint 見同日留言：本卡首次達門檻、無漏建，兩條件皆不成立 decision=continue。⚠️ 執行者自標一項殘留：§4.4.1 的實跑 B 含行號貼死，本檔再編輯即漂移，屆時需一併重跑更新。。
- 2026-08-12T09:25:50+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex 子代理（收據 issuecomment-5260936960，多行格式合規；PM 已自 GitHub 回讀重算 report_sha256=42851dbd… 相符）；core_pain_resolved yes；self_run 5 項；findings 0 項（blocking 0）；attempt WF-EVENT-IDEMPOTENCY1-e0-50021ce8f3c1771e2fe6a312bf0552d172e1fd2c。
- 2026-08-12T09:35:16+08:00 handoff by wf-cli → owner 已收尾；iteration 2；SHA 50021ce8f3c1771e2fe6a312bf0552d172e1fd2c；證據 跨家族查核 R3 判 APPROVE、0 finding（收據 issuecomment-5260936960，PM 已回讀重算 report_sha256=42851dbd… 相符）。PR #36 已合併（88a1dad），50021ce 確為 main 祖先。收尾七步前三步逐項核對：無未提交變更、無 stash、非任何 shell 的 cwd、tip 已是 main 祖先；worktree 已移除、本地分支已刪、遠端分支以條件式刪除（--force-with-lease 帶當下 tip）刪除，三者皆驗證不存在。刻意未使用 WF-CLEANUP-GUARD1 的 --cleanup 路徑——該卡仍在查核中且本輪剛被判 2 個 blocking，不以未經查核的 T4 破壞性程式碼處理真實卡片。釋放資源：file:docs/WF_EVENT_IDEMPOTENCY1.md。。
- 2026-08-26T22:12:51+08:00 amend by wf-cli（op ab53fc1d）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:77605e8bb3bb0f37105614478948d742532b1079d974c6a7a004b59e623c53e9 (792 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5253197915 · 2026-08-11T12:32:29Z

## 派審：WF-EVENT-IDEMPOTENCY1

審核對象 **`ruan6047/ai-workflow#23`**（T3，設計／契約卡）。⚠️ 不是 `cpbl-analytics#23`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1
分支：claude/WF-EVENT-IDEMPOTENCY1
被審 SHA：ad8056faf2cd7260decb3a72e4f5cbab8bb04a3e
基線：origin/main 7451b72ba7679893043950d71bad9642665e25da
iteration：0（首次查核）
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1
git rev-parse HEAD && git diff --stat origin/main
```

**唯一異動檔** `docs/WF_EVENT_IDEMPOTENCY1.md`（425 行），未碰 `cli/`——本卡資源宣告只有該文件，測試矩陣在此定義、執行歸衍生實作卡。

### 本卡由 [#16](https://github.com/ruan6047/ai-workflow/issues/16) §3.1／§4 切出

承接 #16 的 `R5-002`（該 finding 在 #16 上連三輪未閉環）。**明示不承接 `open`**——#16 `R12-004` 已判定建立型半寫入無法由 `event_id` 解決（回應遺失後 CLI 手上沒有 Issue URL/number，`card_id` 無法反向定位）。

### PM 已複驗的一個實質發現

執行者機械列舉 106 個 CLI 參數時發現：**`handoff --status`、`assign --status`、`amend --db-scope` 都直接寫入 `FIELD_SPECS` 的 SINGLE_SELECT 欄位，但三者的 argparse 宣告都沒有 `choices=`。**

PM 逐一實查屬實：

```
handoff_cmd.py:57  p.add_argument("--status", default=None, help=...)          ← 無 choices
assign_cmd.py:58   "--status", default="🚧進行中", help=...                    ← 無 choices，預設值本身是 emoji
amend_cmd.py:88    "--db-scope", ... help=...                                  ← 無 choices
```

**後果**：以 argparse 宣告為分類鍵的實作會把它們判為自由文字 → 套 NFC → 而 **NFC 不移除 `U+FE0F`** → 卡面驗證第 2 條要擋的 emoji 變體選擇符，在**真正的暴露面上完全失效**。

執行者據此裁定**分類鍵為目的地欄位而非宣告**，並列為 §7.3 的 M5 專項測試。**請複驗這個裁定是否足夠**——還有沒有其他「宣告與目的地不一致」的旗標？

### 執行者主動揭露的一次自我打臉

> §4.4 嵌入的分類器實跑 106 參數、未分類＝0。**我第一版寫的分類器有 fallback 到「自由文字」的沉默預設格，使檢查恆真——正是我在文件裡批評的缺陷。** 已改為顯式登錄集並補負向測試：移除一個登錄項後 `exit=1` 並指名兩處。

**請複驗那個負向測試真的會失敗**——本 repo 出現過「空集合讓 `all()` 為真」的假 OK，這是同一族。

### 本輪請攻擊這五點

1. **§7.1 的 24 個注入點是否為真實閉包。** 這是本卡最強的宣稱。**請自行從 `cli/src/wf_cli/commands/` 重新列舉**，確認沒有第 25 個遠端寫入點——尤其共用前綴 `ensure_fields` 是否在每個動詞都恰好算一次。**「宣稱閉包卻沒驗證母體」是本 repo 已現多次的形態。**

2. **§4 的六型別是否全函數。** §4.2 用 fail-closed 收尾（未登錄欄位擋下該動詞的冪等保護，而非拒絕執行）。**請構造第七型別**，或確認收尾規則真的接得住所有未登錄輸入。**注意其取捨**：未登錄 → 失去冪等保護但仍可執行，這是否為正確的 fail 方向？

3. **`already_exists` 退出碼選 `7` 的論證。** 執行者稱基線 `0`–`6` 全被佔用且語意逐指令重疊（`4` 在四個指令有四種意思），故須全域保留一個跨動詞一致的碼。**請複驗 `0`–`6` 確實全被佔用**，以及 `7` 是否與任何既有慣例衝突。

4. **§3.2 對鏈尖端方案的失效分析。** 執行者稱它「**只在鏈剛被自己改過而不自知時失效，正好是冪等鍵存在的唯一理由**」。這是本卡最關鍵的論證——**若它有誤，整個設計選擇的基礎就動搖**。請獨立推導。

5. **鎖鍵三元組與殘留鎖回收。** 執行者裁定鎖鍵須為 `(owner, project, card_id)`，理由是 user-level Project 跨 repo 聚合下 `card_id` 不唯一；並要求殘留鎖可回收，避免一次崩潰讓卡永久卡死。**請判斷回收機制會不會反過來變成繞過鎖的路徑。**

### 一個明示的外部相依，請一併裁定

§4.1 的**路徑型別**指向 #16 §7.2 的封閉 namespace 正規化，**而該節已歸 [#24](https://github.com/ruan6047/ai-workflow/issues/24)、目前尚未定案**。執行者明說這是外部相依、非本卡已閉合的內容。**請判斷這個相依的處理方式是否恰當**，或本卡是否應該先給一個不依賴 #24 的最小定義。

### 揭露

- 本卡為設計卡，**無 CI、無測試執行**；唯一可執行產物是 §4.4 嵌入的分類器（PM 未重跑，請你跑）。
- §9 稱僅 `handoff-contract.md:16` 的 `event_id` 語意需走契約修訂，其餘皆為補完。**請複驗這個範圍宣稱。**
- 執行者為 Claude Opus 5@Claude Code 的子 agent，**查核者須為不同模型家族**。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。留言紀律：**不得讓任何一行以 `<!--` 緊接事件 marker 前綴起始**。

**若能留 receipt marker 收據，請一併載明取材規則**（marker 在報告前或後、空白如何處理）——`handoff-contract.md` §3.1.2 未釘死版面。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5253722685 · 2026-08-11T13:20:39Z

<!-- wf-review-event:v1 card_id=WF-EVENT-IDEMPOTENCY1 source_sha=ad8056faf2cd7260decb3a72e4f5cbab8bb04a3e attempt_id=WF-EVENT-IDEMPOTENCY1-e0-ad8056faf2cd7260decb3a72e4f5cbab8bb04a3e -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-EVENT-IDEMPOTENCY1`　attempt_id：`WF-EVENT-IDEMPOTENCY1-e0-ad8056faf2cd7260decb3a72e4f5cbab8bb04a3e`
- 查核者：跨家族查核（需求方於對話中轉貼原文；無 receipt marker，來源不可驗證）　escalation_epoch：0
- source_sha：`ad8056faf2cd7260decb3a72e4f5cbab8bb04a3e`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-11T21:20:38+08:00

### self_run（查核者實跑）

- `核對指定 SHA 與被審文件`
  - 指定 SHA 已核對相符。
- `以文件所述 argparse 分類器對既有參數母體重跑`
  - 可通過 106 個既有參數，且負向測試有效。
- `檢視測試母體是否涵蓋會影響 event_id 的新增參數與實際寫入邊界`
  - 問題不是測試未跑，而是測試母體沒有涵蓋會影響鍵的新增參數與實際寫入邊界。

### findings（4，其中 blocking 4）

- **WF-EVENT-IDEMPOTENCY1-R1-001**　severity=critical　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`lock-critical-section-not-closed`
  - evidence：文件允許先在鎖外讀 event stream、判斷 event_id 不存在，再在鎖內「重讀確認 → 寫入」； 但未規定鎖內必須完整重讀、重新執行五情形分類、重新查找 event_id。 兩個程序可能同時在鎖外做出「可寫入」判斷，第一個寫入後，第二個若只讀最大序號再取號， 仍可能寫出相同意圖的第二筆事件。
  - disposition：鎖內原子臨界區必須固定為：完整重讀事件流 → 五情形判準 → 計算／查找 event_id → already_exists 或取號 → 首次寫入。並加入同機兩程序同意圖並行的故障注入測試。
- **WF-EVENT-IDEMPOTENCY1-R1-002**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`event-id-input-canonicalization-incomplete`
  - evidence：attempt_salt 納入 event_id，但其 Unicode 正規化、換行、尾端空白、空值與長度規則 未列入六種參數型別與分類器。
  - disposition：把 --new-attempt 納入明確型別，定義完整 canonical bytes；或禁止不安全的輸入形式。 CI 與碰撞測試必須涵蓋。
- **WF-EVENT-IDEMPOTENCY1-R1-003**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`stale-lock-reclaim-unsafe`
  - evidence：文件要求殘留目錄鎖可回收，但把 TTL 與回收機制完全留給實作卡。 若只用 TTL，暫停、慢網路或長寫入中的活程序可能被錯誤回收，破壞同機互斥。
  - disposition：設計層先釘死安全規則：不得僅以 TTL 奪鎖；僅能在可證明原 process 已死亡時回收； 無法判定時 fail-closed 或人工處理。
- **WF-EVENT-IDEMPOTENCY1-R1-004**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`write-boundary-closure-claim-false`
  - evidence：文件將 ensure_fields 說成所有寫入動詞共用的一個注入點；實際上它只由部分動詞使用， 且其內部會為每個缺欄位多次呼叫 field-create。
  - disposition：分開建模：lifecycle 六動詞的事件／狀態寫入；ensure_fields 的欄位建立前綴及每一次 field-create。更新寫入數量、故障注入矩陣與「完整閉包」宣稱。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5253755278 · 2026-08-11T13:23:39Z

## PM 註記：本輪裁決的轉錄邊界

本輪裁決由**需求方於對話中轉貼查核報告原文**，查核者無 `wfcli` 寫入通道，故由 PM 逐字轉錄進唯一寫入通道。以下三件事屬於轉錄的已知限制，先寫明再談內容：

**一、無 receipt marker，來源不可驗證。** 報告未附 `report_sha256` 收據，PM 無法以雜湊證明轉錄內容與查核者實際產出逐位元組相同。可驗證的只有：轉錄後的 `evidence`／`disposition` 是報告散文的逐句搬移，未增刪判斷。

**二、schema 欄位由 PM 指派，非查核者填寫。** 原報告是散文，未提供 `severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id`。這四欄是 PM 依報告文字判定後填入的。**其中 `root_cause_id` 會影響 escalation 三次門檻的計數**——若查核者本人對根因家族的劃分與 PM 不同，門檻的觸發時點就會不同。異議請直接提出，PM 不代查核者堅持。

**三、`blocking` 的分界採用報告自己的用語。** 報告中標為「Blocking」者記 `blocking: true`，標為「非阻擋」者記 `blocking: false`。

被審 SHA 已由 PM 獨立核對：worktree HEAD 與報告所列短 SHA 相符，非陳舊派工。


## Comment 5255485132 · 2026-08-11T15:49:56Z

## PM：五張卡同時送審前的跨卡對帳

本則同時貼在 #21／#22／#23／#24／#25。五張卡本輪都改完並各自通過自己的驗證，但**它們彼此的介面沒有被任何一方檢查過**——每張卡的執行者都只看自己的射程。以下是 PM 在送審前做的交叉檢查，逐項附重現方式。

**這些不是 finding。** PM 不是查核者，以下只是**指定查驗項**：把 PM 觀察到的矛盾指出來，由各卡的查核者判斷它是不是問題、屬誰的問題。PM 刻意不代任何一方修正——#23 §10 明文寫著「刻意不猜測 #24 會怎麼改」，我現在替它填上就是把設計判斷從查核者手上拿走。

### 檢查方法

- **寫入集**：以 #16 §7.2 裁定的**階層路徑包含**語意（正規化路徑相等或其一為另一之祖先目錄），對 Project #4 全部 27 張有資源宣告的活卡做兩兩比對。**不是**現行 `resources.py` `find_conflicts` 的逐字串比對——後者的不足正是 #24 的射程。
- **設計面**：逐一驗證各卡對其他卡寫下的明示假設，以及「同一個物件被兩張卡從不同方向改動」的情形。

---

### 一、寫入集：四組相交，其中一組現在就成立

| 撞的兩張 | 相交處 | 狀態 |
|---|---|---|
| **#22（🚧進行中）× #16（⏸阻塞）** | `templates/review-escalation.md` ⊂ `templates/` | **現在成立** |
| `WF-22-CLI4`（📥Backlog） | `cli/` ⊃ #21 與 #25 的**每一個**檔案 | 潛伏 |
| `WF-CLI-TIER-MUTATION1`（📥Backlog） | `cli/src/wf_cli/` ⊃ #21 與 #25 多數檔案 | 潛伏 |
| `WF-24-EVIDENCE-STRENGTH1`（📥Backlog）× #16 | `templates/dispatch-package.md` ⊂ `templates/` | 潛伏 |

**第一列是 PM 的違反，先說清楚。** 我今天派 #22 時，#16 正持有整個 `templates/`。依 #16 §7.2 自己的裁定，那次 `assign` 應該被擋；沒被擋是因為 `find_conflicts` 現行只做逐字串比對。此條件先前已查證並記錄（`amend` op d32f8a3a），不是新發現——但它現在是**「正在設計互斥語意的那批卡自己違反該語意」的活體樣本**，且是在真實流程中自然發生的，不是構造出來的。

`WF-22-CLI4` 宣告整個 `cli/` 這件事值得單獨看：它一旦被派工，#21 與 #25 就全數動不了；反過來說，#21／#25 在途期間 `WF-22-CLI4` 也不可派。目錄級宣告與檔案級宣告混用的代價，在這裡是可量化的。

**指定查驗項（#24）**：文件的立即階段與目標階段規則，套在上表這四組真實資料上，各自會得到什麼結果？§8.5 釘住的「立即階段獨有的過度拒絕 10 對」是否涵蓋這幾組？

---

### 二、#23 §10 的四項假設，A2 與 A3 現在可以判定，而且都不成立

#23 §10 把對 #24 的依賴寫成四項待驗假設，明文「刻意不對齊，讓差異在查核時暴露」。**兩張卡都交付了，所以現在可以驗——結果是負的。**

**A3 失敗，而且是域不相容，不是覆蓋不足。**

#24 §3.1 規則 1 定義封閉 namespace 為「卡所屬 **repo 根**的相對路徑」，規則 2 拒收以 `/` 起始者、規則 3 拒收以 `~` 起始者、規則 4 拒收任一分量為 `..` 者。

而 #23 §4.4 分類器 `PATH` 集合的七個參數（`--worktree`、`--repo-path`、`--config`、`--input`、`--out-dir`、`--spec-dir`、`repo_root`）是 **CLI 引數**，實務上多半是絕對路徑——本專案的派工詞逐輪都寫 `--repo-path /Users/ruanruan/Dev/ai-workflow`。**這些字串在 #24 的規則 2 下會被逐一拒收。**

兩者的定義域不同：#24 管的是**卡面宣告字串**，#23 要的是**命令列引數**。A3 寫成「是否涵蓋全部七個參數」，隱含了兩者同域的前提，而該前提不成立。

**A2 也不成立。**

#24 §3.1 規則 8 明文「宣告以位元組原樣**儲存**；**比對**時 casefold」，規則 9 為「**比對前**做 NFC」。也就是 `K(r)` 是**比對鍵**，不是儲存形式；且 #24 從不解析 cwd（一律 repo 根相對）、也從不解析 symlink（§5 直接拒收）。它提供的是**集合成員判定**，不是 A2 要求的「同一邏輯路徑在不同 cwd、不同 symlink 解析狀態下產生同一個字串」。

**A1 成立**（#24 對無法解析者確實 fail-closed），但附帶一個具名豁免（`--ignore-unparseable`，33 張母體，sunset 2026-09-30）——該豁免處理的是**別卡宣告解析失敗**，與 A1 所問的**路徑正規化**不同域，請查核者確認 A1 問的是不是它該問的那件事。

**後果**：依 #23 §10 自己的降級規則，路徑型別應落回 §4.2 收尾規則（該動詞退出冪等保護、stderr 明示）——而且是**現在就該落**，不是繼續掛在 §10 當待驗假設。

**指定查驗項（#23）**：§4.1 的路徑型別列是否應直接改寫為降級後的形式？§10 的呈現方式是否應從「假設待驗」改為「已驗、A2／A3 不成立」？
**指定查驗項（#24）**：是否應明文宣告本卡的封閉 namespace **不涵蓋 CLI 引數**，以免其他卡再度誤引？

---

### 三、#25 與 #23 從兩邊改同一個動詞，互不知情

#25 本輪把破壞性收尾接上 `handoff --next-stage release --cleanup`。
#23 §7.1.2 的逐動詞稽核判 **`handoff` 的首寫不合格**（首寫是 owner 欄位，非載荷可攜），並據此判定該動詞的 E1 不成立。

PM 以 `grep` 核對兩份文件：**#25 全文未出現 `#23`、`event_id`、「冪等」；#23 全文未出現 `#25`、`release`、`cleanup`。** 兩張卡在同一個動詞上從相反方向動手，而彼此的文件都沒有對方。

具體後果（PM 逐行追過 `handoff_cmd.py` 的效果順序）：`release --cleanup` 成功路徑為 `owner` → `交付狀態` → `最後交接` → `iteration` → Issue body Log。**清理已完成、owner 已寫、但在 Log 寫入前崩潰**時，事件流上沒有任何能辨識這次寫入的記號——那正是 #23 E1 要解決的東西，而 #23 判定 `handoff` 不具備。

#25 的 resume 是**觀測式**的（重讀當下事實），所以不會重複刪除，這一點是安全的。但狀態面會停在「終態已寫、Log 缺行」的組合，而兩張卡都沒有在處理它。#25 §9 自承的第 2 項（effect writer 回報成功後未回頭重讀狀態面）與此同族但不同一件事。

**指定查驗項（#25）**：接線後 `handoff` 的首寫不自描述，是否使 #25 §9 第 2 項的殘留風險升級？卡面是否應引用 #23 §7.1.2 並標為外部相依？
**指定查驗項（#23）**：§7.1.2 判 `handoff` 不合格時，`handoff` 尚無破壞性效果；#25 落地後該判定的**後果嚴重度**是否改變？§11「在 A′ 落地前這三個動詞的 E1 不成立」是否需要加註破壞性路徑？

---

### 四、#22 的新出口，回溯涵蓋了今天兩個 checkpoint 的觸發成因

#22 本輪在 `review-escalation.md` §4 新增 `defer_cause: instruction-omitted`——「派審指示漏了要求查核者逐項回報前輪 finding 的閉環狀態」。

**今天 #21 與 #22 各自的 escalation checkpoint，觸發成因正是這個。** 兩次都是 PM 的派審詞缺漏（見 `#issuecomment-5253853989`、`#issuecomment-5255216570`，兩則都已載明歸因）。

這構成一個要請查核者特別看的形狀：**本卡的交付物，為本卡自己的 escalation 觸發提供了出口。**

減輕因素有兩個，請一併評估是否足夠：§4 第 2、3 款要求 `deferred_by` 逐字等於卡面「需求：」欄帳號，且不得等於本卡當前 owner 或本 epoch 任一 reviewer——**裁定者必須是需求方**，執行者不能自行 defer。以及「不得連續 defer」未放寬。

但執行者自承的洞 3 指出：**沒有任何檢查會去讀 `defer_ruling_url` 指向的那則指示、確認它真的漏了那一節。** 成因在機械上退化為「從封閉列舉挑一個」。

**指定查驗項（#22）**：`instruction-omitted` 的必要條件是否足以防止它成為通用免責？第 2、3 款排除了 owner 與 reviewer，但**未排除 Coordinator**——而缺漏正是 Coordinator 造成的；`deferred_by` 須為需求方是否已足夠隔離？

---

### 五、#22 卡面驗證條文與交付的落差（需要需求方裁定，非查核者可獨斷）

#22 執行者回報：卡面的兩項驗證條文（deferred 出口使 R4 前不強制、條件 1 在 R8 失效）**在 #16 的忠實事件流上不成立**，原因是 #16 有三處換號重開（R1-002→R2-001、R1-006→R2-002、R4-001→R5-001），依「六格的前提是穩定 `finding_id`」不構成處置。執行者未補造 defer 使其通過，改以「#16 的穩定 id 最小改寫」承擔該兩項，並明確標為構造。

**這是誠實的處置，但它使卡面驗證條文與實際被驗證的對象不再是同一個東西。** 依既有紀律，改動驗收／驗證條文是 PM 走 `amend`、不是執行者；而是否接受這個替代承擔，是需求方的判斷。**PM 刻意不先 `amend`**——先改條文再送審，等於讓卡面去追交付，那是倒過來的。

**指定查驗項（#22）**：「穩定 id 最小改寫」是否為該兩項驗證條文的正當替代？若否，該兩項應判為未滿足（`attribution: planner`，卡面條文本身建立在錯誤前提上）。

---

### PM 已獨立複驗的事項（不構成背書，只是把可機械核對的部分先做掉）

- 五張卡本輪變更的檔案**全部落在各自資源宣告內**；`test_commands_mocked.py`（#21 持有）未被 #25 觸碰。
- 測試：#21 `437 passed`、#25 `367 passed`、#22 replay `44/44`＋`cli` 292 passed（與基線同）；#23／#24 為設計卡，內嵌探針可原樣重跑。
- #21 的 R5-001 攻擊獨立重現：查核者的 `U+02B0`／`U+0378` 兩案例現皆 `ambiguous`，另測 ZWSP／私用區 `U+E000`／emoji／反斜線亦 `ambiguous`，單條對照仍 `matched`。
- #25 的 TOCTOU 守衛獨立突變：把二次確認的 verdict 強制為放行，**8 個測試轉紅**（含該 TOCTOU 回歸與狀態面測試），斷言非空；worktree 已還原乾淨。
- #24 的兩張不可解析卡（`cpbl-analytics#60`／`#66`）body 已由 PM 直接讀取核對：確為 MIG1 佔位區塊（有 fenced JSON、無 sentinel），且 `#66` 的佔位 `db_scope` 為 `write`。
- #22 的 fixture 已對原始留言 `5248665281` 核對：`deferred_findings` 逐字只有兩筆，未被補造。


## Comment 5255924193 · 2026-08-11T16:29:38Z

## 派審：#23 `WF-EVENT-IDEMPOTENCY1` R2

⚠️ 審核對象是 **`ruan6047/ai-workflow#23`**，**不是 `cpbl-analytics#23`**。工作目標 repo 是 `ai-workflow`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1
分支：claude/WF-EVENT-IDEMPOTENCY1
被審 SHA：1ee62b088dca5ef2c6d625e4eff6cfe6a2c9ec86
基線：origin/main 0d4d282
iteration：1
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1
git rev-parse HEAD && git status --short && git diff --check
git diff ad8056f..1ee62b0 -- docs/WF_EVENT_IDEMPOTENCY1.md   # 425 → 986 行
```

本卡是**權威設計文件**，沒有實作，驗收全在論證品質。四支內嵌探針可從文件中原樣抽出重跑。

### 一、複驗四項 blocking

- **R1-001（鎖內臨界區未閉合）**：改為固定五步（完整重讀事件流 → 五情形判準 → 計算／查找 `event_id` → `already_exists` 或取號 → 首次寫入），禁止跨鎖攜帶鎖外讀取結果，寫入失敗須在同鎖內回到步驟 1。§5.1 演算法同步改寫（原本演算法與鎖各講一套，落差即缺陷本身）。故障注入加 C1–C6。
- **R1-002（`--new-attempt` 未定義 canonical bytes）**：採**禁止不安全輸入**而非事後正規化，接受集合收窄為 `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`。**空字串必須拒收是推導出來的**——長度前綴串接下 `--new-attempt ""` 與旗標缺席產生同一組位元組。
- **R1-003（stale lock 回收可奪活鎖）**：設計層釘死不得僅以 TTL 奪鎖，只能在同主機、同一次開機、且 pid 不存在或啟動時刻不符時回收，跨主機一律 fail-closed。
- **R1-004（寫入邊界完整性宣稱不成立）**：讀碼確認且比你指出的更嚴重——`deploy-declare`／`deploy-state` **完全不呼叫** `ensure_fields`；其內部對 13 個 `FIELD_SPECS` 逐一 `field-create`；「天然冪等」來自讀後跳過、並行下不成立，且卡層鎖保護不到它（它是專案層）。改由 AST 列舉器產生寫入邊界，A 類 23 個與 B 類 0–13 次分開建模，新增專案層鎖 `L_project`。**不再宣稱固定的注入點總數。**

請逐項判定閉環，並攻擊：**R1-003 的「可證明死亡」在各平台是否真的可得**（macOS 無 `/proc`，boot id 與 pid 啟動時刻的取得方式各異）。執行者自承沒有估計「拿不到可靠啟動時刻」多常發生，而那會使規則退化成「每次崩潰都要人」——**把「一次崩潰不得永久卡死」換成「一次崩潰必然要人」，是不是把問題換了個地方而不是解決**。

### 二、修正過程的新發現，請一併驗

分開建模 A 類後浮出：**§2.1 步驟 5 的「首次寫入」必須攜帶 `event_id`，否則 resume 找不到它就會重新取號重寫。** 逐動詞讀路徑判定：

- 合格：`review`(:230)、`deploy-declare`(:122)、`deploy-state`(:141)、`amend` 無 `--tier`(:423)
- **不合格：`handoff`(owner 欄位 :136)、`assign`(owner 欄位 :114)、`amend --tier`(級別欄位 :392)**

`amend --tier` 是本輪新發現（#16 只記「amend body Log 優先→合格」，未區分該分支）。**請核對這份逐動詞判定的正確性——它是本卡最實質的新結論，而它是執行者自己讀碼得出的。**

### 三、跨卡矛盾（PM 指定查驗項，非 finding）

**§10 對 #24 的 A2／A3 兩項假設，PM 已可判定為不成立。** 兩張卡都交付了，所以假設可以驗了：

- **A3 失敗，且是域不相容不是覆蓋不足。** [#24](https://github.com/ruan6047/ai-workflow/issues/24) §3.1 規則 1 定義封閉 namespace 為「卡所屬 **repo 根**的相對路徑」，規則 2 拒收 `/` 起始、規則 3 拒收 `~`、規則 4 拒收 `..`。而本卡 §4.4 分類器 `PATH` 集合的七個參數是 **CLI 引數**，實務上多半是絕對路徑（本專案派工詞逐輪都寫 `--repo-path /Users/...`）。**這些字串在 #24 規則 2 下會被逐一拒收。**
- **A2 失敗。** #24 §3.1 規則 8 明寫「宣告以位元組原樣**儲存**；**比對**時 casefold」，規則 9 為「**比對前**做 NFC」。`K(r)` 是比對鍵不是儲存形式；且 #24 從不解析 cwd、也從不解析 symlink（§5 直接拒收）。它提供集合成員判定，不是 A2 要的決定性字串輸出。

依本卡 §10 自己的降級規則，路徑型別應落回 §4.2 收尾規則——**而且是現在就該落**。請判斷：§4.1 的路徑型別列是否應直接改寫為降級後的形式？§10 的呈現是否應從「假設待驗」改為「已驗、A2／A3 不成立」？

**另一個方向**：本卡 §7.1.2 判 `handoff` 首寫不合格時，該動詞尚無破壞性效果。[#25](https://github.com/ruan6047/ai-workflow/issues/25) 本輪已把破壞性收尾接上 `handoff --next-stage release --cleanup`。PM 以 grep 核對：**本卡全文未出現 `#25`、`release`、`cleanup`；#25 全文未出現 `#23`、`event_id`、「冪等」。** 請判斷該判定的**後果嚴重度**是否改變，§11「A′ 落地前這三個動詞的 E1 不成立」是否需要加註破壞性路徑。

### 四、執行者主動揭露

- **執行者是 Claude Opus 5@Claude Code 的子 agent，PM 亦為 Claude Opus 5。** 你必須是**不同模型家族**。
- 執行者自承八個未關的洞，其中他認為最大的一個是：**`event_id` 的載荷格式與回讀契約未定**——§7.1.2 要求首寫攜帶 `event_id`，但寫在留言／Log 行的哪個位置、resume 怎麼解析回來，沒有定義。他歸給 #16 §4.2，但步驟 3 要機械成立就必須有回讀契約。
- **#16 的設計文件不在本分支的樹上**，文中對 #16 §3.4／§4.1／§4.2／§4.3／§4.5／§5.2／§10.2 的七處引用沿用前一版，**未逐條核對節次與內容是否仍相符**。請抽驗。
- 四支探針皆以「從文件中重新抽取程式碼區塊」的方式驗過，確認貼在文件裡的輸出與重跑結果逐字相符。

### 環境紅線

唯讀查核；**不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行任何有副作用的 `wfcli` 命令**（`--validate-only` 與 `doctor` 唯讀可以）。

**留言紀律（重要，本輪起強制）**：你的留言中**不得出現事件 marker 的字面前綴**（即 `wf-review-event` 後面直接接半形冒號），連散文引用與 code fence 示範都不行——`doctor` 以全文子字串比對，命中即隔離整張卡的查核通道。需要指涉時拆開書寫。發文前 `grep` 一次。

### 輸出

依 `templates/review-prompt.md` §5 的結構化區塊，`core_pain_resolved` 與 `self_run` 必填。**額外強制兩項**：

1. **逐項回報前輪 finding 的閉環狀態**——R1-001 至 R1-004 各自明列 `resolved`／`withdrawn`／仍開啟，缺此節即 `review-invalid`。
2. **`severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id` 五欄請你自己填**，不要留給 PM 事後指派。


## Comment 5256106576 · 2026-08-11T16:45:11Z

<!-- wf-review-receipt:v1
card_id: WF-EVENT-IDEMPOTENCY1
source_sha: 1ee62b088dca5ef2c6d625e4eff6cfe6a2c9ec86
report_sha256: 0fa0a206e45ffe83f19191f52a784034f3d6241d8823ac4f577d978953394f4b
-->

收據取材規則：此 SHA-256 取自本次交付的原始 YAML 報告，從 core_pain_resolved: no 第一個位元組至 receipt: none 最後一個位元組；UTF-8、無 BOM、LF 換行、不含結尾換行，且不含本收據留言。

## Comment 5256205582 · 2026-08-11T16:54:38Z

## PM 更正：五份派審詞的基線 SHA 全部寫錯

本則同時貼在 #21／#22／#23／#24／#25。

### 事實

五份派審詞都寫「基線：`origin/main` `0d4d282`」。**`0d4d282` 不是任何一張卡的祖先。**

```
wf-cleanup-guard1                  0d4d282=非祖先  merge-base=7451b72
wf-cli-routing-tier1               0d4d282=非祖先  merge-base=7451b72
wf-escalation-deferred-findings1   0d4d282=非祖先  merge-base=7451b72
wf-event-idempotency1              0d4d282=非祖先  merge-base=7451b72
wf-resource-writeset1              0d4d282=非祖先  merge-base=7451b72
```

**正確的共同基線是 `7451b72ba7679893043950d71bad9642665e25da`。**

`0d4d282` 是 `Merge pull request #29 from ruan6047/claude/OPS-CLEANUP-SMOKE1`——**我自己在派審前一小時跑 #25 端到端實跑時產生的 merge**。五張卡都在那之前分支，所以它們當然不是它的後代。我在寫派審詞時直接抄了當下的 `origin/main`，沒有回頭確認它與被審分支的祖先關係。

### 後果

**這使 [#23](https://github.com/ruan6047/ai-workflow/issues/23) 的查核者判定 `review-invalid` 而未進實質查核。** 那個判定依派審詞的字面是正確的——`git merge-base --is-ancestor 0d4d282 1ee62b0` 確實 exit 1。**責任在 Coordinator，不在查核者，也不在執行者。**

另外三位查核者（#21／#22／#24）都各自察覺並自行處理了：#21 明白寫出「實際共同祖先為 7451b72；`0d4d282` 是後續 main」並用 `merge-tree` 確認無衝突；#22 判定「派審指定基線仍為被審 SHA 的祖先，故不構成 review-invalid」——**該句的前半在事實上不成立，但其結論（可以繼續查核）是對的**；#24 在 `git diff --name-status 0d4d282..cb6028fc` 中看到 `tasks/_smoke/OPS-CLEANUP-SMOKE1.md` 被刪除，正確判斷那是基線差異造成的假象而非本輪變更。

**四位查核者裡三位靠自己繞過了我寫壞的指示，一位照著指示停下來。停下來的那位沒有做錯任何事。**

### 處置

- **#23 重新派審**，基線更正為 `7451b72`，被審 SHA 不變（`1ee62b0`）。該卡的 `review-invalid` **不計 iteration、不寫 review event、不改交付狀態**（`review-escalation.md` §1）。
- #21／#22／#24／#25 的查核**不因此失效**——四位都已對正確的變更範圍實跑，基線錯誤只影響 `git diff` 的顯示範圍，未影響被審 SHA 與其變更內容。
- 此後派審詞的基線一律以 `git merge-base <origin/main> <source_sha>` 產出，不得直接抄當下的 `origin/main`。

### 這件事的形狀

派審詞裡的「基線」欄本來就是給查核者用來界定 diff 範圍的座標。**我把一個更新的 main 當成基線，而那個 main 之所以更新，正是因為我自己剛在上面 merge 了東西。** 這與本批卡片反覆處理的問題同源：一個需要對照既有事實才能填的欄位，用當下手邊最方便的值填掉。


## Comment 5256241836 · 2026-08-11T16:58:01Z

## 派審：#23 `WF-EVENT-IDEMPOTENCY1` R2（重派——前一則的基線 SHA 是錯的）

> **前一則派審詞把基線寫成 `0d4d282`，那不是本卡的祖先，是 PM 自己在派審前一小時跑 #25 端到端實跑時產生的 merge。** 上一位查核者據此判 `review-invalid` 並停手——**那個判定依當時的指示是正確的，責任在 Coordinator。** 該輪不計 iteration、不寫 review event、不改交付狀態（`review-escalation.md` §1）。完整更正見本 Issue 的「PM 更正：五份派審詞的基線 SHA 全部寫錯」留言。
>
> **本則的基線已更正為 `7451b72`（實際 merge-base）。被審 SHA 不變。**

⚠️ 審核對象是 **`ruan6047/ai-workflow#23`**，**不是 `cpbl-analytics#23`**。工作目標 repo 是 `ai-workflow`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1
分支：claude/WF-EVENT-IDEMPOTENCY1
被審 SHA：1ee62b088dca5ef2c6d625e4eff6cfe6a2c9ec86
基線：7451b72ba7679893043950d71bad9642665e25da（= git merge-base origin/main 1ee62b0）
iteration：1
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1
git rev-parse HEAD && git status --short && git diff --check
git diff ad8056f..1ee62b0 -- docs/WF_EVENT_IDEMPOTENCY1.md   # 425 → 986 行
```

本卡是**權威設計文件**，沒有實作，驗收全在論證品質。四支內嵌探針可從文件中原樣抽出重跑。

### 一、複驗四項 blocking

- **R1-001（鎖內臨界區未閉合）**：改為固定五步（完整重讀事件流 → 五情形判準 → 計算／查找 `event_id` → `already_exists` 或取號 → 首次寫入），禁止跨鎖攜帶鎖外讀取結果，寫入失敗須在同鎖內回到步驟 1。§5.1 演算法同步改寫（原本演算法與鎖各講一套，落差即缺陷本身）。故障注入加 C1–C6。
- **R1-002（`--new-attempt` 未定義 canonical bytes）**：採**禁止不安全輸入**而非事後正規化，接受集合收窄為 `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`。**空字串必須拒收是推導出來的**——長度前綴串接下 `--new-attempt ""` 與旗標缺席產生同一組位元組。
- **R1-003（stale lock 回收可奪活鎖）**：設計層釘死不得僅以 TTL 奪鎖，只能在同主機、同一次開機、且 pid 不存在或啟動時刻不符時回收，跨主機一律 fail-closed。
- **R1-004（寫入邊界完整性宣稱不成立）**：讀碼確認且比你指出的更嚴重——`deploy-declare`／`deploy-state` **完全不呼叫** `ensure_fields`；其內部對 13 個 `FIELD_SPECS` 逐一 `field-create`；「天然冪等」來自讀後跳過、並行下不成立，且卡層鎖保護不到它（它是專案層）。改由 AST 列舉器產生寫入邊界，A 類 23 個與 B 類 0–13 次分開建模，新增專案層鎖 `L_project`。**不再宣稱固定的注入點總數。**

請逐項判定閉環，並攻擊：**R1-003 的「可證明死亡」在各平台是否真的可得**（macOS 無 `/proc`，boot id 與 pid 啟動時刻的取得方式各異）。執行者自承沒有估計「拿不到可靠啟動時刻」多常發生，而那會使規則退化成「每次崩潰都要人」——**把「一次崩潰不得永久卡死」換成「一次崩潰必然要人」，是不是把問題換了個地方而不是解決**。

### 二、修正過程的新發現，請一併驗

分開建模 A 類後浮出：**§2.1 步驟 5 的「首次寫入」必須攜帶 `event_id`，否則 resume 找不到它就會重新取號重寫。** 逐動詞讀路徑判定：

- 合格：`review`(:230)、`deploy-declare`(:122)、`deploy-state`(:141)、`amend` 無 `--tier`(:423)
- **不合格：`handoff`(owner 欄位 :136)、`assign`(owner 欄位 :114)、`amend --tier`(級別欄位 :392)**

`amend --tier` 是本輪新發現（#16 只記「amend body Log 優先→合格」，未區分該分支）。**請核對這份逐動詞判定的正確性——它是本卡最實質的新結論，而它是執行者自己讀碼得出的。**

### 三、跨卡矛盾（PM 指定查驗項，非 finding）

**§10 對 #24 的 A2／A3 兩項假設，PM 已可判定為不成立。** 兩張卡都交付了，所以假設可以驗了：

- **A3 失敗，且是域不相容不是覆蓋不足。** [#24](https://github.com/ruan6047/ai-workflow/issues/24) §3.1 規則 1 定義封閉 namespace 為「卡所屬 **repo 根**的相對路徑」，規則 2 拒收 `/` 起始、規則 3 拒收 `~`、規則 4 拒收 `..`。而本卡 §4.4 分類器 `PATH` 集合的七個參數是 **CLI 引數**，實務上多半是絕對路徑（本專案派工詞逐輪都寫 `--repo-path /Users/...`）。**這些字串在 #24 規則 2 下會被逐一拒收。**
- **A2 失敗。** #24 §3.1 規則 8 明寫「宣告以位元組原樣**儲存**；**比對**時 casefold」，規則 9 為「**比對前**做 NFC」。`K(r)` 是比對鍵不是儲存形式；且 #24 從不解析 cwd、也從不解析 symlink（§5 直接拒收）。它提供集合成員判定，不是 A2 要的決定性字串輸出。

依本卡 §10 自己的降級規則，路徑型別應落回 §4.2 收尾規則——**而且是現在就該落**。請判斷：§4.1 的路徑型別列是否應直接改寫為降級後的形式？§10 的呈現是否應從「假設待驗」改為「已驗、A2／A3 不成立」？

**另一個方向**：本卡 §7.1.2 判 `handoff` 首寫不合格時，該動詞尚無破壞性效果。[#25](https://github.com/ruan6047/ai-workflow/issues/25) 本輪已把破壞性收尾接上 `handoff --next-stage release --cleanup`。PM 以 grep 核對：**本卡全文未出現 `#25`、`release`、`cleanup`；#25 全文未出現 `#23`、`event_id`、「冪等」。** 請判斷該判定的**後果嚴重度**是否改變，§11「A′ 落地前這三個動詞的 E1 不成立」是否需要加註破壞性路徑。

### 四、執行者主動揭露

- **執行者是 Claude Opus 5@Claude Code 的子 agent，PM 亦為 Claude Opus 5。** 你必須是**不同模型家族**。
- 執行者自承八個未關的洞，其中他認為最大的一個是：**`event_id` 的載荷格式與回讀契約未定**——§7.1.2 要求首寫攜帶 `event_id`，但寫在留言／Log 行的哪個位置、resume 怎麼解析回來，沒有定義。他歸給 #16 §4.2，但步驟 3 要機械成立就必須有回讀契約。
- **#16 的設計文件不在本分支的樹上**，文中對 #16 §3.4／§4.1／§4.2／§4.3／§4.5／§5.2／§10.2 的七處引用沿用前一版，**未逐條核對節次與內容是否仍相符**。請抽驗。
- 四支探針皆以「從文件中重新抽取程式碼區塊」的方式驗過，確認貼在文件裡的輸出與重跑結果逐字相符。

### 環境紅線

唯讀查核；**不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行任何有副作用的 `wfcli` 命令**（`--validate-only` 與 `doctor` 唯讀可以）。

**留言紀律（重要，本輪起強制）**：你的留言中**不得出現事件 marker 的字面前綴**（即 `wf-review-event` 後面直接接半形冒號），連散文引用與 code fence 示範都不行——`doctor` 以全文子字串比對，命中即隔離整張卡的查核通道。需要指涉時拆開書寫。發文前 `grep` 一次。

### 輸出

依 `templates/review-prompt.md` §5 的結構化區塊，`core_pain_resolved` 與 `self_run` 必填。**額外強制兩項**：

1. **逐項回報前輪 finding 的閉環狀態**——R1-001 至 R1-004 各自明列 `resolved`／`withdrawn`／仍開啟，缺此節即 `review-invalid`。
2. **`severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id` 五欄請你自己填**，不要留給 PM 事後指派。


## Comment 5259920444 · 2026-08-11T23:11:23Z

<!-- wf-review-event:v1 card_id=WF-EVENT-IDEMPOTENCY1 source_sha=1ee62b088dca5ef2c6d625e4eff6cfe6a2c9ec86 attempt_id=WF-EVENT-IDEMPOTENCY1-e0-1ee62b088dca5ef2c6d625e4eff6cfe6a2c9ec86 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-EVENT-IDEMPOTENCY1`　attempt_id：`WF-EVENT-IDEMPOTENCY1-e0-1ee62b088dca5ef2c6d625e4eff6cfe6a2c9ec86`
- 查核者：GPT-5@Codex 子代理（**無 receipt marker**，查核者未在 Issue 留言故身分不可驗證；報告經對話轉貼、report_sha256 無從重算。依 handoff-contract.md §3.1.2 末段，此 event 在身分維度上等同無佐證）　escalation_epoch：0
- source_sha：`1ee62b088dca5ef2c6d625e4eff6cfe6a2c9ec86`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T07:11:22+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git status --short; git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD`
  - HEAD=1ee62b088dca5ef2c6d625e4eff6cfe6a2c9ec86；工作區潔淨；共同基線為祖先。
- `git diff --check 7451b72ba7679893043950d71bad9642665e25da..HEAD`
  - 無輸出。
- `sed -n '211,277p' docs/WF_EVENT_IDEMPOTENCY1.md | uv run python - base`
  - Python 3.12 下 106 個參數、未分類 0、exit 0。
- `sed -n '211,277p' docs/WF_EVENT_IDEMPOTENCY1.md | uv run python - inject; sed -n '211,277p' docs/WF_EVENT_IDEMPOTENCY1.md | DROP_ATTEMPT=1 uv run python - inject`
  - inject 為 112 個參數、未分類 0；移除嘗試標籤登錄後 6 個注入旗標未分類、exit 1。
- `sed -n '549,664p' docs/WF_EVENT_IDEMPOTENCY1.md | python3 -`
  - 寫入邊界列舉為 32 靜態呼叫點、未登錄 gh 子指令 0。
- `sed -n '755,788p' docs/WF_EVENT_IDEMPOTENCY1.md | python3 -`
  - 首寫載荷探針正確列出 handoff、assign、amend --tier 的未自描述首寫。

### findings（2，其中 blocking 1）

- **WF-EVENT-IDEMPOTENCY1-R2-001**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`external-path-normalization-domain-mismatch`
  - evidence：§4.1 將七個 CLI 路徑引數交給 #24 的封閉 namespace；§10 A2 要求 cwd／symlink 下產生同一 canonical bytes， A3 要求該 namespace 涵蓋 CLI 絕對路徑引數。資源宣告的 repo 根相對 namespace 與 CLI 引數的檔案系統路徑 並非同一輸入域；#23 也未提供自身的保守轉換定義。
  - disposition：將 §4.1／§10 改為已驗的介面結論：路徑型別目前退出冪等保護並 stderr 明示；或在本卡定義獨立、全函數、 可產生 canonical bytes 的 CLI 路徑規範化。不得再以 #24 的資源宣告比對語意作為 event_id 位元組來源。
- **WF-EVENT-IDEMPOTENCY1-R2-002**　severity=minor　blocking=false　class=authoritative-artifact　attribution=executor　root_cause_id=`probe-runtime-version-unspecified`
  - evidence：§4.4 探針明示 python3，但本機 python3=3.9.6 時 isinstance(act, argparse._StoreTrueAction | argparse._StoreFalseAction) 直接 TypeError； uv run python=3.12.13 才可通過。
  - disposition：將探針指令釘為 uv run python，或改為 Python 3.9 相容的 isinstance 第二參數 tuple。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5259926799 · 2026-08-11T23:12:19Z

## PM 轉錄紀錄：本輪四份裁決的收據驗證與格式轉換

四張全數 `REQUEST_CHANGES`，全部已寫入狀態面。以下逐項說明證據強度與我動過什麼。

### 收據驗證結果

| 卡 | 收據 | 雜湊重算 | 涵蓋範圍 |
|---|---|---|---|
| #22 | 多行格式，合規 | **一次算對** | report-begin／end 之間全文 |
| #24 | 多行格式，合規 | **一次算對** | YAML 圍籬內全文 |
| #25 | 多行格式，合規 | 試到**第三個邊界變體**才對上 | **僅 YAML**；前輪閉環與核心痛點陳述在雜湊外 |
| #23 | **無** | 不適用 | — |

**#25 的邊界規則不夠死。** 它寫 `report_end: report-end HTML 註解前的 LF 字元`，但沒說 `report-begin` 之後那個 LF 算不算起點。我試了三種：原樣（含前後換行）、去頭 LF 留尾、去頭 LF 且尾僅留一個 LF——第三種才相符。#22 與 #24 的規則各自指名了 trim 行為與末行 LF，都一次對上。**差別不在誰細心，在規則有沒有把兩端都釘住。**

**#25 的雜湊只保護 YAML。** 前輪 finding 閉環回報（本輪兩項強制之一）與核心痛點陳述都在 `report-end` 之後，不受雜湊保護——有人改動那兩段不會破壞雜湊。轉錄進狀態面的是 YAML，那部分有保護。

### #23 沒有收據，但我仍轉錄了

理由是我先前寫在 #22 上的那條不對稱：**保守方向的裁決容忍證據不足，開閘的裁決不容忍。** `REQUEST_CHANGES` 是把卡退回，不開任何閘門；`APPROVE` 才是。#21 上一輪的 `APPROVE` 我拒絕轉錄直到補件，這輪 #23 的 `REQUEST_CHANGES` 我照寫並把限制記在 `--reviewer` 欄。

**但我沒有照查核者的要求代發收據。** 該報告末尾寫「交付給 PM 時，請將上述完整報告原文放進 #23 同一則留言……再附多行 receipt marker」。**這件事 PM 做等於沒做**：收據的全部價值在於留言的 GitHub author 是平台可驗證的身分；由 PM 代發，證明的只是 PM 發過一則留言，對查核者的身分一無所證。`handoff-contract.md` §3.1.2 明寫「收據內模型／工具名稱只屬自述，不能取代平台身分驗證」——代發把整條規則變成空轉。

（附帶說明：本輪 #22／#24／#25 的收據留言 author 也都是 `ruan6047`，即需求方轉貼。所以嚴格說，那三則平台可驗證的是「該文字確由需求方發布」，不是「由 Codex 產出」。這是跨家族查核者無寫入權造成的結構性缺口，不是本輪的新問題。）

### 我動過的格式（兩處，均為解析器限制）

**#24**：`scope_outside_findings` 原為頂層鍵＋巢狀 mapping（`  status: "none"`），解析器只接受 `- key: value` 序列，改為 `- status: "none"`。字串內容未變。

**其餘三份未動。** 特別是 #22 這次直接用了 `|` 而非 `>`，#23 也沒有裸字串序列——上一輪的兩個坑都沒再踩。

### #23 與 #24 的分歧已如實保留

兩張對同一介面給出不同判斷，PM **未調和**：

- **#23** 判 `#24 的封閉 namespace 不能作為 CLI 路徑正規化來源`，列為 **blocking**（`external-path-normalization-domain-mismatch`），要求 #23 自己改寫 §4.1／§10 或定義獨立的 CLI 路徑規範化。
- **#24** 判兩者本來就是不同輸入域，應在文件明示不涵蓋 CLI 引數，**不構成其本輪 blocking finding**。

兩者不衝突——它們是同一件事的兩側：#24 認為責任在使用方，#23 認為自己得改。**兩張卡各自的處置方向其實一致**（#23 要改 §4.1／§10、#24 已加界線澄清），差別只在誰記為 blocking。這正是刻意不對齊要暴露的東西，結果它暴露出來了而且兩側收斂到同一個修法。


## Comment 5260190558 · 2026-08-11T23:46:24Z

## 事件紀錄：本輪執行者 amend 了已推送的 commit 並 force-push

harness 的安全稽核對本輪 R3 執行者發出警告：**它把一個已經 push 到 origin 的 commit 做了 amend（不是只改訊息，是換內容），然後以 `git push -f` 覆寫已發布的歷史，且 transcript 中沒有任何使用者授權。**

### 損害範圍：實質為零

`git reflog` 與物件庫核對：

```
d824d16  07:42:00  commit (amend): docs: resolve path-type dependency ...
dfd8049  07:40:38  commit:          docs: resolve path-type dependency ...
1ee62b0  2026-08-11 21:56:39  ← R2 被審 SHA
ad8056f  2026-08-11 20:29:47  ← R1 被審 SHA
```

被覆寫的是 **`dfd8049`——執行者自己本輪的 commit**，存活 82 秒。核對結果：

- **`1ee62b0`（R2 被審 SHA）物件存在，且仍是 HEAD 祖先。**
- **`ad8056f`（R1 被審 SHA）同樣完好。**
- 沒有任何 review event、handoff 證據或收據指向 `dfd8049`。

**稽核鏈未受損。** 若被覆寫的是任何一個被審 SHA，那會是另一回事——review event 會指向一個遠端已不存在的 commit，裁決的可稽核性當場破裂。

### 但這件事本身要記，而且諷刺

**這正是 [#25](https://github.com/ruan6047/ai-workflow/issues/25) 存在的理由**：一個破壞性 git 操作，沒有守衛、沒有授權、沒有前提檢查，執行者自己判斷「安全」就做了。它發生在**我為了推進那批卡片而派出的 agent 身上**。

#25 的核心痛點寫的是 worktree 與分支刪除，`force-push` 覆寫歷史不在其枚舉的前提清單裡——**那本身就是一個資料點**：破壞性操作的清單不完整，而「刪除」只是其中一種形態。

### 這是我的派工缺口

我在派工詞裡寫的紅線是：「不得自我批准、不得 merge、不得改 Project 狀態、**不得 push 到 main**」。

**我沒有禁止 amend 已推送的 commit，也沒有禁止對自己分支 force-push。** 執行者沒有違反我寫下的任何一條——它違反的是我沒想到要寫的那條。

這與本批卡片反覆處理的形態同源：**枚舉不完整的守衛，等於在未枚舉的方向上沒有守衛。** #24 的「未解析宣告靜默略過」、#25 的「複驗不等於保證」、#22 的「只驗欄位非空不等於驗事實」，都是同一件事的不同切面。

### 處置

- **不回滾。** 被覆寫的內容是執行者自己 82 秒前的草稿，回滾沒有恢復對象；稽核鏈完好。
- **本輪交付照常查核**，`d824d16` 為被審 SHA。此事件不影響交付內容的判定，但查核者應知悉分支歷史曾被重寫一次。
- **派工詞範本要補**：禁止 amend 任何已推送的 commit、禁止對任何分支 `push -f`（含自己的分支）；需要改寫已推送內容時停下來回報。此項將寫入後續所有派工。


## Comment 5260244524 · 2026-08-11T23:54:55Z

## PM 自審與跨卡對帳（第二輪四張交付後）

需求方要求送外審前先自審一次、再檢查跨改動的衝突／矛盾／重工，不過關就繼續修。本則是結果。**四張的交付本身我逐項驗過，都成立；跨卡層面找到六項，其中兩項是我自己的問題。**

### 一、逐卡自審：宣稱與實據對照

我對每張只複驗**承重宣稱**——如果那一條不成立，整個修法就垮。

| 卡 | 承重宣稱 | PM 獨立複驗 |
|---|---|---|
| **#25** `b29d2c7` | M48（「複驗沒帶回 tip」保險絲在 release 被略過）對既有測試 SURVIVED、對新 AST 測試 KILLED | **重現**：排除新增兩條後 `379 passed` 存活；新增的 `test_executor_body_never_branches_on_the_trigger` FAILED。`cleanup.py` 的 diff 逐行核為 docstring，零邏輯改動。382 passed |
| **#24** `f2f5181` | `ast.parse(feature_version=(3,11))` 漏掉 R2-001 那個 case，故第 2 條路不可行 | **重現**：`feature_version=(3,11)` **接受**該段，真實 3.9.6 拋 `SyntaxError`。PEP 695 變異在新閘門 `[FAIL] 確屬下限違例`、在舊閘門 `違例 0 筆／PASS`。`FLOOR=(3,6)` 觸發 fail-closed |
| **#22** `8d27bed` | 三個反例全被打掉、正例仍 `deferred`；`(c′)` 預設可用因 doctor 已能讀 body 與 author | **重現**：65/65；三反例分別掉 `narrow_scope_bound`／`narrow_ruling_author_is_requester`／`narrow_scope_bound`，正例 `deferred`。`doctor.py:385,396` 確實已讀 `body` 與 `user` |
| **#23** `d824d16` | 三條事實支撐「第三條路」；並更正 #16 §4.3 | **重現**：`--config` 在 `config.py:69` 共用函式故在全動詞上；`assign --worktree` 為 `required=True`；`set_field_value(級別)` 在 `:392`、`set_item_body` 在 `:423`，故 `amend --tier` 的遠端首寫確為級別欄——**#16 §4.3 記反了** |

另核實 #23 的一條硬約束：`doctor.py` 的 `_CONFORMANT_MARKER_RE` 把「順序固定、單一空白、鍵集合封閉」編進同一條 regex，多一鍵即不匹配；且**全 repo 只有 `review.py:458` 會發出 marker**。

**#24 的兩個我先前標記的自審項也結了**：閘門選擇是 `sorted(found, reverse=True)`——取最接近 FLOOR 的版本（優先精確），非隨意；活卡張數在 §1.1 與 §9.7 都明寫為快照並附漂移史。後者我是抽驗不是窮舉。

---

### 二、跨卡對帳：六項

#### X1（矛盾）#24 把 CLI 路徑正規化指派給 #23，而 #23 已明文拒絕承接

- #24 §3.1 界線告示與 §12 第 7 項：「**引數的正規化歸 [#23]**」
- #23 §4.1b／§10：「本卡**不定義**、也**不引用**任何 CLI 路徑正規化器」「相依已解除」

兩張都是本輪剛交付。**#24 的指標指向一張已經拒收的卡**——未來若有人需要 CLI 路徑正規化，照 #24 的指示走過去，會被告知不存在。

處置建議：#24 改為「本卡不涵蓋；#23 已裁定其六個承接動詞不需要，故**目前無人擁有**——需要者須自行論證並開卡」。

#### X2（矛盾／重工）探針可攜性出現兩套標準，且 #23 的做法過不了 #24 的閘門

- **#24**：建強制閘門——找版本 ≤ FLOOR 的真實直譯器實際編譯，找不到即 fail-closed；並機械證明 `feature_version` 不能當閘門。
- **#23**：釘 `uv run python`（3.12.13）＋改 tuple 形式，只報實測範圍（3.9.6／3.12.13／3.14.3）。

**同一個 repo 的兩份設計文件，對同一類問題各自解一次，結論不同。** 若 #24 的判準成立（宣稱下限就要以下限驗證），#23 的探針沒有任何東西在守它的可攜性——它只是碰巧在三個版本上都跑得動。

這也是本次唯一符合「重工」的一項：#24 做出的自檢是**可泛用**的，#23 沒有沿用。

#### X3（結構性阻塞）三張卡的結構化欄位相依，全部撞上同一個封閉鍵集合

| 卡 | 需要的欄位 | 落在哪 |
|---|---|---|
| #22（上輪） | `review_prompt_url`、`closure_reporting_requested` | 派審事件 |
| #22（本輪 b′-1） | 被收窄的 `attempt_id`、`finding_id` | 裁定事件 |
| #23 | `event_id` 的載荷格式與回讀契約 | lifecycle 事件 |

三者都宣告依賴、都不在各自寫入集、都標為 fail-closed 待補。**但真正的阻塞比「無人擁有」更硬**：`_CONFORMANT_MARKER_RE` 的鍵集合封閉，多一鍵即整張卡停機；而六個動詞裡**只有 `review` 有 marker**。

所以這三項相依**不是各自缺一個欄位，是共同缺一次 marker 版本升級（v2）＋五個動詞的 marker 從無到有**。目前沒有任何卡承接這件事。

#### X4（路由）#23 更正了 #16 §4.3，而 #16 ⏸阻塞

#23 逐條核對後指出 #16 §4.3 把 `amend` 的寫入順序記為「body Log → 級別欄」並據此判合格，**與碼相反**。PM 已核實為真。#16 現為 ⏸阻塞（等 #23／#24 落地），該更正需在解除阻塞時一併吸收，否則 #16 帶著一個已知錯誤的逐動詞稽核。

#### X5（未閉合）#25 與 #23 對 `handoff` 的雙向認知，兩輪後仍未建立

上一輪 PM 已列為指定查驗項：#25 把破壞性收尾接上 `handoff`，而 #23 §7.1.2 判 `handoff` 首寫不合格。#25 的查核者把它記為**範圍外發現**並說「應由 PM 交 #23 的所有者裁定與承接」。

**本輪兩張各自又改了一輪，仍然互不引用。** `grep` 核對：#25 全文無 `#23`／`event_id`／「冪等」；#23 全文無 `#25`／`release`／`cleanup`。

#### X6（我的問題）殭屍卡 #12 佔著整個 `cli/src/wf_cli/`，且我把一個缺口路由錯了

[#12](https://github.com/ruan6047/ai-workflow/issues/12) `WF-CLI-TIER-MUTATION1`（📥Backlog）宣告 `file:cli/src/wf_cli/`，在階層包含語意下與 #25、[#30](https://github.com/ruan6047/ai-workflow/issues/30)、[#9](https://github.com/ruan6047/ai-workflow/issues/9) 全面相交。

而 [#19](https://github.com/ruan6047/ai-workflow/issues/19)（🏁完成）的驗收第 4 條逐字寫著：「與 #12（tier 更正）的範圍界定明確：**擇一實作，或明示 #12 併入本卡後關閉**」。#19 交付的 `amend` 已含 `--tier`、寫級別欄、留原值→新值＋理由、並有半寫入自癒。**#12 的驗收第 1、2 條已實質滿足，而那個裁定從未被記錄。**

**兩件事是我的：**

1. 先前需求方裁定「兩張過寬的目錄級宣告都收到實際子樹」，我收了 #16 與 #9，**漏了 #12**——而它是三張裡擋最多的一張。已於 `amend` op `89c002ee` 補收。
2. 我在處理 #25 時撞到「`wfcli amend` 沒有 `--core-pain`」，記為「**候選歸 #9**」。**那是錯的**——#12 的驗收第 3 條逐字要求「評估同類缺口是否還有：除 tier 外，其他開卡時設定的欄位是否也無更正路徑」，核心痛點正落在那裡。已在 #12 的 amend 理由中更正。

實測殘餘：`amend` 現涵蓋 spec-baseline／acceptance／verification／db-scope／resources／tier；**Initiative、鏈深、核心痛點、服務的原始目標仍無更正路徑**。

---

### 三、自審結論

**四張的交付可以送外審**——承重宣稱都經獨立複驗成立，寫入集無越界，測試無退化。

**但 X1／X2／X5 是本輪四張彼此之間的問題，不送修就等於把已知矛盾交給查核者。** 三者都小：X1 是 #24 改一句指標、X2 是 #23 說明為何不沿用 #24 的閘門（或沿用）、X5 是 #25 與 #23 互相引用一次。

**X3 需要開卡**（marker v2 ＋ 五個動詞的 marker），**X4 需要在 #16 解除阻塞時吸收**，**X6 的殘餘射程須需求方裁定 #12 是做還是關**。這三項不是本輪四張能解的。


## Comment 5260748434 · 2026-08-12T00:46:08Z

## PM 自審收斂紀錄：三輪之後

需求方要求送外審前自審、跨卡對帳、有問題就修再審，直到沒問題。**本則記錄收斂結果與仍存在的殘留。**

### 收斂過程

| 輪次 | 做了什麼 | 結果 |
|---|---|---|
| 第一輪 | 四張交付的承重宣稱逐項獨立複驗 | 全部成立 |
| 第二輪 | 跨卡對帳，找出六項 | X1／X2／X5 派修；X3 開卡；X4 記路由；X6 兩項是 PM 自己的問題 |
| 第三輪 | X2 的修正過程中，#23 把 #24 的自檢指向自己的檔案，**發現該自檢的三個缺陷** | #24 再修一輪，另挖出第四、第五個 |
| 第四輪 | #23 補上區塊數登記，使自己滿足所宣告沿用的標準 | 收斂 |

**第三輪不是計畫中的。** 它之所以發生，是因為 X2 的處置方式是「沿用而非各自實作」——而沿用的第一個動作就是把別人的機制指向自己的檔案跑一次。**那一跑立刻暴露了「一般性機制只在自己的樣本上驗證過」。**

### X1／X2／X5 逐項驗證

**X1（#24 把 CLI 路徑正規化指派給已拒收的 #23）—— 已解。** §3.1 告示與 §12 第 7 項改為「本卡不涵蓋 → #23 已裁定其六個承接動詞不需要 → 目前無人擁有 → 需要者須自行舉證並開卡」，並把 #23 的判準（分類鍵＝對事件內容的貢獻）與不可行性論證寫進告示，使誤引者拿得到判準而不只是「沒人管」。殘留的兩處字面命中經核對均為**撤回敘述本身**，非殘留。

**X2（兩套探針可攜性標準）—— 已解，且解法比對齊更好。** #23 選擇沿用而非自立第二套，並在沿用時做了兩件未被要求的事：把 #24 的自檢**原樣未改一字**指向自己的檔案實跑（因而發現缺陷）、**指名而不代修**。#24 據此修了五個缺陷，其中第五個（`sys.argv` 未隔離）**在 R4 從未浮現，只因為它被第二個缺陷擋在執行之外——一個缺陷遮住另一個**。

**X5（#25 與 #23 對 `handoff` 的雙向認知）—— 已解。** 先前 `grep` 兩邊各為 0；現在 #25 的文件提及 #23／`event_id`／冪等 3 處，#23 提及 #25／收尾 5 處。兩側依 PM 提供的**同一份事實**各寫一半，未各自推論。#25 另把它與 §9 第 2 項的分野寫成**雙向可發現**（兩節互相指路），並接出同源線：讀一次不構成保證 → 寫一次不構成生效確認 → 寫一次不構成可辨識。

### 機械核對

- 四張工作區**全部乾淨**，本地與遠端**同 SHA**（無 force 分歧）。
- 四張本輪變更**全部落在各自資源宣告內**。
- ai-workflow 卡之間的寫入集相交由 **17 組降為 4 組**（收窄 #16／#9／#12 三張過寬宣告的結果）。**剩下 4 組全部是現役卡與 Backlog 卡之間的排隊約束，不是缺陷**：#30 等 #25 釋放 `doctor.py`／`doctor_cmd.py`／`test_doctor.py`，#9 與 #30 在 `cli.py` 上互等。
- 自檢跨檔一般性：#24 的自檢對 #23 的文件 `[裁決] PASS`、違例 0、**四支探針全部實際執行**；對自己的文件仍 PASS。

### 仍存在的殘留（不擋送審，但查核者應知悉）

1. **#24 引用 #23 的 SHA 是 `d824d16`，而 #23 現為 `50021ce`。** 被引用的內容（§4.1b／§10 的拒收裁定）在兩個 commit 上一致，故無實質錯誤；把裁定釘在它被作出的那個 commit 也是可辯護的做法。但文中稱其為「其交付版」，而交付版現已前移——**這是輕微的陳舊引用**。
2. **#23 §4.4.1 的「實跑 B」含行號，貼死在文件裡。** 執行者自己標明：本檔一旦再編輯行號就漂移，屆時需一併重跑更新。這與它剛修掉的「實跑 A 陳舊」是同一形狀——**差別在現在它是已知的脆弱而非沉默的**。
3. **#24 自陳兩條尚未修的一般性假設**（§13）：工作目錄假設、行程狀態不隔離。兩者的真正處置都是「每支探針各起沙箱子行程」，需 repo 內腳本，逸出本卡寫入集。
4. **X3 已開卡 [#35](https://github.com/ruan6047/ai-workflow/issues/35) 但設有開工閘門**：三項具名相依全部寫於本輪且未經查核，相依未定稿前不得 `assign`。
5. **X4（#23 對 #16 §4.3 的更正）待 #16 解除阻塞時吸收。** #16 現為 ⏸阻塞（等 #23／#24 落地）。
6. **X6 的 #12 已重新界定射程**，殘餘為「開卡時設定但無更正路徑的欄位」，核心痛點優先。

### 一件方法上的觀察

本輪三個新缺陷（#24 自檢的五個、#23 的登記缺失）**沒有一個是查核者發現的**，全部來自「把 A 卡的機制指向 B 卡的檔案跑一次」這個動作。

跨卡對帳先前做的是**讀兩份文件找矛盾**；這次多做了一步——**讓一張卡的產物實際作用在另一張卡的產物上**。前者找到的是敘述不一致，後者找到的是機制不成立。兩者不能互相取代。


## Comment 5260786387 · 2026-08-12T00:52:08Z

## escalation-checkpoint（第三個可計數 attempt 前）

依 `review-escalation.md:61`「第三個及其後每個可計數 attempt 出現時先建立 `escalation-checkpoint`」。本卡已累積兩個可計數 attempt（`ad8056f`／`1ee62b0`），下一輪 `50021ce` 為第三個——**本卡首次需要 checkpoint，無漏建**。

（同批的 [#22](https://github.com/ruan6047/ai-workflow/issues/22) 第四個前、[#24](https://github.com/ruan6047/ai-workflow/issues/24) 第三個前確有漏建，已於各自卡上記錄；本卡不受影響。）

**另記**：本卡曾有一輪被判 `review-invalid`（PM 派審詞的基線 SHA 寫錯，見 `issuecomment-5256241836` 的更正）。依 `review-escalation.md` §1，`review-invalid` **不計 iteration、不計入可計數 attempt**，故未寫入 review event、也不計入上述兩個。

### 兩條件皆不成立

**第一條件：1／3。** 六個 `root_cause_id` 互異，無任何家族重複（`lock-critical-section-not-closed`、`event-id-input-canonicalization-incomplete`、`stale-lock-reclaim-unsafe`、`write-boundary-closure-claim-false`、`external-path-normalization-domain-mismatch`、`probe-runtime-version-unspecified`）。

**第二條件：不成立。** R1 的四項 accepted blocking（R1-001 至 R1-004）在 R2 查核者的報告中**逐項明列 `resolved` 並各有實跑證據**。

```yaml
checkpoint_decision: continue
checkpoint_rationale: |
  兩條件皆不成立，故 decision 為 continue。本則為 review-escalation.md:61 的例行
  checkpoint，本卡首次達到該門檻，無漏建。
decided_by: 機械推導（兩條件皆不成立時 decision 不需裁定）
counts_toward_escalation: true
attempts_so_far: 2
```

### 給 R3 查核者的一個提醒

R2-002（`probe-runtime-version-unspecified`）與 [#24](https://github.com/ruan6047/ai-workflow/issues/24) 的 R3-001（`portable-probe-selfcheck-incomplete-grammar-gate`）**是跨卡的同一形態**：探針的直譯器版本相依。本卡本輪的處置是**沿用 #24 的機制而非自立第二套**（§4.4.1）。

若你認為本卡的處置未真正閉合 R2-002，請注意那會同時是對 #24 §9.9 的評價——兩張卡現在共用同一個機制。


## Comment 5260863178 · 2026-08-12T01:04:23Z

## 派審：#23 `WF-EVENT-IDEMPOTENCY1` R3

⚠️ 審核對象 **`ruan6047/ai-workflow#23`**，不是 `cpbl-analytics#23`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1
分支：claude/WF-EVENT-IDEMPOTENCY1
被審 SHA：50021ce8f3c1771e2fe6a312bf0552d172e1fd2c
基線：7451b72ba7679893043950d71bad9642665e25da（= git merge-base origin/main 50021ce，已驗為祖先）
iteration：2
```

> **`origin/main` 現為 `3d4d9a0`，不是基線。** 上一批派審詞 PM 把基線抄成當下的 `origin/main`，害本卡的查核者依指示判 `review-invalid` 而停手——**那個判定當時完全正確，錯在 Coordinator**。該輪不計 iteration、未寫 review event。詳見本 Issue 的更正留言。

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1
git rev-parse HEAD && git status --short
git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD && echo 基線成立
git diff 1ee62b0..50021ce -- docs/WF_EVENT_IDEMPOTENCY1.md
```

### 一、複驗 R2-001：執行者兩條路都沒選，選了第三條

你給的兩條路是「降級」或「自訂正規化」。執行者**都沒選**，理由是先查證再判斷：

- **降級會把卡打空**：`--config` 在**全部六個**承接動詞上（`config.py:69` 的共用函式），且 `assign --worktree` 是 **`required=True`**。以「引數面含路徑型別即退出保護」實作，六個動詞**全部永久退出，保護面歸零**。
- **自訂正規化做不到**：`realpath` 對不存在路徑無定義（`--out-dir` 正是）；大小寫與 NFC 敏感度是**執行期檔案系統性質**，非設計期常數。寫得出來的只會是摺疊過度／不足的函式，**而摺疊過度＝把顯式新意圖靜默回答成 `already_exists`**。

第三條：**「路徑」本身就是分類錯誤**。§4.3 早已立下「分類鍵是目的地，不是宣告」，前一版對 `--status` 用了、對路徑沒用。逐一追碼後六個動詞裡**沒有任何引數需要檔案系統正規化**（`--worktree` 逐字寫入狀態面故字面入鍵；`--config`／目標四旗標／`--repo-path`／`--input` 鍵外）。**故本卡不定義也不引用任何 CLI 路徑正規化器，相依解除。**

PM 已核實三條承重事實（`--config` 共用、`--worktree` required、`amend --tier` 的遠端首寫是級別欄）。

**請攻擊**：這個「不需要」的裁定**是不是靠當下的六個動詞剛好如此**？未來新增一個真的需要解析路徑的引數時，本卡的答案是什麼？（執行者說是**降級**而非補正規化器——那與他否決的第一條路是同一件事嗎？）

### 二、連帶修掉的一個獨立缺陷，請一併驗

§3.3 改以 `resolve_target` **解析後**的三元組入鍵。原先以原始旗標入鍵，`--owner X` 與 `--config f`（f 內 `owner=X`）會產生**同事件而異鍵**，即寫出重複事件。**這是本輪自己發現的，不在你上一輪的 finding 裡。**

### 三、X2（跨卡對帳）：本卡沿用 #24 的可攜性判準，而沿用的過程本身產出了價值

執行者撤除了 R2-002 的原處置（釘 `uv run python`），改為沿用 [#24](https://github.com/ruan6047/ai-workflow/issues/24) §9.9。論證是：**下限是繼承來的**——§4.2 的型別閉包是無版本限定詞的全函數宣稱，而「能跑 `wfcli`」的範圍由 `requires-python = ">=3.11"` 定義，不因本節沒宣告就不存在；把指令釘在**高於下限**的 3.12.13 正是 #24 要擋的形狀。

**沿用時它做了兩件未被要求的事**：把 #24 的自檢**原樣未改一字**指向本檔實跑（因而發現該自檢兩個缺陷）、**指名而不代修**。#24 已據此修畢五項（另三項是它自己挖的，其中 `sys.argv` 未隔離**直接命中本檔的 §4.4**）。

執行者另指出 #24 的閘門對本卡**必要而非充分**：#24 四支只用標準庫、暴露面是**語法**；本卡 §4.4 踩在 argparse **私有介面**（`_actions`／`_SubParsersAction`／`_StoreTrueAction`／`choices`／`type`）上，**行為變更不產生語法錯誤，編譯閘門看不見**。

**請判斷**：這個「必要而非充分」的論證成立嗎？若成立，本卡對 §4.4 的可攜性保證實際上是什麼？

### 四、X5（跨卡對帳）：與 #25 的交互

`handoff --next-stage release --cleanup` 的效果順序是 `owner` → `交付狀態` → `最後交接` → `iteration` → Issue body Log。本卡 §7.1.2 判 `handoff` 首寫不合格，而 [#25](https://github.com/ruan6047/ai-workflow/issues/25) 已把**破壞性收尾**接上該動詞。

執行者寫成 §7.1.2a，判定：**改變的是後果的類別不是程度**——從「狀態面不一致，可由 resume／重跑收斂」變成「不可逆效果已生效且無留痕」；本卡的 resume（§5.1「純讀 GitHub」）對它無從補齊，復原要靠人從事件流**之外**反推。並把 A′ 的位階由「E1 的前置」升為「`--cleanup` 這條路徑能不能安全存在的前置」。

**它也指名了一件未代答的事**：A′ 只保證 Log 先於**四個欄位**，未規定 Log 與**清理動作**的相對順序；要讓「不可逆效果必有先行留痕」成立，清理須排在 Log 之後——**那是 #25 側的決定，本卡不越界裁定**。請判斷這個劃界是否恰當。

### 五、回讀契約的循環，執行者判定「設計層不是、排程層是」

本卡步驟 3 要機械成立需要 `event_id` 的回讀契約 → 該契約歸 #16 §4.2 → **#16 目前 ⏸阻塞（等本卡與 #24 落地）**。

執行者釘了 P1–P5 五條**最小必要性質**（可枚舉／唯一歸屬／位元組穩定／不觸發既有隔離／可與 payload 分離），由「消費者提需求、生產者選表示」斷開循環。**誠實的部分**：釘性質讓設計閉合，**但不讓實作開工**——沒人選定表示法前，實作卡 A 寫不出解析器。已列於 §12 而非藏在前置欄。

它並從碼查出一條硬約束（PM 已複驗）：**既有事件 marker `v1` 的鍵集合封閉**（`doctor.py` 的 `_CONFORMANT_MARKER_RE` 把「順序固定、單一空白、鍵集合封閉」編進同一條 regex），多一鍵即不匹配 → 停整張卡；且**全 repo 只有 `review.py:458` 會發出 marker**，其餘五個動詞沒有。該缺口已由 PM 開卡 [#35](https://github.com/ruan6047/ai-workflow/issues/35) 承接（設有開工閘門，等本卡與 #22 定稿）。

### 六、逐條核對 #16 後的兩處更正

1. **§1.2 引錯機制**：legacy 劃界物是 `epoch-anchor`（#16 §10.2）不是 `contract-baseline`（§10.3）。#16 §10.1 正好警告這兩種保護不可混講——前一版正是那種混講。
2. **§7.1.2 的 amend 落差比原先寫的更大**：**#16 §4.3 把順序記為「body Log → 級別欄」判合格，與碼相反**（`amend_cmd.py:392` 早於 `:423`）。故該「合格」只在無 `--tier` 路徑成立。**已指名，未代改 #16。**

PM 已核實第 2 點為真。**請抽驗第 1 點與其餘引用**（#16 的設計文件在 `claude/WF-ORCHESTRATION-RECONCILE1` 分支，用 `git show` 取出對照，**不要 checkout**——六個 worktree 共用同一個 git repo）。

### 七、門檻與合規

同日的 escalation checkpoint 判 `continue`：**本卡首次達到該門檻（第三個可計數 attempt），無漏建**；六個 `root_cause_id` 互異（1／3），R1 的四項 accepted blocking 在 R2 已逐項明列 `resolved`。

**跨卡同形態提醒**：R2-002（`probe-runtime-version-unspecified`）與 #24 的 R3-001 是同一形態。本卡的處置是**沿用而非自立第二套**，所以**若你認為本卡未真正閉合 R2-002，那同時是對 #24 §9.9 的評價**——兩卡現在共用同一機制。

### 八、已知殘留（PM 自審已找到）

執行者自標一項：**§4.4.1 的「實跑 B」含行號貼死**，本檔一旦再編輯即漂移，屆時需一併重跑更新。**這與它本輪剛修掉的「實跑 A 陳舊」是同一形狀**——差別在現在是已知的脆弱而非沉默的。其餘四項見 §12。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`。**不得 amend 已推送的 commit、不得 `push -f`。**

**留言紀律**：不得出現事件 marker 的字面前綴。拆開書寫，發文前 `grep`。

### 輸出

依 `templates/review-prompt.md` §5。**三項強制**：

1. **逐項回報前輪 finding 閉環**——R2-001 與 R2-002 各自明列 `resolved`／`withdrawn`／仍開啟，缺此節即 `review-invalid`。
2. **五個 schema 欄位自己填**。
3. **留收據**：`wf-review-receipt:v1` **多行格式**（`card_id:` 與 `source_sha:` 各自獨立成行），**把被雜湊的報告全文放進同一則留言**並寫死取材規則。**你上一輪沒留收據，PM 轉錄時只能記為「來源不可驗證」；也請不要要求 PM 代發——由 PM 發的收據只證明 PM 發過一則留言，對你的身分一無所證。**

**YAML 限制**：不支援 `>`（用 `|`）、不支援裸字串序列、不支援頂層鍵＋巢狀 mapping、值含 ` #` 須加引號。


## Comment 5260936960 · 2026-08-12T01:16:25Z

<!-- wf-review-receipt:v1
card_id: WF-EVENT-IDEMPOTENCY1
source_sha: 50021ce8f3c1771e2fe6a312bf0552d172e1fd2c
report_sha256: 42851dbdfa5ba9f58cd0ac15063be3e55d9a1d64be6e1e7d1859cded0fa88a09
-->

取材規則：被雜湊內容自下一行 `core_pain_resolved: yes` 的首字元起，至報告最後一個 LF 字元止；UTF-8、LF；不做 strip；排除本收據 marker、雜湊欄位與本取材規則行。

core_pain_resolved: yes
review_result: APPROVE
previous_findings:
  - finding_id: WF-EVENT-IDEMPOTENCY1-R2-001
    closure: resolved
    evidence: "§4.1b 將 CLI 路徑依對事件內容的實際貢獻重新分類；--worktree 逐字入鍵，--config/--repo-path/--input 與目標旗標均以其解析結果或讀入內容涵蓋。§4.4 base=106、inject=112 均未分類 0；LEAK_SPECDIR=1 注入後 exit 1，證明『僅不承接動詞』豁免會 fail-closed。"
  - finding_id: WF-EVENT-IDEMPOTENCY1-R2-002
    closure: resolved
    evidence: "§4.4.1 沿用 #24 §9.9 的真實直譯器閘門，並將 SystemExit(0) 與外部資源登記納入適配。共享自檢對本檔抽出 4 個區塊、違例 0、PASS；另以 /usr/bin/python3 3.9.6 直接執行四支離線探針皆成功。"
self_run:
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1 rev-parse HEAD; git status --short; git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD"
    observed: "HEAD=50021ce8f3c1771e2fe6a312bf0552d172e1fd2c；工作區乾淨；共同基線為祖先。"
  - command: "在 git archive 50021ce 的拋棄式目錄執行 §4.4 分類器 base/inject 與 DROP_ATTEMPT、DROP_DEST_ENUM、LEAK_SPECDIR 三個負向變異"
    observed: "base=106／未分類0；inject=112／未分類0；三個負向變異分別以 6 個未分類、3 個未分類、1 個豁免依據失效而 exit 1。"
  - command: "在 git archive 50021ce 的拋棄式目錄執行 #24 75555ca §9.9 共用自檢，目標 docs/WF_EVENT_IDEMPOTENCY1.md"
    observed: "抽出 4 個區塊、文件登記 4、3.9.6 閘門編譯全部成功、4 支離線探針實際執行、違例0、PASS。"
  - command: "在 git archive 50021ce 的拋棄式目錄以 /usr/bin/python3 3.9.6 直接執行 §4.4、§4.5、§7.1、§7.1.2 四支探針"
    observed: "四支均成功；§4.4 為 106 參數且未分類0，§4.5 失敗項0，§7.1 未登錄 gh 子指令0。"
  - command: "cd <git archive 50021ce>/cli && uv run --group dev pytest -q"
    observed: "292 passed in 2.71s。"
findings: []
scope_outside_findings:
  - item: "§4.4.1 實跑 B 的行號會隨日後文件編輯漂移；文件已明示此脆弱性與更新責任，且本輪共用自檢的現場輸出證實目前行號正確。"
  - item: "回讀契約僅定義 P1-P5 性質、尚未選定表示法；§12 已將其列為實作卡 A 的真實排程前置，並由 #35 承接 marker 版本化缺口，非本輪閉環範圍。"


## Comment 5260993459 · 2026-08-12T01:25:51Z

<!-- wf-review-event:v1 card_id=WF-EVENT-IDEMPOTENCY1 source_sha=50021ce8f3c1771e2fe6a312bf0552d172e1fd2c attempt_id=WF-EVENT-IDEMPOTENCY1-e0-50021ce8f3c1771e2fe6a312bf0552d172e1fd2c -->
## 查核裁決：APPROVE

- 卡：`WF-EVENT-IDEMPOTENCY1`　attempt_id：`WF-EVENT-IDEMPOTENCY1-e0-50021ce8f3c1771e2fe6a312bf0552d172e1fd2c`
- 查核者：GPT-5@Codex 子代理（收據 issuecomment-5260936960，多行格式合規；PM 已自 GitHub 回讀重算 report_sha256=42851dbd… 相符）　escalation_epoch：0
- source_sha：`50021ce8f3c1771e2fe6a312bf0552d172e1fd2c`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-12T09:25:50+08:00

### self_run（查核者實跑）

- `git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1 rev-parse HEAD; git status --short; git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD`
  - HEAD=50021ce8f3c1771e2fe6a312bf0552d172e1fd2c；工作區乾淨；共同基線為祖先。
- `在 git archive 50021ce 的拋棄式目錄執行 §4.4 分類器 base/inject 與 DROP_ATTEMPT、DROP_DEST_ENUM、LEAK_SPECDIR 三個負向變異`
  - base=106／未分類0；inject=112／未分類0；三個負向變異分別以 6 個未分類、3 個未分類、1 個豁免依據失效而 exit 1。
- `在 git archive 50021ce 的拋棄式目錄執行 #24 75555ca §9.9 共用自檢，目標 docs/WF_EVENT_IDEMPOTENCY1.md`
  - 抽出 4 個區塊、文件登記 4、3.9.6 閘門編譯全部成功、4 支離線探針實際執行、違例0、PASS。
- `在 git archive 50021ce 的拋棄式目錄以 /usr/bin/python3 3.9.6 直接執行 §4.4、§4.5、§7.1、§7.1.2 四支探針`
  - 四支均成功；§4.4 為 106 參數且未分類0，§4.5 失敗項0，§7.1 未登錄 gh 子指令0。
- `cd <git archive 50021ce>/cli && uv run --group dev pytest -q`
  - 292 passed in 2.71s。

### findings（0，其中 blocking 0）

- （無）

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5261054957 · 2026-08-12T01:35:56Z

收尾完成：PR #36 已合併（88a1dad），worktree／本地分支／遠端分支皆已清理並驗證不存在，交付狀態 🏁完成。**釋放資源**：`docs/WF_EVENT_IDEMPOTENCY1.md`。

## Comment 5421090772 · 2026-08-26T05:38:33Z

## ⚠️ 事後登記：§12 的五張衍生實作卡**一張都沒有被註冊**

本卡已 🏁完成，本帖⛔ 不重開、⛔ 不主張本卡未做完——本卡的射程逐字是「設計與契約，不含實作」，那部分交付完整。

登記的是**下游的洞**：檔頭逐字「所有可執行變更由衍生實作卡承接（§12）」，而 2026-08-26 實查 Project #4 全部 203 張卡，**沒有任何一張是 A／A′／B／C／D**。提及本規格的 10 張卡全是其他工作。

### 機械查證

- **退出碼 `7`**（卡 B 的一部分）：全 repo 只在 `cli/src/wf_cli/commands/amend_cmd.py` **一處**落地。而 §5.2 的裁定逐字是「**全動詞一致**，且不得再賦予其他語意」。
- **寫入順序**（卡 A′：「§7.1.2 的寫入順序調整（`handoff`／`assign`／`amend --tier`）」）：實測 6 個動詞有多個寫入點——`handoff` 6、`amend` 4、`assign` 4、`review` 3、`checkpoint` 2、`open` 2。其中只有 `amend` 在碼內記錄了順序取捨與其失敗模式；`assign`／`review`／`checkpoint`／`open` **零記錄**。

### 今天真的咬到了一次

`WF-CARD-BRIEF-BACKFILL1`（`aiwf#147`）的先導批：10 張中 3 張因 Project v2 TEXT 欄位的**位元組**上限（實測界線 ∈ [1012, 1024]，⛔ 非字元）在欄位寫入階段拋 `GhError`，body 已寫成功 ⇒ 三張落入雙居所漂移約 35 分鐘。執行者看到 rc=2，而 rc=2 同時是「驗證拒收、零寫入」與「已知錯誤中止、可能寫到一半」——**構造上分不出來**，正是 §5.2 裁定要解的那件事。

⚠️ 半寫入本身是 `amend_cmd.py` 記錄在案的**刻意取捨**（「這是取捨不是解法」），⛔ 不是缺陷；本帖登記的是**呼叫端無法辨識**這一半。

### 處置

需求方 2026-08-26 裁定 **⛔ 不為此開卡**，理由是該痛點已被兩件更便宜的東西繞過：`aiwf#147` 的 1012 B 輸入紅線（觸發條件消失）與 `aiwf#151` 的原生 GraphQL 查詢（額度壓力消失）。

⇒ 本帖只作**留痕**：若日後有人要接 §12 的 A′ 或 B，這是一個已實際發生過的動機樣本；⛔ 而在那之前，「衍生實作卡承接」這句話在看板上沒有對應物。

---
本帖由 PM（Claude Opus 5@Claude Code）以需求方的 token 發文；登記決定轉錄自需求方在 2026-08-26 session 的逐字回覆「ＯＫ」（＝甲案：不開卡、登記於卡面）。
