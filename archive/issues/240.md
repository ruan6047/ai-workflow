# #240 [清單] 卡的 write-set 與記錄其機制狀態的文件分離，機制落地與記錄更新不可能同卡完成
- state: open  created: 2026-09-02T12:12:55Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/240
- comments: 0

## Body

### 出處可指

`AI_WORKFLOW.md:274`／`:283`、`README.md:22`、`AGENTS.md:22`；對照 `ruan6047/ai-workflow#221`（`WF-REDESIGN-W3`）的資源宣告欄。

### 是觀察不是結論

**結構性事實**：`WF-REDESIGN-W3` 的 write-set 今日為 6 條——`file:cli/src/`、`file:cli/tests/`、`file:scripts/`、`file:.github/workflows/ci.yml`、`file:stage-rules/`、`file:templates/database-contract.md`。⇒ **記錄該卡機制狀態的三個檔皆不在其中。**

**三處逐字現況與落地後的落差**：

1. `AI_WORKFLOW.md:274`（§0.1 執行者狀態表 row #4）逐字：「⚠️ 僅事後偵測：`cleanup.classify_state`。逃生門 `handoff_cmd.py` 的 `if args.status:` 分支敞開。**承接者＝`WF-REDESIGN-W3′`**」。而同節 `:283` 逐字：「⛔ **不得宣稱本卡任何一條已機械化。** 機械化屬子卡；**子卡落地時應回頭更新本表**。」⇒ 該卡落地後應更新此列，而 `AI_WORKFLOW.md` ⛔ 不在其 write-set。
   ⚠️ 併記：即使能改也**⛔ 不得標為已機械化**——該卡驗收 8 的射程逐字只含 `handoff_cmd.py`，`assign_cmd.py:303` 的同形逃生門未涵蓋（另見 `ruan6047/ai-workflow#239`）。
2. `README.md:22` 與 `AGENTS.md:22` 逐字：「⚠️ 「① 印給你」的**機械列印尚未生效**（**機制歸 `WF-REDESIGN-W3`**；沿 canonical §0.1 先例，⛔ 不啟用尚無 writer 的規則）。在那之前 ① 由 PM 人工…」。而需求方 2026-09-02 決策 20 乙′ 逐字裁定「⛔ **不做主動列印**；note 清冊接進現有 `refusal_message`」，該卡規格逐字承接為「主動列印（「進入階段時印」）**⛔ 本卡不做**」。⇒ 該卡結案後，這兩行會指向**一張已結案而未做該事的卡**；兩檔皆⛔ 不在其 write-set。
3. `AI_WORKFLOW.md:275`（同表 row 5）逐字：「§6.3 parser 須沿用 `resources.py` 哨兵、不得自寫 markdown 解析 | ✅ **有**：`brief.py` 的 `_reuse_probe()` 於模組載入時檢查」。該卡規劃者登記該欄為過度宣稱（`_reuse_probe` 防的是共用函式被改壞，⛔ 不是「誰沒用它」），而該卡驗收 2 會動卡面解析路徑 ⇒ 落地時該欄的正確性會被實際觸及；同樣⛔ 不在 write-set。

⇒ 可觀測現象：**一張卡的 write-set 與「記錄該卡機制狀態的文件」是分離的**，於是機制落地與記錄更新⛔ 不可能在同一張卡內完成。

⚠️ **⛔ 不宣稱這是設計缺陷**——`AI_WORKFLOW.md:283` 逐字要求「子卡落地時應回頭更新本表」，但⛔ 未規定該更新由哪張卡、以什麼機制執行。本項登記的是**該要求今日無執行路徑**。

⚠️ ⛔ 未量測：其他已結案子卡是否也留下同形漂移（母體未掃）。

### 查重留痕

已跑（`gh issue list --repo ruan6047/ai-workflow --state all --search <關鍵字>`）：

```bash
gh issue list --repo ruan6047/ai-workflow --state all --search "write-set 文件"
gh issue list --repo ruan6047/ai-workflow --state all --search "機制狀態"
gh issue list --repo ruan6047/ai-workflow --state all --search "AI_WORKFLOW.md 更新"
gh issue list --repo ruan6047/ai-workflow --state all --search "canonical 同步"
```

命中：`#146`（`WF-CANONICAL-SELF-STALENESS1`，已關閉）／`#119`（`WF-CANONICAL-STALE-SYNC1`，已關閉）／`#159`（`DOC-STALE-FILE-LINE-POINTERS1`，已關閉）／`#238`／`#177`／`#217`／`#221`／`#56`／`#91`／`#89`／`#30`／`#115`／`#52`。逐一核對：`#119`／`#146`／`#159` 皆為**已發生的**文件與現實不符之個案修復，⛔ 非「write-set 與記錄檔分離」這個結構；`#89`（`WF-BASELINE-UPSTREAM-TRIGGER1`）對象為 baseline-cascade 缺上游觸發者，⛔ 非本項。**⛔ 無任何一張以本項為痛點。**

### 屬哪個 repo

ai-workflow

### 提案者身分

- GitHub 帳號：`ruan6047`（本 issue 的 author 欄即為此帳號，可核）
- session ID：`cc0a7952-07a5-4978-8d03-8b5f48fbc690`（PM session，Claude Code，模型 `claude-fable-5`）
- 該則訊息定位：本項由該 session 於 2026-09-02 為 `#221` 跑 `handoff` 進執行階段前，逐項判定「掛著未動的另案是否影響本卡」時量到；三處逐字皆於當日實查。transcript 於需求方本機 `~/.claude/projects/-Users-ruanruan-Dev-cpbl-analytics--claude-worktrees-workflow-review-optimization-33882b/` 可核。

---

⚠️ **提案者即 PM**：由需求方於同 session 逐字裁定「不要硬合」後與 `ruan6047/ai-workflow#239` 分別建立。收件閘的「提案者≠肇因者」成立、「提案者≠收件者」不成立 ⇒ 由需求方決定是否補一次第二 PM 收件裁決。

> ⛔ 本項不配卡ID、⛔ 不掛成任何卡的 sub-issue、⛔ 不進 Project #4；升級走 `wfcli open --from-issue <本 URL>`。

