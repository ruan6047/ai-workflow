# #78 WF-CLEANUP-SQUASH-AWARE1 收尾守衛用祖先關係驗合併，而 squash 合併永遠不產生祖先關係——兩條裁定互相打架
- state: closed  created: 2026-08-13T00:47:56Z  closed: 2026-08-13T07:08:16Z
- url: https://github.com/ruan6047/ai-workflow/issues/78
- comments: 12

## Body

- 需求：—　規劃：—
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；改的是 WF-CLEANUP-GUARD1 已通過查核的破壞性路徑守衛。難點不在寫碼，在裁定「內容已在 main」該用什麼證明取代祖先關係，且該證明不得比祖先關係弱——放寬它等於讓未合併的分支也能被刪。）　查核：待指派（建議 主力型；紅線：本卡碰的是唯一會刪除工作內容的路徑。新判準若比祖先關係弱，後果是刪掉未合併的分支且不可復原。查核重點在新判準能不能拒絕「內容不在 main」的分支，而非只確認它接受了 squash 的情形。須跨家族。）
- Initiative：—　spec 基線：docs/ROADMAP.md（main 36b3f07）§3.5 squash 裁定與 §0 目標 1。WF-CLEANUP-GUARD1（#25）的守衛已通過跨家族查核並在 2026-08-13 真實使用過三次（#53、#43、#24），本卡不得放寬其保護強度。需求方 2026-08-13 裁定採 (A) 給守衛一條 squash 感知的驗證，而非改回 merge 合併或手動清理。⚠️ 依 ROADMAP §5，本卡的開立是需求方的排程裁定，不是因為衝突存在就開。
- DB：db_scope=none
- 服務的原始目標：讓 squash 合併的卡也能經守衛收尾，而不是繞過守衛手動清理

## 簡介
<!-- card-brief:begin -->
讓收尾守衛認得 squash 合併：ROADMAP §3.5 裁定卡片一律 squash 後，分支 tip 永遠不會是 main 的祖先，以 merge-base --is-ancestor 驗證的守衛遂對之後每一張卡恆拒（當日四張已合併的卡三張被擋），而收尾是唯一會刪 worktree 與分支的路徑。交付 content_absorbed 判準，並做授權分流：squash 只授權移除 worktree，刪本地與遠端分支仍需 ancestor。**適用時機**：要改 cleanup 的「內容已在 main」判準時；或收尾被 merge_verified_local／merge_verified_remote 擋下要查原因時。⛔ 非射程：不放寬 WF-CLEANUP-GUARD1（aiwf#25）其餘九項前提與它們之間的 AND 結構；不代當日被擋的 aiwf#9／#63／#73 執行收尾，只證明新判準對它們回 allow。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：2026-08-13 兩條裁定互相打架，且是同日作出的。ROADMAP §3.5 裁定卡片一律以 squash 合併——理由是 GitHub merge 按鈕產不出 Reviewed-by，界線跨過後每次按鈕合併都是 DEV-COMMIT-TRAILER-GUARD1 檢查器的違規。而 WF-CLEANUP-GUARD1（#25）的收尾守衛以 merge-base --is-ancestor 驗證「分支已併入 main」，squash 產生的是一筆全新 commit、分支 tip 永遠不會是 main 的祖先。實測：當日四張已 APPROVE 並合併的卡跑 handoff --next-stage release --cleanup，三張被擋（阻擋碼 merge_verified_local 與 merge_verified_remote），唯一通過的 #48 是當日唯一用 --merge 合併的（PR #69，在 §3.5 裁定之前）。⚠️ 守衛沒有擋錯——它驗的是「這個分支的內容真的在 main 上嗎」，而 squash 之後那個答案在 git 拓撲上確實是「不知道」。⚠️ 這不是那三張的特例：§3.5 生效後【之後每一張卡的收尾都會被恆拒】，而收尾是唯一會刪 worktree 與分支的路徑，恆拒的後果是 worktree 與分支無限累積、且卡停在 ✅通過 無法進終態。PM 在寫 §3.5 時只想到「被審 SHA 不出現在 main 歷史上」這個代價，沒想到它會讓收尾守衛失效。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/cleanup.py",
    "file:cli/tests/test_cleanup.py",
    "file:cli/src/wf_cli/commands/handoff_cmd.py",
    "file:cli/src/wf_cli/doctor.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] ⚠️【射程，需求方 2026-08-13 二次裁定 issuecomment-5275084185】判準只授權【移除 worktree】。刪除本地與遠端分支的授權一律仍需 ancestor——兩種合併方式因此都有正確的保護：merge 走 ancestor 可全收尾，squash 走 content_absorbed 只收 worktree。交付報告須指出授權分流在哪一行碼。⚠️ 卡面【核心痛點欄的文字仍是舊版】（同時要求「支援 squash」與「不得比祖先關係弱」，那是 PM 寫的自相矛盾）——amend --core-pain 需核對需求方身分，而本卡開卡時「需求」欄漏填為 —、amend 無 --requested-by 旗標可補，故核心痛點改不了。【以本條與該則裁定留言為準】。
- [ ] ⚠️ 必須能拒絕「內容不在 main」的分支。以突變證明：拿一個確實未合併的分支跑收尾，新判準須擋下並附輸出。【只證明它接受 squash 的情形不算】——本卡碰的是唯一會刪除工作內容的路徑。
- [ ] 保留既有 merge 合併的路徑仍然可用（#48 即以 --merge 合併並成功全收尾）。新舊判準的關係須明確，且【授權範圍的差異須在碼與文件兩處都看得到】。
- [ ] ⚠️ 不得放寬 WF-CLEANUP-GUARD1 的其餘前提（工作區乾淨、遠端 tip 與本地一致、租約比對、illegal_terminal_before_cleanup 分類等九項與它們之間的 AND 結構）。交付報告須確認未動。
- [ ] ⚠️ R1 已交付的判準本體【全部保留】：A∩B=∅、--no-renames、11 格矩陣、merge-tree 獨立神諭、兩個突變。【三種誤放行的自陳一字不刪】——它們在新授權下的後果從「不可逆刪除」降為「worktree 被移除而分支仍在」，但它們仍然是誤放行、仍該被讀到。
- [ ] 當日三張被擋的卡（#9、#63、#73）須能以新判準移除 worktree。本卡【不代它們執行收尾】，只需證明新判準對它們回 allow 並附三張各自的判定輸出。

## 驗證

- [ ] cd cli && uv run pytest -q 不得退化（基線自己跑）。
- [ ] 以突變注入證明新判準有鑑別力：讓它對未合併分支誤放行，測試須轉紅並附輸出。
- [ ] 凡寫下「內容已在 main」須指出證明它的是哪一行碼；沒有機械執行者的寫成約定。
## Log

- 2026-08-13T08:47:55+08:00 open by —；owner 待指派；iteration 0。
- 2026-08-13T08:49:23+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code 子agent；分支worktree claude/WF-CLEANUP-SQUASH-AWARE1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cleanup-squash-aware1；交付狀態 🚧進行中；實際能力層級 主力型（與卡面建議 主力型 相符）。
- 2026-08-13T09:36:46+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA 7b52d31669b8e50824ee07cc7ec15ab146a02d5f；證據 R1：⚠️ 被審 SHA 為 7b52d31（gh pr update-branch 產生的 merge commit，parents = d36f9648 + 52839f0d），不是執行者報告裡的 d36f9648——遠端 tip 與 worktree HEAD 都已是它，那才是查核者 git rev-parse HEAD 會拿到的、也才是實際會被 squash 進 main 的內容；d36f9648 是它的祖先、trailer 3/3，而 7b52d31 trailer 0/3（GitHub API 產生的 merge commit 產不出 trailer，同 merge 按鈕），依 ROADMAP §3.5 squash 會把它壓掉不落 main。判準：令 base=merge-base(tip,main)，A=分支相對 base 改動過的路徑、B=與 main 仍有差異的路徑，內容已吸收 ⟺ A∩B=∅。⚠️ 執行者原本選 tree hash 比對，在真實資料上失敗——本地 ref 從未被 gh pr update-branch 更新過（那是伺服器端做的），三張卡的 local 檢查全部誤拒，它據此換掉。四個候選各自的誤放行情境它都找出來，其中 git cherry/patch-id 那個最尖銳：patch 被 apply 後又 revert，patch-id 仍算「在 main 上」而內容其實已不在。--no-renames 是正確性所需並附實測（改名格在 --find-renames 下誤放行）；它並主動更正自己 docstring 裡把 -z 也寫成正確性關鍵是錯的。新舊判準關係為 OR、風險全落在新的那條；守衛其餘九項前提與 AND 結構一行未動（已用 diff 機械確認）。⚠️ 正面回答「什麼時候會刪掉不該刪的東西」為三種而非「不會」，第三種它自標最嚴重：中間 commit 才有的內容（分支第 1 筆新增、第 3 筆刪除，tip 沒有 main 也沒有）刪掉就拿不回來——該損失是 squash 造成的，但【是本判準讓那個不可逆刪除得以發生】，這是它比祖先關係弱的真正所在。取證：三張被擋的卡 local+remote 六項全 pass（content_absorbed，吸收路徑數 8/5/1）；未合併分支被擋是用它自己的 PR 分支測的（非沙箱），輸出逐字列出三個路徑並說「這些內容不在 main 上，刪掉分支就沒了」；突變 M1（判準恆回 content_absorbed）18 紅、M2（--no-renames→--find-renames）精準命中改名格。測試新增 28 條，含 11 格判準矩陣跑真 git ＋ 同 11 格以 git merge-tree --write-tree 當獨立神諭交叉比對。PM 自審：d36f9648 是 7b52d31 祖先、對 main merge-tree CLEAN、寫入集兩檔零逸出、合併樹實跑 865 passed。⚠️ PM 已將 PR #80 轉為 draft——執行者開 PR 無違規（派工詞禁 merge 沒禁開 PR）且換到了真實取證，但一個 CLEAN 隨時可合併的 PR 會讓「查核先於合併」變成靠人記得；此為 PM 的派工詞缺口。⚠️ 執行者順帶發現（未改）：_execute_closeout 用 git branch -d 當第二道防線，實測對已 push 且與 upstream 一致的分支恆過——本專案所有卡分支都是這樣，那條防線一直是空的。⚠️ 它自陳五項證明不了的，其中「內容撞號與淨零兩種誤放行只論證了檔案內容零損失、沒證明 commit 紀錄的損失可接受——那是需求方的判斷」須查核者知悉。。
- 2026-08-13T10:03:52+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5275050968 未經編輯，PM 依其取材規則（core_pain_resolved 起至 EOF）回讀重算相符；core_pain_resolved no；self_run 5 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-CLEANUP-SQUASH-AWARE1-e0-7b52d31669b8e50824ee07cc7ec15ab146a02d5f。
- 2026-08-13T10:10:53+08:00 amend by wf-cli（op 6c12b7da）→ 驗收條件：原值「[ ] 裁定「內容已在 main」在 squash 之後該用什麼證明。⚠️ 判準：新證明【不得比 merge-base --is-ancestor 弱】。祖先關係證明的是「這些 commit 就在 main 的歷史裡」；任何替代品須說明它證明了什麼、以及它在什麼情況下會誤放行。候選（不限於此，執行者自行論證）：比對 tree hash、驗 GitHub PR 的 merged 狀態與 merge_commit_sha、比對 diff 為空。；[ ] ⚠️ 必須能拒絕「內容不在 main」的分支。以突變證明：拿一個確實未合併的分支跑收尾，新判準須擋下並附輸出。【只證明它接受 squash 的情形不算】——那是單向測試，而本卡碰的是唯一會刪除工作內容的路徑。；[ ] 保留既有 merge 合併的路徑仍然可用（#48 即以 --merge 合併並成功收尾）。新舊兩條判準的關係須明確：擇一即可、還是都要？誤放行的風險落在哪一條？；[ ] ⚠️ 不得放寬 WF-CLEANUP-GUARD1 的其餘前提。該守衛的其他檢查（工作區乾淨、遠端 tip 與本地一致、租約比對、illegal_terminal_before_cleanup 分類）與本卡無關，一律不動。交付報告須確認未動。；[ ] 當日三張被擋的卡（#9、#63、#73）須能以新判準收尾。⚠️ 本卡【不代它們執行收尾】——那是 PM 的操作；本卡只需證明新判準對它們回 allow，並附三張各自的判定輸出。」→ 新值「⚠️【射程，需求方 2026-08-13 二次裁定 issuecomment-5275084185】判準只授權【移除 worktree】。刪除本地與遠端分支的授權一律仍需 ancestor——兩種合併方式因此都有正確的保護：merge 走 ancestor 可全收尾，squash 走 content_absorbed 只收 worktree。交付報告須指出授權分流在哪一行碼。⚠️ 卡面【核心痛點欄的文字仍是舊版】（同時要求「支援 squash」與「不得比祖先關係弱」，那是 PM 寫的自相矛盾）——amend --core-pain 需核對需求方身分，而本卡開卡時「需求」欄漏填為 —、amend 無 --requested-by 旗標可補，故核心痛點改不了。【以本條與該則裁定留言為準】。；⚠️ 必須能拒絕「內容不在 main」的分支。以突變證明：拿一個確實未合併的分支跑收尾，新判準須擋下並附輸出。【只證明它接受 squash 的情形不算】——本卡碰的是唯一會刪除工作內容的路徑。；保留既有 merge 合併的路徑仍然可用（#48 即以 --merge 合併並成功全收尾）。新舊判準的關係須明確，且【授權範圍的差異須在碼與文件兩處都看得到】。；⚠️ 不得放寬 WF-CLEANUP-GUARD1 的其餘前提（工作區乾淨、遠端 tip 與本地一致、租約比對、illegal_terminal_before_cleanup 分類等九項與它們之間的 AND 結構）。交付報告須確認未動。；⚠️ R1 已交付的判準本體【全部保留】：A∩B=∅、--no-renames、11 格矩陣、merge-tree 獨立神諭、兩個突變。【三種誤放行的自陳一字不刪】——它們在新授權下的後果從「不可逆刪除」降為「worktree 被移除而分支仍在」，但它們仍然是誤放行、仍該被讀到。；當日三張被擋的卡（#9、#63、#73）須能以新判準移除 worktree。本卡【不代它們執行收尾】，只需證明新判準對它們回 allow 並附三張各自的判定輸出。」；理由 R1-01（blocking，core_pain_resolved: no）：查核者指出新判準只驗 tip 快照，中間 commit 曾有而 tip 已刪除的內容仍會被放行後刪除且 main 無法回復，直接違反卡面第一條「不得比祖先關係弱」。需求方 2026-08-13 裁定（issuecomment-5275084185）該矛盾是 PM 寫在卡面上的——squash 本質上就會丟掉中間 commit 的內容，任何內容判準對那一格必然較弱，而祖先關係在 squash 後永遠不成立，兩條要求互斥。處置：收尾只移除 worktree、不刪分支——不做不可逆的那一步，不必放寬守衛也不必推翻 §3.5。⚠️ 本次只改驗收未改核心痛點：amend --core-pain 需核對需求方身分，而本卡開卡時「需求」欄漏填為 —（今日新開的 #65／#66／#73／#78 皆然），amend 無 --requested-by 旗標可補。需求方 2026-08-13 裁定採 (C)：不改核心痛點、以驗收與裁定留言為準，該落差記為已知限制。attribution: coordinator——同一形狀第四次（#57 三次、本卡一次）：PM 要一個結構上拿不到的東西。。
- 2026-08-13T10:11:15+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 1；SHA 7b52d31669b8e50824ee07cc7ec15ab146a02d5f；證據 R1-01（blocking）：需求方裁定收尾只移除 worktree、不刪分支（issuecomment-5275084185），驗收五條已重寫（amend 見 Log）。⚠️ 核心痛點欄的文字仍是舊版且改不了——amend --core-pain 需核對需求方身分而本卡「需求」欄開卡時漏填為 —，amend 無 --requested-by 旗標；以驗收與裁定留言為準。R1 的判準本體全部保留，只改授權範圍。PR #80 已由 PM 轉為 draft。。
- 2026-08-13T10:34:10+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 1；SHA 8efc1d2021ca6fe39d0f630eedf44bd1c94482d5；證據 R2：R1-01 已處置。需求方 2026-08-13 裁定收尾只移除 worktree、不刪分支（issuecomment-5275084185），驗收已改寫為授權分流（amend op 6c12b7da）。⚠️ 設計轉折：分界不是「強證明／弱證明」而是【可逆／不可逆】。授權表 AUTHORITY_BY_PROOF 在 cleanup.py:359-364，一個 proof kind 一列——ancestor 授權三個動作、content_absorbed 只授權 remove_worktree、diverged 與 unobservable 空集合；GuardDecision.authorized_actions（:392）取本地與遠端兩份證明的交集以最弱者為準，讀不到即 NO_AUTHORITY（:367）fail-closed；三個破壞性動作各自的閘門在 :1362／:1377／:1398。⚠️ 它以一組【對照突變】證明安全性不再依賴判準正確：同一條確實未合併的分支，判準被完全攻破時——突變成 content_absorbed 則 worktree 移除而本地與遠端分支都存活、突變成 ancestor 則分支被刪光。「判準被攻破仍沒有不可逆遺失，靠的是授權表不是判準。」四個突變：M1 判準恆回 content_absorbed → 38 紅（R1 時 18）、M2 --no-renames→--find-renames 2 紅、M3 給 content_absorbed 刪分支權 → 4 紅（直接打在推翻裁定的那一行）、M4 observe 忽略授權範圍 → 1 紅。三張卡授權交集皆 [remove_worktree]、刪分支獲授權 False。未合併分支仍被擋（真實、本 PR 自己的分支，proof_kind=diverged、授權交集空）。R1 判準本體全部保留、三種誤放行自陳保留並更新後果描述。⚠️ 正面回答「新授權下還有沒有不可逆遺失」為【有一條且未收窄】：ancestor 誤判（main_ref 被 force push 改寫）仍會刪未合併分支——但那是舊判準本來就有的，本卡沒加寬也沒收窄；經由 content_absorbed 則沒有不可逆遺失。⚠️⚠️ 它另帶回一個會動搖整個裁定前提的發現並誠實標為未處理：git worktree remove 的可逆性有前提——守衛的 no_uncommitted_changes 覆蓋未提交與未追蹤檔，但【被 .gitignore 忽略的檔案不在 git status --porcelain 預設輸出裡】（build/、.env、node_modules/），worktree remove 會連它們一起刪且無從還原。那是既有守衛的邊界非本卡引入，但整個裁定的安全論證就架在「移除 worktree 是可逆的」上面。它建議另開卡。PM 自審：遠端 tip 相符、7b52d31 是祖先（非 force）、對 main merge-tree CLEAN、寫入集兩檔零逸出、授權表逐字複驗與報告一致。⚠️ 它自陳最想請查核者盯的一處：控制流順序改了——守衛評估移到觀測之前（守衛唯讀；擋下時觀測範圍退回全集，故 detect_only 分類逐字相同）。另 _BODY_ALLOWED_GLOBALS 新增兩個名字，該清單設計本意是「漏一個只是轉紅、要有人回來複核」，而這次複核的是它自己。⚠️ trailer：它的兩筆真實 commit 皆合規，那 1 筆違規是 7b52d31（gh pr update-branch 產生的 merge commit）缺 Reviewed-by——正是 ROADMAP §3.5 明寫「squash 會把它壓掉、不落 main」的那一類。PR #80 仍為 draft、它未動狀態。。
- 2026-08-13T10:56:23+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5275366866 未經編輯，PM 依其取材規則（core_pain_resolved 起至 EOF）回讀重算相符；core_pain_resolved no；self_run 4 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-CLEANUP-SQUASH-AWARE1-e0-8efc1d2021ca6fe39d0f630eedf44bd1c94482d5。
- 2026-08-13T10:56:42+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 2；SHA 8efc1d2021ca6fe39d0f630eedf44bd1c94482d5；證據 R2-01（blocking）：squash 路徑只移除 worktree 並保留分支，但【終態留痕仍宣稱本地／遠端分支「皆已不存在」】——造成可稽核內容失真。查核者在隔離 repo 重現該錯誤語意，並確認 R1 blocking 已閉環、869 個測試 100% 完成、未修改被審 worktree、未變更 PR 狀態。⚠️ 這是 ROADMAP §0 目標 2（可稽核的內容：事後能從留痕重建做了什麼）的直接違反——授權分流改了行為卻沒改留痕的措辭，於是留痕描述的是舊行為。修法方向：終態與相關訊息須據【實際執行的動作集合】產生，而非固定字串； 已有該資訊。⚠️ 執行者須確認凡宣稱「已刪除」之處都改為據實敘述，含 Log 索引行、stderr、以及 doctor／snapshot 若有讀取該敘述之處。。
- 2026-08-13T11:19:49+08:00 amend by wf-cli（op e6456d0a）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/cleanup.py", "file:cli/tests/test_cleanup.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/cleanup.py、file:cli/tests/test_cleanup.py、file:cli/src/wf_cli/commands/handoff_cmd.py、file:cli/src/wf_cli/doctor.py」；理由 補宣告 handoff_cmd.py 與 doctor.py。R2-01 要求「凡宣稱『已刪除』之處都改為據實敘述」，而【留痕的產生點與消費端本來就不在 cleanup.py 內】——終態字串由 handoff_cmd.py:392 寫入、Log 索引行在 :314 內插同一個值、doctor 的收尾預覽 verdict 也印同類敘述。開卡時 PM 只宣告了判準所在的檔，沒有把留痕的消費端算進去，那是 planner 的疏漏。執行者主動報備逸出並請 PM 補宣告或裁定——該報備是對的，PM 補宣告而非退回。⚠️ 互斥檢查：兩檔目前無其他活卡宣告（#30 WF-MARKER-SCOPE-CLEARANCE1 宣告 doctor.py 但為 Backlog、owner 待指派，依 assign_cmd.py:118-124「未認領的卡其資源宣告不保留資源」故不成立）。。
- 2026-08-13T11:20:18+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 2；SHA 64f1a0cd5526ce66041bbc1066060d0e28053bd9；證據 R3：R2-01 已處置。留痕的唯一產生點改為 cleanup.py 的 describe_cleanup()，輸入是 executor 在 :1544 現場組出的 CleanupOutcome（那一輪實際做過什麼），措辭字詞唯一來源是 ACTION_LABELS；終態與 Log 索引行是同一個 cleanup_note、一次修正兩處。掃到並改掉九處（不只查核者列的四處），並列出三處掃到但確認無須改的（doctor 孤兒分支預測本來就以 is_ancestor 判定與新標準一致、NO_CLEANUP_WARNING 恆真、reconcile 側尚未接線無第二消費端）。前後對照：squash 路徑舊為「worktree 與本地／遠端分支皆已不存在」（即 R2-01），新為「已清除 worktree；本地分支、遠端分支 依授權保留（未刪除）」。突變 M5（describe_cleanup 退回固定字串）5 紅、M6（executor 不傳 outcome）2 紅，前輪 M1-M4 仍 38/2/4/1。新增 6 條測試合計 875，含全分割窮舉（4的3次方=64 種指派、每個標籤恰好出現 1 次）與 AST 掃描禁止可輸出的固定刪除宣稱。⚠️ 正面回答「還有沒有留痕描述沒發生的動作或漏掉發生了的」：在 describe_cleanup 射程內【沒有，且是結構性的】——三個動作對五個桶構成完整分割，unaccounted 兜住所有沒落到前四格的，「漏講」在該函式裡寫不出來。但射程外仍有三處未關：(1) mode != applied 時終態根本不寫，而 aborted 模式已經移除了 worktree、效果被扣住，卡片上不會有任何記載、只有 stderr，而 stderr 不是留痕——這是「發生了的動作漏掉」的真實案例且在 R2 之前就存在，修它要動「效果扣住」那條規則、超出本卡，它建議另開卡；(2) 留痕描述的是 executor 送出了哪些指令而非遠端現在真的長怎樣，push --delete 回 0 之後遠端仍可能因受保護分支或鏡像同步而留著，覆核只擋住終態寫入不修正敘述；(3) docs/WF_CLEANUP_GUARD1.md 與 docs/WF_EVENT_IDEMPOTENCY1.md 共四處仍把收尾寫成「移除 worktree、刪本地與遠端分支」，對 squash 路徑已不成立——它未改，因那是 #25／#41 的 canonical 設計文件、不在其資源宣告內，請 PM 裁定。PM 自審：8efc1d2 是祖先（非 force）、對 main merge-tree CLEAN、合併樹實跑 875 passed。⚠️ 寫入集逸出：宣告兩檔而實際四檔，多出的 handoff_cmd.py 與 doctor.py 正是查核者指名的留痕消費端；【執行者主動報備並請 PM 補宣告或裁定】，PM 已補宣告（amend 見 Log）而非退回——開卡時只宣告判準所在的檔、沒把留痕消費端算進去是 planner 疏漏。⚠️ 它另報 worktree 計數由 21 變 20，已逐一核對所有註冊 worktree 與 17 個卡分支 worktree 全數健在、差額落在 /private/tmp 下別的 session 的臨時工作區，其驗證腳本內 0 處 worktree remove/prune，但它無法證明是哪一個何時消失的——只能證明不是它、且無工作內容遺失。。
- 2026-08-13T11:38:55+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5275651849 未經編輯，PM 依其取材規則回讀重算相符；core_pain_resolved yes；self_run 5 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-CLEANUP-SQUASH-AWARE1-e0-64f1a0cd5526ce66041bbc1066060d0e28053bd9。
- 2026-08-13T11:43:45+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 3；SHA 64f1a0cd5526ce66041bbc1066060d0e28053bd9；證據 R3-01（blocking）：aborted 路徑已移除部分資源，卻只寫 stderr、不留 Issue Log，因此事後無法重建實際動作。查核者確認 R2-01 已閉環、四檔改動皆在射程內未見夾帶、875 項全通過。⚠️ PM 裁定【在卡內窄修，不縮射程】：依 ROADMAP §4 判準「它會不會讓留痕重建不出來——會 → 不是細節」，aborted 模式已經移除了 worktree 而卡片上一個字都沒有，那正是該判準的字面情況，故查核者判 blocking 是對的。⚠️ 執行者上一輪把它標為「超出本卡、修它要動效果扣住那條規則」——PM 判定該劃界過寬：handoff_cmd.py:414 的 mode != applied 是【整個不寫狀態面】，而問題只在於「該不該留一筆做過什麼的紀錄」。【寫一筆 Log 記錄不等於寫終態】，效果扣住那條規則可以完全不動。修法方向：mode != applied 時仍寫 Log 索引行（用同一個 describe_cleanup(outcome)），但不寫終態、不關 Issue。三個理由：不動效果扣住；用 R3 剛做好的既有產生點；aborted 的資訊已在資料結構裡（outcome.aborted，:186 已經在印 stderr）。⚠️ 這與 R2-01 是同一病灶的第二半——R2-01 是「敘述與行為不同源」，本項是「行為發生了但沒有敘述」，兩者都是留痕與行為脫節，分開處理反而不自然。R1/R2/R3 的判準本體、授權表、describe_cleanup 全部保留。。
- 2026-08-13T14:31:45+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex）；iteration 3；SHA e36f592178ee54a1db0b8260ab09a4c8f7a9662f；證據 第四輪交付 e36f592（64f1a0c..e36f592，兩檔 +274/-9，全在 cli/）。修 R3-01：抽出 append_card_log 使 Log 附加與欄位寫入解耦，新增 _record_actions_without_terminal 在「本次真的動了東西、終態卻沒寫」時附加一行明確非終態的紀錄；敘述走 describe_cleanup（與終態留痕同一產生點）、第 4 步走 effect_calls、阻擋原因走 blocking_reasons。⚠️ 執行者未照 PM 字面的 mode != applied，改讀動作集合（outcome.performed or outcome.aborted），並以突變實測證明字面版兩邊都錯：applied 但效果被扣住那一格會漏（worktree 與本地分支已不在、終態同樣沒寫，即查核者 R3 self_run 重現過的那格），而 detect_only 恆為零動作、按 mode 分流會讓每次被擋的重跑都疊噪音。PM 核可此偏離：它蓋得比字面版準，且是 R2「不要從 mode 推論做了什麼」的直接套用。⚠️ 效果扣住規則未被動到：新函式收 effect_calls 名稱序列而非 writer（機械上發不出第 4 步），不呼叫 set_field_value、不關 Issue，:414 的 mode != applied 分支與所有 return 碼原封不動。PM 已獨立重跑 uv run pytest -q 得 879 passed（R3 基準 875，+4），並核對 e36f592 已推到 origin、新路徑無 set_field_value 呼叫。⚠️ 執行者主動標記兩處待判：(1) write_status_face 這個函式名同時涵蓋欄位與 Log，若採「Log 屬狀態面」的讀法可能被判仍寫了狀態面（未改名，超出射程）；(2) item.body 是快照，兩個 Log 消費者以「終態已寫就不再記」互斥，單一 run 內不覆蓋，但跨 run 並行寫入本就無保護、非本輪引入。。
- 2026-08-13T15:04:40+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex 子代理（需求方轉貼）；core_pain_resolved yes；self_run 7 項；findings 1 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-CLEANUP-SQUASH-AWARE1-e0-e36f592178ee54a1db0b8260ab09a4c8f7a9662f。
- 2026-08-13T15:08:04+08:00 handoff by wf-cli → owner ruan6047；iteration 3；SHA e36f592178ee54a1db0b8260ab09a4c8f7a9662f；證據 四輪跨家族查核末輪 APPROVE（blocking 零、879 項通過），需求方授權後以 squash 合併入 main = af01307，PR #80。merge body 未含 Closes 以免自動關 Issue 觸發 illegal_terminal_before_cleanup。本次收尾即本卡所修機制的首次實戰：squash 不產生祖先關係，預期走 content_absorbed 證據並僅授權 remove_worktree。首次執行時因主 checkout 的 local main 尚未快進而仍跑到舊碼、被舊判準擋下（detect_only，零動作、未寫狀態面），快進至 af01307 後重跑。；收尾清理：已清除 worktree；本地分支、遠端分支 依授權保留（未刪除）。
- 2026-08-26T22:03:29+08:00 amend by wf-cli（op 1a1d50aa）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:0982bd117e4838c6561d7ba05c108364eb11738fe01d46ab6ce18881570486a7 (790 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5275050968 · 2026-08-13T02:02:21Z

<!-- wf-review-receipt:v1
card_id: WF-CLEANUP-SQUASH-AWARE1
source_sha: 7b52d31669b8e50824ee07cc7ec15ab146a02d5f
report_sha256: 8698cad583d6d076f5ad433fa19e2e2ec8fe48f4a9ceb35c81cebce3682aa88d
-->

core_pain_resolved: no
review_result: REQUEST_CHANGES
prior_accepted_blocking_findings:
  - status: "首輪，無前輪 accepted blocking finding"
self_run:
  - command: "git rev-parse HEAD；Issue Log 最後 handoff SHA 比對"
    observed: "兩者皆為 7b52d31669b8e50824ee07cc7ec15ab146a02d5f"
  - command: "cd cli && uv run pytest tests/test_cleanup.py"
    observed: "105 tests，exit 0"
  - command: "cd cli && uv run pytest -q；uv run ruff check src/wf_cli/cleanup.py tests/test_cleanup.py；git diff --check 基線..被審 SHA"
    observed: "三者皆 exit 0"
  - command: "拋棄式 /tmp repo：分支提交 intermediate.txt 後刪除，呼叫 prove_content_in_main(card, main)"
    observed: "proof=content_absorbed，outcome=pass；git merge-base --is-ancestor card~1 main exit 1；main..card 含 intermediate"
  - command: "git diff 與 CHECK_IDS/evaluate_cleanup_guard 比對基線"
    observed: "其餘九項前提與 all(pass) AND 聚合未動；僅兩個 merge_verified 檢查及刪除前複驗改為共用新證明"
findings:
  - finding_id: "WF-CLEANUP-SQUASH-AWARE1-R1-001"
    severity: critical
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: "tip-snapshot-omits-intermediate-commits"
    evidence: "prove_content_in_main 只比較 base..tip 的淨路徑集合；在 /tmp/wf-cleanup-review.A2Hw7W，card 的第一筆提交新增 intermediate.txt、第二筆提交刪除它，函式仍回 content_absorbed/pass，但 main 不可達 card~1。刪除 card 後該內容僅剩可被 GC 回收的無參照物件。"
    disposition: "不得以 tip 快照吸收作為刪除分支的放行證明。修正判準或改成 fail-closed，必須保住分支所有非 main 可達的中間提交內容，並新增此案例的端到端拒絕測試。"

## Comment 5275060386 · 2026-08-13T02:03:53Z

<!-- wf-review-event:v1 card_id=WF-CLEANUP-SQUASH-AWARE1 source_sha=7b52d31669b8e50824ee07cc7ec15ab146a02d5f attempt_id=WF-CLEANUP-SQUASH-AWARE1-e0-7b52d31669b8e50824ee07cc7ec15ab146a02d5f -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CLEANUP-SQUASH-AWARE1`　attempt_id：`WF-CLEANUP-SQUASH-AWARE1-e0-7b52d31669b8e50824ee07cc7ec15ab146a02d5f`
- 查核者：GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5275050968 未經編輯，PM 依其取材規則（core_pain_resolved 起至 EOF）回讀重算相符　escalation_epoch：0
- source_sha：`7b52d31669b8e50824ee07cc7ec15ab146a02d5f`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-13T10:03:52+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD；Issue Log 最後 handoff SHA 比對`
  - 兩者皆為 7b52d31669b8e50824ee07cc7ec15ab146a02d5f
- `cd cli && uv run pytest tests/test_cleanup.py`
  - 105 tests，exit 0
- `cd cli && uv run pytest -q；uv run ruff check src/wf_cli/cleanup.py tests/test_cleanup.py；git diff --check 基線..被審 SHA`
  - 三者皆 exit 0
- `拋棄式 /tmp repo：分支提交 intermediate.txt 後刪除，呼叫 prove_content_in_main(card, main)`
  - proof=content_absorbed，outcome=pass；git merge-base --is-ancestor card~1 main exit 1；main..card 含 intermediate
- `git diff 與 CHECK_IDS/evaluate_cleanup_guard 比對基線`
  - 其餘九項前提與 all(pass) AND 聚合未動；僅兩個 merge_verified 檢查及刪除前複驗改為共用新證明

### findings（1，其中 blocking 1）

- **WF-CLEANUP-SQUASH-AWARE1-R1-001**　severity=critical　blocking=true　class=implementation　attribution=executor　root_cause_id=`tip-snapshot-omits-intermediate-commits`
  - evidence：prove_content_in_main 只比較 base..tip 的淨路徑集合；在 /tmp/wf-cleanup-review.A2Hw7W，card 的第一筆提交新增 intermediate.txt、第二筆提交刪除它，函式仍回 content_absorbed/pass，但 main 不可達 card~1。刪除 card 後該內容僅剩可被 GC 回收的無參照物件。
  - disposition：不得以 tip 快照吸收作為刪除分支的放行證明。修正判準或改成 fail-closed，必須保住分支所有非 main 可達的中間提交內容，並新增此案例的端到端拒絕測試。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-CLEANUP-SQUASH-AWARE1-e0-7b52d31669b8e50824ee07cc7ec15ab146a02d5f
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: no
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: "跨家族查核（GPT-5@Codex 子代理）"
findings:
  - finding_id: WF-CLEANUP-SQUASH-AWARE1-R1-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: tip-snapshot-omits-intermediate-commits
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5275084185 · 2026-08-13T02:07:43Z

## 需求方裁定（2026-08-13）：squash 合併的卡，收尾只刪 worktree、不刪分支

> ⚠️ 內容由需求方 `ruan6047` 明確核准，**文字由 PM 代擬並代貼**（角色：PM 代擬／需求方核可，`docs/ROADMAP.md` §1）。

### 先認一件事：本卡的卡面自相矛盾，那是 PM 寫的

卡面第一條驗收要求「**新證明不得比 `merge-base --is-ancestor` 弱**」，同時卡的目的是**讓 squash 合併的卡也能收尾**。

**這兩條不可能同時滿足**：

- squash **在本質上就會丟掉中間 commit 的內容**——main 上永遠不會有它
- 因此**任何**基於「內容是否在 main 上」的判準，對那一格**必然**比祖先關係弱
- 而**祖先關係在 squash 之後永遠不成立**

**PM 在卡面上同時要了兩個互斥的東西。** 查核者判 blocking 是對的，執行者做到了能做的極限也是對的——**不存在的東西沒有人做得出來**。

執行者其實已經把話說清楚了，是 PM 的驗收只問了後半：

> 這份損失**是 squash 造成的**，但**是本判準讓那個不可逆刪除得以發生**。

### 裁定

**收尾對 squash 合併的卡只移除 worktree，不刪除本地與遠端分支。**

### 理由

**唯一不需要放寬任何保護、也不需要推翻任何裁定的做法。** 不可逆的那個動作（刪分支）就不做；可逆的（移除 worktree）照做。

- **中間 commit 的內容留在分支上**，`merge-base --is-ancestor` 那一格要保護的東西不再有失去的可能
- **不必放寬守衛**：`A ∩ B = ∅` 這個判準仍然可用，只是它的授權範圍縮成「可以移除 worktree」
- **不必推翻 §3.5**：squash 仍是卡片的合併方式
- **代價是分支無限累積**——那是噪音，**而噪音比不可逆的資料遺失便宜**

**這也解釋了為什麼 `git branch -d` 那道防線是空的卻無所謂**（執行者順帶發現：對已 push 且與 upstream 一致的分支恆過）——**因為根本不該走到刪分支那一步。**

### 因此須修改的

- **核心痛點**：本卡的目的改為「讓 squash 合併的卡能移除 worktree」，明寫**不含刪除分支**
- **驗收第一條**：「不得比祖先關係弱」改為——**判準只授權移除 worktree；刪除分支的授權一律仍需 `ancestor`**。兩種合併方式因此都有正確的保護：merge 走 `ancestor` 可全收尾，squash 走 `content_absorbed` 只收 worktree
- 交付文件與 `cleanup.py` 中凡把 `content_absorbed` 當成「可以刪分支」之處，改為「可以移除 worktree」

### 明確保留

執行者已交付的判準本身（`A ∩ B = ∅`、`--no-renames`、11 格矩陣、`merge-tree` 獨立神諭、兩個突變）**全部保留**——它們仍然是「內容是否在 main 上」的正確判定，只是授權範圍改了。

**三種誤放行的自陳一字不刪**：它們在新授權下的後果從「不可逆刪除」降為「worktree 被移除而分支仍在」，**但它們仍然是誤放行，仍該被讀到**。

### 分支累積的處置

**本裁定不處理它。** 依 §5，那要等它真的造成問題才排——而它是可逆的、可事後批次清理的。`doctor` 的孤兒分支清單已經在列它們。

### PM 的帳

**這是同一形狀第四次**：#57 三次、#78 一次。**PM 要一個結構上拿不到的東西，執行者做到能做的極限，查核者正確地指出那不是 PM 要的。**

`attribution: coordinator`。


## Comment 5275270916 · 2026-08-13T02:36:23Z

## PM 更正：那個 `.gitignore` 發現的實際規模，比 PM 在 handoff evidence 裡寫的小很多

本卡最後一筆 `handoff` 的 evidence 裡，PM 把執行者的自陳寫成：

> ⚠️⚠️ 它另帶回一個**會動搖整個裁定前提**的發現……

**那個措辭是 PM 加的，不是執行者說的。** 執行者的原話是「那是**既有守衛的邊界、不是本卡引入的**」，並建議另開卡。**是 PM 把它升級了。**

### 需求方問了一句，然後 PM 去查了

> 確認價值。如果是沒有意義或錯誤的內容，刪掉其實沒差。

實測本 repo 全部 22 個 worktree 的 `.gitignore` 忽略檔：

```
.ruff_cache/   cli/.pytest_cache/   cli/.ruff_cache/   cli/.venv/
cli/src/wf_cli/__pycache__/   cli/src/wf_cli/commands/__pycache__/   cli/tests/__pycache__/

總計 11,728 KB（約 11.7 MB）
```

**全部可重新產生**（`uv sync` 一行就回來）。

`find` 全部 worktree 找 `.env*`／`*.key`／`*credential*` → **零命中**。

**執行者舉的 `build/`、`.env`、`node_modules/` 在本 repo 一個都不存在。**

### 更正後的判斷

**機制屬實**——`.gitignore` 的檔案確實不在 `git status --porcelain` 預設輸出裡，`worktree remove` 確實會連它們一起刪。

**但依 `docs/ROADMAP.md` §5 第 1 步「它會不會現在就造成低級事故？」——刪掉 11.7 MB 的快取不是事故。** 它屬目標 3：**記錄，不開卡。**

### 給查核者的更正指示

**請據實際規模而非機制本身判斷這一項。** PM 先前在 evidence 裡的措辭會誘導把它當 blocking——**那是 PM 的過度升級，不是執行者的宣稱，也不是事實**。

本輪真正該被審的是另外三處：**授權表的窮舉性**（`AUTHORITY_BY_PROOF` 之外還有別的路徑能發出刪分支指令嗎）、**控制流順序改動**（執行者自己說那是它最想請查核者盯的一處）、**`_BODY_ALLOWED_GLOBALS` 的自我複核**。

### PM 的帳

**這是需求方今日第五次糾正同一件事：PM 在追一個原則，而沒有問那個東西值多少。** `attribution: coordinator`。


## Comment 5275366866 · 2026-08-13T02:52:25Z

<!-- wf-review-receipt:v1
card_id: WF-CLEANUP-SQUASH-AWARE1
source_sha: 8efc1d2021ca6fe39d0f630eedf44bd1c94482d5
report_sha256: 575986d3f839b8bf56e78d093d71a46609432ee8f104465395bb14ef44b0013f
-->

取材規則：被雜湊內容從本規則之後的下一個 'core_pain_resolved:' 起，到被雜湊報告全文最後一個字元止；UTF-8、LF、無 strip；排除本收據註解與本取材規則。

core_pain_resolved: no
review_result: REQUEST_CHANGES
previous_round_closure:
  - finding_id: WF-CLEANUP-SQUASH-AWARE1-R1-01
    status: closed
    evidence: "R1 的 blocking（content_absorbed 會刪分支而遺失中間 commit）已由 AUTHORITY_BY_PROOF 收斂：content_absorbed 僅授權 remove_worktree；隔離 squash 重現確認本地與遠端分支存活。"
self_run:
  - command: "git rev-parse HEAD; git merge-base --is-ancestor 52839f0d81d90a0b790520764219ffe04a792f15 HEAD"
    observed: "HEAD=8efc1d2021ca6fe39d0f630eedf44bd1c94482d5；基線為祖先（exit 0）。"
  - command: "uv run pytest -qq --disable-warnings --tb=short"
    observed: "869 tests 完成至 100%，無失敗輸出。"
  - command: "temporary git repository: execute_closeout_transition on a squash-merged branch"
    observed: "mode=applied、state=completed、authorized_actions=[remove_worktree]，writer 呼叫 write_release_terminal，但 local_branch_exists=True 且 remote_branch_exists=True。"
  - command: "git diff --check 52839f0d81d90a0b790520764219ffe04a792f15..HEAD; git merge-tree --write-tree 52839f0d81d90a0b790520764219ffe04a792f15 HEAD"
    observed: "diff check 無輸出；合併樹成功產生 3488090c9bef52dd5790236a92d349a2e145c2eb。"
findings:
  - finding_id: WF-CLEANUP-SQUASH-AWARE1-R2-01
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: closeout-terminal-evidence-not-scoped-to-authority
    evidence: "cleanup.py:1458-1468 以 scoped authorized_actions 判定 cleanup_done，故 squash 的 remove_worktree-only 路徑會呼叫 effect_writer；但 handoff_cmd.py:352-355 仍把該呼叫寫成「worktree 與本地／遠端分支皆已不存在」。隔離重現已證明此時兩分支仍存在。"
    disposition: "修改終態寫入內容，使其依 result.authorized_actions 與實際 observation_after 留下真實、可稽核的收尾範圍；squash 路徑必須明示分支刻意保留，並加入經 _release_with_cleanup 的回歸測試。需先由需求方或 PM 擴充本卡寫入集納入 cli/src/wf_cli/commands/handoff_cmd.py。"

## Comment 5275392015 · 2026-08-13T02:56:25Z

<!-- wf-review-event:v1 card_id=WF-CLEANUP-SQUASH-AWARE1 source_sha=8efc1d2021ca6fe39d0f630eedf44bd1c94482d5 attempt_id=WF-CLEANUP-SQUASH-AWARE1-e0-8efc1d2021ca6fe39d0f630eedf44bd1c94482d5 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CLEANUP-SQUASH-AWARE1`　attempt_id：`WF-CLEANUP-SQUASH-AWARE1-e0-8efc1d2021ca6fe39d0f630eedf44bd1c94482d5`
- 查核者：GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5275366866 未經編輯，PM 依其取材規則（core_pain_resolved 起至 EOF）回讀重算相符　escalation_epoch：0
- source_sha：`8efc1d2021ca6fe39d0f630eedf44bd1c94482d5`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-13T10:56:23+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git merge-base --is-ancestor 52839f0d81d90a0b790520764219ffe04a792f15 HEAD`
  - HEAD=8efc1d2021ca6fe39d0f630eedf44bd1c94482d5；基線為祖先（exit 0）。
- `uv run pytest -qq --disable-warnings --tb=short`
  - 869 tests 完成至 100%，無失敗輸出。
- `temporary git repository: execute_closeout_transition on a squash-merged branch`
  - mode=applied、state=completed、authorized_actions=[remove_worktree]，writer 呼叫 write_release_terminal，但 local_branch_exists=True 且 remote_branch_exists=True。
- `git diff --check 52839f0d81d90a0b790520764219ffe04a792f15..HEAD; git merge-tree --write-tree 52839f0d81d90a0b790520764219ffe04a792f15 HEAD`
  - diff check 無輸出；合併樹成功產生 3488090c9bef52dd5790236a92d349a2e145c2eb。

### findings（1，其中 blocking 1）

- **WF-CLEANUP-SQUASH-AWARE1-R2-01**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`closeout-terminal-evidence-not-scoped-to-authority`
  - evidence：cleanup.py:1458-1468 以 scoped authorized_actions 判定 cleanup_done，故 squash 的 remove_worktree-only 路徑會呼叫 effect_writer；但 handoff_cmd.py:352-355 仍把該呼叫寫成「worktree 與本地／遠端分支皆已不存在」。隔離重現已證明此時兩分支仍存在。
  - disposition：修改終態寫入內容，使其依 result.authorized_actions 與實際 observation_after 留下真實、可稽核的收尾範圍；squash 路徑必須明示分支刻意保留，並加入經 _release_with_cleanup 的回歸測試。需先由需求方或 PM 擴充本卡寫入集納入 cli/src/wf_cli/commands/handoff_cmd.py。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-CLEANUP-SQUASH-AWARE1-e0-8efc1d2021ca6fe39d0f630eedf44bd1c94482d5
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: no
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: "跨家族查核（GPT-5@Codex 子代理）"
findings:
  - finding_id: WF-CLEANUP-SQUASH-AWARE1-R2-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: closeout-terminal-evidence-not-scoped-to-authority
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5275397142 · 2026-08-13T02:57:11Z

## PM 更正：上一筆 handoff 的 evidence 被 shell 吃掉一段

`handoff` 的 `--evidence` 裡有一段用了反引號，**被 zsh 當成指令替換展開後消失**。缺的是修法方向那一句。完整版：

> 修法方向：終態與相關訊息須據**實際執行的動作集合**產生，而非固定字串；`actions_withheld_unauthorized` 已有該資訊。

⚠️ **這正是 PM 連續兩次提醒查核者避開的那個坑**（先前有兩個 delimiter 名稱在收據裡被 shell 展開而遺失），而 PM 自己在同一天踩了。`attribution: coordinator`。

## R2-01 的完整內容（供執行者參考）

**squash 路徑只移除 worktree 並保留分支，但終態留痕仍宣稱本地／遠端分支「皆已不存在」——造成可稽核內容失真。**

查核者在隔離 repo 重現了該錯誤語意，並確認：R1 blocking 已閉環、869 個測試 100% 完成、未修改被審 worktree、未變更 PR 狀態。

### 這是 ROADMAP §0 目標 2 的直接違反

> **可稽核的內容**：事後能從留痕重建「做了什麼、依據是什麼」。

**授權分流改了行為，卻沒改留痕的措辭**——於是留痕描述的是舊行為。**這個形狀值得單獨記**：本輪的改動是「不做某個動作」，而**留痕是照著「做了什麼」的舊假設寫死的**，所以行為變了、敘述沒變，兩者從此不同源。

### 執行者須確認的範圍

凡宣稱「已刪除」之處都改為據實敘述，**不只是終態那一行**：

- `_execute_closeout` 的回傳與其 `actions_performed`／`actions_skipped_absent` 的語意
- `handoff` 印出的 stderr（「已執行：remove_worktree, delete_local_branch, delete_remote_branch」那一行）
- Log 索引行
- `doctor`／`snapshot` 若有讀取該敘述之處

**判準**：留痕須據**實際執行的動作集合**產生，而非固定字串。`actions_withheld_unauthorized` 已經有那個資訊，問題在沒有人讀它。


## Comment 5275651849 · 2026-08-13T03:37:05Z

<!-- wf-review-receipt:v1
card_id: WF-CLEANUP-SQUASH-AWARE1
source_sha: 64f1a0cd5526ce66041bbc1066060d0e28053bd9
report_sha256: ebfd5e9de3838a453554fffff912d7813bda52d0b91bc5cfccb76f9cc716e35c
-->

取材規則：被雜湊內容從本規則之後的下一個 'core_pain_resolved:' 起，到被雜湊報告全文最後一個字元止；UTF-8、LF、無 strip；排除本收據註解與本取材規則。

core_pain_resolved: yes
review_result: REQUEST_CHANGES
previous_round_closure:
  - finding_id: WF-CLEANUP-SQUASH-AWARE1-R2-01
    status: closed
    evidence: "squash 隔離測試通過：終態為『收尾清理：已清除 worktree；本地分支、遠端分支 依授權保留（未刪除）』，兩分支仍存在；終態與 Log 共用同一 cleanup_note。"
self_run:
  - command: "git rev-parse HEAD; git merge-base --is-ancestor 52839f0d81d90a0b790520764219ffe04a792f15 HEAD"
    observed: "HEAD=64f1a0cd5526ce66041bbc1066060d0e28053bd9；基線為祖先（exit 0）。"
  - command: "uv run pytest -qq --disable-warnings --tb=short"
    observed: "875 tests 完成至 100%，無失敗輸出。"
  - command: "uv run pytest -q tests/test_cleanup.py::test_a_rejected_conditional_delete_aborts_rather_than_raising tests/test_cleanup.py::test_the_terminal_note_matches_what_was_actually_done_on_the_squash_path tests/test_cleanup.py::test_the_cleanup_description_accounts_for_every_action_in_every_partition"
    observed: "3 passed；證實 aborted 會有 performed 動作但 effect writer 零呼叫，並覆核 squash 留痕與 64 種有效指派。"
  - command: "temporary git repository: pretend remote delete command succeeds while remote ref remains"
    observed: "重新觀測在寫終態前發現遠端分支仍在，result=applied、state=cleanup_in_progress、writer_calls=[]；故『只記指令不看遠端』不是目前實作的事實。"
  - command: "git diff --check 52839f0d81d90a0b790520764219ffe04a792f15..HEAD; git merge-tree --write-tree 52839f0d81d90a0b790520764219ffe04a792f15 HEAD"
    observed: "diff check 無輸出；合併樹成功產生 ee0197440eea662f4504fbf78ad9de81224faa47。"
findings:
  - finding_id: WF-CLEANUP-SQUASH-AWARE1-R3-01
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: partial-closeout-actions-have-no-durable-audit-record
    evidence: "cleanup.py:1524-1540 在 aborted 時回傳 actions_performed 與 actions_aborted，但不呼叫 effect writer；handoff_cmd.py:414-419 隨即只輸出 stderr 並 return 5。既有測試 test_a_rejected_conditional_delete_aborts_rather_than_raising 也斷言 writer.calls == []，同時 actions_performed 包含 remove_worktree 與 delete_local_branch。stdout/stderr 不是 Issue Log。"
    disposition: "保留『不寫終態、不關 Issue』的安全規則，但為 aborted 寫入一筆明確非終態、append-only 的持久紀錄，內容必須由 CleanupOutcome 與阻擋原因產生；新增經 _release_with_cleanup 的回歸測試，驗證部分動作、未走到動作與中止原因皆可從 Issue 留痕重建。"
scope_external:
  - item: "完整分割的適用邊界"
    disposition: "64 種窮舉只覆蓋每個 DESTRUCTIVE_ORDER 動作被分派到四個 executor 桶一次的有效輸入；CleanupOutcome 本身不驗證互斥，任意呼叫者可把同一動作塞進兩桶並得到矛盾文字。現行 executor 的單一迴圈維持互斥，故非本輪 blocking；不可把它宣稱成一般輸入的完整分割。"
  - item: "遠端實況"
    disposition: "不是『只描述指令』：cleanup.py:1542-1551 會在終態前 observe，隔離模擬的遠端分支仍存在時不寫終態。觀測之後仍可能有外部鏡像重建的時間窗，屬非原子分散式系統殘餘；本輪沒有證據顯示它正在造成低級事故。"
  - item: "canonical 文件四處仍寫三動作收尾"
    disposition: "文件與 squash 授權分流不一致，應由文件權威卡統一修正；終態與 Issue Log 已能重建實際動作，故不以此獨立阻擋 R3。"
  - item: "handoff_cmd.py 與 doctor.py 的寫入集"
    disposition: "兩檔改動皆直接服務 R2-01：handoff 將同一 CleanupOutcome 接到終態與 CLI 摘要；doctor 顯示實際授權範圍，避免 squash 預覽暗示三刪。未發現夾帶無關行為。"
  - item: "worktree 數量 21 至 20"
    disposition: "已知範圍內的註冊 worktree 與 17 個卡分支均健在，且被審 diff 無任何 remove 或 prune 呼叫；未知的 /private/tmp 臨時工作區無法歸因，現有證據足以不列為本卡 finding。"

## Comment 5275665718 · 2026-08-13T03:38:57Z

<!-- wf-review-event:v1 card_id=WF-CLEANUP-SQUASH-AWARE1 source_sha=64f1a0cd5526ce66041bbc1066060d0e28053bd9 attempt_id=WF-CLEANUP-SQUASH-AWARE1-e0-64f1a0cd5526ce66041bbc1066060d0e28053bd9 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CLEANUP-SQUASH-AWARE1`　attempt_id：`WF-CLEANUP-SQUASH-AWARE1-e0-64f1a0cd5526ce66041bbc1066060d0e28053bd9`
- 查核者：GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5275651849 未經編輯，PM 依其取材規則回讀重算相符　escalation_epoch：0
- source_sha：`64f1a0cd5526ce66041bbc1066060d0e28053bd9`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-13T11:38:55+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git merge-base --is-ancestor 52839f0d81d90a0b790520764219ffe04a792f15 HEAD`
  - HEAD=64f1a0cd5526ce66041bbc1066060d0e28053bd9；基線為祖先（exit 0）。
- `uv run pytest -qq --disable-warnings --tb=short`
  - 875 tests 完成至 100%，無失敗輸出。
- `uv run pytest -q tests/test_cleanup.py::test_a_rejected_conditional_delete_aborts_rather_than_raising tests/test_cleanup.py::test_the_terminal_note_matches_what_was_actually_done_on_the_squash_path tests/test_cleanup.py::test_the_cleanup_description_accounts_for_every_action_in_every_partition`
  - 3 passed；證實 aborted 會有 performed 動作但 effect writer 零呼叫，並覆核 squash 留痕與 64 種有效指派。
- `temporary git repository: pretend remote delete command succeeds while remote ref remains`
  - 重新觀測在寫終態前發現遠端分支仍在，result=applied、state=cleanup_in_progress、writer_calls=[]；故『只記指令不看遠端』不是目前實作的事實。
- `git diff --check 52839f0d81d90a0b790520764219ffe04a792f15..HEAD; git merge-tree --write-tree 52839f0d81d90a0b790520764219ffe04a792f15 HEAD`
  - diff check 無輸出；合併樹成功產生 ee0197440eea662f4504fbf78ad9de81224faa47。

### findings（1，其中 blocking 1）

- **WF-CLEANUP-SQUASH-AWARE1-R3-01**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`partial-closeout-actions-have-no-durable-audit-record`
  - evidence：cleanup.py:1524-1540 在 aborted 時回傳 actions_performed 與 actions_aborted，但不呼叫 effect writer；handoff_cmd.py:414-419 隨即只輸出 stderr 並 return 5。既有測試 test_a_rejected_conditional_delete_aborts_rather_than_raising 也斷言 writer.calls == []，同時 actions_performed 包含 remove_worktree 與 delete_local_branch。stdout/stderr 不是 Issue Log。
  - disposition：保留『不寫終態、不關 Issue』的安全規則，但為 aborted 寫入一筆明確非終態、append-only 的持久紀錄，內容必須由 CleanupOutcome 與阻擋原因產生；新增經 _release_with_cleanup 的回歸測試，驗證部分動作、未走到動作與中止原因皆可從 Issue 留痕重建。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-CLEANUP-SQUASH-AWARE1-e0-64f1a0cd5526ce66041bbc1066060d0e28053bd9
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: "跨家族查核（GPT-5@Codex 子代理）"
findings:
  - finding_id: WF-CLEANUP-SQUASH-AWARE1-R3-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: partial-closeout-actions-have-no-durable-audit-record
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5277027399 · 2026-08-13T06:51:42Z

<!-- wf-review-receipt:v1
card_id: WF-CLEANUP-SQUASH-AWARE1
source_sha: e36f592178ee54a1db0b8260ab09a4c8f7a9662f
report_sha256: 2682946224e64212f54c7017544d664c4e480b9bb438f89fe18a1ac700920212
-->

取材規則：被雜湊內容從本規則之後的下一個 `core_pain_resolved:` 起，到被雜湊報告全文最後一個字元止；編碼為 UTF-8；換行形式為 LF；不做 strip()；排除本收據註解與本取材規則。此檔案結尾的 LF 屬於被雜湊報告全文。

core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "git merge-base --is-ancestor 52839f0d81d90a0b790520764219ffe04a792f15 e36f592178ee54a1db0b8260ab09a4c8f7a9662f"
    observed: "exit 0；baseline 是 source SHA 的祖先。"
  - command: "git diff --stat 52839f0d81d90a0b790520764219ffe04a792f15..e36f592178ee54a1db0b8260ab09a4c8f7a9662f；git diff --stat 64f1a0cd5526ce66041bbc1066060d0e28053bd9..e36f592178ee54a1db0b8260ab09a4c8f7a9662f"
    observed: "完整範圍為 5 檔 +1478/-64；本輪增量嚴格為 handoff_cmd.py 與 test_release_cleanup.py，+274/-9；diff --check 無輸出。"
  - command: "cd cli && uv run pytest -q"
    observed: "879 passed in 48.53s，exit 0。"
  - command: "cd cli && uv run pytest -q tests/test_release_cleanup.py::test_an_aborted_closeout_leaves_a_non_terminal_record_of_what_it_did tests/test_release_cleanup.py::test_actions_are_recorded_even_when_an_applied_run_had_its_effect_withheld tests/test_release_cleanup.py::test_a_guard_block_that_touched_nothing_writes_no_record tests/test_release_cleanup.py::test_a_completed_closeout_records_the_actions_exactly_once"
    observed: "4 passed in 3.20s。"
  - command: "cd cli && uv run pytest -q tests/test_release_cleanup.py::test_status_face_stays_put_when_the_remote_delete_is_aborted tests/test_release_cleanup.py::test_release_fails_when_cleanup_reported_success_but_did_not_complete tests/test_cleanup.py::test_a_rejected_conditional_delete_aborts_rather_than_raising"
    observed: "3 passed in 3.20s。"
  - command: "控制流逐段查核 execute_closeout_transition、_release_with_cleanup、_record_actions_without_terminal"
    observed: "detect_only 在破壞迴圈前以空集合回傳；aborted 先附加 aborted 動作才回傳；applied 若 effect_done 為否，授權且存在的資源在迴圈中只會附加 performed、附加 aborted，或拋出例外而不回傳 CloseoutResult。沒有『已動資源且 performed/aborted 皆空』的第三種回傳路徑。"
  - command: "增量 diff 與呼叫面查核"
    observed: "新函式僅接收 effect_calls 名稱序列與 append_log callback；不持有 writer，未呼叫 set_field_value 或 issue close；mode != applied 分支和所有既有 return 碼未變。"
findings:
  - finding_id: WF-CLEANUP-SQUASH-AWARE1-R4-01
    severity: minor
    blocking: false
    finding_class: test-coverage
    attribution: executor
    evidence: "aborted 測試逐欄比對交付狀態、owner、最後交接、iteration 且確認 Issue 未關；但 applied-效果扣住測試只斷言交付狀態與 Issue，守衛擋下與完成測試也未逐欄比對。因此『四條皆為完整雙面斷言』不成立。"
    disposition: "不阻擋本卡：R3 的 aborted 核心病灶已有完整雙面端到端斷言，且新增函式的型別與呼叫面不能寫狀態欄位。後續若整理測試，可讓另外三條同樣快照並逐欄比較狀態面。"
reviewed_non_findings:
  - topic: "動作集合觸發條件"
    conclusion: "正確。它涵蓋 mode=applied 但效果扣住的已動作格，並排除 detect_only 的零動作噪音；比 mode != applied 更符合實際狀態機。"
  - topic: "write_status_face 命名"
    conclusion: "non-blocking。名稱仍描述其主要狀態面寫入，附加 Log 是既有交接原子操作的一部分；本輪以 append_card_log 分離非終態留痕，未改名不影響機械狀態面的事實或安全性。"
  - topic: "item.body 快照"
    conclusion: "non-blocking。單一 run 由『終態已寫則不記非終態』互斥，不會雙寫覆蓋；跨 run 並行的 read-modify-write 競態既存且非本輪引入。"


## Comment 5277133957 · 2026-08-13T07:02:46Z

<!-- wf-review-receipt:v1
card_id: WF-CLEANUP-SQUASH-AWARE1
source_sha: e36f592178ee54a1db0b8260ab09a4c8f7a9662f
report_sha256: 5e7a2774f08cbae91e1c4b504bfe71937c0ae46688b18ffcff7adbd12621aca8
-->

取材規則：被雜湊內容從本規則之後的下一個 `core_pain_resolved:` 起，到被雜湊報告全文最後一個字元止；編碼為 UTF-8；換行形式為 LF；不做 strip()；排除本收據註解與本取材規則。此檔案結尾的 LF 屬於被雜湊報告全文。

core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "git merge-base --is-ancestor 52839f0d81d90a0b790520764219ffe04a792f15 e36f592178ee54a1db0b8260ab09a4c8f7a9662f"
    observed: "exit 0；baseline 是 source SHA 的祖先。"
  - command: "git diff --stat 52839f0d81d90a0b790520764219ffe04a792f15..e36f592178ee54a1db0b8260ab09a4c8f7a9662f；git diff --stat 64f1a0cd5526ce66041bbc1066060d0e28053bd9..e36f592178ee54a1db0b8260ab09a4c8f7a9662f"
    observed: "完整範圍為 5 檔 +1478/-64；本輪增量嚴格為 handoff_cmd.py 與 test_release_cleanup.py，+274/-9；diff --check 無輸出。"
  - command: "cd cli && uv run pytest -q"
    observed: "879 passed in 48.53s，exit 0。"
  - command: "cd cli && uv run pytest -q tests/test_release_cleanup.py::test_an_aborted_closeout_leaves_a_non_terminal_record_of_what_it_did tests/test_release_cleanup.py::test_actions_are_recorded_even_when_an_applied_run_had_its_effect_withheld tests/test_release_cleanup.py::test_a_guard_block_that_touched_nothing_writes_no_record tests/test_release_cleanup.py::test_a_completed_closeout_records_the_actions_exactly_once"
    observed: "4 passed in 3.20s。"
  - command: "cd cli && uv run pytest -q tests/test_release_cleanup.py::test_status_face_stays_put_when_the_remote_delete_is_aborted tests/test_release_cleanup.py::test_release_fails_when_cleanup_reported_success_but_did_not_complete tests/test_cleanup.py::test_a_rejected_conditional_delete_aborts_rather_than_raising"
    observed: "3 passed in 3.20s。"
  - command: "控制流逐段查核 execute_closeout_transition、_release_with_cleanup、_record_actions_without_terminal"
    observed: "detect_only 在破壞迴圈前以空集合回傳；aborted 先附加 aborted 動作才回傳；applied 若 effect_done 為否，授權且存在的資源在迴圈中只會附加 performed、附加 aborted，或拋出例外而不回傳 CloseoutResult。沒有『已動資源且 performed/aborted 皆空』的第三種回傳路徑。"
  - command: "增量 diff 與呼叫面查核"
    observed: "新函式僅接收 effect_calls 名稱序列與 append_log callback；不持有 writer，未呼叫 set_field_value 或 issue close；mode != applied 分支和所有既有 return 碼未變。"
findings:
  - finding_id: WF-CLEANUP-SQUASH-AWARE1-R4-01
    severity: minor
    blocking: false
    finding_class: implementation
    attribution: executor
    root_cause_id: incomplete-status-face-regression-assertions
    evidence: "aborted 測試逐欄比對交付狀態、owner、最後交接、iteration 且確認 Issue 未關；但 applied-效果扣住測試只斷言交付狀態與 Issue，守衛擋下與完成測試也未逐欄比對。因此『四條皆為完整雙面斷言』不成立。"
    disposition: "不阻擋本卡：R3 的 aborted 核心病灶已有完整雙面端到端斷言，且新增函式的型別與呼叫面不能寫狀態欄位。後續若整理測試，可讓另外三條同樣快照並逐欄比較狀態面。"


## Comment 5277149247 · 2026-08-13T07:04:41Z

<!-- wf-review-event:v1 card_id=WF-CLEANUP-SQUASH-AWARE1 source_sha=e36f592178ee54a1db0b8260ab09a4c8f7a9662f attempt_id=WF-CLEANUP-SQUASH-AWARE1-e0-e36f592178ee54a1db0b8260ab09a4c8f7a9662f -->
## 查核裁決：APPROVE

- 卡：`WF-CLEANUP-SQUASH-AWARE1`　attempt_id：`WF-CLEANUP-SQUASH-AWARE1-e0-e36f592178ee54a1db0b8260ab09a4c8f7a9662f`
- 查核者：GPT-5@Codex 子代理（需求方轉貼）　escalation_epoch：0
- source_sha：`e36f592178ee54a1db0b8260ab09a4c8f7a9662f`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-13T15:04:40+08:00

### self_run（查核者實跑）

- `git merge-base --is-ancestor 52839f0d81d90a0b790520764219ffe04a792f15 e36f592178ee54a1db0b8260ab09a4c8f7a9662f`
  - exit 0；baseline 是 source SHA 的祖先。
- `git diff --stat 52839f0d81d90a0b790520764219ffe04a792f15..e36f592178ee54a1db0b8260ab09a4c8f7a9662f；git diff --stat 64f1a0cd5526ce66041bbc1066060d0e28053bd9..e36f592178ee54a1db0b8260ab09a4c8f7a9662f`
  - 完整範圍為 5 檔 +1478/-64；本輪增量嚴格為 handoff_cmd.py 與 test_release_cleanup.py，+274/-9；diff --check 無輸出。
- `cd cli && uv run pytest -q`
  - 879 passed in 48.53s，exit 0。
- `cd cli && uv run pytest -q tests/test_release_cleanup.py::test_an_aborted_closeout_leaves_a_non_terminal_record_of_what_it_did tests/test_release_cleanup.py::test_actions_are_recorded_even_when_an_applied_run_had_its_effect_withheld tests/test_release_cleanup.py::test_a_guard_block_that_touched_nothing_writes_no_record tests/test_release_cleanup.py::test_a_completed_closeout_records_the_actions_exactly_once`
  - 4 passed in 3.20s。
- `cd cli && uv run pytest -q tests/test_release_cleanup.py::test_status_face_stays_put_when_the_remote_delete_is_aborted tests/test_release_cleanup.py::test_release_fails_when_cleanup_reported_success_but_did_not_complete tests/test_cleanup.py::test_a_rejected_conditional_delete_aborts_rather_than_raising`
  - 3 passed in 3.20s。
- `控制流逐段查核 execute_closeout_transition、_release_with_cleanup、_record_actions_without_terminal`
  - detect_only 在破壞迴圈前以空集合回傳；aborted 先附加 aborted 動作才回傳；applied 若 effect_done 為否，授權且存在的資源在迴圈中只會附加 performed、附加 aborted，或拋出例外而不回傳 CloseoutResult。沒有『已動資源且 performed/aborted 皆空』的第三種回傳路徑。
- `增量 diff 與呼叫面查核`
  - 新函式僅接收 effect_calls 名稱序列與 append_log callback；不持有 writer，未呼叫 set_field_value 或 issue close；mode != applied 分支和所有既有 return 碼未變。

### findings（1，其中 blocking 0）

- **WF-CLEANUP-SQUASH-AWARE1-R4-01**　severity=minor　blocking=false　class=implementation　attribution=executor　root_cause_id=`incomplete-status-face-regression-assertions`
  - evidence：aborted 測試逐欄比對交付狀態、owner、最後交接、iteration 且確認 Issue 未關；但 applied-效果扣住測試只斷言交付狀態與 Issue，守衛擋下與完成測試也未逐欄比對。因此『四條皆為完整雙面斷言』不成立。
  - disposition：不阻擋本卡：R3 的 aborted 核心病灶已有完整雙面端到端斷言，且新增函式的型別與呼叫面不能寫狀態欄位。後續若整理測試，可讓另外三條同樣快照並逐欄比較狀態面。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-CLEANUP-SQUASH-AWARE1-e0-e36f592178ee54a1db0b8260ab09a4c8f7a9662f
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（GPT-5@Codex）
findings:
  - finding_id: WF-CLEANUP-SQUASH-AWARE1-R4-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: implementation
    attribution: executor
    root_cause_id: incomplete-status-face-regression-assertions
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。
