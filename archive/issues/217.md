# #217 WF-REDESIGN-W1 待審清單與開卡閘（四波五卡 W1）
- state: open  created: 2026-08-31T16:52:13Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/217
- comments: 14

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；已知模式的 CLI 改動（表單／schema／旗標擴充），依 w1.md 級別依據）　查核：待指派（建議 主力型；主力型＋獨立查核（建議 Codex 跨實體——實體效力實證）；public contract 改動，獨立性要求疊加於層級之上）
- Initiative：WF-REDESIGN1　spec 基線：ai-workflow 93bb8c086f0cf8870537390511b5f0aa2d037c97
- DB：db_scope=none
- 服務的原始目標：可稽核＋防低級事故＋流程順暢——開卡產生器、空驗收與 DraftIssue 直通是防低級事故軸的洞

## 簡介
<!-- card-brief:begin -->
適用時機：四波五卡 W1——待審清單與開卡閘。開卡唯一路徑改 open --from-issue、收件表單上線、card-face JSON schema（本卡唯一 owner）、驗收必填、amend feature/routing 擴充。階段計畫：需求→規劃→執行→審核→結案。級別依據：wfcli 為狀態面唯一寫入通道＝public contract ⇒ 至少 T3；可逆（git revert）。spec_version: 1（甲′ 規格住卡面；來源 wave-specs/w1.md 屆時封存）。

**前置（P1-18 修訂）**：板上唯一 DraftIssue item 之處置於開工時經需求方一句裁定（轉 Issue／封存／明示保留）；退場 oracle＝raw inventory artifact——（P1-29）producer＝W1 前置一次性唯讀查詢，貼上即跑（query_version=inv-v1；輸出 root 含 query_version／fetched_at(UTC)／project_id；rows 依 item id 排序；sha256 另檔）：
```bash
OUT=raw-inventory-$(date -u +%Y%m%dT%H%M%SZ).json; CUR=null; : > /tmp/inv_rows.jsonl
while :; do
  R=$(gh api graphql -f query='query($a:String){user(login:"ruan6047"){projectV2(number:4){id items(first:100,after:$a){pageInfo{hasNextPage endCursor} nodes{id type c:fieldValueByName(name:"卡ID"){... on ProjectV2ItemFieldTextValue{text}}}}}}}' -F a="$CUR")
  echo "$R" | jq -c '.data.user.projectV2.items.nodes[] | {item_id:.id, content_type:.type, card_id:(.c.text // null)}' >> /tmp/inv_rows.jsonl
  [ "$(echo "$R"|jq -r '.data.user.projectV2.items.pageInfo.hasNextPage')" = true ] || break
  CUR=$(echo "$R"|jq -r '.data.user.projectV2.items.pageInfo.endCursor')
done
PID=$(echo "$R"|jq -r '.data.user.projectV2.id')
jq -s --arg v inv-v1 --arg ts "$(date -u +%FT%TZ)" --arg pid "$PID" '{query_version:$v,fetched_at:$ts,project_id:$pid,rows:(sort_by(.item_id))}' /tmp/inv_rows.jsonl > "$OUT"
shasum -a 256 "$OUT" | tee "$OUT.sha256"
```
驗證＝有效樣本實跑＋**DraftIssue 負控**（rows 中 content_type=="DRAFT_ISSUE" 者必出現——現板（2026-08-30）恰 1 筆為活控制組）；expected DraftIssue count 於裁定後釘入。artifact 顯示 DraftIssue 列數 0 後，讀相容方可移除；創建封閉與遺留可讀兩軸各有測試。

⛔ 非射程：不新增 wfcli 動詞；不動狀態語彙（歸切換 Initiative）；不改 canonical（W2A）。

**AC3 規格全文（card-face JSON schema，本卡唯一 owner 居所；勾選項僅指向此段）**：
3. （P1-30：本卡＝card-face JSON schema **唯一 owner**）sentinel 字面＝`<!-- card-face-form:v1:begin -->`／`<!-- card-face-form:v1:end -->`（⛔ 與 resource-claims 哨兵不同名、⛔ 不以「找到一個 JSON fence」定位）；完整 JSON Schema（draft 2020-12，writer／reader tests 對同一 validator 跑正負 fixture）：
```json
{"$schema":"https://json-schema.org/draft/2020-12/schema",
 "type":"object","additionalProperties":false,
 "required":["schema_version","stage_plan","tier_basis","list_convergence"],
 "properties":{
  "schema_version":{"const":"1"},
  "stage_plan":{"type":"array","minItems":1,"items":{"type":"object","additionalProperties":false,
    "required":["stage","goal"],
    "properties":{"stage":{"enum":["需求","研究","規劃","執行","審核","部署","維護","結案"]},
                  "goal":{"type":"string","minLength":1}}}},
  "tier_basis":{"type":"object","additionalProperties":false,
    "required":["sensitive_surfaces","recoverability","blast_radius"],
    "properties":{"sensitive_surfaces":{"type":"string","minLength":1},
                  "recoverability":{"type":"string","minLength":1},
                  "blast_radius":{"type":"string","minLength":1}}},
  "list_convergence":{"type":"array","items":{"type":"object","additionalProperties":false,
    "required":["issue_url","claim"],
    "properties":{"issue_url":{"type":"string","pattern":"^https://github\\.com/[^/]+/[^/]+/issues/[1-9][0-9]*$"},
                  "claim":{"enum":["covers","related"]}}}}}}
```
schema 外附加規則（validator 同步實作、各有拒收 fixture）：stage_plan 重複 stage 拒收；list_convergence 允許空陣列、重複 issue_url 拒收。**issue_url 裁定：⛔ 不允許 trailing slash／query／fragment**（正規形唯一）；拒收 fixture 四類＝repo 首頁／issues 列表頁／PR URL／issue number 為 0 或負；正例＝合法 issue URL。
升版規則＝v1 reader 對未知 `schema_version` **fail-closed 拒收**並指示走 migration（migration 屬未來版 owner）；tests 釘 round-trip／legacy 無區塊 fallback／同類兩區塊拒收／malformed 拒收／unknown version 拒收／與 resource-claims 共存
<!-- card-brief:end -->

## 核心痛點

- **痛點**：開卡速率高於可證明的推進速率下界（2026-08-29 快照 10 日差分：開卡 5.2 張/日；推進 **≥**3.9 次/日——日差分吃掉同日多次轉移，⛔ 不宣稱嚴格不等式）；⭐ 承重證據＝2026-08-28 一天四張同族卡（開卡產生器實例）；open 允許直接建 issue 與 DraftIssue（實測板上有 1 張 DraftIssue）、--acceptance 可為空、--core-pain 只驗非空。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/open_cmd.py",
    "file:cli/src/wf_cli/commands/amend_cmd.py",
    "file:cli/src/wf_cli/card.py",
    "file:cli/tests/",
    "file:.github/ISSUE_TEMPLATE/",
    "file:cli/src/wf_cli/card_face.py",
    "file:cli/src/wf_cli/intake.py",
    "file:cli/src/wf_cli/project.py",
    "file:cli/src/wf_cli/config.py",
    "file:cli/README.md",
    "file:docs/CONTRACT_TOOL_RECONCILE.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] `.github/ISSUE_TEMPLATE` 收件表單上線：五條件各一欄
- [ ] 1b.（P1-27）清單機制上線後同批建立**四個**清單項（W2A／W2B／W3′／切換 Initiative——內容逐字取 list-items.md）；oracle＝四 URL 存在且⛔ 不在 Project #4
- [ ] `open --from-issue <url>` 為唯一開卡路徑：直接建 issue 與 DraftIssue 兩分支移除；拒絕訊息含**跑得出**的補救指令
- [ ] （P1-30）card-face JSON schema 唯一 owner：sentinel 字面、draft 2020-12 全文、附加拒收規則與升版規則悉依本卡簡介「AC3 規格全文」段逐字實作（writer/reader 對同一 validator 跑正負 fixture）
- [ ] 驗收條件改必填（≥1）；--needs-deploy 移除
- [ ] 5. （P1-07 修訂）撤銷程序的**規則條文化歸 W2A**（requirement.md 生效時已含 ADD 撤銷邊與固定動作）；本卡僅於收件模板說明欄註記「降回清單＝PM 執行 deleteProjectV2Item＋轉移留言」，⛔ 不新增 CLI 動詞、⛔ 不先行生效任何 stage-rule
- [ ] 5b.（P1-26，唯一 owner＝本卡；退場 oracle 依需求方 2026-09-01 裁定甲修訂）既有 `amend` 動詞擴充 feature／routing 更新旗標（⛔ 非新增動詞；依 CLI 增量原則走三層評估）：write-set 含 Issue title＋`content.title`＋`功能` 欄＋routing 行，round-trip test 讀回驗證；以此通道同步 #177 的 routing（移除「不可逆狀態遷移」句改「W2A canonical T4 紅線」）與 title／功能——**退場 oracle：Issue title＋`content.title`＋`功能` 欄三項皆含「四波五卡」且零「五波施工」、routing 零「不可逆」字樣**。⚠️ Project 內建 `Title` 欄**退出**本判準（該欄無 writer、為 add-time 快照——五輪量測見 #217 issuecomment-5488724887）；實作對該欄仍分開讀回並印事實註記，⛔ 不得升為判準、⛔ 不得讀成「已同步」

## 驗證

- [ ] 對缺表單欄位的 --from-issue 實跑拒收（訊息含補救）
- [ ] 對舊路徑（直接建 issue／DraftIssue）實跑確認移除
- [ ] pytest 全綠
- [ ] 交付報告附 CLI 淨 LOC 變化（diff 產生）
- [ ] ⭐ W2A 的清單項用本機制實際升級一次＝驗收即實戰

## Log

- 2026-09-01T00:52:11+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-09-01T01:55:26+08:00 assign by wf-cli → owner session 250bf6e2-0c06-41e3-8570-3f14e311ef34@Claude Code（高階型）；分支worktree claude/wf-redesign-w1-execution-ef4e2d @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-redesign-w1-execution-ef4e2d；交付狀態 🔨執行中；實際能力層級 高階型（偏離卡面建議 主力型；偏離理由：高於建議（主力型）：執行 session 實際模型 claude-opus-5＝高階型；已知模式 CLI 改動上位無害，PM 接受不壓回（換 session 成本大於收益））；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-09-01T03:24:40+08:00 amend by wf-cli（op 25bb7461）→ 資源宣告：原值指紋 sha256:1b3a02f8a5442fc253d3d925dacabed66eb8d913543d2af959ec1f565be8e298 (298 bytes) → 新值指紋 sha256:c97220fd5812e0161b8bbf1dc0bf98ffd7ad6ba1fcc981a5619148bc0ebb08bb (371 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 執行者依紅線停下上呈之授權缺口補宣告（交付報告 §五逐檔理由：AC3 唯一 owner 自成模組×2、AC5b 需 Issue title writer、help/README 防謊言文件、對帳器 required 測試）；併行實查無交集。⚠️ 資源整份取代已含原五項。
- 2026-09-01T03:27:06+08:00 handoff by wf-cli → owner Codex@OpenAI（獨立查核）；iteration 0；SHA d747370229ccc5e93e099302b318f83d847f99b0；階段 執行；踩坑回應 13 族（已檢查 13／不適用 0／發現 0）；證據 執行者交付報告（session 250bf6e2，轉錄於 PM session）：AC1-5b 逐條、CI run 33427508105 headSha 逐字核對、PR #223 merge-result tests pass；踩坑 13 族逐條轉錄自執行者報告 §七（全 已檢查）；兩件上呈已 PM 處置（資源補宣告 op 25bb7461／清單項非逐字補充留待查核判 AC 符合性）。
- 2026-09-01T04:36:28+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 Codex@OpenAI（GPT-5，session 01a0596b-879f-7281-957c-44bd92208e50）；core_pain_resolved yes；self_run 10 項；findings 6 項（blocking 5）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-REDESIGN-W1-e0-d747370229ccc5e93e099302b318f83d847f99b0。
- 2026-09-01T12:09:20+08:00 amend by wf-cli（op fc632960）→ 驗收條件：原值指紋 sha256:fe6b33d88b9737a488223b175790583717cf7d1989d8def8b6dc1792945944d0 (1548 bytes) → 新值指紋 sha256:7fde1905a5a1e7bd2fd94a061e89c848249a09996261bf38d6670fb5d11d6b54 (1876 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方 2026-09-01 裁定甲：Project 內建 `Title` 欄退出 AC5b 退場 oracle，判準收為 Issue title＋content.title＋功能 欄三項（依據＝五輪實跑量測：無 writer／add-time 快照／母體零反例／讀者看不到／wfcli 零消費者，全文見 #217 issuecomment-5488724887，該留言由執行者 session 250bf6e2 轉錄裁定並自陳非需求方本人張貼）；本次由需求方於 PM session cc0a7952 逐字轉交執行。⚠️ --acceptance 整份取代：僅 5b 改動，其餘六條逐字照抄；驗證項未改動故不送（amend 對值未變欄位拒收）。
- 2026-09-01T12:32:31+08:00 handoff by wf-cli → owner Codex@OpenAI（獨立查核）；iteration 0；SHA 3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e；階段 審核；踩坑回應 8 族（已檢查 4／不適用 0／發現 4）；證據 R1 四筆歸執行者的 finding 修復完成，交回 R2。commit：e24fd95（C1′，只改 trailer 區塊）／5dbd87c（R1-1 讀回拆三面＋R1-2 空白與 no-op 拒收）／3fd9b3e（R1-1 裁定甲落地）。驗證：pytest 1610 passed/1 skipped rc=0；replay rc=0；contract_tool_reconcile --check rc=0；doctor --commit-trailers --require-planned-by 違規 0／合規 3 rc=0；CI push run 33468379494 與 pull_request run 33468385968（tests，required 那一支）皆 success，兩者 headSha 與本機 HEAD 及 PR #223 headRefOid 四者逐字元相同。留痕：交付報告 v2 issuecomment-5488574951、研究備忘與裁定甲 issuecomment-5488724887、v2 更正三則 issuecomment-5488821045。R1-3 歸 planner，本輪未動 #219-#222。⚠️ 兩點請 R2 知情：(1) 本次 handoff 由執行者本人執行，而派工包原本把它指定給 PM——需求方於本 session 直接指示，⛔ 非我自行擴權；(2) 踩坑報告答的是離開階段解析出的『審核』8 族（卡面 階段 欄自 R1 退回後停在審核未翻回執行），而我實際離開的是執行；該 8 族的族名是執行 13 族的前 8 個，故答案取自我實際做過的工作，⛔ 不是為不存在的審核工作填表。。
- 2026-09-01T12:59:07+08:00 handoff by wf-cli → owner session 250bf6e2-0c06-41e3-8570-3f14e311ef34@Claude Code；iteration 1；SHA d747370229ccc5e93e099302b318f83d847f99b0；階段 審核；踩坑回應 8 族（已檢查 5／不適用 0／發現 3）；證據 R1 裁決 REQUEST_CHANGES（issuecomment-5484232567，5 blocking）⇒ 退回執行者修復；本筆補記 審核→執行 之轉移（PM 退回清單逐筆轉錄於 PM session；R1-3 歸 planner 已由 PM 處置）。
- 2026-09-01T12:59:37+08:00 handoff by wf-cli → owner Codex@OpenAI（獨立查核）；iteration 1；SHA 3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e；階段 執行；踩坑回應 13 族（已檢查 12／不適用 0／發現 1）；證據 R1 修復第二輪：交付報告 v2（issuecomment-5488574951，執行者本人貼）＋更正三則（-5488821045）＋R1-1 裁定甲備忘（-5488724887）；PM 收件初審通過三項（注意事項實質性／AC 對應可見性／入口 SHA 綁定＝3fd9b3e）；PM 獨立實跑：三 commit trailers 各 4 欄解析、CI 兩支綠含 required tests（merge-result）、污染符全範圍 8＋C3 新增 0、七條 AC 皆有著落。
- 2026-09-01T13:11:39+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 Codex@OpenAI（gpt-5.6-sol，session 01a05afc-e755-7840-a9ff-f1c74c3670e7）；core_pain_resolved yes；self_run 10 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-REDESIGN-W1-e0-3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e。
- 2026-09-01T13:36:06+08:00 handoff by wf-cli → owner session 250bf6e2-0c06-41e3-8570-3f14e311ef34@Claude Code；iteration 2；SHA 3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e；階段 審核；踩坑回應 8 族（已檢查 7／不適用 0／發現 1）；證據 R2 裁決 REQUEST_CHANGES（issuecomment-5489219732，唯一 blocking R2-1）⇒ 退回執行者；本筆補記 審核→執行 之轉移。
- 2026-09-01T13:36:25+08:00 handoff by wf-cli → owner Codex@OpenAI（獨立查核）；iteration 2；SHA e84575a94a8f1730ab9d668d7f0ebcf425aa9cb2；階段 執行；踩坑回應 13 族（已檢查 12／不適用 0／發現 1）；證據 R2-1 修復（C4）：交付報告 v3＝issuecomment-5489384343（執行者本人貼，入口 SHA＝head）；PM 收件初審三項通過（族 1 值＝發現與失誤登記一致／AC 對應不變＋AC1b 收件合規已由第二 PM 閉合／入口 SHA e84575a＝source_sha＝PR headRefOid）；PM 獨立實跑：四 commit trailers 各 4 欄、CI 兩支綠含 required tests(33473821266)、超界措辭現行碼零殘留（(e) 段為刻意留證）、C4 污染符新增 0。
- 2026-09-01T13:45:00+08:00 review by wf-cli → APPROVE（✅通過）；查核者 Codex@OpenAI（gpt-5.6-sol，session 01a05afc-e755-7840-a9ff-f1c74c3670e7）；core_pain_resolved yes；self_run 10 項；findings 0 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-REDESIGN-W1-e0-e84575a94a8f1730ab9d668d7f0ebcf425aa9cb2。
- 2026-09-01T13:57:44+08:00 handoff by wf-cli → owner ruan6047；iteration 2；SHA f656a678e540d4083740e0f30f1214e887e42c04；階段 審核；踩坑回應 8 族（已檢查 6／不適用 0／發現 2）；證據 R3 APPROVE（issuecomment-5489479105，findings 0，source_sha e84575a）；PR #223 update-branch（BEHIND，零交集實查）後 squash merge→main f656a67；main 實跑：scanner 188 七項全零、pytest 1612 passed 1 skipped。⚠️ merge head fcfd66c≠審過 e84575a，差額＝PM 三筆 stage-rules/pm-conduct.md commit、與被審檔零重疊。⚠️ 合併 commit 的 trailer 因本文與區塊間缺空行而 interpret-trailers 解析 0 行（PM 失誤，main 不改寫；缺口已開清單項 #227）；⚠️ 未帶 --cleanup 且未帶 --repo-path，收尾清理未執行（worktree、本地分支、遠端分支皆未處理），狀態面已寫終態。


## Comment 5481588662 · 2026-08-31T16:54:10Z

open 寫入留痕（2026-09-01）：Project 簡介 TEXT 欄於 open 時因 GraphQL text 欄位長度上限拒收（規格全文 ~3.5k 字），body 權威居所已完整寫入、其餘欄位皆齊；PM 事後以導出摘要補該欄並註明非恆等。⛔ 依雙居所契約 body 哨兵為權威——讀規格一律讀 body。

## Comment 5481619507 · 2026-08-31T16:57:02Z

簡介欄上限實測補充（2026-09-01，需求方質疑 1024 後量測）：Project TEXT 欄上限＝**1024 UTF-8 bytes**（⛔ 非字元）——探針：ASCII x*1024 rc=0／x*1025 rc=1；中*341+x（恰 1024B）rc=0／中*342（1026B）rc=1；短多行 rc=0（換行不是拒因）。⇒ 中文簡介實際容量約 341 字。探針覆寫已還原為導出摘要（末次寫入即現值）。

## Comment 5482156427 · 2026-08-31T17:41:11Z

W1 前置留痕（2026-09-01）：需求方原裁定「封存」；實測推翻前提——archiveProjectV2Item 後 items 連線仍含該項（isArchived=true 但 producer 仍回 1 筆），封存無法達成 DraftIssue=0 的退場 oracle。改議「全文留痕後刪除」待需求方確認。以下為該 DraftIssue（WF-CARD-BODY-BUDGET1-PROBE-DRAFT1，#139 拋棄式探針）逐字全文備份：

---

# WF-CARD-BODY-BUDGET1-PROBE-DRAFT1 拋棄式探針：在真實 DraftIssue 上驗證 Log 退回全文

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 經濟型；拋棄式探針，只跑一次 amend 並讀回 Log；⛔ 不改任何生產碼。）　查核：待指派（建議 經濟型；查核只需核對 Log 行是否含 sha256 與退回理由字串；⛔ 無設計判斷。結論回寫 aiwf#139 的 V3。）
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：ROADMAP §0 目標 2「可稽核的內容」——`aiwf#139` 交付若把 V3 列為未驗，查核者無從判斷 draft 路徑是否真的 fail-safe，而該路徑一旦錯就是**不可逆的資料損失**（draft 卡沒有任何平台版本可還原）。

## 簡介
<!-- card-brief:begin -->
aiwf#139 的 V3 逐字要求「須用真實 draft item（Project 4 現有 0 張，須自建 throwaway），⛔ 不接受 mock」。本卡是為此建立的拋棄式載體。**適用時機**：僅此一次，做完即 🛑已停止。⛔ 非射程：不承載任何真實工作、不改生產碼、結論一律回寫 aiwf#139。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：`aiwf#139` 的 V3 需要在**真實** `DraftIssue` 上驗證「Log 退回寫全文」，而 Project 4 現有 0 張 draft ⇒ 缺載體，該條只能永遠列為未驗。⚠️ 而 canonical §6.4.2 逐字把「驗得了但沒驗」的揭露判為**替代勞動**，並以 `aiwf#129` 為據（派審包寫「未驗」，同一輪的 blocking finding 就是那一項，重現耗時不到兩分鐘）。⇒ 不建這張卡就等於把已知的攻擊向量交給查核者。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": []
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 這段舊驗收原文用來證明退路真的寫了全文而不是漏寫

## 驗證

- [ ] DV1 完整 stdout／stderr 與 rc 逐字附上。
- [ ] DV2 ⚠️ 射程：本卡證明的是「draft 路徑會退回全文」，⛔ 不是「所有退路都對」——另三條（totalCount=0／內容取回 null／舊值非 body 來源）由 aiwf#139 自己的測試承擔。

## Log

- 2026-08-26T00:12:11+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-26T00:13:08+08:00 amend by wf-cli（op 2d41a69c）→ 驗收條件：原值「[ ] D1 本卡的 `content_type` 實測為 `DraftIssue`（⛔ 非 Issue）。；[ ] D2 對它跑一次 `amend`，Log 新增行**不含** `sha256:`，且逐字載明退回理由 `content_type=DraftIssue`。；[ ] D3 ⭐ 負控：Log 必須含舊值**全文**（可辨識的連續字串），⇒ 證明退路真的走了寫全文而非漏寫。；[ ] D4 做完即 `handoff` 至 🛑已停止；結論逐字回寫 `aiwf#139` 的 V3。⛔ 本卡不留待辦。」→ 新值「這段舊驗收原文用來證明退路真的寫了全文而不是漏寫」（⚠️ 全文：content_type=DraftIssue（平台無 userContentEdits））；理由 D2/D3：在真實 DraftIssue 上驗證 Log 退回寫全文。
- 2026-08-26T00:14:57+08:00 handoff by wf-cli → owner —（已停止）；iteration 0；SHA d2d2ee95b12d237172cf2bcd2b681486e0ac9af5；證據 D1–D3 全部成立、DV1/DV2 已記。content_type=DraftIssue；Log 走全文格式（結構判準：指紋格式不命中、全文格式命中）；退回理由取自格式第 3 捕獲組為 content_type=DraftIssue（平台無 userContentEdits）；負控舊值 254 字元含開卡時的 D4 尾段 ⇒ 全文確實寫入。⛔ 本卡不承載真實工作、不留待辦。⚠️ 並登記：第一次驗證的三個檢查全部被卡片自身內容汙染（我把 sha256: 與 content_type=DraftIssue 寫進本卡驗收條文，又去 grep 那兩個字串）⇒ 零資訊，已改用結構判準重驗。結論回寫 aiwf#139 的 V3。；⚠️ 未帶 --cleanup 且未帶 --repo-path，收尾清理未執行（worktree、本地分支、遠端分支皆未處理），狀態面已寫終態。

## Comment 5482194215 · 2026-08-31T17:44:30Z

W1 前置完成（2026-09-01，需求方裁定：留痕後刪除）：deleteProjectV2Item 已執行（deletedItemId=PVTI_lAHOAvJcys4BfXPrzg3-THk；全文備份見前一留言）。raw inventory artifacts（inv-v1，producer 逐字照卡面）：artifact 1＝2026-08-31T17:12:11Z、214 rows、DRAFT_ISSUE 1 筆（活控制組）、sha256 482e6a7131500bc2fdc113cc2ca4b9b0b8db9f29146faa0712fac03a8120da32；artifact 2＝17:43:52Z、213 rows、DRAFT_ISSUE 0 筆、sha256 3da7110d27f27b33e4b00fa74cc92256b46984dd9e69758d168ed92dea94ead8。⇒ expected DraftIssue count 釘入＝0，讀相容移除條件成立。附註：中途曾照原裁定跑封存，實測 isArchived=true 仍在 items 連線（PM 前提未驗之失誤，已登記）；封存態已被刪除取代。

## Comment 5482328542 · 2026-08-31T17:56:35Z

階段留痕（2026-09-01，舊制看板過渡期）：本卡階段計畫之「需求→規劃→執行」前兩段——需求＝open 完成（規格住卡面）；規劃＝Initiative 層產出（P1 廿二輪跨家族審＋規劃 Gate @93bb8c0），本卡不另產出。assign 已將交付狀態置🔨執行中（閘門由此推斷現階段＝執行，與現實相符）；⛔ 不回填逆向轉移。執行者＝session 250bf6e2@Claude Code（高階型，偏離留痕見 assign Log）。

## Comment 5483941876 · 2026-08-31T20:13:00Z

交付報告（執行者本人貼；③ 之一部分）

# 交付報告 · WF-REDESIGN-W1（#217）執行 ③

- **session ID**：`250bf6e2-0c06-41e3-8570-3f14e311ef34`（`~/.claude/projects/-Users-ruanruan-Dev-ai-workflow--claude-worktrees-wf-redesign-w1-execution-ef4e2d/<id>.jsonl`）
- **實際模型行**：`claude-opus-5`（Opus 5）＝高階型。卡面建議 主力型 ⇒ **偏離（往上）**，PM 於 assign 已接受留痕（#217 Log 2026-09-01T01:55:26+08:00）。
- **分支**：`claude/wf-redesign-w1-execution-ef4e2d`　**worktree**：`/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-redesign-w1-execution-ef4e2d`
- **commit**：`d747370229ccc5e93e099302b318f83d847f99b0`（單一 commit）
- **spec 基線**：`93bb8c086f0cf8870537390511b5f0aa2d037c97`；本分支自 `46fe93d032f9055d9cd3c0279cf03c6daa57c0bb`（＝當時 main tip）分出。

## CI head_sha 核對

| 項目 | 值 |
|---|---|
| 本機 `git rev-parse HEAD` | `d747370229ccc5e93e099302b318f83d847f99b0` |
| CI run | `33427508105`（event=push，name=`CI`，conclusion=**success**） |
| CI `headSha` | `d747370229ccc5e93e099302b318f83d847f99b0` |
| 核對 | **相同**（逐字元） |

查詢方法：`gh run list --repo ruan6047/ai-workflow --branch claude/wf-redesign-w1-execution-ef4e2d --json databaseId,headSha,status,conclusion,name,event`

⚠️ 該 run 的 job 名是 `tests (branch head)`（非 `tests`）——CI 檔逐字：分支頭那一支永遠不是 required check，只是參考。**合併結果那一支尚未跑**（本分支還沒開 PR）。

---

## 一 · 做了什麼（事實；⛔ 不寫狀態）

### 新增檔

| 檔 | 行 | 內容 |
|---|---|---|
| `.github/ISSUE_TEMPLATE/list-intake.yml` | +78 | 收件表單，五條件各一欄；欄位標題逐字取自 `stage-rules/list-intake-requirements.md` 節名 |
| `cli/src/wf_cli/card_face.py` | +410 | 卡面表單：哨兵、draft 2020-12 schema 全文、子集走訪器、升版 fail-closed |
| `cli/src/wf_cli/intake.py` | +150 | 收件表單讀取端與可跑補救訊息產生器 |
| `cli/tests/test_card_face.py` | +280 | 37 條 |
| `cli/tests/test_intake.py` | +138 | 17 條 |

### 改動檔（淨 LOC，`git diff --cached --numstat` 產生）

| 檔 | + | − | 淨 |
|---|---:|---:|---:|
| `cli/src/wf_cli/card.py` | 151 | 6 | +145 |
| `cli/src/wf_cli/commands/open_cmd.py` | 270 | 36 | +234 |
| `cli/src/wf_cli/commands/amend_cmd.py` | 133 | 0 | +133 |
| `cli/src/wf_cli/project.py` | 14 | 0 | +14 |
| `cli/src/wf_cli/config.py` | 4 | 2 | +2 |
| `cli/README.md` | 13 | 6 | +7 |
| `docs/CONTRACT_TOOL_RECONCILE.md` | 2 | 0 | +2 |
| `cli/tests/*`（9 檔） | 758 | 40 | +718 |

**CLI 淨 LOC 變化**（卡面驗證項逐字要求，diff 產生）：

| 範圍 | + | − | 淨 |
|---|---:|---:|---:|
| `cli/src/wf_cli/`（產品碼） | 1132 | 44 | **+1088** |
| `cli/tests/` | 1078 | 40 | **+1038** |
| `cli/` 全部（含 README） | 2223 | 90 | **+2133** |
| 全 diff | 2303 | 90 | **+2213** |

### AC 逐條

1. **AC1 收件表單**：`list-intake.yml`，五欄（出處可指／是觀察不是結論／查重留痕／屬哪個 repo／提案者身分），全部 `required: true`。標題字面由 `wf_cli.intake.REQUIREMENTS` 持有，`tests/test_intake.py::test_the_form_exists_and_has_one_field_per_requirement` 以模板檔為來源逐字對照（含順序）。
2. **AC1b 四個清單項**：#219（W2A）／#220（W2B）／#221（W3′）／#222（切換 Initiative），2026-09-01 建立。oracle 兩半皆通過，見 §二。
3. **AC2 `--from-issue` 為唯一路徑**：`open_cmd` 的 `create_repo_issue`／`create_draft_item` 兩條分支移除（`test_open_has_no_way_to_create_an_issue_or_a_draft_item` 以 `hasattr` ＋原始碼字面雙重釘住）。四種拒收全部零遠端寫入：URL 非正規形／缺表單欄位／body 已是卡面／issue 已在板上。
4. **AC3 card-face JSON schema**：sentinel `<!-- card-face-form:v1:begin -->`／`<!-- card-face-form:v1:end -->`；schema 全文逐字自卡 body 搬入 `SCHEMA_TEXT`；`validate()` 同時被 writer（`render_block`）與 reader（`parse_block`）呼叫。
5. **AC4**：`--acceptance` 改 `required=True` ＋ 空白字串硬拒；`--needs-deploy` 移除，部署狀態初值改由 `--stage-plan` 是否含 `部署` 導出。
6. **AC5**：撤銷註記「降回清單＝PM 執行 deleteProjectV2Item＋轉移留言」逐字寫進表單說明欄。⛔ 未新增任何 CLI 動詞（`test_the_card_adds_no_cli_verb_for_revocation` 掃 `COMMAND_MODULES`）、⛔ 未生效任何 stage-rule（本次 diff 未動 `stage-rules/`）。
7. **AC5b `amend` 擴充**：`--feature` ＋ 六個 routing 旗標。#177 已實跑同步，退場 oracle 通過，見 §二。

### 刻意決策（各自就地留了註解）

- **DraftIssue 的「讀取相容」刻意保留**。卡面驗收 2 逐字只要求「直接建 issue 與 DraftIssue **兩分支**移除」——那兩個分支在 `open_cmd`，已移除。卡面簡介另一句「artifact 顯示 DraftIssue 列數 0 後，讀相容**方可**移除」，其**下一句**是「創建封閉與遺留可讀**兩軸各有測試**」⇒ 遺留可讀是要留著並被測的那一軸。⇒ `project.list_items`／`set_item_body`／`review`／`checkpoint`／`amend` 的 DraftIssue 讀取路徑一個字都沒動，並新增 `fake_gh.seed_legacy_draft_card` 當那一軸的輸入端（`test_draft_issue_card_always_falls_back_to_full_text`、`test_assign_blocks_draft_issue_card`、`test_draft_item_without_issue_timeline_is_rejected`、`test_amend_feature_is_unavailable_on_a_legacy_draft_card` 四條）。⚠️ **這是判斷不是疏漏**；PM 若裁定「連讀相容一起移除」，那是另一次改動。
- **`--needs-deploy` 的取代者選定為階段計畫**：`docs/research/WORKFLOW-REDESIGN-2026-08-30.md` §一第 12 列逐字（被取代者＝該旗標；取代者＝開卡表單「階段計畫」；唯一 owner＝W1），且 `archive/wave-specs/w1.md` frontmatter 逐字 `replacement_rows: [12]`。⇒ `stage_plan` 含 `部署` ⇒ `⏸未部署`，否則 `—不適用`。
- **`list_convergence` ⛔ 不自動填入 `--from-issue` 自己**：升級後那個 issue **就是**本卡，指向自己是退化的。
- **`_ecma_regex`**：JSON Schema 的 `pattern` 是 ECMA-262 語意，其 `$` 只匹配字串真結尾；Python 的 `$` **也**匹配結尾換行之前 ⇒ 直接 `re.compile` 會放行 `".../issues/1\n"`（JSON 字串裝得下換行）。已釘成拒收 fixture `結尾換行`。
- **`validate_issue_url` 訊息不寫 `PR` 那兩個大寫字母**：`scripts/contract_tool_reconcile.py` 以詞界比對卡面欄位名，而 `templates/tasks-card.md` 有同名欄位 ⇒ 一個流進遠端寫入的字串裡出現該 token 會把該欄位判定由 `mention-only` 翻成 `write-only`。那個翻轉是**假的**（本模組一個字都沒寫進該欄位）。

### ⚠️ 污染符（決議 §二）在本 diff 的命中，逐處交代

`git diff origin/main..HEAD | grep -E '^\+.*(needs-deploy|spec-dir|claim 事件|events.jsonl|workflow_ledger|control-plane|Discovery lead)'` 共 **7 處**，⛔ 沒有一處把它當現行機制：

| # | 位置 | 性質 |
|---|---|---|
| 1–2 | `open_cmd.py` `DEPLOY_STAGE` docstring | 逐字說明「這是 `--needs-deploy` 的取代者」，並指名決議 §一第 12 列 |
| 3 | `open_cmd.py` `--stage-plan` 的 help | 同上，一句話交叉引用 |
| 4 | `open_cmd.py` `deployment_status=` 上方註解 | 「⛔ 不再有 `--needs-deploy`」 |
| 5–6 | `test_commands_mocked.py::test_needs_deploy_flag_is_gone` 的名字與斷言 | 斷言**該旗標不存在**，字面是被斷言的對象本身 |
| 7 | `open_cmd.py` `--spec-dir` | **diff 假陽性**：該旗標未改動，只因整檔重寫而顯示為 `+` 行。它是取代清單第 10 列，owner＝W3′，⛔ 不在本卡射程 |

---

## 二 · self_run 實跑紀錄（真 GitHub／真 Project #4）

### R1 · 缺表單欄位的 `--from-issue` 拒收（卡面驗證項一）

```
$ uv run --project cli wfcli open LIVE-REFUSAL-PROBE1 --owner ruan6047 --project 4 \
    --repo ruan6047/ai-workflow --from-issue https://github.com/ruan6047/ai-workflow/issues/213 ...
[open] 拒絕（未寫入任何狀態）：https://github.com/ruan6047/ai-workflow/issues/213 缺收件表單欄位
['出處可指', '是觀察不是結論', '查重留痕', '屬哪個 repo', '提案者身分']——五條件各一欄，缺任一項即退回提案者補
（stage-rules/list-intake-requirements.md，⛔ PM 不代填）。
⇒ 補齊後重跑。缺的 5 欄可用下列三行補進原 issue（已代入實際 repo 與編號）：
    gh issue view 213 --repo ruan6047/ai-workflow --json body --jq .body > /tmp/intake-213.md
    printf '\n### 出處可指\n\n<在此填寫>\n…' >> /tmp/intake-213.md
    gh issue edit 213 --repo ruan6047/ai-workflow --body-file /tmp/intake-213.md
rc=2
```

**補救指令可跑性實測**：第 1 行實跑 rc=0、產出 1,014 bytes；第 2 行實跑 rc=0、檔案增為 1,198 bytes、`grep -c '^### '` ＝ **5**。
⛔ **第 3 行刻意未跑**——它會改動 #213 的 body，而本次只驗訊息可跑，⛔ 不是要修那張清單項。

### R2 · 舊路徑實跑確認移除（卡面驗證項二）

```
$ uv run --project cli wfcli open LIVE-OLDPATH-PROBE1 --owner ruan6047 --project 4 --repo ruan6047/ai-workflow …（不給 --from-issue）
wfcli open: error: the following arguments are required: --from-issue
rc=2
```

**兩次拒收的零寫入複驗**（看被改變的狀態，⛔ 不看 rc）：Project #4 items 在拒收前後同為 **213**；以逐字比對兩個探針卡ID（`LIVE-REFUSAL-PROBE1`／`LIVE-OLDPATH-PROBE1`）掃全部 213 個 item 的 `卡ID` 欄，**0 命中**。

### R3 · AC1b oracle

| 項 | issue | state | 在 Project #4？ | 五欄齊？ |
|---|---|---|---|---|
| W2A | https://github.com/ruan6047/ai-workflow/issues/219 | OPEN | **否** | 是 |
| W2B | https://github.com/ruan6047/ai-workflow/issues/220 | OPEN | **否** | 是 |
| W3′ | https://github.com/ruan6047/ai-workflow/issues/221 | OPEN | **否** | 是 |
| 切換 Initiative | https://github.com/ruan6047/ai-workflow/issues/222 | OPEN | **否** | 是 |

「在 Project #4？」的量法：分頁走完全部 213 個 item，逐一取 `content.number` 與四個編號比對。「五欄齊」的量法：`gh issue view --json body` 取回 body，餵 `wf_cli.intake.missing_requirements`，四張皆回空清單。

### R4 · AC5b 退場 oracle（#177）

```
$ uv run --project cli wfcli amend WF-REDESIGN1 --owner ruan6047 --project 4 --repo ruan6047/ai-workflow \
    --reason "…" --feature "工作流框架重整：8 階段 × 10 狀態、清單制、四波五卡施工（Initiative 父卡）" \
    --exec-capability-reason "Initiative 父卡的規劃與協調屬架構層；子卡含 W2A canonical T4 紅線，取風險最高者"
[amend] 卡面預算：本次 +801 字元／寫入後 15,984／上限 129,486／餘裕 113,502
[amend] 已修訂 WF-REDESIGN1（op 1eb573ce，2 個欄位，原值指紋已寫入 Log（原文見平台前一版））
rc=0
```

（先跑過 `--dry-run`，輸出與正式跑逐字相同，rc=0。）

| 欄 | 值 | 含「四波五卡」 | 含「五波施工」 |
|---|---|---|---|
| Issue title | `WF-REDESIGN1 工作流框架重整：8 階段 × 10 狀態、清單制、四波五卡施工（Initiative 父卡）` | ✅ | ❌ |
| Project item title | 同上 | ✅ | ❌ |
| `功能` 欄 | `工作流框架重整：8 階段 × 10 狀態、清單制、四波五卡施工（Initiative 父卡）` | ✅ | ❌ |

routing 行改後：
`- 執行：待指派（建議 高階型；Initiative 父卡的規劃與協調屬架構層；子卡含 W2A canonical T4 紅線，取風險最高者）　查核：待指派（建議 高階型；波 2 為 canonical 紅線改版，查核須跨模型家族或需求方 sign-off——獨立性要求疊加於層級之上；本卡總驗收對照服務目標三項）`
含「不可逆」＝**否**。⇒ **退場 oracle 三項全通過。**

⚠️ **改動前 Issue title 已含「四波五卡」**（只有 `功能` 欄殘留「五波施工」）⇒ title 那一次寫入在值上是 no-op；它仍被送出並讀回驗證。⛔ 不得由「三欄皆通過」推出「三欄都被本次改動改過」。
⚠️ 查核側理由未動（它不含「不可逆」）——卡面只要求改「不可逆狀態遷移」那一句，⛔ 我不擴權。

### R5 · pytest

```
$ cd cli && uv run pytest -q
1606 passed, 1 skipped in 64.02s
rc=0
```
基線（改動前，`46fe93d`）：`1528 passed, 1 skipped`。差 **+78 條**（新增 37＋17＋24）。

```
$ uv run --no-project --python 3.12 scripts/replay_escalation_rules.py
rc=0
```

### R6 · DraftIssue 負控的獨立複驗

我自己跑一次分頁盤點：Project #4 items **213**、`type == "DRAFT_ISSUE"` **0**。與 PM 前置 inv-v1 artifact #2（213 rows／DRAFT_ISSUE 0）**相符**。
⛔ 這**不是**對 PM artifact 的 sha256 核對（我沒有那兩個檔），只是同一個查詢在 2026-09-01 的重跑結果相同。

### R7 · AC3 schema 與卡面逐字相同（實跑）

```
$ python3 -c '取 gh issue view 217 body 內 AC3 段的第一個 ```json fence，與 wf_cli.card_face.SCHEMA_TEXT 逐字比對'
卡面 fence 與 SCHEMA_TEXT 逐字相同： True
```

### R8 · 對帳器

```
$ uv run --project cli python scripts/contract_tool_reconcile.py --check
rc=0
```

---

## 三 · 失誤登記（逐項；⛔ 不摘要、⛔ 不加緩和語）

1. **違反「⛔ 不截斷輸出」**。基線 pytest 我跑 `uv run pytest -q 2>&1 | tail -5`，`echo "rc=${PIPESTATUS[0]}"` 印出空值（zsh 用 `pipestatus`）⇒ **那一次基線跑的 rc 根本沒取到**，我只憑 stdout 的「1528 passed」判斷它綠。之後另有三次也用了 `| tail`。第四次起改成寫檔＋分開取 rc。⇒ 基線那筆的 rc 至今**未取得**，⛔ 不宣稱它是 0。
2. **零寫入複驗的比對條件寫太寬**。我用 `卡ID.startswith("LIVE-")` 掃殘留探針，命中一張與本次無關的既有卡 `LIVE-WORKER-RESCHEDULE-FILTER1`，差一點被我讀成「拒收留下了殘留」。正確比對是逐字對兩個探針卡ID；§二 R2 的數字已是改用逐字比對後重跑的。
3. **`card_face.py` 第一版寫壞兩處**：`_ecma_regex` 定義在 `ISSUE_URL_PATTERN` 之後 ⇒ 模組載入 `NameError`；docstring 非 raw string 且含 `\Z` ⇒ `SyntaxWarning: invalid escape sequence`。同一次執行內發現並修正。
4. **`validate_issue_url` 的第一版訊息含 `PR URL` 字面**，讓 `contract_tool_reconcile` 把卡面欄位 `PR` 的判定由 `mention-only` 翻成 `write-only`（假陽性），`test_live_dispositions_cover_every_gap` 因此紅。改寫措辭後恢復。
5. **工作目錄漂移**：`cd cli` 後未回到 worktree 根，之後三次相對路徑指令回 `No such file or directory`。改用絕對路徑。
6. **違反 worktree 路徑紀律**。寫完報告後我跑 `cp $SP/WF-REDESIGN-W1-delivery-report.md .../worktrees/wf-redesign-w1-execution-ef4e2d/../../../WF-...md`，該相對路徑解析到**主 checkout 的 repo 根** `/Users/ruanruan/Dev/ai-workflow/`，於是在主 checkout 留下一個未追蹤檔（`git status --porcelain` 顯示 `?? WF-REDESIGN-W1-delivery-report.md`）。⇒ 這是 §六 #1 那一條的**實際違反**，⛔ 不得由 §六 #1 的「已遵循」推出全程零違反。已 `rm` 移除，移除後主 checkout `git status --porcelain` 為空。⚠️ 該檔僅存在約 1 分鐘、未被 commit、未進任何分支。
7. **`test_amend.py` 新增的 helper 與既有 `_routing_line` 同名**，一次覆寫掉既有 helper、25 條測試轉紅。改名為 `_card_routing_line`。

---

## 四 · 未驗清單（逐項＋各自原因；⛔ 不摘要）

1. **⭐ W2A 清單項的實際升級未跑**。原因：派工包逐字「W1 審核通過後由 PM 於 W2A 開卡時實戰，⛔ 你不用預跑」。⇒ `open --from-issue` 的**成功路徑在真實 GitHub 上一次都沒跑過**，只跑過四種拒收路徑。
2. **GitHub Issue Forms 的實際渲染輸出未實測**。`### <label>` 這個形狀是我依 GitHub 的已知行為寫的；#219–#222 是我以 `gh issue create --body` 手工組出來的 body，⛔ **不是**經表單送出的。⇒「照這份表單填出來的 body 真的長這樣」**未驗**，而整條升級路徑的定位錨點就建在它上面。**這是本卡最承重的未驗項。** 複驗方法：在瀏覽器用該模板開一張 issue，把產出的 body 餵 `wf_cli.intake.missing_requirements`。
3. **`set_issue_title` 之後 Project item title 的平台導出延遲未量測**。fake 是同步更新；真實環境我只有 #177 這一次成功讀回（同一條指令內），n=1。⇒ 若真實導出有延遲，`amend --feature` 會回 rc=8 並要求重跑——那條路徑**未在真實環境觸發過**。
4. **`amend --feature` 對 DraftIssue 卡的拒收只在 mock 上驗過**。板上 `DRAFT_ISSUE` 為 0 ⇒ 真實環境無樣本可跑。
5. **卡面表單走訪器未與任何真正的 draft-2020-12 實作對照**。`cli/pyproject.toml` `dependencies = []`，我刻意不引入 `jsonschema`。⇒ `additionalProperties: false`／`minItems`／`const` 的語意由我自寫的子集實作，正確性只由本檔 fixture 支撐。`_assert_schema_is_understood` 只保證「schema 沒用到走訪器不懂的關鍵字」，⛔ 不保證「懂的那些實作對」。
6. **`docs/CONTRACT_TOOL_RECONCILE.md` 新增的兩筆 disposition 值抄自對帳器輸出**，⛔ 我未獨立判斷那四個守衛「該不該」在 `card.py`／`amend_cmd.py` 的寫入路徑上跑。形狀沿用既有的 `→brief` 兩列先例。
7. **`wfcli doctor` 未跑**。原因：它是唯讀報告工具，本次沒有它才答得出的問題；⛔ 但這代表「本次改動有沒有讓 doctor 對既有 213 張卡的判定改變」**未驗**。
8. **`--spec-dir` 路徑未跑**。本次 open 的所有實跑與測試都沒帶它；它是取代清單第 10 列、owner＝W3′。
9. **合併結果（`refs/pull/N/merge`）上的 CI 未跑**——本分支尚未開 PR。⛔ 不得由分支頭綠推出合併結果綠（CI 檔逐字記著 2026-08-12 的反例）。

---

## 五 · 授權缺口：實際寫入集**超出**卡面宣告（⚠️ 停下上呈）

卡面 `resource-claims` 宣告：`open_cmd.py`／`amend_cmd.py`／`card.py`／`cli/tests/`／`.github/ISSUE_TEMPLATE/`。

**實際另動 6 個檔**，逐項理由：

| 檔 | 淨 | 為什麼非動不可 |
|---|---:|---|
| `cli/src/wf_cli/card_face.py`（新） | +410 | AC3 逐字「本卡＝card-face JSON schema **唯一 owner**」。哨兵區塊的 owner 在本 repo 一律自成模組（`resources.py`／`brief.py` 兩個先例）；塞進 `card.py` 會讓 2,236 行的檔再長 400 行，且 owner 關係看不出來 |
| `cli/src/wf_cli/intake.py`（新） | +150 | AC1／AC2 的收件檢查與補救訊息產生器。同上，讀取端自成模組 |
| `cli/src/wf_cli/project.py` | +14 | 只加了 `set_issue_title` 一個函式（AC5b 寫入集的「Issue title」必須有 writer）。替代方案是在 `open_cmd` 與 `amend_cmd` 各自直接組 `gh issue edit` 呼叫 ⇒ 同一個 gh 呼叫形狀出現兩份，那是本 repo 已登記過的形狀 |
| `cli/src/wf_cli/config.py` | +2 | `--repo` 的 help 逐字寫著「未給則建立 Project draft issue」，AC2 之後**該句為假**。⛔ 留著等於交付一份說謊的 `--help` |
| `cli/README.md` | +7 | 動詞表與「跨專案目標指定」節同樣描述已被移除的行為 |
| `docs/CONTRACT_TOOL_RECONCILE.md` | +2 | `test_live_dispositions_cover_every_gap` 是既有 required 測試；新模組帶進兩個守衛缺口，不登記處置就是紅的。⛔ 「刪掉一列讓它變綠」被該對帳器明文擋住 |

⇒ **請 PM 以 `wfcli amend WF-REDESIGN-W1 --resources …` 把宣告補齊**（我⛔ 不動看板）。建議值：原五項 ＋ `file:cli/src/wf_cli/card_face.py`、`file:cli/src/wf_cli/intake.py`、`file:cli/src/wf_cli/project.py`、`file:cli/src/wf_cli/config.py`、`file:cli/README.md`、`file:docs/CONTRACT_TOOL_RECONCILE.md`。

⚠️ 併行風險實查：同期唯一在飛的 worktree `wf-control-plane-type-registry1` 只改 `templates/control-plane-contract.md`（`git diff --stat origin/main...origin/claude/WF-CONTROL-PLANE-TYPE-REGISTRY1` ＝ 1 檔）⇒ 本次越界**沒有**造成實際交集。⛔ 這不等於宣告可以不補。

## 五之二 · 四個清單項的內容：兩處**非逐字**補充（⚠️ 上呈）

AC1b 逐字「內容逐字取 `list-items.md`」。該檔給的「查重＝彼此互指＋WF-REDESIGN1」與「提案者身分＝PM session cc0a7952（transcript 可核）」**填不滿** `stage-rules/list-intake-requirements.md` 條件 3（逐字列出搜過的關鍵字）與條件 5（三格）。

我的處置：**觀察句一個字都沒動**；兩欄各保留來源原句，其後以 `⚠️ 以下…**非** list-items.md 原文` 明確分隔，補上：

- 查重欄：我實際跑過的四條 `gh issue list --search` 指令與命中（`#217`／`#177`／`#213`）
- 身分欄：`GitHub 帳號：ruan6047`（本 issue 的 author 欄即為此，可核）；**訊息定位那一格逐字寫「⛔ 來源檔未給，⛔ 不代填、⛔ 不推定」**

⇒ 若 PM 認為連這兩處補充都算偏離「逐字」，四張的 body 可直接 `gh issue edit` 改回純原文；⛔ 但那樣它們就過不了自己這道收件閘門。

---

## 六 · 決議 §八「執行 12」逐條三值＋evidence

| # | 注意事項 | 三值 | evidence |
|---|---|---|---|
| 1 | worktree 路徑紀律 | **發現：**一次違反（失誤 6：`cp` 的相對路徑解析到主 checkout 的 repo 根，留下一個未追蹤檔）。**處置**＝`rm` 移除，移除後主 checkout `git status --porcelain` 為空 | 除該次外，所有 Edit／Write／pytest 都在 `/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-redesign-w1-execution-ef4e2d` 內。失誤 5 是工作目錄漂到 `cli/`（仍在 worktree 內），⛔ 不是跨 checkout |
| 2 | （並行共用 checkout 時）逐檔 add、SHA rev-parse | **不適用**：本次是**獨立 worktree**、非共用 checkout；`git status --porcelain` 在 commit 前只有本次改動的 21 個路徑 |
| 3 | ⛔ 不截斷輸出 | **發現：**見失誤 1（四次 `| tail`，其中基線那次 rc 未取到）。**處置**＝改成 `pytest -q > <檔> 2>&1; echo rc=$?`，全量輸出留在 scratchpad 的 `t1`–`t9`；本報告所有數字取自未截斷的那幾份 |
| 4 | rc=0 ⛔ 非成功看狀態 | **已遵循** | 兩次拒收另外量了**被改變的狀態**：Project #4 item 數 213→213、探針卡ID 逐字 0 命中。amend 之後另外重讀 Issue／Project 兩處欄位比對，⛔ 不以 `rc=0` 代替 |
| 5 | 宣告成功前核執行識別碼 | **已遵循** | CI run `33427508105` 的 `headSha` 與本機 `git rev-parse HEAD` 逐字元比對（§CI 表）；amend 的 `op 1eb573ce` 記在 §二 R4 |
| 6 | 驗證器 import ⛔ 不重打 | **已遵循** | `card_face`／`intake` 皆 `from .brief import _reuse_probe`（即 `resources._split_at_log` 的行為探測），⛔ 未自寫第二份；`intake` 的 `REQUIREMENTS` 被 `fake_gh.COMPLETE_INTAKE_BODY` 與 `test_intake` 直接 import；`ISSUE_URL_PATTERN` 由 `SCHEMA` 取出、⛔ 未重打；`test_amend` 的 routing round-trip 用 `compare_capability_to_card`（assign 真正會跑的那條），⛔ 未自寫正則 |
| 7 | 複驗用會通過的樣本 | **已遵循** | `test_amend_runs_the_guard_before_any_remote_write` 沿用既有的「乾淨值 ＋ rc=0」設計；AC5b 的實跑對 #177 先 `--dry-run`（rc=0）再正式跑（rc=0），⛔ 不以被拒收的樣本推論順序 |
| 8 | 算術不可能最先響 | **已遵循** | 基線 1528＋新增 37＋17＋24 ＝ 1606，與實跑數字相符；LOC 表的四個範圍值由同一份 `--numstat` 聚合，逐檔加總可覆算 |
| 9 | 刻意行為就地留註解 | **已遵循** | 六處刻意決策各自帶 (a) 現在的行為／(b) 為什麼／(c) ⛔ 不得推出什麼：`open_cmd` 模組 docstring 的 DraftIssue 讀相容、`DEPLOY_STAGE`、`_ecma_regex`、`validate_issue_url` 措辭、`intake.read_form` 的排版例外吞法、`fake_gh.forget_revisions` |
| 10 | 修過期最易留新過期 | **發現：**改 `open` 之後 `config.py --repo` 的 help 與 `cli/README.md` 三處立刻變成過期文字。**處置**＝同一個 commit 一併改（見 §五），⛔ 不留到後續 |
| 11 | 交付物寫事實 ⛔ 不寫狀態 | **已遵循** | 本報告不寫「已 push」「已綠」，改寫查詢方法＋當次識別碼（run id／op id／head_sha／item 數） |
| 12 | 失誤登記與未驗清單逐項 ⛔ 不摘要 ⛔ 不加緩和語（＋「全部」附 artifact 窮舉證據） | **已遵循** | §三 七項、§四 九項逐項列出。**「全部」的兩處宣稱各自附窮舉證據**：(a) 污染符 7 處由 `git diff \| grep -E` 產生（§一末表）；(b) 四個清單項「⛔ 不在 Project #4」由分頁走完全部 213 個 item 逐一比對產生，⛔ 不是抽查 |

---

## 七 · 踩坑族清冊（`pitfalls.roster_for("執行")`，13 族逐條裸值）

| # | 族名 | 值 | evidence |
|---|---|---|---|
| 1 | 宣稱超過證據 | 已檢查 | §四 逐項寫明未驗；§二 R6 明寫「不是 sha256 核對」；§二 R4 明寫 title 那一次是值上 no-op |
| 2 | 列舉或覆蓋不完整 | 已檢查 | `_assert_schema_is_understood` 在模組載入期擋下走訪器不懂的關鍵字與型別；`_UNDERSTOOD_KEYWORDS`／`_TYPE_CHECKS` 是封閉集合 |
| 3 | 交付未落地或未接線 | 已檢查 | 四個清單項與 #177 的改動都在真實 GitHub 上、URL 可查；`--from-issue` 的成功路徑在真實環境**未跑**（§四 1） |
| 4 | 文件與現實漂移 | 已檢查 | `config.py` help、`cli/README.md` 三處、`docs/CONTRACT_TOOL_RECONCILE.md` 同一個 commit 一併更新（§六 #10） |
| 5 | 狀態轉移或生命週期 | 已檢查 | 部署狀態初值改由 stage_plan 導出，兩個方向各有測試（`test_open_derives_initial_deployment_status_from_the_stage_plan` 同時斷言 `⏸未部署` 與 `—不適用`） |
| 6 | 可重現性不足 | 已檢查 | 四個清單項由 scratchpad 的 `mk_list_items.py` 產生（可重跑，不帶 `--apply` 只印 body）；oracle 的兩個量法在 §二 R3 寫明 |
| 7 | 並發或時序不安全 | 已檢查 | `amend` 既有的「寫入前重讀比對 body」未改動，其非原子性的誠實聲明仍在模組 docstring；`set_issue_title` 之後的平台導出延遲**未量測**（§四 3） |
| 8 | 資源或寫入集宣告 | 已檢查 | §五 逐檔列出越界與理由，並實查併行卡無交集 |
| 9 | 守衛涵蓋不足或可被繞過 | 已檢查 | `card_face.parse_block`／`try_parse_block` 第一參數為 `body` 且其餘有預設 ⇒ 自動進 `card.body_read_paths()` 的寫入邊界守衛；`enforce_card_render_boundary` 另加「卡面表單」的往返比對 |
| 10 | 身分或歸屬對應錯誤 | 已檢查 | `open` 的 repo 由 `--from-issue` URL 決定（＝registry 軸 A 的判定基準），`--repo` 不一致即拒收；清單項身分欄的缺格逐字標為未給、⛔ 不代填 |
| 11 | 程序或規格照字面不成立 | 已檢查 | 兩處逐字要求彼此有張力（「讀相容方可移除」vs「兩軸各有測試」），已在 §一 與 `open_cmd` docstring 逐字引兩句並說明取捨；AC1b 的「逐字」與收件五條件的張力見 §五之二 |
| 12 | 留痕失真或遺失 | 已檢查 | 升級在 Log 記來源 URL ＋ 清單項原文 sha256（原文由平台 `userContentEdits` 保存）；⚠️ 代價明說＝離線讀 Log 只拿得到指紋 |
| 13 | 解析或正規化錯誤 | 已檢查 | `_ecma_regex` 修掉 `$` 的 Python／ECMA 語意差，並釘成 `結尾換行` 拒收 fixture；哨兵定位一律走 `resources._split_at_log`，⛔ 未自寫 markdown 解析；重複標題一律 fail-closed、⛔ 不取第一個 |

---

## 八 · 給查核者的入口

- 分支 `claude/wf-redesign-w1-execution-ef4e2d` @ `d747370229ccc5e93e099302b318f83d847f99b0`
- `cd cli && uv run pytest -q`（期待 1606 passed, 1 skipped）
- `uv run --no-project --python 3.12 scripts/replay_escalation_rules.py`（期待 rc=0）
- `uv run --project cli python scripts/contract_tool_reconcile.py --check`（期待 rc=0）
- AC3 的規格是**卡 #217 body 的「AC3 規格全文」段**；`cli/src/wf_cli/card_face.py::SCHEMA_TEXT` 應與它逐字相同
- ⛔ 我未 merge、未開 PR、未動看板欄位（除 AC5b 逐字要求的 #177 三欄與 routing 行）


## Comment 5484232567 · 2026-08-31T20:36:32Z

<!-- wf-review-event:v1 card_id=WF-REDESIGN-W1 source_sha=d747370229ccc5e93e099302b318f83d847f99b0 attempt_id=WF-REDESIGN-W1-e0-d747370229ccc5e93e099302b318f83d847f99b0 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-REDESIGN-W1`　attempt_id：`WF-REDESIGN-W1-e0-d747370229ccc5e93e099302b318f83d847f99b0`
- 查核者：Codex@OpenAI（GPT-5，session 01a0596b-879f-7281-957c-44bd92208e50）　escalation_epoch：0
- source_sha：`d747370229ccc5e93e099302b318f83d847f99b0`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-09-01T04:36:28+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git status --short --branch; gh pr view 223 --json headRefOid,baseRefOid,statusCheckRollup,commits`
  - 唯讀 worktree HEAD=d747370229ccc5e93e099302b318f83d847f99b0、parent/base=46fe93d032f9055d9cd3c0279cf03c6daa57c0bb、單一 commit、工作區乾淨；PR branch-head 與 merge-result 的 tests 皆 SUCCESS。
- `cd cli && uv run pytest -q`
  - 1606 passed, 1 skipped in 76.11s；rc=0。
- `uv run --with jsonschema python <AC3 differential probe>; node <ECMA-262 pattern probe>`
  - #217 AC3 第一個 JSON fence 與 card_face.SCHEMA_TEXT 逐字相同；Draft202012Validator.check_schema 通過，10 組 schema 關鍵字正負案例與自寫 validate() 零分歧；Node RegExp 對合法 URL=true、結尾換行=false，_ecma_regex 的當前轉譯判斷成立。
- `web open GitHub official github/issue-parser README and GitHub issue-form schema`
  - GitHub 官方 issue-parser 以 `### The Name of the Thing` 示範 issue-form label 的輸出，且列 textarea 空值為 `_No response_`；足以支持 intake 的兩個承重字面。未建立真 issue，因此不冒充實際表單送出 smoke test。
- `gh issue view 219..222; gh project item-list 4 --owner ruan6047 --format json --limit 1000; compare stage-rules/list-intake-requirements.md`
  - 四 URL 均 OPEN 且依 repo+number 比對均不在 Project #4；list-items.md 的觀察句與共同欄原文均保留。但四份 body 都明載訊息定位未給，且沒有另一 PM 的收件裁決者身分與時間，違反生效規則條件 5 與 PM 自提案條款。
- `sealed FakeGhRunner probe: amend --feature with current value, then whitespace-only value`
  - 相同值回 rc=0 並寫入「示範功能→示範功能」Log；三個空白亦回 rc=0，最後 功能='   '、title='FEATURE-PROBE1    '。兩條都發生遠端替身寫入。
- `gh issue view 177; branch project.list_items() read Snapshot.title, fields['Title'], fields['功能']; gh project item-list --format json`
  - Issue/content.title 與 功能 欄含「四波五卡」；但 Project `Title` 欄／gh item-list 頂層 title 仍是「五波施工」。實作的 after_item.title 讀 content.title，沒有讀獨立的 fields['Title']，故 AC5b 三欄退場 oracle 未通過。
- `git diff 46fe93d..d747370 | grep -E '^\+.*(needs-deploy|spec-dir|claim 事件|events.jsonl|workflow_ledger|control-plane|Discovery lead)'`
  - 8 處命中，不是交付報告的 7；漏列 card_face.py:23 的 --needs-deploy 取代說明。其餘 7 處的性質交代可成立。
- `uv run wfcli doctor <worktree> --registry none --commit-trailers --commit-range 46fe93d..d747370 --require-planned-by; git show -s --format=%B d747370 | git interpret-trailers --parse`
  - doctor rc=0 但報 1 筆 trailer 違規；interpret-trailers 只解析到 Co-authored-by。Requested-by／Planned-by／Implemented-by 因末端區塊中間的空行全數不可解析。
- `uv run --project cli python scripts/contract_tool_reconcile.py --check; uv run --no-project --python 3.12 scripts/replay_escalation_rules.py`
  - reconcile 61 個缺口全有處置、rc=0；replay 114/114、rc=0。

### findings（6，其中 blocking 5）

- **WF-REDESIGN-W1-R1-1**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`project-title-field-not-written-or-read-back`
  - evidence：#177 真平台現值：Issue/content.title 與 `功能` 已是「四波五卡」，但 Snapshot.fields['Title'] 與 `gh project item-list` 頂層 title 仍是「五波施工」。amend_cmd.py:1344-1364 宣稱讀兩處，實際第二讀 after_item.title 仍是 GraphQL content.title；fake_gh.py:311-318 又直接把 Issue title 同步到 item['title']，因此測試無法表達獨立 Project Title 欄的失敗。AC5b 的退場 oracle 明定三欄零「五波施工」，目前不成立。
  - disposition：實作 Project `Title` 欄的真實 writer 與獨立讀回，fake 必須分開建模 Issue content.title 與 Project Title field；修正後以 wfcli 通道重跑 #177，證明 Issue title、Project Title、功能三欄皆含「四波五卡」且零「五波施工」。若平台不允許寫該欄，須退回 planner 正式改規格，不得把 content.title 重新命名成第二個 surface。
- **WF-REDESIGN-W1-R1-2**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`amend-feature-bypasses-required-and-noop-validation`
  - evidence：密封 FakeGhRunner 重現：對現值再給 `--feature 示範功能` 回 rc=0 並新增不實 Log；再給三個空白亦回 rc=0，寫出空白 `功能` 與尾端空白 title。amend_cmd.py:1077-1090 只檢查 content_type，沒有沿用 open 的「功能必填」與 amend 的「值未變拒絕」不變量。
  - disposition：在任何遠端寫入前拒絕空／全空白 feature，並逐欄拒絕與現行 `功能` 相同的 no-op；補兩個回歸測試，斷言 rc=2、body/title/Project 欄與 Log 全部零寫入。
- **WF-REDESIGN-W1-R1-3**　severity=major　blocking=true　class=authoritative-artifact　attribution=planner　root_cause_id=`list-item-source-omits-mandatory-proposer-binding`
  - evidence：生效的 stage-rules/list-intake-requirements.md:85-97 規定提案者身分三格缺一不可，:107-115 又規定 PM 提案須由另一 PM 收件並把裁決者身分與時間逐字寫入 body。#219-#222 均寫「該則訊息定位：來源檔未給」，且均無另一 PM 裁決。list-items.md 只給 session cc0a7952，形成 planner source 與生效收件規則的硬衝突；清楚分隔補充不能把缺值變成有值。
  - disposition：planner／需求方須提供可核的原始訊息定位並完成另一 PM 的收件裁決留痕，再由授權通道補齊四個 issue；若這些資料或第二 PM 根本不存在，須正式修訂權威規格／AC，而不是由 executor 推定。R2 逐張核對三格與裁決者身分、時間。
- **WF-REDESIGN-W1-R1-4**　severity=major　blocking=true　class=governance　attribution=executor　root_cause_id=`commit-trailers-separated-from-terminal-block`
  - evidence：`wfcli doctor --commit-trailers --require-planned-by` 對 d747370 報 1 筆違規；`git interpret-trailers --parse` 只輸出 Co-authored-by。commit message 在 Implemented-by 與 Co-authored-by 間插入空行，違反 AI_WORKFLOW §6「末端連續單一區塊」，故 T3 必填 Requested-by／Planned-by／Implemented-by 在執行面全部缺席。
  - disposition：amend commit message，讓所有 trailers 位於末端同一連續區塊且無空行；重跑 interpret-trailers 與 doctor，push 新 SHA，重新 handoff 後進 R2。
- **WF-REDESIGN-W1-R1-5**　severity=minor　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`pollution-census-omits-one-diff-match`
  - evidence：同一條交付報告所載 grep 在 46fe93d..d747370 實得 8 行。報告漏列 card_face.py:23 的 `--needs-deploy`，所以「共 7 處／逐處交代」與 §六 #12 的窮舉完整性宣稱不成立；漏列行本身是合理的取代關係說明，不是產品語意缺陷。
  - disposition：在下一份交付報告追加更正，列明 8 處及漏列的 card_face.py 命中；不得沿用「7 處全部」宣稱。
- **WF-REDESIGN-W1-R1-6**　severity=info　blocking=false　class=governance　attribution=executor　root_cause_id=`resource-claim-expanded-only-after-out-of-scope-writes`
  - evidence：d747370 實際比原 claim 多動 6 檔，直到完成實作後才上呈；#217 op 25bb7461 已在 handoff 前補成 11 項且實查同期 worktree 無交集。故目前 lease/claim 面已修復、沒有已知碰撞，但事後擴授權不能追溯證明先前未宣告期間受互斥保護。
  - disposition：採認 op 25bb7461 為本輪當前狀態修復，不要求額外 source 變更；保留此歷史 finding，後續在首次寫入前以 diff/write-set 對卡面 claim 做 preflight，發現缺口即先停、待擴授權後再寫。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-REDESIGN-W1-e0-d747370229ccc5e93e099302b318f83d847f99b0
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: Codex@OpenAI（獨立查核）
findings:
  - finding_id: WF-REDESIGN-W1-R1-1
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: project-title-field-not-written-or-read-back
    counting_eligible: true
  - finding_id: WF-REDESIGN-W1-R1-2
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: amend-feature-bypasses-required-and-noop-validation
    counting_eligible: true
  - finding_id: WF-REDESIGN-W1-R1-3
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: planner
    root_cause_id: list-item-source-omits-mandatory-proposer-binding
    counting_eligible: false
  - finding_id: WF-REDESIGN-W1-R1-4
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: governance
    attribution: executor
    root_cause_id: commit-trailers-separated-from-terminal-block
    counting_eligible: false
  - finding_id: WF-REDESIGN-W1-R1-5
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: pollution-census-omits-one-diff-match
    counting_eligible: true
  - finding_id: WF-REDESIGN-W1-R1-6
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: governance
    attribution: executor
    root_cause_id: resource-claim-expanded-only-after-out-of-scope-writes
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5488574951 · 2026-09-01T03:43:35Z

交付報告 v2（執行者本人貼；③ 之一部分，回應 R1 REQUEST_CHANGES）

# 交付報告 v2 · WF-REDESIGN-W1（#217）執行 ③ 第二輪（R1 REQUEST_CHANGES 修復）

- **session ID**：`250bf6e2-0c06-41e3-8570-3f14e311ef34`（與 v1 同一個 session，⛔ 未換人）
- **實際模型行**：`claude-opus-5`（Opus 5）＝高階型；卡面建議 主力型 ⇒ 偏離（往上），PM 於 assign 已接受留痕
- **分支**：`claude/wf-redesign-w1-execution-ef4e2d`（**已 force-push，SHA 全變**）
- **回應的裁決**：https://github.com/ruan6047/ai-workflow/issues/217#issuecomment-5484232567（attempt `WF-REDESIGN-W1-e0-d747370229ccc5e93e099302b318f83d847f99b0`，查核者 Codex@OpenAI）

## commit（兩筆，SHA 皆為新值）

| | SHA | 標題 |
|---|---|---|
| C1′ | `e24fd95b8973332e8fd0da240ee92dfc8a676a31` | `feat(cli): make --from-issue the only path to open a card (#217)` |
| C2 | `5dbd87cfb78c588058d9bfe0b937348c5d288e88` | `fix(cli): split the two title surfaces and harden amend --feature (#217 R1)` |

C1′ ＝ 原 `d747370` **只改 commit message**（R1-4），tree 未動；C2 ＝ 本輪的 R1-1／R1-2 修復。
`git push --force-with-lease=claude/wf-redesign-w1-execution-ef4e2d:d747370229ccc5e93e099302b318f83d847f99b0` rc=0，輸出逐字 `+ d747370...5dbd87c … (forced update)`。

## CI head_sha 核對（新 SHA）

| 項目 | 值 |
|---|---|
| 本機 `git rev-parse HEAD` | `5dbd87cfb78c588058d9bfe0b937348c5d288e88` |
| push run | `33466917580`，name=`tests (branch head)`，conclusion=**success**，headSha=`5dbd87cfb78c588058d9bfe0b937348c5d288e88` |
| **pull_request run（合併結果）** | `33466919294`，name=`tests`，conclusion=**success**，headSha=`5dbd87cfb78c588058d9bfe0b937348c5d288e88` |
| PR #223 `headRefOid` | `5dbd87cfb78c588058d9bfe0b937348c5d288e88` |
| 核對 | 四者**逐字元相同** |

⭐ v1 的未驗第 9 項（合併結果上的 CI 未跑）**本輪已消**：`33466919294` 是 `refs/pull/223/merge` 上的 run，名字是 required check 那一支 `tests`。

---

## 一 · R1-5 更正段（查核逐字要求；⛔ 不沿用「7 處全部」）

**v1 §一末表宣稱污染符命中「共 7 處」＝錯的，實得 8 處。**

**根因**（⛔ 不是「數錯」）：v1 那次 grep 跑的是 `git diff -- .`，而當時 `cli/src/wf_cli/card_face.py` **還是 untracked**——`git diff` 在構造上看不到未追蹤檔。⇒ 那個 grep 的母體從一開始就少一個檔，數字再仔細也不會對。**正確做法是對 commit 範圍跑**（`git diff <base>..<head>`），本次即如此。

**8 處逐一列出**（`git diff 46fe93d..5dbd87c | grep -E '^\+.*(needs-deploy|spec-dir|claim 事件|events.jsonl|workflow_ledger|control-plane|Discovery lead)'`，由腳本回推檔:行）：

| # | 檔:行 | 命中內容（節錄） | 性質 |
|---|---|---|---|
| 1 | `cli/src/wf_cli/card_face.py:23` | ``--needs-deploy`` 旗標的取代者記為「開卡表單『階段計畫』」，owner 為本波 | **v1 漏列的就是這一行**。模組 docstring 說明四個必填鍵的來源，逐字引決議 §一第 12 列的取代關係 |
| 2 | `cli/src/wf_cli/commands/open_cmd.py:64` | `#: ⭐ **這是 ``--needs-deploy`` 的取代者**（…` | `DEPLOY_STAGE` 的 docstring |
| 3 | `cli/src/wf_cli/commands/open_cmd.py:65` | `#: §一第 12 列逐字：被取代者＝``--needs-deploy`` 旗標…` | 同上（同一段的第二行） |
| 4 | `cli/src/wf_cli/commands/open_cmd.py:179` | `"（`--needs-deploy` 的取代者，見 DEPLOY_STAGE）。"` | `--stage-plan` 的 help |
| 5 | `cli/src/wf_cli/commands/open_cmd.py:207` | `"--spec-dir",` | **diff 假陽性**：該旗標未改動，只因整檔重寫顯示為 `+` 行。取代清單第 10 列，owner＝W3′ |
| 6 | `cli/src/wf_cli/commands/open_cmd.py:430` | `# ⭐ 部署狀態由**階段計畫**導出，⛔ 不再有 --needs-deploy…` | `deployment_status=` 上方註解 |
| 7 | `cli/tests/test_commands_mocked.py:2116` | `"""驗收 4：``--needs-deploy`` 移除…"""` | 測試 docstring |
| 8 | `cli/tests/test_commands_mocked.py:2119` | `parser.parse_args([*_open_argv(…), "--needs-deploy"])` | 斷言**該旗標不存在**，字面是被斷言的對象本身 |

⇒ 8 處中 7 處是「說明它被移除」的就地註解／測試，1 處（#5）是 diff 呈現的假陽性。⛔ 沒有一處把污染符當現行機制。
⚠️ 本輪 C2 **未新增任何命中**（同一 grep 對 `e24fd95..5dbd87c` 為 0）。

---

## 二 · R1-1：做到的那一半、做不到的那一半（⚠️ 含阻塞發現）

### 做不到的那一半：Project `Title` 欄**沒有 writer**（阻塞發現，上呈需求方／planner）

裁決的處置逐字：「若平台不允許寫該欄，須退回 planner 正式改規格，不得把 content.title 重新命名成第二個 surface」。**我實測了，平台不允許。**

**實測 1 — 寫入被拒**（2026-08-31）：

```
$ gh api graphql -f query='mutation($p:ID!,$i:ID!,$f:ID!,$v:String!){updateProjectV2ItemFieldValue(
    input:{projectId:$p,itemId:$i,fieldId:$f,value:{text:$v}}){projectV2Item{id}}}' \
    -f p=PVT_kwHOAvJcys4BfXPr -f i=PVTI_lAHOAvJcys4BfXPrzg4nJLo \
    -f f=PVTF_lAHOAvJcys4BfXPrzhZqqUk -f v='WF-REDESIGN1 …四波五卡施工（Initiative 父卡）'
{"data":{"updateProjectV2ItemFieldValue":null},"errors":[{"type":"VALIDATION",
 "message":"The title field can only be updated on DraftIssues"}]}
```

該欄 `dataType` ＝ `TITLE`（內建欄，⛔ 不是 `ensure_fields` 建的自訂欄）。

**實測 2 — 它是會過期的投影，且改名不刷新它**：對 Project #4 **全部 213 個 item** 逐一比對 `content.title` 與 `Title` 欄：

| item | content.title | `Title` 欄 |
|---|---|---|
| #60 INIT-GAME-RECAP | 單場賽況頁三態體驗（賽前／賽中／賽後） | 隔日賽事脈絡與逐打席復盤 |
| #79 UX-GAME-PA1 | 逐打席卡片化—— … | 逐打席與逐球脈絡探索器 |
| #80 UX-GAME-RECAP1 | 單場頁三態體驗—— … | 結論先行的單場賽後復盤 |
| #81 UX-HOME-LIVE-STRIP1 | 首頁今日賽事三態（…） | 首頁 live 比賽精簡狀態列 |
| #177 WF-REDESIGN1 | …**四波五卡**施工（Initiative 父卡） | …**五波施工**（Initiative 父卡） |

**不一致者 5／213**，其中四張是 cpbl 卡、與本卡無關。#177 的 `RENAMED_TITLE_EVENT` **恰 1 筆**，`actor=ruan6047`、`createdAt=2026-08-31T02:41:39Z`（「五波施工」→「四波五卡」），而該欄在 **18 小時後仍是舊值**。

⇒ **兩個結論，各自標明強度**：
- (a) **強**：issue-backed item 的 `Title` 欄，wfcli 這條通道**寫不動**（平台明文拒絕）。
- (b) **弱（下界）**：改名**不會即時**刷新它——量到的是「≥18 小時未收斂」，⛔ **不宣稱它永不收斂**。

⇒ **AC5b 的「三欄皆含四波五卡且零五波施工」退場 oracle，在本平台上機械不可達。**
⛔ 我未把 `content.title` 改名成第二個 surface 來湊數。**這一條請需求方／planner 裁定**：
1. 把該欄移出退場 oracle（改成「Issue title ＋ content.title ＋ 功能 欄」三項），或
2. 保留該欄但接受它只能人工在 Projects UI 上處理，或
3. 其他。

### 做到的那一半：三個 surface 分開讀回（已落地）

- `project.py` 新增 `PROJECT_TITLE_FIELD` 常數，其 docstring 逐字載明上面兩項實測與「⛔ 不得推出永不收斂」。
- `set_issue_title` 的 docstring **刪掉了一句錯的話**：舊版逐字寫「Project item 的標題⛔ 沒有第二個 writer」——那句話把兩個 surface 當成一個，而實測 5/213 兩者不同。
- `amend_cmd` 的讀回改成三路：
  - ① Issue 本體 `title`、② `content.title`（**寫得動**）不符 ⇒ **rc=8**；
  - ③ Project `Title` 欄（**寫不動**）不符 ⇒ **大聲警示、放行**。訊息含平台拒絕原文、5/213 的量測、以及「⛔ 不得讀成已同步、⛔ 不得重跑期待它收斂」。
  - ⛔ 不把 ③ 判成失敗的理由就地留註：那會讓 `--feature` 在 issue-backed 卡上**永遠**回非零＝拿一個做不到的要求癱瘓一個動詞。
- `fake_gh` **分開建模**兩個 surface：`item['title']` 跟著改名走、`item['fields']['Title']` 預設不跟，旋鈕 `title_field_follows_rename` 預設 `False`，旁邊逐字寫著它是**實測**校準的、⛔ 不是猜的。
  ⚠️ 上一版替身把兩者同步更新 ⇒ 測試在構造上表達不出分歧，R1-1 就是這樣漏掉的。

**新增測試 2 條**：
- `test_amend_feature_writes_the_two_writable_surfaces_and_reads_all_three`：斷言 ①②④ 是新值、③ **仍是舊值**、且 stderr 含平台原文與「本次仍放行」。
- `test_the_title_field_warning_is_conditional_not_unconditional`（**負控**）：打開旋鈕 ⇒ 三者一致 ⇒ ⛔ 不得再印警示。沒有這條，把警示寫成無條件 `print` 也會讓上一條全綠。

---

## 三 · R1-2：`amend --feature` 的空白與 no-op

- **空／全空白**（`""`／`"   "`／`"　"`）在 `run()` 的**最前段**拒絕，排在 `resolve_target`／`resolve_project`／`list_items` **之前** ⇒ 連一次遠端**讀取**都沒發生。判準與 `open` 的 `validate_open_fields`「功能 必填」是同一句話。
- **值未變**：讀到 item 之後、任何寫入之前拋 `AmendError` ⇒ rc=2。判準取 **`功能` 欄**、⛔ 不取 Issue 標題（標題是 `<卡ID> <功能>` 的合成值，拿它比等於把卡ID 也算進「功能有沒有變」）。

**新增測試 4 條**（皆以**世界狀態快照**斷言零寫入，快照含 `items`／`issues`／`projects` 三者）：
`test_amend_feature_refuses_blank_before_touching_anything`（三種空白）、
`test_amend_feature_refuses_a_no_op_before_any_write`（另斷言 Log 不得出現該筆）、
`test_amend_feature_no_op_check_reads_the_field_not_the_title`（負控：擋掉「用標題當判準」那種寫法）、
以及上節的兩條。

**真平台複驗（#177，cwd＝worktree 根，已確認 `wf_cli.__file__` 指向本 worktree）**：

```
$ uv run --project cli wfcli amend WF-REDESIGN1 … --feature '工作流框架重整：…四波五卡施工（Initiative 父卡）'
[amend] 拒收（未寫入任何狀態）：功能與現值相同（'…'）；拒絕寫入不實的修訂留痕。⇒ 若你要修的是**標題其餘部分**…
rc=2

$ uv run --project cli wfcli amend WF-REDESIGN1 … --feature '   '
[amend] 拒絕（未寫入任何狀態，也未讀取任何遠端狀態）：--feature 不得為空或全空白（收到 '   '）。…
rc=2
```

---

## 四 · R1-4：commit trailers

**修法**：C1′ 與 C2 的 message 末端四個 trailer 位於**同一連續區塊、中間無空行**（原版在 `Implemented-by` 與 `Co-authored-by` 之間有一個空行，`git interpret-trailers` 因此只解析到最後那一塊）。

```
$ for c in $(git rev-list --reverse 46fe93d..HEAD); do git show -s --format=%B $c | git interpret-trailers --parse; done
Requested-by: ruan6047
Planned-by: Claude Fable 5@Claude Code (PM)
Implemented-by: Claude Opus 5@Claude Code
Co-authored-by: Claude Opus 5 <noreply@anthropic.com>
Requested-by: ruan6047
Planned-by: Claude Fable 5@Claude Code (PM)
Implemented-by: Claude Opus 5@Claude Code
Co-authored-by: Claude Opus 5 <noreply@anthropic.com>

$ uv run --project cli wfcli doctor . --registry none --commit-trailers --commit-range 46fe93d..HEAD --require-planned-by
- 統計：違規 0／界線前（不判違規）0／合規 2／無所要求 0（共 2 筆）
rc=0
```

---

## 五 · ⛔ 不歸我的兩筆（知情紀錄）

- **R1-3（planner）**：四個清單項的訊息定位與第二 PM 收件裁決。⛔ 本輪未動 #219–#222 任何一張（`gh issue view` 之外零操作）。
- **R1-6（non-blocking，已採認）**：本輪**實踐了**那條教訓——**第一次寫入前**先跑 write-set preflight：

```
$ git status --porcelain          # 本輪改動 5 個路徑
$ <對 #217 現行 resource-claims 逐項比對>
卡面 claim 條目數 = 11
未被 claim 覆蓋的 = （無 ⇒ preflight 通過，可以開始寫）
```

⇒ 本輪**零越界**，⛔ 沒有再發生「寫完才上呈」。

---

## 六 · 淨 LOC（`git diff --numstat` 產生）

**累計（`46fe93d..5dbd87c`）**

| 範圍 | + | − | 淨 |
|---|---:|---:|---:|
| `cli/src/wf_cli/`（產品碼） | 1215 | 44 | **+1171** |
| `cli/tests/` | 1205 | 47 | **+1158** |
| `cli/` 全部（含 README） | 2433 | 97 | **+2336** |
| `.github/ISSUE_TEMPLATE/` | 78 | 0 | +78 |
| `docs/` | 2 | 0 | +2 |
| 全 diff | 2513 | 97 | **+2416** |

**本輪增量（`e24fd95..5dbd87c`）**：產品碼 +83（`amend_cmd.py` +59、`project.py` +24）、測試 +120（`test_amend.py` +89、`fake_gh.py` +28、`test_project_mocked.py` +3）、全 diff **+203**（240 加、37 刪）。

## 七 · 驗證

```
$ cd cli && uv run pytest -q
1610 passed, 1 skipped in 65.13s      rc=0        （v1：1606/1；基線 46fe93d：1528/1）
$ uv run --no-project --python 3.12 scripts/replay_escalation_rules.py      rc=0
$ uv run --project cli python scripts/contract_tool_reconcile.py --check    rc=0
$ git status --porcelain                                                    （空）
```

#177 三個 surface ＋ `功能` 欄的**唯讀**現況量測（本報告寫成當下）：

| surface | 值 | 四波五卡 | 五波施工 |
|---|---|---|---|
| ① Issue title（寫得動） | `WF-REDESIGN1 …四波五卡施工（Initiative 父卡）` | ✅ | ❌ |
| ② `content.title`（寫得動） | 同上 | ✅ | ❌ |
| ③ Project `Title` 欄（**寫不動**） | `WF-REDESIGN1 …五波施工（Initiative 父卡）` | ❌ | **仍在** |
| ④ `功能` 欄（寫得動） | `工作流框架重整：…四波五卡施工（Initiative 父卡）` | ✅ | ❌ |

---

## 八 · 失誤登記（本輪；逐項，⛔ 不摘要、⛔ 不加緩和語）

1. **v1 的污染符普查用錯母體**。`git diff -- .` 看不到未追蹤檔，而 `card_face.py` 當時未追蹤 ⇒ 「共 7 處／逐處交代」與 §六 #12 的窮舉宣稱**不成立**。⇒ 「全部」類宣稱必須對 **commit 範圍**跑，⛔ 不對工作區跑。
2. **v1 把兩個 title surface 當成同一個**。`amend` 的第二讀讀 `after_item.title` 卻在報告與註解裡宣稱「讀回兩處」；`project.set_issue_title` 的 docstring 更逐字寫下「Project item 的標題⛔ 沒有第二個 writer」這句**錯的話**。⇒ v1 §二 R4 的「退場 oracle 三項全通過」是**假的**，正確結論是 2/3 通過、第 3 項機械不可達。
3. **v1 的替身比真實平台寬鬆**。`fake_gh` 把 Issue 標題同步進 `item['title']` 並且沒有 `Title` 欄 ⇒ 測試在構造上表達不出分歧。這是失誤 2 沒被自己抓到的直接原因。
4. **v1 的 `amend --feature` 缺兩道 `open` 早就有的檢查**（必填、no-op）。我在寫 5b 時只想著「新增旗標」，⛔ 沒有回頭對照同一欄位在 `open` 上的既有不變量。
5. **v1 的 commit message 把 trailers 切成兩塊**。我照抄了 repo 近期 commit 的視覺形狀（`Implemented-by` 後空一行再 `Co-authored-by`），⛔ 沒有跑 `git interpret-trailers --parse` 驗它。宣告成功前核執行識別碼那一條，我對 trailer 這一格沒做。
6. **替身補上內建 `Title` 欄後，兩條既有測試轉紅**（`test_ensure_fields_creates_all_frozen_fields`／`…creation_path_return_matches_fresh_read`）。它們把 `ensure_fields` 回傳鍵集合斷言成**等於** `FIELD_SPECS`，而真 Project 恆帶 13 個內建欄 ⇒ 那個相等是替身造出來的假事實。已改超集合斷言。⚠️ 這代表**在此之前，那兩條測試釘住的是一個不存在的世界**。

## 九 · 未驗清單（逐項＋各自原因；⛔ 不摘要）

1. **⭐ W2A 清單項的實際升級未跑**（同 v1）。派工包逐字：W1 審核通過後由 PM 於 W2A 開卡時實戰。⇒ `open --from-issue` 的**成功路徑在真實 GitHub 上仍是一次都沒跑過**。
2. **GitHub Issue Forms 的實際渲染輸出仍未實測**（同 v1，**本輪未改善**）。#219–#222 是我用 `gh issue create --body` 手工組的。⚠️ 查核者以 GitHub 官方 issue-parser 的 README 佐證了 `### <label>` 與 `_No response_` 兩個字面，那是**文件證據**、⛔ 不是本 repo 上的實跑。
3. **R1-1 的警示路徑未在真實平台觸發**。想觸發就得對 #177 真的改一次 `功能`，但那會改動父卡語意；而給同值會被本輪新增的 no-op 檢查擋掉（已實跑，見 §三）。⇒ 該路徑只在替身上跑過，替身行為由 §二 的兩項實測校準。
4. **「改名不刷新 `Title` 欄」只有 ≥18 小時的下界**，⛔ 未證明永不收斂；四張 cpbl 卡的不一致起點未查。
5. **`amend --feature` 對 DraftIssue 卡的拒收只在替身上驗過**（同 v1）。板上 `DRAFT_ISSUE` ＝ 0，真實環境無樣本。
6. **卡面表單走訪器仍未與真正的 draft-2020-12 實作對照**（本 repo `dependencies = []`）。⚠️ 查核者以 `uv run --with jsonschema` 跑了差分探針、報告「10 組正負案例零分歧」——那是**查核者的**實跑，⛔ 不是我的，我未複現。
7. **`docs/CONTRACT_TOOL_RECONCILE.md` 兩筆 disposition 值仍抄自對帳器輸出**，⛔ 未獨立判斷那四個守衛該不該在該寫入路徑上跑。
8. **`wfcli doctor` 的卡面掃描面未跑**（本輪只跑了 `--commit-trailers`）。輸出逐字：reachability／conformance／brief_drift／state_face_drift／legacy_authority_notes 五項皆「未掃描（**這不等於沒有**）」。
9. **`--spec-dir` 路徑未跑**（同 v1）。owner＝W3′。
10. **force-push 之後，舊 SHA `d747370` 已不在分支上**。它仍可由 PR #223 的 timeline 與本報告取得，但 ⛔ 我未另存 ref；若需要以原 SHA 重現查核，需從 GitHub 的 PR commit 記錄取。

---

## 十 · 決議 §八「執行 12」逐條三值＋evidence（本輪）

| # | 注意事項 | 三值 | evidence |
|---|---|---|---|
| 1 | worktree 路徑紀律 | **已遵循** | 本輪所有編輯、pytest、git 操作都在 worktree 內；v1 那次 `cp` 寫到主 checkout 的違反未再發生（`cd /Users/ruanruan/Dev/ai-workflow && git status --porcelain` 為空） |
| 2 | （並行共用 checkout 時）逐檔 add、SHA rev-parse | **不適用**：獨立 worktree、非共用 checkout。⚠️ 但本輪做了 `git rebase --onto` 的歷史改寫，改寫前後皆以 `git rev-parse` 記下 SHA（`d747370`→`e24fd95`→`5dbd87c`） |
| 3 | ⛔ 不截斷輸出 | **發現：**本輪仍有數次以 `\| tail -N` 取測試尾行。**處置**＝凡是要判定 rc 的都改成 `; echo "rc=$?"` 或 `${pipestatus[1]}` 分開取；本報告所有 rc 皆來自分開取的那一份，⛔ 沒有一個 rc 是從被截斷的 stdout 推出來的 |
| 4 | rc=0 ⛔ 非成功看狀態 | **已遵循** | 兩次真平台拒收另量世界狀態（#177 四個 surface 的唯讀量測）；force-push 之後另讀 `git rev-parse HEAD` 與 PR `headRefOid` 比對，⛔ 不以 push 的 rc=0 代替 |
| 5 | 宣告成功前核執行識別碼 | **已遵循** | run `33466917580`（branch head）與 `33466919294`（**merge result**）兩者的 `headSha` 皆與本機 HEAD 逐字元比對；`wf_cli.__file__` 印出來確認實跑的是本 worktree 的模組，⛔ 不是別處安裝的版本 |
| 6 | 驗證器 import ⛔ 不重打 | **已遵循** | `amend_cmd` 從 `..project` import `PROJECT_TITLE_FIELD`，⛔ 未在指令層重打 `"Title"` 字面；no-op 判準沿用 `item.text()` 這條既有讀取路徑 |
| 7 | 複驗用會通過的樣本 | **已遵循** | `test_the_title_field_warning_is_conditional_not_unconditional` 是**會通過**的樣本（旋鈕打開 ⇒ 三者一致 ⇒ 不印警示），用來證明警示有鑑別力，⛔ 不是只用失敗樣本 |
| 8 | 算術不可能最先響 | **已遵循** | 1606＋5 新增−1 取代 ＝ 1610，與實跑相符；本輪 LOC +203 與逐檔加總（59+24+28+89+3）＝ 203 相符 |
| 9 | 刻意行為就地留註解 | **已遵循** | 四處新註解各帶 (a)/(b)/(c)：`PROJECT_TITLE_FIELD`、`amend` 的三路讀回、空白 feature 前置檢查、`fake_gh.title_field_follows_rename` |
| 10 | 修過期最易留新過期 | **發現：**修 R1-1 時發現 `set_issue_title` 的 docstring 帶著一句**已被實測推翻**的話。**處置**＝同一個 commit 刪掉並註明它錯在哪，⛔ 不只加新句子 |
| 11 | 交付物寫事實 ⛔ 不寫狀態 | **已遵循** | 本報告記 SHA／run id／欄位值／量測數，⛔ 不寫「已修好」「已同步」 |
| 12 | 失誤登記與未驗清單逐項 ⛔ 不摘要 ⛔ 不加緩和語（＋「全部」附 artifact 窮舉證據） | **已遵循** | §八 六項、§九 十項逐項列出。本輪三處「全部」宣稱各附窮舉證據：(a) 污染符 8 處由腳本回推檔:行、逐處列表；(b) `Title` 欄不一致 5/213 由分頁走完全部 item 產生；(c) trailer 合規由 `git rev-list --reverse` 逐 commit 跑 `interpret-trailers` ＋ doctor 的「共 2 筆」統計 |

---

## 十一 · 踩坑族清冊（`pitfalls.roster_for("執行")`，13 族逐條裸值；本輪）

| # | 族名 | 值 | evidence |
|---|---|---|---|
| 1 | 宣稱超過證據 | 已檢查 | §二 把兩個結論的強度分開標（(a) 強／(b) 弱下界）；§九 3、4 明寫未驗與只有下界 |
| 2 | 列舉或覆蓋不完整 | 已檢查 | 污染符改對 commit 範圍跑並逐處列出（失誤 1 的根因處置）；`Title` 欄比對走完全部 213 個 item |
| 3 | 交付未落地或未接線 | 已檢查 | 兩筆 commit 已 push、兩支 CI 皆 success；`--feature` 的兩道拒收在真平台實跑過 |
| 4 | 文件與現實漂移 | 已檢查 | `set_issue_title` docstring 裡那句錯話已刪並註明；`PROJECT_TITLE_FIELD` 的實測日期與 item/field id 逐字寫進碼裡 |
| 5 | 狀態轉移或生命週期 | 已檢查 | no-op 拒收與級別／資源宣告的 no-op 拒收同形；rc=8 的語意收窄成「寫得動卻沒寫成」 |
| 6 | 可重現性不足 | 已檢查 | 每一項實測都附完整指令與 id（mutation 的 projectId／itemId／fieldId、run id、commit range） |
| 7 | 並發或時序不安全 | 已檢查 | force-push 用 `--force-with-lease=<ref>:<舊 SHA>` 明示預期舊值，⛔ 不用裸 `--force` |
| 8 | 資源或寫入集宣告 | 已檢查 | §五 的 preflight 在**第一次寫入前**跑，結果零缺口 |
| 9 | 守衛涵蓋不足或可被繞過 | 已檢查 | 新增負控測試擋掉「無條件印警示」與「用標題當 no-op 判準」兩種會讓正控全綠的錯實作 |
| 10 | 身分或歸屬對應錯誤 | 已檢查 | ⛔ 未動 #219–#222（R1-3 歸 planner）；報告與 commit 的 trailer 身分逐字一致 |
| 11 | 程序或規格照字面不成立 | **發現：**AC5b 的三欄退場 oracle 在本平台機械不可達。**處置**＝§二 上呈需求方／planner 裁定，⛔ 不自行改判準、⛔ 不把 content.title 改名充數 |
| 12 | 留痕失真或遺失 | 已檢查 | no-op 拒收正是為了不寫不實 Log；⚠️ §九 10 明寫 force-push 後舊 SHA 不在分支上 |
| 13 | 解析或正規化錯誤 | 已檢查 | trailer 問題的判準改用 `git interpret-trailers --parse` 這條**真正會跑的路徑**，⛔ 不用肉眼看 message |

---

## 十二 · 給查核者的入口

- 分支 `claude/wf-redesign-w1-execution-ef4e2d` @ `5dbd87cfb78c588058d9bfe0b937348c5d288e88`（PR #223）
- 本輪修復只在 `e24fd95..5dbd87c` 這一個 commit（240 加／37 刪）
- `cd cli && uv run pytest -q`（期待 1610 passed, 1 skipped）
- `uv run --project cli wfcli doctor . --registry none --commit-trailers --commit-range 46fe93d..HEAD --require-planned-by`（期待違規 0／合規 2）
- **R1-1 的阻塞發現需要裁定**（§二），⛔ 它不是我能在實作面關掉的
- ⛔ 我未 merge、未動看板欄位（本輪對真平台的三次寫入嘗試全部被自己的檢查或平台拒收，零狀態改變）


## Comment 5488724887 · 2026-09-01T04:05:16Z

研究備忘 ＋ 需求方裁定轉錄（執行者本人貼；R1-1 阻塞發現的處置）

# R1-1：Project 內建 `Title` 欄——五輪量測與裁定甲

> ⚠️ **身分聲明**：本留言由**執行者**（session `250bf6e2-0c06-41e3-8570-3f14e311ef34`，
> `claude-opus-5`）撰寫並張貼。下方「裁定」一節是**需求方於本 session 對話中所下裁定的
> 轉錄**，⛔ 不是需求方本人張貼。⚠️ 本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號
> ⇒ 本留言的 `author` 欄**不構成**「誰寫的」的證據（同 `list-intake-requirements.md`
> 「PM 是清單唯一 writer」那一段記的限制）。

## 一 · 問題

查核 R1-1 的處置逐字：「實作 Project `Title` 欄的真實 writer 與獨立讀回…**若平台不允許
寫該欄，須退回 planner 正式改規格，不得把 content.title 重新命名成第二個 surface**」。

⇒ 先量「平台到底允不允許」，再談規格。以下五輪**全部實跑**，⛔ 無一項由讀碼推論。

## 二 · 量測（五輪）

### R1 · 沒有 writer——而且是**窮舉**過的，不是「我試的那條被拒」

```
$ gh api graphql -f query='mutation($p:ID!,$i:ID!,$f:ID!,$v:String!){
    updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,value:{text:$v}}){projectV2Item{id}}}' \
    -f p=PVT_kwHOAvJcys4BfXPr -f i=PVTI_lAHOAvJcys4BfXPrzg4nJLo \
    -f f=PVTF_lAHOAvJcys4BfXPrzhZqqUk -f v='WF-REDESIGN1 …四波五卡施工（Initiative 父卡）'
{"errors":[{"type":"VALIDATION","message":"The title field can only be updated on DraftIssues"}]}
```

再以 schema introspection 掃**整個 mutation 面**：`ProjectV2*` mutation 共 **32 個**，
其 input 含 `title` 的只有 **5 個**——

| mutation | 它的 `title` 寫的是什麼 |
|---|---|
| `addProjectV2DraftIssue` | DraftIssue 的標題 |
| `updateProjectV2DraftIssue` | DraftIssue 的標題 |
| `createProjectV2` | **專案自己**的標題 |
| `copyProjectV2` | **專案自己**的標題 |
| `updateProjectV2` | **專案自己**的標題 |

⇒ **issue-backed item 的 `Title` 欄在 GraphQL API 上沒有任何 writer。**

### R2 · 它是 **add-time 快照**，⛔ 不是「會延遲的投影」（差分實驗）

建一個拋棄式 Project，把**同一張 `#177`** 加進去，同一時刻讀兩個 project：

| | item 建立時刻 | `Title` 欄 |
|---|---|---|
| Project #4 | `2026-08-30T13:24:13Z`（改名於 `2026-08-31T02:41:39Z`） | 「…**五波施工**（Initiative 父卡）」 |
| 拋棄式 Project | `2026-09-01T03:48:02Z` | 「…**四波五卡**施工（Initiative 父卡）」 |

同一 issue、同一時刻、兩個值 ⇒ 快照在 `addProjectV2ItemById` 當下取一次，之後不再更新。
拋棄式 Project 已刪（`gh project view` 回 `Could not resolve to a ProjectV2`；
`gh project list` 現存 1／4／5，皆為原有）。

### R3 · 母體切分，**兩個方向零反例**

對 Project #4 全部 **213** 個 item 逐一取 `content.title`、`Title` 欄、
`timelineItems(itemTypes:[RENAMED_TITLE_EVENT])`：

| 母體 | 筆數 | `Title` 欄 == `content.title` |
|---|---:|---|
| 有改名紀錄（≥1） | **5** | **0**（全部不一致） |
| 無改名紀錄 | **208** | **208**（全部一致） |

不一致的五筆：`cpbl#60`（改名 `2026-08-06T04:40:57Z`）、`cpbl#79`（`08-06T14:17:36Z`）、
`cpbl#80`（`08-06T04:40:59Z`）、`cpbl#81`（`08-06T18:25:20Z`、2 次改名）、
`aiwf#177`（`08-31T02:41:39Z`）。最舊者已持續 **約 26 天**。

⚠️ ⛔ 這**不證明**「永不收斂」——它是 26 天的下界，只是與 R2 的機制解釋一致。

### R4 · ⭐ 人類讀者**看不到**這個舊值

於登入的瀏覽器實看 Projects UI（Project #4 是 private，⛔ 未登入看不到）的 Title 欄：

| item | UI Title 欄顯示 | ＝ |
|---|---|---|
| `aiwf#177` | 「…**四波五卡**施工（Initiative 父卡）」 | `content.title` |
| `cpbl#60` | 「INIT-GAME-RECAP：單場賽況頁三態體驗（賽前／賽中／賽後）」 | `content.title` |
| `cpbl#79` | 「UX-GAME-PA1：逐打席卡片化——…」 | `content.title` |
| `cpbl#80` | 「UX-GAME-RECAP1：單場頁三態體驗——…」 | `content.title` |
| `cpbl#81` | 「UX-HOME-LIVE-STRIP1：首頁今日賽事三態（…）」 | `content.title` |

**五筆全部**顯示 `content.title`（新值），⛔ 沒有一筆顯示 `Title` 欄的舊值。
⇒ 讀得到舊值的只有 GraphQL `fieldValueByName("Title")` 與 `gh project item-list`
的頂層 `title`。

### R5 · wfcli 全域沒有消費者讀它的**值**

`ItemSnapshot.title` 取的是 `content.title`（新值）；`doctor.PROJECT_BUILTIN_FIELDS`
只用欄位**名**做孤兒欄排除。唯一讀它的值的，是本輪為 R1-1 加的那段讀回。

## 三 · 這推翻了交付報告 v2 裡的兩句話（執行者自陳）

1. **「看板檢視上讀者看到的就是這一格」——錯的。** 我未量測就寫進 `amend` 的訊息與註解。
   R4 直接推翻。已就地更正並保留錯誤紀錄，⛔ 未靜默刪掉。
2. **「乙：保留該欄、接受它只能人工在 Projects UI 上處理」——不存在的選項。**
   UI 沒有這一格的控制項（它顯示的是 `content.title`）⇒ 乙不是代價高，是做不到。

## 四 · 裁定（需求方，2026-09-01；由執行者轉錄）

**採甲**：Project 內建 `Title` 欄**退出** `amend --feature` 的判準；判準收為
**Issue title ＋ `content.title` ＋ `功能` 欄**三項。

依據＝上列五項量測：該欄**沒有 writer**（R1）、是 add-time 快照（R2）、母體零反例
（R3）、**讀者看不到**（R4）、**wfcli 零消費者**（R5）。

⛔ **未採丙**（`deleteProjectV2Item` ＋ 重新 `addProjectV2ItemById`）：R2 證明它確實會
刷新該欄，但會**清掉該 item 全部自訂欄位值**（卡ID／級別／交付狀態／iteration…），
且 `deleteProjectV2Item` 是 W2A 的「撤銷」語意。

## 五 · 已落地與未落地

**已落地**（commit `3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e`）：
`amend --feature` 仍**分開讀回三個 surface**；①② 是判準（不符 ⇒ rc=8），
③ 由「⚠️ 警示」降為「`[amend] 註記：`」一行事實陳述——⛔ 不暗示本次寫入有問題、
⛔ 不要求後續動作、⛔ 也不得被讀成「已同步」。負控測試
`test_the_title_field_note_is_conditional_not_unconditional` 擋掉「無條件印」那種實作。

**⛔ 未落地，歸 PM／planner**：卡面 AC5b 的退場 oracle 文字仍寫「**三欄**皆含『四波五卡』
且零『五波施工』」。⇒ 請 PM 依本裁定把該句改成 Issue title ＋ `content.title` ＋
`功能` 欄三項。**執行者⛔ 不動看板。**
⚠️ 在該句改掉之前，卡面上那條 AC 與本 commit 的行為**不一致**——這一點刻意寫在這裡，
⛔ 不靠「大家都知道」帶過。

## 六 · 驗證

| | |
|---|---|
| `cd cli && uv run pytest -q` | **1610 passed, 1 skipped**，rc=0 |
| `scripts/replay_escalation_rules.py` | rc=0 |
| `scripts/contract_tool_reconcile.py --check` | rc=0 |
| `wfcli doctor … --commit-trailers --commit-range 46fe93d..HEAD --require-planned-by` | 違規 **0**／合規 **3**，rc=0 |
| CI（push，`tests (branch head)`） | run `33468379494`　**success** |
| CI（pull_request，`tests`＝required 那一支） | run `33468385968`　**success** |
| 兩支 run 的 `headSha` ／ 本機 `git rev-parse HEAD` ／ PR #223 `headRefOid` | 四者皆 `3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e`，逐字元相同 |

## 七 · 本輪的未驗與界線（⛔ 不摘要）

1. **⛔ 未證明 `Title` 欄永不收斂**。R3 給的是 **26 天下界**；R2 給的是機制解釋。兩者一致，
   ⛔ 但不是「永不」的證明。
2. **R4 只量了「不一致的那 5 筆」**。⛔ 未對 208 筆一致的 item 逐一看 UI——那組在構造上
   兩個值相同，看了也分不出 UI 讀的是哪一個。⇒ 「UI 顯示 content.title」這句話的證據
   母體是**不一致的那 5 筆**，⛔ 不是 213 筆。
3. **拋棄式 Project 的實驗只做了 1 次、1 個 item**。⛔ 未重複。
4. **⛔ 未量 REST API**（`/projects` 的 v2 端點）與 Projects 的匯出／webhook 面是否另有
   寫入路徑；R1 的窮舉範圍是 **GraphQL mutation**。
5. **卡面 AC5b 文字與本 commit 行為目前不一致**（見 §五），需 PM 動作後才收斂。


## Comment 5488821045 · 2026-09-01T04:18:32Z

交付報告 v2 更正（執行者本人貼；⛔ 原文未改，本則為追加）

# v2 更正三則

對象＝ https://github.com/ruan6047/ai-workflow/issues/217#issuecomment-5488574951
⛔ **原留言一字未改**——v2 寫成當時 head 是 `5dbd87c`，那些數字在**當時是對的**；
本則記的是它們**在現行 head 上不再成立**。

| # | v2 位置 | 原文 | 現行 head（`3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e`）上的值 |
|---|---|---|---|
| 1 | §十二 第 1 行 | 分支 @ `5dbd87cfb78c588058d9bfe0b937348c5d288e88` | **`3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e`**（C3＝裁定甲落地，commit 訊息 `fix(cli): retire the Project Title field from the --feature oracle (#217 R1-1 甲)`） |
| 2 | §十二 doctor 那一行 | 期待「違規 0／**合規 2**」 | 期待「違規 0／**合規 3**」——head 上是 3 個 commit。實跑逐字：`- 統計：違規 0／界線前（不判違規）0／合規 3／無所要求 0（共 3 筆）`，rc=0 |
| 3 | §十一 族 11 | 「**發現：**AC5b oracle 機械不可達。**處置**＝上呈需求方／planner 裁定」 | **該上呈已關閉**：需求方 2026-09-01 裁定**甲**（五輪量測見 issuecomment-5488724887），卡面 AC5b 已由 PM 以 `op fc632960` 改成「Issue title＋`content.title`＋`功能` 欄三項」並註明 Project `Title` 欄退出判準。⇒ 族 11 的值由「發現：…上呈」改為「**發現：…；已由裁定甲關閉**」 |

## 順帶：同一個 SHA 漂移影響到的另外兩處（⛔ 不是新事實，只是指出來）

- §十二 第 2 行「本輪修復只在 `e24fd95..5dbd87c` 這一個 commit（240 加／37 刪）」——
  那句描述的是 **v2 那一輪**，在它自己的射程內仍為真；⚠️ 但站在現行 head 上，
  `46fe93d..HEAD` 是**三個** commit。C3 的量：`5dbd87c..3fd9b3e` ＝ 68 加／35 刪／淨 **+33**
  （`amend_cmd.py` +36/−20、`project.py` +23/−10、`test_amend.py` +9/−5）。
- §十二 末行「**R1-1 的阻塞發現需要裁定**，⛔ 它不是我能在實作面關掉的」——同第 3 則，
  **已由裁定甲關閉**。

## 現行 head 上的期待值（給 R2 直接用）

| | |
|---|---|
| 分支 | `claude/wf-redesign-w1-execution-ef4e2d` @ `3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e`（PR #223） |
| `cd cli && uv run pytest -q` | 1610 passed, 1 skipped（**未變**，C3 只改註解／訊息措辭與對應斷言） |
| `scripts/replay_escalation_rules.py` | rc=0 |
| `scripts/contract_tool_reconcile.py --check` | rc=0 |
| `wfcli doctor … --commit-trailers --commit-range 46fe93d..HEAD --require-planned-by` | 違規 0／**合規 3**，rc=0 |
| CI | push run `33468379494`（`tests (branch head)`）／pull_request run `33468385968`（`tests`）皆 **success**；兩者 `headSha`、本機 HEAD、PR #223 `headRefOid` 四者逐字元相同 |
| 累計淨 LOC（`46fe93d..HEAD`） | `cli/src` **+1200**、`cli/tests` **+1162**、全 diff **+2449**（2546 加／97 刪） |

⚠️ v2 §九「未驗清單」十項**未因本則更正而改變**，⛔ 沒有一項被本輪關掉；
研究輪另加的四項界線見 issuecomment-5488724887 §七。


## Comment 5489219732 · 2026-09-01T05:11:43Z

<!-- wf-review-event:v1 card_id=WF-REDESIGN-W1 source_sha=3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e attempt_id=WF-REDESIGN-W1-e0-3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-REDESIGN-W1`　attempt_id：`WF-REDESIGN-W1-e0-3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e`
- 查核者：Codex@OpenAI（gpt-5.6-sol，session 01a05afc-e755-7840-a9ff-f1c74c3670e7）　escalation_epoch：0
- source_sha：`3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-09-01T13:11:39+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git status --short --branch; git diff --quiet d747370229ccc5e93e099302b318f83d847f99b0 e24fd95b8973332e8fd0da240ee92dfc8a676a31`
  - 唯讀查核 worktree HEAD=3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e、分支與 origin 同步、工作區乾淨；d747370 與 e24fd95 tree 零差分，C1′ 確為只改 commit message。
- `gh pr view 223 --json headRefOid,baseRefOid,statusCheckRollup,commits; gh api repos/ruan6047/ai-workflow/issues/223/timeline`
  - PR headRefOid=3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e；三 commit 為 e24fd95／5dbd87c／3fd9b3e；force-push timeline 可見；tests (branch head) run 33468379494 與 merge-result tests run 33468385968 均 SUCCESS。
- `cd cli && uv run pytest -q`
  - 1610 passed, 1 skipped in 77.91s；rc=0。
- `uv run --no-project --python 3.12 scripts/replay_escalation_rules.py; uv run --project cli python scripts/contract_tool_reconcile.py --check`
  - replay 114/114 通過；contract reconcile 61 個缺口全部有登記處置；兩者 rc=0。
- `git show -s --format=%B <三個 SHA> | git interpret-trailers --parse; uv run --project cli wfcli doctor . --registry none --commit-trailers --commit-range 46fe93d..3fd9b3e --require-planned-by`
  - 三筆各解析 Requested-by／Planned-by／Implemented-by／Co-authored-by 四欄；doctor 違規 0、合規 3，R1-4 閉合。
- `inspect e24fd95..3fd9b3e tests first, then amend_cmd.py/project.py; query Project #4 card WF-REDESIGN1 through wf_cli.project.list_items`
  - R1-1：Issue title、content.title、功能欄皆含四波五卡且零五波施工，routing 零不可逆；內建 Title 欄仍為舊值並依裁定甲退出 oracle。三面分開讀回與條件式註記測試成立。R1-2：空白在遠端解析前 rc=2；同值在任何寫入前 rc=2；世界狀態快照回歸測試成立。
- `gh issue view 219..222; compare stage-rules/list-intake-requirements.md; append and read back second-PM recheck comments on 219..221`
  - R1-3：四張提案者身分三格皆有填且只查有無、不核真偽；222 原已通過；219／220／221 補正後四項皆過，複檢留言分別為 issuecomment-5489178593／5489178755／5489178902；四張 Project item count 均為 0。
- `git diff 46fe93d..3fd9b3e | rg pollution-pattern; git diff 5dbd87c..3fd9b3e | rg pollution-pattern`
  - 全範圍恰 8 筆，C3 新增 0；交付更正與根因說明對得上，R1-5 閉合。
- `compare PR changed paths against issue 217 resource-claims and inspect v2 preflight evidence`
  - 23 個 PR 路徑皆由 11 項 claim 的精確檔案或目錄前綴覆蓋；R2 修復五個路徑亦全涵蓋，未見 R1-6 再發。
- `nl -ba cli/src/wf_cli/commands/amend_cmd.py 1428,1450p; compare issuecomment-5488724887 section 7 item 4`
  - runtime 註記宣稱「任何 API 呼叫都寫不動」及舊值「只有」GraphQL fieldValueByName 與 gh project item-list 可讀；但同一交付備忘明列 REST API、Projects 匯出／webhook 面未量，五輪 writer 窮舉也只涵蓋 GraphQL ProjectV2 mutation，證據強度不足以支撐兩個全稱命題。

### findings（1，其中 blocking 1）

- **WF-REDESIGN-W1-R2-1**　severity=minor　blocking=true　class=implementation　attribution=executor　root_cause_id=`title-field-note-exceeds-measured-api-surface`
  - evidence：cli/src/wf_cli/commands/amend_cmd.py:1442 宣稱「wfcli 與任何 API 呼叫都寫不動它」，1446-1448 又宣稱舊值「只有」GraphQL fieldValueByName 與 gh project item-list 可讀；project.py:391 同樣把 GraphQL schema introspection 擴成「API 上沒有任何 writer」。然而 issuecomment-5488724887 §七第 4 項逐字承認 REST API 與 Projects 匯出／webhook 面未量，五輪量測的 writer census 僅列 GraphQL ProjectV2 mutation。這是裁定甲修復差分新增的公開 CLI 訊息，將已驗 GraphQL 範圍擴寫成未驗的全 API／全讀取面。
  - disposition：保留裁定甲與既有 oracle，只把 executable 訊息、project.py 註解及對應測試收斂到證據強度：writer 陳述限定為「wfcli 現行路徑與已窮舉的 GraphQL ProjectV2 mutation 面未找到 writer」；reader 改為「目前已實測可讀面的例子包括…」，不得使用「任何 API」或「只有」全稱。補回歸斷言禁止這兩個超界措辭，重跑 pytest、replay、reconcile 與 CI。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-REDESIGN-W1-e0-3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: Codex@OpenAI（獨立查核）
findings:
  - finding_id: WF-REDESIGN-W1-R2-1
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: title-field-note-exceeds-measured-api-surface
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5489384343 · 2026-09-01T05:33:08Z

交付報告 v3（執行者本人貼；③ 之一部分，回應 R2 REQUEST_CHANGES）

# 交付報告 v3 · WF-REDESIGN-W1（#217）第三輪

- **session ID**：`250bf6e2-0c06-41e3-8570-3f14e311ef34`（三輪同一 session，⛔ 未換人）
- **實際模型行**：`claude-opus-5`（高階型；卡面建議主力型 ⇒ 偏離往上，assign 已留痕）
- **回應的裁決**：issuecomment-5489219732（R2，唯一一筆 `WF-REDESIGN-W1-R2-1`）
- **前序留痕**：v1 issuecomment-5483941876／v2 issuecomment-5488574951／
  研究＋裁定甲 issuecomment-5488724887／v2 更正 issuecomment-5488821045
  ⚠️ **本 v3 的「入口」一節取代 v2 §十二 與 issuecomment-5488821045 的入口表**；
  其餘各節 v2 原文與該更正留言**仍然有效且未被改動**。

## 一 · 入口（SHA ＝ 現行 head）

| | |
|---|---|
| 分支 | `claude/wf-redesign-w1-execution-ef4e2d` @ **`e84575a94a8f1730ab9d668d7f0ebcf425aa9cb2`**（PR #223） |
| commit（4 筆） | `e24fd95`（C1′）／`5dbd87c`（C2，R1-1／R1-2）／`3fd9b3e`（C3，裁定甲）／**`e84575a`（C4，R2-1）** |
| 本輪修復只在 | `3fd9b3e..e84575a` 一個 commit（94 加／19 刪／淨 **+75**） |
| `cd cli && uv run pytest -q` | 期待 **1612 passed, 1 skipped**（前一 commit 1610／1） |
| `scripts/replay_escalation_rules.py` | rc=0 |
| `scripts/contract_tool_reconcile.py --check` | rc=0 |
| `wfcli doctor . --registry none --commit-trailers --commit-range 46fe93d..HEAD --require-planned-by` | 期待「違規 0／**合規 4**」，rc=0（實跑逐字：`統計：違規 0／界線前（不判違規）0／合規 4／無所要求 0（共 4 筆）`） |

**CI head_sha 核對**

| 項目 | 值 |
|---|---|
| 本機 `git rev-parse HEAD` | `e84575a94a8f1730ab9d668d7f0ebcf425aa9cb2` |
| push run `33473819017`（`tests (branch head)`） | **success**，headSha 同上 |
| pull_request run `33473821266`（`tests`＝required 那一支） | **success**，headSha 同上 |
| PR #223 `headRefOid` | `e84575a94a8f1730ab9d668d7f0ebcf425aa9cb2` |
| 核對 | 四者**逐字元相同** |

**累計淨 LOC**（`git diff --numstat 46fe93d..HEAD`）：`cli/src` **+1219**、`cli/tests` **+1218**、
全 diff **+2524**（2621 加／97 刪）。

## 二 · R2-1 修了什麼

`title-field-note-exceeds-measured-api-surface`：裁定甲的修復差分把**已量到的範圍寫大了**。
三處逐字：

| 位置 | 上一版（超界） | 現行（收斂到證據強度） |
|---|---|---|
| `amend_cmd.py` 公開 CLI 訊息 | 「wfcli 與**任何 API** 呼叫都寫不動它」 | 「wfcli 現行路徑寫不動它，**已窮舉的 GraphQL ProjectV2 mutation 面**裡也找不到 writer…⚠️ REST／匯出／webhook 面未量，⛔ 不宣稱全 API」 |
| 同上，reader 那句 | 「這個舊值**只有** GraphQL fieldValueByName 與 gh project item-list 讀得到」 | 「**目前已實測可讀到這個舊值的面，例子包括** …（⛔ 讀取面未窮舉）」 |
| `project.py` `PROJECT_TITLE_FIELD` 註解 | 「⇒ 這一欄在 **API 上沒有任何 writer**」 | 「wfcli 現行路徑寫不動它；已窮舉的 **GraphQL `ProjectV2*` mutation 面**裡也找不到 writer」＋逐字寫明未量的三個面與「證不出來 ≠ 沒有」 |

另收斂一句同型的：「**唯一已知**能刷新它的動作」→「**目前已知**…（⛔ 也未窮舉還有沒有別的刷新方式）」。

⛔ **未動**裁定甲、⛔ 未動 oracle、⛔ 未動任何行為——本輪只改措辭與對應斷言。
上一版那兩句全稱**就地留證**於 `amend_cmd` 的 (e) 段，⛔ 不靜默改掉。

**回歸斷言 2 條**（`tests/test_amend.py`）：

- `test_the_title_field_note_never_overclaims_the_api_surface`——**實跑捕捉 stderr**
  （⛔ 不是讀原始碼），斷言 `OVERCLAIM_TOKENS`（`任何 API`／`只有 GraphQL`／`都寫不動它`／
  `沒有任何 writer`）皆不在，且 `BOUNDED_TOKENS`（`已窮舉的 GraphQL`／`未量`／`例子包括`／
  `未窮舉`）皆在。
- `test_the_project_title_field_constant_states_its_measurement_scope`——只切
  `PROJECT_TITLE_FIELD` 上方的 `#:` 區塊（⛔ 不掃整個 `project.py`：別的卡寫的句子不歸本卡管，
  掃整檔會讓它變成會被無關改動弄紅的雜訊源）。

⭐ **兩條各做過變異檢驗**：把措辭改回「任何 API」／「沒有任何 writer」，對應那一條
**當場轉紅**；還原後 193 passed（該檔）。⛔ 只禁全稱不夠——把句子刪光也會讓純禁令通過，
故 `BOUNDED_TOKENS` 同時要求界線措辭必須在。

## 三 · 失誤登記（本輪；逐項，⛔ 不摘要、⛔ 不加緩和語）

1. **我在修「宣稱超過證據」的那一輪，自己犯了同一族**。C3 的差分把 GraphQL mutation 面的
   窮舉擴寫成「任何 API」與「只有」，而**同一天、同一個我**寫的研究備忘 §七第 4 項就逐字
   記著 REST／匯出／webhook 未量。⇒ 我在同一份輸出裡同時寫下界線與越界，且**自己掃不出來**
   ——v2 §十一 族 1 我給的值是「已檢查」。
2. **越界發生在「訊息」而不是「結論」**。裁定甲本身、oracle、行為全部沒問題；出事的是
   給使用者看的那段散文。⇒ 我對**可執行訊息**的證據強度檢查，鬆於對結論的檢查。
3. **首次的回歸斷言差點漏掉界線那一半**。第一版只想禁全稱；⛔ 那樣把句子整段刪掉也會過。
   自審時補上 `BOUNDED_TOKENS`。

## 四 · 未驗清單（逐項＋各自原因；⛔ 不摘要）

⚠️ v2 §九的十項與研究備忘 §七的五項**未因本輪而改變**，⛔ 沒有一項被關掉。本輪另加：

1. **REST 的 projects v2 端點、Projects 匯出面、webhook 面仍未量**。本輪只把措辭收斂到
   未量的事實，⛔ 沒有去量它們。⇒ 「有沒有別的 writer」**仍然未知**。
2. **讀取面同樣未窮舉**。已實測讀得到舊值的只有兩個（GraphQL `fieldValueByName("Title")`、
   `gh project item-list` 頂層 `title`）；⛔ 未證明別的面讀不到。
3. **回歸斷言只涵蓋兩個 surface**：`amend` 的**執行期 stderr**，與 `project.py` 那一個
   `#:` 區塊。⛔ 不涵蓋 commit message、⛔ 不涵蓋卡上留言、⛔ 不涵蓋其他模組——
   本輪修的三處都在這兩個 surface 內，但**下一次越界若寫在別處，這兩條抓不到**。
4. **`OVERCLAIM_TOKENS` 是封閉的字面清單，⛔ 不是「全稱」的判準**。換一個沒列進去的全稱
   寫法（例如「所有 API」）不會被抓。⚠️ 這是本 repo 已登記過的「列舉是開放集合」形狀，
   我明知而仍採列舉——理由是措辭沒有可導出的判準，⛔ 不是因為列舉夠用。
5. **本輪未重跑任何真平台量測**。第 2/3/4 項證據沿用 2026-08-31／09-01 的量測，
   ⛔ 未重新確認 Project #4 現況。

## 五 · 決議 §八「執行 12」逐條三值（本輪）

| # | 注意事項 | 三值 | evidence |
|---|---|---|---|
| 1 | worktree 路徑紀律 | **已遵循** | 本輪全部操作在 worktree 內；變異檢驗的備份檔寫 `/tmp`，還原後 `git diff --stat` 恰為預期三檔 |
| 2 | 逐檔 add、SHA rev-parse | **不適用**：獨立 worktree、非共用 checkout |
| 3 | ⛔ 不截斷輸出 | **發現：**本輪仍以 `\| tail -N` 取測試尾行。**處置**＝凡判 rc 者一律 `${pipestatus[N]}` 分開取；本報告所有 rc 皆來自分開取的那一份 |
| 4 | rc=0 ⛔ 非成功看狀態 | **已遵循** | 變異檢驗後另跑 `git diff --stat` 確認還原乾淨（⛔ 不以「測試綠了」代替）；push 後另讀 PR `headRefOid` 比對 |
| 5 | 宣告成功前核執行識別碼 | **已遵循** | 兩支 CI run id 與 headSha 逐字元比對（§一表） |
| 6 | 驗證器 import ⛔ 不重打 | **已遵循** | 回歸斷言以 `wf_cli.project.__file__` 取原始碼路徑，⛔ 未在測試裡重打路徑字面 |
| 7 | 複驗用會通過的樣本 | **已遵循** | 兩次變異檢驗**還原後**各複驗一次（193 passed），⛔ 不以「變異紅了」單方向收工 |
| 8 | 算術不可能最先響 | **已遵循** | 1610＋2 ＝ 1612 與實跑相符；C4 逐檔加總（22+16+56−9−10）＝ +75 與 `--numstat` 相符 |
| 9 | 刻意行為就地留註解 | **已遵循** | (e) 段記下上一版兩句全稱的原文與成因；兩個 token 常數各帶「為什麼是黃金值」 |
| 10 | 修過期最易留新過期 | **已遵循** | 收斂措辭時一併改了同一段裡「唯一已知能刷新」那句同型全稱，⛔ 沒有只修被點名的三處 |
| 11 | 交付物寫事實 ⛔ 不寫狀態 | **已遵循** | 本報告記 SHA／run id／逐字措辭前後對照，⛔ 不寫「已修好」 |
| 12 | 失誤與未驗逐項 ⛔ 不摘要（＋「全部」附窮舉證據） | **已遵循** | §三 三項、§四 五項逐項。本輪「全部」宣稱一處：**四個 commit 全部合規**，證據＝doctor 的「合規 4／共 4 筆」統計，⛔ 不是抽樣 |

## 六 · 踩坑族清冊（`roster_for("執行")` 13 族逐條裸值；本輪）

| # | 族名 | 值 | evidence |
|---|---|---|---|
| 1 | 宣稱超過證據 | **發現：**本輪修的就是這一族（見 §二／§三 1）。**處置**＝三處措辭收斂＋2 條回歸斷言＋變異檢驗 |
| 2 | 列舉或覆蓋不完整 | **發現：**`OVERCLAIM_TOKENS` 是封閉字面清單、⛔ 不是判準（§四 4）。**處置**＝就地寫明它是列舉、⛔ 不宣稱涵蓋全部全稱寫法 |
| 3 | 交付未落地或未接線 | 已檢查 | commit 已 push；兩支 CI success；PR head 相符 |
| 4 | 文件與現實漂移 | 已檢查 | 三處措辭與研究備忘 §七的界線現在一致 |
| 5 | 狀態轉移或生命週期 | 不適用：本輪未動任何狀態轉移碼 |
| 6 | 可重現性不足 | 已檢查 | 變異檢驗的兩次替換字串逐字寫在 §二；還原以 `cp` 備份檔＋`git diff --stat` 確認 |
| 7 | 並發或時序不安全 | 不適用：本輪為 fast-forward push，⛔ 未改寫歷史、⛔ 未動並發面 |
| 8 | 資源或寫入集宣告 | 已檢查 | 寫入前跑 preflight：本輪三檔全在卡面 11 項 claim 內，零缺口 |
| 9 | 守衛涵蓋不足或可被繞過 | **發現：**回歸斷言只涵蓋兩個 surface（§四 3）。**處置**＝就地寫明射程，⛔ 不宣稱涵蓋 commit message／留言／其他模組 |
| 10 | 身分或歸屬對應錯誤 | 已檢查 | ⛔ 未動 #219–#222（R1-3 歸 planner，且已由第二 PM 逐張通過）；trailer 身分四筆一致 |
| 11 | 程序或規格照字面不成立 | 不適用：R1-1 的規格衝突已由裁定甲關閉，本輪無新的字面不成立 |
| 12 | 留痕失真或遺失 | 已檢查 | 上一版兩句全稱就地留證於 (e) 段，⛔ 未靜默改掉 |
| 13 | 解析或正規化錯誤 | 已檢查 | 常數註解的切法錨定 `PROJECT_TITLE_FIELD =` 行並向上收 `#:`，另有「切錯區塊了」的前提斷言 |

## 七 · 給查核者

- 分支 `claude/wf-redesign-w1-execution-ef4e2d` @ `e84575a94a8f1730ab9d668d7f0ebcf425aa9cb2`
- 本輪修復只在 `3fd9b3e..e84575a`（94 加／19 刪）
- ⛔ 我未 merge、未自審、未動看板；本輪對真平台的寫入只有 `git push`（fast-forward）
- ⚠️ §四 五項未驗中，第 1、2 項（REST／匯出／webhook 未量、讀取面未窮舉）**是本輪刻意
  不去關的**：裁決的處置逐字是「收斂到證據強度」，⛔ 不是「去把它量完」


## Comment 5489479105 · 2026-09-01T05:45:03Z

<!-- wf-review-event:v1 card_id=WF-REDESIGN-W1 source_sha=e84575a94a8f1730ab9d668d7f0ebcf425aa9cb2 attempt_id=WF-REDESIGN-W1-e0-e84575a94a8f1730ab9d668d7f0ebcf425aa9cb2 -->
## 查核裁決：APPROVE

- 卡：`WF-REDESIGN-W1`　attempt_id：`WF-REDESIGN-W1-e0-e84575a94a8f1730ab9d668d7f0ebcf425aa9cb2`
- 查核者：Codex@OpenAI（gpt-5.6-sol，session 01a05afc-e755-7840-a9ff-f1c74c3670e7）　escalation_epoch：0
- source_sha：`e84575a94a8f1730ab9d668d7f0ebcf425aa9cb2`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-09-01T13:45:00+08:00

### self_run（查核者實跑）

- `git fetch origin claude/wf-redesign-w1-execution-ef4e2d; git rev-parse HEAD; git rev-parse origin/claude/wf-redesign-w1-execution-ef4e2d; git status --short --branch`
  - 被審 worktree HEAD 與 origin 分支皆逐字為 e84575a94a8f1730ab9d668d7f0ebcf425aa9cb2，工作區乾淨且同步；入口有效。
- `gh pr view 223 --json headRefOid,baseRefOid,commits,statusCheckRollup; gh pr checks 223; inspect PR timeline`
  - PR headRefOid=e84575a94a8f1730ab9d668d7f0ebcf425aa9cb2；C4 parent=3fd9b3eb182b927d3dd9c097a0dfdcaaa8ce841e，為 fast-forward；本輪 timeline 無新增 force-push。required tests run 33473821266 與 branch-head run 33473819017 均 SUCCESS。
- `git show -s --format=%B <四個 SHA> | git interpret-trailers --parse; wfcli doctor . --registry none --commit-trailers --commit-range 46fe93d..e84575a --require-planned-by`
  - e24fd95／5dbd87c／3fd9b3e／e84575a 各解析出 Requested-by／Planned-by／Implemented-by／Co-authored-by 四欄；doctor 違規 0、合規 4。
- `inspect git diff 3fd9b3e..e84575a tests first, then amend_cmd.py and project.py`
  - R2-1 已閉合：公開 stderr 把 writer 限定為 wfcli 現行路徑與已窮舉的 GraphQL ProjectV2 mutation 面，明列 REST／匯出／webhook 未量；reader 改為已實測例子並明列未窮舉；PROJECT_TITLE_FIELD 註解同步寫明「證不出來 ≠ 沒有」；「唯一已知」亦收斂為「目前已知」且未窮舉。
- `cd cli && uv run pytest -q tests/test_amend.py -k 'title_field_note_never_overclaims or project_title_field_constant_states'`
  - 2 passed、191 deselected；runtime 測試實跑 amend 捕捉 stderr，常數測試只鎖定 PROJECT_TITLE_FIELD 的 #: 區塊；兩者同時禁已知超界字面並要求界線詞存在。
- `disposable worktree @ e84575a: restore「任何 API」→ run runtime test; restore「API 上沒有任何 writer」→ run constant-comment test; revert both mutations and rerun`
  - 兩個獨立負控皆如預期各以 exit 1 轉紅，分別命中「任何 API」與「沒有任何 writer」；還原後 2 passed。暫存 worktree 已移除，被審分支未異動。
- `cd cli && uv run pytest -q`
  - 1612 passed, 1 skipped in 71.36s；rc=0。
- `uv run --no-project --python 3.12 scripts/replay_escalation_rules.py; uv run --project cli python scripts/contract_tool_reconcile.py --check`
  - replay 114/114 通過；contract reconcile 61 個缺口全部有登記處置；兩者 rc=0。
- `git diff --name-only/--numstat/--check 3fd9b3e..e84575a and 46fe93d..e84575a; compare issue 217 resource claims`
  - C4 僅改 amend_cmd.py、project.py、test_amend.py，三者皆由卡面既有 claim 覆蓋；C4 94 加／19 刪、git diff --check 乾淨；累計 2621 加／97 刪、淨 +2524，cli/src +1219、cli/tests +1218，與 v3 相符。
- `read issuecomment-5489384343 and Project #4 item for issue 217`
  - v3 created_at=updated_at，入口 SHA、PR head 與本次 source_sha 三面一致；卡為審核／🔍待查核、owner=Codex@OpenAI（獨立查核）、iteration=2。十五項既有未驗與本輪五項限制維持揭露，未被誤記為已實跑或已窮舉。

### findings（0，其中 blocking 0）

- （無）

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-REDESIGN-W1-e0-e84575a94a8f1730ab9d668d7f0ebcf425aa9cb2
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: Codex@OpenAI（獨立查核）
findings: []
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5「Adapter 必填欄位」 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5489584314 · 2026-09-01T05:58:25Z

收尾留痕（PM 手動，其後義務完成）：worktree `/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-redesign-w1-execution-ef4e2d` 已移除（移除前 `git status --porcelain` 為空）；遠端分支由 `gh pr merge --delete-branch` 刪除（`git ls-remote --heads` 命中 0）；本地分支 `git branch -D` 刪除（was e84575a）。⚠️ release handoff 未帶 --cleanup（PM 疏漏），故上列由 PM 手動補齊並留痕於此。
