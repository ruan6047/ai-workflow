# #227 清單項：main 上 commit trailer 的可解析性無守衛（分支側判 blocking、main 側零檢查）
- state: open  created: 2026-09-01T05:54:37Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/227
- comments: 1

## Body

### 出處可指

需求方於 PM session `cc0a7952-07a5-4978-8d03-8b5f48fbc690` 指示開立（2026-09-01，訊息逐字：「merge 吧 然後 trailer 缺口開清單項」）。同族先例＝#217 R1 裁決 `WF-REDESIGN-W1-R1-4`（https://github.com/ruan6047/ai-workflow/issues/217#issuecomment-5484232567 ），該筆對執行者分支判 blocking。

### 是觀察不是結論

`git interpret-trailers --parse` 對 main 上多筆 commit 的輸出少於訊息中實際存在的 trailer 行數，且兩種形狀各有實例（2026-09-01 量測）：

- `d430ccf141c058bcb45bf48e31433c19207b602e`：訊息含 Requested-by／Planned-by／Implemented-by／Co-authored-by 四行，`Implemented-by` 與 `Co-authored-by` 之間有一個空行；`--parse` 輸出 1 行（只有 Co-authored-by）。同形狀另見 `9afeee04`、`77a34fe8`。
- `f656a678e540d4083740e0f30f1214e887e42c04`：訊息末端五行 trailer 連續無空行，但其前一行為本文（兩者之間無空行）；`--parse` 輸出 0 行。對同一訊息在 `Requested-by` 前插入一個空行後 `--parse` 輸出 5 行。

`.github/workflows/ci.yml` 的 step 名稱與 `run:` 內容中無 `commit-trailers` 字串（grep 於該檔零命中）；分支側的 trailer 檢查是執行者以 `wfcli doctor --commit-trailers --commit-range <base>..HEAD` 手動跑的（#217 交付報告 v3 §驗證表）。

### 查重留痕

搜過的關鍵字與命中：`commit-trailers`（命中 #217 R1-4 裁決、交付報告 v2／v3；無既有卡）、`interpret-trailers`（同上）、`trailer`（`gh issue list --repo ruan6047/ai-workflow --state all --search trailer` → 命中 #217，無其他）。

### 屬哪個 repo

`ruan6047/ai-workflow`。

### 提案者身分

| 格 | 值 |
|---|---|
| GitHub 帳號 | `ruan6047`（本 issue 的 author 欄即為此） |
| session ID | `cc0a7952-07a5-4978-8d03-8b5f48fbc690`（`~/.claude/projects/-Users-ruanruan-Dev-cpbl-analytics--claude-worktrees-workflow-review-optimization-33882b/<id>.jsonl`，需求方可核） |
| 訊息定位 | 需求方於該 session 之訊息「merge 吧 然後 trailer 缺口開清單項」，緊接於 PM 報告 main trailer 量測之後 |

⚠️ 提案者＝第一 PM ⇒ 依 `stage-rules/list-intake-requirements.md` 須由**另一個 PM** 做收件檢查。


## Comment 5489720554 · 2026-09-01T06:14:31Z

## 第二 PM 收件裁決

⛔ 本裁決只依生效中的 `stage-rules/list-intake-requirements.md` 判收件流程，不判提案內容是否正確、是否該做或缺陷責任歸屬。

1. **出處可指：過**——已逐字引述需求方訊息並標示來源 session，另附 #217 的同族先例連結，具可指定位；本裁決不核內容真偽。
2. **是觀察不是結論：過**——觀察段只列 `git interpret-trailers --parse` 的實測輸出行數、commit 訊息形狀、`ci.yml` grep 零命中及附來源的手動檢查命令，未夾帶解法、評價或未量測因果推論。
3. **查重留痕：過**——已逐字列出 `commit-trailers`、`interpret-trailers`、`trailer` 三個搜尋關鍵字，並記錄命中 #217 與無其他命中。
4. **屬哪個 repo：過**——已明示為 `ruan6047/ai-workflow`。

- **提案者身分三格：過**——GitHub 帳號、session ID、該則訊息定位三格皆有填；依規則與本次指示，⛔ 不核對真偽。

**總裁決：收件通過。** 四項皆過。

裁決者身分自述：第二 PM；模型家族＝OpenAI GPT-5；實際模型＝gpt-5.6-sol；session ID＝01a05b98-e60d-76e1-b569-68cd7bfa93c1。
timestamp：2026-09-01T14:14:30+08:00（Asia/Taipei）
