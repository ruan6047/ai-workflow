# AGENTS.md — ai-workflow 專案 AI 運行準則

本 repo 是**跨專案 AI 協作治理的 canonical 來源**。它**受自己定義的機制管理**（dogfooding）。

> **規則本體＝ [`AI_WORKFLOW.md`](AI_WORKFLOW.md)**（唯一權威）。本 repo 的任務狀態面＝GitHub Project #4（`gh project item-list 4 --owner ruan6047`）；`TASKS.md` 已停用封存。

## 在本 repo 工作時
- 改規則（`AI_WORKFLOW.md`）＝一張任務卡：**開分支 `ai/<模型@工具>/<卡ID>` → 獨立審核（≠ 執行者）→ merge main**。規則屬「錯了影響全專案」→ 視為 **🔴紅線**，審核**必換模型家族或使用者 sign-off**。
- 規則更新後**不需同步各專案**（各專案只放指向本檔的 stub、不複製全文）。
- T0/T1 commit 至少加 `Requested-by / Implemented-by`；T2 以上實作 commit 加 `Requested-by / Planned-by / Implemented-by`；merge、PR 結案或權威文件核可紀錄再加 `Reviewed-by`（見 AI_WORKFLOW §6）。

## commit trailer

trailer 是 `docs/ROADMAP.md` §1 那兩個身分維度（**角色**＋**模型**）的 commit 形式。
執行面是**完整性檢查**——欄位有沒有填、能不能被 `git interpret-trailers --parse` 解析出來。
**不驗證「他真的是他」**：本 repo 的人類、PM、執行者、查核者共用同一個 GitHub 帳號，
那種檢查恆真（ROADMAP §1）。值一律當**宣稱**收下。

### 檢查器（唯讀，**不阻擋任何 push／merge**）

```bash
wfcli doctor <repo> --registry none --commit-trailers --commit-range origin/main..HEAD
# 稽核整段歷史（含界線前）：加 --trailer-epoch none
# 明知該範圍是 T2 以上：加 --require-planned-by
```

實作在 `cli/src/wf_cli/doctor.py`（`audit_commit_trailers`）。它**只是偵測器**：
跑了才看得到，不在 push 路徑也不在 merge 路徑上，因此**擋不住任何一次違規的落地**。
最接近執行面的是 CI（`DEV-AIWF-MINIMAL-CI1`，#48，持有 `.github/workflows/`），
但依 `docs/ROADMAP.md` §2，**#48 本身也擋不了人**：CI 產生的是紅叉，紅叉要變成閘門
需要 repo 的 `required_status_checks` ruleset，而 repo setting 不是檔案、不在任何
寫入集的值域裡。**牙齒長出來的時點是 ruleset 套用那一刻。** 在那之前，本節寫的是
**約定**，不是強制。

判定摘要（判準全部從 commit 自身導出，不依賴人工標註）：

- **實作 commit**（含 root commit、cherry-pick）：必須解析得出 `Requested-by` ＋
  `Implemented-by`。這是 T0/T1 與 T2 要求的交集，故不需知道卡的級別（級別在卡面、
  不在 commit 裡）。`Planned-by` 只有 T2 以上要求，**預設只回報不判違規**。
- **merge commit**：combined diff（`git diff-tree --cc`）為空者不是實作 commit
  ——tree 由 parent 完全解釋得出，沒有自己著作的內容；但 §6 仍要求 `Reviewed-by`。
  combined diff 非空者（衝突解法／evil merge）**照實作 commit 辦**，堵掉「把改動
  塞進 merge commit」這條規避路徑。**基線更新 merge 不另立一格**：它與整合 merge
  都只是 `parents >= 2`，誰是 main 取決於站在哪個 ref 上看，導不出來就不假裝導得出來。
- **cherry-pick**：不設特例。`-x` 是選配，沒帶就與原生 commit 無法區分，認不出來
  就 fail-closed。代價為零——訊息連同 trailer 一起複製。
- **空 commit**：不是實作 commit（沒有著作內容就沒有來歷要宣告）。逐 commit 獨立
  判定、**不繼承**：一筆帶齊 trailer 的空 commit 不會讓它前面那筆裸的 commit 變綠。
  既成歷史要不要**採認**那種補記是規則層裁定，檢查器不代為裁定。
- **分流界線** `2026-08-13T00:00:00+08:00`（committer date，`doctor.TRAILER_GUARD_EPOCH`）：
  之前的 commit 列為「界線前」、不計違規——補它只能改寫已推送歷史，本專案禁止，
  那種 finding 沒有人被允許修。界線是分流輔助，**不是安全邊界**（`GIT_COMMITTER_DATE`
  可任意設定）。

### 根因家族名（裁定，2026-08-12）

本缺陷家族的 canonical `root_cause_id` ＝ **`commit-trailer-required-but-missing`**。
後續查核者引用此名，不再各給一個。取此名的理由：它已是既有事件裡的多數用法（4 張卡
中 2 張），且它命名**可觀測的事實**（必填 trailer 缺席）而非成因判斷，重新診斷時不必改名。

**只約束未來。** 已寫入的事件不追溯改寫（本專案紅線）。下表是**唯讀對照紀錄**，
讓後來的人看得出它們是同一族，而不是三件各發作一次的事：

| 出現處 | 曾用名 |
|---|---|
| #39 R3-001、#47 R1-002 | `commit-trailer-required-but-missing`（即 canonical） |
| #52 R1-001 | `governance-provenance-trailer-omission` |
| #48 R2-002 | `unknown-DEV-AIWF-MINIMAL-CI1-R2-002`（佔位字串） |

⚠️ **統一命名本身不會讓升級門檻數到 3**，別這樣宣稱。`templates/review-escalation.md:50`
把 attempt 定義為 `(card_id, escalation_epoch, source_sha)`，`:73` 的累計限於「本 epoch」
——四張不同卡的 finding 本來就不會相加，與叫什麼名字無關。且 `:40` 把 trailer 明列為
`governance` 類，而 `:57` 明文排除純 `governance` finding 消耗 escalation 額度。
統一命名的真實價值是**同一張卡內**的重複可被辨識，以及人讀得出跨卡的復發。

## 模型路由
本 repo 幾乎全是文件治理：規劃/改規則屬架構層 → Opus/Fable；純文字修訂 → Sonnet/Haiku。查核紅線（規則正確性）→ 換家族或人審。
