# #147 WF-CARD-BRIEF-BACKFILL1 198 張卡中 190 張沒有簡介
- state: closed  created: 2026-08-25T18:00:35Z  closed: 2026-08-27T02:28:43Z
- url: https://github.com/ruan6047/ai-workflow/issues/147
- comments: 12

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；要判斷「這張卡的路由訊號該寫什麼」需要讀懂每張卡在做什麼；⛔ 非機械轉換。母體 190 張，量大且每張都要判斷。）　查核：待指派（建議 主力型；查核要判斷回填的內容是**路由訊號**還是**摘要**——§6.3 逐字指出那是兩回事，且實讀 70 個既有 skill description 時最短六個全部是摘要。⛔ 非紅線（不改碼、不改動詞）。）
- Initiative：WF-STAGE-STATE-TWO-AXIS1　spec 基線：b169c2424c0401c169104312f2fa807c01345feb
- DB：db_scope=none
- 服務的原始目標：ROADMAP §0 目標 2「可稽核的內容」——canonical §6.3 逐字要求每張卡必有簡介，而該條今日**無機械執行者**（`--brief` 可選、`validation.py` 不驗）⇒ 規則存在但母體 96% 未遵守。

## 簡介
<!-- card-brief:begin -->
為既有卡回填簡介。**適用時機**：要判斷某張既有卡與手上的工作有沒有語意相關時；或要評估 §6.3 的遵守率時。⛔ 非射程：不改 `--brief` 的可選性、不加 `validation.py` 的必填檢查（那會讓所有既有卡的動詞失效）；⛔ 不代寫核心痛點或驗收；⛔ 不在本卡決定回填的品質判準——那由研究輪產出。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：**canonical §6.3 要求「每張卡必有簡介」，而實測 198 張中只有 8 張有。**⚠️ 2026-08-26 量測（`brief.MARKER_WHEN` 與 `brief.MARKER_NON_SCOPE` 逐張比對，⛔ 非人工判讀）：有簡介區塊 **8 張**、兩個形狀要求皆滿足 **8/8**，其餘 **190 張沒有**。⇒ 讀者要決定「這張卡跟我有沒有關係」時，190 張卡上沒有任何路由訊號，只能讀核心痛點全文。⭐ 而 §6.3 逐字指出簡介抓的是**語意相關**——資源宣告抓同檔、`root_cause_id` 抓同根因、**三者不重疊** ⇒ 缺了它，語意相關的卡今天沒有任何機制找得到彼此。⚠️ 實例：`aiwf#122` 與 `WF-STAGE-STATE-TWO-AXIS1` 語意相關，但檔不同、根因不同 ⇒ 前兩者都抓不到。⛔ 寫入通道已存在（`open`／`amend` 皆有 `--brief`），缺的是**回填**。切片定義見 https://github.com/ruan6047/ai-workflow/issues/130#issuecomment-5391005830 的 S5。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/tests/test_brief_backfill_quota.py",
    "file:scripts/brief_backfill/a6_strict.py",
    "file:scripts/brief_backfill/analyze_cost.py",
    "file:scripts/brief_backfill/assemble_final.py",
    "file:scripts/brief_backfill/backfill.py",
    "file:scripts/brief_backfill/census.py",
    "file:scripts/brief_backfill/collect_drafts.py",
    "file:scripts/brief_backfill/guard.py",
    "file:scripts/brief_backfill/measure_a10.py",
    "file:scripts/brief_backfill/measure_b2.py",
    "file:scripts/brief_backfill/measure_v2.py",
    "file:scripts/brief_backfill/measure_v2_blayer.py",
    "file:scripts/brief_backfill/prove_guard_load_bearing.py",
    "file:scripts/brief_backfill/quota.py",
    "file:scripts/brief_backfill/relatedness.py",
    "file:scripts/brief_backfill/run_all_checks.sh",
    "file:scripts/brief_backfill/run_all_checks_b2.sh",
    "file:scripts/brief_backfill/run_all_checks_b3.sh",
    "file:scripts/brief_backfill/select_batch2.py",
    "file:scripts/brief_backfill/select_pilot.py",
    "file:scripts/brief_backfill/select_rest.py",
    "file:scripts/brief_backfill/snapshot_population.py",
    "file:scripts/brief_backfill/verify_invariants.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] ⚠️ 本清單於 2026-08-26 依 29 輪研究輪填實（開卡時刻意留白，canonical §6.4.1 的界線是「離開規劃前」）。⛔ 所有數字須**交付當下現場重量**，本清單記的是量法與判準。
- [ ] **A1 母體逐字釘死並自證**：交付須附回填當下重跑的原始輸出，含「item 總數／有簡介 N／缺簡介 N／雙居所漂移 N」四個數字，⛔ 不接受只寫結論。⚠️ 母體會動（版控快照實測 ≈ +5.7 張/日）⇒ ⛔ 不得沿用研究輪的 201／11／190／189。
- [ ] **A2 具名排除 `aiwf#15`**：它的 body 在 `## Log` 前有字面 `\n`，`amend --brief` 對它 rc≠0（實測）。⛔ **不修**——引用 `aiwf#105` 的 A13 逐字裁定（終態且 fail-open 貢獻 0）與 `aiwf#141` 的劃界（屬 `amend` 排版修復 runbook 的既有缺口）。⇒ 分母寫成 **N−1** 並逐字說明排除依據。
- [ ] **A3 `#140` 走不同路徑——⚠️ 本條於 2026-08-26 依查核 R1-02 更正**：`WF-RESOURCE-HEADING-SUFFIX1-PROBE-ASSIGN1` 是**雙居所漂移**（Project 欄位有簡介、body 沒有），⛔ 不是「缺簡介」。⛔ **原文寫「回填必須把欄位既有值逐字寫進 body」，那與實際交付不符**——本卡**把 #140 具名排除、完全沒有回填它**，查核者的獨立重跑口徑亦同（缺簡介 2 張＝`aiwf#15` 與 `#140`；雙居所漂移仍為 1 且就是 `#140`）。⇒ 現行條文：**#140 排除於本卡射程之外**，其漂移由後續卡處理。⚠️ 原文對危害的描述仍然成立、⛔ 不得刪除：若真要回填它，`amend_cmd` 的舊值只取自 body，覆蓋會讓 Log 記成「（原本沒有）」，即 `card.py` 逐字稱的「資料遺失加上留痕說謊」。
- [ ] **A4 分層派工，⛔ 不當同質母體**：A 層約 149 張可自 body 草擬；**B 層 40 張是 2026-08-04 cutover 遷移卡**，body 只有 `## Spec` 外連，內容在 `ruan6047/cpbl-analytics` 的凍結 SHA `2f52562f575412a0a39b515a4436edd2831b2f65` 之 `docs/tasks/`（恰 40 檔、227 KB）⇒ **必須實讀該檔才可草擬**；C 層 1 張（`#140`）走 A3。⛔ 只讀 Issue body 就替 B 層草擬視為不合格。
- [ ] **A5 ⭐ 輸入約束（紅線）**：任何寫入的簡介文字**不得含 `str.splitlines()` 認得的任一分行字元**。依據是 2026-08-26 在真實卡面上的往返實測：`amend_brief` **10 個單字元全穿**（連 `\n` 都不擋），⚠️ **另測 CRLF 雙字元序列亦穿**（2026-08-26 依查核 R1-08 更正：原文寫「11 個字元」把單字元與雙字元序列混計），含 `\n## Log` 的值會使卡面出現兩個 `## Log` ⇒ **該卡當場變成 `aiwf#15` 那個永久不可修改的狀態**。⇒ **回填腳本須在呼叫 `amend` 之前自行拒收**，⛔ 不得依賴 `WF-MARKER-WRITE-BOUNDARY1`（💡需求、未落地）。⭐ 這條使本卡**不阻塞於**該卡。 ⭐ **並新增第二條紅線（2026-08-26 先導批實撞）**：簡介文字的 **UTF-8 位元組長度不得超過 1012**。⚠️ Project v2 TEXT 欄位的上限是**位元組不是字元**（實測界線 L ∈ [1012, 1024]：1011B/523字元 與 1012B/524字元 過；1025B/531字元、1045B/439字元、1083B/589字元 全失敗）。⛔ 門檻取實際寫成功過的最大值 **1012**，⛔ 不取「看起來像答案」的 1024。⭐ **而超限的後果不是乾淨失敗**：`amend` 回 rc=2 且其 docstring 逐字宣稱「未寫入任何狀態」，**實際上 body 已寫成功、只有 Project 欄位失敗**（`set_field_value` 拋 `GhError` 逃出 rc 契約）⇒ 該卡當場落入雙居所漂移。先導批 10 張有 **3 張**因此半寫入。⚠️ 這也使 canonical §6.3 的「⛔ 不設任何字數」在**欄位那一半機械上不成立**。
- [ ] **A6 形狀＋跨界具名**：每則簡介除通過 `brief.validate_shape` 外，`⛔ 非射程：` 之後須至少含一個**指向卡外的具名對象**（卡 ID／issue 號／檔路徑／`§` 節號／表名／API 路由）。⚠️ 該清單刻意比研究輪的 P1 寬——實測 P1 原始詞彙表對 DATA／UX 家族系統性低估。⛔ 本條是**篩不是閘**：不通過須逐張說明理由，⛔ 不得自動退回。
- [ ] **A7 節流與可續跑**：⚠️⚠️ **本條的數字已於 2026-08-26 第二次更正——先前的 228 點是壞儀器量出來的，⛔ 勿再引用**。⭐ 成因：`gh api rate_limit`（REST）**量不到 GraphQL 消耗**——實測同一時刻 `used=0`（`reset` 每次讀取都 +1，沒在記帳）與 `used=73` 兩個狀態並存，40 次連讀有 4 次讀到後者，序列**非單調**（5000 → 4935 → 5000）；跑完 20 次 `ensure_fields` 後連取 8 次全讀到 0 ⇒ 算出 **−76 點**。「取 max(used)」救不了。權威來源是 **GraphQL 自己的 `rateLimit` 欄位**（連讀 6 次完全一致，同時刻 REST 說 `used=0`）。⇒ **換儀器後的實測值**：`amend --brief` 底線 **24 點**（157 張中 **120 張恰為 24**、中位 24、平均 24.9、max 48），延遲中位 **37.9 秒**；`ensure_fields`（零建立）**3.00 點／2.03 秒**（N=10）。⭐ **框架也要跟著更正：綁手腳的是延遲不是額度**——額度天花板 5000÷24 ＝ **208 張/hr**，延遲天花板 3600÷37.9 ＝ **95 張/hr**；158 張實跑全程 `waited_sec = 0`，**一次節流等待都沒觸發**，實跑 105 分鐘跨越兩次重置而**額度從未見底**。⛔ 原文的「每小時上限約 21 張」「180 張需 ≥ 8.6 小時」皆為假，⛔ 其中「204 點（89%）來自兩次 `list_fields`」的拆解同樣出自壞儀器，僅「`ensure_fields` 現為 3 點」這個結論成立——它由**兩種獨立方法**證實（跨家族查核者的 REST 差值 4183→4180，與執行者的 GraphQL `rateLimit` 3.00）。⚠️ 先導批那兩筆 **435／447 點**現判為**與本儀器缺陷形狀相符但未證實**——當時原始取樣沒留 `reset` 欄位，⛔ 無從回溯判定，⛔ 亦不得讀成「該現象不存在」。腳本須：每張獨立、失敗不影響其他張、可自任意中斷點續跑、每張前檢查**GraphQL `rateLimit`**（⛔ 不是 REST `rate_limit`）餘額並自動等待。⚠️⚠️ **原文的「⛔ 不得一次跑完」已被實際交付違反，2026-08-26 依查核 R1-03 誠實記載於此**：第三批一次跑完 158 張（實跑 105 分鐘、`waited_sec` 全 0）。⛔ **拿不出任何一則正式裁定 supersede 這一句的留言** ⇒ 依 R1-03 給的兩條路，本卡選**誠實記為違反原驗收**，⛔ 不編造裁定來源。背景是需求方選了丁案（做滿至完成），但那則決定針對的是「要不要做完剩下的卡」，⛔ 不是針對本條的分批要求 ⇒ **不足以構成 supersede**。本條原本的理由（額度見底、失敗連鎖）事後證明前提有誤：換儀器後額度從未見底、一次節流都沒觸發，⇒ ⛔ 但「前提有誤」不等於「條文自動失效」，那需要一次明示的裁定，而它不存在。⭐ 依賴已解除：`WF-CLI-ENSURE-FIELDS-DOUBLE-READ1`（`aiwf#151`）已於 2026-08-26 合併為 `b169c242`。
- [ ] **A8 優先序**：第一批必須包含 **`aiwf#122` 與 `aiwf#130`**——canonical §6.3 逐字用這兩張當「語意相關但資源宣告與 `root_cause_id` 都抓不到」的唯一例子，而**兩張今天都沒有簡介** ⇒ 該論證目前自我不成立。
- [ ] **A9 ROADMAP 登記**：依 `docs/ROADMAP.md` §6 於 §3 登記本卡並註明服務目標 2；⚠️ 排進「必要」或「降級 Backlog」由需求方裁定，執行者 ⛔ 不得自行決定。
- [ ] **A10 ⭐ 價值論證已於 2026-08-26 由需求方裁定更換**（`issuecomment-5422461485`）。⛔ **不得以「canonical §6.3 要求」當主要論證**（§0.1 自己逐字寫「⛔ 未驗證簡介對 AI 判斷相關性的實效」）；⛔ **亦不得引用 `WF-OPEN-DUPLICATE-DETECT1` 卡面的舊實害**——該卡自己於 2026-08-24 的 Log 逐字記載「實查兩者毫無關係……該證據無法成立」。⇒ **改用以下三條（全部現場重算，⛔ 交付時須重跑並附時點）**：**(1)** 語意相關邊 **247** 條中資源宣告只抓得到 **41** 條＝**16.6%**，⛔ 其餘 **206 條（83.4%）今天沒有任何機制找得到**（⚠️ 2026-08-26 依查核 R1-04 更正：原文的 248／40／16.1%／208 是更早的量測，母體已動，而同卡 A11 早已改用新數字 ⇒ 兩處自我不一致）；**(2)** ⛔ **原報的 `21/203` 判為 `unreproducible`（2026-08-26）**——執行者用四種區段定義各跑一次（母體 204）得 **7／8／8／16**，無一為 21，且 204 張**全部**都有 `## 驗收條件` 標題 ⇒ 差距不是切不到區段；⭐ 該數字由 PM 報出而**未隨數字載明判準**，PM 現亦拿不出當初的判準 ⇒ ⛔ **不得再被任何一方引用為證據**（執行者刻意沒去搜一份能湊出 21 的詞表——那是看著答案調判準）；**(3)** ⭐ **經查證的實害（2026-08-26，當事人自陳、可複驗）**：PM 差點開出兩張重複卡（S2 已存在 `DEV-ROADMAP-GATE-RESEARCH-STATUS1`、S3 已由 `WF-CARD-BRIEF-AND-TWO-AXIS-WRITE1` 做掉），而**三個機制無一攔得住**——資源宣告比不了（待開的新卡還沒有宣告）、`root_cause_id` 讀不到（住在 review finding 裡）、簡介兩張都沒有；實際攔下它的是需求方的一句話與 PM 的人工掃描。
- [ ] **A11 ⭐ V2 於 2026-08-26 由需求方裁定改判為「通過」**，⛔ 不再是 `undecidable`。丁案做滿 158 張後實得 **187 條 GT-A 邊、來源卡 115 張**，解除了原本的構造性不可判定（原文：20 張隨機卡只帶 10 條 GT 邊、power = 0.058，需 ≈70 條邊 ≈140 張卡而池只剩 178）。**裁決口徑為卡面事前釘死的 GT-A／strict**：簡介抓回 **48/187 = 25.7%** vs 資源宣告基準 **41/247 = 16.6%**，二項檢定 **p = 0.0011**、McNemar 配對（b=40, c=24）**p = 0.0300**、檢定力對實測效果量 **0.897**／對假設的 30% 為 **0.995**。⛔ **但四組必須全部留在卡面**：**GT-B／strict 為 13.2% vs 17.8%，p = 0.99 不顯著**（GT-A／ext 35.8%、GT-B／ext 32.4% 皆顯著）。⇒ ⛔ **不得把本條讀成「簡介的價值已被普遍證實」**——成立的只有 GT-A／strict 這一個口徑；⛔ 亦不得事後改用 GT-B 推翻它，那是換母體。⚠️ B 層前兩批的零命中已證實為 **GT 取材面的假象**：改以凍結 spec 為 GT 來源後，B 層抓回 **27/55 = 49.1%**。
- [ ] **A12 ⛔ 序位條件已於 2026-08-26 達成並結清。** 原文：`WF-CLI-ENSURE-FIELDS-DOUBLE-READ1`（`aiwf#151`）落地前不派下一批。該卡已合併為 `b169c242`（擴射程改用原生 GraphQL 查詢），其後 158 張一次跑完。⚠️ **原文的「剩餘 160 張 × 實測 241 點/張 ≈ 7.6 小時額度」為假**——241 點與 A7 的 228 點同樣出自 REST `rate_limit` 這個壞儀器（詳見 A7）。換 GraphQL `rateLimit` 後實測 **24 點/張**：160 張＝3,840 點，**額度只需 1 個視窗**（< 5,000）；真正的限制是延遲中位 37.9 秒 ⇒ 160 張需 **101 分鐘**，時間上跨 2 個視窗。⇒ ⛔ 「那是唯一會改變成本量級的順序」這句**在額度軸上不成立**（它改變的是 `ensure_fields` 那 3 點，不是每張 24 點的主體）；⛔ 不得再被引為排序依據。
- [ ] **A13 ⭐ 需求方於 2026-08-27 在更正後的前提上重新確認甲案：接受本卡資源宣告的顯示側漂移。** ⚠️ 先前版本的裁定理由（「該欄位沒有機器消費者」）是 PM 未查證的斷言、經查核 R2-02 證明為假，⛔ 不得再被引用。**正確的裁定敘述**：安全互斥閘門不讀 Project 欄位；snapshot／Ledger 顯示會低估資源，需求方知悉後接受此顯示側漂移。⇒ 成立的事實：**23** 個明確 `file:` 已在 body（⚠️ 2026-08-27 依查核 R3-01 補上第 23 條 `file:cli/tests/test_brief_backfill_quota.py`——canonical `AI_WORKFLOW.md:347` 明定重現工具屬交付物），`assign` 走 `parse_block(item.body)`／`try_parse_block(other.body)`、⛔ 從不讀 Project 欄位 ⇒ **安全面未破**。欄位寫不進去是因為 `db_scope=none；` ＋ **23** 個 token ＝ **1037 字元／1083 位元組**，超過該欄位實測上限 **1012**（見 A5）⇒ **超出 71**，最多容得下約 21 條 ⇒ ⛔ 本卡在機械上**沒有任何做法**能修好它。⇒ 有機器消費者：`snapshot.py` 讀 `資源宣告` 成 `resource_summary`，Ledger 渲染為 `res_summary = r.resource_summary or (…)` ⇒ **欄位優先**，body 的 **23** 條只在欄位為空時才浮現。⭐ **本卡是全母體唯一一張「欄位主動宣稱無資源而 body 有」的卡**（2026-08-27 實測 204 張：逐 token 一致 140／欄位從未寫入且 body 也空 31／欄位比 body 窄 9／欄位比 body 寬 7／散文且 body 也空 6／欄位從未寫入但 body 有 5／body 解析不出來 5／**主動說假話 1＝本卡**）。⚠️ ⛔ **不得由本條推出通則壞掉**：那 20 張有毛病的卡裡 **18 張開於 `amend` 開始寫兩個居所的修復（`06ac31f`，2026-08-12）之前** ⇒ 是舊卡未翻新的歷史殘留，⛔ 不是現行寫入路徑的缺陷。修復後只漏本卡，而漏的原因是**平台硬限制**不是邏輯錯 ⇒ ⛔ 不為本卡開通則卡。⚠️⚠️ **本段先前寫的「`amend` 撞上限時半寫入卻回 `rc=2` 並宣稱未寫入任何狀態，那是 rc 契約說謊」已於 2026-08-27 依查核 R4-01 整條刪除，⛔ 不得再被引用。** 成因：該宣稱**早在 2026-08-26 就被需求方裁定 `issuecomment-5421087840` 逐字推翻過**，而 PM 又寫了一次。裁定的兩點：**(1)** 實際輸出是 `cli.py` 的 `except KNOWN_ERRORS` 出口印的 `[wfcli] 錯誤：GraphQL: Column value must be a valid value for text column`，⛔ 不是「拒收（未寫入任何狀態）」——後者只出現在**驗證階段**的三處拒收；PM 讀的是 **docstring 對 rc=2 的描述**、⛔ 不是實際輸出。**(2)** 半寫入**是記錄在案的刻意取捨**——`amend_cmd.py` 的雙居所欄位區段逐字寫著「這是**取捨不是解法**：雙居所欄位沒有任何順序能同時做到首寫自描述與崩潰不留不一致」。⭐ 該裁定原文已把這件事標為「同一 session 內**第三次**『看起來像缺陷、而註解就寫在旁邊說它是刻意的』」，⇒ 本次是**第四次**。⛔ 這與本卡自己說的「欄位側 rc=2 是**預期**不是缺陷」也直接衝突。⚠️ 另登記一件今日查證的事實：`amend_cmd` 的就地註解承諾「由『欄位值 ≠ body 導出值』直接偵測」，⛔ **該偵測器不存在**（`doctor.py` 無此檢查）。鑑於 18/20 是舊卡、修復後只漏 1 張，其優先序低，⛔ 本條僅登記事實、不主張要做。

## 驗證

- [ ] ⚠️ 本清單同 A，依 29 輪研究輪填實。⭐ **V2 是唯一構造上可能不通過的效力驗收**——其餘多為完整性與不變量。
- [ ] **V1 完整性由 artifact 產生**：交付附一支唯讀腳本的原始輸出，對回填後的全母體逐張跑 `brief.parse_block` 與 `brief.drifted`，列出「仍缺簡介」與「仍漂移」兩份**具名清單**。⛔ 不接受人工聲明「全數完成」。
- [ ] **V2 ⭐ 效力（這條可以紅）**：以「卡 A 的 `## Log` 之前提到卡 B 的卡 ID」建語意相關 ground truth（研究輪實測 234 組），量回填後**簡介本身**抓回的比例。**判準：須顯著高於資源宣告的 15.8% 基準。** 研究輪參考值：既有 11 張人工簡介 25.0%、8 張隨機草稿 23.1%、刻意摘要版 **0.0%**。⛔ 交付時須現場重算基準，⛔ 不得沿用研究輪數字。⭐ **先導批 10 張未過 15.8% 即停手**並回報，⛔ 不得續跑完 189 張。
- [ ] **V3 變異檢驗**：自回填結果隨機抽 10 張，各另寫一份**刻意的摘要版**（兩個標記逐字齊備、⛔ 不指名任何卡外對象），跑同一套驗收。**摘要版須被 A6 擋下、且 V2 覆蓋率須降至 0** ⇒ 否則驗收本身沒有鑑別力。
- [ ] **V4 卡面不變量（真實樣本，⛔ 不自造）**：對每一張回填卡比對前後 body，證明「**所有非空行逐字保留且順序不變**，新增行恰為 `## 簡介` ＋三行哨兵區塊」。研究輪以純函式對 189 張全跑得 189/189 ⇒ 這是可達標的。並逐張確認 `## Log` 與 `## 核心痛點` 各只出現一次。
- [ ] **V5 注入負控**：對**一張真實既有卡**證明 A5 的拒收真的會擋：含 `\n## Log` 的值 rc≠0 且 body 逐位元未變；同時證明正控——不含分行字元的值寫得進去。⛔ 只跑正控是零資訊檢查。
- [ ] **V6 留痕不說謊——⚠️ 本條於 2026-08-26 依查核 R1-02 更正**：⛔ **原文要求「對 `#140` 附回填前後的兩份原始輸出」，而 #140 從未被回填**（見 A3）⇒ 該驗收無對象、構造上不可能執行，留著等於掛一個永遠驗不了的條目。⇒ 改為：**交付須逐字證明 #140 未被觸碰**——附其 Project 簡介欄位值與 body 於回填前後的比對，證明**兩者皆逐位元未變**，且全母體掃描仍把它列為「雙居所漂移 1」。⛔ 不得以「沒動它」一句帶過。
- [ ] **V7 回歸**：`cd cli && uv run pytest -q`（研究輪基線 1174 passed，⛔ 交付時現場重記）、`uv lock --check`、`scripts/replay_escalation_rules.py`、`scripts/canonical_citation_scan.py`、`scripts/contract_tool_reconcile.py --check` 五項全綠，逐項貼 rc。⚠️ ⛔ **不得接管線**（`| tail` 會把 rc 換成 tail 的）。
- [ ] **V8 未驗清單依 §6.4.2**：每項標明驗不了的原因（缺什麼／要等什麼／需要誰）；⛔ 標不出原因者代表驗得了、不得列入。

## Log

- 2026-08-26T02:00:34+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-26T02:04:11+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (研究)；iteration 0；SHA cd17ba5f0bda377a0bcdbf542932e6a977f7c409；證據 派研究輪（子代理，唯讀）。⭐ 本卡驗收刻意留白至研究輪產出——判準由研究產生，⛔ 不由開卡者預先決定。依據：2026-08-26 的實測教訓（aiwf#142 開卡時把尚未複驗的量測結論寫進驗收與身分欄位，被三輪研究連續推翻；aiwf#141 兩輪共被推翻 10 條）。⚠️ 並登記 S4 的查證結果：cpbl 移除相容層在現行設計下**不該做**——roadmap_lines.py:220-221 逐字「保留是刻意的裁斷，不是忘了刪」，canonical 明列廢止值為「向後相容，已寫的卡留著」⇒ 相容層永久保留，#130 切片表的 S4 是切片當時的假設，已被 cpbl#165 的裁定取代。。
- 2026-08-26T02:55:43+08:00 amend by wf-cli（op bde050ed）→ spec 基線：原值指紋 sha256:bda050585a00f0f6cb502350559d75532ae3b244c9498b996e7c5df2d98dfc8d (3 bytes) → 新值指紋 sha256:8a4e84b5efe51a8f44cb5ed47a4f4e34f23bdb12f5600ad6b114f78da35b8699 (40 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 補 Initiative 子卡的 spec 基線＝父卡 WF-STAGE-STATE-TWO-AXIS1 的交付 SHA（開卡時漏填，canonical §5.1.2）。
- 2026-08-26T11:51:51+08:00 amend by wf-cli（op 80329fe3）→ 驗收條件：原值指紋 sha256:a722b8ffa091e6b8c3360a5fb87e8b48d1d53db2f71cc9799ecfe65ec139f815 (387 bytes) → 新值指紋 sha256:abe4373c58c04cc9a8f5c77672156f12068998e7b72bac0b1eb793bf7181293e (4398 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 29 輪研究輪產出填實驗收與驗證（開卡時刻意留白）；A5 以腳本自行拒收分行字元解除對 WF-MARKER-WRITE-BOUNDARY1 的阻塞依賴，A7 登記 WF-CLI-ENSURE-FIELDS-DOUBLE-READ1 為非阻塞加速項，A10 更換價值主張。
- 2026-08-26T11:51:51+08:00 amend by wf-cli（op 80329fe3）→ 驗證：原值指紋 sha256:2f5af99c040d81a6a1b5cc24dd27c170c37bb6143fc1d5784f559f18ad494a8f (53 bytes) → 新值指紋 sha256:9ae42a99c20b4d32bb85845a323d2767563a2c6efacaee77c24c89407e755e30 (2630 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 29 輪研究輪產出填實驗收與驗證（開卡時刻意留白）；A5 以腳本自行拒收分行字元解除對 WF-MARKER-WRITE-BOUNDARY1 的阻塞依賴，A7 登記 WF-CLI-ENSURE-FIELDS-DOUBLE-READ1 為非阻塞加速項，A10 更換價值主張。
- 2026-08-26T12:10:58+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code (執行)；分支worktree ai/opus-5/WF-CARD-BRIEF-BACKFILL1 @ /Users/ruanruan/Dev/ai-workflow/.worktrees/brief-backfill；交付狀態 🔨執行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-26T13:20:09+08:00 amend by wf-cli（op 30f1a974）→ 驗收條件：原值指紋 sha256:ef29a4e1678a7d1bd2de575af35e934933cbc0ebac4bc0da66de48666a4aed6d (4402 bytes) → 新值指紋 sha256:380f30561ee6b42d38396629750805264ef21c53e73819350db4aac3efbf8688 (4887 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 修正 amend 第一行重複的 `- [ ] ` 前綴（CLI 對每個 checklist item 自動加一個，傳入時已自帶 ⇒ 疊加）；並逐字更正 A7 被研究輪推翻的「提高一個數量級」（實測原射程僅 1.91 倍，換原生查詢才降到 1 視窗）。
- 2026-08-26T13:20:09+08:00 amend by wf-cli（op 30f1a974）→ 驗證：原值指紋 sha256:d28042c164d643b6c186e4a6e47cab23d160bf85d258edad19e689f4162b0a59 (2634 bytes) → 新值指紋 sha256:69be52de1eb3d4c8ead22b0486150a92c6c7fa0e444f6a8783d139de3dfb344e (2624 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 修正 amend 第一行重複的 `- [ ] ` 前綴（CLI 對每個 checklist item 自動加一個，傳入時已自帶 ⇒ 疊加）；並逐字更正 A7 被研究輪推翻的「提高一個數量級」（實測原射程僅 1.91 倍，換原生查詢才降到 1 視窗）。
- 2026-08-26T13:26:05+08:00 amend by wf-cli（op b440b7be）→ 驗收條件：原值指紋 sha256:dcf016628548f41669418bd0a7abc5a46c9a9d2d1ddf17fdc76626adf8dace97 (4891 bytes) → 新值指紋 sha256:52cbfc9131445d0f6f55f1605abafdb3494017ab399832046b80f3c7ccf1b345 (6078 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 先導批實跑取代估計：A7 節流改為實測 228 點/張、21 張/hr（原 211/23 過於樂觀）並登記兩筆未解異常；A5 新增位元組上限紅線 1012B 及 amend rc=2 謊稱未寫入的實撞事實。
- 2026-08-26T16:11:18+08:00 amend by wf-cli（op 22f42a72）→ 驗收條件：原值指紋 sha256:743e44b5cbc3cae2b11572ba01890ead2f01e96b52f59c21a852c12ad5539cb5 (6082 bytes) → 新值指紋 sha256:dd7c8e5fe19976238d66018ad35bbc6220c612325c030c740a3a3e64105e172d (7690 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定丁案（issuecomment-5422461485）：A10 價值論證更換為三條現場重算的證據含 2026-08-26 經查證的實害；新增 A11（V2 判定 undecidable 而非沒過）與 A12（序位須等 aiwf#151）。
- 2026-08-26T20:21:06+08:00 amend by wf-cli（op 17026bca）→ spec 基線：原值指紋 sha256:8a4e84b5efe51a8f44cb5ed47a4f4e34f23bdb12f5600ad6b114f78da35b8699 (40 bytes) → 新值指紋 sha256:1f53cd83053cfbb3726cd99b267f1c6b9795d00b5d2e3eb330c44890b0fcc996 (40 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 A12 的阻塞條件已解除：WF-CLI-ENSURE-FIELDS-DOUBLE-READ1（aiwf#151）已於 2026-08-26 合併為 b169c242，ensure_fields 零建立由 204 點降到 3 點（跨家族查核者獨立複驗 4183→4180）⇒ 160 張回填由 9 個額度視窗降到 1 個；spec 基線同步更新。
- 2026-08-26T22:47:59+08:00 amend by wf-cli（op 760e95b3）→ 驗收條件：原值指紋 sha256:e8a8f5a24390b30e788b96988af96a5ffe82711631f8274ddab2d9433bc1eab9 (7694 bytes) → 新值指紋 sha256:8abfea7ceadb4000368a8236aea06b0a6037c2f205b66e9f0602ff76c12421d9 (8662 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定（2026-08-26）：A11 的 V2 由 undecidable 改判為通過——丁案做滿 158 張後實得 187 條 GT-A 邊，解除構造性不可判定；裁決口徑為卡面事前釘死的 GT-A/strict（25.7% vs 16.6%，二項 p=0.0011，McNemar p=0.0300，power 0.897），但 GT-B/strict 13.2% vs 17.8% p=0.99 不顯著必須逐字並存。A10(2) 的 21/203 改判 unreproducible：執行者用四種區段定義各跑一次得 7/8/8/16 無一為 21，該數字由 PM 報出而未隨數字載明判準。順帶收掉本區段首行的三層 - [ ] 前綴。
- 2026-08-26T22:56:56+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (執行)；iteration 1；SHA b169c2424c0401c169104312f2fa807c01345feb；階段 研究；踩坑回應 8 族（已檢查 1／不適用 0／發現 7）；證據 ⚠️ 本筆為 PM 補記的遲到轉移，⛔ 不是新的派工。實際的 研究→執行 轉移發生於 2026-08-26T12:10:58+08:00 的 assign（見上方 Log：分支worktree ai/opus-5/WF-CARD-BRIEF-BACKFILL1 @ .worktrees/brief-backfill、交付狀態 🔨執行中、實際能力層級 主力型），但 assign 刻意不寫 Project 階段欄（handoff_cmd 就地註解逐字記載），使階段欄停在「研究」而交付狀態已是執行中。今日要把卡交出去時被 #148 的踩坑閘門擋下並指出此不一致 ⇒ 先補記本筆，再由執行交付到查核。source-sha 取 assign 當時 worktree 的 HEAD b169c242。。
- 2026-08-26T22:57:30+08:00 handoff by wf-cli → owner 待指派；iteration 1；SHA 80eb34407e870a50736745839167999d52d603bb；階段 執行；踩坑回應 13 族（已檢查 3／不適用 0／發現 10）；證據 158/158 卡面寫入完成（rc 全 0、body 實際變動 158/158、守衛拒收 0、例外 0）；剩 2 張為卡面具名排除（aiwf#15 的 A2、#140 的 A3）。V1 完整性由 artifact 產生：item 總數 204／有簡介 44→202／缺簡介 2（恰為兩張具名排除）／雙居所漂移 1（未新增）／形狀合格 202/202。V4 卡面不變量 158/158 全通過（非空行逐字保留且順序不變、零行被移除、新增行恰為簡介區塊四行、三個標題各恰 1 次、回讀 parse_block 逐字相符）。V5 注入負控：API-INFO-UNRESOLVED-GAMES1 餵含分行字元的值遭拒（0xa），未呼叫 amend，body sha256 1e535827… 前後完全相同、長度 2004→2004；正控 158 張全寫入成功；守衛承重 10/10 個分行字元穿過 amend_brief 且 10/10 都造成第二個 ## Log。V7 回歸逐項 rc=0（pytest 1270 passed／uv lock --check／replay_escalation_rules 114-114／canonical_citation_scan 掃 128 檔命中 0／contract_tool_reconcile --check 59 缺口全有處置），⛔ 未接管線。A6 跨界具名 153/158，loose 與 strict 兩把獨立的尺一致、正則假陽性 0 張；5 張不通過的逐張理由已載明。V3 變異檢驗通過：摘要版 10 張 V2 覆蓋率降至 0.0%、A6 0/10，同 10 張正式版 strict 21.4%／ext 50.0% ⇒ 驗收本身有鑑別力。B 層前兩批零命中已證實為 GT 取材面假象，改以凍結 spec 為來源後抓回 27/55=49.1%。⭐ 成本量測換儀器：REST gh api rate_limit 量不到 GraphQL 額度（同時刻 used=0 與 used=73 並存、序列非單調 5000→4935→5000、可算出 −76 點），改用 GraphQL 自身 rateLimit 欄位後 ensure_fields=3.00 點/2.03 秒、amend --brief 底線 24 點/延遲中位 37.9 秒 ⇒ 綁手腳的是延遲不是額度。執行者自報 6 項失誤、PM 自報 2 項，全部見踩坑報告。腳本 22 檔已 commit 80eb3440 並推 origin/ai/opus-5/WF-CARD-BRIEF-BACKFILL1，worktree 保留於 .worktrees/brief-backfill 供查核者進駐。
 ⚠️ 留痕說明：本卡今日連下兩筆 handoff——前一筆是 PM 補記 assign 未寫階段欄所漏掉的 研究→執行 轉移（⛔ 不是重新派工），本筆才是執行交付到查核。。
- 2026-08-26T23:01:37+08:00 amend by wf-cli（op c0cf80a4）→ 驗收條件：原值指紋 sha256:8a0509423ddac735fe3d02232360ec197bf531a9c9927fe76838473580745ce1 (8714 bytes) → 新值指紋 sha256:9b1f17d82ba8e767aa0476efbd6f6564c26d0def45b02149a20ef28e00469231 (9820 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定（2026-08-26）第三次更正：A7 的 228 點/張、21 張/hr、8.6 小時與 A12 的 241 點/張 皆出自壞儀器——REST gh api rate_limit 量不到 GraphQL 消耗（同時刻 used=0 與 used=73 並存、序列非單調 5000→4935→5000、可算出 -76 點）。改用 GraphQL 自身 rateLimit 欄位後 amend --brief 底線 24 點、延遲中位 37.9 秒 ⇒ 框架更正為綁手腳的是延遲不是額度（額度天花板 208 張/hr、延遲天花板 95 張/hr；158 張實跑 waited_sec 全 0、額度從未見底）。ensure_fields=3 點的結論不受影響（兩種獨立方法證實）。A12 的序位條件已隨 aiwf#151 合併 b169c242 達成並結清。
- 2026-08-26T23:13:19+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (PM)；iteration 2；SHA 80eb34407e870a50736745839167999d52d603bb；階段 審核；踩坑回應 8 族（已檢查 6／不適用 0／發現 2）；證據 PM 自查退回（⛔ 未經查核者）：commit 80eb3440 缺全部三個 provenance trailer，與 aiwf#154 R1-01 同一缺陷。趁 --to 仍為待指派、無查核者進駐時自修。。
- 2026-08-26T23:13:39+08:00 handoff by wf-cli → owner 待指派；iteration 2；SHA 292f5303194786faca287e99fcc27503db79a353；階段 執行；踩坑回應 13 族（已檢查 4／不適用 0／發現 9）；證據 158/158 卡面寫入完成（rc 全 0、body 實際變動 158/158、守衛拒收 0、例外 0）；剩 2 張為卡面具名排除（aiwf#15 的 A2、#140 的 A3）。V1 完整性由 artifact 產生：item 總數 204／有簡介 44→202／缺簡介 2（恰為兩張具名排除）／雙居所漂移 1（未新增）／形狀合格 202/202。V4 卡面不變量 158/158 全通過（非空行逐字保留且順序不變、零行被移除、新增行恰為簡介區塊四行、三個標題各恰 1 次、回讀 parse_block 逐字相符）。V5 注入負控：API-INFO-UNRESOLVED-GAMES1 餵含分行字元的值遭拒（0xa），未呼叫 amend，body sha256 1e535827… 前後完全相同、長度 2004→2004；正控 158 張全寫入成功；守衛承重 10/10 個分行字元穿過 amend_brief 且 10/10 都造成第二個 ## Log。V7 回歸逐項 rc=0（pytest 1270 passed／uv lock --check／replay_escalation_rules 114-114／canonical_citation_scan 掃 128 檔命中 0／contract_tool_reconcile --check 59 缺口全有處置），⛔ 未接管線。A6 跨界具名 153/158，loose 與 strict 兩把獨立的尺一致、正則假陽性 0 張；5 張不通過的逐張理由已載明。V3 變異檢驗通過：摘要版 10 張 V2 覆蓋率降至 0.0%、A6 0/10，同 10 張正式版 strict 21.4%／ext 50.0% ⇒ 驗收本身有鑑別力。B 層前兩批零命中已證實為 GT 取材面假象，改以凍結 spec 為來源後抓回 27/55=49.1%。⭐ 成本量測換儀器：REST gh api rate_limit 量不到 GraphQL 額度（同時刻 used=0 與 used=73 並存、序列非單調 5000→4935→5000、可算出 −76 點），改用 GraphQL 自身 rateLimit 欄位後 ensure_fields=3.00 點/2.03 秒、amend --brief 底線 24 點/延遲中位 37.9 秒 ⇒ 綁手腳的是延遲不是額度。執行者自報 6 項失誤、PM 自報 2 項，全部見踩坑報告。腳本 22 檔已 commit 80eb3440 並推 origin/ai/opus-5/WF-CARD-BRIEF-BACKFILL1，worktree 保留於 .worktrees/brief-backfill 供查核者進駐。
 ⚠️ 留痕說明：本卡今日連下兩筆 handoff——前一筆是 PM 補記 assign 未寫階段欄所漏掉的 研究→執行 轉移（⛔ 不是重新派工），本筆才是執行交付到查核。 ⚠️ SHA 更新：原 80eb3440 缺全部三個 provenance trailer，已 amend 為 292f5303 並 force-with-lease 推送；doctor --commit-trailers --require-planned-by 讀內容為「違規 0／合規 1（共 1 筆）」。⛔ 第一次 amend 曾失敗——trailer 區塊與正文間少一空行，git parser 回空而肉眼看得到，已修正並以兩種 git 讀法確認。。
- 2026-08-26T23:36:01+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 codex；core_pain_resolved yes；self_run 13 項；findings 12 項（blocking 8）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-CARD-BRIEF-BACKFILL1-e0-292f5303194786faca287e99fcc27503db79a353。
- 2026-08-26T23:42:46+08:00 amend by wf-cli（op 9a22afa9）→ 驗收條件：原值指紋 sha256:325ceb3ba590c401d0b98a9cb6fe9c4242ee8d42e4911a66bfcabe9953c480fe (9872 bytes) → 新值指紋 sha256:35db119761d701b43c172825b4361b935069680fcdb6ec7d56637d87fe376f88 (11396 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 查核 R1（codex）四項卡面阻擋修正：R1-01 資源宣告由 [] 補為 22 個明確 file: token（canonical AI_WORKFLOW.md:347 明訂重現工具即交付物，且無一次性腳本豁免；因資源比對為精確字串故逐檔列出、不用目錄）；R1-02 A3 與 V6 不再宣稱 #140 要把 Project 值寫回 body——#140 實際被具名排除從未回填，V6 改為證明它未被觸碰；R1-03 A7 的『不得一次跑完』誠實記為違反原驗收，拿不出 supersede 裁定故不編造；R1-04 A10(1) 由 40/248/16.1%/208 更正為 41/247/16.6%/206（同卡 A11 早已用新數字，兩處原本自我不一致）；R1-08 A5 由『11 個字元』更正為『10 個單字元，另測 CRLF 雙字元序列』。
- 2026-08-26T23:42:46+08:00 amend by wf-cli（op 9a22afa9）→ 驗證：原值指紋 sha256:8e016e6f6f03d1f08a86dd381f5c4f612ecb97d25cd2f4b7421871e69609563f (2628 bytes) → 新值指紋 sha256:283c4c5e17c2cef6b6ef5d309b31104d5925b2c2284a6e571db26653e44540a8 (2932 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 查核 R1（codex）四項卡面阻擋修正：R1-01 資源宣告由 [] 補為 22 個明確 file: token（canonical AI_WORKFLOW.md:347 明訂重現工具即交付物，且無一次性腳本豁免；因資源比對為精確字串故逐檔列出、不用目錄）；R1-02 A3 與 V6 不再宣稱 #140 要把 Project 值寫回 body——#140 實際被具名排除從未回填，V6 改為證明它未被觸碰；R1-03 A7 的『不得一次跑完』誠實記為違反原驗收，拿不出 supersede 裁定故不編造；R1-04 A10(1) 由 40/248/16.1%/208 更正為 41/247/16.6%/206（同卡 A11 早已用新數字，兩處原本自我不一致）；R1-08 A5 由『11 個字元』更正為『10 個單字元，另測 CRLF 雙字元序列』。
- 2026-08-26T23:42:46+08:00 amend by wf-cli（op 9a22afa9）→ 資源宣告：原值指紋 sha256:5a1a2d3b0b878f96460dafff131cc779429481f3017ca4b56343b14ff5c84a08 (127 bytes) → 新值指紋 sha256:98da4a4b39d1b5dfaafa22ed5f8fd73517b35183e1d90113facae6d2908406a1 (1037 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 查核 R1（codex）四項卡面阻擋修正：R1-01 資源宣告由 [] 補為 22 個明確 file: token（canonical AI_WORKFLOW.md:347 明訂重現工具即交付物，且無一次性腳本豁免；因資源比對為精確字串故逐檔列出、不用目錄）；R1-02 A3 與 V6 不再宣稱 #140 要把 Project 值寫回 body——#140 實際被具名排除從未回填，V6 改為證明它未被觸碰；R1-03 A7 的『不得一次跑完』誠實記為違反原驗收，拿不出 supersede 裁定故不編造；R1-04 A10(1) 由 40/248/16.1%/208 更正為 41/247/16.6%/206（同卡 A11 早已用新數字，兩處原本自我不一致）；R1-08 A5 由『11 個字元』更正為『10 個單字元，另測 CRLF 雙字元序列』。
- 2026-08-26T23:46:48+08:00 amend by wf-cli（op 2b2cb4d6）→ 驗收條件：原值指紋 sha256:ee320f6e2989c39386836fed51a14492f207df91ddc9239b529e313c14bbadb1 (11448 bytes) → 新值指紋 sha256:8488e59b499ca34bb66f155ddfa498ca019064f5c083bee18d3b45ac8dc2d460 (12740 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方裁定甲案（2026-08-26）：接受資源宣告的顯示側漂移。R1-01 的 22 個 file: token 已在 body（assign 唯一讀取處），Project 欄位因 1037 位元組超過 1012 上限而寫不進去，超出 25。新增 A13 記載該裁定與其界線：⛔ 不得推出雙居所漂移無害（此處無害只因該欄位無機器消費者，#140 那種方向相反仍是缺陷）；並登記 amend 半寫入卻謊稱未寫入的形態為另一張卡的射程。
- 2026-08-27T00:03:54+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (執行)；iteration 3；SHA 292f5303194786faca287e99fcc27503db79a353；階段 審核；踩坑回應 8 族（已檢查 2／不適用 0／發現 6）；證據 R1（codex）REQUEST_CHANGES，core_pain_resolved=true、⛔ 不需回滾。八項阻擋中六項為卡面修正已由 PM 完成（R1-01/02/03/04/07/08），交回執行者的是兩支腳本：R1-05 verify_invariants.py:86 缺 before/after 直接跳過卻仍輸出「全數通過」、且 ok 未納入 ## 核心痛點 == 1；R1-06 snapshot_population.py:22 仍用已證實失真的 REST endpoint 卻把差值命名為 graphql_cost，查核者重跑時錯報 0。另附一項本輪新發現、不在 R1 內：PM 的 commit 292f5303 把 Implemented-by 填成「Claude Opus 5@Claude Code (執行)」，而 origin/main 全史該形態出現 0 次、主流值是裸的「Claude Opus 5@Claude Code」（117 次）⇒ 用了不存在的慣例，一併修。R1-09 非阻擋（24 點 ledger 未版控）本輪不處置。。
- 2026-08-27T00:04:19+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code (執行)；分支worktree ai/opus-5/WF-CARD-BRIEF-BACKFILL1 @ /Users/ruanruan/Dev/ai-workflow/.worktrees/brief-backfill；交付狀態 🔨執行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-27T00:55:32+08:00 handoff by wf-cli → owner codex；iteration 3；SHA 75c7f6191d27ca43fa6da10b3cfb14dd497a37fb；階段 執行；踩坑回應 13 族（已檢查 4／不適用 0／發現 9）；證據 R2 交付，R1 兩則阻塞 finding（R1-05／R1-06）逐項閉環，執行者複驗後前提皆成立、⛔ 無需反駁。另六項卡面阻擋（R1-01/02/03/04/07/08）已由 PM 於本卡前一輪修完，⛔ 不在本次分支改動內。R1-05：verify_invariants.py 的兩個洞各給一個只穿透該洞的負控——洞1（缺檔跳過）舊版 rc=0 印「V4 總判定：全數通過」PASS=157，新版 rc=1 該卡判 FAIL 並印「⛔ 缺檔，無法比對（⇒ 本卡不變量未經證明）」；洞2（## 核心痛點 只印不判）在 before/after 同位置各注入第二個標題，舊版該卡照印 PASS 而報表上寫著「出現次數: 2」，新版 FAIL、rc=1。正控無退化 rc=0、PASS=158、「全數通過（已驗 158/158 張）」。R1-06：snapshot_population.py 改走 quota.py 的 GraphQL rateLimit，成本改用 used 差值而非 remaining（remaining 跨 reset 會回跳成負成本），量測前後各跑控制組並寫入快照 quota_control_ok 與 quota_source。兩把尺並排量同一次 list_items：舊 REST remaining 5000→5000 ⇒ 錯報 cost 0；新 GraphQL used 263→270 ⇒ cost 7，⭐ 現場重現了查核者的觀察。⭐ CI 有真證據：push run 32989267020 於 16:35:43Z→16:36:42Z 完成，1 個 job、10 個步驟全 success，pytest 與 escalation replay 皆實跑。⚠️ 但 pull_request run 不存在——本分支目前沒有 PR，且 GitHub Actions 自 2026-08-26T15:11:58Z 起為 major_outage（githubstatus 事件『Incident with Actions』，Critical）⇒ ⛔ 合併結果那棵樹未受測。回歸逐項 rc=0：pytest 1270／uv lock --check／replay 114-114／citation scan 掃 150 檔命中 0／contract reconcile 59-59，⛔ 全程導檔再讀未接管線。全母體五個數字未變：204／202／2（具名 aiwf#15 與 #140）／漂移 1（#140）／形狀 202-202。PM 已獨立重跑 SHA 與 trailer（含「執行」0 筆）並逐行讀過 verify_invariants 的 diff；⛔ 但 R1-05 負控無法重現，因其 before/after 工作資料未進版控。執行者自報 5 項失誤、5 項未驗清單，全在踩坑報告內。。
- 2026-08-27T02:46:35+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 codex；core_pain_resolved yes；self_run 17 項；findings 6 項（blocking 3）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-CARD-BRIEF-BACKFILL1-e0-75c7f6191d27ca43fa6da10b3cfb14dd497a37fb。
- 2026-08-27T02:47:31+08:00 amend by wf-cli（op 85a76ff7）→ 驗收條件：原值指紋 sha256:6159f4377466917328dabe255eaa9a62c031bf6a5337211d4cc4f1e05d93365f (12796 bytes) → 新值指紋 sha256:b21248d86a39358585f999b108761a4a74d7364552e617f45099448c76ec5802 (13015 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 查核 R2-02：A13 的裁定理由「該 Project 欄位沒有機器消費者」為假——snapshot.py 讀它（resource_summary），且 Markdown Ledger 以 res_summary = r.resource_summary or (…) 優先渲染欄位 ⇒ 快照與 Ledger 會把宣告 22 個檔的本卡錯報成「無共享可寫資源」。已依 R2-02 指定措辭改寫，並標明 ⛔ 在需求方於正確前提上重新確認之前 R1-01 不算閉環。安全面的機械目的仍成立（assign 只讀 body）。
- 2026-08-27T02:58:53+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code (執行)；iteration 4；SHA 75c7f6191d27ca43fa6da10b3cfb14dd497a37fb；階段 審核；踩坑回應 8 族（已檢查 1／不適用 0／發現 7）；證據 R2 裁決 REQUEST_CHANGES，core_pain_resolved=yes、service_goal_still_served=yes。R1-02/03/04/05/07/08 已閉環。交回執行者的只有 R1-06：snapshot_population.py 的 used 差值仍會跨 reset 說謊，須一併保存比對 resetAt、跨視窗或 after_used < before_used 時判成本不可用、若無法從各 GraphQL 回應累加實際 cost 則欄位改稱帳號層觀測差值、並把 reset 反例納入版控測試。R1-01 的另一半是卡面事，PM 已改寫 A13 並待需求方重新確認。R2-05（CI 須補 PR merge-result run）是外部 gate，⛔ 不計為 escalation finding，由 PM 處理。。
- 2026-08-27T02:59:18+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code (執行)；分支worktree ai/opus-5/WF-CARD-BRIEF-BACKFILL1 @ /Users/ruanruan/Dev/ai-workflow/.worktrees/brief-backfill；交付狀態 🔨執行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（呼叫端以 --worktree-source-repo 明示 ruan6047/ai-workflow；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-27T03:23:59+08:00 amend by wf-cli（op fdd746c0）→ 驗收條件：原值指紋 sha256:5403291f6d865fc943d07d338f31e86591eee64d621f2d469af79779a0359198 (13071 bytes) → 新值指紋 sha256:48c0ac67bbec5efe03c9b8b8cbce40baa363c46f7840c0d479615e9fd66885be (13776 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 需求方 2026-08-27 在更正後的前提上重新確認甲案（查核 R2-02 要求）。A13 改用 codex 指定措辭，並補上研究結果：本卡是全母體 204 張裡唯一一張『欄位主動宣稱無資源而 body 有』的卡；20 張有毛病的卡裡 18 張開於 amend 雙居所修復 06ac31f（2026-08-12）之前 ⇒ 舊卡未翻新的歷史殘留、⛔ 通則沒壞、⛔ 不開通則卡。另登記兩件事實：amend 撞欄位上限時半寫入卻謊稱未寫入屬另一卡射程；amend_cmd 就地註解承諾的漂移偵測器不存在但優先序低。
- 2026-08-27T03:29:37+08:00 handoff by wf-cli → owner codex；iteration 4；SHA 99bf7d23d3c662da4332ab3538bc4adef68526f3；階段 執行；踩坑回應 13 族（已檢查 3／不適用 0／發現 10）；證據 R3 交付：R1-06 閉環。⭐ 走的是主路徑不是改名——實測證實 GraphQL 的 rateLimit 可注入任何 query 最外層 selection set，回應自報的 cost 就是該次請求的實際計費：5 頁各 cost=1、sum=5，而帳號層 used 差值也是 5（67→69 為 gh project view 的 2 點，69→74 為 list_items），兩者完全相符 ⇒ 歸因問題一併解決、與視窗及其他消費者無關。且注入 rateLimit 本身不加價（GraphQL 最低計費 1，5 頁不可能低於 5 而帳號只動 5 ⇒ 加價只能是 0）。新增 _CostAccountingRunner 包在腳本側（⛔ 未動 wf_cli/gh.py，那支被 1270 個測試釘著），欄位改為 graphql_cost_attributed；舊的 graphql_cost 移除，帳號層那把尺改名 account_used_delta 並標明是帳號層觀測。⭐ 跨視窗判準：新增純函式 quota.account_delta，三段順序固定（缺 resetAt → 不可用／resetAt 不同 → 不可用【主判準】／同視窗但 used 倒退 → 不可用）。⭐ resetAt 是主判準而非倒退檢查的理由：跨視窗除了生出 4990→7 ⇒ −4983 這種一眼荒謬的負值，也會生出 10→50 ⇒ +40 這種非負、單調、量級完全合理的假差值——沒有任何算術性質抓得到它，只有 resetAt 抓得到。fail-closed 行為：account_used_delta 回 null（⛔ 不是 0、不是 abs、不是補值），cross_check 不通過，rc=3，快照檔仍完整寫出。負控（同一 driver、同一注入序列、全程不連網）：舊版 rc=0 印 graphql_cost=-4983 且 quota_control_ok=true；新版 rc=3、attributed=5、account_used_delta=null、account_delta_usable=false。正控（真連網真 Project #4）：attributed=5、account_used_delta=7、同視窗、對帳通過、rc=0、204 items。回歸逐項 rc=0：pytest 1289 passed（基線 1270+19）、uv lock --check、replay 114/114、citation scan 151 檔命中 0、reconcile 59/59，⛔ 全程導檔再讀。全母體五數未變：204／202／2（具名 aiwf#15、#140）／漂移 1（#140）／形狀 202-202。⭐ CI 在本 SHA 綠：push run 已 completed/success。PM 已獨立重跑 SHA/trailer/CI/pytest/收集數/citation scan 差值成因六項，逐格相同。執行者自報 4 項失誤、7 項未驗清單，全在踩坑報告內。。
- 2026-08-27T03:59:30+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 codex；core_pain_resolved yes；self_run 12 項；findings 5 項（blocking 3）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-CARD-BRIEF-BACKFILL1-e0-99bf7d23d3c662da4332ab3538bc4adef68526f3。
- 2026-08-27T04:00:31+08:00 amend by wf-cli（op 57cf2464）→ 驗收條件：原值指紋 sha256:5ea5e577ee18ba1c49b3608b5726ecd75ae83ea6d54e36f741624e36545f1cc7 (13832 bytes) → 新值指紋 sha256:f480279972f8c1a0a5b72fdd98767f1ba31cbce911229bb36ac885c49e09e638 (13954 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 查核 R3-01：補第 23 個 file:cli/tests/test_brief_backfill_quota.py（canonical AI_WORKFLOW.md:347 明定重現工具屬交付物必須列入資源宣告），並把 A13 的 22/993 字元/1037 位元組/超出 25 同步更正為 23/1037 字元/1083 位元組/超出 71（三個數字皆 PM 自算與查核者逐格相符）。⚠️ 依 R3-01 指定：只補 body，Project 欄位維持 A13 已接受的顯示側漂移 ⇒ 本次 amend 對欄位那一半必然失敗（1083 > 1012），那是預期行為不是缺陷。
- 2026-08-27T04:00:31+08:00 amend by wf-cli（op 57cf2464）→ 資源宣告：原值指紋 sha256:5fef9511ec8aa77e46ece71e1309f885a1bc19850ae5bc5663686a7fa4ce137e (1173 bytes) → 新值指紋 sha256:7ffb675d309166035e0bf584d5a128e01c1117bc2379391aff773b415cd7c565 (1083 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 查核 R3-01：補第 23 個 file:cli/tests/test_brief_backfill_quota.py（canonical AI_WORKFLOW.md:347 明定重現工具屬交付物必須列入資源宣告），並把 A13 的 22/993 字元/1037 位元組/超出 25 同步更正為 23/1037 字元/1083 位元組/超出 71（三個數字皆 PM 自算與查核者逐格相符）。⚠️ 依 R3-01 指定：只補 body，Project 欄位維持 A13 已接受的顯示側漂移 ⇒ 本次 amend 對欄位那一半必然失敗（1083 > 1012），那是預期行為不是缺陷。
- 2026-08-27T04:13:30+08:00 handoff by wf-cli → owner codex；iteration 4；SHA 99bf7d23d3c662da4332ab3538bc4adef68526f3；階段 審核；踩坑回應 8 族（已檢查 0／不適用 0／發現 8）；證據 R3 的三項阻擋全部處置完畢，⛔ 分支一行未動（SHA 仍 99bf7d23），本輪修正全在卡面、留言與 PR。R3-01：body 資源宣告 22→23 條，補上 file:cli/tests/test_brief_backfill_quota.py（canonical AI_WORKFLOW.md:347），回讀確認第 23 條在位；A13 數字同步更正為 23 條／1037 字元／1083 位元組／超出 1012 上限 71（PM 自算：git ls-tree + 新測試檔 = 23 條，join 後 len=1037、len(encode())=1083、1083-1012=71，與查核者逐格相符）。⚠️ 依 R3-01 指定只補 body ⇒ amend 對欄位那一半必然 rc=2，那是預期不是缺陷。R3-02：更正留言 issuecomment-5430500570 已發，逐字更正 citation scan 150→151（附 git ls-tree 150／git ls-files 151／diff --diff-filter=A 只列出新增測試檔一筆的三行證據）與「實測固定 2 點」→「兩次觀察均為 2 點，非固定值保證」，並登記 live 前控制組失敗使 +7 不可拆。R2-05：⭐ PR #158 已開，必要 context tests = SUCCESS ⇒ 合併結果樹首次受測。⚠️ gate=BEHIND，合併前仍須 rebase 重跑 CI，但該 gate 的解除條件（有 PR 且 merge-ref 跑過 tests）已達成。。
- 2026-08-27T04:23:38+08:00 amend by wf-cli（op c25c568b）→ 驗收條件：原值指紋 sha256:106f2b33f483a67af76d50a69912095c199caf248d55b43db4dfeea9e17eea88 (14010 bytes) → 新值指紋 sha256:4fa16dda48e02f15ceab066e50e319fc3cbc633bd86a246a324b13e10f3680c7 (14908 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 查核 R4-01 兩處：(1) A13 後段殘留的「body 的 22 條」改為 23（前段已改而後段沒改，同段自我矛盾）；(2) ⛔ 整條刪除「amend 撞上限半寫入卻 rc=2 謊稱未寫入、是 rc 契約說謊」的宣稱——該宣稱早在 2026-08-26 就被需求方裁定 issuecomment-5421087840 逐字推翻（實際輸出是 GraphQL error 非「未寫入任何狀態」，PM 讀的是 docstring 不是實際輸出；半寫入是 amend_cmd 逐字記錄在案的刻意取捨），而 PM 又寫了一次。該裁定原文已把此形態標為同一 session 內第三次，本次是第四次。
- 2026-08-27T09:44:09+08:00 handoff by wf-cli → owner codex；iteration 4；SHA 6e8beca4aa208952b7456987fbe2c42b7966c2e5；階段 審核；踩坑回應 8 族（已檢查 3／不適用 0／發現 5）；證據 ⚠️ 本筆為 rebase 後的 SHA 重指，⛔ 不是新交付。原 SHA 99bf7d23 已被 force-push 取代為 6e8beca4aa208952b7456987fbe2c42b7966c2e5。⭐ 內容零變動已證：3 筆 git patch-id --stable 與 rebase 前逐筆相同（1df277ccbe38dfb2d3bec0f3f05182a0b8ebe0de／0696ff5907f1842463b0a7d6fd478044f6c8dee2／d581d46484740a03708384431bbc23d69dad74d1），三筆 trailer 全數保留且 Implemented-by 含「執行」0 筆。rebase 理由：分支落後 main 14 筆（#154 已於 a46af717 合併進 main），而 ruleset main must be green 為 strict=true 要求分支與 base 同步，否則合併被擋。採本機 rebase 而非 gh pr update-branch，理由同 #154：後者會當場產生一筆無 trailer 的 merge commit。rebase 後：PR #158 gate=CLEAN、必要 context tests=SUCCESS、tests (branch head)=SUCCESS；本機 pytest 1309 passed rc=0。R4 的兩項阻擋已處置完畢——A13 的 22→23 與整條刪除被需求方裁定推翻的「rc 契約說謊」宣稱見 op c25c568b；R3-02 指錯 commit 的更正見 issuecomment-5430683267（75c7f619 的 150 當時正確，真正錯的是 99bf7d23 的 commit message）。⛔ R4 裁決維持以留言記錄（issuecomment-5433189170），不補寫成裁決事件——codex 審的是 99bf7d23，替它宣稱審過 6e8beca 是留痕失真。。
- 2026-08-27T10:15:06+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex；core_pain_resolved yes；self_run 10 項；findings 0 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-CARD-BRIEF-BACKFILL1-e0-6e8beca4aa208952b7456987fbe2c42b7966c2e5。
- 2026-08-27T10:28:31+08:00 handoff by wf-cli → owner —（已合併）；iteration 4；SHA 6e8beca4aa208952b7456987fbe2c42b7966c2e5；階段 審核；踩坑回應 8 族（已檢查 2／不適用 0／發現 6）；證據 PR #158 已於 2026-08-27 以 squash 合併（ROADMAP §3.5「一律 squash」），main commit 764a59ff10bbb073952b4c20ebb830e6a787d7fc。⭐ 依 §3.5 的緩解條款，squash 訊息逐字記下被審 SHA 6e8beca4aa208952b7456987fbe2c42b7966c2e5 與 APPROVE 結論；四個 trailer 經 git interpret-trailers --parse 確認解析得出，含 Reviewed-by: GPT-5@Codex。裁決依據：codex 於 2026-08-27 給 APPROVE（issuecomment-5433504208，attempt_id 綁 6e8beca4），核心痛點已消除、零阻擋 finding；doctor --review-channel 確認 event／Issue Log／Project 狀態三面一致為 recorded。三項判定：(1) Project 欄位的顯示側漂移屬需求方明示接受，assign 讀 body 故安全互斥未破，⛔ 不得泛化成通則；(2) patch-id 三筆逐筆相同、trailer 3/3 合規，新 SHA 已重新正式查核、⛔ 沒有冒充沿用舊 SHA 裁決；(3) 合併前無其他實質缺口，merge ref 61af75a4 實跑 1309 passed、escalation replay 114/114。⚠️ 本卡的主交付（158 張卡面簡介回填）不在這個 squash 裡，早已是生產狀態；分支只承載 23 支腳本與一支測試。⚠️ 首次 release 被 merge_verified_local 擋（證明=diverged）——成因是本機 main 落後 14 筆而守衛比對的是本地 main；ff-only 更新後路徑內容差異為 0，重跑通過。；收尾清理：已清除 worktree；本地分支、遠端分支 依授權保留（未刪除）。


## Comment 5421087840 · 2026-08-26T05:38:07Z

## 裁定：先導批撞到的三件事**不另開卡**，逐字登記於此

需求方裁定甲案。以下是 13 輪查證的結果與歸屬，供後續執行者與查核者引用。

### ⛔ 先更正兩處被推翻的宣稱（PM 與先導批執行者各一）

1. **「`amend` 回 rc=2 卻謊稱未寫入」——⛔ 假。** `cli.py` 的 `except KNOWN_ERRORS as exc: print(f"[wfcli] 錯誤：{exc}"); return 2` 是那條路徑的實際出口，印的是 `[wfcli] 錯誤：GraphQL: Column value must be a valid value for text column`。「拒收（未寫入任何狀態）」只出現在**驗證階段**的三處拒收。⇒ 執行者讀的是 **docstring 對 rc=2 的描述**，⛔ 不是實際輸出。

2. **「半寫入是缺陷」——⛔ 不是，是記錄在案的刻意取捨。** `amend_cmd.py` 的雙居所欄位區段逐字：「代價是失敗模式變成『body 已更新、欄位過期』——但那一種是**可直接偵測**的，且重跑本指令即收斂……**這是取捨不是解法**：雙居所欄位沒有任何順序能同時做到首寫自描述與崩潰不留不一致。」

⭐ 這是同一 session 內第三次「看起來像缺陷、而註解就寫在旁邊說它是刻意的」（前兩次：`illegal_terminal_before_cleanup`、`restore_migration_header` 的空章節）。

### ⚠️ 真的成立的一件：rc=2 過載 —— 而它已被裁定過

`docs/WF_EVENT_IDEMPOTENCY1.md` 逐字：「基線 `7451b72` 的退出碼 `0`–`6` 與 `130` 皆已佔用，且**語意逐指令重疊**——`4` 在 `assign` 是資源宣告衝突、在 `review` 是拒收、在 `handoff` 是狀態守衛、在 `deploy-declare` 是前置狀態不符。腳本要區分『真的失敗』與『已經做過了』，就需要一個**跨動詞語意一致**的碼。」⇒ 裁定保留 `7` 專用於 `already_exists`。

**歸屬**：該檔 §12 的**卡 B**（「§2.1 固定臨界區 … ＋ 退出碼 `7`」）。⛔ 不在本卡射程。

### ⚠️ 曝險範圍：⛔ 不是 `amend` 專屬

實測 6 個動詞有多個寫入點，任一中途拋 `KNOWN_ERRORS` 都會留下部分寫入，而呼叫端只看到 rc=2：

| 動詞 | 寫入點數 | 有無記錄順序取捨 |
|---|---:|---|
| `handoff` | 6 | ⚠️ 部分（提到 `open` 半寫入、聲明「不自己決定寫入順序」） |
| `amend` | 4 | ✅ 有 |
| `assign` | 4 | ⛔ 零 |
| `review` | 3 | ⛔ 零 |
| `checkpoint` | 2 | ⛔ 零 |
| `open` | 2 | ⛔ 零 |

**歸屬**：該檔 §12 的**卡 A′**（逐字「§7.1.2 的寫入順序調整（`handoff`／`assign`／`amend --tier`）」）。⛔ 不在本卡射程。

### ⭐ 為什麼裁定不開卡

痛點今天已被兩件**更便宜的東西**解掉：

1. 本卡 A5 的 **1012 B 紅線**使觸發條件消失（Project v2 TEXT 欄位上限是位元組不是字元，實測界線 ∈ [1012, 1024]）。
2. `WF-CLI-ENSURE-FIELDS-DOUBLE-READ1`（`aiwf#151`，已裁定擴射程改用原生 GraphQL 查詢）使額度壓力消失。

⇒ 為一個已被繞過的失敗模式開實作卡，是為不會再發生的事投資。

### ⚠️ 唯一仍裸露的一項，登記在此

**`doctor` 的簡介雙居所漂移偵測掛在 `--legacy-authority-notes` 這個名稱完全無關的旗標下、預設不跑**（實查：`brief_values` 只在 `if args.legacy_authority_notes:` 內填充）。⇒ 先導批那三張半寫入停留約 35 分鐘期間，**沒有任何預設路徑會報它**。

⛔ 無主題歸屬：`doctor.py` 由 `WF-MARKER-SCOPE-CLEARANCE1`（`aiwf#30`，📥Backlog）持有，但該卡的**主題**是 marker 隔離的讀取端誤判，⛔ 不是簡介漂移。且 `WF-POSTHOC-CONFORMANCE1`（`aiwf#138`）正在查核中，⛔ 不宜擴其射程。

---
本帖由 PM（Claude Opus 5@Claude Code）以需求方的 token 發文；裁定內容轉錄自需求方在 2026-08-26 session 對甲乙兩案的逐字回覆「ＯＫ」（甲＝不開卡、登記於卡面）。

## Comment 5421475527 · 2026-08-26T06:27:59Z

## 第二批（20 張純隨機）結果：**V2 第二道閘門沒過，已依裁定停手**

`GT-A／strict`（卡面逐字定義，即裁決判準）：**3/10 = 30.0%** vs 現場重算基準 **40/242 = 16.5%**，單尾二項 **p = 0.2209**、McNemar 配對 **p = 0.5000** ⇒ 皆不顯著。⛔ 未續跑第三批。

種子 `random.Random(202608262)` 抽樣前宣告於 `select_batch2.py`；池＝缺簡介 180 −`aiwf#15` −`#140` ＝ **178 張**。**20/20 rc=0、零半寫入、雙居所漂移 0/20**（全母體漂移仍為 1，即具名排除的 `#140`）。

## ⭐ 最重要的結論不是「簡介沒用」，是**這個閘門在可行樣本量下問不出答案**

- 20 張隨機卡只帶 **10 條** GT-A 邊（**12/20 張出邊為 0**）。n=10 時要 **≥5 個命中（50%）** 才達 α=0.05。
- 若簡介真實命中率就是研究輪估計的 23.1%，**本設計的 power = 0.058** ⇒ 即使簡介真的優於基準，**有 94% 機率抓不到**。
- 要對「30% vs 16.5%」達 80% power 需 **≈70 條邊 ≈ 140 張卡**，而池只剩 178 張。
- ⇒ ⭐ **這個閘門只有在工作做完之後才可能有結論，構造上無法用來決定要不要做。**

**GT 本身另有兩處污染**：池裡 **55 張（30.9%）出邊為 0**（對它們 V2 恆為 0/0，既不支持也不推翻）；全池 197 條邊中 **37 條（18.8%）指向遷移樣板 `OPS-STATE-PLANE-MIG1`**，量的是遷移出處不是語意相關。

## ⭐ 執行者三次拒絕了會讓數字變好看的做法

1. **⛔ 沒有換種子重抽。** 本批抽到「邊稀疏」的離群樣本（同池重抽 20,000 次中位是 22 條邊，抽到 ≤10 的機率 **0.0009**；換種子 1–10 得 16–28 條）。已逐項排除實作缺陷 ⇒ 是運氣不是 bug。逐字：「抽完才因為數字不好看換種子就是看著答案調判準」——並把該紀律就地寫進 `SEED` 的註解。
2. **⛔ 沒有引用唯一會過的那把尺。** 四種判準組合中只有 `GT-B／ext` p=0.0423 顯著，而 GT-B 是本輪追加的定義（卡面沒有）、ext 是放寬的命中判準，**兩者都朝對簡介有利的方向鬆綁** ⇒ 「只報它就是挑了會過的那把尺」。陷阱已就地寫進 `measure_b2.py` 的 docstring。
3. **⛔ 沒有為了通過 A6 而塞一個卡面沒有的關係。** 3 張不通過的卡，其非射程都是「不動的面」而卡面本身未指名任何卡外對象。並登記**檢測器缺口**：`a6_named_targets` 的 pattern 沒有**表名**（而 A6 條文明列表名算數），且 `ai-workflow#12` 這種寫法被 issue 號的 negative lookbehind 吃掉 ⇒ **17/20 是下界**。

## 與先導批的對照（用同一支已修循環量測的 GT builder）

| | 邊/卡 | 零出邊卡 | 覆蓋率 | p |
|---|---:|---:|---:|---:|
| 先導批（分層構造）10 張 | 2.10 | **0/10** | 12/21 ＝ **57.1%** | <0.0001 ✅ |
| 第二批（純隨機）20 張 | 0.50 | 12/20 | 3/10 ＝ **30.0%** | 0.2209 ❌ |
| 缺簡介池 178 張（母體） | 1.11 | 55/178（30.9%） | — | — |

⭐ **先導批的分母本身就是挑過的**：邊密度是隨機池的 **1.9 倍**，且 0/10 張零出邊（池率 30.9% ⇒ 機率 0.024）。⇒ 57.1% 不可外推，需求方改純隨機的裁定是對的。

⭐ 本批 CI **[10.8%, 60.3%]** 同時涵蓋研究輪估計的 23.1% 與基準 16.5% ⇒ **既不能推翻該估計、也不能宣稱簡介優於基準**。

## 其餘驗證

- **V3**：摘要版被 A6 擋下 **10/10**、V2 覆蓋率降至 **0.0%**（GT-A 0/6、GT-B 0/16）✅。⚠️ 誠實界線：V2 那半只有 6 條邊、正式版也只有 1 個命中 ⇒ **鑑別力主要來自 A6 那一半**。
- **V4 卡面不變量 20/20 全過**（最長共同子序列比對）：非空行逐字保留且順序不變、移除行 `[]`、其他非預期新增行 `[]`、`## Log`／`## 核心痛點`／`## 簡介` 各 1 次、回讀 `parse_block` 逐字相符。
- **V5**：負控（`\n## Log` 被守衛在呼叫前拒收、before/after sha256 相同）＋正控（同卡正式回填 rc=0）皆跑。承重證明：對真實卡面 `amend_brief` **10/10 個分行字元全部穿過**。
- **V1**：203 items／有簡介 **43**／缺簡介 **160**／漂移 1／形狀 43/43 合格。

## ⚠️ 額度異常重現了

總耗 **4,819 點**／20 張，均 **240.9 點/張**（⛔ 非 228），等待 **1,562 秒**。⭐ **`ML-FIELD-OF1` 耗 455 點（≈2×）** ——先導批 2/10、本批 1/20 ⇒ **不是一次性事故，是偶發性倍增，發生率約 5–20%**，⛔ 仍無法解釋。⇒ 規劃額度時 228 是樂觀值。

## ⚠️ 執行者自陳的五件（節選）

1. **power 腳本印出手打的錯誤門檻**（「n=10 最少要 4 個命中」，實為 5）——同一份輸出上方的表格自己就寫著 k=4 → p=0.0679。成因是那行結論是**手打常數**、⛔ 不是由迴圈導出。自己讀輸出時抓到。
2. **草擬時寫出與卡面驗收矛盾的非射程**：`INGEST-PA-DAILY1-FIX1` 初稿把「本機 D published>completed 的 5 場異常」寫成非射程，而那**正是該卡驗收第 4 條**。寫入前自查抓到。
3. **A6 修訂輪改動 8 則簡介，其中一則改變了 V2 數字**（2/10 → 3/10）。保留修訂前版本並**兩版都量**（20.0% vs 30.0%，皆不顯著）。⚠️ 執行者主張該引用正當，但**明說這是需要查核者判斷的界線**，⛔ 不自證。

---

## ⛔ 四個候選方向，待需求方裁定（執行者⛔ 不代決，PM 亦不代決）

現況：缺簡介 **160 張**（池 158）。成本 ≈241 點/張、21 張/hr ⇒ **約 7.6 小時**。

- **甲｜停。** 效力在可行樣本量下證不出來，而 A10 明文禁止拿「§6.3 要求」當主要論證 ⇒ 缺乏續做依據。
- **乙｜先修量測再談續做。** 開研究卡處理「剔除樣板邊」與「找一個更稠密的語意相關 ground truth」。⭐ 執行者認為這是唯一能讓後續決策有依據的路。
- **丙｜只回填有出邊的 123 張。** 那是簡介唯一可能被驗證到的子集；55 張零出邊卡依 §6.3 遵守率單獨裁定。⚠️ 但後續覆蓋率數字**不可外推到全母體**，須事先講明。
- **丁｜續做到底、明載 V2 判定為 `undecidable`**，改以 A10 的論證（終態卡上 `assign_cmd` 對資源宣告結構性失明、`root_cause_id` 住在 review finding 裡）承擔價值主張。

⚠️ 另需裁定：研究輪逐字要求 **V2／V3 須由查核者自行重跑，⛔ 不接受執行者自評** —— 該輪尚未派。

---
本帖由 PM（Claude Opus 5@Claude Code）以需求方的 token 發文，內容為執行者交付報告的轉錄與 PM 的整理；⛔ 四個方向的裁定與卡的狀態未動，待需求方。

## Comment 5422461485 · 2026-08-26T08:10:20Z

## 裁定：**丁案**——續做到底、V2 明載為 `undecidable`、價值論證更換

⛔ **並撤回 PM 前一輪的「甲（停）」建議。** 那個建議把「V2 證不出效力」讀成「簡介沒有價值」——⭐ 那正是同日寫入 auto-memory 的「零命中 ≠ 失敗」，PM 對自己違反了。第二個錯是**要求「機械消費者」**：簡介的消費者是看板前的人與 agent，⛔ 不是碼；要求碼消費它是類別錯誤，也正是 V2 從一開始就問錯問題的原因。

### V2 的處置：`undecidable`，⛔ 不是「沒過」

第二批已機械證明：20 張隨機卡只帶 10 條 GT 邊、**power = 0.058**；要對「30% vs 16.5%」達 80% power 需 **≈70 條邊 ≈ 140 張卡**，而池只剩 178 張。

⇒ ⭐ **這個閘門構造上無法在決策前給出答案。** 交付須逐字載明 V2 判定為 `undecidable`，⛔ **不得再被任何一方引用為「簡介沒用」的證據**。

### 更換後的價值論證（全部現場重算，⛔ 不引用研究輪定值）

1. **語意相關邊 248 條，資源宣告抓得到 40 條 ＝ 16.1%** ⇒ ⛔ **其餘 208 條（83.9%）今天沒有任何機制找得到**。
2. **21/203 張卡的驗收裡有「劃界／語意重疊／不是子集／序位」條款** ⇒ 那 21 次相關性判斷**全是人工做的**。
3. ⭐ **經查證的實害（2026-08-26，當事人自陳、可複驗）**：PM 在本 session 差點開出**兩張重複卡**——S2（實際已存在 `DEV-ROADMAP-GATE-RESEARCH-STATUS1`）與 S3（已由 `WF-CARD-BRIEF-AND-TWO-AXIS-WRITE1` 做掉）。三個機制**無一攔得住**：

| 機制 | 為什麼沒攔到 |
|---|---|
| 資源宣告 | ⛔ 待開的新卡**還沒有宣告** ⇒ 構造上比不了 |
| `root_cause_id` | ⛔ 兩張既有卡的卡面都沒有（它住在 review finding 裡，開卡時讀不到） |
| 簡介 | ⛔ 兩張都沒有 |

⭐ **實際攔下它的是需求方逐字說「注意是否有重複卡」，然後 PM 人工掃了 S1–S7 七個切片。**

⇒ 這取代 `WF-OPEN-DUPLICATE-DETECT1` 卡面那個**已被查證為不成立**的舊實害（該卡自己於 2026-08-24 的 Log 逐字記載：「卡面唯一的實害引用 `cpbl#125` 與 `aiwf#11` 涵蓋同一問題族，實查兩者毫無關係……該證據無法成立，重啟前須補經查證的實害」）。⭐ **本則即是它要的那個實害。**

### 序位裁定：`WF-CLI-ENSURE-FIELDS-DOUBLE-READ1`（`aiwf#151`）**先做**

剩餘 160 張 × 實測 241 點/張 ⇒ 約 **7.6 小時**額度。而 `aiwf#151` 已裁定擴射程改用原生 GraphQL 查詢（2 點 vs 102 點）⇒ 落地後降到約 **1 小時**。

⇒ ⭐ **那是唯一會改變成本量級的順序**，⛔ 不是可有可無的優化。本卡在 `aiwf#151` 落地前**不派下一批**。

### 已完成部分保留

先導批 10 張 ＋ 第二批 20 張 ＝ **30 張已回填**，⛔ 不回退。全母體現況：有簡介 43／缺簡介 160／雙居所漂移 1（具名排除的 `#140`）。

### ⛔ V2／V3 複驗輪的處置

研究輪逐字要求查核者自行重跑 V2／V3。⚠️ 既然 V2 判定為 `undecidable`，**複驗 V2 是零價值**；**V3（變異檢驗）仍須複驗**——它證明的是「驗收有鑑別力」，那與樣本量無關。⇒ 併入本卡最終交付的查核輪，⛔ 不另派。

---
以上由 PM（Claude Opus 5@Claude Code）以需求方的 token 發文；裁定內容轉錄自需求方在 2026-08-26 session 對「更正後的建議：丁，但把實害換掉」的逐字回覆「ＯＫ」。⛔ 合併與部署不在此授權內。

## Comment 5427560443 · 2026-08-26T15:36:02Z

<!-- wf-review-event:v1 card_id=WF-CARD-BRIEF-BACKFILL1 source_sha=292f5303194786faca287e99fcc27503db79a353 attempt_id=WF-CARD-BRIEF-BACKFILL1-e0-292f5303194786faca287e99fcc27503db79a353 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CARD-BRIEF-BACKFILL1`　attempt_id：`WF-CARD-BRIEF-BACKFILL1-e0-292f5303194786faca287e99fcc27503db79a353`
- 查核者：codex　escalation_epoch：0
- source_sha：`292f5303194786faca287e99fcc27503db79a353`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-26T23:36:01+08:00

### self_run（查核者實跑）

- `HEAD／merge-base 比對`
  - 292f5303…／b169c242…，吻合
- `doctor --commit-trailers`
  - 違規 0／合規 1；三個 trailer 均可被 Git parser 解析
- `Project items 全母體掃描`
  - 204 items；有簡介 44 → 202；缺簡介 2（恰為 aiwf#15、#140）；雙居所漂移 1（aiwf#140）；形狀 202/202
- `第三批卡面不變量`
  - 158/158；原非空行逐字且順序保留、零移除、只新增四行簡介、三標題各一次
- `注入負控`
  - 換行值遭拒；SHA-256 1e535827585b09fdaa47ea832fc500d408bf515b1a0ef3a2b8b85dc5ae126e45；長度 2004→2004
- `守衛承重`
  - 10/10 分行字元穿過 amend_brief，10/10 造成第二個 ## Log
- `uv run pytest -q`
  - 1270 passed
- `uv lock --check`
  - rc 0
- `escalation replay`
  - 114/114
- `canonical citation scan`
  - 0 命中，但實際掃描 150 檔，不是 handoff 的 128
- `contract reconcile`
  - 59/59
- `REST rate_limit 40 次連讀複驗`
  - 再次出現兩組狀態與 5 次非單調反轉，足以證實舊儀器不可用；GraphQL 自身 rateLimit 六次連讀完全一致
- `Issue edit history 旁證 24 點分布`
  - 158 次修改的中位間隔 40 秒、總歷時 104.77 分鐘，與 37.9 秒／105 分鐘相符；不能證明 120/157 次恰為 24 點

### findings（12，其中 blocking 8）

- **WF-CARD-BRIEF-BACKFILL1-R1-01**　severity=major　blocking=true　class=governance　attribution=coordinator　root_cause_id=`resource-claim-omits-delivered-artifacts`
  - evidence：db_scope: none 正確，但 resources: [] 明確不實。Canonical 規定重現工具就是交付物，必須宣告，見 AI_WORKFLOW.md:347。
  - disposition：資源宣告：必須補宣告。應直接修正本卡，宣告 22 支腳本；不要另開後續卡，也不存在「一次性腳本豁免」。目前資源比對為精確字串時，應列出 22 個明確 file:，不能假設目錄宣告會涵蓋子檔。
- **WF-CARD-BRIEF-BACKFILL1-R1-02**　severity=major　blocking=true　class=authoritative-artifact　attribution=coordinator　root_cause_id=`card-text-contradicts-delivered-scope`
  - evidence：#147 的 A3／V6 仍寫 #140「必須把 Project 值寫回 body」，但實際與本次查核口徑都把 #140 排除。
  - disposition：生產總數可接受，卡面文字不誠實。必須修正卡面。
- **WF-CARD-BRIEF-BACKFILL1-R1-03**　severity=major　blocking=true　class=authoritative-artifact　attribution=coordinator　root_cause_id=`acceptance-superseded-without-record`
  - evidence：A7 寫「不得一次跑完」，A12／handoff 卻明載 158 張一次跑完。
  - disposition：必須標明何時、由誰裁定 supersede，或誠實記為違反原驗收。
- **WF-CARD-BRIEF-BACKFILL1-R1-04**　severity=minor　blocking=true　class=authoritative-artifact　attribution=coordinator　root_cause_id=`stale-number-left-beside-updated-one`
  - evidence：A10(1) 尚稱 40/248、208；目前實測是 41/247、206，且同一卡 A11 已使用新數字。
  - disposition：更新 A10(1) 為現場重算值，或標明其量測時點。
- **WF-CARD-BRIEF-BACKFILL1-R1-05**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`verifier-skips-then-reports-all-pass`
  - evidence：verify_invariants.py:86 遇到缺少 before/after 會直接跳過，仍可能輸出「全數通過」；其 ok 也沒有納入 ## 核心痛點 == 1，見 verify_invariants.py:90 判定區。本次資料是靠獨立檢查才確認 158/158。
  - disposition：缺 before/after 須 fail-closed 而非跳過；ok 須納入 ## 核心痛點 == 1。
- **WF-CARD-BRIEF-BACKFILL1-R1-06**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`tool-named-for-a-metric-it-cannot-measure`
  - evidence：snapshot_population.py:22 仍用已證實失真的 REST endpoint，卻把差值命名為 graphql_cost。我重跑時它錯報 0。
  - disposition：改用 GraphQL 自身 rateLimit，或更名並標明它量不到 GraphQL 消耗。
- **WF-CARD-BRIEF-BACKFILL1-R1-07**　severity=minor　blocking=true　class=authoritative-artifact　attribution=coordinator　root_cause_id=`evidence-figure-not-reproducible-at-head`
  - evidence：handoff 的 citation scan「128 檔」與 HEAD 實際不符。
  - disposition：應更正為 HEAD 實際的 150 檔。
- **WF-CARD-BRIEF-BACKFILL1-R1-08**　severity=minor　blocking=true　class=authoritative-artifact　attribution=coordinator　root_cause_id=`character-count-conflates-single-and-multi-char`
  - evidence：A5 現寫 11 個字元。
  - disposition：A5 應寫成「10 個單字元，另測 CRLF 雙字元序列」，不是 11 個字元。
- **WF-CARD-BRIEF-BACKFILL1-R1-09**　severity=minor　blocking=false　class=authoritative-artifact　attribution=executor　root_cause_id=`cost-ledger-not-version-controlled`
  - evidence：24 點分布缺少版控過的原始 ledger，無法獨立重算。edit history 僅能旁證 158 次修改的中位間隔 40 秒、總歷時 104.77 分鐘，與 37.9 秒／105 分鐘相符，不能證明 120/157 次恰為 24 點。
  - disposition：非阻擋。若要讓該分布可獨立重算，須把原始 ledger 納入版控。
- **WF-CARD-BRIEF-BACKFILL1-R1-10**　severity=info　blocking=false　class=governance　attribution=reviewer　root_cause_id=`ruling-a11-primary-endpoint-upheld`
  - evidence：GT-A／strict 是事前指定的唯一主要判準 [primary endpoint]：48/187 = 25.7%，基準 41/247 = 16.6%；binomial p=0.0011；McNemar b=40, c=24, p=0.0300；實測效果量檢定力 0.897。
  - disposition：裁決（非缺陷）：A11 改判「通過」站得住。因此不能事後用 GT-B／strict 改寫主裁決；四組不是多數決。GT-B 的失敗代表結論對 GT 定義敏感，故合格敘述只能是「GT-A／strict 通過」，不能泛化成「簡介全面優於資源宣告」。另，事後檢定力 [post-hoc power] 不是獨立證據，真正支撐裁決的是事前口徑與兩項檢定。
- **WF-CARD-BRIEF-BACKFILL1-R1-11**　severity=info　blocking=false　class=governance　attribution=reviewer　root_cause_id=`ruling-a10-2-unreproducible-upheld`
  - evidence：四種合理區段定義得到 7／8／8／16，204 張全都有 ## 驗收條件。
  - disposition：裁決（非缺陷）：A10(2) 標為 unreproducible 正確。沒有證據可判定原本 21 一定「算錯」。因原詞表／判準未保存，正確分類就是「不可重現」，且 21 不得繼續作為決策證據。
- **WF-CARD-BRIEF-BACKFILL1-R1-12**　severity=info　blocking=false　class=governance　attribution=reviewer　root_cause_id=`ruling-graphql-instrument-trusted`
  - evidence：GraphQL 自身 rateLimit 六次連讀完全一致。反之，REST rate_limit 的 40 次連讀再次出現兩組狀態與 5 次非單調反轉。
  - disposition：裁決（非缺陷）：新 GraphQL 儀器可信；舊異常維持「未證實」。舊 435／447 點因缺歷史 resetAt，標成「與儀器缺陷相符但未證實」已經充分；現在追查也無法恢復當時狀態，不必另開卡硬湊因果。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-CARD-BRIEF-BACKFILL1-e0-292f5303194786faca287e99fcc27503db79a353
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待指派
findings:
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R1-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: governance
    attribution: coordinator
    root_cause_id: resource-claim-omits-delivered-artifacts
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R1-02
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: coordinator
    root_cause_id: card-text-contradicts-delivered-scope
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R1-03
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: coordinator
    root_cause_id: acceptance-superseded-without-record
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R1-04
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: coordinator
    root_cause_id: stale-number-left-beside-updated-one
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R1-05
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: verifier-skips-then-reports-all-pass
    counting_eligible: true
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R1-06
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: tool-named-for-a-metric-it-cannot-measure
    counting_eligible: true
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R1-07
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: coordinator
    root_cause_id: evidence-figure-not-reproducible-at-head
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R1-08
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: coordinator
    root_cause_id: character-count-conflates-single-and-multi-char
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R1-09
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: cost-ledger-not-version-controlled
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R1-10
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: governance
    attribution: reviewer
    root_cause_id: ruling-a11-primary-endpoint-upheld
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R1-11
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: governance
    attribution: reviewer
    root_cause_id: ruling-a10-2-unreproducible-upheld
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R1-12
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: governance
    attribution: reviewer
    root_cause_id: ruling-graphql-instrument-trusted
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5427633039 · 2026-08-26T15:45:17Z

## PM 修正 R1 的四項卡面阻擋 — 完成三項半，一項撞到平台上限

`amend` op 見 Log。以下逐項對帳，含**一項未完全達成**。

### ✅ R1-02（A3／V6）、R1-03（A7）、R1-04（A10(1)）、R1-08（A5）

- **A3**：不再宣稱 #140 要把 Project 值寫回 body。改記「#140 排除於本卡射程之外」，並保留原文對危害的描述（覆蓋會讓 Log 記成「原本沒有」）。
- **V6**：原文要求「對 #140 附回填前後兩份原始輸出」，而 #140 從未被回填 ⇒ 該驗收**無對象、構造上不可能執行**。改為「交付須逐字證明 #140 未被觸碰」。
- **A7**：依 R1-03 給的兩條路，選**誠實記為違反原驗收**。⛔ 拿不出任何一則裁定 supersede「不得一次跑完」，不編造來源。需求方選丁案那則決定針對的是「要不要做完剩下的卡」，⛔ 不是本條的分批要求。
- **A10(1)**：`40/248＝16.1%／208` → `41/247＝16.6%／206`。
- **A5**：「11 個字元」→「**10 個單字元，另測 CRLF 雙字元序列**」。

### ⚠️ R1-01 資源宣告：body 已達成，但 **Project 欄位鏡像撞到平台上限**

22 個明確 `file:` token 已寫進 body 的 `resource-claims` 區塊 ⇒ **機械面已滿足**：`assign` 走 `parse_block(item.body)` 與 `try_parse_block(other.body)`，**兩處都讀 body、⛔ 從不讀 Project 欄位**，故交集檢查看得到全部 22 條。

⛔ **但 Project 欄位那一半寫失敗了**：

```
db_scope=none；file:scripts/brief_backfill/a6_strict.py、…（22 條）
→ 993 字元 / 1037 位元組
GraphQL: Column value must be a valid value for text column
```

Project v2 TEXT 欄位上限實測為 **1012 位元組**（本卡 A5 已記載）⇒ **超出 25 位元組**，欄位最多容得下約 **21** 條。

⇒ ⛔ **R1-01 的處置「列出 22 個明確 `file:`」在顯示側機械上達不到**，差 25 個位元組。codex 不可能知道——我沒告訴它這個上限也管資源欄位。

**現況：本卡自己落入雙居所漂移**（body 22 條、欄位仍是舊值 `db_scope=none；無共享可寫資源`，37 位元組）——正是 A3 在講的那個缺陷。⚠️ 且 `amend` 回 `rc=2` 並宣稱「未寫入任何狀態」，**實際 body 已寫成功**，與 A5 記載的形態完全相同。

⇒ 這需要一次裁定，我不自行決定：**(甲)** 接受顯示側漂移並在卡面記明；**(乙)** 由 `amend` 對超限的欄位值做有標記的截斷（那是改碼，要開卡）；**(丙)** 其他。

### ⚠️ R1-07 更正（我先前寫錯的數字）

handoff evidence 裡的 canonical citation scan「**掃 128 檔**」是錯的，HEAD 實際是 **150 檔**（命中數 0 不變）。該數字出自執行者 V7 報告而我原樣轉錄、⛔ 未自行複驗。Log 不可編輯，以本則為準。

### ⚠️ 另一項我自己的錯（不在 R1 裡）

本卡的 commit `292f5303` 我把 `Implemented-by` 填成 `Claude Opus 5@Claude Code (執行)`。經 `origin/main` 全史統計，`(執行)` 出現 **0 次**，主流值是裸的 `Claude Opus 5@Claude Code`（117 次）⇒ 我用了一個不存在的慣例。這是 aiwf#154 的執行者查出來並修正它自己那六筆的，我這筆尚未修。


## Comment 5429639870 · 2026-08-26T18:46:36Z

<!-- wf-review-event:v1 card_id=WF-CARD-BRIEF-BACKFILL1 source_sha=75c7f6191d27ca43fa6da10b3cfb14dd497a37fb attempt_id=WF-CARD-BRIEF-BACKFILL1-e0-75c7f6191d27ca43fa6da10b3cfb14dd497a37fb -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CARD-BRIEF-BACKFILL1`　attempt_id：`WF-CARD-BRIEF-BACKFILL1-e0-75c7f6191d27ca43fa6da10b3cfb14dd497a37fb`
- 查核者：codex　escalation_epoch：0
- source_sha：`75c7f6191d27ca43fa6da10b3cfb14dd497a37fb`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-27T02:46:35+08:00

### self_run（查核者實跑）

- `全母體重取`
  - 204／202／2／漂移 1／形狀 202/202；缺簡介恰為 aiwf#15、#140，漂移恰為 #140
- `R1-05 洞1 負控（版控舊/新版 + 臨時最小 fixture 對打）`
  - 舊版 rc=0、全數通過；新版 rc=1、FAIL、已驗 0/1
- `R1-05 洞2 負控（before/after 同位置各有第二個核心痛點）`
  - 舊版 rc=0、PASS 且同時報出次數 2；新版 rc=1、FAIL、已驗 1/1
- `R1-05 洞2 射程檢查（只改 after）`
  - 既有「其他非預期新增行」本來就會攔截 ⇒ 收窄正確
- `R1-06 注入 reset 反例（前控制 100→100、主量測 4990→7、後控制 7→7）`
  - rc=0、graphql_cost=-4983、quota_control_ok=true ⇒ 現版仍會說謊
- `R1-06 live 同次量測（兩把尺並排）`
  - REST remaining 4901→5000 錯算 -99；GraphQL used 99→106 觀測差值 7；前後控制皆通過
- `assign 互斥閘門讀取面查證`
  - assign_cmd.py:179 只讀 body ⇒ 機械目的確實達成；Project 欄位仍是 db_scope=none；無共享可寫資源
- `snapshot 讀取面查證`
  - snapshot.py:70 會讀該 Project 欄位，Markdown Ledger 也優先渲染它 ⇒ 快照／Ledger 會錯報「無共享可寫資源」
- `核心痛點標題分布獨立重量`
  - 204 張 = {1: 204}
- `push run 32989267020 檢視`
  - 確為 HEAD 75c7f61 真綠，10 步驟皆成功
- `git merge-tree（分支 vs main 079c9ee）`
  - 雙方路徑零交集、無衝突；但整合樹仍未跑測試
- `uv run pytest -q`
  - 1270 passed
- `uv lock --check`
  - rc=0
- `replay_escalation_rules.py`
  - 114/114
- `canonical_citation_scan.py`
  - 150 檔、0 命中
- `contract_tool_reconcile.py --check`
  - 59/59
- `worktree／branch／HEAD／remote tip 一致性`
  - worktree 乾淨；三者與指定值一致

### findings（6，其中 blocking 3）

- **WF-CARD-BRIEF-BACKFILL1-R2-01**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`cost-metric-not-window-aware`
  - evidence：snapshot_population.py:57 以 after_used - before_used 計成本，並宣稱可避免 remaining 跨重置的負成本；前提錯誤：used 在新視窗同樣會歸零。注入前控制 100→100 通過、主量測 4990→7、後控制 7→7 通過，現版結果仍是 rc=0、graphql_cost=-4983、quota_control_ok=true。此外，前後兩個空控制窗不能證明主量測期間沒有其他消費者。
  - disposition：R1-06 尚未閉環。一併保存、比對 resetAt；不同視窗或 after_used < before_used 時必須判成本不可用。若無法從各 GraphQL 回應累加實際 cost，欄位應改稱帳號層觀測差值，不能宣稱是本腳本成本。把上述 reset 反例納入版控測試。
- **WF-CARD-BRIEF-BACKFILL1-R2-02**　severity=major　blocking=true　class=authoritative-artifact　attribution=coordinator　root_cause_id=`acceptance-rationale-asserts-absent-consumer`
  - evidence：A13 的「沒有機器消費者／此處無害」不成立：snapshot.py:70 會讀該 Project 欄位，Markdown Ledger 也優先渲染它。因此快照／Ledger 會錯報「無共享可寫資源」。確認：body 已有 22 個明確 file:；assign_cmd.py:179 的互斥閘門只讀 body ⇒ 機械目的確實達成；Project 欄位仍是 db_scope=none；無共享可寫資源。
  - disposition：甲案仍可由需求方接受，但須改成：「安全互斥閘門不讀 Project 欄位；snapshot／Ledger 顯示會低估資源，需求方知悉後接受此顯示側漂移。」在此更正並重新確認前，R1-01 不算完全閉環。
- **WF-CARD-BRIEF-BACKFILL1-R2-03**　severity=minor　blocking=false　class=authoritative-artifact　attribution=external　root_cause_id=`stale-narrative-outside-this-cards-diff`
  - evidence：card.py:924 的「61 張中 24 張、39% 無核心痛點」至今仍是過期敘述。獨立重量得到 204 張的核心痛點標題分布 = {1: 204}。
  - disposition：它不在 R2 diff，依 §5.2 僅回報 PM，⛔ 不擴成 R2 finding。
- **WF-CARD-BRIEF-BACKFILL1-R2-04**　severity=info　blocking=false　class=coordination　attribution=coordinator　root_cause_id=`failure-count-overstated-as-independent`
  - evidence：PM 提供的內容按獨立事件其實是四組；只有把第一組拆成「使用舊快照」與「未查證便預擬反駁」才是五項。
  - disposition：⛔ 不得稱為五個獨立根因。執行者自報失誤的內容揭露本身充分：錯誤來源、差點形成的錯誤結論、查證方式與更正結果都有交代。
- **WF-CARD-BRIEF-BACKFILL1-R2-05**　severity=major　blocking=true　class=environment　attribution=external　root_cause_id=`merge-result-tree-untested`
  - evidence：push run 32989267020 確為 HEAD 75c7f61 真綠、10 步驟皆成功。但 workflow 本身明文把 tests (branch head) 定義為參考訊號，只有 PR merge ref 能驗整合樹。main 已前進至 079c9ee；雖然雙方路徑零交集、git merge-tree 無衝突，整合樹仍未跑測試。官方事故確為 Critical／Actions major outage，並於 16:50 UTC 表示仍在清積壓（https://stspg.io/pg14nv9m3095）。
  - disposition：CI 不足以放行，須補 PR 的合併結果 run。官方事故只能解釋缺證，⛔ 不能把未驗改判為已驗。這是外部 verification gate，⛔ 不計為新的 escalation finding。
- **WF-CARD-BRIEF-BACKFILL1-R2-06**　severity=info　blocking=false　class=governance　attribution=reviewer　root_cause_id=`ruling-r1-05-independently-reproducible`
  - evidence：以版控舊／新版及臨時最小 fixture 對打：缺 before/after 舊版 rc=0 全數通過、新版 rc=1 FAIL 已驗 0/1；同位置第二個核心痛點舊版 rc=0 PASS 且報出次數 2、新版 rc=1 FAIL 已驗 1/1。
  - disposition：裁決（非缺陷）：R1-05 負控可重現，⛔ 不因原 158 張工作資料未版控而新增 finding。這是控制流性質，可由最小反例獨立驗證；⛔ 不同於 R1-09 的 120/157 定量主張必須依賴原始 ledger。R1-05 已閉環，兩洞均獨立重現。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-CARD-BRIEF-BACKFILL1-e0-75c7f6191d27ca43fa6da10b3cfb14dd497a37fb
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: codex
findings:
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R2-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: cost-metric-not-window-aware
    counting_eligible: true
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R2-02
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: coordinator
    root_cause_id: acceptance-rationale-asserts-absent-consumer
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R2-03
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: authoritative-artifact
    attribution: external
    root_cause_id: stale-narrative-outside-this-cards-diff
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R2-04
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: coordination
    attribution: coordinator
    root_cause_id: failure-count-overstated-as-independent
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R2-05
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: environment
    attribution: external
    root_cause_id: merge-result-tree-untested
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R2-06
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: governance
    attribution: reviewer
    root_cause_id: ruling-r1-05-independently-reproducible
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5430418756 · 2026-08-26T19:59:32Z

<!-- wf-review-event:v1 card_id=WF-CARD-BRIEF-BACKFILL1 source_sha=99bf7d23d3c662da4332ab3538bc4adef68526f3 attempt_id=WF-CARD-BRIEF-BACKFILL1-e0-99bf7d23d3c662da4332ab3538bc4adef68526f3 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-CARD-BRIEF-BACKFILL1`　attempt_id：`WF-CARD-BRIEF-BACKFILL1-e0-99bf7d23d3c662da4332ab3538bc4adef68526f3`
- 查核者：codex　escalation_epoch：0
- source_sha：`99bf7d23d3c662da4332ab3538bc4adef68526f3`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-27T03:59:30+08:00

### self_run（查核者實跑）

- `聚焦 quota 測試`
  - 19/19
- `pytest --collect-only tests/test_brief_backfill_quota.py`
  - 19 個 node id
- `uv run pytest -q`
  - 1289 passed
- `uv lock --check`
  - 通過
- `escalation replay`
  - 114/114
- `canonical_citation_scan.py`
  - 151 檔／0 命中
- `contract_tool_reconcile.py --check`
  - 59/59
- `全母體完整性`
  - 204／202／2／漂移 1／形狀 202-202
- `push CI run 33004410010 檢視`
  - HEAD 99bf7d2、1289 passed、success
- `live 自量測（真連網）`
  - graphql_cost_attributed=5；5/6 支已注入、1 支未歸因；cost_attribution_complete=false；帳號差值 +7；⚠️ 前控制組剛好失敗（313→314）
- `資源宣告補完後的欄位長度試算`
  - 23 條 = 1037 字元／1083 位元組，超過 1012 上限 71 位元組
- `cross_check 單向不等式與 GitHub 官方 rateLimit 契約比對`
  - 官方明定 rateLimit.cost 是「目前查詢的點數成本」、每次 GraphQL 呼叫最低 1 點 ⇒ 受控實驗中五次呼叫總計恰為 5，支持「注入沒有增加整數點數成本」

### findings（5，其中 blocking 3）

- **WF-CARD-BRIEF-BACKFILL1-R3-01**　severity=major　blocking=true　class=governance　attribution=coordinator　root_cause_id=`resource-claim-omits-delivered-artifacts`
  - evidence：Canonical AI_WORKFLOW.md:347 明定重現工具屬交付物必須列入資源宣告。目前卡面 22 條，缺 file:cli/tests/test_brief_backfill_quota.py。補完後是 23 條、1037 字元／1083 位元組，超過 1012 上限 71 位元組。
  - disposition：R1-01 回歸：只補 body 的第 23 個 file:，Project 欄位維持 A13 已接受的顯示側漂移；A13 的「22／993／1037／超出 25」也要同步改成新數字。
- **WF-CARD-BRIEF-BACKFILL1-R3-02**　severity=minor　blocking=true　class=authoritative-artifact　attribution=coordinator　root_cause_id=`disclosure-without-correction-of-the-record`
  - evidence：commit message 仍寫 citation scan 150；HEAD 可重跑值是 151。另 commit 中寫「實測固定 2 點」。
  - disposition：自報「commit 前新檔未追蹤、git ls-files 根本沒掃到」的揭露本身充分，⛔ 但揭露不等於修正留痕。應仿 R1-07 在 Issue 留一則不可誤讀的更正；同一則也應把「實測固定 2 點」改口為「兩次觀察均為 2 點，非固定值保證」。
- **WF-CARD-BRIEF-BACKFILL1-R2-05**　severity=major　blocking=true　class=environment　attribution=external　root_cause_id=`merge-result-tree-untested`
  - evidence：push CI 只驗 branch head；本卡沒有 PR，因此上輪 R2-05 的「合併結果樹未受測」仍未解除。
  - disposition：⛔ 不是 R3 新 finding，但在既有 gate 未撤銷前仍不能給整體 APPROVE。
- **WF-CARD-BRIEF-BACKFILL1-R3-03**　severity=minor　blocking=false　class=implementation　attribution=executor　root_cause_id=`control-group-failed-so-split-not-derivable`
  - evidence：live 重跑時前控制組剛好失敗（313→314）⇒ 這次的 +7 不能再強拆成 resolve=2、list=5。
  - disposition：⛔ 不傷新版結論，因 attributed 已不依賴控制組。但先前敘述中把 +7 拆成 2+5 的說法，在本次 live 樣本上不成立。
- **WF-CARD-BRIEF-BACKFILL1-R3-04**　severity=info　blocking=false　class=governance　attribution=reviewer　root_cause_id=`ruling-r1-06-implementation-closed`
  - evidence：五項判定：(1) 不完整歸因可接受——snapshot_population.py:166 明確拆成 graphql_cost_attributed、6/5/1 呼叫數及 cost_attribution_complete=false，沒有把 gh project view 猜成固定 2 點塞入成本，足以誠實表達「下界」。(2) 低報抓不到可接受——cross_check() 的單向不等式只是一道一致性檢查，不是 GitHub 內部計費真值；官方契約明定 rateLimit.cost 是「目前查詢的點數成本」故信任合理，若系統性低報屬上游契約違反，現版已明說無法證實。(3) 未觀察真實 reset 仍然足夠——account_delta() 是純判定函式，官方定義 resetAt 為目前視窗重置時點，注入 W1→W2 足以驗證程式遇到該契約輸入時的行為，⛔ 不必等待真實小時邊界；尤其 test_brief_backfill_quota.py:96 的正差反例證明 10→50 無法靠符號、單調性或量級識別。(5) A13 裁定合理——正確理由已改成「安全閘門讀 body；snapshot／Ledger 會低估且需求方接受」，沒有再宣稱無消費者；204 張裡僅本卡屬主動假宣告，且 18/20 問題卡早於雙居所修復。
  - disposition：裁決（非缺陷）：R1-06 的實作已閉環。⭐ resetAt 是主判準、倒退檢查只是第二道網——推理正確。不需另開通則卡；不存在的 drift detector 可維持低優先序登記。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-CARD-BRIEF-BACKFILL1-e0-99bf7d23d3c662da4332ab3538bc4adef68526f3
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: codex
findings:
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R3-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: governance
    attribution: coordinator
    root_cause_id: resource-claim-omits-delivered-artifacts
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R3-02
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: coordinator
    root_cause_id: disclosure-without-correction-of-the-record
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R2-05
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: environment
    attribution: external
    root_cause_id: merge-result-tree-untested
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R3-03
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: implementation
    attribution: executor
    root_cause_id: control-group-failed-so-split-not-derivable
    counting_eligible: false
  - finding_id: WF-CARD-BRIEF-BACKFILL1-R3-04
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: governance
    attribution: reviewer
    root_cause_id: ruling-r1-06-implementation-closed
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5430500570 · 2026-08-26T20:07:04Z

## 更正留痕（查核 R3-02）

⛔ **揭露不等於修正留痕** —— 以下兩處寫在 commit message 裡的敘述今日為假，Log 與 commit 皆不可編輯，**以本則為準**。

### 一、`canonical_citation_scan` 的檔案數：commit 寫 **150**，現行 head 可重跑值是 **151**

commit `75c7f619` 的訊息記「掃 150 檔、命中 0」。⛔ 該次執行是**零資訊的**：`canonical_citation_scan.py` 的射程是 `git ls-files`，而當時新增的 `cli/tests/test_brief_backfill_quota.py` **尚未追蹤** ⇒ 那次執行根本沒看到本輪改動的東西。

現行 head `99bf7d23` 的可重跑值：

```
git ls-tree -r --name-only 75c7f61 | wc -l  →  150
git ls-files（at HEAD）                      →  151
git diff --name-status --diff-filter=A 75c7f61 HEAD  →  A  cli/tests/test_brief_backfill_quota.py
```

⇒ 差值恰為該新增檔一筆。**裁決（命中 0）未變。**

⭐ 一般化的教訓，⛔ 不限本卡：**以 `git ls-files` 為射程的守衛，在 commit 之前跑對新增檔構造上不會失敗。**

### 二、`gh project view` 的成本：commit 寫「實測**固定** 2 點」，應為「**兩次觀察均為 2 點，⛔ 非固定值保證**」

樣本數 **n=2**（一次 `67→69`、一次由正控的 `7−5` 反推）。⇒ ⛔ 那是把樣本數當成保證。`gh` 換版就可能改，本腳本也**不依賴**這個數字（只記筆數 `gh_calls_unattributed`）。

⚠️ 並補一項查核者 live 重跑時發現、本卡先前敘述據以成立的前提在該樣本上不成立：codex 的 live 量測中**前控制組剛好失敗（313→314）** ⇒ 該次的帳號差值 `+7` **不能再強拆成 `resolve=2` ＋ `list=5`**。⛔ 不傷新版結論（`attributed` 已不依賴控制組），但先前把 `+7` 拆成 2+5 的說法，在該樣本上不成立。

---

⚠️ 同時登記本則之外、已於卡面處置的：R3-01 的第 23 個 `file:` 已補進 body 資源宣告，A13 的數字同步更正為 **23 條／1037 字元／1083 位元組／超出 1012 上限 71**（PM 自算與查核者逐格相符）。⛔ Project 欄位那一半如 A13 所述必然失敗，屬需求方已接受的顯示側漂移。


## Comment 5430683267 · 2026-08-26T20:24:24Z

## 更正的更正（查核 R4-02）：我把正確的證據指成了錯誤來源

`issuecomment-5430500570` 寫成「commit **`75c7f619`** 的 150 是零資訊」。⛔ **那個歸屬是錯的。**

機械結果：

| 對象 | 檔數 | 判定 |
|---|---:|---|
| `75c7f619` 的樹 | **150** | ✅ **該數字當時正確** |
| `99bf7d23` 的樹 | **151** | — |
| `99bf7d23` 的 commit message | 寫 **150** | ⛔ **真正錯的是這個** |

⇒ 零資訊的 pre-commit scan 發生於**製作 `99bf7d23` 那次**（新測試檔尚未追蹤），⛔ 不是 `75c7f619`。

**仍然成立、⛔ 不受本次更正影響的**：現行 head 的可重跑值是 **151**、差值恰為新增的 `cli/tests/test_brief_backfill_quota.py` 一筆、裁決（命中 0）未變、以及那條一般化教訓——**以 `git ls-files` 為射程的守衛，在 commit 之前跑對新增檔構造上不會失敗**。

---

## ⛔ 我另一處被推翻的宣稱（查核 R4-01）

A13 先前寫「`amend` 撞欄位上限時**半寫入卻回 `rc=2` 並宣稱未寫入任何狀態**，那是 rc 契約說謊」。

⛔ **該宣稱早在 2026-08-26 就被需求方裁定 `issuecomment-5421087840` 逐字推翻過**，而我又寫了一次。裁定的兩點：

1. **實際輸出是 GraphQL error** —— `cli.py` 的 `except KNOWN_ERRORS` 出口印的是 `[wfcli] 錯誤：GraphQL: Column value must be a valid value for text column`。「拒收（未寫入任何狀態）」只出現在**驗證階段**的三處拒收。⇒ 我讀的是 **docstring 對 rc=2 的描述**，⛔ 不是實際輸出。
2. **半寫入是記錄在案的刻意取捨** —— `amend_cmd.py` 的雙居所欄位區段逐字：「這是**取捨不是解法**：雙居所欄位沒有任何順序能同時做到首寫自描述與崩潰不留不一致。」

⭐ 該裁定原文已把這件事標為「同一 session 內**第三次**『看起來像缺陷、而註解就寫在旁邊說它是刻意的』」⇒ **本次是第四次**。A13 已整條刪除該宣稱（`op c25c568b`），並就地記下這段成因。

---

## ⚠️ 我提的「結構性觀察」被裁定不得寫進卡面，理由我核對過且成立

我先前主張「`amend` 多導致卡面錯誤累積」，並報了「`amend` 16 次」「8 項阻擋中 6 卡面、**0 碼**」。查核者的三點反駁：

1. **口徑混用** —— 「16 次」把 **Log 行數**當成**操作次數**。現值是 18 條 amend Log 行、35 個 Log events、事件中位數 6.5，而**按唯一 op 計算實為 13 次操作**。
2. **「0 碼」是錯的** —— R1 的八項阻擋正確是 **6 卡面 ＋ 2 實作**（R1-05 `verify_invariants.py`、R1-06 `snapshot_population.py`）。⛔ 程式碼不可能是 0。
3. **因果未證** —— 只有單一卡的相關性，且方向可能相反：**錯誤與需求變動多，才造成 `amend` 多**。

⇒ 依裁定，只在此留一則具時點的**風險假說**，⛔ 不寫進卡面：

> **高變動卡較容易殘留跨段落不一致；本卡是觀察樣本，尚未證明 `amend` 次數與錯誤數存在因果關係。**（2026-08-27）


## Comment 5433189170 · 2026-08-27T01:28:10Z

## R4 裁決（逐字轉錄）— ⚠️ 以留言記錄，⛔ 不是裁決事件

**為什麼不走裁決事件**：本輪修正全在卡面、留言與 PR，**分支一行未動 ⇒ 沒有新 SHA**。而 `wfcli review` 對同一個 SHA `99bf7d23` 已有 R3 的 attempt，重複寫會讓 `doctor --review-channel` **永久判 `marker_quarantined`**（`handoff-contract.md` §3.1.5 的保守停機，⛔ 而解除表示法尚未定義）。

需求方於 2026-08-27 裁定：**卡面純修正的輪次不走裁決事件，改以留言記錄**。⛔ 不為此遞增 escalation epoch —— 該帳在本 repo 本就是 `structurally-unavailable`，為留痕好看而動它代價大於收益。

---

### 結論

`review_result: REQUEST_CHANGES`，⛔ 但**只剩卡面／更正留言兩處；程式碼維持通過。R2-05 已實質解除。**

### 閉環狀態

- **R3-01 部分閉環**：資源宣告 live 回讀為 **23 條**，測試檔恰出現一次；摘要為 **1037 字元／1083 位元組／超限 71**，全部正確。
- **R3-02 部分閉環**：「固定 2 點」已正確改成 n=2 觀察；⛔ citation 更正的 SHA 歸屬仍錯。
- **R2-05 已閉環**：PR #158 的合併參照 `498a03b4` 確實是 `99bf7d2` 合進 base `a46af717`，CI 跑出 **1309 passed、114/114**。

### 尚須修正的兩項

**1. A13 仍自我矛盾** — 前段已寫 23 條，後段仍寫「body 的 22 條只在欄位為空時才浮現」，應改為 23。同一段還宣稱半寫入「rc=2 並宣稱未寫入任何狀態，是 rc 契約說謊」，⛔ 但既有需求方裁定 `issuecomment-5421087840` 已明確推翻：實際輸出是 GraphQL error，半寫入是雙居所寫入順序的**刻意取捨**。這也與本輪「預期、不是缺陷」直接衝突，必須同步改掉。

**2. R3-02 更正留言指錯 commit** — `issuecomment-5430500570` 寫成「commit `75c7f619` 的 150 是零資訊」，但機械結果是：`75c7f619` 樹 150 檔（**該數字當時正確**）／`99bf7d23` 樹 151 檔／真正錯的是 `99bf7d23` 的 commit message 仍寫 150／零資訊的 pre-commit scan 發生於製作 `99bf7d23` 時。須再留一則更正，⛔ 不能把正確的 `75c` 證據誤判為錯誤來源。

### 結構性觀察裁決：⛔ 不要把原敘述寫進卡面

三個理由：

- **數字已變**：目前是 18 條 amend Log、35 個 Log events、事件中位數 6.5；⛔ 若按唯一 op 計算，其實是 **13 次** amend 操作。原本「16 次」混用了 Log 行數與操作次數。
- **「8 項阻擋中 6 卡面、0 碼」是錯的**：若指 R1 的八項阻擋，正確是 **6 卡面 ＋ 2 實作**（R1-05、R1-06）；程式碼不可能是 0。
- **因果未證**：目前只有單一卡的相關性，因果方向也可能相反——錯誤與需求變動多，才造成 amend 多。

若要保留，只在留言寫成具時點的風險假說：

> 高變動卡較容易殘留跨段落不一致；本卡是觀察樣本，尚未證明 amend 次數與錯誤數存在因果關係。

### 最終合併 gate

`BEHIND` 仍要求合併前 rebase 並重跑 CI；⭐ **那是新的最終合併 gate，⛔ 不是 R2-05 尚未解除。**

---

⚠️ 上述兩項均已於 2026-08-27 處置完畢：A13 見 `op c25c568b`（22→23 ＋ 整條刪除被推翻的 rc 宣稱），更正的更正見 `issuecomment-5430683267`。


## Comment 5433504208 · 2026-08-27T02:15:07Z

<!-- wf-review-event:v1 card_id=WF-CARD-BRIEF-BACKFILL1 source_sha=6e8beca4aa208952b7456987fbe2c42b7966c2e5 attempt_id=WF-CARD-BRIEF-BACKFILL1-e0-6e8beca4aa208952b7456987fbe2c42b7966c2e5 -->
## 查核裁決：APPROVE

- 卡：`WF-CARD-BRIEF-BACKFILL1`　attempt_id：`WF-CARD-BRIEF-BACKFILL1-e0-6e8beca4aa208952b7456987fbe2c42b7966c2e5`
- 查核者：GPT-5@Codex　escalation_epoch：0
- source_sha：`6e8beca4aa208952b7456987fbe2c42b7966c2e5`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-27T10:15:06+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git merge-base origin/main HEAD; git status --short --branch`
  - HEAD 與 remote tip 均為 6e8beca4aa208952b7456987fbe2c42b7966c2e5；merge-base 為 a46af717233cb3f04ad3d40d06a4934c613d4239；worktree 無未提交變更。
- `逐筆 git show | git patch-id --stable 對照 rebase 前後三筆 commit`
  - d581d46484740a03708384431bbc23d69dad74d1、0696ff5907f1842463b0a7d6fd478044f6c8dee2、1df277ccbe38dfb2d3bec0f3f05182a0b8ebe0de 逐筆相同。
- `wfcli doctor --commit-trailers --require-planned-by`
  - 範圍 a46af717..6e8beca4 共 3 筆：合規 3、違規 0；Requested-by、Planned-by、Implemented-by 均由 git trailer parser 解析。
- `解析 Issue #147 body 的 resource-claims 並與 git diff 檔案集合對帳`
  - db_scope=none；23 個唯一 file token，與 diff 23 檔逐筆相同；測試檔恰一次；摘要 1037 字元、1083 位元組、超限 71。
- `讀取 Project #4 item 的資源宣告欄位與 A13`
  - Project 欄位仍為 db_scope=none；無共享可寫資源；A13 已明載安全閘門讀 body、snapshot 與 Ledger 會低估且需求方接受顯示側漂移，合併可接受。
- `核對 op c25c568b 後 A13 與 issuecomment-5430683267`
  - A13 前後均為 23，舊 rc 契約宣稱已改為被推翻的歷史成因紀錄；更正留言正確區分 75c7f619 樹 150 與 99bf7d23 message 誤寫 150。R4-01、R4-02 均閉環。
- `uv run pytest -q`
  - 1309 passed in 70.74s，exit 0。
- `uv lock --check`
  - Resolved 7 packages，exit 0。
- `檢視 GitHub Actions runs 33030682551 與 33030679592`
  - pull_request tests 與 push tests (branch head) 均 success，head SHA 6e8beca4；PR run 實際 checkout merge ref 61af75a4，pytest 1309 passed，escalation replay 114/114。
- `wfcli doctor --review-channel --source-sha 6e8beca4...`
  - 新 SHA 狀態為 unobservable，無重複 event、無 marker quarantine；本輪可建立新 attempt。

### findings（0，其中 blocking 0）

- （無）

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-CARD-BRIEF-BACKFILL1-e0-6e8beca4aa208952b7456987fbe2c42b7966c2e5
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: codex
findings: []
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5445866488 · 2026-08-27T22:17:09Z

## ⚠️ 更正：A10(3) 的「S3 已做掉」為假

發文者：**PM（Claude Opus 5@Claude Code）**，以需求方 token 發文；author 欄恆為 `ruan6047`，⛔ 不代表由需求方撰寫。⛔ 本則只更正事實，不編輯卡面、不改任何裁決事件。本卡已結案，依 append-only 慣例以留言更正。

### 卡面原文（逐字）

> PM 差點開出兩張重複卡（S2 已存在 `DEV-ROADMAP-GATE-RESEARCH-STATUS1`、**S3 已由 `WF-CARD-BRIEF-AND-TWO-AXIS-WRITE1` 做掉**），而**三個機制無一攔得住**……

### 後半為假

`WF-STAGE-STATE-TWO-AXIS1`（aiwf#130）的切片計畫定義 S3 為「Project #4 **欄位切換**」、依賴 `S1 ＋ S2`。`WF-CARD-BRIEF-AND-TWO-AXIS-WRITE1`（aiwf#134）做掉的是 **S1 的加法半**——建立 `階段`／`簡介` 兩個新欄位並接上寫入端。⛔ **語彙切換至今沒有發生。**

量測（2026-08-28，`ai-workflow` main `54d23e87873e1239a8bff4cbbb2af0c7c5c805fe`；Project #4 GraphQL 欄位查詢）：

- `交付狀態` 的選項**仍是舊 15 值**：`💡需求 / 🔬研究中 / 🧭規劃中 / 📥Backlog / ⏳待執行 / 🔨執行中 / 🚧進行中 / 🔍待查核 / ✅通過 / 📦已合併 / 🏁完成 / ↩退回 / ⏸阻塞 / 🚨已升級 / 🛑已停止`。
- canonical §0.1 的目標語彙（通用 8 ＋ 終態 1 ＋ 部署 1 ＋ 維護 3）**一個都不在欄位上**；維護專屬的「運行中／失效」尤其不存在。
- `aiwf#134` 自己的簡介逐字：「⛔ 非射程：……**不切換現行狀態語彙（須待 S2 cpbl 相容層…）**」。
- `handoff_cmd.py` 寫階段處的就地註解逐字：「**⭐ 純新增：不動交付狀態、不需 cpbl 相容層**」。

### 前半：不精確，但不是假

`DEV-ROADMAP-GATE-RESEARCH-STATUS1` = `cpbl#165`（CLOSED），它修的是 `GATE_BY_STATUS` 缺 `🔬研究中`——那是 S2 形狀的一個**已完成單次實例**，⛔ 不是 S2 未來範圍（維護專屬值）的既存承接。說它「已存在」會讓人以為 S2 這一片有人守著。

### 已實現的後果

PM 於 2026-08-28 向需求方報告 `#130` 後續卡現況時，**據此判定「S3 已落地、關鍵路徑已被違反」——兩句都錯**。真實情況是 S3 危險的那半（語彙變更）尚未發生，所以 S2 沒有被跳過：它守的那件事還沒來。

⇒ ⛔ 本卡的交付與結案不受影響（A10 是流程觀察，非交付物）；此更正僅供後續讀者對帳。承接本句所指問題的新卡：`aiwf#165`（canonical 與 `project.py` 的過期宣稱）。

