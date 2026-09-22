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
python -m pip install ai_workflow_vnext-<版本>-py3-none-any.whl
wfx
```

- 需要 Python **≥ 3.14**（`requires-python`）。
- 執行期⛔ 無 Python 相依（`pip show ai-workflow-vnext` 的 `Requires:` 為空）；
  `git` 與 `gh` 是**外部指令**，各自另行安裝。
- 安裝後⛔ 不需要本框架的 checkout、也⛔ 不需要 `PYTHONPATH`：規則樹（17 份 markdown）
  隨 wheel 走，住在 `wfx/rules/`，⛔ 不複製進你的專案。
- 無參數執行 `wfx` 會印用法並以 **rc 2** 結束（用法錯）。

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
- `unknown`＝這個直譯器裡⛔ 無 `ai-workflow-vnext` 的 distribution metadata
  （典型情況：以原始碼樹 `PYTHONPATH=… python -m wfx` 直跑）。**這是事實，⛔ 不是錯誤。**
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
| 格式錯誤 | 存在但形狀不合法（設定鍵、欄位型別、選項字面、狀態欄有第二個居所） |
| 環境阻塞 | 外部工具給出客觀錯誤；逐字附上**工具名、rc 與 stderr 首行** |
| 無法確認 | 本清單內的上游那一項還沒滿足，所以這一項還判不了 |

**rc ⛔ 不表達就緒與否**：清單產得出來一律 **rc 0**（不論項目狀態），連清單都產不出來
（`--project-root` 不是既存目錄、規則樹取不到）才 **rc 1**，用法錯是 **rc 2**。
要機械判斷就緒與否，讀第 7 節的計數行，⛔ 不要讀 rc。

判準邊界：文件類只判「存在且非空」，⛔ 不判內容品質；欄位型別依 `rules/core/github.md` §2，
SingleSelect 的選項依 `rules/core/values.md` 逐字比對；內建 `Status` 與自訂 `狀態`
**同時存在**＝狀態有第二個居所＝格式錯誤。

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

Project 的七個核心概念欄位（型別與選項逐字見清單第 5 節）**由你在平台上建立**，
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
⛔ 無 schema 還原步驟。

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
