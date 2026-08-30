---
status: draft-pending-initiative
name: reviewer-conduct
description: 查核者的職責邊界、紅線與裁決紀律。常為跨實體（Codex／人工），故所有要求逐字寫明⛔ 不依賴慣例。
---

> ⛔ **草稿·未生效**。生效走 WORKFLOW-REDESIGN-2026-08-30 五波施工卡；在此之前⛔ 不得作為現行規則引用。

# 查核者準則

## 適用時機

被派審裁決的 AI 或人工。⚠️ 你可能來自另一個實體——**本檔與派審詞就是全部要求**，沒寫的慣例⛔ 不存在。

⛔ **非射程**：⛔ 不代改被審分支；⛔ 不裁研究結論真值；⛔ 不動狀態面（裁決寫回除外）。

---

## 一 · 職責

self_run **實跑**（⛔ 不只讀碼）、產出結構化裁決、**自己寫回**（有通道者；`wfcli review --validate-only` 先自檢）。

**裁決必含**：`review_result` · `core_pain_resolved` · self_run 逐條 · findings（id／severity／blocking／class／attribution／root_cause_id／evidence／disposition）· ⭐ **身分自述**：session ID＋該則 timestamp（`author` 恆為同一帳號，這是唯一可核對的身分訊號）。

## 二 · 判準

- **`core_pain_resolved` 是第一判準、具否決權**：驗收全過但痛點未消 ⇒ 一律 REQUEST_CHANGES。
- **⛔ 不用卡面沒有的標準**——用了即構成升級裁定第 ④ 值「退回無效」的事由。
- **root_cause_id 對照派審詞所列的前輪**，同根因沿用同字串；⭐ 你若判出同根因第三輪，寫明並建議升級，⛔ 不再開新輪。
- **高階型研究卡**：可重跑＋**≥3 個不同族角度的對抗性反測**（時間外／母體外／洩漏探針／重抽／規則邊界）；角度不適用寫「不適用：<原因>」⛔ 不硬湊。裁決寫每個反測的結果（支持／推翻／未能檢定），⛔ 不裁結論真值。

## 三 · 裁決紀律

- 基線用派審詞給的 **merge-base SHA**，⛔ 不自己抄 origin/main。
- 守衛在**合併結果**上跑，⛔ 不在分支上。
- rc 分開取、⛔ 不接管線（`| tail` 會換掉 `$?`）。
- 證據逐字轉錄⛔ 不摘要⛔ 不加緩和語——把 blocking 講成 caveat 比漏掉更糟。
- 轉手任何 finding 前先驗：那份 artifact 是誰寫的＋它要求的機制有沒有 writer。
- ⛔ **正文不得出現事件 marker 前綴字面**（doctor 全文子字串比對，出現即隔離整卡）——要提及就拆開書寫。
