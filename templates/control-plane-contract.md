# Control-plane Contract — <專案名>

> 共同不變量見 canonical `AI_WORKFLOW.md` §4.1、§4.3、§4.4。本檔定義該專案如何把協作狀態與本機資源鎖分離；不得填入 token、secret 或使用者個資。

## 1. Adapter 邊界

| 範圍 | 實作 | 事實來源／用途 |
|---|---|---|
| Remote coordination（GitHub 預設） | <Issue／Project #<n>／Actions workflow> | 唯一 lifecycle writer：跨人 task、review、lease、CI 與協作事件 |
| **狀態寫入通道** | <祕書 CLI 指令；canonical §4.3 要求唯一通道> | 繞過它的狀態寫入（含看板 UI 手改欄位）即違規 |
| Local resource | <原子目錄鎖／OS lock／container runtime> | worktree、port、container、未提交變更的暫時互斥；只回報 telemetry，不改 card state |
| Event store | <Issue timeline ＋結構化 comment／受保護 Git history／外部 append-only store> | 事件歷史；採 Issue timeline 時必須有定期 snapshot export 作離線稽核副本 |
| Ledger projection | <產生方式與位置；cutover 後＝snapshot 產生，不手改> | 活卡 current-state 顯示；不得手改 |
| **封存的舊狀態面** | <舊 event log／Ledger 路徑與終筆 SHA；已 cutover 才填> | 唯讀，不得再追加或重建 |

## 2. Event schema 與狀態

```yaml
event_id: <UUID/monotonic ID>
card_id: <CARD_ID>
type: claim | handoff | handoff-accepted | contract-baseline | preflight-failed | review | review-invalid | review-correction | escalation-epoch-change | escalation-checkpoint | status-change | correction | merge | release
actor: <GitHub account / model@tool>
occurred_at: <ISO 8601>
state_version: <strictly increasing integer>
iteration: <integer>
source_sha: <required for review/handoff/merge/release>
evidence: <PR, CI, test or decision link>
```

review preflight／退回／升級另依 [`review-escalation.md`](review-escalation.md) 實作
`attempt_id`、`escalation_epoch`、結構化 findings 與 `counts_toward_escalation`；不得把所有
`REJECT` event 直接視為一次升級計數。專案可擴充 event type，但必須文件化狀態轉移，
不得將未識別 type 默默當成 review attempt。

local telemetry 另以同一 envelope 記錄 `resource-acquired | resource-released`，但必填 `lifecycle: false`、`claim_event_id`，且不得填 `state_version` 或改 card state。

**允許的狀態轉移、Gate／preflight 退回、`⏸阻塞` 的 TTL、escalation checkpoint 與
`🚨已升級` 的決策 owner 由下方 §2.1 定義（canonical 本體，⛔ 不下放）。** 採用專案在此
**只宣告與 §2.1 的差異**，且每條差異必須指名它由**哪一行程式或哪一位角色**執行：

<專案差異；⛔ 不得留空、⛔ 不得留本佔位符原樣——無差異時逐字寫「無差異」>

> (a) **刻意保留這個位置、只換掉它的語意，而不是刪掉它。**
> (b) 為什麼：刪掉等於宣稱「專案不可能有差異」，那是假的——部署軸適不適用、哪些 CLI 入口
> 有副作用、維護階段用不用得到，逐專案都不同（canonical `AI_WORKFLOW.md` §7 的委派表列的
> 正是這幾項）。改成差異宣告則保留了表達力，又不要求任何人憑空重寫一整張表。
> (c) ⛔ **不得由此推出**「專案可以在這裡改寫 §2.1 的任何一列」——差異宣告的作用是**記下
> 不一致並指名執行者**，不是就地立法；改 §2.1 本體要回 canonical 改。
>
> ⛔ **不留空的理由**是形狀性的，不是禮貌：空白與「還沒想過」在事後長得一模一樣，而這兩者
> 的處置完全不同（同一形狀的既有判例見 `cli/src/wf_cli/commands/handoff_cmd.py` 的
> `PHASE_UNDECIDABLE_MARK`：「⛔ 不留白：留白與『這個欄位還沒上線』在事後長得一模一樣」）。

### 2.1 允許的狀態轉移（canonical 本體；採用專案**引用不複製**）

> **歸屬裁定**（`WF-TRANSITION-TABLE-UNWRITTEN1`，`ruan6047/ai-workflow#122`，2026-08-26）：
> 本表**上收 canonical**——⛔ 不留在 `<專案實作>`，⛔ 也不採「canonical 定通則＋專案宣告
> 差異」的兩層制。理由見下方四點；代價見「代價，不掩飾」。
>
> ⚠️ **採用專案建立自己的 `CONTROL_PLANE_CONTRACT.md` 時，本節請以連結引用，⛔ 不複製全文**
> ——形狀比照 canonical §7「專案只保留指向本檔的 stub，不複製全文」。複製即產生第二份會漂移
> 的權威，那正是本節要治的病。

> ⚠️ **本節刻意不把 mention-only、not-established、deploy-state 這類字串放進獨立反引號**
> （⭐ 上一句自己也沒放，理由同下——本註解的初稿放了，於是它一寫下去就把 `--check` 弄紅）。
> (a) 刻意如此，⛔ 不是排版失誤。
> (b) 為什麼：`scripts/contract_tool_reconcile.py` 的 `_KEBAB_IN_BACKTICKS` 以**詞法**導出契約
> 的事件型別 universe——判準是「整段反引號恰好是一個 kebab token」。散文裡順手加一對反引號，
> 那個字串就會被判成「契約宣告了一個事件型別」而長出一個假缺口，使 `--check` 轉紅（本節初稿
> 實際觸發過五個，缺口數由 59 變成 64）。形狀同源於 `cli/src/wf_cli/pitfalls.py` 那段
> 「刻意不列舉交付狀態的字面值」的既有註解。
> (c) ⛔ **不得由此推出**「本節提到的每個帶連字號的詞都不是事件型別」——`preflight-failed`、
> `escalation-resolution`、`handoff-accepted` 三個**是**，故仍以反引號書寫；⛔ 也不得推出
> 「對帳器的過度抽取是缺陷」，那是它明文選擇的取捨（見 `docs/CONTRACT_TOOL_RECONCILE.md` §2）。

#### 為什麼不下放（直接回應「一個看板服務兩個 repo」）

1. **看板是一個、repo 是兩個，這是量得出來的。** 2026-08-26 的版控快照（`origin/snapshots`
   `413bd4d`，`snapshots/2026-08-26/snapshot.json`，`generated_at` 為 `2026-08-26T10:40:12+08:00`）
   共 **202 張卡**，依 `issue_url` 分屬 `ruan6047/cpbl-analytics` **117**、`ruan6047/ai-workflow`
   **84**，另 **1** 張 DraftIssue 無 Issue URL。⇒ 一張共用看板不可能有兩份互相獨立的「允許的
   狀態轉移」表，而 `<專案實作>` 佔位符預設它可以。

2. **唯一寫入通道也只有一份，而且它住在 canonical repo。** canonical §4.3 明訂狀態寫入的
   唯一通道＝祕書 CLI（`ruan6047/ai-workflow` 的 `cli/` 之 `wfcli`），§7.1 明訂「規則與祕書 CLI 住本
   repo（跨專案共用資產）」。轉移能不能發生，今天是由 `wfcli` 的分支決定的 ⇒ **執行者已經
   在 canonical repo 裡**。把規則寫在專案側會造成「條文在 A、執行者在 B」，而那正是
   `handoff_cmd.py` 逐字治過的病：「**先有條文才有這段碼**——讓工具執行 canonical 沒說的規則，
   正是 `WF-BACKLOG-STAGE1` 要治的病，重演一次即是回歸」。

3. **canonical §7 的委派表本來就沒有列狀態轉移。** `AI_WORKFLOW.md` §7 給
   `CONTROL_PLANE_CONTRACT.md` 的專案自決範圍逐字是「狀態面目標（repo／Project）、**哪些 CLI
   入口屬破壞性須驗 lease**、**當前仍有副作用的 CLI 入口清單**、資源宣告詞彙」——⛔ 四項裡
   沒有狀態轉移。⇒ 本檔原 §2 的佔位符與 §7 的委派表**互相矛盾**，而矛盾的一方是佔位符。

4. **下放已經實測失敗，而失敗的機制已經被寫下來了。** canonical §6.4 逐字：「該前例是警告：
   同檔的『允許的狀態轉移』下放後**兩個專案都從未填過**（`aiwf#122` 為此而開且至今 OPEN）……
   ⇒ **下放不落空的條件是『可自動產生』，不是『有佔位符』**」。狀態轉移表**產不出來**（它要人
   憑空寫）⇒ 條件不成立。實查佐證：`cpbl-analytics/docs/CONTROL_PLANE_CONTRACT.md`（220 行，
   @ `3b470d70`）對 `轉移`／`⏸阻塞`／`📥Backlog`／`規劃中` 四個關鍵詞命中**全部是 0**；
   `ruan6047/ai-workflow` **根本沒有**這個檔。

#### 代價，不掩飾

上收讓兩個專案失去「宣告自己不同」的**預設**位置。處置是上方的差異宣告：⛔ 不是取消該位置，
是把它從**空白佔位符**改成**必須非空、且必須指名執行者**的差異宣告。

⭐ **本表不關任何一個口。** 它產出的是一張說得出合法性的表；把口關上屬各 `WF-CLI-*` 動詞卡，
本表是它們的**輸入**（需求方 2026-08-22 裁定 1 已明示並接受此代價）。

#### 兩軸不可合讀 ⭐

2026-08-26 起 `handoff` 的 Log 行開始記**階段**（`handoff_cmd.py` 的 `PHASE_LOG_LABEL`；行形狀
為 `…；階段 <離開側>；踩坑回應 N 族（…）；證據 …`）。⛔ **那不是交付狀態，兩者是不同的軸。**

| | 軸一：**階段** | 軸二：**交付狀態** | 軸三：**部署狀態** |
|---|---|---|---|
| 值域 | 7（canonical §0.1） | 15（`project.FIELD_SPECS`） | 7 |
| 寫入者 | `open`（恆「需求」）、`handoff`（`STAGE_PHASE` 六鍵；⛔ `backlog` 刻意不在表內） | `open`／`assign`／`handoff`／`review` **四個呼叫點**（`set_field_value` 全域窮舉） | `wfcli deploy-declare`／`wfcli deploy-state` |
| Log 行記不記 | ✅ 記，且記的是**離開側** | ⛔ **不記** | ✅ 記（Issue timeline 逐字 `transition: A → B`） |
| 事後可否由留痕反推 | 可反推**離開側**階段 | ⛔ **反推不出** | ✅ 可 |
| 轉移是否受檢查 | ⛔ 無（階段欄跟著 `--next-stage` 走，不驗前身） | 逐列見表一（多數為 ⛔ 無） | ✅ **只准相鄰前進**（`DEPLOYMENT_TRANSITIONS`；`deploy_state_cmd.py` 的 `expected != args.to` → `rc=4`） |

⇒ **「階段已可反推」⛔ 不蘊含「狀態轉移已可重建」。** 兩者記的東西不同、方向相反：Log 記的是
**離開側**階段，而本次寫入的是**進入側**狀態，兩者不互推（`handoff_cmd.py` 的 `PHASE_LOG_LABEL`
上方註解逐字給了兩個理由）。因此 `doctor.UNDECIDABLE_HANDOFF`（值 `handoff_status_not_in_log`）
在 `aiwf#148` 之後**判定未變**。

⭐ **三軸裡只有軸三「有一張表、而且那張表真的被執行」**，形狀值得照抄：轉移表是碼裡的一個
`dict`，而閘門逐字比對 `DEPLOYMENT_TRANSITIONS.get(current) != args.to` 即拒絕。軸二今天沒有
這樣的 `dict`——⛔ 本表**不是**那個 `dict`，它是條文；把它變成碼屬 `WF-CLI-*` 動詞卡。

**2026-08-26 現場量測**（唯讀；走 `wfcli` 自己的讀取路徑 `project.list_items` ＋
`doctor.audit_state_face_drift_batch`，常數由 `import` 取得而非手打，⛔ 未呼叫任何寫入動詞）：

| 量 | 值 |
|---|---:|
| 有卡 ID 的 item | 204 |
| `undecidable`／`drift`／`consistent` | 185／13／6 |
| 其中 `handoff_status_not_in_log` | **172** |
| Project `階段` 欄有值 | 17（空值 187） |
| 卡面 Log 含 `；階段 ` 字面 | **3** |

⚠️ **最後兩列是那個「新事實」的實際覆蓋率。** `；階段` 2026-08-26 才上線 ⇒ 任何以它為輸入的
檢查在**既有卡上回放幾乎全滅**，只能對新卡生效，且須先釘一個界線（形狀比照
`pitfalls.PITFALL_GATE_EPOCH` 與 `doctor.STATE_FACE_DRIFT_EPOCH`）。
⛔ **不得由「Log 已記階段」推出「現在就可以據它做檢查」。**

#### 表一：交付狀態的允許轉移

**讀法**：`唯一合法動詞` 欄寫 ⛔ 無動詞者，表示今天只有自由文字逃生門寫得進去（第 17 列）。
⭐ **`機械執行者` 欄的每一格都指得出是哪一段程式在檢查，或明說沒有**——這是本表的紅線（`docs/ROADMAP.md`
§1：沒有執行者的偵測器不算達成目標 1）。⛔ 沒有「大概有檢查」這種值。

> ⚠️ **「機械執行者」欄刻意以「檔名＋符號或運算式」指認，⛔ 不寫行號。**
> (a) 刻意如此。
> (b) 為什麼：canonical `AI_WORKFLOW.md` §0.1 已經吃過這個虧並逐字記下來——「原文寫的
> `:511`／`:513` 今日已分別指到 `:532`／`:535`，⛔ 而宣稱本身仍成立 ⇒ **腐爛的是引用形態不是
> 判斷**」。本表的壽命以年計，行號的壽命以次計。
> (c) ⛔ **不得由此推出「這一欄不可複驗」**：每一格寫的都是可以 `grep` 到唯一命中的字面
> （符號名或該行的實際運算式），複驗方式是拿它去搜、看它落在哪個分支上；⛔ 也不得推出
> 「指不出行號＝沒有執行者」——那一欄裡沒有執行者的格子一律逐字寫「⛔ **無**」。

| # | 從 → 到 | 唯一合法動詞 | 前提檢查 | 機械執行者（指到符號） | 誠實邊界 |
|---:|---|---|---|---|---|
| 1 | （無）→ `💡需求` | `wfcli open` | ⛔ 無（新卡無前身） | ⚠️ 有的是**單一寫入路徑**不是前提檢查：值來自 `card.py` 的 dataclass 預設 `delivery_status: str = "💡需求"`，`open` 無 `--status` 旋鈕（`open_cmd.py` 的 `values["交付狀態"] = card.delivery_status`） | 「寫不出別的值」**只對 `open` 這個入口成立**；卡開完的下一秒 `assign --status`／`handoff --status` 就能改成任何 Project 既有選項 |
| 1b | 任意 → `💡需求`（**退回需求方裁決**） | `handoff --next-stage requirement` | ⛔ 無 | ⛔ **無**：與第 2、3、6、7 列同一個 `else: new_status = STAGE_STATUS[args.next_stage]`，**不讀現值** | ⭐ 這條真的被走過——本卡自己 2026-08-22 即以此被退回（Log 逐字「退回 💡需求」）。⚠️ 它可以**跨階退回**（canonical §0.1 舉的 `cpbl#162` 逐字「退回需求方裁決」跨三階），⛔ 而留痕不記進入側狀態 ⇒ 事後看不出退到哪一格 |
| 2 | 任意 → `🔬研究中` | `handoff --next-stage research` | ⛔ 無 | ⛔ **無**：`handoff_cmd.run` 末尾的 `else: new_status = STAGE_STATUS[args.next_stage]`，**不讀現值** | 需求方 2026-08-22「高複雜或影響較大的卡必跑 `🔬研究中`」在此**無執行者**，見表六第 1 列 |
| 3 | 任意 → `🧭規劃中` | `handoff --next-stage planning` | ⛔ 無 | ⛔ **無**：同上 `else` 分支 | canonical §3 的三個 Gate（Discovery／Design／Plan）今天**都沒有動詞** ⇒ 轉進這一格⛔ 不蘊含任何 Gate 事實 |
| 4 | `🧭規劃中` → `📥Backlog`（**T2／T3／T4，及級別讀不到／為空／語彙外者**） | `handoff --next-stage backlog` | ✅ 當下交付狀態必須逐字為 `🧭規劃中`（`BACKLOG_REQUIRED_PRIOR_STATUS`） | ✅ **有**：`handoff_cmd.py` 的 `if current_status != BACKLOG_REQUIRED_PRIOR_STATUS:` → `return 4` | ⛔ 只證明**狀態面說**它來自規劃，不證明規劃做過（`🧭規劃中` 本身也寫得進 `--status`）；且它**管不住級別本身**——`amend --tier` 改成 T1 就掉到第 5 列 |
| 5 | 任意 → `📥Backlog`（**T0／T1**） | 同上 | ⛔ **無，而且是刻意的** | ⛔ **無**：`handoff_cmd.py` 的 `if tier in BACKLOG_GATE_EXEMPT_TIERS:` 直通分支，只往 stderr 印一行「**本次未做任何前身狀態檢查**」 | (a) 刻意如此 (b) canonical §3.1 的表**沒有 T0／T1 的列**，沒有條文就沒有可執行的前提，硬編一個等於工具自己立法 (c) ⛔ 不得由「這個動詞成功了」推出這張 T0／T1 卡走過規劃 |
| 6 | 任意 → `🔨執行中` | `assign`（`--status` 預設 `🔨執行中`）／`handoff --next-stage implementation` | ⛔ 無 | ⛔ **無**：`assign_cmd.py` 的 `set_field_value(..., fields["交付狀態"], args.status)` 無條件寫；`handoff` 走同一個 `else` 分支 | ⭐ **含終態**：`🏁完成`／`🛑已停止` 的卡也拉得回來，見第 16 列 |
| 7 | 任意 → `🔍待查核` | `handoff --next-stage review` | ⛔ 無 | ⛔ **無**：同 `else` 分支 | canonical §3 的 review preflight（不符時寫 `preflight-failed`、⛔ 不得派 reviewer）**無 writer**；該事件型別在 `docs/CONTRACT_TOOL_RECONCILE.md` 的登記表判 「mention-only」 |
| 8 | `🔍待查核` → `✅通過` | `wfcli review --review-result APPROVE` | ⚠️ **只警示不擋** | ⚠️ `review_cmd.py` 的 `if current_status != AWAITING_REVIEW_STATUS:` 只 `print(... file=sys.stderr)` 後**照寫**（該處註解逐字「不硬擋」）。⛔ 這一格**沒有**前身閘門 | 真正 fail-closed 的是**別的東西**：`attempt_id` 去重（`validation.check_attempt_not_duplicated`）與 checkpoint 閘門（表四）。⛔ 不得把它們讀成前身狀態檢查 |
| 9 | `🔍待查核` → `↩退回` | `wfcli review --review-result REQUEST_CHANGES` | 同上 | 同上；值由 `review.py` 的 `STATUS_BY_RESULT` 決定 | 同上 |
| 10 | `↩退回` → `🔨執行中`（iteration + 1） | `handoff --next-stage implementation` | ⛔ 無 | ⛔ **無前身檢查**；iteration 遞增在 `handoff_cmd.py` 的 `elif args.next_stage == "implementation": new_iteration = current_iteration + 1` 是**無條件**的，⛔ 不驗現值是否為 `↩退回` | ⇒ 從任何狀態下 `--next-stage implementation` 都會 +1。⛔ **不得由「iteration 高」推出「被退回過那麼多次」** |
| 11 | `✅通過` → `📦已合併` | ⛔ **無動詞** | — | ⛔ **無** | 只有 `assign --status`／`handoff --status` 寫得進去。canonical §4.4 明訂「現役的定義含 `📦已合併`」「停在 `📦已合併` 不收尾＝假活卡」，而**它是怎麼被寫進去的，工具帳上分不出來**（若是看板 UI 直接改欄位即違反 §4.3 紅線）——已登記於 `docs/CONTRACT_TOOL_RECONCILE.md` §4.1，待需求方裁定 |
| 12 | `📦已合併` → `🏁完成` | `handoff --next-stage release --cleanup --repo-path <路徑>` | ✅ 兩道，⚠️ **但都不是前身狀態檢查** | ✅ (a) 部署閘門：`handoff_cmd.py` 的 `if deployment_status not in (None, "—不適用", "✅已驗證"): ... return 4`；(b) 收尾守衛：終態由 `cleanup.execute_closeout_transition` 在清理**確實完成後**才呼叫 `write_release_terminal` ⇒「終態先於清理」在這條路徑上**寫不出來**（`_CallbackEffectWriter` 的 docstring 逐字：不是靠呼叫端自律） | ⛔ **不檢查前身是否為 `📦已合併`**——任何狀態都 release 得出去。另有兩分支契約：帶 `--repo-path` 卻不帶 `--cleanup` 一律 `rc=2`（`REPO_PATH_WITHOUT_CLEANUP_REFUSAL`）；不帶 `--repo-path` 則放行並把「收尾清理未執行」寫進 Log（`NO_REPO_PATH_TRACE_SUFFIX`） |
| 13 | 任意 → `⏸阻塞` | ⛔ **無動詞** | — | ⛔ **無** | 只有 `--status` 自由文字。canonical §5 末段要求「`⏸阻塞` 必填 owner、原因、等待對象與解除條件」——⛔ **那四個必填今天沒有任何地方可以驗**，因為沒有專責動詞。TTL 見表三 |
| 13b | 任意 → `🛑已停止`（撤卡／停止） | ⛔ **無動詞** | — | ⛔ **無** | 只有 `--status` 自由文字。canonical §0 逐字「`🛑已停止` **必填決策與原因後封存**」——⛔ 那兩個必填一樣沒有地方可以驗。⚠️ 它是 `TERMINAL_STATUSES` 的成員 ⇒ 一旦寫入，`assign` 的資源交集檢查會把這張卡**整張跳過**（`for other in items:` 迴圈裡的 `continue`），它宣告的資源即刻視為釋放 |
| 14 | 任意 → `🚨已升級` | ⛔ **無動詞** | — | ⛔ **無** | `checkpoint --decision escalate` **不改交付狀態**，只印一行提示要人手打 `handoff --status 🚨已升級`（`checkpoint_cmd.py` 逐字：「本指令不改交付狀態」）⇒ **「該不該升級」與「卡真的變成已升級」之間沒有機械連線** |
| 15 | `🚨已升級` → `🔨執行中`（解除） | ⛔ **無動詞** | — | ⛔ **無** | `escalation-resolution` 是 `templates/review-escalation.md` §4 已裁定的**獨立事件型別**，其 writer **未實作**（`validation.validate_checkpoint_input` 對 `escalation_resolution` 鍵 fail-closed 拒收並逐字說明）。⇒ 在它落地前，事件流上該區間**恆為升級中** |
| 16 | `🏁完成`／`🛑已停止` → `🔨執行中`（**終態被拉回**） | `assign` | ⛔ **無** | ⛔ **無**：`TERMINAL_STATUSES`（`assign_cmd.py`）只在資源交集迴圈 `for other in items:` 裡的 `if (other.delivery_status or "") in TERMINAL_STATUSES: continue` 被讀——那是在掃**別張卡**。**本卡自己的終態一個字都不讀** ⇒ `rc=0`、無警告 | Discovery 實驗 F（2026-08-22）。⛔ 本卡不修（非射程），承接者未指名，見表六第 3 列 |
| 17 | 任意 → 任意（**逃生門**） | `handoff --status <自由文字>`／`assign --status <自由文字>` | ⛔ 無 | ⛔ **無**：兩處 `--status` 皆**無 `choices`**；且 `handoff_cmd.run` 的 `if args.status:` 分支排在**所有**閘門之前 ⇒ 給了它，部署閘門與 Backlog 前身閘門**一條都不跑** | 唯一的實際約束來自平台：`project.set_field_value` 要求該值是 Project 上既有的 SINGLE_SELECT 選項 ⇒ 寫得進去的是那 15 個值，⛔ 不是任意字串。收斂 `--status` 成 `choices` 已登記於 `docs/CONTRACT_TOOL_RECONCILE.md` §4.1，⛔ 不在本表射程 |
| 18 | 任意 → `⏳待執行`／`🚧進行中`（**廢止值**） | `--status` 自由文字 | ⛔ 無 | ⛔ **無** | canonical §0 逐字「新寫入不得用」，而兩個值仍在 `project.FIELD_SPECS` 的選項列舉裡 ⇒ `--status` 寫得進去。⚠️ SINGLE_SELECT 的選項一經建立，`ensure_fields` 對已存在欄位「原樣保留」⇒ **移不掉**，只能靠條文 |

> (a) **第 18 列刻意保留在表內，而它描述的是一個被禁止的轉移。**
> (b) 為什麼：本表若只列「允許的」，讀者無從分辨「沒列到」與「列了但擋不住」。第 11、13、13b、
> 14、15、16、17、18 這八列全是**寫得出來但沒有執行者**的格子——它們不在表內，這張表就會
> 變成「看起來完備」的東西。
> (c) ⛔ **不得由「它在表內」推出「它是合法轉移」**：合法性看「唯一合法動詞」欄，執行力看
> 「機械執行者」欄，兩欄各自獨立。

> ⭐ **表一的窮舉性是跑出來的，⛔ 不是人工宣稱的。** 值域由 `import` 取得而非手打；
> 複驗（2026-08-26 實跑，結果為「未涵蓋 0 個狀態、0 個 next-stage」）：
>
> ```bash
> python3 - <<'EOF'
> import re, sys, pathlib
> sys.path.insert(0, "cli/src")
> from wf_cli.project import FIELD_SPECS
> doc = pathlib.Path("templates/control-plane-contract.md").read_text(encoding="utf-8")
> # 標題以行首錨定：本區塊自己也寫了「表一／表二」字樣，但它們前面有 `> `，
> # 故不是行首命中 ⇒ 自指不會把切片截斷。⭐ 自指命中是可見的，⛔ 不是被偷偷排除的。
> lo = re.search(r'(?m)^#### 表一：', doc).start()
> hi = re.search(r'(?m)^#### 表二：', doc).start()
> t = doc[lo:hi]
> print("未涵蓋的狀態:", [x for x in FIELD_SPECS["交付狀態"][1] if x not in t])
> print("未涵蓋的 next-stage:", [g for g in
>       ("requirement","research","planning","backlog","implementation","review","release")
>       if f"--next-stage {g}" not in t])
> EOF
> ```
>
> ⛔ **不得由「窮舉」推出「完備」**：本表窮舉的是**值域**（每個狀態至少出現在一列），
> ⛔ 不是**狀態對**（15×15 的組合）。後者絕大多數今天由第 17 列那一格逃生門統包，
> 逐對展開只會得到 200 多列同樣寫著「⛔ 無」的東西。

#### 表二：Gate／preflight 退回

| Gate／退回點 | canonical 出處 | 動詞／事件 | 機械執行者（指到符號） |
|---|---|---|---|
| Discovery Gate | §3、§3.1 | ⛔ 無 | ⛔ **無** |
| Design Gate | §3 | ⛔ 無 | ⛔ **無，而且連記錄的地方都沒有**：卡面 `Design` 區塊在 `docs/CONTRACT_TOOL_RECONCILE.md` 的卡面欄位表判 `absent`（open 渲染=否、amend 可改=否） |
| Plan Gate／spec 基線 | §3 | `wfcli contract-baseline` | ⚠️ **部分**：`checkpoint_cmd.run_contract_baseline` 的 `if history.baseline_count:` → `return 2`（one-shot cutover，`review-escalation.md:276`）。⛔ 它擋的是**重複 baseline**，不是「Plan 有沒有做」 |
| 規劃閘門三級制 T3 的「需求方批註放行」 | §3.1 | ⛔ 無 | ⛔ **無，且刻意不做**：`docs/ROADMAP.md` §1——本 repo 全部角色共用同一個 GitHub 帳號 `ruan6047`，該節逐字禁止「寫看起來在驗證身分、實際恆真的條文」 |
| 進 `📥Backlog` 的前身狀態 | §3.1 | `handoff --next-stage backlog` | ✅ **有**（T2 以上）：見表一第 4 列。⛔ T0／T1 無：見表一第 5 列 |
| review preflight | §3、`review-escalation.md` §3 第 1 款 | `preflight-failed` 事件 | ⛔ **無 writer，且今天結構上不可能有**：`validation.derive_preflight_basis` **恆回** `PREFLIGHT_NOT_ESTABLISHED`（該函式 docstring 逐字寫明本 repo 今天恆為 not-established），成因是沒有受管轄的 preflight pass event writer，且本 repo 唯一可能的通道訊號（留言 author）**無鑑別力**——全部角色共用同一帳號。恆虛性以 `preflight_basis_binding: structurally-unavailable` 加蓋進事件而非拒寫 |
| 踩坑族清冊「離開閘門」 | §6.4 | `handoff --pitfall-report` | ✅ **有**：`handoff_cmd.run` 的 `gate = _pitfall_gate(...)` → `if gate.rc != 0: return gate.rc`，且該行之前**零寫入**（由 `test_missing_report_makes_no_gh_write_call_at_all` 以唯讀呼叫白名單釘住）。⚠️ **三條分流有兩條是明文豁免**：時戳早於 `pitfalls.PITFALL_GATE_EPOCH`、離開階段判不出來。⭐ 後者是**真實的口**：把交付狀態改成沒有反函數的值（`📥Backlog`／`📦已合併`／`⏸阻塞`）就繞得過去 |
| 查核退回 → 執行 | §3 | `handoff --next-stage implementation` | ⚠️ **有副作用、無前提**：iteration 無條件 +1，⛔ 不驗現值是否為 `↩退回`（表一第 10 列） |

#### 表三：`⏸阻塞` 的 TTL

⛔ **今天不存在。** 三件事各自為真，逐條寫明，⛔ 不以任何一條單獨成立：

1. **canonical 沒有條文。** `AI_WORKFLOW.md` 對 TTL 只在 **lease** 上有話（§4.1「lease 可續約、
   可到期回收；回收前先檢查未提交變更」），而 §7 的委派表把 TTL 列在 **Runbook** 那一欄，
   ⛔ 不在 `CONTROL_PLANE_CONTRACT.md` 那一欄。⇒ 「`⏸阻塞` 的 TTL」這句要求指向一個**在
   canonical 沒有本體**的東西。
2. **欄位不存在。** `project.FIELD_SPECS` 沒有任何時限欄；`⏸阻塞` 又沒有專責動詞，⇒ canonical
   §5 末段的四個必填（owner／原因／等待對象／解除條件）**沒有地方可以要求、也沒有地方可以驗**。
3. **碼裡零命中。** `cli/src/` 對 `lease_expires_at`／`--ttl`／`expires_at` 三個字串
   **全部 0 命中**（2026-08-26 實跑 `grep -rn`，`rc=1`）。

⭐ **零命中 ≠ 沒有機制**——這種落空有四類歸因（名稱猜錯／機制在別的模組／機制在別的 repo／
真的沒有）。本項取第四類，**依據是第 1、2 點**（條文與欄位都不存在），⛔ **不是**靠 grep 落空
本身。

⇒ **裁定**：`⏸阻塞` 今天**沒有 TTL，也沒有等待上限的執行者**。⛔ 不得在此寫一個看起來有時限
的數字——那會正好是 `docs/ROADMAP.md` §1 禁止的那種條文。要有 TTL，前置是先有 `⏸阻塞` 的
**專責動詞**（已登記於 `docs/CONTRACT_TOOL_RECONCILE.md` §4.1）。

#### 表四：escalation checkpoint

| 項 | 內容 |
|---|---|
| 規則本體 | `templates/review-escalation.md` §3／§4／§5；canonical §5 末段 |
| 觸發條件 | 第三個及其後**每一個可計數 attempt** 出現時，先建立 checkpoint；⛔ 不得只按整數直接寫 `🚨已升級` |
| 動詞 | `wfcli checkpoint`（`commands/checkpoint_cmd.py`） |
| 機械執行者 | ✅ **有**：`validation.check_checkpoint_gate`，由 `review_cmd` 在**寫入任何遠端狀態之前**呼叫（與 `check_attempt_not_duplicated` 同一個 `try:` 區塊）。判準是**兩面一致**——留言的結構化區塊 ＋ Issue body `## Log` 的同行索引，只有其一視為未建立 |
| 欄位檢查 | ✅ **有**：`validation.validate_checkpoint_input`——`trigger_attempt_id` 須合 `<card>-e<epoch>-<40 hex sha>`、反解出的卡與 epoch 須相符、`unique_attempt_count >= 3`、`checkpoint_decision ∈ CHECKPOINT_DECISIONS`、`checkpoint_rationale` 非空且不含三連反引號（圍籬字元會破壞結構化區塊） |
| ⚠️ **誠實邊界（必讀）** | **這道閘門今天恆不觸發。** 鏈條逐段可查：`review_cmd` 只在 `preflight.established` 時算 `counts`，而 `validation.derive_preflight_basis` **恆回** `PREFLIGHT_NOT_ESTABLISHED` ⇒ `counts` 恆為 `None` ⇒ 事件寫的是 `escalation_account: not-asserted` ⇒ `fact.counts` 恆為假 ⇒ `validation.counted_attempts` 恆為空 ⇒ `check_checkpoint_gate` 在 `if len(counted) < 3: return` 恆早退。⭐ **這是「有執行者、但前提在本 repo 結構上無法成立」的一格，⛔ 不得計為「有檢查」** |
| checkpoint **不改**交付狀態 | `checkpoint_cmd` 明文，`decision=escalate` 之後仍要人手打 `handoff --status 🚨已升級` ⇒ 表一第 14 列 |

#### 表五：`🚨已升級` 的決策 owner

| 問 | 答 |
|---|---|
| 誰**決定** | **需求方**（本 repo ＝ `ruan6047`）。canonical §1「需求方擁有問題優先序、目標、非目標與**各 Gate 的最終核可**」；§1.1「決策 100% 屬需求方本人」；§5 末段「不同根因且逐輪閉合、持續收斂時**由需求方決定**續修、重規劃、換執行者或升級」 |
| 誰**寫** | **唯一的 PM 祕書 session**，經 `wfcli`（canonical §1.1、§4.3）。checkpoint 事件的 `written_by` 取自 `review_cmd.resolve_platform_login` |
| 機械執行者 | ⛔ **無，而且結構上不可能有。** `docs/ROADMAP.md` §1 逐字：本 repo 的人類、PM、每個執行者、每個查核者**共用同一個 GitHub 帳號 `ruan6047`**；該節同時逐字禁止「寫看起來在驗證身分、實際恆真的條文」 |
| ⇒ 正解 | **記下宣告，不追求驗證**（ROADMAP §1 的裁定）：`written_by` 與 `checkpoint_rationale` 是宣告；代貼他人裁定時須在留言內註明**代擬代貼與授權來源**——那就是角色欄位的散文形式 |
| **解除** | 另一則 `escalation-resolution` 事件（`review-escalation.md` §4「escalate 之後的第三種結果」）。⛔ **writer 未實作** ⇒ 表一第 15 列 |

#### 表六：規劃期須納入的三項，各自的落點與「今天有沒有執行者」

| # | 事項 | 在本表的落點 | 今日執行者 |
|---:|---|---|---|
| 1 | 需求方 2026-08-22 的流程意向：**高複雜或影響較大的卡必跑 `🔬研究中`** | 表一第 2 列的前提欄；以及第 4、6 列的前提欄——因為「必跑過研究」只能在**離開**時檢查，不能在進入時 | ⛔ **無。** canonical §3 只寫「T3／T4、大卡、跨系統與不可逆變更先完成 Discovery Gate」，⛔ 沒有把它綁到 `🔬研究中` 這個狀態值；`handoff --next-stage research` 不讀級別也不讀前身。<br>⭐ **可行的形狀 2026-08-26 之後才出現**：Log 行現在記離開側階段，而 `研究` 是 `STAGE_PHASE` 的值之一 ⇒「Log 裡有沒有一筆離開研究階段的 handoff」**變成機械可判**。⚠️ 這正是 `WF-BACKLOG-STAGE1` 當時否決的候選 A，而它的否決理由（「handoff 的 Log 行不記 `--next-stage`」）**只對進入側成立**。<br>⛔ **但今天做不了**：實測全板只有 **3／204** 張卡的 Log 帶該標記 ⇒ 回放既有卡幾乎全滅，只能對新卡生效且須先釘界線 |
| 2 | 需求方 2026-08-22 的流程意向：**`🧭規劃中` 必含 Design Gate** | 表二「Design Gate」列；以及表一第 4 列（`🧭規劃中 → 📥Backlog`）的前提欄 | ⛔ **無，且連記錄的地方都沒有**：卡面 `Design` 區塊判 `absent`。canonical §3 已寫「純技術 T3／T4 可標註 Design Gate `N/A`，但**必須記錄理由**」⇒ 今天那個「記錄」**無處可放** |
| 3 | Discovery 實驗 F（2026-08-22）：`🏁完成` 的終態卡被 `assign` 直接拉回 `🔨執行中`，`rc=0` 且無任何警告 | 表一第 16 列 | ⛔ **無。** `TERMINAL_STATUSES` 只在掃**別張卡**的資源交集迴圈裡被讀，本卡自己的終態不讀。⛔ 本表不修（非射程），**承接者未指名** |

#### 表七：條文 ↔ `handoff_cmd.py` 的落差登記

**對帳基準**：`6148bd4495fd3134f0e42db926b558a02761fda8`。⚠️ 該檔在 `6148bd4` → `b169c242`
（其後的 main）之間**零改動**（`git diff <兩個 SHA> -- cli/src/wf_cli/commands/handoff_cmd.py`
為空），故以工作樹現值對帳與以基準對帳等價。

**表 ↔ 碼：0 條不一致。** 上面各表凡宣稱 `handoff_cmd` 的格子，其引用的字面共 18 個，逐一在
該檔命中（3 個為「定義處＋使用處」各一，其餘唯一）。⛔ 這一句不是「已對帳」三個字——複驗方式
是把每個格子裡的字面拿去 `grep -F`，命中 0 次即本表寫錯。

**條文 ↔ 碼：7 條落差**，逐條標明哪一邊要改：

| # | 條文說 | 碼實際做 | 哪一邊要改 |
|---:|---|---|---|
| D1 | canonical §0 給了一條交付狀態的**序列** | `--next-stage` 的六個非 release 值走同一個 `else`，**完全不讀現值** ⇒ 任何順序都走得通 | ⚖️ **條文**。§0 那一行是**敘述順序，不是約束**；本節表一已把它寫成「哪幾格有前提、哪幾格沒有」。要把它變成約束屬 `WF-CLI-*` 動詞卡，⛔ 不是把序列重寫一次 |
| D2 | canonical §5：`⏸阻塞` **必填** owner、原因、等待對象與解除條件 | `⏸阻塞` 沒有專責動詞 ⇒ **沒有任何地方可以要求或驗這四個欄位** | 🔧 **碼**。前置是先有 `⏸阻塞` 的專責動詞（已登記於 `docs/CONTRACT_TOOL_RECONCILE.md` §4.1） |
| D3 | canonical §0：`🛑已停止` **必填決策與原因後封存** | 同 D2，只有 `--status` 寫得進去 | 🔧 **碼**。同一前置 |
| D4 | canonical §0：廢止值 `⏳待執行`／`🚧進行中` **新寫入不得用** | 兩者仍在 `project.FIELD_SPECS` 的選項裡，`--status` 寫得進去 | 🔧 **碼**（收斂 `--status` 成 `choices`；已登記，⛔ 不在本節射程）。⚠️ Project 的 SINGLE_SELECT 選項刪不掉，故只能擋在 CLI 這一層 |
| D5 | canonical §3.1 T3：**需求方批註放行**後才進 `📥Backlog` | 未實作，且 `handoff_cmd` 的 docstring 逐字說明**刻意不實作** | ⚖️ **條文**。`docs/ROADMAP.md` §1 已裁定：本 repo 全角色同帳號 ⇒ 該款恆真，正解是**記下宣告不驗證身分**。⛔ 不得做成一個看起來在檢查的欄位 |
| D6 | canonical §0：release 以**終態**落地，序列上它排在 `✅通過`／`📦已合併` 之後 | `--next-stage release` **不檢查前身狀態**，任何格子都 release 得出去 | 🔧 **碼**（低優先）。主要危害已被收尾守衛擋住——`--cleanup` 路徑上終態只能在清理完成後寫；剩下的是「跳過查核直接結案」這條，屬動詞卡 |
| D7 | 「iteration」被口語讀成**被退回幾次** | `--next-stage implementation` **無條件** `+1`，⛔ 不驗現值是否為 `↩退回` | ⚖️ **條文／讀法**。碼是對的：iteration 的語意是「第幾輪」，而交回執行就是開新一輪。⛔ 要改的是任何把 iteration 讀成退回次數的說法（本節表一第 10 列已寫明） |

⭐ **D1、D5、D7 標「條文」，⛔ 不是因為改條文比較省事**——三者各有具名依據：D1 的 §0 那一行
自己就只是列舉、從未寫「不得跳過」；D5 是 `ROADMAP` §1 已裁定的一整類；D7 是碼的語意本來
就對。⛔ 其餘四條一律標「碼」，⛔ 不得反過來以「條文寫得太嚴」為由放寬。

#### 承接卡的狀態（需求方 2026-08-22 裁定 2 的另一半）

⚠️ **裁定 2 指名要另開的那張卡，至今未註冊。** 2026-08-26 以 `project.list_items` 現場掃 Project #4
全部 204 張，卡 ID 與功能欄命中「UNDECIDABLE／next-stage／stage-log」等關鍵詞的**只有一張**，
而那是已 🏁完成 的 `WF-BACKLOG-STAGE1`（`aiwf#120`，即當初把這件事延後的那張）；卡面 body 提到
`UNDECIDABLE_HANDOFF` 的只有 `WF-OPEN-INITIAL-STATUS1`（`aiwf#118`，🏁完成）與本卡。
⭐ **關鍵字沒命中 ⛔ 不等於不存在**——本項的依據是「用兩個不同的欄位面各掃一次都只掃到已完成的
卡」，⛔ 不是單一 grep 落空。

⭐ **前半的狀況要寫對，⛔ 不是「已被反序做掉」那麼簡單。** `WF-STAGE-PITFALL-LIST1`（`aiwf#148`，
🏁完成）確實讓 Log 行開始記階段，**但記的是離開側，而裁定 2 講的「記下 stage」是進入側**，而且
那是**刻意的相反選擇**：`handoff_cmd.py` 的 `PHASE_LOG_LABEL` 上方註解逐字給了兩個理由，第二個
正是「記進入側會讓 `--next-stage` 變得可反推，而 doctor 的狀態面漂移推導以『handoff 的留痕反推
不出狀態』為前提……⇒ 不製造需要改它的漂移」。⇒ **前半不是被提前做掉，是被做成了相反方向**；
後半（翻掉 `doctor.UNDECIDABLE_HANDOFF` 及其守衛）**一個字都沒動**，且 `aiwf#148` 之後它成立的
理由更強。

⇒ **本節的表不因此改變形狀**（兩軸已在上方分開）。承接卡的**射程需重寫**，兩條路徑互斥，
⛔ 本節不選、也不代開卡：

- **甲：讓寫入端留下可反推的東西**（Log 行加記進入側狀態，或加記 `--next-stage` 鍵）。代價已被
  測試預先標明——`cli/tests/test_commands_mocked.py` 的
  `test_handoff_log_line_never_carries_the_status_it_wrote` 會轉紅，而它的 docstring 逐條寫了
  「這三條各自會被什麼推翻」。⭐ **轉紅是守衛在做它該做的事，⛔ 不是違反它。**
- **乙：讓讀取端從離開側階段推導寫入狀態。** ⛔ **不成立**：離開側不含進入側資訊，`STAGE_PHASE`
  在六個鍵上單射只保證「進入側 → 階段」可算，⛔ 反方向算不回來。

#### ⛔ 本節刻意不做的（非射程）

1. ⛔ 不改 `handoff` 的 Log 記法、不改 `doctor.UNDECIDABLE_HANDOFF` 及其守衛（需求方
   2026-08-22 裁定 2：拆兩張，本表是那張卡的**輸入**）。
2. ⛔ 不補「終態卡可被 `assign` 直接拉回執行中」那個洞。
3. ⛔ 不把 `--status` 收斂成 `choices`。
4. ⛔ 不新增、不移除任何狀態值或 Project 欄位。
5. ⛔ 本節是**條文不是碼**：它不會擋下任何一次違規轉移。要它擋得住，得有 `WF-CLI-*` 動詞卡
   把它翻成軸三那樣的 `dict` ＋ 閘門。⛔ 不得把「表寫好了」讀成「口關上了」。

## 3. Claim、lease 與 WIP

- claim command／workflow：<命令或 URL>
- concurrency key：<repository + card/resource key>
- lease TTL／續約：<時間與命令>
- 到期回收：<未提交變更檢查、通知與人工介入>
- WIP limit：agent <n>；review queue <n>；超過時 <行為>
- **派工前資源交集比對**：<命令；比對本卡寫入集 × 現役卡寫入集，撞則排隊。現役含 `📦已合併` 未收尾者—canonical §4.4>
- **破壞性 CLI（啟動須驗 lease，無 lease 拒跑）**：<入口清單>
- **當前仍有副作用的 CLI 入口（查核／探索禁跑）**：<入口清單／無—canonical §6.1 第 6 條>
- **worktree 註冊**：<認領時把實際路徑＋分支寫回卡的命令>；派工前必跑的 `doctor` 對帳：<命令>

## 4. Handoff 與 optional tmux adapter

- Handoff contract：從 [`handoff-contract.md`](handoff-contract.md) 建立 `<專案>/docs/HANDOFF_CONTRACT.md`；T2 以上或 owner 變更必填。
- Receiver 驗證：<驗證完整 SHA、baseline、lease、證據的 command／workflow>
- Receiver 接受事件：<`handoff-accepted` writer 與權限>
- tmux：<不用／僅 session launcher／僅 wake-up；不得作為遠端狀態來源>
- Local runtime：<路徑；必須在 `.gitignore`；清理／重啟程序>

## 5. 權限與事故處理

- GitHub Actions token／App 權限：<最小 permissions>
- 外部協作者可做／不可做：<claim、review、merge、release>
- GitHub 不可用時：<停止 claim／本機鎖的限制／恢復程序>
- 對帳：<claim、handoff、merge、release 後的檢查命令>
