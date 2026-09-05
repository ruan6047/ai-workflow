---
name: requirement
when: 卡在需求階段：從清單項升級成卡、填卡面判準欄、決定階段計畫與級別
non_scope: ⛔ 不寫規格與驗收條件怎麼寫（住 stages/planning.md）；⛔ 不寫收件表單的欄位（住 core/card-schema.md §3）
last_confirmed: 2026-09-05
---

# 需求階段

## 1 · 目標與產出

- 產出＝一張卡：核心痛點、非射程、服務的原始目標、`feature`、`when`、階段計畫、級別與三軸、能力層級、`db_scope`、資源宣告、清單收斂宣告全部填實。
- 交回物是卡面文字，⛔ 不是成品。
- 缺陷走同一階段、同一卡面：重現步驟、預期與實際、根因、回歸測試寫進核心痛點與驗收條件。

## 2 · 進入／離開條件

- 進入＝需求方點頭升級的清單項經 `open` 上板（`core/verbs.md`）；缺陷開不開卡由需求方決定，直接 commit 是不開卡時的合法路徑。
- 離開＝`move` 印的建卡必填缺欄為空、PM 判 R1 R2 過、需求方未否決；T2 以上下一階段必含規劃，缺規劃由 `move` 印。
- 撤銷＝`move --to 清單`，卡ID 保留、iteration 延續；可判「現在不做」走撤銷，⛔ 不走停止。
- 注意事項候選要升為 P- 或 F- 條目的提案形狀＝三格：條文、來源（留言 URL）、處理手段；缺一格不提。

## 3 · 狀態 delta

- 無；核心值與轉移依 `core/state-machine.md`。

## 4 · 階段內迴圈

- ① `notes --stage 需求` ② PM `brief --for executor` 派填表 ③ 執行者交回卡面文字 ④ PM 判缺欄、R1 痛點還成立嗎、R2 射程 ⑤ `move` 到下一階段／退回／撤銷。
- 級別＝三軸各自定級後取最高（`core/tiers.md` §2）；級別依據三格填在 `tier_basis`。

## 5 · 各角色做／⛔ 不做

- 需求方：決定升級、填 `service_goal`、判痛點還成立嗎；⛔ 不代填表單。
- PM：跑 `open`、填 PM 欄、判缺欄與 R1 R2、收斂清單；⛔ 不判該不該做。
- 執行者：提供卡面散文素材（觀察、出處）；⛔ 不落欄、⛔ 不寫解法、⛔ 不配卡ID。
- 查核者：不在本階段。

## 6 · 注意事項

- F-需求-01：核心痛點從清單項逐字帶入，⛔ 不重打。
- F-需求-02：開卡前讀清單項全部留言，⛔ 不只讀 body。
- F-需求-03：開卡前三問：服務哪個目標、執行者是誰、現在有人受害嗎。
- F-需求-04：一根問題一張卡；開新卡僅限需要不同能力域的執行者、紅線隔離、寫入集不相交可真平行三情形。
- F-需求-05：鏈深沿父鏈算，>2（2026-09-04 種子）只印；全域問題脫鏈獨立運行，⛔ 不入鏈。
- F-需求-06：待審清單不佔投影欄、不進盤點分母；清單當墓地可接受。
- F-需求-07：高複雜或影響大的卡把研究列進階段計畫；交付物是排程、爬蟲、告警等外部觸發時列維護；純文件卡⛔ 不列部署。

→ [archive/rules-2026-09/stage-rules/requirement.md](../archive/rules-2026-09/stage-rules/requirement.md)、[archive/rules-2026-09/stage-rules/list-intake-requirements.md](../archive/rules-2026-09/stage-rules/list-intake-requirements.md)、[archive/rules-2026-09/stage-rules/defect-path.md](../archive/rules-2026-09/stage-rules/defect-path.md)
