---
name: verbs
when: 跑或實作任一 CLI 動詞、判一次拒收是不是合法、查 notes 合成順序時讀
non_scope: ⛔ 不寫誰在什麼時候該跑（住 roles/、stages/）；⛔ 不寫 schema（住 core/card-schema.md、core/handoff.md）
last_confirmed: 2026-09-05
---

# 七動詞

CLI 提供資訊清單，AI 判斷；CLI 只確認清單有沒有填，⛔ 不做內容判讀（第零條）。動詞集合固定為七個；模組只能宣告旗標；新動詞須需求方裁定。

## 1 · 動詞表

| 動詞 | 輸入 | 硬擋（rc≠0，寫 `wf:reject`） | 印（rc=0） | 寫 |
|---|---|---|---|---|
| `open <issue> [--parent <card_id>]` | 清單項或撤銷卡的 issue 號；父卡ID | 不是清單項也不是撤銷卡、已在板上、JSON 鍵不合法、`--parent` 不存在（D2、D3、D4） | 缺欄清單（建卡必填欄）、鏈深（>2 印「上限 2」）、清單項留言數與未讀警示 | 卡面 JSON、Project 五欄、卡ID；撤銷卡復板沿用 `card_id`／`iteration` |
| `move <card> --to <階段/狀態> [--actor A] [--source-sha SHA] [--ruling URL]` | 去向（階段／狀態）；派工時 actor；交回時 source_sha；裁定 URL | 卡面 JSON 解析失敗、轉移不在合成表內、終態出邊、`--source-sha` 不在遠端、已給的 `--ruling` URL 不存在（D3、D1、D4） | 進終態前 PR 與分支狀態；缺 `--ruling`（撤銷、阻塞、停止、級別下修）；裁定留言無 `wf-return`／`wf-ruling` 區塊；裁定留言作者；`wf-ruling` 依 kind 的必要鍵缺；離開規劃時 `acceptance` 或 `verification` 空；T4 而 `grilling` 空；T2+ 而 `stage_plan` 缺規劃 | Project 五欄；`owner`／`branch`／`iteration`／`source_sha`／`blocked`；不論來源，進入執行／進行中即 `iteration` +1 且 `source_sha`=null；交回時寫 `--source-sha`；轉移記錄留言 `wf:move`；進終態即封存 |
| `edit <card> --set <欄>=<值> [--ruling URL]` | 欄與值 | JSON 不合法、改 `card_id` 或 `source_issue`、`--set parent=` 指到不存在的卡、`--set source_sha=` 不在遠端、已給的 `--ruling` URL 不存在（D3、D4） | 無裁定連結；卡在審核階段；`--set parent=` 後的鏈深（>2 印「上限 2」） | JSON；`wf:edit` 留言（欄、原值 hash → 新值 hash）；規格欄變動 ⇒ `spec_version` +1；審核階段另貼 `edit during review` 留言 |
| `notes <card> [--stage <階段>]` | — | 卡面 JSON 解析失敗（D3） | 一份編號清單（§3） | 無 |
| `brief <card> --for executor\|reviewer\|closeout` | 角色 | 卡面 JSON 解析失敗（D3） | 派工單或裁定單的 CLI 段（`core/handoff.md`）；`--for reviewer` 另印分支頭 ≠ 來源 SHA、來源 SHA 未 push、`merge-tree` 衝突；`--for closeout` 另印 merge SHA 是否 main 祖先、CI 狀態；缺人填段；每段首行 `[來源: <來源>/<檔>#<節> · confirmed <日期>]`，過期（`rule_confirm_days`）標 ⚠️ | 無；stdout 由 PM 貼進留言 |
| `review <card> --file <交回單.json> --role executor\|reviewer` | 本機交回單 JSON | schema 不合法（D3） | 缺段（依卡面 `tier`：T2 以上的 `unverified`、`note_responses`、`out_of_scope`，與依 `role` 的段，`core/handoff.md` §2）；`note_responses` 的 id 未覆蓋 `notes` 清單；交回單欄位不一致（`review_result` 對 `findings`，PM 判） | 一則帶 `json wf-return` 的留言；⛔ 不動狀態 |
| `snapshot` | — | 任一卡 JSON 解析失敗（D3） | — | 本機 JSON＋Markdown；含全部 `wf-note` 候選與 `last_cited` |

`move --to 清單`＝撤銷；`move --to 阻塞`＝寫 `blocked.from`；離開阻塞＝回 `blocked.from` 並清 `blocked`。

## 2 · 寫入契約

- D1 轉移在合成表內；終態無出邊；⛔ 無自由文字狀態。
- D2 `open` 只從清單項或撤銷卡，兩者皆不在板上。
- D3 JSON 合法、鍵集合封閉；`card_id`／`source_issue` 建卡後不可改；解析失敗整卡拒，該卡所有動詞不跑。
- D4 `--source-sha` 在遠端存在；`--ruling` URL 存在；`parent` 指到板上存在的卡。
- 檢查先於首次遠端寫入：先純計算並確認新內容符合資料有效性，再開始第一次寫（→ [#023](../archive/issues/023.md)、[#141](../archive/issues/141.md)、[#147](../archive/issues/147.md)、[#148](../archive/issues/148.md)、[#221](../archive/issues/221.md)）。
- 寫入順序＝卡面 JSON → 五個投影欄 → 回讀；回讀不等＝D3 拒收（rc≠0，寫 `wf:reject`）；下一次動詞先對帳。
- 每次拒收寫一則 `wf:reject` 留言：一行 `拒收・<D 編號>・<原因>`；印不寫留言。
- 留言 append-only：一次寫入一則；⛔ 不編輯既有留言、⛔ 不開可編輯的日誌留言。
- CLI 只讀三種留言區塊：`wf-return`、`wf-ruling`、`wf-note`；散文與首行不讀。
- CLI ⛔ 不產生統計數字、⛔ 不比對內容同義、⛔ 不判斷該不該。
- 硬擋只落在寫壞資料（D1、D3）與指向不存在（D2、D4）；其餘一律印。

## 3 · notes 合成

- 順序＝框架核心 F- → 已啟用模組 F- → 專案層 P- → 卡面 `notes` 欄 T-；四個來源累加、不覆寫。
- 專案層與卡面只能加嚴：⛔ 不得移除或改寫上游條目。
- 每條印 `id`、`text`、來源標記；候選（`wf:note` 留言）另列於清單末，標「候選」。
- `--stage` 缺省＝卡當前階段。
