# 萃取 04 · templates/ 與 docs 入口文件

> 母體：`templates/` 全部 16 份、`docs/ROADMAP.md`、`docs/CONSUMER_CONFORMANCE.md`、`ADOPTION.md`、`AGENTS.md`、`README.md`（逐行讀）；`docs/` 其餘 9 份設計文件只讀檔頭 30 行判定處置。
> 行號全部來自 `cat -n` 實讀；行數來自 `wc -l`。
> 桶名逐字：`核心-硬擋`／`核心-印`／`範本欄位（人填）`／`範本欄位（CLI 填）`／`模組(名稱)`／`砍`。模組名不在既定八個之內者加 ※，並在「空洞」節登記。
> 分桶規則沒有給「角色行為準則」（誰不得做什麼）一桶；本檔把它們歸 `核心-印`——brief 印出、CLI 只查 from／to 欄有沒有填，不判內容。

## 規則

| # | 規則（一句祈使句） | 來源 `檔名:行號` | 來歷事故（有寫才填） | 桶 | 一句理由 |
|---|---|---|---|---|---|
| 1 | 派工由需求方決策、PM 機械寫入；任何 session 不得自行派工 | dispatch-package.md:3 | | 核心-印 | 角色歸屬無平台執行者；brief 印 from／to |
| 2 | 鏈深 > 2 不得派工，須整鏈重審 | dispatch-package.md:12 | | 核心-印 | 鏈深由卡面 JSON 父卡欄推得，CLI 印出；是否重審是需求方判斷 |
| 3 | 核心痛點逐字帶入每份交接文件，作查核第一判準的錨 | dispatch-package.md:13; delivery-report.md:12; review-dispatch.md:14 | | 範本欄位（CLI 填） | 卡面 JSON 有此欄 |
| 4 | 資源宣告（file:／port:／container:／db:）逐條寫入集，含交付必要的重現工具 | dispatch-package.md:15 | | 模組(資源互斥檢查與 worktree 註冊) | 單線作業無互斥對象 |
| 5 | 信封含「實際模型／卡面建議／偏離理由」一行；相符時填「相符」 | dispatch-package.md:16; handoff-contract.md:244-249 | | 範本欄位（人填） | 建議由 CLI 抄卡面；實際與偏離理由只有撰寫者知道 |
| 6 | 撰寫者自述 GitHub 帳號、session ID、該則訊息定位 | dispatch-package.md:20-22; verdict.md:20-23 | review-dispatch.md:3（2026-08-29 換實體查核，session ID 當場掉了） | 模組(身分自述) | 已定為模組 |
| 7 | 驗證指令 rc 分開取，⛔ 不接管線 | dispatch-package.md:27; review-prompt.md:43 | dispatch-package.md:29（同族三犯，指向 pm-conduct 四） | 核心-印 | `\| tail` 換掉 `$?`；shell 用法 CLI 擋不到 |
| 8 | 完整性宣稱一律由指令輸出產生；「全部／全數」附窮舉證據 | dispatch-package.md:28; delivery-report.md:33 | | 核心-印 | 內容真偽 CLI 不判 |
| 9 | 回報「已寫入」前看全文輸出，stderr 併入後不截斷 | dispatch-package.md:29 | 同 #7 | 砍 | 描述舊 `wfcli` 拒絕訊息走 stderr 的行為；原則已在 #7 |
| 10 | 已知未驗項逐項＋原因，三分類擇一（驗不了／沒去驗／刻意不驗），⛔ 不裸列 | dispatch-package.md:33-37; handoff-contract.md:242 | review-dispatch.md:40（連續八輪裸列，2026-08-31 修正） | 範本欄位（人填） | 分類是判斷；CLI 只查每列分類值在值域內 |
| 11 | 從 `origin/main` 以完整 40 碼 SHA 建 worktree，實際路徑＋分支寫回卡面 | dispatch-package.md:43-44; worktree-lifecycle.md:5 | | 模組(資源互斥檢查與 worktree 註冊) | 已定為模組 |
| 12 | 寫入授權逐條列出，其餘唯讀；動到唯讀即越界，停下寫阻塞發現 | dispatch-package.md:45-46 | | 範本欄位（人填） | 授權範圍是 PM 判斷；越界可由 diff 對照印出 |
| 13 | 規格權威居所＝卡面 body，⛔ 不是草稿檔 | dispatch-package.md:50; template-migration-map.md:13 | | 核心-印 | 新 CLI 只讀卡面；brief 不從別處組裝 |
| 14 | 驗收條件逐條抄自卡面，一條一列，⛔ 不改寫不合併 | dispatch-package.md:51; review-dispatch.md:56; review-prompt.md:35 | | 範本欄位（CLI 填） | 卡面 JSON 直接展開 |
| 15 | 非目標逐字帶入 | dispatch-package.md:52 | | 範本欄位（CLI 填） | 同上 |
| 16 | 注意事項三層編號（F-階段／P-專案／T-任務）累加⛔ 不覆寫；③ 逐條回應三值；④ 只對格數與值域⛔ 不判內容；格數不符＝退回 | dispatch-package.md:56-58; delivery-report.md:71 | | 核心-印 | 這就是 brief DI ＋ 完整性檢查的本體 |
| 17 | 13 族踩坑清冊每族恰一行，三值（已檢查／不適用／發現），與注意事項三值⛔ 不互代 | dispatch-package.md:59; delivery-report.md:77-85 | | 模組(13 族踩坑清冊) | 已定為模組 |
| 18 | 上一輪退回理由逐字帶入派工包；無則寫「無前輪」 | dispatch-package.md:60 | | 範本欄位（CLI 填） | 前輪裁決在卡面 JSON |
| 19 | 範圍外發現只能是報告的一節交需求方；⛔ 不自行開卡、⛔ 不 spawn 背景任務 | dispatch-package.md:64; delivery-report.md:93; verdict.md:90 | | 核心-印 | 行為約束，無平台執行者 |
| 20 | 需要等待時前景輪詢或不結束回合；⛔ 不以「等背景通知」結束回合 | dispatch-package.md:65 | | 核心-印 | harness 行為，CLI 不可見 |
| 21 | 分支更新走本地 rebase ＋ `--force-with-lease`，⛔ 不用 `gh pr update-branch` | dispatch-package.md:66 | | 核心-印 | 見未驗：squash 政策下此害是否仍存 |
| 22 | `gh pr update-branch` 狹義例外（綁 `TRAILER_GUARD_EPOCH`，派工包內具名判定） | dispatch-package.md:66-67 | 需求方 2026-08-21 於 `ai-workflow#39` 裁定 | 砍 | 綁舊守衛 epoch 的過渡註記 |
| 23 | 詭異數據標「待人工判讀」交需求方；外部佐證定性 only、數值以官方為權威、附 URL＋日期 | dispatch-package.md:68 | statistical-redline.md:32（2026-08-05 裁定） | 砍 | 資料專案條款，由專案層帶入，不進框架 |
| 24 | commit trailer 為訊息末端連續單一區塊，中間無空行 | dispatch-package.md:69-76 | | 核心-硬擋 | `git interpret-trailers --parse` 遇空行即切；推上去的歷史不可改寫 |
| 25 | ⛔ 不真跑爬蟲、訓練等有副作用的 CLI；副作用入口清單必須指得出居所，PM 代填須逐字標明 | dispatch-package.md:78-80; review-dispatch.md:70; review-prompt.md:41 | | 核心-印 | 清單是專案層欄位；原則由 brief 印 |
| 26 | 執行者推分支到 origin，⛔ 不 merge；回報 40 碼 SHA | dispatch-package.md:84 | | 核心-硬擋 | 分支保護＋required check 在平台層擋 |
| 27 | 交付報告是 ③ 的一部分：只推 commit 沒報告＝仍在進行中 | dispatch-package.md:85; delivery-report.md:3 | | 核心-印 | CLI 查「有沒有報告 JSON」即可印 |
| 28 | 執行者⛔ 不得自派查核者、⛔ 不得自 merge | dispatch-package.md:86 | | 核心-硬擋 | CLI 比對派審 to 與執行者 owner 相同即拒 |
| 29 | 交回前把 shell cwd 移出 worktree（`lsof +D` 無輸出） | dispatch-package.md:87 | | 模組(資源互斥檢查與 worktree 註冊) | 只在 worktree 收尾時需要 |
| 30 | 文件自身的已知落差自陳；無則逐字寫「無」，⛔ 不留空 | dispatch-package.md:91-94; control-plane-contract.md:43,64-66 | | 範本欄位（人填） | 空白與「還沒想過」事後同形 |
| 31 | 自評只有本人寫得出；PM 代寫逐字標「複驗報告」 | delivery-report.md:3 | | 核心-印 | 角色歸屬 |
| 32 | 報告的交付入口 SHA 必須等於 handoff `source_sha`；報告後再 commit ⇒ 退回 | delivery-report.md:13,16 | | 核心-硬擋 | CLI 比對報告 JSON 的 SHA 與分支 head |
| 33 | `self_run` 是實跑紀錄，⛔ 不讀碼推論、⛔ 不轉抄他人輸出 | delivery-report.md:26; verdict.md:27 | | 範本欄位（人填） | 真偽 CLI 不判；空／非空可查 |
| 34 | `rc=0` ⛔ 不等於成功，判成敗看被改變的狀態 | delivery-report.md:32; status-change-ruling.md:34; closeout-report.md:29 | status-change-ruling.md:34（`gh pr merge` 印拒絕理由卻回 0） | 核心-印 | shell 行為，印給人 |
| 35 | 本輪 commit 清單由 `git log` 取 | delivery-report.md:47 | | 範本欄位（CLI 填） | git 機械可得 |
| 36 | 改動面每檔一列 | delivery-report.md:48 | | 範本欄位（CLI 填） | `git diff --stat` 可得 |
| 37 | 交付物寫事實⛔ 不寫狀態；可變狀態一律寫查詢方法 | delivery-report.md:49 | | 核心-印 | 撰寫紀律 |
| 38 | 逐驗收條件一節：做法／證據／falsifier，⛔ 不合併 | delivery-report.md:53-59 | | 範本欄位（人填） | falsifier 是判斷 |
| 39 | 失誤登記逐項轉錄，⛔ 不摘要不加緩和語；無則逐字寫「無」 | delivery-report.md:63-67; closeout-report.md:66 | | 範本欄位（人填） | 「無」與空白 CLI 可分 |
| 40 | 高階型研究卡附可重跑 harness；非研究卡逐字寫「不適用」⛔ 不刪節 | delivery-report.md:99-100 | | 模組(統計紅線)※ | 此模組不在既定清單 |
| 41 | 派審詞＋查核者準則就是全部要求，沒寫的慣例⛔ 不存在 | review-dispatch.md:3 | review-dispatch.md:3（2026-08-29） | 核心-印 | brief 必須自足，是 DI 的設計前提 |
| 42 | 紅線卡查核者跨模型家族或人工；同家族不同工具不算獨立 | review-dispatch.md:4; review-prompt.md:3; AGENTS.md:35 | | 核心-硬擋 | 執行者與查核者的模型家族欄可機械比對 |
| 43 | 查核者⛔ 不得代改 source branch | review-dispatch.md:4; review-prompt.md:42; worktree-lifecycle.md:9 | | 核心-硬擋 | 查核期間分支 head 變動由 SHA 比對抓到 |
| 44 | spec 基線與父卡當前版本不一致即退回；子卡註冊時即必填 | review-dispatch.md:11; baseline-cascade.md:24 | baseline-cascade.md:24（WF-18 首戰命中的是漏填） | 模組(基線遞變)※ | 無父卡時不存在 |
| 45 | 基線 SHA ＝ merge-base，釘死字面；⛔ 不抄 `origin/main`、⛔ 不動態算 | review-dispatch.md:28; review-prompt.md:21 | docs/ROADMAP.md:283（三次派審詞 SHA 漂移） | 範本欄位（CLI 填） | git 可算；人抄才漂移 |
| 46 | 查核進駐後第一件事核對 `git rev-parse HEAD` == `source_sha` 且工作區乾淨，不同即 review-invalid | review-dispatch.md:29; review-prompt.md:22 | | 核心-硬擋 | brief 派審時直接驗分支 tip |
| 47 | 守衛在合併結果上跑，⛔ 不在分支頭上 | review-dispatch.md:30; review-prompt.md:43; verdict.md:33 | docs/ROADMAP.md:122-124（分支 388 passed、併 main 14 error） | 核心-硬擋 | required check `strict: true` 在平台層擋（docs/ROADMAP.md:134） |
| 48 | PM 交規劃產出物給查核者前先以「同一份 R1–R4 表」自審 | review-dispatch.md:40 | | 砍 | R1–R4 表不在本批檔案，指標懸空 |
| 49 | 第一判準具否決權：`core_pain_resolved: no` ⇒ 一律 REQUEST_CHANGES，finding `attribution: planner`、`finding_class: authoritative-artifact` | review-dispatch.md:48-52; verdict.md:48-50; review-prompt.md:28-31; review-escalation.md:214 | | 核心-硬擋 | JSON 三欄一致性可機械檢查 |
| 50 | 前輪 findings 必列（finding_id／severity／blocking／root_cause_id／前輪處置／本輪應閉環）；R1 逐字寫「無前輪」 | review-dispatch.md:58-64 | | 範本欄位（CLI 填） | 前輪裁決 JSON 在卡面 |
| 51 | `closure_reporting_requested: false` 記錄一次偏離範本，須在派審當下寫下 | review-dispatch.md:66; review-prompt.md:73 | | 模組(升級梯) | 只服務 deferred_findings 出口（#106） |
| 52 | 驗證命令會改 tracked file 時在 disposable worktree／容器執行；審查沙箱無 claim、無 owner | review-dispatch.md:71; worktree-lifecycle.md:9 | | 模組(資源互斥檢查與 worktree 註冊) | |
| 53 | 跨 repo 證據以絕對路徑＋釘住 SHA＋碼段對帳 | review-dispatch.md:72; review-prompt.md:44; statistical-redline.md:60 | | 核心-印 | 撰寫紀律 |
| 54 | worktree 內 submodule 目錄為空是預期，「檔案不在我的樹裡」不構成 finding | review-dispatch.md:72; worktree-lifecycle.md:7 | | 模組(資源互斥檢查與 worktree 註冊) | 只在 worktree＋submodule 情境 |
| 55 | 正文⛔ 不得出現事件 marker 前綴字面 | review-dispatch.md:74; review-prompt.md:46; verdict.md:98 | docs/CONSUMER_CONFORMANCE.md:46（#15、#17 因派審留言引用而凍卡） | 砍 | 新 CLI 不讀 marker，病灶消失 |
| 56 | 沒有 `self_run` 的 APPROVE 無效，記 review-invalid、不計 iteration | review-dispatch.md:81; verdict.md:34; review-prompt.md:67; review-escalation.md:17 | | 核心-硬擋 | JSON `self_run` 非空可查 |
| 57 | 有寫入通道者自己寫回，先 `--validate-only` 自檢；無通道者交 PM 轉錄，PM ⛔ 不判裁決對錯 | review-dispatch.md:80; verdict.md:96-97 | | 核心-印 | 轉錄不判內容是四角色分工 |
| 58 | R2 以後只做前輪 finding 逐項閉環＋回歸不倒退；⛔ 不重跑已過項、⛔ 不擴審 | review-dispatch.md:85; review-prompt.md:73 | | 核心-印 | 收斂紀律 |
| 59 | PM 自產出物同罩注意事項清冊（P-派審／P-裁定／P-結案） | review-dispatch.md:89-97; status-change-ruling.md:104-112; closeout-report.md:85-95 | | 核心-印 | 同 #16 |
| 60 | 裁決一句話理由與 findings 語意一致；APPROVE 與 open blocking finding 並存即擋 | verdict.md:55 | | 核心-硬擋 | JSON 內 blocking／status 與 result 可機械比對 |
| 61 | finding 八欄全必填（finding_id／severity／blocking／finding_class／attribution／root_cause_id／evidence／disposition）；無 finding 逐字寫「無」 | verdict.md:65-74; review-prompt.md:57-64 | | 範本欄位（人填） | 值域 CLI 查、內容人判；finding_id 由 CLI 編 |
| 62 | 高階型研究卡 ≥3 不同族角度對抗性反測；⛔ 不裁結論真值，只驗量測可重跑 | verdict.md:80-86 | | 模組(統計紅線)※ | |
| 63 | 收據 `wf-review-receipt:v1` 選配；無收據時查核者身分只有自由文字 | verdict.md:98; handoff-contract.md:65-79 | | 砍 | marker 機制 |
| 64 | 裁定歸需求方，PM 只準備裁定單、⛔ 不裁定 | status-change-ruling.md:4 | | 核心-印 | 角色分工 |
| 65 | 裁定前先讀實際值（`gh issue view`／`gh project item-list`），⛔ 不憑印象 | status-change-ruling.md:25-29 | docs/ROADMAP.md:164-166（PM 憑印象排程；前一日三次用記憶答狀態） | 範本欄位（CLI 填） | 現況由 CLI 印，人就不必憑印象 |
| 66 | 狀態面唯一寫入通道＝CLI；GitHub UI 手改欄位即違規 | status-change-ruling.md:32; control-plane-contract.md:10; AGENTS.md:19 | | 核心-印 | UI 手改擋不到；漂移靠每日快照偵測 |
| 67 | 每個寫入動作後回讀驗證；多筆遠端寫入無交易性，半寫入須被偵測而非靜默視為完成 | status-change-ruling.md:33; handoff-contract.md:99-105 | handoff-contract.md:105 | 核心-硬擋 | CLI 每個寫入動詞自帶回讀 |
| 68 | 一張裁定單⛔ 只裁一類 | status-change-ruling.md:48 | | 範本欄位（人填） | 類別 enum CLI 查 |
| 69 | 升級四選一（換人／退回上一階段／停卡／退回無效）；「改規格」⛔ 不是合法值 | status-change-ruling.md:50,65-74 | | 模組(升級梯) | 已定為模組 |
| 70 | 停止＝終態、⛔ 無出口；復活＝開新卡 | status-change-ruling.md:51,76-81 | | 核心-硬擋 | 狀態機終態，CLI 拒絕自終態的轉移 |
| 71 | 撤銷降回清單：`deleteProjectV2Item`，卡 ID 保留、輪次延續；撤銷≠停止 | status-change-ruling.md:52,83-87 | | 核心-印 | GitHub 機械操作是 CLI 動詞；是否撤銷是裁定 |
| 72 | 級別升自由、降須需求方裁定留痕，並逐項列出被繞過的閘門 | status-change-ruling.md:53,89-93 | | 核心-印 | 級別差異 CLI 印；閘門清單人填 |
| 73 | 裁定單「為什麼走到這裡」只寫事實⛔ 不含建議 | status-change-ruling.md:56-61 | | 範本欄位（人填） | 推薦會把裁定變背書 |
| 74 | 停止類必填可證偽復活條件 | status-change-ruling.md:80 | | 範本欄位（人填） | |
| 75 | 結案階段的 ④＝需求方；確認後才轉終態＋封存 | closeout-report.md:3 | | 核心-印 | 角色分工 |
| 76 | 合併⛔ 不是結案 | closeout-report.md:29; worktree-lifecycle.md:11 | worktree-lifecycle.md:11（三次停在 📦已合併留假活卡） | 核心-印 | |
| 77 | 結案四道停下條件：blocking 未 resolved／CI 非綠或 merge 後狀態不符／BEHIND 衝突／T4 人工 sign-off | closeout-report.md:57-62 | | 核心-硬擋 | 前三項由 findings JSON、CI API、PR mergeState 得；第四項印 |
| 78 | 清單收斂：真解決才關；終態才釋放資源；不帶 `--cleanup` 的 release 寫明理由 | closeout-report.md:73-75 | | 核心-印 | |
| 79 | 翻案把手必須可跑（`git revert <merge SHA>`）；寫不出即逐字「無把手」＋原因 | closeout-report.md:79-82 | | 範本欄位（人填） | |
| 80 | 裁決層面更正走 `review-correction` 事件 | closeout-report.md:81; review-escalation.md:44 | | 砍 | 舊事件型別；新 CLI 只寫卡面 JSON |
| 81 | review-prompt 節次編號⛔ 不得改（cli 六處引用） | review-prompt.md:5; template-migration-map.md:61 | | 砍 | 舊 CLI 實作耦合 |
| 82 | 查核⛔ 不用卡面沒有的標準；用了即「退回無效」事由 | review-prompt.md:37 | | 核心-印 | 內容判斷 |
| 83 | 結構化輸出區塊⛔ 不混散文；同一報告⛔ 不得兩個含 `review_result` 的區塊 | review-prompt.md:69 | review-prompt.md:69（把範本區塊與實際裁決一起貼） | 核心-硬擋 | fenced JSON 多於一塊即拒 |
| 84 | 聊天、PR 留言、tmux 訊息只可作通知，⛔ 不可作狀態 | handoff-contract.md:7; ADOPTION.md:28 | | 核心-印 | 狀態只住 Project 欄位＋卡面 JSON |
| 85 | `source_sha` 固定完整 40 碼、須已 push；⛔ 不接受 branch name／短 SHA／未提交 | handoff-contract.md:8,37; worktree-lifecycle.md:9 | | 核心-硬擋 | CLI 對 remote ref 解析即可拒 |
| 86 | receiver 驗證失敗寫阻塞或 findings，⛔ 不得自行修正 sender 內容 | handoff-contract.md:9 | | 核心-印 | 角色紀律 |
| 87 | 本機 runtime／queue 必須 `.gitignore`；重啟以 remote 為準，不信本機暫存 | handoff-contract.md:11; control-plane-contract.md:86 | | 砍 | tmux／swarmforge 情境不在新框架 |
| 88 | 每次 handoff 引用有效 claim／lease；過期不得接受 | handoff-contract.md:10,38 | | 模組(資源互斥檢查與 worktree 註冊) | lease 只在並行時有意義 |
| 89 | 鍵集合封閉：出現未定義鍵即 fail-closed，⛔ 不忽略後照常解析 | handoff-contract.md:91 | | 核心-硬擋 | JSON schema 嚴格模式 |
| 90 | 讀不懂的留痕⛔ 不得跳過後照常放行；fail-closed 作用域是整張卡 | handoff-contract.md:119-121 | | 核心-硬擋 | 卡面 JSON 解析失敗 ⇒ 該卡所有動詞拒跑 |
| 91 | 序列化成功 ⟹ 解析成功且值逐字相同；結構字元逐欄位明列處置（保留／逃逸／不適用） | handoff-contract.md:185-199 | handoff-contract.md:183（`#21` 往返缺陷，`#37` 修） | 核心-硬擋 | JSON 天然滿足；寫入前仍須拒收非法值 |
| 92 | 寫入端拒收，⛔ 不以正規化代替；拒收須乾淨（可辨識訊息＋非零 rc） | handoff-contract.md:201-205 | | 核心-硬擋 | |
| 93 | 讀寫往返測試必須機械、含真實語料、含負向半邊、走真正會跑的路徑 | handoff-contract.md:207-214 | | 核心-硬擋 | CLI 測試要求 |
| 94 | 指不出執行者所在檔與行的規則一律寫成「約定」，⛔ 不得寫成「強制」 | handoff-contract.md:216,255-258; docs/ROADMAP.md:14,138-139 | | 核心-印 | 重寫時的撰寫規則；防「看起來有閘門」 |
| 95 | 未登記等同未生效；fail-open 落差必須有追蹤卡 | handoff-contract.md:284-296; docs/CONSUMER_CONFORMANCE.md:7 | | 砍 | 服務 marker 消費者登記；母體已空（docs/CONSUMER_CONFORMANCE.md:91） |
| 96 | preflight 至少驗：必填欄、spec 基線、依賴狀態、handoff 與 branch tip SHA 同一、已推送、工作區乾淨、證據存在、trailer | review-escalation.md:15 | | 核心-硬擋 | 全部機械可得 |
| 97 | 可修正的交付缺口記 preflight-failed；等外部條件轉阻塞；兩者不建 review、不派 reviewer、不計 iteration | review-escalation.md:9-10,15 | | 模組(升級梯) | iteration 計數只服務升級 |
| 98 | 同一 reviewer 對同一 SHA 重複回報且無新範圍 ⇒ review-invalid | review-escalation.md:17 | | 模組(升級梯) | |
| 99 | finding 另帶 `accepted`／`status`（open／resolved／withdrawn）；accepted 由 lifecycle writer 標，reviewer ⛔ 不決定是否消耗額度 | review-escalation.md:25-36,44 | | 模組(升級梯) | |
| 100 | finding_class 五類定義；文件不因副檔名自動豁免 | review-escalation.md:38-42 | | 範本欄位（人填） | 值域進 JSON schema |
| 101 | `root_cause_id=unknown` ⛔ 不得跨 finding 當同根因；finding_id 須穩定，換號重開不構成處置 | review-escalation.md:44,97; AGENTS.md:84-86 | | 模組(升級梯) | |
| 102 | 可計數退回四條件；純 governance／coordination／environment finding ⛔ 不消耗額度 | review-escalation.md:50-57 | | 模組(升級梯) | |
| 103 | 第三個可計數 attempt 先建 checkpoint，⛔ 不按整數直接升級；severity ⛔ 不單獨推定 | review-escalation.md:61-66 | | 模組(升級梯) | |
| 104 | 第一條件須累計＋存活；carry set 六格，「未提及」為預設觸發格 | review-escalation.md:69-99 | | 模組(升級梯) | |
| 105 | epoch 遞增須需求方授權；adapter 拒跳號、倒退 | review-escalation.md:159 | | 模組(升級梯) | |
| 106 | `deferred_findings` 出口（spec-narrowed／instruction-omitted）及其款次 | review-escalation.md:101-157,236-248 | review-escalation.md:149（本 repo 今天寫不出來） | 砍 | 服務母體為空；docs/ROADMAP.md:300 判 `#39` 過度工程 |
| 107 | `escalation-resolution` 型別、`carried-forward`、`authorization_binding` | review-escalation.md:161-197,250-277 | | 砍 | docs/ROADMAP.md:64-66,300：收斂為宣告欄位 |
| 108 | `counts_toward_escalation` 由 adapter 算，reviewer ⛔ 不自行宣告 | review-escalation.md:343 | | 模組(升級梯) | |
| 109 | `review-marker-clearance`、停機態、`contract-baseline` cutover | review-escalation.md:19,279-341,343 | | 砍 | marker 機制 |
| 110 | worktree 註冊制：沒登記才算違規，命名對不上不算 | worktree-lifecycle.md:5 | | 模組(資源互斥檢查與 worktree 註冊) | |
| 111 | 派工前必跑 `doctor` 對帳（孤兒／死路徑／submodule／殘留 lease），唯讀不自動清理 | worktree-lifecycle.md:6; control-plane-contract.md:78 | docs/ROADMAP.md:307-313（降級 20 張後報 17 筆假孤兒） | 模組(資源互斥檢查與 worktree 註冊) | |
| 112 | 同卡族共用 worktree，修復切新分支不另開目錄 | worktree-lifecycle.md:8 | | 模組(資源互斥檢查與 worktree 註冊) | |
| 113 | merge 者先離開 worktree；卡族全結案後才移除 worktree、刪本地／遠端分支 | worktree-lifecycle.md:10 | | 模組(資源互斥檢查與 worktree 註冊) | |
| 114 | 收尾＝走完結案清單（main 複驗→清理→釋放資源→狀態收尾→對帳）；無法完成任一項明確交回，不留中間態 | worktree-lifecycle.md:11-19 | worktree-lifecycle.md:11（WF-18） | 模組(資源互斥檢查與 worktree 註冊) | 其中卡檔封存（:16）與 Ledger 重建（:17）母體已空 → 砍 |
| 115 | 禁止從仍被 checkout 的分支刪 branch；禁止在 worktree 內移除自身目錄 | worktree-lifecycle.md:22 | | 模組(資源互斥檢查與 worktree 註冊) | |
| 116 | 回收前先檢查未提交變更，禁止靜默刪除工作內容 | docs/WF_CLEANUP_GUARD1.md:11; docs/ROADMAP.md:353-356 | docs/ROADMAP.md:353-356（未初始化 submodule 目錄連同工作內容被刪） | 模組(資源互斥檢查與 worktree 註冊) | 硬擋屬性，但只在 worktree 情境 |
| 117 | 基線變更：執行者凍結受影響部分並留 `baseline-change-request`，⛔ 不自行改基線後續作 | baseline-cascade.md:12 | | 模組(基線遞變)※ | |
| 118 | 觸發者／評估者／核可者三職不可合併於一人 | baseline-cascade.md:8 | | 模組(基線遞變)※ | 四角色下對應見未驗 |
| 119 | 影響級別 none／scope／blocked／invalidated 由評估者判並留痕，非觸發者自判 | baseline-cascade.md:15-20,31 | | 模組(基線遞變)※ | |
| 120 | 需求方核可前新基線不生效；已合併卡不回改，缺口另開 follow-up | baseline-cascade.md:22-23 | | 模組(基線遞變)※ | 「已合併不回改」可升 核心-印 |
| 121 | 契約檔不得填 token／secret／連線字串／個資 | control-plane-contract.md:3; database-contract.md:3 | | 核心-印 | |
| 122 | Issue timeline 作 event store 時必須有定期 snapshot export 作離線稽核副本 | control-plane-contract.md:12 | | 模組(每日快照) | 已定為模組 |
| 123 | Ledger 投影＝snapshot 產生，不手改 | control-plane-contract.md:13; worktree-lifecycle.md:17 | | 砍 | Ledger 已移除（template-migration-map.md:17） |
| 124 | event schema／type 列舉／local telemetry envelope | control-plane-contract.md:18-35 | | 砍 | 舊事件模型 |
| 125 | 派工前資源交集比對（本卡寫入集 × 現役卡寫入集，撞則排隊）；現役含 📦已合併未收尾者 | control-plane-contract.md:75; closeout-report.md:75 | | 模組(資源互斥檢查與 worktree 註冊) | |
| 126 | 派工守衛每一站對無法安全判定的輸入以「阻擋」或「一次性具名留痕豁免」結束，⛔ 不得「略過並繼續」 | docs/WF_RESOURCE_WRITESET1.md:9 | | 模組(資源互斥檢查與 worktree 註冊) | 檔頭不變式；全檔不含實作 |
| 127 | 破壞性 CLI 啟動須驗 lease，無 lease 拒跑 | control-plane-contract.md:76 | | 模組(資源互斥檢查與 worktree 註冊) | |
| 128 | WIP limit（agent／review queue） | control-plane-contract.md:74; ADOPTION.md:28 | | 模組(資源互斥檢查與 worktree 註冊) | 單線無意義 |
| 129 | db 資源 token 文法：`db:<env>:schema`／`db:<env>:table:<name>`，`schema`／`table` 是字面關鍵字 | database-contract.md:30-41 | database-contract.md:47-50（cpbl 5 行 6 處寫成 schema 名，靜默失效） | 模組(資源互斥檢查與 worktree 註冊) | 文法檢查機械 |
| 130 | `db:<env>:schema` 不支配 `db:<env>:table:<name>`；互斥是完全字串比對 | database-contract.md:52-55; docs/ROADMAP.md:369-371 | | 模組(資源互斥檢查與 worktree 註冊) | 已知漏報；重寫時決定比對語意 |
| 131 | 碰 DB 的卡必填 `db_scope`／`db_namespace`／`db_resources`／`migration_phase` | database-contract.md:27-35; dispatch-package.md:14 | | 範本欄位（CLI 填） | 卡面 JSON 欄位 |
| 132 | 不可逆 DB 操作須人工 sign-off 並記錄誰、如何 | database-contract.md:75 | | 核心-印 | |
| 133 | Initiative 級／T4／不可逆需求在 Discovery Gate 前完成同步對抗式質詢真對話；本欄是殘渣，⛔ 不以填欄代替對話 | discovery-brief.md:21-26 | | 範本欄位（人填） | 需求階段；CLI 只查有無填 |
| 134 | T2 以上前提逐條附實查證據；未驗證前提必須標示且不得設為硬前置 | discovery-brief.md:27-28 | | 範本欄位（人填） | |
| 135 | 統計卡「先跑紅」不適用；等價防線＝紅線區塊＋查核者重跑 | statistical-redline.md:3,8 | | 模組(統計紅線)※ | |
| 136 | 紅線條目具體化為該卡數字／窗口／門檻，⛔ 不照抄泛用句；⛔ 不以「接近門檻」放行；區塊缺席即 request-changes | statistical-redline.md:7,65 | | 模組(統計紅線)※ | |
| 137 | 十條失效模式清單（時間分離／in-out sample／特徵洩漏／門檻先定／選型洩漏／baseline 對照／小樣本／可重跑／as-of／離群個案查證） | statistical-redline.md:15-24 | statistical-redline.md:28-29（cpbl#98 裁決）；:55-58（VAL1 反例） | 模組(統計紅線)※ | 清單原樣保留 |
| 138 | #7／#9／#10 適用所有研究結論，不限紅線卡 | statistical-redline.md:9,28-30 | | 模組(統計紅線)※ | |
| 139 | 目標排序：防止低級事故（須有機械執行者）＞可稽核內容＞其他 | docs/ROADMAP.md:14-16 | docs/ROADMAP.md:10（需求方 2026-08-12 裁定） | 核心-印 | 重寫的取捨判準 |
| 140 | 開卡前三問：服務哪個目標／執行者是誰／現在有人受害嗎 | docs/ROADMAP.md:20-22 | | 範本欄位（人填） | 需求階段欄位 |
| 141 | 身分只需兩維度：角色＋模型；資料不完整即退回；⛔ 不寫恆真的身分驗證條文 | docs/ROADMAP.md:40-43,57-58 | | 核心-印 | 完整性檢查即新 CLI 的全部 |
| 142 | 代貼他人裁定時註明代擬代貼與授權來源 | docs/ROADMAP.md:60 | | 範本欄位（人填） | |
| 143 | 欄位同時承載可攜宣告與機器局部細節時，判定建立在可攜那一半 | docs/ROADMAP.md:96-106 | docs/ROADMAP.md:85-92（51 絕對／18 相對路徑） | 核心-印 | worktree 路徑欄設計依據 |
| 144 | 偵測器的卡⛔ 不得宣稱「已預防」 | docs/ROADMAP.md:138-139 | | 核心-印 | 撰寫規則 |
| 145 | 卡片一律 squash 合併；squash 訊息逐字記被審 SHA 與查核結論 | docs/ROADMAP.md:244-258 | docs/ROADMAP.md:234-237（merge 按鈕產不出 Reviewed-by） | 核心-硬擋 | repo 設定只允許 squash；訊息由 CLI 組 |
| 146 | 驗收政策：core_pain yes ＋ blocking 全屬細節 → 驗收，細節開 Backlog；細節判準是後果 | docs/ROADMAP.md:405-417 | docs/ROADMAP.md:421-422（2026-08-12 開 20 結 4） | 核心-印 | 見未驗：與 #60、#77 的 blocking 語意衝突 |
| 147 | finding 處置順序：是否立刻造成低級事故→服務哪個目標→是否與排程衝突；⛔ 不因 finding 存在就開卡；⛔ 不由 disposition 決定開卡 | docs/ROADMAP.md:436-450 | | 核心-印 | |
| 148 | stub 指向 canonical 不複製全文；範本使用時組裝，⛔ 不複製進專案 repo | ADOPTION.md:7,30; control-plane-contract.md:49-58 | | 核心-印 | brief DI 的採用形狀 |
| 149 | 部署：merge 後自動記錄已合併／PR URL／merge SHA；deploy→verify→update 同鏈；需部署卡 ✅已驗證 才完成；失敗不封存 | ADOPTION.md:40-42 | | 模組(部署階段) | |
| 150 | 程式碼與文件衝突時以程式碼為準 | AGENTS.md:17; README.md:17 | | 核心-印 | |
| 151 | 卡由待審清單項升級，`open --from-issue` 唯一路徑 | AGENTS.md:18; README.md:18 | | 核心-硬擋 | CLI 動詞入口 |
| 152 | 每階段五步迴圈：①印 ②派 ③交回 ④對完整性 ⑤路由 | AGENTS.md:20; README.md:20 | | 核心-印 | 新框架核心迴圈 |
| 153 | 改規則＝一張卡；規則錯了影響全專案 ⇒ 紅線 | AGENTS.md:35; README.md:24 | | 核心-印 | dogfooding |
| 154 | trailer：T0/T1 至少 Requested-by＋Implemented-by；T2 以上加 Planned-by；merge／核可加 Reviewed-by | AGENTS.md:37 | | 核心-硬擋 | CI 檢查 |
| 155 | trailer 判定細節（merge combined diff、cherry-pick、空 commit、epoch 界線） | AGENTS.md:62-80 | | 砍 | 舊 doctor 實作描述 |
| 156 | 根因家族 canonical 名與曾用名對照 | AGENTS.md:82-101 | | 砍 | 本 repo 歷史 |
| 157 | 卡面只寫能力層級（經濟型／主力型／高階型）⛔ 不寫模型名；缺欄即拒開卡 | AGENTS.md:105 | | 核心-硬擋 | enum 檢查 |
| 158 | 入口不指向會變的東西；活卡、範本清單一律用查的 | README.md:26-35; AGENTS.md:27-32 | README.md:35（檔案樹六個檔已不存在） | 核心-印 | 文件形狀規則 |

## 範本欄位

> 六份帶信封的範本（派工包／交付報告／派審詞／裁決／裁定單／結案報告）信封段落逐字相同者只列一次，標「信封（六份共用）」；某份獨有的信封欄另列。review-prompt.md 無信封。

| 範本 | 欄位 | 人填／CLI 填／砍 | 一句理由 |
|---|---|---|---|
| 信封（六份共用） | 卡ID／Issue（`<owner/repo>#<n>`） | CLI 填 | Project 欄位 |
| 信封（六份共用） | 級別（T0–T4） | CLI 填 | 卡面 JSON |
| 信封（六份共用） | Initiative（父卡／—） | CLI 填 | 卡面 JSON；無父卡即「—」 |
| 信封（六份共用） | spec 基線 | CLI 填 | 父卡 JSON `spec_version`；模組(基線遞變)※ |
| 信封（六份共用） | 階段 | CLI 填 | Project 欄位 |
| 信封（六份共用） | 輪次（iteration／R<n>） | CLI 填 | 由卡面 JSON 前輪紀錄計數 |
| 信封（六份共用） | from／to | CLI 填 | 角色與帳號在卡面 JSON owner 欄；模型@工具由 claim 記錄 |
| 信封（六份共用） | 核心痛點（卡面原文逐字） | CLI 填 | 卡面 JSON |
| 信封（六份共用） | 模型：實際 | 人填 | 只有撰寫者知道自己是誰 |
| 信封（六份共用） | 模型：卡面建議 | CLI 填 | 卡面 JSON `exec/review capability` |
| 信封（六份共用） | 模型：偏離理由 | 人填 | 判斷；相符時逐字「相符」 |
| 信封（六份共用） | 信封二：GitHub 帳號 | CLI 填 | `gh api user`；模組(身分自述) |
| 信封（六份共用） | 信封二：session ID | 人填 | harness 本機檔名，CLI 無法從 GitHub 得；模組(身分自述) |
| 信封（六份共用） | 信封二：該則訊息定位 | 人填 | 同上；模組(身分自述) |
| 信封（六份共用） | 信封三：驗證指令逐條（標註 worktree／容器／環境變數） | CLI 填 | 專案層檔案 DI 進 brief |
| 信封（六份共用） | 信封三：「rc 分開取」「完整性由輸出產生」「stderr 全文」三段警語 | 砍 | 是規則不是欄位；由 brief 印（規則 #7、#8） |
| 信封（六份共用） | 信封四：未驗項 #／項目／分類／原因 | 人填 | 分類是判斷；CLI 查分類值域與「原因」非空 |
| 派工包（獨有信封欄） | 服務的原始目標 | 人填 | 需求方意圖 |
| 派工包（獨有信封欄） | 鏈深 | CLI 填 | 父卡鏈由 JSON 推得 |
| 派工包（獨有信封欄） | `db_scope` | CLI 填 | 卡面 JSON |
| 派工包（獨有信封欄） | 資源宣告（寫入集逐條） | CLI 填 | 卡面 JSON；模組(資源互斥) |
| 派工包 §1 | repo 絕對路徑＋`origin/main` 40 碼 SHA | CLI 填 | git |
| 派工包 §1 | worktree 路徑／分支 | CLI 填 | claim 時 CLI 建立並寫回；模組(worktree 註冊) |
| 派工包 §1 | 寫入授權逐條 | 人填 | PM 判斷 |
| 派工包 §1 | 唯讀範圍 | 人填 | PM 判斷 |
| 派工包 §2 | 要做什麼（範圍） | CLI 填 | 卡面 body |
| 派工包 §2 | 驗收條件逐條 | CLI 填 | 卡面 JSON |
| 派工包 §2 | 非目標 | CLI 填 | 卡面 JSON |
| 派工包 §3 | 三層編號清單（F-／P-／T-） | CLI 填 | brief DI：階段檔＋專案層＋卡面 JSON 任務層 |
| 派工包 §3 | 踩坑族清冊範本 | CLI 填 | 模組(13 族踩坑清冊) 產生 |
| 派工包 §3 | 上一輪退回理由 | CLI 填 | 前輪裁決 JSON |
| 派工包 §4 | 六條標準條款全文 | 砍 | 是角色檔內容，由 brief DI 印；不是每份手抄的欄位 |
| 派工包 §4 | 「本卡是否援引狹義例外」 | 砍 | 規則 #22 砍 |
| 派工包 §4 | 副作用 CLI 入口清單 | CLI 填 | 專案層檔案；缺檔時 CLI 印「專案層未宣告」 |
| 派工包 §5 | 交付方式四條 | 砍 | 角色檔內容，brief 印 |
| 派工包 §6 | 這份派工包的已知落差 | 人填 | 文件自身缺陷，無則「無」 |
| 交付報告（獨有信封欄） | 交付入口 SHA／分支 | CLI 填 | `git rev-parse`；CLI 同時驗等於分支 head |
| 交付報告 信封三 | `self_run` 表（指令／rc／原始輸出） | 人填 | 實跑紀錄；CLI 查非空 |
| 交付報告 §1 | 本輪 commit 清單 | CLI 填 | `git log` |
| 交付報告 §1 | 改動面每檔一列 | CLI 填 | `git diff --stat` |
| 交付報告 §2 | AC 條文 | CLI 填 | 卡面 JSON |
| 交付報告 §2 | 做法／證據／falsifier | 人填 | 判斷 |
| 交付報告 §3 | 失誤登記（失誤／何時／影響／補救） | 人填 | 無則逐字「無」 |
| 交付報告 §4 | 注意事項回應清冊（編號 → 三值） | 人填 | 編號由 CLI 印；三值由人填；CLI 對格數與值域 |
| 交付報告 §5 | 13 族踩坑清冊 | 人填 | 族名由 CLI 印；模組(13 族踩坑清冊) |
| 交付報告 §6 | 待需求方裁決 | 人填 | 無則「無」 |
| 交付報告 §7 | 高階型研究卡加項：harness 路徑＋跑法 | 人填 | 模組(統計紅線)※；非研究卡由 CLI 印「不適用」 |
| 派審詞（獨有信封欄） | escalation epoch | CLI 填 | 模組(升級梯) |
| 派審詞（獨有信封欄） | 與執行者是否同家族 | CLI 填 | 兩個模型欄比對 |
| 派審詞 信封三 | 進駐 worktree／被審分支／`source_sha` | CLI 填 | 卡面 JSON＋git |
| 派審詞 信封三 | 基線 SHA（merge-base） | CLI 填 | git |
| 派審詞 信封三 | 「進駐後第一件事核對 HEAD」 | 砍 | 規則 #46 改由 CLI 派審時硬擋 |
| 派審詞 §1 | 第一判準問句（含痛點原文） | CLI 填 | 痛點來自卡面 |
| 派審詞 §2 | 逐項驗收清單 | CLI 填 | 卡面 JSON |
| 派審詞 §3 | 前輪 findings 表（六欄） | CLI 填 | 前輪裁決 JSON |
| 派審詞 §3 | 升級判準長段 | 砍 | 模組(升級梯) 檔內容，brief DI 印，不逐份重抄 |
| 派審詞 §3 | `closure_reporting_requested` | 砍 | 規則 #51、#106 砍 |
| 派審詞 §4 | 環境紅線五條 | 砍 | 角色檔（查核者）內容，brief 印 |
| 派審詞 §5 | 要交回什麼（schema／人讀／寫回方式） | 砍 | 角色檔內容 |
| 派審詞 §6 | R2 以後的範圍 | 砍 | 階段檔內容；R<n> 由 CLI 判 |
| 派審詞 §7 | P-派審-01..05 | 人填 | 編號由 CLI 印；三值人填 |
| 裁決（獨有信封欄） | 被審分支／`source_sha`／基線 | CLI 填 | 抄自派審詞，CLI 同時驗 HEAD |
| 裁決 信封三 | `self_run` 表 | 人填 | CLI 查非空；APPROVE 且空即拒 |
| 裁決 §1 | `core_pain_resolved` | 人填 | 判斷；CLI 驗與 result 一致 |
| 裁決 §1 | 證據 | 人填 | |
| 裁決 §2 | `review_result` | 人填 | CLI 驗與 findings 一致 |
| 裁決 §2 | 一句話理由 | 人填 | |
| 裁決 §3 | AC 條文 | CLI 填 | 卡面 JSON |
| 裁決 §3 | 判定（過／不過）／證據 | 人填 | |
| 裁決 §4 | finding_id | CLI 填 | `<卡>-R<n>-<序>` 機械編號 |
| 裁決 §4 | severity／blocking／finding_class／attribution／root_cause_id／evidence／disposition | 人填 | 值域 CLI 查 |
| 裁決 §4 | 升級建議長段 | 砍 | 模組(升級梯) 檔內容 |
| 裁決 §5 | 對抗性反測表 | 人填 | 模組(統計紅線)※；非研究卡 CLI 印「不適用」 |
| 裁決 §6 | 範圍外發現 | 人填 | 無則「無」 |
| 裁決 §7 | 寫回四條 | 砍 | 角色檔內容；收據條（:98）砍 |
| 裁定單（獨有信封欄） | 裁定回填：裁定者帳號／時間／訊息定位 | CLI 填 | GitHub comment author／created_at／URL |
| 裁定單 信封三 | 現況讀取指令 | 砍 | 改為 CLI 直接印現況值 |
| 裁定單 信封三 | 裁定落地的寫入動作／回讀驗證 | CLI 填 | CLI 動詞自帶回讀 |
| 裁定單 §1 | 類別勾選（升級／停止／撤銷／級別變更／其他） | 人填 | enum；CLI 查恰一個 |
| 裁定單 §1 | 升級判準長段 | 砍 | 模組(升級梯) |
| 裁定單 §2 | 事件序 | CLI 填 | 卡面 JSON 前輪紀錄＋Project 欄位歷史 |
| 裁定單 §2 | 三次退回逐字理由 | CLI 填 | 前輪裁決 JSON |
| 裁定單 §2 | 相關 findings 與 root_cause_id | CLI 填 | 同上 |
| 裁定單 §3.1 | 四選一各值「若成立會是什麼證據」 | 人填 | |
| 裁定單 §3.2 | 決策／原因／可證偽復活條件 | 人填 | |
| 裁定單 §3.3 | 清單項 URL | CLI 填 | `deleteProjectV2Item` 由 CLI 做 |
| 裁定單 §3.4 | 原級別→新級別／方向 | CLI 填 | 級別欄差異 |
| 裁定單 §3.4 | 降級後被繞過的閘門逐項 | 人填 | |
| 裁定單 §4 | 裁定值／裁定理由（需求方原文） | CLI 填 | 從需求方留言抄；PM 不改寫 |
| 裁定單 §4 | 生效動作／回讀驗證輸出 | CLI 填 | |
| 裁定單 §5 | P-裁定-01..05 | 人填 | 編號 CLI 印 |
| 結案報告 信封三 | `merge-base --is-ancestor` 指令／rc | CLI 填 | git |
| 結案報告 信封三 | CI／測試指令／指標 | CLI 填 | CI API |
| 結案報告 §1 | 痛點 → 處置一句話 | 人填 | |
| 結案報告 §2 | 最終 `review_result`／`core_pain_resolved` | CLI 填 | 末輪裁決 JSON |
| 結案報告 §2 | blocking findings → resolved 證據 | CLI 填 | findings JSON status |
| 結案報告 §3 | merge SHA／PR／CI | CLI 填 | GitHub API |
| 結案報告 §4 | 四道停下條件本卡狀況 | CLI 填 | 前三項機械；第四項（T4 人工 sign-off）人填 |
| 結案報告 §5 | 失誤登記／未驗清單逐字轉錄 | CLI 填 | 若交付報告與裁決為 JSON，轉錄即拼接 |
| 結案報告 §6 | 開卡時宣告涵蓋的清單項 URL | CLI 填 | 卡面 JSON |
| 結案報告 §6 | 逐項確認（真解決才關） | 人填 | |
| 結案報告 §7 | 翻案把手 | 人填 | 寫不出即「無把手」＋原因 |
| 結案報告 §8 | P-結案-01..06 | 人填 | 編號 CLI 印 |
| review-prompt §1 | 進駐位置／被審分支／source_sha／基線／卡與基線 | 砍 | 與派審詞信封一、信封三逐字重疊（review-prompt.md:24 自承「由派審詞帶入」） |
| review-prompt §2 | 第一判準 | 砍 | 與派審詞 §1 重疊 |
| review-prompt §3 | 逐項驗收清單 | 砍 | 與派審詞 §2 重疊 |
| review-prompt §4 | 環境紅線 | 砍 | 與派審詞 §4 重疊 |
| review-prompt §5 | 結構化輸出 schema（`core_pain_resolved`／`review_result`／`self_run`／`findings` 八欄） | CLI 填（schema 定義） | 這是唯一該留的部分，成為裁決 fenced JSON 的 schema |
| review-prompt §6 | R2 以後的範圍 | 砍 | 與派審詞 §6 重疊 |

### 五份能不能收成幾份

**能收成三份人填文件＋一份 JSON schema。** 依據是三組逐字重疊的欄位集合：

1. **派工包 ≡ 派審詞**（PM → 執行者／查核者）。兩者的信封一至四、「進駐位置＋基線 SHA」、「驗收條件逐條」、「注意事項清冊」、「已知落差／PM 自審清冊」全部同形；差異只在收件角色帶進的段落——派工包的六條標準條款（dispatch-package.md:63-80）對應派審詞的環境紅線（review-dispatch.md:68-74），派審詞多一張前輪 findings 表（review-dispatch.md:58-66）。這兩塊在新框架都是**角色檔＋前輪 JSON 由 brief DI 印出**，不是人抄的欄位。⇒ 收成一份「派工單」，`to` 欄的角色值決定 brief 帶入哪份角色檔；人填欄只剩：寫入授權、唯讀範圍、未驗項、文件自身落差、模型行的實際與偏離理由。
2. **交付報告 ≡ 裁決**（執行者／查核者 → PM）。兩者的信封、`self_run` 表、逐 AC（做法／證據／falsifier 對 判定／證據）、失誤登記 對 findings、注意事項清冊、待需求方裁決 對 範圍外發現、高階型研究卡加項 對 對抗性反測，逐段對位。review-prompt §5 已經是裁決的 schema；交付報告缺的只是同形的 schema。⇒ 收成一份「交回單」，fenced JSON 用同一個 schema、以 `role` 欄區分（執行者的 `findings` 即失誤登記；查核者的多 `core_pain_resolved`／`review_result` 兩欄）。
3. **狀態變更裁定單 ≡ 結案報告**（PM → 需求方）。兩者都是「PM 整理事實、需求方裁定／確認」：裁定單 §2 事件序＋三次退回理由 對 結案 §2 裁決摘要＋§5 逐字轉錄；裁定單 §4 裁定值 對 結案的需求方確認；兩者各有 P- 清冊。結案報告的「一屏七段」（closeout-report.md:4）在裁定單類別 enum 裡就是第六個值「結案確認」。⇒ 收成一份「裁定單」，類別 enum ＝ 升級／停止／撤銷／級別變更／結案確認／其他；事實段全部由 CLI 從卡面 JSON 拼出，人填只剩四選一證據、復活條件、翻案把手、被繞過的閘門。
4. **review-prompt.md 整份溶解**：§1–§4、§6 與派審詞逐字重疊（review-prompt.md:24 自承 §1 的值「由派審詞的信封一與信封三帶入」）；§5 抽成 CLI 的 JSON schema 定義。

信封四段的處置：信封一（卡與身分）全部 CLI 填；信封三（機械指令）由專案層 DI；信封二為模組(身分自述)，條件不成立時不印；信封四（未驗項）是三份文件唯一共同的人填段。

## 文件處置

| 檔 | 行數 | 處置（保留形狀／併入某檔／封存） | 一句理由 |
|---|---|---|---|
| templates/baseline-cascade.md | 31 | 併入 模組(基線遞變)※ 檔 | 程序五步＋影響級別表＋反模式是完整的模組形狀；模組名待定 |
| templates/closeout-report.md | 96 | 併入 裁定單（類別＝結案確認） | 事實段全可由 CLI 拼；人填只剩 §6 逐項確認、§7 翻案把手 |
| templates/control-plane-contract.md | 93 | 封存 | §2 event schema、Ledger、tmux 屬舊模型；§3 資源欄（:70-78）移入 模組(資源互斥) 的專案層欄位 |
| templates/database-contract.md | 76 | 保留形狀（專案層契約） | §3 token 文法與已發生事故（:38-55）是機械檢查依據；§1／§2／§4／§5 是專案自填表；無對應模組名（見空洞） |
| templates/delivery-report.md | 100 | 併入 交回單（role＝執行者） | 與 verdict.md 逐段對位 |
| templates/discovery-brief.md | 33 | 保留形狀（需求階段人填欄） | 對抗式質詢（:21-26）與前提實查（:27-28）是唯一寫在範本裡的需求階段判斷欄 |
| templates/dispatch-package.md | 93 | 併入 派工單（to＝執行者） | §4 六條、§5 交付方式改由角色檔 DI |
| templates/handoff-contract.md | 296 | §1、§3.2、§3.3 併入核心；§2、§3.1、§4、§5、§6 封存 | §3.2 三規則（:185-216）是 CLI 寫入端的設計約束；§3.1 marker 契約（:43-177）母體隨新 CLI 消失 |
| templates/review-dispatch.md | 97 | 併入 派工單（to＝查核者） | §4 環境紅線改由查核者角色檔 DI；前輪 findings 由 CLI 填 |
| templates/review-escalation.md | 349 | §1–§4 至 :99 併入 模組(升級梯)；:101-197、:279-341 封存 | deferred_findings、escalation-resolution、marker-clearance 三段依 docs/ROADMAP.md:300 與母體為空判砍 |
| templates/review-prompt.md | 75 | §5 抽成 CLI JSON schema；其餘併入 派工單 | :24 自承 §1 值來自派審詞 |
| templates/statistical-redline.md | 65 | 保留形狀 → 模組(統計紅線)※ | 十條清單＋具體化示例＋反例是自足的模組；模組名待定 |
| templates/status-change-ruling.md | 112 | 併入 裁定單 | 類別 enum 與各類必填欄保留；§1 升級長段改由模組檔 DI |
| templates/template-migration-map.md | 173 | 封存 | 過渡文件；:4 自述「不是範本，不要拿它組裝任何交接文件」 |
| templates/verdict.md | 99 | 併入 交回單（role＝查核者） | 與 delivery-report.md 逐段對位；schema 已在 review-prompt §5 |
| templates/worktree-lifecycle.md | 22 | 併入 模組(資源互斥檢查與 worktree 註冊) | 七步收尾清單（:11-19）是 WF_CLEANUP_GUARD1 引用的權威（docs/WF_CLEANUP_GUARD1.md:23）；:16 卡檔封存、:17 Ledger 兩步砍 |
| docs/ROADMAP.md | 456 | 封存；§0、§1、§1.5、§3.5、§4、§5 的裁定句已萃入規則表 | §3 排程表 :395-396 自承「已脫節，不可當現況讀」 |
| docs/CONSUMER_CONFORMANCE.md | 96 | 封存 | 登記對象是 marker 消費者；:91 自述無其他消費者 |
| ADOPTION.md | 52 | 保留形狀，重寫內容 | 「基本三步＋有 X 才接 Y」（:3, :26, :32, :36）正是核心＋模組啟用條件的形狀；:6、:16、:18、:48 引用的檔已移除 |
| AGENTS.md | 109 | 保留形狀（L0 三塊＋一分鐘心智模型＋現況用查的）；:39-101 封存 | trailer 判定細節與根因家族對照是本 repo 歷史 |
| README.md | 55 | 保留形狀 | :26-35 「入口不列會變的東西」是入口文件的形狀規則 |
| docs/CONTRACT_TOOL_RECONCILE.md | 662 | 封存 | :7 「本檔不實作任何一項修補」；對帳對象是舊契約 universe |
| docs/DEV_AIWF_MINIMAL_CI1.md | 823 | 封存 | :3-5 為 CI 形狀的裁定與自證紀錄；閘門後由 ruleset 接手（docs/ROADMAP.md:133-135） |
| docs/DEV_MAIN_RED_CAPABILITY_FLAGS1_FIX1.md | 292 | 封存 | :3 自述「取證紀錄，不是設計文件」 |
| docs/WF-25-REVIEW-WRITE-CHANNEL1.md | 96 | 封存 | :6-9 實測能力盤點，時點 2026-08-08 |
| docs/WF_CLEANUP_GUARD1.md | 483 | 封存；:11 原則已萃入規則 #116 | :5 實作已在 cleanup.py；:7 射程只到 release |
| docs/WF_EVENT_IDEMPOTENCY1.md | 1259 | 封存 | :7 「本檔是設計與契約，不含實作」 |
| docs/WF_EVENT_MARKER_V2.md | 969 | 封存 | :3 「契約設計，尚未實作」；:6 自承引用即凍卡 |
| docs/WF_RESOURCE_WRITESET1.md | 1416 | 封存；:9 不變式已萃入規則 #126 | :5 「本檔不含實作」 |
| docs/research/WORKFLOW-REDESIGN-2026-08-30.md | 119 | 保留（決議紀錄，非本次處置對象） | :4 優先權條款；本檔多處範本註記「對照見決議 §一」指向它 |

## 空洞

1. **DB 沒有模組名。** `database-contract.md` 全檔、`db_scope`／`db_resources`（dispatch-package.md:14-15）、db token 文法（database-contract.md:38-55）只能暫掛 模組(資源互斥檢查與 worktree 註冊)；但 migration 階段表（database-contract.md:63-69）與回滾（:71-76）不是互斥問題。既定八模組沒有一個承接。
2. **Initiative／spec 基線／基線遞變沒有模組名。** baseline-cascade.md 全檔、review-dispatch.md:11、信封一的 Initiative 與 spec 基線欄，條件是「有父卡」，既定清單無此模組。
3. **統計／研究卡沒有模組名。** statistical-redline.md 全檔、delivery-report.md:97-100、verdict.md:78-86，條件是「卡屬統計／ML／資料正確性紅線」，既定清單無此模組。
4. **review-dispatch.md:40 的「R1–R4 表」** 不在本批檔案任何一處，指標懸空。
5. **注意事項清冊的內容**（`F-<階段>-NN`）住 `stage-rules/` 各檔 §5（dispatch-package.md:56），不在本批母體；本檔只萃出機制（規則 #16），沒有萃出任何一條編號條目。
6. **部署階段與維護階段**在本批母體只有 ADOPTION.md:36-42 五行；templates/ 沒有對應範本，`部署狀態` 欄的去向在 docs/research/WORKFLOW-REDESIGN-2026-08-30.md:17 只寫「退位成部署階段產出物」。
7. **每日快照**在本批母體只有 control-plane-contract.md:12 一句「定期 snapshot export」；快照格式、頻率、比對對象無任何範本描述。
8. **Log 移留言**在本批母體沒有任何範本描述；handoff-contract.md:102 提到 Issue body `## Log` 索引行是舊三面一致的一面。
9. **升級梯的動詞面**：review-escalation.md 的機制全部以事件型別（`escalation-checkpoint`、`escalation-epoch-change`）表述；新 CLI 只讀寫卡面 JSON 與 Project 欄位，這些狀態在 JSON 裡的形狀本批母體沒有寫。
10. **需求／研究／規劃階段的範本形狀**：ADOPTION.md:16 引用的 `design-brief.md`、`research-plan.md` 已移除（「見 git 歷史」），本批只剩 discovery-brief.md 一份。
11. **「不得因當下額度預先把建議層級寫小」** 只在 CLAUDE.md（本 repo 專案指引，不在本批母體），AGENTS.md:103-109 沒有此句。
12. 分桶規則沒有「專案層」一桶：規則 #23（詭異數據條款）、#25 的副作用入口清單、database-contract §1／§2／§4／§5 都是「由專案自填、框架只留槽位」的東西，本檔把條款本身歸 砍、槽位歸 範本欄位（CLI 填），這是本檔的解讀，不是母體的裁定。

## 未驗

1. 本檔對 `stage-rules/`、`cli/`、`MODEL_ROUTING.md`、`tier-rules.md` 的引用全部轉抄自範本文字，未開檔驗證那些節次是否存在。
2. 範本引用的 GitHub issue／留言（`#39` issuecomment-5367447565、cpbl#98 comment 5208856434 等）未查證。
3. `docs/` 下 9 份設計文件只讀檔頭 30 行；處置判定依檔頭自述（「不含實作」「取證紀錄」「尚未實作」），檔身內容未讀。
4. **規則衝突待裁定**：docs/ROADMAP.md:412 「core_pain yes ＋ blocking 全屬細節 → 驗收」與 verdict.md:55、closeout-report.md:59 「open blocking finding ⇒ 不得 APPROVE／停下」語意相反；本檔兩邊都列（#60、#77、#146），未裁。
5. **規則衝突待裁定**：dispatch-package.md:66 禁 `gh pr update-branch`（理由：synthetic merge 污染歷史）與 docs/ROADMAP.md:248 「update-branch 產生的 merge commit 只在 PR 分支上，squash 會壓掉」；一律 squash 後禁令的害是否仍存，未裁。
6. **四角色對應未驗**：baseline-cascade.md:8 的「評估者＝規劃者（或 Coordinator）」、review-escalation.md 通篇的「Coordinator／需求方」、review-escalation.md:41 finding_class `coordination` 的定義，在四角色（需求方／PM／執行者／查核者）下該落誰，本檔假定 Coordinator→PM、規劃者→PM，未經裁定。
7. review-prompt.md §5 的 yaml schema 是否等於現行 `wfcli review` 解析器接受的集合，未對照 `cli/src/`。
8. 結案報告是否在「五份交接文件」之列，本檔依 handoff-contract.md:220-224 的說法（不在五份、同罩信封）；決議紀錄 §六本身只讀了檔頭 30 行，未核對。
9. 「信封（六份共用）」的判定是本檔逐行比對六份範本信封段後的結論；status-change-ruling.md 信封二多一行「裁定回填」、delivery-report.md 信封一多「交付入口 SHA」、review-dispatch.md／verdict.md 多「escalation epoch」與被審分支三格，已各自另列，其餘逐字同形。
