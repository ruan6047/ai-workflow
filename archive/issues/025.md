# #25 WF-CLEANUP-GUARD1 破壞性收尾操作的守衛：reconcile 與 release 刪 worktree／分支前的前提
- state: closed  created: 2026-08-11T04:53:50Z  closed: 2026-08-12T08:54:53Z
- url: https://github.com/ruan6047/ai-workflow/issues/25
- comments: 38

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code
- 執行：待指派　查核：跨家族查核（T4 紅線：不可逆且會毀資料，須人工 sign-off）
- Initiative：—　spec 基線：自 ai-workflow#16 切出（需求方 2026-08-11 裁定縮小 #16 射程）。基準內容＝#16 設計文件 §5.3 於 SHA 2d361303ce438c6fecf475b2aaa1fcbc06518dc9 的狀態，源自 R7-001（critical，跨家族查核提出）。列 T4 的理由：操作不可逆且直接毀掉未提交的工作內容，屬 canonical §5 的資料正確性紅線；本卡未經實測與需求方 sign-off 不得結案。#16 縮為框架卡後只保留「release 與 reconcile 的破壞性步驟受本卡守衛節制」，前提本體歸本卡。
- DB：db_scope=none
- 服務的原始目標：讓任何會毀掉工作內容的自動化步驟，在所有前提可機械驗證成立前不得執行；無法判定時只回報不動手。

## 簡介
<!-- card-brief:begin -->
給會毀掉工作內容的破壞性收尾（handoff --next-stage release --cleanup）建立守衛：枚舉全部前提——無未提交變更、無 stash、無 locked worktree、無 active lease、目標未被佔用、待刪分支 tip 為 main 祖先（本地與遠端各自驗）——任一不成立即降為純偵測只回報；所有路徑禁 --force；並把前置條件與效果分離（終態寫入是狀態面序列最後一步），中斷後續作須觀測式而非讀本機進度記錄。**適用時機**：要改 cli/src/wf_cli/cleanup.py 的刪除路徑或前提時；或收尾被擋、要查是哪一項前提不成立時。⛔ 非射程：不涵蓋 reconcile --apply（該指令尚不存在且完全無守衛，殘餘由 WF-RECONCILE-CLEANUP-GUARD1／aiwf#45 承接）；刪除順序引用 templates/worktree-lifecycle.md 第 11 行既有清單而不重述。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：破壞性收尾會移除 worktree、刪本地與遠端分支。canonical AI_WORKFLOW.md:146 明文「回收前先檢查未提交變更，禁止靜默刪除工作內容」，但既有設計與實作都沒有把該檢查變成守衛。本卡涵蓋今天真實存在的那一條路徑：handoff --next-stage release --cleanup。**reconcile --apply 完全無守衛，且該指令尚未存在**——原痛點指名的危險主體「一個無人看管的批次修復可以刪掉別人尚未提交的工作」指的正是它，**本卡未關閉它**，該殘餘由 WF-RECONCILE-CLEANUP-GUARD1 承接。本卡在 release 之外真正買到的第二件東西是形狀：收尾 executor 刻意設計成兩個觸發者共用、函式體內取不到觸發者標籤，使 reconcile 建成時可直接接上而不需重寫守衛；該形狀已由 AST 檢查、介面面與七個分叉突變釘住（含 M48——整份既有行為套件全綠、只有新增的 AST 規則殺得掉那條）。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:docs/WF_CLEANUP_GUARD1.md",
    "file:cli/src/wf_cli/cleanup.py",
    "file:cli/src/wf_cli/doctor.py",
    "file:cli/src/wf_cli/commands/doctor_cmd.py",
    "file:cli/src/wf_cli/commands/handoff_cmd.py",
    "file:cli/tests/test_cleanup.py",
    "file:cli/tests/test_doctor.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 枚舉全部前提，任一不成立即降純偵測只回報：無未提交變更（git status --porcelain 空、無 stash、無 locked worktree）、無 active lease、目標未被佔用（非任何 shell 的 cwd、非 primary worktree）、待刪分支 tip 為 main 祖先（本地與遠端各自驗）。
- [ ] 所有觸發路徑一律禁用 --force 及等價旗標；需要強制的情境即為需要人判斷的定義。唯一例外是帶明確期望 tip 的 --force-with-lease 條件式刪除，且該例外的形狀須由機械判準釘死。
- [ ] 刪除順序沿用 worktree-lifecycle.md 第 11 行既有清單，本卡引用而不重述。
- [ ] **（2026-08-12 需求方裁定，正式縮小射程）本卡的實作射程限於 release 觸發路徑。** reconcile --apply 白名單第 2 條的接線歸 #16 §9 的 G 卡。理由：reconcile 子命令目前不存在於 cli.py，且它在 #16 §5.2 標為 reserved pending 本卡，兩卡會互相等待。**此前的驗收條文要求「無論由 release 或 reconcile 觸發都是同一份實作、不得依觸發者切分實作範圍」，該條文自本次修訂起不再適用**——先前該裁定只記在 checkpoint 留言與 handoff 證據，未寫進卡面，導致 R3 查核者對著卡面正確判定驗收未達成（R3-001，attribution 應為 coordinator 而非 executor）。
- [ ] **單一 executor 形狀須保留**：release 路徑必須經由 execute_closeout_transition，且該函式不得因只接一條路徑而內含 release 專屬邏輯——後續接 reconcile 時只應新增呼叫點，不得需要複製或分叉實作。這是縮小射程的代價上限。
- [ ] **卡面與交付文件須明載 reconcile 側尚未受任何守衛**，且核心痛點僅部分關閉。查核者判定 core_pain_resolved 時，判準為「本卡宣告射程（release 路徑）內的痛點是否消失」，不以 reconcile 未接線為由判 no；但若文件對該限制的揭露不足或語氣淡化，仍應判 no。
- [ ] **前置條件與效果必須分離，不得構成循環**：權威清單第 1–3 步（merge 複驗＋push／worktree 與分支清理／資源宣告釋放）為前置條件；第 4 步（Issue 關閉＋release 事件＋終態落地）是本轉換的效果本身，不得列為前置；第 5–7 步（卡檔封存／Ledger 投影重建／對帳三件套）為其後義務，三者皆不寫狀態面。
- [ ] **終態寫入是狀態面序列的最後一步**：第 1–3 步完成後才寫 🏁完成／關閉 Issue。
- [ ] **明定合法的暫時中間態**：本機資源可部分完成（worktree 已移除但分支未刪等）；遠端狀態僅限非終態。不允許終態寫入或關閉 Issue 先於第 1–3 步完成。
- [ ] **中斷後的續作必須是觀測式的**：重新讀取當下事實判斷剩餘步驟，不得依賴任何「做到哪」的本機記錄；續作須推進到完成或維持在合法暫時態。

## 驗證

- [ ] 以真實 worktree 做破壞性測試：分別在有未提交變更、有 stash、有 active lease、worktree 為當前 cwd、分支未合併五種情境下執行，必須全數拒絕刪除並回報原因；且測試須驗證「拒絕後工作內容仍完整存在」，不是只驗回傳碼。
- [ ] 故障注入：在收尾轉換的每個步驟之間中斷，續作後不得產生半完成組合（例如 Issue 已關但分支仍在），也不得重複刪除。每個步驟間隙都要有對應案例。
- [ ] **循環前置專項**：驗證守衛不檢查第 4 步（否則 release 永遠無法發動），且第 5–7 步未完成不阻擋 release。
- [ ] 驗證 --force 在 reconcile 路徑確實不可用（不只是文件寫著）。
- [ ] T4 紅線：跨家族或人工審核，且最高風險項（實際刪除路徑）由需求方 sign-off。
## Log

- 2026-08-11T12:53:48+08:00 open by Claude Opus 5@Claude Code；owner 待指派；iteration 0。
- 2026-08-11T13:42:32+08:00 amend by wf-cli（op 64a28d93）→ 驗收條件：原值「[ ] 枚舉全部前提，任一不成立即降純偵測只回報：無未提交變更（git status --porcelain 空、無 stash、無 locked worktree）、無 active lease、目標未被佔用（非任何 shell 的 cwd、非 primary worktree）、待刪分支 tip 為 main 祖先（本地與遠端各自驗）。；[ ] reconcile 路徑一律禁用 --force 及等價旗標；需要強制的情境即為需要人判斷的定義。；[ ] 同一組前提亦適用 release 內含的 cleanup；差別僅在 release 由操作者當場發動，故 reconcile 側的前提不得放寬。；[ ] 刪除順序沿用 worktree-lifecycle.md 第 11 行既有清單（先離開 worktree 再移除目錄、刪本地分支、刪遠端分支），本卡引用而不重述。」→ 新值「枚舉全部前提，任一不成立即降純偵測只回報：無未提交變更（git status --porcelain 空、無 stash、無 locked worktree）、無 active lease、目標未被佔用（非任何 shell 的 cwd、非 primary worktree）、待刪分支 tip 為 main 祖先（本地與遠端各自驗）。；reconcile 路徑一律禁用 --force 及等價旗標；需要強制的情境即為需要人判斷的定義。；同一組前提亦適用 release 內含的 cleanup；差別僅在 release 由操作者當場發動，故 reconcile 側的前提不得放寬。；刪除順序沿用 worktree-lifecycle.md 第 11 行既有清單（先離開 worktree 再移除目錄、刪本地分支、刪遠端分支），本卡引用而不重述。；**（2026-08-11 追加，承 #16 R8-001）本卡承接整個收尾轉換，不得依破壞性與否切分實作範圍。** reconcile 白名單第 2 條為單一 guarded transition，全有或全無（#16 §5.2.1）；把它拆給兩張卡實作等於在實作層重建已被否決的部分套用路徑。；**終態寫入必須是最後一步**：清理完成後才寫 🏁完成／關閉 Issue，順序即 worktree-lifecycle.md 第 11 行清單。關閉 Issue 是收尾完成的可觀測標記，不得先於清理。；**中斷後的續作必須是觀測式的**：轉換若在中途中斷，續作重新讀取當下事實判斷剩餘步驟，不得依賴任何「做到哪」的本機記錄（呼應 #16 §4.2 的本機零狀態）。」；理由 #16 R9 指出：正文 §5.2.1 已禁止部分套用，但 §9 的 G 卡仍把同一 cleanup transition 依破壞性與否拆給兩張卡，實作時會重建被否決的半完成路徑。整個轉換改歸本卡，並補上終態寫入順序、觀測式續作與故障注入三項——前兩項原本沒有任何卡承接。
- 2026-08-11T13:42:32+08:00 amend by wf-cli（op 64a28d93）→ 驗證：原值「[ ] 以真實 worktree 做破壞性測試：分別在有未提交變更、有 stash、有 active lease、worktree 為當前 cwd、分支未合併五種情境下執行，必須全數拒絕刪除並回報原因；且測試須驗證「拒絕後工作內容仍完整存在」，不是只驗回傳碼。；[ ] 驗證 --force 在 reconcile 路徑確實不可用（不只是文件寫著）。；[ ] T4 紅線：跨家族或人工審核，且最高風險項（實際刪除路徑）由需求方 sign-off。」→ 新值「以真實 worktree 做破壞性測試：分別在有未提交變更、有 stash、有 active lease、worktree 為當前 cwd、分支未合併五種情境下執行，必須全數拒絕刪除並回報原因；且測試須驗證「拒絕後工作內容仍完整存在」，不是只驗回傳碼。；**故障注入**：在收尾轉換的每個步驟之間中斷，續作後不得產生半完成組合（例如 Issue 已關但分支仍在），也不得重複刪除。每個步驟間隙都要有對應案例。；驗證 --force 在 reconcile 路徑確實不可用（不只是文件寫著）。；T4 紅線：跨家族或人工審核，且最高風險項（實際刪除路徑）由需求方 sign-off。」；理由 #16 R9 指出：正文 §5.2.1 已禁止部分套用，但 §9 的 G 卡仍把同一 cleanup transition 依破壞性與否拆給兩張卡，實作時會重建被否決的半完成路徑。整個轉換改歸本卡，並補上終態寫入順序、觀測式續作與故障注入三項——前兩項原本沒有任何卡承接。
- 2026-08-11T16:19:55+08:00 amend by wf-cli（op a2ef40db）→ 驗收條件：原值「[ ] 枚舉全部前提，任一不成立即降純偵測只回報：無未提交變更（git status --porcelain 空、無 stash、無 locked worktree）、無 active lease、目標未被佔用（非任何 shell 的 cwd、非 primary worktree）、待刪分支 tip 為 main 祖先（本地與遠端各自驗）。；[ ] reconcile 路徑一律禁用 --force 及等價旗標；需要強制的情境即為需要人判斷的定義。；[ ] 同一組前提亦適用 release 內含的 cleanup；差別僅在 release 由操作者當場發動，故 reconcile 側的前提不得放寬。；[ ] 刪除順序沿用 worktree-lifecycle.md 第 11 行既有清單（先離開 worktree 再移除目錄、刪本地分支、刪遠端分支），本卡引用而不重述。；[ ] **（2026-08-11 追加，承 #16 R8-001）本卡承接整個收尾轉換，不得依破壞性與否切分實作範圍。** reconcile 白名單第 2 條為單一 guarded transition，全有或全無（#16 §5.2.1）；把它拆給兩張卡實作等於在實作層重建已被否決的部分套用路徑。；[ ] **終態寫入必須是最後一步**：清理完成後才寫 🏁完成／關閉 Issue，順序即 worktree-lifecycle.md 第 11 行清單。關閉 Issue 是收尾完成的可觀測標記，不得先於清理。；[ ] **中斷後的續作必須是觀測式的**：轉換若在中途中斷，續作重新讀取當下事實判斷剩餘步驟，不得依賴任何「做到哪」的本機記錄（呼應 #16 §4.2 的本機零狀態）。」→ 新值「枚舉全部前提，任一不成立即降純偵測只回報：無未提交變更（git status --porcelain 空、無 stash、無 locked worktree）、無 active lease、目標未被佔用（非任何 shell 的 cwd、非 primary worktree）、待刪分支 tip 為 main 祖先（本地與遠端各自驗）。；reconcile 路徑一律禁用 --force 及等價旗標；需要強制的情境即為需要人判斷的定義。；同一組前提亦適用 release 內含的 cleanup；差別僅在 release 由操作者當場發動，故 reconcile 側的前提不得放寬。；刪除順序沿用 worktree-lifecycle.md 第 11 行既有清單（先離開 worktree 再移除目錄、刪本地分支、刪遠端分支），本卡引用而不重述。；**本卡是收尾轉換的唯一機械 executor。** 無論由 release（操作者當場發動）或 reconcile --apply 白名單第 2 條（批次）觸發，都是同一份實作；**不得依破壞性與否、亦不得依觸發者切分實作範圍**。#16 §9 的 G 卡只保留 merge 後置與白名單第 1 條。；**終態寫入必須是最後一步**：清理完成後才寫 🏁完成／關閉 Issue。關閉 Issue 是收尾完成的可觀測標記，不得先於清理。；**明定合法的暫時中間態**（#16 §5.2.1）：本機資源可部分完成（worktree 已移除但分支未刪等）；遠端狀態僅限非終態（仍 📦已合併、Issue 仍開啟）。**不允許終態寫入或關閉 Issue 先於清理完成。**；**中斷後的續作必須是觀測式的**：重新讀取當下事實判斷剩餘步驟，不得依賴任何「做到哪」的本機記錄（#16 §4.2 本機零狀態）；續作須推進到完成或維持在合法暫時態，不得停在已寫終態但未清理完的組合。」；理由 #16 R10：(1)「沒有中間態」的表述錯誤——本卡明定可中斷與觀測式續作，即表示執行期一定有中間態，故須改為明定哪些暫時態合法；(2) G 與本卡對 release-收尾 transition 所有權重疊，須確保只有一個機械 executor。兩點皆為 R8-001 第三輪的處置。
- 2026-08-11T18:01:34+08:00 amend by wf-cli（op 8325ca29）→ 驗收條件：原值「[ ] 枚舉全部前提，任一不成立即降純偵測只回報：無未提交變更（git status --porcelain 空、無 stash、無 locked worktree）、無 active lease、目標未被佔用（非任何 shell 的 cwd、非 primary worktree）、待刪分支 tip 為 main 祖先（本地與遠端各自驗）。；[ ] reconcile 路徑一律禁用 --force 及等價旗標；需要強制的情境即為需要人判斷的定義。；[ ] 同一組前提亦適用 release 內含的 cleanup；差別僅在 release 由操作者當場發動，故 reconcile 側的前提不得放寬。；[ ] 刪除順序沿用 worktree-lifecycle.md 第 11 行既有清單（先離開 worktree 再移除目錄、刪本地分支、刪遠端分支），本卡引用而不重述。；[ ] **本卡是收尾轉換的唯一機械 executor。** 無論由 release（操作者當場發動）或 reconcile --apply 白名單第 2 條（批次）觸發，都是同一份實作；**不得依破壞性與否、亦不得依觸發者切分實作範圍**。#16 §9 的 G 卡只保留 merge 後置與白名單第 1 條。；[ ] **終態寫入必須是最後一步**：清理完成後才寫 🏁完成／關閉 Issue。關閉 Issue 是收尾完成的可觀測標記，不得先於清理。；[ ] **明定合法的暫時中間態**（#16 §5.2.1）：本機資源可部分完成（worktree 已移除但分支未刪等）；遠端狀態僅限非終態（仍 📦已合併、Issue 仍開啟）。**不允許終態寫入或關閉 Issue 先於清理完成。**；[ ] **中斷後的續作必須是觀測式的**：重新讀取當下事實判斷剩餘步驟，不得依賴任何「做到哪」的本機記錄（#16 §4.2 本機零狀態）；續作須推進到完成或維持在合法暫時態，不得停在已寫終態但未清理完的組合。」→ 新值「枚舉全部前提，任一不成立即降純偵測只回報：無未提交變更（git status --porcelain 空、無 stash、無 locked worktree）、無 active lease、目標未被佔用（非任何 shell 的 cwd、非 primary worktree）、待刪分支 tip 為 main 祖先（本地與遠端各自驗）。；reconcile 路徑一律禁用 --force 及等價旗標；需要強制的情境即為需要人判斷的定義。；同一組前提亦適用 release 內含的 cleanup；差別僅在 release 由操作者當場發動，故 reconcile 側的前提不得放寬。；刪除順序沿用 worktree-lifecycle.md 第 11 行既有清單，本卡引用而不重述。；**本卡是收尾轉換的唯一機械 executor。** 無論由 release（操作者當場發動）或 reconcile --apply 白名單第 2 條（批次）觸發，都是同一份實作；不得依破壞性與否、亦不得依觸發者切分實作範圍。#16 §9 的 G 卡只保留 merge 後置與白名單第 1 條。；**前置條件與效果必須分離，不得構成循環**：權威清單第 1–3 步（merge 複驗＋push／worktree 與分支清理／資源宣告釋放）為**前置條件**；第 4 步（Issue 關閉＋release 事件＋終態落地）是**本轉換的效果本身**，不得列為前置；第 5–7 步（卡檔封存／Ledger 投影重建／對帳三件套）為**其後義務**，三者皆不寫狀態面。；**終態寫入是狀態面序列的最後一步，不是整份清單的最後一步**：第 1–3 步完成後才寫 🏁完成／關閉 Issue；其後仍有第 5–7 步，但那三步不寫狀態面，故不與此限制衝突。；**明定合法的暫時中間態**（#16 §5.2.1）：本機資源可部分完成（worktree 已移除但分支未刪等）；遠端狀態僅限非終態（仍 📦已合併、Issue 仍開啟）。不允許終態寫入或關閉 Issue 先於第 1–3 步完成。；**中斷後的續作必須是觀測式的**：重新讀取當下事實判斷剩餘步驟，不得依賴任何「做到哪」的本機記錄（#16 §4.2 本機零狀態）；續作須推進到完成或維持在合法暫時態，不得停在已寫終態但未清理完的組合。」；理由 #16 R11：release 守衛要求七步清單全數完成，但第 4 步（Issue 關閉＋release 事件＋終態）正是 release 自己的效果，構成循環前置；且「終態是最後一步」與清單第 5–7 步在其後相衝。前置／效果／後續義務三段須明確分離。
- 2026-08-11T18:01:34+08:00 amend by wf-cli（op 8325ca29）→ 驗證：原值「[ ] 以真實 worktree 做破壞性測試：分別在有未提交變更、有 stash、有 active lease、worktree 為當前 cwd、分支未合併五種情境下執行，必須全數拒絕刪除並回報原因；且測試須驗證「拒絕後工作內容仍完整存在」，不是只驗回傳碼。；[ ] **故障注入**：在收尾轉換的每個步驟之間中斷，續作後不得產生半完成組合（例如 Issue 已關但分支仍在），也不得重複刪除。每個步驟間隙都要有對應案例。；[ ] 驗證 --force 在 reconcile 路徑確實不可用（不只是文件寫著）。；[ ] T4 紅線：跨家族或人工審核，且最高風險項（實際刪除路徑）由需求方 sign-off。」→ 新值「以真實 worktree 做破壞性測試：分別在有未提交變更、有 stash、有 active lease、worktree 為當前 cwd、分支未合併五種情境下執行，必須全數拒絕刪除並回報原因；且測試須驗證「拒絕後工作內容仍完整存在」，不是只驗回傳碼。；故障注入：在收尾轉換的每個步驟之間中斷，續作後不得產生半完成組合（例如 Issue 已關但分支仍在），也不得重複刪除。每個步驟間隙都要有對應案例。；**循環前置專項**：驗證守衛不檢查第 4 步（否則 release 永遠無法發動），且第 5–7 步未完成不阻擋 release。；驗證 --force 在 reconcile 路徑確實不可用（不只是文件寫著）。；T4 紅線：跨家族或人工審核，且最高風險項（實際刪除路徑）由需求方 sign-off。」；理由 #16 R11：release 守衛要求七步清單全數完成，但第 4 步（Issue 關閉＋release 事件＋終態）正是 release 自己的效果，構成循環前置；且「終態是最後一步」與清單第 5–7 步在其後相衝。前置／效果／後續義務三段須明確分離。
- 2026-08-11T20:15:37+08:00 amend by wf-cli（op 9c33d1b5）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:docs/WF_CLEANUP_GUARD1.md" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:docs/WF_CLEANUP_GUARD1.md、file:cli/src/wf_cli/cleanup.py、file:cli/src/wf_cli/doctor.py、file:cli/src/wf_cli/commands/doctor_cmd.py、file:cli/tests/test_cleanup.py、file:cli/tests/test_doctor.py」；理由 資源盤查後確認 doctor.py／doctor_cmd.py／test_doctor.py 皆未被任何活卡佔用，故本卡可同時交付設計與實作；驗證條文要求真實 worktree 破壞性測試與故障注入，僅宣告設計文件無法滿足。
- 2026-08-11T20:17:54+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree claude/WF-CLEANUP-GUARD1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cleanup-guard1；交付狀態 🚧進行中。
- 2026-08-11T20:43:18+08:00 handoff by wf-cli → owner 跨家族查核（T4，待指派）；iteration 0；SHA a036ed5088ae44054654e532fe896ad6e14e7663；證據 PR https://github.com/ruan6047/ai-workflow/pull/27；pytest 347 passed（基線 292＋新增 55）；突變測試 21/21 KILLED（首輪 M19 存活後補測）；真資料唯讀實跑 2 repo × 2 worktree 皆正確 detect_only。T4：不得自我批准，最高風險項（實際刪除路徑）須需求方 sign-off。。
- 2026-08-11T21:19:45+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 跨家族查核（需求方於對話中轉貼原文；無 receipt marker，來源不可驗證）；core_pain_resolved no；self_run 3 項；findings 2 項（blocking 2）；attempt WF-CLEANUP-GUARD1-e0-a036ed5088ae44054654e532fe896ad6e14e7663。
- 2026-08-11T22:05:44+08:00 amend by wf-cli（op 455b98d9）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:docs/WF_CLEANUP_GUARD1.md", "file:cli/src/wf_cli/cleanup.py", "file:cli/src/wf_cli/doctor.py", "file:cli/src/wf_cli/commands/doctor_cmd.py", "file:cli/tests/test_cleanup.py", "file:cli/tests/test_doctor.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:docs/WF_CLEANUP_GUARD1.md、file:cli/src/wf_cli/cleanup.py、file:cli/src/wf_cli/doctor.py、file:cli/src/wf_cli/commands/doctor_cmd.py、file:cli/src/wf_cli/commands/handoff_cmd.py、file:cli/tests/test_cleanup.py、file:cli/tests/test_doctor.py、file:cli/tests/test_release_cleanup.py」；理由 需求方 2026-08-11 裁定 R1-002 的接線射程為「只接 release」：本輪把 handoff --next-stage release 接上 execute_closeout_transition，reconcile --apply 留給 #16 §9 的 G 卡。理由是 reconcile 在 #16 §5.2 白名單第 2 條標記為 reserved pending #25，先做會構成兩卡互等；而 release 是現行就有人用的路徑，接上守衛立即有價值。故擴充宣告加入 handoff_cmd.py。測試另立 test_release_cleanup.py 而非寫入 test_commands_mocked.py——後者由現役卡 WF-CLI-ROUTING-TIER1 佔用，寫入即破壞互斥契約。cli.py 不需納入（release 是既有子命令的行為變更，非新註冊）。。
- 2026-08-11T22:06:19+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 1；SHA a036ed5088ae44054654e532fe896ad6e14e7663；證據 R1 兩項 blocking，需求方已裁定射程。R1-001（遠端刪除前 TOCTOU）：一併修——遠端刪除前須重讀 branch SHA、確認 commit object 可觀測、重驗 merge-base --is-ancestor，失敗或不可觀測一律 detect_only，並加「清完本地分支後有人 push 新提交」的回歸測試。R1-002（唯一 executor 未接線）：需求方裁定「只接 release」——本輪把 handoff --next-stage release 接上 execute_closeout_transition，reconcile --apply 留給 #16 §9 的 G 卡（reconcile 指令目前不存在於 cli.py，且在 #16 §5.2 標記 reserved pending #25，先做構成兩卡互等）。卡面須明說 reconcile 側尚未受保護，核心痛點僅部分解決。資源宣告已於 op 455b98d9 擴充加入 handoff_cmd.py 與新測試檔 test_release_cleanup.py。。
- 2026-08-11T23:05:14+08:00 handoff by wf-cli → owner 跨家族查核（T4，待需求方指派）；iteration 1；SHA b1273ab6a8b05adbb6496b774ebfb1935d384d78；證據 R2：兩項 blocking 依需求方裁定處置（5 檔全在宣告內；test_commands_mocked.py／cli.py／fake_gh.py 一字未動，#21 的互斥未被破壞）。R1-001：新增 recheck_remote_branch()，在 push --delete 前一刻以同一次 ls-remote 重讀 branch 與 main 當下 SHA、cat-file -e 確認 tip 可觀測、重驗 merge-base --is-ancestor，缺一即拒；拒絕收在新的 mode=aborted 而非併進 detect_only（已移除 worktree 的 run 自稱純偵測不誠實），效果第 4 步一併扣住、狀態停在合法的 cleanup_in_progress。回歸測試以另一個共用 bare remote 的 clone，在 after_delete_local_branch 時點 push 新提交，斷言遠端刪除被拒、理由指名 remote_tip_still_merged、並重新 clone 讀出檔案內容證明新提交仍在；參數化兩支覆蓋未 fetch 的 unobservable 與已 fetch 的 merge-base fail（少了後半，有人先 fetch 過守衛就退回舊行為）。R1-002：需求方裁定只接 release。handoff --next-stage release 已接上 execute_closeout_transition，--cleanup 為選配、預設不清理（理由：守衛擋得住誤刪前提，擋不住使用者根本沒想刪；漏清理可補跑、刪錯無補救），且刻意不提供 --main-ref／--remote。不帶旗標的 release 會造出 illegal_terminal_before_cleanup 並印警示，事後補 --cleanup 會被擋（已寫成測試）。文件四處明說 reconcile 側尚未受保護、核心痛點僅部分解決，G 卡歸 #16 §9。清理中途失敗的四種情境狀態面一字未寫（前三者皆落 LEGAL_STATES，重跑即續作）。pytest 367 passed（基線 347）。突變 32/32 KILLED，M19 同型確認仍被殺；首輪 4 個存活體全部補測轉紅，其中 M30 是原測試綠得是因為錯誤的理由（拔掉分支後 exit code 碰巧也是 5，改斷言 executor 根本沒被啟動才殺得掉）。PM 獨立突變複驗：把二次確認的 verdict 強制為放行，8 個測試轉紅含該 TOCTOU 回歸，斷言非空。ruff 無新增項。T4 未結事項：--cleanup 路徑僅對真 git ＋假 GitHub 實跑，未對真實 Project／Issue 執行過，該最高風險項須需求方 sign-off，不得由執行者或 PM 代行。執行者自承七個未關的洞，含 reconcile 側全無守衛、effect writer 回報成功後未回頭重讀狀態面（與『push --delete 回 0 卻沒刪掉』同型但未被接住）、第 4 步的 Issue 結案留言未實作。。
- 2026-08-12T00:55:08+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（留有 receipt marker；PM 未能重算 report_sha256——報告經對話轉貼，位元組不可還原）；core_pain_resolved no；self_run 5 項；findings 1 項（blocking 1）；attempt WF-CLEANUP-GUARD1-e0-b1273ab6a8b05adbb6496b774ebfb1935d384d78。
- 2026-08-12T01:18:44+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 2；SHA b1273ab6a8b05adbb6496b774ebfb1935d384d78；證據 R3：R2-001（critical，跨家族查核以隔離實測重現資料遺失）——recheck_remote_branch() 回傳 delete 後、push --delete 送出前仍有時間窗，兩者間無 compare-and-swap；現有回歸測試的 step_hook 打在 after_delete_local_branch，早於二次確認，未覆蓋該窗。R1-002 已 resolved（release 接線）。escalation checkpoint 見同日留言：第二條件成立（R1-001 明列仍開啟）故 decision=escalate，需求方裁定 continue 並指定方向「先試條件式刪除」。PM 實測前提：git push origin --force-with-lease=refs/heads/X:<過期SHA> :refs/heads/X 會被 stale info 拒絕且分支存活，帶當下 SHA 才刪得掉——該原子操作可得，不需退讓為不自動刪；但實測用本機 bare repo，真實 GitHub 行為須另驗。。
- 2026-08-12T01:59:48+08:00 handoff by wf-cli → owner 跨家族查核（T4，待需求方指派）；iteration 2；SHA bc099f658642ce53d1dd7e7106a291df6b4adc5d；證據 R3：R2-001 依需求方裁定改為條件式刪除。複驗改回傳 RemoteDeleteDecision(verdict, check, expected_tip)，讀到的 tip 原樣成為租約期望值，經唯一刪除入口 conditional_delete_args() 組成 push --force-with-lease=refs/heads/<branch>:<tip> origin --delete <branch>；沒有期望 tip 就組不出指令（丟 CleanupGuardError，不退回無條件刪除）。_forbid_force 只開形狀固定的窄口：裸 lease、短名 refspec、全零期望值、非 SHA 期望值一律仍擋——那四種都會讓租約靜默失效。刪除被拒的處置與守衛同型：具名 remote_delete_lease_refused、降 aborted、效果扣住、CLI rc=5，不重試不降級。真實 GitHub 驗證分兩半，執行者誠實劃界：拒絕路徑已實證——對 github.com:ruan6047/ai-workflow.git（SSH）以 --dry-run 送租約過期的刪除得 ! [rejected] (delete) (stale info)、returncode 1、GIT_TRACE_PACKET 顯示客戶端只送出一個 flush、一條更新指令都沒送，證明租約檢查完全在客戶端對 GitHub 剛送出的 ref advertisement 完成；接受路徑未實證——需在真實遠端建拋棄式探針分支，該次 push 被執行環境權限層擋下，執行者未繞道（明說後來自己分支的 push 是不同指令形狀、未回頭重試被拒的那一個）。替代證據在本機 bare repo 含線路追蹤：接受時線路上是 <非零 old-oid> 0000… refs/heads/x，與無租約刪除的 old-oid 相同，故租約真正加上去的就是客戶端那次比對。未證明 GitHub receive-pack 是否對 delete 做 old-oid CAS、advertisement 是否恆為最新（該風險所有 --force-with-lease 使用者共有）；失敗方向安全（誤拒＝aborted 雜訊非資料遺失）故未改走 fail-closed。新測試改用 runner 攔截，卡在「複驗已回傳可刪」與「git 真的被執行」之間；反假綠設計四條：斷言注入真的發生、先斷言遠端工作還在（重新 clone 讀回內容）再斷言記帳、斷言複驗那一筆是 pass（擋下的是租約不是複驗）、逐字比對送出的租約等於複驗讀到的 tip。pytest 379 passed（基線 b1273ab 實測 367）。突變 11/11 KILLED。PM 已獨立複驗最關鍵的一項：植入 M34（拿掉租約退回無條件刪除）後，舊的 TOCTOU 測試 2 passed 存活，全套 4 紅含新測試——注入點差一步就差一整條覆蓋，為證據非論述。執行者另報兩件方法上的事：M41 第一次的「殺掉」是假的（拿掉 worktree remove 失敗檢查後照樣丟 CleanupGuardError，只是晚一步炸在 branch -d），補「停在哪一步」的斷言才真殺掉；並加了反向突變體 M36（連合法租約也擋）防止「寫成全擋也會全綠」。執行者主動把 doc §9 第 2 項（effect writer 回報成功不等於狀態面真的變了）的嚴重度調高，並明說不應再被描述為「與 §3.3 同類、已被同一招接住」——R2-001 的教訓是「讀一次不構成保證」，該洞是同形狀在狀態面的翻版，而 GitHub 側沒有 --force-with-lease 這種現成工具。仍未關：reconcile 側無守衛（指令尚不存在）、接受路徑未對真實 GitHub 實跑、advertisement 到套用之間的毫秒級窗客戶端無法涵蓋。T4 未結事項不變：最高風險項須需求方 sign-off；PM 於 R2 期間已在真實狀態面實跑過拋棄式卡的成功與拒絕路徑，但那是 b1273ab 的碼，本輪的條件式刪除未再實跑一次。。
- 2026-08-12T07:10:14+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（收據 issuecomment-5259852016，多行格式合規；PM 回讀重算 report_sha256=2d8f6618… 相符，但試到第三個邊界變體才對上——其 report_end 未指明起始 LF 是否納入。⚠️ 被雜湊區段只涵蓋本 YAML，前輪閉環回報與核心痛點陳述在 report-end 之後、不受雜湊保護）；core_pain_resolved no；self_run 5 項；findings 1 項（blocking 1）；attempt WF-CLEANUP-GUARD1-e0-bc099f658642ce53d1dd7e7106a291df6b4adc5d。
- 2026-08-12T07:17:04+08:00 amend by wf-cli（op 3cd13f81）→ 驗收條件：原值「[ ] 枚舉全部前提，任一不成立即降純偵測只回報：無未提交變更（git status --porcelain 空、無 stash、無 locked worktree）、無 active lease、目標未被佔用（非任何 shell 的 cwd、非 primary worktree）、待刪分支 tip 為 main 祖先（本地與遠端各自驗）。；[ ] reconcile 路徑一律禁用 --force 及等價旗標；需要強制的情境即為需要人判斷的定義。；[ ] 同一組前提亦適用 release 內含的 cleanup；差別僅在 release 由操作者當場發動，故 reconcile 側的前提不得放寬。；[ ] 刪除順序沿用 worktree-lifecycle.md 第 11 行既有清單，本卡引用而不重述。；[ ] **本卡是收尾轉換的唯一機械 executor。** 無論由 release（操作者當場發動）或 reconcile --apply 白名單第 2 條（批次）觸發，都是同一份實作；不得依破壞性與否、亦不得依觸發者切分實作範圍。#16 §9 的 G 卡只保留 merge 後置與白名單第 1 條。；[ ] **前置條件與效果必須分離，不得構成循環**：權威清單第 1–3 步（merge 複驗＋push／worktree 與分支清理／資源宣告釋放）為**前置條件**；第 4 步（Issue 關閉＋release 事件＋終態落地）是**本轉換的效果本身**，不得列為前置；第 5–7 步（卡檔封存／Ledger 投影重建／對帳三件套）為**其後義務**，三者皆不寫狀態面。；[ ] **終態寫入是狀態面序列的最後一步，不是整份清單的最後一步**：第 1–3 步完成後才寫 🏁完成／關閉 Issue；其後仍有第 5–7 步，但那三步不寫狀態面，故不與此限制衝突。；[ ] **明定合法的暫時中間態**（#16 §5.2.1）：本機資源可部分完成（worktree 已移除但分支未刪等）；遠端狀態僅限非終態（仍 📦已合併、Issue 仍開啟）。不允許終態寫入或關閉 Issue 先於第 1–3 步完成。；[ ] **中斷後的續作必須是觀測式的**：重新讀取當下事實判斷剩餘步驟，不得依賴任何「做到哪」的本機記錄（#16 §4.2 本機零狀態）；續作須推進到完成或維持在合法暫時態，不得停在已寫終態但未清理完的組合。」→ 新值「枚舉全部前提，任一不成立即降純偵測只回報：無未提交變更（git status --porcelain 空、無 stash、無 locked worktree）、無 active lease、目標未被佔用（非任何 shell 的 cwd、非 primary worktree）、待刪分支 tip 為 main 祖先（本地與遠端各自驗）。；所有觸發路徑一律禁用 --force 及等價旗標；需要強制的情境即為需要人判斷的定義。唯一例外是帶明確期望 tip 的 --force-with-lease 條件式刪除，且該例外的形狀須由機械判準釘死。；刪除順序沿用 worktree-lifecycle.md 第 11 行既有清單，本卡引用而不重述。；**（2026-08-12 需求方裁定，正式縮小射程）本卡的實作射程限於 release 觸發路徑。** reconcile --apply 白名單第 2 條的接線歸 #16 §9 的 G 卡。理由：reconcile 子命令目前不存在於 cli.py，且它在 #16 §5.2 標為 reserved pending 本卡，兩卡會互相等待。**此前的驗收條文要求「無論由 release 或 reconcile 觸發都是同一份實作、不得依觸發者切分實作範圍」，該條文自本次修訂起不再適用**——先前該裁定只記在 checkpoint 留言與 handoff 證據，未寫進卡面，導致 R3 查核者對著卡面正確判定驗收未達成（R3-001，attribution 應為 coordinator 而非 executor）。；**單一 executor 形狀須保留**：release 路徑必須經由 execute_closeout_transition，且該函式不得因只接一條路徑而內含 release 專屬邏輯——後續接 reconcile 時只應新增呼叫點，不得需要複製或分叉實作。這是縮小射程的代價上限。；**卡面與交付文件須明載 reconcile 側尚未受任何守衛**，且核心痛點僅部分關閉。查核者判定 core_pain_resolved 時，判準為「本卡宣告射程（release 路徑）內的痛點是否消失」，不以 reconcile 未接線為由判 no；但若文件對該限制的揭露不足或語氣淡化，仍應判 no。；**前置條件與效果必須分離，不得構成循環**：權威清單第 1–3 步（merge 複驗＋push／worktree 與分支清理／資源宣告釋放）為前置條件；第 4 步（Issue 關閉＋release 事件＋終態落地）是本轉換的效果本身，不得列為前置；第 5–7 步（卡檔封存／Ledger 投影重建／對帳三件套）為其後義務，三者皆不寫狀態面。；**終態寫入是狀態面序列的最後一步**：第 1–3 步完成後才寫 🏁完成／關閉 Issue。；**明定合法的暫時中間態**：本機資源可部分完成（worktree 已移除但分支未刪等）；遠端狀態僅限非終態。不允許終態寫入或關閉 Issue 先於第 1–3 步完成。；**中斷後的續作必須是觀測式的**：重新讀取當下事實判斷剩餘步驟，不得依賴任何「做到哪」的本機記錄；續作須推進到完成或維持在合法暫時態。」；理由 需求方 2026-08-12 裁定：正式把「只接 release」寫進卡面規範欄位。R3 跨家族查核以此判 critical blocking（R3-001）——而該判定是對的：卡面驗收逐字要求兩條觸發路徑都由同一實作接線，需求方於 2026-08-11 的縮小射程裁定只寫進 checkpoint 留言與 handoff 證據，從未 amend 進規範欄位。**該 finding 的 attribution 實為 coordinator（PM 未落實裁定），非 executor。** 本次修訂同時加入兩項先前未明文的條件：單一 executor 形狀須保留（避免縮小射程變成分叉實作），以及 core_pain_resolved 的判準改以本卡宣告射程為界但揭露不足仍判 no。⚠️ **寫入通道限制須記錄**：wfcli amend 無 --core-pain 旗標，核心痛點段落無法經唯一寫入通道修改。查核者要求「正式更正驗收與核心痛點」，本次只做得到前者；核心痛點仍描述 reconcile 與 release 兩條路徑，該落差由本次驗收條文第 6 項的判準吸收，但那是繞過而非修好。此缺口另記，候選歸 #9。。
- 2026-08-12T07:24:02+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 3；SHA bc099f658642ce53d1dd7e7106a291df6b4adc5d；證據 R4：卡面已於 amend op 3cd13f81 正式縮小射程為 release-only，R3-001 的處置（修卡面）已完成，其 attribution 經 PM 更正為 coordinator。本輪不是修 R3-001 的實作面，而是兩件必須的事：(1) **機械前提**——attempt_id = <card>-e<epoch>-<source_sha>，R3 的裁決已用 bc099f6 在 epoch 0 寫過一次；同 SHA 再審會產生第二則同 attempt 事件，doctor.py:409-415 一律判 marker_quarantined 且 clearance 的留言平面表示法尚未定義（#30 未開工），#21 即因此被鎖至今。故必須有新 SHA 才能重新派審。(2) **實質**——新驗收條文加了兩項交付文件尚未回應的條件：單一 executor 形狀須保留（後續接 reconcile 只應新增呼叫點，不得複製或分叉實作），以及 core_pain_resolved 的判準改以本卡宣告射程為界但揭露不足仍判 no。文件目前把 release-only 描述成別處記錄的射程決定，amend 後它是卡面的規範要求，敘事基礎需對齊。。
- 2026-08-12T08:52:49+08:00 handoff by wf-cli → owner 跨家族查核（T4，待需求方指派）；iteration 3；SHA bbce273877ac8d8df9409c9a5c7830fd2f4eb415；證據 R4：本輪為 R3-001 的處置後續與跨卡對帳 X5，非新一輪實作。R3-001（critical，closeout-executor-not-wired-to-real-destructive-paths）的處置是修卡面——amend op 3cd13f81 正式把射程縮小為 release-only 並加兩項新條文（單一 executor 形狀須保留；core_pain_resolved 以本卡宣告射程為界但揭露不足仍判 no）；PM 已將該 finding 的 attribution 更正為 coordinator，因需求方 2026-08-11 的裁定 PM 只寫進 checkpoint 留言與 handoff 證據、從未 amend 進規範欄位。b29d2c7 回應新條文：以 AST＋介面面＋七個分叉突變體檢查單一 executor 形狀（現行實作已符合但先前只是碰巧成立，新增兩條測試釘住），並改寫三處「reconcile 已共用 executor」的假現在式敘述，敘事基礎由 checkpoint 留言換為卡面驗收第 4 條。bbce273 處理 X5：把「本卡把不可逆刪除接在一個首寫不自描述的動詞上」寫成 §9 第 10 項，與 §9 第 2 項的分野寫成雙向可發現。PM 獨立複驗：M48（複驗沒帶回 tip 的保險絲在 release 被略過）對既有測試 379 passed 存活、對新 AST 測試 FAILED——注入點差一步就差一整條覆蓋；cleanup.py 的 diff 逐行核為 docstring 零邏輯改動；382 passed。PM 另於真實 GitHub 補跑條件式刪除（拋棄式卡 #33），GIT_TRACE_PACKET 捕到 old-oid 為複驗讀到的 tip 而非全零；並以獨立探針證明帶明確期望值時租約比對的是遠端當下廣告值而非本地過期追蹤 ref（保護比執行者論證的更強），該實驗與其未證部分見同卡報告。escalation checkpoint 見同日留言：兩條件皆不成立，decision=continue；兩個根因家族各差一次即滿足門檻，派審詞已要求沿用家族名。自審收斂紀錄與四項殘留見同日跨卡對帳留言。。
- 2026-08-12T09:26:59+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（收據 issuecomment-5260924860，多行格式合規；PM 已回讀重算 report_sha256=7a9df9fd… 相符。⚠️ 被雜湊區段末尾另有三段散文（核心痛點裁決／驗收與證據覆核／範圍外發現），解析器不接受區塊內混散文，故本 event 只轉錄 YAML 部分；散文原文在收據留言內且受同一雜湊保護）；core_pain_resolved no；self_run 5 項；findings 2 項（blocking 2）；attempt WF-CLEANUP-GUARD1-e0-bbce273877ac8d8df9409c9a5c7830fd2f4eb415。
- 2026-08-12T12:38:57+08:00 amend by wf-cli（op de18defc）→ 核心痛點：原值「reconcile --apply 與 release 的 cleanup 會移除 worktree、刪本地與遠端分支。canonical AI_WORKFLOW.md:146 明文「回收前先檢查未提交變更，禁止靜默刪除工作內容」，但既有設計與實作都沒有把該檢查變成守衛——一個無人看管的批次修復可以刪掉別人尚未提交的工作。」→ 新值「破壞性收尾會移除 worktree、刪本地與遠端分支。canonical AI_WORKFLOW.md:146 明文「回收前先檢查未提交變更，禁止靜默刪除工作內容」，但既有設計與實作都沒有把該檢查變成守衛。本卡涵蓋今天真實存在的那一條路徑：handoff --next-stage release --cleanup。**reconcile --apply 完全無守衛，且該指令尚未存在**——原痛點指名的危險主體「一個無人看管的批次修復可以刪掉別人尚未提交的工作」指的正是它，**本卡未關閉它**，該殘餘由 WF-RECONCILE-CLEANUP-GUARD1 承接。本卡在 release 之外真正買到的第二件東西是形狀：收尾 executor 刻意設計成兩個觸發者共用、函式體內取不到觸發者標籤，使 reconcile 建成時可直接接上而不需重寫守衛；該形狀已由 AST 檢查、介面面與七個分叉突變釘住（含 M48——整份既有行為套件全綠、只有新增的 AST 規則殺得掉那條）。」；理由 需求方 2026-08-12 裁定 R4-001 走出路 (a)：以唯一寫入通道正式更正核心痛點。R4 查核者判 critical blocking，disposition 逐字禁止「以縮小驗收條文間接覆寫核心痛點」，並要求由需求方裁定的可稽核更正或完成 reconcile 接線。背景：需求方 2026-08-11 即已裁定「只接 release」，但 PM 只寫進 checkpoint 留言與 handoff 證據、從未 amend 進規範欄位，查核者把該 finding 的 attribution 更正為 coordinator 是對的；今天是補上那個從未走完的通道，不是新決定。更正文字由 PM 寫死而非留給執行者措辭——--core-pain 是需求方授權通道，讓執行者自擬等於把授權轉手（需求方 2026-08-12 裁定）。三點必須全部出現且已全部出現：涵蓋範圍限於今天存在的 release 路徑；reconcile 無守衛且指令不存在、原危險主體未被關閉並已具名承接卡；executor 共用形狀是本卡真正買到的第二件東西（需求方認定），該認定使本卡與「只做一半」有實質區別。T4 sign-off 不隨本次更正給予，須待下一輪查核通過且最高風險項證據被確認後另行給出。不追溯補建或改寫任何歷史留痕（需求方明示）。；授權 依需求方 ruan6047 於 https://github.com/ruan6047/ai-workflow/issues/25#issuecomment-5262342420 的裁定（GitHub comment author 已逐字核對，非留言內文自述）。
- 2026-08-12T12:43:39+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 3；SHA 4353c1863f8b83e5532585dbcdcdb25e876098a2；證據 R5：兩件事。R4-002 已處置；R4-001 依需求方裁定走出路 (a) 由卡面更正承接。

R4-002（major，blocking，executor-trigger-branch-regression-guard-bypass）：執行者選 disposition 的第二條（可驗證的資料流限制）而非第一條（更完整的 AST 檢查），理由是後者無論做到多細，能誠實宣稱的都只有「常見寫法會被擋」，而 §4.0 要承擔的是「不得分叉」——強度對不上就只能改宣稱，等於把問題留著。作法：execute_closeout_transition 縮成只有一個運算式的貼標籤層，真正做事的 _execute_closeout 簽章裡沒有 trigger、也無同名自由變數或模組全域；公開簽章一字未改，handoff_cmd 與既有測試零改動；守衛仍在函式體內故繞過貼標籤層直接呼叫私有函式不會繞過守衛。

⚠️ 執行者自己抓到一件關鍵的事並據以重做：最初三個突變全死在**編譯期常數摺疊**上（"rec" + "oncile" 被摺成 reconcile），若就此收工，「3/3 KILLED」的承重點會站在編譯器最佳化上。它改用 "".join([...]) 做防摺疊版重跑，M54/M56 才是承重證據。PM 已於拋棄式目錄獨立注入查核者原句的防摺疊版驗證：test_the_destructive_body_cannot_name_the_trigger 轉紅、其餘 387 全綠。M55（走呼叫堆疊的防摺疊版）形狀面三層全綠、只有行為面接住——執行者據此把 §4.0 的宣稱誠實分成三段：可宣稱（函式體無法以名稱取得觸發者標籤、無法靠改名夾帶，執行者在 test_cleanup.py，作用域不及其他模組）、不可宣稱（「依觸發者分叉不可能」——走堆疊仍拿得到，這是實證不是保留意見）、是約定不是強制（reconcile 將來必須呼叫同一函式）。

R4-001（critical，blocking，closeout-executor-not-wired-to-real-destructive-paths）：需求方 2026-08-12 裁定走出路 (a)，核心痛點已以 wfcli amend --core-pain --ruling-url 正式更正（op de18defc，裁定留痕 issuecomment-5262342420，授權綁定生效）。查核者的 disposition 逐字禁止「以縮小驗收條文間接覆寫核心痛點」，故更正後的痛點自己寫下三件：涵蓋範圍限於今天真實存在的 release --cleanup 路徑；reconcile --apply 完全無守衛且該指令尚未存在，原痛點指名的危險主體「無人看管的批次修復」未被本卡關閉；executor 共用形狀是本卡在 release 之外真正買到的第二件東西（需求方認定），使 reconcile 建成時可直接接上而不需重寫守衛。殘餘已具名承接於新開的 WF-RECONCILE-CLEANUP-GUARD1（#45，T4），不留在本卡備註裡。

需求方 2026-08-11 即已裁定「只接 release」但 PM 只寫進 checkpoint 留言與 handoff 證據、從未 amend 進規範欄位，查核者把 R3-001 的 attribution 更正為 coordinator 是對的；本次是補上那個從未走完的通道。不追溯補建或改寫任何歷史留痕（需求方明示）。

⚠️ T4 sign-off 未給予。查核者逐字：「這些證據足以讓需求方做 sign-off 判斷，卻不能代替需求方 sign-off；目前未見該 sign-off，因此本卡也不得結案。」需求方裁定 sign-off 應待本輪查核通過且最高風險項（實際刪除路徑）證據被確認後另行給出。

驗證：pytest 382 → 388，寫入集三檔零逸出，無 .bak 殘留，marker 字面 0 處。執行者主動報告一件過程事故：突變 harness 批次跑 M51 時被 2 分鐘 timeout 砍掉、finally 未跑完而把突變留在工作樹（.bak 殘留），它在 commit 前逐檔讀 diff 時抓到並還原、單獨重跑確認後才提交——抓到它靠的是人工讀 diff 不是 harness 保證，與本卡在講的「中斷後留下的半完成組合」是同一形狀。。
- 2026-08-12T13:20:01+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5262617332 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=e578f526… 一次相符。本輪四份裁決皆無需 PM 作任何格式調整——區塊零散文、序列已縮排、無 code fence）；core_pain_resolved yes；self_run 5 項；findings 0 項（blocking 0）；attempt WF-CLEANUP-GUARD1-e0-4353c1863f8b83e5532585dbcdcdb25e876098a2。
- 2026-08-12T13:50:21+08:00 amend by wf-cli（op fb2df674）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:docs/WF_CLEANUP_GUARD1.md", "file:cli/src/wf_cli/cleanup.py", "file:cli/src/wf_cli/doctor.py", "file:cli/src/wf_cli/commands/doctor_cmd.py", "file:cli/src/wf_cli/commands/handoff_cmd.py", "file:cli/tests/test_cleanup.py", "file:cli/tests/test_doctor.py", "file:cli/tests/test_release_cleanup.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:docs/WF_CLEANUP_GUARD1.md、file:cli/src/wf_cli/cleanup.py、file:cli/src/wf_cli/doctor.py、file:cli/src/wf_cli/commands/doctor_cmd.py、file:cli/src/wf_cli/commands/handoff_cmd.py、file:cli/tests/test_cleanup.py、file:cli/tests/test_doctor.py」；理由 需求方 2026-08-12 指示先解開阻塞。本卡已 APPROVE 並併入 main（PR #27，5d22a7f），對 cli/tests/test_release_cleanup.py 的工作已結束，宣告的用途（防併發編輯）已消失。而該檔正是 main 轉紅的所在——本卡的分支基線 7451b72 早於 WF-CLI-ROUTING-TIER1 把四個能力旗標改為必填的合併，故其 fixture 未帶那四個旗標，在自己的工作樹 388 passed 為真、併進 main 卻產生 14 個 error。修復卡 DEV-MAIN-RED-CAPABILITY-FLAGS1（#47）被本卡的宣告擋住而無法派工。 **刻意不以走完部署鏈的方式解開**：deploy-state 到 ✅已驗證 需要寫證據，而 main 現在是紅的、紅的正是本卡交付的那個檔——簽「已驗證」會是一句假話。退出單一檔案的宣告是更小且誠實的解法，不需要對部署狀態作任何不實陳述。 本卡的部署狀態維持 ⏸未部署、交付狀態維持 ✅通過，待 main 轉綠後再依需求方裁定處理部署鏈與結案。需求方已表示認同本卡實質上不需部署、合併即足夠，該流程問題另行討論。。
- 2026-08-12T16:55:36+08:00 handoff by wf-cli → owner —（結案）；iteration 3；SHA 4353c1863f8b83e5532585dbcdcdb25e876098a2；證據 跨家族查核（GPT-5@Codex 子代理）於 4353c18 判 APPROVE、core_pain_resolved=yes、findings 0、self_run 5 項；R4-001 與 R4-002 皆判 resolved。收據 issuecomment-5262617332 合規未編輯，PM 回讀重算 report_sha256=e578f526… 一次相符。需求方 T4 sign-off 見 issuecomment-5262731441。

部署鏈已走完至 ✅已驗證（五個 deploy-state 事件皆帶證據）。其中「⏳部署中」如實記錄為**空轉**——wfcli 是使用者自 repo 本機執行的 CLI，無建置／發佈／推送／重啟任何一步，不虛構動作。「✅已部署」的實質定義為交付已在 main 上、使用者自 main 執行即取得該能力，已驗 merge-base --is-ancestor 4353c18 origin/main 成立。

✅已驗證的證據是自 origin/main（02b5d9a）乾淨樹的三項實跑：wfcli handoff --help 列出 --cleanup 且說明正確；cleanup.py 內 execute_closeout_transition 與 _execute_closeout 兩函式定義皆在（即 R4-002 修法的貼標籤層／破壞性本體分離結構已在 main）；被 R4-002 打穿又修好的守衛測試在 main 通過（3 passed）。main 全套同時點 658 passed 0 errors。

⚠️ 誠實邊界（已寫進 ✅已驗證 事件）：本驗證證明的是能力在 main 上存在且守衛測試通過，**不是不可逆刪除路徑已對真實 Project 與 Issue 執行過**——後者從未發生，需求方 sign-off 已明確接受該界線。

⚠️ 本卡未關閉原核心痛點指名的危險主體：reconcile --apply 完全無守衛且該指令尚未存在，已具名承接於 WF-RECONCILE-CLEANUP-GUARD1（#45，T4）。核心痛點已於 op de18defc 依需求方裁定正式更正並逐字寫下這件事。

流程面待議（需求方 2026-08-12 提出）：本卡實質上不需部署、合併即足夠，「需部署卡」的判準對本機執行的 CLI 是否適用另行討論。本次為避免在 main 為紅時簽下不實的「已驗證」，曾先以 amend op fb2df674 將 cli/tests/test_release_cleanup.py 退出本卡宣告以解開 DEV-MAIN-RED-CAPABILITY-FLAGS1（#47）的派工阻塞，而非走部署鏈繞過；該檔的工作當時已結束，宣告用途已消失。。
- 2026-08-26T22:02:50+08:00 amend by wf-cli（op 2c1611a8）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:ab2c7c2f4093ecf227a16205cf658f8696f76fd14814eb5bf5771521ff49d811 (875 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5253356003 · 2026-08-11T12:46:10Z

## 派審：WF-CLEANUP-GUARD1（**T4 紅線**）

審核對象 **`ruan6047/ai-workflow#25`**。⚠️ 不是 `cpbl-analytics#25`。

**T4：本卡管的是會刪掉 worktree、本地分支、遠端分支的自動化路徑。寫錯就是別人沒提交的工作沒了。** 依 canonical §5，T4 須**跨家族或人工審核**，且**最高風險項（實際刪除路徑）由需求方 sign-off**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cleanup-guard1
分支：claude/WF-CLEANUP-GUARD1
被審 SHA：a036ed5088ae44054654e532fe896ad6e14e7663
基線：origin/main 7451b72ba7679893043950d71bad9642665e25da
PR：https://github.com/ruan6047/ai-workflow/pull/27（OPEN，未 merge）
iteration：0
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cleanup-guard1
git rev-parse HEAD && git diff --stat origin/main && cd cli && uv run pytest -q
```

**PM 已複驗**：6 檔 +2016／−2，**全部在資源宣告內**（`op 9c33d1b5` 已擴充）；**347 passed**（基線 292＋55）。PR OPEN 未 merge。

### 承接 #16 的 R7-001（critical）

本卡是收尾轉換的**唯一機械 executor**——`release`（操作者當場發動）與 `reconcile --apply` 白名單第 2 條（批次）共用同一份實作。

**執行者把「不得放寬」做進了型別**，不是靠紀律：

```python
def evaluate_cleanup_guard(target, *, registry, card_body, runner=None, occupancy_prober=None) -> GuardDecision:
    """回傳 proceed／detect_only。**沒有 trigger 參數，也沒有 force 參數。**"""
```

PM 已核對簽章屬實。**「reconcile 側前提不得放寬」在型別層根本寫不出來**——這比在文件裡寫一句強得多。

### 執行者主動揭露的一個突變存活，是本輪最有價值的東西

> **第一輪 20/21 — M19 存活。** 把「效果只在清理**確實完成**後才發動」的條件拿掉，**50 個測試全綠**。缺口在於沒有任何案例覆蓋「守衛放行、但清理實際上沒完成」（遠端回報刪除成功而分支仍在：受保護分支、鏡像同步、最終一致）。補上 `test_effect_is_withheld_when_cleanup_did_not_actually_complete` 後轉 KILLED。第二輪 21/21。

**請複驗這個突變**。它抓到的是「守衛通過 ≠ 動作成功」——而那正好是會產生半完成狀態的路徑。

### 本輪請攻擊這六點

1. **21 個突變體是否涵蓋真正的危險面。** 這是本卡的核心證據。**請自行構造第 22 個**——尤其：把 `assert_work_intact()` 弱化成只驗回傳碼？把 `unobservable` 當成 `pass`（執行者說有覆蓋，請確認）？把三值判定退成二值？

2. **十項前提的窮盡性。** `CHECK_IDS` 涵蓋四類，`classify_state` 五類、32 種組合窮舉。**請找第十一項前提**，或確認 32 組合的參數軸就是真實輸入軸——**「宣稱窮舉卻沒驗證母體」是本 repo 已現多次的形態。**

3. **`--force` 三路驗證是否真的擋死。** 執行者稱 `_forbid_force()` 掛在模組唯一 git 入口、換 runner 也繞不過，另掃整個 argparse 樹並比對實際 argv。**請找繞過路徑**——直接呼叫 `subprocess`？經由 `git_ops.py`（該檔**不在本卡宣告內**）？

4. **兩個解析器的漂移防護。** `git_ops.py` 不在宣告內，故 `locked` 位另在 `cleanup.py` 解析；執行者加了測試比對兩者對同一輸入的 path／branch 一致。**請判斷這個防護是否足夠**，或這本身就是應該擴充宣告而非另寫一份的情形。

5. **完整放行路徑未在真資料上跑過**（執行者明列，見下）。請判斷這對 T4 是否可接受。

6. **界線是否即為卡面所指**：本卡未接線 `wfcli release`／`reconcile --apply`，第 4 步以 `CloseoutEffectWriter` 注入；指令本體屬 #16 §9-E／§9-G，且 `cli.py` 不在宣告內。執行者稱這符合「不得依觸發者切分實作」。**請確認這個界線正確**——它是「共用守衛與 executor 已交付、只差接線」，還是「關鍵的接線缺口被劃到界外」？

### 執行者明列的四項限制

1. **完整放行路徑未在真資料上跑過。** 兩 repo 目前皆無 `📦已合併` 活卡，預覽段輸出零列。真資料只證明了**拒絕路徑**（兩個在途 worktree 正確 `detect_only`，真 `lsof` 掃了 458 個 process）；**放行路徑的證據全來自沙箱 repo**（真 git、真 remote，但非真卡）。已寫入設計文件 §7.1。
2. **未接線 `wfcli release`／`reconcile --apply`**（見攻擊點 6）。
3. **`--registry` 只支援 `tasks-md`／`none`**，已 cutover 到 GitHub Issues 的專案活卡讀不進預覽（`registry.py` 不在宣告內）。
4. **`git_ops.py` 不在宣告內**（見攻擊點 4）。

### 其他揭露

- 本 repo 的 `cli/` **未安裝 ruff**，故無 lint 步驟可跑——這與前幾張卡的環境不同，請勿以「未附 ruff 輸出」計為缺失。
- 執行者為 Claude Opus 5@Claude Code 的子 agent，**查核者須為不同模型家族**。
- **T4 的需求方 sign-off 依定義不由執行者完成**，尚未取得。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。留言紀律：**不得讓任何一行以 `<!--` 緊接事件 marker 前綴起始**。

> **關於收據的一個已知矛盾，請一併裁定**：派審詞的環境紅線寫「不得改 Project 狀態」，而留 receipt marker 需要在 Issue／PR 留言——這兩者在本 repo 已被發現直接衝突（見 [#13](https://github.com/ruan6047/ai-workflow/issues/13) 的停止紀錄）。**留言本身不改 Project 狀態，故留收據不違反紅線**；若你判斷仍衝突，請明說，那是一個尚未有卡承接的設計缺口。**若留收據，請一併載明取材規則。**

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5253712428 · 2026-08-11T13:19:46Z

<!-- wf-review-event:v1 card_id=WF-CLEANUP-GUARD1 source_sha=a036ed5088ae44054654e532fe896ad6e14e7663 attempt_id=WF-CLEANUP-GUARD1-e0-a036ed5088ae44054654e532fe896ad6e14e7663 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CLEANUP-GUARD1`　attempt_id：`WF-CLEANUP-GUARD1-e0-a036ed5088ae44054654e532fe896ad6e14e7663`
- 查核者：跨家族查核（需求方於對話中轉貼原文；無 receipt marker，來源不可驗證）　escalation_epoch：0
- source_sha：`a036ed5088ae44054654e532fe896ad6e14e7663`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-11T21:19:45+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD（與 PR #27 head 比對）`
  - 指定 SHA 與 PR head 一致。
- `git diff --check`
  - 通過，無輸出。
- `cd cli && uv run pytest -q`
  - 347 passed。

### findings（2，其中 blocking 2）

- **WF-CLEANUP-GUARD1-R1-001**　severity=critical　blocking=true　class=implementation　attribution=executor　root_cause_id=`remote-branch-toctou-before-destructive-delete`
  - evidence：cli/src/wf_cli/cleanup.py:788 的守衛通過後，遠端刪除前僅重新確認分支仍存在； 未重新確認該分支 tip 仍是 main 的祖先。 重現序列： 1. 守衛確認遠端 feature 已併入 main。 2. 本機 worktree、local branch 清理完成。 3. 另一個 clone 將新提交 push 到同一遠端 feature。 4. 執行器仍執行 git push origin --delete feature，刪除新提交。
  - disposition：遠端刪除前必須重新讀取 branch SHA、確認 commit object 可觀測，並重新驗證 git merge-base --is-ancestor <tip> <main-tip>；驗證失敗或不可觀測一律 detect_only。 新增「在 after_delete_local_branch 推入新遠端提交」的回歸測試。
- **WF-CLEANUP-GUARD1-R1-002**　severity=critical　blocking=true　class=implementation　attribution=executor　root_cause_id=`closeout-executor-not-wired-to-real-destructive-paths`
  - evidence：execute_closeout_transition() 僅在新模組內定義，現有程式中沒有 release 或 reconcile --apply 的呼叫點。doctor --cleanup-preview 只做偵測，無法取代實際 刪除路徑的守衛。這與卡面「無論由 release 或 reconcile 觸發，均為同一份實作」 的驗收不符。新守衛已能拒絕多數危險情境，但尚未接到真正的 release／ reconcile --apply 路徑，因此尚未保護卡面所指的自動化收尾。
  - disposition：在同一張卡完成兩條觸發路徑的接線，並以整合測試證明兩者確實經由同一 executor。 若依範圍裁定接線留給後卡，則本卡不得宣稱核心痛點已解決。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5253755045 · 2026-08-11T13:23:37Z

## PM 註記：本輪裁決的轉錄邊界

本輪裁決由**需求方於對話中轉貼查核報告原文**，查核者無 `wfcli` 寫入通道，故由 PM 逐字轉錄進唯一寫入通道。以下三件事屬於轉錄的已知限制，先寫明再談內容：

**一、無 receipt marker，來源不可驗證。** 報告未附 `report_sha256` 收據，PM 無法以雜湊證明轉錄內容與查核者實際產出逐位元組相同。可驗證的只有：轉錄後的 `evidence`／`disposition` 是報告散文的逐句搬移，未增刪判斷。

**二、schema 欄位由 PM 指派，非查核者填寫。** 原報告是散文，未提供 `severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id`。這四欄是 PM 依報告文字判定後填入的。**其中 `root_cause_id` 會影響 escalation 三次門檻的計數**——若查核者本人對根因家族的劃分與 PM 不同，門檻的觸發時點就會不同。異議請直接提出，PM 不代查核者堅持。

**三、`blocking` 的分界採用報告自己的用語。** 報告中標為「Blocking」者記 `blocking: true`，標為「非阻擋」者記 `blocking: false`。

被審 SHA 已由 PM 獨立核對：worktree HEAD 與報告所列短 SHA 相符，非陳舊派工。


## Comment 5255485628 · 2026-08-11T15:49:59Z

## PM：五張卡同時送審前的跨卡對帳

本則同時貼在 #21／#22／#23／#24／#25。五張卡本輪都改完並各自通過自己的驗證，但**它們彼此的介面沒有被任何一方檢查過**——每張卡的執行者都只看自己的射程。以下是 PM 在送審前做的交叉檢查，逐項附重現方式。

**這些不是 finding。** PM 不是查核者，以下只是**指定查驗項**：把 PM 觀察到的矛盾指出來，由各卡的查核者判斷它是不是問題、屬誰的問題。PM 刻意不代任何一方修正——#23 §10 明文寫著「刻意不猜測 #24 會怎麼改」，我現在替它填上就是把設計判斷從查核者手上拿走。

### 檢查方法

- **寫入集**：以 #16 §7.2 裁定的**階層路徑包含**語意（正規化路徑相等或其一為另一之祖先目錄），對 Project #4 全部 27 張有資源宣告的活卡做兩兩比對。**不是**現行 `resources.py` `find_conflicts` 的逐字串比對——後者的不足正是 #24 的射程。
- **設計面**：逐一驗證各卡對其他卡寫下的明示假設，以及「同一個物件被兩張卡從不同方向改動」的情形。

---

### 一、寫入集：四組相交，其中一組現在就成立

| 撞的兩張 | 相交處 | 狀態 |
|---|---|---|
| **#22（🚧進行中）× #16（⏸阻塞）** | `templates/review-escalation.md` ⊂ `templates/` | **現在成立** |
| `WF-22-CLI4`（📥Backlog） | `cli/` ⊃ #21 與 #25 的**每一個**檔案 | 潛伏 |
| `WF-CLI-TIER-MUTATION1`（📥Backlog） | `cli/src/wf_cli/` ⊃ #21 與 #25 多數檔案 | 潛伏 |
| `WF-24-EVIDENCE-STRENGTH1`（📥Backlog）× #16 | `templates/dispatch-package.md` ⊂ `templates/` | 潛伏 |

**第一列是 PM 的違反，先說清楚。** 我今天派 #22 時，#16 正持有整個 `templates/`。依 #16 §7.2 自己的裁定，那次 `assign` 應該被擋；沒被擋是因為 `find_conflicts` 現行只做逐字串比對。此條件先前已查證並記錄（`amend` op d32f8a3a），不是新發現——但它現在是**「正在設計互斥語意的那批卡自己違反該語意」的活體樣本**，且是在真實流程中自然發生的，不是構造出來的。

`WF-22-CLI4` 宣告整個 `cli/` 這件事值得單獨看：它一旦被派工，#21 與 #25 就全數動不了；反過來說，#21／#25 在途期間 `WF-22-CLI4` 也不可派。目錄級宣告與檔案級宣告混用的代價，在這裡是可量化的。

**指定查驗項（#24）**：文件的立即階段與目標階段規則，套在上表這四組真實資料上，各自會得到什麼結果？§8.5 釘住的「立即階段獨有的過度拒絕 10 對」是否涵蓋這幾組？

---

### 二、#23 §10 的四項假設，A2 與 A3 現在可以判定，而且都不成立

#23 §10 把對 #24 的依賴寫成四項待驗假設，明文「刻意不對齊，讓差異在查核時暴露」。**兩張卡都交付了，所以現在可以驗——結果是負的。**

**A3 失敗，而且是域不相容，不是覆蓋不足。**

#24 §3.1 規則 1 定義封閉 namespace 為「卡所屬 **repo 根**的相對路徑」，規則 2 拒收以 `/` 起始者、規則 3 拒收以 `~` 起始者、規則 4 拒收任一分量為 `..` 者。

而 #23 §4.4 分類器 `PATH` 集合的七個參數（`--worktree`、`--repo-path`、`--config`、`--input`、`--out-dir`、`--spec-dir`、`repo_root`）是 **CLI 引數**，實務上多半是絕對路徑——本專案的派工詞逐輪都寫 `--repo-path /Users/ruanruan/Dev/ai-workflow`。**這些字串在 #24 的規則 2 下會被逐一拒收。**

兩者的定義域不同：#24 管的是**卡面宣告字串**，#23 要的是**命令列引數**。A3 寫成「是否涵蓋全部七個參數」，隱含了兩者同域的前提，而該前提不成立。

**A2 也不成立。**

#24 §3.1 規則 8 明文「宣告以位元組原樣**儲存**；**比對**時 casefold」，規則 9 為「**比對前**做 NFC」。也就是 `K(r)` 是**比對鍵**，不是儲存形式；且 #24 從不解析 cwd（一律 repo 根相對）、也從不解析 symlink（§5 直接拒收）。它提供的是**集合成員判定**，不是 A2 要求的「同一邏輯路徑在不同 cwd、不同 symlink 解析狀態下產生同一個字串」。

**A1 成立**（#24 對無法解析者確實 fail-closed），但附帶一個具名豁免（`--ignore-unparseable`，33 張母體，sunset 2026-09-30）——該豁免處理的是**別卡宣告解析失敗**，與 A1 所問的**路徑正規化**不同域，請查核者確認 A1 問的是不是它該問的那件事。

**後果**：依 #23 §10 自己的降級規則，路徑型別應落回 §4.2 收尾規則（該動詞退出冪等保護、stderr 明示）——而且是**現在就該落**，不是繼續掛在 §10 當待驗假設。

**指定查驗項（#23）**：§4.1 的路徑型別列是否應直接改寫為降級後的形式？§10 的呈現方式是否應從「假設待驗」改為「已驗、A2／A3 不成立」？
**指定查驗項（#24）**：是否應明文宣告本卡的封閉 namespace **不涵蓋 CLI 引數**，以免其他卡再度誤引？

---

### 三、#25 與 #23 從兩邊改同一個動詞，互不知情

#25 本輪把破壞性收尾接上 `handoff --next-stage release --cleanup`。
#23 §7.1.2 的逐動詞稽核判 **`handoff` 的首寫不合格**（首寫是 owner 欄位，非載荷可攜），並據此判定該動詞的 E1 不成立。

PM 以 `grep` 核對兩份文件：**#25 全文未出現 `#23`、`event_id`、「冪等」；#23 全文未出現 `#25`、`release`、`cleanup`。** 兩張卡在同一個動詞上從相反方向動手，而彼此的文件都沒有對方。

具體後果（PM 逐行追過 `handoff_cmd.py` 的效果順序）：`release --cleanup` 成功路徑為 `owner` → `交付狀態` → `最後交接` → `iteration` → Issue body Log。**清理已完成、owner 已寫、但在 Log 寫入前崩潰**時，事件流上沒有任何能辨識這次寫入的記號——那正是 #23 E1 要解決的東西，而 #23 判定 `handoff` 不具備。

#25 的 resume 是**觀測式**的（重讀當下事實），所以不會重複刪除，這一點是安全的。但狀態面會停在「終態已寫、Log 缺行」的組合，而兩張卡都沒有在處理它。#25 §9 自承的第 2 項（effect writer 回報成功後未回頭重讀狀態面）與此同族但不同一件事。

**指定查驗項（#25）**：接線後 `handoff` 的首寫不自描述，是否使 #25 §9 第 2 項的殘留風險升級？卡面是否應引用 #23 §7.1.2 並標為外部相依？
**指定查驗項（#23）**：§7.1.2 判 `handoff` 不合格時，`handoff` 尚無破壞性效果；#25 落地後該判定的**後果嚴重度**是否改變？§11「在 A′ 落地前這三個動詞的 E1 不成立」是否需要加註破壞性路徑？

---

### 四、#22 的新出口，回溯涵蓋了今天兩個 checkpoint 的觸發成因

#22 本輪在 `review-escalation.md` §4 新增 `defer_cause: instruction-omitted`——「派審指示漏了要求查核者逐項回報前輪 finding 的閉環狀態」。

**今天 #21 與 #22 各自的 escalation checkpoint，觸發成因正是這個。** 兩次都是 PM 的派審詞缺漏（見 `#issuecomment-5253853989`、`#issuecomment-5255216570`，兩則都已載明歸因）。

這構成一個要請查核者特別看的形狀：**本卡的交付物，為本卡自己的 escalation 觸發提供了出口。**

減輕因素有兩個，請一併評估是否足夠：§4 第 2、3 款要求 `deferred_by` 逐字等於卡面「需求：」欄帳號，且不得等於本卡當前 owner 或本 epoch 任一 reviewer——**裁定者必須是需求方**，執行者不能自行 defer。以及「不得連續 defer」未放寬。

但執行者自承的洞 3 指出：**沒有任何檢查會去讀 `defer_ruling_url` 指向的那則指示、確認它真的漏了那一節。** 成因在機械上退化為「從封閉列舉挑一個」。

**指定查驗項（#22）**：`instruction-omitted` 的必要條件是否足以防止它成為通用免責？第 2、3 款排除了 owner 與 reviewer，但**未排除 Coordinator**——而缺漏正是 Coordinator 造成的；`deferred_by` 須為需求方是否已足夠隔離？

---

### 五、#22 卡面驗證條文與交付的落差（需要需求方裁定，非查核者可獨斷）

#22 執行者回報：卡面的兩項驗證條文（deferred 出口使 R4 前不強制、條件 1 在 R8 失效）**在 #16 的忠實事件流上不成立**，原因是 #16 有三處換號重開（R1-002→R2-001、R1-006→R2-002、R4-001→R5-001），依「六格的前提是穩定 `finding_id`」不構成處置。執行者未補造 defer 使其通過，改以「#16 的穩定 id 最小改寫」承擔該兩項，並明確標為構造。

**這是誠實的處置，但它使卡面驗證條文與實際被驗證的對象不再是同一個東西。** 依既有紀律，改動驗收／驗證條文是 PM 走 `amend`、不是執行者；而是否接受這個替代承擔，是需求方的判斷。**PM 刻意不先 `amend`**——先改條文再送審，等於讓卡面去追交付，那是倒過來的。

**指定查驗項（#22）**：「穩定 id 最小改寫」是否為該兩項驗證條文的正當替代？若否，該兩項應判為未滿足（`attribution: planner`，卡面條文本身建立在錯誤前提上）。

---

### PM 已獨立複驗的事項（不構成背書，只是把可機械核對的部分先做掉）

- 五張卡本輪變更的檔案**全部落在各自資源宣告內**；`test_commands_mocked.py`（#21 持有）未被 #25 觸碰。
- 測試：#21 `437 passed`、#25 `367 passed`、#22 replay `44/44`＋`cli` 292 passed（與基線同）；#23／#24 為設計卡，內嵌探針可原樣重跑。
- #21 的 R5-001 攻擊獨立重現：查核者的 `U+02B0`／`U+0378` 兩案例現皆 `ambiguous`，另測 ZWSP／私用區 `U+E000`／emoji／反斜線亦 `ambiguous`，單條對照仍 `matched`。
- #25 的 TOCTOU 守衛獨立突變：把二次確認的 verdict 強制為放行，**8 個測試轉紅**（含該 TOCTOU 回歸與狀態面測試），斷言非空；worktree 已還原乾淨。
- #24 的兩張不可解析卡（`cpbl-analytics#60`／`#66`）body 已由 PM 直接讀取核對：確為 MIG1 佔位區塊（有 fenced JSON、無 sentinel），且 `#66` 的佔位 `db_scope` 為 `write`。
- #22 的 fixture 已對原始留言 `5248665281` 核對：`deferred_findings` 逐字只有兩筆，未被補造。


## Comment 5255866375 · 2026-08-11T16:24:12Z

## PM 實跑報告：`release --cleanup` 在真實狀態面上的端到端觀察

需求方 2026-08-12 裁定 T4 的 sign-off 必須建立在**觀察**而非文件上，並定門檻為**成功路徑 ＋ 至少一條拒絕路徑**。以下是實跑紀錄。

**被審 SHA 未變**（`b1273ab6a8b05adbb6496b774ebfb1935d384d78`）——實跑不改碼，只是把該 SHA 的行為在真實 GitHub 上執行一次。

### 載體

拋棄式卡 `OPS-CLEANUP-SMOKE1`（[#28](https://github.com/ruan6047/ai-workflow/issues/28)，T0，無任何交付價值），走完整流程：`wfcli open` → 手建 worktree 與分支 → `wfcli assign` → trivial commit `485163f` → [PR #29](https://github.com/ruan6047/ai-workflow/pull/29) → merge（`0d4d282`）。全程以本卡 worktree 的碼執行（`uv run --project .claude/worktrees/wf-cleanup-guard1/cli`），**不是** main 的版本。

### 拒絕路徑：worktree 內有未提交變更

在 worktree 放一個從未提交的檔案 `UNCOMMITTED_CANARY.txt`，執行 `handoff --next-stage release --cleanup`。

第一次跑同時命中兩個阻擋（本地 main 未更新故 `merge_verified_local` 也響）。為了證明是**未提交變更**擋的、不是別的原因順便擋住，我更新本地 main 後重跑，阻擋收斂為單一項：

```
- 阻擋：[no_uncommitted_changes] 有 1 筆未提交變更／未追蹤檔：?? UNCOMMITTED_CANARY.txt
[handoff] 拒絕 release：收尾未完成（mode=detect_only），狀態面未寫入；請處理上列阻擋原因後重跑
[handoff] 收尾轉換：mode=detect_only／狀態=cleanup_in_progress（合法=True）
exit 5
```

**拒絕後逐項核對（兩次拒絕之後）：**

| 觀察對象 | 結果 |
|---|---|
| `UNCOMMITTED_CANARY.txt` | 完好，內容逐字未變 |
| 本地分支 `claude/OPS-CLEANUP-SMOKE1` | 仍在 |
| 遠端分支 | 仍在 |
| Issue #28 | 仍 `OPEN` |
| 交付狀態 | 仍 `🚧進行中`（未變） |
| owner | 仍 `Claude Opus 5@Claude Code (PM)`（未變） |
| iteration | 仍 `0`（未變） |
| Issue body Log | **只有 `open` 與 `assign` 兩行**——兩次被拒的 release 一行都沒追加 |

最後一列是關鍵：`write_status_face` 是個 closure，只在清理確實完成後才被 executor 呼叫，所以「狀態面未寫入」不是只有 Project 欄位沒動，**連 Log 都沒有**。這與卡面「第 4 步是本轉換的效果本身，不得列為前置」的設計一致，且是在真實 GitHub 上觀察到的，不是 mock。

### 成功路徑

移除 canary 後重跑：

```
[handoff] 收尾轉換：mode=applied／狀態=completed（合法=True）
  - 已執行：remove_worktree, delete_local_branch, delete_remote_branch
[handoff] 已交接 OPS-CLEANUP-SMOKE1 → 已收尾（狀態=🏁完成）
exit 0
```

**逐項核對：**

| 觀察對象 | 結果 |
|---|---|
| worktree 目錄 | `No such file or directory` |
| `git worktree list` 註冊 | 已無該筆 |
| 本地分支 | 已刪 |
| 遠端分支（`git ls-remote`） | 已刪 |
| Issue #28 | `CLOSED`（`2026-08-11T16:22:28Z`） |
| 交付狀態 | `🏁完成` |
| 已合併內容在 main | **仍在**（`git show origin/main:tasks/_smoke/OPS-CLEANUP-SMOKE1.md` 讀得到） |
| Log 末行 | 帶「收尾清理已完成（worktree 與本地／遠端分支皆已不存在）」註記 |

最後兩列一起看才有意義：**被刪掉的是分支與工作目錄，不是工作成果**——已合併的內容留在 main，這正是「清理」與「毀掉工作」的分界。

### 這次實跑順帶證實的一件別卡的事

`wfcli assign` 在派工時印出：

```
[assign] 警告：以下活卡沒有可解析的資源宣告，交集檢查略過它們（不擋派工）：INIT-GAME-RECAP、ML-FIELD-OF1
```

這是 [#24](https://github.com/ruan6047/ai-workflow/issues/24) R1-001 所述 fail-open 的**現場實況**，不是文件推論。已於同日的跨卡對帳留言記錄；此處補上它在真實派工流程中確實會發生的證據。

### 沒有被這次實跑覆蓋的

誠實劃界，以下**不在**本次觀察範圍，sign-off 不應被讀成涵蓋它們：

1. **遠端 TOCTOU 競態**（R1-001）——需要在守衛通過與 `push --delete` 之間精準插入他人的 push，真實環境無法可靠製造。證據仍只有測試內以 `step_hook` 觸發的真 git 雙 clone 回歸（PM 已獨立突變複驗：強制放行後 8 個測試轉紅）。
2. **中途中斷後的續作**——需求方裁定不納入本次門檻。
3. **其他四種拒絕情境**（stash、active lease、worktree 為當前 cwd、分支未合併）——本次只實跑了未提交變更這一種；其餘仍只有測試證據。
4. **執行者自承的殘留洞**（doc §9 七項）一項都未被本次實跑觸及，尤其第 2 項「effect writer 回報成功後未回頭重讀狀態面」。

### 給查核者

上述觀察是 PM 做的，**不構成對本卡的裁決，也不代替 T4 的 sign-off**（sign-off 是需求方的動作）。它只是把「這條路徑從未在真實狀態面上跑過」這個事實消除掉，讓你們的判斷有實際行為可對照。若你認為某一項觀察方法不足以支持其結論，那本身是可以提的 finding。


## Comment 5255923722 · 2026-08-11T16:29:35Z

## 派審：#25 `WF-CLEANUP-GUARD1` R2（T4）

⚠️ 審核對象是 **`ruan6047/ai-workflow#25`**，**不是 `cpbl-analytics#25`**。工作目標 repo 是 `ai-workflow`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cleanup-guard1
分支：claude/WF-CLEANUP-GUARD1（PR #27）
被審 SHA：b1273ab6a8b05adbb6496b774ebfb1935d384d78
基線：origin/main 0d4d282
iteration：1
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cleanup-guard1
git rev-parse HEAD && git status --short && git diff --check
git diff a036ed5..b1273ab                      # 本輪全部變更（5 檔）
cd cli && uv run pytest -q
```

**這是 T4 卡，操作不可逆且會刪除工作內容。** 標準比其他卡嚴。

### 一、複驗 R1-001（遠端刪除前的 TOCTOU）

修法是新增 `recheck_remote_branch()`，在 `push --delete` 前一刻以同一次 `ls-remote` 重讀 branch 與 main 當下 SHA、`cat-file -e` 確認 tip 可觀測、重驗 `merge-base --is-ancestor`，缺一即拒。拒絕收在新的 `mode="aborted"`（不併進 `detect_only`）。

請攻擊：**三項檢查是否真的窮盡了「tip 換人」的所有形態**？例如 force-push 使 tip 倒退到仍是祖先的某個 commit——那時三項全過，但遠端分支上有人刻意做過事。以及 `aborted` 與 `detect_only` 分家後，**所有既有消費點是否都認得新的 mode**，還是有地方只判 `!= "applied"` 而把兩者混為一談。

### 二、複驗 R1-002（唯一 executor 未接線）——需求方已裁定射程

需求方裁定**只接 `release`，不做 `reconcile`**。依據：`reconcile` 子命令目前完全不存在於 `cli.py`，且 `reconcile --apply` 白名單第 2 條在 #16 §5.2 標為 reserved pending #25，本卡若必須先建出它，兩張卡互相等待。

處置是把 `handoff --next-stage release --cleanup` 接上 `execute_closeout_transition`，`--cleanup` 為**選配、預設不清理**。

請判斷三件事：

1. **「預設不清理」是解法還是迴避。** 不帶旗標的 release 會造出 `illegal_terminal_before_cleanup` 並印警示——**那是不是等於本卡預設不保護任何東西**？既有使用者的預期是 release 只改狀態，而預設維持該預期的代價是守衛預設不生效。
2. **卡面對「核心痛點僅部分解決」的宣告是否誠實**（doc 開頭警語＋§4.1 表格＋§8＋測試檔 docstring 四處）。reconcile 側完全無守衛這件事，有沒有被寫得夠明白，還是被「已接線」的語氣蓋過去了。
3. **刻意不提供 `--main-ref`／`--remote`** 的理由（那是能讓祖先檢查名存實亡的旋鈕）是否成立，還是只是把可設定性藏起來。

### 三、PM 已在真實狀態面實跑過，請覆核方法而非只讀結論

需求方 2026-08-12 裁定 T4 的 sign-off 須建立在觀察上，門檻為**成功路徑 ＋ 至少一條拒絕路徑**。PM 以拋棄式卡 [#28](https://github.com/ruan6047/ai-workflow/issues/28) 實跑，紀錄見本 Issue 的實跑報告留言。

**請覆核那份報告的方法，不是接受它的結論**：拒絕路徑只測了「未提交變更」一種（另四種仍只有測試證據）；成功路徑證明了 worktree／本地／遠端分支真的消失且已合併內容留在 main。**報告末段自己列了四項未被覆蓋的範圍——請判斷那份劃界是否誠實、有沒有漏列。**

### 四、跨卡矛盾（PM 指定查驗項，非 finding）

本卡把破壞性收尾接上 `handoff`，而 [#23](https://github.com/ruan6047/ai-workflow/issues/23) §7.1.2 判 **`handoff` 的首寫不合格**（首寫是 owner 欄位，非載荷可攜），據此判該動詞 E1 不成立。PM 以 grep 核對：**本卡全文未出現 `#23`、`event_id`、「冪等」；#23 全文未出現 `#25`、`release`、`cleanup`。**

具體後果：`release --cleanup` 成功路徑的效果順序是 `owner` → `交付狀態` → `最後交接` → `iteration` → Log。**清理已完成、owner 已寫、Log 寫入前崩潰**時，事件流上沒有任何辨識這次寫入的記號。本卡的 resume 是觀測式的所以不會重複刪除，但狀態面會停在「終態已寫、Log 缺行」的組合。

請判斷：這是否使本卡 §9 第 2 項的殘留風險升級？卡面是否應引用 #23 §7.1.2 並標為外部相依？

### 五、執行者主動揭露

- **本卡的執行者是 Claude Opus 5@Claude Code 的子 agent，PM 亦為 Claude Opus 5。** 你必須是**不同模型家族**——同家族不同工具不算獨立（canonical §5）。
- 突變測試 32/32 KILLED；首輪 4 個存活體全部補測轉紅，其中 **M30 是「原測試綠得是因為錯誤的理由」**（拔掉分支後 exit code 碰巧也是 5，改斷言「executor 根本沒被啟動」才殺得掉）。**請抽驗這類「綠得有理由嗎」的測試還有沒有別的。**
- 執行者自承七個未關的洞（doc §9），含 effect writer 回報成功後未回頭重讀狀態面、第 4 步的 Issue 結案留言未實作（只關閉、留痕走 body Log）。**請判斷這七項的劃界是否完整。**
- `cli/tests/test_commands_mocked.py` 由 #21 持有，本卡未觸碰（可 `git diff --stat` 核對）。

### 環境紅線

唯讀查核；**不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行任何有副作用的 `wfcli` 命令**。破壞性驗證一律在 disposable 的臨時 repo／worktree 內做，不得對本專案任何真實分支或 worktree 執行刪除。

**留言紀律（重要，本輪起強制）**：你的留言中**不得出現事件 marker 的字面前綴**（即 `wf-review-event` 後面直接接半形冒號），連散文引用與 code fence 示範都不行——`doctor` 以全文子字串比對，命中即隔離整張卡的查核通道（#21 已因此被鎖）。需要指涉時拆開書寫。發文前 `grep` 一次。

### 輸出

依 `templates/review-prompt.md` §5 的結構化區塊，`core_pain_resolved` 與 `self_run` 必填。**本輪起額外強制兩項**：

1. **逐項回報前輪 finding 的閉環狀態**——R1-001、R1-002 各自明列 `resolved`／`withdrawn`／仍開啟，缺此節即 `review-invalid`。
2. **`severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id` 五欄請你自己填**，不要留給 PM 事後指派——上一輪是散文形式，五欄由 PM 代填，而 `root_cause_id` 直接影響 escalation 門檻的計數。


## Comment 5256094441 · 2026-08-11T16:44:04Z

wf-review-receipt:v1
card_id: WF-CLEANUP-GUARD1
source_sha: b1273ab6a8b05adbb6496b774ebfb1935d384d78
review_result: REQUEST_CHANGES
report_sha256: e3992d14af7ab65ff65dc26212242e4e5e5ddb7fb37c161352317d0d51be442f
取材規則：本收據只取自查核者在指定 worktree 對指定 source_sha 實際執行的唯讀命令與 /tmp 拋棄式 Git 儲存庫破壞性測試；report_sha256 為下列完整原始查核報告（UTF-8 位元組、含末尾換行）的 SHA-256。未修改 Project 狀態或 source branch。


## Comment 5256102817 · 2026-08-11T16:44:51Z

wf-review-receipt:v1
card_id: WF-CLEANUP-GUARD1
source_sha: b1273ab6a8b05adbb6496b774ebfb1935d384d78
review_result: REQUEST_CHANGES
report_sha256: 7d838351340cea5d9252c3a181f7550b1cf3f9aed6ed7b13772e4c3cda5df373
取材規則：本收據只取自查核者在指定 worktree 對指定 source_sha 實際執行的唯讀命令與 /tmp 拋棄式 Git 儲存庫破壞性測試；report_sha256 為完整原始查核報告（UTF-8 位元組、含末尾換行）的 SHA-256。未修改 Project 狀態或 source branch。此收據取代前一則收據的報告引用。


## Comment 5256117481 · 2026-08-11T16:46:12Z

<!-- wf-review-receipt:v1
card_id: WF-CLEANUP-GUARD1
source_sha: b1273ab6a8b05adbb6496b774ebfb1935d384d78
review_result: REQUEST_CHANGES
report_sha256: 7d838351340cea5d9252c3a181f7550b1cf3f9aed6ed7b13772e4c3cda5df373
supersedes: issuecomment-5256102817
取材規則：本收據只取自查核者在指定 worktree 對指定 source_sha 實際執行的唯讀命令與 /tmp 拋棄式 Git 儲存庫破壞性測試；report_sha256 為完整原始查核報告（UTF-8 位元組、含末尾換行）的 SHA-256。未修改 Project 狀態或 source branch。
-->


## Comment 5256206054 · 2026-08-11T16:54:41Z

## PM 更正：五份派審詞的基線 SHA 全部寫錯

本則同時貼在 #21／#22／#23／#24／#25。

### 事實

五份派審詞都寫「基線：`origin/main` `0d4d282`」。**`0d4d282` 不是任何一張卡的祖先。**

```
wf-cleanup-guard1                  0d4d282=非祖先  merge-base=7451b72
wf-cli-routing-tier1               0d4d282=非祖先  merge-base=7451b72
wf-escalation-deferred-findings1   0d4d282=非祖先  merge-base=7451b72
wf-event-idempotency1              0d4d282=非祖先  merge-base=7451b72
wf-resource-writeset1              0d4d282=非祖先  merge-base=7451b72
```

**正確的共同基線是 `7451b72ba7679893043950d71bad9642665e25da`。**

`0d4d282` 是 `Merge pull request #29 from ruan6047/claude/OPS-CLEANUP-SMOKE1`——**我自己在派審前一小時跑 #25 端到端實跑時產生的 merge**。五張卡都在那之前分支，所以它們當然不是它的後代。我在寫派審詞時直接抄了當下的 `origin/main`，沒有回頭確認它與被審分支的祖先關係。

### 後果

**這使 [#23](https://github.com/ruan6047/ai-workflow/issues/23) 的查核者判定 `review-invalid` 而未進實質查核。** 那個判定依派審詞的字面是正確的——`git merge-base --is-ancestor 0d4d282 1ee62b0` 確實 exit 1。**責任在 Coordinator，不在查核者，也不在執行者。**

另外三位查核者（#21／#22／#24）都各自察覺並自行處理了：#21 明白寫出「實際共同祖先為 7451b72；`0d4d282` 是後續 main」並用 `merge-tree` 確認無衝突；#22 判定「派審指定基線仍為被審 SHA 的祖先，故不構成 review-invalid」——**該句的前半在事實上不成立，但其結論（可以繼續查核）是對的**；#24 在 `git diff --name-status 0d4d282..cb6028fc` 中看到 `tasks/_smoke/OPS-CLEANUP-SMOKE1.md` 被刪除，正確判斷那是基線差異造成的假象而非本輪變更。

**四位查核者裡三位靠自己繞過了我寫壞的指示，一位照著指示停下來。停下來的那位沒有做錯任何事。**

### 處置

- **#23 重新派審**，基線更正為 `7451b72`，被審 SHA 不變（`1ee62b0`）。該卡的 `review-invalid` **不計 iteration、不寫 review event、不改交付狀態**（`review-escalation.md` §1）。
- #21／#22／#24／#25 的查核**不因此失效**——四位都已對正確的變更範圍實跑，基線錯誤只影響 `git diff` 的顯示範圍，未影響被審 SHA 與其變更內容。
- 此後派審詞的基線一律以 `git merge-base <origin/main> <source_sha>` 產出，不得直接抄當下的 `origin/main`。

### 這件事的形狀

派審詞裡的「基線」欄本來就是給查核者用來界定 diff 範圍的座標。**我把一個更新的 main 當成基線，而那個 main 之所以更新，正是因為我自己剛在上面 merge 了東西。** 這與本批卡片反覆處理的問題同源：一個需要對照既有事實才能填的欄位，用當下手邊最方便的值填掉。


## Comment 5256211042 · 2026-08-11T16:55:09Z

<!-- wf-review-event:v1 card_id=WF-CLEANUP-GUARD1 source_sha=b1273ab6a8b05adbb6496b774ebfb1935d384d78 attempt_id=WF-CLEANUP-GUARD1-e0-b1273ab6a8b05adbb6496b774ebfb1935d384d78 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CLEANUP-GUARD1`　attempt_id：`WF-CLEANUP-GUARD1-e0-b1273ab6a8b05adbb6496b774ebfb1935d384d78`
- 查核者：GPT-5@Codex 子代理（留有 receipt marker；PM 未能重算 report_sha256——報告經對話轉貼，位元組不可還原）　escalation_epoch：0
- source_sha：`b1273ab6a8b05adbb6496b774ebfb1935d384d78`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T00:55:08+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git status --short && git rev-parse origin/main`
  - HEAD=b1273ab6a8b05adbb6496b774ebfb1935d384d78；origin/main=0d4d282ef3bb5eae6e78316a368029ced7ff98db；工作區乾淨。
- `git diff --check && git diff --name-only a036ed5088ae44054654e532fe896ad6e14e7663..HEAD`
  - 無 whitespace 錯誤；本輪僅 5 個宣告內檔案。
- `cd cli && uv run pytest -q`
  - 367 passed in 27.70s。
- `disposable /tmp Git repo 實測，以自訂 Git runner 在 recheck_remote_branch() 回傳 delete 後、git push --delete 前由第二個 clone 推入新 commit`
  - injected_between_recheck_and_delete=True；mode=applied；actions=(remove_worktree, delete_local_branch, delete_remote_branch)；remote_exists_after_delete=False。新提交被刪除。
- `grep marker preflight（以組合字串建構禁用 marker）`
  - forbidden-marker-absent。

### findings（1，其中 blocking 1）

- **WF-CLEANUP-GUARD1-R2-001**　severity=critical　blocking=true　class=implementation　attribution=executor　root_cause_id=`remote-branch-toctou-before-destructive-delete`
  - evidence：recheck_remote_branch() 在 cleanup.py:635-679 讀取與驗證遠端 tip， 但 cleanup.py:921-930 在其回傳 delete 後才另送 git push origin --delete <branch>； 兩者沒有 compare-and-swap [比較並交換] 或 server-side lease。隔離實測在兩者之間 push 一筆新提交，executor 仍回 applied 並刪除遠端分支。現有回歸測試 test_cleanup.py:814-824 僅在 after_delete_local_branch 注入，恰好早於二次確認， 未覆蓋此最後時間窗。
  - disposition：遠端刪除必須改為由遠端原子驗證預期舊 tip 的條件式刪除；若現有 Git/遠端契約 無法安全提供該原子操作，則不得自動刪遠端分支，應 fail-closed [失敗即封閉] 交人工處理。新增在二次確認完成、送出刪除前推入新 commit 的真 Git 回歸測試， 並驗證遠端新內容仍可重新 clone 讀取。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5256475572 · 2026-08-11T17:18:27Z

## escalation-checkpoint（第三個可計數 attempt 前）

### 第二條件成立

R1 的 accepted blocking 為 R1-001（`remote-branch-toctou-before-destructive-delete`）與 R1-002。R2 查核者逐項回報閉環：**R1-002 判 `resolved`，R1-001 判「仍開啟」。**

依 `review-escalation.md` §4 末段，觸發條件是「前一 attempt 的 accepted blocking finding **未在下一 attempt 明列 `resolved`／`withdrawn`**」。**明列「仍開啟」清償了複驗義務，但它不是 `resolved` 也不是 `withdrawn`，因此仍落在觸發格。** `checkpoint_decision` 只能是 `escalate`。

第一條件（同根因跨三個唯一可計數 attempt）：R2-001 沿用同一個 `root_cause_id`，故該家族已跨 R1／R2 兩個 attempt，**2／3，尚未成立**。再一次即成立。

### 這一輪與前兩次的觸發不同，值得記下

本卡今日稍早在 #21 與 #22 上的兩次 checkpoint，觸發成因都是 Coordinator 的派審詞缺漏（未要求逐項回報閉環）。**本次不是。** R2 查核者完整回報了閉環，正是因為他照做了，R1-001 的「仍開啟」才被明白寫下來並觸發條件。

**這是機制在正常運作，不是誤觸。** 執行者修了一輪、把時間窗縮小了，但沒有關掉；查核者用隔離實測直接重現資料遺失。門檻在這裡響是對的。

### R2 的 finding 是被實測重現的，不是論證

查核者在 `/tmp` 建拋棄式 repo，以自訂 git runner **在 `recheck_remote_branch()` 回傳 `delete` 之後、`git push --delete` 送出之前**推入新提交：`mode=applied`、遠端分支被刪、新提交消失。

PM 已獨立讀碼確認該窗存在：`cleanup.py` 的 recheck 是**讀**，其後的 `push --delete` **無條件**，兩者之間沒有 compare-and-swap。且現有回歸測試的 `step_hook` 打在 `after_delete_local_branch`——那是遠端刪除**動作開始之前**，所以注入的提交在 recheck 執行時已存在、recheck 正確拒絕。**那條測試驗的是 recheck 本身，不是 recheck 到 delete 之間的窗。**

PM 先前在 handoff 證據中寫「PM 獨立突變複驗：強制放行後 8 個測試轉紅」——**該突變在設計上不可能抓到這個窗**（它移除的是 recheck，而非行使 recheck 之後的時間差）。PM 當時的說法比實際驗到的範圍大，一併記入。

### 裁定

```yaml
checkpoint_decision: escalate
escalation_resolution: continue
checkpoint_rationale: |
  第二條件成立（R1-001 被明列為「仍開啟」，非 resolved 亦非 withdrawn），
  故 checkpoint_decision 只能是 escalate。需求方裁定 continue，維持同執行者角色
  （Claude Opus 5@Claude Code 子 agent），不換人、不切卡，並指定修法方向：
  先試條件式刪除，不直接退讓成「不自動刪遠端分支」。
  裁定依據為需求方 2026-08-12 的原話：「開三個agent派修正，#25 先試條件式刪除」。
decided_by: ruan6047（需求方）
counts_toward_escalation: true
attempts_so_far: 2
```

### 需求方指定的修法方向，附 PM 實測前提

查核者的 disposition 給了兩條路：條件式刪除，或無法安全提供該原子操作時退讓為不自動刪遠端分支、fail-closed 交人工。**需求方裁定先試前者。**

PM 已在拋棄式 repo 實測，確認 git 提供該原子操作：

```
git push origin --force-with-lease=refs/heads/feature:<過期SHA> :refs/heads/feature
  → ! [rejected]  (delete) -> feature (stale info)；遠端分支存活

git push origin --force-with-lease=refs/heads/feature:<當下SHA> :refs/heads/feature
  → - [deleted]   feature
```

**該實測用的是本機 bare repo，不是 GitHub。** 真實遠端是否行為一致必須另行驗證，不得以此推定。


## Comment 5259553352 · 2026-08-11T22:24:50Z

## 派審：#25 `WF-CLEANUP-GUARD1` R3（T4）

⚠️ 審核對象是 **`ruan6047/ai-workflow#25`**，**不是 `cpbl-analytics#25`**。工作目標 repo 是 `ai-workflow`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cleanup-guard1
分支：claude/WF-CLEANUP-GUARD1（PR #27）
被審 SHA：bc099f658642ce53d1dd7e7106a291df6b4adc5d
基線：7451b72ba7679893043950d71bad9642665e25da（= git merge-base origin/main bc099f6，已驗證為祖先）
iteration：2
```

> **基線這次是用 `git merge-base` 算出來的。** 上一輪五份派審詞都把基線寫成當下的 `origin/main`（`0d4d282`），而那是 PM 自己跑實跑時產生的 merge、不是任何一張卡的祖先，害 #23 的查核者依指示判 `review-invalid` 而停手。詳見本 Issue 的「PM 更正」留言。**若你發現本則的基線仍不成立，那也是 Coordinator 的問題，請直接指出。**

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cleanup-guard1
git rev-parse HEAD && git status --short && git diff --check
git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD && echo "基線成立"
git diff b1273ab..bc099f6                       # 本輪變更（4 檔）
cd cli && uv run pytest -q
```

**這是 T4 卡。上一輪你們的同僚用隔離實測真的刪掉了一筆新提交。**

### 一、複驗 R2-001（critical）——需求方裁定走條件式刪除

複驗改回傳 `RemoteDeleteDecision(verdict, check, expected_tip)`，讀到的 tip **原樣**成為租約期望值，經**唯一**刪除入口 `conditional_delete_args()` 組成：

```
git push --force-with-lease=refs/heads/<branch>:<tip> origin --delete <branch>
```

沒有期望 tip 就組不出指令（丟 `CleanupGuardError`，**不退回無條件刪除**）。`_forbid_force` 只開一個形狀固定的窄口：裸 lease、短名 refspec、全零期望值、非 SHA 期望值一律仍擋——**那四種都會讓租約靜默失效**。

請攻擊：

1. **那四種失效形狀是否窮盡。** 還有沒有別的寫法能讓 `--force-with-lease` 看起來在保護、實際不保護？（例如 `+refs/...` 強制前綴、`--force-if-includes` 的交互、多個 refspec 同時送出、環境變數影響）
2. **`_forbid_force` 的窄口本身。** 它現在必須放行一個含 `force` 字樣的旗標——這個例外是以正則判形狀。**正則能被繞過嗎？** 本專案已經有一張卡（#21）連五輪栽在「以字串形狀判語意」上。
3. **殘餘窗的誠實度。** advertisement 到套用之間的毫秒級窗客戶端無法涵蓋，執行者列為殘餘。那個窗有多大、在什麼情況下會被打中，文件說清楚了嗎？

### 二、真實 GitHub 的驗證只做了一半，請判斷那一半夠不夠

執行者誠實劃界，兩半請分開評：

**拒絕路徑已實證**：對 `github.com:ruan6047/ai-workflow.git`（SSH）以 `--dry-run` 送租約過期的刪除 → `! [rejected] (delete) … (stale info)`、returncode **1**，且 `GIT_TRACE_PACKET` 顯示**客戶端只送出一個 flush、一條更新指令都沒送**。這證明租約檢查完全在客戶端對 GitHub 剛送出的 ref advertisement 完成。

**接受路徑未實證**：需在真實遠端建拋棄式探針分支，該次 `git push` 被執行環境權限層擋下，**執行者未繞道**（並明說後來自己分支的 push 是不同指令形狀、他沒回頭重試被拒的那一個）。替代證據在本機 bare repo 含線路追蹤。

**明確未證明的兩件**：GitHub 的 receive-pack 是否對 delete 做 old-oid CAS；GitHub 的 advertisement 是否恆為最新。執行者主張失敗方向安全（誤拒＝`aborted` 雜訊，非資料遺失）故未改走 fail-closed。

**請判斷這個推論**：「客戶端拒絕已實證 ＋ 失敗方向安全」是否足以支撐「條件式刪除保護了那個窗」？如果 GitHub 的 advertisement 可能不是最新的，客戶端拿到過期的 tip 當租約、而遠端 CAS 又不存在，**那租約會不會反而製造一種「看起來有保護」的假象**？

### 三、方法上的三件事，請一併查

1. **注入點的移動有直接證據。** 新測試改用 runner 攔截，卡在「複驗已回傳可刪」與「git 真的被執行」之間。突變 **M34（拿掉租約）對舊測試 SURVIVED、對新測試 KILLED**。PM 已獨立重現：舊 TOCTOU 測試 2 passed 存活，全套 4 紅。**請確認新測試的四條反假綠設計真的都有作用**（斷言注入發生、先斷言遠端工作還在再斷言記帳、斷言複驗那筆是 `pass`、逐字比對送出的租約等於複驗讀到的 tip）。
2. **M41 第一次的「殺掉」是假的。** 拿掉 `worktree remove` 的失敗檢查後照樣丟 `CleanupGuardError`，只是晚一步炸在 `branch -d`。**這是本卡第二次抓到同型假綠**（上輪是 M30）。請抽驗還有沒有第三個。
3. **新增反向突變體 M36（連合法租約也擋）。** 只驗「該擋的擋住」的話，寫成全擋也會全綠——而那會讓遠端刪除永遠發不出去。請確認這類反向覆蓋沒有別的缺口。

### 四、執行者主動把一個自承缺口的嚴重度調高，請評估他調得對不對

doc §9 第 2 項（effect writer 回報成功 ≠ 狀態面真的變了）被調高，並明說**不應再被描述為「與 §3.3 同類、已被同一招接住」**——理由是 R2-001 的教訓不是「複驗漏一項」而是「**讀一次不構成保證**」，該洞是同形狀在狀態面的翻版，而 GitHub 側沒有 `--force-with-lease` 這種現成工具，要等價保證得自己做「讀→帶條件寫→重讀驗證」。

請判斷這個類比是否成立，以及調高後的描述是否已經足夠。

### 五、T4 未結事項

- **最高風險項（實際刪除路徑）須需求方 sign-off**，不由查核者或 PM 代行。
- PM 曾在真實狀態面實跑過拋棄式卡的成功與拒絕路徑（見本 Issue 的實跑報告留言），**但那是 `b1273ab` 的碼，本輪的條件式刪除未再實跑一次**。請判斷是否需要再跑一次才足以 sign-off。
- **reconcile 側仍完全無守衛**（指令尚不存在），核心痛點仍只關了一半。

### 六、執行者主動揭露

- **執行者是 Claude Opus 5@Claude Code 的子 agent，PM 亦為 Claude Opus 5。** 你必須是**不同模型家族**。
- pytest **379 passed**（基線 `b1273ab` 實測 367）。突變 11/11 KILLED。只動宣告內 4 檔，`test_commands_mocked.py` 未觸碰（#21 持有）。
- 執行者自承六個未關的洞（doc §9），含條件式刪除只覆蓋遠端分支、`--cleanup` 非預設、`no_stash` 只認 git 預設訊息格式、第 4 步結案留言未實作。
- 執行者順帶回報他自己踩到 `${PIPESTATUS[0]}` 在 zsh 拿到空值（zsh 是 `pipestatus`），改用 `ls-remote` 直讀遠端確認。**PM 在同一輪也踩過同型的管線遮蔽 exit code。**

### 環境紅線

唯讀查核；**不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行任何有副作用的 `wfcli` 命令**。**破壞性驗證一律在 disposable 的臨時 repo／worktree 內做**，不得對本專案任何真實分支或 worktree 執行刪除。

**留言紀律**：你的留言中**不得出現事件 marker 的字面前綴**（即 `wf-review-event` 後面直接接半形冒號），連散文引用與 code fence 示範都不行——`doctor` 以全文子字串比對，命中即隔離整張卡的查核通道。需要指涉時拆開書寫。發文前 `grep` 一次。

### 輸出

依 `templates/review-prompt.md` §5 的結構化區塊，`core_pain_resolved` 與 `self_run` 必填。**額外強制三項**：

1. **逐項回報前輪 finding 的閉環狀態**——R2-001 明列 `resolved`／`withdrawn`／仍開啟，缺此節即 `review-invalid`。
2. **`severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id` 五欄請你自己填**。若你判定 R2-001 仍開啟，請沿用 `remote-branch-toctou-before-destructive-delete` 這個根因家族——它已跨 R1／R2 兩個 attempt，**再一次即滿足三次門檻**。
3. **留一則收據**（`wf-review-receipt:v1`，多行格式，`card_id:` 與 `source_sha:` 各自獨立成行），並把被雜湊的報告全文放進同一則留言、在留言內寫死取材規則。上一輪只有兩張留了合格收據；沒有收據的裁決在身分維度上等同無佐證，而這張是 T4。


## Comment 5259779018 · 2026-08-11T22:52:40Z

## PM 補跑報告：R3 的條件式刪除在真實 GitHub 上的觀察

需求方 2026-08-12 裁定補跑。先前那次真實狀態面實跑（`issuecomment-5255866375`）用的是 **R2 的碼（`b1273ab`）**，本輪的租約路徑從未對真實 GitHub 走完一次。本則補上。

**被審 SHA 未變**（`bc099f658642ce53d1dd7e7106a291df6b4adc5d`）。全程以本卡 worktree 的碼執行。

### 一、接受路徑：已在真實 GitHub 上完成，且線路可證

拋棄式卡 `OPS-CLEANUP-SMOKE2`（[#33](https://github.com/ruan6047/ai-workflow/issues/33)）走完 `open` → `assign` → commit `701747e` → [PR #34](https://github.com/ruan6047/ai-workflow/pull/34) → merge → `handoff --next-stage release --cleanup`。

```
[handoff] 收尾轉換：mode=applied／狀態=completed（合法=True）
  - 已執行：remove_worktree, delete_local_branch, delete_remote_branch
exit 0
```

**以 `GIT_TRACE_PACKET` 捕捉到送往 GitHub 的更新指令：**

```
push> 701747e19761f6d543aa51ff90883f7d2ed2271a 0000000000000000000000000000000000000000 refs/heads/claude/OPS-CLEANUP-SMOKE2
```

old-oid **正是複驗讀到的那個 tip**，不是全零。這補上了執行者列為「未實證」的接受路徑：租約確實帶著非零 old-oid 送到真實 GitHub 並被接受。

逐項核對：worktree 目錄不存在、`git worktree list` 無該筆、本地分支已刪、遠端分支已刪、Issue `CLOSED`、交付狀態 `🏁完成`、**已合併內容仍在 main**（`git show origin/main:tasks/_smoke/OPS-CLEANUP-SMOKE2.md` 讀得到）。

### 二、額外做的一個實驗：租約到底跟誰比對

執行者把「GitHub 的 advertisement 是否恆為最新」列為殘餘風險，並說「此風險所有 `--force-with-lease` 使用者共有」。我想知道那個窗實際上有多大，所以做了一個直接的探針。

**設計**：建拋棄式分支 `probe/lease-cas` → 另一個 clone 推入新提交 → 回到本機 checkout **刻意不 fetch**，使其 remote-tracking ref 仍停在舊 tip → 以**與該過期追蹤 ref 一致**的期望值送出租約刪除。

若 `--force-with-lease` 比對的是本地 remote-tracking ref，兩者一致，客戶端就會放行，更新指令會送出，然後成敗取決於 GitHub 是否做 CAS。

**實際結果**：

```
! [rejected]  (delete) -> probe/lease-cas (stale info)
```

而且 `GIT_TRACE_PACKET` 裡 **grep 不到任何針對該 ref 的 `push>` 更新指令**——一條都沒送出。

**結論**：帶明確期望值時，`--force-with-lease` 比對的是**遠端在本次連線中剛廣告的 tip**，不是本地那個可能過期的 remote-tracking ref。這比執行者論證的更強——他的本機 bare repo 證據無法區分這兩種比對對象，而這一點正是「租約會不會製造假象」的關鍵。

### 三、仍未證明的，以及為什麼證不到

**GitHub 的 receive-pack 是否對 delete 強制 old-oid CAS，仍未證明。** 我原本的探針就是要測這件事，但客戶端先擋下了，更新指令根本沒到伺服器。要繞過客戶端檢查得自己組 pkt-line 送 receive-pack，porcelain git 做不到。

**但這個未知的重要性下降了**：既然客戶端比對的是本次連線剛拿到的廣告值，殘餘窗只剩「GitHub 廣告該 ref 之後、同一次 push 套用刪除之前」的那一小段。執行者對這個窗的描述是準確的。

**另外未涵蓋**：本次只跑成功路徑。租約拒絕路徑（複驗與 push 之間有人推入）在真實環境無法可靠製造——那需要在 CLI 內部注入，屬測試層。執行者已以 `--dry-run` 對真實 GitHub 證過拒絕會發生（`stale info` ＋ returncode 1 ＋ 只送一個 flush），PM 上述第二節的探針也是同一形狀的第二個實例。

### 四、順帶：一次真實卡片的手動收尾

同一時段 [#21](https://github.com/ruan6047/ai-workflow/issues/21) 通過查核並結案。**我刻意沒用本卡的 `--cleanup` 處理它**——本卡仍在查核中，不以未經查核的 T4 破壞性程式碼處理真實卡片；改手動執行 `worktree-lifecycle.md` 第 11 行的既有清單。遠端刪除我用了條件式刪除（帶當下 tip 的 `--force-with-lease`），因為那本身是安全側的，與是否採用本卡無關。

這個對照有一點參考價值：**手動走完七步是可行的，只是每一項前提都得自己記得檢查**——而那正是本卡要機械化的東西。

### 五、這份補跑證明什麼、不證明什麼

**證明**：R3 的租約路徑在真實 GitHub 上走得完，old-oid 確實上線路，且客戶端的比對對象是新鮮的廣告值而非過期的本地追蹤 ref。

**不證明**：GitHub 伺服器端是否做 CAS；租約拒絕路徑在 CLI 實際執行中的行為（只有測試層與 `--dry-run` 證據）；`reconcile` 側（指令仍不存在）。

**仍不構成 sign-off。** 這是 PM 做的觀察，不是裁決，也不代替需求方對最高風險項的 sign-off。若查核者認為某項觀察方法不足以支持其結論，那本身是可以提的 finding。


## Comment 5259852016 · 2026-08-11T23:01:52Z

<!-- wf-review-receipt:v1
card_id: WF-CLEANUP-GUARD1
source_sha: bc099f658642ce53d1dd7e7106a291df6b4adc5d
review_result: REQUEST_CHANGES
report_sha256: 2d8f6618e1c91ea72a7b36eb9a11166865ff88cd6ea39bd23f3896cad1a6fa72
report_encoding: UTF-8
report_line_endings: LF
report_strip: false
report_start: 緊接下方 report-begin HTML 註解後的第一個字元
report_end: report-end HTML 註解前的 LF 字元
report_exclusions: receipt 區塊與兩個 HTML 邊界註解均不納入雜湊
-->
<!-- report-begin -->
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git rev-parse HEAD && git status --short && git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD"
    observed: "HEAD=bc099f658642ce53d1dd7e7106a291df6b4adc5d；工作區乾淨；指定基線為祖先。"
  - command: "git diff --check 7451b72ba7679893043950d71bad9642665e25da..HEAD"
    observed: "通過，無 whitespace 錯誤。"
  - command: "cd cli && uv run pytest -q tests/test_cleanup.py tests/test_release_cleanup.py"
    observed: "82 passed；破壞性案例僅在 pytest tmp_path 的拋棄式 Git 儲存庫與 bare remote 執行。"
  - command: "cd cli && uv run pytest -q"
    observed: "379 passed；完整回歸無失敗。"
  - command: "rg -n conditional_delete_args,recheck_remote_branch,--cleanup,reconcile cli/src/wf_cli/cleanup.py cli/src/wf_cli/commands/handoff_cmd.py docs/WF_CLEANUP_GUARD1.md"
    observed: "遠端刪除唯一現行呼叫以帶明確 tip 的 --force-with-lease 組成；release 已接線；reconcile 子命令仍不存在。"
findings:
  - finding_id: "WF-CLEANUP-GUARD1-R3-001"
    severity: critical
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: "closeout-executor-not-wired-to-real-destructive-paths"
    evidence: "Issue #25 驗收明定 release 與 reconcile --apply 白名單第 2 條均須由同一 executor 觸發；docs/WF_CLEANUP_GUARD1.md §4.1 與 R3 派審均明載 reconcile 子命令不存在且尚未受保護。現有 handoff --next-stage release --cleanup 是唯一接線，故批次 cleanup 路徑尚無機械守衛。"
    disposition: "在本卡接上 reconcile --apply 的白名單第 2 條並以整合測試證明它與 release 進入同一個 execute_closeout_transition；若需求方要永久縮小卡面，須先由唯一狀態寫入通道正式更正驗收與核心痛點，之後再重新派審。"

<!-- report-end -->

## 前輪 accepted blocking findings 閉環

- R1-001／R2-001 remote-branch-toctou-before-destructive-delete：resolved。R3 的 RemoteDeleteDecision.expected_tip 經唯一 conditional_delete_args() 進入具明確 SHA 的租約；隔離測試覆蓋複驗後、推送前的變動，並驗證新提交可重新 clone 讀取。
- R1-002 closeout-executor-not-wired-to-real-destructive-paths：仍開啟。release 接線已完成，但 reconcile --apply 的白名單第 2 條沒有現行指令或整合呼叫，與卡面「兩條觸發路徑」驗收不符。

## 獨立範圍外發現

無。

核心痛點尚未消失：release 的遠端刪除 TOCTOU [time-of-check to time-of-use] 已關閉，但 reconcile 的破壞性自動化路徑仍沒有接到同一守衛。故本次裁決為 REQUEST_CHANGES。

## Comment 5259911663 · 2026-08-11T23:10:16Z

<!-- wf-review-event:v1 card_id=WF-CLEANUP-GUARD1 source_sha=bc099f658642ce53d1dd7e7106a291df6b4adc5d attempt_id=WF-CLEANUP-GUARD1-e0-bc099f658642ce53d1dd7e7106a291df6b4adc5d -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CLEANUP-GUARD1`　attempt_id：`WF-CLEANUP-GUARD1-e0-bc099f658642ce53d1dd7e7106a291df6b4adc5d`
- 查核者：GPT-5@Codex 子代理（收據 issuecomment-5259852016，多行格式合規；PM 回讀重算 report_sha256=2d8f6618… 相符，但試到第三個邊界變體才對上——其 report_end 未指明起始 LF 是否納入。⚠️ 被雜湊區段只涵蓋本 YAML，前輪閉環回報與核心痛點陳述在 report-end 之後、不受雜湊保護）　escalation_epoch：0
- source_sha：`bc099f658642ce53d1dd7e7106a291df6b4adc5d`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T07:10:14+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git status --short && git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD`
  - HEAD=bc099f658642ce53d1dd7e7106a291df6b4adc5d；工作區乾淨；指定基線為祖先。
- `git diff --check 7451b72ba7679893043950d71bad9642665e25da..HEAD`
  - 通過，無 whitespace 錯誤。
- `cd cli && uv run pytest -q tests/test_cleanup.py tests/test_release_cleanup.py`
  - 82 passed；破壞性案例僅在 pytest tmp_path 的拋棄式 Git 儲存庫與 bare remote 執行。
- `cd cli && uv run pytest -q`
  - 379 passed；完整回歸無失敗。
- `rg -n conditional_delete_args,recheck_remote_branch,--cleanup,reconcile cli/src/wf_cli/cleanup.py cli/src/wf_cli/commands/handoff_cmd.py docs/WF_CLEANUP_GUARD1.md`
  - 遠端刪除唯一現行呼叫以帶明確 tip 的 --force-with-lease 組成；release 已接線；reconcile 子命令仍不存在。

### findings（1，其中 blocking 1）

- **WF-CLEANUP-GUARD1-R3-001**　severity=critical　blocking=true　class=implementation　attribution=executor　root_cause_id=`closeout-executor-not-wired-to-real-destructive-paths`
  - evidence：Issue #25 驗收明定 release 與 reconcile --apply 白名單第 2 條均須由同一 executor 觸發；docs/WF_CLEANUP_GUARD1.md §4.1 與 R3 派審均明載 reconcile 子命令不存在且尚未受保護。現有 handoff --next-stage release --cleanup 是唯一接線，故批次 cleanup 路徑尚無機械守衛。
  - disposition：在本卡接上 reconcile --apply 的白名單第 2 條並以整合測試證明它與 release 進入同一個 execute_closeout_transition；若需求方要永久縮小卡面，須先由唯一狀態寫入通道正式更正驗收與核心痛點，之後再重新派審。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5259927082 · 2026-08-11T23:12:22Z

## PM 轉錄紀錄：本輪四份裁決的收據驗證與格式轉換

四張全數 `REQUEST_CHANGES`，全部已寫入狀態面。以下逐項說明證據強度與我動過什麼。

### 收據驗證結果

| 卡 | 收據 | 雜湊重算 | 涵蓋範圍 |
|---|---|---|---|
| #22 | 多行格式，合規 | **一次算對** | report-begin／end 之間全文 |
| #24 | 多行格式，合規 | **一次算對** | YAML 圍籬內全文 |
| #25 | 多行格式，合規 | 試到**第三個邊界變體**才對上 | **僅 YAML**；前輪閉環與核心痛點陳述在雜湊外 |
| #23 | **無** | 不適用 | — |

**#25 的邊界規則不夠死。** 它寫 `report_end: report-end HTML 註解前的 LF 字元`，但沒說 `report-begin` 之後那個 LF 算不算起點。我試了三種：原樣（含前後換行）、去頭 LF 留尾、去頭 LF 且尾僅留一個 LF——第三種才相符。#22 與 #24 的規則各自指名了 trim 行為與末行 LF，都一次對上。**差別不在誰細心，在規則有沒有把兩端都釘住。**

**#25 的雜湊只保護 YAML。** 前輪 finding 閉環回報（本輪兩項強制之一）與核心痛點陳述都在 `report-end` 之後，不受雜湊保護——有人改動那兩段不會破壞雜湊。轉錄進狀態面的是 YAML，那部分有保護。

### #23 沒有收據，但我仍轉錄了

理由是我先前寫在 #22 上的那條不對稱：**保守方向的裁決容忍證據不足，開閘的裁決不容忍。** `REQUEST_CHANGES` 是把卡退回，不開任何閘門；`APPROVE` 才是。#21 上一輪的 `APPROVE` 我拒絕轉錄直到補件，這輪 #23 的 `REQUEST_CHANGES` 我照寫並把限制記在 `--reviewer` 欄。

**但我沒有照查核者的要求代發收據。** 該報告末尾寫「交付給 PM 時，請將上述完整報告原文放進 #23 同一則留言……再附多行 receipt marker」。**這件事 PM 做等於沒做**：收據的全部價值在於留言的 GitHub author 是平台可驗證的身分；由 PM 代發，證明的只是 PM 發過一則留言，對查核者的身分一無所證。`handoff-contract.md` §3.1.2 明寫「收據內模型／工具名稱只屬自述，不能取代平台身分驗證」——代發把整條規則變成空轉。

（附帶說明：本輪 #22／#24／#25 的收據留言 author 也都是 `ruan6047`，即需求方轉貼。所以嚴格說，那三則平台可驗證的是「該文字確由需求方發布」，不是「由 Codex 產出」。這是跨家族查核者無寫入權造成的結構性缺口，不是本輪的新問題。）

### 我動過的格式（兩處，均為解析器限制）

**#24**：`scope_outside_findings` 原為頂層鍵＋巢狀 mapping（`  status: "none"`），解析器只接受 `- key: value` 序列，改為 `- status: "none"`。字串內容未變。

**其餘三份未動。** 特別是 #22 這次直接用了 `|` 而非 `>`，#23 也沒有裸字串序列——上一輪的兩個坑都沒再踩。

### #23 與 #24 的分歧已如實保留

兩張對同一介面給出不同判斷，PM **未調和**：

- **#23** 判 `#24 的封閉 namespace 不能作為 CLI 路徑正規化來源`，列為 **blocking**（`external-path-normalization-domain-mismatch`），要求 #23 自己改寫 §4.1／§10 或定義獨立的 CLI 路徑規範化。
- **#24** 判兩者本來就是不同輸入域，應在文件明示不涵蓋 CLI 引數，**不構成其本輪 blocking finding**。

兩者不衝突——它們是同一件事的兩側：#24 認為責任在使用方，#23 認為自己得改。**兩張卡各自的處置方向其實一致**（#23 要改 §4.1／§10、#24 已加界線澄清），差別只在誰記為 blocking。這正是刻意不對齊要暴露的東西，結果它暴露出來了而且兩側收斂到同一個修法。


## Comment 5259964693 · 2026-08-11T23:17:46Z

## PM：R3-001 的歸因更正，以及一個寫入通道的缺口

### 一、R3-001 的 `attribution` 應為 `coordinator`，不是 `executor`

查核者判 `attribution: executor`，依卡面而言那個判定完全正確——卡面驗收逐字要求「無論由 release 或 reconcile --apply 觸發，都是同一份實作；**不得依觸發者切分實作範圍**」，而交付只接了 release。

**但執行者是照著我的指示做的。** 需求方於 2026-08-11 裁定「只接 release」，我把它寫進了 escalation checkpoint 留言、寫進了 handoff 證據、也要求執行者寫進交付文件——**唯獨沒有 `amend` 進卡面的規範欄位**。執行者交付了裁定要求的東西，卡面要求的卻是另一件；差距是我造成的。

已於 `amend` op `3cd13f81` 正式把射程縮小寫進驗收條件，並在理由中記錄此歸因更正。**下一輪查核不必再複驗 R3-001 的實作面**——它的處置是修卡面，卡面已修。

這與本批卡片反覆處理的病灶同源：**裁定留在散文裡，沒有落進規範欄位。** 我一直在對別人指出這件事。

### 二、本次修訂同時加入兩項先前未明文的條件

**單一 executor 形狀須保留**：`release` 路徑必須經由 `execute_closeout_transition`，且該函式**不得因只接一條路徑而內含 release 專屬邏輯**——後續接 reconcile 時只應新增呼叫點，不得需要複製或分叉實作。這是縮小射程的**代價上限**：允許少接一條路徑，不允許把實作切成兩份。

**`core_pain_resolved` 的判準**：以本卡宣告射程（release 路徑）為界，不以 reconcile 未接線為由判 `no`；**但若文件對該限制的揭露不足或語氣淡化，仍應判 `no`**。後半句是刻意的——縮小射程不該變成淡化未解決部分的許可。

### 三、寫入通道的缺口：核心痛點改不了

查核者的 disposition 寫「須先由唯一狀態寫入通道正式更正**驗收與核心痛點**」。

**`wfcli amend` 沒有 `--core-pain` 旗標**（可改的只有 `--spec-baseline`／`--acceptance`／`--verification`／`--db-scope`／`--resources`／`--tier`）。所以那個要求只做得到一半。

我**沒有**手改 Issue body 的核心痛點段落——那會繞過唯一寫入通道，而唯一寫入通道正是這批卡片在建立的東西。現況是：核心痛點仍描述 reconcile 與 release 兩條路徑，該落差由新驗收條文第 6 項的判準吸收。

**那是繞過，不是修好。** 一個 `core_pain_resolved` 具否決權的欄位，其判準卻只能由另一個欄位間接改寫，這本身是契約缺陷。此缺口另記，候選歸 [#9](https://github.com/ruan6047/ai-workflow/issues/9)（該卡已宣告 `review.py`／`validation.py`／`review_cmd.py`＋新 writer，加一個 `--core-pain` 屬同一寫入面）。

### 四、下一輪的路由

本卡**不派執行者**。交付 `bc099f6` 的文件已經明載「reconcile 側尚未受保護、核心痛點僅部分解決」——那與縮小後的卡面一致，不需要改。所以本卡直接重新派審，被審 SHA 不變。

若下一輪查核者認為交付文件對 reconcile 限制的揭露仍不足（新驗收條文第 6 項的後半句），那才是執行者的事。


## Comment 5260244802 · 2026-08-11T23:54:58Z

## PM 自審與跨卡對帳（第二輪四張交付後）

需求方要求送外審前先自審一次、再檢查跨改動的衝突／矛盾／重工，不過關就繼續修。本則是結果。**四張的交付本身我逐項驗過，都成立；跨卡層面找到六項，其中兩項是我自己的問題。**

### 一、逐卡自審：宣稱與實據對照

我對每張只複驗**承重宣稱**——如果那一條不成立，整個修法就垮。

| 卡 | 承重宣稱 | PM 獨立複驗 |
|---|---|---|
| **#25** `b29d2c7` | M48（「複驗沒帶回 tip」保險絲在 release 被略過）對既有測試 SURVIVED、對新 AST 測試 KILLED | **重現**：排除新增兩條後 `379 passed` 存活；新增的 `test_executor_body_never_branches_on_the_trigger` FAILED。`cleanup.py` 的 diff 逐行核為 docstring，零邏輯改動。382 passed |
| **#24** `f2f5181` | `ast.parse(feature_version=(3,11))` 漏掉 R2-001 那個 case，故第 2 條路不可行 | **重現**：`feature_version=(3,11)` **接受**該段，真實 3.9.6 拋 `SyntaxError`。PEP 695 變異在新閘門 `[FAIL] 確屬下限違例`、在舊閘門 `違例 0 筆／PASS`。`FLOOR=(3,6)` 觸發 fail-closed |
| **#22** `8d27bed` | 三個反例全被打掉、正例仍 `deferred`；`(c′)` 預設可用因 doctor 已能讀 body 與 author | **重現**：65/65；三反例分別掉 `narrow_scope_bound`／`narrow_ruling_author_is_requester`／`narrow_scope_bound`，正例 `deferred`。`doctor.py:385,396` 確實已讀 `body` 與 `user` |
| **#23** `d824d16` | 三條事實支撐「第三條路」；並更正 #16 §4.3 | **重現**：`--config` 在 `config.py:69` 共用函式故在全動詞上；`assign --worktree` 為 `required=True`；`set_field_value(級別)` 在 `:392`、`set_item_body` 在 `:423`，故 `amend --tier` 的遠端首寫確為級別欄——**#16 §4.3 記反了** |

另核實 #23 的一條硬約束：`doctor.py` 的 `_CONFORMANT_MARKER_RE` 把「順序固定、單一空白、鍵集合封閉」編進同一條 regex，多一鍵即不匹配；且**全 repo 只有 `review.py:458` 會發出 marker**。

**#24 的兩個我先前標記的自審項也結了**：閘門選擇是 `sorted(found, reverse=True)`——取最接近 FLOOR 的版本（優先精確），非隨意；活卡張數在 §1.1 與 §9.7 都明寫為快照並附漂移史。後者我是抽驗不是窮舉。

---

### 二、跨卡對帳：六項

#### X1（矛盾）#24 把 CLI 路徑正規化指派給 #23，而 #23 已明文拒絕承接

- #24 §3.1 界線告示與 §12 第 7 項：「**引數的正規化歸 [#23]**」
- #23 §4.1b／§10：「本卡**不定義**、也**不引用**任何 CLI 路徑正規化器」「相依已解除」

兩張都是本輪剛交付。**#24 的指標指向一張已經拒收的卡**——未來若有人需要 CLI 路徑正規化，照 #24 的指示走過去，會被告知不存在。

處置建議：#24 改為「本卡不涵蓋；#23 已裁定其六個承接動詞不需要，故**目前無人擁有**——需要者須自行論證並開卡」。

#### X2（矛盾／重工）探針可攜性出現兩套標準，且 #23 的做法過不了 #24 的閘門

- **#24**：建強制閘門——找版本 ≤ FLOOR 的真實直譯器實際編譯，找不到即 fail-closed；並機械證明 `feature_version` 不能當閘門。
- **#23**：釘 `uv run python`（3.12.13）＋改 tuple 形式，只報實測範圍（3.9.6／3.12.13／3.14.3）。

**同一個 repo 的兩份設計文件，對同一類問題各自解一次，結論不同。** 若 #24 的判準成立（宣稱下限就要以下限驗證），#23 的探針沒有任何東西在守它的可攜性——它只是碰巧在三個版本上都跑得動。

這也是本次唯一符合「重工」的一項：#24 做出的自檢是**可泛用**的，#23 沒有沿用。

#### X3（結構性阻塞）三張卡的結構化欄位相依，全部撞上同一個封閉鍵集合

| 卡 | 需要的欄位 | 落在哪 |
|---|---|---|
| #22（上輪） | `review_prompt_url`、`closure_reporting_requested` | 派審事件 |
| #22（本輪 b′-1） | 被收窄的 `attempt_id`、`finding_id` | 裁定事件 |
| #23 | `event_id` 的載荷格式與回讀契約 | lifecycle 事件 |

三者都宣告依賴、都不在各自寫入集、都標為 fail-closed 待補。**但真正的阻塞比「無人擁有」更硬**：`_CONFORMANT_MARKER_RE` 的鍵集合封閉，多一鍵即整張卡停機；而六個動詞裡**只有 `review` 有 marker**。

所以這三項相依**不是各自缺一個欄位，是共同缺一次 marker 版本升級（v2）＋五個動詞的 marker 從無到有**。目前沒有任何卡承接這件事。

#### X4（路由）#23 更正了 #16 §4.3，而 #16 ⏸阻塞

#23 逐條核對後指出 #16 §4.3 把 `amend` 的寫入順序記為「body Log → 級別欄」並據此判合格，**與碼相反**。PM 已核實為真。#16 現為 ⏸阻塞（等 #23／#24 落地），該更正需在解除阻塞時一併吸收，否則 #16 帶著一個已知錯誤的逐動詞稽核。

#### X5（未閉合）#25 與 #23 對 `handoff` 的雙向認知，兩輪後仍未建立

上一輪 PM 已列為指定查驗項：#25 把破壞性收尾接上 `handoff`，而 #23 §7.1.2 判 `handoff` 首寫不合格。#25 的查核者把它記為**範圍外發現**並說「應由 PM 交 #23 的所有者裁定與承接」。

**本輪兩張各自又改了一輪，仍然互不引用。** `grep` 核對：#25 全文無 `#23`／`event_id`／「冪等」；#23 全文無 `#25`／`release`／`cleanup`。

#### X6（我的問題）殭屍卡 #12 佔著整個 `cli/src/wf_cli/`，且我把一個缺口路由錯了

[#12](https://github.com/ruan6047/ai-workflow/issues/12) `WF-CLI-TIER-MUTATION1`（📥Backlog）宣告 `file:cli/src/wf_cli/`，在階層包含語意下與 #25、[#30](https://github.com/ruan6047/ai-workflow/issues/30)、[#9](https://github.com/ruan6047/ai-workflow/issues/9) 全面相交。

而 [#19](https://github.com/ruan6047/ai-workflow/issues/19)（🏁完成）的驗收第 4 條逐字寫著：「與 #12（tier 更正）的範圍界定明確：**擇一實作，或明示 #12 併入本卡後關閉**」。#19 交付的 `amend` 已含 `--tier`、寫級別欄、留原值→新值＋理由、並有半寫入自癒。**#12 的驗收第 1、2 條已實質滿足，而那個裁定從未被記錄。**

**兩件事是我的：**

1. 先前需求方裁定「兩張過寬的目錄級宣告都收到實際子樹」，我收了 #16 與 #9，**漏了 #12**——而它是三張裡擋最多的一張。已於 `amend` op `89c002ee` 補收。
2. 我在處理 #25 時撞到「`wfcli amend` 沒有 `--core-pain`」，記為「**候選歸 #9**」。**那是錯的**——#12 的驗收第 3 條逐字要求「評估同類缺口是否還有：除 tier 外，其他開卡時設定的欄位是否也無更正路徑」，核心痛點正落在那裡。已在 #12 的 amend 理由中更正。

實測殘餘：`amend` 現涵蓋 spec-baseline／acceptance／verification／db-scope／resources／tier；**Initiative、鏈深、核心痛點、服務的原始目標仍無更正路徑**。

---

### 三、自審結論

**四張的交付可以送外審**——承重宣稱都經獨立複驗成立，寫入集無越界，測試無退化。

**但 X1／X2／X5 是本輪四張彼此之間的問題，不送修就等於把已知矛盾交給查核者。** 三者都小：X1 是 #24 改一句指標、X2 是 #23 說明為何不沿用 #24 的閘門（或沿用）、X5 是 #25 與 #23 互相引用一次。

**X3 需要開卡**（marker v2 ＋ 五個動詞的 marker），**X4 需要在 #16 解除阻塞時吸收**，**X6 的殘餘射程須需求方裁定 #12 是做還是關**。這三項不是本輪四張能解的。


## Comment 5260748754 · 2026-08-12T00:46:11Z

## PM 自審收斂紀錄：三輪之後

需求方要求送外審前自審、跨卡對帳、有問題就修再審，直到沒問題。**本則記錄收斂結果與仍存在的殘留。**

### 收斂過程

| 輪次 | 做了什麼 | 結果 |
|---|---|---|
| 第一輪 | 四張交付的承重宣稱逐項獨立複驗 | 全部成立 |
| 第二輪 | 跨卡對帳，找出六項 | X1／X2／X5 派修；X3 開卡；X4 記路由；X6 兩項是 PM 自己的問題 |
| 第三輪 | X2 的修正過程中，#23 把 #24 的自檢指向自己的檔案，**發現該自檢的三個缺陷** | #24 再修一輪，另挖出第四、第五個 |
| 第四輪 | #23 補上區塊數登記，使自己滿足所宣告沿用的標準 | 收斂 |

**第三輪不是計畫中的。** 它之所以發生，是因為 X2 的處置方式是「沿用而非各自實作」——而沿用的第一個動作就是把別人的機制指向自己的檔案跑一次。**那一跑立刻暴露了「一般性機制只在自己的樣本上驗證過」。**

### X1／X2／X5 逐項驗證

**X1（#24 把 CLI 路徑正規化指派給已拒收的 #23）—— 已解。** §3.1 告示與 §12 第 7 項改為「本卡不涵蓋 → #23 已裁定其六個承接動詞不需要 → 目前無人擁有 → 需要者須自行舉證並開卡」，並把 #23 的判準（分類鍵＝對事件內容的貢獻）與不可行性論證寫進告示，使誤引者拿得到判準而不只是「沒人管」。殘留的兩處字面命中經核對均為**撤回敘述本身**，非殘留。

**X2（兩套探針可攜性標準）—— 已解，且解法比對齊更好。** #23 選擇沿用而非自立第二套，並在沿用時做了兩件未被要求的事：把 #24 的自檢**原樣未改一字**指向自己的檔案實跑（因而發現缺陷）、**指名而不代修**。#24 據此修了五個缺陷，其中第五個（`sys.argv` 未隔離）**在 R4 從未浮現，只因為它被第二個缺陷擋在執行之外——一個缺陷遮住另一個**。

**X5（#25 與 #23 對 `handoff` 的雙向認知）—— 已解。** 先前 `grep` 兩邊各為 0；現在 #25 的文件提及 #23／`event_id`／冪等 3 處，#23 提及 #25／收尾 5 處。兩側依 PM 提供的**同一份事實**各寫一半，未各自推論。#25 另把它與 §9 第 2 項的分野寫成**雙向可發現**（兩節互相指路），並接出同源線：讀一次不構成保證 → 寫一次不構成生效確認 → 寫一次不構成可辨識。

### 機械核對

- 四張工作區**全部乾淨**，本地與遠端**同 SHA**（無 force 分歧）。
- 四張本輪變更**全部落在各自資源宣告內**。
- ai-workflow 卡之間的寫入集相交由 **17 組降為 4 組**（收窄 #16／#9／#12 三張過寬宣告的結果）。**剩下 4 組全部是現役卡與 Backlog 卡之間的排隊約束，不是缺陷**：#30 等 #25 釋放 `doctor.py`／`doctor_cmd.py`／`test_doctor.py`，#9 與 #30 在 `cli.py` 上互等。
- 自檢跨檔一般性：#24 的自檢對 #23 的文件 `[裁決] PASS`、違例 0、**四支探針全部實際執行**；對自己的文件仍 PASS。

### 仍存在的殘留（不擋送審，但查核者應知悉）

1. **#24 引用 #23 的 SHA 是 `d824d16`，而 #23 現為 `50021ce`。** 被引用的內容（§4.1b／§10 的拒收裁定）在兩個 commit 上一致，故無實質錯誤；把裁定釘在它被作出的那個 commit 也是可辯護的做法。但文中稱其為「其交付版」，而交付版現已前移——**這是輕微的陳舊引用**。
2. **#23 §4.4.1 的「實跑 B」含行號，貼死在文件裡。** 執行者自己標明：本檔一旦再編輯行號就漂移，屆時需一併重跑更新。這與它剛修掉的「實跑 A 陳舊」是同一形狀——**差別在現在它是已知的脆弱而非沉默的**。
3. **#24 自陳兩條尚未修的一般性假設**（§13）：工作目錄假設、行程狀態不隔離。兩者的真正處置都是「每支探針各起沙箱子行程」，需 repo 內腳本，逸出本卡寫入集。
4. **X3 已開卡 [#35](https://github.com/ruan6047/ai-workflow/issues/35) 但設有開工閘門**：三項具名相依全部寫於本輪且未經查核，相依未定稿前不得 `assign`。
5. **X4（#23 對 #16 §4.3 的更正）待 #16 解除阻塞時吸收。** #16 現為 ⏸阻塞（等 #23／#24 落地）。
6. **X6 的 #12 已重新界定射程**，殘餘為「開卡時設定但無更正路徑的欄位」，核心痛點優先。

### 一件方法上的觀察

本輪三個新缺陷（#24 自檢的五個、#23 的登記缺失）**沒有一個是查核者發現的**，全部來自「把 A 卡的機制指向 B 卡的檔案跑一次」這個動作。

跨卡對帳先前做的是**讀兩份文件找矛盾**；這次多做了一步——**讓一張卡的產物實際作用在另一張卡的產物上**。前者找到的是敘述不一致，後者找到的是機制不成立。兩者不能互相取代。


## Comment 5260778461 · 2026-08-12T00:50:50Z

## escalation-checkpoint（第四個可計數 attempt 前）

依 `review-escalation.md:61`「第三個及其後**每個**可計數 attempt 出現時先建立 `escalation-checkpoint`」。本卡已累積三個（`a036ed5`／`b1273ab`／`bc099f6`），下一輪 `bbce273` 為第四個。

### 兩條件皆不成立

**第一條件（同根因跨三個唯一可計數 attempt）：最高 2／3。**

| 根因家族 | 出現於 | 計數 |
|---|---|---:|
| `remote-branch-toctou-before-destructive-delete` | R1-001、R2-001 | 2 |
| `closeout-executor-not-wired-to-real-destructive-paths` | R1-002、R3-001 | 2 |

**第二條件（前一 attempt 的 accepted blocking 未在下一 attempt 明列 `resolved`／`withdrawn`）：不成立。** R2 的 accepted blocking 為 R2-001，R3 查核者明列其為 `resolved`（並附隔離實測與租約線路證據）。

```yaml
checkpoint_decision: continue
checkpoint_rationale: |
  兩條件皆不成立，故 decision 為 continue，非 escalate。
  本則為 review-escalation.md:61 的例行 checkpoint（第三個之後每一個可計數
  attempt 皆須建立），不是因為門檻被觸發。
decided_by: 機械推導（兩條件皆不成立時 decision 不需裁定）
counts_toward_escalation: true
attempts_so_far: 3
```

### 兩個家族各差一次就滿足門檻，請查核者知悉

R4 若再出現這兩個 `root_cause_id` 中的任一個，即滿足第一條件、下一輪強制 `escalate`。

- `closeout-executor-not-wired-to-real-destructive-paths`：R3-001 的處置是**修卡面**（`amend` op `3cd13f81` 正式縮小射程為 release-only），PM 已將其 `attribution` 更正為 `coordinator`。若 R4 查核者認為卡面修訂不足以閉合它，請**沿用同一家族名**，不要另起新名。
- `remote-branch-toctou-before-destructive-delete`：R3 判 resolved，PM 另於真實 GitHub 補跑並取得線路證據。

### 一併記錄的合規缺口

本卡第三個 attempt 前的 checkpoint 已建（`issuecomment-5256475572`），**沒有漏建**。但 PM 先前是「察覺門檻條件才建」而非依 `:61` 的例行要求建——同批的 [#22](https://github.com/ruan6047/ai-workflow/issues/22)（第四個前）與 [#24](https://github.com/ruan6047/ai-workflow/issues/24)（第三個前）確有漏建，已於各自卡上記錄。**漏建不追溯補寫**：事後補一則自稱當時作出的裁定，正是本專案明令禁止的形態。


## Comment 5260862782 · 2026-08-12T01:04:19Z

## 派審：#25 `WF-CLEANUP-GUARD1` R4（T4）

⚠️ 審核對象 **`ruan6047/ai-workflow#25`**，不是 `cpbl-analytics#25`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cleanup-guard1
分支：claude/WF-CLEANUP-GUARD1（PR #27）
被審 SHA：bbce273877ac8d8df9409c9a5c7830fd2f4eb415
基線：7451b72ba7679893043950d71bad9642665e25da（= git merge-base origin/main bbce273，已驗為祖先）
iteration：3
```

> **`origin/main` 現為 `3d4d9a0`，不是基線。** 抄它會得到錯誤的 diff 範圍——PM 上一批派審詞就是這樣寫錯，害一位查核者判 `review-invalid` 而停手。

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cleanup-guard1
git rev-parse HEAD && git status --short
git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD && echo 基線成立
git diff bc099f6..bbce273        # 本輪兩段：b29d2c7 卡面對齊、bbce273 跨卡 X5
cd cli && uv run pytest -q       # 基線 382
```

### 本輪的性質：R3-001 的處置是修卡面，不是修實作

R3 你們判的 critical（`closeout-executor-not-wired-to-real-destructive-paths`）是對的——卡面驗收當時逐字要求 release 與 reconcile 兩條路徑都由同一實作接線，而交付只接了 release。

**但那是 Coordinator 的問題。** 需求方 2026-08-11 裁定「只接 release」，PM 只寫進 checkpoint 留言與 handoff 證據，**從未 `amend` 進規範欄位**。已於 `amend` op `3cd13f81` 補正，並把該 finding 的 `attribution` 更正為 `coordinator`。

**請判斷這個更正是否正當**——若你認為即使卡面修訂了，交付仍未滿足新條文，那是另一回事，直接說。

### 一、複驗新增的兩項驗收條文

**（1）單一 executor 形狀須保留**：`release` 必須經由 `execute_closeout_transition`，且該函式**不得因只接一條路徑而內含 release 專屬邏輯**。

執行者的檢查分三種手段：AST（`trigger` 在函式體內只出現於四個 `CloseoutResult(...)` 的關鍵字引數，無 `"release"`／`"reconcile"` 字面常數）、介面面（executor 輸入全是純資料，release 專屬翻譯全在呼叫點）、**七個分叉突變體**。

**M48 值得單獨看**：它分叉在「複驗沒帶回 tip」的保險絲上，**整份既有套件全綠，只有新的 AST 規則殺得掉**。PM 已獨立重現——排除本輪新增兩條後 `379 passed` 存活，新測試 FAILED。

請攻擊：**AST 檢查能否被繞過**？（例如把分支藏進被呼叫的 helper、或用 `trigger` 以外的變數承載同一資訊）執行者自承 `CloseoutEffectWriter.write_release_terminal()` 名字帶 release 但主張那是命名不是分叉——**請判斷那個區分成不成立**。

**（2）`core_pain_resolved` 的判準改了**：以本卡宣告射程（release 路徑）為界，**但若文件對 reconcile 限制的揭露不足或語氣淡化，仍應判 `no`**。

執行者改掉的最重要一處：原文件第 4 節開頭**用現在式宣稱 reconcile 已共用 executor**，而 reconcile 根本不存在；同型敘述在 `cleanup.py` 的模組 docstring 與 `evaluate_cleanup_guard` docstring 各一處，三處全改。

請判斷揭露是否已足夠——**這是新條文明文賦予你的否決依據**。

### 二、跨卡 X5：本卡把不可逆刪除接在一個首寫不自描述的動詞上

`handoff --next-stage release --cleanup` 的效果順序是 `owner` → `交付狀態` → `最後交接` → `iteration` → Issue body Log。[#23](https://github.com/ruan6047/ai-workflow/issues/23) §7.1.2 判 `handoff` 首寫**不合格**（首寫是 owner 欄位，非載荷可攜），故該動詞 E1 不成立。

執行者寫成 §9 第 10 項，並與 §9 第 2 項明確分野：第 2 項是「**寫了，但不知道有沒有生效**」，第 10 項是「**生效了，但事件流上認不出是誰寫的**」，兩節互相指路。並接出同源線：R2-001「讀一次不構成保證」→ 第 2 項「寫一次不構成生效確認」→ 第 10 項「寫一次不構成可辨識」。

請判斷：**這個三面綜合成立嗎**？以及不合併的理由（「其中一條被修掉會讓另一條被誤判為一併解決」）是否充分。

### 三、PM 的兩份實跑報告，請覆核方法而非接受結論

- **R2 期間**（`b1273ab` 的碼）：拋棄式卡 [#28](https://github.com/ruan6047/ai-workflow/issues/28)，成功路徑＋拒絕路徑各一次。
- **R3 之後**（`bc099f6` 的碼）：拋棄式卡 [#33](https://github.com/ruan6047/ai-workflow/issues/33)，條件式刪除在真實 GitHub 上走完，`GIT_TRACE_PACKET` 捕到 old-oid 為複驗讀到的 tip 而非全零。

**PM 另做了一個獨立實驗**：建探針分支 → 另一 clone 推入新提交 → 本機刻意不 fetch 使 remote-tracking ref 停在舊值 → 以與該過期追蹤 ref 一致的期望值送出租約刪除。結果**被客戶端拒絕且線路上一條更新指令都沒送**——證明帶明確期望值時租約比對的是**遠端當下廣告的 tip**，不是本地過期的追蹤 ref。

**這比執行者論證的更強，但也讓「GitHub 伺服器端是否做 CAS」測不到了**（客戶端先擋下）。兩份報告都自列了未涵蓋範圍，**請判斷那些劃界是否誠實、有沒有漏列**。

### 四、門檻提醒（重要）

同日的 escalation checkpoint 判 `continue`（兩條件皆不成立），但**兩個根因家族各已跨兩個 attempt**：

| 家族 | 出現於 |
|---|---|
| `remote-branch-toctou-before-destructive-delete` | R1-001、R2-001 |
| `closeout-executor-not-wired-to-real-destructive-paths` | R1-002、R3-001 |

**R4 若再出現任一個，即滿足第一條件、下一輪強制 `escalate`。** 若你判定 R3-001 仍開啟（例如認為卡面修訂不足以閉合它），**請沿用 `closeout-executor-not-wired-to-real-destructive-paths` 這個家族名，不要另起新名**——另起新名會把門檻洗掉。

### 五、已知殘留（PM 自審已找到，不必重複報，但可判斷處置是否恰當）

1. `reconcile` 側完全無守衛（指令不存在），核心痛點僅部分關閉——已由卡面第 4 條劃出射程。
2. §9 第 2 項（effect writer 回報成功 ≠ 狀態面真的變了）本輪未修，執行者上一輪已主動調高其嚴重度。
3. `--cleanup` 非預設；不帶旗標的 release 會造出 `illegal_terminal_before_cleanup`，事後補 `--cleanup` 會被擋（已寫成測試）。
4. 本輪的條件式刪除**未再對真實狀態面實跑**——PM 的補跑用的是 `bc099f6`，本輪只改文件與測試，`cleanup.py` 為 docstring 零邏輯改動（PM 已逐行核）。

### 六、T4 未結事項

**最高風險項（實際刪除路徑）須需求方 sign-off**，不由查核者或 PM 代行。請判斷現有證據是否足以支撐 sign-off，或還缺什麼。

### 環境紅線

唯讀查核；**不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行任何有副作用的 `wfcli`**。破壞性驗證一律在 disposable 臨時 repo 內做。**不得 amend 已推送的 commit、不得 `push -f`。**

**留言紀律**：不得出現事件 marker 的字面前綴（`wf-review-event` 後直接接半形冒號），連散文引用與 code fence 示範都不行——`doctor` 全文子字串比對，命中即隔離整卡。拆開書寫，發文前 `grep` 一次。

### 輸出

依 `templates/review-prompt.md` §5，`core_pain_resolved` 與 `self_run` 必填。**三項強制**：

1. **逐項回報前輪 finding 閉環**——R3-001 明列 `resolved`／`withdrawn`／仍開啟，缺此節即 `review-invalid`。
2. **五個 schema 欄位自己填**；`root_cause_id` 見上方門檻提醒。
3. **留收據**：`wf-review-receipt:v1` **多行格式**（`card_id:` 與 `source_sha:` 各自獨立成行，單行 `key=value` 形式 `doctor` 認不得），**把被雜湊的報告全文放進同一則留言**並在留言內寫死取材規則（起點、終點、編碼、換行、是否 strip、排除範圍）。上一輪你們的 #25 收據只雜湊了 YAML，前輪閉環與核心痛點陳述在雜湊外；且邊界規則不夠死，PM 試到第三個變體才對上。

**YAML 限制**：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、值含 ` #` 須加引號。非 schema 的頂層鍵會被容忍。


## Comment 5260924860 · 2026-08-12T01:14:28Z

<!-- wf-review-receipt:v1
card_id: WF-CLEANUP-GUARD1
source_sha: bbce273877ac8d8df9409c9a5c7830fd2f4eb415
report_sha256: 7a9df9fd45267ac0aad1965d92970d3d652d4bddbdec9612c5e16a4988f73591
-->

取材規則：被雜湊報告區段從 `<report-begin>` 下一行第一個 `c`（`core_pain_resolved`）起，到 `<report-end>` 前一行最後的 LF 為止；UTF-8 編碼、LF 換行、無 strip、排除收據 HTML 註解、此取材規則行與兩個邊界標記。

<report-begin>
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cleanup-guard1 && git rev-parse HEAD && git status --short && git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD"
    observed: "HEAD=bbce273877ac8d8df9409c9a5c7830fd2f4eb415；工作區乾淨；指定基線為祖先；遠端 claude/WF-CLEANUP-GUARD1 同 SHA。"
  - command: "在 git archive bbce273877ac8d8df9409c9a5c7830fd2f4eb415 建立的 /tmp/wf-cleanup-review.Git1Oq/cli 執行 uv run pytest -q"
    observed: "382 passed in 31.72s；僅使用拋棄式副本與 pytest 暫存 Git 儲存庫。"
  - command: "在相同拋棄式副本執行 uv run pytest -q tests/test_cleanup.py tests/test_release_cleanup.py -rA"
    observed: "85 passed in 29.00s；包含本機 bare remote、拒絕、恢復與 release 接線案例。"
  - command: "在拋棄式副本把 expected_tip 為 None 的保險絲改成 `and locals()[\"trig\" + \"ger\"] == \"rec\" + \"oncile\"`，再執行 uv run pytest -q tests/test_cleanup.py::test_executor_body_never_branches_on_the_trigger"
    observed: "1 passed；突變已在 executor 內依 trigger 分叉，但 AST 測試未偵測，因為它只找 Name(trigger) 與完整 release/reconcile 常數。"
  - command: "git diff --check 7451b72ba7679893043950d71bad9642665e25da..bbce273877ac8d8df9409c9a5c7830fd2f4eb415；閱讀 Issue #25 最後派審、escalation checkpoint、PM 自審收斂紀錄與 #28/#33 PM 實跑報告"
    observed: "diff 無 whitespace 錯誤；前置與指定證據皆已覆核。"
prior_round_closure:
  - finding_id: "WF-CLEANUP-GUARD1-R3-001"
    status: "仍開啟"
    evidence: "卡面驗收雖經 amend 縮為 release-only，但 Issue 核心痛點原文仍明定 reconcile --apply 與 release，並把『無人看管的批次修復』列為危險主體；PM 亦明認 wfcli amend 沒有 core-pain 更正通道。依 canonical §5.1，驗收條文不能取代具否決權的核心痛點。"
    disposition: "以唯一狀態寫入通道提供並執行核心痛點/驗收一致的正式更正，或由需求方明確重開並重界定問題；在此之前不得宣告核心痛點已消失。"
findings:
  - finding_id: "WF-CLEANUP-GUARD1-R4-001"
    severity: critical
    blocking: true
    finding_class: authoritative-artifact
    attribution: coordinator
    root_cause_id: "closeout-executor-not-wired-to-real-destructive-paths"
    evidence: "Issue #25 的權威核心痛點仍要求 reconcile --apply 與 release 均受守衛，且特別指出無人看管的批次修復；現況只接 release，文件 §4.1/§9.1 也明載 reconcile 完全無守衛。amend 僅改驗收條件，不能更改 canonical §5.1 的第一判準。"
    disposition: "不要以縮小驗收條文間接覆寫核心痛點。先由唯一寫入通道新增可稽核的核心痛點更正並由需求方裁定，或完成 reconcile 接線；否則維持 REQUEST_CHANGES。"
  - finding_id: "WF-CLEANUP-GUARD1-R4-002"
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: "executor-trigger-branch-regression-guard-bypass"
    evidence: "test_executor_body_never_branches_on_the_trigger 只拒絕 AST Name(trigger) 的非結果讀取與完整字面常數。隔離突變以 locals()[\"trig\" + \"ger\"] 與 \"rec\" + \"oncile\" 在 expected_tip 為 None 的保險絲依觸發者分叉，該測試仍 1 passed。這直接反駁文件 §4.0 對 AST 不能以其他變數/藏在表達式繞過的承重宣稱；M48 恰是未被行為測試覆蓋的保險絲。"
    disposition: "以可驗證的資料流限制或更完整 AST/語意檢查封堵動態名稱與組合字串，並新增 M48 類情境的 release/reconcile 行為測試；新測試須先對本突變跑紅。"

核心痛點裁決：否。原始痛點的無人看管 reconcile --apply 路徑仍完全沒有守衛；本卡當前的 release 接線雖安全性回歸通過，卻不能消除權威核心痛點。故依 canonical AI_WORKFLOW.md §5.1 結論必為 REQUEST_CHANGES。

驗收與證據覆核：release 的接線、清理前提、條件式刪除與觀測式恢復在隔離測試中通過。reconcile 限制的揭露充分且沒有淡化；§9 第 2 項與第 10 項的分野成立，前者是寫入結果確認、後者是事件來源可辨識性，修法與失敗模式不同，不應合併。X5 的雙向引用與外部相依揭露已閉合。PM 對 #28/#33 的實跑範圍劃界誠實：真實 GitHub 成功路徑與 stale lease 客戶端拒絕已證實，但 GitHub server-side CAS 與 CLI 內真實競態拒絕仍未證實。這些證據足以讓需求方做 sign-off 判斷，卻不能代替需求方 sign-off；目前未見該 sign-off，因此本卡也不得結案。

範圍外發現：無。
<report-end>

## Comment 5261000458 · 2026-08-12T01:27:00Z

<!-- wf-review-event:v1 card_id=WF-CLEANUP-GUARD1 source_sha=bbce273877ac8d8df9409c9a5c7830fd2f4eb415 attempt_id=WF-CLEANUP-GUARD1-e0-bbce273877ac8d8df9409c9a5c7830fd2f4eb415 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CLEANUP-GUARD1`　attempt_id：`WF-CLEANUP-GUARD1-e0-bbce273877ac8d8df9409c9a5c7830fd2f4eb415`
- 查核者：GPT-5@Codex 子代理（收據 issuecomment-5260924860，多行格式合規；PM 已回讀重算 report_sha256=7a9df9fd… 相符。⚠️ 被雜湊區段末尾另有三段散文（核心痛點裁決／驗收與證據覆核／範圍外發現），解析器不接受區塊內混散文，故本 event 只轉錄 YAML 部分；散文原文在收據留言內且受同一雜湊保護）　escalation_epoch：0
- source_sha：`bbce273877ac8d8df9409c9a5c7830fd2f4eb415`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T09:26:59+08:00

### self_run（查核者實跑）

- `cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cleanup-guard1 && git rev-parse HEAD && git status --short && git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD`
  - HEAD=bbce273877ac8d8df9409c9a5c7830fd2f4eb415；工作區乾淨；指定基線為祖先；遠端 claude/WF-CLEANUP-GUARD1 同 SHA。
- `在 git archive bbce273877ac8d8df9409c9a5c7830fd2f4eb415 建立的 /tmp/wf-cleanup-review.Git1Oq/cli 執行 uv run pytest -q`
  - 382 passed in 31.72s；僅使用拋棄式副本與 pytest 暫存 Git 儲存庫。
- `在相同拋棄式副本執行 uv run pytest -q tests/test_cleanup.py tests/test_release_cleanup.py -rA`
  - 85 passed in 29.00s；包含本機 bare remote、拒絕、恢復與 release 接線案例。
- `在拋棄式副本把 expected_tip 為 None 的保險絲改成 `and locals()["trig" + "ger"] == "rec" + "oncile"`，再執行 uv run pytest -q tests/test_cleanup.py::test_executor_body_never_branches_on_the_trigger`
  - 1 passed；突變已在 executor 內依 trigger 分叉，但 AST 測試未偵測，因為它只找 Name(trigger) 與完整 release/reconcile 常數。
- `git diff --check 7451b72ba7679893043950d71bad9642665e25da..bbce273877ac8d8df9409c9a5c7830fd2f4eb415；閱讀 Issue #25 最後派審、escalation checkpoint、PM 自審收斂紀錄與 #28/#33 PM 實跑報告`
  - diff 無 whitespace 錯誤；前置與指定證據皆已覆核。

### findings（2，其中 blocking 2）

- **WF-CLEANUP-GUARD1-R4-001**　severity=critical　blocking=true　class=authoritative-artifact　attribution=coordinator　root_cause_id=`closeout-executor-not-wired-to-real-destructive-paths`
  - evidence：Issue #25 的權威核心痛點仍要求 reconcile --apply 與 release 均受守衛，且特別指出無人看管的批次修復；現況只接 release，文件 §4.1/§9.1 也明載 reconcile 完全無守衛。amend 僅改驗收條件，不能更改 canonical §5.1 的第一判準。
  - disposition：不要以縮小驗收條文間接覆寫核心痛點。先由唯一寫入通道新增可稽核的核心痛點更正並由需求方裁定，或完成 reconcile 接線；否則維持 REQUEST_CHANGES。
- **WF-CLEANUP-GUARD1-R4-002**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`executor-trigger-branch-regression-guard-bypass`
  - evidence：test_executor_body_never_branches_on_the_trigger 只拒絕 AST Name(trigger) 的非結果讀取與完整字面常數。隔離突變以 locals()["trig" + "ger"] 與 "rec" + "oncile" 在 expected_tip 為 None 的保險絲依觸發者分叉，該測試仍 1 passed。這直接反駁文件 §4.0 對 AST 不能以其他變數/藏在表達式繞過的承重宣稱；M48 恰是未被行為測試覆蓋的保險絲。
  - disposition：以可驗證的資料流限制或更完整 AST/語意檢查封堵動態名稱與組合字串，並新增 M48 類情境的 release/reconcile 行為測試；新測試須先對本突變跑紅。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5261330607 · 2026-08-12T02:19:48Z

## 需求方裁定：R4-001 走出路 (a)——以唯一寫入通道正式更正核心痛點

R4 查核者給了三條出路：**(a)** 以唯一寫入通道新增可稽核的核心痛點更正並由需求方裁定、**(b)** 完成 reconcile 接線、**(c)** 由需求方明確重開並重界定問題。

**需求方 2026-08-12 裁定 (a)**（原話：「#25 走 (a)」）。

### 這代表什麼

**R4-001 的處置不在本卡射程內。** 它需要 `wfcli amend --core-pain`，而該能力今天不存在——本卡（與 PM）在 2026-08-12 嘗試縮小射程時撞到的正是這件事，當時只能改由驗收條文的判準吸收，PM 自記「繞過而非修好」，查核者隨即把它判為 critical。

該能力由 [#37](https://github.com/ruan6047/ai-workflow/issues/37) `WF-CARD-FIELD-CORRECTION1` 承接（自 [#12](https://github.com/ruan6047/ai-workflow/issues/12) 的殘餘射程轉出），需求方已裁定「核心痛點補，帶授權綁定」，**執行中**。

**所以 R4-001 在 #37 交付並通過查核之前，本卡無法閉合它。** 這是排程相依，不是執行者的問題。

### 為什麼不選 (c)——它更快，但代價要講清楚

(c) 就是本專案剛對 #12 做過的一手：結案、以正確的核心痛點另開卡承接。它會**立刻**解開本卡、**立刻**釋放 `doctor.py` 讓 [#30](https://github.com/ruan6047/ai-workflow/issues/30) 動起來，且交付的工作不丟（分支轉掛）。

需求方選 (a) 而非 (c) 的理由，PM 記錄如下：**(c) 會是第二次用「開新卡」繞過欄位改不了的問題。同一個繞法用兩次，該問的是為什麼欄位一直改不了——而那正是 #37 在解的。** 選 (a) 等一輪，換來的是那個能力本身。

**代價要明說**：本卡與 #30 的排程因此延後，`doctor.py` 繼續被本卡持有。

### R4-002 不受影響，本輪照修

R4-002（`executor-trigger-branch-regression-guard-bypass`）與 R4-001 無關，且 PM 已獨立重現：以 `locals()["trig" + "ger"] == "rec" + "oncile"` 在保險絲上依 trigger 分叉，`test_executor_body_never_branches_on_the_trigger` **1 passed**、全套 **382 passed**，都沒抓到。文件 §4.0 對「AST 不能以其他變數／藏在表達式繞過」的承重宣稱被推翻。

**本卡本輪只處理 R4-002。** R4-001 在卡上維持開啟，並於下一輪派審詞明示其阻塞歸屬，不得被誤記為 `resolved`。


## Comment 5262342420 · 2026-08-12T04:38:19Z

## 需求方裁定：R4-001 走出路 (a)，正式更正核心痛點

R4 查核者判 `core_pain_resolved: no`、`critical`、blocking，`root_cause_id: closeout-executor-not-wired-to-real-destructive-paths`，disposition 逐字：

> 不要以縮小驗收條文間接覆寫核心痛點。先由唯一寫入通道新增可稽核的核心痛點更正並由需求方裁定，或完成 reconcile 接線；否則維持 REQUEST_CHANGES。

**需求方 2026-08-12 裁定：走 (a)。**

### 先認一件事

需求方**2026-08-11 就已裁定「只接 release」**，但 PM 只把它寫進 checkpoint 留言與 handoff 證據，**從未 `amend` 進規範欄位**。查核者把該 finding 的 `attribution` 更正為 `coordinator` 是對的。今天這則裁定是補上那個從未走完的通道，不是新決定。

### 更正後的痛點必須自己承認的事

原痛點的危險主體逐字是「一個無人看管的批次修復可以刪掉別人尚未提交的工作」——**那指的是 `reconcile --apply`，而該指令不存在**。收窄到 release 之後，**本卡關掉的不是它原本命名的那個危險**。

更正後的痛點因此必須自己寫下這件事，**不得把 reconcile 從句子裡刪掉當作沒發生過**——那會是換一種方式做同一件被判 critical 的事。三點須全部出現：

1. 守衛涵蓋**今天真實存在的破壞性收尾路徑**（`handoff --next-stage release --cleanup`），該路徑會移除 worktree、刪本地與遠端分支；
2. **`reconcile --apply` 完全無守衛，且該指令尚未存在**——原痛點指名的「無人看管的批次修復」**未被本卡關閉**；
3. executor 形狀刻意設計成兩個觸發者共用，使 reconcile 建成時可直接接上而不需重寫守衛。**需求方認定這是本卡真正買到的東西**，也是它與「只做一半」的實質區別；該形狀已由 AST 檢查、介面面與七個分叉突變釘住（含 M48——整份既有套件全綠、只有新的 AST 規則殺得掉的那條）。

### 殘餘的去處

原危險主體未關閉這件事**已另開卡承接**，不留在本卡的備註裡。沒有承接卡的話，這次更正等於把一個 critical 的痛點降級成無人負責的句子。

### 不在本則範圍

**T4 的 sign-off 不由本則給予。** 查核者逐字：「這些證據足以讓需求方做 sign-off 判斷，卻不能代替需求方 sign-off；目前未見該 sign-off，因此本卡也不得結案。」sign-off 應在下一輪查核通過、最高風險項（實際刪除路徑）的證據被確認之後另行給出。

**亦不追溯補建或改寫任何歷史留痕**（需求方 2026-08-12 明示）。本則為前向更正。

### 本則的用途

依 `WF-CARD-FIELD-CORRECTION1`（#37，已於 `20f2ea3` 併入 main）上線的 `wfcli amend --core-pain --ruling-url`，核心痛點更正須綁定一則需求方裁定留言並比對其 GitHub comment author。**本則即該裁定留痕。**

## Comment 5262404015 · 2026-08-12T04:48:03Z

## escalation-checkpoint（第五個可計數 attempt 前）

```yaml
escalation_epoch: 0
trigger_attempt_id: WF-CLEANUP-GUARD1-e0-bbce273877ac8d8df9409c9a5c7830fd2f4eb415
unique_attempt_count: 4
checkpoint_decision: escalate
checkpoint_rationale: |
  第一條件成立。根因家族 closeout-executor-not-wired-to-real-destructive-paths
  跨三個 unique attempt：a036ed5（R1-002）、bc099f6（R3-001）、bbce273（R4-001）。
  依 templates/review-escalation.md §4，條件成立時 checkpoint_decision 只能是 escalate。

  另兩個家族未達門檻：remote-branch-toctou-before-destructive-delete 跨兩個
  （a036ed5 R1-001、b1273ab R2-001）；executor-trigger-branch-regression-guard-bypass
  一個（bbce273 R4-002）。第二條件不成立——R4-001 與 R4-002 皆已於 4353c18 處置，
  無前輪 accepted blocking finding 未被表態。

  數字由指令輸出產生：以 gh 取四則 review event 原文、正則抽 finding_id 與
  root_cause_id 後計 unique attempt 集合，非人工清點。
```

### 這則與我先前六則的差別

我在 2026-08-11／12 於 #21／#22／#24／#25 手寫的七則 checkpoint **全部不合 §5**：缺 `escalation_epoch`、`trigger_attempt_id`、`unique_attempt_count` 三個必填欄，並多出四個未定義鍵（`escalation_resolution`、`decided_by`、`counts_toward_escalation`、`attempts_so_far`）。該事實已由 `WF-ESCALATION-RESOLUTION-GAP1`（#39）於 `41a9f41` 以機械輸出逐則判定，處置為**全部標 legacy、不改寫、不重發、不追溯補建**（需求方 2026-08-12 明示不補歷史紀錄）。

**本則是第一則照 §5 五個必填欄寫的 checkpoint。** 上述四個未定義鍵一個都沒有用。

### `escalate` 之後怎麼辦，契約今天答不出來

§4 規定條件成立時只能 `escalate`，而 `escalation-epoch-change` 的理由只有 `replan` 與 `change-executor` 兩個。**「escalate 之後需求方選擇維持同執行者」在契約裡沒有表示法**——那正是 #39 要補的缺口，它已於 `41a9f41` 設計為獨立事件型別 `escalation-resolution`（否決了把它塞進 checkpoint 的乙案），但**尚未通過查核、尚未合併**。

`WF-22-CLI4`（#9）的 checkpoint writer 亦已明確**拒收** `escalation_resolution` 作為 checkpoint 欄位，訊息指名等待 #39——那個拒收是對的，我不繞過它。

**所以本則只記 `escalate`，不記解除。** 需求方對「是否維持同執行者」的裁定須另以留言為之，並在 #39 落地後補寫為正式的 `escalation-resolution` 事件；在那之前，事件流上這張卡的狀態就是**升級中**。

### 給下一輪查核者

若你在 `4353c18` 上再次產出 `closeout-executor-not-wired-to-real-destructive-paths` 家族的 finding，那會是**第四次**。請沿用該家族名，**不要另起新名**——另起新名會把門檻洗掉，而那會直接改變需求方是否換執行者的判斷。

R4-001 已依需求方裁定走出路 (a) 由核心痛點更正承接（op `de18defc`）；若你認為該更正不足以閉合它，那是正當 finding，但請如實沿用同一家族名。

## Comment 5262430465 · 2026-08-12T04:52:16Z

## 需求方裁定：升級後維持同執行者

同日的 escalation-checkpoint（`issuecomment-5262404015`）依 §4 判 `escalation_decision: escalate`——根因家族 `closeout-executor-not-wired-to-real-destructive-paths` 跨三個 unique attempt（`a036ed5` R1-002、`bc099f6` R3-001、`bbce273` R4-001），第一條件成立時 `checkpoint_decision` 只能是該值。

**需求方 2026-08-12 裁定：維持同執行者。**

### 判準

三次的性質不同，不是同一個執行者反覆做錯同一件事：

| attempt | finding | 實質歸因 |
|---|---|---|
| `a036ed5` | R1-002 | 執行者——真的沒接線，交付只做了一半 |
| `bc099f6` | R3-001 | **Coordinator**——需求方 2026-08-11 已裁定「只接 release」，PM 只寫進 checkpoint 留言與 handoff 證據、從未 `amend` 進規範欄位。查核者已將該 finding 的 `attribution` 更正為 `coordinator` |
| `bbce273` | R4-001 | **Coordinator**——同一缺口的延續：核心痛點原文仍寫著兩條路徑，而 `--core-pain` 通道當時尚不存在 |

**三次裡有兩次的歸因指向 Coordinator。** 家族計數本身沒錯——它量的是「同一個病灶反覆出現」，而那確實發生了——但**病灶的擁有者不是執行者**。

第四個家族 `executor-trigger-branch-regression-guard-bypass`（R4-002）是全新的，且執行者本輪的處置品質高於要求：它自己發現最初三個突變全死在**編譯期常數摺疊**上（`"rec" + "oncile"` 被摺成 `reconcile`），判定若就此收工「3/3 KILLED」的承重點會站在編譯器最佳化上，因而重做了防摺疊版（`"".join([...])`）。那是沒有人要求的自我否定。

### 利害衝突揭露

**提出此建議的 PM 正是被歸因兩次的那一方**，故該建議帶有明顯的利害衝突，裁定權在需求方而非 PM。需求方已依上表逐項檢視後裁定維持。

### 這則裁定今天沒有正式的事件表示法

§4 規定條件成立時只能 `escalate`，而 `escalation-epoch-change` 的理由只有 `replan` 與 `change-executor` 兩個——**「維持同執行者」在契約裡沒有表示法**。`WF-ESCALATION-RESOLUTION-GAP1`（#39）已於 `41a9f41` 設計 `escalation-resolution` 獨立事件型別補此缺口，但尚未通過查核、尚未合併；`WF-22-CLI4`（#9）的 checkpoint writer 亦正確拒收 `escalation_resolution` 作為 checkpoint 欄位。

**所以本則是散文留痕，不是事件。** #39 落地後應據此補寫為正式的 `escalation-resolution` 事件（`resolution_basis: fresh-ruling`、`continued_owner` 為當前執行者、`resolved_by: ruan6047`、`authorization_binding: structurally-vacuous`）。在那之前，事件流上這張卡的狀態仍是升級中——**本則不改變那個事實，只記錄需求方對它的處置。**

### 給下一輪查核者

本裁定**不降低**本輪的判準。若你在 `4353c18` 上再次產出 `closeout-executor-not-wired-to-real-destructive-paths` 家族的 finding，那是第四次，請沿用該家族名、不要另起新名——維持同執行者的裁定是針對前三次作出的，第四次會使它需要重新評估。

## Comment 5262453721 · 2026-08-12T04:55:50Z

## 派審：#25 `WF-CLEANUP-GUARD1` R5（T4）

⚠️ 審核對象 **`ruan6047/ai-workflow#25`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cleanup-guard1
分支：claude/WF-CLEANUP-GUARD1（PR #27）　　被審 SHA：4353c1863f8b83e5532585dbcdcdb25e876098a2
基線：7451b72ba7679893043950d71bad9642665e25da（已驗為祖先）　　iteration：3
```

> **本則為權威。** 摘要表格與轉述若衝突以本則為準；**值解不開時先回對本則，不要直接停手**。

### ⚠️ 門檻：第一條件已成立，本輪是第五個可計數 attempt

同日 checkpoint（`issuecomment-5262404015`）依 §4 判 `escalate`。數字由指令輸出產生：

| 根因家族 | unique attempt |
|---|---:|
| `closeout-executor-not-wired-to-real-destructive-paths` | **3**（`a036ed5` R1-002、`bc099f6` R3-001、`bbce273` R4-001） |
| `remote-branch-toctou-before-destructive-delete` | 2 |
| `executor-trigger-branch-regression-guard-bypass` | 1 |

**需求方裁定維持同執行者**（`issuecomment-5262430465`），判準是三次裡有兩次的實質歸因指向 Coordinator 而非執行者。**該裁定不降低本輪判準**——若你再次產出第一個家族的 finding，那是第四次，**請沿用該家族名，不要另起新名**；另起新名會把門檻洗掉，直接改變需求方是否換人的判斷。

### 一、複驗 R4-002：執行者取資料流限制而非更完整的 AST 檢查

理由是後者無論做到多細，能誠實宣稱的都只有「常見寫法會被擋」，而 §4.0 要承擔的是「不得分叉」——**強度對不上就只能改宣稱，等於把問題留著**。

作法：`execute_closeout_transition` 縮成只有一個運算式的貼標籤層；真正做事的 `_execute_closeout` **簽章裡沒有 trigger**，也無同名自由變數或模組全域。公開簽章一字未改，守衛仍在函式體內故繞過貼標籤層直接呼叫私有函式不會繞過守衛。

**⚠️ 執行者自己抓到一件事並據以重做**：最初三個突變全死在**編譯期常數摺疊**上（`"rec" + "oncile"` 被摺成 `reconcile`），若就此收工「3/3 KILLED」的承重點會站在編譯器最佳化上。它改用 `"".join([...])` 做防摺疊版重跑，`M54`／`M56` 才是承重證據。**PM 已於拋棄式目錄獨立注入你原句的防摺疊版驗證**：`test_the_destructive_body_cannot_name_the_trigger` 轉紅、其餘 387 全綠。

**請攻擊**：(a) 資料流限制真的關掉了你原本那條路嗎，還是只是把它推遠？(b) `M55`（走呼叫堆疊的防摺疊版）**形狀面三層全綠、只有行為面接住**——執行者據此把 §4.0 的宣稱分成「可宣稱／不可宣稱／是約定不是強制」三段。**請判斷那個三分是否誠實且完整**，特別是「行為面只覆蓋跑過的路徑」這句買到了什麼。

### 二、R4-001 走出路 (a)，請判斷更正是否正當

需求方 2026-08-12 裁定走 (a)，核心痛點已以 `wfcli amend --core-pain --ruling-url` 正式更正（op `de18defc`，裁定留痕 `issuecomment-5262342420`，授權綁定生效）。

你的 disposition 逐字禁止「以縮小驗收條文間接覆寫核心痛點」，故更正後的痛點**自己寫下三件**：涵蓋範圍限於今天真實存在的 `release --cleanup`；**`reconcile --apply` 完全無守衛且該指令尚未存在，原痛點指名的危險主體「無人看管的批次修復」未被本卡關閉**；executor 共用形狀是本卡在 release 之外真正買到的第二件東西（需求方認定）。

殘餘已具名承接於新開的 **#45**（T4），不留在本卡備註裡。

**請判斷**：(a) 這個更正是否真的不是「換一種方式做同一件被判 critical 的事」？(b) 第三點（共用形狀算不算價值）需求方認定為算——**你可以有不同判斷**；若你認為不算，本卡的定位就要再降一級。

### 三、T4 未結事項

**sign-off 尚未給予。** 你上一輪逐字說明「這些證據足以讓需求方做 sign-off 判斷，卻不能代替需求方 sign-off」。需求方裁定 sign-off 待本輪通過且最高風險項（實際刪除路徑）證據被確認後另行給出。**請說明現有證據是否足以支撐，或還缺什麼。**

### 四、一件過程事故，執行者主動報告

突變 harness 批次跑 `M51` 時被 2 分鐘 timeout 砍掉、`finally` 未跑完，**把突變留在工作樹**（`.bak` 殘留）。它在 commit 前逐檔讀 diff 時抓到並還原、單獨重跑確認後才提交。**抓到它靠的是人工讀 diff 不是 harness 保證**——執行者指出這與本卡在講的「中斷後留下的半完成組合」是同一形狀。

### 五、已知殘留

`reconcile` 側完全無守衛（指令不存在）；§9 第 2 項（effect writer 回報成功 ≠ 狀態面真的變了）本輪未修；`--cleanup` 非預設；本輪未再對真實狀態面實跑（`cleanup.py` 本輪為邏輯改動故此點**與上輪不同**，請自行判斷是否需要新的真實實跑）。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**（`resolved`／`withdrawn`／仍開啟）並附證據。
2. **五個 schema 欄位自己填**。`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` **多行格式**（`card_id:` 與 `source_sha:` **各自獨立成行**，單行 `key=value` 形式 `doctor` 認不得），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍。**規則若提到起訖 delimiter 的字面，請說清楚是「本規則之後的下一個」。**

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、值含 ` #` 須整個值加引號、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**。非 schema 的頂層鍵會被容忍。


## Comment 5262617332 · 2026-08-12T05:15:19Z

<!-- wf-review-receipt:v1
card_id: WF-CLEANUP-GUARD1
source_sha: 4353c1863f8b83e5532585dbcdcdb25e876098a2
report_sha256: e578f526f772bc919a93ef509a165adea82971090c9d08be33de1043d073a689
-->
取材規則：取本規則之後下一個 `--- report-begin ---` 的下一個字元起，至其後下一個 `--- report-end ---` 的前一個字元止；UTF-8、LF、no strip，包含結尾 LF；排除 receipt HTML 註解、此取材規則行與兩條 delimiter 行。
--- report-begin ---
core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "git rev-parse HEAD; git status --porcelain; git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD"
    observed: "HEAD=4353c1863f8b83e5532585dbcdcdb25e876098a2；工作區乾淨；基線祖先檢查 exit 0；origin/claude/WF-CLEANUP-GUARD1 指向該 SHA。"
  - command: "git diff --check 7451b72ba7679893043950d71bad9642665e25da 4353c1863f8b83e5532585dbcdcdb25e876098a2; git diff --name-status 7451b72ba7679893043950d71bad9642665e25da 4353c1863f8b83e5532585dbcdcdb25e876098a2"
    observed: "無 whitespace error；寫入集為 cleanup.py、doctor.py、doctor_cmd.py、handoff_cmd.py、三個對應測試與交付文件；R5 最後提交僅更新 WF_CLEANUP_GUARD1.md 的宣稱邊界。"
  - command: "git archive 4353c1863f8b83e5532585dbcdcdb25e876098a2 | tar -x -C /tmp/wf25-r5.x3SNSH; cd /tmp/wf25-r5.x3SNSH/cli; PYTHONDONTWRITEBYTECODE=1 uv run pytest -q tests/test_cleanup.py"
    observed: "77 passed in 27.18s；在拋棄式副本執行，未改被審工作樹。"
  - command: "cd /tmp/wf25-r5.x3SNSH/cli; PYTHONDONTWRITEBYTECODE=1 uv run pytest -q tests/test_amend.py tests/test_card.py tests/test_commands_mocked.py tests/test_doctor.py tests/test_git_ops.py tests/test_project_mocked.py tests/test_registry.py tests/test_release_cleanup.py tests/test_resources.py tests/test_review.py tests/test_validation.py"
    observed: "311 passed in 8.82s；合計 388 passed。ruff executable 不在此 uv 環境，無法執行 ruff check。"
  - command: "在拋棄式副本將 _execute_closeout 注入 sys._getframe(1).f_locals 的防常數摺疊 trigger 分叉，執行 pytest -q tests/test_cleanup.py -k 'destructive_body_cannot_name or destructive_body_frame or labelling_wrapper or swapping_the_trigger'"
    observed: "1 failed、4 passed；失敗為 test_swapping_the_trigger_changes_nothing_but_the_label 的 release 與 reconcile fingerprint 不同，證實行為面接住 M55 類反例；T1 至 T3 仍通過，與文件揭露一致。"
prior_accepted_blocking_findings:
  - finding_id: "WF-CLEANUP-GUARD1-R4-001"
    status: resolved
    evidence: "Issue 卡面以 amend op de18defc 正式更正核心痛點並綁定需求方裁定；現行核心痛點逐字限縮至 release --cleanup、明載 reconcile 未關閉且由 WF-RECONCILE-CLEANUP-GUARD1 承接，沒有以驗收條文暗中覆寫。"
  - finding_id: "WF-CLEANUP-GUARD1-R4-002"
    status: resolved
    evidence: "cleanup.py 將公開貼標籤層與不收 trigger 的 _execute_closeout 分離；資料流、行為等價與防常數摺疊 call-stack 反例均已複驗。文件明確撤回不可證的『不可能分叉』宣稱，並列出行為面僅覆蓋已跑路徑的殘留。"
sign_off_assessment:
  - outcome: "現有拋棄式真 git 刪除情境、全套測試與條件式刪除拒絕路徑的證據足以供需求方作 T4 sign-off 判斷；本查核不代替需求方 sign-off，亦不把尚未對真實 Project 和 Issue 執行的不可逆接受路徑誤報為已實跑。"
findings: []
scope_outside_findings:
  - topic: "lint 環境"
    observation: "拋棄式 uv 環境未提供 ruff executable；pytest 全數通過。此為驗證環境限制，未構成被審實作 finding。"
--- report-end ---


## Comment 5262670201 · 2026-08-12T05:20:02Z

<!-- wf-review-event:v1 card_id=WF-CLEANUP-GUARD1 source_sha=4353c1863f8b83e5532585dbcdcdb25e876098a2 attempt_id=WF-CLEANUP-GUARD1-e0-4353c1863f8b83e5532585dbcdcdb25e876098a2 -->
## 查核裁決：APPROVE

- 卡：`WF-CLEANUP-GUARD1`　attempt_id：`WF-CLEANUP-GUARD1-e0-4353c1863f8b83e5532585dbcdcdb25e876098a2`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5262617332 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=e578f526… 一次相符。本輪四份裁決皆無需 PM 作任何格式調整——區塊零散文、序列已縮排、無 code fence）　escalation_epoch：0
- source_sha：`4353c1863f8b83e5532585dbcdcdb25e876098a2`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-12T13:20:01+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git status --porcelain; git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD`
  - HEAD=4353c1863f8b83e5532585dbcdcdb25e876098a2；工作區乾淨；基線祖先檢查 exit 0；origin/claude/WF-CLEANUP-GUARD1 指向該 SHA。
- `git diff --check 7451b72ba7679893043950d71bad9642665e25da 4353c1863f8b83e5532585dbcdcdb25e876098a2; git diff --name-status 7451b72ba7679893043950d71bad9642665e25da 4353c1863f8b83e5532585dbcdcdb25e876098a2`
  - 無 whitespace error；寫入集為 cleanup.py、doctor.py、doctor_cmd.py、handoff_cmd.py、三個對應測試與交付文件；R5 最後提交僅更新 WF_CLEANUP_GUARD1.md 的宣稱邊界。
- `git archive 4353c1863f8b83e5532585dbcdcdb25e876098a2 | tar -x -C /tmp/wf25-r5.x3SNSH; cd /tmp/wf25-r5.x3SNSH/cli; PYTHONDONTWRITEBYTECODE=1 uv run pytest -q tests/test_cleanup.py`
  - 77 passed in 27.18s；在拋棄式副本執行，未改被審工作樹。
- `cd /tmp/wf25-r5.x3SNSH/cli; PYTHONDONTWRITEBYTECODE=1 uv run pytest -q tests/test_amend.py tests/test_card.py tests/test_commands_mocked.py tests/test_doctor.py tests/test_git_ops.py tests/test_project_mocked.py tests/test_registry.py tests/test_release_cleanup.py tests/test_resources.py tests/test_review.py tests/test_validation.py`
  - 311 passed in 8.82s；合計 388 passed。ruff executable 不在此 uv 環境，無法執行 ruff check。
- `在拋棄式副本將 _execute_closeout 注入 sys._getframe(1).f_locals 的防常數摺疊 trigger 分叉，執行 pytest -q tests/test_cleanup.py -k 'destructive_body_cannot_name or destructive_body_frame or labelling_wrapper or swapping_the_trigger'`
  - 1 failed、4 passed；失敗為 test_swapping_the_trigger_changes_nothing_but_the_label 的 release 與 reconcile fingerprint 不同，證實行為面接住 M55 類反例；T1 至 T3 仍通過，與文件揭露一致。

### findings（0，其中 blocking 0）

- （無）

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5262731441 · 2026-08-12T05:24:56Z

## 需求方 T4 sign-off

**需求方 2026-08-12 對本卡最高風險項（實際刪除路徑）給予 sign-off，授權合併結案。**

### 簽的是什麼證據水準

跨家族查核（GPT-5@Codex 子代理）於 `4353c1863f8b83e5532585dbcdcdb25e876098a2` 判 **APPROVE**、`core_pain_resolved: yes`、**findings 0**，R4-001 與 R4-002 皆判 `resolved`。其 sign-off 評估逐字：

> 現有拋棄式真 git 刪除情境、全套測試與條件式刪除拒絕路徑的證據足以供需求方作 T4 sign-off 判斷；本查核不代替需求方 sign-off，**亦不把尚未對真實 Project 和 Issue 執行的不可逆接受路徑誤報為已實跑**。

**需求方明確知悉並接受最後一句所指的界線**：不可逆的實際刪除路徑**從未對真實 Project 與 Issue 執行過**。已實跑的是拋棄式臨時 repo，以及兩張拋棄式智慧卡（#28、#33）——後者於真實 GitHub 上走完條件式刪除，`GIT_TRACE_PACKET` 捕到 old-oid 為複驗讀到的 tip 而非全零。

**簽的是「在這個證據水準上放行」，不是「已窮盡驗證」。**

### 查核者做了一件 PM 沒做的驗證

它在拋棄式副本注入 `sys._getframe(1).f_locals` 的**防常數摺疊 trigger 分叉**（M55 類），結果 `1 failed / 4 passed`：失敗的是 `test_swapping_the_trigger_changes_nothing_but_the_label` 的 release 與 reconcile fingerprint 不同，**證實行為面確實接住該類反例**；T1–T3 形狀面仍通過，與文件揭露的三段式宣稱一致（可宣稱／不可宣稱／是約定不是強制）。

### 本 sign-off 不涵蓋的

1. **`reconcile --apply` 完全無守衛，且該指令尚未存在。** 原核心痛點指名的危險主體「無人看管的批次修復」**未被本卡關閉**，已具名承接於 [#45](https://github.com/ruan6047/ai-workflow/issues/45)（T4）。本 sign-off 不對該路徑作任何認可。
2. **§9 第 2 項**（effect writer 回報成功 ≠ 狀態面真的變了）本輪未修。
3. **`--cleanup` 非預設**；不帶旗標的 release 會造出 `illegal_terminal_before_cleanup`。

### escalation 狀態

同日 checkpoint（`issuecomment-5262404015`）依 §4 判 `escalate`（家族 `closeout-executor-not-wired-to-real-destructive-paths` 跨三個 unique attempt），需求方裁定維持同執行者（`issuecomment-5262430465`）。**本輪 findings 為 0，該家族未出現第四次。**

「escalate 之後維持同執行者」在契約裡今天仍無事件表示法（#39 設計中、未合併），故該裁定與本 sign-off 皆為散文留痕。#39 落地後應補寫為正式的 `escalation-resolution` 事件。

## Comment 5264536517 · 2026-08-12T08:53:50Z

## deployment-state

- event: deployment-status-change
- card_id: WF-CLEANUP-GUARD1
- actor: ruan6047
- owner: ruan6047
- occurred_at: 2026-08-12T16:53:48+08:00
- transition: ⏸未部署 → 🚀待部署
- project_status: Todo
- evidence: 交付 4353c18 已由 PR #27 併入 main（5d22a7f），跨家族查核 APPROVE、findings 0、需求方已給 T4 sign-off（issuecomment-5262731441）。本卡為 wfcli CLI 變更，無伺服器部署面。


## Comment 5264539279 · 2026-08-12T08:54:06Z

## deployment-state

- event: deployment-status-change
- card_id: WF-CLEANUP-GUARD1
- actor: ruan6047
- owner: ruan6047
- occurred_at: 2026-08-12T16:54:04+08:00
- transition: 🚀待部署 → ⏳部署中
- project_status: In Progress
- evidence: 本狀態對本卡為空轉。wfcli 是使用者自 repo 本機執行的 CLI，沒有建置、發佈、推送或重啟任何一步——「部署中」在此無對應的實際動作。如實記錄為空而非虛構一個步驟。


## Comment 5264541745 · 2026-08-12T08:54:21Z

## deployment-state

- event: deployment-status-change
- card_id: WF-CLEANUP-GUARD1
- actor: ruan6047
- owner: ruan6047
- occurred_at: 2026-08-12T16:54:19+08:00
- transition: ⏳部署中 → ✅已部署
- project_status: In Progress
- evidence: 對本機執行的 CLI 而言，「已部署」的實質定義是：交付已在 main 上，使用者自 main 執行即取得該能力。已驗證 git merge-base --is-ancestor 4353c1863f8b83e5532585dbcdcdb25e876098a2 origin/main 成立（origin/main = 02b5d9a）。


## Comment 5264544364 · 2026-08-12T08:54:36Z

## deployment-state

- event: deployment-status-change
- card_id: WF-CLEANUP-GUARD1
- actor: ruan6047
- owner: ruan6047
- occurred_at: 2026-08-12T16:54:34+08:00
- transition: ✅已部署 → 🧪驗證中
- project_status: In Progress
- evidence: 以 git archive origin/main 解出乾淨樹，實跑三項驗證本卡交付的能力確實在 main 上生效而非只是檔案存在。


## Comment 5264547544 · 2026-08-12T08:54:50Z

## deployment-state

- event: deployment-status-change
- card_id: WF-CLEANUP-GUARD1
- actor: ruan6047
- owner: ruan6047
- occurred_at: 2026-08-12T16:54:49+08:00
- transition: 🧪驗證中 → ✅已驗證
- project_status: Done
- evidence: 自 origin/main（02b5d9a）的乾淨樹實跑三項全部通過：(1) wfcli handoff --help 列出 --cleanup 旗標並帶正確說明（僅 --next-stage release：連同執行守衛化的收尾清理）；(2) cleanup.py 內 execute_closeout_transition 與 _execute_closeout 兩個函式定義皆存在，即 R4-002 修法的貼標籤層／破壞性本體分離結構已在 main 上；(3) 被 R4-002 打穿又修好的守衛測試在 main 上通過——pytest -k "destructive_body_cannot_name or swapping_the_trigger" 得 3 passed。

main 全套於同時點實測 658 passed 0 errors（#47 修復 main 紅燈後）。

⚠️ 誠實邊界：本驗證證明的是「交付的能力在 main 上存在且其守衛測試通過」，不是「不可逆刪除路徑已對真實 Project 與 Issue 執行過」。後者從未發生，需求方的 T4 sign-off 已明確知悉並接受該界線（issuecomment-5262731441）。已實跑的是拋棄式臨時 repo 與兩張拋棄式智慧卡（#28、#33）。

⚠️ 本卡的部署鏈中「⏳部署中」為空轉，如實記錄——wfcli 是本機執行的 CLI，無建置／發佈／重啟步驟。需求方 2026-08-12 已表示認同本卡實質上不需部署、合併即足夠，該流程問題另行討論。


## Comment 5265955378 · 2026-08-12T11:16:03Z

## 守衛的第一次真實生產使用：它擋下了協調者的順序錯誤

供 T4 sign-off 的證據。**這不是拋棄式卡（#28／#33），是一張真實已合併的卡走完整條收尾路徑。**

### 發生的事

`DEV-CLI-VERB-REGISTRY1`（#53）查核 APPROVE 後，PM 建 PR #59 合併進 main。**PM 在 PR body 裡寫了 `Closes #53`**——合併時 GitHub 自動關閉了該 Issue。

然後 PM 執行 `wfcli handoff … --next-stage release --cleanup`，得到：

```
[handoff] 收尾轉換（DEV-CLI-VERB-REGISTRY1）：mode=detect_only／狀態=illegal_terminal_before_cleanup（合法=False）
  - 阻擋：[illegal_state] 狀態面已寫終態／已關 Issue，但第 1–3 步尚未完成；這是非法組合，須人工判斷，守衛不代為修復
[handoff] 拒絕 release：收尾未完成（mode=detect_only），狀態面未寫入；請處理上列阻擋原因後重跑
```

**成因逐條可查**：`effect_started = terminal_status_written or not issue_open`（`cleanup.py:803-804`）。#53 的交付狀態當時是 `✅通過`（**不在** `TERMINAL_STATUSES = {"🏁完成", "🛑已停止"}` 內），所以觸發項是 `issue_open` 為 False——GitHub 於 `2026-08-12T10:52:57Z` 因 PR 關鍵字關閉了它。`classify_state` 因此走 `not cleanup_done and effect_started` → `illegal_terminal_before_cleanup`。

**守衛沒有代為修復，也沒有寫任何狀態面**（`mode=detect_only`，卡停在原本的交付狀態）。PM 手動 reopen Issue 還原至 `cleanup_in_progress` 後重跑：

```
[handoff] 收尾轉換（DEV-CLI-VERB-REGISTRY1）：mode=applied／狀態=completed（合法=True）
  - 已執行：remove_worktree, delete_local_branch, delete_remote_branch
[handoff] 已交接 DEV-CLI-VERB-REGISTRY1 → …（狀態=🏁完成，SHA=e1b33d8…）
```

### 這證明了什麼、沒證明什麼

**證明了**：(1) 非法態偵測在真實 GitHub 狀態上會觸發，不只在 fixture 上；(2) 觸發時**狀態面零寫入**，卡可重跑續作，不需要任何人工修復狀態面；(3) 前提齊備後三個破壞性動作實際執行、第 4 步在其後落地、終態最後寫入。

**沒證明**：條件式刪除的租約路徑本輪未再獨立取證（PM 先前於 `bc099f6` 以 `GIT_TRACE_PACKET` 捕過 old-oid）；本次遠端分支刪除的線路封包未再抓一次。

### 一個非預期的、值得單獨記的點

**PM 的 PR body 慣例（`Closes #N`）本身就是一條繞過收尾順序的路徑**，而它不經 `wfcli`、不經任何守衛。守衛擋住了後果，但**沒有東西擋住那個成因**——下一個人寫 `Closes #N` 還是會製造同一個非法態，只是會在 `--cleanup` 那一刻才被發現。

這對本卡是加分還是缺口，PM 不自行裁定：可以說「守衛的價值正在於它在唯一會造成不可逆後果的那一刻攔下」，也可以說「§9 該多一項，把狀態面的旁路寫入路徑列進已知限制」。**請查核者或需求方裁示。**

