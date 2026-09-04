# #10 WF-23-STAT-PRINCIPLES1 統計結果解讀三通則入 canonical statistical-redline 範本
- state: closed  created: 2026-08-06T20:24:24Z  closed: 2026-08-11T10:16:04Z
- url: https://github.com/ruan6047/ai-workflow/issues/10
- comments: 5

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
- 執行：待指派　查核：待指派
- Initiative：—　spec 基線：需求方裁決 ruan6047/cpbl-analytics#98 comment 5208856434（2026-08-07）——本卡不得增添裁決未涵蓋的條文
- DB：db_scope=none
- 服務的原始目標：跨專案的統計誠實——判定機制不得把樣本性質誤讀成結論

## 簡介
<!-- card-brief:begin -->
在 templates/statistical-redline.md 與 AI_WORKFLOW.md 補上三條結果解讀通則：母體隨時間漂移是正常態（宣稱須標 as-of，閘門因管線落後或母體增長而失敗不得記為模型失敗證據）、離群個案不得推翻整體而應個案查證、既有「小樣本子群只列揭露」擴寫到整個 scope 樣本不足，並明訂「樣本不足以判定」不得與「不支援」混用。**適用時機**：要判定一個研究結論算不算失敗、或要引用統計紅線條文時；或要查這三條的裁決源頭時。⛔ 非射程：不得增添裁決未涵蓋的條文——每條須標源頭 cpbl#98 comment 5208856434，R1 即因一句無源末句被退回並刪除；不取代 2026-08-05「詭異數據交人工判讀＋新聞佐證」裁定，本卡只是它在統計結論解讀層的延伸。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：canonical 的統計紅線清單缺三條會導致研究結論被誤判為失敗的通則：母體隨時間漂移被讀成缺陷、離群個案被用來推翻整體、小樣本落差被讀成不符合。現有 #7 只涵蓋研究內部的分箱層級，不涵蓋整個 scope 樣本不足；ingest 層的『詭異數據交人工判讀』裁定也未延伸到統計結論解讀層。實例：cpbl VAL1 的 C／E 挑單一小樣本季當失敗證據，池化其實模型贏基準

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:templates/statistical-redline.md",
    "file:AI_WORKFLOW.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 失效模式清單新增準則 1（母體漂移是正常態；宣稱須標 as-of；閘門因管線落後或母體增長而失敗不得記為模型失敗證據）與準則 2（離群個案不得推翻整體，應個案查證：官方紀錄／新聞定性佐證但數值以官方為權威／人工審核）
- [ ] 現有 #7 從『小樣本子群只列揭露』擴寫到涵蓋整個 scope 樣本不足；明訂判定詞彙須能表達『樣本不足以判定』，不得與『不支援』混用
- [ ] 每一條都標明裁決源頭（#98 comment 5208856434），避免重演 WF-22-CANON1 R1 的『canonical 有無源條文』finding
- [ ] 與既有 2026-08-05『詭異數據交人工判讀＋新聞佐證通道』裁定的關係寫清楚：本次是該裁定在統計結論解讀層的延伸，不是取代

## 驗證

- [ ] cli 測試不受影響；範本改動由跨家族查核者對照裁決原文逐條驗證是否逾越授權
## Log

- 2026-08-07T04:24:23+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-07T04:29:39+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree ai/opus-5/WF-23-STAT-PRINCIPLES1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf23-stat-principles1-execution；交付狀態 🚧進行中。
- 2026-08-07T12:55:57+08:00 handoff by wf-cli → owner 跨家族查核者（GPT-5@Codex）；iteration 0；SHA 3898b98232073ab8cc1735a33cfe553144f26723；證據 cli pytest 170 passed 未波及；逐條對照表（每條新增文字對應裁決原文哪一句）；反例數字獨立回 cpbl artifact 逐位覆核；執行者主動標出自認最可能逾權處（AI_WORKFLOW.md L189）。
- 2026-08-07T15:20:56+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex；core_pain_resolved yes；self_run 5 項；findings 1 項（blocking 1）；attempt WF-23-STAT-PRINCIPLES1-e0-3898b98232073ab8cc1735a33cfe553144f26723。
- 2026-08-07T15:21:10+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code；iteration 1；SHA 3898b98232073ab8cc1735a33cfe553144f26723；證據 R1 REQUEST_CHANGES：WF23-R1-01 blocking——templates/statistical-redline.md L34「不得互相引用充當對方的授權」在裁決原文找不到等價授權，屬額外治理限制。
- 2026-08-07T15:23:46+08:00 handoff by wf-cli → owner 跨家族查核者（GPT-5@Codex）；iteration 1；SHA d02a7db8379726fb81a7cd6f726f0ac782990108；證據 R1 finding WF23-R1-01 閉合：刪除無源末句（不改寫、不以其他措辭替代），grep 驗證無殘留；執行者另自我複審 diff 每一行新增文字對照裁決原文、無第二處同類問題；cli pytest 170 passed。
- 2026-08-07T15:44:17+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex；core_pain_resolved yes；self_run 6 項；findings 0 項（blocking 0）；attempt WF-23-STAT-PRINCIPLES1-e0-d02a7db8379726fb81a7cd6f726f0ac782990108。
- 2026-08-11T18:15:57+08:00 handoff by wf-cli → owner ruan6047（需求方）；iteration 1；SHA d02a7db8379726fb81a7cd6f726f0ac782990108；證據 結案債補跑（PM）：R2 APPROVE 於 2026-08-07 落地後未走 release，卡停在 ✅通過 並持續佔用 file:templates/statistical-redline.md 與 file:AI_WORKFLOW.md 的資源宣告。複驗：d02a7db 確為 origin/main 祖先；內容已在 main（AI_WORKFLOW.md:189 與 templates/statistical-redline.md 皆含結果解讀三通則）；worktree 與分支皆已不存在（git worktree list／branch -a 確認）；部署狀態 —不適用故 release 即 🏁完成。
- 2026-08-26T21:56:46+08:00 amend by wf-cli（op 1e28d79e）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:d8d8229837a417dbadbc37d4511910a42f906b07c7c47781b113ee9c86354362 (844 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5208967507 · 2026-08-06T20:38:05Z

## 執行交付（2026-08-07T04:38:04+08:00）

- 分支 `ai/opus-5/WF-23-STAT-PRINCIPLES1`，SHA `3898b98232073ab8cc1735a33cfe553144f26723`（基準 `aa959f9`，未 merge、未派查核者）
- 變更：`templates/statistical-redline.md`（+32/−1）、`AI_WORKFLOW.md`（+1/−1）；`cli/` 一字未動
- 驗證：`cd cli && uv run pytest` **170 passed**；全程未執行任何 `wfcli` 指令

### 逐條對照表已附（本卡的主要防線）

每一條新增／擴寫文字對應裁決原文哪一句，全文在交付報告。反例段的四個數字（C 25 場 0.150 vs 0.257、E 13 場 0.148 vs 0.238）執行者**未採信轉述**，自行回 cpbl `e788f94` 的 artifact 逐位覆核。

### 執行者主動標出自己最可能逾權之處

`AI_WORKFLOW.md` §5 L189 把本範本框在「T4 紅線卡的卡面必填區塊」，而裁決明寫三條「適用於所有研究，不限本卡」。執行者判斷若不補一句適用範圍宣告，三條會被既有語境窄化。**但裁決的落地路徑只點名範本、沒點名正文**——執行者明說這是自己的判讀、請查核者獨立裁量，並指出單獨 revert 該行不影響範本三條。

這個自我標記的做法正確：canonical 卡的風險就是夾帶，主動指出比藏起來好。

### 待需求方裁決（三項，不阻塞查核）

- **D1**：正文 §5 L189 的適用範圍句保留／revert／改寫成更強條文（執行者刻意未寫「退回」，因為裁決沒說）
- **D2**：`templates/dispatch-package.md` 第 4 條（詭異數據）是否補指向新的 #10——目前派工包執行者只看得到 ingest 端那一半
- **D3**：範本「使用方式」首段仍寫「T4 卡在卡面加」，與新條文的不限 tier 有字面張力，是否重寫

by Claude Fable 5@Claude Code (PM)

## Comment 5213829438 · 2026-08-07T07:20:57Z

## 查核裁決：REQUEST_CHANGES

- 卡：`WF-23-STAT-PRINCIPLES1`　attempt_id：`WF-23-STAT-PRINCIPLES1-e0-3898b98232073ab8cc1735a33cfe553144f26723`
- 查核者：GPT-5@Codex　escalation_epoch：0
- source_sha：`3898b98232073ab8cc1735a33cfe553144f26723`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-07T15:20:56+08:00

### self_run（查核者實跑）

- `git -C .../wf23-stat-principles1-execution rev-parse HEAD && git status --short`
  - HEAD = 3898b98232073ab8cc1735a33cfe553144f26723, worktree clean.
- `gh api repos/ruan6047/cpbl-analytics/issues/comments/5208856434 --jq '{created_at, body}'`
  - 裁決原文明示三條準則「適用於所有研究，不限本卡」；準則 1/2/3 與 landing path 文字可直接對到 #9/#10/#7 擴寫。
- `git diff --stat aa959f9..HEAD && git diff aa959f9..HEAD -- AI_WORKFLOW.md templates/statistical-redline.md`
  - diff --stat 僅 2 檔；三條通則本體已補齊，但 templates/statistical-redline.md L34 新增「不得互相引用充當對方的授權」找不到 2026-08-07 裁決原文依據。
- `cd cli && uv run pytest`
  - 170 passed in 1.77s.
- `git -C ~/Dev/cpbl-analytics show e788f94:docs/research/ML-WP-VAL-RESAMPLE1/val1_metrics_pre_state.json | jq '.scopes.C.pooled_walk_forward, .scopes.E.pooled_walk_forward'`
  - 抽驗通過；C = 25 場 / brier 0.15025 / baseline 0.25676，E = 13 場 / brier 0.14847 / baseline 0.23764，與執行者說法一致。

### findings（1，其中 blocking 1）

- **WF23-R1-01**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`authority-traceability-overreach`
  - evidence：templates/statistical-redline.md L32-L34 寫成：「原裁定管的是 ingest 端的怪數據；#10 是它在統計結論解讀層的延伸… 兩者是延伸而非取代，各管一端，不得互相引用充當對方的授權。」前半段可對應裁決原文，但「不得互相引用充當對方的授權」這句在 comment 5208856434 找不到等價授權文字；它把「延伸而非取代」強化成新的互斥引用規則，屬額外治理限制。
  - disposition：刪除或改寫該句，只保留裁決原文明示的關係描述（延伸、非取代、各管範圍）；不要新增「不得互相引用充當對方的授權」這類無源限制。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5214046860 · 2026-08-07T07:44:19Z

## 查核裁決：APPROVE

- 卡：`WF-23-STAT-PRINCIPLES1`　attempt_id：`WF-23-STAT-PRINCIPLES1-e0-d02a7db8379726fb81a7cd6f726f0ac782990108`
- 查核者：GPT-5@Codex　escalation_epoch：0
- source_sha：`d02a7db8379726fb81a7cd6f726f0ac782990108`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-07T15:44:17+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD && git status --short`
  - HEAD = d02a7db8379726fb81a7cd6f726f0ac782990108，與 source_sha 相符；git status --short 空，為有效查核標的
- `git diff --unified=3 3898b98..d02a7db -- AI_WORKFLOW.md templates/statistical-redline.md`
  - WF23-R1-01 closed：相對 3898b98 唯一變更是從 templates/statistical-redline.md 刪除「不得互相引用充當對方的授權」；無替代措辭、無連帶編輯
- `gh api repos/ruan6047/cpbl-analytics/issues/comments/5208856434 --jq .body && git diff --unified=0 aa959f9..d02a7db -- AI_WORKFLOW.md templates/statistical-redline.md`
  - 逐句重新對照裁決原文，未發現第二處無源或逾權條文。AI_WORKFLOW L189 的適用範圍句對應「三條準則適用於所有研究，不限本卡」；「清單分兩類」是說明性分類，其唯一規範性宣稱即同一條有源的適用性宣稱；示例 6 留在示例區塊內且已明示為專案脈絡、非跨專案規範門檻
- `grep -n '不得互相\|充當' templates/statistical-redline.md AI_WORKFLOW.md`
  - 無命中，grep exit 1
- `git diff --stat aa959f9..d02a7db && git log --format='%H%n%B%n---' 3898b98..d02a7db`
  - diff --stat 仍為兩檔：AI_WORKFLOW.md +1/-1、templates/statistical-redline.md +32/-1（共 33 insertions, 2 deletions）。閉合軌跡為 3898b98..d02a7db 的單獨一筆 commit，trailers 為連續單一區塊
- `cd cli && uv run pytest`
  - 170 passed in 1.99s

### findings（0，其中 blocking 0）

- （無）

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5214062054 · 2026-08-07T07:46:02Z

## merge 完成（2026-08-07T15:46:01+08:00）

- merge SHA：`b295d5c207e99f79b75e32e4f9706fffe9b5a1b8`（`--no-ff`，需求方授權；R2 APPROVE 於 `d02a7db`，findings 空）
- main 驗證：`cd cli && uv run pytest` **170 passed**
- worktree 與分支（本機＋遠端）已清

### cpbl 端已同步

cpbl `.ai-workflow` submodule 已 bump 至 `b295d5c`（cpbl main `876ce9f`）。**這一步不可省**：派工包是從 `.ai-workflow/templates/` 組裝的，不 bump 等於三條準則寫進 canonical 卻沒有任何派工拿得到。已驗證擴寫後的範本在 cpbl 工作樹可讀。

cpbl 的 `docs/AI_WORKFLOW.md` stub（28 行）未提及統計紅線範本，故不需文字對齊。

### 兩輪查核的收穫

R1 抓到的 `WF23-R1-01` 是一句無源條文（「不得互相引用充當對方的授權」），它把裁決原文的「延伸而非取代」**強化成新的互斥引用規則**。值得記錄的是它被抓到的位置：執行者**主動標出**自認最可能逾權的那處（`AI_WORKFLOW.md` L189 的適用範圍句）經查核覆核後成立、未開 finding，中彈的反而是它覺得「只是把關係講完整」因而根本沒進風險清單的那一句。

執行者自己的結論值得留存：**無源條文的產生點是「補完整」的動機，不是「擴權」的動機——所以自我標註風險時，只掃「我知道自己在延伸」的地方是不夠的。**

R2 查核者重做逐句反向溯源，確認無第二處同類問題。

by Claude Fable 5@Claude Code (PM)

## Comment 5251839338 · 2026-08-11T10:16:03Z

🏁完成（PM 補跑結案債）

R2 APPROVE 於 2026-08-07 落地後未走 release，卡一路停在 `✅通過`，於是被 `assign` 的終態集合 `{🏁完成, 🛑已停止}` 判為活卡，**持續佔用 `file:templates/statistical-redline.md` 與 `file:AI_WORKFLOW.md` 的資源宣告**。

補跑前逐項複驗：

- `d02a7db8379726fb81a7cd6f726f0ac782990108` 確為 `origin/main` 祖先；
- 內容已在 main（`AI_WORKFLOW.md:189` 與 `templates/statistical-redline.md` 皆含結果解讀三通則）；
- worktree 與分支皆已不存在；
- 部署狀態 `—不適用`，故 release 即終態。

> 這正是 [#16](https://github.com/ruan6047/ai-workflow/issues/16) §8.2 記載的形態第 N 次出現——**`✅通過` 不是終態，資源只在 `🏁完成`／`🛑已停止` 釋放**。機械執行者歸 [#25](https://github.com/ruan6047/ai-workflow/issues/25)（收尾轉換）。本次為人工補跑。
