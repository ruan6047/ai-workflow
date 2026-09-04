# #129 WF-RELEASE-NO-CLEANUP-REFUSE1 release 明知會產生自己拒修的非法終態，卻只印警示就照做；唯一屏障是一行字
- state: closed  created: 2026-08-22T13:39:24Z  closed: 2026-08-24T08:07:01Z
- url: https://github.com/ruan6047/ai-workflow/issues/129
- comments: 7

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；改的是唯一寫入通道的終態路徑，收緊過頭會擋掉正當收尾、收緊不足等於沒改；且須先回答「不帶 --cleanup 的正當用途是什麼」才知道拒絕條件該長怎樣。）　查核：待指派（建議 主力型；查核者須自行構造出「該拒卻放行」與「該放行卻拒」兩個方向的實例，而非只讀 diff；此卡的風險在誤擋，靜態閱讀看不出來。）
- Initiative：—　spec 基線：WF-CLEANUP-GUARD1（#25，CLOSED）
- DB：db_scope=none
- 服務的原始目標：目標 1 防止低級事故：把「印警示後照做」改為「拒絕」，執行者從人的眼睛換成 CLI 自己。

## 簡介
<!-- card-brief:begin -->
把 handoff --next-stage release 帶 --repo-path 卻漏帶 --cleanup 的行為，從「印一行警示後照做」改成 rc=2 拒絕且狀態面一個字都不寫，避免卡落進 cleanup.classify_state 的 illegal_terminal_before_cleanup——該態守衛明文拒絕代修，只能人工刪 worktree 與分支再手動關 Issue。**適用時機**：release 被 CLI 擋下想知道為什麼；或要查 cpbl#166、cpbl#138 兩例人工收尾的成因、以及 --cleanup 預設不清理那個理由被推翻的依據時。⛔ 非射程：拒絕不外溢，requirement／research／planning／backlog／implementation／review 六種 next-stage 一律不受影響；不改 cleanup.py 的 classify_state 與 AUTHORITY_BY_PROOF。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：handoff --next-stage release 不帶 --cleanup 時，會在清理完成前寫入終態，落成 cleanup.classify_state 的 illegal_terminal_before_cleanup；該狀態守衛明文拒絕代修（實得 illegal_state：須人工判斷，守衛不代為修復），只能人工刪 worktree、本地分支、遠端分支再手動關 Issue。handoff_cmd.py 的 docstring 逐字承認這是刻意設計：「因此該路徑會印出警示，而不是靜靜維持原狀」⇒ 唯一屏障是一行印出來的字，依 ROADMAP §0 Check 2 那是靠人讀、屬目標 3 的執行者。實害已發生：2026-08-22 PM 把首次 release 的 rc=5 阻擋以 tail -1 截掉、誤以為成功而改用無 --cleanup 重跑，cpbl#166 因此落入該非法態並以人工收尾。⇒ 判斷資訊本來就在手上：classify_state 是全函數、32 種組合窮舉測試，illegal_terminal_before_cleanup 即 not cleanup_done and effect_started。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/handoff_cmd.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] handoff --next-stage release 帶 --repo-path 卻沒帶 --cleanup 時拒絕，rc=2，且狀態面一個字都不寫（owner／交付狀態／最後交接／iteration 皆未變、Issue 未關、worktree 與本地遠端分支皆在）
- [ ] ⛔ 拒絕不外溢：其他 next-stage（requirement／research／planning／backlog／implementation／review）帶 --repo-path 且無 --cleanup 一律不受影響。理由是本卡自身的 research／planning／backlog 三次 handoff 都是該組合
- [ ] 沒給 --repo-path 的 release 不拒絕、行為不變（警示照印、狀態面照寫），但「收尾清理未執行（worktree、本地分支、遠端分支皆未處理）」須寫進卡上 handoff Log 行——⛔ 不得只印 stderr
- [ ] --cleanup 的 help 與模組說明須與新行為一致：⛔ 不得保留「預設不清理——刪除不可逆，預設值取代價可回復的那一邊」這個已被推翻的理由。推翻依據為 cleanup.AUTHORITY_BY_PROOF 僅在 ancestor 授權刪分支（content_absorbed 只授權 remove_worktree、diverged 與 unobservable 皆為空集合），⇒ 不可逆的那一半已被證明分級中和
- [ ] 拒絕與留痕兩處的常數須自帶推翻理由與兩例實害（cpbl#138 於 2026-08-15、cpbl#166 於 2026-08-22），⛔ 且須註明因該路徑先前不寫卡上留痕，兩例是下限而非總數

## 驗證

- [ ] 三個變異檢驗各須有對應測試轉紅：移除拒絕分支、留痕後綴改回不傳、拒絕條件去掉 next_stage 限制。⚠️ 改 source 後須在 pytest 自己的 process 內印 module.__file__ 確認載入的是變異版——本 session 已有三次無效突變測試
- [ ] 照本 repo CI 的三步驗，⛔ 不套用 cpbl 慣例（本 repo CI 不跑 ruff）：cd cli && uv lock --check；cd cli && uv run --frozen pytest -q；uv run --no-project --python 3.12 scripts/replay_escalation_rules.py（⚠️ 該步在 repo 根，不在 cli/）
- [ ] ⚠️ rc 一律以重導向或 PIPESTATUS 取自受測對象本身，⛔ 不得取管線尾端——PM 本 session 已四次把 tail 的 rc 誤讀為腳本的
- [ ] help 與行為一致性須有回歸測試：斷言 --cleanup 的 help 文字不含已被推翻的說法、且含兩分支契約
- [ ] ⚠️ 須明列未驗項：拒絕分支只在 FakeGhRunner 封閉環境驗過、未對真實 GitHub 執行過一次被拒的 release；「無 --repo-path 的 release」本專案零歷史實例，⇒ 該留痕無法用既有資料驗證會被用到
## Log

- 2026-08-22T21:39:23+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-22T21:47:07+08:00 amend by wf-cli（op d7da0824）→ spec 基線：原值「—」→ 新值「WF-CLEANUP-GUARD1（#25，CLOSED）」；理由 補上游關係與資源共用，需求方 2026-08-22 裁定（選項甲）。本卡針對的正是 #25 交付的守衛「不帶 --cleanup 就印警示後照做」這個設計選擇，handoff_cmd.py docstring 逐字承認其刻意性，⇒ #25 是 spec 基線而非重複。另須留痕：#84 DEV-RELEASE-STATUS-DONE1（📥Backlog）宣告的資源含完全相同字串 file:cli/src/wf_cli/commands/handoff_cmd.py，兩張都改 release 路徑（#84 設 Status=Done、本卡改為拒絕），⇒ 排程時不得並行認領。⚠️ 另實測反證供 #84 參考、非本卡射程：#84 痛點寫「免部署卡 Issue 永遠開著」，但 2026-08-22 cpbl#169（免部署、帶 --cleanup）release 後 Issue 直接 CLOSED，只有漏帶 --cleanup 的 cpbl#166 沒關 ⇒ 該前提可能已不成立，PM 未查證何時被修。。
- 2026-08-22T22:00:26+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 0；SHA 251e211d8c3149a22a7ada483638b5fa884c7ed8；證據 T2 且改動唯一寫入通道的終態路徑 ⇒ 依需求方 2026-08-22 政策先跑 Discovery。單一核心未知：不帶 --cleanup 的 release 是否存在正當用途？若存在，拒絕會擋掉它們；若不存在，該旗標本身就不該是選配。Discovery 須以歷史事件與程式碼回答，不得憑推理。。
- 2026-08-22T22:03:28+08:00 handoff by wf-cli → owner ruan6047；iteration 0；SHA 251e211d8c3149a22a7ada483638b5fa884c7ed8；證據 Discovery 結論（2026-08-22，基線 ai-workflow origin/main 251e211d8c3149a22a7ada483638b5fa884c7ed8）。單一未知是「不帶 --cleanup 的 release 是否存在正當用途」。答案：存在，但只有一個，且它不支持現行的預設值。⇒ 本卡的形狀須修正：⛔ 不是「一律拒絕」，而是「可清理卻不清理時拒絕」。

發現一（決定性）：現行預設的理由與事實相反。--cleanup 的 help 逐字為「預設不清理——刪除不可逆，預設值取代價可回復的那一邊」。但不可逆的那一半早就被守衛以證明分級處理掉了。cleanup.py:390 的 AUTHORITY_BY_PROOF 逐字：ancestor 授權 remove_worktree、delete_local_branch、delete_remote_branch；content_absorbed（squash）只授權 remove_worktree、分支刻意保留；diverged 與 unobservable 皆為空集合；NO_AUTHORITY 亦為空集合，註解逐字「沒有任何證明可讀時的授權。空集合＝fail-closed：證不出來就不動手」。⇒ 只有在分支已被證明是 main 的祖先（即 commit 都在 main、刪了可用 git branch <name> <sha> 復原）時才會刪分支。⇒ 「刪除不可逆」這個危險在 --cleanup 內部已被中和。

而預設選的那一邊產生的是 illegal_terminal_before_cleanup ——守衛明文拒絕代修（2026-08-22 實得 illegal_state：「須人工判斷，守衛不代為修復」）。cpbl#166 因此只能人工刪 worktree、本地分支、遠端分支再手動關 Issue。⇒ 預設值實際上選了比較不可回復的那一邊，與它自己寫下的理由相反。

發現二：唯一的正當用途是「拿不到本機 repo」。handoff_cmd.py:429-430 逐字「拒絕：--cleanup 需要 --repo-path（守衛要在真實 repo 上驗前提）」，而 :434 的 if args.repo_path 顯示 release 本身不強制 --repo-path。⇒ 在沒有本機 checkout 的環境（例如只有 gh 憑證的機器）release 是做得到的，但 --cleanup 做不到。⛔ 一律拒絕會擋掉這個情境。

發現三：「已經人工清乾淨」不構成省略理由。cleanup.py:1429-1430 對無對象的情況回「收尾清理：無任何對象」，⇒ 帶著 --cleanup 跑一個沒東西可清的卡是良性的，不需要靠省略旗標繞開。

發現四（量化，含測不準揭露）：以 gh search issues 搜三個留痕字串，「收尾清理：…已清除」得 28 筆，「…未走到」與「…無任何對象」皆 0 筆。⚠️ 0 筆有兩種讀法且本輪無法區分：一是歷史上不帶 --cleanup 的 release 從未發生過（cpbl#166 是首例），二是不帶 --cleanup 的路徑根本不寫收尾留痕、⇒ 事後不可觀測。⛔ PM 未證明是哪一種，但兩種讀法都支持本卡：若是前者，拒絕不會擋到任何既有用法；若是後者，那條路徑的不可觀測本身就是缺口。

⇒ 修正後的形狀（待 Design gate 定案，本階段不實作）：給了 --repo-path 卻沒給 --cleanup 時拒絕——此時工具看得見資源、能證明繼續下去會產生非法態；沒給 --repo-path 時工具看不見資源，改為要求一個顯式的承認旗標，使進入非法態成為刻意行為而非漏打。⇒ 把「印警示後照做」換成「要嘛清理、要嘛明講你要跳過」，執行者從人的眼睛換成 CLI。

⚠️ 本階段未驗：一、發現四的 0 筆歸因未定，如上。二、未查 gh search 是否會漏索引 Issue body 中的中文字串，⇒ 28 這個數字可能低估。三、未列舉「沒有本機 repo 仍要 release」在本專案是否真的發生過——發現二證明它機械上可行，⛔ 未證明它實際被用過。四、未評估承認旗標的命名與是否該併入 --evidence。

⚠️ 排程限制不變：#84 DEV-RELEASE-STATUS-DONE1（📥Backlog）宣告的資源含完全相同字串 file:cli/src/wf_cli/commands/handoff_cmd.py，兩張都改 release 路徑，不得並行認領。。
- 2026-08-23T02:00:48+08:00 handoff by wf-cli → owner 排隊中：待 cpbl#172 結案，且不得與 aiwf#84 並行；iteration 0；SHA 251e211d8c3149a22a7ada483638b5fa884c7ed8；證據 Design gate 通過，需求方 2026-08-22 裁定採乙′。本則同時更正前一則 Discovery 留痕中的一個假數字。

⛔ 更正（重要）：前一則 Discovery 的「發現四」寫「以 gh search issues 搜『收尾清理：…已清除』得 28 筆」。該數字無效。gh search 命中的是「卡面文字含該字串」的卡，不是「有該筆留痕」的卡——第一筆命中就是本卡 aiwf#129 自己，因為 PM 把該字串寫進核心痛點裡了（重測總數 29，含本卡）。⇒ 留痕與散文引用在該搜尋層面無法區分，「清理成功過幾次」以此法測不到。PM 撤回該數字，不以它支持任何結論。

三輪追加研究的結果如下。

第一輪（決定性，解掉前一則的歸因未定）：handoff_cmd.py:558-561 逐字為 else: if args.next_stage == "release": print(NO_CLEANUP_WARNING, file=sys.stderr) 然後 write_status_face()。⇒ 不帶 --cleanup 的路徑不寫任何卡上留痕，唯一訊號是 stderr 一行字。⇒ 前一則「未走到／無任何對象皆 0 筆」的那個 0 是「構造上不可觀測」，不是「未發生」。⭐ 該不可觀測本身即缺口：illegal_terminal_before_cleanup 被造出來時零持久紀錄，事後無法稽核它發生過幾次。

第二輪（換可觀測面，找到歷史實例）：改以「遠端仍存在的 ai/* 分支」為觀測面，兩 repo 共 8 條。逐一以 git merge-base --is-ancestor 對 origin/main 判定：cpbl#126、#134、#152、#135 與 aiwf#88 皆非 main 祖先 ⇒ squash 合併，依 AUTHORITY_BY_PROOF 的 content_absorbed 只授權 remove_worktree、分支刻意保留，正確；cpbl#172 與 aiwf#89 仍在流程中，合法。⛔ 唯一例外是 cpbl#138 DATA-OFFICIAL-STATUS-TIEBREAK1 @ 6d534b12：它是 origin/main 的祖先卻仍存在於遠端，而 ancestor 授權本應刪它。查其 Issue body 無任何收尾留痕，Log 最後一筆為 2026-08-15T11:36:49+08:00 handoff by wf-cli → owner —（已結案）。⇒ 2026-08-15 已發生過一次不帶 --cleanup 的 release，cpbl#166 不是首例，已知兩例。

第三輪（決策修正）：前一則把「無本機 repo 的 release 是否真被用過」列為卡住決策的未知，並據此傾向甲案（廢除 --cleanup 旗標、release 強制 --repo-path）。第二輪的證據使該問題不再關鍵——兩個已知實例（#138、#166）都發生在有 --repo-path 的情況下，成因是有 repo 卻沒帶旗標，不是拿不到 repo。⇒ 甲案打的是一個沒有實例的靶。

⇒ 定案形狀（乙′）：一、給了 --repo-path 卻沒給 --cleanup 時拒絕——此時工具看得見資源、能證明繼續下去會產生守衛自己拒修的非法態，兩個已知實例皆落在此分支。二、沒給 --repo-path 時維持現行行為，但把該警示寫進卡上留痕而非只印 stderr——該分支無實例、不為它設計拒絕，但必須讓它可事後稽核，否則下一次仍然查不到。

⚠️ 仍未驗（須帶進實作與查核）：一、第二輪只掃「遠端仍活著的分支」。若某次未清理而分支事後被手動刪除，該次不可觀測 ⇒ 兩例是下限而非總數。二、#138 未清理是以「無留痕」推斷的，⛔ 未直接證明它當時沒帶 --cleanup（也可能帶了但刪除失敗）。三、承認旗標的命名、以及第二點的留痕該寫進 Log 事件或卡面哪一區，未定。四、AUTHORITY_BY_PROOF 的 diverged 與 unobservable 皆為空集合，本案未觸及，實作時不得順手更動。

⚠️ 排程限制不變：aiwf#84 DEV-RELEASE-STATUS-DONE1（📥Backlog）宣告的資源含完全相同字串 file:cli/src/wf_cli/commands/handoff_cmd.py，兩張都改 release 路徑，不得並行認領。。
- 2026-08-24T13:54:54+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree ai/opus-5/WF-RELEASE-NO-CLEANUP-REFUSE1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/release-no-cleanup-refuse1；交付狀態 🔨執行中；實際能力層級 高階型（偏離卡面建議 主力型；偏離理由：卡面建議主力型。實際由高階型執行：改的是唯一寫入通道的終態路徑，收緊過頭會擋掉正當收尾、不足等於沒改；且 Design gate 定案的形狀是兩分支（有 --repo-path 拒絕／無 --repo-path 要留痕），須同時處理兩條路徑與其偵測。）；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-24T14:03:24+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 0；SHA 4172324ef3c1f155ee85e1b37a142deee8cf50ad；證據 R1 交付 4172324ef3c1f155ee85e1b37a142deee8cf50ad（基線 251e211d8c3149a22a7ada483638b5fa884c7ed8，以 merge-base 實算）。兩檔：cli/src/wf_cli/commands/handoff_cmd.py（+42/-1）、cli/tests/test_release_cleanup.py（+61/-9）。

實作 Design gate 定案的兩分支形狀（見 issuecomment-5390450940 的 gate 記錄）：

一、--next-stage release 帶了 --repo-path 卻沒帶 --cleanup ⇒ 拒絕、rc=2、狀態面一個字都不寫。判準是「守衛看得見資源就不准製造非法態」。新增常數 REPO_PATH_WITHOUT_CLEANUP_REFUSAL，其 docstring 記錄為何從警示改為拒絕：原設計的理由是 --cleanup 的 help 逐字「預設不清理——刪除不可逆，預設值取代價可回復的那一邊」，但不可逆那一半早被 cleanup.AUTHORITY_BY_PROOF 以證明分級中和（ancestor 才授權刪分支、content_absorbed 只授權 remove_worktree、diverged 與 unobservable 皆為空集合、NO_AUTHORITY 亦空且註解逐字「空集合＝fail-closed：證不出來就不動手」）⇒ 預設選的那一邊產生的才是比較不可回復的狀態。

二、沒給 --repo-path ⇒ 行為不變（不拒絕、警示照印、狀態面照寫），但新增後綴 NO_REPO_PATH_TRACE_SUFFIX 寫進卡上 handoff Log 行。理由：該分支的 --cleanup 構造上做不到（既有拒絕 --cleanup and not args.repo_path），且本專案無該情境實例，⛔ 不為它設計拒絕；但它先前只印 stderr、卡上零紀錄，使該路徑事後不可觀測。

測試共 20 條通過（原 18＋改寫 2＋新增 2）。⚠️ 須特別說明：本卡改動使兩條既有測試轉紅，PM 判斷那是本卡的目的而非回歸——test_release_without_cleanup_flag_deletes_nothing 的 docstring 逐字「預設值取較安全的一邊：沒要求就不刪」，正是 Design gate 推翻的那個理由；test_cleanup_after_a_status_only_release_is_refused_as_illegal 的不變量仍成立，但到達非法態的路徑改為「無 --repo-path」，第一次呼叫因此不再帶 --repo-path。兩條皆已改寫並在 docstring 記錄變更理由。

新增兩條：test_release_without_repo_path_is_allowed_but_traced_on_the_card（驗留痕落在 handoff Log 行、以檔內既有 handoff_log_lines helper 讀取而非自造存取路徑）、test_non_release_stages_are_untouched_by_the_refusal（⭐ 驗拒絕不外溢——本卡今晚的 research／planning／backlog 三次 handoff 都帶 --repo-path 且無 --cleanup，收緊過頭會擋掉正當流程）。

⭐ 三個變異檢驗，各有對應測試轉紅 ⇒ 不是零資訊的檢查：拿掉拒絕分支 → test_repo_path_without_cleanup_is_refused_and_writes_nothing 紅；留痕後綴改回不傳 → test_release_without_repo_path_is_allowed_but_traced_on_the_card 紅；拒絕條件放寬為 not args.cleanup and args.repo_path（去掉 next_stage 限制）→ test_non_release_stages_are_untouched_by_the_refusal 紅。每次變異後皆還原原檔。

PM 自驗（照本 repo CI 的三步，⛔ 非套用 cpbl 慣例——本 repo CI 不跑 ruff）：uv lock --check 通過；uv run --frozen pytest -q 得 1086 passed；uv run --no-project --python 3.12 scripts/replay_escalation_rules.py 得 114/114 通過、rc=0（⭐ rc 以重導向取自腳本本身，非管線尾端——PM 今晚已四次把 tail 的 rc 誤讀為腳本的）。四個 trailer 齊全。

⚠️ 未驗到：一、拒絕分支只在 FakeGhRunner 的封閉環境驗過，⛔ 未對真實 GitHub 執行過一次被拒的 release。二、「無 --repo-path 的 release」在本專案無歷史實例，⇒ 該分支的留痕是為了未來可稽核，⛔ 無法用既有資料驗證它真的會被用到。三、aiwf#84（📥Backlog）宣告完全相同字串 file:cli/src/wf_cli/commands/handoff_cmd.py，兩張不得並行認領；#84 目前未被認領故無衝突。四、需求方已裁定本卡照做、不併入 aiwf#130（該卡的「結案倒轉」若落地會使本卡的碼可能被取代），⇒ 承認的代價已記於 issuecomment-5390728621。。
- 2026-08-24T14:18:06+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex；core_pain_resolved yes；self_run 10 項；findings 2 項（blocking 2）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-RELEASE-NO-CLEANUP-REFUSE1-e0-4172324ef3c1f155ee85e1b37a142deee8cf50ad。
- 2026-08-24T14:18:28+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 1；SHA 4172324ef3c1f155ee85e1b37a142deee8cf50ad；證據 R1 兩個阻擋。R1-001（executor）：--cleanup help 與模組說明仍保留已被推翻的「預設不清理較安全」說法，PM 只在新常數的 docstring 記了推翻、⛔ 沒改舊字面。R1-002（coordinator）：⭐ 本卡卡面的驗收與驗證欄至今是 TODO 佔位符，PM 帶著 TODO 送審——同一晚 PM 為 aiwf#130 寫了 11 條驗收，卻讓本卡空著。兩項皆已獨立證實（sed -n '21p' 與 :437-443 見過期字面；gh issue view 129 見兩個 TODO）。收回修正。。
- 2026-08-24T14:19:23+08:00 amend by wf-cli（op 727cf0cf）→ 驗收條件：原值「[ ] TODO：填入可獨立驗證的條件」→ 新值「handoff --next-stage release 帶 --repo-path 卻沒帶 --cleanup 時拒絕，rc=2，且狀態面一個字都不寫（owner／交付狀態／最後交接／iteration 皆未變、Issue 未關、worktree 與本地遠端分支皆在）；⛔ 拒絕不外溢：其他 next-stage（requirement／research／planning／backlog／implementation／review）帶 --repo-path 且無 --cleanup 一律不受影響。理由是本卡自身的 research／planning／backlog 三次 handoff 都是該組合；沒給 --repo-path 的 release 不拒絕、行為不變（警示照印、狀態面照寫），但「收尾清理未執行（worktree、本地分支、遠端分支皆未處理）」須寫進卡上 handoff Log 行——⛔ 不得只印 stderr；--cleanup 的 help 與模組說明須與新行為一致：⛔ 不得保留「預設不清理——刪除不可逆，預設值取代價可回復的那一邊」這個已被推翻的理由。推翻依據為 cleanup.AUTHORITY_BY_PROOF 僅在 ancestor 授權刪分支（content_absorbed 只授權 remove_worktree、diverged 與 unobservable 皆為空集合），⇒ 不可逆的那一半已被證明分級中和；拒絕與留痕兩處的常數須自帶推翻理由與兩例實害（cpbl#138 於 2026-08-15、cpbl#166 於 2026-08-22），⛔ 且須註明因該路徑先前不寫卡上留痕，兩例是下限而非總數」；理由 R1-002（major、blocking、attribution=coordinator）：本卡的驗收與驗證欄自開卡起是 TODO 佔位符，PM 帶著 TODO 送審。⛔ 同一晚 PM 為 aiwf#130 寫了 11 條驗收卻讓本卡空著。依已定案的兩分支行為補齊。。
- 2026-08-24T14:19:23+08:00 amend by wf-cli（op 727cf0cf）→ 驗證：原值「[ ] TODO：填入驗證指令與證據要求」→ 新值「三個變異檢驗各須有對應測試轉紅：移除拒絕分支、留痕後綴改回不傳、拒絕條件去掉 next_stage 限制。⚠️ 改 source 後須在 pytest 自己的 process 內印 module.__file__ 確認載入的是變異版——本 session 已有三次無效突變測試；照本 repo CI 的三步驗，⛔ 不套用 cpbl 慣例（本 repo CI 不跑 ruff）：cd cli && uv lock --check；cd cli && uv run --frozen pytest -q；uv run --no-project --python 3.12 scripts/replay_escalation_rules.py（⚠️ 該步在 repo 根，不在 cli/）；⚠️ rc 一律以重導向或 PIPESTATUS 取自受測對象本身，⛔ 不得取管線尾端——PM 本 session 已四次把 tail 的 rc 誤讀為腳本的；help 與行為一致性須有回歸測試：斷言 --cleanup 的 help 文字不含已被推翻的說法、且含兩分支契約；⚠️ 須明列未驗項：拒絕分支只在 FakeGhRunner 封閉環境驗過、未對真實 GitHub 執行過一次被拒的 release；「無 --repo-path 的 release」本專案零歷史實例，⇒ 該留痕無法用既有資料驗證會被用到」；理由 R1-002（major、blocking、attribution=coordinator）：本卡的驗收與驗證欄自開卡起是 TODO 佔位符，PM 帶著 TODO 送審。⛔ 同一晚 PM 為 aiwf#130 寫了 11 條驗收卻讓本卡空著。依已定案的兩分支行為補齊。。
- 2026-08-24T14:23:20+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 1；SHA e75d9e1b48247c5cc76f73283690b6feae1ef102；證據 R2 交付 e75d9e1b48247c5cc76f73283690b6feae1ef102（基線 251e211d8c3149a22a7ada483638b5fa884c7ed8）。R1 兩個阻擋皆處置。PR #131 仍為 open。

R1-002（阻擋，attribution=coordinator）閉環：本卡的驗收與驗證欄自開卡起是 TODO 佔位符，PM 帶著 TODO 送審。⭐ 同一晚 PM 為 aiwf#130 寫了 11 條驗收卻讓本卡空著——查核者的裁定完全正確，PM 無異議。已於 op 727cf0cf 補齊 5 條驗收與 5 條驗證，內容依已定案的兩分支行為，且包含查核者本輪指出的 help 一致性（驗收第 4 條）與變異檢驗須確認 module.__file__（驗證第 1 條）。

R1-001（阻擋，attribution=executor）閉環：模組說明的「預設不清理，理由寫在這裡而不是只寫在文件裡」整節改寫為兩分支契約；--cleanup 的 help 亦改寫。⭐ 兩處皆保留一段對舊論證的引述並標明它已被推翻及理由——原論證逐字「漏清理可以再跑一次補；刪錯了沒有補救」，而刪錯那一半早被 cleanup.AUTHORITY_BY_PROOF 以證明分級中和（只有 ancestor 授權刪分支、content_absorbed 只授權 remove_worktree、diverged 與 unobservable 皆為空集合、NO_AUTHORITY 亦空且註解逐字「空集合＝fail-closed：證不出來就不動手」）。

新增 test_cleanup_help_states_the_two_branch_contract。⭐ 該測試斷言的是 help 的實際輸出（build_parser 後 parse_args(["handoff","--help"]) 捕捉 stdout），⛔ 刻意不 grep 原始碼——模組說明 :228 刻意保留了對舊說法的逐字引述（那是歷史不是宣稱），grep 會誤判。⇒ 請查核者確認該取捨成立，或裁定引述也該移除。

變異檢驗四項，各有對應測試轉紅：移除拒絕分支 → test_repo_path_without_cleanup_is_refused_and_writes_nothing；留痕後綴改回不傳 → test_release_without_repo_path_is_allowed_but_traced_on_the_card；拒絕條件去掉 next_stage 限制 → test_non_release_stages_are_untouched_by_the_refusal；help 改回舊字面 → test_cleanup_help_states_the_two_branch_contract。每次變異後皆還原原檔。

PM 自驗（照本 repo CI 三步，rc 皆以重導向取自受測對象本身）：uv lock --check rc=0；uv run --frozen pytest -q rc=0、1087 passed；uv run --no-project --python 3.12 scripts/replay_escalation_rules.py rc=0、114/114 通過。四個 trailer 齊全。

⚠️ 仍未驗到（不變）：一、拒絕分支只在 FakeGhRunner 封閉環境驗過，⛔ 未對真實 GitHub 執行過一次被拒的 release。二、「無 --repo-path 的 release」本專案零歷史實例 ⇒ 該留痕無法用既有資料驗證會被用到。三、aiwf#84 宣告完全相同字串 file:cli/src/wf_cli/commands/handoff_cmd.py，兩張不得並行認領（#84 目前未被認領）。四、需求方已裁定本卡照做不併入 aiwf#130，該卡的結案倒轉若落地會使本卡的碼可能被取代。

⭐ PM 另記一件本輪的紀律事實：查核者的 R1-002 指出的是 PM 的送審前檢查不完整，而 PM 在同一晚對另一張卡做了五輪掃描確認「討論過但沒記」的漏項，⛔ 卻沒對本卡做最基本的欄位檢查。⇒ 那不是遺漏而是分配錯誤，PM 不辯解。。
- 2026-08-24T14:48:18+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex；core_pain_resolved yes；self_run 8 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-RELEASE-NO-CLEANUP-REFUSE1-e0-e75d9e1b48247c5cc76f73283690b6feae1ef102。
- 2026-08-24T14:48:42+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 2；SHA e75d9e1b48247c5cc76f73283690b6feae1ef102；證據 R2-001 阻擋：help 回歸測試以連續字串比對 argparse 格式化輸出，折行可把舊字面拆開使負向斷言通過。查核者已構造變異重現——保留所有現行關鍵字、把完整舊字面放在會折行的位置，測試 1 passed。⭐ 該缺陷屬 PM memory 記載的「零資訊的檢查」族：構造上可被繞過。收回以 ''.join(out.split()) 正規化後重驗，並重跑該折行變異確認轉紅。。
- 2026-08-24T14:52:38+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 2；SHA 294b4369a229a20d9ac98df32e8858bd20c940a5；證據 R3 交付 294b4369a229a20d9ac98df32e8858bd20c940a5（基線 251e211d8c3149a22a7ada483638b5fa884c7ed8）。R2 唯一 finding 已處置，單檔 cli/tests/test_release_cleanup.py。

R2-001（阻擋，help 測試可被折行繞過）閉環，且 PM 未僅採信而是獨立重現。

機制查明：argparse 走 textwrap，而 textwrap 的 break_long_words 預設為 True ⇒ 中文長串（無 ASCII 空白）會被從中間切斷 ⇒ 舊字面只要剛好落在折行處，連續字串的負向斷言就通過。

⚠️ PM 第一次的重現嘗試失敗——把舊字面塞在「需搭配 --repo-path。」之後，測試照樣轉紅、原始輸出仍含完整字面 ⇒ 沒打中折行點。改以程式掃 0 到 57 的填充長度，於 pad=42 時取得：原始輸出含該字面=False（被折斷）、去空白後含該字面=True（仍在）⇒ 繞過成立，查核者的 finding 完全正確。

修法：斷言前以 ''.join(capsys.readouterr().out.split()) 正規化，並多加一條負向斷言「預設不清理——刪除不可逆」。測試內以註解記錄機制與 pad=42 這個具體重現參數。

驗證兩個方向：一、pad=42 的繞過變異在修正後轉紅（修正前 pass）。二、前四個變異未被正規化弱化——重跑「移除拒絕分支」得 1 failed / 20 passed，對應測試仍抓得到。

⭐ PM 歸類：該缺陷屬「零資訊的檢查」族——構造上可被繞過。判準是「先講出什麼結果會推翻它」，而修正前的答案是「把舊字面放在折行處」，那正是查核者做的事。⇒ PM 寫測試時沒問那個問題。

PM 自驗（本 repo CI 三步，rc 皆以重導向取自受測對象本身）：uv lock --check rc=0；uv run --frozen pytest -q rc=0、1087 passed；scripts/replay_escalation_rules.py rc=0、114/114 通過。四個 trailer 齊全。

⚠️ 仍未驗到（不變）：一、拒絕分支只在 FakeGhRunner 封閉環境驗過，⛔ 未對真實 GitHub 執行過一次被拒的 release。二、「無 --repo-path 的 release」本專案零歷史實例 ⇒ 該留痕無法用既有資料驗證會被用到。三、aiwf#84 宣告完全相同字串 file:cli/src/wf_cli/commands/handoff_cmd.py，兩張不得並行認領。四、需求方已裁定本卡照做不併入 aiwf#130。

⚠️ 本輪新增一項未驗：⛔ 正規化只處理空白，未處理其他可能的分隔（例如若日後 help 內插入 ANSI 色碼或全形空白）。PM 未構造那些變異，也未主張正規化已窮舉所有繞過路徑。。
- 2026-08-24T15:03:00+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex；core_pain_resolved yes；self_run 8 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-RELEASE-NO-CLEANUP-REFUSE1-e0-294b4369a229a20d9ac98df32e8858bd20c940a5。
- 2026-08-24T15:03:23+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 3；SHA 294b4369a229a20d9ac98df32e8858bd20c940a5；證據 R3-001 阻擋，且 root_cause_id 與 R2-001 相同（help-output-linewrap-normalization-omission）⇒ ⭐ 同族第二次。PM 於 R3 派審包已預測「若構造出新的繞過，代表本輪修法與 R2 同族、只換一個分隔字元」——查核者用 U+200B 證實。⇒ 依 PM memory 的「同族連續多輪＝形狀錯了」，本輪不得再補一個要移除的字元，須換形狀：從「移除清單」（開放集合）改為「只保留允許字元」（封閉集合），並對 haystack 與 needle 施加同一個轉換。查核者的 disposition 已指出該形狀。。
- 2026-08-24T15:07:20+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 3；SHA 12d7fc7706d26a8a5cbe4c21cc9ad7bbe6ff740e；證據 R4 交付 12d7fc7706d26a8a5cbe4c21cc9ad7bbe6ff740e（基線 251e211d8c3149a22a7ada483638b5fa884c7ed8）。單檔 cli/tests/test_release_cleanup.py。

R3-001（阻擋，U+200B 可繞過正規化）閉環，⭐ 且處置的是形狀不是實例。

查核者維持與 R2-001 相同的 root_cause_id（help-output-linewrap-normalization-omission）⇒ 同族第二次。⭐ PM 於 R3 派審包已預測該可能性，逐字「若你能構造出一個新的繞過，那代表本輪的修法與 R2 同族、只是換了一個分隔字元」——查核者以 U+200B 證實。⇒ 依 PM memory 的「同族連續多輪＝形狀錯了」，本輪不再補一個要移除的字元。

形狀變更：從「移除清單」改為「封閉集合」。新增 comparable()——先剝 ANSI escape sequence，再只保留 str.isalnum() 為真的字元與底線。CJK 在 Unicode 下 isalnum() 為真 ⇒ 中文全保留；空白、零寬字元、破折號、標點、控制碼全部落掉。⛔ 移除清單是開放集合（永遠有下一個分隔字元：U+FEFF、ESC、各種 Unicode 空白），封閉集合沒有那個尾巴。

⚠️ 代價已釘進 docstring：破折號等標點也被移除 ⇒ 期待值必須走同一個轉換，否則含 —— 的負向期待永遠不會命中。⇒ 測試中 haystack 與 needle 兩側都呼叫 comparable()，那是本形狀的必要條件不是可選項。

五個繞過向量實測，皆為「原始輸出命中 False、comparable 命中 True」：換行折斷、U+200B、U+FEFF、全形空白 U+3000、ANSI 色碼。其中前四個以完整測試重跑確認轉紅（各 1 failed）。⇒ 包含查核者用的 U+200B 與 PM 自己在 R3 列為未驗的 ANSI 與全形空白。

未弱化既有防線：重跑「留痕後綴改回不傳」變異得 1 failed / 20 passed，對應測試仍抓得到。

PM 自驗（本 repo CI 三步，rc 皆以重導向取自受測對象本身）：uv lock --check rc=0；uv run --frozen pytest -q rc=0、1087 passed；scripts/replay_escalation_rules.py rc=0、114/114 通過。四個 trailer 齊全。

⚠️ ⛔ PM 不主張窮舉：封閉集合的邊界是 str.isalnum()，PM 未證明不存在「isalnum 為真但視覺上不可見或可用於偽裝」的字元（例如某些 Unicode 格式字元或同形異義字）。⇒ 本形狀比移除清單強，但不是不可能被繞過。請查核者判該界線是否可接受，或裁定需要更窄的允許集合（例如逐字列舉 CJK 區塊與 ASCII 範圍）。

⚠️ 仍未驗到（不變）：一、拒絕分支只在 FakeGhRunner 封閉環境驗過，未對真實 GitHub 執行過一次被拒的 release。二、「無 --repo-path 的 release」本專案零歷史實例。三、aiwf#84 宣告完全相同字串 file:cli/src/wf_cli/commands/handoff_cmd.py，兩張不得並行認領。四、需求方已裁定本卡照做不併入 aiwf#130。。
- 2026-08-24T15:17:06+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex；core_pain_resolved yes；self_run 9 項；findings 2 項（blocking 2）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-RELEASE-NO-CLEANUP-REFUSE1-e0-12d7fc7706d26a8a5cbe4c21cc9ad7bbe6ff740e。
- 2026-08-24T15:17:28+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 4；SHA 12d7fc7706d26a8a5cbe4c21cc9ad7bbe6ff740e；證據 R4 兩個阻擋，⭐ 兩者的 root_cause_id 皆為新（comparable-unicode-allowlist-overbroad、ansi-csi-grammar-incomplete）⇒ 依 PM 於 R4 派審包的請求，查核者確認這是「封閉集合的邊界選錯」而非「形狀錯」，與前三輪不同族。R4-001：str.isalnum() 保留 CJK Compatibility Ideographs，U+F967／U+F966 在 NFKC 下映射為不／復，現行實作保留原碼點。R4-002：ANSI regex 只吃數字與分號，私有 CSI ESC[?25l 未被剝除、殘留 25l 打斷禁止文字。收回：先 NFKC，再只保留 ASCII 字母數字、底線與明確列舉的 CJK Unified Ideographs 範圍；ANSI 改用完整 CSI 語法。。
- 2026-08-24T15:21:43+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 4；SHA 3a81c14bf03457985649e476984b90167aeee860；證據 R5 交付 3a81c14bf03457985649e476984b90167aeee860（基線 251e211d8c3149a22a7ada483638b5fa884c7ed8）。單檔 cli/tests/test_release_cleanup.py。R4 兩個 finding 皆處置。

⭐ 兩者皆為封閉集合的邊界錯而非形狀錯——查核者依 PM 於 R4 派審包的請求，用了兩個新的 root_cause_id（comparable-unicode-allowlist-overbroad、ansi-csi-grammar-incomplete），確認與前三輪不同族。PM 接受該歸類。

R4-001 閉環，PM 已獨立重現而非採信：str.isalnum() 連 CJK Compatibility Ideographs 一起保留。實測 U+F967 與 U+F966 的 isalnum() 皆為 True、NFKC 後分別映射為「不」「復」；以它們替換注入串後，原始命中=False、舊 comparable 命中=False ⇒ 繞過成立。

R4-002 閉環，同樣獨立重現：舊 ANSI regex 為 \x1b\[[0-9;]*[A-Za-z]，對私有 CSI \x1b[?25l 剝除後字串原樣保留 ⇒ 殘留 25l 打斷禁止文字、繞過成立。改用完整 CSI 語法 \x1b\[[0-?]*[ -/]*[@-~] 後剝除結果為完整原句。

修法：先剝完整 CSI 語法，再 NFKC 正規化，最後只保留逐字列舉的字元——ASCII 字母數字、底線、CJK Unified Ideographs U+4E00 到 U+9FFF 與 Ext A U+3400 到 U+4DBF。⇒ 允許集合從「isalnum() 為真」收窄為明列範圍。

七個向量實測，皆為原始命中 False、comparable 命中 True：換行折斷、U+200B、U+FEFF、全形空白 U+3000、ANSI 基本色碼、私有 CSI、CJK 相容漢字。其中 CJK 相容漢字、私有 CSI、折行 pad=42 三個以完整測試重跑確認轉紅（各 1 failed）。既有防線未弱化：21 passed。

comparable() 的 docstring 已釘進三輪演進與各自的失敗：R2 直接比對格式化輸出（折行即繞）、R3 str.split() 移除空白（U+200B 即繞，與 R2 同 root_cause_id ⇒ 形狀錯）、R4 只保留 isalnum()（形狀對但邊界太寬）。⇒ 後人讀得到為什麼是現在這個形狀。

PM 自驗（本 repo CI 三步，rc 皆以重導向取自受測對象本身）：uv lock --check rc=0；uv run --frozen pytest -q rc=0、1087 passed；scripts/replay_escalation_rules.py rc=0、114/114 通過。四個 trailer 齊全。

⛔ 仍不主張窮舉，界線已寫進 docstring：允許集合可以再窄（例如逐字列舉本專案實際用到的字）；NFKC 不處理所有同形異義——Cyrillic а 在 NFKC 下不變且不在允許集合內會被落掉（安全方向），但若攻擊面換成 ASCII 同形則本函式擋不住。⇒ 請查核者判該界線可否接受。

⚠️ 仍未驗到（不變）：一、拒絕分支只在 FakeGhRunner 封閉環境驗過，未對真實 GitHub 執行過一次被拒的 release。二、「無 --repo-path 的 release」本專案零歷史實例。三、aiwf#84 宣告完全相同字串 file:cli/src/wf_cli/commands/handoff_cmd.py，兩張不得並行認領。四、需求方已裁定本卡照做不併入 aiwf#130。

⭐ PM 另記：本卡的四輪查核已回饋到 aiwf#130——該卡的族對階段對應表把「守衛涵蓋不足或可被繞過」只印在規劃，而本卡的缺陷發生在執行，⇒ 對應表已據此更正並由需求方裁定退回 🧭規劃中 重新核可（issuecomment-5391882309）。那是 #130 第一次取得非循環的驗證證據。。
- 2026-08-24T15:34:58+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex；core_pain_resolved yes；self_run 5 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-RELEASE-NO-CLEANUP-REFUSE1-e0-3a81c14bf03457985649e476984b90167aeee860。
- 2026-08-24T15:35:21+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 5；SHA 3a81c14bf03457985649e476984b90167aeee860；證據 R5-001 阻擋：OSC 非 CSI 控制序列可繞過。⭐ 這是 ANSI 上的第二次（R4-002 是 CSI 語法不完整、本輪是非 CSI 家族遺漏）⇒ 依「同族連續多輪＝形狀錯了」，⛔ 不得再加一個要剝的 escape 家族——列舉 escape 家族是開放集合。查核者 disposition 的第二個選項即封閉形狀：在比較前明確拒絕 help 輸出中的非換行控制字元。⇒ 控制字元集合有限可列舉（C0 U+0000-001F、DEL U+007F、C1 U+0080-009F），只允許 \n \r \t，其餘出現即測試失敗，⛔ 不再嘗試正確剝除每個家族。。
- 2026-08-24T15:39:08+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 5；SHA baa02937567f1e3665b0132728273993cfa2aff1；證據 R6 交付 baa02937567f1e3665b0132728273993cfa2aff1（基線 251e211d8c3149a22a7ada483638b5fa884c7ed8）。單檔 cli/tests/test_release_cleanup.py。R5 唯一 finding 已處置，⭐ 且處置的是形狀不是實例。

R5-001 閉環。⭐ 這是 ANSI 上的第二次——R4-002 是 CSI 語法不完整、本輪是非 CSI 家族遺漏 ⇒ 依「同族連續多輪＝形狀錯了」，PM 不再加一個要剝的 escape 家族。查核者 disposition 的第二個選項（在比較前明確拒絕非換行控制字元）即該封閉形狀，PM 採用之。

⭐ 機制查明（PM 獨立重現而非採信）：OSC 的 payload 是英數字——'0;X' 的 '0' 與 'X' 通過 comparable 的允許集合，插在句中把字面切斷。實測 comparable(注入串) 得「預設值取0X代價可回復的那一邊」。⇒ ⛔ 即使正確剝掉 ESC 與 BEL，殘留的 payload 仍能繞過，所以「剝除」這條路本身是錯的。

形狀變更的依據：escape 家族是開放集合（CSI、OSC、DCS、APC、PM、SOS、單字元 ESC 序列…），⭐ 但控制字元本身是封閉集合（C0 U+0000 到 U+001F、DEL U+007F、C1 U+0080 到 U+009F）。⇒ 新增 assert_no_control_chars()：非 \n\r\t 的控制字元存在即失敗，⛔ 不嘗試剝除任何序列。comparable() 相應移除 _ANSI_RE，只負責可見字元的正規化。兩層分工寫進各自的 docstring。

⭐ 驗證的關鍵：六個變異全轉紅，其中三個是不同的 escape 家族——OSC 以 BEL 終止、OSC 以 ST 終止、DCS——而本輪的碼裡沒有列舉任何一個家族。它們被同一條控制字元斷言擋下。⇒ 這是形狀修法有效的直接證據，非個案修補。另加私有 CSI、CJK 相容漢字、折行 pad=42 三個回歸變異亦轉紅；既有防線未弱化（21 passed）。

PM 自驗（本 repo CI 三步，rc 皆以重導向取自受測對象本身）：uv lock --check rc=0；uv run --frozen pytest -q rc=0、1087 passed；scripts/replay_escalation_rules.py rc=0、114/114 通過。四個 trailer 齊全。

⛔ 仍不主張窮舉，界線已釘進 docstring：控制字元這一面已封閉（集合有限可列舉），⚠️ 但可見字元那一面沒有——NFKC 不處理所有同形異義，若攻擊面換成 ASCII 同形（例如把 illegal 寫成 il1egal）則 comparable 擋不住。⇒ 請查核者判該不對稱是否可接受：一面封閉、一面開放。

⚠️ 仍未驗到（不變）：一、拒絕分支只在 FakeGhRunner 封閉環境驗過，未對真實 GitHub 執行過一次被拒的 release。二、「無 --repo-path 的 release」本專案零歷史實例。三、aiwf#84 宣告完全相同字串 file:cli/src/wf_cli/commands/handoff_cmd.py，兩張不得並行認領。四、需求方已裁定本卡照做不併入 aiwf#130。

⭐ PM 記錄本卡的輪次成本供需求方判斷：本卡自 R1 至 R6 共六輪，其中 R2 至 R6 五輪全部在同一條 help 一致性測試上——R2 折行、R3 零寬字元、R4 CJK 相容漢字與私有 CSI、R5 OSC。⚠️ 該測試本身是 R1-001 的處置，而 R1-001 修的是「help 與行為不一致」這個非阻擋級的文件問題。⇒ 是否值得再投入，屬需求方的投資決策，PM 不代為判斷。。
- 2026-08-24T15:52:40+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 5；SHA cd88270f10d634e1e4f5c12bd6ac6a3e6b89f57f；證據 R7 交付 cd88270f10d634e1e4f5c12bd6ac6a3e6b89f57f（基線 251e211d8c3149a22a7ada483638b5fa884c7ed8）。單檔 cli/tests/test_release_cleanup.py，+50/-86（⭐ 淨減 36 行）。

R5-001 閉環，⭐ 但處置的不是那一個繞過，是整條路徑。

需求方要求 PM 研究風險後給建議，PM 據此發現一件應該在 R2 就發現的事：⛔ 本 repo 早有黃金值的先例，而 PM 五輪都在自己發明。tests/test_amend.py:1064-1075 記載三件套，其中 test_golden_note_is_reflow_stable 直接命中 PM 打了五輪的折行問題。⇒ 那正是 aiwf#130 核心痛點第二段的形態——教訓不在該用的那一刻出現，只是這次不是 memory 而是同一個 repo 裡的既有測試。

形狀變更的依據：R2 折行、R3 U+200B、R4 CJK 相容漢字與私有 CSI、R5 OSC，五個繞過的修法都是「再列舉一個要處理的字元或 escape 家族」。⛔ 自由文字上的負向斷言構造上封閉不了——永遠有下一種混淆。⭐ 逐字黃金值是封閉的：任何插入都會改變字串；且它斷言的是 argparse 的原始 help 字串而非格式化輸出，⇒ 折行那一整族的問題根本不存在。

三件套（形狀取自既有先例，⛔ 不自行發明）：test_cleanup_help_is_verbatim_golden 逐字比對原始 help；test_cleanup_help_golden_is_reflow_stable 檢查黃金值不含連續空白或換行；test_cleanup_help_golden_carries_the_two_branch_contract 釘住語意必要成分（兩分支契約、illegal_terminal_before_cleanup、收尾清理未執行）並斷言舊說法不在黃金值裡。

移除 comparable() 與 assert_no_control_chars()，約 60 行。⚠️ ⛔ 那不是回歸，請查核者特別確認：黃金值讓控制字元與字元混淆問題構造上不存在，而非改為不檢查。實測為證——六個歷史繞過向量各自 1 failed：折行 pad=42、U+200B、CJK 相容漢字、私有 CSI、OSC 以 BEL 終止、DCS。⭐ 而黃金值的碼裡沒有列舉任何字元或 escape 家族。另 R1-001 的真實回歸（help 整段改回舊字面）亦 1 failed。

PM 自驗（本 repo CI 三步，rc 皆以重導向取自受測對象本身）：uv lock --check rc=0；uv run --frozen pytest -q rc=0、1089 passed；scripts/replay_escalation_rules.py rc=0、114/114 通過。四個 trailer 齊全。

⚠️ 承認的代價：help 正當修改時本測試必紅、須同步黃金值。⭐ 那是特性不是缺陷——它強制一次刻意的動作，且 diff 會顯示改了什麼。維護成本已量：handoff_cmd.py 該檔存在以來總 commit 數為 10，且 --cleanup 的 help 為純字串常數（動態片段 0）。

⛔ 不驗語意：若有人把黃金值與 help 一起改成錯的，測試會過。那一層靠查核，而 R1-001 本來就是查核抓到的。

⚠️ 仍未驗到（不變）：一、拒絕分支只在 FakeGhRunner 封閉環境驗過，未對真實 GitHub 執行過一次被拒的 release。二、「無 --repo-path 的 release」本專案零歷史實例。三、aiwf#84 宣告完全相同字串 file:cli/src/wf_cli/commands/handoff_cmd.py，兩張不得並行認領。四、需求方已裁定本卡照做不併入 aiwf#130。

⭐ PM 記錄輪次成本供需求方判斷（不變）：本卡 R1 至 R7 共七輪，其中 R2 至 R7 六輪全部在同一條 help 一致性測試上，而該測試是 R1-001 的處置、R1-001 修的是非阻擋級的文件不一致。核心痛點（release 製造不可修復的非法態）自 R1 起每輪 core_pain_resolved 皆為 yes。⇒ 是否值得再投入屬需求方的投資決策，PM 不代為判斷。。
- 2026-08-24T16:04:42+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex；core_pain_resolved yes；self_run 5 項；findings 0 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-RELEASE-NO-CLEANUP-REFUSE1-e0-cd88270f10d634e1e4f5c12bd6ac6a3e6b89f57f。
- 2026-08-24T16:06:46+08:00 handoff by wf-cli → owner ruan6047；iteration 5；SHA cd88270f10d634e1e4f5c12bd6ac6a3e6b89f57f；證據 需求方 2026-08-24 授權合併。⭐ 以 cpbl#166 交付、cpbl#172 修正後的合併程序執行（該程序住在 cpbl 的 AI_RUNBOOK，本次為它首度用於 ai-workflow）。

實得：第 3 步判準對 cd88270f 得 true（本 repo 的 required check 是 tests，非 cpbl 的 api/web，PM 已相應替換名稱）；第 4 步 251e211..cd88270  HEAD -> main；第 4b 步 Updating 251e211..cd88270 / Fast-forward，本地 main 同步；第 5 步印「本分支無 open PR，不動」，PR #131 於 2026-08-24T08:05:50Z 自動標為 MERGED。查核 SHA 與合併 SHA 相同，無 rebase。

⭐ 4b 的價值再次確認：本次收尾未被 merge_verified_local 阻擋，與 cpbl#169 那次（本地 main 過期、rc=5）形成對照。

七輪的結果與成本，供後人判斷：核心痛點（release 帶 --repo-path 卻不清理會製造守衛自己拒修的非法態）於 R1 即解決，core_pain_resolved 自 R1 起每輪皆為 yes。⚠️ 而 R2 至 R7 六輪全部在同一條 help 一致性測試上——該測試是 R1-001 的處置，而 R1-001 修的是「help 與行為不一致」這個非阻擋級的文件問題。五個繞過依序為折行、U+200B、CJK 相容漢字與私有 CSI、OSC；最終以逐字黃金值收斂，查核者另構造 U+2060 亦被捕捉。

⭐ 最該留給後人的一件事：跳出法本 repo 早有先例而 PM 五輪都在自己發明。tests/test_amend.py:1064-1075 的黃金值三件套，其中 test_golden_note_is_reflow_stable 直接命中 PM 打了五輪的折行問題。⇒ 那是 aiwf#130 核心痛點第二段的實例——教訓不在該用的那一刻出現，只是這次不是 AI 私有 memory，而是同一個 repo 裡的既有測試。該實例已回饋至 #130。

⚠️ 交付未涵蓋（不變）：拒絕分支只在 FakeGhRunner 封閉環境驗過，未對真實 GitHub 執行過一次被拒的 release；「無 --repo-path 的 release」本專案零歷史實例，該留痕無法用既有資料驗證會被用到。

⚠️ 排程：aiwf#84（📥Backlog）宣告完全相同字串 file:cli/src/wf_cli/commands/handoff_cmd.py，本卡合併後該檔已變動，#84 認領前須重新對齊 origin/main。另 aiwf#130 的「結案倒轉」若日後落地，會使本卡的碼可能被取代——需求方已於 issuecomment-5390728621 裁定接受該代價。；收尾清理：已清除 worktree、本地分支、遠端分支。
- 2026-08-26T22:19:04+08:00 amend by wf-cli（op 07df6706）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:52eb79287256f81ba93ca539b296a9212fda739273e923fd42de0c89484cd0dc (728 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5390728621 · 2026-08-24T04:27:28Z

## 需求方裁定（2026-08-24）：本卡照做，不併入 aiwf#130

`aiwf#130`（T4，🧭規劃中）的定案設計含「結案不是需求方去設的值，是 CLI 清理成功後自己寫下的結果」⇒ 若該卡落地，本卡要防的 `illegal_terminal_before_cleanup` **構造上進不去**，本卡的碼可能因此被取代。

需求方裁定**本卡照原計畫執行**（選項甲）。理由：`#130` 是 T4、七項射程、跨兩 repo，落地時程未知；而本卡修的是**已發生兩次**的靜默失敗（cpbl#138 於 2026-08-15、cpbl#166 於 2026-08-22，且因該路徑不寫卡上留痕，兩例是下限非總數）。⇒ 承認的代價：本卡的碼日後可能被 `#130` 取代，但那比讓非法態繼續存在便宜。

⚠️ 排程限制不變：`aiwf#84`（📥Backlog）宣告完全相同字串 `file:cli/src/wf_cli/commands/handoff_cmd.py`，兩張不得並行認領。

## Comment 5391441964 · 2026-08-24T06:18:08Z

<!-- wf-review-event:v1 card_id=WF-RELEASE-NO-CLEANUP-REFUSE1 source_sha=4172324ef3c1f155ee85e1b37a142deee8cf50ad attempt_id=WF-RELEASE-NO-CLEANUP-REFUSE1-e0-4172324ef3c1f155ee85e1b37a142deee8cf50ad -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-RELEASE-NO-CLEANUP-REFUSE1`　attempt_id：`WF-RELEASE-NO-CLEANUP-REFUSE1-e0-4172324ef3c1f155ee85e1b37a142deee8cf50ad`
- 查核者：GPT-5@Codex　escalation_epoch：0
- source_sha：`4172324ef3c1f155ee85e1b37a142deee8cf50ad`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-24T14:18:06+08:00

### self_run（查核者實跑）

- `git -C /tmp/r129 rev-parse HEAD && git status --porcelain=v1 && git merge-base origin/main HEAD`
  - HEAD=4172324ef3c1f155ee85e1b37a142deee8cf50ad；工作區乾淨；merge-base=251e211d8c3149a22a7ada483638b5fa884c7ed8
- `gh pr view 131 --repo ruan6047/ai-workflow --json state,headRefOid,statusCheckRollup`
  - PR OPEN；head SHA 相符；tests 與 tests (branch head) 均 SUCCESS
- `cd /tmp/r129/cli && uv lock --check`
  - rc=0
- `cd /tmp/r129/cli && uv run --frozen pytest -q`
  - 1086 passed in 70.36s
- `cd /tmp/r129 && uv run --no-project --python 3.12 scripts/replay_escalation_rules.py`
  - 114/114 通過；腳本 rc=0
- `以 PYTHONPATH 指向 /tmp/r129/cli/src 的前置分支探針，列舉 10 組 next-stage、repo-path、cleanup 組合`
  - 只有 release+repo-path+無 cleanup 回 rc=2；六個非 release stage 均 reached_target
- `在 /tmp/r129-mut-refusal 移除拒絕分支後跑對應測試`
  - module.__file__ 指向該 worktree；1 failed，實得 rc=0 非預期 rc=2
- `在 /tmp/r129-mut-trace 移除留痕後綴後跑對應測試`
  - module.__file__ 指向該 worktree；1 failed，handoff Log 未含收尾清理未執行
- `在 /tmp/r129-mut-scope 移除 next_stage 限制後跑對應測試`
  - module.__file__ 指向該 worktree；1 failed，implementation 實得 rc=2
- `cd /tmp/r129/cli && uv run --frozen wfcli handoff --help`
  - --cleanup help 仍輸出「預設不清理……預設值取代價可回復的那一邊」

### findings（2，其中 blocking 2）

- **WF-RELEASE-NO-CLEANUP-REFUSE1-R1-001**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`release-cleanup-help-contract-stale`
  - evidence：實作已令 release+repo-path+無 cleanup 回 rc=2，但 handoff help 與模組說明仍宣稱預設不清理是較可回復的一邊。
  - disposition：更新 --cleanup help 與模組說明為兩分支契約，並加入 help 與行為一致性的回歸測試。
- **WF-RELEASE-NO-CLEANUP-REFUSE1-R1-002**　severity=major　blocking=true　class=governance　attribution=coordinator　root_cause_id=`review-preflight-required-sections-left-todo`
  - evidence：GitHub #129 的「驗收條件」與「驗證」章節仍分別保留 TODO 佔位符。
  - disposition：由 PM 祕書依已定案的兩分支行為補齊可獨立驗證的驗收與驗證欄，完成送審前檢查後再交付。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-RELEASE-NO-CLEANUP-REFUSE1-e0-4172324ef3c1f155ee85e1b37a142deee8cf50ad
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（待指派）
findings:
  - finding_id: WF-RELEASE-NO-CLEANUP-REFUSE1-R1-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: release-cleanup-help-contract-stale
    counting_eligible: true
  - finding_id: WF-RELEASE-NO-CLEANUP-REFUSE1-R1-002
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: governance
    attribution: coordinator
    root_cause_id: review-preflight-required-sections-left-todo
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5391701902 · 2026-08-24T06:48:20Z

<!-- wf-review-event:v1 card_id=WF-RELEASE-NO-CLEANUP-REFUSE1 source_sha=e75d9e1b48247c5cc76f73283690b6feae1ef102 attempt_id=WF-RELEASE-NO-CLEANUP-REFUSE1-e0-e75d9e1b48247c5cc76f73283690b6feae1ef102 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-RELEASE-NO-CLEANUP-REFUSE1`　attempt_id：`WF-RELEASE-NO-CLEANUP-REFUSE1-e0-e75d9e1b48247c5cc76f73283690b6feae1ef102`
- 查核者：GPT-5@Codex　escalation_epoch：0
- source_sha：`e75d9e1b48247c5cc76f73283690b6feae1ef102`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-24T14:48:18+08:00

### self_run（查核者實跑）

- `git -C /tmp/r129b rev-parse HEAD && git status --porcelain=v1 && git merge-base origin/main HEAD`
  - HEAD=e75d9e1b48247c5cc76f73283690b6feae1ef102；工作區乾淨；merge-base=251e211d8c3149a22a7ada483638b5fa884c7ed8
- `gh pr view 131 --repo ruan6047/ai-workflow --json state,headRefOid,statusCheckRollup`
  - PR OPEN；head SHA 相符；tests 與 tests (branch head) 均 SUCCESS
- `gh issue view 129 --repo ruan6047/ai-workflow --json body`
  - 驗收條件 5 條、驗證 5 條；各節 TODO=false；已明列兩項未驗邊界
- `cd /tmp/r129b/cli && uv lock --check`
  - rc=0
- `cd /tmp/r129b/cli && uv run --frozen pytest -q`
  - 1087 passed in 71.12s
- `cd /tmp/r129b && uv run --no-project --python 3.12 scripts/replay_escalation_rules.py`
  - 114/114 通過；rc=0
- `四個 disposable mutation worktree 以 PYTHONPATH 指向各自 cli/src，並印出 module.__file__ 後執行對應單測`
  - 移除拒絕、移除留痕、放寬拒絕範圍、改回舊 help，四項各自 1 failed；每次 module.__file__ 均為變異 worktree
- `在 disposable worktree 保留兩分支關鍵字，並將完整舊 help 字面放在 argparse 會折行的位置後執行 test_cleanup_help_states_the_two_branch_contract`
  - module.__file__ 為變異 worktree；測試 1 passed；原始輸出不含連續字串，但移除所有空白後可偵測完整舊字面

### findings（1，其中 blocking 1）

- **WF-RELEASE-NO-CLEANUP-REFUSE1-R2-001**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`help-output-linewrap-normalization-omission`
  - evidence：help 回歸測試直接以連續字串比對 argparse 格式化輸出。折行可將舊字面拆開，使負向斷言通過；已以保留所有現行關鍵字的變異重現。
  - disposition：在斷言前以 ''.join(out.split()) 正規化 help 輸出，再檢查舊字面不存在與兩分支契約存在；重跑該折行變異，必須轉紅。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-RELEASE-NO-CLEANUP-REFUSE1-e0-e75d9e1b48247c5cc76f73283690b6feae1ef102
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（待指派）
findings:
  - finding_id: WF-RELEASE-NO-CLEANUP-REFUSE1-R2-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: help-output-linewrap-normalization-omission
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5391812354 · 2026-08-24T07:03:02Z

<!-- wf-review-event:v1 card_id=WF-RELEASE-NO-CLEANUP-REFUSE1 source_sha=294b4369a229a20d9ac98df32e8858bd20c940a5 attempt_id=WF-RELEASE-NO-CLEANUP-REFUSE1-e0-294b4369a229a20d9ac98df32e8858bd20c940a5 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-RELEASE-NO-CLEANUP-REFUSE1`　attempt_id：`WF-RELEASE-NO-CLEANUP-REFUSE1-e0-294b4369a229a20d9ac98df32e8858bd20c940a5`
- 查核者：GPT-5@Codex　escalation_epoch：0
- source_sha：`294b4369a229a20d9ac98df32e8858bd20c940a5`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-24T15:03:00+08:00

### self_run（查核者實跑）

- `git -C /tmp/r129c rev-parse HEAD && git status --porcelain=v1 && git merge-base origin/main HEAD`
  - HEAD=294b4369a229a20d9ac98df32e8858bd20c940a5；工作區乾淨；merge-base=251e211d8c3149a22a7ada483638b5fa884c7ed8
- `gh pr view 131 --repo ruan6047/ai-workflow --json state,headRefOid,statusCheckRollup`
  - PR OPEN；head SHA 相符；tests 與 tests (branch head) 均 SUCCESS
- `cd /tmp/r129c/cli && uv lock --check && uv run --frozen pytest -q`
  - lock rc=0；1087 passed in 69.19s
- `cd /tmp/r129c && uv run --no-project --python 3.12 scripts/replay_escalation_rules.py`
  - 114/114 通過；rc=0
- `在 pad=42 disposable worktree 跑 test_cleanup_help_states_the_two_branch_contract`
  - module.__file__ 指向變異 worktree；1 failed，折行後的舊字面已被正規化偵測
- `在移除拒絕分支的 disposable worktree 跑對應測試`
  - module.__file__ 指向變異 worktree；1 failed，實得 rc=0 非預期 rc=2
- `在 help 舊宣稱的兩個禁止片段內插入 U+200B，再跑 test_cleanup_help_states_the_two_branch_contract`
  - module.__file__ 指向變異 worktree；測試 1 passed；raw_old_literal=false，但移除 U+200B 後完整舊宣稱=true，zero_width_count=2
- `python 檢查 U+3000、U+200B、U+FEFF、ESC 的 isspace 與 split 行為`
  - U+3000 會被 split 移除；U+200B、U+FEFF、ESC 均不會

### findings（1，其中 blocking 1）

- **WF-RELEASE-NO-CLEANUP-REFUSE1-R3-001**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`help-output-linewrap-normalization-omission`
  - evidence：R3 只以 str.split() 移除空白。U+200B 插入「不可逆」與「預設值取」內後，使用者視覺上仍是舊宣稱，移除零寬字元可還原完整字面，但現有測試通過。
  - disposition：先移除 ANSI escape sequence，再建立只保留 ASCII 字母數字、底線與 CJK 字元的比較字串；相應把含破折號的負向期待值改為其比較字串形式，並加入 U+200B 變異，必須轉紅。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-RELEASE-NO-CLEANUP-REFUSE1-e0-294b4369a229a20d9ac98df32e8858bd20c940a5
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（待指派）
findings:
  - finding_id: WF-RELEASE-NO-CLEANUP-REFUSE1-R3-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: help-output-linewrap-normalization-omission
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5391931362 · 2026-08-24T07:17:08Z

<!-- wf-review-event:v1 card_id=WF-RELEASE-NO-CLEANUP-REFUSE1 source_sha=12d7fc7706d26a8a5cbe4c21cc9ad7bbe6ff740e attempt_id=WF-RELEASE-NO-CLEANUP-REFUSE1-e0-12d7fc7706d26a8a5cbe4c21cc9ad7bbe6ff740e -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-RELEASE-NO-CLEANUP-REFUSE1`　attempt_id：`WF-RELEASE-NO-CLEANUP-REFUSE1-e0-12d7fc7706d26a8a5cbe4c21cc9ad7bbe6ff740e`
- 查核者：GPT-5@Codex　escalation_epoch：0
- source_sha：`12d7fc7706d26a8a5cbe4c21cc9ad7bbe6ff740e`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-24T15:17:06+08:00

### self_run（查核者實跑）

- `git -C /tmp/r129d rev-parse HEAD && git status --porcelain=v1 && git merge-base origin/main HEAD`
  - HEAD=12d7fc7706d26a8a5cbe4c21cc9ad7bbe6ff740e；工作區乾淨；merge-base=251e211d8c3149a22a7ada483638b5fa884c7ed8
- `gh pr view 131 --repo ruan6047/ai-workflow --json state,headRefOid,statusCheckRollup`
  - PR OPEN；head SHA 相符；tests 與 tests (branch head) 均 SUCCESS
- `cd /tmp/r129d/cli && uv lock --check && uv run --frozen pytest -q`
  - lock rc=0；1087 passed in 62.20s
- `cd /tmp/r129d && uv run --no-project --python 3.12 scripts/replay_escalation_rules.py`
  - 114/114 通過；rc=0
- `對換行、U+200B、U+FEFF、U+3000、ANSI 基本色碼分別呼叫 comparable`
  - 五個向量皆為 raw=false、comparable=true
- `在 pad=42 disposable worktree 跑 help 測試`
  - module.__file__ 指向變異 worktree；1 failed
- `在移除留痕後綴的 disposable worktree 跑對應測試`
  - module.__file__ 指向變異 worktree；1 failed
- `在 help 內以 U+F967 替換「不」、U+F966 替換「復」，再跑 help 測試`
  - module.__file__ 指向變異 worktree；測試 1 passed；原始字面=false；NFKC 後再比較可還原完整舊宣稱=true
- `在 help 禁止片段內插入私有 CSI ESC[?25l，再跑 help 測試`
  - module.__file__ 指向變異 worktree；測試 1 passed；現行 comparable 偵測=false；完整 CSI 規則剝除後偵測=true

### findings（2，其中 blocking 2）

- **WF-RELEASE-NO-CLEANUP-REFUSE1-R4-001**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`comparable-unicode-allowlist-overbroad`
  - evidence：str.isalnum() 保留 CJK Compatibility Ideograph。U+F967（不）與 U+F966（復）在 NFKC 下分別映射為「不」「復」，但現行 comparable 保留原碼點，讓兩段負向斷言皆被繞過。
  - disposition：先做 NFKC，再只保留 ASCII 字母數字、底線與明確列舉的 CJK Unified Ideographs 範圍；新增這組相容漢字變異，必須轉紅。
- **WF-RELEASE-NO-CLEANUP-REFUSE1-R4-002**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`ansi-csi-grammar-incomplete`
  - evidence：現行 ANSI regex 僅匹配數字與分號參數。有效私有 CSI ESC[?25l 不會被剝除，過濾後殘留 25l，能打斷兩段禁止文字並讓測試通過。
  - disposition：將 ANSI CSI 匹配改為完整語法，例如 ESC[ 後接受 [0-?]*、[ -/]*、[@-~]；新增私有 CSI 變異，必須轉紅。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-RELEASE-NO-CLEANUP-REFUSE1-e0-12d7fc7706d26a8a5cbe4c21cc9ad7bbe6ff740e
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（待指派）
findings:
  - finding_id: WF-RELEASE-NO-CLEANUP-REFUSE1-R4-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: comparable-unicode-allowlist-overbroad
    counting_eligible: true
  - finding_id: WF-RELEASE-NO-CLEANUP-REFUSE1-R4-002
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: ansi-csi-grammar-incomplete
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5392085621 · 2026-08-24T07:35:00Z

<!-- wf-review-event:v1 card_id=WF-RELEASE-NO-CLEANUP-REFUSE1 source_sha=3a81c14bf03457985649e476984b90167aeee860 attempt_id=WF-RELEASE-NO-CLEANUP-REFUSE1-e0-3a81c14bf03457985649e476984b90167aeee860 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-RELEASE-NO-CLEANUP-REFUSE1`　attempt_id：`WF-RELEASE-NO-CLEANUP-REFUSE1-e0-3a81c14bf03457985649e476984b90167aeee860`
- 查核者：GPT-5@Codex　escalation_epoch：0
- source_sha：`3a81c14bf03457985649e476984b90167aeee860`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-24T15:34:58+08:00

### self_run（查核者實跑）

- `git clone --branch ai/opus-5/WF-RELEASE-NO-CLEANUP-REFUSE1 ruan6047/ai-workflow /tmp/r129e && git rev-parse HEAD && git merge-base origin/main HEAD`
  - 交付 SHA 為 3a81c14bf03457985649e476984b90167aeee860；merge-base 為 251e211d8c3149a22a7ada483638b5fa884c7ed8；worktree 乾淨
- `cd /tmp/r129e/cli && uv lock --check && uv run --frozen pytest -q`
  - lock 通過；1087 passed in 72.14s
- `cd /tmp/r129e && uv run --no-project --python 3.12 scripts/replay_escalation_rules.py`
  - 114/114 通過
- `在獨立 worktree 將 help 注入 OSC 序列，以 PYTHONPATH 對應該 worktree 執行 help 測試並列印 module.__file__`
  - module_file 指向 /private/tmp/r129e-mut-osc/cli/src/wf_cli/commands/handoff_cmd.py；目標測試仍 1 passed；原始與目前 comparable 比對皆 False，但先剝 OSC 後兩段舊說法皆為 True
- `以目前 comparable() 對換行、U+200B、U+FEFF、U+3000、基本 CSI、私有 CSI、CJK 相容漢字各自注入舊字面`
  - 七個向量均為 raw=False、comparable=True

### findings（1，其中 blocking 1）

- **WF-RELEASE-NO-CLEANUP-REFUSE1-R5-001**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`ansi-noncsi-escape-family-omission`
  - evidence：目前 _ANSI_RE 僅匹配 ESC[ 的 CSI。將兩段舊說法分別插入 OSC 後，help 測試通過；終端移除 OSC 後可還原「預設不清理——刪除不可逆」與「預設值取代價可回復的那一邊」。
  - disposition：正規化前應處理 OSC（含 BEL 與 ST 終止）等非 CSI 控制字串；或在比較前明確拒絕 help 輸出中的非換行控制字元。新增此變異的回歸測試，並確認載入變異 worktree 模組。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-RELEASE-NO-CLEANUP-REFUSE1-e0-3a81c14bf03457985649e476984b90167aeee860
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（待指派）
findings:
  - finding_id: WF-RELEASE-NO-CLEANUP-REFUSE1-R5-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: ansi-noncsi-escape-family-omission
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5392363038 · 2026-08-24T08:04:44Z

<!-- wf-review-event:v1 card_id=WF-RELEASE-NO-CLEANUP-REFUSE1 source_sha=cd88270f10d634e1e4f5c12bd6ac6a3e6b89f57f attempt_id=WF-RELEASE-NO-CLEANUP-REFUSE1-e0-cd88270f10d634e1e4f5c12bd6ac6a3e6b89f57f -->
## 查核裁決：APPROVE

- 卡：`WF-RELEASE-NO-CLEANUP-REFUSE1`　attempt_id：`WF-RELEASE-NO-CLEANUP-REFUSE1-e0-cd88270f10d634e1e4f5c12bd6ac6a3e6b89f57f`
- 查核者：GPT-5@Codex　escalation_epoch：0
- source_sha：`cd88270f10d634e1e4f5c12bd6ac6a3e6b89f57f`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-24T16:04:42+08:00

### self_run（查核者實跑）

- `gh repo clone ruan6047/ai-workflow /tmp/r129f -- --branch ai/opus-5/WF-RELEASE-NO-CLEANUP-REFUSE1 && git rev-parse HEAD && git merge-base origin/main HEAD`
  - HEAD 為 cd88270f10d634e1e4f5c12bd6ac6a3e6b89f57f；merge-base 為 251e211d8c3149a22a7ada483638b5fa884c7ed8；worktree 乾淨
- `git diff --stat baa02937567f1e3665b0132728273993cfa2aff1 HEAD && gh pr view 131 --json state,headRefOid,mergeStateStatus,statusCheckRollup`
  - 僅 test_release_cleanup.py 變更 +50/-86；PR OPEN、head 相符、mergeState CLEAN；兩個 tests check 均 SUCCESS
- `cd /tmp/r129f/cli && uv lock --check && uv run --frozen pytest -q`
  - lock 通過；1089 passed in 68.71s
- `cd /tmp/r129f && uv run --no-project --python 3.12 scripts/replay_escalation_rules.py`
  - 114/114 通過
- `在獨立 worktree 將 help 的「兩分支契約」插入 U+2060；列印 module.__file__ 後以 PYTHONPATH 指向該 worktree 執行 test_cleanup_help_is_verbatim_golden`
  - module_file 指向 /private/tmp/r129f-mut-wj/cli/src/wf_cli/commands/handoff_cmd.py；變異測試 1 failed，逐字黃金值捕捉插入

### findings（0，其中 blocking 0）

- （無）

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-RELEASE-NO-CLEANUP-REFUSE1-e0-cd88270f10d634e1e4f5c12bd6ac6a3e6b89f57f
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（待指派）
findings: []
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。
