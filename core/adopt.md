---
name: adopt
when: 乾淨 repository 要第一次採用本框架、確認安裝是否完整，或停止使用框架但保留專案歷史時讀
non_scope: ⛔ 不寫 readiness 基準後的版本升級（歸 WF-012）；⛔ 不寫 repo 前置與 Project 建板的人工步驟（住 ADOPTION.md）
last_confirmed: 2026-09-20
---

# 首次採用

採用是一條可重跑、可診斷、可退出的流程。CLI 只落地框架自己產生的資產並印清單，⛔ 不判斷採用專案該不該採用（第零條）。

## 0 · 合成 consumer 樹

- 「合成 consumer 樹」＝在暫存目錄內現場建出的一棵採用專案樹：`git init` 一顆 superproject，把 rules source 以 submodule 掛進去，寫出 `.wf/modules.json`，其餘內容由該次判準自己造。
- 它逐字排除三者：**本 repo 工作樹**（判準⛔ 不在 aiwf 自己的簽出上驗）、**`.git/`**（版本控制內部狀態⛔ 不進任何檔案集合或內容摘要的母體）、**`archive/`**（唯讀封存，⛔ 不引為判準）。
- ⛔ 不依賴本 repo 歷史存在：合成樹的每一顆 commit 都在該次執行內現場產生，⛔ 不引用 aiwf 的任何 SHA、⛔ 不要求網路。
- 其餘各條以「掃描面＝合成 consumer 樹（`core/adopt.md` §0）」引用本段。

## 1 · canonical install mode 與對帳

- canonical install mode 恰一種：**submodule**。rules source 以 git submodule 掛在採用專案內，路徑寫進 `.wf/modules.json` 的 `rules.path`（相對 project_root）。package 與 vendor 複製仍可讀，但⛔ 不是 canonical，只會少判、⛔ 不會誤判。
- 三個 gitlink 取源，各自診斷不同的真實狀態，⛔ 不以任一側冒充另一側：
  - **索引側**（`gitlink.index`）＝superproject 的 `git ls-files -s` 取 mode 160000 那筆的 SHA。這是 consumer 當下宣告要採用的版本，是 `framework-commit` 的權威取源。
  - **HEAD 側**（`gitlink.head`）＝superproject 的 `git ls-tree HEAD` 同一條路徑。它是診斷取源：只暫存未 commit 時兩側會分歧，而單靠 HEAD 側⛔ 不診斷「只暫存」。
  - **子模組簽出 HEAD**（`submodule.checkout`）＝rules root 自己的 HEAD，取源是 `wf.gh.target.local_git_facts(<rules root>)` 的 `head_sha`，且其 `top_level` 必須等於 rules root 才採信。守門是必要的：對**未初始化**的子模組目錄直接讀 HEAD 會成功並回 superproject 自己的 HEAD，naive 取源會把 consumer 自己的 commit 誤當框架版本。
- rules root 的定位恰三個分支（取源＝`.wf/modules.json` 與三個全域旗標，`ADOPTION.md` §2）：
  - `--rules-root` ⇒ 取其 canonical 路徑；⛔ 不在 project root 之下 ⇒ 四列全 `unknown`，理由逐字「規則來源在專案根目錄之外」。
  - `rules.path` ⇒ **以該宣告值本身**當 gitlink 路徑（posix、相對 project_root）；它正是 git 索引認得的那個名字。
  - 兩者皆無（規則就在 project_root）⇒ 四列全 `unknown`，理由逐字「規則來源就在專案根目錄，⛔ 無 gitlink」。
  - rules source ⛔ 不是檔案系統轉接器（`RulesSource` 恰四成員、⛔ 無 path）⇒ 四列全 `unknown`，理由逐字「規則來源⛔ 不是檔案系統轉接器」。
- 取源 ID 欄的封閉字彙恰六個：`manifest.pin`、`rules.version`、`manifest.source_commit`、`gitlink.index`、`gitlink.head`、`submodule.checkout`。表外值⛔ 不得出現；每一個取源至少有一個消費列。
- **對帳表**：恰四列，逐列只比**同一種識別粒度**，各標 `ok`／`fail`／`unknown`，由 `snapshot --adopt preflight` 印。

| 列名 | 左側（取源 ID） | 右側（取源 ID） | 粒度 |
|---|---|---|---|
| `framework-version` | manifest 內 `framework-managed` 項 `pin` 的彙整值（`manifest.pin`） | 現行 rules source 讀到的版本值（`rules.version`） | 版本值對版本值 |
| `framework-commit` | manifest 頂層 `source_commit`（`manifest.source_commit`） | 現在讀到的索引側 gitlink SHA（`gitlink.index`） | commit 對 commit |
| `gitlink-committed` | 索引側 gitlink SHA（`gitlink.index`） | HEAD 側 gitlink SHA（`gitlink.head`） | commit 對 commit |
| `gitlink-checkout` | 索引側 gitlink SHA（`gitlink.index`） | 子模組簽出 HEAD（`submodule.checkout`） | commit 對 commit |

- 逐列獨立：任一側不可得即**該列** `unknown`，理由用固定措辭；某一列的取源不可得⛔ 不得使另一列由可得變 `unknown`。理由字串⛔ 不得含例外類別名（⛔ 不把例外物件轉成字串印出）。
- **⛔ 不做的兩件事**：⛔ 不把 `pin`（版本字串）與 gitlink SHA 直接比相等——兩者是不同識別粒度的資料，比相等恆為假、⛔ 不構成有效對帳。⛔ 不做 SHA→版本值 映射，三條理由：① 該 commit 的物件只在**已初始化的子模組自身物件庫**取得得到，superproject 取不到；② 未初始化時該來源不存在，而 `modules/resource-lock/module.md` F-resource-lock-04 逐字「worktree 內 submodule 目錄空是預期，需要時明確初始化；「檔案不在我的樹裡」⛔ 不構成 finding」⇒ 此情形必須標 `unknown`、⛔ 不得標 fail；③ 四列已同粒度涵蓋版本與 commit 兩種身分，映射只多回答「這顆 SHA 當時寫的版本字串是什麼」，而那正是需要缺席物件的那一項。
- 框架版本值的唯一居所＝rules source 的 `cli/pyproject.toml` `[project] version`，以 `tomllib` 解析取得。⛔ 不建立遞增規則、⛔ 不建立 CHANGELOG、⛔ 不在規則本體另開第二個居所。

## 2 · manifest

- 唯一居所＝採用專案的 `.wf/adopt/manifest.json`（相對 project_root）。它是框架在 consumer 樹內的**唯一登記處**；⛔ 不另開 log、⛔ 不把所有權寫進被管理檔自身。
- 頂層鍵恰三個：`schema`（固定字面 `wf-adopt-manifest`）、`source_commit`、`assets`。
- `source_commit`＝`--adopt install` 當下由 consumer superproject 讀到的**索引側** gitlink SHA（40 碼）；不可得時逐字寫 `null`、⛔ 不省略該鍵、⛔ 不填猜測值。它是 framework 層的**單一**事實（rules source 整體的身分），故⛔ 不是每項資產一個，也⛔ 不得出現在任一 `assets` 項內。gitlink 變動後重跑 `install` 會產生不同的 `source_commit`：這是預期行為，⛔ 不得被讀成冪等性缺陷（冪等的判準見 §3 的 `bootstrap`）。
- `assets` 每項恰四鍵：`path`（相對 project_root、posix）、`ownership`、`digest`（內容摘要 `sha256:<hex>`）、`pin`（來源版本值）。同一份 manifest 內 `path` 值兩兩相異。
- `ownership` 是封閉二值：`framework-managed`（框架落地並負責移除）、`consumer-owned`（採用專案自己的，框架只登記、⛔ 不刪除、⛔ 不改寫）。
- `path` 的文法分兩類，由 `#` 的出現次數機械分辨，故單一 `path` 值⛔ 不得同時屬於兩類：
  - **整檔**：⛔ 不含 `#` 的相對路徑；其 `digest` 的前像是該檔的全部位元組。
  - **片段**：恰一個 `#`，左段是承載檔的相對路徑、右段是片段名，兩段皆非空。
- 片段資產的判定（`smoke` 與 `deactivate` 共用這一份定義，⛔ 不另立第二套）：
  - `digest` 的前像＝承載檔內該 job 的**逐字文字**：自該 job 的鍵行起、到下一個縮排 ≤ 該鍵行的非空行之前，去掉尾端空白行。故只改動承載檔內⛔ 非框架 job 的位元組時該 `digest` ⛔ 不得改變。
  - 「存在」＝承載檔內有同名 job；「摘要相符」＝該逐字文字的 `sha256:<hex>` 等於該項 `digest`。
  - 「片段區間」＝上述行區間。`jobs:` 標頭行**屬頂層骨架、⛔ 不屬任何片段區間**：`install` 只在**新建**承載檔時經頂層骨架把它帶進來，對**已存在**的承載檔⛔ 不新增該標頭行；`deactivate` ⛔ 不移除該標頭行（包含移除全部框架片段後 `jobs:` 之下再無鍵的情形）。⛔ 不得推出「`install` 可以改寫承載檔的頂層骨架」——片段區間之外的位元組逐一不變。
  - job 鍵行的辨識：縮排恰兩格、鍵名後恰一個半形冒號，其後只准空白與一段 `#` 行尾註解（`  secret-scan: # consumer job` 是一個 job 鍵行）。`jobs:` 之下有⛔ 不符該形狀的⛔ 非空白、⛔ 非整行註解的兩格縮排行時，片段邊界**無法安全辨識**，`install` 對該承載檔零寫入並印一行說明。
  - `install` 與 `deactivate` 都**維持承載檔檔尾有⛔ 無換行的原狀**：為了把新行接上去而補的那個換行⛔ 不屬於任何片段區間，⛔ 不得留在檔尾。行尾序列（LF／CRLF）在片段區間之外逐一保留：讀寫走位元組，⛔ 不做 universal newlines 正規化。
  - 登記路徑在 consumer 樹上是**符號連結**時，`install` ⛔ 不寫入該路徑、`deactivate` ⛔ 不移除它，各印一行說明：寫穿連結會改到連結指向的（多半⛔ 未登記的）consumer 檔，解析後再刪也是刪錯對象。該判準與 §5「刪除面封閉在 project_root 之內」是**兩條**判準，⛔ 不得以任一條冒充另一條。
- **manifest 結構宣告**：可解析的 JSON ⛔ 不等於有效 manifest。下表逐列列出⛔ 不合法的形狀；命中任一列即整份 manifest 判為不可解析，全部讀取端回固定理由並續跑、⛔ 不 raise。

| 缺陷代號 | ⛔ 不合法的形狀 |
|---|---|
| `top-keys` | 頂層⛔ 不是物件，或頂層鍵集合 ≠ `schema`／`source_commit`／`assets` 三鍵（含頂層缺 `schema`） |
| `schema-value` | `schema` 的值 ≠ 固定字面 `wf-adopt-manifest` |
| `source-commit` | `source_commit` 既⛔ 非 40 碼字串也⛔ 非 `null` |
| `assets-type` | `assets` ⛔ 非陣列 |
| `entry-type` | 某一項⛔ 非物件（含 `assets: [null]`） |
| `entry-keys` | 某一項的鍵集合 ≠ `path`／`ownership`／`digest`／`pin` 四鍵（缺一鍵或多一鍵皆是） |
| `entry-value` | 某一項的 `path` ⛔ 非非空字串、`ownership` 不在封閉二值內、或 `digest`／`pin` ⛔ 非字串 |
| `path-unique` | 同一份 manifest 內有兩項 `path` 值相同 |
| `path-grammar` | 某一項的 `path` ⛔ 無法被上面的文法歸入整檔或片段恰一類 |

- manifest 自身登記自己，`ownership`＝`framework-managed`。其 `digest` 的前像刻意定義為「把自己那一項的 `digest` 值換成空字串後的 canonical JSON」：否則摘要自指、算不出定值。⛔ 不得推出「manifest 可以不被登記」——未登記的路徑在 `install` 前後必須逐一不變。
- `framework-version` 的彙整規則四條，**母體只含 `ownership`＝`framework-managed` 的項**（`consumer-owned` 項的 `pin` ⛔ 不進彙整）：`pin` 值集合基數為 1 ⇒ 與現行版本值比；基數 >1 ⇒ `fail`（理由列出排序後的全部相異值）；任一項缺 `pin` 或 `pin` 非非空字串 ⇒ `unknown`（理由列出缺項的路徑，⛔ 不以部分資料判 ok）；manifest 不存在或⛔ 不合上面的結構宣告 ⇒ `unknown`（⛔ 不 raise——preflight 是零寫入診斷，`core/verbs.md` §1 `snapshot` 列硬擋欄逐字為「—」）。
- **consumer 面 job 片段表**：「承載檔」欄與「片段來源檔」欄各只有一個值；`_adopt` 層對該兩個值各只有一個字面居所、與本表逐字相等，且⛔ 不由 `.wf/modules.json` 或任何設定鍵宣告。

| 片段名 | 承載檔 | 片段來源檔 | 是否帶 `actions/setup-python` |
|---|---|---|---|
| `secret-scan` | `.github/workflows/wf.yml` | `.github/adopt/consumer-jobs.yml` | 否 |
| `commit-trailer` | `.github/workflows/wf.yml` | `.github/adopt/consumer-jobs.yml` | 是 |

- 片段來源檔與框架自身 `.github/workflows/ci.yml` 的同名 job **允許的差異恰一處**：consumer 側在該 job 的 `actions/checkout` 步驟的 `with:` 區塊內多一行逐字 `submodules: true`。該同步是測試義務，⛔ 不只是宣告。`reachability` 與 `cli-tests` 兩個 job 檢查的是本 repo 自己的被測物，⛔ 不進本表。
- 新建承載檔時，其頂層骨架（至少 `name`、`on`、`permissions`、`jobs` 四鍵，且 `on` 之下同時有 `push` 與 `pull_request`）逐字取自片段來源檔，CLI ⛔ 不另建第二個居所；承載檔已存在時 CLI ⛔ 不改寫其頂層骨架、只在 `jobs:` 之下處置片段。既有承載檔⛔ 無 `jobs:` 標頭時，補上該鍵就是改寫頂層骨架 ⇒ `install` 對該檔零寫入、⛔ 不登記任何片段，並印一行說明。
- `install` ⛔ 不覆寫整檔登記為 `consumer-owned` 的承載檔：該情形下對該檔零寫入、⛔ 不登記任何片段，並印一行說明。整檔登記與 `<承載檔>#<片段名>` 的片段登記是**兩種**登記，整檔登記涵蓋該檔的全部位元組。

## 3 · 五個 step

`snapshot --adopt <step>` 的值域封閉為五個，順序即首次採用的順序。⛔ 無第六個 step；要加須需求方裁定。

- `install`：機械。把框架管理的資產從 rules source 落地到 consumer 樹（整檔資產直接寫檔；片段資產自片段來源檔**逐字**取該 job 寫進承載檔，承載檔不存在時以片段來源檔的頂層骨架建立它），並寫 manifest（含 `source_commit`）。⛔ 不動任何未登記的路徑、⛔ 不覆寫既有的 `consumer-owned` 登記項（含整檔登記的承載檔）、⛔ 不覆寫承載檔內未登記為 `framework-managed` 的同名 job、⛔ 不寫穿符號連結、⛔ 不在既有承載檔內新增 `jobs:` 標頭、片段邊界無法安全辨識時⛔ 不猜；上述各情形一律對該路徑零寫入並各印一行說明。
- `preflight`：機械、零寫入。印診斷清單恰七項：static 身分三項（`roots`、`repository`、`configured Project`）與 §1 的對帳四列，順序固定、逐列標 `ok`／`fail`／`unknown`。清單來源是 `_adopt` 層的單一常數，⛔ 不含資料相依的 `ModuleValidation.lines` 列。
- `bootstrap`：機械、冪等。建立採用專案自有的骨架（`.wf/modules.json` 種子、`.wf/stages/<階段>.md`）並把它們以 `consumer-owned` 登記進 manifest；已存在的檔一律沿用、⛔ 不覆寫。種子的 `rules` 鍵寫入 bootstrap 當次解析到的 rules root（相對 project_root；規則就在 project_root 時寫 `null`），使同一棵樹上⛔ 不帶任何全域旗標的 `preflight` 解析到同一個 rules root。冪等的判準＝連跑兩次後樹的路徑集合與每個檔的內容摘要逐一相等（⛔ 不比對 mtime）。
- `smoke`：機械、零寫入。逐項印最小端到端檢查，每項標 `ok`／`fail`／`unknown`。取源 ID 的封閉字彙恰六個：`manifest.file`、`tree.assets`、`rules.version`、`config.file`、`rules.stages`、`tree.stages`；表外值⛔ 不得出現，每一個取源至少有一個消費項。`managed-assets` 是**雙向**判準，母體＝應安裝集合（整檔項與上面片段表的片段項）：每一項都必須①在 manifest 內有登記、且②在樹上存在且摘要相符，任一方向任一項⛔ 不成立即該列 `fail`；manifest 不存在或⛔ 不合 §2 結構宣告時該列⛔ 不得標 `ok`。

| 項名 | 取源 ID |
|---|---|
| `adopt-manifest` | `manifest.file` |
| `managed-assets` | `manifest.file`、`tree.assets` |
| `version-pin` | `manifest.file`、`rules.version` |
| `project-config` | `config.file` |
| `stage-notes` | `rules.stages`、`tree.stages` |

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

- `deactivate` 只移除 manifest 內 `ownership`＝`framework-managed` 的項（含 manifest 自己）：**整檔**項刪該路徑，**片段**項自承載檔移除該片段區間；移除後刪掉因此變空的 `.wf/adopt/` 目錄。
- 對 `consumer-owned` 的 `.wf/`（含 `.wf/modules.json`、`.wf/stages/`）零刪除、零改寫；對 Issue、留言、Project 資料與 ruleset 的 mutation 原語呼叫序列長度為 0。
- 判準只看 manifest 的 `ownership` 欄，⛔ 不看路徑前綴、⛔ 不看副檔名：一項被標成 `framework-managed` 就會被移除，標成 `consumer-owned` 就⛔ 不會。
- 刪除面封閉在 project_root 之內：某項的 `path` 解析後（含絕對路徑、`..`、經符號連結越出）⛔ 不在 project_root 之下時，該項⛔ 不刪除並印一行說明。封閉性看的是**那個名字落在哪裡**，處置的是**那個名字本身**：⛔ 不得以 `resolve()` 後的目標當處置對象，否則登記路徑是樹內符號連結時會刪到連結指向的⛔ 未登記 consumer 檔（樹內刪錯對象，⛔ 不是越界）。
- `install` 與 `deactivate` 對承載檔是**位元組級可逆**：install 之前⛔ 不存在的承載檔在 deactivate 之後⛔ 不存在；install 之前已存在的承載檔在 deactivate 之後仍存在且位元組與 install 之前逐一相等（含原本⛔ 無任何 job 的承載檔——⛔ 無 `jobs:` 鍵、只有一個⛔ 無子鍵的 `jobs:` 標頭、檔尾⛔ 無換行、行尾為 CRLF 四種形狀皆在本條母體內）。本條與 §2 的片段區間定義同向：`jobs:` 標頭行與接行用的換行都⛔ 不屬片段區間，故兩側都⛔ 不動它們。
- 專案歷史（git、Issue、留言、Project）一律保留；停用框架⛔ 不等於刪除採用專案的任何紀錄。
- 未登記的路徑⛔ 不在 `deactivate` 的射程內：manifest 缺席或⛔ 不合 §2 結構宣告時該次執行零刪除，並印一行說明。
