# #165 DOC-STALE-DEGREE-WORDS1 canonical 與 project.py 四處宣稱今天為假，其中兩處是改記量法後殘留的定性程度詞
- state: closed  created: 2026-08-27T22:14:12Z  closed: 2026-08-29T21:25:12Z
- url: https://github.com/ruan6047/ai-workflow/issues/165
- comments: 7

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；四處逐字替換本身機械，但替換文必須選一種不會腐爛的寫法（釘死探針／不變量／artifact+sha256／只記量法），選錯就是第三次重犯同一形狀；且須自己重跑量測而非抄卡面數字。）　查核：待指派（建議 主力型；查核要判的是新寫法會不會再腐爛——即對每一處問「什麼時候這句話會再變假」，而不是只驗它今天為真。⛔ 非紅線（純文件與註解、零行為改動），毋須跨家族。）
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：目標 2 可稽核：權威文件上讀到的宣稱，必須是今天為真且能被重新量測的，而不是某一刻的快照被當成常態。

## 簡介
<!-- card-brief:begin -->
把 AI_WORKFLOW.md 與 cli/src/wf_cli/project.py 裡四處今天為假的宣稱改成不會腐爛的寫法。適用時機：要引用 §0.1 執行者狀態表的 5c 列、§6.3 的簡介覆蓋敘述、或 project.py 階段欄註解時。⛔ 非射程：不蓋偵測機制；⛔ 不碰兩軸語彙定義或 S2／S3 實作；⛔ 不回填任何卡的簡介。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：**痛點**：權威文件與寫入端的碼裡有四處宣稱今天為假，而它們正是別人拿來判斷「S3 做了沒、階段欄能不能用、簡介要不要補」的依據——PM 本人 2026-08-28 就因為讀了其中兩處而向需求方報出錯誤現況。逐處（量在 ai-workflow main 54d23e87873e1239a8bff4cbbb2af0c7c5c805fe）：(1) cli/src/wf_cli/project.py 階段欄註解逐字「本欄位建立後暫時無人寫入」——而 open_cmd.py:332 無條件寫 values["階段"]="需求"、handoff_cmd.py 依 STAGE_PHASE 寫六鍵，看板 206 張裡 19 張該欄有值；(2) 同註解逐字「切換那一刻三支腳本會停」——實測只有一支：workflow_ledger.py --check 回 rc=1 並印「docs/TASKS.md 已於 2026-08-04 cutover 封存唯讀，本腳本已停用」，state_plane_migrate.py 讀的是 git show origin/main:docs/TASKS.md 這個凍結檔而非看板，只有 roadmap_lines.py 真的讀活看板；(3) AI_WORKFLOW.md §0.1 執行者狀態表 5c 列逐字「條文寫了而多數卡沒照，⛔ 含本卡自己」；(4) AI_WORKFLOW.md §6.3 末段逐字「絕大多數卡沒有簡介區塊」——(3)(4) 皆已被 WF-CARD-BRIEF-BACKFILL1 的回填推翻：以該格自己指定的量法（wf_cli.brief.parse_block 對 list_items 逐張試解析）實測為 204/206 有簡介，無簡介者僅 WF-REVIEW-EVENT-MARKER-CONTRACT1 與 WF-RESOURCE-HEADING-SUFFIX1-PROBE-ASSIGN1 兩張。⭐ (3)(4) 是 DOC-CANON-01-ENFORCER-STALE1（aiwf#150，已結案）「改記量法」那次修法留下的殘餘：數字換成了量法，而「多數」「絕大多數」這兩個定性程度詞本身也是數字，一樣會腐爛。⛔ 非射程：不處理「這些宣稱為什麼會腐爛」的通則（那是 WF-CANONICAL-SELF-STALENESS1 的射程，已上線）；⛔ 不改 §0.1 的兩軸語彙定義；⛔ 不動 S2／S3 的任何實作。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:AI_WORKFLOW.md",
    "file:cli/src/wf_cli/project.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] A1 cli/src/wf_cli/project.py 階段欄註解逐字「⇒ 本欄位建立後暫時無人寫入，交付狀態仍承載階段與狀態兩者。」為假，須改。⚠️ ⛔ 不得只換成新的當日數字——那會在同一週再度變假。反證（開卡時實測 @ 54d23e87）：open_cmd.py 無條件寫 values["階段"]="需求"；handoff_cmd.py 依 STAGE_PHASE 寫六鍵。什麼會推翻本條：交付後該句仍以「今天有幾張卡有值」這種會漂移的量作為主張。
- [ ] A2 同註解逐字「roadmap_lines.gate_of 對未知狀態 fail closed，切換那一刻三支腳本會停。」為假，須改。實測（cpbl main 3b470d70）：workflow_ledger.py --check 回 rc=1 並印「docs/TASKS.md 已於 2026-08-04 cutover 封存唯讀，本腳本已停用」；state_plane_migrate.py 讀 git show origin/main:docs/TASKS.md 這個凍結檔而非看板；只有 roadmap_lines.py 讀活看板。⇒ 會停的是一支不是三支。⚠️ 同句的「cpbl 有六個檔綁狀態語彙」已由 DOC-CANON-01-ENFORCER-STALE1（aiwf#150）裁為非射程（「綁」未定義），⛔ 本卡不處理該半句，但若改寫時順手動到它須逐字說明。
- [ ] A3 AI_WORKFLOW.md §0.1 執行者狀態表 5c 列逐字「條文寫了而多數卡沒照，⛔ 含本卡自己」為假，須改。實測：以該格自己指定的量法（wf_cli.brief.parse_block 對 list_items 逐張試解析，@ 54d23e87 與看板 206 items）得 204/206 有簡介，無簡介者僅 WF-REVIEW-EVENT-MARKER-CONTRACT1 與 WF-RESOURCE-HEADING-SUFFIX1-PROBE-ASSIGN1。⚠️ 執行者須自己重跑該量法，⛔ 不得抄本卡面的 204/206——那是開卡當日的值。
- [ ] A4 AI_WORKFLOW.md §6.3 末段逐字「且 validation.py 完全不驗簡介 ⇒ 絕大多數卡沒有簡介區塊。」的後半為假，須改。⚠️ 前半（validation.py 不驗簡介）今日仍為真，⛔ 不得一併刪掉。⭐ 本條與 A3 是同一個病灶的兩個居所：aiwf#150 的「改記量法」修法把數字換成了量法，而「多數」「絕大多數」這兩個定性程度詞本身也是數字，一樣會腐爛。
- [ ] A5 ⭐ 四處的新寫法各須說明「什麼時候這句話會再變假」，並指出它屬於 canonical 已有的哪一種不腐爛形式。⛔ 說不出再變假條件的改寫，等於把同一個病灶挪個位置。⚠️ 這是本卡唯一有價值的部分——只把今天的假話改成今天的真話是零資訊。⭐ ⚠️ 2026-08-29 需求方裁定修正（升級裁定 ②，issuecomment-5461290769；attribution: planner）：選「不變量」形式時，該不變量本身須先以**一次實跑證明為真**並貼出輸出；跑不出來就⛔ 不得選它，改用「只記量法」並逐字標明它得到的是**下界**。⛔ 未經實跑的不變量宣稱比原本的假話更糟——它看起來像保證。依據：R2-01／R2-02／R3-01 同一 root_cause `falsifier-written-as-open-instance-list` 連三輪，R3 宣稱 set_field_value 是欄位寫入唯一原語，實測 project.py 另有 update_item_field_value 且有 6 個呼叫點不經它。
- [ ] A6 ⛔ 零行為改動：只改 project.py 的註解與 AI_WORKFLOW.md 的散文。什麼會推翻它：git diff 出現宣告以外的檔，或 cli/src/ 下有任何一行非註解的改動。唯一宣告資源是 file:AI_WORKFLOW.md 與 file:cli/src/wf_cli/project.py。
- [ ] A7 ⛔ 本卡不得引入任何新的 檔:行號 形式指標。依據：DOC-STALE-FILE-LINE-POINTERS1（aiwf#159）的實例——主旨寫「移除行號引用」的 commit 自己留下 2 個新行號、26 小時內失效。⚠️⚠️ 2026-08-28 需求方裁定修正本條（issuecomment-5449007200；attribution: planner）：原文逐字「交付後須以 scripts/qualified_pointer_scan.py 實跑證明紅數為 0」把兩件事寫成一條——紅數 0 是整個 repo 的狀態、⛔ 不是本卡能控制的量。實證：本卡在 project.py 加 18 行註解，就把別人寫在 scripts/brief_backfill/snapshot_population.py 第 5 行的 project.py:377 推到空行上而轉紅，而該指標從出生就錯 130 幾行（它宣稱指的「中文欄位 key 編碼壞」在基線是 project.py:509-510），且 aiwf#146 掃描器 docstring 逐字「⛔ 不驗指得對不對。目標行非空即算過」「紅數是下界」⇒ 它對兩道守衛都是隱形的。⇒ 判準改為兩條：(a) 本卡自己寫的文字裡零個新的 檔:行號 指標；(b) 掃描若因本卡浮出既有的紅，須逐筆具名登記（來源檔、指標逐字、為什麼它在基線上是綠的）並交 PM 開卡承接。⛔ 不得在本卡內修那些紅（射程外的檔）、⛔ 不得縮短或改寫註解讓行號落回非空行——那是看著答案調判準，本 repo 已具名禁止。什麼會推翻它：交付文字裡出現新的 檔:行號，或浮出的紅沒有逐筆具名登記。

## 驗證

- [ ] V1 四處逐處貼出「改前逐字 → 改後逐字」，並各附一句「什麼時候這句話會再變假」。⛔ 不得摘要合併成一段。⭐ 以及該再變假條件的**一次實跑輸出**（指令＋rc＋結果）。⛔ 不接管線——`| tail` 會把 `$?` 換成 tail 的 rc。⚠️ 2026-08-29 隨 A5 一併修正（同一裁定）。
- [ ] V2 A3/A4 的簡介覆蓋數字須由執行者自己重跑（wf_cli.brief.parse_block 對 list_items 逐張試解析），貼出母體數、有簡介數、無簡介者的卡 ID 清單，並註明量在哪顆 SHA 與哪個時點。⛔ 不得引用本卡面的 204/206。
- [ ] V3 A2 的「只有一支會停」須由執行者自己重跑證實，⛔ 不得引用本卡面：在 cpbl 上分別跑 workflow_ledger.py --check 與 state_plane_migrate.py --dry-run，逐項貼 rc 與輸出首行；並貼出 state_plane_migrate.py 讀取來源的碼段（DEFAULT_BASELINE_REF 與 git show 那一行）。⛔ 不接管線——| tail 會把 $? 換成 tail 的 rc。
- [ ] V4 回歸不退化，量在交付 SHA，rc 分開跑並逐項貼，⛔ 全部不接管線：uv run --frozen --project cli pytest -q 的 rc=0 且通過數 >= merge-base 的通過數（merge-base 的數字也要自己跑一次）；uv lock --check、scripts/replay_escalation_rules.py、scripts/canonical_citation_scan.py、scripts/contract_tool_reconcile.py --check 四項 rc 全 0。⚠️⚠️ 2026-08-28 更正（查核 finding R2-05，attribution: planner）：原文另要求「scripts/qualified_pointer_scan.py」rc=0，⛔ **那是整個 repo 的狀態、不是本卡能控制的量**——與同日已被需求方裁定修正的原 A7（issuecomment-5449007200）完全同形，PM 當時只修了 A7、⛔ 漏了本條。⇒ 掃描器的判準改由 A7(a)(b) 承擔：(a) 本卡自己寫的文字裡零個新 檔:行號；(b) 掃描若因本卡浮出既有的紅，逐筆具名登記並交 PM 開卡承接。⛔ 本條不再要求 repo 全域紅數 0。⚠️ 本輪 V4 之所以恰好達成，是因為射程外那筆紅已被 aiwf#166 修掉，⛔ 不是原寫法變對了。⚠️ 腳本以 CI 釘死的 python 3.12 跑。
- [ ] V5 ⛔ 射程誠實：交付須逐字寫出本卡不涵蓋什麼——⛔ 不蓋任何偵測機制、⛔ 不處理「cpbl 六個檔綁狀態語彙」那半句（aiwf#150 已裁非射程）、⛔ 不碰 §0.1 的兩軸語彙定義、⛔ 不回填任何卡的簡介、⛔ 不動 S2／S3 的實作。什麼會推翻它：交付出現「canonical 已無過期宣稱」這類未收窄的宣稱。

## Log

- 2026-08-28T06:14:10+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-28T12:48:04+08:00 amend by wf-cli（op c5eeff61）→ 驗收條件：原值「[ ] TODO：填入可獨立驗證的條件」→ 新值「A1 cli/src/wf_cli/project.py 階段欄註解逐字「⇒ 本欄位建立後暫時無人寫入，交付狀態仍承載階段與狀態兩者。」為假，須改。⚠️ ⛔ 不得只換成新的當日數字——那會在同一週再度變假。反證（開卡時實測 @ 54d23e87）：open_cmd.py 無條件寫 values["階段"]="需求"；handoff_cmd.py 依 STAGE_PHASE 寫六鍵。什麼會推翻本條：交付後該句仍以「今天有幾張卡有值」這種會漂移的量作為主張。；A2 同註解逐字「roadmap_lines.gate_of 對未知狀態 fail closed，切換那一刻三支腳本會停。」為假，須改。實測（cpbl main 3b470d70）：workflow_ledger.py --check 回 rc=1 並印「docs/TASKS.md 已於 2026-08-04 cutover 封存唯讀，本腳本已停用」；state_plane_migrate.py 讀 git show origin/main:docs/TASKS.md 這個凍結檔而非看板；只有 roadmap_lines.py 讀活看板。⇒ 會停的是一支不是三支。⚠️ 同句的「cpbl 有六個檔綁狀態語彙」已由 DOC-CANON-01-ENFORCER-STALE1（aiwf#150）裁為非射程（「綁」未定義），⛔ 本卡不處理該半句，但若改寫時順手動到它須逐字說明。；A3 AI_WORKFLOW.md §0.1 執行者狀態表 5c 列逐字「條文寫了而多數卡沒照，⛔ 含本卡自己」為假，須改。實測：以該格自己指定的量法（wf_cli.brief.parse_block 對 list_items 逐張試解析，@ 54d23e87 與看板 206 items）得 204/206 有簡介，無簡介者僅 WF-REVIEW-EVENT-MARKER-CONTRACT1 與 WF-RESOURCE-HEADING-SUFFIX1-PROBE-ASSIGN1。⚠️ 執行者須自己重跑該量法，⛔ 不得抄本卡面的 204/206——那是開卡當日的值。；A4 AI_WORKFLOW.md §6.3 末段逐字「且 validation.py 完全不驗簡介 ⇒ 絕大多數卡沒有簡介區塊。」的後半為假，須改。⚠️ 前半（validation.py 不驗簡介）今日仍為真，⛔ 不得一併刪掉。⭐ 本條與 A3 是同一個病灶的兩個居所：aiwf#150 的「改記量法」修法把數字換成了量法，而「多數」「絕大多數」這兩個定性程度詞本身也是數字，一樣會腐爛。；A5 ⭐ 四處的新寫法各須說明「什麼時候這句話會再變假」，並指出它屬於 canonical 已有的哪一種不腐爛形式。⛔ 說不出再變假條件的改寫，等於把同一個病灶挪個位置。⚠️ 這是本卡唯一有價值的部分——只把今天的假話改成今天的真話是零資訊。；A6 ⛔ 零行為改動：只改 project.py 的註解與 AI_WORKFLOW.md 的散文。什麼會推翻它：git diff 出現宣告以外的檔，或 cli/src/ 下有任何一行非註解的改動。唯一宣告資源是 file:AI_WORKFLOW.md 與 file:cli/src/wf_cli/project.py。；A7 ⛔ 不得引入任何新的 檔:行號 形式指標。依據：DOC-STALE-FILE-LINE-POINTERS1（aiwf#159）的實例——主旨寫「移除行號引用」的 commit 自己留下 2 個新行號、26 小時內失效。交付後須以 scripts/qualified_pointer_scan.py 實跑證明紅數為 0。」（⚠️ 全文：totalCount=0（首寫，平台無前一版））；理由 填實驗收與驗證（open 時為 TODO 佔位符，⛔ 不得帶佔位符送審）。⭐ A5 是本卡唯一有價值的部分：只把今天的假話改成今天的真話是零資訊，新寫法必須說得出再變假的條件。A3/A4 標明數字須執行者自己重跑，⛔ 不得抄卡面——那正是本卡要修的病。A7 釘死 aiwf#159 的教訓（修行號引用的 commit 自己留下新行號）。。
- 2026-08-28T12:48:04+08:00 amend by wf-cli（op c5eeff61）→ 驗證：原值「[ ] TODO：填入驗證指令與證據要求」→ 新值「V1 四處逐處貼出「改前逐字 → 改後逐字」，並各附一句「什麼時候這句話會再變假」。⛔ 不得摘要合併成一段。；V2 A3/A4 的簡介覆蓋數字須由執行者自己重跑（wf_cli.brief.parse_block 對 list_items 逐張試解析），貼出母體數、有簡介數、無簡介者的卡 ID 清單，並註明量在哪顆 SHA 與哪個時點。⛔ 不得引用本卡面的 204/206。；V3 A2 的「只有一支會停」須由執行者自己重跑證實，⛔ 不得引用本卡面：在 cpbl 上分別跑 workflow_ledger.py --check 與 state_plane_migrate.py --dry-run，逐項貼 rc 與輸出首行；並貼出 state_plane_migrate.py 讀取來源的碼段（DEFAULT_BASELINE_REF 與 git show 那一行）。⛔ 不接管線——| tail 會把 $? 換成 tail 的 rc。；V4 回歸不退化，量在交付 SHA，rc 分開跑並逐項貼，⛔ 全部不接管線：uv run --frozen --project cli pytest -q 的 rc=0 且通過數 >= merge-base 的通過數（merge-base 的數字也要自己跑一次）；uv lock --check、scripts/replay_escalation_rules.py、scripts/canonical_citation_scan.py、scripts/contract_tool_reconcile.py --check、scripts/qualified_pointer_scan.py 五項 rc 全 0。；V5 ⛔ 射程誠實：交付須逐字寫出本卡不涵蓋什麼——⛔ 不蓋任何偵測機制、⛔ 不處理「cpbl 六個檔綁狀態語彙」那半句（aiwf#150 已裁非射程）、⛔ 不碰 §0.1 的兩軸語彙定義、⛔ 不回填任何卡的簡介、⛔ 不動 S2／S3 的實作。什麼會推翻它：交付出現「canonical 已無過期宣稱」這類未收窄的宣稱。」（⚠️ 全文：totalCount=0（首寫，平台無前一版））；理由 填實驗收與驗證（open 時為 TODO 佔位符，⛔ 不得帶佔位符送審）。⭐ A5 是本卡唯一有價值的部分：只把今天的假話改成今天的真話是零資訊，新寫法必須說得出再變假的條件。A3/A4 標明數字須執行者自己重跑，⛔ 不得抄卡面——那正是本卡要修的病。A7 釘死 aiwf#159 的教訓（修行號引用的 commit 自己留下新行號）。。
- 2026-08-28T12:49:34+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree ai/opus-5/DOC-STALE-DEGREE-WORDS1 @ /Users/ruanruan/Dev/ai-workflow/.worktrees/stale-degree-words；交付狀態 🔨執行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-28T12:50:57+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 1；SHA 54d23e87873e1239a8bff4cbbb2af0c7c5c805fe；階段 需求；踩坑回應 8 族（已檢查 3／不適用 1／發現 4）；證據 首次派工。分支 ai/opus-5/DOC-STALE-DEGREE-WORDS1 @ /Users/ruanruan/Dev/ai-workflow/.worktrees/stale-degree-words，基線 54d23e87。四處為假：project.py 階段欄註解兩句（暫時無人寫入／三支腳本會停）＋ AI_WORKFLOW.md 兩處定性程度詞（§0.1 5c 的多數卡沒照／§6.3 的絕大多數卡沒有簡介區塊）。⭐ A5 是本卡唯一有價值的部分：新寫法須說得出再變假的條件並指出屬 canonical 已有的哪一種不腐爛形式。⛔ A6 零行為改動、⛔ A7 不得引入新的檔:行號指標（aiwf#159 的教訓：修行號的 commit 自己留下新行號、26 小時失效）。A3/A4 的數字執行者須自己重跑，⛔ 不得抄卡面。。
- 2026-08-28T13:57:53+08:00 amend by wf-cli（op bad01367）→ 驗收條件：原值指紋 sha256:20d33c9cec06d972e47a52c8668debd7d17daf0a3549eacefa8e1ed81510cbdd (3054 bytes) → 新值指紋 sha256:613f5f65e0ff17a19749baf4cd6e6ad5d543298b83dde8ab14756880df7bb5db (4229 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方 2026-08-28 裁定（issuecomment-5449007200，採乙′案）修正 A7，attribution: planner。原 A7 把「不得引入新的 檔:行號 指標」（本卡該負責）與「掃描紅數 0」（整個 repo 的狀態、本卡控制不了）寫成一條，導致執行者被一個寫壞的驗收條擋住：本卡在 project.py 加 18 行註解就把別人寫的 project.py:377 推到空行而轉紅，而該指標從出生就錯 130 幾行、對 aiwf#159 與 aiwf#146 兩道守衛都是隱形的。⛔ 不擴充資源宣告（依需求方既有規矩：問題卡自己修、只改符合本卡核心痛點的東西）。A1–A6 未變。。
- 2026-08-28T16:35:06+08:00 handoff by wf-cli → owner 待指派；iteration 1；SHA 54463adb9fce24776d1a939bf686806844e507fa；階段 執行；踩坑回應 13 族（已檢查 5／不適用 0／發現 8）；證據 送審（解除阻塞後）。分支 ai/opus-5/DOC-STALE-DEGREE-WORDS1 @ 54463adb9fce24776d1a939bf686806844e507fa（已推 origin）；merge-base f0dfcfc688999f75f9cb57d606fd1255f7e4528e。⭐ 本卡原本因射程外的既有壞指標而交付紅（qualified_pointer_scan rc=1 紅 1、pytest 3 failed 1476 passed），依需求方裁定（issuecomment-5449007200，修正 A7 為 (a)(b) 兩條）走登記→開卡承接路徑：aiwf#166 已修掉那筆指標並合併進 main（f0dfcfc6），本卡以 merge（⛔ 非 rebase）接上，受審 SHA a715ae8ef5f55e5453f2e50851182a277aa0d36d 仍在祖先鏈（PM 以 merge-base --is-ancestor 複驗為真）。PM 獨立重跑（⛔ 非轉述）：diff --name-status 相對新 merge-base 恰為 AI_WORKFLOW.md 與 cli/src/wf_cli/project.py 兩個宣告檔；qualified_pointer_scan.py rc=0 宇宙 80 紅 0；cli/tests/test_qualified_pointer_scan.py 37 passed rc=0；全套 pytest rc=0 1479 passed 1 skipped，與 merge-base 的 1479 相同未退化 ⇒ 派工詞點名的三件由紅轉綠全部達成。⭐ 執行者本輪自抓兩件 PM 未提醒的：(1) merge commit 本身受 trailer 守衛管轄（doctor.classify_commit_shape 對 parents>=2 且 combined diff 為空判 merge_clean，required_trailers 回 Reviewed-by），原本零 trailer 屬違規，已依 canonical §6「不適用」形態補為「Reviewed-by: —（基線更新 merge，無查核對象）」並把「這道閘門今天沒有鑑別力」寫進留痕；⛔ 未在 merge_clean 上加 Implemented-by。(2) grep 的 --include=* 被 zsh glob 打掛而 || 印出假「零命中」，改 git grep 後才發現真有一筆命中（docs/WF_EVENT_IDEMPOTENCY1.md 的 project.py:28，經查指得正確且未被本卡擾動）。⚠️ 交查核者複核的未閉環項：(1) canonical §6 第 3 條要求分支更新用 rebase，狹義例外需 (i)(ii) 同時成立；執行者讀為兩者皆不成立，而 PM 在派工中具名判定用 merge（理由：保住受審 SHA 在祖先鏈）。該條逐字為「派工包層的約定：由撰寫派工包者判定並在派工包內具名、由查核者複核，⛔ 不得宣稱它已機械化」⇒ 執行者照辦並把讀法寫進 merge 留痕、⛔ 未自行裁定，請查核者複核。(2) merge_clean 的「不適用」trailer 形態是否正確。(3) 執行者的簡介覆蓋數 206/208 用 live 查詢而非版控快照 artifact，其判斷未經覆核。(4) ⭐ 卡面派工詞逐字指定的那一題仍無答案：新寫法會不會再腐爛——執行者只能證明每處寫下了可 grep 的再變假條件，⛔ 不能證明那些條件充分。⚠️ PM 在本卡另有一處未修的同族錯誤：V4 與原 A7 同病（把 repo 全域 rc=0 寫成本卡判準），PM 只修了 A7、⛔ 未修 V4；本次交付因射程外的紅已被承接卡修掉而 V4 恰好達成，⛔ 但那不代表 V4 的寫法是對的。⚠️ 本次 handoff 被 CLI 連兩次以「已檢查 須整格逐字相等、不許帶說明」拒收共三格；PM 改為裸「已檢查」並把說明留在本欄——⛔ 刻意不升成「發現：」，那會膨脹發現數（aiwf#167 查核 R1-01 正是指出該偏差方向，⭐ 而它假設的 CLI 機制在本次真的發生了）。被裁掉說明的三格：可重現性不足（每個數字附 SHA／時點／指令；cpbl 觀測基線釘成字面 3b470d70；merge-base 通過數以拋棄式 worktree 實跑取得⛔ 非推算）、資源或寫入集宣告（相對新 merge-base 只動兩個宣告檔，⛔ 全程未越界改 snapshot_population.py／brief.py）、留痕失真或遺失（a715ae8 保留在祖先鏈上；上一輪試改第三方檔已還原並逐位元比對，交付 diff 無殘留）。執行者的完整報告、失誤登記（11 筆）與未驗清單（5 項）由 PM 於本次 handoff 後立即代貼於卡上留言並自述轉錄來源。。
- 2026-08-28T17:04:49+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 Claude Opus 5@Claude Code (Reviewer)；core_pain_resolved yes；self_run 18 項；findings 6 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt DOC-STALE-DEGREE-WORDS1-e0-54463adb9fce24776d1a939bf686806844e507fa。
- 2026-08-28T17:06:59+08:00 amend by wf-cli（op cba86c2e）→ 驗證：原值指紋 sha256:d7a96228466ec1cb4e3bcec63619338ae60addb04520a7397bcc71b7000cc781 (1642 bytes) → 新值指紋 sha256:ddac5c4cc000283087eda5caab71cc8914464ddb04a058342c85605c0ad59545 (2336 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 查核 finding R2-05（minor、非阻擋、attribution: planner）：V4 與原 A7 同病——把「scripts/qualified_pointer_scan.py rc=0」這個 repo 全域狀態寫成本卡判準。需求方 2026-08-28 已裁定修正原 A7（issuecomment-5449007200），PM 當時⛔ 漏了 V4。本次同步修正：掃描器判準改由 A7(a)(b) 承擔，V4 只留本卡控制得了的四項。⚠️ 本輪 V4 恰好達成是因為射程外的紅已被 aiwf#166 修掉，⛔ 不是原寫法變對了——該事實逐字寫進條文本身。V1／V2／V3／V5 未變（--verification 是整份取代故全列）。。
- 2026-08-28T17:08:09+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 2；SHA 54463adb9fce24776d1a939bf686806844e507fa；階段 審核；踩坑回應 8 族（已檢查 3／不適用 0／發現 5）；證據 R3 派工。R1 查核 REQUEST_CHANGES（Claude Opus 5@Claude Code (Reviewer)，六筆：1 blocking ＋ 5 非阻擋）。⭐ 唯一必修 R2-01（major、blocking、attribution executor）：§0.1 表 5c 與 §6.3 兩處新寫法共用的再變假條件，其指名令牌在碼庫零命中、且「唯一命中」的宣稱不成立。PM 逐項複驗屬實：git grep 'brief\.parse_block' -- cli/src rc=1 零命中；git grep -- '--brief' cli/src 12 命中橫跨 brief.py／card.py／amend_cmd.py／open_cmd.py／doctor.py 五檔；doctor.py:2012 有 RuleEpoch(rule_id='brief_present', disposition=DISPOSITION_MIGRATE)、判定點在 :2155。⇒ 修法（查核者逐字）：把兩處的再變假條件由「列舉實例」改成「封閉述詞」，並把 doctor.brief_present 補進結構性列舉；⛔ 刪掉「grep 得到唯一命中」那句；⛔ 不要改用「只記量法」（那是 aiwf#150 留下殘餘的那一手）。⭐ 形狀對稱：本卡在修 #150 的「改記量法」留下的定性程度詞，而它自己會留下一個「指名令牌零命中」的證偽條件——同一病灶換一個居所，⛔ 不要變成第三次。非阻擋五筆：R2-02（階段欄 writer 條件同族，建議改封閉述詞）、R2-03（STAGE_PHASE 六鍵複製成第二個居所）、R2-04（PM 的 merge 判定記為具名偏離、⛔ 非例外成立）、R2-05（PM 已同步修正 V4，op cba86c2e——原文與原 A7 同病，⇒ ⚠️ 執行者本輪請以修正後的 V4 為準）、R2-06（206/208 的快照 schema 互斥，PM 將開承接卡）。⛔ 全文與逐字量測見卡上裁決留言。分支 ai/opus-5/DOC-STALE-DEGREE-WORDS1 @ 54463adb，merge-base f0dfcfc6。。
- 2026-08-29T15:14:22+08:00 handoff by wf-cli → owner 查核者（待指派）；iteration 2；SHA cb62b20f03d9b90327aa358d9cfd4b3e81b5532e；階段 執行；踩坑回應 13 族（已檢查 7／不適用 4／發現 2）；證據 R3 送審。基線＝merge-base f0dfcfc688999f75f9cb57d606fd1255f7e4528e（非 origin/main）。diff 恰兩檔：AI_WORKFLOW.md、cli/src/wf_cli/project.py，+44/-6。前一輪 R2 對 54463adb 裁決 REQUEST_CHANGES（6 筆，R2-01 major blocking），core_pain_resolved=yes。⛔ 本次踩坑清冊由 PM 自評，非執行者自評：R3 推送後未在卡上留下執行者交付報告。⛔ PM 未對 cb62b20f 重跑 pytest；上一輪查核在 54463adb 實跑 1479 passed, 1 skipped，與 merge-base 相同。。
- 2026-08-29T15:33:01+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 gpt-5.6-terra@Codex；core_pain_resolved no；self_run 9 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt DOC-STALE-DEGREE-WORDS1-e0-cb62b20f03d9b90327aa358d9cfd4b3e81b5532e。
- 2026-08-29T16:26:13+08:00 handoff by wf-cli → owner 待指派；iteration 2；SHA cb62b20f03d9b90327aa358d9cfd4b3e81b5532e；階段 審核；踩坑回應 8 族（已檢查 4／不適用 2／發現 2）；證據 升級裁定 ②（退回上一階段／規劃）：https://github.com/ruan6047/ai-workflow/issues/165#issuecomment-5461290769 。同一 root_cause falsifier-written-as-open-instance-list 第三輪（R2-01／R2-02／R3-01）⇒ 形狀錯了而非實例沒抓乾淨。R3-01 由 PM 獨立複驗屬實：project.py 有兩個寫入原語，update_item_field_value 有 6 個呼叫點不經 set_field_value。。
- 2026-08-29T16:30:08+08:00 amend by wf-cli（op 89d3c7db）→ 驗收條件：原值指紋 sha256:ad17babfc923fd6463ec4a2fe2bde1458eaa2b39bab69a97bdcd8889ae5404ca (4257 bytes) → 新值指紋 sha256:6c89e7418de31f07d5b818544ac02ca949dea7fcfac9f91a34bb0a24bed862e9 (4879 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 升級裁定 ② 退回規劃重定射程（issuecomment-5461290769）：A5 由「說得出再變假條件」升級為「跑得出」，V1 併同要求貼出實跑輸出。⛔ 其餘 5 條 A 與 4 條 V 逐字不動（整份取代機制所需）。核心痛點⛔ 未動。。
- 2026-08-29T16:30:08+08:00 amend by wf-cli（op 89d3c7db）→ 驗證：原值指紋 sha256:b51a8781bea7c6dc4ee24087b35ec8d71a65ad24f2ce27d5017c8ec7201633e6 (2356 bytes) → 新值指紋 sha256:86e8ad45a365a4b4f77a80d4cd91b5a60aa6f678ad610b4bc0b75ffee14ba359 (2540 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 升級裁定 ② 退回規劃重定射程（issuecomment-5461290769）：A5 由「說得出再變假條件」升級為「跑得出」，V1 併同要求貼出實跑輸出。⛔ 其餘 5 條 A 與 4 條 V 逐字不動（整份取代機制所需）。核心痛點⛔ 未動。。
- 2026-08-29T16:34:31+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 3；SHA cb62b20f03d9b90327aa358d9cfd4b3e81b5532e；階段 規劃；踩坑回應 8 族（已檢查 5／不適用 2／發現 1）；證據 R4 派工。規格已於升級裁定 ② 後修訂（op 89d3c7db）：A5 由「說得出再變假條件」升級為「跑得出」、V1 併同要求貼實跑輸出，其餘 10 條逐字不動、核心痛點未動。分支 ai/opus-5/DOC-STALE-DEGREE-WORDS1 @ HEAD cb62b20f，worktree 乾淨。。
- 2026-08-30T04:59:47+08:00 handoff by wf-cli → owner 查核者（待指派）；iteration 3；SHA 1c3607054aad3a39b8165bdb3f6a89f7f149cdb8；階段 執行；踩坑回應 13 族（已檢查 5／不適用 4／發現 4）；證據 R4 送審。基線＝merge-base f0dfcfc688999f75f9cb57d606fd1255f7e4528e（非 origin/main）。執行者交付報告逐字轉錄見 https://github.com/ruan6047/ai-workflow/issues/165#issuecomment-5464850072 。前一輪 R3 由 gpt-5.6-terra@Codex 裁決 REQUEST_CHANGES、core_pain_resolved=no，R3-01 root_cause falsifier-written-as-open-instance-list 為同族第三輪，需求方升級裁定 ② 退回規劃並修訂 A5／V1。PM 已獨立驗證機械面：worktree 乾淨、f888b0c3 不在分支上、is-ancestor rc=0、diff 恰兩檔 +69/-7、cli/src 非註解新增 0 行、trailer 四行連續。PM 未對交付 SHA 重跑 pytest，執行者報告 1479 passed 1 skipped 與 merge-base 相同。。
- 2026-08-30T05:17:56+08:00 review by wf-cli → APPROVE（✅通過）；查核者 gpt-5.6-terra@Codex；core_pain_resolved yes；self_run 8 項；findings 0 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt DOC-STALE-DEGREE-WORDS1-e0-1c3607054aad3a39b8165bdb3f6a89f7f149cdb8。
- 2026-08-30T05:24:59+08:00 handoff by wf-cli → owner —；iteration 3；SHA 52780f6c1cabe4dee8142e17590b457b01367e22；階段 審核；踩坑回應 8 族（已檢查 6／不適用 1／發現 1）；證據 R4 APPROVE 後合併並收尾。PR https://github.com/ruan6047/ai-workflow/pull/171 squash 合併為 52780f6c1cabe4dee8142e17590b457b01367e22。查核 gpt-5.6-terra@Codex 於 2026-08-30T05:17:56+08:00 APPROVE、core_pain_resolved=yes、findings 0；身分自述 Codex session 01a04f55-fa21-7f31-b536-87c7098e5212，PM 已核對本機 transcript（originator=Codex Desktop、model=gpt-5.6-terra 由 harness 寫入）。CI tests 與 tests (branch head) 皆 pass。被審 SHA 1c360705 為合併前 head 的祖先，且與 main 在兩個宣告檔上 diff 為空。首次 release 因本地 main 落後一個 commit 被 merge_verified_local 守衛以 rc=5 擋下，已 git pull --ff-only 對齊後重跑。；收尾清理：已清除 worktree；本地分支、遠端分支 依授權保留（未刪除）。


## Comment 5449007200 · 2026-08-28T05:57:19Z

## 需求方裁定：修正 A7，⛔ 不擴充資源宣告

**轉錄自述**：本則由 **PM（Claude Opus 5@Claude Code）** 以需求方 token 發文；author 欄恆為 `ruan6047`，⛔ 不代表由需求方撰寫。需求方於對話中的回覆逐字為「**ＯＫ**」，係對 PM 提出甲／乙′兩案後採**乙′**。

### 執行者的升級成立，且被擋住的原因是 PM 寫壞了驗收條

執行者於交付 SHA `a715ae8ef5f55e5453f2e50851182a277aa0d36d` 停下並升級：`scripts/qualified_pointer_scan.py` rc=1、紅 1，唯一那筆紅是

```
scripts/brief_backfill/snapshot_population.py 第 5 行:
  [F3_目標行為空] project.py:377 → cli/src/wf_cli/project.py （指到空行）
```

⛔ **那不是執行者寫的指標**，而修它要動宣告資源以外的第三個檔 ⇒ 與 A6 直接相斥。

PM 複驗（量在 `54d23e87` 與 `a715ae8`）：

- 該指標宣稱指「中文欄位 key 編碼壞」，那句話在基線是 `cli/src/wf_cli/project.py:509-510`、交付後是 `:526`，**從來不在 377**。基線上 377 行是 `args += ["--text", str(value)]`。⇒ **它從出生就錯，錯 130 幾行。**
- `aiwf#159` 沒有漏掉它：`#159` 動的 16 個檔不含 `scripts/brief_backfill/snapshot_population.py`，卡面提及該檔 0 次。原因是 `#159` 的判準逐字是「指向**空行或不存在檔**」，而它當時指的是非空行 ⇒ 不紅。
- `aiwf#146` 的掃描器 docstring 逐字：「**⛔ 不驗指得對不對。** 目標行非空即算過」「任何由本腳本得到的紅數都是**下界**」。

⇒ **一個指錯 130 幾行的指標，對兩道守衛都是隱形的。** 它今天轉紅純粹是因為本卡在該檔前面插了 18 行把它推到空行上——那是運氣，⛔ 不是偵測。

### 裁定

**A7 由 PM 寫壞**（`attribution: planner`）：原文把兩件事寫成一條——「不得引入新的 `檔:行號` 指標」（本卡該負責）與「掃描紅數 0」（整個 repo 的狀態，⛔ 本卡控制不了）。執行者是被錯的驗收條擋住，⛔ 不是做錯事。

⇒ **A7 修正為兩條判準**（見卡面現值）：(a) 本卡自己寫的文字裡零個新的 `檔:行號` 指標；(b) 掃描若因本卡浮出既有的紅，逐筆具名登記並交 PM 開卡承接。

⛔ **不擴充資源宣告**。依據需求方既有規矩逐字：「不要為將以前舊卡的問題找通則 應該是請問題卡修正」與「當然是符合卡片核心痛點的再改」——本卡核心痛點點名的是四處，`snapshot_population.py:5` 是第五處且是別人的檔。

⭐ 且這是同族第三次修實例：`#159` 修 27 個、本筆是第 28 個、執行者另撞見 `cli/src/wf_cli/brief.py` 的 `try_parse_block` docstring 是第 29 個。承接卡的正題**不是再修兩個實例**，是「掃描器只驗得到『指到空行』，指錯但落在非空行的永遠隱形」——`紅數是下界` 這句話今天有了第一個實證。

### 執行者本輪要做的

⛔ 不修那筆紅、⛔ 不縮短註解讓行號落回非空行（看著答案調判準，本 repo 已具名禁止）。依新 A7(b) 把它逐筆具名登記進交付報告即可。⚠️ `brief.py` 的同族漂移同樣只登記、⛔ 不修。


## Comment 5450407007 · 2026-08-28T08:45:21Z

## 執行者交回：交付報告、失誤登記與未驗清單（`DOC-STALE-DEGREE-WORDS1` / #165）

> **轉錄自述**：本則由 **PM（Claude Opus 5@Claude Code）** 以需求方 token 發文，內容為**執行者 `Claude Opus 5@Claude Code` 交回 PM 的報告逐字轉錄**。⛔ PM 未修改任何一個字。author 欄恆為 `ruan6047`（token 持有者），⛔ 不代表本文由需求方撰寫。踩坑清冊 13 族的回應由 PM 依此報告另行撰寫後寫入 handoff 事件，⛔ 非逐字等同本則——**兩份是不同作者的不同文件**。

**交付 SHA `54463adb9fce24776d1a939bf686806844e507fa`**（遠端同 SHA、工作樹乾淨）。**merge-base `f0dfcfc688999f75f9cb57d606fd1255f7e4528e`**（自行 `git merge-base origin/main HEAD` 算得）。**祖先鏈**：`54463ad`（merge）← `f0dfcfc`（#166）＋ `a715ae8`（實作 commit，仍在鏈上，`merge-base --is-ancestor` 實測為真）。相對 merge-base 的檔案集：`AI_WORKFLOW.md`、`cli/src/wf_cli/project.py`。

### ⚠️ 我在本輪自己抓到並修掉的一個違規

merge 之後我沒有直接收工，而是去讀了守衛的碼 —— **原本的 merge commit 零 trailer，那是違規。**

`doctor.classify_commit_shape` 逐字：`parents >= 2` 且 combined diff 為空 → `merge_clean`；`required_trailers("merge_clean")` 回 `(MERGE_TRAILER,)` 即 `("Reviewed-by",)`。實測我的 merge：parents 2 個、`git show --cc` **0 行**、commit 時間 `2026-08-28T16:11:18+08:00` 晚於 `TRAILER_GUARD_EPOCH = "2026-08-13T00:00:00+08:00"` ⇒ **在射程內且缺 `Reviewed-by`**。⭐ 該 docstring 還明文堵掉了我可能拿來自我開脫的路：「**基線更新 merge**：也是 merge commit，同一格處理。本模組**刻意不區分**它與整合 merge」。

已依 canonical §6 的「不適用」形態 amend：`Reviewed-by: —（基線更新 merge，無查核對象）`，並照該條要求把「這道閘門今天沒有鑑別力」寫進留痕。

**⚠️ 一併呈報一個我不代為裁定的點**：canonical §6 第 3 條要求分支更新用 **rebase**，狹義例外需 (i)(ii) **同時成立**。我讀下來**兩者皆不成立**——main 上沒有已合併的碼引用 `a715ae8`；本分支 commit 皆晚於 `TRAILER_GUARD_EPOCH`。但同一條也逐字寫明：「它是**派工包層的約定**：由撰寫派工包者判定並在派工包內具名、由查核者複核，⛔ 不得宣稱它已機械化」。你在派工中已具名判定（「用 merge，⛔ 不要 rebase」＋理由），⇒ 我照辦並把我的讀法寫進 merge commit 留痕，**留給查核者複核，⛔ 不宣稱它已成立**。

### V1 四處逐處（merge 後逐句實測仍在，舊句全數為 0）

六個新句 marker 各 `grep -c` = 1；四句舊假話在兩檔各 `grep -c` = 0。

**① 階段欄註解（A1）** 改後逐字：`#: ⇒ 本欄位有兩個 writer：open_cmd 無條件寫「需求」（不在任何 if 之下），handoff --next-stage 依 STAGE_PHASE 的六個鍵寫；⛔ assign 不寫它…⚠️ **此處刻意記 writer 的符號、⛔ 不記「今天有幾張卡有值」**`
查證：`open_cmd.py` 的 `values["階段"] = "需求"` 不在任何 `if` 之下；`handoff_cmd.py` 有 `set_field_value(..., fields["階段"], phase)`、`phase = STAGE_PHASE.get(args.next_stage)`、六鍵；`grep -n "階段" assign_cmd.py` → **rc=1 零命中**。
**何時再變假**：`STAGE_PHASE` 增刪鍵、`assign` 開始寫本欄、或 `open` 不再無條件寫「需求」。
**不腐爛形式**：canonical §0.1 逐字「⚠️ **此處刻意以符號而非行號指認**」＋表一前 blockquote「⚠️ **「機械執行者」欄刻意以「檔名＋符號或運算式」指認，⛔ 不寫行號。**」

**②（同註解，A2）** 改後逐字：`…fail closed（raise CheckFailed）⇒ 切換那一刻會停的，是「**讀活看板、且把交付狀態餵進 gate_of**」的消費者。⚠️ **此處刻意記判準、⛔ 不記支數**——支數隨腳本增刪而變，判準不會。`
**何時再變假**：新增任何讀活看板並經 `gate_of` 的消費者，或 `DEFAULT_BASELINE_REF` 由凍結 ref 改指活看板。
**不腐爛形式**：同 ① 的符號指認，疊加 canonical 逐字「⭐ **查核者可複現**（基線釘死為字面 SHA `cd88270f`，⛔ 不用動態 merge-base）」—— 我照此把 cpbl 觀測基線釘成字面 `3b470d70`。⚠️「cpbl 有六個檔綁狀態語彙」**一個字未動**。

**③ §0.1 表 5c（A3）** 改後逐字：`一張沒有簡介的卡，open 得出來、amend／handoff 一路走到終態都不會被擋——⭐ 這是**結構性的**（--brief 可選、brief.try_parse_block 對解析失敗回 None 走 fail-open、validation.py 對簡介零命中），⛔ 不是「今天有幾張卡沒寫」。`
**何時再變假**：`--brief` 由可選改為必填，或 `validation.py` 出現以 `brief.parse_block` 為判準的檢查。
**不腐爛形式**：canonical 的**結構性恆真**形式。⭐ 為什麼**不**再用「只記量法」：那正是 `aiwf#150` 用過的一手，而它留下了「多數」。⭐ 這次在文字裡就地寫明兩者正交：「回填把每張卡都補齊，`--brief` 仍然是可選的」。

**④ §6.3 末段（A4）** 改後逐字：`且 validation.py 完全不驗簡介 ⇒ **沒有簡介的卡寫得出來，且一路走到終態不會被任何動詞擋下**（brief.try_parse_block 對解析失敗回 None…）。⚠️ **此處刻意記「寫得出來」而非比數**——`
⚠️ 前半**逐字保留**；查證今日仍為真：`grep -n "brief\|簡介" validation.py` → **rc=1 零命中**。

### V2 簡介覆蓋（自己重跑，⛔ 未引用卡面 204/206）

量法為該格自己指定的：`wf_cli.brief.parse_block` 對 `wf_cli.project.list_items` 逐張試解析（走 `import`）。量在 **`54d23e87`、2026-08-28T12:59:51+08:00**：母體 **208**、有簡介 **206**、無簡介 **2**（`WF-RESOURCE-HEADING-SUFFIX1-PROBE-ASSIGN1`、`WF-REVIEW-EVENT-MARKER-CONTRACT1`）。⭐ 卡面開卡當日 204/206，我實測 206/208 —— **幾小時內分母分子各 +2**，這正是我把數字降級為「漂移示例」而非論據的理由。⚠️ 本數字**未因 merge 失效**：`#166` 對 `brief.py` 的改動我逐行看過，是 docstring-only。

### V3「只有一支會停」（自己重跑）

cpbl `3b470d70` 唯讀執行，rc 分開取、⛔ 無管線：`workflow_ledger.py --check` rc=**1**，stderr 首行「`docs/TASKS.md 已於 2026-08-04 cutover 封存唯讀，本腳本已停用。`」；`state_plane_migrate.py --dry-run` rc=**0**，「`基準：origin/main @ 3b470d70…；卡數：38`」。讀取來源碼段逐字：`DEFAULT_BASELINE_REF = "origin/main"`、`ledger_md = git_show(args.baseline_ref, "docs/TASKS.md")` ⇒ 其預檢查跑的是由**凍結檔**解析出的 rows。⇒ **會停的是一支**；`workflow_ledger.py` 的 rc=1 是 2026-08-15 停用裁定，⛔ 與 `gate_of` 無關。cpbl `git status --porcelain` 無 tracked 變更。

### V4 回歸（rc 分開取、⛔ 全程無管線）

`pytest -q` @ merge-base `f0dfcfc6`（拋棄式 worktree 實跑）rc=0 `1479 passed, 1 skipped in 242.89s`；@ 交付 `54463adb` rc=0 `1479 passed, 1 skipped in 237.62s`。`uv lock --check` rc=0；`replay_escalation_rules.py` rc=0 `114/114 通過`；`canonical_citation_scan.py` rc=0 命中 0；`contract_tool_reconcile.py --check` rc=0；`qualified_pointer_scan.py` rc=0 紅 0（宇宙 80、掃 155 檔）。三支腳本以 CI 釘死的 `--python 3.12` 跑。

**點名的三件由紅轉綠，逐項實測**：`qualified_pointer_scan.py` rc=1 紅 1 → **rc=0 紅 0**；`test_qualified_pointer_scan.py` 3 failed → **37 passed rc=0**；全套 `3 failed, 1476 passed` → **rc=0 1479 passed 1 skipped**。

### V5 射程誠實（逐字）

⛔ 不蓋任何偵測機制；⛔ 不處理「cpbl 六個檔綁狀態語彙」那半句（`aiwf#150` 已裁非射程，一字未動）；⛔ 不碰 §0.1 兩軸語彙定義；⛔ 不回填任何卡的簡介；⛔ 不動 S2／S3 實作。⛔ **不宣稱** canonical 已無過期宣稱 —— 我只改了卡面點名的四處，且本輪就有第三、四處由他人在我的登記之上找出。

### A7 登記（依新判準 (a)(b)）

**(a)** 我自己的文字裡零個新 `檔:行號` —— 相對新 merge-base 對兩個檔跑正則，**rc=1 零命中**。
**(b) 登記項 ①**（`snapshot_population.py:5` 的 `project.py:377`）✅ **已由 `aiwf#166` 修復並合併（`f0dfcfc6`）**，換成 `project.py::list_items`；我自行 `git grep -n -E 'project\.py:[0-9]'` 複驗。
**(b) 登記項 ②**（`brief.py` 的 `try_parse_block` docstring）✅ **已由 `aiwf#166` 一併修掉** —— ⭐ 我依指示自行讀出現況逐字確認，⛔ 未採信 PM 那句。⭐ 新寫法是 canonical 家族**第五種**不腐爛形式（轉述判準而非逐字轉引），我原本沒列出來。
**新查**：`docs/WF_EVENT_IDEMPOTENCY1.md` 有 `project.py:28`（指 `FIELD_SPECS`）—— 我的編輯起於第 55 行，**未擾動它**；第 28 行在基線與新 HEAD 皆逐字為 `FIELD_SPECS: dict[...] = {`，**指得正確** ⇒ 無須登記。

### CI（⭐ 鎖 headSha）

`gh run list --branch … --json databaseId,headSha,status,conclusion` 過濾 `headSha == 54463adb…`：`run=33155127195 name='CI' status=completed conclusion=success`。該分支共 2 個 run，headSha 命中 1 個。⚠️ job 名 `tests (branch head)` 依 `ci.yml` 設計**永遠不是 required check**。

### commit trailer

`a715ae8`（shape=`implementation`）四行連續、無空行斷開、末段齊全。`54463ad`（shape=`merge_clean`）`Reviewed-by: —（基線更新 merge，無查核對象）`；⛔ 刻意不加 `Implemented-by` —— merge_clean 未著作任何內容，canonical 逐字「**要求 trailer 的是內容，不是 commit 這個容器**」，加上去是不誠實。

### 失誤登記（累計 11 筆）

1. 決定註解長度前沒檢查「誰用行號指著這個檔」—— A7 是明文約束，我只驗了單一方向，commit 之後才跑掃描器。
2. 第一時間把那筆紅預設成我寫的指標，查了才知是第三方且從出生就錯。
3. 首輪用系統 `python3`（3.14.3）跑腳本，未對齊 CI 釘死的 3.12。
4. `state_plane_migrate.py --dry-run` 先跑了才確認它不會寫檔。在被交代唯讀的 repo 上，順序應反過來。
5. zsh `$VAR:path` 展開吃字元致一次 `git show` 失敗。
6. **⭐ 碼段引述錯誤（PM 複驗抓到）** —— 我寫「`764a59ff` 上第 377 行是 `if field_meta.type == "TEXT":`」。**錯**，那是第 **376** 行。成因：用 `sed -n '373,381p' | cat -n` 讀，把 `cat -n` 的**相對**編號當絕對行號，整組差一。⭐ 諷刺在於這張卡的主題就是行號會錯位，而我論證它時自己錯位一行。
7. 「我加了 18 行」未量就寫 —— 實際淨 **+17**（`--numstat` 逐字 `19  2`）。我從 `--stat` 的 `21` 心算，而 21 是異動行數不是淨增。
8. 把 PM 的 `:526` 與我的 `:527` 預設成矛盾 —— 實際兩者都對，那句跨兩行。⛔ 差點寫成需裁定的分歧。
9. `cat -A` 在 macOS 不存在，我連用兩次，且 `||` 回退未觸發（退出碼被 `sed` 換掉）。
10. **⭐ 本輪：`grep -rn ... --include=*` 被 zsh glob 打掛，我差點把 `||` 印出的「（零命中）」當成證據** —— 那是**指令失敗**不是零命中。自己抓到後改用 `git grep` 重驗，才發現其實**有一筆命中**。⭐ 這正是 `keyword-absence-is-not-evidence` 的實例，而且差一點就寫進交付。
11. **merge 後我原本要直接收工，沒想到 merge commit 自己也受 trailer 守衛管轄** —— 是去讀 `doctor.py` 才發現。若直接回報，會交付一個機械可偵測的違規。

### 未驗清單（5 項）

1. **「新寫法不會再腐爛」仍未驗，構造上也驗不了** —— 我只能證明每處都寫下可 `grep` 的再變假條件，⛔ 不能證明那些條件充分。需要：查核者判定。
2. **merge 而非 rebase 的判定未複核** —— canonical §6 第 3 條例外的 (i)(ii) 我讀為皆不成立，但該條明訂由派工包作者判定、查核者複核。需要：查核者。
3. **同族過期是否還有第五處以上，未驗** —— 本輪已知第三處由 `#166` 查核者找到，不是我。我沒做窮舉掃描。
4. **`206/208` 用 live 查詢而非版控快照 artifact，判斷未經覆核** —— 需要：查核者或需求方。
5. **`scratchpad/v165c` 有一個 detached @ `a715ae8` 的 worktree，不是我建的**（推測是 PM 複驗用的）。⛔ 我沒動它。


## Comment 5450584132 · 2026-08-28T09:04:54Z

<!-- wf-review-event:v1 card_id=DOC-STALE-DEGREE-WORDS1 source_sha=54463adb9fce24776d1a939bf686806844e507fa attempt_id=DOC-STALE-DEGREE-WORDS1-e0-54463adb9fce24776d1a939bf686806844e507fa -->
## 查核裁決：REQUEST_CHANGES

- 卡：`DOC-STALE-DEGREE-WORDS1`　attempt_id：`DOC-STALE-DEGREE-WORDS1-e0-54463adb9fce24776d1a939bf686806844e507fa`
- 查核者：Claude Opus 5@Claude Code (Reviewer)　escalation_epoch：0
- source_sha：`54463adb9fce24776d1a939bf686806844e507fa`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-28T17:04:49+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD；git status --porcelain（唯讀進駐 .worktrees/stale-degree-words）`
  - 54463adb9fce24776d1a939bf686806844e507fa；status 輸出為空。收尾時複查仍同 ⇒ source branch 零位元寫入
- `git diff --name-status f0dfcfc6..54463adb；同指令對 54d23e87..a715ae8`
  - 兩次皆恰兩列：M AI_WORKFLOW.md、M cli/src/wf_cli/project.py ⇒ 本卡自己著作的 commit 相對舊基線亦不越界
- `git merge-base --is-ancestor a715ae8 54463adb; echo $?`
  - 0（為真）
- `git show --cc --format= 54463adb | wc -l`
  - 0 行 ⇒ shape 為 merge_clean
- `python3 正則掃 diff 新增行（[\w./-]+\.(py|md|sql|json|jsonl|sh|toml|ya?ml|txt)\s*:\s*\d+）；另判 project.py 新增行是否全為 # 開頭`
  - 新增 30 行／移除 7 行；檔:行號 命中 0（唯二匹配寬鬆 :\d+ 的是時戳 2026-08-28T12:59+08:00）；project.py 新增 19 行、非註解 0 行
- `uv run --frozen --project cli pytest -q（拋棄式 worktree @ 54463adb 與 @ f0dfcfc6 各一次）`
  - 交付 rc=0 1479 passed, 1 skipped in 259.22s；merge-base rc=0 1479 passed, 1 skipped in 259.12s ⇒ 未退化
- `qualified_pointer_scan.py @ 交付；pytest cli/tests/test_qualified_pointer_scan.py；uv lock --check；replay；ccs；ctr --check（rc 分開取、⛔ 無管線）`
  - 掃描 rc=0：掃 155 檔、宇宙 80、豁免 2、可強制 78、紅 0；37 passed in 14.22s rc=0；其餘四項 rc 依序 0／0（114/114）／0（命中 0）／0（59 個缺口全部有登記處置）
- `git grep -n -E 'brief|簡介' -- cli/src/wf_cli/validation.py`
  - rc=1，零命中 ⇒ 「validation.py 完全不驗簡介」今日為真
- `⭐ git grep -n 'brief\.parse_block' -- cli/src`
  - rc=1，零命中 ⇒ 再變假條件指名的字面在碼庫中不存在（碼庫一律 from .brief import parse_block 後裸用）
- `⭐ git grep -n -- '--brief' cli/src | wc -l`
  - 12，分布於 brief.py／card.py／amend_cmd.py／open_cmd.py／doctor.py 五個檔 ⇒ 「grep 得到唯一命中」不成立
- `⭐ git grep -n 'brief' -- cli/src/wf_cli/doctor.py`
  - doctor.py:2012 RuleEpoch(rule_id='brief_present', epoch='2026-08-25T02:40:38+08:00', disposition=DISPOSITION_MIGRATE)；doctor.py:2155 evaluate_card_conformance 內 brief_try_parse(body) is None → violations.append(('brief_present', …))；該函式 docstring 逐字「純函式，不碰網路」「⛔ 不修任何東西、⛔ 不拋例外」⇒ 今日只事後稽核、不擋動詞
- `git grep -n 'set_field_value(' -- cli/src；git grep -n '"階段"' -- cli/src；git grep -n 'pending_field_writes' -- amend_cmd.py`
  - 全庫 12 個 set_field_value 呼叫點，只有 open_cmd.py:334 與 handoff_cmd.py:903 寫階段；assign_cmd 對「階段」零命中；pending_field_writes 今日只裝 Initiative／簡介／資源宣告 ⇒ 「兩個 writer」今日成立
- `檢視 handoff_cmd.py 的 STAGE_PHASE 定義；sed -n '40,50p' cli/src/wf_cli/pitfalls.py`
  - STAGE_PHASE 恰六鍵，其 docstring 逐字「⚠️ 缺 maintenance …須待子卡 S2（cpbl 相容層）落地」；pitfalls.py 模組 docstring 已逐字寫「STAGE_PHASE 只有六個鍵」且無再變假註記 ⇒ 該數字的第二個居所
- `sed -n '1016,1030p' doctor.py；git grep -n 'TRAILER_GUARD_EPOCH = '；git log -1 --format='%aI %cI' a715ae8 與 54463adb`
  - required_trailers 對 merge_clean 逐字 return (MERGE_TRAILER,)；TRAILER_GUARD_EPOCH = 2026-08-13T00:00:00+08:00；a715ae8 為 2026-08-28T13:06:26+08:00、merge 為 16:13:34+08:00 ⇒ §6-3 例外條件 (ii) 不成立
- `grep -n rebase AI_WORKFLOW.md`
  - 第 746 行逐字：狹義例外 (i)(ii)「須同時成立」；「由撰寫派工包者判定並在派工包內具名、由查核者複核，⛔ 不得宣稱它已機械化」
- `cpbl 拋棄式 worktree @3b470d70：python3 scripts/workflow_ledger.py --check（rc 分開取）；git grep -n gate_of 全樹；git show 3b470d70:scripts/state_plane_migrate.py 檢視讀取來源`
  - workflow_ledger rc=1，stderr 首行逐字「docs/TASKS.md 已於 2026-08-04 cutover 封存唯讀，本腳本已停用。」（該檔 docstring 另逐字「需求方 2026-08-15 裁定停用」）；gate_of 命中僅 scripts/roadmap_lines.py（8）與 tests/test_roadmap_lines.py（9）⇒ roadmap_lines.py 是唯一生產消費者；state_plane_migrate 的 DEFAULT_BASELINE_REF='origin/main'、ledger_md = git_show(args.baseline_ref, 'docs/TASKS.md')、gate_of 零命中
- `git ls-tree -r --name-only origin/snapshots snapshots/2026-08-28/ 並解析 snapshot.json`
  - 存在；generated_at 2026-08-28T10:40:19+08:00、cards 208 筆；單筆鍵集為 card_id…content_type ⇒ ⛔ 無 body、無簡介 ⇒ 有簡介數 206 構造上無法由現行快照導出
- `git grep -n 結構性恆真 -- .（全庫）`
  - 零命中 ⇒ A5 要求的「canonical 已有的形式」在 ③④ 未逐字成立

### findings（6，其中 blocking 1）

- **DOC-STALE-DEGREE-WORDS1-R2-01**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`falsifier-written-as-open-instance-list`
  - evidence：§0.1 表 5c 與 §6.3 兩處新寫法共用同一條再變假條件：「--brief 由可選改為必填，或 validation.py 出現以 brief.parse_block 為判準的檢查——兩者都是 cli/src/wf_cli/ 內 grep 得到唯一命中的符號改動」。三項實測推翻它的機械性：(1) git grep -n 'brief\.parse_block' -- cli/src → rc=1 零命中（碼庫一律 from .brief import parse_block 後裸用）⇒ 指名令牌在今天的碼裡不存在。(2) git grep -n -- '--brief' cli/src | wc -l → 12（5 個檔）⇒「唯一命中」不成立。(3) 兩條已在庫內具名、且落點不在 validation.py 的證偽路徑：(a) cli/src/wf_cli/doctor.py 的 RuleEpoch(rule_id='brief_present', epoch='2026-08-25T02:40:38+08:00', disposition=DISPOSITION_MIGRATE)，判定點在 evaluate_card_conformance（brief_try_parse(body) is None → violations）。今天它是純函式事後稽核、不擋動詞（故受審句今日仍為真），但處置逐字是 migrate；(b) §6.3 自己下一行逐字「⇒ 承接者是既有卡的補寫與新卡的必填時點」——「新卡的必填時點」最自然的落點是 open_cmd 的一個 if card.brief is None:，不動 validation.py、也不必把 argparse 的 default=None 改掉。⇒ 兩條路徑各自會讓「沒有簡介的卡…一路走到終態不會被任何動詞擋下」為假，而條件指名的兩個符號一個字都不用改。另：該句的三腳結構性列舉（--brief 可選／try_parse_block fail-open／validation.py 零命中）漏了 doctor.brief_present 這條腿，而同表第 4 列的既有慣例正是用「⚠️ 僅事後偵測：cleanup.classify_state」表達這種狀態。
  - disposition：把 §0.1 5c 與 §6.3 的再變假條件由「列舉實例」改成「封閉述詞」，例如：「cli/src/wf_cli/ 內出現任何以缺簡介為由回非零 rc 或拋例外的路徑（今日封閉集合：brief_present 只出現在 doctor.evaluate_card_conformance 的事後稽核，try_parse_block 是唯一讀取入口且 fail-open）」。並把 doctor.brief_present（disposition=migrate）補進結構性列舉。⛔ 刪掉「grep 得到唯一命中」這句——實測不成立。⛔ 不要改用「只記量法」（那是 #150 留下殘餘的那一手）。
- **DOC-STALE-DEGREE-WORDS1-R2-02**　severity=minor　blocking=false　class=authoritative-artifact　attribution=executor　root_cause_id=`falsifier-written-as-open-instance-list`
  - evidence：project.py 階段欄註解的再變假條件逐字只列三個實例：「STAGE_PHASE 增刪鍵、assign 開始寫本欄、或 open 不再無條件寫『需求』」。但「本欄位有兩個 writer」會被任何第三個模組開始寫該欄推翻，而 amend_cmd 的 pending_field_writes 是通用機制（實測今日只裝 Initiative／簡介／資源宣告，加一行即成第三個 writer），review_cmd.py:416 亦已在寫別的欄位。
  - disposition：改成封閉述詞，例如「本句何時再變假：git grep -n 'fields["階段"]' cli/src 的命中集合不再恰為 open_cmd.py 與 handoff_cmd.py 兩處」。
- **DOC-STALE-DEGREE-WORDS1-R2-03**　severity=minor　blocking=false　class=authoritative-artifact　attribution=executor　root_cause_id=`scheduled-count-duplicated-into-second-home`
  - evidence：新註解逐字「handoff --next-stage 依 STAGE_PHASE 的六個鍵寫」。該數字對本句不承重，卻是一個已具名排程要變的量：STAGE_PHASE 的 docstring 逐字「⚠️ 缺 maintenance …須待子卡 S2（cpbl 相容層）落地」；且 cli/src/wf_cli/pitfalls.py 模組 docstring 已逐字寫「STAGE_PHASE 只有六個鍵」而無任何再變假註記 ⇒ 新寫法把同一個數字複製成第二個居所，S2 落地時要改兩處，其中只有一處帶註記。
  - disposition：建議刪成「依 STAGE_PHASE 的鍵寫」；若保留數字，須一併處理 pitfalls.py 那個沒有註記的居所，或就地明示由子卡 S2 同時更新兩處。
- **DOC-STALE-DEGREE-WORDS1-R2-04**　severity=minor　blocking=false　class=governance　attribution=coordinator　root_cause_id=`narrow-exception-invoked-outside-its-two-conditions`
  - evidence：canonical AI_WORKFLOW.md 第 746 行逐字：分支更新「一律本地 rebase」，狹義例外需 (i)(ii)「須同時成立」。複核結果兩者皆不成立：(i) main 上無已合併的碼引用 a715ae8（f0dfcfc6 為 aiwf#166，內容不含該 SHA）；(ii) a715ae8 committer 時間 2026-08-28T13:06:26+08:00、merge 2026-08-28T16:13:34+08:00，皆晚於 TRAILER_GUARD_EPOCH = 2026-08-13T00:00:00+08:00。PM 具名的理由（保住 a715ae8 在祖先鏈）不在該條列的兩項之內；且 a715ae8 從未作為任何 review event 的 source_sha（卡上 Log 無 review 事件，它只出現在需求方裁定留言的量測基準）。⚠️ 無實害：merge combined diff 實測 0 行、trailer 已補齊、全部守衛綠。
  - disposition：留痕上把本次記為「具名偏離 §6 第 3 條」而非「例外成立」。若「受審／被裁定留言引用的 SHA 須留在祖先鏈」要成為可重複使用的理由，須交需求方裁定是否在 §6-3 增列第三個條件——今天的兩個條件涵蓋不到它。⛔ 查核者不裁定 canonical 變更。
- **DOC-STALE-DEGREE-WORDS1-R2-05**　severity=minor　blocking=false　class=governance　attribution=planner　root_cause_id=`card-criterion-asserts-repo-wide-state-as-this-cards-bar`
  - evidence：V4 逐字要求「scripts/qualified_pointer_scan.py 五項 rc 全 0」，而該掃描器的紅數是整個 repo 的狀態，與需求方 2026-08-28 已裁定修正的原 A7（issuecomment-5449007200）完全同形；PM 只修 A7、未修 V4。本次 V4 達成是因為射程外的紅已被 aiwf#166 修掉（查核者實測 rc=0、宇宙 80、紅 0），⛔ 不代表 V4 的寫法是對的。
  - disposition：由 PM 決定同步修正 V4 的寫法，或在結案留痕上具名登記「V4 本輪偶然成立、其判準與原 A7 同病」。⛔ 本輪不因此退回執行者。
- **DOC-STALE-DEGREE-WORDS1-R2-06**　severity=minor　blocking=false　class=authoritative-artifact　attribution=executor　root_cause_id=`snapshot-artifact-cannot-carry-the-quantity-the-clause-demands`
  - evidence：§0.1 封存節逐字「本節引用的所有看板數字，來源是版控過的快照 artifact，⛔ 不是臨時查詢」，並逐字「⛔ 自行查詢後附上時戳仍然是自陳」。新文字寫入的 206/208 來自 live list_items。複核：origin/snapshots 的 snapshots/2026-08-28/snapshot.json 確實存在（generated_at 2026-08-28T10:40:19+08:00、cards 208 筆）⇒ 母體 208 本可由版控 artifact 佐證；但該 artifact 每筆 card 無 body 欄（鍵集實測為 card_id…content_type），而 5c 自己指定的量法是 brief.parse_block 對 body 逐張試解析 ⇒ 有簡介數 206 構造上無法由現行快照導出。⇒ 執行者的判斷大體成立，真正的缺口是快照 schema 與 §6.3 量法今天互斥。
  - disposition：本輪不退回。交 PM 開承接卡二選一：把 body／簡介覆蓋數納入 wfcli snapshot 的 artifact schema，或在 §0.1 就地註明「本量法與『只引版控快照』今天互斥」並具名承接者。執行者若要一併降低暴露面，最省的做法是把 206/208 整組拿掉——該格自己逐字寫著「本格刻意不記數字」。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: DOC-STALE-DEGREE-WORDS1-e0-54463adb9fce24776d1a939bf686806844e507fa
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待指派
findings:
  - finding_id: DOC-STALE-DEGREE-WORDS1-R2-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: falsifier-written-as-open-instance-list
    counting_eligible: true
  - finding_id: DOC-STALE-DEGREE-WORDS1-R2-02
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: falsifier-written-as-open-instance-list
    counting_eligible: false
  - finding_id: DOC-STALE-DEGREE-WORDS1-R2-03
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: scheduled-count-duplicated-into-second-home
    counting_eligible: false
  - finding_id: DOC-STALE-DEGREE-WORDS1-R2-04
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: governance
    attribution: coordinator
    root_cause_id: narrow-exception-invoked-outside-its-two-conditions
    counting_eligible: false
  - finding_id: DOC-STALE-DEGREE-WORDS1-R2-05
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: governance
    attribution: planner
    root_cause_id: card-criterion-asserts-repo-wide-state-as-this-cards-bar
    counting_eligible: false
  - finding_id: DOC-STALE-DEGREE-WORDS1-R2-06
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: snapshot-artifact-cannot-carry-the-quantity-the-clause-demands
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5461079215 · 2026-08-29T07:33:04Z

<!-- wf-review-event:v1 card_id=DOC-STALE-DEGREE-WORDS1 source_sha=cb62b20f03d9b90327aa358d9cfd4b3e81b5532e attempt_id=DOC-STALE-DEGREE-WORDS1-e0-cb62b20f03d9b90327aa358d9cfd4b3e81b5532e -->
## 查核裁決：REQUEST_CHANGES

- 卡：`DOC-STALE-DEGREE-WORDS1`　attempt_id：`DOC-STALE-DEGREE-WORDS1-e0-cb62b20f03d9b90327aa358d9cfd4b3e81b5532e`
- 查核者：gpt-5.6-terra@Codex　escalation_epoch：0
- source_sha：`cb62b20f03d9b90327aa358d9cfd4b3e81b5532e`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-29T15:33:01+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git status --short（/Users/ruanruan/Dev/ai-workflow/.worktrees/stale-degree-words）`
  - HEAD 為 cb62b20f03d9b90327aa358d9cfd4b3e81b5532e；被審 worktree 的 status 為空。
- `git diff --name-status f0dfcfc688999f75f9cb57d606fd1255f7e4528e cb62b20f03d9b90327aa358d9cfd4b3e81b5532e`
  - 恰兩檔：M AI_WORKFLOW.md、M cli/src/wf_cli/project.py；統計為 +44/-6。
- `git merge-base --is-ancestor f0dfcfc688999f75f9cb57d606fd1255f7e4528e cb62b20f03d9b90327aa358d9cfd4b3e81b5532e; rc=$?`
  - rc=0；指定 merge-base 確為交付 SHA 祖先。
- `uv run --frozen --project cli pytest -q（交付 worktree）; rc=$?`
  - rc=0；1479 passed, 1 skipped in 66.55s。
- `uv run --frozen --project cli pytest -q（/tmp/aiwf-review-165/merge-base @ f0dfcfc）; rc=$?`
  - 實跑至 100% 後程序結束；執行環境未回傳最終彙總行，故不把它推定為 rc=0。命令本身未接管線且 rc 由獨立變數取得。
- `git grep -n 'update_item_field_value(' -- cli/src/wf_cli ':!cli/src/wf_cli/project.py'; git grep -n 'set_field_value(' -- cli/src/wf_cli ':!cli/src/wf_cli/project.py'`
  - deploy_declare_cmd.py 有 2 個、deploy_state_cmd.py 有 4 個直接 update_item_field_value 呼叫；set_field_value 並非所有欄位寫入的唯一原語。
- `git grep -n 'from \.\+brief import' -- cli/src; git grep -n -E 'brief_present|disposition=DISPOSITION_MIGRATE' -- cli/src/wf_cli/doctor.py`
  - 簡介述詞的 importer 集合可重導出，且 doctor.brief_present 為事後稽核 migrate；R2-01 已閉環。
- `git -C /Users/ruanruan/Dev/cpbl-analytics show 3b470d70:scripts/roadmap_lines.py | rg -n 'gh project item-list|def gate_of|gate_of\(cid'; git -C /Users/ruanruan/Dev/cpbl-analytics show 3b470d70:scripts/state_plane_migrate.py | rg -n 'DEFAULT_BASELINE_REF|git_show'`
  - roadmap_lines.py 讀活看板並呼叫 gate_of；state_plane_migrate.py 的 DEFAULT_BASELINE_REF=origin/main 且讀封存 docs/TASKS.md。R3 已移除固定支數。
- `gh issue view 165 --repo ruan6047/ai-workflow --json body,comments`
  - R2-05 已在 2026-08-28T17:06:59+08:00 修正 V4；R2-04 已在 R3 派工留痕表述為具名偏離、非例外成立。

### findings（1，其中 blocking 1）

- **DOC-STALE-DEGREE-WORDS1-R3-01**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`falsifier-written-as-open-instance-list`
  - evidence：project.py 的 R3 新註解把 set_field_value 宣稱為『欄位寫入的唯一原語（所有欄位寫入都經它）』，並以其呼叫點當作階段 writer 的封閉集合。但 project.py 另定義 update_item_field_value；交付 SHA 的 deploy_declare_cmd.py 直接呼叫 2 次、deploy_state_cmd.py 直接呼叫 4 次，均未經 set_field_value。故這個唯一原語述詞今天即為假，也無法保證未來階段 writer 必然出現在所列集合。
  - disposition：把階段 writer 的再變假條件改成對兩條寫入原語均封閉的述詞／重新導出法，或先將唯一原語事實在程式碼中做實；不可繼續宣稱 set_field_value 是所有欄位寫入的唯一原語。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: DOC-STALE-DEGREE-WORDS1-e0-cb62b20f03d9b90327aa358d9cfd4b3e81b5532e
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: no
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 查核者（待指派）
findings:
  - finding_id: DOC-STALE-DEGREE-WORDS1-R3-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: falsifier-written-as-open-instance-list
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5461290769 · 2026-08-29T08:25:45Z

## 升級裁定：② 退回上一階段（規劃）

**裁定值**：四選一之 ②「退回上一階段」。⛔ 不是換人、⛔ 不是停卡、⛔ 不是退回無效。

### 為什麼是 ②

同一個 `root_cause_id = falsifier-written-as-open-instance-list` 出現在 **R2-01、R2-02、R3-01** —— 第三輪。判準逐字：「同族第三輪＝形狀錯了，⛔ 不是實例沒抓乾淨」。⇒ 再派第四輪去修第四個實例，形狀不會變。

**規格本身要求了做不到的事。** 本卡要求把假宣稱改寫成「封閉的證偽述詞」，但這個 repo 的欄位寫入本來就有**兩條原語路徑**，要讓述詞真的封閉必須先把碼改成只有一條——而那⛔ 不在一張 T1 文件卡的射程內。

⇒ 規格要在規劃階段重新定射程。建議的跳出方向：**⛔ 不宣稱封閉性**，改成「記重新導出的量法 ＋ 逐字標明它得到的是下界」。

### PM 對 R3-01 的獨立複驗（⛔ 不是轉述查核者）

`project.py` 定義兩個欄位寫入原語：`set_field_value`（:383）與 `update_item_field_value`（:414）。交付 SHA `cb62b20f` 上 `update_item_field_value` 的呼叫點實測 **6 個**：`deploy_declare_cmd.py:134,137`、`deploy_state_cmd.py:156,157,158,159`，全部不經 `set_field_value`。查核者報的 2+4 與實測一字不差。

⚠️ **但 R3 的結論本身仍成立**：那 6 個呼叫寫的是部署狀態／Status／owner／最後交接，⛔ 沒有一個寫「階段」。⇒ 為假的是**保證**，⛔ 不是答案。重新定射程時不必推翻「階段今天有兩個 writer」這個結論。

### 未被本裁定處置

⚠️ 查核者⛔ **未在裁決內文寫入自身 session id 與訊息定位**，而派審詞逐字要求了。本 repo 的 `author` 欄恆為 `ruan6047`（單一 token）⇒ 該裁決的撰寫者身分**今天無法核對**。此落差不影響 R3-01 的事實正確性（PM 已獨立複驗），但身分自述那條規則第一次實施即未被遵守，應登記。

### 裁定者

需求方 ruan6047，2026-08-29 於本 session 對話中逐字回覆「接受你的建議」，係對 PM 提出四選一並推薦 ② 後採納。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。


## Comment 5464850072 · 2026-08-29T20:59:07Z

## 執行者交回：R4 交付報告、失誤登記與未驗清單（`DOC-STALE-DEGREE-WORDS1` / #165）

> **轉錄自述**：本則由 **PM（Claude Opus 5 @ Claude Code）** 以需求方 token 發文，內容為**執行者 `Claude Opus 5@Claude Code` 交回 PM 的報告逐字轉錄**。⛔ PM 未增刪內容、未加緩和語。author 欄恆為 `ruan6047`，⛔ 不代表由需求方撰寫。PM session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

---

**交付 SHA（40 字元）**：`1c3607054aad3a39b8165bdb3f6a89f7f149cdb8`
分支 `ai/opus-5/DOC-STALE-DEGREE-WORDS1`，worktree `/Users/ruanruan/Dev/ai-workflow/.worktrees/stale-degree-words`，`git status --porcelain` 為空。
基線 merge-base `f0dfcfc688999f75f9cb57d606fd1255f7e4528e`（`git merge-base --is-ancestor` rc=0）。
⛔ 未 push、⛔ 未 merge、⛔ 未跑任何 `wfcli` 寫入動詞。

⚠️ **本輪產生過兩顆 SHA**：`f888b0c3…`（首次 commit）→ `1c360705…`（`--amend`，只重排 `project.py` 一處換行、內容等價）。**請一律引用 `1c36070`**，`f888b0c` 已不在分支上。

---

## 1. 四處逐處（改前逐字 → 改後逐字 → 形式 → 為什麼 → 再變假條件 → 實跑輸出）

### 處① `project.py` 階段欄註解「本欄位建立後暫時無人寫入」（A1）

**改前逐字**：`#: ⇒ 本欄位建立後暫時無人寫入，交付狀態仍承載階段與狀態兩者。`

**改後**：改為「本欄位今天有 writer，⛔ 不是無人寫入」，並就地記量法與下界性質（全文見交付 diff）。

**形式**：**只記量法 ＋ 逐字標明下界**。

**為什麼**：R3-01 已證實封閉性在本 repo 做不到——欄位寫入有兩條互不呼叫的原語。⭐ 關鍵是本句宣稱的邏輯型別：「**有** writer」是存在型，下界對存在型**恰好充分**（下界 ≥ 1 ⇒ 存在為真）；R3 的錯不在答案錯，在於它為一個存在型宣稱套了一個做不到的全稱保證。改寫後就地寫死「下界證不成『只有』」，⛔ 不再作封閉宣稱。

**再變假條件**：量法輸出裡不再有任何一個把「階段」送進欄位寫入的呼叫點（下界歸零）。

**實跑輸出**（⛔ 無管線）：

```
$ git grep -n '"階段"' -- cli/src ':!cli/src/wf_cli/project.py'
cli/src/wf_cli/commands/handoff_cmd.py:308:PHASE_LOG_LABEL = "階段"
cli/src/wf_cli/commands/handoff_cmd.py:526:        item.text("階段"), item.fields.get("交付狀態"), STAGE_STATUS, STAGE_PHASE
cli/src/wf_cli/commands/handoff_cmd.py:902:        if phase is not None and "階段" in fields:
cli/src/wf_cli/commands/handoff_cmd.py:903:            set_field_value(runner, project, item.item_id, fields["階段"], phase)
cli/src/wf_cli/commands/open_cmd.py:332:    values["階段"] = "需求"
rc=0
```

判讀：5 個命中中，`handoff_cmd.py:903` 與 `open_cmd.py:332` 是寫入（另三個為常數、讀取、守衛）⇒ 下界 = 2 ≥ 1 ⇒ 「有 writer」為真。

同段第二句「交付狀態仍同時承載階段與狀態」的再變假條件是 `FIELD_SPECS` 的「交付狀態」選項元組移除階段詞。實跑得 `stage-flavoured = ['💡需求','🔬研究中','🧭規劃中']`、`state-flavoured = ['🔍待查核','✅通過']`、`BOTH_AXES_PRESENT = True`、rc=0。

### 處② 同註解「切換那一刻三支腳本會停」（A2）

**改前逐字**：`#: roadmap_lines.gate_of 對未知狀態 fail closed，切換那一刻三支腳本會停。`

**形式**：候選集合用**只記量法 ＋ 下界**；`gate_of` fail-closed 這一項用**釘死探針**。

**為什麼**：R3 的再變假條件是「新增任何讀活看板並經 gate_of 的消費者」——那是**未來實例的開放清單**，跑不出來，正是連三輪的同一形狀。⭐ 條件 (b) 我**先寫成 grep 再自己推翻**（見失誤登記 1）。

**再變假條件**：(a) 交集下界歸零；(b) `gate_of` 不再 fail closed；(c) `DEFAULT_BASELINE_REF` 由凍結 ref 改指活看板。

**實跑輸出**（⛔ 無管線）：

```
$ git grep -l 'gate_of' 3b470d70 -- scripts
3b470d70:scripts/roadmap_lines.py
rc=0
$ git grep -l 'item-list' 3b470d70 -- scripts
3b470d70:scripts/roadmap_lines.py
3b470d70:scripts/state_plane_migrate.py
3b470d70:scripts/workflow_ledger.py
rc=0
⇒ 檔案交集 = {roadmap_lines.py}，下界 1

$ python3 -c "…; rl.gate_of('PROBE','不存在的狀態') …"
fail-closed OK: CheckFailed
rc=0
```

### 處③ `AI_WORKFLOW.md` §0.1 執行者狀態表 5c 列（A3）

**形式**：**只記量法 ＋ 逐字標明下界**，且**同時收窄被支撐的宣稱本身**。

**為什麼**：「不存在擋下路徑」是**全稱否定**，而字面枚舉得到的是擋下路徑的**下界**——下界 0 ⛔ 不蘊含實際為 0。R3 在此寫「證偽述詞（封閉）」，形式上比原本的定性程度詞**看起來更像保證**，實際上一樣證不出來。⇒ 本輪把量法的下界性質與**宣稱的收窄**一起寫在同一格。

**再變假條件**：量法輸出裡出現任何一個在缺簡介時回非零 rc 或拋未攔截例外的成員（今日下界為 0）。

**實跑輸出**：`git grep -n -E "from \.+brief import|import brief" -- cli/src` 得 8 個 importer（rc=0）；`git grep -n -E "card-brief:begin|## 簡介" -- cli/src` 得 7 處（rc=0）。判讀：8 個 importer 中 `try_parse_block`／`drifted` 為 fail-open，`validate_shape` 只在**有給**簡介時驗形狀 ⇒ **缺簡介時回非零 rc 或拋未攔截例外的成員 = 0（下界）**。

### 處④ `AI_WORKFLOW.md` §6.3 末段（A4）

**形式**：**只記量法 ＋ 逐字標明下界**（與處③同一病灶的第二個居所，同一手法）。

**為什麼**：A4 逐字要求保留前半「`validation.py` 完全不驗簡介」（今日仍真）並修後半。本輪把它降成「**可證偽的存在型前半**（沒有簡介的卡寫得出來）＋**搜尋型後半**（以該量法搜不到擋它的路徑）」，並就地寫明封閉性在本 repo 做不到、硬寫封閉「看起來還更像保證」。⭐ 把三輪的教訓寫進條文本身，⛔ 不只是改掉一次實例。

⚠️ 量法的正則刻意寫 `\.+` 而非 `\.`——`open_cmd` 走 `from ..brief import`，只寫一個點會漏掉它，⭐ 本句初稿就是這樣漏的。

**前半的實跑**：`git grep -n -E 'brief|簡介' -- cli/src/wf_cli/validation.py` → rc=1，零命中 ⇒ 「validation.py 完全不驗簡介」今日仍為真。

---

## 2. V2 簡介覆蓋率（自己重跑，⛔ 未引用卡面）

量法：`wf_cli.brief.parse_block` 對 `list_items` 逐張試解析（5c 自己指定的量法）。腳本住 scratchpad、⛔ 未進 repo，一律 `import` ⛔ 未重打常數。

- 量在 SHA `cb62b20f03d9b90327aa358d9cfd4b3e81b5532e`，時點 `2026-08-29T16:40:41+08:00`，來源 live GraphQL `list_items`

```
population    = 211
with_brief    = 209
without_brief = 2
```

無簡介卡逐張：`WF-RESOURCE-HEADING-SUFFIX1-PROBE-ASSIGN1`（#140，🛑已停止）拋 `BriefError: body 內找不到獨立標題行 ## 簡介`；`WF-REVIEW-EVENT-MARKER-CONTRACT1`（#15，🏁完成）拋 `BriefError: 無法以 Log 標題切分 body…`。

⭐ 卡面的 204/206（量於 `54d23e87`）**一天內已成 209/211** —— 這正是本卡在講的事，⛔ 交付文字裡因此一個數字都沒記。

**版控佐證**：`origin/snapshots` 的 `snapshots/2026-08-29/snapshot.json`（`generated_at 2026-08-29T10:48:07+08:00`，snapshots 分支 commit `fe100080653755874a0f7c82bc5e0b4678c2eb77`，sha256 `63548974758a9c416624aa34335e1002a76b02545b48febd009a3ef9a7973839`）`cards = 211`，與 live 母體一字不差。⚠️ **但 `with_brief = 209` 仍無法由該 artifact 導出**：其 per-card 鍵集**無 `body`**。R2-06 指出的 schema 互斥今天未閉環。

---

## 3. V3 A2「只有一支會停」（自己重跑）

在 cpbl 拋棄式 worktree（`3b470d7023f73621c53b0d81118a3ca005801ad8`，`%cI` = `2026-08-23T02:04:29+08:00`）上跑，rc 分開取、⛔ 全部無管線。

| 腳本 | rc | 輸出首行（逐字） |
|---|---:|---|
| `workflow_ledger.py --check` | **1** | stdout 0 bytes；stderr `docs/TASKS.md 已於 2026-08-04 cutover 封存唯讀，本腳本已停用。` |
| `state_plane_migrate.py --dry-run` | **0** | `基準：origin/main @ 0146fd3e72fb0ef2d17a6b47221dfc01d17c23b6；卡數：38` |

讀取來源碼段逐字：`DEFAULT_BASELINE_REF = "origin/main"`；`ledger_md = git_show(args.baseline_ref, "docs/TASKS.md")` ⇒ 讀的是 `git show` 出來的**封存唯讀凍結檔**，⛔ 不是活看板；`gate_of` 在該檔零命中。

⇒ 三支之中只有 `roadmap_lines.py` 會被看板語彙切換停掉。

---

## 4. V4 回歸不退化（⛔ 全部無管線，rc 分開取）

| 項目 | 位置 | rc | 結果 |
|---|---|---:|---|
| `uv run --frozen --project cli pytest -q` | 交付 SHA | **0** | `1479 passed, 1 skipped in 59.92s` |
| 同上 | merge-base（拋棄式 worktree） | **0** | `1479 passed, 1 skipped in 61.68s` |
| `uv lock --check` | 交付 SHA | **0** | `Resolved 7 packages in 4ms` |
| `scripts/replay_escalation_rules.py` | 交付 SHA | **0** | `114/114 通過` |
| `scripts/canonical_citation_scan.py` | 交付 SHA | **0** | `掃描檔案數：155　命中（不含排除）：0　排除集：0 項` |
| `scripts/contract_tool_reconcile.py --check` | 交付 SHA | **0** | `[reconcile] OK：59 個缺口全部有登記處置，判定一致。` |

通過數 1479 = merge-base 的 1479 ⇒ **未退化**。腳本以 CI 釘死的 python 3.12 跑。兩個拋棄式 worktree 用畢皆已 `git worktree remove --force`。

**A6／A7 機械驗證**（相對 merge-base）：`git diff --name-status` 恰兩列；`--stat` 為 `+69/-7`；`cli/src` 下改動 40 行、**非註解 0 行**；A7(a) 新增 69 行以嚴格與寬鬆兩種正則掃描皆 **0 命中**；A7(b) `scripts/qualified_pointer_scan.py` rc=**0**，`掃描檔案數：155／宇宙：80／豁免：2／可強制：78／紅：0` ⇒ **本卡未浮出任何既有的紅，⛔ 無須具名登記**；定性程度詞（`多數|大部分|大多|幾乎所有`）在新增行 **0 命中**。

---

## 5. V5 射程誠實（逐字）

- ⛔ **不蓋任何偵測機制**：沒有新增守衛、CI 步驟、或會擋下動詞的碼。
- ⛔ **不處理「cpbl 有六個檔綁狀態語彙」那半句**（aiwf#150 已裁非射程）。⛔ 未動一個字。
- ⛔ **不碰 §0.1 的兩軸語彙定義**。
- ⛔ **不回填任何卡的簡介**：兩張無簡介的卡今天仍無簡介。
- ⛔ **不動 S2／S3 的實作**。
- ⛔ **不宣稱「canonical 已無過期宣稱」**：只改了卡面點名的四處，⛔ 未對 canonical 全文窮舉；且下述兩處同族過期宣稱**確實存在而本卡不修**。
- ⛔ **不宣稱新寫法不會再腐爛**：能證明的只有「每一處都寫下了一個今天跑得出來的再變假條件」，⛔ **不能證明那些條件充分**。

---

## 6. 失誤登記與未驗清單

### 6.1 失誤登記（逐項，⛔ 不合併計數）

1. **處②的再變假條件 (b) 我先寫了 `git grep -n "raise CheckFailed" 3b470d70 -- scripts/roadmap_lines.py`**。實跑得 28 個命中，橫跨 `parse`／`reconcile`／`render` 等多個函式，**指不到 `gate_of` 本身** ⇒ 那是構造上不會失敗的檢查。commit 前自行實跑才發現，改成直接呼叫 `gate_of` 的釘死探針並實跑證明。⚠️ **若不是 A5／V1 新增的「跑得出」要求，這個零資訊檢查會原樣進交付。**
2. **§6.3 改寫第一版只換掉「證偽述詞（封閉）」那一段，卻把它支撐的全稱否定原封不動留著** ⇒ 等於把量法降級成下界、卻讓結論維持在封閉強度，**形狀與 R2-01／R3-01 完全相同**。自行重讀時發現並收窄；§0.1 5c 列有同一問題，一併收窄。
3. **首次 commit `f888b0c3` 在 `project.py` 留下一處排版破碎的換行**。以 `--amend` 修為 `1c360705`，內容等價。⇒ 本輪存在兩顆 SHA，`f888b0c3` 已不在分支上。
4. **卡面 A3/A4 的 204/206 我一度打算直接沿用**（因兩張無簡介卡與卡面一致）。實跑後母體是 211、有簡介 209 —— 兩張無簡介卡相同，**母體卻差 5 張**。若沿用，報告會出現一個一天前的母體數卻掛著今天的時點。

### 6.2 射程外發現（⛔ 本卡不修，交 PM 判斷）

- **`cli/src/wf_cli/card.py` 的 `amend_brief` docstring 逐字**：`⚠️ **既有卡沒有 ## 簡介 區段**（canonical §6.3 逐字：今天沒有任何卡符合這一條）。` 與同段 `那會讓 188 張既有卡永遠補不了簡介`。⇒ 它引用的 canonical 原句**已於 2026-08-26 更正**，這個居所沒跟上；`188` 亦為固定數（今日母體 211）。
- **`cli/src/wf_cli/commands/amend_cmd.py` 的 `--brief` help 文字**：同一句話的第四個居所，同樣帶固定數 188。
- ⛔ **兩者皆非本卡宣告資源**，⛔ 未動一個位元；且 `amend_cmd.py` 那一處若要改是 help 字串、屬非註解改動，A6 明文禁止。
- ⭐ 這兩處是**本卡量法自己抓出來的**，⛔ 不是額外掃描 —— 交付的量法在第一次執行時就找到了它自己射程外的兩個同族實例。

### 6.3 未驗清單（每項標明驗不了的原因，⛔ 不合併計數）

1. **新寫法會不會再腐爛 —— 未驗。** 能證明的是每處都寫下了今天跑得出來的再變假條件並貼了輸出；**⛔ 不能證明那些條件充分**。⚠️ 這是「驗不了」不是「沒去驗」：一個證偽條件是否窮盡，無法從 artifact 內部判定——這正是本卡連三輪的根因所在。
2. **`with_brief = 209` 未由版控 artifact 佐證 —— 驗不了。** 母體 211 已由快照佐證，**但該 artifact 的 per-card 鍵集無 `body`**，而量法是對 body 逐張試解析 ⇒ 構造上導不出來。R2-06 已具名此互斥，本卡射程不含修快照 schema。
3. **§6.3／5c 的量法是否窮盡「所有可能擋下動詞的路徑」—— 驗不了，且交付文字已就地承認。** 字面枚舉對「以別的標記自寫檢查」「資料驅動的規則表」是盲的。
4. **未實際跑過任何 `wfcli` 寫入動詞去確認一張無簡介的卡真的能 `open`／`amend`／`handoff` —— 沒去驗（刻意）。** 原因：會變更真實 Project 狀態，且派工詞明令⛔ 不跑 wfcli 寫入動詞。
5. **`gate_of` 釘死探針只在 cpbl `3b470d70` 上跑過，⛔ 未在 cpbl main 上跑 —— 刻意不驗。** 原因：註解本身把基線釘死為該 SHA。⚠️ 代價是：若 main 上 `gate_of` 已改，本註解不會自己知道。
6. **「`doctor.brief_present` 一旦執行即為假」未實跑證實 —— 沒去驗。** 沿用查核者的實測而未自己觸發 migrate 路徑；觸發它需要改 `doctor` 的 epoch 處置，屬非註解改動、A6 禁止。

---

## 7. 交付摘要

| 項目 | 值 |
|---|---|
| 交付 SHA | `1c3607054aad3a39b8165bdb3f6a89f7f149cdb8` |
| 分支 | `ai/opus-5/DOC-STALE-DEGREE-WORDS1`（⛔ 未 push） |
| merge-base | `f0dfcfc688999f75f9cb57d606fd1255f7e4528e`（`--is-ancestor` rc=0） |
| 相對 merge-base | 恰兩檔 `+69/-7`；`cli/src` 非註解改動 0 行 |
| 本輪相對 `cb62b20f` | `+50/-26` |
| commit 訊息尾四行 | 逐字比對 `MATCH = True` |
| worktree | `git status --porcelain` 為空 |

⭐ **本輪的核心變更不是換掉第四個實例，是換掉保證的強度**：四處全部改為「只記量法 ＋ 逐字標明下界」（`gate_of` fail-closed 一項改用**已實跑證明**的釘死探針），並且**把被支撐的宣稱一起收窄**——存在型宣稱留著（下界足以證成），全稱否定降級為「以該量法搜不到」。⛔ 交付文字裡不再有任何封閉性承諾。


## Comment 5464938738 · 2026-08-29T21:17:59Z

<!-- wf-review-event:v1 card_id=DOC-STALE-DEGREE-WORDS1 source_sha=1c3607054aad3a39b8165bdb3f6a89f7f149cdb8 attempt_id=DOC-STALE-DEGREE-WORDS1-e0-1c3607054aad3a39b8165bdb3f6a89f7f149cdb8 -->
## 查核裁決：APPROVE

- 卡：`DOC-STALE-DEGREE-WORDS1`　attempt_id：`DOC-STALE-DEGREE-WORDS1-e0-1c3607054aad3a39b8165bdb3f6a89f7f149cdb8`
- 查核者：gpt-5.6-terra@Codex　escalation_epoch：0
- source_sha：`1c3607054aad3a39b8165bdb3f6a89f7f149cdb8`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-30T05:17:56+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git status --short; git merge-base --is-ancestor f0dfcfc688999f75f9cb57d606fd1255f7e4528e 1c3607054aad3a39b8165bdb3f6a89f7f149cdb8`
  - HEAD 為指定 source SHA；工作區乾淨；祖先判定 rc=0。身分自述：Codex session id `01a04f55-fa21-7f31-b536-87c7098e5212`；timestamp `2026-08-30T05:16:28+08:00`。
- `git diff --name-status/--numstat f0dfcfc688999f75f9cb57d606fd1255f7e4528e..1c3607054aad3a39b8165bdb3f6a89f7f149cdb8`
  - 恰兩檔 AI_WORKFLOW.md、cli/src/wf_cli/project.py；+69/-7。
- `uv run --frozen --project cli pytest -q（source SHA 與 merge-base 各一次）`
  - 兩次皆 rc=0，1479 passed、1 skipped（分別 69.75s、72.68s）。
- `git diff 新增 cli/src 行的非註解掃描；新增行的檔:行號及程度詞掃描；scripts/qualified_pointer_scan.py`
  - 非註解 0 行；兩種新增行掃描均 rc=1 零命中；qualified_pointer_scan rc=0、紅 0。
- `git grep -n '"階段"' -- cli/src ':!cli/src/wf_cli/project.py'`
  - rc=0；實際欄位寫入命中 handoff_cmd.py:903 與 open_cmd.py:332，存在型「有 writer」由下界 >=1 證成，沒有推出封閉集合。
- `cpbl@3b470d70 的 gate_of/item-list 交集量法、gate_of('PROBE','不存在的狀態') 探針、workflow_ledger.py --check、state_plane_migrate.py --dry-run`
  - 交集只有 roadmap_lines.py；探針 rc=0 並印 fail-closed OK: CheckFailed；workflow_ledger rc=1 為已停用；state_plane_migrate dry-run rc=0 且讀 docs/TASKS.md。
- `git grep -n -E 'from \.+brief import|import brief' -- cli/src；git grep -n -E 'card-brief:begin|## 簡介' -- cli/src；try_parse_block 缺簡介探針`
  - 兩量法皆 rc=0；缺簡介探針 rc=0 並回傳 None；文件將結論限制為「以該量法搜不到」，明記下界不證明不存在。四處舊的當日假話均已移除，且未驗清單第 1 項的「條件充分性不可由 artifact 內部證明」不再被偽裝成封閉保證。
- `uv lock --check；scripts/replay_escalation_rules.py；scripts/canonical_citation_scan.py；scripts/contract_tool_reconcile.py --check`
  - 全部 rc=0；replay 114/114 通過、citation 命中 0、reconcile 59 個缺口皆有處置。

### findings（0，其中 blocking 0）

- （無）

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: DOC-STALE-DEGREE-WORDS1-e0-1c3607054aad3a39b8165bdb3f6a89f7f149cdb8
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 查核者（待指派）
findings: []
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。
