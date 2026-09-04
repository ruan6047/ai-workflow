# #140 WF-RESOURCE-HEADING-SUFFIX1-PROBE-ASSIGN1 拋棄式探針：在真實卡面形狀上實跑 assign 與 userContentEdits 回滾
- state: open  created: 2026-08-25T12:11:58Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/140
- comments: 1

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
- Initiative：—　spec 基線：—

- 執行：待指派（建議 經濟型；拋棄式探針，只跑既有動詞並記錄輸出，⛔ 不改任何生產碼；判斷成分低。）　查核：待指派（建議 經濟型；查核只需核對三段輸出是否逐字相符；⛔ 無設計判斷。本卡的結論會回寫到 aiwf#105 的 V5／V13，實質查核在那張卡。）
- DB：db_scope=none
- 服務的原始目標：ROADMAP §0 目標 2「可稽核的內容」——`aiwf#105` 交付若把 V5／V13 列為未驗，查核者無從判斷「修好之後真的能派工／真的回得去」，那正是本卡族要消滅的失效模式。

## 資源宣告（機器可讀；`null`／`[]` 代表未正式宣告，不代表無資源）
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:docs/reference/PROBE_WF_RESOURCE_HEADING_SUFFIX1.md"
  ]
}
```
<!-- resource-claims:end -->

## 核心痛點


## 驗收條件


## 驗證

## Log

- 2026-08-25T20:11:56+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-25T20:15:29+08:00 amend by wf-cli（op 322223d9）→ 資源宣告（補哨兵）：原值「## 資源宣告（機器可讀；`null`／`[]` 代表未正式宣告，不代表無資源） ```json { "db_scope": "none", "resources": [ "file:docs/reference/PROBE_WF_RESOURCE_HEADING_SUFFIX1.md" ] } ```」→ 新值「（已包入 resource-claims 哨兵）」；理由 P1→P2：把既有資源宣告包進哨兵（與那 33 張真實遷移卡走同一條路徑）。
- 2026-08-25T20:15:57+08:00 amend by wf-cli（op 1586fc34）→ 卡面標頭（補回遷移缺行）：原值「（原卡面無標頭行與三章節）」→ 新值「- 需求：ruan6047 規劃：Claude Opus 5@Claude Code (PM) - Initiative：— spec 基線：— ## 核心痛點 ## 驗收條件 ## 驗證」；理由 P2：補回標頭行與 §6.4.1 必要章節（與第四段走同一條路徑）。
- 2026-08-25T20:16:50+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree ai/opus-5/PROBE-ASSIGN1 @ —；交付狀態 🔨執行中；實際能力層級 經濟型（卡面無建議層級：卡面標頭區沒有獨立成行的 <!-- wf-routing:v1 --> 宣告：本卡開立於規劃期路由必填之前；理由：拋棄式探針，卡面無 wf-routing 宣告（outcome=absent）故必須補理由；本卡不承載真實工作。）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 path_unanchored（機器局部，沉默不代表無誤）。
- 2026-08-25T20:24:57+08:00 handoff by wf-cli → owner —（已停止）；iteration 0；SHA d4ba7ce5f3fa526fc3a7aa0ebbeee3c926e5eb28；證據 P1–P5／PV1–PV4 全部完成，結論已回寫 aiwf#105 的 V5／V13（issuecomment-5410327425）。負控 rc=2 零寫入、修復兩步 rc=0、assign 不帶理由 rc=2 帶理由 rc=0、回滾三段逐位元相同（sha256 b78881b5182ef8193ec475dfefc85b2b02b74384e68ac6873bad54822ab8b80e）。⛔ 本卡不承載任何真實工作、不留待辦，做完即停止。⚠️ 順帶登記一個活的 fail-open 缺口：assign 對 3 張 db_scope:null 的活卡靜默略過交集檢查（僅警告不擋），屬另一張卡。；⚠️ 未帶 --cleanup 且未帶 --repo-path，收尾清理未執行（worktree、本地分支、遠端分支皆未處理），狀態面已寫終態。


## Comment 5414010662 · 2026-08-25T17:12:51Z

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

