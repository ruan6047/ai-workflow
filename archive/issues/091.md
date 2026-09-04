# #91 WF-ASSIGN-REGISTER-AFTER-CREATE1 把 assign 的登記順序倒回 canonical：要求 worktree 先存在
- state: open  created: 2026-08-16T04:26:05Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/91
- comments: 1

## Body

- 需求：ruan6047　規劃：Claude Fable 5@Claude Code (PM)
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；改動面小（assign 的一個必填前提＋錯誤路徑）但判斷密度高：要在不破壞既有 21 個 worktree 與跨機器可攜性宣稱的前提下倒轉一個已寫進多份文件的順序，且須處理『倒轉後 assign 綁機器』這個未驗代價。經濟型容易只改必填旗標而不追既有登記與文件的連帶。）　查核：待指派（建議 高階型；本卡的價值全押在一個宣稱上——倒回 canonical 順序後軸 B 才有事實可查、兩個真實漂移 worktree 會被擋下。該宣稱來自 WF-WORKTREE-REPO-OWNERSHIP1 第五輪執行者的真實磁碟實測，尚未經任何查核者複驗。若它不成立，本卡整個沒有理由存在。另須獨立判斷『assign 綁在 worktree 所在機器』的代價，那是單機假設下容易被低估的。跨家族。）
- Initiative：—　spec 基線：—
- DB：db_scope=none
- 服務的原始目標：讓 worktree 建錯 repo 這件事有一個機械執行者會擋下它，而不是靠人記得。#57 走的是『加一個判定引擎』（+1037 行，軸 A 純字串比對且 --worktree-source-repo 非必填，漂移而不宣告仍回 allow）；本卡走的是『把順序倒回模板，讓既有的軸 B 有事實可查』。後者是預防，前者是逐案打補丁。

## 簡介
<!-- card-brief:begin -->
把 wfcli assign 的 --worktree required=True 造成的「登記必然早於建立」順序倒回 templates/worktree-lifecycle.md 第 1 點的先建後登記，使 registry.observe_local_worktree（軸 B）不再恆沉默——實測兩個至今仍在的跨 repo 漂移 worktree 在現行順序 assign exit 0 放行、倒轉後 exit 6 被擋。另須把「assign 自此綁在 worktree 所在機器」的代價寫進 help 並註明單機是假設非已驗事實。**適用時機**：要改 assign 的 worktree 前提或錯誤路徑時；或要判斷「worktree 建錯 repo 由哪一軸擋下」時。⛔ 非射程：不走 WF-WORKTREE-REPO-OWNERSHIP1（aiwf#57）那條「加一個判定引擎」的逐案補丁路線；不回溯檢查既有登記，不得讓已完成的卡因新前提變成違規。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：wfcli assign 的 --worktree 是 required=True，把 claim 與登記併成一步，使【登記必然早於建立】。於是 registry.observe_local_worktree（軸 B）在現行操作順序下恆沉默——它只在『登記的路徑此刻存在、且它自己就是另一個 repo 的 worktree』時說得出話，而登記時目標永不存在。模組自陳『它的沉默不是判定』。⚠️ 這個順序與 canonical 相反：templates/worktree-lifecycle.md 第 1 點逐字寫『Coordinator／祕書原子 claim 成功後建立 worktree，並把實際路徑＋分支寫回卡面』＝先建後登記。是 CLI 把順序倒過來的，不是模板要求的。代價實測（WF-WORKTREE-REPO-OWNERSHIP1 第五輪，真實磁碟非 fixture）：兩個至今仍在的跨 repo 漂移 worktree（cpbl-analytics 底下、commondir 指向其 .git/modules/.ai-workflow、origin 是 ai-workflow、卻註冊在 cpbl 的卡上）在現行順序下 assign exit 0 放行，在倒轉順序下 assign exit 6 擋下，擋它們的是軸 B 不是軸 A。⚠️ 該實測未經查核者複驗，是本卡的頭號待驗證假設。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/assign_cmd.py",
    "file:cli/tests/test_commands_mocked.py",
    "file:templates/worktree-lifecycle.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] assign 在登記的 worktree 路徑不存在時 fail-closed，並在錯誤訊息指出正確順序是先 git worktree add 再 assign；不得只降為 warning。
- [ ] 兩個真實跨 repo 漂移 worktree 的重現案例（或其等價 fixture）在本卡交付後由 assign 擋下，且證據須指明擋它的是軸 B（observe_local_worktree）而非軸 A。⚠️ 若複驗發現該宣稱不成立，本卡應即刻停止並回報，不得改用其他理由續作。⚠️ 2026-08-16 跨家族查核已獨立複驗此前提成立（現行順序 exit 0、先建後登記 exit 6），但仍請自行重跑。
- [ ] templates/worktree-lifecycle.md 第 1 點與 CLI 行為一致——現況是文件說先建後登記、CLI 強制先登記後建，兩者擇一改到相符，不得留下兩份互相矛盾的敘述。
- [ ] 『assign 自此綁在 worktree 所在的機器上』這個代價須寫進 assign 的 help 與 --worktree 的說明，且須明寫本專案單機是【假設非已驗事實】。不得只寫在卡面或 commit message。
- [ ] 【承接 #57 的 R5-01】registry.py 模組 docstring 第 1 點在 a5d3843 加上的限定詞（「今天的」「所以這一刻的」）目前只被一條宣稱過強的測試守著：跨家族查核實測——整段回退會紅，但【只移除那兩個限定詞仍是 1 passed】，因為三個 required token 可在後段繼續滿足、而 banned 字串受 reflow 空白影響沒命中。本卡改該段文字時須一併修正該測試：比對正規化後的局部句／段落關係，不得只驗三個 token 在模組任意位置存在。⚠️ 須以變異檢驗證明「只移除限定詞」這個具體變異會轉紅。

## 驗證

- [ ] 倒轉前後各跑一次真實磁碟重現（非 fixture），逐筆記錄 exit code 與判定它的軸，數字須可重跑。
- [ ] 全 repo grep 既有登記：確認倒轉後既有卡片的登記不被回溯檢查（不得讓已完成的卡因新前提變成違規）。
- [ ] cli 測試全綠且新增測試在移除該必填前提時轉紅（變異檢驗）。
## Log

- 2026-08-16T12:26:04+08:00 open by Claude Fable 5@Claude Code (PM)；owner 待指派；iteration 0。
- 2026-08-16T22:55:36+08:00 amend by wf-cli（op 88dc15c8）→ 驗收條件：原值「[ ] assign 在登記的 worktree 路徑不存在時 fail-closed，並在錯誤訊息指出正確順序是先 git worktree add 再 assign；不得只降為 warning。；[ ] 兩個真實跨 repo 漂移 worktree 的重現案例（或其等價 fixture）在本卡交付後由 assign 擋下，且證據須指明擋它的是軸 B（observe_local_worktree）而非軸 A。⚠️ 若複驗發現該宣稱不成立，本卡應即刻停止並回報，不得改用其他理由續作。；[ ] templates/worktree-lifecycle.md 第 1 點與 CLI 行為一致——現況是文件說先建後登記、CLI 強制先登記後建，兩者擇一改到相符，不得留下兩份互相矛盾的敘述。；[ ] 『assign 自此綁在 worktree 所在的機器上』這個代價須寫進 assign 的 help 與 --worktree 的說明，且須明寫本專案單機是【假設非已驗事實】。不得只寫在卡面或 commit message。」→ 新值「assign 在登記的 worktree 路徑不存在時 fail-closed，並在錯誤訊息指出正確順序是先 git worktree add 再 assign；不得只降為 warning。；兩個真實跨 repo 漂移 worktree 的重現案例（或其等價 fixture）在本卡交付後由 assign 擋下，且證據須指明擋它的是軸 B（observe_local_worktree）而非軸 A。⚠️ 若複驗發現該宣稱不成立，本卡應即刻停止並回報，不得改用其他理由續作。⚠️ 2026-08-16 跨家族查核已獨立複驗此前提成立（現行順序 exit 0、先建後登記 exit 6），但仍請自行重跑。；templates/worktree-lifecycle.md 第 1 點與 CLI 行為一致——現況是文件說先建後登記、CLI 強制先登記後建，兩者擇一改到相符，不得留下兩份互相矛盾的敘述。；『assign 自此綁在 worktree 所在的機器上』這個代價須寫進 assign 的 help 與 --worktree 的說明，且須明寫本專案單機是【假設非已驗事實】。不得只寫在卡面或 commit message。；【承接 #57 的 R5-01】registry.py 模組 docstring 第 1 點在 a5d3843 加上的限定詞（「今天的」「所以這一刻的」）目前只被一條宣稱過強的測試守著：跨家族查核實測——整段回退會紅，但【只移除那兩個限定詞仍是 1 passed】，因為三個 required token 可在後段繼續滿足、而 banned 字串受 reflow 空白影響沒命中。本卡改該段文字時須一併修正該測試：比對正規化後的局部句／段落關係，不得只驗三個 token 在模組任意位置存在。⚠️ 須以變異檢驗證明「只移除限定詞」這個具體變異會轉紅。」；理由 承接 WF-WORKTREE-REPO-OWNERSHIP1（#57）R5-01 這條無機械落點的 non-blocking finding。需求方 2026-08-16 裁定 #57 採丙案（不把跨家族輸出當查核記、卡收回 Backlog），代價是其兩條 non-blocking finding 不入 finding 帳；R5-02 已由 op 7a9c7a0f 修正，R5-01 會掉。#91 本來就要動 registry.py 模組 docstring 第 1 點的同一段文字（那正是本卡要改的順序敘述），故由本卡接住，非擴大射程。。
- 2026-08-26T21:58:47+08:00 amend by wf-cli（op 1d96aae2）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:3ce24a7111577c00d100bc56a6ec0fa42a7d45b907cc9736038220f2afdf23ae (800 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。
- 2026-08-29T14:59:44+08:00 handoff by wf-cli → owner 待指派；iteration 0；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 阻塞登記（來源狀態 📥Backlog）：https://github.com/ruan6047/ai-workflow/issues/91 之阻塞留言。解除條件＝待審清單機制上線。。


## Comment 5460928628 · 2026-08-29T06:55:54Z

## 阻塞登記

**狀態**：⏸阻塞。**來源狀態：📥Backlog**（解除時回到此狀態）。

**阻塞原因**：需求方於 2026-08-29 決定，在階段狀態重整（8 階段 × 10 狀態、待審清單、CLI 射程收斂）定案並落地前，暫停所有 ai-workflow 流程卡，避免它們與重構討論互相干擾。

**可證偽的解除條件**：待審清單機制上線（label ＋ issue template ＋ 可見分組）。屆時本卡改列為清單參考項，或依當時前提是否仍成立重新排程。

**本次未做**：核心痛點、驗收條件、射程一律未動。`iteration` 未遞增。`階段` 欄未寫入。本登記僅改交付狀態與 owner。

**已知的射程重疊**（供解除時參考，非本次裁定）：#66／#38 的實質可能由「七份交接文件格式」承接；#128 可能由「待審清單收件條件三·查重留痕」＋`open --from-issue` 承接；#11 的證據紀律已部分寫入 PM 準則但痛點（靠人記得）未消失。⛔ 上述皆未經裁定，解除時須逐張重驗。

**裁定者**：需求方 ruan6047，2026-08-29 本 session 對話中指示「把目前所有 WF 卡片暫停，避免干擾目前重構討論」。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

