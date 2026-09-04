# #57 WF-WORKTREE-REPO-OWNERSHIP1 worktree 建錯 repo 沒有預防，只有事後對帳
- state: open  created: 2026-08-12T09:42:43Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/57
- comments: 28

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code PM
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；須裁定 registry 的 github 模式形狀並確認不與既有 doctor 對帳重複或衝突；推理鏈中等。）　查核：待指派（建議 經濟型；預防性守衛，風險有限；查核重點在誤報率與跨 repo 判定是否可靠。）
- Initiative：—　spec 基線：自 WF-ORCHESTRATION-RECONCILE1（#16）§9 衍生卡切出。該清單自 2026-08-11 提出後從未開卡；需求方 2026-08-12 盤點後裁定「先開卡、#16 續審排後面」，判準是清單被執行才是 #16 的價值。 #16 §9 衍生卡 H：§7、§7.1 連結卡欄位、registry github 模式。無相依。
- DB：db_scope=none
- 服務的原始目標：讓 worktree 建在錯的 repo 這件事在建立當下被擋，而不是事後才在對帳裡看到

## 簡介
<!-- card-brief:begin -->
在 wfcli assign 這條路徑上加跨 repo 歸屬檢查，讓 worktree 建在錯的 repo 於建立當下被擋——事後對帳看不見真實案例：兩個真實漂移 worktree 在兩個 repo 的頂層 git worktree list 都是 0 命中，doctor 不可能發現。**適用時機**：Project #4 同時裝 ai-workflow 與 cpbl-analytics 兩 repo 的卡、Issue 編號還會撞，要判 worktree 該建在哪；或要查這道守衛買到與沒買到什麼時。⛔ 非射程：承諾只到 assign，⛔ 不是「登記面已被保護」——人直接跑 git worktree add、分支worktree 這個 Project TEXT 欄可被 GraphQL 直改、既有登記不重掃，三條皆為已知限制；先建後登記的真正預防歸 aiwf#91；doctor.py 的孤兒誤報修法歸 aiwf#30。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：worktree 建錯 repo 今天沒有任何預防，只有事後對帳——而該對帳本身看不見真實案例：兩個真實跨 repo 漂移 worktree（cpbl-analytics 底下、commondir 指向其 .git/modules/.ai-workflow、origin 是 ai-workflow、卻註冊在 cpbl 的卡上）在兩個 repo 的頂層 git worktree list 都是 0 命中，doctor 不可能發現。【承諾範圍，需求方 2026-08-13 二次裁定】本卡的承諾是 wfcli assign 這一條路徑上的跨 repo 歸屬檢查，【不是「登記面已被保護」】。射程外有三條路徑，皆為已知限制而非待辦：(1) 人直接跑 git worktree add——wfcli 全域無此指令，完全不經本閘門；(2) 分支worktree 是 Project 的 TEXT 欄，web UI／gh project item-edit／GraphQL 可直接改寫，而 Project 欄位權限是 setting、不是檔案、不在資源模型值域裡（ROADMAP §2）；(3) 既有登記不重掃。⚠️ 兩次縮射程的形狀相同：wfcli 是慣例不是機制。需求方接受此限度並要求它寫在讀得到的地方，不得靠人記得；registry.py 頂端 danger 區塊須逐字保留建立面那句，並新增一句同等強度的關於 Project 欄位直接寫入。【已降 Backlog，保留 finding R4-01】登記發生在建立之前，allow 之後仍可由另一個 repo 建立同一路徑的 worktree，只能事後觀測到矛盾。要成立須做「建立後以可驗證事實回寫或驗證登記、不符即拒絕交接或撤銷登記」的執行面，屬新工程、不在收斂期射程。【⚠️ 2026-08-16 訂正一句與事實不符的敘述】本卡先前寫著「已合入 main 的 assign 路徑檢查、可攜 repo slug 歸屬與拒絕 ancestor 路徑推論登記不受本降級影響」——那三項都不在 main。複驗：origin/main 的 registry.py 與 assign_cmd.py 兩 blob 與 merge-base e8a638c 逐位元組相同、四個符號在 main 命中 0 個檔、該分支從未開過 PR。全部交付只存在於 claude/WF-WORKTREE-REPO-OWNERSHIP1，main 上只有 ROADMAP 的散文。需求方 2026-08-16 裁定：分支送跨家族查核，通過後合併，卡仍維持 Backlog。【合併買到什麼】軸 A 是純字串比對、順序無關、可攜，它在有人主動宣告跨 repo 時拒絕並指向 #16 §7.1 的連結卡做法。【合併沒買到什麼——不得誤讀】--worktree-source-repo 是 default=None 非必填，省略即宣告「屬於卡自己的 repo」，所以「漂到另一個 repo 而不宣告」這個真正的失效模式仍然回 allow；軸 B 只在登記路徑此刻存在且自身是另一 repo 的 worktree 時說得出話，而 assign --worktree 為 required=True 使登記必然早於建立，故軸 B 在現行操作順序下恆沉默——模組自陳「它的沉默不是判定」。合併不使核心痛點關閉。【finding 帳面狀態，2026-08-16 跨家族查核複驗後訂正】R3-01 closed、R3-02 superseded_by_requester_ruling、R4-01 open——只有 R4-01 一項是 open。本卡先前寫「三項維持未閉合」不成立，正確說法是：合併不消除底層風險（登記仍不綁定建立），但不得據此宣稱三項 finding 都還開著。本次合併不視為驗收。【真正的預防不在本卡】templates/worktree-lifecycle.md 第 1 點的 canonical 順序是「claim 成功後建立 worktree，並把實際路徑＋分支寫回卡面」＝先建後登記，是 CLI 把順序倒過來的；倒回模板後軸 B 才有事實可查。⚠️ 2026-08-16 跨家族查核已【獨立複驗】此點：兩個真實漂移 worktree 在現行順序（目標不存在）下 exit 0，先建後登記時皆由軸 B 擋下 exit 6。承接卡 #91 WF-ASSIGN-REGISTER-AFTER-CREATE1，其代價是把 assign 綁在 worktree 所在機器上、屬需求方取捨，且「本專案單機」是假設而非已驗事實。

跨 repo 這件事在本專案是實況而非假想：Project #4 同時裝著 ai-workflow 與 cpbl-analytics 兩個 repo 的卡，**Issue 編號會撞**（今天 #43、#45 各有兩張同號卡分屬兩 repo），PM 今天也因抽取未分 repo 而虛驚一場。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/registry.py",
    "file:cli/tests/test_registry.py",
    "file:cli/src/wf_cli/commands/assign_cmd.py",
    "file:cli/tests/test_commands_mocked.py",
    "file:cli/tests/test_release_cleanup.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 在 worktree 建立路徑上加預防：偵測 worktree 的目標 repo 與卡所屬 repo 不符時擋下。須說明「卡所屬 repo」怎麼判定，以及判不出來時的行為（fail-closed 或放行，二擇一並論證）。
- [ ] 裁定 registry 的 github 模式：#16 §7 提出 registry 應可讀 GitHub 而非只讀本機檔。本卡須裁定該模式的形狀，或論證不需要。
- [ ] 處理既有的誤報：doctor 今天把 WF 卡的 worktree 全報為孤兒，因為它讀 TASKS.md 投影。本卡須說明新守衛是否受同一問題影響；**若 doctor 的修法逸出本卡寫入集（doctor.py 由 #30 持有），明列為衍生而非代做**。

## 驗證

- [ ] 以真實的跨 repo 情境驗證：構造一張 cpbl-analytics 的卡並嘗試在 ai-workflow 內建 worktree，證明被擋。不得只有合成 fixture。
- [ ] 誤報率：以現有全部 worktree 實跑，證明新守衛不會擋下任何合法的既有配置。
- [ ] pytest 不得退化（基線自己跑）。凡寫下「會擋下」須指出執行者所在的檔與行。
## Log

- 2026-08-12T17:42:42+08:00 open by Claude Opus 5@Claude Code PM；owner 待指派；iteration 0。
- 2026-08-12T17:59:51+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code 子agent；分支worktree claude/WF-WORKTREE-REPO-OWNERSHIP1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-worktree-repo-ownership1；交付狀態 🚧進行中；實際能力層級 主力型（與卡面建議 主力型 相符）。
- 2026-08-12T18:25:03+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA 1e4888928d29ca061d359bce6087192bbce5f1d1；證據 R1：registry.py +372／test_registry.py +277，零逸出。pytest 基線 658（自跑於 e8a638c）→ **693**；ruff 其兩檔 All checks passed；marker 0。**PM 已複驗 693 passed、worktree 數 22 確實復原。**

⚠️ **本卡交付判定，未交付強制。** wfcli 全域沒有任何 git worktree add（實測零命中），唯一建立路徑是 assign 寫入 --worktree 註冊欄那一刻，攔截點在 **assign_cmd.py——寫入集外且由 #54 持有**。在 #54 接上前，block 判定**攔不下任何一次真實派工**。已寫進模組頂端 warning 與 commit message。

卡所屬 repo **只認 Issue URL**，明文拒絕 --repo／.wfcli.json／WFCLI_REPO：那是**呼叫端的主張**，而漂移形狀正是「人在 A repo 的環境下操作 B repo 的卡」——拿被檢查者的說法當基準，守衛在該擋的那一刻必然恆真通過。worktree 的 repo 由 **commondir 的 origin** 導出，比對軸是 slug 不是路徑（否則 submodule 的 commondir 在父 repo 的 .git/modules/ 下會被誤判成父 repo——**不是假想，見下**）。

判不出來 → **fail-closed**，三點論證：代價不對稱（誤擋是當場可讀的拒絕且訊息必附合法出路；誤放是沉默錯置、數週後才在會誤報的對帳裡浮出）；判不出來的每種輸入都不是合法穩態；fail-closed 不會被無關故障觸發（**守衛不新增任何網路相依**）。**刻意沒有 --force 逃生口**：漂移成因不是有人想跨 repo，是沒人注意到自己跨了。

⚠️ **它在真實環境找到兩個現在還活著的跨 repo 漂移，PM 已逐字複驗**：cpbl-analytics/.claude/worktrees/{wfcli-deploy-state1-execution, re24-prod-rebuild1-execution} 的 commondir 是 cpbl-analytics/.git/modules/.ai-workflow、origin 是 ai-workflow，分支 codex/WFCLI-DEPLOY-STATE1 與 codex/DATA-RE24-PROD-REBUILD1，**卻註冊在 cpbl 的卡上**；而**兩個 repo 的頂層 worktree list 都是 0 命中**——doctor 今天不可能發現。執行者未動它們，只指名。

誤報率**窮舉不抽樣**：磁碟現況 18 個可配對 → 18 allow／0 block；Project #4 全部 67 筆 → 64 allow／3 block，**三筆逐一查證無一誤擋**（兩筆是上述真陽性、經真實 commondir 證實；第三筆目錄已不存在、走祖先 proxy，**標為未確認、不宣稱真陽性**）。**對照：同一批 18 個，doctor 唯讀實跑全部報孤兒——18/18 vs 0/18。**

registry github 模式裁定**需要**，形狀是 **adapter 不是第二介面**；**必須補一欄 repo**（TASKS.md Ledger 沒有 repo 欄，這正是跨 repo 漂移在舊 registry 內**不可表達**的原因），該欄已落地且 TasksMdRegistry 一律留 None（不猜）。loader 本體不做——唯一消費者是 #30 與 #54，且把 gh 相依塞進純 stdlib 的 registry 會改變 doctor 的相依形狀。

自陳六項無機械執行者，第 3 項有量測：**67 筆中 18 筆是相對路徑**，若操作者 cwd 在錯的 repo，**誤擋從 0 暴增到 19 筆**——「守衛的正確性依賴在對的地方執行指令，而沒有任何東西強制這件事」。第 6 項是唯一真正窮舉的（reason→decision 全表，刻意不寫成「驗回傳值屬枚舉故恆真」）。。
- 2026-08-12T19:25:45+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5265964235，PM 回讀重算相符、未經編輯、marker 字面 0）；core_pain_resolved no；self_run 4 項；findings 3 項（blocking 3）；attempt WF-WORKTREE-REPO-OWNERSHIP1-e0-1e4888928d29ca061d359bce6087192bbce5f1d1。
- 2026-08-12T19:38:16+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 1；SHA 1e4888928d29ca061d359bce6087192bbce5f1d1；證據 三項 blocking，root_cause_id 皆為 worktree-repo-ownership。R1-01（planner）：判定引擎未接入 assign 攔截點，核心痛點要求「建立當下擋下」而交付只有判定；須改卡切分或改為純判定引擎且不得宣稱痛點已解。R1-02（executor）：probe_worktree_repo 對不存在目標問最近存在祖先，repo 外絕對路徑的合法新 worktree 會落到非 git 祖先而 block 且無 escape hatch；相對路徑預設 Path.cwd。R1-03（executor）：67 筆與 18 個的窮舉數字沒有同 HEAD 可重跑的 artifact，須交付唯讀枚舉器。。
- 2026-08-12T20:12:05+08:00 amend by wf-cli（op 2bf9ffaf）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/registry.py", "file:cli/tests/test_registry.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/registry.py、file:cli/tests/test_registry.py、file:cli/src/wf_cli/commands/assign_cmd.py、file:cli/tests/test_commands_mocked.py、file:cli/tests/test_release_cleanup.py」；理由 需求方 2026-08-12 裁定（issuecomment-5266614483）：R1-01 採 (a) 真正接線。assign_cmd.py 自 #54 移入（#54 已同步撤下宣告），連帶納入 test_commands_mocked.py 與 test_release_cleanup.py——執行者在拋棄式樹的接線原型實測 23 個既有測試被閘門當場拒絕（9 failed, 727 passed, 14 errors），那 23 個 fixture 須補真 Issue URL 與可判定的 worktree 路徑。代價已量化，裁定在知情下作出。同時定案 --worktree 路徑慣例：新的 assign 一律絕對路徑，或以 --worktree-source-repo 明示來源；既有 14 筆相對路徑不回溯檢查。。
- 2026-08-12T21:18:39+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 1；SHA 5575f82995f1d93e63d62056bd80c3c74c4869f6；證據 R2：三項 blocking 皆處置。R1-01 需求方裁定採 (a) 真正接線（issuecomment-5266614483），assign_cmd.py 自 #54 移入寫入集（#54 已撤下宣告，op dc04bcd5／2bf9ffaf）。閘門在任何 set_field_value／set_item_body 之前呼叫 check_assign_repo_ownership，blocked 回 5；--worktree-source-repo 已真的註冊（原型漏此，另有專測釘住旗標存在且省略時為 None）。23 個 fixture 逐項處置：test_commands_mocked.py 9 個改真 Issue ＋ source_repo fixture（刻意不把路徑改成剛好座落某 repo 底下，避免偷偷依賴磁碟佈局）；test_release_cleanup.py 14 個**不讓它通過閘門**，改把 assign 從 fixture 拿掉直接寫註冊欄——理由是該檔沙箱 repo 的 origin 只能是 tmp_path bare 路徑、導不出 owner/repo，閘門正確 fail-closed，而偽造 GitHub 形狀 origin 會讓 cleanup 的 ls-remote／push --delete 打向真實網路（已實測 url.insteadOf 連 remote get-url 一起改寫、pushInsteadOf 只救 push）。**代價誠實記錄：本檔不再覆蓋 assign 這條指令路徑。** R1-02 承認上一輪「判不出來的每種輸入都不是合法穩態」是錯的，根源在把歸屬當路徑座落問題而 git 真語意是 worktree 永遠屬於執行 add 的來源 repo；改為三級權威導出（source_repo／target_dir／ancestor_dir 並標 inferred），Path.cwd() 從判定路徑完全移除，新增 worktree_path_unanchored，並以 monkeypatch.chdir 回歸測試把「cwd 錯置誤擋暴增」機械封死。R1-03 交付 python -m wf_cli.registry 唯讀枚舉器，--input 重播兩次 cmp 逐位元組相同。⚠️ 自陳七項證明不了的，第 4 項最該看：現在有機械執行者但射程三條硬邊界——只管新寫入不回溯、只守 assign 一個入口（人直接在 shell 跑 git worktree add 完全不經過 wfcli，閘門擋的是登記不是建立）、origin 非 GitHub 形狀的 repo 一律過不了。第 7 項為新增自陳：test_release_cleanup.py 的 assign 覆蓋是淨損失，它證明不了那 14 個測試在真實 assign 路徑下仍等價。⚠️ 另主動報備 cli/tests/test_commands_mocked.py:290 有一處**既存**的事件 marker 前綴字面（git log -S 追到 26a0149，非本輪引入、不在其 diff 內），因該檔現在在其寫入集內故報備，未動它。PM 自審：遠端 tip 相符、1a1d9df 是祖先（非 force）、對 main merge-tree CLEAN、相對基線寫入集五檔逐項對上卡面宣告零逸出、trailer 三件齊備、合併樹 2677a98 實測 755 passed。。
- 2026-08-12T22:29:00+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼）；⚠️ 本卡收到兩則收據 issuecomment-5267827318 與 5267837844，需求方轉貼時稱前者「雜湊不符」——PM 逐一驗算後**該描述不成立**：兩則的雜湊各自都對得上自己的取材規則，且被雜湊內容逐位元組相同（sha 3cccc220095f288d、3503 bytes），為純重試無歧義。轉錄採 5267837844；core_pain_resolved no；self_run 5 項；findings 1 項（blocking 1）；attempt WF-WORKTREE-REPO-OWNERSHIP1-e0-5575f82995f1d93e63d62056bd80c3c74c4869f6。
- 2026-08-12T22:36:09+08:00 amend by wf-cli（op 97defb22）→ 核心痛點：原值「#16 §8 的四件真實漂移案例之一是「cpbl 卡的 worktree 建在 ai-workflow repo 內」。今天的處置是 doctor 事後對帳報孤兒，**沒有建立時的預防**。而 doctor 的對帳本身有已知誤報——2026-08-12 實測它把六個 WF 卡的 worktree 全報為「孤兒／未註冊」，因為它讀的是已封存的 TASKS.md 投影而非 GitHub 狀態面（cutover 後的既存落差）。」→ 新值「worktree 建錯 repo 今天沒有任何預防，只有事後對帳——而該對帳本身看不見真實案例：兩個真實跨 repo 漂移 worktree（cpbl-analytics 底下、commondir 指向其 .git/modules/.ai-workflow、origin 是 ai-workflow、卻註冊在 cpbl 的卡上）在兩個 repo 的頂層 git worktree list 都是 0 命中，doctor 不可能發現。【射程】本卡在 assign 登記 worktree 歸屬的當下攔截跨 repo 錯置；【刻意不涵蓋】git worktree add 的建立行為——wfcli 全域無任何 git worktree add（實測零命中），人直接在 shell 建立完全不經過本閘門。需求方 2026-08-12 裁定（issuecomment 見 Log）縮為登記面並另開承接卡；該卡未落地前，本 repo 對「人直接在 shell 建到錯的 repo」沒有任何預防，此句須逐字保留在 registry.py 頂端 danger 區塊，不得因本裁定軟化。」；理由 R2-01（blocking）查核者給兩條路，需求方採第二條：範圍明確改為僅保護登記而非建立，並依其要求同步修正核心痛點與服務原始目標，不得宣稱已在建立當下預防。裁定留言由 PM 代擬代貼、需求方核准，該事實寫在留言開頭——amend 的 author 檢查對 PM 恆真（#62 承接）。；授權 依需求方 ruan6047 於 https://github.com/ruan6047/ai-workflow/issues/57#issuecomment-5268265532 的裁定（GitHub comment author 已逐字核對，非留言內文自述）。
- 2026-08-12T22:37:01+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 2；SHA 5575f82995f1d93e63d62056bd80c3c74c4869f6；證據 R2-01（major, blocking, implementation, executor, worktree-repo-ownership）：source_repo 只唯讀查該目錄 origin，未觀測或綁定實際 git worktree add，故操作者可在 assign 給相符 source_repo 取得 allow 後從另一 repo 直接建立。需求方採查核者給的第二條路（issuecomment-5268265532）：射程縮為保護登記，核心痛點已 amend，建立面另開承接卡。執行者本輪須使文件與縮小後射程一致，並確保 registry.py 頂端 danger 區塊逐字保留「該卡未落地前本 repo 對人直接在 shell 建到錯的 repo 沒有任何預防」。三項前輪 blocking 查核者皆判 closed。。
- 2026-08-13T06:20:19+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 2；SHA 544e162b736a681532f49744f6a7fdfb2b79d96f；證據 R3：R2-01 已處置。需求方 2026-08-12 裁定射程縮為登記面（issuecomment-5268265532），核心痛點已 amend；本輪使交付物與縮小後射程一致。⚠️ 執行者正面回答 PM 指定的問題「縮射程後核心痛點真的關閉了嗎」，答案是【沒有完全關閉，登記面本身仍有一個同形狀的缺口且在射程內】：分支worktree 是 GitHub Project 的 TEXT 欄，web UI／gh project item-edit／GraphQL 皆可直接改寫，「唯一寫入通道=wfcli」是慣例不是機制——與 git worktree add 繞過閘門是完全相同的形狀，只是發生在登記面而非建立面，裁定把建立面移出射程卻沒有把這一個移出去。它並自陳無法為此加執行者（依 ROADMAP §2，Project 欄位權限是 setting、不是檔案、不在資源模型值域裡）。另兩項未閉合：既有 17 筆 block 判定永遠不被重掃（枚舉器列得出但無執行者、無排程，依 ROADMAP §0「沒有執行者的偵測器不算達成目標 1」）；46 筆 allow 裡 31 筆是 ancestor_dir 推測。結論自評為【部分閉合】並明說「若查核者依此判 core_pain_resolved: no，我不反駁」。閉合的部分經機械查證：assign 確實是 wfcli 全域唯一寫該欄的指令（逐一掃過所有 set_field_value 呼叫點：open_cmd 的 branch/worktree 無 CLI 旗標恆為 None、amend 只寫 Initiative/資源宣告/級別、handoff/review 只寫 owner/狀態/iteration），拒絕時零 mutation（recording runner 實證）。16 處「預防建立→攔截登記」的改動逐處列表交回（含 refusal_message 與 --worktree-source-repo help 兩處使用者可見字串）。danger 區塊兩種字面都留（卡面 amend 版與派審詞版不是彼此的子字串，只留一種必然違反另一份要求），並新增四條測試釘住，其中一條【反向釘死三個舊字面】防止有人補說明時把舊框架寫回來。建立面承接卡未開、未假設已排程（依 ROADMAP §5）。順帶修掉一處既有錯誤：check_worktree_repo_ownership 論證第 2 點仍寫著「判不出來的每一種輸入都不是合法穩態」，而 R1-02 早已舉出反例，改為列出三個 undeterminable 碼的補齊管道並把「當初那句錯在哪」留在原地不抹掉。數字：main dbf18d7 拋棄式 701、本輪分支 716（前輪 712，+4 無既有測試改動或刪除）、合併樹 7dd1bb2e 實跑 759 CLEAN；locale 矩陣 C 與 en_US.UTF-8 各 126 passed；uvx ruff 五檔 All checks passed；CI 另兩步在合併樹上亦跑過（uv lock --check 通過、replay 65/65）；枚舉器不動點 cmp 逐位元組相同。兩個真實漂移 worktree 只讀未動，git worktree list 仍 21。PM 自審：遠端 tip 相符、5575f82 是祖先（非 force）、對 main merge-tree CLEAN、寫入集四檔在卡面宣告五檔之內、trailer 3/3。⚠️ 執行者自陳六項證明不了的，第 1 項須查核者知悉：七項自陳的第 1、5 項是依 HEAD 的碼重新導出而非原文引用，原文只存在於 R2 交給 PM 的報告、Issue 上無留痕。⚠️ 環境已變：main 現為 d0397e0（#63 已 squash 合併），且 repo 已套用 required_status_checks ruleset（id 20768920、bypass_actors 0、strict true）——本卡的 PR 會被閘門實際擋一次，分支落後時須先 update-branch。。
- 2026-08-13T07:03:57+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5273770006。四項前輪 finding（R1-01/02/03、R2-01）皆判 closed。scope_outside 兩項未入區塊、保存於收據雜湊範圍內；core_pain_resolved no；self_run 6 項；findings 2 項（blocking 2）；attempt WF-WORKTREE-REPO-OWNERSHIP1-e0-544e162b736a681532f49744f6a7fdfb2b79d96f。
- 2026-08-13T07:22:43+08:00 amend by wf-cli（op 2759c387）→ 核心痛點：原值「worktree 建錯 repo 今天沒有任何預防，只有事後對帳——而該對帳本身看不見真實案例：兩個真實跨 repo 漂移 worktree（cpbl-analytics 底下、commondir 指向其 .git/modules/.ai-workflow、origin 是 ai-workflow、卻註冊在 cpbl 的卡上）在兩個 repo 的頂層 git worktree list 都是 0 命中，doctor 不可能發現。【射程】本卡在 assign 登記 worktree 歸屬的當下攔截跨 repo 錯置；【刻意不涵蓋】git worktree add 的建立行為——wfcli 全域無任何 git worktree add（實測零命中），人直接在 shell 建立完全不經過本閘門。需求方 2026-08-12 裁定（issuecomment 見 Log）縮為登記面並另開承接卡；該卡未落地前，本 repo 對「人直接在 shell 建到錯的 repo」沒有任何預防，此句須逐字保留在 registry.py 頂端 danger 區塊，不得因本裁定軟化。」→ 新值「worktree 建錯 repo 今天沒有任何預防，只有事後對帳——而該對帳本身看不見真實案例：兩個真實跨 repo 漂移 worktree（cpbl-analytics 底下、commondir 指向其 .git/modules/.ai-workflow、origin 是 ai-workflow、卻註冊在 cpbl 的卡上）在兩個 repo 的頂層 git worktree list 都是 0 命中，doctor 不可能發現。【承諾範圍，需求方 2026-08-13 二次裁定】本卡的承諾是 wfcli assign 這一條路徑上的跨 repo 歸屬檢查，【不是「登記面已被保護」】。射程外有三條路徑，皆為已知限制而非待辦：(1) 人直接跑 git worktree add——wfcli 全域無此指令，完全不經本閘門；(2) 分支worktree 是 Project 的 TEXT 欄，web UI／gh project item-edit／GraphQL 可直接改寫，而 Project 欄位權限是 setting、不是檔案、不在資源模型值域裡（ROADMAP §2）；(3) 既有登記不重掃。⚠️ 兩次縮射程的形狀相同：wfcli 是慣例不是機制。需求方接受此限度並要求它寫在讀得到的地方，不得靠人記得；registry.py 頂端 danger 區塊須逐字保留建立面那句，並新增一句同等強度的關於 Project 欄位直接寫入。」；理由 R3-01（blocking，attribution=planner）查核者給兩條路，需求方採第二條：把承諾降為僅 wfcli assign 路徑的檢查。理由與 ROADMAP §1 對身分的結論同構——追求涵蓋所有寫入路徑是在追一個結構上拿不到的東西，不可得的東西該被寫成已知限制而非待辦。降級不是放棄：assign 已機械查證為 wfcli 全域唯一寫該欄的指令、拒絕時零 mutation，能證明的部分照樣算數。⚠️ 本裁定不處置 R3-02（32 個 ancestor_dir 推測仍回 allow）——那落在縮小後的射程之內，須另行處置。；授權 依需求方 ruan6047 於 https://github.com/ruan6047/ai-workflow/issues/57#issuecomment-5273953073 的裁定（GitHub comment author 已逐字核對，非留言內文自述）。
- 2026-08-13T07:23:24+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 3；SHA 544e162b736a681532f49744f6a7fdfb2b79d96f；證據 R3 兩項 blocking。R3-01（governance, planner）：需求方 2026-08-13 二次裁定採查核者給的第二條路——承諾降為僅 wfcli assign 路徑的檢查，非「登記面已被保護」（issuecomment-5273953073）。核心痛點已 amend，明列射程外三條路徑為已知限制：git worktree add 直接建立、Project 欄位直接改寫、既有登記不重掃。執行者本輪須使交付物與此一致，並在 registry.py 頂端 danger 區塊【逐字保留建立面那句】、【新增一句同等強度的關於 Project 欄位直接寫入】。⚠️ R3-02（implementation, executor）【不在本裁定的處置範圍，須另行處理】：registry.py 把不存在目標的 ancestor_dir 標為 inferred 且明說不是事實，然而 check_assign_repo_ownership 對 slug 相符仍回 match/allow；本輪 Project 枚舉有 32 個 ancestor_dir allow；source 不觀測也不綁定後續 git worktree add，故可把登記寫成與祖先 repo 相符、後續卻由另一 repo 建立。disposition：新登記須要求可驗證且可留存的來源 repo 證據，或讓 inferred 一律拒絕並要求 source_repo；並以端到端測試證明無法以 ancestor_dir 推測取得 allow 後將同一路徑建立為另一 repo 的 worktree。⚠️ R3-02 落在【縮小後的射程之內】——assign 路徑上的判定該不該接受推測，與寫入路徑涵蓋範圍無關，不得因縮射程而視為已解。四項前輪 finding（R1-01/02/03、R2-01）查核者皆判 closed。⚠️ 環境已變：main 現為 0d6aae2（#9、#63、#73 皆已 squash 合併），ruleset 生效中；依 ROADMAP §3.5 卡片一律 squash 合併，分支落後時須先 update-branch。。
- 2026-08-13T07:52:04+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 3；SHA a0c25dbaacdd96660d64b37c5e1847d05adec7a0；證據 R4：兩項 blocking 皆處置。R3-01（planner）需求方 2026-08-13 裁定承諾降為僅 wfcli assign 路徑的檢查，核心痛點已 amend；執行者逐處對齊 14 項並在 danger 區塊新增第三句「本 repo 對『有人繞過 wfcli 直接改寫 Project 的分支worktree 欄』沒有任何預防」，三句皆有機械執行者（parametrize 三格 PASSED），並新增反向釘死禁用字面「登記面已被保護」「登記面攔截的唯一有效位置」。R3-02（executor）處置為 inferred 一律拒絕（新 reason code worktree_repo_inferred）。⚠️ 該處置【實質修改了需求方 08-12 的二擇一裁定】（絕對路徑或明示來源 → 兩者都要），執行者主動標示並指出翻回位置；需求方 2026-08-13 已裁定接受（issuecomment 見 Log），理由是執行者指出的是內部矛盾非取捨——_slug_of_dir 註解寫「比對軸是 origin slug 不是路徑」而祖先推測的全部證據只有路徑座落，31/47 的放行建立在模組自己判為無效的軸上。代價已量化：allow 47→16、block 17→48（翻面 31 筆，target_exists 全為 false 且閘門不回溯），真正代價落在未來每次 assign 都要多打一個旗標。⚠️ 需求方知情接受執行者自陳第 2 項的殘餘風險：修法可能把 cwd 依賴從碼裡趕到人腦裡——最順手的旗標答案就是「我現在站的這個 repo」，同一錯誤形狀換成社會層，碼裡仍不讀 cwd 但這條沒有執行者。⚠️ 執行者正面回答 PM 指定的兩題，答案都是「不是」：(1) 修完後 allow 不都是已驗證事實——只有 target_dir 是事實且只在檢查當下為真，source_repo 是宣告、git 只驗了那目錄是具 GitHub 形狀 origin 的 repo，沒觀測也沒綁定後續建立，它把這寫成測試（真跑一次跨 repo git worktree add 並確認成功）而非保證；(2) 第三次縮射程在路上且它現在就指名——「建立行為 assign 觀測不到」，真正能關掉它的是建立之後的對帳（fact 這時才存在），而今天沒有任何東西在建立之後看過一眼；依 §5 未開卡。端到端劇本全程真 git：推測說相符→判 block（劇本第一步就斷）→真的從另一 repo git worktree add 到同一路徑（成功，證明閘門沒綁定建立）→建立後重探證明當初推測指向與事實相反的 repo。PM 自審：遠端 tip 相符、544e162 是祖先（非 force）、對 main merge-tree CLEAN、寫入集四檔在卡面宣告五檔內、trailer 3/3、合併樹 27c9d441 實跑 901 passed。⚠️ 執行者自陳五項，第 5 項須查核者知悉：本輪唯一被翻面的既有測試 test_assign_allows_absolute_worktree_… 上一輪斷言的是相反結果且註明那是需求方裁定的預設用法，它改了並把理由寫在測試名字與 docstring 裡，但「改對不對是需求方的判斷」。。
- 2026-08-13T07:56:35+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 4；SHA a0c25dbaacdd96660d64b37c5e1847d05adec7a0；證據 ⛔ 撤回本輪派審，交回實作。無查核者進駐，本輪不計為可計數 attempt。成因：需求方 2026-08-13 問「絕對路徑是否是無效資訊，尤其是不同台電腦路徑不會完全相同」，PM 查證後推翻 R3-02 處置所依賴的前提，裁定見 issuecomment-5274176358。三項查證事實：(1) Project #4 全量絕對路徑 51 筆／相對路徑 18 筆，相對路徑中 cpbl-analytics 16 筆、ai-workflow 2 筆——「一律絕對路徑」那條慣例實際只約束了 PM 自己在打的那一半；(2) 相對路徑比絕對路徑更接近可稽核形式，先前收緊的方向收緊的是比較不可攜的那一種；(3) probe_worktree_repo 從路徑讀 commondir 反推 repo，換一台機器 target_dir 探測必然失敗、落到 ancestor_dir 或 undeterminable，依 R3-02 新規則即一律 block——故枚舉器那 64 筆是「這台機器的判定」不是 repo 的事實。裁定：分支worktree 欄混了兩種性質不同的東西而歸屬判定建立在錯的那一種上；歸屬應由 slug 表達不由路徑反推，--worktree-source-repo 應收 slug 而非目錄（可攜、可稽核、不需讀檔案系統），路徑退回 cleanup 的操作輸入、不參與歸屬判定。⚠️ 路徑不可移除——cleanup.py 用它做破壞性收尾、doctor/snapshot/handoff 亦讀它；這不是「路徑無效」是「兩者不該共用一個判定軸」。⚠️ 這是 ROADMAP §1 同一形狀第三次：身分那次追「驗證他真的是他」而只需「記下宣稱」，這次追「路徑指向的 repo 是什麼」而只需「這張卡宣稱屬於哪個 repo」；執行者上一輪自己指名的第三次縮射程（建立行為 assign 觀測不到）與此同源。處置：R3-01 的對齊工作（14 處措辭＋danger 第三句＋反向釘死）與本裁定無衝突、保留；R3-02 的處置（inferred 一律拒絕、--worktree-source-repo 收目錄）依本裁定重做；2026-08-13 那則「接受絕對路徑且明示來源」的裁定 issuecomment-5274150740 一併作廢，它建立在同一個被推翻的前提上。⚠️ attribution: coordinator——那則裁定是 PM 代擬、需求方核可，而 PM 當時沒有查證路徑的可攜性就下了「兩者都要」，需求方在核可後才自己提出這個問題。。
- 2026-08-13T08:40:30+08:00 handoff by wf-cli → owner 待指派；iteration 5；SHA 36b3f07d331f6a5118ab06851dc2c6ac8aa2d350；證據 依需求方 2026-08-13 裁定降為 Backlog：caaf664 交付後 Project #4 全量 64 筆，軸 A（可攜的歸屬判定）allow 64／block 0，軸 B（本機觀測）抓到 2 筆真實跨 repo 漂移但依 ROADMAP §1.5 不准影響判定——能擋的抓不到，抓得到的不准擋。依 §0 判準「目標 1 的卡：執行者是誰？答案若是靠人記得，它其實是目標 3」，本卡兩邊都不構成有機械執行者會擋下它。⚠️ 降級不是關閉也不是否定交付：caaf664 內容品質高，含跨機器一致性的實質證明（把 subprocess.run 與 Path.is_dir 換成會爆炸的替身證明歸屬判定執行期一次都沒碰檔案系統；三個不同 cwd 下四組輸入逐欄全等）；降級理由是這條路在可攜約束下走完了、不是走錯了。⚠️ 未閉合的 R3-01／R3-02 維持未閉合，本次降級不視為驗收；caaf664 未合併未查核。⚠️ 真正能關掉核心痛點的是建立之後的對帳（fact 那時才存在），執行者兩輪前已指名、今天無人承接，依 §5 本裁定不開卡只記義務。⚠️ 兩個真實漂移 worktree 仍在磁碟上、doctor 仍看不見。attribution: coordinator——本卡五輪中前四輪有三輪的前提是 PM 給錯的。。
- 2026-08-13T16:18:13+08:00 amend by wf-cli（op 424a6dfd）→ 核心痛點：原值「worktree 建錯 repo 今天沒有任何預防，只有事後對帳——而該對帳本身看不見真實案例：兩個真實跨 repo 漂移 worktree（cpbl-analytics 底下、commondir 指向其 .git/modules/.ai-workflow、origin 是 ai-workflow、卻註冊在 cpbl 的卡上）在兩個 repo 的頂層 git worktree list 都是 0 命中，doctor 不可能發現。【承諾範圍，需求方 2026-08-13 二次裁定】本卡的承諾是 wfcli assign 這一條路徑上的跨 repo 歸屬檢查，【不是「登記面已被保護」】。射程外有三條路徑，皆為已知限制而非待辦：(1) 人直接跑 git worktree add——wfcli 全域無此指令，完全不經本閘門；(2) 分支worktree 是 Project 的 TEXT 欄，web UI／gh project item-edit／GraphQL 可直接改寫，而 Project 欄位權限是 setting、不是檔案、不在資源模型值域裡（ROADMAP §2）；(3) 既有登記不重掃。⚠️ 兩次縮射程的形狀相同：wfcli 是慣例不是機制。需求方接受此限度並要求它寫在讀得到的地方，不得靠人記得；registry.py 頂端 danger 區塊須逐字保留建立面那句，並新增一句同等強度的關於 Project 欄位直接寫入。」→ 新值「worktree 建錯 repo 時，wfcli assign 會把錯誤歸屬登記進 Project 而無任何檢查——登記一旦寫入就成為後續判斷的依據，卻沒有任何東西擋下它。本卡只涵蓋 wfcli assign 這條路徑：Project 欄位仍可經網頁 UI、gh project item-edit 或 GraphQL 直接改寫，該面無預防，屬另卡射程。」；理由 依需求方裁定 issuecomment-5277820230 承接第三輪 finding R3-01（governance／planner）：本卡承諾降為僅 wfcli assign 路徑的檢查，不再宣稱涵蓋 Project 欄位的其他寫入路徑（網頁 UI／gh project item-edit／GraphQL）。涵蓋直接寫入的機械執行面屬另一張卡，依 ROADMAP §3 進降級清單。；授權 依需求方 ruan6047 於 https://github.com/ruan6047/ai-workflow/issues/57#issuecomment-5277820230 的裁定（GitHub comment author 已逐字核對，非留言內文自述）。
- 2026-08-13T16:18:50+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex）；iteration 5；SHA caaf6641a2e8e17520bc828aa1954cb941f7850a；證據 第四輪送審 caaf664（已推到 origin）。承接第三輪兩項 blocking：R3-01（governance／planner）由需求方裁定 issuecomment-5277820230 選 (B)——本卡承諾降為僅 wfcli assign 路徑的檢查，不再宣稱涵蓋 Project 欄位的其他寫入路徑；PM 已據該裁定以 wfcli amend（op 424a6dfd、ruling-url 綁定）改寫核心痛點，原值完整留在 Log。涵蓋直接寫入的機械執行面屬另卡射程，依 ROADMAP §3 進降級清單。R3-02（implementation／executor）由 a0c25db「refuse ancestor-path inference as a basis for ownership registration」承接，另有 caaf664「base worktree ownership on the portable repo slug」——後者對應需求方先前的發現：絕對路徑在不同電腦上不會相同，故不是可攜的歸屬依據。⚠️ 本卡自 544e162 受審後停置一段時間，這兩筆是停置期間完成但從未送審的碼，PM 今日盤點時才發現，非新交付。。
- 2026-08-13T17:07:49+08:00 contract-baseline by wf-cli → contract templates/review-escalation.md；宣告者 ruan6047；留言 https://github.com/ruan6047/ai-workflow/issues/57#issuecomment-5278306440。
- 2026-08-13T17:08:16+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼）；core_pain_resolved no；self_run 5 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-WORKTREE-REPO-OWNERSHIP1-e0-caaf6641a2e8e17520bc828aa1954cb941f7850a。
- 2026-08-13T17:09:09+08:00 amend by wf-cli（op e013514c）→ 核心痛點：原值「worktree 建錯 repo 時，wfcli assign 會把錯誤歸屬登記進 Project 而無任何檢查——登記一旦寫入就成為後續判斷的依據，卻沒有任何東西擋下它。本卡只涵蓋 wfcli assign 這條路徑：Project 欄位仍可經網頁 UI、gh project item-edit 或 GraphQL 直接改寫，該面無預防，屬另卡射程。」→ 新值「【已降 Backlog，保留 finding R4-01】worktree 建錯 repo 時，wfcli assign 會登記歸屬卻無法綁定實際建立：登記發生在建立之前，allow 之後仍可由另一個 repo 建立同一路徑的 worktree，只能事後觀測到矛盾。要成立須做「建立後以可驗證事實回寫或驗證登記、不符即拒絕交接或撤銷登記」的執行面，屬新工程、不在收斂期射程。已合入 main 的 assign 路徑檢查、可攜 repo slug 歸屬與拒絕 ancestor 路徑推論登記不受本降級影響。」；理由 依需求方裁定 issuecomment-5278315424 承接第四輪 finding R4-01：登記發生在建立之前且不綁定建立，即使限縮到 wfcli assign 路徑仍達不到核心痛點；依 ROADMAP §0 第一項『沒有執行者的偵測器不算達成』，本卡降為 Backlog 並保留 R4-01。已合入 main 的 assign 檢查、可攜 slug 歸屬與拒絕 ancestor 推論不受影響。；授權 依需求方 ruan6047 於 https://github.com/ruan6047/ai-workflow/issues/57#issuecomment-5278315424 的裁定（GitHub comment author 已逐字核對，非留言內文自述）。
- 2026-08-16T12:23:58+08:00 amend by wf-cli（op 3eb6ec6f）→ 核心痛點：原值「【已降 Backlog，保留 finding R4-01】worktree 建錯 repo 時，wfcli assign 會登記歸屬卻無法綁定實際建立：登記發生在建立之前，allow 之後仍可由另一個 repo 建立同一路徑的 worktree，只能事後觀測到矛盾。要成立須做「建立後以可驗證事實回寫或驗證登記、不符即拒絕交接或撤銷登記」的執行面，屬新工程、不在收斂期射程。已合入 main 的 assign 路徑檢查、可攜 repo slug 歸屬與拒絕 ancestor 路徑推論登記不受本降級影響。」→ 新值「worktree 建錯 repo 今天沒有任何預防，只有事後對帳——而該對帳本身看不見真實案例：兩個真實跨 repo 漂移 worktree（cpbl-analytics 底下、commondir 指向其 .git/modules/.ai-workflow、origin 是 ai-workflow、卻註冊在 cpbl 的卡上）在兩個 repo 的頂層 git worktree list 都是 0 命中，doctor 不可能發現。【承諾範圍，需求方 2026-08-13 二次裁定】本卡的承諾是 wfcli assign 這一條路徑上的跨 repo 歸屬檢查，【不是「登記面已被保護」】。射程外有三條路徑，皆為已知限制而非待辦：(1) 人直接跑 git worktree add——wfcli 全域無此指令，完全不經本閘門；(2) 分支worktree 是 Project 的 TEXT 欄，web UI／gh project item-edit／GraphQL 可直接改寫，而 Project 欄位權限是 setting、不是檔案、不在資源模型值域裡（ROADMAP §2）；(3) 既有登記不重掃。⚠️ 兩次縮射程的形狀相同：wfcli 是慣例不是機制。需求方接受此限度並要求它寫在讀得到的地方，不得靠人記得；registry.py 頂端 danger 區塊須逐字保留建立面那句，並新增一句同等強度的關於 Project 欄位直接寫入。【已降 Backlog，保留 finding R4-01】登記發生在建立之前，allow 之後仍可由另一個 repo 建立同一路徑的 worktree，只能事後觀測到矛盾。要成立須做「建立後以可驗證事實回寫或驗證登記、不符即拒絕交接或撤銷登記」的執行面，屬新工程、不在收斂期射程。【⚠️ 2026-08-16 訂正一句與事實不符的敘述】本卡先前寫著「已合入 main 的 assign 路徑檢查、可攜 repo slug 歸屬與拒絕 ancestor 路徑推論登記不受本降級影響」——那三項都不在 main。複驗：origin/main 的 registry.py 與 assign_cmd.py 兩 blob 與 merge-base e8a638c 逐位元組相同、四個符號在 main 命中 0 個檔、該分支從未開過 PR。全部交付只存在於 claude/WF-WORKTREE-REPO-OWNERSHIP1，main 上只有 ROADMAP 的散文。需求方 2026-08-16 裁定：分支送跨家族查核，通過後合併，卡仍維持 Backlog。【合併買到什麼】軸 A 是純字串比對、順序無關、可攜，它在有人主動宣告跨 repo 時拒絕並指向 #16 §7.1 的連結卡做法。【合併沒買到什麼——不得誤讀】--worktree-source-repo 是 default=None 非必填，省略即宣告「屬於卡自己的 repo」，所以「漂到另一個 repo 而不宣告」這個真正的失效模式仍然回 allow；軸 B 只在登記路徑此刻存在且自身是另一 repo 的 worktree 時說得出話，而 assign --worktree 為 required=True 使登記必然早於建立，故軸 B 在現行操作順序下恆沉默——模組自陳「它的沉默不是判定」。合併不使核心痛點關閉，R3-01／R3-02／R4-01 維持未閉合，本次合併不視為驗收。【真正的預防不在本卡】templates/worktree-lifecycle.md 第 1 點的 canonical 順序是「claim 成功後建立 worktree，並把實際路徑＋分支寫回卡面」＝先建後登記，是 CLI 把順序倒過來的；倒回模板後軸 B 才有事實可查，第五輪執行者在真實磁碟上實測兩個漂移 worktree 皆被擋下（exit 6）。該項另開承接卡，因其代價是把 assign 綁在 worktree 所在機器上、屬需求方取捨，且「本專案單機」是假設而非已驗事實。」；理由 第五輪執行者指出核心痛點末句「已合入 main 的 assign 路徑檢查、可攜 repo slug 歸屬與拒絕 ancestor 路徑推論登記不受本降級影響」與事實不符，PM 2026-08-16 獨立複驗成立：origin/main 的 registry.py 與 assign_cmd.py 兩個 blob 與 merge-base e8a638c 逐位元組相同（50088d2d／126f2a80），四個關鍵符號在 main 的 cli/ 命中 0 個檔（同組在分支 3/2/4/2），該分支從未開過 PR。需求方 2026-08-13 的降級裁定因此建立在錯誤前提上。本次 amend 移除該假敘述、改寫為分支未合併的事實，並依需求方 2026-08-16 裁定加註合併的射程（買到什麼、沒買到什麼），以免假印象由「在 main」平移為「在 main 所以漂移有人管」。卡仍維持 Backlog，合併不視為驗收。；授權 依需求方 ruan6047 於 https://github.com/ruan6047/ai-workflow/issues/57#issuecomment-5305701956 的裁定（GitHub comment author 已逐字核對，非留言內文自述）。
- 2026-08-16T12:30:08+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex）；iteration 5；SHA a5d38439e4fe5bab6f446f55797cfa6801e3d9f6；證據 ⚠️ 本輪查核目的與前四輪不同：卡已降 Backlog、core_pain_resolved 構造上不可達（唯一解法被卡面寫在射程外），**本輪要判的是這個分支該不該合併進 main**。起因是第五輪執行者發現卡面核心痛點與 08-13 降級裁定都寫著「已合入 main 的 assign 路徑檢查、可攜 repo slug 歸屬與拒絕 ancestor 路徑推論登記不受本降級影響」——那三項都不在 main。PM 2026-08-16 獨立複驗成立：origin/main 的 registry.py 與 assign_cmd.py 兩 blob 與 merge-base e8a638c 逐位元組相同（50088d2d／126f2a80）、四個關鍵符號在 main 的 cli/ 命中 0 個檔（同組在分支 3/2/4/2）、該分支從未開過 PR。需求方是在「有用的那一半已經入袋」的認知下降級的。需求方 2026-08-16 裁定（issuecomment-5305701956）：核心痛點已 amend（op 3eb6ec6f）移除該假敘述並加註合併的射程；分支送查核，通過後合併，卡仍維持 Backlog，合併不視為驗收，R3-01／R3-02／R4-01 維持未閉合。本輪唯一新增 commit a5d3843 為零行為改動（把 registry.py 模組 docstring 第 1 點「登記必然早於建立」加回限定詞——它是操作慣例非結構必然——並加一條測試釘住）。執行者自量：分支 723 passed（進駐 722，+1）、合併樹 944 passed（進駐 943）、merge-tree 乾淨 0 conflict、uvx ruff 宣告五檔 All checks passed；變異檢驗 M1–M5 五條既有守衛逐一拿掉皆轉紅、還原後綠（執行者自承腳本把 M0／還原兩列 label 寫錯標成 MUTATION NOT CAUGHT，數據本身正確）。未 rebase，落後 31 筆。⚠️ 執行者自陳中途 git checkout -- registry.py 誤清掉自己的修改、發現後重做。承接卡 #91 WF-ASSIGN-REGISTER-AFTER-CREATE1 已開，其頭號待驗證假設（倒轉順序後兩個真實漂移 worktree 被軸 B 擋下 exit 6）尚未經任何查核者複驗，本輪請一併驗。。
- 2026-08-16T12:40:13+08:00 amend by wf-cli（op 7a9c7a0f）→ 核心痛點：原值「worktree 建錯 repo 今天沒有任何預防，只有事後對帳——而該對帳本身看不見真實案例：兩個真實跨 repo 漂移 worktree（cpbl-analytics 底下、commondir 指向其 .git/modules/.ai-workflow、origin 是 ai-workflow、卻註冊在 cpbl 的卡上）在兩個 repo 的頂層 git worktree list 都是 0 命中，doctor 不可能發現。【承諾範圍，需求方 2026-08-13 二次裁定】本卡的承諾是 wfcli assign 這一條路徑上的跨 repo 歸屬檢查，【不是「登記面已被保護」】。射程外有三條路徑，皆為已知限制而非待辦：(1) 人直接跑 git worktree add——wfcli 全域無此指令，完全不經本閘門；(2) 分支worktree 是 Project 的 TEXT 欄，web UI／gh project item-edit／GraphQL 可直接改寫，而 Project 欄位權限是 setting、不是檔案、不在資源模型值域裡（ROADMAP §2）；(3) 既有登記不重掃。⚠️ 兩次縮射程的形狀相同：wfcli 是慣例不是機制。需求方接受此限度並要求它寫在讀得到的地方，不得靠人記得；registry.py 頂端 danger 區塊須逐字保留建立面那句，並新增一句同等強度的關於 Project 欄位直接寫入。【已降 Backlog，保留 finding R4-01】登記發生在建立之前，allow 之後仍可由另一個 repo 建立同一路徑的 worktree，只能事後觀測到矛盾。要成立須做「建立後以可驗證事實回寫或驗證登記、不符即拒絕交接或撤銷登記」的執行面，屬新工程、不在收斂期射程。【⚠️ 2026-08-16 訂正一句與事實不符的敘述】本卡先前寫著「已合入 main 的 assign 路徑檢查、可攜 repo slug 歸屬與拒絕 ancestor 路徑推論登記不受本降級影響」——那三項都不在 main。複驗：origin/main 的 registry.py 與 assign_cmd.py 兩 blob 與 merge-base e8a638c 逐位元組相同、四個符號在 main 命中 0 個檔、該分支從未開過 PR。全部交付只存在於 claude/WF-WORKTREE-REPO-OWNERSHIP1，main 上只有 ROADMAP 的散文。需求方 2026-08-16 裁定：分支送跨家族查核，通過後合併，卡仍維持 Backlog。【合併買到什麼】軸 A 是純字串比對、順序無關、可攜，它在有人主動宣告跨 repo 時拒絕並指向 #16 §7.1 的連結卡做法。【合併沒買到什麼——不得誤讀】--worktree-source-repo 是 default=None 非必填，省略即宣告「屬於卡自己的 repo」，所以「漂到另一個 repo 而不宣告」這個真正的失效模式仍然回 allow；軸 B 只在登記路徑此刻存在且自身是另一 repo 的 worktree 時說得出話，而 assign --worktree 為 required=True 使登記必然早於建立，故軸 B 在現行操作順序下恆沉默——模組自陳「它的沉默不是判定」。合併不使核心痛點關閉，R3-01／R3-02／R4-01 維持未閉合，本次合併不視為驗收。【真正的預防不在本卡】templates/worktree-lifecycle.md 第 1 點的 canonical 順序是「claim 成功後建立 worktree，並把實際路徑＋分支寫回卡面」＝先建後登記，是 CLI 把順序倒過來的；倒回模板後軸 B 才有事實可查，第五輪執行者在真實磁碟上實測兩個漂移 worktree 皆被擋下（exit 6）。該項另開承接卡，因其代價是把 assign 綁在 worktree 所在機器上、屬需求方取捨，且「本專案單機」是假設而非已驗事實。」→ 新值「worktree 建錯 repo 今天沒有任何預防，只有事後對帳——而該對帳本身看不見真實案例：兩個真實跨 repo 漂移 worktree（cpbl-analytics 底下、commondir 指向其 .git/modules/.ai-workflow、origin 是 ai-workflow、卻註冊在 cpbl 的卡上）在兩個 repo 的頂層 git worktree list 都是 0 命中，doctor 不可能發現。【承諾範圍，需求方 2026-08-13 二次裁定】本卡的承諾是 wfcli assign 這一條路徑上的跨 repo 歸屬檢查，【不是「登記面已被保護」】。射程外有三條路徑，皆為已知限制而非待辦：(1) 人直接跑 git worktree add——wfcli 全域無此指令，完全不經本閘門；(2) 分支worktree 是 Project 的 TEXT 欄，web UI／gh project item-edit／GraphQL 可直接改寫，而 Project 欄位權限是 setting、不是檔案、不在資源模型值域裡（ROADMAP §2）；(3) 既有登記不重掃。⚠️ 兩次縮射程的形狀相同：wfcli 是慣例不是機制。需求方接受此限度並要求它寫在讀得到的地方，不得靠人記得；registry.py 頂端 danger 區塊須逐字保留建立面那句，並新增一句同等強度的關於 Project 欄位直接寫入。【已降 Backlog，保留 finding R4-01】登記發生在建立之前，allow 之後仍可由另一個 repo 建立同一路徑的 worktree，只能事後觀測到矛盾。要成立須做「建立後以可驗證事實回寫或驗證登記、不符即拒絕交接或撤銷登記」的執行面，屬新工程、不在收斂期射程。【⚠️ 2026-08-16 訂正一句與事實不符的敘述】本卡先前寫著「已合入 main 的 assign 路徑檢查、可攜 repo slug 歸屬與拒絕 ancestor 路徑推論登記不受本降級影響」——那三項都不在 main。複驗：origin/main 的 registry.py 與 assign_cmd.py 兩 blob 與 merge-base e8a638c 逐位元組相同、四個符號在 main 命中 0 個檔、該分支從未開過 PR。全部交付只存在於 claude/WF-WORKTREE-REPO-OWNERSHIP1，main 上只有 ROADMAP 的散文。需求方 2026-08-16 裁定：分支送跨家族查核，通過後合併，卡仍維持 Backlog。【合併買到什麼】軸 A 是純字串比對、順序無關、可攜，它在有人主動宣告跨 repo 時拒絕並指向 #16 §7.1 的連結卡做法。【合併沒買到什麼——不得誤讀】--worktree-source-repo 是 default=None 非必填，省略即宣告「屬於卡自己的 repo」，所以「漂到另一個 repo 而不宣告」這個真正的失效模式仍然回 allow；軸 B 只在登記路徑此刻存在且自身是另一 repo 的 worktree 時說得出話，而 assign --worktree 為 required=True 使登記必然早於建立，故軸 B 在現行操作順序下恆沉默——模組自陳「它的沉默不是判定」。合併不使核心痛點關閉。【finding 帳面狀態，2026-08-16 跨家族查核複驗後訂正】R3-01 closed、R3-02 superseded_by_requester_ruling、R4-01 open——只有 R4-01 一項是 open。本卡先前寫「三項維持未閉合」不成立，正確說法是：合併不消除底層風險（登記仍不綁定建立），但不得據此宣稱三項 finding 都還開著。本次合併不視為驗收。【真正的預防不在本卡】templates/worktree-lifecycle.md 第 1 點的 canonical 順序是「claim 成功後建立 worktree，並把實際路徑＋分支寫回卡面」＝先建後登記，是 CLI 把順序倒過來的；倒回模板後軸 B 才有事實可查。⚠️ 2026-08-16 跨家族查核已【獨立複驗】此點：兩個真實漂移 worktree 在現行順序（目標不存在）下 exit 0，先建後登記時皆由軸 B 擋下 exit 6。承接卡 #91 WF-ASSIGN-REGISTER-AFTER-CREATE1，其代價是把 assign 綁在 worktree 所在機器上、屬需求方取捨，且「本專案單機」是假設而非已驗事實。」；理由 跨家族查核 non-blocking finding 2：卡面「R3-01／R3-02／R4-01 維持未閉合」與正式帳面不符。查核者複驗的帳面狀態是 R3-01 closed、R3-02 superseded_by_requester_ruling、R4-01 open——只有一項是 open，不能統稱三項都未閉合，只能說底層風險未被合併消除。該錯誤句由 PM 於 2026-08-16 op 3eb6ec6f 寫入，屬同一批修正中新引入的不精確宣稱，本次更正。；授權 依需求方 ruan6047 於 https://github.com/ruan6047/ai-workflow/issues/57#issuecomment-5305745859 的裁定（GitHub comment author 已逐字核對，非留言內文自述）。
- 2026-08-16T22:54:45+08:00 handoff by wf-cli → owner 待指派；iteration 6；SHA a5d38439e4fe5bab6f446f55797cfa6801e3d9f6；證據 需求方 2026-08-16 裁定採丙案：本卡不會有 review 事件落地，狀態自 🔍待查核 收回 📥Backlog。診斷：PM 把「這個分支該不該合併」送進查核通道，得到一份長得像查核的回答，卻記不進去——因為它本來就不是查核。契約的第一判準是核心痛點消失了沒（validation.py:268-272 硬擋 core_pain_resolved=no 併 review_result=APPROVE），即查核講的是驗收不是合併決定，而合併決定屬需求方。查核者在收據頭自寫 review_scope: merge-suitability-not-acceptance，那個欄位 schema 不認識，即為此事的證據。⚠️ PM 的操作錯誤有二：(1) 以 handoff --next-stage review 把卡推到 🔍待查核、製造「有一份查核待落地」的預期；(2) 先合併才發現查核事件寫不進去，正確順序是先落事件再合併。兩者已於 issuecomment-5305806507 自陳。分支已合併：PR #93 於 2026-08-16T12:53:15+08:00 squash merge，origin/main = d18cd83，CI 兩個 check 皆 SUCCESS。查核者的實質意見保留為 Issue 留言 issuecomment-5305745859（含密封 source 723 passed、合併樹 944 passed、五檔 Ruff、merge-tree 產出 f65a7ed7457b813546ff53782d23317bc6f45c73 無衝突、兩個真實漂移 worktree 的 exit 6 / exit 0），不進 finding 帳。⚠️ 代價明列：其兩條 non-blocking finding 不入帳。R5-02（finding 狀態帳面不精確）已於 op 7a9c7a0f 修正；R5-01（a5d3843 的 mutation 宣稱過強——整段回退會紅，但只移除兩個限定詞仍綠）無機械落點、會掉，已轉由 #91 承接（#91 本來就要動同一段 docstring）。⚠️ 查核者拒絕貼一份他知道仍然無效的裁決，並診斷出「只補 self_run 無法讓帳成立」——尚有 core_pain_resolved=no 不允許 APPROVE、finding_class: test-adequacy 不在合法列舉、兩條 finding 缺 evidence 與 disposition。三條經 PM 獨立驗實。其提議的「擴充 schema 正式區分合併適用性與驗收」另開卡處理，不卡本卡收帳。。
- 2026-08-26T22:25:49+08:00 amend by wf-cli（op 947dd577）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:ee64097749a8f6fbee75e73b59de76b62f473d842e5b7e6bad5edd11942d3d68 (777 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。
- 2026-08-29T14:58:32+08:00 handoff by wf-cli → owner 待指派；iteration 6；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 阻塞登記（來源狀態 📥Backlog）：https://github.com/ruan6047/ai-workflow/issues/57 之阻塞留言。解除條件＝待審清單機制上線。。


## Comment 5265853866 · 2026-08-12T11:05:28Z

## 派審：#57 `WF-WORKTREE-REPO-OWNERSHIP1` R1

⚠️ 審核對象 **`ruan6047/ai-workflow#57`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-worktree-repo-ownership1
分支：claude/WF-WORKTREE-REPO-OWNERSHIP1　　被審 SHA：1e4888928d29ca061d359bce6087192bbce5f1d1
基線：e8a638c40f1028b6b85f6c59fd12ee9c1e85582d（PM 已重算並驗為祖先）　　iteration：0（首輪）
寫入集：cli/src/wf_cli/registry.py（+372）、cli/tests/test_registry.py（+277）
```

> **權威來源**：本則派審詞與本 Issue Log 最後一筆 `handoff` 事件的 `SHA` **必須一致**。**若你發現兩者不符，以 handoff 事件為準並回報該不符**——PM 本日在 #9 與 #38 上各犯過一次「做了 handoff 卻沒補發派審詞」，其中一位查核者因此審了舊產物，另一位正確拒審。

`origin/main` 現為 **`e1b33d8`**（#53 已於本日合併，pytest 基線由 658 升為 701）。**PM 已實測 merge(e1b33d8, 本分支) 無衝突且 736 passed。** 交付報告寫的 693 是對舊 main `e8a638c` 算的，兩個數字都對，差額 43 全部來自 #53 新增的註冊表測試。

### ⚠️ 先看這個：本卡是交付判定，未交付強制

執行者主動上記錄：**`wfcli` 全域沒有任何 `git worktree add`（實測零命中）**，唯一建立路徑是 `assign` 寫入 `--worktree` 註冊欄那一刻，攔截點在 **`assign_cmd.py`——寫入集外且由 #54 持有**。在 #54 接上前，block 判定**攔不下任何一次真實派工**。已寫進模組頂端 warning 與 commit message。

**請裁定這個形狀能不能算關閉核心痛點**，還是必須連同攔截點一起交付才算。

### 一、它在真實環境找到兩個現在還活著的跨 repo 漂移

**PM 已逐字複驗**：`cpbl-analytics/.claude/worktrees/{wfcli-deploy-state1-execution, re24-prod-rebuild1-execution}` 的 commondir 是 `cpbl-analytics/.git/modules/.ai-workflow`、origin 是 `ai-workflow`，分支 `codex/WFCLI-DEPLOY-STATE1` 與 `codex/DATA-RE24-PROD-REBUILD1`，**卻註冊在 cpbl 的卡上**；而**兩個 repo 的頂層 `git worktree list` 都是 0 命中**——`doctor` 今天不可能發現它們。執行者未動它們，只指名。

**請自行複驗這兩筆**（唯讀：讀 `.git` 檔的 `commondir`、`git -C … remote get-url origin`）。**不要刪除或修改它們。**

### 二、三項規格裁定，各自請攻擊

**（a）卡所屬 repo 只認 Issue URL**，明文拒絕 `--repo`／`.wfcli.json`／`WFCLI_REPO`。理由：那些是**呼叫端的主張**，而漂移形狀正是「人在 A repo 的環境下操作 B repo 的卡」——拿被檢查者的說法當基準，守衛在該擋的那一刻必然恆真通過。

**（b）比對軸是 slug 不是路徑**：worktree 的 repo 由 **commondir 的 origin** 導出。若比路徑，submodule 的 commondir 落在父 repo 的 `.git/modules/` 下會被誤判成父 repo——**上面那兩筆就是活的反例，不是假想**。

**（c）判不出來 → fail-closed，且刻意沒有 `--force` 逃生口。** 三點論證：代價不對稱（誤擋是當場可讀的拒絕且訊息必附合法出路；誤放是沉默錯置、數週後才在**會誤報的**對帳裡浮出）；判不出來的每種輸入都不是合法穩態；fail-closed 不會被無關故障觸發（**守衛不新增任何網路相依**）。不給 `--force` 的理由是「漂移成因不是有人想跨 repo，是沒人注意到自己跨了」。

**請攻擊 (c)**：沒有逃生口意味著判不出來時**無法用任何旗標繼續**。合法但守衛判不出來的情境舉得出來嗎？舉得出來就是 blocking。

### 三、誤報率是窮舉不是抽樣，請覆核方法

磁碟現況 18 個可配對 → **18 allow／0 block**；Project #4 全部 **67 筆 → 64 allow／3 block**，三筆逐一查證無一誤擋（兩筆是上述真陽性、經真實 commondir 證實；**第三筆目錄已不存在、走祖先 proxy，執行者標為未確認、不宣稱真陽性**）。

**對照組值得單獨看**：同一批 18 個，`doctor` 唯讀實跑**全部報孤兒——18/18 vs 0/18**。

**請攻擊**：67 筆是今天的 Project 快照，**不是可重跑的固定 fixture**。這個窮舉明天還成立嗎？以及「祖先 proxy」這條路徑在多少比例的輸入上會被走到？

### 四、registry 的 github 模式與新增的 repo 欄

裁定**需要**，形狀是 **adapter 不是第二介面**；**必須補一欄 `repo`**——TASKS.md Ledger 沒有 repo 欄，**這正是跨 repo 漂移在舊 registry 內不可表達的原因**。該欄已落地，`TasksMdRegistry` 一律留 `None`（不猜）。loader 本體不做，理由是唯一消費者是 #30 與 #54，且把 `gh` 相依塞進純 stdlib 的 registry 會改變 `doctor` 的相依形狀。

### 五、執行者自陳六項無機械執行者，第 3 項有量測

**67 筆中 18 筆是相對路徑**，若操作者 cwd 在錯的 repo，**誤擋從 0 暴增到 19 筆**——「守衛的正確性依賴在對的地方執行指令，而沒有任何東西強制這件事」。**這與 (c) 的 fail-closed 相乘，請判斷合起來的後果。**

第 6 項是唯一真正窮舉的（reason→decision 全表），執行者刻意不寫成「驗回傳值屬枚舉故恆真」——那個形狀本 repo 剛在 #39 上被打過。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5265964235 · 2026-08-12T11:17:01Z

<!-- wf-review-receipt:v1
card_id: WF-WORKTREE-REPO-OWNERSHIP1
source_sha: 1e4888928d29ca061d359bce6087192bbce5f1d1
report_sha256: 0c84c4aee9c8c7f9389d3c68cf26d359277fbbe348e0944e2070e156e63517e7
-->
取材規則：被雜湊文字起點為本規則之後的下一個 <!-- report:start --> 的下一個 LF；終點為本規則之後的下一個 <!-- report:end --> 前一個 LF；UTF-8 編碼、LF 換行、不得 strip；排除收據、取材規則及兩個 delimiter 行。
<!-- report:start -->
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C source-worktree rev-parse HEAD; git status --porcelain; git merge-base --is-ancestor baseline source_sha"
    observed: "HEAD=1e4888928d29ca061d359bce6087192bbce5f1d1，工作區乾淨，基線 e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 是祖先。"
  - command: "git archive source_sha | tar -x -C /private/tmp/aiwf57-review.xtCSMU; cd cli && uv run pytest -q tests/test_registry.py"
    observed: "密封副本的 registry 測試 42 passed。"
  - command: "PYTHONPATH=source/cli/src python -c check_assign_repo_ownership(...live cpbl worktrees...)"
    observed: "兩個真實漂移 worktree 均回傳 repo_mismatch/block，worktree_repo=ruan6047/ai-workflow。"
  - command: "git grep check_assign_repo_ownership source_sha -- cli/src/wf_cli，並讀 commands/assign_cmd.py"
    observed: "判定函式僅在 registry.py 定義與匯出；assign_cmd.py 在 set_field_value 前沒有呼叫，無攔截執行者。"
findings:
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R1-01"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: planner
    root_cause_id: "worktree-repo-ownership"
    evidence: "核心痛點要求在建立當下擋下；source 的 registry.py 明載判定不等於強制，且 source_sha 的 assign_cmd.py 沒有 check_assign_repo_ownership 呼叫，派工仍直接寫 owner、worktree、status。"
    disposition: "修正卡切分與交付範圍：同一可驗證交付必須在真正 assign 攔截點於任何寫入前執行判定並非零拒絕，或將本卡改為純判定引擎且不得宣稱核心痛點已解。"
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R1-02"
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: "worktree-repo-ownership"
    evidence: "probe_worktree_repo 對不存在目標改問最近存在祖先；絕對路徑位於 repo 外的合法新 worktree 會落到 /tmp 類非 git 祖先，得到 worktree_repo_undeterminable/block，且沒有 escape hatch。canonical §4.5 明定 worktree 路徑由實際建立者決定，未限定必須巢狀於 repo。相對路徑又預設 Path.cwd，程式自身承認 cwd 錯置會把合法配置誤擋。"
    disposition: "在接入 assign 前定義並實作可判定的目標 repo 語意，例如由實際 git worktree add 的來源 repo 或經驗證的明確 repo root 導出，支援 repo 外絕對目標；相對路徑必須綁定明確 base_dir，並加入此合法案例的回歸測試。"
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R1-03"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: "worktree-repo-ownership"
    evidence: "交付宣稱 67 筆與 18 個現況窮舉，但 source_sha 沒有產生該清單或結果的工具及 artifact；test_registry.py 僅建立暫時兩 repo，不能重跑 Project 快照或驗證既有全部配置。canonical §6.2 要求全部宣稱由指令輸出及同 HEAD 可重現 artifact 支持。"
    disposition: "交付可重跑的唯讀枚舉器與釘住輸入或足以重建輸入的來源，將每筆 path、issue URL、derived slug、reason 與決定列入可檢核輸出；以此取代 commit message 的不可重跑數字。"

## 前輪 accepted blocking finding 閉環

首輪，無前輪 accepted blocking finding。

## 逐項驗收

- 建立當下的預防：未通過；判定引擎未接入唯一派工寫入路徑。
- registry 的 GitHub 模式：僅有 adapter 形狀裁定與 repo 欄；沒有 loader，且不能補足未接入的預防。
- 既有 doctor 誤報隔離：引擎簽章確實未讀 TASKS.md，但因沒有執行者，不能視為活守衛的驗證。
- 真實跨 repo 情境：引擎對兩個真實漂移 worktree 均回傳 block；尚未證明 wfcli 派工會拒絕。
- 現有全部 worktree 的誤報率：未通過；67 筆與 18 筆的數字沒有同 HEAD 可重跑的輸入與輸出 artifact。

## 範圍外發現

- 無。
<!-- report:end -->

## Comment 5266086951 · 2026-08-12T11:25:47Z

<!-- wf-review-event:v1 card_id=WF-WORKTREE-REPO-OWNERSHIP1 source_sha=1e4888928d29ca061d359bce6087192bbce5f1d1 attempt_id=WF-WORKTREE-REPO-OWNERSHIP1-e0-1e4888928d29ca061d359bce6087192bbce5f1d1 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-WORKTREE-REPO-OWNERSHIP1`　attempt_id：`WF-WORKTREE-REPO-OWNERSHIP1-e0-1e4888928d29ca061d359bce6087192bbce5f1d1`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5265964235，PM 回讀重算相符、未經編輯、marker 字面 0）　escalation_epoch：0
- source_sha：`1e4888928d29ca061d359bce6087192bbce5f1d1`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T19:25:45+08:00

### self_run（查核者實跑）

- `git -C source-worktree rev-parse HEAD; git status --porcelain; git merge-base --is-ancestor baseline source_sha`
  - HEAD=1e4888928d29ca061d359bce6087192bbce5f1d1，工作區乾淨，基線 e8a638c 是祖先。
- `git archive source_sha | tar -x -C /private/tmp/aiwf57-review.xtCSMU; cd cli && uv run pytest -q tests/test_registry.py`
  - 密封副本的 registry 測試 42 passed。
- `PYTHONPATH=source/cli/src python -c check_assign_repo_ownership(...live cpbl worktrees...)`
  - 兩個真實漂移 worktree 均回傳 repo_mismatch/block，worktree_repo=ruan6047/ai-workflow。
- `git grep check_assign_repo_ownership source_sha -- cli/src/wf_cli，並讀 commands/assign_cmd.py`
  - 判定函式僅在 registry.py 定義與匯出；assign_cmd.py 在 set_field_value 前沒有呼叫，無攔截執行者。

### findings（3，其中 blocking 3）

- **WF-WORKTREE-REPO-OWNERSHIP1-R1-01**　severity=major　blocking=true　class=authoritative-artifact　attribution=planner　root_cause_id=`worktree-repo-ownership`
  - evidence：核心痛點要求在建立當下擋下；source 的 registry.py 明載判定不等於強制，且 source_sha 的 assign_cmd.py 沒有 check_assign_repo_ownership 呼叫，派工仍直接寫 owner、worktree、status。
  - disposition：修正卡切分與交付範圍：同一可驗證交付必須在真正 assign 攔截點於任何寫入前執行判定並非零拒絕，或將本卡改為純判定引擎且不得宣稱核心痛點已解。
- **WF-WORKTREE-REPO-OWNERSHIP1-R1-02**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`worktree-repo-ownership`
  - evidence：probe_worktree_repo 對不存在目標改問最近存在祖先；絕對路徑位於 repo 外的合法新 worktree 會落到 /tmp 類非 git 祖先，得到 worktree_repo_undeterminable/block，且沒有 escape hatch。canonical §4.5 明定 worktree 路徑由實際建立者決定，未限定必須巢狀於 repo。相對路徑又預設 Path.cwd，程式自身承認 cwd 錯置會把合法配置誤擋。
  - disposition：在接入 assign 前定義並實作可判定的目標 repo 語意，例如由實際 git worktree add 的來源 repo 或經驗證的明確 repo root 導出，支援 repo 外絕對目標；相對路徑必須綁定明確 base_dir，並加入此合法案例的回歸測試。
- **WF-WORKTREE-REPO-OWNERSHIP1-R1-03**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`worktree-repo-ownership`
  - evidence：交付宣稱 67 筆與 18 個現況窮舉，但 source_sha 沒有產生該清單或結果的工具及 artifact；test_registry.py 僅建立暫時兩 repo，不能重跑 Project 快照或驗證既有全部配置。canonical §6.2 要求全部宣稱由指令輸出及同 HEAD 可重現 artifact 支持。
  - disposition：交付可重跑的唯讀枚舉器與釘住輸入或足以重建輸入的來源，將每筆 path、issue URL、derived slug、reason 與決定列入可檢核輸出；以此取代 commit message 的不可重跑數字。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5266614483 · 2026-08-12T12:10:00Z

## 需求方裁定（2026-08-12）：接線納入本卡，並定案 `--worktree` 的路徑慣例

> ⚠️ **本則留言的來歷**：內容由需求方 `ruan6047` 明確核准，**文字由 PM（Claude Opus 5@Claude Code）代擬並代貼**。PM 的 `gh` 以 `ruan6047` 認證，故任何以 comment author 為據的授權檢查對 PM **恆真、無區辨力**。此限度已於 `WF-AMEND-AUTHZ-BINDING1`（#62）開卡承接——該卡要修的正是「授權欄宣稱了一件它證明不了的事」。**本則的實質授權是真的，其機械證明是空的。**

### 一、`cli/src/wf_cli/commands/assign_cmd.py` 移入本卡寫入集

R1-01 的兩條路中採 **(a)**，理由採納執行者的論證：**(b) 會讓強制變成無主**。`WF-CLI-RESUME1`（#54）的驗收條全是首寫自描述與 `resume`，跨 repo 歸屬閘門塞進去是範圍外擴張——依 §6.1 第 1 條，#54 的執行者正確做法是寫報告回祕書而**不是**順手做。所以 (b) 的實際效果不是延後交付，是這件事沒有任何一張卡的驗收條在管它。

互斥不成立的依據是專案自己的規則：`assign_cmd.py:118-124` 連同其模組 docstring 逐字裁定「**未認領的卡其資源宣告不保留資源**」，而 #54 現為 `owner: 待指派`。#54 的宣告仍會一併撤下該檔，避免它日後被指派時才撞上。

連帶納入 `cli/tests/test_commands_mocked.py` 與 `cli/tests/test_release_cleanup.py`——執行者在拋棄式樹的接線原型實測 **23 個既有測試被閘門當場拒絕**（`9 failed, 727 passed, 14 errors`），那 23 個 fixture 要補上真 Issue URL 與可判定的 worktree 路徑。**代價已量化，不是 drop-in，裁定在知情下作出。**

### 二、`--worktree` 的路徑慣例：一律絕對路徑，或明示來源 repo

閘門接上後，相對路徑的 `--worktree` 會被拒（reason `worktree_path_unanchored`）。今天 62 筆註冊中 **14 筆是相對路徑**，全屬既有卡。

**裁定**：新的 `assign` 一律給**絕對路徑**；若確實從別的 repo 執行 `git worktree add`，以 `--worktree-source-repo` 明示。

判準是執行者查出的 git 真語意：`git -C <src> worktree add <任意路徑>` 產生的 worktree **永遠屬於 `<src>`，與目標落在磁碟哪裡無關**。既然歸屬不由路徑決定，要求路徑可錨定就不是額外負擔，而是讓判定有據。

**既有 14 筆不回溯檢查**——它們是已寫入的狀態面，本裁定只約束新的寫入。

### 三、需求方明確知悉且接受的代價

- 派工指令變長（絕對路徑）。
- 判定為 `inferred` 的那 28 筆 allow **不構成「守衛不誤擋合法配置」的證據**，執行者已自陳，本裁定不因採納 (a) 而視為已解決。
- **核心痛點在接線落地前仍然開著。** 模組頂端的 `danger` 逐字寫「在接線前，任何『已預防／會擋下』的宣稱都是假的」——該句在本輪交付前不得移除。


## Comment 5267615503 · 2026-08-12T13:41:51Z

## 派審：#57 `WF-WORKTREE-REPO-OWNERSHIP1` R2

⚠️ 審核對象 **`ruan6047/ai-workflow#57`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-worktree-repo-ownership1
分支：claude/WF-WORKTREE-REPO-OWNERSHIP1　　被審 SHA：5575f82995f1d93e63d62056bd80c3c74c4869f6
基線：e8a638c40f1028b6b85f6c59fd12ee9c1e85582d　　iteration：1
寫入集（卡面已 amend，op 2bf9ffaf）：registry.py、test_registry.py、commands/assign_cmd.py、test_commands_mocked.py、test_release_cleanup.py
```

> **權威來源**：本則與 Log 最後一筆 `handoff` 的 `SHA` 必須一致；不符時**以 handoff 事件為準並回報**。

**PM 自審**：遠端 tip 相符、`1a1d9df` 是祖先（非 force）、對 main `merge-tree` **CLEAN**、相對基線寫入集**五檔逐項對上 amend 後的宣告零逸出**、trailer 三件齊備、合併樹 `2677a98` 實測 **755 passed**。

### 零、卡面已擴張寫入集，這是需求方裁定的結果

R1-01（`attribution: planner`）判定判定引擎未接入 assign 攔截點。執行者選 (a) 真正接線並**實測代價**：接上後 `9 failed, 727 passed, 14 errors`——**23 個既有測試被閘門當場拒絕**，訊息為真。需求方據此裁定（`issuecomment-5266614483`）把 `assign_cmd.py` 自 #54 移入本卡（#54 已撤下宣告，op `dc04bcd5`），連帶納入兩個測試檔，**並定案 `--worktree` 路徑慣例：新的 assign 一律絕對路徑，或以 `--worktree-source-repo` 明示；既有 14 筆相對路徑不回溯檢查。**

該裁定留言由 PM 代擬代貼、需求方核准，事實寫在留言開頭（`amend` 的 author 檢查對 PM 恆真，已開卡 #62 承接）。

### 一、R1-01：接線本體

閘門在**任何** `set_field_value`／`set_item_body` 之前呼叫 `check_assign_repo_ownership`，`blocked` 印 `refusal_message()` 並 `return 5`。位置排在能力閘門之後、資源交集檢查之前。

`--worktree-source-repo` **已真的註冊**（原型漏了，等於出路只存在於文件裡），並有專測釘住旗標存在且省略時為 `None` 而非空字串。

新增 5 條閘門專測，其中 `test_assign_blocks_cross_repo_worktree_before_any_mutation` 用 `_RecordingRunner` 證明**整條拒絕路徑零 mutation**——**閘門若排錯位置這條會紅**。

**請攻擊**：這 5 條是不是同一個機制的 5 種寫法？以及 `test_assign_allows_absolute_worktree_under_the_card_repo` 是唯一的「不誤擋」正面證據，**一條夠嗎**？

### 二、⚠️ 14 個測試的處置是一個淨損失，執行者自己這樣標

`test_release_cleanup.py` 的 14 個 error **沒有讓它們通過閘門**，而是把 assign 從 fixture 拿掉、改直接寫註冊欄。

理由（已寫進該處註解）：該檔沙箱 repo 必須 push 得出去，origin 只能是 `tmp_path` 底下的 bare 路徑、導不出 `owner/repo`，**閘門正確地 fail-closed**；給 `--worktree-source-repo` 救不了（來源 repo 就是同一個沙箱）；偽造 GitHub 形狀的 origin 會讓 `cleanup.py` 的 `ls-remote`／`push --delete` **打向真實網路**（已實測 `url.insteadOf` 連 `git remote get-url` 一起改寫、`pushInsteadOf` 只救 push）。

**代價執行者自己記了：本檔不再覆蓋 `assign` 這條指令路徑**，改由 `test_commands_mocked.py` 與 `test_registry.py` 專測承擔。它並自陳**證明不了那 14 個測試在真實 assign 路徑下仍等價**。

**請判斷這個取捨。** 這是本輪最可能被判不足的一點。

### 三、R1-02：執行者承認自己上一輪錯了，並找到更上游的根源

它上一輪寫「判不出來的每種輸入都不是合法穩態」——**它現在說那是錯的**，你的反例成立。根源在更上游：舊版把「worktree 屬於哪個 repo」當**路徑座落**問題，而 git 的真語意是 `git -C <src> worktree add <任意路徑>` 產生的 worktree **永遠屬於 `<src>`，與目標落在磁碟哪裡無關**。

改為三級權威導出（`source_repo` 須經 git 驗證／`target_dir` 是事實／`ancestor_dir` 標 `inferred=True`）。**`Path.cwd()` 從判定路徑完全移除**，新增 `worktree_path_unanchored`，並以 `monkeypatch.chdir` 把「cwd 錯置誤擋暴增」那條自陳**機械封死**——若還讀 cwd 會得到 `repo_mismatch`，實得 `worktree_path_unanchored`。

`source_repo` **不是 `--force`**：`test_source_repo_is_not_a_force_flag` 證明給錯來源 repo 照樣 `repo_mismatch/block`。

### 四、R1-03：唯讀枚舉器

`python -m wf_cli.registry`，`--input` 重播**不動點實證**：兩次輸出 `cmp` 逐位元組相同、sha256 一致。實跑摘要 `total 62 / allow 45 / block 17 / target_exists 19 / inferred 29`。

**它不替上一輪的 67／18 辯護**：「差異是看板變動還是原始計數有誤，**無從判斷——因為沒有留下任何 artifact，這正是 R1-03 的論點本身**」。

順帶抓到一個真實資料缺陷：Project 的 `分支worktree` 欄存的是 markdown code span（外包反引號），不剝會讓既存目錄被判成不存在。

### 五、自陳七項，第 4 項是核心

接線後**有了機械執行者，但射程三條硬邊界**（全寫進 `registry.py` 頂端 warning）：只管新寫入不回溯；**只守 assign 一個入口——人直接在 shell 跑 `git worktree add` 完全不經過 `wfcli`，閘門擋的是「登記」不是「建立」**；`origin` 非 GitHub 形狀的 repo 一律過不了。

第 2 項亦更新：那 28 筆 `inferred` 的 allow **性質一字未變**，仍不構成「守衛不誤擋合法配置」的證據。

### 六、兩件環境事實

1. ⚠️ **你會再次讀到 `cpbl-analytics` 底下兩個真實跨 repo 漂移 worktree。只讀不動**——不得刪除、修改或 `git worktree prune`。執行者本輪亦只讀（`rev-parse`／`remote get-url`），`git worktree list` 仍 21。
2. **執行者主動報備** `cli/tests/test_commands_mocked.py:290` 有一處**既存**的事件 marker 前綴字面（`git log -S` 追到 `26a0149`，非本輪引入、不在其 diff 內）。因該檔現在在其寫入集內故報備，**未動它**。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5267827318 · 2026-08-12T13:59:38Z

<!-- wf-review-receipt:v1
card_id: WF-WORKTREE-REPO-OWNERSHIP1
source_sha: 5575f82995f1d93e63d62056bd80c3c74c4869f6
report_sha256: 29028fd89066e1ac245ab3c67a726075242c4e7e10ab30d2e3dbb567368cb547
-->
取材規則：被雜湊文字起點為本規則之後的下一個 <!-- report:start --> 的下一個 LF；終點為本規則之後的下一個 <!-- report:end --> 前一個 LF；UTF-8 編碼、LF 換行、不得 strip；排除收據、取材規則及兩個 delimiter 行。
<!-- report:start -->
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "gh issue view 57 --repo ruan6047/ai-workflow --json body -q .body | grep 'handoff by wf-cli' | tail -1; git -C source-worktree rev-parse HEAD; git -C source-worktree merge-base --is-ancestor e8a638c40f1028b6b85f6c59fd12ee9c1e85582d HEAD"
    observed: "最後 handoff 與 HEAD 均為 5575f82995f1d93e63d62056bd80c3c74c4869f6；fork point 祖先檢查成功。"
  - command: "git archive 5575f82995f1d93e63d62056bd80c3c74c4869f6 | tar -x -C /tmp/aiwf57-audit.MXHfQn; cd /tmp/aiwf57-audit.MXHfQn/cli && uv run pytest -q"
    observed: "密封副本完整測試 712 passed in 44.32s。"
  - command: "cd /tmp/aiwf57-audit.MXHfQn/cli && LC_ALL=C uv run pytest -q tests/test_registry.py tests/test_commands_mocked.py -k 'ownership or cross_repo or source_repo or unanchored or worktree_source or absolute_worktree or relative_worktree'; LC_ALL=en_US.UTF-8 uv run pytest -q tests/test_registry.py tests/test_commands_mocked.py -k 'ownership or cross_repo or source_repo or unanchored or worktree_source or absolute_worktree or relative_worktree'"
    observed: "C 與 UTF-8 locale 各為 15 passed。"
  - command: "cd /tmp/aiwf57-audit.MXHfQn/cli && uv run python -m wf_cli.registry --from-project ruan6047/4 --output /tmp/aiwf57-project.json; uv run python -m wf_cli.registry --input /tmp/aiwf57-project.json --output /tmp/aiwf57-replay.json; cmp /tmp/aiwf57-project.json /tmp/aiwf57-replay.json; shasum -a 256 /tmp/aiwf57-project.json /tmp/aiwf57-replay.json"
    observed: "兩份產物逐位元組相同，SHA256 均為 5bfa8350ea98c8548afe1a1a33a3708b4086dcede159246a592cd5438d1ca314；現況 total 63、allow 46、block 17。"
  - command: "cd /tmp/aiwf57-audit.MXHfQn/cli && uv run python -c live_cross_repo_probe"
    observed: "兩個 cpbl-analytics 路徑的真實漂移均得到 block、repo_mismatch、card_repo ruan6047/cpbl-analytics、worktree_repo ruan6047/ai-workflow。"
prior_round_closure:
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R1-01"
    status: "closed"
    evidence: "assign_cmd.py 在所有 set_field_value 與 set_item_body 前呼叫 check_assign_repo_ownership；test_assign_blocks_cross_repo_worktree_before_any_mutation 以 recording runner 驗證拒絕路徑零 mutation。"
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R1-02"
    status: "closed"
    evidence: "source_repo、target_dir、ancestor_dir 三級導出已落地；repo 外絕對目標加 source_repo 的正面案例、錯誤 source_repo 的拒絕案例，以及 cwd 不參與判定的回歸測試均通過。"
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R1-03"
    status: "closed"
    evidence: "python -m wf_cli.registry 已可唯讀枚舉與 --input 重播；本次從 Project #4 取得 63 列後重播 cmp 成功且兩份 SHA256 相同。"
findings:
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R2-01"
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: "worktree-repo-ownership"
    evidence: "assign_cmd.py:143-146 只把 args.worktree_source_repo 傳入判定函式；registry.py 的 probe_worktree_repo 在 source_repo 存在時只以唯讀 git 查該目錄的 origin，沒有執行或觀測 git worktree add，也沒有把後續建立動作綁到該來源。故操作者可在 assign 時給與卡相符的 source_repo 而獲 allow，之後從另一個 repo 直接執行 git worktree add；本卡 Log 亦明載直接 shell 執行不經 wfcli，閘門只擋登記而非建立。這保留了核心痛點所述的錯 repo worktree 建立路徑。"
    disposition: "將實際 git worktree add 納入同一受控入口，或以可驗證的建立事件把其來源 repo 與已核准 assign 記錄綁定並在不符時拒絕登記或交接；補一個端到端測試，先以相符 source_repo 通過 assign、再以不同來源 repo 嘗試建立同一路徑，必須被拒絕且無可採信的註冊。若需求方將範圍明確改為僅保護登記而非建立，須同步修正卡的服務原始目標與核心痛點，不能宣稱已在建立當下預防。"
scope_outside_findings:
  - note: "Project #4 目前枚舉 63 列而非 handoff 摘要的 62 列，屬查核時看板變動；枚舉器產物內含輸入並可重播，未將數量差異納入 finding。"
  - note: "密封副本未安裝 ruff，uv run ruff check 回報 executable 不存在；pytest 與 locale 驗證仍可完成，未視為 source finding。"
<!-- report:end -->

## Comment 5267837844 · 2026-08-12T14:00:32Z

<!-- wf-review-receipt:v1
card_id: WF-WORKTREE-REPO-OWNERSHIP1
source_sha: 5575f82995f1d93e63d62056bd80c3c74c4869f6
report_sha256: 3cccc220095f288d86ab08646344a3d645f70fc3be3a51070286b4a0555f1291
-->
取材規則：被雜湊文字起點為本規則之後的下一個 <!-- report:start --> 的下一個 LF；終點為本規則之後的下一個 <!-- report:end --> 前一個 LF；UTF-8 編碼、LF 換行、不得 strip；排除收據、取材規則及兩個 delimiter 行。
<!-- report:start -->
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "gh issue view 57 --repo ruan6047/ai-workflow --json body -q .body | grep 'handoff by wf-cli' | tail -1; git -C source-worktree rev-parse HEAD; git -C source-worktree merge-base --is-ancestor e8a638c40f1028b6b85f6c59fd12ee9c1e85582d HEAD"
    observed: "最後 handoff 與 HEAD 均為 5575f82995f1d93e63d62056bd80c3c74c4869f6；fork point 祖先檢查成功。"
  - command: "git archive 5575f82995f1d93e63d62056bd80c3c74c4869f6 | tar -x -C /tmp/aiwf57-audit.MXHfQn; cd /tmp/aiwf57-audit.MXHfQn/cli && uv run pytest -q"
    observed: "密封副本完整測試 712 passed in 44.32s。"
  - command: "cd /tmp/aiwf57-audit.MXHfQn/cli && LC_ALL=C uv run pytest -q tests/test_registry.py tests/test_commands_mocked.py -k 'ownership or cross_repo or source_repo or unanchored or worktree_source or absolute_worktree or relative_worktree'; LC_ALL=en_US.UTF-8 uv run pytest -q tests/test_registry.py tests/test_commands_mocked.py -k 'ownership or cross_repo or source_repo or unanchored or worktree_source or absolute_worktree or relative_worktree'"
    observed: "C 與 UTF-8 locale 各為 15 passed。"
  - command: "cd /tmp/aiwf57-audit.MXHfQn/cli && uv run python -m wf_cli.registry --from-project ruan6047/4 --output /tmp/aiwf57-project.json; uv run python -m wf_cli.registry --input /tmp/aiwf57-project.json --output /tmp/aiwf57-replay.json; cmp /tmp/aiwf57-project.json /tmp/aiwf57-replay.json; shasum -a 256 /tmp/aiwf57-project.json /tmp/aiwf57-replay.json"
    observed: "兩份產物逐位元組相同，SHA256 均為 5bfa8350ea98c8548afe1a1a33a3708b4086dcede159246a592cd5438d1ca314；現況 total 63、allow 46、block 17。"
  - command: "cd /tmp/aiwf57-audit.MXHfQn/cli && uv run python -c live_cross_repo_probe"
    observed: "兩個 cpbl-analytics 路徑的真實漂移均得到 block、repo_mismatch、card_repo ruan6047/cpbl-analytics、worktree_repo ruan6047/ai-workflow。"
prior_round_closure:
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R1-01"
    status: "closed"
    evidence: "assign_cmd.py 在所有 set_field_value 與 set_item_body 前呼叫 check_assign_repo_ownership；test_assign_blocks_cross_repo_worktree_before_any_mutation 以 recording runner 驗證拒絕路徑零 mutation。"
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R1-02"
    status: "closed"
    evidence: "source_repo、target_dir、ancestor_dir 三級導出已落地；repo 外絕對目標加 source_repo 的正面案例、錯誤 source_repo 的拒絕案例，以及 cwd 不參與判定的回歸測試均通過。"
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R1-03"
    status: "closed"
    evidence: "python -m wf_cli.registry 已可唯讀枚舉與 --input 重播；本次從 Project #4 取得 63 列後重播 cmp 成功且兩份 SHA256 相同。"
findings:
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R2-01"
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: "worktree-repo-ownership"
    evidence: "assign_cmd.py:143-146 只把 args.worktree_source_repo 傳入判定函式；registry.py 的 probe_worktree_repo 在 source_repo 存在時只以唯讀 git 查該目錄的 origin，沒有執行或觀測 git worktree add，也沒有把後續建立動作綁到該來源。故操作者可在 assign 時給與卡相符的 source_repo 而獲 allow，之後從另一個 repo 直接執行 git worktree add；本卡 Log 亦明載直接 shell 執行不經 wfcli，閘門只擋登記而非建立。這保留了核心痛點所述的錯 repo worktree 建立路徑。"
    disposition: "將實際 git worktree add 納入同一受控入口，或以可驗證的建立事件把其來源 repo 與已核准 assign 記錄綁定並在不符時拒絕登記或交接；補一個端到端測試，先以相符 source_repo 通過 assign、再以不同來源 repo 嘗試建立同一路徑，必須被拒絕且無可採信的註冊。若需求方將範圍明確改為僅保護登記而非建立，須同步修正卡的服務原始目標與核心痛點，不能宣稱已在建立當下預防。"
scope_outside_findings:
  - note: "Project #4 目前枚舉 63 列而非 handoff 摘要的 62 列，屬查核時看板變動；枚舉器產物內含輸入並可重播，未將數量差異納入 finding。"
  - note: "密封副本未安裝 ruff，uv run ruff check 回報 executable 不存在；pytest 與 locale 驗證仍可完成，未視為 source finding。"
<!-- report:end -->

## Comment 5268180933 · 2026-08-12T14:29:02Z

<!-- wf-review-event:v1 card_id=WF-WORKTREE-REPO-OWNERSHIP1 source_sha=5575f82995f1d93e63d62056bd80c3c74c4869f6 attempt_id=WF-WORKTREE-REPO-OWNERSHIP1-e0-5575f82995f1d93e63d62056bd80c3c74c4869f6 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-WORKTREE-REPO-OWNERSHIP1`　attempt_id：`WF-WORKTREE-REPO-OWNERSHIP1-e0-5575f82995f1d93e63d62056bd80c3c74c4869f6`
- 查核者：GPT-5@Codex 子代理（需求方轉貼）；⚠️ 本卡收到兩則收據 issuecomment-5267827318 與 5267837844，需求方轉貼時稱前者「雜湊不符」——PM 逐一驗算後**該描述不成立**：兩則的雜湊各自都對得上自己的取材規則，且被雜湊內容逐位元組相同（sha 3cccc220095f288d、3503 bytes），為純重試無歧義。轉錄採 5267837844　escalation_epoch：0
- source_sha：`5575f82995f1d93e63d62056bd80c3c74c4869f6`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T22:29:00+08:00

### self_run（查核者實跑）

- `gh issue view 57 --repo ruan6047/ai-workflow --json body -q .body | grep 'handoff by wf-cli' | tail -1; git -C source-worktree rev-parse HEAD; git -C source-worktree merge-base --is-ancestor e8a638c40f1028b6b85f6c59fd12ee9c1e85582d HEAD`
  - 最後 handoff 與 HEAD 均為 5575f82995f1d93e63d62056bd80c3c74c4869f6；fork point 祖先檢查成功。
- `git archive 5575f82995f1d93e63d62056bd80c3c74c4869f6 | tar -x -C /tmp/aiwf57-audit.MXHfQn; cd /tmp/aiwf57-audit.MXHfQn/cli && uv run pytest -q`
  - 密封副本完整測試 712 passed in 44.32s。
- `cd /tmp/aiwf57-audit.MXHfQn/cli && LC_ALL=C uv run pytest -q tests/test_registry.py tests/test_commands_mocked.py -k 'ownership or cross_repo or source_repo or unanchored or worktree_source or absolute_worktree or relative_worktree'; LC_ALL=en_US.UTF-8 uv run pytest -q tests/test_registry.py tests/test_commands_mocked.py -k 'ownership or cross_repo or source_repo or unanchored or worktree_source or absolute_worktree or relative_worktree'`
  - C 與 UTF-8 locale 各為 15 passed。
- `cd /tmp/aiwf57-audit.MXHfQn/cli && uv run python -m wf_cli.registry --from-project ruan6047/4 --output /tmp/aiwf57-project.json; uv run python -m wf_cli.registry --input /tmp/aiwf57-project.json --output /tmp/aiwf57-replay.json; cmp /tmp/aiwf57-project.json /tmp/aiwf57-replay.json; shasum -a 256 /tmp/aiwf57-project.json /tmp/aiwf57-replay.json`
  - 兩份產物逐位元組相同，SHA256 均為 5bfa8350ea98c8548afe1a1a33a3708b4086dcede159246a592cd5438d1ca314；現況 total 63、allow 46、block 17。
- `cd /tmp/aiwf57-audit.MXHfQn/cli && uv run python -c live_cross_repo_probe`
  - 兩個 cpbl-analytics 路徑的真實漂移均得到 block、repo_mismatch、card_repo ruan6047/cpbl-analytics、worktree_repo ruan6047/ai-workflow。

### findings（1，其中 blocking 1）

- **WF-WORKTREE-REPO-OWNERSHIP1-R2-01**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`worktree-repo-ownership`
  - evidence：assign_cmd.py:143-146 只把 args.worktree_source_repo 傳入判定函式；registry.py 的 probe_worktree_repo 在 source_repo 存在時只以唯讀 git 查該目錄的 origin，沒有執行或觀測 git worktree add，也沒有把後續建立動作綁到該來源。故操作者可在 assign 時給與卡相符的 source_repo 而獲 allow，之後從另一個 repo 直接執行 git worktree add；本卡 Log 亦明載直接 shell 執行不經 wfcli，閘門只擋登記而非建立。這保留了核心痛點所述的錯 repo worktree 建立路徑。
  - disposition：將實際 git worktree add 納入同一受控入口，或以可驗證的建立事件把其來源 repo 與已核准 assign 記錄綁定並在不符時拒絕登記或交接；補一個端到端測試，先以相符 source_repo 通過 assign、再以不同來源 repo 嘗試建立同一路徑，必須被拒絕且無可採信的註冊。若需求方將範圍明確改為僅保護登記而非建立，須同步修正卡的服務原始目標與核心痛點，不能宣稱已在建立當下預防。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5268265532 · 2026-08-12T14:35:51Z

## 需求方裁定（2026-08-12）：本卡射程縮為「保護登記」，建立面另開卡

> ⚠️ 內容由需求方 `ruan6047` 明確核准，**文字由 PM 代擬並代貼**。PM 的 `gh` 以 `ruan6047` 認證，故 comment author 檢查對 PM **恆真、無區辨力**（已由 #62 承接）。實質授權是真的，機械證明是空的。

針對 `R2-01`（major、blocking、implementation、`root_cause_id: worktree-repo-ownership`）。查核者給了兩條路，需求方採**第二條**：

> 若需求方將範圍明確改為僅保護登記而非建立，**須同步修正卡的服務原始目標與核心痛點，不能宣稱已在建立當下預防**。

### 裁定

**本卡射程為：在 `assign` 登記 worktree 歸屬的當下攔截跨 repo 錯置。不涵蓋 `git worktree add` 的建立行為。**

### 理由

**一、把建立納入受控入口是新能力，不是修復。** `wfcli` 全域沒有任何 `git worktree add`（執行者實測零命中）。要讓它擁有建立，等於新增一個動詞與其守衛——那是 `WF-CLI-*` 系列的形狀，不是本卡兩輪查核在處理的東西。硬塞進來會讓本卡第三輪還在長。

**二、登記面本身有真實價值，且已被證明。** 執行者實測兩個真實漂移 worktree 皆得 `block/repo_mismatch`，而**兩個 repo 的頂層 `git worktree list` 都是 0 命中**——`doctor` 今天不可能發現它們。登記是「卡 ↔ worktree 歸屬」成為事實的那一刻，守住它不是無意義的。

**三、誠實優先於完整。** 維持原核心痛點（「建立當下擋下」）而只交付登記面，就是 `R1-01` 被判 blocking 的那個形狀。**縮小射程是承認限制，不是規避。**

### 因此須同步修正的兩處（PM 執行）

- **服務的原始目標**：由「在建立當下被擋」改為「在登記歸屬的當下被擋」
- **核心痛點**：明寫本卡不涵蓋建立行為，並指名承接卡

### 承接

建立面另開卡。**該卡未落地前，本 repo 對「人直接在 shell 跑 `git worktree add` 建到錯的 repo」沒有任何預防**——這一句須逐字保留在 `registry.py` 頂端的 danger 區塊，不得因本裁定而軟化。

### 明確不涵蓋

本裁定**不放寬** `R2-01` 以外的任何項目，也不改變三項前輪 blocking 已被判 `closed` 的狀態。


## Comment 5273458293 · 2026-08-12T22:21:29Z

## 派審：#57 `WF-WORKTREE-REPO-OWNERSHIP1` R3

⚠️ 審核對象 **`ruan6047/ai-workflow#57`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-worktree-repo-ownership1
分支：claude/WF-WORKTREE-REPO-OWNERSHIP1　　被審 SHA：544e162b736a681532f49744f6a7fdfb2b79d96f
基線：e8a638c40f1028b6b85f6c59fd12ee9c1e85582d（PM 已重算並驗為祖先）　　iteration：2
寫入集：assign_cmd.py、registry.py、test_registry.py、test_commands_mocked.py、test_release_cleanup.py（本輪只動前四檔）
```

> **權威來源**：本則與 Log 最後一筆 `handoff` 的 `SHA` 必須一致；不符時**以 handoff 事件為準並回報**。

**先讀 `docs/ROADMAP.md`（在 `origin/main` 上），它比本則權威。**

**PM 自審**：遠端 tip 相符、`5575f82` 是祖先（非 force）、對 main `merge-tree` **CLEAN**、寫入集在卡面宣告之內、trailer 3/3。

### 零、⚠️ 卡面核心痛點已被需求方 amend，射程縮了

R2-01 判定閘門只擋登記不擋建立。查核者給兩條路，需求方採第二條（`issuecomment-5268265532`）：**射程明確改為僅保護登記**，並依查核者要求同步修正核心痛點與服務原始目標。**本輪是讓交付物與縮小後的射程一致，不是重新爭論射程。**

### 一、⚠️ 執行者正面回答了「縮射程後核心痛點真的關閉了嗎」——答案是沒有

PM 在派工詞裡指定它必須回答這一題，理由是**需求方縮的是射程，不是降低對射程內那件事的要求**。它的答案：

> **沒有完全關閉。縮射程之後，登記面本身仍有一個同形狀的缺口，而它在射程內。**
>
> `分支worktree` 是 GitHub Project 的 TEXT 欄，在 web UI、`gh project item-edit`、GraphQL 都可直接改寫。「唯一寫入通道＝wfcli」是 2026-08-04 的**慣例，不是機制**——這與 `git worktree add` 繞過閘門是**完全相同的形狀**，只是發生在登記面而非建立面。**裁定把建立面移出射程，沒有把這一個移出去。**

它自陳無法為它加執行者，依 ROADMAP §2：**Project 的欄位權限是 setting，不是檔案、不在資源模型的值域裡、不可能被宣告進任何寫入集。**

另兩項未閉合（皆射程內）：**既有 17 筆 block 判定永遠不被重掃**（枚舉器列得出但無執行者、無排程——依 ROADMAP §0「沒有執行者的偵測器不算達成目標 1」）；**46 筆 allow 裡 31 筆是 `ancestor_dir` 推測**，不是事實。

**它的自評是「部分閉合」，並明說「若查核者依此判 `core_pain_resolved: no`，我不反駁」。**

**請正面裁示。** 兩個方向都正當：一個是縮射程後射程內仍未閉合故 `no`；另一個是「經 wfcli 的新登記已被機械擋下且可證明」構成射程內的實質進展。**PM 不預設答案。**

### 二、閉合的部分經機械查證，請複驗

`assign` 確實是 `wfcli` 全域**唯一**寫 `分支worktree` 欄的指令。執行者逐一掃過所有 `set_field_value` 呼叫點：`open_cmd` 雖寫該欄但 `Card.branch`／`Card.worktree` 無任何 CLI 旗標可設、恆為 `None` → 恆為 `—`；`amend_cmd` 可寫欄位只有 `Initiative`／`資源宣告`／`級別`；`handoff_cmd`／`review_cmd` 只寫 owner／狀態／iteration。拒絕時**零 mutation**（recording runner 實證）。

### 三、16 處措辭改動，兩處是使用者可見字串

執行者交回逐處對照表。兩處值得單獨看：

- **`refusal_message()`**：「跨 repo **建立** worktree」→「**這筆登記**會把 worktree 歸給 X……**拒絕登記**」，並加註「訊息刻意說『拒絕登記』而不是『已阻止建立』」
- **`--worktree-source-repo` 的 help**：「**實際會執行** `git worktree add` 的來源 repo」→「**這筆登記主張的**來源 repo」＋「**不觀測、也不綁定後續真正的 `git worktree add`**」

**請攻擊**：16 處窮舉了嗎？有沒有殘留的「預防建立」框架？

### 四、danger 區塊：兩種字面都留，並有反向測試

需求方裁定明文要求逐字保留那一句。**卡面 amend 的版本與派審詞的版本不是彼此的子字串**，執行者兩種都留——「只留一種必然違反另一份要求」。

四條測試釘住，其中一條**反向釘死三個舊字面**（`建立當下的預防`／`建立當下被擋`／`預防的唯一有效位置`），**防止有人補說明時把舊框架寫回來**。

### 五、順帶修掉一處既有錯誤

`check_worktree_repo_ownership` 論證第 2 點仍寫著「判不出來的每一種輸入都不是合法穩態」——**R1-02 早已舉出反例**（repo 外的絕對路徑是 canonical §4.5 允許的合法配置）。改為列出三個 `undeterminable` 碼各自的補齊管道，**並把「當初那句錯在哪」留在原地，不抹掉**。

### 六、數字

`origin/main`（拋棄式）**701** ／ 本輪分支 **716**（前輪 712，+4 且無既有測試改動或刪除）／ **合併樹 `7dd1bb2e` 實跑 759、CLEAN**。locale 矩陣 `C` 與 `en_US.UTF-8` 各 **126 passed**；`uvx ruff` 五檔 All checks passed；CI 另兩步在合併樹上亦跑過（`uv lock --check` 通過、replay **65/65**）；枚舉器不動點 `cmp` 逐位元組相同。

### 七、⚠️ 執行者自陳六項，第 1 項你必須知悉

**七項自陳的第 1、5 項是依 HEAD 的碼「重新導出」，不是原文引用**——原文只存在於 R2 交給 PM 的報告，**Issue 上沒有留痕**。它主動標示了這一點。其餘：第 7 項（`test_release_cleanup.py` 不再覆蓋 assign 路徑是淨損失）未修；第 1 點缺口它只證明「機制上可繞過」，**沒有證明「今天有人繞過」**（需 GitHub audit log，不在唯讀 `gh` 可及範圍）；枚舉器產物 SHA 與 R2 那次不同是 Project 快照隨時間變動，**不是不動點被打破**；**CI 它沒有實際觸發過**，只在合併樹上以 CI 的三步與 CI 釘的 locale 本機重現。

### 環境紅線

**唯讀查核。不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`、不得改 repo settings。不要在被審 worktree 內 `checkout`／`reset`／`stash`**（20+ worktree 共用同一 git repo）。
⚠️ **你會再次讀到 `cpbl-analytics` 底下兩個真實跨 repo 漂移 worktree。只讀不動**——不得刪除、修改或 `git worktree prune`（執行者本輪亦只讀，`git worktree list` 仍 21）。
⚠️ **`cli/tests/test_commands_mocked.py:290` 有一處既存的 marker 前綴字面**（非本卡引入）。
⚠️ **repo 已套用 `required_status_checks` ruleset**（`id 20768920`、`bypass_actors: 0`、`strict: true`），`main` 現為 `d0397e0`。
留言**不得出現 `wf-review-event` 後面直接接半形冒號的字面**，發文前 `grep` 確認 0 次。

### 輸出

依 `templates/review-prompt.md` §5。**逐項回報前輪 accepted blocking finding 閉環**（`R2-01`）。**五個 schema 欄位自己填**，`root_cause_id` 沿用 `worktree-repo-ownership`，**不得用佔位字串**。

**留收據**：多行格式（`card_id:`／`source_sha:` 各自獨立成行）、報告全文同帖、取材規則寫死起訖／編碼／換行／是否 strip／排除範圍。

⚠️ **更正一條 PM 先前寫錯的規則**：「一卡只留一則」的**正確單位是「一個 attempt（`card_id` + `source_sha`）」**，不是一張卡。同一張卡的不同輪次各自留一則，那不是重複。「發現有誤也不要再貼」只適用於**同一個 attempt 之內**。

⚠️ **取材規則請避開反引號**（上一張卡的 delimiter 名稱被 shell 展開而遺失），用單引號 heredoc。**發出後不要編輯。**

**YAML 限制**：不支援 `>`（用 `|`）、不支援裸字串序列、不支援頂層鍵＋巢狀 mapping、序列項須縮排 2 空格、區塊內不得混入散文或 code fence、值含 ` #` 須加引號。


## Comment 5273770006 · 2026-08-12T23:00:15Z

<!-- wf-review-receipt:v1
card_id: WF-WORKTREE-REPO-OWNERSHIP1
source_sha: 544e162b736a681532f49744f6a7fdfb2b79d96f
report_sha256: 049d8f60786b90858fce94dd6d2a9d4e585db76c4cf7bdb122a74aeb75994849
-->

取材規則：被雜湊文字起點為本規則之後的下一個 <!-- report:start --> 的下一個 LF；終點為本規則之後的下一個 <!-- report:end --> 前一個 LF；UTF-8 編碼、LF 換行、不得 strip；排除收據、取材規則及兩個 delimiter 行。
<!-- report:start -->
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "gh issue view 57 --repo ruan6047/ai-workflow --json body -q .body | grep 'handoff by wf-cli' | tail -1; git -C .claude/worktrees/wf-worktree-repo-ownership1 rev-parse HEAD; git -C .claude/worktrees/wf-worktree-repo-ownership1 merge-base --is-ancestor e8a638c40f1028b6b85f6c59fd12ee9c1e85582d HEAD"
    observed: "最後 handoff、被審工作樹 HEAD 均為 544e162b736a681532f49744f6a7fdfb2b79d96f；基線祖先檢查成功。"
  - command: "git archive 544e162b736a681532f49744f6a7fdfb2b79d96f | tar -x -C /tmp/aiwf57-r3.OUruSf; cd /tmp/aiwf57-r3.OUruSf/cli; uv run pytest -q"
    observed: "密封副本完整 pytest 命令 exit 0。"
  - command: "cd /tmp/aiwf57-r3.OUruSf/cli; LC_ALL=C uv run pytest -q tests/test_registry.py tests/test_commands_mocked.py -k 'ownership or cross_repo or source_repo or unanchored or worktree_source or absolute_worktree or relative_worktree'; LC_ALL=en_US.UTF-8 uv run pytest -q tests/test_registry.py tests/test_commands_mocked.py -k 'ownership or cross_repo or source_repo or unanchored or worktree_source or absolute_worktree or relative_worktree'"
    observed: "C 與 en_US.UTF-8 locale 各 15 passed、111 deselected。"
  - command: "cd /tmp/aiwf57-r3.OUruSf/cli; uvx ruff check src/wf_cli/commands/assign_cmd.py src/wf_cli/registry.py tests/test_registry.py tests/test_commands_mocked.py; uv lock --check"
    observed: "ruff 顯示 All checks passed；lock 檢查成功。"
  - command: "cd /tmp/aiwf57-r3.OUruSf/cli; uv run python -m wf_cli.registry --from-project ruan6047/4 --output /tmp/aiwf57-r3-project.json; uv run python -m wf_cli.registry --input /tmp/aiwf57-r3-project.json --output /tmp/aiwf57-r3-replay.json; cmp /tmp/aiwf57-r3-project.json /tmp/aiwf57-r3-replay.json"
    observed: "Project 快照與重播逐位元組相同；現況 total 64、allow 47、block 17，其中 ancestor_dir 32。"
  - command: "cd /tmp/aiwf57-r3.OUruSf/cli; uv run python - <<'PY' (呼叫 check_assign_repo_ownership 並傳入兩個指定 cpbl-analytics worktree 絕對路徑)"
    observed: "兩個真實 cpbl-analytics 漂移 worktree 均得到 block、repo_mismatch、card_repo ruan6047/cpbl-analytics、worktree_repo ruan6047/ai-workflow。"
prior_round_closure:
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R1-01"
    status: "closed"
    evidence: "assign_cmd.py 在 set_field_value 與 set_item_body 前呼叫 check_assign_repo_ownership；test_assign_blocks_cross_repo_worktree_before_any_mutation 仍以 recording runner 證明拒絕時零 mutation。"
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R1-02"
    status: "closed"
    evidence: "source_repo、target_dir、ancestor_dir 三級探測已存在；repo 外絕對路徑加 source_repo、錯誤 source_repo 拒絕、以及不讀 cwd 的回歸測試均在上述兩種 locale 通過。"
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R1-03"
    status: "closed"
    evidence: "python -m wf_cli.registry 可從 Project 取材並以 --input 重播；本輪產物 cmp 相同，兩份 SHA256 都是 c3a9fc8080b3f3ea713fb46ceb6cdd7e301ed5740a2c60e96473a51ab96743ea。"
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R2-01"
    status: "closed"
    evidence: "需求方 issuecomment-5268265532 將服務原始目標與核心痛點明確改為保護登記、排除建立；source 的 assign_cmd.py 與 registry.py 已同步改為拒絕登記而非聲稱阻止建立，並保留建立面無預防的 danger 文字。"
findings:
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R3-01"
    severity: major
    blocking: true
    finding_class: governance
    attribution: planner
    root_cause_id: "worktree-repo-ownership"
    evidence: "ROADMAP §2 明定唯一寫入通道 wfcli 只是單機信任模型的治理慣例，Project web UI、gh project item-edit 與 GraphQL 可直接改寫分支worktree TEXT 欄；source 只能在 assign() 內攔截，不能覆蓋這些同一登記面的直接寫入路徑。因此登記歸屬仍可在沒有拒絕、沒有驗證的情況下被錯置。"
    disposition: "需求方須依 ROADMAP §5 的整體規劃，裁定並提供能涵蓋 Project 欄位直接寫入的機械執行面，或再明確把本卡的承諾降為僅 wfcli assign 路徑的檢查；在前者未存在且後者未裁定前，不可驗收為已保護登記面。"
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R3-02"
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: "worktree-repo-ownership"
    evidence: "registry.py 將不存在目標的 ancestor_dir 結果標為 inferred，且明說它不是事實；然而 check_assign_repo_ownership 對 slug 相符仍回傳 match/allow。這次 Project 枚舉有 32 個 ancestor_dir allow；source 不會觀測或綁定後續 git worktree add，故可把登記寫成與祖先 repo 相符，後續卻由另一 repo 建立，登記本身仍非已驗證的歸屬事實。"
    disposition: "新登記必須要求可驗證且可留存的來源 repo 證據，或讓 inferred 一律拒絕並要求 source_repo；並以端到端測試證明無法以 ancestor_dir 推測取得 allow 後將同一路徑建立為另一 repo 的 worktree。"
scope_outside_findings:
  - note: "已存在的 17 筆 block 與其 14 筆未錨定相對路徑沒有重掃排程；本報告不把既有資料清理擴入本輪 finding 集合。"
  - note: "本輪 Project 快照是 total 64、allow 47、block 17，與 handoff 摘要的數字不同；產物可重播，差異屬動態 Project 現況。"
<!-- report:end -->


## Comment 5273800984 · 2026-08-12T23:03:58Z

<!-- wf-review-event:v1 card_id=WF-WORKTREE-REPO-OWNERSHIP1 source_sha=544e162b736a681532f49744f6a7fdfb2b79d96f attempt_id=WF-WORKTREE-REPO-OWNERSHIP1-e0-544e162b736a681532f49744f6a7fdfb2b79d96f -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-WORKTREE-REPO-OWNERSHIP1`　attempt_id：`WF-WORKTREE-REPO-OWNERSHIP1-e0-544e162b736a681532f49744f6a7fdfb2b79d96f`
- 查核者：GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5273770006。四項前輪 finding（R1-01/02/03、R2-01）皆判 closed。scope_outside 兩項未入區塊、保存於收據雜湊範圍內　escalation_epoch：0
- source_sha：`544e162b736a681532f49744f6a7fdfb2b79d96f`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-13T07:03:57+08:00

### self_run（查核者實跑）

- `gh issue view 57 --json body -q .body | grep 'handoff by wf-cli' | tail -1; git rev-parse HEAD; git merge-base --is-ancestor e8a638c HEAD`
  - 最後 handoff、被審工作樹 HEAD 均為 544e162b736a681532f49744f6a7fdfb2b79d96f；基線祖先檢查成功。
- `git archive 544e162 | tar -x -C /tmp/aiwf57-r3.OUruSf; cd cli; uv run pytest -q`
  - 密封副本完整 pytest 命令 exit 0。
- `LC_ALL=C 與 LC_ALL=en_US.UTF-8 各跑 tests/test_registry.py tests/test_commands_mocked.py -k 'ownership or cross_repo or source_repo or unanchored or worktree_source or absolute_worktree or relative_worktree'`
  - C 與 en_US.UTF-8 locale 各 15 passed、111 deselected。
- `uvx ruff check 四檔; uv lock --check`
  - ruff 顯示 All checks passed；lock 檢查成功。
- `uv run python -m wf_cli.registry --from-project ruan6047/4 --output …; --input … --output …; cmp 兩份`
  - Project 快照與重播逐位元組相同；現況 total 64、allow 47、block 17，其中 ancestor_dir 32。
- `uv run python -c 呼叫 check_assign_repo_ownership 並傳入兩個 cpbl-analytics worktree 絕對路徑`
  - 兩個真實漂移 worktree 均得到 block、repo_mismatch、card_repo ruan6047/cpbl-analytics、worktree_repo ruan6047/ai-workflow。

### findings（2，其中 blocking 2）

- **WF-WORKTREE-REPO-OWNERSHIP1-R3-01**　severity=major　blocking=true　class=governance　attribution=planner　root_cause_id=`worktree-repo-ownership`
  - evidence：ROADMAP §2 明定唯一寫入通道 wfcli 只是單機信任模型的治理慣例，Project web UI、gh project item-edit 與 GraphQL 可直接改寫分支worktree TEXT 欄；source 只能在 assign() 內攔截，不能覆蓋這些同一登記面的直接寫入路徑。因此登記歸屬仍可在沒有拒絕、沒有驗證的情況下被錯置。
  - disposition：需求方須依 ROADMAP §5 的整體規劃，裁定並提供能涵蓋 Project 欄位直接寫入的機械執行面，或再明確把本卡的承諾降為僅 wfcli assign 路徑的檢查；在前者未存在且後者未裁定前，不可驗收為已保護登記面。
- **WF-WORKTREE-REPO-OWNERSHIP1-R3-02**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`worktree-repo-ownership`
  - evidence：registry.py 將不存在目標的 ancestor_dir 結果標為 inferred 且明說它不是事實；然而 check_assign_repo_ownership 對 slug 相符仍回傳 match/allow。這次 Project 枚舉有 32 個 ancestor_dir allow；source 不會觀測或綁定後續 git worktree add，故可把登記寫成與祖先 repo 相符，後續卻由另一 repo 建立，登記本身仍非已驗證的歸屬事實。
  - disposition：新登記必須要求可驗證且可留存的來源 repo 證據，或讓 inferred 一律拒絕並要求 source_repo；並以端到端測試證明無法以 ancestor_dir 推測取得 allow 後將同一路徑建立為另一 repo 的 worktree。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5273953073 · 2026-08-12T23:22:28Z

## 需求方裁定（2026-08-13）：承諾降為「僅 `wfcli assign` 路徑的檢查」

> ⚠️ 內容由需求方 `ruan6047` 明確核准，**文字由 PM 代擬並代貼**。依 `docs/ROADMAP.md` §1，身分以宣告欄位記錄——本段即該宣告（角色：PM 代擬／需求方核可）。

針對 `R3-01`（major、blocking、governance、`attribution: planner`）。查核者給了兩條路，需求方採**第二條**：

> 或再明確把本卡的承諾**降為僅 `wfcli assign` 路徑的檢查**；在前者未存在且後者未裁定前，不可驗收為已保護登記面。

### 裁定

**本卡的承諾是：`wfcli assign` 這一條路徑上的跨 repo 歸屬檢查。不是「登記面已被保護」。**

### 理由

**一、追求「涵蓋所有寫入路徑」是在追一個結構上拿不到的東西。** `分支worktree` 是 GitHub Project 的 TEXT 欄，web UI／`gh project item-edit`／GraphQL 皆可直接改寫。要覆蓋它需要 Project 的欄位權限，而依 ROADMAP §2，**repo／Project setting 不是檔案、不在資源模型的值域裡、不可能被宣告進任何寫入集**。這與 §1 對身分的結論同構：**不可得的東西不該被寫成待辦，該被寫成已知限制。**

**二、降級不是放棄。** `wfcli assign` 仍是唯一被慣例約束的登記路徑，守住它有實質價值——執行者已機械查證它是 `wfcli` 全域唯一寫該欄的指令，且拒絕時零 mutation。**能證明的部分照樣算數，不能證明的部分不要宣稱。**

**三、這是本卡第二次縮射程，兩次的形狀相同。** 第一次把「建立面」移出（`git worktree add` 不經 wfcli）；這次把「登記面的其他入口」移出（Project 欄位可直接改寫）。**兩次都是同一件事：wfcli 是慣例不是機制。** 需求方接受這個限度，並要求它被寫在讀得到的地方，而不是靠人記得。

### 因此須修改的

- **核心痛點**：明寫本卡的承諾範圍是 `wfcli assign` 路徑，並列出射程外的三條路徑（`git worktree add` 直接建立、Project 欄位直接改寫、既有登記不重掃）
- **`registry.py` 頂端的 danger 區塊**：既有那句關於建立面的**逐字保留**，並新增一句同等強度的關於 Project 欄位直接寫入的
- 交付文件中凡宣稱「登記面已被保護」之處，改為「`wfcli assign` 路徑已被保護」

### 明確不涵蓋

**本裁定不處置 `R3-02`**（32 個 `ancestor_dir` 推測仍回 `allow`）。那是 `attribution: executor` 的實作 finding，**落在縮小後的射程之內**——`wfcli assign` 路徑上的判定該不該接受推測，與寫入路徑涵蓋範圍無關。**須另行處置，不得因本裁定而視為已解。**


## Comment 5274150740 · 2026-08-12T23:51:48Z

## 需求方裁定（2026-08-13）：接受「絕對路徑**且**明示來源」，修改 08-12 的二擇一

> ⚠️ 內容由需求方 `ruan6047` 明確核准，**文字由 PM 代擬並代貼**（角色：PM 代擬／需求方核可，依 `docs/ROADMAP.md` §1）。

### 被修改的是什麼

2026-08-12 裁定（`issuecomment-5266614483`）：

> 新的 `assign` **一律給絕對路徑，或**若確實從別的 repo 執行 `git worktree add`，以 `--worktree-source-repo` 明示。

**那是二擇一。本裁定改為兩者都要**：`inferred`（`ancestor_dir` 推測）一律拒絕，因此巢狀於卡自己 repo 底下的絕對路徑——**即生產慣例**——也必須補 `--worktree-source-repo`。

### 理由：執行者指出的是內部矛盾，不是保守與否的取捨

> `_slug_of_dir` 的註解寫「**比對軸是 origin slug 不是路徑**」，而祖先推測的全部證據只有「這條路徑座落在誰底下」——**31/47 的放行建立在模組自己判為無效的軸上**。

需求方接受這個論證。**一個模組不能一邊宣告某條軸無效、一邊用它放行三分之二的案例。**

### 代價，需求方知情接受

Project #4 全量枚舉（同一枚舉器同一輸入）：

| | allow | block |
|---|---:|---:|
| 改動前 | 47 | 17 |
| 改動後 | **16** | **48**（新增 `worktree_repo_inferred` 31） |

**真正的代價不在那 31 筆**——它們 `target_exists` 全為 false，且閘門不回溯。**代價落在未來每一次 `assign`：PM 從此每次都要多打一個旗標**，因為生產慣例是登記早於建立，常態就落在這一格。

### ⚠️ 需求方明確知悉的殘餘風險

執行者自陳第 2 項，需求方逐字採納為已知限制：

> **我的修法可能把 cwd 依賴從碼裡趕到人腦裡。** R1-02 用 `monkeypatch.chdir` 機械封死了「判定隨在哪執行而變」；現在要求 PM 每次手打 `--worktree-source-repo`，**而最順手的答案就是「我現在站的這個 repo」——同一個錯誤形狀換成社會層**。碼裡仍不讀 cwd，但這條**沒有執行者**。

**接受這個風險的理由**：機械層的矛盾是確定的、社會層的誤用是可能的；先消掉確定的那個。**但這不是解決，是取捨，且該取捨今天沒有任何東西在監看。**

### 翻回的方式

執行者已把翻回位置寫進碼（刪 `OWNERSHIP_DECISIONS` 該列）。**需求方一行裁定即可翻回**，不需重新論證。

### 明確不涵蓋

本裁定**不處置**執行者指名的第三次縮射程（「**建立行為 `assign` 觀測不到**」——`source_repo` 是宣告不是綁定，它以真跑一次跨 repo `git worktree add` 的測試證明閘門確實沒綁定建立）。它落在射程之內、今天沒有執行者、依 ROADMAP §5 未開卡。**需求方知悉，排程另議。**


## Comment 5274176358 · 2026-08-12T23:55:57Z

## ⛔ PM 撤回本輪派審：需求方推翻了 `R3-02` 處置所依賴的前提

本卡於 `a0c25db` 交接查核後尚未有任何查核者進駐。**需求方 2026-08-13 提出一個問題，查證後推翻了該處置的前提。本輪撤回，不計為可計數 attempt，交回實作。**

### 需求方的問題

> 絕對路徑是否是無效資訊，尤其是不同台電腦路徑不會完全相同。

### 查證結果（PM 實跑，三項皆為事實）

**一、路徑有兩種寫法並存，分佈按 repo 走。** Project #4 全量：**絕對路徑 51 筆、相對路徑 18 筆**；相對路徑中 **cpbl-analytics 16 筆、ai-workflow 2 筆**。

也就是說「新的 `assign` 一律給絕對路徑」這條 2026-08-12 的慣例，**實際上只約束了 ai-workflow 這一半，而那一半是 PM 自己在打**。cpbl-analytics 的卡從來沒照做過。

**二、相對路徑比絕對路徑更接近可稽核的形式。** `.claude/worktrees/xxx` 在任何 clone 上指向同一相對位置；`/Users/ruanruan/Dev/…` 只在單一台機器成立。**先前收緊的方向，收緊的是比較不可攜的那一種。**

**三、歸屬檢查建立在機器局部的東西上。** `probe_worktree_repo` 從路徑讀 `commondir` 反推 repo——**換一台機器，`target_dir` 探測必然失敗**，落到 `ancestor_dir` 或 `undeterminable`，依 `R3-02` 的新規則就是**一律 block**。

**推論**：枚舉器那 64 筆判定是**「這台機器的判定」，不是 repo 的事實**。它一直被當成對帳視圖使用，而它對帳的是本機磁碟。

### 裁定

**`分支worktree` 欄混了兩種性質不同的東西，而歸屬判定建立在錯的那一種上。**

| | 性質 | 誰需要 |
|---|---|---|
| **repo slug** | 可攜、可稽核、跨機器成立 | 歸屬判定、對帳、查核 |
| **本機路徑** | 機器局部、操作用 | `cleanup` 刪 worktree、`doctor` 探測 |

**歸屬應由 slug 表達，不由路徑反推。** `--worktree-source-repo` 應收 **slug** 而非目錄——那可攜、可稽核、且**不需要讀任何檔案系統**；路徑退回它該待的位置：`cleanup` 的操作輸入，**不參與歸屬判定**。

⚠️ **路徑不可移除**：`cleanup.py` 用它做破壞性收尾（`status --porcelain` 檢查乾淨、`resolve()` 後刪除），`doctor`／`snapshot`／`handoff` 亦讀它。**這不是「路徑無效」，是「兩者不該共用一個判定軸」。**

### 這是同一個形狀第三次

`ROADMAP.md` §1：身分那次追「驗證他真的是他」，而目標只需要「記下宣稱」。
**這次追「路徑指向的 repo 是什麼」，而目標只需要「這張卡宣稱屬於哪個 repo」。**

執行者在上一輪自己指名了第三次縮射程（「建立行為 `assign` 觀測不到」）。**本裁定認為那三次都是同一個根源：把可攜的宣告與機器局部的探測混在同一個欄位、同一條判定軸上。**

### 本輪交付的處置

`R3-01` 的對齊工作（14 處措辭 ＋ danger 第三句 ＋ 反向釘死）**與本裁定無衝突，保留**。

`R3-02` 的處置（`inferred` 一律拒絕、`--worktree-source-repo` 收目錄）**依本裁定重做**。2026-08-13 那則「接受絕對路徑**且**明示來源」的裁定（`issuecomment-5274150740`）**一併作廢**——它建立在同一個被推翻的前提上。

⚠️ **PM 的責任**：那則裁定是 PM 代擬、需求方核可的，而 PM 當時**沒有查證路徑的可攜性就下了「兩者都要」**。需求方在核可後才自己提出這個問題。`attribution: coordinator`。


## Comment 5274502179 · 2026-08-13T00:40:15Z

## 需求方裁定（2026-08-13）：本卡降為 Backlog，承認在可攜約束下沒有執行面

> ⚠️ 內容由需求方 `ruan6047` 明確核准，**文字由 PM 代擬並代貼**（角色：PM 代擬／需求方核可，`docs/ROADMAP.md` §1）。

### 決定性的數字

`caaf664` 交付後，Project #4 全量 64 筆：

```
軸 A（可攜的歸屬判定）   allow 64   block 0
軸 B（本機觀測）         抓到 2 筆真實跨 repo 漂移，但依 §1.5 不准影響判定
```

**能擋的抓不到，抓得到的不准擋。**

執行者自己不包裝這件事：

> 它擋得住的只有**明示宣告**，而**現實漂移的成因是沒注意到**。這不是可以靠測試補的缺口，是這個判定形狀的上限。上表 64 筆裡軸 A 的 block 數是 **0**——**這個數字就是證據，我不打算包裝它。**

### 依 ROADMAP §0 的判準，本卡已是目標 3

> 目標 1 的卡：**執行者是誰？** 答案若是「靠人記得」，它其實是目標 3。

軸 A 的執行者存在但無事可做；軸 B 有事可做但依 §1.5 不准做。**兩邊都不構成「有機械執行者會擋下它」。**

### 裁定

**降為 📥Backlog。** 這不是否定交付——`caaf664` 的內容品質很高，且其中數項是**跨機器一致性的實質證明**（把 `subprocess.run` 與 `Path.is_dir` 換成會爆炸的替身，證明歸屬判定執行期一次都沒碰檔案系統；三個不同 cwd 下四組輸入逐欄全等）。**降級的理由是這條路在可攜約束下走完了，不是走錯了。**

**⚠️ 降級不是關閉。** 未閉合的 `R3-01`／`R3-02` 維持未閉合，本次降級**不視為驗收**；`caaf664` 未合併、未查核。

### 真正能關掉核心痛點的東西，執行者兩輪前就指名了

> 真正能關掉它的是**建立之後的對帳**（fact 這時才存在），而今天沒有任何東西在建立之後看過一眼。

**那是另一張卡的形狀，且今天沒有人承接。** 依 §5，開不開、何時排是需求方的判斷——**本裁定不開卡**，只把這個義務記在這裡。

### 這張卡留下的三樣東西

1. **兩個真實跨 repo 漂移已被具名**（`WFCLI-DEPLOY-STATE1`、`DATA-RE24-PROD-REBUILD1`，commondir 指向 `cpbl-analytics/.git/modules/.ai-workflow`、origin 是 ai-workflow、卻註冊在 cpbl 的卡上），且**兩個 repo 的頂層 `git worktree list` 都是 0 命中**——`doctor` 今天仍然看不見它們。**它們還在磁碟上。**
2. **`ROADMAP §1.5`** 就是從本卡的第三次縮射程長出來的。
3. **一個未具名的偵測落差**：`WF-25-REVIEW-WRITE-CHANNEL1` 的路徑指向 cpbl 目錄樹、目標尚未建立，上一版靠祖先推測判 block，本版降為警示——**警示沒有執行者**。

### PM 的帳

本卡走了五輪。**前四輪有三輪的前提是 PM 給錯的**：射程沒縮就要求「在建立當下擋下」、把「絕對路徑且明示來源」寫成裁定而沒查證路徑的可攜性、以及一路把「登記面已被保護」當成可達成的目標。第五輪的問題不是前提錯，**是這條路走完了**。

`attribution: coordinator`。


## Comment 5277820230 · 2026-08-13T08:17:28Z

## 需求方裁定：本卡承諾降為 wfcli assign 路徑

第三輪查核 finding R3-01（governance，attribution: planner）指出：本卡承諾保護 worktree
歸屬登記，但 `wfcli` 只是單機信任慣例——Project 網頁 UI、`gh project item-edit` 與 GraphQL
都能直接改寫該 TEXT 欄，碼只能在 `assign()` 內攔截。查核者給的處置是二選一，並指名須由
需求方裁定。

**需求方選 (B)：明確把本卡的承諾降為僅 `wfcli assign` 路徑的檢查。**

理由（PM 記錄）：「`wfcli` 是唯一寫入通道」本來就是**慣例而非機制**，與 `docs/ROADMAP.md`
§1 身分欄位「宣告存在、強制不存在」是同一性質的缺口。把承諾寫成實際做得到的範圍，比留
一個做不到的承諾誠實。

選項 (A)（提供涵蓋 Project 欄位直接寫入的機械執行面）**不在本卡射程**：它需要 webhook 或
排程對帳，屬另一張卡的份量，依 ROADMAP §3 應進降級清單，不塞進本卡。

本裁定不追溯改寫任何既有留痕，僅向前生效。


## Comment 5277930332 · 2026-08-13T08:29:24Z

<!-- wf-review-receipt:v1
card_id: WF-WORKTREE-REPO-OWNERSHIP1
source_sha: caaf6641a2e8e17520bc828aa1954cb941f7850a
report_sha256: ebe60678819eb6371053e75f17b92ffacc900be805be19f42cd39c02018046ad
-->
取材規則：被雜湊文字起點為本規則之後的下一個 <!-- report:start --> 的下一個 LF；終點為本規則之後的下一個 <!-- report:end --> 前一個 LF；UTF-8 編碼、LF 換行、不得 strip()；排除收據、取材規則及兩個 delimiter 行。
<!-- report:start -->
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git merge-base --is-ancestor e8a638c40f1028b6b85f6c59fd12ee9c1e85582d caaf6641a2e8e17520bc828aa1954cb941f7850a"
    observed: "exit 0；baseline 是 source_sha 的祖先。"
  - command: "git log --oneline 544e162b736a681532f49744f6a7fdfb2b79d96f..caaf6641a2e8e17520bc828aa1954cb941f7850a"
    observed: "恰為 a0c25db 與 caaf664 兩筆指定增量。"
  - command: "cd cli && uv run pytest tests/test_registry.py tests/test_commands_mocked.py -q -k 'ownership or cross_repo or source_repo or local_axis or local_observation or nesting or worktree_source or relative_registration'"
    observed: "18 passed, 114 deselected。包含 test_ownership_allow_does_not_bind_the_actual_creation。"
  - command: "cd cli && uvx ruff check src/wf_cli/commands/assign_cmd.py src/wf_cli/registry.py tests/test_commands_mocked.py tests/test_registry.py tests/test_release_cleanup.py && uv lock --check"
    observed: "ruff All checks passed；uv lock --check 成功。"
  - command: "wfcli review --validate-only"
    observed: "未執行；需求明令查核者不得執行任何 wfcli 動詞，故不能以此命令自檢。"
prior_round_closure:
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R3-01"
    status: "closed"
    evidence: "核心痛點、assign_cmd.py 與 registry.py 均明定承諾僅限 wfcli assign；Project web UI、gh project item-edit、GraphQL、git worktree add 與既有登記皆列為已知射程外。搜尋到的『登記面已被保護』只存在於否定式說明與其反向測試。"
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R3-02"
    status: "superseded_by_requester_ruling"
    evidence: "caaf664 移除了 ancestor_dir 作為 allow 依據；軸 A 僅比較 Issue URL 與可攜 slug，軸 B 對 ancestor nesting 僅警示。這符合需求方後續推翻『以路徑推測歸屬』前提的裁定，但沒有達成 R3-02 原先要求的建立行為約束。"
findings:
  - finding_id: "WF-WORKTREE-REPO-OWNERSHIP1-R4-01"
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: "worktree-repo-ownership"
    evidence: "check_worktree_repo_ownership() 在 --worktree-source-repo 缺省時以 card_repo_default 直接回 match/allow；assign_cmd.py 隨即寫入分支worktree。目標尚未建立時 observe_local_worktree() 回 target_absent/pass。test_ownership_allow_does_not_bind_the_actual_creation 更以真實 git worktree add 證明：先以 ai-workflow slug 取得 allow，後從 cpbl-analytics 把同一路徑建成 worktree，僅事後得到 contradiction。故未注意到的跨 repo 建立仍可先取得可採信的登記，與 amend 後核心痛點所稱 assign 不再把錯誤歸屬登記進 Project 不符。"
    disposition: "本卡若要宣稱 core_pain_resolved，須使建立後的可驗證事實回寫或驗證該登記，並在不符時拒絕交接或撤銷登記；單靠可攜 slug 宣告不能完成。若需求方維持其『本卡無可用執行面、降為 Backlog』裁定，則保留此 finding、不可將 caaf664 驗收為已解。"
scope_outside_findings:
  - note: "既有 17 筆 block 與未錨定相對路徑未被本次寫入改寫；source 亦明示不回溯。其清理或重掃仍屬另一個對帳或資料遷移工作，未擴入本輪 finding。"
  - note: "未主張完整 pytest 成功：完整測試命令在此環境留下未回傳終態的背景程序；本報告只採信上述 18 項聚焦測試。"
<!-- report:end -->

## Comment 5278306440 · 2026-08-13T09:07:51Z

## Contract baseline：WF-WORKTREE-REPO-OWNERSHIP1

```yaml
wf_contract_baseline: v1
contract: templates/review-escalation.md
effective_from: "2026-08-13T17:07:49+08:00"
declared_by: ruan6047
rationale: "本卡三則早期 review event（issuecomment-5266086951／5268180933／5273800984）寫入於 WF-22-CLI4（#9）escalation 帳能力落地之前，機械上不可能帶有當時尚不存在的帳事實；#9 於今日（2026-08-13）併入 main = 10de6f1 後開始強制，依 review-escalation.md:276 將其判為「未知」而非「不計數」，使第四輪裁決無法寫入。需求方授權在此刻切 baseline：baseline 之前的事件維持原貌不追溯改寫，之後的事件依新契約帶帳。此為 forward correction，不補歷史紀錄。"
```

---

此 marker 為 one-shot cutover（`review-escalation.md` §5）：不得附在 review 等其他事件上，啟用後再次出現必須 fail loud。本行之前的 attempt 依契約「維持原貌」，其 `counts_toward_escalation` 為**未知**（而非「不計數」）；本行之後的 review event 一律由 `wfcli review` 附上結構化 counts 事實。

## Comment 5278311314 · 2026-08-13T09:08:18Z

<!-- wf-review-event:v1 card_id=WF-WORKTREE-REPO-OWNERSHIP1 source_sha=caaf6641a2e8e17520bc828aa1954cb941f7850a attempt_id=WF-WORKTREE-REPO-OWNERSHIP1-e0-caaf6641a2e8e17520bc828aa1954cb941f7850a -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-WORKTREE-REPO-OWNERSHIP1`　attempt_id：`WF-WORKTREE-REPO-OWNERSHIP1-e0-caaf6641a2e8e17520bc828aa1954cb941f7850a`
- 查核者：GPT-5@Codex 子代理（需求方轉貼）　escalation_epoch：0
- source_sha：`caaf6641a2e8e17520bc828aa1954cb941f7850a`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-13T17:08:16+08:00

### self_run（查核者實跑）

- `git merge-base --is-ancestor e8a638c40f1028b6b85f6c59fd12ee9c1e85582d caaf6641a2e8e17520bc828aa1954cb941f7850a`
  - exit 0；baseline 是 source_sha 的祖先。
- `git log --oneline 544e162b736a681532f49744f6a7fdfb2b79d96f..caaf6641a2e8e17520bc828aa1954cb941f7850a`
  - 恰為 a0c25db 與 caaf664 兩筆指定增量。
- `cd cli && uv run pytest tests/test_registry.py tests/test_commands_mocked.py -q -k 'ownership or cross_repo or source_repo or local_axis or local_observation or nesting or worktree_source or relative_registration'`
  - 18 passed, 114 deselected。包含 test_ownership_allow_does_not_bind_the_actual_creation。
- `cd cli && uvx ruff check src/wf_cli/commands/assign_cmd.py src/wf_cli/registry.py tests/test_commands_mocked.py tests/test_registry.py tests/test_release_cleanup.py && uv lock --check`
  - ruff All checks passed；uv lock --check 成功。
- `wfcli review --validate-only`
  - 未執行；需求明令查核者不得執行任何 wfcli 動詞，故不能以此命令自檢。

### findings（1，其中 blocking 1）

- **WF-WORKTREE-REPO-OWNERSHIP1-R4-01**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`worktree-repo-ownership`
  - evidence：check_worktree_repo_ownership() 在 --worktree-source-repo 缺省時以 card_repo_default 直接回 match/allow；assign_cmd.py 隨即寫入分支worktree。目標尚未建立時 observe_local_worktree() 回 target_absent/pass。test_ownership_allow_does_not_bind_the_actual_creation 更以真實 git worktree add 證明：先以 ai-workflow slug 取得 allow，後從 cpbl-analytics 把同一路徑建成 worktree，僅事後得到 contradiction。故未注意到的跨 repo 建立仍可先取得可採信的登記，與 amend 後核心痛點所稱 assign 不再把錯誤歸屬登記進 Project 不符。
  - disposition：本卡若要宣稱 core_pain_resolved，須使建立後的可驗證事實回寫或驗證該登記，並在不符時拒絕交接或撤銷登記；單靠可攜 slug 宣告不能完成。若需求方維持其『本卡無可用執行面、降為 Backlog』裁定，則保留此 finding、不可將 caaf664 驗收為已解。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-WORKTREE-REPO-OWNERSHIP1-e0-caaf6641a2e8e17520bc828aa1954cb941f7850a
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: no
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（GPT-5@Codex）
findings:
  - finding_id: WF-WORKTREE-REPO-OWNERSHIP1-R4-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: worktree-repo-ownership
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5278315424 · 2026-08-13T09:08:41Z

## 需求方裁定：本卡降為 Backlog，保留 R4-01

第四輪查核 finding R4-01 指出結構性事實：**登記發生在建立之前，而登記不綁定建立**。
`check_worktree_repo_ownership()` 在 `--worktree-source-repo` 缺省時以 `card_repo_default`
直接回 `match/allow`；目標尚未建立時 `observe_local_worktree()` 回 `target_absent/pass`。
查核者以測試親自證明：allow 之後仍可由另一個 repo 建立同一路徑的 worktree，**只能事後
觀測到矛盾**。

這代表即使依前一次裁定（issuecomment-5277820230）把承諾限縮到 `wfcli assign` 路徑，
本卡仍達不到其核心痛點。

**需求方選查核者處置的第二項：承認本卡沒有可用的執行面，降為 Backlog，保留 R4-01。**

依 `docs/ROADMAP.md` §0 第一項判準逐字：

> **防止低級事故**｜有機械執行者會擋下它。沒有執行者的偵測器**不算**達成。

本卡現況正是一個沒有執行者的偵測器。要補上執行面，須做「建立後以可驗證事實回寫或驗證該
登記、不符時拒絕交接或撤銷登記」的機制——那是新工程，不在收斂期的射程內。

**已合入 main 的碼不受本裁定影響**：`assign` 路徑的檢查、可攜 repo slug 歸屬、拒絕以
ancestor 路徑推論登記，這些都已在 main 上並持續生效。降級的是**本卡對「防止錯 repo 建立」
的承諾**，不是既有能力。

既有登記資料（17 筆 block、其中未錨定相對路徑者）的清理維持 scope outside，屬另一個對帳
或資料遷移工作。

本裁定不追溯改寫任何既有留痕，僅向前生效。


## Comment 5305701956 · 2026-08-16T04:23:06Z

## 需求方裁定 2026-08-16：核心痛點含一句與事實不符的敘述，須 amend；分支送查核後合併；順序倒轉另開卡

⚠️ **本留言由 PM（Claude Fable 5@Claude Code）代擬代貼，內容為需求方 ruan6047 於對話中的裁定逐字轉錄與其採納的建議。** amend 的 author 檢查對 PM 恆真（#62 承接中），故此處明寫來源。

需求方逐字：

> 依據你研究後的建議

採納的建議即以下三步。

### 一、要修的事實錯誤

現行核心痛點與 2026-08-13 降級裁定皆寫著：

> 已合入 main 的 assign 路徑檢查、可攜 repo slug 歸屬與拒絕 ancestor 路徑推論登記不受本降級影響

**這三項都不在 main。** 由 PM 於 2026-08-16 獨立複驗（非採信執行者轉述）：

```
正控組（確認 grep 在量東西）：origin/main:cli/src/wf_cli/registry.py 大小 6662 bytes

blob 同一性：
  cli/src/wf_cli/registry.py            main=50088d2d  merge-base(e8a638c)=50088d2d
  cli/src/wf_cli/commands/assign_cmd.py main=126f2a80  merge-base(e8a638c)=126f2a80

四個符號在 origin/main 的 cli/ 命中檔數：
  check_assign_repo_ownership     0
  check_worktree_repo_ownership   0
  worktree_source_repo            0
  repo_slug                       0
同一組在 claude/WF-WORKTREE-REPO-OWNERSHIP1：3 / 2 / 4 / 2

gh pr list --head claude/WF-WORKTREE-REPO-OWNERSHIP1 --state all  →  []   （從未開過 PR）
```

即：需求方 2026-08-13 是在「有用的那一半已經入袋」的認知下降級的，而實際上**此分支不合併，repo 一項都拿不到**；main 目前只有 `docs/ROADMAP.md` 提到本卡結論的散文，沒有碼。

此發現由本卡第五輪執行者提出，PM 複驗成立。

### 二、裁定：分支送跨家族查核，通過後合併，卡仍維持 Backlog

降級的理由是「剩下那截屬新工程、不在收斂期射程」，**不是碼有問題**。碼不入 main 等於四輪工作歸零，且下一次承接會從零重推同樣四輪。

⚠️ **amend 須同時寫清楚合併買到什麼、沒買到什麼**，否則只是把假印象從「在 main」搬到「在 main 所以漂移有人管」。合併**不**使核心痛點關閉；R3-01／R3-02／R4-01 維持未閉合，本次合併不視為驗收。

### 三、真正的預防另開卡：把登記與建立的順序倒回 canonical

PM 於本次研究讀完兩條軸的實作，結論如下（供承接卡引用）：

- **軸 A `check_assign_repo_ownership`** 是純字串比對（卡的 repo 取自 Issue URL vs `--worktree-source-repo` 宣告的 slug），不讀檔案系統、順序無關。**但該旗標是 `default=None` 非必填**，help 明寫「省略＝宣告『屬於卡自己的 repo』，那是絕大多數情形」。因此真正的失效模式——把 worktree 漂到另一個 repo 而**不宣告**——軸 A 拿卡的 repo 跟自己比，回 allow。它只在有人**主動宣告**跨 repo 時開火。
- **軸 B `observe_local_worktree`** 只在「登記的路徑此刻存在、且它自己就是另一個 repo 的 worktree」時說得出話。而 `assign --worktree` 是 `required=True`，把 claim 與登記併成一步，**登記必然早於建立**，目標永遠不存在 → 軸 B 恆沉默。模組自己寫著「它的沉默不是判定」。
- **`templates/worktree-lifecycle.md` 第 1 點的順序是相反的**，逐字：「claim 成功後建立 worktree，並把**實際路徑＋分支**寫回卡面」。**canonical 規定先建後登記，是 CLI 把順序倒過來的。**
- 第五輪執行者在真實磁碟上量過：兩個至今仍在的跨 repo 漂移 worktree，在倒轉順序下**都被擋下（assign exit 6）**，擋它們的是軸 B。

即：**1037 行的判定引擎是逐案打補丁，把順序倒回模板才是預防。**

⚠️ 未驗的代價：倒轉順序會把 `assign` 綁在 worktree 所在的機器上。本專案目前單機，但那是假設不是事實——第五輪執行者已標示此點未驗，承接卡須把它當待驗證假設而非既定條件。

因此該項**不夾帶進本卡**，另開承接卡由需求方單獨裁定機器綁定的取捨。


## Comment 5305714433 · 2026-08-16T04:27:01Z

承接卡已開：**#91 `WF-ASSIGN-REGISTER-AFTER-CREATE1`**（2026-08-16，📥Backlog）。

射程即本卡 2026-08-16 裁定第三節：把 `assign` 的登記順序倒回 `templates/worktree-lifecycle.md` 第 1 點的 canonical 順序（先建後登記），讓軸 B 有事實可查。

⚠️ #91 的頭號待驗證假設，直接繼承自本卡第五輪執行者、**尚未經任何查核者複驗**：兩個至今仍在磁碟上的跨 repo 漂移 worktree，在現行順序下 `assign` exit 0 放行、在倒轉順序下 exit 6 擋下，擋它們的是軸 B 不是軸 A。#91 的驗收條 2 明寫：若複驗發現該宣稱不成立，該卡應即刻停止並回報，不得改用其他理由續作。

⚠️ #91 的已知代價（本卡執行者只驗了有效性、沒驗成本）：倒轉順序會把 `assign` 綁在 worktree 所在的機器上。「本專案單機」是假設不是已驗事實，#91 驗收條 4 要求該句須寫進 `assign` 的 help，不得只留在卡面。

本卡與 #91 的分工：本卡是**判定引擎**（軸 A，+1037 行，逐案），#91 是**把順序倒回模板**（讓既有軸 B 生效，預防）。#91 不依賴本卡合併與否而成立，但若本卡合併，#91 的改動面會與 `assign_cmd.py` 重疊——排程時須留意資源互斥。

## Comment 5305745859 · 2026-08-16T04:37:13Z

<!-- wf-review-receipt:v1
card_id: WF-WORKTREE-REPO-OWNERSHIP1
source_sha: a5d38439e4fe5bab6f446f55797cfa6801e3d9f6
review_scope: merge-suitability-not-acceptance
reviewer: GPT-5.6@Codex
-->

## 跨家族查核裁決（R5）：建議合併，但不視為驗收

```yaml
core_pain_resolved: no
review_result: APPROVE
merge_recommendation: approve_after_update_branch
source_sha: a5d38439e4fe5bab6f446f55797cfa6801e3d9f6
merge_base: e8a638c40f1028b6b85f6c59fd12ee9c1e85582d
findings:
  - finding_id: WF-WORKTREE-REPO-OWNERSHIP1-R5-01
    severity: minor
    blocking: false
    finding_class: test-adequacy
    attribution: executor
    root_cause_id: docstring-mutation-assertion-overstated
  - finding_id: WF-WORKTREE-REPO-OWNERSHIP1-R5-02
    severity: minor
    blocking: false
    finding_class: governance
    attribution: planner
    root_cause_id: prior-finding-status-wording-inexact
```

### 裁決理由

**合併不會製造「漂移有人管」的假保證。** 我沿實際 call path 複驗：軸 A `check_assign_repo_ownership` 的輸入只有 Issue URL 與宣告 slug，`default=None` 形成 `card_repo_default/match/allow`，不讀檔案系統。軸 B 才讀 `--worktree`，且只有已存在、可辨識、實際屬另一 repo 的 worktree 會 `contradiction/refuse`。目前 `assign` 把 claim 與必填 `--worktree` 登記併成一步，常態是先登記後建立，因此真正的「未宣告漂移」仍可得到軸 A allow、軸 B `target_absent/pass`。

但盲區沒有被藏起來，且不只留在卡面：

- `registry.py` 頂端先把承諾限為「`wfcli assign` 這一條路徑」，danger 明寫直接 `git worktree add`、Project TEXT 欄直接改寫、既有登記不重掃三條射程外；warning 又逐條寫明 allow 只是宣告相符、未宣告漂移抓不到、軸 B 沉默不是判定。
- `assign_cmd.py` 的模組文件與 `--worktree-source-repo` help 都直接寫明它是宣告，閘門不觀測、也不綁定後續真正的 `git worktree add`。
- allow 留痕會寫「本閘門不觀測也不綁定後續的 git worktree add」及「沉默不代表無誤」。
- `check_assign_repo_ownership` 雖然函式名簡短，但 docstring、簽章、呼叫點註解與相鄰軸 B 足以阻止把它讀成實體 worktree 漂移守衛。

因此它是「能力很窄、但射程誠實」的守衛，不屬於宣稱構造上不可能保證的那一族。合併買到的是：**有人明示跨 repo slug 時，assign 在任何 Project 寫入前拒絕；卡 repo 只由 Issue URL 導出；不再用 ancestor 路徑推論歸屬；並留下可重跑枚舉與本機矛盾觀測。** 合併沒買到真正未宣告漂移的預防，故 `core_pain_resolved: no`。

### 前提與機械複驗

- 遠端 tip：`a5d38439e4fe5bab6f446f55797cfa6801e3d9f6`。
- 自算 merge-base：`e8a638c40f1028b6b85f6c59fd12ee9c1e85582d`；`origin/main...source` 為 **31 behind / 7 ahead**。
- 差異：五檔，`+2207/-29`；七筆 commit。
- `origin/main` 的 `registry.py`／`assign_cmd.py` blob 與 merge-base 分別逐位元組相同（`50088d2d…`／`126f2a80…`）；四個符號在 main 命中檔數均為 0，而 source 為 3/2/4/2。GitHub 全狀態 PR 搜尋為空。故 2026-08-16 的「三項都還不在 main」訂正成立。
- 密封 source：**723 passed**；五檔 Ruff：**All checks passed**。
- `git merge-tree --write-tree origin/main source` 成功產生 `f65a7ed7457b813546ff53782d23317bc6f45c73`，無衝突；密封合併樹：**944 passed**；五檔 Ruff：**All checks passed**。
- ruleset `20768920` 複驗為 active，strict required status checks，`bypass_actors=[]`、`current_user_can_bypass=never`。分支落後，故合併前必須先 update-branch，再走 PR／CI；本裁決沒有修改 source、沒有 merge，也沒有執行 `wfcli`。

### 真實磁碟順序宣稱

兩個具名路徑目前都仍存在；兩者的 commondir 都是 `cpbl-analytics/.git/modules/.ai-workflow`，origin 都是 `https://github.com/ruan6047/ai-workflow.git`，分支分別為 `codex/WFCLI-DEPLOY-STATE1` 與 `codex/DATA-RE24-PROD-REBUILD1`。

以 cpbl Issue URL、未提供 source slug 呼叫實際 `assign_cmd.run` call path（遠端 mutation 全部替換為 recording no-op）：

- 兩個已存在目標：軸 A 均 `allow/match/card_repo_default`；軸 B 均 `refuse/contradiction`；`assign` **exit 6**，零寫入。
- 同父層不存在的目標：軸 A 同樣 allow；軸 B `target_absent/pass`；`assign` **exit 0**。

`templates/worktree-lifecycle.md:5` 的 canonical 文字確為 claim 成功後「建立 worktree，並把實際路徑＋分支寫回卡面」，即先建後登記。故 #91 的有效性前提成立：倒回該順序後，軸 B 對這兩個真實漂移有事實可查。這只證明有效性；機器綁定成本仍未驗證。

### Findings

**R5-01（non-blocking）— `a5d3843` 的測試宣稱過強。**

commit 本身只有 docstring／測試文字，沒有行為改動；新說明與既有 `test_ownership_allow_does_not_bind_the_actual_creation` 不衝突，兩者分別釘「現行先登記的殘留」與「順序可倒轉」。

但變異結果須精確描述：

- 把整段回退成前一版，新增測試確實轉紅。
- **只拿掉原句的「今天的」與「所以這一刻的」，保留後面的操作慣例／canonical／本卡未做說明，測試仍是 1 passed。** 原因是三個 required token 可在後段繼續滿足，而 banned 字串受 reflow 空白影響，沒有命中。

所以「拿掉限定詞即轉紅」不是一般性成立；只能說「整段回退會紅」。這不阻擋合併，因 source 當前文件本身正確、完整測試與合併樹皆綠；但後續若要宣稱語意被釘死，應讓測試比對正規化後的局部句／段落關係，而不是只驗三個 token 在模組任意位置存在。

**R5-02（non-blocking）— 不得把三個舊 finding 的正式狀態統稱為「維持未閉合」。**

歷史收據的帳面是：

- R3-01：R4 的 `prior_round_closure.status = closed`（以需求方把承諾降為僅 `wfcli assign` 路徑處置）。
- R3-02：R4 的 `prior_round_closure.status = superseded_by_requester_ruling`。
- R4-01：review event 明載 `status: open`，且降 Backlog 後保留。

因此本次合併**不會關閉任何 finding**，也**不會重新開啟**已 closed／superseded 的 R3 finding。精確說法應是：R3-01／R3-02 所指出的底層風險仍未由本次合併消除，R4-01 仍 open，且本次合併不視為驗收。Issue 現行「R3-01／R3-02／R4-01 維持未閉合」若被當作正式 lifecycle status 讀取，會與既有收據矛盾；本留言明確校正其帳面語意。

### 最終判定

**APPROVE 合併建議；core pain 仍是 no。** 先 update-branch、讓 strict CI 在更新後 SHA 重跑，再以 PR 合併。合併後 #57 仍維持 Backlog；真正預防由 #91 承接，不得以本次 merge 結案或宣稱漂移已受保護。


## Comment 5305806507 · 2026-08-16T04:56:57Z

## ⚠️ PM 留痕缺口自陳：分支已合併進 main，但本卡 Log 上沒有查核事件，也沒有合併事件

### 事實

- **分支已合併**：PR #93 於 2026-08-16 squash merge，`origin/main` 現為 `d18cd83`。CI 兩個 check 皆 SUCCESS，merge 前狀態 `MERGEABLE / CLEAN`。
- **本卡 Log 最後一筆是 `12:40:13` 的 amend（op `7a9c7a0f`）**。沒有 review 事件、沒有 release 事件。卡的交付狀態仍是 `🔍待查核`、iteration 5。

### 為什麼沒有查核事件

`wfcli review` 拒收了該裁決：

```
[review] 拒收（review-invalid，不計 iteration、卡片狀態不變）：
  - APPROVE 未附 self_run（或所有項目都沒有 command）：沒有自跑證據的通過不是查核。
    依 canonical AI_WORKFLOW.md §5.2
```

⚠️ **這是格式不符，不是查核沒做。** `issuecomment-5305745859` 的裁決實際附了大量自跑證據——密封 source `723 passed`、密封合併樹 `944 passed`、五檔 Ruff `All checks passed`、`git merge-tree` 產生 `f65a7ed7457b813546ff53782d23317bc6f45c73` 無衝突、以及對兩個真實漂移 worktree 走實際 `assign_cmd.run` call path 的 exit 6 / exit 0 對照——但它們寫在散文與條列裡，不在 schema 要求的 `self_run:` 鍵下、沒有 `command:` 欄位。

**PM 不代寫 `self_run`。** 那等於由 PM 捏造查核者跑過什麼，正是本專案在修的那族問題（見 #62）。

### PM 的操作錯誤

⚠️ **我把順序做反了：先合併，才發現查核事件寫不進去。** 正確順序是先落地 review 事件、確認留痕成立，再走 PR 合併。

⚠️ 另外：本卡今日的兩筆 amend（op `3eb6ec6f`、`7a9c7a0f`）都由 PM 貼裁定留言、再引用該留言當授權——那正是 #62 正在修的恆真檢查。留言開頭已寫明代擬代貼，但機械上仍是自己核自己。

### 需求方要裁的

**甲**：請查核者以 schema 格式（含 `self_run` 與 `command`）重貼一次裁決，PM 再落 review 事件補齊留痕。留痕正確，代價是多一個往返。

**乙**：需求方裁定本卡的散文自跑證據等同 `self_run`，由 PM 記一筆例外並落事件。代價是在 `self_run` 這條紅線上開一個先例。

PM 建議**甲**：`self_run` 的紅線存在的理由就是「沒有自跑證據的通過不是查核」，而這次證據明明有、只是格式不對——為了省一個往返而在紅線上開先例，代價不對稱。且查核者重貼的成本很低。

### 不受影響的

合併本身的技術狀態沒有問題：CI 綠、無衝突、合併樹 944 passed 由查核者密封複驗。缺的是**帳**，不是**證據**。


## Comment 5307998582 · 2026-08-16T14:45:51Z

承上則（`issuecomment-5305806507`）的留痕缺口——需求方 2026-08-16 裁定採**甲案**：請查核者以 schema 格式（含 `self_run` 與 `command`）重貼一次裁決，PM 再落 review 事件補齊留痕。**不裁定散文證據等同 `self_run`。**

理由在研究後比原本更強：`validation.py:162` 的 docstring 明載——`templates/review-escalation.md` §1 列的無效查核有六種，**只有「`APPROVE` 未附 `self_run`」在寫入通道可以機械判定**，其餘五種（查核順序、環境污染、reviewer 獨立性、審錯 artifact、同一 reviewer 對同一 SHA 重複回報）都需要 CLI 拿不到的事實、由 Coordinator 人判。**這是六道防線裡唯一一道機器守得住的**，在它上面開先例等於把唯一自動化的那道也交回人腦。

而重貼成本極低：查核者手上的證據（密封 source 723 passed、合併樹 944 passed、五檔 Ruff、`merge-tree` 產出 `f65a7ed7457b813546ff53782d23317bc6f45c73`、兩個真實漂移 worktree 的 exit 6 / exit 0）直接就能填進 `self_run` 的 `command`／`observed` 兩欄。

---

## 順帶開卡：#94

研究這一題時查到的東西比這一題本身大。

`review_cmd.py:216-221` 偵測到 `review-invalid` 之後只 `print` 到 stderr 然後 `return 4`——**沒有事件、沒有留言、Log 一行都沒有**。但 §1 的表格把 `review-invalid` 列在「結果／事件」欄，契約說它是事件。

再查下去，§1 的五個層次裡有三個沒有寫入者：

| §1 層次 | 事件型別 | 碼裡有寫入者 |
|---|---|---|
| 送審前檢查 | `preflight-failed` | 無（只在 `review.py:627` 的註解被提到） |
| 外部阻塞 | `status-change` → `⏸阻塞` | 無專責動詞；`⏸阻塞` 在 `project.py:41` 的狀態表裡，但 `amend_cmd.py:351` 明寫「轉 ⏸阻塞 是 lifecycle 決定……不由一個 [amend] 決定」 |
| 無效查核 | `review-invalid` | 無（五處命中全是註解、字串、`__all__`） |
| 實質查核 | `APPROVE`／`REQUEST_CHANGES` | 有 |
| 留痕解析停機 | `review-marker-clearance` | 有 |

**五個層次，機器只寫得出兩個。** 而 `card.append_log_line()` 就在 `card.py:439`——不是做不到，是沒接。

後果不是漏一筆流水帳：**「卡沒往前走」這件事在工具帳上不可見**。看板與 Log 只記錄成功的那條路，於是一張卡可以被反覆拒收而完全沒有訊號，也無法回答「這張卡到底卡在哪一關」。本卡今天就是活例——分支已合併進 main，而卡上看不到任何查核或合併紀錄。

已開 **#94 `WF-REVIEW-INVALID-TRACE1`**，射程只取「已被機械偵測、卻沒有寫入」的那一個；另兩個連機械偵測都沒有，屬不同工程量級，已記在 #94 的核心痛點裡明說是備忘不是承諾。

## Comment 5308049508 · 2026-08-16T14:58:02Z

## 需求方 2026-08-16 裁定：採丙案——不把該輸出當查核記，卡收回 📥Backlog

⚠️ 本留言由 PM 代擬代貼，內容為需求方於對話中的裁定。

### 診斷（推翻本卡稍早兩則留言的框架）

`issuecomment-5305806507` 把這件事寫成「留痕缺口，請查核者重貼」、`issuecomment-5307998582` 據此裁定甲案。**兩則的框架都錯了。**

查核者拒絕貼一份他知道仍然無效的裁決，並診斷出「只補 `self_run` 無法讓帳成立」——原先的錯誤訊息只是前置檢查提早返回，遮住了後續的 schema 錯誤。PM 獨立驗實三條：

- `validation.py:268-272`：`core_pain_resolved=no` 時 `review_result` 只能是 `REQUEST_CHANGES`
- `finding_class: test-adequacy` 不在 `FINDING_CLASSES` 列舉內
- R5-01／R5-02 都缺 `evidence` 與 `disposition`（`FINDING_KEYS` 要求全部非空）

而改成 `REQUEST_CHANGES` 會扭曲原意，且依 §1 會推向 `↩退回`、增加 iteration、計入 escalation——對一張已合併的 Backlog 卡全是錯的。

**真正的診斷是：schema 沒壞，是 PM 用錯通道。**

契約的第一判準是「核心痛點消失了沒」，即**查核講的是驗收，合併決定屬需求方**。PM 把「這個分支該不該合併」送進查核通道，得到一份長得像查核的回答，然後記不進去——因為它本來就不是查核。查核者在收據頭自寫 `review_scope: merge-suitability-not-acceptance`，那個 schema 不認識的欄位就是證據。

⚠️ **PM 的兩個操作錯誤**：(1) 以 `handoff --next-stage review` 把卡推到 🔍待查核、製造「有一份查核待落地」的預期；(2) 先合併才發現事件寫不進去，正確順序是先落事件再合併。

### 處置

- 卡自 🔍待查核 收回 **📥Backlog**（handoff，owner 待指派）。**不會有 review 事件落地。**
- 查核者的實質意見保留為 `issuecomment-5305745859`，**不進 finding 帳**。
- 分支已合併：PR #93 於 2026-08-16T12:53:15+08:00 squash merge，`origin/main` = `d18cd83`，CI 兩個 check 皆 SUCCESS。這是需求方的合併裁定，不需要 review 事件背書。

### ⚠️ 代價明列

兩條 non-blocking finding 不入帳：

- **R5-02**（finding 狀態帳面不精確）已於 op `7a9c7a0f` 修正。
- **R5-01**（`a5d3843` 的 mutation 宣稱過強——整段回退會紅，但只移除「今天的」「所以這一刻的」兩個限定詞仍是 1 passed，因三個 required token 可在後段繼續滿足、banned 字串受 reflow 空白影響沒命中）**無機械落點、會掉**。已轉由 **#91** 承接（op `88dc15c8` 新增為其第 5 條驗收條件；#91 本來就要動同一段 docstring）。

### 這個形狀另開卡

丙案解決了本卡，**沒有解決形狀**——下一次拿合併適用性去問查核者會再撞一次。已開 **#95 `WF-REVIEW-MERGE-SUITABILITY1`**：讓合併適用性成為一條可記錄的獨立軸，且**不得成為繞過第一判準的後門**。其驗收條 5 要求以本卡 2026-08-16 的原裁決重放，內容須能完整落地而不需刪改。

## Comment 5460928309 · 2026-08-29T06:55:49Z

## 阻塞登記

**狀態**：⏸阻塞。**來源狀態：📥Backlog**（解除時回到此狀態）。

**阻塞原因**：需求方於 2026-08-29 決定，在階段狀態重整（8 階段 × 10 狀態、待審清單、CLI 射程收斂）定案並落地前，暫停所有 ai-workflow 流程卡，避免它們與重構討論互相干擾。

**可證偽的解除條件**：待審清單機制上線（label ＋ issue template ＋ 可見分組）。屆時本卡改列為清單參考項，或依當時前提是否仍成立重新排程。

**本次未做**：核心痛點、驗收條件、射程一律未動。`iteration` 未遞增。`階段` 欄未寫入。本登記僅改交付狀態與 owner。

**已知的射程重疊**（供解除時參考，非本次裁定）：#66／#38 的實質可能由「七份交接文件格式」承接；#128 可能由「待審清單收件條件三·查重留痕」＋`open --from-issue` 承接；#11 的證據紀律已部分寫入 PM 準則但痛點（靠人記得）未消失。⛔ 上述皆未經裁定，解除時須逐張重驗。

**裁定者**：需求方 ruan6047，2026-08-29 本 session 對話中指示「把目前所有 WF 卡片暫停，避免干擾目前重構討論」。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

