# #45 WF-RECONCILE-CLEANUP-GUARD1 reconcile 的破壞性清理完全無守衛，而該指令尚未存在
- state: open  created: 2026-08-12T04:39:58Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/45
- comments: 1

## Body

- 需求：ruan6047　規劃：Claude Opus 5@Claude Code PM
<!-- wf-routing:v1 -->
- 執行：待指派（建議 主力型；須先裁定 reconcile 是否真的要存在、以及它的破壞半徑，才談得上守衛；推理鏈中等但涉及不可逆刪除的設計決策。）　查核：待指派（建議 主力型；紅線：不可逆刪除路徑，查核者須跨模型家族；查核重點在守衛是否真能覆蓋無人看管的批次情境，而非只覆蓋互動式呼叫。）
- Initiative：—　spec 基線：WF-CLEANUP-GUARD1（#25）於 2026-08-12 依需求方裁定走出路 (a) 更正核心痛點時切出（op de18defc，裁定留痕 issuecomment-5262342420）。#25 的 R4-001（critical，blocking，root_cause_id=closeout-executor-not-wired-to-real-destructive-paths）逐字要求不得以縮小驗收條文間接覆寫核心痛點，本卡即該收窄所留下的殘餘之具名承接。
- DB：db_scope=none
- 服務的原始目標：讓原本被指名的危險主體有人負責，而不是隨著射程收窄靜默消失

## 簡介
<!-- card-brief:begin -->
具名承接 WF-CLEANUP-GUARD1（aiwf#25）射程收窄後被丟下的危險主體——「一個無人看管的批次修復可以刪掉別人尚未提交的工作」，並裁定 reconcile 該不該存在。結論是停卡：該指令今天根本不存在，而危險沒消失，只是換名字成操作者在 shell 裡打 git worktree remove --force 或 rm -rf，落在本 repo 任何程式碼射程之外。**適用時機**：要查「那個 critical 痛點現在承接在哪、為什麼不建守衛」的依據；或 reconcile 真被建造時（本裁定即失效，須重開卡）。⛔ 非射程：不改 cleanup.py 的收尾 executor 形狀；release 路徑的守衛歸 aiwf#25 與 WF-RELEASE-NO-CLEANUP-REFUSE1，不在此卡。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：WF-CLEANUP-GUARD1（#25）原核心痛點的危險主體逐字是「一個無人看管的批次修復可以刪掉別人尚未提交的工作」——指的是 reconcile --apply。該卡於 2026-08-12 依需求方裁定收窄射程至 release 路徑，其交付因此**沒有關閉那個危險**。而 reconcile 這個指令今天根本不存在，所以現況不是「有一條路徑沒守衛」，是「有一個被指名的危險主體，既無實作也無守衛也無人負責」。若不具名承接，一個被跨家族查核者判為 critical 的痛點會隨著另一張卡的射程收窄而靜默消失——那正是該查核者明文禁止的形態。本卡的存在先於它的實作：即使 reconcile 長期不被建造，這張卡也必須存在，用來承接「那個危險還在」這個事實。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:docs/WF_RECONCILE_CLEANUP_GUARD1.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] 先裁定 reconcile 是否真的要存在，以及若要存在其破壞半徑為何。「不建造」是合法結論，但須說明在不建造的前提下，原危險主體是否因此消失、或只是換一個名字（例如由人手動跑一串 git 指令達成同樣效果）。
- [ ] 若裁定要建造：守衛須沿用 WF-CLEANUP-GUARD1 已交付的收尾 executor 形狀（函式體內取不到觸發者標籤，兩個觸發者共用），不得為 reconcile 另寫一條刪除路徑——後者會使 #25 買到的形狀保證失效，而該形狀已由 AST 檢查、介面面與七個分叉突變釘住。
- [ ] 須明確處理「無人看管」這個限定詞。#25 的守衛設計在互動式路徑上驗過，但原痛點指名的是批次情境；請說明批次情境下哪些前提檢查仍成立、哪些不成立（例如無人可回答的提示、無 TTY、超時後的半完成狀態）。
- [ ] 交付物須通過 WF-24-EVIDENCE-STRENGTH1 的 (e)：凡寫下「擋下／拒絕／不可能」等字眼，須指出執行者所在的檔與行、作用域邊界、邊界外會發生什麼；沒有機械執行者的寫成約定。

## 驗證

- [ ] T4：任何破壞性驗證只能在拋棄式臨時 repo 內做，不得對本專案任何真實分支或 worktree 執行刪除。
- [ ] 若裁定不建造，須以指令輸出證明今天沒有任何既有路徑可觸發 reconcile 式的批次刪除（含 scripts/ 與 cli/ 的全文掃描），而非以宣稱代替。
- [ ] T4 最高風險項須需求方 sign-off，不由查核者或 PM 代行。
## Log

- 2026-08-12T12:39:57+08:00 open by Claude Opus 5@Claude Code PM；owner 待指派；iteration 0。
- 2026-08-12T23:11:44+08:00 handoff by wf-cli → owner 待指派；iteration 1；SHA ba4755f4f2e33436d8128a9d68498250540f0cbb；證據 依 docs/ROADMAP.md §0／§3 降級：本卡屬目標 3（治理精緻化），非「防止低級事故」或「可稽核的內容」。需求方 2026-08-12 裁定降級為 Backlog、有餘力再做。⚠️ 降級不是關閉——本卡載有真實 finding 的紀錄，關閉會讓那些發現消失；降級可逆。。
- 2026-08-21T15:04:36+08:00 handoff by wf-cli → owner ruan6047；iteration 1；SHA 39b53e41a8d6d2d05413e0581fb089cdadf3c2c2；證據 需求方 2026-08-21 裁定：採卡面驗收條 :26 預先授權的「不建造」結論收尾。**無任何交付、無碼變更、未經查核**（不需要——沒有建造任何東西），故終態取 🛑已停止 而非 🏁完成。

⚠️ source_sha 為當下 origin/main（39b53e41a8d6d2d05413e0581fb089cdadf3c2c2），**非本卡交付**——本卡無交付。

裁定全文與七項指令輸出證據見 https://github.com/ruan6047/ai-workflow/issues/45#issuecomment-5366346860 ，摘要：
（1）reconcile 指令不存在（cli.py／commands/__init__.py 各 0 命中）；
（2）:34 要求的全文掃描通過——cli/src/ ＋ scripts/ 除 cleanup.py 外刪除路徑 0 命中，cleanup.py 內 15 命中全在已守衛的收尾 executor；
（3）⭐「無人看管」限定詞無對象——cleanup.py 的 input(/isatty/prompt 命中 0，executor 完全非互動；
（4）cleanup.py:185 Trigger = Literal["release","reconcile"] ⇒ 驗收條 :27 構造上已滿足；
（5）_forbid_force() 掛在模組唯一 git 入口，--force/-f/-D 送進 subprocess 前即丟 CleanupGuardError；
（6）實測 git worktree remove 對 dirty worktree 回 fatal 拒絕（拋棄式 repo 內做，符合 :33）；
（7）反方向的洞（未初始化 submodule）已由 SubmoduleScan 補上，比 git 嚴一格。

⚠️ **:26「或只是換一個名字」的答案是「有」，不得省略**：原危險主體「無人看管的批次修復刪掉別人未提交的工作」沒有消失，它換成「操作者在 shell 裡打 git worktree remove --force 或 rm -rf」，在本 repo 任何程式碼射程之外；git 預設拒絕是唯一後盾而 --force 就繞過。⭐ 卡面 :10 說本卡存在的理由是「承接『那個危險還在』這個事實」——它現在承接在裁定留言裡，不在一張永遠不會被派工的卡上。

重啟條件：若 reconcile 指令被建造，本裁定失效，須重開卡並依 :27 沿用既有收尾 executor 形狀。

⚠️ 未做：未跑 wfcli doctor；未逐行讀 cleanup.py 全部 1600+ 行（第三／五／七項為定點查證＋原文引用）；第六項未在本專案真實 worktree 重現（:33 明文禁止）。。
- 2026-08-21T15:05:44+08:00 handoff by wf-cli → owner ruan6047；iteration 0；SHA 39b53e41a8d6d2d05413e0581fb089cdadf3c2c2；證據 ⚠️ 更正前一則（15:04:36）的副作用，非新的交接：該則未帶 --iteration，handoff 自動把 iteration 由 0 遞增為 1，而**本卡從未被派工、從未被退回**——iteration=1 是假訊號。本則以 --iteration 0 釘回原值。此為 PM 操作疏失（2026-08-13 的批次狀態校正曾為同一理由明文釘 --iteration 0，本次忘記帶）。交付狀態、終態理由與證據一律不變，見 15:04 那則與 issuecomment-5366346860。。
- 2026-08-26T22:18:22+08:00 amend by wf-cli（op e0fac5d1）→ 簡介：原值指紋 sha256:6ee8b2e1733d3dbe9d1bf849faa7a845dae933fbe230f6385c44c52062aa817d (18 bytes) → 新值指紋 sha256:2343629d5340f6f3e27922bd6705542f33529605aaadebc4fed268e84a36ea0d (735 bytes)（現值見上方欄位；原值見平台 userContentEdits 前一版）；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。


## Comment 5366346860 · 2026-08-21T07:03:23Z

## 需求方裁定（2026-08-21）：採「不建造」結論，本卡收尾

PM 代擬代貼。卡面驗收條 `:26` 逐字預先授權：「**「不建造」是合法結論**，但須說明在不建造的前提下，原危險主體是否因此消失、**或只是換一個名字**」；`:34` 要求「以**指令輸出證明**…而非以宣稱代替」。以下七項全部是量測輸出。

### 一、`reconcile` 指令不存在

```
grep -c "reconcile" cli/src/wf_cli/cli.py                → 0
grep -c "reconcile" cli/src/wf_cli/commands/__init__.py  → 0
ls docs/WF_RECONCILE_CLEANUP_GUARD1.md                   → No such file
```

`cleanup.py:36` 逐字：「`reconcile --apply` 白名單第 2 條（批次）尚不存在」。

### 二、除 `cleanup.py` 外，`cli/src/` ＋ `scripts/` 沒有任何刪除路徑

```
grep -rn "worktree remove|branch -D|branch -d|rmtree|os.remove|unlink|push.*--delete|:refs/heads" \
     cli/src/ scripts/ | grep -v cleanup.py    → 0 命中
（同一組樣式在 cleanup.py 內 → 15 命中，全部落在已守衛的收尾 executor）
```

**⇒ `:34` 要求的全文掃描：通過。**

### 三、⭐「無人看管」這個限定詞在現行 executor 上**沒有對象**

```
grep -c 'input(\|isatty\|prompt' cli/src/wf_cli/cleanup.py   → 0
```

收尾 executor **完全非互動**，沒有任何提示可以「沒人回答」。卡面 `:28` 要求處理的「無人可回答的提示、無 TTY、超時後的半完成狀態」——**前兩者構造上不存在**，因為根本沒有互動點。

### 四、reconcile 若日後真被建造，會自動落進同一個守衛

```
cleanup.py:185:  Trigger = Literal["release", "reconcile"]
```

**`reconcile` 已經在同一個守衛入口的型別裡。** 卡面 `:27`（「不得為 reconcile 另寫一條刪除路徑」）**構造上已滿足**，不需要本卡做任何事來達成。

### 五、`--force` 是硬阻擋，不是約定

`cleanup.py:47-51` 逐字：「`_forbid_force()` 掛在**本模組唯一的 git 執行入口**上。任何帶 `--force`／`-f`／`-D` 等旗標的 git 呼叫會在送進 subprocess 之前就丟 `CleanupGuardError`。這不是文件約定，是呼叫點的硬阻擋」。

### 六、人手打指令時，git 自己就拒絕

實測（拋棄式 repo，未碰任何真實分支或 worktree，符合 `:33`）：

```
$ git worktree add ../gtw && echo dirty > ../gtw/x.txt && git -C ../gtw add x.txt
$ git worktree remove ../gtw
fatal: '../gtw' contains modified or untracked files, use --force to delete it
```

### 七、反方向的洞已被補上，且比 git 嚴一格

`cleanup.py:122-131` 記錄了一個 git 自己看不到的情形：「gitlink 目錄裡有檔案、但 submodule 沒初始化時，`git status` 什麼都不報、`git worktree remove` 照常移除並把那些檔案一起刪掉」。處置逐字：「本模組加的是第 2 步的一條前提（`SubmoduleScan`）：**任何非空的 gitlink 目錄都不放行**（比 git 嚴一格）」。

---

## ⚠️ `:26` 的答案：危險**沒有消失，它換了名字**

原危險主體逐字是「一個**無人看管的批次修復**可以刪掉別人尚未提交的工作」。

- `reconcile` 不存在了 ✅
- 但**操作者在 shell 裡打 `git worktree remove --force` 或 `rm -rf`** 達成完全相同的效果，而那在本 repo 任何程式碼的射程之外。
- git 的預設拒絕（第六項）是唯一的後盾，**而 `--force` 就繞過它**。

**這句話是本次結案的主要留痕，不得省略。** 卡面 `:10` 逐字寫明本卡存在的理由是「用來承接『那個危險還在』這個事實」——它現在承接在這則裁定裡，不在一張永遠不會被派工的卡上。⭐ 這正是 `#25` 的跨家族查核者當初禁止的「痛點隨另一張卡的射程收窄而靜默消失」的反面：**它沒有靜默消失，它被寫下來了。**

## 未來重啟條件

若 `reconcile` 指令被建造，本裁定失效，須重開卡並依 `:27` 沿用 `cleanup.py` 既有的收尾 executor 形狀（`Trigger` 已含 `reconcile`，見第四項）。

## ⚠️ 本次未做的事

- 未跑 `wfcli doctor`（唯讀但需網路與 owner/project 參數；PM 選擇把「零副作用」守到底）。
- 未逐行讀 `cleanup.py` 全部 1600+ 行，第三／五／七項均為定點查證＋原文引用。
- 第六項在拋棄式 repo 實測，**未在本專案任何真實 worktree 上重現**（`:33` 明文禁止）。

