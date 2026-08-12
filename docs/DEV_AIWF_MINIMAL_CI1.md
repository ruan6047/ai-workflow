# DEV-AIWF-MINIMAL-CI1 — ai-workflow 最小 CI 的裁定與自證

> 對應卡：[#48](https://github.com/ruan6047/ai-workflow/issues/48)。實作＝
> [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)（本 repo 第一支 workflow）。
> 本檔記錄「為什麼是這個形狀」「它擋得住什麼」「它擋不住什麼」，以及**哪些話是強制、哪些只是約定**。

## 0. 先講最重要的一句

**本 CI 今天不擋任何 merge。**

`gh api repos/ruan6047/ai-workflow/rulesets` 於 2026-08-12 回 `[]`——本 repo **沒有任何 ruleset**，
因此也沒有 required status check。GitHub 上「merge 按鈕是否可按」與本 workflow 的紅綠**沒有連線**。
本卡的寫入集只有 `ci.yml` 與本檔，設定 ruleset 是 repo 設定變更，不在射程內。

所以本檔往下所有措辭，一律照這條分：

- **強制**＝有機械執行者，且執行者在版控裡指得出檔與行。
- **約定**＝靠人記得。canonical §2.2 已經說過靠人記得的檢查遲早會漏，本檔不假裝相反。

本 CI 目前提供的是**強制產生的證據**（紅綠一定會算出來、一定留在 run 紀錄裡、不能被忘記跑），
而不是**強制執行的閘門**。這兩件事的差距就是 §7 那條待辦。

## 1. 裁定：最小形狀

跑什麼、何時跑、失敗時發生什麼：

- **跑什麼**：只有一個 job（`cli tests`）。`uv lock --check` 確認鎖檔沒過期
  （`ci.yml:63`），然後 `uv run --frozen pytest -q` 跑 `cli/` 底下全部測試（`ci.yml:68`）。
  沒有 lint、沒有型別檢查、沒有 matrix——本 repo 沒有 ruff／mypy 設定，加了等於憑空發明標準。
- **何時跑**：`push`（不過濾分支）與 `pull_request`，兩者都留（`ci.yml:12-13`）。
- **失敗時**：job 以 exit code 1 結束，run 標記為 failure，PR 頁與 commit 上出現紅叉。
  **沒有東西被鎖住**（見 §0）。

### 1.1 為什麼 `push` 與 `pull_request` 兩支都要

這是本卡唯一真正的設計決定，其餘都是細節。

兩個事件取出的**不是同一棵樹**：

- `push` 取的是**分支頭**。這是執行者自己的回饋，也是 main 被推入紅碼時的事後偵測。
- `pull_request` 取的是 `refs/pull/N/merge`，也就是 head 併入當時 base 之後的**合併結果**。

2026-08-12 的事故整個活在這個差距裡。同一批 SHA 的實測（本機，`cli/` 目錄，`uv run --frozen pytest -q`）：

| 受測的樹 | 結果 |
|---|---|
| base `3e47838`（PR #27 最後一次 synchronize 時的 main） | 437 passed，綠 |
| head `4353c18`（WF-CLEANUP-GUARD1 分支頭） | 388 passed，綠 |
| **merge(base, head)**——`pull_request` 取的正是這棵 | **519 passed, 14 errors，紅** |
| `5d22a7f`（實際合併後的 main） | **644 passed, 14 errors，紅** |

基線綠、分支頭綠、只有合併結果紅。PM 當時做的兩件事——`git merge-tree` 與「在分支自己的基線上跑測試」——
恰好各自對應上表的前兩列，**兩列都是綠的，而且都是真的**。`git merge-tree` 是文字比對，
四個能力旗標從必填變成必填不會產生文字衝突，所以它也不會叫。

只有第三列會叫，而 `pull_request` 事件天生就取第三列。

### 1.2 時序：CI 若當時存在，會在合併前兩小時就叫

| 時間（+08:00） | 事件 |
|---|---|
| 06:45:26 | `a5d4770` 併入 main —— 四個能力旗標改為必填 |
| 11:29:02 | PR #27 最後一次 synchronize（head `4353c18`，當時 main tip `3e47838`） |
| 13:25:11 | PR #27 合併，main 轉紅 |

11:29 的 synchronize 會觸發 `pull_request` run，取出的 merge ref 同時含有陳舊 fixture 與必填旗標——
即上表第三列，**519 passed, 14 errors**。距離 13:25 的合併還有近兩小時。

這一格是**用真實 SHA 在本機重建合併結果後實跑出來的**（`git worktree add --detach 3e47838` →
`git merge 4353c186` → pytest），不是推論。

## 2. 自證：兩個真實 CI run

卡面要求「不得以本機模擬代替」。以下兩筆都是 GitHub Actions 的實際執行輸出。

### 2.1 紅：對 `5d22a7f` 的 `cli/` 樹判紅

不需要另外造一個「5d22a7f + ci.yml」的分支——本卡的分支**就是**。分支自 `5d22a7f` 切出且
本卡不動 `cli/` 一個字元，因此 `cli/` 子樹逐位元組相同：

```
git rev-parse 549ab8f:cli  → 2379393d99f78dfe4332967b857636a4b8ab8b56
git rev-parse 5d22a7f:cli  → 2379393d99f78dfe4332967b857636a4b8ab8b56
```

CI run 自己也把這棵樹印進 log（`ci.yml:41-48` 的「標示實際受測的樹」步驟，正是為了讓
run 能自證測的是哪棵樹）：

- run：<https://github.com/ruan6047/ai-workflow/actions/runs/31568427729>
- log 節錄：
  ```
  event          = push
  checked-out    = 549ab8f63583f2894d1999c7a4a14db2e52e2322
  cli/ tree      = 2379393d99f78dfe4332967b857636a4b8ab8b56
  ...
  wfcli open: error: the following arguments are required: --exec-capability,
    --exec-capability-reason, --review-capability, --review-capability-reason
  644 passed, 14 errors in 17.82s
  ##[error]Process completed with exit code 1.
  ```
- 結論：**failure**。`644 passed, 14 errors` 與本機對 `5d22a7f` 的實跑數字一致。

CI 的 log 甚至直接指名了真因（四個必填旗標），不必人去逆向。

### 2.2 綠：同一支 workflow 對修好的樹判綠

`DEV-MAIN-RED-CAPABILITY-FLAGS1`（#47）的分支在本卡執行時尚未推上 origin
（`git ls-remote --heads origin` 查無），故依派工包指示自行構造等價修法：

- 分支：`claude/DEV-AIWF-MINIMAL-CI1-green-control`，SHA `cd86b1d`
- 與紅色那筆的**唯一差異**是 `cli/tests/test_release_cleanup.py` 的 fixture 補值：
  `_open_argv` 補 `--exec-capability`／`--exec-capability-reason`／`--review-capability`／
  `--review-capability-reason`，`assign` 補 `--actual-capability`。workflow、runner、
  uv 版本、Python 版本全部相同。
- run：<https://github.com/ruan6047/ai-workflow/actions/runs/31568601428>
- log 節錄：
  ```
  checked-out    = cd86b1d4d65a2cea4f72bdef3d3d1fa49b67186b
  cli/ tree      = 5c2fae557978aa80e0c91c9d898a8228203ef7d0
  658 passed in 17.91s
  ```
- 結論：**success**。

順帶一個本身就說明問題的觀察：第一層（open 的四個旗標）補完後，`assign` 的
`--actual-capability` 才顯露出來。**第二層是第一層修好之後 CI 才看得見的**——
只跑一次分支頭測試的人不會遇到第二層。

### 2.3 這兩筆證明了什麼、沒證明什麼

- **證明了**：同一支 workflow 對紅樹判紅、對綠樹判綠。它會分辨，不是恆綠的裝飾。
- **沒證明**：`pull_request` 路徑在本 repo 的實跑。本卡射程內不能開 PR（開 PR 是需求方的動作；
  本 repo 的 PR 全部由 `ruan6047` 開），因此 `on: pull_request`（`ci.yml:13`）目前**只有
  GitHub 文件保證、沒有本 repo 的實跑證據**。這是本檔最弱的一格，不粉飾。

  可落地的補強（給查核者的**可證偽預測**）：本卡自己的 PR 開出來時，因為 main 現在是紅的
  （#47 未修），merge ref 必然含那 14 個 error，**該 PR 的第一個 `pull_request` run 必為
  failure**。若它是綠的，本檔 §1.1 的整套推理就是錯的，請據此退回。

## 3. 擋不住的事故（至少三種）與承接者

寫「擋不住」比寫「會擋下」重要，因為前者才是別人需要接手的部分。

**一、被合併的紅碼本身。**
CI 產生紅叉，但沒有 required status check（§0），所以**紅叉不阻止任何人按 merge**。
2026-08-12 那個事故若今天重演，CI 會在 11:29 叫，13:25 仍然可以照併。
→ 承接者：**需求方**（唯一有權改 repo 設定的人）。動作見 §7。在那之前，
「不在紅色 run 上 merge」是**約定**，沒有機械執行者。

**二、CI run 本身的陳舊（stale-green）。**
`pull_request` 只在 PR 建立與 head 變動（synchronize）時重跑。若 PR 最後一次 synchronize
之後 base 才前進，那個綠勾指的是**舊的 base**，而合併用的是新的。08-12 若時序顛倒
（PR 先 synchronize、旗標後合併），CI 會是綠的而事故照樣發生。
→ 承接者：**平台設定**。GitHub 的「require branches to be up to date before merging」
（ruleset 的 `strict_required_status_checks_policy`）就是為這個而生，同樣屬 §7。
在那之前，「合併前重跑一次」是**約定**。

**三、測試沒覆蓋到的語意衝突。**
本 CI 的判準完全等於 `cli/tests/` 的覆蓋範圍。08-12 之所以擋得住，是因為那次的語意衝突
剛好打在 fixture 上、剛好會爆。同樣是陳舊基線，若衝突落在無測試覆蓋的路徑（例如兩張卡各自
修改 `AI_WORKFLOW.md` 的相鄰段落造成規則互相矛盾、或改到 `templates/` 的文件契約），
CI 全綠、事故照發。
→ 承接者：**獨立查核者**（canonical §5）。CI 不是查核的替代品，它只是把「有沒有跑過測試」
這一格從人腦搬到機器。

**四、資源互斥與 control plane 的一致性。**
兩張卡宣告了相交的寫入集、或狀態面與 event log 對不上——這些都不是 pytest 看得到的東西。
→ 承接者：`wfcli doctor` 與 WF-RESOURCE-WRITESET1／WF-RESOURCE-BLOCK-ANCHOR1 那一族的守衛。

**五、CI 設定自身的退化。**
有人把 `ci.yml` 改成 `continue-on-error`、加上 `paths-ignore` 讓測試被跳過、或把釘住的
action SHA 換成可重指的 tag——CI 會照樣顯示綠勾。**CI 監督不了自己。**
（`ci.yml:15-17` 刻意不加 `paths` 過濾並寫明理由，但那是註解，不是強制。）
→ 承接者：**查核者**對 `.github/` 變更的人工審查。這是**約定**。

## 4. 對既有 PR 實務（B1／B2／T0–T1）的影響

canonical §0 允許 B1／T0–T1 直推 main，§2.2 並且明講「required status checks 不是預設要求：
對 §0 允許的 B1／T0–T1 直推 main 工作流，它會鎖死既有路徑」。

本 CI 與該分類**不衝突**，理由是三段：

1. **本 CI 不是 required status check**（§0）。直推 main 的 B1／T0–T1 照樣推得進去，
   只是事後多一個 run。紅了不阻擋、綠了不加速。
2. **刻意不做 `paths` 過濾**（`ci.yml:15-17`）。看似浪費——改一行 TASKS.md 也跑一次 pytest——
   但代價是四十秒，而 `paths` 過濾在「日後被設為 required」時會讓被跳過的 PR 永遠停在 pending
   而無法合併。這個坑不划算換那四十秒。
3. **在飛卡不會卡死**。目前有 15 張以上的在飛卡（`gh issue list`），其分支多半基於
   本 workflow 之前的 SHA。它們的分支上沒有 `ci.yml`，`push` 事件不會觸發任何 run；
   本卡併入 main 後，它們的 `pull_request` merge ref 才開始含 `ci.yml`。屆時只要 main 是綠的，
   它們的 run 就反映自己的真實狀態——這正是我們要的。**沒有任何在飛卡因為本卡而被鎖住**，
   因為沒有任何東西被設為必要條件。

若日後要把它升為 required（§7），**才會**與 B1／T0–T1 直推路徑衝突，屆時 §2.2 的取捨要重新裁，
不在本卡射程。

## 5. 環境重現性：落差清單

CI 環境與本機的已知差異，逐條列出而非略過：

- **`gh` 認證：無落差。** `cli/tests/` 全部用 `FakeGhRunner`（純記憶體，不打網路）與
  `sandbox_repo` fixture（`tmp_path` 底下一次性 `git init`）。全套測試不需要 `GH_TOKEN`、
  不碰真實 repo。這是原作者刻意設計的（見 `cli/tests/fake_gh.py` 檔頭），本卡只是確認它成立：
  CI 的 644／658 passed 與本機逐數字吻合，就是這件事的證據。
  **對應地，`cli/tests/` 不驗證真實 `gh` 互動的正確性**——那部分由各卡的 live smoke run 承接，
  CI 覆蓋不到，屬 §3 第三類。
- **Python patch 版本有落差。** 本機 3.12.13（uv 自管），CI 是 ubuntu-latest 的
  `/usr/bin/python3.12`＝3.12.3。minor 相同、patch 不同。目前無影響（測試不碰 patch 級行為），
  但這是**真實落差**。
- **本 repo 沒有 `.python-version`。** 本機那個 3.12 是 uv 當下的偶然解析結果——換一台機器、
  換一個 uv 預設，本機就可能跑在 3.13 而 CI 仍是 3.12。CI 側已釘死（`ci.yml:57`），
  **本機側沒有釘**。補一個 `.python-version` 是正解，但該檔不在本卡寫入集，列為 §7 待辦。
- **uv 版本已釘 `0.11.19`**（`ci.yml:56`）＝執行本卡時的本機版本。升版是刻意動作，不是自動漂移。
- **鎖檔以 `uv lock --check` 把關**（`ci.yml:63`），`pyproject.toml` 與 `uv.lock` 不同步即紅。
  `uv run --frozen`（`ci.yml:68`）完全照鎖檔安裝，不在 CI 裡重解相依。
- **作業系統有落差且不打算消除。** 本機 macOS／arm64，CI Linux／x86-64。測試不含原生相依，
  但這代表「只在 macOS 出現的問題」CI 看不到，反之亦然。

## 6. 第一次觸發：會發生什麼、紅了怎麼辦

本 repo 至今沒有任何 workflow（`gh api .../actions/workflows` 回 `total_count: 0`），
本卡是第一支。已知行為：

- **已經觸發過了。** 本卡的分支推上去時就跑了第一個 run，而且**如預期是紅的**（§2.1）——
  那個紅正是交付物的一部分，不是意外。
- **本卡併入 main 之後**，main 上會出現第一個 push run。**只要 #47 還沒修，它必定是紅的**，
  因為 main 現在就是紅的。這不是 CI 壞掉，是 CI 第一次把既有事實顯示出來。
- **紅不會卡死 main。** 沒有 ruleset、沒有 required check（§0），紅叉不阻止 push、
  不阻止 merge、不阻止任何既有路徑。**CI 本身不可能讓 main 卡死**，這是目前唯一一個
  「還沒設閘門」帶來的好處。
- **建議的合併次序**：先 #47（修紅）、再 #48（本卡）。這樣 main 上的第一個 run 就是綠的，
  不用向後人解釋一個開局即紅的歷史。這是**建議**，不是強制——反過來併也不會壞事，只是難看。
- **若 CI 因為它自己而紅**（YAML 語法、action 版本、runner 環境），處置是直接 revert
  `ci.yml` 這一個檔：本卡的寫入集刻意只有兩個新檔，**回退不牽動任何既有程式碼**。
- **成本**：public repo，GitHub Actions 免費額度內。單次 run 約 40 秒。

## 7. 沒有做、需要需求方裁決的

本卡刻意停在這裡，因為以下每一項都超出寫入集：

1. **把 `cli tests` 設為 required status check。** 這是「CI 從產生證據升級為執行閘門」
   的唯一一步，也是 §3 第一類事故的解法。與 canonical §2.2 對 B1／T0–T1 直推路徑的保留
   有真實張力，須需求方裁。
2. **一併開啟 strict（require branches to be up to date）。** §3 第二類（stale-green）的解法。
   代價是每次 base 前進都要重跑，在飛卡多時會很吵。
3. **建立 ruleset 本身。** 目前 `rulesets` 是空的——意即 canonical §2.2 要求的
   `deletion` ＋ `non_fast_forward` 歷史防線**在本 repo 也還沒實作**。這是本卡查證時
   順帶發現的範圍外事實，照派工包第 1 條寫在報告裡，不自行處置。
4. **補 `.python-version`**（§5）。
5. **刪除 `claude/DEV-AIWF-MINIMAL-CI1-green-control`。** 它是 §2.2 的對照組，
   commit 標題已寫 DO NOT MERGE。證據連結指向它的 run，故**結案前不要刪**，結案時刪。

## 8. 本檔哪些話沒有機械執行者

自我適用，逐條列：

- 「不在紅色 run 上 merge」——**約定**。沒有 required check，執行者是人。
- 「合併前重跑一次 CI」——**約定**。沒有 strict 模式，執行者是人。
- 「不把 `ci.yml` 改成 `continue-on-error` 或加 `paths` 過濾」——**約定**。`ci.yml:15-17`
  只是註解，沒有守衛檢查它。
- 「綠色控制組分支不得併入 main」——**約定**。靠 commit 標題與本節，沒有機械阻擋。
- 「先併 #47 再併 #48」——**建議**，非強制。

有機械執行者的只有這些，逐一指得出檔與行：

| 宣稱 | 執行者 |
|---|---|
| 每一次 push 與每一個 PR 都會跑全套 `cli/` 測試，不會被忘記 | `.github/workflows/ci.yml:12-13` |
| PR 上測的是合併結果而非分支頭 | `.github/workflows/ci.yml:13`（`pull_request` 事件語意）＋ `ci.yml:41-48` 把受測樹印進 log 供事後對帳 |
| 測試失敗會讓 run 判紅 | `.github/workflows/ci.yml:68`（pytest exit code 傳導） |
| 鎖檔與 `pyproject.toml` 不同步會判紅 | `.github/workflows/ci.yml:63` |
| CI 不會偷偷換 action 或 uv／Python 版本 | `.github/workflows/ci.yml:36`、`52`（釘 commit SHA）、`56`、`57` |
| 卡住的 job 不會無限佔用額度 | `.github/workflows/ci.yml:32`（`timeout-minutes: 15`） |
