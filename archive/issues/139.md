# #139 WF-CARD-BODY-BUDGET1 amend 寫入路徑上的卡面容量預算：量測、預警、硬線，並以指紋取代 Log 全文重複
- state: closed  created: 2026-08-25T08:21:25Z  closed: 2026-08-25T17:02:31Z
- url: https://github.com/ruan6047/ai-workflow/issues/139
- comments: 9

## Body

- 需求：ruan6047　規劃：—
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；改動唯一寫入通道的 Log 產生邏輯，須同時處理「平台有前一版」與「沒有前一版」兩條路徑；邏輯不深但錯了會靜默損失還原點，需要主力型的謹慎度。）　查核：待指派（建議 高階型；查核要判定的是「Log 由全文改為指紋後，歷史是否仍可證明地回得去」——這需要獨立驗證 userContentEdits 的保存語意（含 totalCount=0 的卡），⛔ 不能只讀測試。屬紅線等級（唯一寫入通道 + 潛在不可逆），須跨家族查核。）
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：ROADMAP §0 目標 1「防止低級事故」——其判準逐字為「**有機械執行者會擋下它。沒有執行者的偵測器不算達成**」。⇒ 本卡的檢查必須落在 amend 的**寫入路徑**上，⛔ 不是 doctor 的事後報告。

## 簡介
<!-- card-brief:begin -->
為 wfcli 的唯一寫入通道加上卡面容量的量測、預警與硬線，並移除 Log 的全文重複成本。**適用時機**：amend 會改動卡面欄位、需要知道「這次付多少、還能改幾次」時；以及要判斷某張卡是否已接近不可寫時。⛔ 非射程：不做卡面內容瘦身（那是逐卡的編輯判斷）、不改 GitHub 的上限、不動 doctor 的既有掃描、不處理已撞上限之卡的救援程序（`#105` 已個案處理完畢）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：`wfcli amend` 每次寫入都把「異動欄位的**舊值全文＋新值全文**」寫進 Log（`amend_cmd.py:406` `_fold` 逐字：「原值摺成一行——但**不截斷**：Log 是唯一還原點」），⇒ 卡面 body 以 Σ(2×欄位大小) **單調成長**，而 GitHub issue body 有硬上限（實測落在 129,486–130,018 之間，⛔ 非文件所載 65,536）。撞上時該卡的**所有** wfcli 動詞同時失效。⚠️ 2026-08-25 `aiwf#105` 實際撞上：body 129,651、Log 佔 96.7%、amend 25 次，需求方必須手動 `gh issue edit --body-file` 才救得回——即繞過唯一寫入通道。而 CLI **全域沒有任何一處量測卡面大小**（`grep -E 'len\(.*body.*\)|MAX_BODY|too long|65536'` 在 `src/wf_cli/` 唯一命中是 `doctor.py:237` 的 findings 計數）⇒ 撞上之前零預警。⭐ 且 `_fold` 賴以成立的前提已被推翻：GitHub `userContentEdits` 保有每一版**逐位元相同**的完整 body（2026-08-25 實測 `#105` 截斷前後 sha256 相符、`#138` 11 版），⇒ Log 並非唯一還原點。⭐ 失效模式**選擇討論最多的卡**：amend 次數越多離上限越近 ⇒ 最關鍵的卡最先失效。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/amend_cmd.py",
    "file:cli/tests/test_commands_mocked.py",
    "file:docs/CONTRACT_TOOL_RECONCILE.md",
    "file:cli/tests/fake_gh.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] ⚠️ 理由與量測全在研究輪 comment（輪1 https://github.com/ruan6047/ai-workflow/issues/139#issuecomment-5407536225／輪2 https://github.com/ruan6047/ai-workflow/issues/139#issuecomment-5407562522），⛔ 卡面只寫判準。
- [ ] A1 Log 條目改為只記 `op｜欄位名｜舊值指紋｜新值指紋｜reason`；指紋＝`sha256` 全長＋位元組數。⛔ 不含任何欄位全文。
- [ ] A2 ⛔ **硬性例外，一律退回寫全文**：(a) `item.content_type != "Issue"`（實測 `DraftIssue` 型別上無 `userContentEdits` ⇒ 平台零保存）；(b) 該卡 `userContentEdits.totalCount == 0`（首寫，無前一版）。兩條各須有獨立測試。
- [ ] A3 例外判定必須是**寫入前實查**，⛔ 不得以 `--repo` 是否給定或卡片來源推定 content_type。
- [ ] A4 amend 每次（含 `--dry-run`）印出預算行：本次寫入位元組數／寫入後 body 大小／餘裕／`還能改 ≈ N 次`。N = 餘裕 ÷ 本次成本，⛔ 無資料時印「—」不印 0。
- [ ] A5 `LIMIT` 取實測下界 **129,486**，並在原始碼註解記下實測區間 (129,486, ~130,018) 與取樣日期。⛔ 不得寫 65,536。
- [ ] A6 軟門檻（餘裕 < 20,000）輸出警告但**放行**；硬線（寫入後 ≥ LIMIT）**拒絕寫入**並回非零 rc，訊息須指出可壓縮的最大欄位名與其大小。
- [ ] A7 ⛔ 不做任何自動瘦身、不改既有卡的 Log、不對既有卡做遷移——本卡只改**今後**的寫入行為。
- [ ] A8 ⚠️ 交付須逐字載明代價：Log 由自足變為依賴平台，離線讀 Log（匯出／封存／repo 遷移）只會拿到指紋；遷離 GitHub 前須先全量匯出版本。⛔ 不得描述為零成本。
- [ ] A9 ⚠️ **本卡最大未證實假設**：`userContentEdits` 是否有保存上限。實測最高 39 版全數取得（`#130`），⛔ 39 以上未驗。執行者須提出實測（找到或構造 >39 版的卡）或官方文件保證；⛔ 兩者皆無則 A1 不得實作，退回只做 A4–A6。
- [ ] A10 硬線拒絕不得使卡進入不可修復狀態：拒絕時須同時印出「本卡已達上限」的處置路徑，且該路徑在 `#105` 的實際救援程序上驗證過。
- [ ] A11 回歸基線逐字記錄（跑前跑後的 passed 數），⛔ 不得只寫「全過」。
- [ ] A12 ⛔ 授權邊界：發現須改本卡未宣告的檔即停、寫阻塞發現、交需求方裁決（canonical §3.2）。

## 驗證

- [ ] V1 端到端：對一張真實 Issue 卡跑 amend，讀回 body 驗證 Log 新增行**不含**舊值任何一段連續 20 字元。
- [ ] V2 端到端：同一張卡連跑兩次 amend，驗證 `userContentEdits.totalCount` 增加，且第 k 版重算出的 sha256 == Log 中對應欄位的舊值指紋。⭐ 這是「歷史仍可證明地回得去」的核心證據。⚠️ **⛔ 增量不必然是 +2**：實測 `aiwf#142`（`totalCount` 原為 0）兩次 amend 後為 **3**——建立那一筆是**首次編輯之後才追溯出現**的。⇒ 判準是「每次 body 寫入各留一版」，⛔ 不是固定的 +2。⚠️ 重算舊值時必須照 `card._amend_checklist` 的 `old_repr` 規則（`「；」.join(f"[{s}] {t}")`，**保留勾選狀態前綴**）；剝掉 `- [ ] ` 會每項少 4 字元、指紋必然對不上——PM 2026-08-25 驗證時即因此誤判一次。
- [ ] V3 例外路徑 (a)：對 `content_type == "DraftIssue"` 的 item 跑 amend，驗證 Log **寫入全文**。⚠️ 須用真實 draft item（Project 4 現有 0 張，須自建 throwaway），⛔ 不接受 mock。
- [ ] V4 例外路徑 (b)：對 `totalCount == 0` 的新卡首次 amend，驗證寫入全文。
- [ ] V5 硬線：構造一張逼近 LIMIT 的卡，驗證 amend 回非零 rc、body 未被改動（讀回比對逐位元相同）。
- [ ] V6 軟門檻：驗證警告出現但 rc == 0 且寫入成功。
- [ ] V7 預算行的算術：以已知大小的欄位做一次 amend，人工核對印出的四個數字。
- [ ] V8 ⚠️ 真實樣本，⛔ 不自造：取三張既有卡（至少一張終態、一張 Log > 30,000）跑 `--dry-run`，驗證預算行對每一張都印得出來且數字與獨立量測相符。
- [ ] V9 變異檢驗：把 A2 的兩條例外各自反注（改成不觸發），驗證 V3／V4 各自轉紅。⛔ 只跑正向不算驗過。
- [ ] V10 A9 的結論（有無保存上限）須附可重現的取證指令與輸出，⛔ 不接受「查過了」。

## Log

- 2026-08-25T16:21:24+08:00 open by —；owner 待指派；iteration 0。
- 2026-08-25T16:26:17+08:00 amend by wf-cli（op a1e17228）→ 驗收條件：原值「[ ] TODO：填入可獨立驗證的條件」→ 新值「⚠️ 理由與量測全在研究輪 comment（輪1 https://github.com/ruan6047/ai-workflow/issues/139#issuecomment-5407536225／輪2 https://github.com/ruan6047/ai-workflow/issues/139#issuecomment-5407562522），⛔ 卡面只寫判準。；A1 Log 條目改為只記 `op｜欄位名｜舊值指紋｜新值指紋｜reason`；指紋＝`sha256` 全長＋位元組數。⛔ 不含任何欄位全文。；A2 ⛔ **硬性例外，一律退回寫全文**：(a) `item.content_type != "Issue"`（實測 `DraftIssue` 型別上無 `userContentEdits` ⇒ 平台零保存）；(b) 該卡 `userContentEdits.totalCount == 0`（首寫，無前一版）。兩條各須有獨立測試。；A3 例外判定必須是**寫入前實查**，⛔ 不得以 `--repo` 是否給定或卡片來源推定 content_type。；A4 amend 每次（含 `--dry-run`）印出預算行：本次寫入位元組數／寫入後 body 大小／餘裕／`還能改 ≈ N 次`。N = 餘裕 ÷ 本次成本，⛔ 無資料時印「—」不印 0。；A5 `LIMIT` 取實測下界 **129,486**，並在原始碼註解記下實測區間 (129,486, ~130,018) 與取樣日期。⛔ 不得寫 65,536。；A6 軟門檻（餘裕 < 20,000）輸出警告但**放行**；硬線（寫入後 ≥ LIMIT）**拒絕寫入**並回非零 rc，訊息須指出可壓縮的最大欄位名與其大小。；A7 ⛔ 不做任何自動瘦身、不改既有卡的 Log、不對既有卡做遷移——本卡只改**今後**的寫入行為。；A8 ⚠️ 交付須逐字載明代價：Log 由自足變為依賴平台，離線讀 Log（匯出／封存／repo 遷移）只會拿到指紋；遷離 GitHub 前須先全量匯出版本。⛔ 不得描述為零成本。；A9 ⚠️ **本卡最大未證實假設**：`userContentEdits` 是否有保存上限。實測最高 39 版全數取得（`#130`），⛔ 39 以上未驗。執行者須提出實測（找到或構造 >39 版的卡）或官方文件保證；⛔ 兩者皆無則 A1 不得實作，退回只做 A4–A6。；A10 硬線拒絕不得使卡進入不可修復狀態：拒絕時須同時印出「本卡已達上限」的處置路徑，且該路徑在 `#105` 的實際救援程序上驗證過。；A11 回歸基線逐字記錄（跑前跑後的 passed 數），⛔ 不得只寫「全過」。；A12 ⛔ 授權邊界：發現須改本卡未宣告的檔即停、寫阻塞發現、交需求方裁決（canonical §3.2）。」；理由 規劃輪：依研究輪 1／2 的實測寫入驗收與驗證。⭐ 相對開卡時的提案有一項實質改變——Log 連**新值**也不寫（新值就在正上方的欄位裡），⇒ 成長律由 O(2×欄位大小) 降為 O(1)。⚠️ 並新增兩條硬性例外（DraftIssue 無 userContentEdits／首寫無前一版）與一條未證實假設（版本保存上限，實測僅到 39）。理由全文見 https://github.com/ruan6047/ai-workflow/issues/139#issuecomment-5407562522。。
- 2026-08-25T16:26:17+08:00 amend by wf-cli（op a1e17228）→ 驗證：原值「[ ] TODO：填入驗證指令與證據要求」→ 新值「V1 端到端：對一張真實 Issue 卡跑 amend，讀回 body 驗證 Log 新增行**不含**舊值任何一段連續 20 字元。；V2 端到端：同一張卡連跑兩次 amend，驗證平台版本數 +2，且第 k 版 sha256 == Log 中對應的舊值指紋。⭐ 這是「歷史仍可證明地回得去」的核心證據。；V3 例外路徑 (a)：對 `content_type == "DraftIssue"` 的 item 跑 amend，驗證 Log **寫入全文**。⚠️ 須用真實 draft item（Project 4 現有 0 張，須自建 throwaway），⛔ 不接受 mock。；V4 例外路徑 (b)：對 `totalCount == 0` 的新卡首次 amend，驗證寫入全文。；V5 硬線：構造一張逼近 LIMIT 的卡，驗證 amend 回非零 rc、body 未被改動（讀回比對逐位元相同）。；V6 軟門檻：驗證警告出現但 rc == 0 且寫入成功。；V7 預算行的算術：以已知大小的欄位做一次 amend，人工核對印出的四個數字。；V8 ⚠️ 真實樣本，⛔ 不自造：取三張既有卡（至少一張終態、一張 Log > 30,000）跑 `--dry-run`，驗證預算行對每一張都印得出來且數字與獨立量測相符。；V9 變異檢驗：把 A2 的兩條例外各自反注（改成不觸發），驗證 V3／V4 各自轉紅。⛔ 只跑正向不算驗過。；V10 A9 的結論（有無保存上限）須附可重現的取證指令與輸出，⛔ 不接受「查過了」。」；理由 規劃輪：依研究輪 1／2 的實測寫入驗收與驗證。⭐ 相對開卡時的提案有一項實質改變——Log 連**新值**也不寫（新值就在正上方的欄位裡），⇒ 成長律由 O(2×欄位大小) 降為 O(1)。⚠️ 並新增兩條硬性例外（DraftIssue 無 userContentEdits／首寫無前一版）與一條未證實假設（版本保存上限，實測僅到 39）。理由全文見 https://github.com/ruan6047/ai-workflow/issues/139#issuecomment-5407562522。。
- 2026-08-25T17:01:58+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (PM)；iteration 0；SHA d4ba7ce5f3fa526fc3a7aa0ebbeee3c926e5eb28；證據 研究輪 1（量測：成長律 Σ(2×欄位)、母體 193 張 body 中位數 4,116、上限實測區間 129,486–130,018、觀測面零命中）issuecomment-5407536225；研究輪 2（DraftIssue 無 userContentEdits／量測零成本／版本保存實測至 39 版／新值亦冗餘⇒O(1)）issuecomment-5407562522。
- 2026-08-25T17:02:26+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (PM)；iteration 0；SHA d4ba7ce5f3fa526fc3a7aa0ebbeee3c926e5eb28；證據 規劃：驗收 A1–A12＋驗證 V1–V10 已填實（amend op a1e17228）；canonical §6.4.1 兩欄於離開規劃前填實成立。
- 2026-08-25T17:02:54+08:00 handoff by wf-cli → owner 待認領；iteration 0；SHA d4ba7ce5f3fa526fc3a7aa0ebbeee3c926e5eb28；證據 T3 閘門：需求方 2026-08-25 逐字裁定「兩個都好」放行；裁定與三項約束見 issuecomment-5407996986（含轉錄聲明）。
- 2026-08-25T22:46:01+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree ai/opus-5/WF-CARD-BODY-BUDGET1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/card-body-budget1；交付狀態 🔨執行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-25T23:16:26+08:00 amend by wf-cli（op 692fd2a8）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/commands/amend_cmd.py", "file:cli/tests/test_commands_mocked.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/commands/amend_cmd.py、file:cli/tests/test_commands_mocked.py、file:docs/CONTRACT_TOOL_RECONCILE.md、file:cli/tests/fake_gh.py」；理由 需求方 2026-08-25 授權擴充資源宣告，兩個新檔皆經查無非終態卡宣告。⭐ 理由一：本卡的 _largest_field_hint 讀取 ## Log 區段以指出最大可壓縮章節 ⇒ 把 card_field/Log 由 write-only 變成 ok，契約對帳 test_live_dispositions_cover_every_gap 因此判「登記了已不存在的缺口」——那是本卡造成的正面效果，處置表須同步，而該表在 docs/CONTRACT_TOOL_RECONCILE.md。⭐ 理由二：_prior_revision_recoverable 走 runner.graphql 查 userContentEdits，FakeGhRunner 認不得該 query 形狀會拋 AssertionError ⇒ 被 except 吞掉後回傳 False ⇒ **所有 mocked 測試都走全文退路、指紋路徑一次都不會被跑到**（＝守衛在測試裡從不執行）。要讓 V1–V10 真的驗到指紋路徑，必須教 FakeGhRunner 認得該形狀。⛔ 原宣告只有兩個檔，這兩處都在射程外，故停下來請裁定而非逕行修改。。
- 2026-08-26T00:08:56+08:00 amend by wf-cli（op d7a07151）→ 驗證：原值指紋 sha256:65a4f01d33cdd063542fbaea8cb1dcd2c2df2842fcb9e9221a5ed6216a5fafcf (1432 bytes) → 新值指紋 sha256:cb12351d21064b3117315f680431a390321efd4b502903bdfd207f4d3772088b (1942 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 ⛔ 更正 V2 的措辭：原寫「驗證平台版本數 +2」，而實測 aiwf#142（totalCount 原為 0）兩次 amend 後為 3——建立那一筆是首次編輯後才追溯出現。⇒ 判準改為「每次 body 寫入各留一版」。並補上重算舊值時必須照 card._amend_checklist 的 old_repr 規則（保留勾選狀態前綴），PM 驗證時曾因剝掉 `- [ ] ` 而誤判一次（每項少 4 字元，與差距 28／24 完全吻合）。。
- 2026-08-26T00:17:33+08:00 handoff by wf-cli → owner GPT-5@Codex（跨家族查核）；iteration 0；SHA d2d2ee95b12d237172cf2bcd2b681486e0ac9af5；證據 A1–A12／V1–V10 完成，三個 commit。⭐ 自審兩輪抓到五件並全部修掉：(1) **單位錯了**——BODY_LIMIT 的 129,651 是字元而實作用位元組，對中文卡面提早約 3 倍觸發；決定性反例 aiwf#130 字元 74,894／位元組 156,942 且真實存在（V8 用真實卡逼出，所有 mock 測試都用 ASCII 碰不到）；(2) 硬線把「正在做的壓縮修復」擋成錯誤指引，已依 cost 正負分流；(3) A2(a) DraftIssue 那條沒有獨立測試（卡面逐字要求「兩條各須有獨立測試」）；(4) A4 超限時印 0 而卡面逐字「不印 0」；(5) A6 差一位（卡面 ≥ LIMIT，我寫 > LIMIT）與 A10 撐大分支未印處置路徑。V1/V2/V3/V8 全部在真實卡上跑，V3 另建拋棄式 DraftIssue（依 canonical §6.4.2「驗得了但沒驗＝替代勞動」，需求方 2026-08-26 授權）。回歸 1158→1170 passed。⚠️ 已知代價：Log 由自足變依賴平台。⚠️ 執行者失誤登記見 commit 訊息與 issuecomment-5413261050／-5413326313。。
- 2026-08-26T00:28:49+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex；core_pain_resolved yes；self_run 5 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-CARD-BODY-BUDGET1-e0-d2d2ee95b12d237172cf2bcd2b681486e0ac9af5。
- 2026-08-26T00:29:38+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 1；SHA d2d2ee95b12d237172cf2bcd2b681486e0ac9af5；證據 接回修 R1-001（major、blocking）。已逐字重現：同一次 dry-run 輸出同時出現「Log 記法：指紋（totalCount=9，最新一版可取得）」與舊值摘要「（全文 1250 字，見 Log）」——而指紋路徑的 Log 只有 sha256，⇒「見 Log」是錯誤的還原指引。並確認 _fold 的 docstring 仍逐字寫「Log 是唯一還原點」，那正是本卡推翻的前提、我改了行為卻沒改它。。
- 2026-08-26T00:43:50+08:00 handoff by wf-cli → owner GPT-5@Codex（跨家族查核）；iteration 1；SHA d05f8eccc957fa2a860ef92df5f9fdf16c955b25；證據 R2：R1-001 已閉環（_short 依實際路徑給還原指引、_fold docstring 更正），三條變異各自轉紅。⭐ 自審另抓到同族兩處查核者未點到（add_parser 的 help 逐字「原值寫入 Log」、模組 docstring 逐字「唯一還原點，摘要不能取代全文」），已修並加掃全檔使用者可見字串的測試（含負控）。回歸 1170→1174 passed，ruff 兩檔皆回 baseline。⚠️ 兩件射程外登記：canonical §6.3「今天沒有任何卡符合」已過期（實測 8/8 通過 brief.validate_shape）；test_commands_mocked.py 被 6 張非終態卡共同宣告、是派工熱點。。
- 2026-08-26T00:57:42+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex；core_pain_resolved yes；self_run 6 項；findings 1 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-CARD-BODY-BUDGET1-e0-d05f8eccc957fa2a860ef92df5f9fdf16c955b25。
- 2026-08-26T01:02:16+08:00 handoff by wf-cli → owner —（已完成）；iteration 1；SHA 446cc68e5b1dc44804a2d789f27e47721d761c5a；證據 R2 APPROVE（GPT-5@Codex，core_pain_resolved=yes；R1 blocking 已閉環、R2 minor 已修）後合併。PR https://github.com/ruan6047/ai-workflow/pull/144；required check tests=SUCCESS、mergeStateStatus=CLEAN。回歸 1158→1174 passed，trailer 守衛違規 0／合規 5，git diff --check 乾淨。⚠️ 已知代價：Log 由自足變依賴平台；A9 只解除到 50 版（⛔ 未證明無上限）。⚠️ 射程外登記：canonical §6.3「今天沒有任何卡符合」已過期（四個獨立來源各自抓到：PM 自審、查核者範圍外觀察、aiwf#141 與 #142 兩輪研究）。；收尾清理：已清除 worktree、本地分支、遠端分支。


## Comment 5407536225 · 2026-08-25T08:22:42Z

## 研究輪 1｜量測與設計選項

⚠️ **先更正我自己稍早的兩個說法**（本輪重新量測後推翻）：
1. 我先前說「amend 次數中位數 **0**」——實測是 **1**。
2. 我先前說「body 最大的前三張都是本 Initiative 的卡」——實測前 8 名中有 5 張是 cpbl 的 DATA 卡（`#159` 63,774／`#134` 53,071／`#154` 38,170／`#139` 37,905／`#155` 36,927）。⇒ **這不是 workflow 卡專屬的問題**，風險母體比我先前描述的廣。

### 一、成長律（機械可導）

`amend_cmd.py:406`：

```python
def _fold(text: str) -> str:
    """Log 是單行條目，原值摺成一行——但**不截斷**：Log 是唯一還原點。"""
    return " ".join(str(text).split())
```

⇒ 每次 amend 對每個異動欄位寫入 **舊值全文 + 新值全文**。⇒ `ΔLog ≈ Σ(2 × 欄位大小)`，且**單調**（Log 是 append-only）。

⇒ 一張欄位大小 `F` 的卡，剩餘可改次數 `= (LIMIT − body) ÷ 2F`。⭐ **`F` 越大、討論越多，可改次數掉得越快**——即失效模式選擇最關鍵的卡。

### 二、母體分布（Project 4，193 張，2026-08-25 實測）

| 指標 | 值 |
|---|---|
| body 中位數 | 4,116 |
| body 平均 | 8,725 |
| body 最大 | 74,894（`#130`，Log 佔 93.6%，amend 26 次） |
| amend 次數中位數 | 1 |

⇒ **中位卡完全沒有風險**（餘裕 >125,000）。風險集中在長尾：Log 佔比在最大的 8 張裡是 83.8%–93.6%。

### 三、上限是實測值，⛔ 非文件值

實測落在 **(129,486, ~130,018)** 之間。⛔ 文件常引的 65,536 是錯的——`#105` 在 129,651 時仍可讀取、寫入才失敗。本卡一律採實測下界 129,486 為 `LIMIT`，⛔ 不引 65,536。

### 四、觀測面：零

```
grep -rEn "len\(.*body.*\)|MAX_BODY|body_limit|too long|65536" src/wf_cli/ | grep -v test
→ src/wf_cli/doctor.py:237:  lines.append(f"- **雙居所漂移 {len(bd.findings)} 張**…")
```

唯一命中是 **findings 的計數**，⛔ 不是 body 大小。⇒ CLI 全域沒有任何一處量測卡面容量。⚠️ 這個結論是**看過命中內容**才下的，⛔ 不是靠「grep 回 0」。

### 五、`_fold` 的前提已被推翻

docstring 的理由是「Log 是唯一還原點」。實測不成立：GitHub `userContentEdits` 對每次 body 編輯保存**逐位元相同**的前一版全文。

- `#105`：截斷前 body 129,651 位元組，sha256 `c94b1d40685a3f67f12586ee985c326b9ca1e04f8940eaa02f8d4b04e9aee5cd`，與平台側前一版比對 **相符**。
- `#138`：11 個版本，最新一版 `== True`（逐位元）。

⚠️ **但不是每張卡都有**：33 張抽樣中 **9 張 `totalCount=0`**（平台無前一版）。⇒ 任何「用指標取代全文」的設計都必須對這條路徑 fail-safe。

### 六、設計選項（供規劃輪裁決）

**甲｜Log 記指紋 + 預算回報（建議）**
- 舊值改記 `sha256 + 位元組數 + 前 N 字`，⛔ 不記全文；**僅當平台確實有前一版時**，否則退回全文。
- 每次 amend 印出「本次付 X 位元組／body 現 Y／餘裕 Z／還能改 ≈ N 次」。
- 軟門檻（餘裕 < 20,000）警告；硬線（寫入後 > LIMIT）拒絕並印出瘦身指引。
- ⇒ 成本砍半，且保留可驗證的完整性檢查（指紋比全文更能證明沒被竄改）。

**乙｜只加預算回報，不動 Log**
- 風險最低，但成長律不變 ⇒ 只是把撞牆時間往後推、不解決。

⛔ 兩案都**不做**卡面內容自動瘦身——那是逐卡的編輯判斷，機器做會丟語意（今天 `#105`／`#138` 的壓縮全部是一對一逐條、人工核對覆蓋率）。

⭐ 建議甲。理由：乙不滿足服務目標的判準（「有機械執行者會擋下它」）——乙的硬線擋得下，但成長律不變會讓硬線變成常態阻塞，⇒ 使用者只會學會繞過它。


## Comment 5407562522 · 2026-08-25T08:25:06Z

## 研究輪 2｜三個前提的實測，以及一個把甲案改強的發現

### 一、⛔ 阻斷條件：DraftIssue 沒有前一版

GraphQL schema 探測（唯讀）：

```
gh api graphql -f query='{ __type(name:"DraftIssue"){ fields{name} } }'
→ assignees body bodyHTML bodyText createdAt creator id projectV2Items projectsV2 title updatedAt
```

⇒ **`DraftIssue` 型別上沒有 `userContentEdits`**。⇒ 對 draft 卡，平台**完全不保存前一版** ⇒ 任何「以指紋取代全文」在該路徑上是**不可逆損失**。

✅ 現況風險為零但路徑是活的：Project 4 實測 `{'Issue': 194, 'DraftIssue': 0}`，然而 `wfcli open` **不給 `--repo` 就會建 DraftIssue**（`project.py:191 create_draft_item`）。

⇒ **硬性設計約束：優化僅在 `content_type == "Issue"` 時啟用，DraftIssue 一律走全文。** 這條要進驗收，⛔ 不是註解。

### 二、✅ 量測是零成本的

`amend_cmd.py:930` 呼叫 `set_item_body(..., body)` 時**完整新 body 已在手上**；而 `:920` 為了競態偵測本來就重讀了一次 `list_items`。⇒ 預算計算與預警**不需要任何額外 API 呼叫**。

### 三、⚠️ 版本保存：支持，但有一項未驗證

| 卡 | Log 行 | 相異 amend op | 平台版本數 |
|---|---|---|---|
| `#137` | 14 | 4 | 9 |
| `#138` | 17 | 7 | 12 |
| `#130` | 40 | 14 | 39 |
| `#105` | 11 | — | 28 |
| `#139` | 1 | 0 | 0 |

版本數 **≥** amend 次數（差額是 `handoff`／`review`／`checkpoint` 等其他 writer 的 body 寫入，我的 regex 只認 amend 的 `op=` 格式）。⇒ **每次 body 寫入都留下一版**成立。`#105` 連續兩次寫入實測 26→27→28，1:1。

⚠️ **未驗證**：實測最高 39 版全部取得，⛔ **沒有證據說明超過 39 之後是否有保存上限**。這是本卡最大的未證實假設，須在驗收裡要求執行者實測到更高版本數或找到官方保證。

### 四、⭐ 發現：新值也是冗餘的 ⇒ 成本可從 O(2F) 降到 O(1)

我原本只提議拿掉舊值全文。但 Log 寫入的**新值**同樣冗餘——**它就在正上方的欄位裡**。

⇒ Log 條目改為只記：`op｜欄位名｜舊值指紋(sha256+位元組數)｜新值指紋｜reason`。還原路徑：

- 最新值 → 讀卡面欄位
- 任一歷史中間值 → 平台第 k 版
- 「這一版有沒有被竄改」 → 比指紋（⭐ 這比存全文**更強**：全文自己不能證明自己沒被改）

| | 現行 | 甲修正案 |
|---|---|---|
| `ΔLog` | `Σ(2 × 欄位大小)` | 約 250 位元組，**與欄位大小無關** |
| `#138` 每次 amend 成本 | 4,878 | ≈ 250 |
| `#138` 剩餘可改次數 | 11 | ≈ 230 |

⇒ 成長律從**線性於內容**變成**常數** ⇒ 撞牆從「必然、只是早晚」變成「實務上不會發生」。

### 五、修正後的建議

**甲′｜Log 只記指紋 + 寫入路徑預算檢查**

1. Log 條目不含任何欄位全文；記 op／欄位／舊值指紋／新值指紋／reason。
2. ⛔ 例外一律退回全文：`content_type != "Issue"`（無版本）、`userContentEdits.totalCount == 0`（首寫、無前一版）。
3. amend 每次印「本次付 X／body 現 Y／餘裕 Z／還能改 ≈ N 次」。
4. 軟門檻警告、硬線拒絕並印瘦身指引。

⚠️ 明確代價（要寫進交付，⛔ 不得省略）：Log 從**自足**變成**依賴平台**。任何離線讀 Log 的流程（匯出、封存、repo 遷移）將只拿得到指紋。⇒ 若未來要遷離 GitHub，需先跑一次全量版本匯出。這是真實的技術債，不是零成本。

⭐ 仍建議甲′。理由：現行設計讓**討論越多的卡越早死**，而那正是最需要被討論的卡；把成長律改成常數是唯一能移除這個反向選擇的做法，其餘都只是延後。


## Comment 5407996986 · 2026-08-25T09:01:25Z

## T3 閘門裁定

**⚠️ 轉錄聲明**：本留言由 PM（Claude Opus 5@Claude Code）以 `ruan6047` 的 gh token 發出，⛔ 故 GitHub 顯示的 author 不構成「誰做的決定」的證據。裁定內容來自需求方 2026-08-25 於 Claude Code 對話中的逐字回覆「**兩個都好**」，回應的是 PM 提出的兩個裁決點（甲：`#139` T3 閘門放行進 Backlog；乙：`#105` 重開）。

### 裁定：放行進 📥Backlog

**依據**（PM 於提請時逐字給出、需求方據此裁定）：

> A9 已經把最大的未證實假設做成硬停條件，執行者證不出保存上限就自動降級成低風險版本。

### 隨裁定成立的三項約束

1. ⛔ **A9 是硬停條件不是提醒**：`userContentEdits` 的保存上限若無實測（>39 版）或官方保證，A1（Log 改記指紋）**不得實作**，退回只做 A4–A6（預算量測與硬線）。此判斷由**執行者提出證據、查核者裁定**，⛔ PM 不代判。
2. ⛔ **A2 的兩條例外不可協商**：`DraftIssue`（型別上無 `userContentEdits`）與 `totalCount == 0`（首寫）一律寫全文，各須獨立測試 + V9 的變異檢驗。
3. ⚠️ **派工序列化**：本卡宣告 `cli/src/wf_cli/commands/amend_cmd.py`，與 `#105`（重開後）相同 ⇒ 兩卡不可同時派工，順序為 `#105` 先。

### ⚠️ 本卡未涵蓋的一項（明記而非靜默省略）

PM 原提「三層」中的**第三層（紀律：研究進 comment、卡面欄位只寫判準）在本卡沒有獨立載體**。A4 的預算行讓成本在寫入當下可見，⛔ 但那不等於一條「研究不進欄位」的規則，也沒有機械執行者。⇒ 今天在 `#105`／`#138`／`#139` 上的做法是 PM 的行為，⛔ 不是機制。此缺口本卡不處理、亦**未開卡**，僅在此登記。


## Comment 5412171342 · 2026-08-25T14:47:32Z

## A9 硬停條件：實測解除（但只解除到 50 版）

卡面 A9 逐字：「`userContentEdits` 是否有保存上限。實測最高 39 版全數取得，⛔ 39 以上未驗。執行者須提出實測（找到或構造 >39 版的卡）或官方文件保證；⛔ 兩者皆無則 A1 不得實作，退回只做 A4–A6。」

### 做法：alias 批次掃全母體，⛔ 不逐張打 API

以 GraphQL alias 一次查 60 個 issue 的 `userContentEdits(first:1){totalCount}`，掃過兩個 repo 共 **202 個 issue**（`ai-workflow` 82／`cpbl-analytics` 120）。

版本數前 10：

| 版本數 | issue |
|---|---|
| **50** | `ai-workflow#16` |
| 39 | `ai-workflow#130` |
| 37 | `ai-workflow#105` |
| 28 | `cpbl-analytics#130` |
| 26 | `ai-workflow#129` |
| 26 | `ai-workflow#57` |
| 24 | `ai-workflow#25` ／ `#22` ／ `#21` |
| 23 | `ai-workflow#134` |

⇒ 全母體 **>39 者恰 1 筆**。

### 對 `aiwf#16` 實際取回並驗證

```
totalCount        = 50
first:100 實取     = 50          ⇒ 全數取回 True
hasNextPage       = False
diff 非 null       = 50/50        ⚠️ null 會代表該版內容取不到
內容大小           min 2,072 / median 21,410 / max 39,213 bytes
時間跨度           2026-08-10T06:38:56Z … 2026-08-18T21:49:44Z（8 天）
最舊一版           2,072 bytes，開頭是 `- 需求：ruan6047　規劃：GPT-5@Codex` ⇒ 是**完整 body**
first:50 分頁測試   實取 50、hasNextPage=False
```

### ⇒ 裁定

**A9 的硬停條件解除，A1（Log 改記指紋）可以實作。**

### ⚠️ 但它只證到這裡（交付須逐字保留）

- ✅ 已證：**50 版全數可取、內容完整、無截斷跡象**，已驗證區間由 39 推到 50。
- ⛔ **未證明「無上限」**。這只是把下界往上推，⛔ 不是證明不存在上限。
- ⛔ **未取得官方文件保證**（A9 允許的另一條路，本輪未查）。
- ⚠️ **未驗長期保留**：最舊的一版只回溯到 2026-08-10（8 天）。⛔ 沒有證據說明數月或數年後仍在。
- ⚠️ **母體限制**：>39 版的樣本只有 **1 個**。⛔ 單一樣本不足以排除「某些卡會被截斷」。

⇒ **A1 的設計必須對「取不到前一版」保持 fail-safe**——這與 A2 既有的兩條例外（`DraftIssue` 無 `userContentEdits`、`totalCount == 0` 首寫）是同一類，⛔ 不得因為本輪結果而放寬。⭐ 具體要求：寫入指紋前**實查**該版可取得，取不到就退回全文。


## Comment 5413261050 · 2026-08-25T16:09:40Z

## V1／V2／V8 實跑證據（真實卡，⛔ 非 mock）

⚠️ 這三條逐字要求**真實卡**。實驗載體是 `aiwf#142` 的兩次 amend——那是需求方裁定「甲」後**本來就要做的**改寫，⛔ 沒有拿真實欄位當診斷探針。

### V8｜三張既有卡的 `--dry-run` 對帳（⛔ 零寫入）

| 卡 | 獨立量測 | CLI 印的 | 對帳 |
|---|---|---|---|
| `WF-STAGE-STATE-TWO-AXIS1`（🏁完成） | 74,894 | 74,894 + 387 = **75,281** | ✅ |
| `WF-RESOURCE-HEADING-SUFFIX1`（Log 59K） | 38,984 | 38,984 + 52 = **39,036** | ✅ |
| `WF-CARD-BODY-BUDGET1`（本卡） | 8,365 | 8,365 + 136 = **8,501** | ✅ |

### ⛔ V8 第一次跑就抓到一個根本錯誤：單位錯了

第一次 `#130` 被判**超限 27,456**，而它 🏁完成且真實存在於 GitHub 上。追查後：

```
#105 截斷前   字元 129,651  ／  位元組 262,130
#130（現存）  字元  74,894  ／  位元組 156,942
```

我當初量到的 129,651 是 Python `len(str)` ＝ **字元**，而實作全部用 `len(body.encode())` ＝ **位元組** ⇒ 對中文卡面（1 字 ≈ 3 位元組）守衛**提早約 3 倍觸發**。⭐ **所有 mock 測試都用 ASCII，構造上碰不到。** 已修（`d2d2ee9`）。

### V1｜Log 不含舊值任何一段連續 20 字元

`aiwf#142` 第二次 amend（`op 68a3d861`，改驗收＋驗證兩欄）：

```
驗收條件  ✅ 未洩漏
驗證      ✅ 未洩漏
```

Log 行實際長相：`→ 驗證：原值指紋 sha256:9dd02429…(726 bytes) → 新值指紋 sha256:…`

### ⭐ V2｜Log 的指紋 == 由平台留存那一版重算出來的 sha256

```
驗收條件  Log f2774a06a3981e3f2ae7…(1195B)  ==  重算 f2774a06a3981e3f2ae7…(1195B)  ✅
驗證      Log 9dd02429dac10787825c…(726B)   ==  重算 9dd02429dac10787825c…(726B)   ✅
```

⇒ **「歷史仍可證明地回得去」有機械證據**：Log 只留指紋，而指紋與平台版本逐位元對得上。

### ⚠️ V2 的兩處措辭已據此更正（見卡面）

1. **⛔ 增量不必然是 +2。** `#142` 的 `totalCount` 原為 **0**，兩次 amend 後是 **3**——建立那一筆是**首次編輯之後才追溯出現**。⇒ 判準改為「每次 body 寫入各留一版」。
2. **重算舊值必須照 `card._amend_checklist` 的 `old_repr` 規則**（`"；".join(f"[{s}] {t}")`，保留勾選狀態前綴）。

### ⛔ 並登記：上面兩處都是我的驗證腳本先錯，⛔ 不是碼錯

- 第一次拿最後一行（`驗證`）的指紋去比 `驗收條件` 的 hash
- 第二次重建舊值時把 `- [ ] ` 整個剝掉 ⇒ 每項少 4 字元 × 7 項 = 28、× 6 項 = 24，**與觀察到的差距完全吻合**

⇒ 兩次都是先看差距的**算術結構**才找到成因，⛔ 不是靠複查。

### ⚠️ V3 仍未做

卡面 V3 逐字：「須用**真實 draft item**（Project 4 現有 0 張，須自建 throwaway），⛔ **不接受 mock**」。
我補的 `test_draft_issue_card_always_falls_back_to_full_text` 是 mock ⇒ **不滿足 V3**。
⛔ 建立拋棄式 draft 卡需要需求方授權（同 `aiwf#140` 探針的做法），目前**未授權、未做**。


## Comment 5413326313 · 2026-08-25T16:15:05Z

## ✅ V3 已實跑完成（真實 DraftIssue，⛔ 非 mock）

卡面 V3 逐字：「須用**真實 draft item**（Project 4 現有 0 張，須自建 throwaway），⛔ **不接受 mock**」。

依 canonical §6.4.2 —— 逐字「**驗得了但沒驗**——揭露是替代勞動 ⇒ 本要求只擋後者」，且其依據是 `aiwf#129` 那個「派審包寫『未驗』、同一輪的 blocking finding 就是那一項、重現耗時不到兩分鐘」的實例 —— 需求方 2026-08-26 授權建立拋棄式 draft 卡 `WF-CARD-BODY-BUDGET1-PROBE-DRAFT1`（🛑已停止）。

### 結果（結構判準，⛔ 非字串 grep）

```
content_type = DraftIssue
指紋格式 → [欄位]：原值指紋 sha256:… → 新值指紋      命中：⛔ 否
全文格式 → [欄位]：原值「…」→ 新值「…」（⚠️ 全文：…）  命中：✅ 是
退回理由（格式第 3 捕獲組）：content_type=DraftIssue（平台無 userContentEdits…
負控：舊值 254 字元、含開卡時 D4 的尾段「本卡不留待辦」⇒ 全文確實寫入，⛔ 非漏寫
```

⇒ **draft 路徑 fail-safe 成立。** 這條特別重要：draft 卡**沒有任何平台版本可還原**，⇒ 一旦誤走指紋就是不可逆的資料損失。

### ⛔ 並登記：第一次驗證的三個檢查全部是零資訊

我把 `` `sha256:` `` 與 `content_type=DraftIssue` **寫進了那張探針卡自己的驗收條文**，然後又去 grep 那兩個字串 ⇒ 檢查命中的是卡片自身的內容、⛔ 不是 Log 的行為。三條判準（D2a／D2b／D3）當場全部誤判——D2a 報「竟走了指紋路徑」、D3 報「舊值沒寫進去」，而實際行為完全正確。

⇒ 已改用**結構判準**（比對 Log 行的格式，並從捕獲組取值）重驗。

⚠️ 這是同族第 N 次：**驗證器與被驗對象共用了字串空間**。與今日稍早的「手打哨兵常數」「issue 號當鍵」同一形狀。

### ⇒ V1／V2／V3／V8 全部完成

| 條 | 狀態 |
|---|---|
| V1 Log 不含舊值連續 20 字元 | ✅ 真實卡（`aiwf#142`） |
| V2 指紋 == 平台版本重算 | ✅ 兩欄位皆逐位元相符 |
| V3 draft 退回全文 | ✅ **真實 DraftIssue** |
| V8 三張既有卡預算對帳 | ✅ 並抓到字元／位元組單位錯誤 |


## Comment 5413489494 · 2026-08-25T16:28:51Z

<!-- wf-review-event:v1 card_id=WF-CARD-BODY-BUDGET1 source_sha=d2d2ee95b12d237172cf2bcd2b681486e0ac9af5 attempt_id=WF-CARD-BODY-BUDGET1-e0-d2d2ee95b12d237172cf2bcd2b681486e0ac9af5 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CARD-BODY-BUDGET1`　attempt_id：`WF-CARD-BODY-BUDGET1-e0-d2d2ee95b12d237172cf2bcd2b681486e0ac9af5`
- 查核者：GPT-5@Codex　escalation_epoch：0
- source_sha：`d2d2ee95b12d237172cf2bcd2b681486e0ac9af5`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-26T00:28:49+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git status --short`
  - HEAD=d2d2ee95b12d237172cf2bcd2b681486e0ac9af5，工作區乾淨。
- `git rev-parse origin/main && git merge-base HEAD origin/main`
  - 兩者皆為 1d80509d2a09059f3fd4b69b861a6129cd1ddd63，可快轉。
- `uv run pytest -q`
  - 被審分支 1170 passed。
- `git clone --no-local . <disposable> && checkout origin/main && uv run pytest -q`
  - 基線 1158 passed；與交付聲明的 +12 相符。
- `uv run wfcli amend --owner ruan6047 --project 4 WF-CARD-BODY-BUDGET1 --repo ruan6047/ai-workflow ... --dry-run`
  - 實際輸出確認預算列與指紋路徑，但同時重現下列誤導訊息。

### findings（1，其中 blocking 1）

- **WF-CARD-BODY-BUDGET1-R1-001**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`fingerprint-log-recovery-message-mismatch`
  - evidence：amend_cmd.py:570 的 _short() 對截斷值固定輸出「全文 N 字，見 Log」； 成功輸出迴圈於 :1224 無條件使用它。對真實 #139 的唯讀 dry-run， CLI 同時輸出「Log 記法：指紋（totalCount=9，最新一版可取得）」與舊值摘要 「全文 1250 字，見 Log」。但此路徑的 Log 僅存 sha256 指紋，全文只能由平台前一版取回， 因此「見 Log」是錯誤的還原指引。
  - disposition：指紋路徑不得宣稱全文在 Log：移除「見 Log」，或依 recoverable 狀態改為 「全文見平台前一版」。同步修正 _fold() 仍稱 Log 為唯一還原點的過期 docstring， 並新增回歸測試：建立可還原版本後，以超過 _short 門檻的舊值執行 amend／dry-run， 斷言輸出不含「見 Log」且明示平台版本還原路徑。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-CARD-BODY-BUDGET1-e0-d2d2ee95b12d237172cf2bcd2b681486e0ac9af5
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: GPT-5@Codex（跨家族查核）
findings:
  - finding_id: WF-CARD-BODY-BUDGET1-R1-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: fingerprint-log-recovery-message-mismatch
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5413835792 · 2026-08-25T16:57:44Z

<!-- wf-review-event:v1 card_id=WF-CARD-BODY-BUDGET1 source_sha=d05f8eccc957fa2a860ef92df5f9fdf16c955b25 attempt_id=WF-CARD-BODY-BUDGET1-e0-d05f8eccc957fa2a860ef92df5f9fdf16c955b25 -->
## 查核裁決：APPROVE

- 卡：`WF-CARD-BODY-BUDGET1`　attempt_id：`WF-CARD-BODY-BUDGET1-e0-d05f8eccc957fa2a860ef92df5f9fdf16c955b25`
- 查核者：GPT-5@Codex　escalation_epoch：0
- source_sha：`d05f8eccc957fa2a860ef92df5f9fdf16c955b25`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-26T00:57:42+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git status --short`
  - HEAD=d05f8eccc957fa2a860ef92df5f9fdf16c955b25；工作區乾淨。
- `git rev-parse origin/main && git merge-base HEAD origin/main`
  - 兩者皆為 1d80509d2a09059f3fd4b69b861a6129cd1ddd63，符合快轉前提。
- `uv run pytest -q`
  - 1174 passed；R1 基線為 1170 passed，新增 4 項測試且無回歸。
- `uv run pytest tests/test_commands_mocked.py -k 'short or recovery or fingerprint or full_text or fulltext or budget' -q`
  - 10 passed。指紋路徑與全文退路皆有正、反向覆蓋。
- `wfcli amend ... --acceptance ... --tier T4 --dry-run`
  - 真實卡唯讀輸出中，舊驗收摘要為「見平台前一版」、新值為「見上方欄位」；
  - 不再出現錯誤的「見 Log」指引。
- `git diff --check d2d2ee9..HEAD`
  - 僅發現 tests/test_commands_mocked.py EOF 多一個空白行；不影響行為。

### findings（1，其中 blocking 0）

- **WF-CARD-BODY-BUDGET1-R2-001**　severity=minor　blocking=false　class=implementation　attribution=executor　root_cause_id=`trailing-blank-line-in-test-artifact`
  - evidence：git diff --check 回報 cli/tests/test_commands_mocked.py:1990 的 EOF 空白行。
  - disposition：合併前移除多餘 EOF 空白行，使 diff 檢查乾淨；不影響本輪 APPROVE。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-CARD-BODY-BUDGET1-e0-d05f8eccc957fa2a860ef92df5f9fdf16c955b25
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: GPT-5@Codex（跨家族查核）
findings:
  - finding_id: WF-CARD-BODY-BUDGET1-R2-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: implementation
    attribution: executor
    root_cause_id: trailing-blank-line-in-test-artifact
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5414011230 · 2026-08-25T17:12:54Z

## ⛔ 更正：我兩次誤報「造成不可修復的非法終態」

**⚠️ 轉錄聲明**：本留言由 PM（Claude Opus 5@Claude Code）以 `ruan6047` 的 gh token 發出；⛔ 顯示的 author 不構成「誰做的判斷」的證據。本則是 PM 的自我更正，⛔ 無需求方裁定成分。

### 我說錯了什麼

2026-08-25／26 我在兩張拋棄式探針卡（`WF-RESOURCE-HEADING-SUFFIX1-PROBE-ASSIGN1`、`WF-CARD-BODY-BUDGET1-PROBE-DRAFT1`）上跑 `handoff --next-stage release --status 🛑已停止` 而**未帶 `--cleanup`**，看到守衛印出：

> 依 `WF_CLEANUP_GUARD1` 的分類，這是 `illegal_terminal_before_cleanup`……事後再補 `--cleanup` 會被擋，屆時只能人工收尾。

⇒ 我據此**連續兩次**報告「我造成了不可修復的非法終態」。**那是誤報。**

### 實測（唯讀）

```
兩張探針卡的實際觀測：
  git branch -a --list "*PROBE*"          → 只有別張卡的 claude/WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1
  git ls-remote --heads origin | grep -i probe → 同上
  ⇒ 兩張卡皆無 worktree、無本地分支、無遠端分支

cleanup.CloseoutObservation(worktree_present=False, local_branch_present=False,
                            remote_branch_present=False, terminal_status_written=True,
                            issue_open=True)
  → cleanup_done      = True
  → classify_state    = "effect_in_progress"     ⭐ 在 LEGAL_STATES 裡

對照（真有殘留時）：worktree_present=True, local_branch_present=True
  → cleanup_done = False → "illegal_terminal_before_cleanup"
```

⭐ `cleanup_done` 的定義逐字是「**授權範圍內**的清理是否都做完了……沒被授權的資源仍在，不算未完成」——**沒有東西要清就是做完了**。

⇒ **兩張探針卡處於合法終態，⛔ 沒有任何東西需要人工收尾。**

### 成因

那句警示是 `release` 未帶 `--cleanup` 時**無條件印**的，講的是「這條路徑可能造成什麼」，⛔ **不是「你剛才造成了什麼」**。而我把**警示文字**當成**分類結果**。

⭐ 這個病在本 repo 有名字：**把「出現」當「宣告」**（`card.py` 回應 R3-001／R4-001 的註解逐字：「R3 用內容猜版本，R4 用存在性猜版本；兩次都把『出現』當『宣告』」）。

⛔ 而更該記的是：**我用它做了自我歸責，而自我歸責感覺像誠實 ⇒ 我一次都沒有去查證。** 「我造成了損害」與「我沒造成損害」需要同樣強度的證據。

### 受影響的留痕（本則一併更正）

| 位置 | 原本寫的 |
|---|---|
| `aiwf#140` 的 handoff evidence | 未提；但當時的對話與後續留痕沿用了該誤判 |
| `aiwf#105` 交付報告 issuecomment-5410372288 §一.1 | 「我在探針卡上造成一筆不可修復的非法終態」 |
| `aiwf#139` R1／R2 派審詞 | 「兩張探針卡留下 `illegal_terminal_before_cleanup`」 |
| PM 記憶 | 已更正 |

⇒ 以上四處**全部作廢**。⚠️ 仍然成立的部分：**有 worktree 或分支的卡**，`release` 不帶 `--cleanup` 確實會造成非法終態且事後補會被擋——`aiwf#105` 與 `aiwf#139` 的收尾都正確帶了 `--cleanup --repo-path`，兩者實測 `mode=applied`／`合法=True`。

