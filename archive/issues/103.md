# #103 WF-STATUS-VOCAB-GATE1 寫入面閘門：preflight 零寫入、assign --status 收斂、iteration fail-loud
- state: closed  created: 2026-08-18T12:18:54Z  closed: 2026-08-18T12:54:30Z
- url: https://github.com/ruan6047/ai-workflow/issues/103
- comments: 1

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code PM
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；碼量小（約 13–20 行），難點是設計出「證明閘門會擋」的實測——現行 fake_gh 的 _ensure_project 以空 fields 起始，ensure_fields 必然用當下 FIELD_SPECS 建欄，preflight 那條分支構造上走不到。#99 已示範經濟型會交出 1015 passed 而 preflight 零觸發。）　查核：待指派（建議 高階型；驗收全押在「preflight 真的會擋」與「拒絕時零寫入」兩句話上，而那是本 repo 反覆失分的形狀。⚠️ 契約字面（MODEL_ROUTING 三個升級條件皆未觸發）指向主力型，但 4 張同形狀先例（#91 #89 #90 #95，全 T3、全 wfcli 寫入路徑）皆選高階型；拆卡把難度不對稱切開後先例的論據只落在本卡，需求方 2026-08-18 裁定取先例。跨家族依慣例非依規定（AI_WORKFLOW.md:28,185 是選言，main 有 d232fae 專門修過同型誤讀）。）
- Initiative：—　spec 基線：ae8f74162797e2eed7180a1cd1ed6692fab3b6d3
- DB：db_scope=none
- 服務的原始目標：狀態面寫入要嘛完整落地、要嘛完全不動

## 簡介
<!-- card-brief:begin -->
原要修狀態面寫入不是原子的（assign 與 handoff 依序寫欄位，交付狀態那格拋 ProjectError 就留下 owner 已換、狀態沒換、Log 零行的殘留，而操作者只看到一句拒絕訊息）、assign --status 自由文字可繞過 escalation 與 merge 前提、iteration 遞增與現況狀態無關三個口；2026-08-18 撤卡，因五輪規劃期研究證偽問題陳述——options 完全正確時的 502 留下逐格相同的殘留，故 preflight 治的不是原子性。**適用時機**：要查「為何不加 preflight、該問題重開成什麼形狀」的依據，或要看拆成 A／C 兩張的來源時。⛔ 非射程：狀態詞彙對齊那半由 WF-STATUS-VOCAB-ALIGN1 交付；不改 assign_cmd.py 無條件覆寫 ↩退回 的行為，射程另計。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：唯一寫入通道對狀態面的寫入不是原子的，而失敗時的殘留看起來像一次乾淨的拒絕。assign 依序寫 owner → 分支worktree → 交付狀態 → Log（assign_cmd.py:253-264）；handoff 依序寫 owner → 交付狀態 → 最後交接 → iteration → Log（handoff_cmd.py:395-404）。交付狀態那一格若值不在該欄 options 內，project.py:231-235 拋 ProjectError、cli.py:50-52 印一行 return 2——先前寫下去的欄位不回滾，Log 一行都不寫。看板進入「owner 換人了、狀態沒換、沒有任何留痕說發生過什麼」的組合，而操作者看到的是一句拒絕訊息。第二個口：assign --status 自由文字、無 choices，射程等於線上欄位當下全部選項，含 🚨已升級 與 📦已合併——契約規定的 escalation checkpoint 與 merge 收尾前提機械上可繞過。第三個口：iteration 的遞增判準是 --next-stage（handoff_cmd.py:373）而與現況狀態無關，於是「狀態校正」這類非交付的 handoff 也會 +1，2026-08-13 那批校正必須逐張用 --iteration 手動釘住（實測 54 次）。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/assign_cmd.py",
    "file:cli/src/wf_cli/commands/handoff_cmd.py",
    "file:cli/tests/test_commands_mocked.py",
    "file:cli/tests/fake_gh.py",
    "file:cli/tests/test_contract_tool_reconcile.py",
    "file:scripts/contract_tool_reconcile.py",
    "file:docs/CONTRACT_TOOL_RECONCILE.md",
    "file:AI_WORKFLOW.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 1)【preflight 零寫入】在「該欄 options 不含目標值」的世界裡，handoff 與 assign 皆非 0 退出，且該次呼叫對 Project／Issue 的寫入次數為 0。⚠️ 判定不看 rc，看呼叫序列：斷言 fake runner 收到的引數中沒有任何 project item-edit --field-id、updateProjectV2ItemFieldValue、issue edit --body、issue comment。只看 rc 分不出「拒絕前零寫入」與「寫了一半才拒絕」，而後者正是現況。2)【preflight 變異檢驗】把判斷條件改成恆真或整段移除後上一條由綠轉紅，紅綠兩態各附實跑輸出。3)⭐【preflight 的射程逐字寫明】交付物須逐字載明什麼結果會推翻它。已知恆綠情形三個：assign --status 收斂後打錯字由 argparse 先擋；Project #4 的兩個新值已於 2026-08-18 存在故該分支恆綠；全新板 ensure_fields 用全套 FIELD_SPECS 建欄亦恆綠。因此 preflight 唯一非空洞的入口是 handoff --status，加上「板早於新值被建起且之後沒人補」這個狀態。不寫清楚就是空洞檢查。4)【拒絕時印指令】preflight 拒絕的 stderr 含可直接複製執行的 gh api graphql 補選項指令，帶齊既有每個 option 的 id／name／color／description（後兩者 NON_NULL，漏帶會抹平既有顏色）。5)【assign choices】choices＝FIELD_SPECS 扣掉 🚧進行中／⏳待執行；⚠️ 必須同時確認 default 已是 🔨執行中（argparse 不驗 default 是否在 choices 內，只改一邊會變成「不打旗標照樣寫廢止值、打了反而被拒」）；給表列外的值時由 argparse 在任何遠端呼叫之前拒絕（exit 2、stderr 含 invalid choice、fake runner 呼叫序列長度 0）。6)【fail-loud】--next-stage implementation 且 from-state ≠ ↩退回 時 rc≠0、零寫入、訊息指出要帶 --iteration；from-state = ↩退回 時照常 +1。7)⭐【fail-loud 的摩擦上限】交付物須量出 fail-loud 會擋下既有流程的比例。基準：歷史 104 筆自動遞增中 from-state ≠ ↩退回 者為 28 筆（27%）。⚠️ 若實測 >20% 回頭重議本項裁定——一條每四次擋你一次的閘門，人會學會每次都帶 --iteration，而那是自由數字零檢查，比現況更糟。8)【逃生口不收斂】handoff --status 無 choices；wfcli handoff --help 與 AI_WORKFLOW.md 各有一句逐字說明它是有 --evidence 必填留痕的逃生口。9)【對帳器偵測判準】修正後 ungated_status_flags 同時列出 assign_cmd.py --status 與 handoff_cmd.py --status（現行判準要求 default 是狀態字面故漏報後者，使 docs/CONTRACT_TOOL_RECONCILE.md:328 的「唯一」成為錯誤陳述）；附變異檢驗：把判準改回原樣則該測試轉紅。10)【逐鍵 diff ＋ §7 重生】附 base 與 head 的 --format json 逐鍵 diff（含 verdict 未變但證據集合變動的列）；§7 以 --format md 整份重生、與工具輸出逐列一致。

## 驗證

- [ ] cd cli && uv run pytest -q。⚠️ 全綠不足以證明 preflight 有效：fake_gh.py:49-53 的 _ensure_project 以 fields 空字典起始，ensure_fields 必然用當下 FIELD_SPECS 建欄，測試世界裡「欄位 options」恆等於「碼側集合」——preflight 分支構造上走不到。實證：#99 的 head 1015 passed 全綠而一行 preflight 都沒有。正解：fixture 先把該欄建成不含新值的選項集；⚠️ 這不難——fake_gh.py:55-66 的 add_builtin_status 已是同型 helper，且 ensure_fields 對既有欄位 continue，一行 seeding 即可；真正的工作量是「現存 0 個測試碰 assign --status」，要從零補覆蓋。另須附現況重現：可重跑腳本證明改動前的 handoff --status 非選項值會留下 owner 已改、交付狀態未動、Log 零行的殘留。⚠️ 本卡不改 assign 覆寫 ↩退回 這個行為——它是 fail-loud 之所以必要的根因（assign_cmd.py:255 無條件寫，實測至少 4 次蓋掉 ↩退回），但修它要重設計 assign 的狀態語意，射程另計；本卡只讓不可靠變得可見，不宣稱修好了訊號，此限度須逐字寫進交付物。
## Log

- 2026-08-18T20:18:52+08:00 open by Claude Opus 5@Claude Code PM；owner 待指派；iteration 0。
- 2026-08-18T20:54:17+08:00 handoff by wf-cli → owner —（已停止）；iteration 0；SHA ae8f74162797e2eed7180a1cd1ed6692fab3b6d3；證據 撤卡（2026-08-18）：開卡後五輪規劃期研究推翻本卡的問題陳述，逐條理由見 issuecomment-5328438618。決定性的一條是服務的原始目標被實驗證偽——options 完全正確時的 502 留下與「值不在選項」逐格相同的殘留，故 preflight 治的不是原子性；而該欄 wfcli amend 改不動，只能撤卡重開。另有五處：驗收 5 沒關它引用的痛點、驗收 5 與 9 互相抵銷（實測落地後 ungated_status_flags 變空清單）、驗收 7 的基準 27% 已超過它自己 20% 的重議門檻、全卡行號對在 f207d2e 而非宣告基線 ae8f741 且 §7 章節不存在、資源宣告漏 project.py 而 WF-REVIEW-RECEIPT-WRITEBACK1 已宣告該檔。重開形狀（切 A/C 兩張、合併須排序）見同一則留言。。
- 2026-08-26T22:25:11+08:00 amend by wf-cli（op 1fb796a8）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:827decb13593d1b54a1bc97a31139bacd42f80f08485a9dc4e7e2d536ffaef67 (796 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5328438618 · 2026-08-18T12:53:46Z

## 撤卡：五輪規劃期研究推翻了本卡的問題陳述（2026-08-18）

本卡於 2026-08-18 20:18 開立，開卡後跑了五輪對抗式研究。結論是**本卡不能以 amend 修好，必須撤回重開**——因為被推翻的是「服務的原始目標」那一欄，而該欄 `wfcli amend` 改不動。

### 一、決定性的：服務目標被實驗推翻

本卡的服務目標是「讓寫入面的拒絕是原子的」。研究以真實碼實跑：把 Project 欄位的 options 設成**完全正確**、只讓寫入序列的第 2 格回 502——**殘留與「值不在選項」那個場景逐格相同**。

也就是說 preflight 治的不是原子性，是「值不在選項」這一個特定原因。而 502／rate limit 每天都有機會發生，詞彙漂移在本 repo 只發生過一次。

更關鍵：**有一個兩行的替代方案**——把 SINGLE_SELECT 排到寫入序列第一位，零殘留、零新碼。preflight 相對於它的唯一增量是「印出補選項的指令」。本卡從未這樣論證過自己。

⚠️ 而本卡第 3 項自承 preflight 在線上 Project #4 上**構造上走不到**（板上 15 個選項與 `FIELD_SPECS` 完全相同，該分支恆綠）。

### 二、驗收條之間互相抵銷（實測）

- **第 5 項沒關它自己引用的痛點**：扣掉兩個廢止值後 `choices` 剩 13 個，`🚨已升級` 與 `📦已合併` **兩個都還在**。核心痛點講的「escalation checkpoint 與 merge 收尾前提機械上可繞過」，第 5 項根本沒關。
- **第 5 與第 9 互相拆台**：`ungated_status_flags` 的判準是 `if "choices" in kwargs: continue`。模擬第 5 項落地後重跑對帳器，該清單由 `['assign_cmd.py --status…']` 變成 `[]`。若第 9 項沒同時落地，報告會從「1 個逃生口」變成「**0 個**」——比現況更糟。
- **第 7 項預先判自己失敗**：它寫「自動遞增佔比 >20% 即重議」，而基準是 28/104 = **27%**，寫下的當下就已觸發。

### 三、fail-loud 的形狀也錯

104/28/26.9% 獨立重現，數字對。但分類改變結論：28 筆裡 **18 筆**的正解是「補一個缺的動詞」（降級 Backlog／撤回派審／解除阻塞，本來就沒有對應動詞）、**7 筆**是「補一個缺的 review 事件」（6 筆早於 `wfcli review` 上線）、**只有 3 筆**真的該由操作者聲明。

而逃生口**早就是常態路徑**：`handoff` Log 共 467 行，證據欄自陳 `--iteration` 者 48 筆（10.3%），**2026-08-13 單日 43.1%**，措辭複製貼上 30 幾次。在沒有 fail-loud 的今天就已經長出反射了——再加一道逼它的閘門只會擴散。

門檻本身也不穩：08-11 是 4.2%、08-12 是 14.7%、08-13 之後 42.1%。**取哪一段窗會讓 20% 門檻翻面。**

### 四、引用整批對錯基線

本卡宣告基線 `ae8f741`，但**所有行號都對在 `f207d2e`**（前一個 commit）：

| 卡面引用 | `f207d2e` | `ae8f741`（宣告基線） |
|---|---|---|
| `handoff_cmd.py:373` | 373 ✅ | 376 ❌ |
| `handoff_cmd.py:395-404` | 395 ✅ | 398 ❌ |
| `docs/CONTRACT_TOOL_RECONCILE.md:328` | 328 ✅ | 322 ❌ |

時序吻合：`ae8f741` 合併於 20:06:58，本卡開立於 20:18:54——卡在 `f207d2e` 上寫完，基線欄改成 `ae8f741` 但引用沒重新解析。這不是三個錯字，是一個系統性形狀。

另外兩處：**`docs/CONTRACT_TOOL_RECONCILE.md` 全檔沒有「唯一」二字**（第 9 項的舉證句照字面查核者會找不到東西；實質「漏報 handoff」仍成立，但要重寫成「單元素清單以列舉暗示唯一」）；**`§7` 這個章節不存在**（該文件標題只到 `## 6`），而第 10 項要求「§7 整份重生」。

### 五、資源宣告漏一檔（fail-open）

本卡宣告 8 個檔案，**沒有 `file:cli/src/wf_cli/project.py`**。但前身卡 `WF-STATUS-VOCAB-ALIGN1`（PR #102）有宣告且實際改了它；而 Backlog 的 `WF-REVIEW-RECEIPT-WRITEBACK1` 已宣告該檔——**兩張同時派工不會被擋**。

且實測：第 5 項若把狀態字面寫在 `assign_cmd.py` 內（最自然的寫法），對帳器 `--check` 會**由綠轉紅**（5 個狀態被誤判成「有 writer」，缺口 51→46）。`choices` 必須由 `project.FIELD_SPECS` 導出。PR #102 實際落在 10 個檔，`test_doctor.py`／`test_registry.py`／`templates/` 都在內，本卡也都沒宣告。

### 重開時的形狀

切兩張：

- **【A｜preflight ＋ 詞彙閘門】**（原第 1–8 項）：`assign_cmd.py`、`handoff_cmd.py`、`project.py`、`fake_gh.py`、`test_commands_mocked.py`、`AI_WORKFLOW.md`。⚠️ 服務目標要重寫——preflight 不是原子性，且必須先論證它相對於「SINGLE_SELECT 排第一」的增量。fail-loud 的觸發集合要改成「語意上不可能是重做輪」的封閉態（擋 7.7%），逃生口不得是 `--iteration <自由整數>`，要各自帶語意的具名旗標。
- **【C｜對帳器判準 ＋ 文件重生】**（原第 9–10 項）：`scripts/contract_tool_reconcile.py`、`test_contract_tool_reconcile.py`、`docs/CONTRACT_TOOL_RECONCILE.md`。與 A 檔案完全不相交可並行，且切出去後對 8 張 Backlog 卡零封鎖。⚠️ 合併順序必須是 A → C（或 C 先合、A 合併時重跑重生），這條內容依賴 `find_conflicts` 看不見。

⚠️ 判準不能用「有沒有 `choices`」：實測「無 choices 即 ungated」會命中 92 個長旗標中的 **81 個**（`--reason`、`--evidence`、`--assignee`…），過報 40 倍。真正寫得進 `交付狀態` 的只有 2 個。判準要改成「這個旗標能寫的集合裡還有沒有屬於別的動詞的狀態」。

### 排序

`OPS-MIG1-CLAIMS-BACKFILL1`（#31）應排在重開的兩張之前，已於本日派出。理由：#31 的漏是**現在進行式**（21 張活卡整組跳過互斥檢查，每次 assign 印一行固定名單），而本卡的 preflight 構造上走不到。兩者資源零交集。

### 我沒驗到的

- 第 1 項是否真能在 13–20 行內完成、`fake_gh` 種子欄位那條測試路徑是否真的可寫——未實作驗證。
- 第 6 項 fail-loud 的行為正確性、第 4 項那串補選項指令是否帶齊 NON_NULL 欄位——未做。
- §2c 的兩個 CI 紅綠變體是在 `git archive` 展開樹上的模擬，不是提案實作。

