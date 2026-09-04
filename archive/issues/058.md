# #58 WF-EVENT-TYPE-REGISTRY-RECONCILE1 同一個事件型別語彙在兩個檔各自封閉演化，且互不知情
- state: open  created: 2026-08-12T09:55:41Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/58
- comments: 12

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code PM
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；須先裁定孰為權威與管轄邊界（CLI 動詞算不算事件型別、部署事件受不受該 envelope 管），才談得上對帳；那是規格判斷不是機械比對，推理鏈中等偏長。）　查核：待指派（建議 主力型；紅線：本卡要裁定兩份封閉語彙的權威關係，錯了會讓兩邊繼續各自演化；須跨家族。）
- Initiative：—　spec 基線：WF-CONTROL-PLANE-TYPE-REGISTRY1（#42）於 b8a4a16 的 R2 交付中發現並登記為已知分歧、明確不裁定（逸出其寫入集）。PM 已獨立複驗兩份語彙的內容與差集屬實。
- DB：db_scope=none
- 服務的原始目標：讓「一個事件型別叫什麼、受誰管轄」在整個 repo 只有一個答案

## 簡介
<!-- card-brief:begin -->
裁定同一套事件型別語彙在 templates/control-plane-contract.md §2（18 項）與 docs/WF_EVENT_MARKER_V2.md 的 EVENTS dict（7 項）兩份各自封閉演化的管轄關係——孰為權威、CLI 動詞算不算事件型別、部署事件受不受 §2 envelope 管——並設計雙向差集閘門的形狀與「什麼算一次型別宣告」的成文判準。**適用時機**：新增或改名事件型別而不知以哪一份為準時；或遇上「逐卡驗證通過不蘊含合起來仍成立」這類由合併製造的不一致時。⛔ 非射程：刻意不含消除既存差集與建立對帳閘門的實作，該實作歸 WF-CONTROL-PLANE-TYPE-REGISTRY1（aiwf#42）且本卡結案不解除其義務；不得單方面修改任一份語彙。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：同一個事件型別語彙在兩個檔各自封閉演化且互不知情，而今天沒有任何地方裁定過它們的管轄關係——誰管語意、誰管表示、跨層同名時以誰為準、什麼算一次型別宣告，全都沒有答案。本卡的射程是把那個答案定下來並使其可審；【刻意不含】消除既存差集與建立對帳閘門的實作——那需要改 templates/control-plane-contract.md，該檔由 WF-CONTROL-PLANE-TYPE-REGISTRY1（#42）持有，且 #42 未閉合的 blocking finding（event-type-registry-incomplete）要求的正是同一件事。需求方 2026-08-12 裁定該實作歸 #42 承接，本卡結案不解除該義務。

（1）`templates/control-plane-contract.md` §2 的 type 列舉，18 項（#42 於 b8a4a16 補登後）。
（2）`docs/WF_EVENT_MARKER_V2.md` 的 `EVENTS` dict，7 項——`review`／`handoff`／`assign`／`amend`／`deployment-declaration`／`deployment-status-change`／`review-marker-clearance`，該檔並明寫「事件型別由 event= 鍵承擔」。

差集：**只在 (2) 有的**是 `assign`、`amend`、`deployment-declaration`、`deployment-status-change`；兩者皆有的只有 `review`、`handoff`、`review-marker-clearance`——**後者是兩份獨立收斂到同名，是個好訊號但也證明沒有任何機制在協調它們**。

**這個不一致是合併製造出來的，不是任何一張卡的缺陷。** #35（marker v2）與 #42（type 登記）各自通過跨家族查核、各自的封閉語彙都自洽；合併後產生新的不一致，而**沒有任何機械檢查會發現，因為兩邊都封閉且 fail-closed，只是封閉在不同的集合上**。#42 的執行者的原話：「病灶不只是漏登，是同一個語彙在兩個檔各自封閉演化，且互不知情。」

今天已有兩次同型的教訓：合併三張卡導致 main 轉紅（各自綠、合起來紅）、以及本件。共同形狀是**逐卡驗證通過不蘊含合起來仍成立**。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:docs/WF_EVENT_TYPE_REGISTRY_RECONCILE1.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 先裁定三個規格問題，它們決定對帳的形狀而非只是細節：(1) 兩份孰為權威，或兩者管轄不同層而各自為權威；(2) CLI 動詞（assign／amend）算不算事件型別；(3) 部署事件（deployment-declaration／deployment-status-change）受不受 control-plane §2 的 envelope 管轄——#42 已指出 §2 的**管轄邊界本身沒有寫在任何地方**，今天靠讀者比對欄位集自行推斷。
- [ ] 依裁定結果設計雙向差集閘門的形狀（實作不在本卡寫入集，本卡只出設計與裁定）。須說明閘門讀哪兩個來源、差集非空時的行為、以及「什麼算型別宣告」的成文判準——後者 #42 兩輪用的都是人讀出來的，是這個對帳最弱的一環。
- [ ] ⚠️ 本卡不得單方面修改任一份語彙。兩份分別由 templates/control-plane-contract.md 與 docs/WF_EVENT_MARKER_V2.md 承載，前者現由 #42 持有；本卡只出裁定與設計，實作與修改由後續卡依裁定執行。若你認為某一份必須立即改，指名並說明為什麼不能等。
- [ ] 須指名今天沒有任何機制在協調兩份語彙這件事的執行者是誰。若答案是「沒有」，就寫成約定並判斷該不該有；該判斷若逸出寫入集，明列為衍生卡。

## 驗證

- [ ] 兩份語彙的內容與差集須由指令輸出產生，不得人工清點。PM 已驗過一次，請自己重跑。
- [ ] 三個規格裁定各附論證與可稽核依據；「兩者管轄不同層」若為結論，須說明層界在哪、以及跨層同名時誰說了算。
- [ ] 凡寫下「會擋下／必須一致」須指出執行者所在的檔與行；沒有機械執行者的寫成約定。本 repo 反覆被 claim-exceeds-evidence 打過。
## Log

- 2026-08-12T17:55:40+08:00 open by Claude Opus 5@Claude Code PM；owner 待指派；iteration 0。
- 2026-08-12T18:00:38+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code 子agent；分支worktree claude/WF-EVENT-TYPE-REGISTRY-RECONCILE1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-type-registry-reconcile1；交付狀態 🚧進行中；實際能力層級 主力型（與卡面建議 主力型 相符）。
- 2026-08-12T18:25:26+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA 0b30a823678ae043c61728ba5a7bf3c31d96adaf；證據 R1：單檔新增 683 行，零逸出。marker 前綴新增 **0 處**（必須逐字引用原始碼的三處以代號代入，代入內容不影響該處要證明的事）。

⚠️ **卡面兩項前提經執行者重跑後不成立，PM 已複驗並發前向更正（issuecomment-5265418916），錯在 PM**：(1)「main 上 18 項」——b8a4a16 **不是 origin/main 祖先**，只在 #42 分支上而 #42 仍待查核；main 是 15 項（執行者算 14，差在行首 token 計法，關鍵事實一致）。故今天的交集只有 review／handoff **兩項**，卡面寫的三項是 #42 併入後的狀態。**執行者對 S1（今天 main）與 S2（#42 併入後）兩態各算一次差集**並裁定對兩態都成立。(2)「兩份封閉語彙」——control-plane 全檔「封閉」**0 次**且 :32 明文「專案可擴充 event type」，marker v2 則 10 次且確實封閉；**病灶因此是「一份開放基準與一份封閉登記之間沒有包含關係檢查」**，這**直接決定閘門必須雙向不對稱**（卡面框架會導出對稱閘門、那是錯的）。

**它另找到卡面與 #42 兩輪都沒提到的第三個宣告面**：§2 telemetry 行宣告 resource-acquired／resource-released 走同一 envelope，**但兩者在 type: 行出現 0 次**（PM 已複驗）——任何把「§2 列舉」等同「type: 那一行」的抽取器都看不見它們。

三個裁定：(1) **不設單一權威，兩者分屬兩層**——L1＝邏輯事件模型（control-plane §2 是**範本**，經 ADOPTION 實例化；**本 repo 自己沒有 docs/CONTROL_PLANE_CONTRACT.md，故它從未管轄過本 repo 任何具體事件**），L2＝單一傳輸的線上格式；**層界＝是否以留言 marker 承載識別符**（可判定，#35 §2.3 已逐動詞裁過）；跨層同名時 L1 管語意與狀態轉移、L2 管表示與鍵集合；導出唯一硬約束 **L2 ⊆ L1**，反向不要求。(2) **CLI 動詞不是事件型別**——動詞是寫入動作、型別是被寫下的事實；提議 assign→claim、amend→correction，**明確標示為推論不是引用**（無任何檔案宣告、wfcli 不寫 type= 欄位、無執行期證據可證偽）。(3) **部署事件受 §2 管轄但屬第三類**——決定性論證是 release 是 L1 型別而 canonical §0 規定「需部署卡在部署已驗證前不得 release」，**若部署事件在 §2 之外，L1 型別的合法性會依賴 L1 看不見的東西**；並回答 #42 的疑問：**§2 管轄邊界之所以沒成文，是因為它從未被決定過**。

閘門設計的核心一步：「什麼算型別宣告」的判準**不是文字啟發式，是位置**——把「窮舉型別」（對自由文字證否、不可證明）換成「**窮舉宣告面**」（6 列、可審）；#42 那條掃描規則**降級為候選提名器**——「啟發式負責發現、登記表負責判斷；今天這兩件事混在一起，於是一個不完整的掃描被當成了完整性論證」。另兩項：差集**雙向不對稱**；**抽取器須對零產出 fail-closed**——它親身踩到（zsh 下 :t 修飾符把抽取吃成 0 筆，**而 comm 照樣印出看起來乾淨的結果**）。

協調機制的執行者是**空集合不是弱執行者**（兩份語彙 cli/+scripts/ 皆零命中、無 .github/、doctor.py 完全沒有事件型別列舉）。**實況比卡面更歪：是三份**——第三份是 doctor.py 隱含的基數 1 語彙 {review}，**而它是唯一今天真的在跑的那份**。裁定**該有但現在不該建**：L2 尚未生效（handoff-contract §3.1.7 明文 v2 未實作、唯一登記消費者只讀 v1、doctor 對 v2 一律停機），今天 0 寫入端 0 讀取端、分歧不可能造成錯誤裁決；**觸發點是 v2 讀取器落地那一刻**，故裁定閘門與 v2 讀取器**同批落地**。是否有哪一份必須立即改：**沒有**——必須立刻做的不是編輯是排程。

執行者自陳 6 條全標約定，第 6 條最重要：「本輪差集已窮舉」只對兩個具名來源成立；它確實找到第三個宣告面也排除了一個候選，**但不能證明找完了**——「**我沒有解決 #42 那個沒有證明覆蓋完整的問題，我把它搬到一個更小的物件上**——可審不等於已證明，把本檔判準當成完整性證明就是本 repo 反覆被打的那個形狀」。。
- 2026-08-12T19:26:07+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5265977021，PM 回讀重算 89ffcd5f… 相符、created_at=updated_at、marker 字面 0）；core_pain_resolved no；self_run 3 項；findings 1 項（blocking 1）；attempt WF-EVENT-TYPE-REGISTRY-RECONCILE1-e0-0b30a823678ae043c61728ba5a7bf3c31d96adaf。
- 2026-08-12T19:45:00+08:00 amend by wf-cli（op 97d7306f）→ 核心痛點：原值「main 上現在有**兩份封閉的事件型別語彙**，各自 fail-closed，且互不知情：」→ 新值「同一個事件型別語彙在兩個檔各自封閉演化且互不知情，而今天沒有任何地方裁定過它們的管轄關係——誰管語意、誰管表示、跨層同名時以誰為準、什麼算一次型別宣告，全都沒有答案。本卡的射程是把那個答案定下來並使其可審；【刻意不含】消除既存差集與建立對帳閘門的實作——那需要改 templates/control-plane-contract.md，該檔由 WF-CONTROL-PLANE-TYPE-REGISTRY1（#42）持有，且 #42 未閉合的 blocking finding（event-type-registry-incomplete）要求的正是同一件事。需求方 2026-08-12 裁定該實作歸 #42 承接，本卡結案不解除該義務。」；理由 R1-01（blocking，attribution=planner）判定本卡的純裁定寫入集與「全 repo 只有一個答案」的核心痛點脫節；查核者給的兩條路中，需求方裁定走「縮小射程」而非「擴充寫入集」。理由是 templates/control-plane-contract.md 由 #42 持有且 #42 自己的未閉合 blocking 要求同一件事，搬檔案只會作廢 #42 兩輪查核成果、再由本卡重做本卡執行者已做出的裁定。裁定留言由 PM 代擬代貼、需求方明確核准，該事實已逐字寫在留言內——因為 amend 的 author 檢查對 PM 恆真（PM 的 gh 即以 ruan6047 認證），機械上分不出誰寫的。；授權 依需求方 ruan6047 於 https://github.com/ruan6047/ai-workflow/issues/58#issuecomment-5266365564 的裁定（GitHub comment author 已逐字核對，非留言內文自述）。
- 2026-08-12T19:46:41+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 1；SHA 0b30a823678ae043c61728ba5a7bf3c31d96adaf；證據 R1-01（major, blocking, governance, attribution=planner, root_cause_id=event-type-registry-incomplete）：純裁定寫入集與「全 repo 只有一個答案」的核心痛點脫節。需求方裁定走縮小射程（issuecomment-5266365564），核心痛點已 amend（op 97d7306f），消除差集與對帳閘門改由 #42 承接並已寫進 #42 驗收（op fe3c4db4）。執行者本輪須使文件與縮小後的射程一致，並明確標示承接關係。。
- 2026-08-12T20:07:02+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 1；SHA 42cfb387985ec335a57ed35217c580964f38dbb9；證據 R2：R1-01（attribution=planner）已由需求方裁定縮小射程處置，卡面核心痛點已 amend（op 97d7306f）。執行者新增 §0.1 射程裁定，把承接寫成三列指名對照表逐項對到 #42 卡面的具體驗收條（四項裁定→第4條、消除差集+可重跑閘門+零產出 fail-closed→第5條、telemetry 宣告面→第1條），非散文「後續由衍生卡處理」。§5.3／§9／§1.4 的既存事實一字未刪只改歸屬（刪掉 #42 就失去要處理的對象）。§8 由「四張衍生卡」改為承接指派、未開卡，並指名兩處 #42 現行單檔資源宣告涵蓋不到的殘餘。撤回一句變成過度宣稱的話（§7 原寫「#42 不需要因本卡而改」）。§6.2 排程裁定拆上界/下界，下界被需求方排程覆寫，執行者明說不反對並指名提早落地的新風險。PM 自審：遠端 tip 相符、0b30a82 是祖先（非 force）、對 main merge-tree CLEAN、寫入集單檔零逸出、兩個 commit trailer 皆齊（Requested-by/Planned-by/Implemented-by，未加 Reviewed-by）。⚠️ 執行者自陳五項證明不了的事，第 1 與第 3 最該看：(1) §0.1 承接對照表是它對 #42 卡面文字的解讀不是機械綁定，#42 再 amend 一次對照表會無聲失效——與 #42 自己 R1-002 被打的形狀同構，它指名了沒解決；(3) 新指名的漏洞：#42 第5條只要求消除差集未指定路徑，若用別的方式湊出空差集則差集歸零而 §4.3 不落地、閘門看不出差別。並附一筆新實測反證：PR #59 的 COMMAND_MODULES 在它跑窮舉時已存在於另一分支（a7e5e21 @17:58）不在 main 也不在其基線、18:52 才併入，判它不是型別宣告面是事後判的；據此把「宣告面已窮舉」降為時間點上的下界，§5.2 判準重述為維持義務而非一次性窮舉。⚠️ 它另對 PM 代擬代貼裁定留言一事作出判斷（PM 要它判），指出 amend 事件的授權欄與理由欄互相矛盾且只有散文那半是對的——PM 查證後確認該句來自 amend_cmd.py:507 的常數字面、對 PM 恆真，已發前向更正 issuecomment-5266565670（attribution=coordinator）並開卡 #62 承接。。
- 2026-08-12T20:52:09+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼）；⚠️ 本卡收到三則收據 5266916658／5266923195／5266932326，PM 逐一驗算三者雜湊皆自洽；第一與第三份內容逐位元組相同（7406a2c6…），中間一份僅因取材規則那行漏進被雜湊區而異，裁決三份一致；轉錄採 5266932326。PM 的轉錄調整：截去 YAML 區塊後的「查核結論／前輪閉環／範圍外」三段散文，該三段完整保存於收據雜湊範圍內，區塊內字串逐字未變；core_pain_resolved no；self_run 3 項；findings 1 項（blocking 1）；attempt WF-EVENT-TYPE-REGISTRY-RECONCILE1-e0-42cfb387985ec335a57ed35217c580964f38dbb9。
- 2026-08-12T23:12:46+08:00 handoff by wf-cli → owner 待指派；iteration 2；SHA ba4755f4f2e33436d8128a9d68498250540f0cbb；證據 依 docs/ROADMAP.md（main ba4755f）§0／§3 降級：本卡屬目標 3（治理精緻化）。#58 解決的「兩份事件型別語彙互不知情」今天 0 寫入端 0 讀取端、不可能造成錯誤裁決（其執行者自己的論證）；#39 的授權款依 §1 收斂——身分只需角色＋模型的宣告欄位，不追求驗證，故其 authorization_binding 的 substantive/structurally-vacuous 設計為過度工程。⚠️ 降級不是關閉，載有的真實 finding 紀錄全數保留、可逆。⚠️ 未閉合的 blocking 維持未閉合，本次降級不視為驗收。。
- 2026-08-26T22:14:15+08:00 amend by wf-cli（op 80f0e16a）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:e3b422cd4c1b9b39f06da37e8815ad3c30aea0a1c5f8a5c902c50bee4d6d5557 (762 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。
- 2026-08-29T14:58:50+08:00 handoff by wf-cli → owner 待指派；iteration 2；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 阻塞登記（來源狀態 📥Backlog）：https://github.com/ruan6047/ai-workflow/issues/58 之阻塞留言。解除條件＝待審清單機制上線。。


## Comment 5265418916 · 2026-08-12T10:20:39Z

## PM 更正：卡面兩項前提不成立，執行者的糾正正確

執行者於 `0b30a82` 交回時指出本卡卡面兩項前提經重跑後不成立。**PM 已逐一複驗，兩項都成立——錯的是卡面。**

### 一、「main 上 18 項」——我把未合併分支的狀態當成了 main

實測 `git merge-base --is-ancestor b8a4a16 origin/main` → **否**。`b8a4a16` 只在 `claude/WF-CONTROL-PLANE-TYPE-REGISTRY1` 上，而 **#42 仍 🔍待查核**。`origin/main` 的 `type:` 列舉是 **15 項**（PM 算法；執行者算 14，差在行首 token 的計法，**「不是 18、不在 main」這個關鍵事實兩者一致**）。

**後果是實質的**：今天的交集只有 `review`／`handoff` **兩項**，卡面寫的三項（含 `review-marker-clearance`）是 **#42 併入後**的狀態。執行者因此對 **S1（今天 main）與 S2（#42 併入後）兩態各算一次差集**，並裁定對兩態都成立——那是比卡面更嚴謹的處理。

**這正是 PM 警告過所有執行者的形狀**（用未合併分支的內容做斷言），而 PM 自己犯了。`attribution: planner`。

### 二、「兩份封閉語彙」——只有一份是封閉的

實測：`templates/control-plane-contract.md` 全檔「封閉」出現 **0 次**，且 `:32` 明文寫「**專案可擴充 event type**，但必須文件化狀態轉移」。`docs/WF_EVENT_MARKER_V2.md` 出現 **10 次**且確實封閉。

`control-plane` 的 fail-closed 是**對未知型別的處置規則**，不是封閉語彙。

**執行者的重新診斷比卡面準**：

> 病灶不是「兩份封閉語彙衝突」，是「**一份開放基準與一份封閉登記之間沒有包含關係檢查**」。

**而這直接決定閘門的形狀**：必須**雙向不對稱**——`L2\L1` 阻擋，`L1\L2` 不阻擋但每項須帶明示的「無 marker」宣告。卡面原本的框架會導出一個對稱閘門，**那是錯的**。

### 三、它另找到卡面與 #42 兩輪都沒提到的第三個宣告面

`control-plane-contract.md:35` 的 telemetry 行宣告 `resource-acquired | resource-released` 走「同一 envelope」，**但兩者在 `type:` 行的出現次數皆為 0**（PM 已複驗）。**任何把「§2 列舉」等同「`type:` 那一行」的抽取器都看不見它們**——包括 #42 用的那一條，也包括 PM 在卡面預設的那一條。

### 不追溯改寫

本則為前向更正，卡面欄位不 `amend`（執行者已對兩態各算一次，交付物本身不依賴卡面的錯誤前提）。**不追溯改寫任何裁決或事件留痕。**

## Comment 5265863440 · 2026-08-12T11:06:26Z

## 派審：#58 `WF-EVENT-TYPE-REGISTRY-RECONCILE1` R1

⚠️ 審核對象 **`ruan6047/ai-workflow#58`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-type-registry-reconcile1
分支：claude/WF-EVENT-TYPE-REGISTRY-RECONCILE1　　被審 SHA：0b30a823678ae043c61728ba5a7bf3c31d96adaf
基線：e8a638c40f1028b6b85f6c59fd12ee9c1e85582d（PM 已重算並驗為祖先）　　iteration：0（首輪）
寫入集：docs/WF_EVENT_TYPE_REGISTRY_RECONCILE1.md 單檔（新增 683 行）
```

> **權威來源**：本則派審詞與本 Issue Log 最後一筆 `handoff` 事件的 `SHA` **必須一致**。**若你發現兩者不符，以 handoff 事件為準並回報該不符**——PM 本日在 #9 與 #38 上各犯過一次「做了 handoff 卻沒補發派審詞」，其中一位查核者因此審了舊產物，另一位正確拒審。

`origin/main` 現為 **`e1b33d8`**（#53 已於本日合併）。單檔文件、與 #53 零重疊、`merge-tree` 無衝突、合併結果 pytest **701 passed**（PM 實測）。marker 前綴新增 **0 處**——必須逐字引用原始碼的三處以代號代入，代入內容不影響該處要證明的事。

### ⚠️ 卡面兩項前提不成立，錯在 PM，前向更正見 `issuecomment-5265418916`

**這兩項都由執行者重跑後推翻，PM 已複驗屬實。查核時請以更正後的版本為準，不要以卡面原文為準。**

**(1)「main 上 18 項」是錯的。** `b8a4a16` **不是 `origin/main` 祖先**——它只在 #42 分支上而 #42 仍待查核。main 是 15 項（執行者算 14，差在行首 token 計法，關鍵事實一致）。故**今天的交集只有 `review`／`handoff` 兩項**，卡面寫的三項是 #42 併入後的狀態。執行者對 **S1（今天 main）與 S2（#42 併入後）兩態各算一次差集**並裁定對兩態都成立。

**(2)「兩份封閉語彙」是錯的。** control-plane 全檔「封閉」**0 次**，且 `:32` 明文「專案可擴充 event type」；marker v2 則出現 10 次且確實封閉。**病灶因此不是「兩份封閉語彙互不知情」，而是「一份開放基準與一份封閉登記之間沒有包含關係檢查」**——而這**直接決定閘門必須雙向不對稱**。卡面的框架會導出對稱閘門，**那是錯的**。

**請判斷**：執行者依據被推翻的卡面前提重寫了問題陳述，這個重寫是否正當、以及重寫後的問題是不是還是同一張卡該解的問題。

### 一、它另找到卡面與 #42 兩輪都沒提到的第三個宣告面

§2 telemetry 行宣告 `resource-acquired`／`resource-released` 走同一 envelope，**但兩者在 `type:` 那一行出現 0 次**（PM 已複驗）。**任何把「§2 列舉」等同「`type:` 那一行」的抽取器都看不見它們。**

### 二、三個裁定，請逐一攻擊

**(a) 不設單一權威，兩者分屬兩層。** L1＝邏輯事件模型（control-plane §2 是**範本**，經 ADOPTION 實例化；**本 repo 自己沒有 `docs/CONTROL_PLANE_CONTRACT.md`，故它從未管轄過本 repo 任何具體事件**），L2＝單一傳輸的線上格式。**層界＝是否以留言 marker 承載識別符**（可判定，#35 §2.3 已逐動詞裁過）。跨層同名時 L1 管語意與狀態轉移、L2 管表示與鍵集合；導出唯一硬約束 **L2 ⊆ L1**，反向不要求。

**(b) CLI 動詞不是事件型別**——動詞是寫入動作、型別是被寫下的事實。提議 `assign`→`claim`、`amend`→`correction`，並**明確標示為推論不是引用**（無任何檔案宣告、`wfcli` 不寫 `type=` 欄位、無執行期證據可證偽）。

**(c) 部署事件受 §2 管轄但屬第三類。** 決定性論證：`release` 是 L1 型別，而 canonical §0 規定「需部署卡在部署已驗證前不得 release」；**若部署事件在 §2 之外，L1 型別的合法性會依賴 L1 看不見的東西**。並回答 #42 的疑問：**§2 管轄邊界之所以沒成文，是因為它從未被決定過。**

### 三、閘門設計的核心一步，這是本卡最該被打的地方

「什麼算型別宣告」的判準**不是文字啟發式，是位置**——把「窮舉型別」（對自由文字證否、不可證明）換成「**窮舉宣告面**」（6 列、可審）。#42 那條掃描規則因此**降級為候選提名器**：「啟發式負責發現、登記表負責判斷；今天這兩件事混在一起，於是一個不完整的掃描被當成了完整性論證。」

另兩項：差集**雙向不對稱**；**抽取器須對零產出 fail-closed**——執行者親身踩到（zsh 下 `:t` 修飾符把抽取吃成 0 筆，**而 `comm` 照樣印出看起來乾淨的結果**）。

**執行者自己把第 6 條自陳寫成最重要的一條，請正面裁決它**：

> 「本輪差集已窮舉」只對兩個具名來源成立；它確實找到第三個宣告面也排除了一個候選，**但不能證明找完了**——「**我沒有解決 #42 那個沒有證明覆蓋完整的問題，我把它搬到一個更小的物件上**——可審不等於已證明，把本檔判準當成完整性證明就是本 repo 反覆被打的那個形狀。」

**這是本輪的判準核心：把不可證明的完整性換成可審的窮舉面，算不算關閉核心痛點？** 兩個方向都正當，但請正面裁示，不要迴避。

### 四、協調機制的執行者是空集合不是弱執行者

兩份語彙在 `cli/`＋`scripts/` 皆零命中、無 `.github/`、`doctor.py` 完全沒有事件型別列舉。**實況比卡面更歪：是三份**——第三份是 `doctor.py` 隱含的基數 1 語彙 `{review}`，**而它是唯一今天真的在跑的那份**。

裁定**該有但現在不該建**：L2 尚未生效（handoff-contract §3.1.7 明文 v2 未實作、唯一登記消費者只讀 v1、`doctor` 對 v2 一律停機），今天 0 寫入端 0 讀取端、分歧不可能造成錯誤裁決；**觸發點是 v2 讀取器落地那一刻**，故裁定閘門與 v2 讀取器**同批落地**。是否有哪一份必須立即改：**沒有**——「必須立刻做的不是編輯是排程」。

**請攻擊這個延後**：把閘門綁在一個尚未排程的落地事件上，與「開了卡但沒人做」的差別是什麼？有沒有機械執行者保證它們真的同批？

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5265977021 · 2026-08-12T11:18:23Z

<!-- wf-review-receipt:v1
card_id: WF-EVENT-TYPE-REGISTRY-RECONCILE1
source_sha: 0b30a823678ae043c61728ba5a7bf3c31d96adaf
report_sha256: 89ffcd5f5d8d37f930d14b5ade3c96b0aa6ad5dec66fa47bd6af76d15b928e2f
-->
取材規則：雜湊取材自本規則之後的下一個「## 查核報告」起，至報告全文 EOF 止；UTF-8 編碼、LF 換行、不做 strip；排除上方 HTML 收據與本取材規則行。

## 查核報告

權威 source SHA：`0b30a823678ae043c61728ba5a7bf3c31d96adaf`。

```yaml
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C .claude/worktrees/wf-event-type-registry-reconcile1 rev-parse HEAD; git -C .claude/worktrees/wf-event-type-registry-reconcile1 status --porcelain; git -C .claude/worktrees/wf-event-type-registry-reconcile1 merge-base --is-ancestor e8a638c40f1028b6b85f6c59fd12ee9c1e85582d HEAD"
    observed: "HEAD 為 0b30a823678ae043c61728ba5a7bf3c31d96adaf，工作區乾淨，基線祖先檢查成功。"
  - command: "以 git show 加 bash 抽取 e8a638c 與 b8a4a16 的 L1，並抽取 e8a638c 的 L2 後執行 comm -13"
    observed: "S1 L1/L2 為 14/7，L2 減 L1 為 5 項；S2 L1/L2 為 18/7，L2 減 L1 仍為 4 項。"
  - command: "git diff --check e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 0b30a823678ae043c61728ba5a7bf3c31d96adaf; git merge-tree e1b33d8984425901de400afeb227d5df67d07212 0b30a823678ae043c61728ba5a7bf3c31d96adaf | grep -E markers | wc -l"
    observed: "diff check 無輸出；對目前 main 的 merge-tree 衝突標記數為 0。"
findings:
  - finding_id: "WF-EVENT-TYPE-REGISTRY-RECONCILE1-R1-01"
    severity: major
    blocking: true
    finding_class: governance
    attribution: planner
    root_cause_id: "event-type-registry-incomplete"
    evidence: "Issue 核心痛點要求全 repo 對型別名稱與管轄只有一個答案；文件第 5.3 節與第 9 節卻明載 L2 減 L1 今日仍為 5 項，且 L2 subset L1、宣告面登記表與閘門皆只是無機械執行者的約定，交由未排程衍生卡。canonical AI_WORKFLOW.md 5.1 規定核心痛點未消時即使驗收清單通過也必須 REQUEST_CHANGES，並歸屬 planner。"
    disposition: "規劃者須先修正卡的核心痛點或寫入集與驗收，使本卡可交付可驗證的閉環；若保留現有核心痛點，需由已授權且已排程的後續交付實際消除 L2 減 L1 並建立可執行的對帳閘門後，再重新派審。"
```

## 查核結論

文件對卡面兩項錯誤前提的前向更正、S1 與 S2 差集重跑、宣告面與零產出 fail-closed 設計，皆有可重現依據；將啟發式降為候選提名器也正確。然而這些裁定沒有讓既存不一致消失：S1 尚有五個、S2 尚有四個 L2 型別未在 L1 登記，且文件明言實作與排程沒有機械執行者。故本卡的純裁定寫入集與「全 repo 只有一個答案」的核心痛點脫節。

## 前輪 accepted blocking finding 閉環

首輪，無前輪 accepted blocking finding。

## 範圍外發現

無。

## Comment 5266092119 · 2026-08-12T11:26:08Z

<!-- wf-review-event:v1 card_id=WF-EVENT-TYPE-REGISTRY-RECONCILE1 source_sha=0b30a823678ae043c61728ba5a7bf3c31d96adaf attempt_id=WF-EVENT-TYPE-REGISTRY-RECONCILE1-e0-0b30a823678ae043c61728ba5a7bf3c31d96adaf -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-EVENT-TYPE-REGISTRY-RECONCILE1`　attempt_id：`WF-EVENT-TYPE-REGISTRY-RECONCILE1-e0-0b30a823678ae043c61728ba5a7bf3c31d96adaf`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5265977021，PM 回讀重算 89ffcd5f… 相符、created_at=updated_at、marker 字面 0）　escalation_epoch：0
- source_sha：`0b30a823678ae043c61728ba5a7bf3c31d96adaf`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T19:26:07+08:00

### self_run（查核者實跑）

- `git -C .../wf-event-type-registry-reconcile1 rev-parse HEAD; status --porcelain; merge-base --is-ancestor e8a638c HEAD`
  - HEAD 為 0b30a823678ae043c61728ba5a7bf3c31d96adaf，工作區乾淨，基線祖先檢查成功。
- `以 git show 加 bash 抽取 e8a638c 與 b8a4a16 的 L1，並抽取 e8a638c 的 L2 後執行 comm -13`
  - S1 L1/L2 為 14/7，L2 減 L1 為 5 項；S2 L1/L2 為 18/7，L2 減 L1 仍為 4 項。
- `git diff --check e8a638c 0b30a82; git merge-tree e1b33d8 0b30a82 並數衝突標記`
  - diff check 無輸出；對目前 main 的 merge-tree 衝突標記數為 0。

### findings（1，其中 blocking 1）

- **WF-EVENT-TYPE-REGISTRY-RECONCILE1-R1-01**　severity=major　blocking=true　class=governance　attribution=planner　root_cause_id=`event-type-registry-incomplete`
  - evidence：Issue 核心痛點要求全 repo 對型別名稱與管轄只有一個答案；文件第 5.3 節與第 9 節卻明載 L2 減 L1 今日仍為 5 項，且 L2 subset L1、宣告面登記表與閘門皆只是無機械執行者的約定，交由未排程衍生卡。canonical AI_WORKFLOW.md 5.1 規定核心痛點未消時即使驗收清單通過也必須 REQUEST_CHANGES，並歸屬 planner。
  - disposition：規劃者須先修正卡的核心痛點或寫入集與驗收，使本卡可交付可驗證的閉環；若保留現有核心痛點，需由已授權且已排程的後續交付實際消除 L2 減 L1 並建立可執行的對帳閘門後，再重新派審。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5266365564 · 2026-08-12T11:44:27Z

## 需求方裁定（2026-08-12）：本卡核心痛點縮為「裁定管轄關係」，不含消除既存差集

> ⚠️ **本則留言的來歷**：內容由需求方 `ruan6047` 明確核准，**文字由 PM（Claude Opus 5@Claude Code）代擬並代貼**。
>
> 記這一句是因為 `wfcli amend --core-pain --ruling-url` 只比對留言的 GitHub comment author，而 PM 的 `gh` 正是以 `ruan6047` 認證——**該 author 檢查對 PM 恆真，機械上分不出誰寫的**。既然驗不出來，就由留言自己說明，而不是讓一個恆真的檢查看起來像有效授權。
>
> 這與本 repo 既有的處理方式一致：`WF-ESCALATION-RESOLUTION-GAP1`（#39）面對同構問題時，拒絕把恆真寫成看似有檢查的條文，改為要求 adapter 導出 `authorization_binding: structurally-vacuous`，把恆真本身寫進事件流。**本則即該形態的一個實例：授權是真的，授權的機械證明是空的。**
>
> 需求方的實際決策留在對話中，本則為其書面化。若日後 `amend` 的授權款取得可逐字比對的獨立身分，本則不因此追溯生效或失效。

### 裁定

本卡核心痛點縮為 **「裁定事件型別語彙的管轄關係」**，**不含消除既存差集**。

### 理由

本卡的寫入集是單一設計文件，而差集要消除必須改 `templates/control-plane-contract.md`——該檔由 `WF-CONTROL-PLANE-TYPE-REGISTRY1`（#42）持有，且 #42 目前為 `↩退回` 的活卡。寫入集互斥使兩張不能同時碰它。

而 #42 自己那條未閉合的 blocking finding（`event-type-registry-incomplete`）逐字要求「**明定兩集合的管轄關係並設可重跑對帳**」——與本卡交付的裁定是同一件事。把檔案搬給本卡，只會讓 #42 兩輪查核的成果作廢，然後由本卡從頭做出本卡執行者**已經做出來的**那份裁定。零增量。

### 承接指派

消除 L2−L1 與建立可重跑對帳閘門**歸 #42**，並將此義務**寫入 #42 的驗收條件**（不是寫在散文裡）。本卡結案不解除該義務。

### 對查核者「已授權且已排程」條件的正面回應

R1-01 明寫縮小射程需要「已授權且已排程的後續交付」，且「僅記錄衍生卡不能使本卡的完整登記目標成立」。本裁定據以主張 #42 滿足該條件，理由有三：它是**開著的活卡**、它**擁有那個檔案**、且它**自己的 blocking finding 尚未閉合**——第三點意味著 #42 想結案就必須做這件事，那不是承諾而是它過不了自己的查核閘門。

**但這不是機械保證，PM 不宣稱它是。** 真正的殘餘風險是：若 #42 長期卡住，S1 的 5 項差集會一直活著而本卡已結案、無人再盯。緩解方式是把義務落在一張**有未閉合 blocking 的開卡**上，而不是落在文件敘述裡。**查核者可以判定這個緩解不足。**


## Comment 5266565670 · 2026-08-12T12:05:05Z

## PM 前向更正：我那則 `amend` 事件的 `授權` 欄陳述了一件它證明不了的事

R2 的執行者指出 `amend` op `97d7306f` 的 `授權` 欄與 `理由` 欄互相矛盾，且只有散文那半是對的。**PM 查證後確認它是對的，而且成因比它說的更硬——那句話是碼裡寫死的。**

`授權` 欄現行內容：

> 依需求方 ruan6047 於 …issuecomment-5266365564 的裁定（**GitHub comment author 已逐字核對，非留言內文自述**）

括號那句來自 `cli/src/wf_cli/commands/amend_cmd.py:507`，是 **f-string 裡的常數字面**，只要 author 檢查通過就無條件輸出。而 PM 的 `gh` 正是以 `ruan6047` 認證——**該檢查對 PM 恆真**。

於是這一欄宣稱的「已逐字核對」在字面上為真（確實比對過），在**語意上卻是誤導**：它讓人以為那個比對具有區辨力，而它一次也沒有區辨過任何東西。

### 為什麼這件事值得單獨記

執行者的兩點批評 PM 全部接受：

1. **自述寫在被質疑真實性的那個 artifact 內部。** 真要偽造授權的人也可以直接省略那段自述。它提高的是誠實度，**加的可驗證性是零**——它是規範不是控制，「擋不住任何實際的濫用，只擋得住不打算濫用的人犯錯」。
2. **只讀結構化欄位的消費者會拿到錯的印象。** 散文（`理由` 欄）說明了恆真性，`授權` 欄沒有。**而這正是本卡整張在治的病：事實活在散文裡，欄位裡的版本是不完整的。**

第 2 點打得最準。PM 把恆真性寫進了留言與 `理由` 欄，卻讓 `授權` 欄繼續輸出那句有區辨力暗示的常數——**等於自己示範了一次「兩份記載各自演化、互不知情」。**

### 處置

- 本則為前向更正，**不追溯改寫** op `97d7306f` 的事件內容（本專案明令禁止）。該 `amend` 的**實質授權是真的**——需求方明確核准，只是其機械證明是空的。
- 執行者建議的修法 PM 採納為開卡方向：讓 `wfcli amend` 在 `--ruling-url` 的 author 等於執行者身分時，**自動導出一個 `authorization_binding: structurally-vacuous` 之類的欄位**，比照 `WF-ESCALATION-RESOLUTION-GAP1`（#39）§5 第 7 款的處置——把恆真性放在機器讀得到的地方，而不是靠每次代貼的人記得寫一段自述。
- **PM 不自行決定該卡的射程**：#39 的處置是「adapter 加蓋、提交面不得含此鍵、含即無效即使值恰好等於導出值」，那是「驗來源不驗值」；`amend` 這裡要驗的是「操作者身分是否等於被引用的授權者身分」，兩者是否同構須由該卡的執行者論證，不由 PM 預設。

`attribution: coordinator`。


## Comment 5266721088 · 2026-08-12T12:20:34Z

## 派審：#58 `WF-EVENT-TYPE-REGISTRY-RECONCILE1` R2

⚠️ 審核對象 **`ruan6047/ai-workflow#58`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-event-type-registry-reconcile1
分支：claude/WF-EVENT-TYPE-REGISTRY-RECONCILE1　　被審 SHA：42cfb387985ec335a57ed35217c580964f38dbb9
基線：e8a638c40f1028b6b85f6c59fd12ee9c1e85582d（PM 已重算並驗為祖先）　　iteration：1
寫入集：docs/WF_EVENT_TYPE_REGISTRY_RECONCILE1.md 單檔
```

> **權威來源**：本則與 Log 最後一筆 `handoff` 的 `SHA` 必須一致；不符時**以 handoff 事件為準並回報**。

**PM 自審**：遠端 tip 相符、`0b30a82` 是祖先（非 force）、對 main（`e1b33d8`）`merge-tree` **CLEAN**、寫入集單檔零逸出、兩個 commit 的 trailer 皆齊。

### 零、⚠️ 卡面核心痛點已在本輪之間被 amend——請以現行卡面為準

R1-01 歸屬 `planner`，需求方裁定走**縮小射程**（`issuecomment-5266365564`），核心痛點已修訂（op `97d7306f`）：**本卡只裁定管轄關係，不含消除既存差集**；消除差集與對帳閘門歸 #42，PM 已把該義務寫進 #42 的第 4、5 兩條驗收（op `fe3c4db4`）。

**該裁定留言由 PM 代擬代貼、需求方明確核准**，此事實逐字寫在留言開頭——因為 `amend --ruling-url` 只比對 comment author 而 PM 的 `gh` 正是以 `ruan6047` 認證，**該檢查對 PM 恆真**。本卡執行者對此作出判斷（PM 要它判），指出 `amend` 事件的 `授權` 欄與 `理由` 欄互相矛盾、只有散文那半是對的。**PM 查證後確認並發前向更正 `issuecomment-5266565670`（`attribution: coordinator`），已開卡 [#62](https://github.com/ruan6047/ai-workflow/issues/62) 承接。** 成因是 `amend_cmd.py:507` 的常數字面。

**請判斷**：R1-01 的 disposition 要求縮小射程須有「**已授權且已排程的後續交付**」，「僅記錄衍生卡不能使本卡的完整登記目標成立」。#42 是否滿足？（PM 的主張：它是開著的活卡、擁有那個檔案、且**自己的 blocking finding 尚未閉合**——第三點意味著它想結案就必須做。**但 PM 不宣稱這是機械保證**，需求方在裁定留言裡也自陳了殘餘風險。）

### ⚠️ 同批送審的另一張卡對本卡的裁定有實質反駁——請把它當成本輪的輸入

`WF-CONTROL-PLANE-TYPE-REGISTRY1`（#42）於 `e7927ac831828494cf09de1a40c2bd645d136a27` 交回，**與本卡同批送審**。它採納了本卡裁定 (a)(c)(d) 與裁定二、三，但**不採納 (b) 的實作**，並指出本卡內部有張力：

> 裁定一說名字屬表示層、裁定二說動詞名不是型別名，**但 §1.3 的閘門原型卻做名稱差集**。L2 的 `event` 值今天就是 `wfcli` 的動詞名，若把它們當型別名做名稱差集，消除差集的唯一手段就是把 `assign`／`amend` 補登進 L1——那正是本檔 §3.3 警告的「L1 從此帶兩組同義字，比今天更難修」。

它改為以 `表示層` 欄作 **L1→L2 解析函數**，判準改成「未解析成員數 = 0」，並主動標記那是它最可能被判不合格的一點；跑本卡 §1.3 的原始抽取器，名稱差集仍會印出 `amend assign`，它把該行保留為 `INFO` 並標「僅供對照、非判準」。

**PM 不預先裁定誰對。** 兩張同批是刻意的——**這個張力必須在同一批被裁掉，不能兩邊各拿半張圖**。請正面回答：本卡 §1.3 的閘門原型與裁定一、二是否真的互相矛盾？若是，那是本卡的缺陷還是 #42 的過度解讀？

### 一、本輪逐條改了什麼

**§0.1 射程裁定**，把承接寫成**三列指名對照表**（四項裁定→#42 第 4 條、消除差集＋閘門＋零產出 fail-closed→第 5 條、telemetry 宣告面→第 1 條），非散文「後續由衍生卡處理」。**PM 已核對 #42 現行驗收確為 5 條、編號對得上。**

**§5.3／§9／§1.4 的既存事實一字未刪，只改歸屬**——理由寫在 §0.1：刪掉它們，#42 就失去要處理的對象。

**§8 由「四張衍生卡」改為承接指派、未開卡**，並指名兩處 #42 現行單檔資源宣告涵蓋不到的殘餘。

**撤回一句變成過度宣稱的話**：§7 原寫「#42 不需要因本卡而改」，今天不成立，已標明撤回並保留仍成立的那一半。

**§6.2 排程裁定拆上界／下界**：上界（閘門不得晚於 v2 讀取器）仍是本檔裁定；下界（「現在還不該建」）被需求方排程覆寫，執行者明說不反對並**指名提早落地的新風險**——閘門一落地即紅而此刻無 v2 消費者因它紅而受益，正是 §5.3 擔心的「第三天被關掉」形狀，只是成因從假警報換成**真警報無人在意**。標為建議非裁定。

### 二、它自陳的五項，第 1、3 最該打

1. **§0.1 承接對照表是它對 #42 卡面文字的解讀，不是機械綁定。** 沒有任何東西把 #42 驗收第 5 條與本檔以 SHA 釘在一起——**#42 再 `amend` 一次，對照表會無聲失效**。它指出這與 #42 自己 R1-002 被打的形狀同構（未釘住的相依不產生可追溯的收斂義務），**指名了沒解決**。
3. **新指名的漏洞**：#42 第 5 條只要求「消除差集」，**未指定路徑**、也未逐字要求本檔 §4.3 的第三類 envelope。若用別的方式湊出空差集，**差集歸零而 §4.3 不落地、閘門看不出差別**。它稱這是本設計最實質的缺口。

另附一筆**新的實測反證**：PR #59 的 `COMMAND_MODULES` 在它跑窮舉時已存在於另一條分支（`a7e5e21` @ 17:58），不在 main、不在其基線，18:52 才併入；**判它不是型別宣告面是事後判的**。據此把「宣告面已窮舉」降為**時間點上的下界**，§5.2 判準重述為**維持義務**而非一次性窮舉。

### 三、範圍外（不代改、不開卡）

§3.4 的**卡片建立事件缺口今天沒有承接者**：`open` 沒有對應的 L1 型別。它在 `templates/control-plane-contract.md` 內（技術上在 #42 寫入集），但**不在 #42 任何一條驗收裡**。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5266916658 · 2026-08-12T12:39:05Z

<!-- wf-review-receipt:v1
card_id: WF-EVENT-TYPE-REGISTRY-RECONCILE1
source_sha: 42cfb387985ec335a57ed35217c580964f38dbb9
report_sha256: 7406a2c66081eff112817a4ef3ac6fe8be3d365b289997af7d850ff9e0b851a1
-->

取材規則：雜湊取材自本規則之後的下一個「## 查核報告」起，至報告全文 EOF 止；UTF-8 編碼、LF 換行、不做 strip；排除上方 HTML 收據與本取材規則行；起訖 delimiter 是「本規則之後的下一個」。

## 查核報告

core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "gh issue view 58 --repo ruan6047/ai-workflow --json body -q .body | grep 'handoff by wf-cli' | tail -1；git -C .claude/worktrees/wf-event-type-registry-reconcile1 rev-parse HEAD；git -C .claude/worktrees/wf-event-type-registry-reconcile1 merge-base --is-ancestor e8a638c40f1028b6b85f6c59fd12ee9c1e85582d HEAD"
    observed: "最後 handoff 與 HEAD 均為 42cfb387985ec335a57ed35217c580964f38dbb9，fork point 祖先檢查成功。"
  - command: "bash 抽取 e1b33d8984425901de400afeb227d5df67d07212 的 L1 與 L2，執行 comm -13"
    observed: "L2 減 L1 為 amend、assign、deployment-declaration、deployment-status-change、review-marker-clearance；本文件第 3 節同時將 assign 與 amend 裁為應映射到 claim 與 correction。"
  - command: "git diff --check e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 42cfb387985ec335a57ed35217c580964f38dbb9；git diff --name-only e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 42cfb387985ec335a57ed35217c580964f38dbb9；git interpret-trailers --parse"
    observed: "diff check 無輸出，唯一變更檔是 docs/WF_EVENT_TYPE_REGISTRY_RECONCILE1.md，兩個實作 commit 的必填 trailers 可解析。"
findings:
  - finding_id: "WF-EVENT-TYPE-REGISTRY-RECONCILE1-R2-01"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: "event-type-registry-incomplete"
    evidence: "文件 §3.1 裁定 CLI 動詞不是事件型別，§3.2 提議 assign 對應 claim、amend 對應 correction；但 §2.5 將 L2 subset L1 定義為原始名稱包含關係，§5.3 亦以未經映射的 comm 名稱差集作阻擋判準。實跑 e1b33d8984425901de400afeb227d5df67d07212 得 L2-minus-L1 包含 amend、assign，而 L1 已有 claim、correction。故依文件本身的提議語意，這兩個表示名已可對應 L1 事實，原始名稱閘門仍必錯判為違反；反之為讓原始名稱差集歸零而把同義名補進 L1，又違反 §3.3 指出的永久雙同義字風險。"
    disposition: "修訂裁定與閘門為同一語意模型：先成文化且可審的 L2 表示名至 L1 canonical 型別映射，再以映射後集合驗證包含關係；映射尚未裁定時，閘門不得把原始名稱差集宣稱為 L2 subset L1 違反。同步界定部署與 review-marker-clearance 的映射或其未決 fail-closed 行為，並以可重跑案例證明正確映射不紅、遺漏映射或未知型別會紅。"
prior_round_closure:
  - finding_id: "WF-EVENT-TYPE-REGISTRY-RECONCILE1-R1-01"
    status: "closed-by-requester-scope-ruling"
    evidence: "卡面核心痛點已由 op 97d7306f 改為僅裁定管轄關係；本輪文件 §0.1 將消除差集與對帳閘門逐項指向 #42 的驗收第 1、4、5 條，並保留該義務不因本卡結案而解除。"
    disposition: "R1 的 planner 射程脫節已依需求方縮小射程裁定閉合；本輪 finding 是縮小後交付物內部的語意與閘門不一致，須由本卡文件修正。"

## 查核結論

核心痛點是裁定事件型別語彙的管轄關係。文件雖完成分層、邊界與承接的敘述，但它把表示層 event 值與邏輯層型別同時判為不同身分又以原始名稱差集強制相等，沒有可審的解析關係。因此管轄裁定尚不能形成一致的對帳設計，核心痛點未解；REQUEST_CHANGES。

## 前輪 accepted blocking finding 閉環

R1-01 已依需求方的縮小射程裁定閉合；證據與閉環處置載於 YAML 的 prior_round_closure。

## 範圍外發現

無。

## Comment 5266923195 · 2026-08-12T12:39:43Z

<!-- wf-review-receipt:v1
card_id: WF-EVENT-TYPE-REGISTRY-RECONCILE1
source_sha: 42cfb387985ec335a57ed35217c580964f38dbb9
report_sha256: 2acb94cf6c1a4caeabc65b8bd6b38d1bdd992a2a2bfa205185e7cdc64ab01d45
-->

取材規則：雜湊取材自本規則之後的下一個「## 查核報告」起，至報告全文 EOF 止；UTF-8 編碼、LF 換行、不做 strip；排除上方 HTML 收據與本取材規則行；起訖 delimiter 是「本規則之後的下一個」。

## 查核報告」起，至報告全文 EOF 止；UTF-8 編碼、LF 換行、不做 strip；排除上方 HTML 收據與本取材規則行；起訖 delimiter 是「本規則之後的下一個」。

## 查核報告

core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "gh issue view 58 --repo ruan6047/ai-workflow --json body -q .body | grep 'handoff by wf-cli' | tail -1；git -C .claude/worktrees/wf-event-type-registry-reconcile1 rev-parse HEAD；git -C .claude/worktrees/wf-event-type-registry-reconcile1 merge-base --is-ancestor e8a638c40f1028b6b85f6c59fd12ee9c1e85582d HEAD"
    observed: "最後 handoff 與 HEAD 均為 42cfb387985ec335a57ed35217c580964f38dbb9，fork point 祖先檢查成功。"
  - command: "bash 抽取 e1b33d8984425901de400afeb227d5df67d07212 的 L1 與 L2，執行 comm -13"
    observed: "L2 減 L1 為 amend、assign、deployment-declaration、deployment-status-change、review-marker-clearance；本文件第 3 節同時將 assign 與 amend 裁為應映射到 claim 與 correction。"
  - command: "git diff --check e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 42cfb387985ec335a57ed35217c580964f38dbb9；git diff --name-only e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 42cfb387985ec335a57ed35217c580964f38dbb9；git interpret-trailers --parse"
    observed: "diff check 無輸出，唯一變更檔是 docs/WF_EVENT_TYPE_REGISTRY_RECONCILE1.md，兩個實作 commit 的必填 trailers 可解析。"
findings:
  - finding_id: "WF-EVENT-TYPE-REGISTRY-RECONCILE1-R2-01"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: "event-type-registry-incomplete"
    evidence: "文件 §3.1 裁定 CLI 動詞不是事件型別，§3.2 提議 assign 對應 claim、amend 對應 correction；但 §2.5 將 L2 subset L1 定義為原始名稱包含關係，§5.3 亦以未經映射的 comm 名稱差集作阻擋判準。實跑 e1b33d8984425901de400afeb227d5df67d07212 得 L2-minus-L1 包含 amend、assign，而 L1 已有 claim、correction。故依文件本身的提議語意，這兩個表示名已可對應 L1 事實，原始名稱閘門仍必錯判為違反；反之為讓原始名稱差集歸零而把同義名補進 L1，又違反 §3.3 指出的永久雙同義字風險。"
    disposition: "修訂裁定與閘門為同一語意模型：先成文化且可審的 L2 表示名至 L1 canonical 型別映射，再以映射後集合驗證包含關係；映射尚未裁定時，閘門不得把原始名稱差集宣稱為 L2 subset L1 違反。同步界定部署與 review-marker-clearance 的映射或其未決 fail-closed 行為，並以可重跑案例證明正確映射不紅、遺漏映射或未知型別會紅。"
prior_round_closure:
  - finding_id: "WF-EVENT-TYPE-REGISTRY-RECONCILE1-R1-01"
    status: "closed-by-requester-scope-ruling"
    evidence: "卡面核心痛點已由 op 97d7306f 改為僅裁定管轄關係；本輪文件 §0.1 將消除差集與對帳閘門逐項指向 #42 的驗收第 1、4、5 條，並保留該義務不因本卡結案而解除。"
    disposition: "R1 的 planner 射程脫節已依需求方縮小射程裁定閉合；本輪 finding 是縮小後交付物內部的語意與閘門不一致，須由本卡文件修正。"

## 查核結論

核心痛點是裁定事件型別語彙的管轄關係。文件雖完成分層、邊界與承接的敘述，但它把表示層 event 值與邏輯層型別同時判為不同身分又以原始名稱差集強制相等，沒有可審的解析關係。因此管轄裁定尚不能形成一致的對帳設計，核心痛點未解；REQUEST_CHANGES。

## 前輪 accepted blocking finding 閉環

R1-01 已依需求方的縮小射程裁定閉合；證據與閉環處置載於 YAML 的 prior_round_closure。

## 範圍外發現

無。

## Comment 5266932326 · 2026-08-12T12:40:37Z

<!-- wf-review-receipt:v1
card_id: WF-EVENT-TYPE-REGISTRY-RECONCILE1
source_sha: 42cfb387985ec335a57ed35217c580964f38dbb9
report_sha256: b892ee4794b7147dfbf2517437feacb8b999f06679d9f236bef44f06ae99d601
-->

取材規則：雜湊取材自本規則之後的下一個「## 查核報告」起，至報告全文 EOF 止；UTF-8 編碼、LF 換行、不做 strip；排除上方 HTML 收據與本取材規則行；起訖 delimiter 是「本規則之後的下一個」。

## 查核報告

core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "gh issue view 58 --repo ruan6047/ai-workflow --json body -q .body | grep 'handoff by wf-cli' | tail -1；git -C .claude/worktrees/wf-event-type-registry-reconcile1 rev-parse HEAD；git -C .claude/worktrees/wf-event-type-registry-reconcile1 merge-base --is-ancestor e8a638c40f1028b6b85f6c59fd12ee9c1e85582d HEAD"
    observed: "最後 handoff 與 HEAD 均為 42cfb387985ec335a57ed35217c580964f38dbb9，fork point 祖先檢查成功。"
  - command: "bash 抽取 e1b33d8984425901de400afeb227d5df67d07212 的 L1 與 L2，執行 comm -13"
    observed: "L2 減 L1 為 amend、assign、deployment-declaration、deployment-status-change、review-marker-clearance；本文件第 3 節同時將 assign 與 amend 裁為應映射到 claim 與 correction。"
  - command: "git diff --check e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 42cfb387985ec335a57ed35217c580964f38dbb9；git diff --name-only e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 42cfb387985ec335a57ed35217c580964f38dbb9；git interpret-trailers --parse"
    observed: "diff check 無輸出，唯一變更檔是 docs/WF_EVENT_TYPE_REGISTRY_RECONCILE1.md，兩個實作 commit 的必填 trailers 可解析。"
findings:
  - finding_id: "WF-EVENT-TYPE-REGISTRY-RECONCILE1-R2-01"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: "event-type-registry-incomplete"
    evidence: "文件 §3.1 裁定 CLI 動詞不是事件型別，§3.2 提議 assign 對應 claim、amend 對應 correction；但 §2.5 將 L2 subset L1 定義為原始名稱包含關係，§5.3 亦以未經映射的 comm 名稱差集作阻擋判準。實跑 e1b33d8984425901de400afeb227d5df67d07212 得 L2-minus-L1 包含 amend、assign，而 L1 已有 claim、correction。故依文件本身的提議語意，這兩個表示名已可對應 L1 事實，原始名稱閘門仍必錯判為違反；反之為讓原始名稱差集歸零而把同義名補進 L1，又違反 §3.3 指出的永久雙同義字風險。"
    disposition: "修訂裁定與閘門為同一語意模型：先成文化且可審的 L2 表示名至 L1 canonical 型別映射，再以映射後集合驗證包含關係；映射尚未裁定時，閘門不得把原始名稱差集宣稱為 L2 subset L1 違反。同步界定部署與 review-marker-clearance 的映射或其未決 fail-closed 行為，並以可重跑案例證明正確映射不紅、遺漏映射或未知型別會紅。"
prior_round_closure:
  - finding_id: "WF-EVENT-TYPE-REGISTRY-RECONCILE1-R1-01"
    status: "closed-by-requester-scope-ruling"
    evidence: "卡面核心痛點已由 op 97d7306f 改為僅裁定管轄關係；本輪文件 §0.1 將消除差集與對帳閘門逐項指向 #42 的驗收第 1、4、5 條，並保留該義務不因本卡結案而解除。"
    disposition: "R1 的 planner 射程脫節已依需求方縮小射程裁定閉合；本輪 finding 是縮小後交付物內部的語意與閘門不一致，須由本卡文件修正。"

## 查核結論

核心痛點是裁定事件型別語彙的管轄關係。文件雖完成分層、邊界與承接的敘述，但它把表示層 event 值與邏輯層型別同時判為不同身分又以原始名稱差集強制相等，沒有可審的解析關係。因此管轄裁定尚不能形成一致的對帳設計，核心痛點未解；REQUEST_CHANGES。

## 前輪 accepted blocking finding 閉環

R1-01 已依需求方的縮小射程裁定閉合；證據與閉環處置載於 YAML 的 prior_round_closure。

## 範圍外發現

無。


## Comment 5267054368 · 2026-08-12T12:52:11Z

<!-- wf-review-event:v1 card_id=WF-EVENT-TYPE-REGISTRY-RECONCILE1 source_sha=42cfb387985ec335a57ed35217c580964f38dbb9 attempt_id=WF-EVENT-TYPE-REGISTRY-RECONCILE1-e0-42cfb387985ec335a57ed35217c580964f38dbb9 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-EVENT-TYPE-REGISTRY-RECONCILE1`　attempt_id：`WF-EVENT-TYPE-REGISTRY-RECONCILE1-e0-42cfb387985ec335a57ed35217c580964f38dbb9`
- 查核者：GPT-5@Codex 子代理（需求方轉貼）；⚠️ 本卡收到三則收據 5266916658／5266923195／5266932326，PM 逐一驗算三者雜湊皆自洽；第一與第三份內容逐位元組相同（7406a2c6…），中間一份僅因取材規則那行漏進被雜湊區而異，裁決三份一致；轉錄採 5266932326。PM 的轉錄調整：截去 YAML 區塊後的「查核結論／前輪閉環／範圍外」三段散文，該三段完整保存於收據雜湊範圍內，區塊內字串逐字未變　escalation_epoch：0
- source_sha：`42cfb387985ec335a57ed35217c580964f38dbb9`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T20:52:09+08:00

### self_run（查核者實跑）

- `gh issue view 58 --repo ruan6047/ai-workflow --json body -q .body | grep 'handoff by wf-cli' | tail -1；git -C .claude/worktrees/wf-event-type-registry-reconcile1 rev-parse HEAD；git -C .claude/worktrees/wf-event-type-registry-reconcile1 merge-base --is-ancestor e8a638c40f1028b6b85f6c59fd12ee9c1e85582d HEAD`
  - 最後 handoff 與 HEAD 均為 42cfb387985ec335a57ed35217c580964f38dbb9，fork point 祖先檢查成功。
- `bash 抽取 e1b33d8984425901de400afeb227d5df67d07212 的 L1 與 L2，執行 comm -13`
  - L2 減 L1 為 amend、assign、deployment-declaration、deployment-status-change、review-marker-clearance；本文件第 3 節同時將 assign 與 amend 裁為應映射到 claim 與 correction。
- `git diff --check e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 42cfb387985ec335a57ed35217c580964f38dbb9；git diff --name-only e8a638c40f1028b6b85f6c59fd12ee9c1e85582d 42cfb387985ec335a57ed35217c580964f38dbb9；git interpret-trailers --parse`
  - diff check 無輸出，唯一變更檔是 docs/WF_EVENT_TYPE_REGISTRY_RECONCILE1.md，兩個實作 commit 的必填 trailers 可解析。

### findings（1，其中 blocking 1）

- **WF-EVENT-TYPE-REGISTRY-RECONCILE1-R2-01**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`event-type-registry-incomplete`
  - evidence：文件 §3.1 裁定 CLI 動詞不是事件型別，§3.2 提議 assign 對應 claim、amend 對應 correction；但 §2.5 將 L2 subset L1 定義為原始名稱包含關係，§5.3 亦以未經映射的 comm 名稱差集作阻擋判準。實跑 e1b33d8984425901de400afeb227d5df67d07212 得 L2-minus-L1 包含 amend、assign，而 L1 已有 claim、correction。故依文件本身的提議語意，這兩個表示名已可對應 L1 事實，原始名稱閘門仍必錯判為違反；反之為讓原始名稱差集歸零而把同義名補進 L1，又違反 §3.3 指出的永久雙同義字風險。
  - disposition：修訂裁定與閘門為同一語意模型：先成文化且可審的 L2 表示名至 L1 canonical 型別映射，再以映射後集合驗證包含關係；映射尚未裁定時，閘門不得把原始名稱差集宣稱為 L2 subset L1 違反。同步界定部署與 review-marker-clearance 的映射或其未決 fail-closed 行為，並以可重跑案例證明正確映射不紅、遺漏映射或未知型別會紅。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5460928404 · 2026-08-29T06:55:50Z

## 阻塞登記

**狀態**：⏸阻塞。**來源狀態：📥Backlog**（解除時回到此狀態）。

**阻塞原因**：需求方於 2026-08-29 決定，在階段狀態重整（8 階段 × 10 狀態、待審清單、CLI 射程收斂）定案並落地前，暫停所有 ai-workflow 流程卡，避免它們與重構討論互相干擾。

**可證偽的解除條件**：待審清單機制上線（label ＋ issue template ＋ 可見分組）。屆時本卡改列為清單參考項，或依當時前提是否仍成立重新排程。

**本次未做**：核心痛點、驗收條件、射程一律未動。`iteration` 未遞增。`階段` 欄未寫入。本登記僅改交付狀態與 owner。

**已知的射程重疊**（供解除時參考，非本次裁定）：#66／#38 的實質可能由「七份交接文件格式」承接；#128 可能由「待審清單收件條件三·查重留痕」＋`open --from-issue` 承接；#11 的證據紀律已部分寫入 PM 準則但痛點（靠人記得）未消失。⛔ 上述皆未經裁定，解除時須逐張重驗。

**裁定者**：需求方 ruan6047，2026-08-29 本 session 對話中指示「把目前所有 WF 卡片暫停，避免干擾目前重構討論」。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

