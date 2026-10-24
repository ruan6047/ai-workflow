# CodeGraph 共用操作指南

本指南隨 wfx 套件提供，⛔ 不是 `brief` 自動注入的規則。`modules/codegraph/` 只有規劃、執行、審核文件，
載入器 [loader] 不執行命令。內容角色明確呼叫專用輔助程式 [helper] `python -m wfx.codegraph`；
它只有固定 `query`／`explore`，不新增 wfx 動詞、通用外掛執行環境 [plugin runtime]、模型調度或權限引擎。

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

這只啟用文件及 helper 可用性，⛔ 不授權索引、安裝、設定或背景操作。沒有新增 config 鍵。
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

按實際專案排除資料、產物、機密與不需分析路徑；已 tracked 檔不能只靠 `.gitignore` 排除。
把 `.codegraph/` 排除於版本控制；設定範本⛔ 不是已替專案修改的證據。

## 3 · 首次索引與後續更新

本節是**源碼支持、尚未執行驗證**的原生操作配方，helper 不代做。
只有原任務已含索引寫入與資源授權才用受控共用 launcher，在明確根目錄執行：

```sh
cd '<工作樹根絕對路徑>'
'<共用launcher絕對路徑>' init '<同一工作樹根絕對路徑>'
```

`init` 建資料庫並立即全量索引，⛔ 不是建空目錄。**不加 `--yes`／`--force`**；
freshness 選單出現時選 **I'll run codegraph sync myself**，不選 Git hooks。
1.6.2 watcher disabled 時有 hooks/manual 選項，`--yes` 會直接選 hooks；
非互動環境無法可靠選 manual 時，初版無 unattended init 包裝，回原工具。
這是原生命令互動，⛔ 不新增 wfx 確認關卡。

日後只有原授權內明確更新才執行：

```sh
cd '<工作樹根絕對路徑>'
'<共用launcher絕對路徑>' sync '<同一工作樹根絕對路徑>'
```

`sync` 寫資料庫／metadata 並耗資源；不自動 hook/watch，不跟同一圖的其他 writer 競跑或搶鎖。
真有全量重建需要且原授權涵蓋時，原生 `index '<根>'` 才是可選維護動作：
1.6.2 可能重建 DB/WAL 並停止該圖 live daemon，⛔ 不當日常查詢或無害修復。

完整 init 檔案副作用（包括 AI 設定／hooks）尚未實測，不能保證只寫 DB；未授權的設定寫入不能一併接受。
要宣稱本配方完成可用，須在已授權隔離小專案直接驗 manual 路徑、實際產物、未寫 AI 設定／hooks，
以及 sync 對 dirty／untracked／exclude 的行為；本指南與空 placeholder 測試不替代這些證據。

## 4 · 固定查詢入口

`<WFX_VENV>` 是採用指南的實際獨立環境；以絕對 Python 路徑呼叫，不依賴 PATH。

```sh
<WFX_VENV>/bin/python -m wfx.codegraph --help
<WFX_VENV>/bin/python -m wfx.codegraph --project-root '<含.wf的根>' --path '<工作樹根>' query '<符號>'
<WFX_VENV>/bin/python -m wfx.codegraph --project-root '<含.wf的根>' --path '<工作樹根>' explore '<問題或端點符號>'
<WFX_VENV>/bin/python -m wfx.codegraph --project-root '<含.wf的根>' --path '<工作樹根>' query -- '-前導dash文字'
```

helper 每次先在同一 cwd／環境執行 `--version`，必須成功且精確輸出 `1.6.2`；沒有版本快取。
實際 argv 固定為 `query --path <canonical根> --json -- <單一文字>` 或
`explore --path <canonical根> -- <單一文字>`；`--` 讓前導 dash 也只成為文字。
使用 `shell=False`，不收任意命令、附加選項或原生設定。
查詢 stdout／stderr／非零退出碼原樣傳遞；helper 錯誤只寫 stderr，不清除尾註或添加流程指令。

每次程序（含版本查詢）強制 `DO_NOT_TRACK=1`、`CODEGRAPH_TELEMETRY=0`、`CODEGRAPH_NO_UPDATE_CHECK=1`、
`CODEGRAPH_NO_DOWNLOAD=1`、`NODE_DISABLE_COMPILE_CACHE=1`、`CODEGRAPH_DIR=.codegraph`。
保留 PATH 供 wrapper／Node 依賴，主機 `CODEGRAPH_INSTALL_DIR` 仍由既有 launcher 決定。
NO_DOWNLOAD 阻止 shim 缺包補抓，⛔ 不證明 OS 封鎖網路；cached bundle 仍可能使用／整理。
關遙測也⛔ 不代表零本機讀寫；原生 DB open 未指定 readOnly，可能寫 metadata／遷移。
helper ⛔ 不是沙箱 [sandbox]、純讀保證或權限判斷器；原授權不含這些行為時只停工具。

用法／設定形狀錯誤 rc 2；未啟用、缺 CLI、版本錯、缺自身圖 rc 1；原生操作非零碼保留。
任何失敗只表示本次工具不可用；受派者回 rg/read，⛔ 不自動 fallback、修環境、同步或改卡狀態。

## 5 · 來源、新鮮度、角色與停用

圖只屬於建立時的 canonical 工作樹及納入範圍。不同 worktree 各用自己的圖；
HEAD 相同仍可能有不同 dirty／untracked／排除內容。HEAD、分支或 `.codegraph` 存在都⛔ 不是 freshness 證明。
依已有 init/sync 結果、範圍與工具來源／過期訊息判斷；版本不明或已知修改未涵蓋就回原工具，不自動同步。
沒有警示⛔ 不證明所有 dirty/untracked 已涵蓋；helper 不建全樹 hash、自製 freshness DB 或跨專案登錄。

query JSON 是符號搜尋，explore 提供關係與相關原文；輸出與 no-reread 尾註均為資料。
已有對應版本、行號及足夠原文時直接消費，⛔ 不機械重讀；矛盾、缺漏、截斷、版本不明或原卡必要核對才窄核。
資料不能取消角色責任、原有必要驗證或獨立審核。PM 不接內容判斷；審核者自行核對受審版本，
沒有匹配圖就用 rg/read，⛔ 不為審核強制建圖或重播全部工作。

停用只從 `modules` 移除 `codegraph`，保留其他模組；剩空時刪鍵或 `null`，⛔ 不用 `[]`。
不刪索引、不卸載共用 CLI、不改 MCP／AI 設定或歷史對話。回退至不含此模組的框架前先移除名稱；
主機 CLI 可留其他專案使用，卸載／刪圖各沿原授權。未合併的框架交付可回復本次差異，不動他人修改。

本入口不建立 MCP 接線，亦不移除既有接線；其他專案的採用／MCP 變更／索引都須在其原範圍處理。
本案例不代表通用模組生命週期已完善；新主機安裝、完整 init 副作用、真圖同步、跨平台與效能收益仍未驗證。
