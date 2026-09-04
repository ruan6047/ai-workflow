# #38 WF-DISPATCH-PRECHECK1 派審詞的正確性今天完全依賴 Coordinator 手抄，且無留痕可事後稽核
- state: open  created: 2026-08-12T02:46:33Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/38
- comments: 21

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；須先自行查證兩起來源事故的真實歸因（PM 的 checkpoint 記錄與可稽核留痕不符），再判斷正解落在範本層、CLI 層還是偵測層；推理鏈中等但要求不接受上游敘述。）　查核：待指派（建議 主力型；紅線：本卡的規則約束 Coordinator 自己，而 Coordinator 即 PM，查核者須跨模型家族以避免自我背書；查核重點在條文是否有真實執行者，而非文字是否周全。）
- Initiative：—　spec 基線：自 WF-24-EVIDENCE-STRENGTH1（#11）於 2026-08-12 的射程收回切出。原條款 A 與 C 由該卡移出。收回依據見 #11 同日 amend op 30964dcc 的理由欄。
- DB：db_scope=none
- 服務的原始目標：讓派審指示的正確性成為可稽核的機械性質，而不是 Coordinator 的手抄品質

## 簡介
<!-- card-brief:begin -->
讓查核者在收到派審詞的當下就能自行判定這份輸入可不可信，且判定所需的一切都在他手上；並裁定基線 SHA 與前輪閉環回報的正解各落在範本層、CLI 層還是偵測層。**適用時機**：派審詞的基線 SHA 或 worktree 路徑抄錯，而查核者無從自查、同一份錯誤輸入產生四種行為時。⛔ 非射程：不得把規則寫進 templates/dispatch-package.md（該檔只送被約束者本人、從不進 Issue 留痕）；wfcli review 於 iteration ≥ 1 的拒收閘門被 WF-22-CLI4（aiwf#9）寫入集擋住、今天無人承接；既有留痕的修正不在射程。2026-08-13 已依 docs/ROADMAP.md §0／§3 降級，射程可能被 aiwf#66 取代。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：派審詞是查核回合的唯一輸入，而它今天由 Coordinator 手抄，查核者收到之後沒有辦法在不信任 Coordinator 的前提下自行判定這份輸入可不可信。2026-08-11 五份派審詞的基線 SHA 全部抄成當下的 origin/main（那是 PM 自己一小時前端到端實跑產生的 merge、不是任何卡的祖先）：其中 #23 的查核者依指示判 review-invalid 並停手，而 #22 的查核者反而斷言「派審指定基線仍為被審 SHA 的祖先」——實測 git merge-base --is-ancestor 0d4d282 1ee62b0 退出 1，那個祖先宣稱是假的，結論正確純屬僥倖。同一份錯誤輸入送到四位查核者產生四種行為，正是「無從自查」的直接後果。2026-08-12 又發生一次同型事故：協調者提示詞的表格用了裸的 worktree 名，#39 的查核者據以組出一個不存在的路徑並判 review-invalid，而 Issue 上的派審詞其實是對的——Coordinator 提供了一個與權威來源競爭的次要來源，查核者無從分辨哪個才算數。本卡要治的是這件事：讓查核者在收到派審詞的當下就能自行判定輸入是否可信，且判定所需的一切都在他手上。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:templates/review-prompt.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 裁定基線 SHA 的正解落在哪一層，並說明為何不是範本層。PM 的判斷是：在範本裡寫「基線須以 merge-base 產出」與現在寫「基線：<40 碼 SHA>」的可靠度差別是零，因為兩者都要人手填、都沒有東西會擋。正解是把值算出來——git_ops.is_ancestor 已存在，只差一個 merge_base()，而 handoff_cmd.py 的 --repo-path 分支已在做本機唯讀驗證。但 handoff_cmd.py 被 #25 的寫入集擋住、cli.py 被 #9 與 #30 同時擋住。請自行驗證此判斷，不要照收。
- [ ] 裁定前輪閉環回報的正解落在哪一層。三層各自的今日可動性須逐一判定：(1) templates/review-prompt.md 把散文升為必填小節（帶 finding_id 逐列），查核者收到即可自查缺節並自判 review-invalid——本卡唯一今天可動且送達對象正確的一層；(2) wfcli review 於 iteration ≥ 1 拒收未逐項指名前輪 accepted blocking finding 的報告——真正治得住的一層；(3) handoff-contract.md §2 的 review_prompt_url 與 closure_reporting_requested——canonical 已於 review-escalation.md:108/:132/:149 指名，該檔由 #35 持有。
- [ ] **（2026-08-12 更正，attribution=planner）**本卡原驗收把上一條的第 (2) 層寫成「屬 #9」，那是規劃者的錯誤斷言。#9（WF-22-CLI4）的卡面驗收逐字為「accepted 標記寫入通道（lifecycle writer 語意）；attempt_id 去重；counts_toward_escalation 推導與 checkpoint 觸發警示」，其第四項是 **checkpoint 漏建**閘門（序位 ≥3 無對應 checkpoint 即 exit 2，validation.check_checkpoint_gate），輸入、判準與失敗模式都與「報告有沒有逐項指名前輪 finding」不同；於 2ba565a 的交付碼逐檔 grep 亦確認未實作。**該閘門今天無人承接**，實作落點 review.py／validation.py／commands/review_cmd.py 三檔均在 #9 資源宣告內，故 #9 交付並釋出寫入集前任何承接卡都開不了。交付物須如實陳述「無人承接 ＋ 被誰擋住」，不得指向任何卡號。
- [ ] 本卡不得把規則寫進 templates/dispatch-package.md。實查：該檔全 repo 僅三筆文件互引（ADOPTION.md:25／AI_WORKFLOW.md:225／README.md:33），cli/ 與 scripts/ 零筆，repo 根無 .github/，且派工詞只送執行者本人、從不進 Issue。把約束 Coordinator 的規則放進只送給被約束者、從不留痕的文件裡，其唯一稽核方式是自白——那正是 #24 R4-001 判過的 claim-exceeds-evidence 形狀。
- [ ] 條款 A 的原始來源實例不成立，須以更正後的事實重寫。#21 R5 派審詞（comment 5253366028）與 #22 R2 派審詞（comment 5251999756）末段皆逐字寫有「請各自明列 resolved／withdrawn／仍開啟」，且兩則 created_at == updated_at（未編輯）。真實形態是指示有給、查核報告沒照做，attribution 應為 reviewer。須指名該治理發現：兩則 escalation-checkpoint 的歸因段落與可稽核留痕不符，而那兩則 checkpoint 是判斷執行者是否連續失敗的依據。修正既有留痕不在本卡射程，但須明列由誰承接。
- [ ] 交付物本身須通過 WF-24-EVIDENCE-STRENGTH1 的 (e)：凡寫下「必須／拒收／擋下／強制」等字眼，須指出執行者所在的檔與行；沒有機械執行者者一律寫成「約定」。**卡號指向須逐一以被指卡的卡面驗收原文核對，不得只核卡號存在**——本卡自身的驗收就犯過這個錯。

## 驗證

- [ ] 兩條規則各附一個「照舊寫法會通過、照新條款會被擋」的對照。若某條在本卡寫入集內做不出這個對照，即為該條不屬範本層的證明，須據此改寫落點裁定而非硬湊對照。
- [ ] 條款 A 的更正事實須由指令輸出產生：以 gh api 取兩則留言原文並列出其 created_at 與 updated_at，證明未經編輯，輸出逐字入交付物。不得只寫「已核對」。
- [ ] cli 測試不受影響（本卡不動 cli/）。範本改動由跨家族查核者對照兩起來源事故逐條驗證是否逾越。
- [ ] 須確認本卡與 #11 資源零相交（#11 宣告 templates/dispatch-package.md 與 AI_WORKFLOW.md，本卡宣告 templates/review-prompt.md），並實跑 assign 的寫入集相交檢查佐證兩卡可並行。
## Log

- 2026-08-12T10:46:32+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-12T11:01:28+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；分支worktree claude/WF-DISPATCH-PRECHECK1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1；交付狀態 🚧進行中；實際能力層級 主力型（卡面建議無法解析：候選路由行不符合 templates/tasks-card.md 第 4 行格式（如全形／半形空白錯置、缺分號或括號、理由為空、查核段缺失、混入零寬字元）；理由：非偏離：實際層級 主力型 與卡面建議 主力型 相符，但基線不可解析故無法機械比對。根因是 WF-CLI-ROUTING-TIER1（#21）往返缺陷的一個更寬形態：card.py:534 的 _ROUTING_PARSE_RE 以 (?P<exec_reason>[^）]+)） 錨定，PM 於 open 時在能力理由內寫入全形括號，正則在第一個全形右括號就斷。open 寫得出、assign 讀不回。此為本卡開立當下的實時重現，已回報 WF-CARD-FIELD-CORRECTION1（#37）作為往返測試語料——原先只知名字欄受影響，本次證明理由欄同樣受影響。）。
- 2026-08-12T11:12:13+08:00 handoff by wf-cli → owner 跨家族查核（本卡規則約束 Coordinator，Coordinator 即 PM，須跨家族避免自我背書）；iteration 0；SHA 075a17ed11486218c917099b738acb5451ec955d；證據 R1：交付 templates/review-prompt.md 新增 §3.1（前輪 accepted blocking finding 逐項閉環回報，per finding_id 表格）＋ §1 基線 SHA 須以 merge-base 自行重算的條目。cli 437 passed、replay 65/65，皆與改動前一致；寫入集僅 templates/review-prompt.md；新增文字含事件 marker 字面 0 處。

執行者自行複驗並推翻了 PM 原記載的事故成因，且比 PM 多驗了另一半：#21 comment 5253366028 與 #22 comment 5251999756 兩份派審詞逐字都寫有「請各自明列 resolved／withdrawn／仍開啟」，created_at == updated_at 未編輯；進一步核 #21 的 R5 review event（comment 5253717667）提及 R4-001|R4-002|R4-003 共 0 次，而派審詞提及 R4-001 共 3 次——「指示有給、報告沒照做」兩側皆獲證實而非推論。並指出兩則 escalation-checkpoint 內同時並存正確觀察與錯誤歸因（#21 的 5253853989:23 正確說報告完全未提及前輪 finding，:27 卻斷言派審詞未要求；#22 的 5255216570:13/:26/:34 稱兩次都是 coordinator 派工缺漏）。

執行者對 PM 的第二項判斷提出有證據的部分不同意：PM 判基線條款在範本層價值為零，執行者同意「無法改善 Coordinator 端的手填」，但主張範本的受眾是查核者，而基線與 source_sha 不同——它可在本機一道指令重算。舉證：同一個錯誤基線 0d4d282 送到四位查核者產生四種行為，其中 #22 的查核者斷言「派審指定基線仍為被審 SHA 的祖先」，而 git merge-base --is-ancestor 0d4d282 1ee62b0 退出 1，該祖先宣稱為假、結論正確純屬僥倖。故新增 §1 條目所擋的不是白費的那一輪（範本層擋不住，#23 的查核者已擋），而是「查核者在未經驗證的基線上完成整輪查核」。

承重約束（執行者發現並繞開）：插入新的 ## 4. 會使 §4/§5/§6 全體改號，而 §5 被 review.py／validation.py／review_cmd.py／cli/README.md／test_review.py 引用、§6 被 review-escalation.md:108/:132 與 replay_escalation_rules.py:394 引用，全部在寫入集外且數個由他卡持有。故採 §3.1 並保留 §6 原位，既有交叉引用全部維持有效。

硬界線遵守：未寫入 templates/dispatch-package.md 任何內容，並獨立複驗該檔僅 3 筆文件互引、cli/ 與 scripts/ 零筆、repo 根無 .github/。資源相交以 resources.parse_block 對 #38 與 #11 的真實 issue body 實跑 find_conflicts 得 []，非以宣稱代替。

衍生卡四項（各附阻塞者）：(1) wfcli review 於 iteration ≥ 1 的閉環閘門，阻於 #9；(2) git_ops.merge_base() 與派工時基線祖先檢查，阻於 #25（handoff_cmd.py）與 #9＋#30（cli.py），執行者另發現一個必須釘住的前提——merge_base(origin/main, source_sha) 在分支併入後會回傳分支尖端，故只在 pre-merge 正確；(3) handoff-contract.md §2 兩欄位，阻於 #35；(4) 兩則 checkpoint 的歸因更正，執行者建議由撰寫者以前向更正留言處理而非編輯，且更正後是否改變兩卡的 escalation 計數屬需求方裁定。

執行者自陳四項無機械執行者的宣稱（本卡是 #11 (e) 條的第一個受試者）：§3.1 全文無機器讀取、已於檔內標為約定並寫明無執行者；§1 基線條目的判定本身機械（git 退出碼）但「查核者會不會跑」無執行者，僅間接由 validation.py:261/:265 強制 self_run 非空——那強制的是有東西，不是這項檢查被跑過；「改號會破壞引用」以 grep 驗過但本 repo 無 CI 可攔未來改號，是它新造的無守衛不變量；以及「查核者端基線檢查可防止在未驗證基線上查核」只證明歷史上有可能，無法證明未來的查核者會跑。。
- 2026-08-12T11:35:47+08:00 amend by wf-cli（op a96c569b）→ 驗收條件：原值「[ ] 裁定基線 SHA 的正解落在哪一層，並說明為何不是範本層。PM 的判斷是：在範本裡寫「基線須以 merge-base 產出」與現在寫「基線：<40 碼 SHA>」的可靠度差別是零，因為兩者都要人手填、都沒有東西會擋。正解是把值算出來——git_ops.is_ancestor 已存在（git_ops.py:133），只差一個 merge_base()，而 handoff_cmd.py:75 的 --repo-path 分支已在做本機唯讀驗證。但 handoff_cmd.py 被 #25 持有、cli.py 被 #9 與 #30 同時持有，故本卡須明列該實作為衍生卡並指名被誰擋住，不得自行逸出寫入集。；[ ] 裁定前輪閉環回報的正解落在哪一層。三層各自的今日可動性須逐一判定：(1) templates/review-prompt.md 把 §6 的散文升為 §3 之後的必填小節（帶 finding_id 逐列），查核者收到即可自查缺節並自判 review-invalid——本卡唯一今天可動且送達對象正確的一層；(2) wfcli review 於 iteration ≥ 1 拒收未逐項指名前輪 accepted blocking finding 的報告——真正治得住的一層，屬 #9；(3) handoff-contract.md §2 的 review_prompt_url 與 closure_reporting_requested——canonical 已於 review-escalation.md:108/132/149 指名，但該檔已由 #35 持有。；[ ] 本卡不得把規則寫進 templates/dispatch-package.md。實查結果：該檔全 repo 僅三筆文件互引（ADOPTION.md:25／AI_WORKFLOW.md:225／README.md:33），cli/ 與 scripts/ 零筆，repo 根無 .github/，且派工詞只送執行者本人、從不進 Issue。把約束 Coordinator 的規則放進只送給被約束者、從不留痕的文件裡，其唯一稽核方式是自白——那正是 #24 R4-001 判過的 claim-exceeds-evidence 形狀。；[ ] 條款 A 的原始來源實例不成立，須以更正後的事實重寫。PM 原記「2026-08-11 連續兩次漏寫，使 #21 與 #22 各被觸發一次 escalation checkpoint」。逐字核對：#21 R5 派審詞（comment 5253366028，12:47:06Z）與 #22 R2 派審詞（comment 5251999756，10:32:18Z）末段皆逐字寫有「請各自明列 resolved／withdrawn／仍開啟」，且兩則 created_at == updated_at（未編輯）。真實形態是指示有給、查核報告沒照做，attribution 應為 reviewer。本卡須指名這件治理發現：兩則 escalation-checkpoint 的歸因段落與可稽核留痕不符，而那兩則 checkpoint 是判斷執行者是否連續失敗的依據。修正該兩則記錄不在本卡射程（不追溯改寫既成留痕），但須明列由誰承接。；[ ] 交付物本身須通過 WF-24-EVIDENCE-STRENGTH1 的 (e)：凡寫下「必須／拒收／擋下」等字眼，須指出執行者所在的檔與行；沒有機械執行者者一律寫成「約定」。」→ 新值「裁定基線 SHA 的正解落在哪一層，並說明為何不是範本層。PM 的判斷是：在範本裡寫「基線須以 merge-base 產出」與現在寫「基線：<40 碼 SHA>」的可靠度差別是零，因為兩者都要人手填、都沒有東西會擋。正解是把值算出來——git_ops.is_ancestor 已存在，只差一個 merge_base()，而 handoff_cmd.py 的 --repo-path 分支已在做本機唯讀驗證。但 handoff_cmd.py 被 #25 的寫入集擋住、cli.py 被 #9 與 #30 同時擋住。請自行驗證此判斷，不要照收。；裁定前輪閉環回報的正解落在哪一層。三層各自的今日可動性須逐一判定：(1) templates/review-prompt.md 把散文升為必填小節（帶 finding_id 逐列），查核者收到即可自查缺節並自判 review-invalid——本卡唯一今天可動且送達對象正確的一層；(2) wfcli review 於 iteration ≥ 1 拒收未逐項指名前輪 accepted blocking finding 的報告——真正治得住的一層；(3) handoff-contract.md §2 的 review_prompt_url 與 closure_reporting_requested——canonical 已於 review-escalation.md:108/:132/:149 指名，該檔由 #35 持有。；**（2026-08-12 更正，attribution=planner）**本卡原驗收把上一條的第 (2) 層寫成「屬 #9」，那是規劃者的錯誤斷言。#9（WF-22-CLI4）的卡面驗收逐字為「accepted 標記寫入通道（lifecycle writer 語意）；attempt_id 去重；counts_toward_escalation 推導與 checkpoint 觸發警示」，其第四項是 **checkpoint 漏建**閘門（序位 ≥3 無對應 checkpoint 即 exit 2，validation.check_checkpoint_gate），輸入、判準與失敗模式都與「報告有沒有逐項指名前輪 finding」不同；於 2ba565a 的交付碼逐檔 grep 亦確認未實作。**該閘門今天無人承接**，實作落點 review.py／validation.py／commands/review_cmd.py 三檔均在 #9 資源宣告內，故 #9 交付並釋出寫入集前任何承接卡都開不了。交付物須如實陳述「無人承接 ＋ 被誰擋住」，不得指向任何卡號。；本卡不得把規則寫進 templates/dispatch-package.md。實查：該檔全 repo 僅三筆文件互引（ADOPTION.md:25／AI_WORKFLOW.md:225／README.md:33），cli/ 與 scripts/ 零筆，repo 根無 .github/，且派工詞只送執行者本人、從不進 Issue。把約束 Coordinator 的規則放進只送給被約束者、從不留痕的文件裡，其唯一稽核方式是自白——那正是 #24 R4-001 判過的 claim-exceeds-evidence 形狀。；條款 A 的原始來源實例不成立，須以更正後的事實重寫。#21 R5 派審詞（comment 5253366028）與 #22 R2 派審詞（comment 5251999756）末段皆逐字寫有「請各自明列 resolved／withdrawn／仍開啟」，且兩則 created_at == updated_at（未編輯）。真實形態是指示有給、查核報告沒照做，attribution 應為 reviewer。須指名該治理發現：兩則 escalation-checkpoint 的歸因段落與可稽核留痕不符，而那兩則 checkpoint 是判斷執行者是否連續失敗的依據。修正既有留痕不在本卡射程，但須明列由誰承接。；交付物本身須通過 WF-24-EVIDENCE-STRENGTH1 的 (e)：凡寫下「必須／拒收／擋下／強制」等字眼，須指出執行者所在的檔與行；沒有機械執行者者一律寫成「約定」。**卡號指向須逐一以被指卡的卡面驗收原文核對，不得只核卡號存在**——本卡自身的驗收就犯過這個錯。」；理由 需求方 2026-08-12：修正卡面的假指向，attribution=planner。執行者於 0681cc7 交回時指出，假指向的源頭是本卡驗收條件 (2) 的「屬 #9」——它照卡面實作，卡面是錯的。PM 確認該斷言為規劃者錯誤：#9 的卡面驗收不含閉環回報閘門，其第四項是 checkpoint 漏建閘門（兩者輸入、判準、失敗模式皆不同），且 2ba565a 交付碼逐檔 grep 確認未實作。執行者另掃全部 100 張 open issue 的驗收段落找閉環回報閘門，只有兩筆命中（#11 已明文把該條款移出到本卡、以及本卡自己），獨立證實「無人承接」而非以宣稱代替。同時新增一條要求：卡號指向須逐一以被指卡的卡面驗收原文核對，不得只核卡號存在——這正是本卡自身犯過的錯，寫進驗收使它此後被檢查。附帶更正執行者報告中的一項錯誤（未進入交付檔）：其所有權掃描稱 templates/review-escalation.md 由 #9／#16／#39 三張宣告，PM 逐張核對 resource-claims JSON 後確認只有 #39 宣告，#9 全為 cli 檔、#16 只有 docs/WF_ORCHESTRATION_RECONCILE1.md；該錯誤未寫進 templates/review-prompt.md，檔內三處卡號指向皆準確。。
- 2026-08-12T12:02:16+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA 0681cc7f1f146d5b3ada45c7055e144ed0fd2336；證據 R1：075a17e 交付 templates/review-prompt.md 新增 §3.1（前輪 accepted blocking finding 逐 finding_id 閉環回報必填小節）＋ §1 基線須自行以 merge-base 重算的條目；0681cc7 修正 §3.1 末段的假指向。

假指向的源頭是本卡卡面驗收 (2) 的「屬 #9」，那是 PM 的規劃錯誤（已 amend op a96c569b 更正，attribution=planner）。#9 的卡面驗收不含閉環回報閘門，其第四項是 checkpoint 漏建閘門（序位 ≥3 無對應 checkpoint 即 exit 2），輸入判準失敗模式皆不同；於 2ba565a 逐檔 grep 亦確認未實作。改寫後陳述為「無人承接 ＋ 被誰擋住」：實作落點 review.py／validation.py／commands/review_cmd.py 三檔均在 #9 資源宣告內，故 #9 釋出寫入集前任何承接卡都開不了。

執行者自行複驗並比 PM 多驗了一半：#21 comment 5253366028 與 #22 comment 5251999756 兩份派審詞逐字都寫有閉環要求且未編輯；進一步核 #21 R5 的 review event（comment 5253717667）提及 R4-001|R4-002|R4-003 共 0 次而派審詞提及 R4-001 共 3 次，「指示有給、報告沒照做」兩側皆獲證實。並指出兩則 escalation-checkpoint 內同時並存正確觀察與錯誤歸因。

它對 PM 第二項判斷提出有證據的部分不同意：PM 判基線條款在範本層價值為零，執行者同意無法改善 Coordinator 端手填，但主張範本受眾是查核者且基線可在本機一道指令重算。舉證：同一錯誤基線 0d4d282 送到四位查核者產生四種行為，其中 #22 的查核者斷言「派審指定基線仍為被審 SHA 的祖先」，而 git merge-base --is-ancestor 0d4d282 1ee62b0 退出 1——該祖先宣稱為假、結論正確純屬僥倖。故該條目擋的是「查核者在未經驗證的基線上完成整輪查核」。

承重約束（執行者發現並繞開）：插入新的 ## 4. 會使 §4/§5/§6 全體改號，而 §5 被 review.py／validation.py／review_cmd.py／README／test_review.py 引用、§6 被 review-escalation.md:108/:132 與 replay_escalation_rules.py:394 引用，全在寫入集外且數個由他卡持有。故採 §3.1 並保留 §6 原位。file:line 引用已改為錨定函式名（行號會隨在飛卡漂移）。

⚠️ 執行者報告中有一項錯誤未進入交付檔，PM 已核：其所有權掃描稱 templates/review-escalation.md 由 #9／#16／#39 三張宣告，逐張核 resource-claims JSON 後確認只有 #39；#9 全為 cli 檔、#16 只有 docs/WF_ORCHESTRATION_RECONCILE1.md。檔內三處卡號指向皆準確。另其「掃了 100 張 open issue」的分母有誤——本 repo open issue 僅 14 張，它掃的應是 Project #4；PM 以 14 張為分母獨立重掃，命中仍只有 #38 與 #11（後者已明文把該條款移出到本卡），結論一致。

cli 437 passed、replay 65/65，與基線及 075a17e 逐項相同。寫入集僅 templates/review-prompt.md，節標題仍為 1,2,3,3.1,4,5,6（未改號），marker 字面 0 處。執行者自陳無機械執行者者四項：§3.1 全文、§1 基線條目（git 退出碼機械但「會不會跑」不是）、無改號不變量（本 repo 無 CI）、以及卡號指向本身的準確性（沒有東西在 #9 交付後重檢它）。。
- 2026-08-12T12:23:56+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5262202954 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=a2edd2fe… 一次相符。PM 的轉錄調整：移除包裹 YAML 的 code fence 行，並自結構化區塊末截斷「## 驗收判定」以下的散文段落——兩者皆為載體格式，區塊內字串逐字未變；被截斷的散文已完整保存於收據留言的雜湊範圍內）；core_pain_resolved no；self_run 7 項；findings 1 項（blocking 1）；attempt WF-DISPATCH-PRECHECK1-e0-0681cc7f1f146d5b3ada45c7055e144ed0fd2336。
- 2026-08-12T12:27:51+08:00 amend by wf-cli（op 166322be）→ 核心痛點：原值「派審詞是查核回合的唯一輸入，而它今天由 Coordinator 手抄、無任何機械前置檢查、其正確性事後也無從稽核。2026-08-11 五份派審詞的基線 SHA 全部抄成當下的 origin/main（那是 PM 自己一小時前端到端實跑產生的 merge、不是任何卡的祖先），#23 的查核者依指示判 review-invalid 並停手——該判定完全正確，白費一整輪。同日另有兩起事故被 PM 記成「派審詞漏寫閉環要求」，但逐字核對留痕後證實派審詞都寫了，真實形態是查核報告沒照做——連 Coordinator 對自己失誤的歸因都是錯的，因為沒有任何東西在核對。這兩類失效同源：一個需要對照既有事實才能填的欄位，被用當下手邊最方便的值填掉，而沒有任何一層會發現。」→ 新值「派審詞是查核回合的唯一輸入，而它今天由 Coordinator 手抄，查核者收到之後沒有辦法在不信任 Coordinator 的前提下自行判定這份輸入可不可信。2026-08-11 五份派審詞的基線 SHA 全部抄成當下的 origin/main（那是 PM 自己一小時前端到端實跑產生的 merge、不是任何卡的祖先）：其中 #23 的查核者依指示判 review-invalid 並停手，而 #22 的查核者反而斷言「派審指定基線仍為被審 SHA 的祖先」——實測 git merge-base --is-ancestor 0d4d282 1ee62b0 退出 1，那個祖先宣稱是假的，結論正確純屬僥倖。同一份錯誤輸入送到四位查核者產生四種行為，正是「無從自查」的直接後果。2026-08-12 又發生一次同型事故：協調者提示詞的表格用了裸的 worktree 名，#39 的查核者據以組出一個不存在的路徑並判 review-invalid，而 Issue 上的派審詞其實是對的——Coordinator 提供了一個與權威來源競爭的次要來源，查核者無從分辨哪個才算數。本卡要治的是這件事：讓查核者在收到派審詞的當下就能自行判定輸入是否可信，且判定所需的一切都在他手上。」；理由 需求方 2026-08-12 裁定 R1-001 走查核者給的第二條出路，且採「重新規劃核心痛點」而非「僅定位為約定」。原痛點的動詞是「正確性」（讓派審輸入的正確性成為可稽核的機械性質），而查核者實跑證明本卡寫入集買不到它——拋棄式目錄中一份故意省略 §3.1 的 iteration 1 報告，wfcli review --validate-only 仍 exit 0；機械落點 review.py／validation.py／commands/review_cmd.py 全在 WF-22-CLI4（#9）的資源宣告內。新痛點的動詞改為「可自查性」：讓查核者在收到派審詞當下就能自行判定輸入可否採信。本卡寫入集買得到它——templates/review-prompt.md 的讀者就是查核者，而 review-invalid 已兩次被證實是查核者真的會執行的裁決（#23 依派審詞字面停手；#39 本輪亦然）。不選「僅定位為約定」的理由：那會交付一份逐字寫著「我們寫了規則但它擋不住任何東西」的文件，而那正是本卡要治的病；問題不在誠實度，在於核心痛點的宣稱高於寫入集買得到的東西。機械閘門仍必要但屬另一張卡，本卡須明列它被誰擋住及兩者關係。裁定留痕見 issuecomment-5262272810，本次為 wfcli amend --core-pain 上線後的第一次實際使用。；授權 依需求方 ruan6047 於 https://github.com/ruan6047/ai-workflow/issues/38#issuecomment-5262272810 的裁定（GitHub comment author 已逐字核對，非留言內文自述）。
- 2026-08-12T12:28:48+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 1；SHA 0681cc7f1f146d5b3ada45c7055e144ed0fd2336；證據 R1-001（major，blocking，authoritative-artifact，attribution=planner，root_cause_id=core-pain-not-mechanically-enforced）：本卡寫入集內的條文未能使派審輸入正確性成為可稽核的機械性質。查核者實跑重現——拋棄式目錄中一份故意省略 §3.1 的 iteration 1 報告，wfcli review --validate-only 仍 exit 0（templates/review-prompt.md:11 明定基線檢查沒有東西強制查核者執行、:36 明定 §3.1 沒有機械執行者）。

查核者同時確認四件正面事實：基線條款的限制判定成立（錯誤基線的祖先檢查 exit 1 已重現）；#21／#22 的來源事故歸因更正成立；#9 假指向已移除且改號未發生（節標題仍維持 ## 4／## 5／## 6，且 #9 的資源確實涵蓋所列三個 CLI 檔但其驗收不是閉環回報閘門）；僅 templates/review-prompt.md 變更、未改 dispatch-package.md，並自行以目錄級掃描確認該檔僅由三份文件引用、cli/ 與 scripts/ 無引用、repo 根無 .github/。其判詞逐字：「條款使用『約定』並指向 validation.py 與 review_cmd.py，未虛稱現有機械執行者。惟該誠實表述同時證明核心痛點尚未解除。」

需求方 2026-08-12 裁定走第二條出路且採「重新規劃核心痛點」而非「僅定位為約定」，裁定留痕 issuecomment-5262272810，核心痛點已以 wfcli amend --core-pain --ruling-url 正式更正（op 166322be，授權綁定生效）。動詞由「正確性」改為「可自查性」。本輪執行者的工作是使交付物與新痛點一致，並明列機械閘門被誰擋住及兩者關係。。
- 2026-08-12T12:41:23+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 1；SHA 88f07b95e434a034a14c18160d60957816f4135d；證據 R2：R1-001（major，blocking，attribution=planner，core-pain-not-mechanically-enforced）依需求方裁定走出路二並採「重新規劃核心痛點」，核心痛點已以 wfcli amend --core-pain --ruling-url 正式更正（op 166322be，裁定留痕 issuecomment-5262272810，授權綁定生效）。動詞由「正確性」改為「可自查性」。

88f07b9 使交付物與新痛點一致。因動詞改變而改寫兩處論證（條文本體未動）：§1 基線理由由「防止查核者在未經驗證的基線上查核」改為「一個 repo、一道指令、一個 exit code——判定所需的全部」；§3.1 結語由「送達是必要條件不是充分條件」改為「本節買的是你看得出來，不是有人擋著」。

因新痛點納入第三個實例而新增兩處：§1「權威來源只有一個」——Issue 派審詞為唯一權威輸入，協調者提示詞、摘要表格、聊天轉述皆為次要來源且不算數，分歧本身即 finding（attribution=coordinator），並含操作面的另一半「值解不開時先回對權威來源，不要直接停手」；§3.1 carry set 改由 Issue 既有 review event 推導而非讀派審詞列出的清單（後者降級為便利摘要）。後者關掉了上一版靜默假設掉的相依——原版預設派審詞會正確列出 carry set。

執行者以原始證據而非 PM 敘述驗證 #39 事故：/Users/…/wf-escalation-resolution-gap1 MISSING、/Users/…/.claude/worktrees/wf-escalation-resolution-gap1 EXISTS、Issue 上的 R1 派審詞帶的是正確那個。

⚠️ 執行者提出並拒絕代答一個判讀問題：痛點的「能自行判定」是能力還是強制。它重跑 R1 查核者的實驗確認強制讀法買不到（故意省略 §3.1 的 iteration 1 報告，wfcli review --validate-only 仍 EXIT=0）。需求方 2026-08-12 裁定為能力，判準與給查核者的明示見 issuecomment-5262368000 附近的裁定留言。請以能力讀法評估 core_pain_resolved；若認為即使在能力讀法下仍未買到，那是正當 finding，但不得以「沒有東西擋住不可信輸入」為由判否——該理由屬已被排除的強制讀法。

機械閘門仍無人承接，其落點三檔仍在 WF-22-CLI4（#9）資源宣告內；執行者本輪重新核過 #9 仍 OPEN 且宣告未變，#37 併入 20f2ea3 未改變該歸屬。

驗證（在本分支量測，未抄任何數字）：改動前後 cli 437 passed、replay 65/65 exit 0，兩次相同；節標題仍為 1,2,3,3.1,4,5,6 無改號；marker 字面 0 處；merge-base 仍為 6e6e8ab 且已驗為 HEAD 祖先。寫入集仍只有 templates/review-prompt.md。

執行者新增一項自陳：「Issue 是權威來源」這條**同樣沒有執行者**——沒有東西阻止 Coordinator 發出競爭的次要通道，也沒有東西偵測它；該條只確保讀到它的查核者知道該信哪一個。它明言寧可講出這個限制，也不讓條文讀起來比實際強。。
- 2026-08-12T13:20:20+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5262590149 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=46247846… 一次相符。本輪四份裁決皆無需 PM 作任何格式調整——區塊零散文、序列已縮排、無 code fence）；core_pain_resolved no；self_run 6 項；findings 1 項（blocking 1）；attempt WF-DISPATCH-PRECHECK1-e0-88f07b95e434a034a14c18160d60957816f4135d。
- 2026-08-12T13:27:43+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 2；SHA 88f07b95e434a034a14c18160d60957816f4135d；證據 R1-001 判 resolved：需求方裁定 issuecomment-5262272810 選擇重新規劃路徑，op 166322be 已將核心痛點由「正確性」改為「可自查性」，88f07b9 亦將兩處論證對齊此判準。能力讀法被採納，查核者未以強制讀法判否。

R2-001（major，blocking，authoritative-artifact，executor，root_cause_id=carry-set-self-verifiability-gap）：review-prompt.md 第 32 行稱 carry set 可由 Issue 既有 review event 推導，卻未要求驗明 event 的 accepted、status 或解析可用性。R1 event 明載這些值由 lifecycle writer 另行標記，但其留言與 Issue Log 都沒有 R1-001 的 accepted/status；doctor 對同一 source（0681cc7）回報 half_written——裁決留言與 Log 索引存在，但 Project 交付狀態當時仍為待查核而非退回。故查核者面對此類既有 event 無法自行分辨該 finding 是否屬 accepted blocking carry set，也無從決定要逐列回報、忽略，或判 review-invalid。

⚠️ 查核者明確定性：「**這是資訊不足，非缺少機械拒寫閘門**」——不要把它讀成又一條需要 #9 才能修的東西。

disposition：在 review-prompt.md 明定 carry set 的**可用來源與前置驗證**：先確認相關 review event 可解析且能取得 lifecycle writer 的 accepted/status；任一前輪 event 為 marker_quarantined、half_written 或缺少該些值時，**明示 input 不可判定並自判 review-invalid**，不得把它當空 carry set，也不得以 review report 的 blocking 欄位替代 accepted。

scope_outside：R1 事件的 Project 狀態 half_written，其修復與 lifecycle 寫入交易性不在本卡寫入集內，未擴大為 finding。**PM 註：該 half_written 是本卡在 R1 裁決後隨即被交回實作、狀態往前走所致，doctor 以 source_sha 回看時看到的是當下已前移的狀態面；但查核者指出的資訊不足問題獨立於此成立——accepted/status 確實不在任何查核者讀得到的地方。**。
- 2026-08-12T16:26:10+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 2；SHA 1b4c1f196202b210eee2a8ab47f88ae896f894ba；證據 R3：R2-001（carry-set-self-verifiability-gap）已處置。

⚠️ 執行者沒有照 disposition 字面寫兩態版本，並說明了為什麼。它查了 merged main（5d22a7f）確認 accepted 的 writer 根本不存在——validate_accepted_overrides 與 mark-not-accepted 都不在，該通道還在 #9 的未合併分支上。所以**今天每一則 review event 都缺那兩個欄位**。一刀切「缺欄即 review-invalid」會讓 #9 合併前的每一輪 iteration ≥ 1 查核全部失效、**包括本卡自己的下一輪**。它的原話：「**那不是 fail-closed，是 deadlock**」，並指出 review-escalation.md §2／§4 明文禁止互鎖的閘門。

改為三態：可判定（events 可解析且 accepted/status 可取得 → carry set = accepted ∧ blocking ∧ status open，逐列回報）；不可判定（event 在已宣告的 contract-baseline cutover 之後卻是 marker_quarantined／half_written／缺欄 → 宣告 input 不可判定並自判 review-invalid，永不當空 carry set）；legacy（event 早於 cutover、或從未發過 contract-baseline → 依 §4／§5 維持原貌不得反向套進六格，**不因此判 review-invalid**，但須明示走 legacy 路徑、列出前輪 findings 並標記其 accepted 為 writer-unmarked、escalation 帳不可導出）。它把 legacy 這一態走既有的 contract-baseline 機制而非發明新語意軸（§4 line 97 對此有具名警告）。

PM 指定的硬禁令逐字寫入：**不得以 report 的 blocking 代替 accepted**，理由同附——blocking 是 reviewer 自填、accepted 是 writer 標記，替代等於讓被判定方決定自己的帳。state 3 列出前輪 findings 是**揭露不是替代**：可供人讀延續，不得進 escalation 計數。

偵測是查核者跑得動的指令而非散文：wfcli doctor --review-channel（唯讀），執行者所在 doctor.py 的 audit_review_channel，兩個判定 marker_quarantined／half_written 皆由它產出。**偵測是機械的，處置是約定**——執行者明確分開這兩件事。

它自己驗證而非採信 PM 的三項：R1 event 5262254982 line 30 帶 blocking=true 但無 accepted/status，line 37 逐字說那些由 lifecycle writer 另行標記且在該指令寫入範圍外；half_written 自行重現（doctor 回報「裁決留言與 Log 索引都在，但 Project 交付狀態為 🚧進行中，與裁決結論應有的 ↩退回 不符」），且**未接受 PM「那只是狀態往前走」的淡化**；merged main 無 contract-baseline cutover 動詞，故今天全部歷史都是 state 3。

驗證：改動前基線取自 88f07b9 的乾淨 git archive（非工作樹）得 cli 437 passed、replay 65/65；改動後 in-tree 同為 437 passed、65/65 exit 0。節標題仍 1,2,3,3.1,4,5,6 未改號。marker 字面 0。**PM 另已實測 merge(origin/main 02b5d9a, 本分支) → 658 passed 全綠**，並重算基線 6e6e8ab 與 handoff 所載相符且為祖先。

執行者自陳的無執行者宣稱四條，最後一條是新的且是它自己造的隱患：「state 3 目前是普遍狀態」只在 accepted 的 writer 未合併期間為真，**而 #9 落地後沒有東西會重新檢查這句話**——屆時該段「為什麼是三態」會過期。它寧可指名也不讓它留著。

寫入集仍只有 templates/review-prompt.md。。
- 2026-08-12T17:00:12+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5264416000 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=e58ef318… 一次相符。本批六份收據皆採內容錨定或分隔行，各自規則不同，PM 逐份照其規則計算、無需任何格式調整）；core_pain_resolved no；self_run 4 項；findings 2 項（blocking 2）；attempt WF-DISPATCH-PRECHECK1-e0-1b4c1f196202b210eee2a8ab47f88ae896f894ba。
- 2026-08-12T17:08:25+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 3；SHA 1b4c1f196202b210eee2a8ab47f88ae896f894ba；證據 R3-001 與 R3-002 兩筆 blocking，皆 authoritative-artifact／executor／carry-set-self-verifiability-gap（**同家族第二次**）。

R3-001：legacy 態以「未發 contract-baseline」為**充分**理由，不把 half_written 與 writer-unmarked 前輪輸入判 review-invalid。而本卡 R2 已由 doctor 重現為 half_written、權威 Log 沒有 cutover——**現行條文因此要求查核者把已知不可完整對帳的輸入當 legacy，而非自行拒收**，核心痛點被保留：Coordinator 未補發 cutover 時查核者不能可靠決定閉環義務。disposition：調整 legacy 邊界，缺 cutover **不得覆蓋**已被機械偵測為 half_written／marker_quarantined／缺 writer 欄位的前輪事件；或提供可由查核者執行的明確且可驗證的遷移條件。**不可把未來 writer 合併當作已完成的解除。**

R3-002：條文把 doctor 的 marker_quarantined 與 half_written 稱為**可自行跑的完整檢測**，但 audit_review_channel 的資料模型**只輸出 review-channel 狀態**，未輸出每筆 finding 的 accepted／status，**也未枚舉或驗證 contract-baseline**。三態分類需要那三類輸入，故偵測與處置的分割**不完整**。disposition：把偵測能力**如實限縮為 review-channel 健全性**，並在範本列出 accepted／status／cutover 的**可讀權威載體與逐一驗證方式**；若現況沒有該載體，**明示為不可判定而非宣稱 doctor 已涵蓋**。

⚠️ 上一輪執行者把「偵測是機械的、處置是約定」分開是對的方向，**但查核者證明偵測那一半被高估了**——doctor 涵蓋的比條文宣稱的少。。
- 2026-08-12T17:26:36+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 3；SHA 85a5c7b00bb0721b5f3899ce526bf569ec826ea9；證據 R4：R3-001 與 R3-002 皆已處置，且執行者正面回答了 PM 提的結構性問題——**三態存活，但分類軸被移除**。

它自己驗了兩半：doctor.py 提及 contract-baseline **0** 次、提及 accepted **0** 次；audit_review_channel 只回一個 status，枚舉為 recorded／receipt_untranscribed／unobservable／marker_quarantined／half_written。**PM 已獨立複驗這三項全部屬實**，並確認 main 的 cli/src 找不到 mark-not-accepted（產生器確實不存在）。結論：以 cutover 分類等於「拿查核者查不到的東西決定查核者的義務」，故換成兩個從查核者座位上查得到的軸——(1) 偵測到損壞（doctor 報 marker_quarantined／half_written，或產生器存在於被審樹卻缺欄）；(2) 產生器系統性不存在（可證明缺席）。

R3-001：state 3 現在要求**三個條件同時成立**，第三個是**正面舉證責任**——「你出示得了產生它們的 writer 不在被審樹裡」（例如 git grep 無命中，**且** Issue 上從未有事件帶過該欄）。逐字寫入：**「(iii) 舉不出來就落第 2 態」——「沒證明產生器不存在」不等於「產生器不存在」**。state 2 帶有查核者要求的那句：**缺 cutover 不是本態的赦免事由**。

**遷移條件現在是可檢查的，不是對未來合併的承諾**：state 3 在 writer 出現於被審樹的當下自動失效——同一個缺值從「從未產生」翻成「這個事件壞了」而落進 state 2，**不需要任何人宣告**。行為對照以本卡自己的 R2 實跑：doctor 對 0681cc7 報 half_written、git grep mark-not-accepted 得 0 命中；舊條文 → legacy → 不判 review-invalid，新條文 → 偵測到損壞 → state 2 → **review-invalid**，而 state 3 因 (i) 失敗而不可用。**那正是查核者說必須不能被赦免的案例。**

R3-002：偵測能力如實限縮。範本現在有三列表格分離載體並明寫邊界——doctor「能證明的只有這條通道健不健全，**證明不了 carry set 算不算得出來**」。未涵蓋的兩欄各給權威載體與指令：accepted／status 自行讀 event 留言 body（gh api …/issues/comments/<id>，逐 finding_id 比對）；**contract-baseline 今天無可讀載體、無法判定**——以表格中的一列如實陳述而非含混帶過。

(e) 作用域陳述寫入檔末：**只有通道健全性有機械執行者**（doctor.audit_review_channel，且僅限那五個枚舉值）；讀 accepted／status、證明產生器缺席、三個處置**全部是約定**——「gh api 與 git grep 是你手上的工具，**不是會擋你的閘門**」。blocking≠accepted 禁令不變，state 3 的列出仍標為**揭露不是替代**。

驗證：改動前基線取自 1b4c1f1 的乾淨 git archive 得 cli 437 passed、replay 65/65；改動後 in-tree 同為 437、65/65 exit 0。節標題仍 1,2,3,3.1,4,5,6。marker 0。**PM 另實測 merge(origin/main e8a638c, 本分支) → replay 65/65、pytest 658 passed 全綠**，並重算基線 6e6e8ab 與所載相符且為祖先。

⚠️ 執行者新造並主動上記錄的一個缺口：**產生器缺席探針把搜尋字串（mark-not-accepted）寫死為範例**。若 #9 以不同名稱落地該 writer，該範例會過期而查核者可能誤判系統性缺席。條款第二肢（Issue 上從未有事件帶過該欄）是佐證檢查，**但沒有東西強制同時用兩肢**——故該探針是**帶已知失效模式的約定**，不是可靠測試。。
- 2026-08-12T21:14:07+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 4；SHA 85a5c7b00bb0721b5f3899ce526bf569ec826ea9；證據 補記漏跑的事件：R4 查核者依本卡交付的 §3.1 第 2 態判 review-invalid 並停手，該判斷正確；但其 R4-001 的前提不成立——它要求 lifecycle writer 修復 R3 attempt 的通道一致性，而那次寫入從頭到尾成功。PM 已於 issuecomment-5266102788 貼出重現：doctor.audit_review_channel 拿歷史 attempt 的裁決結論比對當下交付狀態，無任何『事件已被取代』的概念（doctor.py:496-497 註解自承『在不引入時間語意的前提下』），故 #38 R2 attempt 88f07b9（已被取代）回報 half_written、而 #39 未被取代的 b039c0b 回報 recorded——half_written 是『卡往前走了』產生的，不是『寫入壞了』。後果：本卡交付的條文把 half_written 定為硬停，兩者相乘使任何走過一輪以上的卡都必然停手，第一個受害者是本卡自己。⚠️ PM 當時宣告退回卻沒跑本指令，狀態面因此停在 🔍待查核 直到 2026-08-12 需求方詢問才發現——這是 PM 同日第四次漏跑 handoff（另三次：#42 貼派審詞未 handoff、#39 跳過 implementation handoff、#57／#52 交回後未推進）。本輪不計為可計數 attempt，R3-001／R3-002 閉環狀態維持未判定。處置方向由執行者裁定，PM 不代答；若正解逸出單檔寫入集，指名而不代修。。
- 2026-08-13T00:24:01+08:00 handoff by wf-cli → owner 待指派；iteration 5；SHA 0ea7abad670681b708f4fbbe15526008b448abe3；證據 依 docs/ROADMAP.md §0／§3 降級：本卡屬目標 3（治理精緻化），非「防止低級事故」或「可稽核的內容」。需求方 2026-08-12 裁定降級為 Backlog、有餘力再做。⚠️ 降級不是關閉——本卡載有的真實 finding 紀錄全數保留、可逆；未閉合的 blocking 維持未閉合，本次降級不視為驗收。⚠️ WF-DISPATCH-PRECHECK1（#38）另有一項：它的射程很可能被 WF-DISPATCH-FROM-HANDOFF1（#66，走「同源產生」路線讓不一致不可能發生）取代，該裁定屬 #66 執行者，本次降級不預判。。
- 2026-08-26T22:10:10+08:00 amend by wf-cli（op f7c8f2b2）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:1430344e99e6863649cdb9a6d566c9fd3f5aa9a36d43d4414d1ad678fb60108a (730 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。
- 2026-08-29T14:57:17+08:00 handoff by wf-cli → owner 待指派；iteration 5；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 阻塞登記（來源狀態 📥Backlog）：https://github.com/ruan6047/ai-workflow/issues/38 之阻塞留言。解除條件＝待審清單機制上線。。


## Comment 5262154486 · 2026-08-12T04:07:23Z

## 派審：#38 `WF-DISPATCH-PRECHECK1` R1

⚠️ 審核對象 **`ruan6047/ai-workflow#38`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1
分支：claude/WF-DISPATCH-PRECHECK1
被審 SHA：0681cc7f1f146d5b3ada45c7055e144ed0fd2336
基線：6e6e8abd650c76fa6a2173f5dff35f99038ca1e0（已驗為祖先）
iteration：0（首輪）　寫入集：templates/review-prompt.md 單檔
```

> **`origin/main` 現為 `3e47838`，不是基線。**

### 一、它推翻了 Coordinator 的事故歸因，而且比 PM 多驗了一半

本卡的來源事故，PM 原記為「2026-08-11 派審詞漏寫閉環要求，害 #21 與 #22 各觸發一次 escalation checkpoint」。執行者逐字核對後證實**兩份派審詞都寫了**（#21 comment `5253366028`、#22 comment `5251999756`，皆 `created_at == updated_at` 未編輯）。

它另去核了 PM 沒核的另一半：**#21 R5 的 review event（comment `5253717667`）提及 `R4-001|R4-002|R4-003` 共 0 次，而派審詞提及 `R4-001` 共 3 次。** 「指示有給、報告沒照做」兩側皆獲證實，不再是推論。

**請自己驗這四則留言**，不要接受本派審詞的轉述——PM 上一次「已核對」的結論就是錯的。

它並指出一個治理發現：**兩則 escalation-checkpoint 內同時並存正確觀察與錯誤歸因**（#21 的 `5253853989`:23 正確說報告完全未提及前輪 finding，:27 卻斷言派審詞未要求）。那兩則是判斷執行者是否連續失敗的依據。**請判斷該由誰承接更正。**

### 二、它有證據地部分不同意 PM，請裁示誰對

PM 判基線條款在範本層價值為零（兩者都要人手填、都沒有東西會擋）。執行者同意前半，但主張**範本的受眾是查核者**，而基線與 `source_sha` 不同——它可在本機一道指令重算。

舉證：同一個錯誤基線 `0d4d282` 送到四位查核者產生四種行為，其中 **#22 的查核者斷言「派審指定基線仍為被審 SHA 的祖先」**，而 `git merge-base --is-ancestor 0d4d282 1ee62b0` 退出 1——**那個祖先宣稱是假的，結論正確純屬僥倖**。

故該條目擋的不是白費的那一輪（範本層擋不住，#23 的查核者已擋），而是**查核者在未經驗證的基線上完成整輪查核**。

**請判斷這個論證是否成立。** 卡面有一條驗證特意設計成可能不可滿足：「若某條在本卡寫入集內做不出『照舊寫法會通過、照新條款會被擋』的對照，**即為該條不屬範本層的證明**」——那是出口不是陷阱，硬湊假對照才是失分。

### 三、承重約束：它繞開了一個會炸掉五個檔的改號

插入新的 `## 4.` 會使 §4/§5/§6 全體改號，而 §5 被 `review.py`／`validation.py`／`review_cmd.py`／README／`test_review.py` 引用、§6 被 `review-escalation.md:108/:132` 與 `replay_escalation_rules.py:394` 引用——全在寫入集外且數個由他卡持有。故採 §3.1 並保留 §6 原位。`file:line` 引用已改為錨定**函式名**（行號會隨在飛卡漂移）。

**請驗證改號真的沒發生**，以及它列的那些引用是否完整。

### 四、假指向的源頭是卡面，不是檔案

§3.1 原寫「該閘門屬 #9」。**那是 PM 寫進卡面驗收 (2) 的規劃錯誤**（已 amend op `a96c569b` 更正，`attribution=planner`）。#9 的卡面驗收不含閉環回報閘門，其第四項是 **checkpoint 漏建**閘門，輸入判準失敗模式皆不同；於 `2ba565a` 逐檔 grep 亦確認未實作。

改寫後陳述為「**無人承接 ＋ 被誰擋住**」：實作落點三檔均在 #9 資源宣告內，故 #9 釋出寫入集前任何承接卡都開不了。

### 五、執行者報告中有一項錯誤，未進入交付檔

其所有權掃描稱 `templates/review-escalation.md` 由 #9／#16／#39 三張宣告。**PM 逐張核 `resource-claims` JSON 後確認只有 #39**；#9 全為 cli 檔、#16 只有 `docs/WF_ORCHESTRATION_RECONCILE1.md`。檔內三處卡號指向皆準確，故未擴散。

另其「掃了 100 張 open issue」的**分母有誤**——本 repo open issue 僅 **14 張**，它掃的應是 Project #4（含 cpbl-analytics 的卡）。PM 以 14 張為分母獨立重掃，命中仍只有 #38 與 #11（後者已明文把該條款移出到本卡），結論一致。**請判斷這兩項是否影響其結論的可採性。**

### 六、已知殘留

執行者自陳四項無機械執行者：§3.1 全文（已於檔內標為約定並寫明無執行者）；§1 基線條目（git 退出碼機械，但「查核者會不會跑」不是，僅間接由 `validation.py` 強制 `self_run` 非空——那強制的是**有東西**，不是這項檢查被跑過）；無改號不變量（本 repo 無 CI、無 `.github/`）；以及**卡號指向本身的準確性**——沒有東西在 #9 交付後重檢它，那是它剛修好的失敗類別，高一層。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**——散文引用與 code fence 示範都一樣。拆開書寫，發文前 `grep` 確認 0 次。

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. 首輪無前輪 finding，**但請明確寫出「首輪，無前輪 accepted blocking finding」**而非略過該節。
2. **五個 schema 欄位自己填**。
3. **留收據**：`wf-review-receipt:v1` **多行格式**（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死。⚠️ 規則若提到起訖 delimiter 的字面，請說清楚是「規則之後的下一個」——PM 上次回讀時第一次就錨到規則散文內的同名字面而失敗。

**YAML 限制**：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、值含 ` #` 須整個值加引號。


## Comment 5262202954 · 2026-08-12T04:15:31Z

<!-- wf-review-receipt:v1
card_id: WF-DISPATCH-PRECHECK1
source_sha: 0681cc7f1f146d5b3ada45c7055e144ed0fd2336
report_sha256: a2edd2fe0833db1862ceef49bf3460c08c4fbc991e9ceeb351f755bd0e2822fd
-->
取材規則：UTF-8、LF、無 strip；排除本收據 HTML 註解與本規則行，並排除起訖 delimiter 行本身。雜湊範圍為本規則之後的下一個「報告全文起點」行與其後「報告全文終點」行之間的全部內容，包含內文原有 LF。
報告全文起點
# WF-DISPATCH-PRECHECK1 R1 獨立查核

首輪，無前輪 accepted blocking finding。

核心痛點未消失。被審版本把查核者端的祖先檢查與前輪閉環回報寫成約定，但沒有把派審輸入正確性變成可稽核的機械性質；錯誤基線仍可由 Coordinator 手填，且 iteration ≥ 1 缺閉環逐列回報的報告仍能通過寫入前驗證。

```yaml
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git rev-parse HEAD && git status --porcelain && git merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD"
    observed: "HEAD=0681cc7f1f146d5b3ada45c7055e144ed0fd2336；工作區乾淨；祖先檢查 exit 0"
  - command: "git merge-base --is-ancestor 0d4d282 1ee62b0"
    observed: "exit 1，驗證派審詞所述錯誤基線不是被審 SHA 的祖先"
  - command: "git diff --check 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0..0681cc7f1f146d5b3ada45c7055e144ed0fd2336 && git diff --name-only 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0..0681cc7f1f146d5b3ada45c7055e144ed0fd2336"
    observed: "diff 無空白錯誤；僅 templates/review-prompt.md"
  - command: "git archive 0681cc7f1f146d5b3ada45c7055e144ed0fd2336 | tar -x -C /tmp/wf38-review.NAolIl; cd /tmp/wf38-review.NAolIl/cli && uv run pytest -q"
    observed: "437 passed"
  - command: "cd /tmp/wf38-review.NAolIl/cli && uv run wfcli review WF-DISPATCH-PRECHECK1 --input /tmp/wf38-review.NAolIl/missing-closure.yaml --source-sha 0681cc7f1f146d5b3ada45c7055e144ed0fd2336 --reviewer GPT-5@Codex --escalation-epoch 1 --validate-only"
    observed: "缺少 §3.1 的 iteration 1 對照報告仍驗證通過；exit 0；未寫入狀態"
  - command: "gh api repos/ruan6047/ai-workflow/issues/comments/5253366028; gh api repos/ruan6047/ai-workflow/issues/comments/5251999756; gh api repos/ruan6047/ai-workflow/issues/comments/5253717667; gh api repos/ruan6047/ai-workflow/issues/comments/5253853989"
    observed: "#21 與 #22 派審詞皆含逐項閉環要求且 created_at=updated_at；#21 R5 報告未提 R4-001、R4-002、R4-003；checkpoint 同時含正確觀察與錯誤的派審缺漏歸因"
  - command: "gh issue view 9 --repo ruan6047/ai-workflow --json body; git show 2ba565a -- cli/src/wf_cli/review.py cli/src/wf_cli/validation.py cli/src/wf_cli/commands/review_cmd.py"
    observed: "#9 資源涵蓋三個 CLI 落點，但其驗收實作是 accepted、attempt_id、counts 與 checkpoint 漏建，不是閉環逐列閘門"
findings:
  - finding_id: "WF-DISPATCH-PRECHECK1-R1-001"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: planner
    root_cause_id: "core-pain-not-mechanically-enforced"
    evidence: "templates/review-prompt.md:11 明定基線檢查沒有東西強制查核者執行；:36 明定 §3.1 沒有機械執行者。拋棄式目錄中的 iteration 1 報告故意省略 §3.1，wfcli review --validate-only 仍 exit 0。故本卡寫入集內的條文未能使派審輸入正確性成為可稽核的機械性質。"
    disposition: "在可寫入 handoff 與 review writer 的卡上實作基線祖先前置檢查及 iteration ≥ 1 carry-set 逐 finding_id 驗證；本卡須在卡面或交付物如實把目前變更定位為非阻擋的查核者約定，或將核心痛點重規劃為該可達目標後再送審。"
```

## 驗收判定

- 基線條款的限制判定成立：範本可提醒查核者，不能在 Coordinator 填寫或派審送出時機械擋錯；錯誤基線的祖先檢查 exit 1 已重現。
- #21 與 #22 的來源事故歸因更正成立：兩份派審詞均有閉環要求，失效在 #21 R5 報告未逐項回報。既有 checkpoint 的錯誤歸因應由其原撰寫者以追加更正留言承接，是否改變 escalation 計數留給需求方裁定。
- #9 假指向已移除且改號未發生：目標檔仍維持 ## 4、## 5、## 6；#9 的資源確實涵蓋所列三個 CLI 檔，但 #9 的驗收不是閉環回報閘門。這不足以使目前無人的閘門成為已承接交付。
- 條款使用「約定」並指向 validation.py 與 review_cmd.py，未虛稱現有機械執行者。惟該誠實表述同時證明核心痛點尚未解除。
- 僅 templates/review-prompt.md 變更；未改 templates/dispatch-package.md。目錄級掃描確認 dispatch-package.md 僅由 ADOPTION.md、AI_WORKFLOW.md、README.md 引用，cli/、scripts/ 無引用，repo 根無 .github/。

## 範圍外發現

無。

報告全文終點


## Comment 5262254982 · 2026-08-12T04:23:57Z

<!-- wf-review-event:v1 card_id=WF-DISPATCH-PRECHECK1 source_sha=0681cc7f1f146d5b3ada45c7055e144ed0fd2336 attempt_id=WF-DISPATCH-PRECHECK1-e0-0681cc7f1f146d5b3ada45c7055e144ed0fd2336 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-DISPATCH-PRECHECK1`　attempt_id：`WF-DISPATCH-PRECHECK1-e0-0681cc7f1f146d5b3ada45c7055e144ed0fd2336`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5262202954 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=a2edd2fe… 一次相符。PM 的轉錄調整：移除包裹 YAML 的 code fence 行，並自結構化區塊末截斷「## 驗收判定」以下的散文段落——兩者皆為載體格式，區塊內字串逐字未變；被截斷的散文已完整保存於收據留言的雜湊範圍內）　escalation_epoch：0
- source_sha：`0681cc7f1f146d5b3ada45c7055e144ed0fd2336`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T12:23:56+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git status --porcelain && git merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD`
  - HEAD=0681cc7f1f146d5b3ada45c7055e144ed0fd2336；工作區乾淨；祖先檢查 exit 0
- `git merge-base --is-ancestor 0d4d282 1ee62b0`
  - exit 1，驗證派審詞所述錯誤基線不是被審 SHA 的祖先
- `git diff --check 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0..0681cc7f1f146d5b3ada45c7055e144ed0fd2336 && git diff --name-only 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0..0681cc7f1f146d5b3ada45c7055e144ed0fd2336`
  - diff 無空白錯誤；僅 templates/review-prompt.md
- `git archive 0681cc7f1f146d5b3ada45c7055e144ed0fd2336 | tar -x -C /tmp/wf38-review.NAolIl; cd /tmp/wf38-review.NAolIl/cli && uv run pytest -q`
  - 437 passed
- `cd /tmp/wf38-review.NAolIl/cli && uv run wfcli review WF-DISPATCH-PRECHECK1 --input /tmp/wf38-review.NAolIl/missing-closure.yaml --source-sha 0681cc7f1f146d5b3ada45c7055e144ed0fd2336 --reviewer GPT-5@Codex --escalation-epoch 1 --validate-only`
  - 缺少 §3.1 的 iteration 1 對照報告仍驗證通過；exit 0；未寫入狀態
- `gh api repos/ruan6047/ai-workflow/issues/comments/5253366028; gh api repos/ruan6047/ai-workflow/issues/comments/5251999756; gh api repos/ruan6047/ai-workflow/issues/comments/5253717667; gh api repos/ruan6047/ai-workflow/issues/comments/5253853989`
  - #21 與 #22 派審詞皆含逐項閉環要求且 created_at=updated_at；#21 R5 報告未提 R4-001、R4-002、R4-003；checkpoint 同時含正確觀察與錯誤的派審缺漏歸因
- `gh issue view 9 --repo ruan6047/ai-workflow --json body; git show 2ba565a -- cli/src/wf_cli/review.py cli/src/wf_cli/validation.py cli/src/wf_cli/commands/review_cmd.py`
  - #9 資源涵蓋三個 CLI 落點，但其驗收實作是 accepted、attempt_id、counts 與 checkpoint 漏建，不是閉環逐列閘門

### findings（1，其中 blocking 1）

- **WF-DISPATCH-PRECHECK1-R1-001**　severity=major　blocking=true　class=authoritative-artifact　attribution=planner　root_cause_id=`core-pain-not-mechanically-enforced`
  - evidence：templates/review-prompt.md:11 明定基線檢查沒有東西強制查核者執行；:36 明定 §3.1 沒有機械執行者。拋棄式目錄中的 iteration 1 報告故意省略 §3.1，wfcli review --validate-only 仍 exit 0。故本卡寫入集內的條文未能使派審輸入正確性成為可稽核的機械性質。
  - disposition：在可寫入 handoff 與 review writer 的卡上實作基線祖先前置檢查及 iteration ≥ 1 carry-set 逐 finding_id 驗證；本卡須在卡面或交付物如實把目前變更定位為非阻擋的查核者約定，或將核心痛點重規劃為該可達目標後再送審。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5262272810 · 2026-08-12T04:26:55Z

## 需求方裁定：R1-001 走第二條——重新規劃核心痛點

查核者於 `0681cc7` 判 `REQUEST_CHANGES`，唯一 blocking 是 `WF-DISPATCH-PRECHECK1-R1-001`（major，`authoritative-artifact`，**`attribution: planner`**，`root_cause_id: core-pain-not-mechanically-enforced`），並實跑重現：拋棄式目錄中一份**故意省略 §3.1** 的 iteration 1 報告，`wfcli review --validate-only` 仍 **exit 0**。

其 disposition 給了兩條出路：

1. 在可寫入 handoff 與 review writer 的卡上實作機械閘門；
2. **本卡如實把目前變更定位為非阻擋的查核者約定，或將核心痛點重規劃為該可達目標後再送審。**

**需求方 2026-08-12 裁定：走第二條，且採「重新規劃核心痛點」而非「僅定位為約定」。**

### 為什麼不選第一條

實作落點 `review.py`／`validation.py`／`commands/review_cmd.py` 全在 `WF-22-CLI4`（#9）的資源宣告內。在 #9 交付並釋出寫入集之前，本卡碰不到它們；而 #9 今天也被退回中。等它等於把本卡無限期掛住。

### 為什麼不選「僅定位為約定」

那會讓本卡交付一份逐字寫著「我們寫了規則但它擋不住任何東西」的文件——**而那正是本卡原本要治的病**。`WF-24-EVIDENCE-STRENGTH1`（#11）正在新增的 (e) 條（守衛的作用域宣稱）要求沒有機械執行者時寫成「約定」而非「強制」，本卡的交付**已經做到了那件事**；問題不在誠實度，在於**核心痛點的宣稱高於本卡寫入集買得到的東西**。

### 重新規劃的方向

原痛點的動詞是「**正確性**」：讓派審輸入的正確性成為可稽核的機械性質。那需要寫入端閘門，逸出本卡寫入集。

新痛點的動詞改為「**可自查性**」：讓查核者在**收到派審詞的當下**就能自行判定輸入是否可信，而不必依賴 Coordinator 填對。這個目標本卡寫入集買得到——`templates/review-prompt.md` 的讀者就是查核者，而 `review-invalid` 已被證實是查核者真的會執行的裁決（#23 那次依派審詞字面判 `review-invalid` 並停手；本卡 #39 的 `review-invalid` 是第二次）。

差別是實質的：**正確性需要有人擋，可自查性只需要有人看得出來。** 前者今天做不到，後者今天做得到，而且它是前者的前置——閘門要擋什麼，得先有人能說清楚「不可信長什麼樣」。

機械閘門仍是必要的，但它屬另一張卡，本卡須明列它被誰擋住、以及本卡的約定與它的關係。

### 這則留言的用途

依 `WF-CARD-FIELD-CORRECTION1`（#37，已於 `20f2ea3` 併入 main）新上線的 `wfcli amend --core-pain --ruling-url`，核心痛點的更正必須綁定一則需求方裁定留言的 URL，取其 GitHub comment author 逐字比對卡面「需求：」欄。**本則即該裁定留痕**，下一步的 `amend` 將指向它。

這是 `--core-pain` 的第一次實際使用。

## Comment 5262359728 · 2026-08-12T04:41:08Z

## 需求方裁定：新痛點的「能自行判定」指**能力**，不是**強制**

執行者於 `88f07b9` 交回時提出一個它拒絕代答的判讀問題，並明言兩種讀法下的結論相反：

> 痛點說查核者「**能**自行判定」——是能力，不是強制。能力這個讀法下本卡買得到；**強制的讀法下本卡買不到，我不會宣稱相反。**

它並重跑了 R1 查核者的實驗確認強制讀法確實買不到：故意省略 §3.1 的 iteration 1 報告，`wfcli review --validate-only` 仍 **EXIT=0**。

**需求方 2026-08-12 裁定：能力。**

### 判準

三件事使能力成為本卡的正確目標，而非退而求其次：

1. **`review-prompt.md` 就在查核者進駐的那個 repo 裡**，所以「判定所需的一切都在他手上」對這份檔是字面為真，不是修辭。
2. **兩個已知輸入缺陷都是一道指令的距離**，執行者已各自重現：錯誤基線 `git merge-base --is-ancestor 0d4d282 1ee62b0` 退出 1；次要來源的路徑 `test -d` MISSING 而權威來源 EXISTS。
3. **`review-invalid` 已三次被證實是查核者真的會執行的裁決**（#23 依派審詞字面停手；#39 本輪亦然；本卡 R1 判 `REQUEST_CHANGES` 而非放行）。文字條款對這個讀者群是有效的執行者。

### 這不是把機械閘門降級

閘門仍必要，而且**能力是它的前置**——閘門要擋什麼，得先有人能說清楚「不可信長什麼樣」。閘門屬另一張卡，其實作落點 `review.py`／`validation.py`／`review_cmd.py` 目前仍在 `WF-22-CLI4`（#9）的資源宣告內，故在 #9 交付並釋出寫入集之前任何承接卡都開不了。**該事實須留在交付物中，不得因本裁定而淡化。**

### 給下一輪查核者的明示

**請以能力讀法評估 `core_pain_resolved`。** 若你認為即使在能力讀法下本卡仍未買到它，那是完全正當的 finding；但請不要以「沒有東西擋住不可信的輸入」為由判否——**那是強制讀法，已由需求方明確排除**。

執行者本輪並主動關掉了一個它上一版靜默假設掉的相依：§3.1 的 carry set 改為由 Issue 上的既有 review event 推導，而非讀派審詞列出的清單（後者降級為便利摘要）。那是「判定所需的一切都在他手上」的實質兌現，不是措辭調整。

## Comment 5262453854 · 2026-08-12T04:55:51Z

## 派審：#38 `WF-DISPATCH-PRECHECK1` R2

⚠️ 審核對象 **`ruan6047/ai-workflow#38`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1
分支：claude/WF-DISPATCH-PRECHECK1　　被審 SHA：88f07b95e434a034a14c18160d60957816f4135d
基線：6e6e8abd650c76fa6a2173f5dff35f99038ca1e0（已驗為祖先）　　iteration：1
寫入集：templates/review-prompt.md 單檔
```

> **本則為權威。** 摘要表格與轉述若衝突以本則為準；**值解不開時先回對本則，不要直接停手**。

### ⚠️ 需求方已裁定一個會決定本輪判準的判讀

你的 R1-001 是對的，其 `attribution: planner` 也是對的。需求方採你的第二條出路，且採「**重新規劃核心痛點**」而非「僅定位為約定」——核心痛點已以 `wfcli amend --core-pain --ruling-url` 正式更正（op `166322be`，裁定留痕 `issuecomment-5262272810`）。**動詞由「正確性」改為「可自查性」。**

執行者交回時提出並**拒絕代答**一個判讀問題：痛點的「**能**自行判定」是**能力**還是**強制**。它重跑你的實驗確認強制讀法買不到（故意省略 §3.1 的 iteration 1 報告，`wfcli review --validate-only` 仍 **EXIT=0**）。

**需求方 2026-08-12 裁定：能力**（判準見 `issuecomment-5262359728`）。

**請以能力讀法評估 `core_pain_resolved`。** 若你認為即使在能力讀法下本卡仍未買到它，那是完全正當的 finding；**但請不要以「沒有東西擋住不可信的輸入」為由判否——那是強制讀法，已由需求方明確排除。**

### 一、因動詞改變而改寫的兩處論證（條文本體未動）

- §1 基線理由：由「防止查核者在未經驗證的基線上查核」改為「一個 repo、一道指令、一個 exit code——判定所需的全部」
- §3.1 結語：由「送達是必要條件不是充分條件」改為「本節買的是你看得出來，不是有人擋著」

**請判斷**：只換論證不換條文，是否構成對新痛點的真實兌現，還是把同一份東西重新包裝？

### 二、因新痛點納入第三個實例而新增的兩處

**§1「權威來源只有一個」**——Issue 派審詞為唯一權威輸入；協調者提示詞、摘要表格、聊天轉述皆為次要來源且不算數；分歧本身即 finding（`attribution: coordinator`）。並含操作面的另一半：**值解不開時先回對權威來源，不要直接停手**。

該實例是 2026-08-12 的真事：協調者提示詞的表格用了裸的 worktree 名，**#39 的查核者據以組出一個不存在的路徑並判 `review-invalid`，而 Issue 上的派審詞其實是對的**。執行者以原始證據而非 PM 敘述驗證（兩個路徑一個 MISSING 一個 EXISTS）。

**§3.1 carry set 改由 Issue 既有 review event 推導**，派審詞列出的清單降級為便利摘要。這關掉了上一版**靜默假設掉**的相依——原版預設派審詞會正確列出 carry set。

**請攻擊**：(a) 「Issue 是權威」這條**同樣沒有執行者**（執行者已自陳）——沒有東西阻止 Coordinator 發出競爭通道，也沒有東西偵測它。那條只確保**讀到它的**查核者知道該信哪一個。這夠嗎？(b) carry set 改由 review event 推導後，**若那些 event 本身被 `marker_quarantined` 呢**？（本 repo 有三張卡處於該狀態）

### 三、機械閘門仍無人承接

實作落點三檔仍在 **#9** 的資源宣告內，執行者本輪重新核過 #9 仍 OPEN 且宣告未變；#37 併入 `20f2ea3` 未改變該歸屬。**請自行複核，不要採信轉述。**

### 四、門檻

iteration 1，第二個可計數 attempt，未達 checkpoint 門檻。R1-001 家族名 `core-pain-not-mechanically-enforced`；若你判定它仍開啟，**請沿用**。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**（`resolved`／`withdrawn`／仍開啟）並附證據。
2. **五個 schema 欄位自己填**。`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` **多行格式**（`card_id:` 與 `source_sha:` **各自獨立成行**，單行 `key=value` 形式 `doctor` 認不得），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍。**規則若提到起訖 delimiter 的字面，請說清楚是「本規則之後的下一個」。**

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、值含 ` #` 須整個值加引號、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**。非 schema 的頂層鍵會被容忍。


## Comment 5262582277 · 2026-08-12T05:12:13Z

<!-- wf-review-receipt:v1
card_id: WF-DISPATCH-PRECHECK1
source_sha: 88f07b95e434a034a14c18160d60957816f4135d
report_sha256: 462478467957af22a4c8a46565cf5cb61fac73994f1b5bd7848629d32921deb3
-->
取材規則：UTF-8、LF、無 strip；排除本收據 HTML 註解、本規則行與起訖 delimiter 行本身。雜湊範圍是本規則之後的下一個「報告全文起點」行與其後「報告全文終點」行之間的全部內容，包含報告原有末尾 LF。
報告全文起點core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git rev-parse HEAD && git status --porcelain && git merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD"
    observed: "HEAD=88f07b95e434a034a14c18160d60957816f4135d；工作區乾淨；基線祖先檢查 exit 0。"
  - command: "git diff --check 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 88f07b95e434a034a14c18160d60957816f4135d && git diff --name-only 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 88f07b95e434a034a14c18160d60957816f4135d"
    observed: "無 whitespace error；寫入集只有 templates/review-prompt.md。"
  - command: "git archive 88f07b95e434a034a14c18160d60957816f4135d | tar -x -C /tmp/wf38-r2.kkdz3m && cd /tmp/wf38-r2.kkdz3m/cli && uv run pytest -q"
    observed: "437 passed。"
  - command: "gh issue view 38 --repo ruan6047/ai-workflow --json body,comments"
    observed: "R1 的 review event 明言 accepted/status/counts 由 lifecycle writer 另行標記；該 event 本身未帶 accepted 或 status，Issue body 的 R1 handoff 行同樣沒有這兩欄。"
  - command: "cd cli && uv run wfcli doctor .. --registry none --review-channel --repo ruan6047/ai-workflow --issue-number 38 --card-id WF-DISPATCH-PRECHECK1 --owner ruan6047 --project 4 --source-sha 0681cc7f1f146d5b3ada45c7055e144ed0fd2336 --json"
    observed: "R1 source 的 review channel 狀態為 half_written；裁決留言與 Log 索引存在，但 Project 交付狀態仍為待查核而非退回。"
  - command: "gh issue view 9 --repo ruan6047/ai-workflow --json state,body"
    observed: "Issue 9 仍 OPEN；其資源宣告包含 review.py、validation.py、commands/review_cmd.py，且卡面明列 accepted 標記與 checkpoint 寫入，但本卡未碰 CLI 實作。"
prior_accepted_blocking_findings:
  - finding_id: WF-DISPATCH-PRECHECK1-R1-001
    status: resolved
    evidence: "需求方裁定 issuecomment-5262272810 選擇 disposition 的重新規劃路徑；Issue body Log 的 op 166322be 已將核心痛點由正確性改為可自查性，88f07b9 亦將兩處論證對齊此判準。"
findings:
  - finding_id: WF-DISPATCH-PRECHECK1-R2-001
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: carry-set-self-verifiability-gap
    evidence: "templates/review-prompt.md 第 32 行稱 carry set 可由 Issue 既有 review event 推導，卻未要求驗明 event 的 accepted、status 或解析可用性。R1 event 明載這些值由 lifecycle writer 另行標記，但其留言與 Issue Log 都沒有 R1-001 的 accepted/status；doctor 對同一 source 回報 half_written。故查核者面對此類既有 event 無法自行分辨該 finding 是否屬 accepted blocking carry set，也無從決定要逐列回報、忽略，或判 review-invalid。這是資訊不足，非缺少機械拒寫閘門。"
    disposition: "在 review-prompt.md 明定 carry set 的可用來源與前置驗證：先確認相關 review event 可解析且能取得 lifecycle writer 的 accepted/status；任一前輪 event 為 marker_quarantined、half_written 或缺少該些值時，明示 input 不可判定並自判 review-invalid，不得把它當空 carry set 或以 review report 的 blocking 欄位替代 accepted。"
scope_outside_findings:
  - topic: "R1 事件的 Project 狀態半寫入"
    observation: "doctor 已回報 R1 為 half_written；修復其 Project 交付狀態與 lifecycle 寫入交易性不在本卡寫入集內，未擴大為 finding。"
報告全文終點

## Comment 5262590149 · 2026-08-12T05:12:54Z

<!-- wf-review-receipt:v1
card_id: WF-DISPATCH-PRECHECK1
source_sha: 88f07b95e434a034a14c18160d60957816f4135d
report_sha256: 462478467957af22a4c8a46565cf5cb61fac73994f1b5bd7848629d32921deb3
-->
取材規則：UTF-8、LF、無 strip；排除本收據 HTML 註解、本規則行與起訖 delimiter 行本身。雜湊範圍是本規則之後的下一個「報告全文起點」行與其後「報告全文終點」行之間的全部內容，包含報告原有末尾 LF。
報告全文起點
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git rev-parse HEAD && git status --porcelain && git merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD"
    observed: "HEAD=88f07b95e434a034a14c18160d60957816f4135d；工作區乾淨；基線祖先檢查 exit 0。"
  - command: "git diff --check 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 88f07b95e434a034a14c18160d60957816f4135d && git diff --name-only 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 88f07b95e434a034a14c18160d60957816f4135d"
    observed: "無 whitespace error；寫入集只有 templates/review-prompt.md。"
  - command: "git archive 88f07b95e434a034a14c18160d60957816f4135d | tar -x -C /tmp/wf38-r2.kkdz3m && cd /tmp/wf38-r2.kkdz3m/cli && uv run pytest -q"
    observed: "437 passed。"
  - command: "gh issue view 38 --repo ruan6047/ai-workflow --json body,comments"
    observed: "R1 的 review event 明言 accepted/status/counts 由 lifecycle writer 另行標記；該 event 本身未帶 accepted 或 status，Issue body 的 R1 handoff 行同樣沒有這兩欄。"
  - command: "cd cli && uv run wfcli doctor .. --registry none --review-channel --repo ruan6047/ai-workflow --issue-number 38 --card-id WF-DISPATCH-PRECHECK1 --owner ruan6047 --project 4 --source-sha 0681cc7f1f146d5b3ada45c7055e144ed0fd2336 --json"
    observed: "R1 source 的 review channel 狀態為 half_written；裁決留言與 Log 索引存在，但 Project 交付狀態仍為待查核而非退回。"
  - command: "gh issue view 9 --repo ruan6047/ai-workflow --json state,body"
    observed: "Issue 9 仍 OPEN；其資源宣告包含 review.py、validation.py、commands/review_cmd.py，且卡面明列 accepted 標記與 checkpoint 寫入，但本卡未碰 CLI 實作。"
prior_accepted_blocking_findings:
  - finding_id: WF-DISPATCH-PRECHECK1-R1-001
    status: resolved
    evidence: "需求方裁定 issuecomment-5262272810 選擇 disposition 的重新規劃路徑；Issue body Log 的 op 166322be 已將核心痛點由正確性改為可自查性，88f07b9 亦將兩處論證對齊此判準。"
findings:
  - finding_id: WF-DISPATCH-PRECHECK1-R2-001
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: carry-set-self-verifiability-gap
    evidence: "templates/review-prompt.md 第 32 行稱 carry set 可由 Issue 既有 review event 推導，卻未要求驗明 event 的 accepted、status 或解析可用性。R1 event 明載這些值由 lifecycle writer 另行標記，但其留言與 Issue Log 都沒有 R1-001 的 accepted/status；doctor 對同一 source 回報 half_written。故查核者面對此類既有 event 無法自行分辨該 finding 是否屬 accepted blocking carry set，也無從決定要逐列回報、忽略，或判 review-invalid。這是資訊不足，非缺少機械拒寫閘門。"
    disposition: "在 review-prompt.md 明定 carry set 的可用來源與前置驗證：先確認相關 review event 可解析且能取得 lifecycle writer 的 accepted/status；任一前輪 event 為 marker_quarantined、half_written 或缺少該些值時，明示 input 不可判定並自判 review-invalid，不得把它當空 carry set 或以 review report 的 blocking 欄位替代 accepted。"
scope_outside_findings:
  - topic: "R1 事件的 Project 狀態半寫入"
    observation: "doctor 已回報 R1 為 half_written；修復其 Project 交付狀態與 lifecycle 寫入交易性不在本卡寫入集內，未擴大為 finding。"
報告全文終點

## Comment 5262674597 · 2026-08-12T05:20:22Z

<!-- wf-review-event:v1 card_id=WF-DISPATCH-PRECHECK1 source_sha=88f07b95e434a034a14c18160d60957816f4135d attempt_id=WF-DISPATCH-PRECHECK1-e0-88f07b95e434a034a14c18160d60957816f4135d -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-DISPATCH-PRECHECK1`　attempt_id：`WF-DISPATCH-PRECHECK1-e0-88f07b95e434a034a14c18160d60957816f4135d`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5262590149 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=46247846… 一次相符。本輪四份裁決皆無需 PM 作任何格式調整——區塊零散文、序列已縮排、無 code fence）　escalation_epoch：0
- source_sha：`88f07b95e434a034a14c18160d60957816f4135d`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T13:20:20+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git status --porcelain && git merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD`
  - HEAD=88f07b95e434a034a14c18160d60957816f4135d；工作區乾淨；基線祖先檢查 exit 0。
- `git diff --check 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 88f07b95e434a034a14c18160d60957816f4135d && git diff --name-only 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 88f07b95e434a034a14c18160d60957816f4135d`
  - 無 whitespace error；寫入集只有 templates/review-prompt.md。
- `git archive 88f07b95e434a034a14c18160d60957816f4135d | tar -x -C /tmp/wf38-r2.kkdz3m && cd /tmp/wf38-r2.kkdz3m/cli && uv run pytest -q`
  - 437 passed。
- `gh issue view 38 --repo ruan6047/ai-workflow --json body,comments`
  - R1 的 review event 明言 accepted/status/counts 由 lifecycle writer 另行標記；該 event 本身未帶 accepted 或 status，Issue body 的 R1 handoff 行同樣沒有這兩欄。
- `cd cli && uv run wfcli doctor .. --registry none --review-channel --repo ruan6047/ai-workflow --issue-number 38 --card-id WF-DISPATCH-PRECHECK1 --owner ruan6047 --project 4 --source-sha 0681cc7f1f146d5b3ada45c7055e144ed0fd2336 --json`
  - R1 source 的 review channel 狀態為 half_written；裁決留言與 Log 索引存在，但 Project 交付狀態仍為待查核而非退回。
- `gh issue view 9 --repo ruan6047/ai-workflow --json state,body`
  - Issue 9 仍 OPEN；其資源宣告包含 review.py、validation.py、commands/review_cmd.py，且卡面明列 accepted 標記與 checkpoint 寫入，但本卡未碰 CLI 實作。

### findings（1，其中 blocking 1）

- **WF-DISPATCH-PRECHECK1-R2-001**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`carry-set-self-verifiability-gap`
  - evidence：templates/review-prompt.md 第 32 行稱 carry set 可由 Issue 既有 review event 推導，卻未要求驗明 event 的 accepted、status 或解析可用性。R1 event 明載這些值由 lifecycle writer 另行標記，但其留言與 Issue Log 都沒有 R1-001 的 accepted/status；doctor 對同一 source 回報 half_written。故查核者面對此類既有 event 無法自行分辨該 finding 是否屬 accepted blocking carry set，也無從決定要逐列回報、忽略，或判 review-invalid。這是資訊不足，非缺少機械拒寫閘門。
  - disposition：在 review-prompt.md 明定 carry set 的可用來源與前置驗證：先確認相關 review event 可解析且能取得 lifecycle writer 的 accepted/status；任一前輪 event 為 marker_quarantined、half_written 或缺少該些值時，明示 input 不可判定並自判 review-invalid，不得把它當空 carry set 或以 review report 的 blocking 欄位替代 accepted。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5264306244 · 2026-08-12T08:30:54Z

## 派審：#38 `WF-DISPATCH-PRECHECK1` R3

⚠️ 審核對象 **`ruan6047/ai-workflow#38`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1
分支：claude/WF-DISPATCH-PRECHECK1　　被審 SHA：1b4c1f196202b210eee2a8ab47f88ae896f894ba
基線：6e6e8abd650c76fa6a2173f5dff35f99038ca1e0（PM 已重算並驗為祖先）　　iteration：2
寫入集：templates/review-prompt.md 單檔
```

> **本則為權威。** `origin/main` 現為 `02b5d9a`。**PM 已實測 merge(origin/main, 本分支) → 658 passed 全綠。**

### 一、複驗 R2-001：執行者沒照你的 disposition 字面寫，並說明了為什麼

你要的是兩態（可判定 ／ 缺欄即 `review-invalid`）。它查了 merged main 確認 **`accepted` 的 writer 根本不存在**——`validate_accepted_overrides` 與 `mark-not-accepted` 都不在 main，該通道還在 #9 的**未合併**分支上。所以**今天每一則 review event 都缺那兩個欄位**。

一刀切會讓 #9 合併前的每一輪 iteration ≥ 1 查核全部失效，**包括本卡自己的下一輪**。它的原話：「**那不是 fail-closed，是 deadlock**」，並指 `review-escalation.md` §2／§4 明文禁止互鎖的閘門。

改為**三態**：

| 態 | 條件 | 處置 |
|---|---|---|
| 可判定 | events 可解析且 `accepted`／`status` 可取得 | carry set = `accepted` ∧ `blocking` ∧ `status: open`，逐列回報 |
| 不可判定 | event 在**已宣告的 `contract-baseline` cutover 之後**卻是 `marker_quarantined`／`half_written`／缺欄 | 宣告 input 不可判定並自判 `review-invalid`，**永不當空 carry set** |
| legacy | event 早於 cutover，或從未發過 `contract-baseline` | 依 §4／§5 維持原貌、**不因此判 `review-invalid`**，但須明示走 legacy、列出前輪 findings 並標記其 `accepted` 為 writer-unmarked、escalation 帳不可導出 |

**請攻擊**：(a) 第三態是不是為了繞過 #9 未落地而存在的？它自陳「**`state 3` 目前是普遍狀態**這句話只在 `accepted` 的 writer 未合併期間為真，**而 #9 落地後沒有東西會重新檢查它**」——那是它自己造的過期隱患。(b) 走既有的 `contract-baseline` 機制而非發明新語意軸（§4 line 97 對此有具名警告），這個選擇對嗎？

### 二、硬禁令已逐字寫入

**不得以 report 的 `blocking` 代替 `accepted`**，理由同附：`blocking` 是 reviewer 自填、`accepted` 是 writer 標記，替代等於**讓被判定方決定自己的帳**。state 3 列出前輪 findings 是**揭露不是替代**——可供人讀延續，**不得進 escalation 計數**。

### 三、偵測是機械的，處置是約定——它把兩者分開了

偵測：`wfcli doctor --review-channel`（唯讀），執行者所在 `doctor.py` 的 `audit_review_channel`，`marker_quarantined`／`half_written` 兩個判定皆由它產出。**這是查核者跑得動的指令，不是散文。**

處置（三態的分流）：**約定，無機械執行者。**

**請判斷這個分割是否誠實**，以及偵測那一半是否真的涵蓋三態所需的全部輸入。

### 四、它自己驗證而非採信 PM 的三項

- R1 event `5262254982` line 30 帶 `blocking=true` 但無 `accepted`／`status`；line 37 逐字說那些由 lifecycle writer 另行標記且在該指令寫入範圍外。
- `half_written` **自行重現**：`doctor` 回報「裁決留言與 Log 索引都在，但 Project 交付狀態為 🚧進行中，與裁決結論應有的 ↩退回 不符」。**它未接受 PM「那只是狀態往前走」的淡化**——PM 當時確實試圖淡化，它拒絕了。
- merged main 無 `contract-baseline` cutover 動詞，故今天全部歷史都是 state 3。

### 五、已知殘留

`half_written` 的修復與 lifecycle 寫入交易性**不在本卡寫入集**，你上一輪已列為 scope_outside。執行者指名未動。

自陳四條無機械執行者：三態處置全文、`blocking`≠`accepted` 禁令（沒有東西阻止查核者靜默用 `blocking`，條文只讓替代**看起來明顯是錯的**）、state 3「須明示宣告 legacy」無 writer 檢查、以及上述那條過期隱患。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5264416000 · 2026-08-12T08:41:33Z

<!-- wf-review-receipt:v1
card_id: WF-DISPATCH-PRECHECK1
source_sha: 1b4c1f196202b210eee2a8ab47f88ae896f894ba
report_sha256: e58ef318c5b487363054247e9ea0c610059e25dcd55d637a568a2d84a9628077
-->
取材規則：起點為本規則之後的下一個「報告全文起點」行的下一行；終點為本規則之後的下一個「報告全文終點」行之前。以 UTF-8、LF、無 strip 取其間報告全文，包含報告末尾 LF；排除本收據 HTML 註解、取材規則行與兩個 delimiter 行。
報告全文起點
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1 rev-parse HEAD; git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1 merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD"
    observed: "HEAD 與被審 SHA 相同；工作區乾淨；基線祖先檢查 exit 0。"
  - command: "git archive 1b4c1f196202b210eee2a8ab47f88ae896f894ba | tar -x -C /tmp/wf38-review.Hd2aRX; cd /tmp/wf38-review.Hd2aRX/cli; uv run pytest -q"
    observed: "437 passed。"
  - command: "cd cli; uv run wfcli doctor .. --registry none --review-channel --repo ruan6047/ai-workflow --issue-number 38 --card-id WF-DISPATCH-PRECHECK1 --owner ruan6047 --project 4 --source-sha 88f07b95e434a034a14c18160d60957816f4135d --json"
    observed: "前輪 R2 source 為 half_written；輸出未提供 accepted、status 或 contract-baseline 判定。"
  - command: "gh issue view 38 --repo ruan6047/ai-workflow --json body -q .body | rg -n contract-baseline"
    observed: "卡的權威 Log 沒有 contract-baseline event。"
prior_accepted_blocking_findings:
  - finding_id: "WF-DISPATCH-PRECHECK1-R2-001"
    status: "writer-unmarked legacy；沒有可推導的 accepted 或閉環狀態。"
    evidence: "R2 review event 明示 accepted 與 status 由 lifecycle writer 另行標記，但該 event 與 Log 均未帶此兩欄；本輪派審要求在未有 cutover 時走 legacy。"
findings:
  - finding_id: "WF-DISPATCH-PRECHECK1-R3-001"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: carry-set-self-verifiability-gap
    evidence: "review-prompt.md 的 legacy 態以未發 contract-baseline 為充分理由，不把 half_written 與 writer-unmarked 前輪輸入判 review-invalid。Issue 38 的 R2 已由 doctor 重現為 half_written，且權威 Log 沒有 cutover；因此現行條文要求查核者把已知不可完整對帳的輸入當 legacy，而非自行拒收。這保留了核心痛點：Coordinator 未補發 cutover 時，查核者不能可靠決定閉環義務。"
    disposition: "調整 legacy 邊界：缺 cutover 不得覆蓋已被機械偵測為 half_written、marker quarantined 或缺 writer 欄位的前輪事件；或提供可由查核者執行的明確且可驗證的遷移條件。不可把未來 writer 合併當作已完成的解除。"
  - finding_id: "WF-DISPATCH-PRECHECK1-R3-002"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: carry-set-self-verifiability-gap
    evidence: "條文將 wfcli doctor 的 marker_quarantined 與 half_written 輸出稱為可自行跑的完整檢測，但 audit_review_channel 的資料模型只輸出 review-channel 狀態，未輸出每筆 finding 的 accepted、status，也未枚舉或驗證 contract-baseline。三態分類仍需這三類輸入，故偵測與處置的分割不完整，不能支撐自我可驗證的結論。"
    disposition: "把偵測能力如實限縮為 review-channel 健全性，並在範本列出 accepted、status 與 cutover 的可讀權威載體和逐一驗證方式；若現況沒有該載體，明示為不可判定而非宣稱 doctor 已涵蓋。"
報告全文終點

## Comment 5264603680 · 2026-08-12T09:00:14Z

<!-- wf-review-event:v1 card_id=WF-DISPATCH-PRECHECK1 source_sha=1b4c1f196202b210eee2a8ab47f88ae896f894ba attempt_id=WF-DISPATCH-PRECHECK1-e0-1b4c1f196202b210eee2a8ab47f88ae896f894ba -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-DISPATCH-PRECHECK1`　attempt_id：`WF-DISPATCH-PRECHECK1-e0-1b4c1f196202b210eee2a8ab47f88ae896f894ba`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5264416000 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=e58ef318… 一次相符。本批六份收據皆採內容錨定或分隔行，各自規則不同，PM 逐份照其規則計算、無需任何格式調整）　escalation_epoch：0
- source_sha：`1b4c1f196202b210eee2a8ab47f88ae896f894ba`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T17:00:12+08:00

### self_run（查核者實跑）

- `git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1 rev-parse HEAD; git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1 merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD`
  - HEAD 與被審 SHA 相同；工作區乾淨；基線祖先檢查 exit 0。
- `git archive 1b4c1f196202b210eee2a8ab47f88ae896f894ba | tar -x -C /tmp/wf38-review.Hd2aRX; cd /tmp/wf38-review.Hd2aRX/cli; uv run pytest -q`
  - 437 passed。
- `cd cli; uv run wfcli doctor .. --registry none --review-channel --repo ruan6047/ai-workflow --issue-number 38 --card-id WF-DISPATCH-PRECHECK1 --owner ruan6047 --project 4 --source-sha 88f07b95e434a034a14c18160d60957816f4135d --json`
  - 前輪 R2 source 為 half_written；輸出未提供 accepted、status 或 contract-baseline 判定。
- `gh issue view 38 --repo ruan6047/ai-workflow --json body -q .body | rg -n contract-baseline`
  - 卡的權威 Log 沒有 contract-baseline event。

### findings（2，其中 blocking 2）

- **WF-DISPATCH-PRECHECK1-R3-001**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`carry-set-self-verifiability-gap`
  - evidence：review-prompt.md 的 legacy 態以未發 contract-baseline 為充分理由，不把 half_written 與 writer-unmarked 前輪輸入判 review-invalid。Issue 38 的 R2 已由 doctor 重現為 half_written，且權威 Log 沒有 cutover；因此現行條文要求查核者把已知不可完整對帳的輸入當 legacy，而非自行拒收。這保留了核心痛點：Coordinator 未補發 cutover 時，查核者不能可靠決定閉環義務。
  - disposition：調整 legacy 邊界：缺 cutover 不得覆蓋已被機械偵測為 half_written、marker quarantined 或缺 writer 欄位的前輪事件；或提供可由查核者執行的明確且可驗證的遷移條件。不可把未來 writer 合併當作已完成的解除。
- **WF-DISPATCH-PRECHECK1-R3-002**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`carry-set-self-verifiability-gap`
  - evidence：條文將 wfcli doctor 的 marker_quarantined 與 half_written 輸出稱為可自行跑的完整檢測，但 audit_review_channel 的資料模型只輸出 review-channel 狀態，未輸出每筆 finding 的 accepted、status，也未枚舉或驗證 contract-baseline。三態分類仍需這三類輸入，故偵測與處置的分割不完整，不能支撐自我可驗證的結論。
  - disposition：把偵測能力如實限縮為 review-channel 健全性，並在範本列出 accepted、status 與 cutover 的可讀權威載體和逐一驗證方式；若現況沒有該載體，明示為不可判定而非宣稱 doctor 已涵蓋。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5265390971 · 2026-08-12T10:17:48Z

<!-- wf-review-receipt:v1
card_id: WF-DISPATCH-PRECHECK1
source_sha: 1b4c1f196202b210eee2a8ab47f88ae896f894ba
report_sha256: fbd5d6e40ba669120093e0a4e03a13bc255abbb45a4d6177a21bb051fcf40f39
-->
取材規則：起點為本規則之後的下一個「報告全文起點」行的下一行；終點為本規則之後的下一個「報告全文終點」行之前。以 UTF-8、LF、無 strip 取其間報告全文，包含報告末尾 LF；排除本收據 HTML 註解、取材規則行與兩個 delimiter 行。
報告全文起點
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1 rev-parse HEAD; git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1 status --porcelain; git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1 merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD"
    observed: "worktree exists and is clean, but HEAD is 85a5c7b00bb0721b5f3899ce526bf569ec826ea9 rather than the authoritative dispatched source SHA 1b4c1f196202b210eee2a8ab47f88ae896f894ba; baseline ancestor check exits 0 for the different HEAD."
  - command: "git -C /Users/ruanruan/Dev/ai-workflow cat-file -e 1b4c1f196202b210eee2a8ab47f88ae896f894ba^{commit}; git -C /Users/ruanruan/Dev/ai-workflow diff --name-only 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 1b4c1f196202b210eee2a8ab47f88ae896f894ba"
    observed: "the dispatched commit exists, and its diff writes templates/review-prompt.md, but it is not the artifact at the dispatched worktree HEAD."
prior_accepted_blocking_findings:
  - finding_id: "WF-DISPATCH-PRECHECK1-R3-001"
    status: "writer-unmarked legacy; no accepted status is derivable."
    evidence: "the Issue review record says accepted and status are lifecycle-writer fields outside the reviewer command; no writer mark is available in the prior record."
  - finding_id: "WF-DISPATCH-PRECHECK1-R3-002"
    status: "writer-unmarked legacy; no accepted status is derivable."
    evidence: "the Issue review record says accepted and status are lifecycle-writer fields outside the reviewer command; no writer mark is available in the prior record."
findings:
  - finding_id: "WF-DISPATCH-PRECHECK1-R3-003"
    severity: major
    blocking: true
    finding_class: coordination
    attribution: coordinator
    root_cause_id: handoff-artifact-identity-mismatch
    evidence: "the authoritative dispatch comment names source_sha 1b4c1f196202b210eee2a8ab47f88ae896f894ba, while git rev-parse HEAD in its named worktree returns 85a5c7b00bb0721b5f3899ce526bf569ec826ea9. Both commits exist, so this is an identity mismatch rather than an unresolved value."
    disposition: "repair the handoff so the named worktree HEAD and source_sha are identical, then request a fresh review; do not treat checks against either different artifact as this review."
報告全文終點

## Comment 5265662553 · 2026-08-12T10:45:12Z

## ⚠️ PM 更正：本卡上一則派審詞的 SHA 是舊的，本輪裁決不予轉錄

**這是 Coordinator 的錯誤，重複了三次（本卡、#38、#42）。**

執行者交回修法後，PM 執行了 `wfcli handoff`（設定狀態面 SHA），**但沒有補發新的派審詞**。Issue 上最後一則「## 派審：」仍載著前一輪的 SHA。

實測：

```
本卡最後一則派審詞　被審 SHA：1b4c1f196202b210eee2a8ab47f88ae896f894ba
實際 handoff／worktree HEAD：85a5c7b00bb0721b5f3899ce526bf569ec826ea9
```

### 而 PM 同時指定了錯的來源當權威

PM 給協調者的提示詞表格列的是 **`85a5c7b00bb0721b5f3899ce526bf569ec826ea9`（正確）**，但同一份提示詞逐字寫著「**權威在 Issue 上，取最後一則派審詞**」。

**兩個來源不一致，而 PM 指定了錯的那個。**

⚠️ **這正是 `WF-DISPATCH-PRECHECK1`（#38）那張卡的主題**——它的 §1「權威來源只有一個」就是為了治這個病，而 PM 在派它去審的過程中犯了同一個病。

`attribution: coordinator`。

### 查核者抓到了，而且處置正確

它比對 worktree HEAD 與派審詞所載 SHA，發現不符，並判定：

> **兩個 commit 都存在，所以這是身分不符而非未解決的值。**

其 disposition 逐字：「修好 handoff 使具名 worktree 的 HEAD 與 `source_sha` 一致，然後請求一次新的查核；**不得把對任一不同產物的檢查當成本次查核**。」

**它拒絕以任一產物當作本次查核，是對的。** 若它逕自改用 worktree HEAD，就會在 PM 指定的權威來源之外自行選擇——那正是本卡 §1 要禁止的形態。

### R3-003 照收

`WF-DISPATCH-PRECHECK1-R3-003`（major，blocking，`coordination`，**`attribution: coordinator`**，`root_cause_id: handoff-artifact-identity-mismatch`）**PM 完全接受**，並記入本則作為留痕。

**本輪裁決不寫入 review event**，因為它本身就是「無法對指定產物完成查核」的回報，而非對 `85a5c7b` 的評價。本輪**不計為可計數 attempt**。

### 這張卡的處境有一層額外的諷刺，值得記

本卡的交付物正在建立「**權威來源只有一個**」與「**值解不開時先回對權威來源，不要直接停手**」兩條條文。而本輪：

- PM 製造了兩個來源不一致 → 本卡條文要防的事
- 查核者回對了權威來源、發現值仍解不開、**如實回報而非自行選擇** → 本卡條文要的行為

**條文尚未上線，行為已經發生了。** 這對下一輪的 `core_pain_resolved` 判定是一個真實的資料點。

### 下一步

PM 將補發對齊 `85a5c7b` 的派審詞。**執行者無須任何動作。**


## Comment 5265680751 · 2026-08-12T10:47:07Z

## 派審：#38 `WF-DISPATCH-PRECHECK1` R4（補發，對齊實際交付 SHA）

⚠️ 審核對象 **`ruan6047/ai-workflow#38`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1
分支：claude/WF-DISPATCH-PRECHECK1　　被審 SHA：85a5c7b00bb0721b5f3899ce526bf569ec826ea9
基線：6e6e8abd650c76fa6a2173f5dff35f99038ca1e0（PM 已重算並驗為祖先）　　iteration：3
寫入集：templates/review-prompt.md 單檔
```

> ⚠️ **權威來源的更正（PM 上一輪犯的錯，而上一輪的查核者抓到了）**：上一輪 PM 做了 handoff 卻沒補發派審詞，導致派審詞載 `1b4c1f1` 而 worktree HEAD 是 `85a5c7b`。**該輪查核者比對後判定「兩個 commit 都存在，所以這是身分不符而非未解決的值」，並拒絕以任一產物當作查核——那是正確的**。其 `R3-003`（`attribution: coordinator`，`handoff-artifact-identity-mismatch`）PM 完全接受，留痕見 `issuecomment-5265662553`。**該輪不計為可計數 attempt。**
>
> **本則派審詞與 Issue Log 最後一筆 `handoff` 事件的 SHA 一致。若你發現不符，以 handoff 事件為準並回報。**

`origin/main` 現為 `e8a638c`。**PM 已實測 merge(origin/main, 本分支) → replay 65/65、pytest 658 全綠。**

### ⚠️ 一件與本卡主題直接相關的事，請納入 `core_pain_resolved` 的判斷

本卡的交付物正在建立兩條條文：「**權威來源只有一個**」與「**值解不開時先回對權威來源，不要直接停手**」。

而上一輪真實發生的是：

- **PM 製造了兩個來源不一致** → 本卡條文要防的事
- **查核者回對了權威來源、發現值仍解不開、如實回報而非自行選擇** → 本卡條文要的行為

**條文尚未上線，行為已經發生了。** 這是一個真實資料點，不是假想。**請判斷它對本卡的痛點是否構成證據——兩個方向都正當**：可以說「條文只是把已在發生的好行為寫下來，價值有限」，也可以說「條文把偶然的好行為變成可預期的」。

### 一、複驗 R3-001 與 R3-002：執行者移除了分類軸

你上一輪判 legacy 態的邊界太寬、以及偵測能力被高估。執行者查了兩半並**移除 `contract-baseline` 這個分類軸**：

`doctor.py` 提及 `contract-baseline` **0 次**、提及 `accepted` **0 次**；`audit_review_channel` 只回一個 `status`，枚舉為五個值。**PM 已獨立複驗這三項全部屬實**，並確認 main 的 `cli/src` 找不到 `mark-not-accepted`（產生器確實不存在）。

結論：以 cutover 分類等於「拿查核者查不到的東西決定查核者的義務」。改成兩個**從查核者座位上查得到**的軸——(1) 偵測到損壞；(2) 產生器系統性不存在。

**R3-001 的修法**：state 3 要求**三個條件同時成立**，第三個是**正面舉證責任**——「你出示得了產生它們的 writer 不在被審樹裡」。逐字寫入：**「(iii) 舉不出來就落第 2 態」——「沒證明產生器不存在」不等於「產生器不存在」**。state 2 帶有你要求的那句：**缺 cutover 不是本態的赦免事由**。

**遷移條件現在可檢查，不是對未來合併的承諾**：state 3 在 writer 出現於被審樹的當下**自動失效**，不需任何人宣告。

行為對照以本卡自己的 R2 實跑：舊條文 → legacy → 不判 `review-invalid`；新條文 → 偵測到損壞 → state 2 → **`review-invalid`**。

**R3-002 的修法**：偵測能力如實限縮，範本以三列表格分離載體並明寫 `doctor`「能證明的只有這條通道健不健全，**證明不了 carry set 算不算得出來**」。未涵蓋的兩欄各給權威載體與指令；**`contract-baseline` 今天無可讀載體、無法判定**，以表格中的一列如實陳述。

**請攻擊**：(a) 三個條件同時成立的 state 3，實務上還進得去嗎，還是變成了空集合？(b) 「產生器自動失效」的機制真的不需要任何人宣告嗎？

### 二、執行者新造並主動上記錄的一個缺口

**產生器缺席探針把搜尋字串（`mark-not-accepted`）寫死為範例。** 若 #9 以不同名稱落地該 writer，該範例會過期而查核者可能**誤判系統性缺席**。條款第二肢（Issue 上從未有事件帶過該欄）是佐證檢查，**但沒有東西強制同時用兩肢**——故該探針是**帶已知失效模式的約定**，不是可靠測試。

**請判斷這個自陳是否足夠，還是該在本輪就修掉。**

### 三、(e) 作用域陳述

檔末寫入：**只有通道健全性有機械執行者**（`doctor.audit_review_channel`，且僅限那五個枚舉值）；讀 `accepted`／`status`、證明產生器缺席、三個處置**全部是約定**——「`gh api` 與 `git grep` 是你手上的工具，**不是會擋你的閘門**」。

`blocking`≠`accepted` 禁令不變，state 3 的列出仍標為**揭露不是替代**。

### 四、驗證

改動前基線取自 `1b4c1f1` 的乾淨 `git archive` 得 cli 437 passed、replay 65/65；改動後 in-tree 同為 437、65/65 exit 0。節標題仍 `1,2,3,3.1,4,5,6` 未改號。marker 0。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5265803015 · 2026-08-12T10:59:55Z

## 派審詞的一處數字更新（不改被審 SHA、不改基線）

`DEV-CLI-VERB-REGISTRY1`（#53）已合併，`origin/main` 由 `e8a638c` 前進至 `e1b33d8`。上一則派審詞（`issuecomment-5265680751`）裡的兩個數字因此過期，更新如下：

- `origin/main` 現為 **`e1b33d8`**（原文寫 `e8a638c`）
- merge(origin/main, 本分支) 實測改為 **replay 65/65、pytest 701 passed**（原文寫 658，差額全部來自 #53 新增的 43 個註冊表測試）

**被審 SHA 仍是 `85a5c7b00bb0721b5f3899ce526bf569ec826ea9`，基線 `6e6e8ab` 不變**——基線是 fork point，不隨 main 前進而移動。本分支寫入集為 `templates/review-prompt.md` 單檔，與 #53 的三個檔零重疊，`git merge-tree` 對新 main **無衝突**。

上一則派審詞的其餘內容全部有效，請照它進行。


## Comment 5265943084 · 2026-08-12T11:14:44Z

<!-- wf-review-receipt:v1
card_id: WF-DISPATCH-PRECHECK1
source_sha: 85a5c7b00bb0721b5f3899ce526bf569ec826ea9
report_sha256: a732d73f9458f22463c8a1b68924564c389be31d6054fd2d92b5506531dbe965
-->
取材規則：起點為本規則之後的下一個「報告全文起點」delimiter 行之後第一個字元；終點為其後下一個「報告全文終點」delimiter 行之前最後一個字元。UTF-8、LF、無 strip；排除本收據 HTML 註解、本規則行，以及兩個 delimiter 行本身；被雜湊內容保留報告原有末尾 LF。
報告全文起點
# WF-DISPATCH-PRECHECK1 R4 獨立查核

## 前輪 accepted blocking finding 閉環

- `WF-DISPATCH-PRECHECK1-R3-001`：無法判定閉環。前輪 source `1b4c1f196202b210eee2a8ab47f88ae896f894ba` 的 `doctor --review-channel` 回報 `half_written`；依被審 `templates/review-prompt.md` §3.1 第 2 態，必須自判 `review-invalid`，不可把缺失的 writer 欄位當空集合。
- `WF-DISPATCH-PRECHECK1-R3-002`：無法判定閉環。相同前輪 review event 未有可讀的 `accepted`／`status`，且通道狀態為 `half_written`；不能確認它是否屬 accepted blocking carry set，因此不對 executor 的修法作實質裁決。

本次無法完成實質查核。權威 handoff SHA、目標 worktree 與基線均有效，但 R3 review event 的權威通道已被 `doctor` 機械判為 `half_written`。被審版本正確要求此狀況停止而非把 carry set 當空集合；故本報告依該契約標記 `review-invalid`，不將 R3-001／R3-002 視作已閉環，也不對其內容作 APPROVE。

core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "gh issue view 38 --repo ruan6047/ai-workflow --json body -q .body | grep 'handoff by wf-cli' | tail -1"
    observed: "最後 handoff SHA=85a5c7b00bb0721b5f3899ce526bf569ec826ea9，與最後派審詞相同"
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1 rev-parse HEAD; git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1 status --porcelain; git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1 merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD"
    observed: "HEAD=85a5c7b00bb0721b5f3899ce526bf569ec826ea9；工作區乾淨；祖先檢查 exit 0"
  - command: "git archive 85a5c7b00bb0721b5f3899ce526bf569ec826ea9 | tar -x -C /tmp/wf38-r4.18mVbx; cd /tmp/wf38-r4.18mVbx/cli && uv run pytest -q"
    observed: "437 passed"
  - command: "cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1/cli && uv run wfcli doctor .. --registry none --review-channel --repo ruan6047/ai-workflow --issue-number 38 --card-id WF-DISPATCH-PRECHECK1 --owner ruan6047 --project 4 --source-sha 1b4c1f196202b210eee2a8ab47f88ae896f894ba --json"
    observed: "review_channel.status=half_written；裁決留言與 Log 索引存在，但 Project 交付狀態實際為待查核而非預期退回"
  - command: "git -C /Users/ruanruan/Dev/ai-workflow grep -n -E 'mark-not-accepted|accepted|contract-baseline' 85a5c7b00bb0721b5f3899ce526bf569ec826ea9 -- cli/src"
    observed: "沒有 mark-not-accepted 或 contract-baseline 命中；accepted 僅為既有 review writer 的保留鍵，不能補足 R3 event 的 writer 標記"
findings:
  - finding_id: "WF-DISPATCH-PRECHECK1-R4-001"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: coordinator
    root_cause_id: "carry-set-self-verifiability-gap"
    evidence: "R3 review event comment 5264603680 的 source_sha 為 1b4c1f196202b210eee2a8ab47f88ae896f894ba；本次 doctor 對該 SHA 回報 half_written，並指出 Issue Log 有裁決但 Project 狀態仍為待查核。被審 review-prompt.md:55 規定偵測到 half_written 必須 review-invalid，不得當空 carry set。"
    disposition: "由唯一 lifecycle writer 修復 R3 attempt 的權威通道一致性與 accepted/status 留痕，完成新的有效 handoff 後，再請求一次查核；本輪不得以 R3-001 或 R3-002 已處置作實質驗收。"

## 驗收判定

- R3-001 與 R3-002 的文字修法尚未進行實質驗收，原因是其前輪 accepted blocking 身分與閉環輸入不可由權威通道可靠推導。
- 被審版本對這個失敗型態的 fail-closed 指示可重現，未把 `half_written` 誤分類為系統性缺席的受限續行。
- diff 僅改動 `templates/review-prompt.md`，且拋棄式 archive 的 CLI 測試 437 passed。

## 範圍外發現

- `doctor` 同次列出多個既有 worktree 註冊對帳警示；與本卡 R3 閉環無關，未納入 finding 集合。
報告全文終點


## Comment 5266102788 · 2026-08-12T11:26:49Z

## PM 對 R4 的處置：裁決不轉錄，但查核者的停手是對的——錯的是它被要求去讀的那個訊號

R4 的查核者依本卡交付的 §3.1 第 2 態判 `review-invalid` 並停手。**那個判斷完全正確**：契約要求偵測到 `half_written` 時停止而非把 carry set 當空集合，它照做了。

但它的 `R4-001` 有一個前提是錯的，而該前提決定了 `disposition`：

> disposition：**由唯一 lifecycle writer 修復 R3 attempt 的權威通道一致性與 accepted/status 留痕**，完成新的有效 handoff 後，再請求一次查核

**沒有東西需要修復。那次寫入從頭到尾是成功的。**

### PM 的獨立重現

我先照它的指令重跑，得到同樣結果：

```
status=half_written
detail: 半寫入：裁決留言與 Log 索引都在，但 Project 交付狀態為 '🔍待查核'，
        與裁決結論應有的 '↩退回' 不符。
expected_delivery_status: ↩退回     actual_delivery_status: 🔍待查核
```

然後我看本卡 Log 的實際時序：

```
17:00:12  review  → REQUEST_CHANGES（↩退回）      ← 這次寫入成功了，狀態確實變成 ↩退回
17:08:25  handoff → implementation（iteration 3）  ← 交回執行者
17:26:36  handoff → review（SHA 85a5c7b）          ← 狀態合法地前進為 🔍待查核
```

**`🔍待查核` 不是漏寫的殘骸，是後續兩次合法 handoff 的結果。**

`doctor.audit_review_channel` 拿一個**歷史 attempt** 的裁決結論，去比對**當下**的交付狀態，而它沒有任何「這則事件已被後續事件取代」的概念。`doctor.py:496-497` 的註解自己承認了這件事：「**在不引入時間語意的前提下**，無法宣稱 v1 較新而應勝出」。

### 判別性實驗

同一支指令、兩個輸入，唯一差別是那則裁決有沒有被後續事件取代：

| 查詢對象 | 該卡當下狀態 | `doctor` 回報 |
|---|---|---|
| #38 R2 attempt `88f07b9`（已被取代） | 🔍待查核 | **`half_written`** |
| #39 R2 attempt `b039c0b`（尚未取代） | ↩退回 | `recorded` |

**`half_written` 是「卡往前走了」產生的，不是「寫入壞了」產生的。**

### 這對本卡意味著什麼

本卡交付的 §3.1 把 `half_written` 定為**硬停**。與上述行為相乘，結論是：

**任何走過一輪以上查核的卡，只要查核者照本卡的條文去查前一輪的通道狀態，就必然得到 `half_written`，於是必然停手。** 本卡自己就是第一個受害者——而且它是被**它自己交付的條文**擋住的。

這不是理論推導，是本輪實際發生的事。

### PM 的處置

1. **本輪不轉錄為 review event**，`review-invalid` 不計為可計數 attempt。查核者無過失。
2. `R4-001` 的**現象**成立、**歸因與處置**不成立：沒有 lifecycle writer 的寫入需要修復。真正的缺陷在 `doctor.audit_review_channel` 無法區分「寫入失敗」與「事件被取代」，而本卡的條文把這個不可區分的狀態定為硬停。
3. **本卡退回實作**，處置方向由執行者裁定，PM 不代答。至少三條路擺著：讓契約區分兩者（需要 `doctor` 側有時間語意，可能逸出寫入集）、把 `half_written` 的硬停改為「查核者須指出它是取代還是壞寫」、或明文限定通道檢查只對**當前** attempt 有效。**若正解逸出單檔寫入集，指名而不代修。**
4. `R3-001`／`R3-002` 的閉環狀態**維持未判定**，不因本則更正而視為已閉環。

### 一件 PM 要一併認的事

派審詞裡我寫了「偵測範圍限縮至 `doctor.audit_review_channel` 的五個枚舉值」，並把它當成**已收斂**的一項。我沒有去查那五個值在真實資料上分別會在什麼情況下出現——**如果查了，這一輪不會被浪費。**


## Comment 5305440359 · 2026-08-16T03:02:17Z

## 本卡的核心痛點於 2026-08-15 在 PM 身上重演一次（PM 自報）

本卡記的是 2026-08-11：

> 五份派審詞的基線 SHA **全部抄成當下的 `origin/main`**（那是 PM 自己一小時前端到端實跑產生的 merge、不是任何卡的祖先）

**2026-08-15，同一個形狀又發生一次，換了一種抄法：**

PM 把 `cpbl-analytics #141` **未 merge 分支的中途測試數 `1798 passed / 12 skipped`** 當成 `main` 的基準，寫進 `#132` 與 `#142` 兩份派工單。`main` 實測為 **`1709 passed / 13 skipped`**。

同一份派工單裡 PM 還寫了「`refresh-cpbl-prod.sh` 與 `backup-prod-db.sh` 的 argv 守衛都是本週剛加的，可參考形狀」——**那兩個守衛也只在該分支上，`main` 沒有**。

**同一個錯在一份派工單裡犯了兩次。** 兩位執行者各自獨立抓到並在交付報告中更正。

### 這對本卡是三件事

**一、它證明本卡的痛點不是歷史事件。** 08-11 五份、08-15 兩份，中間隔四天，而本卡一直在 Backlog。

**二、它擴大了本卡痛點的形狀。** 08-11 是「抄成 `origin/main`」，08-15 是「抄成某個分支的中途值」。共同點不是抄錯哪一個值，是**引用了一個沒有在共享基線上量過的數字**。本卡驗收條 1 的正解（`git_ops.is_ancestor` 已存在、只差一個 `merge_base()`，把值算出來）**對兩種形狀都成立**——這強化了那個裁定而非動搖它。

**三、⚠️ PM 於 2026-08-16 誤開了一張重複卡。** `#90 WF-EVIDENCE-PROVENANCE1` 的第 ① 條就是本卡驗收條 1 的等價物，PM 開卡前沒有讀本卡。`#90` 已關閉（`not planned`），其 ① 歸位本卡、② 歸位 `#11` 的 (f)。

⚠️ 而 PM 犯的正是本卡最後一條驗收條件寫的那個錯的變體：

> **卡號指向須逐一以被指卡的卡面驗收原文核對，不得只核卡號存在**——本卡自身的驗收就犯過這個錯。

PM 核的是 canonical 的字面命中數，**沒有核卡的原文**。

### 本則不改變本卡任何欄位

僅追加實證。本卡的四條驗收條件與射程維持原狀。


## Comment 5305467959 · 2026-08-16T03:11:03Z

## 需求方裁定：前瞻射程由 `#66` 承接，本卡**維持 OPEN** 至三輪 findings 結清（2026-08-16）

### 裁定

本卡的**前瞻射程**（要建什麼）移交 `#66 WF-DISPATCH-FROM-HANDOFF1`，已於該卡 `amend` op `21c34aa1` 具名寫入。裁定全文見 `#66` 的 `issuecomment-5305463996`。

**但本卡不關閉。**

### 為什麼不關

**本卡在 iteration 5，有 3 輪 `REQUEST_CHANGES` 的 findings 未閉合**：

```
2026-08-12 12:23:56  REQUEST_CHANGES  GPT-5@Codex 子代理  收據 issuecomment-5262202954
2026-08-12 13:20:20  REQUEST_CHANGES  GPT-5@Codex 子代理  收據 issuecomment-5262590149
2026-08-12 17:00:12  REQUEST_CHANGES  GPT-5@Codex 子代理  收據 issuecomment-5264416000
```

其後於 2026-08-13 00:24 被批次降級（`0ea7abad`）拉回 Backlog。

**本卡不是一張沒開工的卡。** 直接關閉會讓那三輪的 findings 消失。

⚠️ PM 尚未讀那三輪的內容，**判不出它們是否隨射程移轉而失效**。在讀之前判「失效」就是本專案反覆在犯的那個錯——宣稱超過證據，也就是 `#11` 的 (a)–(f) 在管的事。

### 解除條件

那三輪的 findings **逐一列出，各自閉合或轉入 `#66`**。

**執行者：`#66` 的執行者**——它本來就得讀那三輪才知道要建什麼，已寫進 `#66` 的驗收條件。

### 移交的兩項，以及為什麼是兩項不是一項

| 本卡的 | 去向 | 註 |
|---|---|---|
| 驗收條 1：基線 SHA 的正解 | `#66` | 本卡自己就指向 `handoff_cmd.py`——「正解是把值算出來，`git_ops.is_ancestor` 已存在，只差一個 `merge_base()`」 |
| 驗收條 2 第 (1) 層：`review-prompt.md` 前輪閉環必填小節 | `#66`，**且已具名** | ⚠️ **同源產生不蘊含它**。`handoff` 產出骨架不會自動要求查核者逐項回報前輪 finding；若 `#66` 只做機械欄位同源，這一層會靜默消失 |

### 本卡痛點於 2026-08-15 重演一次

已另記於本卡（`issuecomment-5305440359`）：PM 把某未 merge 分支的中途測試數當成 `main` 基準寫進兩份派工單。**08-11 是抄成 `origin/main`，08-15 是抄成分支中途值——共同點不是抄錯哪個值，是引用了一個沒有在共享基線上量過的數字。**

這強化了本卡驗收條 1 的裁定（把值算出來）而非動搖它，該裁定已隨移交進入 `#66`。


## Comment 5460928058 · 2026-08-29T06:55:45Z

## 阻塞登記

**狀態**：⏸阻塞。**來源狀態：📥Backlog**（解除時回到此狀態）。

**阻塞原因**：需求方於 2026-08-29 決定，在階段狀態重整（8 階段 × 10 狀態、待審清單、CLI 射程收斂）定案並落地前，暫停所有 ai-workflow 流程卡，避免它們與重構討論互相干擾。

**可證偽的解除條件**：待審清單機制上線（label ＋ issue template ＋ 可見分組）。屆時本卡改列為清單參考項，或依當時前提是否仍成立重新排程。

**本次未做**：核心痛點、驗收條件、射程一律未動。`iteration` 未遞增。`階段` 欄未寫入。本登記僅改交付狀態與 owner。

**已知的射程重疊**（供解除時參考，非本次裁定）：#66／#38 的實質可能由「七份交接文件格式」承接；#128 可能由「待審清單收件條件三·查重留痕」＋`open --from-issue` 承接；#11 的證據紀律已部分寫入 PM 準則但痛點（靠人記得）未消失。⛔ 上述皆未經裁定，解除時須逐張重驗。

**裁定者**：需求方 ruan6047，2026-08-29 本 session 對話中指示「把目前所有 WF 卡片暫停，避免干擾目前重構討論」。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

