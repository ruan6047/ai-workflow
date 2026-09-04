# #30 WF-MARKER-SCOPE-CLEARANCE1 受管轄判準收窄為宣告行 ＋ clearance 的留言平面表示法與 writer
- state: open  created: 2026-08-11T16:16:58Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/30
- comments: 1

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
- 執行：待指派　查核：跨家族查核（契約消費端，須走 PR）
- Initiative：—　spec 基線：自 ai-workflow#16 切出（需求方 2026-08-12 裁定）。基準內容＝#16 設計文件 §3.2（受管轄判準的收窄，Q8）與 §3.3（停機解除：clearance_decision）於 SHA 2d361303ce438c6fecf475b2aaa1fcbc06518dc9 的狀態。已機械驗證 §3.2 區段在 2d36130／0e0d39b／168e433／ba04209 四個 SHA 上位元組完全相同，故基線無漂移。#16 縮為框架卡後只保留「狀態機假設裁決留言可被辨識」，機制本體歸本卡。⚠️ 本卡有兩個前置：cli/src/wf_cli/doctor.py 由 WF-CLEANUP-GUARD1 持有至其結案為止；cli/src/wf_cli/cli.py 與 WF-22-CLI4 的新動詞相交。兩者皆須先後派工，不得以縮小宣告規避。
- DB：db_scope=none
- 服務的原始目標：讓「這則留言是不是裁決」有一個可機械判定且不誤傷散文的判準，並讓已停機的卡有一條可稽核的解除路徑。

## 簡介
<!-- card-brief:begin -->
把 doctor 的事件 marker 受管轄判準從全文子字串比對收窄為全函數三分類（宣告行完整／畸形以行首是否起始宣告判定，行內引用視為散文不觸發停機，三類互斥且窮盡），並補 clearance 的留言平面表示法與新 wfcli writer，讓已停機的卡有一條可稽核的解除路徑。**適用時機**：留言只是提到 marker 字樣就把整張卡打成 marker_quarantined（aiwf#15／#17／#21 三張因此無法自動對帳）時；或真正壞掉的 marker 找不到解除路徑時。⛔ 非射程：只補表示法、不改 review-escalation.md §5 既有的消費端語意（雙欄相符、hash 變動即重新停機、forged-rejected 不自動解除）；doctor.py 由 WF-CLEANUP-GUARD1 持有至其結案、cli.py 與 aiwf#9 相交，須先後派工。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：doctor 以全文子字串比對事件 marker 前綴，任何留言只要提到該字樣就隔離整張卡。#15／#17／#21 三張裁決完整、三面一致的卡因此無法自動對帳；而真正壞掉的 marker 又無解除路徑（CONSUMER_CONFORMANCE 落差 7：clearance 只有事件欄位，沒有留言平面表示法、沒有 writer），形成兩頭都不能動的死鎖。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/doctor.py",
    "file:cli/src/wf_cli/commands/doctor_cmd.py",
    "file:cli/src/wf_cli/commands/clearance_cmd.py",
    "file:cli/src/wf_cli/cli.py",
    "file:cli/tests/test_doctor.py",
    "file:cli/tests/test_clearance.py",
    "file:docs/CONSUMER_CONFORMANCE.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 受管轄判準收窄為 §3.2.1 的全函數三分類：宣告行（完整／畸形）以行首是否起始宣告判定，行內引用視為散文不觸發停機。三類必須互斥且窮盡。
- [ ] 以 #15、#17、#21 三張真實卡為回歸語料：收窄後皆不得再回 marker_quarantined，且各自的三面一致判定須與人工核對結果相符。
- [ ] 仍須停機的情形一項不得漏：首行畸形、非首行的完整 marker、任何位置的畸形宣告行、同 attempt 跨留言重複。
- [ ] clearance 的留言平面表示法：首行 marker 承載識別、fenced 區塊承載全欄位；clearance marker 適用與事件 marker 相同的三分類。
- [ ] clearance writer 為新 wfcli 動詞；消費端判定沿用 review-escalation.md §5 既有規則（雙欄相符、hash 變動即重新停機、forged-rejected 不自動解除、分類與 author 事實不符即無效），本卡只補表示法不改其語意。
- [ ] CONSUMER_CONFORMANCE.md 落差 7 與其連帶敘述須同步更新，不得留下已解決卻仍標為仍缺的條目。

## 驗證

- [ ] 三分類以窮舉或性質測試證明互斥且窮盡，不得以列舉案例代替；且須有突變驗證證明斷言非空。
- [ ] #15／#17／#21 三張真實卡的收窄前後對照，逐張列出判定變化與理由。
- [ ] clearance 的五種 clearance_decision 各至少一條測試，含 forged-rejected 不解除停機、repaired-verified 缺前一筆有效 clearance 時無效。
- [ ] 不得引入任何會使停機被靜默解除的路徑；反向測試須證明繞道被擋。
## Log

- 2026-08-12T00:16:56+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-26T22:15:40+08:00 amend by wf-cli（op 4405b2b4）→ 簡介：原值「（原本沒有）」→ 新值「把 doctor 的事件 marker 受管轄判準從全文子字串比對收窄為全函數三分類（宣告行完整／畸形以行首是否起始宣告判定，行內引用視為散文不觸發停機，三類互斥且窮盡），並補 clearance 的留言平面表示法與新 wfcli writer，讓已停機的卡有一條可稽核的解除路徑。**適用時機**：留言只是提到 marker 字樣就把整張卡打成 marker_quarantined（aiwf#15／#17／#21 三張因此無法自動對帳）時；或真正壞掉的 marker 找不到解除路徑時。⛔ 非射程：只補表示法、不改 review-escalation.md §5 既有的消費端語意（雙欄相符、hash 變動即重新停機、forged-rejected 不自動解除）；doctor.py 由 WF-CLEANUP-GUARD1 持有至其結案、cli.py 與 aiwf#9 相交，須先後派工。」（⚠️ 全文：totalCount=0（首寫，平台無前一版））；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。
- 2026-08-29T14:57:00+08:00 handoff by wf-cli → owner 待指派；iteration 0；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 阻塞登記（來源狀態 📥Backlog）：https://github.com/ruan6047/ai-workflow/issues/30 之阻塞留言。解除條件＝待審清單機制上線。。


## Comment 5460927998 · 2026-08-29T06:55:44Z

## 阻塞登記

**狀態**：⏸阻塞。**來源狀態：📥Backlog**（解除時回到此狀態）。

**阻塞原因**：需求方於 2026-08-29 決定，在階段狀態重整（8 階段 × 10 狀態、待審清單、CLI 射程收斂）定案並落地前，暫停所有 ai-workflow 流程卡，避免它們與重構討論互相干擾。

**可證偽的解除條件**：待審清單機制上線（label ＋ issue template ＋ 可見分組）。屆時本卡改列為清單參考項，或依當時前提是否仍成立重新排程。

**本次未做**：核心痛點、驗收條件、射程一律未動。`iteration` 未遞增。`階段` 欄未寫入。本登記僅改交付狀態與 owner。

**已知的射程重疊**（供解除時參考，非本次裁定）：#66／#38 的實質可能由「七份交接文件格式」承接；#128 可能由「待審清單收件條件三·查重留痕」＋`open --from-issue` 承接；#11 的證據紀律已部分寫入 PM 準則但痛點（靠人記得）未消失。⛔ 上述皆未經裁定，解除時須逐張重驗。

**裁定者**：需求方 ruan6047，2026-08-29 本 session 對話中指示「把目前所有 WF 卡片暫停，避免干擾目前重構討論」。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

