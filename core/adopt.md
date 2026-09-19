---
name: adopt
when: 乾淨 repository 要第一次採用本框架、確認安裝是否完整，或停止使用框架但保留專案歷史時讀
non_scope: ⛔ 不寫 readiness 基準後的版本升級（歸 WF-012）；⛔ 不寫 repo 前置與 Project 建板的人工步驟（住 ADOPTION.md）
last_confirmed: 2026-09-20
---

# 首次採用

採用是一條可重跑、可診斷、可退出的流程。CLI 只落地框架自己產生的資產並印清單，⛔ 不判斷採用專案該不該採用（第零條）。

## 1 · canonical install mode 與對帳

- canonical install mode 恰一種：**submodule**。rules source 以 git submodule 掛在採用專案內，路徑寫進 `.wf/modules.json` 的 `rules.path`（相對 project_root）。package 與 vendor 複製仍可讀，但⛔ 不是 canonical，只會少判、⛔ 不會誤判。
- 三個 gitlink 取源，各自診斷不同的真實狀態，⛔ 不以任一側冒充另一側：
  - **索引側**＝superproject 的 `git ls-files -s` 取 mode 160000 那筆的 SHA。這是 consumer 當下宣告要採用的版本，是 `framework-commit` 的權威取源。
  - **HEAD 側**＝superproject 的 `git ls-tree HEAD` 同一條路徑。它是診斷取源：只暫存未 commit 時兩側會分歧，而單靠 HEAD 側⛔ 不診斷「只暫存」。
  - **子模組簽出 HEAD**＝rules root 自己的 HEAD，取源是 `wf.gh.target.local_git_facts(<rules root>)` 的 `head_sha`，且其 `top_level` 必須等於 rules root 才採信。守門是必要的：對**未初始化**的子模組目錄直接讀 HEAD 會成功並回 superproject 自己的 HEAD，naive 取源會把 consumer 自己的 commit 誤當框架版本。
- rules root 的定位恰三個分支（取源＝`.wf/modules.json` 與三個全域旗標，`ADOPTION.md` §2）：
  - `--rules-root` ⇒ 取其 canonical 路徑；⛔ 不在 project root 之下 ⇒ 四列全 `unknown`，理由逐字「規則來源在專案根目錄之外」。
  - `rules.path` ⇒ **以該宣告值本身**當 gitlink 路徑（posix、相對 project_root）；它正是 git 索引認得的那個名字。
  - 兩者皆無（規則就在 project_root）⇒ 四列全 `unknown`，理由逐字「規則來源就在專案根目錄，⛔ 無 gitlink」。
  - rules source ⛔ 不是檔案系統轉接器（`RulesSource` 恰四成員、⛔ 無 path）⇒ 四列全 `unknown`，理由逐字「規則來源⛔ 不是檔案系統轉接器」。
- 對帳恰四列，逐列只比**同一種識別粒度**，各標 `ok`／`fail`／`unknown`，由 `snapshot --adopt preflight` 印：

| 列名 | 比什麼（左） | 比什麼（右） | 粒度 |
|---|---|---|---|
| `framework-version` | manifest 各項 `pin` 彙整出的唯一版本值 | 現行 rules source 讀到的版本值 | 版本值對版本值 |
| `framework-commit` | manifest 頂層 `source_commit` | 現在讀到的索引側 gitlink SHA | commit 對 commit |
| `gitlink-committed` | 索引側 gitlink SHA | HEAD 側 gitlink SHA | commit 對 commit |
| `gitlink-checkout` | 索引側 gitlink SHA | 子模組簽出 HEAD（經 `top_level` 守門） | commit 對 commit |

- 任一側不可得即該列 `unknown`，理由用固定措辭；理由字串⛔ 不得含例外類別名（⛔ 不把例外物件轉成字串印出）。
- **⛔ 不做的兩件事**：⛔ 不把 `pin`（版本字串）與 gitlink SHA 直接比相等——兩者是不同識別粒度的資料，比相等恆為假、⛔ 不構成有效對帳。⛔ 不做 SHA→版本值 映射，三條理由：① 該 commit 的物件只在**已初始化的子模組自身物件庫**取得得到，superproject 取不到；② 未初始化時該來源不存在，而 `modules/resource-lock/module.md` F-resource-lock-04 逐字「worktree 內 submodule 目錄空是預期，需要時明確初始化；「檔案不在我的樹裡」⛔ 不構成 finding」⇒ 此情形必須標 `unknown`、⛔ 不得標 fail；③ 四列已同粒度涵蓋版本與 commit 兩種身分，映射只多回答「這顆 SHA 當時寫的版本字串是什麼」，而那正是需要缺席物件的那一項。
- 框架版本值的唯一居所＝rules source 的 `cli/pyproject.toml` `[project] version`，以 `tomllib` 解析取得。⛔ 不建立遞增規則、⛔ 不建立 CHANGELOG、⛔ 不在規則本體另開第二個居所。

## 2 · manifest

- 唯一居所＝採用專案的 `.wf/adopt/manifest.json`（相對 project_root）。它是框架在 consumer 樹內的**唯一登記處**；⛔ 不另開 log、⛔ 不把所有權寫進被管理檔自身。
- 頂層鍵恰三個：`schema`（固定字面）、`source_commit`、`assets`。
- `source_commit`＝`--adopt install` 當下由 consumer superproject 讀到的**索引側** gitlink SHA（40 碼）；不可得時逐字寫 `null`、⛔ 不省略該鍵、⛔ 不填猜測值。它是 framework 層的**單一**事實（rules source 整體的身分），故⛔ 不是每項資產一個。gitlink 變動後重跑 `install` 會產生不同的 `source_commit`：這是預期行為，⛔ 不得被讀成冪等性缺陷（冪等的判準見 §3 的 `bootstrap`）。
- `assets` 每項恰四鍵：`path`（相對 project_root、posix）、`ownership`、`digest`（內容摘要 `sha256:<hex>`）、`pin`（來源版本值）。
- `ownership` 是封閉二值：`framework-managed`（框架落地並負責移除）、`consumer-owned`（採用專案自己的，框架只登記、⛔ 不刪除、⛔ 不改寫）。
- manifest 自身登記自己，`ownership`＝`framework-managed`。其 `digest` 的前像刻意定義為「把自己那一項的 `digest` 值換成空字串後的 canonical JSON」：否則摘要自指、算不出定值。⛔ 不得推出「manifest 可以不被登記」——未登記的路徑在 `install` 前後必須逐一不變。
- `framework-version` 的彙整規則四條：`pin` 值集合基數為 1 ⇒ 與現行版本值比；基數 >1 ⇒ `fail`（理由列出排序後的全部相異值）；任一項缺 `pin` 或 `pin` 非非空字串 ⇒ `unknown`（理由列出缺項的路徑，⛔ 不以部分資料判 ok）；manifest 不存在或 JSON 不合法 ⇒ `unknown`（⛔ 不 raise——preflight 是零寫入診斷，`core/verbs.md` §1 `snapshot` 列硬擋欄逐字為「—」）。

## 3 · 五個 step

`snapshot --adopt <step>` 的值域封閉為五個，順序即首次採用的順序。⛔ 無第六個 step；要加須需求方裁定。

- `install`：機械。把框架管理的資產從 rules source 落地到 consumer 樹，並寫 manifest（含 `source_commit`）。⛔ 不動任何未登記的路徑、⛔ 不覆寫既有的 `consumer-owned` 登記項。
- `preflight`：機械、零寫入。印診斷清單：static 身分三項（roots、repository、configured Project）、`ModuleValidation` 的每一條 `lines` 各一列、§1 的對帳四列，逐列標 `ok`／`fail`／`unknown`。
- `bootstrap`：機械、冪等。建立採用專案自有的骨架（`.wf/modules.json` 種子、`.wf/stages/<階段>.md`）並把它們以 `consumer-owned` 登記進 manifest；已存在的檔一律沿用、⛔ 不覆寫。冪等的判準＝連跑兩次後樹的路徑集合與每個檔的內容摘要逐一相等（⛔ 不比對 mtime）。
- `smoke`：機械、零寫入。逐項印最小端到端檢查，每項標 `ok`／`fail`／`unknown`。
- `deactivate`：機械。見 §5。
- 人工的部分⛔ 不由 CLI 做：repo ruleset 與 required status checks、Project 建板與五欄、第一張卡，全部住 `ADOPTION.md` §1／§3／§4 與本檔 §4。

## 4 · 遠端 Project 與 ruleset 的人工步驟

五個 step 對 Issue、留言、Project 資料與 ruleset 的 mutation 原語呼叫序列長度一律為 0。下列各項只列步驟、由人做，CLI ⛔ 不代做、⛔ 不用測試 mutation 探測權限；不可證明者一律明列 `unknown`（⛔ 不冒充允許或拒絕）：

- 建 ruleset：main 禁刪、禁改史、`required_linear_history`，bypass 清空（`ADOPTION.md` §1）。
- 設 required status checks（`secret-scan`、`commit-trailer`，有可達性檢查的專案加 `reachability`）。
- 建 Project 與五欄、兩個 view 與分組（`ADOPTION.md` §3）；建好後把 `{"owner": …, "number": …}` 回填 `.wf/modules.json` 的 `project`。
- 填 `.wf/modules.json` 的 `areas`（`ADOPTION.md` §2）與 `remote`。
- 授予 CLI 執行者對 repo 與 Project 的寫入權限。

## 5 · deactivate／remove 邊界

- `deactivate` 只移除 manifest 內 `ownership`＝`framework-managed` 的項（含 manifest 自己），並在移除後刪掉因此變空的 `.wf/adopt/` 目錄。
- 對 `consumer-owned` 的 `.wf/`（含 `.wf/modules.json`、`.wf/stages/`）零刪除、零改寫；對 Issue、留言、Project 資料與 ruleset 的 mutation 原語呼叫序列長度為 0。
- 判準只看 manifest 的 `ownership` 欄，⛔ 不看路徑前綴、⛔ 不看副檔名：一項被標成 `framework-managed` 就會被移除，標成 `consumer-owned` 就⛔ 不會。
- 專案歷史（git、Issue、留言、Project）一律保留；停用框架⛔ 不等於刪除採用專案的任何紀錄。
- 未登記的路徑⛔ 不在 `deactivate` 的射程內：manifest 缺席或不可解析時該次執行零刪除，並印一行說明。
