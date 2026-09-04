# #234 清單項：research.md 同一份檔內把 ④ 指給兩個不同角色（§3 查核者 vs §4 PM）
- state: open  created: 2026-09-01T17:47:32Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/234
- comments: 0

## Body

### 出處可指

ai-workflow `stage-rules/research.md`（main 現行 `13cc5f0551759934f8a9a7295de219b4c4164b3e`；該檔由 `WF-REDESIGN-W2A`／`#219` 於 `950b3e278371e948900dd381cd7b4e595882c6b0` 生效）。

### 是觀察不是結論

同一份 `stage-rules/research.md` 內，`④` 被指給兩個不同角色：

- `:16`（§3 階段內流程）逐字：「…④ **查核者**只驗量測可重跑；**高階型卡另加 ≥3 個不同族角度的對抗性反測**（時間外／母體外／洩漏探針／重抽／規則邊界；不適用寫「不適用：<原因>」）。」
- `:22`（§4 各角色表）逐字：「| PM | 派工包含該卡與相關卡既有留言；**④ 對量測完整性** | 不判結論對錯 |」
- `:24`（同表下一列）逐字：「| 查核者 | 驗量測可重跑（高階型＋三反測） | 不裁結論真值 |」——**該列⛔ 無 `④` 標號**。

⇒ `:16` 把 `④` 標給查核者；`:22` 把 `④` 標給 PM，並把查核者的同一項職責在 `:24` 另列且不編號。

其他可觀測事實：

- 對照其餘七份 stage-rules 的 `④` 首次出現：`requirement`「④ R1 由需求方／人工（痛點還成立嗎）」、`implementation`「④ → 審核／待辦」、`review`「④ 過」、`deploy`／`maintenance`「④ 對格數與值域機械對照（⛔ 不判內容）」、`planning`／`closeout` 該處為單獨的「④」字元。⇒ **`④` 的執行者逐階段不同**；`research.md` 是唯一在**同一份檔內**把它指給兩個角色者。
- `stage-rules/` 全掃 `豁免`／`免除`／`可跳過`／`得跳過`：**零命中**（排除「豁免條目」「不含豁免」等他義用法）⇒ 該衝突⛔ 無既有的迴避途徑。
- 實例：`WF-POLLUTION-MANIFEST-STALE1`（`#231`）於 2026-09-02 需離開研究階段時遭遇本項，需求方逐案裁定「本卡採 §4 讀法」並逐字聲明「⛔ 不宣稱 §3 是筆誤」（該卡 `issuecomment-5497931407`）。⇒ 本項在該卡上**以逐案裁定繞過，⛔ 未被解決**。
- 影響面：`research.md` §1 逐字「進入＝階段計畫有列研究」⇒ 凡階段計畫列有研究的卡皆經過此步。

### 查重留痕

已跑（`gh issue list --repo ruan6047/ai-workflow --state open --search <關鍵字>`）：

```bash
gh issue list --repo ruan6047/ai-workflow --state open --search "research.md"
gh issue list --repo ruan6047/ai-workflow --state open --search "階段內流程"
gh issue list --repo ruan6047/ai-workflow --state open --search "角色表"
```

命中：`#231`（本項的發現處，已 🛑已停止）、`#214`（W0）、`#221`（`[清單] W3′`）、`#213`、`#66`、`#228`、`#52`、`#58`。逐一核對：`#221` 對 `stage-rules` 的提及**僅為引用 `list-intake-requirements.md` 的收件條件**（條件 3、條件 5），⛔ 不涵蓋本項；`#228` 的對象是 canonical §3 的取代清單覆蓋缺口，⛔ 非 `research.md`。**三個關鍵字都沒有命中以本項為痛點的既有清單項或卡。**

### 屬哪個 repo

ai-workflow

### 提案者身分

- GitHub 帳號：`ruan6047`（本 issue 的 author 欄即為此帳號，可核）
- session ID：`cc0a7952-07a5-4978-8d03-8b5f48fbc690`（PM session，Claude Code，模型 `claude-fable-5`）
- 該則訊息定位：本項由該 session 於 2026-09-02 處理 `#231` 的研究階段離開時發現並逐字量測，過程留痕於 `#231` 的 `issuecomment-5497931407`（裁定二）；transcript 於需求方本機 `~/.claude/projects/-Users-ruanruan-Dev-cpbl-analytics--claude-worktrees-workflow-review-optimization-33882b/` 可核。

---

⚠️ **提案者即 PM。** 本項由 PM 於執行 PM 職責時發現，⛔ 非 PM 自己造成（該檔由 `#219` 的執行者撰寫、經跨家族查核通過）。收件閘的獨立性在「提案者≠肇因者」這一面成立，但「提案者≠收件者」不成立 ⇒ 由需求方決定是否補一次第二 PM 收件裁決。

> ⛔ 本項不配卡ID、⛔ 不掛成任何卡的 sub-issue、⛔ 不進 Project #4；升級走 `wfcli open --from-issue <本 URL>`。

