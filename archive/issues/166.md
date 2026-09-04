# #166 DOC-CITATION-POINTS-ELSEWHERE1 兩處引用指不到它們說的東西，其中一處從出生就錯 132 行且正在擋 CI
- state: closed  created: 2026-08-28T06:12:08Z  closed: 2026-08-28T08:10:03Z
- url: https://github.com/ruan6047/ai-workflow/issues/166
- comments: 3

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；改動極小，⛔ 但這正是 aiwf#159 栽過的形狀：主旨寫「移除行號引用」的 commit 自己留下 2 個新行號、26 小時失效。執行者要在移除一個行號指標的同時不製造新的，並自證掃描由紅轉綠——那是判斷不是替換。）　查核：待指派（建議 主力型；查核要判的是新錨點會不會再位移（即對它問「什麼會讓這句話再指錯」），而非只驗掃描今天綠。⛔ 非紅線（純註解、零行為改動），毋須跨家族。）
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：目標 2 可稽核：文件與註解裡的引用必須指得到它宣稱的那個東西，否則讀的人會照著錯的位置去查。

## 簡介
<!-- card-brief:begin -->
把兩處指不到目標的引用換成不會位移的錨點：snapshot_population.py 第 5 行的 project.py:377（從出生就錯 132 行，現正擋住 aiwf#165 的 CI）與 brief.py 的 try_parse_block docstring（引的 canonical 原句 2026-08-26 已被更正）。適用時機：aiwf#165 因掃描紅而合併不了時；或要引用這兩處註解時。⛔ 非射程：不改掃描器判準、不擴大偵測面、不做窮舉掃描、零行為改動。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：**痛點**：三處引用今天帶不到讀者該去的地方，其中一處正在擋 CI。(1) scripts/brief_backfill/snapshot_population.py 第 5 行**完整逐字**為「⛔ 不寫任何東西到 GitHub。⛔ 不用 ``gh project item-list``（中文欄位 key 編碼壞，見 project.py:377）——一律走 ``wf_cli.project.list_items``，使盤點與守衛同源。」⚠️⚠️ **本卡要修的只有 project.py:377 這個行號指標，⛔ 不是那句話的結論**——「不用 item-list、改走 list_items」今日仍為真且該行已自己寫出正解（PM 實測：gh api graphql 回傳的欄位名一字未壞）。那個指標指的「中文欄位 key 編碼壞」在 cli/src/wf_cli/project.py 的實際位置，於 main 54d23e87 是第 509-510 行、於 aiwf#165 的分支 a715ae8 是第 526-527 行，⛔ **從來不在 377**；引入它的 commit 764a59ff 上第 377 行是 args += ["--text", str(value)] ⇒ **它從出生就錯 132 行**。⭐ 而它對兩道守衛都是隱形的：aiwf#159 的判準逐字是「指向空行或不存在檔」而它當時指的是非空行故不紅（#159 動的 16 個檔不含本檔、卡面提及 0 次）；aiwf#146 掃描器 docstring 逐字「⛔ 不驗指得對不對。目標行非空即算過」「任何由本腳本得到的紅數都是下界」。它今天轉紅純粹是因為 aiwf#165 在 project.py 前面插了淨 17 行把它推到空行上——那是運氣不是偵測。⇒ 現況：qualified_pointer_scan.py rc=1 紅 1，cli/tests/test_qualified_pointer_scan.py 三條紅，CI run 33143969013 @ a715ae8 conclusion=failure，⇒ **aiwf#165 即使查核通過也合併不了**（ruleset 是 main must be green + strict + required context tests，⛔ 不讀卡面驗收條）。(2) cli/src/wf_cli/registry.py 的 fetch_project_rows docstring 逐字「刻意**不用** ``gh project item-list``：它對中文欄位名的 JSON key 有編碼錯誤（``project.py::list_items`` 已記錄此雷；本檔實測 ``卡ID`` 被輸出成 U+FFFD）」——PM 掃兩 repo 全部 8 處提及，**這是唯一一處只寫「不要用什麼」而⛔ 沒寫「改用什麼」**，讀者會停在「這是個沒解的問題」。(3) cli/src/wf_cli/brief.py 的 try_parse_block docstring 第 170-171 行逐字「⚠️ 既有卡在簡介欄位上線前一律沒有簡介（canonical §6.3 逐字：今天沒有任何卡符合這一條）」——它引的原句已被更正，canonical 現行段落逐字寫「⚠️ 本段於 2026-08-26 更正。原文逐字寫『今天沒有任何卡符合這一條』」⇒ 該引用今天指向一句已經不存在的話。⛔ 非射程：⛔ 不改 qualified_pointer_scan.py 的判準、⛔ 不擴大掃描器的偵測面（「指錯但落在非空行的永遠隱形」是另一張研究卡的射程）、⛔ 不做任何窮舉掃描找同族第四處、⛔ 不碰 cpbl roadmap_lines.py 那句錯誤診斷（「欄名開頭的 emoji 被打爛」，而欄名裡沒有 emoji；屬 cpbl 的卡）、⛔ 零行為改動。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:scripts/brief_backfill/snapshot_population.py",
    "file:cli/src/wf_cli/brief.py",
    "file:cli/src/wf_cli/registry.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] A1 scripts/brief_backfill/snapshot_population.py 第 5 行的 project.py:377 換成不會位移的錨點（符號名或該行的實際字面），⛔ 不得換成另一個行號。⚠️ 破折號後的「一律走 wf_cli.project.list_items，使盤點與守衛同源」逐字保留、一個字不動——本卡修的是指標，⛔ 不是那句話的結論。什麼會推翻它：改後仍是 檔:行號 形式，或那句結論被改寫。
- [ ] A2 cli/src/wf_cli/registry.py 的 fetch_project_rows docstring 補上「改用什麼」。⚠️⚠️ **執行者須先讀碼確認 fetch_project_rows 實際走的是哪條路徑**，⛔ 不得照抄 project.py 那句「改走 list_items」——PM 初判該函式自己就走 GraphQL，⇒ 正確寫法可能是「本函式自己就是那個正解」而非指去別處，但這須由執行者以碼驗證後決定。什麼會推翻它：補上的敘述與該函式實際的資料來源不符。
- [ ] A3 cli/src/wf_cli/brief.py 的 try_parse_block docstring 第 170-171 行，改掉對已被更正原句的引用。逐字現況「⚠️ 既有卡在簡介欄位上線前一律沒有簡介（canonical §6.3 逐字：今天沒有任何卡符合這一條）」，而 canonical 現行段落逐字寫「⚠️ 本段於 2026-08-26 更正。原文逐字寫『今天沒有任何卡符合這一條』」⇒ 它引的是一句已經不存在的話。⚠️ 該 docstring 的功能敘述（解析失敗回 None，供缺簡介不阻擋任何動詞的 fail-open 路徑使用）今日仍為真，⛔ 不得一併改掉。
- [ ] A4 ⛔ 不得引入任何新的 檔:行號 形式指標。依據：DOC-STALE-FILE-LINE-POINTERS1（aiwf#159）的實例——主旨寫「移除行號引用」的 commit 自己留下 2 個新行號、26 小時內失效。⭐ 本卡整張的主題就是這個，重犯即自我推翻。
- [ ] A5 ⛔ 零行為改動：只改註解與 docstring 文字。什麼會推翻它：git diff --name-only 出現三個宣告檔以外的檔，或任何一行非註解、非 docstring 的改動。宣告資源為 file:scripts/brief_backfill/snapshot_population.py、file:cli/src/wf_cli/brief.py、file:cli/src/wf_cli/registry.py。
- [ ] A6 掃描與測試由紅轉綠：scripts/qualified_pointer_scan.py 在交付 SHA 上 rc=0、紅 0；cli/tests/test_qualified_pointer_scan.py 的三條紅（test_repo_wide_scan_finds_no_broken_qualified_pointers、test_the_two_intentional_placeholders_are_exempted_not_missed、test_cli_exits_zero_on_the_real_repo）全綠。⚠️ 那三條今天紅在 aiwf#165 的分支上；本卡基線是 main，須在 main 上先確認它們今天是綠的、再確認改動後仍綠。⛔ 不得靠改 EXEMPTIONS 登記簿或縮短文字讓行號落回非空行達成——那是看著答案調判準，本 repo 已具名禁止。

## 驗證

- [ ] V1 三處逐處貼出「改前逐字 → 改後逐字 → 什麼會讓這個引用再指錯」。⛔ 不得摘要合併。
- [ ] V2 A2 的判斷須附碼證據：貼出 fetch_project_rows 實際取資料那幾行，證明你補的「改用什麼」與它真正走的路徑一致。⛔ 不接受「照 project.py 的寫法」這種理由。
- [ ] V3 scripts/qualified_pointer_scan.py 在 merge-base 與交付 SHA 各跑一次，逐項貼 rc 與宇宙／可強制／紅三個數字（預期紅由 1 降為 0、宇宙少 1）。⛔ 不接管線——| tail 會把 $? 換成 tail 的 rc。
- [ ] V4 回歸不退化，量在交付 SHA，rc 分開跑並逐項貼，⛔ 全部不接管線：uv run --frozen --project cli pytest -q 的 rc=0 且通過數 >= merge-base 的通過數（merge-base 的數字也要自己跑一次）；uv lock --check、scripts/replay_escalation_rules.py、scripts/canonical_citation_scan.py、scripts/contract_tool_reconcile.py --check、scripts/qualified_pointer_scan.py 五項 rc 全 0。⚠️ 腳本以 CI 釘死的 python 3.12 跑。
- [ ] V5 commit trailer 四行連續、無空行斷開、置於 message 最後一段：Requested-by / Planned-by / Implemented-by / Co-Authored-By。以 git interpret-trailers --parse 實際解析結果為準並貼出。⚠️ 今日另一張卡就是栽在這裡（跑單一測試檔沒跑全套，漏掉 trailer 守衛的紅）。
- [ ] V6 ⛔ 射程誠實：交付須逐字寫出本卡不涵蓋什麼——⛔ 不改 qualified_pointer_scan.py 的判準、⛔ 不擴大掃描器偵測面、⛔ 不做窮舉掃描找同族第四處、⛔ 不碰 cpbl roadmap_lines.py 的錯誤診斷、⛔ 零行為改動。什麼會推翻它：交付出現「同族已清乾淨」這類未收窄的宣稱。

## Log

- 2026-08-28T14:12:06+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-28T14:20:56+08:00 amend by wf-cli（op 8c5bbf97）→ 核心痛點：原值「**痛點**：兩處引用今天指不到它們說的東西，其中一處正在擋 CI。(1) scripts/brief_backfill/snapshot_population.py 第 5 行逐字「⛔ 不用 ``gh project item-list``（中文欄位 key 編碼壞，見 project.py:377）」——那句「中文欄位 key 編碼壞」在 cli/src/wf_cli/project.py 的實際位置，於 main 54d23e87 是第 509-510 行、於 aiwf#165 的分支 a715ae8 是第 526-527 行，⛔ **從來不在 377**；引入它的 commit 764a59ff 上第 377 行是 args += ["--text", str(value)] ⇒ **它從出生就錯 132 行**。⭐ 而它對兩道守衛都是隱形的：aiwf#159 的判準逐字是「指向空行或不存在檔」而它當時指的是非空行故不紅（#159 動的 16 個檔不含本檔、卡面提及 0 次）；aiwf#146 掃描器 docstring 逐字「⛔ 不驗指得對不對。目標行非空即算過」「任何由本腳本得到的紅數都是下界」。它今天轉紅純粹是因為 aiwf#165 在 project.py 前面插了淨 17 行把它推到空行上——那是運氣不是偵測。⇒ 現況：qualified_pointer_scan.py rc=1 紅 1，cli/tests/test_qualified_pointer_scan.py 三條紅，CI run 33143969013 @ a715ae8 conclusion=failure，⇒ **aiwf#165 即使查核通過也合併不了**（ruleset 是 main must be green + strict + required context tests，⛔ 不讀卡面驗收條）。(2) cli/src/wf_cli/brief.py 的 try_parse_block docstring 第 170-171 行逐字「⚠️ 既有卡在簡介欄位上線前一律沒有簡介（canonical §6.3 逐字：今天沒有任何卡符合這一條）」——它引的原句已被更正，canonical 現行段落逐字寫「⚠️ 本段於 2026-08-26 更正。原文逐字寫『今天沒有任何卡符合這一條』」⇒ 該引用今天指向一句已經不存在的話。⛔ 非射程：⛔ 不改 qualified_pointer_scan.py 的判準、⛔ 不擴大掃描器的偵測面（「指錯但落在非空行的永遠隱形」是另一張研究卡的射程）、⛔ 不做任何窮舉掃描找同族第三處、⛔ 零行為改動。」→ 新值「**痛點**：三處引用今天帶不到讀者該去的地方，其中一處正在擋 CI。(1) scripts/brief_backfill/snapshot_population.py 第 5 行**完整逐字**為「⛔ 不寫任何東西到 GitHub。⛔ 不用 ``gh project item-list``（中文欄位 key 編碼壞，見 project.py:377）——一律走 ``wf_cli.project.list_items``，使盤點與守衛同源。」⚠️⚠️ **本卡要修的只有 project.py:377 這個行號指標，⛔ 不是那句話的結論**——「不用 item-list、改走 list_items」今日仍為真且該行已自己寫出正解（PM 實測：gh api graphql 回傳的欄位名一字未壞）。那個指標指的「中文欄位 key 編碼壞」在 cli/src/wf_cli/project.py 的實際位置，於 main 54d23e87 是第 509-510 行、於 aiwf#165 的分支 a715ae8 是第 526-527 行，⛔ **從來不在 377**；引入它的 commit 764a59ff 上第 377 行是 args += ["--text", str(value)] ⇒ **它從出生就錯 132 行**。⭐ 而它對兩道守衛都是隱形的：aiwf#159 的判準逐字是「指向空行或不存在檔」而它當時指的是非空行故不紅（#159 動的 16 個檔不含本檔、卡面提及 0 次）；aiwf#146 掃描器 docstring 逐字「⛔ 不驗指得對不對。目標行非空即算過」「任何由本腳本得到的紅數都是下界」。它今天轉紅純粹是因為 aiwf#165 在 project.py 前面插了淨 17 行把它推到空行上——那是運氣不是偵測。⇒ 現況：qualified_pointer_scan.py rc=1 紅 1，cli/tests/test_qualified_pointer_scan.py 三條紅，CI run 33143969013 @ a715ae8 conclusion=failure，⇒ **aiwf#165 即使查核通過也合併不了**（ruleset 是 main must be green + strict + required context tests，⛔ 不讀卡面驗收條）。(2) cli/src/wf_cli/registry.py 的 fetch_project_rows docstring 逐字「刻意**不用** ``gh project item-list``：它對中文欄位名的 JSON key 有編碼錯誤（``project.py::list_items`` 已記錄此雷；本檔實測 ``卡ID`` 被輸出成 U+FFFD）」——PM 掃兩 repo 全部 8 處提及，**這是唯一一處只寫「不要用什麼」而⛔ 沒寫「改用什麼」**，讀者會停在「這是個沒解的問題」。(3) cli/src/wf_cli/brief.py 的 try_parse_block docstring 第 170-171 行逐字「⚠️ 既有卡在簡介欄位上線前一律沒有簡介（canonical §6.3 逐字：今天沒有任何卡符合這一條）」——它引的原句已被更正，canonical 現行段落逐字寫「⚠️ 本段於 2026-08-26 更正。原文逐字寫『今天沒有任何卡符合這一條』」⇒ 該引用今天指向一句已經不存在的話。⛔ 非射程：⛔ 不改 qualified_pointer_scan.py 的判準、⛔ 不擴大掃描器的偵測面（「指錯但落在非空行的永遠隱形」是另一張研究卡的射程）、⛔ 不做任何窮舉掃描找同族第四處、⛔ 不碰 cpbl roadmap_lines.py 那句錯誤診斷（「欄名開頭的 emoji 被打爛」，而欄名裡沒有 emoji；屬 cpbl 的卡）、⛔ 零行為改動。」（⚠️ 全文：totalCount=0（首寫，平台無前一版））；理由 需求方 2026-08-28 裁定（issuecomment-5449168296）：開卡時 PM 截斷了 snapshot_population.py:5 的引述，砍掉破折號後的「一律走 wf_cli.project.list_items」正解，使卡面讀起來像那是個沒解的問題——⛔ 製造該誤會的是 PM 不是原作者。本次改為完整引述並逐字載明本卡只修那個行號指標、⛔ 不是那句話的結論。同時依裁定把 cli/src/wf_cli/registry.py 納入——PM 掃兩 repo 8 處提及，它是唯一一處只寫「不要用什麼」而沒寫「改用什麼」。⛔ cpbl roadmap_lines.py 的錯誤診斷不納入（屬 cpbl 的卡）。；授權 依需求方 ruan6047 於 https://github.com/ruan6047/ai-workflow/issues/166#issuecomment-5449168296 的裁定（已核對：該 URL 指向本卡 issue 的既存留言，且其 GitHub author 欄逐字等於卡面「需求：」欄。本指令不讀取留言內文或操作者身分，故不判定留言內容是否構成裁定——上句「裁定」是操作者的宣告，不是本指令查得的事實——亦不區分「需求方本人張貼」與「他人代擬代貼」）。
- 2026-08-28T14:21:29+08:00 amend by wf-cli（op 978f78bc）→ 資源宣告：原值指紋 sha256:0d540fb0a68817ab9e8ce8dd26a7c3ac60e69e99c448765016a06a1c54f678be (213 bytes) → 新值指紋 sha256:6d1d0e918c582619ad2ec04971fa998e1989f4dc79365a175a4d570606240a2c (131 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 依需求方裁定 issuecomment-5449168296 第 2 點把 cli/src/wf_cli/registry.py 納入射程，資源宣告同步擴充。⚠️ --resources 是整份取代，故三個檔全列。互斥複驗（2026-08-28 看板快照）：宣告 brief.py 的 WF-CARD-BRIEF-AND-TWO-AXIS-WRITE1、宣告 snapshot_population 的 WF-CARD-BRIEF-BACKFILL1 皆 🏁完成；registry.py 於本次擴充前無活卡宣告。⛔ 交集檢查只擋已認領且非終態的卡，開工前仍須重跑。。
- 2026-08-28T14:23:36+08:00 amend by wf-cli（op 7b6c92d5）→ 驗收條件：原值指紋 sha256:268b4facf0d0fd887895f6e57a0cdd3b1af9115e6fa1e969fd3a9fcc18405f66 (41 bytes) → 新值指紋 sha256:087a9c98ce4ed0073e4b83ca36f1927221d96118883f1e5a21113461c1b93613 (2791 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 填實驗收與驗證（open 時為 TODO 佔位符）。⚠️ A6 刻意寫成「由紅轉綠」而⛔ 不是像 aiwf#165 的原 A7 那樣寫成「repo 全域紅數 0」——本卡的改動正是移除那筆紅，rc=0 是它能控制的量；aiwf#165 不能，那條驗收條已因此被裁定修正。A2 明文要求執行者先讀碼、⛔ 不得照抄 project.py 的寫法。V5 釘 trailer 是因為今天另一張卡在此栽過。。
- 2026-08-28T14:23:36+08:00 amend by wf-cli（op 7b6c92d5）→ 驗證：原值指紋 sha256:90fbd8cfc6fb7de40197d7b06994d08cc624908b02039602d773fcbeb65bed42 (44 bytes) → 新值指紋 sha256:079b4082265ceb3a7ae3eb4fc6fb824b620f2e2c6ae30ef48e633cbc107add16 (1732 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 填實驗收與驗證（open 時為 TODO 佔位符）。⚠️ A6 刻意寫成「由紅轉綠」而⛔ 不是像 aiwf#165 的原 A7 那樣寫成「repo 全域紅數 0」——本卡的改動正是移除那筆紅，rc=0 是它能控制的量；aiwf#165 不能，那條驗收條已因此被裁定修正。A2 明文要求執行者先讀碼、⛔ 不得照抄 project.py 的寫法。V5 釘 trailer 是因為今天另一張卡在此栽過。。
- 2026-08-28T14:24:31+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree ai/opus-5/DOC-CITATION-POINTS-ELSEWHERE1 @ /Users/ruanruan/Dev/ai-workflow/.worktrees/citation-anchor；交付狀態 🔨執行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-28T14:24:48+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 1；SHA 54d23e87873e1239a8bff4cbbb2af0c7c5c805fe；階段 需求；踩坑回應 8 族（已檢查 1／不適用 0／發現 7）；證據 首次派工。分支 ai/opus-5/DOC-CITATION-POINTS-ELSEWHERE1 @ /Users/ruanruan/Dev/ai-workflow/.worktrees/citation-anchor，基線 54d23e87。三處引用帶不到讀者該去的地方：snapshot_population.py:5 的 project.py:377（從出生就錯 132 行，現正擋住 aiwf#165 的 CI）、registry.py 的 fetch_project_rows docstring（8 處提及裡唯一只寫「不要用什麼」的）、brief.py:170-171（引的 canonical 原句 2026-08-26 已被更正）。⭐ A2 須先讀碼確認 fetch_project_rows 實際走哪條路，⛔ 不得照抄 project.py。⛔ A4 不得引入新的 檔:行號（本卡主題就是這個，重犯即自我推翻）。⛔ A6 不得靠改 EXEMPTIONS 或縮短文字讓行號落回非空行。。
- 2026-08-28T14:58:42+08:00 handoff by wf-cli → owner 待指派；iteration 1；SHA 79b1418ad552b067e5c520d6cb0d9a63dfdf4311；階段 執行；踩坑回應 13 族（已檢查 5／不適用 1／發現 7）；證據 送審。分支 ai/opus-5/DOC-CITATION-POINTS-ELSEWHERE1 @ 79b1418ad552b067e5c520d6cb0d9a63dfdf4311（已推 origin）；基線 54d23e87873e1239a8bff4cbbb2af0c7c5c805fe；改動恰為三個宣告檔（brief.py +9/-2、registry.py +7、snapshot_population.py +2/-1）。⚠️ 卡面兩處由 PM 寫錯，執行者未粉飾而是逐字指出（attribution 皆為 planner）：(1) A2 指名的 fetch_project_rows 在 repo 內 0 定義，真符號是 _run_gh_graphql，⭐ 而唯一出現該字樣處是測試名 test_registry.py:778，它自己就是同族過期指標；(2) V3 括號寫「預期紅由 1 降為 0」而 main 基線上紅本來就是 0——那筆紅只存在於 aiwf#165 的分支。PM 獨立重跑（⛔ 非轉述）：git diff --stat 恰三檔 15 insertions／3 deletions；qualified_pointer_scan.py rc=0，宇宙 81→80、可強制 79→78、紅 0；uv run --frozen --project cli pytest -q rc=0 1479 passed 1 skipped，與 merge-base 的 1479 相同未退化。PM 另複驗執行者順帶登記的第四處：全 repo 引「今天沒有任何卡符合這一條」者現剩 AI_WORKFLOW.md:773（更正段落自身）與 cli/src/wf_cli/card.py:1622（amend_brief docstring），後者⛔ 未修、不在宣告資源內。執行者的交付報告、失誤登記（4 筆）與未驗清單（6 筆）全文由 PM 於卡上留言代貼——⚠️ 本欄寫下時該留言尚未張貼，PM 將於本次 handoff 後立即補上並在該則自述；⛔ 查核者若在卡上看不到它，請以此欄為準並開 finding。。
- 2026-08-28T15:48:39+08:00 review by wf-cli → APPROVE（✅通過）；查核者 Claude Opus 5@Claude Code (Reviewer)；core_pain_resolved yes；self_run 21 項；findings 4 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt DOC-CITATION-POINTS-ELSEWHERE1-e0-79b1418ad552b067e5c520d6cb0d9a63dfdf4311。
- 2026-08-28T16:09:50+08:00 handoff by wf-cli → owner ruan6047；iteration 1；SHA f0dfcfc688999f75f9cb57d606fd1255f7e4528e；階段 審核；踩坑回應 8 族（已檢查 4／不適用 1／發現 3）；證據 R1 查核 APPROVE（Claude Opus 5@Claude Code (Reviewer)，四筆非阻擋：R1-01 minor／R1-02 info（皆 planner）＋ R1-03 minor／R1-04 info（皆 executor））。受審 SHA 79b1418ad552b067e5c520d6cb0d9a63dfdf4311；PR https://github.com/ruan6047/ai-workflow/pull/168 squash 合併為 f0dfcfc688999f75f9cb57d606fd1255f7e4528e，CI 兩項 check 全 pass（run 33154100694 為 merge 結果）。⚠️ 未閉環項逐項：(1) R1-01：PM 在 A2 逐字指名的 fetch_project_rows 在 repo 內 0 定義（真符號 _run_gh_graphql），⛔ 卡面未修；查核者判未污染交付（卡面同時給了逐字 docstring 內容當冗餘識別子），但明記「這次能救回來只因為卡面有冗餘識別子，不是因為錯得無害」。(2) R1-02：PM 在 V3 括號寫「預期紅由 1 降為 0」而 main 基線紅本來就是 0，⛔ 卡面未修。(3) R1-03（executor）：A3 的再變假條件清單缺一條靜默路徑——若 validation.py 日後只對新卡加簡介檢查，docstring 的「validation.py 完全不驗簡介」即為假而 try_parse_block 的 fail-open 行為完全不用改；反例來源是 canonical §6.3 自己逐字寫的承接者「既有卡的補寫與新卡的必填時點」（AI_WORKFLOW.md:771，PM 已複驗）。⛔ 未要求返工。(4) R1-04（executor）：A2 的清單缺「gh 修掉 item-list 的 key 編碼 bug」這條，且 docstring 內無 gh 版本錨。⛔ 未處置。(5) ⭐ 全卡最大的未收窄：新錨點只在改名時腐爛，而改名這條今天沒有任何機械守衛擋得住——查核者實測 qualified_pointer_scan 的 _POINTER 與 canonical_citation_scan 的 _QUALIFIED_REF 兩條 regex 都硬性要求 :\d+，探針 project.py::list_items 0 命中。⇒ 這是把靜默腐爛換成改名時腐爛，⛔ 不是已解。(6) 同族第四處（card.py:1622）已由 aiwf#167 承接（🔍待查核）；⛔ 未做窮舉掃描，同族有無第五處未量測。(7) 範圍外 O-2（查核者提出、⛔ 未開卡）：cli/tests/test_registry.py:778 的測試名 test_fetch_project_rows_... 指向 0 定義的符號，⭐ 而它正是製造本卡 A2 卡面缺陷的那個陷阱，留著下一個規劃者會再踩一次。(8) 範圍外 O-3：A1 的新錨點送讀者到 list_items 的 docstring，而該 docstring 自己的後續指標「見 OPS-STATE-PLANE-MIG1 Task 1「意外發現」」有歧義——cpbl 該檔內有兩個含「意外發現」的標題，先命中的是主題不同的那個。；收尾清理：已清除 worktree；遠端分支 本來就不存在；本地分支 依授權保留（未刪除）。


## Comment 5449168296 · 2026-08-28T06:20:12Z

## 需求方裁定：核心痛點改為完整引述，並把 `registry.py` 納入射程

**轉錄自述**：本則由 **PM（Claude Opus 5@Claude Code）** 以需求方 token 發文；author 欄恆為 `ruan6047`，⛔ 不代表由需求方撰寫。需求方於對話中先提出問題，逐字為：「**如果有解為什麼文件還要寫中文欄位 key 編碼壞 而不是提正確方案 這樣容易造成沒有修的誤會**」；PM 量測並提出建議後，需求方回覆逐字「**好**」。

### ⛔ 開卡時 PM 截斷了證據，砍掉的那半改變了意思

本卡開卡時，核心痛點引 `scripts/brief_backfill/snapshot_population.py` 第 5 行為：

> ⛔ 不用 ``gh project item-list``（中文欄位 key 編碼壞，見 project.py:377）

**原文不是這樣。** 完整逐字是：

> ⛔ 不寫任何東西到 GitHub。⛔ 不用 ``gh project item-list``（中文欄位 key 編碼壞，見 project.py:377）——**一律走 ``wf_cli.project.list_items``，使盤點與守衛同源。**

⇒ PM 引了括號裡的**病因**、砍掉了破折號後的**正解**。後人讀本卡卡面會以為那是個沒解的問題——⭐ **而製造那個誤會的是 PM，⛔ 不是原作者。**

### 量測：8 處提及裡有 7 處寫了正解

PM 於 2026-08-28 掃兩 repo（`ai-workflow` main `54d23e87`、`cpbl-analytics` main `3b470d70`，排除 worktree 副本）：

| 位置 | 有無正解 |
|---|---|
| `cli/src/wf_cli/project.py`（`list_items` docstring） | ✅「刻意走原生 GraphQL 分頁查詢」在前 |
| `cli/src/wf_cli/gh.py`（`graphql` docstring） | ✅「所有批次讀取一律走這裡的原生 GraphQL」 |
| `cli/tests/test_marker_write_boundary.py` | ✅「⛔ 走 `project.list_items`（wfcli 自己的讀取路徑）」在前 |
| `scripts/brief_backfill/snapshot_population.py` | ✅「一律走 `wf_cli.project.list_items`」 |
| cpbl `docs/research/OPS-STATE-PLANE-MIG1_field_mapping.md` | ✅ 最完整：「這是 `gh` CLI（2.92.0）這個便利指令本身的問題，不是資料毀損——改用 `gh api graphql` 搭配 `fieldValueByName`，回傳完全正確」 |
| cpbl `scripts/state_plane_migrate.py` | ✅「已知陷阱（本腳本已規避）……讀回一律走 `gh api graphql`」 |
| cpbl `scripts/roadmap_lines.py` | ✅ 特例（它吃 stdin 的 item-list JSON、走不了 GraphQL，故用後綴），且自書「先精確、後後綴」與自審反例 |
| **`cli/src/wf_cli/registry.py`** | ⛔ **無** ——「刻意**不用** `gh project item-list`：它對中文欄位名的 JSON key 有編碼錯誤（`project.py::list_items` 已記錄此雷；本檔實測 `卡ID` 被輸出成 U+FFFD）」只講不要用什麼、⛔ 沒講改用什麼 |

PM 亦實測確認**確實有解**：`gh api graphql` 回傳的欄位名一字未壞（`卡ID Initiative 級別 功能 owner 分支／worktree iteration 交付狀態 部署狀態 最後交接 服務的原始目標 鏈深 分支worktree 資源宣告 簡介 階段`）。壞的只有 `gh project item-list --format json` 那一條路徑，成因是 `gh` 2.92.0 把欄位名轉 JSON key 時對**第一個 byte** 做小寫轉換，而中文首字佔 3 個 byte。

### 裁定

1. **核心痛點改為完整引述** `snapshot_population.py:5`，把「一律走 `wf_cli.project.list_items`」補回去，並逐字載明本卡要修的是**那個行號指標**、⛔ 不是那句話的結論（該結論今日仍為真且已寫出正解）。
2. **`cli/src/wf_cli/registry.py` 納入射程**：它是 8 處裡唯一沒有把讀者帶到正解的一處，與本卡是同一件事（引用沒把讀者帶到它該去的地方），⛔ 不是另一個問題。資源宣告同步擴充。
3. ⛔ **cpbl `roadmap_lines.py` 的錯誤診斷不納入**（該註解逐字寫「欄名開頭的 emoji 被打爛」，而欄名裡沒有 emoji——`卡ID` 首字是「卡」）。那是 cpbl 的卡，⛔ 不混進本卡。
4. ⛔ **不改 `gh` 的行為、⛔ 不改任何讀取路徑**：本卡只動註解文字，零行為改動不變。


## Comment 5449473851 · 2026-08-28T07:00:30Z

## 執行者交回：交付報告、失誤登記與未驗清單（`DOC-CITATION-POINTS-ELSEWHERE1` / #166）

> **轉錄自述**：本則由 **PM（Claude Opus 5@Claude Code）** 以需求方 token 發文，內容為**執行者 `Claude Opus 5@Claude Code` 交回 PM 的報告逐字轉錄**。⛔ PM 未修改任何一個字、未增刪任何一項。平台上的 author 欄恆為 `ruan6047`（token 持有者），⛔ 不代表本文由需求方撰寫。踩坑清冊 13 族的回應由 PM 依此報告改寫後寫入 handoff 事件，⛔ 非逐字等同本則。

**交付 SHA** `79b1418ad552b067e5c520d6cb0d9a63dfdf4311`；基線 `54d23e87873e1239a8bff4cbbb2af0c7c5c805fe`。
`git diff --stat`：`brief.py 9 +++++++--`／`registry.py 7 +++++++`／`snapshot_population.py 2 +-`，共 `3 files changed, 15 insertions(+), 3 deletions(-)`。

### ⚠️ 卡面與現實的落差（A2）

**A2 逐字指名「`cli/src/wf_cli/registry.py` 的 `fetch_project_rows` docstring」，但該符號在 repo 內不存在。** `grep -rn "def fetch_project_rows"` rc=1、0 命中。repo 內只有 `_run_gh_graphql`（承載卡面逐字引用的那段 docstring）與 `fetch_project_ownership_rows`（分頁取列）。唯一出現 `fetch_project_rows` 字樣的地方是測試名 `cli/tests/test_registry.py::test_fetch_project_rows_paginates_and_drops_rows_without_worktree`——**那個測試名自己就是同一族的過期指標**。執行者以卡面同時給出的逐字 docstring 內容定位，命中 `_run_gh_graphql`，逐字完全吻合；⛔ 未自行改寫卡面，也未修那個過期測試名（不在宣告資源內）。

### V1 三處逐處

**(1) `snapshot_population.py` 模組 docstring**：`見 project.py:377）` → `見 ``project.py::list_items``）`。破折號後的「——一律走 `wf_cli.project.list_items`，使盤點與守衛同源。」逐字未動、仍連續落在同一行未被換行切開。錨點理由：本 repo 既有形式（`registry.py` 同段 docstring、`docs/CONTRACT_TOOL_RECONCILE.md` 大量使用 `檔::符號`）；`project.py` 在 `git ls-files` 內唯一；病因原文確實寫在 `list_items` 的 docstring 裡。
**什麼會讓它再指錯**：`list_items` 被改名、或病因說明搬到別的符號底下；`project.py` 被搬走或出現第二個同名檔。⛔ 插行刪行搬段落不再會讓它失效——那正是舊指標的失效方式。⚠️ **誠實補一句：上述三種失效今天沒有任何機械守衛擋得住**（`qualified_pointer_scan.py` 只認 `檔:行號`）⇒ 這是把「會靜默腐爛」換成「只在改名時腐爛」，⛔ 不是「已解」。

**(2) `registry.py` 的 `_run_gh_graphql` docstring**：原兩段一字未動，其後**新增**一段，逐字為「⭐ **改用什麼：就是本函式走的這一條，⛔ 不必去別處找解。** 壞掉的只有 `gh project item-list --format json` 把欄位名轉成 JSON key 的那一步；`gh api graphql` 根本沒有那一步——欄位名是 `_PROJECT_ITEMS_GQL` 裡 `field { name }` 回傳的**值**，由 `fetch_project_ownership_rows` 在 Python 端自己拿它當 dict 的鍵。同一個 `卡ID` 在本路徑實測一字未壞（2026-08-28，Project #4 首頁 50 筆，無任何 U+FFFD）。」
**什麼會讓它再指錯**：`_PROJECT_ITEMS_GQL` 改成不再要 `field { name }`，或取列邏輯搬離 `fetch_project_ownership_rows`；本函式改成呼叫 `gh project item-list`。⚠️ 那句實測是有日期、有母體、有量法的觀察，⛔ 不是恆真宣稱。

**(3) `brief.py` 的 `try_parse_block` docstring**：改後逐字為「⚠️ 缺簡介是**構造上合法**的狀態：`--brief` 在 `open`／`amend` 都只是可選旗標（兩處皆 `default=None`），`validation.py` 也完全不驗簡介（canonical §6.3〈卡片簡介〉）。⛔ 不得讓這些卡因缺欄位而無法 `amend` 或 `handoff`。」＋「⛔ 此處刻意只轉述該節的判準、不逐字引它的句子：原先引的那一句已於 2026-08-26 被 canonical 自己更正掉，⇒ 逐字轉引等於另立一份會獨立腐爛的副本。」功能敘述那一行逐字未動。兩個事實各自以碼驗證：`open_cmd.py:86-87` 與 `amend_cmd.py:377-378` 皆 `default=None`；`grep -c "brief" cli/src/wf_cli/validation.py` = 0。
**什麼會讓它再指錯**：`--brief` 變必填或 `validation.py` 開始驗簡介（⚠️ 但那同時也會讓 fail-open 這條路本身該被重新檢討，⇒ 失效方向是連函式行為一起要改，不是靜默指錯）；canonical §6.3 被改號或改名——已保留 `§6.3` 並加上節標題〈卡片簡介〉讓改號後仍搜得到。⭐ 舊寫法的失效方式（來源把那句話更正掉、引用端毫無所覺）已消除。

### V2 A2 的碼證據

`_run_gh_graphql` 實際取資料：`subprocess.run(["gh", "api", "graphql", "--input", "-"], input=json.dumps(payload), ...)` → `json.loads(proc.stdout)`。欄位名來源（`_PROJECT_ITEMS_GQL` 逐字）：`fieldValues(first:50){nodes{__typename ... on ProjectV2ItemFieldTextValue{text field{... on ProjectV2FieldCommon{name}}}}}`。消費端（`fetch_project_ownership_rows`）：`name = (fv.get("field") or {}).get("name")` → `fields[name] = fv["text"]`。⇒ 欄位名是 GraphQL 回應裡 `field.name` 的**值**，dict 的鍵由本檔在 Python 端組出來，**全程沒有「gh 把欄位名轉成 JSON key」那一步**。

活體實測（唯讀，用 `registry.py` 自己的 `_PROJECT_ITEMS_GQL` 與 `_run_gh_graphql`，Project #4 首頁 50 筆，2026-08-28T14:3x+08:00）：`first-page nodes: 50`；`distinct field names seen: ['Title', '卡ID', 'Initiative', '功能', 'owner', '分支／worktree', '最後交接', '服務的原始目標', '簡介', '分支worktree', '資源宣告']`；`U+FFFD present in any name: False`。

### V3 掃描器兩次

指令皆 `uv run --no-project --python 3.12 scripts/qualified_pointer_scan.py`，⛔ 未接管線、rc 單獨 `echo $?`。

| 量在哪 | rc | 宇宙 | 可強制 | 紅（不含豁免） |
|---|---|---|---|---|
| merge-base `54d23e87`（2026-08-28T14:27+08:00） | 0 | 81 | 79 | 0 |
| 交付 `79b1418a`（2026-08-28T14:39+08:00） | 0 | 80 | 78 | 0 |

⚠️ **與 V3 括號裡的預期有一處不符，我不粉飾**：V3 寫「預期紅由 1 降為 0」，但**在 main 基線上紅本來就是 0**——那筆紅只存在於 `aiwf#165` 的分支（該分支在 `project.py` 前面插了淨 17 行，把行號推到空行）。A6 自己已載明這件事。⇒ 實際結果是**宇宙少 1（81→80）、紅 0→0**，⛔ 不是 1→0。

`project.py:377` 在 merge-base 的 `--all` 輸出裡逐字為 `scripts/brief_backfill/snapshot_population.py 第 5 行: [ok] project.py:377 → cli/src/wf_cli/project.py`；交付 SHA 上該筆已不存在（宇宙 -1 的來源）。

A6 三條測試 @ `79b1418a`：三條皆 `PASSED`、`37 passed in 6.60s`、rc=0；同三條在 merge-base 上先跑過一次 `3 passed, 34 deselected`（rc=0）⇒ **改動前綠、改動後仍綠**。⛔ `EXEMPTIONS` 一字未動、⛔ 未縮短或改寫任何文字讓行號落回非空行。

### V4 回歸（六項各自跑、rc 逐項印、⛔ 全部不接管線）

量在 `79b1418a`（`git status --porcelain` 為空）：`pytest -q` rc=0 `1479 passed, 1 skipped in 64.49s`；`uv lock --check` rc=0；`replay_escalation_rules.py` rc=0 `114/114 通過`；`canonical_citation_scan.py` rc=0 `掃描檔案數：155　命中（不含排除）：0`；`contract_tool_reconcile.py --check` rc=0 `59 個缺口全部有登記處置`；`qualified_pointer_scan.py` rc=0。

merge-base 對照同樣六項各跑一次：pytest rc=0 `1479 passed, 1 skipped in 63.48s`，其餘五項 rc 全 0。⇒ **通過數 1479 = merge-base 的 1479，未退化。** 那 1 個 skip 兩邊相同、與本卡無關：`SKIPPED [1] cli/tests/test_review.py:1620: 未設 CI 或 WF_LIVE_BOARD_CORPUS：本地預設不打網路`。

分支 CI（額外訊號，非 V4 要求）：run `33148723656`，`conclusion=success`；log 內 `checked-out = 79b1418ad552b067e5c520d6cb0d9a63dfdf4311`（⭐ 核的是這一行，⛔ 不是「最近一筆 run」）、`1480 passed in 43.02s`、`114/114 通過`。⚠️ 它的 job name 是 `tests (branch head)`，repo 自己的 CI 檔逐字說明這一支「永遠不是 required check，只是參考」。

**A5 零行為改動的機械證明**：三檔各自剝除 module／function／class 的 docstring 節點後 `ast.dump()` 與基線逐字相同——三檔皆 `True`。
**A4 未引入新指標**：以守衛測試檔自己的 `_load_module()` 載入掃描器、取其 `_POINTER` 屬性（⛔ 未重打 regex）套在 diff 的新增行上——新增 15 行、**命中 0 筆**；刪除 3 行、命中 1 筆（正是被移除的那個）。變異檢驗：人工塞一個由 `qps.pointer_token()` 拼出的合格指標，同一支檢查**會**命中 ⇒ 該 0 命中非零資訊。

### V5 trailer

`git interpret-trailers --parse` 解析出 `Requested-by: ruan6047`／`Planned-by: Claude Opus 5@Claude Code (PM)`／`Implemented-by: Claude Opus 5@Claude Code`／`Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`，rc=0。message 最後以 `cat -e` 檢視證明四行連續、⛔ 無空行斷開、且是最後一段。全套 `pytest -q` 已跑（1479 passed），⛔ 不是只跑單一測試檔 ⇒ trailer 守衛若存在也已被實際執行。

### V6 射程誠實（逐字）

本卡**不涵蓋**：⛔ 不改 `qualified_pointer_scan.py` 的判準、⛔ 不擴大掃描器的偵測面（「指錯但落在非空行的永遠隱形」不在本卡）、⛔ 不做任何窮舉掃描找同族第四處、⛔ 不碰 cpbl `roadmap_lines.py` 的錯誤診斷、⛔ 零行為改動。

⛔ 我**不宣稱**「同族已清乾淨」。⛔ 我**不宣稱**本卡讓 repo 全域的行號腐爛歸零——掃描器自己逐字寫「任何由本腳本得到的紅數都是**下界**」，而本卡修的三處裡**只有第一處在它射程內**，另外兩處它今天與明天都看不見。

**順帶命中、⛔ 未修、⛔ 未再擴大搜尋**：為了定位 canonical §6.3 現行段落，我必須 grep 那句被更正掉的原話，那一次 grep 回了兩筆——`AI_WORKFLOW.md`（更正段落自身）與 **`cli/src/wf_cli/card.py` 的 `amend_brief` docstring**，後者逐字寫「（canonical §6.3 逐字：今天沒有任何卡符合這一條）」，**與本卡 A3 修的是同一個病**。它不在宣告資源內 ⇒ 我沒有動它，也沒有再跑任何額外掃描去找更多。是否開卡由 PM 判斷。

### 失誤登記（逐項逐字）

1. **自寫 importlib loader 漏註冊 `sys.modules`，A4 檢查第一次 rc=1。** 我用 `importlib.util.module_from_spec` + `exec_module` 載入掃描器，沒有做 `sys.modules[spec.name] = mod`，`@dataclass(frozen=True)` 在 `_is_type` 走 `sys.modules.get(cls.__module__).__dict__` 時拿到 `None`，拋 `AttributeError`。⇒ **那是驗證器壞掉，不是改動有問題**，但它先印出了一個 rc=1。修法：改用守衛測試檔自己的 `_load_module()`，⛔ 不自寫。
2. **zsh 參數修飾詞吃掉 `$B:path`，一度輸出「改前逐字」的假象。** 我寫 `git show $B:scripts/...` 與 `git show $B:cli/...`；zsh 把 `:s` 當成替換修飾詞、`:c` 亦被吞，結果第一段印出的是 commit 訊息，第二段報 `fatal: ambiguous argument`。⇒ **差一點就把一段假的「改前逐字」寫進報告。** 修法：改寫字面 SHA 並整串加單引號。
3. **`pytest -q -rs` 未設 timeout，被 2 分鐘上限砍掉（rc=143）。** 重跑加 timeout 才拿到 skip 明細。⚠️ 該次耗時 253 秒，而同一棵樹前兩次是 63/64 秒——**我沒有查明為什麼變慢，⛔ 不宣稱原因**；可確認的只有通過數三次一致。
4. **A2 我一開始按卡面字面去找 `fetch_project_rows`，0 命中。** 我沒有立刻採信卡面，而是改以卡面同時給出的逐字 docstring 內容定位，命中 `_run_gh_graphql`。⇒ 沒有造成錯誤產出，但值得記：若卡面只給名字沒給逐字內容，我會找不到目標。

### 未驗清單（每項標明驗不了的原因）

1. **「本卡讓 `aiwf#165` 的 CI 由紅轉綠」——未驗。** 要驗必須把本分支與 `#165` 的分支合起來跑，而我⛔ 無 merge 授權，且卡面明令⛔ 不得拿 `#165` 的分支當基線。我只能給結構性論證（那個 token 已整個從檔案消失）——⛔ **那是論證不是量測**。
2. **required check `tests` 在合併結果上的顏色——未驗。** 我拿到的是 `tests (branch head)`。repo 的 CI 檔逐字說明分支頭那一支「永遠不是 required check」，required 的 `tests` 只由 pull_request 的 merge ref 或 main 產生——而我⛔ 不得開 PR。⇒ **「分支頭綠」不等於「合併結果綠」**。
3. **「同族只有這三處」——未驗且刻意不驗。** 卡面明令⛔ 不做窮舉掃描。我只回報為定位 canonical 而必須跑的那一次 grep 順帶命中的 `card.py::amend_brief`。⇒ ⛔ 不得把本報告讀成「同族已盤點完」。
4. **新錨點在「符號被改名／搬檔」下的存活——未驗，且今日無守衛。** 我驗到的是「插刪行不再讓它失效」；「改名會讓它失效」這條**沒有任何機械檢查擋得住**。⇒ 這是把靜默腐爛換成改名時腐爛，⛔ 不是解決。
5. **本機 pytest 63s vs 253s 的差異原因——未驗。** 我沒有可區分機器負載與測試自身行為的儀器，且與本卡改動無關聯證據。
6. **A2 那句活體實測的跨時效性——未驗。** 它量的是 2026-08-28 的 Project #4 首頁 50 筆；`gh` 換版本或看板改欄位後可能不同。docstring 內已標日期與母體。


## Comment 5449890586 · 2026-08-28T07:48:43Z

<!-- wf-review-event:v1 card_id=DOC-CITATION-POINTS-ELSEWHERE1 source_sha=79b1418ad552b067e5c520d6cb0d9a63dfdf4311 attempt_id=DOC-CITATION-POINTS-ELSEWHERE1-e0-79b1418ad552b067e5c520d6cb0d9a63dfdf4311 -->
## 查核裁決：APPROVE

- 卡：`DOC-CITATION-POINTS-ELSEWHERE1`　attempt_id：`DOC-CITATION-POINTS-ELSEWHERE1-e0-79b1418ad552b067e5c520d6cb0d9a63dfdf4311`
- 查核者：Claude Opus 5@Claude Code (Reviewer)　escalation_epoch：0
- source_sha：`79b1418ad552b067e5c520d6cb0d9a63dfdf4311`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-28T15:48:39+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git status --porcelain（唯讀進駐 .worktrees/citation-anchor）`
  - 79b1418ad552b067e5c520d6cb0d9a63dfdf4311；status 空。查核結束後複核仍同 ⇒ source branch 一個位元未動
- `git merge-base origin/main HEAD；git diff --stat；git log --oneline base..HEAD`
  - 54d23e87873e1239a8bff4cbbb2af0c7c5c805fe；brief.py 9 +++++++--／registry.py 7 +++++++／snapshot_population.py 2 +-，3 files changed, 15 insertions(+), 3 deletions(-)；單一 commit 79b1418
- `python3 逐字比對 base 與 head 的 snapshot_population.py 第 5 行`
  - 尾句「——一律走 wf_cli.project.list_items，使盤點與守衛同源。」兩邊皆在且未被換行切開；head 第 5 行含阿拉伯數字 = False；其他行完全相同 = True；行數 221 = 221
- `git ls-files 找 project.py；grep -n 'def list_items'；ast.get_docstring`
  - project.py 唯一（cli/src/wf_cli/project.py）；def list_items 全 repo 唯一 @ 506；其 docstring 逐字承載病因「後者對中文欄位名稱的 JSON key 有編碼錯誤」⇒ 新錨點解析得到目標
- `grep -rn --include=*.py 'def fetch_project_rows' . ；grep -rn 'fetch_project_rows' .`
  - def 版 rc=1、0 命中；字樣唯一命中 cli/tests/test_registry.py:778 的測試名，該測試實際呼叫 fetch_project_ownership_rows（同檔 817 行）⇒ PM 卡面錯誤 1 成立
- `sed -n '1050,1135p' cli/src/wf_cli/registry.py`
  - _run_gh_graphql 走 subprocess.run(['gh','api','graphql','--input','-']) → json.loads；_PROJECT_ITEMS_GQL 含 field{... on ProjectV2FieldCommon{name}}；fetch_project_ownership_rows 以 fields[name]=fv['text'] 在 Python 端組鍵 ⇒ 補的敘述與實際路徑一致
- `自寫唯讀腳本，用 registry 自己的 _PROJECT_ITEMS_GQL + _run_gh_graphql 讀 Project #4 首頁`
  - first-page nodes 50；distinct field names 11 個含 卡ID；U+FFFD present False ⇒ 獨立重現執行者的活體實測
- `grep -c brief cli/src/wf_cli/validation.py；grep -ci 'brief|簡介' 同檔；grep -A3 --brief open_cmd.py amend_cmd.py`
  - 兩個 grep 皆 0（rc=1）；open_cmd.py:86-87 與 amend_cmd.py:377-378 皆 default=None ⇒ A3 的兩個碼事實成立
- `sed -n '755,800p' AI_WORKFLOW.md（讀 §6.3 全文核對轉述忠實度）`
  - §6.3 標題「### 6.3 卡片簡介（WF-STAGE-STATE-TWO-AXIS1）」@757；本文逐字含「--brief 是可選旗標」與「validation.py 完全不驗簡介」⇒ 轉述忠實。同段亦逐字寫承接者含「新卡的必填時點」⇒ 即 finding R1-03 的反例來源
- `grep -n re.compile scripts/qualified_pointer_scan.py scripts/canonical_citation_scan.py`
  - _POINTER 與 _QUALIFIED_REF 兩條都硬性要求 :\d+ ⇒ 全 repo 無守衛認得 檔::符號，執行者的自我限縮屬實。探針：project.py::list_items 0 命中、project.py:506 命中
- `grep -rInoE '檔::符號 形式' . | wc -l；grep -rn --include=*.py '\blist_items\b' . | wc -l`
  - 檔::符號 214 處分布 18 個檔 ⇒ 是 repo 既有形式；list_items 154 處引用散在 25 個檔 ⇒ 改名會斷所有呼叫端（吵，非靜默）
- `自寫 rev_a4.py：載入掃描器取 find_pointers 套在 diff 增刪行 + 自設變異（注入被移除的真實 token）`
  - added 15 行 → 0 命中；removed 3 行 → 1 命中 project.py:377；變異（真實 token 注入 15 條新增行）→ 15/15 命中 ⇒ A4 通過且 0 命中非零資訊。⚠️ 執行者原本用 pointer_token() 合成，鑑別力較弱；其刪除行那 1 筆真實陽性對照才是強的，兩者合起來成立
- `自寫 rev_a5.py：剝 docstring 後 ast.dump 比對 + 雙向變異 + hunk 落點檢查`
  - 三檔 same=True；注入 return 值改動 → same=False（有鑑別力）；只改 docstring → same=True（不誤報）；新增行 brief.py 170..176／registry.py 1061..1067／snapshot_population.py 5..5 全落在 docstring 節點範圍內
- `qualified_pointer_scan.py 兩個 SHA 各一次（merge-base 另開 detached worktree，跑完 remove --force rc=0）`
  - merge-base rc=0 宇宙 81 可強制 79 紅 0；交付 rc=0 宇宙 80 可強制 78 紅 0 ⇒ PM 卡面錯誤 2 成立：main 基線紅本來就是 0，非 1→0
- `qualified_pointer_scan.py --all 兩個 SHA，grep snapshot_population`
  - base 逐字「snapshot_population.py 第 5 行: [ok] project.py:377 → cli/src/wf_cli/project.py」；head grep rc=1 不存在 ⇒ 宇宙 -1 來源確認，且 base 上裁決是 [ok]（掃描器從未抓到它）
- `sed -n '377p' cli/src/wf_cli/project.py @ 54d23e87；grep -n 編碼錯誤 同檔`
  - 377 行 = args += ["--text", str(value)]；病因句在 510 行 ⇒ 卡面「從出生就錯 132 行」前提成立
- `pytest -q（全套）兩個 SHA 各一次，rc 分開取不接管線`
  - @79b1418a rc=0 1479 passed, 1 skipped in 249.71s；@54d23e87 rc=0 1479 passed, 1 skipped in 172.90s ⇒ 1479 = 1479 未退化
- `A6 三條測試兩個 SHA 各一次；uv lock --check；replay；ccs；ctr --check（各自跑、rc 分開取）`
  - 三條測試兩邊皆 rc=0『3 passed, 34 deselected』；其餘四項 rc 全 0，114/114 通過、掃描 155 命中 0、59 個缺口全部有登記處置
- `git interpret-trailers --parse；尾段 cat -e`
  - rc=0，四行齊全；cat -e 顯示四行連續、無空行斷開、為最後一段
- `gh run list --commit 79b1418ad552b067e5c520d6cb0d9a63dfdf4311`
  - databaseId 33148723656、headSha 逐字相符、event push、conclusion success（核的是 headSha 不是最近一筆）。CI 檔逐字規定分支頭那支永遠叫 tests (branch head)，執行者標為參考而非 required check 是對的
- `grep -rn 今天沒有任何卡符合這一條 .；gh issue list --search`
  - AI_WORKFLOW.md:773（更正段落自身）與 cli/src/wf_cli/card.py:1622 ⇒ 與 PM 宣稱一致；#167 DOC-CANON-QUOTE-CARD-PY1 已 OPEN（O-1 已有承接者）；fetch_project_rows 只回 #166 本身（O-2 無承接者）

### findings（4，其中 blocking 0）

- **DOC-CITATION-POINTS-ELSEWHERE1-R1-01**　severity=minor　blocking=false　class=authoritative-artifact　attribution=planner　root_cause_id=`card-face-names-a-symbol-that-does-not-exist`
  - evidence：grep -rn --include='*.py' 'def fetch_project_rows' . → rc=1、0 命中；字樣唯一命中 cli/tests/test_registry.py:778 的測試名，該測試實際呼叫 fetch_project_ownership_rows（同檔 817 行）。真符號是 _run_gh_graphql（cli/src/wf_cli/registry.py:1056）。查核報告全文見 https://github.com/ruan6047/ai-workflow/issues/166
  - disposition：未影響交付：卡面同時給了逐字 docstring 內容，執行者以該冗餘識別子定位到唯一正確符號並逐字報出衝突，處置正確、無須返工。記錄用途：卡面逐字指名符號時，規劃者須自行以 grep 驗證該符號存在；本次能救回只因卡面有冗餘識別子，不是因為錯得無害。根因（過期測試名）見範圍外項 O-2。
- **DOC-CITATION-POINTS-ELSEWHERE1-R1-02**　severity=info　blocking=false　class=authoritative-artifact　attribution=planner　root_cause_id=`acceptance-expectation-measured-on-wrong-baseline`
  - evidence：V3 括號逐字「預期紅由 1 降為 0」。查核者在 merge-base 54d23e87 自建 detached worktree 實跑 qualified_pointer_scan.py：rc=0、宇宙 81、可強制 79、紅 0。實際為宇宙 81→80、紅 0→0。那筆紅只存在於 aiwf#165 的分支。
  - disposition：未影響交付：A6 的本文已寫對（「須在 main 上先確認它們今天是綠的、再確認改動後仍綠」），錯的只有 V3 的括號；執行者量到不符後逐字報出未粉飾。記錄用途：驗證條的預期值必須標明量在哪個基線，否則會把另一個分支的觀察寫成本卡基線的預期。
- **DOC-CITATION-POINTS-ELSEWHERE1-R1-03**　severity=minor　blocking=false　class=implementation　attribution=executor　root_cause_id=`incomplete-restaleness-condition-list`
  - evidence：V1(3) 逐字宣稱「--brief 變必填或 validation.py 開始驗簡介（⚠️ 但那同時也會讓 fail-open 這條路本身該被重新檢討，⇒ 失效方向是連函式行為一起要改，不是靜默指錯）」。反例落在該宣稱自己的母體內：AI_WORKFLOW.md §6.3（查核者讀 755-800 行）逐字寫承接者為「既有卡的補寫與新卡的必填時點」。若 validation.py 之後只對新卡加簡介檢查，docstring 的「validation.py 也完全不驗簡介」即為假，而 try_parse_block 對既有卡的 fail-open 行為完全不需要改——就是靜默指錯，且該路徑被 canonical 自己列為 roadmap。
  - disposition：非阻擋、不要求返工：docstring 今天的兩個碼事實仍為真（查核者已複驗 default=None ×2、grep 0），核心痛點已消。要求記入下一次同族卡的參考：撰寫「什麼會讓它再變假」時，須先讀來源自己宣告的後續工作，那裡通常就寫著最可能的失效路徑。
- **DOC-CITATION-POINTS-ELSEWHERE1-R1-04**　severity=info　blocking=false　class=implementation　attribution=executor　root_cause_id=`incomplete-restaleness-condition-list`
  - evidence：V1(2) 列的三條失效條件全在本 repo 內（_PROJECT_ITEMS_GQL 不再要 field { name }／取列邏輯搬離 fetch_project_ownership_rows／本函式改呼叫 gh project item-list）。缺「gh 修掉 item-list 的 key 編碼 bug」這條：屆時「刻意不用」的前提與新段落的「壞掉的只有那一步」同時失效，而 docstring 內無任何 gh 版本錨（需求方裁定留言的 gh 2.92.0 未寫進碼）。未驗清單 #6 只把版本框在正面實測的時效上，未覆蓋反面前提。
  - disposition：非阻擋。若 PM 認為值得，可在後續卡把 gh 版本寫進該 docstring（形式比照執行者已採用的「日期＋母體＋量法」）。本卡射程僅要求補「改用什麼」，執行者已達成。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: DOC-CITATION-POINTS-ELSEWHERE1-e0-79b1418ad552b067e5c520d6cb0d9a63dfdf4311
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待指派
findings:
  - finding_id: DOC-CITATION-POINTS-ELSEWHERE1-R1-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: authoritative-artifact
    attribution: planner
    root_cause_id: card-face-names-a-symbol-that-does-not-exist
    counting_eligible: false
  - finding_id: DOC-CITATION-POINTS-ELSEWHERE1-R1-02
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: authoritative-artifact
    attribution: planner
    root_cause_id: acceptance-expectation-measured-on-wrong-baseline
    counting_eligible: false
  - finding_id: DOC-CITATION-POINTS-ELSEWHERE1-R1-03
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: implementation
    attribution: executor
    root_cause_id: incomplete-restaleness-condition-list
    counting_eligible: false
  - finding_id: DOC-CITATION-POINTS-ELSEWHERE1-R1-04
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: implementation
    attribution: executor
    root_cause_id: incomplete-restaleness-condition-list
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。
