---
name: verbs
when: 跑或實作任一 CLI 動詞、判一次拒收是不是合法、查 notes 合成順序時讀
non_scope: ⛔ 不寫誰在什麼時候該跑（住 roles/、stages/）；⛔ 不寫 schema（住 core/card-schema.md、core/return.md、core/ruling.md）
last_confirmed: 2026-09-07
---

# 七動詞

CLI 提供資訊清單，AI 判斷；CLI 只確認清單有沒有填，⛔ 不做內容判讀（第零條）。動詞集合固定為七個；模組只能宣告旗標；新動詞須需求方裁定。

## 1 · 動詞表

| 動詞 | 輸入 | 硬擋（rc≠0，寫 `wf:reject`） | 印（rc=0） | 寫 |
|---|---|---|---|---|
| `open <issue> [--parent <card_id>] [--area <AREA>]` | 清單項或撤銷卡的 issue 號；父卡ID；AREA（`areas` 只有一值時可省略＝隱含） | 不是清單項也不是撤銷卡、已在板上、JSON 鍵不合法、`--parent` 不存在、缺 `--area` 而 `areas` 多值或 `--area` 不在 `areas`（無法組合法卡ID）（D2、D3、D4） | 缺欄清單（建卡必填欄）、鏈深（>2 印「上限 2」，2026-09-04 種子）、清單項留言數與未讀警示 | 卡面 JSON、Project 五欄、卡ID；撤銷卡復板沿用 `card_id`／`iteration` |
| `move <card> --to <階段/狀態> [--actor <role>:<actor>] [--source-sha SHA] [--ruling URL]` | 目標階段／狀態；派工時 `role:actor`（role 四值）；交回時 source_sha；裁定 URL | 卡面 JSON 解析失敗、轉移不在合成表內、終態出邊、`--actor` 的 role 不在四值、`--source-sha` 不在遠端、已給的 `--ruling` URL 不存在（D3、D1、D4） | 已啟用模組 §0 `adds.move_prints` 列的印項（語意住該模組 §1）；離開需求時建卡必填缺欄（`core/card-schema.md` §2）；進終態前 PR 與分支狀態；缺 `--ruling`（撤銷、阻塞、停止、級別下修、離開審核／待確認）；裁定留言無 `wf-return`／`wf-ruling` 區塊；裁定留言作者；裁定留言不在本卡（URL 所屬 issue ≠ 本卡，印兩張卡ID）；`wf-ruling` 依 kind 的必要鍵缺；離開規劃時 `acceptance` 或 `verification` 空；T4 而 `grilling` 空；T2+ 而 `stage_plan` 缺規劃；`stage_plan` 空（合成表只有需求階段，離不開需求） | 先寫卡面 JSON 的 `stage`／`state`（目標階段／狀態）再回寫 Project 五欄；`owner`／`branch`／`iteration`／`source_sha`／`blocked`；不論來源，進入執行／進行中即 `iteration` +1 且 `source_sha`=null；交回時寫 `--source-sha`；轉移記錄留言 `wf:move`；進終態即關 issue 並封存；已啟用模組 §0 `adds.counters` 列的欄（`move --to */退回` 時 +1，進執行或該模組宣告的離開該計數狀態的轉移時歸零）；進阻塞時寫 `blocked.from` 與 `blocked.ruling`（缺 `--ruling` 則 `ruling`＝null）；`owner` 只在派工邊（`*/待辦→same/進行中`、`*/退回→same/進行中`）由 `--actor` 寫，缺則保留原值並印「未指定 actor」，其他邊⛔ 不動 `owner` |
| `edit <card> --set <欄>=<值> [--ruling URL]` | 欄與值 | JSON 不合法、改 `card_id`／`source_issue`／`stage`／`state`（後兩鍵只由 `move` 寫，D1）、`--set parent=` 指到不存在的卡、`--set source_sha=` 不在遠端、已給的 `--ruling` URL 不存在（D1、D3、D4） | 無裁定連結；卡在審核階段；`--set parent=` 後的鏈深（>2 印「上限 2」，2026-09-04 種子） | JSON；`wf:edit` 留言（欄、原值 hash → 新值 hash）；規格欄變動 ⇒ `spec_version` +1；審核階段另貼 `edit during review` 留言 |
| `notes <card> [--stage <階段>]` | — | 卡面 JSON 解析失敗（D3） | 一份編號清單（§3） | 無 |
| `brief <card> --for executor\|reviewer\|closeout [--requested-by A] [--planned-by A] [--implemented-by A] [--reviewed-by A]…` | 角色；`--for closeout` 的 trailer 值（字面，缺即印缺；`--reviewed-by` 可重複） | 卡面 JSON 解析失敗（D3） | 派工單或裁定單的 CLI 段（`core/dispatch.md`、`core/ruling.md`，含已啟用模組的段）；`--for reviewer` 另印分支頭 ≠ 來源 SHA、來源 SHA 未 push、`merge-tree` 衝突；`--for closeout` 另印 merge SHA 是否 main 祖先、CI 狀態、squash 訊息（標題一行＝卡ID＋`feature`；本文逐字＝被審 SHA 與本 iteration 每則 `wf:verdict` 的來源＋`review_result`；trailer＝末端連續單一區塊，鍵取 P5 允許集合、值全取字面：Requested-by／Planned-by／Implemented-by 取同名旗標、缺旗標印缺；Reviewed-by＝每個 `--reviewed-by` 一行、缺旗標則每則 `wf:verdict` 的留言作者一行（首行⛔ 不讀，§2）；⛔ 不自動 merge）；缺人填段；每段首行 `[來源: <來源>/<檔>#<節> · <name>：<when> · confirmed <日期>]`（`name`、`when` 取該檔 frontmatter），過期（`rule_confirm_days`）標 ⚠️ | 無；stdout 由 PM 貼進留言 |
| `review <card> --file <交回單.json> --role executor\|reviewer` | 本機交回單 JSON | schema 不合法（D3）；executor 而卡面 `branch` null、遠端無該分支或遠端 ref 解析不出 40 碼 commit SHA（D4） | 缺段（全級別 `self_run`、`acceptance`；T2 以上另加 `unverified`、`note_responses`、`out_of_scope`；依 `role` 的段；已啟用模組的交回單段，`core/return.md`）；`note_responses` 的 id 未覆蓋 `notes` 清單、`not_applicable`／`found` 而 text 空、`unverified.reason` 空、模組段內 `不適用`／`發現` 而 text 空；`finding_id` 與本卡既有 `wf-return` 撞號；交回單欄位不一致（`review_result` 對 `findings`，PM 判） | 補 `card_id`／`iteration`／`role`／`source_sha` 後驗 schema——`source_sha` 依 role 取源：reviewer＝卡面 `source_sha`（null 即 schema 不合法，D3）；executor＝卡面 `branch` 在遠端的分支頭，⛔ 不用本機分支頭、⛔ 不用 null 或全零；本機分支頭 ≠ 遠端頭時印、本機 git 狀態取不到時印「未能比對本機分支頭」（rc=0）——貼一則留言，首行依 role：executor＝`wf:return`、reviewer＝`wf:verdict`，帶 `json wf-return`，散文段附 `git log` 的 commit 清單與 `git diff --stat` 的改動面；⛔ 不動狀態、⛔ 不另產生其他留言 |
| `snapshot` | — | 任一卡 JSON 解析失敗（D3；schema 仍從 core 讀，⛔ 不做 §3 合成） | 對帳不等的卡與欄（§2 例外，⛔ 不重寫） | 本機 JSON＋Markdown；含全部 `wf-note` 候選與 `last_cited`（從 `wf-return.note_responses` 推得，不存卡面） |

`move --to 清單`＝撤銷；`move --to 阻塞`＝寫 `blocked.from`；離開阻塞＝回 `blocked.from` 並清 `blocked`。

## 2 · 寫入契約

- D1 轉移在合成表內；終態無出邊；⛔ 無自由文字狀態。
- D2 `open` 只從清單項或撤銷卡，兩者皆不在板上。
- D3 JSON 合法、鍵集合封閉；`card_id`／`source_issue` 建卡後不可改；投影 TEXT 欄超過 `max_bytes`；解析失敗整卡拒，該卡所有動詞不跑。
- D4 `--source-sha` 在遠端存在；`--ruling` URL 存在；`parent` 指到板上存在的卡。
- 檢查先於首次遠端寫入：先純計算並驗證新內容，再開始第一次寫（→ [#023](../archive/issues/023.md)、[#141](../archive/issues/141.md)、[#147](../archive/issues/147.md)、[#148](../archive/issues/148.md)、[#221](../archive/issues/221.md)）。
- 寫入順序＝卡面 JSON → 五個投影欄 → 回讀；回讀不等＝D3 拒收（rc≠0，寫 `wf:reject`）。
- 下一次動詞先對帳卡面 JSON 與五個投影欄；不等＝以卡面 JSON 重寫該欄後續跑並印重寫了哪幾欄，⛔ 不拒收；`snapshot` 例外＝只印不重寫（`modules/snapshot/module.md` §1 唯讀）。
- 每次拒收寫一則 `wf:reject` 留言：一行 `拒收・<D 編號>・<原因>`；印不寫留言。
- 留言 append-only：一次寫入一則；⛔ 不編輯既有留言、⛔ 不開可編輯的日誌留言。
- CLI 只讀三種留言區塊：`wf-return`、`wf-ruling`、`wf-note`；散文與首行不讀。
- CLI ⛔ 不產生統計數字、⛔ 不比對內容同義、⛔ 不判斷該不該。
- 硬擋只落在寫壞資料（D1、D3）與指向不存在（D2、D4）；其餘一律印。
- 缺陷的留痕走狀態面（卡面 JSON 與留言），⛔ 不另開 log。
- 模組欄只由該模組條文指定的動詞寫；`adds.counters` 列的欄⛔ 不由 `edit --set` 改。

## 3 · notes 合成

- 順序＝框架核心 F- → 已啟用模組 F- → 專案 P- → 卡面 `notes` 欄 T-；四個來源累加，下游不改寫上游。
- 專案與卡面只能加嚴：⛔ 不得刪除或改寫上游條目。
- 每條印 `id`、`text`、來源標記；候選（`wf:note` 留言）另列於清單末，標「候選」。
- pitfalls-13 模組啟用時，清單末另印其樣板（樣板內容住該模組 `module.md`）。
- `--stage` 缺省＝卡當前階段。
