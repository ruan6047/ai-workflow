---
name: conduct-common
when: 任何角色在跑指令、量測、轉錄、寫規則或交接文件之前
non_scope: ⛔ 不寫某一角色專屬的職責與紅線（住各角色檔）
last_confirmed: 2026-09-05
---

# 共用紀律

## 1 · 操作紀律

- 實跑，⛔ 不讀碼推論；⛔ 不把警示文字當分類結果、⛔ 不把 docstring 當實際輸出；「看起來像缺陷」先讀就地註解是否寫著刻意。
- 開工與量測前先 `git fetch`；量在 `origin/main`，⛔ 不在本機工作樹。
- 輸出不截斷；`rc` 先存變數再印，stdout／stderr／rc 三者分開落檔；⛔ 不接 `| tail`；zsh 傳含反引號的字串用引號界定的 heredoc。
- `rc=0` 不等於成功；判成敗看被改變的狀態，宣告成功前先核那次執行的識別碼。
- 引用零命中、零失敗或做複驗前，先用會響的樣本證明工具有效，附負控輸出；變異與負控選最可能打穿的形狀，只跑正向是零資訊。
- 驗證器先於被測物受懷疑：三處變異印同一則訊息＝變異沒生效；算術上不可能的結果最先響；驗證對原件，⛔ 不對經任何一層加工的字串。
- 更正任何事實前先 grep 出它的全部居所，一次改完。
- 登記不是處置：自己登記過的缺口⛔ 不因「登記了」而免修；跑一部分⛔ 不當全部，封存、收尾、合併前跑全套並用 repo 宣告的工具鏈。
- 同一卡同一時間只有一個所有者，交接完成前非所有者⛔ 不動卡、分支、worktree；跨卡協調、射程變更、優先序調整一律經需求方或 PM。
- 狀態面不可用時狀態操作暫停；⛔ 不改用聊天、本機檔案或記憶暫代，已派工作續作，轉移於恢復後補寫；UI 手改投影欄、T2 以上直推 main 同屬違反本紀律。
- 需要等待時前景輪詢或不結束回合；射程外發現只寫進交回單的射程外發現段，⛔ 不開卡、⛔ 不 spawn 背景任務。

→ [archive/rules-2026-09/stage-rules/executor-conduct.md](../archive/rules-2026-09/stage-rules/executor-conduct.md)、[archive/issues/161.md](../archive/issues/161.md)、[archive/issues/219.md](../archive/issues/219.md)、[archive/issues/221.md](../archive/issues/221.md)

## 2 · 書寫紀律

- 引用裁定或規則逐字；⛔ 不節略、⛔ 不把選言轉述成禁令、⛔ 不改變其所述事實狀態。
- 轉錄失誤登記、未驗清單、證據與他人自陳逐字；⛔ 不摘要、⛔ 不加緩和語、⛔ 不升級措辭。
- 數字帶日期或指令；⛔ 不寫現況數字，只留閾值、封閉集合基數、已釘 SHA 的基線。
- 文件與碼的引用⛔ 不寫行號；用檔名＋符號或節次＋逐字片段。
- 交付物寫事實⛔ 不寫可變狀態；SHA 用 `git rev-parse` 取；「已 push」類狀態寫查詢方法。
- 完整性宣稱（全部、全數、零例外）由指令輸出產生，與提交的 artifact 出自同一次執行。
- 刻意行為就地留註解（刻意／為什麼／不得推出什麼），寫在 commit 訊息不算；無則逐字寫「無」，⛔ 不留空；正文用詞依 `core/glossary.md`，用到禁用同義詞＝查核者列一條 `governance` finding，⛔ 不擋。
- ⛔ 不寫看起來在驗證身分、實際恆真的條文；身分只做宣告欄位＋完整性檢查。
- 發現候選注意事項即在該卡貼一則 `wf:note`（`origin`＝來源 finding 留言 URL）；⛔ 不直接寫進規則檔。
- commit trailer 約定：T0／T1 至少 `Requested-by`＋`Implemented-by`；T2 以上加 `Planned-by`；merge 與核可 commit 加 `Reviewed-by`；未開卡的缺陷修正至少帶前兩鍵（CI 只驗鍵與連續，`core/platform.md` P5）。
- 代貼他人裁定或裁決時首行標記依 `core/naming.md` §3；原文從第二行起一字不改。

→ [archive/rules-2026-09/stage-rules/pm-conduct.md](../archive/rules-2026-09/stage-rules/pm-conduct.md)、[archive/issues/037.md](../archive/issues/037.md)、[archive/issues/150.md](../archive/issues/150.md)
