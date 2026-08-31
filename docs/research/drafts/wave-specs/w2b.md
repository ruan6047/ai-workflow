---
card: WF-REDESIGN-W2B
status: draft-pending-initiative
replacement_rows: []
---
> ⛔ 草稿·規劃產出物。各波開卡時逐字搬進卡面（甲′：規格住卡面＋spec_version）；本檔屆時封存。spec_version: 1


> replacement_rows 為空的原因：機械配套，無取代列。
# W2B · 配套與 contract templates（T3，依賴 W2A）

**痛點（落差）**：五份交接文件中三份（交付報告／裁決／狀態變更裁定單）無範本、兩份（派工包／派審詞）現行檔為舊制形狀；L0 入口未成形；被守衛釘住的舊模板群（封閉五檔：tasks-card.md、bug-card.md、bug-workflow.md、initiative-card.md、templates/TASKS.md——P1-15 更正：⛔ 非六檔）仍會被誤讀為現行。（stage-rules 與 tier-rules 依 P1-02 丙移入 W2A。）
**⛔ 非射程**：不動 canonical 本體（W2A 已完）；不動 CLI 碼（W3′）。
**階段計畫**：需求 → 執行 → 審核 → 結案（內容已確認，跳過研究／規劃）。
**級別依據**（P1-11 重推）：改寫 dispatch-package 等 contract templates＝public contract ⇒ **T3**。執行 主力型／查核 主力型＋獨立；需求方閘門適用。硬依賴：W2A 終態後才可開工。執行 主力型／查核 主力型。db-scope none。
**資源**：file:templates/、file:AGENTS.md、file:README.md、file:MODEL_ROUTING.md、file:docs/CONTRACT_TOOL_RECONCILE.md、file:cli/tests/test_contract_tool_reconcile.py
**驗收**：
0.（P1-35 範本 owner，四類輸出面）dispatch-package／delivery-report／review-dispatch／**closeout-report（新檔 templates/closeout-report.md，七段結案報告——falsifier 同新五檔）**全含「注意事項回應清冊」欄（逐條編號三值）
1. （P1-15 封閉 mapping）舊 → 新逐檔對照，各附 falsifier：tasks-card.md → 移除（卡面 fenced JSON 承接）；bug-card.md＋bug-workflow.md → 移除（缺陷走清單＋一般卡）；initiative-card.md → 移除（父卡模型住 stage-rules）；templates/TASKS.md → 移除（state plane）。新五檔：templates/dispatch-package.md（改寫）、templates/review-dispatch.md（新——派審信封）、templates/delivery-report.md（新）、templates/verdict.md（新）、templates/status-change-ruling.md（新）——各以「檔案存在＋含信封四段標題」為存在性判準。**（P1-15 補）templates/review-prompt.md → 改寫保留**（wfcli review 的結構化輸出契約，碼引用 6 處不動；改寫使其與 verdict.md 分工：前者 schema、後者人讀範本）；被移除各舊檔以 git grep 檔名於 post-image 驗「舊入口零引用」（mapping 文件自身除外）
2. （P1-19＋P1-32）**基線已釘（P1-32 canonical 序列化）**：`baseline-universe.json`——管線＝`contract_tool_reconcile.py --format json` → rows 依 `(kind,name)` 排序 → `json.dumps(ensure_ascii=False, sort_keys=True, separators=(',',': '))` → sha256=`c1a1279324f2b5f40421eaa0408314a1afadae2c374c0c98782f66510af4bb68`；artifact 內 `_meta` 載 source SHA 與 generator 版本。diff identity＝`(kind,name)`：added／removed 依 key、changed＝同 key canonical row 不同）。W2B 於 W2A＋W2B merge result 以同指令產同 schema artifact 做 **set diff**——每個 removed／added／changed symbol 逐項 disposition（count 只作摘要，集合與 hash 才是基線）；`--check` 與 33 專測再對 merge result 執行，⛔ 不得只改登記讓綠燈恢復
3. L0 成形：AGENTS／README 指向「canonical 前兩節＋專案心智模型，其餘用查的」，並含決議 §三之二指定句逐字：「**stage-rules/＝八份 SOP，① 印給你、③ 逐條回**」
4. 封閉五檔依 mapping 落地，CI 全綠
**驗證**：pytest 全綠；污染符 grep 零命中；派工包範本可實際產出一份（對 W3′ 的派工試打）。
