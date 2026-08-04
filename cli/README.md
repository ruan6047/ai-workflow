# wf-cli — 祕書 CLI 最小集（WF-22-CLI1）

> 決議 1「祕書單寫入通道」的機械化：任務狀態面遷移至 GitHub Issues/Projects v2 後，
> **本 CLI 是唯一寫入通道**。文件明示：**不經本 CLI 對 Ledger 欄位／資源宣告的狀態
> 寫入即違規**（例如直接在 GitHub UI 手改 Project 欄位）。CLI 本身不做權限強制
> （單機信任模型），紀律由治理承擔，不是技術鎖死。

## 五指令

| 指令 | 做什麼 | 讀寫 |
|---|---|---|
| `open` | 依範本開卡：建立 Issue／Project draft item ＋（可選）git spec 檔骨架；核心痛點／服務的原始目標／tier／db_scope／資源宣告五項機械檢查全過才建卡 | 寫 |
| `assign` | 派工：寫 owner／分支worktree／交付狀態；比對本卡與其他**已認領**活卡的資源宣告交集，撞則拒絕並列出衝突卡 | 寫（有條件拒絕） |
| `handoff` | 交接：驗證 `source_sha`（完整 40 碼 hex）與證據欄非空，依 `--next-stage` 轉交付狀態、寫 owner／最後交接；`release` 且需部署卡在部署狀態 `✅已驗證` 前拒絕 | 寫（有條件拒絕） |
| `doctor` | 對帳：`git worktree list` vs 卡註冊、submodule 初始化、孤兒分支、殘留 lease、prunable worktree | **唯讀**，不清理 |
| `snapshot` | 匯出 Project 全部卡片為 JSON＋人類可讀 Markdown Ledger | 讀＋寫本機檔案（不寫回 GitHub） |

## 安裝與執行

```bash
cd cli
uv sync
uv run wfcli <command> --help
uv run pytest        # 98 個測試，本 repo 新增
```

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
- **`handoff` 只驗證 release 的部署閘門，不管理部署狀態的中間轉移**
  （`🚀待部署→⏳部署中→✅已部署→🧪驗證中→✅已驗證` 由各專案自己的部署管線
  負責）；`open --needs-deploy` 只設定初始值 `⏸未部署` vs `—不適用`。
- **`doctor` 的卡註冊來源可插拔**（`--registry tasks-md|none`）：`tasks-md` 解析
  `docs/TASKS.md`／`TASKS.md`（未 cutover 專案的現行事實來源）；未來完全 cutover 的
  repo 可改用 GitHub Project 作為登記來源（`src/wf_cli/registry.py` 留了擴充點，
  v1 未實作 `github` 模式，因為本卡驗收的唯讀對帳目標——cpbl-analytics——尚未
  cutover，`tasks-md` 已足夠覆蓋卡面驗收）。

## 已知限制

- `doctor` 無法分辨「未登記的 worktree」是真孤兒還是「有人正在用、只是還沒開卡」；
  這需要人類或另一層「哪些 session 目前存活」的資訊，本 CLI 不越權猜測。
- `assign`／`handoff` 對別卡（非本次目標卡）解析不出資源宣告時只警告、不擋——遷移期
  間舊卡尚未補宣告不該讓新卡整個卡死；目標卡自己解析失敗則直接拒絕（fail closed）。
- 目前只有 `open` 會做「重複卡ID」檢查；`assign`／`handoff` 找不到卡ID時回報「找不到
  卡」（exit 3），不會嘗試模糊比對或自動建卡。

## 專案結構

```
cli/
├── pyproject.toml
├── src/wf_cli/
│   ├── gh.py            # gh CLI／graphql 底層包裝（唯一 subprocess 出口）
│   ├── project.py        # Projects v2 adapter：欄位、item 建立、批次讀取
│   ├── resources.py      # 資源宣告 schema、fenced JSON 解析／渲染、交集比對
│   ├── card.py           # Card model、spec／Issue body 範本渲染、Log 附加
│   ├── validation.py      # SHA／證據／必填欄機械檢查
│   ├── registry.py        # TASKS.md Ledger 解析（doctor 的卡註冊來源）
│   ├── git_ops.py         # 唯讀 git worktree／submodule／branch 操作
│   ├── doctor.py          # 對帳邏輯（組合 git_ops + registry）
│   ├── snapshot.py        # JSON／Markdown Ledger 渲染
│   ├── config.py          # --owner/--project/--repo/--config 目標解析
│   ├── cli.py             # argparse 組裝＋錯誤處理
│   └── commands/          # 五個子指令的 argparse handler
└── tests/                  # 98 個 pytest（純邏輯＋真實 sandbox git repo＋FakeGhRunner）
```
