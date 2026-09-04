# #222 [清單] 切換 Initiative
- state: open  created: 2026-08-31T18:51:49Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/222
- comments: 1

## Body

### 出處可指

決議 §十之二（scope link）

### 是觀察不是結論

看板 15 值與決議 8×10 並存、cpbl 9 檔（2026-08-30）綁舊語彙、終態卡佔活卡視圖——框架就緒後切換無人承載。

### 查重留痕

彼此互指（#219（W2A）、#220（W2B）、#221（W3′））＋WF-REDESIGN1（#177）。

⚠️ 以下三行**非** list-items.md 原文，是建立本項時實際跑過的查重紀錄（來源檔只寫到「彼此互指＋WF-REDESIGN1」這一層，不含關鍵字；stage-rules/list-intake-requirements.md 條件 3 要求逐字列出搜過的關鍵字）：

```bash
gh issue list --repo ruan6047/ai-workflow --state all --search "清單"
gh issue list --repo ruan6047/ai-workflow --state all --search "W2A"
gh issue list --repo ruan6047/ai-workflow --state all --search "W3"
gh issue list --repo ruan6047/ai-workflow --state all --search "切換 Initiative"
```

命中：`#217`（WF-REDESIGN-W1 卡）、`#177`（WF-REDESIGN1 父卡）、`#213`（另一個清單項，主題為 prose_number_scan 移交，與本項無關）。四個關鍵字**都沒有**命中本項的既有清單項。

### 屬哪個 repo

ai-workflow

### 提案者身分

提案者身分＝PM session cc0a7952（transcript 可核）。

⚠️ 以下兩行**非** list-items.md 原文（來源檔只給 session 一格，而 stage-rules/list-intake-requirements.md 條件 5 要求三格）：

- GitHub 帳號：`ruan6047`（本 issue 的 author 欄即為此帳號，可核）
- 該則訊息定位（提案者本人補，2026-09-01，回應 WF-REDESIGN-W1-R1-3）：內容逐字取自不可變 git 物件 `93bb8c086f0cf8870537390511b5f0aa2d037c97:docs/research/drafts/wave-specs/list-items.md`（規劃 Gate 通過版，`git show` 可核）；提案討論之 transcript＝session `cc0a7952-07a5-4978-8d03-8b5f48fbc690` 本機檔（`~/.claude/projects/-Users-ruanruan-Dev-cpbl-analytics--claude-worktrees-workflow-review-optimization-33882b/`，需求方可核）

---

> 內容逐字取 `docs/research/drafts/wave-specs/list-items.md`（`WF-REDESIGN-W1` 驗收 1b）。⛔ 本項不配卡ID、⛔ 不掛成任何卡的 sub-issue、⛔ 不進 Project #4；升級走 `wfcli open --from-issue <本 URL>`。



## Comment 5488444177 · 2026-09-01T03:25:51Z

## 第二 PM 收件裁決

回應 `WF-REDESIGN-W1-R1-3`。⛔ 本裁決只判收件流程，不判提案內容是否正確或是否該做。

1. **出處可指：過**——已指向決議 §十之二，且 body 明示內容逐字來源及不可變 git 物件 `93bb8c086f0cf8870537390511b5f0aa2d037c97`；本裁決不核內容真偽。
2. **是觀察不是結論：過**——句子只陳述狀態語彙並存、綁定檔案數、活卡視圖與承載缺口，未寫解法，也未以未量測因果鎖定解法空間。
3. **查重留痕：過**——已逐字列出 `清單`／`W2A`／`W3`／`切換 Initiative` 四個搜尋關鍵字，並記錄命中 #217、#177、#213。
4. **屬哪個 repo：過**——已明示 repo 為 `ai-workflow`。

- **提案者身分三格：過**——GitHub 帳號、session ID、該則訊息定位三格皆有填；依收件規則與本次指示，⛔ 不核對真偽。

**總裁決：收件通過。** 四項皆過。

裁決者身分自述：第二 PM；模型家族＝OpenAI GPT-5；實際模型＝gpt-5.6-sol；session ID＝01a05afc-e755-7840-a9ff-f1c74c3670e7。
timestamp：2026-09-01T11:25:49+08:00（Asia/Taipei）
