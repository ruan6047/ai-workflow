# 衝突 C1–C14・量測與建議（2026-09-04）

> 需求方要求「研究幾輪再給建議」。每條先列量測（兩輪、不同母體或量法、附負控），再列建議。
> 母體：`archive/issues/`（aiwf 112 張，含留言）、`origin/snapshots`（2026-08-19 到 09-03 共 16 天）、`origin/main` git 歷史、GitHub API（cpbl 只讀）。
> 量測由 PM 以腳本直接跑（兩個量測子代理分別停滯與撞額度，零產出）。指令在本 session transcript；數字全部是當次輸出。
> ⛔ 本檔是建議，⛔ 非裁定。

## C1 · 需求站 R1 由誰判

**量**：archive 留言含「R1 前提／R1 不過／前提還」的行 23 行；其中同時提到「需求方」0 行、「PM」0 行。R1 語彙 08-29 才出現，沒有實例可分「誰判過」。第二輪：05 空洞 6——需求方裁定普遍只存在對話，卡上無留言。
**建議**：維持決策 3，**PM 判 R1**，需求方保留否決（撤銷或停止）。理由：把 R1 掛需求方等於每張卡多一個要你出場的點，而你的裁定今天已經是留痕最薄的一環。條文改法：requirement.md 那兩行「R1 由需求方」改成「PM 判 R1；需求方在 ④ 前可撤銷」。

## C2 · blocking finding 與驗收

**量一**（aiwf 193 則結構化裁決：APPROVE 64／RC 129）：APPROVE 且帶 `blocking: true` 的 **1 則**（#24，severity major）；RC 且全部 blocking 皆 minor／low 的 **0 則**。負控：`blocking: true` 全語料 295 次。
**量二**（cpbl 隨機 12 張 🏁完成 卡，15 則裁決：APPROVE 9／RC 6）：APPROVE 帶 blocking **0**，RC 全 minor **0**。
**建議**：兩個 repo 加起來 208 則裁決，「細節 blocking 卻驗收」從未發生。**採簡單版：open blocking ⇒ REQUEST_CHANGES，無例外**（H13）。「細節」由查核者標 `blocking: false` ＋ `disposition: backlog` 表達，不另立驗收特例。ROADMAP:412 那句不進新規則。

## C3 · `gh pr update-branch` 禁令

**量一**（aiwf `origin/main`）：08-13 squash 裁定後 21 個 merge commit，其中 10 個不是 `Merge pull request`；`Merge branch 'main' into …` 在 main 上**存活 4 個**；最近 40 個已合併 PR 裡 #223 分支內有 1 個 merge commit。兩個 repo 的設定 `allow_merge_commit`／`allow_squash_merge`／`allow_rebase_merge` **三者全 true**。
**量二**（cpbl main 最近 100 個 commit）：merge commit 3 個，**全部非 PR**，訊息形如 `merge: <卡ID> … (cross-family review APPROVE, requester-authorized)`——cpbl 刻意用 merge commit 承載查核結論。
**負控**：#244 的 merge commit 有兩個 parent，證明 `%P` 量法會響。
**結論**：squash 政策沒有機械執行者，禁令防的害（synthetic merge 進 main）在 aiwf 真的發生了 4 次；cpbl 則根本不 squash。
**建議**：
1. **H19 砍**，換成 repo 設定：aiwf 關 `allow_merge_commit` 與 `allow_rebase_merge`，只留 squash。設定即執行者，update-branch 產生的 merge 會被 squash 壓掉，禁令失去對象。
2. cpbl 的合併方式是**專案層設定**，不進核心；它要 merge commit 就自己承擔 update-branch 的害。
3. 05#17「已被派審詞引用的 SHA 不得 force-push 覆寫」升為核心規則（K5），執行者＝H11 的「進駐 HEAD 必須等於 source_sha」。

## C4 · PM 自產物誰查

**量一**：archive 提到「第二 PM」的留言 29 則，全在 12 張 REDESIGN 時代的卡（#177 #213 #217 #219–#222 #227 #228 #231 #242 #243）；其中 23 則含收件通過／退回字樣。第二 PM 只判過收件流程（05 空洞 5）。
**量二**：193 則裁決中提到 Codex／gpt 的 71、提到 Claude／Opus 的 56、兩者皆無 66；246 則結構化 finding 的 attribution：coordinator 42＋planner 31＝**73（30%）**。派審留言 99 則，其中 17 則之後同卡沒有任何裁決。
**結論**：PM 側缺陷是第二大宗，而第二 PM 從未查過派審詞或結案報告。
**建議**：**不設第二 PM。查核者查 PM 的產出**，方式是交回單 schema 已有的 `attribution: coordinator／planner`——查核者收到派工單時，派工單本身就在被審範圍（04#41「派審詞就是全部要求」）。清單收件條件 2（是觀察不是結論）由需求方在點頭升級時判，不另設角色。結案報告由需求方 ④ 看，本來就是。

## C5 · 撤銷

**量一**（16 天逐日快照差集）：從板上移除 **1 張**（09-01，`WF-CARD-BODY-BUDGET1-PROBE-DRAFT1`，當時 🛑已停止，是拋棄式探針）。負控：同日自比差集 0。
**量二**：archive 提到 `deleteProjectV2Item` 2 檔、「撤銷」11 檔——談的多、做的零。
**建議**：撤銷是 `move` 的一個 to 值（`move --to 清單`），⛔ 不另立動詞。語意照 S6。

## C6 · 隨模組退場的三個狀態值

**量一**（16 天快照）：`🚨已升級` **0 卡·日**；`🔬研究中` 10 卡·日，單日最多 3 張；部署狀態非 `—不適用` 的卡 34。
**量二**（archive）：「不可判定」出現在 29 檔（討論語境居多）、「運行中」4 檔、「已升級」9 檔，Log 內轉到 🚨已升級 9 行（全在 08-19 之前，快照期內為 0）。負控：🏁完成 最新 128。
**建議**：**核心值域＝待辦／進行中／待確認／完成／退回＋阻塞**。`升級`、`不可判定`、`運行中` 各隨模組存在；CLI 的 choices 由核心＋已啟用模組組出，模組未啟用時該值寫不進去。S4 照此改。

## C7 · 三角色共用操作紀律的居所

**量**：05 反覆失誤表前六名（行號腐爛 11 卡、驗證器出錯 11、宣稱超過證據 10、多居所只修一處 10、逐字轉錄失敗 7、shell 吃字 6）全部是三角色都犯的操作失誤，不屬任一角色。
**建議**：加一份 **`conduct-common.md`**（跨角色操作紀律：實跑、fetch、不截斷、rc、負控、逐字轉錄、多居所一次改完、驗證對原件），`brief` 對每個角色都注入。「一角色一檔」不被破壞：它是第五份、每個角色都讀的那份；「同一條只住一處」成立。

## C8 · 級別表本體與紅線定義住哪

**量**：tier-rules 刻意不放副本、指向 canonical §0；03 萃取把判準句暫住 stage-requirement（03 未驗 #8）。
**建議**：新結構加一個 **`core/`** 目錄放定義檔：`state-machine.md`（階段、狀態值域、轉移表）、`tiers.md`（T0–T4 表、紅線域、能力層級判準）、`card-schema.md`（fenced JSON 欄位集）、`verbs.md`（六動詞語意）。階段檔與角色檔只引用不複製。這就是決策 9「每條規則一句、理由連結 archive」的定義層。

## C9 · `db_scope` 與紅線

**量一**（09-03 快照）：db_scope none 149／read 41／write 19／schema 2／data-migration 1／空 5。write 的級別 T4 12、T3 6、T2 1；schema 與 data-migration **全部 T4**；「schema 或 data-migration 但級別 < T3」**0 張**。
**量二**：`resources` 含 `db:` 的卡 7，db_scope ≥ write 的卡 22，交集 7；**write 以上但無 `db:` 宣告 15 張**（與 08-30 量到的 68% 相同）。
**建議**：`db_scope` 是**核心卡面欄位**（enum 含 none），因為級別推導要讀它；紅線規則住 `core/tiers.md`：「db_scope ∈ {schema, data-migration} ⇒ 至少 T4」。namespace、migration phase、環境別名表、`db:` 資源文法歸**資料庫契約模組**（啟用條件：專案有 DB）。`db:` 宣告覆蓋率差是互斥模組的問題，不是紅線的問題。

## C10 · 硬擋與印的邊界

**建議**：以 00 稿新加的「核心-語意」桶收掉：轉移表、iteration、鏈深、封存是動詞的固定行為，不是拒絕也不是印。剩下的硬擋只有 §二 19 條減 H19 加 K4 K5，共 20 條。

## C11 · 卡面修訂動詞 `edit`

**量一**（archive Log）：`amend` 行 **552**，改過的卡 **96／112**。欄位次數：驗收條件 158、資源宣告 143、核心痛點 129、簡介 123（含一次性回填）、spec 基線 75、非射程 38、級別 23、服務的原始目標 19。
**量二**：body 內 `spec_version` 只在 7 張卡出現、≥2 的 2 張——機制太新，不能當需求證據；量一是主證據。負控：Log 行形狀先讀 3 行確認再寫正則。
**建議**（需求方已裁加 `edit`，此為細節）：
- 可改欄＝fenced JSON 全部欄位，除 `card_id` 與 issue 號。
- 每次 `edit` 在留言追加一筆 `edit <欄> <原值 hash> → <新值 hash>`；⛔ 不進 body。
- 改到規格類欄（驗收、驗證、非射程、資源宣告）⇒ `spec_version` 自動 +1。
- 卡在審核階段時 `edit` 印警示「查核中修卡面，須告知查核者」（05#25），不擋。
- 改核心痛點或級別下修時接受 `--ruling <留言 URL>`；沒給就印「無裁定連結」，不擋（P1）。

## C12 · 對話裁定的留痕

**量**：05 空洞 6——T4 sign-off「只存在對話，卡上無留言」；所有需求方裁定留言都標「撰寫者≠決定者」；05#3 三張卡因裁定沒落卡面被查核退回。
**建議**：**裁定的生效點＝一則 GitHub 留言**。需求方自己貼最好；PM 代貼時留言首行固定 `代貼裁定・授權來源：<session id／時間>`。需要裁定的動作（`move` 到停止或撤銷、`edit` 核心痛點、級別下修、T4 sign-off）都收 `--ruling <留言 URL>` 欄位；缺即印。這條讓「對話裁定」變成可稽核的一行，而不是多一個角色。

## C13 · 拒收留痕

**量**：05#21——互斥拒絕 110 次派工 0 次留痕；05 空洞 2——五個層次的事件型別機器只寫得出兩個。
**建議**：新 CLI 拒收點只剩 §二那 20 條硬擋。**每次硬擋拒收在卡上追加一則留言 `拒收・<閘門>・<原因>`**（一行，不含填空樣板）。印警示不寫留言。這樣效益可觀測，代價是每次拒收一次 API 寫入。

## C14 · 無寫入通道的查核者

**量**：05 空洞 1——一晚十輪裁決約 20 次人工搬運；收據紀律「構造上無法遵守」；193 則裁決中 66 則看不出實體。
**建議**：**裁決＝一則 GitHub 留言，誰貼都可以**。有 shell 的查核者用 `wfcli review` 產交回單並貼；沒 shell 的（人、雲端 Copilot）直接在 GitHub 貼同一格式的留言。狀態轉移由 PM 跑 `move --ruling <該留言 URL>`，PM 不再轉錄內容。這條把 C12、C13、C14 收成同一個機制：**留言是裁決與裁定的載體，URL 是 CLI 唯一要的東西**。

## 第三輪 · 對抗（找會推翻建議的證據）

| # | 想推翻什麼 | 量到什麼 | 對建議的影響 |
|---|---|---|---|
| C2 | 「RC 一定伴隨 blocking」 | RC 且零 `blocking: true` 的裁決 **5／129**（#25 三則為 schema 前的自由文字；#62 `core_pain_resolved: no`；#147 一則） | 建議補一句：REQUEST_CHANGES 的充分條件＝有 open blocking **或** `core_pain_resolved: no`；兩者皆無而退回即無效裁決 |
| C3 | 「已有 ruleset 擋 merge commit」 | aiwf ruleset 只有 `required_status_checks`；cpbl 另有 `main-history-guard`；兩者都沒有 `required_linear_history` | 建議升級：aiwf 在 ruleset 加 `required_linear_history`（bypass 清空，比 repo 設定強），再關 merge／rebase 兩個按鈕 |
| C4 | 「查核者實際不會抓 PM 的問題」 | 裁決內 attribution：executor 162／planner 66／coordinator 51；Codex 裁決裡 coordinator 16＋planner 18＝34／130 | 推翻失敗：跨實體查核者已在抓 PM 側缺陷，機制存在，只是沒有角色名 |
| C6 | 「三個專屬狀態有設計理由不可拆」 | 決議 §三的判準是「換成通用狀態會不會丟失行為差別」——理由綁在各自的階段上 | 推翻失敗：理由隨模組走，模組未啟用時該階段不存在，行為差別也不存在 |
| C11 | 「查核中改卡面很少見」 | `amend` 發生在 🔍待查核 期間的行 **119／550**（上界：狀態機以 Log 行推、裁決行沒對上會黏住），跨 20 張卡 | 建議強化：`edit` 在審核階段⛔ 不只印警示，還在卡上追加一則留言 `edit during review・<欄>`，讓查核者看得到 |
| C12／C14 | 「CLI 驗不了留言 URL」 | `gh api …/issues/comments/<id>` 回 id、author、created_at、長度 | 推翻失敗：URL 可機械驗存在與作者 |
| C13 | 「拒收留痕沒人要」 | 22 檔留言有人手貼 `rc=2`／`拒絕：`，13 行是原樣貼上的拒絕訊息 | 推翻失敗：人已經在手動做這件事，機器做更便宜 |
| C7 | 「共用紀律檔沒有先例」 | Backlog.md 要求每次對話先讀 MANIFESTO；Writ 與 Bernstein 的 reviewer 一律 fresh context、只讀交接文件 | 推翻失敗：外部三套都有「每個角色都讀的那一份」 |

三輪後建議不變的：C1、C5、C8、C9、C10。修正的：C2（加 core_pain 子句）、C3（ruleset 線性歷史）、C11（審核期 edit 留言）。

## 附 · 建議的合併效果

| 收掉的 | 換成 |
|---|---|
| 第二 PM、人工查核兩個角色 | 查核者查 PM 產出（attribution）；需求方裁清單條件 2 |
| H19 update-branch 禁令 | repo 設定只留 squash（aiwf）；cpbl 專案層自選 |
| 三個階段專屬狀態在核心 | 隨模組存在 |
| 撤銷動詞 | `move --to 清單` |
| 轉錄、收據、身分自述的一半 | 裁決與裁定＝留言，CLI 只收 URL |
| 五份交接文件 | 三份＋一份 schema（04） |
| 級別表散在三處 | `core/tiers.md` |

## 未驗

- C2 的 severity／blocking 配對用正則抓，finding 區塊跨行超過 6 行會漏配；負控只證 `blocking: true` 抓得到，不證配對正確。
- C3 沒有量 cpbl 分支內 update-branch 的次數，只看到 main 上 3 個 merge commit 全是刻意的。
- C4 「提到 Codex／Claude」是字面，不是身分驗證。
- C11 的欄位計數對同一行多欄位各計一次；`簡介` 123 次含 08-26 的一次性回填，扣掉後的常態次數未分開量。
- C1 沒有可分「誰判」的實例，建議純依設計推。
- 全部量測沒有第二人複跑。

## 裁定（需求方 2026-09-04）

C1–C14 全部照本檔建議（含第三輪修正的 C2、C3、C11）。C12／C13／C14 作為同一機制實作：裁決與裁定＝GitHub 留言，CLI 動詞只收 `--ruling <URL>` 並驗存在與作者。
