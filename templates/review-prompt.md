# 查核詞範本 (Review Prompt)

> 承載 canonical `AI_WORKFLOW.md` §5.1／§5.2。祕書派審時以此組裝。紅線卡的查核者必須**跨模型家族或人工**（canonical §5）；同家族不同工具不算獨立。查核者**不得代改 source branch**。

## 1. 進駐位置與基準 SHA 核對

> **本節的每一條都設計成你當場驗得完**：判定輸入可不可信所需的東西——repo、Issue、幾道 git 指令——都已經在你手上，**不需要信任 Coordinator，也不需要等任何人補檢查**。驗不過就停，不必猜對方是不是筆誤。

- **權威來源只有一個**：本輪查核的輸入是 **Issue 上的派審留言**。協調者提示詞、摘要表格、對話轉述都是**次要來源，一律不作數**，即使更方便或更晚出現。兩者不符時以 Issue 為準，並把該不符本身寫成 finding（`attribution: coordinator`）。
  - **值解不開時先回對權威來源，不要直接停手**：2026-08-12 #39 的查核者把協調者表格裡的**裸 worktree 名**接到 repo 根目錄，組出一個不存在的路徑並判 `review-invalid`——而 **Issue 上的派審詞給的路徑是對的**。程序上那個判定沒錯，但它在你手上就避得掉：路徑、SHA、分支名都當場驗得了（`test -d`／`git rev-parse`／`git cat-file -e`），驗完再判。
- 進駐 worktree：`<絕對路徑>`（**唯讀查核**）——`test -d` 驗得到才進駐；解不開先回 Issue 對，不要用任何摘要表格裡的簡稱自行拼路徑。
- 被審分支：`<branch>`　`source_sha`：`<完整 40 碼 SHA>`
- **進駐後第一件事**：核對 `git rev-parse HEAD` 與 handoff 指定的 `source_sha` 完全相同、工作區乾淨。不同即停，回報 `review-invalid`，不進實質查核。
- 卡與基線：`<CARD_ID>`（`<owner/repo>#<n>`）；spec 基線 `<版本>`——與父卡當前版本不一致即退回。
- **基線須自行驗為祖先**：派審詞給的「基線」是界定 diff 範圍的座標，由 Coordinator 手填、**送出前無任何前置檢查**。進駐後跑 `git merge-base --is-ancestor <基線> HEAD`；exit 非 0 即停，回報 `review-invalid`。判準本身是機械的（git 的 exit code），但**沒有東西強制查核者跑它**，故本條是**約定**；把結果寫進 §5 `self_run` 後，`self_run` 非空由 `cli/src/wf_cli/validation.py` 的 `validate_review_report` 強制（基線 `6e6e8ab` 時在 :261／:265）——**但那只強制「有寫東西」，不驗這個檢查真的跑過**。
  - **一個 repo、一道指令、一個 exit code——判定所需的全部。** 本條不宣稱能阻止 Coordinator 填錯（那在派審當下已成立），它買的是**你當場分辨得出來**。2026-08-11 同一個錯誤基線（`0d4d282`，非任何卡的祖先）送給四位查核者，四種處置：一位據此停手（正確）、一位寫下「基線仍為被審 SHA 的祖先」——**該斷言不成立**，只是結論恰好無害。差別不在能力，在有沒有人告訴他這件事該當場驗；無此條時「驗過」與「沒驗」在報告上無法區分。

## 2. 第一判準（具否決權）

先答：**核心痛點「`<卡面痛點原文>`」是否已消失？證據是什麼？**

- 痛點未消 → `REQUEST_CHANGES`，**即使驗收清單全過**；並指出清單與痛點脫節之處（spec 缺陷，`attribution: planner`）。

## 3. 逐項驗收清單

- [ ] `<卡面驗收條件逐條抄入，一條一列；不得摘要合併>`

## 3.1 前輪 finding 閉環回報（iteration ≥ 1 必填）

R1 之後的每一輪，報告須有本節，把上一輪每一筆 `accepted` 且 `blocking` 的 finding **逐列**列出。**一列一個 `finding_id`；不得合併、不得只寫「前輪均已處理」**：

| finding_id | 處置 | 證據 |
|---|---|---|
| `<卡ID>-R<n>-<序>` | `resolved`／`withdrawn`／仍 `open` | `<可重現的重現方式或來源>` |

- **carry set 以 Issue 上的前輪 review event 為準，不以派審詞列的清單為準。** 派審詞裡的清單是便民摘要（＝次要來源，同 §1）；兩者不符時以 review event 為準，並把差異寫成 finding。**推導 carry set 所需的留痕都在 Issue 上**，所以派審詞漏列或錯列時你不必依賴它，也不必回頭問 Coordinator。
- **但先驗那些 event 讀不讀得出來——回對了權威來源不代表值解得開。** 逐項閉環之前先做前置驗證。**三個判準輸入分屬三個載體，能力差很多，別混為一談**：

  | 判準輸入 | 權威載體 | 今天的能力 |
  |---|---|---|
  | 通道健全性（marker 解析、三面一致） | `wfcli doctor --review-channel`（唯讀） | **可機械偵測** |
  | 每筆 finding 的 `accepted`／`status` | 前輪 `review` event **留言本文**的結構化區塊 | **須自行讀取比對**，`doctor` 不輸出 |
  | `contract-baseline` cutover 是否存在 | — | **今天無可讀載體，無法判定** |

  **`doctor` 的作用域邊界——別高估它**：`audit_review_channel`（`cli/src/wf_cli/doctor.py`，基線 `6e6e8ab` 時在 :312）只回**一個** review-channel 狀態，列舉值恰為 `recorded`／`receipt_untranscribed`／`unobservable`／`marker_quarantined`／`half_written`（:70–80；後兩者判在 :419／:460）。它**不輸出任何 finding 的 `accepted`／`status`，也不枚舉或驗證 `contract-baseline`**。它能證明的只有「這條通道健不健全」，**證明不了 carry set 算不算得出來**。

  - 通道：`wfcli doctor --review-channel --repo <owner/repo> --issue-number <n> --card-id <CARD_ID> --owner <owner> --project <n> --source-sha <前輪 SHA> <repo_root>`
  - 欄位：`gh api repos/<owner>/<repo>/issues/comments/<留言 id>`，逐 `finding_id` 自行比對 `accepted`／`status`（由 lifecycle writer 標記；`review-escalation.md` §2：**reviewer 不得自行決定是否消耗 escalation 額度**）。

  **分類軸不用 `contract-baseline`**：契約（`review-escalation.md` §4／§5）確以 cutover 界定 legacy，但**該軸今天沒有可讀載體**——merged main 沒有產生它的動詞，`doctor` 也不枚舉它。**沒有載體的軸不能拿來分類**，否則等於用查核者驗不了的東西決定他的義務。改用下面兩個都驗得到的判準。

  **三態，依「偵測到損壞」與「產生器不存在」劃分**：

  1. **可判定**——`doctor` 未報 `marker_quarantined`／`half_written`，且該 event 逐 `finding_id` 取得到 `accepted` 與 `status` → 依 `accepted: true` ＋ `blocking: true` ＋ `status: open` 推 carry set，照上表逐列。
  2. **已知損壞 → `review-invalid`**——`doctor` 報 `marker_quarantined` 或 `half_written`，**或**產生 `accepted`／`status` 的 writer 在被審樹裡存在而該 event 仍缺值。**明示 input 不可判定並自判 `review-invalid`**，不得當空 carry set。**缺 cutover 不是本態的赦免事由**：偵測到的損壞就是損壞，與有沒有發過 cutover 無關。
  3. **產生器系統性不存在 → 受限續行**——三件**同時**成立才可用：(i) `doctor` 未報損壞；(ii) 該 event 缺 `accepted`／`status`；(iii) **你出示得了產生它們的 writer 不在被審樹裡**（例如 `git grep -n "mark-not-accepted" -- cli/src` 無命中，且該 Issue 歷來無任何 event 帶過該欄）。**(iii) 舉不出來就落第 2 態**——「沒證明產生器不存在」不等於「產生器不存在」。本態須明示：走的是受限路徑、逐列列出報告平面看到的前輪 finding、標記其 `accepted` 未經 writer 標記且 escalation 帳無法據此推導。

  **遷移條件現在就驗得了，不是等未來合併**：第 3 態隨 (iii) 自動失效——writer 一旦出現在被審樹裡，同樣的缺值就從「系統性不存在」變成「該筆損壞」而落第 2 態。這個判準你當場跑得完，**不需要任何人宣告 cutover，也不把未來的合併當成已完成的解除**。

  **為什麼仍留第 3 態**：`accepted`／`status` 的 writer 今天不在已併入 main 的碼裡，故現階段每一筆 event 都缺這兩個值。若「缺值一律 `review-invalid`」，今天起所有 iteration ≥ 1 查核全部無效——那不是 fail-closed，是死鎖，而 `review-escalation.md` §2／§4 明文要求數個 gate **不得互相鎖死**。**但第 3 態只赦免「從來沒被產生過」，不赦免「被偵測到壞掉」**——界線由第 2 態末句釘死。

  **一條硬禁止**：**不得以 review report 的 `blocking` 欄代替 `accepted`**。`blocking` 由 reviewer 自己填、`accepted` 由 lifecycle writer 標；拿前者當後者等於讓被判定方自己決定要不要進帳。第 3 態列出前輪 finding 是**揭露**，不是替代——供人接續可以，**計入 escalation 帳不行**。

  **本前置驗證的作用域總結**：只有「通道健全性」有機械執行者（`doctor.audit_review_channel`，且僅限上列五個列舉值）。「讀 `accepted`／`status`」「出示產生器不存在」「三態的處置」**全部是約定**——`gh api` 與 `git grep` 是你手上的工具，**不是會擋你的閘門**。
- **逐列是判準的一部分，不是排版偏好**：[`review-escalation.md`](review-escalation.md) §4 逐 `finding_id` 推導 checkpoint 的格位，整體式結論映射不到任何一格，與未提及等價。
- 缺本節、或 carry set 中有 `finding_id` 未表態 → 查核者**自判** `review-invalid`，不進實質查核（處置同 §1）。
- **仍 `open` 是合法且常常正確的表態**，不是失敗；defer 延後的是評估而非結果（`review-escalation.md` §4）。把仍未解的寫成 `resolved` 才是失分。

**本節今天沒有機械執行者，故為約定而非強制。** `wfcli review` 的寫入前閘門（`cli/src/wf_cli/validation.py` 的 `validate_review_report`，基線 `6e6e8ab` 時在 :224，由 `commands/review_cmd.py:155` 呼叫；函式名才是穩定錨點，行號會隨在飛的卡位移）只驗 §5 區塊的欄位與列舉，**既不檢查本節是否存在，也不知道前輪的 carry set**。

**「iteration ≥ 1 未逐項指名前輪 accepted blocking finding 即拒寫」這個閘門目前無人承接**——請不要讀成某張卡的待辦而停止追問。`ai-workflow#9` **不涵蓋本節**：其驗收逐字為「accepted 標記寫入通道（lifecycle writer 語意）；attempt_id 去重；counts_toward_escalation 推導與 checkpoint 觸發警示」，其中第四項是 **checkpoint 漏建**閘門（上一個可計數 attempt 序位 ≥3 卻無對應 checkpoint 即 exit 2，`validation.check_checkpoint_gate`），輸入、判準與失敗模式都與「報告有沒有逐項指名前輪 finding」不同。

**被誰擋住**：該閘門的實作落點是 `review.py`／`validation.py`／`commands/review_cmd.py`，而這三個檔都在 #9 的資源宣告內，故 **#9 交付並釋出寫入集之前，任何承接卡都開不了**。需要它的人須自行舉證並開卡，不得假定已有人在做。

**本節買的是「你看得出來」，不是「有人擋著」。** 本檔的讀者就是查核者，而它就在你進駐的 repo 裡——判定本輪輸入完不完整所需的東西，你手上都有，不必問 Coordinator。但**看得出來不等於一定會去看**：2026-08-11 的兩次 checkpoint 觸發（#21 R5、#22 R2）中，兩份派審詞**都逐字寫了**逐項閉環要求，缺的是報告那一側。要把「看得出來」變成「擋得住」，需要上面那個無人承接的機械閘門；**本節不假裝自己是它**。

## 4. 環境紅線

- DB 一律唯讀（除非卡面明示）；**不得真跑爬蟲、訓練或資料重建類 CLI**。需要驗證 CLI 行為時走密封探針或容器。
- 不得改 source branch。驗證命令若會改動 tracked file，於 disposable 驗證 worktree／容器內執行（[`worktree-lifecycle.md`](worktree-lifecycle.md) §3）。
- **跨 repo 證據**：以絕對路徑 ＋ 釘住的 SHA ＋ 碼段摘錄對帳。worktree 內 submodule 目錄為空是預期（canonical §4.5）——「檔案不在我的樹裡」不構成 finding。
- 範圍外發現寫進報告的獨立一節交 PM，不自行擴大 finding 集合、不開卡。

## 5. 結構化輸出（必填）

```yaml
core_pain_resolved: yes | no       # 第一判準；no 一律 REQUEST_CHANGES
review_result: APPROVE | REQUEST_CHANGES
self_run:                          # 必填：查核者自己實際跑過的指令與觀察到的輸出
  - command: <指令>
    observed: <輸出摘要／數字>
findings:
  - finding_id: <卡ID>-R<n>-<序>
    severity: critical | major | minor | info
    blocking: true | false
    finding_class: implementation | authoritative-artifact | governance | coordination | environment
    attribution: executor | planner | coordinator | reviewer | external
    root_cause_id: <穩定根因家族；unknown 每個 finding 唯一>
    evidence: <可重現的重現方式或來源>
    disposition: <要求的修法或決策>
```

**沒有 `self_run` 的 `APPROVE` 無效**——記 `review-invalid`，不計 iteration（[`review-escalation.md`](review-escalation.md) §1）。完整 finding schema 與 `accepted`／`status` 的採認規則見同檔 §2。

## 6. R2 以後的範圍

R2 只做兩件：**R1 finding 逐項閉環驗證** ＋ **回歸不倒退**。不重跑 R1 已通過項、不擴審新範圍——擴審會讓 iteration 無法收斂，也讓 escalation 計數失義。

逐項閉環驗證要**寫成什麼形狀**見 §3.1（逐 `finding_id` 一列）。本節定範圍，§3.1 定回報格式；`review-escalation.md` §4 對 carry set 的推導同時依賴兩者。
