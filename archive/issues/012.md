# #12 WF-CLI-TIER-MUTATION1 wfcli 補上已開卡的 tier 更正能力（現在只能在 open 時設定）
- state: closed  created: 2026-08-08T09:36:34Z  closed: 2026-08-10T16:37:14Z
- url: https://github.com/ruan6047/ai-workflow/issues/12
- comments: 5

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
- 執行：待指派　查核：待指派
- Initiative：—　spec 基線：cpbl-analytics#107 ER-REBUILD-R3-001（root_cause_id=WFCLI-TIER-MUTATION-GAP，attribution=external）＋需求方 2026-08-08 裁定手動更正為授權例外
- DB：db_scope=none
- 服務的原始目標：開卡時標錯的欄位要有合規的更正路徑，不必在違規與死結之間二選一

## 簡介
<!-- card-brief:begin -->
開卡時標錯的欄位要有合規更正路徑。tier 本身已由 `#19` 的 `amend --tier` 交付，本卡承接殘餘射程：核心痛點、服務的原始目標、Initiative、鏈深、卡片標題今日仍無更正路徑，其中核心痛點餵給 `core_pain_resolved`、而該欄在 `templates/review-prompt.md` §2 具否決權。**適用時機**：發現某張已開卡的欄位標錯而 wfcli 改不動、只能在違規與死結之間二選一時。⛔ 非射程：tier 的更正路徑已由 `#19` 交付、本卡不重做；不得改 Projects v2 的欄位定義（本專案曾因此讓 56 張卡狀態被清空）。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：wfcli 的六個指令（open／assign／handoff／review／doctor／snapshot）沒有任何一個能修改已開卡的 tier，只能在 open 時設定。2026-08-08 #107 開卡誤標 T3、跨家族查核判應為 T4（canonical §5 明列統計／ML 與資料正確性為紅線卡），結果是：PM 不能改（紅線 1：wfcli 是狀態面唯一寫入通道，且本專案有直接改 Projects v2 欄位導致 56 張卡狀態被清空的前例），需求方手動在 Project UI 改了之後，查核者又開 ER-REBUILD-R3-001 判該手動寫入違反單一寫入通道。一個 blocking finding 因此卡在一個不存在的能力上

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/amend_cmd.py",
    "file:cli/src/wf_cli/card.py",
    "file:cli/tests/test_amend.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] **（2026-08-12 重新界定射程）本卡原標題所述的 tier 更正能力已由 #19 交付**：amend --tier 存在（amend_cmd.py:97）、寫入級別欄、留「原值→新值＋理由」軌跡、並有半寫入偵測與自癒（先寫級別讀回驗證再寫 body，退出碼 5）。#19 驗收第 4 條要求「與 #12 的範圍界定明確：擇一實作，或明示 #12 併入本卡後關閉」——**該裁定當時未被記錄，本次補上：不關閉，改為只承接殘餘射程**。原驗收第 1、2 條視為已由 #19 滿足。
- [ ] **殘餘射程＝開卡時設定但無更正路徑的欄位。** 實測 amend 現涵蓋 spec-baseline／acceptance／verification／db-scope／resources／tier；**仍無更正路徑者：核心痛點、服務的原始目標、Initiative、鏈深、feature（卡片標題）**。逐一裁定要不要補，不必全做，但要說明取捨。
- [ ] **核心痛點優先。** 它餵給 core_pain_resolved，而該欄在 templates/review-prompt.md §2 具否決權（痛點未消即 REQUEST_CHANGES，即使驗收清單全過）。一個有否決權的欄位沒有更正路徑，其後果不是不便而是治理缺陷：2026-08-12 需求方裁定縮小 #25 射程時，核心痛點無法經唯一寫入通道修改，只能改由新驗收條文的判準吸收——PM 當場記錄「那是繞過而非修好」（見 #25 的 amend op 3cd13f81 與同日 PM 留言）。
- [ ] **更正屬治理事件**：須留下「原值→新值＋理由＋誰裁定」的軌跡，讓查核者能區分「開卡就標對」與「事後更正」（沿用原驗收第 2 條）。
- [ ] ⚠️ **動 Projects v2 欄位的實作必須避開已知事故模式**：本專案曾因 updateProjectV2Field（改欄位定義、重生選項 ID）導致 56 張卡狀態被清空。更正 item 值應走 updateProjectV2ItemFieldValue，並在測試中釘住「不得觸及欄位定義」（沿用原驗收第 4 條）。

## 驗證

- [ ] 以真實 Project 驗證更正前後的欄位值與留痕；驗完把測試卡還原或清除
- [ ] wfcli 既有測試不退步
## Log

- 2026-08-08T17:36:33+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-12T07:53:26+08:00 amend by wf-cli（op 89c002ee）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/commands/amend_cmd.py、file:cli/src/wf_cli/card.py、file:cli/tests/test_amend.py」；理由 PM 跨卡對帳 2026-08-12：收窄過寬的目錄級宣告，並記錄一件更重要的事——**本卡的主要能力已由 #19 交付，但本卡從未依 #19 的驗收第 4 條作出範圍裁定**。#19（WF-CLI-CARD-AMEND1，🏁完成）驗收第 4 條逐字要求「與 #12（tier 更正）的範圍界定明確：擇一實作，或明示 #12 併入本卡後關閉」；#19 交付的 amend 指令已含 --tier（amend_cmd.py:97）、寫入級別欄、留原值→新值＋理由軌跡、並有半寫入偵測與自癒（先寫級別讀回驗證再寫 body，退出碼 5）。本卡驗收第 1、2 條因此已實質滿足，而該裁定從未被記錄，本卡遂以 📥Backlog 狀態持續佔用整個 cli/src/wf_cli/，在階層包含語意下與 WF-CLEANUP-GUARD1、WF-MARKER-SCOPE-CLEARANCE1、WF-22-CLI4 全面相交。收窄後的宣告對應的是**尚未交付的殘餘射程**：驗收第 3 條「評估同類缺口是否還有」——實測 amend 現已涵蓋 spec-baseline／acceptance／verification／db-scope／resources／tier，但 **Initiative、鏈深、核心痛點、服務的原始目標仍無更正路徑**。其中核心痛點的缺口 PM 於同日處理 #25 時撞到並誤記為「候選歸 #9」，此處更正：那屬本卡驗收第 3 條的射程，不是 #9。是否要做殘餘射程、或直接關閉本卡，須需求方裁定。。
- 2026-08-12T08:18:03+08:00 amend by wf-cli（op fc261ae3）→ 驗收條件：原值「[ ] 提供合規的 tier 更正路徑（新指令或既有指令加旗標由執行者判斷），寫入須經 wfcli 並留痕更正理由；不得要求使用者手動改 Project UI；[ ] 更正屬治理事件，須留下「原值→新值＋理由＋誰裁定」的軌跡，讓查核者能區分「開卡就標對」與「事後更正」；[ ] 評估同類缺口是否還有：除 tier 外，其他開卡時設定的欄位（db_scope、Initiative、鏈深、資源宣告…）是否也無更正路徑。有則一併列出，不必一次全做，但要說明取捨；[ ] ⚠️ 動 Projects v2 欄位的實作必須避開已知事故模式：本專案曾因 updateProjectV2Field（改欄位「定義」、重生選項 ID）導致 56 張卡狀態被清空。更正 item 值應走 updateProjectV2ItemFieldValue，並在測試中釘住「不得觸及欄位定義」」→ 新值「**（2026-08-12 重新界定射程）本卡原標題所述的 tier 更正能力已由 #19 交付**：amend --tier 存在（amend_cmd.py:97）、寫入級別欄、留「原值→新值＋理由」軌跡、並有半寫入偵測與自癒（先寫級別讀回驗證再寫 body，退出碼 5）。#19 驗收第 4 條要求「與 #12 的範圍界定明確：擇一實作，或明示 #12 併入本卡後關閉」——**該裁定當時未被記錄，本次補上：不關閉，改為只承接殘餘射程**。原驗收第 1、2 條視為已由 #19 滿足。；**殘餘射程＝開卡時設定但無更正路徑的欄位。** 實測 amend 現涵蓋 spec-baseline／acceptance／verification／db-scope／resources／tier；**仍無更正路徑者：核心痛點、服務的原始目標、Initiative、鏈深、feature（卡片標題）**。逐一裁定要不要補，不必全做，但要說明取捨。；**核心痛點優先。** 它餵給 core_pain_resolved，而該欄在 templates/review-prompt.md §2 具否決權（痛點未消即 REQUEST_CHANGES，即使驗收清單全過）。一個有否決權的欄位沒有更正路徑，其後果不是不便而是治理缺陷：2026-08-12 需求方裁定縮小 #25 射程時，核心痛點無法經唯一寫入通道修改，只能改由新驗收條文的判準吸收——PM 當場記錄「那是繞過而非修好」（見 #25 的 amend op 3cd13f81 與同日 PM 留言）。；**更正屬治理事件**：須留下「原值→新值＋理由＋誰裁定」的軌跡，讓查核者能區分「開卡就標對」與「事後更正」（沿用原驗收第 2 條）。；⚠️ **動 Projects v2 欄位的實作必須避開已知事故模式**：本專案曾因 updateProjectV2Field（改欄位定義、重生選項 ID）導致 56 張卡狀態被清空。更正 item 值應走 updateProjectV2ItemFieldValue，並在測試中釘住「不得觸及欄位定義」（沿用原驗收第 4 條）。」；理由 需求方 2026-08-12 裁定：依 PM 跨卡對帳 X6 的建議，本卡不關閉、改為只承接殘餘射程。背景：#19（🏁完成）已交付本卡原標題所述的 tier 更正能力，而 #19 驗收第 4 條要求的範圍界定裁定從未被記錄，本卡遂以 Backlog 狀態持續存在並（在收窄前）佔用整個 cli/src/wf_cli/。不關閉的理由是驗收第 3 條「評估同類缺口是否還有」不但未交付，且今日產生具體觸發案例：PM 縮小 #25 射程時發現 wfcli amend 無 --core-pain，而核心痛點餵給具否決權的 core_pain_resolved。**另記一件同型事實：本卡的 feature（標題）本身也無更正路徑**——wfcli amend 沒有 --feature，故本卡將持續帶著一個描述已交付工作的標題。那不是註腳，是本卡殘餘射程的活體實例：標題與核心痛點一樣是開卡時設定、事後無法經唯一寫入通道更正的欄位。。
- 2026-08-12T09:44:47+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；分支worktree claude/WF-CLI-TIER-MUTATION1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-cli-tier-mutation1；交付狀態 🚧進行中；實際能力層級 主力型（卡面無建議層級：卡面標頭區沒有獨立成行的 <!-- wf-routing:v1 --> 宣告：本卡開立於規劃期路由必填之前；理由：卡面第 4 行為舊制格式（執行：待指派），依 WF-CLI-ROUTING-TIER1 R4-002 的需求方裁定，既有 18 張卡永久以 absent 派工、不補標記、不新增遷移入口，故無建議層級可比對，依 assign 規則必填偏離理由。實際派主力型的依據：本卡射程是 wfcli 寫入通道的欄位更正能力，需逐一判定哪些開卡欄位缺更正路徑並權衡是否補，推理鏈中等、無需前沿能力；且它直接解鎖 WF-CLEANUP-GUARD1（T4）卡在核心痛點無更正通道的 blocking。）。
- 2026-08-12T10:05:54+08:00 handoff by wf-cli → owner 已結案（能力由 #19 交付，殘餘射程轉出）；iteration 0；SHA 6e6e8abd650c76fa6a2173f5dff35f99038ca1e0；證據 需求方 2026-08-12 裁定結案，原話「#12 結案，以正確標題另開卡承接殘餘射程」。結案依據分兩半：(1) 本卡驗收第 1、2 條所述的 tier 更正能力已由 #19（WF-CLI-CARD-AMEND1，🏁完成）交付——amend --tier 存在於 amend_cmd.py:97、寫級別欄、留原值→新值＋理由軌跡、有半寫入偵測與自癒；#19 驗收第 4 條當時即要求「與 #12 的範圍界定明確：擇一實作，或明示 #12 併入本卡後關閉」，該裁定拖至今日才被記錄。(2) 驗收第 3 條的殘餘射程（開卡時設定但無更正路徑的欄位）轉出至新卡承接，含需求方本日裁定的三項：核心痛點帶授權綁定、--tier 降級不對稱、--resources 雙面同步。轉案而非放棄。**結案同時解決本卡的狀態面三方不一致**（Issue 自 2026-08-08 即 CLOSED、Project 內建 status=Done、自訂交付狀態仍 🚧進行中）——該不一致源於 08-08 依「已由 #19 併入」關閉後、08-12 的 amend／assign 未重開。⚠️ 未使用 --cleanup：worktree claude/WF-CLI-TIER-MUTATION1 內有進行中的評估與實作工作，依 canonical AI_WORKFLOW.md:146「回收前先檢查未提交變更，禁止靜默刪除工作內容」，該 worktree 與分支由 PM 於交付時轉掛新卡，不在本次結案清理。資源宣告（amend_cmd.py／card.py／test_amend.py）隨之移交新卡。。
- 2026-08-26T14:21:09+08:00 amend by wf-cli（op ff43263c）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:d4f91032d2e720b7731e1ff30f0268c299b66724c141eb309855b46e80a9dc01 (629 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第二批（20 張純隨機）：依 canonical §6.3 回填簡介；文字經 A5 守衛（分行字元＋1012B 上限）預先拒收檢查。


## Comment 5226767965 · 2026-08-08T15:28:31Z

## 同族缺口追加：`resource-claims`／`db_scope` 開卡後同樣不可更正（2026-08-08T23:28:29+0800）

本卡目前的範圍是 **tier** 的開卡後更正。2026-08-08 又撞到同一族的第二個實例，記錄於此供解法一併考慮。

**實例**：`cpbl-analytics#113 DATA-INCOMPLETE-BOX-INGEST1` 的查核 finding `R1-04`（attribution: planner）要求把 `db_scope` 由 `write` 收斂為 `read`——理由是需求方已裁決「不處置」，寫入路徑不再需要，而該 PR 實際零寫入（4 檔皆為 src/tests/docs）。

**做不到**：`wfcli` 的子命令為 `open`／`assign`／`deploy-declare`／`deploy-state`／`handoff`／`review`／`doctor`／`snapshot`，**沒有任何一個能修改已開卡的 `resource-claims` 區塊或 `db_scope`**。而 `wfcli` 是狀態面唯一寫入通道，直接編輯 Issue body 即違規（`cli/README.md` 紅線 1）。PM 因此未動，改記為缺口。

**共同形狀**：**卡面欄位在 `open` 之後一律不可變。** tier 是第一個被撞到的，`db_scope`／`resources` 是第二個。若解法只針對 tier 開一個 `--set-tier`，下一個欄位會再來一次。建議解法設計時把「開卡後欄位更正」當成一類問題處理，而不是逐欄位補洞——但**哪些欄位可改、可改到什麼程度、要不要留原值痕跡**，是需要判斷的（例如 tier 下修與上修的風險不對稱：T4→T2 會繞過紅線卡的查核要求）。

**順帶一個詞彙表缺口**（同一則 finding 提出）：`DATABASE_CONTRACT.md` §3 的 `db_namespace` 合法值只有「`<CARD_ID>` 專屬 database/schema」或 `shared-lease`，**沒有一個值能表達「宣告了 DB 意圖但尚未核發 lease」**。#113 的執行者填了 `unassigned`——不在詞彙表內但比誤填 `shared-lease` 誠實，查核者判定該保留。建議正式納入。

by Claude Fable 5@Claude Code (PM)

## Comment 5243133028 · 2026-08-10T16:37:13Z

**已由 #19（`WF-CLI-CARD-AMEND1`）併入實作，非棄置。**

本卡範圍是「開卡後的 tier 更正」。#19 實作 `wfcli amend` 時，`級別` 是 Project SINGLE_SELECT 欄位、既有 `set_field_value` 已支援，與 body 欄位放同一指令即可——兩者技術上是不同寫入面，但對使用者是同一件事「開完卡才發現要改」，拆兩張卡只會讓人記不住該用哪個。

#19 R2 查核裁定「#12 於 #19 merge 後再關閉」的時序恰當；#19 已於 main `5d821e1` 合併，故此時關閉。

用法：`wfcli amend <CARD-ID> --repo <owner/repo> --reason "開卡時填錯" --tier T3`

## Comment 5260244948 · 2026-08-11T23:54:59Z

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


## Comment 5261179907 · 2026-08-12T01:56:15Z

## PM 複驗：`amend --resources` 只寫 body、不寫 Project 欄位——含 PM 自己四次收窄的實際後果

本輪評估（未實作）抓到一個既有缺陷。PM 已逐項複驗，**成立**。

### 事實

`amend_cmd.py` 全檔**只有一處** `set_field_value`（`:392`，且只給 `級別`）。`--resources`／`--db-scope` 只走 `amend_resource_block`（body 區塊）。

而 `snapshot.py::build_rows` 同時讀兩面：`resource_summary` 取自 **Project 欄位**，`resources`／`resource_db_scope` 取自 **body**。

### PM 自己四次 `amend --resources` 的現況

| 卡 | Project 欄位（陳舊） | body（正確） | 方向 |
|---|---|---|---|
| #16 `WF-ORCHESTRATION-RECONCILE1` | `docs/…RECONCILE1.md、file:templates/` | 只有 doc | 欄位**較寬** |
| [#9](https://github.com/ruan6047/ai-workflow/issues/9) `WF-22-CLI4` | `file:cli/` | 八個具體檔 | 欄位**較寬** |
| 本卡 | `file:cli/src/wf_cli/` | 三個具體檔 | 欄位**較寬** |
| [#25](https://github.com/ruan6047/ai-workflow/issues/25) `WF-CLEANUP-GUARD1` | 只有 doc | **八個檔含 `cleanup.py`／`doctor.py`／`handoff_cmd.py`** | 欄位**較窄** ⚠️ |

**前三張是保守方向**（看板誇大佔用，最多讓人多等）。**#25 是危險方向**——看板顯示它只佔一份文件，實際持有三支 `cli/` 程式碼。有人讀看板會以為 `doctor.py` 是空的。

### 但衝突檢查沒有被騙

`assign` 的 `find_conflicts` 讀的是**卡面 body 的資源宣告區塊**，不是 Project 欄位。所以：

- **PM 的四次收窄對「擋不擋派工」是生效的**，先前的相交分析用的也是 body 值，結論不受影響。
- 受影響的是**看板／Ledger 這一面**——它與實際互斥判準不一致。

**這正是「雙居所欄位若照現行模式實作就會壞」的現成反例**，而本卡的殘餘射程裡有三個雙居所欄位（`服務的原始目標`、`Initiative`、`feature`）。

### 歸屬

`amend_cmd.py` 在本卡宣告的寫入集內，**本卡可修**。評估建議把它列入射程，PM 同意——但要不要做、與其他殘餘欄位的優先序，等需求方裁定。

### 順帶：本卡狀態面三方不一致

Issue `state=CLOSED`、Project 內建 `status=Done`、自訂 `交付狀態=🚧進行中`。2026-08-08 依「已由 #19 併入」關閉後，08-12 的 `amend`／`assign` 未重開 Issue。**PM 未逕行更動**——本卡是否重開屬需求方裁定（評估報告的建議是：正解可能是結案本卡、以正確標題另開一張承接殘餘射程）。


## Comment 5261252278 · 2026-08-12T02:08:01Z

## 結案：能力由 #19 交付，殘餘射程轉出至 [#37](https://github.com/ruan6047/ai-workflow/issues/37)

需求方 2026-08-12 裁定結案（原話：「#12 結案，以正確標題另開卡承接殘餘射程」），交付狀態 🏁完成。**這同時解決本卡自 08-08 起的狀態面三方不一致**（Issue CLOSED／Project Done／交付狀態 🚧進行中）。

**承接關係**：[#37](https://github.com/ruan6047/ai-workflow/issues/37) `WF-CARD-FIELD-CORRECTION1` 承接本卡驗收第 3 條的殘餘射程，含需求方本日裁定的三項（核心痛點帶授權綁定、`--tier` 降級不對稱、`--resources` 雙面同步）與三項不補的裁定及其理由。資源宣告（`amend_cmd.py`／`card.py`／`test_amend.py`）隨之移交。

**本卡的存在方式本身是一則記錄**：它的標題描述的是已由 #19 交付的能力，而 `wfcli amend` 沒有 `--feature`，所以那個標題永遠修不掉——**結案另開卡是繞過，不是修好**。#37 的 spec 基線欄已把這件事寫成該卡存在的理由。

⚠️ **worktree 與分支未清理**：`claude/WF-CLI-TIER-MUTATION1` 內有進行中的評估與實作工作。依 canonical `AI_WORKFLOW.md:146`「回收前先檢查未提交變更，禁止靜默刪除工作內容」，PM 將於交付時把它轉掛 #37，不在本次結案清理。
