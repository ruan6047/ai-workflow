# #52 WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1 WF_EVENT_IDEMPOTENCY1.md 檔頭摘要與 §4.4 節末對「探針執行指令是否釘選」互相矛盾
- state: open  created: 2026-08-12T09:23:38Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/52
- comments: 8

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code PM
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；須先裁定「現在該釘什麼指令」才談得上修文字，那是實質規格判斷；並須確認該裁定與 #24 已撤除執行能力後的現況相容。）　查核：待指派（建議 經濟型；單檔文件一致性修正，查核只需確認裁定後的敘述在全檔一致且與 main 現況相符；不涉紅線。）
- Initiative：—　spec 基線：WF-EVENT-IDEMPOTENCY1-ADAPT-STALE1（#41）於 ebca7ec 的 R1-001（major，非阻擋，attribution=planner，root_cause_id=preexisting-authoritative-instruction-drift）。查核者 disposition 逐字：另由原規格所有者或 PM 裁定現行指令後開獨立權威文件修正卡；本輪不擴寫入集。#41 已 APPROVE 併入 main（e8a638c）。
- DB：db_scope=none
- 服務的原始目標：讓權威設計文件不會對同一件事給出兩個相反的指示

## 簡介
<!-- card-brief:begin -->
`docs/WF_EVENT_IDEMPOTENCY1.md` 的檔頭摘要（約 :9）與 §4.4 節末（約 :454）對「四支探針的執行指令要不要釘為 `uv run python`」給出兩個相反指示；該矛盾在交付當下就存在，不是後來撤除自檢執行能力造成的。**適用時機**：要照該檔操作那四支探針、或要判斷 `#24` 撤除共用自檢執行能力後「釘選執行指令」這件事還適不適用時。⛔ 非射程：不追溯改寫任何裁決或事件留痕；只動 `docs/WF_EVENT_IDEMPOTENCY1.md` 一檔。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：docs/WF_EVENT_IDEMPOTENCY1.md 的檔頭摘要（約 :9）寫「四支探針……執行指令一律釘為 uv run python（專案 venv，實測 3.12.13）」，而同檔 §4.4 節末（約 :454）明文「前一版把指令釘選在 uv run python（3.12.13）……本輪撤除該處置」。同一份權威文件對同一件事給出兩個相反的指示。

這個矛盾**在 #23 交付當下就已存在**，是該卡自己的內部漂移，**不是 #24 撤除自檢執行能力所造成**——WF-EVENT-IDEMPOTENCY1-ADAPT-STALE1（#41）的執行者在窮舉時發現並明確劃出這條界線，判定「修它要決定現在該釘什麼指令，那是實質規格判斷屬原撰寫者／PM，不是事實更正」，故未動。跨家族查核者同意並列為非阻擋 finding。

之所以不能只挑一句刪掉：#24 已把共用自檢的執行能力整個撤除（改為純靜態閘門），所以「釘哪個指令」的答案可能兩句都不對——現況可能根本沒有需要釘選的執行指令。裁定前先修文字會產生第三個版本的錯誤。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:docs/WF_EVENT_IDEMPOTENCY1.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 先裁定現況：#24 撤除執行能力後，本檔的四支探針是否仍有任何被執行的路徑？若無，「釘選執行指令」這件事本身是否已不適用？裁定須以 main 現況為據並附指令輸出，不得只讀文件。
- [ ] 依裁定結果修正兩處敘述使全檔一致。若結論是「已不適用」，兩處都要改；若結論是「仍需釘選」，須說明釘什麼、為什麼，並與 #24 §9.9 的閘門機制對齊。
- [ ] 窮舉全檔是否還有其他處對執行指令／執行能力作出陳述，不得只改這兩處。窮舉須由指令輸出產生。
- [ ] 不得追溯改寫任何裁決或事件留痕；改動以本卡 commit 為時點、明示為後續更正。

## 驗證

- [ ] 修改後以 main 上的共用自檢跑本檔，確認閘門仍通過、登記相符、違例 0。
- [ ] 窮舉輸出附完整命中清單與逐項處置。
- [ ] 確認只動 docs/WF_EVENT_IDEMPOTENCY1.md 一檔。
## Log

- 2026-08-12T17:23:37+08:00 open by Claude Opus 5@Claude Code PM；owner 待指派；iteration 0。
- 2026-08-12T18:00:14+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code 子agent；分支worktree claude/WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1-probe-cmd-drift1；交付狀態 🚧進行中；實際能力層級 主力型（與卡面建議 主力型 相符）。
- 2026-08-12T18:24:41+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA 161ab8a347c35fd323ac395eef5ca4161f3fe0f1；證據 R1：單檔 +40/-3。裁定**不是**卡面預設的「已不適用」，而是**依角色分流**——執行者立的實質規格判斷，請查核者重點看。

驗證／閘門角色：釘 uv run python **與現行機制不相容**，不只是被撤除。§4.4.1／§12 A 已把「§4.4 探針須以下限直譯器實跑」移轉給實作卡 A 的獨立 CI 步驟並要求釘 3.11；而實測 uv run python = 3.12.13，閘門過濾是 v[:2] <= FLOOR（FLOOR=(3,11)）→ False，該指令**不具閘門資格**。**PM 已複驗。** 故本檔不指定任何指令。

人工重跑角色：**仍存在**（檔頭承諾可自 repo root 重跑），但不再釘單一指令。理由是釘選買不到它要買的東西——今日實測 3.9.6／3.12.13／3.14.3，§4.4 base 輸出去掉自報版本行後**逐位元組相同**（md5 三份一致），而原釘選理由「其中一個會直接 TypeError」針對的是**前一版探針文字**、在今天的探針上不復現。執行者並自陳「三個資料點不是可攜性保證」。

現況查證全部自己重跑未採信 #41 轉述：對抽出的區塊做 AST 全呼叫點列舉，執行原語只命中 subprocess.run 兩處，逐一讀呼叫址確認送出的是**常數字面程式**、文件區塊原始碼以 **stdin 資料**傳入被剖析、從不求值；無 exec／eval／compile(...,"exec")／runpy／__import__，無 except BaseException。本 repo 無 .github/、全 repo grep 無任何處引用本檔探針。

窮舉：grep uv run 全檔 6 處逐項列處置（改 3、不動 3），並區分**規範性 vs 描述性**。自檢實跑（改後）裁決 PASS、違例 0、登記相符、exit=0 且**已達定點**。

⚠️ **PM 派工詞的一個假設是錯的，執行者查證後指出**：PM 寫「該檔必然含事件 marker 前綴字面」，實測 **main 版 0 次、本分支 0 次、新增 0 次**（PM 已複驗）。PM 把 #35 那份的性質誤套到這一份。attribution=coordinator。

⚠️ **範圍外發現，未修並指名**：§4.4 探針**今日對 main 的 cli/ 已失效**——三個直譯器**一致地** rc=1，參數面 106 → **117**，四個未分類旗標為 open --exec-capability-reason／--review-capability-reason、assign --capability-deviation-reason、amend --ruling-url，**全是今天併入的**（#21 路由層級、#37 授權綁定）。意謂「重跑可重現正文輸出」今天不成立。修它須動 §4.1 型別表 → 超出單檔寫入集。**與本卡裁定無關**（三直譯器失敗完全相同）。

執行者自陳五項無機械執行者，第 1 項最該打：「人工重跑角色仍存在」是規格判斷非機械可判——**若查核者認為文件不該承諾人工重跑，裁定二應改為全面不適用**。。
- 2026-08-12T19:25:27+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5265944399，PM 回讀重算 SHA-256 相符、未經編輯、marker 字面 0）；core_pain_resolved yes；self_run 4 項；findings 1 項（blocking 1）；attempt WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1-e0-161ab8a347c35fd323ac395eef5ca4161f3fe0f1。
- 2026-08-12T19:37:53+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 1；SHA 161ab8a347c35fd323ac395eef5ca4161f3fe0f1；證據 R1-001（major, blocking, governance, attribution=executor, root_cause_id=governance-provenance-trailer-omission）：commit 缺 AGENTS.md:10 要求的 Requested-by／Planned-by／Implemented-by trailer。核心痛點查核者判已消失（yes），本 finding 純為治理留痕。⚠️ PM 補充：本項為今日全批問題非本卡獨有——今日落 main 的 31 筆非 merge commit 帶 Implemented-by 者 0 筆、在飛五個分支亦全為 0、最後一筆帶 trailer 是 2026-08-11；PM 的執行者提示詞從未提過 trailer，該層歸 coordinator。已合併的 31 筆不追溯改寫（補 trailer 只能改寫歷史，本專案明令禁止）。。
- 2026-08-12T21:18:12+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 1；SHA 9f09466635e86d6180e5e0a9a88976033eac7635；證據 R2：R1-001（trailer 缺失）已處置。執行者追加 9f09466 為**刻意的空 commit**（tree 與 161ab8a 完全相同 f746e641…，git diff 空輸出），實質內容一字未動、docs/WF_EVENT_IDEMPOTENCY1.md 相對基線仍為 +40/-3 單檔。trailer 四行齊備且為末端連續單一區塊。級別判定 T2 取自 Project 欄位（GraphQL 讀取非推測），依 AI_WORKFLOW.md:211-216 適用三件式；:217-220 明定 Reviewed-by 只在 merge／PR 結案／B2 核可，故未加（加了等同自我批准）。⚠️ 執行者指名一個它沒有解掉的矛盾並寫進 commit body 而非只寫報告：trailer 語意描述其所附著的 commit，而要讓 161ab8a 自己帶 trailer 只能改寫已推送歷史——disposition 明令不得 amend，本專案亦明令禁止追溯改寫，**兩條規則在 commit 推送後不可能同時滿足**。它選保留歷史＋後續補記，緩解是兩個 commit 來歷恰好同一組人故補記的值正確，但明列殘留缺口：逐 commit 檢查仍會看到 161ab8a 本身是裸的；若查核者判準是「每筆實作 commit 各自帶 trailer」，本處置不滿足且在不改寫歷史下無法滿足。⚠️ 它並主張 attribution 應為 coordinator 而非 executor，三項機械依據：本 repo 對 trailer 零機械強制（AI_WORKFLOW.md:221 寫「守衛必紅」而該守衛不存在，cli/ 內 grep 零命中）、CLAUDE.md:10 與 AGENTS.md:10 對 Reviewed-by 互相矛盾（照前者字面辦會在實作 commit 上自我批准）、覆蓋率斷點是集體且同日跨執行者的。PM 已複驗三項屬實並開卡 DEV-COMMIT-TRAILER-GUARD1（#63）統一處理。PM 自審：遠端 tip 相符、161ab8a 是祖先（非 force）、對 main merge-tree CLEAN、相對基線寫入集單檔零逸出（對上卡面宣告）、合併樹 ea7c6e8 實測 701 passed。。
- 2026-08-12T22:28:39+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5267773576 未經編輯，PM 依其取材規則（## 結構化裁決 → EOF）回讀重算 report_sha256=77c34e84… 相符。PM 的轉錄調整：自 yaml fence 內取結構化區塊，fence 外的散文（查核結論／範圍外）保存於收據雜湊範圍內，區塊內字串逐字未變；core_pain_resolved yes；self_run 4 項；findings 1 項（blocking 1）；attempt WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1-e0-9f09466635e86d6180e5e0a9a88976033eac7635。
- 2026-08-12T22:37:25+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 2；SHA 9f09466635e86d6180e5e0a9a88976033eac7635；證據 R2-001（major, blocking, governance, attribution 由 executor 改判 coordinator, governance-provenance-trailer-omission）：空 commit 的 trailer 不會被 161ab8a 繼承，R1-001 判 not_closed。查核者明判本項在卡內無解——「禁 amend 已推送歷史使 executor 沒有卡內可行修法」，須由規則層前向裁定。已將該裁定納入 DEV-COMMIT-TRAILER-GUARD1（#63）驗收（op 2a03da44），本卡在 #63 裁定前無法閉合。⚠️ 本卡 core_pain_resolved 判 yes，實質內容未被打；卡住的純為治理留痕。執行者暫不需動手，等 #63 的規則層裁定。。
- 2026-08-13T00:23:20+08:00 handoff by wf-cli → owner 待指派；iteration 3；SHA 0ea7abad670681b708f4fbbe15526008b448abe3；證據 依 docs/ROADMAP.md §0／§3 降級：本卡屬目標 3（治理精緻化），非「防止低級事故」或「可稽核的內容」。需求方 2026-08-12 裁定降級為 Backlog、有餘力再做。⚠️ 降級不是關閉——本卡載有的真實 finding 紀錄全數保留、可逆；未閉合的 blocking 維持未閉合，本次降級不視為驗收。⚠️ WF-DISPATCH-PRECHECK1（#38）另有一項：它的射程很可能被 WF-DISPATCH-FROM-HANDOFF1（#66，走「同源產生」路線讓不一致不可能發生）取代，該裁定屬 #66 執行者，本次降級不預判。。
- 2026-08-26T14:21:52+08:00 amend by wf-cli（op 135a54bc）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:ecf96d9e3fe95b929e800e13c5a752a4c96cfc3598aa61ee4e5c1b0cdddfad0d (537 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第二批（20 張純隨機）：依 canonical §6.3 回填簡介；文字經 A5 守衛（分行字元＋1012B 上限）預先拒收檢查。
- 2026-08-29T14:57:53+08:00 handoff by wf-cli → owner 待指派；iteration 3；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 阻塞登記（來源狀態 📥Backlog）：https://github.com/ruan6047/ai-workflow/issues/52 之阻塞留言。解除條件＝待審清單機制上線。。


## Comment 5265845107 · 2026-08-12T11:04:33Z

## 派審：#52 `WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1` R1

⚠️ 審核對象 **`ruan6047/ai-workflow#52`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1-probe-cmd-drift1
分支：claude/WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1　　被審 SHA：161ab8a347c35fd323ac395eef5ca4161f3fe0f1
基線：e8a638c40f1028b6b85f6c59fd12ee9c1e85582d（PM 已重算並驗為祖先）　　iteration：0（首輪）
寫入集：docs/WF_EVENT_IDEMPOTENCY1.md 單檔（+40/-3）
```

> **權威來源**：本則派審詞與本 Issue Log 最後一筆 `handoff` 事件的 `SHA` **必須一致**。**若你發現兩者不符，以 handoff 事件為準並回報該不符**——PM 本日在 #9 與 #38 上各犯過一次「做了 handoff 卻沒補發派審詞」，其中一位查核者因此審了舊產物，另一位正確拒審。

`origin/main` 現為 **`e1b33d8`**（#53 已於本日合併）。本分支單檔文件，與 #53 的三個檔零重疊，`git merge-tree` **無衝突**；合併結果 pytest **701 passed**（PM 實測）。

### 一、本卡的裁定不是卡面預設的答案，請重點看這裡

卡面預設的處置是「釘選探針執行指令」或「宣告已不適用」。**執行者兩個都沒選，改為依角色分流**，這是它自己立的實質規格判斷：

**驗證／閘門角色 → 釘 `uv run python` 與現行機制不相容，不只是被撤除。** §4.4.1／§12 A 已把「§4.4 探針須以下限直譯器實跑」移轉給實作卡 A 的獨立 CI 步驟並要求釘 3.11；而實測 `uv run python` = **3.12.13**，閘門過濾條件是 `v[:2] <= FLOOR`（FLOOR=(3,11)）→ **False**。該指令**不具閘門資格**。**PM 已複驗這兩項**。

**人工重跑角色 → 仍存在，但不再釘單一指令。** 理由是釘選買不到它要買的東西：今日實測 3.9.6／3.12.13／3.14.3，§4.4 base 輸出去掉自報版本行後**逐位元組相同**（md5 三份一致）；而原釘選理由「其中一個會直接 TypeError」針對的是**前一版探針文字**，在今天的探針上不復現。**執行者自陳「三個資料點不是可攜性保證」。**

**請攻擊**：這個分流把一份文件裡的同一個指令切成兩種身分。**查核者若認為文件根本不該承諾人工重跑，裁定二應改為全面不適用**——執行者自己把這條列為第 1 項最該被打的無機械執行者項。請正面裁示。

### 二、執行者拒絕採信轉述，自己重跑了現況查證

它沒有採信 #41 的轉述，改為：對抽出的區塊做 **AST 全呼叫點列舉**，執行原語只命中 `subprocess.run` 兩處，逐一讀呼叫址確認送出的是**常數字面程式**、文件區塊原始碼以 **stdin 資料**傳入被剖析、**從不求值**；無 `exec`／`eval`／`compile(...,"exec")`／`runpy`／`__import__`，無 `except BaseException`。本 repo 無 `.github/`、全 repo grep 無任何處引用本檔探針。

窮舉：`grep` 全檔 `uv run` 六處逐項列處置（改 3、不動 3），並區分**規範性 vs 描述性**。自檢實跑（改後）裁決 PASS、違例 0、登記相符、`exit=0` 且**已達定點**。

### 三、⚠️ PM 派工詞的一個假設是錯的，執行者查證後指出

PM 寫「該檔必然含事件 marker 前綴字面」。實測 **main 版 0 次、本分支 0 次、新增 0 次**（PM 已複驗）。PM 把 #35 那份的性質誤套到這一份。`attribution` 為 `coordinator`。**你不必為此開 finding，但可以判斷 PM 的處置是否恰當。**

### 四、⚠️ 範圍外發現：§4.4 探針今日對 main 的 `cli/` 已失效

執行者未修並指名：三個直譯器**一致地** `rc=1`，參數面 **106 → 117**，四個未分類旗標為 `open --exec-capability-reason`／`--review-capability-reason`、`assign --capability-deviation-reason`、`amend --ruling-url`，**全是今天併入的**（#21 路由層級、#37 授權綁定）。意謂「重跑可重現正文輸出」今天不成立。修它須動 §4.1 型別表 → **超出單檔寫入集**。

執行者主張這**與本卡裁定無關**（三個直譯器失敗完全相同，故不影響可攜性的判斷）。**請判斷這個劃界成不成立**——若你認為本卡的核心痛點在這個失效之下無法宣告關閉，那是 `core_pain_resolved: no` 的依據。

（PM 已另記待開卡承接該失效，但那張卡尚未開；不影響本輪裁決。）

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5265944399 · 2026-08-12T11:14:53Z

<!-- wf-review-receipt:v1
card_id: WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1
source_sha: 161ab8a347c35fd323ac395eef5ca4161f3fe0f1
report_sha256: 49f1cc8dfb72858f32a82401d39b256fb41801fd48dbc2f61e3197759d9e32a7
-->
取材規則：取本規則之後的下一個 `## 結構化裁決` 起始字元，到報告末尾最後一個 LF 為止；UTF-8、LF、不可 strip；排除本收據 HTML 註解與本取材規則段落。起訖 delimiter 是「本規則之後的下一個」。

## 結構化裁決

```yaml
core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1-probe-cmd-drift1 rev-parse HEAD && git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1-probe-cmd-drift1 status --porcelain=v1 && git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1-probe-cmd-drift1 merge-base --is-ancestor e8a638c40f1028b6b85f6c59fd12ee9c1e85582d HEAD"
    observed: "HEAD 為 161ab8a347c35fd323ac395eef5ca4161f3fe0f1；status 無輸出；基線祖先檢查 exit 0。"
  - command: "git archive 161ab8a347c35fd323ac395eef5ca4161f3fe0f1 | tar -x -C /tmp/wf52-review.3RH6dR；以 origin/main 的 §9.9 靜態自檢執行 /tmp/wf52-review.3RH6dR/docs/WF_EVENT_IDEMPOTENCY1.md"
    observed: "抽出 4 個 Python 區塊、probe-blocks=4、4 個皆由 3.9.6 剖析通過、違例 0、exit 0。"
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1-probe-cmd-drift1 show -s --format=%B 161ab8a347c35fd323ac395eef5ca4161f3fe0f1 | git interpret-trailers --parse"
    observed: "只解析出 Co-Authored-By；沒有 Requested-by、Planned-by 或 Implemented-by。"
  - command: "git -C /Users/ruanruan/Dev/ai-workflow diff --name-only e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 161ab8a347c35fd323ac395eef5ca4161f3fe0f1 && rg -n 'wf-review-event': /tmp/wf52-review.3RH6dR/docs/WF_EVENT_IDEMPOTENCY1.md"
    observed: "差異僅 docs/WF_EVENT_IDEMPOTENCY1.md；事件 marker 的冒號字面命中 0。"
findings:
  - finding_id: WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1-R1-001
    severity: major
    blocking: true
    finding_class: governance
    attribution: executor
    root_cause_id: governance-provenance-trailer-omission
    evidence: "被審 commit 161ab8a347c35fd323ac395eef5ca4161f3fe0f1 的 git interpret-trailers --parse 僅輸出 Co-Authored-By。AI_WORKFLOW.md §6 與 AGENTS.md 要求 T2 以上實作 commit 必有 Requested-by、Planned-by、Implemented-by；即使此權威文件修正被判為 T0/T1，§6 仍至少要求 Requested-by 與 Implemented-by。"
    disposition: "以新的、更正後 commit 補齊適用的末端連續 trailer 區塊後重新 handoff；不得 amend 已推送 commit。"
```

## 核心痛點裁定

已消失。檔頭、§4.4 節末及 §4.4 探針用法不再把 `uv run python` 說成通用釘選命令；新增 §4.4.2 明確區分驗證／閘門角色（不指定命令，等待實作卡 A 的 3.11 CI）與人工重跑角色（不釘單一命令）。此裁定與目前共用自檢「只編譯、不執行」的實測一致。故本 finding 不否定實質內容，而是阻擋交接的治理留痕缺口。

## 前一輪 accepted blocking findings 閉環

首輪，無前輪 accepted blocking finding。

## 範圍外發現

§4.4 探針對今日 main 的 cli 參數面已由 106 增至 117，四個未分類旗標使三個直譯器同為 exit 1；此項在被審文件已如實記錄、且需修改 §4.1 型別表，超出本卡單檔寫入集，未納入 findings。


## Comment 5266082291 · 2026-08-12T11:25:28Z

<!-- wf-review-event:v1 card_id=WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1 source_sha=161ab8a347c35fd323ac395eef5ca4161f3fe0f1 attempt_id=WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1-e0-161ab8a347c35fd323ac395eef5ca4161f3fe0f1 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1`　attempt_id：`WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1-e0-161ab8a347c35fd323ac395eef5ca4161f3fe0f1`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5265944399，PM 回讀重算 SHA-256 相符、未經編輯、marker 字面 0）　escalation_epoch：0
- source_sha：`161ab8a347c35fd323ac395eef5ca4161f3fe0f1`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-12T19:25:27+08:00

### self_run（查核者實跑）

- `git -C .../wf-event-idempotency1-probe-cmd-drift1 rev-parse HEAD && status --porcelain=v1 && merge-base --is-ancestor e8a638c HEAD`
  - HEAD 為 161ab8a347c35fd323ac395eef5ca4161f3fe0f1；status 無輸出；基線祖先檢查 exit 0。
- `git archive 161ab8a | tar -x -C /tmp/wf52-review.3RH6dR；以 origin/main 的 §9.9 靜態自檢執行該檔`
  - 抽出 4 個 Python 區塊、probe-blocks=4、4 個皆由 3.9.6 剖析通過、違例 0、exit 0。
- `git show -s --format=%B 161ab8a | git interpret-trailers --parse`
  - 只解析出 Co-Authored-By；沒有 Requested-by、Planned-by 或 Implemented-by。
- `git diff --name-only e8a638c 161ab8a 並 grep 事件 marker 字面`
  - 差異僅 docs/WF_EVENT_IDEMPOTENCY1.md；事件 marker 的冒號字面命中 0。

### findings（1，其中 blocking 1）

- **WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1-R1-001**　severity=major　blocking=true　class=governance　attribution=executor　root_cause_id=`governance-provenance-trailer-omission`
  - evidence：被審 commit 161ab8a 的 git interpret-trailers --parse 僅輸出 Co-Authored-By。AGENTS.md:10 要求 T2 以上實作 commit 加 Requested-by / Planned-by / Implemented-by；即使判為 T0/T1，仍至少要求 Requested-by 與 Implemented-by。
  - disposition：以新的、更正後 commit 補齊適用的末端連續 trailer 區塊後重新 handoff；不得 amend 已推送 commit。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5266110265 · 2026-08-12T11:27:17Z

## PM 補充：本 finding 成立，但它不是本卡的問題——是今日全批的問題

`R1-001`（缺 `Requested-by`／`Planned-by`／`Implemented-by` trailer）**查核者是對的**，`AGENTS.md:10` 逐字要求：

> T0/T1 commit 至少加 `Requested-by / Implemented-by`；T2 以上實作 commit 加 `Requested-by / Planned-by / Implemented-by`

但 PM 窮舉之後，範圍遠大於本卡：

```
main 上非 merge commit           193 筆，帶 Implemented-by 的 132 筆
今日（2026-08-12）落 main 的      31 筆，帶 Implemented-by 的   0 筆
最後一筆帶 trailer 的 commit      2026-08-11
在飛分支 9c80363／1e48889／0b30a82／161ab8a／85a5c7b   全部 0
```

**今日 31 筆全數違反，包含已通過跨家族查核並合併的卡**（`WF-CLEANUP-GUARD1`、`DEV-CLI-VERB-REGISTRY1` 等）。**先前四輪的查核者沒有任何一位抓到這條**，本輪的查核者是第一個。

### 歸因

查核者填 `attribution: executor`。PM 認為那不完整：**PM 的執行者提示詞從來沒有提過 trailer**，卡面驗收也沒有，而慣例在 08-11 之後整批消失。執行者依提示詞辦事而提示詞漏了——這一層是 `coordinator`。

PM **不代改查核者的 finding**（`attribution` 是查核者的判斷，不是 PM 的）。本則以獨立留言記錄範圍與 PM 這一層的責任。

### 處置

1. 本卡依裁決退回、補 trailer 後重新交付，這部分照原 disposition 走。
2. **今日其餘在飛的四張（#9、#38、#52 之外的 #57、#58，以及剛交回的 #39）同樣缺 trailer**。PM 會在下一次 handoff 前把 trailer 要求寫進執行者提示詞，並在派審詞裡列為查核者應檢項。
3. **已合併的 31 筆不追溯改寫**——本專案明令禁止事後 amend 已推送 commit，而補 trailer 只能靠改寫歷史。此為既成事實，記錄於此。
4. 沒有任何機械執行者會檢查 trailer。`DEV-AIWF-MINIMAL-CI1`（#48）正在設計最小 CI，PM 已將此項轉為該卡的候選檢查——**但那是該卡執行者的裁定，不是 PM 指派的結論**。


## Comment 5267604766 · 2026-08-12T13:40:53Z

## 派審：#52 `WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1` R2

⚠️ 審核對象 **`ruan6047/ai-workflow#52`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-idempotency1-probe-cmd-drift1
分支：claude/WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1　　被審 SHA：9f09466635e86d6180e5e0a9a88976033eac7635
基線：e8a638c40f1028b6b85f6c59fd12ee9c1e85582d　　iteration：1
寫入集：docs/WF_EVENT_IDEMPOTENCY1.md 單檔（相對基線 +40/-3，本輪 tree 未變）
```

> **權威來源**：本則與 Log 最後一筆 `handoff` 的 `SHA` 必須一致；不符時**以 handoff 事件為準並回報**。

**PM 自審**：遠端 tip 相符、`161ab8a` 是祖先（非 force）、對 main `merge-tree` **CLEAN**、相對基線寫入集**單檔**逐項對上卡面宣告零逸出、合併樹 `ea7c6e8` 實測 **701 passed**。

### 前輪閉環

R1-001（trailer 缺失）為唯一 blocking，**你上一輪已判 `core_pain_resolved: yes`**——實質內容沒有被打，卡住的是治理留痕。

### 一、處置是一個刻意的空 commit

`9f09466` 的 tree 與 `161ab8a` **完全相同**（`f746e641…`），`git diff` 空輸出。**實質內容一字未動**，執行者未順手改任何文件。

trailer 四行齊備、末端連續無空行。級別 T2 取自 Project 欄位（GraphQL 讀取，非推測），依 `AI_WORKFLOW.md:211-216` 適用三件式；`:217-220` 明定 `Reviewed-by` 只在 merge／PR 結案／B2 核可，故**未加**（加了等同自我批准）。

### 二、⚠️ 執行者指名一個它沒有解掉的矛盾，並寫進 commit body 而非只寫報告

> trailer 的語意是描述**它所附著的那個 commit** 的來歷。要讓 `161ab8a` 自己帶 trailer，唯一手段是改寫它的訊息——而它已推送，disposition 明令不得 amend，本專案也明令禁止追溯改寫。**「trailer 附著於 commit」與「禁改寫已推送歷史」在 commit 已推送後不可能同時滿足。**

它選保留歷史＋後續補記，緩解是兩個 commit 的來歷**恰好同一組人**（同卡、同需求方、同規劃者、同執行者），故補記的**值本身正確**，不存在「用 A 的來歷冒充 B 的來歷」。

**但它明列殘留缺口**：任何逐 commit 檢查仍會看到 `161ab8a` 本身是裸的。**若你的判準是「每一筆實作 commit 各自帶 trailer」，本處置不滿足，且在不改寫歷史的前提下無法滿足**——那樣的話正解是把規則改成「以卡為單位、分支上有一筆帶齊即可」，那是規則卡不是本卡射程。

**請正面裁示這個兩難。** PM 不預設答案。

### 三、⚠️ 執行者主張 `attribution` 應為 `coordinator` 而非 `executor`

依據不是「大家都沒做」，是三個機械事實（**PM 已逐項複驗屬實**）：

1. **本 repo 對 trailer 零機械強制**——全 repo 無 `.github/`（本輪）、無 git hook、`cli/` 內 `grep -rn "Implemented-by\|interpret-trailers\|Planned-by"` 在非 docs 路徑**零命中**。而 `AI_WORKFLOW.md:221` 白紙黑字寫「守衛必紅」——**那個守衛不存在**。
2. **規則本身自相矛盾**——`CLAUDE.md:10` 把 `Reviewed-by` 也列為「一律」，`AGENTS.md:10` 與 `AI_WORKFLOW.md §6` 則明確分流。**執行者若照 `CLAUDE.md` 字面辦，會在實作 commit 上加 `Reviewed-by`——那才是真正的治理事故（自我批准的形狀）。**
3. **覆蓋率斷點是集體、同日、跨執行者的**——今日落 main 的 31 筆帶 `Implemented-by` 者 **0**，最後一筆帶 trailer 是 2026-08-11，先前四輪跨家族查核**無一人抓到**。

它主張：一條沒有守衛、沒有派工詞、沒有驗收條目、四輪查核都不看的規則，其失效不可能歸給第五輪的執行者。**PM 不代改 finding 的 `attribution`（那是查核者的判斷），但要指出 PM 的執行者提示詞從未提過 trailer、卡面驗收也沒有——該層確實是 `coordinator`。**

已開卡 [`DEV-COMMIT-TRAILER-GUARD1`（#63）](https://github.com/ruan6047/ai-workflow/issues/63)統一處理該缺陷家族（含統一 `root_cause_id`、機械檢查器、與 `CLAUDE.md` 矛盾的修正）。

### 四、上一輪的範圍外發現仍然開著

§4.4 探針**今日對 main 的 `cli/` 已失效**：三個直譯器一致 `rc=1`，參數面 106 → 117，四個未分類旗標全是當日併入的（#21 路由層級、#37 授權綁定）。修它須動 §4.1 型別表，**超出單檔寫入集**。你上一輪判定它不納入 findings，本輪未變。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5267773576 · 2026-08-12T13:55:04Z

<!-- wf-review-receipt:v1
card_id: WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1
source_sha: 9f09466635e86d6180e5e0a9a88976033eac7635
report_sha256: 77c34e84e49747f1a722f36a16cd32d5d8752046b00743afd1eb6527c7280200
-->
取材規則：取本規則之後的下一個 `## 結構化裁決` 起始字元，到報告最後一個字元為止；UTF-8、LF、不可 strip；排除本收據 HTML 註解與本取材規則段落。起訖 delimiter 是「本規則之後的下一個」。

## 結構化裁決

```yaml
core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: "gh issue view 52 --repo ruan6047/ai-workflow --json body -q .body | grep handoff | tail -1; git rev-parse HEAD; git merge-base --is-ancestor e8a638c40f1028b6b85f6c59fd12ee9c1e85582d HEAD"
    observed: "最後 handoff SHA 與 HEAD 均為 9f09466635e86d6180e5e0a9a88976033eac7635；基線祖先檢查 exit 0；派審 SHA 無不符。"
  - command: "git diff --quiet 161ab8a347c35fd323ac395eef5ca4161f3fe0f1 9f09466635e86d6180e5e0a9a88976033eac7635; git show -s --format=%B <sha> | git interpret-trailers --parse"
    observed: "兩個 commit tree 相同；9f09466 解析出 Requested-by、Planned-by、Implemented-by、Co-Authored-By；161ab8a 只解析出 Co-Authored-By。"
  - command: "git archive 9f09466635e86d6180e5e0a9a88976033eac7635 | tar -x -C /tmp/wf52-r2-audit; extract §9.9 probe to /tmp; LC_ALL=C and LC_ALL=en_US.UTF-8 /usr/bin/python3 probe99.py docs/WF_EVENT_IDEMPOTENCY1.md"
    observed: "兩種 locale 均 exit 0；抽出 4 個 Python 區塊、probe-blocks=4、違例 0、RESULT PASS。"
  - command: "git diff --check e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 9f09466635e86d6180e5e0a9a88976033eac7635; git diff --name-status e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 9f09466635e86d6180e5e0a9a88976033eac7635"
    observed: "無 whitespace error；相對基線只有 docs/WF_EVENT_IDEMPOTENCY1.md，40 insertions、3 deletions。"
findings:
  - finding_id: "WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1-R2-001"
    severity: major
    blocking: true
    finding_class: governance
    attribution: coordinator
    root_cause_id: "governance-provenance-trailer-omission"
    evidence: "R1-001 的被指出對象 161ab8a347c35fd323ac395eef5ca4161f3fe0f1 仍是含 40/-3 實質文件變更的 T2 implementation commit，git interpret-trailers --parse 仍僅輸出 Co-Authored-By。9f09466 是同 tree 的後續空 commit；其 trailer 描述自己的 commit，不能附著或回填到 161ab8a。AI_WORKFLOW.md §6 與 AGENTS.md 要求 T2 以上 implementation commit 本身帶三個 trailer。"
    disposition: "原 R1 disposition 的『新增更正 commit 補齊』無法閉合逐 commit 規則，且禁 amend 已推送歷史使 executor 沒有卡內可行修法。需求方或 Coordinator 必須在 DEV-COMMIT-TRAILER-GUARD1 的規則層作前向裁定：明示此既成歷史的例外並以卡為單位採認，或維持逐 commit 規則而將本 attempt 記為不可補正的治理違規；在該裁定前不得宣告 R1-001 resolved。"
prior_round_closure:
  - finding_id: "WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1-R1-001"
    status: "not_closed"
    evidence: "9f09466 的三件式 trailer 值正確且連續，但 R1 evidence 所指 161ab8a 的 trailer 狀態未改；Git commit metadata 不會由 descendant commit 繼承。"
    disposition: "同 R2-001：需規則層處置既成歷史與逐 commit 規則的不可兼容性。"
scope_outside_findings:
  - item: "§4.4 classifier 對當前 cli 參數面有四個未分類旗標而在三個直譯器同樣失敗，屬既知單檔範圍外型別表議題；不納入本輪 finding。"
  - item: "CLAUDE.md 對 Reviewed-by 的全稱要求與 AI_WORKFLOW.md、AGENTS.md 的分流規則矛盾，已由 #63 承接；不在本卡擴審。"
```

## 核心痛點裁定

已消失。檔頭、§4.4 節末與 §4.4 探針用法不再互相要求與撤除同一個 `uv run python` 釘選；§4.4.2 已以驗證閘門與人工重跑的角色區分取代衝突指示。隔離 archive 的靜態自檢於 `LC_ALL=C` 與 `LC_ALL=en_US.UTF-8` 均為 PASS，沒有內容回退。

## 前一輪 accepted blocking finding 閉環

R1-001 未閉環。後續空 commit 不能修改或繼承先前實作 commit 的 metadata；這是規則與禁止追溯改寫歷史的治理衝突，不是可由 executor 以另一筆空 commit 修復的程式缺陷。

## 範圍外發現

本卡原始核心痛點已解決；未把既知 classifier 型別表漂移或 trailer 守衛缺失擴大為本輪額外 finding。

## Comment 5268176415 · 2026-08-12T14:28:41Z

<!-- wf-review-event:v1 card_id=WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1 source_sha=9f09466635e86d6180e5e0a9a88976033eac7635 attempt_id=WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1-e0-9f09466635e86d6180e5e0a9a88976033eac7635 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1`　attempt_id：`WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1-e0-9f09466635e86d6180e5e0a9a88976033eac7635`
- 查核者：GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5267773576 未經編輯，PM 依其取材規則（## 結構化裁決 → EOF）回讀重算 report_sha256=77c34e84… 相符。PM 的轉錄調整：自 yaml fence 內取結構化區塊，fence 外的散文（查核結論／範圍外）保存於收據雜湊範圍內，區塊內字串逐字未變　escalation_epoch：0
- source_sha：`9f09466635e86d6180e5e0a9a88976033eac7635`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-12T22:28:39+08:00

### self_run（查核者實跑）

- `gh issue view 52 --repo ruan6047/ai-workflow --json body -q .body | grep handoff | tail -1; git rev-parse HEAD; git merge-base --is-ancestor e8a638c40f1028b6b85f6c59fd12ee9c1e85582d HEAD`
  - 最後 handoff SHA 與 HEAD 均為 9f09466635e86d6180e5e0a9a88976033eac7635；基線祖先檢查 exit 0；派審 SHA 無不符。
- `git diff --quiet 161ab8a347c35fd323ac395eef5ca4161f3fe0f1 9f09466635e86d6180e5e0a9a88976033eac7635; git show -s --format=%B <sha> | git interpret-trailers --parse`
  - 兩個 commit tree 相同；9f09466 解析出 Requested-by、Planned-by、Implemented-by、Co-Authored-By；161ab8a 只解析出 Co-Authored-By。
- `git archive 9f09466635e86d6180e5e0a9a88976033eac7635 | tar -x -C /tmp/wf52-r2-audit; extract §9.9 probe to /tmp; LC_ALL=C and LC_ALL=en_US.UTF-8 /usr/bin/python3 probe99.py docs/WF_EVENT_IDEMPOTENCY1.md`
  - 兩種 locale 均 exit 0；抽出 4 個 Python 區塊、probe-blocks=4、違例 0、RESULT PASS。
- `git diff --check e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 9f09466635e86d6180e5e0a9a88976033eac7635; git diff --name-status e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 9f09466635e86d6180e5e0a9a88976033eac7635`
  - 無 whitespace error；相對基線只有 docs/WF_EVENT_IDEMPOTENCY1.md，40 insertions、3 deletions。

### findings（1，其中 blocking 1）

- **WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1-R2-001**　severity=major　blocking=true　class=governance　attribution=coordinator　root_cause_id=`governance-provenance-trailer-omission`
  - evidence：R1-001 的被指出對象 161ab8a347c35fd323ac395eef5ca4161f3fe0f1 仍是含 40/-3 實質文件變更的 T2 implementation commit，git interpret-trailers --parse 仍僅輸出 Co-Authored-By。9f09466 是同 tree 的後續空 commit；其 trailer 描述自己的 commit，不能附著或回填到 161ab8a。AI_WORKFLOW.md §6 與 AGENTS.md 要求 T2 以上 implementation commit 本身帶三個 trailer。
  - disposition：原 R1 disposition 的『新增更正 commit 補齊』無法閉合逐 commit 規則，且禁 amend 已推送歷史使 executor 沒有卡內可行修法。需求方或 Coordinator 必須在 DEV-COMMIT-TRAILER-GUARD1 的規則層作前向裁定：明示此既成歷史的例外並以卡為單位採認，或維持逐 commit 規則而將本 attempt 記為不可補正的治理違規；在該裁定前不得宣告 R1-001 resolved。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5460928231 · 2026-08-29T06:55:48Z

## 阻塞登記

**狀態**：⏸阻塞。**來源狀態：📥Backlog**（解除時回到此狀態）。

**阻塞原因**：需求方於 2026-08-29 決定，在階段狀態重整（8 階段 × 10 狀態、待審清單、CLI 射程收斂）定案並落地前，暫停所有 ai-workflow 流程卡，避免它們與重構討論互相干擾。

**可證偽的解除條件**：待審清單機制上線（label ＋ issue template ＋ 可見分組）。屆時本卡改列為清單參考項，或依當時前提是否仍成立重新排程。

**本次未做**：核心痛點、驗收條件、射程一律未動。`iteration` 未遞增。`階段` 欄未寫入。本登記僅改交付狀態與 owner。

**已知的射程重疊**（供解除時參考，非本次裁定）：#66／#38 的實質可能由「七份交接文件格式」承接；#128 可能由「待審清單收件條件三·查重留痕」＋`open --from-issue` 承接；#11 的證據紀律已部分寫入 PM 準則但痛點（靠人記得）未消失。⛔ 上述皆未經裁定，解除時須逐張重驗。

**裁定者**：需求方 ruan6047，2026-08-29 本 session 對話中指示「把目前所有 WF 卡片暫停，避免干擾目前重構討論」。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

