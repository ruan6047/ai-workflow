# #111 WF-REVIEW-RECEIPT-CHANNEL1 收據紀律假設查核者能寫 GitHub，而跨家族查核者沒有寫入通道
- state: closed  created: 2026-08-19T04:58:51Z  closed: 2026-08-19T06:39:10Z
- url: https://github.com/ruan6047/ai-workflow/issues/111
- comments: 2

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；三條出路的取捨要跨 canonical、templates 與 doctor 三處判斷，且錯誤方向難察覺（選錯會留下一條沒人能遵守的紀律或一個永遠報綠的檢查）。MODEL_ROUTING 升級條款「跨模組取捨」命中）　查核：待指派（建議 高階型；查核要判的是否定式性質：修法之後「無收據」是否真的不再被報成已查核。這需要獨立構造零收據樣本驗證，不是複核執行者的測試——今日的實例正是 doctor 對零收據回 [recorded] 全綠）
- Initiative：—　spec 基線：ai-workflow 4dd9d325f00050a7c056964ca93e31aeb1bedb86；實證＝2026-08-19 五筆裁決零收據，留痕見各卡「留痕補正：本輪裁決無 wf-review-receipt:v1 收據」
- DB：db_scope=none
- 服務的原始目標：查核者的身分要嘛真的可驗證，要嘛紀律誠實地承認它驗不了——不留一條沒人能遵守的規則和一個看不見它的檢查

## 簡介
<!-- card-brief:begin -->
處置「跨家族查核者沒有 GitHub 寫入通道，收據紀律構造上無法遵守」：從 templates/dispatch-package.md:55 撤除 wf-review-receipt:v1 紀律、canonical 明寫查核者身分機械上不可驗證由需求方背書，並讓 doctor --review-channel 據實標註 identity_basis，使 [recorded] 不再讀起來像身分已驗證。**適用時機**：要判斷一次裁決的「查核者是誰」有多少證據力（2026-08-19 五筆跨家族裁決收據數為 0 而 doctor 全綠）；或要查為何不採代貼收據與 receipt_untranscribed 警告時。⛔ 非射程：不做需求方代貼收據，也不新增警告或阻擋；PM 轉錄是否忠實仍無機器面檢查，該缺口歸 WF-REVIEW-RECEIPT-WRITEBACK1。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：dispatch-package.md:55 要求查核者留 wf-review-receipt:v1 收據、PM 只能轉錄與收據 hash 相符的報告、且明文「不能以 --reviewer 自由字串代替收據」。但跨家族查核者**沒有 GitHub 寫入通道**（既有事實，見 ai-workflow#13 與記憶 reviewer-has-no-write-channel），它貼不了收據——要收據就得由需求方代貼，而代貼者的身分又回到同一個問題。於是這條紀律在現行「需求方轉貼、PM 轉錄」的通道上**構造上無法遵守**。2026-08-19 實測：當日五筆跨家族裁決（cpbl#150、#139、ai-workflow#106、#107、#65）**收據數全為 0**，--reviewer 全是 PM 打的自由字串。⚠️ 而 wfcli doctor --review-channel 對零收據的 cpbl#150 回報 [recorded] 三面一致——它驗的是事件／Log／Project 三面是否相符，而三面都是 PM 寫的，自然一致，**收據缺席它看不見**。doctor.py:92 與 :578 有 receipt_untranscribed 這個判定，但它沒有在這條路徑上生效

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/doctor.py",
    "file:cli/tests/test_doctor.py",
    "file:templates/dispatch-package.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] ⭐ 需求方 2026-08-19 裁定：走**丙＋甲的殘留**。丙＝承認收據機制對跨家族通道不適用，從 templates/dispatch-package.md:55 移除該紀律，並在 canonical 明寫「跨家族查核者的身分機械上不可驗證，由需求方背書」。裁定理由逐字保留：乙（代貼收據）只是把不可驗證往上挪一層——需求方代貼驗的是「需求方確實貼了」而非「查核者確實這樣說」，而那件事需求方轉貼時本來就在做，多一道 hash 不增驗證力只增操作負擔；甲（doctor 報 receipt_untranscribed）會製造一個每次都響、內容永遠一樣的警告，因為收據構造上拿不到故它會永遠響，即 ai-workflow#31 停卡理由記過的「構造上不會不響的警告，在資訊量上等於靜默」
- [ ] ⚠️ 甲的殘留（配套，不可省）：doctor 對「review 事件的 --reviewer 是自由字串且無收據」**不報錯、不影響判定**，但在 --review-channel 的輸出裡**據實標明「身分由需求方背書、非機械可驗」**。目的是讓 [recorded] 不再讀起來像「身分已驗證」。推翻條件：修法後對一張零收據卡跑 doctor，輸出仍讓人讀成身分已驗證；或該標註被實作成警告／阻擋（那就退回甲，違反裁定）
- [ ] 不論如何，交付後「零收據的跨家族裁決」須有明確且一致的機器行為。推翻條件：構造一張零收據卡跑 doctor --review-channel，得到讓人讀成「已查核且身分可驗」的輸出
- [ ] ⚠️ 交付物須明寫本修法擋不住什麼。已知：doctor 仍只是偵測器（AGENTS.md 明文「擋不住任何一次違規的落地」），且**無自動執行路徑**——兩 repo 的 .github 對 doctor 零命中，只有 dispatch-package 的流程要求。移除紀律後「PM 轉錄是否忠實」完全沒有機器面檢查，此事實須寫進 canonical 而非略過。不得宣稱「已預防」
- [ ] ⚠️ 射程風險須先評估並寫進報告：templates/dispatch-package.md 是**所有派工包的來源**，移除一條紀律會影響未來每一張卡。執行者須先列出該檔現行被哪些卡／文件引用、以及移除後的連帶影響，交查核者判射程是否過寬

## 驗證

- [ ] cd cli && uv run pytest 不退化；新增測試至少涵蓋「零收據」與「有收據且 hash 相符」兩例
- [ ] 對 2026-08-19 的五張真實卡（cpbl#150／#139、ai-workflow#106／#107／#65）逐張重跑 doctor --review-channel，貼出修法前後的輸出對照——修法前全部 [recorded]，修法後應與裁定一致
## Log

- 2026-08-19T12:58:50+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-19T13:13:08+08:00 amend by wf-cli（op 86033755）→ 驗收條件：原值「[ ] ⚠️ 需求方先裁三條出路擇一，本卡不自選：(甲) doctor 對「無收據」報 receipt_untranscribed 而非 [recorded]——讓缺口可見，代價是每筆跨家族裁決都會報一筆，需同時定義它是警告還是阻擋；(乙) 裁定代貼收據的合法形式（需求方代貼＋身分自述＋PM 引用 URL），代價是身分驗證退化為「需求方背書」而非機械可驗；(丙) 承認此機制對跨家族通道不適用，從 dispatch-package.md:55 移除該紀律並在 canonical 明寫「跨家族查核者的身分機械上不可驗證，由需求方背書」。⚠️ 裁定寫進卡面後才開工；[ ] 不論選哪條，交付後「零收據的跨家族裁決」這個情境必須有明確且一致的機器行為：或報 receipt_untranscribed、或不再宣稱 [recorded]、或紀律已移除故無此檢查。推翻條件：構造一張零收據卡跑 doctor --review-channel，仍得到讓人讀成「已查核」的輸出；[ ] ⚠️ 交付物須明寫本修法擋不住什麼。已知：即使選甲，doctor 仍只是偵測器（AGENTS.md 明文「擋不住任何一次違規的落地」），且它無自動執行路徑——兩 repo 的 .github 對 doctor 零命中，只有 dispatch-package 的流程要求。不得宣稱「已預防」」→ 新值「⭐ 需求方 2026-08-19 裁定：走**丙＋甲的殘留**。丙＝承認收據機制對跨家族通道不適用，從 templates/dispatch-package.md:55 移除該紀律，並在 canonical 明寫「跨家族查核者的身分機械上不可驗證，由需求方背書」。裁定理由逐字保留：乙（代貼收據）只是把不可驗證往上挪一層——需求方代貼驗的是「需求方確實貼了」而非「查核者確實這樣說」，而那件事需求方轉貼時本來就在做，多一道 hash 不增驗證力只增操作負擔；甲（doctor 報 receipt_untranscribed）會製造一個每次都響、內容永遠一樣的警告，因為收據構造上拿不到故它會永遠響，即 ai-workflow#31 停卡理由記過的「構造上不會不響的警告，在資訊量上等於靜默」；⚠️ 甲的殘留（配套，不可省）：doctor 對「review 事件的 --reviewer 是自由字串且無收據」**不報錯、不影響判定**，但在 --review-channel 的輸出裡**據實標明「身分由需求方背書、非機械可驗」**。目的是讓 [recorded] 不再讀起來像「身分已驗證」。推翻條件：修法後對一張零收據卡跑 doctor，輸出仍讓人讀成身分已驗證；或該標註被實作成警告／阻擋（那就退回甲，違反裁定）；不論如何，交付後「零收據的跨家族裁決」須有明確且一致的機器行為。推翻條件：構造一張零收據卡跑 doctor --review-channel，得到讓人讀成「已查核且身分可驗」的輸出；⚠️ 交付物須明寫本修法擋不住什麼。已知：doctor 仍只是偵測器（AGENTS.md 明文「擋不住任何一次違規的落地」），且**無自動執行路徑**——兩 repo 的 .github 對 doctor 零命中，只有 dispatch-package 的流程要求。移除紀律後「PM 轉錄是否忠實」完全沒有機器面檢查，此事實須寫進 canonical 而非略過。不得宣稱「已預防」；⚠️ 射程風險須先評估並寫進報告：templates/dispatch-package.md 是**所有派工包的來源**，移除一條紀律會影響未來每一張卡。執行者須先列出該檔現行被哪些卡／文件引用、以及移除後的連帶影響，交查核者判射程是否過寬」；理由 依需求方 2026-08-19 裁定填入三選一的結果（丙＋甲的殘留），並把裁定理由逐字寫進卡面。原驗收條 1 的「需求方先裁三條出路擇一，本卡不自選」已履行，改為裁定結果本身；新增射程風險評估條，因 dispatch-package.md 是所有派工包的來源、移除紀律的影響面大於開卡時的估計（此點由 PM 於裁定時提出，未經查核）。。
- 2026-08-19T13:14:59+08:00 assign by wf-cli → owner Claude Fable 5@Claude Code 子agent；分支worktree claude/review-receipt-channel-111 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/receipt-channel-111；交付狀態 🔨執行中；實際能力層級 高階型（偏離卡面建議 主力型；偏離理由：卡面建議主力型；向上偏離理由為可用性：執行者是本會話子代理，繼承現行模型 Claude Fable 5（MODEL_ROUTING L3 等價），另起主力型模型的協調成本高於能力差價。射程不因層級提高而擴大——裁定已釘死走丙＋甲的殘留，執行者不得自選出路。）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-19T14:00:58+08:00 handoff by wf-cli → owner 待指派；iteration 0；SHA f772b584160ede147914efc09bcb09f26b002b01；證據 執行交付（2026-08-19）：分支 claude/review-receipt-channel-111 @ f772b58（單一 commit，rebase 至 ddb78cc），改動恰為資源宣告三檔（doctor.py +59、test_doctor.py +124、dispatch-package.md 8 行），trailer 4 行，worktree 保留。PM 複驗：identity_basis 已以 Literal 三值宣告（先前的型別診斷已消）、pytest 1052 passed、身分附註如設計不影響判定。⭐⭐ 執行者揭露一個卡面預期不成立的實測落差，且它指向 doctor 的真缺陷：驗證條 2 假設「修法前五張全部 recorded」，今日重跑**五張全部 half_written**——原因是這五張今天都已 release 結案、交付狀態推進到 🏁完成，而 --review-channel 的三面比對**沒有時間語意**，它比的是現在的狀態欄。PM 獨立複跑 cpbl#150 確認，並見 doctor 逐字輸出「請補齊狀態欄，不要重跑查核」——⚠️ 但 🏁完成 是正確的最終態不是失敗的半寫入，**這道檢查不理解 release 之後的狀態**，會把已正常結案的卡誤報為半寫入並指示補齊。此為既有缺陷非本卡引入，但本卡的驗證條因此構造上不可達，執行者改取仍停在 ✅通過 的 cpbl#126 補上 recorded 的前後對照（修法前『三面一致，狀態面已有裁決』→ 修法後『三面一致，**裁決內容**已在狀態面』＋身分基礎說明；--json 面 identity_basis=requester_endorsed）。⭐ 執行者另修一處未列於卡面的問題：recorded 路徑先前把找到的收據丟棄，導致「收據背書的 recorded」與「純自由字串的 recorded」輸出逐字相同，現一併帶出 receipt_urls／receipt_authors。條 5 射程評估先於改動完成：dispatch-package.md 被 7 處引用，唯一會斷的是 docs/WF_EVENT_MARKER_V2.md:134 的硬編行號，執行者把改寫控制成行數不變使指標未斷（已 grep 覆核）。⚠️ 查核重點：(a) **驗收條 1／4 說「寫進 canonical」而 AI_WORKFLOW.md 不在資源宣告內**，執行者寫進 dispatch-package.md（該檔自述承載 canonical §6.1）——判此是否滿足，或需 amend 資源後另做；(b) 條 3 的推翻條件是否定式判斷，執行者明言不由自己宣稱，交查核者獨立判；(c) marker_quarantined 帶收據時維持 not_applicable 是執行者的判斷非卡面指定；(d) 人類面附註靠 detail 內嵌換行而非 doctor_cmd.py 專屬渲染（該檔不在宣告內），執行者自陳是繞路非最乾淨分層。⚠️ 執行者自報三處資源宣告外的殘留不一致待裁：templates/handoff-contract.md:63 仍寫「receipt 只在查核者無法執行 wfcli 時需要」（與本卡方向相反）、docs/CONSUMER_CONFORMANCE.md:28-29 未列新增的 identity_basis、docs/WF-25-REVIEW-WRITE-CHANNEL1.md:32,52 仍以留收據為常態路徑。另：--strict exit code 只在一張卡做前後對照；「跨家族查核者構造上拿不到收據」未獨立證實（引用卡面與 #13），故收據保留為選配而非刪除；ruff 未跑（cli 環境無 ruff）。⚠️ 身分不符：assign 記 Claude Fable 5、實際為 Opus 5，歸因 coordinator（PM 派工時的 --assignee 值）。。
- 2026-08-19T14:11:13+08:00 review by wf-cli → APPROVE（✅通過）；查核者 Google DeepMind Antigravity；core_pain_resolved yes；self_run 7 項；findings 4 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-REVIEW-RECEIPT-CHANNEL1-e0-f772b584160ede147914efc09bcb09f26b002b01。
- 2026-08-19T14:38:57+08:00 handoff by wf-cli → owner —（已合併）；iteration 0；SHA f772b584160ede147914efc09bcb09f26b002b01；證據 release（2026-08-19）：R1 APPROVE（Google DeepMind Antigravity，跨家族）後合併。被審 f772b58 基線未變（merge-base 即 ddb78cc）故無 rebase、被審 SHA 即被合 SHA、無保真問題；PR #114 兩 check 皆 pass 後 squash merge → main 39b53e4。merge 後驗：doctor.py 的 identity_basis 8 處落地、dispatch-package.md 的「不能以 --reviewer 自由字串代替收據」命中 0（紀律已撤）。⭐ 本卡的意義：它讓「零收據的跨家族裁決」從被讀成『已查核且身分可驗』改為據實標明『已進狀態面的是裁決內容，不是查核者身分』——而今日五筆裁決（含本卡自身）全部零收據，正是它處理的那個缺口。⚠️ 查核者列的三條 coordinator finding 待後續：canonical AI_WORKFLOW.md 未納入資源宣告故該處未同步、資源宣告外三處敘述殘留（handoff-contract.md:63／CONSUMER_CONFORMANCE.md:28-29／WF-25-REVIEW-WRITE-CHANNEL1.md:32,52）、assign 事件身分與實際模型不符。⚠️ 另一條 external finding 建議另開卡：--review-channel 的三面一致檢查無 release 後生命週期語意，會把已正常結案推進為 🏁完成 的卡誤判為 half_written 並指示補齊狀態欄。；收尾清理：已清除 worktree；遠端分支 本來就不存在；本地分支 依授權保留（未刪除）。
- 2026-08-26T22:23:09+08:00 amend by wf-cli（op a9e3a249）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:33968c8ab89dd9dbd0023e59fd1bcb1b82b1f0b4147655dceddd6a232b8a0505 (745 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5338169774 · 2026-08-19T06:03:13Z

# 跨家族查核委託：`ai-workflow#111 WF-REVIEW-RECEIPT-CHANNEL1` @ `f772b584160ede147914efc09bcb09f26b002b01`（2026-08-19）

你無 wfcli 寫入通道——產出文字裁決＋findings，由需求方轉貼、PM 轉錄。全程唯讀，收尾回報兩棵真樹 `git status --porcelain -uno` 為空。

## 環境

```
worktree      /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/receipt-channel-111
分支/SHA      claude/review-receipt-channel-111 @ f772b584160ede147914efc09bcb09f26b002b01（單一 commit，rebase 至 ddb78cc）
改動          cli/src/wf_cli/doctor.py +59、cli/tests/test_doctor.py +124、templates/dispatch-package.md 8 行（＝資源宣告三檔）
契約          卡面 6 條驗收＋2 條驗證
```

進駐第一件事：`git rev-parse HEAD` 對 source_sha、工作區乾淨；不同即 review-invalid。

## 背景：需求方裁定已釘死出路

本卡開立時列三條出路，需求方 2026-08-19 裁定走 **丙＋甲的殘留**（裁定與理由逐字在驗收條 1）：

- **丙**＝承認收據機制對跨家族通道不適用，從 `dispatch-package.md` 移除該紀律，並明寫「跨家族查核者的身分機械上不可驗證，由需求方背書」。
- **甲的殘留**＝doctor 對「`--reviewer` 是自由字串且無收據」**不報錯、不影響判定**，但據實標明身分基礎。⚠️ **標成警告或阻擋就是違反裁定。**

## ⭐ 第一判準

痛點是：`dispatch-package.md` 要求收據、明文禁止以 `--reviewer` 自由字串代替，而跨家族查核者**沒有 GitHub 寫入通道**故收據構造上取不到；同時 `doctor --review-channel` 對零收據回 `[recorded]` 讓人讀成「已查核且身分可驗」。

判：**痛點是否已消**——現在零收據的裁決是否有明確且一致的機器行為，且 `[recorded]` 是否不再讀成身分已驗證。

## 要驗的

1. **「不影響判定」的三重證據**：`test_identity_annotation_is_not_a_warning_and_not_a_gate` 釘住有收據／零收據兩種輸入的 `(status, expected, actual)` 三欄逐欄相同；`--strict` 的 exit code 前後不變；附註措辭自述「這不是缺陷」且不掛在 warning／blocking 通道。⚠️ **親跑至少第一項**，並自己構造零收據樣本驗第二項。
2. **`identity_basis` 的三值分派是否正確**：`requester_endorsed`／`receipt_backed`／`not_applicable`。⚠️ 執行者把 `marker_quarantined` 帶收據時也維持 `not_applicable`（理由：沒有裁決被採認就沒有身分問題）——**這是執行者的判斷、非卡面指定**，判是否正確。
3. **`recorded` 路徑先前丟棄收據**（使「收據背書」與「純自由字串」輸出逐字相同），現一併帶出 `receipt_urls`／`receipt_authors`——這是執行者自己加的、未列於卡面，判是否該收。
4. **射程評估（驗收條 5，執行者先於改動完成）**：`dispatch-package.md` 被 7 處引用，唯一會斷的是 `docs/WF_EVENT_MARKER_V2.md:134` 的**硬編行號**，執行者把改寫控制成**行數不變**使指標未斷。⚠️ **親自複核該行號現在指到什麼**。
5. `pytest`：改動前 1045 collected → 改動後 **1052 passed**（新增 7 個測試，含卡面要求的零收據與有收據兩例）。

## ⚠️ 本輪最重要的裁決題（執行者與 PM 都無法自判）

**驗收條 1／4 說「寫進 canonical」，而 `AI_WORKFLOW.md` 不在本卡資源宣告內。** 執行者把陳述寫進 `templates/dispatch-package.md`（該檔開頭自述「承載 canonical `AI_WORKFLOW.md` §6.1」）。

判：**這是否滿足「寫進 canonical」**，或需 amend 資源宣告後另做。⚠️ 這是 PM 開卡時的射程疏漏，歸因 coordinator。

## ⭐ 執行者揭露的既有缺陷（非本卡引入，但影響驗證條 2）

驗證條 2 要求「對五張真實卡（`cpbl#150`／`#139`／`ai-workflow#106`／`#107`／`#65`）跑修法前後對照」，並假設「修法前全部 `recorded`」。**今日重跑五張全部 `half_written`**——因為它們今天都已 release 結案、交付狀態推進到 `🏁完成`，而 `--review-channel` 的三面比對**沒有時間語意**，比的是現在的狀態欄。PM 獨立複跑 `cpbl#150` 確認，doctor 逐字輸出「請補齊狀態欄，不要重跑查核」。

⚠️ **但 `🏁完成` 是正確的最終態，不是失敗的半寫入**——這道檢查不理解 release 之後的狀態，會把已正常結案的卡誤報並指示補齊。

執行者改取仍停在 `✅通過` 的 `cpbl#126`（`244c9df8be069458b7629042a469b137fce60cdf`）補 `recorded` 的前後對照。判：**這個替代是否可接受**，以及該既有缺陷要不要另開卡。

## 執行者自報、需你判分量的

- **三處資源宣告外的殘留不一致**（未改，交裁）：`templates/handoff-contract.md:63` 仍寫「receipt 只在查核者無法執行 wfcli 時需要」（與本卡方向相反）、`docs/CONSUMER_CONFORMANCE.md:28-29` 未列新增的 `identity_basis`、`docs/WF-25-REVIEW-WRITE-CHANNEL1.md:32,52` 仍以留收據為常態路徑。
- **「跨家族查核者構造上拿不到收據」未獨立證實**（引用卡面與 `#13`），故執行者把收據保留為**選配**而非整段刪除——「若某查核者其實貼得了，紀律不該堵死它」。判此保留是否正確。
- `--strict` exit code 只在**一張**卡做前後對照，未六張全跑。
- 人類面附註靠 `detail` 內嵌換行而非 `doctor_cmd.py` 專屬渲染（該檔不在宣告內），執行者自陳是繞路非最乾淨分層。
- `ruff` 未跑（`cli/` 的 uv 環境無 ruff）。
- **身分不符**：assign 事件記 `Claude Fable 5`、實際執行為 `Opus 5`，commit trailer 照實際身分寫。⚠️ 歸因 **coordinator**（PM 派工時的 `--assignee` 值），非執行者過失。

## 回報格式

裁決 `APPROVE`／`REQUEST_CHANGES`＋`core_pain_resolved: yes|no`＋理由；findings 結構化欄位——⚠️ **`severity` 只能用 `critical|major|minor|info`、`finding_class` 只能用 `implementation|authoritative-artifact|governance|coordination|environment`、`attribution` 只能用 `executor|planner|coordinator|reviewer|external`**（前四次轉錄都因用了列舉外的詞而需 PM 映射）；`self_run` 必填（無 self_run 的 APPROVE 無效）。⭐ 沒驗到的不得省略；5xx/空回應標 UNKNOWN。

⚠️ 報告與留言**不得出現 event marker 的完整前綴字面**（`wf-review-event` 緊接半形冒號）——契約會把含該前綴的留言判為受管轄，引用即停機。寫「event marker」或「前綴（冒號略）」。


## Comment 5338249457 · 2026-08-19T06:11:14Z

<!-- wf-review-event:v1 card_id=WF-REVIEW-RECEIPT-CHANNEL1 source_sha=f772b584160ede147914efc09bcb09f26b002b01 attempt_id=WF-REVIEW-RECEIPT-CHANNEL1-e0-f772b584160ede147914efc09bcb09f26b002b01 -->
## 查核裁決：APPROVE

- 卡：`WF-REVIEW-RECEIPT-CHANNEL1`　attempt_id：`WF-REVIEW-RECEIPT-CHANNEL1-e0-f772b584160ede147914efc09bcb09f26b002b01`
- 查核者：Google DeepMind Antigravity　escalation_epoch：0
- source_sha：`f772b584160ede147914efc09bcb09f26b002b01`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-19T14:11:13+08:00

### self_run（查核者實跑）

- `git -C <worktree> rev-parse HEAD`
  - f772b584160ede147914efc09bcb09f26b002b01（對齊 source_sha）
- `uv run --directory cli pytest`
  - 1052 passed in 60.39s（原 1045 ＋ 新增 7）
- `uv run --directory cli pytest tests/test_doctor.py -k 'receipt or identity or half_written or quarantined'`
  - 17 passed, 139 deselected in 0.03s
- `Python 腳本獨立構造零收據與有收據樣本，跑 audit_review_channel 與 --strict exit code`
  - 狀態全為 recorded、expected/actual 全同（recorded/✅通過/✅通過）、exit code 全為 0、detail 含「不是缺陷」「不改變上面的判定」。⚠️ PM 補正：對 cpbl 真 repo 實跑 --strict 得 exit 1（與執行者一致），該 1 來自 repo 本地既有的其他 doctor 發現、改碼前即為 1；查核者的 0 出自隔離模擬。兩者皆支持「身分附註不改變 exit code」
- `硬編行號指針核對：docs/WF_EVENT_MARKER_V2.md:134 與 templates/dispatch-package.md:56`
  - line 56 精確指向「留言引用紀律」，指針未斷。⚠️ PM 補正：查核者報範本 57 行，PM 實測 wc -l 為 56 行；指標正確性不受影響
- `audit_commit_trailers('HEAD~1..HEAD')`
  - 違規 0、合規 1、無所要求 0
- `git status --porcelain -uno（worktree 與兩棵主工作樹）`
  - 皆為空

### findings（4，其中 blocking 0）

- **WF-REVIEW-RECEIPT-CHANNEL1-R1-01**　severity=info　blocking=false　class=coordination　attribution=coordinator　root_cause_id=`canonical-not-in-resource-declaration`
  - evidence：查核者原以 description 欄名書寫，逐字：卡面驗收條要求『寫進 canonical』，但資源宣告未包含 AI_WORKFLOW.md。執行者在 templates/dispatch-package.md 完成改寫，滿足派工紀律撤除之實質需求。裁定：可接受——執行者嚴格遵守資源宣告邊界（不跨界越權寫入 AI_WORKFLOW.md），且修改派工包範本已直接達成派工紀律撤除與身分說明的實質目標。
  - disposition：未將 AI_WORKFLOW.md 納入宣告歸因 coordinator 疏漏；後續文檔整併時同步即可。
- **WF-REVIEW-RECEIPT-CHANNEL1-R1-02**　severity=info　blocking=false　class=authoritative-artifact　attribution=coordinator　root_cause_id=`receipt-discipline-residuals-outside-scope`
  - evidence：查核者原欄名 description，逐字：資源宣告外存在 3 處敘述殘留（templates/handoff-contract.md:63、docs/CONSUMER_CONFORMANCE.md:28-29、docs/WF-25-REVIEW-WRITE-CHANNEL1.md:32,52），執行者依寫入界線未予更動。
  - disposition：待後續專卡或文檔掃描更新。
- **WF-REVIEW-RECEIPT-CHANNEL1-R1-03**　severity=minor　blocking=false　class=implementation　attribution=external　root_cause_id=`review-channel-lacks-post-release-lifecycle-semantics`
  - evidence：查核者原欄名 description，逐字：--review-channel 的三面一致檢查未包含 release 後生命週期語意，導致已正常結案推進為『🏁完成』的卡面被誤判為 half_written 並要求補齊狀態欄。此為既有缺陷。⭐ 查核者另裁定：執行者以仍停留在 ✅通過 的 cpbl#126 進行前後比對之替代**完全可接受**。
  - disposition：建議另開卡追蹤修復生命週期感知能力。
- **WF-REVIEW-RECEIPT-CHANNEL1-R1-04**　severity=info　blocking=false　class=coordination　attribution=coordinator　root_cause_id=`assign-owner-model-mismatch`
  - evidence：查核者原欄名 description，逐字：派工 assign 事件記載為 Claude Fable 5，實際執行者為 Claude Opus 5。commit trailer 已依實質身分載明，無違規。
  - disposition：歸因 coordinator（派工時 --assignee 設定偏差），不影響本卡交付成果。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-REVIEW-RECEIPT-CHANNEL1-e0-f772b584160ede147914efc09bcb09f26b002b01
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待指派
findings:
  - finding_id: WF-REVIEW-RECEIPT-CHANNEL1-R1-01
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: coordination
    attribution: coordinator
    root_cause_id: canonical-not-in-resource-declaration
    counting_eligible: false
  - finding_id: WF-REVIEW-RECEIPT-CHANNEL1-R1-02
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: authoritative-artifact
    attribution: coordinator
    root_cause_id: receipt-discipline-residuals-outside-scope
    counting_eligible: false
  - finding_id: WF-REVIEW-RECEIPT-CHANNEL1-R1-03
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: implementation
    attribution: external
    root_cause_id: review-channel-lacks-post-release-lifecycle-semantics
    counting_eligible: false
  - finding_id: WF-REVIEW-RECEIPT-CHANNEL1-R1-04
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: coordination
    attribution: coordinator
    root_cause_id: assign-owner-model-mismatch
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。
