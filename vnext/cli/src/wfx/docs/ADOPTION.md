# 採用指南（ADOPTION）

本檔隨 wheel 出貨（`wfx/docs/ADOPTION.md`），**⛔ 不是框架規則**：`brief` ⛔ 不載入它，
`rules/core/` 也⛔ 不因它變長。規則本體只住 `wfx/rules/`。

三個名稱各有唯一居所：distribution `ai-workflow-vnext`／import package `wfx`／console script `wfx`。
版本值的唯一居所是 `pyproject.toml` 的 `version`，執行期走
`importlib.metadata.version("ai-workflow-vnext")`；取不到就是 `unknown`，⛔ 無第二個版本來源。

**CLI 對採用者的專案永遠是唯讀的**：⛔ 不建立、⛔ 不修改、⛔ 不刪除你的檔案、`~/.wf/` 或
GitHub Project schema，⛔ 不登入、⛔ 不保存憑證、⛔ 不安裝工具、⛔ 不呼叫 AI。
採用清單只告訴你缺什麼、要貼什麼——**套用一律由你自己執行**。

## 1 · 安裝

```
WFX_VENV="$HOME/.venvs/wfx"                                  # 獨立 venv 位置，可自選
WFX_WHEEL="ai_workflow_vnext-<版本>-py3-none-any.whl"         # 換成實際 wheel 檔路徑
python3.14 -m venv "$WFX_VENV"
"$WFX_VENV/bin/python" -m pip install "$WFX_WHEEL"
test -x "$WFX_VENV/bin/wfx" && echo "OK: $WFX_VENV/bin/wfx" || echo "MISSING: $WFX_VENV/bin/wfx"
"$WFX_VENV/bin/wfx"                                          # 以絕對路徑啟動，不依賴 PATH
```

- 需要 Python **≥ 3.14**（`requires-python`）。
- 執行期⛔ 無 Python 相依（`pip show ai-workflow-vnext` 的 `Requires:` 為空）；
  `git` 與 `gh` 是**外部指令**，各自另行安裝。
- 安裝後⛔ 不需要本框架的 checkout、也⛔ 不需要 `PYTHONPATH`：規則樹（19 份 markdown）
  隨 wheel 走，住在 `wfx/rules/`，⛔ 不複製進你的專案。
- 無參數執行 `wfx` 會印用法並以 **rc 2** 結束（用法錯）。
- `wfx: command not found` 先看上面的檢查：
  - 印 `OK`＝**只是 PATH 未設定**，⛔ 不是安裝缺陷：用 `"$WFX_VENV/bin/wfx"`，或
    `source "$WFX_VENV/bin/activate"` 後再打 `wfx`。
  - 印 `MISSING`＝**console script 真缺失**：以 `"$WFX_VENV/bin/python" -m pip show -f ai-workflow-vnext`
    確認有無安裝紀錄與 `bin/wfx`，再 `--force-reinstall` 該 wheel。`python -m wfx` 能跑⛔ 不證明
    console script 裝好，安裝驗證只看 `$WFX_VENV/bin/wfx`。

## 2 · 版本確認

```
wfx --project-root <你的專案> facts --task <id>    # 第 ⑦ 節
```

```
## 7 · 規則來源與套件版本
rules source: package｜override
package version: <版本>｜unknown
```

- `package`＝讀套件內的規則樹；給了 `--rules-root <p>` 就是 `override`。
- `unknown`＝這個直譯器的 `sys.path` 上⛔ 無 `ai-workflow-vnext` 的 distribution metadata
  （典型情況：以原始碼樹 `PYTHONPATH=… python -m wfx` 直跑）。**這是事實，⛔ 不是錯誤。**
  **判準是 metadata 在不在 `sys.path` 上，不是「有沒有 pip install」**：`build` 會在
  `src/` 留下 `ai_workflow_vnext.egg-info/`，那份殘留也算 metadata，此時同一道原始碼樹直跑
  會報出 **egg-info 裡的版本**而非 `unknown`。要重現 `unknown`，`sys.path` 上只放 `wfx/`
  套件目錄本身（見第 10 節 E8）。
- 本節⛔ 不印任何路徑：印了會讓「同一輸入兩次執行逐字相同」隨機器而破。

## 3 · 採用清單：怎麼讀

```
wfx --project-root <你的專案> facts --adopt [--rules-root <p>]
```

`--adopt` 與 `--task`／`--sha` **互斥**，兩者皆缺＝用法錯（rc 2）。它⛔ 不需要任務、
⛔ 不需要 git 工作樹、⛔ 不需要 `.wf/`、⛔ 不需要 Project——**空的既存目錄照樣輸出完整清單**。

固定七節、固定順序：執行環境／框架套件／`.wf/` 骨架／repository 身分／Project schema／
下一步／摘要。輸出⛔ 無時間戳、⛔ 無絕對路徑；**同一狀態重跑逐字相同**。

逐項五類：

| 類別 | 意思 |
|---|---|
| 已完成 | 目標存在且形狀合法 |
| 缺少 | 目標不存在 |
| 格式錯誤 | 存在但形狀不合法（設定鍵、欄位型別、選項字面、狀態欄有第二個居所；路徑上不是該有的型別、或文件讀不出 UTF-8 文字也算） |
| 環境阻塞 | 外部工具給出客觀錯誤；逐字附上**工具名、rc 與 stderr 首行**（訊息裡的 `--project-root` 絕對路徑換成 `<project-root>`） |
| 無法確認 | 本清單內的上游那一項還沒滿足，所以這一項還判不了 |

**rc ⛔ 不表達就緒與否**：清單產得出來一律 **rc 0**（不論項目狀態），連清單都產不出來
（`--project-root` 不是既存目錄、規則樹取不到）才 **rc 1**，用法錯是 **rc 2**。
要機械判斷就緒與否，讀第 7 節的計數行，⛔ 不要讀 rc。

判準邊界：文件類只判「存在且非空」，⛔ 不判內容品質；欄位型別依 `rules/core/github.md` §2，
SingleSelect 的選項依 `rules/core/values.md` 逐字比對；內建 `Status` 與自訂 `狀態`
**同時存在**＝狀態有第二個居所＝格式錯誤。

**「實際 schema 無法確認」⛔ 不等於「預期規格未知」**：Project 還讀不到時，第 5／6 節照樣印出
七個概念的預期欄型、SingleSelect 值域與 `Status` 唯一居所——那三項都來自規則樹，與能不能讀到
Project 無關。同理，`.git` 已存在而 git 回非 0 是**外部工具的客觀錯誤**（環境阻塞），
清單⛔ 不推論成「工作樹缺少」、⛔ 不建議 `git init`。

## 4 · 人工套用

第 6 節印的是**可直接貼的骨架與指令**，CLI 只印、零寫入。典型順序：

```
mkdir -p .wf
cat > .wf/config.json <<'JSON'
{
  "rules": null,
  "remote": null,
  "project": {"owner": "<owner>", "number": <Project 編號>}
}
JSON
cat > .wf/model-policy.md <<'MD2'
# 專案層政策

具體模型名稱、額度與帳號狀態⛔ 不住這裡（core/boundaries.md §2／§3）。
MD2
git init && git remote add origin git@github.com:<owner>/<name>.git
gh auth login
```

Project 的七個核心概念欄位（型別、選項與唯一居所逐字見清單第 5／6 節，Project 還讀不到時
也照樣印）**由你在平台上建立**，
或自行以 `gh project field-create` 操作（旗標形狀見 `gh project field-create --help`）。
**CLI ⛔ 不代建欄位、⛔ 不改 Project schema，連「只建缺的那一個」都不做。**

套用完重跑同一道指令，逐項應轉成「已完成」。

## 5 · 升級

```
python -m pip install --force-reinstall ai_workflow_vnext-<新版本>-py3-none-any.whl
```

- 升級只動 `site-packages`。⛔ 無版本比較、⛔ 無相容矩陣、⛔ 無自動遷移、⛔ 無 legacy 讀取路徑：
  這個 CLI 對「上一版留下什麼」⛔ 不做任何假設，也⛔ 不改寫你的資料。
- 要確認實際生效的版本，看第 2 節的 `package version`。

## 6 · 「`.wf/` 不變」驗證

升級或重跑前後各取一次快照，逐字比對：

```
find <你的專案> -type f | sort | xargs shasum -a 256 > /tmp/before.txt
ls -la ~/.wf
gh project field-list <number> --owner <owner> --format json > /tmp/before-schema.json
# …執行 wfx 或升級…
find <你的專案> -type f | sort | xargs shasum -a 256 > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt          # 應⛔ 無差異
```

`~/.wf/` **不存在**時 `ls` 的 not-found 訊息前後相同即成立——⛔ 不要為了讓比對好看而建立它。

## 7 · 回退

```
python -m pip install --force-reinstall ai_workflow_vnext-<舊版本>-py3-none-any.whl
```

回退只換套件。**你的 `.wf/`、repository 與 Project 都沒有被本 CLI 改過**，因此⛔ 無資料回滾步驟、
⛔ 無 schema 還原步驟。唯一例外：已啟用模組的專案，要回退到不含該模組的版本前，**先**從 `modules` 移除該模組
（清單變空時刪鍵或設 `null`，⛔ 不留 `[]`），否則 `brief` 會報 `LayerMissing`（第 11 節）。

## 8 · 移除

```
python -m pip uninstall ai-workflow-vnext
```

移除只刪套件與規則樹副本。你的 `.wf/`、Issue、Project 與 repository **原樣保留**——
它們從來不是本 CLI 建的。要一併清掉專案層設定，自行 `rm -rf .wf`（CLI ⛔ 不代刪）。

## 9 · 重現條件

任何人要重現一份輸出，需要而且只需要：

1. **exact SHA** 的乾淨 checkout 或同一顆 wheel（`pip install` 到全新 venv）；
2. 同一個 `--project-root`（其 `.wf/` 內容相同）；
3. 同一份規則樹來源（`package`，或同一個 `--rules-root` checkout）；
4. `facts --task`／`brief` 另需**同一次遠端讀取**——遠端資料變動導致輸出不同是正確行為，
   ⛔ 不得為了讓比對好看而快取或凍結即時遠端資料。

`facts --adopt` ⛔ 不讀任何 Issue、⛔ 不讀遠端 repository：它只看本機環境、`.wf/`、
remote 身分與（設了 `project` 時的）Project schema。

## 10 · 受控端到端驗證（可重現步驟）

要自己把「乾淨環境能裝、清單零寫入、升級不動資料」重跑一遍，照下面的順序。全程
**⛔ 無非 dry-run 的遠端寫入**；會連網的只有 `facts --task`／`brief`／`write --dry-run`
的**唯讀查詢**。先設三個變數（`PY` 換成你的 ≥3.14 直譯器）：

```
PY=<python3.14 的絕對路徑>
PROJ=$(mktemp -d)                 # 空的採用者專案
WHL=/tmp/wfx-dist/ai_workflow_vnext-0.1.0-py3-none-any.whl
```

- **E1 離線出輪子**。`uv build --offline --wheel --python "$PY" --out-dir /tmp/wfx-dist <此套件目錄>`
  （或任何 PEP 517 前端配 `setuptools`；`python -m build --no-isolation` 需先把
  `setuptools` 裝進該直譯器）。輪子⛔ 不進 repo。
- **E2 乾淨 venv 安裝**。`$PY -m venv /tmp/wfx-venv` →
  `/tmp/wfx-venv/bin/python -m pip install --no-index --no-cache-dir "$WHL"`。
  無參數跑 `wfx` 應印用法並 **rc 2**（console script 會把 `main()` 的回傳值當 exit code）。
- **E3 輪子內容**。`unzip -Z1 "$WHL"`：`wfx/rules/**` 的 `.md` 應為 **19 份**、
  `wfx/docs/ADOPTION.md` 在，且⛔ 無 `.wf/`、⛔ 無任務／模型資料、⛔ 無憑證。
  `pip show -f ai-workflow-vnext` 的 `Requires:` 須為**空**。
- **E4 空目錄清單＋零寫入**。`find "$PROJ" | sort` 前後比對，中間跑兩次
  `wfx --project-root "$PROJ" facts --adopt`：rc 0、兩次輸出 `diff` 逐字相同、`find` 無差異。
  第 ①②節（直譯器、git／gh、套件）本來就會是「已完成」——**那是環境事實，不是專案狀態**。
- **E5 套用後收斂**。照第 4 節建 `.wf/` 與 remote 後重跑：全項應轉「已完成」，
  且 `shasum` 快照顯示 CLI 仍然零寫入。
- **E6 未登入負控**。`GH_CONFIG_DIR=$(mktemp -d) GH_TOKEN= GITHUB_TOKEN= wfx … facts --adopt`：
  「gh 已登入」應為**環境阻塞**並附 `gh auth status｜rc=1｜<stderr 首行>`，rc 仍 **0**。
  **⛔ 不要跑 `gh auth logout`**——用完刪掉那個暫存 `GH_CONFIG_DIR` 即可，你真實的登入自始未被碰過
  （`gh auth status` 前後相同可證）。清單⛔ 不印 `gh auth status` 的 stdout：帳號名與 token scope 在那裡。
- **E7 安裝版 `brief`**。**不帶 `--rules-root`** 跑 `brief --task <id> --role <角色> --stage <階段>`：
  rc 0，且 `framework:`／`user:`／`project:`／`task:` 四層來源標記齊全。
- **E8 三種來源**。同一道 `facts --task`：不帶旗標＝`package`；帶 `--rules-root <checkout>`＝`override`；
  把**只含 `wfx/` 套件目錄**（⛔ 無 `*.egg-info`）的路徑放進 `PYTHONPATH` 直跑＝`unknown`。
- **E9／E10 `write --dry-run`**。留言路徑用 `--comment-file`、欄位路徑用 `--field`；
  兩者都印 `would-write ⛔ 未送出任何 mutation`。零 mutation 的證據＝dry-run 前後的
  Issue `updatedAt`、留言數、`facts` 第 ③節兩個基準與 `gh project field-list` 逐字相同。
  **⛔ 不要為了取證貼測試留言。**
- **E11 缺環境負控**。空目錄跑 `brief --task`＝rc 1 `LayerMissing`；非 git 且⛔ 無 `GH_REPO`
  跑 `facts --task`＝rc 1 `TargetError`；`--project-root` 指到不存在的路徑跑 `facts --adopt`＝
  rc 1 `AdoptUnavailable`。三者的 **stdout 都應為空**（⛔ 不印半份結果）。
- **E12 升級不變**。照第 6 節取三份快照 → 在 **`/tmp` 的原始碼副本**改 `version` 再 build
  （**⛔ 不改你自己的工作樹、⛔ 不 commit 版本號**）→ `pip install --force-reinstall` →
  三份快照逐字相同。回退與移除照第 7／8 節，之後專案樹仍應逐字不變。
- **E13 測試**。`python -m pytest <此套件目錄>/tests -q`（3.14）須全綠。

收尾：刪掉 `/tmp/wfx-dist`、`/tmp/wfx-venv`、`$PROJ` 與那個暫存 `GH_CONFIG_DIR`；
你的工作樹 `git status` 應為 clean（輪子與 venv **從來不該**落在 repo 裡）。

## 11 · 選用模組

契約本體住 `rules/core/boundaries.md` §5「本版契約：選用文件模組」；本節只講怎麼操作。

- **本版只支援文件模組**：模組內容隨框架套件出貨，住規則樹 `modules/<名稱>/<階段>.md`。
  你的專案**⛔ 不複製、⛔ 不自寫**模組內容；專案自己的補充照舊寫在 `.wf/*.md`。
  目前套件出貨 `tdd`（只在 `執行`、`審核` 階段有文件，屬選用指引）；可用名稱以你安裝的版本規則樹 `modules/` 下的目錄為準。
- **啟用**：在 `.wf/config.json` 加一個鍵，其餘三鍵不動：

  ```
  "modules": ["<名稱>"]
  ```

  之後 `brief` 在該模組有文件的階段，會在首屏多一段 `### 啟用模組定位`、並把原文以
  `framework:modules/<名稱>/<階段>.md` 的來源標記附在 `### 適用規則` 之後；沒有文件的階段只在首屏
  標明「本階段⛔ 無文件，⛔ 不注入」。
- **停用／降級**：刪掉 `modules` 鍵，或設成 `null`（⛔ 不是 `[]`——空清單是形狀錯）。`brief` 輸出回到與未啟用時逐字相同，
  ⛔ 無其他清理步驟。回退到不認得 `modules` 鍵的舊套件前，**先**從設定移除它——舊版會把它當未知鍵
  （`ConfigError`）。
- **錯誤怎麼讀**（皆 rc 1、stdout 空）：
  - `ConfigError: modules 須為 null 或非空、不重複的模組名稱清單…`＝形狀錯（不是清單、空清單 `[]`、重複、空字串、
    含 `/` 或 `\`、以 `.` 開頭或前後有空白）；三個動詞都會擋，`facts --adopt` 把它列成「格式錯誤」。
  - `LayerMissing: 缺少必要層 framework：modules/<名稱>（…）`＝這個名稱不在你用的規則樹裡，或該目錄沒有文件。
    這一項要讀規則樹才判得出來，**只有 `brief` 會報**；`facts --adopt` 只驗形狀。
  - `MalformedInput: framework:modules/<名稱> 的檔名不是階段值：…`＝規則樹本身寫錯，請回報框架，⛔ 不要自行改檔。
