---
name: stat-redline
when: 卡面 tier_basis.sensitive 含 statistics：統計／ML／資料正確性
non_scope: ⛔ 不寫研究階段本身（住 modules/research）
last_confirmed: 2026-09-05
---

# 模組 stat-redline

## 0 · 宣告區塊

唯一啟用條件＝`enable_when`（一個 predicate；事實來源＝`fact_source`）；未啟用時下列每一項都不存在。宣告以 YAML 的 JSON 子集書寫，CLI 與 CI 以 JSON 讀。

```yaml wf-module
{
  "name": "stat-redline",
  "enable_when": "statistics ∈ 卡面 tier_basis.sensitive",
  "fact_source": "卡面 JSON",
  "adds": {
    "fields": [],
    "stages": [],
    "states": [],
    "transitions": {
      "add": [],
      "remove": []
    },
    "flags": [],
    "notes": [],
    "handoff_sections": [
      "紅線區塊（本卡的窗口與門檻）",
      "對抗性反測表（≥3 角度，各寫支持／推翻／未能檢定）"
    ]
  },
  "project_inputs": [],
  "params": {}
}
```

## 1 · 條文

- 在卡面規格欄列「紅線（違反即退回）」區塊；每條從下表取用並具體化為本卡的數字、窗口與門檻，⛔ 不照抄泛用句。
- 對統計結論⛔ 不套「先跑紅」（`stages/implementation.md` F-執行-02）；等價防線＝紅線區塊＋查核者重跑。
- 查核者逐條核對紅線區塊，任一違反即 REQUEST_CHANGES；⛔ 不以「接近門檻」放行。
- 執行者在 `self_run` 列可重跑的驗證指令（隨機種子固定、環境標註）。
- 查核者至少重跑一個保留驗證集。
- 卡的 `stage_plan` 含研究且能力層級為高階型時，查核者用交回的指令跑 ≥3 個不同族角度的對抗性反測（時間外／母體外／洩漏探針／重抽／規則邊界），在裁決的對抗性反測表逐角度寫支持／推翻／未能檢定（§0）；不含研究的卡⛔ 不要求。

| # | 紅線 | 防的失效模式 |
|---|---|---|
| 1 | 訓練／驗證嚴格時間分離；嵌套窗口（基礎模型窗、調參／校準窗、驗證期）全部早於驗證期 | 時間洩漏 |
| 2 | 擬合對象明示 in-sample 或 out-of-sample；偏差剖面不同時⛔ 不混用 | 用錯誤差來源學修正 |
| 3 | 特徵只用 target 時點前可得資訊；逐筆 running state 在套用該筆結果前計算 | 特徵洩漏 |
| 4 | 判定門檻在看到驗證結果前固定；修訂門檻完整留痕理由 | 事後放寬門檻 |
| 5 | 模型／超參／校準器選型⛔ 不以驗證期表現挑選；以訓練窗內指標定案 | 選型洩漏 |
| 6 | 與最簡單基準並排對照；新結果劣於基準 ⛔ 不採用 | 沒學到東西卻上線 |
| 7 | 小樣本子群只列揭露、⛔ 不作支持證據；分組樣本數下限明示；整個子群樣本不足時，落差已由樣本數解釋，判「樣本不足以判定」，⛔ 不判不符合、不需再作第 10 條的個案查證；判定詞彙須能表達「樣本不足以判定」 | 把「測不了」壓成「測了，不準」 |
| 8 | 驗證指令可重跑（隨機種子固定、環境標註）；查核者至少重跑一個保留驗證集 | 不可重現的宣稱 |
| 9 | 母體隨資料新增而變動是正常狀態；母體數字標資料截止時點，⛔ 不設法凍結數字、⛔ 不把漂移讀成缺陷；因管線落後或母體增長（而非模型性質）而失敗或翻面的判定記「不具證據等級」，⛔ 不記為模型失敗證據 | 把母體漂移讀成缺陷 |
| 10 | 少數幾筆與其他差異過大時先個案查證是 (a) 資料錯誤、(b) 未考慮到的特殊情況、(c) 本來就資料缺失，查證管道＝官方紀錄、新聞定性佐證（數值以官方為權威）、人工審核；查證前⛔ 不判整體錯誤或不符合 | 拿離群個案當整體證據 |

## 2 · 注意事項

- F-stat-redline-01：紅線區塊缺席、或條目停在泛用句未綁定本卡窗口與門檻，本身即 REQUEST_CHANGES 事由。
- F-stat-redline-02：反測角度不適用時寫「不適用：<原因>」，⛔ 不硬湊。
- F-stat-redline-03：⛔ 不把單一小樣本季當失敗證據而略過全期合併結果（cpbl-analytics#98 VAL1 反例，2026-08-07）。

→ [archive/rules-2026-09/templates/statistical-redline.md](../../archive/rules-2026-09/templates/statistical-redline.md)、[archive/rules-2026-09/stage-rules/research.md](../../archive/rules-2026-09/stage-rules/research.md)、[archive/rules-2026-09/stage-rules/reviewer-conduct.md](../../archive/rules-2026-09/stage-rules/reviewer-conduct.md)
