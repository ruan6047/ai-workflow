# #106 WF-CLEANUP-SUBMODULE-AWARE1 收尾守衛對含 submodule 的 repo 構造性失敗：空 gitlink 目錄即被 git 拒絕
- state: closed  created: 2026-08-18T21:47:11Z  closed: 2026-08-19T05:35:40Z
- url: https://github.com/ruan6047/ai-workflow/issues/106
- comments: 5

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；守衛碼帶破壞性相鄰操作（worktree remove），錯誤難察覺（fail-open 或誤刪都靜默）；MODEL_ROUTING 升級條款命中）　查核：待指派（建議 主力型；要驗的是否定式性質：修法不得引入 rm -rf 型繞道、不得弱化既有 fail-closed;須獨立構造非空 submodule 樣本攻擊）
- Initiative：—　spec 基線：ai-workflow ae8f74162797e2eed7180a1cd1ed6692fab3b6d3；實證＝cpbl#149 issuecomment-5331774491（三次中止＋人工收尾留痕）與 cpbl#139 同型留痕
- DB：db_scope=none
- 服務的原始目標：收尾守衛要能收掉含 submodule 的 repo 的尾，而不是把每張卡都推回它自己定義為說謊的人工路徑

## 簡介
<!-- card-brief:begin -->
讓 cleanup 收得掉含 submodule 的 repo 的尾，而不是把每張卡都推回它自己定義為說謊的人工路徑。執行者以逐格實測推翻卡面原本的機制解釋：空 gitlink 目錄其實移得掉，真 blocker 是 worktree gitdir 下 modules 存在即曾初始化；並反向量到一個卡面沒提的真洞——gitlink 目錄有檔案但 submodule 未初始化時 git 報乾淨、remove 會連同工作內容一起刪除。交付新前提 no_blocking_submodule：不做任何檔案系統寫入、非空即擋（比 git 嚴一格）、讀不到即 unobservable fail-closed。**適用時機**：cpbl 這類含 submodule 的 worktree 跑 cleanup 被擋、或要判斷會不會誤刪工作內容時。⛔ 非射程：不用 --force、不 rm -rf、不 deinit——非空 submodule 一律 fail-closed 並給人工路徑與留痕範本（範本即 cpbl#149）；對無 submodule 的 repo 行為逐字不變，cli/tests/test_cleanup.py 既有測試一行未改。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：cleanup 守衛的 git worktree remove 對任何 cpbl worktree 構造性失敗：git 自己的 validate_no_submodules 對「index 含 gitlink 且該路徑存在為目錄」一律拒絕——空目錄也算，而 worktree add 必建空 .ai-workflow 目錄（實測 13/13 cpbl worktree 皆有）；移除目錄後樹轉髒，守衛依設計不加 --force（cleanup.py:47-51 _forbid_force 掛在唯一 git 入口）。兩道門都關＝catch-22。2026-08-19 已兩次退回人工收尾（cpbl#149 三次中止留痕、cpbl#139），人工收尾正是 ROADMAP §3 判為「真正說謊」的形狀：終態寫入了、清理一步沒做。與 #78 同判準同族（收尾守衛恆拒→每張卡收不掉尾），對象從 squash 換成 cpbl——而 cpbl 才是有使用者的 repo。此缺陷使 ROADMAP §3.6「交回主線」判準由是翻否

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/cleanup.py",
    "file:cli/tests/test_cleanup.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] cleanup 對「index 含 gitlink 且該路徑為空目錄」的 worktree 能完成 remove：移除前安全處理空的 submodule 目錄（僅限空目錄——entries 為零；判空由碼實測不由名稱推斷）。推翻條件：對含未初始化 submodule 的真實 cpbl worktree 跑 cleanup 仍失敗，或實作用了 --force
- [ ] 非空 submodule 目錄（已初始化/有內容）維持 fail-closed：不得 rm -rf、不得 deinit、不得 --force，錯誤訊息須指名人工路徑並引用受據格式（cpbl#149 收尾留痕即範本）。推翻條件：構造一個含已初始化 submodule 的 worktree，cleanup 未拒絕或以任何形式刪了它
- [ ] 對無 submodule 的 repo 行為逐字不變。推翻條件：既有 test_cleanup.py 任一測試需要修改才能過（新增可以，改舊的即回歸破壞）

## 驗證

- [ ] cd cli && uv run pytest -q 全綠；新增測試至少三例：空 gitlink 目錄可清、非空 fail-closed、無 submodule 回歸
- [ ] 端到端：在 disposable 的真實 cpbl worktree 上（含空 .ai-workflow 目錄）實跑一次完整 cleanup 並貼原始輸出——不得只以 fake_gh/fixture 自證
## Log

- 2026-08-19T05:47:10+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-19T11:03:00+08:00 assign by wf-cli → owner Claude Fable 5@Claude Code 子agent；分支worktree claude/cleanup-submodule-aware-106 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/cleanup-submodule-106；交付狀態 🔨執行中；實際能力層級 高階型（偏離卡面建議 主力型；偏離理由：卡面建議主力型；向上偏離：繼承本會話子代理模型 Claude Fable 5（MODEL_ROUTING L3 等價）；為單張卡另起低階模型的協調成本高於能力差價，射程不因層級擴大。）；跨 repo 歸屬 ruan6047/ai-workflow（未明示，依預設取自卡自己的 repo；本閘門不觀測也不綁定後續的 git worktree add）；本機觀測 consistent（機器局部，沉默不代表無誤）。
- 2026-08-19T11:31:45+08:00 handoff by wf-cli → owner 待指派；iteration 0；SHA c81886865d8ead489124558cdccc163b9a2e7539；證據 執行交付（2026-08-19）：分支 claude/cleanup-submodule-aware-106，恰兩檔＝資源宣告（cleanup.py +197、test_cleanup.py +300，既有測試刪除 0 行），worktree 保留。⭐⭐ 最重要：執行者以逐格實測**推翻了卡面核心痛點的機制解釋**，PM 已獨立複驗兩格確認執行者正確、PM 原判斷錯誤（attribution: coordinator，更正見 issuecomment-5337160339）。(a) 空 gitlink 目錄實測 worktree remove rc=0 移得掉、不需 --force——卡面「空目錄也算、故對任何 cpbl worktree 構造性失敗」為過度推論；真正 blocker 是 <worktree gitdir>/modules 存在即曾初始化 submodule。cpbl#149 落在該格（其派工包第 2 步逐字要求 submodule update --init）故確實被擋；cpbl#139 我先 rmdir 再直接帶 --force，從未測過不帶 --force 是否本來就能過。(b) 執行者反向量到一個卡面沒提的真洞、PM 複驗確認：gitlink 目錄有檔案但 submodule 未初始化時，git status --porcelain --ignore-submodules=none 報空（git 自己看不見）、worktree remove rc=0 並**連同工作內容一起刪除**——這是靜默的工作內容遺失，正是本模組 canonical 指名要防的事，而 _check_uncommitted 結構上看不到。實作：新增前提 no_blocking_submodule，不做任何檔案系統寫入；非空即擋（比 git 嚴一格，方向保守）；已初始化/modules 殘留→fail 並給人工路徑與留痕範本；讀不到→unobservable（fail-closed）；空目錄測量後刻意不動。_execute_closeout 一行未改。驗證：pytest 1017 passed（基線 1009+8）、uv lock --check 過、escalation replay 65/65、trailer 守衛實測未沉睡（audit_commit_trailers 回 status=compliant）、五個變異逐一注入皆被指名測試接住並還原。⚠️ 查核第一題（執行者自己指出的施力點）：**驗收條 1「移除前安全處理空的 submodule 目錄」的文字與交付不同**——交付是「測量後刻意不動」，執行者實證移走空目錄會讓樹轉髒、改以另一理由被拒，故該處方在不用 --force 前提下無出口。PM 未修改驗收條（事後改驗收條配合交付即搬門柱），此偏離是否可接受請裁決。⚠️ 其他查核重點：(c) 「檢查比 git 嚴一格」是新擋點，方向保守但確為新增；(d) 執行者收尾 disposable worktree 時 submodule deinit 寫到共享 .git/config 一度弄壞主 checkout 的 submodule 註冊，已修復並自報，PM 複驗主 checkout 現況 f207d2e/20 entries/status 乾淨，但執行者自陳無法證明 submodule.active key 動手前是否存在；(e) git 版本只驗 2.50.1 一個；(f) 已初始化路徑的行為由拋 CleanupGuardError 改為 detect_only，呼叫端錯誤處理路徑不同、執行者只讀碼未實跑；(g) Implemented-by trailer 與卡面 owner 不逐字相同（執行者實為 Opus 5，已在 trailer 內註明），執行者主動揭露。。
- 2026-08-19T12:24:10+08:00 review by wf-cli → APPROVE（✅通過）；查核者 Google DeepMind Antigravity；core_pain_resolved yes；self_run 5 項；findings 0 項（blocking 0）；escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；attempt WF-CLEANUP-SUBMODULE-AWARE1-e0-c81886865d8ead489124558cdccc163b9a2e7539。
- 2026-08-19T13:35:29+08:00 handoff by wf-cli → owner —（已合併）；iteration 0；SHA 800562f6d7819513c5913e41a9cb28777f032783；證據 release（2026-08-19）：R1 APPROVE、0 findings（Google DeepMind Antigravity，跨家族）後合併。ai-workflow ruleset 20768920「main must be green」active、required check=tests、bypass 0，故走 PR：被審 c818868 rebase 至 cb2be04 上為 800562f，內容保真＝git diff c818868 800562f 中只有 doctor.py／test_doctor.py／ROADMAP（rebase 帶進的 #109／#110），**被審的 cleanup.py 與 test_cleanup.py 不在 diff 中即逐位元未動**；PR #112 兩 check 皆 pass 後 squash merge。merge 後驗：cleanup.py 的 no_blocking_submodule 已在 origin/main。⭐ 卡面前提被執行者實測推翻、PM 複驗、查核者獨立六格矩陣逐格重現：空 gitlink 目錄移得掉，真 blocker 是曾初始化 submodule；反向新洞（gitlink 目錄有檔案但未初始化時 git 報乾淨且 remove 連同內容刪除）由新守衛封堵。⭐ 同日兩個正面佐證：cpbl#150 的 --cleanup 三項全通（其 worktree 從未 init submodule）、本卡自身 release 的 cleanup 亦然。⚠️ 本輪無 wf-review-receipt:v1 收據，留痕見 issuecomment-5337720176，機制缺口承接卡 #111。；收尾清理：已清除 worktree；遠端分支 本來就不存在；本地分支 依授權保留（未刪除）。
- 2026-08-26T22:04:10+08:00 amend by wf-cli（op 0301763e）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:415d4da5966ab294516f918c2d83a87602fb6a2299cb6a610ab8683324d418ec (981 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5336995770 · 2026-08-19T03:04:46Z

## 派工包：`WF-CLEANUP-SUBMODULE-AWARE1`（2026-08-19）

**基線** `4e6925e9fbdfd5c3ad715c63d2cb801cee63900a`（origin/main）
**分支／worktree** `claude/cleanup-submodule-aware-106` @ `/Users/ruanruan/Dev/ai-workflow/.claude/worktrees/cleanup-submodule-106`
**射程**：只准改 `cli/src/wf_cli/cleanup.py` 與 `cli/tests/test_cleanup.py`（＝資源宣告）。

### 病灶的精確形狀（PM 三次實跑，別重推導）

`git worktree remove` 被 **git 自己**的 `validate_no_submodules`（`builtin/worktree.c`，**不是 wfcli 的碼——去 cli/src 找會零命中**）拒絕，判準是「index 含 gitlink 且該路徑存在為目錄」——**空目錄也算**。而 `worktree add` 必然把 gitlink 實體化成空目錄（實測 13/13 cpbl worktree 皆有 `.ai-workflow` 空目錄）。移除該目錄後樹轉髒 → `_check_uncommitted` 擋下；`--force` 被 `cleanup.py:47-51` 的 `_forbid_force` 硬擋（掛在本模組唯一 git 入口）。**兩道門都關。**

實證留痕：`cpbl#149 issuecomment-5331774491`（三次中止＋人工收尾）、`cpbl#139` 同型。

### 特別注意

- 驗收條 2 的 fail-closed 是**攻擊條款**：構造含**已初始化**submodule 的 worktree，證明不會被刪、不 deinit、不 --force，且錯誤訊息指名人工路徑。
- 驗收條 3：既有 `test_cleanup.py` 任一測試需要**修改**才能過即算回歸破壞（新增可以）。
- 驗證條 2 要**真實 cpbl worktree 端到端**跑一次完整 cleanup 並貼原始輸出——不得只以 fake_gh/fixture 自證。⚠️ 那會真的刪掉一個 worktree：請自建一個 disposable 的（`git -C /Users/ruanruan/Dev/cpbl-analytics worktree add` 一個拋棄式分支），**不得動任何現役卡的 worktree**（目前現役含 #139/#150 等）。

### 交付紀律（三張共通）

- ⚠️ 報告中凡「實測／窮舉／全庫／逐字／唯一／零命中」，同句數字與列舉必須附指令＋原始輸出，否則寫「未驗」。
- commit 帶 trailer 四件套（Requested-by: ruan6047／Planned-by: Claude Fable 5@Claude Code (PM)／Implemented-by: 你的 claim 身分／Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>）。⚠️ trailer 守衛在「分支無新 commit」時 skip——**先 commit 再跑 pytest**，否則它整場沉睡（本專案已踩過一次）。
- Conventional Commits；push 分支，**不碰 main、不 merge、不跑任何 wfcli 動詞**；worktree 保留給查核者。
- 報告必含：逐條驗收狀態與證據、**沒驗到的／未證實假設／失敗或不如預期**（不得省略）、受 5xx／配額影響項目（標 UNKNOWN，不得寫成 0 或不存在）。
- 工具坑：`gh project item-list --format json` 的中文欄位名首位元組壞成 U+FFFD（用 endswith 後綴比對）；**body 在 `content.body`**（不必走 REST）。ai-workflow 卡面標題是半形空格、cpbl 混用全形冒號。`## Log` 有資源宣告哨兵歷史回音，判定用 `wf_cli.resources.parse_block` 不要 grep。


## Comment 5337160339 · 2026-08-19T03:30:06Z

## ⚠️ 卡面前提被執行者實測推翻（2026-08-19，PM 複驗確認）

本卡核心痛點由 PM 依三次失敗經驗撰寫，其中的機制解釋**是錯的**。執行者以 disposable worktree 逐格量測 git 自身行為推翻它，PM 已獨立複驗兩格。**驗收條不因此修改**——事後改驗收條以配合交付即是搬門柱；交付與卡面文字的偏離交查核者裁決。

### 錯在哪（PM 複驗，git 2.50.1 Apple Git-155）

卡面寫「git `validate_no_submodules` 判準是『index 含 gitlink 且該路徑存在為目錄』——**空目錄也算**，因此對任何 cpbl worktree 構造性失敗」。**實測不成立**：

```
$ git worktree add -b throwaway/pm-verify-empty /tmp/wf/pmverify origin/main
$ ls -a /tmp/wf/pmverify/.ai-workflow | wc -l   → 2（只有 . 與 ..，即 worktree add 產生的空目錄）
$ git -C /tmp/wf/pmverify status --porcelain -uno | wc -l   → 0
$ git worktree remove /tmp/wf/pmverify            （未帶 --force）
→ rc=0，目錄已移除
```

**空 gitlink 目錄移得掉。** 真正的 blocker 是 `<worktree gitdir>/modules` 存在，即**該 worktree 曾初始化 submodule**。

### 那我的三次失敗是什麼

- **`cpbl#149`**：該卡的工作內容就是 bump submodule，派工包第 2 步逐字要求 `git submodule update --init .ai-workflow`——**它落在「已初始化」那一格，真的被擋**。症狀屬實，機制歸因錯。
- **`cpbl#139`**：我先 `rmdir` 空目錄再直接帶 `--force`，**從未測過不帶 --force 是否本來就能過**。那次的人工收尾可能根本不必要。

**「此判準對任何 cpbl worktree 皆成立」是過度推論，我的錯（attribution: coordinator）。** 已連帶影響 `cpbl#149`／`cpbl#139` 的收尾留痕與 `ROADMAP §3.6` 的判準重答，三處更正另行處理。

### ⭐ 但執行者量到一個反方向的真洞，PM 複驗確認

gitlink 目錄**有檔案但 submodule 未初始化**時：

```
$ echo "重要工作內容-不該被靜默刪掉" > <worktree>/.ai-workflow/IMPORTANT.txt
$ git -C <worktree> status --porcelain --ignore-submodules=none
（空白——git 認為工作樹乾淨）
$ git worktree remove <worktree>                  （未帶 --force）
→ rc=0
$ cat <worktree>/.ai-workflow/IMPORTANT.txt
→ 檔案連同工作內容一起被刪了
```

**這是靜默的工作內容遺失**，而 `_check_uncommitted` 結構上看不到它——因為 git 自己就看不到。這正是本模組 canonical「回收前先檢查未提交變更，禁止靜默刪除工作內容」指名要防的事，而它今天防不到。

**本卡的價值因此轉向**：不是「解開一個擋住所有人的 catch-22」，而是「(a) 正確偵測真正的 blocker（已初始化 submodule）並給人工路徑，(b) 補上 git 看不見的靜默刪除防線」。執行者的實作正是這兩件——但那與卡面第 1 條驗收「移除前安全處理空的 submodule 目錄」的文字不同（它測量後**刻意不動**空目錄，並實證移走反而會讓樹轉髒、改以另一理由被拒）。**此偏離是否可接受，交查核者裁決。**


## Comment 5337326503 · 2026-08-19T03:55:52Z

# 跨家族查核委託（一）：ai-workflow 兩張治理卡（2026-08-19）

你無 wfcli 寫入通道——產出文字裁決＋findings，由需求方轉貼、PM 轉錄。全程唯讀，收尾回報兩棵真樹 `git status --porcelain -uno` 為空。

⚠️ **本委託的特殊之處：兩張卡的卡面前提都被執行者實測推翻，而 PM 已複驗確認執行者正確、PM 錯。** 所以你的第一判準不是「有沒有照卡面做」，而是「**在前提被推翻之後，交付的東西是不是對的**」。

## 環境

```
ai-workflow origin/main   4dd9d325f00050a7c056964ca93e31aeb1bedb86
#106 worktree             /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/cleanup-submodule-106
     分支/SHA             claude/cleanup-submodule-aware-106 @ c81886865d8ead489124558cdccc163b9a2e7539（基線 4e6925e）
#107 worktree             /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/daily-snapshot-107
     分支/SHA             claude/daily-snapshot-107 @ f04c29251b179c958fe7cf654a95fbecfccc6dff（三 commit）
另有 orphan 分支          origin/snapshots @ 8fda3e03019083185edc600e672a59ee769a3cf2（#107 的產物落點）
相關 PR                   #110（ROADMAP 更正，因 #106 的推翻而發）
```

進駐第一件事：`git rev-parse HEAD` 對 source_sha、工作區乾淨；不同即 review-invalid。

---

## 標的一：`#106 WF-CLEANUP-SUBMODULE-AWARE1`

改動恰兩檔＝資源宣告（`cleanup.py` +197、`test_cleanup.py` +300，既有測試刪除 0 行）。

### ⭐ 第一判準（具否決權）

卡面核心痛點（PM 寫的）：「git `validate_no_submodules` 判準是『index 含 gitlink 且路徑存在為目錄』——**空目錄也算**，故對**任何** cpbl worktree 構造性失敗」。

**執行者實測推翻，PM 複驗確認（git 2.50.1 Apple Git-155）**：空 gitlink 目錄 `worktree remove` rc=0 移得掉、不需 `--force`；真正 blocker 是 `<worktree gitdir>/modules` 存在（曾初始化 submodule）。

你要裁的第一題：**推翻本身對不對**（自己重跑那格），以及**推翻之後這張卡還該不該存在**。執行者主張價值轉向為「(a) 正確偵測真 blocker 並給人工路徑；(b) 補上 git 看不見的靜默刪除防線」。

### 要驗的

1. **推翻的六格行為表**——執行者列了六種 gitlink 目錄狀態 × `git status` × `worktree remove` 的結果。**至少親跑「空目錄可移除」與「rmdir 後樹轉髒改以另一理由拒絕」兩格**（後者是「卡面處方無出口」的關鍵）。用 disposable worktree，收尾清乾淨。
2. ⭐ **反向的新洞**（PM 已複驗，你獨立重跑）：gitlink 目錄有檔案但 submodule 未初始化時，`git status --porcelain --ignore-submodules=none` 報空、`worktree remove` rc=0 **連同內容一起刪**。判這是否構成 canonical「禁止靜默刪除工作內容」的實質違反、以及新守衛是否真的擋得住。
3. **驗收條 1 的偏離**（執行者自己指出的施力點）：卡面要「移除前安全處理空的 submodule 目錄」，交付是「測量後**刻意不動**」。PM **未修改驗收條**（事後改驗收條配合交付＝搬門柱）。判此偏離可否接受。
4. **「比 git 嚴一格」是新擋點**：非空即擋，會擋下 git 本來會放行的「非空但未初始化」。方向保守但確為新增，判可否接受。
5. **五個變異注入**是否各由指名測試接住——親跑至少兩個。
6. `pytest 1017 passed`（基線 1009+8）、既有測試零修改、`_execute_closeout` 一行未改。

### 執行者自報、需你判分量的四項

- 收尾 disposable worktree 時 `submodule deinit` 寫到**共享** `.git/config`，一度弄壞 cpbl 主 checkout 的 submodule 註冊；已修復並自報。PM 複驗現況 `f207d2e`／20 entries／status 乾淨。但執行者自陳無法證明 `submodule.active` key 動手前是否存在（未事先備份 config）。
- **git 版本只驗 2.50.1 一個**；執行者主張若某版本真的拒絕空目錄則無可實作的解（rmdir → 樹轉髒 → 改以另一理由拒絕），並寫了 `test_git_itself_refuses_removal_only_for_an_initialized_submodule` 讓判準一變即轉紅並指名理由。判這個處置是否足夠。
- **未讀 git C 原始碼**，機制解釋（`.git` 可否解析為 git dir）**未經原始碼驗證**；實作只依賴行為表。
- 已初始化路徑的行為由**拋 `CleanupGuardError`** 改為 **`detect_only`**——兩者都 fail-closed，但呼叫端錯誤處理路徑不同，執行者只讀碼未實跑。
- `Implemented-by` trailer 與卡面 owner 不逐字相同（執行者實為 Opus 5，已在 trailer 內註明），主動揭露。

---

## 標的二：`#107 OPS-DAILY-SNAPSHOT1`

改動恰兩檔＝資源宣告（`scripts/daily_snapshot.sh` +342、`snapshots/README.md` +67）。

### ⭐ 第一判準

核心痛點：canonical `AI_WORKFLOW.md:138` 逐字「必須以每日 snapshot export 回 git 建立離線稽核副本」，而實測零產物、零排程 15 天。

**執行者揭露一個 PM 開卡時不知道的差距**：`wfcli snapshot` 匯出的是**看板當前狀態**（13 個凍結欄位＋卡面資源宣告），**不含 Issue timeline 上的 lifecycle event 留言**——被事後編輯或刪除的結構化 comment，這份快照**偵測不到**。而 `:138` 要的是「**事件流**」的副本。

你要裁：**做到「狀態面那一半」算不算痛點已消？** 執行者未包裝成已解決，寫進了 README 與 commit 訊息，但 canonical 本文仍讀起來像它有。

### 要驗的

1. ⭐ **落點是孤兒分支 `snapshots` 而非 main，是執行者自主決定、卡面沒預期。** 理由：ruleset 20768920 對 default branch 要求 status check、`strict=true`、`bypass_actors` 空，無人值守直推過不去；`allow_auto_merge=false` 故走 PR 需機器自行 merge（治理違規）。⚠️ **該前提未實測**（實測需往 main 推一筆，派工明令不碰 main），旁證只有 ruleset 設定值＋生效後 main 每筆 commit 都掛得到 PR。**判此決定可否接受**；另判「新開一條遠端分支」是否逸出 `file:snapshots/` 的宣告字面。
2. **驗收條 2 明確未成立**：只有 1 筆產物且 `trigger: launchd-selftest`（kickstart 非日曆觸發，字串刻意區分）。執行者給了可證偽的預先登記：merge 後第二、三天 10:40±數分應各出現一筆 `trigger: launchd`、目錄名為當日日期；出現 `trigger: manual`、兩筆同日或目錄跳號即判排程沒跑。**判這個「時鐘從 merge 開始走」的安排可否接受**，或應退回要求先取得兩日產物。
3. **驗收條 3 未執行**，卡在授權（`AI_WORKFLOW.md` 不在資源宣告內）。判該補宣告重做，或另開卡。
4. ⚠️ **PM 卡面的 GraphQL 成本數字錯**：卡面寫「2 點/日」，PM 自跑 `gh api rate_limit` 前後差實測 **6 requests/次**（隨卡數成長，`list_items` 每 50 張多一頁）。屬 coordinator，待裁後 amend。
5. 執行者自報未驗：10:40 日曆觸發本身（只驗 kickstart）、睡眠/關機補跑、跨日產生不同目錄是用 `date` shim **模擬**非真跨日、`snapshots` 分支未來可能被 cleanup 誤判為可清理的孤兒分支。
6. `trailer 守衛實測有跑到`（`doctor --commit-trailers` 違規 0／合規 3）、`pytest 1009 passed`、escalation replay 65/65。

---

## 回報格式（兩張分開）

每張：裁決 `APPROVE`／`REQUEST_CHANGES`＋`core_pain_resolved: yes|no`＋理由。
findings 用結構化欄位：`finding_id`／`severity: critical|major|minor|info`／`blocking`／`finding_class: implementation|authoritative-artifact|governance|coordination|environment`／`attribution: executor|planner|coordinator|reviewer|external`／`root_cause_id`／`evidence`（附指令與原始輸出）／`disposition`。
⚠️ 請**只用上列列舉值**——前兩次轉錄都因用了列舉外的詞而需 PM 映射。
`self_run` 必填（無 self_run 的 APPROVE 無效）。⭐ 沒驗到的不得省略；5xx/空回應標 UNKNOWN。報告不得含 wfcli 查核事件 marker 前綴字面。


## Comment 5337509051 · 2026-08-19T04:24:11Z

<!-- wf-review-event:v1 card_id=WF-CLEANUP-SUBMODULE-AWARE1 source_sha=c81886865d8ead489124558cdccc163b9a2e7539 attempt_id=WF-CLEANUP-SUBMODULE-AWARE1-e0-c81886865d8ead489124558cdccc163b9a2e7539 -->
## 查核裁決：APPROVE

- 卡：`WF-CLEANUP-SUBMODULE-AWARE1`　attempt_id：`WF-CLEANUP-SUBMODULE-AWARE1-e0-c81886865d8ead489124558cdccc163b9a2e7539`
- 查核者：Google DeepMind Antigravity　escalation_epoch：0
- source_sha：`c81886865d8ead489124558cdccc163b9a2e7539`
- core_pain_resolved：**yes**
- 交付狀態：✅通過
- 寫入時間：2026-08-19T12:24:10+08:00

### self_run（查核者實跑）

- `獨立 disposable repo 重跑六格行為矩陣（CASE1 空 gitlink／CASE2 rmdir 後／CASE3 已初始化／CASE4 deinit 後／CASE5 未初始化含檔案／CASE6 無 submodule）`
  - CASE1 is_dir_empty=True status='' rm_rc=0 → git 原生放行；CASE2 status='D vendor/sub' rm_rc=128 'contains modified or untracked files, use --force' → 轉髒必死；CASE3 status='' rm_rc=128 'working trees containing submodules cannot be moved or removed'；CASE4 deinit 後 is_dir_empty=True 仍 rm_rc=128（modules 殘留）；CASE5 status='' rm_rc=0 file_still_exists=False → git 靜默刪除內容；CASE6 rm_rc=0 正常放行
- `反向新洞實測：在未初始化 vendor/sub 寫入 untracked_secret.txt 後 git status 與 worktree remove`
  - git status --porcelain --ignore-submodules=none 輸出為空；worktree remove rc=0，工作區被刪除且 untracked_secret.txt 遭靜默抹除。test_content_hiding_under_an_uninitialized_gitlink_path_is_refused 斷言守衛判 fail 並轉 detect_only，實測通過
- `cd .../cleanup-submodule-106/cli && uv run pytest`
  - 1017 passed in 68.00s
- `五個變異注入逐一實跑`
  - 變異1 放行非空 gitlink → test_content_hiding_... 接住；變異2 忽略無法讀取的 gitdir → test_an_unreadable_gitdir_... 接住；變異3 跳過 modules 檢查 → test_a_deinitialized_submodule_... 接住；變異4 列不出目錄當作空 → test_the_submodule_scan_reports_an_unreadable_gitlink_dir_... 接住；變異5 空目錄視為阻擋 → test_a_worktree_whose_submodule_dir_is_empty_is_cleaned_up 接住
- `進駐校驗：git rev-parse HEAD 對 source_sha、git status --porcelain -uno、git --version`
  - HEAD=c818868 對齊；工作區乾淨；git 2.50.1 (Apple Git-155)

### findings（0，其中 blocking 0）

- （無）

### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）

```yaml
wf_escalation_facts: v1
attempt_id: WF-CLEANUP-SUBMODULE-AWARE1-e0-c81886865d8ead489124558cdccc163b9a2e7539
escalation_epoch: 0
review_result: APPROVE
core_pain_resolved: yes
preflight_basis_binding: structurally-unavailable
escalation_account: not-asserted
owner_field_at_verdict_write: 待指派
findings: []
```

---

本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。
`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；`status` 新採認一律 `open`（review-escalation.md §2）；`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。
`preflight_basis_binding` 由本指令**加蓋**（提交面不得出現此鍵，出現即拒收，即使值恰好等於導出值）。它是 `event-verified` 時，§3 第 1 款是一條真的會擋下東西的檢查；是 **`structurally-unavailable`** 時，代表本 repo 沒有受管轄的 preflight pass event writer、也沒有該事件的可驗證格式——**這道閘門今天沒有鑑別力**。任何一則長得像該事件的 Issue 留言都不算依據：「受管轄」是通道屬性，而本 repo 的人類與每個 AI agent 共用同一個 GitHub 帳號，內文判定不出通道。
綁定為 `structurally-unavailable` 時，本事件**不寫** `preflight_passed`、**也不寫** `counts_toward_escalation`，改以 `escalation_account: not-asserted` 顯式宣告「不對 escalation 帳作任何斷言」。這不是把那個布林欄位擴充成三值（`unknown`／`unavailable` 仍為禁止），是不對它斷言。⚠️ 因此本事件是一則**缺 §5:168 `preflight_passed: true` 的不完整 review event**；此落差刻意不藏，應登記於 `docs/CONSUMER_CONFORMANCE.md`。
消費者**不得**把 `not-asserted` 讀成「已判定為不計數」，也不得把「本 epoch 沒有可計數 attempt」讀成「執行者沒有累計」——escalation 自動計數在承接卡（受管轄 preflight pass event 的 writer ＋ 可驗證格式）落地前不可用，**包括三振門檻**。那些 attempt 仍真實發生過，只是帳上沒有斷言。
`owner_field_at_verdict_write` 是 Project「owner」欄在**本則裁決寫入當下**的快照，**不是該 attempt 全程的 owner**。依現行派審慣例（`handoff --next-stage review --to <查核者>` 會把該欄改成查核者），此值通常是**查核者**而非產出 source_sha 的執行者；用於 `review-escalation.md` §5 第 3 款的 `continued_owner` 比對前必須先確認這一點。

## Comment 5337720176 · 2026-08-19T04:57:55Z

## ⚠️ 留痕補正：本輪裁決無 `wf-review-receipt:v1` 收據（2026-08-19，PM）

`templates/dispatch-package.md:55` 逐字要求「查核者先在被審 Issue conversation 或 PR review body 留 `wf-review-receipt:v1`（`card_id`、完整 `source_sha`、查核報告 UTF-8 `report_sha256`）」，且「PM 僅能逐字轉錄與收據 hash 相符的報告……**不能以 `--reviewer` 自由字串代替收據**」。

**本卡的 review 事件不符合這條紀律**，據實記錄：

- 本卡收據數 **0**（`gh api .../comments --jq "[.[]|select(.body|test(\"wf-review-receipt\"))]|length"`）。
- `--reviewer` 欄是 PM 打的自由字串，**非可驗證身分**。查核者的實際身分由需求方口頭轉述，機械上無從驗證。
- `wfcli doctor --review-channel` 對本卡回報 `[recorded]`（三面一致）——⚠️ **它驗的是事件／Log／Project 三面是否一致，而三面都是 PM 寫的，自然一致；收據缺席它看不見。**

**不追溯本筆裁決**，理由三項：(1) 裁決的實質內容經 PM 逐項獨立複驗（非僅信任查核者），複驗指令與輸出見本卡 review 事件的 self_run 與 PM 補正段；(2) 收據機制假設查核者能寫 GitHub，而跨家族查核者**沒有寫入通道**（既有事實），故該紀律在現行「需求方轉貼」通道上**構造上無法遵守**；(3) 追溯需重跑查核，成本遠高於風險。

機制缺口另開卡處理（承接卡見 ai-workflow）。本帖僅為留痕，不改變本卡狀態。
