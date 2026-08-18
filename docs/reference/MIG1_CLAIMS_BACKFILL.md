# MIG1 遷移卡資源宣告補正（`OPS-MIG1-CLAIMS-BACKFILL1`）

> 卡：[`ai-workflow#31`](https://github.com/ruan6047/ai-workflow/issues/31)　基線 `ae8f74162797e2eed7180a1cd1ed6692fab3b6d3`
> 本檔是本卡唯一的 file 資源（`file:docs/reference/MIG1_CLAIMS_BACKFILL.md`）。探針因此**內嵌於本檔**、不另開 `scripts/`——
> 一張要求別人守住資源宣告的卡，自己不能寫到宣告以外的路徑。抽出執行方式見 §7。

---

## 0. 結論（先讀）

**驗收條件 1「以 `wfcli amend` 寫入正式宣告」在本卡基線上機械不可執行。** 母體 33 張（含 21 張活卡）
沒有一張的 body 有獨立標題行 `## 資源宣告`——它們寫的是
`## 資源宣告（機器可讀；`null`／`[]` 代表未正式宣告，不代表無資源）`。
`amend` 的資源路徑第一行就是 `parse_block(item.body)`，解析失敗即 `return 2`，零寫入。
**33/33 不可達，實測。**

因此本輪交付的是**判定與待裁定清單**，不是已寫入的宣告。實際寫入需要先解掉 §1 的阻斷器，
而解法有三條、每一條都超出本卡的射程或違反本卡的硬約束，**須需求方裁定選哪一條**。

同時發現三件與本卡射程相鄰、但都不是本卡能自己解決的事：

- **母體外出現 1 張硬阻擋**（§6）：`WF-REVIEW-EVENT-MARKER-CONTRACT1` #15，2026-08-12 釘選時為 0。
- **assign 的 fail-open 規模比派工包所述更大**（§2）：比對母體 42 張中 **21 張**被靜默略過，正好一半。
- **相交判定的實作與契約不一致**（§5）：`find_conflicts` 是完全字串比對，`WF_RESOURCE_WRITESET1` §2.2
  定義的卻是分量序列前綴謂詞。現役可解析活卡中，**契約認定相交但實作抓不到的有 10 組**。

---

## 1. 阻斷器：`wfcli amend --resources` 對 MIG1 遷移卡機械不可達

### 1.1 兩道各自獨立的門，任一即擋

**第一道**——`cli/src/wf_cli/commands/amend_cmd.py` 的 `run()`，資源路徑首行：

```python
if wants_resources:
    current = parse_block(item.body)   # ← MIG1 卡在這裡就拋 ResourceDeclarationError
```

`parse_block` → `_declaration_section` 以**獨立標題行** `## 資源宣告` 定位，找不到即拋，
外層 `except (AmendError, ResourceDeclarationError)` → 印拒收 → `return 2`。

**第二道**——即使繞過第一道，`card.amend_resource_block` 仍要走 `_locate_section(lines, "## 資源宣告")`，
該函式要求「Log 之前恰好 1 次」，MIG1 卡是 0 次 → `AmendError`。

### 1.2 實測（非推論）

```
$ wfcli amend ML-PT3 --owner ruan6047 --project 4 --repo ruan6047/cpbl-analytics \
    --reason "測試：確認 amend 能否對 MIG1 遷移卡寫入資源宣告" \
    --db-scope read --resources "file:docs/tasks/ML-PT3.md" --dry-run

[amend] 拒收（未寫入任何狀態）：body 內找不到獨立標題行 `## 資源宣告`（`## 資源宣告` 字樣
出現在 Log 之前但不是獨立標題行，排版可能已被字面 \n 破壞）
```

§7 探針 [B] 段把它擴到全母體：**恰好一個獨立標題行者 0/33；不可達 33/33**；
33 張的標題行**逐字相同**，都是 `## 資源宣告（機器可讀；...）`。

### 1.3 診斷訊息本身是錯的，而它會把人推去做被禁止的事

錯誤訊息說「排版可能已被字面 `\n` 破壞」。**這 21 張沒有任何排版破壞**——
`## 資源宣告` 只是 `## 資源宣告（機器可讀；…）` 的**字首子字串**，
`_declaration_section` 的 `elif _SECTION_HEADING in head` 因此命中，給出與事實無關的提示。

更嚴重的是 `_LAYOUT_MARKERS = ("不是獨立標題行", "個 `## Log` 標題")` 會讓 `_is_layout_failure` 回 True，
於是 amend 印出 `_LAYOUT_RUNBOOK`，其**步驟 6 是 `gh issue edit <N> --body-file /tmp/body.md`**。
那條路徑同時被兩份文件禁止：`cpbl-analytics/docs/AI_RUNBOOK.md` §7.1（「狀態寫入只可經 PM 祕書的 `wfcli`，
不得直接改 GitHub UI」）與本卡派工包的硬約束 6。**工具在它自己判斷失敗的地方，指示操作者走一條被禁止的路。**

而那份 runbook 的機械檢查（步驟 4）**對真正的排版損壞也不成立**——見 §6.2。

### 1.4 三條出路（須需求方裁定，本卡不自選）

| 出路 | 內容 | 代價／風險 |
|---|---|---|
| **A. 改 `wfcli`** | 讓 `resources._declaration_section` 與 `card._locate_section` 認得 `## 資源宣告` 後帶括號補述的標題（或提供一次性的 `--adopt-heading` 遷移旗標） | 寫入 `cli/src/**`，**超出本卡宣告的寫入集**，且改的是治理閘門本身的定位規則——應為獨立卡＋獨立查核 |
| **B. 一次性 body 正規化** | 把 33 張的標題行改回 `## 資源宣告`，宣告內容原樣保留 | 唯一可用通道是 `gh issue edit`，**被 AI_RUNBOOK §7.1 與本卡硬約束 6 禁止**；且 33 次人工寫入正是「繞道仍存在」的證據 |
| **C. 縮小驗收** | 承認本卡在現行工具下只能交付判定，寫入延到出路 A 落地後 | 驗收條件 1／3 當期不成立，需改卡面 |

**我的建議是 A**，理由：B 每執行一次就製造一次繞道，而繞道正是本卡上游要消滅的東西；
C 把問題留在原地。A 的成本是一張新卡，但它讓「宣告可被 `wfcli` 修復」這件事對**未來所有**
MIG1 遺留卡成立，而不是這一次。

---

## 2. 母體重新量測（before）

派工包給的 21 張名單**逐字複驗通過**，但周邊數字全部漂了：

| 項目 | 2026-08-12 釘選（`WF_RESOURCE_WRITESET1` §9.7b） | 2026-08-18 本卡實測 |
|---|---|---|
| Project #4 有卡 ID 的 item | 99 | **155** |
| 宣告無法解析 | 33 | **34** |
| 帶 MIG1 marker（封閉母體） | 33 | 33 |
| 帶 sentinel 卻仍失敗 | 0 | **1** |
| 母體外的解析失敗（不可豁免） | 0 | **1** |
| 母體中已註冊 worktree | 0 | 0 |
| `issue_url` 無法解析 owner/repo | 0 | 0 |
| 母體內 db_scope 分佈 | `none`11／`read`10／`write`8／`schema`1／`None`3 | 逐字相同 |

母體 33 張的狀態分佈：**21 張 `💡需求`**（本卡射程）、7 張 `🛑已停止`、4 張 `🏁完成`、1 張 `📦已合併`。
後 12 張今天不參與 fail-open，但**被排除的理由有兩種、不是同一種**：11 張命中
`TERMINAL_STATUSES = {🏁完成, 🛑已停止}`；`INGEST-GAME-TM-REFACTOR1` 是 `📦已合併`，
**它不在終態集合裡**，被擋下靠的是 `owner` 欄為 `—` 使 `is_owner_assigned` 為 False。
換句話說，只要有人把它的 owner 填回去，它會立刻回到 fail-open 集合。
驗收條件 3 的「解析失敗數須為 0」對全體 34 張說話，這 12 張仍計入。

**fail-open 的實際規模**：`assign` 的比對母體（非終態＋`is_owner_assigned`）是 **42 張**，
其中可解析 21、被靜默略過 **21**。派工包說「21 張整組被跳過」是對的，但沒說的是——
**那正好是比對母體的一半**。互斥檢查今天對半數現役卡不成立。

---

## 3. 逐張判定（21 張）

判定只依卡面 spec（`ruan6047/cpbl-analytics` 的 `docs/tasks/<CARD_ID>.md`）逐字所寫，
**不從卡名或領域推測**。`db_scope` 一律沿用 spec 的 `DB：db_scope: …` 欄位。
環境名只用 `local｜test｜production`（`cpbl-analytics/docs/DATABASE_CONTRACT.md` §2 只定義這三個）。

### 3.1 可判定：spec 明文指名寫入標的（6 張）

| 卡 | 提案宣告 | 逐字依據 |
|---|---|---|
| `DEV-VERIFY-TM-ASSERTS1` | `read` / `file:scripts/verify_deep_tm_backfill.py` | 「邊界：只動這支腳本與其測試」；「範圍：`scripts/verify_deep_tm_backfill.py` 四段驗證…」；紅線 4「本卡唯讀」 |
| `MATCHUP-DATA2` | `read` / `file:src/cpbl/api/matchups.py` | 「機制：…`aggregate_matchup_rows`（`src/cpbl/api/matchups.py:89`）以 `opp_id` 分組後，取最新年度那列…」 |
| `ML-PA-SIM-CONTEXT1` | `read` / `file:src/cpbl/models/pa_sim.py` | 「範圍：`src/cpbl/models/pa_sim.py` 的結果機率估計；不含 UI」 |
| `ML-PA-SIM-TEAM1` | `read` / `file:src/cpbl/models/pa_sim.py` | 「範圍：`pa_sim` 的對手聚合層；不含 UI」 |
| `UX-TEAM-FIELD-HIST1` | `read` / `file:src/cpbl/api/routers/leaders.py`、`file:web/src/app/teams/[code]/page.tsx` | 「守備位置圖讀 `/api/v1/season/fielding`」（定義於 `routers/leaders.py:556`）；「預估範圍：S～M（後端聚合 union＋前端沿用既有 `FieldDiagram`）」；球隊頁 `web/src/app/teams/[code]/page.tsx:46` 即該圖的消費點 |
| `OPS-POSTGAME-OBSERVE1` | `read` / `file:docs/research/OPS-POSTGAME-OBSERVE1_RESULTS.md` | 驗收條件逐字：「結果檔置於 `docs/research/OPS-POSTGAME-OBSERVE1_RESULTS.md`」；DB 欄「不得寫入 `cpbl` schema」 |

**這六張的宣告都不完整，而缺的那一半不能猜**：

- `DEV-VERIFY-TM-ASSERTS1` 的測試檔今天不存在（`tests/` 下無對應檔），檔名由執行者決定。
- `MATCHUP-DATA2` 的驗證要求「route snapshot／API 測試同步」，`UX-TEAM-FIELD-HIST1` 同（`tests/test_route_snapshot.py`）。
  **但那是全 repo 共用檔**，宣告它會讓每一張動端點的卡彼此互斥——見 §4 待裁定 (3)。
- `OPS-POSTGAME-OBSERVE1` 還要交「可重跑的觀測程式」，路徑未指名。
- `MATCHUP-DATA2` 的驗收條件 4 明寫 Discovery 須判根因層級，判成來源 `pitcher_team_no` 錯置時 **`db_scope` 要升 `write`**——
  現在宣告 `read` 是依卡面現值，不是保證。

### 3.2 Initiative 卡：無交付物，寫入集是治理寫入（3 張）

`INIT-GAME-RECAP`、`INIT-OFFICIAL-DATA1`、`INIT-PRODUCT-UX`。
三張都逐字寫著「Initiative 本身不直接驗收交付物」／只列子卡與 Gate。它們唯一會被寫的檔案是
**自己的 spec 檔**（`docs/tasks/INIT-*.md` 的「基線變更紀錄」）。

提案：`db_scope: none` ＋ `resources: ["file:docs/tasks/INIT-<ID>.md"]`。

**但這是提案不是判定**——canonical 沒有明文說治理寫入算不算資源宣告的射程，
而三張 spec 檔自 2026-08-01 起（cutover 前後）**無任何 commit**，所以「它還會被寫」是推論不是觀測。
見 §4 待裁定 (2)。**這三張不可宣告 `resources: []`**：那會把「Initiative 的寫入語意未定」
靜默轉譯成「Initiative 不寫任何東西」，正是本卡卡面禁止的那個轉譯。

### 3.3 判不定：射程未定，交需求方裁定（12 張）

全部落在同一形狀——**閘門未過或前置未完成，spec 明文把射程指向一份尚不存在的結論**。

| 卡 | 未定的是什麼（逐字） |
|---|---|
| `INGEST-LIVE-RECONCILE1` | 「Design：待需求方核可（provisional 欄位範圍、promotion／correction 優先序…）」；append-only provisional 表未命名；硬依賴 `INGEST-GAME-TM-REFACTOR1-G4` 的 production sign-off（**未達成**） |
| `INGEST-POSTGAME-FINALIZE1` | 「範圍：依 `OPS-POSTGAME-OBSERVE1` 的核可結果實作；不得先行假設延遲門檻」；「硬前置：`OPS-POSTGAME-OBSERVE1` 結果已完成」（未完成） |
| `ML-FIELD-LINEUP1` | 純研究／定契約，「不得在本卡偷渡寫入」；交付「研究報告、狀態機 contract」但報告檔名未指定 |
| `ML-FIELD-OAA-VAL1` | 「`db_scope: write`（實作階段：建立 OAA 計算與期望出局數表）」——表未命名；依賴 `INGEST-DEEP-TRACKMAN1`＋`ML-FIELD-LINEUP1` |
| `ML-FIELD-OF1` | 「`db_scope: write`（實作階段：新指標表）」——表未命名；「Design Gate（必過）」未過 |
| `ML-PT3` | 「範圍：2026 季末再評估 CPBL Stuff+；執行前重查 `PROPOSAL_EVALUATION.md`…」 |
| `ML-SIM2` | 「範圍：…**目前明確不開工**」 |
| `OPS-BACKUP-DR1` | 「Discovery：本卡第一項交付是『現行備份的故障域到底有幾個、異地目標選什麼』的判斷，**不是直接寫推送腳本**」；「視 Discovery 結論可能新增演練腳本、排程設定與告警去向」 |
| `OPS-REMOTE-PROBE1` | Phase 1；「依賴：`OPS-REMOTE-CRAWL1` 先核可 probe contract…未核可不得 claim」；CLI 模組路徑未指名 |
| `OPS-REMOTE-ROUTE1` | Phase 2；交付是證據矩陣與 GO/NO-GO 報告，檔名未指名；依賴 PROBE1 通過查核 |
| `OPS-REMOTE-WORKER1` | Phase 3；「`db_scope: write`，**僅隔離 namespace／artifact**」——namespace 未命名；依賴 ROUTE1 明確 GO |
| `OPS-REMOTE-CUTOVER1` | Phase 4–5；依賴 WORKER1 T4 APPROVE＋sign-off；且卡面 2026-07-27 註記**本鏈可能整條被「stats 域 VPS 爬蟲」新卡取代**，存廢待裁定 |

**這 12 張不是失敗，是本卡預期會有的輸出。** 全部 `💡需求`、全部尚未過 Design/Discovery Gate，
射程未定是它們**應有**的狀態。硬湊一個宣告才是錯的——那會讓互斥檢查以一個沒人負責的猜測為基礎放行。

---

## 4. 待需求方裁定

1. **§1.4 的三條出路選哪一條。** 這是其他所有事的前提；不裁定，21 張的宣告一個字也寫不進去。
2. **Initiative 卡（3 張）的治理寫入算不算資源。** 若算，§3.2 的提案可直接用；若不算，
   需要一個「本卡無交付物」的正式表達方式——`resources: []` 在本卡卡面被禁，而 `db_scope: none` 單獨不足以表達。
3. **共用測試檔要不要進宣告。** `tests/test_route_snapshot.py` 幾乎每張動端點的卡都會改。
   宣告它 → 所有 API 卡兩兩互斥（過度序列化）；不宣告 → 真的會有兩張卡同時改它（漏放）。
   這是政策問題不是技術問題，我不自選。
4. **12 張判不定者要不要改狀態。** 卡面驗收條 2 給了兩個選項（「裁定射程」或「改狀態」）。
   其中 `ML-SIM2`（明確不開工）與 `OPS-REMOTE-*` 四張（整鏈存廢待 8/7 後裁定，而今天是 8/18）
   看起來比較像「該改狀態」而不是「該補宣告」，但那是需求方的判斷。
5. **母體外的 `WF-REVIEW-EVENT-MARKER-CONTRACT1` #15 誰負責。** 見 §6。它不在本卡母體，
   但驗收條 3 要「解析失敗數為 0」，不處理它就到不了 0。
6. **`DATA-TIE-REMEDY1` 的 `db:dev:table:game_completion_evidence`。** 這是現役可解析活卡中
   **唯一**帶 `dev` 環境的宣告（`📦已合併`）。`ai-workflow#87` 第四項的列舉化落地後，
   該卡的 `amend` 會在 `parse_block(現值)` 就死——與本卡 33 張同一個形狀的單向門。
   `cpbl-analytics` 的 `DEV-RESOURCE-VOCAB-ALIGN1` 已註冊此問題（驗收條 1 逐字盤點出
   「prod×5 / production×2 / local×8 / dev×2」），**但那張卡的驗收條 1 括號內寫的是「既有卡面不可改」**——
   若列舉化先落地，`dev×2` 就永久卡死。兩張卡的先後順序需要裁定。

---

## 5. 相交分析

### 5.1 提案彼此之間：新產生 1 組（實作謂詞）

- **`ML-PA-SIM-CONTEXT1` × `ML-PA-SIM-TEAM1` → `file:src/cpbl/models/pa_sim.py`**
  兩者 `db_scope` 皆 `read`，但 `find_conflicts` 的 `both_read_only` 豁免**只對 `db:*` 生效**，
  `file:` 一律互斥。**解決方式：先後派工。**
  依據不是我的偏好——`ML-PA-SIM-TEAM1` 卡面逐字寫「與 `ML-PA-SIM-CONTEXT1` 無強順序，
  但**若情境條件化通過，聚合需一併考慮情境維度**（樣本壓力更大）」，即 CONTEXT1 的結論會改變 TEAM1 的設計。
  故 **CONTEXT1 先、TEAM1 後**。兩張的開工都另有「須先與需求方討論並取得核可才可 claim」閘門，
  這個序列化在閘門層就可以執行，不必等到 `assign`。

### 5.2 提案 × 現有可解析活卡：實作謂詞 0 組，契約謂詞 5 組

`find_conflicts` 判定 **0 組相交**。但那是**完全字串比對**的結果，不是「沒有重疊」。
按 `WF_RESOURCE_WRITESET1` §2.2 定義的謂詞（分量序列前綴、NFC＋casefold），同一批提案有 **5 組**重疊：

| 提案 | 現役活卡 | 重疊 |
|---|---|---|
| `MATCHUP-DATA2` | `UX-WINPROB-CURVE-MIGRATE1` | `file:src/cpbl/api/matchups.py` ⊂ `file:src/cpbl/api/` |
| `ML-PA-SIM-CONTEXT1` | `ML-WP-ROLLWIN1` | `file:src/cpbl/models/pa_sim.py` ⊂ `file:src/cpbl/models/` |
| `ML-PA-SIM-TEAM1` | `ML-WP-ROLLWIN1` | 同上 |
| `UX-TEAM-FIELD-HIST1` | `UX-WINPROB-CURVE-MIGRATE1` | `…/routers/leaders.py` ⊂ `file:src/cpbl/api/`；`web/src/app/teams/[code]/page.tsx` ⊂ `file:web/` |
| `OPS-POSTGAME-OBSERVE1` | `ML-WP-ROLLWIN1` | `docs/research/OPS-POSTGAME-OBSERVE1_RESULTS.md` ⊂ `file:docs/research/` |

### 5.3 實作與契約不一致，而這**不是**本卡造成的

同一支探針對**現役可解析活卡彼此之間**跑同樣兩個謂詞：**實作抓到 1 組，契約額外抓到 10 組**（§7 輸出 [D] 段）。
也就是說，`find_conflicts` 今天對現役卡就已經漏報 10 組——`file:tests/`、`file:src/cpbl/models/`、
`file:web/`、`file:docs/research/`、`file:migrations/` 這幾個目錄級宣告全部形同虛設。

`WF_RESOURCE_WRITESET1` §2.2 是**設計文件，不是實作**。這與該卡 §8.7／§8.8 的
`--ignore-unparseable`／`UNPARSEABLE_EXEMPTION_SUNSET` 在 `cli/src` 命中為 0 是同一個形狀：
契約寫了、碼沒寫、而讀契約的人會以為它在跑。

**本卡不修它**（射程外，且那是 `cli/src/**`）。列在這裡是因為驗收條 4 要求「逐組列出並解決」——
第 5.1 組我給了解決方式；5.2 的 5 組**在現行實作下不會被 `assign` 擋**，
所以它們是不是「須解決的衝突」取決於採用哪個謂詞，這件事需求方要先裁定（§4 之外的第 7 項）。

---

## 6. 母體外的硬阻擋：`WF-REVIEW-EVENT-MARKER-CONTRACT1` #15

### 6.1 事實

- repo `ruan6047/ai-workflow`，`🏁完成`，**不帶** `state-plane-mig1` marker → 不在封閉母體。
- 它**有**正確的獨立標題行 `## 資源宣告`（精確 1 行）也**有** sentinel，但仍解析失敗。
- 真因與 MIG1 那 33 張不同，是**真的排版損壞**：body 內有 1 處字面 `\n`，位置就在 `## Log` 之前。
  `## Log` 的獨立標題行數為 **0**，而 `## Log` 字樣存在 → `_split_at_log` fail-closed 拒絕定位。
- 2026-08-12 §9.7b 釘選時「母體外的解析失敗」為 0，**這一張是新增的**。
- 依 `WF_RESOURCE_WRITESET1` §8.7.1／§8.8.1，母體外的解析失敗**不可豁免**。
  今天它沒造成 fail-open（`🏁完成` 在 `TERMINAL_STATUSES`，`assign` 解析前就 `continue`），
  但驗收條 3 的「解析失敗數須為 0」把它算進去。

### 6.2 附帶發現：`amend` 的排版修復 runbook 對這唯一的真實案例也不成立

`_LAYOUT_VERIFY_SNIPPET` 的判準是 `o.count("\n## Log\n\n")`（四個字元皆為字面，即 `\`＋`n`）。
#15 的實際損壞是**字面 `\n` 後接 `## Log` 再接兩個真換行**，逐字為 `'。\n\\n## Log\n\n'`（Python repr）。
把該判準原樣套上去：

```
runbook 判準 t = '\\n## Log\\n\\n'
body 中 t 的出現次數 c = 0
→ runbook 步驟 4 會印：NG：原文有 0 處候選標記，本程序只處理恰好 1 處
```

**本 repo 目前唯一一個真正排版損壞的 body，那份人工程序判它「不處理」。**
這不在本卡射程，記在此處免得下一個人重新撞一次。

---

## 7. 探針（可原樣抽出執行）

抽出與執行：

```bash
cd /path/to/ai-workflow
sed -n '/^# OPS-MIG1-CLAIMS/,/^# --- 探針結束/p' docs/reference/MIG1_CLAIMS_BACKFILL.md > /tmp/mig1_probe.py
cd cli && uv run python /tmp/mig1_probe.py
```

```python
# OPS-MIG1-CLAIMS-BACKFILL1 探針。依賴：wf_cli（gh CLI 已登入）。唯讀：不寫 repo、不寫 GitHub。
# 需外部資源：網路與 gh 憑證（list_items 打 GitHub API，1 次 GraphQL）。散文註解，非機制（同 §9.7b）。
import json, re, sys
from collections import Counter
from wf_cli.gh import default_runner
from wf_cli.project import list_items, resolve_project
from wf_cli.resources import ResourceDeclarationError, parse_block, try_parse_block, find_conflicts
from wf_cli.commands.assign_cmd import TERMINAL_STATUSES, is_owner_assigned

SENTINEL = "<!-- resource-claims:begin -->"
HEADING = "## 資源宣告"
MIG1_MARK = re.compile(r"<!--\s*state-plane-mig1:card_id=")
MIG1_JSON = re.compile(r"##\s*資源宣告（機器可讀[^\n]*\n```json\s*(?P<j>.*?)```", re.DOTALL)
ISSUE_URL = re.compile(r"https://github\.com/([^/]+/[^/]+)/issues/")

def key(res):
    """WF_RESOURCE_WRITESET1 §2.1 的比對鍵 K(r)：分量序列、捨棄空與 `.`、NFC＋casefold。"""
    import unicodedata
    p = res[len("file:"):]
    return tuple(unicodedata.normalize("NFC", c).casefold()
                 for c in p.split("/") if c not in ("", "."))

def contract_intersect(x, y):
    """§2.2 謂詞：其一為另一之前綴（含相等）。只對 file: 定義；非 file: 退回完全相等。"""
    if not (x.startswith("file:") and y.startswith("file:")):
        return x == y
    kx, ky = key(x), key(y)
    n = min(len(kx), len(ky))
    return kx[:n] == ky[:n]

items = [it for it in list_items(default_runner, resolve_project(default_runner, "ruan6047", 4))
         if it.card_id]

# --- A. §9.7b 封閉母體普查（逐字沿用其輸出格式）---
fail = []
for it in items:
    try: parse_block(it.body)
    except ResourceDeclarationError: fail.append(it)
in_cohort = [it for it in fail if MIG1_MARK.search(it.body or "")]
with_worktree = [it.card_id for it in in_cohort
                 if (it.branch_worktree or "—").strip() not in ("", "—")]
no_repo = sum(1 for it in items if not ISSUE_URL.match(it.issue_url or ""))
print("[A] §9.7b 封閉母體普查")
print(f"  Project #4 有卡ID 的 item {len(items)} 張；宣告無法解析 {len(fail)} 張")
print(f"  帶 state-plane-mig1 marker（封閉母體）：{len(in_cohort)}")
print(f"  帶 resource-claims sentinel 卻仍失敗：{sum(1 for it in fail if SENTINEL in (it.body or ''))}")
print(f"  母體外的解析失敗（＝不可豁免、硬阻擋）：{len(fail) - len(in_cohort)}")
for it in fail:
    if not MIG1_MARK.search(it.body or ""):
        print(f"    └ 母體外：{it.card_id} #{it.issue_number} [{it.delivery_status}] {it.issue_url}")
print(f"  母體中已註冊「分支worktree」者：{with_worktree or 0}")
print(f"  全 item 中 issue_url 無法解析出 owner/repo 者：{no_repo}")
scopes = Counter()
for it in in_cohort:
    m = MIG1_JSON.search(it.body or "")
    scopes[repr(json.loads(m.group("j")).get("db_scope")) if m else "（無 JSON）"] += 1
print(f"  母體內佔位 db_scope 分佈：{dict(scopes)}")

# --- B. amend 可達性：wfcli amend --resources 能不能寫進去 ---
# amend_cmd.run 的資源路徑第一行是 parse_block(item.body)；card.amend_resource_block 再要求
# 「## 資源宣告」在 Log 之前**恰好一個獨立標題行**。兩者任一不成立即 return 2。
print("\n[B] wfcli amend --resources 可達性（母體 33 張）")
reach = 0
for it in in_cohort:
    head = (it.body or "").split("\n## Log")[0]
    exact = sum(1 for line in head.splitlines() if line.strip() == HEADING)
    if exact == 1:
        reach += 1
print(f"  body 內有恰好一個獨立標題行 `{HEADING}`（＝amend 可達）：{reach}/{len(in_cohort)}")
print(f"  amend 不可達：{len(in_cohort) - reach}/{len(in_cohort)}")
alt = Counter()
for it in in_cohort:
    for line in (it.body or "").splitlines():
        if line.startswith("## ") and "資源宣告" in line:
            alt[line.strip()] += 1
print("  實際存在的標題行逐字：")
for k, v in alt.items():
    print(f"    {v:>2} 張 → {k!r}")

# --- C. assign 比對母體的 fail-open 規模 ---
active = [it for it in items
          if (it.delivery_status or "") not in TERMINAL_STATUSES and is_owner_assigned(it.owner_field)]
parsed = {it.card_id: d for it in active if (d := try_parse_block(it.body)) is not None}
print("\n[C] assign 交集檢查母體")
print(f"  非終態＋已認領（assign 實際比對的母體）：{len(active)} 張")
print(f"  其中可解析：{len(parsed)}；被靜默略過（fail-open）：{len(active) - len(parsed)}")

# --- D. 相交：實作謂詞 vs 契約謂詞 ---
print("\n[D] 現役可解析活卡的相交（實作 find_conflicts vs 契約 §2.2 前綴謂詞）")
ks = sorted(parsed)
impl = ctr = 0
for i in range(len(ks)):
    for j in range(i + 1, len(ks)):
        a, b = parsed[ks[i]], parsed[ks[j]]
        if find_conflicts(a, ks[j], b):
            impl += 1
            print(f"  [實作抓到] {ks[i]} × {ks[j]}：{find_conflicts(a, ks[j], b)}")
        pairs = [(x, y) for x in a.resources for y in b.resources
                 if contract_intersect(x, y) and x != y]
        if pairs:
            ctr += 1
            print(f"  [僅契約抓到] {ks[i]} × {ks[j]}：{pairs}")
print(f"  實作謂詞相交組數：{impl}；契約謂詞額外相交組數：{ctr}")
# --- 探針結束 ---
```

### 7.1 BEFORE（2026-08-18 21:12 +0800）

```text
[A] §9.7b 封閉母體普查
  Project #4 有卡ID 的 item 155 張；宣告無法解析 34 張
  帶 state-plane-mig1 marker（封閉母體）：33
  帶 resource-claims sentinel 卻仍失敗：1
  母體外的解析失敗（＝不可豁免、硬阻擋）：1
    └ 母體外：WF-REVIEW-EVENT-MARKER-CONTRACT1 #15 [🏁完成] https://github.com/ruan6047/ai-workflow/issues/15
  母體中已註冊「分支worktree」者：0
  全 item 中 issue_url 無法解析出 owner/repo 者：0
  母體內佔位 db_scope 分佈：{"'none'": 11, "'read'": 10, "'write'": 8, "'schema'": 1, 'None': 3}

[B] wfcli amend --resources 可達性（母體 33 張）
  body 內有恰好一個獨立標題行 `## 資源宣告`（＝amend 可達）：0/33
  amend 不可達：33/33
  實際存在的標題行逐字：
    33 張 → '## 資源宣告（機器可讀；`null`／`[]` 代表未正式宣告，不代表無資源）'

[C] assign 交集檢查母體
  非終態＋已認領（assign 實際比對的母體）：42 張
  其中可解析：21；被靜默略過（fail-open）：21

[D] 現役可解析活卡的相交（實作 find_conflicts vs 契約 §2.2 前綴謂詞）
  [僅契約抓到] DAILY-MIXED-DAY-UX1 × ML-WP-ROLLWIN1：[('file:tests/test_daily_summary.py', 'file:tests/')]
  [僅契約抓到] DAILY-MIXED-DAY-UX1 × UX-WINPROB-CURVE-MIGRATE1：[('file:web/src/components/daily-hub.tsx', 'file:web/'), ('file:web/src/lib/daily-summary.ts', 'file:web/'), ('file:web/src/lib/daily-summary.test.ts', 'file:web/'), ('file:tests/test_daily_summary.py', 'file:tests/')]
  [僅契約抓到] DATA-BOX-REVISION-SNAPSHOT1 × DOC-LIVELOG-SEMANTICS-GAP1：[('file:migrations/', 'file:migrations/016_game_log.sql')]
  [僅契約抓到] DEV-ROADMAP-LINES-SILENT-ZERO1 × ML-WP-ROLLWIN1：[('file:tests/test_roadmap_lines.py', 'file:tests/')]
  [僅契約抓到] DEV-ROADMAP-LINES-SILENT-ZERO1 × UX-WINPROB-CURVE-MIGRATE1：[('file:tests/test_roadmap_lines.py', 'file:tests/')]
  [僅契約抓到] ML-WP-ASOF-PUSHDOWN1 × ML-WP-ROLLWIN1：[('file:src/cpbl/models/winprob_val.py', 'file:src/cpbl/models/'), ('file:src/cpbl/models/winprob_strength.py', 'file:src/cpbl/models/'), ('file:tests/test_winprob_val.py', 'file:tests/')]
  [僅契約抓到] ML-WP-ASOF-PUSHDOWN1 × UX-WINPROB-CURVE-MIGRATE1：[('file:tests/test_winprob_val.py', 'file:tests/')]
  [僅契約抓到] ML-WP-CAL1-RERUN1 × ML-WP-ROLLWIN1：[('file:src/cpbl/models/winprob_cal.py', 'file:src/cpbl/models/'), ('file:docs/research/ML-WP-CAL1-RERUN1/', 'file:docs/research/'), ('file:tests/test_winprob_cal.py', 'file:tests/')]
  [僅契約抓到] ML-WP-CAL1-RERUN1 × UX-WINPROB-CURVE-MIGRATE1：[('file:tests/test_winprob_cal.py', 'file:tests/')]
  [僅契約抓到] ML-WP-ROLLWIN1 × RESEARCH-REASON-RESTATE1：[('file:docs/research/', 'file:docs/research/GAME-RECAP-WP-VAL1_RESULTS.md'), ('file:docs/research/', 'file:docs/research/GAME-RECAP-WP-VAL1-FIX1_ERRATA.md'), ('file:docs/research/', 'file:docs/research/GAME-RECAP-WP-STRENGTH1_RESULTS.md')]
  [實作抓到] ML-WP-ROLLWIN1 × UX-WINPROB-CURVE-MIGRATE1：['file:tests/']
  實作謂詞相交組數：1；契約謂詞額外相交組數：10
```

### 7.2 「可原樣抽出執行」的驗證（不是宣稱）

AFTER 那一次**不是**跑 scratchpad 裡的副本，是跑從本檔 `sed` 抽出來的檔案：

```
$ sed -n '/^# OPS-MIG1-CLAIMS/,/^# --- 探針結束/p' docs/reference/MIG1_CLAIMS_BACKFILL.md > /tmp/mig1_probe.py
抽出行數: 104
$ python3 -c "import ast; ast.parse(open('/tmp/mig1_probe.py').read())"
AST 剖析通過
$ cd cli && uv run python /tmp/mig1_probe.py    # ← §7.3 的輸出由這一行產生
```

（`WF_RESOURCE_WRITESET1` R2-001 的教訓：文件內的探針抽出來即 `SyntaxError`，而沒有任何檢查會發現。
故此處把抽出、剖析、執行三步都跑過，不只寫「可抽出」。**唯一未驗的是低版本相容性**——
本輪只在 CPython 3.12.13 上剖析與執行過，未在 `requires-python` 下限 3.11 上驗。）

### 7.3 AFTER（2026-08-18 21:17 +0800）

**與 §7.1 的 BEFORE 逐字相同（`diff` 零輸出），這是預期而非疏漏。**
本輪對 GitHub 的寫入次數為 0——§1 的阻斷器使 `amend --resources` 對母體 33 張全部 `return 2`，
故解析失敗數維持 34、封閉母體維持 33。

**驗收條件 3「解析失敗數須為 0、E1 母體清單同步清空」因此未達成**，原因見 §1，出路見 §1.4。
把 AFTER 貼在這裡而不是省略，是因為「補宣告這件事今天在機器上完全沒有發生」本身就是本卡最重要的輸出；
一份看不出 before/after 沒有差別的報告，會讓人以為它動了什麼。

---

## 8. 我沒驗到的

- **21 張的宣告一個字也沒寫進 GitHub。** 本輪對 GitHub 的寫入次數為 0（唯一的 `amend` 呼叫帶 `--dry-run`）。
  §3 的提案宣告**沒有經過 `ResourceDeclaration.__post_init__` 以外的任何機器驗證**——
  我在本機構造同樣的物件跑過前綴檢查與 `find_conflicts`，但沒有經過 `amend` 的完整路徑。
- **「spec 逐字」的射程限於 `docs/tasks/<CARD_ID>.md`。** 我沒有去讀各卡引用的上游文件
  （`ops-remote-crawler-rollout.md`、`OFFICIAL_DATA_GAP1_RESULTS.md`、`PRODUCT_UX_BLUEPRINT.md`、
  `ml-sim1-spec.md` 等）。那些文件可能指名更多寫入標的，也可能推翻我對「射程未定」的判定。
  **12 張判不定者中，若有哪張其實在上游文件裡已把射程寫死，那是我漏掉的。**
- **§3.1 六張的「宣告內容與實際會寫的檔案相符」我只驗到 spec 逐字這一層。** 驗證條 2 要求
  「抽驗至少 5 張…非形式上填滿」——我對 `UX-TEAM-FIELD-HIST1` 與 `MATCHUP-DATA2` 有真的去 grep
  程式碼確認端點與函式位置（`routers/leaders.py:556`、`api/matchups.py`、`teams/[code]/page.tsx:46`），
  對 `ML-PA-SIM-*` 只確認 `src/cpbl/models/pa_sim.py` 存在、**沒有讀它確認改動真的落在該檔**，
  對 `DEV-VERIFY-TM-ASSERTS1` 只確認 `scripts/verify_deep_tm_backfill.py` 存在。
  **這六張沒有一張達到「宣告 × 實際 diff 對帳」的強度**——那需要卡真的被執行過才驗得到。
- **Initiative 三張的寫入語意是推論。** 「基線變更會寫回 `docs/tasks/INIT-*.md`」這件事我沒有找到
  canonical 明文，只有該檔內部的「基線變更紀錄」節與 cutover 前的 commit 歷史；
  三張自 2026-08-01 起無 commit，**所以我連「它還會被寫」都沒有觀測證據**。
- **`is_owner_assigned("ruan6047（Design Gate）") == True` 的治理語意我沒查。** 派工包也標了同一個未知。
  這 21 張因此「已認領」而留在比對母體裡——若那是意外而非慣例，正確處置可能是改 owner 而不是補宣告。
- **§5.2 的 5 組契約謂詞重疊我沒有解決，只列出。** 因為它們在現行實作下不會被 `assign` 擋，
  「要不要解決」取決於採用哪個謂詞——而那是待裁定項。**若查核者認為驗收條 4 要求的是無條件解決，這一條就是未達成。**
- **`ML-FIELD-OF1` #66 的 body 沒有 `## Log` 區段**（0 個獨立標題行且無字面 `\n`）。
  `_split_at_log` 對此回傳 `(body, "")` 不拋錯，故不構成第二個缺陷；
  但「為什麼 2026-08-13 的批次 handoff 沒有在它身上留下 Log 行」我沒有追。
- **GitHub 配額／5xx**：本輪 `wf_cli.list_items`（＝`gh project item-list`，2 點／次）共 **4 次**——
  母體重量測 1、BEFORE 1、AFTER 1，加上 `wfcli amend --dry-run` 內部 1。單卡查詢一律走 REST。
  **無 5xx、無空回應、無因配額而未取得的項目。**
