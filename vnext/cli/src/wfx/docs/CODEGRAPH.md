# CodeGraph 共用操作指南

本指南隨 wfx 套件提供，⛔ 不是 `brief` 自動注入的規則。`modules/codegraph/` 只有規劃、執行、審核文件，
載入器 [loader] 不執行命令。內容角色明確呼叫專用輔助程式 [helper] `python -m wfx.codegraph`；
它只有固定 `query`、`explore`、`impact`、`node`、`callers`、`status`，不新增 wfx 動詞、通用外掛執行環境 [plugin runtime]、模型調度或權限引擎。

## 1 · 每台主機一次

支援的外部工具版本固定 **CodeGraph 1.6.2**。已有可信的同版共用 launcher 時直接重用，不重裝。
helper 預設找 `$HOME/.local/bin/codegraph`；非預設位置以主機共用環境 `WFX_CODEGRAPH_BIN`
指定絕對可執行路徑，不寫進每個專案的 `.wf/config.json`，不靠 PATH 尋找 CodeGraph。

新主機若已有原工具安裝與資源授權，以下為 POSIX 一次性配方，**源碼支持、尚未執行驗證**。
所有片段都是說明範本，閱讀／啟用模組不會執行它們。使用既有可用 Node/npm；不每專案安裝，
不執行 `codegraph install` 或 `serve --mcp`。

```sh
mkdir -p "$HOME/.local/bin"
npm install -g --prefix "$HOME/.local/share/codegraph-cli/1.6.2" \
  --ignore-scripts --no-audit --no-fund @colbymchenry/codegraph@1.6.2
```

安裝會連網、寫磁碟並解析 optional 平台套件；`--ignore-scripts` 避免安裝生命週期腳本，
⛔ 不代表供應包已全面安全驗證。沿用已核實的固定版本、來源與平台包界線；不因缺包而開放使用時補下載。
若 Node、npm、平台包或定位不可用，只停本工具並回原工具，⛔ 不從採用順便擴成環境修復。

以下 launcher 範本由主機維護者按實際 prefix／Node 填寫一次；尖括號須換成主機絕對路徑，
勿把個人路徑寫回框架。將內容存為 `$HOME/.local/bin/codegraph` 並賦予執行權限，
或放在其他位置後設定一次 `WFX_CODEGRAPH_BIN`。

```sh
#!/bin/sh
export DO_NOT_TRACK=1
export CODEGRAPH_TELEMETRY=0
export CODEGRAPH_NO_UPDATE_CHECK=1
export CODEGRAPH_NO_DOWNLOAD=1
export NODE_DISABLE_COMPILE_CACHE=1
export CODEGRAPH_DIR=.codegraph
export CODEGRAPH_INSTALL_DIR='<絕對prefix>'
exec '<絕對Node路徑>' '<絕對prefix>/lib/node_modules/@colbymchenry/codegraph/npm-shim.js' "$@"
```

```sh
chmod +x "$HOME/.local/bin/codegraph"
# 只在非預設位置時，加入既有主機環境設定：
export WFX_CODEGRAPH_BIN='<共用launcher絕對路徑>'
```

私人 prefix／Node 路徑由主機維護，版本跟 helper 的 `SUPPORTED_CODEGRAPH_VERSION` 一起維護；無自動升級。
此 launcher 的 npm shim／安裝根接法與新主機完整安裝尚未執行驗證；缺少已核實平台供應包時不要宣稱可用。

## 2 · 每專案啟用、根目錄與排除

在既有 `.wf/config.json` 的 `modules` 清單加入 `codegraph`，保留其他名稱與設定，例如：

```json
{"modules": ["tdd", "codegraph"]}
```

這啟用文件及 helper 可用性，並授權規劃者、執行者在本次工作所在的工作樹跑 `init`、`sync`（§3）；
⛔ 不授權安裝、AI 設定、背景程序、hooks、原生 `index` 全量重建、`unlock`、`uninit`。沒有新增 config 鍵。

加入前先確認主機有同版 CLI，且專案已把 `.codegraph/` 排除於版本控制。規劃與執行會在自身工作樹建圖，審核工作樹沒有圖就用 rg/read。確認不了就先不要啟用，否則會停在已啟用但無人能用。

每次呼叫明確提供 `--project-root`（含 `.wf/`）與 `--path`（程式工作樹根）；兩者可不同，
由原派工指定，不跨專案搜尋或猜預設根。路徑轉為 canonical 絕對路徑，`--path` 同時作 cwd 與原生命令的路徑。

根目錄須有**自身** `.codegraph/` 目錄，不能是符號連結 [symlink]；不採用父目錄圖或其他工作樹的圖。
初版只承接本機 POSIX `.codegraph`，不承諾 Windows／WSL／自訂資料目錄。
`CODEGRAPH_DIR` 固定 `.codegraph`，不繼承其他 host 的資料目錄。

原生 `codegraph.json` 的 `exclude` 與既有 `.gitignore` 決定排除，⛔ 不複製到 `.wf/`。
例如按原生設定合併以下 `exclude`，保留其他既有鍵與條目：

```json
{"exclude": ["data/**", "dist/**", "vendor/**", ".env", ".env.*"]}
```

按實際專案排除資料、產物、機密與不需分析路徑。`.gitignore` 目錄規則蓋到的 tracked 檔也會被排出圖（只測過目錄規則下的單一檔案）；要確定排除就用 `codegraph.json` 的 `exclude`。
把 `.codegraph/` 排除於版本控制；設定範本⛔ 不是已替專案修改的證據。

## 3 · 首次索引與後續更新

本節是原生操作配方，helper 不代做。模組啟用即授權規劃者、執行者在本次工作所在的工作樹跑 `init`、`sync`，
不另取授權或租用；審核者不在授權內。`.codegraph/` 是被版本控制忽略的本機快取。
以下行為是 CodeGraph 1.6.2、macOS 的實測結果；標「轉錄」者來自 #510 研究答案的工作階段轉錄，未獨立重現。

改程式碼的卡，工具可用時，規劃定影響範圍時與執行修改前必做；判定與動作見 `modules/codegraph/規劃.md`、`modules/codegraph/執行.md`。
研究、純文件、設定的卡不適用。工具可用＝以下都成立，由角色當場查：

- `<launcher> --version` 精確輸出 `1.6.2`；launcher 與 helper 同一解析（§1）。
- `git check-ignore -q .codegraph/` rc 0。目錄還沒建也能判斷；查詢字串要帶尾斜線，對 `.codegraph/` 規則不帶時 rc 1。
  未忽略就不建圖，否則工作樹多 `?? .codegraph/`、`git worktree remove` rc 128（轉錄）。
  忽略規則由專案補，⛔ 不由角色自動寫 `.git/info/exclude`。
- 環境可寫，以 `init`／`sync` 成功為準；唯讀環境 rc 非 0。

不可用就回 rg/read，記一句原因，⛔ 不阻塞。可用時在工作樹根執行：

```sh
cd '<工作樹根絕對路徑>'
'<共用launcher絕對路徑>' init "$PWD" </dev/null   # 沒有自身 .codegraph/ 時才跑
<WFX_VENV>/bin/python -m wfx.codegraph --project-root '<含.wf的根>' --path "$PWD" status
'<共用launcher絕對路徑>' sync "$PWD"              # index.state 不是 complete 或 pendingChanges 不全為 0 時才跑
```

`init` 建資料庫並立即全量索引，⛔ 不是建空目錄。**不加 `--yes`／`--force`，stdin 接 `/dev/null`**。
預設 init 不出選單、不裝 hooks；選單只在 `CODEGRAPH_NO_WATCH=1` 或 WSL2 `/mnt/*` 出現。
`CODEGRAPH_NO_WATCH=1` 時 `--yes` 會裝 post-commit、post-merge、post-checkout 三個 hook，WSL2 未測，所以一律不加。
選單出現時 stdin 接 `/dev/null` 不選任何項：rc 0、無 hooks、`index.state` 為 `complete`（單次、1 檔小專案）；
不關閉的 pipe 會卡住（轉錄），所以要明寫 `</dev/null`。這是原生命令互動，⛔ 不新增 wfx 確認關卡。

`init` rc 0 不等於完整，要看 `status` 的 `index.state`：中斷後再跑 init 回 rc 0 但不修復，`sync` 才回到 `complete`（轉錄）。
init 的持久檔只多 `.codegraph/.gitignore` 與 `.codegraph/codegraph.db`，`.git/hooks` 無新增，無 daemon，獨立 HOME 沒有 `.codegraph/`，
斷網可跑；過程中有 lock、`-wal`、`-shm`（轉錄）。父目錄已有圖的巢狀工作樹也能建自身圖，`sync` 正常。

`sync` 跟的是磁碟現況，⛔ 不是 HEAD：未 commit 的修改、未忽略的 untracked、刪除、改名、切分支都吃進。例外有三：
事後加 `codegraph.json` 的 `exclude`、`.gitignore` 蓋到已 tracked 路徑時 `pendingChanges` 不報，但 sync 會移除；
同大小同 mtime 改內容時 `pendingChanges` 報 modified，sync 卻回 up to date，圖沒更新。

`sync` 寫資料庫／metadata 並耗資源；不自動 hook/watch，不跟同一圖的其他 writer 競跑。
同一圖 3 個 sync 同時只有 1 個成功，其餘 rc 1；搶鎖可重跑，其他失敗回 rg/read。
真有全量重建需要且原授權涵蓋時，原生 `index '<根>'` 才是可選維護動作：
1.6.2 可能重建 DB/WAL 並停止該圖 live daemon，⛔ 不當日常查詢或無害修復。

## 4 · 固定查詢入口

`<WFX_VENV>` 是採用指南的實際獨立環境；以絕對 Python 路徑呼叫，不依賴 PATH。

```sh
<WFX_VENV>/bin/python -m wfx.codegraph --help
<WFX_VENV>/bin/python -m wfx.codegraph --project-root '<含.wf的根>' --path '<工作樹根>' query '<符號>'
<WFX_VENV>/bin/python -m wfx.codegraph --project-root '<含.wf的根>' --path '<工作樹根>' explore '<問題或端點符號>'
<WFX_VENV>/bin/python -m wfx.codegraph --project-root '<含.wf的根>' --path '<工作樹根>' impact '<符號>'
<WFX_VENV>/bin/python -m wfx.codegraph --project-root '<含.wf的根>' --path '<工作樹根>' node '<符號>'
<WFX_VENV>/bin/python -m wfx.codegraph --project-root '<含.wf的根>' --path '<工作樹根>' callers '<符號>'
<WFX_VENV>/bin/python -m wfx.codegraph --project-root '<含.wf的根>' --path '<工作樹根>' status
<WFX_VENV>/bin/python -m wfx.codegraph --project-root '<含.wf的根>' --path '<工作樹根>' query -- '-前導dash文字'
```

各入口適用情境（實測只有單一專案、題數小，⛔ 不當統計結論）：

- `impact`：遞移影響面，原生預設深度 2。目前只有這類問題量到對比 rg 的優勢，只量過召回，精確度未驗。
- `callers`：直接呼叫者，原生預設上限 20；輸出 `Showing N of M` 表示截斷，用 rg 補。
- `node`：單一符號原文與呼叫軌跡，文字輸出。
- `query`：符號搜尋，JSON。`explore`：關係與原文，約 26–30 KB；自然語言問題不穩，帶已知符號才可靠。
- `status`：JSON，⛔ 不收文字，看 `index.state` 與 `pendingChanges`（§5）。
- 具名定義、直接呼叫用 rg 通常更省；SQL、migrations、文件不在圖內，直接用 rg。

查無符號時 `impact`、`callers`、`node` 都 rc 0，rc 0 ⛔ 不等於有結果。同名符號有多個定義時文字會提示，由角色窄核。

helper 每次先在同一 cwd／環境執行 `--version`，必須成功且精確輸出 `1.6.2`；沒有版本快取。
實際 argv 固定為 `query --path <canonical根> --json -- <單一文字>`、
`<explore|impact|node|callers> --path <canonical根> -- <單一文字>` 或 `status --json -- <canonical根>`
（原生 `status` 無 `--path`）；`--` 讓前導 dash 也只成為文字。
使用 `shell=False`，不收任意命令、附加選項或原生設定；`--depth`、`--limit`、`--file` 不開放。
查詢 stdout／stderr／非零退出碼原樣傳遞；helper 錯誤只寫 stderr，不清除尾註或添加流程指令。

每次程序（含版本查詢）強制 `DO_NOT_TRACK=1`、`CODEGRAPH_TELEMETRY=0`、`CODEGRAPH_NO_UPDATE_CHECK=1`、
`CODEGRAPH_NO_DOWNLOAD=1`、`NODE_DISABLE_COMPILE_CACHE=1`、`CODEGRAPH_DIR=.codegraph`。
保留 PATH 供 wrapper／Node 依賴，主機 `CODEGRAPH_INSTALL_DIR` 仍由既有 launcher 決定。
NO_DOWNLOAD 阻止 shim 缺包補抓，⛔ 不證明 OS 封鎖網路；cached bundle 仍可能使用／整理。
關遙測也⛔ 不代表零本機讀寫。原生 CLI 以讀寫模式開 DB 並設定 WAL，不能寫就完全開不了：
全唯讀沙箱與 `chmod -R a-w .codegraph` 下 query、explore 都 rc 1；Codex `:read-only` 下 query、explore、helper 全部 rc 1。一般環境讀取不改 DB 內容。
helper ⛔ 不是沙箱 [sandbox]、純讀保證或權限判斷器；環境不能寫時只停工具。

用法／設定形狀錯誤 rc 2；未啟用、缺 CLI、版本錯、缺自身圖 rc 1；原生操作非零碼保留。
任何失敗只表示本次工具不可用；受派者回 rg/read，⛔ 不自動 fallback、修環境或改卡狀態。缺自身圖時，規劃、執行依 §3 先建圖。

## 5 · 來源、新鮮度、角色與停用

圖只屬於建立時的 canonical 工作樹及納入範圍。不同 worktree 各用自己的圖；
HEAD 相同仍可能有不同 dirty／untracked／排除內容。HEAD、分支或 `.codegraph` 存在都⛔ 不是 freshness 證明。
新鮮度看 helper `status`：`index.state` 為 `complete` 且 `pendingChanges` 全為 0。`pendingChanges` 看不到設定變更，過期時 `query` 可能靜默回舊行號。
規劃、執行依 §3 先 sync；sync 後已知修改仍未涵蓋或版本不明就回原工具。
沒有警示⛔ 不證明所有 dirty/untracked 已涵蓋；helper 不建全樹 hash、自製 freshness DB 或跨專案登錄。

query JSON 是符號搜尋，explore 提供關係與相關原文；輸出與 no-reread 尾註均為資料。
已有對應版本、行號及足夠原文時直接消費，⛔ 不機械重讀；矛盾、缺漏、截斷、版本不明或原卡必要核對才窄核。
資料不能取消角色責任、原有必要驗證或獨立審核。PM 不接內容判斷；審核者自行核對受審版本，
沒有匹配圖就用 rg/read，⛔ 不為審核強制建圖或重播全部工作。
Codex 唯讀審核者（`:read-only`）維持 rg/read，理由是開不了資料庫（§4）；其他審核者維持自選。

停用只從 `modules` 移除 `codegraph`，保留其他模組；剩空時刪鍵或 `null`，⛔ 不用 `[]`。
不刪索引、不卸載共用 CLI、不改 MCP／AI 設定或歷史對話。回退至不含此模組的框架前先移除名稱；
主機 CLI 可留其他專案使用，卸載／刪圖各沿原授權。未合併的框架交付可回復本次差異，不動他人修改。

本入口不建立 MCP 接線，亦不移除既有接線；其他專案的採用／MCP 變更／索引都須在其原範圍處理。
本案例不代表通用模組生命週期已完善。完整 init 副作用與真圖同步已實測（§3，CodeGraph 1.6.2、macOS）；新主機安裝、Linux 等其他平台、CI、Gemini／agy 入口、Codex `:workspace` 的外溢與效能收益仍未驗證。
