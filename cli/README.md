# wf-cli — 祕書 CLI 最小集（WF-22-CLI1）

> 決議 1「祕書單寫入通道」的機械化：任務狀態面遷移至 GitHub Issues/Projects v2 後，
> **本 CLI 是唯一寫入通道**。文件明示：**不經本 CLI 對 Ledger 欄位／資源宣告的狀態
> 寫入即違規**（例如直接在 GitHub UI 手改 Project 欄位）。CLI 本身不做權限強制
> （單機信任模型），紀律由治理承擔，不是技術鎖死。

## 八指令

| 指令 | 做什麼 | 讀寫 |
|---|---|---|
| `open` | 依範本開卡：建立 Issue／Project draft item ＋（可選）git spec 檔骨架；核心痛點／服務的原始目標／tier／db_scope／資源宣告／鏈深五＋一項機械檢查全過才建卡；`--chain-depth`（預設 0）> 2 依決議 5 鏈式停損協定硬拒 | 寫 |
| `assign` | 派工：寫 owner／分支worktree／交付狀態；比對本卡與其他**已認領**活卡的資源宣告交集，撞則拒絕並列出衝突卡 | 寫（有條件拒絕） |
| `handoff` | 交接：驗證 `source_sha`（完整 40 碼 hex）與證據欄非空，依 `--next-stage` 轉交付狀態、寫 owner／最後交接／iteration；`--next-stage implementation`（查核退回語意）自動 +1，`review`／`release` 不遞增，`--iteration N` 可顯式覆寫（印警示，理由寫在 `--evidence`）；`release` 且需部署卡在部署狀態 `✅已驗證` 前拒絕 | 寫（有條件拒絕） |
| `deploy-declare` | 需求方已明確裁決既有卡需要部署時，唯一允許 `—不適用 → ⏸未部署`；必填固定 `needs-deploy` decision、reason、actor，先追加真實 Issue timeline event，再只以 `updateProjectV2ItemFieldValue` 寫入部署狀態與內建 `Status=Todo`；`--dry-run` 零遠端寫入 | 寫（有條件拒絕） |
| `deploy-state` | 部署狀態只允許相鄰前進（`⏸未部署 → 🚀待部署 → ⏳部署中 → ✅已部署 → 🧪驗證中 → ✅已驗證`）；必填下一 stage owner、actor、evidence，先追加真實 Issue timeline event，再只以 `updateProjectV2ItemFieldValue` 寫入部署狀態、內建 `Status`、owner、最後交接；`--dry-run` 零遠端寫入 | 寫（有條件拒絕） |
| `review` | 查核裁決：驗 `templates/review-prompt.md` §5 結構化輸出（`review_result` 列舉、`core_pain_resolved` 必填、`self_run` 非空、finding 八欄 schema、結論與 findings 的語意一致性），過了才把裁決全文寫成 Issue 留言並轉交付狀態（`APPROVE`→`✅通過`／`REQUEST_CHANGES`→`↩退回`）；**無 `self_run` 的 `APPROVE` 記 `review-invalid` 拒收** | 寫（有條件拒絕） |
| `doctor` | 對帳：`git worktree list` vs 卡註冊、submodule 初始化、孤兒分支、殘留 lease、prunable worktree | **唯讀**，不清理 |
| `snapshot` | 匯出 Project 全部卡片為 JSON＋人類可讀 Markdown Ledger | 讀＋寫本機檔案（不寫回 GitHub） |

## 安裝與執行

```bash
cd cli
uv sync
uv run wfcli <command> --help
uv run pytest        # 全套測試（本 repo 新增；數量以此指令輸出為準）
```

## `review`：查核輸出契約的機械閘門（WF-22-CLI3）

```bash
# 查核者送審前自檢：只驗格式，完全不連 GitHub
wfcli review WF-22-CLI3 --input report.md --source-sha <40hex> --reviewer Codex --validate-only

# 祕書寫入裁決（真實副作用需 --repo）
wfcli review WF-22-CLI3 --repo ruan6047/ai-workflow --input report.md \
  --source-sha <40hex> --reviewer Codex
cat report.md | wfcli review WF-22-CLI3 --repo ... --source-sha <40hex> --reviewer Codex
```

`--input` 吃**整份查核報告**（散文＋圍籬區塊），自動抽出含 `review_result` 的
```` ```yaml ````／```` ```json ```` 區塊；抽到兩個以上一律拒收（不用「取最後一個」
這種順序啟發式猜哪個是裁決）。退出碼：

- `0` 通過並已寫入（或 `--validate-only` 驗證通過）
- `2` 讀不到／解析失敗／契約檢查失敗（含 `APPROVE` 帶 blocking finding、
  `REQUEST_CHANGES` 零 finding 兩條硬拒）／缺必要旗標——**未寫入任何遠端狀態**
- `3` 找不到卡
- `4` `review-invalid`（`templates/review-escalation.md` §1）：目前可機械判定的是
  「`APPROVE` 未附 `self_run`」；§1 規定此情形留在 `🔍待查核`、不計 iteration，
  所以刻意什麼都不寫

## 跨專案目標指定

```bash
wfcli open --owner ruan6047 --project 4 CARD-ID ...      # 明打旗標
wfcli open --config .wfcli.json CARD-ID ...               # 讀設定檔 {"owner":...,"project":...,"repo":...}
WFCLI_OWNER=ruan6047 WFCLI_PROJECT=4 wfcli open CARD-ID    # 環境變數
```

`--repo owner/repo` 有給時，`open` 建立**真實 repo Issue**（`gh issue create` + `gh project
item-add`）；未給則建立**Project draft issue**（無 repo 掛載，`gh project item-create`）。
兩種模式的 Ledger 欄位讀寫、資源宣告解析、`assign`／`handoff` 邏輯完全一致。

## 凍結欄位結構（`OPS-STATE-PLANE-MIG1` Task 1 + 需求方裁決）

13 個 Ledger 欄位對照 GitHub Project custom fields（`src/wf_cli/project.py::FIELD_SPECS`
是唯一事實來源，`ensure_fields` 冪等建立缺少的欄位）：

- TEXT：卡ID、Initiative、功能、owner、分支worktree、最後交接、服務的原始目標、資源宣告（摘要）
- NUMBER：iteration、鏈深
- SINGLE_SELECT：級別（T0–T4）、交付狀態（13 值，含 canonical §0 全集＋實務常見值）、部署狀態（7 值）

**最後交接**＝TEXT 完整 ISO-8601（`isoformat(timespec="seconds")`，例如
`2026-08-04T22:47:51+08:00`）：字典序即時序，不用 DATE（其 API 層會靜默截斷時分秒）。

**資源宣告**的 machine-of-record 是卡片 body 內固定的 `## 資源宣告` 區塊：

```
## 資源宣告
<!-- resource-claims:begin -->
```json
{"db_scope": "write", "resources": ["file:a.py", "port:8080"]}
```
<!-- resource-claims:end -->
```

Project 上的「資源宣告」TEXT 欄位只放人類可讀摘要，不參與 `assign` 的交集比對；
機械比對一律解析 body（`src/wf_cli/resources.py`）。刻意不用 `MULTI_SELECT`（GitHub
GraphQL schema 確實存在但未文件化、`gh` CLI 未曝露，见 Task 1 field-mapping 文件的
「意外發現」節）。

## 設計取捨（讀程式碼前建議先看這裡）

- **`assign` 的資源衝突比對範圍限定「已認領」的活卡**（owner 不是「待指派」等佔位
  字串）。單純兩張卡都在 Backlog、都規劃碰同一檔案，不會互相卡住——真正的風險是
  「兩張卡同時有人在執行」，這才是 worktree／資源撞車的實際情境。
- **`doctor` 是唯讀報告工具，不做任何清理／回收**。卡面紅線 3 要求破壞性操作「先列
  清單再執行」；本卡刻意把「列清單」與「執行清理」拆成兩個決策點，v1 只做前者。
- **`doctor` 的孤兒 worktree 判準**：`git worktree list --porcelain` 逐一分類——
  `prunable` 直接算孤兒；`detached` 但非 prunable 視為查核用 disposable worktree
  （worktree-lifecycle.md §3 認可的型態），**不**算孤兒；其餘依分支名稱比對卡註冊
  （TASKS.md Ledger 或 GitHub Project），對不上才算孤兒。這代表 doctor 找到的孤兒是
  「未見於任何活卡登記」，不是「保證真的沒人在用」——例如一個尚未正式開卡、但有人
  正在裡面工作的暫時性 worktree，也會被列出來，這是刻意的（見下方「已知限制」）。
- **殘留 lease 是啟發式，不是判決**：(a) 註冊的 worktree 路徑在磁碟上不存在＝機械
  確定的訊號；(b) 最後交接超過可設定的 TTL（預設 48h）＝時間啟發式，只供人工判斷，
  不觸發任何自動回收。
- **`deploy-declare` 是既有卡部署分類的唯一更正入口**：只在需求方明確決策後使用，
  固定要求 `--decision needs-deploy` 與非空 `--reason`，且只允許
  `—不適用 → ⏸未部署`。它不是 `deploy-state` 的跳轉例外；其餘重分類、重複宣告、
  跳級與倒退全數拒絕。新卡仍由 `open --needs-deploy` 決定初始分類。
- **`deploy-state` 是部署狀態的唯一中間轉移入口**：它只允許
  `⏸未部署` 後的相鄰前進轉換。
  內建 `Status` 固定映射為 `⏸未部署`／`🚀待部署`→`Todo`、
  `⏳部署中`／`✅已部署`／`🧪驗證中`→`In Progress`、`✅已驗證`→`Done`；Project
  缺少對應 option 一律拒絕，不以色彩或順序猜測。命令不建立或修改任何 Project
  欄位定義，所有 item 值都走 `updateProjectV2ItemFieldValue`。需要真實 repo Issue，
  draft item 直接拒絕，避免失去 timeline event。
- **`doctor` 的卡註冊來源可插拔**（`--registry tasks-md|none`）：`tasks-md` 解析
  `docs/TASKS.md`／`TASKS.md`（未 cutover 專案的現行事實來源）；未來完全 cutover 的
  repo 可改用 GitHub Project 作為登記來源（`src/wf_cli/registry.py` 留了擴充點，
  v1 未實作 `github` 模式，因為本卡驗收的唯讀對帳目標——cpbl-analytics——尚未
  cutover，`tasks-md` 已足夠覆蓋卡面驗收）。
- **鏈深與 iteration 的寫入路徑**（WF-22-CLI2）：`open --chain-depth` 與 `handoff`
  的 iteration 遞增在 CLI1 交付時只有底層 `set_field_value` 能寫、組裝層沒接，兩個
  凍結欄位形同虛設 0。`--chain-depth`＝原始目標之下第幾層，> 2 依決議 5「鏈式停損
  協定」在 `validation.validate_chain_depth`（CLI 層）與 `Card.__post_init__`（model
  層，供繞過 CLI 直接建構 Card 的呼叫端）雙重擋下，訊息固定引用「整鏈重審」與
  「決議 5」（`card.chain_depth_violation_message`，兩層共用同一段文字避免漂移）。
  iteration 遞增接點依需求方 2026-08-05 裁決：`handoff --next-stage implementation`
  （承載「查核退回」語意）讀回現值＋1 寫回；`review`／`release` 不遞增；`--iteration
  N` 是顯式覆寫逃生門（印警示，覆寫理由說明於既有必填的 `--evidence`，不另立欄位）。
- **`review` 不碰 iteration／owner／最後交接**（WF-22-CLI3）：iteration 的唯一遞增點
  是 `handoff --next-stage implementation`，review 若也動就會讓一次退回被記成兩次；
  裁決也不是交接，所以 owner 與最後交接同樣留給 `handoff`。`review` 只寫兩件事——
  Issue 留言（裁決全文；canonical §4.3「事件＝Issue timeline ＋結構化 comment」）與
  交付狀態，另在 body `## Log` 補一行索引。
- **`review` 先留言、後翻狀態**：反過來若留言失敗，板上會留下沒有裁決全文的
  `✅通過`，那正是本卡要消滅的「宣稱與證據脫節」。
- **`APPROVE` 不得含 `blocking: true` 的 finding**（硬拒，exit 2）：有阻斷缺陷卻核可
  是語意矛盾，二擇一——改 `REQUEST_CHANGES`，或把該 finding 改為 `blocking: false`。
  需求方 2026-08-06 裁決（[`ruan6047/ai-workflow#8`](https://github.com/ruan6047/ai-workflow/issues/8) 查核留言），由警示升為硬拒。
- **`REQUEST_CHANGES` 不得零 finding**（硬拒，exit 2）：退回必須附至少一項可執行
  finding，否則執行者無從修起。與「`findings` 鍵須顯式存在」的互動：顯式寫
  `findings: []` 搭配 `REQUEST_CHANGES` 現在同樣被擋（顯式不等於豁免）。
  需求方 2026-08-06 裁決（[`ruan6047/ai-workflow#8`](https://github.com/ruan6047/ai-workflow/issues/8) 查核留言）。
  兩條的判準都在 `validation.validate_review_report`，且只在 finding 本身解析乾淨時
  才判——否則作者會同時看到「缺欄」與由缺欄衍生的矛盾訊息，被導去修錯的地方。
- **`review` 自己寫受限 YAML 子集解析器，不引 PyYAML**：除了零第三方 runtime 相依，
  更關鍵的是寬鬆解析與 fail-closed 互斥——YAML 1.1 會把 `yes` 讀成布林、重複鍵靜默
  取最後一個。這裡只認 review-prompt.md §5 已經在用的固定子集（頂層純量、`- key:
  value` mapping 序列、`[]`、`|`／`|-` 區塊純量），語法之外一律拒收；```json 區塊走
  `json.loads`，兩條路徑收斂到同一套契約檢查。
- **`review` 的行內註解規則**：`key:   # 說明` 與 `review_result: APPROVE  # 說明`
  這種「整段註解」或「單 token ＋註解」會切掉註解（範本每行都帶註解，照抄填值是最
  常見用法）；但**片語後接 `' #'` 一律拒收**（`evidence: 見 PR #12` 若照 YAML 砍註解
  會靜默截成 `見 PR`——截斷的 audit 記錄比被拒收糟），要求作者加引號。

## 已知限制

- `doctor` 無法分辨「未登記的 worktree」是真孤兒還是「有人正在用、只是還沒開卡」；
  這需要人類或另一層「哪些 session 目前存活」的資訊，本 CLI 不越權猜測。
- `assign`／`handoff` 對別卡（非本次目標卡）解析不出資源宣告時只警告、不擋——遷移期
  間舊卡尚未補宣告不該讓新卡整個卡死；目標卡自己解析失敗則直接拒絕（fail closed）。
- 目前只有 `open` 會做「重複卡ID」檢查；`assign`／`handoff` 找不到卡ID時回報「找不到
  卡」（exit 3），不會嘗試模糊比對或自動建卡。
- `review` 只能機械判定 `review-escalation.md` §1 六種 `review-invalid` 中的**一種**
  （`APPROVE` 未附 `self_run`）。查核順序、環境污染、reviewer 獨立性、審錯 artifact、
  同一 reviewer 對同一 SHA 重複回報都需要 CLI 拿不到的事實，由 Coordinator 判定——
  本指令不假裝能判定，但也不因此放行。
- `review` **不計算 `counts_toward_escalation`、不標記 `accepted`／`status`**
  （§2／§3 規定由 lifecycle writer 依可重現證據標記，reviewer 不得自決）；查核輸出裡
  出現這些 writer-only 欄位只會被警示並忽略。escalation 帳（epoch、attempt 去重、
  checkpoint）目前仍在 CLI 之外。
- `review` 只擋格式與契約，**不驗查核者的獨立性**（跨模型家族／人工）——`--reviewer`
  是自陳字串。canonical §5 的獨立性紅線仍由治理承擔。
- `review` 需要真實 repo Issue（`--repo`）：Project draft item 沒有 timeline 可留言，
  會被拒絕而不是退化成「只翻板狀態」。

## 專案結構

```
cli/
├── pyproject.toml
├── src/wf_cli/
│   ├── gh.py            # gh CLI／graphql 底層包裝（唯一 subprocess 出口）
│   ├── project.py        # Projects v2 adapter：欄位、item 建立、批次讀取
│   ├── resources.py      # 資源宣告 schema、fenced JSON 解析／渲染、交集比對
│   ├── review.py          # 查核輸出結構：區塊抽取、受限 YAML 子集解析、裁決留言渲染
│   ├── card.py           # Card model、spec／Issue body 範本渲染、Log 附加
│   ├── validation.py      # SHA／證據／必填欄／查核輸出契約的機械檢查
│   ├── registry.py        # TASKS.md Ledger 解析（doctor 的卡註冊來源）
│   ├── git_ops.py         # 唯讀 git worktree／submodule／branch 操作
│   ├── doctor.py          # 對帳邏輯（組合 git_ops + registry）
│   ├── snapshot.py        # JSON／Markdown Ledger 渲染
│   ├── config.py          # --owner/--project/--repo/--config 目標解析
│   ├── cli.py             # argparse 組裝＋錯誤處理
│   └── commands/          # 六個子指令的 argparse handler
└── tests/                  # pytest：純邏輯＋真實 sandbox git repo＋FakeGhRunner（數量見 uv run pytest）
```
