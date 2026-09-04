# #21 WF-CLI-ROUTING-TIER1 wfcli open 補上建議執行／查核能力層級與理由
- state: closed  created: 2026-08-10T18:22:50Z  closed: 2026-08-11T22:47:00Z
- url: https://github.com/ruan6047/ai-workflow/issues/21
- comments: 27

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code
- 執行：待指派　查核：獨立校讀
- Initiative：—　spec 基線：templates/tasks-card.md 第 4 行的卡面格式 ＋ MODEL_ROUTING.md「路由決定於規劃期」（main 91d8a1f）；缺口於 2026-08-11 查證 wfcli open 旗標、Card dataclass 與 Project 凍結欄位三處皆無此欄位時發現
- DB：db_scope=none
- 服務的原始目標：讓「路由決定於規劃期」這條規則在唯一寫入通道上真的生效，而不是只存在於範本文字。

## 簡介
<!-- card-brief:begin -->
讓「路由決定於規劃期」在唯一寫入通道上真的生效：open 支援填建議執行／查核能力層級＋理由並渲染成 templates/tasks-card.md 第 4 行格式，assign 端接受實際模型、與卡面建議不符時 fail-closed 要求偏離理由，遷移標記改以結構位置（獨立一行且緊鄰唯一路由行）辨識而非子字串比對。**適用時機**：開卡或派工時要判斷能力層級怎麼填、偏離要不要理由；或碰上能力層級與 T0–T4 風險級別命名碰撞時。⛔ 非射程：既有 18 張卡永久以 absent 派工，不補標記、不新增任何受控遷移入口（需求方 2026-08-11 承 R4-002 裁定）；卡面只引用能力層級不寫模型名，名單以 MODEL_ROUTING.md 為準。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：templates/tasks-card.md 第 4 行與 MODEL_ROUTING.md 都要求開卡時必填「建議執行／查核能力層級＋理由」，但 wfcli open 沒有對應旗標、Card 也不渲染該欄位、Project 凍結欄位亦無。於是每一張以 CLI 開的卡都靜默不符範本，且不會報錯——2026-08-11 開的 #17／#19／#20 三張卡執行欄皆只有「待指派　查核：獨立校讀」，缺少括號內的層級與理由。規則寫在範本裡、產生端不支援，等於規則從未生效。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/card.py",
    "file:cli/src/wf_cli/commands/open_cmd.py",
    "file:cli/src/wf_cli/commands/assign_cmd.py",
    "file:cli/tests/test_card.py",
    "file:cli/tests/test_commands_mocked.py",
    "file:cli/tests/test_amend.py",
    "file:cli/tests/test_review.py",
    "file:cli/README.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] open 支援指定執行／查核的建議能力層級與理由，並渲染成 templates/tasks-card.md 第 4 行的格式。
- [ ] 缺層級時的處理必須明確（硬拒或預設＋警示，擇一並寫明理由）；不得靜默產出不符範本的卡。
- [ ] 卡面引用「能力層級」而非模型名（MODEL_ROUTING：名單會過期、層級是穩定介面）。
- [ ] 與 --tier／級別（T0–T4 風險級別）的命名碰撞須在 --help 與 README 明確區分。
- [ ] assign 端的偏離留痕：assign 須接受實際模型（能力層級語彙同開卡端），並在實際層級與卡面建議不符時 fail-closed 要求偏離理由；兩者一併寫入 assign／claim 事件的 Log。相符時不強制理由。
- [ ] 本卡完成後，「路由決定於規劃期」的規劃端與派工端皆須由唯一寫入通道執行；README 不得再宣稱本卡未涵蓋派工端。
- [ ] **（2026-08-11 追加，承 R4-001）遷移標記須以結構位置辨識**，不得以子字串出現與否判定：標記須為獨立一行且緊鄰唯一路由行。須加回歸測試——舊卡經 amend 或任何自由文字含該標記字串時，仍須判 absent。
- [ ] **（2026-08-11 追加，承 R4-002；需求方裁定）既有 18 張卡永久以 absent 派工**：不補標記、**不新增任何受控遷移入口**。理由：(1) R4-001 已證明「能寫入 head 的入口即漏洞來源」，新增遷移入口就是新增第二個必須自證不會重蹈 R4-001 的入口；(2) 事後補填的四個路由值未必反映規劃期判斷，違反 MODEL_ROUTING.md 第 14 行「路由決定於規劃期」。**代價（既有卡至結案前每次派工需多帶偏離理由，且該理由實質為雜訊）需求方已知悉並接受。** README 不得暗示未來會補遷移入口。

## 驗證

- [ ] 測試涵蓋渲染格式、缺欄處理，以及能力層級與 T0–T4 不相混。
- [ ] 以 #17／#19／#20 的實際開卡情境重放，證明新版產出符合 templates/tasks-card.md 第 4 行格式。
- [ ] **assign 偏離專項**：實際層級等於建議時不要求理由且照常派工；不等於建議且未給理由時 fail-closed 拒絕派工；給了理由則兩者皆寫入 Log 且可被讀回。三種情形各有測試。
## Log

- 2026-08-11T02:22:49+08:00 open by Claude Opus 5@Claude Code；owner 待指派；iteration 0。
- 2026-08-11T12:53:36+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree claude/WF-CLI-ROUTING-TIER1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-routing-tier1；交付狀態 🚧進行中。
- 2026-08-11T13:02:08+08:00 handoff by wf-cli → owner 跨家族查核（待需求方指派）；iteration 0；SHA 26a0149262ac1d99fa9bd0f6490be531a7ec0978；證據 cd cli && uv run pytest -q → 324 passed（基線 296，新增 28 項：能力層級語彙與 MODEL_ROUTING.md 比對、封閉枚舉、與 T0–T4 值域零交集、缺欄／空白理由硬拒、範本第 4 行渲染格式、#17／#19／#20 開卡情境重放）；ruff findings 與 main 同集合無新增。
- 2026-08-11T13:04:42+08:00 amend by wf-cli（op eeb4fc50）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/card.py", "file:cli/src/wf_cli/commands/open_cmd.py", "file:cli/tests/test_card.py", "file:cli/tests/test_commands_mocked.py", "file:cli/README.md" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/card.py、file:cli/src/wf_cli/commands/open_cmd.py、file:cli/tests/test_card.py、file:cli/tests/test_commands_mocked.py、file:cli/tests/test_amend.py、file:cli/tests/test_review.py、file:cli/README.md」；理由 執行者實際寫入 cli/tests/test_amend.py 與 cli/tests/test_review.py（新旗標成為必填後，這兩檔自建的 open argv 需同步），但未先擴充資源宣告。宣告是互斥契約的事實面，寫入超出宣告即該面失效；此為事後補正，非擴大授權範圍。
- 2026-08-11T13:40:54+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 獨立校讀（需求方於對話中轉貼原文；Issue 上無 receipt marker，模型／工具與 GitHub author 皆不可驗證）；core_pain_resolved no；self_run 4 項；findings 1 項（blocking 1）；attempt WF-CLI-ROUTING-TIER1-e0-26a0149262ac1d99fa9bd0f6490be531a7ec0978。
- 2026-08-11T13:48:21+08:00 amend by wf-cli（op b5ef4049）→ 驗收條件：原值「[ ] open 支援指定執行／查核的建議能力層級與理由，並渲染成 templates/tasks-card.md 第 4 行的格式；[ ] 缺層級時的處理必須明確（硬拒或預設＋警示，擇一並寫明理由）；不得靜默產出不符範本的卡；[ ] 卡面引用「能力層級」而非模型名（MODEL_ROUTING：名單會過期、層級是穩定介面）；[ ] 與 --tier／級別（T0–T4 風險級別）的命名碰撞須在 --help 與 README 明確區分，避免誤以為已有此欄位」→ 新值「open 支援指定執行／查核的建議能力層級與理由，並渲染成 templates/tasks-card.md 第 4 行的格式。；缺層級時的處理必須明確（硬拒或預設＋警示，擇一並寫明理由）；不得靜默產出不符範本的卡。；卡面引用「能力層級」而非模型名（MODEL_ROUTING：名單會過期、層級是穩定介面）。；與 --tier／級別（T0–T4 風險級別）的命名碰撞須在 --help 與 README 明確區分，避免誤以為已有此欄位。；**（2026-08-11 追加，承 R1-001）assign 端的偏離留痕**：MODEL_ROUTING.md 第 14 行後半要求「派工時可依可用性偏離建議，但實際模型與偏離理由記入 claim 事件」。assign 須接受實際模型（能力層級語彙同開卡端），並在**實際層級與卡面建議不符時 fail-closed 要求偏離理由**；兩者一併寫入 assign／claim 事件的 Log。相符時不強制理由。；**本卡完成後，「路由決定於規劃期」的規劃端與派工端皆須由唯一寫入通道執行**；README 不得再宣稱本卡未涵蓋派工端。」；理由 需求方 2026-08-11 裁定把 R1-001 納入本卡而非拆卡：查核者指出 assign 無法記錄實際模型、更無法在偏離時要求理由，故 MODEL_ROUTING.md 第 14 行後半仍僅是文字；拆卡則本卡不得宣稱該契約已落地。同時擴充資源宣告含 assign_cmd.py，並將級別由 T2 提為 T3——本卡自此改動 assign 事件的必填欄位語意，屬 control-plane 契約變更而非局部修正。
- 2026-08-11T13:48:21+08:00 amend by wf-cli（op b5ef4049）→ 驗證：原值「[ ] 測試涵蓋渲染格式、缺欄處理，以及能力層級與 T0–T4 不相混；[ ] 以 #17／#19／#20 的實際開卡情境重放，證明新版產出符合 templates/tasks-card.md 第 4 行格式」→ 新值「測試涵蓋渲染格式、缺欄處理，以及能力層級與 T0–T4 不相混。；以 #17／#19／#20 的實際開卡情境重放，證明新版產出符合 templates/tasks-card.md 第 4 行格式。；**assign 偏離專項**：實際層級等於建議時不要求理由且照常派工；不等於建議且未給理由時 fail-closed 拒絕派工；給了理由則兩者皆寫入 Log 且可被讀回。三種情形各有測試。」；理由 需求方 2026-08-11 裁定把 R1-001 納入本卡而非拆卡：查核者指出 assign 無法記錄實際模型、更無法在偏離時要求理由，故 MODEL_ROUTING.md 第 14 行後半仍僅是文字；拆卡則本卡不得宣稱該契約已落地。同時擴充資源宣告含 assign_cmd.py，並將級別由 T2 提為 T3——本卡自此改動 assign 事件的必填欄位語意，屬 control-plane 契約變更而非局部修正。
- 2026-08-11T13:48:21+08:00 amend by wf-cli（op b5ef4049）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/card.py", "file:cli/src/wf_cli/commands/open_cmd.py", "file:cli/tests/test_card.py", "file:cli/tests/test_commands_mocked.py", "file:cli/tests/test_amend.py", "file:cli/tests/test_review.py", "file:cli/README.md" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/card.py、file:cli/src/wf_cli/commands/open_cmd.py、file:cli/src/wf_cli/commands/assign_cmd.py、file:cli/tests/test_card.py、file:cli/tests/test_commands_mocked.py、file:cli/tests/test_amend.py、file:cli/tests/test_review.py、file:cli/README.md」；理由 需求方 2026-08-11 裁定把 R1-001 納入本卡而非拆卡：查核者指出 assign 無法記錄實際模型、更無法在偏離時要求理由，故 MODEL_ROUTING.md 第 14 行後半仍僅是文字；拆卡則本卡不得宣稱該契約已落地。同時擴充資源宣告含 assign_cmd.py，並將級別由 T2 提為 T3——本卡自此改動 assign 事件的必填欄位語意，屬 control-plane 契約變更而非局部修正。
- 2026-08-11T13:48:21+08:00 amend by wf-cli（op b5ef4049）→ 級別：原值「T2」→ 新值「T3」；理由 需求方 2026-08-11 裁定把 R1-001 納入本卡而非拆卡：查核者指出 assign 無法記錄實際模型、更無法在偏離時要求理由，故 MODEL_ROUTING.md 第 14 行後半仍僅是文字；拆卡則本卡不得宣稱該契約已落地。同時擴充資源宣告含 assign_cmd.py，並將級別由 T2 提為 T3——本卡自此改動 assign 事件的必填欄位語意，屬 control-plane 契約變更而非局部修正。
- 2026-08-11T13:48:52+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 1；SHA 26a0149262ac1d99fa9bd0f6490be531a7ec0978；證據 R1-001 依需求方裁定納入本卡：卡面已 amend（op 見 Log）新增 assign 端偏離留痕的驗收與驗證、資源宣告含 assign_cmd.py、級別 T2→T3。其餘四個攻擊點查核者皆判無 finding。
- 2026-08-11T13:58:55+08:00 handoff by wf-cli → owner 跨家族查核（待需求方指派）；iteration 1；SHA d81d604d0bd393cf5126103c682eee7a6b04e73b；證據 R1-001 已修：assign 新增必填 --actual-capability 與 --capability-deviation-reason，比對走四格全函數（matched/deviated/absent/ambiguous），後三格 fail-closed 要求理由且零寫入。cd cli && uv run pytest -q → 350 passed（基線 main 292，新增 58、移除 0，以 --collect-only 逐項 diff 產出）；卡面驗證三情形各有測試（相符不要求理由、不符未給理由拒絕且 owner/交付狀態/body 皆未變、給了理由則實際層級與理由皆入 Log 可讀回）。ruff findings 與 main 逐項比對為同一集合。查證：FIELD_SPECS 13 欄無能力層級欄位，Issue body 解析是唯一路徑，脆弱性三點已在 README 明列；以 #21 實際 body（含 12 行 Log 引用舊值）實跑分類為 absent，未誤讀 Log 歷史。。
- 2026-08-11T16:26:36+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 獨立校讀（需求方於對話中轉貼原文；查核者聲明未執行 wfcli review 亦未留 receipt marker，故模型／工具與 GitHub author 皆不可驗證）；core_pain_resolved no；self_run 4 項；findings 2 項（blocking 1）；attempt WF-CLI-ROUTING-TIER1-e0-d81d604d0bd393cf5126103c682eee7a6b04e73b。
- 2026-08-11T16:27:26+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 2；SHA d81d604d0bd393cf5126103c682eee7a6b04e73b；證據 R2：R1-001 判 resolved；新增 R2-001（major blocking，解析器對破損卡面誤判 matched／absent）與 R2-002（minor，零寫入測試非呼叫可觀測）。
- 2026-08-11T16:34:56+08:00 handoff by wf-cli → owner 跨家族查核（待需求方指派）；iteration 2；SHA 8cfb1b312a611280ace9880cbf98f9014b293c30；證據 R2-001 已修：解析器改兩段判定（先判該行是否自稱新制，自稱了就須完整合格否則 ambiguous；完全無痕跡才 absent），並逐欄驗執行與查核兩軸的層級與理由。查核者提的兩個 case（空理由誤判 matched、半形空格誤判 absent）皆已修並各有精確回歸測試；另自查出查核者未列的第三個洞（查核軸層級從未驗證）一併修正。破壞方式系統性列舉 16 種各有測試：13 種→ambiguous、2 種無語意空白→仍 matched、1 種真舊格式→absent，且每種破壞另有一條「Log 不得寫成卡面無建議層級」斷言。R2-002 已修：新增 _RecordingRunner 代理記錄每次 gh 呼叫，斷言拒絕路徑零 mutation，另加反向測試防探針沒接上；措辭同步收斂為「拒絕路徑不做任何 item／body mutation」，不再稱零寫入。cd cli && uv run pytest -q → 381 passed（基線 main 292，上輪 350，本輪淨增 31：新增 32、移除 1 為改名的舊零寫入測試）。反向驗證：拿掉 fail-closed 閘門後新測試如預期轉紅，非空斷言。ruff findings 與 main 逐項比對為同一集合。以 #21 實際 body 重跑分類仍為 absent。。
- 2026-08-11T18:18:58+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 獨立校讀（需求方於對話中轉貼原文；無 receipt marker，來源不可驗證）；core_pain_resolved no；self_run 4 項；findings 1 項（blocking 1）；attempt WF-CLI-ROUTING-TIER1-e0-8cfb1b312a611280ace9880cbf98f9014b293c30。
- 2026-08-11T18:19:20+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 3；SHA 8cfb1b312a611280ace9880cbf98f9014b293c30；證據 R3：R2-002 resolved（_RecordingRunner 經突變測試證實接得上）；R2-001 仍開啟並改記為 R3-001——替代判準以自然語言 token 當版本訊號，造成舊卡誤攔與零寬字元破壞的新卡誤判 absent。
- 2026-08-11T18:30:36+08:00 handoff by wf-cli → owner 跨家族查核（待需求方指派）；iteration 3；SHA 6325ae2ca0972ee10f9440d6f73cd7bc80eff6b4；證據 R3-001 已修。先答事實問題：舊卡與新卡在 body 內容上不可區分——舊制執行／查核欄是不受限自由文字，可產生與新制逐位元組相同的一行（已寫成測試釘住）；真實語料 #16／#22–#25 佐證全形括號＋自由文字是常態。故改用遷移標記 <!-- wf-routing:v1 -->：open 在新制卡寫入，分類只查標記存在與否，內容完全不參與版本判定。標記不在→absent；標記在→須恰一行合格路由行否則 ambiguous，無退回舊卡路徑。刻意不做零寬字元正規化（標記是布林事實，不受行內破壞影響；再加正規化等於重造猜測層）。查核者五個注入案例全部通過：舊卡含「依建議降級」→absent、舊卡含「主力型模型當班」→absent、新制行前置 U+200B→ambiguous、層級內插 U+200B→ambiguous、理由含「依建議降級」的合格新卡→matched。真實語料 18 張卡全掃：17 張 absent，1 張（#15）ambiguous 因其 body 排版本就損壞（字面 \n 破壞 ## Log），屬正確 fail-closed。cd cli && uv run pytest -q → 401 passed（基線 main 292，上輪 381，本輪新增 20、移除 0）。ruff findings 與 main 逐項比對為同一集合。。
- 2026-08-11T19:02:32+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 獨立校讀（留有 receipt marker；PM 重算 report_sha256 相符——取材＝marker 之後的報告原文 strip()）；core_pain_resolved no；self_run 4 項；findings 2 項（blocking 2）；attempt WF-CLI-ROUTING-TIER1-e0-6325ae2ca0972ee10f9440d6f73cd7bc80eff6b4。
- 2026-08-11T19:04:48+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 4；SHA 6325ae2ca0972ee10f9440d6f73cd7bc80eff6b4；證據 R4：R3-001 resolved。R4-001（executor）marker 以 in head 子字串判定，amend 可寫入 head 使舊卡誤升 ambiguous；R4-002（planner）遺留卡遷移未明定——需求方裁定既有卡永久以 absent 派工、不補 marker、不新增遷移入口，須寫入卡面。
- 2026-08-11T19:05:29+08:00 amend by wf-cli（op 66180d6c）→ 驗收條件：原值「[ ] open 支援指定執行／查核的建議能力層級與理由，並渲染成 templates/tasks-card.md 第 4 行的格式。；[ ] 缺層級時的處理必須明確（硬拒或預設＋警示，擇一並寫明理由）；不得靜默產出不符範本的卡。；[ ] 卡面引用「能力層級」而非模型名（MODEL_ROUTING：名單會過期、層級是穩定介面）。；[ ] 與 --tier／級別（T0–T4 風險級別）的命名碰撞須在 --help 與 README 明確區分，避免誤以為已有此欄位。；[ ] **（2026-08-11 追加，承 R1-001）assign 端的偏離留痕**：MODEL_ROUTING.md 第 14 行後半要求「派工時可依可用性偏離建議，但實際模型與偏離理由記入 claim 事件」。assign 須接受實際模型（能力層級語彙同開卡端），並在**實際層級與卡面建議不符時 fail-closed 要求偏離理由**；兩者一併寫入 assign／claim 事件的 Log。相符時不強制理由。；[ ] **本卡完成後，「路由決定於規劃期」的規劃端與派工端皆須由唯一寫入通道執行**；README 不得再宣稱本卡未涵蓋派工端。」→ 新值「open 支援指定執行／查核的建議能力層級與理由，並渲染成 templates/tasks-card.md 第 4 行的格式。；缺層級時的處理必須明確（硬拒或預設＋警示，擇一並寫明理由）；不得靜默產出不符範本的卡。；卡面引用「能力層級」而非模型名（MODEL_ROUTING：名單會過期、層級是穩定介面）。；與 --tier／級別（T0–T4 風險級別）的命名碰撞須在 --help 與 README 明確區分。；assign 端的偏離留痕：assign 須接受實際模型（能力層級語彙同開卡端），並在實際層級與卡面建議不符時 fail-closed 要求偏離理由；兩者一併寫入 assign／claim 事件的 Log。相符時不強制理由。；本卡完成後，「路由決定於規劃期」的規劃端與派工端皆須由唯一寫入通道執行；README 不得再宣稱本卡未涵蓋派工端。；**（2026-08-11 追加，承 R4-001）遷移標記須以結構位置辨識**，不得以子字串出現與否判定：標記須為獨立一行且緊鄰唯一路由行。須加回歸測試——舊卡經 amend 或任何自由文字含該標記字串時，仍須判 absent。；**（2026-08-11 追加，承 R4-002；需求方裁定）既有 18 張卡永久以 absent 派工**：不補標記、**不新增任何受控遷移入口**。理由：(1) R4-001 已證明「能寫入 head 的入口即漏洞來源」，新增遷移入口就是新增第二個必須自證不會重蹈 R4-001 的入口；(2) 事後補填的四個路由值未必反映規劃期判斷，違反 MODEL_ROUTING.md 第 14 行「路由決定於規劃期」。**代價（既有卡至結案前每次派工需多帶偏離理由，且該理由實質為雜訊）需求方已知悉並接受。** README 不得暗示未來會補遷移入口。」；理由 R4 兩項處置入卡面：R4-001 要求標記改為結構位置辨識；R4-002 為 planner 類 finding，需求方裁定既有卡永久 absent 且不新增遷移入口，該裁定須寫入卡面而非只留在 Issue 留言。
- 2026-08-11T19:12:16+08:00 handoff by wf-cli → owner 跨家族查核（待需求方指派）；iteration 4；SHA 19f5a0f10db741adb7a86564b164d3bdbc1926bc；證據 R4-001 已修：宣告改由結構位置判定，三條件須同時成立——(1) 獨立成行（整行 strip 後恰等於標記）(2) 位於標頭區（第一個 '## ' 標題之前，amend 的驗收/驗證/資源宣告都在章節內故結構上碰不到）(3) 緊鄰唯一合格路由行。任一不成立即無宣告→absent；宣告成立卻讀不出合格路由行→ambiguous。另擋 amend --spec-baseline 含換行（標頭區唯一其他寫入路徑，單行欄位須保持單行否則可長出偽宣告行）。回歸測試 12 項：五種 amend 注入仍 absent、三種行內出現不成立、章節內出現不成立、未緊鄰→ambiguous、兩宣告→ambiguous、spec-baseline 換行遭拒。突變驗證：把判定退回 'ROUTING_MARKER in head' 後 test_card.py 22 項轉紅，斷言非空。R4-002 已依需求方裁定寫入 README：既有 18 張卡永久 absent，明說是最終行為非過渡，且不得暗示未來會補遷移入口；已 grep 確認無殘留暗示，並移除已被打穿的殘留假設宣稱。測試：413 passed（基線 main 292，上輪 401，本輪新增 12、移除 0）。ruff 0.16.2 逐項輸出（worktree 與 main 完全相同，9 項全為既有）：src/wf_cli/commands/amend_cmd.py I001；src/wf_cli/commands/amend_cmd.py RUF100；src/wf_cli/doctor.py FURB167；src/wf_cli/doctor.py I001；tests/test_amend.py F841；tests/test_amend.py PLW1510；tests/test_amend.py RUF059 x2；tests/test_doctor.py I001。diff 兩側輸出為 IDENTICAL。。
- 2026-08-11T20:43:21+08:00 handoff by wf-cli → owner 跨家族查核（待需求方指派）；iteration 4；SHA c8ffc3e7ed0b4122474485cf6ffb5499c1a12acf；證據 R4-003 已修（基於 19f5a0f 續作）。根因：候選路由行用 startswith 嚴格收集，任何讓前綴失配的擾動都讓該行靜默消失，於是兩條路由行降成一條 → matched 且免除理由。修法是把判準改成「失敗往哪邊倒」：偵測側（誰算候選）寬鬆——NFKC 折疊全形半形＋去除 Cc/Cf/Mn/Me 不可見與格式字元＋去除所有空白後比前綴，寧可多收；受理側（能否當基線）嚴格——一律用原始行比對，不套用任何偵測正規化。兩側皆不可能產出偽 matched。方向性紅線已寫入 card.py 註解。R3-001 當時「不需正規化」的論證邊界已在碼與 README 修正：對標記辨識成立（漏認→absent→保守側），對多行掃描不成立。驗證：八種遮蔽第二條路由行的擾動（ZWSP/BOM/ZWJ/VS16/全形冒號改半形/前綴多空白/行尾空白/兩條都正常）全部 ambiguous，單條對照仍 matched。性質斷言（非列舉）：三個基準卡面 × 在 Log 之前每行每位置插入六種不可見字元，斷言原本要理由者破損後仍要理由，全數通過。突變驗證：把候選判定退回 startswith 後，性質測試與六項列舉測試共 7 項轉紅，斷言非空。真實語料 18 張卡回歸不變（17 absent、1 ambiguous 為 #15 既有排版損壞）。測試：426 passed（基線 main 292，上輪 413，本輪新增 13、移除 0）。ruff 0.16.2 逐項輸出，worktree 與 main 兩側 diff 為 IDENTICAL，9 項全為既有：amend_cmd.py:31:1 I001；amend_cmd.py:260:44 RUF100；doctor.py:7:1 I001；doctor.py:228:67 FURB167；test_amend.py:490:5 F841；test_amend.py:620:5 RUF059；test_amend.py:632:5 RUF059；test_amend.py:682:11 PLW1510；test_doctor.py:1:1 I001。。
- 2026-08-11T21:20:12+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 跨家族查核（需求方於對話中轉貼原文；無 receipt marker，來源不可驗證）；core_pain_resolved no；self_run 4 項；findings 3 項（blocking 1）；attempt WF-CLI-ROUTING-TIER1-e0-c8ffc3e7ed0b4122474485cf6ffb5499c1a12acf。
- 2026-08-11T21:32:50+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 5；SHA c8ffc3e7ed0b4122474485cf6ffb5499c1a12acf；證據 R5：blocking R5-001（候選偵測可因未涵蓋的 Unicode 類別縮減候選集合而誤放行 matched）；非阻擋 R5-002（mutation 宣稱 7 實測 6）、R5-003（性質測試以數量代替位置覆蓋）。escalation checkpoint 見 #issuecomment-5253853989：第二條件成立故 decision=escalate，需求方裁定 continue、維持同執行者；並裁定 R5-001 與 R4-001 同根因家族（代表 routing-marker-unanchored-head-substring）。。
- 2026-08-11T22:02:24+08:00 handoff by wf-cli → owner 跨家族查核（待需求方指派）；iteration 5；SHA e928050d52cb585906d9a6928c4a2f7ad2c961ea；證據 R6：R5-001 已修，且非補列舉——候選資格改為「已知非路由行」的補集，已知判準是原始行對固定字面前綴 startswith，故插入任何字元只能破壞前綴比對而更嚴，不可能憑空造出前綴；_detection_key 與字元類別清單整段刪除。PM 獨立重現：查核者的 U+02B0(Lm)／U+0378(Cn) 兩案例現皆 ambiguous，另測 U+200B／U+E000 私用區／U+1F600／反斜線亦 ambiguous，單條對照仍 matched。「緊鄰唯一候選可保護漏網擾動」的不成立宣稱已自碼註解與 README 移除。R5-002：重跑該突變得 7 個 node id（6 參數化＋1 性質測試），與查核者實測 6 的差異為計數口徑，本輪改附切點與 node id 組成。R5-003：改為 (行號,位置,字元) 三元組集合等於獨立算出的全集。pytest 437 passed（main 基線 292、上輪 426）。突變三組：候選收集退回 startswith→17 紅、退回 R5-001 版→11 紅、性質產生器少掃末位→4 紅。ruff 與 main 逐項 diff IDENTICAL。執行者自承三個未關的面（借殼行、同行語意竄改、收緊判準的保守誤判）已寫入 README；PM 抽測四種借殼變體皆 ambiguous，未能打穿，但非證明。。
- 2026-08-12T01:14:58+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex 子代理（收據 issuecomment-5256357740，多行格式合規；PM 已依其取材規則自 GitHub 回讀重算 report_sha256=d9970c7b… 相符。留言 GitHub author 為 ruan6047 即需求方轉貼，故平台可驗證的是「該文字確由需求方發布」，非「該文字由 Codex 產出」）；core_pain_resolved yes；self_run 6 項；findings 0 項（blocking 0）；attempt WF-CLI-ROUTING-TIER1-e0-e928050d52cb585906d9a6928c4a2f7ad2c961ea。
- 2026-08-12T06:46:41+08:00 handoff by wf-cli → owner 已收尾；iteration 5；SHA e928050d52cb585906d9a6928c4a2f7ad2c961ea；證據 跨家族查核 R6 判 APPROVE、0 blocking（收據 issuecomment-5256357740，PM 已依其自載取材規則回讀重算 report_sha256=d9970c7b… 相符）。PR #32 已合併（a5d4770），e928050 確為 main 祖先。收尾七步前三步已完成並逐項核對：無未提交變更、無 stash、非任何 shell 的 cwd、分支 tip 已是 main 祖先；worktree 已移除、本地分支已刪、遠端分支以條件式刪除（--force-with-lease 帶當下 tip）刪除，三者皆已驗證不存在。刻意未使用 WF-CLEANUP-GUARD1 的 --cleanup 路徑——該卡仍在查核中，不以未經查核的 T4 破壞性程式碼處理真實卡片；本次為手動執行 worktree-lifecycle.md 第 11 行的既有清單。。
- 2026-08-26T22:08:08+08:00 amend by wf-cli（op b817c59e）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:2f8f1169999d3c862ed4e385a7c0ce769014442a5f864bafda5a4875a67aec96 (765 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5244255811 · 2026-08-10T18:23:25Z

## 本卡自身即為痛點的現場證據

本卡以 `wfcli open` 建立，其執行／查核欄產出為：

```
- 執行：待指派　查核：獨立校讀
```

而 `templates/tasks-card.md` 第 4 行要求：

```
- 執行：<模型@工具／待指派>（建議 <MODEL_ROUTING 能力層級>；<能力軸理由>）　查核：<模型@工具／待指派>（<層級；紅線須跨家族或人工>；須 ≠ 執行）
```

**開這張卡的動作本身就產生了一張不符範本的卡**，而工具沒有報錯——這正是核心痛點描述的形態。同日以相同方式開立的 #17／#19／#20 皆然。

### 命名碰撞（驗收第 4 條的由來）

`--tier`／Project 的 `級別` 是 **T0–T4 風險級別**；`MODEL_ROUTING.md` 的能力層級是**經濟型／主力型／高階型**。兩者都叫「層級」，容易讓人以為工具已支援。查證時三處（`open` 的 21 個旗標、`Card` dataclass、Project 13 個凍結欄位）皆無能力層級欄位。

### 已結案卡的回填

#17／#19／#20 已 merge 或待查核。執行者建議**不回填**：那三張卡的實際執行與查核者都已載於 Log 與 handoff 事件，回填層級只是補檔案、不改變任何已做出的判斷。若需求方認為留痕完整性優先，可於本卡完成後以 `wfcli amend` 補。

## Comment 5249198958 · 2026-08-11T05:05:15Z

## PM 複核註記（派審前）

執行者交付後，PM 獨立複核，三件事留痕。

**一、可查證的宣稱已複驗通過。**

| 宣稱 | 複驗方式 | 結果 |
|---|---|---|
| `26a0149262ac1d99fa9bd0f6490be531a7ec0978` 已推送 | `git rev-parse origin/claude/WF-CLI-ROUTING-TIER1` | 相符 |
| 324 passed | 在 worktree 獨立重跑 `uv run pytest -q` | **324 passed** |
| 三級語彙未自創 | 讀 `MODEL_ROUTING.md` 第 5–10 行 | 相符。表格四列去修飾後確為三級；第 9 行「高階型 **+ 跨家族 review**」的加號後段是查核獨立性附加要求（同 `templates/tasks-card.md` 第 4 行「紅線須跨家族或人工」），第 7 行「／deterministic automation」是同一級的英文註解——**兩者都不是第四級**，執行者的讀法成立 |

**二、資源宣告與實際寫入不符，已補正。**

實際改動 7 檔，其中 `cli/tests/test_amend.py`、`cli/tests/test_review.py` **不在原資源宣告內**。執行者在報告中以散文揭露了這兩檔，但**沒有先擴充宣告**。

資源宣告是互斥契約的**事實面**——寫入超出宣告，該面就失效，其他卡的派工交集檢查會據以放行一個實際會撞的組合。已由 PM `amend` 補正（`op eeb4fc50`），原值完整寫入 Log。

> **這不是苛責**：新旗標成為必填後，那兩檔自建的 `open` argv 必然要同步，是合理的連帶改動。**正確程序是先 `amend` 宣告再寫**，而非事後在報告裡說明。此形態與 [#24](https://github.com/ruan6047/ai-workflow/issues/24) 要解的問題同源：宣告若不等於實際寫入集，守衛就只是宣稱。

**三、handoff 證據欄有一處數字錯誤，執行者已自陳。**

`handoff` 的 `--evidence` 寫「基線 296，新增 28 項」，正確值為**基線 292、新增 32**（`324 passed` 本身正確）。`wfcli` 無修正既有 Log 證據的通道，故以本則為準。**執行者主動揭露而非被抓到**，記此以示區別。

**查核者請以本則的數字與資源宣告為準，並注意上述第二點在你的驗收範圍內。**


## Comment 5249337307 · 2026-08-11T05:28:44Z

## 派審：WF-CLI-ROUTING-TIER1

審核對象 **`ruan6047/ai-workflow#21`**（Issue）。⚠️ **不是 `cpbl-analytics#21`**——先核對 repo；若看到棒球資料相關內容，立刻停止並回報。

**T2 程式碼卡**，卡面查核欄為「獨立校讀」——**不強制跨家族，但不得由執行本卡的同一 session 進行**。執行者為 Claude Opus 5@Claude Code 的子 agent。

### 進駐與身分核對

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-routing-tier1
分支：claude/WF-CLI-ROUTING-TIER1
被審 SHA：26a0149262ac1d99fa9bd0f6490be531a7ec0978
基線：origin/main 7451b72ba7679893043950d71bad9642665e25da
iteration：0（首次查核）
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-routing-tier1
git rev-parse HEAD && git diff --stat origin/main
cd cli && uv run pytest -q
```

預期 `26a0149…`、**7 個檔案（+503 / −6）**、**324 passed**。

### 這張卡在做什麼

canonical `AI_WORKFLOW.md` 第 100 行要求「Plan 產出必含建議執行／查核能力層級與理由」，`MODEL_ROUTING.md` 第 14 行要求「路由決定於規劃期、卡面引用**層級**而非模型名」。但 `wfcli open` 沒有這個欄位——**規則只存在於範本文字，唯一寫入通道不執行它**。本卡補上。

新增四個旗標：`--exec-capability`／`--exec-capability-reason`／`--review-capability`／`--review-capability-reason`，渲染集中在 `card.format_routing_line()`，git spec 檔與 Issue body 共用一個渲染點。

### 本輪請特別攻擊這五點

1. **三級枚舉是否真的來自既有權威。** 執行者主張 `MODEL_ROUTING.md` 第 5–10 行的表格四列去修飾後恰好三級（`經濟型`／`主力型`／`高階型`），理由是第 7 行「／deterministic automation」是同一級的英文註解、第 9 行「+ 跨家族 review」是查核**獨立性附加要求**而非第四級。**請獨立複驗這個讀法**——這是本 repo 反覆被抓到的形態（自訂分類覆蓋既有權威分類），執行者宣稱沒犯，請自行判斷。
2. **缺層級時「硬拒」是否正確。** 執行者選擇不給預設值，理由是「預設值等於在未讀本卡風險的前提下代替規劃者作答，只是把靜默不符範本換成靜默填錯層級」。請判斷這個取捨，以及**雙層擋**（CLI 層 argparse ＋ model 層 `Card` dataclass 必填區）是否真的擋得住繞過 CLI 的路徑。
3. **兩軸命名碰撞。** `--tier` 是風險級別 T0–T4，新旗標是能力層級——值域零交集，兩個方向的誤填都被 argparse 硬擋。**請找出仍會混淆的使用情境**，或確認 README 的對照表足夠。
4. **測試是否真的守得住。** 有一個測試直接解析 `MODEL_ROUTING.md` 表格抽出權威三級並斷言集合相等（語彙一漂移測試就紅）。**請確認該測試不是恆真**——例如若表格解析失敗回傳空集合，斷言會不會 vacuously pass？**本 repo 出現過「空集合讓 `all()` 為真」的假 OK。**
5. **兩項刻意不做的判斷是否正確。** (a) 未把能力層級加進 `project.py::FIELD_SPECS`，理由是它是規劃期一次性建議、不是 current-state，多開一欄會製造第二真相來源；(b) 未改 `assign` 的偏離留痕（`MODEL_ROUTING.md` 第 14 行後半），理由是卡面驗收只涵蓋開卡端。兩者都寫了理由而非靜默略過，但**請判斷理由是否成立**，特別是 (b) ——沒有偏離留痕，第 14 行後半仍然只存在於文字。

### 執行者已揭露、PM 已複核的三件事

詳見本 Issue 的 [PM 複核註記](https://github.com/ruan6047/ai-workflow/issues/21#issuecomment-5249198958)，摘要：

1. **資源宣告與實際寫入不符，已由 PM 補正**（`op eeb4fc50`）。實際改動 7 檔，其中 `cli/tests/test_amend.py`、`cli/tests/test_review.py` 不在原宣告內；執行者以散文揭露但未先 `amend`。**此形態在你的驗收範圍內**——宣告若不等於實際寫入集，互斥守衛就只是宣稱。
2. **handoff 證據欄有數字錯誤**：寫「基線 296、新增 28」，正確為**基線 292、新增 32**（`324 passed` 本身正確）。`wfcli` 無修正既有 Log 的通道，以 PM 註記為準。**執行者主動揭露而非被抓到。**
3. **PM 已獨立複驗**：SHA、324 passed、三級語彙三項皆相符。

### 環境紅線與獨立性

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。

留言紀律：**不得讓任何一行以 `<!--` 緊接事件 marker 前綴起始**（會使本卡停機）；行中提及安全。

無法執行 `wfcli` 時，請依 `templates/handoff-contract.md` §3.1.2 留 receipt marker 收據（`card_id`、完整 `source_sha`、查核報告原文 UTF-8 `report_sha256`）由 PM 轉錄。**請盡量讓結構化區塊的 YAML 可直接解析**（值含 `#` 加引號、圍籬記得閉合）。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5249412960 · 2026-08-11T05:40:55Z

<!-- wf-review-event:v1 card_id=WF-CLI-ROUTING-TIER1 source_sha=26a0149262ac1d99fa9bd0f6490be531a7ec0978 attempt_id=WF-CLI-ROUTING-TIER1-e0-26a0149262ac1d99fa9bd0f6490be531a7ec0978 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CLI-ROUTING-TIER1`　attempt_id：`WF-CLI-ROUTING-TIER1-e0-26a0149262ac1d99fa9bd0f6490be531a7ec0978`
- 查核者：獨立校讀（需求方於對話中轉貼原文；Issue 上無 receipt marker，模型／工具與 GitHub author 皆不可驗證）　escalation_epoch：0
- source_sha：`26a0149262ac1d99fa9bd0f6490be531a7ec0978`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-11T13:40:54+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git diff --stat origin/main`
  - repo 為 ruan6047/ai-workflow；HEAD 26a0149262ac1d99fa9bd0f6490be531a7ec0978，7 檔 +503/-6，worktree 乾淨。
- `cd cli && uv run pytest -q`
  - 324 passed in 1.96s。
- `cd cli && uv run python（解析 MODEL_ROUTING.md 並直接建構 Card）`
  - 權威解析與實作皆為 經濟型／主力型／高階型；T3 填能力層級被 ValueError 拒絕；缺四欄直接建構 Card 會 TypeError。
- `cd cli && uv run wfcli open --help`
  - --tier 與四個 capability 旗標及 README 對照表均清楚區分兩軸。

### findings（1，其中 blocking 1）

- **WF-CLI-ROUTING-TIER1-R1-001**　severity=major　blocking=true　class=authoritative-artifact　attribution=planner　root_cause_id=`routing-deviation-not-enforced`
  - evidence：MODEL_ROUTING.md 明定派工可偏離規劃建議，但實際模型與偏離理由必須記入 claim 事件。現有 assign_cmd.py 僅接受 assignee/branch/worktree/status，Log 只記 owner、分支與狀態；無法記錄實際模型，更無法在偏離時要求理由。README 亦明言本卡未處理此項，故該權威規則仍僅是文字。
  - disposition：將 assign 的實際模型與偏離理由納入唯一寫入通道；至少在實際模型不同於卡面建議時 fail-closed 要求理由，並把兩者寫入 claim/assign 事件。若需另卡，須由需求方明示拆卡後，本卡不得宣稱整個「路由決定於規劃期」契約已落地。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5249454821 · 2026-08-11T05:47:38Z

## PM 補記：R1 裁決的來源說明與散文結論

### 一、轉錄來源與其限制（查核者已主動更正，此處確認一致）

前一則 `wfcli review` 寫入的裁決，**來源是需求方於對話中轉貼的查核輸出，Issue 上並無 receipt marker 收據**。查核者本人亦已聲明：該報告未寫入 Issue、無收據，僅為本地唯讀查核輸出，不得宣稱 Issue 上已有收據。

**兩邊一致，無矛盾。** 轉錄時 `--reviewer` 欄即已載明：

> 獨立校讀（需求方於對話中轉貼原文；Issue 上無 receipt marker，模型／工具與 GitHub author 皆不可驗證）

依 `docs/WF-25-REVIEW-WRITE-CHANNEL1.md` §3，這是 **C 方案（純 PM 轉錄）**，其已知限制為：`report_sha256` 無從重算、GitHub author 無從驗證、模型／工具僅為自述。**不得把自由字串升格為已驗證身分。**

查核者未執行 `wfcli review` 是**遵守派審詞的環境紅線**（不得改 Project 狀態），非違規。

### 二、散文結論補記（不在結構化區塊內，故另記）

派審詞列了五個攻擊點，查核者對其中四點的結論如下——**四點皆判無 finding**：

| 攻擊點 | 結論 |
|---|---|
| 三級枚舉的權威讀法 | **正確**。斜線為同級註解、「+ 跨家族 review」是附加獨立性要求，皆非第四級 |
| 守語彙的測試會不會恆真 | **不會**。表格解析成空集合時，`CAPABILITY_TIERS` 非空，集合相等斷言會**失敗**而非 vacuously pass |
| 缺層級硬拒 ＋ 雙層防線 | **合理**；README 兩軸對照足以降低 CLI 誤填 |
| 不新增 `FIELD_SPECS` | **合理**：這是卡面上的規劃期建議，不是可變 current-state |

另：資源宣告已由 PM 補正為實際 7 檔、handoff 測試數字錯誤已由 PM 註記校正，**兩者均不另列 finding**。

> 第二點值得標記：我在派審詞裡援引本 repo 曾出現的「空集合讓 `all()` 為真」先例要求查核該測試，查核者**實際檢查了斷言形式**而非接受宣稱——結論是該測試用的是集合相等而非全稱量化，故不具該風險。**這是一個被排除的假設，不是一個未被檢查的假設。**

### 三、唯一 blocking 的處置

`R1-001`（`routing-deviation-not-enforced`）：需求方裁定**納入本卡**，不拆卡。卡面將相應 `amend`。


## Comment 5249550427 · 2026-08-11T06:01:18Z

## 派審：R2（取代前一則派審詞）

⚠️ 前一則指向 `26a0149`，**已過期**。審核對象仍是 **`ruan6047/ai-workflow#21`**，不是 `cpbl-analytics#21`。

**級別已由 T2 提為 T3**（本卡自此改動 `assign` 事件的必填欄位語意，屬 control-plane 契約變更）。卡面查核欄仍為「獨立校讀」，但依 T3 需獨立查核；**不得由執行本卡的同一 session 進行**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-routing-tier1
分支：claude/WF-CLI-ROUTING-TIER1
被審 SHA：d81d604d0bd393cf5126103c682eee7a6b04e73b
基線：origin/main 7451b72ba7679893043950d71bad9642665e25da
iteration：1
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-routing-tier1
git rev-parse HEAD && git diff --stat origin/main
git diff 26a0149..d81d604            # 本輪新增的部分
cd cli && uv run pytest -q
```

**分支累計為 8 檔 +1063 / −11、350 passed**；本輪新增的是其中 5 檔（`card.py`、`assign_cmd.py`、`test_card.py`、`test_commands_mocked.py`、`README.md`）。全部落在 `amend` 後的資源宣告內（`op b5ef4049` 已加入 `assign_cmd.py`）。

### R1-001 的處置

`MODEL_ROUTING.md` 第 14 行後半（派工可偏離建議，但實際模型與偏離理由須記入 claim 事件）原本無人執行。需求方裁定**納入本卡**，已實作於 `assign`。

**執行者沒有做「相符／不符」二分**，而是四格：

| 結果態 | 情況 | 需要理由 |
|---|---|---|
| `matched` | 卡面有建議且與實際相同 | 否 |
| `deviated` | 卡面有建議且與實際不同 | 是 |
| `absent` | 無「- 執行：」行，或為新制之前的舊格式 | 是 |
| `ambiguous` | 該行不唯一／body 排版損壞／層級不在 `MODEL_ROUTING` 語彙內 | 是 |

### 本輪請攻擊這五點

1. **四格是否真的全函數。** 執行者宣稱三個防「其餘」的機制：理由政策走顯式表 `_REASON_REQUIRED_BY_OUTCOME`（新增結果態忘了決定政策會 `KeyError` 當場炸，有測試鎖）、`log_fragment` 四格各自措辭且末尾 `raise`、以及「四格皆可達」的測試。**請自行構造第五類輸入**——本 repo 已現七例「分類漏一整類輸入」。

2. **`absent`／`ambiguous` 也要理由，這個取捨是否正確。** 執行者的論證是：這兩格是「沒有可比對的基線」而非「比對過且相符」，當成相符等於用沉默宣稱一致性；依據是 `assign` 對目標卡自己的資源宣告解析失敗已經 fail closed。**代價是所有舊卡派工都要多打一個旗標**——請判斷這個代價是否被低估，以及會不會促使人隨便填理由來過關。

3. **解析 Issue body 是唯一路徑，這個脆弱性是否被誠實處理。** 執行者實跑確認 `FIELD_SPECS` 13 欄與 `CARD_FIELD_MAP` 皆無此欄位，故只能解析 body 第 2 行；已在 `card.py` 註解與 README 專節列出三條（依賴渲染形狀但有 round-trip 測試且兩支正規表達式分開維護、不猜一律歸 `ambiguous`、只讀 `## Log` 之前）。**請攻擊第三條**：切在 `## Log` 之前是否涵蓋所有 Log 引用舊值的形態？若某次 `amend` 的原值本身含 `## Log` 字樣會怎樣？

4. **零寫入的驗證是否真的零寫入。** 執行者宣稱「不符且未給理由時 exit 2 且 owner、交付狀態、body 三者皆與派工前逐一相等」。**請確認該測試比對的是實際遠端呼叫而非只有回傳值**——本 repo 出現過「探針通過但程式不正確」的先例。

5. **`absent` 的 Log 不得寫成「偏離」。** 執行者為此加了專測，理由是沒有建議就沒有東西可偏離、寫成偏離是不實留痕。請確認四格的 `log_fragment` 沒有任何一格產生會誤導後續讀者的措辭。

### 執行者主動揭露、PM 已複核

- **PM 獨立複驗**：`d81d604` 已推、**350 passed**（我在其 worktree 重跑）、8 檔全在宣告內、README 已無 out-of-scope 宣稱（`grep` 確認）。
- **資源宣告兩度由 PM 補正**：`op eeb4fc50`（首輪越界寫入兩個測試檔）、`op b5ef4049`（本輪納入 `assign_cmd.py` 並提 tier）。**第一次是執行者寫超出宣告未先 amend**，此形態在你的驗收範圍內。
- **前一輪 handoff 證據欄有數字錯誤**（寫「基線 296、新增 28」，正確為 292／32），執行者主動揭露，`wfcli` 無修正既有 Log 的通道。本輪數字為 **350 passed、基線 292、新增 58**，執行者稱以 `--collect-only` 逐項 diff 產出——**請抽驗這個數字**。
- **R1 的四個攻擊點查核者皆判無 finding**（三級枚舉讀法正確、守語彙測試不恆真、硬拒合理、不動 `FIELD_SPECS` 合理），詳見本 Issue 的 PM 補記。

### 環境紅線與獨立性

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。

留言紀律：**不得讓任何一行以 `<!--` 緊接事件 marker 前綴起始**；行中提及安全。

**若你不執行 `wfcli`（派審詞的環境紅線本就禁止改 Project 狀態），請明說**——R1 即為此情況，結論由 PM 轉錄並在 `--reviewer` 欄標記為不可驗證來源。若能留 receipt marker 收據（`card_id`、完整 `source_sha`、報告原文 UTF-8 `report_sha256`）則可升為可驗證，PM 會重算比對。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。**R1-001 請明列 `resolved`／`withdrawn`／仍開啟。**


## Comment 5250788778 · 2026-08-11T08:26:37Z

<!-- wf-review-event:v1 card_id=WF-CLI-ROUTING-TIER1 source_sha=d81d604d0bd393cf5126103c682eee7a6b04e73b attempt_id=WF-CLI-ROUTING-TIER1-e0-d81d604d0bd393cf5126103c682eee7a6b04e73b -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CLI-ROUTING-TIER1`　attempt_id：`WF-CLI-ROUTING-TIER1-e0-d81d604d0bd393cf5126103c682eee7a6b04e73b`
- 查核者：獨立校讀（需求方於對話中轉貼原文；查核者聲明未執行 wfcli review 亦未留 receipt marker，故模型／工具與 GitHub author 皆不可驗證）　escalation_epoch：0
- source_sha：`d81d604d0bd393cf5126103c682eee7a6b04e73b`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-11T16:26:36+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git diff --stat origin/main; git diff --check origin/main`
  - ai-workflow repo，SHA d81d604d0bd393cf5126103c682eee7a6b04e73b；8 檔 +1063/-11；無 whitespace error。
- `cd cli && uv run pytest -q`
  - 350 passed in 1.70s。
- `cd cli && uv run pytest --collect-only -q`
  - 350 tests collected；以已確認基線 292 計算，新增 58 項相符。
- `cd cli && uv run python（對 compare_capability_to_card 注入破損卡面）`
  - 缺執行理由的卡面被判 matched；新格式分隔符損壞的卡面被判 absent，均與宣稱的 fail-closed ambiguous 不符。

### findings（2，其中 blocking 1）

- **WF-CLI-ROUTING-TIER1-R2-001**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`malformed-routing-card-misclassified`
  - evidence：以正規 render 的 body 分別注入： 1. `（建議 主力型；） 查核…`：compare_capability_to_card(..., "主力型") 回傳 matched。 2. 將 `） 查核：` 改為 `） 查核：`：回傳 absent，Log 會宣稱「卡面無建議層級」。 兩者都已有可見的建議語意，卻不是舊格式或真正無基線；第一種更會免除理由。
  - disposition：解析器須將任何帶 `- 執行：` 卻不完整符合新制欄位的情形歸為 ambiguous，並要求理由；正規表示式至少須拒絕空的執行／查核能力理由。新增上述兩個回歸測試，確認 Log 不會把格式受損的建議寫成 absent。
- **WF-CLI-ROUTING-TIER1-R2-002**　severity=minor　blocking=false　class=implementation　attribution=executor　root_cause_id=`zero-write-test-not-call-observable`
  - evidence：test_assign_deviation_without_reason_is_refused_with_zero_writes 只比較 FakeGhRunner 的 owner、交付狀態與 body 最終值；FakeGhRunner 未記錄 execute 呼叫。且 assign 在能力 檢查前已呼叫 ensure_fields，若 Project 欄位缺失可先執行 field-create。
  - disposition：為 FakeGhRunner 加入呼叫紀錄，測試拒絕路徑沒有 field/item/body mutation；或明確把保證限縮為 owner、交付狀態、body 三個狀態值不變，勿稱「零寫入」。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5250794198 · 2026-08-11T08:27:12Z

## PM 補記：R2 的來源說明與散文結論

**轉錄來源**：需求方於對話中轉貼；查核者**明確聲明未執行 `wfcli review`、未留 receipt marker**（遵守派審詞「不得改 Project 狀態」的環境紅線）。故本輪同 R1 為 `WF-25` 的 **C 方案（純 PM 轉錄）**，`report_sha256` 無從重算、GitHub author 無從驗證。`--reviewer` 欄已載明。

### 散文結論補記（不在結構化區塊內）

| 項目 | 結論 |
|---|---|
| `R1-001` | **`resolved`**——已納入 `assign` 並記錄實際能力層級與偏離理由 |
| `absent`／`ambiguous` 要理由 | **取捨正確**：它們不是「已比對相符」 |
| 派審詞攻擊點 3（`## Log` 切割） | **策略成立**：`amend` 的原值經 `_fold()` 摺成單行，即使原文含 `## Log`，正常 Log 標題仍唯一 |
| 四格措辭 | 正常路徑正確，`absent` 不會寫成「偏離」——**但 R2-001 的誤分類會產生不實的 absent 留痕** |

> 攻擊點 3 是我在派審詞裡提出的假設（「若某次 amend 的原值本身含 `## Log` 字樣會怎樣」）。查核者**去讀了 `_fold()` 的行為**才下結論，不是接受宣稱。**這是一個被排除的假設。**

### R2-001 值得特別記：兩個 bug 都是注入測出來的

查核者沒有只讀碼，而是對 `compare_capability_to_card` **注入破損卡面**：

1. **`（建議 主力型；）　查核…`（理由為空）→ 判 `matched`** — 不但誤判，還**免除了理由要求**。
2. **全形空格改半形（`）　查核：` → `） 查核：`）→ 判 `absent`** — Log 會寫「卡面無建議層級」，**而卡面明明有建議**。

兩者都不是舊格式、也不是真正無基線。**執行者宣稱的四格「不猜、一律歸 `ambiguous`」在這兩種輸入上沒有生效。**

`attribution` 為 `executor`（實作缺陷），與本卡先前的 `planner` 類 finding 不同。

### R2-002（minor，非 blocking）

「零寫入」的測試**不是呼叫可觀測的**：`FakeGhRunner` 未記錄 `execute` 呼叫，且 `assign` 在能力檢查前已呼叫 `ensure_fields`，欄位缺失時可能先執行 field-create。

**這正是我在派審詞攻擊點 4 要求確認的事**（「請確認該測試比對的是實際遠端呼叫而非只有回傳值」）——結論是**確實只比對了最終值**。兩條處置擇一：為 `FakeGhRunner` 加呼叫紀錄並斷言拒絕路徑無任何 mutation，或**把保證誠實限縮為「三個狀態值不變」而不再稱「零寫入」**。


## Comment 5250881088 · 2026-08-11T08:36:46Z

## 派審：R3（取代前一則派審詞）

⚠️ 前一則指向 `d81d604`，**已過期**。審核對象仍是 **`ruan6047/ai-workflow#21`**（T3）。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-routing-tier1
分支：claude/WF-CLI-ROUTING-TIER1
被審 SHA：8cfb1b312a611280ace9880cbf98f9014b293c30
基線：origin/main 7451b72ba7679893043950d71bad9642665e25da
iteration：2
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-routing-tier1
git diff d81d604..8cfb1b3          # 本輪
cd cli && uv run pytest -q          # 預期 381 passed
```

分支累計 8 檔；本輪 4 檔 +267／−18，全部在資源宣告內。

### R2-001 的根因與修法

執行者自陳的根因：**把兩種不同的失敗混成一格**——「正規表示式沒匹配」一律當成舊卡，於是排版壞掉的卡面被寫成「卡面無建議層級」。

改為兩段判定：先看該行是否**自稱**新制（含「建議」字樣或任一能力層級值），自稱了就必須完整合格、否則 `ambiguous`；完全沒有痕跡才是 `absent`。誤判方向刻意偏向 `ambiguous`。

**執行者另自查出查核者未列的第三個洞**：`rev_tier` 從未驗證，`查核：X（建議 旗艦型；…）` 一路判 `matched`。已一併修正。

**系統性列舉 16 種破壞方式**，13 種判 `ambiguous`（理由空／只有空白、全形改半形、層級不在語彙、缺分號／缺括號、括號分號改半形、查核段缺失、執行舊式但查核新式），2 種仍判 `matched`（層級值前後空白、行尾空白——空白不帶語意），1 種 `absent`。每種各有兩條斷言：分類正確 ＋ **Log 不得出現「卡面無建議層級」或「偏離卡面建議」**。

### PM 已獨立重現查核者的注入

**我沒有只跑測試**，直接對 `compare_capability_to_card` 注入：

| 注入 | outcome | requires_reason |
|---|---|---|
| 正常（相符） | `matched` | False |
| **R2-001① 執行理由為空** | **`ambiguous`** | True |
| **R2-001② 全形→半形分隔** | **`ambiguous`** | True |
| 執行者自查③ 查核層級不在語彙 | `ambiguous` | True |
| 理由只有空白 | `ambiguous` | True |
| 缺分號 | `ambiguous` | True |
| 完全無新制痕跡 | `absent` | True |

**R2-001 的兩個 repro 皆已不再重現。** 381 passed（在其 worktree 重跑）。

### R2-002：兩條都做了

`_RecordingRunner` 代理記錄每次 `execute`／`run_json`／`graphql`，斷言拒絕路徑零 mutation（涵蓋 `item-edit`／`item-create`／`item-add`／`field-create`／`issue create|edit|comment` 與 GraphQL mutation）。**做在測試檔內而非 `tests/fake_gh.py`**——後者不在資源宣告內（執行者明言 R1 已在這件事上被補正過一次）。

同時做了誠實限縮：測試改名 `..._refused_before_any_mutation`，README 改為「拒絕路徑不做任何 item／body mutation」，**不再用「零寫入」**——因為 `ensure_fields` 在能力檢查前先跑，全新 project 上會先建欄位。

### 本輪請攻擊這四點

1. **16 種列舉是否窮盡。** 這是本輪的核心宣稱。**請自行構造第 17 種**——尤其：兩個能力層級值互為子字串的情形？`建議` 二字出現在理由文字裡（例如理由寫「依建議降級」）？多行 body 中有兩行都像 `- 執行：`？零寬字元或 emoji 變體選擇符混入層級值？
2. **「自稱新制」的判準本身。** 以「含『建議』字樣或任一層級值」來認定自稱——**這個判準是全函數嗎？** 一張舊卡若理由或功能敘述剛好含「建議」二字，會不會被誤拉進 `ambiguous` 而使正常舊卡派工被擋？執行者宣稱以 #21 自己的 body 重跑仍為 `absent`，但那只是一個樣本。
3. **兩種仍判 `matched` 的寬容度是否安全。** 「層級值前後空白」「行尾多餘空白」判 `matched`。請確認這個寬容不會與第 1 點的某種構造疊加成漏判。
4. **`_RecordingRunner` 是否真的接得上。** 執行者做了反向測試（成功派工必須被同一支代理看見 mutation）與突變測試（把 fail-closed 閘門改 `if False:` 應轉紅 2 條，還原後 381 全綠）。**請複驗那個突變**——本 repo 出現過「探針通過但程式不正確」。

### 揭露

- 本輪兩項的 `attribution` 皆為 `executor`。R2-001 的根因是實作把兩種失敗混成一格，**與本 repo 反覆出現的「分類漏一整類輸入」同族**。
- 執行者自查出第三個洞（`rev_tier` 未驗證）——**這是它第一次在被指出之前自己找到同族缺陷**。
- 前兩輪的轉錄皆為 `WF-25` C 方案（純 PM 轉錄、無 receipt、來源不可驗證）。**若你能留 receipt marker 收據（`card_id`、完整 `source_sha`、報告原文 UTF-8 `report_sha256`），PM 會重算比對，可把來源升為可驗證。**

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。留言紀律：**不得讓任何一行以 `<!--` 緊接事件 marker 前綴起始**。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。**R2-001／R2-002 請各自明列 `resolved`／`withdrawn`／仍開啟。**


## Comment 5251872312 · 2026-08-11T10:18:59Z

<!-- wf-review-event:v1 card_id=WF-CLI-ROUTING-TIER1 source_sha=8cfb1b312a611280ace9880cbf98f9014b293c30 attempt_id=WF-CLI-ROUTING-TIER1-e0-8cfb1b312a611280ace9880cbf98f9014b293c30 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CLI-ROUTING-TIER1`　attempt_id：`WF-CLI-ROUTING-TIER1-e0-8cfb1b312a611280ace9880cbf98f9014b293c30`
- 查核者：獨立校讀（需求方於對話中轉貼原文；無 receipt marker，來源不可驗證）　escalation_epoch：0
- source_sha：`8cfb1b312a611280ace9880cbf98f9014b293c30`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-11T18:18:58+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git status --short`
  - HEAD = 8cfb1b312a611280ace9880cbf98f9014b293c30；工作區乾淨。
- `cd cli && uv run pytest -q`
  - 381 passed in 1.80s。
- `PYTHONPATH=cli uv run python <直接注入 compare_capability_to_card>`
  - 舊式「- 執行：待指派（理由：依建議降級）　查核：獨立校讀」→ ambiguous；
  - 完整新制行前置 U+200B 零寬字元 → absent；
  - 層級值內插 U+200B／U+FE0F → ambiguous；
  - 合格新制理由含「依建議降級」→ matched。
- `在 disposable worktree 將 assign_cmd.py 的 fail-closed 條件突變為 if False，執行兩個 _RecordingRunner 測試`
  - 拒絕派工測試轉紅（rc 預期 2、實得 0）；成功派工探針測試仍綠。已刪除 disposable worktree，未改動被審分支。

### findings（1，其中 blocking 1）

- **WF-CLI-ROUTING-TIER1-R3-001**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`routing-format-presence-heuristic-is-not-semantic`
  - evidence：card.py:522-523 以行內任意「建議」或能力層級子字串判定新制。 舊卡「- 執行：待指派（理由：依建議降級） 查核：獨立校讀」被判 ambiguous， 因而要求不應存在的偏離理由；「主力型模型當班」也同樣誤判。 反向地，完整新制行前插 U+200B 後不再符合 startswith("- 執行："), card.py:626-633 直接判 absent，Log 仍會不實寫成「卡面無建議層級」。
  - disposition：不可再以自然語言 token 當格式版本訊號。應建立可機械辨識的版本／結構標記， 並為「舊卡自由文字含建議或能力詞」與「前綴遭零寬／格式字元破壞的新卡」各加回歸測試。 若無法從既有 body 無歧義區分，需明確定義遷移標記，而不是聲稱此判準全函數且語意正確。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5252013513 · 2026-08-11T10:33:46Z

## 派審：R4（取代前一則）

⚠️ 前一則指向 `8cfb1b3`，**已過期**。審核對象 **`ruan6047/ai-workflow#21`**（T3）。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-routing-tier1
分支：claude/WF-CLI-ROUTING-TIER1
被審 SHA：6325ae2ca0972ee10f9440d6f73cd7bc80eff6b4
基線：origin/main 7451b72ba7679893043950d71bad9642665e25da
iteration：3
```

```bash
git diff 8cfb1b3..6325ae2 && cd cli && uv run pytest -q     # 預期 401 passed
```

### 執行者先答了事實問題：**不能區分，且是資訊上不可能**

舊制執行／查核兩欄是**不受限的自由文字**。把 executor 填成 `待指派（建議 主力型；跨模組）`、reviewer 填成 `獨立校讀（建議 高階型；紅線）`，產生的行與新制 `format_routing_line` 的輸出**逐位元組相同**——已寫成測試 `test_old_card_can_be_byte_identical_to_a_new_one` 釘住。

真實語料（#7–#25 全 18 張）證明括號＋自由文字是常態，非邊緣案例：`#16` 執行欄 `待指派（先 grilling）`、`#22` 查核欄 `跨家族查核（契約本體，依 AI_WORKFLOW.md B2 例外須走 PR）`、`#25` 查核欄 `跨家族查核（T4 紅線：不可逆且會毀資料，須人工 sign-off）`。

**前兩輪都是在一個無解的問題上調啟發式。** 故採遷移標記。

### 機制

`open` 在新制卡的路由行**上方**寫入 `<!-- wf-routing:v1 -->`，分類**只查標記是否存在**：

- 標記不在 → `absent`，**完全不看內容**；
- 標記在 → 卡面自我宣告新制，必須拿得出恰一行合格路由行，否則 `ambiguous`。**沒有「退回當舊卡」這條路。**

標記只認 `## Log` 之前的區段，有專測擋「標記被 `amend` 原值引用進 Log 就誤升級」。**零寬字元刻意不加正規化層**——標記在不在是布林事實，不受行內字元破壞影響；再加一層「哪些碼位可剝除」就是重新造出這輪要消滅的猜測層。

### PM 已獨立複驗（八個案例，含位元組相同那個）

| 輸入 | outcome | 要理由 |
|---|---|---|
| 新制（有標記，相符） | `matched` | 否 |
| 舊卡 `（理由：依建議降級）` | `absent` | 是 |
| 舊卡含「主力型模型當班」 | `absent` | 是 |
| **位元組與新制相同的舊卡（無標記）** | **`absent`** | 是 |
| 新制行前置 U+200B | `ambiguous` | 是 |
| 層級值內插 U+200B | `ambiguous` | 是 |
| 合格新制、理由含「依建議降級」 | `matched` | 否 |
| **標記只出現在 Log 內** | **`absent`** | 是 |

401 passed（在其 worktree 重跑）。R3 的五個注入案例全部符合期望。

### 本輪請攻擊這五點

1. **殘留假設是否可接受。** 執行者明說：**舊卡自由文字不會剛好含 `<!-- wf-routing:v1 -->` 這串**。他主張這與「不會剛好含『建議』二字」是不同量級。請判斷——並特別檢查**有沒有任何路徑會把該字串寫進 head 區**（`amend` 的原值引用？`open` 的 `--feature`／`--core-pain` 自由文字？某個渲染把 Log 內容折進 head？）。

2. **遷移成本沒有被討論。** 現有 18 張卡**全部沒有標記**，因此**全部落 `absent`、全部在 `assign` 時要求偏離理由**。執行者沒有評估這個代價，也沒有提供補標記的路徑（`amend` 能不能加？該不該加？）。**請判斷這是否構成一個未處理的遷移缺口。**

3. **`#15` 判 `ambiguous` 是正確還是死結。** 執行者說那張 body 排版**本來就已損壞**（`## Log` 被字面 `\n` 破壞），無法安全定位 head 故 fail-closed。請確認這是正確行為，還是意味著**排版損壞的卡從此無法派工且無自救路徑**。

4. **標記與 doctor 事件 marker 的不碰撞是否成立。** 執行者主張不碰撞（doctor 只掃 Issue **留言**且鎖 `wf-review-event:` 前綴）。**請實查 doctor 的掃描範圍**，不要接受宣稱。

5. **「不加正規化層」是刻意不做還是漏做。** 執行者的論證是標記機制已在結構層解決。請找一個**標記存在、但行內字元破壞導致誤判**的構造。

### 揭露

- 這是同一個分類器第四輪（R2-001 → R3-001 → 本輪）。**前三輪都是在調啟發式**，本輪才去回答「能不能區分」這個事實問題——**該問題本來就該在第一輪問**。
- 真實語料全掃 18 張：17 張 `absent`、1 張 `ambiguous`（#15，body 本已損壞）。
- ruff 抓到執行者在測試裡寫了字面零寬字元，已改為 `​`／`️` 具名常數。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。留言紀律：**不得讓任何一行以 `<!--` 緊接事件 marker 前綴起始**。

**若能留 receipt marker 收據**（`card_id`、完整 `source_sha`、報告原文 UTF-8 `report_sha256`），PM 會重算比對——前三輪皆為純 PM 轉錄、來源不可驗證。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊。**R3-001 請明列 `resolved`／`withdrawn`／仍開啟。**


## Comment 5252262210 · 2026-08-11T10:59:44Z

<!-- wf-review-receipt:v1
card_id: WF-CLI-ROUTING-TIER1
source_sha: 6325ae2ca0972ee10f9440d6f73cd7bc80eff6b4
report_sha256: 167f609a835e18c219f8679a7c9bf8a694c6c165bf287749b21768d0b0676d56
-->

core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git rev-parse HEAD && git status --short"
    observed: "HEAD=6325ae2ca0972ee10f9440d6f73cd7bc80eff6b4；工作區乾淨。"
  - command: "cd cli && uv run pytest -q"
    observed: "401 passed in 1.83s。"
  - command: "cd cli && uv run python (純函式探針)"
    observed: "舊卡 amend 驗收文字嵌入 marker 後，分類由 absent 變 ambiguous；完整 marker 加路由前綴／層級 U+200B 均為 ambiguous。"
  - command: "cd cli && uv run ruff check"
    observed: "未執行：此 uv 環境找不到 ruff executable（Failed to spawn: ruff）。"
findings:
  - finding_id: WF-CLI-ROUTING-TIER1-R4-001
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: routing-marker-unanchored-head-substring
    evidence: "compare_capability_to_card 以 ROUTING_MARKER in head 判定（card.py:642）；amend_acceptance 可把任意文字寫入 Log 前（card.py:400-418）。純函式探針證明舊卡驗收文字含 marker 時由 absent 誤升 ambiguous。"
    disposition: "標記必須以結構位置辨識（獨立行、且緊鄰唯一路由行），並新增舊卡經 amend/free-text 含 marker 仍為 absent 的回歸測試。"
  - finding_id: WF-CLI-ROUTING-TIER1-R4-002
    severity: major
    blocking: true
    finding_class: governance
    attribution: planner
    root_cause_id: routing-tier1-legacy-migration-unspecified
    evidence: "README 明載 #7-#25 全無 marker、皆 absent，assign 因此全要求 deviation reason；amend 沒有更新四個 routing 欄位或受控補 marker 的入口。"
    disposition: "需求方須明定並留痕：既有卡永久以 absent 派工，或提供具四項路由值、原值 Log 與審核界線的遷移路徑；先完成選擇及測試再合併。"

## Comment 5252291954 · 2026-08-11T11:02:32Z

<!-- wf-review-event:v1 card_id=WF-CLI-ROUTING-TIER1 source_sha=6325ae2ca0972ee10f9440d6f73cd7bc80eff6b4 attempt_id=WF-CLI-ROUTING-TIER1-e0-6325ae2ca0972ee10f9440d6f73cd7bc80eff6b4 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CLI-ROUTING-TIER1`　attempt_id：`WF-CLI-ROUTING-TIER1-e0-6325ae2ca0972ee10f9440d6f73cd7bc80eff6b4`
- 查核者：獨立校讀（留有 receipt marker；PM 重算 report_sha256 相符——取材＝marker 之後的報告原文 strip()）　escalation_epoch：0
- source_sha：`6325ae2ca0972ee10f9440d6f73cd7bc80eff6b4`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-11T19:02:32+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git status --short`
  - HEAD=6325ae2ca0972ee10f9440d6f73cd7bc80eff6b4；工作區乾淨。
- `cd cli && uv run pytest -q`
  - 401 passed in 1.83s。
- `cd cli && uv run python (純函式探針)`
  - 舊卡 amend 驗收文字嵌入 marker 後，分類由 absent 變 ambiguous；完整 marker 加路由前綴／層級 U+200B 均為 ambiguous。
- `cd cli && uv run ruff check`
  - 未執行：此 uv 環境找不到 ruff executable（Failed to spawn: ruff）。

### findings（2，其中 blocking 2）

- **WF-CLI-ROUTING-TIER1-R4-001**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`routing-marker-unanchored-head-substring`
  - evidence：compare_capability_to_card 以 ROUTING_MARKER in head 判定（card.py:642）；amend_acceptance 可把任意文字寫入 Log 前（card.py:400-418）。純函式探針證明舊卡驗收文字含 marker 時由 absent 誤升 ambiguous。
  - disposition：標記必須以結構位置辨識（獨立行、且緊鄰唯一路由行），並新增舊卡經 amend/free-text 含 marker 仍為 absent 的回歸測試。
- **WF-CLI-ROUTING-TIER1-R4-002**　severity=major　blocking=true　class=governance　attribution=planner　root_cause_id=`routing-tier1-legacy-migration-unspecified`
  - evidence：README 明載 #7-#25 全無 marker、皆 absent，assign 因此全要求 deviation reason；amend 沒有更新四個 routing 欄位或受控補 marker 的入口。
  - disposition：需求方須明定並留痕：既有卡永久以 absent 派工，或提供具四項路由值、原值 Log 與審核界線的遷移路徑；先完成選擇及測試再合併。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5252312819 · 2026-08-11T11:04:34Z

## PM 補記：收據已驗證 ＋ R4-002 的需求方裁定

### 一、本輪是本卡首次留下可驗證收據

`report_sha256 = 167f609a…0676d56`，**PM 重算相符**。

**但取材規則與前三輪不同**：本輪 receipt marker 在留言**開頭**、報告在其後，雜湊取材為 **marker 之後的報告原文 `.strip()`**；前幾輪（#16 R1–R11）則是 marker 在**結尾**、取材為 **body 去 marker 後 `.rstrip()`**。

PM 試了五種取材才命中。`handoff-contract.md` §3.1.2 只寫「查核報告原文 UTF-8 `report_sha256`」，**未釘死版面與取材邊界**——兩種寫法都合契約，但消費端必須逐一嘗試才能驗。

> **這是 marker 契約的一個缺口**（#15 已 merge 的射程），非本卡問題。**已記於此供後續開卡取用**：收據應明定「report 相對 marker 的位置」與「取材的空白處理」，否則 `report_sha256` 的可驗證性依賴猜測。

### 二、R4-001（executor）：正是派審詞攻擊點 1 的第二個構造

我在派審詞問「有沒有任何路徑會把 marker 字串寫進 head 區（`amend` 的原值引用？`open` 的自由文字？）」。查核者實測答案是**有**：`amend_acceptance` 可把任意文字寫入 Log 之前，舊卡驗收文字含 marker 即由 `absent` 誤升 `ambiguous`。

**執行者的殘留假設「舊卡自由文字不會剛好含這串 HTML 註解」因此不成立**——不需要人手打進姓名欄，`amend` 就寫得進去。

處置：**標記必須以結構位置辨識**（獨立行、且緊鄰唯一路由行），並加回歸測試。

### 三、R4-002（**planner**）：需求方裁定

查核者要求明定並留痕。**需求方 2026-08-11 裁定：既有卡永久以 `absent` 派工，不補 marker、不新增遷移入口。**

理由：

1. **R4-001 剛證明「能寫入 head 的入口就是漏洞來源」**；新增一個受控補 marker 的入口，就是新增第二個必須自證不會變成 R4-001 的入口。
2. 補上的四個路由值是**事後補填的建議**，未必反映當初規劃期的判斷——那正是 `MODEL_ROUTING.md` 第 14 行「路由決定於規劃期」要防的。
3. 代價是 18 張卡到結案前每次派工多打一個 `--deviation-reason`，且那些理由實質上是雜訊。**這個代價需求方已知悉並接受。**

**卡面須明載此裁定**（不得只留在 Issue 留言），且 README 不得暗示未來會補遷移入口。

### 四、查核者澄清的三點（本輪無 finding）

- **#15 不是派工死結**：`assign` 可帶理由繼續；`amend --escalate` 另提供人工 `gh issue edit` 修復與驗證 runbook。
- **`doctor` 與 routing marker 不碰撞**：doctor 只對 Issue 留言與 PR review body 掃 `wf-review-event:`，Issue body 只用作 Log 索引，前綴不同。**查核者實查了掃描範圍，非接受宣稱。**
- **不做正規化並非漏做**：完整標記存在時，路由前綴或能力值插入 U+200B 都正確落 `ambiguous`；理由文字中的零寬字元仍 `matched`（理由本來就是自由文字）；零寬字元插進標記本身則不再逐位元組相符，依設計落 `absent`。

**`R3-001` 判 `resolved`**——以自然語言內容猜版本的分類器已消除。

### 五、查核者環境的一項限制

`cd cli && uv run ruff check` **未執行**（該 uv 環境找不到 ruff executable）。執行者宣稱「ruff findings 與 main 逐項比對為同一集合」**本輪未被獨立複驗**。


## Comment 5253234060 · 2026-08-11T12:35:50Z

## PM 註記：本輪查核的 SHA 已過期，且 finding_id 與前一輪碰撞

### 一、被審 SHA 是 `6325ae2`，但分支已前進到 `19f5a0f`

**這是 PM 的疏失**：執行者於 `19f5a0f` 交付後，我沒有補發指向新 SHA 的派審詞。查核者發現工作樹已前進，**改以 `git archive 6325ae2` 建唯讀暫存快照驗證**——處理方式正確，責任在我。

### 二、finding_id 與前一則 R4 裁決碰撞

同一個 `source_sha`（`6325ae2`）上已有另一份 R4 報告（含 receipt，`report_sha256` 已驗）。兩份的編號重疊但內容不同：

| id | 前一份 | 本份 |
|---|---|---|
| `R4-001` | marker 以 `in head` 子字串判定，`amend_acceptance` 可寫入 head | **`amend_spec_baseline`** 可插入完整 marker |
| `R4-002` | 遺留卡遷移未明定 | 同左 |
| `R4-003` | — | **多行遮蔽：兩條路由行其一前置 U+200B 被略過，`ambiguous` 降為 `matched`** |

依 `review-escalation.md` §3，同 SHA 多份報告**合併處理、最多計一次**。本則以內容區分，不以編號區分。

### 三、PM 已實測：三項在 `19f5a0f` 上的存活狀態

```
== R4-001：amend_spec_baseline 注入 marker ==
   已被擋: AmendError「spec 基線是單行欄位，不得含換行（會在卡面標頭區插入額外行）」

== R4-003：兩條路由行，其一前置 U+200B ==
   結果: matched  requires_reason=False   ← 應為 ambiguous

== 對照：兩條都正常 ==
   結果: ambiguous
```

| finding | 在 `19f5a0f` 的狀態 |
|---|---|
| `R4-001`（`amend_spec_baseline`） | **已修**。執行者於 `19f5a0f` 自查發現同一路徑並擋掉換行——**與查核者獨立發現的是同一個洞** |
| `R4-002`（遷移決策） | **已裁定並落地**：需求方裁定「既有卡永久以 `absent` 派工、不補標記、不新增遷移入口」，已寫入卡面驗收第 8 條（`op 66180d6c`）與 README |
| **`R4-003`（多行遮蔽）** | **仍重現，且是新洞** |

### 四、`R4-003` 為什麼重要

它與前幾輪的形態不同：前面幾次是**破損被誤判為 `absent`**（漏檢），這次是**破損把 `ambiguous` 降為 `matched`**——

> 兩條有效路由行原應判 `ambiguous`（宣告不唯一）；把其中一條前置 U+200B 後，該行不再符合 `startswith("- 執行：")` 而被掃描**略過**，剩下一條有效行 → **`matched`，且免除偏離理由**。

**破損不該讓判定變得更寬鬆。** 這是本卡第五輪同一個分類器，且是**唯一一次錯在放行方向**。

### 五、其餘攻擊點查核者的結論（本輪無 finding）

- `#15` 判 `ambiguous` 是**正確的 fail-closed**；仍可帶理由 `assign`，且有人工 break-glass 修復程序，**並非無法派工**。
- `doctor` 的掃描確實只取 Issue comments／PR reviews，Issue body 僅作 Log 對帳，且只鎖 `wf-review-event:`，**不碰撞**。

本輪未留 receipt marker（受唯讀紅線限制）。


## Comment 5253366028 · 2026-08-11T12:47:06Z

## 派審：R5（取代所有先前派審詞）

⚠️ 先前兩則指向 `6325ae2`／`19f5a0f`，**皆已過期**。審核對象 **`ruan6047/ai-workflow#21`**（T3）。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-routing-tier1
分支：claude/WF-CLI-ROUTING-TIER1
被審 SHA：c8ffc3e7ed0b4122474485cf6ffb5499c1a12acf
基線：origin/main 7451b72ba7679893043950d71bad9642665e25da
iteration：5
```

```bash
git diff 19f5a0f..c8ffc3e && cd cli && uv run pytest -q     # 預期 426 passed
```

### 前輪三項的處置

| finding | 狀態 |
|---|---|
| `R4-001`（`amend --spec-baseline` 注入 marker） | **已修於 `19f5a0f`**——執行者自查發現，比查核者早；PM 實測確認被 `AmendError` 擋下 |
| `R4-002`（遺留卡遷移） | **已裁定並落地**：需求方裁定既有卡永久 `absent`、不補標記、不新增遷移入口（卡面驗收第 8 條、`op 66180d6c`） |
| **`R4-003`（多行遮蔽）** | **本輪修正對象** |

### R4-003 的修法，以及執行者對自己前一輪論證的更正

前一輪執行者刻意不加正規化，論證是「標記機制已在結構層解決」。**他這輪推翻了自己的邊界劃法**：

> 那個論證對標記辨識成立，對多行候選掃描不成立。**但真正的判準不是「單行 vs 多行」，是失敗會往哪邊倒**：

| 步驟 | 比對失敗的後果 | 方向 |
|---|---|---|
| 標記辨識 | 少一個宣告 → `absent` → **要求理由** | 保守 |
| 候選路由行收集 | 少一條候選 → 可能剩 1 條 → `matched` → **免除理由** | **危險** |

所以正規化**只加在偵測側、且只用來擴大候選集**：

- **偵測（誰算候選）— 寬鬆**：NFKC → 去除 `Cc`／`Cf`／`Mn`／`Me` → 去空白 → 比前綴。
- **受理（候選能否當基線）— 嚴格**：用**原始行**，不套任何偵測正規化。

**兩側都不可能產出偽 `matched`**：多收只會更嚴，受理端從不放寬。方向性紅線已寫進 `card.py` 註解，不只留在測試裡。

### PM 已獨立複驗（七種遮蔽）

| 輸入 | outcome |
|---|---|
| 兩條，其一前置 ZWSP `U+200B` | `ambiguous` |
| 兩條，其一前置 BOM `U+FEFF` | `ambiguous` |
| 兩條，其一前置 VS16 `U+FE0F` | `ambiguous` |
| 兩條，其一全形冒號改半形 | `ambiguous` |
| 兩條，其一前綴多空白 | `ambiguous` |
| 兩條都正常 | `ambiguous` |
| **單條（對照）** | **`matched`** |

**對照組仍 `matched`**，證明不是把全部打成 `ambiguous` 蒙混。426 passed。

### 本輪請攻擊這五點

1. **性質斷言是否真的是性質斷言。** 執行者稱：三個基準卡面 × 在 `## Log` 之前**每一行每個位置**插入**六種**不可見字元，斷言「原本要理由的卡面，破損後仍要理由」，另有 `checked > 100` 的下限防空測試。**請確認那個下限真的會在掃描範圍失效時失敗**，以及六種字元的選取是否有代表性。

2. **偵測側的寬鬆會不會反噬。** 「多收只會更嚴」這個推論**在 `matched` 判定上成立**——但**在 `absent` 判定上呢**？一張真正的舊卡若因為 NFKC 折疊而讓某行被誤收為候選，會不會從 `absent` 變 `ambiguous`（＝多要一個理由，仍是保守側），還是有路徑能變成別的？

3. **`Cf` 類別的副作用。** 去除 `Cf` 會一併去掉 `U+00AD`（軟連字號）與**雙向控制字元**（`U+202A`–`U+202E`）。**若卡面本來就含合法的雙向文字**（例如混排阿拉伯文或希伯來文的理由），偵測側會如何？這是「正規化本身造出新分類」的候選。

4. **突變測試的覆蓋。** 執行者稱把候選判定退回 `startswith` 後 7 項轉紅。**請複驗**，並判斷 7 項是否足以綁住「方向性」這條規則本身，而不只是綁住當前的實作。

5. **誠實邊界的措辭。** 執行者寫：「偵測正規化不宣稱窮盡所有 Unicode 擾動。保證的是**方向**而非完備；漏網擾動仍受『宣告必須緊鄰唯一候選』這條純結構規則保護。」**請驗證那條結構規則真的能接住漏網情形**——若接不住，這句話就是一個未經驗證的安全宣稱。

### 揭露

- **這是同一個分類器第五輪。** 五次病灶：用內容猜版本 → 用存在性猜版本 → 用嚴格前綴掃描。**前四次都錯在保守側（漏檢），只有 R4-003 錯在放行側。**
- **前一輪的查核 SHA 過期是 PM 的疏失**（執行者交付 `19f5a0f` 後未補派審詞）。查核者以 `git archive` 建唯讀快照處理，正確。**本則已對齊最新 SHA。**
- 同一 SHA 上曾有兩份 R4 報告、`R4-001` 編號碰撞但內容不同——依 `review-escalation.md` §3 合併處理。**這是 [#22](https://github.com/ruan6047/ai-workflow/issues/22) 正在修的 stable id 問題的活實例。**
- ruff 逐項輸出已附於 handoff 證據，兩側 `diff` IDENTICAL、9 項全為既有。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。留言紀律：**不得讓任何一行以 `<!--` 緊接事件 marker 前綴起始**。

> **留 receipt marker 不違反上述紅線**（留言不改 Project 狀態）。若留收據，**請一併載明取材規則**（marker 在報告前或後、空白如何處理）——`handoff-contract.md` §3.1.2 未釘死版面。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊。**R4-001／002／003 請各自明列 `resolved`／`withdrawn`／仍開啟。**


## Comment 5253717667 · 2026-08-11T13:20:13Z

<!-- wf-review-event:v1 card_id=WF-CLI-ROUTING-TIER1 source_sha=c8ffc3e7ed0b4122474485cf6ffb5499c1a12acf attempt_id=WF-CLI-ROUTING-TIER1-e0-c8ffc3e7ed0b4122474485cf6ffb5499c1a12acf -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CLI-ROUTING-TIER1`　attempt_id：`WF-CLI-ROUTING-TIER1-e0-c8ffc3e7ed0b4122474485cf6ffb5499c1a12acf`
- 查核者：跨家族查核（需求方於對話中轉貼原文；無 receipt marker，來源不可驗證）　escalation_epoch：0
- source_sha：`c8ffc3e7ed0b4122474485cf6ffb5499c1a12acf`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-11T21:20:12+08:00

### self_run（查核者實跑）

- `cd cli && uv run pytest -q`
  - 426 passed in 2.21s。
- `ruff check`
  - ruff 未安裝，無法執行。
- `在兩條合法路由行中，於第二條前插入 U+02B0（Lm）與 U+0378（Cn）後重跑偵測`
  - 系統仍回傳 matched 且 requires_reason=False；
  - 對照組以 U+200B 插入則正確得到 ambiguous。
- `（未執行任何有副作用的 wfcli 命令）`
  - 全程唯讀，無任何寫入。

### findings（3，其中 blocking 1）

- **WF-CLI-ROUTING-TIER1-R5-001**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`routing-detection-normalization-incomplete`
  - evidence：cli/src/wf_cli/card.py:586-612 的 _detection_key 只去除 Cc／Cf／Mn／Me 與空白字元。 在兩條合法路由行中，第二條前加入 U+02B0（Lm）與 U+0378（Cn），系統仍回傳 matched 且 requires_reason=False。原因是第二條不再被收集為 candidate， 第一條剛好仍緊鄰 marker，導致「唯一候選」錯誤放行。 U+200B 的對照測試則正確得到 ambiguous，證明問題在未被正規化涵蓋的字元類別。
  - disposition：候選偵測須改成無法因未知 Unicode 前綴而縮減候選集合；至少加入上述兩組回歸測試， 並移除「緊鄰唯一候選可保護漏網擾動」的不成立宣稱。
- **WF-CLI-ROUTING-TIER1-R5-002**　severity=minor　blocking=false　class=implementation　attribution=executor　root_cause_id=`mutation-evidence-count-overstated`
  - evidence：mutation 證據聲稱 startswith 退化會讓 7 個案例轉紅；獨立實測為 6 個。
  - disposition：修正文件與註解中的數字，或補上使第七個案例成立的測試。
- **WF-CLI-ROUTING-TIER1-R5-003**　severity=minor　blocking=false　class=implementation　attribution=executor　root_cause_id=`property-test-volume-mistaken-for-coverage`
  - evidence：性質測試以 checked > 100 證明覆蓋量，未直接證明每一行與每一位置都被掃描。
  - disposition：改以窮舉或不變量斷言證明位置覆蓋，而非以抽樣數量代替覆蓋宣稱。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5253765631 · 2026-08-11T13:24:35Z

## PM 註記：本輪裁決的轉錄邊界，以及本卡查核通道已被 marker 隔離

### 一、轉錄邊界

本輪裁決由**需求方於對話中轉貼查核報告原文**，查核者無 `wfcli` 寫入通道，故由 PM 逐字轉錄進唯一寫入通道。三件已知限制：

1. **無 receipt marker，來源不可驗證。** 報告未附 `report_sha256` 收據。可驗證的只有：轉錄後的 `evidence`／`disposition` 是報告散文的逐句搬移，未增刪判斷。
2. **schema 欄位由 PM 指派，非查核者填寫。** 原報告是散文，未提供 `severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id`。這四欄由 PM 依報告文字判定後填入。
3. **`blocking` 採報告自己的用語**：標為「Blocking」者記 true，標為「非阻擋」者記 false。

被審 SHA 已由 PM 獨立核對：worktree HEAD `c8ffc3e` 與報告所列相符，非陳舊派工。

### 二、`root_cause_id` 的指派牽動門檻，請覆核

R5-001 我記為 `routing-detection-normalization-incomplete`。**這與 R4-001 的 `routing-marker-unanchored-head-substring` 可能屬同一根因家族**——兩者都是「偵測側的字串前處理不足，未涵蓋的輸入形態可規避判定」。若判為同族，則同根因已跨 R4／R5 兩個唯一可計數 attempt；再一次就滿足 `review-escalation.md` §4 第一條件。

我刻意不在此把它併進 R4-001 的家族，理由是：**併與不併都會改變門檻觸發時點，而這個判斷本該由查核者做，不該由有動機延後門檻的一方做。** 請查核者或需求方裁定歸屬。escalation checkpoint 會在派下一輪之前另行建立。

### 三、`doctor --review-channel` 對本卡回傳 `marker_quarantined`

實跑結果（`--owner ruan6047 --project 4 --issue-number 21 --card-id WF-CLI-ROUTING-TIER1 --source-sha c8ffc3e…`）：本卡**不是** `recorded`，而是 `marker_quarantined`，依 `handoff-contract.md` §3.1.4 停止自動裁決判定。

三則停機來源全部是 **PM 自己寫的派審／裁決留言**，它們在散文中提到了事件 marker 的前綴字串（`wf-review-event` 加半形冒號，此處刻意拆開書寫以免本則成為第四個來源）：

- `#issuecomment-5252013513`（R4 派審詞，第 57 行）
- `#issuecomment-5252312819`（R4 裁決轉錄，第 36 行）
- `#issuecomment-5253234060`（R4-003 裁決轉錄，第 49 行）

三則都是在討論「routing marker 與事件 marker 是否碰撞」時引用該字串——**諷刺之處在於，討論碰撞的留言本身造成了碰撞。**

**這暴露一個真的錯誤，是我的：** 我在多輪派審詞裡寫的留言紀律是「不得讓任何一行以 `<!--` ＋事件 marker 前綴起始；**行中提及安全**」。後半句對照 `doctor.py:164` 的 `_EVENT_PREFIX` 是錯的——實作是**全文子字串比對**，不分宣告行或行內引用，命中即隔離整卡。#16 §3.2.3 設計的宣告行／行內引用三分類**尚未落地到 doctor**，我卻按設計稿的語意在派工。

**未自行解除。** `doctor` 訊息本身說明解除須依 `review-escalation.md` §5 的 `review-marker-clearance`，而該事件在留言平面的表示法尚未定義（`docs/CONSUMER_CONFORMANCE.md`）——這正是 #13 停止時記錄的同一個未落地缺口。我也不編輯那三則歷史留言把字串打斷：那會讓這次誤判從紀錄上消失，而它是 #16 §3.2.3 目前最有力的真實語料。

**三面一致改以人工核對，結果相符：** 裁決留言首行為合格 marker；Issue body Log 索引已寫入 `2026-08-11T21:20:12+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）`；Project 交付狀態為 `↩退回`。故本卡狀態面無不一致，`marker_quarantined` 是**偵測面停機**，不是狀態面損壞。


## Comment 5253853989 · 2026-08-11T13:32:18Z

## escalation-checkpoint（第六個可計數 attempt 前）

### 需求方裁定：R5-001 與 R4-001 同根因家族

需求方於 2026-08-11 裁定：**「同族」**。R5-001 的 `routing-detection-normalization-incomplete` 與 R4-001 的 `routing-marker-unanchored-head-substring` 併為同一根因家族，**以先出現者 `routing-marker-unanchored-head-substring` 為家族代表**。

家族的共同形態：**偵測側對非預期輸入形態的處理不完整，且失敗方向偏向不安全側**——R4-001 是未錨定的子字串比對可讓舊卡誤升，R5-001 是未涵蓋的 Unicode 類別可讓候選靜默消失、兩條路由行降成一條而誤放行。

**本裁定無法寫回既有事件。** 兩則 review event 已 append-only 落地，各自帶著原本的 `root_cause_id`。adapter 依事件流機械推導 checkpoint 時**看不到這次合併**，只會看到兩個不同的家族各出現一次。這是契約的一個缺口：**目前沒有任何事件型別可以表示「事後裁定兩個根因家族實為同一個」**。本則留言是人可讀的覆蓋，不是機器可讀的更正。此缺口併入既有的契約修訂待辦，不另開卡。

### 兩條件的成立情形

**第一條件（同根因跨三個唯一可計數 attempt）：依裁定為 2／3，尚未成立。**

家族落點為 R4（`6325ae2`）與 R5（`c8ffc3e`），兩個唯一可計數 attempt。

**但這個 2 是保守數。** 更寬的讀法會把 R3-001（`routing-format-presence-heuristic-is-not-semantic`，零寬字元可讓新卡誤判 absent）與 R2-001（`malformed-routing-card-misclassified`，破損卡面誤判 matched／absent）也納入同一家族——它們的形態同樣是「偵測判定被輸入層擾動繞過」。那樣是 **4／3，早已成立**。

我不自行擴大合併：需求方的裁定明確只涵蓋 R4-001 與 R5-001，而**我是有動機把門檻往後推的那一方**，擴或不擴都不該由我決定。若需求方認為 R2-001／R3-001 亦屬同族，請直接裁示，本卡的 escalation 帳會回溯調整。

**第二條件（前一 attempt 的 accepted blocking finding 未在下一 attempt 明列 `resolved`／`withdrawn`）：成立。**

R4 的 accepted blocking 為 R4-001 與 R4-002。R5 的查核報告是散文形式，**完全未提及前輪任何 finding**，故兩者皆未被明列 `resolved` 或 `withdrawn`。轉錄時 PM 亦未代為補填——代填等於代查核者宣告閉環，那正是本專案反覆被打穿的形態。

**因此 `checkpoint_decision` 只能是 `escalate`，不得信任手填的 `continue`（§4 末段）。**

需要說明的是：這一次觸發**部分源於派審流程本身**。R5 的派審詞未要求查核者逐項回報前輪 finding 的閉環狀態（前幾輪的派審詞有此要求），報告因此沒有那一節。這不使條件不成立——條件的判準是事件流上有沒有那個宣告，不是為什麼沒有——但下一輪派審詞必須把該要求寫回去。

### 裁定

```yaml
checkpoint_decision: escalate
escalation_resolution: continue
checkpoint_rationale: |
  第二條件成立（R4-001／R4-002 未在 R5 報告中明列 resolved 或 withdrawn），
  故 checkpoint_decision 只能是 escalate。需求方裁定 continue，維持同執行者角色
  （Claude Opus 5@Claude Code 子 agent），不換人、不切卡。
  裁定依據為需求方 2026-08-11 的原話：「同族，先建 checkpoint 再派agent」。
  PM 對該句的讀法是「維持執行者、繼續下一輪修正」；若本意為更換執行者，
  請於本則之下回覆更正，PM 不代為推定。
decided_by: ruan6047（需求方）
counts_toward_escalation: true
attempts_so_far: 5
```

### 下一輪派審詞的強制項

1. **必須逐項回報前輪 finding 的閉環狀態**（`resolved`／`withdrawn`／仍開啟），缺此節即 `review-invalid`。
2. 必須要求查核者填齊 `severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id`，不再由 PM 事後指派。
3. 留言紀律更正：**不得在留言中出現事件 marker 的字面前綴，連散文引用與 code fence 示範都不行**。先前派審詞寫的「行中提及安全」是錯的，已使本卡三則留言遭隔離（見 `#issuecomment-5253765631`）。需要指涉時拆開書寫。


## Comment 5255484548 · 2026-08-11T15:49:53Z

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


## Comment 5255923976 · 2026-08-11T16:29:37Z

## 派審：#21 `WF-CLI-ROUTING-TIER1` R6

⚠️ 審核對象是 **`ruan6047/ai-workflow#21`**，**不是 `cpbl-analytics#21`**。工作目標 repo 是 `ai-workflow`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-routing-tier1
分支：claude/WF-CLI-ROUTING-TIER1
被審 SHA：e928050d52cb585906d9a6928c4a2f7ad2c961ea
基線：origin/main 0d4d282
iteration：5
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-routing-tier1
git rev-parse HEAD && git status --short && git diff --check
git diff c8ffc3e..e928050                      # 本輪變更（3 檔）
cd cli && uv run pytest -q
```

**請先讀本 Issue 的 escalation checkpoint 留言（`#issuecomment-5253853989`）。** 這是本卡第六輪，需求方已裁定 R5-001 與 R4-001 **同根因家族**。請不要因為「已經第六輪」而放寬標準。

### 一、複驗 R5-001（Unicode 擾動可繞過雙路由行偵測）

上一輪的洞：`_detection_key` 只去除 `Cc`／`Cf`／`Mn`／`Me` 與空白，於是 `U+02B0`(Lm)／`U+0378`(Cn) 前置第二條路由行時該行靜默消失，兩條降成一條 → `matched` 且免除理由。

修法**不是補字元類別**，是把候選資格倒過來定義：

> **候選資格 ＝「已知非路由行」的補集。** 標頭區的一行只有被正面辨識為 `render_issue_body` 會產出的某一種已知行時才不算候選；**其餘一律是候選，包含任何看不懂的行。**「已知」的判準是**原始行**對固定字面前綴的 `startswith`，所以插入任何字元只能破壞前綴比對（→ 掉進候選 → 更嚴），不可能憑空造出前綴。`_detection_key` 與字元類別清單已整段刪除。

請攻擊這個「單調性」宣稱本身：**是否真的不存在任何輸入，能讓一條實際存在的路由行從候選集合中消失？** 執行者宣稱的機械證明只涵蓋「加字元或加行不會使候選集縮小」（全碼位掃描 1,112,062 個碼位＋逐 category＋逐位置等式）。**刪減、重排、跨行拼接不在該證明內。**

執行者自承**借殼行**（把路由行接在已知前綴後面，如 `- DB：… - 執行：…`）這個面沒有關掉——他加了一條非承載性收緊，但自承可被寫法變形繞過。PM 抽測四種變體皆 `ambiguous`，未打穿，**但那不是證明**。請認真打這一面。

### 二、複驗兩項非阻擋

- **R5-002**：上輪宣稱該突變讓 7 個案例轉紅，你上輪實測 6。本輪執行者重跑得 7 個 node id（6 參數化＋1 性質測試），主張差異是計數口徑。請判斷這個解釋是否成立，還是在替一個錯誤的數字找說法。
- **R5-003**：性質測試改為 `(行號, 位置, 字元)` 三元組集合**等於**獨立算出的全集。請驗證那個「獨立算出的全集」是否真的獨立——如果它與被測程式共用同一個生成邏輯，等式就恆真。

### 三、跨卡矛盾（PM 指定查驗項，非 finding）

本卡宣告持有 `cli/tests/test_review.py`，而 [#9](https://github.com/ruan6047/ai-workflow/issues/9)（`WF-22-CLI4`）的宣告已於 2026-08-12 收窄後仍包含該檔——**這是真實的寫入集重疊，須以先後派工解決**，已在 #9 的 amend 理由中明示、不以縮小宣告規避。此處僅告知，不需你處置。

### 四、本卡的查核通道目前被隔離，請知悉

`doctor --review-channel` 對本卡回傳 `marker_quarantined`，來源是**三則 PM 自己寫的留言**在散文中引用了事件 marker 的字面前綴（`#issuecomment-5253765631` 有完整說明）。這代表：**你的裁決回來後，三面一致只能人工核對。** 已開卡 [#30](https://github.com/ruan6047/ai-workflow/issues/30) 處理判準收窄與 clearance 表示法，但它被資源佔用擋著、尚未開工。

**這不影響你的查核，但請你的留言務必遵守下方紀律，否則會再多一個隔離來源。**

### 五、執行者主動揭露

- **執行者是 Claude Opus 5@Claude Code 的子 agent，PM 亦為 Claude Opus 5。** 你必須是**不同模型家族**。
- 同一形態（偵測側對非預期輸入的處理不完整、失敗偏向不安全側）**已連續五輪出現**（R2-001／R3-001／R4-001／R5-001）。需求方已裁定 R4-001 與 R5-001 同族。**若你認為 R2-001／R3-001 亦屬同族，請直接裁示**——那會使第一條件成立，本卡的 escalation 帳會回溯調整。PM 刻意不自行擴大合併（有動機把門檻往後推的是 PM）。
- 執行者自承三個未關的面（借殼行、同行內語意竄改、收緊判準的保守誤判），已寫進 README 而非只留在報告裡。
- 突變三組：候選收集退回 `startswith`→17 紅、退回 R5-001 版→11 紅、性質產生器少掃末位→4 紅。
- `ruff` 與 main 逐項 diff 為 IDENTICAL（9 項全為既有）。

### 環境紅線

唯讀查核；**不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行任何有副作用的 `wfcli` 命令**（`--validate-only` 與 `doctor` 唯讀可以）。

**留言紀律（重要，本輪起強制）**：你的留言中**不得出現事件 marker 的字面前綴**（即 `wf-review-event` 後面直接接半形冒號），連散文引用與 code fence 示範都不行。需要指涉時拆開書寫。發文前 `grep` 一次。

### 輸出

依 `templates/review-prompt.md` §5 的結構化區塊，`core_pain_resolved` 與 `self_run` 必填。**本輪起額外強制兩項**：

1. **逐項回報前輪 finding 的閉環狀態**——R5-001、R5-002、R5-003 各自明列 `resolved`／`withdrawn`／仍開啟，缺此節即 `review-invalid`。**上一輪漏了這一節，直接造成本卡的 escalation checkpoint 被觸發。**
2. **`severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id` 五欄請你自己填**，不要留給 PM 事後指派——`root_cause_id` 直接影響門檻計數。


## Comment 5256205014 · 2026-08-11T16:54:34Z

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


## Comment 5256346879 · 2026-08-11T17:07:44Z

<!-- wf-review-receipt:v1
card_id: WF-CLI-ROUTING-TIER1
source_sha: e928050d52cb585906d9a6928c4a2f7ad2c961ea
report_sha256: d9970c7bebb2cc944a1772024865ff798d01faa28d33b488a4e4c80d226a8918
-->

取材規則：雜湊的輸入為本留言中緊接下一個空白行後、首字元為 `core_pain_resolved: yes` 的報告全文，至最後一個範圍外發現項目句末的全形句號為止；以 UTF-8 編碼、LF 換行，先對該段 Unicode 文字套用 `strip()`（移除首尾空白與最終 LF），不含本收據 marker、取材規則段與分隔空白行。

core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "git rev-parse HEAD && git status --short && git diff --check"
    observed: "HEAD=e928050d52cb585906d9a6928c4a2f7ad2c961ea；工作樹乾淨；diff --check 無輸出。"
  - command: "git diff c8ffc3e7ed0b4122474485cf6ffb5499c1a12acf..e928050d52cb585906d9a6928c4a2f7ad2c961ea"
    observed: "R6 僅修改 card.py、test_card.py、README.md；候選行改為已知非路由標頭行的補集。"
  - command: "cd cli && uv run pytest -q"
    observed: "437 passed in 4.89s。"
  - command: "cd cli && uv run pytest -q tests/test_card.py -k 'second_routing_line_survives or no_single_codepoint_prefix or candidate_set_is_monotone or generated_header_line or routing_shape_hidden or duplicated_known or corruption_never or insertion_never or detection_is_permissive'"
    observed: "14 passed, 122 deselected in 2.01s；涵蓋 U+02B0、U+0378、全碼位前綴掃描、插行單調性、借殼行與位置覆蓋。"
  - command: "git merge-base 0d4d282 e928050d52cb585906d9a6928c4a2f7ad2c961ea; git merge-tree 7451b72ba7679893043950d71bad9642665e25da 0d4d282 e928050d52cb585906d9a6928c4a2f7ad2c961ea"
    observed: "實際共同祖先為 7451b72；0d4d282 是後續 main。無衝突標記，main 後新增的 smoke 檔不會因本分支合併被刪除。"
  - command: "cd cli && uv run ruff check"
    observed: "無法執行：目前 uv 環境未安裝 ruff（Failed to spawn: ruff）；非程式碼失敗。"
findings: []

核心痛點已消失：`open` 的四個能力層級欄位、卡面渲染與 `assign` 的實際能力／偏離理由留痕皆已落在唯一寫入通道；R6 的未知 Unicode [Unicode] 前綴不再能讓第二條路由行靜默離開候選集合並放寬成 `matched`。

前輪 finding 閉環：

| Finding | 狀態 | 證據 |
|---|---|---|
| R1-001 | resolved | `assign` 已記錄實際能力與偏離理由。 |
| R2-001 → R3-001 | resolved | 改用結構化版本標記，後續再由 R4 修正標記結構位置。 |
| R4-001 | resolved | 標記必須獨立成行、位於標頭區、且緊鄰唯一路由行。 |
| R4-002 | resolved | 卡面與 README 已明定既有卡永久 `absent`，不設遷移入口。 |
| R4-003 | resolved | R5 版寬鬆字元正規化已移除，改為補集候選收集。 |
| R5-001 | resolved | U+02B0／U+0378 皆為 `ambiguous`；全碼位前綴掃描通過。 |
| R5-002 | resolved | 7 的口徑為 6 個參數化案例加 1 個性質測試；文件已改明組成。 |
| R5-003 | resolved | 實際造訪的 `(行號, 位置, 字元)` 集合與獨立建立的全集相等。 |

範圍外發現：

- #9 與本卡的 `cli/tests/test_review.py` 資源重疊已在跨卡對帳與 #9 卡面明示；屬派工先後順序的協調 [coordination]，本輪不新增 finding。
- README 已誠實列出借殼行、同行語意竄改與保守誤判的殘留面。本輪實測含零寬字元的借殼變體仍為 `matched`，但它不是可被解析成第二條有效路由行的結構，亦不會改寫標記緊鄰、有效路由行所提供的建議基線；不構成本輪 blocking finding。
- 本輪未寫入 Issue，故無收據 [receipt]。若 PM 日後轉錄，報告 SHA-256 [SHA-256] 的取材規則應為「此報告原文 UTF-8，結構化 YAML 開始至範圍外發現結束，整體 `strip()` 後雜湊」。


## Comment 5256357740 · 2026-08-11T17:08:46Z

<!-- wf-review-receipt:v1
card_id: WF-CLI-ROUTING-TIER1
source_sha: e928050d52cb585906d9a6928c4a2f7ad2c961ea
report_sha256: d9970c7bebb2cc944a1772024865ff798d01faa28d33b488a4e4c80d226a8918
-->

取材規則：雜湊輸入是本留言第二個空白行之後的完整報告；起點為該報告第一行 YAML 第一個鍵名的首字元，終點為最後一個範圍外發現項目句末的全形句號。以 UTF-8 編碼與 LF 換行，對這一段 Unicode 文字套用 `strip()`，移除首尾空白與最終 LF；不含收據 marker、取材規則段及兩個分隔空白行。此留言取代 issuecomment-5256346879 的雜湊宣告。

core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "git rev-parse HEAD && git status --short && git diff --check"
    observed: "HEAD=e928050d52cb585906d9a6928c4a2f7ad2c961ea；工作樹乾淨；diff --check 無輸出。"
  - command: "git diff c8ffc3e7ed0b4122474485cf6ffb5499c1a12acf..e928050d52cb585906d9a6928c4a2f7ad2c961ea"
    observed: "R6 僅修改 card.py、test_card.py、README.md；候選行改為已知非路由標頭行的補集。"
  - command: "cd cli && uv run pytest -q"
    observed: "437 passed in 4.89s。"
  - command: "cd cli && uv run pytest -q tests/test_card.py -k 'second_routing_line_survives or no_single_codepoint_prefix or candidate_set_is_monotone or generated_header_line or routing_shape_hidden or duplicated_known or corruption_never or insertion_never or detection_is_permissive'"
    observed: "14 passed, 122 deselected in 2.01s；涵蓋 U+02B0、U+0378、全碼位前綴掃描、插行單調性、借殼行與位置覆蓋。"
  - command: "git merge-base 0d4d282 e928050d52cb585906d9a6928c4a2f7ad2c961ea; git merge-tree 7451b72ba7679893043950d71bad9642665e25da 0d4d282 e928050d52cb585906d9a6928c4a2f7ad2c961ea"
    observed: "實際共同祖先為 7451b72；0d4d282 是後續 main。無衝突標記，main 後新增的 smoke 檔不會因本分支合併被刪除。"
  - command: "cd cli && uv run ruff check"
    observed: "無法執行：目前 uv 環境未安裝 ruff（Failed to spawn: ruff）；非程式碼失敗。"
findings: []

核心痛點已消失：`open` 的四個能力層級欄位、卡面渲染與 `assign` 的實際能力／偏離理由留痕皆已落在唯一寫入通道；R6 的未知 Unicode [Unicode] 前綴不再能讓第二條路由行靜默離開候選集合並放寬成 `matched`。

前輪 finding 閉環：

| Finding | 狀態 | 證據 |
|---|---|---|
| R1-001 | resolved | `assign` 已記錄實際能力與偏離理由。 |
| R2-001 → R3-001 | resolved | 改用結構化版本標記，後續再由 R4 修正標記結構位置。 |
| R4-001 | resolved | 標記必須獨立成行、位於標頭區、且緊鄰唯一路由行。 |
| R4-002 | resolved | 卡面與 README 已明定既有卡永久 `absent`，不設遷移入口。 |
| R4-003 | resolved | R5 版寬鬆字元正規化已移除，改為補集候選收集。 |
| R5-001 | resolved | U+02B0／U+0378 皆為 `ambiguous`；全碼位前綴掃描通過。 |
| R5-002 | resolved | 7 的口徑為 6 個參數化案例加 1 個性質測試；文件已改明組成。 |
| R5-003 | resolved | 實際造訪的 `(行號, 位置, 字元)` 集合與獨立建立的全集相等。 |

範圍外發現：

- #9 與本卡的 `cli/tests/test_review.py` 資源重疊已在跨卡對帳與 #9 卡面明示；屬派工先後順序的協調 [coordination]，本輪不新增 finding。
- README 已誠實列出借殼行、同行語意竄改與保守誤判的殘留面。本輪實測含零寬字元的借殼變體仍為 `matched`，但它不是可被解析成第二條有效路由行的結構，亦不會改寫標記緊鄰、有效路由行所提供的建議基線；不構成本輪 blocking finding。
- 本輪未寫入 Issue，故無收據 [receipt]。若 PM 日後轉錄，報告 SHA-256 [SHA-256] 的取材規則應為「此報告原文 UTF-8，結構化 YAML 開始至範圍外發現結束，整體 `strip()` 後雜湊」。


## Comment 5256428794 · 2026-08-11T17:15:00Z

<!-- wf-review-event:v1 card_id=WF-CLI-ROUTING-TIER1 source_sha=e928050d52cb585906d9a6928c4a2f7ad2c961ea attempt_id=WF-CLI-ROUTING-TIER1-e0-e928050d52cb585906d9a6928c4a2f7ad2c961ea -->
## 查核裁決：APPROVE

- 卡：`WF-CLI-ROUTING-TIER1`　attempt_id：`WF-CLI-ROUTING-TIER1-e0-e928050d52cb585906d9a6928c4a2f7ad2c961ea`
- 查核者：GPT-5@Codex 子代理（收據 issuecomment-5256357740，多行格式合規；PM 已依其取材規則自 GitHub 回讀重算 report_sha256=d9970c7b… 相符。留言 GitHub author 為 ruan6047 即需求方轉貼，故平台可驗證的是「該文字確由需求方發布」，非「該文字由 Codex 產出」）　escalation_epoch：0
- source_sha：`e928050d52cb585906d9a6928c4a2f7ad2c961ea`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-12T01:14:58+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git status --short && git diff --check`
  - HEAD=e928050d52cb585906d9a6928c4a2f7ad2c961ea；工作樹乾淨；diff --check 無輸出。
- `git diff c8ffc3e7ed0b4122474485cf6ffb5499c1a12acf..e928050d52cb585906d9a6928c4a2f7ad2c961ea`
  - R6 僅修改 card.py、test_card.py、README.md；候選行改為已知非路由標頭行的補集。
- `cd cli && uv run pytest -q`
  - 437 passed in 4.89s。
- `cd cli && uv run pytest -q tests/test_card.py -k 'second_routing_line_survives or no_single_codepoint_prefix or candidate_set_is_monotone or generated_header_line or routing_shape_hidden or duplicated_known or corruption_never or insertion_never or detection_is_permissive'`
  - 14 passed, 122 deselected in 2.01s；涵蓋 U+02B0、U+0378、全碼位前綴掃描、插行單調性、借殼行與位置覆蓋。
- `git merge-base 0d4d282 e928050d52cb585906d9a6928c4a2f7ad2c961ea; git merge-tree 7451b72ba7679893043950d71bad9642665e25da 0d4d282 e928050d52cb585906d9a6928c4a2f7ad2c961ea`
  - 實際共同祖先為 7451b72；0d4d282 是後續 main。無衝突標記，main 後新增的 smoke 檔不會因本分支合併被刪除。
- `cd cli && uv run ruff check`
  - 無法執行：目前 uv 環境未安裝 ruff（Failed to spawn: ruff）；非程式碼失敗。

### findings（0，其中 blocking 0）

- （無）

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5256438794 · 2026-08-11T17:15:40Z

## PM 驗證紀錄：本卡的 `APPROVE` 憑什麼被轉錄

本卡是這批六輪來第一個 `APPROVE`，它會把交付狀態推進 `✅通過`。PM 先前拒絕轉錄（無收據、身分不可驗證），查核者補件後才寫入。以下是 PM 實際做的核對，供任何人重跑。

### 一、雜湊重算相符（可重跑）

自 GitHub 回讀收據留言 `issuecomment-5256357740` 的 body，依其自載的取材規則計算：

```
輸入 = 留言第二個空白行之後的全部內容，UTF-8、LF、strip()
算出 report_sha256 = d9970c7bebb2cc944a1772024865ff798d01faa28d33b488a4e4c80d226a8918
收據宣告        = d9970c7bebb2cc944a1772024865ff798d01faa28d33b488a4e4c80d226a8918
相符
```

**一次算對，未試任何變體。** 先前有一輪為了對上雜湊試過五種取材範圍，那次是規則寫得不夠死；本次的規則把起點、終點、編碼、換行、`strip()` 與排除範圍全部指名，PM 依字面照做即得。

### 二、收據格式合規（機械可辨識）

`doctor` 的 `receipt_matches()` 以**整行相等**比對，非子字串：

- `card_id: WF-CLI-ROUTING-TIER1` — 獨立成行 ✓
- `source_sha: e928050d52cb585906d9a6928c4a2f7ad2c961ea` — 獨立成行、完整 40 碼 ✓
- 多行 marker 語法，合 `handoff-contract.md` §3.1.2 ✓

**對照組**：#24 的收據採單行 `key=value` 形式，`receipt_matches()` **完全認不得**，等同無收據——該卡的裁決是 `REQUEST_CHANGES`（保守方向）故仍已轉錄，但其查核者身分同樣無佐證。

### 三、裁決內容與先前轉貼版本逐行相同

留言內 `core_pain_resolved` 至 `findings: []` 的 16 行，與需求方先前於對話中轉貼、PM 已 `--validate-only` 驗過的版本**逐行相同**（去除空行與行尾空白後比對）。**補收據沒有夾帶裁決內容的改動。**

### 四、禁用前綴 0 次

收據留言全文不含事件 marker 的字面前綴。本卡目前仍因三則舊 PM 留言處於 `marker_quarantined`，這則沒有讓情況變糟。

### 這份收據證明什麼、不證明什麼

**證明**：這段報告文字自被雜湊之後未經竄改，且與轉錄進狀態面的內容是同一份。

**不證明**：留言的 GitHub author 是 `ruan6047`（需求方），不是 Codex 的帳號。所以平台可驗證的事實是「**該文字確由需求方發布**」，不是「該文字由 Codex 產出」。查核者的模型／工具身分仍屬自述——`handoff-contract.md` §3.1.2 明寫「收據內模型／工具名稱只屬自述，不能取代平台身分驗證」。

這條限制在本專案是結構性的：跨家族查核者沒有 `wfcli`、也沒有本 repo 的寫入權，所有裁決都經需求方轉貼。**收據把「內容未被竄改」這一半釘住了，「誰產出的」那一半仍然沒有。** 這不是本次補件的缺陷，是通道本身的缺口。

### 三面一致仍須人工核對

`doctor --review-channel` 對本卡回傳 `marker_quarantined`（三則舊 PM 留言引用了字面前綴），故自動裁決判定停機。PM 已人工核對：裁決留言首行為合格 marker、Issue body Log 已寫入對應 attempt 的 review 索引行、Project 交付狀態為 `✅通過`。**三面一致，但不是機器判定的。** 根治歸 [#30](https://github.com/ruan6047/ai-workflow/issues/30)。


## Comment 5259736536 · 2026-08-11T22:46:59Z

收尾完成：PR #32 已合併（a5d4770），worktree／本地分支／遠端分支皆已清理並驗證不存在，交付狀態 🏁完成。

遠端分支以條件式刪除移除（`--force-with-lease` 帶當下 tip），非無條件刪除——雖然 #25 尚未落地，該用法本身是安全側的。

**釋放的資源**：`cli/src/wf_cli/card.py`、`commands/open_cmd.py`、`commands/assign_cmd.py`、`tests/test_card.py`、`tests/test_commands_mocked.py`、`tests/test_amend.py`、`tests/test_review.py`、`cli/README.md`。這解除了 [#9](https://github.com/ruan6047/ai-workflow/issues/9) 與 [#30](https://github.com/ruan6047/ai-workflow/issues/30) 的部分排隊。
