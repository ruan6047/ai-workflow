# #24 WF-RESOURCE-WRITESET1 資源宣告的互斥語意：寫入集相交、封閉 path namespace、symlink 與 revision 釘選
- state: closed  created: 2026-08-11T04:52:58Z  closed: 2026-08-12T16:18:00Z
- url: https://github.com/ruan6047/ai-workflow/issues/24
- comments: 24

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code
- 執行：待指派　查核：跨家族查核（契約本體，須走 PR）
- Initiative：—　spec 基線：自 ai-workflow#16 切出（需求方 2026-08-11 裁定縮小 #16 射程）。基準內容＝#16 設計文件 §7.2 於 SHA 2d361303ce438c6fecf475b2aaa1fcbc06518dc9 的狀態，該節已歷 R4／R5／R6／R7 四輪跨家族查核（R5-001 連四輪未閉環）。需求方已裁定採「階層路徑包含比對」而非「禁止目錄宣告」，理由是只有目錄宣告能表達「我會在這裡新增檔案」，逐檔宣告的摩擦會造成少宣告。#16 縮為框架卡後只保留「狀態機假設 assign 的守衛等於寫入集互斥」，機制本體歸本卡。
- DB：db_scope=none
- 服務的原始目標：讓 assign 的資源守衛真的等於寫入集互斥，且任何無法安全判定的情形一律拒絕派工而非放行。

## 簡介
<!-- card-brief:begin -->
定義 assign 的資源守衛真正等於寫入集互斥所需的語意：相交＝正規化路徑相等或其一為祖先目錄並以路徑邊界判定（templates/ 撞 templates/a.md、不撞 templates2/a.md）、封閉 path namespace（拒收 ..／glob／絕對路徑／跨 repo，且拒收發生在 open／amend 而非派工時）、symlink 與 realpath containment、revision 釘選加原子鎖解 TOCTOU、兩階段落地。**適用時機**：兩張卡宣告的路徑字面不同卻會改到同一份檔案；或要查「為何採階層路徑包含比對而非禁止目錄宣告」的裁定依據時。⛔ 非射程：本卡只交 docs/WF_RESOURCE_WRITESET1.md 與測試矩陣定義，resources.py／assign_cmd.py 的實作歸衍生卡且須待 aiwf#21 釋放該檔。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：canonical AI_WORKFLOW.md:145 要求「共享可寫資源必須宣告並互斥」、control-plane-contract.md:49 用的詞是「比對本卡寫入集 × 現役卡寫入集」；但 resources.find_conflicts 只做完全相同字串比對。目錄宣告對其子檔案不提供任何保護，symlink 可讓字面不同的兩個宣告指向同一實際檔案——派工守衛因此是宣稱而非保證。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:docs/WF_RESOURCE_WRITESET1.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 定義相交：兩個 file: 資源相交當且僅當正規化路徑相等或其一為另一之祖先目錄，以路徑邊界判定（templates/ 撞 templates/a.md，不撞 templates2/a.md）。
- [ ] 封閉 path namespace，不留「其餘」格：repo 根相對路徑；拒收 ..、glob、絕對路徑、~、跨 repo 路徑；結尾斜線＝目錄宣告；位元組精確比對且大小寫不敏感檔案系統上只差大小寫者視為相交。拒收發生在 open／amend 而非派工時。
- [ ] symlink：拒收任一路徑分量或自身在目標 revision 中 git 模式為 120000 的宣告；assign 另對實際 worktree 做 realpath 解析（含未追蹤 symlink）與 containment 檢查，交集比對取字面與 realpath 的聯集。路徑尚不存在時解析到最深既存祖先。
- [ ] revision 釘選與 TOCTOU：assign 先把 worktree HEAD 解析為完整 40 hex 記為 resource_check_rev 並寫入 assign 事件；解析、檢查、寫入三者在同機原子目錄鎖內完成，寫入前重讀 HEAD，已變動則放棄本次派工。
- [ ] 兩階段落地且兩階段都機械，不得有任何一刻依賴人工紀律：立即階段在 find_conflicts 加樸素前綴比對（過度拒絕但 fail-closed）；目標階段才做邊界判定。

## 驗證

- [ ] 定義回歸測試矩陣須含：templates/ vs templates2/ 邊界、..／glob／絕對路徑拒收、大小寫差異視為相交、tracked 與 untracked symlink 各自的攔截、realpath 逸出 worktree 的拒絕，以及 ai-workflow#16（file:templates/）與 #22（file:templates/review-escalation.md）這組真實反例。**矩陣在本卡定義，執行歸衍生實作卡**——assign_cmd.py 與 resources.py 的改動須待 ai-workflow#21 釋放 assign_cmd.py。
- [ ] 立即階段的過度拒絕行為須在矩陣中明確固定，避免日後被當成 bug 修掉。
- [ ] 跨家族查核確認與 canonical AI_WORKFLOW.md:145 及 control-plane-contract.md:49 的寫入集語意一致。
## Log

- 2026-08-11T12:52:56+08:00 open by Claude Opus 5@Claude Code；owner 待指派；iteration 0。
- 2026-08-11T20:16:17+08:00 amend by wf-cli（op 84823404）→ 驗證：原值「[ ] 回歸測試須含：templates/ vs templates2/ 邊界、..／glob／絕對路徑拒收、大小寫差異視為相交、tracked 與 untracked symlink 各自的攔截、realpath 逸出 worktree 的拒絕，以及 ai-workflow#16（file:templates/）與 #22（file:templates/review-escalation.md）這組真實反例。；[ ] 立即階段的過度拒絕行為須有測試明確固定，避免日後被當成 bug 修掉。；[ ] 跨家族查核確認與 canonical AI_WORKFLOW.md:145 及 control-plane-contract.md:49 的寫入集語意一致。」→ 新值「定義回歸測試矩陣須含：templates/ vs templates2/ 邊界、..／glob／絕對路徑拒收、大小寫差異視為相交、tracked 與 untracked symlink 各自的攔截、realpath 逸出 worktree 的拒絕，以及 ai-workflow#16（file:templates/）與 #22（file:templates/review-escalation.md）這組真實反例。**矩陣在本卡定義，執行歸衍生實作卡**——assign_cmd.py 與 resources.py 的改動須待 ai-workflow#21 釋放 assign_cmd.py。；立即階段的過度拒絕行為須在矩陣中明確固定，避免日後被當成 bug 修掉。；跨家族查核確認與 canonical AI_WORKFLOW.md:145 及 control-plane-contract.md:49 的寫入集語意一致。」；理由 本卡資源僅含自身設計文件，而原驗證條文要求實跑回歸測試；且 assign_cmd.py 目前由 #21 佔用。改為在本卡定義測試矩陣、執行歸衍生卡。
- 2026-08-11T20:18:49+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code；分支worktree claude/WF-RESOURCE-WRITESET1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-resource-writeset1；交付狀態 🚧進行中。
- 2026-08-11T20:33:29+08:00 handoff by wf-cli → owner 跨家族查核（契約本體，須走 PR）；iteration 0；SHA 0ae8a1171376842e7ef6b8a57a40bff2d57ee134；證據 docs/WF_RESOURCE_WRITESET1.md 交付（設計／契約，無實作）。五條驗收逐條落 §2／§3＋§4／§5／§6／§8；三條驗證落 §9 矩陣（43 列＋三項列舉式斷言）、§8.5、§11.1。對基線 #16 §7.2 有四處實測修正＋三處補完（§11 逐條列表），其中立即階段的字面規格實測為 fail-OPEN（5 個漏放案例）而非其宣稱的 fail-closed。所有數字由探查程式對真實 repo 與 Project #4 產生，§9.6 的調查程式已內嵌於文件且經驗證可從文件原樣抽出重跑（輸出：規則 A 同 repo 0 對；B／C 各 1 對＝#16 × #22 真實反例）。cli/ 未動，pytest 292 passed。新增裁定：宣告路徑存在性不硬拒、強制機械提示（§7）。§12.1 提出但不裁定一項超出驗收射程的邊界發現（無法解析的宣告目前 fail-open，實測 2 張活卡）。。
- 2026-08-11T21:21:05+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 跨家族查核（需求方於對話中轉貼原文；無 receipt marker，來源不可驗證）；core_pain_resolved no；self_run 4 項；findings 1 項（blocking 1）；attempt WF-RESOURCE-WRITESET1-e0-0ae8a1171376842e7ef6b8a57a40bff2d57ee134。
- 2026-08-11T21:33:49+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 1；SHA 0ae8a1171376842e7ef6b8a57a40bff2d57ee134；證據 R1-001（blocking，critical）：§5 將「無法解析資源宣告」列為不處理情形，與卡面「任何無法安全判定的情形一律拒絕派工」直接矛盾，構成 fail-open。查核者重跑文件內嵌探針，INIT-GAME-RECAP 與 ML-FIELD-OF1 兩張已指派活卡仍無法解析。已驗證正確的部分：B ⊇ C 對已正規化 file: 路徑成立、258 組合枚舉 b_misses_c=0、templates/ 與 templates2/a.md 不相交。首輪查核，無 escalation checkpoint。。
- 2026-08-11T22:04:53+08:00 handoff by wf-cli → owner 跨家族查核（契約本體，須走 PR）；iteration 1；SHA cb6028fc9f704459fd68456491bbf7238f8e10be；證據 R2：R1-001 已處置（文件 573→954 行，僅動 docs/WF_RESOURCE_WRITESET1.md）。先查證根因再修法：兩張不可解析卡不是宣告缺漏或解析器太嚴，而是 OPS-STATE-PLANE-MIG1 遷移寫出自我標示為「未正式宣告」的佔位區塊——有 fenced JSON、無 resource-claims sentinel。PM 獨立核對 cpbl-analytics#60／#66 的 body 屬實，且 #66 佔位 db_scope 為 write。故裁定解析器不放寬：放寬後 30/33 張會解析「成功」並得 resources=[]，把「寫入集未知」靜默轉譯成「寫入集為空」，等於用安靜的 fail-open 換掉吵鬧的 fail-open。修法為 assign 對別卡解析失敗一律拒絕派工並輸出 card id 與錯誤原文，移除 skipped_unparseable；上層加貫穿全檔的不變式 I（守衛管線每站對無法安全判定的輸入只能以阻擋或一次性具名留痕豁免結束），附 S1–S10 逐站處置表，其中 S7（git ls-tree 查詢失敗 vs 查詢成功為空）與 S8（realpath OSError）為新抓出的同型漏洞。豁免三要件：具名（逐張 card id、拒收萬用字元、不寫持久設定）、可稽核（錯誤原文與 resource_check_rev 入 assign 事件、陳舊豁免即錯誤）、到期（母體為 33 個 ID 的原始碼字面清單、單調收縮、硬性 sunset 2026-09-30）。執行者草稿中自行抓到並修掉一個洞：原以「body 帶 MIG1 marker」為謂詞式母體，但 body 可手改故不封閉，已改為字面常數清單並把 E1 強度誠實降為「不可能靜默發生」。一併處理三件自標事項：§4.2 repo 限定詞改為放行方向規則、別卡歸屬判不出來退回視同同 repo 比對（原探針把它算成不相交，同病灶落在證據程式裡）；立即階段 fail-OPEN 與 glob 誤拒 41 檔收攏進 §8.9。§8.2 原「258 組合」來自不可重跑的 session 腳本，本輪以內嵌 §9.8 取代（語料不同故 276），已在 §13 明說為刻意替換。執行者自承六個未關的洞，含豁免本身即真放行、E3 到期後全 Project assign 硬停、宣告×實際寫入脫鉤完全未解。。
- 2026-08-12T00:56:19+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（留有 receipt marker，但採單行格式、不合 handoff-contract.md §3.1.2 的多行語法；PM 未能重算 report_sha256）；core_pain_resolved no；self_run 5 項；findings 1 項（blocking 1）；attempt WF-RESOURCE-WRITESET1-e0-cb6028fc9f704459fd68456491bbf7238f8e10be。
- 2026-08-12T01:19:29+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 2；SHA cb6028fc9f704459fd68456491bbf7238f8e10be；證據 R3：R2-001（major，blocking）——§9.7b 第 719-720 行把含反斜線的 re.match 正則直接放進 f-string expression，從文件原樣抽出第 694-733 行執行即 SyntaxError；故第 739-761 行的 33 張封閉母體、母體外 0、sentinel 失敗 0、db_scope 分佈與字面清單全部不是可重跑 artifact，而那正是 §8.7.2 與 §8.8.1 至 E1 的必要證據。R1-001 已 resolved。查核者另作三項跨卡裁決（皆非 blocking）：#23 的 A2/A3 屬定義域不相容、本卡 namespace 只規範卡面 file: 宣告不是 CLI 路徑正規化器，建議在 §3.1 或 §4 加一句明示不涵蓋 CLI 引數；repo 限定詞屬座標補全非 canonical 語意擴充；豁免與 sunset 滿足非靜默例外要求且文件正確描述了全 Project 停機的半徑。無 escalation checkpoint（R1-001 已 resolved、新 finding 根因不同）。。
- 2026-08-12T01:41:46+08:00 handoff by wf-cli → owner 跨家族查核（契約本體，須走 PR）；iteration 2；SHA 3cd2865780dcd54b1a6ab30f0497726d9c0a20cb；證據 R3：R2-001 已修，且根因比查核者所述更深。不是語法瑕疵而是版本相依的隱形失敗——cli/pyproject.toml 的 requires-python 下限是 3.11，而含反斜線的正則放進 f-string 取值部在 3.12 以前是 SyntaxError（PEP 701 之前）；執行者在 3.14 上寫、在 3.14 上驗，查核者用系統 3.9.6 撞到。PM 已獨立重現：舊版經 /usr/bin/python3（3.9.6）ast.parse 拋出與查核者逐字相同的錯誤並指到同一條 re.match；新版 parse OK；新版以 sed 原樣抽出實跑輸出與報告逐字相符。修法：含反斜線正則提升為模組層 re.compile 常數。結構性處置＝新增 §9.9 探針自檢（純文件內、無網路、無 wf_cli 依賴、退出碼即裁決）：抽出全部 python 圍籬 → 逐一編譯 → 在 3.12+ 以 AST 掃 FormattedValue 原始碼片段補上 3.12 前才存在的閘門 → 執行不 import wf_cli 者。imports_wf_cli 以 AST 判 import 而非字串比對，否則 §9.8 語料裡的 cli/src/wf_cli/ 會讓離線探針被靜默跳過。PM 已實跑自檢：交付版 4 區塊、違例 0、PASS、exit 0；反向驗證跑在修正前檔案上 FAIL 兩筆（只抽到 3 個區塊、第 720 行 f-string 取值部含反斜線），而且是在 compile() 會通過的 3.14 上抓到——該自檢確實能捕捉當前直譯器碰不到的版本相依失敗。§9.6 新增第 57 列要求衍生卡把自檢落成 repo 內腳本掛 CI 並以兩種變異測試釘住（本卡只宣告一個檔案故不落地腳本）。⚠️ 執行者主動回報一件由 PM 行為造成的證據失效：§9.7 的 B／C 由 1 對變 0 對，因為 PM 於 2026-08-12T00:13:42 以 amend op df7e0929 把 file:templates/ 移出 #16 宣告。上一版寫的「不變的是結論：規則 B／C 找到 #16 × #22」把線上狀態誤當不變量——與 R2-001 同族（把會變的東西當證據）。§1.2 與 §9.7 已改寫：被斷言的不變量只剩「對固定輸入 A 判不相交而 B／C 判相交」與「現行守衛從未判出任何 file: 階層相交」，#16 × #22 降為歷史舉證。母體 33 個 ID 逐字未變、順序未變；唯一變動是 item 96→99，係 PM 新開的三張卡（smoke／#30／#31）。跨卡界線澄清已寫入：§3.1 標題改為「只管卡面 file: 資源宣告，不管 CLI 路徑引數」並加告示框，§12 新增第 7 項非目標互指，另修 §4.2 的錯誤引用（§9.7→§9.7b）。執行者自承四個未關的洞，其中第 2 項最該看：自檢射程只到內嵌四支探針，§1.1／§4.1／§3.2／§3.3 的數字仍來自一次性 session 腳本，與 R2-001 同族只是還沒人踩到——該界線是執行者自己畫的，查核者可以不接受。。
- 2026-08-12T07:09:08+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（收據 issuecomment-5259838968，多行格式合規；PM 依其取材規則回讀重算 report_sha256=a7d93646… 一次相符。PM 另將 scope_outside_findings 的巢狀 mapping 轉為序列 mapping 以通過解析器，字串內容未變）；core_pain_resolved no；self_run 6 項；findings 1 項（blocking 1）；attempt WF-RESOURCE-WRITESET1-e0-3cd2865780dcd54b1a6ab30f0497726d9c0a20cb。
- 2026-08-12T07:18:27+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 3；SHA 3cd2865780dcd54b1a6ab30f0497726d9c0a20cb；證據 R4：R3-001（major，blocking，portable-probe-selfcheck-incomplete-grammar-gate）——§9.9 把 FLOOR 固定為 3.11 並宣稱檢查跨直譯器可攜性，但 950-961 行唯一針對舊版的補充檢查只搜尋 f-string 取值部反斜線，969-974 行仍以執行中的直譯器 ast.parse 編譯。若 CI 以 3.12+ 執行，任何其他 3.12+ 新語法都會編譯通過且不被該掃描命中，卻無法在宣稱下限 3.11 執行。R2-001 判 resolved。disposition：改為以 Python 3.11 直譯器實際編譯每個抽出區塊，或使用可證明覆蓋完整 3.11 語法的版本化語法閘門；並在 §9.6 第 57 列加入一個非 f-string 的高版本語法變異證明該閘門會非零失敗。收據合規（多行格式，PM 回讀重算一次相符）。無 escalation checkpoint（R2-001 已 resolved、新 finding 根因不同）。。
- 2026-08-12T08:53:58+08:00 handoff by wf-cli → owner 跨家族查核（契約本體，須走 PR）；iteration 3；SHA 75555caa848bd5f4f717a6205f5b584a8dbacec9；證據 R4：兩件事。X1（跨卡對帳）——§3.1 界線告示與 §12 第 7 項曾把 CLI 路徑正規化歸屬給 #23，而 #23 於 d824d16 已明文拒絕承接；aa1b47d 改為「本卡不涵蓋 → #23 已裁定其六個承接動詞不需要 → 目前無人擁有 → 需要者須自行舉證並開卡」，並把 #23 的判準（分類鍵＝對事件內容的貢獻）與其不可行性論證寫進告示，使誤引者拿得到判準而非只拿到「沒人管」。R3-001 的處置——75555ca 修 §9.9 自檢的五個缺陷，其中三個由 #23 把該自檢原樣指向自己的檔案時發現：(a) except BaseException 把 SystemExit(0) 當拋錯（乾淨結束的探針被判 FAIL）、(b) imports_wf_cli ⇒ 需 gh ⇒ 只編譯的推論不成立（只做 argparse 內省的探針被靜默跳過而自檢仍 PASS）、(c) len(probes) < 4 是寫死常數。執行者另自行挖出 (d) __name__ 方向反了與 (e) sys.argv 未隔離——(e) 在 R4 從未浮現只因被 (b) 擋在執行之外，一個缺陷遮住另一個。修法：退出碼 0 視為乾淨結束、KeyboardInterrupt 往外拋、改為 probe-requires 顯式登記且未登記一律執行（預設從跳過翻成做事）、probe-blocks 逐檔登記且缺登記 fail-closed、__name__ 改 __main__ 並隔離 sys.argv。PM 獨立複驗全部五項，並實測 ast.parse(feature_version=(3,11)) 確實接受 R2-001 那段而真實 3.9.6 拒收（故第 2 條路不可行的反例成立）、PEP 695 變異新閘門攔舊閘門放行、FLOOR 不可得時 fail-closed。跨檔一般性：自檢指向 #23 的文件四支探針全部實際執行、僅缺登記一筆 FAIL，#23 補一行後違例 0 PASS。執行者自陳 R4 的六條宣稱有三條在別人文件上不成立，並列出兩條尚未修的一般性假設（工作目錄、行程狀態不隔離），歸因為「量尺對但只在自己的樣本上量」。escalation checkpoint 見同日留言：兩條件皆不成立 decision=continue，同時記錄第三個 attempt 前的漏建（PM 合規缺口，不追溯補建），並請查核者裁示三個 root_cause 是否應合併為「宣稱大於證據」同一家族——若合併即 3／3、下一輪強制 escalate。。
- 2026-08-12T09:26:41+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（收據 issuecomment-5260903533，多行格式合規；PM 已回讀重算 report_sha256=ac25a726… 相符）；core_pain_resolved yes；self_run 4 項；findings 1 項（blocking 1）；attempt WF-RESOURCE-WRITESET1-e0-75555caa848bd5f4f717a6205f5b584a8dbacec9。
- 2026-08-12T09:31:50+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；iteration 4；SHA 75555caa848bd5f4f717a6205f5b584a8dbacec9；證據 R5：R4-001（major，blocking，claim-exceeds-evidence）——§9.9.1-D／§13 只用文字要求採用者的 python 區塊唯讀，程式卻對所有未標 probe-requires 的區塊 exec(compile(...))。PM 已獨立重現：建一份只有 probe-blocks: 1、唯一區塊為 pathlib.Path('side-effect-created').write_text(...) 的文件，自檢實際建立該檔案並回 PASS、違例 0、退出碼 0。該風險是 R6 修法自己引入的（預設由跳過翻成執行），執行者於 §13 自陳四已寫明「R4 的錯誤推論順帶當了一層安全網，翻成預設執行後那層網沒了」——查核者把那句自陳變成可執行的利用。disposition 兩條：改成可強制的隔離邊界（每探針子行程且限制檔案系統／網路／狀態面），或收窄契約為不執行外部文件並 fail-closed；不得以作者自我宣告的 probe-requires／唯讀承諾作為安全邊界。R1-001／R2-001／R3-001 三項查核者皆判 resolved。⚠️ escalation checkpoint 見同日留言：查核者裁定該三項併入 claim-exceeds-evidence，加上 R4-001 同家族已跨四個 attempt，第一條件成立故 decision=escalate；需求方裁定 continue、維持同執行者。下一輪若再出現同家族即第五次。查核者另於 scope_outside 指出：§3.1 對 #23 d824d16 的引用稱「交付版」而交付已前移（PM 已揭露的輕微陳舊引用，非 blocking）；§9.6 的八個變異不是八個獨立機制而是不同分支案例，文件未作錯誤宣稱。。
- 2026-08-12T10:02:14+08:00 handoff by wf-cli → owner 跨家族查核（契約本體，須走 PR）；iteration 4；SHA 3e45646d1f9fdfd1c8f1bc1ff777a5b6e8d4653f；證據 R6：R4-001 已處置，選查核者給的第 2 條——收窄契約為不執行外部文件。執行者先自行重現該利用（75555ca 版對利用文件 PASS 且 side-effect-created 被建立），再判定第 1 條在本卡射程內做不出來且理由不是逸出寫入集：子行程只解決狀態污染不限制檔案系統；/usr/bin/sandbox-exec 實測確實擋下寫入但 macOS 專屬且已 deprecated，同機無 bwrap／firejail，落地會退化成「有沙箱就跑、沒有就跳過」＝R3-001 的形狀；Python 層假沙箱可被 os／ctypes／subprocess 繞過。處置：移除全部執行路徑（AST 確認腳本內無 exec／eval／compile／__import__），撤除 probe-self／probe-requires 兩個標記，不提供任何執行開關。PM 獨立複驗三項：同一份利用文件在 R5 版下 side-effect-created 不存在、裁決行自述「未執行任何區塊」；#23 的 50021ce 仍 exit 0 四區塊全過；本檔仍 PASS。執行者明確指出收窄不是把利用文件判 FAIL——沒有程式能可靠認出「這段碼會寫檔」，判 FAIL 又是用猜的代替判定；收窄要做的是讓那件事無從發生，故 §9.6 第 57c 列的斷言是「副作用檔案不存在」而非退出碼。誠實標記：本輪讓本卡探針執行覆蓋歸零，是能力的減少而非「更安全所以更好」；「§9.8 今天是否仍 PASS」現只由一次人工執行佐證，在衍生卡掛 CI 前是操作紀律不是機械保證。歸因：R6 的跨檔樣本全是善意文件，而同輪把預設翻成執行——「當一個機制會對別人的輸入做事，就得用對方是惡意的來量」。escalation checkpoint 見同日留言：第一條件仍成立（claim-exceeds-evidence 跨四個 attempt），decision=escalate，沿用需求方同日對同一組事實的 continue 裁定；若本輪查核產生第五次同家族 finding 須重新裁定。⚠️ 對已結案的 #23：其 §4.4.1 兩項具名適配失去標的，需 PM 處理歸屬。。
- 2026-08-12T11:06:12+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5261716854 多行格式合規，PM 依其取材規則回讀重算 report_sha256=46b1a470… 相符；PM 僅將 observations 的裸字串序列轉為 - observation: 形式以通過解析器，字串內容逐字未變）；core_pain_resolved yes；self_run 5 項；findings 1 項（blocking 0）；attempt WF-RESOURCE-WRITESET1-e0-3e45646d1f9fdfd1c8f1bc1ff777a5b6e8d4653f。
- 2026-08-12T11:13:13+08:00 handoff by wf-cli → owner —（結案）；iteration 4；SHA 3e45646d1f9fdfd1c8f1bc1ff777a5b6e8d4653f；證據 跨家族查核（GPT-5@Codex 子代理）於 3e45646d 判 APPROVE、core_pain_resolved=yes、self_run 5 項、findings 1 項（R6-001，minor，非 blocking，attribution=coordinator）。收據 issuecomment-5261716854 多行格式合規，PM 依其取材規則回讀重算 report_sha256=46b1a470… 相符（第一次錨點抓到取材規則散文內的同名字面而失敗，改以規則所指的「下一個」delimiter 後即一次相符）。R4-001（claim-exceeds-evidence，major blocking）判 resolved：移除對外部文件執行的能力後，利用文件仍 PASS 但不再建立 side-effect-created。未產生第五次同家族 finding，escalation 第一條件未再觸發。

以 PR #40 併入 main，merge commit 3e47838c69e7de49bafe0fb515364e91536962e9。刻意不 rebase：分支基於 7451b72、main 已前進三個 merge，但 git merge-tree 實測無衝突且分支相對基線只新增一個檔案，rebase 會使被審 SHA 3e45646d 失去可達性而 review event 正指向它。已於併後驗證 git merge-base --is-ancestor 3e45646d origin/main 成立。此處與 dispatch-package.md:31「分支更新一律本地 rebase ＋ --force-with-lease」的關係：該條管的是需要更新分支的情形，本次不需要更新，而「被 review event 指名過的 SHA 不可變」是更強的不變量——此張力已寫入 WF-24-EVIDENCE-STRENGTH1（#11）的 B 條款。

R6-001 未由本卡關閉且不應由本卡關閉（修改已結案的 #23 逸出本卡寫入集）。需求方 2026-08-12 裁定另開卡修正 #23 的 docs/WF_EVENT_IDEMPOTENCY1.md §4.4.1——該處仍把 SystemExit(0) 與 probe-requires 兩項適配寫成共用自檢的現役機制，而本卡本輪已撤除它們。選擇改檔案而非在 Issue 留註記的理由：該檔是讀者會經過的平面，Issue 留言不是，與 PM 判 dispatch-package.md 不適合承載規則是同一條論證。。
- 2026-08-13T00:17:21+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code PM；iteration 4；SHA 0ea7abad670681b708f4fbbe15526008b448abe3；證據 ⚠️ 前向更正：把交付狀態自 🏁完成 倒退為 📦已合併，以還原至可清理的合法態。成因與處置同 WF-RESOURCE-BLOCK-ANCHOR1：終態早已寫入而收尾第 1-3 步一步未做，cleanup.classify_state 判 illegal_terminal_before_cleanup、守衛拒絕動作。不追溯改寫既有事件，Log 依序記「終態寫入 → 更正倒退 → 清理 → 終態重寫」。。
- 2026-08-13T00:17:45+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code PM；iteration 4；SHA 0ea7abad670681b708f4fbbe15526008b448abe3；證據 收尾：碼早已在 main（分支 tip 3e45646 為 origin/main 祖先，PM 已複驗）。前一筆事件已倒退為 📦已合併，本次由守衛執行第 1-3 步後才寫終態。；收尾清理已完成（worktree 與本地／遠端分支皆已不存在）。
- 2026-08-26T22:20:22+08:00 amend by wf-cli（op 2997e8da）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:e645cef210340a868089080739d75cd0748ec7ab51441c9456bea23aa47c89cd (774 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5253376047 · 2026-08-11T12:48:05Z

## 派審：WF-RESOURCE-WRITESET1

審核對象 **`ruan6047/ai-workflow#24`**（T3，設計／契約卡）。⚠️ 不是 `cpbl-analytics#24`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-resource-writeset1
分支：claude/WF-RESOURCE-WRITESET1
被審 SHA：0ae8a1171376842e7ef6b8a57a40bff2d57ee134
基線：origin/main 7451b72ba7679893043950d71bad9642665e25da
iteration：0（首次查核）
```

```bash
git rev-parse HEAD && git diff --stat origin/main    # 唯一異動 docs/WF_RESOURCE_WRITESET1.md
```

本卡由 [#16](https://github.com/ruan6047/ai-workflow/issues/16) §7.2 切出，承接 `R5-001`（在 #16 上**連四輪未閉環**）。資源宣告只有自身文件，`cli/` 未動；**測試矩陣在此定義、執行歸衍生實作卡**（`assign_cmd.py` 由 #21 佔用中）。

### 本卡最值得先看的是：它推翻了 #16 §7.2 的三處結論

這三處都是**實測而非推論**，且都翻轉了我（PM）在 #16 寫下的東西：

1. **立即階段的字面規格其實是 fail-OPEN，不是它宣稱的 fail-closed** —— 5 個漏放案例（`./`、`//`、大小寫、祖先未標目錄、純大小寫差異）。**而且 #16 舉的那個過度拒絕例（`templates/` 誤撞 `templates2/a.md`）在其自身規格下根本不成立**，因為結尾斜線擋住了 `startswith`。修法：先正規化再做字串前綴。
2. **「拒收 glob」照直覺實作會誤拒 41 個現存檔案** —— cpbl 的 Next.js 動態路由 `[sno]`／`[id]`，而 `UX-WINPROB-CURVE-MIGRATE1` 已宣告 `file:web/` 涵蓋它們。收窄為只拒 `*`／`?`。
3. **比對集合跨 repo** —— Project #4 含 ai-workflow 10 張＋cpbl 44 張非終態卡，`file:` 是 **repo 相對路徑卻在同一平面比**。**今日跨 repo 誤判為 0 是運氣不是設計**（兩 repo 皆有 `docs/`）。補 repo 限定詞＋DraftIssue fail-closed。

另補完 Unicode 正規化（25 個現存 CJK 追蹤路徑）與空路徑（`file:.` 會靜默鎖死全 repo）。

### 存在性檢查的裁定（§7）：不硬拒，但強制機械提示

決定性理由很直接：**硬拒會拒絕掉定義這條規則的卡自己**——`docs/WF_RESOURCE_WRITESET1.md` 在 #24 開卡當下不存在，#23／#25 同樣如此。

更根本的論證：**存在性不是區分好壞宣告的判準**。#13 的 `file:cli/wfcli` 與本卡的宣告在「路徑不存在」上**完全相同**，區分兩者的是意圖，而意圖不可機械判定。且不存在的宣告是**過度**宣稱而非少宣稱，方向本就安全。

提示則是免費的：§5.2 的逐分量走查**本來就要跑**，「還有幾個分量沒走到」是副產品。以 #13 重放：`cli/wfcli` 的最深既存祖先是 `cli/`，其下無 `wfcli` → **提示會響，PM 不必在三天後人工發現**。

另裁定一個確實該硬拒的子情形（blob 之下開子路徑），並**誠實聲明它抓不到 #13**；#13 真正的病灶是宣告與實際寫入雙向脫鉤，對應機制列入 §12.3 建議另開卡、**未夾帶進本卡**。

### 本輪請攻擊這六點

1. **§9.6 的內嵌調查程式**（文件內可原樣抽出重跑）。執行者稱輸出與文中宣稱一致：規則 A（現行）同 repo **0 對**——守衛是睡著的；規則 B／C 各 **1 對**，正是 #16 × #22。**請自行抽出重跑**，並確認它不是恆真（前有先例：本 repo 出現過「空集合讓 `all()` 為真」的假 OK）。

2. **43 列矩陣是否為真實輸入空間。** 這是本卡最強的宣稱。**#23 的 768 組就被判為只是「縮約後的投影空間」**——請用同一標準檢視：43 列的參數軸有沒有漏掉會影響相交判定的維度？

3. **§3.1 的十一條規則表宣稱「無其餘格」。** 請構造第十二種路徑。

4. **§8.2 的 `B ⊇ C` 證明。** 立即階段（樸素前綴）必須是目標階段（邊界判定）的**超集**，才能保證過渡期只會過度拒絕而不會漏放。**請獨立驗證這個包含關係**——它是「兩階段都機械且都 fail-closed」的全部依據。

5. **repo 限定詞是否為語意擴充。** 執行者主動標出：§4 若被判為語意擴充，應退回另走契約 PR，**他不自行認定**。請裁定。

6. **§12.1 提出但不裁定的邊界**：無法解析的宣告目前**靜默 fail-open**（實測兩張活卡 `INIT-GAME-RECAP`、`ML-FIELD-OF1`；本卡自己 `assign` 時就印出該警告）。這與卡面「服務的原始目標」寫的「任何無法安全判定的情形一律拒絕派工」**直接衝突**，但超出五條驗收射程。**請判斷這個處理方式**（明列供裁定、未納入矩陣、未指派衍生卡）是否恰當。

### 執行者主動揭露的一次自查修正

> 初次用 `git ls-files | grep -P '[^\x00-\x7F]'` 探查非 ASCII 路徑，得到「兩 repo 皆無」的**錯誤**結論——`git ls-files` 預設對非 ASCII 做 C-style 引號。改用 `-c core.quotePath=false` 後查出 25 筆，**§3.3 因此從「不需要」翻轉為「需要」**。

**這是一個工具預設值造成的假陰性。** 請留意文件中是否還有其他依賴 shell 探查結果的結論。

### 其他

- 本卡為設計卡，**§9 矩陣未被執行**（卡面已明訂執行歸衍生卡）。§10 註明 `resources.py` **無活卡佔用**，故立即階段可先行落地。
- **明確不涵蓋**：派工後才建立的未追蹤 symlink、跨主機併發 assign（需遠端 CAS）。
- 執行者為 Claude Opus 5@Claude Code 的子 agent，**查核者須為不同模型家族**。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態。留言紀律：**不得讓任何一行以 `<!--` 緊接事件 marker 前綴起始**。

> **留 receipt marker 不違反上述紅線**（留言不改 Project 狀態）。若留收據，**請一併載明取材規則**。

**輸出**：依 `templates/review-prompt.md` §5 結構化區塊，`core_pain_resolved` 與 `self_run` 必填。


## Comment 5253727464 · 2026-08-11T13:21:06Z

<!-- wf-review-event:v1 card_id=WF-RESOURCE-WRITESET1 source_sha=0ae8a1171376842e7ef6b8a57a40bff2d57ee134 attempt_id=WF-RESOURCE-WRITESET1-e0-0ae8a1171376842e7ef6b8a57a40bff2d57ee134 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-RESOURCE-WRITESET1`　attempt_id：`WF-RESOURCE-WRITESET1-e0-0ae8a1171376842e7ef6b8a57a40bff2d57ee134`
- 查核者：跨家族查核（需求方於對話中轉貼原文；無 receipt marker，來源不可驗證）　escalation_epoch：0
- source_sha：`0ae8a1171376842e7ef6b8a57a40bff2d57ee134`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-11T21:21:05+08:00

### self_run（查核者實跑）

- `重跑 docs/WF_RESOURCE_WRITESET1.md 內嵌探針（現役卡資源宣告解析）`
  - 仍列出兩張已指派活卡未能解析：INIT-GAME-RECAP、ML-FIELD-OF1。
- `對已接受且正規化的 file: 路徑驗證 B ⊇ C 關係`
  - 關係成立。
- `枚舉 258 個有限組合`
  - b_misses_c=0。
- `檢查 templates/ 與 templates2/a.md 的不相交處理`
  - 符合文件定義，不相交。

### findings（1，其中 blocking 1）

- **WF-RESOURCE-WRITESET1-R1-001**　severity=critical　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`unparsable-resource-declaration-fail-open`
  - evidence：docs/WF_RESOURCE_WRITESET1.md:550-564 明確將「無法解析資源宣告」列為不處理情形。 這與卡面原始目標「任何無法安全判定的情形，一律拒絕派工」直接矛盾。 實際重跑文件內嵌探針，仍列出兩張已指派活卡未能解析：INIT-GAME-RECAP、ML-FIELD-OF1。 若這些卡被略過，寫入集衝突檢查可能把一張活卡視為不存在，導致並行派工。
  - disposition：未解析資源宣告必須 fail-closed，阻擋派工並顯示 card id 與解析錯誤； 若確有例外，必須設計具名、可稽核、具到期條件的例外機制，不可靜默忽略。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5253755520 · 2026-08-11T13:23:40Z

## PM 註記：本輪裁決的轉錄邊界

本輪裁決由**需求方於對話中轉貼查核報告原文**，查核者無 `wfcli` 寫入通道，故由 PM 逐字轉錄進唯一寫入通道。以下三件事屬於轉錄的已知限制，先寫明再談內容：

**一、無 receipt marker，來源不可驗證。** 報告未附 `report_sha256` 收據，PM 無法以雜湊證明轉錄內容與查核者實際產出逐位元組相同。可驗證的只有：轉錄後的 `evidence`／`disposition` 是報告散文的逐句搬移，未增刪判斷。

**二、schema 欄位由 PM 指派，非查核者填寫。** 原報告是散文，未提供 `severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id`。這四欄是 PM 依報告文字判定後填入的。**其中 `root_cause_id` 會影響 escalation 三次門檻的計數**——若查核者本人對根因家族的劃分與 PM 不同，門檻的觸發時點就會不同。異議請直接提出，PM 不代查核者堅持。

**三、`blocking` 的分界採用報告自己的用語。** 報告中標為「Blocking」者記 `blocking: true`，標為「非阻擋」者記 `blocking: false`。

被審 SHA 已由 PM 獨立核對：worktree HEAD 與報告所列短 SHA 相符，非陳舊派工。


## Comment 5255485376 · 2026-08-11T15:49:57Z

## PM：五張卡同時送審前的跨卡對帳

本則同時貼在 #21／#22／#23／#24／#25。五張卡本輪都改完並各自通過自己的驗證，但**它們彼此的介面沒有被任何一方檢查過**——每張卡的執行者都只看自己的射程。以下是 PM 在送審前做的交叉檢查，逐項附重現方式。

**這些不是 finding。** PM 不是查核者，以下只是**指定查驗項**：把 PM 觀察到的矛盾指出來，由各卡的查核者判斷它是不是問題、屬誰的問題。PM 刻意不代任何一方修正——#23 §10 明文寫著「刻意不猜測 #24 會怎麼改」，我現在替它填上就是把設計判斷從查核者手上拿走。

### 檢查方法

- **寫入集**：以 #16 §7.2 裁定的**階層路徑包含**語意（正規化路徑相等或其一為另一之祖先目錄），對 Project #4 全部 27 張有資源宣告的活卡做兩兩比對。**不是**現行 `resources.py` `find_conflicts` 的逐字串比對——後者的不足正是 #24 的射程。
- **設計面**：逐一驗證各卡對其他卡寫下的明示假設，以及「同一個物件被兩張卡從不同方向改動」的情形。

---

### 一、寫入集：四組相交，其中一組現在就成立

| 撞的兩張 | 相交處 | 狀態 |
|---|---|---|
| **#22（🚧進行中）× #16（⏸阻塞）** | `templates/review-escalation.md` ⊂ `templates/` | **現在成立** |
| `WF-22-CLI4`（📥Backlog） | `cli/` ⊃ #21 與 #25 的**每一個**檔案 | 潛伏 |
| `WF-CLI-TIER-MUTATION1`（📥Backlog） | `cli/src/wf_cli/` ⊃ #21 與 #25 多數檔案 | 潛伏 |
| `WF-24-EVIDENCE-STRENGTH1`（📥Backlog）× #16 | `templates/dispatch-package.md` ⊂ `templates/` | 潛伏 |

**第一列是 PM 的違反，先說清楚。** 我今天派 #22 時，#16 正持有整個 `templates/`。依 #16 §7.2 自己的裁定，那次 `assign` 應該被擋；沒被擋是因為 `find_conflicts` 現行只做逐字串比對。此條件先前已查證並記錄（`amend` op d32f8a3a），不是新發現——但它現在是**「正在設計互斥語意的那批卡自己違反該語意」的活體樣本**，且是在真實流程中自然發生的，不是構造出來的。

`WF-22-CLI4` 宣告整個 `cli/` 這件事值得單獨看：它一旦被派工，#21 與 #25 就全數動不了；反過來說，#21／#25 在途期間 `WF-22-CLI4` 也不可派。目錄級宣告與檔案級宣告混用的代價，在這裡是可量化的。

**指定查驗項（#24）**：文件的立即階段與目標階段規則，套在上表這四組真實資料上，各自會得到什麼結果？§8.5 釘住的「立即階段獨有的過度拒絕 10 對」是否涵蓋這幾組？

---

### 二、#23 §10 的四項假設，A2 與 A3 現在可以判定，而且都不成立

#23 §10 把對 #24 的依賴寫成四項待驗假設，明文「刻意不對齊，讓差異在查核時暴露」。**兩張卡都交付了，所以現在可以驗——結果是負的。**

**A3 失敗，而且是域不相容，不是覆蓋不足。**

#24 §3.1 規則 1 定義封閉 namespace 為「卡所屬 **repo 根**的相對路徑」，規則 2 拒收以 `/` 起始者、規則 3 拒收以 `~` 起始者、規則 4 拒收任一分量為 `..` 者。

而 #23 §4.4 分類器 `PATH` 集合的七個參數（`--worktree`、`--repo-path`、`--config`、`--input`、`--out-dir`、`--spec-dir`、`repo_root`）是 **CLI 引數**，實務上多半是絕對路徑——本專案的派工詞逐輪都寫 `--repo-path /Users/ruanruan/Dev/ai-workflow`。**這些字串在 #24 的規則 2 下會被逐一拒收。**

兩者的定義域不同：#24 管的是**卡面宣告字串**，#23 要的是**命令列引數**。A3 寫成「是否涵蓋全部七個參數」，隱含了兩者同域的前提，而該前提不成立。

**A2 也不成立。**

#24 §3.1 規則 8 明文「宣告以位元組原樣**儲存**；**比對**時 casefold」，規則 9 為「**比對前**做 NFC」。也就是 `K(r)` 是**比對鍵**，不是儲存形式；且 #24 從不解析 cwd（一律 repo 根相對）、也從不解析 symlink（§5 直接拒收）。它提供的是**集合成員判定**，不是 A2 要求的「同一邏輯路徑在不同 cwd、不同 symlink 解析狀態下產生同一個字串」。

**A1 成立**（#24 對無法解析者確實 fail-closed），但附帶一個具名豁免（`--ignore-unparseable`，33 張母體，sunset 2026-09-30）——該豁免處理的是**別卡宣告解析失敗**，與 A1 所問的**路徑正規化**不同域，請查核者確認 A1 問的是不是它該問的那件事。

**後果**：依 #23 §10 自己的降級規則，路徑型別應落回 §4.2 收尾規則（該動詞退出冪等保護、stderr 明示）——而且是**現在就該落**，不是繼續掛在 §10 當待驗假設。

**指定查驗項（#23）**：§4.1 的路徑型別列是否應直接改寫為降級後的形式？§10 的呈現方式是否應從「假設待驗」改為「已驗、A2／A3 不成立」？
**指定查驗項（#24）**：是否應明文宣告本卡的封閉 namespace **不涵蓋 CLI 引數**，以免其他卡再度誤引？

---

### 三、#25 與 #23 從兩邊改同一個動詞，互不知情

#25 本輪把破壞性收尾接上 `handoff --next-stage release --cleanup`。
#23 §7.1.2 的逐動詞稽核判 **`handoff` 的首寫不合格**（首寫是 owner 欄位，非載荷可攜），並據此判定該動詞的 E1 不成立。

PM 以 `grep` 核對兩份文件：**#25 全文未出現 `#23`、`event_id`、「冪等」；#23 全文未出現 `#25`、`release`、`cleanup`。** 兩張卡在同一個動詞上從相反方向動手，而彼此的文件都沒有對方。

具體後果（PM 逐行追過 `handoff_cmd.py` 的效果順序）：`release --cleanup` 成功路徑為 `owner` → `交付狀態` → `最後交接` → `iteration` → Issue body Log。**清理已完成、owner 已寫、但在 Log 寫入前崩潰**時，事件流上沒有任何能辨識這次寫入的記號——那正是 #23 E1 要解決的東西，而 #23 判定 `handoff` 不具備。

#25 的 resume 是**觀測式**的（重讀當下事實），所以不會重複刪除，這一點是安全的。但狀態面會停在「終態已寫、Log 缺行」的組合，而兩張卡都沒有在處理它。#25 §9 自承的第 2 項（effect writer 回報成功後未回頭重讀狀態面）與此同族但不同一件事。

**指定查驗項（#25）**：接線後 `handoff` 的首寫不自描述，是否使 #25 §9 第 2 項的殘留風險升級？卡面是否應引用 #23 §7.1.2 並標為外部相依？
**指定查驗項（#23）**：§7.1.2 判 `handoff` 不合格時，`handoff` 尚無破壞性效果；#25 落地後該判定的**後果嚴重度**是否改變？§11「在 A′ 落地前這三個動詞的 E1 不成立」是否需要加註破壞性路徑？

---

### 四、#22 的新出口，回溯涵蓋了今天兩個 checkpoint 的觸發成因

#22 本輪在 `review-escalation.md` §4 新增 `defer_cause: instruction-omitted`——「派審指示漏了要求查核者逐項回報前輪 finding 的閉環狀態」。

**今天 #21 與 #22 各自的 escalation checkpoint，觸發成因正是這個。** 兩次都是 PM 的派審詞缺漏（見 `#issuecomment-5253853989`、`#issuecomment-5255216570`，兩則都已載明歸因）。

這構成一個要請查核者特別看的形狀：**本卡的交付物，為本卡自己的 escalation 觸發提供了出口。**

減輕因素有兩個，請一併評估是否足夠：§4 第 2、3 款要求 `deferred_by` 逐字等於卡面「需求：」欄帳號，且不得等於本卡當前 owner 或本 epoch 任一 reviewer——**裁定者必須是需求方**，執行者不能自行 defer。以及「不得連續 defer」未放寬。

但執行者自承的洞 3 指出：**沒有任何檢查會去讀 `defer_ruling_url` 指向的那則指示、確認它真的漏了那一節。** 成因在機械上退化為「從封閉列舉挑一個」。

**指定查驗項（#22）**：`instruction-omitted` 的必要條件是否足以防止它成為通用免責？第 2、3 款排除了 owner 與 reviewer，但**未排除 Coordinator**——而缺漏正是 Coordinator 造成的；`deferred_by` 須為需求方是否已足夠隔離？

---

### 五、#22 卡面驗證條文與交付的落差（需要需求方裁定，非查核者可獨斷）

#22 執行者回報：卡面的兩項驗證條文（deferred 出口使 R4 前不強制、條件 1 在 R8 失效）**在 #16 的忠實事件流上不成立**，原因是 #16 有三處換號重開（R1-002→R2-001、R1-006→R2-002、R4-001→R5-001），依「六格的前提是穩定 `finding_id`」不構成處置。執行者未補造 defer 使其通過，改以「#16 的穩定 id 最小改寫」承擔該兩項，並明確標為構造。

**這是誠實的處置，但它使卡面驗證條文與實際被驗證的對象不再是同一個東西。** 依既有紀律，改動驗收／驗證條文是 PM 走 `amend`、不是執行者；而是否接受這個替代承擔，是需求方的判斷。**PM 刻意不先 `amend`**——先改條文再送審，等於讓卡面去追交付，那是倒過來的。

**指定查驗項（#22）**：「穩定 id 最小改寫」是否為該兩項驗證條文的正當替代？若否，該兩項應判為未滿足（`attribution: planner`，卡面條文本身建立在錯誤前提上）。

---

### PM 已獨立複驗的事項（不構成背書，只是把可機械核對的部分先做掉）

- 五張卡本輪變更的檔案**全部落在各自資源宣告內**；`test_commands_mocked.py`（#21 持有）未被 #25 觸碰。
- 測試：#21 `437 passed`、#25 `367 passed`、#22 replay `44/44`＋`cli` 292 passed（與基線同）；#23／#24 為設計卡，內嵌探針可原樣重跑。
- #21 的 R5-001 攻擊獨立重現：查核者的 `U+02B0`／`U+0378` 兩案例現皆 `ambiguous`，另測 ZWSP／私用區 `U+E000`／emoji／反斜線亦 `ambiguous`，單條對照仍 `matched`。
- #25 的 TOCTOU 守衛獨立突變：把二次確認的 verdict 強制為放行，**8 個測試轉紅**（含該 TOCTOU 回歸與狀態面測試），斷言非空；worktree 已還原乾淨。
- #24 的兩張不可解析卡（`cpbl-analytics#60`／`#66`）body 已由 PM 直接讀取核對：確為 MIG1 佔位區塊（有 fenced JSON、無 sentinel），且 `#66` 的佔位 `db_scope` 為 `write`。
- #22 的 fixture 已對原始留言 `5248665281` 核對：`deferred_findings` 逐字只有兩筆，未被補造。


## Comment 5255924445 · 2026-08-11T16:29:39Z

## 派審：#24 `WF-RESOURCE-WRITESET1` R2

⚠️ 審核對象是 **`ruan6047/ai-workflow#24`**，**不是 `cpbl-analytics#24`**。工作目標 repo 是 `ai-workflow`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-resource-writeset1
分支：claude/WF-RESOURCE-WRITESET1
被審 SHA：cb6028fc9f704459fd68456491bbf7238f8e10be
基線：origin/main 0d4d282
iteration：1
```

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-resource-writeset1
git rev-parse HEAD && git status --short && git diff --check
git diff 0ae8a11..cb6028f -- docs/WF_RESOURCE_WRITESET1.md   # 573 → 954 行
```

本卡是**權威設計文件**，沒有實作。三支內嵌探針可從文件中原樣抽出重跑（§9.7、§9.7b 需網路，§9.8 離線）。

### 一、複驗 R1-001，但重點在**修法方向**而不是修了沒有

執行者先查證根因再修法，結論是：那兩張不可解析卡**不是**宣告缺漏、不是格式舊、也不是解析器太嚴，而是 `OPS-STATE-PLANE-MIG1` 遷移寫出**自我標示為「未正式宣告」的佔位區塊**（有 fenced JSON、無 `resource-claims` sentinel）。實測 96 張卡中 33 張如此，**帶 sentinel 卻仍失敗 0 張**。

由此裁定**解析器不放寬**：放寬後 30/33 張會解析「成功」並得 `resources: []`，把「寫入集未知」靜默轉譯成「寫入集為空」——**用安靜的 fail-open 換掉吵鬧的 fail-open**。

PM 已獨立核對 `cpbl-analytics#60`／`#66` 的 body，確為該形狀，且 `#66` 的佔位 `db_scope` 是 `"write"`。

**請攻擊這個「不放寬」的推論**：它成立的前提是「佔位區塊的 `[]` 不代表無資源」——那是佔位區塊自己的標題文字說的。**用被質疑對象的自述來論證不能信任它，是不是循環？** 有沒有不依賴該自述、純從結構就能判定的辦法。

### 二、豁免機制的三要件是本輪最大的新增面，請重點打

`--ignore-unparseable` 逐張 card id，拒收 `*`／`all`／空值，只對本次 assign 生效、不寫任何持久設定；card id ＋解析錯誤原文＋執行者＋`resource_check_rev` 入 assign 事件；母體是**原始碼字面清單**（33 個 ID），硬性 sunset `2026-09-30`。

執行者在草稿中自己抓到並修掉一個洞：原本把母體定義成「body 帶 MIG1 marker」的**謂詞**，但 body 任何人都能在網頁上手改，貼一行 marker 就能取得豁免資格——謂詞式母體不封閉。改為字面常數清單後，E1 的強度**誠實降為「不可能靜默發生」**（不是「結構上不可能」）。

請判斷：**「不可能靜默發生」夠不夠。** 執行者自承 E1／E3 都只擋得住靜默，擋不住「過 PR 改常數」，也擋不住改系統時鐘。以及**陳舊豁免即錯誤**（名單含已可解析的卡就拒絕）這條，是否真的能強迫名單隨母體收縮，還是只要沒人跑就沒人知道。

### 三、需求方已裁定的一項，請確認執行者理解正確

**需求方 2026-08-12 裁定接受硬 sunset**（會自動放寬的截止不是截止），並同時開了 [#31](https://github.com/ruan6047/ai-workflow/issues/31) `OPS-MIG1-CLAIMS-BACKFILL1` 補齊那 33 張的宣告，讓 sunset 有人負責。

但需求方裁定時是知道爆炸半徑的：**到期後不是「那 33 張不能派工」，是「只要還有任何一張不可解析的活卡，任何卡都不能派工」**——那是全 Project 停機。請確認文件對這個半徑的描述**沒有寫小**。

### 四、跨卡矛盾（PM 指定查驗項，非 finding）

[#23](https://github.com/ruan6047/ai-workflow/issues/23) §10 把對本卡的依賴寫成四項假設並刻意不對齊。兩張都交付了，**PM 判定 A2 與 A3 不成立**：

- **A3**：本卡 §3.1 規則 1 定義 namespace 為「卡所屬 repo 根的相對路徑」，規則 2 拒收 `/` 起始、規則 3 拒收 `~`、規則 4 拒收 `..`。而 #23 要引用它的是**七個 CLI 引數**（`--repo-path`、`--out-dir`、`--config`、`--input`、`--spec-dir`、`--worktree`、`repo_root`），實務上多半絕對路徑——**本卡會把它們全部拒收**。這是域不相容，不是覆蓋不足。
- **A2**：本卡 §3.1 規則 8「宣告以位元組原樣儲存；比對時 casefold」、規則 9「比對前做 NFC」——`K(r)` 是比對鍵不是儲存形式，且本卡從不解析 cwd 或 symlink。提供的是集合成員判定，不是決定性字串輸出。

**請判斷：本卡是否應明文宣告封閉 namespace 不涵蓋 CLI 引數**，以免其他卡再度誤引。

**另外**：PM 於 2026-08-12 實跑 `wfcli assign` 時，該指令當場印出

```
[assign] 警告：以下活卡沒有可解析的資源宣告，交集檢查略過它們（不擋派工）：INIT-GAME-RECAP、ML-FIELD-OF1
```

這是 R1-001 所述 fail-open 的**現場實況**，不是文件推論。詳見 #25 的實跑報告留言。

### 五、執行者主動揭露

- **執行者是 Claude Opus 5@Claude Code 的子 agent，PM 亦為 Claude Opus 5。** 你必須是**不同模型家族**。
- **§8.2 原本的「258 組合」來自 R1 當時的 session 腳本、不可重跑**，本輪以內嵌的 §9.8 取代（語料不同故組合數為 276）。這是刻意替換，已在 §13 明說。**請確認替換沒有讓覆蓋變弱。**
- 你上輪已驗證通過的三項（`B ⊇ C`、`b_misses_c=0`、`templates/` 與 `templates2/a.md` 不相交）結論維持不變，但證據載體換了。
- 執行者自承六個未關的洞，含：豁免本身就是真的放行（今日 2 張）、E3 到期後全 Project `assign` 硬停、**宣告 × 實際寫入脫鉤完全沒解**（本卡只能保證「宣告的不撞」，保不了「宣告的就是會寫的」）、`is_owner_assigned` 把兩張其實沒在動的卡當成已認領（他刻意不收緊，因為縮小比對集合是 fail-open 方向）。

### 環境紅線

唯讀查核；**不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行任何有副作用的 `wfcli` 命令**（`--validate-only` 與 `doctor` 唯讀可以；讀 GitHub 的 `gh api`／`gh issue view` 唯讀可以）。

**留言紀律（重要，本輪起強制）**：你的留言中**不得出現事件 marker 的字面前綴**（即 `wf-review-event` 後面直接接半形冒號），連散文引用與 code fence 示範都不行——`doctor` 以全文子字串比對，命中即隔離整張卡的查核通道。需要指涉時拆開書寫。發文前 `grep` 一次。

### 輸出

依 `templates/review-prompt.md` §5 的結構化區塊，`core_pain_resolved` 與 `self_run` 必填。**額外強制兩項**：

1. **逐項回報前輪 finding 的閉環狀態**——R1-001 明列 `resolved`／`withdrawn`／仍開啟，缺此節即 `review-invalid`。
2. **`severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id` 五欄請你自己填**，不要留給 PM 事後指派。


## Comment 5256123716 · 2026-08-11T16:46:47Z

<!-- wf-review-receipt:v1 card_id=WF-RESOURCE-WRITESET1 source_sha=cb6028fc9f704459fd68456491bbf7238f8e10be report_sha256=ff3e916d0f8a83d0ef85c1e57557ffd9ecdbc7b63ed05ed8cde25e5678c35c18 -->

R2 查核收據：REQUEST_CHANGES。

取材規則：`report_sha256` 對查核者完整 YAML 報告區塊計算；UTF-8 編碼、LF 換行、末行含 LF；不含本收據正文。SHA-256：`ff3e916d0f8a83d0ef85c1e57557ffd9ecdbc7b63ed05ed8cde25e5678c35c18`。

收據未含狀態轉換；結構化裁決與完整證據由查核者交 PM。

## Comment 5256205839 · 2026-08-11T16:54:39Z

## PM 更正：五份派審詞的基線 SHA 全部寫錯

本則同時貼在 #21／#22／#23／#24／#25。

### 事實

五份派審詞都寫「基線：`origin/main` `0d4d282`」。**`0d4d282` 不是任何一張卡的祖先。**

```
wf-cleanup-guard1                  0d4d282=非祖先  merge-base=7451b72
wf-cli-routing-tier1               0d4d282=非祖先  merge-base=7451b72
wf-escalation-deferred-findings1   0d4d282=非祖先  merge-base=7451b72
wf-event-idempotency1              0d4d282=非祖先  merge-base=7451b72
wf-resource-writeset1              0d4d282=非祖先  merge-base=7451b72
```

**正確的共同基線是 `7451b72ba7679893043950d71bad9642665e25da`。**

`0d4d282` 是 `Merge pull request #29 from ruan6047/claude/OPS-CLEANUP-SMOKE1`——**我自己在派審前一小時跑 #25 端到端實跑時產生的 merge**。五張卡都在那之前分支，所以它們當然不是它的後代。我在寫派審詞時直接抄了當下的 `origin/main`，沒有回頭確認它與被審分支的祖先關係。

### 後果

**這使 [#23](https://github.com/ruan6047/ai-workflow/issues/23) 的查核者判定 `review-invalid` 而未進實質查核。** 那個判定依派審詞的字面是正確的——`git merge-base --is-ancestor 0d4d282 1ee62b0` 確實 exit 1。**責任在 Coordinator，不在查核者，也不在執行者。**

另外三位查核者（#21／#22／#24）都各自察覺並自行處理了：#21 明白寫出「實際共同祖先為 7451b72；`0d4d282` 是後續 main」並用 `merge-tree` 確認無衝突；#22 判定「派審指定基線仍為被審 SHA 的祖先，故不構成 review-invalid」——**該句的前半在事實上不成立，但其結論（可以繼續查核）是對的**；#24 在 `git diff --name-status 0d4d282..cb6028fc` 中看到 `tasks/_smoke/OPS-CLEANUP-SMOKE1.md` 被刪除，正確判斷那是基線差異造成的假象而非本輪變更。

**四位查核者裡三位靠自己繞過了我寫壞的指示，一位照著指示停下來。停下來的那位沒有做錯任何事。**

### 處置

- **#23 重新派審**，基線更正為 `7451b72`，被審 SHA 不變（`1ee62b0`）。該卡的 `review-invalid` **不計 iteration、不寫 review event、不改交付狀態**（`review-escalation.md` §1）。
- #21／#22／#24／#25 的查核**不因此失效**——四位都已對正確的變更範圍實跑，基線錯誤只影響 `git diff` 的顯示範圍，未影響被審 SHA 與其變更內容。
- 此後派審詞的基線一律以 `git merge-base <origin/main> <source_sha>` 產出，不得直接抄當下的 `origin/main`。

### 這件事的形狀

派審詞裡的「基線」欄本來就是給查核者用來界定 diff 範圍的座標。**我把一個更新的 main 當成基線，而那個 main 之所以更新，正是因為我自己剛在上面 merge 了東西。** 這與本批卡片反覆處理的問題同源：一個需要對照既有事實才能填的欄位，用當下手邊最方便的值填掉。


## Comment 5256223552 · 2026-08-11T16:56:20Z

<!-- wf-review-event:v1 card_id=WF-RESOURCE-WRITESET1 source_sha=cb6028fc9f704459fd68456491bbf7238f8e10be attempt_id=WF-RESOURCE-WRITESET1-e0-cb6028fc9f704459fd68456491bbf7238f8e10be -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-RESOURCE-WRITESET1`　attempt_id：`WF-RESOURCE-WRITESET1-e0-cb6028fc9f704459fd68456491bbf7238f8e10be`
- 查核者：GPT-5@Codex 子代理（留有 receipt marker，但採單行格式、不合 handoff-contract.md §3.1.2 的多行語法；PM 未能重算 report_sha256）　escalation_epoch：0
- source_sha：`cb6028fc9f704459fd68456491bbf7238f8e10be`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T00:56:19+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git status --short; git diff --check; git rev-parse origin/main`
  - HEAD=cb6028fc9f704459fd68456491bbf7238f8e10be；工作樹乾淨；diff --check 通過；origin/main=0d4d282ef3bb5eae6e78316a368029ced7ff98db
- `sed -n '769,855p' docs/WF_RESOURCE_WRITESET1.md | python3`
  - §9.8 PASS；23 接受語料、14 拒收語料、276 組合、b_misses_c=0、§9.1 的 11 列全數符合
- `sed -n '611,664p' docs/WF_RESOURCE_WRITESET1.md | PYTHONPATH=cli/src python3`
  - §9.7 可執行；目前快照為 17 張已指派活卡、15 可解析、2 不可解析，A/B/C 均為同 repo 0 對；文件已說明活卡集合是快照
- `sed -n '694,733p' docs/WF_RESOURCE_WRITESET1.md | PYTHONPATH=cli/src python3`
  - §9.7b 原樣執行失敗：SyntaxError: f-string expression part cannot include a backslash，位於 issue_url 正則的 f-string expression
- `git diff --name-status 0d4d282..cb6028fc; git show --stat --oneline cb6028fc; git show --stat --oneline 0ae8a11`
  - R2 commit 僅改文件；完整被審差異另含 R1 的 docs/WF_RESOURCE_WRITESET1.md 新增，未見本輪未宣告實作變更

### findings（1，其中 blocking 1）

- **WF-RESOURCE-WRITESET1-R2-001**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`rerunnable-cohort-probe-syntax-invalid`
  - evidence：docs/WF_RESOURCE_WRITESET1.md §9.7b 第 719 至 720 行把含反斜線的 re.match 正則直接放在 f-string expression。從文件原樣抽出第 694 至 733 行執行即 SyntaxError，故第 739 至 761 行的 33 張封閉母體、母體外 0、sentinel 失敗 0、db_scope 分佈與字面清單都不是可重跑 artifact。這些正是 §8.7.2 與 §8.8.1 至 E1 的必要證據。
  - disposition：修正 §9.7b，使其能從文件原樣執行並在現行 Project 快照產生輸出；以修正後同次輸出更新或明確釘住母體清單、數量與日期。再送審時附原樣抽取的實跑結果。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5259553591 · 2026-08-11T22:24:51Z

## 派審：#24 `WF-RESOURCE-WRITESET1` R3

⚠️ 審核對象是 **`ruan6047/ai-workflow#24`**，**不是 `cpbl-analytics#24`**。工作目標 repo 是 `ai-workflow`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-resource-writeset1
分支：claude/WF-RESOURCE-WRITESET1
被審 SHA：3cd2865780dcd54b1a6ab30f0497726d9c0a20cb
基線：7451b72ba7679893043950d71bad9642665e25da（= git merge-base origin/main 3cd2865，已驗證為祖先）
iteration：2
```

> **基線這次是用 `git merge-base` 算出來的。** 上一輪五份派審詞都把基線寫成當下的 `origin/main`（`0d4d282`），而那是 PM 自己跑實跑時產生的 merge。你上一輪在 `git diff --name-status 0d4d282..cb6028fc` 裡看到 `tasks/_smoke/OPS-CLEANUP-SMOKE1.md` 被刪除並正確判斷那是基線假象——**那個假象是 PM 造成的**。詳見本 Issue 的「PM 更正」留言。

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-resource-writeset1
git rev-parse HEAD && git status --short && git diff --check
git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD && echo "基線成立"
git diff cb6028f..3cd2865 -- docs/WF_RESOURCE_WRITESET1.md
```

### 一、複驗 R2-001——根因比你指出的更深

你報的是「§9.7b 從文件原樣抽出即 SyntaxError」。執行者查出的根因是**版本相依的隱形失敗**：`cli/pyproject.toml` 的 `requires-python` 下限是 **3.11**，而含反斜線的正則放進 f-string 取值部在 **3.12 以前**是 `SyntaxError`（PEP 701 之前）。執行者在 3.14 上寫、在 3.14 上驗；你用系統 3.9.6 撞到。

**PM 已獨立重現全鏈**：舊版經 `/usr/bin/python3`（3.9.6）`ast.parse` 拋出與你逐字相同的錯誤、指到同一條 `re.match`；新版 parse OK；新版以 `sed` 原樣抽出實跑，輸出與報告逐字相符。

修法：含反斜線正則提升為模組層 `re.compile` 常數，f-string 只放已算好的變數。

**結構性處置是新增 §9.9 探針自檢**（純文件內、無網路、無 `wf_cli` 依賴、退出碼即裁決）：抽出全檔 python 圍籬 → 逐一編譯 → **在 3.12+ 以 AST 掃 `FormattedValue` 的原始碼片段補上 3.12 前才存在的閘門** → 實際執行不 import `wf_cli` 者。`imports_wf_cli` 以 AST 判 import 而非字串比對，否則 §9.8 語料裡的 `"cli/src/wf_cli/"` 會讓離線探針被靜默跳過。

**PM 已實跑自檢與其反向驗證**：交付版 4 區塊、違例 0、PASS；跑在修正前檔案上 **FAIL 兩筆**（只抽到 3 個區塊、第 720 行 f-string 取值部含反斜線），**而且是在 `compile()` 會通過的 3.14 上抓到的**。

請攻擊：

1. **自檢的可攜性檢查只涵蓋「f-string 反斜線」這一種版本相依語法。** 3.12+ 上寫出的其他新語法（3.10 的 `match`、3.11 的例外群組、3.12 的型別參數語法）不會被抓到。執行者自承這一點並說「真正徹底的做法是 CI 用 3.11 直譯器實跑」。**這個劃界可接受嗎，還是自檢應該直接以宣稱下限的直譯器編譯？**
2. **自檢只對「需 gh 登入」的探針編譯不執行**，所以 §9.7／§9.7b 的**執行期正確性**（而非語法）仍未被守住。
3. **自檢會抽到自己**（以 `probe-selfcheck` 標記避免遞迴但仍受檢）。這個自指是否留下漏洞？

### 二、執行者主動報了一件由 PM 行為造成的證據失效，請評估其處理

§9.7 的 B／C 由 **1 對變 0 對**——因為 PM 於 `2026-08-12T00:13:42+08:00` 以 `amend`（op `df7e0929`）把 `file:templates/` 移出 #16 的宣告。

執行者的自我判定值得逐字看：**上一版寫的「不變的是結論：規則 B／C 找到 #16 × #22」把線上狀態誤當不變量——這與 R2-001 是同一種病（把會變的東西當證據）。**

處置：§1.2 與 §9.7 改寫，被斷言的不變量只剩「對固定輸入 A 判不相交而 B／C 判相交」（§9.1 第 1 列＋§9.8 凍結語料）與「現行守衛從未判出任何 `file:` 階層相交」；#16 × #22 降為**歷史舉證**，證據是那條 amend 軌跡。

**請判斷**：這個重新劃界是否徹底？文件裡還有沒有別的宣稱建立在「線上當下狀態」而非凍結語料上？（母體 item 數本輪由 96 變 99，是 PM 新開三張卡造成的——那算不算同一類？）

### 三、你上一輪三項跨卡裁決的落地

- **#23 的 A2／A3**：你裁定屬定義域不相容，並建議在 §3.1 或 §4 加一句明示不涵蓋 CLI 引數。執行者已照做：§3.1 標題改為「語彙規則（**只管卡面 `file:` 資源宣告，不管 CLI 路徑引數**）」並加告示框，§12 新增第 7 項非目標互指。另修 §4.2 的錯誤引用（`§9.7` → `§9.7b`，因 §9.7 只掃已指派活卡而該斷言要的是全 item）。**請確認這句界線寫得夠死，不會被下一張卡再度誤引。**
- **repo 限定詞**、**豁免與 sunset**：你裁定無須改動，執行者未動。

### 四、母體數字的變動

33 個 ID **逐字未變、順序未變**（執行者以 `diff` 對帳文件內清單 vs 本次輸出，零差異）；母體外 0、sentinel 卻失敗 0、已註冊 worktree 0、`db_scope` 分佈、混入卡 ID 的那 1 張皆未變。**唯一變動是 item 96 → 99**，係 PM 新開的三張卡（實跑用的 smoke 卡、[#30](https://github.com/ruan6047/ai-workflow/issues/30)、[#31](https://github.com/ruan6047/ai-workflow/issues/31)）。全部數字釘選在 **2026-08-12 01:28 +0800**。

### 五、執行者主動揭露

- **執行者是 Claude Opus 5@Claude Code 的子 agent，PM 亦為 Claude Opus 5。** 你必須是**不同模型家族**。
- 只動 `docs/WF_RESOURCE_WRITESET1.md`（+191/−20），`cli/` 未動。
- **執行者自承的第 2 個洞最該看**：自檢的射程只到內嵌四支探針。§1.1 的接受對照表、§4.1 的 repo 分佈（10/44、7/11）、§3.2 的 `*`／`?`／`[` 計數、§3.3 的 25 個非 ASCII 路徑**仍來自一次性 session 腳本，與 R2-001 同族，只是還沒人踩到**。執行者畫了一條界線（那些支撐定性結論，而 §8.7.2／§8.8.1 靠的是具體數值與具名清單），並明說「**這條界線是我畫的，查核者可以不接受**」。若判定要全數補成內嵌探針，工作量在本檔內、不逸出寫入集。
- 「宣告 × 實際寫入脫鉤」（自承第 1 洞）完全沒解，§8.9-3 維持原狀未弱化，只補了一筆同向實證：#16 的 amend 理由本身就是人工做的 `git diff --name-only` 對帳，與 §1.3 的 #13「由 PM 人工發現」是同一形狀的第二個實例——**證明機制必要且有效，也證明它仍完全沒有機械執行者**。
- §9.6 新增第 57 列要求衍生卡把自檢落成 repo 內腳本掛 CI 並以「植入反斜線」「刪去一個探針區塊」兩種變異測試釘住。本卡只宣告一個檔案故**不落地腳本**（新增 workflow 會逸出自己的寫入集）。

### 環境紅線

唯讀查核；**不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行任何有副作用的 `wfcli` 命令**（`doctor` 唯讀與 `--validate-only` 可以；讀 GitHub 的 `gh api`／`gh issue view` 唯讀可以，你會需要它跑 §9.7／§9.7b）。

**留言紀律**：你的留言中**不得出現事件 marker 的字面前綴**（即 `wf-review-event` 後面直接接半形冒號）。需要指涉時拆開書寫。發文前 `grep` 一次。

### 輸出

依 `templates/review-prompt.md` §5 的結構化區塊，`core_pain_resolved` 與 `self_run` 必填。**額外強制三項**：

1. **逐項回報前輪 finding 的閉環狀態**——R2-001 明列 `resolved`／`withdrawn`／仍開啟，缺此節即 `review-invalid`。
2. **`severity`／`blocking`／`finding_class`／`attribution`／`root_cause_id` 五欄請你自己填**。
3. **留一則收據**（`wf-review-receipt:v1`，**多行格式**——`card_id:` 與 `source_sha:` 各自獨立成行）。**你上一輪的收據用了單行 `key=value` 形式，`doctor` 的 `receipt_matches()` 以整行相等比對，完全認不得它，等同沒留。** 請把被雜湊的報告全文放進同一則留言，並在留言內寫死取材規則（起點、終點、編碼、換行、是否含尾端換行），讓 PM 能自己回讀重算。


## Comment 5259838968 · 2026-08-11T23:00:04Z

<!-- wf-review-receipt:v1
card_id: WF-RESOURCE-WRITESET1
source_sha: 3cd2865780dcd54b1a6ab30f0497726d9c0a20cb
report_sha256: a7d9364657e717366e62af0c7d38206813f9290c99a0d7d8c6fb0375b85f4a9a
-->

取材規則：雜湊取自本則留言 YAML 圍籬內，第一個 core_pain_resolved 字元起至最後一個 LF 為止；採 UTF-8 編碼、LF 換行、含末行 LF；不含收據 marker、取材規則文字與 Markdown 圍籬。

```yaml
core_pain_resolved: "no"
review_result: "REQUEST_CHANGES"
previous_findings:
  - finding_id: "WF-RESOURCE-WRITESET1-R2-001"
    closure_status: "resolved"
    evidence: "§9.7b 可從文件原樣抽出並在本次查核實跑；Python 3.9.6 自檢亦抽出四個區塊且 PASS，R2 的 f-string 反斜線 SyntaxError 已消失。"
self_run:
  - command: "git rev-parse HEAD; git status --short; git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD; git diff --check"
    observed: "HEAD 為 3cd2865780dcd54b1a6ab30f0497726d9c0a20cb；工作樹潔淨；基線祖先關係與 diff 檢查通過。"
  - command: "sed -n 624,677p docs/WF_RESOURCE_WRITESET1.md | PYTHONPATH=cli/src python3"
    observed: "§9.7 原樣可執行；16 張已指派活卡、14 可解析、2 不可解析，A/B/C 同 repo 與跨 repo 皆為 0 對。"
  - command: "sed -n 713,754p docs/WF_RESOURCE_WRITESET1.md | PYTHONPATH=cli/src python3"
    observed: "§9.7b 原樣可執行；100 個 Project item、33 個不可解析、33 個封閉母體、母體外 0、sentinel 卻失敗 0。"
  - command: "sed -n 793,880p docs/WF_RESOURCE_WRITESET1.md | python3"
    observed: "§9.8 PASS；23 接受語料、14 拒收語料、276 組合、b_misses_c 為 0，11 列矩陣均符合。"
  - command: "sed -n 916,997p docs/WF_RESOURCE_WRITESET1.md | python3"
    observed: "§9.9 在 Python 3.9.6 抽出四個 Python 區塊，實際執行一個離線探針，違例 0，PASS。"
  - command: "git ls-remote origin refs/heads/claude/WF-RESOURCE-WRITESET1; nl -ba docs/WF_RESOURCE_WRITESET1.md | sed -n 950,997p; rg -n requires-python cli/pyproject.toml"
    observed: "遠端分支指向被審 SHA；§9.9 宣稱下限 3.11，但可攜性額外掃描僅處理 f-string 取值部反斜線。"
findings:
  - finding_id: "WF-RESOURCE-WRITESET1-R3-001"
    severity: "major"
    blocking: true
    finding_class: "authoritative-artifact"
    attribution: "executor"
    root_cause_id: "portable-probe-selfcheck-incomplete-grammar-gate"
    evidence: "docs/WF_RESOURCE_WRITESET1.md 的 §9.9 將 FLOOR 固定為 3.11，並宣稱檢查跨直譯器可攜性；但 950 至 961 行唯一針對舊版 Python 的補充檢查只搜尋 f-string 取值部反斜線，969 至 974 行仍以執行中的直譯器 ast.parse 編譯。若 CI 以 3.12 以上執行，任何其他 3.12 以上的新語法都會編譯通過且不會被該掃描命中，卻無法在宣稱下限 3.11 執行。故 R2 的特定反斜線案例已修復，但機械自檢不能兌現其一般性的 3.11 可攜性宣稱。"
    disposition: "將自檢改為以 Python 3.11 直譯器實際編譯每個抽出的區塊，或使用等價且可證明覆蓋完整 Python 3.11 語法的版本化語法閘門；在 §9.6 第 57 列加入一個非 f-string 的高版本語法變異，證明該閘門會非零失敗。"
scope_outside_findings:
  status: "none"
```


## Comment 5259903369 · 2026-08-11T23:09:10Z

<!-- wf-review-event:v1 card_id=WF-RESOURCE-WRITESET1 source_sha=3cd2865780dcd54b1a6ab30f0497726d9c0a20cb attempt_id=WF-RESOURCE-WRITESET1-e0-3cd2865780dcd54b1a6ab30f0497726d9c0a20cb -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-RESOURCE-WRITESET1`　attempt_id：`WF-RESOURCE-WRITESET1-e0-3cd2865780dcd54b1a6ab30f0497726d9c0a20cb`
- 查核者：GPT-5@Codex 子代理（收據 issuecomment-5259838968，多行格式合規；PM 依其取材規則回讀重算 report_sha256=a7d93646… 一次相符。PM 另將 scope_outside_findings 的巢狀 mapping 轉為序列 mapping 以通過解析器，字串內容未變）　escalation_epoch：0
- source_sha：`3cd2865780dcd54b1a6ab30f0497726d9c0a20cb`
- core_pain_resolved：**no**（第一判準具否決權，canonical §5.1）
- 交付狀態：↩退回
- 寫入時間：2026-08-12T07:09:08+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git status --short; git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD; git diff --check`
  - HEAD 為 3cd2865780dcd54b1a6ab30f0497726d9c0a20cb；工作樹潔淨；基線祖先關係與 diff 檢查通過。
- `sed -n 624,677p docs/WF_RESOURCE_WRITESET1.md | PYTHONPATH=cli/src python3`
  - §9.7 原樣可執行；16 張已指派活卡、14 可解析、2 不可解析，A/B/C 同 repo 與跨 repo 皆為 0 對。
- `sed -n 713,754p docs/WF_RESOURCE_WRITESET1.md | PYTHONPATH=cli/src python3`
  - §9.7b 原樣可執行；100 個 Project item、33 個不可解析、33 個封閉母體、母體外 0、sentinel 卻失敗 0。
- `sed -n 793,880p docs/WF_RESOURCE_WRITESET1.md | python3`
  - §9.8 PASS；23 接受語料、14 拒收語料、276 組合、b_misses_c 為 0，11 列矩陣均符合。
- `sed -n 916,997p docs/WF_RESOURCE_WRITESET1.md | python3`
  - §9.9 在 Python 3.9.6 抽出四個 Python 區塊，實際執行一個離線探針，違例 0，PASS。
- `git ls-remote origin refs/heads/claude/WF-RESOURCE-WRITESET1; nl -ba docs/WF_RESOURCE_WRITESET1.md | sed -n 950,997p; rg -n requires-python cli/pyproject.toml`
  - 遠端分支指向被審 SHA；§9.9 宣稱下限 3.11，但可攜性額外掃描僅處理 f-string 取值部反斜線。

### findings（1，其中 blocking 1）

- **WF-RESOURCE-WRITESET1-R3-001**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`portable-probe-selfcheck-incomplete-grammar-gate`
  - evidence：docs/WF_RESOURCE_WRITESET1.md 的 §9.9 將 FLOOR 固定為 3.11，並宣稱檢查跨直譯器可攜性；但 950 至 961 行唯一針對舊版 Python 的補充檢查只搜尋 f-string 取值部反斜線，969 至 974 行仍以執行中的直譯器 ast.parse 編譯。若 CI 以 3.12 以上執行，任何其他 3.12 以上的新語法都會編譯通過且不會被該掃描命中，卻無法在宣稱下限 3.11 執行。故 R2 的特定反斜線案例已修復，但機械自檢不能兌現其一般性的 3.11 可攜性宣稱。
  - disposition：將自檢改為以 Python 3.11 直譯器實際編譯每個抽出的區塊，或使用等價且可證明覆蓋完整 Python 3.11 語法的版本化語法閘門；在 §9.6 第 57 列加入一個非 f-string 的高版本語法變異，證明該閘門會非零失敗。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5259926950 · 2026-08-11T23:12:20Z

## PM 轉錄紀錄：本輪四份裁決的收據驗證與格式轉換

四張全數 `REQUEST_CHANGES`，全部已寫入狀態面。以下逐項說明證據強度與我動過什麼。

### 收據驗證結果

| 卡 | 收據 | 雜湊重算 | 涵蓋範圍 |
|---|---|---|---|
| #22 | 多行格式，合規 | **一次算對** | report-begin／end 之間全文 |
| #24 | 多行格式，合規 | **一次算對** | YAML 圍籬內全文 |
| #25 | 多行格式，合規 | 試到**第三個邊界變體**才對上 | **僅 YAML**；前輪閉環與核心痛點陳述在雜湊外 |
| #23 | **無** | 不適用 | — |

**#25 的邊界規則不夠死。** 它寫 `report_end: report-end HTML 註解前的 LF 字元`，但沒說 `report-begin` 之後那個 LF 算不算起點。我試了三種：原樣（含前後換行）、去頭 LF 留尾、去頭 LF 且尾僅留一個 LF——第三種才相符。#22 與 #24 的規則各自指名了 trim 行為與末行 LF，都一次對上。**差別不在誰細心，在規則有沒有把兩端都釘住。**

**#25 的雜湊只保護 YAML。** 前輪 finding 閉環回報（本輪兩項強制之一）與核心痛點陳述都在 `report-end` 之後，不受雜湊保護——有人改動那兩段不會破壞雜湊。轉錄進狀態面的是 YAML，那部分有保護。

### #23 沒有收據，但我仍轉錄了

理由是我先前寫在 #22 上的那條不對稱：**保守方向的裁決容忍證據不足，開閘的裁決不容忍。** `REQUEST_CHANGES` 是把卡退回，不開任何閘門；`APPROVE` 才是。#21 上一輪的 `APPROVE` 我拒絕轉錄直到補件，這輪 #23 的 `REQUEST_CHANGES` 我照寫並把限制記在 `--reviewer` 欄。

**但我沒有照查核者的要求代發收據。** 該報告末尾寫「交付給 PM 時，請將上述完整報告原文放進 #23 同一則留言……再附多行 receipt marker」。**這件事 PM 做等於沒做**：收據的全部價值在於留言的 GitHub author 是平台可驗證的身分；由 PM 代發，證明的只是 PM 發過一則留言，對查核者的身分一無所證。`handoff-contract.md` §3.1.2 明寫「收據內模型／工具名稱只屬自述，不能取代平台身分驗證」——代發把整條規則變成空轉。

（附帶說明：本輪 #22／#24／#25 的收據留言 author 也都是 `ruan6047`，即需求方轉貼。所以嚴格說，那三則平台可驗證的是「該文字確由需求方發布」，不是「由 Codex 產出」。這是跨家族查核者無寫入權造成的結構性缺口，不是本輪的新問題。）

### 我動過的格式（兩處，均為解析器限制）

**#24**：`scope_outside_findings` 原為頂層鍵＋巢狀 mapping（`  status: "none"`），解析器只接受 `- key: value` 序列，改為 `- status: "none"`。字串內容未變。

**其餘三份未動。** 特別是 #22 這次直接用了 `|` 而非 `>`，#23 也沒有裸字串序列——上一輪的兩個坑都沒再踩。

### #23 與 #24 的分歧已如實保留

兩張對同一介面給出不同判斷，PM **未調和**：

- **#23** 判 `#24 的封閉 namespace 不能作為 CLI 路徑正規化來源`，列為 **blocking**（`external-path-normalization-domain-mismatch`），要求 #23 自己改寫 §4.1／§10 或定義獨立的 CLI 路徑規範化。
- **#24** 判兩者本來就是不同輸入域，應在文件明示不涵蓋 CLI 引數，**不構成其本輪 blocking finding**。

兩者不衝突——它們是同一件事的兩側：#24 認為責任在使用方，#23 認為自己得改。**兩張卡各自的處置方向其實一致**（#23 要改 §4.1／§10、#24 已加界線澄清），差別只在誰記為 blocking。這正是刻意不對齊要暴露的東西，結果它暴露出來了而且兩側收斂到同一個修法。


## Comment 5260244682 · 2026-08-11T23:54:56Z

## PM 自審與跨卡對帳（第二輪四張交付後）

需求方要求送外審前先自審一次、再檢查跨改動的衝突／矛盾／重工，不過關就繼續修。本則是結果。**四張的交付本身我逐項驗過，都成立；跨卡層面找到六項，其中兩項是我自己的問題。**

### 一、逐卡自審：宣稱與實據對照

我對每張只複驗**承重宣稱**——如果那一條不成立，整個修法就垮。

| 卡 | 承重宣稱 | PM 獨立複驗 |
|---|---|---|
| **#25** `b29d2c7` | M48（「複驗沒帶回 tip」保險絲在 release 被略過）對既有測試 SURVIVED、對新 AST 測試 KILLED | **重現**：排除新增兩條後 `379 passed` 存活；新增的 `test_executor_body_never_branches_on_the_trigger` FAILED。`cleanup.py` 的 diff 逐行核為 docstring，零邏輯改動。382 passed |
| **#24** `f2f5181` | `ast.parse(feature_version=(3,11))` 漏掉 R2-001 那個 case，故第 2 條路不可行 | **重現**：`feature_version=(3,11)` **接受**該段，真實 3.9.6 拋 `SyntaxError`。PEP 695 變異在新閘門 `[FAIL] 確屬下限違例`、在舊閘門 `違例 0 筆／PASS`。`FLOOR=(3,6)` 觸發 fail-closed |
| **#22** `8d27bed` | 三個反例全被打掉、正例仍 `deferred`；`(c′)` 預設可用因 doctor 已能讀 body 與 author | **重現**：65/65；三反例分別掉 `narrow_scope_bound`／`narrow_ruling_author_is_requester`／`narrow_scope_bound`，正例 `deferred`。`doctor.py:385,396` 確實已讀 `body` 與 `user` |
| **#23** `d824d16` | 三條事實支撐「第三條路」；並更正 #16 §4.3 | **重現**：`--config` 在 `config.py:69` 共用函式故在全動詞上；`assign --worktree` 為 `required=True`；`set_field_value(級別)` 在 `:392`、`set_item_body` 在 `:423`，故 `amend --tier` 的遠端首寫確為級別欄——**#16 §4.3 記反了** |

另核實 #23 的一條硬約束：`doctor.py` 的 `_CONFORMANT_MARKER_RE` 把「順序固定、單一空白、鍵集合封閉」編進同一條 regex，多一鍵即不匹配；且**全 repo 只有 `review.py:458` 會發出 marker**。

**#24 的兩個我先前標記的自審項也結了**：閘門選擇是 `sorted(found, reverse=True)`——取最接近 FLOOR 的版本（優先精確），非隨意；活卡張數在 §1.1 與 §9.7 都明寫為快照並附漂移史。後者我是抽驗不是窮舉。

---

### 二、跨卡對帳：六項

#### X1（矛盾）#24 把 CLI 路徑正規化指派給 #23，而 #23 已明文拒絕承接

- #24 §3.1 界線告示與 §12 第 7 項：「**引數的正規化歸 [#23]**」
- #23 §4.1b／§10：「本卡**不定義**、也**不引用**任何 CLI 路徑正規化器」「相依已解除」

兩張都是本輪剛交付。**#24 的指標指向一張已經拒收的卡**——未來若有人需要 CLI 路徑正規化，照 #24 的指示走過去，會被告知不存在。

處置建議：#24 改為「本卡不涵蓋；#23 已裁定其六個承接動詞不需要，故**目前無人擁有**——需要者須自行論證並開卡」。

#### X2（矛盾／重工）探針可攜性出現兩套標準，且 #23 的做法過不了 #24 的閘門

- **#24**：建強制閘門——找版本 ≤ FLOOR 的真實直譯器實際編譯，找不到即 fail-closed；並機械證明 `feature_version` 不能當閘門。
- **#23**：釘 `uv run python`（3.12.13）＋改 tuple 形式，只報實測範圍（3.9.6／3.12.13／3.14.3）。

**同一個 repo 的兩份設計文件，對同一類問題各自解一次，結論不同。** 若 #24 的判準成立（宣稱下限就要以下限驗證），#23 的探針沒有任何東西在守它的可攜性——它只是碰巧在三個版本上都跑得動。

這也是本次唯一符合「重工」的一項：#24 做出的自檢是**可泛用**的，#23 沒有沿用。

#### X3（結構性阻塞）三張卡的結構化欄位相依，全部撞上同一個封閉鍵集合

| 卡 | 需要的欄位 | 落在哪 |
|---|---|---|
| #22（上輪） | `review_prompt_url`、`closure_reporting_requested` | 派審事件 |
| #22（本輪 b′-1） | 被收窄的 `attempt_id`、`finding_id` | 裁定事件 |
| #23 | `event_id` 的載荷格式與回讀契約 | lifecycle 事件 |

三者都宣告依賴、都不在各自寫入集、都標為 fail-closed 待補。**但真正的阻塞比「無人擁有」更硬**：`_CONFORMANT_MARKER_RE` 的鍵集合封閉，多一鍵即整張卡停機；而六個動詞裡**只有 `review` 有 marker**。

所以這三項相依**不是各自缺一個欄位，是共同缺一次 marker 版本升級（v2）＋五個動詞的 marker 從無到有**。目前沒有任何卡承接這件事。

#### X4（路由）#23 更正了 #16 §4.3，而 #16 ⏸阻塞

#23 逐條核對後指出 #16 §4.3 把 `amend` 的寫入順序記為「body Log → 級別欄」並據此判合格，**與碼相反**。PM 已核實為真。#16 現為 ⏸阻塞（等 #23／#24 落地），該更正需在解除阻塞時一併吸收，否則 #16 帶著一個已知錯誤的逐動詞稽核。

#### X5（未閉合）#25 與 #23 對 `handoff` 的雙向認知，兩輪後仍未建立

上一輪 PM 已列為指定查驗項：#25 把破壞性收尾接上 `handoff`，而 #23 §7.1.2 判 `handoff` 首寫不合格。#25 的查核者把它記為**範圍外發現**並說「應由 PM 交 #23 的所有者裁定與承接」。

**本輪兩張各自又改了一輪，仍然互不引用。** `grep` 核對：#25 全文無 `#23`／`event_id`／「冪等」；#23 全文無 `#25`／`release`／`cleanup`。

#### X6（我的問題）殭屍卡 #12 佔著整個 `cli/src/wf_cli/`，且我把一個缺口路由錯了

[#12](https://github.com/ruan6047/ai-workflow/issues/12) `WF-CLI-TIER-MUTATION1`（📥Backlog）宣告 `file:cli/src/wf_cli/`，在階層包含語意下與 #25、[#30](https://github.com/ruan6047/ai-workflow/issues/30)、[#9](https://github.com/ruan6047/ai-workflow/issues/9) 全面相交。

而 [#19](https://github.com/ruan6047/ai-workflow/issues/19)（🏁完成）的驗收第 4 條逐字寫著：「與 #12（tier 更正）的範圍界定明確：**擇一實作，或明示 #12 併入本卡後關閉**」。#19 交付的 `amend` 已含 `--tier`、寫級別欄、留原值→新值＋理由、並有半寫入自癒。**#12 的驗收第 1、2 條已實質滿足，而那個裁定從未被記錄。**

**兩件事是我的：**

1. 先前需求方裁定「兩張過寬的目錄級宣告都收到實際子樹」，我收了 #16 與 #9，**漏了 #12**——而它是三張裡擋最多的一張。已於 `amend` op `89c002ee` 補收。
2. 我在處理 #25 時撞到「`wfcli amend` 沒有 `--core-pain`」，記為「**候選歸 #9**」。**那是錯的**——#12 的驗收第 3 條逐字要求「評估同類缺口是否還有：除 tier 外，其他開卡時設定的欄位是否也無更正路徑」，核心痛點正落在那裡。已在 #12 的 amend 理由中更正。

實測殘餘：`amend` 現涵蓋 spec-baseline／acceptance／verification／db-scope／resources／tier；**Initiative、鏈深、核心痛點、服務的原始目標仍無更正路徑**。

---

### 三、自審結論

**四張的交付可以送外審**——承重宣稱都經獨立複驗成立，寫入集無越界，測試無退化。

**但 X1／X2／X5 是本輪四張彼此之間的問題，不送修就等於把已知矛盾交給查核者。** 三者都小：X1 是 #24 改一句指標、X2 是 #23 說明為何不沿用 #24 的閘門（或沿用）、X5 是 #25 與 #23 互相引用一次。

**X3 需要開卡**（marker v2 ＋ 五個動詞的 marker），**X4 需要在 #16 解除阻塞時吸收**，**X6 的殘餘射程須需求方裁定 #12 是做還是關**。這三項不是本輪四張能解的。


## Comment 5260748605 · 2026-08-12T00:46:09Z

## PM 自審收斂紀錄：三輪之後

需求方要求送外審前自審、跨卡對帳、有問題就修再審，直到沒問題。**本則記錄收斂結果與仍存在的殘留。**

### 收斂過程

| 輪次 | 做了什麼 | 結果 |
|---|---|---|
| 第一輪 | 四張交付的承重宣稱逐項獨立複驗 | 全部成立 |
| 第二輪 | 跨卡對帳，找出六項 | X1／X2／X5 派修；X3 開卡；X4 記路由；X6 兩項是 PM 自己的問題 |
| 第三輪 | X2 的修正過程中，#23 把 #24 的自檢指向自己的檔案，**發現該自檢的三個缺陷** | #24 再修一輪，另挖出第四、第五個 |
| 第四輪 | #23 補上區塊數登記，使自己滿足所宣告沿用的標準 | 收斂 |

**第三輪不是計畫中的。** 它之所以發生，是因為 X2 的處置方式是「沿用而非各自實作」——而沿用的第一個動作就是把別人的機制指向自己的檔案跑一次。**那一跑立刻暴露了「一般性機制只在自己的樣本上驗證過」。**

### X1／X2／X5 逐項驗證

**X1（#24 把 CLI 路徑正規化指派給已拒收的 #23）—— 已解。** §3.1 告示與 §12 第 7 項改為「本卡不涵蓋 → #23 已裁定其六個承接動詞不需要 → 目前無人擁有 → 需要者須自行舉證並開卡」，並把 #23 的判準（分類鍵＝對事件內容的貢獻）與不可行性論證寫進告示，使誤引者拿得到判準而不只是「沒人管」。殘留的兩處字面命中經核對均為**撤回敘述本身**，非殘留。

**X2（兩套探針可攜性標準）—— 已解，且解法比對齊更好。** #23 選擇沿用而非自立第二套，並在沿用時做了兩件未被要求的事：把 #24 的自檢**原樣未改一字**指向自己的檔案實跑（因而發現缺陷）、**指名而不代修**。#24 據此修了五個缺陷，其中第五個（`sys.argv` 未隔離）**在 R4 從未浮現，只因為它被第二個缺陷擋在執行之外——一個缺陷遮住另一個**。

**X5（#25 與 #23 對 `handoff` 的雙向認知）—— 已解。** 先前 `grep` 兩邊各為 0；現在 #25 的文件提及 #23／`event_id`／冪等 3 處，#23 提及 #25／收尾 5 處。兩側依 PM 提供的**同一份事實**各寫一半，未各自推論。#25 另把它與 §9 第 2 項的分野寫成**雙向可發現**（兩節互相指路），並接出同源線：讀一次不構成保證 → 寫一次不構成生效確認 → 寫一次不構成可辨識。

### 機械核對

- 四張工作區**全部乾淨**，本地與遠端**同 SHA**（無 force 分歧）。
- 四張本輪變更**全部落在各自資源宣告內**。
- ai-workflow 卡之間的寫入集相交由 **17 組降為 4 組**（收窄 #16／#9／#12 三張過寬宣告的結果）。**剩下 4 組全部是現役卡與 Backlog 卡之間的排隊約束，不是缺陷**：#30 等 #25 釋放 `doctor.py`／`doctor_cmd.py`／`test_doctor.py`，#9 與 #30 在 `cli.py` 上互等。
- 自檢跨檔一般性：#24 的自檢對 #23 的文件 `[裁決] PASS`、違例 0、**四支探針全部實際執行**；對自己的文件仍 PASS。

### 仍存在的殘留（不擋送審，但查核者應知悉）

1. **#24 引用 #23 的 SHA 是 `d824d16`，而 #23 現為 `50021ce`。** 被引用的內容（§4.1b／§10 的拒收裁定）在兩個 commit 上一致，故無實質錯誤；把裁定釘在它被作出的那個 commit 也是可辯護的做法。但文中稱其為「其交付版」，而交付版現已前移——**這是輕微的陳舊引用**。
2. **#23 §4.4.1 的「實跑 B」含行號，貼死在文件裡。** 執行者自己標明：本檔一旦再編輯行號就漂移，屆時需一併重跑更新。這與它剛修掉的「實跑 A 陳舊」是同一形狀——**差別在現在它是已知的脆弱而非沉默的**。
3. **#24 自陳兩條尚未修的一般性假設**（§13）：工作目錄假設、行程狀態不隔離。兩者的真正處置都是「每支探針各起沙箱子行程」，需 repo 內腳本，逸出本卡寫入集。
4. **X3 已開卡 [#35](https://github.com/ruan6047/ai-workflow/issues/35) 但設有開工閘門**：三項具名相依全部寫於本輪且未經查核，相依未定稿前不得 `assign`。
5. **X4（#23 對 #16 §4.3 的更正）待 #16 解除阻塞時吸收。** #16 現為 ⏸阻塞（等 #23／#24 落地）。
6. **X6 的 #12 已重新界定射程**，殘餘為「開卡時設定但無更正路徑的欄位」，核心痛點優先。

### 一件方法上的觀察

本輪三個新缺陷（#24 自檢的五個、#23 的登記缺失）**沒有一個是查核者發現的**，全部來自「把 A 卡的機制指向 B 卡的檔案跑一次」這個動作。

跨卡對帳先前做的是**讀兩份文件找矛盾**；這次多做了一步——**讓一張卡的產物實際作用在另一張卡的產物上**。前者找到的是敘述不一致，後者找到的是機制不成立。兩者不能互相取代。


## Comment 5260781908 · 2026-08-12T00:51:24Z

## escalation-checkpoint（第四個可計數 attempt 前）＋ 一則漏建的合規記錄

### 先記漏建：本卡第三個 attempt 前應建而未建

`review-escalation.md:61` 要求「第三個及其後**每個**可計數 attempt 出現時先建立 `escalation-checkpoint`」。本卡已累積三個可計數 attempt（`0ae8a11`／`cb6028f`／`3cd2865`），**第三個（`3cd2865`）派審前沒有 checkpoint**。

**這是 PM 的合規缺口**：先前的做法是「察覺門檻條件成立才建」，而 `:61` 要求的是**例行建立**——兩者不同，後者是為了讓每一輪都有一個明示的判定點，而不是只在出事時才有。

**不追溯補建。** 事後補一則自稱當時作出的裁定，正是本專案明令禁止的形態（見 PM 於 `5249247912` 的公開撤回）。此處只記錄事實：第三輪缺少該判定點；若當時建立，依當時證據 decision 亦為 `continue`（R1-001 已於 R2 被判 `resolved`，兩個 root_cause 互異），故該缺漏未使任何應升級的情形被漏掉——**但那是事後推算，不是當時的判定**。

### 本輪（第四個 attempt 前）：兩條件皆不成立

**第一條件：1／3。** 三輪的 `root_cause_id` 互異，無任何家族重複：

| 輪次 | `root_cause_id` |
|---|---|
| R1-001 | `unparsable-resource-declaration-fail-open` |
| R2-001 | `rerunnable-cohort-probe-syntax-invalid` |
| R3-001 | `portable-probe-selfcheck-incomplete-grammar-gate` |

**第二條件：不成立。** R2 的 accepted blocking 為 R2-001，R3 查核者明列其為 `resolved`（§9.7b 可原樣抽出實跑、3.9.6 自檢 PASS）。

```yaml
checkpoint_decision: continue
checkpoint_rationale: |
  兩條件皆不成立，故 decision 為 continue。本則為 review-escalation.md:61 的例行
  checkpoint，不是因為門檻被觸發。同時記錄第三個 attempt 前的漏建，該漏建不追溯補建。
decided_by: 機械推導（兩條件皆不成立時 decision 不需裁定）
counts_toward_escalation: true
attempts_so_far: 3
```

### 給 R4 查核者的一個提醒

三個 `root_cause_id` 雖然字面互異，但**它們有共同的上層形態**：R2-001 是「探針宣稱可原樣重跑但不能」、R3-001 是「自檢宣稱一般性可攜但只兌現一個特例」——兩者都是**宣稱大於證據**。R6 的執行者自己也把它記為「這是同一病灶的第三次發作，只是這次發作在自檢自己身上」。

**若你認為這三者應合併為同一根因家族，請直接裁示**——那會使第一條件立即成立（3／3），下一輪強制 `escalate`。PM 不自行合併：合併與否都會改變門檻時點，而 PM 是有動機延後它的一方。


## Comment 5260862907 · 2026-08-12T01:04:21Z

## 派審：#24 `WF-RESOURCE-WRITESET1` R4

⚠️ 審核對象 **`ruan6047/ai-workflow#24`**，不是 `cpbl-analytics#24`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-resource-writeset1
分支：claude/WF-RESOURCE-WRITESET1
被審 SHA：75555caa848bd5f4f717a6205f5b584a8dbacec9
基線：7451b72ba7679893043950d71bad9642665e25da（= git merge-base origin/main 75555ca，已驗為祖先）
iteration：3
```

> **`origin/main` 現為 `3d4d9a0`，不是基線。** 上一批派審詞 PM 抄了當下的 `origin/main`，你在 `git diff --name-status` 裡看到的 `tasks/_smoke/...` 刪除就是那個假象。

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-resource-writeset1
git rev-parse HEAD && git status --short
git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD && echo 基線成立
git diff 3cd2865..75555ca -- docs/WF_RESOURCE_WRITESET1.md
```

### 一、複驗 R3-001（可攜性閘門），但重點在**它被指向別人的檔案時發生了什麼**

你上一輪判：§9.9 把 FLOOR 固定為 3.11 並宣稱檢查跨直譯器可攜性，但補充檢查只搜尋 f-string 反斜線，其餘仍以執行中的直譯器編譯——**一般性宣稱只兌現一個特例**。

執行者選了第 1 條路（真實舊直譯器實際編譯），並**先用機械反例否決第 2 條**：

```
ast.parse("print(f\"{__import__('re').match(r'a\\.b','a.b')}\")", feature_version=(3,11)) → 接受
真實 3.9.6 → SyntaxError: f-string expression part cannot include a backslash
```

**它漏掉的正好是 R2-001 那個 case**——用 `feature_version` 當閘門會原樣放行本卡上一輪被打的 bug。PM 已獨立重現。

**但真正的事件是這個**：[#23](https://github.com/ruan6047/ai-workflow/issues/23) 本輪決定沿用本卡的判準，把這支自檢**原樣未改一字**指向它自己的文件——**一跑就踩中兩個缺陷**，執行者再修時又挖出三個：

| # | 缺陷 | 後果 |
|---|---|---|
| (a) | `except BaseException` 捕獲 `SystemExit(0)` | 乾淨結束的探針被判 FAIL——假陽性 |
| (b) | `imports_wf_cli ⇒ 需 gh ⇒ 只編譯` | 只做 argparse 內省的探針被靜默跳過，**而自檢仍 PASS** |
| (c) | `len(probes) < 4` 寫死 | 區塊數多於 4 的文件上是恆真檢查 |
| (d) | `__name__ = "__probe__"` | 方向反了——「原樣抽出執行」就是當腳本跑 |
| (e) | `sys.argv` 未隔離 | 探針繼承自檢的 `argv[1]`；**在 R4 從未浮現，只因被 (b) 擋在執行之外——一個缺陷遮住另一個** |

PM 逐項實測確認 (a)(b)(c)(e)，並驗證修正後：自檢指向 #23 的文件時四支探針**全部實際執行**、僅缺登記一筆 FAIL；#23 補一行後違例 0、PASS。

**請攻擊**：

1. **(b) 的新做法是「預設執行、跳過才登記」**。執行者自承這翻轉**移除了一層安全網**——R4 的錯誤推論順帶讓碰狀態面的碼不會被執行。他要求採用本自檢的文件其 `python` 區塊必須唯讀。**那個要求有機械執行者嗎，還是只是一句話？**
2. **(c) 的 `probe-blocks: N` 逐檔登記**：登記值本身由文件作者填，**填錯了誰抓**？
3. §9.6 第 57 列的變異由 3 個增為 8 個。**請確認那八個真的各自對應一個機制，而不是同一個機制的八種寫法。**

### 二、X1（跨卡對帳）：撤回一個懸空的所有權指派

§3.1 界線告示與 §12 第 7 項曾寫「引數的正規化**歸 #23**」，而 #23 於 `d824d16` 已明文拒絕承接。已改為「本卡不涵蓋 → #23 已裁定其六個承接動詞不需要 → **目前無人擁有** → 需要者須自行舉證並開卡」，並把 #23 的判準與不可行性論證寫進告示。

**已知瑕疵**：該處引用 #23 的 SHA 為 `d824d16`，而 #23 現為 `50021ce`。被引內容（§4.1b／§10）兩處一致、無實質錯誤，把裁定釘在它被作出的 commit 也可辯護——**但文中稱其為「其交付版」而交付版已前移**。PM 判斷這是輕微陳舊引用，未要求修；**你可以有不同判斷。**

### 三、門檻提醒（重要）

同日的 escalation checkpoint 判 `continue`，但**三個 `root_cause_id` 雖字面互異，有共同的上層形態**：

| 輪次 | `root_cause_id` | 形態 |
|---|---|---|
| R1-001 | `unparsable-resource-declaration-fail-open` | 無法安全判定卻放行 |
| R2-001 | `rerunnable-cohort-probe-syntax-invalid` | 宣稱可原樣重跑但不能 |
| R3-001 | `portable-probe-selfcheck-incomplete-grammar-gate` | 宣稱一般性可攜但只兌現特例 |

執行者自己也把 R3-001 記為「這是同一病灶（**宣稱大於證據**）的第三次發作，只是這次發作在自檢自己身上」。

**若你判定這三者應合併為同一根因家族，第一條件立即成立（3／3），下一輪強制 `escalate`。** PM 不自行合併——合併與否都會改變門檻時點，而 PM 是有動機延後它的一方。

### 四、一則合規記錄

本卡**第三個 attempt 前應建而未建 escalation checkpoint**（`review-escalation.md:61` 要求第三個及其後每個可計數 attempt 出現時先建立）。這是 PM 的缺口，**不追溯補建**——事後補一則自稱當時作出的裁定是本專案明令禁止的形態。詳見同日 checkpoint 留言。

### 五、已知殘留（PM 自審已找到）

1. 執行者自陳兩條**尚未修**的一般性假設（§13）：工作目錄假設、行程狀態不隔離。真正處置需 repo 內腳本，逸出寫入集。
2. R3 遺留：§1.1／§3.2／§3.3／§4.1 的數字仍來自一次性 session 腳本，不在自檢射程。執行者明說「這條界線是我畫的，查核者可以不接受」。
3. §9.7 的活卡張數逐日漂移（17→16），文件已標為快照；執行者自承未窮舉全檔是否還有把它當不變量引用之處。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`gh api`／`gh issue view` 唯讀可用，你會需要它跑 §9.7／§9.7b）。**不得 amend 已推送的 commit、不得 `push -f`。**

**留言紀律**：不得出現事件 marker 的字面前綴。拆開書寫，發文前 `grep`。

### 輸出

依 `templates/review-prompt.md` §5。**三項強制**：

1. **逐項回報前輪 finding 閉環**——R3-001 明列 `resolved`／`withdrawn`／仍開啟，缺此節即 `review-invalid`。
2. **五個 schema 欄位自己填**；`root_cause_id` 見門檻提醒。
3. **留收據**：多行格式、報告全文同帖、取材規則寫死。**你上一輪的收據是合格的（PM 一次算對），請沿用同樣寫法。**

**YAML 限制**：不支援 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、**不支援頂層鍵＋巢狀 mapping**（你上一輪的 `scope_outside_findings: / status:` 被拒，PM 轉為序列才寫得進去）、值含 ` #` 須加引號。


## Comment 5260898979 · 2026-08-12T01:10:07Z

<!-- wf-review-receipt:v1
card_id: WF-RESOURCE-WRITESET1
source_sha: 75555caa848bd5f4f717a6205f5b584a8dbacec9
report_sha256: 0b8bc6e4ab2d0192cb11cc3bc825820cad8879544a64a12a934388fa350fdb08
-->

取材規則：起點為下方報告全文的第一個字元 core_pain_resolved，終點為最後一個換行後的最後一個字元；UTF-8、LF、保留末尾單一 LF、無 strip；排除本收據 HTML 註解、空白分隔行與本行。

core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C .claude/worktrees/wf-resource-writeset1 rev-parse HEAD; git status --short; git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD"
    observed: "HEAD=75555caa848bd5f4f717a6205f5b584a8dbacec9；工作區乾淨；共同基線為祖先。"
  - command: "git archive 75555caa848bd5f4f717a6205f5b584a8dbacec9 | tar -x -C /tmp/wf-resource-writeset1-review-qMd45y；從該 archive 抽出 §9.9 自檢後以 python3 執行 docs/WF_RESOURCE_WRITESET1.md"
    observed: "Python 3.9.6 的 stricter 閘門編譯四個區塊；一支離線探針實際執行；違例 0；裁決 PASS。"
  - command: "在 /tmp/wf-resource-r3closure-XXXXXX 以同一自檢執行含 type FutureAlias = int 的 probe-blocks: 1 文件，以及缺 probe-blocks 的文件"
    observed: "兩例皆非 0：前者被 3.9.6 閘門以 SyntaxError 攔下；後者報文件未登記區塊數。"
  - command: "在 /tmp/wf-resource-writeset1-review-qMd45y 以同一自檢執行 probe-blocks: 1 的文件；唯一 Python 區塊為 pathlib.Path(\"side-effect-created\").write_text(\"proves execution\")"
    observed: "自檢回傳 0、裁決 PASS，且 temp 目錄出現 side-effect-created；證明未登記區塊可寫入後仍被接受。"
previous_blocking_closure:
  - finding_id: "WF-RESOURCE-WRITESET1-R1-001"
    status: "resolved"
    evidence: "§8.6–§8.9 已把不可解析宣告導向阻擋或具名豁免；本輪範圍未見其回歸。"
  - finding_id: "WF-RESOURCE-WRITESET1-R2-001"
    status: "resolved"
    evidence: "真實 3.9.6 閘門拒絕 type alias 高版本語法；缺逐檔 probe-blocks 亦 fail-closed。"
  - finding_id: "WF-RESOURCE-WRITESET1-R3-001"
    status: "resolved"
    evidence: "§9.9 已由真實版本不高於 3.11 的直譯器逐區塊編譯；本輪 archive 重跑四區塊 PASS，且非 f-string 高版本語法非 0。"
root_cause_assessment:
  - assessment: "R1-001、R2-001、R3-001 應併為上層根因 claim-exceeds-evidence：三者均是在無法完整證明時仍讓守衛或證據宣稱成立。其字面子類別不同，未改變同一 fail-open／證據不足形態。"
  - escalation_effect: "此判定令既有三個可計數 attempt 滿足同根因三次條件；下一個 checkpoint 依 review-escalation.md §4 必須為 escalate。"
findings:
  - finding_id: "WF-RESOURCE-WRITESET1-R4-001"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: claim-exceeds-evidence
    evidence: "§9.9.1-D／§13 只用文字要求採用者的 python 區塊唯讀，程式卻對所有未標 probe-requires 的區塊 exec(compile(...))。上述 archive 隔離重現中，未標記的 pathlib 寫檔區塊建立 side-effect-created，仍得到退出碼 0／PASS；因此唯讀要求沒有機械執行者，錯誤或惡意的目標文件可在 CI 或查核環境被執行。"
    disposition: "在把自檢宣告為可用於目標文件或掛 CI 前，必須改成可強制的隔離邊界（每探針子行程且限制檔案系統、網路與狀態面），或收窄契約為不執行外部文件並 fail-closed；不得以作者自我宣告的 probe-requires／唯讀承諾作為安全邊界。"
scope_outside_findings:
  - observation: "§3.1 對 #23 d824d16 的引用稱為交付版而現行交付已前移，屬 PM 已揭露的輕微陳舊引用；其 §4.1b／§10 被引裁定未見實質差異，未列 blocking finding。"
  - observation: "§9.6 的八個變異不是八個彼此獨立機制：a／b 覆蓋同一語法閘門，c／c2／c3／c4 覆蓋同一逐檔登記機制，e 與 f 分別覆蓋退出碼與顯式跳過。它們是不同分支案例，文件未作一對一機制的錯誤宣稱。"

## Comment 5260903533 · 2026-08-12T01:10:53Z

<!-- wf-review-receipt:v1
card_id: WF-RESOURCE-WRITESET1
source_sha: 75555caa848bd5f4f717a6205f5b584a8dbacec9
report_sha256: ac25a726349bd5a7487fc9522dfa4280c0c10ed062ef8137f25f080b9ccf058e
-->

取材規則：起點為下方報告全文的第一個字元 core_pain_resolved，終點為最後一個換行後的最後一個字元；UTF-8、LF、保留末尾單一 LF、無 strip；排除本收據 HTML 註解、空白分隔行與本行。此收據取代 issuecomment-5260898979 的報告，唯一修正為第一條 self_run 的 git status 指令補上正確的 -C worktree。

core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C .claude/worktrees/wf-resource-writeset1 rev-parse HEAD; git -C .claude/worktrees/wf-resource-writeset1 status --short; git -C .claude/worktrees/wf-resource-writeset1 merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD"
    observed: "HEAD=75555caa848bd5f4f717a6205f5b584a8dbacec9；工作區乾淨；共同基線為祖先。"
  - command: "git archive 75555caa848bd5f4f717a6205f5b584a8dbacec9 | tar -x -C /tmp/wf-resource-writeset1-review-qMd45y；從該 archive 抽出 §9.9 自檢後以 python3 執行 docs/WF_RESOURCE_WRITESET1.md"
    observed: "Python 3.9.6 的 stricter 閘門編譯四個區塊；一支離線探針實際執行；違例 0；裁決 PASS。"
  - command: "在 /tmp/wf-resource-r3closure-XXXXXX 以同一自檢執行含 type FutureAlias = int 的 probe-blocks: 1 文件，以及缺 probe-blocks 的文件"
    observed: "兩例皆非 0：前者被 3.9.6 閘門以 SyntaxError 攔下；後者報文件未登記區塊數。"
  - command: "在 /tmp/wf-resource-writeset1-review-qMd45y 以同一自檢執行 probe-blocks: 1 的文件；唯一 Python 區塊為 pathlib.Path(\"side-effect-created\").write_text(\"proves execution\")"
    observed: "自檢回傳 0、裁決 PASS，且 temp 目錄出現 side-effect-created；證明未登記區塊可寫入後仍被接受。"
previous_blocking_closure:
  - finding_id: "WF-RESOURCE-WRITESET1-R1-001"
    status: "resolved"
    evidence: "§8.6–§8.9 已把不可解析宣告導向阻擋或具名豁免；本輪範圍未見其回歸。"
  - finding_id: "WF-RESOURCE-WRITESET1-R2-001"
    status: "resolved"
    evidence: "真實 3.9.6 閘門拒絕 type alias 高版本語法；缺逐檔 probe-blocks 亦 fail-closed。"
  - finding_id: "WF-RESOURCE-WRITESET1-R3-001"
    status: "resolved"
    evidence: "§9.9 已由真實版本不高於 3.11 的直譯器逐區塊編譯；本輪 archive 重跑四區塊 PASS，且非 f-string 高版本語法非 0。"
root_cause_assessment:
  - assessment: "R1-001、R2-001、R3-001 應併為上層根因 claim-exceeds-evidence：三者均是在無法完整證明時仍讓守衛或證據宣稱成立。其字面子類別不同，未改變同一 fail-open／證據不足形態。"
  - escalation_effect: "此判定令既有三個可計數 attempt 滿足同根因三次條件；下一個 checkpoint 依 review-escalation.md §4 必須為 escalate。"
findings:
  - finding_id: "WF-RESOURCE-WRITESET1-R4-001"
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: claim-exceeds-evidence
    evidence: "§9.9.1-D／§13 只用文字要求採用者的 python 區塊唯讀，程式卻對所有未標 probe-requires 的區塊 exec(compile(...))。上述 archive 隔離重現中，未標記的 pathlib 寫檔區塊建立 side-effect-created，仍得到退出碼 0／PASS；因此唯讀要求沒有機械執行者，錯誤或惡意的目標文件可在 CI 或查核環境被執行。"
    disposition: "在把自檢宣告為可用於目標文件或掛 CI 前，必須改成可強制的隔離邊界（每探針子行程且限制檔案系統、網路與狀態面），或收窄契約為不執行外部文件並 fail-closed；不得以作者自我宣告的 probe-requires／唯讀承諾作為安全邊界。"
scope_outside_findings:
  - observation: "§3.1 對 #23 d824d16 的引用稱為交付版而現行交付已前移，屬 PM 已揭露的輕微陳舊引用；其 §4.1b／§10 被引裁定未見實質差異，未列 blocking finding。"
  - observation: "§9.6 的八個變異不是八個彼此獨立機制：a／b 覆蓋同一語法閘門，c／c2／c3／c4 覆蓋同一逐檔登記機制，e 與 f 分別覆蓋退出碼與顯式跳過。它們是不同分支案例，文件未作一對一機制的錯誤宣稱。"

## Comment 5260998613 · 2026-08-12T01:26:42Z

<!-- wf-review-event:v1 card_id=WF-RESOURCE-WRITESET1 source_sha=75555caa848bd5f4f717a6205f5b584a8dbacec9 attempt_id=WF-RESOURCE-WRITESET1-e0-75555caa848bd5f4f717a6205f5b584a8dbacec9 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-RESOURCE-WRITESET1`　attempt_id：`WF-RESOURCE-WRITESET1-e0-75555caa848bd5f4f717a6205f5b584a8dbacec9`
- 查核者：GPT-5@Codex 子代理（收據 issuecomment-5260903533，多行格式合規；PM 已回讀重算 report_sha256=ac25a726… 相符）　escalation_epoch：0
- source_sha：`75555caa848bd5f4f717a6205f5b584a8dbacec9`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-12T09:26:41+08:00

### self_run（查核者實跑）

- `git -C .claude/worktrees/wf-resource-writeset1 rev-parse HEAD; git -C .claude/worktrees/wf-resource-writeset1 status --short; git -C .claude/worktrees/wf-resource-writeset1 merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD`
  - HEAD=75555caa848bd5f4f717a6205f5b584a8dbacec9；工作區乾淨；共同基線為祖先。
- `git archive 75555caa848bd5f4f717a6205f5b584a8dbacec9 | tar -x -C /tmp/wf-resource-writeset1-review-qMd45y；從該 archive 抽出 §9.9 自檢後以 python3 執行 docs/WF_RESOURCE_WRITESET1.md`
  - Python 3.9.6 的 stricter 閘門編譯四個區塊；一支離線探針實際執行；違例 0；裁決 PASS。
- `在 /tmp/wf-resource-r3closure-XXXXXX 以同一自檢執行含 type FutureAlias = int 的 probe-blocks: 1 文件，以及缺 probe-blocks 的文件`
  - 兩例皆非 0：前者被 3.9.6 閘門以 SyntaxError 攔下；後者報文件未登記區塊數。
- `在 /tmp/wf-resource-writeset1-review-qMd45y 以同一自檢執行 probe-blocks: 1 的文件；唯一 Python 區塊為 pathlib.Path("side-effect-created").write_text("proves execution")`
  - 自檢回傳 0、裁決 PASS，且 temp 目錄出現 side-effect-created；證明未登記區塊可寫入後仍被接受。

### findings（1，其中 blocking 1）

- **WF-RESOURCE-WRITESET1-R4-001**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`claim-exceeds-evidence`
  - evidence：§9.9.1-D／§13 只用文字要求採用者的 python 區塊唯讀，程式卻對所有未標 probe-requires 的區塊 exec(compile(...))。上述 archive 隔離重現中，未標記的 pathlib 寫檔區塊建立 side-effect-created，仍得到退出碼 0／PASS；因此唯讀要求沒有機械執行者，錯誤或惡意的目標文件可在 CI 或查核環境被執行。
  - disposition：在把自檢宣告為可用於目標文件或掛 CI 前，必須改成可強制的隔離邊界（每探針子行程且限制檔案系統、網路與狀態面），或收窄契約為不執行外部文件並 fail-closed；不得以作者自我宣告的 probe-requires／唯讀承諾作為安全邊界。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。

## Comment 5261025805 · 2026-08-12T01:31:12Z

## escalation-checkpoint（第五個可計數 attempt 前）：第一條件成立

### 查核者做了根因合併裁定

R4 查核者在 `root_cause_assessment` 明寫：

> R1-001、R2-001、R3-001 應併為上層根因 `claim-exceeds-evidence`：三者均是在無法完整證明時仍讓守衛或證據宣稱成立。其字面子類別不同，未改變同一 fail-open／證據不足形態。
> 此判定令既有三個可計數 attempt 滿足同根因三次條件；下一個 checkpoint 依 `review-escalation.md` §4 必須為 `escalate`。

而他本輪的 **R4-001 也用同一個 `root_cause_id`**——那是第四次。

**PM 採認該裁示。** 上一則 checkpoint 已把這個問題交給查核者（「若你判定這三者應合併為同一根因家族，第一條件立即成立」），並明說 PM 不自行合併，因為 PM 是有動機延後門檻的一方。**查核者判了，PM 照辦。**

| 輪次 | 原 `root_cause_id` | 併入 |
|---|---|---|
| R1-001 | `unparsable-resource-declaration-fail-open` | `claim-exceeds-evidence` |
| R2-001 | `rerunnable-cohort-probe-syntax-invalid` | 同上 |
| R3-001 | `portable-probe-selfcheck-incomplete-grammar-gate` | 同上 |
| R4-001 | （查核者直接標記） | `claim-exceeds-evidence` |

**第一條件成立（4 ／ 3），`checkpoint_decision` 只能是 `escalate`。**

### R4-001 的內容值得單獨看：這一次的宣稱是 R6 修法自己引入的

R4-001 指出 §9.9.1-D／§13 只用**文字**要求採用者的 python 區塊唯讀，程式卻對所有未標 `probe-requires` 的區塊 `exec(compile(...))`。

**PM 已獨立重現**：建一份只有 `probe-blocks: 1`、唯一區塊為 `pathlib.Path("side-effect-created").write_text(...)` 的文件，自檢**實際建立了該檔案**並回 **PASS、違例 0、退出碼 0**。

而這個風險**是 R6 修法自己引入的**——它把預設從「跳過」翻成「執行」，執行者在 §13 自陳四明寫「R4 的錯誤推論順帶當了一層安全網，翻成預設執行後那層網沒了」。**查核者把那句自陳變成了可執行的利用。**

這使根因合併更站得住：R6 修的是「宣稱大於證據」，而修法本身又立了一個只有文字沒有執行者的宣稱。

### 裁定

```yaml
checkpoint_decision: escalate
escalation_resolution: continue
checkpoint_rationale: |
  第一條件成立：查核者裁定 R1-001／R2-001／R3-001 併入 claim-exceeds-evidence，
  加上本輪 R4-001 同家族，已跨四個唯一可計數 attempt（門檻為三）。
  故 checkpoint_decision 只能是 escalate。
  需求方裁定 continue，維持同執行者角色（Claude Opus 5@Claude Code 子 agent），
  不換人、不切卡。裁定依據為需求方 2026-08-12 的原話：「#24 continue」。
decided_by: ruan6047（需求方）
counts_toward_escalation: true
attempts_so_far: 4
```

### 給下一輪的兩點

1. **同根因已第四次。** 下一輪若再出現 `claim-exceeds-evidence`，那是第五次——需求方已用過一次 `continue`，屆時的裁定應該考慮這一點。
2. **R4-001 的處置方向查核者給了兩條**：改成可強制的隔離邊界（每探針子行程並限制檔案系統／網路／狀態面），或**收窄契約為不執行外部文件並 fail-closed**。**不得以作者自我宣告的 `probe-requires`／唯讀承諾作為安全邊界。** 執行者上一輪自己也說過真正的處置是「每支探針各起一個沙箱子行程」，但那需要 repo 內腳本、逸出本卡寫入集——**若結論是本卡做不到，那就是收窄契約，不是再寫一句要求。**


## Comment 5261214208 · 2026-08-12T02:01:57Z

## escalation-checkpoint（第六個可計數 attempt 前）

### 第一條件仍成立，狀態自上一則 checkpoint 起未變

查核者已於 R4 裁定 R1-001／R2-001／R3-001 併入 `claim-exceeds-evidence`，加上 R4-001 同家族，**已跨四個唯一可計數 attempt**（門檻為三）。

R5 是**修正輪**、不是查核輪，**未產生新 finding**，故家族計數仍為 4。第一條件成立，`checkpoint_decision` 只能是 `escalate`。

**第二條件不成立**：R4 的 accepted blocking 為 R4-001，R5 已處置（PM 已獨立複驗：同一份利用文件在 R5 版下不再產生副作用檔案）。

### 裁定

```yaml
checkpoint_decision: escalate
escalation_resolution: continue
checkpoint_rationale: |
  第一條件仍成立（claim-exceeds-evidence 跨四個 attempt），故 decision 只能是 escalate。
  需求方已於同日的前一則 checkpoint（issuecomment-5261025805）對**同一組事實**裁定
  continue，原話「#24 continue」；R5 為修正輪、未產生新 finding，家族計數與該次裁定
  當時完全相同，故沿用。
  ⚠️ 若本輪（第六個 attempt）的查核產生第五次同家族 finding，該裁定不再涵蓋，
  須由需求方重新裁定。
decided_by: ruan6047（需求方，2026-08-12；沿用同日前一則 checkpoint 的裁定，事實未變）
counts_toward_escalation: true
attempts_so_far: 5
```

### R5 的處置方向值得記，因為它是「減少能力」而非「加強保護」

執行者選了查核者給的第 2 條——**收窄契約為不執行外部文件**，並說明第 1 條（可強制的隔離邊界）為何在本卡做不出來：子行程只解決狀態污染不限制檔案系統；OS 級設施（`sandbox-exec`）macOS 專屬且已 deprecated，Linux runner 預設沒有 `bwrap`／`firejail`，落地會退化成「有沙箱就跑、沒有就跳過」——**那正是 R3-001 的形狀**；Python 層假沙箱可被 `os`／`ctypes`／`subprocess` 繞過。

**它明說這是能力的減少，不是「更安全所以更好」**：本卡原本同時宣稱兩件事，第二件的實作方式不安全，於是拿掉並指名歸屬。拿掉後「§9.8 今天是否仍 PASS」只由一次人工執行佐證，**在衍生卡把它掛上 CI 之前那是操作紀律，不是機械保證**。

它自己的歸因（§9.9.8／§13）也切中同一個家族：

> R6 加的跨檔樣本**全是善意文件**，而同一輪把預設翻成「執行」——用「會不會誤判」的量尺去量「會不會替對方做事」，取樣再多也照不到。**當一個機制會對別人的輸入做事，就得用「對方是惡意的」來量。**

### 對 [#23](https://github.com/ruan6047/ai-workflow/issues/23) 的影響（已 🏁完成）

PM 已實跑確認 `50021ce` 在 R5 版下仍 **exit 0、四個區塊全過**。但 #23 §4.4.1 的兩項具名適配（`SystemExit(0)` 視為通過、以「需憑證」決定是否執行）**失去標的**——它們只在「自檢會執行探針」的世界裡有意義。

#23 已結案，本卡未代改。**該卡的 §4.4.1 措辭與其實作卡 A 的驗收欄會與現實脫節，需 PM 處理歸屬。**


## Comment 5261600653 · 2026-08-12T02:50:26Z

## 派審：#24 `WF-RESOURCE-WRITESET1` R6

⚠️ 審核對象 **`ruan6047/ai-workflow#24`**，不是 `cpbl-analytics#24`。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-resource-writeset1
分支：claude/WF-RESOURCE-WRITESET1
被審 SHA：3e45646d1f9fdfd1c8f1bc1ff777a5b6e8d4653f
基線：7451b72ba7679893043950d71bad9642665e25da（= git merge-base origin/main 3e45646d，已驗為祖先）
iteration：4
```

> **`origin/main` 現為 `6e6e8ab`，不是基線。** 抄它會得到錯誤的 diff 範圍。PM 已跑機械前置：SHA／基線／祖先關係／工作區乾淨（0 項）／已推送／該 SHA 尚無 review event（`doctor --review-channel` 判 `unobservable`）。若你仍發現對不上，直接回報 `review-invalid`，不要自行繞過。

```bash
cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-resource-writeset1
git rev-parse HEAD && git status --short
git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD && echo 基線成立
git diff 75555ca..3e45646 -- docs/WF_RESOURCE_WRITESET1.md
```

### 一、複驗 R4-001：執行者選了你給的第 2 條路，代價是能力歸零

你判的是 `claim-exceeds-evidence`（major, blocking）：§9.9.1-D／§13 只用**文字**要求採用者的 python 區塊唯讀，程式卻對所有未標 `probe-requires` 的區塊 `exec(compile(...))`。你給兩條 disposition：(1) 可強制的隔離邊界，(2) 收窄契約為不執行外部文件並 fail-closed。

執行者選 (2)，並**先自行重現該利用**（`75555ca` 版對利用文件 PASS 且 `side-effect-created` 被建立），再論證 (1) 在本卡射程內做不出來，而理由**不是**逸出寫入集：

- 子行程只解決狀態污染，不限制檔案系統；
- `/usr/bin/sandbox-exec` 實測確實擋下寫入，但 macOS 專屬且已 deprecated，同機無 `bwrap`／`firejail`，落地會退化成「有沙箱就跑、沒有就跳過」＝**R3-001 的形狀**；
- Python 層假沙箱可被 `os`／`ctypes`／`subprocess` 繞過。

處置：移除全部執行路徑（AST 確認腳本內無 `exec`／`eval`／`compile`／`__import__`），撤除 `probe-self`／`probe-requires` 兩個標記，**不提供任何執行開關**。

PM 已獨立複驗三項：同一份利用文件在本版下 `side-effect-created` 不存在、裁決行自述「未執行任何區塊」；#23 的 `50021ce` 仍 exit 0 四區塊全過；本檔仍 PASS。

**請攻擊三點：**

1. **這是「修好」還是「移除問題所在的能力」？** 執行者自己標明「本輪讓本卡探針執行覆蓋歸零，是能力的減少而非『更安全所以更好』」。你要判的是：R4-001 的痛點（宣稱唯讀但實際執行）是否真被關閉，還是被搬到別處——**現在「§9.8 今天是否仍 PASS」只由一次人工執行佐證，在衍生卡掛 CI 前是操作紀律不是機械保證**。這句話本身會不會就是新一輪的 `claim-exceeds-evidence`？
2. **AST 確認「腳本內無 `exec`／`eval`／`compile`／`__import__`」能否被繞過？** 這與 #25 R4-002 是同一形態的檢查（那張卡的 AST 守衛被 `locals()["trig"+"ger"]` 打穿）。請實際試。
3. **收窄不是把利用文件判 FAIL。** 執行者明說沒有程式能可靠認出「這段碼會寫檔」，判 FAIL 又是用猜的代替判定；故 §9.6 第 57c 列的斷言是「副作用檔案不存在」而非退出碼。**請判斷這個區分成不成立**，以及該斷言是否真的驗得到它宣稱的性質。

### 二、門檻：第一條件已成立，你這輪可能觸發第五次

| 輪次 | `root_cause_id` |
|---|---|
| R1-001 | `unparsable-resource-declaration-fail-open` |
| R2-001 | `rerunnable-cohort-probe-syntax-invalid` |
| R3-001 | `portable-probe-selfcheck-incomplete-grammar-gate` |
| R4-001 | `claim-exceeds-evidence` |

上一輪**你自己裁定前三項併入 `claim-exceeds-evidence`**，加上 R4-001 即跨四個 attempt，第一條件成立、checkpoint 判 `escalate`；**需求方裁定 continue、維持同執行者**。

**若你本輪產生第五次同家族 finding，請沿用 `claim-exceeds-evidence` 這個家族名，不要另起新名**——另起新名會把門檻洗掉，而那會直接改變需求方是否要換執行者的判斷。

### 三、一件 PM 必須交代的跨卡後果

[#23](https://github.com/ruan6047/ai-workflow/issues/23) 已結案併入 main，而它的 §4.4.1 有兩項具名適配是指向本卡**舊版**的自檢機制（`probe-requires`／`probe-self`）——本輪把那兩個標記撤除後，**那兩項具名適配失去標的**。這是執行者主動回報的。

**請判斷**：這是否構成本卡的 blocking finding，還是屬 PM 的跨卡歸屬處理（#23 已結案，改它需另開卡）。**PM 不自行裁定，因為 PM 是有動機把它推到卡外的一方。**

### 四、已知殘留（PM 自審已找到，不必重複發現，但可判斷處置是否恰當）

1. §3.1 對 #23 `d824d16` 的引用稱「交付版」而交付已前移至 `50021ce`（你上一輪已列為 scope_outside、非 blocking）。
2. §9.6 的八個變異不是八個獨立機制而是不同分支案例（你上一輪的認定，文件未作錯誤宣稱）。
3. §1.1／§3.2／§3.3／§4.1 的數字仍來自一次性 session 腳本，不在自檢射程——而本輪自檢已無執行能力，這條的**性質改變了**：從「有射程但沒涵蓋」變成「射程本身不存在」。請判斷文件是否誠實反映了這個改變。
4. §9.7 的活卡張數逐日漂移，文件已標為快照。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`gh api`／`gh issue view`／`doctor` 唯讀可用，你會需要它跑 §9.7／§9.7b）。**不得 amend 任何已推送的 commit；rebase 後只准 `--force-with-lease`，禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時，在**拋棄式**臨時目錄做（`git archive <sha> | tar -x -C /tmp/...`）——**不要在被審 worktree 內 `checkout`／`reset`／`stash`**，六個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被隔離**——散文引用、code fence 示範都一樣。需要指涉時拆開書寫，發文前 `grep` 一次確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**——R4-001 明列 `resolved`／`withdrawn`／仍開啟並附證據。
2. **五個 schema 欄位自己填**；`root_cause_id` 見第二節門檻提醒。
3. **留收據**：`wf-review-receipt:v1` **多行格式**（`card_id:` 與 `source_sha:` **各自獨立成行**，單行 `key=value` 形式 `doctor` 認不得），**把被雜湊的報告全文放進同一則留言**並寫死取材規則（起點、終點、編碼、換行、是否 strip、排除範圍）。你前兩輪的收據都合格、PM 各一次算對，請沿用同樣寫法。

**YAML 限制**（解析器是自寫的固定子集，看不懂就拒收）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、值含 ` #` 須整個值加引號。非 schema 的頂層鍵會被容忍。


## Comment 5261716854 · 2026-08-12T03:03:07Z

<!-- wf-review-receipt:v1
card_id: WF-RESOURCE-WRITESET1
source_sha: 3e45646d1f9fdfd1c8f1bc1ff777a5b6e8d4653f
report_sha256: 46b1a470619094cac2e1cf324727f9f754fc6c6b362d966e4c5ad7794b86c2f0
-->

取材規則：被雜湊報告從下一個 `<!-- report-begin -->` 之後的第一個位元組開始，到 `<!-- report-end -->` 之前的最後一個換行為止；UTF-8 編碼、LF 換行、保留末尾一個換行、不做 strip；排除 receipt、這段取材規則、兩個 delimiter 與任何 Markdown 外框。
<!-- report-begin -->
core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "git rev-parse HEAD; git status --short; git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD"
    observed: "HEAD 為 3e45646d1f9fdfd1c8f1bc1ff777a5b6e8d4653f；工作樹乾淨；指定基線為祖先。"
  - command: "git archive 3e45646d1f9fdfd1c8f1bc1ff777a5b6e8d4653f | tar -x -C /tmp/wf-resource-review.7OLOY4；抽出 §9.9 並以 /usr/bin/python3 對目標文件執行"
    observed: "3.9.6 stricter 閘門剖析 4 個區塊，違例 0，退出 0，輸出明示執行覆蓋為 0。"
  - command: "在拋棄式 archive 目錄，對 probe-blocks: 1 且唯一區塊會建立 side-effect-created 的不受信任文件執行 R7 自檢"
    observed: "退出 0／PASS，但 side-effect-created 不存在；利用內容未被求值。"
  - command: "以 getattr(__builtins__, \"ex\" + \"ec\")(src) 植入自檢副本，再以只找直接 Name 呼叫的 AST 掃描檢查並對同一利用文件執行"
    observed: "直接禁用呼叫清單仍為空，但 side-effect-created 被建立；AST 禁字掃描可繞過，不能單獨作安全保證。"
  - command: "抽出 §9.7／§9.7b，以 PYTHONPATH=cli/src /usr/bin/python3 執行；並以 R7 自檢檢查 git show 50021ce:docs/WF_EVENT_IDEMPOTENCY1.md"
    observed: "§9.7 得到活卡 17、可解析 15、不可解析 2；§9.7b 得到 Project 104、無法解析 33；#23 四區塊僅靜態剖析全過、退出 0。"
previous_findings:
  - finding_id: WF-RESOURCE-WRITESET1-R4-001
    severity: major
    blocking: true
    accepted: true
    status: resolved
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: claim-exceeds-evidence
    evidence: "R7 只經 ast.parse 與固定 PARSE stdin 閘門處理目標內容；利用文件 PASS 時副作用檔不存在。§9.9.6／§13 亦明記 §9.8 執行不再有機械保證。"
    disposition: "已採收窄契約；共用自檢不得恢復執行外部文件，未來如需執行須在各卡受審 CI 的具名步驟完成。"
findings:
  - finding_id: WF-RESOURCE-WRITESET1-R6-001
    severity: minor
    blocking: false
    accepted: true
    status: open
    finding_class: coordination
    attribution: coordinator
    root_cause_id: cross-card-contract-drift
    evidence: "#23 已結案的 §4.4.1 仍把 SystemExit(0) 與 probe-requires 的兩項適配寫成共用自檢的現役機制；R7 已撤除它們。#24 §9.9.9 已如實列出影響，故本卡沒有隱瞞或錯誤聲稱。"
    disposition: "PM 須留可稽核的跨卡歸屬裁定：另開卡修正或註記 #23，或明示接受歷史措辭保留並指向各卡 CI；這不是本卡的 blocking finding，因修改已結案 #23 逸出本卡寫入集。"
observations:
  - "R7 是移除不安全的『對任意文件執行』能力，而非保留能力後加強隔離；這正是 R4-001 給定 disposition 的第 2 條。§9.8 今日 PASS 僅有人工作證，文件已明示不是機械保證，未構成 claim-exceeds-evidence。"
  - "AST 禁字掃描可被動態名稱繞過；但 §9.6 第 57c 的安全斷言是行為測試與結構檢查的合取，實測行為測試有效。文件也只把結構檢查稱為較弱的第二道防線，故不另列 blocking finding。"
  - "利用文件應 PASS 的區分成立：靜態語法與 probe-blocks 登記皆正確，退出碼不應被當作副作用判定；副作用檔不存在才直接驗到『未執行該利用』。"
  - "§1.1／§3.2／§3.3／§4.1 的一次性數字仍不在自檢射程；§13 已明說自檢僅保證可剖析，並未假稱會重跑這些數字。§9.7／§9.7b 是快照，今日實跑數字已不同，未見文件把它們宣稱為不變量。"
<!-- report-end -->


## Comment 5261743789 · 2026-08-12T03:06:14Z

<!-- wf-review-event:v1 card_id=WF-RESOURCE-WRITESET1 source_sha=3e45646d1f9fdfd1c8f1bc1ff777a5b6e8d4653f attempt_id=WF-RESOURCE-WRITESET1-e0-3e45646d1f9fdfd1c8f1bc1ff777a5b6e8d4653f -->
## 查核裁決：APPROVE

- 卡：`WF-RESOURCE-WRITESET1`　attempt_id：`WF-RESOURCE-WRITESET1-e0-3e45646d1f9fdfd1c8f1bc1ff777a5b6e8d4653f`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5261716854 多行格式合規，PM 依其取材規則回讀重算 report_sha256=46b1a470… 相符；PM 僅將 observations 的裸字串序列轉為 - observation: 形式以通過解析器，字串內容逐字未變）　escalation_epoch：0
- source_sha：`3e45646d1f9fdfd1c8f1bc1ff777a5b6e8d4653f`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-12T11:06:12+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git status --short; git merge-base --is-ancestor 7451b72ba7679893043950d71bad9642665e25da HEAD`
  - HEAD 為 3e45646d1f9fdfd1c8f1bc1ff777a5b6e8d4653f；工作樹乾淨；指定基線為祖先。
- `git archive 3e45646d1f9fdfd1c8f1bc1ff777a5b6e8d4653f | tar -x -C /tmp/wf-resource-review.7OLOY4；抽出 §9.9 並以 /usr/bin/python3 對目標文件執行`
  - 3.9.6 stricter 閘門剖析 4 個區塊，違例 0，退出 0，輸出明示執行覆蓋為 0。
- `在拋棄式 archive 目錄，對 probe-blocks: 1 且唯一區塊會建立 side-effect-created 的不受信任文件執行 R7 自檢`
  - 退出 0／PASS，但 side-effect-created 不存在；利用內容未被求值。
- `以 getattr(__builtins__, "ex" + "ec")(src) 植入自檢副本，再以只找直接 Name 呼叫的 AST 掃描檢查並對同一利用文件執行`
  - 直接禁用呼叫清單仍為空，但 side-effect-created 被建立；AST 禁字掃描可繞過，不能單獨作安全保證。
- `抽出 §9.7／§9.7b，以 PYTHONPATH=cli/src /usr/bin/python3 執行；並以 R7 自檢檢查 git show 50021ce:docs/WF_EVENT_IDEMPOTENCY1.md`
  - §9.7 得到活卡 17、可解析 15、不可解析 2；§9.7b 得到 Project 104、無法解析 33；#23 四區塊僅靜態剖析全過、退出 0。

### findings（1，其中 blocking 0）

- **WF-RESOURCE-WRITESET1-R6-001**　severity=minor　blocking=false　class=coordination　attribution=coordinator　root_cause_id=`cross-card-contract-drift`
  - evidence：#23 已結案的 §4.4.1 仍把 SystemExit(0) 與 probe-requires 的兩項適配寫成共用自檢的現役機制；R7 已撤除它們。#24 §9.9.9 已如實列出影響，故本卡沒有隱瞞或錯誤聲稱。
  - disposition：PM 須留可稽核的跨卡歸屬裁定：另開卡修正或註記 #23，或明示接受歷史措辭保留並指向各卡 CI；這不是本卡的 blocking finding，因修改已結案 #23 逸出本卡寫入集。

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。
