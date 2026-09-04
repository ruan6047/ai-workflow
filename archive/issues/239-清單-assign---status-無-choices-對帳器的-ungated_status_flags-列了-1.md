# #239 [清單] assign --status 無 choices：對帳器的 ungated_status_flags 列了 15 天而承接卡已撤
- state: open  created: 2026-09-02T12:12:11Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/239
- comments: 0

## Body

### 出處可指

`scripts/contract_tool_reconcile.py:903` 的 `ungated_status_flags`（今日實跑輸出見下）；`cli/src/wf_cli/commands/assign_cmd.py:120`（旗標定義）與 `:303`（寫入點）；`docs/CONTRACT_TOOL_RECONCILE.md:135`。

### 是觀察不是結論

**對帳器今日（2026-09-02）實跑**：

```bash
python3 scripts/contract_tool_reconcile.py --format json | \
  python3 -c "import json,sys;d=json.load(sys.stdin);..."   # 取 ungated_status_flags
```

輸出逐字：

```
ungated_status_flags = ['assign_cmd.py --status（預設 🔨執行中，無 choices）']
```

⇒ **恰好一項，且該項自 2026-08-18 起即在清單上。**

**碼側逐字**：`assign_cmd.py:120` 為 `p.add_argument("--status", default="🔨執行中", help="assign 後的交付狀態；預設 🔨執行中")`——**⛔ 無 `choices`**；`:303` 為 `set_field_value(runner, project, item.item_id, fields["交付狀態"], args.status)`——**直接寫入，⛔ 無值域檢查**。`TERMINAL_STATUSES`（`:89`）只用於 `:233` 檢查**別的卡**是否終態，⛔ 不驗本次要寫的值。

⇒ `wfcli assign <卡> --status 🏁完成 …` 可把任何卡直接設為完成，繞過 `AI_WORKFLOW.md:187` 逐字「**結案不是任何角色可直接設定的值**，是 CLI 清理成功後自身寫下的結果」。

**已登記且有機械追蹤，但無人承接**：

- `ruan6047/ai-workflow#103`（`WF-STATUS-VOCAB-GATE1`）痛點逐字已載：「第二個口：**`assign --status` 自由文字、無 `choices`，射程等於線上欄位當下全部選項，含 `🚨已升級` 與 `📦已合併`——契約規定的 escalation checkpoint 與 merge 收尾前提機械上可繞過**」。該卡**2026-08-18 撤卡**（Log 逐字「撤卡（2026-08-18）：開卡後五輪規劃期研究推翻本卡的問題陳述」），⇒ 該口**未交付**。
- `ruan6047/ai-workflow#101`（`WF-STATUS-VOCAB-ALIGN1`，已關閉）交付的是**狀態詞彙與落點對齊**，⛔ 未涵蓋本項。
- `docs/CONTRACT_TOOL_RECONCILE.md:135` 逐字：「對帳器現在把這類逃生口用 `ungated_status_flags` **機械列在報告開頭，不靠散文記得**」⇒ 告警存在且每次跑都印。

⇒ 可觀測現象：**一個機械告警在報告開頭連續列了 15 天（2026-08-18 → 2026-09-02），而承接它的卡已撤、⛔ 無其他卡接手。**

**與 `WF-REDESIGN-W3`（`#221`）的關係**：該卡驗收 8 承接 canonical `AI_WORKFLOW.md:274` row #4 的同形問題，但其射程**逐字只含 `cli/src/wf_cli/commands/handoff_cmd.py`**（需求方 2026-09-01 註記之三 `issuecomment-5492051143`）。⇒ 該卡交付後，`assign` 側**仍不成立**；PM 已於 `issuecomment-5508136680` §四登記⛔ 不自行擴張。

### 查重留痕

已跑（`gh issue list --repo ruan6047/ai-workflow --state all --search <關鍵字>`）：

```bash
gh issue list --repo ruan6047/ai-workflow --state all --search "assign --status"
gh issue list --repo ruan6047/ai-workflow --state all --search "逃生門"
gh issue list --repo ruan6047/ai-workflow --state all --search "結案 直接設定"
gh issue list --repo ruan6047/ai-workflow --state all --search "WF-STATUS-VOCAB-ALIGN1"
```

命中：`#103`（已撤卡，見上）／`#101`（已關閉，射程不同）／`#221`（射程只含 `handoff_cmd.py`）／`#57`／`#84`／`#16`／`#42`／`#238`／`#119`／`#159`／`#87`。逐一核對：`#57` 對象為 worktree 建錯 repo；`#84` 為 release 同步 Projects Status；`#42` 為事件型別列舉；`#119`／`#159`／`#87` 分別為 canonical 同步、file:line 指標、資源詞彙 token。**⛔ 無任何一張以本項為痛點且仍在活。**

### 屬哪個 repo

ai-workflow

### 提案者身分

- GitHub 帳號：`ruan6047`（本 issue 的 author 欄即為此帳號，可核）
- session ID：`cc0a7952-07a5-4978-8d03-8b5f48fbc690`（PM session，Claude Code，模型 `claude-fable-5`）
- 該則訊息定位：本項由該 session 於 2026-09-02 處理 `#221` 的執行階段交接時量到；`#103` 的既有登記係於本項建立前的查重步驟中發現（⇒ 本項**⛔ 非新發現**，是既有登記的重新承接）。transcript 於需求方本機 `~/.claude/projects/-Users-ruanruan-Dev-cpbl-analytics--claude-worktrees-workflow-review-optimization-33882b/` 可核。

---

⚠️ **提案者即 PM**：由需求方於同 session 逐字裁定「不要硬合」後建立。收件閘的「提案者≠肇因者」成立、「提案者≠收件者」不成立 ⇒ 由需求方決定是否補一次第二 PM 收件裁決。

> ⛔ 本項不配卡ID、⛔ 不掛成任何卡的 sub-issue、⛔ 不進 Project #4；升級走 `wfcli open --from-issue <本 URL>`。

