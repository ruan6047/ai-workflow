# #120 WF-BACKLOG-STAGE1 handoff 補上 backlog 階段：讓「閘門過了、進待辦池」有一個受檢查的專責轉換
- state: closed  created: 2026-08-21T14:24:23Z  closed: 2026-08-22T04:23:49Z
- url: https://github.com/ruan6047/ai-workflow/issues/120
- comments: 4

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；改動面已由 2026-08-21 的研究界定完畢（STAGE_STATUS ＋ choices ＋ doctor 的鏡射表 ＋ 三處「六個」散文 ＋ 對帳處置表），而 test_doctor.py:1733-1735 釘的是**導出的同一性**不是硬編清單，故加一格會自動流進斷言。難點在兩處：(1) 新階段要不要帶前提檢查（「受檢查的」是 finding 的用詞），以及那個檢查在單帳號結構下擋不擋得住；(2) 動 CONTRACT_TOOL_RECONCILE.md 時新增或移除任何反引號 kebab 符號都會改變對帳器的 universe。）　查核：待指派（建議 主力型；本卡改的是每一次 handoff 都會走的 choices 與推導表，改錯會影響全部卡片的狀態推導；且它是 ai-workflow#118 的解除條件，查核結論直接決定那張卡能不能合併。**要求跨模型家族或人工查核。** 查核重點：新階段的前提檢查是真的會擋人還是恆真、doctor 鏡射是否同步、以及對帳器缺口數變動是否逐一說明。）
- Initiative：—　spec 基線：ai-workflow#118 R1 的 finding WF-OPEN-INITIAL-STATUS1-R1-002（major／blocking／planner／backlog-transition-has-no-dedicated-writer，收據 issuecomment-5369798326）＋ 需求方 2026-08-21 裁定保留 📥Backlog 補動詞而非移除 @ ai-workflow main 2ae1ff0b
- DB：db_scope=none
- 服務的原始目標：把卡送進待辦池這件事，要有一條會被檢查的路，而不是只有繞過所有閘門的那一條

## 簡介
<!-- card-brief:begin -->
給 📥Backlog 補上專責 writer——它從來沒有過，唯一寫得出它的是 open 的 dataclass 預設與無 choices 的自由文字 --status，使合規轉換與繞過所有閘門的轉換在機械上完全同形。交付：handoff_cmd.py:87-93 的 STAGE_STATUS 與 :280 choices 新增 backlog 階段、doctor.py:1233 鏡射表同步、四處「六個」散文改七個、CONTRACT_TOOL_RECONCILE.md 判定由 read-only 翻回有 writer；並解除 aiwf#118 的合併阻塞。**適用時機**：要查交付狀態如何由 handoff 階段推導、或要新增／變更階段時。⛔ 非射程：不動 cli/src/wf_cli/card.py 的 open 預設（屬 aiwf#118）；不動 AI_WORKFLOW.md（屬 aiwf#119，動它會撞卡）；不移除任何交付狀態；不給 --status 加 choices。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：`📥Backlog` 沒有專責 writer——而且它**從來沒有過**。

`cli/src/wf_cli/commands/handoff_cmd.py:87-93` 的 `STAGE_STATUS` 只有五個階段（`requirement`／`research`／`planning`／`implementation`／`review`），`:280` 的 `choices` 加上 `release` 共六個。**`backlog` 不在其中。** 唯一能寫出 `📥Backlog` 的路徑是 `wfcli open` 的 dataclass 預設（`card.py:295`）與 `--status` 這個**無 `choices` 的自由文字旗標**。

⭐ **也就是說：`open` 的預設一直在**意外充當**它的 writer。** 而 `ai-workflow#118` 把那個預設改成 `💡需求`（正確——規劃閘門在開卡之後才跑）之後，`📥Backlog` 就一個 writer 都不剩：`contract_tool_reconcile` 對它的判定由 `ok` 翻成 `read-only`，`--check` 當場 exit 1。

⚠️ **`#118` 沒有造成回歸，它是把既有的洞露出來。** 該卡的 R1 跨家族查核據此判 `R1-002`（major／blocking／planner／`backlog-transition-has-no-dedicated-writer`），disposition 逐字：「需求方／PM **另卡**決定並實作**受檢查的專責轉換**，或正式移除 Backlog；**完成前不得合併本卡**」。**本卡就是那張另卡。**

**需求方 2026-08-21 已裁定保留 `📥Backlog`、補動詞而非移除**，依據是實查：canonical `AI_WORKFLOW.md:18` 印的序列 `📥Backlog → ⏳待執行 → 🔨執行中` 裡，**中間那一格在同一句話內被廢止**（「廢止的歷史值…新寫入不得用：`🚧進行中`、`⏳待執行`」）；而 `docs/CONTRACT_TOOL_RECONCILE.md:427` 記著 `⏳待執行` 是 `read-only`、來源只有兩份**印序列的文件**、**從來沒有 writer**；全 173 張卡現況分布中它 **0 張**。⇒ **`⏳待執行` 從來不是一個真的替代品，`📥Backlog` 是唯一存在過的「閘門過了、等人認領」那一格。** 移除它，`💡需求` 與「有人在做」之間就沒有東西了。

⚠️ **而現況的實害是機械的**：`assign --status` 與 `handoff --status` 都是自由文字、無 `choices`（`docs/CONTRACT_TOOL_RECONCILE.md:303` 逐字記著它「**現在讓所有前提都可繞過**」），所以今天把卡送進 Backlog 的唯一途徑，也是繞過所有閘門的那條途徑——**合規的轉換與違規的轉換在機械上完全同形。**

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/handoff_cmd.py",
    "file:cli/src/wf_cli/doctor.py",
    "file:cli/tests/test_doctor.py",
    "file:cli/tests/test_commands_mocked.py",
    "file:docs/CONTRACT_TOOL_RECONCILE.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] ⭐ handoff 新增 backlog 階段：cli/src/wf_cli/commands/handoff_cmd.py:87-93 的 STAGE_STATUS 加 backlog → 📥Backlog，:280 的 choices 同步加入。⚠️ 位置須在 planning 與 implementation 之間，與 canonical AI_WORKFLOW.md:18 的序列同序。
- [ ] ⭐ doctor 的鏡射表同步：cli/src/wf_cli/doctor.py:1233 的 HANDOFF_STAGE_EXPECTED_STATUS 加同一格。⚠️ 該檔 :1210／:1228／:1396 三處散文寫著「六個」，測試 docstring（test_doctor.py:1728）也寫「六個」——四處皆須改為七個。⛔ 只改表不改散文會留下一份說謊的註解。
- [ ] ⭐ 「受檢查的」是 finding 的用詞，須逐項回答並在卡上留痕：本階段要不要帶前提檢查？若帶，檢查什麼（例如「Log 內須有 planning 階段的事件」）？⚠️ 若該檢查在本 repo 的單帳號結構下恆真，**必須明文標注它恆真**而不是留一個看似有檢查的欄位——ROADMAP §1 明文禁止「把恆真性導出成 structurally-vacuous 再假裝那是檢查」。⛔ 判斷不出來就停下回報，不得自行決定。
- [ ] ⭐ 對帳處置表同步：docs/CONTRACT_TOOL_RECONCILE.md 內 delivery_status/📥Backlog 的判定會由 read-only 翻回有 writer，JSON 與 §6 的產生輸出表皆須更新。⚠️ 這一項是 #118 R1-003 被判 blocking 的同一種病（產生輸出未重產），本卡不得重蹈。
- [ ] ⭐ 雙向可證偽驗收：(a) 以 mocked 路徑實跑 handoff --next-stage backlog，斷言交付狀態為 📥Backlog；(b) 對照組——doctor 的 audit_state_face_drift 對「Log 有 backlog 階段事件、欄位為 📥Backlog」的卡須判 consistent，對「欄位為 📥Backlog 但 Log 無任何解釋事件」的卡仍須判 drift。⚠️ 只驗 (a) 會被一個「永遠回 📥Backlog」的實作通過。
- [ ] ⭐ 變異檢驗：只改 STAGE_STATUS 不改 doctor 鏡射 → test_doctor.py:1733 的同一性斷言必須轉紅；反向亦然。兩個方向都要，且都在最終碼上跑。
- [ ] ⛔ 非目標——不動 cli/src/wf_cli/card.py 的 open 預設（那是 #118 的射程，且本卡與它撞檔須序列化）；⛔ 不動 AI_WORKFLOW.md（跨專案 canonical，且 ai-workflow#119 正在該檔上執行——**動它會直接撞卡**）；⛔ 不移除 📥Backlog 或任何交付狀態；⛔ 不給 --status 加 choices（那是獨立一問，docs/CONTRACT_TOOL_RECONCILE.md:303 已登記）。
- [ ] 既有 cd cli && uv run --frozen pytest -q 不得因本卡而失效或被排除；scripts/contract_tool_reconcile.py --check 須維持 exit 0。

## 驗證

- [ ] ⭐ 端到端實證：以 mocked 路徑實跑 handoff --next-stage backlog，貼出寫入的交付狀態欄位值。⚠️ 不得只靠讀碼宣稱。
- [ ] ⭐ 變異檢驗兩個方向各貼一次指令與輸出，還原後貼檔案 sha256 或 git diff 為空的證明。
- [ ] ⭐ 四處「六個」→「七個」的散文改動逐處貼出（含 test_doctor.py:1728 的 docstring）。
- [ ] python3 scripts/contract_tool_reconcile.py --check 貼真實 exit code 與缺口數。⚠️ 量 exit code 不要接管線（$? 會抓到 tail 的狀態）。⚠️ 缺口數必然變動（📥Backlog 從 read-only 翻回有 writer），須逐一說明是哪個符號、判定怎麼變、為什麼。
- [ ] cd cli && uv run --frozen pytest -q 貼末行並與改動前並列說明差額。
- [ ] ⚠️ 報告須明列沒驗到什麼。至少包含：本卡不改任何既有卡的狀態；未在真實狀態面驗證（不得跑 wfcli 寫入動詞去測，會污染真實看板）；以及新階段是否真的被人使用——那要等 PM 之後開卡時採用，本卡驗不到。
- [ ] ⚠️ 不 merge、不跑任何 wfcli 寫入動詞、不 gh issue comment。
## Log

- 2026-08-21T22:24:22+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-21T22:25:14+08:00 handoff by wf-cli → owner ruan6047；iteration 0；SHA 2ae1ff0be3ae78f38392b81e1c5b3fe9409c79b8；證據 規劃 Gate 通過（需求方 2026-08-21）。Discovery 與 Design 皆已於當日完成並固化進卡面：改動面已界定（STAGE_STATUS ＋ choices ＋ doctor:1233 鏡射表 ＋ 四處「六個」散文 ＋ 對帳處置表），且已查證 test_doctor.py:1733-1735 釘的是**導出的同一性**（set(HANDOFF_STAGE_EXPECTED_STATUS) == set(STAGE_STATUS) | {'release'}）而非硬編清單，故加一格會自動流進斷言、只改一邊必紅。方向裁定：保留 📥Backlog 補動詞而非移除——依據是 ⏳待執行 在 AI_WORKFLOW.md:18 同一句內被廢止、CONTRACT_TOOL_RECONCILE.md:427 記它 read-only 無 writer、全 173 張卡 0 張，⇒ 它從來不是真的替代品。⚠️ --iteration 釘住 0。。
- 2026-08-21T22:25:41+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code（子代理）；分支worktree claude/WF-BACKLOG-STAGE1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-backlog-stage1；交付狀態 🔨執行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-21T22:47:39+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 0；SHA 3c236ca73344ccff7373a0e0483d78506483fee5；證據 交付 3c236ca（基線 2ae1ff0b，單一 commit），寫入集嚴格為卡面宣告五檔。PM 獨立複驗：git diff --name-only 逐字為那五檔、card.py 與 AI_WORKFLOW.md 命中 0；STAGE_STATUS 新增 backlog→📥Backlog；前提檢查在 handoff_cmd.py:417-427 實際讀 Project 交付狀態欄、不符 return 4，非裝飾；CI 對本 SHA success（headSha=3c236ca7，run 32493540493），PM 以 --commit 鎖 SHA 查詢而非看最近一筆。執行者對「受檢查的專責轉換」逐項作答：檢查=前一狀態須為 🧭規劃中；否決候選 A（Log 有 planning 事件）因 handoff 留痕不記 --next-stage 故機械上不可判定；否決候選 B（需求方批註放行）因本 repo 全角色共用同一帳號故恆真，並依 ROADMAP §1 明文標注它仍無執行者、不宣稱落地。⭐ 三項要查核者裁決：(a) 前提檢查對真實流程的副作用未驗，執行者未回放既有卡。PM 實測當下看板：176 張，💡需求 30／📥Backlog 22／🧭規劃中 0／🔬研究中 0。#118 合併後 open 不再預設 Backlog，屆時每張卡都須走 💡需求→🧭規劃中→📥Backlog；而 canonical §3.1 第 113 行只點名 T3 需要需求方批註放行才進 Backlog，T0-T2 無此要求。是否要讓所有級別都被強制走 🧭規劃中，屬需求方取捨，執行者依 §0 序列取 fail-closed 那一邊並主動請求退回審視。(b) 端到端證據全走 FakeGhRunner mocked 路徑，刻意不污染真實看板，故「在真的 GitHub Project 上寫得成功」本卡無證據。(c) 對帳器缺口數 58→58 未變，派工包寫「必然變動」的前提是錯的——該前提只在 #118 合併後成立，本卡基線上 card.py:295 仍在寫 📥Backlog 故本來就是 ok；錯的是派工包，執行者的處置正確且已寫進 CONTRACT_TOOL_RECONCILE.md §4.1.1。另注意執行者過程中初稿 docstring 寫了「非目標」三字，使對帳器把 card_field/非目標 由 absent 翻成 mention-only、--check exit 1；處置是改寫措辭而非把該判定登記進 JSON，理由是登記等於記下一個假訊號。⚠️ §6 大表非 --check 涵蓋範圍，執行者以逐字 diff 補驗，但那一層沒有機械執行者（CI 不跑對帳器）。。
- 2026-08-21T23:12:02+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex（需求方轉貼；無 GitHub 收據留言，PM 逐字轉錄）；core_pain_resolved yes；self_run 10 項；findings 3 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-BACKLOG-STAGE1-e0-3c236ca73344ccff7373a0e0483d78506483fee5。
- 2026-08-22T00:29:18+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子代理）；iteration 1；SHA 3c236ca73344ccff7373a0e0483d78506483fee5；證據 R1 REQUEST_CHANGES 退回原執行者、原分支 claude/WF-BACKLOG-STAGE1、原 worktree .claude/worktrees/wf-backlog-stage1，iteration 遞增至 1。需求方 2026-08-21 就 R1-001 裁定採丙案：閘門依級別分流，T2 以上要求前一狀態為 🧭規劃中，T0／T1 直通。裁定依據為 AI_WORKFLOW.md §3.1 表格第三列逐字「所有 T2 以上」屬疊加下限故 T2 在射程內、只有 T0／T1 無對應列且照 §3.1 前言可直接 commit；實測支撐為全 176 張中 T2 佔 61（35%）、現在 📥Backlog 22 張中 T2 佔 8（36%），甲案 T3-only 會讓三分之一流量繼續沒有狀態可表達規劃。⚠️ 需求方同時確認丙案是文本加一次推論而非逐字，故本輪必須把該規則寫進 canonical AI_WORKFLOW.md，不得只在工具內硬編——工具執行 canonical 沒說的規則正是本卡要治的病。附帶三條：T0／T1 直通分支須明文標注此分支不做檢查因 §3.1 無對應列；級別讀不到或不認得一律 fail closed 要求 🧭規劃中；⛔ 不得加 ⏸阻塞 當合法前驅狀態（實查四張阻塞卡全部從執行或退回態阻塞、解阻回 🔨執行中，觀察到的實例為 0，加了就是零資訊的檢查）。另須補 R1-001 未閉合的另一半：回放既有卡證明閘門不會扭曲既有流程。⚠️ 基線須更新：main 已由 2ae1ff0b 前進到 b2a6d54（#119 已 merge，動過 AI_WORKFLOW.md 與 templates/TASKS.md），本分支基線仍是 2ae1ff0b 且本輪要動 AI_WORKFLOW.md，必須先對齊新 main。R1 已通過項不重驗、不擴審（review-prompt.md §6）。。
- 2026-08-22T01:10:14+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 1；SHA fe296ad665cac8ed69a4f15b9d2df0931d6b26c5；證據 R2 交付 fe296ad（基線 b2a6d54，已 rebase 對齊含 #119 的新 main）。PM 獨立複驗：寫入集六檔逐字為 AI_WORKFLOW.md 加原五檔、card.py 命中 0；canonical §3.1 新條文「進 📥Backlog 的狀態前提依級別分流」在位；BACKLOG_GATE_EXEMPT_TIERS=(T0,T1) 於 :196 定義、:470 使用；閘門 fail closed（級別不在 TIERS 一律照 T2 以上）且豁免分支有明文標注不做檢查並往 stderr 印出；CI 以 --commit fe296ad665 鎖 SHA 查詢為 success（run 32506159794），非看最近一筆。R1-001 的四條要求逐項閉環，規則先寫進 canonical 再鏡射進碼，且有一條測試讀 AI_WORKFLOW.md 正文比對常數、分家即紅。⚠️ 三項要查核者特別看：(1) 執行者用 rebase + force-with-lease 對齊 main，使 R1 的交付 SHA 3c236ca 在 remote 上不再可達（PM 複驗：git ls-remote 命中 0，保存用 tag wf-backlog-stage1-r1-preserved 只在本機、未 push），而 R1 review event 的 attempt_id 內嵌該 SHA；rebase 的選擇理由執行者已具名（§7.3 第 3 條，狹義例外兩項皆不成立），但代價是否可接受請裁決。(2) 卡面「非目標」欄仍寫著不得動 AI_WORKFLOW.md，本輪動它的授權來自 iteration 1 的 handoff 事由；欄與實際授權不一致，PM 依開卡後欄位不可改的慣例未 amend，以 Log 為準。(3) 回放的 A 段執行者自行判定為零鑑別力並明說不當通過證據，B 段指出三案「會被擋」相等是因為此刻 0 張停在 🧭規劃中（算術性質非閘門嚴格），有資訊的是 C 段可證偽預測：丙案對甲案的增量 = 未終態 T2 卡 14 張 24.6%，並預先寫明「若接近 0 則丙案是零收益擴張應退回甲案」。請判斷這個回放形狀是否真的有鑑別力。另注意執行者主動揭露：變異檢驗時曾用 git checkout -- 洗掉未 commit 的編輯，重做後逐位元比對過，但該事件發生過。快照母體與 PM 報的數字不同（執行者用 08-21 10:40 的 170 張快照，PM 報 176 張），兩者觀測時點不同、未對齊。。
- 2026-08-22T02:06:27+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex（需求方轉貼；無 GitHub 收據留言，PM 逐字轉錄）；core_pain_resolved yes；self_run 9 項；findings 3 項（blocking 2）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-BACKLOG-STAGE1-e0-fe296ad665cac8ed69a4f15b9d2df0931d6b26c5。
- 2026-08-22T02:22:56+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子代理）；iteration 2；SHA fe296ad665cac8ed69a4f15b9d2df0931d6b26c5；證據 R2 REQUEST_CHANGES 退回原執行者、原分支 claude/WF-BACKLOG-STAGE1、原 worktree，iteration 遞增至 2。R2-002（R1 交付 SHA 無遠端保存 ref）已由需求方 2026-08-22 授權處置完畢：PM 建立並 push annotated tag refs/tags/reviewed/WF-BACKLOG-STAGE1-r1 指向 3c236ca73344ccff7373a0e0483d78506483fee5，遠端複驗該 tag 的 peeled ref 解出同一 SHA，tag 訊息載明保存對象與依據；執行者不需為此做任何事。剩 R2-001（doctor.py 手寫 canonical 行號引用未隨插入兩行更新）：需求方裁定採甲案，改為穩定引用形式而非更新數字——理由是同族已三輪（#119 抓到、#120 弄壞、現在修），再修數字在 #118 落地時會有第四次。查核者處置原文為「更新引用，或改為穩定章節錨點」，甲案取後者。⚠️ 前提更正已記入 R2-001：以釘死基線 b2a6d54 實測，:216 本來就是 merge 規則而非 T2 規則、:211 指到程式碼圍欄行、:222 指到空行，三者原本已錯；本輪明確造成的回歸只有 :220 那 6 處，:222 那 2 處則由空行偶然變正確。R2 已通過項不重驗、不擴審：R1-001 四條閉環判定通過、變異檢驗 M1 至 M4 已由查核者自行重跑、回放 C 段判定有鑑別力、裁決 (b) 卡面非目標未 amend 判定正確、裁決 (c) fail-closed 測試判定不是零資訊。。
- 2026-08-22T02:44:34+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 2；SHA 94dc3c323c0e98bad939d954bc2b5fe3902e982a；證據 R3 交付 94dc3c3（基線 b2a6d54，進駐時 origin/main 仍是 b2a6d54，未 rebase 未 merge、未動任何 tag、未 force-push）。本輪 diff 三檔（doctor.py、test_doctor.py、CONTRACT_TOOL_RECONCILE.md），整支對基線六檔，與宣告寫入集逐字相同。CI 以 --commit 94dc3c3 鎖 SHA 為 success（run 32514432605）。

R2-002 已由需求方 2026-08-22 授權、PM 處置完畢：annotated tag refs/tags/reviewed/WF-BACKLOG-STAGE1-r1 已 push，遠端 peeled ref 解出 3c236ca73344ccff7373a0e0483d78506483fee5。執行者未碰該 tag。

新引用形狀：CANONICAL_ANCHORS 收三段條文原文片段，CANONICAL_SECTION 由節標題導出而非另寫數字，canonical_cite() 產出節次加逐字片段，註解／docstring／使用者可見診斷訊息共用同一份。反長回來的判準取封閉集合（點名 canonical 的那一行不得夾帶任何數字），故 §6:220、第 220 行、L220 都抓得到，不必事先窮舉寫法。

執行者做了七個變異，M1 至 M5 KILLED、M6 對照組如記載存活、M7（條文語意反轉但片段字串原封不動）存活且執行者實測證明它是真的漏而非假設。過程中自陳兩次自打：守衛先擋下他自己一次（parents[2] 與檔名同行），M5 第一版因門檻寫成 count 大於等於 3 而存活、已改為扣掉定義與 dict 鍵後至少一處並補對照組。

PM 獨立複驗：寫入集逐字相符；Pyright 在 doctor.py:607/:625/:641 報的 identity_basis 型別錯誤位於本輪第一個 hunk（:664）之前，屬既有非本輪造成。

三項要查核者裁決：

(a) 執行者再度更正了前提，PM 與前一輪查核者兩邊都寫錯過。執行者在 b2a6d54 自行重驗的結論是：:222 那兩處並沒有偶然變對，基線是空行、HEAD 上指到 trailer 末端規則而非它宣稱的 merge 規則（merge 規則在 HEAD :218），是換一種錯法；且 :211 與 :216 的真正規則同在基線 :210 那一條 bullet 裡。請自行複驗這個更正。

(b) 執行者指出 PM 說的十處是 grep 前綴形式的命中數，漏了第十一處 doctor.py:664 的區間式引用（AI_WORKFLOW.md §6:210-226，含空格與節號故 pattern 掃不到，且基線上就已越界跨進 §6.1），已一併處理。PM 已複驗該引用在基線存在、在交付上已改為錨點形式。

(c) 最重要的一項：射程外有十三處引用在基線上是正確的、被本分支的加兩行位移弄壞，本輪不改善它們。清單為 cleanup.py:3、handoff_cmd.py:25、WF_CLEANUP_GUARD1.md:11 與 :234、WF_EVENT_IDEMPOTENCY1.md:13 與 :59 與 :1193 至 :1197、WF_RESOURCE_WRITESET1.md:17 與 :1361。PM 抽驗 :141 與 :146 兩個目標行，確認基線與交付上的內容完全不同，claim 屬實。另有基線上就已錯的兩處（ROADMAP.md:120 引 :221 off-by-one、WF_RESOURCE_WRITESET1.md:287 引 :147 指到空行）。執行者並自陳十七這個數字是下界不是窮舉，裸接續寫法如 WF_EVENT_IDEMPOTENCY1.md:1196 的形式不被其掃描 pattern 計入。請裁決：明知弄壞十三處正確引用而不修，是否構成 blocking，還是應以另案處理。

執行者自陳沒驗到：M7 是刻意保留的漏，若需求方要求語意漂移也轉紅需要條文層雜湊或快照，本輪未做也未評估成本；新守衛只保護 doctor.py 與 test_doctor.py，#118 若動 canonical 射程外那批仍會靜默腐爛；CI 只確認 job 整體 success，未逐步比對 escalation replay 那一步的輸出內容；pytest 1064 passed（釘死基線 b2a6d54 為 1052）。。
- 2026-08-22T10:15:02+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex（需求方轉貼；無 GitHub 收據留言，PM 逐字轉錄）；core_pain_resolved yes；self_run 9 項；findings 2 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-BACKLOG-STAGE1-e0-94dc3c323c0e98bad939d954bc2b5fe3902e982a。
- 2026-08-22T10:17:56+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子代理）；iteration 3；SHA 94dc3c323c0e98bad939d954bc2b5fe3902e982a；證據 R3 REQUEST_CHANGES 退回原執行者、原分支、原 worktree，iteration 遞增至 3。R3-002（M7 語意反轉漏網）判為 info 非阻擋、不需處理，查核者理由是條文雜湊或快照只會把每次合法改文也打紅、仍無法判定語意正確，不應作為本卡必備機制。剩 R3-001（本分支造成 13 處原本正確的行號引用失準且未修復）為唯一 blocking，處置原文為「需先取得範圍授權並修復，或由需求方安排依賴修復後再合併本 SHA」。需求方 2026-08-22 選前者並授權擴充寫入集，新增四檔：cli/src/wf_cli/cleanup.py、docs/WF_CLEANUP_GUARD1.md、docs/WF_EVENT_IDEMPOTENCY1.md、docs/WF_RESOURCE_WRITESET1.md（handoff_cmd.py 原已在寫入集內）。PM 實查：該 13 處全部指進 AI_WORKFLOW.md §4.1 Control-plane Contract（基線 :134 至 :149），故需求方指示修法為把行號拿掉改引節次加原文片段，而非更新數字。R3 已通過項不重驗、不擴審：R2-001 判定已閉環、七個變異矩陣已由查核者自行重跑（M1 至 M5 KILLED、M6 與 M7 存活符合預期）、前提複核、tag peeled ref、差異檔案數、CI、對帳器、SHA-256 與 trailer 均已通過。。
- 2026-08-22T10:48:34+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子代理）；iteration 4；SHA 64024e5922d7458fddbe4d06ab40e11fbdec775f；證據 R4 執行者依指示停手回報：snapshots/README.md:53 的 canonical:138 是本分支插兩行直接推歪的（基線 :138 為 remote coordination adapter 是唯一 lifecycle event writer、完全正確；HEAD :138 已變成別的條文），屬 R3-001 裁決語句「不能明知合併會留下錯誤 canonical 引用」涵蓋的同一類，但該檔不在十檔寫入集內。PM 已複驗該落差屬實、且 snapshots/README.md 確實在 origin/main 上。需求方 2026-08-22 授權擴充寫入集，新增第十一檔 snapshots/README.md，交回原執行者續修，iteration 遞增至 4。本輪不是查核退回、是範圍擴充後的續作。R4 已完成且不重驗的部分：十檔寫入集未越界、CI 於 64024e59 為 success（run 32546993914）、窮舉四種寫法並修 23 行、守衛判準取封閉集合、pytest 1065 passed（基線 b2a6d54 經另開 detached worktree 實跑確認為 1052）、對帳器 exit 0 缺口 58、uv lock --check 與 replay 114/114、trailer 四筆全 compliant。R4 另更正兩項前提，已記錄：PM 說的「13 處全部指進 §4.1」不成立（:162 與 :165 在 §4.3 狀態面與單一寫入通道），查核者說的「13 處都是本分支造成、非既有瑕疵」有兩處反例（WF_EVENT_IDEMPOTENCY1.md:1197 與 WF_RESOURCE_WRITESET1.md:287 在基線上就已指錯，後者是查核者清單漏列的第 14 處）。。
- 2026-08-22T11:07:23+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子代理）；iteration 5；SHA 7628bb0bf6c65dc5344dde613d146e01746f292d；證據 R5 執行者依指示停手回報第二處同族缺陷：scripts/daily_snapshot.sh:14 的 canonical:138 與 snapshots/README.md:53 完全同形，且該檔在本分支未被改動故 :14 是基線原文，屬被本分支推歪而非基線就錯。PM 已複驗屬實（git diff --name-only b2a6d54..7628bb0 對 daily_snapshot.sh 命中 0；基線 :138 為 remote coordination adapter 是唯一 lifecycle event writer、R5 上 :138 已變成別的條文）。

需求方 2026-08-22 裁定採乙案：不再逐檔加白名單，改為全 repo 掃描一次修完，並把守衛由封閉清單換成開放集合加明文排除集。理由是每一輪都多一處（R3 列 13、R4 修 23 並停手回報 1、R5 又找到 1），白名單保證還有下一輪且證明不了沒有下一個；執行者已自行指出正解是開放集合、只被寫入集鎖死。

寫入集授權擴充為：所有含有帶行號 canonical 引用的檔案，加上守衛與測試檔本身。硬性非目標維持：不動 cli/src/wf_cli/card.py（#118 射程）、不改任何條文語意、只動引用該行。若窮舉結果的檔案數或改動量大到執行者判斷本輪會失控，須停下回報而非硬做。

R5 已完成不重驗：snapshots/README.md:53 修正、守衛射程加入該檔、V4 與 V5 與 V6 三個變異（V4 紅 V5 綠 V6 綠，證明清單項承載而非裝飾）、pytest 1065、對帳器 exit 0 缺口 58、uv lock --check、CI run 32547825166 於 7628bb0 success、trailer 四鍵。

執行者本輪自陳兩項續存限制，需求方已知悉：守衛只管形態不管指得對不對（節次加一段不存在的文字照樣全綠，片段逐字性是一次性人工查的、無持續守衛）；snapshots/README.md:3 引同一條文且節次寫對，但引文去掉內層粗體標記且跨行斷開故不是 raw 逐字，非行號缺陷故未處理。另執行者主動揭露其第一版變異腳本以 git checkout -- 還原時洗掉未 commit 的 R5 改動，已重做並改用記憶體備份重跑，報告結論來自重跑那次；同形狀錯誤在 R2 已發生過一次。。
- 2026-08-22T11:35:00+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 5；SHA 729ea7f1521e8a6dcdf5a546607ac6646a70195a；證據 R6 交付 729ea7f（基線 b2a6d54，執行者進駐後確認 origin/main 未前進、merge-base 相符）。需求方 2026-08-22 裁定採乙案：不再逐檔加白名單，全 repo 掃描一次修完，守衛由封閉清單換成開放集合加明文排除集；寫入集授權為所有含帶行號 canonical 引用的檔案加守衛與測試檔。交付十六檔。

PM 獨立複驗：CI 以 --commit 729ea7f 鎖 SHA 為 success（run 32549133164）；在 worktree 實跑 python3 scripts/canonical_citation_scan.py 得 SCAN_EXIT=0、掃描檔案數 123、命中不含排除 0、排除集 1 項；--all 確認被排除者仍列得出來（是刻意排除而非沒掃到）。工作樹乾淨、HEAD 為 729ea7f。

窮舉結果：原始 8 檔 39 行，其中 4 行純因 ISO 時戳的時分秒誤判、改用精確完整 ISO 8601 剪除後歸零，執行者判定那不是缺陷也不需要排除項。剩 5 檔 35 行：CONTRACT_TOOL_RECONCILE.md 30 行排除（產生物）、ROADMAP.md 2 行修、DEV_AIWF_MINIMAL_CI1.md 1 行修、daily_snapshot.sh 1 行修、test_doctor.py 1 行修（守衛自己的註解寫了字面壞例子，改以字串拼接造樣本）。

執行者的重要發現：四處手寫引用裡有三處早就指錯而從未有東西報過錯。PM 抽驗兩處確認屬實：ROADMAP:120 引 :221，基線 :221 是 review event 必答那條而非它宣稱的 commit trailer 守衛；ROADMAP:234 引 §6:222，基線 :222 是空行。⚠️ 第三處請查核者自行判斷：執行者說 daily_snapshot.sh 引的 :138 指到 §4.1 開頭的 adapter 定義而非它要引的條文，但 PM 實查基線 :138 的 bullet 內含「必須以每日 snapshot export 回 git 建立離線稽核副本」該子句，故該處是否算早就指錯有判斷空間，PM 不下定論。

守衛形狀：scripts/canonical_citation_scan.py 同時是可執行腳本與被 pytest 呼叫的實作，故窮舉與守衛不可能分岔。排除集只有一項且理由寫在碼裡；test_every_exclusion_is_load_bearing 機械保證排除集不是垃圾桶，關掉排除重掃後沒有實際命中的排除項會判死、必須刪除。五個變異全部符合預期，其中 M4 精確重現了執行者自己在 R4 犯的 ISO 剪除漏報 bug。執行者本輪先 commit 再做變異，未再用 git checkout -- 還原（該錯誤它在 R2 與 R5 各犯過一次）。

數字：pytest 1080 passed，對帳為 1065 減 1 加 16；對基線 b2a6d54 的 1052 為加 28。contract_tool_reconcile.py --check exit 0 缺口 58。uv lock --check OK、replay 114/114。trailer 兩筆 commit 三個治理鍵皆解析得出、末端連續。

執行者自陳九項沒驗到，其中三項請查核者特別裁決：其一，散文片段的逐字性完全沒有守衛，只驗形態不驗指得對不對，節次寫錯或片段根本不存在於 canonical 照樣全綠；執行者量過全 repo 引號內容 47 段逐字命中、56 段沒有，但那 56 段絕大多數是中文行文的一般引號而非引用，要驗逐字性得先發明機器可辨識的引用語法並全面改寫，判斷會失控故未做。其二，R4 與 R5 寫的部分散文引用加了 canonical 沒有的強調標記（例 WF_CLEANUP_GUARD1.md 引的那句 canonical 該行無粗體），不帶行號故不在本輪窮舉射程，但過不了嚴格逐字檢查。其三，CI 綠不代表合併結果綠：這一 run 是 push 事件、job 名為 tests (branch head)，依本 repo CI 設計明確不是 required check，合併結果只在 pull_request 事件下才測。另六項：未追蹤檔看不到（掃描中途曾報 121 檔、看不到剛寫的兩個新檔直到 git add，已寫成測試釘住邊界）；條文語意被改寫而片段字串沒動時不會響；gate 是「行內有 AI_WORKFLOW 或 canonical」，用別的稱呼引用會完全漏掉（查過目前沒有這種寫法帶行號，但那是現在剛好沒有）；test_doctor.py 仍有一份封閉的兩檔清單刻意保留、是更嚴的規則且該兩檔同時被全 repo 掃描涵蓋，但清單本身仍是人維護；ruff 未跑，本 repo 工具鏈沒有 ruff；R5 與 R4 已驗項目依指示未重驗。。
- 2026-08-22T12:20:13+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex（需求方轉貼；無 GitHub 收據留言，PM 逐字轉錄）；core_pain_resolved yes；self_run 10 項；findings 3 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-BACKLOG-STAGE1-e0-729ea7f1521e8a6dcdf5a546607ac6646a70195a。
- 2026-08-22T12:23:34+08:00 handoff by wf-cli → owner —；iteration 5；SHA 729ea7f1521e8a6dcdf5a546607ac6646a70195a；證據 需求方 2026-08-22 授權合併。PR 123 以 merge commit 2dcab60 落 main，四個 trailer 齊全含 Reviewed-by: GPT-5@Codex。⭐ 查核者判 (c) 非阻擋時明說「本次 CI 只證明交付 SHA，未證明未來合併結果」——開 PR 後 ruleset 要求的 tests check（merge ref 那支）實測 SUCCESS，該項由推論轉為觀測；tests (branch head) 亦 SUCCESS。免部署卡故 release 即終態。三個非阻擋 finding 未處理：R6-001（ISO 專測不是獨立承載的，M4 時仍通過、是被其他測試擋下，建議後續改成不含 ISO 的節次引用）、R6-002（排除集保證只對死排除成立、不證明理由語意正確；同一實作不分岔的宣稱範圍應收斂為已驗證的執行條件）、R6-003（push CI 不代表合併樹、散文片段逐字性未驗、部分散文多加粗體）。本卡合併解除 ai-workflow#118 WF-OPEN-INITIAL-STATUS1 的阻塞條件。；收尾清理：已清除 worktree、本地分支、遠端分支。
- 2026-08-26T21:59:28+08:00 amend by wf-cli（op 25dcee09）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:b90bdfcb404ad0d20a4dc071e3265bec1f44820cce39812f2df1cfcfaf93713b (791 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5371712614 · 2026-08-21T15:12:03Z

<!-- wf-review-event:v1 card_id=WF-BACKLOG-STAGE1 source_sha=3c236ca73344ccff7373a0e0483d78506483fee5 attempt_id=WF-BACKLOG-STAGE1-e0-3c236ca73344ccff7373a0e0483d78506483fee5 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-BACKLOG-STAGE1`　attempt_id：`WF-BACKLOG-STAGE1-e0-3c236ca73344ccff7373a0e0483d78506483fee5`
- 查核者：GPT-5@Codex（需求方轉貼；無 GitHub 收據留言，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`3c236ca73344ccff7373a0e0483d78506483fee5`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-21T23:12:02+08:00

### self_run（查核者實跑）

- `git diff --name-only 2ae1ff0b..3c236ca73344ccff7373a0e0483d78506483fee5`
  - 寫入集恰為五檔；card.py、AI_WORKFLOW.md diff 為 0；--status 仍無 choices
- `檢視 handoff_cmd.py:417 的前提檢查與 test_commands_mocked.py:928 的端對端測試`
  - 實作確實讀 Project 的交付狀態欄，不符直接 return 4，且拒絕路徑不寫欄位或 Log；端對端測試同時覆蓋拒絕與放行
- `變異檢驗兩方向（只改寫入端、只改導出端），還原後重跑`
  - test_drift_handoff_table_is_exhaustive_and_pinned_to_writer 兩方向皆紅；還原後通過；兩檔 SHA-256 與變異前一致，最終工作樹乾淨
- `檢視 test_doctor.py:1727 的導出同一性斷言`
  - HANDOFF_STAGE_EXPECTED_STATUS 與 STAGE_STATUS 聯集 release 的集合與逐格同一性成立；新增 Backlog 自動進入參數化案例
- `pytest（基線與交付各一次）`
  - 基線 1052 collected；交付 1056 passed；差額 4 = 3 個新測試加參數化自動增加 Backlog 一例
- `gh run 以指定 SHA 查詢`
  - CI 成功，run 32493540493
- `檢視 doctor.py:1229 散文`
  - 已是「前六個」
- `contract_tool_reconcile.py --check 並比對 §6 產生表`
  - exit 0，缺口仍為 58；§6 表與本 SHA 產生器輸出逐字相同
- `檢視 CONTRACT_TOOL_RECONCILE.md §4.1.1 對 disposition JSON 的處置`
  - 處置正確：基線 2ae1ff0b 的 Backlog 本來不是缺口，#118 合併後才會改變該事實
- `檢視 AI_WORKFLOW.md:100 與 :113 對各級別的要求`
  - T0–T2 僅要求範圍與驗收；T3 才明定需求方批註放行後才進 Backlog

### findings（3，其中 blocking 1）

- **WF-BACKLOG-STAGE1-R1-001**　severity=major　blocking=true　class=governance　attribution=planner　root_cause_id=`gate-scope-tier-unspecified`
  - evidence：handoff_cmd.py:417 的 backlog 閘門完全未讀取級別，會強制 T0–T4 都先到 🧭規劃中；其依據只是 AI_WORKFLOW.md:18 的 §0 順序，但 :100 對 T0–T2 僅要求範圍與驗收，:113 才對 T3 明定需求方批註放行後才進 Backlog。卡面未指定閘門的級別適用範圍。與此同根：未回放既有 176 卡，故無法證明把閘門擴張至 T0–T4 不會扭曲既有流程。
  - disposition：退回需求方裁定級別適用範圍。在未改 canonical 前，採 T3-only 最符合最小擴張原則；不得以 §0 的狀態順序自行擴張。T4 與 Initiative 若要納入，還需其更強閘門的可驗證設計，不能只靠「目前是規劃中」。
- **WF-BACKLOG-STAGE1-R1-002**　severity=info　blocking=false　class=governance　attribution=external　root_cause_id=`reconcile-section6-no-standing-guard`
  - evidence：CONTRACT_TOOL_RECONCILE.md §6 表未納入 --check；本次逐字比對已證明表由本 SHA 重產，但沒有持續性的機械守衛（CI 不跑對帳器）。
  - disposition：應另列後續缺口，不應冒充已自動化。非本卡拒絕理由。
- **WF-BACKLOG-STAGE1-R1-003**　severity=info　blocking=false　class=environment　attribution=external　root_cause_id=`mocked-only-integration-risk`
  - evidence：端對端證據僅走 FakeGhRunner，無真實 Project 寫入驗證。
  - disposition：本任務禁止真實 Project 寫入；現有測試已覆蓋讀欄位、拒絕、放行與零寫入拒絕路徑。屬已揭露的整合風險，不是本卡拒絕理由。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-BACKLOG-STAGE1-e0-3c236ca73344ccff7373a0e0483d78506483fee5
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（待指派）
findings:
  - finding_id: WF-BACKLOG-STAGE1-R1-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: governance
    attribution: planner
    root_cause_id: gate-scope-tier-unspecified
    counting_eligible: false
  - finding_id: WF-BACKLOG-STAGE1-R1-002
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: governance
    attribution: external
    root_cause_id: reconcile-section6-no-standing-guard
    counting_eligible: false
  - finding_id: WF-BACKLOG-STAGE1-R1-003
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: environment
    attribution: external
    root_cause_id: mocked-only-integration-risk
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5373506315 · 2026-08-21T18:06:29Z

<!-- wf-review-event:v1 card_id=WF-BACKLOG-STAGE1 source_sha=fe296ad665cac8ed69a4f15b9d2df0931d6b26c5 attempt_id=WF-BACKLOG-STAGE1-e0-fe296ad665cac8ed69a4f15b9d2df0931d6b26c5 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-BACKLOG-STAGE1`　attempt_id：`WF-BACKLOG-STAGE1-e0-fe296ad665cac8ed69a4f15b9d2df0931d6b26c5`
- 查核者：GPT-5@Codex（需求方轉貼；無 GitHub 收據留言，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`fe296ad665cac8ed69a4f15b9d2df0931d6b26c5`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-22T02:06:27+08:00

### self_run（查核者實跑）

- `檢視 AI_WORKFLOW.md:118 的新條文`
  - 已先寫入自足規則。T2 以上必須由規劃中進 Backlog；T0／T1 直通；未知級別 fail-closed；阻塞不是合法前身
- `檢視 handoff_cmd.py:470 的 T0／T1 分支`
  - 明示「未做任何前身狀態檢查」並寫 stderr
- `重跑變異檢驗 M1–M4 並還原`
  - 四個變異均自行重跑為紅；還原後 SHA-256 與交付一致、工作樹乾淨
- `以釘死基線 b2a6d54 實測 :211／:216／:220／:222 的實際內容`
  - :216 本來就是 merge 規則不是 T2 規則，原本已錯；:220×6 原本正確、本輪指向 Reviewed-by 範例而失準；:222×2 由原本空行偶然變正確
- `pytest 於三個 SHA 各跑一次`
  - b2a6d54 為 1052 passed；R1 的 3c236ca 為 1056 passed；交付 fe296ad 為 1062 passed。R1 到 R2 的差額確為 6；把 1056 當作釘死基線則不正確
- `contract_tool_reconcile.py --check`
  - exit 0，缺口 58
- `gh run 以指定 SHA 查詢`
  - CI 成功，run 32506159794
- `檢視回放 C 段的可證偽預測`
  - 事前寫出可推翻條件（增量接近 0 即退回甲案），實測未終態 T2 卡 14 張、24.6%，顯然不是零收益
- `查驗 R1 交付 SHA 的遠端可達性`
  - 3c236ca 已無遠端 branch 或 tag 參照；本機 tag 不構成共享持久的稽核保存

### findings（3，其中 blocking 2）

- **WF-BACKLOG-STAGE1-R2-001**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`canonical-line-ref-rot`
  - evidence：doctor.py 的手寫 canonical 引用未隨插入兩行更新。尤其 6 處 AI_WORKFLOW.md:220 現指向 Reviewed-by 範例，真正的 trailer 空行規則已移到 :222；實際診斷訊息也會輸出錯誤定位。doctor.py 在本卡寫入集內。⚠️ 前提更正：以釘死基線 b2a6d54 實測，:216 本來就是 merge 規則而非 T2 規則，原本已錯、本輪未修；本輪明確造成的回歸是 :220×6，:222×2 則由空行偶然變正確。
  - disposition：更新引用，或改為穩定章節錨點。
- **WF-BACKLOG-STAGE1-R2-002**　severity=major　blocking=true　class=governance　attribution=executor　root_cause_id=`reviewed-artifact-unreachable-after-force-push`
  - evidence：R1 的交付 SHA 3c236ca 已無遠端 branch 或 tag 參照，本機 tag 不構成共享、持久的稽核保存；R1 review event 的 attempt_id 內嵌該 SHA。
  - disposition：rebase 本身符合「更新分支採 rebase 加 force-with-lease」，但不可接受其代價是舊查核對象只剩可能被 GC 的物件。需由有權者建立遠端不可變保存 ref，或需求方明示接受失去可重現性。
- **WF-BACKLOG-STAGE1-R2-003**　severity=info　blocking=false　class=governance　attribution=external　root_cause_id=`falsifiable-threshold-not-numeric`
  - evidence：回放 C 段的可推翻條件「增量接近 0」未數值化，不能當嚴格統計門檻。
  - disposition：不構成阻擋；C 段整體判定為有鑑別力、通過。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-BACKLOG-STAGE1-e0-fe296ad665cac8ed69a4f15b9d2df0931d6b26c5
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（待指派）
findings:
  - finding_id: WF-BACKLOG-STAGE1-R2-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: canonical-line-ref-rot
    counting_eligible: true
  - finding_id: WF-BACKLOG-STAGE1-R2-002
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: governance
    attribution: executor
    root_cause_id: reviewed-artifact-unreachable-after-force-push
    counting_eligible: false
  - finding_id: WF-BACKLOG-STAGE1-R2-003
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: governance
    attribution: external
    root_cause_id: falsifiable-threshold-not-numeric
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5377313738 · 2026-08-22T02:15:04Z

<!-- wf-review-event:v1 card_id=WF-BACKLOG-STAGE1 source_sha=94dc3c323c0e98bad939d954bc2b5fe3902e982a attempt_id=WF-BACKLOG-STAGE1-e0-94dc3c323c0e98bad939d954bc2b5fe3902e982a -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-BACKLOG-STAGE1`　attempt_id：`WF-BACKLOG-STAGE1-e0-94dc3c323c0e98bad939d954bc2b5fe3902e982a`
- 查核者：GPT-5@Codex（需求方轉貼；無 GitHub 收據留言，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`94dc3c323c0e98bad939d954bc2b5fe3902e982a`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-22T10:15:02+08:00

### self_run（查核者實跑）

- `重跑七個變異矩陣`
  - M1 至 M5 皆失敗（KILLED）、M6 與 M7 存活，符合預期。M7 的語意反轉漏網已明載且實測為真
- `在基線 b2a6d54 複核 :211／:216／:222 與 doctor.py:664 的區間引用`
  - :222 是空行；:211 與 :216 是同一條 T0/T1 至 T2 bullet 的範例。doctor.py:664 的區間式引用確在基線存在
- `git ls-remote --tags origin`
  - reviewed tag peeled 至 3c236ca73344ccff7373a0e0483d78506483fee5
- `git diff --name-only（兩個區間）`
  - fe296ad 至 HEAD 為 3 檔；b2a6d54 至 HEAD 為 6 檔
- `focused tests 與測試收集數對帳`
  - 4 passed；收集數基線 1052、交付 1064
- `gh run 以鎖定 SHA 查詢`
  - run 32514432605 成功，日誌為 1064 passed
- `contract_tool_reconcile.py --check`
  - exit 0，缺口 58
- `三個相關檔案 SHA-256 與 HEAD blob 比對、工作區與 trailer 檢查`
  - 三檔 SHA-256 均與 HEAD blob 相同，工作區乾淨，trailer 連續且可解析
- `逐一檢視射程外引用在本分支上的指向`
  - 13 處原本正確的行號引用失準且未修復：cleanup.py、handoff_cmd.py、WF_CLEANUP_GUARD1.md 兩處、WF_EVENT_IDEMPOTENCY1.md 七處、WF_RESOURCE_WRITESET1.md 兩處

### findings（2，其中 blocking 1）

- **WF-BACKLOG-STAGE1-R3-001**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`canonical-line-ref-rot`
  - evidence：本分支相對基線 b2a6d54 已造成 13 處原本正確的行號引用失準且未修復。它們是本分支在 §3.1 插入兩行後直接造成，不是既有瑕疵；目前全都仍指向錯誤條文。已知 13 是下界也不影響裁決。
  - disposition：不能明知合併會留下錯誤 canonical 引用。需先取得範圍授權並修復，或由需求方安排依賴修復後再合併本 SHA。
- **WF-BACKLOG-STAGE1-R3-002**　severity=info　blocking=false　class=implementation　attribution=external　root_cause_id=`anchor-guard-semantic-blind-spot`
  - evidence：M7 的語意反轉漏網（片段字串原封不動、條文語意被反轉時守衛不轉紅）已明載且實測為真。
  - disposition：R2-001 本身已閉環，此漏對「引用漂移」守衛已足夠。條文雜湊或快照只會把每次合法改文也打紅、仍無法判定語意正確，不應作為本卡必備機制。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-BACKLOG-STAGE1-e0-94dc3c323c0e98bad939d954bc2b5fe3902e982a
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（待指派）
findings:
  - finding_id: WF-BACKLOG-STAGE1-R3-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: canonical-line-ref-rot
    counting_eligible: true
  - finding_id: WF-BACKLOG-STAGE1-R3-002
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: implementation
    attribution: external
    root_cause_id: anchor-guard-semantic-blind-spot
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5377836938 · 2026-08-22T04:20:14Z

<!-- wf-review-event:v1 card_id=WF-BACKLOG-STAGE1 source_sha=729ea7f1521e8a6dcdf5a546607ac6646a70195a attempt_id=WF-BACKLOG-STAGE1-e0-729ea7f1521e8a6dcdf5a546607ac6646a70195a -->
## 查核裁決：APPROVE

- 卡：`WF-BACKLOG-STAGE1`　attempt_id：`WF-BACKLOG-STAGE1-e0-729ea7f1521e8a6dcdf5a546607ac6646a70195a`
- 查核者：GPT-5@Codex（需求方轉貼；無 GitHub 收據留言，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`729ea7f1521e8a6dcdf5a546607ac6646a70195a`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-22T12:20:13+08:00

### self_run（查核者實跑）

- `核對 HEAD 與工作區`
  - 729ea7f 完全一致；乾淨
- `python3 scripts/canonical_citation_scan.py`
  - 123 檔、0 非排除命中、exit 0
- `python3 scripts/canonical_citation_scan.py --all`
  - 唯一排除路徑仍被列出；0 非排除命中
- `測試收集數對帳`
  - 基線收集 1052、HEAD 收集 1080
- `gh run 以鎖定 SHA 查詢`
  - run 32549133164 成功，1080 passed in 32.62s
- `contract_tool_reconcile.py --check`
  - exit 0；58 缺口
- `git diff --name-only b2a6d54..HEAD`
  - 16 檔
- `五個變異並還原`
  - M1 紅（124 檔 1 命中）；M2 綠且 --all 顯示為排除項；M3 紅（123 檔 30 命中）；M4 紅（掃描器測試 4 failed）；M5 紅（ROADMAP 該行被命中）。還原後原 worktree 未改，掃描器與其測試與 ROADMAP 的 SHA-256 均與 HEAD blob 一致
- `本機掃描器測試`
  - 16 passed。⚠️ 本機完整 pytest 的終端回傳在約 26 至 33 百分比被執行環境截斷，故不宣稱本機成功；以鎖定 SHA 的 CI 完整結果為準
- `核對 daily_snapshot.sh 引用的 :138 在基線上是否已指錯`
  - 否。基線 AI_WORKFLOW.md:138 的同一 bullet 已包含「必須以每日 snapshot export 回 git 建立離線稽核副本」；該引用在基線語意正確，是本分支插入兩行後才失準

### findings（3，其中 blocking 0）

- **WF-BACKLOG-STAGE1-R6-001**　severity=minor　blocking=false　class=implementation　attribution=executor　root_cause_id=`iso-test-not-independently-load-bearing`
  - evidence：test_iso_stripping_does_not_swallow_a_section_line_ref 在 M4 仍通過：鬆散剪除已吃掉 §6:220，但同一行剩下的 ISO 時間片段仍產生冒號數字命中，掩蓋了漏報。M4 最終仍被其他測試擋下（裸節次形態與純時戳測試），故守衛有效，但該專測的說明不精確。
  - disposition：建議後續改成不含 ISO 的節次引用，或先斷言 ISO 已完整剔除。
- **WF-BACKLOG-STAGE1-R6-002**　severity=info　blocking=false　class=implementation　attribution=external　root_cause_id=`guard-scope-limits-disclosed`
  - evidence：排除集保證只對「沒有實際承載內容的死排除」成立（M3 證實刪除後立即暴露 30 項），不證明排除理由的語意正確，也無法阻止有人把壞內容故意塞進已排除產生物。同一實作的不分岔宣稱在人手以預設 root 執行與 pytest 呼叫 main() 的範圍內成立，宣稱任何情況都不可能分岔過強（root、Git 索引狀態與執行時環境仍可能不同）。
  - disposition：目前唯一排除項確為產生輸出，非阻擋。宣稱範圍應收斂為已驗證的執行條件。
- **WF-BACKLOG-STAGE1-R6-003**　severity=info　blocking=false　class=environment　attribution=external　root_cause_id=`push-ci-not-merge-tree`
  - evidence：push 事件的 CI 不代表合併樹；本次 CI 只證明交付 SHA，未證明未來合併結果。散文片段逐字性未驗與部分散文多加粗體兩項，射程、成本與驗不到的原因均明載。
  - disposition：三項皆判非阻擋。本卡目標是消除行號漂移，不是假稱驗證語意或逐字引文；CI 限制屬既有 CI 與分支保護設計。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-BACKLOG-STAGE1-e0-729ea7f1521e8a6dcdf5a546607ac6646a70195a
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（待指派）
findings:
  - finding_id: WF-BACKLOG-STAGE1-R6-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: implementation
    attribution: executor
    root_cause_id: iso-test-not-independently-load-bearing
    counting_eligible: false
  - finding_id: WF-BACKLOG-STAGE1-R6-002
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: implementation
    attribution: external
    root_cause_id: guard-scope-limits-disclosed
    counting_eligible: false
  - finding_id: WF-BACKLOG-STAGE1-R6-003
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: environment
    attribution: external
    root_cause_id: push-ci-not-merge-tree
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。
