# DEV-AIWF-MINIMAL-CI1 — ai-workflow 最小 CI 的裁定與自證

> 對應卡：[#48](https://github.com/ruan6047/ai-workflow/issues/48)。實作＝
> [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)（本 repo 第一支 workflow）。
> 本檔記錄「為什麼是這個形狀」「它擋得住什麼」「它擋不住什麼」，以及**哪些話是強制、哪些只是約定**。

## 0. 先講最重要的兩句

**第一句：本 CI 今天仍然不擋任何 merge。**
本 repo 沒有任何 required status check，紅叉與 merge 按鈕沒有連線。設定它是 repo 設定變更，
不在本卡寫入集。§7 已把需求方要套用的**確切設定內容**與套用後的驗證程序準備好，
但在需求方按下去之前，本 CI 提供的是**強制產生的證據**，不是**強制執行的閘門**。

**第二句：先修正一個前一輪查證的錯誤結論。**
前一輪（含查核者）以 `gh api repos/ruan6047/ai-workflow/rulesets` 回 `[]` 為據，
結論是「本 repo 沒有任何分支保護，canonical §2.2 的 `deletion` ＋ `non_fast_forward`
歷史防線也還沒實作」。**後者是錯的。** `rulesets` 是空的，但 **classic branch protection 存在**，
兩者是 GitHub 上兩套獨立的設定，各自有各自的 API：

```
$ gh api repos/ruan6047/ai-workflow/branches/main/protection
{ "enforce_admins":      { "enabled": true  },
  "allow_force_pushes":  { "enabled": false },
  "allow_deletions":     { "enabled": false },
  "required_linear_history": { "enabled": false },
  "lock_branch":         { "enabled": false },
  ... }
```

`required_status_checks` 與 `required_pull_request_reviews` 兩個鍵**不存在**於回應中——那才是
真正的缺口。所以現況精確地說是：

| canonical §2.2 要求 | 現況 | 實作在哪 |
|---|---|---|
| `non_fast_forward`（禁 force push） | **已實作**，且 admin 也受約束 | classic protection `allow_force_pushes=false` ＋ `enforce_admins=true` |
| `deletion`（禁刪分支） | **已實作**，且 admin 也受約束 | classic protection `allow_deletions=false` ＋ `enforce_admins=true` |
| CI 綠燈才能合併 | **未實作** | 無 `required_status_checks`——本卡 §7 |

真正的教訓不是「防線沒做」，是**防線做在一個沒人去看的地方**：連續兩輪、三個不同的角色都只查了
`rulesets` 就下了「什麼都沒有」的結論。§7 因此刻意把新設定放進 `rulesets`——不是因為 ruleset 比較好，
是因為**那是大家已經會去查的地方**。

往下所有措辭一律照這條分：

- **強制**＝有機械執行者，且執行者在版控裡指得出檔與行。
- **約定**＝靠人記得。canonical §2.2 已經說過靠人記得的檢查遲早會漏，本檔不假裝相反。

## 1. 裁定：最小形狀

- **跑什麼**：一個 job。`uv lock --check` 確認鎖檔沒過期（`ci.yml:76`）、
  `uv run --frozen pytest -q` 跑 `cli/` 全部測試（`ci.yml:81`）、
  `scripts/replay_escalation_rules.py` 跑 escalation 規則回放（`ci.yml:93`，理由見 §1.3）。
  **沒有 lint、沒有型別檢查、沒有 matrix**（理由見 §1.5）。
- **何時跑**：`push`（不過濾分支）與 `pull_request`（`ci.yml:14-15`）。
- **失敗時**：job exit 1，run 判 failure，PR 頁與 commit 上出現紅叉。**目前沒有東西被鎖住**（§0）。
- **check 叫什麼**：`pull_request` 事件與 push 到 main 產生的 check 叫 **`tests`**；
  其餘分支的 push run 叫 **`tests (branch head)`**（`ci.yml:43`，理由見 §1.4）。
  **只有 `tests` 該被設為 required。**

### 1.1 為什麼 `push` 與 `pull_request` 兩支都要

這是本卡最核心的設計決定。兩個事件取出的**不是同一棵樹**：

- `push` 取**分支頭**。這是執行者自己的回饋，也是 main 被推入紅碼時的事後偵測。
- `pull_request` 取 `refs/pull/N/merge`，也就是 head 併入當時 base 之後的**合併結果**。

2026-08-12 的事故整個活在這個差距裡。本機對真實 SHA 的實跑：

| 受測的樹 | 結果 |
|---|---|
| base `3e47838`（PR #27 最後一次 synchronize 時的 main） | 437 passed，綠 |
| head `4353c18`（WF-CLEANUP-GUARD1 分支頭） | 388 passed，綠 |
| **merge(base, head)**——`pull_request` 取的正是這棵 | **519 passed, 14 errors，紅** |
| `5d22a7f`（實際合併後的 main） | **644 passed, 14 errors，紅** |

PM 當時做的兩件事——`git merge-tree` 與「在分支自己的基線上跑測試」——恰好各自對應前兩列，
**兩列都是綠的，而且都是真的**。`git merge-tree` 是文字比對；四個能力旗標從選填變必填不會產生
文字衝突，所以它不會叫。只有第三列會叫，而 `pull_request` 事件天生取第三列。

**這一段不再是推理。** §2.4 有一筆真實的 `pull_request` run，log 裡自己印著
`subject = Merge a17e944… into e1b33d8…`：分支頭 659 passed 綠、合併結果 1 failed 紅，
同一分鐘、同一支 workflow、同一個 head SHA。

### 1.2 時序：CI 若當時存在，會在合併前兩小時就叫

| 時間（+08:00） | 事件 |
|---|---|
| 06:45:26 | `a5d4770` 併入 main —— 四個能力旗標改為必填 |
| 11:29:02 | PR #27 最後一次 synchronize（head `4353c18`，當時 main tip `3e47838`） |
| 13:25:11 | PR #27 合併，main 轉紅 |

11:29 的 synchronize 會觸發 `pull_request` run，取出的 merge ref 同時含陳舊 fixture 與必填旗標
——即上表第三列。距離 13:25 的合併還有近兩小時。

### 1.3 裁定：`scripts/replay_escalation_rules.py` 納入 CI

**納入。** 判準不是「凡是腳本都納入」，是這四條同時成立：

1. **它至今沒有任何自動執行者。** `cli/pyproject.toml` 的 `testpaths = ["tests"]` 讓 pytest
   永遠看不到 `scripts/`；它只在有人手動跑的時候被驗證過。
2. **它驗的是會被引用來裁決的規則**——`templates/review-escalation.md` §4／§5 的 checkpoint
   判定，也就是 finding 要不要 escalate。這比大多數 cli 測試更接近本 repo 的核心語意。
3. **它是確定性的**：純標準庫、不連網、不讀檔（`grep -n "open(\|Path(\|read_text\|__file__"`
   只命中同名的 `valid_open` 函式），退出碼即判定。
4. **它是 0.9 秒**（本機 `time` 實測），對總時間無感。

放同一個 job 而非另開一個：0.9 秒平行化沒有收益，而**每多一個 job 就多一個 required check
名字要維護，多一個設錯就讓 PR 永遠 pending 的機會**。用 `if: ${{ !cancelled() }}`（`ci.yml:91`）
讓 pytest 紅了它仍會跑，一次拿到兩個訊號；它自己失敗一樣讓 job 判紅——**這不是 `continue-on-error`**。

直譯器用 `uv run --no-project --python 3.12` 而不是 runner 的 `python3`：後者沒有釘版本。

### 1.4 裁定：required 的 check 名字不可以來自分支頭

這一條是取證過程中**實測撞到**的，不是設計時想到的，但它會讓閘門失效，所以修。

第一版 job 固定叫 `tests`。開出探針 PR 後，同一個 head SHA `f36c00e` 上出現了兩個 check：

```
$ gh api repos/ruan6047/ai-workflow/commits/f36c00e…/check-runs
tests | failure | started=11:31:35Z completed=11:32:05Z   ← pull_request（合併結果）
tests | success | started=11:31:12Z completed=11:31:38Z   ← push（分支頭）
```

**同名、同一個 SHA、結論相反、完成時間差 27 秒。** 同名 check 由哪一個算數是平台內部行為；
而在 synchronize 時兩個 run 幾乎同時啟動、耗時都是二十幾秒，誰後完成實質是擲硬幣。

**我沒有辦法證明平台會選哪一個**——那要先有 ruleset 才測得出來，而設 ruleset 不在本卡射程。
所以處置不是去論證，而是讓同名這件事**不可能發生**（`ci.yml:43`）：

```yaml
name: ${{ (github.event_name == 'pull_request' || github.ref == 'refs/heads/main') && 'tests' || 'tests (branch head)' }}
```

修完後同一形狀重測，碰撞消失（`a17e944` 的 check-runs）：

```
tests               | failure   ← 合併結果
tests (branch head) | success   ← 分支頭
```

附帶的好處正好對到本卡的主題：**分支頭綠正是 2026-08-12 誤導 PM 的那個訊號**，
現在它在 UI 上有一個不同的名字，而且結構上不可能成為閘門的依據。

為什麼不乾脆把 `push` 限制成只跑 main（那樣也沒有碰撞）：執行者在開 PR 前仍需要回饋，
而且本卡對 `5d22a7f` 的判紅取證就是靠分支 push run 做出來的。

**已知代價**：job 層的 `if:` 條件不能拿來做同樣的事——被 `if` 跳過的 job 會產生一個
conclusion 為 `skipped` 的同名 check，而 skipped 在 required check 的判定裡算通過。
**改名只能在 `name:` 這一層做，不能在 `if:` 這一層做。**

### 1.5 裁定：不把 lint 納入 CI

**不納入**，而且這是本卡最需要正面說清楚的取捨。

先講事實：**本 repo 沒有 ruff。** `git grep -i ruff origin/main` 只命中一行
`cli/.gitignore:5:.ruff_cache/`；沒有 `ruff.toml`、沒有 `[tool.ruff]`、
`cli/pyproject.toml` 的 dev group 只有 `pytest`。`uv run ruff check` 會直接
`Failed to spawn: ruff`。**「push 前跑 ruff」是 cpbl-analytics 的準則，不是本 repo 的**——
本 repo 的文件裡從來沒寫過這句（`git grep` 為證），所以這裡沒有「已宣告但無執行者」的規範可補，
只有「要不要在此刻替整個 repo 發明一套 lint 基準」這個新決定。

不納入的三個理由：

1. **加了就等於現在替整個 repo 定義 lint 基準**，而這件事本身該是一張卡，不是 CI 卡的附帶效果。
   選哪些規則集、`I001` 的 import 排序要不要管、行寬多少、既有違規一次修完還是逐檔收——
   每一項都需要需求方裁定。
2. **main 上已有既有違規**（本卡未安裝 ruff 故未親自計數，沿用派工包所載「`I001` 至少 12 筆」，
   標為**未經本卡查證**）。把 lint 加進去等於讓 CI 開局即紅，而且紅的是與正確性無關的排版。
   **一支經常為了無關理由而紅的 CI，會訓練所有人忽略紅色**——那正好摧毀本卡要建立的東西。
3. **它與本卡的痛點無關。** 08-12 的事故是陳舊基線的語意衝突，lint 抓不到；
   本卡要先把「合併結果有沒有跑過測試」這一格做成機械的。

**建議的正確路徑**（另開一卡，不在本卡射程）：一張卡內同時做完「加 ruff dev 依賴 ＋ 寫設定 ＋
一次修完既有違規」，該卡綠了之後再往 `ci.yml` 加一個 lint 步驟。順序反過來就是拿一支長期紅的 CI
去逼人修排版。

## 2. 自證：四筆真實 CI run

以下四筆全部是 GitHub Actions 的實際執行輸出，**全部跑的是本卡交付的最終版 `ci.yml`**
（前一輪那兩筆 run `31568427729`／`31568601428` 跑的是舊版檔案，已被本節取代，不再作為證據引用）。
每一筆的 log 都自己印出受測的樹（`ci.yml:54-61`），可事後對帳。

| # | run | 事件 | check 名字 | checked-out | 結果 |
|---|---|---|---|---|---|
| 2.1 | [31592609174](https://github.com/ruan6047/ai-workflow/actions/runs/31592609174) | push | `tests (branch head)` | `5e29f19` | **failure** |
| 2.2 | [31592587018](https://github.com/ruan6047/ai-workflow/actions/runs/31592587018) | push | `tests (branch head)` | `e9c8c0b` | **success** |
| 2.3 | [31592612356](https://github.com/ruan6047/ai-workflow/actions/runs/31592612356) | push | `tests (branch head)` | `a17e944` | **success** |
| 2.4 | [31592615503](https://github.com/ruan6047/ai-workflow/actions/runs/31592615503) | pull_request | `tests` | `4800f07`（merge commit） | **failure** |

### 2.1 紅：對 `5d22a7f`（修復前的紅 main）判紅

分支 `claude/DEV-AIWF-MINIMAL-CI1-red-probe`＝`5d22a7f` 的完整樹疊上最終版 `ci.yml`，
`cli/` 子樹逐位元組相同（`git rev-parse 5d22a7f:cli` 與 `5e29f19:cli` 皆為 `2379393d`）。
run 的 log 自己印出這件事：

```
event          = push
checked-out    = 5e29f1912db1765f273a1cbc25b355fb05b18f31
cli/ tree      = 2379393d99f78dfe4332967b857636a4b8ab8b56
subject        = ci(probe): re-run red evidence under the final ci.yml — DO NOT MERGE
...
wfcli open: error: the following arguments are required: --exec-capability,
  --exec-capability-reason, --review-capability, --review-capability-reason
644 passed, 14 errors in 18.45s
##[error]Process completed with exit code 1.
65/65 通過
```

`644 passed, 14 errors` 與本機對 `5d22a7f` 的實跑一致。CI 的 log 直接指名真因，不必人去逆向。
最後一行也順帶說明 `escalation replay` 在 pytest 紅之後仍然跑完（`ci.yml:91`）。

### 2.2 綠：對現在的 main 判綠

本卡的交付分支（main `e1b33d8` ＋ `ci.yml` ＋ 本檔）：

```
checked-out    = e9c8c0b0b0dc89a36095c1c808a8c0c12e0ccc40
cli/ tree      = 9f7e5e0a22424593b2728856358f61318b245223   ← 與 origin/main 相同
701 passed in 18.21s
65/65 通過
```

2.1 與 2.2 合起來證明：同一支 workflow 對紅樹判紅、對綠樹判綠。**它會分辨，不是恆綠的裝飾。**

### 2.3／2.4 `pull_request` 路徑：分支頭綠、合併結果紅

前一輪這一格只有「可證偽預測」，被查核者以 `unproven-pr-merge-ref-path` 退回。本輪改為實跑。

取證載體是**拋棄式 draft PR [#61](https://github.com/ruan6047/ai-workflow/pull/61)**，
head 分支 `claude/DEV-AIWF-MINIMAL-CI1-pr-probe`，構造刻意重現 08-12 的形狀，用今天的 main：

- 基線 `02b5d9a`（當時的 main，658 passed 全綠）
- 加一條對**當時** `cli.py` 內部結構為真的測試（動詞模組是 `wf_cli.cli` 的屬性）
- 而 `a7e5e21`（#59）之後把動詞註冊搬進 `commands/__init__.py` 的 `COMMAND_MODULES`，
  那些屬性不再存在
- **兩邊改的是不同檔案，`git merge-tree` 沒有文字衝突可報**

兩個 run 的 log 並排：

```
# 2.3  push（分支頭）           check = tests (branch head)
checked-out    = a17e9448f4fa02afef3341595206504ceb1317e2
cli/ tree      = 59a31a5d1df3ff0c4fbfaf9fc625f3364a08d50b
659 passed in 17.16s                                        → success

# 2.4  pull_request（合併結果）  check = tests
checked-out    = 4800f0761e899bab48e6b47ff754fcf1e8264819
cli/ tree      = ab7b010140648697c2242bc19dfb18ab7daec0d9
subject        = Merge a17e9448f4fa02afef3341595206504ceb1317e2 into e1b33d8984425901de400afeb227d5df67d07212
FAILED tests/test_ci_probe_stale_baseline.py::test_verb_modules_reachable_from_cli_namespace
  - AssertionError: wf_cli.cli 沒有屬性 open_cmd
1 failed, 701 passed in 20.91s                              → failure
```

**`subject = Merge … into …` 這一行是本卡最重要的一行證據**：它由 CI 自己印出，
證明 `pull_request` 事件檢出的是合併結果而不是分支頭，而那棵樹是紅的。
本機以 `git archive` 對兩棵樹先行實跑的預測（659 passed／1 failed, 701 passed）與 CI 逐數字相符。

### 2.5 這四筆證明了什麼、沒證明什麼

- **證明了**：workflow 會分辨紅綠；`pull_request` 取的是合併結果；分支頭綠與合併結果紅可以同時為真
  而 CI 兩者都看得到；同名 check 碰撞已被消除。
- **沒證明**：**紅色 check 會阻止任何人合併**。本 repo 目前沒有 required status check（§0），
  PR #61 現在的 `mergeStateStatus` 是 `UNSTABLE`／`mergeable: MERGEABLE`——
  **紅著也還是併得下去**。這一格要等需求方套用 §7 的設定才做得出來，
  §7.4 已把該次驗證要跑的指令與預期輸出寫好。**在那之前，本卡不宣稱閘門存在。**

## 3. 擋不住的事故與承接者

寫「擋不住」比寫「會擋下」重要，因為前者才是別人需要接手的部分。

**一、被合併的紅碼本身。**
CI 產生紅叉，但沒有 required status check，所以紅叉不阻止任何人按 merge。08-12 的事故若今天重演，
CI 會在 11:29 叫，13:25 仍然可以照併。→ 承接者：**需求方**（唯一有權改 repo 設定的人），
動作見 §7。在那之前「不在紅色 run 上 merge」是**約定**。

**二、CI run 本身的陳舊（stale-green）。**
`pull_request` 只在 PR 建立與 head 變動時重跑。**base 前進不會重跑**。若 PR 最後一次 synchronize
之後 base 才前進，那個綠勾指的是舊的 base，而合併用的是新的。
→ 承接者：**平台設定**，`strict_required_status_checks_policy`（§7.2）。在那之前是**約定**。

**三、測試沒覆蓋到的語意衝突。**
本 CI 的判準完全等於 `cli/tests/` ＋ 那支 replay 的覆蓋範圍。08-12 擋得住是因為那次的衝突剛好打在
fixture 上。同樣是陳舊基線，若衝突落在無測試覆蓋的路徑（例如兩張卡各自改 `AI_WORKFLOW.md` 的
相鄰段落造成規則互相矛盾、或改到 `templates/` 的文件契約），CI 全綠、事故照發。
→ 承接者：**獨立查核者**（canonical §5）。CI 不是查核的替代品。

**四、資源互斥與 control plane 的一致性。**
兩張卡宣告了相交的寫入集、狀態面與 event log 對不上——不是 pytest 看得到的東西。
→ 承接者：`wfcli doctor` 與 WF-RESOURCE-WRITESET1／WF-RESOURCE-BLOCK-ANCHOR1 那一族的守衛。

**五、CI 設定自身的退化。**
有人把 `ci.yml` 改成 `continue-on-error`、加 `paths-ignore` 讓測試被跳過、把釘住的 action SHA
換成可重指的 tag、或**把 job 改名**（§1.4：改名後 required check 永遠 pending，
而修法的誘惑會是「把 required 拿掉」）——CI 都會照樣顯示綠勾或看似無害。**CI 監督不了自己。**
→ 承接者：**查核者**對 `.github/` 變更的人工審查。這是**約定**。

**六、跨 repo 的語意衝突。**
本 repo 是 cpbl-analytics 的 submodule 來源；`templates/` 與 canonical 的改動可能讓**主專案**的
流程壞掉，而本 CI 只跑本 repo 的測試。→ 承接者：主專案自己的 CI 與部署宣告閘門。

## 4. 對既有 PR 實務（B1／B2／T0–T1）的影響

分兩種狀態講，因為兩者的答案不同。

**現在（尚未設 required check）：完全不衝突。**
直推 main 的 B1／T0–T1 照樣推得進去，只是事後多一個 run；沒有任何東西是必要條件，
在飛的十幾張卡不會被鎖住。刻意不做 `paths` 過濾（`ci.yml:16-18`）：省下的幾十秒不值得換
「日後設為 required 時被跳過的 PR 永遠停在 pending」這個坑。

**套用 §7 之後：與 canonical §0 的直推允許有真實張力，需求方必須裁。**
canonical §2.2 自己就寫過「required status checks 不是預設要求：對 §0 允許的 B1／T0–T1
直推 main 工作流，它會鎖死既有路徑」。§7.3 把三條可能的相容路徑與各自的代價列出來，
並標明哪些是我實測過的、哪些是我**預測但沒能力驗證**的。

## 5. 環境重現性：落差清單

- **`gh` 認證：無落差。** `cli/tests/` 全部用 `FakeGhRunner`（純記憶體，不打網路）與
  `sandbox_repo` fixture（`tmp_path` 底下一次性 `git init`），不需 `GH_TOKEN`、不碰真實 repo。
  CI 的 701 passed 與本機逐數字吻合就是證據。**對應地，`cli/tests/` 不驗證真實 `gh` 互動的
  正確性**——那部分由各卡的 live smoke run 承接，屬 §3 第三類。
- **replay 腳本無外部相依**：純標準庫、不連網、不讀檔（§1.3），CI 與本機都是 65/65。
- **Python patch 版本有落差**：本機 3.12.13（uv 自管），CI 是釘住的 3.12（`ci.yml:70`）。
  minor 相同、patch 不同。目前無影響，但這是真實落差。
- **本 repo 沒有 `.python-version`**：CI 側已釘死，**本機側沒有**。換一台機器、換一個 uv 預設，
  本機就可能跑在 3.13 而 CI 仍是 3.12。補一個 `.python-version` 是正解，但該檔不在本卡寫入集，
  列為 §7 待辦。
- **uv 版本已釘 `0.11.19`**（`ci.yml:69`）＝執行本卡時的本機版本。升版是刻意動作，不是自動漂移。
- **鎖檔以 `uv lock --check` 把關**（`ci.yml:76`），`uv run --frozen`（`ci.yml:81`）完全照鎖檔安裝。
- **作業系統有落差且不打算消除**：本機 macOS／arm64，CI Linux／x86-64。
  測試不含原生相依，但「只在 macOS 出現的問題」CI 看不到，反之亦然。

## 6. 第一次觸發：會發生什麼、紅了怎麼辦

- **本卡併入 main 之後**，main 上會出現第一個 push run，check 名字是 `tests`。
  以現在的 main（`e1b33d8`，701 passed）為準它會是綠的。
- **紅不會卡死 main**：沒有 required check，紅叉不阻止 push、不阻止 merge。
  **CI 本身不可能讓 main 卡死**——這是「還沒設閘門」目前唯一的好處，而它在 §7 套用後就消失。
- **若 CI 因為它自己而紅**（YAML 語法、action 版本、runner 環境），處置是 revert `ci.yml` 這一個檔：
  本卡寫入集刻意只有兩個新檔，**回退不牽動任何既有程式碼**。
- **成本**：public repo，GitHub Actions 免費額度內。單次 run 約 40 秒。

## 7. 需求方要套用的設定（本卡準備好、但無權套用）

本節是 R1-01 的處置：**設定內容與其效果**由本卡提供，套用由需求方執行。

### 7.1 確切的 ruleset 內容

```bash
gh api --method POST repos/ruan6047/ai-workflow/rulesets --input - <<'JSON'
{
  "name": "main must be green",
  "target": "branch",
  "enforcement": "active",
  "bypass_actors": [],
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
  "rules": [
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "do_not_enforce_on_create": false,
        "required_status_checks": [
          { "context": "tests", "integration_id": 15368 }
        ]
      }
    }
  ]
}
JSON
```

逐欄的理由：

- **`"context": "tests"`** —— 這個字串必須逐字等於 job 產生的 check 名字。
  **`tests` 是實測值不是猜的**：`gh api .../commits/a17e944/check-runs` 回的 `name` 就是 `tests`
  與 `tests (branch head)`。**只列 `tests`**——`tests (branch head)` 來自分支頭，
  永遠不該是閘門（§1.4）。
- **`"integration_id": 15368`** —— GitHub Actions 這個 app 的 id，同樣是實測值
  （同一個 check-runs 回應的 `app.id`，`app.slug = github-actions`）。指定它之後，
  只有 Actions 送出的 `tests` 算數，別的來源送同名 status 不能冒充。
- **`strict_required_status_checks_policy: true`** —— 這是 §3 第二類（stale-green）的唯一解：
  要求 head 分支與 base 同步後才准合併，否則 base 前進之後那個綠勾指的是舊的樹。
  **代價是真的**：本 repo 現在有二十幾個並行 worktree，main 前進得很勤，
  每次前進都會讓在飛 PR 需要更新分支並重跑。若嫌吵，這一欄可以先設 `false` 再視情況打開，
  但那等於接受 §3 第二類事故。
- **`bypass_actors: []`** —— 見 §7.3，這是唯一需要需求方拍板的一欄。
- **只放進 `rulesets`，不動 classic protection** —— 兩個理由：classic protection 的 API 是整包
  PUT，改它有把既有 `enforce_admins`／`allow_force_pushes=false` 洗掉的風險；
  而且 `rulesets` 是大家已經會去查的地方（§0）。
  **`deletion` 與 `non_fast_forward` 不要再加進這個 ruleset**——classic 已經在管，
  重複宣告會製造兩份會漂移的真相。

**回退**：`gh api --method DELETE repos/ruan6047/ai-workflow/rulesets/{id}`（id 由建立時的回應取得）。
單一物件、刪掉即完全復原，不影響 classic protection。

### 7.2 套用後會改變什麼

| | 現在 | 套用後 |
|---|---|---|
| PR 的 `tests` 紅 | 可以合併（實測 `mergeStateStatus: UNSTABLE`／`MERGEABLE`） | 合併被拒 |
| PR 的 base 在最後一次 CI 之後前進 | 綠勾照樣是綠的 | 被要求先更新分支再跑 |
| 直推 main | 允許 | **見 §7.3——這是有代價的一項** |
| force push／刪 main | 已被禁（classic） | 不變 |

### 7.3 與 canonical B1／T0–T1 直推 main 的相容性——需要需求方裁

required status check 的判定是「**被推上去的那個 commit 上有沒有綠的 `tests`**」。
直推 main 的 commit 在推之前不可能有 check（check 是推上去才跑的），所以預設情況下**直推會被擋**。

三條路，代價各不相同：

1. **接受直推消失**（`bypass_actors: []`，即 §7.1 的預設）。B1／T0–T1 也要走 PR：
   開 draft PR → 等 `tests` 綠（約 40 秒）→ 合併。閘門最強，代價是最小的卡也要多一次 PR。
2. **保留直推，改走「同一個 SHA 先取得綠 check」**：把 commit 先推到臨時分支或開 PR 讓
   `tests` 在**那個 head SHA** 上跑綠，再把同一個 SHA 直推 main。
   ⚠️ **這條我沒有能力實測**（要先有 ruleset 才測得出來），它建立在兩個前提上：
   （a）required check 是對 commit SHA 判定的；
   （b）`pull_request` run 的 check 掛在 PR 的 **head SHA** 上——**(b) 我實測過**
   （`gh api .../commits/f36c00e/check-runs` 確實回了那筆 pull_request 的 check）。
   (a) 未經本 repo 實測。**請當成待驗證的預測，不要當成事實引用。**
3. **加 admin bypass**（`bypass_actors: [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"}]`；
   `actor_id: 5` 一般對應 repository admin 角色，**但這個數字我沒有在本 repo 查證過**，
   套用前請在 ruleset 的 UI 頁面用角色名稱選一次再回讀 API 確認）。
   直推照舊，但**閘門對唯一的人類就變成可繞過**：
   紅著也還是能按 merge，只是要多按一個「我知道我在做什麼」。
   ⚠️ 誠實地說：08-12 的事故是**無意識的遺漏**（根本沒去看），不是有意識的覆寫。
   把「不可能」降成「要刻意按一下」仍然解決了那次的失效模式，但它**不擋有意識的偷懶**。

**本卡的建議**：先用第 1 條（無 bypass）跑一週。若 T0–T1 的摩擦真的痛，再改第 3 條——
從嚴放寬只要改一個欄位，從寬收緊則要重新說服自己。

### 7.4 套用後立刻可做的驗證（含現成的紅色 PR）

**PR [#61](https://github.com/ruan6047/ai-workflow/pull/61) 就是為此保留的**：它的合併結果是紅的，
是現成的失敗案例。**在套用 ruleset 並跑完這一節之前不要關它。**

```bash
# 套用前（現在的實測值）
gh pr view 61 --repo ruan6047/ai-workflow --json mergeStateStatus,mergeable
# → {"mergeStateStatus":"UNSTABLE","mergeable":"MERGEABLE"}   ← 紅著也併得下去

# 套用 ruleset 後，同一個指令
# 預期 → mergeStateStatus 變為 "BLOCKED"

# 直接試按合併（預期被拒，且訊息指名 required check）
gh pr merge 61 --repo ruan6047/ai-workflow --merge
# ⚠️ 這是刻意要它失敗；若它成功了，代表 ruleset 沒生效，請立刻回報
```

⚠️ 兩點提醒：#61 的 base 是 `02b5d9a`，已落後 main，所以在 `strict` 開啟時它會**同時**因為
「check 紅」與「分支未更新」兩個理由被擋；要單獨驗證 check 那一項，看 API 回應裡列出的
未滿足項目名稱，或先把 `strict` 設為 `false` 測一次再打開。
第二點：**這一節的預期輸出是預測，不是實測**——套用是需求方的動作，本卡無權執行。

### 7.5 其餘待辦

1. **補 `.python-version`**（§5），本機側才會跟 CI 一樣被釘住。該檔不在本卡寫入集。
2. **另開 lint 卡**（§1.5）：加 ruff 依賴 ＋ 設定 ＋ 一次修完既有違規，綠了之後再加 CI 步驟。
3. **刪除三個 DO NOT MERGE 分支與關閉 #61**——結案時做，順序見 §9。

## 8. 本檔哪些話沒有機械執行者

**有機械執行者的，逐一指得出檔與行：**

| 宣稱 | 執行者 |
|---|---|
| 每一次 push 與每一個 PR 都會跑全套 `cli/` 測試，不會被忘記 | `ci.yml:14-15` |
| PR 上測的是**合併結果**而非分支頭 | `ci.yml:15`（`pull_request` 事件語意）＋ `ci.yml:54-61` 把受測樹印進 log；實跑證據見 §2.4 |
| 測試失敗會讓 run 判紅 | `ci.yml:81`（pytest 退出碼傳導） |
| escalation 規則回放失敗會讓 run 判紅 | `ci.yml:93`（退出碼傳導）；`ci.yml:91` 保證 pytest 紅了它仍會跑 |
| 鎖檔與 `pyproject.toml` 不同步會判紅 | `ci.yml:76` |
| 分支頭的綠不可能被當成閘門的依據 | `ci.yml:43`（名字表達式）；實測見 §1.4 |
| CI 不會偷偷換 action 或 uv／Python 版本 | `ci.yml:49`、`65`（釘 commit SHA）、`69`、`70` |
| 卡住的 job 不會無限佔用額度 | `ci.yml:45`（`timeout-minutes: 15`） |
| main 不能被 force push、不能被刪，admin 也不例外 | classic branch protection（§0），不是本檔 |

**沒有機械執行者的，逐條列（自我適用）：**

- 「不在紅色 run 上 merge」——**約定**。沒有 required check，執行者是人。§7 套用後才會變成強制。
- 「合併前重跑一次 CI」——**約定**。沒有 `strict`，執行者是人。
- 「不把 `ci.yml` 改成 `continue-on-error`、不加 `paths` 過濾、不改 job 名字」——**約定**。
  `ci.yml:16-18` 與 `ci.yml:30-40` 只是註解，沒有守衛檢查它們。
- 「三個 DO NOT MERGE 分支不得併入 main」——**約定**。靠 commit 標題、draft 狀態與 §9，
  沒有機械阻擋。
- 「lint 另開一卡做」——**約定**。

## 9. 本卡產生的拋棄式物件（結案時清理）

| 物件 | 用途 | 何時可以清 |
|---|---|---|
| PR [#61](https://github.com/ruan6047/ai-workflow/pull/61)（draft） | §2.4 的 merge-ref 取證；§7.4 的現成失敗案例 | **套用 ruleset 並跑完 §7.4 之後**才關；不合併 |
| `claude/DEV-AIWF-MINIMAL-CI1-pr-probe` | #61 的 head | 關閉 #61 後刪 |
| `claude/DEV-AIWF-MINIMAL-CI1-red-probe` | §2.1 的判紅取證 | 本卡結案後刪 |
| `claude/DEV-AIWF-MINIMAL-CI1-green-control` | 前一輪的判綠對照組（已被 §2.2 取代，不再被引用） | **現在就可以刪** |

三個分支的 commit 標題都寫了 DO NOT MERGE；`-pr-probe` 與 `-green-control` 含 `cli/` 的改動，
**都不是本卡的交付物**——本卡對 `origin/main` 的 diff 只有 `.github/workflows/ci.yml`
與本檔兩個檔案。
