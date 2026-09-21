---
name: adopt
when: 乾淨 repository 要第一次採用本框架、確認安裝是否完整，或停止使用框架但保留專案歷史時讀
non_scope: ⛔ 不寫 readiness 基準後的版本升級（歸 WF-012）；⛔ 不寫 repo 前置與 Project 建板的人工步驟（住 ADOPTION.md）
last_confirmed: 2026-09-20
---

# 首次採用

採用是一條可重跑、可診斷、可退出的流程。CLI 只落地框架自己產生的資產、只交事實與未完成項；⛔ 不判斷採用專案該不該採用，⛔ 不推導採用者既有檔案的插入或移除區間，⛔ 不解析採用者既有檔案的內部結構（第零條）。既有檔案的整合由執行者 AI 在既有授權內完成，由查核者核對結果。

## 0 · 合成 consumer 樹

- **step 名的封閉值域恰五個**，順序即首次採用的順序：`install`、`preflight`、`bootstrap`、`smoke`、`deactivate`。本節是該值域的唯一居所，`snapshot --adopt` 解析層的封閉值域與本清單逐字相等；⛔ 無第六個 step，要加須需求方裁定。
- 「合成 consumer 樹」＝在暫存目錄內現場建出的一棵採用專案樹：`git init` 一顆 superproject，把 rules source 以 submodule 掛進去，寫出 `.wf/modules.json`，其餘內容由該次判準自己造。
- 它逐字排除三者：**本 repo 工作樹**（判準⛔ 不在 aiwf 自己的簽出上驗）、**`.git/`**（版本控制內部狀態⛔ 不進任何檔案集合或內容摘要的母體）、**`archive/`**（唯讀封存，⛔ 不引為判準）。
- ⛔ 不依賴本 repo 歷史存在：合成樹的每一顆 commit 都在該次執行內現場產生，⛔ 不引用 aiwf 的任何 SHA、⛔ 不要求網路。
- 其餘各條以「掃描面＝合成 consumer 樹（`core/adopt.md` §0）」引用本段。
- **首次採用的必要配置項**恰九項，本節是該母體的唯一居所；每一項的「由誰填」與「何時填」住 `ADOPTION.md` 的對應節，⛔ 不住 `notes` 合成輸出（`.wf/stages/<階段>.md` 的 `P-` 或卡面 `notes` 的 `T-`）。
- 該母體逐字恰為：`areas`、`merge_method`、`modules`、`project`、`rules`、`remote`、`ruleset`、`required-status-checks`、`project-fields`。

## 1 · canonical install mode 與對帳

- canonical install mode 恰一種：**submodule**。rules source 以 git submodule 掛在採用專案內，路徑寫進 `.wf/modules.json` 的 `rules.path`（相對 project_root）。package 與 vendor 複製仍可讀，但⛔ 不是 canonical，只會少判、⛔ 不會誤判。
- 三個 gitlink 取源，各自診斷不同的真實狀態，⛔ 不以任一側冒充另一側：
  - **索引側**（`gitlink.index`）＝superproject 的 `git ls-files -s` 取 mode 160000 那筆的 SHA。這是 consumer 當下宣告要採用的版本，是 `framework-commit` 的權威取源。
  - **HEAD 側**（`gitlink.head`）＝superproject 的 `git ls-tree HEAD` 同一條路徑。它是診斷取源：只暫存未 commit 時兩側會分歧，而單靠 HEAD 側⛔ 不診斷「只暫存」。
  - **子模組簽出 HEAD**（`submodule.checkout`）＝rules root 自己的 HEAD，取源是 `wf.gh.target.local_git_facts(<rules root>)` 的 `head_sha`，且其 `top_level` 必須等於 rules root 才採信。守門是必要的：對**未初始化**的子模組目錄直接讀 HEAD 會成功並回 superproject 自己的 HEAD，naive 取源會把 consumer 自己的 commit 誤當框架版本。
- 另三個取源：`manifest.pin`＝manifest 內 `framework-managed` 項 `pin` 的彙整值；`manifest.source_commit`＝manifest 頂層 `source_commit`；`rules.version`＝現行 rules source 讀到的版本值。
- rules root 的定位恰三個分支（取源＝`.wf/modules.json` 與三個全域旗標，`ADOPTION.md` §2）：
  - `--rules-root` ⇒ 取其 canonical 路徑；⛔ 不在 project root 之下 ⇒ 四列全 `unknown`，理由逐字「規則來源在專案根目錄之外」。
  - `rules.path` ⇒ **以該宣告值本身**當 gitlink 路徑（posix、相對 project_root）；它正是 git 索引認得的那個名字。
  - 兩者皆無（規則就在 project_root）⇒ 四列全 `unknown`，理由逐字「規則來源就在專案根目錄，⛔ 無 gitlink」。
  - rules source ⛔ 不是檔案系統轉接器（`RulesSource` 恰四成員、⛔ 無 path）⇒ 四列全 `unknown`，理由逐字「規則來源⛔ 不是檔案系統轉接器」。
- 取源 ID 的封閉字彙恰六個：`manifest.pin`、`rules.version`、`manifest.source_commit`、`gitlink.index`、`gitlink.head`、`submodule.checkout`。表外值⛔ 不得出現；每一個取源至少有一個消費列。
- **對帳表**：恰四列，逐列只比**同一種識別粒度**，各標 `ok`／`fail`／`unknown`，由 `snapshot --adopt preflight` 印。左右兩欄各只寫一個取源 ID。

| 列名 | 左側取源 ID | 右側取源 ID | 粒度 |
|---|---|---|---|
| `framework-version` | `manifest.pin` | `rules.version` | 版本值對版本值 |
| `framework-commit` | `manifest.source_commit` | `gitlink.index` | commit 對 commit |
| `gitlink-committed` | `gitlink.index` | `gitlink.head` | commit 對 commit |
| `gitlink-checkout` | `gitlink.index` | `submodule.checkout` | commit 對 commit |

- 逐列獨立：任一側不可得即**該列** `unknown`，理由用固定措辭；某一列的取源不可得⛔ 不得使另一列由可得變 `unknown`。理由字串⛔ 不得含例外類別名（⛔ 不把例外物件轉成字串印出）。
- **⛔ 不做的兩件事**：⛔ 不把 `pin`（版本字串）與 gitlink SHA 直接比相等——兩者是不同識別粒度的資料，比相等恆為假、⛔ 不構成有效對帳。⛔ 不做 SHA→版本值 映射，三條理由：① 該 commit 的物件只在**已初始化的子模組自身物件庫**取得得到，superproject 取不到；② 未初始化時該來源不存在，而 `modules/resource-lock/module.md` F-resource-lock-04 逐字「worktree 內 submodule 目錄空是預期，需要時明確初始化；「檔案不在我的樹裡」⛔ 不構成 finding」⇒ 此情形必須標 `unknown`、⛔ 不得標 fail；③ 四列已同粒度涵蓋版本與 commit 兩種身分，映射只多回答「這顆 SHA 當時寫的版本字串是什麼」，而那正是需要缺席物件的那一項。
- 框架版本值的唯一居所＝rules source 的 `cli/pyproject.toml` `[project] version`，以 `tomllib` 解析取得。⛔ 不建立遞增規則、⛔ 不建立 CHANGELOG、⛔ 不在規則本體另開第二個居所。

## 2 · manifest 與框架資產

- 唯一居所＝採用專案的 `.wf/adopt/manifest.json`（相對 project_root）。它是框架在 consumer 樹內的**唯一登記處**；⛔ 不另開 log、⛔ 不把所有權寫進被管理檔自身。
- 頂層鍵恰三個：`schema`（固定字面 `wf-adopt-manifest`）、`source_commit`、`assets`。
- `source_commit`＝`--adopt install` 當下由 consumer superproject 讀到的**索引側** gitlink SHA（40 碼）；不可得時逐字寫 `null`、⛔ 不省略該鍵、⛔ 不填猜測值。它是 framework 層的**單一**事實（rules source 整體的身分），故⛔ 不是每項資產一個，也⛔ 不得出現在任一 `assets` 項內。gitlink 變動後重跑 `install` 會產生不同的 `source_commit`：這是預期行為，⛔ 不得被讀成冪等性缺陷（冪等的判準見 §3 的 `bootstrap`）。
- `assets` 每項恰四鍵：`path`（相對 project_root、posix）、`ownership`、`digest`（內容摘要 `sha256:<hex>`）、`pin`（來源版本值）。同一份 manifest 內 `path` 值兩兩相異。
- `ownership` 是封閉二值：`framework-managed`（框架落地並負責移除）、`consumer-owned`（採用專案自己的，框架只登記、⛔ 不刪除、⛔ 不改寫）。
- **`path` 只有整檔一種文法**：⛔ 不含 `#` 的相對路徑，其 `digest` 的前像是該檔的全部位元組。CLI 新產生的登記項一律是這一種；⛔ 不得有第二種文法，⛔ 不得以 `path` 指向檔案內的一段。
- **legacy 登記項**：manifest 內**既有**的、`path` 含 `#` 的項是已退休的片段機制殘留，一律視為 legacy。CLI 只在診斷中逐項列出並指向 `ADOPTION.md` §5，⛔ 不處置、⛔ 不重寫、⛔ 不刪除其承載檔；它們也⛔ 不進 `framework-version` 的彙整母體與 `managed-assets` 的母體。⛔ 不得推出「legacy 項使整份 manifest 無效」——結構宣告⛔ 不以 `#` 判不合法。
- **控制檔集合恰一個成員**：`.wf/adopt/manifest.json`（相對 project_root）。本條是它的**具名宣告**、⛔ 不是資產表的一列；它⛔ 無來源檔、⛔ 非整檔複製產生、⛔ 不適用下面兩個分支，由 `install` 與 `bootstrap` 依本節的結構宣告生成或就地更新。**控制檔⛔ 不在 `assets` 內登記自己**：它的生成、更新與移除權限來自本條，⛔ 非來自任何登記項；`assets` 內任一項的 `path` ⛔ 不得等於它（結構宣告的 `control-path` 列，命中即整份 manifest 判為不可用）。它自身的機械事實由 §3 的 `adopt-manifest` 項承接——存在且合結構宣告即 `ok`，**⛔ 不比對自身的內容摘要**：⛔ 無自指摘要、⛔ 不得再有第二種 `digest` 前像文法。
- **框架資產表**：恰四欄，逐列列出 `install` 應交付的框架資產。資產名集合與 `_adopt` 層的資產常數逐字相等，且必含使 `ADOPTION.md` §1 的 required status checks 成立所需的兩個 CI job（`secret-scan`、`commit-trailer`）的來源資產。

| 資產名 | 來源檔 | 目標路徑 | 是否必要 |
|---|---|---|---|
| `consumer-ci-jobs` | `.github/adopt/consumer-jobs.yml` | `.github/workflows/wf.yml` | 必要 |
| `trailer-check` | `.github/scripts/trailer_check.py` | `.github/scripts/trailer_check.py` | 必要 |

- 每項資產另宣告兩件事，供未完成項使用：**必要內容識別**（CI 資產＝job 名）與**規範定位**（`ADOPTION.md` 的節次）。`consumer-ci-jobs` 承載 `secret-scan` 與 `commit-trailer` 兩個 job、定位 `ADOPTION.md` §1；`trailer-check` 承載 `trailer_check.py` 這個 P5 檢查腳本、定位 `ADOPTION.md` §1。
- **兩個分支的前置條件是控制檔可用**：控制檔路徑上已有一個⛔ 不合本節結構宣告的既有物（含⛔ 非 JSON、目錄、符號連結）時，`install` 對**全樹**零位元組寫入（含⛔ 不存在的目標路徑）、⛔ 不落地任何資產、⛔ 不生成控制檔，輸出一項未完成項並回固定理由續跑、⛔ 不 raise，⛔ 不進入分支判定。這是前置條件、**⛔ 不是第三個分支**。`bootstrap` 同此前置條件。
- **`install` 的行為恰兩個分支、⛔ 無第三種**：
  - ① 目標路徑上⛔ 無既有物 ⇒ 由來源檔**整檔**落地，落地後目標內容與來源檔位元組逐一相等，並在 manifest 登記一項。
  - ② 目標路徑上已有既有物（一般檔、目錄、符號連結皆是，**⛔ 不論其內容、⛔ 不解析其內部結構**），或該路徑已是 `consumer-owned` 登記項 ⇒ 對該路徑零位元組寫入、⛔ 不登記、⛔ 不產生同一路徑雙重登記，並輸出一項**未完成項**。
- **未完成項**的鍵集合封閉、恰四鍵，值皆⛔ 非空：`source`（來源資產路徑）、`target`（目標路徑）、`content`（該資產所承載的必要內容識別）、`section`（規範定位，`ADOPTION.md` 的節次）。CLI 只交事實與未完成項；採用者既有內容的整合由執行者 AI 完成、由查核者核對結果。`bootstrap` 的既有檔情形用同一個鍵集合。
- `install` 對**兩個宣告集合的聯集**（資產表的目標路徑集合＋控制檔集合）以外的任何**一般檔案**零影響：存在性與整檔內容摘要（口徑＝SHA-256，⛔ 不比對 mtime）在 `install` 前後逐一相等。**目錄與符號連結另立口徑**：`install` 得為宣告面內的目標建立缺少的父目錄（目錄⛔ 無整檔摘要，故⛔ 不進摘要母體），除此之外⛔ 不建立、⛔ 不移除任何目錄；對任何符號連結⛔ 不建立、⛔ 不改寫、⛔ 不跟隨，其存在性與指向物在前後逐一相等。
- **登記的正確性以轉移性質陳述**（每次執行前後可測，⛔ 不依賴歷史事實）：每次 `install` 後，新增的 `framework-managed` 登記項集合逐字等於本次走分支 ① 落地的目標路徑集合；本次之前既有且合結構宣告的 `framework-managed`、`consumer-owned` 與 legacy 登記項一律逐字保留。`bootstrap` 同此：新增的 `consumer-owned` 登記項集合逐字等於本次建立或沿用的骨架路徑集合，本次之前既有的其餘登記項一律逐字保留。**⛔ 不得以「已落地物」這類樹上不可觀察的歷史事實定義對應的另一側**——那會使右側由左側定義、等式退化為恆真。
- **CI 來源資產與框架自身 `.github/workflows/ci.yml` 的同步是測試義務**，⛔ 不只是宣告：兩者的 `secret-scan` 與 `commit-trailer` 差異恰一處——consumer 側在該 job 的 `actions/checkout` 步驟的 `with:` 區塊內多一行逐字 `submodules: true`——其餘每一行逐字相等。該比對的母體是**兩個檔案**（各讀整檔），⛔ 不經任何片段解析器：consumer 來源資產自 `jobs:` 之後的全部位元組，去掉恰兩行 `submodules: true` 後，逐字等於 `ci.yml` 自 `jobs:` 之後的同長度前綴。`reachability` 與 `cli-tests` 兩個 job 檢查的是本 repo 自己的被測物，⛔ 進不了該前綴、⛔ 不進本條母體。`ci.yml` 是唯讀端。
- 帶 Python 消費點的 job 一併帶走該 job 的 `actions/setup-python` 步驟（`python-version: "3.14"`），否則下游會跑到 runner 內建的未釘選 `python3`；該步驟是上一條逐字相等的一部分，⛔ 不另立居所。
- `framework-version` 的彙整規則四條，**母體只含 `ownership`＝`framework-managed` 且⛔ 非 legacy 的項**（`consumer-owned` 項的 `pin` ⛔ 不進彙整）：`pin` 值集合基數為 1 ⇒ 與現行版本值比；基數 >1 ⇒ `fail`（理由列出排序後的全部相異值）；任一項缺 `pin` 或 `pin` 非非空字串 ⇒ `unknown`（理由列出缺項的路徑，⛔ 不以部分資料判 ok）；manifest 不存在或⛔ 不合下面的結構宣告 ⇒ `unknown`（⛔ 不 raise——preflight 是零寫入診斷，`core/verbs.md` §1 `snapshot` 列硬擋欄逐字為「—」）。
- **manifest 結構宣告**：可解析的 JSON ⛔ 不等於有效 manifest。下表逐列列出⛔ 不合法的形狀；命中任一列即整份 manifest 判為不可用，全部讀取端回固定理由並續跑、⛔ 不 raise。

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
| `control-path` | 某一項的 `path` 等於控制檔集合的成員路徑（控制檔⛔ 不自登記） |

## 3 · 五個 step

step 值域住 §0；`install` 與 `bootstrap` 的未完成項鍵集合住 §2。

- `install`：機械。把資產表宣告的框架資產自 rules source **整檔**落地到目標路徑，並寫 manifest（含 `source_commit`）。兩個分支見 §2；宣告集合以外的路徑零影響。
- `preflight`：機械、零寫入。印診斷清單恰七項：static 身分三項（`roots`、`repository`、`configured Project`）與 §1 的對帳四列，順序固定、逐列標 `ok`／`fail`／`unknown`。清單來源是 `_adopt` 層的單一常數，⛔ 不含資料相依的 `ModuleValidation.lines` 列。`verbs/main.py` 的三個 bootstrap 失敗入口印同一份項名清單，逐項狀態由該入口**實際已解析到**的取源決定、⛔ 不連坐。
- `bootstrap`：機械、冪等。建立採用專案自有的骨架（`.wf/modules.json` 種子、`.wf/stages/<階段>.md`）並把它們以 `consumer-owned` 登記進 manifest；已存在的路徑一律位元組不變、⛔ 不覆寫、⛔ 不合併，並各輸出一項 §2 鍵集合的未完成項。**登記面只收樹上那個名字本身的一般檔**：該路徑上有符號連結（leaf 自身是，含斷鏈；或其完整父路徑上任一段是）⇒ ⛔ 不登記，只交未完成項。零跟隨判準與 §2 `install`、§5 `deactivate` 是**同一個**，⛔ 不得三處各寫一套而讓同一形狀在 `install` 是零寫入、在 `bootstrap` 卻是登記——跟隨 leaf 連結取摘要等於把**指向物**的位元組登記成樹上那個名字的內容。種子的唯一機器可讀居所＝rules source 的 `.github/adopt/modules.seed.json`；CLI ⛔ 不以「文件內第 N 個 json 圍欄」或散文行首字串定位採用資料。種子的 `rules` 鍵寫入 bootstrap 當次解析到的 rules root（相對 project_root；規則就在 project_root 時寫 `null`），使同一棵樹上⛔ 不帶任何全域旗標的 `preflight` 解析到同一個 rules root。冪等的判準＝連跑兩次後樹的路徑集合與每個檔的內容摘要逐一相等（⛔ 不比對 mtime）。
- `smoke`：機械、零寫入。逐項印最小端到端檢查，每項標 `ok`／`fail`／`unknown`，並分**兩類**：（甲）機械可確認的安裝事實；（乙）須由 AI 判定的整合結果。（乙）類任一項**一律標 `unknown`、⛔ 不得標 `ok`**，並印出判定該項所需的證據種類，由執行者提出證據、查核者核對；CLI ⛔ 不得對採用者既有檔案內由 AI 整合的內容宣稱已驗證其正確性。
- `smoke` 取源 ID 的封閉字彙恰六個：`manifest.file`、`tree.assets`、`rules.version`、`config.file`、`rules.stages`、`tree.stages`；表外值⛔ 不得出現，每一個取源至少有一個消費項。**逐項獨立**——某一項的取源不可得⛔ 不得使另一項由可得變 `unknown`。取源宣告與實際相依的一致性是**測試義務**：其變異形狀清單與基線定義住卡面 `verification` 與 `cli/tests`，**⛔ 不住本檔**——規則本體是採用規則的居所、⛔ 不是測試矩陣的居所。

| 項名 | 類別 | 取源 ID |
|---|---|---|
| `adopt-manifest` | 甲 | `manifest.file` |
| `managed-assets` | 甲 | `manifest.file`、`tree.assets` |
| `version-pin` | 甲 | `manifest.file`、`rules.version` |
| `project-config` | 甲 | `config.file` |
| `stage-notes` | 甲 | `rules.stages`、`tree.stages` |
| `pending-integration` | 乙 | `manifest.file` |
| `legacy-entries` | 乙 | `manifest.file` |

- `adopt-manifest` 的語意恰為：控制檔存在且合 §2 結構宣告 ⇒ `ok`，否則⛔ 非 `ok`。它**⛔ 不比對控制檔自身的內容摘要**（§2 的控制檔具名宣告）。
- `managed-assets` 是**雙向**判準，母體＝§2 資產表宣告的目標路徑集合（**整檔**，⛔ 不含任何 legacy 項；基數由該表解析取得）。**母體⛔ 不因任何樹的狀態而收窄**——空母體、或以「manifest 內已登記者」定義母體皆⛔ 不允許。逐一成員的處置是對該母體的**全函數**，恰三種情形、⛔ 無第四種，且**每一個成員逐行印出它落在哪一種情形**（成員行在前、該項的狀態行在後）：
  - （甲-a）該路徑有 `framework-managed` 登記 ⇒ 必須在樹上存在且**整檔**摘要相符，任一方向⛔ 不成立 ⇒ 該成員 `fail`。
  - （甲-b）該路徑⛔ 無 `framework-managed` 登記且在樹上**⛔ 不存在** ⇒ 既未落地也未整合 ⇒ 該成員 `fail`。
  - （甲-c）該路徑⛔ 無 `framework-managed` 登記但在樹上**存在**（＝走過 §2 分支 ② 的零寫入）⇒ CLI ⛔ 不解析既有物的內部結構 ⇒ 該成員 `unknown`，該行逐字印「既有物・未登記・見 pending-integration」。**必要內容識別（CI 資產＝job 名）只有一個居所，即 `pending-integration`；本項⛔ 不自行重印 job 名。**
- 該項的狀態＝成員狀態的最劣者：任一成員 `fail` ⇒ `fail`；否則任一成員 `unknown` ⇒ `unknown`；全部成立才 `ok`。故 `ok` 逐字只承諾一件事——**母體每一項都由框架落地且整檔完好**；它⛔ 不承諾「採用者既有檔案內由 AI 整合的內容已被驗證」。（甲-c）成員同時由 `pending-integration` 承接「整合是否成功」這個**另一個問題**，該成員在兩項各出現一次。
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

停止使用框架時保留專案資料與歷史，CLI 只移除其有明確權限處置的資產。

- `deactivate` 前後全樹的差異恰**兩類**、⛔ 無第三類：**（一）** `ownership`＝`framework-managed` 的**整檔**登記路徑中，**樹上實際內容摘要與該登記項的 `digest` 相符者**消失；**（二）** §2 宣告的控制檔集合的路徑消失，及因此變空的 `.wf/adopt/` 目錄。控制檔由（二）**具名承接**，⛔ 不屬於「完全未登記的路徑」、⛔ 非經登記移除。**（一）與（二）兩個全稱一律以本節後述的封閉面、零跟隨與⛔ 非一般檔三條為例外**：那三條的域逐字含控制檔集合，⛔ 不得因（二）是具名承接就把它排在例外之外——否則「控制檔恆消失」會成為唯一一條可以刪到 project_root 之外的路徑。
- 其餘一律位元組不變：`consumer-owned` 登記路徑（含 `.wf/modules.json` 與 `.wf/stages/`）、legacy 登記項所指的承載檔、完全未登記的路徑，以及**摘要與登記項⛔ 不相符的 `framework-managed` 登記路徑**（＝採用者改過的框架檔），其存在性與內容摘要在 `deactivate` 前後逐一相等。
- 摘要⛔ 不相符者 CLI **⛔ 不刪除**，印一行並指向 `ADOPTION.md` §5，由執行者 AI 依證據處理、查核者核對結果：採用者改過的檔⛔ 不是框架有明確權限處置的資產（本節起首逐字「CLI 只移除其有明確權限處置的資產」）。
- CLI ⛔ 不對採用者既有檔案做任何內容移除或改寫。legacy 登記項與所有由 AI 整合進既有檔案的內容，只在輸出中逐項列出並指向 `ADOPTION.md` §5，由執行者 AI 依證據處理、查核者核對結果。
- 判準只看 manifest 的 `ownership` 欄與該路徑的**整檔摘要**，⛔ 不看路徑前綴、⛔ 不看副檔名：標成 `consumer-owned` 一律⛔ 不移除；標成 `framework-managed` 且摘要相符才移除。
- 刪除面封閉在 project_root 之內。**本條全稱的域＝移除面的全部路徑**，即上述（一）的 `framework-managed` 登記項 `path` 與（二）具名承接的**控制檔集合**兩者的聯集：控制檔⛔ 不在 `assets` 內登記自己（§2 方案 A）⇒ ⛔ 不得以「manifest 內任一項的 `path`」界定本條，那會把控制檔漏在封閉面之外、使它成為唯一一條⛔ 無封閉義務的刪除路徑。域內任一路徑解析後（含絕對路徑、`..`、經符號連結越出）⛔ 不在 project_root 之下時，該路徑⛔ 不刪除並印一行說明。封閉性看的是**那個名字落在哪裡**，處置的是**那個名字本身**：⛔ 不得以 `resolve()` 後的目標當處置對象，否則登記路徑是樹內符號連結時會刪到連結指向的⛔ 未登記 consumer 檔（樹內刪錯對象，⛔ 不是越界）。
- 移除面上的路徑（域同上條）**上有符號連結**時——leaf 自身是（含斷鏈），或其完整父路徑上任一段是——`deactivate` ⛔ 不移除它、⛔ 不跟隨它，印一行說明：解析後再刪是刪錯對象。該判準與上一條「刪除面封閉在 project_root 之內」是**兩條**判準，⛔ 不得以任一條冒充另一條。零跟隨判準與 §2 `install`、§3 `bootstrap` 所用的是**同一個**：三處⛔ 不得各寫一套，否則兩個動詞會對同一形狀給相反答案。
- 移除面上的路徑有既有物但**⛔ 非一般檔**（例：登記路徑被換成同名目錄）時⛔ 不刪除——框架只落整檔，而目錄⛔ 無整檔摘要——並印一行說明；該行**⛔ 不得宣稱那條路徑已不在樹上**。存在與否的判準與 §2 分支 ②、§3（甲-c）是**同一個**，⛔ 不以「讀得出整檔位元組」代替。
- 專案歷史（git、Issue、留言、Project）一律保留；停用框架⛔ 不等於刪除採用專案的任何紀錄。
- 未登記的路徑⛔ 不在 `deactivate` 的射程內：manifest 缺席或⛔ 不合 §2 結構宣告時該次執行零刪除，並印一行說明。
