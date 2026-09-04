# #89 WF-BASELINE-UPSTREAM-TRIGGER1 baseline-cascade 只有下游觸發者，上游產生新基線時沒有對應出口
- state: open  created: 2026-08-16T01:53:52Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/89
- comments: 1

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；純流程與文件推理，無碼；但要改的是 canonical 引用的 runbook，措辭失真會傳播到每個採用專案，且本 repo 已有多次「規則寫對了但沒有執行路徑」的前例，需要能自己看出那個陷阱的層級。）　查核：待指派（建議 高階型；改動落在 canonical 的 runbook，一旦成文即對所有採用專案生效且不易回收；且本卡的核心主張是「機制存在、缺一個觸發方向」，查核者必須能獨立判斷這個診斷是對的，而不是又補了一條沒有讀者的規則。）
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：已經被推翻的前提不得繼續當紅線用

## 簡介
<!-- card-brief:begin -->
在 templates/baseline-cascade.md 補上「上游觸發者」：現行 runbook 只為「下游執行者發現自己偏離已核可基線」而寫，上游卡產生新結論、使他人的 spec 基線失效時沒有任何一步為那個方向而寫——ML-WP-VERDICT-ROBUST1 的 §6 宣告完整、指標正確、位置適當，八天無人讀，PM 遂據已被推翻的措辭下裁定。須明訂觸發時機可判定（merge／release／Plan 產出，不得寫「適時」）、影響集合可機械求得。**適用時機**：一張卡的結論會使別張卡的 spec 基線失效，要決定通知誰、在什麼時點、以什麼形式時。⛔ 非射程：不取代 templates/baseline-cascade.md 既有的下游觸發條文（兩者並存）；不得只加規則而無執行路徑——本 repo 已有 registered-finding label 未建立、gate_evidence 全庫零命中等前例。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：templates/baseline-cascade.md 的觸發者只有「下游執行者實作中發現偏離已核可基線」。上游卡產生新結論、使他人的 spec 基線失效時，runbook 裡沒有任何一步為那個方向而寫，於是取代關係只能寫成散文躺在報告裡。實例：ML-WP-VERDICT-ROBUST1（merge 2026-08-07）的 §6 逐字寫「#100 的對外文案要用哪個詞，等這個裁決」與「#98 §7-D1 與 AUDIT1 §3.1-D 都在等這個」——宣告完整、指標正確、位置適當，八天無人讀；2026-08-15 PM 據已被推翻的措辭下裁定，執行者據此建出一張手工覆寫表

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:templates/baseline-cascade.md",
    "file:AI_WORKFLOW.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] runbook 補上上游觸發者，並明確它與既有下游觸發者的關係（並存而非取代）——下游觸發是「我偏離了基線」，上游觸發是「我讓別人的基線失效了」，兩者的評估者與核可者是否相同須明寫;觸發時機須可判定：是 merge、release、還是 Plan 產出當下就知道會失效——不得寫成「適時」這類不可判定的詞;影響評估的對象集合須可機械求得。spec 基線 是現成的卡面欄位且實測四張 WP 卡都指名了來源文件（ROBUST1 merge 當天 grep「RESAMPLE1」即可找到 #100 與 #95），但它是自由文字——本卡須說明如何求交集，或裁定改為結構化;⚠️ 不得只加規則而無執行路徑。本 repo 與消費端已累積多個「命名了但沒接線」實例（registered-finding label 未建立、db:<env>:cpbl 被 grammar 拒收、🧭規劃中 不是狀態選項、gate_evidence 全庫零命中）。若結論是暫時只能靠人，須明寫誰在什麼時點被要求做，不得包裝成已有守衛

## 驗證

- [ ] 以 ROBUST1 → #100／#95 這組真實案例回放：若當時已有本卡的機制，#100 的裁定會在什麼時點、以什麼形式、被誰看到。回放須具體到指令或畫面，不接受「會被提醒」這種敘述;檢查本卡自己有沒有犯同一個病——本卡若成文，它使哪些既有卡的 spec 基線失效？逐一列出並跑一次自己定義的流程
## Log

- 2026-08-16T09:53:51+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-26T22:00:09+08:00 amend by wf-cli（op ac83d632）→ 簡介：原值「（原本沒有）」→ 新值「在 templates/baseline-cascade.md 補上「上游觸發者」：現行 runbook 只為「下游執行者發現自己偏離已核可基線」而寫，上游卡產生新結論、使他人的 spec 基線失效時沒有任何一步為那個方向而寫——ML-WP-VERDICT-ROBUST1 的 §6 宣告完整、指標正確、位置適當，八天無人讀，PM 遂據已被推翻的措辭下裁定。須明訂觸發時機可判定（merge／release／Plan 產出，不得寫「適時」）、影響集合可機械求得。**適用時機**：一張卡的結論會使別張卡的 spec 基線失效，要決定通知誰、在什麼時點、以什麼形式時。⛔ 非射程：不取代 templates/baseline-cascade.md 既有的下游觸發條文（兩者並存）；不得只加規則而無執行路徑——本 repo 已有 registered-finding label 未建立、gate_evidence 全庫零命中等前例。」（⚠️ 全文：totalCount=0（首寫，平台無前一版））；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。
- 2026-08-29T14:59:26+08:00 handoff by wf-cli → owner 待指派；iteration 0；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 阻塞登記（來源狀態 📥Backlog）：https://github.com/ruan6047/ai-workflow/issues/89 之阻塞留言。解除條件＝待審清單機制上線。。


## Comment 5460928549 · 2026-08-29T06:55:53Z

## 阻塞登記

**狀態**：⏸阻塞。**來源狀態：📥Backlog**（解除時回到此狀態）。

**阻塞原因**：需求方於 2026-08-29 決定，在階段狀態重整（8 階段 × 10 狀態、待審清單、CLI 射程收斂）定案並落地前，暫停所有 ai-workflow 流程卡，避免它們與重構討論互相干擾。

**可證偽的解除條件**：待審清單機制上線（label ＋ issue template ＋ 可見分組）。屆時本卡改列為清單參考項，或依當時前提是否仍成立重新排程。

**本次未做**：核心痛點、驗收條件、射程一律未動。`iteration` 未遞增。`階段` 欄未寫入。本登記僅改交付狀態與 owner。

**已知的射程重疊**（供解除時參考，非本次裁定）：#66／#38 的實質可能由「七份交接文件格式」承接；#128 可能由「待審清單收件條件三·查重留痕」＋`open --from-issue` 承接；#11 的證據紀律已部分寫入 PM 準則但痛點（靠人記得）未消失。⛔ 上述皆未經裁定，解除時須逐張重驗。

**裁定者**：需求方 ruan6047，2026-08-29 本 session 對話中指示「把目前所有 WF 卡片暫停，避免干擾目前重構討論」。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

