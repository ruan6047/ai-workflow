---
name: glossary
when: 寫或讀任何規則檔、CLI enum、Project 選項名、審核提示時查詞
non_scope: ⛔ 不解釋為什麼；⛔ 不管 schema 英文鍵名與 GitHub 平台詞（issue、PR、Project、ruleset、comment）
last_confirmed: 2026-09-05
---

# 通用語言

每列一個詞。中文正文只准用「詞」欄的字；違規判定條文住 `roles/conduct-common.md` §2。schema 鍵名與平台詞不入表，正文指涉時用對應詞。

| 詞 | 定義 | ⛔ 不是什麼 | 禁用同義詞 |
|---|---|---|---|
| 卡 | 在板上的 issue，帶 `wf-card` 區塊與卡ID | 不是清單項、不是 PR | Backlog、task、票 |
| 清單項 | 不在板、無 `wf-card` 區塊、帶 `wf-intake` 的 issue | 沒有卡ID | 提案、inbox item |
| 撤銷卡 | 不在板但帶 `wf-card` 區塊的 issue；`open` 可復板 | 不是清單項、不是停止 | 關閉的卡、歸檔卡 |
| 待審清單 | 全部清單項的集合；`open` 的唯一入口 | 不是看板欄位、不進任何分母 | backlog、inbox、待辦池 |
| 階段 | 需求／研究／規劃／執行／審核／部署／維護／結案 八個之一 | 不是狀態 | 站、phase、gate |
| 階段計畫 | 卡面 `stage_plan`：這張卡要走的階段子序列 | 不是流程圖 | 流程、pipeline、路線 |
| 狀態 | 待辦／進行中／待確認／完成／退回／阻塞，加階段與模組 delta 的值 | 不是部署狀態、不是交付狀態 | Status、進度 |
| 狀態面 | 卡當下的階段＋狀態＋阻塞；唯一居所＝issue body JSON 與 Project 投影欄 | 不是聊天、不是本機檔 | 看板狀態、board |
| 終態 | 出邊為空的狀態：完成、停止 | 不含撤銷 | 結束、closed、done |
| 轉移 | `move` 的一次寫入；轉移記錄＝其留言 | 不是事件流 | 事件、event、handoff |
| 合成表 | 核心轉移表 ∪ 已啟用模組 add − remove，再按該卡 `stage_plan` 展開 | 不是流程圖 | 狀態表、workflow 圖 |
| 模組 | opt-in 的規則包，帶恰一個啟用條件 | 未啟用時不存在 | 外掛、plugin、功能旗標 |
| 模組 delta | 模組宣告區塊對狀態值域、轉移、欄位、注意事項的增減 | 不是覆寫 | patch、override |
| iteration | 卡進入執行階段的次數 | 不是退回次數 | 輪次、輪、round |
| 查核輪 R1–R4 | 前提／射程／內容／影響面四題 | 不是 iteration | 輪次、pass |
| 硬擋 | CLI rc≠0 或平台拒絕的行為 | 不是印 | 守衛、閘門、偵測器 |
| 印 | CLI rc=0 並列出資訊的行為 | 不是判斷 | 警告（作為類別名） |
| 語意 | 動詞的固定行為 | 不是拒絕 | 邏輯、實作 |
| 拒收 | 一次硬擋事件與其 `wf:reject` 留言 | 不是硬擋類別名 | 駁回、reject |
| 寫壞資料、指向不存在 | CLI 拒收的僅有兩類：D1／D3 與 D2／D4 | 不含內容判讀 | 驗證失敗、invalid |
| 資料有效性、平台委託 | 硬擋的兩類來源：D1–D4／P1–P5 | 不是內容判讀 | 驗證、校驗、guard |
| 完整性 | 必要欄或必要段齊不齊 | 不是對不對 | 正確性、品質 |
| 裁定 | 需求方的決定，形狀＝一則留言 | 不是裁決 | 批准、核可 |
| 裁決 | 查核者的結論，形狀＝一則帶 `wf-return` 的留言 | 不是裁定 | verdict（作為動詞）、判決 |
| sign-off | 需求方對 T4 卡的最終授權裁定 | 不是每張卡都有 | approve、核准 |
| 派工單 | PM 給執行者或查核者的文件 | 不是聊天訊息 | 派工包、派審詞 |
| 交回單 | 執行者或查核者給 PM 的文件，帶 `wf-return` | 不是 PR 描述 | 交付報告、裁決報告 |
| 裁定單 | PM 給需求方的文件 | 不是裁定本身 | 狀態變更裁定單、結案報告 |
| 需求方 | 出題、裁定、sign-off 的人 | 不是 PM | 使用者、owner（作為角色） |
| PM | 派工、判 R1 R2、跑 `move` 的角色 | 不是查核者、不是第二 PM | 祕書、Coordinator、規劃者 |
| 執行者 | 做卡、交交回單的角色 | 不 merge 自己的變更 | 實作者、agent |
| 查核者 | 判 R3 R4、貼裁決的角色 | 不代改分支 | 人工查核、第二 PM、reviewer（中文語境） |
| 實體 | 跑角色的一個 session | 不是帳號 | 帳號、人、instance |
| 家族 | 模型家族 | 不是工具 | 供應商、vendor |
| 獨立查核 | 查核者實體不同於本 iteration 執行者實體 | 同家族不同工具不算跨家族 | 第二雙眼、peer review |
| 級別 | T0–T4 風險軸 | 不是難度 | tier（中文語境）、等級 |
| 能力層級 | 經濟型／主力型／高階型 | 不是模型名 | 模型、model |
| 紅線 | 至少 T3 的變更域 | 不是「高風險」的泛稱 | 敏感、高風險 |
| 單向門 | 級別只升不降；降級需裁定 | 不是不可逆的泛稱 | 不可逆、one-way |
| 核心痛點 | 卡面第一判準欄，從清單項逐字帶入 | 不是解法 | 目標、需求 |
| 驗收條件 | 卡面 `acceptance`：什麼算過 | 不是驗證項目 | 範圍、scope、AC |
| 驗證項目 | 卡面 `verification`：怎麼證明、誰證 | 不是 `self_run` | 測試計畫、驗證方式 |
| 非射程 | 卡面 `non_scope`：這張卡不做什麼 | 不是未驗 | 非目標、out of scope |
| 服務的原始目標 | 卡面 `service_goal`，需求方填 | 不是核心痛點 | 目的、initiative 目標 |
| 規格、規格欄 | 規格＝卡面判準與規格欄的總稱；規格欄＝使 `spec_version` +1 的四欄：`acceptance`／`verification`／`non_scope`／`resources` | 核心痛點不在此列 | 需求文件、spec |
| 清單收斂宣告 | 這張卡吸收哪些清單項：卡面 `source_issue`＋收件表單 `dedupe` 欄，落卡面 `list_convergence` | 不是查重 | 合併宣告、去重 |
| 設計閘（Design gate） | 規劃離開前 `verification` 填齊的檢查點 | 不是設計審查會 | 設計審、design review |
| 質詢 | T4 卡離開規劃前需求方與 PM 逐題定案的紀錄，落 `wf:log` | 不是 code review | grilling、訪談、審問 |
| 父卡、鏈深 | `parent` 指到的卡；沿父鏈算的層數 | 鏈深 >2 只印 | 母卡、子卡、family、epic |
| 資源宣告 | 卡面 `resources` 字串陣列 | 文法住模組 | 依賴、鎖 |
| owner | 卡當下的 {role, actor}，由 `move --actor` 寫 | 不是 GitHub assignee | 負責人、承辦 |
| 分支 | 卡面 `branch`：該卡工作所在的 git 分支 | 不是 worktree | feature、工作區 |
| 合併方式 | 專案層 `merge_method`，由平台強制 | 不是 CLI 判斷 | merge 策略 |
| SHA 四種 | 被審＝查核者讀到的 commit；來源＝卡面 `source_sha`；合併基底＝派工單的 merge-base；合併＝main 上的 merge commit | 不寫短 SHA | 版本、HEAD（作為名詞） |
| 注意事項 | 一份編號清單，四個來源合成 | 不是規則正文 | 踩坑清冊、清單（作為同義） |
| 加嚴層級 F-／P-／T- | 注意事項的三個編號前綴：框架／專案／卡面 | 不是來源 | 層 |
| 來源（四個） | core／module／project／card | 不是層 | 層、layer |
| 回應三值 | followed／not_applicable／found | 不是「已檢查」 | 已檢查、已遵守、N/A |
| 未驗清單三分類 | cannot／skipped／deferred | 不是裸列 | 未驗（裸列）、TODO |
| self_run | 交回單內實跑的指令與原始輸出 | 不是讀碼推論 | 本地測試、手動驗證 |
| falsifier | 交回單逐條驗收條件的證偽條件 | 不是反測 | 反向案例 |
| 失誤登記 | 交回單裡執行者自報的錯誤與修正 | 不是 finding | 自首、bug list |
| finding | 查核者交回單裡一條帶 id、severity、blocking、attribution 的問題 | 不是 GitHub issue | 缺陷、bug、issue（中文語境） |
| attribution | finding 責任歸屬：executor／coordinator／planner／reviewer／external | 不是 blame | 責任方 |
| 退回理由 | 裁定單裡每輪退回引用的 finding | 不是散文 | 駁回原因 |
| 復活條件 | 裁定單裡停止或撤銷後可重開的條件 | 不是重試 | 重啟條件、reopen |
| 翻案把手 | 裁定單裡推翻本次裁定所需的證據種類 | 不是上訴程序 | 上訴、appeal、反證 |
| 副作用入口 | 派工單列的、改動會外溢的檔或設定 | 不是影響面泛稱 | blast list |
| 派工、交回 | 五步迴圈的 ②（`move` 到進行中）與 ③（`move` 到待確認） | 不是聊天通知 | 認領、assign、handoff |
| 候選 | 貼在 `wf:note` 留言、尚未進任何加嚴層級的注意事項 | 不是正式條目 | 草稿、提案 |
| 七動詞 | open／move／edit／notes／brief／review／snapshot | 沒有第八個 | amend、assign、handoff、verdict（作為動詞） |
| 寫入契約 | `core/verbs.md` 的固定節：檢查先於首次遠端寫入、寫後回讀、拒收留痕 | 不是 transaction | 寫入規則 |
| 留言標頭 wf:* | CLI 與人留言的首行 | 不是 marker | marker、事件型別 |
| 投影欄 | Project 上由 CLI 回寫的五欄：階段／狀態／級別／owner／卡ID | 不是事實來源 | 看板欄位、Ledger 欄 |
| 封存、撤銷、停止 | 三個離開動作：終態封存／回清單／終態 | 封存不是刪除 | 關閉、刪除、歸檔 |
| db_scope | 卡對資料庫的變更範圍：none／read／write／schema／data-migration | 不是資源宣告 | db_permission、資料庫權限 |
| trailer | commit 訊息末端連續的 `Key: value` 區塊 | 不是 footer 散文 | footer、git-tag |
