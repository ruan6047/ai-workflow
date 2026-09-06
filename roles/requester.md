---
name: requester
when: 你是出題、裁定、sign-off 的那個人，卡在需求階段、要停止、要降級、要結案確認、或有人請你裁時
non_scope: ⛔ 不寫 PM 怎麼組裁定單（住 core/handoff.md §3）；⛔ 不寫 R1 R2 的判法（住 roles/pm.md）
last_confirmed: 2026-09-05
---

# 需求方

## 1 · 職責

- 決定哪個清單項升級為卡、缺陷開不開卡；⛔ 不代填清單項。
- 填卡面 `service_goal`；PM 判 R1 後保留否決：撤銷或停止。
- 裁定：停止、撤銷、級別下修、進入阻塞、授權缺口擴權或開新卡、升級四選一（換人／退回上一階段／停止／退回無效）、事後查核是否回退 main、T4 sign-off。裁定＝一則 `wf:ruling` 留言（`core/handoff.md` §3）；PM 可代貼。
- 結案：讀裁定單；不否決則 PM 依 `stages/closeout.md` §4 直行；T4 須 sign-off。
- 規劃階段核可取捨與驗收條件；⛔ 不寫規格。
- T4 卡離開規劃前做質詢，紀錄落 `wf:log` 留言。
- 注意事項正式化：候選要升為 P- 或 F- 條目時，確認三格（條文、來源、處理手段）；缺處理手段⛔ 不升。
- 硬擋新增的唯一入口：處理手段屬 recoverable＝irreversible 或平台層事故時才裁定升為平台委託 P-（`core/platform.md`）；預設不升，⛔ 不擴 CLI 硬擋。
- 定期回看：每 `guard_review_period`（`core/params.md`）張結案卡收 PM 一份回看清單（零拒收硬擋、正式化候選、`last_confirmed` 過期的規則檔三類），一則裁定留言處理。
- 確認規則檔的 `last_confirmed`；改規則開一張卡，sensitive 含 rules。

## 2 · 紅線

- 裁定只以留言生效；只存在對話的裁定⛔ 不算，PM 代貼時首行標記授權來源。
- ⛔ 不代填表單、⛔ 不代寫規格、⛔ 不代改執行者的產出。
- 不在場時決策進待審清單；AI 只續做已派的工作。

## 3 · 動作前自檢

- 裁定前讀實際值（卡面 JSON、投影欄、留言），⛔ 不憑印象。
- 停止類裁定含 reason、revive_condition、reversal_handle；阻塞類含 reason、waiting_on、unblock_condition。
- 級別下修前看裁定單列的被繞過的要求。

## 4 · 注意事項

- F-需求方-01：需求表單只寫可觀測現象（「X 指向 Y，但 Y 不存在」），⛔ 不寫解法、⛔ 不寫未量測的因果推論。
- F-需求方-02：finding 存在時⛔ 不因此開卡；依序問是否立刻造成事故 → 服務哪個目標 → 是否與排程衝突再處置。

→ [archive/rules-2026-09/stage-rules/requirement.md](../archive/rules-2026-09/stage-rules/requirement.md)、[archive/rules-2026-09/docs/ROADMAP.md](../archive/rules-2026-09/docs/ROADMAP.md)、[archive/issues/219.md](../archive/issues/219.md)、[archive/issues/147.md](../archive/issues/147.md)
