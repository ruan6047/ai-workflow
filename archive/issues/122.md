# #122 WF-TRANSITION-TABLE-UNWRITTEN1 允許的狀態轉移表：契約明文下放給各專案，兩個專案都沒寫，而共用看板不可能有兩份
- state: closed  created: 2026-08-21T16:32:22Z  closed: 2026-08-26T12:56:08Z
- url: https://github.com/ruan6047/ai-workflow/issues/122
- comments: 3

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；改動量不大但要先做一次歸屬裁定，而裁定的依據是「一個看板服務兩個 repo」與範本下放模型的衝突，屬結構判讀不是填空。表寫出來後每一條還要逐條對照 handoff_cmd.py 的實際分支並標注有無機械執行者——那一步很容易退化成宣稱式對帳。）　查核：待指派（建議 主力型；判準是表寫的與工具實際執行的是否逐條相符、以及「有無機械執行者」欄位是不是誠實（恆真或無執行者的條目有沒有被標注，還是被包裝成看起來有檢查）。非紅線卡、無碼行為變更。⚠️ 但本卡會產出跨專案權威文件，查核者須確認它不與 AI_WORKFLOW.md §0／§3.1 或 #120 落地的閘門互相矛盾。）
- Initiative：—　spec 基線：2026-08-21 三項實查：templates/control-plane-contract.md:37-40 的 <專案實作> 佔位符、cpbl docs/CONTROL_PLANE_CONTRACT.md 四個關鍵詞命中 0、ai-workflow 無該檔；Project #4 實測 176 張分屬 cpbl 111／ai-workflow 65 @ ai-workflow main b2a6d54
- DB：db_scope=none
- 服務的原始目標：規則說哪些狀態轉移合法的時候，那句話要真的存在於某個檔案裡

## 簡介
<!-- card-brief:begin -->
裁定「允許的狀態轉移」表該住在 canonical 還是各專案，並實際寫出該表；每條轉移逐條標注今天有沒有機械執行者。**適用時機**：要判斷某個狀態轉移合不合法時；或要在某個 wfcli 動詞上加狀態閘門、需要一份可引用的依據時。⛔ 非射程：⛔ 不改 handoff 的 Log 記法與 `doctor.py` 的 UNDECIDABLE_HANDOFF（需求方 2026-08-22 裁定丙案拆成另一張卡，以本卡產出為輸入）；⛔ 不補 `assign_cmd.py:227` 終態卡可被直接拉回執行中那個洞；⛔ 不重做 WF-BACKLOG-STAGE1 已落地的逐案閘門——本卡處理的是「那張表該住在哪、由誰寫」這個結構問題。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：- **痛點**：canonical 契約範本明文要求列出「允許的狀態轉移」，**下放給各採用專案，而兩個採用專案都沒有寫**。今天沒有任何地方寫著哪些狀態轉移合法。

`templates/control-plane-contract.md:37-40` 逐字要求「列出**允許的狀態轉移**、Gate／preflight 退回、`⏸阻塞` 的 TTL、escalation checkpoint 與 `🚨已升級` 的決策 owner」，下一行是佔位符 `<專案實作>`。

實查（2026-08-21）：

- `cpbl-analytics/docs/CONTROL_PLANE_CONTRACT.md` 存在、220 行，但 `轉移`／`⏸阻塞`／`📥Backlog`／`規劃中` 四個關鍵詞**命中數全部是 0**
- `ai-workflow` **完全沒有** `docs/CONTROL_PLANE_CONTRACT.md`
- cpbl 該檔 §5「已知待決」列了 6 項，**這一項不在其中** —— 是未登記的缺口，不是已知延後項

⭐ **下放模型本身不成立**：Project #4 是**一個看板服務兩個 repo**（cpbl 111 張／ai-workflow 65 張，全 176 張），`wfcli` 也只有一份。一張共用看板不可能有兩份互相獨立的「允許的狀態轉移」表，但範本的 `<專案實作>` 佔位符預設它可以。

⚠️ **這件事現在正在造成實害**：`ai-workflow#120 WF-BACKLOG-STAGE1` 正在寫**史上第一條機械狀態轉移規則**（`handoff --next-stage backlog` 的前驅狀態閘門），而它被寫進 canonical 共用的 `handoff_cmd.py`。R1 跨家族查核已就此開出 blocking finding（級別適用範圍超出 canonical 明文），需求方裁定丙案並要求把規則補寫進 `AI_WORKFLOW.md`。**那是逐案補洞；本卡處理的是「這張表該住在哪、由誰寫」這個結構問題。**

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:templates/control-plane-contract.md",
    "file:AI_WORKFLOW.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 1. 裁定「允許的狀態轉移」表的歸屬：留在 `<專案實作>`、上收 canonical、或兩層（canonical 定通則＋專案宣告差異）。裁定須附理由，並直接回應「一個看板兩個 repo」這個事實。
2. 依裁定結果實際寫出該表，涵蓋範本 :37 點名的五項：允許的狀態轉移、Gate／preflight 退回、`⏸阻塞` 的 TTL、escalation checkpoint、`🚨已升級` 的決策 owner。
3. 表中每一條轉移須標注它今天**有沒有機械執行者**。恆真或無執行者的條目必須明文標注，⛔ 不得留下看起來有檢查的空殼（`docs/ROADMAP.md` §1）。
4. ⛔ **對帳基準已於 2026-08-26 由需求方更新，⛔ 不再是 `#120`。** 表寫的與 `handoff_cmd.py` **實際執行的**若有落差，逐項列出並標明哪一邊要改。⚠️ **基準改為 `6148bd4495fd3134f0e42db926b558a02761fda8`**（今日 main）——理由：本條寫於 2026-08-22，而 `WF-STAGE-PITFALL-LIST1`（`aiwf#148`）已於 08-26 大改該檔（新增踩坑離開閘門、`ensure_fields` 由前置段搬到閘門後、Log 行新增 `；階段 X；踩坑回應 N 族`）⇒ 照 `#120` 對帳會對到一個不存在的現實。
5. 若裁定為上收 canonical，須說明 `templates/control-plane-contract.md:37` 的 `<專案實作>` 佔位符要怎麼處置。
6. ⭐ **表必須建立在「`handoff` 的 Log 已經記得下階段」這個 2026-08-26 才成立的新事實上。** `aiwf#148` 的 A5 已落地：Log 行現為 `…；階段 <離開側>；踩坑回應 N 族（…）；證據 …`。⚠️ 而**只做了一半**——`doctor.UNDECIDABLE_HANDOFF = "handoff_status_not_in_log"` 仍在，2026-08-26 實測仍有 **172 張**判它（`handoff` 記的是**階段**、⛔ 不是**交付狀態**，兩者是不同的軸）。⇒ 本卡的表須明文區分這兩軸，⛔ 不得把「階段已可反推」誤讀為「狀態轉移已可重建」。
7. ⚠️ **裁定 2 指名要「另開一張」的承接卡至今未註冊。** 該卡逐字射程是「讓 `handoff` 的 Log 記得下 stage、翻掉 `doctor.UNDECIDABLE_HANDOFF` 及其守衛」，並以**本卡產出為輸入**。⭐ 而前半已被 `aiwf#148` 於本卡產出存在**之前**做掉 ⇒ 順序與裁定 2 相反。⇒ 本卡交付須明文交代：後半（翻掉 `UNDECIDABLE_HANDOFF`）由誰承接，以及本卡的表要不要因此改變形狀。⛔ 本卡不自行開那張卡。

## 驗證

- [ ] - `grep -c` 證明 `轉移`／`⏸阻塞`／`📥Backlog`／`規劃中` 在目標檔的命中數由 0 變為非 0
- 表內每一條轉移逐條對照 `cli/src/wf_cli/commands/handoff_cmd.py` 的實際分支，落差逐項列出（不得只寫「已對帳」）
- 「有無機械執行者」欄位的判定須可重現：能指出是哪一行程式在檢查，或明說沒有
- `pytest` 與 `contract_tool_reconcile.py --check` 不因本卡退步（exit code 不得接管線取）

## Log

- 2026-08-22T00:32:21+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-22T13:23:52+08:00 amend by wf-cli（op 132d4d91）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:templates/control-plane-contract.md", "file:docs/CONTROL_PLANE_CONTRACT.md" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:templates/control-plane-contract.md」；理由 修正 PM 開卡時的錯誤宣告。原宣告含 file:docs/CONTROL_PLANE_CONTRACT.md，但本卡在 ai-workflow，裸 docs/ 路徑讀作 ai-workflow，而該 repo 沒有這個檔（實查 ls 回 No such file or directory）——那個檔在 cpbl-analytics。wfcli 只比對字串、不驗證檔案存在，故該宣告靜默通過了。 ⛔ 不改用跨 repo 形式。實測 amend --dry-run 接受 file:ruan6047/cpbl-analytics:docs/CONTROL_PLANE_CONTRACT.md 的語法，但 resources.py 的 find_conflicts 逐字寫「完全相同字串才算撞（不做路徑前綴模糊比對，避免誤判）」——cpbl 那側的卡宣告的是裸 file:docs/CONTROL_PLANE_CONTRACT.md，兩個字串不同、永遠不會撞。⇒ 跨 repo 宣告語法上成立但保護為零，是一個看起來有宣告的空殼，不寫。 故本次只留 ai-workflow 側真正有保護的那一個。⚠️ cpbl 側是否要動、以及要不要另開 cpbl 的卡持有該檔的宣告，屬本卡規劃期要裁斷的內容之一（本卡的核心問題正是「那張表該住在 canonical 還是各專案」），不在開卡時預先決定。 同時記錄本卡的流程瑕疵：本卡 2026-08-22T00:32 開卡即落 📥Backlog，Log 只有 open 一行，未經任何閘門。成因是 card.py 的 open 預設值缺陷（承接卡 ai-workflow#118 已交付 R2、在 🔍待查核）。而本卡級別 T3，canonical AI_WORKFLOW.md §3 逐字要求「T3／T4、大卡、跨系統與不可逆變更先完成 Discovery Gate」，§3.1 另要求 T3 經核心痛點三問並由需求方批註放行後才進 📥Backlog——兩者本卡都跳過了。需求方 2026-08-22 裁定退回重走，先進 🔬研究中 做 Discovery。。
- 2026-08-22T13:24:51+08:00 handoff by wf-cli → owner ruan6047（Discovery Gate）；iteration 0；SHA 2dcab601c0c9e0500524a717697208bc117d9f5a；證據 退回 💡需求：本卡 2026-08-22T00:32 開卡即落 📥Backlog，Log 只有 open 一行、未經任何閘門，成因是 card.py 的 open 預設值缺陷（承接卡 ai-workflow#118 已交付 R2、在 🔍待查核）。本卡級別 T3，canonical AI_WORKFLOW.md §3 逐字要求「T3／T4、大卡、跨系統與不可逆變更先完成 Discovery Gate」，§3.1 另要求 T3 經核心痛點三問並由需求方批註放行後才進 📥Backlog——兩者本卡都跳過了。需求方 2026-08-22 裁定退回重走。資源宣告的錯誤已於 amend op 132d4d91 一併修正。。
- 2026-08-22T13:25:15+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子代理，唯讀 Discovery）；iteration 0；SHA 2dcab601c0c9e0500524a717697208bc117d9f5a；證據 需求方 2026-08-22 裁定進 Discovery。⭐ 這是本 repo 首次實際使用 🔬研究中——該狀態自 ae8f741（#102，2026-08-18）加入詞彙表以來板上掛 0 張。本卡級別 T3 且屬跨系統治理問題（一個 Project 看板服務兩個 repo，而契約把允許的狀態轉移表下放給各專案），故依 canonical §3 Discovery 為必要。派唯讀子代理做調查，零檔案改動、不寫狀態面；Discovery brief 交需求方，放行是需求方的動作。⚠️ 已知 cpbl-analytics 的 scripts/roadmap_lines.py 的 GATE_BY_STATUS 缺 🔬研究中（承接卡 cpbl-analytics#165，因資源撞 #143 排在其後），故本卡進入該狀態期間，cpbl 的 §3 區塊重生會 fail closed。⛔ 本卡不因此改用別的狀態——那會把工具缺陷變成流程扭曲；#165 修好前該重生指令請勿執行。。
- 2026-08-22T16:35:25+08:00 handoff by wf-cli → owner ruan6047（排隊中：待 cpbl#166 與主站卡）；iteration 0；SHA 251e211d8c3149a22a7ada483638b5fa884c7ed8；證據 需求方 2026-08-22 就 Discovery brief 逐項裁定。本卡留在 🔬研究中，依裁定 3 排在 cpbl-analytics#166 與主站 CI 覆蓋卡之後，暫不進規劃期。

裁定 1（服務哪個目標）：目標 2「可稽核的內容」，判準逐字為「事後能從留痕重建做了什麼、依據是什麼」。⛔ 不是 Discovery 建議的目標 3。理由：PM 獨立重現兩個數字——175 張有 Log 的卡中 159 張（91%）判 undecidable，其中 158 張因 handoff_status_not_in_log，即事後重建不出狀態轉移；114 張有 assign 的卡中 96 張（84%）在第一次 assign 前零 handoff。⇒ 目標 2 的判準在 91% 的卡上不成立，那是量得出來的缺口而非「有最好非必要」。而 ROADMAP §0 的檢查 3「現在有人因它受害嗎」只適用目標 3，本卡不適用。⚠️ PM 量測時另有一項自陳作廢：報告的 16 張 drift 是因為餵了固定期望值 🔨執行中 而非逐張真實欄位值，屬量法造成的假 drift，該數字不得使用；91% 那項不受影響，因該判定與期望值無關。

⭐ 裁定 1 的代價已明示並接受：本卡不會關掉 assign 那個口。它產出的是一張說得出合法性的表，閘門屬那批 WF-CLI-* 動詞卡的事，本卡是它們的輸入。

裁定 2（要不要含留痕改造）：採丙——拆兩張。本卡只產出轉移表；「讓 handoff 的 Log 記得下 stage、翻掉 doctor.UNDECIDABLE_HANDOFF 及其守衛」另開一張，以本卡產出為輸入。

⭐ 理由不是「乙太貴」。PM 研究後發現 ai-workflow#118 R3 剛 merge 的那條測試 test_handoff_log_line_never_carries_the_status_it_wrote 並非禁令而是前提守衛——其 docstring 首句逐字「UNDECIDABLE_HANDOFF 的前提：handoff 寫進欄位的狀態，復原不出來」，且三條斷言各自標明會被什麼推翻（written_status not in line 在寫入端開始寫狀態值時紅、stage not in line 在改記 next-stage 鍵時紅）。⇒ 留痕改造會讓它轉紅，那正是守衛在做該做的事，不是違反它。依賴面實測僅 12 處且全在 cli/ 內（handoff_cmd.py 1、doctor.py 4、test_commands_mocked.py 4、test_doctor.py 3），無跨 repo、無文件契約依賴。

⇒ 拆兩張的真正理由是查核可切性：表的判準是「說得出合法性」、留痕的判準是「重建得出發生什麼」，⚠️ 一張卡塞兩個判準就是 ai-workflow#120 跑六輪的形狀。且順序上表必須先有——要決定 Log 該記什麼欄位，得先知道有哪些轉移，反過來做會憑感覺選欄位。

⭐ 裁定後解除的前提：Discovery 的假設 D「不得假設 #118 的結果」已解除。ai-workflow#118 於 2026-08-22 經三輪查核 APPROVE 並合併（merge commit 251e211，PR 127），card.py:295 現為 💡需求、doctor.py:1317 的 OPEN_INITIAL_STATUS 同步。⇒ 轉移表的起點確定為 💡需求，本卡規劃期無未決前提。⭐ 併帶效果：assign 那個口從此每次使用都留下可見痕跡——💡需求 → 🔨執行中 一眼看得出跳過三格，而舊行為下 📥Backlog → 🔨執行中 看起來正常；轉移表因此拿到能分辨合法與否的資料。

⚠️ 規劃期須納入但本次未裁的兩項：需求方 2026-08-22 的兩條流程意向（高複雜或影響較大的卡必跑 🔬研究中；🧭規劃中 必含 Design Gate）在表裡的落點，包含「今天無執行者」這個答案；以及 Discovery 實驗 F 的新發現——🏁完成 的終態卡被 assign 直接拉回 🔨執行中 得 rc=0 無任何警告，TERMINAL_STATUSES 只在比對別卡時被讀（assign_cmd.py:227），本卡終態無任何保護。。
- 2026-08-26T12:29:49+08:00 amend by wf-cli（op a40385c0）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:fdf96c03b5a8b36b64471ec7c4cd66e2f2bfb6591bcbab34ed0d3288f3d2b54f (698 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 先導批 10 張：回填 canonical AI_WORKFLOW.md §6.3 的卡片簡介。⭐ 價值主張依卡面 A10：131 張終態卡上 assign_cmd 讓資源宣告結構性失明、root_cause_id 住在 review finding 裡，簡介是三個相關性機制裡唯一還能用的那個。⛔ 未改動任何其他欄位。A5 守衛已在呼叫前拒收 str.splitlines() 認得的全部分行字元（由該函式自身導出，非手打清單）。。
- 2026-08-26T17:58:15+08:00 amend by wf-cli（op c217c31e）→ 驗收條件：原值指紋 sha256:0e06f57305d7e656c6d409f5a45b9147ae3284e0eaaac23692af69613d3ac69a (238 bytes) → 新值指紋 sha256:9c1169596135a5a6612ed9150e49d5ef579fc6600e39c21dd05dec8d878126ab (2437 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定進規劃期前更新三處：驗收第 4 條的對帳基準由 #120 改為今日 main 6148bd4（aiwf#148 已大改 handoff_cmd.py）；新增第 6 條要求表建立在「Log 已記階段」的新事實上並區分階段與交付狀態兩軸；新增第 7 條登記裁定 2 的承接卡未註冊且其前半已被 #148 反序做掉。
- 2026-08-26T17:59:09+08:00 handoff by wf-cli → owner 待指派（規劃）；iteration 0；SHA 6148bd4495fd3134f0e42db926b558a02761fda8；階段 研究；踩坑回應 8 族（已檢查 2／不適用 1／發現 5）；證據 需求方 2026-08-26 裁定進規劃期。裁定 3 的兩個排隊條件今日皆已解除：cpbl-analytics#166 OPS-CPBL-MERGE-GATE1 已 🏁完成/CLOSED、主站 CI 覆蓋卡 DEV-AIWF-MINIMAL-CI1（aiwf#48）已 🏁完成。⛔ 並更正 PM 先前兩度的錯誤說法「本卡留言 0 則、從沒動過」——Discovery 已跑完且經需求方三項逐字裁定，產出全在 Log 而非留言，那是用觀測面推論實際狀態的錯。#130 七節逐項對照通過：§6.3 簡介有且形狀通過、兩居所逐字一致；§5.1.1 服務的原始目標有值；§6.4.1 驗收與驗證已填實且無佔位符（原偵測到的 < 是驗收第 1 條引用 <專案實作> 這個範本裡真實存在的字串，屬假陽性）；Initiative 為 — 故 spec 基線非必填。開工前已 amend 三處：對帳基準由 #120 改為 6148bd4、新增第 6 條要求表建立在 Log 已記階段的新事實上並區分階段與交付狀態兩軸、新增第 7 條登記裁定 2 的承接卡未註冊。⚠️ Log 原記的兩項「規劃期須納入但本次未裁」仍有效：需求方 08-22 的兩條流程意向在表裡的落點含「今天無執行者」這個答案、以及 Discovery 實驗 F 的新發現。。
- 2026-08-26T19:19:05+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code (規劃)；分支worktree ai/opus-5/WF-TRANSITION-TABLE-UNWRITTEN1 @ /Users/ruanruan/Dev/ai-workflow/.worktrees/transition-table；交付狀態 🧭規劃中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-26T19:55:56+08:00 handoff by wf-cli → owner 待認領（跨家族查核）；iteration 0；SHA 7020cf9617a27a98dd9c838caa154ef2dd3069e7；階段 規劃；踩坑回應 8 族（已檢查 0／不適用 1／發現 7）；證據 PR #156。裁定上收 canonical（四個可複驗理由，直接回應「一個看板兩個 repo」：快照 202 張分屬 cpbl 117／aiwf 84、唯一寫入通道 wfcli 只有一份且住 canonical repo、canonical §7 委派表根本沒把狀態轉移列為專案自決、§6.4 已寫下下放失敗的機制）。產出九張表：轉移 20 列＋Gate/preflight＋⏸阻塞 TTL＋checkpoint＋🚨已升級 決策 owner＋兩項規劃期須納入＋條文對帳。驗收 3 每條以符號指認有無機械執行者，⭐ 答案大多是 ⛔ 無（五個階段狀態互轉的 else 分支不讀現值、assign 無條件寫、逃生門 --status 排在所有閘門之前且無 choices、廢止值仍寫得進去），並揭露兩個「看起來有檢查其實不是」（review 只印 stderr 後照寫）與一個「有執行者但恆不觸發」（escalation checkpoint）。驗收 4 基準確認 git diff 6148bd4 b169c242 -- handoff_cmd.py 為空；表↔碼 0 條不一致、條文↔碼 7 條逐條標歸屬。回歸：contract_tool_reconcile --check rc=0、pytest rc=0 1270 passed、replay_escalation_rules rc=0 114/114、uv lock --check rc=0、文件內複驗片段 rc=0（未涵蓋 0 個狀態、0 個 next-stage）。⚠️ 授權邊界四項：規則本體正式居所應是 AI_WORKFLOW.md 但不在宣告內（未擴權）、§7 委派表矛盾未修、cpbl 側未補差異宣告、WF-CONTROL-PLANE-TYPE-REGISTRY1 宣告同檔。踩坑清冊逐族內文全文見本證據上方的 --pitfall-report 段落與 PR #156 內文。。
- 2026-08-26T20:06:24+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 跨家族查核者（身分未自述；收據原文見 PR #156 的 issuecomment-5424996339，PM 逐字轉錄）；core_pain_resolved no；self_run 8 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-TRANSITION-TABLE-UNWRITTEN1-e0-7020cf9617a27a98dd9c838caa154ef2dd3069e7。
- 2026-08-26T20:07:44+08:00 amend by wf-cli（op ae12134f）→ 資源宣告：原值指紋 sha256:80b400c55dcc8ce98887a6b42cfd4f3e5b46f0db2aff8dedfacc89b51075de39 (171 bytes) → 新值指紋 sha256:fbe57e8e43651ebed79e0e1aff13caf52ba93fb655a5caa47b2c03a5f5b1f5b2 (78 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定擴宣告以修 R1-001：規則本體須移至唯一權威載體 AI_WORKFLOW.md，template 僅留連結與差異宣告。ADOPTION.md:23 逐字要求從該 template 建立各專案的實體檔（cpbl 那份實測 220 行確為複製），而 :25 對另一批範本逐字寫「不複製進專案 repo」⇒ 兩類分得很清楚，control-plane-contract.md 屬會被複製的那類；規劃者引為判例的 review-escalation.md 正好在不複製那份清單裡。
- 2026-08-26T20:40:30+08:00 handoff by wf-cli → owner 待認領（跨家族查核）；iteration 0；SHA 2aa2f32b37a1d8b8aa14670e8a74143153573d5e；階段 審核；踩坑回應 8 族（已檢查 1／不適用 1／發現 6）；證據 R1-001 修復送審（第 2 輪，PR #156 留言 issuecomment-5425400394）。規則本體移進 AI_WORKFLOW.md §0.2（落點三個理由：裁定與被裁定的條文必須同節、它管的軸就是 §0 定義的軸、⛔ 不放 §4.1/§7 因為那兩節是委派面而把本體擺進委派面正是本卡指出的矛盾形狀）；範本僅 +32（連結＋差異宣告＋三段就地註解）。⭐ 內容沒掉是機械證明：原區塊 291 行/35403 bytes/sha256 aaf5e649b46d…；P1 帶內容行 222、今日範本殘留 0 且同一支檢查套回 7020cf9 得 222/222 全中；P2+P3 新居所扣掉前言 18 行後逐位元等於舊區塊套上恰好三條取代（每條斷言命中恰為 1）；P5 窮舉性片段剝掉 > 前綴逐字重跑 rc=0 且兩個未涵蓋清單皆 []。「三件不要弄丟」逐項確認錨點 old/new 命中皆 1:1。§7 委派表判定不修（矛盾的一方是佔位符、§7 一直是對的那一邊；⛔ 更不該把差異宣告補進 §7 因為那欄的欄名是「專案自行決定」而差異宣告是揭露不是決定），該判斷就地寫進 §0.2 前言。回歸最終樹逐項直取未接管線：contract_tool_reconcile --check rc=0（59 同基線）、canonical_citation_scan rc=0（128 檔/命中 0）、replay_escalation_rules rc=0（114/114）、uv lock --check rc=0、pytest rc=0 1270 passed。⛔ 三項授權邊界外未動並逐項登記。踩坑清冊逐族內文見上方 --pitfall-report 段落。。
- 2026-08-26T20:53:22+08:00 review by wf-cli → APPROVE（✅通過）；查核者 跨家族查核者（身分未自述；收據原文見 PR #156 的 issuecomment-5425539439，PM 逐字轉錄）；core_pain_resolved yes；self_run 8 項；findings 0 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-TRANSITION-TABLE-UNWRITTEN1-e0-2aa2f32b37a1d8b8aa14670e8a74143153573d5e。
- 2026-08-26T20:55:51+08:00 handoff by wf-cli → owner 已合併（無部署面）；iteration 0；SHA 079c9ee3e0b9e05037c68b2a46fd5ffaeeec15fe；階段 審核；踩坑回應 8 族（已檢查 1／不適用 1／發現 6）；證據 第 2 輪查核 APPROVE（findings 0，收據原文 PR #156 的 issuecomment-5425539439）。查核者獨立重跑 P1/P2/P3（222 帶內容行在新範本殘留 0、套回 7020cf9 為 222/222、僅三項替換各命中一次且替換後逐位元相等）與 P5（未涵蓋清單皆 []），並確認 §0 序列確實在 §0.2 前方、表七 D1 直接裁定該序列僅是描述、§7 不改合理、§6.4 的引用已補成歷史語境且未見第二處同類漏同步。⭐ 分支未落後 main 且閘門 CLEAN ⇒ ⛔ 本張不需先併 main。gh pr merge 156 --merge，merge commit 079c9ee3e0b9e05037c68b2a46fd5ffaeeec15fe。合併結果上重跑：pytest 1270 passed、contract_tool_reconcile --check rc=0、canonical_citation_scan rc=0、replay_escalation_rules rc=0；並機械確認 AI_WORKFLOW.md 的「### 0.2 允許的狀態轉移」命中 1、範本的「### 2.1 允許的狀態轉移」殘留 0。⚠️ 三項授權邊界外未動並已登記（review-escalation.md §5 的引用指錯檔、CONTRACT_TOOL_RECONCILE.md 錨點漂移、§7 只列決定不列義務），查核者判定皆非阻擋。本卡為純文件變更，⛔ 無部署面。；收尾清理：已清除 worktree、本地分支、遠端分支。


## Comment 5425014655 · 2026-08-26T12:06:26Z

<!-- wf-review-event:v1 card_id=WF-TRANSITION-TABLE-UNWRITTEN1 source_sha=7020cf9617a27a98dd9c838caa154ef2dd3069e7 attempt_id=WF-TRANSITION-TABLE-UNWRITTEN1-e0-7020cf9617a27a98dd9c838caa154ef2dd3069e7 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-TRANSITION-TABLE-UNWRITTEN1`　attempt_id：`WF-TRANSITION-TABLE-UNWRITTEN1-e0-7020cf9617a27a98dd9c838caa154ef2dd3069e7`
- 查核者：跨家族查核者（身分未自述；收據原文見 PR #156 的 issuecomment-5424996339，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`7020cf9617a27a98dd9c838caa154ef2dd3069e7`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-26T20:06:24+08:00

### self_run（查核者實跑）

- `git diff b169c242 7020cf9 -- cli/src/wf_cli/commands/handoff_cmd.py`
  - rc=0
- `python3 scripts/contract_tool_reconcile.py --check`
  - rc=0（59 缺口）
- `cd cli && uv run pytest -q`
  - rc=0（1270 passed）
- `python3 scripts/replay_escalation_rules.py`
  - rc=0（114/114）
- `cd cli && uv lock --check`
  - rc=0
- `表一窮舉片段逐字執行`
  - rc=0（兩個未涵蓋清單皆 []）
- `快照計數複驗`
  - 202 張：cpbl 117／ai-workflow 84／DraftIssue 1
- `cpbl 3b470d70 四詞掃描`
  - 0 命中

### findings（1，其中 blocking 1）

- **WF-TRANSITION-TABLE-UNWRITTEN1-R1-001**　severity=critical　blocking=true　class=authoritative-artifact　attribution=planner　root_cause_id=`canonical-rule-placed-in-a-copied-template`
  - evidence：狀態表雖宣稱上收 canonical，實際卻放在採用流程會**直接複製**的 template。`ADOPTION.md:23` 逐字要求「從 templates/control-plane-contract.md 建立 <專案>/docs/CONTROL_PLANE_CONTRACT.md」⇒ 完整 §2.1 會形成第二份可漂移的規則，直接違反「專案只保留連結 stub、不複製全文」。⭐ PM 獨立複驗並補三項：(1) cpbl 的 docs/CONTROL_PLANE_CONTRACT.md 實測 **220 行**、開頭是自己的標題與內文 ⇒ 確實是複製的實體檔而非連結；(2) `ADOPTION.md:25` 對另一批範本逐字寫「（使用時組裝，**不複製進專案 repo**）」⇒ repo 自己把兩類分得很清楚，而 control-plane-contract.md 明確屬於會被複製的那類；(3) ⛔ 規劃者引為判例的 templates/review-escalation.md **正好在 :25 那句不複製的清單裡** ⇒ 判例引反了。禁令出處：AGENTS.md:9、AI_WORKFLOW.md:596／:602。
  - disposition：將規則移至唯一權威載體，template 僅保留連結與差異宣告。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-TRANSITION-TABLE-UNWRITTEN1-e0-7020cf9617a27a98dd9c838caa154ef2dd3069e7
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: no
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待認領（跨家族查核）
findings:
  - finding_id: WF-TRANSITION-TABLE-UNWRITTEN1-R1-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: planner
    root_cause_id: canonical-rule-placed-in-a-copied-template
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5425588969 · 2026-08-26T12:53:24Z

<!-- wf-review-event:v1 card_id=WF-TRANSITION-TABLE-UNWRITTEN1 source_sha=2aa2f32b37a1d8b8aa14670e8a74143153573d5e attempt_id=WF-TRANSITION-TABLE-UNWRITTEN1-e0-2aa2f32b37a1d8b8aa14670e8a74143153573d5e -->
## 查核裁決：APPROVE

- 卡：`WF-TRANSITION-TABLE-UNWRITTEN1`　attempt_id：`WF-TRANSITION-TABLE-UNWRITTEN1-e0-2aa2f32b37a1d8b8aa14670e8a74143153573d5e`
- 查核者：跨家族查核者（身分未自述；收據原文見 PR #156 的 issuecomment-5425539439，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`2aa2f32b37a1d8b8aa14670e8a74143153573d5e`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-26T20:53:22+08:00

### self_run（查核者實跑）

- `git diff --stat b169c242 2aa2f32`
  - rc=0；AI_WORKFLOW.md +321、templates/control-plane-contract.md +32
- `P1/P2/P3：以 git 取出 7020cf9 原區塊、與目前兩檔內容 Python 逐位元比對`
  - rc=0；原區塊 291 行／35,403 bytes／sha256 aaf5e649b46d48a62d4b64c355999bb7b8123a87d715d0611e1219917aa47213；222 個帶內容行在新 template 殘留 0、在 7020cf9 為 222/222；僅三項宣告替換、各命中一次，替換後逐位元相等
- `P5：自 AI_WORKFLOW.md §0.2 擷取窮舉片段、剝掉 '> ' 後逐字執行`
  - rc=0；未涵蓋的狀態: []、未涵蓋的 next-stage: []
- `python3 scripts/contract_tool_reconcile.py --check`
  - rc=0；59 缺口
- `python3 scripts/canonical_citation_scan.py`
  - rc=0；128 檔、命中 0
- `python3 scripts/replay_escalation_rules.py`
  - rc=0；114/114
- `cd cli && uv lock --check；cd cli && uv run pytest -q`
  - rc=0；rc=0、1270 passed
- `git diff --exit-code 6148bd4 b169c242 -- cli/src/wf_cli/commands/handoff_cmd.py；git diff --check b169c242 2aa2f32`
  - rc=0；rc=0

### findings（0，其中 blocking 0）

- （無）

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-TRANSITION-TABLE-UNWRITTEN1-e0-2aa2f32b37a1d8b8aa14670e8a74143153573d5e
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待認領（跨家族查核）
findings: []
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5433927435 · 2026-08-27T03:18:48Z

## ⛔ 本卡的交付在 canonical 裡留下兩處壞引用，今日已腐爛

本卡的交付 commit `57bff9f`（PR #156，主旨 `docs(control-plane): pull the state-transition table up to canonical and write it out`）在 `AI_WORKFLOW.md` 寫下兩處引用，2026-08-27 實測（基線 `764a59ff`）**兩處都是壞的**。

### 缺陷一：`AI_WORKFLOW.md:392` 指向一個空行

該行逐字（表二「Plan Gate／spec 基線」列）：

> `checkpoint_cmd.run_contract_baseline` 的 `if history.baseline_count:` → `return 2`（one-shot cutover，`review-escalation.md:276`）

實測 `templates/review-escalation.md` 的 **第 276 行是空的**。

⇒ ⛔ 讀者照它去查會**看到空行、找不到依據**。該檔談 `contract-baseline` cutover 的段落實際在 `:97`／`:195`／`:277` 附近（§5 末段）。

**建議**：改為指**節次**（`review-escalation.md` §5 末段）或該段的**逐字片段**，⛔ 不用行號 —— 依 canonical 自己的紀律「**本表的壽命以年計，行號的壽命以次計**」。

### 缺陷二：`AI_WORKFLOW.md:325` 逐字轉引了一句今日為假的話

該行是 blockquote，逐字轉引 `AI_WORKFLOW.md:85-86`：

> `:511`／`:513` 今日已分別指到 `:532`／`:535`，⛔ 而宣稱本身仍成立 ⇒ **腐爛的是引用形態不是判斷**

⛔ 而 `:532`／`:535` 今日與它描述的東西**無關**（實測 `:532` 是 `from_status = pitfalls.status_to_phase(...)`、`:535` 是它的 `if`；它描述的 `if args.status:` 在 **695**、release 閘門在 **697**）。

⚠️ **原句屬 `aiwf#150`**（已於 `issuecomment-5433923349` 具名），⭐ **但本卡是第二居所**——修來源不會自動修這裡，⇒ **兩處都要改**。

⭐ 這一筆的形態值得單獨記：**逐字轉引會把來源的過期複製一份**，而且轉引處通常不會被來源卡的修正掃到。

### ⛔ 我沒有代改

canonical 的變更需要卡與查核。本則只把事實放回它的來源卡上。

---

⚠️ 附帶說明：這是我（PM）在 `aiwf#146` 的第五輪研究中量到的。⭐ 需求方逐字指示「**不要為以前舊卡的問題找通則，應該是請問題卡修正**」⇒ 故 ⛔ 不造守衛、⛔ 不進 Backlog，改在此具名。

