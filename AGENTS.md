# AGENTS.md — ai-workflow 專案 AI 運行準則

本 repo 是**跨專案 AI 協作治理的 canonical 來源**。它**受自己定義的機制管理**（dogfooding）。

## L0 · 進來先讀這三塊，其餘用查的

⛔ **不要通讀 canonical。** 入門只有三塊：

1. [`AI_WORKFLOW.md`](AI_WORKFLOW.md) **§1 角色與所有權**；
2. [`AI_WORKFLOW.md`](AI_WORKFLOW.md) **§2 不可違反的規則**；
3. 下面那張一分鐘心智模型。

§1／§2 就排在 §0 之前，⛔ 不需要先捲過分類與狀態表。canonical 的其餘節次是**查詢對象**，⛔ 不是入門讀物。

### 一分鐘心智模型

- **規則本體＝ [`AI_WORKFLOW.md`](AI_WORKFLOW.md)**（唯一權威）。衝突時以它為準；程式碼與文件衝突時以程式碼為準。
- **一件事一張卡**；卡由待審清單項升級而來（`wfcli open --from-issue` 是唯一路徑），收件條件見 [`stage-rules/list-intake-requirements.md`](stage-rules/list-intake-requirements.md)。
- **狀態面唯一寫入通道＝ `wfcli`**（[`cli/README.md`](cli/README.md)）。不經它的狀態寫入即違規。
- 每個階段跑同一個五步迴圈：① 印注意事項 → ② 派工 → ③ 交回 → ④ 對完整性 → ⑤ 路由。
- **`stage-rules/＝八份 SOP，① 印給你、③ 逐條回`**——八份指八個階段（需求／研究／規劃／執行／審核／部署／維護／結案）各一份；同目錄另有三份角色準則（PM／執行者／查核者）與一份清單收件條件，那四份不是階段檔。
  ⚠️ 「① 印給你」的**機械列印尚未生效**（機制歸 `WF-REDESIGN-W3`；沿 canonical §0.1 先例，⛔ 不啟用尚無 writer 的規則）。在那之前 ① 由 PM 人工交出該階段 §5 的編號清單，③ 的逐條回應照跑。
- **交接一律走 [`templates/`](templates/) 的範本**：派工包／交付報告／派審詞／裁決／狀態變更裁定單，共用同一個四段信封（定義在 [`templates/handoff-contract.md`](templates/handoff-contract.md) §3.3）。

### 現況要用查的

⛔ 入口不指向會變的東西。活卡、SOP 與範本清單一律查：

```bash
gh project item-list 4 --owner ruan6047        # 本 repo 的活卡（狀態面）
ls stage-rules/ templates/                     # SOP 與交接範本的實況
```

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

卡面只寫**能力層級**、⛔ 不寫模型名——模型名單會過期，層級才是穩定介面。合法值三個：**經濟型／主力型／高階型**（值域與判準見 [`MODEL_ROUTING.md`](MODEL_ROUTING.md) 與 [`tier-rules.md`](tier-rules.md)；`wfcli open` 以 `--exec-capability`／`--review-capability` 機械強制，缺欄即拒絕開卡）。

本 repo 幾乎全是文件治理，判準逐條在 [`CLAUDE.md`](CLAUDE.md) 的「模型路由」節（工具中立的讀者照同一組判準：純機械文字＝經濟型；要讀懂既有條文才改得動、語意收斂在單一檔或單一動詞＝主力型；動到 `AI_WORKFLOW.md` 條文、跨模組語意、根因不明或不可逆＝高階型）。

規則正確性屬紅線：不論選哪一層，查核**必換模型家族或由使用者 sign-off**。
