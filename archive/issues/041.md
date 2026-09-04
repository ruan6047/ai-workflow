# #41 WF-EVENT-IDEMPOTENCY1-ADAPT-STALE1 已結案 #23 的 §4.4.1 仍把兩項已被撤除的自檢適配寫成現役機制
- state: closed  created: 2026-08-12T03:14:09Z  closed: 2026-08-17T13:12:58Z
- url: https://github.com/ruan6047/ai-workflow/issues/41
- comments: 4

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 經濟型；單檔文件更正，事實已由 #24 的 R6 查核逐條確立，執行者只需核對現況並改寫兩處措辭；推理鏈短。）　查核：待指派（建議 經濟型；低風險文件更正，查核只需確認改寫後的敘述與 main 上的自檢現況相符、且未追溯改寫歷史裁決；不涉紅線故不強制跨家族。）
- Initiative：—　spec 基線：WF-RESOURCE-WRITESET1（#24）R6 查核 finding R6-001（minor，非 blocking，attribution=coordinator，root_cause_id=cross-card-contract-drift），收據 issuecomment-5261716854。需求方 2026-08-12 裁定另開卡修檔案本身而非在 Issue 留註記。
- DB：db_scope=none
- 服務的原始目標：讓已結案卡的交付文件不會對讀者陳述一個已經不存在的機制

## 簡介
<!-- card-brief:begin -->
更正 docs/WF_EVENT_IDEMPOTENCY1.md §4.4.1：該節仍把 SystemExit(0) 處理與 probe-requires 登記寫成現役機制，但 WF-RESOURCE-WRITESET1（aiwf#24）於 3e45646d 已撤除整個執行路徑與 probe-self／probe-requires 兩個標記，兩項適配早已失去標的；改寫須保留「當時發生了什麼」的歷史價值，並以指令輸出窮舉全檔其他引用已撤除機制之處。**適用時機**：讀該交付文件而懷疑某機制是否還在時；或要查「跨卡文件失真該改檔還是在 Issue 留註記」的裁定依據時。⛔ 非射程：不動 docs/WF_RESOURCE_WRITESET1.md 與任何 templates/、cli/ 檔，寫入集只有一個檔；不追溯改寫任何裁決或事件留痕。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：WF-EVENT-IDEMPOTENCY1（#23）已結案併入 main，其 docs/WF_EVENT_IDEMPOTENCY1.md §4.4.1 仍把兩項適配寫成共用自檢的現役機制：SystemExit(0) 的處理與 probe-requires 登記。但 #24 於 3e45646d 為了關閉 R4-001（宣稱唯讀卻實際 exec 外部文件）已把整個執行路徑與 probe-self／probe-requires 兩個標記全部撤除，兩項適配因此失去標的。#24 自己的 §9.9.9 已如實列出影響，故沒有隱瞞；問題在 #23 那一側——讀者打開該檔會相信那兩項機制還在。查核者判這不是 #24 的 blocking finding（修改已結案卡逸出其寫入集），但要求 PM 留下可稽核的跨卡歸屬裁定。選擇改檔案而非在 Issue 留註記，理由是該檔是讀者會經過的平面而 Issue 留言不是——與判 dispatch-package.md 不適合承載規則是同一條論證。

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

- [ ] 核對 main 上 docs/WF_RESOURCE_WRITESET1.md §9.9 的自檢現況，逐一確認 §4.4.1 兩項適配（SystemExit(0) 處理、probe-requires 登記）確實已無標的。若發現其中任一其實仍成立，如實回報並只改真正失效的那些——不得因卡面這樣寫就照改。
- [ ] 改寫 §4.4.1 使其陳述與現況相符，並保留該段的歷史價值：它記錄的是 #23 把 #24 的自檢原樣指向自己的檔案時發現的真實缺陷（那次一跑就踩中兩個，#24 再修時又挖出三個）。改寫後須讓讀者仍能理解「當時發生了什麼」與「現在的機制是什麼」，不得直接刪段落。
- [ ] 不得追溯改寫任何裁決或事件留痕。本卡只改交付文件的敘述，且改動須以本卡的 commit 為時點、明示是後續更正而非原文如此。
- [ ] 窮舉全檔是否還有其他處引用已撤除的機制（probe-self、probe-requires、對外部文件執行、退出碼即裁決等），不得只改 §4.4.1 就宣稱處理完畢。窮舉須由指令輸出產生。

## 驗證

- [ ] 以指令輸出證明窮舉範圍與結果：列出全檔命中的行號與各自處置（改／不改及理由），不得只寫「已檢查全檔」。
- [ ] 改動後的敘述須與 main 上 #24 交付版的實際機制逐條對應，對應關係寫進交付報告。
- [ ] 確認未動 docs/WF_RESOURCE_WRITESET1.md 或任何 templates/ 與 cli/ 檔案；本卡寫入集只有一個檔。
## Log

- 2026-08-12T11:14:08+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-12T13:32:34+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code 子agent；分支worktree claude/WF-EVENT-IDEMPOTENCY1-ADAPT-STALE1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1-adapt-stale1；交付狀態 🚧進行中；實際能力層級 經濟型（與卡面建議 經濟型 相符）。
- 2026-08-12T16:18:03+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c；證據 R1：docs/WF_EVENT_IDEMPOTENCY1.md 單檔 +33/-2。

執行者自己核了真因未照卡面照改，結論是兩項適配確實都失效但方式不同：適配 1（SystemExit(0) 視為通過）——抽出 main 上 WF_RESOURCE_WRITESET1.md §9.9 自檢區塊逐行掃執行原語，命中只有 raise SystemExit（自檢自己在 fence 未閉合時的錯誤路徑）、except OSError、except SyntaxError ×2，**沒有 exec／eval／compile(...,"exec")／runpy／except BaseException**；既然不執行任何區塊就沒有探針裁決可解讀。適配 2（probe-requires 登記）——全 repo grep 只有 8 筆，全部在 WF_RESOURCE_WRITESET1.md 的散文裡描述它們被撤除，沒有任何正則、常數或程式路徑消費這兩個標記。

⚠️ 它另分辨出卡面沒點名的第三項：len(probes) < 4 → probe-blocks 逐檔登記**仍然存活且仍然必要**，故未動。

窮舉由 grep -n 產生，9 組 pattern，逐項列出處置。除 §4.4.1 外唯一命中是 **§12 實作卡 A 的驗收欄**（:1220）逐字要求「套用 §4.4.1 的兩項適配」，已附更正註改為純靜態閘門＋逐檔登記、探針執行改由分離的具名 CI 步驟。改寫保留歷史價值：兩項適配的原始論述原文保留、由節首更正格統一標示失效，唯一時態錯誤的標籤「實跑 B（現況…）」改為「歷史」而**輸出內容一字未改**，節末新增實跑 C。

驗證：以 origin/main 版自檢（3.9.6 stricter 模式）跑改動後的本檔——4 個區塊全數閘門編譯通過、probe-blocks 登記相符、違例 0、裁決 PASS、退出碼 0。文件內實跑 C 記載的輸出與實際輸出 diff 逐行相同（先貼了猜測的行號，實跑後已改為程式產生的真值）。

⚠️ 執行者指名一項超出本卡、判定不該自己動的發現：該檔 :9（檔案開頭摘要）寫「執行指令一律釘為 uv run python（實測 3.12.13）」，但同檔 §4.4 節末 :454 明文「本輪撤除該處置」。**這兩句在 #23 交付當下就互相矛盾，是 #23 自己的內部漂移、不是 #24 撤除機制造成的**，故不在本卡窮舉標的內；修它要決定「現在該釘什麼指令」，屬實質規格判斷而非事實更正。建議另開卡。

執行者自陳四項無機械執行者：更正格靠版面位置（若日後有人在 §4.4.1 之前插入內容或折疊該格，保護就消失）；「原文一字未刪」只有 diff 讀者能確認、無測試釘住；實跑 C 只是快照非持續保證；窮舉完整性依賴它選的 9 組關鍵字，若已撤除機制還有別名會漏。

寫入集單檔零逸出，marker 新增 0 處。。
- 2026-08-12T17:00:35+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5264450677 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=e120a72e… 一次相符。本批六份收據皆採內容錨定或分隔行，各自規則不同，PM 逐份照其規則計算、無需任何格式調整）；core_pain_resolved yes；self_run 4 項；findings 1 項（blocking 0）；attempt WF-EVENT-IDEMPOTENCY1-ADAPT-STALE1-e0-ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c。
- 2026-08-12T17:15:32+08:00 handoff by wf-cli → owner —（結案）；iteration 0；SHA ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c；證據 跨家族查核判 APPROVE、core_pain_resolved=yes、0 blocking。收據 issuecomment-5264450677 未編輯，PM 回讀重算 report_sha256=e120a72e… 一次相符。查核者自 3e45646 抽出 §9.9 靜態自檢以 /usr/bin/python3 實跑：4 區塊、登記 4、3.9.6 stricter 閘門全通過、違例 0、退出碼 0、未執行任何區塊。以 PR #51 併入 main（e8a638c），PM 已於併前實測 merge 結果 658 passed、併後驗證被審 SHA 仍為祖先。一筆非阻擋 finding（attribution=planner，preexisting-authoritative-instruction-drift）：該檔開頭摘要與 §4.4 節末對「執行指令是否釘為 uv run python」互相矛盾，此矛盾已存在於基線、是 #23 自己的內部漂移，修它要決定現行指令屬實質規格判斷，由 PM 另開卡承接。。
- 2026-08-12T23:11:23+08:00 handoff by wf-cli → owner 待指派；iteration 1；SHA ba4755f4f2e33436d8128a9d68498250540f0cbb；證據 依 docs/ROADMAP.md §0／§3 降級：本卡屬目標 3（治理精緻化），非「防止低級事故」或「可稽核的內容」。需求方 2026-08-12 裁定降級為 Backlog、有餘力再做。⚠️ 降級不是關閉——本卡載有真實 finding 的紀錄，關閉會讓那些發現消失；降級可逆。。
- 2026-08-16T10:39:27+08:00 handoff by wf-cli → owner —（已結案）；iteration 0；SHA ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c；證據 還原終態（需求方 2026-08-16 裁定；PM 手動執行）。

【本卡於 2026-08-12 已達終態，其後被批次降級誤傷】
原始時序：review APPROVE（跨家族 GPT-5@Codex）→ handoff owner —（結案）、iteration 0 → 六小時後被 handoff ba4755f4 降回 待指派／iteration 1。本卡自此在看板上被算成待辦四天。

【誤傷的證據來自那筆降級事件自己的文字】
三張受影響卡（#35／#37／#41）的降級證據欄**逐字完全相同**，是一份批次模板，其理由為：
「⚠️ 降級不是關閉——本卡載有真實 finding 的紀錄，**關閉會讓那些發現消失**；降級可逆。」
**那句話在邏輯上不適用於這三張**：它預設「發現尚未交付、關掉就會消失」，而這三張都已 APPROVE 並結案，發現早已交付完畢。理由本身證明了批次執行時不知道它們的狀態。
佐證二：三份文字逐字相同＝模板套用而非逐卡判斷。
佐證三：降級把 iteration 由 0 改為 1，謊稱本卡回來了第二輪——而它沒有回來。

【這正是 ROADMAP 自己記下卻沒擋住的錯】
docs/ROADMAP.md:161-166 逐字寫著：「⚠️ 本表前一版把 #43 與 #24 排成序 1、2…那是錯的，它們的碼在寫這份藍圖之前就已經在 main 了。PM 憑印象排程、沒有先查狀態…**排程前先查狀態，這一條沒有機械執行者**。」
而 :207-217 的降級清單就在四十行之後，把這三張已結案的卡列進「降級為 Backlog（有餘力再做）」。**同一份文件，上面記著教訓，下面就再犯三次。**

【根因與預防】
handoff 的降級路徑不檢查現行交付狀態是否為終態，故一次批次降級可以改寫已結案的卡。cleanup.classify_state 已有 illegal_terminal_before_cleanup 的同型判定可複用。已建議加終態守衛：現行狀態落在終態集合時拒絕降級，除非帶顯式反轉旗標＋理由。

【--iteration 0 的用途】
本次以 --iteration 0 釘回原值，撤銷那筆降級造成的錯誤遞增。若不釘，帳面會顯示本卡經歷過兩輪而事實上只有一輪——iteration 是查核升級判定的輸入，錯誤的值會影響往後的 escalation 計算。

⚠️ 本則不改變本卡的技術結論：跨家族查核的 APPROVE、findings 0、以及交付 SHA 皆維持原值，本次只還原被誤傷的狀態與 iteration。。
- 2026-08-26T22:13:35+08:00 amend by wf-cli（op 60d979b7）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:9c261d2487db08ddaa506919e1cd5cdedf80d47b5664f51215751a55b9852537 (730 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5264329575 · 2026-08-12T08:33:17Z

## 派審：#41 `WF-EVENT-IDEMPOTENCY1-ADAPT-STALE1` R1

⚠️ 審核對象 **`ruan6047/ai-workflow#41`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1-adapt-stale1
分支：claude/WF-EVENT-IDEMPOTENCY1-ADAPT-STALE1　　被審 SHA：ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c
基線：5d22a7f3da57a3790179e999d9d28262fda4d19a（PM 已重算並驗為祖先）　　iteration：0（首輪）
寫入集：docs/WF_EVENT_IDEMPOTENCY1.md 單檔　　改動 +33 / -2
```

> **本則為權威。** `origin/main` 現為 `02b5d9a`。**PM 已實測 merge(origin/main, 本分支) → 658 passed 全綠。**

### 背景

已結案併入 main 的 `WF-EVENT-IDEMPOTENCY1`（#23）其 §4.4.1 仍把兩項適配寫成共用自檢的**現役機制**，而 `WF-RESOURCE-WRITESET1`（#24）為關閉一個 blocking finding 已把整個執行路徑與那兩個標記全部撤除。#24 的 R6 查核判這不是它的 blocking finding（修改已結案卡逸出其寫入集），但要求 PM 留下可稽核的跨卡歸屬裁定。需求方裁定**改檔案本身而非在 Issue 留註記**，理由是該檔是讀者會經過的平面。

### 一、執行者自己核了真因，未照卡面照改

**適配 1（`SystemExit(0)` 視為通過）→ 確實無標的。** 抽出 main 上 `WF_RESOURCE_WRITESET1.md` §9.9 自檢區塊逐行掃執行原語，命中只有 `raise SystemExit`（自檢自己在 fence 未閉合時的錯誤路徑）、`except OSError`、`except SyntaxError` ×2——**沒有 `exec`／`eval`／`compile(...,"exec")`／`runpy`／`except BaseException`**。既然不執行任何區塊，就沒有探針裁決可解讀。

**適配 2（`probe-requires` 登記）→ 確實無標的。** 全 repo grep 只有 8 筆，**全部在 `WF_RESOURCE_WRITESET1.md` 的散文裡描述它們被撤除**，沒有任何正則、常數或程式路徑消費這兩個標記。

⚠️ **它另分辨出卡面沒點名的第三項**：`len(probes) < 4` → `probe-blocks` 逐檔登記**仍然存活且仍然必要**，故未動。**請驗這個分辨是否正確**——若第三項其實也失效，那是漏改。

### 二、窮舉與改寫方式

窮舉由 `grep -n` 產生，9 組 pattern，逐項列出處置。**除 §4.4.1 外唯一命中是 §12 實作卡 A 的驗收欄**（:1220），逐字要求「套用 §4.4.1 的兩項適配」，已附更正註改為純靜態閘門＋逐檔登記、探針執行改由分離的具名 CI 步驟。

改寫**保留歷史價值**：兩項適配的原始論述**原文保留**，由節首更正格統一標示失效；唯一時態錯誤的標籤「實跑 B（現況…）」改為「歷史」而**輸出內容一字未改**，節末新增實跑 C。

**請攻擊**：(a) 窮舉的 9 組 pattern 夠嗎——執行者自陳「**若已撤除機制還有我沒想到的別名，會漏**」。(b) 更正格靠**版面位置**讓讀者先讀到，它自陳「若日後有人在 §4.4.1 之前插入內容或折疊該格，保護就消失」——這個處置夠嗎？

### 三、驗證

以 `origin/main` 版自檢（3.9.6 stricter 模式）跑改動後的本檔：**4 個區塊全數閘門編譯通過、`probe-blocks` 登記相符、違例 0、裁決 PASS、退出碼 0**。文件內實跑 C 記載的輸出與實際輸出 `diff` **逐行相同**（它先貼了猜測的行號，實跑後改為程式產生的真值）。

### 四、⚠️ 一項超出本卡、執行者判定不該自己動的發現

該檔 **:9（檔案開頭摘要）**寫「執行指令一律釘為 `uv run python`（實測 3.12.13）」，但**同檔 §4.4 節末 :454 明文「本輪撤除該處置」**。

**這兩句在 #23 交付當下就互相矛盾，是 #23 自己的內部漂移、不是 #24 撤除機制造成的**，故不在本卡窮舉標的內。它沒有改，因為修它要決定「現在該釘什麼指令」——**那是實質規格判斷屬原撰寫者／PM，不是事實更正**。建議另開卡。

**請判斷這個劃界是否恰當**，以及該矛盾是否嚴重到本輪就該處理。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5264450677 · 2026-08-12T08:45:07Z

core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "前輪 accepted blocking finding 閉環"
    observed: "首輪，無前輪 accepted blocking finding。"
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1-adapt-stale1 rev-parse HEAD && git -C ... merge-base --is-ancestor 5d22a7f3da57a3790179e999d9d28262fda4d19a ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c"
    observed: "HEAD 為 ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c；基線祖先檢查退出碼 0；工作區乾淨；diff 為 docs/WF_EVENT_IDEMPOTENCY1.md 單檔 +33/-2。"
  - command: "git archive ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c | tar -x -C /tmp/wf41-review.gmVkqV；自 3e45646 的 docs/WF_RESOURCE_WRITESET1.md 抽出 §9.9 靜態自檢後以 /usr/bin/python3 執行"
    observed: "4 個 python 區塊、probe-blocks 登記 4、3.9.6 stricter 閘門全數編譯及剖析通過、違例 0、PASS、退出碼 0；未執行任何區塊。"
  - command: "rg 交叉窮舉 SystemExit、imports_wf_cli、需網路、需憑證、probe-requires、probe-self、len(probes)、實際執行、已執行"
    observed: "兩項已失效適配僅出現於更正格、歷史輸出或受更正註覆蓋的歷史敘述；§12 實作卡 A 已改列純靜態閘門與分離具名 CI。"
findings:
  - finding_id: "WF-EVENT-IDEMPOTENCY1-ADAPT-STALE1-R1-001"
    severity: major
    blocking: false
    finding_class: authoritative-artifact
    attribution: planner
    root_cause_id: preexisting-authoritative-instruction-drift
    evidence: "source_sha 的本卡未動檔案開頭摘要仍稱執行指令一律釘為 uv run python 3.12.13，而同檔第 4.4 節末明載本輪撤除該處置；此矛盾已存在於基線，且修正需選定現行指令，不是本卡兩項失效適配的事實更正。"
    disposition: "另由原規格所有者或 PM 裁定現行指令後開獨立權威文件修正卡；本輪不擴寫入集。"

<!-- wf-review-receipt:v1
card_id: WF-EVENT-IDEMPOTENCY1-ADAPT-STALE1
source_sha: ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c
report_sha256: e120a72e97d575e4a886a71b9eca02e620753fe5e4e05b141b6e396d73e0269e
-->
取材規則：起點為本規則之後的下一個 core_pain_resolved: 行；終點為該 YAML 報告最後一行後的 LF；編碼 UTF-8；換行 LF；strip 否；排除本收據區塊、取材規則本行與本行之前的報告副本。被雜湊內容如下：

core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "前輪 accepted blocking finding 閉環"
    observed: "首輪，無前輪 accepted blocking finding。"
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1-adapt-stale1 rev-parse HEAD && git -C ... merge-base --is-ancestor 5d22a7f3da57a3790179e999d9d28262fda4d19a ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c"
    observed: "HEAD 為 ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c；基線祖先檢查退出碼 0；工作區乾淨；diff 為 docs/WF_EVENT_IDEMPOTENCY1.md 單檔 +33/-2。"
  - command: "git archive ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c | tar -x -C /tmp/wf41-review.gmVkqV；自 3e45646 的 docs/WF_RESOURCE_WRITESET1.md 抽出 §9.9 靜態自檢後以 /usr/bin/python3 執行"
    observed: "4 個 python 區塊、probe-blocks 登記 4、3.9.6 stricter 閘門全數編譯及剖析通過、違例 0、PASS、退出碼 0；未執行任何區塊。"
  - command: "rg 交叉窮舉 SystemExit、imports_wf_cli、需網路、需憑證、probe-requires、probe-self、len(probes)、實際執行、已執行"
    observed: "兩項已失效適配僅出現於更正格、歷史輸出或受更正註覆蓋的歷史敘述；§12 實作卡 A 已改列純靜態閘門與分離具名 CI。"
findings:
  - finding_id: "WF-EVENT-IDEMPOTENCY1-ADAPT-STALE1-R1-001"
    severity: major
    blocking: false
    finding_class: authoritative-artifact
    attribution: planner
    root_cause_id: preexisting-authoritative-instruction-drift
    evidence: "source_sha 的本卡未動檔案開頭摘要仍稱執行指令一律釘為 uv run python 3.12.13，而同檔第 4.4 節末明載本輪撤除該處置；此矛盾已存在於基線，且修正需選定現行指令，不是本卡兩項失效適配的事實更正。"
    disposition: "另由原規格所有者或 PM 裁定現行指令後開獨立權威文件修正卡；本輪不擴寫入集。"


## Comment 5264607358 · 2026-08-12T09:00:36Z

<!-- wf-review-event:v1 card_id=WF-EVENT-IDEMPOTENCY1-ADAPT-STALE1 source_sha=ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c attempt_id=WF-EVENT-IDEMPOTENCY1-ADAPT-STALE1-e0-ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c -->
## 查核裁決：APPROVE

- 卡：`WF-EVENT-IDEMPOTENCY1-ADAPT-STALE1`　attempt_id：`WF-EVENT-IDEMPOTENCY1-ADAPT-STALE1-e0-ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5264450677 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=e120a72e… 一次相符。本批六份收據皆採內容錨定或分隔行，各自規則不同，PM 逐份照其規則計算、無需任何格式調整）　escalation_epoch：0
- source_sha：`ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-12T17:00:35+08:00

### self_run（查核者實跑）

- `前輪 accepted blocking finding 閉環`
  - 首輪，無前輪 accepted blocking finding。
- `git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1-adapt-stale1 rev-parse HEAD && git -C ... merge-base --is-ancestor 5d22a7f3da57a3790179e999d9d28262fda4d19a ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c`
  - HEAD 為 ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c；基線祖先檢查退出碼 0；工作區乾淨；diff 為 docs/WF_EVENT_IDEMPOTENCY1.md 單檔 +33/-2。
- `git archive ebca7eca5ac2c7a68b2d59c741ab5ac828f71f9c | tar -x -C /tmp/wf41-review.gmVkqV；自 3e45646 的 docs/WF_RESOURCE_WRITESET1.md 抽出 §9.9 靜態自檢後以 /usr/bin/python3 執行`
  - 4 個 python 區塊、probe-blocks 登記 4、3.9.6 stricter 閘門全數編譯及剖析通過、違例 0、PASS、退出碼 0；未執行任何區塊。
- `rg 交叉窮舉 SystemExit、imports_wf_cli、需網路、需憑證、probe-requires、probe-self、len(probes)、實際執行、已執行`
  - 兩項已失效適配僅出現於更正格、歷史輸出或受更正註覆蓋的歷史敘述；§12 實作卡 A 已改列純靜態閘門與分離具名 CI。

### findings（1，其中 blocking 0）

- **WF-EVENT-IDEMPOTENCY1-ADAPT-STALE1-R1-001**　severity=major　blocking=false　class=authoritative-artifact　attribution=planner　root_cause_id=`preexisting-authoritative-instruction-drift`
  - evidence：source_sha 的本卡未動檔案開頭摘要仍稱執行指令一律釘為 uv run python 3.12.13，而同檔第 4.4 節末明載本輪撤除該處置；此矛盾已存在於基線，且修正需選定現行指令，不是本卡兩項失效適配的事實更正。
  - disposition：另由原規格所有者或 PM 裁定現行指令後開獨立權威文件修正卡；本輪不擴寫入集。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5316525695 · 2026-08-17T13:12:57Z

交付狀態已於 `handoff --next-stage release` 寫成 `🏁完成`，但本卡免部署、沒有走 deploy-state 那條會把 Projects Status 帶到 Done 的路徑，Issue 因此停在 OPEN。這是已登記缺口 ruan6047/ai-workflow#84 的實例，依該卡卡面所述的現行 workaround 由 PM 手動關閉。本次收斂共四張：#35 #37 #41 #63。
