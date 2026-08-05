# <卡ID> <功能名>  〔T0/T1/T2/T3/T4；🔴紅線 / ⚪一般〕

- 需求：<GitHub 帳號>　規劃：<模型@工具 / 帳號>
- 執行：<模型@工具／待指派>（建議 <MODEL_ROUTING 能力層級>；<能力軸理由>）　查核：<模型@工具／待指派>（<層級；紅線須跨家族或人工>；須 ≠ 執行）
- Initiative：<父卡 ID／—>　spec 基線：<版本／—>
- DB：<`db_scope`／namespace／resource claims；無影響填 `none`—canonical §4.2>
- 服務的原始目標：<這根鏈最終要解的問題；必填—canonical §3.3>
- 部署：<是/否>　環境：<staging/production/—>　PR：<#/URL>　Merge SHA：<SHA/—>
- 範圍：見 [`<spec 檔>`](../<spec 檔>) §<X>（T3/T4 必填）／或於此簡述（T0–T2）
- Discovery：<brief 路徑／人類確認者與時間／T0–T2 可填—>
- Design：<design brief 路徑／Design Gate N/A 與理由>
- owner、**分支／worktree（認領時登記實際值）**、iteration、鏈深、最後交接、阻塞與交付／部署 current-state 見狀態面（Issue／Project item，canonical §4.3）；未 cutover 的專案見 [`../TASKS.md`](../TASKS.md) Ledger。歷史寫入 adapter event log

> 「**核心痛點**」「**驗收條件**」「**驗證**」「**資源宣告**」是**標準章節名**：查核提示詞產生器、祕書 CLI 的資源交集比對與 Ledger lint 以此錨定，不得改寫為「目標與驗收」「Gate 與驗證」等變體。T4 統計／ML／資料正確性卡另須「紅線（違反即退回）」章節（見 [`statistical-redline.md`](statistical-redline.md)）。有 Initiative 的卡，`spec 基線` 欄**註冊時即必填**父卡當前版本——「—」或缺欄視同不一致，查核直接退回（[`baseline-cascade.md`](baseline-cascade.md) §5）。**分支名不是識別依據**：worktree 走註冊制，登記了才算數（canonical §4.5）。

## 核心痛點

- **痛點**：<一句話；查核報告第一行必答此痛點是否已消失，具否決權—canonical §5.1>

## 資源宣告

<!-- resource-claims:begin -->
```json
{"db_scope": "none", "resources": ["file:<path>", "port:<n>", "container:<name>", "db:<env>:table:<name>"]}
```
<!-- resource-claims:end -->

> 機器可讀的寫入集，祕書派工時據此做交集比對（canonical §4.4）。交付必要的重現工具也要列。merge 後 `file:` 資源即釋放。

## 驗收條件

- [ ] <可獨立驗證的條件；T3/T4 必填並引用 spec 章節>

## 驗證

- [ ] <驗證指令、環境與證據要求>

## Log

- <ISO 8601> handoff by <actor> → owner <actor>；iteration <n>；SHA <sha>；證據 <連結>。
- <ISO 8601> review by <actor> → approve/request-changes；finding <severity｜證據｜處置>；source SHA <sha>。
- <ISO 8601> blocked/escalated by <actor> → <原因；等待對象；解除條件／決策>。
