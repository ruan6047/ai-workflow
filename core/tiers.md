---
name: tiers
when: 開卡定級別、選能力層級、判紅線、判降級、判缺陷級別時讀
non_scope: ⛔ 不寫查核者怎麼審（住 roles/reviewer.md）；⛔ 不列模型名（住專案層）
last_confirmed: 2026-09-05
---

# 級別與紅線

## 1 · 級別表

| 級別 | 最低要求 | 規劃階段 | 查核者獨立性 |
|---|---|---|---|
| T0 | 直推 main；格式與連結自查 | 跳過 | 無 |
| T1 | 直推 main；聚焦自查；⛔ 不改 versioned source、設定、生成物、規格文字 | 跳過 | 無 |
| T2 | 分支＋聚焦回歸測試＋獨立查核 | 必跑 | 不同實體 |
| T3 | T2 加規格與驗收條件、self_run、merge 前 required check | 必跑 | 不同實體 |
| T4 | T3 加跨家族查核或需求方 sign-off、實測證據 | 必跑，離開前附質詢 | 跨家族，或 sign-off |

→ [archive/rules-2026-09/AI_WORKFLOW.md §0 級別表](../archive/rules-2026-09/AI_WORKFLOW.md)。

## 2 · 判準

- 級別＝敏感面／可復原性／影響面三軸各自定級後取最高；⛔ 不取平均、不取多數。
- ⛔ 不以估時、檔案數、工作量、當下額度定級或降級。
- 三軸值域＝卡面 `tier_basis`：sensitive 多選（§3 紅線域）；recoverable＝reversible／rollback_only／irreversible；blast＝file／module／repo／cross_repo。
- irreversible 或 cross_repo ⇒ 至少 T3；sensitive 含任一紅線域 ⇒ 依 §3。
- 混合卡以三軸最高的項定級。

## 3 · 紅線域

sensitive 值域＝public_contract／security／payment／data_write／migration／production／rules／statistics。

- 含 public_contract、security、payment、data_write、production ⇒ 至少 T3。
- 含 migration、rules、statistics ⇒ T4。
- `db_scope ∈ {schema, data-migration}` ⇒ T4，且 sensitive 必含 migration（C9）。
- T4 查核者的獨立性條件＝注意事項，住 `roles/pm.md` §4；級別表的「跨家族，或 sign-off」是形狀。
- 注意事項升為硬擋的唯一入口＝需求方裁定，且處理手段屬不可逆或平台層事故（條文住 `roles/requester.md` §1）；預設不升。

## 4 · 單向門

- 級別升：PM 用 `edit --set tier=` 直接升，⛔ 不需裁定。
- 級別降：須 `--ruling <裁定留言 URL>`（`wf-ruling` kind=tier_change）；缺即印；裁定單列出被繞過的要求。
- 已離開規劃的卡降級後不回頭補跑規劃；補跑與否由需求方在裁定內寫。

## 5 · 缺陷套用表

| 缺陷 | 級別 |
|---|---|
| 已知 typo、文案，無行為影響 | T1 |
| 根因已知、局部、可逆、無紅線 | T2 |
| 根因不明、跨檔、契約／資料／安全影響 | 至少 T3 |
| sensitive 含 statistics | T4 |

⛔ 不因「很小」略過三軸判定。缺陷不配專屬卡種；重現步驟、預期與實際、根因、回歸測試寫進核心痛點與驗收條件。

## 6 · 能力層級

值域＝經濟型／主力型／高階型；卡面寫層級，⛔ 不寫模型名。

| 工作 | 建議 |
|---|---|
| 純文字、格式、狀態同步 | 經濟型；語意會改規則時升主力型 |
| 一般規劃、執行、查核 | 主力型；跨模組、未知根因、含紅線域升高階型 |
| security、payment、statistics、data_write | 高階型＋跨家族查核 |
| 部署與 migration 異常 | 主力型；recoverable＝irreversible 或根因不明升高階型 |

- 先依風險定層級，再挑實際跑的模型名（住專案層）；高能力層級不取代測試、平台委託、獨立查核。
- 派工實際層級低於卡面建議時，派工單寫偏離理由。

## 7 · 專案層

- 專案層檔 `.wf/tiers.md` 只能加嚴：宣告某類工作至少 Tn、或在某級之上加要求。
- ⛔ 不下修最低要求、不新增比 T0 弱的級別、不改判框架 T3／T4 更低、不自創級別代號。
- 沒有 `.wf/tiers.md`＝沒有加嚴。加嚴的數字由專案填；框架不給預設（2026-09-05 未定）。
