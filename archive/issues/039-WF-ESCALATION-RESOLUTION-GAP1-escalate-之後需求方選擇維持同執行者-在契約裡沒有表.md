# #39 WF-ESCALATION-RESOLUTION-GAP1 escalate 之後需求方選擇維持同執行者，在契約裡沒有表示法
- state: closed  created: 2026-08-12T02:54:23Z  closed: 2026-08-21T10:08:34Z
- url: https://github.com/ruan6047/ai-workflow/issues/39
- comments: 23

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；契約條文設計，須把一個真實但未被表示的治理狀態納入既有 escalation 狀態機而不破壞既有 replay；推理鏈中等，須逐條對照 review-escalation.md 既有欄位與 #9 的 writer 相依。）　查核：待指派（建議 主力型；紅線：本卡補的正是 PM 自己被逼著自創欄位的缺口，查核者須跨模型家族以避免 PM 自我背書；查核重點在新表示法是否會讓既有六則不合規 checkpoint 被追溯正當化。）
- Initiative：—　spec 基線：自 WF-22-CLI4（#9）2026-08-12 的執行前評估切出。該評估逐則比對 PM 手寫的六則 checkpoint 與契約 §5，發現四個未定義鍵，其中三個是 PM 的錯誤（分類錯誤／差一／不可機械核對），但 escalation_resolution 是契約真缺。需求方同日裁定：補進契約，另開卡承接。
- DB：db_scope=none
- 服務的原始目標：讓 escalation 狀態機能表示真實發生過的治理決定，而不是逼寫入者自創欄位

## 簡介
<!-- card-brief:begin -->
為「升級條件成立、checkpoint 判 escalate，然後需求方裁定 continue 並維持同執行者」這個契約沒有表示法的真實治理狀態設計表示法並寫進 templates/review-escalation.md，使 replay 僅憑事件流即可重建「該輪維持同執行者且是誰決定的」；授權條款須誠實標註本 repo 只有一個人類帳號、§4 (a′) 是結構性成立而非實質成立。**適用時機**：checkpoint 要記一個既非 replan 也非 change-executor 的結果，而寫入者只能自創欄位時；或要查「一次 continue 的效力涵蓋幾個 attempt」的裁定時。⛔ 非射程：不追溯正當化既有六則自創 escalation_resolution 鍵的不合規 checkpoint；型別登記進 control-plane §2 歸 aiwf#42；checkpoint writer 實作歸 aiwf#9。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：templates/review-escalation.md §4 規定升級條件成立時 checkpoint_decision 只能是 escalate，而 escalation-epoch-change 的理由只有 replan 與 change-executor 兩個。但 2026-08-12 在 #24 與 #25 上真實發生的是第三種：條件成立、checkpoint 判 escalate，然後需求方裁定 continue 並維持同執行者。契約對這個結果沒有任何表示法，PM 因此在六則 checkpoint 上自創了未定義鍵 escalation_resolution 來記它。後果有兩層：一是該事實只存在於自由文字，任何 replay 都重建不出來；二是 #9 的 checkpoint writer 若照契約嚴格實作就寫不出這個真實狀態，若沿用 PM 的自創鍵就是用實作既成事實反推契約——兩條路都錯。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:templates/review-escalation.md",
    "file:scripts/replay_escalation_rules.py",
    "file:docs/CONTRACT_TOOL_RECONCILE.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 為「條件成立、需求方裁定維持同執行者」設計表示法，並說明它與既有 replan／change-executor 的關係：是 escalation-epoch-change 的第三個理由，還是 checkpoint 上的獨立欄位，或是一個新的事件型別。三者的 replay 後果不同，須逐一比較後選一個並論證。
- [ ] 須裁定該決定的授權要求。它移除的是一個紅線閘門（升級門檻觸發後本應換執行者或重新規劃），故不得由 PM 自行記錄。但本 repo 只有 ruan6047 一個人類 GitHub 帳號，執行者與查核者根本不是 GitHub 帳號（是「Claude Opus 5@Claude Code（子 agent）」這類自由文字）——§4 (a′) 那套平台身分綁定在此是結構性成立而非實質成立。請誠實處理這個限制，不得寫出一個看似有授權檢查但實際恆真的條文；若結論是今天買不到實質授權，就寫成約定並指名它何時才會生效。
- [ ] 須明確處理「同一組事實被沿用到下一輪」的情形。#24 的第六個 checkpoint 逐字寫著「沿用需求方同日對同一組事實的 continue 裁定」——一次裁定被沿用到後續 attempt。契約須裁定：一次 continue 的效力涵蓋幾個 attempt、沿用是否需要重新表態、以及「若本輪查核產生第五次同家族 finding 須重新裁定」這種條件式效力要不要納入表示法。
- [ ] 不得追溯正當化既有六則不合規 checkpoint。那六則缺三個必填欄（escalation_epoch／trigger_attempt_id／unique_attempt_count）、多出四個未定義鍵，其中 counts_toward_escalation 是分類錯誤、attempts_so_far 差一、decided_by 的值有時不是帳號。新表示法只約束此後寫入；既有六則的處置（改寫還是標為 legacy）須明確裁定，且事後補一則自稱當時作出的裁定是本專案明令禁止的形態。
- [ ] 須指名對 #9 的介面：#9 的 checkpoint writer 在本卡落地前遇到該情形應 fail-closed 並指名等待本卡，不得靜默沿用未定義鍵。本卡落地後 #9 須據此更新。

## 驗證

- [ ] 以 replay 驗證：構造一條「條件成立 → escalate → 需求方 continue → 下一輪」的事件序列，證明僅憑事件流可重建出「該輪維持同執行者且是誰決定的」。若重建不出來，即為表示法不足。
- [ ] 既有六則 checkpoint 逐則以新條文判定，輸出每則的合規狀態與缺項，由指令輸出產生而非人工聲明。
- [ ] 授權條文若含機械檢查，須附一個「今天會恆真」的誠實標註與其失效條件；若無機械檢查，須逐字寫成約定並指出無執行者。
- [ ] templates/review-escalation.md 既有的 replay 腳本（scripts/replay_escalation_rules.py，65/65）不得退化；新增條文須有對應的新案例。
## Log

- 2026-08-12T10:54:22+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-12T11:00:39+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；分支worktree claude/WF-ESCALATION-RESOLUTION-GAP1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1；交付狀態 🚧進行中；實際能力層級 主力型（與卡面建議 主力型 相符）。
- 2026-08-12T11:23:27+08:00 amend by wf-cli（op 309677b0）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:templates/review-escalation.md" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:templates/review-escalation.md、file:scripts/replay_escalation_rules.py」；理由 需求方 2026-08-12 批准擴充：加入 scripts/replay_escalation_rules.py。執行者於 058100ad 交付後回報，新增的 escalation-resolution 條文目前只有 scratchpad 的構造 replay（16 條斷言）佐證，repo 內沒有回歸守衛，正式案例（正例重建、continued_owner 缺項對照、owner 雙相檢查、carried-forward 三項比對、連續沿用、authorization_binding 三態）須併入該腳本才有機械保證。不批的話新條文是紙上規則，任何後續改動都不會有東西轉紅。該檔目前無任何活卡宣告，且既有 65/65 已驗證改前改後皆通過、未退化。第三項（templates/control-plane-contract.md 的 type 列舉登記）不併入本卡——review-marker-clearance 也不在該列舉裡，是既存的同型落差，需求方裁定另開小卡一併處理兩者。。
- 2026-08-12T12:02:37+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA 41a9f419df9c375b5df45a72c2ff5439edce0fa8；證據 R1：058100ad 於 templates/review-escalation.md 純新增 +67/-0（§4 末「escalate 之後的第三種結果」整節 ＋ §5 新增 escalation-resolution schema 與七款必要條件）；41a9f41 將構造 replay 併入正式腳本 +517/-9（需求方批准擴充寫入集，op 309677b0）。

表示法三選一的論證：（甲）escalation-epoch-change 第三個理由——否決，該事件定義即遞增 epoch 而新 epoch 從零計數，一次 continue 會抹掉本 epoch 的 occurrence 累計、重界 carry set、消滅 defer 清償義務，比缺口更糟（缺口只是記不下來，甲案是記錯）；實例可證：#24 第二則 checkpoint 之所以再次強制 escalate 正因家族計數仍為 4，走甲案該訊號當場消失。（乙）checkpoint 上的獨立欄位——否決，把機械可導的告警與需等人的裁定綁進同一則事件，只有兩種寫法：等裁定到了才寫（使機械判定成為人類裁定的人質，且「條件已成立但尚無人裁定」無表示法，並把漏建誘因制度化——本 repo 已漏建兩次、成因正是此）或先寫再編輯（湮滅原文，§5 已否決）。（丙）新事件型別——採用，兩則之間的區間就是升級狀態本身。

授權款誠實標註：需求方帳號同屬 writer 集合、且執行者查核者根本不是 GitHub 帳號時，author 比對與 owner/reviewer 排除恆真且分不開任何兩方。故不寫成看似有檢查的條文，而要求 adapter 導出 authorization_binding: substantive | structurally-vacuous，把恆真本身寫進事件流；今天恆為後者（replay 機械驗出），失效條件為需求方帳號脫離 writer 集合或執行者查核者取得可逐字比對的平台身分，在那之前該段是約定。今天確實會 FAIL 的三件：裁定須為獨立留言（既有七則全是寫在被裁定文本內，此款打掉它們）、body 須逐字含本輪 trigger_attempt_id（內含 source SHA 故免時鐘新鮮性）、1:1 解除與沿用上限。

沿用：一次裁定效力恰好涵蓋一則 checkpoint；沿用須重新發事件且以 resolution_basis: carried-forward ＋ carried_by／resolved_by 分開，使二手事實不能寫成一手；條件式效力改為機械判準（強制成因集合相同 ＋ 第一條件根因 occurrence 累計數相同 ＋ 第二條件觸發集合為子集）；不得連續沿用。

既有 checkpoint 逐則機械判定（gh api 取原文，非人工聲明）：受檢七則（#21×1、#22×2、#24×3、#25×1），全部缺三個必填欄、多出未定義鍵，帶 escalation_resolution 者五則、其新條文下十個必填欄一個都不存在，attempts_so_far < 3 者兩則（#22 5255216570、#25 5256475572）。⚠️ PM 的派工詞說「六則」與「一則」，執行者按實際七則與兩則判並依指示未對齊派工詞——PM 已認錯。處置：全部標 legacy，不改寫不重發不追溯補建。

replay：87/87 exit 0；改前 65 條逐字與順序未動且全 PASS（抽出斷言區段逐行 diff 證明），新增 22 條全部追加在後。併進同一個事件層引擎而非另起第二個。第 3 組做實：同一條違規事件流跑兩次，two-phase 出現 structural 違規、draft-single-phase（初稿）因對尚不存在的下一個 attempt 求值而恆真、完全不擋——差異本身即斷言。E4 的失效款次隔離到恰為 ruling_is_standalone（既有七則的形態）。E7 用途是證明授權款今天沒有實質保證而非證明它有。

執行者撤回一項自陳（carried-forward 三項比對現跑在正式引擎、有回歸守衛，不再是紙上規則），並新增明列 E 段未打掉任何案例的六款（one_to_one、resolution_value、carried_source_unused、carried_by_recorded、trigger_matches／epoch_matches、auth_binding_derived），不宣稱條件都驗過了。

⚠️ 對 #9 的介面須查核者知悉：§5 第 3 款雙相 continued_owner 的後半今天仍無執行者。#9 已於 78d4064 補上 owner 時點快照，但執行者查碼證明該快照裝的是查核者而非產出 source_sha 的執行者（handoff --next-stage review --to <查核者> 先設 owner 欄，裁決在其後才寫），拿去比對會系統性誤報。詳見 #9 的 issuecomment-5262093113。

寫入集實際觸及兩檔零逸出，marker 字面 0 處，__pycache__ 未提交。執行者自陳兩項無機械執行者：「共用引擎 ⇒ 證的是同一套規則」這一步無機械檢查（根據是既有 65 條逐字不動且全 PASS，那是必要非充分）；「六款未涵蓋清單是完整的」是人工聲明，未寫必要性窮舉器。。
- 2026-08-12T13:02:00+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5262443238 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=4d6325a7… 一次相符。PM 的轉錄調整：自結構化區塊末截斷「## 範圍外發現」以下的散文段落，該段已完整保存於收據的雜湊範圍內；區塊內字串逐字未變）；core_pain_resolved yes；self_run 5 項；findings 1 項（blocking 1）；attempt WF-ESCALATION-RESOLUTION-GAP1-e0-41a9f419df9c375b5df45a72c2ff5439edce0fa8。
- 2026-08-12T13:02:19+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 1；SHA 41a9f419df9c375b5df45a72c2ff5439edce0fa8；證據 R1-001（major，blocking，implementation，attribution=executor，root_cause_id=resolution-authorization-binding-not-validated-against-event）：§5 規定 authorization_binding 必須由 adapter 導出，手填、缺欄或省略即本則無效；但 replay_escalation_rules.py:496-504 的 RES() 建構事件不含此欄而 E1 仍輸出 VALID，:726-727 僅檢查 derive_authorization_binding(ctx) 的回傳值屬枚舉、沒有比較事件欄位，故無法拒絕缺欄或偽造值。

disposition：令 resolution fixture 與 replay 的 event schema 明確承載 authorization_binding，並驗證其存在且逐字等於 adapter 導出值；新增缺欄、手填 structurally-vacuous 與手填 substantive 的獨立反例，均須使 resolution 無效。

⚠️ 這一條打在執行者自己最強調的那個設計上：它主張「不寫成看似有檢查的條文，而是把恆真本身寫進事件流」，並以 E7 宣稱該款的誠實性已被證明。查核者指出 replay 從未驗證事件真的承載了那個值——條文要求 adapter 導出，測試卻只驗 adapter 函式的回傳值落在枚舉內。設計正確（core_pain_resolved=yes）但兌現不完整。

查核者確認的正面事實：core_pain_resolved 判 yes；寫入集僅兩檔；87/87 通過且 py_compile 通過；E3 的 two-phase 對照確實在 owner 不符時產生 structural 違規而 draft-single-phase 對照沒有（該對照成立）；並獨立讀取 #21／#22／#24／#25 的既有 checkpoint 確認本卡對 cutover 前事件採 legacy、不改寫、不重發、不追溯補建，未把新 type 反向正當化歷史事件。

scope_outside 兩項（非 finding）：escalation-resolution 尚未登記至 control-plane-contract.md 的 type 列舉、亦無 checkpoint writer，被審文本已明確交由 #42 與 #9 承接；§5 第 3 款的 continued_owner 雙相語意依賴 #9 寫入端取得真正產出 source_sha 的執行者 owner，本輪未把 #9 現有的 reviewer snapshot 當成可用 owner 證據。。
- 2026-08-12T13:13:24+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 1；SHA b039c0b08113382566d9b687087dea1f08f3915c；證據 R2：R1-001 已處置。執行者接受 finding 並指出病灶比查核者所述更深一層——不只是「只驗回傳值屬枚舉故恆真」，還有**加蓋時點在校驗之後**，於是被校驗的值與消費者讀到的值不同源；那才是該款從未被驗到的機制。它並自述「我寫了整整一節論證不得寫出看似有檢查、實際恆真的條文，然後在自己的測試裡放了一條」。

契約側（§5 第 7 款）：authorization_binding 改為 adapter **加蓋**的欄位，提交面不得含此鍵，**含即無效即使其值恰好等於導出值**——「值恰好對」不是「由 adapter 導出」，本款驗來源不驗值。援引 counts_toward_escalation 為同形先例（PM 已核對 #9 分支 review.py:61 的 WRITER_ONLY_KEYS 確含該鍵，引用屬實）。

腳本側：來源顯式建模（_binding_source ∈ adapter／writer／無），加蓋時點移到校驗之前，投影直接用已加蓋的事件。原一款拆三款：auth_binding_present 擋缺欄、auth_binding_not_hand_filled 擋提交面自帶（驗來源）、auth_binding_matches_derived 擋值不符。

三個反例的失效款次（實測輸出）：缺欄→[present, matches_derived]；手填 structurally-vacuous（同值）→**[not_hand_filled] 恰為一款**；手填 substantive→[not_hand_filled, matches_derived]。對照組以 41a9f41 的 enum-only 寫法跑同三例→[True, True, True] 全放行。

⚠️ PM 已獨立驗過那條分水嶺斷言（scripts:1894-1897），它同時斷言 auth_binding_matches_derived is True **與** 導出值逐字等於手填值——兩者缺一，「只驗值抓不到」就只是碰巧一起紅。這正是 PM 在派工詞裡點名最容易做成假綠的那一條，執行者做實了。

執行者刻意不把缺欄做成單款隔離：缺欄時 matches_derived 一併失效（None ≠ 導出值），它如實斷言兩款，並說明要做成單款只能讓 matches_derived 在欄位不存在時判 True——「那就是該物不存在時條件恆真，正是本卡通篇在反對、也正是這次被打的形狀。不為了整齊再犯一次」。

退化檢查：既有 87 條逐行 diff，只有 E1 一條措辭更新（加驗來源後改寫敘述，仍 PASS），其餘 86 條逐字未動且全 PASS；新增 7 條（E8）。總計 94/94、FAIL 0、exit 0、py_compile 通過。PM 已複驗 review-escalation.md 無節標題增刪，故 #38 與 #9 對 §3／§4／§5 的引用不受影響。

六款未涵蓋清單如實更新：本輪關掉 auth_binding_derived（拆三款各有反例，從清單移除）；仍在清單的五項為 trigger_matches／epoch_matches／one_to_one／resolution_value／carried_source_unused／carried_by_recorded 中的五個，執行者指出前四項是本引擎定址方式導致的結構性恆真（與被打的那一款同型），carried_by_recorded 純粹是沒寫案例，並自陳上一輪說要做的必要性證明器**這一輪仍然沒做**，只補了被 finding 點名的那一款。

scope_outside 兩項照裁定未動：type 列舉登記與 checkpoint writer 交由 #42／#9，契約內劃界文字未改；§5 第 3 款的 continued_owner 未因 #9 於 779e575 加了 owner 欄而改寫——依 PM issuecomment-5262093113 的裁定該快照裝的是查核者不是執行者，條文原樣保留。

執行者自陳兩項無機械執行者：pre-fix-enum-only 對照組是它對舊碼的模型不是舊碼本身（已引 41a9f41:726 原文與「RES() 不含該欄」佐證模型忠實，但等價性無機械檢查，因舊檔無 hand_filled 參數故無法整份載入跑同組 fixture）；契約說「提交面不得含此鍵」但本 repo 沒有任何寫入端在執行它（#9 未完成），腳本裡的 _binding_source 是 fixture 宣告的、不是從真實 payload 觀察到的——規則層有守衛，寫入層沒有。

寫入集兩檔零逸出，marker 字面 0 處，工作區乾淨。。
- 2026-08-12T18:43:44+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5265393753 未經編輯，PM 依其取材規則回讀重算 report_sha256=68c3b589… 一次相符。PM 的轉錄調整：自結構化區塊末截斷「前輪 accepted blocking finding 閉環」以下的散文段落，該段已完整保存於收據雜湊範圍內；區塊內字串逐字未變）；core_pain_resolved yes；self_run 5 項；findings 1 項（blocking 1）；attempt WF-ESCALATION-RESOLUTION-GAP1-e0-b039c0b08113382566d9b687087dea1f08f3915c。
- 2026-08-12T20:00:02+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 1；SHA ba90b81a52172a64c44702d70c93ca5835ddd0ad；證據 R3：R2-001 已處置。執行者指出病灶是定址而非守衛——舊 RES() 只有一個 key checkpoint_trigger，replay 用它取 cp、_resolution_conditions 再拿同一個 key 跟 cp.trigger 比，同源比對故 cp 取得出來時恆真、取不出來時 bool(cp) 已先擋掉，錯誤 trigger 在該 fixture 裡根本表達不出來。把定址與宣稱分離後才可能為假。五種反例逐一隔離到恰為一款：錯誤 trigger→trigger_matches；錯誤 epoch 分兩條路徑（宣稱不符、跨 epoch 補發）→epoch_matches 的兩個合取項；重複解除→one_to_one（第二則刻意附另一則完全合規的獨立裁定留言，故留痕五款皆成立）；列舉外 resolution→resolution_value；同一 fresh-ruling 第二次沿用→carried_source_unused；缺 carried_by→carried_by_recorded。⚠️ 它另窮舉出查核者點名六款之外還有四款既未涵蓋也未列入清單（checkpoint_is_escalate、resolved_by_is_requester、ruling_url_on_card、carry_forcing_set_identical），各補一個隔離反例。刪掉人工清單 E_NOT_EXERCISED，改為 resolution_clause_coverage() 掃 resolution_audit 機械彙總，並反向測試該彙總器（拿掉三個登記會如實印出未涵蓋並 exit 1），另斷言 set(RESOLUTION_CONDITIONS)==set(audit keys) 防止款名寫錯虛報涵蓋。replay 94→114，既有 94 條零退化。PM 自審：遠端 tip 相符、b039c0b 是祖先（非 force）、對 main merge-tree CLEAN、本輪寫入集僅 scripts/replay_escalation_rules.py（+388/-28）零逸出、拋棄式副本重跑 114/114。⚠️ 執行者主動記四件證明不了的事，其中第 3 件最該看：resolution_basis 落在列舉外時 §5 第 5、6 兩款會整批退化為恆真，本則仍被 resolution_value 擋下故 fail-closed 成立但只剩一層；它未改條件式結構（超出 disposition），改以會 FAIL 的斷言把該形狀釘住。⚠️ commit 缺 AGENTS.md:10 要求的 trailer（今日全批問題，另卡已判 blocking）。。
- 2026-08-12T20:51:18+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼）；⚠️ 本卡收到三則收據 issuecomment-5266870914／5266877703／5266881324，PM 逐一驗算：三者被雜湊內容逐位元組相同（sha c0f251a6…），為同一份報告的重試，無歧義；轉錄採最後一則 5266881324；core_pain_resolved yes；self_run 5 項；findings 2 項（blocking 2）；attempt WF-ESCALATION-RESOLUTION-GAP1-e0-ba90b81a52172a64c44702d70c93ca5835ddd0ad。
- 2026-08-12T23:12:22+08:00 handoff by wf-cli → owner 待指派；iteration 2；SHA ba4755f4f2e33436d8128a9d68498250540f0cbb；證據 依 docs/ROADMAP.md（main ba4755f）§0／§3 降級：本卡屬目標 3（治理精緻化）。#58 解決的「兩份事件型別語彙互不知情」今天 0 寫入端 0 讀取端、不可能造成錯誤裁決（其執行者自己的論證）；#39 的授權款依 §1 收斂——身分只需角色＋模型的宣告欄位，不追求驗證，故其 authorization_binding 的 substantive/structurally-vacuous 設計為過度工程。⚠️ 降級不是關閉，載有的真實 finding 紀錄全數保留、可逆。⚠️ 未閉合的 blocking 維持未閉合，本次降級不視為驗收。。
- 2026-08-21T15:37:38+08:00 amend by wf-cli（op 89dca46f）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:templates/review-escalation.md", "file:scripts/replay_escalation_rules.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:templates/review-escalation.md、file:scripts/replay_escalation_rules.py、file:docs/CONTRACT_TOOL_RECONCILE.md」；理由 需求方 2026-08-21 事前擴權（前瞻性授權，非事後揭露）：PR #116 讓 CI 首次在合併結果上跑，tests 轉紅——本卡文件引入 4 個契約符號（event/carried-forward、event/continue-same-executor、event/escalation-resolution、event/fresh-ruling）而 docs/CONTRACT_TOOL_RECONCILE.md 的處置表未登記，test_live_dispositions_cover_every_gap 斷言 55 個缺口不符（實際 58／登記 54）。該對帳器由 #97（6561e04）帶入，晚於本卡最後一輪查核（2026-08-12），故三輪查核抓不到不是查核疏失。補登記須寫該檔，先擴權再派工。零衝突：全 21 張 open 卡逐張查核卡面宣告，無任何一張宣告該檔。。
- 2026-08-21T15:38:33+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code（子代理）；分支worktree claude/WF-ESCALATION-RESOLUTION-GAP1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1；交付狀態 🔨執行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-21T16:10:45+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 2；SHA 28ac73b6c3a93e4939e3321f866a5997b55f67b0；證據 R4 交付。PR #116（https://github.com/ruan6047/ai-workflow/pull/116）：tests 在合併結果 refs/pull/116/merge 上 pass 40s、tests (branch head) pass 41s、mergeState CLEAN、未 merge。基線以 git merge-base origin/main HEAD 算得 39b53e41a8d6d2d05413e0581fb089cdadf3c2c2（非抄 origin/main）。

本輪射程：PR 首次讓 CI 在合併結果上跑，test_live_dispositions_cover_every_gap 轉紅（55 個缺口不符，實際 58／登記 54）——本卡文件引入 4 個契約符號而 docs/CONTRACT_TOOL_RECONCILE.md 未登記。該對帳器由 #97（6561e04）帶入 main，晚於本卡最後一輪（2026-08-12），故三輪查核抓不到不是查核疏失。執行者補登記 4 條處置（全為「補寫入者」）並把分支更新到 main。

R1–R3 四個 finding 今日複查全部閉環：R1-001 resolved（R2 報告）；R2-001 resolved（R3 收據 prior_round_closure status: resolved）；R3-001 缺 trailer 構造上免責（ba90b81 = 2026-08-12T19:20:36+08:00 早於 doctor.py:752 的 TRAILER_GUARD_EPOCH 2026-08-13T00:00:00+08:00）；R3-002 已由需求方 2026-08-12T12:59:26Z 裁定「接受本 attempt，缺漏記錄不追溯補建」。三輪皆 core_pain_resolved: yes。

PM 交付前自驗：寫入集零越界（diff 只有宣告的三檔）；三筆新 commit 皆帶 Requested-by／Planned-by／Implemented-by；四筆既有已查核 commit 的 SHA 未變（用 merge 非 rebase）。

⚠️ 兩項未閉、須查核者一併裁量：(1) 執行者用本地 merge 而 AI_WORKFLOW.md:229 §6.1 第 3 款寫「分支更新禁 gh pr update-branch…一律本地 rebase」——標的是禁那個按鈕，但該款自陳的危害「污染歷史與守衛判讀」在本地 merge 上同樣發生；執行者拒絕 rebase 的兩個理由 PM 已複驗成立（rebase 會讓 main 的 validation.py:783/:829 指向不存在的 058100ad，且 cli/src 在寫入集外改不了；rebase 重設 committer date 會把四筆免責 commit 翻成無法修的違規）。PM 查到先例：origin/claude/WF-22-CLI4（#9，已結案合併）分支上有 3 個基線更新 merge commit 且全部零 trailer，另 DEV-COMMIT-TRAILER-GUARD1 與 DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1 各 2 個——本地 merge 是既有慣例，只是它們全在 epoch 前故守衛未及。(2) merge commit b6900c6 缺 Reviewed-by，是全分支唯一違規；required_trailers(merge_clean) = (Reviewed-by,)，而該規則的形狀假設是「merge_clean ＝ 卡片合併」，b6900c6 是基線更新 merge、無人查核也無從查核。⭐ 執行者拒絕填捏造的查核者換守衛變綠，改在 commit 訊息明寫偏離。PM 建議以 squash 合併使該 commit 不落地，並把守衛的形狀缺口（不分辨卡片合併與基線更新）另記——但這是需求方／查核者的裁量，不是 PM 的裁定。

⚠️ 執行者自列未驗 8 項，全數轉入派審詞，其中關鍵三項：CI 綠不等於四條處置在語意上正確（--check 只比對 key→判定字串）；三個取值只做到 grep 在 cli/src 零出現、未窮舉其他字面形態；未讀 WF-22-CLI4 卡不知它是否真涵蓋該 writer。。
- 2026-08-21T16:28:03+08:00 contract-baseline by wf-cli → contract templates/review-escalation.md；宣告者 ruan6047；留言 https://github.com/ruan6047/ai-workflow/issues/39#issuecomment-5367425415。
- 2026-08-21T16:28:33+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex（需求方轉貼；收據 issuecomment-5367319357，PM 逐字轉錄）；core_pain_resolved yes；self_run 5 項；findings 1 項（blocking 1）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-ESCALATION-RESOLUTION-GAP1-e0-28ac73b6c3a93e4939e3321f866a5997b55f67b0。
- 2026-08-21T16:30:26+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子代理）；iteration 3；SHA 28ac73b6c3a93e4939e3321f866a5997b55f67b0；證據 R4 判 REQUEST_CHANGES（R4-001，major／blocking／governance），需求方已於 issuecomment-5367447565 下前向裁定，交回執行者做 R5。

裁定摘要：(1) trailer 那一半**不建立例外**，改為把「不適用」寫進事件——基線更新 merge 須帶 Reviewed-by: —（基線更新 merge，無查核對象）；依據是需求方 2026-08-12 記於 review.py:657-661 的「正解不是不寫，是寫下去、並把『這道閘門今天沒有鑑別力』寫在事件上」，同族既有實例為 authorization_binding: structurally-vacuous 與 escalation_account: not-asserted。(2) rebase 那一半建立狹義例外（兩項適用條件須同時成立），⚠️ 明文標注它**沒有機械執行者**、屬派工包層約定；⭐ **對 b6900c6 不追溯適用**——例外只免除「必須 rebase」，不免除任何 trailer。(3) 因此須重建分支。

⭐ PM 補的三項讀碼事實決定了上述形狀：(a) doctor.py:789-790 的 trailer_keys() 只回鍵、:915 的 missing 只比對鍵——守衛從不看值，故 merge commit 上的 Reviewed-by 從未證明過任何人查核了任何東西；(b) doctor.py:863-867 守衛作者已明文否決「基線更新 merge」是可導出的形狀（「誰是 main 取決於你站在哪個 ref 上看，那是脈絡不是 commit 自身的性質」），故任何以該概念為條件的 trailer 例外構造上不可能有機械執行者，而以 merge_clean 為條件會連帶豁免併入 main 的卡片 merge；(c) doctor.py:827 分流界線用 committer date，rebase／cherry-pick 皆重設之，會把四筆 epoch 前已查核 commit 翻成無法修的違規，且 rebase 會換掉 main 的 validation.py:783/:829 逐字引用的 058100ad。

⚠️ R5 不得 force-push（執行者上輪已回報被 harness 權限分類器擋下），改以新分支重建：自 ba90b81 開新分支（四筆已查核 commit 的 SHA 一個都不變）→ 帶齊四個 trailer 重做基線更新 merge → 取回 aeda16a／6d54318 兩筆文件 commit → push 新分支 → 改指或重開 PR。

⚠️ 兩項另案（不阻擋本卡）：AI_WORKFLOW.md §6.1.3 的例外條文屬跨專案 canonical 變更須另開卡，在該卡落地前本裁定即為該例外的權威出處；守衛的 Reviewed-by 只驗鍵存在使該欄在所有 merge commit 上都不具區辨力，比本 finding 更大，#63 已 CLOSED 無承接者。。
- 2026-08-21T16:45:09+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code（子代理）；分支worktree claude/WF-ESCALATION-RESOLUTION-GAP1-r5 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1-r5；交付狀態 🔨執行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-21T16:46:05+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 3；SHA ba4f1e2dbc149e4488075fe2015a34fa7e18fecd；證據 R5 交付。分支 claude/WF-ESCALATION-RESOLUTION-GAP1-r5，PR #117（https://github.com/ruan6047/ai-workflow/pull/117）。⚠️ PR #116 已關（GitHub 的 PATCH /pulls/{n} 構造上不接受 head 欄位，「改指」做不到；#116 comments 0／reviews 0，關掉不孤立任何留痕）。

本輪射程只有一件：依需求方 2026-08-21 前向裁定（issuecomment-5367447565）重建合規分支，解 R4-001。**內容一個字未改，本輪實際編輯檔案數為 0。**

PM 獨立複驗（非轉述執行者）：
- 最終樹與 R4 被審的 28ac73b6 逐位元相同：git diff --stat 無輸出；兩者 ^{tree} 皆為 9f9280ae9f9e4c46390405d6dd04a9dfc093efc7
- 四筆已查核 commit（058100ad／41a9f419／b039c0b0／ba90b81a）逐一 merge-base --is-ancestor 皆 YES，committer date 全部仍是 2026-08-12，早於 TRAILER_GUARD_EPOCH，免責不變
- doctor --commit-trailers --require-planned-by --commit-range origin/main..ba4f1e2d：**統計 違規 0／界線前 4／合規 4**（R4 被審的 28ac73b 同指令為 違規 1，b6900c6 缺 Reviewed-by）
- PR #117：tests pass 37s（合併結果）／tests (branch head) pass 41s；headRefOid=ba4f1e2dbc14；mergeStateStatus=CLEAN；state=OPEN
- 寫入集零越界：diff 只有宣告的三檔
- 舊分支 claude/WF-ESCALATION-RESOLUTION-GAP1 保留於 origin（058100ad 的可達性），本機舊 worktree 未動

⚠️ 兩項與派工包不同，須查核者裁量：
(1) 重放的是**三筆**今日文件 commit（aeda16a／6d54318／28ac73b → 新對應 1ebd089／83e3276／ba4f1e2），不是派工包寫的兩筆。⭐ **錯的是派工包**——PM 漏算了 28ac73b 本身也是文件 commit；只取兩筆會使最終樹不等於 28ac73b6，與驗收第一條直接衝突。執行者以驗收條款為準，判斷正確。三筆皆今日、post-epoch、帶齊三個 trailer，cherry-pick 重設 committer date 對它們無害（doctor 判合規）。
(2) 執行者未替新分支保留 worktree（理由：scratchpad 會被回收；放 .claude/worktrees/ 又會產生沒有卡註冊的 worktree，而它被禁止跑 wfcli 註冊）。**PM 已於交付後補建** /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1-r5 並以 assign 更新卡面欄位。

⚠️ 執行者自列未驗 7 項，全數轉入派審詞，其中最關鍵：未重跑 R1–R4 任何 finding 的複驗（R5 射程只有重建，內容未動）；**未讀 validation.py:783/:829 確認那兩行今天仍逐字寫著 058100ad**（只驗到該 SHA 目前可達）；⭐ **AI_WORKFLOW.md:229 仍逐字寫「一律本地 rebase」——該例外目前只存在於 issue 留言，查核者若只讀 canonical 會看到與本分支相反的規則**（需求方已裁定該條文屬跨專案 canonical 變更、另案處置，在該卡落地前本裁定即為權威出處）。

⚠️ Reviewed-by: —（基線更新 merge，無查核對象）在 git interpret-trailers --parse 與 %(trailers:only=true,unfold=true) 兩支都原樣吐出，全形括號與破折號未造成切斷。。
- 2026-08-21T18:04:37+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex（需求方轉貼；收據 issuecomment-5368428121，PM 逐字轉錄）；core_pain_resolved yes；self_run 4 項；findings 0 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-ESCALATION-RESOLUTION-GAP1-e0-ba4f1e2dbc149e4488075fe2015a34fa7e18fecd。
- 2026-08-21T18:08:20+08:00 handoff by wf-cli → owner ruan6047；iteration 3；SHA 2ae1ff0be3ae78f38392b81e1c5b3fe9409c79b8；證據 結案（2026-08-21，需求方授權 merge）：跨家族 APPROVE（GPT-5@Codex）／core_pain_resolved=yes／**findings 空**／R5 一輪過。**已 merge**：merge commit `2ae1ff0be3ae`，PR #117。

【⭐ 刻意用 merge commit 而非 squash，理由是一條會斷掉的引用】main 的 `cli/src/wf_cli/validation.py:783` 與 `:829` **逐字引用 `058100ad`**（R5 查核者已複驗那兩行今天仍在）。squash 會讓該 commit 不再是 main 的祖先、只剩舊分支可達，日後刪分支就可能被 GC。merge 之後 `git merge-base --is-ancestor 058100ad origin/main` → **YES**，永久留在 main 的歷史裡。⚠️ 這與本 repo 近期 12/12 squash 的慣例不同，是刻意偏離。

【這張卡走了五輪，前四輪的帳】R1-001／R2-001（`resolution-authorization-binding-not-validated-against-event` 家族，實作面）皆 resolved；R3-001（缺 trailer）構造上免責——`ba90b81` = `2026-08-12T19:20:36+08:00` 早於 `doctor.py:752` 的 `TRAILER_GUARD_EPOCH`；R3-002（coordinator 跳過 implementation handoff）由需求方 2026-08-12T12:59:26Z 裁定「接受本 attempt，缺漏記錄不追溯補建」。**五輪皆 `core_pain_resolved: yes`。**

【⭐ 為什麼會有 R4／R5：PR 開下去才第一次驗到合併結果】本卡 2026-08-12 走完 R3 後被批次 handoff `ba4755f4` 掃進 Backlog（**該筆的 evidence 文字寫的是 `#58` 的內容**，且把 iteration 撞到 2，違反十小時前才下的「iteration 維持 1」裁定——屬 `#84` 缺陷 2 的實例）。2026-08-21 PM 重啟並開 PR #116，讓 CI **第一次在 `refs/pull/N/merge` 上跑**，`tests` 立刻轉紅：本卡文件引入 4 個契約符號而 `docs/CONTRACT_TOOL_RECONCILE.md` 未登記（實際缺口 58／登記 54）。⭐ **三輪查核抓不到不是查核疏失**——該對帳器由 `#97`（`6561e04`）帶入 main，晚於本卡最後一輪。

【R4 的 finding 與需求方裁定】R4-001（major／blocking／governance）：`b6900c6` 是本地 merge（與 `AI_WORKFLOW.md:229` §6.1.3「一律本地 rebase」不符），且 shape 為 `merge_clean` 而缺 `Reviewed-by`。⭐ **查核者打掉了 PM 的 squash 建議**，逐字「它只避免 `b6900c6` 進 main，**不能使送審分支符合既有 preflight**」——PM 把問題當成 main 的歷史乾不乾淨，而它是被審 SHA 本身含不含違反。**PM 建議撤回。**

需求方 2026-08-21 前向裁定（issuecomment-5367447565）分兩半：
- **trailer 那一半不建立例外**，改為把「不適用」寫進事件：`Reviewed-by: —（基線更新 merge，無查核對象）`。⭐ 依據是三項讀碼事實：(a) `doctor.py:789-790` 的 `trailer_keys()` 只回鍵、`:915` 的 `missing` 只比對鍵，**該守衛從未驗過任何值**；(b) `doctor.py:863-867` 守衛作者已明文否決「基線更新 merge」是可導出的形狀（「誰是 main 取決於你站在哪個 ref 上看，那是脈絡不是 commit 自身的性質」），故該概念的 trailer 例外構造上不可能有機械執行者，而以 `merge_clean` 為條件會連帶豁免併入 main 的卡片 merge；(c) `doctor.py:827` 分流界線用 committer date，rebase／cherry-pick 皆重設之。原則出自需求方 2026-08-12 記於 `review.py:657-661` 的「正解不是不寫，是**寫下去、並把『這道閘門今天沒有鑑別力』寫在事件上**」。
- **rebase 那一半建立狹義例外**（兩項適用條件須同時成立），⚠️ **明文標注它沒有機械執行者**、屬派工包層約定，且**對 `b6900c6` 不追溯適用**。

【R5：只重建 commit 圖，內容一個字未改】⚠️ **不得 force-push**（執行者上輪試 amend ＋ `--force-with-lease` 被 harness 權限分類器擋下），改自 `ba90b81` 開新分支 `claude/WF-ESCALATION-RESOLUTION-GAP1-r5`。**本輪實際編輯檔案數為 0。**

證據（PM 與 R5 查核者各自獨立取得）：
- **最終樹與 R4 被審的 `28ac73b6` 逐位元相同**：`^{tree}` 皆 `9f9280ae9f9e4c46390405d6dd04a9dfc093efc7`，`git diff` 為空
- **四筆已查核 commit 未改寫**：`058100ad`／`41a9f419`／`b039c0b0`／`ba90b81a` 逐一 `merge-base --is-ancestor` 皆 YES，committer date 全部仍是 2026-08-12
- **`doctor --commit-trailers --require-planned-by`：違規 0／界線前 4／合規 4**（對照組 `28ac73b` 同指令為 **違規 1**）
- **新 merge 的樹是決定性的**：`git merge-tree --write-tree ba90b81 39b53e4` = `fd3ba233…` = `b6900c6^{tree}` = 新 merge 的樹，不是人工湊的
- ⭐ **R5 查核者補驗了 PM 標紅的那一項**：`validation.py:783`／`:829` **今天仍逐字引用 `058100ad`**——那是 rebase 例外適用條件 (i) 的事實基礎，執行者只驗到「SHA 可達」，查核者補上了「main 的碼還在引用它」
- ⭐ R5 查核者**用明示基線而非 `origin/main`** 跑 doctor，理由逐字「避免過舊 `origin/main` 造成範圍污染」

【⭐ 派工包的錯，記在這裡】PM 的 R5 派工包寫「取回 `aeda16a` 與 `6d54318` **兩筆**」，**漏算了 `28ac73b` 本身也是文件 commit，實際三筆**。只取兩筆會使最終樹不等於 `28ac73b6`，與驗收第一條直接衝突。**執行者以驗收條款為準取三筆，判斷正確。**

【平台事實：PR 不能改指】PR #116 已關、另開 #117。GitHub 的 `PATCH /repos/{owner}/{repo}/pulls/{n}` **不接受 `head` 欄位**（實測傳不存在的分支回 200 而 `head.ref` 原封不動；`gh pr edit` 只有 `--base`）。#116 `comments 0`／`reviews 0`，關掉不孤立任何留痕。

【⚠️ 移交的未閉項】
1. ⭐ **`AI_WORKFLOW.md:229` 仍逐字寫「一律本地 rebase ＋ `git push --force-with-lease`」**——狹義例外目前只存在於 issue 留言。**任何只讀 canonical 的人會看到與本次交付相反的規則。** 需求方 2026-08-21 裁定：該條文屬跨專案 canonical 變更（cpbl 以 stub 指向本檔），**不開卡**，於**下次有人動 `AI_WORKFLOW.md` §6 時順手補**；在補上之前，issuecomment-5367447565 即為該例外的權威出處。
2. ⚠️ 同一次順手要補的還有：`AI_WORKFLOW.md:216` 寫 `Reviewed-by` 的值域是 `<GitHub 帳號／模型@工具>`，而本次裁定授權的 `—（基線更新 merge，無查核對象）` **不在該值域內**，且守衛只驗鍵存在、不會抓到。**那是本次裁定造成的殘留，不是既有缺陷。**
3. `escalation-resolution` 的 **writer 仍不存在**——`checkpoint_cmd.py:261` 與 `validation.py:827` 兩處自陳「尚未實作」。本卡只交付契約表示法與可反證的回放案例，**writer 補在 `WF-22-CLI4`（#9）或另開卡由需求方裁定**。`docs/CONTRACT_TOOL_RECONCILE.md` 的四條處置皆登記為「補寫入者」，如實反映 writer 不存在。
4. ⚠️ **`contract-baseline` 於 2026-08-21T16:28:03+08:00 切出**（issuecomment-5367425415），**僅為讓 R4 裁決能進入狀態面**——R1／R2／R3 三則事件寫於 2026-08-12、早於 escalation 帳契約，事件流中沒有可讀的帳事實，依 `review-escalation.md:276` 是「未知」而非「不計數」。baseline 之前的三則事件維持原貌。⚠️ 該指令自陳**跨卡唯一性目前只是約定、沒有機械執行者**。
5. ⚠️ **本 epoch 累計 2 個未斷言 attempt**（R4／R5 皆 `escalation_account: not-asserted`）——`preflight_basis_binding=structurally-unavailable`，自動計數含三振門檻在承接卡落地前不可用。**不得把「沒有可計數 attempt」讀成「執行者沒有累計」。**
6. ⚠️ **`--escalation-resolution` 的第五處字面**（`checkpoint_cmd.py:104` 的 argparse 保留旗標）被 `_contains_symbol` 的詞界規則漏掃（`_WORDISH` 含 `-`）——⭐ 而那條詞界正是用來擋 `deployment-status-change` 誤命中 `status-change`，**不是可單獨拿掉的 bug**。已如實記在 `docs/CONTRACT_TOOL_RECONCILE.md` §4.7／§5，並註明它對 write 角色一樣成立。
7. ⚠️ **舊分支 `claude/WF-ESCALATION-RESOLUTION-GAP1`（tip `28ac73b`）保留於 origin**——原因是保住 `058100ad` 的可達性。⭐ **merge 之後該理由已消失**（`058100ad` 現為 main 祖先），該分支可另行清理，本次不動。；收尾清理：已清除 worktree、本地分支、遠端分支。
- 2026-08-26T22:12:09+08:00 amend by wf-cli（op 812abaf1）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:ad8306f029a12e916324d599b873dd728a2d354fbda7078ec74214af0a9a0038 (807 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5262154606 · 2026-08-12T04:07:25Z

## 派審：#39 `WF-ESCALATION-RESOLUTION-GAP1` R1

⚠️ 審核對象 **`ruan6047/ai-workflow#39`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1
分支：claude/WF-ESCALATION-RESOLUTION-GAP1
被審 SHA：41a9f419df9c375b5df45a72c2ff5439edce0fa8
基線：6e6e8abd650c76fa6a2173f5dff35f99038ca1e0（已驗為祖先）
iteration：0（首輪）　寫入集：templates/review-escalation.md、scripts/replay_escalation_rules.py
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1
python3 scripts/replay_escalation_rules.py     # 87/87
git diff 6e6e8ab..058100ad -- templates/review-escalation.md   # +67/-0 純新增
```

### 一、三選一的論證，兩個被否決的理由請重點打

缺口：§4 規定條件成立時 `checkpoint_decision` 只能是 `escalate`，而 `escalation-epoch-change` 只有 `replan`／`change-executor`。但 #24 與 #25 真實發生的是第三種：**條件成立 → checkpoint 判 escalate → 需求方裁定 continue 並維持同執行者**。契約無表示法，PM 因此自創了未定義鍵。

- **（甲）`escalation-epoch-change` 第三個理由——否決。** 該事件定義即遞增 epoch 而新 epoch 從零計數，一次 `continue` 會抹掉本 epoch 的 occurrence 累計、重界 carry set、消滅 defer 清償義務。**「缺口只是記不下來，甲案是記錯」。** 實例：#24 第二則 checkpoint 之所以再次強制 escalate 正因家族計數仍為 4，走甲案該訊號當場消失。
- **（乙）checkpoint 上的獨立欄位——否決。** 把機械可導的告警與需等人的裁定綁進同一則事件，只有兩種寫法：等裁定到了才寫（**使機械判定成為人類裁定的人質**，且「條件已成立但尚無人裁定」變成無表示法，並**把漏建誘因制度化**——本 repo 已漏建兩次、成因正是「察覺門檻成立才建」）；或先寫再編輯（湮滅原文，§5 已否決）。
- **（丙）新事件型別——採用。** 兩則之間的區間就是升級狀態本身。

**請攻擊**：甲案的「記錯」論證是否誇大？乙案的兩難是否真的窮盡（有沒有第三種寫法）？丙案新增一個事件型別的代價（消費者、登記、marker 管轄）是否被誠實計入？

### 二、授權款：它明白說今天買不到實質保證

需求方帳號同屬 writer 集合、且執行者查核者根本不是 GitHub 帳號時，author 比對與 owner/reviewer 排除**恆真且分不開任何兩方**（後者兩邊型別不同，永遠不可能相等）。

故不寫成看似有檢查的條文，而要求 adapter 導出 **`authorization_binding: substantive | structurally-vacuous`**，把恆真本身寫進事件流；今天恆為後者（replay 機械驗出）。失效條件寫死：需求方帳號脫離 writer 集合，**或**執行者查核者取得可逐字比對的平台身分。

**今天確實會 FAIL 的三件**（分開的是留痕不是人）：(i) 裁定須為**獨立留言**——「`decided_by` 寫在被裁定的文本自己裡面」不構成裁定留痕，而**既有七則全是這個做法**；(ii) body 須逐字含本輪 `trigger_attempt_id`（內含 source SHA ⇒ 免時鐘新鮮性）；(iii) 1:1 解除與沿用上限。

**請判斷**：把恆真寫進事件流是誠實還是把問題重新包裝？E7 的用途是證明授權款今天沒有實質保證——那條斷言的形狀對嗎？

### 三、既有 checkpoint 的逐則判定，含兩處 PM 報數錯誤

執行者以 `gh api` 取原文、腳本輸出（非人工聲明）判定**七則**：#21×1、#22×2、#24×3、#25×1。全部缺三個必填欄、多出未定義鍵；帶 `escalation_resolution` 者五則、其新條文下十個必填欄一個都不存在；`attempts_so_far < 3` 者**兩則**（#22 `5255216570`、#25 `5256475572`）。

⚠️ **PM 的派工詞說「六則」與「一則」，執行者按實際七則與兩則判並依指示未對齊派工詞。PM 已認錯。** 請自己重數。

處置：全部標 legacy，不改寫、不重發、不追溯補建。**請判斷這個處置是否恰當**，以及新條文是否真的沒有追溯正當化它們。

### 四、replay 的品質，請重點看第 3 組

- **87/87 exit 0**；改前 65 條**逐字與順序未動且全 PASS**（抽出斷言區段逐行 diff 證明），新增 22 條全部追加在後。併進**同一個事件層引擎**而非另起第二個。
- **第 3 組（owner 雙相）做實了**：同一條違規事件流跑兩次——`two-phase`（修訂後）出現 `structural` 違規；`draft-single-phase`（初稿）因對**尚不存在的下一個 attempt** 求值而恆真、完全不擋。**差異本身即斷言。** 這是它自己 replay 抓到初稿缺陷後補的。
- E4 的失效款次隔離到**恰為** `ruling_is_standalone`（既有七則的形態）；E5 三個變體只差一處，各自只打掉一款，證明兩款獨立而非靠總開關。

**請攻擊**：「共用引擎 ⇒ 證的是同一套規則」這一步沒有機械檢查（執行者自陳，根據是既有 65 條逐字不動且全 PASS——必要非充分）。`owner_check` 分支只作用於 E 段路徑，理論上仍可能與 A～D 的判定語意脫節。

### 五、對 #9 的介面，查核者須知悉

§5 第 3 款雙相 `continued_owner` 的後半**今天仍無執行者**。#9 已於 `78d4064` 補上 owner 時點快照，但其執行者查碼證明**該快照裝的是查核者而非產出 `source_sha` 的執行者**（`handoff --next-stage review --to <查核者>` 先設 owner 欄，裁決在其後才寫），拿去比對會**系統性誤報**。詳見 #9 的 `issuecomment-5262093113`。

**#9 的追加沒有改變這件事。** 請不要因為 #9 補了欄位就當該款可執行。

### 六、已知殘留

執行者撤回一項自陳（`carried-forward` 三項比對現跑在正式引擎、有回歸守衛，不再是紙上規則），並**新增**明列 E 段未打掉任何案例的六款（`one_to_one`、`resolution_value`、`carried_source_unused`、`carried_by_recorded`、`trigger_matches`／`epoch_matches`、`auth_binding_derived`），不宣稱條件都驗過了。它另自陳「這份清單是完整的」本身是人工聲明，未寫必要性窮舉器。

第三項擴充（`control-plane-contract.md` 的 type 列舉登記）**需求方裁定不併入本卡**，另開 #42 一併處理 `review-marker-clearance` 那個既存落差。執行者的第 8 節第 4 項自陳原樣保留、未自行裁定：新型別是否需 marker 承載、是否受 `handoff-contract.md` §3.1 管轄未驗。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**——散文引用與 code fence 示範都一樣。拆開書寫，發文前 `grep` 確認 0 次。

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. 首輪無前輪 finding，**但請明確寫出「首輪，無前輪 accepted blocking finding」**而非略過該節。
2. **五個 schema 欄位自己填**。
3. **留收據**：`wf-review-receipt:v1` **多行格式**（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死。⚠️ 規則若提到起訖 delimiter 的字面，請說清楚是「規則之後的下一個」——PM 上次回讀時第一次就錨到規則散文內的同名字面而失敗。

**YAML 限制**：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、值含 ` #` 須整個值加引號。


## Comment 5262269595 · 2026-08-12T04:26:23Z

## 重派：#39 R1（前一輪 `review-invalid`，錯在 Coordinator）

**上一輪的 `review-invalid` 判定在程序上正確，但它陳述的前提不對——而真正的錯是我的。**

查核者回報「指定工作樹 `/Users/ruanruan/Dev/ai-workflow/wf-escalation-resolution-gap1` 不存在」。實測：

```
/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1   ← 存在
/Users/ruanruan/Dev/ai-workflow/wf-escalation-resolution-gap1                     ← 不存在
```

**本 Issue 上一則派審詞給的是第一個，是正確的。** 查核者回報的第二個，是把我給協調者的提示詞表格裡 `worktree` 欄位的**裸名**接到 repo 根目錄會得到的東西——我在那張表格寫了 `wf-escalation-resolution-gap1` 而沒有 `.claude/worktrees/` 前綴。

**我同時提供了兩個來源，而次要那個有歧義。** 這與 2026-08-11 抄錯基線是同一類事故：Coordinator 提供了一個與權威來源競爭的來源。`attribution: coordinator`。該輪不計 iteration、未寫 review event。

### 本則為權威

**任何摘要表格、協調者提示詞或轉述若與本則衝突，一律以本則為準。** 進駐位置逐字為：

```
/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1
git rev-parse HEAD    # 應為 41a9f419df9c375b5df45a72c2ff5439edce0fa8
```

其餘一切——被審 SHA、基線、iteration、寫入集、六節攻擊點、環境紅線、留言紀律、輸出契約與收據格式——**完全沿用本 Issue 前一則派審詞（`issuecomment-5262154606`）**，未作任何修改。請直接依該則執行。

（同批的另外三張未中此問題，因為那三位查核者讀了 Issue 而非表格。）

## Comment 5262443238 · 2026-08-12T04:54:10Z

<!-- wf-review-receipt:v1
card_id: WF-ESCALATION-RESOLUTION-GAP1
source_sha: 41a9f419df9c375b5df45a72c2ff5439edce0fa8
report_sha256: 4d6325a7ae91b0e47f4336ff0fc7e858f5fe116f410c849eb5879f63f0b28737
-->
取材規則：UTF-8、LF、無 strip；雜湊範圍為本規則之後的下一個 `--- report-begin ---` 結束換行後第一個字元，至其後下一個 `--- report-end ---` 開始前的前一個換行為止；排除 receipt HTML 註解、取材規則、兩個 delimiter 行及它們之外的所有文字。

--- report-begin ---
首輪，無前輪 accepted blocking finding。

```yaml
core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: "git rev-parse HEAD && git status --porcelain && git merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD"
    observed: "HEAD=41a9f419df9c375b5df45a72c2ff5439edce0fa8；工作區乾淨；基線祖先檢查 exit 0；origin/claude/WF-ESCALATION-RESOLUTION-GAP1 包含該 SHA。"
  - command: "git diff --check 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 41a9f419df9c375b5df45a72c2ff5439edce0fa8 && git diff --name-status 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 41a9f419df9c375b5df45a72c2ff5439edce0fa8"
    observed: "無 whitespace error；寫入集僅 templates/review-escalation.md 與 scripts/replay_escalation_rules.py。"
  - command: "git archive 41a9f419df9c375b5df45a72c2ff5439edce0fa8 | tar -x -C /tmp/wf39-review.UuyRDI && cd /tmp/wf39-review.UuyRDI && python3 scripts/replay_escalation_rules.py && python3 -m py_compile scripts/replay_escalation_rules.py"
    observed: "87/87 通過；Python 編譯通過。E3 的 two-phase 對照確實在 owner 不符時產生 structural 違規，draft-single-phase 對照沒有。"
  - command: "nl -ba scripts/replay_escalation_rules.py | sed -n '486,507p;672,734p'; nl -ba templates/review-escalation.md | sed -n '250,290p'"
    observed: "RES() 建構的 resolution fixture 未含 authorization_binding；_resolution_conditions() 的 auth_binding_derived 僅測 derive_authorization_binding(ctx) 落在兩個允許字串，未讀 event 欄位。與 §5 的缺欄或手填即無效要求不一致。"
  - command: "gh api repos/ruan6047/ai-workflow/issues/21/comments?per_page=100 --paginate; gh api repos/ruan6047/ai-workflow/issues/22/comments?per_page=100 --paginate; gh api repos/ruan6047/ai-workflow/issues/24/comments?per_page=100 --paginate; gh api repos/ruan6047/ai-workflow/issues/25/comments?per_page=100 --paginate"
    observed: "可獨立讀到既有 checkpoint 的未定義鍵形態；本卡對 cutover 前事件採 legacy、不改寫、不重發、不追溯補建的處置，未把新 type 反向正當化歷史事件。"
findings:
  - finding_id: "WF-ESCALATION-RESOLUTION-GAP1-R1-001"
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: "resolution-authorization-binding-not-validated-against-event"
    evidence: "templates/review-escalation.md §5 規定 authorization_binding 必須由 adapter 導出，手填、缺欄或省略即本則無效。scripts/replay_escalation_rules.py:496-504 的 RES() 建構事件不含此欄，E1 仍輸出 VALID；:726-727 僅檢查 derive_authorization_binding(ctx) 的回傳值屬枚舉，沒有比較事件欄位，故無法拒絕缺欄或偽造值。"
    disposition: "令 resolution fixture 與 replay 的 event schema 明確承載 authorization_binding，並驗證其存在且逐字等於 adapter 導出值；新增缺欄、手填 structurally-vacuous 與手填 substantive 的獨立反例，均須使 resolution 無效。"
```

## 範圍外發現

- `escalation-resolution` 尚未登記至 control-plane-contract.md 的 type 列舉，也尚無 checkpoint writer；被審文本已明確交由 #42 與 #9 承接，未擴大為本輪 finding。
- §5 第 3 款的 continued_owner 雙相語意依賴 #9 寫入端取得真正產出 source_sha 的執行者 owner；本輪未把 #9 的現有 reviewer snapshot 當成可用 owner 證據。
--- report-end ---


## Comment 5262492509 · 2026-08-12T05:02:02Z

<!-- wf-review-event:v1 card_id=WF-ESCALATION-RESOLUTION-GAP1 source_sha=41a9f419df9c375b5df45a72c2ff5439edce0fa8 attempt_id=WF-ESCALATION-RESOLUTION-GAP1-e0-41a9f419df9c375b5df45a72c2ff5439edce0fa8 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-ESCALATION-RESOLUTION-GAP1`　attempt_id：`WF-ESCALATION-RESOLUTION-GAP1-e0-41a9f419df9c375b5df45a72c2ff5439edce0fa8`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5262443238 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=4d6325a7… 一次相符。PM 的轉錄調整：自結構化區塊末截斷「## 範圍外發現」以下的散文段落，該段已完整保存於收據的雜湊範圍內；區塊內字串逐字未變）　escalation_epoch：0
- source_sha：`41a9f419df9c375b5df45a72c2ff5439edce0fa8`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-12T13:02:00+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git status --porcelain && git merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD`
  - HEAD=41a9f419df9c375b5df45a72c2ff5439edce0fa8；工作區乾淨；基線祖先檢查 exit 0；origin/claude/WF-ESCALATION-RESOLUTION-GAP1 包含該 SHA。
- `git diff --check 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 41a9f419df9c375b5df45a72c2ff5439edce0fa8 && git diff --name-status 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 41a9f419df9c375b5df45a72c2ff5439edce0fa8`
  - 無 whitespace error；寫入集僅 templates/review-escalation.md 與 scripts/replay_escalation_rules.py。
- `git archive 41a9f419df9c375b5df45a72c2ff5439edce0fa8 | tar -x -C /tmp/wf39-review.UuyRDI && cd /tmp/wf39-review.UuyRDI && python3 scripts/replay_escalation_rules.py && python3 -m py_compile scripts/replay_escalation_rules.py`
  - 87/87 通過；Python 編譯通過。E3 的 two-phase 對照確實在 owner 不符時產生 structural 違規，draft-single-phase 對照沒有。
- `nl -ba scripts/replay_escalation_rules.py | sed -n '486,507p;672,734p'; nl -ba templates/review-escalation.md | sed -n '250,290p'`
  - RES() 建構的 resolution fixture 未含 authorization_binding；_resolution_conditions() 的 auth_binding_derived 僅測 derive_authorization_binding(ctx) 落在兩個允許字串，未讀 event 欄位。與 §5 的缺欄或手填即無效要求不一致。
- `gh api repos/ruan6047/ai-workflow/issues/21/comments?per_page=100 --paginate; gh api repos/ruan6047/ai-workflow/issues/22/comments?per_page=100 --paginate; gh api repos/ruan6047/ai-workflow/issues/24/comments?per_page=100 --paginate; gh api repos/ruan6047/ai-workflow/issues/25/comments?per_page=100 --paginate`
  - 可獨立讀到既有 checkpoint 的未定義鍵形態；本卡對 cutover 前事件採 legacy、不改寫、不重發、不追溯補建的處置，未把新 type 反向正當化歷史事件。

### findings（1，其中 blocking 1）

- **WF-ESCALATION-RESOLUTION-GAP1-R1-001**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`resolution-authorization-binding-not-validated-against-event`
  - evidence：templates/review-escalation.md §5 規定 authorization_binding 必須由 adapter 導出，手填、缺欄或省略即本則無效。scripts/replay_escalation_rules.py:496-504 的 RES() 建構事件不含此欄，E1 仍輸出 VALID；:726-727 僅檢查 derive_authorization_binding(ctx) 的回傳值屬枚舉，沒有比較事件欄位，故無法拒絕缺欄或偽造值。
  - disposition：令 resolution fixture 與 replay 的 event schema 明確承載 authorization_binding，並驗證其存在且逐字等於 adapter 導出值；新增缺欄、手填 structurally-vacuous 與手填 substantive 的獨立反例，均須使 resolution 無效。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5262609174 · 2026-08-12T05:14:35Z

## 派審：#39 `WF-ESCALATION-RESOLUTION-GAP1` R2

⚠️ 審核對象 **`ruan6047/ai-workflow#39`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1
分支：claude/WF-ESCALATION-RESOLUTION-GAP1　　被審 SHA：b039c0b08113382566d9b687087dea1f08f3915c
基線：6e6e8abd650c76fa6a2173f5dff35f99038ca1e0（已驗為祖先）　　iteration：1
寫入集：templates/review-escalation.md、scripts/replay_escalation_rules.py
```

> **本則為權威。** 摘要表格與轉述若衝突以本則為準；**值解不開時先回對本則，不要直接停手**。

### 一、複驗 R1-001：執行者說病灶比你指出的更深一層

你判：`RES()` 建構的事件不含 `authorization_binding` 而 E1 仍 `VALID`；檢查只驗 `derive_authorization_binding(ctx)` 的回傳值屬枚舉、從未比較事件欄位。

執行者接受，並指出**還有加蓋時點的問題**：舊碼在校驗**通過之後**才把導出值貼上投影，於是**被校驗的值與消費者讀到的值不同源**——那才是該款從未被驗到的機制。它自述「我寫了整整一節論證不得寫出看似有檢查、實際恆真的條文，然後在自己的測試裡放了一條」。

**修法分兩側：**

- **契約 §5 第 7 款**：`authorization_binding` 改為 adapter **加蓋**，提交面**不得含此鍵**，**含即無效即使其值恰好等於導出值**——本款驗**來源**不驗值。援引 `counts_toward_escalation` 為同形先例。
- **腳本**：來源顯式建模（`_binding_source` ∈ adapter／writer／無），**加蓋時點移到校驗之前**，投影直接用已加蓋的事件。原一款拆三款：`auth_binding_present`（缺欄）／`auth_binding_not_hand_filled`（**驗來源**）／`auth_binding_matches_derived`（驗值）。

**請攻擊**：(a) 「加蓋時點」這個更深的診斷成立嗎，還是把一個簡單缺陷講得比較好聽？(b) 三款拆分後，有沒有**第四種**繞過路徑（例如 adapter 被騙成蓋錯值、或 `_binding_source` 本身可被提交面設定）？

### 二、分水嶺那條，PM 已獨立驗過，請你也驗

三個反例的失效款次（實測）：

| 反例 | 失效款次 |
|---|---|
| 缺欄／省略 | `[present, matches_derived]` |
| **手填 `structurally-vacuous`（同值）** | **`[not_hand_filled]` ——恰為一款** |
| 手填 `substantive`（不同值） | `[not_hand_filled, matches_derived]` |
| 對照組（`41a9f41` 的 enum-only 寫法）跑同三例 | `[True, True, True]` **全放行** |

**關鍵在 `scripts:1894-1897` 那條後設斷言**，它同時斷言 `auth_binding_matches_derived is True` **與**導出值逐字等於手填值——兩者缺一，「只驗值抓不到」就只是碰巧一起紅。PM 已讀過該斷言並確認它釘住了前提。

**請自己重跑並判斷**：(a) 對照組是執行者對舊碼的**模型**不是舊碼本身（它已自陳，並引 `41a9f41:726` 原文與「`RES()` 不含該欄」佐證模型忠實，但等價性無機械檢查——舊檔無 `hand_filled` 參數故無法整份載入跑同組 fixture）。那個模型可信嗎？(b) 缺欄那條**沒有做成單款隔離**，執行者拒絕為了整齊而讓 `matches_derived` 在欄位不存在時判 True——「那就是該物不存在時條件恆真，正是本卡通篇在反對、也正是這次被打的形狀」。**請判斷這個拒絕是否正確。**

### 三、退化與跨卡

既有 87 條逐行 diff：**只有 E1 一條措辭更新**（加驗來源後改寫敘述，仍 PASS），其餘 86 條逐字未動且全 PASS；新增 7 條（E8）。總計 **94/94、FAIL 0、exit 0**、`py_compile` 通過。

PM 已複驗 `review-escalation.md` **無節標題增刪**（§1–§5 原樣），故 #38 與 #9 對 §3／§4／§5 的引用不受影響。PM 另核對 #9 分支 `review.py:61` 的 `WRITER_ONLY_KEYS = ("accepted", "status", "counts_toward_escalation")`，**確認第 7 款援引的先例屬實**。

### 四、六款未涵蓋清單，執行者如實更新且結論對它不利

**本輪關掉**：`auth_binding_derived`（拆三款各有反例，從清單移除）。

**仍在清單的五項**：`trigger_matches`／`epoch_matches`／`one_to_one`／`resolution_value`／`carried_source_unused`／`carried_by_recorded` 中的五個。執行者指出前四項是**本引擎定址方式導致的結構性恆真**（**與被打的那一款同型**），`carried_by_recorded` 純粹是沒寫案例。

**它並自陳上一輪說要做的必要性證明器這一輪仍然沒做**，只補了被 finding 點名的那一款。

**請判斷**：既然它自己說剩下四項與被打的那一款**同型**，只修被點名的那一款是否足夠？還是這一輪應該一併處理？

### 五、scope_outside 兩項照裁定未動

1. type 列舉登記與 checkpoint writer → 交由 **#42**／**#9**，契約內劃界文字未改。
2. §5 第 3 款的 `continued_owner` **未因 #9 於 `779e575` 加了 owner 欄而改寫**——依需求方裁定（#9 的 `issuecomment-5262093113`）該快照裝的是**查核者**不是執行者，不足以支撐該款。條文原樣保留。**請維持這個立場，不要因為 #9 加了欄位就當該款可執行。**

### 六、執行者自陳的兩項無機械執行者

1. 對照組是模型不是舊碼（見第二節）。
2. **契約說「提交面不得含此鍵」，但本 repo 沒有任何寫入端在執行它**（#9 未完成）；腳本裡的 `_binding_source` 是 fixture 宣告的，**不是從真實 payload 觀察到的**。**規則層有守衛，寫入層沒有。**

### 七、門檻

iteration 1，第二個可計數 attempt，未達 checkpoint 門檻。R1-001 家族名 `resolution-authorization-binding-not-validated-against-event`；若你判定它仍開啟，**請沿用該家族名**。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做——不要在被審 worktree 內 `checkout`／`reset`／`stash`。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴，命中即**永久隔離整張卡**。本卡會讓你大量引用事件內容——用 `gh api` 讀進來處理即可，不要把前綴字面寫進報告。發文前 `grep`。（`review-escalation.md` §5 的 `repaired-verified` 條目內有一處**既存**前綴字面，那是 repo 檔案內容非留言，不影響。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制**：逐項回報 R1-001 的閉環狀態（`resolved`／`withdrawn`／仍開啟）並附證據；**五個 schema 欄位自己填**；**留收據**（多行格式、報告全文同帖、取材規則寫死，並寫明起訖 delimiter 是「本規則之後的下一個」——你上一輪的收據合格且 PM 一次算對，請沿用同樣寫法）。

**YAML 限制**：不支援 `>`（用 `|`）、不支援裸字串序列、不支援頂層鍵＋巢狀 mapping、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**（你上一輪的「## 範圍外發現」散文段被解析器拒收，PM 截斷後才寫得進去）、值含 ` #` 須加引號。


## Comment 5264828301 · 2026-08-12T09:22:48Z

## 派審：#39 `WF-ESCALATION-RESOLUTION-GAP1` R2

⚠️ 審核對象 **`ruan6047/ai-workflow#39`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1
分支：claude/WF-ESCALATION-RESOLUTION-GAP1　　被審 SHA：b039c0b08113382566d9b687087dea1f08f3915c
基線：6e6e8abd650c76fa6a2173f5dff35f99038ca1e0（PM 已重算並驗為祖先）　　iteration：1
寫入集：templates/review-escalation.md、scripts/replay_escalation_rules.py
```

> **本則為權威**；摘要表格與轉述若衝突以本則為準，**值解不開時先回對本則，不要直接停手**。`origin/main` 現為 `e8a638c`。**PM 已實測 merge(origin/main, 本分支) → replay 94/94、pytest 658 passed 全綠。**

⚠️ **本卡交付延誤是 PM 的錯，不是執行者的。** 它於 `b039c0b` 交付後即轉 🔍待查核，但 PM **漏了發派審詞**，卡在該狀態數小時。PM 另曾在 #9 與 #42 的留痕中誤稱本卡「本批查核 APPROVE」——**那是錯的**，本卡唯一一次查核是 R1（`REQUEST_CHANGES`），`b039c0b` 至今無任何 review event。兩處已發前向更正。**這些都不影響對交付物的評價。**

### 一、複驗 R1-001：執行者說病灶比你指出的更深一層

你判：`RES()` 建構的事件不含 `authorization_binding` 而 E1 仍 `VALID`；檢查只驗 `derive_authorization_binding(ctx)` 的回傳值屬枚舉、從未比較事件欄位。

它接受，並指出**還有加蓋時點的問題**：舊碼在校驗**通過之後**才把導出值貼上投影，於是**被校驗的值與消費者讀到的值不同源**——那才是該款從未被驗到的機制。它自述：「我寫了整整一節論證不得寫出看似有檢查、實際恆真的條文，**然後在自己的測試裡放了一條**。」

**修法兩側**：契約 §5 第 7 款把 `authorization_binding` 改為 adapter **加蓋**、提交面**不得含此鍵**、**含即無效即使其值恰好等於導出值**（驗**來源**不驗值），援引 `counts_toward_escalation` 為同形先例（**PM 已核對 #9 分支 `review.py` 的 `WRITER_ONLY_KEYS` 確含該鍵**）；腳本側來源顯式建模、**加蓋時點移到校驗之前**、原一款拆三款。

**請攻擊**：(a)「加蓋時點」這個更深的診斷成立嗎，還是把一個簡單缺陷講得比較好聽？(b) 三款拆分後有沒有**第四種**繞過路徑（例如 adapter 被騙成蓋錯值、或 `_binding_source` 本身可被提交面設定）？

### 二、分水嶺那條，PM 已用突變獨立驗過

三個反例的失效款次（實測）：缺欄 → `[present, matches_derived]`；**手填 `structurally-vacuous`（同值）→ `[not_hand_filled]` 恰為一款**；手填 `substantive` → `[not_hand_filled, matches_derived]`。對照組（`41a9f41` 的 enum-only 寫法）跑同三例 → **`[True, True, True]` 全放行**。

關鍵在 `scripts:1894-1897` 那條**後設斷言**，它同時斷言 `auth_binding_matches_derived is True` **與**導出值逐字等於手填值——**兩者缺一，「只驗值抓不到」就只是碰巧一起紅**。

**PM 另做了一次突變驗證**：把 `auth_binding_not_hand_filled` 改成恆真後，手填同值那條的失效款次變成 **`[]`（完全放行）**，94/94 → 91/94、三條轉紅且理由都對，而「合規事件在兩種寫法下都通過」仍 PASS（未誤傷正例）。**那道來源檢查是承重的。**

**請自己重跑並判斷**：(a) 對照組是執行者對舊碼的**模型**不是舊碼本身（它已自陳，舊檔無 `hand_filled` 參數故無法整份載入跑同組 fixture）——那個模型可信嗎？(b) 缺欄那條**沒有做成單款隔離**，它拒絕為了整齊而讓 `matches_derived` 在欄位不存在時判 True——「**那就是該物不存在時條件恆真，正是本卡通篇在反對、也正是這次被打的形狀。不為了整齊再犯一次。**」**請判斷這個拒絕是否正確。**

### 三、退化與跨卡

既有 87 條逐行 diff：**只有 E1 一條措辭更新**（加驗來源後改寫敘述，仍 PASS），其餘 86 條逐字未動且全 PASS；新增 7 條（E8）。總計 **94/94、FAIL 0、exit 0**。**PM 已複驗 `review-escalation.md` 無節標題增刪**（§1–§5 原樣）。

### 四、六款未涵蓋清單，執行者如實更新且結論對它不利

**本輪關掉** `auth_binding_derived`（拆三款各有反例）。**仍在清單的五項**：`trigger_matches`／`epoch_matches`／`one_to_one`／`resolution_value`／`carried_source_unused`／`carried_by_recorded` 中的五個。它指出**前四項是本引擎定址方式導致的結構性恆真——與被打的那一款同型**，並自陳上一輪說要做的必要性證明器**這一輪仍然沒做**，只補了被 finding 點名的那一款。

**請判斷**：既然它自己說剩下四項與被打的那一款**同型**，只修被點名的那一款是否足夠？

### 五、scope_outside 兩項照裁定未動

type 列舉登記交由 **#42**（該卡本批 `REQUEST_CHANGES`，其中一筆 blocking 正是「`escalation-resolution` 的先行登記未被釘住」——**與本卡直接相關，請注意兩者的相互依賴**）；§5 第 3 款的 `continued_owner` **未因 #9 加了 owner 欄而改寫**，依需求方裁定該快照裝的是**查核者**不是執行者。

### 六、執行者自陳的兩項無機械執行者

對照組是模型不是舊碼；**契約說「提交面不得含此鍵」但本 repo 沒有任何寫入端在執行它**（#9 未完成），腳本裡的 `_binding_source` 是 fixture 宣告的、**不是從真實 payload 觀察到的**——**規則層有守衛，寫入層沒有**。

### 七、門檻

iteration 1，第二個可計數 attempt，未達 checkpoint 門檻。R1-001 家族名 `resolution-authorization-binding-not-validated-against-event`；若你判定它仍開啟，**請沿用**。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5265393753 · 2026-08-12T10:18:06Z

<!-- wf-review-receipt:v1
card_id: WF-ESCALATION-RESOLUTION-GAP1
source_sha: b039c0b08113382566d9b687087dea1f08f3915c
report_sha256: 68c3b5891ac51535e5451a91480093f5a5f30c5b389f4a277c193593808a954d
-->
取材規則：起點為本規則之後的下一個 core_pain_resolved: 行；終點為報告最後一個字元；UTF-8；LF；不 strip；排除本收據 HTML 註解與本取材規則行。

core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1 rev-parse HEAD"
    observed: "b039c0b08113382566d9b687087dea1f08f3915c；與派審 source_sha 一致。"
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1 status --short"
    observed: "發現未追蹤 scripts/__pycache__/；本次未在被審 worktree 寫入，驗證均在 /tmp/wf39-review.* 進行。"
  - command: "git -C /Users/ruanruan/Dev/ai-workflow archive b039c0b08113382566d9b687087dea1f08f3915c | tar -x -C /tmp/wf39-review.* && python3 /tmp/wf39-review.*/scripts/replay_escalation_rules.py"
    observed: "exit 0；94/94 通過；E8 的缺欄、同值手填、異值手填分別失效 [present, matches_derived]、[not_hand_filled]、[not_hand_filled, matches_derived]。"
  - command: "python3 -m py_compile /tmp/wf39-review.*/scripts/replay_escalation_rules.py"
    observed: "exit 0。"
  - command: "git -C /Users/ruanruan/Dev/ai-workflow show 41a9f419df9c375b5df45a72c2ff5439edce0fa8:scripts/replay_escalation_rules.py"
    observed: "舊版 RES() 未承載 authorization_binding，且舊條件僅驗 derive_authorization_binding(ctx) 的枚舉回傳值；對照模型的核心行為與舊碼相符。"
findings:
  - finding_id: "WF-ESCALATION-RESOLUTION-GAP1-R2-001"
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: "resolution-authorization-binding-not-validated-against-event"
    evidence: "R1-001 已閉環：§5 第 7 款與 E8 對缺欄、同值手填、異值手填均有反例，且手填同值時 auth_binding_matches_derived 為 true、只由來源款拒絕。惟 scripts/replay_escalation_rules.py:1288-1296 明列 trigger_matches／epoch_matches、one_to_one、resolution_value、carried_source_unused、carried_by_recorded 未被任何案例打掉；其中前四項被交付物自述為定址造成的結構性恆真。它們同屬此卡新增 escalation-resolution 必要條件，現有綠燈不能證明其 guard 可拒絕錯誤事件。"
    disposition: "為每個未涵蓋必要條件加入最小反例及 assertion：錯誤 trigger 或 epoch、重複解除同一 checkpoint、列舉外 resolution、同一 fresh-ruling 第二次沿用、缺 carried_by；逐案斷言該 resolution 無效且升級狀態維持。不得以 fixture 定址同源或人工未涵蓋清單取代守衛證據。"

前輪 accepted blocking finding 閉環

- WF-ESCALATION-RESOLUTION-GAP1-R1-001：resolved。證據為 §5 第 7 款改為 adapter 加蓋，E8 三個反例均使 resolution 無效；同值手填僅失敗 auth_binding_not_hand_filled，並有值比對確為 true 的後設斷言。缺欄同時失敗 present 與 matches_derived 是正確的 fail-closed 行為，非未隔離缺陷。

範圍外發現

- 被審 worktree 存在未追蹤 scripts/__pycache__/，與派審所稱工作區乾淨不一致；本報告未將其歸為 executor 的實質交付 finding，因它不屬 source SHA 且本次檢查未使用該 worktree 寫入。應由 lifecycle writer 在後續 handoff preflight 清理或重新驗證。

## Comment 5265648228 · 2026-08-12T10:43:45Z

<!-- wf-review-event:v1 card_id=WF-ESCALATION-RESOLUTION-GAP1 source_sha=b039c0b08113382566d9b687087dea1f08f3915c attempt_id=WF-ESCALATION-RESOLUTION-GAP1-e0-b039c0b08113382566d9b687087dea1f08f3915c -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-ESCALATION-RESOLUTION-GAP1`　attempt_id：`WF-ESCALATION-RESOLUTION-GAP1-e0-b039c0b08113382566d9b687087dea1f08f3915c`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5265393753 未經編輯，PM 依其取材規則回讀重算 report_sha256=68c3b589… 一次相符。PM 的轉錄調整：自結構化區塊末截斷「前輪 accepted blocking finding 閉環」以下的散文段落，該段已完整保存於收據雜湊範圍內；區塊內字串逐字未變）　escalation_epoch：0
- source_sha：`b039c0b08113382566d9b687087dea1f08f3915c`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-12T18:43:44+08:00

### self_run（查核者實跑）

- `git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1 rev-parse HEAD`
  - b039c0b08113382566d9b687087dea1f08f3915c；與派審 source_sha 一致。
- `git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1 status --short`
  - 發現未追蹤 scripts/__pycache__/；本次未在被審 worktree 寫入，驗證均在 /tmp/wf39-review.* 進行。
- `git -C /Users/ruanruan/Dev/ai-workflow archive b039c0b08113382566d9b687087dea1f08f3915c | tar -x -C /tmp/wf39-review.* && python3 /tmp/wf39-review.*/scripts/replay_escalation_rules.py`
  - exit 0；94/94 通過；E8 的缺欄、同值手填、異值手填分別失效 [present, matches_derived]、[not_hand_filled]、[not_hand_filled, matches_derived]。
- `python3 -m py_compile /tmp/wf39-review.*/scripts/replay_escalation_rules.py`
  - exit 0。
- `git -C /Users/ruanruan/Dev/ai-workflow show 41a9f419df9c375b5df45a72c2ff5439edce0fa8:scripts/replay_escalation_rules.py`
  - 舊版 RES() 未承載 authorization_binding，且舊條件僅驗 derive_authorization_binding(ctx) 的枚舉回傳值；對照模型的核心行為與舊碼相符。

### findings（1，其中 blocking 1）

- **WF-ESCALATION-RESOLUTION-GAP1-R2-001**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`resolution-authorization-binding-not-validated-against-event`
  - evidence：R1-001 已閉環：§5 第 7 款與 E8 對缺欄、同值手填、異值手填均有反例，且手填同值時 auth_binding_matches_derived 為 true、只由來源款拒絕。惟 scripts/replay_escalation_rules.py:1288-1296 明列 trigger_matches／epoch_matches、one_to_one、resolution_value、carried_source_unused、carried_by_recorded 未被任何案例打掉；其中前四項被交付物自述為定址造成的結構性恆真。它們同屬此卡新增 escalation-resolution 必要條件，現有綠燈不能證明其 guard 可拒絕錯誤事件。
  - disposition：為每個未涵蓋必要條件加入最小反例及 assertion：錯誤 trigger 或 epoch、重複解除同一 checkpoint、列舉外 resolution、同一 fresh-ruling 第二次沿用、缺 carried_by；逐案斷言該 resolution 無效且升級狀態維持。不得以 fixture 定址同源或人工未涵蓋清單取代守衛證據。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5266531397 · 2026-08-12T12:01:33Z

## 派審：#39 `WF-ESCALATION-RESOLUTION-GAP1` R3

⚠️ 審核對象 **`ruan6047/ai-workflow#39`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1
分支：claude/WF-ESCALATION-RESOLUTION-GAP1　　被審 SHA：ba90b81a52172a64c44702d70c93ca5835ddd0ad
基線：6e6e8abd650c76fa6a2173f5dff35f99038ca1e0（PM 已重算並驗為祖先）　　iteration：2
本輪寫入集：scripts/replay_escalation_rules.py 單檔（+388/-28）
```

> **權威來源**：本則與本 Issue Log 最後一筆 `handoff` 事件的 `SHA` **必須一致**；不符時**以 handoff 事件為準並回報**。

`origin/main` 現為 `e1b33d8`（#53 已合併）。**PM 自審**：遠端 tip 相符、`b039c0b` 是 `ba90b81` 的祖先（**非 force push**）、對 main `merge-tree` **CLEAN**、本輪寫入集單檔零逸出（卡面宣告兩檔）、拋棄式副本重跑 **114/114 exit 0**。

> **本輪新增的檢查項**：`AGENTS.md:10` 與 `AI_WORKFLOW.md §6` 要求 T2 以上實作 commit 加 `Requested-by` / `Planned-by` / `Implemented-by` trailer。**本卡的被審 commit 沒有。** 這是今日全批問題（今日落 main 的 31 筆非 merge commit 帶 `Implemented-by` 者 0 筆、最後一筆帶 trailer 是 2026-08-11、先前四輪跨家族查核者無一抓到），而 PM 的執行者提示詞從未提過它。#52 的查核者已把同一項判為 **blocking**。**你可以判定本卡是否同樣 blocking，也可以判定該歸屬 executor 還是 coordinator**——#52 的執行者主張應為 coordinator，依據是本 repo 對 trailer 零機械強制（`AI_WORKFLOW.md:221` 寫「守衛必紅」而該守衛不存在）、且 `CLAUDE.md:10` 與 `AGENTS.md:10` 互相矛盾（前者把 `Reviewed-by` 列為一律，照字面辦會在實作 commit 上自我批准）。PM 已複驗那兩項屬實。

### 一、複驗 R2-001：執行者說病灶是**定址**不是守衛

你判：`:1288-1296` 明列六款未被任何案例打掉，其中前四項自述為「定址造成的結構性恆真」。

執行者的診斷：舊 `RES()` 只有一個 key `checkpoint_trigger`，replay 用它 `cps.get()` 取 `cp`，`_resolution_conditions` 再拿**同一個 key** 跟 `cp.trigger` 比——**同源比對**。`cp` 取得出來時它必為真；取不出來時 `bool(cp)` 已先擋掉。**錯誤 trigger 的事件在該 fixture 裡根本表達不出來。**「這不是守衛，是定址。」

五種反例逐一**隔離到恰為一款**（全部斷言「失效款次恰為該一款」＋「升級狀態維持、`cp.resolution is None`」）：

- **錯誤 trigger** → `trigger_matches`
- **錯誤 epoch** 分兩條路徑驗（§5 第 1 款是兩個合取項）：宣稱 epoch 不符 → `epoch_matches`，**並另立斷言釘住 `trigger_matches is True`**，證明不是被前者順帶抓到；epoch 遞增後才補發裁定 → `epoch_matches` 的第二合取項
- **重複解除** → `one_to_one`，第二則**刻意附另一則完全合規的獨立裁定留言**，故留痕五款皆成立
- **列舉外 resolution** → `resolution_value`
- **同一 fresh-ruling 第二次沿用** → `carried_source_unused`（`carried_from` 指向的**仍是** fresh-ruling，故不是被 `carried_from_is_fresh` 抓到）
- **缺 `carried_by`** → `carried_by_recorded`

**請攻擊**：這些反例是不是又一次「fixture 定址同源」，只是換了個位置？你上一輪的 disposition 明寫「**不得以 fixture 定址同源或人工未涵蓋清單取代守衛證據**」——請判斷這一輪有沒有真的離開那個形狀。

### 二、它自己窮舉出你沒點到的四款

除你點名的六個 key，還有**四款既未涵蓋也未列入清單**：`checkpoint_is_escalate`、`resolved_by_is_requester`（`resolved_by` 非需求方但留言 author 仍是需求方，證明與 `ruling_author_is_requester` 獨立）、`ruling_url_on_card`（裁定留言存在且完全合規，只是掛在 `issues/9` 上，與「讀不到留言」分開）、`carry_forcing_set_identical`。各補一個隔離反例。

### 三、人工清單已被刪除，換成機械彙總——**請重點打這一步**

`E_NOT_EXERCISED` 刪掉，改為 `resolution_clause_coverage()` 掃過所有 E 段回放的 `resolution_audit`，機械彙總哪些款曾被判為 False，並斷言未涵蓋為空。

**彙總器本身經過反向測試**：在 scratchpad 副本裡拿掉 `E9f/E9h/E9j` 三個登記，它如實印出 `未涵蓋：['checkpoint_is_escalate', 'resolved_by_is_requester', 'carried_source_unused']` 且斷言 FAIL、exit 1。另有一條斷言釘住 `set(RESOLUTION_CONDITIONS) == set(audit keys)`，防止款名寫錯而虛報涵蓋。

登記範圍**刻意只含契約本身**的回放；`draft-single-phase` 與 `pre-fix-enum-only` 是反面對照組，拿它們充覆蓋會把結論反過來。

**請判斷**：這個彙總器證明的是「每款都有反例」還是「每款都有**我登記過的**反例」？登記範圍由誰決定、填錯了誰抓？——**這正是它上一輪被打的同一個問題換了一層。**

### 四、執行者主動上記錄的四件證明不了的事，第 3 件最該看

1. **只有兩款需要改碼，其餘是補測試。** `trigger_matches`／`epoch_matches` 需要把定址與宣稱分離才可能為假；其餘各款求值邏輯**一行未改**，本輪補的是它們缺席的反例。**它明說沒有把兩者混為一談。**
2. **9c 在舊寫法下本來就擋得住**——`epoch_matches` 先前只缺一個合取項，不是整款恆真。對照組印出 `[True, True, False]`，它把第三個 False 寫成斷言而非含糊帶過。
3. ⚠️ **`resolution_basis` 落在列舉外時，§5 第 5、6 兩款會整批退化為恆真**——`is_fresh` 與 `is_carried` 皆 false，所有 `if is_fresh else True` 一起變 True。本則仍被 `resolution_value` 擋下（fail-closed 成立）**但只剩一層**。它**未改條件式結構**（超出你的 disposition），改以會 FAIL 的斷言把該形狀釘住，「而不是藏在註解裡」。**請判斷這個處理是否足夠，還是該在本輪就修掉結構。**
4. `auth_binding_*` 三款可以為假，但它們保證的「授權」在本 repo 仍是 `structurally-vacuous`；可以為假的是**來源與值的核對**，不是第二方獨立核可。

另補一個順手發現的靜默漏洞：`checkpoint_ref` 定址不到任何 checkpoint 時，audit 掛在 checkpoint 上、整則事件不留痕，「沒被解除」與「沒有這則事件」在輸出上分不開。現在落 `structural` 紀錄並以斷言釘住。

### 五、門檻

`root_cause_id` `resolution-authorization-binding-not-validated-against-event` 已跨 R1／R2 兩個 attempt。**若你判定本輪仍屬同家族，即滿足第一條件、下一輪強制 `escalate`——請沿用該家族名，不要另起新名把門檻洗掉。**

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api`／`gh run view` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**並附證據；首輪須明確寫出「首輪，無前輪 accepted blocking finding」那一節。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` 多行格式（`card_id:` 與 `source_sha:` **各自獨立成行**），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍，並寫明起訖 delimiter 是「**本規則之後的下一個**」。

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**、值含 ` #` 須整個值加引號。


## Comment 5266794821 · 2026-08-12T12:27:21Z

## ⚠️ PM 更正：派審詞寫的 `iteration：2` 與狀態面不符，實際是 **1**——而落差的成因是 PM 漏了一步

Log 上最後一筆 `handoff` 記的是 `iteration 1`。派審詞寫 2，**錯的是派審詞**。

### 成因，以及它為什麼不只是打錯字

R2 判 REQUEST_CHANGES 之後，正確的流程是：

```
review（↩退回） → handoff --next-stage implementation（iteration +1，交回執行者）
              → 執行者修 → handoff --next-stage review
```

**PM 跳過了中間那一步。** 我直接派了修復執行者，然後在它交回後跑 `handoff --next-stage review`。而 `iteration` 只在 `--next-stage implementation` 遞增（WF-22-CLI2 既有規則），於是它停在 1。

後果有兩層：

1. **數字不對**：本輪實質上是本卡的第三次交付（R1 `41a9f41` → R2 `b039c0b` → 本輪 `ba90b81`），但 `iteration` 顯示 1。
2. **更重要的一層：Log 上沒有任何一筆事件記載「本輪交回執行者」。** 從狀態面看，這張卡從 `↩退回` 直接變成 `🔍待查核`，中間那段修復期間**沒有留痕**。attempt 序列還在（每個 `handoff` 都帶 SHA），但「誰在什麼時候接手修」這件事，本輪只存在於 PM 的對話裡。

**同一批的 #52／#57／#58／#42 PM 都有跑那一步，只有本卡漏了。**

### PM 不追溯補建

事後補一則自稱當時作出的 `handoff` 是本專案明令禁止的形態（`review-escalation.md:61` 同旨）。**本則為前向更正，`iteration` 維持 1 不強行覆寫**——`--iteration` 是異常修正逃生門，拿它來蓋掉一個「事件根本沒發生」的落差，等於把漏留痕改寫成留過痕。

### 對查核者的實際影響

- **`attempt_id` 不受影響**：它由 `card_id-e{epoch}-{source_sha}` 構成，`ba90b81…` 是唯一的。
- **升級門檻不受影響**：門檻數的是**可計數 attempt** 與 `root_cause_id` 家族，不是 `iteration` 欄。本卡 `resolution-authorization-binding-not-validated-against-event` 已跨 R1／R2 兩個 attempt——**若本輪仍屬同家族即滿足第一條件、下一輪強制 `escalate`**，這一點不因 `iteration` 顯示 1 而改變。
- **前輪閉環義務不受影響**：R2-001 仍是 accepted blocking，本輪必須逐項回報。

**若你認為「修復期間無留痕」本身構成 finding，那是正當的**——`attribution` 應為 `coordinator`，PM 不代填也不預先辯護。

### 其餘不變

被審 SHA `ba90b81a52172a64c44702d70c93ca5835ddd0ad`、基線 `6e6e8abd650c76fa6a2173f5dff35f99038ca1e0`、本輪寫入集 `scripts/replay_escalation_rules.py` 單檔——**PM 已重驗，與 Log 最後一筆 `handoff` 一致**。上一則派審詞（`issuecomment-5266531397`）的其餘內容全部有效。

另附一項 PM 交叉對帳的結果，供你知悉：**同批送審的 [#42](https://github.com/ruan6047/ai-workflow/issues/42) 把 `escalation-resolution` 的 provisional pin 釘在本卡的 `b039c0b`**（前一個 attempt），而本卡現行 tip 是 `ba90b81`。PM 已比對兩者的 `templates/review-escalation.md` blob **逐位元組相同**（`ee823e2e…`），故該 pin 內容無誤。**但本輪若你要求本卡再動那個檔，該 pin 會失效**——請在 disposition 裡把這個相依講出來。


## Comment 5266870914 · 2026-08-12T12:34:38Z

<!-- wf-review-receipt:v1
card_id: WF-ESCALATION-RESOLUTION-GAP1
source_sha: ba90b81a52172a64c44702d70c93ca5835ddd0ad
report_sha256: c0f251a692f7ace2e228ba00530a8557fd2f08672b7cc913a8be2990ac72893a
-->
取材規則：起點為本規則之後的下一個 `--- report-begin ---` 結束換行後的第一個字元；終點為其後下一個 `--- report-end ---` 開始前的前一個換行前一個字元；UTF-8、LF、不 strip；排除 receipt HTML 註解、取材規則行、兩個 delimiter 行與它們之外的所有文字。

--- report-begin ---
core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1 rev-parse HEAD && git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1 merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD"
    observed: "HEAD=ba90b81a52172a64c44702d70c93ca5835ddd0ad，與最後 handoff SHA 一致；基線祖先檢查 exit 0。"
  - command: "git archive ba90b81a52172a64c44702d70c93ca5835ddd0ad | tar -x -C /tmp/wf39-review.7H1cBP && python3 /tmp/wf39-review.7H1cBP/scripts/replay_escalation_rules.py && python3 -m py_compile /tmp/wf39-review.7H1cBP/scripts/replay_escalation_rules.py"
    observed: "拋棄式副本 replay 114/114 通過，且 py_compile exit 0。"
  - command: "git diff --check 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 ba90b81a52172a64c44702d70c93ca5835ddd0ad && git diff --name-status 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 ba90b81a52172a64c44702d70c93ca5835ddd0ad"
    observed: "無 whitespace error；相對 fork point 的變更為 scripts/replay_escalation_rules.py 與前輪既有的 templates/review-escalation.md。"
  - command: "git show --format=%B --no-patch ba90b81a52172a64c44702d70c93ca5835ddd0ad | git interpret-trailers --parse"
    observed: "只解析出 Co-Authored-By；缺 Requested-by、Planned-by、Implemented-by。"
  - command: "git diff b039c0b08113382566d9b687087dea1f08f3915c ba90b81a52172a64c44702d70c93ca5835ddd0ad -- scripts/replay_escalation_rules.py"
    observed: "checkpoint_ref 與兩個事件宣稱欄位已分離；E9a 至 E9l 各以隔離反例打掉對應款次，resolution_clause_coverage() 機械彙總 audit 並斷言所有 RESOLUTION_CONDITIONS 都曾為 false。"
findings:
  - finding_id: "WF-ESCALATION-RESOLUTION-GAP1-R3-001"
    severity: major
    blocking: true
    finding_class: governance
    attribution: executor
    root_cause_id: "commit-trailer-required-but-missing"
    evidence: "AGENTS.md:10 與 AI_WORKFLOW.md §6 要求 T2 以上實作 commit 在訊息末端連續帶 Requested-by、Planned-by、Implemented-by。被審 ba90b81 的 interpret-trailers 輸出僅有 Co-Authored-By；三個必填 trailer 均不存在。"
    disposition: "不得將此 source SHA 視為通過交付。因已推送 commit 不得 amend，需求方須裁定例外或使本次執行嘗試失效後重新交付，並由後續 preflight 機械阻擋同類缺失。"
  - finding_id: "WF-ESCALATION-RESOLUTION-GAP1-R3-002"
    severity: major
    blocking: true
    finding_class: coordination
    attribution: coordinator
    root_cause_id: "implementation-stage-handoff-omitted"
    evidence: "Issue #39 的 PM 更正明載 R2 REQUEST_CHANGES 後，Coordinator 跳過 handoff --next-stage implementation，故本輪修復期間沒有 owner 與時間的 lifecycle event；AI_WORKFLOW.md §1 要求同一卡每階段僅一個 Stage Owner，§3 要求退回後先交回原執行者並遞增 iteration。"
    disposition: "不得追溯補造 handoff。需求方須以前向決策處置本 attempt 的可採信性與卡片狀態；在決策完成前不得以此段無留痕修復作為可 merge 的正常交付。"
prior_round_closure:
  - finding_id: "WF-ESCALATION-RESOLUTION-GAP1-R2-001"
    status: resolved
    root_cause_id: "resolution-authorization-binding-not-validated-against-event"
    evidence: "E9a 至 E9l 把前輪指出的五種情境及額外四款拆成可表達的最小反例；每例斷言失效款次恰為目標款、升級狀態維持。resolution_clause_coverage() 掃所有 E 段 resolution_audit，114/114 的 E 段覆蓋斷言通過。R2 的 authorization_binding 缺欄、同值手填、異值手填 E8 反例亦仍通過。"
scope_outside_findings:
  - item: "被審 worktree 的 scripts/__pycache__/ 為未追蹤檔，符合派審已知環境例外；本查核未在該 worktree 寫入。"
  - item: "resolution_basis 為列舉外值時，第 5、6 款會退化為真，但 E9e 已斷言 resolution_value fail-closed；本輪沒有依此擴大 finding。"

--- report-end ---

## Comment 5266877703 · 2026-08-12T12:35:17Z

<!-- wf-review-receipt:v1
card_id: WF-ESCALATION-RESOLUTION-GAP1
source_sha: ba90b81a52172a64c44702d70c93ca5835ddd0ad
report_sha256: c50c8f945acf8ca426506fc8719cf0b35b40e466453aa5715f4439e6fd8d70a0
-->
取材規則：起點為本規則之後的下一個 `--- report-begin ---` 結束換行後的第一個字元；終點為其後下一個 `--- report-end ---` 開始前的前一個換行前一個字元；UTF-8、LF、不 strip；排除 receipt HTML 註解、取材規則行、兩個 delimiter 行與它們之外的所有文字。

--- report-begin ---
core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1 rev-parse HEAD && git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1 merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD"
    observed: "HEAD=ba90b81a52172a64c44702d70c93ca5835ddd0ad，與最後 handoff SHA 一致；基線祖先檢查 exit 0。"
  - command: "git archive ba90b81a52172a64c44702d70c93ca5835ddd0ad | tar -x -C /tmp/wf39-review.7H1cBP && python3 /tmp/wf39-review.7H1cBP/scripts/replay_escalation_rules.py && python3 -m py_compile /tmp/wf39-review.7H1cBP/scripts/replay_escalation_rules.py"
    observed: "拋棄式副本 replay 114/114 通過，且 py_compile exit 0。"
  - command: "git diff --check 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 ba90b81a52172a64c44702d70c93ca5835ddd0ad && git diff --name-status 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 ba90b81a52172a64c44702d70c93ca5835ddd0ad"
    observed: "無 whitespace error；相對 fork point 的變更為 scripts/replay_escalation_rules.py 與前輪既有的 templates/review-escalation.md。"
  - command: "git show --format=%B --no-patch ba90b81a52172a64c44702d70c93ca5835ddd0ad | git interpret-trailers --parse"
    observed: "只解析出 Co-Authored-By；缺 Requested-by、Planned-by、Implemented-by。"
  - command: "git diff b039c0b08113382566d9b687087dea1f08f3915c ba90b81a52172a64c44702d70c93ca5835ddd0ad -- scripts/replay_escalation_rules.py"
    observed: "checkpoint_ref 與兩個事件宣稱欄位已分離；E9a 至 E9l 各以隔離反例打掉對應款次，resolution_clause_coverage() 機械彙總 audit 並斷言所有 RESOLUTION_CONDITIONS 都曾為 false。"
findings:
  - finding_id: "WF-ESCALATION-RESOLUTION-GAP1-R3-001"
    severity: major
    blocking: true
    finding_class: governance
    attribution: executor
    root_cause_id: "commit-trailer-required-but-missing"
    evidence: "AGENTS.md:10 與 AI_WORKFLOW.md §6 要求 T2 以上實作 commit 在訊息末端連續帶 Requested-by、Planned-by、Implemented-by。被審 ba90b81 的 interpret-trailers 輸出僅有 Co-Authored-By；三個必填 trailer 均不存在。"
    disposition: "不得將此 source SHA 視為通過交付。因已推送 commit 不得 amend，需求方須裁定例外或使本次執行嘗試失效後重新交付，並由後續 preflight 機械阻擋同類缺失。"
  - finding_id: "WF-ESCALATION-RESOLUTION-GAP1-R3-002"
    severity: major
    blocking: true
    finding_class: coordination
    attribution: coordinator
    root_cause_id: "implementation-stage-handoff-omitted"
    evidence: "Issue #39 的 PM 更正明載 R2 REQUEST_CHANGES 後，Coordinator 跳過 handoff --next-stage implementation，故本輪修復期間沒有 owner 與時間的 lifecycle event；AI_WORKFLOW.md §1 要求同一卡每階段僅一個 Stage Owner，§3 要求退回後先交回原執行者並遞增 iteration。"
    disposition: "不得追溯補造 handoff。需求方須以前向決策處置本 attempt 的可採信性與卡片狀態；在決策完成前不得以此段無留痕修復作為可 merge 的正常交付。"
prior_round_closure:
  - finding_id: "WF-ESCALATION-RESOLUTION-GAP1-R2-001"
    status: resolved
    root_cause_id: "resolution-authorization-binding-not-validated-against-event"
    evidence: "E9a 至 E9l 把前輪指出的五種情境及額外四款拆成可表達的最小反例；每例斷言失效款次恰為目標款、升級狀態維持。resolution_clause_coverage() 掃所有 E 段 resolution_audit，114/114 的 E 段覆蓋斷言通過。R2 的 authorization_binding 缺欄、同值手填、異值手填 E8 反例亦仍通過。"
scope_outside_findings:
  - item: "被審 worktree 的 scripts/__pycache__/ 為未追蹤檔，符合派審已知環境例外；本查核未在該 worktree 寫入。"
  - item: "resolution_basis 為列舉外值時，第 5、6 款會退化為真，但 E9e 已斷言 resolution_value fail-closed；本輪沒有依此擴大 finding。"
--- report-end ---

## Comment 5266881324 · 2026-08-12T12:35:39Z

<!-- wf-review-receipt:v1
card_id: WF-ESCALATION-RESOLUTION-GAP1
source_sha: ba90b81a52172a64c44702d70c93ca5835ddd0ad
report_sha256: c0f251a692f7ace2e228ba00530a8557fd2f08672b7cc913a8be2990ac72893a
-->
取材規則：起點為本規則之後的下一個 `--- report-begin ---` 結束換行後的第一個字元；終點為其後下一個 `--- report-end ---` 開始前的前一個換行前一個字元；UTF-8、LF、不 strip；排除 receipt HTML 註解、取材規則行、兩個 delimiter 行與它們之外的所有文字。

--- report-begin ---
core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1 rev-parse HEAD && git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1 merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD"
    observed: "HEAD=ba90b81a52172a64c44702d70c93ca5835ddd0ad，與最後 handoff SHA 一致；基線祖先檢查 exit 0。"
  - command: "git archive ba90b81a52172a64c44702d70c93ca5835ddd0ad | tar -x -C /tmp/wf39-review.7H1cBP && python3 /tmp/wf39-review.7H1cBP/scripts/replay_escalation_rules.py && python3 -m py_compile /tmp/wf39-review.7H1cBP/scripts/replay_escalation_rules.py"
    observed: "拋棄式副本 replay 114/114 通過，且 py_compile exit 0。"
  - command: "git diff --check 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 ba90b81a52172a64c44702d70c93ca5835ddd0ad && git diff --name-status 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 ba90b81a52172a64c44702d70c93ca5835ddd0ad"
    observed: "無 whitespace error；相對 fork point 的變更為 scripts/replay_escalation_rules.py 與前輪既有的 templates/review-escalation.md。"
  - command: "git show --format=%B --no-patch ba90b81a52172a64c44702d70c93ca5835ddd0ad | git interpret-trailers --parse"
    observed: "只解析出 Co-Authored-By；缺 Requested-by、Planned-by、Implemented-by。"
  - command: "git diff b039c0b08113382566d9b687087dea1f08f3915c ba90b81a52172a64c44702d70c93ca5835ddd0ad -- scripts/replay_escalation_rules.py"
    observed: "checkpoint_ref 與兩個事件宣稱欄位已分離；E9a 至 E9l 各以隔離反例打掉對應款次，resolution_clause_coverage() 機械彙總 audit 並斷言所有 RESOLUTION_CONDITIONS 都曾為 false。"
findings:
  - finding_id: "WF-ESCALATION-RESOLUTION-GAP1-R3-001"
    severity: major
    blocking: true
    finding_class: governance
    attribution: executor
    root_cause_id: "commit-trailer-required-but-missing"
    evidence: "AGENTS.md:10 與 AI_WORKFLOW.md §6 要求 T2 以上實作 commit 在訊息末端連續帶 Requested-by、Planned-by、Implemented-by。被審 ba90b81 的 interpret-trailers 輸出僅有 Co-Authored-By；三個必填 trailer 均不存在。"
    disposition: "不得將此 source SHA 視為通過交付。因已推送 commit 不得 amend，需求方須裁定例外或使本次執行嘗試失效後重新交付，並由後續 preflight 機械阻擋同類缺失。"
  - finding_id: "WF-ESCALATION-RESOLUTION-GAP1-R3-002"
    severity: major
    blocking: true
    finding_class: coordination
    attribution: coordinator
    root_cause_id: "implementation-stage-handoff-omitted"
    evidence: "Issue #39 的 PM 更正明載 R2 REQUEST_CHANGES 後，Coordinator 跳過 handoff --next-stage implementation，故本輪修復期間沒有 owner 與時間的 lifecycle event；AI_WORKFLOW.md §1 要求同一卡每階段僅一個 Stage Owner，§3 要求退回後先交回原執行者並遞增 iteration。"
    disposition: "不得追溯補造 handoff。需求方須以前向決策處置本 attempt 的可採信性與卡片狀態；在決策完成前不得以此段無留痕修復作為可 merge 的正常交付。"
prior_round_closure:
  - finding_id: "WF-ESCALATION-RESOLUTION-GAP1-R2-001"
    status: resolved
    root_cause_id: "resolution-authorization-binding-not-validated-against-event"
    evidence: "E9a 至 E9l 把前輪指出的五種情境及額外四款拆成可表達的最小反例；每例斷言失效款次恰為目標款、升級狀態維持。resolution_clause_coverage() 掃所有 E 段 resolution_audit，114/114 的 E 段覆蓋斷言通過。R2 的 authorization_binding 缺欄、同值手填、異值手填 E8 反例亦仍通過。"
scope_outside_findings:
  - item: "被審 worktree 的 scripts/__pycache__/ 為未追蹤檔，符合派審已知環境例外；本查核未在該 worktree 寫入。"
  - item: "resolution_basis 為列舉外值時，第 5、6 款會退化為真，但 E9e 已斷言 resolution_value fail-closed；本輪沒有依此擴大 finding。"
--- report-end ---

## Comment 5267045276 · 2026-08-12T12:51:19Z

<!-- wf-review-event:v1 card_id=WF-ESCALATION-RESOLUTION-GAP1 source_sha=ba90b81a52172a64c44702d70c93ca5835ddd0ad attempt_id=WF-ESCALATION-RESOLUTION-GAP1-e0-ba90b81a52172a64c44702d70c93ca5835ddd0ad -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-ESCALATION-RESOLUTION-GAP1`　attempt_id：`WF-ESCALATION-RESOLUTION-GAP1-e0-ba90b81a52172a64c44702d70c93ca5835ddd0ad`
- 查核者：GPT-5@Codex 子代理（需求方轉貼）；⚠️ 本卡收到三則收據 issuecomment-5266870914／5266877703／5266881324，PM 逐一驗算：三者被雜湊內容逐位元組相同（sha c0f251a6…），為同一份報告的重試，無歧義；轉錄採最後一則 5266881324　escalation_epoch：0
- source_sha：`ba90b81a52172a64c44702d70c93ca5835ddd0ad`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-12T20:51:18+08:00

### self_run（查核者實跑）

- `git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1 rev-parse HEAD && git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1 merge-base --is-ancestor 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 HEAD`
  - HEAD=ba90b81a52172a64c44702d70c93ca5835ddd0ad，與最後 handoff SHA 一致；基線祖先檢查 exit 0。
- `git archive ba90b81a52172a64c44702d70c93ca5835ddd0ad | tar -x -C /tmp/wf39-review.7H1cBP && python3 /tmp/wf39-review.7H1cBP/scripts/replay_escalation_rules.py && python3 -m py_compile /tmp/wf39-review.7H1cBP/scripts/replay_escalation_rules.py`
  - 拋棄式副本 replay 114/114 通過，且 py_compile exit 0。
- `git diff --check 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 ba90b81a52172a64c44702d70c93ca5835ddd0ad && git diff --name-status 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0 ba90b81a52172a64c44702d70c93ca5835ddd0ad`
  - 無 whitespace error；相對 fork point 的變更為 scripts/replay_escalation_rules.py 與前輪既有的 templates/review-escalation.md。
- `git show --format=%B --no-patch ba90b81a52172a64c44702d70c93ca5835ddd0ad | git interpret-trailers --parse`
  - 只解析出 Co-Authored-By；缺 Requested-by、Planned-by、Implemented-by。
- `git diff b039c0b08113382566d9b687087dea1f08f3915c ba90b81a52172a64c44702d70c93ca5835ddd0ad -- scripts/replay_escalation_rules.py`
  - checkpoint_ref 與兩個事件宣稱欄位已分離；E9a 至 E9l 各以隔離反例打掉對應款次，resolution_clause_coverage() 機械彙總 audit 並斷言所有 RESOLUTION_CONDITIONS 都曾為 false。

### findings（2，其中 blocking 2）

- **WF-ESCALATION-RESOLUTION-GAP1-R3-001**　severity=major　blocking=true　class=governance　attribution=executor　root_cause_id=`commit-trailer-required-but-missing`
  - evidence：AGENTS.md:10 與 AI_WORKFLOW.md §6 要求 T2 以上實作 commit 在訊息末端連續帶 Requested-by、Planned-by、Implemented-by。被審 ba90b81 的 interpret-trailers 輸出僅有 Co-Authored-By；三個必填 trailer 均不存在。
  - disposition：不得將此 source SHA 視為通過交付。因已推送 commit 不得 amend，需求方須裁定例外或使本次執行嘗試失效後重新交付，並由後續 preflight 機械阻擋同類缺失。
- **WF-ESCALATION-RESOLUTION-GAP1-R3-002**　severity=major　blocking=true　class=coordination　attribution=coordinator　root_cause_id=`implementation-stage-handoff-omitted`
  - evidence：Issue #39 的 PM 更正明載 R2 REQUEST_CHANGES 後，Coordinator 跳過 handoff --next-stage implementation，故本輪修復期間沒有 owner 與時間的 lifecycle event；AI_WORKFLOW.md §1 要求同一卡每階段僅一個 Stage Owner，§3 要求退回後先交回原執行者並遞增 iteration。
  - disposition：不得追溯補造 handoff。需求方須以前向決策處置本 attempt 的可採信性與卡片狀態；在決策完成前不得以此段無留痕修復作為可 merge 的正常交付。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5267136272 · 2026-08-12T12:59:26Z

## 需求方裁定（2026-08-12）：接受本 attempt，缺漏記錄不追溯補建

> ⚠️ **本則留言的來歷**：內容由需求方 `ruan6047` 明確核准，**文字由 PM（Claude Opus 5@Claude Code）代擬並代貼**。PM 的 `gh` 以 `ruan6047` 認證，故任何以 comment author 為據的授權檢查對 PM **恆真、無區辨力**；此限度已由 `WF-AMEND-AUTHZ-BINDING1`（#62）承接。**本則的實質授權是真的，其機械證明是空的。**

針對 `WF-ESCALATION-RESOLUTION-GAP1-R3-002`（major、blocking、coordination、`attribution: coordinator`、`root_cause_id: implementation-stage-handoff-omitted`）。

查核者逐字要求：「不得追溯補造 handoff。**需求方須以前向決策處置本 attempt 的可採信性與卡片狀態**；在決策完成前不得以此段無留痕修復作為可 merge 的正常交付。」

### 裁定

**本 attempt（`ba90b81a52172a64c44702d70c93ca5835ddd0ad`）的可採信性維持有效，缺漏的 `handoff --next-stage implementation` 事件不追溯補建。**

### 理由

**一、缺的是流程記錄，不是交付證據。** 查核者自己判 `core_pain_resolved: yes`，並在 `prior_round_closure` 明列 R2-001 為 `resolved`，evidence 是它在拋棄式副本實跑的 replay 114/114 與 E9a–E9l 的逐款隔離。**那些證據附著在 commit 上，不附著在缺的那筆事件上。** 作廢本 attempt 不會讓任何一項證據變得更可信。

**二、重做產出的是同一份程式碼。** 執行者會在同一個基線上做同樣的修改，得到內容相同、SHA 不同的交付，而**「當時真正發生的時間與 owner」在重做後依然補不回來**——重做記的是重做那一刻，不是原本那一刻。用一輪換一個仍然不真的紀錄。

**三、缺漏本身已有前向留痕。** PM 於 `issuecomment-5266794821` 已完整記錄成因（跳過 `--next-stage implementation`，而 `iteration` 只在該處遞增，故停在 1）、影響範圍（`attempt_id`、升級門檻、前輪閉環義務三者皆不受影響）、以及不追溯的理由。**該筆更正就是這段空白的紀錄。**

### 明確不涵蓋的部分

- **`iteration` 維持 1，不以 `--iteration` 覆寫。** 那個旗標是異常修正逃生門；拿它蓋掉一個「事件根本沒發生」的落差，等於把漏留痕改寫成留過痕。**本卡的 `iteration` 欄與實際交付輪次不一致，此為已知且刻意保留的狀態。**
- **本裁定只處置本 attempt，不建立通則。** 下一次 PM 再漏同一步，不得引用本則主張已獲授權。
- **`R3-002` 的 `attribution: coordinator` 與其 `root_cause_id` 不因本裁定改變。** 它是成立的 finding，處置方式是接受後果而非否認缺陷。

### 對 `R3-001`（trailer 缺失）不生效

本裁定**不涵蓋** `R3-001`。該項須依其 disposition 另行處置，且需求方已裁定開卡統一處理該缺陷家族（見下一則）。


## Comment 5367197392 · 2026-08-21T08:12:05Z

## 派審：ai-workflow#39 `WF-ESCALATION-RESOLUTION-GAP1` R4

⚠️ 審核對象 **`ruan6047/ai-workflow#39`**（不是 cpbl）。

```
PR：      https://github.com/ruan6047/ai-workflow/pull/116
被審 SHA：28ac73b6c3a93e4939e3321f866a5997b55f67b0
基線：    39b53e41a8d6d2d05413e0581fb089cdadf3c2c2（以 git merge-base origin/main HEAD 算得，非抄 origin/main）
分支：    claude/WF-ESCALATION-RESOLUTION-GAP1
worktree：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1
iteration：2（⚠️ 見下方「iteration 欄不可信」）
寫入集：  templates/review-escalation.md、scripts/replay_escalation_rules.py、docs/CONTRACT_TOOL_RECONCILE.md
```

⭐ **本卡雖為 T3，卡面第 4 行明訂查核者須跨模型家族**：「本卡補的正是 PM 自己被逼著自創欄位的缺口，查核者須跨模型家族以避免 PM 自我背書」。

### 本輪射程（很窄）

前三輪（2026-08-12）的交付未變。本輪只做兩件：

1. **補登記 4 個契約符號的處置**到 `docs/CONTRACT_TOOL_RECONCILE.md`
2. **把分支更新到 main**（落後 9 天）

起因：PM 於 2026-08-21 開 PR #116，讓 CI **第一次在合併結果（`refs/pull/116/merge`）上跑**，`tests` 轉紅：

```
FAILED tests/test_contract_tool_reconcile.py::test_live_dispositions_cover_every_gap
AssertionError: 55 個缺口與登記處置不符
  - event/carried-forward（absent）／event/continue-same-executor（absent）
  - event/escalation-resolution（mention-only）／event/fresh-ruling（absent）
⚠️ 實際缺口 58、登記 54
```

⭐ **三輪查核抓不到不是查核疏失**——`contract_tool_reconcile` 由 `#97`（`6561e04`）帶入 main，**晚於本卡最後一輪**。

### R1–R3 的閉環狀態（PM 已複查，請獨立複驗）

| Finding | 狀態 | PM 查到的依據 |
|---|---|---|
| `R1-001` `resolution-authorization-binding-not-validated-against-event` | resolved | R2 報告：§5 第 7 款改 adapter 加蓋，E8 三反例均使 resolution 無效 |
| `R2-001`（`:1288-1296` 五款無反例、四款結構性恆真） | resolved | R3 收據 `prior_round_closure: status: resolved` |
| `R3-001` commit 缺三個 trailer | **構造上免責** | `ba90b81` = `2026-08-12T19:20:36+08:00` < `doctor.py:752 TRAILER_GUARD_EPOCH` = `2026-08-13T00:00:00+08:00` |
| `R3-002` coordinator 跳過 implementation handoff | **已裁定** | 需求方 `2026-08-12T12:59:26Z`「接受本 attempt，缺漏記錄不追溯補建」 |

三輪皆 `core_pain_resolved: yes`。**請逐項回報閉環狀態並附你自己的證據**；若判定仍開啟，請沿用原 `root_cause_id` 家族名。

### PM 交付前自驗（你不必信，請自己重跑）

- 寫入集零越界：`git diff --stat` 只有宣告的三檔
- 三筆新 commit 皆帶 `Requested-by`／`Planned-by`／`Implemented-by`
- 四筆既有已查核 commit 的 SHA **未變**（用 merge 非 rebase）
- `tests` pass 40s（合併結果）／`tests (branch head)` pass 41s；`mergeState: CLEAN`；未 merge

### ⚠️ 兩項未閉，請一併裁量（不是要你放行，是要你判）

**(1) 執行者用本地 merge，而 `AI_WORKFLOW.md:229` §6.1 第 3 款寫「一律本地 rebase」。**

該款逐字：「分支更新**禁 `gh pr update-branch`**：它產生 synthetic merge、**污染歷史與守衛判讀**；一律本地 rebase ＋ `git push --force-with-lease`」。標的是那個按鈕，**但它自陳的危害在本地 merge 上同樣發生**。

執行者拒絕 rebase 的兩個理由，PM 已複驗成立：
- rebase 會換掉 `058100ad`，而 **main 的 `cli/src/wf_cli/validation.py:783` 與 `:829` 逐字引用該 SHA**，且 `cli/src/` 在寫入集外改不了
- rebase 重設 committer date 為今天，會把四筆 **epoch 前免責** 的 commit 翻成**無法修的違規**（依約不得改寫已推送內容）

PM 查到先例：`origin/claude/WF-22-CLI4`（`#9`，**已結案合併**）分支上有 **3 個基線更新 merge commit 且全部零 trailer**；`DEV-COMMIT-TRAILER-GUARD1` 與 `DEV-MAIN-RED-CAPABILITY-FLAGS1-FIX1` 各 2 個。⚠️ **但它們全在 epoch 前，守衛未及**——所以先例證明的是「本地 merge 是既有慣例」，不是「守衛接受它」。

**(2) merge commit `b6900c6` 缺 `Reviewed-by`——全分支唯一違規。**

`required_trailers("merge_clean")` = `(Reviewed-by,)`（`doctor.py:895-896`）。而該規則的形狀假設是「`merge_clean` ＝ 卡片合併」；`b6900c6` 是**基線更新 merge**，無人查核也無從查核。

⭐ **執行者拒絕填一個捏造的查核者把守衛換綠**，改在 commit 訊息明寫偏離。

PM 的建議（**不是裁定**）：以 squash 合併使該 commit 不落地 main，並把守衛的形狀缺口（不分辨卡片合併與基線更新）另記。**請你判這個建議成不成立**，以及守衛的形狀缺口該不該成為本輪的 finding。

### ⚠️ 執行者自列的未驗（八項，全數轉入，請視為你的起點不是終點）

1. **CI 綠不等於那四條處置在語意上正確**——`--check` 只比對 `key → 判定字串`，判斷不了 `補寫入者` 對不對
2. `absent`／`mention-only` 是機械輸出；對 `escalation-resolution` 逐處讀碼確認四處全非寫入路徑，但三個取值只做到 `grep -r` 在 `cli/src` 零出現，**未窮舉其他字面形態**
3. **未讀 `WF-22-CLI4` 那張卡**，不知它是否真涵蓋此 writer（歸屬是引自 `validation.py` 的訊息）
4. merge commit 的 `Reviewed-by` 違規未解決
5. §6.1.3 的張力未取得裁定
6. 快照重跑只證明「零判定變化、零消失列」，**未逐列人工核對每個新 `檔案:行` 錨點**
7. **三筆 doc commit 而非一筆**——原想 amend 收成一筆被 harness 權限分類器擋下
8. 未 merge、未留言、未碰 `cli/src`、未動 `docs/ROADMAP.md`、未跑任何 wfcli 寫入動詞

### ⭐ 執行者主動查到的三件（請驗它們對不對）

1. **`structurally-vacuous` 判 `ok` 是字面碰撞，不是本節已實作。** 它的 writer（`validation.py:480/483/486`）導出的是 **accepted 標記**的授權綁定；`review.py:614` 註解逐字聲明「這**不是** #39 的那個欄位」
2. **`escalation-resolution` 與 `review-correction` 不是同型缺口**：前者 `相關動詞=無`、後者 `相關動詞=review`（初稿寫成同型，已於 `6d54318` 自行更正）
3. **對帳器少看到第五處字面** `--escalation-resolution`（`checkpoint_cmd.py:104` 的 argparse 保留旗標）：`_contains_symbol` 因 `_WORDISH` 含 `-` 回 `False`。⭐ **而那條詞界正是用來擋 `deployment-status-change` 誤命中 `status-change`**——不是沒人想到，是明著擋住

### ⚠️ iteration 欄不可信

Project 顯示 `iteration 2`，但需求方 2026-08-12 的裁定逐字寫「**`iteration` 維持 1，不以 `--iteration` 覆寫**…本卡的 `iteration` 欄與實際交付輪次不一致，**此為已知且刻意保留的狀態**」。之後 `ba4755f4` 的批次 handoff 仍把它撞到 2。**請以「本輪是 R4」為準，不要以欄位值推算輪次。**

### 交付格式

依 `templates/review-prompt.md` §5。三項強制：

1. **逐項回報 R1-001／R2-001／R3-001／R3-002 的閉環狀態**（`resolved`／`withdrawn`／仍開啟）並附你自己的證據
2. **五個 schema 欄位自己填**（`core_pain_resolved`／`review_result`／`self_run`／`findings`／`delivery_status`）
3. **留收據**：多行格式、報告全文同帖、取材規則寫死並寫明起訖 delimiter 是「本規則之後的下一個」

⚠️ **留言中不得出現 review 事件那個機讀前綴的完整字樣**（前綴後緊接半形冒號的那串）。契約把任何含該前綴的留言判為受管轄，**引用即停機**——實測 `#15`／`#17` 兩張已結案卡都因派審留言引用而被凍。轉述時寫「event marker」即可。

⚠️ **不得 merge**（PM 保留 merge 動作）。⚠️ **不得跑任何 wfcli 寫入動詞**（狀態面由 PM 寫）。


## Comment 5367319357 · 2026-08-21T08:20:55Z

<!-- wf-review-receipt:v1
card_id: WF-ESCALATION-RESOLUTION-GAP1
source_sha: 28ac73b6c3a93e4939e3321f866a5997b55f67b0
report_sha256: 7a7f7a1ce15976fb4a25913dd713f2f7d327b79238fe879d8039a95affe1f879
-->

取材規則：UTF-8、LF、無 strip；雜湊範圍起點是本規則之後的下一個 `--- report-begin ---` delimiter 結束 LF 後的第一個位元組，終點是其後下一個 `--- report-end ---` delimiter 前的 LF（該 LF 不含）；排除 receipt HTML 註解、本規則、兩個 delimiter 行及其餘文字。

--- report-begin ---
本輪核心痛點「強制升級後，需求方選擇維持同一執行者在契約內無表示法」已消失；本輪補登記也正確。但交付分支仍有一項阻擋性的治理缺口，故不能放行。

## 前輪 finding 閉環

- `R1-001`：**resolved**。在被審 SHA 實跑 `python3 scripts/replay_escalation_rules.py` 為 114/114 通過；E8 的缺欄、手填 `structurally-vacuous`、手填 `substantive` 三反例均使 resolution 無效，且同值手填僅由來源款擋下，證明不再只是比對值。
- `R2-001`：**resolved**。同一 replay 的 E9a–E9l 與「E 段覆蓋」機械彙總通過；錯誤 trigger、epoch、重複解除、列舉外值、二次沿用與缺 `carried_by` 都各有可使對應條款為假的反例，不再保留原先的結構性恆真缺口。
- `R3-001`：**resolved（構造上免責）**。我讀取 `ba90b81` 的 committer date 為 `2026-08-12T19:20:36+08:00`，早於 `cli/src/wf_cli/doctor.py:752` 的 `TRAILER_GUARD_EPOCH=2026-08-13T00:00:00+08:00`；該 commit 的缺 trailer 不落入後設 guard 的可修正範圍。
- `R3-002`：**resolved（已裁定）**。需求方在 [2026-08-12 的裁定](https://github.com/ruan6047/ai-workflow/issues/39#issuecomment-5267136272) 明確接受 `ba90b81` attempt、禁止追溯補建 implementation handoff，且裁定只作用於本 attempt；這正是 R3 處置要求的前向決策。

## 本輪四個符號與回歸

`python3 scripts/contract_tool_reconcile.py --check` 回報「58 個缺口全部有登記處置，判定一致」；專屬測試 `cd cli && uv run pytest tests/test_contract_tool_reconcile.py -q -rA` 為 33 passed。

我另讀取 JSON 輸出及寫入路徑：

- `escalation-resolution` 為 `mention-only`、writer 0、相關動詞=無；`checkpoint_cmd.py:261–265` 也直接說明 writer 尚未實作。
- `fresh-ruling`、`carried-forward`、`continue-same-executor` 都為 `absent`。
- §6 的 disposition snapshot 確實登記上述四個 `event/` key，與機械判定一致。
- `--escalation-resolution` 是 `checkpoint_cmd.py:104` 的保留且拒收旗標，並非 writer；其被詞界規則漏掃已在 §4.7/§5 如實揭露。
- `structurally-vacuous` 的既有 writer 是 accepted 標記的另一套欄位；`review.py:614–617` 明示不是 #39 的欄位，故未被誤當成本卡 writer。
- [WF-22-CLI4 #9](https://github.com/ruan6047/ai-workflow/issues/9) 的資源宣告包含 `validation.py` 與 `checkpoint_cmd.py)，其卡面也把 checkpoint writer 列為驗收；把實作歸屬交由該卡／需求方裁量的說法有依據。

相對指定基線 `39b53e41a8d6d2d05413e0581fb089cdadf3c2c2` 的 diff 只觸及三個已宣告檔案，且 `git diff --check` 無輸出。PR #116 的 branch-head 與 merge-result checks 目前皆為成功，head 仍為被審 SHA，PR 未合併。

```yaml
core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C /tmp/ai-workflow-r4-28ac73b rev-parse HEAD; git -C /tmp/ai-workflow-r4-28ac73b status --short; git -C /tmp/ai-workflow-r4-28ac73b merge-base 39b53e41a8d6d2d05413e0581fb089cdadf3c2c2 28ac73b6c3a93e4939e3321f866a5997b55f67b0"
    observed: "HEAD 與指定 SHA 完全相同；進入查核前工作區乾淨；merge-base 輸出指定基線。"
  - command: "cd /tmp/ai-workflow-r4-28ac73b && python3 scripts/replay_escalation_rules.py"
    observed: "114/114 通過；E8 與 E9 覆蓋均通過。"
  - command: "cd /tmp/ai-workflow-r4-28ac73b && python3 scripts/contract_tool_reconcile.py --check; cd cli && uv run pytest tests/test_contract_tool_reconcile.py -q -rA"
    observed: "對帳器報 58 個缺口全部有登記處置；專屬測試 33 passed。"
  - command: "git -C /tmp/ai-workflow-r4-28ac73b diff --name-only 39b53e41a8d6d2d05413e0581fb089cdadf3c2c2...28ac73b6c3a93e4939e3321f866a5997b55f67b0; git -C /tmp/ai-workflow-r4-28ac73b diff --check 39b53e41a8d6d2d05413e0581fb089cdadf3c2c2...28ac73b6c3a93e4939e3321f866a5997b55f67b0"
    observed: "僅 docs/CONTRACT_TOOL_RECONCILE.md、scripts/replay_escalation_rules.py、templates/review-escalation.md；無 whitespace error。"
  - command: "git -C /tmp/ai-workflow-r4-28ac73b show --format=%B --no-patch b6900c6af406ecb3828cf9d2bb8496741a96cdfc | git interpret-trailers --parse; nl -ba /tmp/ai-workflow-r4-28ac73b/AI_WORKFLOW.md | sed -n '229,235p'; nl -ba /tmp/ai-workflow-r4-28ac73b/cli/src/wf_cli/doctor.py | sed -n '891,902p'"
    observed: "b6900c6 有 Requested-by、Planned-by、Implemented-by，沒有 Reviewed-by；§6.1.3 要求本地 rebase；required_trailers(merge_clean) 只要求 Reviewed-by。"
findings:
  - finding_id: "WF-ESCALATION-RESOLUTION-GAP1-R4-001"
    severity: major
    blocking: true
    finding_class: governance
    attribution: executor
    root_cause_id: "branch-update-policy-and-merge-trailer-noncompliance"
    evidence: "b6900c6 是以本地 merge 將 39b53e4 併入分支，與 AI_WORKFLOW.md §6.1.3 的「一律本地 rebase」不符；其 shape 為 merge_clean，而 doctor.required_trailers() 要求 Reviewed-by，實際 trailer 解析沒有該欄。"
    disposition: "不得以 squash merge 視為修復：它只避免 b6900c6 進 main，不能使送審分支符合既有 preflight。需求方須留下可稽核的前向裁定：要麼為此精確的基線更新建立狹義例外（適用條件、查核與 trailer 規則、對 b6900c6 的效力），要麼要求在不捏造 Reviewed-by 的前提下重建合規分支。現行規則未區分「卡片 merge」與「基線更新 merge」；但 clean merge 仍整合兩個父提交、可被查核，因此這不是可直接忽略的守衛形狀缺口，也不另拆成第二個 implementation finding。"
delivery_status: "↩退回"
```

## 裁量結論

PM 的「squash 合併即可」建議不成立：它處理 main 的線性歷史，沒有處理被審 SHA 已包含的 policy 違反與缺 trailer。b6900c6 的兩項偏離合併為上述單一治理 finding；不計入 executor escalation，但在需求方作出可稽核的前向裁定前，交付不可放行。
--- report-end ---

## Comment 5367425415 · 2026-08-21T08:28:04Z

## Contract baseline：WF-ESCALATION-RESOLUTION-GAP1

```yaml
wf_contract_baseline: v1
contract: templates/review-escalation.md
effective_from: "2026-08-21T16:28:03+08:00"
declared_by: ruan6047
rationale: "需求方 2026-08-21 明示 cutover。R1／R2／R3 三則 review event 寫於 2026-08-12，早於 escalation 帳契約落地，故事件流中沒有可讀的帳事實；依 review-escalation.md:276 那是「未知」而非「不計數」，wfcli review 因此拒絕寫入 R4 裁決。切 baseline 的目的僅為讓 R4 的裁決能進入狀態面——baseline 之前的三則事件依 :276 維持原貌，不追溯改寫、不推定其計數與否。⚠️ 本次 cutover 不對 R4 的裁決內容表態：R4 為 REQUEST_CHANGES、含一項 major blocking 治理 finding（R4-001），該 finding 的處置另循需求方前向裁定。"
```

---

此 marker 為 one-shot cutover（`review-escalation.md` §5）：不得附在 review 等其他事件上，啟用後再次出現必須 fail loud。本行之前的 attempt 依契約「維持原貌」，其 `counts_toward_escalation` 為**未知**（而非「不計數」）；本行之後的 review event 一律由 `wfcli review` 附上結構化 counts 事實。

## Comment 5367432851 · 2026-08-21T08:28:34Z

<!-- wf-review-event:v1 card_id=WF-ESCALATION-RESOLUTION-GAP1 source_sha=28ac73b6c3a93e4939e3321f866a5997b55f67b0 attempt_id=WF-ESCALATION-RESOLUTION-GAP1-e0-28ac73b6c3a93e4939e3321f866a5997b55f67b0 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-ESCALATION-RESOLUTION-GAP1`　attempt_id：`WF-ESCALATION-RESOLUTION-GAP1-e0-28ac73b6c3a93e4939e3321f866a5997b55f67b0`
- 查核者：GPT-5@Codex（需求方轉貼；收據 issuecomment-5367319357，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`28ac73b6c3a93e4939e3321f866a5997b55f67b0`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-21T16:28:33+08:00

### self_run（查核者實跑）

- `git -C /tmp/ai-workflow-r4-28ac73b rev-parse HEAD; git -C /tmp/ai-workflow-r4-28ac73b status --short; git -C /tmp/ai-workflow-r4-28ac73b merge-base 39b53e41a8d6d2d05413e0581fb089cdadf3c2c2 28ac73b6c3a93e4939e3321f866a5997b55f67b0`
  - HEAD 與指定 SHA 完全相同；進入查核前工作區乾淨；merge-base 輸出指定基線。
- `cd /tmp/ai-workflow-r4-28ac73b && python3 scripts/replay_escalation_rules.py`
  - 114/114 通過；E8 與 E9 覆蓋均通過。
- `cd /tmp/ai-workflow-r4-28ac73b && python3 scripts/contract_tool_reconcile.py --check; cd cli && uv run pytest tests/test_contract_tool_reconcile.py -q -rA`
  - 對帳器報 58 個缺口全部有登記處置；專屬測試 33 passed。
- `git -C /tmp/ai-workflow-r4-28ac73b diff --name-only 39b53e41a8d6d2d05413e0581fb089cdadf3c2c2...28ac73b6c3a93e4939e3321f866a5997b55f67b0; git -C /tmp/ai-workflow-r4-28ac73b diff --check 39b53e41a8d6d2d05413e0581fb089cdadf3c2c2...28ac73b6c3a93e4939e3321f866a5997b55f67b0`
  - 僅 docs/CONTRACT_TOOL_RECONCILE.md、scripts/replay_escalation_rules.py、templates/review-escalation.md；無 whitespace error。
- `git -C /tmp/ai-workflow-r4-28ac73b show --format=%B --no-patch b6900c6af406ecb3828cf9d2bb8496741a96cdfc | git interpret-trailers --parse; nl -ba /tmp/ai-workflow-r4-28ac73b/AI_WORKFLOW.md | sed -n '229,235p'; nl -ba /tmp/ai-workflow-r4-28ac73b/cli/src/wf_cli/doctor.py | sed -n '891,902p'`
  - b6900c6 有 Requested-by、Planned-by、Implemented-by，沒有 Reviewed-by；§6.1.3 要求本地 rebase；required_trailers(merge_clean) 只要求 Reviewed-by。

### findings（1，其中 blocking 1）

- **WF-ESCALATION-RESOLUTION-GAP1-R4-001**　severity=major　blocking=true　class=governance　attribution=executor　root_cause_id=`branch-update-policy-and-merge-trailer-noncompliance`
  - evidence：b6900c6 是以本地 merge 將 39b53e4 併入分支，與 AI_WORKFLOW.md §6.1.3 的「一律本地 rebase」不符；其 shape 為 merge_clean，而 doctor.required_trailers() 要求 Reviewed-by，實際 trailer 解析沒有該欄。
  - disposition：不得以 squash merge 視為修復：它只避免 b6900c6 進 main，不能使送審分支符合既有 preflight。需求方須留下可稽核的前向裁定：要麼為此精確的基線更新建立狹義例外（適用條件、查核與 trailer 規則、對 b6900c6 的效力），要麼要求在不捏造 Reviewed-by 的前提下重建合規分支。現行規則未區分「卡片 merge」與「基線更新 merge」；但 clean merge 仍整合兩個父提交、可被查核，因此這不是可直接忽略的守衛形狀缺口，也不另拆成第二個 implementation finding。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-ESCALATION-RESOLUTION-GAP1-e0-28ac73b6c3a93e4939e3321f866a5997b55f67b0
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（待指派）
findings:
  - finding_id: WF-ESCALATION-RESOLUTION-GAP1-R4-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: governance
    attribution: executor
    root_cause_id: branch-update-policy-and-merge-trailer-noncompliance
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5367447565 · 2026-08-21T08:29:38Z

## 需求方前向裁定（2026-08-21）：`R4-001` 的處置

PM 代擬代貼。回應 `WF-ESCALATION-RESOLUTION-GAP1-R4-001` 的 disposition 逐字要求：「需求方須留下可稽核的前向裁定：要麼為此精確的基線更新建立狹義例外（適用條件、查核與 trailer 規則、對 `b6900c6` 的效力），要麼要求在不捏造 `Reviewed-by` 的前提下重建合規分支。」

### 先接受查核者對 PM 的兩處更正

1. **「squash 合併即可」不成立。** 查核者逐字：「它只避免 `b6900c6` 進 main，**不能使送審分支符合既有 preflight**。」PM 把問題當成「main 的歷史乾不乾淨」，而它是「**被審的那個 SHA 本身含不含違反**」。squash 動的是前者。**PM 的建議撤回。**
2. **兩項偏離合併為單一治理 finding、不計入 executor escalation** —— 接受。

### ⭐ PM 補三項讀碼事實，它們決定了處置形狀

**(a) 守衛只驗 trailer 的「鍵存在」，從不看值。**

```python
def trailer_keys(self) -> set[str]:            # doctor.py:789-790
    return {k.lower() for k, _ in self.trailers}

missing = tuple(k for k in required if k.lower() not in present)   # :915
```

⭐ **所以 merge commit 上的 `Reviewed-by` 從來沒有證明過任何人查核了任何東西——它證明的是有人打了那個鍵。** 本 finding 的機械內容是「一個鍵不存在」，不是「沒有人查核」。

**(b) 守衛的作者已經明文否決「基線更新 merge」是一種可導出的形狀。** `doctor.py:863-867` 逐字：

> **基線更新 merge**：也是 merge commit，同一格處理。本模組**刻意不區分**它與整合 merge——兩者都只是 `parents >= 2`，誰是 main 取決於你站在哪個 ref 上看，**那是脈絡不是 commit 自身的性質**。既然導不出來就不假裝導得出來。

⇒ **任何以「這是基線更新 merge」為條件的 trailer 例外，構造上不可能有機械執行者。** 而以 `merge_clean` 為條件的例外會**連帶豁免併入 main 的卡片 merge**——那正是 `Reviewed-by` 最該存在的地方。以 `--commit-range` 為條件也不行：該旗標 `刻意不給預設`（`doctor_cmd.py:59`），範圍由操作者給。

**(c) rebase 在本卡構造上不可行，PM 已複驗。** `doctor.py:827` 逐字「分流界線（**committer date**）」；rebase 與 cherry-pick 都重設 committer date ⇒ 四筆早於 `TRAILER_GUARD_EPOCH` 的已查核 commit 全數翻成 violation，而依約不得改寫其內容 ⇒ **無法修**。另 rebase 會換掉 `058100ad`，而 main 的 `cli/src/wf_cli/validation.py:783`／`:829` 逐字引用該 SHA。

### 裁定：分成兩半，各走各的

**一、trailer 那一半：不建立例外，改為把「不適用」寫進事件。**

重建的基線更新 merge 須帶 `Reviewed-by: —（基線更新 merge，無查核對象）`。

⭐ 這不是捏造查核者，是本專案既有的慣用法——需求方 2026-08-12 的裁定（記於 `cli/src/wf_cli/review.py:657-661`）逐字：

> 正解不是不寫，是**寫下去、並把「這道閘門今天沒有鑑別力」寫在事件上**，讓查核者與未來的消費者從事件本身讀得到。

同族既有實例：`authorization_binding: structurally-vacuous`、`escalation_account: not-asserted`、Project 欄位以 `—` 表不適用。**依 (a)，守衛本來就只驗鍵存在，所以填一個誠實的「無查核對象」與填任何值在機械上等價，但在留痕上誠實。**

**二、rebase 那一半：建立狹義例外，寫進 `AI_WORKFLOW.md` §6.1.3。**

- **適用條件**（兩項須同時成立，由撰寫派工包者判定並在派工包內具名）：(i) rebase 會使 **main 上已合併的碼**所引用的 SHA 失效；(ii) rebase 會把早於 `TRAILER_GUARD_EPOCH` 的 commit 推過界線，使其翻成無法修正的違規。
- **查核與 trailer 規則**：例外只免除「必須 rebase」，**不免除任何 trailer**。該 merge commit 仍須帶 `merge_clean` 所要求的 `Reviewed-by`，值依上一項填「無查核對象」。
- **⚠️ 誠實標注**：本例外**沒有機械執行者**——依 (b)，「這是基線更新 merge」導不出來，所以它是**派工包層的約定**，由撰寫者判定、由查核者複核。不得在 `AI_WORKFLOW.md` 或任何地方宣稱它已機械化。
- **對 `b6900c6` 的效力**：**不追溯適用**。`b6900c6` 缺 `Reviewed-by`，例外不免除 trailer，故它仍不合規。

**三、因此本卡須重建分支——但不得 force-push。**

執行者已回報 amend ＋ `--force-with-lease` 被 harness 權限分類器擋下。**改以新分支重建**：自 `ba90b81`（四筆已查核 commit 的最後一筆，committer date 仍為 2026-08-12、免責不變）開新分支 → 以帶齊四個 trailer（含 `Reviewed-by: —（基線更新 merge，無查核對象）`）的訊息重做基線更新 merge → 取回 `aeda16a`／`6d54318` 兩筆文件 commit → push 新分支 → 重開或改指 PR。

⭐ **這樣四筆已查核 commit 的 SHA 一個都不變**（不 rebase、不 cherry-pick 它們），`058100ad` 仍可達，main 的引用不斷。

### ⚠️ 未閉、須另案處置（不阻擋本卡）

1. **`AI_WORKFLOW.md` 是 canonical，改它會影響 cpbl-analytics**（該專案以 stub 指向本檔）。§6.1.3 的例外條文屬跨專案契約變更，**不在本卡射程**，須另開卡。**在該卡落地前，本裁定就是那條例外的權威出處。**
2. ⭐ **守衛的 `Reviewed-by` 只驗鍵存在**（上列 (a)）——這使該欄在所有 merge commit 上都不具區辨力，不只在基線更新 merge 上。**這是一個比本 finding 更大的形狀問題**，`DEV-COMMIT-TRAILER-GUARD1`（#63）已 CLOSED，無承接者。記錄於此，是否開卡由需求方裁定。
3. `contract-baseline` 已於 2026-08-21T16:28:03+08:00 切出（issuecomment-5367425415），**僅為讓 R4 裁決能進入狀態面**；baseline 之前的三則事件依 `review-escalation.md:276` 維持原貌。⚠️ 該指令自陳跨卡唯一性目前只是約定、沒有機械執行者。


## Comment 5367677791 · 2026-08-21T08:46:59Z

## 派審：ai-workflow#39 `WF-ESCALATION-RESOLUTION-GAP1` R5

⚠️ 審核對象 **`ruan6047/ai-workflow#39`**。

```
PR：      https://github.com/ruan6047/ai-workflow/pull/117   ⚠️ #116 已關（見下）
被審 SHA：ba4f1e2dbc149e4488075fe2015a34fa7e18fecd
基線：    39b53e41a8d6d2d05413e0581fb089cdadf3c2c2（git merge-base origin/main HEAD 算得）
分支：    claude/WF-ESCALATION-RESOLUTION-GAP1-r5
worktree：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-escalation-resolution-gap1-r5
iteration：3
寫入集：  templates/review-escalation.md、scripts/replay_escalation_rules.py、docs/CONTRACT_TOOL_RECONCILE.md
```

⭐ 卡面第 4 行明訂查核者須**跨模型家族**。

### 本輪射程極窄：只重建 commit 圖，內容一個字未改

R4 判 `REQUEST_CHANGES`，唯一 finding `R4-001`（major／blocking／governance）：`b6900c6` 是本地 merge（與 `AI_WORKFLOW.md` §6.1.3「一律本地 rebase」不符），且 shape 為 `merge_clean` 而缺 `Reviewed-by`。

需求方已於 [issuecomment-5367447565](https://github.com/ruan6047/ai-workflow/issues/39#issuecomment-5367447565) 下前向裁定，**請先整份讀完**。摘要：

1. **trailer 那一半不建立例外**，改為把「不適用」寫進事件：`Reviewed-by: —（基線更新 merge，無查核對象）`。依據是需求方 2026-08-12 記於 `cli/src/wf_cli/review.py:657-661` 的原則。
2. **rebase 那一半建立狹義例外**，⚠️ **對 `b6900c6` 不追溯適用**，且明文標注**該例外沒有機械執行者**、屬派工包層約定。
3. 故重建分支。⚠️ **不得 force-push**（harness 權限分類器擋下），改自 `ba90b81` 開新分支。

**本輪實際編輯檔案數為 0。**

### PM 獨立複驗（非轉述執行者，請你再獨立跑一次）

| 項目 | 結果 |
|---|---|
| 最終樹與 R4 被審的 `28ac73b6` 逐位元相同 | `git diff --stat` 無輸出；兩者 `^{tree}` 皆 `9f9280ae9f9e4c46390405d6dd04a9dfc093efc7` |
| 四筆已查核 commit 仍是祖先且 SHA 未變 | `058100ad`／`41a9f419`／`b039c0b0`／`ba90b81a` 逐一 `merge-base --is-ancestor` 皆 YES；committer date 全部仍 2026-08-12 |
| `doctor --commit-trailers --require-planned-by` | **違規 0／界線前 4／合規 4** |
| 對照組（R4 被審的 `28ac73b`，同指令） | **違規 1**（`b6900c6` 缺 `Reviewed-by`） |
| PR #117 | `tests` pass 37s（合併結果）／`tests (branch head)` pass 41s；`headRefOid=ba4f1e2dbc14`；`CLEAN`；`OPEN` |
| 寫入集 | diff 只有宣告的三檔 |
| 舊分支 | `claude/WF-ESCALATION-RESOLUTION-GAP1` 保留於 origin（`058100ad` 的可達性靠它） |

### ⚠️ 兩項與派工包不同，請裁量

**(1) 重放的是三筆今日文件 commit，不是派工包寫的兩筆。**

`aeda16a`／`6d54318`／`28ac73b` → 新對應 `1ebd089`／`83e3276`／`ba4f1e2`。

⭐ **錯的是派工包**——PM 漏算了 `28ac73b` 本身也是文件 commit。只取兩筆會使最終樹**不等於** `28ac73b6`，與驗收第一條直接衝突。**執行者以驗收條款為準，判斷正確。** 三筆皆今日、post-epoch、帶齊三個 trailer，cherry-pick 重設 committer date 對它們無害。

**(2) 執行者未替新分支保留 worktree。**

理由：scratchpad 路徑會被回收；放 `.claude/worktrees/` 又會產生一個**沒有卡註冊**的 worktree，而它被禁止跑 wfcli 註冊。**PM 已於交付後補建** worktree 並以 `assign` 更新卡面欄位（上表路徑即為現值）。

### ⚠️ 執行者自列的未驗（七項，全數轉入）

1. **未重跑 R1–R4 任何 finding 的複驗**——R5 射程只有重建，內容未動，未重新檢視 `templates/review-escalation.md` §4／§5 的實質正確性
2. **未讀 `validation.py:783`／`:829` 確認那兩行今天仍逐字寫著 `058100ad`**——只驗到該 SHA 目前可達。⭐ 那是 rebase 例外適用條件 (i) 的事實基礎，**值得你補驗**
3. ⭐ **`AI_WORKFLOW.md:229` 仍逐字寫「一律本地 rebase ＋ `git push --force-with-lease`」**——例外目前只存在於 issue 留言。**你若只讀 canonical，會看到與本分支相反的規則。** 需求方已裁定該條文屬跨專案 canonical 變更、另案處置，在該卡落地前那則裁定即為權威出處
4. 未驗證 #117 body 是否符合任何模板要求（PR body 不是 wfcli 事件）
5. 未驗證關閉 #116 對狀態面的影響
6. `cli/0` 這個未追蹤檔在 session 前就存在，非本輪產生
7. 本機跑過 `pytest 1052 passed`、`uv lock --check` 通過、`replay_escalation_rules.py` 114/114——但那是**本機**結果

### ⚠️ 為什麼關 #116 而不是改指

GitHub 的 `PATCH /repos/{owner}/{repo}/pulls/{n}` **不接受 `head` 欄位**（實測傳不存在的分支回 200 而 `head.ref` 原封不動；`gh pr edit` 只有 `--base`）。**「改指」在平台上做不到。** #116 `comments 0`／`reviews 0`，查核留痕全在 issue #39，關掉不孤立任何東西。

### 交付格式

依 `templates/review-prompt.md` §5。三項強制：

1. **逐項回報 `R4-001` 的閉環狀態**（`resolved`／`withdrawn`／仍開啟）並附你自己的證據
2. **五個 schema 欄位自己填**
3. **留收據**：多行格式、報告全文同帖、取材規則寫死並寫明起訖 delimiter 是「本規則之後的下一個」

⚠️ **留言中不得出現 review 事件那個機讀前綴的完整字樣**（前綴後緊接半形冒號）。契約把任何含該前綴的留言判為受管轄，**引用即停機**。轉述時寫「event marker」。

⚠️ **不得 merge**。⚠️ **不得跑任何 wfcli 寫入動詞**。


## Comment 5368428121 · 2026-08-21T10:03:25Z

<!-- wf-review-receipt:v1
card_id: WF-ESCALATION-RESOLUTION-GAP1
source_sha: ba4f1e2dbc149e4488075fe2015a34fa7e18fecd
report_sha256: a3d33ae30e3d5cf8e5f389006bc0dc59de9f993a14852d6ea092d008b48ddca1
-->

取材規則：UTF-8、LF、無 strip；雜湊範圍起點是本規則之後的下一個 `--- report-begin ---` delimiter 結束 LF 後的第一個位元組，終點是其後下一個 `--- report-end ---` delimiter 前的 LF（該 LF 不含）；排除 receipt HTML 註解、本規則、兩個 delimiter 行及其餘文字。

--- report-begin ---
本輪只驗 R4-001 與重建後 commit 圖；未重新擴審內容，因為被審樹與 R4 被審樹逐位元相同。

## R4-001 閉環

`R4-001`（`branch-update-policy-and-merge-trailer-noncompliance`）：**resolved**。

我的證據：

1. 被審 SHA `ba4f1e2dbc149e4488075fe2015a34fa7e18fecd` 的 tree 與 R4 SHA `28ac73b6c3a93e4939e3321f866a5997b55f67b0` 都是 `9f9280ae9f9e4c46390405d6dd04a9dfc093efc7`；`git diff --quiet` 成功。故 R5 只改 commit 圖，沒有偷偷改交付內容。
2. 四筆既有受審 commit `058100ad`、`41a9f419`、`b039c0b`、`ba90b81` 都仍是被審 SHA 的祖先，SHA 未變，committer date 皆仍為 2026-08-12，保持在 trailer guard epoch 之前。
3. 新的基線 merge `e4f4fdac` 與被取代的 `b6900c6` tree 同為 `fd3ba233d12dfc8eadcd256d75b76bd74f5f2fd2`；它保留同一個 clean merge 結果，但改以連續 trailer 區塊記錄 `Requested-by`、`Planned-by`、`Implemented-by` 與 `Reviewed-by: —（基線更新 merge，無查核對象）`。
4. 以派審釘定基線（而非我本機過舊的 `origin/main` ref）執行 `wfcli doctor --commit-trailers --commit-range 39b53e41a8d6d2d05413e0581fb089cdadf3c2c2..HEAD --require-planned-by`，結果為：違規 0／界線前 4／合規 4。
5. 我直接讀取 `validation.py:783`、`:829`，兩處仍逐字引用 `058100ad`；因此前向裁定的第一個狹義例外條件成立。前向裁定已明說例外只免除 rebase、絕不免除 trailer，且不追溯適用舊的 `b6900c6`；R5 的新 merge 確實遵守此界線。
6. 指定 worktree 的 HEAD 是被審 SHA、工作區乾淨；Issue body 已有對應 r5 branch/worktree 的 assign 與 handoff 記錄。派工包漏算第三筆文件 commit 的偏差不構成 finding：三筆皆 post-epoch、均在同一樹等價重放中必須存在，且 doctor 已驗其 trailer。

前向裁定確實留下「rebase 例外尚無機械執行者」的限制，這是如實揭露的派工包層約定，不是 R4-001 的未處置部分；本輪由需求方裁定與查核者核對其兩個精確適用條件。守衛只驗 trailer key、不驗 `Reviewed-by` 值的較大形狀問題已在裁定中明列為另案決策，沒有被本輪偽裝成已修。

PR #117 的 branch-head 與 merge-result checks 均成功，`headRefOid` 為被審 SHA、PR 保持 OPEN/CLEAN。#116 已 CLOSED，且我以 GitHub API 確認其 comments=0、reviews=0；關閉未遺失查核留痕。

```yaml
core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "git -C /tmp/ai-workflow-r5-ba4f1e2 rev-parse HEAD HEAD^{tree} 28ac73b6c3a93e4939e3321f866a5997b55f67b0^{tree}; git -C /tmp/ai-workflow-r5-ba4f1e2 diff --quiet 28ac73b6c3a93e4939e3321f866a5997b55f67b0 ba4f1e2dbc149e4488075fe2015a34fa7e18fecd"
    observed: "HEAD 與指定 SHA 相同；兩個 tree 都是 9f9280ae9f9e4c46390405d6dd04a9dfc093efc7；內容 diff 為空。"
  - command: "cd /tmp/ai-workflow-r5-ba4f1e2/cli && uv run wfcli doctor /tmp/ai-workflow-r5-ba4f1e2 --registry none --commit-trailers --commit-range 39b53e41a8d6d2d05413e0581fb089cdadf3c2c2..HEAD --require-planned-by"
    observed: "違規 0／界線前 4／合規 4；使用明示基線，避免過舊 origin/main 造成範圍污染。"
  - command: "git -C /tmp/ai-workflow-r5-ba4f1e2 rev-parse e4f4fdac9d5d7e9fc7b3374f240b332180ff3956^{tree} b6900c6af406ecb3828cf9d2bb8496741a96cdfc^{tree}; git -C /tmp/ai-workflow-r5-ba4f1e2 show --format=%B --no-patch e4f4fdac9d5d7e9fc7b3374f240b332180ff3956 | git interpret-trailers --parse"
    observed: "兩個 merge tree 都是 fd3ba233d12dfc8eadcd256d75b76bd74f5f2fd2；新 merge 的四個必要 trailer 均被解析。"
  - command: "nl -ba /tmp/ai-workflow-r5-ba4f1e2/cli/src/wf_cli/validation.py | sed -n '780,832p'; gh pr view 117 --repo ruan6047/ai-workflow --json state,mergeStateStatus,headRefOid,statusCheckRollup"
    observed: "validation.py:783/:829 仍引用 058100ad；PR #117 OPEN、CLEAN、head 為被審 SHA，兩項 tests 成功。"
findings: []
delivery_status: "✅通過"
```

R4-001 已閉環；本 R5 無新增 finding。
--- report-end ---

## Comment 5368439517 · 2026-08-21T10:04:38Z

<!-- wf-review-event:v1 card_id=WF-ESCALATION-RESOLUTION-GAP1 source_sha=ba4f1e2dbc149e4488075fe2015a34fa7e18fecd attempt_id=WF-ESCALATION-RESOLUTION-GAP1-e0-ba4f1e2dbc149e4488075fe2015a34fa7e18fecd -->
## 查核裁決：APPROVE

- 卡：`WF-ESCALATION-RESOLUTION-GAP1`　attempt_id：`WF-ESCALATION-RESOLUTION-GAP1-e0-ba4f1e2dbc149e4488075fe2015a34fa7e18fecd`
- 查核者：GPT-5@Codex（需求方轉貼；收據 issuecomment-5368428121，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`ba4f1e2dbc149e4488075fe2015a34fa7e18fecd`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-21T18:04:37+08:00

### self_run（查核者實跑）

- `git -C /tmp/ai-workflow-r5-ba4f1e2 rev-parse HEAD HEAD^{tree} 28ac73b6c3a93e4939e3321f866a5997b55f67b0^{tree}; git -C /tmp/ai-workflow-r5-ba4f1e2 diff --quiet 28ac73b6c3a93e4939e3321f866a5997b55f67b0 ba4f1e2dbc149e4488075fe2015a34fa7e18fecd`
  - HEAD 與指定 SHA 相同；兩個 tree 都是 9f9280ae9f9e4c46390405d6dd04a9dfc093efc7；內容 diff 為空。
- `cd /tmp/ai-workflow-r5-ba4f1e2/cli && uv run wfcli doctor /tmp/ai-workflow-r5-ba4f1e2 --registry none --commit-trailers --commit-range 39b53e41a8d6d2d05413e0581fb089cdadf3c2c2..HEAD --require-planned-by`
  - 違規 0／界線前 4／合規 4；使用明示基線，避免過舊 origin/main 造成範圍污染。
- `git -C /tmp/ai-workflow-r5-ba4f1e2 rev-parse e4f4fdac9d5d7e9fc7b3374f240b332180ff3956^{tree} b6900c6af406ecb3828cf9d2bb8496741a96cdfc^{tree}; git -C /tmp/ai-workflow-r5-ba4f1e2 show --format=%B --no-patch e4f4fdac9d5d7e9fc7b3374f240b332180ff3956 | git interpret-trailers --parse`
  - 兩個 merge tree 都是 fd3ba233d12dfc8eadcd256d75b76bd74f5f2fd2；新 merge 的四個必要 trailer 均被解析。
- `nl -ba /tmp/ai-workflow-r5-ba4f1e2/cli/src/wf_cli/validation.py | sed -n '780,832p'; gh pr view 117 --repo ruan6047/ai-workflow --json state,mergeStateStatus,headRefOid,statusCheckRollup`
  - validation.py:783/:829 仍引用 058100ad；PR #117 OPEN、CLEAN、head 為被審 SHA，兩項 tests 成功。

### findings（0，其中 blocking 0）

- （無）

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-ESCALATION-RESOLUTION-GAP1-e0-ba4f1e2dbc149e4488075fe2015a34fa7e18fecd
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
