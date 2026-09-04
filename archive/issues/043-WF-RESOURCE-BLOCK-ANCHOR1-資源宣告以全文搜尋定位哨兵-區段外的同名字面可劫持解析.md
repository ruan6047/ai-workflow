# #43 WF-RESOURCE-BLOCK-ANCHOR1 資源宣告以全文搜尋定位哨兵，區段外的同名字面可劫持解析
- state: closed  created: 2026-08-12T03:42:34Z  closed: 2026-08-12T16:16:43Z
- url: https://github.com/ruan6047/ai-workflow/issues/43
- comments: 4

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；改動雖小但踩在 assign 的寫入集閘門上，須先釐清區段定位的 fail-closed 邊界並確認不破壞三個讀者檔的既有測試；推理鏈中等。）　查核：待指派（建議 主力型；本卡修的是治理閘門的 fail-open，查核重點在新定位法是否引入新的靜默放行、以及 fail-closed 是否真的關得住；建議跨家族但不強制。）
- Initiative：—　spec 基線：需求方 2026-08-12 提問「是否有辦法避免掃描到 LOG 導致誤判，尤其是將它寫到驗收或任務需求可能會造成遞迴也會失去可靠性」。PM 實測後確認問題比提問更嚴重（不是誤判是劫持），據此開卡。
- DB：db_scope=none
- 服務的原始目標：讓卡片能寫下自己的格式規範而不打壞讀它的解析器

## 簡介
<!-- card-brief:begin -->
把 resources.parse_block 的資源宣告區塊定位，從全文搜尋第一個哨兵改成兩層（先以標題結構切區段、再在區段內找哨兵，沿用 card.py:352 split_at_log 的 fail-closed 紀律），關掉「卡面把哨兵當示範寫進驗收條件就能劫持解析結果」這個靜默 fail-open——被劫持的結果會直接餵給 find_conflicts 與 assign 的寫入集閘門。**適用時機**：想在卡上寫下自己的格式規範又怕打壞解析器；或要查 Log 歷史回音、標題缺失、多個同名區段這類定位失效該拒還是該取時。⛔ 非射程：doctor 事件前綴全文子字串掃描的同族病由 WF-MARKER-SCOPE-CLEARANCE1（aiwf#30）承接；不得改 cli/tests/test_amend.py、test_card.py、test_validation.py。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：resources.parse_block 以 _BLOCK_RE.search(body) 全文搜尋取第一個命中來定位資源宣告區塊。任何出現在真區塊之前的同名哨兵字面都會贏——包括把哨兵寫進驗收條件當示範。PM 已實測：構造一份把哨兵示範寫在驗收條件、真區塊在後的 body，parse_block 回傳的是誘餌的內容（db_scope=write、resources=[file:DECOY.py]）而非真宣告，且無任何錯誤訊息。那份結果直接餵給 find_conflicts 與 assign 的寫入集閘門，故這是治理閘門的靜默 fail-open。真正的代價是它逼人把規則留在腦子裡——今天無法在卡上寫下自己的格式規範，因為寫下去就會打壞解析器。同一種病在 doctor 的事件前綴全文子字串掃描上也有一個實例（後果是整張卡的自動裁決被永久隔離），那個由 WF-MARKER-SCOPE-CLEARANCE1（#30）承接；本卡只治 resources 這一個。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/resources.py",
    "file:cli/tests/test_resources.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 把定位改為兩層：先以標題結構切到資源宣告所在的區段，再在該區段內尋找哨兵。碼裡已有正確形狀可循——card.py:352 的 split_at_log 具備三個性質：以獨立標題行定位而非字串出現、排版損壞即拒絕、多個同名標題即拒絕。請沿用同一組 fail-closed 紀律，不要各寫一套。
- [ ] PM 的誘餌案例須釘成回歸測試：驗收條件區段內含完整哨兵示範、真區塊在其後，斷言解析結果為真宣告而非誘餌。該測試須先對修改前的碼跑紅。
- [ ] 窮舉並裁定其餘定位失效情境，逐一給出處置：Log 區段內的歷史回音（amend 會把舊值原樣寫進 Log，含哨兵字面）；區段標題本身缺失；同一份 body 出現多個資源宣告區段；區段存在但哨兵在區段外。每一種都須明確是「拒絕」還是「取某一個」，且拒絕優先——讀不出宣告時 assign 必須擋，不得靜默當成無資源（既有 docstring 已如此宣告，不得因本次改動而弱化）。
- [ ] 不得改動 cli/tests/test_amend.py、cli/tests/test_card.py、cli/tests/test_validation.py——三者都 import 或間接依賴 parse_block，但分別由 WF-CARD-FIELD-CORRECTION1（#37，test_amend.py）與 WF-22-CLI4（#9，test_validation.py）持有，test_card.py 無人持有但仍逸出本卡宣告。若你的改動使其中任一轉紅，停下回報，說明是哪個測試、為什麼、以及該由誰承接——不得自行修改，也不得為了讓它們綠而弱化新定位法。
- [ ] 交付物須通過 WF-24-EVIDENCE-STRENGTH1 的 (e)：凡寫下「擋下／拒絕／不可能」等字眼，須指出執行者所在的檔與行與作用域邊界；沒有機械執行者的寫成約定。特別是「區段定位使誘餌無效」這句——請指出它對哪些形態有效、哪些無效。

## 驗證

- [ ] pytest 不得退化（基線以 git merge-base origin/main HEAD 那個 commit 實測為準，自己跑出來，不要抄本卡面數字）。ruff 只修自己引入的。
- [ ] 誘餌案例與每一種失效情境各附紅→綠證據：突變前 baseline 須為綠，否則 KILLED 判定無效。
- [ ] 以真實 repo 的全部 open issue body 實跑改前改後的 parse_block，證明沒有任何一張現有卡的解析結果改變。輸出由指令產生，列出每張卡的改前改後值。
- [ ] 證明本卡未使 assign 的寫入集閘門新增任何靜默放行路徑：列出 parse_block 的全部退出點，逐一標明是拋錯還是回值。
## Log

- 2026-08-12T11:42:33+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-12T11:43:14+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code 子agent；分支worktree claude/WF-RESOURCE-BLOCK-ANCHOR1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-resource-block-anchor1；交付狀態 🚧進行中；實際能力層級 主力型（與卡面建議 主力型 相符）。
- 2026-08-12T12:50:24+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA bf777d434288a48aa8120bc2601869a75d753075；證據 R1：df4e594 把 parse_block 的定位由全文搜尋取第一個命中改為兩層（先以標題結構切到資源宣告區段、再在區段內找哨兵），沿用 card.split_at_log 的 fail-closed 紀律；bf777d4 修正一處行號引用。

問題形態：任何出現在真區塊之前的同名哨兵字面都會贏，包括把哨兵寫進驗收條件當示範。PM 實測改前回傳誘餌的 db_scope=write 與 file:DECOY.py 且無任何錯誤訊息，而該結果直接餵給 find_conflicts 與 assign 的寫入集閘門——治理閘門的靜默 fail-open。真正的代價是它逼人把規則留在腦子裡：改前無法在卡上寫下自己的格式規範，因為寫下去就會打壞讀它的解析器。

四種失效情境逐一裁定（新測試 10 條，對改動前的碼 9 紅 1 綠，唯一綠的是防退化守衛非突變殺手）：Log 內歷史回音且真區段仍在→取真宣告（結構性排除，不拒絕）；只剩 Log 回音無真區段→拒絕（改前靜默回傳回音）；區段標題缺失→拒絕（改前靜默解析）；多個宣告區段→拒絕、不取第一個（改前靜默取第一個）；哨兵在區段外→拒絕（改前靜默解析區段外那組）。PM 已以自己構造的四個案例獨立打過，全部符合裁定表。

全 open issue 改前改後對照由指令產生：14 張全部 SAME，改變 0 張。相容性不是巧合——結構稽核顯示 14 張每張都恰有 1 個獨立資源宣告標題行、1 個獨立 Log 標題行、區段內恰好 1 組哨兵，而 #9/#16/#25/#37/#39 的多餘哨兵字面（#25 多達 2 組）全部落在 Log 尾段，正是被新定位法排除的那一類。

parse_block 退出點以 AST 機械列舉：本體 6 個 raise ＋ 1 個 return，唯一回值路徑仍會經 __post_init__ 再驗；本次新增的路徑全是 raise，零新增回值路徑，故 assign 的寫入集閘門沒有新的靜默放行。try_parse_block 維持 None 降級且有測試釘住它降級成 None 而非降級成誘餌的值。

作用域邊界（執行者自陳，PM 認為是本卡最誠實的一句）：保護只在 parse_block 這一條讀路徑內。任何不經它的讀取——例如 PM 今天用的 awk／grep 掃 begin/end——完全不受保護，照樣會被 Log 回音騙；PM 今天正是在那上面栽了兩次，已據此改變自己的工具習慣。另指出誘餌若貼進資源宣告區段內部時區段定位救不了，擋它的是哨兵數量唯一性檢查，若哪天放寬那個檢查同一劫持形態會原封不動往內縮一層復活。

bf777d4 修的是執行者自己預告過的風險在數小時內實現：docstring 引用 card.py:352 = split_at_log，而 #37 併入 20f2ea3 後 split_at_log 已移至 476 行、:352 指向一句無關註解。已改為錨定函式名（與 WF-DISPATCH-PRECHECK1 同日對同型問題的處置一致），並掃過寫入集兩檔的全部跨檔引用逐一列出處置。⚠️ 執行者同時糾正 PM 一個機制上的錯誤：PM 要求「重算基線、不要沿用 3e47838」暗示該值會變，但 merge-base 是分叉點不是當下的 main，不 merge 不 rebase 時 main 前進不會移動分叉點，重算結果仍為 3e47838；PM 可能想問的是落後量 rev-list --count HEAD..origin/main = 5。PM 已複驗執行者為對。

執行者另做一項未被要求的獨立驗證：PM 說 #37 與其寫入集零相交，它認為檔名不相交不等於語意不衝突（其 _split_at_log 刻意鏡射 card.split_at_log 而 #37 正好大改 card.py），故另開臨時 detached worktree 試合併 origin/main——無衝突、562 passed、雙方新測試同時全綠，用完已移除。

驗證：pytest 437(基線 3e47838) → 447；受保護三檔 test_amend.py／test_card.py／test_validation.py diff 為 0 行、三檔單獨跑 205 passed；寫入集兩檔零逸出；marker 字面 0 處。執行者自陳新增一項無執行者宣稱：「引用一律錨定函式名不寫行號」是 docstring 內的約定，沒有 lint 或測試擋下未來有人再寫行號；要有執行者得是一條掃 .py:數字 的 lint，超出本卡寫入集。。
- 2026-08-12T13:20:40+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5262616305 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=adfb830d… 一次相符。本輪四份裁決皆無需 PM 作任何格式調整——區塊零散文、序列已縮排、無 code fence）；core_pain_resolved yes；self_run 6 項；findings 0 項（blocking 0）；attempt WF-RESOURCE-BLOCK-ANCHOR1-e0-bf777d434288a48aa8120bc2601869a75d753075。
- 2026-08-12T13:22:41+08:00 handoff by wf-cli → owner —（結案）；iteration 0；SHA bf777d434288a48aa8120bc2601869a75d753075；證據 跨家族查核（GPT-5@Codex 子代理）於 bf777d4 判 APPROVE、core_pain_resolved=yes、findings 0、self_run 6 項。收據 issuecomment-5262616305 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=adfb830d… 一次相符。

查核者以自建的六種輸入獨立打過 parse_block（驗收條件誘餌在前、僅 Log 回音、缺標題、兩個標題、區段外哨兵、區段內重複哨兵），第一種回真宣告、其餘五種全部拋 ResourceDeclarationError；並自行以 Python AST 列舉退出點（6 raise／1 return）、盤點全 repo 讀取路徑確認未發現另一個全文哨兵解析器。它另指出一件 PM 與執行者都未涵蓋的事實：對照除變更當時的 14 張外，加上提交後新建的 #45 共 15 張也全數 SAME。

以 PR #46 併入 main。刻意不 rebase（git merge-tree 實測無衝突），已於併後驗證 git merge-base --is-ancestor bf777d4 origin/main 成立。

本卡的實質貢獻是把讀取端拉回與寫入端一直在用的同一套定位——amend_resource_block 早就走 split_at_log() → _locate_section()，只有 parse_block 是全文搜尋；缺陷的本質是寫入端與讀取端不對稱，而非解析器不夠嚴。該角度由 PM 於第二輪跨卡對帳查出並補進派審詞（issuecomment-5262542203），執行者的原交付報告未涵蓋。

誠實劃界（查核者確認正確）：保護只在 parse_block 這一條讀路徑內，不經它的讀取如 awk／grep 完全不受保護；誘餌若貼進區段內部則區段定位無效，擋它的是哨兵數量唯一性檢查，放寬該檢查會使同一劫持形態往內縮一層復活。執行者另自陳「引用一律錨定函式名不寫行號」這條新約定沒有機械執行者。

驗證：pytest 437(基線 3e47838)→447；受保護三檔 test_amend.py／test_card.py／test_validation.py diff 為 0 行、三檔單獨跑 205 passed；寫入集兩檔零逸出；marker 字面 0 處。。
- 2026-08-13T00:15:53+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code PM；iteration 0；SHA 0ea7abad670681b708f4fbbe15526008b448abe3；證據 ⚠️ 前向更正：把交付狀態自 🏁完成 倒退為 📦已合併，以還原至可清理的合法態。成因：本卡的終態早已寫入，但收尾第 1-3 步（移除 worktree、刪本地與遠端分支）一步都沒做，Issue 亦未關；cleanup.classify_state 因此判 illegal_terminal_before_cleanup（effect_started=terminal_status_written or not issue_open，此處觸發項為終態已寫），守衛拒絕動作並回「須人工判斷，守衛不代為修復」。本次不追溯改寫任何既有事件——Log 依序記下「終態寫入 → 本次更正倒退 → 清理 → 終態重寫」，那是準確的事件序。發現經過：2026-08-13 依 docs/ROADMAP.md §3 檢視排程時，PM 才發現自己把兩張【碼早已在 main】的卡排成序 1、2 並寫成「是後面三張的前提」——排程是憑印象寫的、沒有先查狀態。ROADMAP §3 須同步更正。。
- 2026-08-13T00:16:28+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code PM；iteration 0；SHA 0ea7abad670681b708f4fbbe15526008b448abe3；證據 收尾：碼早已在 main（分支 tip bf777d4 為 origin/main 祖先，PM 以 merge-base --is-ancestor 複驗）。前一筆事件已把交付狀態自 🏁完成 倒退為 📦已合併以還原至合法態，本次由守衛執行第 1-3 步後才寫終態——順序正確，不再是 illegal_terminal_before_cleanup。；收尾清理已完成（worktree 與本地／遠端分支皆已不存在）。
- 2026-08-26T22:19:43+08:00 amend by wf-cli（op d775c251）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:b74e1d79d05c937c42ba15029ac3cdccf93def4dbdebea6d03cea921a02fe995 (783 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5262454005 · 2026-08-12T04:55:53Z

## 派審：#43 `WF-RESOURCE-BLOCK-ANCHOR1` R1

⚠️ 審核對象 **`ruan6047/ai-workflow#43`**。

```
進駐位置：/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-resource-block-anchor1
分支：claude/WF-RESOURCE-BLOCK-ANCHOR1　　被審 SHA：bf777d434288a48aa8120bc2601869a75d753075
基線：3e47838c69e7de49bafe0fb515364e91536962e9（= merge-base origin/main bf777d4，已驗為祖先）
iteration：0（首輪）　　寫入集：cli/src/wf_cli/resources.py、cli/tests/test_resources.py
```

> **本則為權威。** `origin/main` 現為 `20f2ea3`，本分支落後它 5 個 commit——**但基線仍是 `3e47838`**：merge-base 是分叉點，不 merge 不 rebase 時 main 前進不會移動它。（PM 曾在派工詞裡把這兩個量混為一談，被執行者糾正。）

### 問題形態

`resources.parse_block` 以 `_BLOCK_RE.search(body)` **全文搜尋取第一個命中**定位資源宣告。任何出現在真區塊之前的同名哨兵字面都會贏——**包括把哨兵寫進驗收條件當示範**。PM 實測改前回傳誘餌的 `db_scope=write` 與 `file:DECOY.py` 且**無任何錯誤訊息**，而該結果直接餵給 `find_conflicts` 與 `assign` 的寫入集閘門：**治理閘門的靜默 fail-open**。

真正的代價：**改前無法在卡上寫下自己的格式規範，因為寫下去就會打壞讀它的解析器。**

### 一、修法是兩層定位，請攻擊它的邊界

先以標題結構切到資源宣告區段，再在區段內找哨兵，沿用 `card.split_at_log()` 的 fail-closed 紀律（以獨立標題行定位／排版損壞即拒絕／多個同名標題即拒絕）。

四種失效情境逐一裁定，**新測試 10 條對改動前的碼 9 紅 1 綠**（唯一綠的是防退化守衛非突變殺手）：

| 情境 | 裁定 | 改前行為 |
|---|---|---|
| Log 內歷史回音、真區段仍在 | 取真宣告 | 同 |
| 只剩 Log 回音、無真區段 | **拒絕** | 靜默回傳回音 |
| 區段標題缺失 | **拒絕** | 靜默解析 |
| 多個宣告區段 | **拒絕、不取第一個** | 靜默取第一個 |
| 哨兵在區段外 | **拒絕** | 靜默解析區段外那組 |

**PM 已以自己構造的四個案例獨立打過，全部符合裁定表。請自己再打一次。**

**執行者已明列它救不了的形態**：誘餌貼進**區段內部**時區段定位無效，擋它的是**哨兵數量唯一性檢查**——「若哪天有人放寬那個數量檢查，同一個劫持形態就會原封不動往內縮一層復活」。另有一個 fail-closed 方向的邊界：區段結尾以 `line.startswith("## ")` 判定，若有人在區段內寫出以 `## ` 開頭的行，區段會提早收邊 → 拒絕（方向安全但會擋下該卡）。

### 二、承重宣稱：全 open issue 零改變

執行者以指令產生 14 張的改前改後對照，**全部 `[SAME]`**。它並說明相容性不是巧合：結構稽核顯示 14 張每張都恰有 1 個獨立資源宣告標題行、1 個獨立 Log 標題行、區段內恰好 1 組哨兵，而 #9/#16/#25/#37/#39 的多餘哨兵字面（**#25 多達 2 組**）全部落在 Log 尾段。

**請自己重跑。**

### 三、退出點的機械列舉

`parse_block` 本體 **6 個 raise ＋ 1 個 return**（AST 列舉非人工清點），唯一回值路徑仍經 `__post_init__` 再驗；**本次新增的路徑全是 raise，零新增回值路徑**。`try_parse_block` 維持 `None` 降級，且有測試釘住它降級成 `None` 而非降級成誘餌的值。

**請判斷**：`try_parse_block` 的使用者（`snapshot`、`assign` 對別卡）會因解析更嚴格而更多落到「略過交集檢查」那條路——那條路**印警告、不擋派工**。執行者實測現況 14 張**零**落入，但明說「這是當下的事實，不是保證」。

### 四、作用域邊界（PM 認為是本卡最誠實的一句）

> 保護**只在 `parse_block` 這一條讀路徑內**。任何不經它的讀取——例如 PM 今天用的 `awk`／`grep` 掃 begin/end——完全不受保護，照樣會被 Log 回音騙。

PM 今天正是在那上面**栽了兩次**（誤判 #16 宣告了 `templates/`、#9 宣告了 `cli/`），已據此改變工具習慣。**請判斷這個劃界是否完整。**

### 五、一項執行者未被要求而做的驗證

PM 說 #37 與其寫入集零相交，它認為**檔名不相交不等於語意不衝突**（其 `_split_at_log` 刻意鏡射 `card.split_at_log`，而 #37 正好大改 `card.py`），故另開臨時 detached worktree 試合併 `origin/main`：**無衝突、562 passed**、雙方新測試同時全綠，用完已移除。

### 六、已知殘留

`bf777d4` 修的是執行者**自己預告過**的風險在數小時內實現：docstring 引用 `card.py:352 = split_at_log`，而 #37 併入後該函式已移至 476 行。已改為錨定函式名（與 #38 同日對同型問題的處置一致）。**執行者自陳這條新約定同樣沒有執行者**——沒有 lint 或測試擋下未來有人再寫行號。

驗證：pytest 437(基線)→447；**受保護三檔 `test_amend.py`／`test_card.py`／`test_validation.py` diff 為 0 行**、三檔單獨跑 205 passed；marker 字面 0 處。

### 環境紅線

唯讀查核；不得改動被審分支、不得 merge、不得改 Project 狀態、不得執行有副作用的 `wfcli`（`--validate-only` 與 `doctor` 唯讀可用；`gh issue view`／`gh api` 唯讀可用）。**不得 amend 任何已推送的 commit；禁無 lease 的 `--force`／`-f`。** 需要跑會改動 tracked file 的驗證時在**拋棄式**目錄做（`git archive <sha> | tar -x -C /tmp/...`）——不要在被審 worktree 內 `checkout`／`reset`／`stash`，多個 worktree 共用同一個 git repo。

**留言紀律**：`doctor` 以全文子字串掃事件 marker 前綴。任何留言只要出現 `wf-review-event` 後面直接接半形冒號的字面，**整張卡的自動裁決判定就被永久隔離**。拆開書寫，發文前 `grep` 確認 0 次。（`wf-review-receipt:v1` 是不同前綴，不受此限。）

### 輸出

依 `templates/review-prompt.md` §5。**三項強制，缺任一即 `review-invalid`：**

1. **逐項回報前輪 accepted blocking finding 的閉環狀態**（`resolved`／`withdrawn`／仍開啟）並附證據。
2. **五個 schema 欄位自己填**。`root_cause_id` 見門檻提醒——**沿用既有家族名，不要另起新名把門檻洗掉**。
3. **留收據**：`wf-review-receipt:v1` **多行格式**（`card_id:` 與 `source_sha:` **各自獨立成行**，單行 `key=value` 形式 `doctor` 認不得），報告全文同帖，取材規則寫死起訖／編碼／換行／是否 strip／排除範圍。**規則若提到起訖 delimiter 的字面，請說清楚是「本規則之後的下一個」。**

**YAML 限制**（自寫固定子集）：不支援折疊純量 `>`（用 `|`）、不支援裸字串序列（用 `- key: value`）、不支援頂層鍵＋巢狀 mapping（用序列）、值含 ` #` 須整個值加引號、**序列項須縮排 2 空格**、**區塊內不得混入散文或 code fence**。非 schema 的頂層鍵會被容忍。


## Comment 5262542203 · 2026-08-12T05:06:48Z

## 派審補充：#43 —— 寫入端與讀取端的定位鏈

補一節進[前一則派審詞](https://github.com/ruan6047/ai-workflow/issues/43#issuecomment-5262454005)，其餘一切不變。**這是 PM 於第二輪跨卡對帳時查到的，執行者的交付報告未涵蓋這個角度。**

### 缺陷的本質是不對稱，不只是「解析器不夠嚴」

PM 原本要查的是：本卡改了讀取端之後，**寫入端與讀取端是否用同一套定位**——那是 `WF-CLI-ROUTING-TIER1`（#21）與 `WF-CARD-FIELD-CORRECTION1`（#37）處理過的往返缺陷形狀（`open` 寫得出、`assign` 讀不回）。

實查結果：

| | 定位鏈 |
|---|---|
| **寫入端** `card.amend_resource_block()` | `split_at_log()` → `_locate_section(lines, _RESOURCE_HEADING)` ——**一直都是區段定位** |
| **讀取端** `resources.parse_block()`（改前） | `_BLOCK_RE.search(body)` ——**全文搜尋取第一個命中** |
| **讀取端**（`bf777d4` 改後） | `_split_at_log()` → `_declaration_section()` → 區段內找哨兵 |

**所以這個缺陷不是「解析器寫得不夠嚴」，是寫入端與讀取端對同一份 body 使用不同的定位語意。** 寫入端會把新宣告寫進 `## 資源宣告` 區段，而讀取端可能讀到區段外的另一組哨兵——兩支對同一張卡給出不一致的答案。

本卡的修法把讀取端拉回與寫入端同一套。

PM 另掃過 `cli/src/` 確認**沒有其他消費者自行掃哨兵**（唯一命中 `card.py:226` 是一則註解）。

### 這對你的查核有什麼用

它讓「這個修法對不對」多一個**可機械判定**的判準，而不只是「四種失效情境的裁定合不合理」：

**請驗證兩支現在是否真的等價。** 具體可攻擊的點：

1. **`resources._split_at_log()` 與 `card.split_at_log()` 是兩份實作，不是共用。** 執行者的理由寫在 docstring 裡：`card.py` 已 import 本模組的 `render_block`，**反向 import 會成環**，並自陳「語意對齊靠 `tests/test_resources.py` 的對照測試釘住，不是靠約定」。**請驗證那些對照測試真的釘得住**——兩份實作能不能構造出一份 body 使它們給出不同答案？（例如多個 `## Log` 標題、字面 `\n` 破壞排版、`## Log` 出現在字串內）
2. **`_declaration_section()` 的區段結尾以 `line.startswith("## ")` 判定，與 `card._locate_section` 同一套**——但 `_locate_section` 是**別人的檔**，`card.py` 目前在 `WF-CARD-FIELD-CORRECTION1` 交付後仍持續被改（該卡已於 `20f2ea3` 併入 main，`card.py` +156 行）。**跨檔語意一致性沒有機械執行者**，這是執行者自陳的殘留之一。請判斷該自陳是否足夠，還是需要更強的處置。
3. **寫入端不在本卡寫入集內。** 若你認為真正的修法應該是讓兩支共用同一個定位器（而非各寫一份靠測試對齊），那需要動 `card.py`——**該檔不在本卡宣告內**，請明列為衍生卡而非要求本卡代做。

### 不變的部分

前一則派審詞的六節攻擊點、環境紅線、留言紀律、輸出契約與收據格式**全部沿用**，本則只是追加第七個角度。

被審 SHA 仍為 `bf777d434288a48aa8120bc2601869a75d753075`，基線仍為 `3e47838c69e7de49bafe0fb515364e91536962e9`。

## Comment 5262616305 · 2026-08-12T05:15:14Z

<!-- wf-review-receipt:v1
card_id: WF-RESOURCE-BLOCK-ANCHOR1
source_sha: bf777d434288a48aa8120bc2601869a75d753075
report_sha256: adfb830da3695e2b072165c4f8a8f342b8408b4db69b125e7b550a9c58eaf129
-->
取材規則：從本規則之後的下一個 `--- report-begin ---` 的下一行第一個字元起，至本規則之後的下一個 `--- report-end ---` 前一行的 LF 為止；UTF-8、LF、strip=false；排除收據註解、取材規則及兩個 delimiter 行。
--- report-begin ---
core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: "git rev-parse HEAD; git status --porcelain; git merge-base --is-ancestor 3e47838c69e7de49bafe0fb515364e91536962e9 HEAD"
    observed: "HEAD=bf777d434288a48aa8120bc2601869a75d753075；工作區乾淨；基線祖先檢查 exit 0；origin/claude/WF-RESOURCE-BLOCK-ANCHOR1 包含此 SHA。"
  - command: "git diff --check 3e47838c69e7de49bafe0fb515364e91536962e9 bf777d434288a48aa8120bc2601869a75d753075; git diff --name-status 3e47838c69e7de49bafe0fb515364e91536962e9 bf777d434288a48aa8120bc2601869a75d753075"
    observed: "無 whitespace error；寫入集僅 cli/src/wf_cli/resources.py 與 cli/tests/test_resources.py。"
  - command: "git archive bf777d434288a48aa8120bc2601869a75d753075 | tar -x -C /tmp/wf43-review.fGlUAj; cd /tmp/wf43-review.fGlUAj/cli && PYTHONDONTWRITEBYTECODE=1 uv run pytest -q"
    observed: "447 passed；在拋棄式目錄執行。"
  - command: "以 parse_block 對六種情境自建輸入：驗收條件誘餌在前、僅 Log 回音、缺資源宣告標題、兩個資源宣告標題、區段外哨兵、區段內重複哨兵。"
    observed: "第一種回傳真宣告 file:r；其餘五種均拋 ResourceDeclarationError，未回傳誘餌。"
  - command: "對基線與被審版 resources.parse_block 比對目前全部 open Issue body；並結構檢查每張的獨立資源宣告標題、Log 標題與區段內 begin/end 哨兵。"
    observed: "變更提交時存在的 14 張 open Issue 改前改後均 SAME；目前另有提交後新建的 #45，現況共 15 張也均 SAME，且全數通過結構檢查與解析。"
  - command: "以 Python AST 列舉 parse_block 的 Raise 與 Return；以 rg 盤點 parse_block、try_parse_block 與哨兵字面使用點。"
    observed: "parse_block 為 6 個 raise、1 個 return；唯一程式讀取路徑為 assign 的嚴格 parse_block 與 snapshot／assign-other-card 的 try_parse_block，未發現另一個全文哨兵解析器。"
first_round_prior_findings:
  - status: "首輪，無前輪 accepted blocking finding。"
findings: []
scope_outside_findings:
  - topic: "手工文字掃描"
    observation: "awk、grep 等未經 parse_block 的手工掃描不受此修法保護；派審詞已正確劃定邊界，未構成被審寫入集內 finding。"
--- report-end ---


## Comment 5262679001 · 2026-08-12T05:20:41Z

<!-- wf-review-event:v1 card_id=WF-RESOURCE-BLOCK-ANCHOR1 source_sha=bf777d434288a48aa8120bc2601869a75d753075 attempt_id=WF-RESOURCE-BLOCK-ANCHOR1-e0-bf777d434288a48aa8120bc2601869a75d753075 -->
## 查核裁決：APPROVE

- 卡：`WF-RESOURCE-BLOCK-ANCHOR1`　attempt_id：`WF-RESOURCE-BLOCK-ANCHOR1-e0-bf777d434288a48aa8120bc2601869a75d753075`
- 查核者：GPT-5@Codex 子代理（需求方轉貼；收據 issuecomment-5262616305 多行格式合規、未經編輯，PM 依其取材規則回讀重算 report_sha256=adfb830d… 一次相符。本輪四份裁決皆無需 PM 作任何格式調整——區塊零散文、序列已縮排、無 code fence）　escalation_epoch：0
- source_sha：`bf777d434288a48aa8120bc2601869a75d753075`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-12T13:20:40+08:00

### self_run（查核者實跑）

- `git rev-parse HEAD; git status --porcelain; git merge-base --is-ancestor 3e47838c69e7de49bafe0fb515364e91536962e9 HEAD`
  - HEAD=bf777d434288a48aa8120bc2601869a75d753075；工作區乾淨；基線祖先檢查 exit 0；origin/claude/WF-RESOURCE-BLOCK-ANCHOR1 包含此 SHA。
- `git diff --check 3e47838c69e7de49bafe0fb515364e91536962e9 bf777d434288a48aa8120bc2601869a75d753075; git diff --name-status 3e47838c69e7de49bafe0fb515364e91536962e9 bf777d434288a48aa8120bc2601869a75d753075`
  - 無 whitespace error；寫入集僅 cli/src/wf_cli/resources.py 與 cli/tests/test_resources.py。
- `git archive bf777d434288a48aa8120bc2601869a75d753075 | tar -x -C /tmp/wf43-review.fGlUAj; cd /tmp/wf43-review.fGlUAj/cli && PYTHONDONTWRITEBYTECODE=1 uv run pytest -q`
  - 447 passed；在拋棄式目錄執行。
- `以 parse_block 對六種情境自建輸入：驗收條件誘餌在前、僅 Log 回音、缺資源宣告標題、兩個資源宣告標題、區段外哨兵、區段內重複哨兵。`
  - 第一種回傳真宣告 file:r；其餘五種均拋 ResourceDeclarationError，未回傳誘餌。
- `對基線與被審版 resources.parse_block 比對目前全部 open Issue body；並結構檢查每張的獨立資源宣告標題、Log 標題與區段內 begin/end 哨兵。`
  - 變更提交時存在的 14 張 open Issue 改前改後均 SAME；目前另有提交後新建的 #45，現況共 15 張也均 SAME，且全數通過結構檢查與解析。
- `以 Python AST 列舉 parse_block 的 Raise 與 Return；以 rg 盤點 parse_block、try_parse_block 與哨兵字面使用點。`
  - parse_block 為 6 個 raise、1 個 return；唯一程式讀取路徑為 assign 的嚴格 parse_block 與 snapshot／assign-other-card 的 try_parse_block，未發現另一個全文哨兵解析器。

### findings（0，其中 blocking 0）

- （無）

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 由 lifecycle writer 另行標記，不在本指令的寫入範圍。
