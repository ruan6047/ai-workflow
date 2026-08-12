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

- **跑什麼**：一個 job。`uv lock --check` 確認鎖檔沒過期（`ci.yml:101`）、
  `uv run --frozen pytest -q` 跑 `cli/` 全部測試（`ci.yml:106`）、
  `scripts/replay_escalation_rules.py` 跑 escalation 規則回放（`ci.yml:118`，理由見 §1.3）。
  **沒有 lint、沒有型別檢查、沒有 matrix**（理由見 §1.5）。
- **何時跑**：`push`（不過濾分支）與 `pull_request`（`ci.yml:14-15`）。
- **失敗時**：job exit 1，run 判 failure，PR 頁與 commit 上出現紅叉。**目前沒有東西被鎖住**（§0）。
- **check 叫什麼**：`pull_request` 事件與 push 到 main 產生的 check 叫 **`tests`**；
  其餘分支的 push run 叫 **`tests (branch head)`**（`ci.yml:56`，理由見 §1.4）。
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
名字要維護，多一個設錯就讓 PR 永遠 pending 的機會**。用 `if: ${{ !cancelled() }}`（`ci.yml:116`）
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
所以處置不是去論證，而是讓同名這件事**不可能發生**（`ci.yml:56`）：

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
每一筆的 log 都自己印出受測的樹（`ci.yml:75-86`），可事後對帳。

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
最後一行也順帶說明 `escalation replay` 在 pytest 紅之後仍然跑完（`ci.yml:116`）。

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
在飛的十幾張卡不會被鎖住。刻意不做 `paths` 過濾（`ci.yml:17-19`）：省下的幾十秒不值得換
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
- **Python patch 版本有落差**：本機 3.12.13（uv 自管），CI 是釘住的 3.12（`ci.yml:95`）。
  minor 相同、patch 不同。目前無影響，但這是真實落差。
- **本 repo 沒有 `.python-version`**：CI 側已釘死，**本機側沒有**。換一台機器、換一個 uv 預設，
  本機就可能跑在 3.13 而 CI 仍是 3.12。補一個 `.python-version` 是正解，但該檔不在本卡寫入集，
  列為 §7 待辦。
- **uv 版本已釘 `0.11.19`**（`ci.yml:94`）＝執行本卡時的本機版本。升版是刻意動作，不是自動漂移。
- **鎖檔以 `uv lock --check` 把關**（`ci.yml:101`），`uv run --frozen`（`ci.yml:106`）完全照鎖檔安裝。
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

### 7.0 ⚠️ 套用順序是強制的：先合併本卡，再套 ruleset

**這一節是 `R2-003` 的處置。** 前一版的 §7.1 直接給出 `enforcement: active` 的 POST 指令，
卻沒有寫「什麼時候可以按下去」。**照那樣做會把所有在飛 PR 鎖死。**

機制：

1. `.github/` **不存在於 `main`**（實測：`git ls-tree origin/main --name-only` 無 `.github`；
   本 workflow 是本 repo 的第一支，還在本卡分支上）。
2. `pull_request` 事件測的是 `refs/pull/N/merge`，也就是 **base 與 head 的合併結果**。
3. 對一個 head 不含 `ci.yml` 的在飛分支，其合併結果同樣不含 `ci.yml`（base 也沒有）
   → **那個 PR 上永遠不會出現名為 `tests` 的 check**。
4. required status check 對「從未出現過的 check」的判定是**無限期 pending**，不是通過。

**結論：ruleset 一旦在本卡合併前套用，本 repo 現有的每一個在飛 PR（含本卡自己的 PR）
都會立刻變成永遠合不進去。** 而解鎖的唯一辦法是把 ruleset 刪掉——也就是說那是一個
會把自己鎖在門外的動作。

#### 強制順序

| 序 | 動作 | 誰做 | 完成判準 |
|---:|---|---|---|
| 1 | 合併本卡到 `main`（`.github/workflows/ci.yml` 因此進入 `main`） | 需求方／獲授權者 | `git ls-tree origin/main .github` 有輸出 |
| 2 | 確認合併後 `main` 的 push run 產生名為 **`tests`** 的 check 且為綠 | 任何人，讀 API | `gh api repos/ruan6047/ai-workflow/commits/main/check-runs --jq '.check_runs[]｜{name,conclusion}'` 出現 `tests` ＋ `success` |
| 3 | **只有第 2 步綠了才**套用 §7.1 的 ruleset | 需求方 | POST 回 201 |
| 4 | 依 §7.4 驗證閘門真的會擋 | 需求方 | `#61` 的 `mergeStateStatus` 由 `UNSTABLE` 變 `BLOCKED` |

⚠️ **第 2 步不可省略。** 它同時證明兩件事：workflow 在 `main` 上真的會跑；以及它產生的
check 名字**逐字**是 `tests`（`§7.1` 的 `context` 欄要比對的就是這個字串，拼錯的後果與
第 3 點相同——永遠 pending）。§1.4 的名字表達式讓 `main` 的 push run 也叫 `tests`，
就是為了讓這一步在合併前後都可驗。

#### 在飛分支怎麼辦（第 1 步之後、它們各自更新之前）

關鍵差別在 **base 有沒有 `ci.yml`**：

- **第 1 步之前**（現況）：base 與 head 都沒有 → 合併結果沒有 workflow → 永遠不產生 `tests`。
  這就是上面第 3 點，也是不能先套 ruleset 的原因。
- **第 1 步之後**：base 已含 `ci.yml` → 合併結果含 workflow → **預期會**產生 `tests`。

⚠️ **後者是預測，本卡沒有實測。** 本卡已有的 `pull_request` 實跑（run `31592615503`）
不能當它的證據：`#61` 的 head 分支自己就含 `.github`（`git ls-tree` 為證），
所以那一筆只證明「head 有就會跑」，**沒有證明「只有 base 有也會跑」**。
前者依賴的是 merge ref 的 git 語意（合併結果含兩側的檔），與 GitHub 由哪一個 ref
解析 workflow 檔的實作行為——後半段是平台行為，我無法在不套用設定的情況下驗證。
**§7.0 的第 2 步之所以必須是一個獨立的完成判準，就是為了在這裡不靠猜。**

另有一個獨立於上述的事實：GitHub **不會**因為 base 前進而自動重跑既有 PR。
所以就算上述預測成立，在飛 PR 也要等下一次 `synchronize`（往該分支推任一 commit，
或關掉再開 PR）才會長出 check。

**因此第 3 步之後、在飛 PR 被推過一次之前，它們的 `tests` 是「不存在」而非「紅」，
而 required 對「不存在」的判定是 pending。**
若嫌這段空窗吵，兩個選項：把 `enforcement` 先設 `evaluate`（GitHub 的 dry-run 模式，
只記錄不阻擋）跑一輪確認每個在飛 PR 都長出 `tests` 之後再改 `active`；
或接受每張在飛卡在下一次推送時自然取得 check。**本卡建議前者**——它讓第 3 步的風險降到零，
代價只是多一次 PATCH。

⚠️ **本節第 1～4 步全部是需求方的動作，本卡無權執行，因此以上關於「套用後會發生什麼」
的敘述一律是預測而非實測。** 唯一實測的是前提：`main` 現在沒有 `.github`（§7.0 第 1 點）。

### 7.1 確切的 ruleset 內容

⚠️ **按下這段之前先讀 §7.0。順序錯了會鎖死整個 repo。**

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
| PR 上測的是**合併結果**而非分支頭 | `ci.yml:15`（`pull_request` 事件語意）＋ `ci.yml:75-86` 把受測樹印進 log；實跑證據見 §2.4 |
| 測試失敗會讓 run 判紅 | `ci.yml:106`（pytest 退出碼傳導） |
| escalation 規則回放失敗會讓 run 判紅 | `ci.yml:118`（退出碼傳導）；`ci.yml:116` 保證 pytest 紅了它仍會跑 |
| 鎖檔與 `pyproject.toml` 不同步會判紅 | `ci.yml:101` |
| 分支頭的綠不可能被當成閘門的依據 | `ci.yml:56`（名字表達式）；實測見 §1.4 |
| CI 不會偷偷換 action 或 uv／Python 版本 | `ci.yml:62`、`90`（釘 commit SHA）、`94`、`95` |
| 卡住的 job 不會無限佔用額度 | `ci.yml:58`（`timeout-minutes: 15`） |
| CI 的 locale 是宣告值而非繼承 runner image | `ci.yml:32-34`（`env:` 是 workflow 層，所有 step 一律生效）；理由見 §10 |
| runner image 的預設 locale 與宣告值不一致時看得見 | `ci.yml:80-86`（每一 run 都印生效值與 image 預設值） |
| main 不能被 force push、不能被刪，admin 也不例外 | classic branch protection（§0），不是本檔 |

**沒有機械執行者的，逐條列（自我適用）：**

- 「不在紅色 run 上 merge」——**約定**。沒有 required check，執行者是人。§7 套用後才會變成強制。
- 「合併前重跑一次 CI」——**約定**。沒有 `strict`，執行者是人。
- 「不把 `ci.yml` 改成 `continue-on-error`、不加 `paths` 過濾、不改 job 名字」——**約定**。
  `ci.yml:17-19` 與 `ci.yml:45-55` 只是註解，沒有守衛檢查它們。
- 「三個 DO NOT MERGE 分支不得併入 main」——**約定**。靠 commit 標題、draft 狀態與 §9，
  沒有機械阻擋。
- 「lint 另開一卡做」——**約定**。
- 「任何 bash 腳本或內嵌探針被接進 CI 時，該步驟必須在 `LC_ALL=C` 與 `LC_ALL=C.UTF-8` 各跑一次」
  ——**約定**（§10.2 的改判條件）。今天 CI 一行 bash 腳本都沒跑，故無從機械化；
  接線的人是不是會記得這一條，沒有東西在檢查。
- 「ruleset 必須在本卡合併且 `main` 的 `tests` 綠之後才套用」——**約定**（§7.0）。
  執行者是需求方本人。**這一條若被跳過，後果是整個 repo 的 PR 全數鎖死**，
  而沒有任何東西會在按下 POST 之前攔住它。

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

---

## 10. 裁定：locale

需求方 2026-08-12 指派本項納入本輪（`#48` 的 `issuecomment-5267275511`）。成因：`#42` 的對帳器
只在 UTF-8 locale 下 `exit 1`（`line 36: min?: unbound variable`），在 `LC_ALL=C` 下 PASS，
而 PM 的 shell 是 `LANG=""`／`LC_CTYPE=C`，於是「四種環境全綠」實際上只驗到同一個軸。

### 10.0 ⚠️ 先更正指派文字裡的一個前提：runner 的預設**不是** UTF-8

指派逐字寫「**本卡的 CI 跑在 GitHub 的 ubuntu runner，那是 UTF-8 locale**」，並據此推論
本 repo 存在一類「本機綠、CI 紅」的落差。**前半句是錯的。** 本卡把 image 的預設值印進 log
實測（run [31612860735](https://github.com/ruan6047/ai-workflow/actions/runs/31612860735)，
`env -u LANG -u LC_ALL locale`）：

```
--- runner image 的預設（不受本 workflow env 影響）---
LANG=
LANGUAGE=
LC_CTYPE="POSIX"
LC_COLLATE="POSIX"
...（其餘 LC_* 全為 POSIX）
```

`ubuntu-latest` 的預設是 `LANG` **未設**、所有 `LC_*` 落在 **`POSIX`**——
也就是 **C locale，與 PM 那台本機同一側**。

這把結論反轉了：**若不顯式釘 locale，本 CI 會與 PM 的 shell 一樣對 `#42` 那一類問題失明。**
指派原本假設 CI 天生就是比較嚴的那一邊、只要把腳本推進來就會抓到；實際上不釘的話，
CI 只會把同一個盲點複製一份，而且是複製到一個大家更會信任的地方。

- 對照組（同一 run，`locale` 印生效值）：`LANG=C.UTF-8`、全部 `LC_*` 為 `C.UTF-8`
  → **`ci.yml:32-34` 的宣告確實生效，且 `C.UTF-8` 在 `ubuntu-latest` 上存在、未靜默退回 `POSIX`。**
- 同一 run 全綠：`701 passed`、replay `65/65 通過`、check `tests (branch head)` = `success`。
  **釘 UTF-8 沒有讓現有的東西變紅。**

本 repo 因此存在的落差要重述為：**「本機綠、CI 也綠、但在任何一台正常設定 locale 的機器上紅」**
——比原本的說法更糟，因為那一類問題在兩道關卡都不會被發現。下面四問的裁定建立在這個更正之上。

以下四問逐一裁定。**先講三件本卡實測到的事**，因為它們決定了答案：

| 實測 | 結果 |
|---|---|
| `LC_ALL=C uv run --frozen pytest -q`（本機） | `701 passed` |
| `LC_ALL=C.UTF-8 uv run --frozen pytest -q`（本機） | `701 passed` |
| `replay_escalation_rules.py` 在 `LC_ALL=C` 與 `LC_ALL=C.UTF-8` | 兩者皆 `exit=0` |
| 同兩者在 CI 的 `C.UTF-8` 下（run `31612860735`） | `701 passed` ＋ `65/65 通過`，job success |

也就是說：**本 CI 今天實際執行的三個步驟，經實測對 locale 不敏感。**
`#42` 那一類是 **bash** 的變數名掃描行為，而**本 CI 一行 bash 腳本都沒跑**（只有 workflow 自己
那幾行 `echo`）。這個事實把四問全部拉回同一個判準：**現在做的是「把基準釘住」，不是「抓現有的蟲」。**

### 10.1 第一問：CI 該不該顯式釘 locale？——**該，釘 UTF-8**

已實作（`ci.yml:32-34`，workflow 層 `env:`，所有 step 一律生效）。三個理由：

1. **不釘的預設值是 `POSIX`，不是中立值**（§10.0 實測）。不釘＝把 CI 調成與已知會漏掉問題的
   那台機器同一側。這一條在拿到 log 之前只是原則，拿到之後是事實。
2. **就算預設是 UTF-8，不釘仍然錯。** runner image 的預設 locale 是 image 的實作細節，
   GitHub 可以在任何一次 image 更新裡改它。判定基準託付給那種值，等於本 repo 的紅綠
   會在沒有任何 commit 的情況下改變——這與 §5 釘死 uv／Python／action SHA 的理由完全相同，
   是同一條紀律的漏項。
3. **選 UTF-8 而不是 C：CI 該是比較嚴的那一邊。** 需求方的問題把兩個方向都寫成正當的，
   我不同意這是對稱的：釘 `C` 的唯一好處是「與已知會漏掉問題的那台機器一致」——
   **那是把偵測器調成永遠不會響**，而那正是 08-12 誤判的成因。至於「釘 UTF-8 可能讓既有腳本
   一開就紅」這個顧慮，§10.0 的 run 已證偽：全綠。
4. **今天釘幾乎沒有代價**（上表與 §10.0 的 run：兩個 payload 在兩種 locale、本機與 CI 都綠），
   **而以後釘就會有代價**——等到有腳本進 CI 才釘，就要同時吸收「釘住」與「修好」兩件事。

順帶把「宣告值」與「生效值」拆開印在每一 run 的 log 裡（`ci.yml:80-86`）：
`locale` 印生效值，`env -u LANG -u LC_ALL locale` 印 image 的預設值。
理由是 `LC_ALL=C.UTF-8` 若在該 image 上不存在，glibc 會**靜默退回** `POSIX` 而不報錯；
不印出來就看不見。**這是觀測，不是判定**——兩者不一致不會讓 job 變紅，只會在 log 裡看得到。

✅ **已實測**（run [31612860735](https://github.com/ruan6047/ai-workflow/actions/runs/31612860735)，
`checked-out = 8d3adbf`）：`C.UTF-8` 在 `ubuntu-latest` 上存在、宣告生效、未退回 `POSIX`，
且釘住之後 `701 passed` ＋ replay `65/65` 全綠。逐字輸出見 §10.0。

### 10.2 第二問：要不要跑兩次？——**不要，現在不要**

判準是**兩次跑的差異能不能被解讀**。今天不能：

- 本 CI 的三個步驟經實測兩種 locale 同結果，跑兩次必然得到兩份相同的輸出。
  **一個永遠不會有差異的比較不是檢查，是儀式**——時間翻倍、兩份輸出要對帳、
  而且它會製造一個「我們有在測 locale」的錯覺，比不做更糟。
- 真正需要雙跑的是 **bash 腳本**，而本 repo 的 bash 全部活在文件裡、今天零自動執行者（見 §10.3）。
  **雙跑矩陣屬於那個執行者，不屬於這裡。** 先有被測物，才有測法。

**改判條件寫在這裡，讓它不必靠人記得**：一旦有任何 `.sh` 或內嵌 bash 探針被接進本 CI，
那一步必須在 `LC_ALL=C` 與 `LC_ALL=C.UTF-8` 各跑一次，差異即為 locale 敏感的證據。
⚠️ **這一條沒有機械執行者**，登記在 §8 的約定清單。

### 10.3 第三問：本卡射程涵不涵蓋文件內嵌探針？——**不涵蓋**

需求方問的是「探針是不是與 `replay_escalation_rules.py` 同一類」。**不是**，判準用 §1.3 那四條原樣套：

| §1.3 的判準 | `replay_escalation_rules.py` | 文件內嵌 bash 探針 |
|---|---|---|
| 至今無自動執行者 | ✅ | ✅ |
| 驗的是會被引用來裁決的規則 | ✅ | 部分 |
| **確定性、退出碼即判定** | ✅ 純標準庫、不連網、不讀檔 | ❌ **多數讀 repo 狀態、打 `gh`、依賴當下 SHA** |
| 秒級 | ✅ 0.9 秒 | ❌ 未知 |

決定性的是第三條。replay 腳本是一個**版控裡的可執行檔，有明確的退出碼契約**，
pytest 看不到它純粹是 `testpaths = ["tests"]` 的機械後果——**接上執行者只是接線**。
文件內嵌探針**連「被測物」都還不存在**：它們是 markdown code fence 裡的文字，
要先有一個抽取器（哪些 fence 是探針？靠什麼標記？）、一個沙箱（它們會打 `gh`、會讀
worktree 狀態）、以及一份「什麼算通過」的契約。**那是一張卡的工作量，不是一個 CI 步驟。**

另外兩條理由：

- **寫入集**。本卡的資源宣告是嚴格兩檔。抽取器與其契約至少要新增 `scripts/` 下的檔案，
  已在宣告之外。
- **與 §1.5 排除 lint 同一個論證**。把一批從未被自動跑過的東西一次接進 CI，
  幾乎保證 CI 開局即紅，而紅的理由是「這些探針本來就沒被維護過」——
  **一支經常為了無關理由而紅的 CI 會訓練所有人忽略紅色**，那會摧毀本卡要建立的東西。

**本卡在此項唯一該做也已做的事：把 CI 的 locale 釘成 UTF-8。** 這樣當探針日後被接進來，
它們一落地就在會抓到 `#42` 那一類問題的環境裡跑，不必再回頭改基準。

### 10.4 第四問：超出射程的部分，承接者是誰

依 `docs/ROADMAP.md` §5，**finding 不得直接開卡**，排程是需求方的。所以這裡給的是
「建議的承接形狀」，登記與排序由需求方裁。分成三段，因為它們的承接者不同：

| 段 | 內容 | 建議承接者 | 依據 |
|---|---|---|---|
| A | `#42` 對帳器那一行的修復 | **`#42` 自己**（`WF-CONTROL-PLANE-TYPE-REGISTRY1`） | 它是被害者也是持有者。ROADMAP §3 已裁定 `#42`「當前輪次跑完即停，轉 Backlog」——修這一行屬**當前輪次內**，不是新工作 |
| B | 文件內嵌 bash 探針的抽取器＋執行者 | **建議開新卡**（暫名 `DEV-DOC-PROBE-RUNNER1`），服務目標 1，排序在 `#48` 之後 | ROADMAP §2：需要牙齒的偵測器排在 `#48` 之後。它今天**沒有**受害者（探針沒被跑，也就沒害到人），依 §5 第 2 步偏向「記錄，不開卡」——**故本卡不主張它現在就做，只主張它被登記** |
| C | 其他 locale 敏感形狀的系統性檢查（`tr`／`sed` 字元類、`sort` 定序、`wc -m`、`[[ ]]` 的字典序比較） | **無人**，且本卡主張**現在不要指派** | PM 自己已聲明只排除了「`$var` 緊接全形標點」一種形狀。把「系統性檢查所有 locale 敏感形狀」變成任務，是拿一個無界的搜尋去換一個尚未發生的事故——典型的 ROADMAP §0 目標 3 |

⚠️ **A 段是本節唯一有已知現存受害者的一項**（`#42` 的對帳器今天在 UTF-8 下就是紅的）。
依 ROADMAP §5 第 1 步，它是「會不會現在就造成低級事故」那一格——**但它落在 `#42` 的射程內，
不落在本卡**。本卡對它的處置就是這一行登記，不代修。

---

## 11. `R2-001`：射程問題，以及一個真實的環

**這一節不改任何交付物，它是把一個結構性問題攤開來交還給需求方。**
`R2-001` 的 disposition 給了兩條路（同一交付含套用 ruleset／把原始目標修窄為「提供 CI 證據」），
並註明後者「必須重新核可 spec」。**卡面文字的修改不是執行者的權限**，故本節只提出論證與建議文字。

### 11.1 環是真的，而且可以機械地證明

```
R1-01 要求「真實失敗 PR 被阻擋的證據」
   └─ 需要 ruleset 已套用
        └─ 需要 main 已含 ci.yml（§7.0，這正是 R2-003 指出的同一件事）
             └─ 需要本卡已合併
                  └─ 需要查核 APPROVE
                       └─ 需要 R1-01 閉環  ←─ 回到起點
```

這不是修辭。每一段箭頭都對應本檔或本卡 Log 裡的一個實測事實：
`main` 無 `.github`（§7.0）、required 對不存在的 check 判 pending（§7.0）、
`rulesets` 為 `[]`（§0）、以及 `AI_WORKFLOW.md:53` 的「執行者不得 merge 自己的變更」。

**一張驗收條件只能在它自己被合併之後才可能滿足的卡，在構造上不可滿足。**
這一點與「該不該有 merge gate」無關——就算所有人都同意應該有，這張卡也走不到那裡。

### 11.2 為什麼答案不是「執行者去把 ruleset 套上」

三條，任一條單獨成立即可：

1. **權限**：套 ruleset 是 repo 設定變更。執行者被明確紅線禁止改 repo settings。
2. **資源宣告**：本卡的宣告是 `file:.github/workflows/ci.yml` 與 `file:docs/DEV_AIWF_MINIMAL_CI1.md`。
   repo setting 不是檔案，**不可能被宣告進任何寫入集**——它不在資源模型的值域裡。
3. **順序**：即使前兩條不存在，§7.0 證明現在套用會鎖死整個 repo。
   **`R2-003` 與 `R2-001` 的 disposition 在這一點上互相衝突**：前者要求「先合併本卡再套」，
   後者要求「本卡交付內含套用並附阻擋證據」。兩者不能同時滿足。

### 11.3 為什麼答案也不是「就這樣驗收，細節以後說」

ROADMAP §4 寫得很明白：`core_pain_resolved: no` → **退回**，本政策不適用。
查核者兩輪都判 `no`，所以不能拿 §4 直接把這張卡放行。

**但 §4 沒有回答的是：`no` 是對「核心痛點」本身的判定，還是對卡面把核心痛點寫成什麼的判定？**
本卡的兩段文字是分開的：

- **核心痛點**（卡面 `## 核心痛點`）：「ai-workflow 完全沒有 CI——repo 根無 `.github/` 目錄……
  沒有 CI 就沒有任何東西站在合併與 main 之間。」→ **這一段已經被消除。**
- **服務的原始目標**（卡面路由區）：「讓『合併後 main 是綠的』成為**機械保證**」
  → **這一段沒有被消除，也不可能由本卡消除**（§11.2）。

`R2-001` 逐字引的是後者（「卡面原始目標」）。**所以兩輪的 `no` 其實判的是第二段。**
本卡主張這是**卡面把兩件事寫成一句**造成的，不是交付缺了什麼。

### 11.4 建議的卡面文字

**以下是建議，不是既成事實。** 本輪執行者未執行任何 `wfcli amend`，卡面在需求方核可前不變。

#### 建議一：`核心痛點` 段末追加一句，界定它到哪裡為止

> **本卡的射程止於「證據」。** CI 產生「合併結果是紅是綠」這個機械事實，
> 並讓它出現在 PR 與 commit 上。**把該事實接上 merge 按鈕是 repo 設定變更**，
> 不是檔案，不可能落入任何寫入集，且依 §7.0 必須在本卡合併之後才能執行——
> 故它是需求方的後續動作，登記為獨立卡，不由本卡背負。

#### 建議二：`服務的原始目標` 一行拆成兩行

> 服務的原始目標（本卡）：讓「合併結果有沒有跑過測試」成為**機械產生的證據**，
> 而不是協調者記得手動驗。
>
> 服務的原始目標（後續卡）：讓該證據成為**機械閘門**——套用 required status check。
> 承接者：需求方。前提：本卡已合併且 `main` 的 `tests` 為綠（§7.0）。

#### 建議三：`驗收條件` 第 2 條改寫

現行逐字是「須以真實紅色案例自證有效……只證明『CI 會跑』不算——那是裝飾」。
**這句話的精神必須保留**——它是對的，而且是本卡最好的一條。但「不是裝飾」的證明有兩種，
現行文字把它們混在一起了：

> - [ ] 須以真實紅色案例自證**判定有效**：取 `5d22a7f` 為輸入證明判紅；
>   並取一個「分支頭綠、合併結果紅」的真實 PR，證明 `pull_request` 事件測的是合併結果。
>   **只證明「CI 會跑」不算——那是裝飾。**
> - [ ] 須明列本 CI 在**閘門套用前**不能做什麼，且交付文件不得有任何一處
>   把「會產生紅叉」寫成「會擋下合併」。（`ROADMAP.md` §2）

#### 建議四：`驗證` 段追加一條，把閘門那一格明確登記為未完成而非已完成

> - [ ] 閘門本身（required status check）**不在本卡射程**。本卡須交付：確切的設定內容、
>   套用順序與其前提、套用後的驗證程序、以及回退指令。
>   **套用與其阻擋證據由需求方在本卡合併後執行**，成果登記於後續卡，不回填本卡。

### 11.5 如果需求方不接受縮射程

那麼唯一自洽的路是**把本卡拆成兩張**，而不是讓它繼續帶著一個不可滿足的條件走輪次：

- `#48` 保留現交付（workflow ＋ 設計文件），驗收條件依 §11.4 修窄，**可以現在結案**。
- 新卡承接閘門：其第一步就是 §7.0 的四步，`R1-01` 的「真實失敗 PR 被阻擋」成為**它的**驗收條件，
  而 `#61` 與三個 probe 分支移交給它（§9 的清理時點隨之改為該卡結案）。

**兩者的差別只在記帳，不在工作量**——同樣的事還是需求方去做。差別是後者讓「閘門未套用」
這件事有一個帶編號的位置，而不是活在一張已結案的卡的註腳裡。
`ROADMAP.md` §2 現在寫著「`#48` 是唯一會真的擋人的東西」；**在 ruleset 套用之前這句話是假的**，
而本卡無法讓它變真。⚠️ **這一點需要需求方知道**：`#48` 合併不等於 §2 的前提成立，
後面所有「靠 `#48` 才有牙齒」的偵測器卡，牙齒要等的是 §7.0 第 3 步，不是本卡的 merge。

### 11.6 本輪證明不了的事（逐條）

| 事項 | 狀態 | 為什麼 |
|---|---|---|
| 紅色 PR 會被閘門擋下（`R1-01`） | **未閉環** | `rulesets` 仍為 `[]`（本輪複驗）；`#61` 仍 `UNSTABLE`／`MERGEABLE`。需 §7.0 全四步，皆為需求方動作 |
| 不合併地關閉 `#61`（`R1-02` 後半） | **未執行，且刻意不執行** | §7.4 與 §9 都以 `#61` 為套用後的現成失敗案例；本輪亦被明令不得關閉它。**merge ref 的取證本身已閉環**（run `31592615503`，`event=pull_request`，`conclusion=failure`）——未閉環的只有清理動作，且它與 `R1-01` 的驗證程序直接衝突 |
| 只有 base 含 `ci.yml` 時 PR 是否產生 `tests` | **未實測** | 見 §7.0；`#61` 的 head 自己含 `.github`，故現有實跑不能當證據 |
| `C.UTF-8` 在 `ubuntu-latest` 上存在且不靜默退回 | ✅ **已實測** | run `31612860735`，見 §10.0／§10.1 |
| 「所有 locale 敏感形狀都已被排除」 | **不宣稱，且不可能宣稱** | 本卡只把基準釘住，一個蟲都沒有找。PM 自己也只排除了「`$var` 緊接全形標點」一種形狀。**釘 UTF-8 不等於已預防**（`ROADMAP.md` §2） |
| 釘 UTF-8 之後不會有既有東西變紅 | **只對今天的三個步驟成立** | run `31612860735` 全綠，但那三個步驟本來就對 locale 不敏感（§10 上表）。日後接進來的東西沒有這個保證——那正是釘住的目的 |
| required check 是否對 commit SHA 判定（§7.3 路徑 2） | **未實測** | 需先有 ruleset。前一輪已標為待驗證的預測，本輪未改變 |
| `main` 上既有 ruff 違規的筆數 | **未查證** | §1.5 沿用派工包數字，本卡未安裝 ruff |
