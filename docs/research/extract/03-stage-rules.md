# 萃取 03：`stage-rules/`（13 檔）、`tier-rules.md`、`MODEL_ROUTING.md`

範圍：`stage-rules/{requirement,list-intake-requirements,research,planning,implementation,review,closeout,deploy,maintenance,defect-path,executor-conduct,reviewer-conduct,pm-conduct}.md`、`tier-rules.md`、`MODEL_ROUTING.md`。行號以 `cat -n` 實讀為準。

桶的讀法（沿派工單）：核心-硬擋＝錯了會造成不可逆或平台層事故，CLI 拒絕或 CLI 自己執行的機械動作；核心-印＝「有沒有填」，CLI 只印缺什麼；階段檔／角色檔＝「填得對不對」，標明住哪一檔；模組(名稱)＝條件不成立即不存在；砍＝裁定過程、來歷、過渡註記、CLI 內部實作描述。

角色檔命名：`role-requester`（需求方）／`role-pm`／`role-executor`／`role-reviewer`。階段檔命名：`stage-requirement`／`stage-research`／`stage-planning`／`stage-implementation`／`stage-review`／`stage-closeout`。

## 主表

| # | 規則（一句，祈使句，⛔ 不帶理由） | 來源 `檔名:行號` | 來歷事故（文中若有寫，一句；沒有寫「—」） | 桶／住哪檔 | 一句理由 |
|---:|---|---|---|---|---|
| 1 | 卡一律由待審清單項升級開出；`open` 只接受來源 issue 編號，不直接建 issue、不走 DraftIssue。 | requirement.md:27; list-intake-requirements.md:16; defect-path.md:25, 33 | — | 核心-硬擋 | `open` 的入口只有一個，沒有來源 issue 就跑不動。 |
| 2 | 卡ID 由 `open` 於升級時配發；清單項不配卡ID，缺陷不配 `BUG-` 前綴。 | requirement.md:29; list-intake-requirements.md:79; defect-path.md:29 | 配了 ID 的清單項不會被 `open` 的唯一性檢查找到，同一件事被開成第二張卡（list-intake-requirements.md:79）。 | 核心-硬擋 | 唯一性檢查只看看板 items，ID 由 CLI 配才守得住。 |
| 3 | 清單項不得掛成任何卡的 sub-issue。 | list-intake-requirements.md:81 | Project 的 Auto-add sub-issues workflow 開著，掛上去就自動上板，清單與看板界線當場消失。 | 核心-硬擋 | 平台層自動化會直接汙染看板。 |
| 4 | 父子鏈深 ≤2。 | requirement.md:36 | — | 核心-硬擋 | `open` 掛 sub-issue 時可機械查的結構上限。 |
| 5 | 卡面只有 `open` 渲染的一種形狀；沒有依卡種（含缺陷）的變體範本。 | defect-path.md:30 | — | 核心-硬擋 | 卡面欄位集合是 CLI 讀寫 JSON 的契約，分岔即分岔契約。 |
| 6 | 狀態轉移只經 `move`；`move` 依該階段的轉移表拒絕非法轉移，不憑印象。 | pm-conduct.md:64 | — | 核心-硬擋 | 轉移表是核心，非法轉移由機械擋。 |
| 7 | 每次狀態轉移由 `move` 寫入時間／from／to／輪次四欄。 | pm-conduct.md:22 | — | 核心-硬擋 | 轉移紀錄是狀態面的唯一來源，由 CLI 自己寫。 |
| 8 | iteration 只在進入執行階段時遞增，其他動詞不動它。 | implementation.md:10 | — | 核心-硬擋 | 計數器由 CLI 持有。 |
| 9 | 完成與停止為終態；終態無出口，復活＝開新卡。 | closeout.md:19, 22 | — | 核心-硬擋 | 終態出邊為空是轉移表的一部分。 |
| 10 | 進入終態時 `move` 一併封存卡；完成與停止皆封存。 | closeout.md:10, 22 | — | 核心-硬擋 | 封存是 GitHub 機械操作，附在 `move` 上。 |
| 11 | 已開卡的留痕全走卡面狀態面，不另開 log 檔。 | defect-path.md:69 | — | 核心-硬擋 | 狀態面單一來源。 |
| 12 | 清單項 body 含四欄：出處（連結或逐字引文＋來源；AI 撞到的寫「哪張卡的哪一步」）、觀察句、查重關鍵字逐字＋命中 issue 編號、所屬 repo；缺任一欄印出退回提案者，PM 不代填；開卡前查重同用此欄。 | list-intake-requirements.md:10, 21-29, 47-59, 65-69, 75-77, 123-127; requirement.md:30 | GitHub 搬 issue 會換號碼，放錯 repo 就得換一次號（list-intake-requirements.md:69）。 | 核心-印 | 四欄都是「有沒有」；「已確認沒有重複」是宣稱不是留痕。 |
| 13 | 非射程欄必填。 | requirement.md:33 | — | 核心-印 | 欄位存在。 |
| 14 | 驗收條件 ≥1。 | requirement.md:34 | — | 核心-印 | 數量可機械查。 |
| 15 | 階段計畫欄只列要跑的階段，值域＝階段名逐字。 | requirement.md:41 | — | 核心-印 | 值域檢查。 |
| 16 | 級別依據欄逐條回答三子問：敏感面（介面／資料／權限）、可復原性（錯了怎麼回來、被回滾前會不會先被引為判準）、影響面（單檔／單模組／整 repo／跨 repo）。 | requirement.md:40; tier-rules.md:54-60 | — | 核心-印 | 三格有沒有填；一致性由 PM 判（見 #44）。 |
| 17 | 開卡時填建議執行與查核能力層級（值域：經濟型／主力型／高階型）＋理由；卡面寫層級不寫模型名。 | MODEL_ROUTING.md:14 | — | 核心-印 | 欄位＋封閉值域。 |
| 18 | 派工與派審時記「實際能力層級／卡面建議／偏離理由」一行。 | MODEL_ROUTING.md:14; pm-conduct.md:22; implementation.md:16; review.md:16 | — | 核心-印 | 三格有沒有填。 |
| 19 | 開卡後在卡面宣告涵蓋哪幾個清單項。 | requirement.md:31 | — | 核心-印 | 欄位存在；核對在結案（#87）。 |
| 20 | T4 卡開卡前附 grilling 質詢紀錄，存活的反駁寫進非射程。 | requirement.md:39 | — | 核心-印 | 紀錄有沒有是機械查；反駁入不入射程歸 PM 判射程。 |
| 21 | `open` 從來源 issue 機械帶入痛點原文與出處，人不重打。 | requirement.md:28 | — | 核心-印 | 逐字沿用由 CLI 做最便宜。 |
| 22 | 交回必附注意事項回應清冊：對 CLI 印出的該階段清單逐條回應，值域＝`已遵循`／`不適用：<原因>`／`發現：<處置>`；格數或值域不符即印出退回；PM 自己的派審詞與結案報告同罩。 | requirement.md:46-48; research.md:45-47; planning.md:38-40; implementation.md:42-44; review.md:43-45; closeout.md:46-48; deploy.md:17-19; maintenance.md:17-19; defect-path.md:101-103; pm-conduct.md:92 | 「執行者有清冊而 PM 沒有」是 2026-08-31 前連續八輪派審詞漏掉未驗分類的結構因（pm-conduct.md:92）。 | 核心-印 | 格數與值域是機械對照，內容不判。 |
| 23 | 派工包（`brief`）印：規格、該階段注意事項清單、上一輪退回理由、能力層級行。 | implementation.md:16; pm-conduct.md:22 | — | 核心-印 | 印清單是 CLI 的本業。 |
| 24 | 交付報告必含：做了什麼（SHA／檔案／行數）、self_run 實跑紀錄、失誤登記逐項、未驗清單逐項＋各自原因、注意事項回應清冊；缺段印出。 | executor-conduct.md:22; implementation.md:10, 16 | — | 核心-印 | 段落有無。 |
| 25 | 未驗清單每項標三分類之一：驗不了／沒去驗／刻意不驗（含委給查核者的理由）。 | pm-conduct.md:91; executor-conduct.md:22 | 連續八輪派審詞裸列未驗（pm-conduct.md:91）。 | 核心-印 | 封閉值域。 |
| 26 | 派審詞必含：merge-base 基線 SHA（由 CLI 算出並釘死字面）、前輪 findings 與 root_cause_id、能力層級行、PM 已知未驗項、PM 自審紀錄。 | review.md:16, 30; reviewer-conduct.md:35; pm-conduct.md:22 | — | 核心-印 | merge-base 是 GitHub 機械操作；其餘段落有無。 |
| 27 | 交付報告宣稱的入口 SHA 須等於派審時的分支 head；不等印出退回。 | pm-conduct.md:30 | 2026-09-01 首戰：報告後又落一個 commit，查核者拿到兩個互相矛盾的 SHA。 | 核心-印 | 兩個 SHA 相等是機械比對。 |
| 28 | 裁決必含 `review_result`、`core_pain_resolved`、self_run 逐條、findings（id／severity／blocking／class／attribution／root_cause_id／evidence／disposition）；缺段印出。 | review.md:10; reviewer-conduct.md:20; pm-conduct.md:22 | — | 核心-印 | 段落有無；對錯歸查核者。 |
| 29 | 結案報告七段：痛點→處置、裁決摘要含 blocking 清零、merge SHA＋CI 指標、停下條件逐項、失誤登記與未驗清單逐字轉錄、清單收斂核對、翻案把手（revert＋review-correction）；缺段印出。 | closeout.md:10, 25; pm-conduct.md:54 | — | 核心-印 | 段落有無。 |
| 30 | 進入完成前印 merge SHA 是否為 main 祖先（`merge-base --is-ancestor`）與 CI 狀態。 | closeout.md:39; pm-conduct.md:50 | `gh pr merge` 印出拒絕理由卻回 rc=0（pm-conduct.md:95）。 | 核心-印 | 狀態面對現實是 GitHub 機械查詢。 |
| 31 | 級別下修時卡面須有需求方裁定；CLI 印出級別下降而無裁定。 | tier-rules.md:44-49; defect-path.md:64; pm-conduct.md:32 | — | 核心-印 | 降級唯一效果是繞過閘門；裁定欄有無可機械查。 |
| 32 | 停止裁定必含決策／原因／可證偽復活條件。 | closeout.md:22 | — | 核心-印 | 三格有無。 |
| 33 | 規格欄變更時 `spec_version` 必 bump；未 bump 印出。 | planning.md:10, 21 | — | 核心-印 | 欄位變了版本沒動是機械比對。 |
| 34 | commit trailer 下限：T0／T1 至少 `Requested-by` 與 `Implemented-by`；T2 以上四欄全加。 | defect-path.md:70-71 | — | 核心-印 | 未開卡時的唯一留痕；PR 上可印缺的 trailer。 |
| 35 | 需求站：進入＝清單項獲需求方點頭＋指派執行者；離開＝表單過 R1–R4 且 `open` 成功；產出＝開卡表單全欄＋收斂後的清單。 | requirement.md:10 | — | 階段檔 stage-requirement | 站的目標與出入口。 |
| 36 | 需求站加轉移「待確認 → 撤銷降回清單」（卡ID 保留、iteration 延續）；可判「現在不做」走撤銷，不走停止。 | requirement.md:13, 37 | — | 階段檔 stage-requirement | 站的轉移表。 |
| 37 | 需求站的交回物是表單文字，不是成品。 | requirement.md:16 | — | 階段檔 stage-requirement | 站內交回形狀。 |
| 38 | 需求方在需求站：決定哪個清單項升級（含缺陷開不開卡）、判 R1 痛點還成立嗎；不代填表單。 | requirement.md:16, 21; defect-path.md:27 | — | 階段檔 stage-requirement | 該站的角色做／不做。 |
| 39 | PM 在需求站：組派工包、判表單射程、跑 `open`、收斂清單；不判該不該做。 | requirement.md:22 | — | 階段檔 stage-requirement | 該站的角色做／不做。 |
| 40 | 執行者在需求站：填表單內容；不寫解法；不配卡ID。 | requirement.md:24 | — | 階段檔 stage-requirement | 該站的角色做／不做。 |
| 41 | 清單項與需求表單只寫可觀測現象（「X 指向 Y，但 Y 不存在」），不寫解法、不寫未量測的因果推論。 | requirement.md:35; list-intake-requirements.md:35-39 | 2026-08-26 兩張卡的身分欄寫成「怎麼判」與未量測的結構假設，兩張都鎖死射程、只能停卡重開（list-intake-requirements.md:41）。 | 階段檔 stage-requirement | 句子裡有沒有解法是 PM 判的流程項。 |
| 42 | 待審清單不佔看板欄位、不進盤點分母、不參與任何檢查；清單當墓地可接受。 | list-intake-requirements.md:17 | — | 階段檔 stage-requirement | 清單的定義句。 |
| 43 | 驗收條件逐條可追溯回痛點原文。 | requirement.md:34; planning.md:16, 26 | — | 階段檔 stage-requirement | 可追溯是內容判斷；規劃站 R3 引用此條。 |
| 44 | 級別取敏感面／可復原性／影響面三者最高，不取平均、不取多數、不按難度、估時或檔案數。 | requirement.md:40; tier-rules.md:40, 62; defect-path.md:49; pm-conduct.md:33 | — | 階段檔 stage-requirement | 級別在此站定，判準住此。 |
| 45 | 缺陷級別：已知 typo／文案無行為影響 T1；根因已知、局部、可逆、無紅線 T2；根因不明、跨檔、契約／資料／安全影響至少 T3；資料正確性紅線 T4；不得因「很小」略過風險判定。 | defect-path.md:51-56, 63 | — | 階段檔 stage-requirement | 級別表對缺陷的套用。 |
| 46 | 開不開卡不由級別決定；直接 commit 是不開卡時的合法路徑，不設級別門檻。 | defect-path.md:43-45, 73-75 | — | 階段檔 stage-requirement | 入口規則。 |
| 47 | 缺陷卡的重現步驟、預期 vs 實際、根因、回歸測試寫進核心痛點與驗收條件，不另立欄位。 | defect-path.md:31 | — | 階段檔 stage-requirement | 痛點寫法。 |
| 48 | 專案層對級別只能加嚴：可宣告某類工作至少 Tn 或在某級之上加閘門；不得下修最低閘門、不得新增比 T0 弱的級別、不得把框架層 T3／T4 改判更低、不得自創級別代號；沒有專案層檔＝沒有加嚴。 | tier-rules.md:27-33, 70-71 | — | 階段檔 stage-requirement | 級別判定處。 |
| 49 | 能力層級判準：純文字／格式／狀態同步→經濟型，語意會改規則時升級；一般規劃／實作／review→主力型，跨模組、未知根因或高風險升級；安全／金流／資料正確性→高階型＋跨家族查核＋人工 sign-off；部署／migration 異常→主力型，不可逆或根因不明升級；先選風險再選供應商；高能力模型不取代測試、平台閘門或獨立審核；不得因當下額度預先降級。 | MODEL_ROUTING.md:5-12, 14 | — | 階段檔 stage-requirement | 層級在開卡時填，判準住此。 |
| 50 | 研究站：產出＝可重跑的量測紀錄＋結論；進入＝階段計畫有列研究；離開＝可判定→規劃或執行，不可判定→結案／完成。 | research.md:10 | — | 階段檔 stage-research | 站的目標與出入口。 |
| 51 | 研究站加轉移「待確認 → 不可判定」「不可判定 → 結案／完成」；不顯著⇒不可判定；不可判定的結論不得被後續卡引為反證。 | research.md:13, 32 | — | 階段檔 stage-research | 站的轉移表與該狀態的引用規則。 |
| 52 | 研究站交回＝量測紀錄＋結論，討論形狀不是送審形狀；交回與查核之間插討論回合，需求方提問、執行者答，出口由討論定。 | research.md:16, 37 | — | 階段檔 stage-research | 站內流程。 |
| 53 | 需求方在研究站：提問、判夠了嗎；不要求附行動建議。 | research.md:21 | — | 階段檔 stage-research | 該站的角色做／不做。 |
| 54 | PM 在研究站：派工包含該卡與相關卡的既有留言；執行者研究前先讀該卡留言；PM 不判結論對錯。 | research.md:22, 38 | — | 階段檔 stage-research | 該站的角色做／不做。 |
| 55 | 執行者在研究站：量測、下結論、誠實標不可判定；不把不顯著寫成否定；不代規劃寫規格。 | research.md:23 | — | 階段檔 stage-research | 該站的角色做／不做。 |
| 56 | 查核者在研究站：只驗量測可重跑；不裁結論真值。 | research.md:24 | — | 階段檔 stage-research | 該站的角色做／不做。 |
| 57 | 高階型研究卡：執行者交可重跑 harness；查核者用它跑 ≥3 個不同族角度的對抗性反測（時間外／母體外／洩漏探針／重抽／規則邊界），不適用寫「不適用：<原因>」不硬湊；裁決寫每個反測結果（支持／推翻／未能檢定）。 | research.md:16, 24, 40; reviewer-conduct.md:31; executor-conduct.md:24 | — | 階段檔 stage-research | 只在研究站發生。 |
| 58 | 先量母體再下結論；不窮舉時說出母體多大、掃了多少，紅數是下界。 | research.md:27, 28 | — | 階段檔 stage-research | 結論寫法。 |
| 59 | 證不出來不寫成沒有。 | research.md:33 | — | 階段檔 stage-research | 結論寫法。 |
| 60 | 量測或設計前先搜既有解法（論文／GitHub／官方文件），列出搜過什麼。 | research.md:39 | — | 階段檔 stage-research | 研究站前置。 |
| 61 | 規劃站：產出＝規格（含 `spec_version`）＋驗收條件＋驗證項目＋（父卡）子卡切片與依賴序；進入＝需求或研究完成；離開＝規格過④；規格只能在規劃站改；T0／T1 跳過本站。 | planning.md:10 | — | 階段檔 stage-planning | 站的目標與出入口。 |
| 62 | 執行與審核的退回目的地＝規劃站。 | planning.md:13 | — | 階段檔 stage-planning | 轉移表入邊。 |
| 63 | 規劃站 ④ 有序：R1 上游產出還有效嗎 → R2 射程 vs 痛點 → R3 驗收逐條（可追溯、非零資訊、基線釘死）。 | planning.md:16 | — | 階段檔 stage-planning | 站內查核順序。 |
| 64 | 執行者（技術規劃者）在規劃站：寫規格、bump `spec_version`；不改痛點；不在未回寫下改已核可方向。 | planning.md:21 | — | 階段檔 stage-planning | 該站的角色做／不做。 |
| 65 | PM 在規劃站：判 R2–R3；不判技術取捨。 | planning.md:22 | — | 階段檔 stage-planning | 該站的角色做／不做。 |
| 66 | 需求方在規劃站：核可取捨與驗收；不寫規格。 | planning.md:23 | — | 階段檔 stage-planning | 該站的角色做／不做。 |
| 67 | 不拿全 repo 現況當本卡的標準。 | planning.md:27 | — | 階段檔 stage-planning | 驗收基線的寫法。 |
| 68 | 每個檢查先寫出什麼結果會推翻它；零資訊的檢查不列。 | planning.md:28 | — | 階段檔 stage-planning | 驗證項目的寫法。 |
| 69 | 間歇型缺陷預先登記可證偽預測；不以「重跑幾次沒再現」結案。 | planning.md:29; defect-path.md:93 | — | 階段檔 stage-planning | 驗證項目的寫法。 |
| 70 | 守衛基線釘死 SHA 字面，不動態算。 | planning.md:30 | — | 階段檔 stage-planning | 規格內容。 |
| 71 | 驗證項目逐項指定誰跑。 | planning.md:31 | — | 階段檔 stage-planning | 規格內容。 |
| 72 | 缺陷卡的驗證項寫回歸測試檔與測試名，不只寫「已加測試」。 | defect-path.md:92 | — | 階段檔 stage-planning | 驗證項目的寫法。 |
| 73 | 執行站：產出＝分支 SHA＋交付報告＋自測證據；進入＝規劃完成（T0／T1 直通）；離開＝交付報告過④→審核。 | implementation.md:10 | — | 階段檔 stage-implementation | 站的目標與出入口。 |
| 74 | 只推 commit 沒交付報告＝仍在進行中，不得轉待確認。 | implementation.md:16; executor-conduct.md:20 | — | 階段檔 stage-implementation | 站內交回定義。 |
| 75 | 執行者失聯：卡停在進行中；出口＝新 iteration 重做，或他人出「複驗報告」（逐字標非自評）。 | implementation.md:16; executor-conduct.md:32 | — | 階段檔 stage-implementation | 站內例外出口。 |
| 76 | PM 在執行站：組派工包、判報告完整性；不判碼對錯；不代寫執行者自評。 | implementation.md:22; executor-conduct.md:20 | — | 階段檔 stage-implementation | 該站的角色做／不做。 |
| 77 | 修缺陷必附回歸測試，且先看它紅再修綠。 | defect-path.md:90 | — | 階段檔 stage-implementation | 缺陷在執行站的做法。 |
| 78 | 審核站：產出＝結構化裁決；進入＝執行④過；離開＝APPROVE→合併（四停下條件內直行）、REQUEST_CHANGES→執行或退回規劃。 | review.md:10 | — | 階段檔 stage-review | 站的目標與出入口。 |
| 79 | 查核者（本站執行者）：self_run 實跑、findings、自己寫回裁決。 | review.md:16, 25, 38; reviewer-conduct.md:18 | — | 階段檔 stage-review | 該站的角色做。 |
| 80 | PM 在審核站：發派審詞、判裁決完整性；不判裁決對錯；不代轉錄。 | review.md:26 | — | 階段檔 stage-review | 該站的角色做／不做。 |
| 81 | 需求方在審核站：T4 卡 sign-off。 | review.md:27 | — | 階段檔 stage-review | 該站的角色做。 |
| 82 | 查核者的 self_run 與守衛在合併結果上跑，不在分支上。 | review.md:37; reviewer-conduct.md:36; planning.md:31 | — | 階段檔 stage-review | 只在審核站發生。 |
| 83 | 結案站：進入＝最後一個適用階段進入完成（入邊：審核 APPROVE、研究不可判定）；離開＝終態（完成／停止）＋封存。 | closeout.md:12-14, 19 | — | 階段檔 stage-closeout | 站的出入口；維護入邊見 #144。 |
| 84 | 結案站 ④＝需求方讀結案報告，確認後才轉完成，或退回補驗。 | closeout.md:25, 31; pm-conduct.md:54 | — | 階段檔 stage-closeout | 該站的角色做。 |
| 85 | 結案報告一屏內。 | closeout.md:30; pm-conduct.md:56 | — | 階段檔 stage-closeout | 報告長度是內容判斷。 |
| 86 | 合併不是結案。 | closeout.md:34 | — | 階段檔 stage-closeout | 站的定義句。 |
| 87 | 清單收斂核對：宣告涵蓋的清單項逐項確認、真解決才關。 | closeout.md:30, 37; requirement.md:31 | — | 階段檔 stage-closeout | PM 在結案站的做。 |
| 88 | 分支在終態刪除；保留不刪要寫明理由進卡面。 | closeout.md:35, 36 | — | 階段檔 stage-closeout | 一卡一分支的收尾。 |
| 89 | PM 只判流程（有沒有填、是不是結論句、有沒有列關鍵字），不判內容對錯。 | pm-conduct.md:26; list-intake-requirements.md:3, 14-15, 27, 39, 57 | — | 角色檔 role-pm | 跨階段的角色邊界。 |
| 90 | PM 不檢查自己的提案、表單與其他自產物。 | pm-conduct.md:27; requirement.md:22; list-intake-requirements.md:109 | — | 角色檔 role-pm | 跨階段；由誰檢查見「空洞」。 |
| 91 | PM 不代填、不代修、不代寫他人的產出或判定；列出問題（哪幾筆、各自證據）交還產出者；只修自己的產出物。 | pm-conduct.md:28, 31; closeout.md:30, 38; review.md:26; list-intake-requirements.md:77 | 需求方 2026-09-01 裁定（pm-conduct.md:31）。 | 角色檔 role-pm | 跨階段紅線。 |
| 92 | 未經需求方明確指示，PM 不得合併、部署、裁定、開卡、改射程、改需求方原文；一次授權不延伸到下一次，上一張卡的同意不適用於這一張。 | pm-conduct.md:39, 41 | — | 角色檔 role-pm | 跨階段紅線。 |
| 93 | 結案直行例外：APPROVE＋裁決完整性過 ⇒ PM 直行 merge→release→cleanup；四停下條件任一成立即停下請示：blocking finding 未 resolved／CI 非綠或 merge 後狀態不符預期／分支 BEHIND 且 `update-branch`（merge 非 rebase）衝突／T4 紅線卡。 | pm-conduct.md:43-52; closeout.md:25; review.md:10 | 需求方 2026-08-30 裁定（pm-conduct.md:43）。 | 角色檔 role-pm | 紅線的唯一例外，跨審核與結案兩站。 |
| 94 | 交付任何規劃產出物給查核者前，以同一份 R1–R4 表自審至少一輪；自審紀錄附進派審詞的已知未驗項。 | pm-conduct.md:22 | 2026-08-30 六份波 spec 零自審送審，4 blocking 中 2 筆自審可攔。 | 角色檔 role-pm | 跨階段自審義務。 |
| 95 | 收件時 R1–R4 有序；R1 不過不跑後面。 | pm-conduct.md:22 | — | 角色檔 role-pm | 跨階段查核順序。 |
| 96 | 派查核前初審：注意事項回應實質抽查（明顯敷衍、與報告他處矛盾者挑出）、每條 AC 有無著落；不判 `core_pain_resolved`、不取代查核。 | pm-conduct.md:30 | 需求方 2026-09-01 裁定。 | 角色檔 role-pm | 初審是 PM 動作，內容判斷。 |
| 97 | 只有 PM 跑 `move`；PM 是狀態的唯一 writer。 | pm-conduct.md:22 | — | 角色檔 role-pm | 誰跑是紀律，CLI 判不出角色。 |
| 98 | PM 兼任執行者：T0／T1 可兼；T2 以上不可兼。 | pm-conduct.md:33 | — | 角色檔 role-pm | 跨階段的角色分離線。 |
| 99 | 轉手任何 finding 前先驗：那份 artifact 是誰寫的、它要求的機制有沒有 writer。 | pm-conduct.md:66-70; review.md:31; reviewer-conduct.md:39 | 2026-08-28 PM 把自己寫的清冊 finding 轉給執行者要求重貼；同日推薦沒有 writer 的 `preflight-failed` 狀態。 | 角色檔 role-pm | 轉手是 PM 的主要動作。 |
| 100 | 回報需求方的數字附產生它的指令與 artifact；不回報自己心算的數。 | pm-conduct.md:72-74 | — | 角色檔 role-pm | 跨階段轉述紀律。 |
| 101 | 敘述不承載現況數字；數字只留閾值／裁定值、不變量與封閉集合基數、已釘 hash 的 artifact 基線三類；其餘改日期化歷史或量法＋artifact 指向；不用程度詞。 | pm-conduct.md:86-87 | 需求方 2026-08-31 裁定。 | 角色檔 role-pm | 文件與報告的書寫紀律。 |
| 102 | 自審紀錄只載指令與原始輸出，不載「全過／已檢查」等結論字樣。 | pm-conduct.md:89 | — | 角色檔 role-pm | 跨階段自審紀律。 |
| 103 | 停止自審的判準＝連續一整批零實質發現（只剩衛生級）；不用筆數遞減外推。 | pm-conduct.md:90 | 2026-08-31 自審批六零筆後，批七仍出三筆實質。 | 角色檔 role-pm | 跨階段自審紀律。 |
| 104 | 提案被推翻後不當場翻面；重新研究至少三輪（各須新量測或新母體）再給新建議。 | pm-conduct.md:98 | — | 角色檔 role-pm | 跨階段轉述紀律。 |
| 105 | 機制卡住先分「設計錯了還是我用錯了」；設計錯了就登記，不繞過、不補只為它成立的例外；不為讓舊卡通過放寬既有條文。 | pm-conduct.md:102 | 2026-09-02 PM 建議「`w2b.md` 維持現狀」與「改 AC＋開 FIX 卡」，需求方擋下。 | 角色檔 role-pm | 跨階段行為準則。 |
| 106 | 派審詞逐字寫出對查核者的全部要求；未寫的慣例視為不存在。 | reviewer-conduct.md:10; pm-conduct.md:108 | Codex 裁決沒寫派審詞明文要求的 session ID（pm-conduct.md:108）。 | 角色檔 role-pm | 派審詞的寫者是 PM。 |
| 107 | 同族第三張卡（或同族第三輪）出現時停手，改判是一根問題還是 N 個實例；是實例則先量母體、開一張窮舉卡，不開第四張；跳出法＝開放集合→封閉集合、追精確度→證明天花板。 | requirement.md:32; pm-conduct.md:122-126; planning.md:32 | 2026-08-28 一天開四張同族卡 `#165`→`#167`，全部由 PM 開出。 | 角色檔 role-pm | 開卡是 PM 動作，跨需求與規劃。 |
| 108 | 執行者：實作、自測、自評（失誤登記＋未驗清單）、交回交付報告；自評只有本人寫得出來。 | executor-conduct.md:18, 20 | — | 角色檔 role-executor | 角色本體。 |
| 109 | 執行者不 merge 自己的變更；不自審。 | executor-conduct.md:28; implementation.md:21 | — | 角色檔 role-executor | 跨階段紅線。 |
| 110 | 遇授權缺口停下，寫「阻塞發現」交 PM；不自行擴權、不開新卡。 | executor-conduct.md:29; implementation.md:21 | — | 角色檔 role-executor | 跨階段紅線。 |
| 111 | 射程擴大或發現未知根因⇒停下、級別當場升 T3 並上呈；不在原卡靜默改射程。 | defect-path.md:65 | — | 角色檔 role-executor | 跨階段紅線。 |
| 112 | 封閉值域只能由 owner 裁定擴張：枚舉／schema／白名單不夠用＝停下上呈；不自行增值、不重新解釋既有值；值域的字面定義處即其 owner。 | executor-conduct.md:30; tier-rules.md:71 | 2026-08-31 R15：inventory 自造三個白名單類被裁決退回。 | 角色檔 role-executor | 跨階段紅線。 |
| 113 | 實跑，不讀碼推論。 | research.md:29 | — | 角色檔 role-executor | 研究與執行共用。 |
| 114 | 開工與量測前先 fetch；量在 `origin/main`，不在本地工作樹。 | research.md:30; closeout.md:40; pm-conduct.md:76-80 | 2026-08-29 worktree 落後 `origin/main` 398 個 commit，第一次量出 4 個檔、重量是 9 個。 | 角色檔 role-executor | 誰量測誰適用。 |
| 115 | 驗證器 `import` 使用，不重打常數。 | research.md:31; implementation.md:31; executor-conduct.md:40 | — | 角色檔 role-executor | 研究與執行共用。 |
| 116 | 關鍵字沒命中不是證據；先讀 diff 或呼叫圖確認形狀。 | research.md:34; pm-conduct.md:96 | — | 角色檔 role-executor | 誰量測誰適用。 |
| 117 | 推翻要在宣稱自己的母體上做。 | research.md:35; pm-conduct.md:99 | 2026-08-29 斷言「Codex PM 沒有寫入通道」，實查 Codex 可跑 wfcli。 | 角色檔 role-executor | 誰量測誰適用。 |
| 118 | 「全部／全數」附由 artifact 自動產生的窮舉證據。 | research.md:36; implementation.md:37; executor-conduct.md:38 | — | 角色檔 role-executor | 交付紀律。 |
| 119 | 不截斷輸出；rc 分開取，不接管線。 | implementation.md:28; executor-conduct.md:39; pm-conduct.md:94; review.md:32; reviewer-conduct.md:37 | 同族三犯迄 2026-08-22，第三次吃掉 `wfcli release` 的 rc=5，把卡推進不可修復的非法終態。 | 角色檔 role-executor | 三角色共用的操作紀律（居所問題見「空洞」）。 |
| 120 | rc=0 不等於成功；判成敗看被改變的狀態。 | implementation.md:29; executor-conduct.md:39; pm-conduct.md:95 | `gh pr merge` 印出拒絕理由卻回 rc=0。 | 角色檔 role-executor | 同上。 |
| 121 | 宣告成功前先核那次執行的識別碼。 | implementation.md:30; executor-conduct.md:39 | — | 角色檔 role-executor | 交付紀律。 |
| 122 | 引用零命中／零失敗或做複驗前，先用會通過（會響）的樣本證明工具有效，附負控輸出。 | implementation.md:31; executor-conduct.md:40; pm-conduct.md:88 | 2026-08-31 P1-38 三輪：R14「裸現況數終掃 0 命中」是假陰性掃描器的假安心。 | 角色檔 role-executor | 交付紀律。 |
| 123 | 算術上不可能的結果最先響。 | implementation.md:32; executor-conduct.md:40 | — | 角色檔 role-executor | 交付紀律。 |
| 124 | 刻意行為就地留註解（刻意／為什麼／不得推出什麼）；寫在 commit 不算。 | implementation.md:33; executor-conduct.md:41 | — | 角色檔 role-executor | 交付紀律。 |
| 125 | 修過期引用後重掃自己新寫的引用。 | implementation.md:35 | — | 角色檔 role-executor | 交付紀律。 |
| 126 | 交付物寫事實不寫可變狀態；SHA 用 `rev-parse` 取不手打；「已 push」類狀態寫查詢方法。 | implementation.md:27, 36; executor-conduct.md:36 | — | 角色檔 role-executor | 交付紀律。 |
| 127 | 失誤登記、未驗清單與證據逐字轉錄，不摘要、不加緩和語。 | implementation.md:37; executor-conduct.md:37; review.md:34; reviewer-conduct.md:38; pm-conduct.md:97; closeout.md:25 | — | 角色檔 role-executor | 三角色共用的轉錄紀律（居所問題見「空洞」）。 |
| 128 | 查核者不代改被審分支；不裁研究結論真值；不動狀態面（裁決寫回除外）。 | reviewer-conduct.md:12; review.md:25, 35 | — | 角色檔 role-reviewer | 跨階段紅線。 |
| 129 | self_run 實跑，不只讀碼。 | reviewer-conduct.md:18; review.md:32 | — | 角色檔 role-reviewer | 角色本體。 |
| 130 | `core_pain_resolved` 是第一判準、具否決權：驗收全過但痛點未消 ⇒ REQUEST_CHANGES。 | review.md:33; reviewer-conduct.md:24 | — | 角色檔 role-reviewer | R3／R4 的內容判斷。 |
| 131 | 不用卡面沒有的標準。 | reviewer-conduct.md:25; review.md:25 | — | 角色檔 role-reviewer | 跨階段判準邊界。 |
| 132 | 基線用派審詞給的 merge-base SHA，不自己抄 `origin/main`。 | reviewer-conduct.md:35; review.md:30 | — | 角色檔 role-reviewer | 查核者側的對應義務（CLI 側見 #26）。 |
| 133 | 需求方裁授權缺口。 | implementation.md:23 | — | 角色檔 role-requester | 缺口可在任何站發生。 |
| 134 | 清單提案者與裁決者填身分三格：GitHub 帳號、session ID（Claude／Codex transcript 檔名的 id）、該則訊息定位（uuid／timestamp）；不填模型名、不填 AI 工具；PM 只判三格有沒有填，不核對；核對由需求方在本機 transcript 做。 | list-intake-requirements.md:85-97, 101; review.md:38; reviewer-conduct.md:20; pm-conduct.md:118 | GitHub `author` 恆為同一帳號（只有一個 token），身分訊號只剩自述（pm-conduct.md:118）。 | 模組(身分自述) | 只在需要跨實體身分驗證時存在。 |
| 135 | 同 root_cause_id 第三輪 ⇒ 不派第四輪，直接升級；root_cause_id 對照派審詞所列前輪，同根因沿用同字串。 | review.md:16, 36; reviewer-conduct.md:26 | — | 模組(升級梯) | 計數鏈。 |
| 136 | 純 governance／coordination／environment finding、planner 錯誤前提、等待外部 sign-off、重複同 SHA 的 review 不計入升級 attempt；已停止產出有效 open finding 的根因不再觸發；升級前先建 escalation-checkpoint。 | review.md:18-20; reviewer-conduct.md:28-30 | — | 模組(升級梯) | 計數鏈的例外表。 |
| 137 | PM 準備升級單（三次退回的逐字理由＋痛點原文＋四個值各自「若成立會是什麼證據」）交需求方四選一裁定；PM 不裁定；「退回無效」是裁定第四值，不是階段狀態。 | pm-conduct.md:22, 29; review.md:13, 27; reviewer-conduct.md:25 | — | 模組(升級梯) | 升級的出口。 |
| 138 | 派工包含 13 族踩坑清冊；交付報告含族清冊回應，「已檢查」裸寫、說明進 evidence，不升成「發現：」。 | implementation.md:16; executor-conduct.md:22 | — | 模組(13 族踩坑清冊) | 已定為模組。 |
| 139 | worktree 內 Edit／Write／server 路徑指向 worktree，不指 main checkout；一卡一 worktree 一 session。 | implementation.md:26; executor-conduct.md:31 | — | 模組(資源互斥檢查與 worktree 註冊) | 只在並行用 worktree 時存在。 |
| 140 | 並行共用 checkout 時逐檔 add，禁 `add docs/`。 | implementation.md:27 | — | 模組(資源互斥檢查與 worktree 註冊) | 只在並行共用時存在。 |
| 141 | 終態才釋放宣告的資源。 | closeout.md:36 | — | 模組(資源互斥檢查與 worktree 註冊) | 沒有互斥登記就沒有「釋放」。 |
| 142 | 部署站：通用狀態；先備份後驗證；產出＝部署事實（環境／時間／SHA／驗證）。 | deploy.md:9 | — | 模組(部署階段) | 已定為模組。 |
| 143 | 環境名枚舉與別名表只住資料庫契約一處。 | tier-rules.md:15-17 | — | 模組(部署階段) | 環境名只在部署情境有意義。 |
| 144 | 維護站：通用狀態＋運行中；轉移 完成→運行中、運行中→待辦、運行中→結案／完成（服務下線）；自迴圈、不主動離開。 | maintenance.md:9; closeout.md:14 | — | 模組(維護階段) | 已定為模組。 |
| 145 | 第二 PM 角色及其分工（PM 表單由第二 PM 查、清單條件 2 由第二 PM 收件、第二 PM＝Codex、原始輸出可見性未定）。 | requirement.md:23, 38; list-intake-requirements.md:107-119; pm-conduct.md:10, 104-118 | — | 砍 | 角色已裁撤；「PM 不檢查自己的產出」保留於 #90。 |
| 146 | 專案層注意事項居所契約（`P-` 前綴、累加不覆寫、只能加嚴、無檔＝沒有、有 `P-` 無 §5 拒收、reader 與 `--repo-path`、今日無消費端）。 | requirement.md:51-71; research.md:50-70; planning.md:43-63; implementation.md:47-67; review.md:48-68 | — | 砍 | 核心已定注意事項為單層清單；reader 段是舊 CLI 實作。 |
| 147 | 頁首「看板值仍為舊語彙（15 值）」註記。 | requirement.md:5; research.md:5; planning.md:5; implementation.md:5; review.md:5; closeout.md:5; deploy.md:5; maintenance.md:5 | — | 砍 | 過渡註記。 |
| 148 | 「目標、尚未生效——機制生效於 W3′」註記。 | closeout.md:44; deploy.md:15; maintenance.md:15; defect-path.md:99 | — | 砍 | 過渡註記。 |
| 149 | 結案進入子句自 canonical 搬入的來歷與舊文互斥說明。 | closeout.md:16-17 | — | 砍 | 來歷敘述。 |
| 150 | defect-path 的來歷、首版更正、來源標注、`prose_number_scan` 語料說明、`BUGS.md` 另議。 | defect-path.md:6-7, 33-41, 58-59, 77-86, 95 | — | 砍 | 裁定過程與來歷。 |
| 151 | 「升級觸發的權威居所＝templates/review-escalation.md §3–§4；不一致以該契約為準」指路句。 | review.md:18, 20; reviewer-conduct.md:28, 30 | — | 砍 | 對其他檔的轉指；規則本體已列於 #136。 |
| 152 | 正文不得出現事件 marker 前綴字面（doctor 全文子字串比對，出現即隔離整卡）。 | reviewer-conduct.md:40 | — | 砍 | 只對舊 CLI（doctor）有意義。 |
| 153 | `wfcli review --validate-only` 先自檢。 | reviewer-conduct.md:18 | — | 砍 | 舊 CLI 動詞。 |
| 154 | 踩坑族名以 `import pitfalls.roster_for()` 取。 | executor-conduct.md:22 | — | 砍 | 舊 CLI 實作。 |
| 155 | PM 評估執行者提出的 CLI 拒收點提案（判準＝拒絕訊息附一條跑得出的補救）。 | pm-conduct.md:22 | — | 砍 | 新 CLI 不擋只印，拒收點設計不存在。 |
| 156 | 同一輪多欄位修訂合併為單次 amend。 | pm-conduct.md:93 | 2026-08-30 實測 #177 十二條 amend 中六條可合併。 | 砍 | 舊 CLI 動詞（amend／Log）。 |
| 157 | 第二 PM 實證、Codex 寫入權盤點、wfcli 無角色概念、「只查核不動狀態是紀律不是機制」。 | pm-conduct.md:106-116 | — | 砍 | 現況盤點敘述。 |
| 158 | 規劃顆粒度三層（重／中／輕；試跑慣例非定案制度）。 | planning.md:33 | — | 砍 | 自陳非定案制度，非可重複的檢查。 |
| 159 | tier-rules「刻意不放級別表副本」的理由段與兩層 DI 表。 | tier-rules.md:24-29, 35-39 | — | 砍 | 理由敘述；判準句已併入 #44、#48。 |
| 160 | MODEL_ROUTING 頁首（每季更新、不用 `latest`）、「各專案記載 model ID／成本／fallback」、claim 事件封存註。 | MODEL_ROUTING.md:3, 12, 14 | — | 砍 | 供應商名單維護說明與過渡註記。 |
| 161 | 各檔「適用時機／非射程」的結構句。 | executor-conduct.md:8-12; reviewer-conduct.md:8; pm-conduct.md:8-16; tier-rules.md:8-18; defect-path.md:11-19; list-intake-requirements.md:8-17 | — | 砍 | 檔案結構描述；其中含規則者已各自列入（#42、#89、#128）。 |
| 162 | 缺陷卡的回應清冊取其實際所跑階段的編號清單。 | defect-path.md:101 | — | 砍 | 與「缺陷＝一般卡」（#1、#5）重複。 |
| 163 | session ID 為何不是自述、身分格為何存在、跨家族查核者核不到。 | list-intake-requirements.md:99, 103 | — | 砍 | 理由敘述；規則本體在 #134。 |

## §5 編號注意事項逐條判定（65 條）

砍的理由只用三種：`與條文重複`／`只對舊 CLI 有意義`／`單一事故的敘述而非可重複的檢查`。

| 編號 | 判定 | 去向／理由 |
|---|---|---|
| F-需求-01 | 保留 | #1 |
| F-需求-02 | 保留 | #21 |
| F-需求-03 | 保留 | #2 |
| F-需求-04 | 保留 | #12（與清單條件 3 合一） |
| F-需求-05 | 保留 | #19（宣告）＋#87（核對） |
| F-需求-06 | 保留 | #107 |
| F-需求-07 | 保留 | #13 |
| F-需求-08 | 保留 | #14（≥1）＋#43（可追溯） |
| F-需求-09 | 保留 | #41 |
| F-需求-10 | 保留 | #4（鏈深）＋#17（路由欄） |
| F-需求-11 | 合併進另一條 | 併入 §2 轉移句 → #36 |
| F-需求-12 | 合併進另一條 | 併入 pm-conduct「不檢查自己的提案」→ #90；「第二 PM」字面隨 #145 砍 |
| F-需求-13 | 保留 | #20 |
| F-需求-14 | 保留 | #16（三子問欄）＋#44（取最高） |
| F-需求-15 | 保留 | #15 |
| F-研究-01 | 保留 | #58 |
| F-研究-02 | 合併進另一條 | 併入 F-研究-01 → #58 |
| F-研究-03 | 保留 | #113 |
| F-研究-04 | 保留 | #114 |
| F-研究-05 | 保留 | #115 |
| F-研究-06 | 合併進另一條 | 併入 §2 轉移句 → #51 |
| F-研究-07 | 保留 | #59 |
| F-研究-08 | 保留 | #116 |
| F-研究-09 | 保留 | #117 |
| F-研究-10 | 保留 | #118 |
| F-研究-11 | 合併進另一條 | 併入 §3 交回句 → #52 |
| F-研究-12 | 合併進另一條 | 併入 PM 角色列 → #54 |
| F-研究-13 | 保留 | #60 |
| F-研究-14 | 合併進另一條 | 併入 §3 高階型反測句 → #57 |
| F-規劃-01 | 合併進另一條 | 併入 F-需求-08 → #43 |
| F-規劃-02 | 保留 | #67 |
| F-規劃-03 | 保留 | #68 |
| F-規劃-04 | 保留 | #69 |
| F-規劃-05 | 保留 | #70 |
| F-規劃-06 | 保留 | #71（指定誰跑）；「在合併結果上跑」半句併入 F-審核-08 → #82 |
| F-規劃-07 | 合併進另一條 | 併入 F-需求-06 → #107 |
| F-規劃-08 | 砍 | 單一事故的敘述而非可重複的檢查（自陳「試跑慣例⛔ 非定案制度」，沒有可對照的檢查動作） |
| F-執行-01 | 保留 | #139（模組） |
| F-執行-02 | 保留 | #140（逐檔 add，模組）＋#126（rev-parse） |
| F-執行-03 | 保留 | #119 |
| F-執行-04 | 保留 | #120 |
| F-執行-05 | 保留 | #121 |
| F-執行-06 | 合併進另一條 | 併入 F-研究-05 → #115 |
| F-執行-07 | 保留 | #122 |
| F-執行-08 | 保留 | #123 |
| F-執行-09 | 保留 | #124 |
| F-執行-10 | 保留 | #125 |
| F-執行-11 | 保留 | #126 |
| F-執行-12 | 保留 | #127；「全部附窮舉證據」半句併入 F-研究-10 → #118 |
| F-審核-01 | 保留 | #26（CLI 算並印）＋#132（查核者用它） |
| F-審核-02 | 合併進另一條 | 併入 pm-conduct 四問 2 → #99 |
| F-審核-03 | 保留 | #129；「rc 分開取」半句併入 F-執行-03 → #119 |
| F-審核-04 | 保留 | #130 |
| F-審核-05 | 合併進另一條 | 併入 F-執行-12 → #127 |
| F-審核-06 | 保留 | #128 |
| F-審核-07 | 保留 | #135（模組） |
| F-審核-08 | 保留 | #82 |
| F-審核-09 | 保留 | #134（身分自述，模組）＋#79（自己寫回） |
| F-結案-01 | 保留 | #86 |
| F-結案-02 | 合併進另一條 | 併入 F-結案-03 → #88 |
| F-結案-03 | 保留 | #88（分支）＋#141（其他資源，模組） |
| F-結案-04 | 保留 | #87 |
| F-結案-05 | 合併進另一條 | 併入 pm-conduct 不代修 → #91 |
| F-結案-06 | 保留 | #30 |
| F-結案-07 | 合併進另一條 | 併入 F-研究-04 → #114 |

## 缺陷路徑（defect-path.md）的位置

- 它不是階段：檔內沒有自己的目標／進入／離開／轉移表，§五自陳「本檔⛔ 不是階段檔」（defect-path.md:101）；它的每一條都落在既有站上。
- 它是流程（橫切）：入口（#1、#2、#46）在需求站前；痛點與級別寫法（#45、#47）在需求站；回歸測試名與可證偽預測（#69、#72）在規劃站；先紅後綠（#77）在執行站；未開卡留痕（#34）在卡外。
- 該進核心的三條：`無 bug 專屬卡種`（#5）、`留痕走狀態面不另開 log`（#11）、`未開卡走 commit trailer 下限`（#34）。其餘分住各站。
- 階段計畫值域不該新增「缺陷」值：缺陷卡跑的是一般站；把它放進值域會回到 `templates/bug-workflow.md` 的獨立卡種模型。

## 空洞

- 部署站注意事項 0 條（deploy.md:11 自陳刻意留空）；只有「先備份後驗證」一句紀律。
- 維護站注意事項 0 條（maintenance.md:11）；只有轉移表。
- PM 自產物（清單提案、開卡表單、派審詞、結案報告）由誰查核：第二 PM 砍掉後沒有承接者；pm-conduct.md:27 與 list-intake-requirements.md:109 只寫「另一個 PM」。
- 需求站 R1 由需求方（requirement.md:16, 21）與已定案「PM 判 R1 前提」對不上。
- 三角色共用的操作紀律（#113–#127 的實跑、fetch、不截斷、rc、負控、逐字轉錄）在「一角色一檔」下沒有單一居所；本表暫住 role-executor。
- 級別表本體（T0–T4 各級最低閘門）與紅線定義：tier-rules.md:14, 35 自陳不放副本、指向 canonical；這批檔只有判準句與缺陷套用表。缺陷 T4 列指向 `templates/statistical-redline.md`（defect-path.md:56），框架層紅線定義在本批檔內沒有。
- 專案層級別數字未裁定（tier-rules.md:66-71）。
- 需求方角色檔內容薄：本批檔只給裁授權缺口（#133）、T4 sign-off（#81）、讀結案報告（#84）、升級裁定（#137）、決定升級清單項（#38）。
- 研究站討論回合（research.md:16）的出口「由討論定」，沒有寫怎麼記錄、誰收口。
- 待審清單的 CLI 觸點：收件由 PM 手動 `gh issue create`（list-intake-requirements.md:75），五動詞裡沒有收件動詞；#12 的「印缺欄」要掛在哪個動詞上未定。
- 結案站「停止」的裁定由誰做：closeout.md:22 只寫裁定內容，未寫角色。
- 一卡一分支在本批檔內沒有明文；executor-conduct.md:31 只寫「一卡一 worktree 一 session」（模組情境）。
- 資源宣告欄位（已定核心）在本批檔內沒有寫法；只有 closeout.md:36「終態才釋放資源」。
- 執行站與審核站的「退回上一站」條件只在 planning.md:13 以「主要目的地」一句帶過，沒有寫什麼情形退規劃、什麼情形退需求。

## 未驗

- 未實跑任何 CLI；所有「CLI 可機械檢查」的判定是對五動詞（`open`／`move`／`notes`／`brief`／`snapshot`）能力的推測，尤其 #31、#33（沒有 edit 動詞，欄位變動只能在下一次動詞呼叫時比對）。
- 未讀 `AI_WORKFLOW.md` 本文；被本批檔引用的 canonical 節次（§0、§2.9、§2.11、§3、§3.2、§4.3、§5、§6、§6.1、§6.4.2）內容未核，只取本批檔的轉述。
- 未讀 `templates/review-escalation.md` §3–§4；#136 只依 review.md:18-20 與 reviewer-conduct.md:28-30 的轉述。
- 未讀 `docs/research/WORKFLOW-REDESIGN-2026-08-30.md`；list-intake-requirements.md:111 與 tier-rules.md:66-68 對它的引用未核。
- 來歷欄只取文中明寫者，未查 git log／blame。
- F-規劃-08 的砍理由套的是第三種的後半句（非可重複的檢查），不是嚴格的「單一事故敘述」。
- 核心-硬擋與核心-印的邊界（#4 鏈深、#8 iteration、#11 狀態面、#31 降級）依「該欄位是否由 CLI 持有」判，未經需求方確認。
- 級別表判準與能力層級判準（#44–#49）暫住 stage-requirement；五桶中沒有「核心條文」桶，需求方若要另立核心定義檔，這幾列要搬。
- #12 把清單收件四欄與 F-需求-04 開卡查重合為一欄，假設兩者是同一份留痕；若開卡時要再搜一次，需拆回兩列。
- #97「只有 PM 跑 move」與 #7「move 寫四欄」拆成紀律與機械兩列；是否應合併由重寫者裁。
