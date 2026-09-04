# #151 WF-CLI-ENSURE-FIELDS-DOUBLE-READ1 每個 wfcli 寫入動詞都跑兩次 list_fields，第二次無條件、各 102 點／4-5 秒
- state: closed  created: 2026-08-26T03:49:46Z  closed: 2026-08-26T10:57:34Z
- url: https://github.com/ruan6047/ai-workflow/issues/151
- comments: 5

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；改動極小但落在每個寫入動詞的共用前置：若回傳的欄位 metadata 不完整，open/amend 會寫到錯的 field id 而**不報錯** ⇒ 須能自己看出「零建立」與「有建立」兩條路徑的回傳必須等價，⛔ 非機械替換。）　查核：待指派（建議 高階型；動的是所有寫入動詞共用的前置，失敗模式是**靜默寫錯欄位**而非拋錯；查核者須獨立設計「有建立」路徑的驗證（該路徑在正常環境構造上跑不到，需刻意造欄位缺失），⛔ 不得只驗零建立情境。）
- Initiative：—　spec 基線：cd17ba5f0bda377a0bcdbf542932e6a977f7c409
- DB：db_scope=none
- 服務的原始目標：ROADMAP §0 目標 2「可稽核的內容」的前提條件——稽核與回填都是批次操作，而每小時 23 次的天花板讓任何全母體操作都必須跨額度視窗切分，切分本身會產生「跑到一半」的中間狀態。

## 簡介
<!-- card-brief:begin -->
消除 wfcli 寫入動詞前置的重複欄位查詢。**適用時機**：抱怨 wfcli 動詞慢或吃額度時；或要改 project.py 的欄位快取時。⛔ 非射程：不改 list_items、不改欄位快取策略、不動任何動詞的呼叫點、⛔ 不順手改 FIELD_SPECS。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：**`project.ensure_fields` 每次都呼叫 `list_fields` 兩次，而第二次在零建立情境下是純浪費——它佔單次寫入動詞 GraphQL 點數成本的 94%、牆鐘 10.41 秒中的一半。** 碼結構：`:175` 先 `existing = list_fields(...)`，中間依 `FIELD_SPECS` 逐項建立缺欄位，`:188` 無條件 `return list_fields(...)`。⇒ **當迴圈一個欄位都沒建立時，第二次查詢必然回傳與第一次逐位元相同的結果。** 實測（2026-08-26，origin/main `cd17ba5`，以 monkeypatch 攔截 `list_fields` 並前後取 `gh api rate_limit` 的 graphql.remaining 相減）：`list_fields#1` **102 點／5.12 秒**、`list_fields#2` **102 點／4.06 秒**、合計 **204 點／10.41 秒**；同一次量測 `list_items` 只要 **7 點／11.34 秒**。⇒ 一次寫入動詞約 211 點中有 **204 點來自這一支**，而 GitHub GraphQL 額度是 5000/小時 ⇒ **每小時只能跑約 23 次寫入動詞**。⚠️ 這個上限已經在限制實際工作：`WF-CARD-BRIEF-BACKFILL1` 要在 190 張卡上跑 `amend --brief`，照現況需跨越 9 個額度視窗。⭐ 而修法的射程比那張卡小得多——⛔ 不是「加快取」，是**在零建立時回傳已經拿到的那份**。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/project.py",
    "file:cli/tests/test_project_mocked.py",
    "file:cli/tests/fake_gh.py",
    "file:cli/tests/ensure_fields_oracle.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] ⚠️ 本清單於 2026-08-26 依 30 輪研究輪填實（開卡時刻意留白）。⭐ **射程已由需求方裁定擴大為乙案**（`issuecomment-5420717647`）：納入「換原生 GraphQL 查詢」。
- [ ] **A0 ⛔ 卡面 `功能` 欄有一句是假的，且機械上改不動 —— 執行者與查核者一律以本清單為準。** `功能` 逐字寫「**每個** wfcli 寫入動詞都跑兩次 `list_fields`」。**假**：實查 `ensure_fields` 的呼叫者只有 `open`／`amend`／`assign`／`handoff`／`review` **5 個**（214 點）；`deploy-declare`／`deploy-state` 走**單次**（112 點）、`checkpoint` **付 0**。⭐ 而 `docs/WF_EVENT_IDEMPOTENCY1.md` §7.1 **已機械修正過一模一樣的錯**（逐字：「『所有寫入動詞共用的一個注入點』兩處都不成立」）⇒ 同一形狀第二次。⚠️ 成因是 PM 開卡時把未驗的結構宣稱寫進身分欄（`open` 有 8 個身分旗標而 `amend` 有 0 個 ⇒ 改不動）。
- [ ] **A0b ⛔ 開卡時寫的「有建立那條在正常環境構造上跑不到」也是假的。** 既有測試套件**已跑它 219 次**（`FakeGhRunner` 專案預設為空），共建 3,285 欄 ⇒ 「刻意造欄位缺失」的機制早就存在且是預設行為。
- [ ] **A1** `ensure_fields` 在**零建立**（迴圈一次 `field-create` 都沒送出）時，不得再發第二次 `list_fields`，回傳值即第一次查詢的結果。⛔ **以符號指認、不寫行號**：`ensure_fields` 內的 `existing = list_fields(...)` 與函式末的 `return list_fields(...)`。理由：`WF-POSTHOC-CONFORMANCE1` 已獲授權對同檔 `ItemSnapshot`（排在 `ensure_fields` **之前**）加欄，落地當下行號即失準。
- [ ] **A2** **有建立**時的回傳，必須與「該次呼叫結束後重新讀取一次」**逐位元相同**，含每個 `FieldMeta` 的 `id`、`type`、以及 `options` 內每個 option 的 id。⛔ **鍵集合相同不算通過**——研究輪實測 off-by-one 錯位與 option id 全錯兩種變異的鍵集合與型別都與正確版相同，既有 `test_ensure_fields_creates_all_frozen_fields` 對兩者全綠。
- [ ] **A3** `FIELD_SPECS` 逐字不動。非 `FIELD_SPECS` 的既有欄位（GitHub 內建 Title／Status／…；真實 Project #4 上 29 欄中有 16 欄屬此類）在兩條路徑上都必須原樣出現在回傳中，型別判定沿用現行 `list_fields` 的 `ProjectV2SingleSelectField` fallback。
- [ ] **A4** 五個呼叫點（`open_cmd`／`amend_cmd`／`assign_cmd`／`handoff_cmd`／`review_cmd`）**一行不改**；`deploy_declare_cmd`／`deploy_state_cmd` 的單次 `list_fields` 與 fail-closed 語意不變；`amend --dry-run` 的分流不變（其負控 `test_amend_dry_run_never_creates_project_fields` 須維持綠）。
- [ ] **A5** 交付須載明修法後的**實測**單次點數，與對 `WF-CARD-BRIEF-BACKFILL1` 母體（附量測時刻與張數）的額度視窗數。⭐ **判準**：乙案落地後 189 張須降到 **1 個視窗**。⚠️ 若只做到消除第二次呼叫（9→5 視窗），須**明說本卡未達成卡面的服務的原始目標**（切分產生的中間狀態不因此消失），`service_goal_still_served` 標 `no`。⭐ `aiwf#147` A7 的同一句錯誤宣稱已於 2026-08-26 更正完畢。
- [ ] **A6** 修法採 **C1（條件分支：零建立時回傳已取得的那份）**，⛔ 不採 C3（解析 `field-create --format json` 回傳併入）——需求方裁定，理由：有建立路徑在生產是死碼，C3 的額外收益幾乎全在測試環境卻引進跨版本相依。
- [ ] **A7 ⭐ 乙案本體：以原生 GraphQL 查詢取代 `gh project field-list`。** `node(id:$projectId){... on ProjectV2 { fields }}`，`list_fields` 簽章向後相容（新增選填 `project_id`，缺省時內部 `resolve_project`），**呼叫點一行不動**；須處理 `fields` 的分頁（`pageInfo.hasNextPage`）。依據：實測原生 **2 點／0.55 秒** vs `gh project field-list` **102 點／4.4 秒**，且對真實 Project #4 **逐位元等價**（29 欄含 option id）。根因：gh CLI `queries.go:1048` 把 `firstItems` 寫死 100 ⇒ 查欄位順便抓 100 items × 100 fieldValues，**102 點是結構常數、與 Project 規模無關**（實測 `-L 100/30/20` 與空專案全部 102）。
- [ ] **A8 ⛔ 明文非射程與必須揭露的限制**：⛔ 不改 `list_items` 的呼叫次數、⛔ 不改欄位快取策略、⛔ 不動 `ensure_fields` 以外的呼叫點。⚠️ **原生查詢在 org-owned Project 的等價性驗不了**（`ruan6047` 名下無 organization，`gh` 實測回 `organization: null`，環境上無樣本）⇒ 交付**必須逐字揭露**，⛔ 不得宣稱「已驗證等價」。
- [ ] **A9 序位**：⛔ 開工前 `WF-POSTHOC-CONFORMANCE1`（`aiwf#138`）須到 **🏁完成**。兩卡宣告字串完全相同 ⇒ `assign` 硬退，且 `TERMINAL_STATUSES` 只有 `🏁完成`／`🛑已停止`（走到 `📦已合併` 仍擋）。

## 驗證

- [ ] ⚠️ 本清單依 30 輪研究輪填實。⭐ **V2 是本卡唯一構造上會抓到錯的驗證** —— 其餘多為等價性與回歸。
- [ ] **V1 差分預言，覆蓋既有全部呼叫點**：加一層測試期包裝，對每一次 `ensure_fields` 的回傳 R 立刻重讀 `list_fields` 得 F，斷言 `R == F`（dataclass 逐欄比對，⛔ 非鍵集合）。研究輪實測既有套件會觸發 **466 次** `ensure_fields`（**219 次有建立**／247 次零建立）⇒ 這一條免費拿到 466 個斷言。交付須附**觸發次數與兩條路徑各自的次數**的原始輸出，⛔「有加測試」不算。
- [ ] **V2 變異檢驗，⛔ 不得省**：至少三個錯誤實作須讓 V1 轉紅，逐一附輸出——M1 無條件 `return existing`；M2 把 `field-create` 回傳掛到**上一個**欄位名下（off-by-one）；M3 option id 全填第一個選項的 id。並須**明說**：研究輪實跑證實 **M1／M2／M3 在「零建立」情境全部 PASS**、只在「有建立」情境 FAIL ⇒ 這就是紅線「⛔ 不得只驗零建立情境」的機械證明。
- [ ] **V3 呼叫次數斷言**：零建立情境下 `field-list` 恰 **1 次**（現況 2 次）。⛔ 單獨不足以驗正確性（M1 也是 1 次），須與 V1 併用。理由須寫入交付：研究輪確認既有 **1,174** 個測試**沒有任何一個**釘住 `field-list` 次數 ⇒ 不加這條，修法會靜默回退而沒人知道。
- [ ] **V4 有建立路徑的真實 gh 實跑（⛔ 不得只靠 mock）**：對**拋棄式** Project（`gh project create` → 跑 → `gh project delete`；⛔ 不得用 Project #4，⛔ 不得用既有的 #1／#5）實跑一次 `ensure_fields`，附 13 次 `field-create` 原始輸出、回傳的 13 個 `FieldMeta`（id／options 逐項）、以及同一 Project 上重新 `list_fields` 的**逐位元對照**，另附 `gh api rate_limit` 前後差值。並逐項回答 mock 與真實 API 的五項差異。
- [ ] **V5 零建立路徑的真實資料等價**：對真實 Project #4 連續兩次 `list_fields` 逐位元比對。研究輪 2026-08-26T12:28 兩輪皆 `True`（29 欄含 option id），各 204 點／8.07 與 9.55 秒。交付須重跑並附輸出與**時刻**。
- [ ] **V6 ⭐ 乙案的等價性證明**：原生查詢與 `gh project field-list` 的結果須**逐位元相同**，餵進**同一支** `list_fields` 比對（研究輪對真實 Project #4 已得 IDENTICAL，29 欄含 option id）。⛔ 並須附**點數與牆鐘的前後對照**，以及分頁邊界的測試（`fields` 超過單頁時）。
- [ ] **V7 回歸，四個守衛逐條附輸出**：`uv run pytest`（基線 **1,174 passed**，⛔ 交付時現場重記）、`scripts/contract_tool_reconcile.py --check`（基線 rc=0「59 個缺口全部有登記處置」）、`scripts/canonical_citation_scan.py`（基線 rc=0）、`wfcli doctor <repo_root> --owner ruan6047 --project 4`（基線 rc=0）。⛔ **不得接管線**（`| tail` 會把 rc 換成 tail 的）。
- [ ] **V8 未驗清單依 canonical §6.4.2**：逐項標明驗不了的原因。⭐ 已知必列的一項：**org-owned Project 的等價性**（環境上無樣本）。⛔ 標不出原因者代表驗得了、不得列入。

## Log

- 2026-08-26T11:49:44+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-26T12:12:12+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (研究)；iteration 0；SHA cd17ba5f0bda377a0bcdbf542932e6a977f7c409；證據 派研究輪（子代理，唯讀）。⚠️ 並登記已知衝突：本卡宣告的 file:cli/src/wf_cli/project.py 與 WF-POSTHOC-CONFORMANCE1（#138，🔨執行中、已指派、子代理進行中）相交 ⇒ 研究輪唯讀故不受影響，但本卡進執行前必須等 #138 交付並釋出。另兩張相交卡 WF-REVIEW-RECEIPT-WRITEBACK1（#86）與 OPS-PROJECT-ARCHIVE-TERMINAL1（#133）皆 Backlog 未認領，依 assign_cmd 的既有裁斷不構成阻擋。核心痛點的數字由 PM 於 2026-08-26 在 origin/main cd17ba5 獨立複驗：ensure_fields 對 list_fields 呼叫兩次、各 102 點、合計 204 點/10.41 秒，對照 list_items 僅 7 點。。
- 2026-08-26T13:21:59+08:00 amend by wf-cli（op 64e82f77）→ 驗收條件：原值指紋 sha256:a7987cbd7026c83b89cac347489ac3b0ddadf2d99877ba6205ada29a794a0c43 (678 bytes) → 新值指紋 sha256:f438cf7d567046f8df3507c2020c0def10720bbbb9c1e912ec9f71c9f49d4773 (4985 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定採乙案擴射程納入換原生查詢（issuecomment-5420717647）；30 輪研究輪填實 A0-A9/V1-V8；並修正開卡時宣告的幽靈路徑 cli/tests/test_project.py（該檔不存在，真名 test_project_mocked.py）。
- 2026-08-26T13:21:59+08:00 amend by wf-cli（op 64e82f77）→ 驗證：原值指紋 sha256:cf04bd0985feae21ece0a49863c0d355b3662d16da32b3ab22d2e3681f9c6fec (263 bytes) → 新值指紋 sha256:049ea5b760d42bf62fc9909ce551cc1fa233edcab132a392b1c969ec19ce9f86 (3218 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定採乙案擴射程納入換原生查詢（issuecomment-5420717647）；30 輪研究輪填實 A0-A9/V1-V8；並修正開卡時宣告的幽靈路徑 cli/tests/test_project.py（該檔不存在，真名 test_project_mocked.py）。
- 2026-08-26T13:21:59+08:00 amend by wf-cli（op 64e82f77）→ 資源宣告：原值指紋 sha256:c25810030f27852728d94043a4b52c5968f6aa9ee5754f80b367cf9ebb9ef193 (195 bytes) → 新值指紋 sha256:6541eb8176fb38d20547e97d21825d891521a9f001470d787da30033a61125cd (86 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定採乙案擴射程納入換原生查詢（issuecomment-5420717647）；30 輪研究輪填實 A0-A9/V1-V8；並修正開卡時宣告的幽靈路徑 cli/tests/test_project.py（該檔不存在，真名 test_project_mocked.py）。
- 2026-08-26T16:14:23+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (規劃)；iteration 0；SHA 5170c27ef61df240ab6452f7172ff5830d1464c4；證據 研究輪 30 輪完成，需求方裁定採乙案擴射程納入換原生 GraphQL 查詢（issuecomment-5420717647）。阻塞已解除：WF-POSTHOC-CONFORMANCE1（#138）已於 5170c27 合併並 🏁完成，project.py 的活衝突消失（另兩張相交卡 #86／#133 皆 Backlog 未認領，依 assign_cmd 既有裁斷不構成阻擋）。並依 WF-CARD-BRIEF-BACKFILL1 的 A12 裁定，本卡排在該卡下一批之前——那是唯一會改變成本量級的順序（160 張回填由 7.6 小時降到約 1 小時）。。
- 2026-08-26T16:14:53+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code (執行)；分支worktree ai/opus-5/WF-CLI-ENSURE-FIELDS-DOUBLE-READ1 @ /Users/ruanruan/Dev/ai-workflow/.worktrees/ensure-fields；交付狀態 🔨執行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-26T17:14:59+08:00 amend by wf-cli（op a2de048f）→ 資源宣告：原值指紋 sha256:8b0f440031decd88837d9be7fb90f0c40a18f0bb1df9cc545c34f6a088bdebb9 (202 bytes) → 新值指紋 sha256:33588c102c0c6372ad6799d73a57abd8903bb70789321d8154fa3d065e2f9623 (155 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 執行者自陳改了 cli/tests/fake_gh.py（宣告外）並新增 cli/tests/ensure_fields_oracle.py：A7 要求把 list_fields 換成 GraphQL，而 FakeGhRunner.graphql 對未知查詢形狀 raise AssertionError ⇒ 不補該分支全套 1226 條會整批爆，構造上無不動它而達成 A7 的路徑；已查 #153 同期落地但未動該檔、無實際撞車。
- 2026-08-26T17:18:00+08:00 handoff by wf-cli → owner 待認領（跨家族查核）；iteration 0；SHA 8bfa088b271215950f5a0d551e561becf00f01fa；階段 規劃；踩坑回應 8 族（已檢查 1／不適用 1／發現 6）；證據 PR #155。乙案落地：ensure_fields 零建立由 204 點/10.41 秒降到 3 點/1.85-2.04 秒（68 倍），每動詞讀取面 211→10 點，203 items × 10 = 2030 點 ⇒ 1 個額度視窗（原 9）。M4 變異證明次數斷言存在理由：拿掉 C1 短路（回傳值仍正確）既有 1218 條全數通過、只有新增那條轉紅。V1 差分預言 475 次（225 有建立/250 零建立）0 不一致，比對順序敏感逐欄位含 option (name,id)。V2 三種錯誤實作在零建立全部 PASS 只在有建立 FAIL。V4 拋棄式 Project #6 真實 API 15 次 field-create。V6 IDENTICAL（29 欄 38 option，解析後與原始 payload 層皆是）。回歸 1218→1226、三守衛 rc=0、ruff 全樹 104=104。⛔ 兩件待需求方：fake_gh.py 補宣告已做、拋棄式 Project #6 未刪（需 gh project delete 6 --owner ruan6047）。。
- 2026-08-26T18:05:08+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 跨家族查核者（身分未自述；收據原文見 PR #155 的 issuecomment-5423663247，PM 逐字轉錄）；core_pain_resolved yes；self_run 10 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-CLI-ENSURE-FIELDS-DOUBLE-READ1-e0-8bfa088b271215950f5a0d551e561becf00f01fa。
- 2026-08-26T18:09:35+08:00 handoff by wf-cli → owner 待認領（跨家族查核）；iteration 0；SHA 6f2d0d350b5afc584b9a780966a57415a011d7d7；階段 審核；踩坑回應 8 族（已檢查 3／不適用 1／發現 4）；證據 R1-001 修復送審（第 2 輪）。commit 6f2d0d3：用法段由 uv run pytest 改為 uv run python -m pytest，並就地寫下 python -m 為何必要、⛔ 不得由該段推出什麼（不是 pytest 的 bug、PYTHONPATH=. 不是等價推薦寫法）、以及兩種形式各自的實測 rc。PM 於清 __pycache__ 後獨立複驗：文件原形 rc=1 ModuleNotFoundError；新形式 rc=0、觸發 475 次、有建立 225/零建立 250、比對不一致 0、1226 passed；uvx ruff check tests/ensure_fields_oracle.py All checks passed。全套 pytest 1226 passed。⭐ 本輪只改一段 docstring，⛔ 未動任何執行路徑 ⇒ 前一輪已通過的所有 self_run（M4、M1、真實額度 3 點、順序敏感差分、分頁、與 #153 合併後 1270 passed）在此 head 上仍成立。⚠️ 基線仍為 merge-base 5170c27ef61df240ab6452f7172ff5830d1464c4。。
- 2026-08-26T18:27:03+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 跨家族查核者（身分未自述；收據原文見 PR #155 的 issuecomment-5423874850，PM 逐字轉錄）；core_pain_resolved yes；self_run 5 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-CLI-ENSURE-FIELDS-DOUBLE-READ1-e0-6f2d0d350b5afc584b9a780966a57415a011d7d7。
- 2026-08-26T18:29:16+08:00 handoff by wf-cli → owner 待認領（跨家族查核）；iteration 0；SHA d30e4d566b52aa3adeffe02a24b051d852c031d1；階段 審核；踩坑回應 8 族（已檢查 3／不適用 1／發現 4）；證據 R2-001 處置送審（第 3 輪）。finding 成立（6f2d0d3 缺三件式 trailer，該 commit 由 PM 撰寫；同分支執行者五個 commit 各有 3 個）。⛔ 但 PM 判定其 disposition「不改寫既有 pushed commit」射程過寬，逐條依 canonical：唯一談歷史防線處射程逐字是「預設分支」（ruleset deletion + non_fast_forward）、同一份逐字強制功能分支「一律本地 rebase + git push --force-with-lease」、而「本專案明令禁止」的兩個出處分別講 TRAILER_GUARD_EPOCH 界線前與「已在 main 上」。實查 6f2d0d3 非 origin/main 祖先、git branch -a --contains 只列本分支自己。⇒ 採 amend + force-with-lease：6f2d0d3 → d30e4d566b52aa3adeffe02a24b051d852c031d1，⭐ tree 逐位元相同（內容一字未改）。守衛以查核者同一指令複驗：全分支 5170c27..d30e4d5 違規 0/合規 6；本輪那顆 8bfa088..d30e4d5 違規 0/合規 1。pytest 1226 passed。⚠️ 交下一輪判斷兩件：PM 對 disposition 射程的不同意是否成立（若維持原判，改寫已不可回收，只能記為既成事實）；以及 PM 已採納查核者「未驗證文字模式應另開流程卡、⛔ 不擴張本卡驗收」的裁斷，該建議尚未開卡。不同意全文見 issuecomment-5423992454。。
- 2026-08-26T18:52:53+08:00 review by wf-cli → APPROVE（✅通過）；查核者 跨家族查核者（身分未自述；收據原文見 PR #155 的 issuecomment-5424080646，PM 逐字轉錄）；core_pain_resolved yes；self_run 6 項；findings 0 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-CLI-ENSURE-FIELDS-DOUBLE-READ1-e0-d30e4d566b52aa3adeffe02a24b051d852c031d1。
- 2026-08-26T18:57:17+08:00 handoff by wf-cli → owner 已合併（無部署面）；iteration 0；SHA b169c2424c0401c169104312f2fa807c01345feb；階段 審核；踩坑回應 8 族（已檢查 2／不適用 1／發現 5）；證據 第 3 輪查核 APPROVE（findings 0，收據原文 PR #155 的 issuecomment-5424080646）。⭐ 查核者逐字確認 PM 對 R2-001 disposition 射程的不同意成立：「我第 2 輪把『已 push』不當地泛化成禁止改寫；canonical 的 non-fast-forward 防線目標是預設分支，而功能分支更新明定採本地 rebase 加 git push --force-with-lease」。並更正 PM 一處：「6f 已無 ref 所以無法驗 tree」不完全成立——dangling object 在 GC 前仍可讀，查核者實測 6f2d0d3^{tree} == d30e4d5^{tree}，但逐字指出那不是長期可依賴的稽核載體。合併流程：分支 git merge origin/main（帶入 PR #153），CI 綠後 gh pr merge 155 --merge，merge commit b169c2424c0401c169104312f2fa807c01345feb。合併結果上重跑：pytest 1270 passed、contract_tool_reconcile --check rc=0、canonical_citation_scan rc=0。⭐ 成果：ensure_fields 零建立由 204 點/10.41 秒降到 3 點，每動詞讀取面 211→10 點，WF-CARD-BRIEF-BACKFILL1 的 160 張回填由 9 個額度視窗降到 1 個 ⇒ 該卡的 A12 阻塞條件已解除。本卡為 CLI 內部最佳化，⛔ 無部署面。；收尾清理：已清除 worktree、本地分支、遠端分支。


## Comment 5420717647 · 2026-08-26T04:45:08Z

## 裁定：採**乙案**——射程擴到「換原生 GraphQL 查詢」

30 輪研究輪證明現射程**達不成本卡自己宣告的原始目標**。逐字對照：

| 方案 | 189 張回填需要的額度視窗 |
|---|---|
| 現況 | 9 |
| 本卡原射程（只消除第二次呼叫） | **5** |
| 換原生查詢 | **1** |

原生查詢實測 **2 點／0.55 秒** vs `gh project field-list` 的 **102 點／4.4 秒**，且已對真實 Project #4 證明**逐位元等價**（29 欄含 option id）。根因在 gh CLI 自己：`queries.go:1048` 把 `firstItems` 寫死 100 ⇒ 查欄位時順便抓 100 items × 100 fieldValues ⇒ **102 點是結構常數、與 Project 規模無關**（`-L` 只餵 `firstFields`，實測 `-L 100/30/20` 與空專案全部 102）。

**理由**：甲案要跑完整流程（worktree／查核／合併／收尾）卻換到一個不達標的結果，那是最貴的一種。

⚠️ **明文接受的限制**：原生查詢在 **org-owned Project 的等價性驗不了**——`ruan6047` 名下無 organization（`gh` 實測回 `organization: null`），環境上無樣本。⇒ 交付**必須逐字揭露**這一項，⛔ 不得宣稱「已驗證等價」。

## ⛔ 卡面 `功能` 欄有一句是假的，且機械上改不動

`功能` 逐字寫「**每個** wfcli 寫入動詞都跑兩次 `list_fields`」。**假**——複驗 `grep -n ensure_fields cli/src/wf_cli/commands/*.py`：呼叫者只有 `handoff`／`assign`／`open`／`amend`／`review` **5 個**；`deploy-declare`／`deploy-state` 走單次（112 點）、`checkpoint` **付 0**。

⭐ 而 `docs/WF_EVENT_IDEMPOTENCY1.md` §7.1 **已經機械修正過一模一樣的錯**，逐字：「『所有寫入動詞共用的一個注入點』兩處都不成立」。⇒ 這不是新形狀，是**同一個形狀第二次**。

⚠️ 這是 PM 開卡時把未驗的結構宣稱寫進身分欄造成的（同 session 內第三次）。`功能` 欄在 `open` 有 8 個身分旗標而 `amend` **有 0 個** ⇒ 改不動。⇒ **以驗收條 A5 逐字更正，執行者與查核者一律以驗收為準。**

## ⛔ 另兩處卡面錯誤

1. **資源宣告指向不存在的檔**：`file:cli/tests/test_project.py` **不存在**（真名 `test_project_mocked.py`，已複驗）。⇒ `find_conflicts` 逐字比對，現況替幽靈路徑佔位、真正要改的測試檔沒被宣告。**待額度重置後 amend 修正。**
2. **驗收留白處寫的「有建立那條在正常環境構造上跑不到」為假**：既有測試套件**已跑它 219 次**（`FakeGhRunner` 專案預設為空），共建 3,285 欄。⇒ 「刻意造欄位缺失」的機制早就存在且是預設行為。

## 序位與其他裁定

- **等 `WF-POSTHOC-CONFORMANCE1`（`aiwf#138`）到 🏁完成再開工**。兩卡宣告字串完全相同 ⇒ `assign` 硬退，且 `TERMINAL_STATUSES` 只有 `🏁完成`／`🛑已停止`（走到 `📦已合併` 仍擋）。⚠️ 且 `#138` 對 `ItemSnapshot` 加欄會讓行號失準 ⇒ **驗收一律以符號指認，⛔ 不寫行號**。
- **修法採 C1**（零建立時回傳已取得的那份），⛔ 不採 C3（併入 `field-create` 回傳）——有建立路徑在生產是死碼，C3 的額外收益幾乎全在測試環境卻引進跨版本相依。
- **`#147` 的 A7 要更正**：它逐字宣稱本卡會「提高一個數量級」，⛔ 假——本卡原射程只有 **1.91 倍**。擴射程後才接近。⇒ PM 於額度重置後一併 amend。
- **修法必須自帶次數斷言**：實查**無任何測試釘住 `field-list` 次數**，兩個方向都無守衛 ⇒ pytest 綠正是問題本身。

## ⚠️ 額度現況即本卡的證據

本裁定寫下時 GraphQL 額度剩 **170/5000**——單一研究輪吃掉約 3,850 點（77%）。⇒ PM 現在**無法對本卡執行 `amend`**（一次要 211 點）。⭐ 這不是巧合，是本卡要治的東西的直接展示。

---
以上由 PM（Claude Opus 5@Claude Code）以需求方的 token 發文；裁定內容轉錄自需求方在 2026-08-26 session 的逐字指示「乙」（＝擴射程納入換原生查詢）。⛔ 合併與部署不在此授權內。

## Comment 5423741245 · 2026-08-26T10:05:09Z

<!-- wf-review-event:v1 card_id=WF-CLI-ENSURE-FIELDS-DOUBLE-READ1 source_sha=8bfa088b271215950f5a0d551e561becf00f01fa attempt_id=WF-CLI-ENSURE-FIELDS-DOUBLE-READ1-e0-8bfa088b271215950f5a0d551e561becf00f01fa -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CLI-ENSURE-FIELDS-DOUBLE-READ1`　attempt_id：`WF-CLI-ENSURE-FIELDS-DOUBLE-READ1-e0-8bfa088b271215950f5a0d551e561becf00f01fa`
- 查核者：跨家族查核者（身分未自述；收據原文見 PR #155 的 issuecomment-5423663247，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`8bfa088b271215950f5a0d551e561becf00f01fa`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-26T18:05:08+08:00

### self_run（查核者實跑）

- `git diff 5170c27 8bfa088 與 git diff --check`
  - rc=0；差異為 4 檔 +584/-11，merge-base 相符
- `gh api rate_limit --jq .resources.graphql.remaining 連續兩次`
  - 4266→4266，rc=0（控制組差值 0）
- `cd cli && uv run --frozen pytest -q（基線與 head）`
  - 5170c27 = 1218 passed rc=0；8bfa088 = 1226 passed rc=0
- `獨立副本移除 C1 短路後跑全套（M4）`
  - 1225 passed、僅 test_ensure_fields_zero_creation_issues_exactly_one_field_read 失敗，rc=1（預期）
- `清 __pycache__/*.pyc 後套用 M1（無條件 return existing）`
  - 零建立兩條 2 passed rc=0；有建立的 test_ensure_fields_creation_path_return_matches_fresh_read 1 failed rc=1（預期）
- `文件聲稱的 cd cli && uv run pytest -q -p tests.ensure_fields_oracle`
  - ModuleNotFoundError: No module named 'tests'，rc=1；改 uv run --frozen python -m pytest -q -p ... 才得 1226 passed、475 次、225 有建立/250 零建立/0 不一致，rc=0
- `順序驗證：構造 option 順序相反的兩個 FieldMeta`
  - dict == 為 True，但 field_diff 回報差異，rc=0
- `test_list_fields_follows_field_pagination + test_list_fields_stops_at_a_single_page`
  - 2 passed rc=0；已檢視 assertions 為 seen_cursors == [None, 'CURSOR_1'] 及跨頁欄位順序
- `真實 Project #4：確認 missing=[] 後跑 ensure_fields`
  - 回傳 29 欄，額度 4183→4180（delta=3）rc=0；原生與 gh project field-list 的 29 欄順序敏感 (id,name,type,option(name,id)) 序列完全相同 rc=0
- `合併 origin/main(6148bd4) 至 head 的獨立副本`
  - 1270 passed rc=0；contract_tool_reconcile --check、canonical_citation_scan、wfcli doctor 皆 rc=0；uvx ruff check 104 errors（與基線相同）

### findings（1，其中 blocking 1）

- **WF-CLI-ENSURE-FIELDS-DOUBLE-READ1-R1-001**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`documented-command-never-executed-as-written`
  - evidence：cli/tests/ensure_fields_oracle.py 的用法段寫 `cd cli && uv run pytest -q -p tests.ensure_fields_oracle`，但 pytest 在載入 -p 外掛時尚未把專案根放進 import path ⇒ 乾淨副本直接 ModuleNotFoundError: No module named 'tests'、rc=1。該外掛是 V1 的唯一可重跑入口，且本 PR 以它作為 475 次差分證據。⭐ PM 於 8bfa088 的工作樹清 __pycache__ 後獨立複驗：文件形式 rc=1 ModuleNotFoundError；uv run python -m pytest -q -p tests.ensure_fields_oracle 得 rc=0、觸發 475 次、比對不一致 0、1226 passed。⚠️ 執行者自陳的失誤第 5 條正是它自己撞到同一個錯（用 PYTHONPATH=. 繞過），卻把未驗證的形式寫進 docstring——與本卡失誤第 1 條（照抄未量過的 94%）同一形狀。
  - disposition：把用法段改成已實測可用的 `uv run python -m pytest -q -p tests.ensure_fields_oracle`（或提供同等可重現的 import-path 修正），並以該精確指令重跑後重審。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-CLI-ENSURE-FIELDS-DOUBLE-READ1-e0-8bfa088b271215950f5a0d551e561becf00f01fa
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待認領（跨家族查核）
findings:
  - finding_id: WF-CLI-ENSURE-FIELDS-DOUBLE-READ1-R1-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: documented-command-never-executed-as-written
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5423984867 · 2026-08-26T10:27:05Z

<!-- wf-review-event:v1 card_id=WF-CLI-ENSURE-FIELDS-DOUBLE-READ1 source_sha=6f2d0d350b5afc584b9a780966a57415a011d7d7 attempt_id=WF-CLI-ENSURE-FIELDS-DOUBLE-READ1-e0-6f2d0d350b5afc584b9a780966a57415a011d7d7 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CLI-ENSURE-FIELDS-DOUBLE-READ1`　attempt_id：`WF-CLI-ENSURE-FIELDS-DOUBLE-READ1-e0-6f2d0d350b5afc584b9a780966a57415a011d7d7`
- 查核者：跨家族查核者（身分未自述；收據原文見 PR #155 的 issuecomment-5423874850，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`6f2d0d350b5afc584b9a780966a57415a011d7d7`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-26T18:27:03+08:00

### self_run（查核者實跑）

- `git diff 8bfa088 6f2d0d3 -- cli/tests/ensure_fields_oracle.py 與 git diff --check`
  - 僅 1 檔、10/+1 行 docstring，rc=0；未動執行路徑
- `隔離副本清 __pycache__ 後跑舊指令 uv run pytest -q -p tests.ensure_fields_oracle`
  - rc=1，確為 ModuleNotFoundError: No module named 'tests'
- `同一乾淨副本跑 uv run python -m pytest -q -p tests.ensure_fields_oracle`
  - rc=0，475 次（有建立 225／零建立 250）、判不了 0、比對不一致 0、1226 passed
- `uvx ruff check tests/ensure_fields_oracle.py`
  - rc=0，All checks passed
- `git interpret-trailers --parse；wfcli doctor --commit-trailers --commit-range 8bfa088..6f2d0d3 --trailer-epoch none --require-planned-by`
  - 只解析出 Co-Authored-By；工具 rc=0 但報 1 筆違規，缺 Requested-by／Implemented-by／Planned-by

### findings（1，其中 blocking 1）

- **WF-CLI-ENSURE-FIELDS-DOUBLE-READ1-R2-001**　severity=major　blocking=true　class=governance　attribution=coordinator　root_cause_id=`implementation-commit-missing-provenance-trailers`
  - evidence：6f2d0d350b5afc584b9a780966a57415a011d7d7 是本 T3 卡的新實作提交，卻缺 Requested-by／Planned-by／Implemented-by。AGENTS.md 逐字「T2 以上實作 commit 加 Requested-by / Planned-by / Implemented-by」。doctor 在精確單提交範圍確認。⭐ PM 獨立複驗：同分支執行者的 5 個 commit（27f6d06／696bcae／e92f567／15dfe1f／8bfa088）各有 3 個 trailer，唯獨 6f2d0d3 為 0 —— 該 commit 由 PM 撰寫，⛔ 非執行者。
  - disposition：以不改寫既有 pushed commit 的合規方式補足本輪交付的 provenance，或依專案既有裁定留下可稽核的例外／處置。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-CLI-ENSURE-FIELDS-DOUBLE-READ1-e0-6f2d0d350b5afc584b9a780966a57415a011d7d7
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待認領（跨家族查核）
findings:
  - finding_id: WF-CLI-ENSURE-FIELDS-DOUBLE-READ1-R2-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: governance
    attribution: coordinator
    root_cause_id: implementation-commit-missing-provenance-trailers
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5423992454 · 2026-08-26T10:27:48Z

## PM 對 `R2-001` 的處置：finding 成立、⛔ 但依 canonical 採了不同的合規路徑

上一則裁決事件已逐字轉錄，⛔ **PM 未改動該 finding 的任何欄位**（含 `disposition`）。本帖是 PM 自己的處置說明與一項**不同意**，交由下一輪查核判斷。

### finding 本身：✅ 成立，且是 PM 造成的

`6f2d0d3` 缺三件式 trailer，**確為事實**。獨立複驗：同分支執行者的五個 commit（`27f6d06`／`696bcae`／`e92f567`／`15dfe1f`／`8bfa088`）**各有 3 個 trailer**，唯獨 `6f2d0d3` 為 **0**。⭐ 該 commit 由 PM 撰寫，⛔ 非執行者。

### ⛔ 但 `disposition` 逐字寫的「**不改寫既有 pushed commit**」，PM 判定其射程過寬

`disposition` 原文：「請以**不改寫既有 pushed commit** 的合規方式補足……或依專案既有裁定留下可稽核的例外／處置」。

**逐條查證**：

1. **canonical `AI_WORKFLOW.md` 唯一談歷史改寫的地方，射程逐字是「預設分支」**：「A 類 repo 的 **main** 必須有平台級歷史防線……標準實作＝GitHub ruleset（`deletion` ＋ `non_fast_forward`，**target 預設分支**）」。⇒ ⛔ 不是所有分支。
2. **同一份 canonical 對功能分支是強制 force-push**：「分支更新禁 `gh pr update-branch`：它產生 synthetic merge、污染歷史與守衛判讀；**一律本地 rebase ＋ `git push --force-with-lease`**」。⇒ ⭐ 兩條不衝突：一條保護 main，一條要求功能分支這樣做。
3. **「本專案明令禁止」的兩個出處都不是通則**：`AGENTS.md` 那句講的是 **`TRAILER_GUARD_EPOCH` 界線前**的歷史 commit；`docs/DEV_MAIN_RED_CAPABILITY_FLAGS1_FIX1.md` 那句逐字是「`adfcbce` **已在 main 上**」。

**本 commit 的實際狀態**（實查）：⛔ **不是 `origin/main` 的祖先**；`git branch -a --contains` 只列出本分支自己（本地＋遠端）；⛔ 無任何其他 ref 或工作基於它。

### 已執行的處置

`git commit --amend` 補上三件式後 `git push --force-with-lease`：

| 項 | 值 |
|---|---|
| SHA | `6f2d0d350b5afc584b9a780966a57415a011d7d7` → `d30e4d566b52aa3adeffe02a24b051d852c031d1` |
| **tree** | ⭐ **逐位元相同**（`git rev-parse <old>^{tree}` == `<new>^{tree}`）⇒ 內容一字未改，只補 trailer |
| 守衛（全分支 `5170c27..d30e4d5`） | **違規 0／界線前 0／合規 6／無所要求 0** |
| 守衛（本輪那一顆 `8bfa088..d30e4d5`） | **違規 0／合規 1** |
| `pytest` | **1226 passed** |

指令與查核者所用的完全相同：`wfcli doctor .. --registry none --commit-trailers --commit-range <範圍> --trailer-epoch none --require-planned-by`。

### ⚠️ 交給下一輪查核判斷的兩件

1. **PM 對 `disposition` 射程的不同意是否成立**（上面三條逐字引用）。若查核者維持原判，PM 已造成的改寫**無法回收**——`6f2d0d3` 已不在任何 ref 上，⇒ 屆時只能記為既成事實，⛔ 不宣稱可修復。
2. ⭐ **查核者在「理由」段的另一項裁斷，PM 採納**：逐字「兩次『未驗證文字』的模式確實存在，但……把它新增為本卡的驗收條目**無法形成新的機械防線**，且會擴張已凍結的卡範圍。若需求方要提升為通則，應**另開流程／治理卡**，處理『註解或交付中的實測宣稱須附可執行收據』的可機械化設計。」⇒ ⛔ **未擴張本卡驗收**；該建議已列入 PM 的待裁定清單，⛔ 尚未開卡。

---
本帖由 PM（Claude Opus 5@Claude Code）以需求方的 token 發文，內容為 **PM 自己的處置說明與不同意**，⛔ 非需求方的裁定，⛔ 亦未改動查核者 finding 的任何欄位。處置決定轉錄自需求方在 2026-08-26 session 對「甲／乙」兩案的逐字回覆「ＯＫ」（甲＝照原樣轉錄、另發更正留言、交下一輪查核判斷）。

## Comment 5424263594 · 2026-08-26T10:52:55Z

<!-- wf-review-event:v1 card_id=WF-CLI-ENSURE-FIELDS-DOUBLE-READ1 source_sha=d30e4d566b52aa3adeffe02a24b051d852c031d1 attempt_id=WF-CLI-ENSURE-FIELDS-DOUBLE-READ1-e0-d30e4d566b52aa3adeffe02a24b051d852c031d1 -->
## 查核裁決：APPROVE

- 卡：`WF-CLI-ENSURE-FIELDS-DOUBLE-READ1`　attempt_id：`WF-CLI-ENSURE-FIELDS-DOUBLE-READ1-e0-d30e4d566b52aa3adeffe02a24b051d852c031d1`
- 查核者：跨家族查核者（身分未自述；收據原文見 PR #155 的 issuecomment-5424080646，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`d30e4d566b52aa3adeffe02a24b051d852c031d1`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-26T18:52:53+08:00

### self_run（查核者實跑）

- `git diff 8bfa088 d30e4d5 -- cli/tests/ensure_fields_oracle.py 與 git diff --check`
  - 僅 1 檔、+10/-1 的 docstring，rc=0
- `歷史／tree 驗證：8bfa^{tree} vs d30^{tree}；6f2d0d3^{tree} vs d30e4d5^{tree}；git diff --quiet 6f2d0d3 d30e4d5；merge-base --is-ancestor；git branch -a --contains`
  - 前兩者不同（文件確有修正）；⭐ 6f2d0d3 雖已不在任何 ref，本機物件庫仍可讀，6f2d0d3^{tree} == d30e4d5^{tree} 且 git diff --quiet rc=0；6f2d0d3 非 origin/main 祖先（rc=1）、branch -a --contains 無輸出
- `新隔離副本清 __pycache__ 後跑 uv run pytest -q -p tests.ensure_fields_oracle`
  - rc=1，為預期的 ModuleNotFoundError: No module named 'tests'
- `同一副本跑 uv run python -m pytest -q -p tests.ensure_fields_oracle`
  - rc=0；475 次（225 有建立／250 零建立）、判不了 0、比對不一致 0、1226 passed
- `wfcli doctor .. --registry none --commit-trailers --commit-range 5170c27..d30e4d5 --trailer-epoch none --require-planned-by`
  - rc=0；違規 0／界線前 0／合規 6／無所要求 0
- `uvx ruff check tests/ensure_fields_oracle.py`
  - rc=0，All checks passed

### findings（0，其中 blocking 0）

- （無）

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-CLI-ENSURE-FIELDS-DOUBLE-READ1-e0-d30e4d566b52aa3adeffe02a24b051d852c031d1
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待認領（跨家族查核）
findings: []
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。
