# #231 WF-POLLUTION-MANIFEST-STALE1 守衛回綠與 manifest 的失效偵測
- state: closed  created: 2026-09-01T14:13:08Z  closed: 2026-09-01T17:43:57Z
- url: https://github.com/ruan6047/ai-workflow/issues/231
- comments: 8

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；單一守衛與其 manifest 的修復；風險在「該不該擴白名單」的判斷，⛔ 不在演算法）　查核：待指派（建議 主力型；T3 依規需獨立查核；查核重點是負控會不會響、load-bearing 檢查抓不抓得到死條目——⛔ 不得只看主跑轉綠）
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：可稽核＋防低級事故——守衛紅了沒有人知道（不在 CI）、manifest 失效沒有東西會喊，兩者都使「跑綠了」這個訊號失去意義（防低級事故軸）

## 簡介
<!-- card-brief:begin -->
適用時機：要讓 main 上的 pollution_check 回到 rc=0，或要判斷「搬動／刪除被核可的檔案時，pollution-allowlist.json 會不會靜默失效」時。本卡處理三件可觀測的事：main 現行 rc=1 的三筆 unapproved 與兩筆 stale-entry；該 manifest 是否需要 load-bearing 檢查（canonical_citation_scan 的 EXCLUSIONS 有、它未經量測）；以及 stale_entries 不進 rc 這個已登記敞口的處置。階段計畫：需求→研究→執行→審核→結案。級別依據：改守衛判準與其 manifest 會改變所有後續卡的紅綠判定 ⇒ T3。

⛔ 非射程：不改 prose_number_scan（歸 #213）；不動 WF-REDESIGN-W2B 的分支或其交付物；不以擴充 allowlist 條目作為唯一手段而不先答「該不該擴」。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：同一支 scripts/pollution_check.py 在相差一個 commit 的兩個 SHA 上輸出不同：950b3e278371e948900dd381cd7b4e595882c6b0 為 rc=0、unapproved_count 0、stale-entry 行 0；fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2 為 rc=1、unapproved_count 3、stale-entry 行 2。3 筆 unapproved 全在 archive/wave-specs/w2a.md；2 筆 stale-entry 訊息為「宣告 1 實得 0」。scripts/pollution-allowlist.json 對舊路徑字串的 grep -c 為 0。.github/ 下對 pollution_check 的 grep 為 0 命中。stale_entries 不進 rc 一項已於 #219 的 W2A 交付報告未驗清單第 10 項逐字登記。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:scripts/pollution_check.py",
    "file:scripts/pollution-allowlist.json",
    "file:cli/tests/test_pollution_check.py",
    "file:.github/workflows/ci.yml"
  ]
}
```
<!-- resource-claims:end -->

## 卡面表單
<!-- card-face-form:v1:begin -->
```json
{
  "list_convergence": [],
  "schema_version": "1",
  "stage_plan": [
    {
      "goal": "清單項 #231 升級為卡，量測逐字住卡面",
      "stage": "需求"
    },
    {
      "goal": "先答「三筆 unapproved 該怎麼處置」，三個候選各附可證偽條件",
      "stage": "研究"
    },
    {
      "goal": "依研究結論修 main 回綠＋補 load-bearing 檢查＋裁定 stale_entries 是否進 rc",
      "stage": "執行"
    },
    {
      "goal": "獨立查核：負控是否真的會響、load-bearing 檢查是否抓得到死條目",
      "stage": "審核"
    },
    {
      "goal": "結案報告七段經需求方確認",
      "stage": "結案"
    }
  ],
  "tier_basis": {
    "blast_radius": "全 repo 後續卡的驗證項；⛔ 不含 cpbl（該側不跑本守衛）",
    "recoverability": "可逆（git revert）；但期間所有卡的該驗證項不可達，且錯誤的 allowlist 條目會讓真污染靜默通過",
    "sensitive_surfaces": "scripts/pollution_check.py 與其 manifest——它的紅綠是所有後續卡的驗證項之一（#220 卡面「驗證」即含「污染符 grep 零命中」）"
  }
}
```
<!-- card-face-form:v1:end -->

## 驗收條件

- [ ] 研究階段先答一題並寫下判準：archive/wave-specs/w2a.md 的三筆 unapproved 該以「加核可條目」「把 archive/ 移出語料」「改 BASE_SHA」何者處置——⛔ 未答不得動 allowlist；三個候選各須寫出「什麼觀察會讓本案不成立」
- [ ] main 上 python3 scripts/pollution_check.py 回到 rc=0，且 unapproved_count 與 stale-entry 行數皆為 0；同時附負控：對一個刻意植入污染符的探針檔，同一支工具仍會響
- [ ] pollution-allowlist.json 取得與 canonical_citation_scan.py 的 EXCLUSIONS 同形的 load-bearing 檢查（未命中的條目即轉紅），並由 cli/tests/test_pollution_check.py 釘死；⛔ 不得只加註解
- [ ] stale_entries 是否進 rc 由本卡明示裁定並就地留註解（含「刻意/為什麼/⛔不得推出什麼」三要素）；若維持不進 rc，須寫出該決定的可證偽條件
- [ ] pollution_check 納入 .github/workflows/ci.yml，使同類破壞不再是靜默的；⛔ 若決定不納入，須在卡面寫明理由與替代偵測路徑

## 驗證

- [ ] main 上 pollution_check rc=0 且兩項計數皆 0
- [ ] ⭐ 負控：探針檔仍會響（⛔ 非零命中即通過）
- [ ] load-bearing 檢查對刻意插入的死條目轉紅
- [ ] pytest 全綠

## Log

- 2026-09-01T22:14:19+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-09-01T22:14:19+08:00 upgrade by wf-cli → 由待審清單項 https://github.com/ruan6047/ai-workflow/issues/231 升級；清單項原文 sha256:b2c872c3284ee4325dee55476c44cdbebd16d8b90207df09441beddc77ac6bc2（原文見平台 userContentEdits 前一版）。
- 2026-09-01T22:37:40+08:00 assign by wf-cli → owner session 8aa0801f-1a4d-484d-92f7-dc1dd8c9a363@Claude Code（高階型）；分支worktree claude/wf-pollution-manifest-stale1-c6d585 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-pollution-manifest-stale1-c6d585；交付狀態 🔨執行中；實際能力層級 高階型（偏離卡面建議 主力型；偏離理由：卡面建議主力型（T3），實際為高階型＝往上偏離，⛔ 非降級。實際模型 claude-opus-5 由該 session transcript 之 model 欄機械核出（~/.claude/projects/-Users-ruanruan-Dev-ai-workflow--claude-worktrees-wf-pollution-manifest-stale1-c6d585/8aa0801f-1a4d-484d-92f7-dc1dd8c9a363.jsonl，63 筆全為該值），⛔ 非自述。W1／W2B 同形先例已留痕。）；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-09-01T22:38:28+08:00 handoff by wf-cli → owner session 8aa0801f-1a4d-484d-92f7-dc1dd8c9a363@Claude Code（高階型）；iteration 0；SHA fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2；階段 需求；踩坑回應 8 族（已檢查 3／不適用 0／發現 5）；證據 補記轉移：assign 已把 owner 與分支/worktree 寫回卡面並置交付狀態🔨執行中，但 assign 不寫階段欄。本段為正向補記 需求→研究，source_sha 取執行者開工基線 fc8b966（＝現行 origin/main，worktree HEAD 實查相同、工作區乾淨、與 origin/main 差 0 commits）。研究階段產出物＝可重跑的量測紀錄＋結論（research.md §1），⛔ 本階段無寫入授權。。
- 2026-09-02T01:43:46+08:00 handoff by wf-cli → owner ruan6047；iteration 0；SHA 13cc5f0551759934f8a9a7295de219b4c4164b3e；階段 研究；踩坑回應 8 族（已檢查 2／不適用 0／發現 6）；證據 需求方 2026-09-02 裁定停止（issuecomment-5497979970），三要件齊備：決策＝轉 🛑已停止、⛔ 不執行 AC1–AC5；原因＝量測顯示 74 筆命中中 73 筆打在仍為現行語彙的 token 上（已退役 token 僅 0 unapproved／1 approved），該守衛全史 1 個 commit、存在一天、42 筆核可條目的 rationale 全為合法引用且 0 筆導致內容被修 ⇒ 切換前構造上幾乎只產生假陽性；可證偽復活條件＝#222 切換 Initiative 的 cutover 落地使那批現行語彙真正退役，屆時重跑本卡 harness 的 token 分類量測，若已退役 token 的命中由 0/1 變為非零即推翻本裁定，復活＝開新卡。本卡產出保留於卡上：可重跑 harness 全文（issuecomment-5497181885 與 5497682648），PM 已兩次獨立重現（88 PASS/0 FAIL、17 PASS/0 FAIL）；候選 2 與候選 3 皆已證偽。⛔ 未執行任何 AC，受管檔零寫入。；收尾清理：已清除 worktree、本地分支；遠端分支 本來就不存在。


## Comment 5495655101 · 2026-09-01T14:39:11Z

派工留痕（2026-09-01，PM）

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`；發文者身分不等於決策者身分。需求方於本機 Claude Code 對話中裁示派工並提供執行者三值。

- 執行者：`session 8aa0801f-1a4d-484d-92f7-dc1dd8c9a363@Claude Code（高階型）`
- 分支：`claude/wf-pollution-manifest-stale1-c6d585`　worktree：`/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-pollution-manifest-stale1-c6d585`
- 基線：`origin/main` = `fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2`。PM 實查該 worktree：`HEAD` 相同、`git status --porcelain` 0 行、`git rev-list --count origin/main..HEAD` = 0 ⇒ 派工前未有任何既成改動。

**能力層級偏離（往上）**：卡面建議執行 主力型（T3），實際 **高階型**。實際模型 `claude-opus-5` 由該 session transcript 的 `model` 欄機械核出（63 筆全為該值），⛔ 非自述。偏離理由已隨 `assign` 寫入 Log。

**階段**：`assign` 置交付狀態 🔨執行中但不寫階段欄，已以 handoff 正向補記 `需求 → 研究`（8 族清冊：已檢查 3／發現 5），現狀態為 **🔬研究中**。

**本輪射程＝研究階段，⛔ 無寫入授權**：卡面資源宣告四項（`pollution_check.py`／`pollution-allowlist.json`／`test_pollution_check.py`／`ci.yml`）屬**執行階段**。本輪只答 AC0：三筆 `unapproved` 該以「加核可條目」「把 `archive/` 移出語料」「改 `BASE_SHA`」何者處置，三個候選各附「什麼觀察會讓本案不成立」。

**⚠️ 執行階段的排程限制（PM 量測，寫在此處以免日後被當成新發現）**：本卡與 `WF-REDESIGN-W2B`（#220）寫入集交集實查為**空**，並行安全。但 `pollution_check` 的語料是 `git diff --name-only --diff-filter=d <釘死 BASE_SHA>` 的 post-image ⇒ **W2B 一旦 merge，它動過的四個檔（`docs/CONTRACT_TOOL_RECONCILE.md` 22 筆／`ADOPTION.md` 4／`cli/tests/test_contract_tool_reconcile.py` 2／`templates/handoff-contract.md` 1，共 29 筆）就進入 main 的語料**。四檔自 `f656a678` 起皆已被改過，逐一實查為「是」。⇒ 本卡 AC1「main 回到 rc=0」若在 W2B merge 前達成，W2B merge 當下即再度轉紅。**建議執行階段排在 W2B merge 之後**，⛔ 本輪研究不受此限。

**PM 未驗**：`SELF_REFERENCE_PATHS` 是否涵蓋得到 `archive/`、`stale_entries` 不進 rc 的**敞口大小**——兩者 PM 都未實跑，是本輪要量的。

**派工包已知落差（PM 自陳）**：(1) 本卡清單項未經第二 PM 收件裁決——提案者、量測者、與造成該差異之 commit 的作者都是同一個 PM session，收件閘獨立性不成立，已逐字寫在 #231 末段；(2) 標準條款第 6 條的「有副作用入口清單」在本 repo 無權威居所，由 PM 代填並標明為推導；(3) PM 在派工包首版把「`stale_entries` 是刻意還是遺漏」列為待查項，實際上 #219 早有逐字記載為**刻意**，已於發包前更正並逐字登記為 `F-研究-12` 的現成反例。


## Comment 5496594916 · 2026-09-01T15:49:03Z

## PM 更正兩處（2026-09-01）＋研究交回的閘門狀態

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`。研究階段的交還報告由執行者 session `8aa0801f-1a4d-484d-92f7-dc1dd8c9a363@Claude Code（claude-opus-5）` 撰寫，經需求方轉交。

### 更正 1 · 派工包 §4／§8-1 引用了一個已不存在的居所（PM 之過）

派工包逐字寫「`#231`（本卡）：清單項本文即量測紀錄；**末段逐字標明「提案者即 PM、⛔ 未經第二 PM 收件裁決」**」。執行者回報該引用 0 命中，PM 實查證實：`gh issue view 231 --json body | grep -c "提案者即 PM\|第二 PM 收件裁決"` ⇒ **0**。

**成因**：`wfcli open --from-issue` 就地升級時以**卡面**覆蓋原清單項 body ⇒ 清單項原文（含該段警語）不再存在於現行 body。PM 在寫派工包時引用的是**開卡前**的內容，⛔ 未回讀確認。⚠️ 這與「修過期引用最容易留下新的過期引用」同族。

**逐字補回**（原文，PM 自 open 前的草稿還原）：

> ⚠️ **提案者即 PM，⛔ 未經第二 PM 收件裁決。** 本項的量測與提案出自同一個 session，該 session 亦為造成上述兩 SHA 差異之 commit 的作者。⇒ 收件閘的獨立性在本項上**不成立**，逐字標明於此，由需求方決定是否補一次第二 PM 收件裁決。

⇒ 該事實**仍然成立**，只是居所從清單項 body 移到本留言。

### 更正 2 · PM 對 `P1-38` 的引用超過 repo 實據（PM 之過）

派工包逐字寫「`P1-38`（`prose_number_scan` 那條線）**跑了九輪**，其中一輪的失敗形狀就是**白名單自我擴張**」。

PM 實查 repo 內 `P1-38` 的直接記載**只有一處**——`stage-rules/pm-conduct.md:88`：

> 引用 0 命中前先證工具會響（2026-08-31 P1-38 **三輪**實據：R14「裸現況數終掃 0 命中」係**假陰性掃描器的假安心**）

⇒ repo 記載的是**三輪**與**假陰性掃描器**，⛔ 不是「九輪」與「白名單自我擴張」。PM 那句取自 `#220` 的 PM 側經驗，**⛔ 不是 repo 可引用的實據**。執行者將其降級為「`#220` 的 PM 類比、⛔ 不引為既成實據」，**該處置正確，PM 接受**。

⚠️ **這件事對本卡有實質影響**：AC0 的三個候選中，PM 曾以「白名單自我擴張是 P1-38 踩過的坑」作為對候選 1（加核可條目）的警戒依據。該依據既已降級為類比，**對候選 1 的警戒強度隨之下降**——⇒ 候選 1 若要出線，其正當性須來自本卡自己的量測，⛔ 不得再引 P1-38 為據。

### 研究交回的閘門狀態（PM 尚未執行 handoff）

執行者交還報告載「**結論（需求方已裁定）：AC0 出口＝候選 1**」。**PM 實查本卡狀態面：留言數 1（PM 的派工留痕），⛔ 無任何裁定留痕。** ⇒ 該裁定若存在，僅存在於執行者 session 的對話中，**狀態面無可稽核紀錄**。PM ⛔ 不以無留痕的裁定為 handoff 的 evidence。

另依 `stage-rules/research.md` §3 逐字：「③ 交回＝量測紀錄＋結論（討論形狀⛔ 非送審形狀）。⭐ **③ 與 ④ 之間插討論回合——需求方提問、執行者答；出口由討論定**。④ **查核者只驗量測可重跑**」——本卡尚未跑討論回合與 ④。

⇒ **PM 暫不執行 `handoff --next-stage implementation`**，上呈需求方決定：(a) 補裁定留痕並跑討論回合＋④；或 (b) 明示豁免其中之一。

### PM 未驗（逐項）

1. 執行者的六輪量測 harness（`scratchpad/harness.py`）PM **未重跑**——該檔在 session scratchpad，⚠️ session 結束可能被清。
2. 三筆新增條目的 `line_sha1`、兩筆待刪條目的 index（40／41）、AC3 接線點行號——PM **未複驗**。
3. 執行者交 PM 裁決的四項（範圍外的 `chmod`／複製／symlink 行為、`canonical_citation_scan.EXCLUSIONS = {}` 從未載過真實條目等）PM **未查證**。


## Comment 5496613910 · 2026-09-01T15:50:28Z

## 需求方裁定轉錄 — `WF-POLLUTION-MANIFEST-STALE1` AC0（2026-09-01）

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`；⚠️ **發文者身分不等於決策者身分**。

⚠️ **PM 更正自己前一則留言**（`issuecomment-5496594916`）：該則寫「本卡狀態面⛔ 無任何裁定留痕 ⇒ 該裁定若存在，僅存在於執行者 session 的對話中」。**對狀態面的觀察正確，但 PM 由此推論裁定可疑，那是錯的**——需求方於執行者 session 中確實已裁定。PM 依需求方指示讀取該 session 的 transcript 後確認，逐字轉錄如下。

**決策定位**：需求方於 session `8aa0801f-1a4d-484d-92f7-dc1dd8c9a363`（本卡執行者 session，Claude Code）中的第 6 則訊息，逐字為：

> 按照你建議

**該訊息所同意的對象**（其前一則 assistant 訊息的結論段，逐字）：

> ## 建議：**候選 1（加核可條目）**，且**必須綁 AC3 把 `stale_entries` 進 rc**
>
> 一句話：候選 2 用「守衛不看 `archive/`」換低維護，而 R5 實測那等於開一條 `git mv` 洗白路徑；候選 1 保住守衛強度，它唯一的病（條目會爛）**恰好就是 AC3 要裁的那件事**，而我實測 stale 進 rc **⛔ 不新增任何一次誤紅**。

**該建議自帶的翻轉條件**（同一則，逐字）：

> - 你裁 **AC3 = stale 進 rc** → 候選 1 成立…誤紅風險實測 **0**
> - 你裁 **AC3 = 維持不進 rc** → **候選 1 不健全**，那時候選 2 反而是兩害相權的較輕者…⛔ 這種情況我⛔ 不推薦候選 1。

⇒ **裁定內容＝AC0 出口為候選 1，且與 AC3「`stale_entries` 進 rc」綁定。** 兩者⛔ 不可分開執行。

transcript 位於需求方本機 `~/.claude/projects/-Users-ruanruan-Dev-ai-workflow--claude-worktrees-wf-pollution-manifest-stale1-c6d585/8aa0801f-1a4d-484d-92f7-dc1dd8c9a363.jsonl`，可核。

### 同 session 內另兩則需求方訊息（一併轉錄，因其改變了執行路徑）

- 第 7 則逐字：「先走 handoff 開執行卡」
- 第 8 則逐字：「應該交還給ＰＭ處裡」

⇒ 需求方於同一 session 內修正：handoff 由 PM 執行，⛔ 非執行者。與標準條款第 6 條一致。

### 執行者六輪量測的關鍵結果（逐字取自其交還報告，⛔ PM 未重跑）

- **R5 證偽候選 2**：活路徑髒檔 `unapproved=1` → `git mv` 進 `archive/` → `unapproved=0` ⇒ 洗白路徑成立。
- **候選 3 早已證偽**：`BASE=fc8b966` ⇒ 掃 0 檔、`total_hits=0`、rc=**0**、42 條目全死。
- **候選 1 成本有界**：42 → 45（今日）→ **58**（封存計畫全走完）；待封存母體＝`docs/research/drafts/` 下 6 檔共 13 筆。
- **manifest 腐爛速率**：**1911 秒／1 commit** 即出現死條目。
- **R4 對 PM 的更正**：`P1-38` 的 repo 內直接記載是「假陰性掃描器的假安心」，⛔ 非白名單自我擴張；「九輪」查無實據。**PM 已於前一則留言接受此更正。**

### PM 未驗（逐項）

1. 六輪量測 PM **全部未重跑**。⚠️ 執行者自陳 **R1／R5／R6 三輪的探針尚未落成腳本**，只在該 session 的 heredoc 跑過 ⇒ 目前**不具備交給查核者重跑的形式**。
2. 三筆新增條目的 `line_sha1`、兩筆待刪條目的 index（40／41）、AC3 接線點行號——PM 未複驗。
3. 執行者交 PM 裁決的四項（`chmod`／複製／symlink 的語料行為屬範圍外、`canonical_citation_scan.EXCLUSIONS = {}` 從未載過真實條目等）PM 未查證。


## Comment 5497181885 · 2026-09-01T16:34:26Z

## PM 轉貼：研究階段 harness 全文（可重跑居所）＋ PM 獨立重現結果

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`。下方 harness 由執行者 session `8aa0801f-1a4d-484d-92f7-dc1dd8c9a363@Claude Code（claude-opus-5）` 撰寫，經需求方轉交，PM 逐字轉貼。

⚠️ **居所說明**：執行者的原檔在其 session scratchpad（session 結束可能被清）⇒ 依 PM 補件要求落在本留言，⛔ 不進 repo（研究階段寫入授權為無，且 `measure.py` 不在卡面資源宣告四項內）。

### ⭐ PM 獨立重現（⛔ 非採信執行者輸出）

PM 將全文轉錄成檔後實跑：

```
python3 wf231_harness.py --src /Users/ruanruan/Dev/ai-workflow
→ ==== 總計 88 PASS / 0 FAIL ====   rc=0
```

⇒ **`stage-rules/research.md` §3 的「④ 查核者只驗量測可重跑」在 PM 這一側已先驗過一次可重跑**（⛔ 不取代查核者的 ④）。

⚠️ **sha256 不相符屬預期**：執行者宣稱 `00d16109431eb46a1f7973d78f3214b3575dc785dc4b3f3274a2588ce5929dbd`（528 行）；PM 的轉錄檔為 `e1cff84ae6daee78df65029b26478a148d58adb6d10616be0f24db55a2a37f31`（529 行）。**PM 是從對話訊息轉錄、⛔ 非原檔複製**，尾端換行等空白差異即足以改變雜湊。⇒ **查核者請以本留言的全文為準**（它已被 PM 實跑驗過），⛔ 不要拿執行者宣稱的 sha256 去核本留言。

### 執行方式

```bash
python3 wf231_harness.py --src /Users/ruanruan/Dev/ai-workflow
```

前置＝`git`＋`python3`（PM 本次以系統 python3 實跑成功）。⛔ 不需 `uv`／網路／`gh`／worktree。`--src` 唯讀。`--rounds nc,r0,…,r7` 可單輪。rc=0 全過／1 有 FAIL／2 環境問題。

### 全文

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF-POLLUTION-MANIFEST-STALE1 研究階段 可重跑 harness（單一自足腳本）。

它自己 clone、自己 checkout、自己造探針樹。除了一份 ai-workflow 的 repo（本機路徑或
URL）之外⛔ 不依賴任何本 session 的中間產物。

    python3 wf231_harness.py --src /path/to/ai-workflow
    python3 wf231_harness.py --src /path/to/ai-workflow --rounds r5,r6
    python3 wf231_harness.py --src /path/to/ai-workflow --work /tmp/wf231

每一條斷言印成 `[PASS]` / `[FAIL]`，末尾給總計；rc=0 全過、rc=1 有 FAIL、rc=2 環境問題。
⛔ 不寫入 --src 指到的樹：所有動作都在 --work 的 clone 與 tempdir 副本上。
"""
from __future__ import annotations

import argparse, importlib.util, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

SHA_BASE = "f656a678e540d4083740e0f30f1214e887e42c04"   # 釘死的 BASE_SHA
SHA_A    = "950b3e278371e948900dd381cd7b4e595882c6b0"   # 守衛最後一次綠
SHA_B    = "fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2"   # 守衛轉紅（本卡開卡時的 main）
SHA_M    = "13cc5f0551759934f8a9a7295de219b4c4164b3e"   # 2026-09-02 W2B 合併後的 main（merge commit⛔ 非 squash）

# 選配：W2B 的兩個量測點（⛔ 不用分支名——分支會動；W2B 若 squash merge 兩者都會消失）
#   (SHA, 語料, unapproved, 其中 archive/, 候選2 降到)
W2B_SHAS = (
    ("2c35d48d024acd8d39a4536daf9401acb2c208ea", 32, 32, 3, 29),   # 2026-09-01 首次量測點
    ("5331fc47906a3a9fb3f1805ba14b1f06aa2588f9", 33, 32, 3, 29),   # 2026-09-02 分支尖端
)
W2B_REF  = "claude/wf-redesign-w2b-templates-be3b1b"    # 僅供診斷：印出現行尖端，⛔ 不用來量

DIRTY = "舊語彙 needs-deploy 出現在這一行\n"
CLEAN = "乾淨的一行\n"

# E1 用：manifest 中兩筆死條目所錨定的原行（sha1(strip)=14fbaec95bd5…）
DEAD_LINE = ('   "excerpt": "5. （P1-31 併判準）三個腐爛自述（「短版」／「最後核實：<日期>」'
             '／行數自述 `[0-9]{3,} ?行`）改為 **checker",')
DEAD_SHA1 = "14fbaec95bd5d9829d5eda66b77e6aa638abfc2d"

_RESULTS: list[tuple[bool, str]] = []


def check(label: str, got, want) -> None:
    ok = got == want
    _RESULTS.append((ok, label))
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: got={got!r} want={want!r}")


def note(label: str, got) -> None:
    print(f"  [INFO] {label}: {got!r}")


def git(root, *a, check_rc=True):
    p = subprocess.run(["git", *a], cwd=str(root), capture_output=True, text=True)
    if check_rc and p.returncode:
        raise RuntimeError(f"git {' '.join(a)} @ {root}\n{p.stderr}")
    return p.stdout.strip()


def commit(root, msg):
    git(root, "add", "-A")
    git(root, "-c", "user.email=t@e.invalid", "-c", "user.name=t", "commit", "-qm", msg)


def load_pc(root):
    """import 受測樹自己的 pollution_check（F-研究-05：⛔ 不重打常數）。"""
    spec = importlib.util.spec_from_file_location("pc", Path(root) / "scripts" / "pollution_check.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["pc"] = m            # dataclass 需要模組已註冊，否則 3.13+ 會炸
    spec.loader.exec_module(m)
    return m


def corpus(pc, root, drop_archive=False, base=None):
    rels = pc.post_image_paths(Path(root), base or pc.BASE_SHA)
    return [r for r in rels if not r.startswith("archive/")] if drop_archive else rels


def scan(pc, root, rels, allowlist=None):
    al = Path(allowlist) if allowlist else Path(root) / "scripts" / "pollution-allowlist.json"
    r = pc.run(Path(root), rels, al)
    return r


def triple(pc, root, rels, allowlist=None):
    r = scan(pc, root, rels, allowlist)
    return len(rels), r["unapproved_count"], len(r["stale_entries"])


def copy_tree(src) -> Path:
    d = Path(tempfile.mkdtemp(prefix="wf231-")) / "r"
    shutil.copytree(src, d, symlinks=True)
    return d


# ===================================================================== 負控
def nc(P):
    print("== NC 負控：本 harness 自己會不會響 ==")
    pc = P["pcB"]
    t = Path(tempfile.mkdtemp(prefix="wf231-nc-"))
    (t / "probe.md").write_text(DIRTY, encoding="utf-8")
    (t / "e.json").write_text('{"entries":[]}', encoding="utf-8")
    r = pc.run(t, ["probe.md"], t / "e.json")
    check("temp fixture 單行污染符 unapproved（==0 則整份判定不成立）", r["unapproved_count"], 1)


# ===================================================================== R0 基線
def r0(P):
    print("== R0 卡面數字重現：950b3e2 vs fc8b966 ==")
    for lab, root, pc, want in (("950b3e2", P["A"], P["pcA"], (16, 0, 0)),
                                ("fc8b966", P["B"], P["pcB"], (17, 3, 2))):
        check(f"{lab} (語料, unapproved, stale)", triple(pc, root, corpus(pc, root)), want)
    rB = scan(P["pcB"], P["B"], corpus(P["pcB"], P["B"]))
    check("fc8b966 total_hits", rB["total_hits"], 189)
    check("fc8b966 self_reference_count", rB["self_reference_count"], 143)
    check("fc8b966 approved_entries", rB["approved_entries"], 42)
    check("fc8b966 rc", 1 if rB["unapproved_count"] else 0, 1)
    paths = sorted({h.path for h in rB["unapproved"]})
    check("fc8b966 三筆 unapproved 全在同一檔", paths, ["archive/wave-specs/w2a.md"])
    # 病因：純改名，內容 0 變動
    a = git(P["A"], "show", f"{SHA_A}:docs/research/drafts/wave-specs/w2a.md")
    b = git(P["B"], "show", f"{SHA_B}:archive/wave-specs/w2a.md")
    check("w2a.md 搬移前後內容相同（純改名）", a == b, True)


# ===================================================================== R1
def r1(P):
    print("== R1 語料對各種 git 操作的反應（合成樹，⛔ 不依賴真 repo 歷史）==")
    pc = P["pcB"]

    def mk():
        t = Path(tempfile.mkdtemp(prefix="wf231-r1-")) / "r"
        t.mkdir(parents=True)
        git(t, "init", "-q", "-b", "main")
        (t / "old_dirty.md").write_text(DIRTY, encoding="utf-8")
        (t / "clean.md").write_text(CLEAN, encoding="utf-8")
        commit(t, "base")
        return t, git(t, "rev-parse", "HEAD")

    def probe(t, base):
        rels = pc.post_image_paths(t, base)
        (t / "e.json").write_text('{"entries":[]}', encoding="utf-8")
        r = pc.run(t, rels, t / "e.json")
        return len(rels), r["unapproved_count"]

    cases = []
    t, b = mk(); git(t, "mv", "old_dirty.md", "renamed.md");                      cases.append(("① 純改名（內容0變動）", probe(t, b), (1, 1)))
    t, b = mk(); (t/"old_dirty.md").write_text(DIRTY+"x\n", encoding="utf-8"); commit(t,"e"); cases.append(("② 內容編輯", probe(t, b), (1, 1)))
    t, b = mk(); (t/"new_dirty.md").write_text(DIRTY, encoding="utf-8"); commit(t,"a");       cases.append(("③ 新增追蹤檔", probe(t, b), (1, 1)))
    t, b = mk(); (t/"untracked.md").write_text(DIRTY, encoding="utf-8");          cases.append(("④ 未追蹤新檔", probe(t, b), (1, 1)))
    t, b = mk(); git(t, "rm", "-q", "old_dirty.md");                              cases.append(("⑤ 刪除髒檔", probe(t, b), (0, 0)))
    t, b = mk(); shutil.copy(t/"old_dirty.md", t/"copy.md"); commit(t,"c");       cases.append(("⑥ 複製到新路徑", probe(t, b), (1, 1)))
    t, b = mk(); os.chmod(t/"old_dirty.md", 0o755); commit(t,"m");                cases.append(("⑦ 真chmod755（內容0變動）", probe(t, b), (1, 1)))
    t, b = mk(); (t/"ig").mkdir(); (t/".gitignore").write_text("ig/\n", encoding="utf-8")
    shutil.move(str(t/"old_dirty.md"), str(t/"ig"/"x.md")); commit(t, "ig");      cases.append(("⑧ 搬進.gitignore目錄", probe(t, b), (1, 0)))
    t, b = mk(); git(t,"mv","old_dirty.md","x.md"); commit(t,"m1")
    git(t,"mv","x.md","old_dirty.md"); commit(t,"m2");                            cases.append(("⑫ 改名再改回（淨變動0）", probe(t, b), (0, 0)))
    t, b = mk(); git(t, "mv", "clean.md", "renamed_clean.md");                    cases.append(("⑪ 乾淨檔改名（對照）", probe(t, b), (1, 0)))
    t, b = mk(); git(t,"mv","old_dirty.md","a.md"); commit(t,"mv")
    for i in range(3): (t/f"n{i}.md").write_text(CLEAN, encoding="utf-8"); commit(t, f"c{i}")
    cases.append(("⑮ 改名後3個不相關commit（單調性）", probe(t, b), (4, 1)))
    t, b = mk(); git(t, "rm", "-q", "old_dirty.md"); commit(t, "del")
    (t/"old_dirty.md").write_text(DIRTY, encoding="utf-8"); commit(t, "re");      cases.append(("⑯ 刪後同路徑同內容加回", probe(t, b), (0, 0)))
    t, b = mk(); os.symlink("old_dirty.md", t/"link.md"); commit(t, "ln");        cases.append(("⑰ symlink指向髒檔", probe(t, b), (1, 1)))

    for label, got, want in cases:
        check(f"{label} (語料, unapproved)", got, want)


# ===================================================================== R2
def r2(P):
    print("== R2 語料拆解 + W2B 分支（選配）==")
    pc, root = P["pcB"], P["B"]
    r = scan(pc, root, corpus(pc, root))
    per = {}
    for h in r["unapproved"]:
        per[h.path] = per.get(h.path, 0) + 1
    check("fc8b966 unapproved 逐檔", per, {"archive/wave-specs/w2a.md": 3})
    stale = sorted((e["path"], e["token"], e["actual"], e["occurrences"]) for e in r["stale_entries"])
    check("fc8b966 stale 逐筆（宣告1 實得0）", stale,
          [("docs/research/drafts/prose-number-inventory.json", "最後核實", 0, 1),
           ("docs/research/drafts/prose-number-inventory.json", "短版", 0, 1)])

    w = P.get("W")
    if not w:
        print("  [SKIP] W2B 的兩個量測 SHA 都取不到（多半已 squash merge 或分支被刪）"
              " ⇒ 本節不可重跑（見報告 §4 第 1 項）")
        return
    tip = ""
    for ref in (f"refs/remotes/origin/{W2B_REF}", f"refs/heads/{W2B_REF}"):
        out = subprocess.run(["git", "rev-parse", "--verify", "-q", ref], cwd=str(w),
                             capture_output=True, text=True)
        if out.returncode == 0:
            tip = out.stdout.strip(); break
    note("W2B 分支現行尖端（僅供診斷，⛔ 不用來量）", tip[:7] if tip else "(分支已不存在)")

    for sha, e_corpus, e_unapp, e_arch, e_c2 in W2B_SHAS:
        if subprocess.run(["git", "cat-file", "-e", sha + "^{commit}"], cwd=str(w),
                          capture_output=True).returncode != 0:
            print(f"  [SKIP] W2B {sha[:7]} 已不可達 ⇒ 該量測點不可重跑")
            continue
        git(w, "checkout", "-q", sha)
        pcw = load_pc(w)
        rels_w = corpus(pcw, w)
        rw = scan(pcw, w, rels_w)
        perw = {}
        for h in rw["unapproved"]:
            perw[h.path] = perw.get(h.path, 0) + 1
        arch = sum(v for k, v in perw.items() if k.startswith("archive/"))
        check(f"W2B {sha[:7]} 語料", len(rels_w), e_corpus)
        check(f"W2B {sha[:7]} unapproved 總數", rw["unapproved_count"], e_unapp)
        check(f"W2B {sha[:7]} 其中 archive/ 佔幾筆", arch, e_arch)
        check(f"W2B {sha[:7]} 候選2 只降到 {e_c2}（rc 仍 1）",
              triple(pcw, w, corpus(pcw, w, True))[1], e_c2)
        note(f"W2B {sha[:7]} 逐檔", dict(sorted(perw.items(), key=lambda x: -x[1])))
        # ⭐ 合併順序敏感性：候選1（+3、-2 死條目）在此樹仍紅
        E = json.loads((Path(w)/"scripts"/"pollution-allowlist.json").read_text(encoding="utf-8"))["entries"]
        hits, _ = pcw.scan_paths(Path(w), ["archive/wave-specs/w2a.md"])
        new = {}
        for h in hits:
            k = (h.path, h.token, h.line_sha1)
            new.setdefault(k, {"path": h.path, "token": h.token, "line_sha1": h.line_sha1,
                               "excerpt": h.line.strip()[:110], "occurrences": 0,
                               "rationale": "已封存的歷史規格，逐字保存⛔ 非新規則文脈（候選1 模擬條目）"})
            new[k]["occurrences"] += 1
        C1 = [e for e in E + list(new.values()) if e["line_sha1"] != DEAD_SHA1]
        tf = Path(tempfile.mkdtemp(prefix="wf231-w2b-")) / "c1.json"
        tf.write_text(json.dumps({"_meta": {}, "entries": C1}, ensure_ascii=False), encoding="utf-8")
        rc1 = scan(pcw, w, rels_w, tf)
        check(f"W2B {sha[:7]} 候選1(+3,-2) 仍紅（AC1「main rc=0」對合併順序敏感）",
              (len(C1), rc1["unapproved_count"], len(rc1["stale_entries"]),
               1 if rc1["unapproved_count"] else 0), (43, e_c2, 0, 1))
        check(f"W2B {sha[:7]} 候選1 的 3 筆 key 在此樹仍精確命中（archive/ 歸零）",
              [h.path for h in rc1["unapproved"] if h.path.startswith("archive/")], [])
        check(f"W2B {sha[:7]} 待刪死條目 index 仍為 40/41",
              [i for i, e in enumerate(E) if e["line_sha1"] == DEAD_SHA1], [40, 41])


# ===================================================================== R3
def r3(P):
    print("== R3 archive/ 是不是唯讀 ==")
    pc, root = P["pcB"], P["B"]
    live = {}
    for f in git(root, "ls-files", "archive/").split():
        n = len(git(root, "log", "--oneline", "--", f).splitlines())
        if n > 1:
            live[f] = n
    check("archive/ 下 commit 數 >1 的檔（⇒ 非唯讀）", live,
          {"archive/TASKS_ARCHIVE.md": 15, "archive/tasks/WF-12.md": 2, "archive/tasks/WF-17.md": 2})
    arch = git(root, "ls-files", "archive/").split()
    hits, _ = pc.scan_paths(Path(root), arch)
    per = {}
    for h in hits:
        per[h.path] = per.get(h.path, 0) + 1
    check("archive/ 追蹤檔數", len(arch), 27)
    check("archive/ 總命中", len(hits), 22)
    check("archive/ 涉及檔數", len(per), 14)
    # 時序意外：w0/w1 封存早於 BASE_SHA 才逃掉，⛔ 非 w2a 的性質
    ct = {c: int(git(root, "log", "-1", "--format=%ct", c)) for c in
          ("38c3afe", "46fe93d", SHA_BASE, SHA_B)}
    check("w0 封存(38c3afe) 早於 BASE_SHA", ct["38c3afe"] < ct[SHA_BASE], True)
    check("w1 封存(46fe93d) 早於 BASE_SHA", ct["46fe93d"] < ct[SHA_BASE], True)
    check("w2a 封存(fc8b966) 晚於 BASE_SHA", ct[SHA_B] > ct[SHA_BASE], True)
    h1, _ = pc.scan_paths(Path(root), ["archive/wave-specs/w1.md"])
    check("w1.md 也帶 1 筆污染符（只是逃掉了）", len(h1), 1)
    # 姊妹掃描器沒有 archive/ 排除，且在 archive/ 0 命中
    check("canonical_citation_scan.EXCLUSIONS 是空的（AC2 的樣板從未載真實條目）",
          len(load_module(root, "canonical_citation_scan").EXCLUSIONS), 0)


def load_module(root, name):
    spec = importlib.util.spec_from_file_location(name, Path(root) / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# ===================================================================== R4
def r4(P):
    print("== R4 manifest 腐爛速率 + P1-38 實據 ==")
    root = P["B"]
    born = int(git(root, "log", "-1", "--format=%ct", SHA_A))
    died = int(git(root, "log", "-1", "--format=%ct", SHA_B))
    check("manifest 建立→首個死條目（秒）", died - born, 1911)
    check("跨幾個 commit", len(git(root, "rev-list", f"{SHA_A}..{SHA_B}").splitlines()), 1)
    check("manifest 只被一個 commit 建立過",
          git(root, "log", "--format=%h", "--", "scripts/pollution-allowlist.json").split(), ["950b3e2"])
    # P1-38：repo 內直接記載
    hit = subprocess.run(["grep", "-rn", "P1-38", "."], cwd=str(root),
                         capture_output=True, text=True).stdout.splitlines()
    files = sorted({l.split(":")[0] for l in hit})
    note("P1-38 出現在（⛔ 無一處記載「白名單自我擴張」或「九輪」）", files)
    check("repo 內對「白名單自我擴張」的命中數",
          len(subprocess.run(["grep", "-rn", "白名單自我擴張", "."], cwd=str(root),
                             capture_output=True, text=True).stdout.splitlines()), 0)


# ===================================================================== R5
def r5(P):
    print("== R5 對抗性：洩漏探針（合成構造）+ 時間外 ==")
    pc = P["pcB"]
    t = copy_tree(P["B"])
    (t / "docs" / "LIVE_RULE.md").write_text(
        "新規則文字：本流程改用 needs-deploy 旗標。\n", encoding="utf-8")
    commit(t, "add live dirty rule")
    before = triple(pc, t, corpus(pc, t, drop_archive=True))
    check("洩漏探針[搬之前] 候選2 (語料,unapproved,stale)", before, (17, 1, 2))
    git(t, "mv", "docs/LIVE_RULE.md", "archive/LIVE_RULE.md")
    commit(t, "move into archive")
    after_c2 = triple(pc, t, corpus(pc, t, drop_archive=True))
    after_now = triple(pc, t, corpus(pc, t, drop_archive=False))
    check("洩漏探針[搬之後] 候選2 → 靜音（unapproved 歸 0）", after_c2, (16, 0, 2))
    check("洩漏探針[搬之後] 現行設計 → 仍響", after_now, (18, 4, 2))
    print("  -- 時間外 --")
    for lab, root, pcx, w_now, w_c2 in (
            ("950b3e2", P["A"], P["pcA"], (16, 0, 0), (16, 0, 0)),
            ("fc8b966", P["B"], P["pcB"], (17, 3, 2), (16, 0, 2))):
        check(f"{lab} 現行", triple(pcx, root, corpus(pcx, root)), w_now)
        check(f"{lab} 候選2", triple(pcx, root, corpus(pcx, root, True)), w_c2)


# ===================================================================== R6
def r6(P):
    print("== R6 候選1 前推成本 + AC1 組合 + stale進rc 誤紅測 + E1 死條目復活 ==")
    pc, root = P["pcB"], P["B"]
    drafts = sorted(git(root, "ls-files", "docs/research/drafts/").split())
    per, tot = {}, 0
    for p in drafts:
        h, _ = pc.scan_paths(Path(root), [p])
        per[p] = len(h); tot += len(h)
    check("待封存母體檔數（窮舉）", len(drafts), 6)
    check("前推總命中", tot, 13)
    note("逐檔", per)

    E = json.loads((Path(root)/"scripts"/"pollution-allowlist.json").read_text(encoding="utf-8"))["entries"]
    check("現行條目數", len(E), 42)
    check("條目數軌跡 現行→今日(+3)→刪死條目(-2)→計畫走完(+13)",
          (len(E), len(E)+3, len(E)+3-2, len(E)+3-2+tot), (42, 45, 43, 56))

    print("  -- AC1 四組合 × rc 兩制 --")
    rels, noar = corpus(pc, root), corpus(pc, root, True)
    tmp = Path(tempfile.mkdtemp(prefix="wf231-r6-"))
    hits, _ = pc.scan_paths(Path(root), ["archive/wave-specs/w2a.md"])
    new = {}
    for h in hits:
        k = (h.path, h.token, h.line_sha1)
        new.setdefault(k, {"path": h.path, "token": h.token, "line_sha1": h.line_sha1,
                           "excerpt": h.line.strip()[:110], "occurrences": 0,
                           "rationale": "已封存的歷史規格，逐字保存⛔ 非新規則文脈（候選1 模擬條目）"})
        new[k]["occurrences"] += 1
    check("候選1 需新增的條目數", len(new), 3)
    note("候選1 三筆 key", sorted((e["token"], e["line_sha1"]) for e in new.values()))
    C1 = E + list(new.values())
    nodead = lambda es: [e for e in es if e["line_sha1"] != DEAD_SHA1]

    def go(rels_, entries, label, want):
        p = tmp / f"{abs(hash(label))}.json"
        p.write_text(json.dumps({"_meta": {}, "entries": entries}, ensure_ascii=False), encoding="utf-8")
        r = scan(pc, root, rels_, p)
        u, s = r["unapproved_count"], len(r["stale_entries"])
        got = (len(entries), u, s, 1 if u else 0, 1 if (u or s) else 0)
        check(f"{label} (條目,unapproved,stale,rc現行,rc含stale)", got, want)

    go(rels, E,            "現況",                (42, 3, 2, 1, 1))
    go(rels, C1,           "候選1",               (45, 0, 2, 0, 1))
    go(rels, nodead(C1),   "候選1＋刪2筆死條目 ⭐",   (43, 0, 0, 0, 0))
    go(noar, E,            "候選2",               (42, 0, 2, 0, 1))
    go(noar, nodead(E),    "候選2＋刪2筆死條目",     (40, 0, 0, 0, 0))

    print("  -- stale 進 rc 是否製造誤紅（改名假想）--")
    c = copy_tree(root)
    (c / "AI_WORKFLOW.md").rename(c / "CANONICAL.md")
    r2_ = [x if x != "AI_WORKFLOW.md" else "CANONICAL.md" for x in rels]
    rr = scan(pc, c, r2_, Path(root)/"scripts"/"pollution-allowlist.json")
    u, s = rr["unapproved_count"], len(rr["stale_entries"])
    check("改名後 (unapproved, stale)", (u, s), (44, 40))
    check("兩制同紅 ⇒ stale 進 rc ⛔ 不新增誤紅",
          (1 if u else 0, 1 if (u or s) else 0), (1, 1))

    print("  -- 候選3 BASE_SHA 前移（已證偽）--")
    for base, lab, want in ((SHA_A, "BASE=950b3e2", (2, 3, 40)),
                            (SHA_B, "BASE=fc8b966（自身）", (0, 0, 42))):
        rl = corpus(pc, root, base=base)
        check(f"候選3 {lab} (語料,unapproved,stale)", triple(pc, root, rl), want)
    rl = corpus(pc, root, base=SHA_B)
    rz = scan(pc, root, rl)
    check("候選3 BASE=自身 → total_hits", rz["total_hits"], 0)
    check("候選3 BASE=自身 → rc 竟為 0（瞎守衛回綠）", 1 if rz["unapproved_count"] else 0, 0)

    print("  -- E1 死條目靜默復活 --")
    d = copy_tree(root)
    tgt = d / "docs/research/drafts/prose-number-inventory.json"
    tgt.write_text(tgt.read_text(encoding="utf-8") + DEAD_LINE + "\n", encoding="utf-8")
    import hashlib
    check("E1 復活行 sha1 與死條目錨點相符",
          hashlib.sha1(DEAD_LINE.strip().encode("utf-8")).hexdigest(), DEAD_SHA1)
    rE = scan(pc, d, rels)
    resurrected = [h for h in rE["unapproved"] if h.line_sha1 == DEAD_SHA1]
    check("E1 復活後 (unapproved, stale)", (rE["unapproved_count"], len(rE["stale_entries"])), (3, 0))
    check("E1 該行的 2 筆命中被自動核可（⛔ 無人複審）", len(resurrected), 0)
    check("E1 五個輸出通道都不提示這是復活死條目",
          bool(rE["invalid_entries"]) or bool(rE["stale_entries"]) or bool(rE["unreadable"]), False)


# ===================================================================== R7
def r7(P):
    """W2B 合併後的 main：AC1「main 上 rc=0」是否仍可達。"""
    print("== R7 W2B 合併後的 main（13cc5f0）：AC1 可達性 ==")
    m = P.get("M")
    if not m:
        print(f"  [SKIP] 取不到 MAIN_SHA={SHA_M} ⇒ 本輪不可重跑")
        return
    pcm = load_pc(m)
    rels = corpus(pcm, m)
    r = scan(pcm, m, rels)
    per = {}
    for h in r["unapproved"]:
        per[h.path] = per.get(h.path, 0) + 1
    arch = sum(v for k, v in per.items() if k.startswith("archive/"))
    check("新 main (語料, unapproved, stale)", triple(pcm, m, rels), (33, 32, 2))
    check("新 main total_hits", r["total_hits"], 218)
    check("新 main 其中 archive/ / 非 archive/", (arch, r["unapproved_count"] - arch), (3, 29))
    note("新 main 逐檔", dict(sorted(per.items(), key=lambda x: -x[1])))
    check("新 main 是 merge commit（⛔ 非 squash）⇒ 兩個 W2B 量測點仍可達",
          [sha[:7] for sha, *_ in W2B_SHAS
           if subprocess.run(["git", "cat-file", "-e", sha + "^{commit}"], cwd=str(m),
                             capture_output=True).returncode == 0],
          ["2c35d48", "5331fc4"])
    E = json.loads((Path(m)/"scripts"/"pollution-allowlist.json").read_text(encoding="utf-8"))["entries"]
    hits, _ = pcm.scan_paths(Path(m), ["archive/wave-specs/w2a.md"])
    new = {}
    for h in hits:
        k = (h.path, h.token, h.line_sha1)
        new.setdefault(k, {"path": h.path, "token": h.token, "line_sha1": h.line_sha1,
                           "excerpt": h.line.strip()[:110], "occurrences": 0,
                           "rationale": "已封存的歷史規格，逐字保存⛔ 非新規則文脈（候選1 模擬條目）"})
        new[k]["occurrences"] += 1
    C1 = [e for e in E + list(new.values()) if e["line_sha1"] != DEAD_SHA1]
    tf = Path(tempfile.mkdtemp(prefix="wf231-r7-")) / "c1.json"
    tf.write_text(json.dumps({"_meta": {}, "entries": C1}, ensure_ascii=False), encoding="utf-8")
    rc1 = scan(pcm, m, rels, tf)
    check("⭐ 候選1(+3,-2) 在新 main (條目,unapproved,stale,rc)",
          (len(C1), rc1["unapproved_count"], len(rc1["stale_entries"]),
           1 if rc1["unapproved_count"] else 0), (43, 29, 0, 1))
    check("⇒ AC1「main 上 rc=0 且兩項計數皆 0」在 #231 射程內可達？",
          rc1["unapproved_count"] == 0 and not rc1["stale_entries"], False)
    check("交付的 3 筆 key 在新 main 仍精確（archive/ 歸零）",
          [h.path for h in rc1["unapproved"] if h.path.startswith("archive/")], [])
    check("交付的待刪死條目 index 在新 main 仍為 40/41",
          [i for i, e in enumerate(E) if e["line_sha1"] == DEAD_SHA1], [40, 41])
    check("新 main 的 allowlist 條目數未變", len(E), 42)
    # 候選2 在新 main 一樣救不了
    check("候選2 在新 main 也只降到 29", triple(pcm, m, corpus(pcm, m, True))[1], 29)


ROUNDS = {"nc": nc, "r0": r0, "r1": r1, "r2": r2, "r3": r3,
          "r4": r4, "r5": r5, "r6": r6, "r7": r7}


def main() -> int:
    ap = argparse.ArgumentParser(description="WF-POLLUTION-MANIFEST-STALE1 研究階段 harness")
    ap.add_argument("--src", required=True, help="ai-workflow 的 repo 路徑或 clone URL（唯讀）")
    ap.add_argument("--work", default=None, help="工作目錄（預設 tempdir）")
    ap.add_argument("--rounds", default="all", help="nc,r0,r1,r2,r3,r4,r5,r6,r7 或 all")
    args = ap.parse_args()

    work = Path(args.work) if args.work else Path(tempfile.mkdtemp(prefix="wf231-work-"))
    work.mkdir(parents=True, exist_ok=True)
    print(f"work={work}\nsrc={args.src}\n")

    A, B = work / "probeA", work / "probeB"
    try:
        if not (A / ".git").exists():
            subprocess.run(["git", "clone", "-q", args.src, str(A)], check=True)
        if not (B / ".git").exists():
            shutil.copytree(A, B, symlinks=True)
        git(A, "checkout", "-q", SHA_A)
        git(B, "checkout", "-q", SHA_B)
    except Exception as exc:
        print(f"[環境錯誤] 取不到受測 SHA：{exc}", file=sys.stderr)
        return 2
    P = {"A": A, "B": B, "pcA": load_pc(A), "pcB": load_pc(B)}

    M = work / "probeM"
    try:
        if not (M / ".git").exists():
            shutil.copytree(A, M, symlinks=True)
        git(M, "checkout", "-q", SHA_M)
        P["M"] = M
    except Exception:
        P["M"] = None

    W = work / "probeW"
    try:
        if not (W / ".git").exists():
            shutil.copytree(A, W, symlinks=True)
        reachable = [sha for sha, *_ in W2B_SHAS
                     if subprocess.run(["git", "cat-file", "-e", sha + "^{commit}"],
                                       cwd=str(W), capture_output=True).returncode == 0]
        P["W"] = W if reachable else None
    except Exception:
        P["W"] = None

    print(f"probeA HEAD={git(A,'rev-parse','HEAD')}")
    print(f"probeB HEAD={git(B,'rev-parse','HEAD')}")
    print("probeW = " + (f"可達 {len([1 for sha,*_ in W2B_SHAS if subprocess.run(['git','cat-file','-e',sha+'^{commit}'],cwd=str(W),capture_output=True).returncode==0])}/{len(W2B_SHAS)} 個 W2B 量測點"
                        if P["W"] else "W2B 量測點皆不可達（R2 後半 SKIP）"))
    print(f"probeM = {'HEAD='+git(M,'rev-parse','HEAD') if P['M'] else '取不到 MAIN_SHA（R7 SKIP）'}")
    print(f"BASE_SHA（自受測樹 import，⛔ 未重打）={P['pcB'].BASE_SHA}\n")

    want = list(ROUNDS) if args.rounds == "all" else [x.strip() for x in args.rounds.split(",")]
    for name in want:
        if name not in ROUNDS:
            print(f"[環境錯誤] 未知輪次 {name}", file=sys.stderr); return 2
        ROUNDS[name](P); print()

    npass = sum(1 for ok, _ in _RESULTS if ok)
    nfail = len(_RESULTS) - npass
    print(f"==== 總計 {npass} PASS / {nfail} FAIL ====")
    for ok, lab in _RESULTS:
        if not ok:
            print(f"  FAIL: {lab}")
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main())
```


## Comment 5497467883 · 2026-09-01T16:58:40Z

## 需求方裁定 — AC1 的處置方向 ＋ 一項補測要求（2026-09-02）

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`；⚠️ **發文者身分不等於決策者身分**。需求方於本機 Claude Code 對話中先給出原則「**舊卡應該做的是補內容修改到符合目前規範**」與「**不要為了舊卡通過而訂違反規劃的修正**」，於 PM 完成下述量測後逐字裁示「**照這樣走，交回 #231 補測**」。transcript 於需求方本機可核。

---

### 一 · 裁定：照 **AC1 原文**做。⛔ 不改 AC、⛔ 不開 FIX 卡、⛔ 不改那 29 筆內容。

**AC1 逐字不動**：「main 上 `python3 scripts/pollution_check.py` 回到 `rc=0`，且 `unapproved_count` 與 stale-entry 行數皆為 0；同時附負控：對一個刻意植入污染符的探針檔，同一支工具仍會響」。

**可達性已實測**（PM 於 main `13cc5f0551759934f8a9a7295de219b4c4164b3e` 上跑）：加 **31** 筆核可條目＋刪 2 筆死條目 ⇒ `unapproved=0`、`stale=0`、**rc=0**，條目 42→71。

⇒ ⛔ **執行者交還報告 §0 的「AC1 在 #231 射程內不可達」不成立**：那 5 個檔確實在寫入集外，**但補救手段（`pollution-allowlist.json`）在寫入集內**。PM 先前接受該宣稱，一併更正於下。

### 二 · 為什麼⛔ 不改 AC、⛔ 不開 FIX 卡（合規面逐條）

| 若走「改 AC1 ＋ 開 FIX 卡」會撞到 | 逐字 |
|---|---|
| `stage-rules/planning.md` §1 | 「**規格只能在這裡改**；每次改必 bump `spec_version`」——本卡階段計畫為 `需求→研究→執行→審核→結案`，**⛔ 無規劃階段** |
| canonical `AI_WORKFLOW.md:672` | 「只有**碼已進 main 的事後查核**才開 `<原卡>-FIX<n>`」——那 29 筆是 **merge 前即知**（PM 當時 defer），⛔ 非事後查核 |
| `stage-rules/requirement.md` `F-需求-01` | 「卡一律由清單項升級」——全 repo 只有 canonical `:672` 與 `templates/worktree-lifecycle.md:8` 兩處提 FIX，**⛔ 無開卡例外** |

⇒ 三處都要為了讓一張舊卡通過而放寬，正是需求方原則所禁。**B（照原文做）⛔ 不違反任何一條。**

### 三 · 為什麼那 29 筆⛔ 不該改寫內容（這是需求方原則的正確套用結果）

需求方原則是「補內容修改到符合目前規範」。PM 逐筆讀完那 29 筆後量到：**它們引用的是「現行」語彙，⛔ 不是過期語彙**。

- canonical `:72` 逐字「**本節定義目標狀態，尚未切換；cutover＝切換 Initiative**」；`:97` 另有一節「**切換前的現行看板語彙與仍有效的約束**」。
- Project #4 實查交付狀態**實際在用**的值：`⏸阻塞`／`🏁完成`／`💡需求`／`📥Backlog`／`📦已合併`／`🔬研究中`／`🛑已停止`。
- `templates/control-plane-contract.md` **存在** ⇒ `control-plane` 是活概念。

⇒ **把它們改寫成 8×10 反而違反目前規範**（會描述一個尚未存在的看板）。污染符 token 的定義逐字是「決議 §二（**新規則文脈**）」，而腳本 docstring 逐字：「`（新規則文脈）` 那類限定詞是**人的判斷**，機器只能給你命中，**由 manifest 的 `rationale` 承接判斷**」。⇒ **核可條目就是這個工具設計上放人類判斷的位置**，⛔ 不是收容所。

⚠️ **每筆 rationale 必須是內容判斷**（「此處為切換前現行語彙的引用／對帳資料／測試 fixture，⛔ 非新規則文脈」），⛔ 不得以泛用理由充數。

### 四 · ⭐ 補測要求（動手前必做，本輪的唯一新增工作）

PM 量到一個會使上述方向產生**週期性干擾**的事實：

`docs/CONTRACT_TOOL_RECONCILE.md` 有四個機器產生區塊——`w2b-historical` 233–245、`reconcile-dispositions` 411–458、`reconcile-generated` 464–541、`w2b-setdiff` 579–662。該檔 22 筆命中的行號逐一對照：

- **產生區塊外（手寫散文）11 筆**：127／152／154／165／167／180／186／192／194／392（同行 2 個 occurrence）
- ⛔ **產生區塊內 11 筆**：418／421（dispositions）、486／508／511／521／522（generated）、637／646／648／652（setdiff）

⇒ **31 筆核可裡有 11 筆錨在機器產生的行上**（條目綁 `line_sha1`）。那些行每次重生產生器就被改寫 ⇒ 條目 stale ⇒ **加上已裁定的 AC3（`stale_entries` 進 rc），每次重生對帳文件都會讓守衛轉紅**。重生是該工具的日常動作（W2B iteration 2 就重生過一次）。

⭐ **這是 AC3 的未測情境**：執行者測「stale 進 rc ⛔ 不新增誤紅」用的是**改名**（`AI_WORKFLOW.md` → `CANONICAL.md`，兩制同紅）。**重生產生區塊沒測過。**

**⇒ 執行者在動任何 allowlist 之前，補一項量測**：

1. 在受測樹上**重生那四個區塊**（用 repo 內既有的產生路徑，⛔ 不自造）。
2. 量：重生後那 11 筆是否 `stale`？兩制 rc（現行／含 stale）各是多少？
3. 若確認會轉紅 ⇒ 逐字寫出**那 11 筆的處置選項與各自的可證偽條件**，⛔ 不自行決定。已知的兩難逐字記在此：**那 11 筆的內容是被對帳的符號本身**（`delivery_status/📥Backlog` 這類），**既不能改寫**（改了對帳器抽不到）、**又不能穩定核可**（行會重生）。
4. ⚠️ 若你認為需要第三種分類（像 `SELF_REFERENCE_PATHS` 那樣的 path／區塊級分類）：**那是值域擴張，須需求方裁定**。`SELF_REFERENCE_PATHS` 的就地註解逐字寫「**⛔ 不是『我不想修它』的收容所；⛔ 恰好三項**」，成員判準是 canonical §6.2 的「本 checker 自己」⇒ 對帳文件⛔ 不符合。**⛔ 不得自行擴張，上呈即可。**

**本輪射程仍是研究階段**：⛔ 無寫入授權、⛔ 不動任何受管檔、⛔ 不跑 `wfcli` 寫入子指令。補測結果交還 PM。

### 五 · PM 失誤登記（歸屬錯誤，逐字更正）

PM 於下列三處把 32 筆整包標成「#231 的射程」：`#220` 的 ④ 完整性（`issuecomment-5496842413`）、`#220` 的 release 留痕（`issuecomment-5496975935`）、`#231` 的派工留痕（`issuecomment-5495655101`）。

**正確歸屬**：
- **3 筆**（`archive/wave-specs/w2a.md`）＝ PM 的封存 commit 造成，查核者 R1-7 判 `attribution=coordinator`。
- **29 筆**＝ **W2B 自己的 post-image**（PM 以逐 PR merge-base 實測：`--base fc8b966` 仍得 29 筆）。⇒ 掃描器一直正確，是流程在 merge 前把它 defer 了。
- ⚠️ **查核者 R1-7 從未說那 29 筆歸 #231**——其 disposition 逐字為「需求方須另裁歸屬與修法」。**那句「歸 #231」是 PM 說的。**

⇒ 依本裁定，兩者**都**由 #231 依 AC1 原文以 allowlist 處置（因為手段在其寫入集內），⛔ 但歸因不因此改變：3 筆是 PM 造成、29 筆是 W2B 的內容。

### 六 · PM 未驗

1. 補測本身（重生後的 stale 行為）——PM ⛔ 未跑，那正是交回的工作。
2. 那 31 筆各自的 rationale 內容判斷——PM 只逐筆讀了行內容做分類，⛔ 未逐筆寫理由。
3. 執行者六輪量測 PM 已以其 harness 獨立重現（`88 PASS / 0 FAIL`），但**未逐輪複核其斷言的正確性**。


## Comment 5497682648 · 2026-09-01T17:16:53Z

## PM 獨立重現 R8 ＋ 收回「週期性紅燈」的顧慮

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`。R8 由執行者 session `8aa0801f-1a4d-484d-92f7-dc1dd8c9a363@Claude Code（claude-opus-5）` 撰寫，經需求方轉交。

### ⛔ PM 的顧慮被實測推翻，逐字收回

PM 於裁定 `issuecomment-5497467883` §四 逐字寫：「**加上已裁定的 AC3（`stale_entries` 進 rc），每次重生對帳文件都會讓守衛轉紅**」。

**PM 把 R8 接進自己那份轉錄 harness 後獨立實跑，得 `17 PASS / 0 FAIL`、rc=0**，逐項結果與執行者相符：

| 擾動 | unapproved | stale | rc現行 | rc含stale | 錨定變 stale |
|---|---|---|---|---|---|
| P-A 同 SHA 重生 | 0 | 0 | 0 | 0 | 0 |
| P-B 改 canonical 節標題後重生 | 4 | 4 | 1 | 1 | 4（508／511／521／522） |
| P-C 只新增內容後重生 | 0 | 0 | 0 | 0 | 0 |
| P-D 移除 `⏳待執行` 後重生 | 3 | 7 | 1 | 1 | 1（508） |
| P-E 只改語料外 `cli/src/` 後重生 | 0 | 0 | 0 | 0 | 0 |
| P-F 移除 `🔍待查核` 後重生 | 2 | 6 | 1 | 1 | 1（522） |

⭐ **P-A 實測：同 SHA 重生後文件逐位元不變** ⇒ 「重生」這個動作本身⛔ 不會讓任何條目 stale。
⭐ **P-C 實測：產生區塊多出新列、行號整批位移，既有錨點 0 stale** ⇒ 錨是 `line_sha1`，⛔ 不是行號。**PM 誤以為它綁行號。**
⭐ **六種擾動中「stale 響而 unapproved 不響」的次數＝0** ⇒ **AC3 ⛔ 不新增任何一次紅燈**。凡錨定失效的情境（P-B／P-D／P-F），現行制已因 `unapproved ≥ 2` 而紅。

⇒ **PM 的「週期性干擾」不成立。** 該顧慮建立在「錨綁行號」與「重生會改寫行」兩個錯誤前提上，兩者都被實測否定。

### ⚠️ 但下述界線必須一併帶著（執行者已自行登記，PM 複核後同意）

1. **11 筆錨定中只有 5 筆真的被重生過**（`reconcile-generated`）。`reconcile-dispositions`（418／421）與 `w2b-setdiff`（637／646／648／652）在 repo 內**查無自動 writer** ⇒ 那 6 筆的重生行為**⛔ 未測**。
2. 「六次分歧＝0」是**構造不出**，⛔ 非「不存在」（`F-研究-07`）。擾動空間無界。
3. 執行者自行登記的一筆失誤值得記：**R8 首版兩支探針對同一擾動給出 `unapproved` 4 vs 32**，根因是合成條目的 `rationale` 只有 6 字元、被 `entry_errors` 判 **invalid 靜默丟棄**，而其量測未檢查 `invalid_entries`。⭐ **那正是本卡的主題發生在量測者自己身上**；已加長 rationale 並在每次量測加 `invalid_entries == 0` 斷言（PM 重現時該 7 條斷言全 PASS）。

### PM 複核執行者對 31 筆的複核（相符）

在 main `13cc5f0551759934f8a9a7295de219b4c4164b3e`：條目 **42 → 71**（＋31 −2 死條目）、`unapproved=0`、`stale=0`、`rc=0`；22 筆的 11／11 區塊拆分與 PM 先前給的行號逐筆相符。

### PM 未驗

1. 未重生的那 6 筆（dispositions 2 ／ setdiff 4）——PM 同樣未測，接受執行者「repo 內查無自動 writer」的登記，⛔ 未獨立驗證該 grep 的完整性。
2. 那 31 筆各自的真實 rationale 內容判斷——R8 用統一佔位文字，真實判斷是執行階段的工作。

### R8 全文（接在 `issuecomment-5497181885` 已貼版本之後）

```python

# ===================================================================== R8
RECON_DOC = "docs/CONTRACT_TOOL_RECONCILE.md"
GEN_BEG = "<!-- reconcile-generated:begin -->"
GEN_END = "<!-- reconcile-generated:end -->"

#: 31 筆補條目的 rationale（⚠️ ``entry_errors`` 要求 ≥10 字元；太短會被靜默判 invalid）
R8_RATIONALE = ("此處為切換前現行語彙的引用／對帳資料／測試 fixture，⛔ 非新規則文脈"
                "（R8 模擬條目；執行者須逐筆改為真實內容判斷）")

#: 11 個錨在機器產生區塊內的條目（line_sha1 前 12 位 → 行號＋區塊）
R8_ANCHORS = {
    "012d4b1baa6d": "418 dispositions", "032e16dfd490": "421 dispositions",
    "9afaebf00662": "486 generated", "33d5ef87e1a8": "508 generated",
    "35a6dfc1a278": "511 generated", "b0024e9b7be1": "521 generated",
    "2eaf6f6a9655": "522 generated", "bea96849926e": "637 setdiff",
    "1dfa9bd73f70": "646 setdiff", "854c38a698cc": "648 setdiff",
    "642e6516ab31": "652 setdiff",
}


def _r8_full_allowlist(pc, root):
    """PM 的 71 筆：現行 42 ＋ 全部 unapproved 逐筆補條目 − 2 筆死條目。"""
    rels = corpus(pc, root)
    E = json.loads((Path(root)/"scripts"/"pollution-allowlist.json").read_text(encoding="utf-8"))["entries"]
    r = scan(pc, root, rels)
    new = {}
    for h in r["unapproved"]:
        k = (h.path, h.token, h.line_sha1)
        new.setdefault(k, {"path": h.path, "token": h.token, "line_sha1": h.line_sha1,
                           "excerpt": h.line.strip()[:110], "occurrences": 0,
                           "rationale": R8_RATIONALE})
        new[k]["occurrences"] += 1
    full = [e for e in E + list(new.values()) if e["line_sha1"] != DEAD_SHA1]
    p = Path(tempfile.mkdtemp(prefix="wf231-r8al-")) / "full.json"
    p.write_text(json.dumps({"_meta": {}, "entries": full}, ensure_ascii=False), encoding="utf-8")
    return rels, full, p, len(new)


def _r8_regen(root):
    """⭐ 用 repo 內既有產生路徑重生 reconcile-generated 區塊，⛔ 不自造產生器。"""
    out = subprocess.run([sys.executable, "scripts/contract_tool_reconcile.py", "--format", "md"],
                         cwd=str(root), capture_output=True, text=True, check=True).stdout
    p = Path(root) / RECON_DOC
    t = p.read_text(encoding="utf-8")
    a = t.index(GEN_BEG) + len(GEN_BEG)
    b = t.index(GEN_END)
    p.write_text(t[:a] + "\n" + out.rstrip("\n") + "\n" + t[b:], encoding="utf-8")


def r8(P):
    """AC3 的未測情境：重生機器產生區塊，11 筆錨定條目會不會讓兩制判定分歧。"""
    print("== R8 重生產生區塊 × AC3（stale 進 rc）是否新增紅燈 ==")
    m = P.get("M")
    if not m:
        print(f"  [SKIP] 取不到 MAIN_SHA={SHA_M} ⇒ 本輪不可重跑")
        return
    pcm = load_pc(m)
    rels, full, AL, n_new = _r8_full_allowlist(pcm, m)
    check("補條目數（複核 PM 的 31 筆）", n_new, 31)
    check("條目數 42 → 71（＋31 −2 死條目）", len(full), 71)
    anchored = sorted(e["line_sha1"][:12] for e in full if e["line_sha1"][:12] in R8_ANCHORS)
    check("錨在機器產生區塊內的條目數", len(anchored), 11)
    note("11 筆錨定逐筆", sorted(R8_ANCHORS[a] for a in anchored))

    def meas(root, label, want):
        q = load_pc(root)
        res = q.run(Path(root), rels, AL)
        check(f"{label} invalid_entries 為 0（⛔ 條目未被靜默丟棄）", len(res["invalid_entries"]), 0)
        u, s = res["unapproved_count"], len(res["stale_entries"])
        ss = {e["line_sha1"][:12] for e in res["stale_entries"]}
        hit = sorted(R8_ANCHORS[k] for k in R8_ANCHORS if k in ss)
        got = (u, s, 1 if u else 0, 1 if (u or s) else 0, len(hit))
        check(f"{label} (unapproved,stale,rc現行,rc含stale,錨定變stale)", got, want)
        if hit:
            note(f"{label} 變 stale 的錨定", hit)
        return s > 0 and u == 0

    def probe(mutate=None):
        d = copy_tree(m)
        if mutate:
            mutate(d)
        _r8_regen(d)
        return d

    a = probe()
    check("P-A 同 SHA 重生後文件逐位元不變",
          (Path(a)/RECON_DOC).read_text(encoding="utf-8") == (Path(m)/RECON_DOC).read_text(encoding="utf-8"), True)
    div_a = meas(a, "P-A 同SHA重生", (0, 0, 0, 0, 0))

    def mut_b(d):
        p = Path(d)/"AI_WORKFLOW.md"
        lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
        for i, l in enumerate(lines):
            if l.lstrip().startswith("#") and "切換前的現行看板語彙與仍有效的約束" in l:
                lines[i] = l.rstrip("\n") + "（改名測試）\n"
        p.write_text("".join(lines), encoding="utf-8")
    div_b = meas(probe(mut_b), "P-B 改節標題後重生", (4, 4, 1, 1, 4))

    def mut_c(d):
        p = Path(d)/"AI_WORKFLOW.md"
        p.write_text(p.read_text(encoding="utf-8")
                     + "\n\n### 合成測試節\n\n新增一個合成事件型別 `synthetic-probe-event` 供 R8 使用。\n",
                     encoding="utf-8")
    div_c = meas(probe(mut_c), "P-C 只新增列後重生", (0, 0, 0, 0, 0))

    def mut_d(d):
        p = Path(d)/"AI_WORKFLOW.md"
        p.write_text(p.read_text(encoding="utf-8").replace("⏳待執行", "ZZ佔位"), encoding="utf-8")
    div_d = meas(probe(mut_d), "P-D 移除⏳待執行後重生", (3, 7, 1, 1, 1))

    def mut_e(d):
        p = Path(d)/"cli/src/wf_cli/commands/handoff_cmd.py"
        p.write_text(p.read_text(encoding="utf-8")
                     + "\n# R8 合成註解：不改行為，只讓掃描器看到不同的檔內容\n", encoding="utf-8")
    div_e = meas(probe(mut_e), "P-E 只改語料外cli/src後重生", (0, 0, 0, 0, 0))

    def mut_f(d):
        p = Path(d)/"AI_WORKFLOW.md"
        p.write_text(p.read_text(encoding="utf-8").replace("🔍待查核", "QQ佔位"), encoding="utf-8")
    div_f = meas(probe(mut_f), "P-F 移除🔍待查核後重生", (2, 6, 1, 1, 1))

    check("⭐ 六種擾動中出現「stale 響而 unapproved 不響」的次數（＝AC3 新增的紅燈）",
          sum([div_a, div_b, div_c, div_d, div_e, div_f]), 0)
```


## Comment 5497931407 · 2026-09-01T17:38:39Z

## 需求方裁定 — 研究階段收束：11 筆錨定＝甲、④ 歸屬＝§4 讀法、進執行階段（2026-09-02）

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`；⚠️ **發文者身分不等於決策者身分**。需求方於本機 Claude Code 對話中，於 PM 提出下述三項建議並完成規範／痛點檢驗後，逐字裁示「**好按你建議**」。transcript 於需求方本機可核。

### 裁定一 · 那 11 筆錨定 ⇒ **甲（什麼都不加，與其餘 60 筆同等對待）**

**規範面**：甲是三案中**唯一不需要規則變更**者。乙（區塊級分類）＝值域擴張——`SELF_REFERENCE_PATHS` 就地註解逐字「**⛔ 不是『我不想修它』的收容所；⛔ 恰好三項**」，成員判準是 canonical §6.2 的「本 checker 自己」⇒ 對帳文件不符合。丙（符號錨）＝改 manifest schema（`_ENTRY_KEYS` 是封閉集合）＋改 AC4，且其反例寫在該文件自己身上（`docs/CONTRACT_TOOL_RECONCILE.md:461` 逐字「符號改名一樣會爛」）。

**代價面**：R8 實測甲的代價接近零——`P-A` 同 SHA 重生後文件**逐位元不變**；`P-C` 產生區塊增列、行號整批位移仍 **0 stale**（錨是 `line_sha1` ⛔ 非行號）；`P-B`／`P-D`／`P-F` 錨定失效的情境下，現行制已因 `unapproved ≥ 2` 而紅。**六種擾動中「stale 響而 unapproved 不響」＝ 0。**

⚠️ 界線一併裁入：11 筆中**只有 5 筆真被重生過**（`reconcile-generated`），`reconcile-dispositions`（418／421）與 `w2b-setdiff`（637／646／648／652）**repo 內查無自動 writer、未測**；「0 分歧」是**構造不出**⛔ 非「不存在」。

### 裁定二 · `research.md` §3／§4 對 ④ 的歸屬衝突 ⇒ 本卡採 **§4 讀法**，且該衝突另行登記

**衝突逐字**：§3「④ **查核者**只驗量測可重跑」 vs §4 角色表「PM ｜ ④ **對量測完整性**」／「查核者 ｜ 驗量測可重跑（高階型＋三反測）」——**查核者那列沒有 ④ 標號**。

**本卡採 §4 讀法**，理由：④ 在其餘四份 stage-rules 一貫是 PM 的完整性檢查（`review.md`「④ PM 對裁決完整性」、`requirement.md`「④ R1 由需求方／人工；R2–R4 由 PM 或第二 PM」），`research.md` §3 是唯一例外寫法。⚠️ **本裁定⛔ 不宣稱 §3 是筆誤**——那要 owner 裁；本裁定只決定**本卡照哪個走**。

⇒ **④ 對量測完整性已完成**：PM 兩次獨立重現執行者的 harness（全輪 `88 PASS / 0 FAIL`；R8 `17 PASS / 0 FAIL`，皆 rc=0），並逐項核對其自陳界線。⇒ 研究階段可離開。

⚠️ **⛔ 未豁免任何步驟**：`stage-rules` 全掃 `豁免`／`免除`／`可跳過`／`得跳過` **零命中** ⇒ 豁免不是一個存在的動作。本裁定是**認定 ④ 已由 PM 履行**，⛔ 不是跳過它。

### 裁定三 · 進執行階段；worktree 已快進至現行 main

PM 已把本卡 worktree 由 `fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2` **快進至 `13cc5f0551759934f8a9a7295de219b4c4164b3e`**（落後 8 個 commit、0 個本地 commit、`--ff-only` 成功、工作區 0 行）。⇒ 執行者在**現行 main** 上動手，⛔ 不在舊樹。

新樹上實跑基線：`pollution_check` rc=1、`scanned_files 33`、`unapproved 32`、`approved_entries 42`。

### 執行階段的射程（AC1 逐字不動）

依 `issuecomment-5497467883` 的裁定：加 **31** 筆核可條目＋刪 **2** 筆死條目 ⇒ `unapproved=0`、`stale=0`、`rc=0`，條目 42→71。⚠️ **每筆 rationale 必須是內容判斷**（此處為切換前現行語彙的引用／對帳資料／測試 fixture，⛔ 非新規則文脈），⛔ 不得泛用理由充數——R8 用的統一佔位文字**⛔ 不得直接沿用**。

⭐ **痛點檢驗（誠實界定）**：AC1 本身**⛔ 不直接解痛點**。痛點逐字是「守衛紅了沒有人知道（不在 CI）、manifest 失效沒有東西會喊」——直接解方是 **AC2**（load-bearing 檢查）、**AC3**（stale 進 rc）、**AC5**（進 CI）。**AC1 的作用是 AC5 的必要前提**：main 不綠就不能把 `pollution_check` 掛進 CI（那會是永久紅的檢查，比沒有更糟）。

### PM 未驗

1. 未重生的那 6 筆（dispositions 2／setdiff 4）——PM 同樣未測，接受執行者「repo 內查無自動 writer」的登記，⛔ 未獨立驗證該 grep 的完整性。
2. 那 31 筆各自的真實 rationale 內容判斷——執行階段的工作。
3. `research.md` §3／§4 衝突的正解——本裁定只決定本卡走法，⛔ 未裁該衝突本身。


## Comment 5497979970 · 2026-09-01T17:42:44Z

## 需求方裁定 — **停止**（`🛑已停止`）：守衛未到時候（2026-09-02）

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`；⚠️ **發文者身分不等於決策者身分**。需求方於本機 Claude Code 對話中問「**我想確認這張卡真的有價值嗎？**」，於 PM 完成下述量測並提出兩個合規選項後，逐字裁示「**乙**」（＝停卡）。transcript 於需求方本機可核。

依 `stage-rules/closeout.md` §2 逐字：「停止（終態、⛔ 無出口；**裁定必含決策／原因／可證偽復活條件**；復活＝開新卡）」——三項逐段列於下。

### 決策

`WF-POLLUTION-MANIFEST-STALE1` 轉 **`🛑已停止`**。⛔ 不執行 AC1–AC5 任何一項。

### 原因（量測，⛔ 非判斷先行）

**這支守衛在切換前構造上幾乎只產生假陽性。**

| token 類別 | unapproved | approved |
|---|---|---|
| **已退役**（`claim 事件`／`claim event`／`events.jsonl`／`workflow_ledger`） | **0** | **1** |
| **現行**（`📥Backlog`／`🔍待查核`／`部署狀態`／`control-plane`／`⏳待執行`／`🚧進行中`／`短版`／`最後核實`／`行數自述`） | **32** | **41** |

⇒ **74 筆命中中有 73 筆打在「仍是現行語彙」的 token 上。** 那些 token 要等 **#222 切換 Initiative** 落地才真正退役。

旁證：
- `scripts/pollution_check.py` 與 `scripts/pollution-allowlist.json` 全史各 **1 個 commit**（2026-09-01 `950b3e2`，即 W2A）⇒ 該守衛存在**一天**。
- 42 筆既有核可條目的 rationale **全部**是「合法引用／對帳資料／owner 是別人」——**0 筆導致內容被修**。
- canonical `:72` 逐字「本節定義目標狀態，**尚未切換**；cutover＝切換 Initiative」；`:97` 另有一節「**切換前的現行看板語彙與仍有效的約束**」；Project #4 實查交付狀態在用的值仍為該組語彙。

⇒ **AC1（main 回綠）要為 31 筆構造上為假的命中寫內容判斷；AC5（進 CI）再把這個近 100% 假陽性的閘門向此後每個 PR 收稅。** W2B 已示範代價：它 29 筆、被 defer 掉一整輪。

⚠️ **⛔ 不是說守衛沒有價值**——是**時機錯了**。切換後那些 token 真的過期，它就會抓到真東西。

### 可證偽復活條件

**`#222` 切換 Initiative 的 cutover 落地，使 `POLLUTION_TOKENS` 中的現行語彙（`📥Backlog`／`🔍待查核`／`部署狀態`／`⏳待執行`／`🚧進行中`／`control-plane`）真正退役。**

⭐ **可機械判定**：屆時重跑本卡 harness 的 token 分類量測（本卡 `issuecomment-5497181885` 全文、`issuecomment-5497682648` 的 R8），若「已退役 token 的命中數」由 **0／1** 變為非零，本裁定即被推翻，**復活＝開新卡**（⛔ 非重開本卡）。

⚠️ **反面也要能判**：若 cutover 落地後該數字仍為 0，代表這批 token 從未真的滲進新規則文字 ⇒ **那時該裁的是移除守衛，⛔ 不是再修它**。

### 停卡留下的東西（誠實列，⛔ 不淡化）

1. main 的 `pollution_check` 維持 **rc=1**（`unapproved 32`、`stale-entry 2`）。
2. 那 2 筆死條目仍在，manifest 仍會**靜默腐爛**（`stale_entries` ⛔ 不進 rc）。
3. 守衛**仍不在 CI**（`.github/` 對 `pollution_check` grep 0 命中）⇒ 它紅了仍然沒有人知道。
4. ⚠️ **這三件在切換前都不造成傷害**（守衛紅了也只是誤報紅），但**切換那天必須先修好才能用**——復活條件即釘住此點。
5. `WF-REDESIGN-W2B`（#220）的驗證項「污染符 grep 零命中」維持未達成，其歸屬更正見 `#220` 的 `issuecomment-5497468178`。

### 本卡已產出且應保留的東西

- 執行者的可重跑 harness（`issuecomment-5497181885` 全文＋`issuecomment-5497682648` 的 R8），PM 已兩次獨立重現（`88 PASS / 0 FAIL`、`17 PASS / 0 FAIL`，皆 rc=0）。**復活時可直接重跑，⛔ 不必重做研究。**
- 候選 2（`archive/` 移出語料）**已被證偽**：R5 實測存在 `git mv` 洗白路徑（活路徑髒檔 `unapproved=1` → 搬進 `archive/` → `0`）。
- 候選 3（改 `BASE_SHA`）**已被證偽**：`BASE=自身` ⇒ 掃 0 檔、`total_hits=0`、**rc=0** 的瞎守衛回綠。
- R8：`stale_entries` 進 rc **⛔ 不新增任何一次紅燈**（六種擾動，分歧＝0；⚠️ 構造不出 ⛔ 非不存在）。
- `research.md` §3／§4 對 ④ 歸屬的衝突（§3 給查核者、§4 給 PM）——**本卡未裁該衝突**，PM 將另行登記。

### PM 未驗

1. 「73/74 打在現行 token」的分類由 PM 以「狀態面 2026-08-04 已遷移」判定四個已退役 token，⛔ 未逐一向 owner 確認該分類。
2. 復活條件的機械判定 PM **未預跑**（cutover 尚未發生）。

