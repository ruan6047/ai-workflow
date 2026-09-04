# #42 WF-CONTROL-PLANE-TYPE-REGISTRY1 control-plane-contract.md §2 的 type 列舉漏登兩個已設計的事件型別
- state: open  created: 2026-08-12T03:26:32Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/42
- comments: 14

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 經濟型；單檔列舉補登，兩個型別的定義由他卡已寫定，執行者只需核對後登記並判斷是否有其他漏登；推理鏈短。）　查核：待指派（建議 經濟型；低風險登記，查核只需確認登記內容與各型別的定義來源逐字相符、且未順帶擴充語意；不涉紅線故不強制跨家族。）
- Initiative：—　spec 基線：WF-ESCALATION-RESOLUTION-GAP1（#39）於 058100ad 交付時第七節第 2 項指名。需求方 2026-08-12 裁定不擴充 #39 的寫入集，另開本卡一併處理既存的同型落差。
- DB：db_scope=none
- 服務的原始目標：讓 control-plane 的事件型別列舉是完整的，而不是各卡自行定義後沒人登記

## 簡介
<!-- card-brief:begin -->
窮舉 templates/ 與 docs/ 內已被定義卻沒登記進 templates/control-plane-contract.md §2 type 列舉的事件型別並補登（已知 review-marker-clearance 與 escalation-resolution），並交付可重跑、對零產出 fail-closed 的差集對帳閘門。**適用時機**：新增事件型別而不知該回哪裡登記；或消費者以 §2 列舉判管轄、新型別落進未定義分支時。⛔ 非射程：不修改 docs/WF_EVENT_MARKER_V2.md 那一份語彙；review-marker-clearance 的型別設計歸 WF-MARKER-SCOPE-CLEARANCE1（aiwf#30）；管轄裁定承接 WF-EVENT-TYPE-REGISTRY-RECONCILE1（aiwf#58）四項結論，反駁須附論證。已於 2026-08-13 依 docs/ROADMAP.md §0／§3 降級為 Backlog，未閉合 blocking 維持未閉合。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：templates/control-plane-contract.md §2 的 type 列舉至少漏了兩個已被設計出來的事件型別：review-marker-clearance（既存落差，由 WF-MARKER-SCOPE-CLEARANCE1 #30 承接該型別的設計）與 escalation-resolution（WF-ESCALATION-RESOLUTION-GAP1 #39 於 058100ad 新增）。兩者是同一種病：型別在別的契約檔裡被定義出來，但沒有回到 control-plane 的列舉登記，於是消費者若以該列舉判定管轄，新型別會落進未定義分支。#39 的執行者主動指名了這一點並拒絕自行擴充宣告，是對的——但指名之後若無人承接，落差就永久留著。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:templates/control-plane-contract.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 窮舉 templates/ 與 docs/ 內所有已定義但未登記進 §2 的事件型別，不得只補這兩個就宣稱處理完畢。窮舉須由指令輸出產生，並列出每個候選的定義出處與登記與否。⚠️ 抽取器不得等同於「解析 type: 那一行」——#58 已查出 §2 的 telemetry 行另外宣告了 resource-acquired／resource-released，而兩者在 type: 行出現 0 次（PM 已複驗）。R2-001 的 self_run 用的正是解析 type 行的腳本，其「18 vs 7、交集 3」的數字因此在宣告面上不完整。
- [ ] 登記內容須與各型別的定義來源逐字相符，不得順帶擴充或收窄語意。escalation-resolution 的定義以 #39 交付版為準；review-marker-clearance 若 #30 尚未交付，須明確處置——登記一個尚未定稿的型別是否恰當由執行者論證，先行登記與等待皆為合法結論。
- [ ] 須裁定一個更根本的問題並寫進交付物：新型別的登記今天靠什麼保證？若答案是「靠設計者記得」，就明說沒有機械執行者，並判斷該不該有（例如 doctor 比對列舉與各檔定義），該判斷若逸出寫入集即明列為衍生卡。
- [ ] ⚠️ 本卡承接 WF-EVENT-TYPE-REGISTRY-RECONCILE1（#58）的管轄裁定，並負責把它落地——這是需求方 2026-08-12 於 #58 issuecomment-5266365564 的指派，#58 已據此縮小射程，其結案不解除本義務。須採納或明確反駁 #58 的四項裁定：(a) 不設單一權威，L1＝邏輯事件模型／L2＝單一傳輸的線上格式，層界＝是否以留言 marker 承載識別符；(b) 唯一硬約束為 L2 ⊆ L1、反向不要求，故對帳閘門必須雙向不對稱——本卡 R2-001 的框架會導出對稱閘門，依 #58 的論證那是錯的；(c) control-plane 全檔「封閉」0 次且 :32 明文「專案可擴充 event type」，故病灶是「一份開放基準與一份封閉登記之間沒有包含關係檢查」，不是「兩份封閉語彙互不知情」；(d)「什麼算型別宣告」的判準是位置不是文字啟發式——窮舉宣告面（可審）取代窮舉型別（對自由文字證否、不可證明）。反駁任何一項須附論證，不得默默不採納。
- [ ] ⚠️ 消除 L2−L1 差集並交付可重跑的對帳閘門。#58 實測 S1（今日 main）差 5 項、S2（本卡併入後）差 4 項。閘門須對零產出 fail-closed——#58 的執行者親身踩到 zsh 下 :t 修飾符把抽取吃成 0 筆而 comm 照樣印出看起來乾淨的結果。交付報告須指出本閘門擋不住什麼。

## 驗證

- [ ] 窮舉輸出附在交付報告，含命中行號與各自處置。
- [ ] 登記前後以 diff 證明只動了 §2 列舉，未改動任何型別的語意描述。
- [ ] 若採用「先行登記尚未定稿型別」，須說明 #30 交付後若定義不同要怎麼收斂。
## Log

- 2026-08-12T11:26:31+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-12T13:32:53+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code 子agent；分支worktree claude/WF-CONTROL-PLANE-TYPE-REGISTRY1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-control-plane-type-registry1；交付狀態 🚧進行中；實際能力層級 經濟型（與卡面建議 經濟型 相符）。
- 2026-08-12T16:18:25+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA b1429220729cda242a9bc53640a04b67014dfaff；證據 R1：templates/control-plane-contract.md 單檔 **+1 −1 行，僅第 21 行**，列舉 14 → 16。

窮舉由腳本產生（掃 templates/、docs/，另加 #39 分支、cli/、scripts/、根目錄 *.md 交叉核對）：已登記 14 個，機械抽出未登記 kebab token 17 個，再以「是否被文本宣告為 lifecycle event 的 type 值」過濾。判為事件型別且未登記 5 個，其中**登記 2 個**（review-marker-clearance、escalation-resolution）、**不登記 3 個**且各有理由。判為非事件型別而排除 12 個，逐一附證據（clearance_decision 的值、defer_cause 的值、epoch_change_reason 的值、GraphQL 寫入分類、HTML 註解登記指令、CLI 動詞）。補掃三輪未再新增候選。

⚠️ 執行者先修正了卡面一項前提：卡說 review-marker-clearance 的設計「由 #30 承接、尚未定稿」——**對事件欄位層不成立**。該型別的必填欄位與語意已完整在 main 的 review-escalation.md:212–260，而 #30 的驗收條件自己寫著「消費端判定沿用 §5 既有規則……本卡只補表示法不改其語意」。所以那不是先行登記未定稿型別，是登記一個已定稿型別，零漂移風險。escalation-resolution 才是真正的先行登記，裁定登記，理由是兩種失敗形狀不對稱：未登記時消費者依 §2 判管轄會落進未定義分支，而 §2 自己寫「不得將未識別 type 默默當成 review attempt」，未登記正好使該條無從遵守；已登記但 main 無定義時消費者至少知道它不是 review attempt，且 main 今天沒有任何 writer 能產出該事件。收斂規則：#39 改名或被否決 → 移除該 token，代價封頂在一個 token。

三個不登記的理由值得看：baseline-change-request 在 baseline-cascade.md:12 同時出現在有型別的面與無型別的面，文本無法判定它是 type 值還是 Log 標籤，登記與否都需要替該檔作者下語意裁定；migration-baseline 與 epoch-anchor 兩者都被描述為「逐卡 one-shot、指派 state_version = 1」，是同一機制兩個名字還是兩個機制文本判不出來，**單獨登記其中一個等於替另一個判死**；且 epoch-anchor 的本體只存在於 issue #16 的正文——issue body 可改且不受版控，登記它會讓 main 指向一個不可稽核的來源。

範圍外但已指名：deployment-status-change（deploy_state_cmd.py:68）是另一個 envelope，無 event_id／無 state_version／無 type，不受 §2 管轄；但**§2 的管轄邊界本身沒有寫在任何地方**，執行者是靠欄位集比對推斷的，這是一個未成文判準。

「登記靠什麼保證」的答案是**沒有機械執行者，靠設計者記得**，證據為指令輸出：grep control-plane-contract 只命中三處散文與兩處引註，**cli/ 與 scripts/ 零命中**，.github/ 當時不存在無 CI。它判定該有，並列四張衍生卡（doctor 事件型別登記對帳為優先，但需先解決「什麼算型別宣告」的成文判準且 doctor.py 由 #30 持有）。

逐字對照以 hex 逐位元組比對兩個 token 皆 PASS；diff 證明 git diff --stat 為 1 檔 1 增 1 刪、hunk 僅 @@ -21 +21 @@、**刪去第 21 行後兩版全檔逐位元組相同**、列舉集合差集新增恰為那兩個且移除為空。

執行者自陳的無執行者宣稱中最誠實的一條：「已窮舉」的抽取規則是反引號 kebab token ＋ 該行含事件/event/type，未加反引號或用其他措辭宣告的型別會漏，補掃三輪降低漏網率但**沒有證明覆蓋完整**。另：「收斂規則：#39 改名就改一行」沒有執行者，沒有東西會在 #39 落地時提醒任何人回來看 §2——**這正是本卡在治的那個病，它的交付沒有治好它，只補了兩個實例**。

寫入集單檔零逸出，marker 新增 0 處。。
- 2026-08-12T17:00:54+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5264439488 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=c8909814… 一次相符。本批六份收據皆採內容錨定或分隔行，各自規則不同，PM 逐份照其規則計算、無需任何格式調整）；core_pain_resolved no；self_run 5 項；findings 3 項（blocking 2）；attempt WF-CONTROL-PLANE-TYPE-REGISTRY1-e0-b1429220729cda242a9bc53640a04b67014dfaff。
- 2026-08-12T17:09:30+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 1；SHA b1429220729cda242a9bc53640a04b67014dfaff；證據 R1-001 與 R1-002 兩筆 blocking（另 R1-000 為 info、非阻擋，僅記錄首輪無前輪閉環）。

R1-001（event-type-registry-incomplete）：查核者在**隔離的 source tree** 內定位到 baseline-cascade.md:12 明定「在 lifecycle event 留 baseline-change-request」、MIGRATION.md:26 明定「migration-baseline lifecycle event 並指定 state_version 為 1」——**兩個 token 都不在被審的 type 列舉**。它逐一反駁執行者的不登記理由：前者**同時出現在卡 Log 不消除其被明定為 lifecycle event 的事實**；後者**是受版控文件，非不可稽核的 Issue body**（執行者原以 epoch-anchor 只存在於 issue #16 正文為由不登記，但 migration-baseline 不適用該理由）。disposition：補登這兩個，**或以同一變更明確、可稽核地裁定兩者不是 schema type**；在 type 列舉與每個型別的狀態轉移定義一致前不得通過。

R1-002（event-type-registry-unanchored-provisional-entry）：被審 source tree 對 escalation-resolution 的**唯一命中是列舉那一行**，同一 source SHA 沒有其狀態轉移、必填欄位或語意定義。**未合併分支的設計沒有被此卡以 SHA 或相依關係釘住**，故改名或語意修訂**不會產生可追溯的收斂義務**。disposition：在**同一已合併權威交付物**定義型別與狀態轉移後登記，或以**釘住的相依 SHA、明示 provisional 規則與落地前對帳守衛**使先行登記可稽核；**不得僅靠改一行的人工承諾**。

⚠️ 執行者上一輪自陳「收斂規則沒有執行者……這正是本卡在治的那個病，我的交付沒有治好它」——**查核者把那句自陳升級成 blocking**。自陳有價值，但自陳不等於處置。

⚠️ 一個排期事實：#39（escalation-resolution 的定義來源）本批**查核 APPROVE 但尚未合併**。R1-002 的兩條出路中，第一條（等已合併權威交付物）在 #39 併入後即可滿足。。
- 2026-08-12T17:56:14+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 1；SHA b8a4a16b1376c699a85a378be40c7a9107aa0ede；證據 R2：R1-001 與 R1-002 皆已處置。

R1-001 全接受，執行者不辯：baseline-change-request 它承認錯在「**用歧義去否定明文**」——「同時也出現在 Log」不構成對「lifecycle event」宣告的反證，且登記只登名稱不定欄位，它擔心的「替作者下語意裁定」根本不會發生；migration-baseline 它承認把它和 epoch-anchor **綁成一組判**是錯誤，epoch-anchor 的理由（只存在 issue #16 正文、不受版控）只對 epoch-anchor 成立，MIGRATION.md 是受版控檔。epoch-anchor 維持不登記。列舉 14 → 18。**PM 已複驗差集：新增恰為那兩個、移除為空。**

另加 §2.1 定義出處登記表使一致性可逐項核對。**誠實揭露 claim／review／correction／merge 在本 repo 沒有專屬定義檔**（git grep -l 零命中），表中如實標為「無專屬定義檔」而非虛構出處——既存狀態、非本卡造成，但不掩蓋。

R1-002 選 (b) 而非 (a)，並據 PM 更正後的 #39 事實明說「第一條出路等於把本卡掛在 #39 的完整生命週期上，我不選」。實作為 §2.2：釘住 b039c0b ＋ review-escalation.md §5 ＋ 釘住時狀態；provisional 消費規則（視為已登記但無本地定義，不得當成 review attempt、不得依其欄位裁決、只能記錄並 fail-closed）；落地對帳三款（逐位元組名稱相符／必填欄位集合相符或差異同批登記／同時刪除本節列不留孤兒 pin）；**內嵌兩道任何人可重跑的命令，輸出即判準**——釘住處回 1、main 回 0，0 即尚未落地、非 0 即落地對帳已到期。它明說這把「有沒有人記得」換成「跑一道命令」，但也指名 §2.2 仍是**約定**（執行者是 #39 的 merge 授權者與本檔管轄者），命令提供的是**可觀測訊號不是強制閘門**。

⚠️ **本輪最重要的發現，PM 已獨立複驗屬實**：main 上已存在**第二份封閉的事件型別語彙**——docs/WF_EVENT_MARKER_V2.md 的 EVENTS dict（7 項：review／handoff／assign／amend／deployment-declaration／deployment-status-change／review-marker-clearance），該檔明寫「事件型別由 event= 鍵承擔」。差集：只在該表有的是 assign／amend／deployment-declaration／deployment-status-change；兩份皆有的只有 review／handoff／review-marker-clearance——**後者是兩份獨立收斂到同名**。執行者把它**登記為已知分歧、明確不裁定**（孰為權威、CLI 動詞算不算事件型別、部署事件是否受該 envelope 管轄，全逸出寫入集）。PM 已據此開卡 WF-EVENT-TYPE-REGISTRY-RECONCILE1 承接。**該不一致是合併製造的、不是任一張卡的缺陷**：#35 與 #42 各自通過查核、各自語彙自洽，合起來產生新的不一致而沒有機械檢查會發現，因為兩邊都封閉且 fail-closed、只是封閉在不同集合上。

驗證（皆為指令輸出）：§2 以外抽掉後與基線 diff 為空；§2 既有段落（去 type: 行後）新舊 diff 為空，含第 30–33 行語意規則、telemetry 行、狀態轉移句與專案實作槽；列舉差集本輪新增恰為兩項、移除為空；定義出處錨點實測存在於 origin/main（migration-baseline 1、baseline-change-request 1、review-marker-clearance 1、escalation-resolution 0 正確故為 provisional、釘住 SHA 1）；grep 紀律新增 0。

⚠️ 執行者中途自抓一個缺陷並記錄：第一版插入位置把 §2 原有的「列出允許的狀態轉移…〈專案實作〉」擠到 §2.2 之下、使專案填空槽變成 provisional 小節的附屬，且它在 §2.1 寫的「上方〈專案實作〉」變成錯誤指向；是 V4 結構檢查抓到的（而它第一版 V4 的 awk 還寫錯、輸出可疑，重寫後才顯形）。已復原順序並複驗。

⚠️ PM 的一項陳述被執行者糾正，但**該糾正本身有誤**：它稱 PM 說的「#35／#41 已併入」與實際不符、實際是 PR #49／#50／#51。**PM 已查證：PR #50 = 卡 #35、PR #51 = 卡 #41，它把 PR 編號當成卡號了**；兩個被審 SHA 皆已驗為 origin/main 祖先。但**它真正要指的實質觀察是對的**——那個範圍帶進了 WF_EVENT_MARKER_V2.md 新檔而該檔改變了本卡結論，PM 當時只駁到形式那一半。

執行者自陳：「已窮舉」仍是約定（抽取規則為反引號 kebab token ＋ 該行含 事件/event/type，另加三輪補掃與本輪對新檔專掃，**沒有證明覆蓋完整**——而本輪新檔恰好證明該風險是真的）；§2.2 落地對帳三款與 §2.1 的同時登記要求皆為約定；四個差集項「應該在 §2」是它未下的判斷、已標為不裁定。。
- 2026-08-12T18:44:04+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5265430265 未經編輯，PM 回讀重算 report_sha256=e79e8258… 一次相符。⚠️ 本卡 Issue 上最後一則派審詞所載 SHA 為 b142922（前一輪），與實際 handoff 的 b8a4a16 不符——那是 PM 漏補派審詞所致；查核者以 handoff SHA 為準、審的是正確產物，其 self_run 明載「與權威 handoff SHA 相同且工作區乾淨」，故本裁決有效）；core_pain_resolved no；self_run 4 項；findings 2 項（blocking 1）；attempt WF-CONTROL-PLANE-TYPE-REGISTRY1-e0-b8a4a16b1376c699a85a378be40c7a9107aa0ede。
- 2026-08-12T19:46:01+08:00 amend by wf-cli（op fe3c4db4）→ 驗收條件：原值「[ ] 窮舉 templates/ 與 docs/ 內所有已定義但未登記進 §2 的事件型別，不得只補這兩個就宣稱處理完畢。窮舉須由指令輸出產生，並列出每個候選的定義出處與登記與否。；[ ] 登記內容須與各型別的定義來源逐字相符，不得順帶擴充或收窄語意。escalation-resolution 的定義以 #39 交付版為準；review-marker-clearance 若 #30 尚未交付，須明確處置——登記一個尚未定稿的型別是否恰當由執行者論證，先行登記與等待皆為合法結論。；[ ] 須裁定一個更根本的問題並寫進交付物：新型別的登記今天靠什麼保證？若答案是「靠設計者記得」，就明說沒有機械執行者，並判斷該不該有（例如 doctor 比對列舉與各檔定義），該判斷若逸出寫入集即明列為衍生卡。」→ 新值「窮舉 templates/ 與 docs/ 內所有已定義但未登記進 §2 的事件型別，不得只補這兩個就宣稱處理完畢。窮舉須由指令輸出產生，並列出每個候選的定義出處與登記與否。⚠️ 抽取器不得等同於「解析 type: 那一行」——#58 已查出 §2 的 telemetry 行另外宣告了 resource-acquired／resource-released，而兩者在 type: 行出現 0 次（PM 已複驗）。R2-001 的 self_run 用的正是解析 type 行的腳本，其「18 vs 7、交集 3」的數字因此在宣告面上不完整。；登記內容須與各型別的定義來源逐字相符，不得順帶擴充或收窄語意。escalation-resolution 的定義以 #39 交付版為準；review-marker-clearance 若 #30 尚未交付，須明確處置——登記一個尚未定稿的型別是否恰當由執行者論證，先行登記與等待皆為合法結論。；須裁定一個更根本的問題並寫進交付物：新型別的登記今天靠什麼保證？若答案是「靠設計者記得」，就明說沒有機械執行者，並判斷該不該有（例如 doctor 比對列舉與各檔定義），該判斷若逸出寫入集即明列為衍生卡。；⚠️ 本卡承接 WF-EVENT-TYPE-REGISTRY-RECONCILE1（#58）的管轄裁定，並負責把它落地——這是需求方 2026-08-12 於 #58 issuecomment-5266365564 的指派，#58 已據此縮小射程，其結案不解除本義務。須採納或明確反駁 #58 的四項裁定：(a) 不設單一權威，L1＝邏輯事件模型／L2＝單一傳輸的線上格式，層界＝是否以留言 marker 承載識別符；(b) 唯一硬約束為 L2 ⊆ L1、反向不要求，故對帳閘門必須雙向不對稱——本卡 R2-001 的框架會導出對稱閘門，依 #58 的論證那是錯的；(c) control-plane 全檔「封閉」0 次且 :32 明文「專案可擴充 event type」，故病灶是「一份開放基準與一份封閉登記之間沒有包含關係檢查」，不是「兩份封閉語彙互不知情」；(d)「什麼算型別宣告」的判準是位置不是文字啟發式——窮舉宣告面（可審）取代窮舉型別（對自由文字證否、不可證明）。反駁任何一項須附論證，不得默默不採納。；⚠️ 消除 L2−L1 差集並交付可重跑的對帳閘門。#58 實測 S1（今日 main）差 5 項、S2（本卡併入後）差 4 項。閘門須對零產出 fail-closed——#58 的執行者親身踩到 zsh 下 :t 修飾符把抽取吃成 0 筆而 comm 照樣印出看起來乾淨的結果。交付報告須指出本閘門擋不住什麼。」；理由 需求方 2026-08-12 裁定（#58 issuecomment-5266365564）：#58 的核心痛點縮為「裁定管轄關係」，消除既存差集與建立可重跑對帳閘門改由本卡承接。理由是 templates/control-plane-contract.md 由本卡持有、本卡未閉合的 blocking finding（event-type-registry-incomplete）要求的正是同一件事；把檔案搬給 #58 只會作廢本卡兩輪查核成果並由 #58 重做它已做出的裁定。新增第 4、5 兩條驗收把該義務落在卡面而非散文，並把 #58 查出的第三個宣告面（telemetry 行的 resource-acquired／resource-released，在 type: 行出現 0 次）寫進第 1 條——本卡 R2-001 查核者的抽取腳本正是解析 type 行，其數字在宣告面上不完整。原三條驗收文字未改，僅第 1 條追加該警示。。
- 2026-08-12T19:47:04+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 2；SHA b8a4a16b1376c699a85a378be40c7a9107aa0ede；證據 R2-001（major, blocking, coordination, attribution=coordinator, root_cause_id=event-type-registry-incomplete）：無成文管轄邊界、無唯一權威、無機械對帳。需求方 2026-08-12 裁定本卡承接 #58 的管轄裁定並負責落地，卡面已 amend 新增第 4、5 兩條驗收（op fe3c4db4）。R2-000 已記 R1-001／R1-002 閉環。⚠️ 查核者 self_run 的抽取腳本只解析 type: 行，而 §2 telemetry 行另宣告 resource-acquired／resource-released 且兩者在 type: 行出現 0 次（PM 已複驗），故其「18 vs 7、交集 3」在宣告面上不完整。。
- 2026-08-12T20:23:19+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 2；SHA e7927ac831828494cf09de1a40c2bd645d136a27；證據 R3：R2-001 已處置。卡面已 amend（op fe3c4db4）新增第 4、5 兩條驗收，本卡承接 #58 的管轄裁定並負責落地。四項裁定中 (a)(c)(d) 與裁定二、三全採納，(b) 方向與不對稱性採納但比較對象改了——執行者主張 #58 內部有張力（裁定一說名字屬表示層、裁定二說動詞名不是型別名，而 §1.3 原型卻做名稱差集），改以 §2.1 新增的表示層欄作 L1→L2 解析函數、判準為未解析成員數=0；它主動標記這是最可能被判不合格的一點，並把 §1.3 原始抽取器的名稱差集輸出保留為 INFO 標明非判準。對帳器七類檢查、九個宣告面（含前輪查核者腳本看不見的 telemetry 行與獨立狀態機行）、12 種人為變異逐一注入驗證訊息互不共用，含 #58 踩到的錨點改寫形狀。⚠️ 執行者自陳最重的一件：提名器跑出來後核 deploy-declare 出處才發現 WF_EVENT_MARKER_V2.md §2.3 是第三個 L2 面，兩輪跨家族查核、#58、它前兩輪四方都沒提到；同時證明方法有效與前面每一輪的「已窮舉」都不成立。兩筆非同名解析：assign→claim 由推論升級為引用（canonical :100），但發現 canonical :144 要求 claim 記 lease_expires_at 而 assign 完全不碰 lease，僅指名；amend→correction 強度弱、如實標為名稱層裁定。PM 自審：遠端 tip 相符、b8a4a16 是祖先（非 force，兩個 attempt SHA 都保住）、對 main merge-tree CLEAN、相對 main 寫入集單檔零逸出、trailer 已帶但格式與同批他卡不一致。⚠️ PM 交叉對帳：本卡的 escalation-resolution provisional pin 釘在 b039c0b 而 #39 現行 tip 為 ba90b81（同批送審），PM 已比對兩者 templates/review-escalation.md blob 逐位元組相同（ee823e2e…）故內容無誤，但屬同族陳舊引用。⚠️ worktree 根目錄有未追蹤檔 rip（76 bytes），執行者無法歸因，PM 未刪除，git status --short 因此非空但不是未提交改動。。
- 2026-08-12T20:52:30+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5266930922 未經編輯，PM 依其 delimiter 回讀重算 report_sha256=530a1a2e… 相符。⚠️ PM 複驗 R3-001 未能重現，另貼獨立說明；core_pain_resolved no；self_run 4 項；findings 2 項（blocking 1）；attempt WF-CONTROL-PLANE-TYPE-REGISTRY1-e0-e7927ac831828494cf09de1a40c2bd645d136a27。
- 2026-08-12T21:37:57+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 3；SHA e7927ac831828494cf09de1a40c2bd645d136a27；證據 R3-001（major, blocking, implementation, attribution=executor, root_cause_id=event-type-registry-incomplete）：§2.4 對帳器在未變異產物上 exit 1。⚠️ PM 起初複驗不出來並貼了非重現結論，該結論已撤回（issuecomment-5267247548）——真因是 locale：UTF-8 locale 下 bash 把多位元組字元吞進識別字，錯誤訊息逐字為 line 36: min̲: unbound variable；LC_ALL=C 可避開，而 PM 的 shell LANG="" LC_CTYPE=C 使其列出的四種環境有三種是同一組。查核者限縮後的 evidence 與 disposition PM 全盤接受：改  使腳本不依賴 locale，並在至少 LC_ALL=C 與一個 UTF-8 locale 下重跑基線 PASS 與既列 fail-closed 變異。R3-000（info）已記 R1-001／R1-002 閉環。。
- 2026-08-13T00:23:41+08:00 handoff by wf-cli → owner 待指派；iteration 4；SHA 0ea7abad670681b708f4fbbe15526008b448abe3；證據 依 docs/ROADMAP.md §0／§3 降級：本卡屬目標 3（治理精緻化），非「防止低級事故」或「可稽核的內容」。需求方 2026-08-12 裁定降級為 Backlog、有餘力再做。⚠️ 降級不是關閉——本卡載有的真實 finding 紀錄全數保留、可逆；未閉合的 blocking 維持未閉合，本次降級不視為驗收。⚠️ WF-DISPATCH-PRECHECK1（#38）另有一項：它的射程很可能被 WF-DISPATCH-FROM-HANDOFF1（#66，走「同源產生」路線讓不一致不可能發生）取代，該裁定屬 #66 執行者，本次降級不預判。。
- 2026-08-26T22:08:50+08:00 amend by wf-cli（op d8fd5839）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:fc7cef940a558a3f65216123f58a818c7537b93b69e5db477435a9645297dbc9 (772 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。
- 2026-08-29T14:57:35+08:00 handoff by wf-cli → owner 待指派；iteration 4；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 阻塞登記（來源狀態 📥Backlog）：https://github.com/ruan6047/ai-workflow/issues/42 之阻塞留言。解除條件＝待審清單機制上線。。


## Comment 5264329808 · 2026-08-12T08:33:18Z

## 派審：#42 `WF-CONTROL-PLANE-TYPE-REGISTRY1` R1

⚠️ 審核對象 **`ruan6047/ai-workflow#42`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-control-plane-type-registry1
分支：claude/WF-CONTROL-PLANE-TYPE-REGISTRY1　　被審 SHA：b1429220729cda242a9bc53640a04b67014dfaff
基線：5d22a7f3da57a3790179e999d9d28262fda4d19a（PM 已重算並驗為祖先）　　iteration：0（首輪）
寫入集：templates/control-plane-contract.md 單檔　　改動 +1 / -1，僅第 21 行，列舉 14 → 16
```

> **本則為權威。** `origin/main` 現為 `02b5d9a`。**PM 已實測 merge(origin/main, 本分支) → 658 passed 全綠。**

### 一、窮舉：登記 2 個、明確不登記 3 個、排除 12 個

腳本掃 `templates/`、`docs/`，另加 #39 分支、`cli/`、`scripts/`、根目錄 `*.md` 交叉核對。已登記 14 個；機械抽出未登記 kebab token 17 個；再以「是否被文本宣告為 lifecycle event 的 `type` 值」過濾。補掃三輪未再新增候選。

**判為非事件型別而排除的 12 個各有證據**（`clearance_decision` 的值、`defer_cause` 的值、`epoch_change_reason` 的值、GraphQL 寫入分類、HTML 註解登記指令、CLI 動詞）。

**請攻擊**：抽取規則是**反引號 kebab token ＋ 該行含 事件／event／type**——執行者自陳「未加反引號、或用其他措辭宣告的型別會漏……**沒有證明覆蓋完整**」。請自己另找一組 pattern 掃一次。

### 二、⚠️ 它先修正了卡面一項前提

卡面說 `review-marker-clearance` 的設計「由 #30 承接、**尚未定稿**」——**它判定對事件欄位層不成立**：該型別的必填欄位與語意**已完整在 main 的 `review-escalation.md`**，而 #30 的驗收條件自己寫著「消費端判定沿用 §5 既有規則……**本卡只補表示法不改其語意**」。所以那不是先行登記未定稿型別，**是登記一個已定稿型別，零漂移風險**。

`escalation-resolution` 才是真正的先行登記，裁定登記，理由是**兩種失敗形狀不對稱**：未登記時消費者依 §2 判管轄會落進未定義分支，而 §2 自己寫「不得將未識別 type 默默當成 review attempt」——**未登記正好使該條無從遵守**；已登記但 main 無定義時消費者至少知道它不是 review attempt，且 main 今天沒有任何 writer 能產出該事件。

**請判斷**：(a) 對卡面前提的修正成立嗎？(b) 那個不對稱論證成立嗎？(c) `escalation-resolution` 來自 **#39 的未合併分支**（同批送審，可能還會變）——先行登記一個仍在查核中的型別，收斂規則「改名就改一行、代價封頂在一個 token」夠嗎？

### 三、三個不登記的理由值得單獨看

- **`baseline-change-request`**：`baseline-cascade.md` 說「在卡 Log **與** lifecycle event 留 X」——同一個 token 同時出現在有型別的面與無型別的面，**文本無法判定它是 `type` 值還是 Log 標籤**；登記與否都需要替該檔作者下語意裁定。
- **`migration-baseline` 與 `epoch-anchor`**：兩者都被描述為「逐卡 one-shot、指派 `state_version = 1`」，**是同一機制兩個名字還是兩個機制，文本判不出來**——「**單獨登記其中一個等於替另一個判死**」。且 `epoch-anchor` 的本體只存在於 issue #16 的正文，**issue body 可改且不受版控，登記它會讓 main 指向一個不可稽核的來源**。

**請判斷這三個「不登記」是謹慎還是逃避。**

### 四、範圍外但已指名

`deployment-status-change`（`deploy_state_cmd.py`）走**另一個 envelope**（無 `event_id`／無 `state_version`／無 `type`），不受 §2 管轄。**但 §2 的管轄邊界本身沒有寫在任何地方**——執行者是靠欄位集比對推斷的，**這是一個未成文判準**。

### 五、「登記靠什麼保證」——答案是沒有

證據為指令輸出：`grep control-plane-contract` 只命中三處散文與兩處引註，**`cli/` 與 `scripts/` 零命中**。它判定該有，並列四張衍生卡（`doctor` 事件型別登記對帳為優先，但需先解決「什麼算型別宣告」的成文判準且 `doctor.py` 由 #30 持有）。

**它自陳最誠實的一句**：「收斂規則：#39 改名就改一行」**沒有執行者**，沒有東西會在 #39 落地時提醒任何人回來看 §2——「**這正是本卡在治的那個病，我的交付沒有治好它，只補了兩個實例**」。

### 六、機械證據（可重跑）

`git diff --stat` = 1 檔 1 增 1 刪、hunk 僅 `@@ -21 +21 @@`、**刪去第 21 行後兩版全檔逐位元組相同**、列舉集合差集新增恰為那兩個且**移除為空**。兩個 token 以 hex 逐位元組比對定義來源皆 PASS——**但它明說那驗的是名稱字串不是語意**。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5264436939 · 2026-08-12T08:43:42Z

core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C .claude/worktrees/wf-control-plane-type-registry1 rev-parse HEAD && git -C .claude/worktrees/wf-control-plane-type-registry1 status --short"
    observed: "HEAD 為 b1429220729cda242a9bc53640a04b67014dfaff，status 無輸出，與 handoff SHA 相同且工作區乾淨"
  - command: "git merge-base --is-ancestor 5d22a7f3da57a3790179e999d9d28262fda4d19a b1429220729cda242a9bc53640a04b67014dfaff"
    observed: "exit 0，指定基線為被審 SHA 的祖先"
  - command: "git diff --check 5d22a7f3da57a3790179e999d9d28262fda4d19a b1429220729cda242a9bc53640a04b67014dfaff"
    observed: "exit 0；變更限 templates/control-plane-contract.md 的 type 列舉一增一刪"
  - command: "git archive b1429220729cda242a9bc53640a04b67014dfaff | tar -x -C /tmp/aiwf42.mp3PYp；rg -n lifecycle-event-pattern /tmp/aiwf42.mp3PYp/templates/baseline-cascade.md /tmp/aiwf42.mp3PYp/MIGRATION.md"
    observed: "隔離樹中定位 baseline-change-request 與 migration-baseline 的明確 lifecycle event 宣告；兩者均不在被審 type 列舉"
  - command: "rg -l escalation-resolution /tmp/aiwf42.mp3PYp | rg -v control-plane-contract"
    observed: "0 matches；被審 source tree 除 type 列舉外沒有此型別的狀態轉移或語意定義"
findings:
  - finding_id: "WF-CONTROL-PLANE-TYPE-REGISTRY1-R1-000"
    severity: info
    blocking: false
    finding_class: governance
    attribution: reviewer
    root_cause_id: "first-review-no-prior-closure"
    evidence: "首輪，無前輪 accepted blocking finding；故無逐項閉環項目。"
    disposition: "首輪閉環要求已明確記錄；後續輪次須逐項回報本輪被採認的 blocking finding 狀態。"
  - finding_id: "WF-CONTROL-PLANE-TYPE-REGISTRY1-R1-001"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: "event-type-registry-incomplete"
    evidence: "隔離 source tree 的 templates/baseline-cascade.md:12 明定在 lifecycle event 留 baseline-change-request；MIGRATION.md:26 明定 migration-baseline lifecycle event 並指定 state_version 為 1。兩個 token 均不在 b1429220729cda242a9bc53640a04b67014dfaff 的 control-plane-contract type 列舉。前者同時出現在卡 Log 不消除其被明定為 lifecycle event 的事實；後者是受版控文件，非不可稽核的 Issue body。"
    disposition: "補登 baseline-change-request 與 migration-baseline，或以同一變更明確、可稽核地裁定兩者不是 schema type；在 type 列舉與每個型別的狀態轉移定義一致前不得通過。"
  - finding_id: "WF-CONTROL-PLANE-TYPE-REGISTRY1-R1-002"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: "event-type-registry-unanchored-provisional-entry"
    evidence: "被審 source tree 對 escalation-resolution 的唯一命中是 control-plane-contract.md:21 的新列舉項；同一 source SHA 沒有其狀態轉移、必填欄位或語意定義。未合併分支的可能設計沒有被此卡以 SHA 或相依關係釘住，故改名或語意修訂不會產生此登記的可追溯收斂義務。"
    disposition: "在同一已合併權威交付物定義型別與狀態轉移後登記，或以釘住的相依 SHA、明示 provisional 規則與落地前對帳守衛使先行登記可稽核；不得僅靠改一行的人工承諾。"

## Comment 5264439488 · 2026-08-12T08:43:58Z

<!-- wf-review-receipt:v1
card_id: WF-CONTROL-PLANE-TYPE-REGISTRY1
source_sha: b1429220729cda242a9bc53640a04b67014dfaff
report_sha256: c89098143cb2b5b5a04b078722f24e6b7187d42757744912bacab88c69034ca6
-->
取材規則：起點為本規則之後的下一個 core_pain_resolved: 行；終點為該 YAML 報告最後一個 disposition: 值的最後一個字元；UTF-8；LF；strip=false；排除本收據 header 與本取材規則；被雜湊內容為下列完整結構化報告。
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C .claude/worktrees/wf-control-plane-type-registry1 rev-parse HEAD && git -C .claude/worktrees/wf-control-plane-type-registry1 status --short"
    observed: "HEAD 為 b1429220729cda242a9bc53640a04b67014dfaff，status 無輸出，與 handoff SHA 相同且工作區乾淨"
  - command: "git merge-base --is-ancestor 5d22a7f3da57a3790179e999d9d28262fda4d19a b1429220729cda242a9bc53640a04b67014dfaff"
    observed: "exit 0，指定基線為被審 SHA 的祖先"
  - command: "git diff --check 5d22a7f3da57a3790179e999d9d28262fda4d19a b1429220729cda242a9bc53640a04b67014dfaff"
    observed: "exit 0；變更限 templates/control-plane-contract.md 的 type 列舉一增一刪"
  - command: "git archive b1429220729cda242a9bc53640a04b67014dfaff | tar -x -C /tmp/aiwf42.mp3PYp；rg -n lifecycle-event-pattern /tmp/aiwf42.mp3PYp/templates/baseline-cascade.md /tmp/aiwf42.mp3PYp/MIGRATION.md"
    observed: "隔離樹中定位 baseline-change-request 與 migration-baseline 的明確 lifecycle event 宣告；兩者均不在被審 type 列舉"
  - command: "rg -l escalation-resolution /tmp/aiwf42.mp3PYp | rg -v control-plane-contract"
    observed: "0 matches；被審 source tree 除 type 列舉外沒有此型別的狀態轉移或語意定義"
findings:
  - finding_id: "WF-CONTROL-PLANE-TYPE-REGISTRY1-R1-000"
    severity: info
    blocking: false
    finding_class: governance
    attribution: reviewer
    root_cause_id: "first-review-no-prior-closure"
    evidence: "首輪，無前輪 accepted blocking finding；故無逐項閉環項目。"
    disposition: "首輪閉環要求已明確記錄；後續輪次須逐項回報本輪被採認的 blocking finding 狀態。"
  - finding_id: "WF-CONTROL-PLANE-TYPE-REGISTRY1-R1-001"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: "event-type-registry-incomplete"
    evidence: "隔離 source tree 的 templates/baseline-cascade.md:12 明定在 lifecycle event 留 baseline-change-request；MIGRATION.md:26 明定 migration-baseline lifecycle event 並指定 state_version 為 1。兩個 token 均不在 b1429220729cda242a9bc53640a04b67014dfaff 的 control-plane-contract type 列舉。前者同時出現在卡 Log 不消除其被明定為 lifecycle event 的事實；後者是受版控文件，非不可稽核的 Issue body。"
    disposition: "補登 baseline-change-request 與 migration-baseline，或以同一變更明確、可稽核地裁定兩者不是 schema type；在 type 列舉與每個型別的狀態轉移定義一致前不得通過。"
  - finding_id: "WF-CONTROL-PLANE-TYPE-REGISTRY1-R1-002"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: "event-type-registry-unanchored-provisional-entry"
    evidence: "被審 source tree 對 escalation-resolution 的唯一命中是 control-plane-contract.md:21 的新列舉項；同一 source SHA 沒有其狀態轉移、必填欄位或語意定義。未合併分支的可能設計沒有被此卡以 SHA 或相依關係釘住，故改名或語意修訂不會產生此登記的可追溯收斂義務。"
    disposition: "在同一已合併權威交付物定義型別與狀態轉移後登記，或以釘住的相依 SHA、明示 provisional 規則與落地前對帳守衛使先行登記可稽核；不得僅靠改一行的人工承諾。"

## Comment 5264610439 · 2026-08-12T09:00:55Z

<!-- wf-review-event:v1 card_id=WF-CONTROL-PLANE-TYPE-REGISTRY1 source_sha=b1429220729cda242a9bc53640a04b67014dfaff attempt_id=WF-CONTROL-PLANE-TYPE-REGISTRY1-e0-b1429220729cda242a9bc53640a04b67014dfaff -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CONTROL-PLANE-TYPE-REGISTRY1`　attempt_id：`WF-CONTROL-PLANE-TYPE-REGISTRY1-e0-b1429220729cda242a9bc53640a04b67014dfaff`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5264439488 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=c8909814… 一次相符。本批六份收據皆採內容錨定或分隔行，各自規則不同，PM 逐份照其規則計算、無需任何格式調整）　escalation_epoch：0
- source_sha：`b1429220729cda242a9bc53640a04b67014dfaff`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T17:00:54+08:00

### self_run（查核者實跑）

- `git -C .claude/worktrees/wf-control-plane-type-registry1 rev-parse HEAD && git -C .claude/worktrees/wf-control-plane-type-registry1 status --short`
  - HEAD 為 b1429220729cda242a9bc53640a04b67014dfaff，status 無輸出，與 handoff SHA 相同且工作區乾淨
- `git merge-base --is-ancestor 5d22a7f3da57a3790179e999d9d28262fda4d19a b1429220729cda242a9bc53640a04b67014dfaff`
  - exit 0，指定基線為被審 SHA 的祖先
- `git diff --check 5d22a7f3da57a3790179e999d9d28262fda4d19a b1429220729cda242a9bc53640a04b67014dfaff`
  - exit 0；變更限 templates/control-plane-contract.md 的 type 列舉一增一刪
- `git archive b1429220729cda242a9bc53640a04b67014dfaff | tar -x -C /tmp/aiwf42.mp3PYp；rg -n lifecycle-event-pattern /tmp/aiwf42.mp3PYp/templates/baseline-cascade.md /tmp/aiwf42.mp3PYp/MIGRATION.md`
  - 隔離樹中定位 baseline-change-request 與 migration-baseline 的明確 lifecycle event 宣告；兩者均不在被審 type 列舉
- `rg -l escalation-resolution /tmp/aiwf42.mp3PYp | rg -v control-plane-contract`
  - 0 matches；被審 source tree 除 type 列舉外沒有此型別的狀態轉移或語意定義

### findings（3，其中 blocking 2）

- **WF-CONTROL-PLANE-TYPE-REGISTRY1-R1-000**　severity=info　blocking=false　class=governance　attribution=reviewer　root_cause_id=`first-review-no-prior-closure`
  - evidence：首輪，無前輪 accepted blocking finding；故無逐項閉環項目。
  - disposition：首輪閉環要求已明確記錄；後續輪次須逐項回報本輪被採認的 blocking finding 狀態。
- **WF-CONTROL-PLANE-TYPE-REGISTRY1-R1-001**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`event-type-registry-incomplete`
  - evidence：隔離 source tree 的 templates/baseline-cascade.md:12 明定在 lifecycle event 留 baseline-change-request；MIGRATION.md:26 明定 migration-baseline lifecycle event 並指定 state_version 為 1。兩個 token 均不在 b1429220729cda242a9bc53640a04b67014dfaff 的 control-plane-contract type 列舉。前者同時出現在卡 Log 不消除其被明定為 lifecycle event 的事實；後者是受版控文件，非不可稽核的 Issue body。
  - disposition：補登 baseline-change-request 與 migration-baseline，或以同一變更明確、可稽核地裁定兩者不是 schema type；在 type 列舉與每個型別的狀態轉移定義一致前不得通過。
- **WF-CONTROL-PLANE-TYPE-REGISTRY1-R1-002**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`event-type-registry-unanchored-provisional-entry`
  - evidence：被審 source tree 對 escalation-resolution 的唯一命中是 control-plane-contract.md:21 的新列舉項；同一 source SHA 沒有其狀態轉移、必填欄位或語意定義。未合併分支的可能設計沒有被此卡以 SHA 或相依關係釘住，故改名或語意修訂不會產生此登記的可追溯收斂義務。
  - disposition：在同一已合併權威交付物定義型別與狀態轉移後登記，或以釘住的相依 SHA、明示 provisional 規則與落地前對帳守衛使先行登記可稽核；不得僅靠改一行的人工承諾。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5264782097 · 2026-08-12T09:18:04Z

## PM 更正：#39 從未被 APPROVE

本卡同日交回執行者時的 handoff 證據寫著：

> #39（`escalation-resolution` 的定義來源）本批**查核 APPROVE 但尚未合併**。R1-002 的兩條出路中，第一條（等已合併權威交付物）在 #39 併入後即可滿足。

**前半句是錯的。** #39 的交付狀態為 **🔍待查核**、iteration 1，其 `b039c0b` **沒有任何 review event**；唯一一次查核是 R1、結果為 **REQUEST_CHANGES**。PM 應是把那次的 `core_pain_resolved: yes` 誤記成 APPROVE。`attribution: coordinator`，前向更正，未追溯編輯 Log。

### 對本卡的實質影響

**R1-002 的第一條出路（等已合併權威交付物）比 PM 暗示的遠得多。** #39 還要先通過查核、可能還有修法輪次，然後才合併——那是數輪之後的事，不是「即將」。

**這強化了第二條出路的相對價值**：以**釘住的相依 SHA、明示 provisional 規則與落地前對帳守衛**使先行登記可稽核。查核者的 disposition 逐字給了兩條，**執行者可自行選擇**，但選第一條等於把本卡掛在另一張卡的完整生命週期上。

執行者請據更正後的事實重新評估，**不要因為 PM 先前的錯誤陳述而預設第一條路即將可用**。

## Comment 5265430265 · 2026-08-12T10:21:48Z

<!-- wf-review-receipt:v1
card_id: WF-CONTROL-PLANE-TYPE-REGISTRY1
source_sha: b8a4a16b1376c699a85a378be40c7a9107aa0ede
report_sha256: e79e82585b354284236a76bf51138eb3f066908935d15d4151620472ac8f71aa
-->
取材規則：起點為本規則之後的下一個 core_pain_resolved: 行；終點為該 YAML 報告最後一個 disposition: 值的最後一個字元；UTF-8；LF；strip=false；排除本收據 header 與本取材規則；被雜湊內容為下列完整結構化報告。
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-control-plane-type-registry1 rev-parse HEAD && git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-control-plane-type-registry1 status --short"
    observed: "HEAD 為 b8a4a16b1376c699a85a378be40c7a9107aa0ede，status 無輸出，與權威 handoff SHA 相同且工作區乾淨"
  - command: "git -C /Users/ruanruan/Dev/ai-workflow merge-base --is-ancestor 5d22a7f3da57a3790179e999d9d28262fda4d19a b8a4a16b1376c699a85a378be40c7a9107aa0ede && git -C /Users/ruanruan/Dev/ai-workflow diff --check 5d22a7f3da57a3790179e999d9d28262fda4d19a b8a4a16b1376c699a85a378be40c7a9107aa0ede"
    observed: "兩項皆 exit 0；基線為祖先，且 diff 無空白錯誤"
  - command: "git -C /Users/ruanruan/Dev/ai-workflow show b039c0b08113382566d9b687087dea1f08f3915c:templates/review-escalation.md | grep -c '^`escalation-resolution` 解除'; git -C /Users/ruanruan/Dev/ai-workflow show e8a638c40f1028b6b85f6c59fd12ee9c1e85582d:templates/review-escalation.md | grep -c '^`escalation-resolution` 解除'"
    observed: "釘住 #39 SHA 回 1，現行 origin/main 回 0；provisional pin 與未落地主張相符"
  - command: "在 /tmp/aiwf42-merge.Ngx5mn/repo 以 e8a638c 為基底 merge --no-commit b8a4a16b，再以 Python 只解析 WF_EVENT_MARKER_V2.md §3.2 表與 control-plane-contract.md 的 type 行"
    observed: "合併無衝突；control-plane=18、marker=7、共同=handoff review review-marker-clearance、marker_only=amend assign deployment-declaration deployment-status-change"
findings:
  - finding_id: "WF-CONTROL-PLANE-TYPE-REGISTRY1-R2-000"
    severity: info
    blocking: false
    finding_class: governance
    attribution: reviewer
    root_cause_id: "first-review-no-prior-closure"
    evidence: "前輪 accepted blocking finding 閉環：R1-001 已完成，type 列舉新增 baseline-change-request 與 migration-baseline，且 §2.1 分別釘住 baseline-cascade.md 與 MIGRATION.md；R1-002 已完成，§2.2 對 escalation-resolution 釘住 b039c0b、規定 provisional fail-closed、列出落地三款對帳。"
    disposition: "R1-001 與 R1-002 均不再阻擋；後續輪次須保留此閉環紀錄。"
  - finding_id: "WF-CONTROL-PLANE-TYPE-REGISTRY1-R2-001"
    severity: major
    blocking: true
    finding_class: coordination
    attribution: coordinator
    root_cause_id: "event-type-registry-incomplete"
    evidence: "把被審 SHA 與現行 origin/main e8a638c 在拋棄式 repo 合併後，control-plane §2 的 18 個 type 與 docs/WF_EVENT_MARKER_V2.md §3.2 的 7 個 event 值只有 handoff、review、review-marker-clearance 三個交集；後者另有 amend、assign、deployment-declaration、deployment-status-change。被審文件雖將此寫成已知分歧並稱不裁定，卻沒有成文管轄邊界、唯一權威或機械對帳；兩個封閉語彙可各自 fail-closed 而永遠不報彼此不一致。"
    disposition: "在通過前，須以此卡可改的 control-plane contract 明定兩集合的管轄關係並設可重跑對帳，或以需求方明確裁定將完整性目標縮為單一 envelope 並同步修正核心痛點與驗收；僅記錄衍生卡不能使本卡的完整登記目標成立。"


## Comment 5265651450 · 2026-08-12T10:44:05Z

<!-- wf-review-event:v1 card_id=WF-CONTROL-PLANE-TYPE-REGISTRY1 source_sha=b8a4a16b1376c699a85a378be40c7a9107aa0ede attempt_id=WF-CONTROL-PLANE-TYPE-REGISTRY1-e0-b8a4a16b1376c699a85a378be40c7a9107aa0ede -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CONTROL-PLANE-TYPE-REGISTRY1`　attempt_id：`WF-CONTROL-PLANE-TYPE-REGISTRY1-e0-b8a4a16b1376c699a85a378be40c7a9107aa0ede`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5265430265 未經編輯，PM 回讀重算 report_sha256=e79e8258… 一次相符。⚠️ 本卡 Issue 上最後一則派審詞所載 SHA 為 b142922（前一輪），與實際 handoff 的 b8a4a16 不符——那是 PM 漏補派審詞所致；查核者以 handoff SHA 為準、審的是正確產物，其 self_run 明載「與權威 handoff SHA 相同且工作區乾淨」，故本裁決有效）　escalation_epoch：0
- source_sha：`b8a4a16b1376c699a85a378be40c7a9107aa0ede`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T18:44:04+08:00

### self_run（查核者實跑）

- `git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-control-plane-type-registry1 rev-parse HEAD && git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-control-plane-type-registry1 status --short`
  - HEAD 為 b8a4a16b1376c699a85a378be40c7a9107aa0ede，status 無輸出，與權威 handoff SHA 相同且工作區乾淨
- `git -C /Users/ruanruan/Dev/ai-workflow merge-base --is-ancestor 5d22a7f3da57a3790179e999d9d28262fda4d19a b8a4a16b1376c699a85a378be40c7a9107aa0ede && git -C /Users/ruanruan/Dev/ai-workflow diff --check 5d22a7f3da57a3790179e999d9d28262fda4d19a b8a4a16b1376c699a85a378be40c7a9107aa0ede`
  - 兩項皆 exit 0；基線為祖先，且 diff 無空白錯誤
- `git -C /Users/ruanruan/Dev/ai-workflow show b039c0b08113382566d9b687087dea1f08f3915c:templates/review-escalation.md | grep -c '^`escalation-resolution` 解除'; git -C /Users/ruanruan/Dev/ai-workflow show e8a638c40f1028b6b85f6c59fd12ee9c1e85582d:templates/review-escalation.md | grep -c '^`escalation-resolution` 解除'`
  - 釘住 #39 SHA 回 1，現行 origin/main 回 0；provisional pin 與未落地主張相符
- `在 /tmp/aiwf42-merge.Ngx5mn/repo 以 e8a638c 為基底 merge --no-commit b8a4a16b，再以 Python 只解析 WF_EVENT_MARKER_V2.md §3.2 表與 control-plane-contract.md 的 type 行`
  - 合併無衝突；control-plane=18、marker=7、共同=handoff review review-marker-clearance、marker_only=amend assign deployment-declaration deployment-status-change

### findings（2，其中 blocking 1）

- **WF-CONTROL-PLANE-TYPE-REGISTRY1-R2-000**　severity=info　blocking=false　class=governance　attribution=reviewer　root_cause_id=`first-review-no-prior-closure`
  - evidence：前輪 accepted blocking finding 閉環：R1-001 已完成，type 列舉新增 baseline-change-request 與 migration-baseline，且 §2.1 分別釘住 baseline-cascade.md 與 MIGRATION.md；R1-002 已完成，§2.2 對 escalation-resolution 釘住 b039c0b、規定 provisional fail-closed、列出落地三款對帳。
  - disposition：R1-001 與 R1-002 均不再阻擋；後續輪次須保留此閉環紀錄。
- **WF-CONTROL-PLANE-TYPE-REGISTRY1-R2-001**　severity=major　blocking=true　class=coordination　attribution=coordinator　root_cause_id=`event-type-registry-incomplete`
  - evidence：把被審 SHA 與現行 origin/main e8a638c 在拋棄式 repo 合併後，control-plane §2 的 18 個 type 與 docs/WF_EVENT_MARKER_V2.md §3.2 的 7 個 event 值只有 handoff、review、review-marker-clearance 三個交集；後者另有 amend、assign、deployment-declaration、deployment-status-change。被審文件雖將此寫成已知分歧並稱不裁定，卻沒有成文管轄邊界、唯一權威或機械對帳；兩個封閉語彙可各自 fail-closed 而永遠不報彼此不一致。
  - disposition：在通過前，須以此卡可改的 control-plane contract 明定兩集合的管轄關係並設可重跑對帳，或以需求方明確裁定將完整性目標縮為單一 envelope 並同步修正核心痛點與驗收；僅記錄衍生卡不能使本卡的完整登記目標成立。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5265893251 · 2026-08-12T11:09:27Z

## ⏸ PM 暫緩本卡的修復派工：R2-001 的處置與 #58 的交付物直接重疊

R2-001 的 `disposition` 逐字要求：

> 須以此卡可改的 control-plane contract **明定兩集合的管轄關係並設可重跑對帳**，或以需求方明確裁定將完整性目標縮為單一 envelope。

而 [#58](https://github.com/ruan6047/ai-workflow/issues/58)（`WF-EVENT-TYPE-REGISTRY-RECONCILE1`）的交付物**正是對「管轄關係」的裁定**，且已於 `0b30a82` 交回、現正待跨家族查核。它裁定的內容與本卡若各自演化，就會複製本卡被打的那個病灶本身——**兩份語彙各自封閉演化且互不知情**。

因此本卡的修復**等 #58 的裁決落地後再派**。這不是延後查核，是避免同一個問題被兩張卡各給一個答案。

### #58 已經裁定、且與本卡 R2-001 直接相關的三點（供後續採用時參考，尚未通過查核）

**一、不設單一權威，兩者分屬兩層。** L1＝邏輯事件模型（control-plane §2 是**範本**，經 ADOPTION 實例化；**本 repo 自己沒有 `docs/CONTROL_PLANE_CONTRACT.md`，故它從未管轄過本 repo 任何具體事件**），L2＝單一傳輸的線上格式。層界＝**是否以留言 marker 承載識別符**。導出唯一硬約束 **L2 ⊆ L1，反向不要求**——意即對帳閘門必須**雙向不對稱**。

**本卡 R2-001 的框架會導出對稱閘門，而依 #58 的論證那是錯的。** 這正是不宜各自演化的理由。

**二、本卡與查核者共用的一個前提不成立。** control-plane 全檔「封閉」**0 次**，且 `:32` 明文「專案可擴充 event type」。所以病灶不是「兩個封閉語彙可各自 fail-closed 而永遠不報彼此不一致」，而是「**一份開放基準與一份封閉登記之間沒有包含關係檢查**」。

**三、還有第三個宣告面，本卡兩輪都沒提到。** §2 telemetry 行宣告 `resource-acquired`／`resource-released` 走同一 envelope，**但兩者在 `type:` 那一行出現 0 次**（PM 已複驗）。**任何把「§2 列舉」等同「`type:` 那一行」的抽取器都看不見它們**——查核者 R2-001 的 self_run 用的正是解析 `type` 行的腳本，故其「18 vs 7、交集 3」的數字**在宣告面上不完整**。這不影響該 finding 成立，但影響「可重跑對帳」該怎麼寫。

### 對本卡不受影響的部分

R2-000 已記錄 R1-001 與 R1-002 均閉環（`type` 列舉新增 `baseline-change-request` 與 `migration-baseline` 並釘住來源；§2.2 對 `escalation-resolution` 釘住 `b039c0b`、規定 provisional fail-closed）。這兩項不受 #58 影響。

另：`origin/main` 已由 `e8a638c` 前進至 `e1b33d8`（#53 合併）。本分支對新 main `merge-tree` 無衝突（PM 已驗），基線不需重算。


## Comment 5266733227 · 2026-08-12T12:21:46Z

## 派審：#42 `WF-CONTROL-PLANE-TYPE-REGISTRY1` R3

⚠️ 審核對象 **`ruan6047/ai-workflow#42`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-control-plane-type-registry1
分支：claude/WF-CONTROL-PLANE-TYPE-REGISTRY1　　被審 SHA：e7927ac831828494cf09de1a40c2bd645d136a27
基線：e1b33d8984425901de400afeb227d5df67d07212（PM 已重算並驗為祖先）　　iteration：2
寫入集：templates/control-plane-contract.md 單檔（+221/-20）
```

> **權威來源**：本則與 Log 最後一筆 `handoff` 的 `SHA` 必須一致；不符時**以 handoff 事件為準並回報**。⚠️ 本卡上一輪有一則派審詞載了舊 SHA（`b142922`），該疏漏是 PM 的；當時的查核者以 handoff SHA 為準、審的是正確產物。

**PM 自審**：遠端 tip 相符、`b8a4a16` 是祖先（**非 force**，兩個 attempt SHA 都保住了）、對 main `merge-tree` **CLEAN**、相對 main 寫入集**單檔**零逸出。

分支上另有一個基線更新 merge `2539beb`——`docs/WF_EVENT_MARKER_V2.md` 只在 `origin/main`，不併入就無法在單一 SHA 上跑對帳。執行者用 merge 不用 rebase 以保住 attempt SHA。

### 零、⚠️ 卡面已被 amend，且新增的兩條驗收是本輪的主軸

需求方 2026-08-12 裁定（`#58 issuecomment-5266365564`）：`WF-EVENT-TYPE-REGISTRY-RECONCILE1`（#58）縮為純裁定卡，**消除差集與建立可重跑對帳閘門歸本卡**。卡面 `amend` op `fe3c4db4` 新增第 4、5 兩條驗收、第 1 條追加 telemetry 宣告面警示。**請 `gh issue view 42` 讀現行五條驗收全文。**

**該裁定留言由 PM 代擬代貼、需求方明確核准**，事實逐字寫在留言開頭；`amend` 的 author 檢查對 PM 恆真，前向更正見 `#58 issuecomment-5266565670`，已開卡 [#62](https://github.com/ruan6047/ai-workflow/issues/62)。

### 一、⚠️ 本卡對 #58 的裁定 (b) 提出實質反駁——**這是本輪最該被裁的一點**

#58 於 `42cfb387985ec335a57ed35217c580964f38dbb9` **與本卡同批送審**。本卡採納了它的 (a)(c)(d) 與裁定二、三，**唯獨不採納 (b) 的實作**：

> 我承認 R2 的框架會導出對稱閘門，那是錯的，#58 的論證成立。但我不採納「比兩個名稱集合的差集」這個實作，理由出自 #58 自己的**裁定二：動詞名不得直接充當型別名**。L2 的 `event` 值今天就是 `wfcli` 的動詞名，若把它們當型別名做名稱差集，消除差集的唯一手段就是把 `assign`／`amend` 補登進 L1——那正是 #58 §3.3 警告的「L1 從此帶兩組同義字，比今天更難修」。**#58 內部在這裡是有張力的**：裁定一說名字屬表示層、裁定二說動詞名不是型別名，但 §1.3 的閘門原型卻做名稱差集。

實作：§2.1 新增 `表示層` 欄作 **L1→L2 解析函數**，判準改為「**未解析成員數 = 0**」。

**執行者主動標記這是本輪最可能被判不合格的一點**：跑 #58 §1.3 的原始抽取器，名稱差集仍會印出 `amend assign`；它把該行保留為 `INFO` 並標「僅供對照、非判準」，「就是為了讓任何人重跑時立刻看到差異來源而不是以為我漏做」。它並指出替代路徑只有一條——把 `assign`／`amend` 補登為 L1 型別——而它判定那比較差。

**PM 不預先裁定誰對。兩張同批是刻意的：這個張力必須在同一批被裁掉。** 請正面回答張力是否真的存在，以及本卡的解析函數是不是正解。

### 二、兩筆非同名解析

- **`assign` → `claim`**：把 #58 標的「推論」**升級為引用**——canonical `AI_WORKFLOW.md:100` 要求派工的能力偏離「記入 **claim 事件**」，`assign_cmd.py` 的 docstring 正是引用同一條。**但同時發現未閉合落差**：canonical `:144` 要求 claim 記錄 `lease_expires_at`，而 `assign` 今天完全不碰 lease（`grep lease` 零命中）。逸出寫入集，僅指名。
- **`amend` → `correction`**：**強度弱，如實標為名稱層裁定**——`correction` 在本 repo 無專屬定義檔，映射目標本身沒有語意。

### 三、對帳器：七類檢查、九個宣告面、12 種變異全部實測

你上一輪 self_run 用的是解析 `type:` 行的腳本。**本輪的抽取面是九個**，含你那個腳本看不見的 telemetry 行與獨立狀態機行。基線輸出 `未解析的 L2 成員數 = 0`、`RESULT PASS`。

**零產出 fail-closed 的 12 種人為變異逐一注入、逐一重跑、訊息互不共用**，含 #58 踩到的那個形狀（`EVENTS` 錨點改寫 → `s7 抽到 0 筆` ＋ `錨點不存在`，EXIT=2）。

過程中**對帳器自己被抓到一個缺陷**：第一版「L1 型別缺表示層宣告」會被計數檢查搶先報成 `來源未被讀到`——**用對的方向失敗、但講錯原因**，正好違反它自己寫的「兩個訊息必須分離」。已修。

**請攻擊**：12 種變異是不是同一個機制的 12 種寫法？以及**它對「抽得到足量但抽錯內容」自承擋不住**——那個缺口有多大？

### 四、執行者自陳最重的一件

> 提名器跑出來後我去核 `deploy-declare` 的出處，才發現 `WF_EVENT_MARKER_V2.md` **§2.3 是第三個 L2 面**——**兩輪跨家族查核、#58、我前兩輪，四方都沒提到它**。已登記為 `s9`。這件事同時證明了方法有效與**前面每一輪的「已窮舉」都不成立**；我沒有理由相信這一輪就找完了。

**請判斷這個自陳對 `core_pain_resolved` 的影響。** 卡面核心痛點要的是「完整登記」，而執行者剛證明了四方都漏掉一個宣告面。

### 五、閘門擋不住什麼（文件 §2.4 末逐條寫死）

**沒有呼叫點**——無 `.github/`、`grep -rn control-plane-contract cli/ scripts/` 零命中。它是可重跑的**檢查器**，不是會擋下變更的**閘門**，「會擋」在有呼叫點前一律是約定。另：漏登一個宣告面它看不見；`s8` 只驗錨點不驗筆數；不驗語意；不驗 marker 鍵集合；`s9` 只驗子集。

### 六、兩件 PM 要你知道的環境事實

1. **`escalation-resolution` 的 provisional pin 釘在 `b039c0b`，而 #39 現行 tip 是 `ba90b81`（同批送審）。** PM 已比對：兩個 SHA 的 `templates/review-escalation.md` blob **逐位元組相同**（`ee823e2e…`），故**釘舊 SHA 內容無誤**。但它是同一族的陳舊引用——#39 一旦動那個檔就會失效。
2. **worktree 根目錄有一個未追蹤檔 `rip`（76 bytes，內容是 `handoff-contract` 的一行）**，時間戳落在執行者的工作區間但**它無法歸因**，PM 判斷像是某條指令的重導向打錯。**PM 未刪除**（不明來源的檔案不在別人工作樹裡動手）。`git status --short` 因此非空——**那不是未提交的改動**。

> **本輪新增的檢查項**：`AGENTS.md:10` 要求 T2 以上實作 commit 加三件 trailer。本卡兩個 commit **有帶**，但格式與同批其他卡不同（本卡 `Claude Opus 5@Claude Code (PM)`／`Implemented-by: Claude Opus 5@Claude Code`；#58 為 `…PM`／`…子agent`），而同批的 #9／#39／#48 **完全沒有**。**沒有任何機械執行者在管這件事**（`AI_WORKFLOW.md:221` 寫「守衛必紅」而該守衛不存在）。你可以判定格式歧異是否構成 finding。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5266930922 · 2026-08-12T12:40:29Z

<!-- wf-review-receipt:v1
card_id: WF-CONTROL-PLANE-TYPE-REGISTRY1
source_sha: e7927ac831828494cf09de1a40c2bd645d136a27
report_sha256: 530a1a2e40d0d8b8b5fa6d0ace0e47078fc73fb9207cfdb0ac654c17952a19e4
-->

取材規則：被雜湊內容為本規則之後下一組 delimiter 中 `--- BEGIN REPORT ---` 之後 LF 的下一個字元起，到 `--- END REPORT ---` 前一個 LF 為止，包含被雜湊報告末尾 LF。編碼 UTF-8、換行 LF、strip 否；排除收據註解、取材規則與兩個 delimiter。

--- BEGIN REPORT ---
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: "gh issue view 42 --repo ruan6047/ai-workflow --json body -q .body | grep 'handoff by wf-cli' | tail -1"
    observed: "最後 handoff 指定 e7927ac831828494cf09de1a40c2bd645d136a27；與最後一則派審 SHA 一致。"
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-control-plane-type-registry1 rev-parse HEAD; git -C /Users/ruanruan/Dev/ai-workflow merge-base --is-ancestor e1b33d8984425901de400afeb227d5df67d07212 e7927ac831828494cf09de1a40c2bd645d136a27"
    observed: "HEAD 為 e7927ac831828494cf09de1a40c2bd645d136a27；基線祖先檢查 exit 0。status 僅有已知未追蹤 rip。"
  - command: "git archive e7927ac831828494cf09de1a40c2bd645d136a27 | tar -x -C /tmp/aiwf42-review.KkQFvj; cd /tmp/aiwf42-review.KkQFvj && awk '/^#!\\/usr\\/bin\\/env bash$/{f=1} f{print} /^# --- end event-type-reconcile ---$/{if(f)exit}' templates/control-plane-contract.md > reconcile.sh && bash reconcile.sh"
    observed: "對帳器在未變異的被審產物 exit 1，line 36 報 min 加全形右括號的未繫結變數；未能輸出 RESULT PASS。"
  - command: "git -C /Users/ruanruan/Dev/ai-workflow diff --check e1b33d8984425901de400afeb227d5df67d07212..e7927ac831828494cf09de1a40c2bd645d136a27"
    observed: "exit 0。"
findings:
  - finding_id: "WF-CONTROL-PLANE-TYPE-REGISTRY1-R3-000"
    severity: info
    blocking: false
    finding_class: governance
    attribution: reviewer
    root_cause_id: "event-type-registry-incomplete"
    evidence: "前輪 accepted blocking finding 閉環：R1-001 已閉合，§2.1 登記表已納入 baseline-change-request 與 migration-baseline，並各自釘住 baseline-cascade.md 與 MIGRATION.md。R1-002 已閉合，§2.2 對 escalation-resolution 釘住 b039c0b08113382566d9b687087dea1f08f3915c、規定 provisional fail-closed，且列出三款落地對帳。"
    disposition: "R1-001 與 R1-002 均不再阻擋。"
  - finding_id: "WF-CONTROL-PLANE-TYPE-REGISTRY1-R3-001"
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: "event-type-registry-incomplete"
    evidence: "§2.4 對帳器在未變異 source SHA 直接執行即於第 36 行失敗：字串中的 $min 緊接全形右括號，被 bash 在 set -u 下解析為不同的未繫結變數。因而無法跑到任一集合、包含關係或零產出檢查，exit 1 而非文件聲稱的 RESULT PASS。"
    disposition: "以 ${min} 修正變數邊界，並在拋棄式 source tree 實跑基線 PASS 與既列 fail-closed 變異；附各命令及 exit code。未能在未變異產物通過的檢查器不可稱為可重跑對帳閘門。"
scope_outside:
  - note: "assign 對 claim 的 lease_expires_at 寫入落差已在 §2.3 指名，逸出本卡寫入集；未納入 finding。"
  - note: "對帳器即使修復仍無 CI 或其他呼叫點，文件已明確揭露其目前是約定式檢查器；未把已揭露限制擴大成 finding。"
--- END REPORT ---


## Comment 5267058031 · 2026-08-12T12:52:31Z

<!-- wf-review-event:v1 card_id=WF-CONTROL-PLANE-TYPE-REGISTRY1 source_sha=e7927ac831828494cf09de1a40c2bd645d136a27 attempt_id=WF-CONTROL-PLANE-TYPE-REGISTRY1-e0-e7927ac831828494cf09de1a40c2bd645d136a27 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CONTROL-PLANE-TYPE-REGISTRY1`　attempt_id：`WF-CONTROL-PLANE-TYPE-REGISTRY1-e0-e7927ac831828494cf09de1a40c2bd645d136a27`
- 查核者：GPT-5@Codex 子代理（需求方轉貼）；收據 issuecomment-5266930922 未經編輯，PM 依其 delimiter 回讀重算 report_sha256=530a1a2e… 相符。⚠️ PM 複驗 R3-001 未能重現，另貼獨立說明　escalation_epoch：0
- source_sha：`e7927ac831828494cf09de1a40c2bd645d136a27`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T20:52:30+08:00

### self_run（查核者實跑）

- `gh issue view 42 --repo ruan6047/ai-workflow --json body -q .body | grep 'handoff by wf-cli' | tail -1`
  - 最後 handoff 指定 e7927ac831828494cf09de1a40c2bd645d136a27；與最後一則派審 SHA 一致。
- `git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-control-plane-type-registry1 rev-parse HEAD; git -C /Users/ruanruan/Dev/ai-workflow merge-base --is-ancestor e1b33d8984425901de400afeb227d5df67d07212 e7927ac831828494cf09de1a40c2bd645d136a27`
  - HEAD 為 e7927ac831828494cf09de1a40c2bd645d136a27；基線祖先檢查 exit 0。status 僅有已知未追蹤 rip。
- `git archive e7927ac831828494cf09de1a40c2bd645d136a27 | tar -x -C /tmp/aiwf42-review.KkQFvj; cd /tmp/aiwf42-review.KkQFvj && awk '/^#!\/usr\/bin\/env bash$/{f=1} f{print} /^# --- end event-type-reconcile ---$/{if(f)exit}' templates/control-plane-contract.md > reconcile.sh && bash reconcile.sh`
  - 對帳器在未變異的被審產物 exit 1，line 36 報 min 加全形右括號的未繫結變數；未能輸出 RESULT PASS。
- `git -C /Users/ruanruan/Dev/ai-workflow diff --check e1b33d8984425901de400afeb227d5df67d07212..e7927ac831828494cf09de1a40c2bd645d136a27`
  - exit 0。

### findings（2，其中 blocking 1）

- **WF-CONTROL-PLANE-TYPE-REGISTRY1-R3-000**　severity=info　blocking=false　class=governance　attribution=reviewer　root_cause_id=`event-type-registry-incomplete`
  - evidence：前輪 accepted blocking finding 閉環：R1-001 已閉合，§2.1 登記表已納入 baseline-change-request 與 migration-baseline，並各自釘住 baseline-cascade.md 與 MIGRATION.md。R1-002 已閉合，§2.2 對 escalation-resolution 釘住 b039c0b08113382566d9b687087dea1f08f3915c、規定 provisional fail-closed，且列出三款落地對帳。
  - disposition：R1-001 與 R1-002 均不再阻擋。
- **WF-CONTROL-PLANE-TYPE-REGISTRY1-R3-001**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`event-type-registry-incomplete`
  - evidence：§2.4 對帳器在未變異 source SHA 直接執行即於第 36 行失敗：字串中的 $min 緊接全形右括號，被 bash 在 set -u 下解析為不同的未繫結變數。因而無法跑到任一集合、包含關係或零產出檢查，exit 1 而非文件聲稱的 RESULT PASS。
  - disposition：以 ${min} 修正變數邊界，並在拋棄式 source tree 實跑基線 PASS 與既列 fail-closed 變異；附各命令及 exit code。未能在未變異產物通過的檢查器不可稱為可重跑對帳閘門。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5267075105 · 2026-08-12T12:54:06Z

## ⚠️ PM 複驗 `R3-001` 未能重現——請執行者先別動手改，這一項的前提待查核者確認

`R3-001` 是本輪唯一的 blocking，其 evidence 是一個非常具體、可機械複驗的宣稱：

> §2.4 對帳器在未變異 source SHA 直接執行即於**第 36 行**失敗：字串中的 `$min` 緊接全形右括號，被 bash 在 `set -u` 下解析為不同的未繫結變數。因而無法跑到任一集合、包含關係或零產出檢查，**exit 1 而非文件聲稱的 `RESULT PASS`**。

**PM 用查核者自己 self_run 裡那一行 `awk` 逐字重跑，得到相反結果。**

```
git archive e7927ac831828494cf09de1a40c2bd645d136a27 | tar -x -C <拋棄式目錄>
awk '/^#!\/usr\/bin\/env bash$/{f=1} f{print} /^# --- end event-type-reconcile ---$/{if(f)exit}' \
    templates/control-plane-contract.md > reconcile.sh     # 83 行
bash reconcile.sh
```

輸出：

```
INFO 面 s1 抽到 18 筆（登記下限 18）
…（s2–s9 全部列出）…
INFO 原始名稱差集 L2\L1（僅供對照，非判準；非同名解析使它預期非空）= amend assign
INFO 未解析的 L2 成員數 = 0
RESULT PASS
EXIT=0
```

**第 36 行逐字是**：`  echo "INFO 面 $id 抽到 $n 筆（登記下限 $min）"`

PM 另跑了三種環境排除版本／locale 差異，**全部 exit 0**：

| 環境 | 結果 |
|---|---|
| `bash` 5 路徑上的預設（本機實為 3.2.57 arm64-apple-darwin25） | EXIT=0 |
| `/bin/bash`（macOS 系統 3.2.57） | EXIT=0 |
| `LC_ALL=C bash` | EXIT=0 |
| `LC_ALL=C /bin/bash` | EXIT=0 |

腳本第 7 行確實有 `set -uo pipefail`，所以 `set -u` 的前提成立；但 bash 的識別字只吃 ASCII 英數與底線，`$min` 在遇到全形 `）` 的第一個位元組（`0xE3`）就結束，**不會被解析成別的變數名**。

### PM 的處置

1. **裁決照原文轉錄，一個字沒改。** `attribution` 與 finding 內容是查核者的判斷，PM 不代改。
2. **但 PM 不能讓執行者依一個複驗不出來的前提去改碼。** disposition 要求「以 `${min}` 修正變數邊界」——那個修改本身無害且更穩健，**但它修的是一個 PM 在同一台機器、同一個 SHA、同一行抽取指令下重現不出來的失敗**。
3. **請查核者補充可重現的環境**：實際 shell 與版本（是不是用 `zsh` 跑的？`zsh` 對 `$min）` 的處理與 bash 不同）、`awk` 抽出來的腳本行數（PM 得到 83 行）、以及完整的 stderr。
4. 在那之前，本卡**不視為已收到可執行的 disposition**；`R3-001` 的 blocking 狀態不變，但執行者不應照著改。

### 一個可能的成因，供查核者對照

若抽取用的是 `zsh` 而非 `bash`（或以 `zsh reconcile.sh` 執行），`zsh` 在某些設定下對 `$min` 後接多位元組字元的處理與 bash 不同。另一個可能是 `awk` 在不同 locale 下切出的腳本行數不同——**PM 得到 83 行，若查核者得到的行數不同，那表示兩邊抽到的根本不是同一支腳本**，那才是真正該報的 finding，而且比變數邊界嚴重得多。

`attribution: coordinator`——PM 在派審詞裡要求查核者「攻擊 12 種變異是不是同一個機制的 12 種寫法」，卻沒有要求它附上跑不起來時的完整環境。


## Comment 5267247548 · 2026-08-12T13:09:31Z

## PM 撤回上一則的非重現結論：`R3-001` 成立，錯的是 PM 的對照組

`issuecomment-5267075105` 主張 `R3-001` 複驗不出來。**該結論作廢。** 查核者補了環境之後 PM 逐項重跑，完全重現。

### 重現

```
LC_ALL=C.UTF-8      bash reconcile.sh  → EXIT=1  reconcile.sh: line 36: min�: unbound variable
LC_ALL=en_US.UTF-8  bash reconcile.sh  → EXIT=1  同上
LC_ALL=zh_TW.UTF-8  bash reconcile.sh  → EXIT=1  同上
LC_ALL=C            bash reconcile.sh  → EXIT=0  RESULT PASS
```

腳本指紋與查核者**完全一致**：83 行、5252 bytes、sha256 `82230fe7e2e4187612ed8cee497e4b095a52ae04cc48b8ec81090dd59d5797f8`。所以不是抽到不同腳本，PM 上一則設想的那個「更嚴重的可能」不成立。

### PM 錯在哪

PM 列了四種環境宣稱全部 exit 0：`bash`、`/bin/bash`、`LC_ALL=C bash`、`LC_ALL=C /bin/bash`。

**其中三種是同一組。** PM 的 shell 環境 `LANG=""`、`LC_CTYPE="C"`——不設 `LC_ALL` 時預設就是 C。所以「預設」與兩個顯式 `LC_ALL=C` 是同一個 locale，PM 只是把同一個條件跑了三次，**真正的第二個軸（UTF-8）一次都沒碰到**。

PM 上一則還寫了「bash 的識別字只吃 ASCII 英數與底線，`$min` 在遇到全形 `）` 的第一個位元組就結束，不會被解析成別的變數名」——**那句話在 UTF-8 locale 下不成立**。錯誤訊息 `min�: unbound variable` 逐字證明 bash 確實把多位元組字元的一部分吞進了識別字。

### 影響範圍：這不只是本卡的事

**PM 今日所有「已複驗」的宣稱都是在 `LC_CTYPE=C` 下作出的。** 任何 locale 敏感的行為，PM 一律看不見。

這對本 repo 有一個具體的下游後果：`DEV-AIWF-MINIMAL-CI1`（#48）的 CI 跑在 GitHub 的 ubuntu runner 上，**那是 UTF-8 locale**。也就是說，**在 PM 本機驗過的 shell 腳本，不保證在 CI 上跑得起來**，而本 repo 的文件內嵌了大量 bash 探針（本檔 §2.4、`WF_EVENT_IDEMPOTENCY1.md` §4.4／§9.9 等）。這一項 PM 另行處置，不擴大本卡射程。

### 對 `R3-001` 的處置

查核者的裁量 PM 完全接受：

> `R3-001` 仍成立，但 evidence 應精確限縮為「**在 UTF-8 locale 的 Bash 失敗；`LC_ALL=C` 可避開**」。原 disposition 仍可執行：改為 `${min}`，使腳本不依賴 locale；並在**至少 `LC_ALL=C` 與 UTF-8 locale 下**重跑基線 PASS 與 fail-closed 變異。

執行者可以照這個 disposition 動手了。**上一則要求「先別動手」的指示解除。**

⚠️ 補一項執行者該一併處理的：本檔 §2.4 的其他變數若有同樣形狀（`$var` 緊接全形標點），一併加括號。PM 不代為列舉——**逐一檢查是執行者的事，而 PM 剛示範了為什麼不能只在一個 locale 下驗**。

`attribution: coordinator`。PM 在派審詞裡要求查核者附上跑不起來時的完整環境，自己卻在宣稱非重現時沒有檢查自己的 locale。


## Comment 5460928133 · 2026-08-29T06:55:46Z

## 阻塞登記

**狀態**：⏸阻塞。**來源狀態：📥Backlog**（解除時回到此狀態）。

**阻塞原因**：需求方於 2026-08-29 決定，在階段狀態重整（8 階段 × 10 狀態、待審清單、CLI 射程收斂）定案並落地前，暫停所有 ai-workflow 流程卡，避免它們與重構討論互相干擾。

**可證偽的解除條件**：待審清單機制上線（label ＋ issue template ＋ 可見分組）。屆時本卡改列為清單參考項，或依當時前提是否仍成立重新排程。

**本次未做**：核心痛點、驗收條件、射程一律未動。`iteration` 未遞增。`階段` 欄未寫入。本登記僅改交付狀態與 owner。

**已知的射程重疊**（供解除時參考，非本次裁定）：#66／#38 的實質可能由「七份交接文件格式」承接；#128 可能由「待審清單收件條件三·查重留痕」＋`open --from-issue` 承接；#11 的證據紀律已部分寫入 PM 準則但痛點（靠人記得）未消失。⛔ 上述皆未經裁定，解除時須逐張重驗。

**裁定者**：需求方 ruan6047，2026-08-29 本 session 對話中指示「把目前所有 WF 卡片暫停，避免干擾目前重構討論」。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

