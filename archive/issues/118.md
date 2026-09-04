# #118 WF-OPEN-INITIAL-STATUS1 open 的初始交付狀態改為 💡需求，並讓 doctor 不再把合規的補救判成漂移
- state: closed  created: 2026-08-21T11:53:03Z  closed: 2026-08-22T07:50:16Z
- url: https://github.com/ruan6047/ai-workflow/issues/118
- comments: 6

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；改動點只有兩個常數，但它決定每一張未來新卡的初始狀態，且 doctor 的漂移判定與多份測試 fixture 都釘在舊值上。難點不在實作量，在三處：(1) 判準要對齊 canonical 與採用專案基線而不是自己發明；(2) test_doctor.py:1765 的語意要反轉（合規補救不再是漂移），改它必須是為了反映新判準而不是讓紅的變綠；(3) 資源撞四張卡的宣告，派工期間要序列化。）　查核：待指派（建議 主力型；本卡改變每一張未來新卡的初始狀態，且正確性取決於是否正確讀出 canonical 與採用專案基線的關係——PM 今日已在同類判讀上犯錯多次。**要求跨模型家族或人工查核**，查核重點在：新預設是否真的符合 canonical §3.1 與採用專案的 §2.0、以及測試改動是否為了反映新判準而非讓紅的變綠。）
- Initiative：—　spec 基線：AI_WORKFLOW.md:113（T3 需求方批註放行後才進 📥Backlog）＋ cpbl-analytics docs/ROADMAP.md §2.0 基線 1（所有新卡一律由 💡需求 開始）＋ 需求方 2026-08-21 裁定採甲案（一律 💡需求，不依 tier 分流）@ ai-workflow main 2ae1ff0b
- DB：db_scope=none
- 服務的原始目標：新卡的初始狀態要是規則說的那一個，而不是工具方便的那一個

## 簡介
<!-- card-brief:begin -->
把 wfcli open 的初始交付狀態預設從 📥Backlog 改成 💡需求，並同步 doctor.py:1251 的 OPEN_INITIAL_STATUS 與 test_doctor.py:1765 的漂移判準——在此之前，每次開卡後為了符合閘門而做的補救，在觀測面上都被記成漂移。**適用時機**：想知道新卡為何一開就落 💡需求、或 doctor 為何不再把「📥Backlog→💡需求」判成 drift；或要查「一律 💡需求、不依 tier 分流」這個 2026-08-21 裁定的依據時。⛔ 非射程：不新增 open 的 --status 顯式覆寫旗標（給了就會有人拿它繞閘門，須需求方另裁）；不改 canonical AI_WORKFLOW.md:113 的規則本體（本卡是讓工具對齊既有規則）；不追溯修正那 10 次違規卡的現行狀態。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：`wfcli open` 把每一張新卡直接寫成 `📥Backlog`，而那是規劃閘門通過**之後**才該到的狀態。

```
canonical AI_WORKFLOW.md:113   T3「需求方批註放行後才進 📥Backlog」
採用專案 cpbl ROADMAP §2.0     「所有新卡一律由 💡需求 開始…才可進 📥Backlog／執行」（無 tier 例外）
wfcli     card.py:295          delivery_status: str = "📥Backlog"
```

⭐ **同一個檔案，437 行之後就寫著不該這樣**——`card.py:732` 的註解逐字「T3 → 核心痛點三問，**需求方批註放行**後才進 📥Backlog」；`commands/amend_cmd.py:36` 也重述一次。**`card.py` 自己記著規則，然後預設違反它。**

⚠️ **而且 `doctor` 把違規釘成了基準**：`doctor.py:1251` `OPEN_INITIAL_STATUS = "📥Backlog"`，註解逐字「`wfcli open` 寫入的初始交付狀態。open 無 `--status`，值即 `card.Card.delivery_status` 的 dataclass 預設；測試釘同一性」。⇒ **doctor 不會抓到它，因為它把錯的當成預期的。**

⭐ **更直接的證據在測試裡**：`cli/tests/test_doctor.py:1765` 逐字

```python
assert (moved.verdict, moved.expected_status, moved.actual_status) == ("drift", "📥Backlog", "💡需求")
```

**今天，一張卡從 `📥Backlog` 移到 `💡需求`，`audit_state_face_drift` 判它是「漂移」。** 而那正是每次開卡後 PM 為了符合 §2.0 而做的補救動作——**在觀測面上，合規的補救被記成漂移。**

**受害是量到的，不是推測**：2026-08-21 的卡況稽核記錄「開卡即落 `📥Backlog`」在三天內累計 **8 次**（`#147`／`#148`／`#138`／`#139` 等）；同日再加 `cpbl#160`、`cpbl#161` 兩次，**共 10 次**。⚠️ `open` **沒有 `--status` 旗標**，所以這個坑對**每一張新卡**都會發生，補救只能靠 PM 事後多下一次 `handoff`——而那次 handoff 又會被 doctor 判成漂移。

依 `docs/ROADMAP.md` §0 的三問：服務**目標 1**（防止低級事故）；**擋下它的是那個預設值本身**（`card.py:295` ＋ `doctor.py:1251`），不是「靠人記得」；**現在有人受害**——三天十次，每一張新卡。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/card.py",
    "file:cli/src/wf_cli/doctor.py",
    "file:cli/tests/test_doctor.py",
    "file:cli/tests/test_commands_mocked.py",
    "file:cli/tests/test_review.py",
    "file:docs/CONTRACT_TOOL_RECONCILE.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] ⭐ 預設改為 💡需求，一律不依 tier 分流：cli/src/wf_cli/card.py:295 的 delivery_status 預設改為 💡需求。⚠️ 需求方 2026-08-21 已裁定採此案而非依 tier 分流（canonical 只點名 T3，採用專案 cpbl §2.0 說所有新卡）——理由是不讓 wfcli 對「哪一級要過閘門」有自己的意見，且一律 💡需求 是保守方向，採用專案想放寬時在自己的流程裡多一次 handoff 即可，反向則不安全。⛔ 不得改成依 --tier 分流。
- [ ] ⭐ doctor 的預期值同步：cli/src/wf_cli/doctor.py:1251 的 OPEN_INITIAL_STATUS 同步改為 💡需求，並更新其註解。⚠️ cli/tests/test_doctor.py:1753 釘的是「OPEN_INITIAL_STATUS == Card 的 dataclass 預設」這個同一性——兩者必須一起改，該測試才會繼續有意義（只改一邊會讓它轉紅，那是正確的紅）。
- [ ] ⭐ test_doctor.py:1765 的語意反轉，且必須逐條說明：該條今天斷言「從 📥Backlog 移到 💡需求 ＝ drift」。改後應為「💡需求 是預期、移到 📥Backlog 才需要有事件解釋」。⛔ 不得為了讓紅的變綠而刪除或弱化任何一條斷言——每改一條都要寫出「原斷言反映的舊判準是什麼、新斷言反映的新判準是什麼」。
- [ ] ⭐ 雙向可證偽驗收：(a) 新開一張卡（可用既有的 mocked 測試路徑）斷言交付狀態為 💡需求；(b) 對照組——一張已由 handoff 明示移到 📥Backlog 的卡，audit_state_face_drift 必須判為 consistent 而非 drift。⚠️ 只驗 (a) 會被一個「永遠回 💡需求」的實作通過。
- [ ] ⭐ 變異檢驗：把 card.py 的預設改回 📥Backlog 而 doctor 不動 → 同一性測試必須轉紅；只改 doctor 不改 card.py → 同樣必須轉紅。兩個方向都要，且都在最終碼上跑。
- [ ] ⭐ 既有 fixture 逐一盤點：cli/tests/test_doctor.py:142／:172／:1762-1765／:1967、cli/tests/test_commands_mocked.py:144、cli/tests/test_registry.py:40 皆內含 📥Backlog 字面。交付須逐處說明「這一處是在測開卡預設（須改）還是在測別的東西而剛好用了這個值（不必改）」——⛔ 不得整批 sed 取代。
- [ ] ⛔ 非目標——不新增 open 的 --status 旗標。本卡只改預設；是否給 open 一個顯式覆寫通道是另一個問題（且給了之後就會有人用它繞過閘門），須由需求方另行裁定。
- [ ] ⛔ 非目標——不動任何既有卡的現行狀態；不改 canonical AI_WORKFLOW.md（本卡是讓工具對齊既有規則，不是改規則）；不碰採用專案 cpbl-analytics 的任何檔。
- [ ] 既有 uv run --frozen pytest -q 不得因本卡而失效或被排除；contract_tool_reconcile --check 須維持 exit 0。

## 驗證

- [ ] ⭐ 全套測試在交付 SHA 上跑：cd cli && uv run --frozen pytest -q，貼末行並與改動前的末行並列說明差額。
- [ ] ⭐ 變異檢驗的兩個方向各貼一次指令與輸出，還原後貼檔案 sha256 或 git diff 為空的證明。
- [ ] ⭐ 端到端實證：以 mocked 路徑實跑一次 open，貼出寫入的交付狀態欄位值。⚠️ 不得只靠讀碼宣稱預設已改。
- [ ] python3 scripts/contract_tool_reconcile.py --check 貼輸出與真實 exit code。⚠️ 量 exit code 不要接管線——本專案 2026-08-21 踩過這個坑（$? 抓到的是 tail 的狀態）。
- [ ] ⚠️ 報告須明列沒驗到什麼。至少包含：本卡不改任何既有卡的狀態，故「10 次違規」的既有卡不會因本卡而變正確——那是既成事實，須照實說。
- [ ] ⚠️ 不得 merge、不得跑任何 wfcli 寫入動詞去測（會污染真實狀態面）、不得 gh issue comment。
## Log

- 2026-08-21T19:53:01+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-21T19:54:24+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code（子代理）；分支worktree claude/WF-OPEN-INITIAL-STATUS1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-open-initial-status1；交付狀態 🔨執行中；實際能力層級 主力型（與卡面建議 主力型 相符）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-21T20:13:51+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 0；SHA 6e2e1707d8cce55a62ac50cff57243405bc9d93c；證據 R1 交付。分支 claude/WF-OPEN-INITIAL-STATUS1，單一 commit 6e2e1707「fix(cli): open a card into the status the planning gate has not yet passed」，基線 2ae1ff0b，6 檔 +88/−15。

PM 獨立複驗：card.py:295 = '💡需求'、doctor.py:1261 = '💡需求'；cd cli && uv run --frozen pytest -q → 1054 passed（改動前 1052，差額 +2 皆為新增測試，無刪除無 skip）；contract_tool_reconcile --check 真實 exit code = 0。

⚠️⚠️ **兩項越界，PM 判為必須交給查核者裁定，不預先擴權以免變成事後追認**：

(1) **改了兩個宣告外的檔**：cli/tests/test_review.py（:542/:624/:680/:684 四處，改後轉紅故必改）與 docs/CONTRACT_TOOL_RECONCILE.md（理由見 (2)）。⚠️ **執行者是先寫後揭露，不是事前停手請求擴權**——與 cpbl#157 的乾淨先例相反、與 cpbl#134 R1-002 同形。
⭐ **但 PM 必須先承認自己的部分**：本卡的派工包**沒有帶那條「需要動宣告外的任何檔時停下來請求擴權」的明文**，而 PM 在同日的 cpbl#160 與 ai-workflow#39 派工包裡都帶了。**這是 coordinator 的疏漏，attribution 不應全歸 executor。** 執行者確實做了衝突檢查（21 張 open 卡的 resource-claims 全數解析，無一宣告那兩個檔），也在報告首節主動標為「請優先看」。
⚠️ 另：宣告的 test_registry.py 未被改（執行者判為「測 Ledger 欄位切分、值只是被解析的儲存格」）——宣告 ⊇ 實際是安全方向。

(2) ⭐ **本卡讓 📥Backlog 變成沒有專責 writer 的狀態，這是真實的新缺口**：card.py:295 與 doctor.py:1251 是該字面僅有的兩個 writer，兩處消失後 contract_tool_reconcile 對它的判定由 ok 翻成 read-only，--check 當場 exit 1（實際缺口 59、登記 58）。執行者依該檔 §6「登記＝承認缺口，不是消除缺口」把它登記進處置表，**沒有補動詞**（卡面非目標明列不新增旗標）。⇒ 規劃閘門過了之後，現在只剩 assign --status／handoff --status 兩個自由文字逃生口。**補不補動詞須由需求方另裁。**

⭐ 執行者的三項強證據：
- **端到端實證**：以 mocked 路徑對 T0–T4 五級各實跑一次 open，五級交付狀態皆 '💡需求'，並固化為常設測試 test_open_initial_status_is_the_same_for_every_tier——**它同時是「不得依 tier 分流」的機械守衛**。
- **變異檢驗雙向**：只改 card.py → 同一性測試紅；只改 doctor.py → 同樣紅；還原後兩檔 sha256 IDENTICAL（diff exit 0）。
- ⚠️ **對照組換了形狀並把原因釘住**：卡面驗收 (b) 原文寫「一張已由 handoff 明示移到 📥Backlog 的卡必須判 consistent」——**機械上不成立**，derive_expected_status 對 handoff 一律回 UNDECIDABLE_HANDOFF（handoff 的 Log 行構造上不記狀態），永遠拿不到 consistent。此為既有行為、與本卡無關。執行者改用 assign（其 Log 行帶「；交付狀態 X」）並新增三條斷言，其中一條刻意驗「同一事件但欄位停在 💡需求 → drift」以證明推導器沒有偏袒 💡需求。**⭐ 卡面驗收條寫錯的是 PM。**

【test_doctor.py:1762-1765 的語意反轉】舊：(drift, 📥Backlog, 💡需求)——從 Backlog 移到需求判成漂移，而那正是 PM 為符合閘門所做的補救，於是觀測面把合規記成異常。新：(drift, 💡需求, 📥Backlog)——方向調轉。斷言數量與強度不變（仍是逐字黃金值三元組），未刪除未弱化。九處 fixture 逐一分類，四處判不改（142/172/1753/test_registry.py:40）並各附「改後未轉紅」的理由。

⚠️ 執行者自列未驗 7 項，全數轉入派審詞，關鍵三項：(a) **既有 10 張違規卡未被修正**，本卡只讓未來的新卡不再發生；(b) **未在真實狀態面驗證**——所有 open 證據來自 FakeGhRunner mocked 路徑，「真的打到 GitHub 也是 💡需求」未經實測；(c) **未驗證新預設在真實工作流上的下游效應**（assign 從 💡需求 認領是否有其他前提檢查、doctor 其他軸對 💡需求 的呈現）。另：CONTRACT_TOOL_RECONCILE.md §6 的產生輸出大表未重貼，其 📥Backlog 那一列仍寫 ok 與舊行號（--check 不讀該表，但人讀會看到過期值）。。
- 2026-08-21T20:29:50+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex（需求方轉貼；收據 issuecomment-5369798326，PM 逐字轉錄）；core_pain_resolved yes；self_run 5 項；findings 3 項（blocking 3）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-OPEN-INITIAL-STATUS1-e0-6e2e1707d8cce55a62ac50cff57243405bc9d93c。
- 2026-08-21T22:15:13+08:00 handoff by wf-cli → owner 待指派；iteration 0；SHA 2ae1ff0be3ae78f38392b81e1c5b3fe9409c79b8；證據 ⏸阻塞：本卡被 R1-002 要求的「另卡」擋住，而該另卡又被本卡擋住——機械死結，故釋放資源等對方先跑。

【死結的機械成因（PM 實查）】R1-002 的 disposition 逐字要求「需求方／PM **另卡**決定並實作受檢查的專責轉換，或正式移除 Backlog；**完成前不得合併本卡**」。PM 研究該另卡要動什麼：handoff_cmd.py:87 的 STAGE_STATUS ＋ :280 的 choices 要加 backlog；⭐ doctor.py:1229 自陳「前五個鏡射 commands/handoff_cmd.py 的 STAGE_STATUS」故必須同步；測試側涉及 test_doctor.py、test_commands_mocked.py（可能還有 test_release_cleanup.py、test_review.py）。⇒ **與本卡宣告的五個檔撞三個**（doctor.py、test_doctor.py、test_commands_mocked.py）。

⚠️ **而本卡擋得住它**：assign 的交集檢查（assign_cmd.py:226-229）以 card.py:240-248 的 is_owner_assigned 判斷，該函式用 startswith(_OWNER_PLACEHOLDER_PREFIXES)，而本卡 review 後的 owner 是「跨家族查核（待指派）」——**開頭是「跨家族查核」不是佔位詞，判定為已認領**。⭐ 那個字串**讀起來像未認領、機械上卻是已認領**，PM 今日一直在用它而到現在才知道語意與字面相反。

⇒ 本卡不能合併（要等另卡）、另卡不能開工（被本卡擋住）。**標 ⏸阻塞 並把 owner 退回「待指派」是唯一不需要推翻任何 finding 的解法**——⭐ 而 ⏸阻塞 正是為這種情況設計的狀態，本卡現在確實是「被另一張卡擋住」，標成別的都不誠實。

【到期條件】backlog stage 卡（尚未開）完成並合併。屆時 R1-002 由該卡解決，本卡回到 implementation 做 R2。

【R2 待辦，逐項（不因本次阻塞而消失）】
- **R1-001**（blocking／coordinator）：⚠️ 「不得追認；PM 以**前向決策重切／重發完整寫入集**後再送審」。PM 須前向把 cli/tests/test_review.py 與 docs/CONTRACT_TOOL_RECONCILE.md 納入宣告並重發，**不是回頭批准**。⭐ 查核者把主要歸屬判給 coordinator，成因是本卡的派工包**沒有帶那條「動宣告外的檔要先請求擴權」的明文**，而 PM 同日的 cpbl#160 與 ai-workflow#39 派工包裡都帶了。
- **R1-002**（blocking／planner）：由 backlog stage 卡承接。
- **R1-003**（blocking／executor）：以本 SHA 的產生器重產 docs/CONTRACT_TOOL_RECONCILE.md §6 的整張輸出表並同步 aggregate（表列 Backlog=ok、缺口 55，而同 SHA 實跑為 read-only、缺口 56）。

【已通過、不必重做的部分】查核者驗證通過：三項強證據（T0–T4 五級端到端實證＋固化為「不得依 tier 分流」的機械守衛、雙向變異檢驗確實各自轉紅、還原後 sha256 IDENTICAL）、以及 handoff 改用 assign 的替代測試。⭐ core_pain_resolved = yes。

⚠️ 交付 SHA 6e2e1707d8cce55a62ac50cff57243405bc9d93c 與分支 claude/WF-OPEN-INITIAL-STATUS1 保留不動；worktree /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-open-initial-status1 保留供 R2 續作。**本次只改狀態面與 owner，不碰任何資源。**

⚠️ --iteration 釘住原值 0：本卡的 iteration 遞增應發生在 R2 的 handoff --next-stage implementation，不在本次阻塞登記。。
- 2026-08-22T12:27:56+08:00 amend by wf-cli（op 224065b8）→ 資源宣告：原值「## 資源宣告 <!-- resource-claims:begin --> ```json { "db_scope": "none", "resources": [ "file:cli/src/wf_cli/card.py", "file:cli/src/wf_cli/doctor.py", "file:cli/tests/test_doctor.py", "file:cli/tests/test_commands_mocked.py", "file:cli/tests/test_registry.py" ] } ``` <!-- resource-claims:end -->」→ 新值「db_scope=none；file:cli/src/wf_cli/card.py、file:cli/src/wf_cli/doctor.py、file:cli/tests/test_doctor.py、file:cli/tests/test_commands_mocked.py、file:cli/tests/test_review.py、file:docs/CONTRACT_TOOL_RECONCILE.md」；理由 R1-001（blocking，attribution=coordinator）的處置逐字為「不得追認；PM 以前向決策重切／重發完整寫入集後再送審」。本次即該前向重發，由 PM 執行。 原宣告五檔與 R1 實際交付六檔的落差：宣告了但未使用 cli/tests/test_registry.py；使用了但未宣告 cli/tests/test_review.py 與 docs/CONTRACT_TOOL_RECONCILE.md。⚠️ 本次不是把既成事實補登為合法，而是以現在的判斷重新切一次寫入集：移除確定不需要的 test_registry.py，納入實作上必然要動的 test_review.py 與 CONTRACT_TOOL_RECONCILE.md（後者是 contract_tool_reconcile.py 的產生物，本卡移除 card.py 的兩個 literal writer 後必然改變其產生輸出，R1-003 要求以本 SHA 的產生器重產整張表）。 R1-001 的根因有 coordinator 的份：本卡派工包未帶「需要動宣告外的任何檔時停下來回報請求擴權」的明文，而 PM 在同日的 cpbl-analytics#160 與 ai-workflow#39 派工包裡都帶了。重發後的派工包會帶這條。 ⭐ R1-002（blocking，attribution=planner）已解除：其處置為「需求方／PM 另卡決定並實作受檢查的專責轉換，或正式移除 Backlog；完成前不得合併本卡」。承接卡 ai-workflow#120 WF-BACKLOG-STAGE1 已於 2026-08-22 經六輪跨家族查核 APPROVE 並合併（merge commit 2dcab60，PR 123，tests 與 tests (branch head) 兩支 check 皆 SUCCESS），實作了依級別分流的受檢查 backlog 轉換：T2 以上要求前身狀態為 🧭規劃中、T0/T1 直通、級別讀不到 fail closed，規則先寫進 canonical AI_WORKFLOW.md §3.1 且有測試讀正文比對。故本卡的合併前提已成立。 ⚠️ 基線同步前移：本卡分支基於 2ae1ff0b，而 main 已前進至 2dcab60。#120 大幅改動 doctor.py、test_doctor.py 與 docs/CONTRACT_TOOL_RECONCILE.md，且新增了 scripts/canonical_citation_scan.py 這道全 repo 開放集合守衛（任何點名 canonical 而夾帶行號的引用會轉紅）。續作須先對齊新 main。。
- 2026-08-22T12:28:55+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子代理）；iteration 1；SHA 6e2e1707d8cce55a62ac50cff57243405bc9d93c；證據 解除阻塞並交回執行者，iteration 遞增至 1。R1-002 的阻塞條件已消滅：承接卡 ai-workflow#120 WF-BACKLOG-STAGE1 於 2026-08-22 經六輪跨家族查核 APPROVE 並合併（merge commit 2dcab60、PR 123，ruleset 要求的 tests 與 tests (branch head) 兩支 check 皆 SUCCESS），實作了依級別分流的受檢查 backlog 專責轉換，故本卡「完成前不得合併」的前提已成立。

R1-001（coordinator）已由 PM 前向重發完整寫入集處置完畢（amend op 224065b8）：移除確定不需要的 cli/tests/test_registry.py，納入 cli/tests/test_review.py 與 docs/CONTRACT_TOOL_RECONCILE.md，共六檔。⛔ 不是追認既成事實，是以現在的判斷重新切一次。⚠️ PM 同時認自己的份：本卡原派工包未帶「動宣告外的檔要停下請求擴權」明文，而同日 cpbl-analytics#160 與 ai-workflow#39 的派工包都帶了；重發後的派工包會帶。

剩 R1-003（executor，blocking）待執行者閉環：以本 SHA 的產生器重產 docs/CONTRACT_TOOL_RECONCILE.md 的整張輸出表並同步 aggregate。

⚠️ 基線前移：本分支基於 2ae1ff0b，main 已至 2dcab60。#120 大幅改動 doctor.py、test_doctor.py、docs/CONTRACT_TOOL_RECONCILE.md，並新增 scripts/canonical_citation_scan.py 這道全 repo 開放集合守衛。續作須先對齊新 main，且任何點名 canonical 而夾帶行號的引用會讓該守衛轉紅。。
- 2026-08-22T12:52:47+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 1；SHA 1be6bc9ef70367f8526b99b59a1790fbdf9e2aa4；證據 R2 交付 1be6bc9e（基線 2dcab60，執行者自己實跑取得非抄錄）。寫入集六檔與 PM 前向重發的宣告完全相同、集外零改動。PM 獨立複驗：git diff --name-only origin/main..HEAD 逐字為那六檔；origin/main 是 HEAD 祖先故合併結果構造上等於分支頭；CI 以 --commit 1be6bc9e 鎖 SHA 為 success（run 32552687144）。

對齊方式選 merge 不 rebase（merge commit 0bbd5a5，雙親 6e2e170 與 2dcab60），三條理由：R1 已被查核且三個 finding 以 SHA 為錨、rebase 會讓證據指向不存在的物件；本 repo 既有分支對齊一律走 merge；merge 後 origin/main 是 HEAD 祖先。⭐ 該 merge commit 使用了 ai-workflow#119 昨日寫進 canonical 的「不適用」值域 Reviewed-by: —（基線更新 merge，無查核對象），PM 複驗屬實，這是該條文首次實際使用。執行者並自陳該 merge commit 原本漏了 trailer、以 reset 加 amend 加 cherry-pick 補上且 tree hash 前後逐字相同 055b6f70。

⭐ 執行者更正了 PM 的探測結論。PM 先前轉給它的訊息報 canonical_citation_scan.py SCAN_EXIT=0，但那是必要而非充分條件：pytest 另抓到第二支紅 test_doctor.py::test_canonical_citations_do_not_regrow_line_numbers，因為 R1 的註解把 AI_WORKFLOW.md 與 §3.1 與 T3 寫在同一行，而 #120 的 doctor 守衛禁止點名 canonical 的行夾帶任何數字（比 canonical_citation_scan.py 的冒號數字規則更嚴）。歸屬為 coordinator：PM 的探測只跑了較寬鬆的那一支就報給執行者。

R1-003 閉環：以對齊後的產生器重產，📥Backlog 仍判 ok、缺口 55 加守衛 3 等於 58 與 main 相同，本卡未製造新缺口。⭐ #120 的 §4.1.1 早就預測「#118 合併後 handoff_cmd.py 讓它不會掉回 read-only」，預測成立；R1 當時的相反宣稱已由執行者收回。

⭐ 三項要查核者評估品質：其一，#118 與 #120 的組合自洽性執行者不用散文宣稱、直接跑成測試 test_open_default_still_reaches_backlog_through_the_checked_transition（T3 卡開出來停 💡需求、直接入池被擋回 4、走 planning 後入池成功），並做兩方向變異（card.py 預設改回 📥Backlog 紅、閘門對所有級別放行紅）、已還原且 git diff 乾淨。其二，執行者逐條說明四類測試改動的理由，並自陳「沒有把紅的改綠、#118 本身的判準在 R1 就釘死本輪一格未動、斷言只增不減」。其三，它指出 #120 的一處註解理由在本卡之後為假（該註解寫「本 repo 現行的 open 預設就是 📥Backlog」），保留步驟但換成更強的理由。

執行者自陳未驗到：合併結果的 CI 沒跑過（此分支無 PR，只有 push 事件的 tests (branch head)，而 CI 設定明說那永遠不是 required check；抓到 2026-08-12「分支頭綠、合併結果紅」的是 pull_request 那一支；緩解是 origin/main 已是 HEAD 祖先故合併結果構造上等於分支頭，但那是推論不是跑過）；引用片段的逐字性只有手動比對、沒有守衛（canonical_citation_scan.py 自己的 docstring 承認只驗形態，doctor.py 的三個具名錨點有守衛但新加的片段不在其中）；cpbl docs/ROADMAP.md 是跨 repo 引用、本 repo 任何守衛都掃不到；--status 逃生口與 amend --tier 繞閘門皆為 #120 已登記的既有限制、本卡未處理；變異只做兩個方向沒有窮舉，第三個顯然的方向（handoff Log 行開始記狀態則 undecidable 應轉紅）只寫進 docstring 沒有實跑；📦已合併 的錨點由 doctor.py:1699 漂移到 :1715 是擴寫註解造成、屬文件自己聲明的漂移不算缺口變化。

執行者回報的驗證：基線 2dcab60 pytest 1080 passed、交付 1083 passed（加 3 新測試）；reconcile --check 兩端皆 exit 0 且 58 缺口；canonical_citation_scan.py 兩端皆 exit 0 命中 0、123 檔；uv lock --check 與 escalation replay 114-114 通過；CI log 自陳 checked-out 與 cli tree hash 與本機相同；trailer 用 repo 自己的檢查器跑三個 commit 全 compliant。PM 未複跑 pytest。。
- 2026-08-22T13:44:23+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex（需求方轉貼；無 GitHub 收據留言，PM 逐字轉錄）；core_pain_resolved yes；self_run 9 項；findings 3 項（blocking 2）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-OPEN-INITIAL-STATUS1-e0-1be6bc9ef70367f8526b99b59a1790fbdf9e2aa4。
- 2026-08-22T14:27:35+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code（子代理）；iteration 2；SHA 1be6bc9ef70367f8526b99b59a1790fbdf9e2aa4；證據 R2 REQUEST_CHANGES 退回原執行者、原分支、原 worktree，iteration 遞增至 2。R2-003 為 info 非阻擋、不需處理。兩個 blocking：

R2-001（對齊 merge 未滿足 canonical §6.1 狹義例外）：查核者裁定 6e2e170 在 trailer epoch 之後、且 2dcab60 沒有引用該 SHA，兩個條件皆不成立，故應依 §7.3 走 rebase 加 force-with-lease。⭐ PM 已於 2026-08-22 經需求方授權先行 push 保存 tag refs/tags/reviewed/WF-OPEN-INITIAL-STATUS1-r1 指向 6e2e1707d8cce55a62ac50cff57243405bc9d93c，趁 rebase 尚未孤立該物件時保住它；遠端複驗已存在。⇒ 執行者對「rebase 會讓 finding 的 SHA 錨點指向不存在物件」的顧慮本身成立，但出口是保存 tag 不是改用 merge——先例為 ai-workflow#120 R2-002 的 reviewed/WF-BACKLOG-STAGE1-r1，同一形狀。⛔ 執行者不需動任何 tag。

R2-002（測試註解宣稱一個它殺不掉的變異）：查核者在隔離副本把 handoff Log 加入交付狀態欄位後，test_drift_explicit_move_to_backlog_is_consistent_and_handoff_stays_undecidable 仍 1 passed，因該測試用固定的 _HANDOFF_LINE、未連到 writer 輸出。處置為移除該保證或改成真正從 handoff 輸出餵入 doctor 的測試。

⚠️ PM 註記：這是 2026-08-22 一夜內同一形狀的第三次（ai-workflow#120 R6-001 的 ISO 專測、ai-workflow#124 修的同一條、本項）。PM 已量測全庫此類散文宣稱共 121 行（ai-workflow 59、cpbl-analytics 62，且只抓中文五種寫法故為下界），將另開形狀卡處理。⛔ 本輪不得試圖在 R3 解決系統性問題——照查核者處置修這一處即可，擴射程會讓已跑兩輪的卡再擴一次。

R2 已通過項不重驗、不擴審：R1-001 三項閉環判定全部通過、組合測試兩個變異已由查核者自行重跑、R1-003 重產判定通過、測試改動判定斷言未被弱化。。
- 2026-08-22T15:26:27+08:00 handoff by wf-cli → owner 跨家族查核（待指派）；iteration 2；SHA 1c2700d729aa4adf4ccbd43885a1450d93af16ff；證據 R3 交付 1c2700d（基線 2dcab60）。⚠️ 過程異常已揭露：原執行者隨 process 結束死亡，工作已 commit 但未 push、未交驗證報告；PM 重派第二位執行者接手「驗證前者所做、補齊缺的證明、然後 push」，⛔ 非重做。本報告的證明由第二位執行者產出。

PM 獨立複驗：遠端已更新至 1c2700d（force-with-lease 釘 1be6bc9 成功）；寫入集恰為宣告六檔；CI 以 --commit 1c2700d729 鎖 SHA 為 success（run 32559354838）。

R2-001（對齊 merge 未滿足 §6.1 狹義例外）閉環：已改走 rebase，origin/main 是 HEAD 祖先、0 個 merge commit。⭐ PM 已於 rebase 前 push 保存 tag reviewed/WF-OPEN-INITIAL-STATUS1-r1 指向 R1 的 6e2e170，複驗仍指該 SHA；⚠️ 並於本次 push 後補建 reviewed/WF-OPEN-INITIAL-STATUS1-r2 指向 R2 的 1be6bc9（force-push 已使其不在任何遠端 ref 上，PM 實查確認）。⭐ PM 自陳：r1 是事前建立、r2 是事後補救，順序上事前較安全。

R2-002（測試註解宣稱一個它殺不掉的變異）閉環，且證明強度高於卡面要求：

⭐ 執行者先破解了 PM 三次無效變異檢驗的成因——PM 在 cwd 直接 import 走了不同解析路徑，執行者改用 pytest plugin 在 pytest 自己的 process 內於 pytest_collection_finish 印出模組身分，實得 handoff_cmd.__file__ 指向 worktree 而非副本，sha256 8d321c22（原檔 f665d624）且 MUTATION MARKER present 為 True，證明改動確實生效於受測模組。

證明一：把 handoff_cmd.py:549 的 f-string 加上交付狀態欄位後，新測試轉紅於 assert written_status not in line，錯誤訊息含實際 Log 行。⭐ 跑全套得 1 failed 1083 passed——全 repo 只有這一條抓得到該變異、它是唯一守衛。另兩條斷言各以獨立變異驗證可證偽：改記 next-stage 鍵紅在 stage not in line、改前綴紅在 startswith，與 docstring 自述「先紅的是 startswith 那行」吻合。

證明二：docstring 第二項宣稱為真、不必改。執行者用變異後產生器的真實輸出（⛔ 非手構樣本，刻意避開「複驗要用會通過的樣本」的坑）餵進 audit_state_face_drift，六個 stage 全數仍 undecidable／UNDECIDABLE_HANDOFF；⭐ 並加 line_carries_status=True 當防空轉自檢，確認樣本真的是夾帶狀態的形狀而非無效證據。根因在 doctor.py:1433-1434 確為無條件短路、從不看行內容。順帶證實 R2-002 的前提：舊測試在同一變異下照樣綠，被撤除的那句保證確實是假的。

證明三：還原後七檔 sha256 前後完全一致、git status 空、HEAD 仍 1c2700d。

執行者自陳未驗到：基線 2dcab60 為 1080 這個數字未獨立複驗（只驗 HEAD 1084 與變異下 1+1083）；卡片主體語意未查核——card.py／doctor.py／test_review.py／CONTRACT_TOOL_RECONCILE.md 中「開卡落 💡需求 而非 📥Backlog」這個實質變更只確認測試全綠，⛔ 沒有回頭對 canonical 判斷它對不對，明言那是查核者的事；該測試封不住的開放集合（狀態以字面與 stage 鍵之外的編碼進 Log 時看不見，docstring 已自陳、執行者複核屬實）；--status 覆寫路徑與 release stage 未被迴圈直接跑到，但 src 全域只有一處產生該 Log 行（handoff_cmd.py:548，讀取端 doctor.py:1433），該結構性保證由測試末行的 count 等於 1 釘住而非散文宣稱；無 PR 故只有 push 事件那一支 tests (branch head)。

⚠️ 請查核者特別注意：執行者明言「卡片主體語意我沒查核」。本卡的實質變更（open 的初始狀態改 💡需求、doctor 的 OPEN_INITIAL_STATUS 同步、test_doctor.py 那條「合規補救被判成漂移」的斷言語意反轉）在 R1 已判閉環，但 R3 的執行者未再複核，⛔ 該部分需查核者自行確認未因 rebase 而語意漂移。。
- 2026-08-22T15:42:52+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex（需求方轉貼；無 GitHub 收據留言，PM 逐字轉錄）；core_pain_resolved yes；self_run 8 項；findings 0 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-OPEN-INITIAL-STATUS1-e0-1c2700d729aa4adf4ccbd43885a1450d93af16ff。
- 2026-08-22T15:50:01+08:00 handoff by wf-cli → owner —；iteration 2；SHA 1c2700d729aa4adf4ccbd43885a1450d93af16ff；證據 需求方 2026-08-22 授權合併。PR 127 以 merge commit 251e211 落 main，四個 trailer 齊全含 Reviewed-by: GPT-5@Codex；PR 的 tests（merge ref）與 tests (branch head) 兩支 check 皆 SUCCESS，故合併結果經 CI 實測而非推論。

⚠️ 合併前需再次對齊：查核通過的 1c2700d 基線是 2dcab60，而 main 已前進至 238ef94（#124 合併）。canonical §6.1 的狹義例外兩項皆不成立（1c2700d 在 TRAILER_GUARD_EPOCH 之後、238ef94 未引用它），故依 §7.3 走 rebase 至 7f63da0。⭐ 保存 tag reviewed/WF-OPEN-INITIAL-STATUS1-r3 於 rebase 之前建立，指向查核通過的 1c2700d——R3 查核者對前一輪事後補建的 tag 裁定「不構成 finding 但屬較弱的恢復措施」，本次採較強形態。三個保存 tag（-r1 指 6e2e170、-r2 指 1be6bc9、-r3 指 1c2700d）皆在遠端。

PM 對齊後複驗：零檔案交集（#124 只動 test_canonical_citation_scan.py，本卡六檔無交集）、rebase exit 0 零衝突、origin/main 是 HEAD 祖先、0 個 merge commit、四個抽驗檔案的 blob 與 1c2700d 逐字相同、三筆 commit trailer 齊全、全套 pytest 1084 passed。

本卡三輪的軌跡：R1 三個 blocking（寫入集未宣告 coordinator／backlog 轉換無專責 writer planner／產生表未重產 executor），第二項引發承接卡 ai-workflow#120，本卡因此 ⏸阻塞七輪；R2 兩個 blocking（對齊 merge 未滿足 §6.1、測試註解宣稱一個它殺不掉的變異），期間執行者隨 process 結束死亡、工作已 commit 未 push，PM 重派第二位接手驗證並 push；R3 APPROVE、findings 空。

已知限度（查核者確認、本卡不處理）：assign 仍可無條件覆寫交付狀態（assign_cmd.py:255），本卡不關那個口；但本卡讓它的每一次使用留下可見痕跡——💡需求 → 🔨執行中 一眼看得出跳過三格，舊行為下 📥Backlog → 🔨執行中 看起來正常。該口的處置屬 ai-workflow#122 的射程。；收尾清理：已清除 worktree、本地分支、遠端分支。
- 2026-08-26T22:17:01+08:00 amend by wf-cli（op 0d759e7c）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:256eb4fc71836f427d8bc56743ba2d7ddd058966f4f11099cb95e36e6fd81f14 (776 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5369483958 · 2026-08-21T11:53:56Z

## ⭐ 本卡是它自己的第一個展品

`wfcli open` 剛剛把本卡寫成 **`📥Backlog`** —— 正是本卡要修的那個預設。

⚠️ **但這一次不需要補救**：規劃閘門（canonical §3.1 的 T3「核心痛點三問」）**在開卡之前就已經與需求方跑完**，本卡是那場對話的產物：

- **痛點是什麼** —— 前端／工具與規則對「新卡的初始狀態」給出不同答案，且 doctor 把違規釘成基準（`doctor.py:1251`）
- **成功怎麼觀察** —— 開一張新卡，交付狀態欄是 `💡需求`；且一張明示移到 `📥Backlog` 的卡不再被 `audit_state_face_drift` 判為漂移
- **最大的未驗證前提** —— ⚠️ 「一律 `💡需求`（不依 tier 分流）對 T0／T1 也是對的」。canonical `AI_WORKFLOW.md:113` **只點名 T3**；採用專案 `cpbl ROADMAP §2.0` 說「所有新卡」。需求方 2026-08-21 裁定採後者（甲案），**理由是保守方向可逆而反向不可逆**，但這個前提本身沒有第三方驗證

⭐ **所以本卡停在 `📥Backlog` 是正確的**，不是又一次違規。**這件事本身就是證據**：現行預設讓「合規」與「違規」在狀態面上長得一模一樣 —— 你無法從欄位值分辨這張卡是「閘門過了」還是「工具直接丟進來的」。

⚠️ **而依 `test_doctor.py:1765`，如果 PM 依 §2.0 把一張卡從 `📥Backlog` 移回 `💡需求`，`audit_state_face_drift` 會判它是 `drift`。** 也就是說：**觀測面今天無法區分違規與補救，而且把補救判成異常。**

## 派工前的資源盤點（實測，非推論）

本卡宣告的五個檔與現有 open 卡的交集：

| 檔 | 也被誰宣告 |
|---|---|
| `cli/src/wf_cli/card.py` | `#105` |
| `cli/src/wf_cli/doctor.py` | `#30` |
| `cli/tests/test_doctor.py` | `#30` |
| `cli/tests/test_commands_mocked.py` | **`#57` `#66` `#84` `#86` `#91` `#105`**（六張的 clique） |
| `cli/tests/test_registry.py` | `#57` |

⚠️ **今天不會響** —— 那些卡全部 `owner=待指派`，`assign_cmd.py:227-230` 的 `find_conflicts` 對未認領的卡 `continue`。**但本卡一旦認領就佔住那個 clique 的核心檔**，`#30`／`#57`／`#66`／`#84`／`#86`／`#91`／`#105` 在本卡 release 前都不能派。

⭐ 需求方 2026-08-21 已知悉此代價並裁定本卡優先 —— 理由是 `#84`／`#91` 是「已咬過三次」與「還沒咬過」，而本卡是**每天都在咬、且沒有任何東西會發現**。


## Comment 5369685290 · 2026-08-21T12:16:04Z

## 派審：ai-workflow#118 `WF-OPEN-INITIAL-STATUS1` R1

⚠️ 審核對象 **`ruan6047/ai-workflow#118`**。⭐ 卡面第 4 行明訂查核者須**跨模型家族或人工**。

```
被審 SHA：6e2e1707d8cce55a62ac50cff57243405bc9d93c
基線：    2ae1ff0be3ae78f38392b81e1c5b3fe9409c79b8（git merge-base origin/main HEAD）
分支：    claude/WF-OPEN-INITIAL-STATUS1
worktree：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-open-initial-status1（乾淨，供進駐）
iteration：1　單一 commit，6 檔 +88/−15
```

### 這張卡在解什麼

`wfcli open` 把每一張新卡直接寫成 `📥Backlog`，而那是規劃閘門通過**之後**才該到的狀態（canonical `AI_WORKFLOW.md:113`；採用專案 `cpbl ROADMAP §2.0`「所有新卡一律由 `💡需求` 開始」）。⭐ **`card.py` 自己在 `:732` 記著這條規則，然後在 `:295` 預設違反它**；而 `doctor.py:1251` 把違規釘成 `OPEN_INITIAL_STATUS`，所以 doctor 也不會發現。

⭐ 最直接的證據在 `cli/tests/test_doctor.py:1765`：今天，一張卡從 `📥Backlog` 移到 `💡需求` 被判為 **`drift`**——**而那正是 PM 為符合閘門所做的補救動作。觀測面把合規記成異常。**

三天十次，每一張新卡。

### PM 獨立複驗（請你再獨立跑一次）

| 項目 | 結果 |
|---|---|
| `card.py:295` / `doctor.py:1261` | 皆為 `💡需求` |
| `cd cli && uv run --frozen pytest -q` | **1054 passed**（改動前 1052，+2 皆新增，無刪除無 skip 無 xfail） |
| `contract_tool_reconcile.py --check` | **真實 exit code = 0**（未接管線） |

---

## ⚠️ 兩項要你裁定的

### (1) 改了兩個宣告外的檔，且是**先寫後揭露**

`cli/tests/test_review.py`（`:542`／`:624`／`:680`／`:684`，改後轉紅故必改）與 `docs/CONTRACT_TOOL_RECONCILE.md`。⚠️ 與 `cpbl#157` 的「事前停手請求擴權」相反、與 `cpbl#134` R1-002 同形。

⭐ **但 PM 必須先認自己的部分**：**本卡的派工包沒有帶那條「需要動宣告外的任何檔時停下來請求擴權」的明文**，而 PM 在同日的 `cpbl#160` 與 `ai-workflow#39` 派工包裡**都帶了**。**這是 coordinator 的疏漏，attribution 不應全歸 executor。**

執行者確實做了衝突檢查（21 張 open 卡的 `resource-claims` 全數解析，無一宣告那兩個檔），也在報告首節主動標為「請優先看」。

⚠️ **PM 沒有事後補擴權**——那會變成追認。**請你判 attribution 與 severity。**

另：宣告的 `cli/tests/test_registry.py` **未被改**（執行者判為「測 Ledger 欄位切分，值只是被解析的儲存格」）——宣告 ⊇ 實際是安全方向。

### (2) ⭐ 本卡讓 `📥Backlog` 變成沒有專責 writer 的狀態

`card.py:295` 與 `doctor.py:1251` **是該字面僅有的兩個 writer**。兩處消失後 `contract_tool_reconcile` 對它的判定由 `ok` 翻成 `read-only`，`--check` 當場 exit 1（實際缺口 59、登記 58）。

執行者依該檔 §6「**登記＝承認缺口，不是消除缺口**」把它登記進處置表，**沒有補動詞**（卡面非目標明列不新增旗標）。

⇒ 規劃閘門過了之後，**現在只剩 `assign --status` 與 `handoff --status` 兩個自由文字逃生口**把卡送進 Backlog。

**請你判**：(a) 這個處置是否正當？(b) 「登記缺口而不補動詞」在本卡射程內是否夠？(c) 是否該成為一項 finding（要求另開卡補專責動詞）？

---

## ⭐ 執行者的三項強證據（請驗它們對不對）

1. **端到端實證**：以 mocked 路徑對 **T0–T4 五級各實跑一次 `open`**，五級交付狀態皆 `💡需求`，並固化為常設測試 `test_open_initial_status_is_the_same_for_every_tier`——⭐ **它同時是「不得依 tier 分流」的機械守衛**。
2. **變異檢驗雙向**：只改 `card.py` → 同一性測試（`test_doctor.py:1753`）紅；只改 `doctor.py` → 同樣紅；還原後兩檔 sha256 `IDENTICAL`（`diff` exit 0）。
3. ⚠️ **對照組換了形狀並把原因釘住**——**卡面驗收條寫錯的是 PM**。

### ⭐ PM 的驗收條 (b) 機械上不成立

原文：「一張已由 **handoff** 明示移到 `📥Backlog` 的卡必須判 `consistent`」。

實測：`derive_expected_status` 對 `handoff by wf-cli` 一律回 `UNDECIDABLE_HANDOFF`——**handoff 的 Log 行構造上不記 next-stage 也不記 `--status`**，永遠拿不到 `consistent`。**此為既有行為、與本卡無關、本卡也沒改。**

執行者改用 `assign`（其 Log 行帶「；交付狀態 X」），新增三條斷言，其中一條刻意驗「**同一事件但欄位停在 `💡需求` → drift**」以證明推導器沒有偏袒 `💡需求`。**請判這個替代形狀是否可接受。**

---

## `test_doctor.py:1762-1765` 的語意反轉

| | 舊 | 新 |
|---|---|---|
| consistent | 預期 `📥Backlog` | 預期 `💡需求`（閘門在開卡之後才跑，開卡當下不可能已通過） |
| drift | `("drift", "📥Backlog", "💡需求")` | `("drift", "💡需求", "📥Backlog")` |

**斷言數量與強度不變**（仍是逐字黃金值三元組），變的只有「哪個值是預期」。**未刪除、未弱化任何斷言。**

九處 fixture 逐一分類，其中**四處判不改**（`test_doctor.py:142`／`:172`／`:1753`、`test_registry.py:40`）並各附「改後未轉紅」的理由。⭐ **請抽驗那四處的分類是否正確**——若其中有一處其實該改而沒改，測試就有一塊沒被更新的語意。

---

## ⚠️ 執行者自列未驗七項（全數轉入）

1. **既有 10 張違規卡未被修正**——本卡不動任何既有卡的狀態，`#147`／`#148`／`#138`／`#139`／`cpbl#160`／`cpbl#161` 等仍停在 `📥Backlog`。**那是既成事實，本卡只讓未來的新卡不再發生。**
2. ⭐ **未在真實狀態面驗證**——所有 open 證據來自 `FakeGhRunner` mocked 路徑；未跑任何 wfcli 寫入動詞打真 Project（卡面禁止）。**「真的打到 GitHub 也是 `💡需求`」未經實測。**
3. **未驗證新預設在真實工作流上的下游效應**（`assign` 從 `💡需求` 認領是否有其他前提檢查、`doctor` 其他軸對 `💡需求` 的呈現）。全套綠只證明既有斷言未破。
4. **`📥Backlog` 失去專責動詞的操作面後果未量測**。
5. **未驗證「一律 `💡需求` 對 T0/T1 也更好」**——卡面自陳的最大未驗證前提，執行者只把需求方裁定固化成測試。
6. **未跑 CI**（分支已 push，GitHub Actions 結果未觀測；本機跑了三個等價步驟）。
7. `CONTRACT_TOOL_RECONCILE.md` §6 的**產生輸出大表未重貼**，其 `📥Backlog` 那一列仍寫 `ok` 與舊行號（`--check` 不讀該表，**但人讀會看到過期值**）。

---

## 交付格式

依 `templates/review-prompt.md` §5。三項強制：

1. **逐項回報上面兩項裁定與三項強證據的驗證結果**並附你自己的證據
2. **五個 schema 欄位自己填**
3. **留收據**：多行格式、報告全文同帖、取材規則寫死並寫明起訖 delimiter 是「本規則之後的下一個」

⚠️ **留言中不得出現 review 事件那個機讀前綴的完整字樣**（前綴後緊接半形冒號）——引用即停機。轉述時寫「event marker」。

⚠️ **不得 merge**。⚠️ **不得跑任何 wfcli 寫入動詞**（狀態面由 PM 寫）。


## Comment 5369798326 · 2026-08-21T12:27:49Z

<!-- wf-review-receipt:v1
card_id: WF-OPEN-INITIAL-STATUS1
source_sha: 6e2e1707d8cce55a62ac50cff57243405bc9d93c
report_sha256: 9f8908061e8ab376410267d55e4303cd3c47823fa4b27d7b765a14ac46480432
-->

取材規則：UTF-8、LF、無 strip；雜湊範圍起點是本規則之後的下一個 `--- report-begin ---` delimiter 結束 LF 後的第一個位元組，終點是其後下一個 `--- report-end ---` delimiter 前的 LF（該 LF 不含）；排除 receipt HTML 註解、本規則、兩個 delimiter 行及其餘文字。

--- report-begin ---
核心痛點 [core pain] 已消失：`wfcli open` 的五個 T0–T4 mocked 開卡路徑皆寫入 `💡需求`，而 `audit_state_face_drift` 現在會把沒有事件依據的 `📥Backlog` 判為 drift。

但本輪仍為 `REQUEST_CHANGES`。原因不是前述修正失效，而是它留下（且文件錯誤呈現）一個不可由專責動詞完成的 `💡需求 → 📥Backlog` 正常轉換，另有未宣告寫入集的治理缺口。

## 逐項裁定

### (1) 宣告外兩檔、先寫後揭露

**成立，major／blocking；主要歸屬 coordinator。** 卡面的 resource claim 只有五檔，提交實際改六檔；`cli/tests/test_review.py` 與 `docs/CONTRACT_TOOL_RECONCILE.md` 未列其中。派工包漏掉「碰到宣告外檔案先停下請求擴權」條款、而 preflight 也未攔下實際 diff，故主要根因與修復所有權在 coordinator。執行者仍有次要流程違反：既有 resource claim 與 canonical §2.11／§4.4 已足以表達寫入邊界，不能因派工包漏句而自行擴寫；事後揭露與衝突檢查可減輕風險，不能倒推成事前授權。

不可事後擴權追認。應由 PM 以前向決策重新發卡／重切提交，完整宣告這兩檔及其必要驗證，再重做該部分工作；本 SHA 不可在保留此 mismatch 的情況下合併。此 finding 的 schema attribution 採 coordinator，故不構成 executor escalation 計數。

### (2) `📥Backlog` 沒有專責 writer

**「登記缺口」是誠實且在本卡非目標內的正當停手；但不是足夠處置，且應成為 major／blocking finding（歸屬 planner）。** `contract_tool_reconcile` 的現況輸出把 `📥Backlog` 判為 `read-only`；我另掃 production 寫入位置，除 Project 選項列舉外沒有 `📥Backlog` 的專責賦值。`assign --status`／`handoff --status` 都是自由文字逃生口，不能取代「規劃閘門已通過」這個具名、受前提檢查的狀態轉換。

所以執行者不應暗中補旗標；但 canonical 明定規劃閘門通過後進 Backlog，現在沒有合規的正常路徑。需求方／PM 必須另以顯式決策建立後續卡：設計並實作專責轉換，或裁定從狀態機移除 Backlog。前者完成（或後者改規則）前，本卡不能合併，否則會以修復初始值為代價讓既有階段不可操作。

### (3) 卡面驗收 (b) 的替代形狀

**可接受。** `handoff` 的 Log 沒有 next-stage 或 `--status`，`audit_state_face_drift` 對它構造性地回傳 `UNDECIDABLE_HANDOFF`，因此原驗收無法測到 `consistent`。`assign` 有逐字的 `交付狀態 X` segment，替代測試同時驗證：明示 `📥Backlog` 時為 consistent、同一事件而欄位仍是 `💡需求` 時為 drift、handoff 保持 undecidable。它保留了反向可證偽性，並非把推導器寫死成 `💡需求`。

這只接受作為漂移觀測的對照組；不改變上項裁定：可觀測的自由文字 override 不是專責 writer。

## 三項強證據與 fixture 抽驗

1. **T0–T4 端到端 mocked 實證：通過。** `test_open_initial_status_is_the_same_for_every_tier` 實跑五級後比對 Project 欄位，目標測試通過。
2. **雙向變異檢驗 [mutation testing]：通過。** 在隔離副本只把 `card.py` 改回 `📥Backlog`，同一性測試 1 failed；只把 `doctor.py` 改回 `📥Backlog`，也是 1 failed。兩邊皆直接失敗於 `test_drift_open_initial_status_is_pinned_and_open_has_no_status_knob` 的相等式。
3. **handoff→assign 對照：通過。** 見上項裁定；三個 golden assertions 都已實跑。
4. **四處不改 fixture：正確。** `test_doctor.py:142`／`:172` 是未認領 Backlog 的 worktree／lease 邊界，非 open 預設；`:1753` 是 Card 與 doctor 常數的同一性守衛，改常數而非改測試本體才是正確；`test_registry.py:40` 是 Markdown registry parser 的既有資料列。後者在 commit diff 中確實未改。

## 額外 blocking finding：生成輸出過期

`docs/CONTRACT_TOOL_RECONCILE.md` §6 的 disposition JSON 已正確新增 `delivery_status/📥Backlog: read-only`，但同檔自稱「產生輸出，非手寫」的大表仍列它為 `ok`、writer 為已移除的 `card.py:295`／`doctor.py:1251`，總缺口仍是 55。我的同一 SHA 重跑輸出為 Backlog=`read-only`、缺口=56；因此這個權威交付物 [authoritative artifact] 對人類讀者是錯的。`--check=0` 只驗 disposition，未驗該表，不能使舊表成立。

## 其他查核結果與限制

- 被審 worktree HEAD=`6e2e1707d8cce55a62ac50cff57243405bc9d93c`，乾淨；merge-base=`2ae1ff0be3ae78f38392b81e1c5b3fe9409c79b8`，皆與派審一致。
- GitHub branch-head CI 成功；目標回歸 4 passed。我的完整 suite 啟動後執行器未回傳終態，故不把 PM 的 1054 passed 當成我的 self-run；以 CI 成功與上述可重現目標測試分開列證。
- 未執行 merge、任何 wfcli 寫入動詞、爬蟲、訓練或資料重建。

```yaml
core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: "git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-open-initial-status1 rev-parse HEAD; git merge-base origin/main HEAD; git diff --quiet"
    observed: "HEAD=6e2e1707d8cce55a62ac50cff57243405bc9d93c；merge-base=2ae1ff0be3ae78f38392b81e1c5b3fe9409c79b8；工作區乾淨。"
  - command: "cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-open-initial-status1/cli && PYTHONPATH=$PWD/src uv run --no-sync pytest -q tests/test_commands_mocked.py::test_open_initial_status_is_the_same_for_every_tier tests/test_doctor.py::test_drift_open_initial_status_is_pinned_and_open_has_no_status_knob tests/test_doctor.py::test_drift_open_derives_requirement_and_flags_moved_face tests/test_doctor.py::test_drift_explicit_move_to_backlog_is_consistent_and_handoff_stays_undecidable"
    observed: "4 passed in 0.05s。"
  - command: "隔離副本各自把 card.py 或 doctor.py 的初始常數改回 📥Backlog，重跑 test_drift_open_initial_status_is_pinned_and_open_has_no_status_knob"
    observed: "兩方向均為 1 failed、156 deselected；相等式分別得到 💡需求 != 📥Backlog。"
  - command: "cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-open-initial-status1 && python3 scripts/contract_tool_reconcile.py --check; printf 'exit=%s\\n' $?"
    observed: "[reconcile] OK：59 個缺口全部有登記處置，exit=0；非 --check 輸出 Backlog=read-only、判定缺口=56。"
  - command: "gh api repos/ruan6047/ai-workflow/commits/6e2e1707d8cce55a62ac50cff57243405bc9d93c/check-runs"
    observed: "tests (branch head) conclusion=success。"
findings:
  - finding_id: WF-OPEN-INITIAL-STATUS1-R1-001
    severity: major
    blocking: true
    finding_class: governance
    attribution: coordinator
    root_cause_id: undeclared-write-set-and-missed-preflight
    evidence: "resource claim 五檔；被審 commit 六檔，新增 cli/tests/test_review.py、docs/CONTRACT_TOOL_RECONCILE.md。"
    disposition: "不得追認；PM 以前向決策重切／重發完整寫入集後再送審。"
  - finding_id: WF-OPEN-INITIAL-STATUS1-R1-002
    severity: major
    blocking: true
    finding_class: implementation
    attribution: planner
    root_cause_id: backlog-transition-has-no-dedicated-writer
    evidence: "兩個唯一 literal writer 移除後，reconcile 將 delivery_status/📥Backlog 判 read-only；只剩自由文字 --status。"
    disposition: "需求方／PM 另卡決定並實作受檢查的專責轉換，或正式移除 Backlog；完成前不得合併本卡。"
  - finding_id: WF-OPEN-INITIAL-STATUS1-R1-003
    severity: major
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: generated-reconcile-report-not-regenerated
    evidence: "文件產生表仍稱 Backlog=ok、缺口=55；同 SHA 的實跑輸出為 Backlog=read-only、缺口=56。"
    disposition: "在合法宣告的後續工作中，以本 SHA 的產生器重產整張輸出表並同步 aggregate。"
```

結論：三項核心行為證據及 assign 替代形狀均通過；但三項 blocking finding 未閉合，不得合併。 
--- report-end ---

## Comment 5369816777 · 2026-08-21T12:29:52Z

<!-- wf-review-event:v1 card_id=WF-OPEN-INITIAL-STATUS1 source_sha=6e2e1707d8cce55a62ac50cff57243405bc9d93c attempt_id=WF-OPEN-INITIAL-STATUS1-e0-6e2e1707d8cce55a62ac50cff57243405bc9d93c -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-OPEN-INITIAL-STATUS1`　attempt_id：`WF-OPEN-INITIAL-STATUS1-e0-6e2e1707d8cce55a62ac50cff57243405bc9d93c`
- 查核者：GPT-5@Codex（需求方轉貼；收據 issuecomment-5369798326，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`6e2e1707d8cce55a62ac50cff57243405bc9d93c`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-21T20:29:50+08:00

### self_run（查核者實跑）

- `git -C /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-open-initial-status1 rev-parse HEAD; git merge-base origin/main HEAD; git diff --quiet`
  - HEAD=6e2e1707d8cce55a62ac50cff57243405bc9d93c；merge-base=2ae1ff0be3ae78f38392b81e1c5b3fe9409c79b8；工作區乾淨。
- `cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-open-initial-status1/cli && PYTHONPATH=$PWD/src uv run --no-sync pytest -q tests/test_commands_mocked.py::test_open_initial_status_is_the_same_for_every_tier tests/test_doctor.py::test_drift_open_initial_status_is_pinned_and_open_has_no_status_knob tests/test_doctor.py::test_drift_open_derives_requirement_and_flags_moved_face tests/test_doctor.py::test_drift_explicit_move_to_backlog_is_consistent_and_handoff_stays_undecidable`
  - 4 passed in 0.05s。
- `隔離副本各自把 card.py 或 doctor.py 的初始常數改回 📥Backlog，重跑 test_drift_open_initial_status_is_pinned_and_open_has_no_status_knob`
  - 兩方向均為 1 failed、156 deselected；相等式分別得到 💡需求 != 📥Backlog。
- `cd /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-open-initial-status1 && python3 scripts/contract_tool_reconcile.py --check; printf 'exit=%s\n' $?`
  - [reconcile] OK：59 個缺口全部有登記處置，exit=0；非 --check 輸出 Backlog=read-only、判定缺口=56。
- `gh api repos/ruan6047/ai-workflow/commits/6e2e1707d8cce55a62ac50cff57243405bc9d93c/check-runs`
  - tests (branch head) conclusion=success。

### findings（3，其中 blocking 3）

- **WF-OPEN-INITIAL-STATUS1-R1-001**　severity=major　blocking=true　class=governance　attribution=coordinator　root_cause_id=`undeclared-write-set-and-missed-preflight`
  - evidence：resource claim 五檔；被審 commit 六檔，新增 cli/tests/test_review.py、docs/CONTRACT_TOOL_RECONCILE.md。
  - disposition：不得追認；PM 以前向決策重切／重發完整寫入集後再送審。
- **WF-OPEN-INITIAL-STATUS1-R1-002**　severity=major　blocking=true　class=implementation　attribution=planner　root_cause_id=`backlog-transition-has-no-dedicated-writer`
  - evidence：兩個唯一 literal writer 移除後，reconcile 將 delivery_status/📥Backlog 判 read-only；只剩自由文字 --status。
  - disposition：需求方／PM 另卡決定並實作受檢查的專責轉換，或正式移除 Backlog；完成前不得合併本卡。
- **WF-OPEN-INITIAL-STATUS1-R1-003**　severity=major　blocking=true　class=authoritative-artifact　attribution=executor　root_cause_id=`generated-reconcile-report-not-regenerated`
  - evidence：文件產生表仍稱 Backlog=ok、缺口=55；同 SHA 的實跑輸出為 Backlog=read-only、缺口=56。
  - disposition：在合法宣告的後續工作中，以本 SHA 的產生器重產整張輸出表並同步 aggregate。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-OPEN-INITIAL-STATUS1-e0-6e2e1707d8cce55a62ac50cff57243405bc9d93c
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（待指派）
findings:
  - finding_id: WF-OPEN-INITIAL-STATUS1-R1-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: governance
    attribution: coordinator
    root_cause_id: undeclared-write-set-and-missed-preflight
    counting_eligible: false
  - finding_id: WF-OPEN-INITIAL-STATUS1-R1-002
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: planner
    root_cause_id: backlog-transition-has-no-dedicated-writer
    counting_eligible: false
  - finding_id: WF-OPEN-INITIAL-STATUS1-R1-003
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: authoritative-artifact
    attribution: executor
    root_cause_id: generated-reconcile-report-not-regenerated
    counting_eligible: true
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5378259931 · 2026-08-22T05:44:24Z

<!-- wf-review-event:v1 card_id=WF-OPEN-INITIAL-STATUS1 source_sha=1be6bc9ef70367f8526b99b59a1790fbdf9e2aa4 attempt_id=WF-OPEN-INITIAL-STATUS1-e0-1be6bc9ef70367f8526b99b59a1790fbdf9e2aa4 -->
## 查核裁決：REQUEST_CHANGES

- 卡：`WF-OPEN-INITIAL-STATUS1`　attempt_id：`WF-OPEN-INITIAL-STATUS1-e0-1be6bc9ef70367f8526b99b59a1790fbdf9e2aa4`
- 查核者：GPT-5@Codex（需求方轉貼；無 GitHub 收據留言，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`1be6bc9ef70367f8526b99b59a1790fbdf9e2aa4`
- core_pain_resolved：**yes**
- 交付狀態：↩退回
- 寫入時間：2026-08-22T13:44:23+08:00

### self_run（查核者實跑）

- `核對 HEAD 與工作區`
  - HEAD 為指定的 1be6bc…e2aa4，工作區全程及結尾皆乾淨
- `git diff --name-only origin/main..HEAD`
  - 恰六檔，且與重發後資源宣告完全一致、未含 test_registry.py
- `pytest 於基線與交付各跑一次`
  - 基線 2dcab60 為 1080 passed；交付為 1083 passed
- `contract_tool_reconcile.py --check`
  - 兩端皆 exit 0、58 缺口；交付產生表為 55 加守衛 3
- `canonical citation scan 與 doctor 的第二守衛`
  - scan exit 0、123 檔、0 命中；doctor 第二守衛亦單獨通過
- `gh run 以精確交付 SHA 查詢`
  - run 32552687144 成功
- `核對承接卡與 tree hash`
  - PR 123 已合併至 2dcab60、tests 與 tests (branch head) 均成功；重做前的 7ac11db 與交付 SHA 的 tree hash 均為 055b6f70，tree 未變
- `隔離副本上把 handoff Log 加入交付狀態欄位後重跑`
  - test_drift_explicit_move_to_backlog_is_consistent_and_handoff_stays_undecidable 仍 1 passed
- `重跑組合測試的兩個指定變異`
  - 兩個變異都紅；移除「剛開卡直接入池必被擋」前半後，閘門全面放行仍可走完後半，確實會退化為零資訊

### findings（3，其中 blocking 2）

- **WF-OPEN-INITIAL-STATUS1-R2-001**　severity=major　blocking=true　class=governance　attribution=executor　root_cause_id=`rebase-exception-conditions-unmet`
  - evidence：對齊 merge 未滿足 canonical §6.1 的狹義例外：6e2e170 在 trailer epoch 之後，且 2dcab60 沒有引用該 SHA，兩個條件皆不成立。Reviewed-by 的「不適用」值域用法本身正確，但不能補足 merge 例外未成立。
  - disposition：例外雙條件不成立時應依 §7.3 走 rebase 加 force-with-lease。
- **WF-OPEN-INITIAL-STATUS1-R2-002**　severity=major　blocking=true　class=implementation　attribution=executor　root_cause_id=`comment-claims-a-mutation-kill-that-does-not-happen`
  - evidence：新增的測試註解宣稱「handoff Log 開始記狀態時測試會先紅」，實測為假：隔離副本把 handoff Log 加入交付狀態欄位後，該測試仍 1 passed。原因是測試使用固定的 _HANDOFF_LINE、未連到 writer 輸出。
  - disposition：移除該保證，或改成真正從 handoff 輸出餵入 doctor 的測試。
- **WF-OPEN-INITIAL-STATUS1-R2-003**　severity=info　blocking=false　class=environment　attribution=external　root_cause_id=`disclosed-gaps-acknowledged`
  - evidence：(a) 合併結果 CI 未跑、(b) 引用逐字性無守衛、(c) cpbl ROADMAP 跨 repo 引用無釘 SHA 的機械驗證、(d) --status 與 amend --tier 繞閘門、(e) 第三方向只寫 docstring 且已證實變異後測試仍綠——五項皆判為缺口但非 source defect；(f) 📦已合併 行號漂移判非缺口，產生器重跑與 --check 已確認判定不變。
  - disposition：(a) 合併前仍應取得實際合併結果的 required tests。(d) 為既有且已揭露、非本卡新引入。其餘列為後續缺口。

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-OPEN-INITIAL-STATUS1-e0-1be6bc9ef70367f8526b99b59a1790fbdf9e2aa4
escalation_epoch: 0
review_result: REQUEST_CHANGES
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（待指派）
findings:
  - finding_id: WF-OPEN-INITIAL-STATUS1-R2-001
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: governance
    attribution: executor
    root_cause_id: rebase-exception-conditions-unmet
    counting_eligible: false
  - finding_id: WF-OPEN-INITIAL-STATUS1-R2-002
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: comment-claims-a-mutation-kill-that-does-not-happen
    counting_eligible: true
  - finding_id: WF-OPEN-INITIAL-STATUS1-R2-003
    accepted: true
    accepted_marked_by: ""
    accepted_marking_binding: not-applicable
    accepted_reason: ""
    status: open
    blocking: false
    finding_class: environment
    attribution: external
    root_cause_id: disclosed-gaps-acknowledged
    counting_eligible: false
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5379067264 · 2026-08-22T07:42:53Z

<!-- wf-review-event:v1 card_id=WF-OPEN-INITIAL-STATUS1 source_sha=1c2700d729aa4adf4ccbd43885a1450d93af16ff attempt_id=WF-OPEN-INITIAL-STATUS1-e0-1c2700d729aa4adf4ccbd43885a1450d93af16ff -->
## 查核裁決：APPROVE

- 卡：`WF-OPEN-INITIAL-STATUS1`　attempt_id：`WF-OPEN-INITIAL-STATUS1-e0-1c2700d729aa4adf4ccbd43885a1450d93af16ff`
- 查核者：GPT-5@Codex（需求方轉貼；無 GitHub 收據留言，PM 逐字轉錄）　escalation_epoch：0
- source_sha：`1c2700d729aa4adf4ccbd43885a1450d93af16ff`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-22T15:42:52+08:00

### self_run（查核者實跑）

- `核對 rebase 與祖先關係`
  - origin/main 為 HEAD 祖先；從 2dcab60 至交付 SHA 為 0 個 merge commit
- `git ls-remote --tags origin 核對兩個保存 tag`
  - R1 tag 指 6e2e170、R2 tag 指 1be6bc9，均指向指定提交
- `寫入狀態值的變異後跑全套`
  - 1 failed, 1083 passed，唯一失敗即新守衛的 written_status not in line；pytest 外掛已確認載入的是變異模組
- `用真實產生器輸出餵 doctor`
  - 輸出確實含狀態，但 doctor 仍回 undecidable 與 handoff_status_not_in_log；舊 doctor 測試在同變異下仍綠，撤除原假保證正確
- `另兩個方向的變異`
  - next-stage 變異紅在 stage not in line；前綴變異紅在 startswith
- `核對實質語意`
  - 開卡初始值改為 💡需求 與 canonical 的狀態序、Backlog 前置閘門及需求方裁定一致；handoff --next-stage backlog 的受檢查路徑仍存在
- `回歸與 CI`
  - 本機 cli 全套通過；指定 CI run 32559354838 亦為 1084 passed
- `還原與對帳`
  - 原 worktree 保持 HEAD 1c2700d729aa4adf4ccbd43885a1450d93af16ff、乾淨；七個受查檔案 SHA-256 前後一致；contract_tool_reconcile --check 通過，58 個缺口皆有處置

### findings（0，其中 blocking 0）

- （無）

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-OPEN-INITIAL-STATUS1-e0-1c2700d729aa4adf4ccbd43885a1450d93af16ff
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 跨家族查核（待指派）
findings: []
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。
