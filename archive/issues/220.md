# #220 WF-REDESIGN-W2B 配套與 contract templates（四波五卡 W2B）
- state: closed  created: 2026-08-31T18:51:47Z  closed: 2026-09-01T16:13:38Z
- url: https://github.com/ruan6047/ai-workflow/issues/220
- comments: 22

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；改寫 contract templates＝public contract，形狀明確、判準逐檔 falsifier 可機械驗（P1-11 重推 T3））　查核：待指派（建議 主力型；T3 依規需獨立查核；獨立性要求疊加於層級之上（⛔ 非第四個層級），須實跑逐檔 falsifier 與對帳 set diff）
- Initiative：WF-REDESIGN1　spec 基線：ai-workflow 93bb8c086f0cf8870537390511b5f0aa2d037c97
- DB：db_scope=none
- 服務的原始目標：可稽核＋防低級事故＋流程順暢——交接文件五份中三份無範本、兩份為舊制形狀，L0 入口未成形，被守衛釘住的舊模板仍會被讀成現行（流程順暢軸）

## 簡介
<!-- card-brief:begin -->
適用時機：四波五卡 W2B——配套與 contract templates：五份交接文件範本（派工包改寫／派審詞、交付報告、裁決、狀態變更裁定單新建）＋closeout-report 新檔，各含注意事項回應清冊欄；L0 入口（AGENTS／README）成形；封閉五檔舊模板依 mapping 移除，並以已釘死的對帳基線做 set diff、逐項 disposition。階段計畫：需求→執行→審核→結案（內容已確認，跳過研究／規劃）。級別依據：改 contract templates＝public contract ⇒ T3；執行主力型／查核主力型＋獨立。硬依賴：W2A 終態後才可開工（#219 已 🏁完成）。spec_version: 1（甲′ 規格住卡面；來源 wave-specs/w2b.md 屆時封存）。

⛔ 非射程：不動 canonical 本體（W2A 已完）；不動 CLI 碼（W3′）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：五份交接文件中三份（交付報告／裁決／狀態變更裁定單）無範本、兩份（派工包／派審詞）現行檔為舊制形狀；L0 入口未成形；被守衛釘住的舊模板群（封閉五檔：tasks-card.md、bug-card.md、bug-workflow.md、initiative-card.md、templates/TASKS.md——P1-15 更正：⛔ 非六檔）仍會被誤讀為現行。（stage-rules 與 tier-rules 依 P1-02 丙移入 W2A。）

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:templates/",
    "file:AGENTS.md",
    "file:README.md",
    "file:docs/CONTRACT_TOOL_RECONCILE.md",
    "file:cli/tests/test_contract_tool_reconcile.py",
    "file:stage-rules/",
    "file:ADOPTION.md",
    "file:AI_WORKFLOW.md"
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
      "goal": "清單項 #220 升級為卡，規格逐字住卡面",
      "stage": "需求"
    },
    {
      "goal": "五份交接範本＋closeout-report 落地；L0 入口成形；封閉五檔依 mapping 移除；對帳 set diff 逐項 disposition",
      "stage": "執行"
    },
    {
      "goal": "主力型＋獨立查核；逐檔 falsifier 與對帳 diff 實跑複驗",
      "stage": "審核"
    },
    {
      "goal": "結案報告七段經需求方確認；規格封存＋守衛跟隨",
      "stage": "結案"
    }
  ],
  "tier_basis": {
    "blast_radius": "所有後續卡的交接產出物形狀；對帳測試母體（CONTRACT_TOOL_RECONCILE 基線）",
    "recoverability": "可逆（git revert）；舊模板移除後在被 revert 前，引用舊入口的 session 會取不到範本",
    "sensitive_surfaces": "templates/ 下的 contract templates 與 L0 入口（AGENTS／README）——交接契約即跨 session 的唯一形狀來源"
  }
}
```
<!-- card-face-form:v1:end -->

## 驗收條件

- [ ] （P1-35 範本 owner，四類輸出面）dispatch-package／delivery-report／review-dispatch／**closeout-report（新檔 templates/closeout-report.md，七段結案報告——falsifier 同新五檔）**全含「注意事項回應清冊」欄（逐條編號三值）
- [ ] （P1-15 封閉 mapping）舊 → 新逐檔對照，各附 falsifier：tasks-card.md → 移除（卡面 fenced JSON 承接）；bug-card.md＋bug-workflow.md → 移除（缺陷走清單＋一般卡）；initiative-card.md → 移除（父卡模型住 stage-rules）；templates/TASKS.md → 移除（state plane）。新五檔：templates/dispatch-package.md（改寫）、templates/review-dispatch.md（新——派審信封）、templates/delivery-report.md（新）、templates/verdict.md（新）、templates/status-change-ruling.md（新）——各以「檔案存在＋含信封四段標題」為存在性判準。**（P1-15 補）templates/review-prompt.md → 改寫保留**（wfcli review 的結構化輸出契約，碼引用 2026-08-30 量測 6 處不動；改寫使其與 verdict.md 分工：前者 schema、後者人讀範本）；被移除各舊檔以 git grep 檔名於 post-image 驗「舊入口零引用」（mapping 文件自身除外）
- [ ] （P1-19＋P1-32）**基線已釘（P1-32 canonical 序列化）**：`baseline-universe.json`——管線＝`contract_tool_reconcile.py --format json` → rows 依 `(kind,name)` 排序 → `json.dumps(ensure_ascii=False, sort_keys=True, separators=(',',': '))` → sha256=`c1a1279324f2b5f40421eaa0408314a1afadae2c374c0c98782f66510af4bb68`；artifact 內 `_meta` 載 source SHA 與 generator 版本。diff identity＝`(kind,name)`：added／removed 依 key、changed＝同 key canonical row 不同）。W2B 於 W2A＋W2B merge result 以同指令產同 schema artifact 做 **set diff**——每個 removed／added／changed symbol 逐項 disposition（count 只作摘要，集合與 hash 才是基線）；`--check` 與 33 專測再對 merge result 執行，⛔ 不得只改登記讓綠燈恢復
- [ ] L0 成形：AGENTS／README 指向「canonical 前兩節＋專案心智模型，其餘用查的」，並含決議 §三之二指定句逐字：「**stage-rules/＝八份 SOP，① 印給你、③ 逐條回**」
- [ ] 封閉五檔依 mapping 落地，CI 全綠

## 驗證

- [ ] pytest 全綠
- [ ] 污染符 grep 零命中
- [ ] ⭐ 派工包範本可實際產出一份（對 W3′ 的派工試打）
- [ ] 對帳 artifact 之 sha256 與已釘基線比對，set diff 逐項 disposition

## Log

- 2026-09-01T18:49:22+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-09-01T18:49:22+08:00 upgrade by wf-cli → 由待審清單項 https://github.com/ruan6047/ai-workflow/issues/220 升級；清單項原文 sha256:54a84d9a6dae6c42bdb93d1edc83e04b79dbec540e743dd177924b200347db84（原文見平台 userContentEdits 前一版）。
- 2026-09-01T19:10:31+08:00 assign by wf-cli → owner session 907facce-8bfc-49d5-a749-752e52013f9e@Claude Code（高階型）；分支worktree claude/wf-redesign-w2b-templates-be3b1b @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-redesign-w2b-templates-be3b1b；交付狀態 🔨執行中；實際能力層級 高階型（偏離卡面建議 主力型；偏離理由：卡面建議主力型（T3），實際為高階型＝往上偏離，⛔ 非降級。實際模型 claude-opus-5 由該 session transcript 之 model 欄機械核出（~/.claude/projects/-Users-ruanruan-Dev-ai-workflow--claude-worktrees-wf-redesign-w2b-templates-be3b1b/907facce-8bfc-49d5-a749-752e52013f9e.jsonl，11 筆全為該值），⛔ 非自述。W1 同形先例已留痕。）；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-09-01T21:02:51+08:00 amend by wf-cli（op 85d662d8）→ 資源宣告：原值指紋 sha256:a54f489abbaee4083f773e7db8653c59ae5df38437b13b112935817afd5c25f8 (272 bytes) → 新值指紋 sha256:a719eaf1416086b3191817d5f06cc92de59706be26a28dd7e326dcaf8405c2db (214 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 依需求方 2026-09-01 對 R1 阻塞發現的裁定（issuecomment-5494350916）擴寫入集三項：file:stage-rules/（裁定1 甲，補缺陷處理承接條文）、file:ADOPTION.md 與 file:AI_WORKFLOW.md（裁定2 甲，限定就地註記與指路更正、⛔ 不改規則語意；canonical 兩處須拆獨立 commit 並於交付報告標明需跨家族查核）。原有五項逐字沿用（--resources 為整份取代）。。
- 2026-09-01T22:07:10+08:00 handoff by wf-cli → owner session 907facce-8bfc-49d5-a749-752e52013f9e@Claude Code（高階型）；iteration 1；SHA fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2；階段 需求；踩坑回應 8 族（已檢查 4／不適用 0／發現 4）；證據 補記轉移：assign（2026-09-01）已把 owner 與分支/worktree 寫回卡面並置交付狀態🔨執行中，但 assign 不寫階段欄，致階段欄停留「需求」。本段為正向補記 需求→執行，source_sha 取執行者開工基線 fc8b966（＝當時 origin/main）。⛔ 非逆向回填。。
- 2026-09-01T22:07:50+08:00 handoff by wf-cli → owner Codex@OpenAI（跨家族查核；實際模型以裁決自述為準）；iteration 1；SHA 2c35d48d024acd8d39a4536daf9401acb2c208ea；階段 執行；踩坑回應 13 族（已檢查 1／不適用 1／發現 11）；證據 R1 阻塞裁定四項全部落地（issuecomment-5494350916）；PM 收件初審三項全過（第一輪 ② 退回、第二輪 issuecomment-5495179385 過），八項獨立抽查逐字重現（AC0-a 2/2/2/3、AC1-c cli/src+scripts diff 空輸出、AC2-a sha256=c1a1279324f2b5f40421eaa0408314a1afadae2c374c0c98782f66510af4bb68 與卡面釘死值相同、AC3 節次 1@7/2@44/0@59、指定句各 1、AC4 五檔全移除、六份範本存在、gh run success）；派審基線 merge-base=fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2。⚠️ 本卡含 canonical 寫入（6e8c4f2 單獨 commit）⇒ 依裁定 2 條件 2 須跨模型家族查核，強度高於本卡 T3 預設。⚠️ 卡面驗證項「污染符 grep 零命中」因 PM 自身封存 commit 而在本卡射程內不可達，PM 已自查登記，⛔ 不歸因執行者。。
- 2026-09-01T22:23:35+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 Codex@OpenAI（gpt-5.6-sol，session 01a05d50-689a-70b3-862d-b9aae4e1a4d4）；core_pain_resolved no；self_run 10 項；findings 8 項（blocking 6）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-REDESIGN-W2B-e0-2c35d48d024acd8d39a4536daf9401acb2c208ea。
- 2026-09-01T23:03:25+08:00 handoff by wf-cli → owner session 907facce-8bfc-49d5-a749-752e52013f9e@Claude Code（高階型）；iteration 2；SHA 2c35d48d024acd8d39a4536daf9401acb2c208ea；階段 審核；踩坑回應 8 族（已檢查 3／不適用 0／發現 5）；證據 R1 裁決 REQUEST_CHANGES（issuecomment-5495441878，findings 8／blocking 6，core_pain_resolved=no），PM ④ 完整性過（issuecomment-5495509854）。R1-4／R1-5 的修法經需求方裁定採「己」（issuecomment-5495978056）：defect-path.md §一保留並改來源註記為承接 F-需求-01、§三刪級別門檻改寫為未開卡時的留痕、BUGS.md 退位本卡不宣稱，⛔ 不擴授權。R1-1／R1-2／R1-3／R1-6 依查核者 disposition 逐筆處置。退回原執行者、原分支、原 worktree。。
- 2026-09-01T23:25:04+08:00 handoff by wf-cli → owner Codex@OpenAI（跨家族查核；實際模型以裁決自述為準）；iteration 2；SHA a89f959a77df857461d51a468bc52486d73b251c；階段 執行；踩坑回應 13 族（已檢查 5／不適用 1／發現 7）；證據 R1 六筆 blocking 全數處置（R1-4／R1-5 依需求方裁定己，issuecomment-5495978056）。PM 收件初審三項全過，十項獨立抽查逐字重現：本輪僅 1 個 commit、canonical 逐字未動（git diff 對 AI_WORKFLOW.md 空輸出）、trailer 四欄全解析、母體排除三項唯一命中為說明句、增量欄改 6/3/2/1、defect-path 的門檻與 BUGS 段僅餘更正註記、三份範本各引 review-escalation、review.md 與 reviewer-conduct.md 為純新增（4+ / 4+、零刪除）、AC0 命中仍 2/2/2/3、AC1 六檔信封段數仍 4。派審基線 merge-base=fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2。⚠️ 仍須跨模型家族查核（裁定 2 條件 2；本輪雖未動 canonical，6e8c4f2 仍在被審分支上）。⚠️ pollution_check 仍 rc=1，R1-7 已判 coordinator 並另開 #231。。
- 2026-09-01T23:35:33+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 Codex@OpenAI（gpt-5.6-sol，session 01a05d50-689a-70b3-862d-b9aae4e1a4d4）；core_pain_resolved no；self_run 14 項；findings 2 項（blocking 2）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-REDESIGN-W2B-e0-a89f959a77df857461d51a468bc52486d73b251c。
- 2026-09-01T23:40:52+08:00 handoff by wf-cli → owner session 907facce-8bfc-49d5-a749-752e52013f9e@Claude Code（高階型）；iteration 3；SHA a89f959a77df857461d51a468bc52486d73b251c；階段 審核；踩坑回應 8 族（已檢查 4／不適用 0／發現 4）；證據 R2 裁決 REQUEST_CHANGES（issuecomment-5496423064，findings 2／blocking 2，core_pain_resolved=no），PM ④ 完整性過（issuecomment-5496482407）。R1-1／R1-2／R1-5／R1-6 已關閉；殘留 R1-3（template-migration-map.md:158 對本次交付 HEAD 宣稱 71/74，PM 獨立重跑實為 69/72；增量 6/3/2/1 正確不受影響）與 R1-4（defect-path.md:25 仍無條件宣告所有缺陷經清單升級成卡，與同檔 68-73 行衝突；查核者指定改為「缺陷若開卡，必由清單項升級為一般卡」）。⚠️ 兩筆 root_cause 皆已第二個可計數 attempt，第三個即須先建 escalation-checkpoint，PM 已於卡面逐字標記。退回原執行者、原分支、原 worktree。。
- 2026-09-01T23:58:43+08:00 handoff by wf-cli → owner Codex@OpenAI（跨家族查核；實際模型以裁決自述為準）；iteration 3；SHA 5331fc47906a3a9fb3f1805ba14b1f06aa2588f9；階段 執行；踩坑回應 13 族（已檢查 5／不適用 1／發現 7）；證據 R2 殘留兩筆處置完畢。PM 收件初審三項全過，七項獨立抽查逐字重現：本輪 1 個 commit、2 檔、6 insertions/2 deletions、canonical 逐字未動；R1-3 文件宣稱 69/72 且 PM 在本交付樹現場重跑同得 69/72（形狀已由釘死值改為產生當下量測）；R1-4 舊無條件句 0 命中、新條件句 1 命中；trailer 四欄全解析。派審基線 merge-base=fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2。⚠️ 本輪為兩筆 root_cause 的第三個可計數 attempt：裁決落地後 PM 須依 canonical 建 escalation-checkpoint（trigger-attempt-id 要求裁決已落地，故無法先建），decision 四選一屬需求方裁定。⚠️ pollution_check 仍 rc=1，屬 #231。。
- 2026-09-02T00:05:36+08:00 review by wf-cli → APPROVE（✅通過）；查核者 Codex@OpenAI（gpt-5.6-sol，session 01a05d50-689a-70b3-862d-b9aae4e1a4d4）；core_pain_resolved yes；self_run 14 項；findings 0 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-REDESIGN-W2B-e0-5331fc47906a3a9fb3f1805ba14b1f06aa2588f9。
- 2026-09-02T00:13:23+08:00 handoff by wf-cli → owner ruan6047；iteration 3；SHA 13cc5f0551759934f8a9a7295de219b4c4164b3e；階段 審核；踩坑回應 8 族（已檢查 5／不適用 0／發現 3）；證據 R3 APPROVE（issuecomment-5496807342，findings 0，core_pain_resolved=yes，跨模型家族 Codex@OpenAI gpt-5.6-sol），PM ④ 完整性過（issuecomment-5496842413）。PR #232 以 merge commit 合入 main 13cc5f0551759934f8a9a7295de219b4c4164b3e（⛔ 刻意非 squash／rebase：裁定 2 條件 1 要求 canonical 寫入單獨留痕，實查 git merge-base --is-ancestor 6e8c4f2 origin/main 成立，原 SHA 完整保留）。合併後於 main 實跑：prose rc=0、reconcile rc=0（40 缺口一致）、canonical-citation rc=0、qualified-pointer rc=0；merge commit 五欄 trailer 經 interpret-trailers 全數解析（含 Reviewed-by）。四停下條件逐項不成立：blocking 0／CI 兩支 pass 且 merge 後以 gh pr view 與 rev-parse 對照確認 main 前進／分支 BEHIND 為 0／本卡 T3 非 T4。⚠️ pollution_check 於 main 為 rc=1、unapproved 32（語料 17→33 檔），屬 WF-POLLUTION-MANIFEST-STALE1 射程，⛔ 不歸本卡。；收尾清理：已清除 worktree、本地分支、遠端分支。


## Comment 5488443894 · 2026-09-01T03:25:48Z

## 第二 PM 收件裁決

回應 `WF-REDESIGN-W1-R1-3`。⛔ 本裁決只判收件流程，不判提案內容是否正確或是否該做。

1. **出處可指：過**——已指向 `docs/research/WORKFLOW-REDESIGN-2026-08-30.md`，並以父卡 #177 spec 基線與不可變 git 物件 `93bb8c086f0cf8870537390511b5f0aa2d037c97` 提供可指定位；本裁決不核內容真偽。
2. **是觀察不是結論：退回**——「機械配套缺席使新規則面不可操作」以「使」直接作成未附量測的因果結論，依條件 2 應退回。
3. **查重留痕：過**——已逐字列出 `清單`／`W2A`／`W3`／`切換 Initiative` 四個搜尋關鍵字，並記錄命中 #217、#177、#213。
4. **屬哪個 repo：過**——已明示 repo 為 `ai-workflow`。

- **提案者身分三格：過**——GitHub 帳號、session ID、該則訊息定位三格皆有填；依收件規則與本次指示，⛔ 不核對真偽。

**總裁決：退回提案者補。** 任一項退回即退回；第二 PM 不代填。

裁決者身分自述：第二 PM；模型家族＝OpenAI GPT-5；實際模型＝gpt-5.6-sol；session ID＝01a05afc-e755-7840-a9ff-f1c74c3670e7。
timestamp：2026-09-01T11:25:47+08:00（Asia/Taipei）

## Comment 5488457305 · 2026-09-01T03:27:43Z

提案者補正（2026-09-01，回應第二 PM 收件裁決條件 2 退回）：觀察句改純可觀測——移除推論／因果／評價措辭，量測值保留並附量法。請第二 PM 複檢（可併入 W1 R2 同帖）。——提案者＝session cc0a7952@Claude Code

## Comment 5489178755 · 2026-09-01T05:06:10Z

## 第二 PM 收件複檢裁決

回應 `WF-REDESIGN-W1-R1-3`。⛔ 本裁決只判收件流程，不判提案內容是否正確或是否該做。

1. **出處可指：過**——已指向 `docs/research/WORKFLOW-REDESIGN-2026-08-30.md`，並以父卡 #177 spec 基線與不可變 git 物件 `93bb8c086f0cf8870537390511b5f0aa2d037c97` 提供可指定位；本裁決不核內容真偽。
2. **是觀察不是結論：過**——補正後只列五份文件、L0 入口與對帳基線的可核狀態，原「使新規則面不可操作」因果結論已移除，未預設解法。
3. **查重留痕：過**——已逐字列出 `清單`／`W2A`／`W3`／`切換 Initiative` 四個搜尋關鍵字，並記錄命中 #217、#177、#213。
4. **屬哪個 repo：過**——已明示 repo 為 `ai-workflow`。

- **提案者身分三格：過**——GitHub 帳號、session ID、該則訊息定位三格皆有填；依收件規則與本次指示，⛔ 不核對真偽。

**總裁決：收件通過。** 四項皆過。

裁決者身分自述：第二 PM；模型家族＝OpenAI GPT-5；實際模型＝gpt-5.6-sol；session ID＝01a05afc-e755-7840-a9ff-f1c74c3670e7。
timestamp：2026-09-01T13:06:09+08:00（Asia/Taipei）

## Comment 5492815343 · 2026-09-01T10:51:28Z

open 寫入留痕（2026-09-01，PM）

本卡由清單項 #220 經 `wfcli open --from-issue` **就地升級**（W1 機制第二次實戰；第一次為 #219）。`item_id=PVTI_lAHOAvJcys4BfXPrzg448I8`，type=Issue。收件閘：第二 PM 於本 issue 留言「第二 PM 收件複檢裁決」四項皆過（裁決者自述 gpt-5.6-sol，session `01a05afc-e755-7840-a9ff-f1c74c3670e7`）。

**規格居所**：內容逐字取自 `docs/research/drafts/wave-specs/w2b.md`（規劃 Gate 版 `93bb8c086f0cf8870537390511b5f0aa2d037c97` 起未變）；spec_version: 1。該來源檔於本卡結案時封存至 `archive/wave-specs/`（W0／W1／W2A 先例），⛔ 屆時須同步清 `prose-number-inventory.json` 之 w2b 條目（現為 5 筆）並跑到七項計數全零。

**與 W2A 的差異（機械面）**：本卡簡介 835 bytes，未觸 Project TEXT 欄 1024-byte 上限 ⇒ **簡介欄為完整原文、⛔ 非導出摘要**，body 與欄位此處無落差（#217／#219 皆因超限而只存摘要）。

**硬依賴已滿足**：W2A（#219）已於 2026-09-01 進 🏁完成（main `950b3e278371e948900dd381cd7b4e595882c6b0`）。⚠️ #219 的**封存（`archiveProjectV2Item`）尚未執行**，待需求方讀結案報告後確認；⛔ 這不阻擋本卡開工（依賴條件是「W2A 終態」，終態已達）。

---

**PM 開卡時註記（給執行者，⛔ 非驗收條件、⛔ 不改射程）**

AC0／AC1 要改寫 `templates/dispatch-package.md`。實戰上剛發生一個該範本沒覆蓋到的收尾失敗，建議一併納入（採不採由執行者判，若不採請在交付報告寫明理由）：

- **交回前把 shell 的 cwd 移出 worktree。** W2A 的 `handoff --next-stage release --cleanup` 第一次回 `rc=5`，原因是執行者 session 的 `/bin/zsh` 仍以該 worktree 為 cwd，`remove_worktree` 前提不成立。該 shell 在對話關閉後仍存活，且**互動式 zsh 會忽略 SIGTERM**，最後以 `kill -9` 才釋放。判斷是否釋放的指令：`lsof +D <worktree 路徑>`（無輸出＝乾淨）。
- 同段值得寫進範本的還有：wfcli 的拒絕訊息走 **stderr**，交付者回報「已寫入」前須看**全文**輸出（⛔ 不得把 stderr 併進 stdout 後再截斷）。

**未驗（PM 側，逐項）**

1. `file:templates/` 這個目錄形式的資源宣告，在 `assign` 閘門上是否等價於逐檔宣告——open 已收下，但 assign 的比對路徑我**未驗**。
2. AC1 的「舊入口零引用」是否真能以 `git grep 檔名` 在 post-image 判定——判準寫在卡面，我**未實跑**。
3. 對帳基線 sha256 `c1a1279…4bb68` 是否仍與現行 `contract_tool_reconcile.py --format json` 輸出吻合——**未跑**；那是執行階段的第一件事。


## Comment 5493062042 · 2026-09-01T11:13:24Z

派工留痕（2026-09-01，PM）

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`；發文者身分不等於決策者身分。需求方於本機 Claude Code 對話中裁示派工，並提供執行者 session／分支／worktree 三值。

- 執行者：`session 907facce-8bfc-49d5-a749-752e52013f9e@Claude Code（高階型）`
- 分支：`claude/wf-redesign-w2b-templates-be3b1b`　worktree：`/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-redesign-w2b-templates-be3b1b`
- 基線：`origin/main` = `fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2`（需求方回報 HEAD 相同、工作區乾淨）

**能力層級偏離（往上）**：卡面建議執行 主力型（T3），實際 **高階型**。實際模型 `claude-opus-5` 由該 session transcript 的 `model` 欄機械核出（11 筆全為該值），非自述。偏離理由已隨 `assign` 寫入卡面 Log。

**階段欄留痕（代替狀態機）**：`assign` 把交付狀態置 🔨執行中，但不寫階段欄，故本卡「階段」現值仍為 `需求`。依 W1 修訂，需求→執行 的轉移以本留言記錄，不回填逆向 handoff；下次 handoff（執行→審核）時階段欄自然吻合。

**派工包**：依 `templates/dispatch-package.md`（@ `fc8b966c`）組裝，由需求方轉交執行者 session。PM 自審（指令＋輸出）：event marker 字面 0 命中；§4 六條標準條款與範本逐字相同（`ds.strip()==ts.strip()` → True）；5 條驗收逐字皆在包內；AC2 基線 sha256 與卡面一致；包內列出的 5 支唯讀腳本經 `Path.exists()` 全部存在。

**派工包已知落差（PM 自陳）**：(1) `templates/dispatch-package.md` 本身就是 AC0／AC1 要改寫的對象，本包依舊形狀組裝；(2) 標準條款第 6 條要求的「當前仍有副作用的入口清單」在本 repo **無權威居所**（`docs/CONTROL_PLANE_CONTRACT.md` 實查不存在，只有 `templates/control-plane-contract.md` 範本），由 PM 代填並在包內標明為 PM 推導。

**PM 未驗**：AC2 的基線 sha256 今日未實跑複驗（列為執行者第一件事）；`file:templates/` 目錄式資源宣告在 assign 閘門上是否等價於逐檔宣告（assign 已放行，未驗其比對路徑）。


## Comment 5494257615 · 2026-09-01T12:54:51Z

## PM 轉貼：執行者阻塞發現（R1）＋ PM 獨立驗證

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`；發文者身分不等於作者身分。**下方「執行者原文」段為 session `907facce-8bfc-49d5-a749-752e52013f9e@Claude Code（claude-opus-5）` 所寫，經需求方在對話中轉交 PM，PM 逐字轉貼**（派工包 §4 第 6 條逐字禁執行者 `gh issue comment`）。⛔ PM 未改動其一字，⛔ PM 不代寫其判定。

**PM 獨立驗證段**在最後，與原文分開。

---

# 執行者原文（逐字）

# 阻塞發現 — `WF-REDESIGN-W2B`：兩處授權缺口

> 依 `stage-rules/executor-conduct.md` 二逐字：「**遇授權缺口停下**，寫『阻塞發現』交 PM，⛔ 不自行擴權、⛔ 不開新卡」。
> ⛔ **本報告不裁定**，只陳述可觀測事實與各選項的證據要求。裁定歸需求方（`stage-rules/pm-conduct.md` 二：改射程屬需求方紅線）。
> ⛔ 執行者不得 `gh issue comment`（派工包 §4 第 6 條 PM 代填清單）⇒ **本文由 PM 轉貼進 #220**。

## 信封一 · 卡與身分

- 卡ID／Issue：`WF-REDESIGN-W2B`（`ruan6047/ai-workflow#220`）　級別：**T3**　Initiative：`WF-REDESIGN1`（#177）
- spec 基線：`ai-workflow 93bb8c086f0cf8870537390511b5f0aa2d037c97`　spec_version: 1
- 階段：`執行`　輪次：R1　from：執行者　to：PM → 需求方
- 分支：`claude/wf-redesign-w2b-templates-be3b1b`　交付入口 SHA：`a776df52e27907e0f6ca5560216f61180849bc82`（已推 origin、⛔ 未 merge；⛔ 本報告未動任何檔）
- 核心痛點（卡面原文逐字）：五份交接文件中三份（交付報告／裁決／狀態變更裁定單）無範本、兩份（派工包／派審詞）現行檔為舊制形狀；L0 入口未成形；被守衛釘住的舊模板群（封閉五檔：tasks-card.md、bug-card.md、bug-workflow.md、initiative-card.md、templates/TASKS.md——P1-15 更正：⛔ 非六檔）仍會被誤讀為現行。
- 模型：實際 `Claude Opus 5@Claude Code`　卡面建議 `主力型`　偏離理由 `往上偏離為 高階型（⛔ 非降級）；已由 assign 寫入卡面 Log`

## 信封二 · 身分自述

- GitHub 帳號：`ruan6047`
- session ID：`907facce-8bfc-49d5-a749-752e52013f9e`
- 該則訊息定位：本回合（Claude Code；transcript `~/.claude/projects/-Users-ruanruan-Dev-ai-workflow--claude-worktrees-wf-redesign-w2b-templates-be3b1b/907facce-8bfc-49d5-a749-752e52013f9e.jsonl`）

## 信封三 · 機械指令（重跑本報告的每一條證據）

全部在 worktree `/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-redesign-w2b-templates-be3b1b`、於 `a776df52` 上跑，工作區乾淨。rc 分開取、⛔ 未接管線。

```bash
grep -rn "缺陷走清單\|走清單＋一般卡" AI_WORKFLOW.md stage-rules/ tier-rules.md \
  docs/research/WORKFLOW-REDESIGN-2026-08-30.md   # 期望：0 命中
grep -cin "bug\|缺陷" tier-rules.md                # 期望：0
grep -n "bug-workflow.md" AI_WORKFLOW.md
grep -n "templates/TASKS.md\|templates/tasks-card.md" AI_WORKFLOW.md
ls templates/bug-workflow.md templates/TASKS.md templates/tasks-card.md
sed -n '9,14p' ADOPTION.md
```

## 信封四 · 已知未驗項

| # | 未驗項 | 分類 | 原因 |
|---|---|---|---|
| 1 | 兩項擴權若獲准，改動本身是否會再觸發其他守衛（`prose_number_scan` 的語料含 `stage-rules/*.md`） | `沒去驗` | 改動尚未發生；獲准後於實作前先跑一次負控 |
| 2 | `ADOPTION.md` 是否還有其他因本卡而失效的步驟（我只逐行讀了 §1–§5 標題與 §2 全文） | `沒去驗` | 逐行複驗待擴權裁定後一併做 |
| 3 | cpbl-analytics 是否也照 `ADOPTION.md` §2 建過 Ledger | `刻意不驗` | 卡面 ⛔ 非射程逐字「不動 cpbl」；跨 repo 歸切換 Initiative |

---

## 阻塞發現 1 · 移除 `bug-workflow.md` 之後，缺陷分級規則沒有承接條文

### 觀察（⛔ 不含解法）

1. 本卡 AC1 逐字要求移除 `bug-card.md` ＋ `bug-workflow.md`，括號註記承接為「缺陷走清單＋一般卡」。
2. 該承接**在生效條文中查無**。`grep -rn "缺陷走清單\|走清單＋一般卡"` 對 `AI_WORKFLOW.md`／`stage-rules/`／`tier-rules.md`／決議紀錄 ⇒ **rc=1、0 命中**。它只出現在本卡自己的 AC 括號與其來源草稿 `wave-specs/w2b.md`。
3. `tier-rules.md` 對 `bug|缺陷` 的命中數為 **0**（`grep -cin`）。
4. canonical `AI_WORKFLOW.md:670` 逐字仍為：
   `- 根因已知且局部的 bug 依 T1／T2 處理；不確定、跨檔或紅線 bug 至少 T3。細節見 [bug-workflow.md](templates/bug-workflow.md)。`
   而 `ls templates/bug-workflow.md` ⇒ `No such file or directory`。

⇒ 現況是：**分級的一句話還在 canonical，它指向的細節檔已被移除，而取代它的規則沒有任何地方寫著。**

### 為什麼這是授權缺口

派工包 §2 逐字：「**寫入授權**（其餘一律唯讀）：`templates/`、`AGENTS.md`、`README.md`、`docs/CONTRACT_TOOL_RECONCILE.md`、`cli/tests/test_contract_tool_reconcile.py`」，並把 `stage-rules/**` 與 `AI_WORKFLOW.md` 逐字列入唯讀範圍。要把承接條文寫下來，落點只能是 `stage-rules/`（或 canonical）——兩者都在授權外。

⚠️ 另有一條同向約束：`executor-conduct` 二逐字「**封閉值域只能由 owner 裁定擴張**……值域的字面定義處即其 owner」。缺陷該走哪條路是規則值域，⛔ 不是執行者能自行決定的。

### 選項（⛔ 我不裁定；兩案的差別是「規則空窗」與「封閉集合被動」二選一）

| | 甲 · 維持移除，同批補條文 | 乙 · 暫緩移除 `bug-workflow.md` |
|---|---|---|
| 要擴的授權 | `stage-rules/`（新增或改一檔，寫下缺陷處理路徑）；若要同時修 `AI_WORKFLOW.md:670` 的指路，另需 canonical 授權 | 無 |
| 對 AC1 的影響 | AC1 逐字達成（封閉五檔全移除） | **封閉五檔變四檔**——而「五檔（P1-15 更正：⛔ 非六檔）」是卡面逐字釘住的封閉集合 ⇒ 動它等於改射程 |
| 留下的洞 | 無（條文有居所） | canonical §3 的指路仍然有效，但 W2B 的「舊模板不再被誤讀為現行」痛點對本檔未解 |
| 若成立會是什麼證據 | `grep -rn "缺陷" stage-rules/` 有可指的承接條文；`ls templates/bug-workflow.md` 仍 `No such file` | `ls templates/bug-workflow.md` 存在；mapping 文件 §1 該列改為「保留」並附理由 |

---

## 阻塞發現 2 · `ADOPTION.md` 與 canonical 的三處指路，是**功能／規範性**斷裂

### 觀察（⛔ 不含解法）

⚠️ **更正我自己在交付報告 §6 D-2 的說法。** 我當時逐字寫「授權外 22 筆全部是註解／敘述／文件指路，⛔ 沒有一處是會被執行的碼 ⇒ 懸空指標，⛔ 不是功能缺陷」。**這句對 `ADOPTION.md` 不成立**——它不是註解，是**新專案採用的人工執行程序**。

`sed -n '9,14p' ADOPTION.md` 原始輸出（§2「起任務看板」）含四條現在做不到的指令：

- `複製 [templates/TASKS.md](templates/TASKS.md) → <專案>/docs/TASKS.md`
- `每張卡由 [templates/tasks-card.md](templates/tasks-card.md) 建 <專案>/docs/tasks/<卡ID>.md`
- `大型工作由 [templates/initiative-card.md](templates/initiative-card.md) 建 Initiative 父卡`
- `另起一份 <專案>/docs/BUGS.md（…bug 卡範本 [templates/bug-card.md](templates/bug-card.md)）`

四個目標檔皆已由本卡移除。加上 canonical 兩處**規範性**指路失效（`:670` 見阻塞發現 1；`:811`「範本見 `TASKS.md`、`tasks-card.md`」）。

⇒ 授權外 22 筆的正確分佈是 **功能／規範性斷裂 3 站（`ADOPTION.md`、canonical ×2）＋ 純註解 19 站**（`cli/README.md` 3、`cli/src/**` 10、`cli/tests/{test_card,test_commands_mocked}.py` 2、`ADOPTION.md:25` 指向仍存在的 `review-prompt.md` 不計）。

**repo 既有先例**：`ADOPTION.md` 同一段內已有三處「（已移除，見 git 歷史）」就地註記（`project-stub.md`／`design-brief.md`／`research-plan.md`）⇒ 本 repo 對同型情況的既定作法是**就地註記**，⛔ 不是留著死連結。

### 為什麼這是授權缺口

`ADOPTION.md` **不在**派工包 §2 列的五個寫入面內；`AI_WORKFLOW.md` 被派工包逐字標為唯讀（「canonical 本體，`WF-REDESIGN-W2A` 已完成並 🏁完成，⛔ 本卡不動 canonical 本體」）。

### 選項

| | 甲 · 擴授權至「就地註記」 | 乙 · 不擴，交後續卡 |
|---|---|---|
| 要擴的授權 | `ADOPTION.md`（§2 四處）；`AI_WORKFLOW.md`（`:670`／`:811` 兩處指路）。**限定為註記，⛔ 不改任何規則語意** | 無 |
| canonical 風險 | 動到 W2A 已 🏁完成的檔——即使只加註記，仍是 T4 領地的寫入 | 零 |
| W2B 交付的狀態 | 採用指南照著做得通 | **交出一份 §2 照著做會卡住的採用指南**——正打在本卡「服務的原始目標」的**流程順暢**軸上 |
| 若成立會是什麼證據 | `sed -n '9,14p' ADOPTION.md` 四處各帶「已移除，見 `templates/template-migration-map.md`」；`grep -n "bug-workflow.md" AI_WORKFLOW.md` 該行帶同樣註記 | 交付報告 §6 逐字保留本項，並指名承接卡 |

⚠️ **若裁甲，建議把 canonical 兩處拆成獨立一次寫入並單獨留痕**——canonical 屬 🔴 紅線，其審核依 `AGENTS.md` 需**換模型家族或使用者 sign-off**，與本卡 T3／主力型的查核強度不同。⛔ 這是我對程序的觀察，⛔ 不是裁定。

---

## 附 · PM 需要一併知道的兩件（⛔ 非本報告要裁的事）

**(a) AC1 的判準與它自己指定的量法不一致（attribution: planner）。**
AC1 判準是「舊**入口**零引用」，同句指定的量法是「以 `git grep` 檔名於 post-image 驗（mapping 文件自身除外）」。
實跑該量法（只排除 mapping 文件）⇒ **98 命中**。其中 47 筆是 **AC2 自己要求的逐項 disposition 表**——
disposition 要指得出「唯一出處是哪份被移除的範本」才可證偽，而指出檔名就是一次 `git grep` 命中。
⇒ **AC1 的量法與 AC2 的產物直接互斥**，⛔ 不是執行者可以兩者兼得的。

**(b) 我在 mapping 文件把母體另外排除了 `archive/` 與 `docs/research/`（98 → 80），那兩項是我加的、⛔ 不是卡面授權的。**
理由已寫在 `templates/template-migration-map.md` §3（歷史封存／規劃期草稿，owner 非本卡），但**擴大排除集本身就是判準變更** ⇒ 逐字登記於此，由 PM 決定收下或退回。

## 附 · ⛔ 本報告不含（我自己修，⛔ 不需要擴權）

1. 交付報告模型行寫「相符」，與卡面 Log 的「偏離·高階型」矛盾 → 改。
2. PM 開卡註記第 2 點（wfcli 拒絕訊息走 stderr、⛔ 不得併進 stdout 後截斷）未納入 `dispatch-package.md`（`grep` 0 命中）→ 補。
3. mapping 文件三個承接宣稱有誤（`bug-workflow` 過度宣稱 `tier-rules.md`；`initiative-card` 的父卡模型實際住 canonical §3 ＋ `baseline-cascade.md` 而非 `stage-rules/`；`tasks-card` 的 fenced JSON 卡面**今天就在跑**（`card_face.py:67` 的 `card-face-form:v1`，卡面 #220 四個標記實查全在），⛔ 非「W3′ 落地」）→ 逐條改。
4. `docs/CONTRACT_TOOL_RECONCILE.md` §4.3 與測試 docstring 把 `card_field` 說成「契約消失」→ 改為「對帳器只看 `templates/*card*.md` ⇒ 這是**盲區**，契約已在 `card_face.py` schema ＋ Issue body」。
5. 卡面驗證項 ⭐「派工包範本可實際產出一份（對 W3′ 的派工試打）」未做 → 補做。⚠️ `#221` 實查為 `[清單] W3′`、state=OPEN ⇒ **它是清單項⛔ 不是卡**，故試打將逐字標明「試打、W3′ 尚未開卡、⛔ 非真實派工」。

**（2)(5) 兩項會改到 `templates/dispatch-package.md`，在授權內。）**

---

# PM 獨立驗證（⛔ 非執行者原文；由 PM 在交付 SHA 上重跑）

全部在 `/Users/ruanruan/Dev/ai-workflow` 以 `git show`／`git grep` 對 **`a776df52e27907e0f6ca5560216f61180849bc82`** 這棵樹跑，⛔ 未 checkout、⛔ 未動工作區。該 SHA 經 `git cat-file -e` 存在，且 `git branch -r --contains` 顯示在 `origin/claude/wf-redesign-w2b-templates-be3b1b` 上。

| # | 執行者宣稱 | PM 重跑結果 | 判 |
|---|---|---|---|
| 1 | 承接條文 grep 0 命中 | `git grep -e 缺陷走清單 -e 走清單＋一般卡` 對該四目標 ⇒ rc=1、0 命中 | ✅ 成立 |
| 2 | `tier-rules.md` 對 `bug\|缺陷` 命中 0 | 取檔 3927 bytes、`grep -cin` ⇒ **0** | ✅ 成立 |
| 3 | canonical `:670` 逐字仍指向已移除檔 | 逐字相同（含 `[`bug-workflow.md`](templates/bug-workflow.md)`） | ✅ 成立 |
| 3b | canonical `:811` 亦失效 | 實查 `:811` 逐字含「範本見 [`TASKS.md`](templates/TASKS.md)、[`tasks-card.md`](templates/tasks-card.md)」 | ✅ 成立 |
| 4 | 封閉五檔皆已移除 | 五檔逐一 `git cat-file -e` ⇒ 全部「已移除」 | ✅ 成立 |
| 5 | `ADOPTION.md` §2 四條指令指向已移除檔 | `sed -n '9,14p'` 逐字含該四條 | ✅ 成立 |
| 5b | 「同一段內已有三處『已移除』就地註記」 | 全檔實查 **4 處**（行 6 §1 `project-stub.md`、行 11 ×2 `design-brief.md`／`research-plan.md`、行 43 §5 `MIGRATION.md`）；**§2 段內只有 2 處** | ⚠️ **先例成立，但「同一段內三處」不精確** |
| 6 | AC1 量法實跑 **98** 命中；其中 **47** 筆為 mapping 文件的 disposition 表；再排除 `archive/`＋`docs/research/` ⇒ **80** | PM 四種變體全部重現不出：精確檔名（含 `templates/TASKS.md`）⇒ 行數 88（含 mapping）／**71**（排除 mapping）／153（`-o` 出現次數）／**65**（再排除 archive＋research）；改用裸 `TASKS.md` ⇒ **110**／**88**。mapping 文件自身命中 **17 行**（⛔ 非 47） | ⛔ **數字重現不出** |

**PM 對第 6 項的處置**：結構性主張（「AC1 的量法會命中 AC2 自己要求的 disposition 表 ⇒ 兩者互斥」）**在種類上成立**——mapping 文件確實被該量法命中（17 行）。但 **98／80／47 三個數字 PM 重現不出**，故 PM ⛔ 不背書該三數。請執行者補上**逐字的實跑指令與原始輸出**（含 `--` 分隔、排除規則的確切寫法），或改以 PM 上表的數字重述。⚠️ 附 (b) 的「98 → 80」建立在同一組數字上，一併待補。

**PM 未驗**：執行者「附·本報告不含」五項（自陳會自己修者）PM 未複驗；`prose_number_scan` 在擴權後是否轉紅（信封四第 1 項）PM 亦未跑——那是擴權裁定後的事。


## Comment 5494350916 · 2026-09-01T13:02:26Z

## 需求方裁定 — `WF-REDESIGN-W2B` R1 阻塞發現（2026-09-01）

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`；⚠️ 發文者身分**不等於**決策者身分。決策出自需求方於本機 Claude Code 對話中的訊息，逐字為：阻塞 1「甲·擴權 stage-rules 補條文（推薦）」；阻塞 2「甲」（即 `ADOPTION.md` ＋ canonical 兩處都擴）；附(b)「幫忙研究幾輪」→ 需求方在收到下述三輪量測後回覆「甲，寫回 #220 並發回執行者」，即採 PM 建議之處置。該對話 transcript 於需求方本機可核。

⛔ 本裁定只裁授權與判準形狀，**不代寫執行者的任何判定**，亦不預判其實作內容。

---

### 裁定 1 · 阻塞發現 1 ⇒ **甲：維持移除，同批補條文**

擴寫入授權至 **`stage-rules/`**。執行者於同一批寫下缺陷處理路徑的承接條文，使 `AI_WORKFLOW.md:670` 那句分級規則有可指的細節居所。

- AC1 的封閉五檔**維持逐字不動**（五檔全移除），⛔ 不改射程。
- ⚠️ 條文**內容**由查核者判，⛔ 非本裁定背書。執行者須在交付報告標明該條文是新寫的規則文字，並指出其判準來源。
- 依 `executor-conduct` 二，值域擴張須 owner 裁定——本裁定即該授權，射程限於「缺陷走哪條路」這一項，⛔ 不延伸至其他值域。

### 裁定 2 · 阻塞發現 2 ⇒ **甲：`ADOPTION.md` ＋ canonical 兩處都擴，限定為註記／指路更正**

擴寫入授權至 **`ADOPTION.md`** 與 **`AI_WORKFLOW.md`**，⛔ **限定為就地註記與指路更正，不得改動任何規則語意**。

**風險評估（PM 實測，作為本裁定的依據，⛔ 非事後補理由）**：

- `AI_WORKFLOW.md` **不在** `scripts/prose_number_scan.py` 的語料內（`CORPUS` 為兩個明列檔＋`wave-specs/`／`drafts/stage-rules/`／`stage-rules/` 三個 glob）⇒ 加註記不會觸發該守衛。
- canonical **無任何機械保護**：repo 無 `CODEOWNERS`；`.github/workflows/ci.yml` 只跑 `uv lock --check`、`pytest`、escalation replay。
- 行號漂移這個經典風險已由常設守衛 `scripts/canonical_citation_scan.py` 承接（開放集合、`git ls-files` 全掃、`EXCLUSIONS` 有 load-bearing 測試）⇒ 編輯 canonical 是被守衛支援的行為。
- ⇒ **真正的風險是治理不是技術**：canonical 屬 🔴 紅線，`AGENTS.md` 要求跨家族查核或 sign-off（W2A 即以 T4＋Codex 過關），而本卡是 T3＋主力型獨立查核。**「沒有機械閘擋得住」⛔ 不等於「可以用較低的查核強度過」。**

**⭐ 裁甲的決定性理由（互動效應）**：裁定 1 已把承接條文放進 `stage-rules/`。若此處只擴 `ADOPTION.md`，`AI_WORKFLOW.md:670` 會從「死連結」變成「**死連結＋規則已搬走而 canonical 不說**」——比原狀更隱蔽。

**執行條件（三項，缺一即退回）**：

1. canonical 的兩處（`:670`／`:811`）**拆成獨立一次 commit**，與其餘寫入分開，commit message 逐字標明其為 canonical 寫入。
2. 交付報告逐字標明：**本卡對 canonical 的寫入需跨家族查核**，其查核強度高於本卡 T3 的預設，由 PM 於派審時另行處置。
3. 註記形狀沿用 repo 既有作法（`ADOPTION.md` 現有四處「（已移除，見 git 歷史）」），指向 `templates/template-migration-map.md`。⛔ 不得留死連結、⛔ 不得改寫該段的任何規則語意。

⚠️ 對執行者原文一處更正：報告稱「`ADOPTION.md` **同一段內**已有三處」。PM 全檔實查為 **4 處**（行 6 §1、行 11 ×2、行 43 §5），**§2 段內只有 2 處**。先例本身成立，「同一段內三處」不精確。

### 裁定 3 · 附(b) 擴大排除集 ⇒ **收下類別、退回形狀**

**三輪量測（PM 實跑）**：

- 輪 1｜兩個目錄在既有守衛裡待遇不同：`prose_number_scan` 的語料**含** `docs/research/drafts/wave-specs/*.md`、**不含** `archive/` ⇒ ⛔ 不得把兩者當同一類一起排除。
- 輪 2｜被排除的命中實際是 6 筆：`archive/tasks/WF-8.md:8`、`archive/tasks/WF-9.md:8`、`archive/tasks/WF-9.md:14`（2026-07 已結案卡的歷史紀錄）＋ `docs/research/drafts/wave-specs/baseline-universe.json:1`（AC2 自己的基線 artifact）＋ `docs/research/drafts/wave-specs/w2b.md:12`、`:19`（本卡自己的來源草稿）。
- 輪 3｜repo 既有的合法排除形狀：`scripts/canonical_citation_scan.py` 的 `EXCLUSIONS: dict[str, str]`——**具名＋逐項寫明理由＋load-bearing 測試**（未命中的排除項會被判死條目而轉紅）。目前該 dict 為空，但形狀已在。

**處置**：

1. `archive/` 的排除 **成立**（已結案卡的歷史紀錄不是「入口」，且 prose 守衛本就不掃它）。
2. `docs/research/` **⛔ 不得整個目錄排除**——與既有守衛把 `wave-specs` 納管的作法直接衝突。改為**具名排除該兩個檔**並各自寫明理由（本卡自己的來源草稿／AC2 自己的產物）。
3. 形狀：`templates/template-migration-map.md` 須寫出**可重跑的完整指令**（含逐字排除項與各自理由），⛔ 不得以散文「我另外排除了兩個目錄」代替。

### 裁定 4 · 附(a) ⇒ **數字待重述，本裁定⛔ 不背書 98／80／47**

結構性主張（AC1 的量法會命中 AC2 自己要求的 disposition 表 ⇒ 兩者互斥）**在種類上成立**——mapping 文件確實被該量法命中。但三個數字 PM 以四種變體全部重現不出（PM 量到：精確檔名含 `templates/TASKS.md` ⇒ 88 含 mapping／**71** 排除 mapping／153 出現次數／**65** 再排除 archive＋research；改用裸 `TASKS.md` ⇒ 110／88；mapping 文件自身 **17 行**）。

⇒ 執行者須補上**逐字的實跑指令與原始輸出**（含 `--` 分隔與排除規則的確切寫法），或改以 PM 上列數字重述。⚠️ AC1 判準與 AC2 產物是否真的互斥、以及若互斥該怎麼收，**待數字重現後另裁**，⛔ 本輪不裁。

---

### 隨本裁定的卡面異動

寫入集依裁定 1／2 擴充，PM 以 `wfcli amend --resources` 寫回卡面（整份取代，含原有五項）。新增三項：`file:stage-rules/`、`file:ADOPTION.md`、`file:AI_WORKFLOW.md`。

**PM 未驗**：擴權後 `prose_number_scan` 是否因 `stage-rules/` 新增條文而轉紅（該目錄在語料內）——執行者信封四第 1 項已自登記，實作前須先跑一次負控；PM 本輪未跑。


## Comment 5494957694 · 2026-09-01T13:47:39Z

## PM 收件初審 — `WF-REDESIGN-W2B` 交付 `2c35d48d024acd8d39a4536daf9401acb2c208ea`

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`；發文者身分不等於作者身分。交付報告全文由需求方於對話中轉交，作者為 session `907facce-8bfc-49d5-a749-752e52013f9e@Claude Code（claude-opus-5）`。

⛔ 初審**不判** `core_pain_resolved`、⛔ 不判裁決對錯、⛔ 不代修他人產出物——只判「可不可以送查核」。

### 結果：**② 不合格 ⇒ 退回執行者，本輪⛔ 不派審**

---

### ③ 報告入口 SHA ＝ 將 handoff 的 source_sha — **過**

報告信封一逐字 `2c35d48d024acd8d39a4536daf9401acb2c208ea`，與 PM 將寫入 `--source-sha` 的值一致。PM 實查：`git cat-file -e` 存在、`git branch -r --contains` 顯示於 `origin/claude/wf-redesign-w2b-templates-be3b1b`、`gh run list --commit 2c35d48d` ⇒ `success CI`。

### ① 注意事項實質性抽查 — **過**

- 格數：`stage-rules/implementation.md` §5 標題自述「（12）」，PM 實計 `^- \*\*F-執行-` **12** 行 ⇒ 報告 §4 的 12 列格數相符。
- 13 族：PM 以 `from wf_cli.pitfalls import roster_for; roster_for('執行')` 取得 **13** 個族名，與報告 §5 的 13 行**逐字同序**。
- 實質性抽查兩條（⛔ 非全查）：
  - `F-執行-04`（rc=0 不等於成功）回應為「發現」且具體指向 `#8 rc=1` 與 `#4` 的交叉核對 ⇒ 實質。
  - `F-執行-10`（修過期引用會留下新的過期引用）回應具體（canonical `:670` 改指路時確認目標檔已存在、死連結掃描 0）⇒ 實質。
- ⚠️ `P-*`／`T-*` 兩層標「不適用：① 未生效，派工包未附」，執行者並自陳「若 ④ 要求三層齊全，本欄即不合格」。**PM 判：機制確實尚未生效（`stage-rules/*.md` §6 逐字「目標、尚未生效——機制生效於 W3′」）⇒ 本欄可收**，但派審時逐字轉給查核者判，⛔ PM 不代判。

### ② AC 與痛點對應可見性 — **不合格**

本報告以**裁定**為軸組織（§2 裁定 1／2／3／4），而卡面驗收是 **AC0–AC4 五條**。逐條核對報告內可見性：

| 卡面驗收 | 在本報告內的逐條證據 | 判 |
|---|---|---|
| AC0 四類輸出面範本全含「注意事項回應清冊」欄 | 僅 §3 F-5 側面提到「四檔全部改為逐字含該字串」 | ⛔ 無判準＋指令＋輸出 |
| AC1 舊→新逐檔對照＋各附 falsifier＋舊入口零引用 | 片段散在 §2 裁定 3／裁定 4 與 §6 D-7 | ⚠️ 不成一條 |
| AC2 對帳 set diff 逐項 disposition＋基線 hash | 僅 §6 D-5 提及 rows canonical sha256 `13141b5d…` | ⛔ 無 set diff 逐項 |
| AC3 L0 成形＋決議 §三之二指定句逐字 | 僅信封四第 6 項側面提到「L0 兩檔已同步」 | ⛔ 無逐字比對證據 |
| AC4 封閉五檔依 mapping 落地、CI 全綠 | CI 見信封三 #1–#3；封閉五檔落地無獨立證據列 | ⚠️ 半條 |

而本報告首行逐字宣告「**取代**先前 SHA `a776df52` 的那份」⇒ 前一份的逐 AC 證據被取代掉了，查核者若要逐 AC 對照，必須自行翻閱一份已被作者宣告取代的報告。**這正是 ② 要擋的形狀。**

**退回要求（⛔ PM 不代補）**：補一張 **AC0–AC4 逐條證據表**（每列：判準逐字／實跑指令／原始輸出／結論），或改寫首行為「與 `a776df52` 那份**合併閱讀**」並逐條指出各 AC 的證據落在哪一份的哪一節。⛔ 兩者擇一，不接受口頭涵蓋。

---

### PM 自身失誤登記（⛔ 非執行者之過，且它使 D-1 成立）

執行者 §6 **D-1** 逐字指出：卡面「驗證」四項之一「污染符 grep 零命中」在本卡開工當下就已 `rc=1`／3 筆，且三筆全在 `archive/`（授權外）⇒ 該驗證項在本卡射程內不可達。

**PM 實查確認該指控成立，且成因是 PM 自己**：

- `950b3e278371e948900dd381cd7b4e595882c6b0`（PM 的封存 PR #230 **之前**）：`pollution_check` **rc=0**、`unapproved_count` **0**、stale-entry **0**、`scanned_files` 16。
- `fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2`（#230 **之後**，僅差該一個 commit）：**rc=1**、`unapproved_count` **3**、stale-entry **2**、`scanned_files` 17。
- 病因：`pollution_check` 的語料是 `git diff --name-only --diff-filter=d <釘死 BASE_SHA f656a678…>` 的 post-image。PM 把 `w2a.md` 由 `docs/research/drafts/wave-specs/` 搬進 `archive/wave-specs/`，新路徑帶著既有污染符進入語料（3 筆：`行數自述`／`短版`／`最後核實`）；PM 同時刪除的 6 筆 inventory 條目中有 2 筆是 allowlist 指著的 ⇒ 「宣告 1 實得 0」的 stale-entry 2 筆。
- PM 當時只跑了 `prose_number_scan`（七項全零）**未跑 `pollution_check`**；且 `pollution_check` **不在 `.github/workflows/ci.yml`**（CI 只跑 `uv lock --check`／`pytest`／escalation replay）⇒ 該破壞是靜默的。
- ⚠️ 修法**不是**單純把核可改鍵到新路徑：PM 實查 `scripts/pollution-allowlist.json` 對舊路徑 `docs/research/drafts/wave-specs/w2a.md` 是 **0 命中**，即舊路徑本來就沒有核可條目。⇒ 任何「加條目讓它變綠」都是白名單自我擴張（P1-38 已踩過的坑），**PM ⛔ 不自行決定**，上呈需求方。

**在該問題解決之前，卡面驗證項「污染符 grep 零命中」不可達**，此事實逐字登記於此，⛔ 不歸因於執行者。

### PM 未驗（逐項）

1. 執行者 §2 裁定 1 的負控（塞裸數 ⇒ `unclassified 1`、移除 ⇒ 回零）PM **未重跑**——那是查核者職責。
2. 執行者 §2 裁定 3 的 load-bearing 負控（完整排除集 71／拿掉 `archive/` 74）PM **未重跑**。
3. `templates/` 下六份範本的內容是否滿足 AC0 逐字要求，PM **未讀**——初審⛔ 不判內容。
4. D-8／D-9（`find_conflicts` 完全相同字串才算撞）PM **未讀碼複驗**；D-9 逐字回答了 PM 開卡留痕的未驗 #1，PM 收下該回答但⛔ 未獨立驗證。


## Comment 5495179385 · 2026-09-01T14:04:14Z

## PM 收件初審（第二輪）— `WF-REDESIGN-W2B` 交付 `2c35d48d024acd8d39a4536daf9401acb2c208ea`

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`；發文者身分不等於作者身分。被審物由需求方於對話中轉交，作者為 session `907facce-8bfc-49d5-a749-752e52013f9e@Claude Code（claude-opus-5）`。

⛔ 初審**不判** `core_pain_resolved`、⛔ 不判 AC 實質、⛔ 不代修——只判「可不可以送查核」。

### 結果：**② 過 ⇒ 三項全過，可送查核**

執行者採 PM 給的第一個選項：另立 `AC0–AC4 逐條證據表`（每條含判準逐字／實跑指令／原始輸出／結論），並更正 `2c35d48` 報告首行的「取代」措辭——現逐字聲明逐 AC 證據的權威居所為該證據表，前兩份為過程紀錄、⛔ 無一作廢。**退回要求已滿足。**

### PM 獨立抽查（⛔ 非全查；在交付樹 `2c35d48d…` 上以 `git show`／`git ls-tree` 重跑，⛔ 未 checkout）

| 抽查項 | 執行者宣稱 | PM 重跑 | 判 |
|---|---|---|---|
| AC0-a 四檔逐字欄名命中數 | 2／2／2／3 | `dispatch-package` **2**、`delivery-report` **2**、`review-dispatch` **2**、`closeout-report` **3** | ✅ 逐字相符 |
| AC1-c `cli/src`＋`scripts` 逐字零改動 | `git diff --stat` 空輸出 | `git diff --stat fc8b966..2c35d48 -- cli/src scripts` ⇒ **空** | ✅ |
| AC2-a 基線 sha256 | `c1a1279…4bb68`，相符 True | `git show …:baseline-universe.json \| shasum -a 256` ⇒ **`c1a1279324f2b5f40421eaa0408314a1afadae2c374c0c98782f66510af4bb68`**，與卡面釘死值逐字相同 | ✅ |
| AC3 canonical 節次順序 | §1(7)／§2(44) 在 §0(59) 之前 | `## 1.` @7、`## 2.` @44、`## 0.` @59 | ✅ |
| AC3 指定句逐字命中 | README 1／AGENTS 1 | README.md **1**、AGENTS.md **1** | ✅ |
| AC4-a 封閉五檔 | 五檔全 `No such file` | 五檔逐一 `git cat-file -e` ⇒ 全部「已移除」 | ✅ |
| AC0 六份範本存在 | 六檔皆 exists、信封段數 4 | `git ls-tree templates/` 含 `closeout-report.md`／`review-dispatch.md`／`verdict.md`／`status-change-ruling.md`／`delivery-report.md`／`dispatch-package.md` | ✅ 存在性成立（段數未複驗，見未驗 3） |
| CI | 三步 rc 全 0 | `gh run list --commit 2c35d48d` ⇒ `success CI` | ✅ |

**⛔ 一處居所問題（⛔ 非退回理由，由 PM 處置）**：`AC-EVIDENCE-W2B.md` **不在交付樹內**（`git ls-tree -r 2c35d48d \| grep -i AC-EVIDENCE` ⇒ 無命中），只存在於對話。⇒ 依派審規則「報告全文同帖」，**由 PM 於派審時將該表全文一併貼入本卡**，使查核者不必向對話索取。

### 承前輪：PM 自身失誤仍未解，且它使卡面驗證項不可達

初審第一輪已登記：`pollution_check` 由 PM 的封存 commit（PR #230）打破——`950b3e2` rc=**0**／unapproved **0**／stale **0**；`fc8b966`（僅差該 commit）rc=**1**／unapproved **3**／stale **2**。卡面「驗證」四項之一「污染符 grep 零命中」因此**在本卡射程內不可達**（三筆全在 `archive/`，本卡授權外）。

**本輪新增的相關事實（執行者提出，PM 收下但⛔ 未獨立驗證）**：`scripts/pollution-allowlist.json` 這份 manifest **沒有 load-bearing 檢查**（`canonical_citation_scan` 的 `EXCLUSIONS` 有、它沒有）⇒ 搬檔使核可條目失效時，不會有任何東西喊。PM 補充一項已登記的相關敞口：`stale_entries` **不進 rc**（W2A 未驗清單第 10 項逐字登記在案）——本次那 2 筆 stale-entry 確實印出來了卻不影響判定。

⇒ 該問題的處置**歸屬未定**：`scripts/` ⛔ 不在 W2B 寫入集內。PM ⛔ 不自行決定修法（加 allowlist 條目即白名單自我擴張，P1-38 已踩過），上呈需求方裁定歸哪張卡。

### PM 未驗（逐項）

1. 執行者 §2 裁定 1 的負控（塞裸數 ⇒ `unclassified 1`、移除 ⇒ 回零）——查核者職責，PM 未重跑。
2. 執行者 AC1-d 的 71／74 load-bearing 負控——PM 未重跑。
3. 六份範本的**信封段數 4**（AC1-a 的 `grep -c '^## 信封[一二三四] · '`）——PM 只驗存在性，⛔ 未驗段數。
4. 六份範本的**內容**是否滿足 AC0／AC1 的實質要求——初審⛔ 不判內容。
5. D-8／D-9（`find_conflicts` 完全相同字串才算撞）——PM 未讀碼複驗。
6. AC2-b 的 §7 三表（36／0／23，未處置 0）——PM 未重跑。


## Comment 5495259953 · 2026-09-01T14:10:12Z

## PM 轉貼：`AC-EVIDENCE-W2B` — AC0–AC4 逐條證據表（逐 AC 證據的權威居所）

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`；發文者身分不等於作者身分。**下方為執行者 session `907facce-8bfc-49d5-a749-752e52013f9e@Claude Code（claude-opus-5）` 所寫，經需求方轉交，PM 逐字轉貼**（執行者無 GitHub 寫入通道）。⛔ PM 未改動其一字。

⚠️ **居所說明**：該表**不在交付樹內**（PM 實查 `git ls-tree -r 2c35d48d… | grep -i AC-EVIDENCE` ⇒ 零命中），原先只存在於對話。轉貼於此使查核者不必向需求方索取。

---

# AC0–AC4 逐條證據表 — `WF-REDESIGN-W2B`（執行者原文，逐字）

> 回應收件初審 ② 的退回要求（`issuecomment-5494957694`）。**本表即該項要求的「逐條證據表」**，
> 每條含：判準逐字（抄自卡面 `#220`）／實跑指令／原始輸出／結論。
>
> ⭐ **與先前兩份報告的關係，逐字說明**（取代初審點名的那句「取代」）：
> **本表是逐 AC 證據的權威居所。** `a776df52` 那份與 `2c35d48` 那份是**過程紀錄**
> （前者含裁定前的原始交付、後者含失誤登記與裁定落地），⛔ 查核者不需要為了逐 AC 對照去翻它們。
> ⛔ 沒有任何一份被宣告作廢——`2c35d48` 那份首行的「取代」二字僅指**信封與失誤登記**兩節的較新版本，
> 措辭不精確，於此更正。
>
> 全部在 worktree `/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-redesign-w2b-templates-be3b1b`、
> 於 **`2c35d48d024acd8d39a4536daf9401acb2c208ea`** 上跑，`git status --porcelain` 0 行。rc 分開取、⛔ 未接管線、⛔ 未截斷。

## AC0

**判準逐字**：（P1-35 範本 owner，四類輸出面）dispatch-package／delivery-report／review-dispatch／**closeout-report（新檔 templates/closeout-report.md，七段結案報告——falsifier 同新五檔）**全含「注意事項回應清冊」欄（逐條編號三值）

### AC0-a · 四類輸出面各含該欄（逐字）

```bash
for f in dispatch-package delivery-report review-dispatch closeout-report; do
  printf "%-20s %s\n" "$f" "$(grep -c 注意事項回應清冊 templates/$f.md)"
done
```

```text
dispatch-package     2
delivery-report      2
review-dispatch      2
closeout-report      3
```

### AC0-b · 逐條**編號**＋**三值**

```bash
grep -n "已遵循.*不適用.*發現" templates/dispatch-package.md templates/delivery-report.md \
  templates/review-dispatch.md templates/closeout-report.md
grep -no "F-<階段>-NN\|F-<階段>-01\|P-派審-0[0-9]\|P-結案-0[0-9]" templates/dispatch-package.md \
  templates/delivery-report.md templates/review-dispatch.md templates/closeout-report.md
```

```text
templates/dispatch-package.md:57:- ③ 交回時必附**注意事項回應清冊**：對上列編號**逐條**回應，三值＝`已遵循`／`不適用：<原因>`／`發現：<處置>`。
templates/closeout-report.md:85:> …發出前**逐條編號**回應，三值＝`已遵循`／`不適用：<原因>`／`發現：<處置>`。
templates/delivery-report.md:75:| `F-<階段>-01` | `已遵循`／`不適用：<原因>`／`發現：<處置>` |
templates/review-dispatch.md:89:> …發出前**逐條編號**回應，三值＝`已遵循`／`不適用：<原因>`／`發現：<處置>`；⛔ 不得只有執行者有清冊而 PM 沒有。
templates/review-dispatch.md:93:| `P-派審-01` 信封四段齊全 | `已遵循`／`不適用：<原因>`／`發現：<處置>` |
---
templates/dispatch-package.md:56:F-<階段>-NN
templates/delivery-report.md:71:F-<階段>-NN
templates/delivery-report.md:75:F-<階段>-01
templates/closeout-report.md:89-94:P-結案-01 … P-結案-06
templates/review-dispatch.md:93-97:P-派審-01 … P-派審-05
```

### AC0-c · `closeout-report.md` 新檔＋七段

```bash
ls -l templates/closeout-report.md
grep -n "^## [1-7]\. " templates/closeout-report.md
```

```text
-rw-r--r--@ 1 ruanruan  staff  4750 Sep  1 19:48 templates/closeout-report.md
41:## 1. 痛點 → 處置
45:## 2. 裁決摘要（含 blocking 清零）
50:## 3. merge SHA ＋ CI 指標
55:## 4. 四道停下條件逐項
64:## 5. 失誤登記與未驗清單（**逐字轉錄**）
71:## 6. 清單收斂核對
77:## 7. 翻案把手
```

**結論：AC0 過。** 四類輸出面各含逐字欄名，編號（`F-<階段>-NN`／`P-派審-NN`／`P-結案-NN`）與三值皆在；`closeout-report.md` 為新檔且七段齊全，其信封 falsifier 與新五檔同（見 AC1-a）。
⚠️ **未驗**：三值的**值域是否被機械強制**——⛔ 沒有，`stage-rules/*.md` §6 逐字「目標、尚未生效——機制生效於 W3′」。範本寫的是應然。

## AC1

**判準逐字**：（P1-15 封閉 mapping）舊 → 新逐檔對照，各附 falsifier：…新五檔…各以「檔案存在＋含信封四段標題」為存在性判準。**（P1-15 補）templates/review-prompt.md → 改寫保留**（wfcli review 的結構化輸出契約，碼引用 2026-08-30 量測 6 處不動；改寫使其與 verdict.md 分工：前者 schema、後者人讀範本）；被移除各舊檔以 git grep 檔名於 post-image 驗「舊入口零引用」（mapping 文件自身除外）

### AC1-a · 新六檔存在性＝檔案存在＋含信封四段標題

```bash
for f in dispatch-package delivery-report review-dispatch verdict status-change-ruling closeout-report; do
  n=$(grep -c '^## 信封[一二三四] · ' "templates/$f.md")
  test -f "templates/$f.md" && e=exists || e=MISSING
  [ "$n" = 4 ] && echo "OK   $f  ($e, 信封段數 $n)" || echo "FAIL $f  ($e, 信封段數 $n)"
done
```

```text
OK   dispatch-package  (exists, 信封段數 4)
OK   delivery-report  (exists, 信封段數 4)
OK   review-dispatch  (exists, 信封段數 4)
OK   verdict  (exists, 信封段數 4)
OK   status-change-ruling  (exists, 信封段數 4)
OK   closeout-report  (exists, 信封段數 4)
```

⚠️ **四段標題的字面由本卡推導**：決議 §六列的是五要素，其中「實際模型 vs 建議層級」逐字是**行**（`pm-conduct` 一亦然）⇒ 五扣一＝四段。對工作樹＋**全部 634 個 commit** 的 `*.md` 窮舉搜「信封」，**⛔ 無任何權威枚舉**。推導寫在 `templates/handoff-contract.md` §3.3。**這是 PM 裁定候補（報告 §6 D-3）。**

### AC1-b · 舊 → 新逐檔對照，各附 falsifier

```bash
sed -n '/## 1. 被移除的五檔/,/⚠️ \*\*移除 ≠ 修復/p' templates/template-migration-map.md
```

輸出為一張五列表，欄位＝`舊檔｜處置｜承接者｜falsifier（什麼觀察會讓本列不成立）`，五列逐字為：
`templates/tasks-card.md`（承接＝卡面 fenced JSON，**今天就在跑**）／`templates/bug-card.md`（承接＝`stage-rules/defect-path.md` 一）／
`templates/bug-workflow.md`（承接＝`stage-rules/defect-path.md` 二／三）／`templates/initiative-card.md`（承接＝canonical §3 ＋ `baseline-cascade.md`）／
`templates/TASKS.md`（承接＝狀態面）。**每列都有自己的 falsifier**。

### AC1-c · `review-prompt.md` 改寫保留、節次不動、碼引用 6 處不動

```bash
grep -c '^## [1-6]\. ' templates/review-prompt.md
for k in core_pain_resolved review_result self_run findings; do
  grep -q "^$k:" templates/review-prompt.md && echo "OK $k" || echo "FAIL $k"; done
git grep -l --fixed-strings -- "review-prompt.md" -- cli/src scripts | sort
git diff --stat fc8b966..HEAD -- cli/src scripts
```

```text
6
OK core_pain_resolved
OK review_result
OK self_run
OK findings
---
cli/src/wf_cli/card.py
cli/src/wf_cli/commands/amend_cmd.py
cli/src/wf_cli/commands/review_cmd.py
cli/src/wf_cli/review.py
cli/src/wf_cli/validation.py
scripts/replay_escalation_rules.py
---
（git diff --stat 空輸出）
```

⭐ **碼引用檔集合恰為 6 個**，且 `git diff fc8b966..HEAD -- cli/src scripts` **空** ⇒ 那 6 處**逐字零改動**。
分工寫在 `review-prompt.md` 檔頭表格：本檔 §5＝schema（機器面）／`verdict.md`＝人讀範本／`review-dispatch.md`＝派審信封。

### AC1-d · 舊入口零引用

```bash
for f in tasks-card.md bug-card.md bug-workflow.md initiative-card.md templates/TASKS.md; do
  git grep -n --fixed-strings -- "$f"
done \
  | grep -Ev '^templates/template-migration-map\.md:' \
  | grep -Ev '^archive/' \
  | grep -Ev '^docs/research/drafts/wave-specs/w2b\.md:' \
  | grep -Ev '^docs/research/drafts/wave-specs/baseline-universe\.json:' \
  | cut -d: -f1,2 | sort -u | wc -l
sed -n '/### 3.2 A · 現行入口殘留/,/### 3.3/p' templates/template-migration-map.md
```

```text
      71
### 3.2 A · 現行入口殘留（授權內）：0

（無）
```

load-bearing 負控（拿掉 `archive/` 那條）⇒ **74**（＞71 ⇒ 該排除項確實在擋東西，⛔ 非死條目）。

**結論：AC1 過（帶兩個明說的保留）。**
① 四段標題字面為本卡推導，⛔ 無權威枚舉（D-3）。
② 「零引用」的判準是 **A ＝ 0**（現行入口殘留），⛔ 不是「`git grep` 總命中為 0」——卡面同句指定的量法在排除集後仍得 **71**，其中 **39 由 AC2 自己強制產生**（§7 逐項處置表 36 ＋ 對帳器合成語料 3）。**AC1 判準與其量法是否互斥，依需求方裁定 4 待另裁**（報告 §6 D-7）。

## AC2

**判準逐字**：（P1-19＋P1-32）**基線已釘（P1-32 canonical 序列化）**：`baseline-universe.json`……sha256=`c1a1279324f2b5f40421eaa0408314a1afadae2c374c0c98782f66510af4bb68`……W2B 於 W2A＋W2B merge result 以同指令產同 schema artifact 做 **set diff**——每個 removed／added／changed symbol 逐項 disposition（count 只作摘要，集合與 hash 才是基線）；`--check` 與 33 專測再對 merge result 執行，⛔ 不得只改登記讓綠燈恢復

### AC2-a · 基線 sha256 複驗（PM 開卡時列為「執行者第一件事」）

```python
import hashlib
raw = open("docs/research/drafts/wave-specs/baseline-universe.json","rb").read()
hashlib.sha256(raw).hexdigest()
```

```text
  c1a1279324f2b5f40421eaa0408314a1afadae2c374c0c98782f66510af4bb68
  卡面釘死值           c1a1279324f2b5f40421eaa0408314a1afadae2c374c0c98782f66510af4bb68
  相符： True
```

⭐ **口徑釐清（卡面未指明，於此釘住）**：`c1a1279…` ＝**全檔位元組**的 sha256，而全檔位元組恰等於卡面所述管線套在**含 `_meta` 的整份文件**上的輸出。⛔ **不是** rows-only——rows-only 為 `d13ba6c04f5954295c705f515dbc1f242bd513d00da2eb708777b940c98d45cc`。四個候選口徑實跑比對後只有這一個命中。

### AC2-b · merge result 的同 schema artifact 與 set diff 逐項 disposition

```text
  基線 rows         d13ba6c04f5954295c705f515dbc1f242bd513d00da2eb708777b940c98d45cc
  merge result rows 13141b5d9b6e7188818d9df12a59ecfd42b43cb8f1a68af8b800ef69387a4421
```

⚠️ 跨 HEAD 比對用 **rows** hash，⛔ 不用全檔 hash——`_meta.source_sha` 每次產生都不同。理由與重跑片段寫在 `docs/CONTRACT_TOOL_RECONCILE.md` §7.0。

```bash
grep -n "^### 7\.[123] " docs/CONTRACT_TOOL_RECONCILE.md
# 各表資料列數與「未處置」筆數（機械計）
```

```text
587:### 7.1 removed（36）——符號離開 universe      → 資料列 36　其中未處置 0
628:### 7.2 added（0）——新符號進 universe         → 資料列 0　其中未處置 0
632:### 7.3 changed（23）——同 key、canonical row 不同 → 資料列 23　其中未處置 0
```

表頭與樣本列：

```text
| kind | 符號 | 基線判定 | 基線出處檔 | 處置 |
|---|---|---|---|---|
| `card_field` | `DB` | `ok` | `templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
| `card_field` | `Design` | `absent` | `templates/initiative-card.md`<br>`templates/tasks-card.md` | `從契約移除`：唯一出處為本卡移除的範本 |
```

**每一列都有處置，未處置 0。** `added=0` 是刻意的（新範本沿用既有符號、emoji 後留空白）；`changed 23` 全部只動 `doc_hits`／`mentions`，**`verdict` 零變動** ⇒ 全判 `錨點漂移`。

### AC2-c · `--check` 與 33 專測在 merge result 上執行

```bash
python3 scripts/contract_tool_reconcile.py --check
cd cli && uv run --frozen pytest tests/test_contract_tool_reconcile.py -q
```

```text
[reconcile] OK：40 個缺口全部有登記處置，判定一致。
  rc=0
---
33 passed in 2.49s
```

⭐ **⛔ 未以「只改登記讓綠燈恢復」達成**：登記由 61 降為 40，**刪掉的每一筆都對應一個已離開 universe 的符號，且逐筆列在 §7.1**；新增的兩筆對應 W2A 已產生但先前未登記的守衛缺口。

**結論：AC2 過。**
⚠️ **未驗**：本卡跑的是**分支頭**，合併結果上重跑歸查核者（`reviewer-conduct` 三）。
⚠️ **未落檔**：merge result 的 artifact **沒有可寫的居所**（`docs/` 不在寫入集，僅 `docs/CONTRACT_TOOL_RECONCILE.md`）⇒ 以 rows hash ＋ §7.0 重跑片段代替（報告 §6 D-5）。

## AC3

**判準逐字**：L0 成形：AGENTS／README 指向「canonical 前兩節＋專案心智模型，其餘用查的」，並含決議 §三之二指定句逐字：「**stage-rules/＝八份 SOP，① 印給你、③ 逐條回**」

```bash
grep -c 'stage-rules/＝八份 SOP，① 印給你、③ 逐條回' README.md AGENTS.md
grep -n "L0 · " README.md AGENTS.md
grep -n "§1 角色與所有權\|§2 不可違反的規則\|其餘用查的" README.md AGENTS.md
grep -n "^## " AI_WORKFLOW.md | head -4
```

```text
README.md:1
AGENTS.md:1
---
AGENTS.md:5:## L0 · 進來先讀這三塊，其餘用查的
README.md:5:## L0 · 三分鐘上手（讀這裡就好，其餘用查的）
---
README.md:9:1. [`AI_WORKFLOW.md`](AI_WORKFLOW.md) **§1 角色與所有權**——誰規劃、誰執行、誰查核…
README.md:10:2. [`AI_WORKFLOW.md`](AI_WORKFLOW.md) **§2 不可違反的規則**——踩到就是紅線的那幾條。
README.md:13:§1／§2 就排在 §0 之前…**其餘一律用查的**——canonical 是查詢對象，⛔ 不是入門讀物。
AGENTS.md:9:1. [`AI_WORKFLOW.md`](AI_WORKFLOW.md) **§1 角色與所有權**；
AGENTS.md:10:2. [`AI_WORKFLOW.md`](AI_WORKFLOW.md) **§2 不可違反的規則**；
---
7:## 1. 角色與所有權
44:## 2. 不可違反的規則
59:## 0. 分類與狀態
626:## 3. 任務流程
```

**三要素逐一對照**：
- 「canonical 前兩節」＝ §1 角色與所有權 ＋ §2 不可違反的規則，兩檔各列為第 1／2 點；canonical 實查 §1(7)／§2(44) 確實排在 §0(59) **之前** ✅
- 「專案心智模型」＝ 兩檔各有「一分鐘心智模型」節（第 3 點）✅
- 「其餘用查的」＝ 兩檔標題逐字含之，並各附 `gh project item-list` 與 `ls` 兩條查詢指令 ✅
- 指定句**逐字各 1 命中** ✅

**結論：AC3 過。**
⚠️ 兩檔就地標明「① 印給你」的**機械列印尚未生效**（機制歸 W3′，沿 canonical §0.1 先例）——指定句逐字帶入，但⛔ 未假裝機制已存在。

## AC4

**判準逐字**：封閉五檔依 mapping 落地，CI 全綠

### AC4-a · 封閉五檔落地

```bash
ls templates/tasks-card.md templates/bug-card.md templates/bug-workflow.md \
   templates/initiative-card.md templates/TASKS.md
git log --diff-filter=D --name-only --format='%h' fc8b966..HEAD -- templates/
```

```text
ls: templates/TASKS.md: No such file or directory
ls: templates/bug-card.md: No such file or directory
ls: templates/bug-workflow.md: No such file or directory
ls: templates/initiative-card.md: No such file or directory
ls: templates/tasks-card.md: No such file or directory
---
41a0697
templates/TASKS.md
templates/bug-card.md
templates/bug-workflow.md
templates/initiative-card.md
templates/tasks-card.md
```

**五檔全部不存在，且刪除動作可追溯至單一 commit `41a0697`。** 對照 mapping §1 的五列 ⇒ 逐檔相符（⛔ 非六檔）。

### AC4-b · CI 全綠（`.github/workflows/ci.yml` 三步逐條）

```bash
cd cli && uv lock --check
cd cli && uv run --frozen pytest -q
cd cli && uv run --no-project --python 3.12 ../scripts/replay_escalation_rules.py
```

```text
Resolved 7 packages in 4ms          rc=0
1617 passed, 1 skipped in 64.00s    rc=0
114/114 通過                         rc=0
```

**結論：AC4 過。**

## 卡面「驗證」四項（⛔ 非 AC，但卡面另列，一併交代）

| 驗證項（逐字） | 結果 |
|---|---|
| pytest 全綠 | ✅ `1617 passed, 1 skipped`、rc=0 |
| **污染符 grep 零命中** | ❌ `rc=1`／`unapproved 32`。**在本卡射程內不可達**——PM 已於初審自行實查確認：`950b3e2` 時 rc=0／0 筆，`fc8b966`（僅差 PM 的封存 commit）rc=1／3 筆，三筆全在 `archive/`（本卡授權外）。逐筆歸因：既有文字 24／本卡新寫 8（8 筆全在機械產生表列內）；只掃本卡新寫 11 檔的負控 ⇒ **0**，且同一支工具對探針檔會響 **2** |
| ⭐ 派工包範本可實際產出一份（對 W3′ 的派工試打） | ✅ 已產出（另附檔）。⚠️ `#221` 實查為 `[清單] W3′`、`state=OPEN` ⇒ **它是清單項⛔ 不是卡**，故試打逐字標明「試打、W3′ 尚未開卡、⛔ 非真實派工」，卡才有的九個格標 `<開卡時填>`。⭐ 試打抓到一個範本缺口：`dispatch-package.md` **沒有「限定條目的資源宣告」欄位**（報告 §6 D-8） |
| 對帳 artifact 之 sha256 與已釘基線比對，set diff 逐項 disposition | ✅ 見 AC2-a／AC2-b |


## Comment 5495281297 · 2026-09-01T14:11:45Z

## 派審：`WF-REDESIGN-W2B`（#220）執行審 **R1** —— 配套與 contract templates（T3，⭐ 含 canonical 寫入 ⇒ 跨家族）

（⚠️ 需求方轉貼時，本詞之後同帖接**交付報告全文**；逐 AC 證據另見本卡 `issuecomment-5495259953`。）

### ① 被審物

- 分支 `claude/wf-redesign-w2b-templates-be3b1b` @ **`2c35d48d024acd8d39a4536daf9401acb2c208ea`**（已推 origin、⛔ 未 merge）
- **派審基線 ＝ `git merge-base origin/main 2c35d48d…` ＝ `fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2`**（實跑取得並釘死字面，⛔ 非抄 origin/main）
- 卡：https://github.com/ruan6047/ai-workflow/issues/220 —— 規格住卡面 body；逐 AC 證據的權威居所＝本卡 `issuecomment-5495259953`
- spec 基線：`ai-workflow 93bb8c086f0cf8870537390511b5f0aa2d037c97`
- 本輪 commit 三筆：`0607f5d`（裁定 1+3+4＋自陳五項）／**`6e8c4f2`（⭐ canonical 單獨 commit）**／`2c35d48`（修 §3.5 壞掉的指令）

### ② 前輪與 root_cause

R1 為執行審**首輪**，⛔ 無前輪 findings。但本卡在執行階段先出過一份**阻塞發現**（`issuecomment-5494257615`），需求方裁定四項（`issuecomment-5494350916`）：

| 裁定 | 內容 | root_cause |
|---|---|---|
| 1 | 甲：擴權 `stage-rules/` 補缺陷處理承接條文 | 移除 `bug-workflow.md` 後承接條文無居所 |
| 2 | 甲：擴權 `ADOPTION.md`＋`AI_WORKFLOW.md`，限定註記／指路更正，三執行條件 | 採用指南與 canonical 兩處指向已移除檔 |
| 3 | 收下類別、退回形狀：`archive/` 排除成立；`docs/research/` ⛔ 不得整目錄排除，改具名兩檔 | 執行者自行擴大排除集＝判準變更 |
| 4 | 數字待重述，⛔ 不背書 98／80／47 | 逐名 `git grep -c` 相加會重複計數 |

⭐ **請重點查裁定落地是否逐條成立**，特別是裁定 2 的三個執行條件（canonical 拆獨立 commit／跨家族聲明／註記形狀無死連結）。

### ③ PM 身分自述

PM：GitHub `ruan6047`（代理發文）；Claude Code；模型 `claude-fable-5`；session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

### ④ 受派者模型行

卡面建議查核 **主力型＋獨立**。⭐ **本輪要求提高為跨模型家族（Codex）**——依裁定 2 條件 2 逐字：本卡對 canonical（`AI_WORKFLOW.md`）的寫入需跨模型家族查核，其強度高於本卡 T3 預設。獨立性要求疊加於層級之上，⛔ 非第四個層級。實際模型以你的裁決自述為準。

### ⑤ PM 未驗（三分類）

**驗不了**
1. 六份範本的**內容**是否滿足 AC0／AC1 的實質要求——PM 初審⛔ 不判內容，這是你的本職。
2. `stage-rules/defect-path.md` 的條文內容對不對——裁定 1 逐字「條文內容由查核者判」。

**沒去驗**
3. 六份範本的信封段數 4（AC1-a 的 `grep -c '^## 信封[一二三四] · '`）——PM 只驗了六檔**存在性**。
4. 執行者 AC1-d 的 71／74 load-bearing 負控。
5. 執行者裁定 1 的負控（塞裸數 ⇒ `unclassified 1`／移除 ⇒ 回零）。
6. AC2-b 的 §7 三表（36／0／23，未處置 0）。
7. D-8／D-9（`find_conflicts` 完全相同字串才算撞）——PM 未讀碼複驗，但 D-9 逐字回答了 PM 開卡留痕的未驗 #1，PM 收下該回答。

**刻意不驗**
8. 合併結果上重跑守衛——`reviewer-conduct` 三，你的職責。
9. 跨家族裁決含身分自述——審核階段本身。

### ⑥ PM 自審紀錄（指令＋原始輸出，⛔ 不載結論字樣）

```
git merge-base origin/main 2c35d48d024acd8d39a4536daf9401acb2c208ea
  → fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2

git diff --stat fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2..2c35d48d… -- cli/src scripts
  → （空輸出）

git show 2c35d48d…:docs/research/drafts/wave-specs/baseline-universe.json | shasum -a 256
  → c1a1279324f2b5f40421eaa0408314a1afadae2c374c0c98782f66510af4bb68

git show 2c35d48d…:AI_WORKFLOW.md | grep -n "^## " | head -4
  → 7:## 1. 角色與所有權 / 44:## 2. 不可違反的規則 / 59:## 0. 分類與狀態 / 626:## 3. 任務流程

for f in README.md AGENTS.md: git show 2c35d48d…:$f | grep -c '<決議指定句>'
  → README.md 1 / AGENTS.md 1

for f in dispatch-package delivery-report review-dispatch closeout-report:
  git show 2c35d48d…:templates/$f.md | grep -c 注意事項回應清冊
  → 2 / 2 / 2 / 3

git show --stat --format='' 6e8c4f2
  → AI_WORKFLOW.md | 4 ++--   1 file changed, 2 insertions(+), 2 deletions(-)

for c in 0607f5d 6e8c4f2 2c35d48: git log -1 --format='%B' $c | git interpret-trailers --parse
  → 三者皆 4 欄：Requested-by / Planned-by / Implemented-by / Co-authored-by

git ls-tree -r --name-only 2c35d48d… | grep -i AC-EVIDENCE
  → （零命中）

gh run list --commit 2c35d48d024acd8d39a4536daf9401acb2c208ea
  → success  CI  2c35d48d

wfcli handoff …--next-stage implementation…（補記 需求→執行）
  → rc=0；踩坑族清冊（離開「需求」，8 族）已收下：已檢查 4／不適用 0／發現 4

wfcli handoff …--next-stage review…
  → rc=0；踩坑族清冊（離開「執行」，13 族）已收下：已檢查 1／不適用 1／發現 11
  → 已交接 WF-REDESIGN-W2B → Codex@OpenAI（狀態=🔍待查核，SHA=2c35d48d…）
```

### ⑦ 失誤登記（PM 側，逐字）

1. **PM 打破了 `pollution_check`，而卡面驗證項因此不可達。** PM 的封存 PR #230 把 `w2a.md` 搬進 `archive/` 並刪除 6 筆 inventory 條目。實測：`950b3e2`（該 commit 前）rc=**0**／`unapproved_count` **0**／stale-entry **0**；`fc8b966`（僅差該 commit）rc=**1**／unapproved **3**／stale **2**。PM 當時只跑 `prose_number_scan` 未跑 `pollution_check`，而後者**不在 `.github/workflows/ci.yml`** ⇒ 破壞是靜默的。⇒ 卡面「驗證」四項之一「污染符 grep 零命中」**在本卡射程內不可達**，⛔ 不歸因執行者。歸屬與修法待需求方裁定（`scripts/` ⛔ 不在本卡寫入集）。
2. **PM 首次派審被閘門拒收（rc=2）**：`assign` 只寫交付狀態不寫階段欄，階段欄停留「需求」，閘門據此索取 8 族清冊而 PM 送了 13 族。已以兩段 handoff 補記正向轉移後重送。⛔ 非執行者之過。
3. **PM 初審第一輪把 ② 判為不合格**（報告以裁定為軸、逐 AC 證據不可見），執行者補表後第二輪過。此為流程內的正常退回，逐字登記於此以免第二輪的「過」被讀成一次就過。

### ⑧ 裁決寫回（你有 wfcli 通道，用結構化事件⛔ 非自由文字留言）

先 `--validate-only` 自檢格式，再正式跑：

```
cd /Users/ruanruan/Dev/ai-workflow/cli
uv run wfcli review WF-REDESIGN-W2B --owner ruan6047 --project 4 --repo ruan6047/ai-workflow \
  --input <你的查核報告.yaml> --source-sha 2c35d48d024acd8d39a4536daf9401acb2c208ea \
  --reviewer "Codex@OpenAI（<實際模型>，session <你的 session id>）"
```

yaml 形狀＝`templates/review-prompt.md` §5（`core_pain_resolved`／`review_result`／`self_run` 必填；findings 每筆**八欄全給**：`finding_id`（形如 `WF-REDESIGN-W2B-R1-1`）／`severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id`／`evidence`／`disposition`）。**沒有 `self_run` 的 APPROVE 無效。**

⚠️ 正式跑時 stderr 可能印 `preflight_basis_binding=structurally-unavailable` 警示——已知且已登記的 schema 落差（`docs/CONSUMER_CONFORMANCE.md`），⛔ 非錯誤、⛔ 不用處理；寫入成功以「已寫入裁決…（交付狀態=…）」那行為準。
⚠️ **wfcli 的拒絕訊息走 stderr**：⛔ 不要把 stderr 併進 stdout 之後再截斷，否則裁決被吃掉還以為成功。

規則：⛔ 不改檔、⛔ 不 merge、⛔ 不動 review 以外的看板欄位；若 wfcli 失敗，改以留言貼結構化區塊（⛔ 無 marker 前綴）由 PM 轉錄。

### 請重點查（⛔ 不限於此）

1. **AC0–AC4 逐條**（以 `issuecomment-5495259953` 為準獨立重跑，⛔ 不採信執行者輸出）。
2. ⭐ **canonical 寫入 `6e8c4f2`**：是否真的只有註記／指路更正、⛔ 有無改動任何規則語意。這是本輪提高查核強度的唯一理由。
3. **`stage-rules/defect-path.md` 的條文內容**——裁定 1 明示歸你判：判準夠不夠、有沒有漏掉 `bug-workflow.md` 的某條、「⛔ 沒有 bug 專屬卡種」與「`BUGS.md` 退位」兩條**本卡新立**的規則該不該成立。
4. **AC1 的兩個保留**：四段信封標題字面由本卡推導（無權威枚舉，D-3）；「零引用」判準取 A=0 而非 grep 總命中 0（排除集後仍 71，其中 39 由 AC2 自己產生）——**AC1 與 AC2 是否互斥、若互斥怎麼收，需求方裁定 4 明示待另裁，請給你的判斷但⛔ 不必代裁**。
5. **裁定 3 的排除集形狀**：四項具名排除是否各自 load-bearing、理由是否成立。
6. **九項待裁（報告 §6 D-1…D-9）**，其中 D-8／D-9 是本輪由派工試打新長出來的。
7. 失誤登記 13 筆中**已外洩的 4 筆**（F-6／F-7／F-8／F-9／F-10）之補救是否確實落地。


## Comment 5495441878 · 2026-09-01T14:23:38Z

<!-- wf-review-event:v1 card_id=WF-REDESIGN-W2B source_sha=2c35d48d024acd8d39a4536daf9401acb2c208ea attempt_id=WF-REDESIGN-W2B-e0-2c35d48d024acd8d39a4536daf9401acb2c208ea -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-REDESIGN-W2B`　attempt_id：`WF-REDESIGN-W2B-e0-2c35d48d024acd8d39a4536daf9401acb2c208ea`
- 查核者：Codex@OpenAI（gpt-5.6-sol，session 01a05d50-689a-70b3-862d-b9aae4e1a4d4）　escalation_epoch：0
- source_sha：`2c35d48d024acd8d39a4536daf9401acb2c208ea`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-09-01T22:23:35+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git status --porcelain=v1; git merge-base origin/main 2c35d48d024acd8d39a4536daf9401acb2c208ea; git merge-tree --write-tree origin/main 2c35d48d024acd8d39a4536daf9401acb2c208ea; git rev-parse 2c35d48d024acd8d39a4536daf9401acb2c208ea^{tree}`
  - HEAD=2c35d48d024acd8d39a4536daf9401acb2c208ea；status 0 行；merge-base=fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2；merge-result tree 與 source tree 都是 218b2aceadad18c2cc4928081c9056aee0954558。
- `cd cli && uv run --frozen pytest -q`
  - 1617 passed, 1 skipped in 75.74s；rc=0。
- `cd cli && uv run --frozen pytest tests/test_contract_tool_reconcile.py -q`
  - 33 passed in 3.22s；rc=0。
- `python3 scripts/contract_tool_reconcile.py --check; python3 scripts/prose_number_scan.py; python3 scripts/qualified_pointer_scan.py; python3 scripts/canonical_citation_scan.py`
  - reconcile rc=0、40 個缺口；prose_number_scan rc=0、unclassified/dead/invalid/mismatch 全 0；qualified_pointer 紅 0；canonical_citation 命中 0。
- `cd cli && uv lock --check; uv run --no-project --python 3.12 ../scripts/replay_escalation_rules.py`
  - uv lock rc=0；replay 114/114 通過、rc=0。
- `以 baseline-universe.json 與 contract_tool_reconcile.py --format json 獨立重算 key set、row hash，並將 identity set 與 docs/CONTRACT_TOOL_RECONCILE.md §7 三表比對`
  - baseline 全檔 c1a1279324f2b5f40421eaa0408314a1afadae2c374c0c98782f66510af4bb68；rows d13ba6c04f5954295c705f515dbc1f242bd513d00da2eb708777b940c98d45cc → 13141b5d9b6e7188818d9df12a59ecfd42b43cb8f1a68af8b800ef69387a4421；86→50、removed=36、added=0、changed=23、verdict_changed=0；文件 missing/extra 都為 0。
- `對六份範本跑 grep -c '^## 信封[一二三四] · '，並對四類輸出面跑 grep -c 注意事項回應清冊`
  - 六檔信封段數全為 4；dispatch/delivery/review-dispatch/closeout 的清冊命中為 2/2/2/3；closeout §1–§7 為 7 段；review-prompt §1–§6 為 6 段。
- `對四個 exclusion 各拿掉一次，重算舊檔名的唯一 file-line 總數`
  - 完整排除集 71；拿掉 mapping/archive/w2b.md/baseline-universe.json 分別為 77/74/73/72，故各自新增 6/3/2/1 個唯一 file-line，四項皆 load-bearing。
- `git show --word-diff=plain 6e8c4f2 -- AI_WORKFLOW.md；並逐行對照 fc8b966 與 2c35d48 的 canonical 規則句`
  - 只改兩行：§3 保留原 T1/T2/T3 分級句、改指 defect-path；§6 保留原留痕段語意、把兩個已移除範本改成就地註記與 migration-map 指路。
- `python3 scripts/pollution_check.py`
  - rc=1；unapproved_count=32、stale-entry 2；其中 archive/wave-specs/w2a.md 有 3 筆基線既存命中。

### findings（8，其中 blocking 6）

- **WF-REDESIGN-W2B-R1-1**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`canonical-standard-clause-truncated`
  - evidence：templates/dispatch-package.md:3 宣稱 §4 六條由 canonical §6.1 逐字帶入、不得省略或改寫；但該檔:66 只寫「一律本地 rebase＋force-with-lease」，漏掉 AI_WORKFLOW.md:831 的狹義例外、兩個必要條件、trailer 對價與「無機械執行者」限制。這會讓合法基線更新情境收到與 canonical 相反的派工指令。
  - disposition：把 canonical §6.1 第 3 條的完整語意逐字帶回 dispatch-package §4；至少不可省略狹義例外的兩個合取條件、trailer 要求與人工複核限制，並重跑 W3′ 派工試打。
- **WF-REDESIGN-W2B-R1-2**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`migration-exclusion-policy-diverged`
  - evidence：templates/template-migration-map.md:76-80 仍宣告「母體排除三項」且整個 docs/research/ 都排除；同檔:104-113 又依裁定 3 宣告不得整目錄排除，改成 mapping、archive、w2b.md、baseline-universe.json 四項。兩段是互斥的規則來源，讀者無法判定應跑哪一套。
  - disposition：刪除或改寫 :76-80 的舊三項政策，使全文只有裁定 3 的四個具名排除；§3.5 指令、理由表與分類說明須引用同一集合。
- **WF-REDESIGN-W2B-R1-3**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`unique-line-count-reported-as-occurrences`
  - evidence：templates/template-migration-map.md:98 宣告本節單位為唯一 file-line，但 :110-113 的 exclusion 命中數寫 10/4/10/4；獨立以該單位重跑，四項實際 load-bearing 增量為 6/3/2/1。10/4/10/4 是 occurrence 口徑，重現了裁定 4 要消除的計數口徑混用。
  - disposition：依本節宣告的唯一 file-line 單位改為 6/3/2/1；若需保留 occurrence 數，須另欄明示單位，且不得拿它當 §3.5 的 line-count 負控輸出。
- **WF-REDESIGN-W2B-R1-4**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`defect-path-t1-card-flow-contradiction`
  - evidence：stage-rules/defect-path.md:25 無條件宣告所有缺陷都走待審清單項→一般卡；同檔:59 又宣告 T1 只留 commit、不得開卡。後者也才與已移除 bug-workflow 的 T1 留痕及 canonical 的 T0/T1 直通規則一致。
  - disposition：把第一節的清單→一般卡路徑明確限縮為 T2 以上，並在同一節就地指出 T1 依第三節直接 commit；「沒有 bug 專屬卡種」可保留。
- **WF-REDESIGN-W2B-R1-5**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`bugs-ledger-retirement-conflicts-adoption`
  - evidence：stage-rules/defect-path.md:61 新立「BUGS.md 為凍結歷史、不得新增」；ADOPTION.md:18 卻仍命令新專案「另起一份 docs/BUGS.md」。ADOPTION 只加了 bug-card 已移除的註記，未撤回建立 ledger 的規則，因此採用者同時收到建立與禁止新增兩個相反指令。
  - disposition：本卡內先撤回 BUGS.md 退位的新規則，或由需求方另行裁定並授權同步改寫 ADOPTION 的規則語意；不得以「範本被移除」自行推出 ledger 也退位。
- **WF-REDESIGN-W2B-R1-6**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`escalation-trigger-collapsed-to-round-count`
  - evidence：templates/review-dispatch.md:60、templates/verdict.md:76、templates/status-change-ruling.md:50 把觸發條件縮成「同 root_cause_id 第三輪」。templates/review-escalation.md §3-§4 的權威條件還要求同 epoch 的三個唯一可計數 attempt、accepted/open/blocking、特定 finding class、executor attribution，並在 trigger attempt 存活；純 governance 或已消失根因不得消耗額度。新範本的縮寫會錯擋第四輪或錯發升級裁定單。
  - disposition：三份範本改為引用 review-escalation §3-§4 的可計數 attempt 與存活判準；不得把「第三輪」或相同字串單獨寫成充分條件。若 stage-rules/review.md 的同形簡寫仍保留，須同步消除兩個權威居所的歧義。
- **WF-REDESIGN-W2B-R1-7**　severity=info　blocking=false　class=environment　attribution=coordinator　root_cause_id=`pollution-baseline-broken-by-archive-move`
  - evidence：merge-result tree 自跑 pollution_check 得 rc=1、unapproved_count=32、stale-entry 2；其中基線 fc8b966 已由 archive/wave-specs/w2a.md 帶入 3 筆。PM 已以 950b3e2→fc8b966 的單 commit 差證實來源為封存 PR，且 scripts 不在本卡寫入集。
  - disposition：本卡不把此環境 finding 歸因執行者；需求方須另裁歸屬與修法。不得以擴 allowlist 直接把紅燈洗綠；修復後在實際 merge result 重跑。
- **WF-REDESIGN-W2B-R1-8**　severity=info　blocking=false　class=coordination　attribution=planner　root_cause_id=`resource-conflict-exact-match-blindness`
  - evidence：D-8/D-9 成立：dispatch-package 只能用自由文字描述限定條件，而 cli/src/wf_cli/resources.py 的 find_conflicts 採 exact set intersection；file:templates/ 不會與 file:templates/verdict.md 相撞，限定單行 delta 也沒有閘門語意。
  - disposition：維持交付報告所列 W3′ AC5(b) owner；本卡不虛構範本欄位或假裝 CLI 已能強制。W3′ 應同批定義 path-prefix/限定條件的結構化表示、衝突語意與正負控。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-REDESIGN-W2B-e0-2c35d48d024acd8d39a4536daf9401acb2c208ea
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: no
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: Codex@OpenAI（跨家族查核；實際模型以裁決自述為準）
findings:
  - finding_id: WF-REDESIGN-W2B-R1-1
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: canonical-standard-clause-truncated
    counting_eligible: true
  - finding_id: WF-REDESIGN-W2B-R1-2
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: migration-exclusion-policy-diverged
    counting_eligible: true
  - finding_id: WF-REDESIGN-W2B-R1-3
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: unique-line-count-reported-as-occurrences
    counting_eligible: true
  - finding_id: WF-REDESIGN-W2B-R1-4
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: defect-path-t1-card-flow-contradiction
    counting_eligible: true
  - finding_id: WF-REDESIGN-W2B-R1-5
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: bugs-ledger-retirement-conflicts-adoption
    counting_eligible: true
  - finding_id: WF-REDESIGN-W2B-R1-6
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: escalation-trigger-collapsed-to-round-count
    counting_eligible: true
  - finding_id: WF-REDESIGN-W2B-R1-7
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: environment
    attribution: coordinator
    root_cause_id: pollution-baseline-broken-by-archive-move
    counting_eligible: false
  - finding_id: WF-REDESIGN-W2B-R1-8
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: coordination
    attribution: planner
    root_cause_id: resource-conflict-exact-match-blindness
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5495509854 · 2026-09-01T14:28:32Z

## PM ④ 對裁決完整性 — `WF-REDESIGN-W2B` R1

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`。被檢查的裁決由查核者自行以 `wfcli review` 寫入（`issuecomment-5495441878`），⛔ 非 PM 代寫。

⛔ **PM 不判裁決對錯**（`review.md` §4 逐字），本節只驗結構完整性與身分自述。

### 結果：**完整，路由＝退回執行者**

| 檢查項 | 實查 |
|---|---|
| `review_result` | `REQUEST_CHANGES` |
| `core_pain_resolved` | `no` |
| `source_sha` | `2c35d48d024acd8d39a4536daf9401acb2c208ea`，與 PM handoff 寫入值一致 |
| `attempt_id` | `WF-REDESIGN-W2B-e0-2c35d48d…`；`escalation_epoch` 0 |
| `self_run` | **10 個區塊**，各含指令與輸出（⛔ 非「已跑」字樣） |
| findings 筆數 | **8**（`W2B-R1-1` … `W2B-R1-8`），blocking **6**／info **2** |
| 八欄齊全 | 逐筆含 `severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id`／`evidence`／`disposition`（＋`finding_id`）——PM 首次以 `欄名:` 形狀 grep 得 0，係渲染為 `欄名=值`，⛔ 非缺欄；逐筆目視核對後八欄皆在 |
| 查核者身分自述 | `Codex@OpenAI（gpt-5.6-sol，session 01a05d50-689a-70b3-862d-b9aae4e1a4d4）` ⇒ 跨模型家族成立，滿足裁定 2 條件 2 |
| 看板狀態讀回 | 階段=`審核`、交付狀態=`↩退回`、`iteration` **1.0**、owner=查核者 |

**attribution 分佈**：executor 6（R1-1…R1-6，全為 blocking）／**coordinator 1（R1-7＝PM 的 `pollution_check` 破壞，info、非阻塞）**／planner 1（R1-8＝D-8／D-9，info、非阻塞）。

### 查核者獨立重跑中與 PM 量測相符者（⛔ 非 PM 自證，係兩造獨立取得同值）

- merge-result tree 與 source tree 同為 `218b2aceadad18c2cc4928081c9056aee0954558`；merge-base `fc8b966c…`。
- 排除集 load-bearing：完整 **71**；拿掉 mapping／archive／w2b.md／baseline-universe.json 分別為 **77／74／73／72**。⇒ 與 PM 先前量到的 71 同值。
- `pollution_check` rc=1、`unapproved_count` 32、stale-entry 2，其中 3 筆由 `archive/wave-specs/w2a.md` 於基線 `fc8b966` 即帶入。
- baseline 全檔 `c1a1279…4bb68`；rows `d13ba6c0…` → `13141b5d…`；removed 36／added 0／changed 23／`verdict_changed` 0。

### 通過的部分（查核者逐字）

`6e8c4f2` 的 canonical 寫入**通過跨家族查核**——只有兩處指路／註記，⛔ 未改規則語意（裁定 2 的核心風險點解除）。AC0／AC3 與封閉五檔刪除的機械判準成立；六份範本皆四段信封；`1617 passed, 1 skipped`／專測 `33 passed`／replay `114/114`。

### 路由

`REQUEST_CHANGES` ⇒ **退回執行者**，6 筆 blocking 逐筆處置。⛔ 本輪⛔ 未達升級門檻（`review.md` §3：同 `root_cause` 第三輪才升級；本輪為 R1，八個 `root_cause_id` 互異）。

### ⭐ 一項需求方待裁（R1-5 逐字給了兩條路，PM ⛔ 不代選）

`stage-rules/defect-path.md:61` 新立「`BUGS.md` 為凍結歷史、不得新增」，與 `ADOPTION.md:18`「另起一份 `docs/BUGS.md`」直接衝突。查核者 disposition 逐字：「**本卡內先撤回 `BUGS.md` 退位的新規則，或由需求方另行裁定並授權同步改寫 ADOPTION 的規則語意；不得以『範本被移除』自行推出 ledger 也退位。**」

⇒ 甲＝撤回該新規則（本卡射程內可自理）；乙＝需求方裁定並**再擴一次授權**至 `ADOPTION.md` 的**規則語意**（⚠️ 現行授權逐字限定「就地註記與指路更正，⛔ 不得改動任何規則語意」）。上呈需求方。

### PM 未驗（逐項）

1. 六筆 blocking finding 的**內容對錯**——⛔ PM 不判裁決對錯。
2. 查核者 self_run 十個區塊 PM **未逐條重跑**；上表「相符」者僅為 PM 先前已獨立量過的四項。
3. R1-6 指的 `stage-rules/review.md` 同形簡寫是否也需同步修——查核者列為 disposition 的條件句，PM 未查該檔現況。


## Comment 5495978056 · 2026-09-01T15:02:47Z

## 需求方裁定 — `WF-REDESIGN-W2B` R1-4／R1-5 的修法（2026-09-01）

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`；⚠️ 發文者身分**不等於**決策者身分。決策出自需求方於本機 Claude Code 對話中的訊息：需求方先後要求 PM「幫忙研究幾輪再給建議」「注意不要違背原則，例如用機械判定之類的」「跑五輪然後如果有改變就再跑直到沒有疑慮」，於 PM 提出下述方案並跑完六輪對抗性複驗、建議未再改變後，逐字裁示「好按你建議」。該對話 transcript 於需求方本機可核。

⛔ 本裁定**不推翻查核者的任何 finding**——R1-4 指出的矛盾**確實存在**，R1-5 指出的衝突**確實存在**。本裁定只決定**修法**，而所採修法與 R1-4 disposition 的字面不同，理由與新證據逐項列於下。

---

### 裁定：採「己」——把 `defect-path.md` 減到有出處的部分，⛔ 不擴授權

1. **§一「⛔ 沒有 bug 專屬卡種」保留**，但**來源註記須改寫**：它⛔ 不是本卡新立，而是承接 `stage-rules/requirement.md` 的 `F-需求-01`（逐字「**卡一律由清單項升級（`--from-issue`）**；⛔ 不直接建 issue、⛔ 不走 DraftIssue」）。
2. **§三刪除級別門檻**（現行「T2 以上：走清單項 → 卡」）。改寫為：**未開卡時**（該清單項未獲需求方升級）留痕＝commit 說明＋canonical `:812` 的 trailer 下限。⇒ T0／T1 的「直接 commit」是**不開卡時的合法路徑**，⛔ 不是「T1 不准開卡」。
3. **`BUGS.md` 退位規則本卡不宣稱**（`defect-path.md` 現行 §三末段整段移除）。它依附在第 2 點刪掉的級別門檻上；與 `ADOPTION.md` 的衝突另議，⛔ 不在本卡處理。
4. **§二 分級表原樣保留**（逐字承接 canonical §3 分級句與已移除的 `bug-workflow.md` 判斷表）。

⇒ **R1-4 與 R1-5 同時消解**：沒有無條件句就沒有內部矛盾；不宣稱退位就不與 `ADOPTION.md:18` 衝突。**⛔ 不需要再擴一次寫入授權。**

### 與 R1-4 disposition 字面不同之處，及其新證據

查核者 disposition 逐字建議「把第一節的清單→一般卡路徑**明確限縮為 T2 以上**」。本裁定改為**刪除級別門檻**，理由是 PM 於裁定前跑的窮舉搜尋找到一份先前雙方都未引用的權威：

- **封閉集合**：main（`fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2`）上 tracked、非 `archive/`、非 worktree 的規則承載檔共 **33 份**（canonical＋AGENTS＋README＋ADOPTION＋tier-rules＋`stage-rules/*.md`＋`templates/*.md`＋決議紀錄），逐檔掃「開卡／不開卡／直接 commit／清單項／待審清單」，命中 **10 份**、逐行讀畢。
- **入口的唯一權威＝`stage-rules/requirement.md`**：§1「進入＝**清單項獲需求方點頭**＋指派執行者」；角色表「需求方 ｜ **決定哪個清單項升級**」；§3「**R1 由需求方／人工（痛點還成立嗎）**」；`F-需求-01`「卡一律由清單項升級」。
- **旁證三項**：canonical §3.2 的「開新卡僅限三情形」逐字為 (1) 不同能力域的執行者 (2) 紅線隔離 (3) 可真平行——**級別不在其中**；`tier-rules.md` 自陳射程為「判**一張卡**該走多強的流程」⇒ 級別作用於卡**之後**；換一組詞彙（快線／慢線／輕量流程／直接修）重掃封閉集合，`AI_WORKFLOW.md` 的唯一命中為誤命中（「直接**修**正問題陳述」）⇒ **canonical 沒有任何快線條文**。

⇒ 入口（開不開卡）與級別（開卡後走多強的流程）是**兩條獨立軸**。把入口綁回級別，⛔ 無論綁在 T2 或 T3，都會與 `F-需求-01` 牴觸。

### 本裁定已知的弱點（逐字登記，⛔ 不隱藏）

1. **`stage-rules/requirement.md` 於 2026-09-01 由 `950b3e2`（W2A）生效，僅一日**。216 張卡中只有 **3 張**於該日或之後建立 ⇒ 它幾乎沒有實務軌跡。
2. PM 原本引為旁證的「7 張 T1 缺陷卡」**全部建立於新制生效前**（例如 `#166` 為 2026-08-28）⇒ 該旁證已由 PM 自行撤下，本裁定**只靠條文**，⛔ 不靠實務分佈。
3. §6「尚未生效」標記的射程判讀：PM 讀為只罩**回應清冊機制**（① 印清單／③ 逐條回／④ 機械對照），⛔ 不罩 `F-需求-NN` 條文本身。**這是解讀，⛔ 不是機械判定**；若該讀法有誤，本裁定退回「本卡不立入口規則、另議」。

### 順帶查明（⛔ 非本裁定射程，供後續參考）

「T2 快線」在 main 上只殘留兩處：`README.md:15`／`:27` 與 `ADOPTION.md:13`。**W2B 分支的 `README.md` 與 `AGENTS.md` 對 `快線`／`BUGS`／`bug-card` 已零命中**，且屬已通過的 AC3。⇒ W2B merge 後唯一殘留為 `ADOPTION.md` 一處。另：main 的 `README.md` 目錄樹自稱「與 `ls` 實況一致」，實列 `BUGS.md`／`TASKS.md`／`tasks/` **三個不存在的路徑**，W2B 的 AC3 已一併修正。

### 其餘四筆 blocking

R1-1／R1-2／R1-3／R1-6 **⛔ 不受本裁定影響**，依查核者 disposition 逐筆處置。


## Comment 5496300640 · 2026-09-01T15:26:32Z

## 派審：`WF-REDESIGN-W2B`（#220）執行審 **R2** —— R1 六筆 blocking 修畢

（⚠️ 需求方轉貼時，本詞之後同帖接**交付報告全文**。逐 AC 證據的權威居所＝本卡 `issuecomment-5495259953`；本輪只有 delta，對照表見 ⑨。）

### ① 被審物

- 分支 `claude/wf-redesign-w2b-templates-be3b1b` @ **`a89f959a77df857461d51a468bc52486d73b251c`**（已推 origin、⛔ 未 merge）
- **派審基線 ＝ `git merge-base origin/main a89f959a…` ＝ `fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2`**（實跑取得並釘死字面，⛔ 非抄 origin/main）
- 本輪**單一 commit** `a89f959a…`「`docs(w2b): close the six R1 blocking findings (#220)`」，9 檔、`69 insertions / 40 deletions`
- ⭐ **canonical 逐字未動**：`git diff --stat 2c35d48..a89f959 -- AI_WORKFLOW.md` **空輸出**。`6e8c4f2` 已於 R1 通過你的跨家族查核，本輪⛔ 未再碰。

### ② 前輪與 root_cause

R1（`issuecomment-5495441878`）：`REQUEST_CHANGES`、`core_pain_resolved=no`、findings 8／blocking 6。

| finding | root_cause_id | 本輪處置摘要 |
|---|---|---|
| R1-1 | `canonical-standard-clause-truncated` | 第 3 條補回狹義例外／兩必要條件／trailer 對價／無機械執行者；加「是否援引」具名格；W3′ 試打重跑 |
| R1-2 | `migration-exclusion-policy-diverged` | 舊「母體排除三項」政策刪除 |
| R1-3 | `unique-line-count-reported-as-occurrences` | 欄位改「load-bearing 增量（唯一 `(檔,行)`）」，值 `6/3/2/1` |
| R1-4 | `defect-path-t1-card-flow-contradiction` | ⭐ 依需求方裁定「己」，**⛔ 非你的 disposition 字面** |
| R1-5 | `bugs-ledger-retirement-conflicts-adoption` | 同上 |
| R1-6 | `escalation-trigger-collapsed-to-round-count` | 三範本改引 `review-escalation.md` §3–§4；另兩檔以純新增註記消歧 |
| R1-7 | `pollution-baseline-broken-by-archive-move` | info／coordinator ⇒ 已另開 **#231**，⛔ 不歸本卡 |
| R1-8 | `resource-conflict-exact-match-blindness` | info／planner ⇒ owner 維持 W3′ AC5(b) |

⭐ **R1-4／R1-5 的修法與你的 disposition 字面不同**，係需求方裁定（`issuecomment-5495978056`）。你的 disposition 建議「把第一節限縮為 T2 以上」；裁定改為**刪除級別門檻**，依據是窮舉 33 份規則承載檔後找到的入口權威 `stage-rules/requirement.md`（`F-需求-01`＋§1＋§3）。**裁定逐字聲明⛔ 不推翻你的 finding——你指出的矛盾與衝突都成立**，只是修法不同。⚠️ 裁定自陳三項弱點（`requirement.md` 僅一日大／PM 原引的 7 張 T1 缺陷卡全為舊制／§6「尚未生效」射程屬解讀非機械判定），**該裁定本身也在你的射程內**。

### ③ PM 身分自述

PM：GitHub `ruan6047`（代理發文）；Claude Code；模型 `claude-fable-5`；session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

### ④ 受派者模型行

⭐ **仍要求跨模型家族（Codex）**。理由：`6e8c4f2` 的 canonical 寫入**仍在被審分支上**，本輪雖未再動它，但被審物是整個分支。實際模型以你的裁決自述為準。

### ⑤ PM 未驗（三分類）

**驗不了**
1. `defect-path.md` 改寫後的**條文內容**是否正確——裁定 1 逐字歸你判。
2. 三份範本引用 `review-escalation.md` §3–§4 後，實際使用時是否讀得懂（需真實升級事件）。

**沒去驗**
3. `prose_number_scan` 的 `dead_entries: 0`、`pytest`、`replay`、`--check`——PM 未在本輪重跑，全採執行者輸出。
4. 執行者 §2 R1-1 的「11 個關鍵語意逐鍵 canonical=True／範本=True」——PM 未逐鍵複驗。
5. `status-change-ruling.md` 對 `review-escalation` 的引用數為 **1**，另兩份為 2——PM 未判這是否足夠。
6. 舊入口分類 `A=0 B=54 C=15`——PM 未重跑。

**刻意不驗**
7. 合併結果上的守衛重跑——`reviewer-conduct` 三，你的職責。
8. 裁定「己」本身的對錯——需求方裁定，⛔ PM 不自審自己轉錄的裁定。

### ⑥ PM 自審紀錄（指令＋原始輸出，⛔ 不載結論字樣）

```
git merge-base origin/main a89f959a…            → fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2
git rev-list --count 2c35d48..a89f959           → 1
git diff --stat 2c35d48..a89f959 -- AI_WORKFLOW.md → （空輸出）
git log -1 --format='%B' a89f959 | git interpret-trailers --parse
                                                → Requested-by / Planned-by / Implemented-by / Co-authored-by
git show a89f959:templates/template-migration-map.md | grep -n 母體排除三項
                                                → 78:兩套互斥政策（舊版在此宣告「母體排除三項」…），讀者無法判定
git show a89f959:stage-rules/defect-path.md | grep -nE 'T2 以上：走清單項|BUGS\.md'
                                                → 78/83/84 三行，皆在「⚠️ 更正本檔首版」的歷史敘述內
for f in review-dispatch verdict status-change-ruling: grep -c review-escalation
                                                → 2 / 2 / 1
git diff 2c35d48..a89f959 -- stage-rules/review.md stage-rules/reviewer-conduct.md
                                                → 各 4 ++++，零刪除零修改（純新增）
AC0 四檔 grep -c 注意事項回應清冊               → 2 / 2 / 2 / 3
AC1 六檔 grep -c '^## 信封[一二三四] · '        → 4 / 4 / 4 / 4 / 4 / 4
gh run list --commit a89f959a…                  → （見 ⑧）
wfcli handoff --next-stage review               → rc=0；13 族清冊 已檢查 5／不適用 1／發現 7
                                                → 狀態=🔍待查核，SHA=a89f959a…
```

### ⑦ 失誤登記（PM 側，本輪）

**⛔ 無新增。** 前輪登記的兩筆（PM 打破 `pollution_check`／PM 首次派審被閘門拒收）**⛔ 不因本輪乾淨而註銷**，逐字仍在 `issuecomment-5495509854`。⚠️ 其中第一筆已由你判為 R1-7（`attribution=coordinator`）並另開 #231 承接。

### ⑧ 裁決寫回

先 `--validate-only` 自檢格式，再正式跑：

```
cd /Users/ruanruan/Dev/ai-workflow/cli
uv run wfcli review WF-REDESIGN-W2B --owner ruan6047 --project 4 --repo ruan6047/ai-workflow \
  --input <你的查核報告.yaml> --source-sha a89f959a77df857461d51a468bc52486d73b251c \
  --reviewer "Codex@OpenAI（<實際模型>，session <你的 session id>）"
```

八欄全給、`self_run` 必填；**沒有 `self_run` 的 APPROVE 無效**。⚠️ `wfcli` 的拒絕訊息走 **stderr**，⛔ 不要把 stderr 併進 stdout 後再截斷。⛔ 不改檔、⛔ 不 merge、⛔ 不動 review 以外的看板欄位。

### ⑨ 本輪改動 → AC 對照（PM 產出，補查核者本來要自己做的映射）

| 改動檔 | 對應 |
|---|---|
| `templates/dispatch-package.md` | **AC0**（四類輸出面之一）＋**AC1**（新五檔之一） |
| `templates/review-dispatch.md`／`verdict.md`／`status-change-ruling.md` | **AC1**（新五檔） |
| `templates/template-migration-map.md` | **AC1**（mapping＋舊入口零引用量法） |
| `docs/CONTRACT_TOOL_RECONCILE.md` | **AC2**（set diff 逐項 disposition） |
| `stage-rules/defect-path.md` | ⛔ 非 AC——裁定 1 的產出物 |
| `stage-rules/review.md`／`reviewer-conduct.md` | ⛔ 非 AC——R1-6 的歧義消除 |

⭐ **PM 已做的回歸檢查**：AC0 四檔命中仍 **2／2／2／3**、AC1 六檔信封段數仍 **4**（六檔全部）⇒ 本輪修補**未破壞** AC0／AC1 的機械判準。AC2／AC3／AC4 的證據 PM ⛔ 未重跑。

### 請重點查（⛔ 不限於此）

1. **六筆 blocking 是否真的關掉**——逐筆獨立重跑，⛔ 不採信執行者輸出。
2. ⭐ **裁定「己」本身**：`defect-path.md` 現行條文是否忠於裁定；裁定依據的 `F-需求-01` 讀法是否成立；裁定自陳的三項弱點你怎麼判。**這是需求方的裁定，但它在你的射程內。**
3. **R1-6 的取捨**：`stage-rules/review.md`／`reviewer-conduct.md` 的舊句**物理保留**、僅以新增註記降級為指路。執行者理由是那兩行在 `prose-number-inventory.json` 有 `threshold-ruling` 登記，改寫會產生 `dead_entries: 2`，而該 inventory ⛔ 不在本卡寫入集內（實測過）。**若你認為必須物理刪除，那需要 inventory 授權 ⇒ 請寫成 blocking 並註明需擴權。**
4. **執行者自查加做的一項**：R1-6 只點名 `review.md`，執行者另查出 `reviewer-conduct.md:26` 同形並一併處置；`planning.md` 的 `F-規劃-07` 判為不同主題未動（未驗第 4 項）——這個判讀對不對歸你。
5. **失誤登記 F-14**（自己編造 `root_cause_id` 字串）的補救是否可信。
6. **仍待裁五項**（D-3／D-4／D-5／D-6／D-7）——請給你的判斷，⛔ 不必代裁。


## Comment 5496423064 · 2026-09-01T15:35:37Z

<!-- wf-review-event:v1 card_id=WF-REDESIGN-W2B source_sha=a89f959a77df857461d51a468bc52486d73b251c attempt_id=WF-REDESIGN-W2B-e0-a89f959a77df857461d51a468bc52486d73b251c -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-REDESIGN-W2B`　attempt_id：`WF-REDESIGN-W2B-e0-a89f959a77df857461d51a468bc52486d73b251c`
- 查核者：Codex@OpenAI（gpt-5.6-sol，session 01a05d50-689a-70b3-862d-b9aae4e1a4d4）　escalation_epoch：0
- source_sha：`a89f959a77df857461d51a468bc52486d73b251c`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-09-01T23:35:33+08:00

### self_run（查核者實跑）

- `git status --porcelain; git merge-base origin/main HEAD; git merge-tree --write-tree fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2 HEAD; git rev-parse HEAD^{tree}`
  - 工作區 0 行；merge-base=fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2；merge-tree 與 HEAD tree 同為 cc85b359ac8b5a7d9cde988c074fb4df981b5a5f。
- `git rev-list --count 2c35d48d024acd8d39a4536daf9401acb2c208ea..HEAD; git diff --stat 2c35d48d024acd8d39a4536daf9401acb2c208ea..HEAD -- AI_WORKFLOW.md; git log -1 --format=%B HEAD | git interpret-trailers --parse`
  - R2 僅 1 commit；canonical diff 空；Requested-by、Planned-by、Implemented-by、Co-authored-by 四欄可解析。
- `nl -ba templates/dispatch-package.md | sed -n '62,68p'; nl -ba AI_WORKFLOW.md | sed -n '825,834p'`
  - R1-1 已關閉：狹義例外兩個合取條件、只免 rebase 不免 trailer、不適用 Reviewed-by 形態、無機械執行者與具名複核均與 canonical §6.1 對齊。
- `git grep 舊入口五檔名後套四項具名排除，並逐項移除單一排除重跑唯一檔行數`
  - 實際完整排除集=69；拿掉 mapping/archive/w2b/baseline 分別=75/72/71/70，故 load-bearing 增量 6/3/2/1 正確；A=0、B=54、C=15 的表亦加總為 69。
- `nl -ba templates/template-migration-map.md | sed -n '70,165p'`
  - R1-2 已關閉：現行排除政策只剩 §3.1 四項；但 §3.5:158 仍宣稱完整排除集 71、拿掉 archive 74，與同檔表格及實跑 69/72 衝突，R1-3 未閉環。
- `nl -ba stage-rules/requirement.md | sed -n '9,50p'; nl -ba stage-rules/defect-path.md | sed -n '23,84p'; nl -ba AI_WORKFLOW.md | sed -n '809,823p'`
  - R1-5 已關閉：BUGS.md 退位只剩歷史更正註記；但 R1-4 未閉環：defect-path:25 仍無條件宣告所有缺陷走清單項→一般卡，與同檔:68-73 的未開卡直接 commit 合法路徑衝突；F-需求-01 只限定卡的建立來源，不能推出所有工作都必須開卡。
- `rg -n -C 2 '升級|review-escalation|輪次' templates/review-dispatch.md templates/verdict.md templates/status-change-ruling.md stage-rules/review.md stage-rules/reviewer-conduct.md stage-rules/planning.md`
  - R1-6 已關閉：三範本明指 review-escalation §3–§4 並列可計數 attempt、累計、存活與排除條件；review/reviewer-conduct 以明確優先序把舊輪次句降為指路。planning F-規劃-07 是規劃形狀的啟發式，不是狀態升級充分條件，未動合理。
- `git grep 與 issue #220 comments 分別搜尋 defect-path-bugs-md-retirement-conflict；核對 R2 派審表的 bugs-ledger-retirement-conflicts-adoption`
  - F-14 補救可信：自創字串在 tracked tree 與 issue 留痕皆 0 命中，R2 派審沿用 R1 真值；錯誤只存在執行者同輪未外洩草稿。
- `python3 scripts/contract_tool_reconcile.py --format json 並與 baseline-universe.json 依 kind/name 做 set diff；python3 scripts/contract_tool_reconcile.py --check`
  - baseline rows sha256=d13ba6c04f5954295c705f515dbc1f242bd513d00da2eb708777b940c98d45cc；current=117793f8cab5955bb414782e0b9b37816b1d2d976656cd07c97ca19c3460d73f；removed/added/changed=36/0/25；verdict_changed=0；check rc=0、40 缺口。
- `cd cli && uv lock --check && uv run --frozen pytest -q`
  - rc=0；1617 passed, 1 skipped in 72.53s。
- `cd cli && uv run --no-project --python 3.12 ../scripts/replay_escalation_rules.py`
  - rc=0；114/114 通過。
- `python3 scripts/prose_number_scan.py; python3 scripts/qualified_pointer_scan.py; python3 scripts/canonical_citation_scan.py`
  - 三者 rc=0；prose total=200 且 unclassified/dead/invalid/mismatch/uncovered/extra 全 0；qualified-pointer 紅 0；canonical-citation 命中 0。
- `python3 scripts/pollution_check.py`
  - rc=1；unapproved_count=32、stale-entry=2，與前輪 R1-7 及 #231 已知 coordinator 缺口一致，未見本輪新增歸因。
- `rg -n '信封[一二三四]|card_field|artifact|CLI 探索紅線|舊入口零引用' templates docs stage-rules README.md AGENTS.md`
  - D-3：四段字面可作本卡局部衍生契約，但若跨專案復用應補唯一權威；D-4：card_field 正控缺席是 W3 守衛缺口，本卡不應虛構；D-5：目前 generator+rows hash+逐項表可重現，足以收件，若要求持久 artifact 須擴寫入集；D-6：第六條清單無權威時採明示 PM 推導並上呈是合理 fail-loud 暫態，後續應由 Project Contract 承接；D-7：卡面『零引用』與 AC2 強制產生引用字面互斥，應由 planner 改成『現行入口零引用/A=0』，不能要求 executor 達成總 grep=0。

### findings（2，其中 blocking 2）

- **WF-REDESIGN-W2B-R1-3**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`unique-line-count-reported-as-occurrences`
  - evidence：templates/template-migration-map.md:100、:121、:131 的 A/B/C 為 0/54/15，且 §3.5 指令實跑為 69；拿掉 archive 排除後實跑為 72。但 :158 仍宣稱本次 HEAD 是 71/74。表內 6/3/2/1 雖已修正，供讀者重跑的同節證據仍是前輪舊數字，文件內部自相矛盾。
  - disposition：把 §3.5 的本次 HEAD 實測改為 69/72，並以同一唯一 (檔,行) 口徑核對它與 A+B+C=69 及 archive 增量 3；不得保留前輪 71/74。
- **WF-REDESIGN-W2B-R1-4**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`defect-path-t1-card-flow-contradiction`
  - evidence：stage-rules/defect-path.md:25 仍無條件宣告『缺陷走的路…待審清單項 → 需求階段升級成一般卡』，但 :68-73 又宣告未開卡時可直接 commit。requirement.md:F-需求-01 的字面只規定『卡一律由清單項升級』，不規定每個工作都要成卡；需求方裁定己亦以『沒有無條件句』作為矛盾消解前提。
  - disposition：依裁定己把 §一入口句限縮為『缺陷若開卡，必由清單項升級為一般卡』或等價字面；保留沒有 bug 專屬卡種，並讓 §一與 §三的未開卡直接 commit 路徑同時成立。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-REDESIGN-W2B-e0-a89f959a77df857461d51a468bc52486d73b251c
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: no
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: Codex@OpenAI（跨家族查核；實際模型以裁決自述為準）
findings:
  - finding_id: WF-REDESIGN-W2B-R1-3
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: unique-line-count-reported-as-occurrences
    counting_eligible: true
  - finding_id: WF-REDESIGN-W2B-R1-4
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: defect-path-t1-card-flow-contradiction
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5496482407 · 2026-09-01T15:40:14Z

## PM ④ 對裁決完整性 — `WF-REDESIGN-W2B` R2

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`。被檢查的裁決由查核者自行以 `wfcli review` 寫入（`issuecomment-5496423064`），⛔ 非 PM 代寫。⛔ PM 不判裁決對錯。

### 結果：完整，路由＝退回執行者

| 檢查項 | 實查 |
|---|---|
| `review_result` ／ `core_pain_resolved` | `REQUEST_CHANGES` ／ `no` |
| `source_sha` | `a89f959a77df857461d51a468bc52486d73b251c`，與 PM handoff 寫入值一致 |
| `attempt_id` ／ `escalation_epoch` | `WF-REDESIGN-W2B-e0-a89f959a…` ／ 0 |
| findings | **2**，皆 `blocking=true`；八欄齊全（`severity=major`／`class=authoritative-artifact`／`attribution=executor`／`root_cause_id`＋`finding_id`／evidence／disposition） |
| 查核者身分自述 | `Codex@OpenAI（gpt-5.6-sol，session 01a05d50-689a-70b3-862d-b9aae4e1a4d4）` ⇒ 跨模型家族成立 |
| 看板讀回 | 階段=`審核`、交付狀態=`↩退回`、`iteration` 2.0 |

### PM 獨立重跑 R1-3 的爭議數字（⛔ 非採信查核者輸出）

以 AC 證據表 §AC1-d 的同一條管線，對兩棵樹各跑一次：

```
交付樹 a89f959：完整排除集 = 69　拿掉 archive 排除 = 72
前輪 2c35d48：完整排除集 = 71　拿掉 archive 排除 = 74
檔內 templates/template-migration-map.md:158 逐字：「實測（本次交付 HEAD）：完整排除集 71；拿掉 archive 那條 74」
```

⇒ **查核者正確**：71／74 是**前一棵樹**的值，對「本次交付 HEAD」是假宣稱。⭐ 增量 `6／3／2／1` **不受影響**（69→72 同樣是 +3），查核者亦逐字如此認定。

### ⚠️ 升級門檻警示（PM 依 `review.md` §3 主動標記）

兩筆 finding 的 `root_cause_id`（`unique-line-count-reported-as-occurrences`、`defect-path-t1-card-flow-contradiction`）**皆為第二個可計數 attempt**（R1 的 `2c35d48` 為第一個）。⇒ **若下一輪任一筆仍 open，即為第三個 attempt**，依 canonical §3「第三個可計數 attempt 先進 escalation checkpoint」與 `review.md` §3「同 root_cause 第三輪 ⇒ ⛔ 不派第四輪，直接升級」，PM 屆時**⛔ 不得逕自派第四輪**，須先建 `escalation-checkpoint` 事件並上呈需求方。逐字標記於此，⛔ 不留給下一輪臨時判斷。

### 已關閉

R1-1／R1-2／R1-5／R1-6 經查核者判定可關閉。另三項判定：「己」裁定的「入口與級別是兩條軸」成立且 `requirement.md` §6 標記射程判讀正確；R1-6 的「保留舊句＋明示權威優先序」可接受；`planning.md` 的 `F-規劃-07` 未動正確。F-14 補救可信。

### PM 未驗

1. 兩筆 finding 的內容對錯——⛔ PM 不判裁決對錯（R1-3 的數字 PM 已獨立重跑，屬事實核對⛔ 非判對錯）。
2. 查核者 self_run 十四個區塊 PM 未逐條重跑；對帳 `36/0/25` 與各守衛全綠 PM 未複驗。


## Comment 5496733832 · 2026-09-01T15:59:59Z

## 派審：`WF-REDESIGN-W2B`（#220）執行審 **R3** —— R2 殘留兩筆修畢

（⚠️ 需求方轉貼時，本詞之後同帖接**交付報告全文**。逐 AC 證據的權威居所＝本卡 `issuecomment-5495259953`。）

### ⭐ 本輪是第三個可計數 attempt —— 請先看這段

`root_cause_id` `unique-line-count-reported-as-occurrences` 與 `defect-path-t1-card-flow-contradiction` 皆已第三輪：

| attempt | source_sha | 你的裁決 |
|---|---|---|
| 1 | `2c35d48d024acd8d39a4536daf9401acb2c208ea` | R1 `REQUEST_CHANGES`（兩筆 raise） |
| 2 | `a89f959a77df857461d51a468bc52486d73b251c` | R2 `REQUEST_CHANGES`（兩筆殘留） |
| **3** | **`5331fc47906a3a9fb3f1805ba14b1f06aa2588f9`** | **本輪** |

依 canonical §3「第三個可計數 attempt 先進 escalation checkpoint」與 `stage-rules/review.md` §3「同 `root_cause` 第三輪 ⇒ ⛔ 不派第四輪，直接升級」：

- **你照常裁決**，⛔ 本段不改變你的判準，也⛔ 不暗示應該放行。
- **裁決落地後由 PM 建 `escalation-checkpoint`**（`wfcli checkpoint` 的 `--trigger-attempt-id` 逐字要求「其 review 裁決**須已落地**」⇒ 構造上無法先建）。`--decision` 四選一（`continue`／`replan`／`change-executor`／`escalate`）屬**需求方裁定**，⛔ 非 PM 亦⛔ 非你。
- ⇒ **若你判 `REQUEST_CHANGES`，PM ⛔ 不會逕自派第四輪**，會先建 checkpoint 並上呈需求方。

### ① 被審物

- 分支 `claude/wf-redesign-w2b-templates-be3b1b` @ **`5331fc47906a3a9fb3f1805ba14b1f06aa2588f9`**（已推 origin、⛔ 未 merge）
- **派審基線 ＝ `git merge-base origin/main 5331fc47…` ＝ `fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2`**（實跑取得並釘死字面）
- 本輪**單一 commit**，**2 檔**、`6 insertions / 2 deletions`（`stage-rules/defect-path.md` 4+/1-、`templates/template-migration-map.md` 4+/1-）
- ⭐ **canonical 逐字未動**：`git diff --stat a89f959..5331fc4 -- AI_WORKFLOW.md` 空輸出。`6e8c4f2` 已於 R1 通過你的跨家族查核。

### ② 前輪與 root_cause

R2（`issuecomment-5496423064`）：`REQUEST_CHANGES`、findings 2、皆 blocking。R1-1／R1-2／R1-5／R1-6 已於 R2 關閉，本輪⛔ 未再動。

| finding | 本輪處置 |
|---|---|
| R1-3 `unique-line-count-reported-as-occurrences` | ⭐ **形狀變更**：兩個絕對數由「寫死在散文裡」改為「產生器在產生當下量出」，並就地聲明⛔ 非釘死值。執行者逐字說明理由：再填一次數字只會在下一個 commit 再度過期，那就是同一個 root_cause 的第三次 |
| R1-4 `defect-path-t1-card-flow-contradiction` | §一 首句由**全稱句**改為你指定的**條件句**「缺陷若開卡，必由清單項升級為一般卡」，並另加一行逐字排除無條件讀法 |

### ③ PM 身分自述

PM：GitHub `ruan6047`（代理發文）；Claude Code；模型 `claude-fable-5`；session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

### ④ 受派者模型行

仍要求**跨模型家族**（`6e8c4f2` 的 canonical 寫入仍在被審分支上）。實際模型以你的裁決自述為準。

### ⑤ PM 未驗（三分類）

**驗不了**
1. R1-3 的**形狀變更是否為你要的解**——R2 退回單逐字要求「那屬形狀變更，要在報告裡寫明理由交查核者判」⇒ 判定歸你，PM ⛔ 不代判。
2. `defect-path.md` §一 改寫後的**條文語意**是否正確。

**沒去驗**
3. `pytest`／`replay`／`--check`／`prose`／`qualified_pointer`／`canonical_citation`——PM 本輪未重跑，全採執行者輸出。
4. 舊入口分類 `A=0 B=54 C=15`、`dead=[]`——PM 未重跑（PM 只重跑了排除集總數）。
5. 執行者的產生器（`old_entry_residual.py`／`refresh_reconcile_doc.py`）住 scratchpad、⛔ 未進 repo ⇒ PM 未取得、未跑。

**刻意不驗**
6. 合併結果上的守衛重跑——`reviewer-conduct` 三，你的職責。

### ⑥ PM 自審紀錄（指令＋原始輸出，⛔ 不載結論字樣）

```
git rev-list --count a89f959..5331fc4                    → 1
git diff --stat a89f959..5331fc4                         → 2 files changed, 6 insertions(+), 2 deletions(-)
git diff --stat a89f959..5331fc4 -- AI_WORKFLOW.md       → （空輸出）
git log -1 --format='%B' 5331fc4 | git interpret-trailers --parse
                                                         → Requested-by / Planned-by / Implemented-by / Co-authored-by

git show 5331fc4:templates/template-migration-map.md | grep -oE '完整排除集 [0-9]+|拿掉 archive 那條 [0-9]+'
                                                         → 完整排除集 69 ／ 拿掉 archive 那條 72

# PM 在【本交付樹 5331fc4】上現場重跑 AC1-d 同一條管線：
  完整排除集 = 69　拿掉 archive 排除 = 72
# 對照：a89f959 上為 69/72；2c35d48 上為 71/74

git show 5331fc4:stage-rules/defect-path.md | grep -c 缺陷走的路與其他工作完全相同      → 0
git show 5331fc4:stage-rules/defect-path.md | grep -c 缺陷若開卡，必由清單項升級為一般卡 → 1

wfcli handoff --next-stage review
    → rc=0；13 族清冊 已檢查 5／不適用 1／發現 7
    → 已交接 → Codex@OpenAI（狀態=🔍待查核，SHA=5331fc47…）
```

### ⑦ 失誤登記（PM 側）

**⛔ 本輪無新增。** 先前登記者⛔ 不因本輪乾淨而註銷：PM 打破 `pollution_check`（已由你判 R1-7 `coordinator`、另開 #231）／PM 首次派審被閘門拒收（`issuecomment-5495509854`）。另 PM 於 #231 已自認兩處引用錯誤，與本卡無關。

### ⑧ 裁決寫回

```
cd /Users/ruanruan/Dev/ai-workflow/cli
uv run wfcli review WF-REDESIGN-W2B --owner ruan6047 --project 4 --repo ruan6047/ai-workflow \
  --input <你的查核報告.yaml> --source-sha 5331fc47906a3a9fb3f1805ba14b1f06aa2588f9 \
  --reviewer "Codex@OpenAI（<實際模型>，session <你的 session id>）"
```

八欄全給、`self_run` 必填；**沒有 `self_run` 的 APPROVE 無效**。⚠️ 拒絕訊息走 **stderr**，⛔ 不要併流後截斷。⛔ 不改檔、⛔ 不 merge。

### 請重點查（⛔ 不限於此）

1. **兩筆是否真的關掉**——執行者這次是用「finding 的成立條件在交付 HEAD 上不成立」的形式給證據（⛔ 非「我改了」），請驗那個形式本身站不站得住。
2. ⭐ **R1-3 的形狀變更**：「產生當下量測＋聲明非釘死值」是不是可接受的解？執行者**自陳仍不免疫**——「若有人改了樹卻不重跑產生器，該行一樣會過期」，並說根除須把產生器放進 `scripts/` 並掛 CI，而 `scripts/` ⛔ 不在本卡寫入集。**這個殘餘風險你接不接受，是本輪最主要的判斷。**
3. **執行者的 F-19 自陳**：「裁定射程 ≠ finding 射程——我把『照裁定做了』等同於『finding 關閉』」。這個根因診斷對不對。
4. **仍待裁五項**（D-3／D-4／D-5／D-6／D-7）以及本輪新增的殘餘風險項——請給判斷，⛔ 不必代裁。


## Comment 5496807342 · 2026-09-01T16:05:39Z

<!-- wf-review-event:v1 card_id=WF-REDESIGN-W2B source_sha=5331fc47906a3a9fb3f1805ba14b1f06aa2588f9 attempt_id=WF-REDESIGN-W2B-e0-5331fc47906a3a9fb3f1805ba14b1f06aa2588f9 -->
## 查核裁決：APPROVE

- 卡：`WF-REDESIGN-W2B`　attempt_id：`WF-REDESIGN-W2B-e0-5331fc47906a3a9fb3f1805ba14b1f06aa2588f9`
- 查核者：Codex@OpenAI（gpt-5.6-sol，session 01a05d50-689a-70b3-862d-b9aae4e1a4d4）　escalation_epoch：0
- source_sha：`5331fc47906a3a9fb3f1805ba14b1f06aa2588f9`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-09-02T00:05:36+08:00

### self_run（查核者實跑）

- `git status --porcelain; git rev-parse HEAD; git merge-base origin/main HEAD; git merge-tree --write-tree fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2 HEAD; git rev-parse HEAD^{tree}`
  - 工作區 0 行；HEAD=5331fc47906a3a9fb3f1805ba14b1f06aa2588f9；merge-base=fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2；merge-tree 與 HEAD tree 同為 ec0936cc4f88da400b4d1c93c55b268b550c5587。
- `git rev-list --count a89f959a77df857461d51a468bc52486d73b251c..HEAD; git diff --stat a89f959a77df857461d51a468bc52486d73b251c..HEAD; git diff --stat a89f959a77df857461d51a468bc52486d73b251c..HEAD -- AI_WORKFLOW.md; git log -1 --format=%B HEAD | git interpret-trailers --parse`
  - R3 僅 1 commit、2 files changed、6 insertions/2 deletions；canonical diff 空；Requested-by、Planned-by、Implemented-by、Co-authored-by 四欄可解析。
- `git grep 舊入口五檔名後套四項具名排除；再拿掉 archive 排除重跑唯一 (檔,行)`
  - 完整排除集=69；拿掉 archive=72；逐檔分類為 ADOPTION 3、AI_WORKFLOW 2、contract test 3、reconcile doc 42、defect-path 4、授權外七檔合計 15，故 A/B/C=0/54/15 且 archive 增量=3。
- `nl -ba templates/template-migration-map.md | sed -n '90,165p'`
  - WF-REDESIGN-W2B-R1-3 已關閉：表格 A/B/C 加總 69、§3.5 當次值 69/72、實跑 69/72 三面一致；6/3/2/1 仍為同一唯一檔行口徑。當次值明示非跨 commit 常數。
- `nl -ba stage-rules/requirement.md | sed -n '20,32p'; nl -ba stage-rules/defect-path.md | sed -n '23,78p'`
  - WF-REDESIGN-W2B-R1-4 已關閉：§一改成『缺陷若開卡』的條件句，並明文排除所有缺陷必須開卡；與 §三未開卡直接 commit 路徑及 F-需求-01 的卡建立來源語意一致。
- `python3 scripts/contract_tool_reconcile.py --format json 並與 baseline-universe.json 依 kind/name 做 set diff；python3 scripts/contract_tool_reconcile.py --check`
  - baseline rows sha256=d13ba6c04f5954295c705f515dbc1f242bd513d00da2eb708777b940c98d45cc；current=117793f8cab5955bb414782e0b9b37816b1d2d976656cd07c97ca19c3460d73f；removed/added/changed=36/0/25；verdict_changed=0；check rc=0、40 缺口。
- `cd cli && uv lock --check && uv run --frozen pytest -q`
  - rc=0；1617 passed, 1 skipped in 74.16s。
- `cd cli && uv run --frozen pytest tests/test_contract_tool_reconcile.py -q`
  - rc=0；33 passed in 1.52s。
- `cd cli && uv run --no-project --python 3.12 ../scripts/replay_escalation_rules.py`
  - rc=0；114/114 通過。
- `python3 scripts/prose_number_scan.py; python3 scripts/qualified_pointer_scan.py; python3 scripts/canonical_citation_scan.py`
  - 三者 rc=0；prose total=200 且 unclassified/dead/invalid/mismatch/uncovered/extra 全 0；qualified-pointer 紅 0；canonical-citation 命中 0。
- `python3 scripts/pollution_check.py`
  - rc=1；unapproved_count=32、stale-entry=2，與前輪 R1-7 及 #231 的 coordinator 缺口一致，本輪兩檔修補未新增污染 finding。
- `gh run list --repo ruan6047/ai-workflow --commit 5331fc47906a3a9fb3f1805ba14b1f06aa2588f9`
  - CI completed success，run 33527743585。
- `讀取 R1 issuecomment-5495441878、R2 issuecomment-5496423064 的 escalation facts，並核對 wfcli checkpoint help 與 checkpoint_cmd.py`
  - 派審所稱『第三個可計數 attempt』不成立：R1/R2 均為 preflight_basis_binding=structurally-unavailable、escalation_account=not-asserted，沒有 counts_toward_escalation=true。checkpoint 的 unique_attempt_count 仍由操作者提供而非事件流推導；本輪 APPROVE 亦不產生可計數退回，故不得以三輪整數宣稱必建 checkpoint。
- `核對 D-3/D-4/D-5/D-6/D-7、F-19 與本輪 scratchpad generator 殘餘風險`
  - F-19 診斷正確：裁定修法完成不等於 finding 證據已失效，本輪已改用 HEAD 上原 evidence predicate 為假來閉環。D-3 可作本卡局部衍生契約但跨專案前應補唯一權威；D-4 正控缺席歸 W3；D-5 現有 generator輸出+rows hash+逐項表足以收件，持久 artifact 需擴權；D-6 以明示 PM 推導並上呈作 fail-loud 暫態，後續由 Project Contract 承接；D-7 應由 planner 把字面改成現行入口零引用/A=0。scratchpad generator 未交付表示數字仍可能因漏重生而漂移；本輪接受為非阻擋維護風險，不宣稱已自動免疫，若要根除須另授權 scripts/ 與 CI。

### findings（0，其中 blocking 0）

- （無）

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-REDESIGN-W2B-e0-5331fc47906a3a9fb3f1805ba14b1f06aa2588f9
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: Codex@OpenAI（跨家族查核；實際模型以裁決自述為準）
findings: []
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5496842413 · 2026-09-01T16:08:20Z

## PM ④ 對裁決完整性 — `WF-REDESIGN-W2B` R3（`APPROVE`）

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`。裁決由查核者自行以 `wfcli review` 寫入（`issuecomment-5496807342`），⛔ 非 PM 代寫。⛔ PM 不判裁決對錯。

### 結果：完整

| 檢查項 | 實查 |
|---|---|
| `review_result` ／ `core_pain_resolved` | `APPROVE` ／ **yes** |
| `source_sha` | `5331fc47906a3a9fb3f1805ba14b1f06aa2588f9`，與 PM handoff 寫入值一致 |
| `attempt_id` ／ `escalation_epoch` | `WF-REDESIGN-W2B-e0-5331fc47…` ／ 0 |
| findings | **0** |
| `self_run` | 14 個指令區塊 |
| 查核者身分自述 | `Codex@OpenAI（gpt-5.6-sol，session 01a05d50-689a-70b3-862d-b9aae4e1a4d4）` ⇒ 跨模型家族成立（裁定 2 條件 2 滿足） |
| 看板讀回 | 階段=`審核`、交付狀態=**`✅通過`**、`iteration` 3.0、級別 T3 |

### ⛔ PM 失誤登記：「第三個可計數 attempt」是我宣稱超過證據

PM 於 R2 的 ④ 完整性（`issuecomment-5496482407`）與 R3 派審詞開頭逐字宣稱「兩筆 finding 皆為**第二個可計數 attempt**」「本輪是**第三個可計數 attempt**」，並據此預告「PM ⛔ 不得逕自派第四輪，須先建 `escalation-checkpoint`」。

查核者於 R3 指出該宣稱無帳務證據。**PM 實查證實**：

```
issuecomment-5495441878（R1）: escalation_account: not-asserted
issuecomment-5496423064（R2）: escalation_account: not-asserted
```

⇒ 三則 review 事件皆 `escalation_account=not-asserted`、無 `counts_toward_escalation=true`；`checkpoint` 的 `--unique-attempt-count` 逐字由**操作者提供**，⛔ 非事件流推導。**PM 把「查核輪次」直接當成「可計數 attempt」，那是推論不是帳務。**

⚠️ **正確的表述應是**：三輪的**可計數性從未被主張**（`not-asserted`）⇒ ⛔ 不得宣稱已計數，**也⛔ 不得宣稱一定不計數**（查核者逐字如此界定）。PM 先前的預告因此**無效**，本卡⛔ 不建 `escalation-checkpoint`。

⭐ 此為「宣稱超過證據」族，與本卡 R1-3 的 root cause 同形——⚠️ **PM 在 R2 的 ④ 中一邊登記執行者的計數口徑錯誤、一邊自己犯了計數口徑錯誤**，逐字登記於此。

### 查核者確認關閉的兩筆

- **R1-3**：`69／72` 與實跑一致、`A/B/C = 0/54/15`、增量 `6/3/2/1` 全部一致。
- **R1-4**：`defect-path.md:25` 已改為「缺陷若開卡」，不再與未開卡直接 commit 衝突。
- **F-19 根因診斷正確**：完成裁定修法⛔ 不等於 finding 自動關閉；本輪以「原 evidence predicate 在 HEAD 上不成立」閉環。
- **scratchpad 產生器未交付**：判為**可接受的非阻擋維護風險**——目前數字正確，但未自動防漂移；根除需另授權 `scripts/` 與 CI。

### 四道停下條件逐項（PM 實查，供需求方判斷是否放行收尾）

1. **blocking finding 未 resolved** — ⛔ 不成立（findings 0、`core_pain_resolved=yes`）。
2. **CI 非綠，或 merge 後狀態不符預期** — CI `success`；merge 後須另驗 main 真的前進。
3. **分支 BEHIND 且 `update-branch` 衝突** — ⛔ 不成立：`git rev-list --count 分支..origin/main` = **0**。
4. **T4 紅線卡須人工 sign-off** — 本卡級別 **T3** ⇒ ⛔ 不觸發。⚠️ 惟本卡含 canonical 寫入（`6e8c4f2`），該項的加強要求（跨模型家族查核）已於 R1 與本輪滿足。

### ⚠️ 收尾的已知阻擋（⛔ 非停下條件，是機械前提）

`lsof +D` 實查該 worktree 仍被 **4 個 process** 佔住 cwd（`disclaime` 92108／`claude` 92109／`node` 92144／`zsh` 98240）⇒ `handoff --next-stage release --cleanup` 會回 `rc=5`。**須先讓執行者 session 結束**，此為 W2A 已驗證過的同一形狀。

### PM 未驗

1. 查核者 14 個 `self_run` 區塊 PM 未逐條重跑。
2. `A/B/C = 0/54/15` PM 未重跑（PM 只重跑了排除集總數 69／72）。


## Comment 5496975935 · 2026-09-01T16:18:09Z

## release 完成 ＋ 收尾第 5 步（卡檔封存）**未完成，逐字說明原因**

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`。需求方於對話中逐字裁示「好合併」與「關了，跑 release」。

### 已完成

- **merge**：PR **#232**，`state=MERGED`、merge commit **`13cc5f0551759934f8a9a7295de219b4c4164b3e`** ＝現行 `origin/main`（以 `gh pr view --json state,mergedAt,mergeCommit` 與 `git rev-parse origin/main` 對照確認，⛔ 不只看 rc）。
- ⭐ **刻意用 merge commit，⛔ 非 squash／rebase**：裁定 2 條件 1 要求 canonical 寫入拆成獨立 commit 單獨留痕。squash 會壓掉它、rebase 會改它的 SHA。實查 `git merge-base --is-ancestor 6e8c4f252684383c3c4159b0cefeda8615c0a4ef origin/main` **成立** ⇒ **原 SHA 完整保留在 main 歷史中**。
- merge commit 的 trailer **五欄**經 `git interpret-trailers --parse` 全數解析（含 `Reviewed-by: Codex@OpenAI (gpt-5.6-sol)`）。
- **release handoff** `rc=0`：狀態 **🏁完成**、SHA `13cc5f05…`；cleanup `mode=applied`，**已執行 `remove_worktree`／`delete_local_branch`／`delete_remote_branch`**（三項全授權——merge commit 使分支成為 main 祖先，證明分級高於 W2A 的 squash 情形）。
- 合併後於 main 實跑守衛：`prose_number_scan` rc=0 七項全零／`contract_tool_reconcile --check` rc=0（40 缺口一致）／`canonical_citation_scan` rc=0／`qualified_pointer_scan` rc=0。

### ⚠️ `pollution_check` 於 main 為 rc=1、`unapproved_count` **32**

語料由 17 檔增為 **33** 檔。**這如 PM 於 `#231` 派工留痕中的預告**：本卡動過的四個檔（`docs/CONTRACT_TOOL_RECONCILE.md` 22 筆／`ADOPTION.md` 4／`cli/tests/test_contract_tool_reconcile.py` 2／`templates/handoff-contract.md` 1，共 29 筆）自釘死 BASE 起皆已被改過，merge 即進 main 語料。⇒ **`WF-POLLUTION-MANIFEST-STALE1`（#231）的 AC1「main 回到 rc=0」的射程由 3 筆變為 32 筆**，PM 將於該卡留痕。⛔ 不歸本卡。

### ⛔ 收尾第 5 步（卡檔封存）**未完成**——與一個守衛結構性互斥

PM 依 W0／W1／W2A 先例嘗試把 `docs/research/drafts/wave-specs/w2b.md` 移入 `archive/wave-specs/` 並清 inventory 的 5 筆條目。**本地掃描器全綠**（`prose_number_scan` 七項全零、total 199→193；`pollution_check` 的 `unapproved` **32→32**、`stale-entry` **2→2**，⛔ 未加重 #231），但 **CI 的 pytest 轉紅**：

```
FAILED tests/test_prose_number_scan.py::test_w2b_six_claim_is_pinned_to_negation_form
FileNotFoundError: …/docs/research/drafts/wave-specs/w2b.md
（run 33530682603）
```

**成因（讀碼確認）**：該測試是 R21 要求補的黃金值回歸測試，同時依賴兩件事——(1) `w2b.md` 存在於 `docs/research/drafts/wave-specs/` 這個**路徑**（`cli/tests/test_prose_number_scan.py:428`）；(2) inventory 內存在 `path` 以 `w2b.md` 結尾的**條目**（`:432-433`）。而封存**必須同時**改掉路徑並刪除那 5 筆條目（不刪即死條目，W1 先例）。⇒ **兩者互斥**。

⇒ PR #233 已關閉、分支已刪除、`w2b.md` 仍在原位、`main` 仍為 `13cc5f05…`、工作區乾淨。**⛔ PM 不自行修改該測試**——那是動守衛，⛔ 非收尾雜務。

⭐ **值得記的對比**：同一個「封存動作打破守衛」的形狀，W2A 那次是 `pollution_check` **靜默轉紅**（不在 CI，PM 當時只跑 prose 就以為過了）；這次是 pytest **大聲失敗**且擋在 merge 前。⇒ **在 CI 內的守衛與不在 CI 內的守衛，後果差一個數量級**——這正是 #231 AC5 要處理的事。

### PM 失誤登記

**PM 提交封存 commit 前只跑了掃描器，⛔ 未跑 `pytest`。** 本地四支掃描器全綠即推 PR，由 CI 抓到。⚠️ 與 W2A 封存那次是**同族**（那次是漏跑 `pollution_check`）：**兩次都是「跑了一部分驗證就當成全部」**。⛔ 不以「這次被 CI 擋下了」淡化——擋下它的是 CI，⛔ 不是 PM。

### 待處置（PM ⛔ 不自行決定）

`w2b.md` 的封存與 `test_w2b_six_claim_is_pinned_to_negation_form` 互斥。三個方向（⛔ 未裁）：(a) 不封存 `w2b.md`，並就地說明它是例外；(b) 改寫該測試使其不依賴 draft 路徑與 inventory 條目——⚠️ 那是**改守衛**，且該測試的存在正是 R21 抓到「舊錯值可通過全套」後補上的；(c) 另立卡處理「封存動作與釘死路徑的守衛」這一類衝突。**上呈需求方。**


## Comment 5497468178 · 2026-09-01T16:58:42Z

## PM 更正：污染符 32 筆的歸屬（2026-09-02）

**轉錄來源自述**：本則由 PM（session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`）以 `gh` token 發文，該 token 即 `ruan6047`。

PM 於本卡兩處把 `pollution_check` 的 32 筆整包標成「屬 `WF-POLLUTION-MANIFEST-STALE1`（#231）的射程」：④ 完整性（`issuecomment-5496842413`）與 release 留痕（`issuecomment-5496975935`）。**該歸屬是錯的，逐字更正如下。**

| 筆數 | 位置 | 正確歸因 |
|---|---|---|
| **3** | `archive/wave-specs/w2a.md` | **PM 的封存 commit（PR #230）造成**；查核者 R1-7 判 `attribution=coordinator` |
| **29** | `docs/CONTRACT_TOOL_RECONCILE.md` 22／`ADOPTION.md` 4／`cli/tests/test_contract_tool_reconcile.py` 2／`templates/handoff-contract.md` 1 | **本卡（W2B）自己的 post-image** |

**證據**：PM 以逐 PR merge-base 實測——`pollution_check --base fc8b966c25a3a805cdb445c7ddec9bb00fe3f8e2`（＝本卡的 merge-base）在現行 main 上仍得 **29 筆、rc=1**。⇒ 那 29 筆落在本卡改過的檔案裡，**掃描器一直是正確的**；是流程在 merge 前把它 defer 了（PM 逐字寫成「既知 #231 缺口」）。

⚠️ **查核者 R1-7 從未把那 29 筆歸給 #231**——其 evidence 逐字只指出「其中基線 `fc8b966` 已由 `archive/wave-specs/w2a.md` 帶入 3 筆」，disposition 逐字為「**需求方須另裁歸屬與修法**」。**「歸 #231」是 PM 加的。**

### 這對本卡的影響：⛔ 無狀態面變更

需求方於 2026-09-02 裁定（`#231` 的 `issuecomment` 逐字轉錄該裁定）：**三處都由 #231 依其 AC1 原文以 allowlist 處置**——理由是那 5 個檔雖在 #231 寫入集外，**但補救手段 `scripts/pollution-allowlist.json` 在其寫入集內**（PM 實測：加 31 筆＋刪 2 筆死條目 ⇒ `rc=0`）。

⇒ **⛔ 不開 `WF-REDESIGN-W2B-FIX1`、⛔ 不重開本卡、⛔ 不改本卡任何欄位。** 本卡維持 🏁完成。本則僅為歸屬更正之留痕。

⚠️ 附帶更正：本卡的驗證項「污染符 grep 零命中」PM 先前判為「在本卡射程內不可達」——**該判斷的理由（射程外）也是錯的**；正確理由是：本卡 merge 時該項確實未達成，且 PM 選擇 defer 而非退回。⇒ **本卡是帶著一個未達成的驗證項通過的**，逐字登記於此。

