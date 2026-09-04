# #237 清單項：Project #4 有 13 張卡的 Initiative 欄值在看板內查無同名卡ID
- state: open  created: 2026-09-01T19:58:32Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/237
- comments: 0

## Body

### 出處可指

Project #4 的 `Initiative` 欄（實查於 2026-09-02，main `7d798062b9b37be3ab98d1de58ceebaf42bdcc2e`）；欄位型別定義在 `cli/src/wf_cli/project.py:30` 逐字 `"Initiative": ("TEXT", None)`；寫入旗標為 `wfcli open --initiative` 與 `wfcli amend --initiative`。

### 是觀察不是結論

以 `wf_cli.project.list_items` 讀取 Project #4 全部 items 後，逐一比對每張卡 `Initiative` 欄的值是否等於某張卡的 `卡ID` 欄：

| `Initiative` 欄的值 | 張數 | 是否有同名卡ID |
|---|---|---|
| `INIT-OFFICIAL-DATA1` | 8 | 有 |
| `INIT-GAME-RECAP` | 6 | 有 |
| `INIT-PRODUCT-UX` | 6 | 有 |
| `WF-REDESIGN1` | 4 | 有 |
| `WF-STAGE-STATE-TWO-AXIS1` | 2 | 有 |
| **`WF-22`** | **5** | **無** |
| **字面字串 `None`** | **7** | **無** |
| **`WF-REDESIGN`** | **1** | **無** |

⇒ 共 **13 張**卡的該欄值在 Project #4 內查無同名卡ID。逐張列出：

- `WF-22`（5）：`OPS-STATE-PLANE-MIG1`、`OPS-CODE-BRANCH-PROTECT1`、`WF-22-CANON1`、`WF-22-CLI3`、`WF-22-CLI4`。⚠️ 其中三張的卡ID 本身以 `WF-22-` 起頭。
- 字面 `None`（7）：`DEV-CI-RED-OWNERSHIP1`、`DEV-EVENT-REPAIR-ANCHOR1`、`DEV-REVIEW-DEACCEPT-TRAIL1`、`DEV-REVIEW-PREFLIGHT-GATE1`、`DEV-REVIEW-PREFLIGHT-SELFCHECK1`、`DOC-CARD-SPEC-RULES1`、`OPS-CONTROL-PLANE-PR-GUARD1`。⚠️ 實查該欄**缺值**（Python `None`）的卡數為 **0** ⇒ 這七張是把 `None` 當成**值寫進去**的，⛔ 非未填。
- `WF-REDESIGN`（1）：**`WF-REDESIGN1` 這張卡自己**（`ruan6047/ai-workflow#177`）——其 `Initiative` 欄的值比它自己的卡ID 少一個尾碼字元。

**⚠️ 該欄是自由文字，⛔ 上述⛔ 不構成違反宣告值域**：`project.py:30` 逐字 `("TEXT", None)`（無選項集）。「值應對應真實卡ID」是慣例，⛔ 未見於任何機讀處——`project.py`／`validation.py` 內對該欄除型別宣告與旗標對映（`:109` 逐字 `"initiative": "Initiative"`）外查無其他引用。

其他可觀測事實（一併記，避免日後被誤讀成缺陷）：

- Project #4 的四張 Initiative 父卡（`INIT-GAME-RECAP`／`INIT-OFFICIAL-DATA1`／`INIT-PRODUCT-UX`／`WF-REDESIGN1`）**全部**為 `交付狀態=💡需求`、`iteration=0.0`；其中僅 `WF-REDESIGN1` 有 `階段` 值（`需求`），另三張為空。⇒ **父卡不隨子卡推進是現行一致行為**，⛔ 非本項所指的漂移。

### 查重留痕

已跑（`gh issue list --repo ruan6047/ai-workflow --state open --search <關鍵字>`）：

```bash
gh issue list --repo ruan6047/ai-workflow --state open --search "Initiative 欄"
gh issue list --repo ruan6047/ai-workflow --state open --search "父卡"
gh issue list --repo ruan6047/ai-workflow --state open --search "卡ID"
```

命中：`#177`／`#221`／`#217`／`#136`／`#213`／`#222`／`#128`／`#234`／`#228`。逐一核對：`#222`（切換 Initiative）處理看板**語彙**切換，⛔ 非欄位值的解析；`#128`（`WF-OPEN-DUPLICATE-DETECT1`）處理 `open` 的卡ID 重複偵測，⛔ 非 `Initiative` 欄；`#234`／`#228` 對象分別為 `research.md` 與 canonical §3。**三個關鍵字都沒有命中以本項為痛點的既有清單項或卡。**

### 屬哪個 repo

ai-workflow

### 提案者身分

- GitHub 帳號：`ruan6047`（本 issue 的 author 欄即為此帳號，可核）
- session ID：`cc0a7952-07a5-4978-8d03-8b5f48fbc690`（PM session，Claude Code，模型 `claude-fable-5`）
- 該則訊息定位：本項由該 session 於 2026-09-02 檢視「接下來處理哪張卡」時順帶量到；量測指令與逐張清單如上，transcript 於需求方本機 `~/.claude/projects/-Users-ruanruan-Dev-cpbl-analytics--claude-worktrees-workflow-review-optimization-33882b/` 可核。

---

⚠️ **提案者即 PM**：本項由 PM 於執行 PM 職責時量到，⛔ 非 PM 造成（那些值由各卡開卡時寫入）。收件閘的「提案者≠肇因者」成立、「提案者≠收件者」不成立 ⇒ 由需求方決定是否補一次第二 PM 收件裁決。

> ⛔ 本項不配卡ID、⛔ 不掛成任何卡的 sub-issue、⛔ 不進 Project #4；升級走 `wfcli open --from-issue <本 URL>`。

