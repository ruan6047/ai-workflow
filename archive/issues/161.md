# #161 WF-BLOCK-VERSION-REGRESSION1 升 BLOCK_VERSION 會讓既有 review 事件全部讀不回，而今天沒有測試會轉紅
- state: closed  created: 2026-08-27T13:47:52Z  closed: 2026-08-27T21:05:31Z
- url: https://github.com/ruan6047/ai-workflow/issues/161
- comments: 12

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；要讀懂 escalation_facts_from_body 的三種區塊語意並以真實既有事件建語料；⛔ 非單純新增一條斷言，但語意影響收斂在單一測試檔內。）　查核：待指派（建議 主力型；查核要判「這條測試真的會在升版時轉紅」而非只驗它今天綠——即要驗變異檢驗那一半；⛔ 非紅線（唯讀測試、零生產碼改動），毋須跨家族。）
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：ROADMAP §0 目標 1「防止低級事故」——判準逐字「有機械執行者會擋下它」。⇒ 檢查須落在 CI 會跑的測試上，⛔ 不是條文或註解。

## 簡介
<!-- card-brief:begin -->
為 review.BLOCK_VERSION 加一條會在升版時轉紅的回歸測試。**適用時機**：要動 BLOCK_VERSION、或要判斷某個 facts/checkpoint/contract-baseline 區塊的讀回相容性時。⛔ 非射程：不改 review.py 或任何生產碼；⛔ 不實作 v2 或任何升版路徑；⛔ 不處理既有事件的內容正確性（那是 aiwf#138 的射程）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：`review.BLOCK_VERSION` 今天由三種區塊共用（`wf_escalation_facts`／`wf_escalation_checkpoint`／`wf_contract_baseline`），任何人把它升成別的值，**看板上既有的 review 事件會全部讀不回**——實測（PM 於基線 `60471f0d` 的 detached worktree）：把 `v1` 改成 `v2` 之後，`escalation_facts_from_body` 對既有事件讀得回的則數歸零。⚠️ ⛔ **母體數字刻意不寫**：它每天在長（同日兩次量測即 62→63、69+50=119 三個值），量法見驗收 A1。⛔ **而今天沒有任何測試會擋住這件事**：全套 **1309** 條在該常數被改成 `v2` 後是 **2 failed／1307 passed**，⚠️ **而那 2 條是寫入端字面斷言**（`assert "wf_escalation_checkpoint: v1" in body`）——升版的人看到的訊息就是「把字面改成 v2」，⛔ 對既有事件一個字都沒說；且**完全沒涵蓋 `wf_escalation_facts`**，那正是絕大多數既有事件走的那一種。⇒ **升版會讓兩條寫入端斷言轉紅，而補它們的方式會讓人以為修好了。** ⚠️ 三處比較的形態⛔ **不一致**：`escalation_facts_from_body` 與 `checkpoint_facts_from_body` 是 `!= BLOCK_VERSION`，而 `body_has_contract_baseline` 是 `== BLOCK_VERSION` ⇒ 驗收 A2 若只導出 `!=` 會漏掉第三處。⛔ **本卡無「危險已被前例審過」的旁證**：先前引用的 `aiwf#35` 管的是 lifecycle 事件的 **marker 版本**（標題逐字「v1 鍵集合封閉，且六個動詞裡只有 review 有 marker」），與 `BLOCK_VERSION` 是**兩個不同的常數** ⇒ 該引用已刪。⇒ 本卡的排程依據**完全落在需求方裁量**上（同 `aiwf#146` 的 A18 形狀）。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/tests/test_review.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] **A1 ⭐ 判準是「關係」，⛔ 不是數字。** 交付**不得**把任何母體數字（事件則數、區塊種數）寫成卡面或測試裡的常數。測試須在跑的當下**從真實看板自行導出**語料，斷言的是三條關係：(1) 現況下每一則帶 marker 且含 facts 區塊的既有事件**都讀得回**；(2) 把 `BLOCK_VERSION` 換成任何其他值之後，**讀得回的則數為 0**；(3) 導出的母體**非空**（⛔ 否則 (1)(2) 都是空真）。**什麼會推翻它**：測試裡出現任何寫死的母體大小，或母體為空時測試仍綠。⚠️ 依據：PM 於 2026-08-27 量到的 111/111 → 0/111 是**當日快照**，其量測腳本落在 session scratchpad ⇒ 會消失，⛔ 不得被引為定值或可複驗來源。
- [ ] **A2 ⛔ 三種區塊的清單須由碼機械導出，⛔ 不得手打。** `BLOCK_VERSION` 今天管 `wf_escalation_facts`／`wf_escalation_checkpoint`／`wf_contract_baseline` 三種，⚠️⚠️ **2026-08-27 更正：判準⛔ 不是「`!= BLOCK_VERSION` 的比較處」**——PM 複驗 `review.py`，三處的形態**不一致**：`escalation_facts_from_body` 與 `checkpoint_facts_from_body` 是 `!=`，而 `body_has_contract_baseline` 是 **`== BLOCK_VERSION`** ⇒ 照原字面導出**會漏掉第三處**。⇒ 正確判準是「**任何一處把 `BLOCK_VERSION` 拿來做相等性比較的地方**」（`ast.Compare` 且 operator ∈ {`Eq`, `NotEq`}），⛔ 不限 `!=`。交付須以 AST 或等價方式導出「有幾處比較它」並在測試內斷言，**⛔ 不得把 3 寫死**。**什麼會推翻它**：日後新增第四種區塊而測試沒有轉紅。
- [ ] **A3 ⛔ 零生產碼改動。** 本卡只新增 `cli/tests/test_review.py` 的測試，⛔ 不改 `review.py`、⛔ 不改 `validation.py`、⛔ 不實作 v2 或任何升版路徑、⛔ 不改任何既有測試的斷言。**什麼會推翻它**：`git diff --name-only <merge-base> HEAD` 出現宣告以外的檔，或 `cli/src/` 下有任何一行改動。⚠️ 唯一宣告資源是 `file:cli/tests/test_review.py`。
- [ ] **A4 ⭐ 變異檢驗必做，⛔ 這是本卡唯一有價值的部分。** 只驗「今天綠」是零資訊——`BLOCK_VERSION` 今天沒被動過，任何測試都會綠。交付須證明它**會在該紅的時候紅**：對 `review.py` 內每一處 `!= BLOCK_VERSION` 的比較**逐處移除**（monkeypatch 或原始碼變異皆可，⛔ 但不得 commit 那個變異），證明測試**逐處都轉紅**。**什麼會推翻它**：任一處被移除而測試仍綠 ⇒ 那一處不在測試射程內，涵蓋宣稱須逐字收窄。
- [ ] **A5 ⚠️ 母體漂移聲明必須在測試內、⛔ 不是在報告裡。** 語料取自活看板 ⇒ 每天不同。測試 docstring 須逐字寫明：母體如何導出、為什麼不釘數字、以及「這條測試斷言的是關係不是規模」。⛔ 交付報告裡的任何數字須附「量在哪顆 SHA、哪個時點」，⛔ 無錨定值一律視為未驗。
- [ ] **A6 ⚠️ 排程依據是需求方裁量，⛔ 不是條文自動導出——逐字登記以免被誤讀。** ROADMAP §0 開卡前檢查第 3 條逐字「現在有人因它受害嗎？沒有就進 Backlog，不排程」。本卡照字面**過不了**：⛔ **今日無人受害** —— `BLOCK_VERSION` 從未被升過版，故該風險是 POTENTIAL、⛔ **非 REALIZED**。⚠️⚠️ **2026-08-27 更正（查核 finding `-R1-03`，`attribution: planner`）**：本條原以 `aiwf#35` 作為「危險已被設計過也被審過」的排程旁證，⛔ **那個引用已被需求方裁定刪除**（`issuecomment-5440813196`）—— `aiwf#35` 管的是 lifecycle 事件的 **marker 版本**，與 `BLOCK_VERSION` 是**兩個不同的常數**。⇒ 本卡**沒有任何「危險已被前例審過」的旁證**。⚠️ PM 於該裁定中已更正核心痛點與 A2，⛔ **漏了本條**，造成同一張卡面同時存在兩句相反的話達三小時。⇒ 需求方 2026-08-27 裁量直接排程，理由逐字：**本卡是 T1、單檔測試新增、零生產碼改動，排程成本約等於一次 CI**，而 §0 第 3 條的用意是擋「排程成本高於收益」的卡。⛔ **不得由本卡推出「成本低就可以繞過第 3 道閘門」的通則**——那須另行裁定。

## 驗證

- [ ] **V1 現況全數讀得回。** 從活看板導出全部「帶 `wf-review-event` 標記且含 facts 區塊」的既有事件，逐則以 `escalation_facts_from_body` 解析，**全數讀得回**且母體非空。附導出指令與當次母體大小（⛔ 大小只作為當次紀錄，⛔ 不進斷言）。**什麼會推翻它**：任一則讀不回，或母體為 0。
- [ ] **V2 ⭐ 換掉常數後讀得回 0。** 同一批語料，把 `BLOCK_VERSION` 換成另一個值後重跑，**讀得回的則數為 0**。⛔ 只驗 V1 是零資訊——它在守衛不存在時也會綠。**什麼會推翻它**：換值後仍有任何一則讀得回 ⇒ 有一條讀取路徑沒有走版本檢查，須逐字登記。
- [ ] **V3 ⭐⭐ 逐處變異負控。** 對 A2 導出的每一處 `!= BLOCK_VERSION` 比較，**逐處**移除後重跑本測試，逐處貼出「該處被移除 ⇒ 測試紅」的輸出。⛔ 只跑一處或只跑總體不算。**什麼會推翻它**：任一處移除後測試仍綠。
- [ ] **V4 回歸不退化。** `cd cli && uv run pytest -q` rc=0 且通過數 ≥ merge-base 的通過數；`uv lock --check`／`replay_escalation_rules.py`／`canonical_citation_scan.py`／`contract_tool_reconcile.py --check` 四項 rc 全 0。⛔ **不接管線**（`| tail` 會把 `$?` 換成 tail 的），rc 分開跑並逐項貼，且註明量在哪顆 SHA。
- [ ] **V5 ⛔ 射程誠實。** 交付須逐字寫出**本測試不涵蓋什麼**：它只驗「版本不符時讀不回」，⛔ **不驗**既有事件的內容正確性（那是 `aiwf#138` 射程）、⛔ **不驗**升版之後的遷移路徑（本 repo 今日無 v2 實作）、⛔ **不驗**除 `escalation_facts_from_body` 以外的讀取端。**什麼會推翻它**：交付出現「相容性已保證」這類未收窄的宣稱。

## Log

- 2026-08-27T21:47:50+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-27T21:53:24+08:00 amend by wf-cli（op 838484ba）→ 核心痛點：原值「**痛點**： 今天由三種區塊共用（／／， 內三處 ），任何人把它升成 ，看板上**111 則帶 marker 的既有 review 事件會全部讀不回**——實測：現況 讀得回 111/111，把常數改成 後讀得回 **0/111**。⛔ **而今天沒有任何測試會因此轉紅**： 全套 1439 條在該常數被改動後仍全綠（未驗，見驗證 V2）。⚠️ 這不是假設性風險—— 就是「marker v2 升版策略」那張卡，其路由行逐字「查核重點在**升版策略是否會使既有卡停機**」⇒ 有人設計過 v2 且該危險被明確審過，只是 v2 從未實作。⇒ 今天的狀態是「危險被知道、被審過、⛔ 但沒有機械執行者」。」→ 新值「`review.BLOCK_VERSION` 今天由三種區塊共用（`wf_escalation_facts`／`wf_escalation_checkpoint`／`wf_contract_baseline`，`review.py` 內三處 `!= BLOCK_VERSION: return None`），任何人把它升成 `v2`，看板上 **111 則帶 marker 的既有 review 事件會全部讀不回** —— 實測：現況 `escalation_facts_from_body` 讀得回 111/111，把常數改成 `v2` 後讀得回 **0/111**。⛔ **而今天沒有任何測試會因此轉紅**：`cli/` 全套 1439 條在該常數被改動後仍全綠（⚠️ 該項未驗，見驗證 V2）。⚠️ 這不是假設性風險 —— `aiwf#35` 就是「marker v2 升版策略」那張卡，其路由行逐字「查核重點在**升版策略是否會使既有卡停機**」⇒ 有人設計過 v2 且該危險被明確審過，只是 v2 從未實作。⇒ 今天的狀態是「危險被知道、被審過、⛔ 但沒有機械執行者」。」（⚠️ 全文：totalCount=0（首寫，平台無前一版））；理由 PM 的 shell 引號錯誤造成核心痛點欄位損壞（反引號被 zsh 當成命令替換執行，識別符全被替換成空字串，且 **痛點**： 前綴重複兩次）；需求方授權以原文修復，⛔ 射程一個字未改；授權 依需求方 ruan6047 於 https://github.com/ruan6047/ai-workflow/issues/161#issuecomment-5440137820 的裁定（已核對：該 URL 指向本卡 issue 的既存留言，且其 GitHub author 欄逐字等於卡面「需求：」欄。本指令不讀取留言內文或操作者身分，故不判定留言內容是否構成裁定——上句「裁定」是操作者的宣告，不是本指令查得的事實——亦不區分「需求方本人張貼」與「他人代擬代貼」）。
- 2026-08-27T22:00:03+08:00 amend by wf-cli（op dce0b603）→ 驗收條件：原值指紋 sha256:268b4facf0d0fd887895f6e57a0cdd3b1af9115e6fa1e969fd3a9fcc18405f66 (41 bytes) → 新值指紋 sha256:b28fb281af063a2c779d43baac81c37893c39e193619c2beb3878b35dc0ff149 (3480 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 填實驗收條件與驗證（open 時未帶）。⭐ 判準刻意寫成「關係」不寫數字：PM 於 2026-08-27 量到的 111/111 → 0/111 是當日快照，其腳本落在 session scratchpad 會消失 ⇒ 執行者須自行從活看板重導出母體。A4/V3 的逐處變異負控是本卡唯一有價值的部分——只驗今天綠是零資訊。A6 逐字登記排程依據是需求方裁量而非條文自動導出（本卡照 §0 第 3 條字面過不了，NEAR_MISS 非 REALIZED）。。
- 2026-08-27T22:00:03+08:00 amend by wf-cli（op dce0b603）→ 驗證：原值指紋 sha256:90fbd8cfc6fb7de40197d7b06994d08cc624908b02039602d773fcbeb65bed42 (44 bytes) → 新值指紋 sha256:deb5d479464739db8b17e50460b4b55303dba4d31973ec59a25148607b50fcc9 (1794 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 填實驗收條件與驗證（open 時未帶）。⭐ 判準刻意寫成「關係」不寫數字：PM 於 2026-08-27 量到的 111/111 → 0/111 是當日快照，其腳本落在 session scratchpad 會消失 ⇒ 執行者須自行從活看板重導出母體。A4/V3 的逐處變異負控是本卡唯一有價值的部分——只驗今天綠是零資訊。A6 逐字登記排程依據是需求方裁量而非條文自動導出（本卡照 §0 第 3 條字面過不了，NEAR_MISS 非 REALIZED）。。
- 2026-08-27T22:01:08+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree ai/opus-5/WF-BLOCK-VERSION-REGRESSION1 @ /Users/ruanruan/Dev/ai-workflow/.worktrees/block-version；交付狀態 🔨執行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-27T22:01:53+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 1；SHA 60471f0db64fe9149d10a322c5d5dd39c0a45610；階段 需求；踩坑回應 8 族（已檢查 2／不適用 1／發現 5）；證據 首次派工。分支 ai/opus-5/WF-BLOCK-VERSION-REGRESSION1 @ .worktrees/block-version，基線 60471f0d。唯一任務：在 cli/tests/test_review.py 新增一條會在 BLOCK_VERSION 升版時轉紅的回歸測試。⭐ 判準寫成關係不寫數字（A1），三種區塊清單由 AST 導出（A2），⛔ 零生產碼改動（A3），⭐ 逐處變異負控是本卡唯一有價值的部分（A4／V3）。排程依據見 A6：照 ROADMAP §0 第 3 條字面本卡過不了（NEAR_MISS 非 REALIZED），需求方裁量直接排程，⛔ 不得推出通則。。
- 2026-08-27T22:45:44+08:00 amend by wf-cli（op 9fbc5a86）→ 核心痛點：原值指紋 sha256:3877b6d820ce978c99fc96cf73b001819d796f474d5a333981cbac694d904e20 (906 bytes) → 新值指紋 sha256:f330faa6ed64000f9b688d7b072eebb99806c5b2603e8856115fd7e60a8e7654 (1701 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 以實測更正核心痛點四處錯誤（PM 開卡時憑印象寫、⛔ 未實測；執行者實測推翻、PM 逐處複驗）：全套是 1309 非 1439 且改成 v2 後是 2 failed 非全綠（但那 2 條是寫入端字面斷言、⛔ 完全沒涵蓋 wf_escalation_facts）；三處比較是兩處 != ＋ 一處 == 故 A2 照字面會漏第三處；111 是當日快照且已漂移故刪去不引入新定值；aiwf#35 管的是 marker 版本而非 BLOCK_VERSION 故該旁證刪除，排程依據完全落在需求方裁量；授權 依需求方 ruan6047 於 https://github.com/ruan6047/ai-workflow/issues/161#issuecomment-5440813196 的裁定（已核對：該 URL 指向本卡 issue 的既存留言，且其 GitHub author 欄逐字等於卡面「需求：」欄。本指令不讀取留言內文或操作者身分，故不判定留言內容是否構成裁定——上句「裁定」是操作者的宣告，不是本指令查得的事實——亦不區分「需求方本人張貼」與「他人代擬代貼」）。
- 2026-08-27T22:47:06+08:00 amend by wf-cli（op 5b1499ea）→ 驗收條件：原值指紋 sha256:bd81ee15ea13e01cb309157aab6cbccf4147d29131220e1a30d1b882274e223d (3504 bytes) → 新值指紋 sha256:d7003e6faec8edea7acc6563f257ec9ebf2bf42a69fd1fe804763b9f7a16f156 (3918 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 更正 A2 的導出判準：原寫「!= BLOCK_VERSION 的比較處」，而 review.py 三處形態不一致（兩處 != ＋ body_has_contract_baseline 是 ==）⇒ 照原字面會漏掉第三處。改為「任何一處把 BLOCK_VERSION 拿來做相等性比較的地方」（ast.Compare 且 operator ∈ {Eq, NotEq}）。⚠️ 執行者已在交付中自行踩到並繞過此坑（其報告逐字登記「三處比較裡只有兩處是 !=，照 A2 字面導出會漏掉 body_has_contract_baseline」），本次更正是把卡面補到與交付一致。。
- 2026-08-27T22:50:28+08:00 handoff by wf-cli → owner 待指派；iteration 1；SHA c189465fd0536fcffa476f45e75f490cbd119b0e；階段 執行；踩坑回應 13 族（已檢查 3／不適用 0／發現 10）；證據 首輪送審。分支 ai/opus-5/WF-BLOCK-VERSION-REGRESSION1 @ c189465f；基線 60471f0d。改動只有 cli/tests/test_review.py（+410 行）。⭐ 卡面核心痛點與 A2 已於送審前依需求方裁定更正四處（issuecomment-5440813196；amend op 9fbc5a86 與 5b1499ea），全部是 PM 開卡時憑印象寫、由執行者實測推翻。執行者的 22 項失誤與未驗清單逐項逐字見 https://github.com/ruan6047/ai-workflow/issues/161#issuecomment-5440642694 ——⛔ 本欄只放 URL、不摘要。PM 獨立重跑（⛔ 非轉述）：pytest rc=0 1310 passed 1 skipped（基線 1309）／uv lock rc=0／replay rc=0 114/114／ccs rc=0 命中 0 排除集 0 項／ctr --check rc=0；CI run 33082224871 @ c189465f conclusion=success、pytest 步驟 1311 passed 0 skipped。。
- 2026-08-27T23:10:29+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex；core_pain_resolved no；self_run 6 項；findings 4 項（blocking 3）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-BLOCK-VERSION-REGRESSION1-e0-c189465fd0536fcffa476f45e75f490cbd119b0e。
- 2026-08-27T23:11:16+08:00 amend by wf-cli（op 26e6b802）→ 驗收條件：原值指紋 sha256:4a9ca425decafef79498f1bf680a2bbc5c7d61773b2d9d684f6b80a98d6d199a (3942 bytes) → 新值指紋 sha256:8520f08fe965ab771c41e108f4b53a8ac1df3005c04aa7cd6160717af8802b96 (4304 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 查核 finding -R1-03（major/blocking，attribution=planner）：A6 仍以 aiwf#35 作為「危險已被審過」的排程旁證，與同日 issuecomment-5440813196 的需求方裁定（該引用已刪）直接矛盾 ⇒ 同一張卡面同時有兩句相反的話。PM 於該裁定中修了核心痛點與 A2、⛔ 漏了 A6，本次補上。更正後本卡沒有任何前例旁證，排程依據完全落在需求方裁量。。
- 2026-08-27T23:28:36+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 2；SHA c189465fd0536fcffa476f45e75f490cbd119b0e；階段 審核；踩坑回應 8 族（已檢查 3／不適用 0／發現 5）；證據 R2 派工。R1 裁決 REQUEST_CHANGES（GPT-5@Codex，四筆：三 blocking ＋ 一 minor）。-R1-03（planner）已由 PM 修完（amend op 26e6b802，A6 的 aiwf#35 旁證已刪）。-R1-01 需求方裁定甲案（issuecomment-5441383497）：活看板偵測器涵蓋 ai-workflow ＋ cpbl-analytics 兩個 repo，⛔ 不收窄 A1；skip-not-fail 維持，但只有其中一個抓得到時須以抓得到的那個做斷言並逐字標明另一個被 skip。執行者本輪要做三件：-R1-01 擴母體、-R1-02 移除測試檔兩處的 aiwf#35 引用（它管的是 marker 版本不是 BLOCK_VERSION）、-R1-04 修正 commit message 的舊數字。⛔ 全文與約束見裁定留言，本欄不再摘要。。
- 2026-08-28T00:37:52+08:00 handoff by wf-cli → owner 待指派；iteration 2；SHA c397b13dab4ffe71234dfcd1f60c61c4de2cb904；階段 執行；踩坑回應 13 族（已檢查 2／不適用 0／發現 11）；證據 R2 送審。分支 @ c397b13d；基線 60471f0d；改動仍只有 cli/tests/test_review.py。R1 四筆全處置：-R1-01 需求方裁定甲案已做（兩 repo 母體，四格情境全驗，另加一條裁定未要求的 fail-closed）；-R1-02 測試檔與 commit message 對 aiwf#35 皆 0 命中；-R1-03（planner）PM 已於 amend op 26e6b802 修完；-R1-04 提交說明已更正。⚠️ 執行者以 --amend 修提交說明 ⇒ R1 被審 SHA c189465f 已不是分支祖先（PM 複驗），逐字記在新提交說明裡；若查核者要求被審 SHA 留在歷史上，需新裁定。執行者的失誤與未驗逐項逐字見 https://github.com/ruan6047/ai-workflow/issues/161#issuecomment-5441530219 ——⛔ 本欄只放 URL。PM 獨立重跑：pytest rc=0 1310 passed 1 skipped（那個 skip 是活看板層因匿名額度耗盡）／uv lock rc=0／replay rc=0／ccs rc=0／ctr rc=0；CI run 33088758081 @ c397b13d conclusion=success。。
- 2026-08-28T02:08:07+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex；core_pain_resolved no；self_run 5 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-BLOCK-VERSION-REGRESSION1-e0-c397b13dab4ffe71234dfcd1f60c61c4de2cb904。
- 2026-08-28T02:11:19+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 3；SHA c397b13dab4ffe71234dfcd1f60c61c4de2cb904；階段 審核；踩坑回應 8 族（已檢查 4／不適用 1／發現 3）；證據 R3 派工。R2 裁決 REQUEST_CHANGES（GPT-5@Codex，1 筆 blocking）。必修 -R2-01：test_review.py:1640 對 find_block_by_key() 的 ReviewParseError 直接 continue ⇒ 同 repo 只要還有一筆正常事件，任何帶 marker 但 facts 區塊毀損／重複／無法解析的既有事件都會被排出母體、測試仍綠。處置：候選 facts 區塊解析失敗即紅，並補「正常事件 + 一筆 malformed 事件」的負向測試。⛔ 全文與三項特別評估逐字見 https://github.com/ruan6047/ai-workflow/issues/161#issuecomment-5443245656 ，本欄不再摘要。查核者另裁：匿名額度非本卡阻擋項（超出宣告範圍，⛔ 本輪不處理）；--amend 造成 R1 SHA 非分支祖先⛔ 不要求新裁定（每個 attempt 以 (card, epoch, source_sha) 區分，canonical 未要求受審 SHA 永久留在 source branch）。分支 ai/opus-5/WF-BLOCK-VERSION-REGRESSION1 @ .worktrees/block-version，基線 60471f0d。。
- 2026-08-28T02:57:11+08:00 handoff by wf-cli → owner 待指派；iteration 3；SHA d48d689c1e81ae53a5dc60bc43084397cfe0a35e；階段 執行；踩坑回應 13 族（已檢查 5／不適用 1／發現 7）；證據 R3 送審。分支 ai/opus-5/WF-BLOCK-VERSION-REGRESSION1 @ d48d689c（已推送 origin）；基線 60471f0d；相對 R2 的 c397b13d 改動仍只有 cli/tests/test_review.py（+34/-2），⛔ 零生產碼改動。R2-01 處置：except ReviewParseError 由 continue 改為 raise AssertionError（帶 repo slug 與留言 URL），並新增 test_live_board_detector_rejects_malformed_facts_alongside_a_valid_event（正常事件＋同 repo 毀損事件，以 monkeypatch 注入、離線可跑）。⚠️ 執行者本輪未貼失誤登記／未驗清單留言，PM ⛔ 不代寫亦不推定為空。PM 獨立重跑（⛔ 非轉述）：git diff --check 無誤；test_review.py 72 passed 1 skipped；新測試單跑 1 passed；⭐ 變異檢驗（在拋棄式 worktree 把 raise 改回 continue）⇒ 1 failed 71 passed 1 skipped，紅的正是該新測試 ⇒ 有鑑別力；uv lock --check rc=0；replay rc=0；CI run 33102855808 @ d48d689c conclusion=success。PM 另補一項執行者未驗的事：以 authenticated gh api 拉兩 repo 全部 1340 則留言（⛔ 不動匿名額度），import 測試檔用的同一組 _EVENT_PREFIX／FACTS_BLOCK_KEY／find_block_by_key 重跑判定 ⇒ 帶 marker 204、進母體 117、解析失敗 0 ⇒ 這個 fail-closed 改動不會讓測試在真實看板上一開就紅。。
- 2026-08-28T04:07:23+08:00 review by wf-cli → APPROVE（✅通過）；查核者 Claude Opus 5@Claude Code (Reviewer)；core_pain_resolved yes；self_run 26 項；findings 2 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-BLOCK-VERSION-REGRESSION1-e0-d48d689c1e81ae53a5dc60bc43084397cfe0a35e。
- 2026-08-28T05:05:19+08:00 handoff by wf-cli → owner ruan6047；iteration 3；SHA 54d23e87873e1239a8bff4cbbb2af0c7c5c805fe；階段 審核；踩坑回應 8 族（已檢查 3／不適用 1／發現 4）；證據 R3 查核 APPROVE（Claude Opus 5@Claude Code (Reviewer)，同家族——卡面路由行明文豁免跨家族；兩筆非阻擋 finding R3-01 minor／R3-02 info）。受審 SHA d48d689c1e81ae53a5dc60bc43084397cfe0a35e；因 ruleset strict 以 gh pr update-branch（merge main，⛔ 非 rebase）產生 eceece64045d38df6aefb6732507b27421280f93，受審 SHA 仍為祖先且相對 main 差異仍逐字為 1 file changed, 503 insertions(+)。PR https://github.com/ruan6047/ai-workflow/pull/164 squash 合併為 54d23e87873e1239a8bff4cbbb2af0c7c5c805fe。CI：受審 SHA run 33102855808 success（pytest 逐字 1312 passed in 40.78s、0 skipped ⇒ 活看板偵測器實際執行）；合併前 run 33116209644 tests pass。PM 於 main 複驗 pytest 1479 passed, 1 skipped。⚠️ 未閉環項逐項：(1) R3-01 的 attribution 錯誤（記為 executor，實為 coordinator）與其「全文無落地處」前提錯誤，已於 https://github.com/ruan6047/ai-workflow/issues/161#issuecomment-5445166368 更正並附 7 筆發現原文；⛔ 裁決事件 append-only 未修改。(2) 執行者 issuecomment-5444962598 的 13 族部分是其獨立自評、⛔ 非 PM 清冊的還原，該輪工是 PM 誤導所致。(3) 活看板偵測器在匿名額度耗盡時 fail-open，本卡未處理。(4) 本輪查核者與執行者同為 Claude Opus 5，獨立性低於 R1／R2 的跨家族 GPT-5@Codex。；收尾清理：已清除 worktree；遠端分支 本來就不存在；本地分支 依授權保留（未刪除）。


## Comment 5440137820 · 2026-08-27T13:52:55Z

## 需求方裁定：授權以原文修復 `#161` 的核心痛點（PM 的 shell 引號錯誤造成卡面損壞）

**轉錄來源**：需求方 ruan6047 於 Claude Code 對話中的回覆，逐字為 —— 「**甲**」。
本則留言由 PM（Claude Opus 5@Claude Code）以需求方 token 代為張貼，⛔ 內容為逐字轉錄，⛔ 非 PM 自行決定。

PM 提出的兩案逐字為：

- 甲：貼裁定留言 → `amend --core-pain --ruling-url`（PM 逐字自述「shell 引號錯誤造成卡面損壞，需求方授權以原文修復」，⛔ 不改射程一個字）
- 乙：停卡重開（⛔ 浪費一個卡號，但避免留下一則「為修復自己失誤而生的裁定」）

### ⛔ 先登記 PM 的失誤

本卡於 `2026-08-27` 建立時，PM 以 `zsh` 單行下 `wfcli open`，`--core-pain` 的內容含**反引號**，被 shell 當成**命令替換**執行 ⇒ 所有被反引號包住的識別符（符號名、檔名、常數值）在寫入前就被替換成**空字串**。stderr 逐字留下十一行 `zsh: command not found: …`（`review.BLOCK_VERSION`／`wf_escalation_facts`／`wf_escalation_checkpoint`／`wf_contract_baseline`／`review.py`／`!=`／`v2`×2／`escalation_facts_from_body`／`aiwf#35`）與一行 `(eval):1: permission denied: cli/`。

⇒ 卡面核心痛點現況逐字（損壞後）：

> **痛點**：**痛點**： 今天由三種區塊共用（／／， 內三處 ），任何人把它升成 ，看板上**111 則帶 marker 的既有 review 事件會全部讀不回**……

⚠️ 另有一處：`**痛點**：` 前綴**重複兩次** —— `wfcli open` 自己會加 `- **痛點**：`，而 PM 在傳入值裡又寫了一次。

⭐ **這是轉錄損壞，⛔ 不是射程變更。** 本裁定授權的範圍逐字限定為：**以 PM 原本要傳入的文字修復該欄**，⛔ 不得增刪任何一項事實、⛔ 不得改變射程、⛔ 不得改動已寫入的 `功能`／`簡介`／`資源宣告`／`服務的原始目標` 任何一欄。

### 修復後的核心痛點原文（逐字，供事後比對）

`review.BLOCK_VERSION` 今天由三種區塊共用（`wf_escalation_facts`／`wf_escalation_checkpoint`／`wf_contract_baseline`，`review.py` 內三處 `!= BLOCK_VERSION: return None`），任何人把它升成 `v2`，看板上 **111 則帶 marker 的既有 review 事件會全部讀不回** —— 實測：現況 `escalation_facts_from_body` 讀得回 111/111，把常數改成 `v2` 後讀得回 **0/111**。⛔ **而今天沒有任何測試會因此轉紅**：`cli/` 全套 1439 條在該常數被改動後仍全綠（⚠️ 該項未驗，見驗證 V2）。⚠️ 這不是假設性風險 —— `aiwf#35` 就是「marker v2 升版策略」那張卡，其路由行逐字「查核重點在**升版策略是否會使既有卡停機**」⇒ 有人設計過 v2 且該危險被明確審過，只是 v2 從未實作。⇒ 今天的狀態是「危險被知道、被審過、⛔ 但沒有機械執行者」。

### ⭐ 教訓（⛔ 不限本卡）

`wfcli open`／`amend` 的長文字欄位一律**先寫檔再以 `"$(cat <檔>)"` 傳入**，⛔ 不得在 shell 命令列內嵌含反引號的內容。本 repo 的卡面文字慣例大量使用反引號標註符號名 ⇒ **這個坑對每一張卡都成立**。


## Comment 5440642694 · 2026-08-27T14:31:45Z

## 執行者交回：失誤登記與未驗清單（`WF-BLOCK-VERSION-REGRESSION1` / #161）

- 分支 `ai/opus-5/WF-BLOCK-VERSION-REGRESSION1`，交付 SHA `c189465fd0536fcffa476f45e75f490cbd119b0e`，基線 `60471f0db64fe9149d10a322c5d5dd39c0a45610`。
- ⚠️ 本則刻意**拆開書寫**事件 marker 前綴（寫成「事件 marker 前綴」而不寫其字面），以免整卡落 `marker_quarantined`。

---

## 一、⛔ 失誤登記（逐項逐字）

### 1. 第一版的變異負控是**空的**，我一度要把它當成 V3 通過

我把整個 `Compare` 節點換成常數當作「移除該處比較」，三處都轉紅。但它紅在**結構斷言**（測試自己用 AST 導出的讀取端鍵集合少了一項），⛔ 不是行為斷言 —— 也就是說它只證明了「節點不見了會被抓到」，⛔ **沒有**證明「該處的讀取行為在測試射程內」。成因：我的變異改動了測試自己用來導出母體的那個 AST。

處置：改為中和**左運算元**（`str(data.get(<KEY>)).strip()` → `(<KEY> and BLOCK_VERSION)`），AST 形狀逐字不變、語意恆真 ⇒ 版本檢查形同不存在而結構斷言不受影響。

### 2. 第二版三輪印出**同一則**失敗訊息，我沒有當場察覺

三處變異（`review.py:1108` / `:1174` / `:1200`）全部回報逐字 `換掉 BLOCK_VERSION 之後仍有 2/4 則讀得回：[('wf_escalation_facts', 1108)]` —— 那是第一輪的結果。⚠️ 三個不同的變異不可能得到同一個訊息，這是「變異沒生效」的算術性指紋，我卻先讀成「三處都轉紅 ⇒ 負控成立」。

### 3. 我加上去排除 (2) 的身分檢查，本身也是假的

我加了「印出 pytest 匯入時看到的那一行」，它回報逐字 `一致：True`，而實際執行的仍是舊碼。成因：`inspect.getsource` 讀的是 `.py` 的**文字**，⛔ 不是實際被執行的位元碼。⇒ 身分檢查必須驗**執行行為**（把語料餵給該處讀取端、看它還讀不讀得回），⛔ 不是讀原始碼。

### 4. ⛔ 成因未完全歸因，交付採用的是**症狀**擋法

`PYTHONDONTWRITEBYTECODE=1` ＋ 每輪清 `__pycache__` 可重現地消除該現象；但另一次獨立實驗（同樣的「先變異 1108、還原、再變異 1174」序列、pyc 未清）卻**正常生效** ⇒ 它是**間歇性**的，⛔ 我沒有把根因釘到底。最終採用的處置是「每輪自我驗證執行面身分 ＋ 硬性要求三輪訊息互異，否則整份判失敗」，那是對症狀的擋法，⛔ 不是根因修復。

### 5. ⭐ 卡面核心痛點的一句話被實測**推翻**

卡面逐字：「⛔ **而今天沒有任何測試會因此轉紅**：`cli/` 全套 1439 條在該常數被改動後仍全綠」。

實測（基線 `60471f0d`，把 `BLOCK_VERSION` 由 `v1` 改成 `v2`，並 deselect 本卡新增的兩條）：**rc=1，`2 failed, 1307 passed, 2 deselected`**。逐字兩條：

```
FAILED tests/test_checkpoint.py::test_checkpoint_writes_comment_and_log_index_with_comment_url
FAILED tests/test_checkpoint.py::test_contract_baseline_writes_once_and_fails_loud_on_second
```

⚠️ **但這不使本卡失去理由，反而使它的理由更準。** 那兩條的斷言逐字是 `assert "wf_escalation_checkpoint: v1" in body`（`tests/test_checkpoint.py:277`）與 `assert "wf_contract_baseline: v1" in body`（`:378`），也就是：

- 它們是**寫入端**的字面斷言，⛔ 不是讀取端。升版的人看到的訊息是「渲染出來的留言裡沒有 `v1` 字面」，⛔ 而正解在他眼裡就是「把字面改成 `v2`」—— 它們對「看板上 63 則既有事件會全部讀不回」**一個字都沒說**。
- ⛔ 它們**完全沒有涵蓋** `wf_escalation_facts`：全 repo 沒有任何一條測試斷言 facts 區塊的版本字面，而 facts 正是那 63 則真實事件走的那一種。

⇒ 正確的說法應為：**升版今天會讓兩條寫入端字面斷言轉紅，而那兩條的補法會讓人以為修好了；⛔ 沒有任何一條測試會告訴他既有事件讀不回。** 我建議卡面該句以此逐字收窄，⛔ 但我不代改卡面。

### 6. 卡面另外兩個數字與我的實測不符（⛔ 只登記差異，不宣稱卡面錯）

- 卡面「`cli/` 全套 **1439** 條」；我在基線 `60471f0d` 實測 `uv run pytest -q` ＝ **1309 passed**（`2026-08-27T22:09:45+08:00`）。
- 卡面「看板上 **111 則**」；我以「帶事件 marker 前綴且含 facts 區塊」為判準實測：`ruan6047/ai-workflow` **62** 則、`ruan6047/cpbl-analytics` **50** 則（合計 112，`2026-08-27T22:12` 前後）；⚠️ 同日稍晚重量 ai-workflow 已是 **63** 則。PM 的量測腳本已消失，我無法重建 111 對應的是哪一個母體 ⇒ ⛔ 不宣稱它是錯的，只登記我量到的不是它。⭐ 這正是 A1 要求「不釘數字」的實證：同一天同一個母體在兩小時內就從 62 變成 63。

### 7. 卡面「三處 `!= BLOCK_VERSION: return None`」與 A2 的字面判準會**漏掉一處**

AST 實測三處中只有**兩處**是 `!=`（`escalation_facts_from_body` / `checkpoint_facts_from_body`），第三處是 `body_has_contract_baseline` 的 `== BLOCK_VERSION` 且回傳布林、⛔ 不 `return None`。⇒ 若照 A2 逐字「`!= BLOCK_VERSION` 的比較處」導出，會**靜默漏掉** `body_has_contract_baseline`。交付刻意**不篩運算子**，並在測試裡就地寫明理由。

### 8. `aiwf#35` 管的是 marker 版本，⛔ 不是 `BLOCK_VERSION`

`docs/WF_EVENT_MARKER_V2.md` §1.5 逐字「其餘一律進 payload（同一則留言內的 fenced 區塊，§3.3）」⇒ 該卡設計的是事件 marker 的 `vN`，而本卡的 `BLOCK_VERSION` 是 payload 區塊的 schema 版本，**是兩個不同的常數**。⇒ 卡面「危險被設計過也被審過」這個論據對 `BLOCK_VERSION` 只是**類比**，⛔ 不是同一個東西。痛點本身（升版 ⇒ 既有事件讀不回）我已獨立實測成立，⛔ 不因此動搖；受影響的只是 A6 的排程論據強度。

---

## 二、⚠️ 未驗清單（逐項逐字，各自寫原因）

1. **A1 的「跑的當下從真實看板自行導出」只在活看板那一層成立，而該層在本機預設 skip。** 離線那層的語料是產線 renderer 在跑的當下產生的，⛔ 不是看板事件。⇒ A1 逐字未被單一測試完整滿足。原因：離線層必須不連網才能當恆定的守衛；兩者的取捨與我選的形狀見交付報告，需求方可裁定改成硬性要求（改動約一行）。
2. **CI 上活看板那層今天跑得起來，⛔ 但我沒有量過它的穩定度。** 實測 run `33082224871`（sha `c189465f`，`2026-08-27T14:27:07Z`）pytest 步驟逐字 `1311 passed in 40.80s`、**0 skipped** ⇒ 匿名 REST 在 runner 上可達且未被擋。⚠️ 匿名額度是 60 次/小時/IP 且 runner IP 共用 ⇒ 未來可能被擋而 skip。⛔ 我只有**一次** CI 觀測，未估過被擋機率。
3. **活看板那層只涵蓋 `origin` 這一個 repo。** 本工作流的卡至少橫跨兩個 repo，`ruan6047/cpbl-analytics` 上另有 50 則同型事件，⛔ **不在**斷言母體內。原因：repo 由 `origin` 機械導出，跨 repo 清單無法從樹裡導出而我不願手打。
4. **活看板那層只涵蓋 `wf_escalation_facts`。** 實測 `wf_escalation_checkpoint` 在看板上今天 **0 則**、`wf_contract_baseline` **3 則** ⇒ 只靠看板導語料會讓 checkpoint 那一處比較**完全不在射程內**。另兩種的涵蓋由離線層承擔。
5. **⛔ 不驗既有事件的內容正確性**（`aiwf#138` 射程）、⛔ **不驗**升版之後的遷移路徑（本 repo 今日無 v2 實作，本卡也不提供）、⛔ **不驗** `escalation_facts_from_body` 以外的下游消費者（例如 `validation` 的閘門如何消費 `None`）。
6. **⛔ 綠燈不得被讀成「相容性已保證」。** 它只說：今天這幾處讀取端與這些語料在同一個版本上。⛔ 沒有任何東西保證別台機器上的那份 `wfcli` 也在同一版（`docs/WF_EVENT_MARKER_V2.md` §1.4 已記下同型殘餘風險）。
7. **離線層存在一個已知逃逸路徑，⛔ 已處置但處置本身會 skip。** 把 `BLOCK_VERSION` 與測試裡的黃金值**一起**改大，離線層回綠。實測該情境：離線層 `1 passed`、活看板層 `1 failed`（逐字 `63/63 則既有事件的版本字面不等於本檔凍結的 'v2'`）⇒ 逃逸由活看板層擋下。⚠️ 但活看板層抓不到語料時會 skip ⇒ 該逃逸在離線環境**擋不住**。
8. **⛔ 我沒有驗過「本測試在 `main` 合併結果上」的行為。** 只驗了分支頭（push run，`tests (branch head)`）。合併結果那一支要等 PR 事件才有。


## Comment 5440813196 · 2026-08-27T14:45:05Z

## 需求方裁定：以實測更正核心痛點的四處錯誤（PM 寫錯，執行者實測推翻）

**轉錄來源**：需求方 ruan6047 於 Claude Code 對話中的回覆，逐字為 —— 「**修**」。
本則留言由 PM（Claude Opus 5@Claude Code）以需求方 token 代為張貼，⛔ 內容為逐字轉錄，⛔ 非 PM 自行決定。

### ⛔ 錯在哪（四處，執行者實測推翻，PM 已逐處複驗）

**(1) 「⛔ 而今天沒有任何測試會因此轉紅：`cli/` 全套 1439 條在該常數被改動後仍全綠」—— 兩半都錯。**

PM 在基線 `60471f0d` 的 detached worktree 把 `BLOCK_VERSION = "v1"` 改成 `"v2"` 重跑，逐字：

```
FAILED tests/test_checkpoint.py::test_checkpoint_writes_comment_and_log_index_with_comment_url
FAILED tests/test_checkpoint.py::test_contract_baseline_writes_once_and_fails_loud_on_second
2 failed, 1307 passed in 62.67s
```

⇒ 全套是 **1309** 條（⛔ 不是 1439），且**有 2 條會轉紅**（⛔ 不是全綠）。

⭐ **但執行者的細分讓本卡仍然成立，那才是正確的陳述**：那 2 條是**寫入端字面斷言**（`assert "wf_escalation_checkpoint: v1" in body`）——升版的人看到的訊息就是「把字面改成 v2」，⛔ 對既有事件一個字都沒說；而且**完全沒涵蓋 `wf_escalation_facts`**，那正是絕大多數既有事件走的那一種。⇒ 正確說法是：**升版會讓兩條寫入端斷言轉紅，而補它們的方式會讓人以為修好了。**

**(2) 「三處 `!= BLOCK_VERSION`」—— 錯，是兩處 `!=` ＋ 一處 `==`。**

PM 複驗 `review.py`：`:1108`（`escalation_facts_from_body`）與 `:1174`（`checkpoint_facts_from_body`）是 `!=`；`:1200`（`body_has_contract_baseline`）是 `== BLOCK_VERSION`。⇒ **驗收 A2 照字面（「`!= BLOCK_VERSION` 的比較處」）導出會漏掉第三處。**

**(3) 「111 則」—— 是當日快照且已漂移。**

PM 今日複量：含 `wf_escalation_facts` 字面的留言 `ai-workflow` **69** ＋ `cpbl-analytics` **50** = **119**。執行者量到 62→63（其 `ai-workflow` 母體判準較嚴）。⇒ ⭐ **這正是驗收 A1 逐字要求「判準寫成關係、⛔ 不寫數字」的理由，本次更正不引入新的定值。**

**(4) 「`aiwf#35` 就是『marker v2 升版策略』那張卡……⇒ 有人設計過 v2 且該危險被明確審過」—— 引錯了。**

`aiwf#35` 標題逐字：「`WF-EVENT-MARKER-V2-SCOPE1` **lifecycle 事件的 marker 覆蓋與版本升級**：v1 鍵集合封閉，且六個動詞裡只有 review 有 marker」。⇒ 它管的是 **marker 版本**，`BLOCK_VERSION` 是**另一個常數**。⛔ 該引用不支持本卡，須刪除。

### 授權範圍

本裁定授權的範圍逐字限定為：**以實測值更正上述四處**，⛔ 不得擴大或縮小射程、⛔ 不得改動 `功能`／`簡介`／`資源宣告`／`服務的原始目標` 任何一欄。

⚠️ **(4) 刪掉之後，本卡就沒有「危險被審過」的旁證了。** 逐字登記：本卡的排程依據因此**完全落在需求方裁量**上（同 `aiwf#146` 的 A18 形狀），⛔ 不是「已有前例」。

### ⭐ 教訓（⛔ 不限本卡）

四處全部是 PM 在開卡當下**憑印象寫的**，⛔ 沒有一處在寫下時實測。而它們全部**可以在寫下前用一條指令驗掉**（改常數重跑、`grep -n BLOCK_VERSION`、`gh issue view 35 --json title`）。⇒ **開卡時的核心痛點與驗收，與交付時的宣稱受同一條紀律管：先量再寫。**


## Comment 5441155144 · 2026-08-27T15:10:33Z

<!-- wf-review-event:v1 card_id=WF-BLOCK-VERSION-REGRESSION1 source_sha=c189465fd0536fcffa476f45e75f490cbd119b0e attempt_id=WF-BLOCK-VERSION-REGRESSION1-e0-c189465fd0536fcffa476f45e75f490cbd119b0e -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-BLOCK-VERSION-REGRESSION1`　attempt_id：`WF-BLOCK-VERSION-REGRESSION1-e0-c189465fd0536fcffa476f45e75f490cbd119b0e`
- 查核者：GPT-5@Codex　escalation_epoch：0
- source_sha：`c189465fd0536fcffa476f45e75f490cbd119b0e`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-27T23:10:29+08:00

### self_run（查核者實跑）

- `git rev-parse / diff --name-status / diff --check`
  - HEAD=c189465f；僅 cli/tests/test_review.py +410；無 whitespace error。
- `三輪記憶體突變負控 [mutation negative control]（PYTHONDONTWRITEBYTECODE=1）`
  - 三輪皆先以實際 parser 行為驗明變異已載入，並各自轉紅：facts 2/4 @1108、checkpoint 1/4 @1174、baseline 1/4 @1200。訊息互異，未重演 pycache 假陰性。
- `CI=1 uv run pytest -q tests/test_review.py::test_the_live_board_events_still_carry_the_frozen_block_version`
  - 1 passed in 5.09s。
- `uv lock --check；replay_escalation_rules.py；canonical_citation_scan.py；contract_tool_reconcile.py --check`
  - 全部 rc=0；replay 114/114、citation 0 hits、reconcile OK。
- `匿名 curl api.github.com repo/comments endpoints`
  - 兩者 HTTP 200；公開 repo 的匿名 REST 可達。
- `GitHub Actions run 33082224871 / job 98552230163`
  - head_sha=c189465f、結論 success，pytest step success。

### findings（4，其中 blocking 3）

- **WF-BLOCK-VERSION-REGRESSION1-R1-01**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`live-corpus-origin-only`
  - evidence：活看板偵測器明示只取 origin，且程式只呼叫 _origin_repo_slug()；已知另一個 cpbl-analytics repo 尚有同型事件，不在母體內。見 cli/tests/test_review.py:1578 與 :1586。
  - disposition：讓 live detector 在可觀測範圍涵蓋兩個已知 repo，或由需求方以 wfcli 正式收窄 A1／核心痛點。離線層不能替代真實 cpbl-analytics 不可變事件。
- **WF-BLOCK-VERSION-REGRESSION1-R1-02**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`marker-version-analogy`
  - evidence：新增測試仍宣稱 aiwf#35 是 BLOCK_VERSION 升版路徑，並把失敗者導向該卡；#35 實際處理的是 lifecycle marker 版本。見 cli/tests/test_review.py:1246 與 :1487。
  - disposition：移除 aiwf#35 引用，改為不指派既有卡的相容讀取端需求；不得把 marker v2 當作 BLOCK_VERSION 的旁證或既定遷移路徑。
- **WF-BLOCK-VERSION-REGRESSION1-R1-03**　severity=major　blocking=true　class=authoritative-artifact　attribution=planner　root_cause_id=`stale-scheduling-basis`
  - evidence：#161 的 A6 仍以 aiwf#35 作為「危險已被審過」的排程論據，與 issuecomment-5440813196 的需求方裁定相反。
  - disposition：由 PM 透過 wfcli 更正 A6：排程依據僅為需求方裁量，不得保留 #35 旁證。
- **WF-BLOCK-VERSION-REGRESSION1-R1-04**　severity=minor　blocking=false　class=authoritative-artifact　attribution=executor　root_cause_id=`stale-pre-correction-commit-message`
  - evidence：commit message 仍稱升版後「沒有任何測試轉紅、1309 全綠」；已知實測是 2 failed / 1307 passed，且兩條僅為寫入端字面斷言。
  - disposition：修正提交說明，使其與需求方裁定一致。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-BLOCK-VERSION-REGRESSION1-e0-c189465fd0536fcffa476f45e75f490cbd119b0e
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: no
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待指派
findings:
  - finding_id: WF-BLOCK-VERSION-REGRESSION1-R1-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: live-corpus-origin-only
    counting_eligible: true
  - finding_id: WF-BLOCK-VERSION-REGRESSION1-R1-02
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: marker-version-analogy
    counting_eligible: true
  - finding_id: WF-BLOCK-VERSION-REGRESSION1-R1-03
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: planner
    root_cause_id: stale-scheduling-basis
    counting_eligible: false
  - finding_id: WF-BLOCK-VERSION-REGRESSION1-R1-04
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: stale-pre-correction-commit-message
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5441383497 · 2026-08-27T15:27:53Z

## 需求方裁定：finding `-R1-01` 採甲案 —— 活看板偵測器涵蓋兩個 repo

**轉錄來源**：需求方 ruan6047 於 Claude Code 對話中的回覆，逐字為 —— 「**ＯＫ**」（對 PM 提出的四項建議一併同意，本則對應其中第 ② 項）。
本則留言由 PM（Claude Opus 5@Claude Code）以需求方 token 代為張貼，⛔ 內容為逐字轉錄，⛔ 非 PM 自行決定。

PM 提出的兩案逐字為：

- 甲：讓偵測器涵蓋兩個已知 repo
- 乙：由需求方以 `wfcli` 正式收窄 A1／核心痛點（明說本卡只保 `ai-workflow`）

### 裁定內容

**採甲案。** 活看板偵測器的母體須涵蓋 `ruan6047/ai-workflow` 與 `ruan6047/cpbl-analytics` 兩個 repo，⛔ 不收窄 A1 或核心痛點。

### 依據

查核者的 disposition 逐字：「讓 live detector 在可觀測範圍涵蓋兩個已知 repo，或由需求方以 `wfcli` 正式收窄 A1／核心痛點。**離線層不能替代真實 `cpbl-analytics` 不可變事件。**」

⇒ 乙案要付的代價是那批事件**真的沒有被保護**。PM 今日複量：含 `wf_escalation_facts` 字面的留言 `ai-workflow` **69** ＋ `cpbl-analytics` **50**（量在 2026-08-27，⚠️ 依 A1 該數字⛔ 不得寫進測試，此處僅作為裁定依據的量級參考）。

三個理由：

1. `_origin_repo_slug()` 已經在了 ⇒ 加第二個 repo 是**擴一個清單**，⛔ 不是改架構。
2. `wfcli` 本來就是**跨 repo 工具** —— 今天的看板 Project #4 同時服務兩個 repo，`assign` 的資源交集閘門也是跨 repo 掃的。
3. 乙案等於**用收窄射程換過關**，而本卡的核心痛點逐字是「看板上既有的 review 事件會全部讀不回」——「看板」本來就不只一個 repo。

### 對交付的約束

1. **repo 清單須機械導出或明文列舉，⛔ 不得寫死單一 `origin`。** ⚠️ 依 A1，⛔ 仍不得把任何**母體大小**寫成常數；repo 清單本身不是母體大小，可以是明文的。
2. ⚠️ **匿名額度壓力加倍**（60 次/小時/IP、runner IP 共用）。⛔ 現行「抓不到即 skip、不 fail」的設計**維持**——需求方⛔ 未裁定改成硬性必跑。若兩個 repo 都抓不到，仍是 skip；⭐ **但若只有其中一個抓得到，須以抓得到的那個做斷言、並在輸出中逐字標明另一個被 skip**，⛔ 不得整條 skip 掉。
3. **離線層（不變式）不受本裁定影響**，維持恆跑。

### 什麼會推翻本裁定

若實作中發現 `cpbl-analytics` 的事件形狀與 `ai-workflow` **不同構**（例如 marker 格式或 block 鍵不同），使兩者無法共用同一組斷言 ⇒ 甲案不可行，**停手回報**，改由需求方在乙案與「兩套斷言」之間裁定。

---

## ⛔ 順帶：`-R1-03` 已修（那一筆是 PM 的）

`amend` op `26e6b802`：A6 中以 `aiwf#35` 作為「危險已被審過」的排程旁證**已刪除**。

⚠️ PM 的失誤已逐字寫進 A6：同日稍早的裁定（`issuecomment-5440813196`）已更正核心痛點與 A2，⛔ **漏了 A6**，造成同一張卡面同時存在兩句相反的話達三小時。

⇒ 本卡自此**沒有任何「危險已被前例審過」的旁證**，排程依據完全落在需求方裁量上（同 `aiwf#146` 的 A18 形狀）。


## Comment 5441530219 · 2026-08-27T15:39:37Z

## 執行者交回 R2：失誤登記與未驗清單（`WF-BLOCK-VERSION-REGRESSION1` / #161）

- 分支 `ai/opus-5/WF-BLOCK-VERSION-REGRESSION1`，交付 SHA **`c397b13dab4ffe71234dfcd1f60c61c4de2cb904`**，基線 `60471f0db64fe9149d10a322c5d5dd39c0a45610`。
- R1 被審 SHA `c189465fd0536fcffa476f45e75f490cbd119b0e`（本輪以 `--amend` 修正提交說明 ⇒ ⚠️ 它已不是分支祖先，逐字記在新提交說明裡）。
- ⚠️ 本則刻意**拆開書寫**事件 marker 前綴（只寫「事件 marker 前綴」、不寫其字面），以免整卡落 `marker_quarantined`。
- ⚠️ 本則由執行者（Claude Opus 5@Claude Code）撰寫，以需求方 token 張貼；⛔ 內容非需求方本人所寫。

---

## 一、本輪處置（逐條對應裁決）

### `-R1-01`（甲案：涵蓋兩個 repo）

**停手條件先查**：`cpbl-analytics` 與 `ai-workflow` 的事件是否同構？⇒ **同構，⛔ 不觸發停手**。三條判準全部用產線碼判、⛔ 未自行重打 regex（`2026-08-27T23:31:22+08:00`）：

| repo | 帶 marker 前綴 | 含 facts 區塊 | 同一讀取端讀得回 | 版本字面 | marker 首行 | 換掉常數後 |
|---|---|---|---|---|---|---|
| `ruan6047/ai-workflow` | 151 | 64 | 64/64 | 全 `v1` | 同一形態 | 0/64 |
| `ruan6047/cpbl-analytics` | 50 | 50 | 50/50 | 全 `v1` | 同一形態 | 0/50 |

**實作**：`_LISTED_BOARD_REPOS` 明文列舉兩個 repo，`_board_repos()` 回傳「明文 ∪ 機械導出的 `origin`」（去重保序）——取聯集而不是二選一，因為那個方向只會讓母體變大、⛔ 不會讓它靜默變小。⛔ 母體大小仍不進任何斷言。

**部分可達的行為**（逐條照裁定），實測四格：

| 情境 | 結果 | 母體 | 被略過的 repo 是否逐字標明 |
|---|---|---|---|
| (a) 兩個都可達（常數暫升 v2） | FAILED | **114/114**（64＋50） | 不適用 |
| (b) `cpbl-analytics` 403 | FAILED | **64/64**（仍對 ai-workflow 斷言） | ✅ UserWarning ＋ stdout |
| (c) `ai-workflow` 403 | FAILED | **50/50**（仍對 cpbl 斷言） | ✅ UserWarning ＋ stdout |
| (d) 兩個都 403 | SKIPPED | 無 | ✅（skip 訊息逐字列出兩個原因） |

(b) 的逐字輸出：

```
⚠️ 本輪未取到、其事件⛔不在母體內的 repo：ruan6047/cpbl-analytics（HTTPError: HTTP Error 403: rate limit exceeded）　｜　本輪實際取到並斷言的 repo：['ruan6047/ai-workflow']
```

另加一條**未在裁定要求內**的 fail-closed：某 repo 取到了留言卻導不出任何事件 ⇒ 硬紅，訊息逐字寫「母體**靜默變小**了……⛔ 不要直接把它從清單裡刪掉了事」。

### `-R1-02`（移除 `aiwf#35`，改為不指派）

兩處都改，⛔ 未換成另一張卡號：

- `:1246` → 「⛔ **本節不實作、也不主張任何升版路徑**，⛔ 也不指名由哪張卡承接。」
- `:1487` → 「⇒ 正解是先落地一個同時認舊版與新版的讀取端（⛔ 本節不指名由誰做），⛔ 不是把本節的黃金值一起改大」

`grep -rn 'aiwf#35' cli/tests/test_review.py` ⇒ **0 命中**；新的提交說明內 ⇒ **0 命中**。

### `-R1-04`（提交說明舊數字）

以 `--amend` 修正並 `push --force-with-lease`。新提交說明逐字寫入實測與其**意義**：`2 failed, 1307 passed`，轉紅兩條是寫入端字面斷言，補它們的方式就是把字面改成 `v2`、⛔ 對既有事件讀不回一個字都沒說，且完全沒涵蓋 `wf_escalation_facts`。

---

## 二、⛔ 失誤登記（逐項逐字）

### 1. ⭐ `-R1-01` 是**我自己上一輪就登記過**的缺口，⛔ 我登記了卻沒有修

上一輪未驗清單第 3 項逐字：「活看板那層只涵蓋 `origin` 這一個 repo。……`ruan6047/cpbl-analytics` 上另有 50 則同型事件，⛔ **不在**斷言母體內。」

⇒ 我把一個**我自己已經指認出來**的涵蓋缺口留給查核者去發現。⚠️ 「登記了」⛔ 不等於「處置了」——登記的用途是讓需求方判要不要修，⛔ 不是拿來豁免不修。⭐ 而查核者的 disposition 逐字「離線層不能替代真實 `cpbl-analytics` 不可變事件」正是我自己寫在測試註解裡的那個論證（「既有事件在 repo 之外，樹裡沒有任何東西知道它們的版本字面」）——**我用那個論證說明了活看板層為什麼必要，卻沒有把它套用到第二個 repo 上。**

### 2. `-R1-02` 是同一個形狀：我在報告裡指出問題、在碼裡保留問題

上一輪失誤登記第 8 項，我逐字寫了「`aiwf#35` 管的是 marker 版本，⛔ 不是 `BLOCK_VERSION`……⛔ 不是同一個東西……只是**類比**」。⇒ 我**判斷出了那是錯的引用**，卻把那兩處引用原樣留在交付碼裡。

⛔ 在報告裡更正、在碼裡保留，是最糟的組合：報告會被讀一次，碼會被讀很多次 ⇒ 下一個讀碼的人會以為 marker v2 是 `BLOCK_VERSION` 的既定遷移路徑。

### 3. `-R1-04` 是「同一個量在兩個地方，我只改了一個」

我在留言裡更正了卡面的「1439 全綠」，⛔ 卻沒回頭改自己 commit message 裡的「1309 條全綠」。兩句話講的是同一件事、都是我寫的、相隔幾分鐘。

### 4. ⚠️ 探針的 (e) 格我差點誤讀成「腳本又壞了」

(e) 情境（兩個 repo 都可達、常數未動）回報 `SKIPPED`，且訊息與 (d)（兩個都被擋）**逐字相同**——那正是我上一輪登記過的「三輪同訊息 ＝ 變異沒生效」指紋。我的第一反應是「探針壞了」。實際去量 `x-ratelimit-remaining` 才知道是**真的把匿名額度用完了**：`limit 60 / remaining 0 / used 60`，reset `2026-08-28T00:31:13`。

⇒ 這次沒有誤判，⛔ 但也只是因為我這次去量了。⭐ 而它同時是一個比我上一輪估計嚴重得多的事實，見未驗清單第 1 項。

---

## 三、⚠️ 未驗清單（逐項逐字，各自寫原因）

1. **⭐ 匿名額度會被打到，而且比我上一輪估的容易得多。** 我在**一小時內的正常開發**就把自己 IP 的額度用完（`0/60`）。本測試一次要 14 次請求（兩個 repo × 7～8 頁）⇒ 一小時內跑滿 4 次就沒了。⇒ 活看板層在**本機 opt-in** 情境下會**經常** skip。CI 上兩次觀測都跑得起來且**兩個 repo 都取到**（run `33082224871` sha `c189465f`、run `33088758081` sha `c397b13d`，皆 `1311 passed`、0 skipped、⛔ 無 warnings summary ⇒ 無 repo 被略過），⛔ 但兩次不構成穩定度證據。
2. **⛔ 我沒有量過、也沒辦法量 CI runner IP 的額度殘量。** 要印它得改 `ci.yml`，⛔ 那不在本卡宣告資源內。⇒「CI 上會不會被擋」我只有兩個綠色觀測，⛔ 沒有機制。
3. **repo 清單漏列，本測試偵測不出來。** `_LISTED_BOARD_REPOS` 是明文的；⛔ 它看不出有沒有第三個 repo 該列而沒列——那是治理事實，樹裡沒有記載。⚠️ **這正是 `-R1-01` 被抓到的成因，處置後該成因仍在**，只是母體從 1 個 repo 變成 2 個。
4. **「repo 可達但零事件」那條 fail-closed ⛔ 未被逼出來過。** 我只在邏輯上讓它硬紅，⛔ 沒有構造情境實跑。⇒ 該分支未驗。
5. **上一輪未驗清單第 4／5／6／8 項原樣仍成立，⛔ 不因本輪修了 repo 涵蓋面而縮小**：⛔ 只看 `wf_escalation_facts`（`wf_escalation_checkpoint` 在看板上仍是 **0 則**、`wf_contract_baseline` **3 則**，另兩種靠離線層）、⛔ 不驗既有事件內容正確性（`aiwf#138` 射程）、⛔ 不驗升版後的遷移路徑、⛔ 不驗其他下游消費者、⛔ 綠燈不得讀成「相容性已保證」、⛔ 未驗「合併結果」那一支 CI（只驗過 `tests (branch head)`）。
6. **`--amend` 使 R1 被審 SHA `c189465f` 不再是分支祖先。** 我把它逐字記在新的提交說明裡（形態沿用本 repo 既有的 §3.5 緩解寫法），⛔ 但那只是文字紀錄——日後在乾淨 clone 上 `git cat-file` 它可能已不可達。⚠️ 若查核者要求被審 SHA 必須留在歷史上，正解是改成追加一筆而非 amend，⛔ 那我需要新的裁定。
7. **⛔ 我沒有重跑「基線 ＋ 改 v2」那個實驗。** `2 failed, 1307 passed` 是量在 `60471f0d`（`2026-08-27` 稍早），本輪未複驗；⛔ 但基線未變，故我判它仍成立——⚠️ 這是推論、不是本輪的量測。


## Comment 5443245656 · 2026-08-27T18:07:19Z

> **轉錄自述**：本則由 **PM（Claude Opus 5@Claude Code）** 以需求方 token 發文，內容為**跨家族查核者 `GPT-5@Codex` 的 R2 收據逐字轉錄**，由需求方於對話中轉貼給 PM。⛔ PM 未修改任何一個字、未增刪 finding。平台上的 author 欄恆為 `ruan6047`（token 持有者），⛔ 不代表本文由需求方撰寫。結構化裁決事件另行寫入。

---

結論：REQUEST_CHANGES。R1 四筆已實質處置，但 R2 新增的活看板偵測器仍會靜默排除「讀不懂」的既有事件，核心痛點尚未完全消除。

* 必修 R2-01：`test_review.py`[ L1640](https://github.com/ruan6047/ai-workflow/blob/c397b13dab4ffe71234dfcd1f60c61c4de2cb904/cli/tests/test_review.py#L1640) 對 `find_block_by_key()` 的 `ReviewParseError` 直接 `continue`。因此同一 repo 只要還有一筆正常事件，任何帶 marker、但 facts 區塊毀損／重複／無法解析的既有事件都會被排出母體，測試仍可綠燈。這違反「全數讀得回」與失敗即封鎖 [fail-closed] 的設計。應改成：候選 facts 區塊解析失敗即紅，並補「正常事件 + 一筆 malformed 事件」的負向測試。

三項特別評估：

1. 匿名額度：同意執行者的界線。每次約 14 次 REST 請求、60/hr/IP 的限制會讓本機 opt-in 偵測器常 skip；兩次 CI 成功不是穩定性證據。這不是本卡的阻擋項，因為離線不變式仍能擋住單純升 `BLOCK_VERSION`，而讓 CI 可觀測額度須動 `ci.yml`，超出宣告範圍。CI run 確為指定 SHA 成功，但僅是 branch-head job，非 PR merge 結果。[CI run](https://github.com/ruan6047/ai-workflow/actions/runs/33088758081)
2. `--amend`：不要求新裁定。R1 的 `c189465f` 已非分支祖先屬實；但規則要求的是每個 review attempt 以 `(card, epoch, source_sha)` 區分，R2 必須重新查 `c397…`，不能沿用 R1。canonical 並未要求被審 SHA 必須永久留在 source branch 歷史；要求 append-only 的是 lifecycle 留痕。R1 SHA 已在交付留痕與新 commit message 明記，足以作為歷史 attempt 識別。只有要新增「受審 SHA 必須可由分支祖先到達」這條規則時，才需要需求方新裁定。
3. 執行者的失誤登記：這次不是額外 finding，本身也不構成修復證據。但它揭示的模式在 R2 仍有具體實例：報告主張「讀不懂即封鎖」，程式卻以 `except ReviewParseError: continue` 保留了靜默排除路徑。故 R2-01 必修。

已核實：

* `60471f0d` 是 `c397…` 祖先；相對差異僅 `cli/tests/test_review.py`，471 行新增，`git diff --check` 無誤。
* 隔離 Git clone：`uv lock --check`、`tests/test_review.py` 為 71 passed, 1 skipped；離線 replay 114/114、citation scan 0 命中、contract reconcile OK。
* R1-01 的雙 repo 甲案與部分可達規則，符合需求方裁定與交付報告；R1-02／03／04 的舊引用與錯誤敘述也已移除／更正。[甲案裁定](https://github.com/ruan6047/ai-workflow/issues/161#issuecomment-5441383497) [R2 交付留痕](https://github.com/ruan6047/ai-workflow/issues/161#issuecomment-5441530219)


## Comment 5443255890 · 2026-08-27T18:08:11Z

<!-- wf-review-event:v1 card_id=WF-BLOCK-VERSION-REGRESSION1 source_sha=c397b13dab4ffe71234dfcd1f60c61c4de2cb904 attempt_id=WF-BLOCK-VERSION-REGRESSION1-e0-c397b13dab4ffe71234dfcd1f60c61c4de2cb904 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-BLOCK-VERSION-REGRESSION1`　attempt_id：`WF-BLOCK-VERSION-REGRESSION1-e0-c397b13dab4ffe71234dfcd1f60c61c4de2cb904`
- 查核者：GPT-5@Codex　escalation_epoch：0
- source_sha：`c397b13dab4ffe71234dfcd1f60c61c4de2cb904`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-28T02:08:07+08:00

### self_run（查核者實跑）

- `git merge-base --is-ancestor 60471f0d c397b13d；git diff --name-status 60471f0d..c397b13d；git diff --check`
  - 60471f0d 是 c397… 祖先；相對差異僅 cli/tests/test_review.py，471 行新增，git diff --check 無誤。
- `隔離 Git clone：uv lock --check；uv run --frozen pytest -q cli/tests/test_review.py`
  - uv lock --check 通過；tests/test_review.py 為 71 passed, 1 skipped。
- `離線 replay_escalation_rules.py；canonical_citation_scan.py；contract_tool_reconcile.py --check`
  - 離線 replay 114/114、citation scan 0 命中、contract reconcile OK。
- `比對 R1 四筆 finding 的閉環狀態（對照甲案裁定與 R2 交付留痕）`
  - R1-01 的雙 repo 甲案與部分可達規則，符合需求方裁定與交付報告；R1-02／03／04 的舊引用與錯誤敘述也已移除／更正。裁定 https://github.com/ruan6047/ai-workflow/issues/161#issuecomment-5441383497 交付留痕 https://github.com/ruan6047/ai-workflow/issues/161#issuecomment-5441530219
- `GitHub CI run 33088758081（指定 SHA）`
  - 確為指定 SHA 成功，但僅是 branch-head job，非 PR merge 結果。

### findings（1，其中 blocking 1）

- **WF-BLOCK-VERSION-REGRESSION1-R2-01**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`silent-exclusion-of-unreadable-events`
  - evidence：test_review.py L1640（https://github.com/ruan6047/ai-workflow/blob/c397b13dab4ffe71234dfcd1f60c61c4de2cb904/cli/tests/test_review.py#L1640）對 find_block_by_key() 的 ReviewParseError 直接 continue。因此同一 repo 只要還有一筆正常事件，任何帶 marker、但 facts 區塊毀損／重複／無法解析的既有事件都會被排出母體，測試仍可綠燈。這違反「全數讀得回」與失敗即封鎖 [fail-closed] 的設計。查核者於三項特別評估第 3 點另記：報告主張「讀不懂即封鎖」，程式卻以 except ReviewParseError: continue 保留了靜默排除路徑。收據逐字全文見 https://github.com/ruan6047/ai-workflow/issues/161#issuecomment-5443245656
  - disposition：應改成：候選 facts 區塊解析失敗即紅，並補「正常事件 + 一筆 malformed 事件」的負向測試。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-BLOCK-VERSION-REGRESSION1-e0-c397b13dab4ffe71234dfcd1f60c61c4de2cb904
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: no
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待指派
findings:
  - finding_id: WF-BLOCK-VERSION-REGRESSION1-R2-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: silent-exclusion-of-unreadable-events
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5444608918 · 2026-08-27T20:06:09Z

> **轉錄自述**：本則由 **PM（Claude Opus 5@Claude Code）** 以需求方 token 發文。內容為 PM 依需求方指示派出的**子代理查核者 `Claude Opus 5@Claude Code (Reviewer)`** 的 R3 報告逐字轉錄。⛔ PM 未修改任何一個字、未增刪 finding。平台上的 author 欄恆為 `ruan6047`（token 持有者），⛔ 不代表本文由需求方撰寫。
>
> ⚠️ **獨立性揭露**：本輪查核者與執行者**同為 Claude Opus 5**，canonical §5 逐字「同家族不同工具不算獨立」。卡面明文豁免（執行/查核路由行逐字「⛔ 非紅線（唯讀測試、零生產碼改動），毋須跨家族。」）故合法，但獨立性低於 R1／R2 的跨家族 `GPT-5@Codex`。
>
> PM 已獨立複驗查核者兩項最尖銳的宣稱：`command -v ruff` 無命中、`cli/pyproject.toml` 與 `.github/workflows/ci.yml` grep ruff 皆 0、repo 根無 ruff 設定；`gh run view 33102855808 --json headSha,conclusion` 回 headSha 逐字 `d48d689c…`、conclusion success，其 log 逐字 `1312 passed in 40.78s` 且無 skipped 行。

---

# R3 查核報告 — `WF-BLOCK-VERSION-REGRESSION1`（#161）

查核者 `Claude Opus 5@Claude Code (Reviewer)`／被審 `d48d689c1e81ae53a5dc60bc43084397cfe0a35e`

## 0. 進駐與基準核對

`git rev-parse d48d689c…` rc=0；`git branch -r --contains` 逐字回 `origin/ai/opus-5/WF-BLOCK-VERSION-REGRESSION1` ⇒ 已推上 origin，**不停審**。

所有會改動 tracked file 的驗證都在我自己 `git worktree add --detach` 的兩棵拋棄式 worktree（scratchpad 底下）跑，跑完 `git worktree remove --force` 收掉。收尾複核：`.worktrees/block-version` HEAD 仍為 `d48d689c`、dirty=0；`origin/ai/opus-5/…` tip 仍為 `d48d689c`。**我沒有寫入 source branch 的任何一個位元，也沒有在 GitHub 上留任何留言。**

## 1. 第一判準：核心痛點是否消失

**是。** 而且我用的是實跑證據，⛔ 不是報告轉述。

痛點的兩個半句要分開驗：

**(a)「升版會讓既有事件全部讀不回」** — `review.py` 三處相等性比較，我逐處變異（拋棄式 worktree，⛔ 未 commit）：

| 變異處 | 結果 | 紅在哪一條斷言 |
|---|---|---|
| `escalation_facts_from_body` L1108 移除 | rc=1 `1 failed` | 讀取端／寫入端區塊鍵集合不相等，`Extra items in the right set: 'wf_escalation_facts'` |
| `checkpoint_facts_from_body` L1174 移除 | rc=1 `1 failed` | 同上，缺 `wf_escalation_checkpoint` |
| `body_has_contract_baseline` L1200 移除 | rc=1 `1 failed` | 同上，缺 `wf_contract_baseline` |
| L1108 保留 AST 節點但令其失效（`if False and …`） | rc=1 `1 failed` | `換掉 BLOCK_VERSION 之後仍有 2/4 則讀得回：[('wf_escalation_facts', 1108)]` |

⭐ 第四列是關鍵：它證明負控**有兩層**——拿掉比較被 AST 集合比對抓到，留著比較但繞過它被「換值後仍讀得回」抓到。⛔ 沒有只靠其中一層。

**(b)「今天沒有任何測試會擋住」** — 已不成立。merge-base `60471f0d` 全套 **1309 passed**（我自己在拋棄式 worktree 實跑，rc=0）；`d48d689c` 全套 **1311 passed, 1 skipped**，rc=0。新增的兩條測試就是缺的機械執行者。

`core_pain_resolved: yes`。

## 2. R2-01 逐項閉環

R2-01 逐字要求兩件，兩件都做到，且我各自獨立證實：

**(1)「候選 facts 區塊解析失敗即紅」** — L1640 的 `except ReviewParseError: continue` 已改為帶 repo slug 與留言 URL 的 `raise AssertionError(…) from exc`。

**(2)「補『正常事件 + 一筆 malformed 事件』的負向測試」** — 新增 `test_live_board_detector_rejects_malformed_facts_alongside_a_valid_event`。

⚠️ 我沒有只看它綠。**「pytest.raises 通過」本身是零資訊**——`raises(AssertionError, match="example.invalid/malformed")` 也可能被下游 `drifted`／`unreadable` 那兩條斷言滿足（它們同樣會把 URL 印進訊息）。所以我寫了一支探針，重現同一組 monkeypatch 後直接把真正拋出的例外印出來：

```
PROBE-1: malformed raises ReviewParseError: 第 2 行的頂層鍵 'wf_escalation_facts' 重複；重複鍵會靜默覆蓋，一律拒收
PROBE-2: valid parses to block? True
PROBE-3: AssertionError => example/board 的既有事件 https://example.invalid/malformed 含 wf_escalation_facts 區塊卻無法解析 ⇒ 它不能被排出母體；既有事件讀不懂時必須 fail closed
PROBE-3: __cause__ = ReviewParseError: 第 2 行的頂層鍵 'wf_escalation_facts' 重複…
```

三件事因此成立：毀損語料**真的**觸發 `ReviewParseError`（不是惰性 fixture）、正常語料**真的**進得了母體（所以「正常事件掩蓋毀損事件」這個 R2-01 的形狀是真的被重現）、拋出的**正是**新加的 fail-closed 例外而非下游斷言。

**變異檢驗**（把 `raise` 改回 `continue`）：rc=1，`1 failed, 71 passed, 1 skipped`，紅的逐字是 `FAILED …::test_live_board_detector_rejects_malformed_facts_alongside_a_valid_event`，理由 `E Failed: DID NOT RAISE AssertionError`。⇒ 有鑑別力。

**R2-01 閉環。**

## 3. 回歸不倒退

**A1** R3 的 +34 行裡⛔ 無任何寫死母體大小（我對 diff 的 `+` 行掃 `== <兩位數以上>`／`len(corpus) …`／`assert …<兩位數以上>`，0 命中）。母體導出邏輯一行未動。

**A2** AST 導出機制（`_block_version_sites()`，判準為含 `BLOCK_VERSION` 的 `ast.Compare`、⛔ 不篩運算子）未被 R3 觸及；種數仍不寫死，靠 `set(readers) == set(writers) == set(_CORPUS_FACTORIES)` 三向相等把關。§1 表的三列即是「新增第四種區塊而測試沒轉紅」的反向證明。

**A3 零生產碼改動 —— 比卡面要求的更嚴。** `git diff --name-only 60471f0d..d48d689c` 只有 `cli/tests/test_review.py`；`-- cli/src/` 過濾後檔案數 **0**；整張卡相對 merge-base 是 **`1 file changed, 503 insertions(+)`、0 deletions** ⇒ ⛔ 沒有修改過任何既有行。另：`test_the_live_board_events_still_carry_the_frozen_block_version` 在 merge-base **不存在**（grep 命中 0），故 R3 動它⛔ 不構成「改既有測試的斷言」。唯一宣告資源 `file:cli/tests/test_review.py` 相符。

**A4／V3** 見 §1 表，逐處都紅，⛔ 未 commit 任何變異（每輪 `git checkout --` 後 dirty=0）。

**A5** 母體漂移聲明所在的 docstring 一字未改。新增的負向測試不導出母體，故 A5 不適用於它。

**V4 回歸不退化 —— ⛔ 全部不接管線，rc 逐項分開跑，量在 `d48d689c`（worktree dirty=0）**：

- `uv run --frozen --project cli pytest -q`：**rc=0**，`1311 passed, 1 skipped`（基線 `60471f0d` 為 `1309 passed`，rc=0）⇒ 1311 ≥ 1309 ✔
- `uv lock --check --project cli`：**rc=0**
- `scripts/replay_escalation_rules.py`：**rc=0**，`114/114 通過`
- `scripts/canonical_citation_scan.py`：**rc=0**，`掃描檔案數：152／命中（不含排除）：0／排除集：0 項`
- `scripts/contract_tool_reconcile.py --check`：**rc=0**，`[reconcile] OK：59 個缺口全部有登記處置，判定一致。`
- `git diff --check c397b13d..d48d689c`：**rc=0**

**V5** 卡面 V5 逐字點名的三項「⛔ 不驗」都在未被 R3 觸及的 docstring 裡原文保留 ⇒ 未倒退。

**A6** 依派審詞不重驗。

## 4. PM 交我判的兩件

### 4-1 執行者未貼失誤登記／未驗清單 ⇒ **不是 `review-invalid`；是一筆 minor、非阻擋的 finding**

依據我自己讀的原文，分四層：

1. **`review-invalid` 的成立要件是封閉列舉的**，`templates/review-escalation.md` §1 逐字：「未依順序進行的查核、查核環境受污染、reviewer 獨立性不符、查核了非 handoff 指定的 artifact、**`APPROVE` 未附 `self_run`**，或同一 reviewer 對同一 SHA 重複回報而沒有新的必要查核範圍」。⇒ 它判的是**查核**，⛔ 不是交付。執行者的留言缺口不在列舉內。
2. **同 §1 明指這是 preflight 的管轄**：preflight 至少驗「必要測試／**證據存在**」，且「可由 sender／Coordinator 修正的交付缺口寫 `preflight-failed`」——⛔ 不增加 iteration、⛔ 不建立 review event、⛔ 不派 reviewer。⇒ 依條文，PM 在派審詞裡已自行觀察到該缺口的那一刻，正解是寫 `preflight-failed`，而不是派審後把它丟給查核者裁。
3. **§6.4.2 只管形狀，且是條件式的**：逐字「未驗清單的**每一項**必須標明**驗不了的原因**……⛔ 標不出原因的，代表它驗得了 ⇒ 不得列入，應直接驗」。⇒ 有列才受管。⭐ 而依它自己的下半句，「全都驗得了」時**正確輸出恰恰就是不列** ⇒ 空清單本身合規。另：`失誤登記` 在 `AI_WORKFLOW.md` 與 `templates/` 全 repo **0 命中** ⇒ 那不是 canonical 詞彙，無條文可違反。
4. **§6.4 的實質義務已滿足**：卡面 Log 的 R3 handoff 行逐字「踩坑回應 13 族（已檢查 5／不適用 1／**發現 7**）」，CLI 已驗每格非空。

⇒ 所以真正的缺口⛔ 不是「沒回應踩坑」，而是**回應的全文沒有任何落地處**。而這是刻意設計出來的：`cli/src/wf_cli/pitfalls.py` 的 `digest()` docstring 逐字「⛔ 不含族名也不含自由文字——只有格數與分佈……**報告全文屬檢閱那一環，不由 Log 承載**」。⇒ 全文只能靠交付留言承載，R1（`5440642694`）／R2（`5441530219`）都有、R3 沒有（我自己列 issue 留言確認最後一則執行者留言仍是 R2 那則）。

**後果要講清楚**：canonical §6.4 逐字說「⛔ CLI 只驗每項有非空回答……**擋敷衍的是檢閱那一環，不是 CLI**」。R3 有 7 格自述「發現」，而**沒有任何消費者讀得到它們** ⇒ canonical 指定的唯一過濾器對 R3 結構上不可執行。這是 finding（`-R3-01`），⛔ 不是 `review-invalid`。

不阻擋的理由：§1–§3 每一條可倒退項我都自己實跑複驗過，結論**不依賴**那份報告。

### 4-2 PM 的看板數字可否採信 ⇒ **可，但⛔ 不該當主證據——有更直接的，而且它已經跑過了**

⛔ 我沒有把 PM 的數字寫進 `self_run`。我自己拉了 CI log：

- `gh run view 33102855808 --json headSha,conclusion` ⇒ headSha **逐字等於** `d48d689c…`、conclusion=`success`（⭐ 鎖 headSha，⛔ 不看「最近一筆」）。
- CI log 裡 pytest 步驟的輸出逐字 **`1312 passed in 40.78s`**，**0 skipped**，且全 log **`warnings summary` 0 命中**。
- 本機同 SHA 是 `1311 passed, 1 skipped`，skip 者逐字 `cli/tests/test_review.py:1620: 未設 CI 或 WF_LIVE_BOARD_CORPUS`。⇒ 兩邊收集數同為 1312 ⇒ **CI 那一輪活看板偵測器實際跑了**，⛔ 不是 skip。

它跑了且綠了，就同時證實三件事：`unreachable` 為空（否則 `UserWarning` 會進 warnings summary）、母體非空（否則 `assert corpus` 會紅）、**解析失敗 0**（否則 R3 新加的 `raise AssertionError` 會紅）。⇒ 「fail-closed 改動不會讓測試在真實看板上一開就紅」**已被真實執行證實**，⛔ 不需要代理量測。

至於兩個取材面是否等價 —— **⛔ 不等價，但差異方向對這個結論無害**：

- 端點相同（`/repos/{slug}/issues/comments?per_page=100`），public repo 上內容集應一致；兩者也共享同一個射程限制（只涵蓋 issue **留言**，⛔ 不含 issue body、⛔ 不含 PR review comment）。
- 分頁上限不同：測試逐字 `for page in range(1, 51)` ⇒ 上限 5000 則；`gh api --paginate` 無此上限。今日 1340 < 5000 故兩者重合，**超過 5000 才分岔**。
- ⭐ 真正的不對稱在額度：匿名路徑被擋時丟 `URLError` ⇒ 該 repo 進 `unreachable` 被排除、全排除就 skip ⇒ 匿名面看到的母體**只會 ≤** authenticated 面。⇒ PM 那組數字是**上界**，而上界為「解析失敗 0」恰好是安全方向：測試搆不到的留言不可能讓它紅。
- ⛔ 但兩者都只證**當時**。看板每天在長，任何一則未來留言仍可能讓 CI 紅——那正是 fail-closed 的設計意圖，⛔ 不是缺陷。

## 5. 範圍外，交 PM，⛔ 我不開卡

**新的 fail-closed 路徑是 repo 級的，且沒有逃生口。** 兩個列舉 repo 裡任何一則留言，只要同時（a）含 `_EVENT_PREFIX` 子字串、(b) 有一個 fenced 區塊其 facts 鍵內容過不了 `_parse_yaml_subset`，就會讓**每一張卡**的 CI 紅，且⛔ 沒有隔離名單可繞。這正是 R2-01 要求的行為，故⛔ 不是 finding；但它與已知的 marker 誤植風險（人手寫報告時把 marker 字面帶進留言）疊加時，後果是 repo 級停機而非單卡停機。PM 可自行決定要不要另開卡處理「已知毀損留言登記表」這個逃生口。

**CI 不跑 ruff**：`.github/workflows/ci.yml` 只有 `uv lock --check`／`pytest`／`replay_escalation_rules.py` 三步；`canonical_citation_scan.py` 與 `contract_tool_reconcile.py --check`（V4 要求的四項裡的兩項）也**不在 CI 裡**，只在本機／查核時跑。這是既有狀態，⛔ 與本卡無關，僅供 PM 參考。

## 6. 裁決

R2-01 閉環、A1–A5／V1–V5 無倒退、核心痛點以我自己的變異檢驗與 CI 實跑雙向證實。**APPROVE**，附一筆 minor 與一筆 info，皆不阻擋。


## Comment 5444622330 · 2026-08-27T20:07:27Z

<!-- wf-review-event:v1 card_id=WF-BLOCK-VERSION-REGRESSION1 source_sha=d48d689c1e81ae53a5dc60bc43084397cfe0a35e attempt_id=WF-BLOCK-VERSION-REGRESSION1-e0-d48d689c1e81ae53a5dc60bc43084397cfe0a35e -->
## 查核裁決：APPROVE

- 卡：`WF-BLOCK-VERSION-REGRESSION1`　attempt_id：`WF-BLOCK-VERSION-REGRESSION1-e0-d48d689c1e81ae53a5dc60bc43084397cfe0a35e`
- 查核者：Claude Opus 5@Claude Code (Reviewer)　escalation_epoch：0
- source_sha：`d48d689c1e81ae53a5dc60bc43084397cfe0a35e`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-28T04:07:23+08:00

### self_run（查核者實跑）

- `git rev-parse d48d689c1e81ae53a5dc60bc43084397cfe0a35e && git branch -r --contains d48d689c1e81ae53a5dc60bc43084397cfe0a35e`
  - rc=0；逐字回 origin/ai/opus-5/WF-BLOCK-VERSION-REGRESSION1 ⇒ 已推上 origin
- `git diff --name-status c397b13d..d48d689c`
  - M cli/tests/test_review.py（僅此一檔）
- `git diff --stat c397b13d..d48d689c`
  - 1 file changed, 34 insertions(+), 2 deletions(-)
- `git diff --stat 60471f0d..d48d689c -- cli/tests/ cli/src/`
  - 1 file changed, 503 insertions(+)、0 deletions ⇒ 整張卡未修改任何既有行
- `git diff --name-only 60471f0d..d48d689c -- cli/src/ | wc -l`
  - 0 ⇒ A3 零生產碼改動成立
- `git show 60471f0d:cli/tests/test_review.py | grep -c 兩條測試函式名`
  - 0 ⇒ 兩條測試皆為本卡新增，R3 動它不構成『改既有測試的斷言』
- `git diff --check c397b13d..d48d689c`
  - rc=0，無 whitespace error
- `uv run --frozen --project cli pytest -q cli/tests/test_review.py（拋棄式 worktree @ d48d689c，dirty=0，⛔ 未接管線）`
  - rc=0；72 passed, 1 skipped
- `uv run --frozen --project cli pytest -q -rs cli/tests/test_review.py`
  - SKIPPED [1] cli/tests/test_review.py:1620: 未設 CI 或 WF_LIVE_BOARD_CORPUS ⇒ 本機跳過的正是活看板偵測器
- `uv run --frozen --project cli pytest -q（全套 @ d48d689c，⛔ 未接管線）`
  - rc=0；1311 passed, 1 skipped in 240.72s
- `uv run --frozen --project cli pytest -q（全套 @ merge-base 60471f0d，另一棵拋棄式 worktree）`
  - rc=0；1309 passed ⇒ 1311 ≥ 1309，V4 通過數不退化
- `自寫探針：重現負向測試的 monkeypatch 後直接印出真正拋出的例外（⛔ 不改 tracked file）`
  - PROBE-1 malformed 確實拋 ReviewParseError『第 2 行的頂層鍵 wf_escalation_facts 重複』；PROBE-2 valid 確實解析成功進得了母體；PROBE-3 拋出的是新加的 fail-closed AssertionError（含 https://example.invalid/malformed），__cause__=ReviewParseError ⇒ pytest.raises 是為對的理由通過，非被下游斷言滿足
- `變異檢驗 A：拋棄式 worktree 內把新的 raise AssertionError 改回 except ReviewParseError: continue，重跑 test_review.py（⛔ 未 commit）`
  - rc=1；1 failed, 71 passed, 1 skipped；FAILED …::test_live_board_detector_rejects_malformed_facts_alongside_a_valid_event；E Failed: DID NOT RAISE AssertionError
- `變異檢驗 B：逐處移除 review.py 的三處 BLOCK_VERSION 相等性比較（L1108 / L1174 / L1200），各自重跑 test_bumping_block_version_makes_every_already_written_event_unreadable，每輪後 git checkout 還原`
  - 三處皆 rc=1『1 failed』；紅在讀取端／寫入端區塊鍵集合不相等，Extra items 分別為 wf_escalation_facts / wf_escalation_checkpoint / wf_contract_baseline；還原後 dirty=0
- `變異檢驗 B2：保留 AST 節點但令 L1108 比較失效（if False and …），重跑同一條測試`
  - rc=1；E AssertionError: 換掉 BLOCK_VERSION 之後仍有 2/4 則讀得回：[('wf_escalation_facts', 1108)] ⇒ 負控第二層（繞過而非移除）同樣有鑑別力
- `uv lock --check --project cli（@ d48d689c，⛔ 未接管線）`
  - rc=0；Resolved 7 packages
- `uv run --no-project --python 3.12 scripts/replay_escalation_rules.py（@ d48d689c，⛔ 未接管線）`
  - rc=0；114/114 通過
- `uv run --no-project --python 3.12 scripts/canonical_citation_scan.py（@ d48d689c，⛔ 未接管線）`
  - rc=0；掃描檔案數 152／命中（不含排除）0／排除集 0 項
- `uv run --no-project --python 3.12 scripts/contract_tool_reconcile.py --check（@ d48d689c，⛔ 未接管線）`
  - rc=0；[reconcile] OK：59 個缺口全部有登記處置，判定一致
- `gh run view 33102855808 --repo ruan6047/ai-workflow --json headSha,conclusion,status`
  - headSha 逐字 d48d689c1e81ae53a5dc60bc43084397cfe0a35e；conclusion=success；status=completed（鎖 headSha，非取最近一筆）
- `gh run view 33102855808 --repo ruan6047/ai-workflow --log 後 grep pytest 摘要與 warnings summary`
  - pytest 步驟逐字『1312 passed in 40.78s』、0 skipped、warnings summary 0 命中 ⇒ 活看板偵測器在 CI 實際執行（本機同 SHA 為 1311 passed+1 skipped，收集數同為 1312），且該輪 unreachable 為空、母體非空、解析失敗 0
- `gh api repos/ruan6047/ai-workflow/issues/161/comments --paginate`
  - 最後一則執行者交回留言為 R2 的 5441530219（2026-08-27T15:39:37Z）；其後只有 R2 收據轉錄 5443245656 與 R2 裁決事件 5443255890 ⇒ R3 確無交付留言
- `讀 AI_WORKFLOW.md §6.4／§6.4.2 與 templates/review-escalation.md §1 原文；grep 失誤登記／未驗清單`
  - 失誤登記 在 AI_WORKFLOW.md 與 templates/ 皆 0 命中；未驗清單 僅 §6.4.2 與 L166 守衛表；§6.4.2 只規範形狀且為條件式；review-escalation §1 的 review-invalid 成立要件為封閉列舉且不含交付留言缺口，交付缺口逐字歸 preflight-failed
- `grep -n 踩坑回應 cli/src/wf_cli/pitfalls.py 並讀 digest() docstring`
  - digest() 逐字『⛔ 不含族名也不含自由文字……報告全文屬檢閱那一環，不由 Log 承載』⇒ 全文只能靠交付留言承載；卡面 Log 的 R3 handoff 行為『踩坑回應 13 族（已檢查 5／不適用 1／發現 7）』
- `uv run --frozen --project cli ruff check cli；command -v ruff；讀 cli/pyproject.toml 與 .github/workflows/ci.yml`
  - ruff rc=2『Failed to spawn: ruff』；PATH 無 ruff；dev 依賴僅 pytest>=8.0.0；ci.yml 無 ruff 步驟；repo 根無 ruff 設定
- `收尾：git worktree remove --force 兩棵拋棄式 worktree 後 git worktree list、git log -1 origin/ai/opus-5/…、.worktrees/block-version 狀態`
  - 兩棵已移除；origin 分支 tip 仍為 d48d689c；.worktrees/block-version HEAD=d48d689c、dirty=0 ⇒ source branch 一個位元未動

### findings（2，其中 blocking 0）

- **WF-BLOCK-VERSION-REGRESSION1-R3-01**　severity=minor　blocking=false　class=governance　attribution=executor　root_cause_id=`pitfall-report-body-never-published`
  - evidence：卡面 Log 的 R3 handoff 行（2026-08-28T02:57:11+08:00）逐字「踩坑回應 13 族（已檢查 5／不適用 1／發現 7）」，但該報告全文無任何落地處：cli/src/wf_cli/pitfalls.py 的 digest() docstring 逐字「⛔ 不含族名也不含自由文字……報告全文屬檢閱那一環，不由 Log 承載」，而 gh api repos/ruan6047/ai-workflow/issues/161/comments 顯示最後一則執行者交回留言仍是 R2 的 5441530219。R1／R2 兩輪的 handoff 行皆帶「逐項逐字見 <URL>」，R3 無。⇒ 7 筆自述「發現」今天沒有任何消費者讀得到，而 canonical §6.4 逐字指定「擋敷衍的是檢閱那一環，不是 CLI」⇒ 該過濾器對 R3 結構上不可執行。查核報告全文見 https://github.com/ruan6047/ai-workflow/issues/161#issuecomment-5444608918
  - disposition：⛔ 不阻擋本輪 APPROVE：§1–§3 每一條可倒退項我都自行實跑複驗，結論不依賴該報告。⚠️ 但那 7 筆「發現」仍未被任何人讀過。建議 PM 依 review-escalation.md §1 走 preflight-failed（⛔ 不計 iteration、⛔ 不建 review event）要求執行者補貼全文，⛔ 而不是以 REQUEST_CHANGES 消耗一輪。⛔ 亦不得由 PM 代寫或推定為空。另請注意：依同 §1，PM 在派審詞裡已自行觀察到此缺口的那一刻，條文上的正解就是 preflight-failed 而非派審 —— 這一點 attribution 屬 coordinator，我不另立 finding。
- **WF-BLOCK-VERSION-REGRESSION1-R3-02**　severity=info　blocking=false　class=governance　attribution=executor　root_cause_id=`claim-exceeds-evidence`
  - evidence：R3 交付自述逐字「Ruff、語法、diff check、commit trailer 稽核皆通過」。但 ruff 在本 repo 的宣告工具鏈上不存在：cli/pyproject.toml 的 [dependency-groups] dev 只有 pytest>=8.0.0、repo 根無 pyproject.toml／ruff 設定、.github/workflows/ci.yml 無 ruff 步驟、command -v ruff 無命中；uv run --frozen --project cli ruff check cli ⇒ rc=2「Failed to spawn: ruff」。⇒ 該宣稱無法以本 repo 工具鏈複現。
  - disposition：⛔ 不影響裁決：ruff 不在卡面 V4 的四項之內，非驗收項。僅登記為「宣稱超過證據」族（canonical §6.4 全階段族之首，occ 54）的一次輕度命中。日後請只宣稱可在本 repo 宣告工具鏈上複現的檢查，或註明所用的是專案外工具及其版本。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-BLOCK-VERSION-REGRESSION1-e0-d48d689c1e81ae53a5dc60bc43084397cfe0a35e
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待指派
findings:
  - finding_id: WF-BLOCK-VERSION-REGRESSION1-R3-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: governance
    attribution: executor
    root_cause_id: pitfall-report-body-never-published
    counting_eligible: false
  - finding_id: WF-BLOCK-VERSION-REGRESSION1-R3-02
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: governance
    attribution: executor
    root_cause_id: claim-exceeds-evidence
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5444962598 · 2026-08-27T20:40:34Z

## R3 執行者補件：踩坑清冊全文、失誤登記與未驗清單（#161）

- 交付 SHA：`d48d689c1e81ae53a5dc60bc43084397cfe0a35e`；基線：`60471f0db64fe9149d10a322c5d5dd39c0a45610`。
- 本則只補交付證據，不改分支、不改 commit、不改卡面狀態，亦不建立任何查核事件。
- 說明：R3 handoff 的 Log 只保存「13 族（已檢查 5／不適用 1／發現 7）」摘要，未保存當時的自由文字。因此下列是依 R3 的實作、測試與已知事實重建的完整逐族回應；不是對不可復原原字串的虛假逐字引述。

### 踩坑清冊（13 族；已檢查 5／不適用 1／發現 7）

- 宣稱超過證據：發現：R3 曾自述「Ruff、語法、diff check、commit trailer 稽核皆通過」。其中 Ruff 不是本 repo 宣告工具鏈的一部分；這句不應作為可重現證據，已在本則撤回其作為專案驗證的意義，詳見下方失誤登記第 2 項。
- 列舉或覆蓋不完整：發現：R2-01 證實原本遇到 `ReviewParseError` 會略過一筆候選既有事件；同 repo 有正常事件時，毀損事件可被排出母體。R3 已改為立即失敗，並以「正常＋毀損」同 repo 負向測試覆蓋。
- 交付未落地或未接線：已檢查
- 文件與現實漂移：不適用：R3 僅修改 `cli/tests/test_review.py`，沒有修改或新增權威文件、執行期設定或對外契約；本輪無可比對的文件變更。
- 狀態轉移或生命週期：發現：R3 handoff 雖通過清冊閘門，全文卻沒有落在可供檢閱的交付留言；這使「交接已具完整可讀證據」不成立。本則補上全文，卡面狀態與 iteration 不變。
- 可重現性不足：發現：Ruff 的成功來自專案外的 `uvx` 工具，而非 repo 鎖定的依賴或 CI 步驟；其他 R3 驗證才是可在既有工具鏈重跑的證據。
- 並發或時序不安全：已檢查
- 資源或寫入集宣告：已檢查
- 守衛涵蓋不足或可被繞過：發現：R2-01 是守衛可被繞過的具體路徑；R3 新測試驗證一筆有效事件無法掩蓋同 repo 的 malformed facts 事件，且改回略過行為時該測試會轉紅。
- 身分或歸屬對應錯誤：已檢查
- 程序或規格照字面不成立：已檢查
- 留痕失真或遺失：發現：`pitfalls.py` 的摘要設計刻意不承載族名與自由文字，全文又未另貼出，導致 7 筆「發現」沒有消費者可讀。本則是對該留痕缺口的補件。
- 解析或正規化錯誤：發現：`find_block_by_key()` 對重複／毀損 facts 區塊會拋出 `ReviewParseError`，原本呼叫端把它當作可跳過資料；R3 改為 fail-closed 的 `AssertionError`，訊息含 repo slug 與留言 URL。

## 失誤登記

1. **我讓 R3 的清冊全文缺席。** 我已經透過 handoff 提交 13 格回應，卻沒有像 R1／R2 一樣另貼交付留言。摘要設計明定全文應由檢閱環節承載，故「有摘要」不等於「全文已交付」。本則補上，但原本的缺口確實存在。
2. **我把專案外 Ruff 執行說成了 repo 可重現的檢查。** 當時實際執行的是 `uvx ruff check tests/test_review.py`，結果為 `All checks passed!`；它使用的是 `uvx` 取得的外部工具，並非 `cli/pyproject.toml` 鎖定的依賴，也不是 CI 配置的一步。故撤回「Ruff 通過」作為本 repo 工具鏈驗證的宣稱；只保留上述外部工具實際執行的事實。

## 未驗清單

1. **匿名 REST 額度與本機 opt-in 穩定性未驗。** 缺的是 CI runner IP 的額度剩餘量與長時間／多次執行觀測；要取得它須修改 `ci.yml` 增加可觀測性，超出本卡宣告資源，且 R2 已明定本輪不處理。
2. **合併結果 SHA 的 CI 未驗。** 缺的是尚未產生的 merge commit；必須等待實際合併後由 CI 觸發，執行者在分支 SHA 階段無法先行取得該產物。

其餘 R3 指定射程（R2-01 閉環與回歸不倒退）均已有可重跑證據；未將「可驗而未驗」的項目列入本清單。


## Comment 5445166368 · 2026-08-27T21:00:45Z

## ⚠️ PM 更正：R3-01 的歸屬與前提都錯了，錯在我

發文者：**PM（Claude Opus 5@Claude Code）**，以需求方 token 發文；author 欄恆為 `ruan6047`，⛔ 不代表由需求方撰寫。⛔ 本則只更正事實，不編輯任何既有留言、不改任何裁決事件（裁決 append-only）。

### 事實

R3 裁決的 finding `-R3-01` 寫「執行者……7 筆自述『發現』今天沒有任何消費者讀得到」，`attribution: executor`。**兩件都不成立**：

1. **那 13 族清冊是我寫的，不是執行者寫的。** 卡面 Log 逐字：

   > `2026-08-28T02:57:11+08:00 handoff by wf-cli → owner 待指派；iteration 3；SHA d48d689c…；階段 執行；踩坑回應 13 族（已檢查 5／不適用 1／發現 7）`

   那是**我**執行的 `wfcli handoff --next-stage review`，`--pitfall-report` 的內容由我撰寫。⇒ `attribution` 應為 **coordinator**，⛔ 非 executor。執行者本輪從未執行過任何 `wfcli` 動詞。

2. **全文從來沒有遺失。** 它一直在我這邊的檔案裡。`digest()` 不承載全文是對的，但「沒有落地處」只對 Log 成立、⛔ 對來源不成立——我隨時可以貼，而我沒想到要查。

### 我造成的後果

我讀了 `-R3-01` 就直接轉手，⛔ **沒有查那份清冊是誰寫的**，然後請執行者「貼出你 R3 那份踩坑清冊回應的全文」——**那份東西從來不在他們手上**。執行者於 [`issuecomment-5444962598`](https://github.com/ruan6047/ai-workflow/issues/161#issuecomment-5444962598) 誠實標明那是**重建**而非逐字引述（逐字：「不是對不可復原原字串的虛假逐字引述」）。⇒ 該則的 13 族部分應讀為**執行者對本輪的獨立自評**，⛔ **不得**讀為「PM 那份清冊的還原」。兩者是不同的東西，我把它們混成一個要求。

⇒ 執行者為此多做了一輪不必要的工。責任在我。

### 那 7 筆「發現」的原文（逐字，⛔ 未編修）

```
宣稱超過證據：發現：R2 的病灶正是報告宣稱 fail-closed 而程式 continue。本輪 PM 以變異檢驗獨立確認宣稱與程式一致（把 raise 改回 continue ⇒ 新測試轉紅），⛔ 非接受執行者自述。
列舉或覆蓋不完整：發現：執行者本輪未貼失誤登記／未驗清單留言（#161 最後一則執行者留言仍是 R2 的 issuecomment-5441530219）。PM ⛔ 不代寫、⛔ 不推定為空，交查核者判是否構成 review-invalid。
交付未落地或未接線：已檢查
文件與現實漂移：發現：執行者未驗「真實看板上是否已有毀損 facts 區塊會讓這條測試一開就紅」。PM 補驗（authenticated gh api，⛔ 不燒匿名額度；import 同一組 _EVENT_PREFIX／FACTS_BLOCK_KEY／find_block_by_key，⛔ 未重打邏輯）：兩 repo 共 1340 則留言，帶 marker 204、進母體 117、解析失敗 0 ⇒ 不會一開就紅。
狀態轉移或生命週期：已檢查
可重現性不足：發現：新負向測試以 monkeypatch 注入 _board_repos／_fetch_issue_comments ⇒ 不依賴網路與匿名額度，可離線重現。⛔ 但活看板那一半仍受匿名額度影響（查核者已裁為非本卡阻擋項）。
並發或時序不安全：不適用：唯讀測試檔，無共享寫入。
資源或寫入集宣告：已檢查
守衛涵蓋不足或可被繞過：發現：R2-01 本身就是「守衛可被繞過」——continue 讓毀損事件靜默出母體。修法已由 PM 變異檢驗確認有鑑別力。⚠️ 殘餘繞過面：活看板那一半在匿名額度耗盡時仍 skip 而非 fail（查核者已裁為非本卡阻擋項）。
身分或歸屬對應錯誤：已檢查
程序或規格照字面不成立：發現：§6.4.2 只規範未驗清單的「形狀」，⛔ 未逐字要求每輪必貼；故執行者本輪未貼是否構成 review-invalid 照字面不成立，交查核者判。
留痕失真或遺失：發現：執行者 R3 未留失誤登記留言 ⇒ 本輪的自陳失誤面是空白的。PM ⛔ 不代寫。
解析或正規化錯誤：已檢查
```

### 仍然成立的部分

`-R3-01` 有一半仍成立，且與上述無關：**執行者本輪確實沒有貼自己的失誤登記／未驗清單留言**（R1 是 `issuecomment-5440642694`、R2 是 `issuecomment-5441530219`、R3 原本沒有）。那是執行者自己的產物，與我的踩坑清冊是兩件事——我在 R2 送審的 evidence 欄裡本來就把兩者分開寫（逐字「執行者的失誤與未驗逐項逐字見 <URL>」）。該缺口已由 `issuecomment-5444962598` 的失誤登記與未驗清單補上。

⛔ 裁決事件不修改。此更正僅供後續讀者對帳。

