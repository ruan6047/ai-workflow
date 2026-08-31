---
name: workflow-redesign-initiative-brief
status: draft-pending-initiative
description: 四波五卡施工 Initiative 的 discovery brief（WF-19 形式；切換另 Initiative）。開卡時逐字沿用。
---
> ⛔ **草稿·未生效**。父卡開卡時以本檔為 discovery brief；spec 基線＝合入本檔的 main commit SHA。

# WF 重整施工 Initiative — Discovery Brief

## 痛點原文（需求方，2026-08-29 session `cc0a7952-…`）

「明明是為了流程順暢 現在卻卡了一個月」「現在是不是又無限開卡了」「目前框架內ＣＬＩ有點過量尤其是很多不該由ＣＬＩ處理的都變成由ＣＬＩ處裡」

**量化佐證**：開卡 5.2 張/日 ＞ 狀態推進 3.9 次/日（快照 10 日差分）；在動的卡恆 0–5 張；審核 APPROVE 105 : REQUEST_CHANGES 150；一天四張同族卡（開卡產生器）；階段欄 88.6% 空；CLI 26 天 17,194 行、fix 47 > feat 38、refactor 4。

## 服務的原始目標

可稽核＋防低級事故＋**流程順暢**（第三項為本次新增的並列目標——前兩項不得以犧牲它的方式達成）。

## 對抗式質詢（WF-19；本 Initiative 的質詢＝兩日共同設計全程，逐題留痕於決議紀錄）

**被推翻的前提**（修正問題陳述）：
- 「SINGLE_SELECT 選項改不掉」→ updateProjectV2Field 可改可刪 ⇒ 遷移走丙（改名＋換選項）
- 「Codex 查核者無寫入通道」→ trusted＋keyring gh ⇒ 跨實體自寫回，轉錄環節消失
- 「部署狀態是正交軸」→ 7 值全部映射到通用狀態 ⇒ 退位成記錄
- 「留 scratchpad 等施工」→ /private/tmp 重開機即滅 ⇒ 先入庫（bf267aa）
- 「逐次合併授權有守門價值」→ 實測 5/5 照准、0 攔截 ⇒ 零資訊檢查，改結案報告閘
- 「git spec 檔可當基線錨」→ 57 份零讀者、活卡三抽三漂移 ⇒ 甲′ 卡面單一居所

**存活的反駁（＝待驗證假設）**：
- 觀察者效應（PM 知道需求方會看而更誠實）無法量測——結案報告閘是對它的下注，回顧點驗（觸發＝cutover 後第 30 張常態卡結案；fail-safe＝2026-10-31）
- 「§0 重寫會變短」是推測；「card.py 砍半」是估計
- PM 對照能否穩定抓住值域錯誤（取代 CLI 硬拒後）——無基線，施工期觀察
- userContentEdits 長期保存未文件化——每日 snapshot 補規格節為對沖
- 刪「有值」SINGLE_SELECT 選項的行為未實測——切換 Initiative 前置拋棄式 project 實測

## 非目標（⛔）

CLI 增量依決議 §七原則（動詞新增須需求方裁定、其餘走三層評估、⛔ 不無限膨脹）；不批次補寫舊停卡的復活條件；不寫部署／維護階段內容（留空槽）；⛔ 本 Initiative 不碰 cpbl（乙′ 解耦；舊卡與移植歸切換 Initiative）；不引入 Gherkin／Repository 層（既有定案）；不做全域轉移表（delta 制）；不為個別卡修通則。

## 拆卡定稿（乙′ 解耦：四波五卡，全 aiwf、零不可逆；硬依賴 W0→W1→W2A→W2B→W3′）

| 卡 | 內容 | 級別 | 配置 |
|---|---|---|---|
| W0 | conduct×3＋intake 生效（sign-off 審） | T4 | 執行⛔ PM 不可兼 |
| W1 | 清單＋open --from-issue＋表單 | T3 | 獨立查核 |
| W2A | canonical＋stage-rules＋tier-rules（規則類整套） | T4 紅線 | 跨家族（Codex） |
| W2B | 交接範本（含 contract templates）／L0／舊模板清理 | T3 | 獨立查核；需求方閘門 |
| W3′ | CLI 內部：Log→留言（7 persistent sinks＝open 1＋append 6）／fenced JSON／doctor 抽出／37 則訊息／find_conflicts／snapshot | T3 | 獨立查核 |

**⛔ 不在本 Initiative**：看板切換（改名／選項／封存）、P1-20 rehearsal 與 forward-repair、cpbl 全部（9 檔／stub／別名副本／submodule bump／原 W4 舊卡）——移交**切換 Initiative**（決議 §十之二），本卡結案條件含其清單項建立。回顧觸發錨於切換；fail-safe 2026-10-31 不變。

## 污染防治

決議紀錄 §一 取代清單＋§二 污染符封閉集合；派工包定閱讀清單；查核 grep diff；波 2 刪⛔ 不留。

## 立即生效（純流程，⛔ 不等波）

丙 直行授權＋結案報告閘／交付報告缺席＝③ 未完成／高階型三反測／信封（含模型行）／轉移記錄手寫進留言。
