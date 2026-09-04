# #101 WF-STATUS-VOCAB-ALIGN1 狀態詞彙與落點對齊：加規劃期兩狀態與三個動詞，執行階段統一到 🔨執行中，兩個廢止值標註
- state: closed  created: 2026-08-18T11:31:21Z  closed: 2026-08-18T12:08:42Z
- url: https://github.com/ruan6047/ai-workflow/issues/101
- comments: 1

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code PM
<!-- wf-routing:v1 -->
- 執行：待指派（建議 經濟型；純比對與列舉對齊，無閘門、無行為判斷。驗收全部是「兩邊字串相不相等」，逐位元組機械可判，不需設計實測路徑。）　查核：待指派（建議 經濟型；同上：查核只需重跑比對腳本並確認輸出一致，不需變異檢驗。難的那半（preflight 會不會擋、拒絕時零寫入）已切到 WF-STATUS-VOCAB-GATE1。）
- Initiative：—　spec 基線：f207d2ecf80556d6b90beeb0438bf648288a5fd9
- DB：db_scope=none
- 服務的原始目標：契約寫的執行狀態，要跟機器實際寫的是同一個

## 簡介
<!-- card-brief:begin -->
把執行階段的狀態詞彙對齊成同一個：cli/src/wf_cli/project.py 的 FIELD_SPECS 與線上 Project #4 該欄 options 逐位元組且逐順序相等、handoff --next-stage 的 requirement／research／planning／implementation 各寫對應狀態、assign 預設改寫 🔨執行中、🚧進行中 與 ⏳待執行 保留在 FIELD_SPECS 但於 AI_WORKFLOW.md:18 與 templates/TASKS.md:6 標為已廢止的歷史值。**適用時機**：契約推薦的狀態詞跟機器實際寫的不是同一個；或要查某個狀態值今天有沒有專責寫入者時。⛔ 非射程：不驗 preflight、不驗任何 --status 收斂、不驗 iteration 遞增邏輯——三者全屬 WF-STATUS-VOCAB-GATE1，⛔ 不得以「狀態已對齊」暗示寫入面已有閘門。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：執行階段的狀態詞彙，契約與機械面指的不是同一個東西，三處落差今天同時成立。(1) 契約推薦的那個沒有寫入者：AI_WORKFLOW.md:18 把 🔨執行中 列為執行階段正線值、templates/review-escalation.md:9,11 也指名它為 preflight-failed／review-invalid 的回落點，但對帳器實測它是 read-only、零專責寫入者。(2) 實際被寫的那個不在契約裡：🚧進行中 是 assign 的預設值（assign_cmd.py:120）與 handoff --next-stage implementation 的常數（handoff_cmd.py:88），歷史上被寫 88 次，而 grep -c 🚧進行中 AI_WORKFLOW.md = 0；它落在對帳器盲區——universe 由掃文件導出，文件沒寫的符號它看不見。(3) 碼側與線上不一致：FIELD_SPECS 交付狀態 13 值、線上 Project #4 該欄 15 值（🔬研究中／🧭規劃中 於 2026-08-18 由人工 GraphQL 補上），而 ensure_fields（project.py:154-169）對既有欄位是 if name in existing: continue、永不補選項，兩邊沒有機械連結。另有 ⏳待執行：零寫入者、全史使用 1 次，只存在於流程圖裡。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/project.py",
    "file:cli/src/wf_cli/commands/handoff_cmd.py",
    "file:cli/src/wf_cli/commands/assign_cmd.py",
    "file:cli/tests/test_commands_mocked.py",
    "file:cli/tests/test_doctor.py",
    "file:cli/tests/test_registry.py",
    "file:AI_WORKFLOW.md",
    "file:templates/TASKS.md",
    "file:templates/handoff-contract.md",
    "file:docs/CONTRACT_TOOL_RECONCILE.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 1) FIELD_SPECS 交付狀態與線上 Project #4 該欄 options 逐位元組且逐順序相等，比對由腳本產生不接受人工聲明；不成立：任一側多少一值、順序不同、或含 variation selector 零寬字元。2) handoff --next-stage 的 requirement／research／planning 各把交付狀態寫成 💡需求／🔬研究中／🧭規劃中，逐位元組比對寫入後的欄位值。3) handoff --next-stage implementation 寫入 🔨執行中；assign 不帶 --status 時寫入 🔨執行中；STAGE_STATUS 內不再有 🚧進行中。4) 🚧進行中與⏳待執行仍在 FIELD_SPECS（不得刪），AI_WORKFLOW.md:18 與 templates/TASKS.md:6 兩處都標為已廢止的歷史值；git grep 那兩值於 cli/src 的命中只剩 project.py 的 FIELD_SPECS 一處。5) 三處狀態序列（AI_WORKFLOW.md:18、templates/TASKS.md:6、templates/handoff-contract.md:22 的 next_stage 值域）彼此一致且與 FIELD_SPECS 一致，比對輸出由腳本產生。6) 對帳器對 delivery_status/🔨執行中 的判定由 read-only 變 ok；不成立：只改了 canonical 措辭而沒有任何動詞寫它。7) 附 base 與 head 兩棵樹 --format json 的逐鍵 diff，含新增缺口、移除缺口、verdict 變更，以及 verdict 未變但 writers／readers／mentions 變動的列——#99 漏的正是最後這類。8) docs/CONTRACT_TOOL_RECONCILE.md §7 以 --format md 整份重生，與工具輸出逐列一致；不得手補個別行號，PR #100 已示範手補會漏（md 渲染器截斷引用清單，四處位移只看得見一處）。

## 驗證

- [ ] cd cli && uv run pytest -q 不得退化（base 1009 passed，數字自己量不要抄卡面）；python3 scripts/contract_tool_reconcile.py --check rc=0；線上欄位以 gh api graphql 取 Project #4 該欄 options 後與 FIELD_SPECS 自動比對，GitHub 回 5xx 或空結果時標「未取得」並重試，不得以碼側值反推線上值。⚠️ 本卡不驗證 preflight、不驗證任何 --status 收斂、不驗證 iteration 邏輯——全部屬 WF-STATUS-VOCAB-GATE1，此限度須逐字寫進交付物，不得以「狀態已對齊」暗示寫入面已有閘門。
## Log

- 2026-08-18T19:31:19+08:00 open by Claude Opus 5@Claude Code PM；owner 待指派；iteration 0。
- 2026-08-18T19:37:20+08:00 assign by wf-cli → owner Claude Haiku 4.5@Claude Code 子代理；分支worktree claude/WF-STATUS-VOCAB-ALIGN1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-status-vocab-align1；交付狀態 🚧進行中；實際能力層級 經濟型（與卡面建議 經濟型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-18T19:52:39+08:00 amend by wf-cli（op 0d7f69cb）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/project.py", "file:cli/src/wf_cli/commands/handoff_cmd.py", "file:cli/src/wf_cli/commands/assign_cmd.py", "file:AI_WORKFLOW.md", "file:templates/TASKS.md", "file:templates/handoff-contract.md", "file:docs/CONTRACT_TOOL_RECONCILE.md" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/project.py、file:cli/src/wf_cli/commands/handoff_cmd.py、file:cli/src/wf_cli/commands/assign_cmd.py、file:cli/tests/test_commands_mocked.py、file:cli/tests/test_doctor.py、file:cli/tests/test_registry.py、file:AI_WORKFLOW.md、file:templates/TASKS.md、file:templates/handoff-contract.md、file:docs/CONTRACT_TOOL_RECONCILE.md」；理由 補宣告三個測試檔（cli/tests/test_commands_mocked.py、test_doctor.py、test_registry.py）。⚠️ 這是規劃者（PM）開卡時的漏列，不是執行者逸出射程：改動狀態字面必然牽動對這些字面下斷言的測試，開卡時就該宣告。執行者已實際改到它們，本次補正使卡面與寫入集一致，並讓資源互斥閘門看得到真實射程。。
- 2026-08-18T19:56:40+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 0；SHA c4438468825a2bb7e5159f4bf81a41eec6575b6e；證據 執行者交付並經 PM 退回修正一輪。實測：pytest 1009 passed（與 base f207d2e 同）、contract_tool_reconcile.py --check「OK：54 個缺口」、線上 Project #4 交付狀態欄 15 值與 FIELD_SPECS 逐位元組且逐順序相等、git grep 兩個廢止值於 cli/src 只剩 project.py:39 一行、AI_WORKFLOW.md:18 與 templates/TASKS.md:6 兩處皆標「🚧進行中、⏳待執行」為廢止的歷史值、templates/handoff-contract.md:22 的 next_stage 值域已含六個值、§7 已整份重生。⚠️ PM 退回的三件：(1) ⏳待執行 漏標，已補；(2) 逐鍵 diff 缺「移除缺口」類與 55→54 的推導，已補；(3) 執行者原報「範圍外發現：無」但實改 10 檔而卡面宣告 7 檔——三個測試檔的漏列責任在 PM（開卡時未宣告），已 amend 補上（op 0d7f69cb），但執行者未自行察覺逸出，已要求日後交付前以 git diff --name-only 對帳。⚠️ 交付報告的缺口統計用的是 delivery_status 軸的 11→10，不是總數 55→54；兩者都對（軸的 -1 即總數的 -1），但報告未把兩者連起來，查核者請留意口徑。。
- 2026-08-18T20:08:30+08:00 handoff by wf-cli → owner —（結案）；iteration 0；SHA ae8f74162797e2eed7180a1cd1ed6692fab3b6d3；證據 跨家族查核 APPROVE，PR #102 squash 合併為 ae8f741；收尾清理：worktree、本地分支、遠端分支 本來就不存在。
- 2026-08-26T22:24:28+08:00 amend by wf-cli（op 56406215）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:61b28fb3f742d6f73421897bc11f442a122e7505fdc39e701fb47572bc03547c (772 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5327899819 · 2026-08-18T12:04:10Z

```yaml
core_pain_resolved: yes
review_result: APPROVE
findings: []
judgments:
  resource_claims_match_actual_writes: yes
  historical_executor_scope_oversight_requires_finding: no
  historical_executor_scope_oversight_reason: >-
    目前卡面資源宣告與 base..head 實際寫入集已完全一致；三個測試檔的漏列已由
    2026-08-18T19:52:39+08:00 的 amend 補正並在 Log 明確歸責給 planner/PM。
    執行者先前未自覺逸出屬已處置的治理缺失，但本次查核未見殘留不一致，因此不另列 finding。
checks:
  - item: 1
    result: pass
    evidence: >-
      `git merge-base origin/main claude/WF-STATUS-VOCAB-ALIGN1` =
      `f207d2ecf80556d6b90beeb0438bf648288a5fd9`；`gh api graphql` 直取 user
      Project #4 的「交付狀態」options，與 `FIELD_SPECS['交付狀態']` 逐位元組、逐順序比對
      `MATCH True`。線上值共 15 個：`💡需求, 🔬研究中, 🧭規劃中, 📥Backlog, ⏳待執行,
      🔨執行中, 🚧進行中, 🔍待查核, ✅通過, 📦已合併, 🏁完成, ↩退回, ⏸阻塞, 🚨已升級, 🛑已停止`。
  - item: 2
    result: pass
    evidence: >-
      以 fake runner 實跑 `handoff --next-stage requirement|research|planning`，寫入結果分別為
      `💡需求`、`🔬研究中`、`🧭規劃中`；`implementation` 實跑寫入 `🔨執行中`。
  - item: 3
    result: pass
    evidence: >-
      `cli/src/wf_cli/commands/handoff_cmd.py` 的 `STAGE_STATUS` 已改為
      `requirement/research/planning/implementation/review`，不含 `🚧進行中`；
      fake runner 實跑 `assign` 不帶 `--status` 的結果為 `🔨執行中`。
  - item: 4
    result: pass
    evidence: >-
      `AI_WORKFLOW.md:18` 與 `templates/TASKS.md:6` 兩處都明示
      `🚧進行中`、`⏳待執行` 為「廢止的歷史值」；`git grep` 顯示這兩值在 `cli/src`
      只剩 `cli/src/wf_cli/project.py:39` 的 `FIELD_SPECS` 一處。
  - item: 5
    result: pass
    evidence: >-
      `AI_WORKFLOW.md:18` 與 `templates/TASKS.md:6` 的序列一致，且
      `templates/handoff-contract.md:22` 的 `next_stage` 值域為
      `requirement | research | planning | implementation | review | release`，共六值。
  - item: 6
    result: pass
    evidence: >-
      `contract_tool_reconcile --format json` 顯示 `delivery_status/🔨執行中`
      由 base 的 `read-only` 變為 head 的 `ok`；head 的 writers 為
      `cli/src/wf_cli/commands/assign_cmd.py:120` 與
      `cli/src/wf_cli/commands/handoff_cmd.py:91`。
  - item: 7
    result: pass
    evidence: >-
      base/head `--format json` 逐鍵 diff：新增列 3 筆
      (`delivery_status/🔬研究中=ok`, `delivery_status/🧭規劃中=ok`,
      `delivery_status/🚧進行中=read-only`)；移除列 0 筆；verdict 變更 2 筆
      (`delivery_status/💡需求: read-only→ok`, `delivery_status/🔨執行中: read-only→ok`)；
      verdict 未變但 metadata 變動 4 筆
      (`card_field/需求`, `delivery_status/🔍待查核`, `delivery_status/✅已驗證`, `delivery_status/🏁完成`)。
      口徑對帳：delivery_status 軸缺口 11→10；總缺口 55→54，等於 JSON 的
      `gap_count 52→51` 加上 `guard_gaps 3→3`。
  - item: 8
    result: pass
    evidence: >-
      `python3 scripts/contract_tool_reconcile.py --format md` 的輸出，與
      `docs/CONTRACT_TOOL_RECONCILE.md` 自 `<!-- reconcile-dispositions:end -->` 之後的整段
      逐列比對 `MATCH`，未見手補漂移。
self_run:
  - command: >-
      git -C /Users/ruanruan/Dev/ai-workflow fetch --quiet origin main claude/WF-STATUS-VOCAB-ALIGN1 &&
      git -C /Users/ruanruan/Dev/ai-workflow merge-base origin/main claude/WF-STATUS-VOCAB-ALIGN1 &&
      git -C /Users/ruanruan/Dev/ai-workflow diff --name-only
      f207d2ecf80556d6b90beeb0438bf648288a5fd9 c4438468825a2bb7e5159f4bf81a41eec6575b6e
    observed: >-
      merge-base = `f207d2ecf80556d6b90beeb0438bf648288a5fd9`；寫入集 10 檔：
      `AI_WORKFLOW.md`, `cli/src/wf_cli/commands/assign_cmd.py`,
      `cli/src/wf_cli/commands/handoff_cmd.py`, `cli/src/wf_cli/project.py`,
      `cli/tests/test_commands_mocked.py`, `cli/tests/test_doctor.py`,
      `cli/tests/test_registry.py`, `docs/CONTRACT_TOOL_RECONCILE.md`,
      `templates/TASKS.md`, `templates/handoff-contract.md`。
  - command: >-
      python3 - <<'PY' ... gh issue view 101 body + git diff --name-only ... PY
    observed: >-
      Issue #101 的 resource claims 與 base..head 實際寫入集完全一致；
      `missing_from_claim=[]`, `extra_in_claim=[]`。
  - command: >-
      gh api graphql -f query='query { user(login:"ruan6047") { projectV2(number: 4) { fields(first: 50) { nodes { ... on ProjectV2SingleSelectField { name options { name } } } } } } }'
    observed: >-
      成功取得線上 Project #4 欄位；「交付狀態」options 與 `FIELD_SPECS` 比對 `MATCH True`。
  - command: cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-status-vocab-align1/cli && uv run pytest -q
    observed: 1009 passed in 123.65s (0:02:03)
  - command: >-
      BASE_DIR=$(mktemp -d /private/tmp/align1-base.XXXXXX) &&
      git -C /Users/ruanruan/Dev/ai-workflow worktree add --quiet --detach "$BASE_DIR"
      f207d2ecf80556d6b90beeb0438bf648288a5fd9 &&
      cd "$BASE_DIR"/cli && uv run pytest -q
    observed: 1009 passed in 130.38s (0:02:10)
  - command: cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-status-vocab-align1 && python3 scripts/contract_tool_reconcile.py --check
    observed: '[reconcile] OK：54 個缺口全部有登記處置，判定一致。'
  - command: >-
      cd "$BASE_DIR" && python3 scripts/contract_tool_reconcile.py --check
      (於 detached base worktree `f207d2ecf80556d6b90beeb0438bf648288a5fd9`)
    observed: '[reconcile] OK：55 個缺口全部有登記處置，判定一致。'
  - command: >-
      cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-status-vocab-align1 &&
      python3 scripts/contract_tool_reconcile.py --format json > align1-head.json &&
      python3 scripts/contract_tool_reconcile.py --format md > align1-head.md
    observed: >-
      產出 head JSON/MD；JSON 顯示 `symbol_count=82`, `gap_count=51`, `guard_gaps=3`。
  - command: >-
      cd "$BASE_DIR" && python3 scripts/contract_tool_reconcile.py --format json > align1-base.json &&
      python3 scripts/contract_tool_reconcile.py --format md > align1-base.md
      (於 detached base worktree `f207d2ecf80556d6b90beeb0438bf648288a5fd9`)
    observed: >-
      產出 base JSON/MD；JSON 顯示 `symbol_count=79`, `gap_count=52`, `guard_gaps=3`。
  - command: >-
      cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-status-vocab-align1/cli &&
      uv run python - <<'PY' ... fake runner exercise for handoff/assign statuses ... PY
    observed: >-
      `handoff --next-stage requirement/research/planning/implementation` 實跑結果依序寫成
      `💡需求 / 🔬研究中 / 🧭規劃中 / 🔨執行中`；`assign` 預設寫入 `🔨執行中`。
  - command: >-
      cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-status-vocab-align1 &&
      git grep -n '🚧進行中' -- cli/src && git grep -n '⏳待執行' -- cli/src
    observed: >-
      兩值在 `cli/src` 都只剩 `cli/src/wf_cli/project.py:39` 的 `FIELD_SPECS` 命中。
  - command: >-
      python3 - <<'PY' ... compare align1-head.md with docs/CONTRACT_TOOL_RECONCILE.md tail after
      <!-- reconcile-dispositions:end --> ... PY
    observed: MATCH
```

