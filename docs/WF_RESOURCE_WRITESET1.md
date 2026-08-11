# WF-RESOURCE-WRITESET1：資源宣告的互斥語意

> **本檔定位**：契約／設計卡，定義 `file:` 資源宣告的**寫入集** [write set] 相交語意、封閉的路徑語彙 [path namespace]、symlink 判定，以及 `assign` 的 revision 釘選與 TOCTOU 防護。
>
> **本檔不含實作**。`cli/src/wf_cli/resources.py` 與 `cli/src/wf_cli/commands/assign_cmd.py` 的改動歸衍生實作卡（§10）；`assign_cmd.py` 目前由 [#21](https://github.com/ruan6047/ai-workflow/issues/21) 佔用。§9 的回歸測試矩陣**在本卡定義、由衍生卡執行**。
>
> **spec 基線**：自 [#16](https://github.com/ruan6047/ai-workflow/issues/16) 設計文件 §7.2 切出，基準內容為 SHA `2d361303ce438c6fecf475b2aaa1fcbc06518dc9` 的 `docs/WF_ORCHESTRATION_RECONCILE1.md`。本檔對該節有四處實測修正，逐條列於 §11。

---

## 1. 問題陳述：既有權威用的詞是「寫入集」，實作用的是字串相等

本節**引用**既有權威，不另立分類。

- canonical `AI_WORKFLOW.md:145`：「共享可寫資源必須宣告並互斥：`file:<path>`、`port:<n>`、`container:<name>`、`db:<env>:schema`、`db:<env>:table:<name>`；read-only 才可共用。」
- `templates/control-plane-contract.md:49`：「派工前資源交集比對：〈命令；**比對本卡寫入集 × 現役卡寫入集**，撞則排隊。〉」

兩處權威講的都是**寫入集相交**。而 `cli/src/wf_cli/resources.py` 的 `find_conflicts` 實作為「完全相同字串才算撞（不做路徑前綴模糊比對，避免誤判）」。

**字串相等是寫入集相交的一個不完備代理** [incomplete proxy]。把代理當成 `assign` 的安全守衛，守衛就是宣稱而非保證。本卡的職責是讓兩者對齊——**不是發明新語意**。

### 1.1 現況實測

以下數字由 §9.6 的調查程式對 Project #4 的真實活卡產生，非人工聲明。

`open`／`amend` 對 `file:` 路徑目前**零語彙檢查**：`ResourceDeclaration` 只跑前綴正則 `^(file:.+|port:\d+|…)$`。實測全數接受——

| 送入的宣告 | 現況 |
|---|---|
| `file:../../etc/passwd` | 接受 |
| `file:/etc/passwd` | 接受 |
| `file:~/secrets` | 接受 |
| `file:**/*.py` | 接受 |
| `file:./a//b/../c` | 接受 |
| `file:cli/wfcli`（不存在的路徑） | 接受 |

`find_conflicts` 對三組應相交的輸入實測均回傳 `[]`（無衝突）：`file:templates/` × `file:templates/review-escalation.md`、`file:templates/` × `file:templates2/a.md`（此組**本就不該**相交，列此為對照）、`file:docs/A.md` × `file:docs/a.md`。

### 1.2 線上真實反例（本檔撰寫當下成立）

- **[#16](https://github.com/ruan6047/ai-workflow/issues/16) `WF-ORCHESTRATION-RECONCILE1`** 宣告 `file:templates/`，交付狀態 `↩退回`、owner 已指派 → **活卡**。
- **[#22](https://github.com/ruan6047/ai-workflow/issues/22) `WF-ESCALATION-DEFERRED-FINDINGS1`** 宣告 `file:templates/review-escalation.md`，交付狀態 `↩退回`、owner 已指派 → **活卡**。

兩者寫入集實際重疊（後者是前者的子路徑），現行檢查判無衝突，**兩張可同時派工**。

對 16 張活卡（已指派、非終態）做全對比對，三條規則的結果：

| 規則 | 同 repo 相交對數 | 跨 repo 相交對數 |
|---|---|---|
| A：現行字串相等 | **0** | 0 |
| B：立即階段（§8.1） | **1** | 0 |
| C：目標階段（§2） | **1** | 0 |

規則 A 在真實資料上找到 **0 個衝突**——守衛是睡著的。規則 B／C 各找到 **1 個**，且正是 #16 × #22。

### 1.3 另一組實證：宣告與實際寫入脫鉤

[#13](https://github.com/ruan6047/ai-workflow/issues/13) `WF-25-REVIEW-WRITE-CHANNEL1` 原宣告三個路徑，其中兩個**根本不存在**（`file:cli/wfcli` 實際為 `cli/src/wf_cli/`；`file:docs/handoff-contract.md` 實際在 `templates/`），而它真正的產出 `docs/WF-25-REVIEW-WRITE-CHANNEL1.md` **未被宣告**。第三個 `file:templates/dispatch-package.md` 被持有三天卻從未寫入，同期被別的卡實際寫過。

該宣告於 2026-08-11T20:14:31 由 PM **人工**發現並 `amend` 修正。**人工發現正是本卡要消滅的東西**。此案的處置見 §7。

---

## 2. 相交定義（驗收 1）

### 2.1 正規化：從資源字串到比對鍵

對一個已被 §3 接受的 `file:` 資源 `r`，定義其**比對鍵** [comparison key] `K(r)` 為一個**分量序列** [component sequence]：

1. 去除 `file:` 前綴，得原始路徑 `p`。
2. 以 `/` 切分 `p`，**捨棄空分量與 `.` 分量**（這摺疊了重複斜線與 `./`）。
3. 對每個分量做 Unicode **NFC** 正規化，再做 `casefold()`。
4. 結果即 `K(r)`，一個字串 tuple。

`p` 結尾是否有斜線**不影響 `K(r)`**；它只表達宣告意圖（目錄／檔案），用於 §3.4 的存在性提示與 §5 的 symlink 判定，**不參與相交判定**。理由見 §2.3 第三項。

### 2.2 相交謂詞

> **定義**：同一 repo 內的兩個 `file:` 資源 `x`、`y` **相交**，當且僅當 `K(x)` 與 `K(y)` 其中之一為另一之**前綴**（prefix，含相等）。
>
> 形式化：令 `n = min(len(K(x)), len(K(y)))`，則 `intersect(x, y) := K(x)[:n] == K(y)[:n]`。

**路徑邊界由「比對分量序列而非字串」自動保證**——這正是邊界判定的最簡形式：

- `file:templates/` 與 `file:templates/a.md` → `('templates',)` 是 `('templates', 'a.md')` 的前綴 → **相交** ✅
- `file:templates/` 與 `file:templates2/a.md` → `('templates',)` vs `('templates2', 'a.md')`，首分量 `templates ≠ templates2` → **不相交** ✅

不需要另加「邊界檢查」步驟；`templates` 與 `templates2` 是兩個不同的分量，字串層面的 `startswith` 陷阱在切分那一步就消失了。

### 2.3 這個謂詞是全函數 [total function]

**每一對已接受的宣告都恰好落在「相交」或「不相交」其一，沒有「其餘」格。** 三個容易被漏掉的輸入類別，逐一給出歸屬：

**(1) 兩者相等** → `K(x) == K(y)`，互為前綴 → 相交。

**(2) 只差大小寫**（`file:docs/A.md` vs `file:docs/a.md`）→ `casefold()` 後相等 → **相交**。

這是**刻意的 fail-closed 側**。git 索引是位元組精確的，兩者在 git 眼中是不同物件；但開發機的檔案系統實測為**大小寫不敏感**（macOS APFS 預設），兩張卡會寫到同一個檔案。判定必須服從「實際會被寫的是什麼」，不是「git 怎麼記」。

代價明說：在大小寫敏感的檔案系統上，這會**誤拒**兩個確實不同的檔案。誤拒的代價是排隊，漏放的代價是兩張卡同時寫同一檔——取前者。

**(3) 祖先未標目錄**（`file:templates` 無結尾斜線，vs `file:templates/a.md`）

**這是基線 §7.2 的「其餘」缺口。** 該節寫的是「其一為另一之**祖先目錄**」，預設了祖先方被宣告為目錄。但 `file:templates`（宣告為檔案）與 `file:templates/a.md` 是合法的一對輸入，而它落在該措辭之外——兩者對 `templates` 的型別認知矛盾，**且無法由字面判斷誰對**。

**本檔的處置**：相交判定**不看結尾斜線**，只看分量序列前綴。於是這一對判為**相交**（fail-closed 側）。矛盾的宣告本來就該擋下並要求宣告者澄清，而不是讓判定悄悄落進一個未定義的格子。

---

## 3. 封閉的 path namespace（驗收 2）

「正規化」若不封閉定義，等價規則就是下一個縫。**`file:` 的路徑語彙限定如下；不符者 `open`／`amend` 逕行拒收。**

### 3.1 語彙規則

| # | 規則 | 內容 | 理由 |
|---|---|---|---|
| 1 | **根** | 一律為**卡所屬 repo 根**的相對路徑 | 見 §4 的 repo 歸屬限定詞 |
| 2 | **絕對路徑** | 拒收以 `/` 起始者 | 逸出 repo 根，相交判定失去共同座標 |
| 3 | **家目錄** | 拒收以 `~` 起始者 | 同上，且展開結果依執行者而異 |
| 4 | **`..`** | 拒收任一分量為 `..` 者 | `..` 使「前綴關係」不可由字面判定 |
| 5 | **萬用字元** | 拒收含 `*` 或 `?` 者 | 見 §3.2 |
| 6 | **正規化** | 空分量與 `.` 分量在 `K(r)` 中被捨棄（§2.1）；**不拒收**，逕行摺疊 | 排版差異不是語意差異 |
| 7 | **結尾斜線** | 有＝目錄宣告，無＝檔案宣告。**不參與相交判定**（§2.3-3），用於 §3.4 與 §5 | 目錄／檔案之別是意圖，須被記錄但不得成為判定漏洞 |
| 8 | **大小寫** | 宣告以位元組原樣**儲存**；**比對**時 casefold（§2.3-2） | 儲存要忠實，比對要 fail-closed |
| 9 | **Unicode** | 比對前做 **NFC** 正規化 | 見 §3.3 |
| 10 | **symlink** | 依 §5 拒收 | git 索引已可判定，不得以殘餘風險打發 |
| 11 | **空路徑** | 拒收去除 `file:` 後為空、或正規化後 `K(r)` 為空者（如 `file:/`、`file:.`、`file:./`） | 「整個 repo」不是可互斥的宣告單位；要宣告全 repo 請逐一列出頂層目錄 |

**規則 11 是封閉性的關鍵**：沒有它，`file:.` 會正規化成空序列，而空序列是**所有**序列的前綴——一張卡就鎖死整個 repo，且是靜默發生的。

**每個輸入字串恰好落在「接受」或「拒收」其一**：規則 2–5、11 是拒收條件的**完整列舉**，任何不觸發其中之一的字串即被接受並可計算 `K(r)`。沒有第三種結果。

### 3.2 萬用字元：實測修正基線的規則

基線 §7.2 寫「glob／萬用字元：拒收」，未指明字元集。若照直覺實作成「拒收 `*`、`?`、`[`、`]`」，**會誤拒 41 個現存的真實檔案**——cpbl-analytics 的 Next.js 動態路由目錄，例如 `web/src/app/games/[sno]/page.tsx`。而 `UX-WINPROB-CURVE-MIGRATE1` 已宣告 `file:web/`，其寫入集**確實涵蓋這 41 個檔案**。

實測（兩 repo 全部追蹤路徑）：含 `*` 者 **0** 個、含 `?` 者 **0** 個、含 `[` 者 **41** 個。

**裁定**：
- 拒收 `*` 與 `?`。
- **不拒收 `[` 與 `]`**，視為普通字元。
- 明訂：**資源字串在任何消費端都不得被 glob 展開，一律以字面路徑處理。**

相交判定本來就純字面，`[` 對正確性毫無影響；`*` 之所以要拒收，不是因為判定會出錯，而是因為**寫 `file:src/**/*.py` 的人意圖是一個模式，而字面處理會使它匹配不到任何真實檔案，靜默地少保護**。這個危害只由 `*`／`?` 產生。

殘餘風險：有人寫 `[abc]` 意圖字元類別，得到的是字面目錄名，靜默少保護。由 §7 的存在性提示攔截——該路徑字面上不存在，提示會響。

### 3.3 Unicode 正規化：不是假設性問題

cpbl-analytics 有 **25 個非 ASCII 追蹤路徑**（如 `docs/reference/棒球規則.txt`、`docs/research/ML-PITCHER-ER-REBUILD1/cases/stratum_多算_差1分_兩者皆有.md`），而 `ML-WP-ROLLWIN1` 宣告 `file:docs/research/`、`RESEARCH-REASON-RESTATE1` 宣告該目錄下的具名檔案。**CJK 路徑在宣告涵蓋範圍內是實況。**

macOS 的 APFS 對檔名做正規化不敏感比對：NFC 與 NFD 形式指向同一檔案。git 則位元組精確。因此**同一個檔案可以有兩種位元組表示，落在兩張卡的宣告裡而判定看不見**——與大小寫是同一類漏洞。

**裁定**：比對前一律 NFC 正規化（§2.1 步驟 3），與 casefold 併用。

實測註記：現存的 CJK 路徑全為漢字，漢字無組合字分解，NFC 與 NFD 相同，故**今天此規則不改變任何判定**。它針對的是帶變音符號的拉丁字母與諺文等未來可能出現的分量。**現在就定，因為它免費，而且事後補會需要重掃全部歷史宣告。**

### 3.4 拒收時機：`open`／`amend`，不是派工時

拒收發生在**寫入卡面時**——**壞的宣告根本進不了系統**，比事後比對安全。

`assign` 仍會**重跑**同一套語彙檢查（防範繞過 CLI 直接編輯 Issue body 的情形），但那是縱深防禦，不是第一道門。

**遷移負債為零**：實測 Project #4 全部非終態卡的 `file:` 宣告，觸犯規則 2–5、11 者 **0 筆**。此規則可即刻全面生效，不需要豁免期、不需要 legacy 旗標。

---

## 4. repo 歸屬限定詞（基線未涵蓋，實測發現）

### 4.1 問題

規則 1 說路徑是「repo 根的相對路徑」。但 `assign` 的比對集合是 **Project #4 的全部活卡**，而 Project #4 **跨兩個 repo**：

| repo | 非終態卡 | 其中已指派 |
|---|---|---|
| `ruan6047/ai-workflow` | 10 | 7 |
| `ruan6047/cpbl-analytics` | 44 | 11 |

資源字串**不帶 repo 限定詞**，於是 `find_conflicts` 把兩個 repo 的 repo-相對路徑放在同一個平面比。基線 §7.2 談的「跨 repo 路徑拒收」處理的是**宣告一個外部 repo 的路徑**，與此處**兩張卡分屬不同 repo** 是不同的問題——後者在基線中完全沒有出現。

危害是雙向的：`file:docs/` 在兩個 repo 都存在（實測皆有 `docs/`），一張 cpbl 卡宣告 `file:docs/` 會與五張 ai-workflow 設計卡的 `file:docs/WF_*.md` 判為相交——**跨 repo 誤拒**；反之兩張真的同 repo 撞車的卡若被誤判為異 repo，則是漏放。

目錄宣告使誤拒的爆炸半徑顯著放大，因此**採用 §2 的定義會讓這個缺口比現在更痛，不是更輕**。

### 4.2 裁定

> **相交判定只在同一 repo 內進行。** 兩張卡的資源，若其所屬 repo 不同，一律**不相交**（`port:` / `container:` / `db:` 資源不適用此限定，見 §4.3）。
>
> **repo 歸屬的來源**：卡的 Issue 所在 repo，由 Project item 的 `issue_url` 解析。
>
> **無法判定歸屬者 fail-closed**：Project item 若為 DraftIssue（無 `issue_url`）而其宣告含任何 `file:` 資源，`assign` **拒絕派工**，要求先轉為真 Issue。

**今日誤拒為 0，是運氣不是設計**：§1.2 的表顯示跨 repo 相交對數為 0——那只是因為目前兩 repo 的活卡路徑碰巧不重疊。實測 DraftIssue 持有 `file:` 宣告者 **0 筆**，故此規則亦可即刻生效、零遷移負債。

### 4.3 為何 `port:`／`container:`／`db:` 不受此限定

它們是**主機層級或環境層級**的資源，不隸屬任何 repo：兩個 repo 的卡搶同一個 `port:4001` 是真的搶。repo 限定詞只加在 `file:` 上。

`db:` 資源另受 canonical §4.1「read-only 才可共用」約束，該規則已在現行 `find_conflicts` 實作，本卡**不修改**它。

---

## 5. symlink（驗收 3）

### 5.1 git 索引已經知道，不需要工作樹

把 symlink 列為「殘餘風險」的前提是「解析需要工作樹存在且與宣告時一致」。**那個前提是錯的**：git 以檔案模式 `120000` 在 tree 中記錄 symlink，`git ls-tree` 讀得到，不需要 checkout。既然機械可判定，就不該用殘餘風險打發。

> **規則 T（tracked）**：宣告路徑的**任一祖先分量或自身**，在目標 revision 的 tree 中模式為 `120000` 者，`open`／`amend`／`assign` **拒收**，並提示改宣告該 symlink 的 target 路徑。

### 5.2 必須逐分量查，不能整條查

實測（scratch repo：`alias -> real`，`real/c.md` 為普通檔）：

- `git ls-tree -r HEAD` 列出 `120000 blob … alias` — 模式可見 ✅
- `git ls-tree HEAD -- alias/c.md` → **空**。**git 不穿越 tree 中的 symlink。**
- `git ls-tree HEAD -- real/new.md`（不存在的路徑）→ **也是空**。

**兩者的空無法區分。** 因此檢查必須是**逐分量的前綴走查**：對 `a/b/c`，依序查 `a`、`a/b`、`a/b/c`——

| 分量查詢結果 | 判定 |
|---|---|
| 模式 `120000` | **拒收**（規則 T） |
| 模式 `040000`（tree） | 繼續走下一分量 |
| 模式 `100644`／`100755`（blob）**且後面還有分量** | **拒收**：宣告在普通檔之下開子路徑，結構上不可能（§7.2） |
| 模式 `100644`／`100755` 且為最後一分量 | 接受（既存檔案） |
| 查無此分量 | **停止走查**，此處即「最深既存祖先」；後續分量視為「將要新增」，接受（存在性提示見 §7） |

走查在第一個查無的分量處終止——這與 §6.2 realpath 解析「解析到最深既存祖先」是同一形狀，兩者可共用同一個走查器。

### 5.3 未追蹤 symlink 也要檢查

把未追蹤 symlink 劃出範圍的理由通常是「資源宣告是 repo 檔案的契約」。**該理由不成立**：`assign` 當下 worktree 就在眼前，未追蹤的 symlink 確實可以讓兩張卡的實際寫入落到同一個檔案。**寫入集是實際會被寫的東西，不是 git 追蹤與否。**

> **規則 U（untracked）**：`assign` 對每個宣告路徑，在 `--worktree` 中另做實際路徑檢查：
>
> 1. **逐層解析**（含未追蹤 symlink）得到 realpath；路徑尚不存在時解析到**最深的既存祖先**為止。
> 2. **containment**：realpath（或該最深既存祖先的 realpath）必須仍在 worktree 根的 realpath 之內。逸出者**拒絕派工**。
> 3. **交集比對取字面與 realpath 的聯集**：以 `K(字面路徑)` 與 `K(realpath 相對於 worktree 根)` 兩組鍵各跑一次 §2.2，**任一命中即相交**（fail-closed 側）。

containment 檢查必須在**解析後**做，且 worktree 根本身也要先 realpath 化——否則 `/var` → `/private/var` 這類系統層 symlink 會製造假逸出。

### 5.4 明確不涵蓋

**派工之後才被建立的未追蹤 symlink。** 那超出任何派工時檢查的能力，屬執行期紀律，**不宣稱涵蓋**。

實測註記：ai-workflow 目前追蹤的 `120000` 項目 **0 筆**，故規則 T 今日不拒收任何現存宣告。

---

## 6. revision 釘選與 TOCTOU（驗收 4）

symlink 可能在宣告之後才被加入，故 `assign` 於派工當下重跑 §5 的檢查。**「當時的 revision」必須釘死，不能只寫「當時」。**

### 6.1 釘選

1. `assign` 先把 `--worktree` 的 `HEAD` 解析為**完整 40 hex commit SHA**，記為 `resource_check_rev`。
2. `resource_check_rev` **寫入 assign 事件**，使該次檢查事後可原樣重放。
3. §5.1 的 tracked symlink 檢查與 §2 的交集比對**都對 `resource_check_rev` 進行**，不對「分支尖端」這種會動的東西。

### 6.2 TOCTOU 防護

> **解析 SHA、跑檢查、寫入 assign 三者在同機原子目錄鎖** [atomic directory lock] **內完成**（canonical `AI_WORKFLOW.md:147`：「本機可採原子目錄鎖」；該鎖的取得／釋放語意歸 [#23](https://github.com/ruan6047/ai-workflow/issues/23)）。
>
> **寫入前重讀 `HEAD`**；若已非 `resource_check_rev`，**放棄本次派工**並要求重跑，不得帶著過期的檢查結果寫入。

放棄而非重試：重試迴圈在 `HEAD` 持續變動時不保證終止，而放棄是有界的，且失敗訊息會把「你的 worktree 在派工途中動了」這件事講明。

**鎖保護不到的部分，明說**：鎖是同機的。`assign` 對 Project／Issue 的寫入是遠端的，遠端側的併發由 [#23](https://github.com/ruan6047/ai-workflow/issues/23) 的事件排序與冪等機制承擔。本卡**不宣稱**解決兩台機器同時 `assign` 同一張卡——那需要遠端 CAS，不在射程內（§12）。

---

## 7. 「宣告的路徑是否存在」該不該檢查（本卡新增的裁定）

§1.3 的 #13 案顯示：兩個不存在的路徑進了系統、活了三天、由人工發現。**問題該問的是「檢查存在性能不能解決它」，而不是「既有實作沒檢查所以不檢查」。**

### 7.1 裁定：不硬拒，強制機械提示

> **硬拒：否。** **`open`／`amend` 必須輸出機械化的存在性提示：是。**

**硬拒為什麼是錯的**：允許目錄宣告的既有理由是「只有目錄宣告能表達『我會在這裡新增檔案』」（需求方 2026-08-11 裁定）。而**檔案宣告一個尚不存在的檔案，是同一個行為**——「我將建立這個檔案」。

決定性的反例是本卡自己：`docs/WF_RESOURCE_WRITESET1.md` 在 [#24](https://github.com/ruan6047/ai-workflow/issues/24) 開卡當下並不存在。硬拒存在性**會拒絕掉定義這條規則的那張卡**。同期的 [#25](https://github.com/ruan6047/ai-workflow/issues/25)（`docs/WF_CLEANUP_GUARD1.md`）、[#23](https://github.com/ruan6047/ai-workflow/issues/23)（`docs/WF_EVENT_IDEMPOTENCY1.md`）同樣如此。

**存在性不是區分好壞宣告的判準**：#13 的 `file:cli/wfcli` 與本卡的 `file:docs/WF_RESOURCE_WRITESET1.md`，在「路徑不存在」這件事上**完全相同**。區分兩者的是**意圖**（打錯字 vs 將要建立），而意圖不可機械判定。以存在性硬拒，就是用一個不相干的判準砍掉一整個合法類別——正是本 repo 反覆被抓到的「分類漏了一整類輸入」的鏡像。

**fail-closed 不受損**：不存在的宣告是**過度宣稱**（鎖住沒人需要的東西），不是**少宣稱**。它的代價是別人排隊，不是兩張卡同時寫同一檔。方向是安全的。

**提示為什麼是對的**：§5.2 的逐分量走查**已經要跑**，走查終止在最深既存祖先——「還有幾個分量沒走到」是那次走查的**免費副產品**。零額外成本，而它在最便宜的時刻（寫入卡面時）攔下打錯的路徑。

> **提示的機械形式**（`open`／`amend`，不阻擋）：對每個 `file:` 宣告，若 `resource_check_rev` 的 tree 中不存在該路徑，輸出該路徑、其最深既存祖先，以及該祖先下**名稱相近的既存項目**（供打錯字比對）。目錄宣告與檔案宣告一視同仁。

以 #13 重放：`file:cli/wfcli` 的最深既存祖先是 `cli/`，其下既存項目含 `src/`、`tests/`、`README.md`——沒有 `wfcli`。提示會把這件事講出來，而 PM 不必在三天後人工發現。

### 7.2 一個確實該硬拒的子情形

> 走查中若某分量為 blob（模式 `100644`／`100755`）**而宣告仍有後續分量**，`open`／`amend` **拒收**。

在普通檔案之下開子路徑結構上不可能，不存在「將要建立」的解讀。機械可判定、無偽陽性。

**誠實聲明：這一條抓不到 #13。** `cli/wfcli` 不是 blob，它整個不存在。#13 靠的是 §7.1 的提示，不是這一條。列出它是為了讓走查的每一種輸出都有歸屬（§5.2 表格的封閉性），不是為了宣稱解決了 #13。

### 7.3 真正對應 #13 病灶的機制，及其歸屬

#13 的傷害有兩半：**(a)** 持有 `templates/dispatch-package.md` 三天卻從未寫入；**(b)** 實際寫入 `docs/WF-25-REVIEW-WRITE-CHANNEL1.md` 卻未宣告。

**存在性檢查只碰到 (a) 的一個弱代理，完全碰不到 (b)。** (b) 是宣告的**反方向**失效——寫了沒宣告的東西——而那才是互斥保證真正被打穿的方向。

對應的機制是**事後對帳**：在 `handoff`／`review` 時，比對該卡分支的 `git diff --name-only <base>..<head>` 與其資源宣告，**任一實際改動落在宣告之外即 fail-closed**。這完全機械、雙向覆蓋，且是本問題真正的槓桿點。

**歸屬**：本卡**不定義**它——它的觸發點在 `handoff`／`review` 而非 `assign`，與本卡「派工前守衛」的射程不同，且需要 base SHA 的語意（歸 [#23](https://github.com/ruan6047/ai-workflow/issues/23) 的事件契約）。**列為建議新卡，記在 §12 非目標，不靜默夾帶。**

---

## 8. 兩階段落地，兩階段都機械（驗收 5）

**過渡期最容易寫成「在實作到位前由 PM 人工執行 fail-closed」——那不算設計完成。** 每一條規則都要有機械執行者；人工紀律不是。

### 8.1 兩個階段

兩階段**共用 §2.1 的正規化**，差別只在前綴測試施加在哪個層次：

| 階段 | `find_conflicts` 的相交謂詞 | 性質 |
|---|---|---|
| **立即**（衍生卡落地前） | 對 `'/'.join(K(x))` 與 `'/'.join(K(y))` 做**字串**前綴測試 | **過度拒絕**，fail-closed |
| **目標**（衍生卡 L） | 對 `K(x)` 與 `K(y)` 做**分量序列**前綴測試（§2.2） | 語意精確 |

立即階段是**同一個謂詞降一個抽象層**：字串前綴不看分量邊界，於是 `templates` 是 `templates2/a.md` 的字串前綴 → 誤判相交。目標階段比對分量序列 → `templates ≠ templates2` → 正確判不相交。

### 8.2 立即階段是 fail-closed 的證明

**命題**：`intersect_B ⊇ intersect_C`（B 抓到的是 C 的超集，故 B 不會漏放 C 會抓的）。

**證明**：若 `K(x)` 是 `K(y)` 的分量前綴，則 `'/'.join(K(y))` 等於 `'/'.join(K(x))` 接上 `'/'` 再接上剩餘分量，故前者是後者的字串前綴。反向同理。∎

實測驗證（9 個案例，含 #16 × #22、邊界、冗餘 `./`、重複斜線、大小寫、祖先未標目錄、Next.js 中括號、CJK 檔名）：**B 漏放 C 的例數 = 0**。

### 8.3 基線的立即階段規格有 fail-open 漏洞（實測修正）

基線 §7.2 寫的是：「保留現行字串相等，另加樸素前綴比對：任一方為**目錄宣告**時，若對方**字串**以其起始即判相交」——即對**原始字串**（保留結尾斜線）操作，不先正規化。

**實測該規格有 5 個漏放案例**：

| 案例 | C 目標階段 | 基線字面版 B | 判定 |
|---|---|---|---|
| `file:./templates/` × `file:templates/a.md` | 相交 | **不相交** | 漏放 |
| `file:templates//` × `file:templates/a.md` | 相交 | **不相交** | 漏放 |
| `file:Templates/` × `file:templates/a.md` | 相交 | **不相交** | 漏放 |
| `file:templates` × `file:templates/a.md` | 相交 | **不相交** | 漏放 |
| `file:docs/A.md` × `file:docs/a.md` | 相交 | **不相交** | 漏放 |

**基線宣稱立即階段「過度拒絕但 fail-closed」，實測是 fail-OPEN。** 且基線舉的過度拒絕例子（`templates/` 誤撞 `templates2/a.md`）在其自身規格下**也不成立**——因為 `"templates2/a.md".startswith("templates/")` 為 `False`（結尾斜線擋住了）。基線的立即階段既沒有它宣稱的安全性，也沒有它宣稱的代價。

**修正**：立即階段必須先跑 §2.1 正規化（含去除 `.`／空分量、NFC、casefold、忽略結尾斜線），再做字串前綴測試。如此 5 個漏放全數消失，而基線宣稱的過度拒絕**真的出現**（`templates` 是 `templates2/a.md` 的字串前綴 → 誤判相交）。

### 8.4 立即階段對「尚未拒收」的非法宣告怎麼辦

立即階段先於 §3 的拒收落地，故仍可能遇到含 `..`／絕對路徑／`*`／`?` 的既有宣告，而這些字串**無法正規化**（`..` 使前綴關係無定義）。

> **裁定**：立即階段遇到無法正規化的 `file:` 宣告時，視該資源與對方卡的**每一個** `file:` 資源皆相交。

fail-closed、有界、且會製造修正該宣告的壓力。實測現存觸犯者 **0 筆**，故此分支今日不會被走到——但它必須存在，否則謂詞在該輸入上無定義（又一個「其餘」格）。

### 8.5 過度拒絕行為必須被測試釘住

立即階段的誤拒（`templates` × `templates2/a.md`）是**刻意的設計取捨**，不是 bug。它必須在 §9 的矩陣中以**斷言相交為真**的形式明確固定，並附註「此為立即階段的預期行為，目標階段才改為不相交」——否則日後會有人把它當成 bug 修掉，而修掉的方式極可能是移除正規化，於是 §8.3 的 5 個漏放全部回來。

---

## 9. 回歸測試矩陣（驗證 1、2）

**矩陣在本卡定義，執行歸衍生實作卡**（§10）。每列須為可獨立執行的斷言。

### 9.1 相交定義（§2）

| # | x | y | 目標階段 | 立即階段 | 要點 |
|---|---|---|---|---|---|
| 1 | `file:templates/` | `file:templates/review-escalation.md` | 相交 | 相交 | **#16 × #22 真實反例** |
| 2 | `file:templates/` | `file:templates2/a.md` | **不相交** | **相交** | 邊界；立即階段的過度拒絕（§8.5） |
| 3 | `file:templates/` | `file:templates` | 相交 | 相交 | 目錄／檔案宣告同路徑 |
| 4 | `file:templates` | `file:templates/a.md` | 相交 | 相交 | 祖先未標目錄（§2.3-3） |
| 5 | `file:docs/A.md` | `file:docs/a.md` | 相交 | 相交 | 純大小寫差異（§2.3-2） |
| 6 | `file:./templates/` | `file:templates/a.md` | 相交 | 相交 | 冗餘 `./`；基線漏放案（§8.3） |
| 7 | `file:templates//` | `file:templates/a.md` | 相交 | 相交 | 重複斜線；基線漏放案 |
| 8 | `file:Templates/` | `file:templates/a.md` | 相交 | 相交 | 大小寫＋目錄；基線漏放案 |
| 9 | `file:a/b/c.md` | `file:a/b/d.md` | 不相交 | 不相交 | 同目錄不同檔，不得誤撞 |
| 10 | `file:web/src/app/games/[sno]/` | `file:web/src/app/games/[sno]/page.tsx` | 相交 | 相交 | 中括號視為字面（§3.2） |
| 11 | `file:docs/reference/` | `file:docs/reference/棒球規則.txt` | 相交 | 相交 | CJK 分量（§3.3） |
| 12 | `file:port:8080` 形式的 `port:8080` × `port:8080` | — | 相交 | 相交 | 非 `file:` 資源沿用字串相等，未被本卡改動 |

**另須斷言 `intersect_B ⊇ intersect_C`**：對第 1–11 列，凡目標階段判相交者，立即階段必須也判相交（§8.2 的機械化證明）。

### 9.2 封閉 namespace 的拒收（§3）

| # | 輸入 | `open`／`amend` | 規則 |
|---|---|---|---|
| 13 | `file:../outside.md` | **拒收** | 3.1-4 |
| 14 | `file:a/../b.md` | **拒收** | 3.1-4（`..` 在中段） |
| 15 | `file:/etc/passwd` | **拒收** | 3.1-2 |
| 16 | `file:~/secrets` | **拒收** | 3.1-3 |
| 17 | `file:src/**/*.py` | **拒收** | 3.1-5 |
| 18 | `file:a?.md` | **拒收** | 3.1-5 |
| 19 | `file:web/src/app/games/[sno]/page.tsx` | **接受** | 3.2：中括號不得誤拒 |
| 20 | `file:docs/reference/棒球規則.txt` | **接受** | 3.3：CJK 不得誤拒 |
| 21 | `file:./a//b/c.md` | **接受**，`K` = `('a','b','c.md')` | 3.1-6：摺疊非拒收 |
| 22 | `file:.` ／ `file:./` ／ `file:/` | **拒收** | 3.1-11：空 `K` 會鎖死全 repo |
| 23 | `file:docs/A.md` | **接受**，body 內原樣保存大小寫 | 3.1-8：儲存忠實 |

**另須斷言**：對 Project #4 全部非終態卡的現存宣告跑規則 2–5、11，拒收數為 **0**（零遷移負債，§3.4）。此斷言須由程式列舉產生，不得人工聲明。

### 9.3 repo 歸屬（§4）

| # | 情境 | 期望 |
|---|---|---|
| 24 | 兩張 ai-workflow 卡，`file:docs/x.md` × `file:docs/` | 相交 |
| 25 | 一張 ai-workflow 卡 `file:docs/x.md` × 一張 cpbl 卡 `file:docs/` | **不相交** |
| 26 | 兩張不同 repo 的卡，`port:4001` × `port:4001` | **相交**（§4.3） |
| 27 | DraftIssue（無 `issue_url`）持有 `file:` 宣告 → `assign` | **拒絕派工** |
| 28 | 現存活卡中 DraftIssue 持 `file:` 宣告者 | 計數為 **0**（列舉產生） |

### 9.4 symlink（§5）

| # | 情境 | 期望 |
|---|---|---|
| 29 | tracked symlink `alias -> real`，宣告 `file:alias/c.md` | **拒收**（規則 T，逐分量命中 `alias`） |
| 30 | tracked symlink 自身，宣告 `file:file_alias.md` | **拒收**（規則 T，末分量即 `120000`） |
| 31 | 同上，但以 `git ls-tree HEAD -- alias/c.md` 單次查詢 | 回傳**空** — 固定「不可整條查」這個事實（§5.2） |
| 32 | 不存在的路徑 `file:real/new.md` | **接受**；走查終止於 `real`；存在性提示觸發（§7.1） |
| 33 | blob 之下開子路徑 `file:real/c.md/x.md` | **拒收**（§7.2） |
| 34 | untracked symlink `u -> ../outside`，宣告 `file:u/x.md`，`assign` | **拒絕派工**（規則 U-2，realpath 逸出 worktree） |
| 35 | untracked symlink `u -> real`，卡 A 宣告 `file:u/c.md`、卡 B 宣告 `file:real/c.md` | **相交**（規則 U-3，realpath 聯集命中） |
| 36 | worktree 根本身位於系統 symlink 下（如 `/tmp` → `/private/tmp`） | **不得**判為逸出（§5.3 末：根須先 realpath 化） |
| 37 | 宣告路徑不存在，其最深既存祖先在 worktree 內 | containment 對該祖先判定，通過 |

### 9.5 revision 釘選與 TOCTOU（§6）

| # | 情境 | 期望 |
|---|---|---|
| 38 | `assign` 成功 | assign 事件含 `resource_check_rev`，且為完整 40 hex |
| 39 | 檢查期間 `HEAD` 未變 | 正常寫入 |
| 40 | 檢查後、寫入前 `HEAD` 變動 | **放棄派工**，不寫入任何欄位，錯誤訊息指明 revision 已變 |
| 41 | 以事件中的 `resource_check_rev` 重放 §5.1 檢查 | 得到與當時相同的結果 |
| 42 | 解析、檢查、寫入三步 | 均在同一次原子目錄鎖持有期間內 |
| 43 | `--worktree` 指向 detached HEAD | `HEAD` 仍可解析為 40 hex，正常運作 |

### 9.6 真實資料調查（生成式證據）

**驗證 1 要求納入 #16／#22 真實反例，本節使其可重跑。** 下列程式對 Project #4 的活卡跑三條規則並輸出對照；衍生卡須將其納入 repo（需 `amend` 擴充資源宣告）並在 CI 或交付報告中附上輸出。

```python
# 對 Project #4 活卡跑 A/B/C 三規則，輸出同 repo 與跨 repo 的相交對數。
# 依賴：wf_cli（gh CLI 已登入）
import re, unicodedata
from itertools import combinations
from wf_cli.card import is_owner_assigned
from wf_cli.gh import default_runner
from wf_cli.project import list_items, resolve_project
from wf_cli.resources import try_parse_block

TERMINAL = {"🏁完成", "🛑已停止"}

def key(r):                                   # §2.1
    comps = [c for c in r[len("file:"):].split("/") if c not in ("", ".")]
    return tuple(unicodedata.normalize("NFC", c).casefold() for c in comps)

def rule_a(x, y): return x == y                                   # 現行
def rule_b(x, y):                                                 # 立即（§8.1）
    a, b = "/".join(key(x)), "/".join(key(y))
    return a.startswith(b) or b.startswith(a)
def rule_c(x, y):                                                 # 目標（§2.2）
    a, b = key(x), key(y); n = min(len(a), len(b))
    return a[:n] == b[:n]

project = resolve_project(default_runner, "ruan6047", 4)
cards, unparseable = [], []
for it in list_items(default_runner, project):
    if not it.card_id or (it.delivery_status or "") in TERMINAL: continue
    if not is_owner_assigned(it.owner_field): continue
    decl = try_parse_block(it.body)
    if decl is None:
        unparseable.append(it.card_id); continue
    m = re.match(r"https://github\.com/([^/]+/[^/]+)/issues/", it.issue_url or "")
    cards.append((it.card_id, m.group(1) if m else None,
                  [r for r in decl.resources if r.startswith("file:")]))

print("無法解析的活卡：", unparseable or "無")
for name, rule in (("A 現行", rule_a), ("B 立即", rule_b), ("C 目標", rule_c)):
    same = cross = 0
    for (c1, r1, f1), (c2, r2, f2) in combinations(cards, 2):
        if any(rule(x, y) for x in f1 for y in f2):
            if r1 == r2 and r1 is not None: same += 1
            else: cross += 1
    print(f"{name}：同 repo {same} 對；跨 repo {cross} 對")
```

**撰寫當下的輸出**（16 張活卡）：規則 A 同 repo 0 對；規則 B 與 C 各 1 對，即 `WF-ORCHESTRATION-RECONCILE1` × `WF-ESCALATION-DEFERRED-FINDINGS1` 於 `file:templates/` ~ `file:templates/review-escalation.md`。跨 repo 皆 0 對。

> **立即後果**：本節生效後，#22 在 #16 進入終態或 `amend` 其資源宣告前**不得派工**——即使現行實作判它們不衝突。**實作現況不等於契約應然**，而本卡的職責正是讓兩者對齊。

---

## 10. 歸屬

契約語意（§2–§8）定義在本卡。實作歸衍生卡（基線 §9-L）：

- `resources.py`：§2.1 正規化、§2.2 相交謂詞、§3 語彙拒收、§4 repo 限定詞、§8 兩階段。
- `open_cmd.py`／`amend_cmd.py`：§3.4 拒收時機、§5.1 tracked symlink 逐分量走查、§7.1 存在性提示。
- `assign_cmd.py`：§5.3 realpath 與 containment、§6 revision 釘選與 TOCTOU、§4.2 DraftIssue fail-closed。
- 測試：§9 全部 43 列＋三項列舉式斷言。

**排程限制**：`assign_cmd.py` 目前由 [#21](https://github.com/ruan6047/ai-workflow/issues/21) 佔用（宣告 `file:cli/src/wf_cli/commands/assign_cmd.py`），衍生卡須待其釋放。`resources.py` 目前**無活卡佔用**，故 §8.1 的立即階段可先行落地——這正是兩階段切分的實務價值。

---

## 11. 對基線 §7.2 的修正（逐條）

本檔非基線的重述，有四處實測修正與兩處補完。

| # | 基線 §7.2 的內容 | 本檔的處置 | 依據 |
|---|---|---|---|
| 1 | 立即階段「過度拒絕但 fail-closed」，對原始字串做前綴 | **修正**：實測有 5 個漏放案例，為 fail-OPEN；且其舉的過度拒絕例在自身規格下不成立。改為先正規化再做字串前綴 | §8.3 |
| 2 | 「glob／萬用字元：拒收」 | **修正**：直覺實作會誤拒 41 個現存 Next.js 動態路由檔案。收窄為只拒 `*`／`?`，並明訂消費端不得 glob 展開 | §3.2 |
| 3 | 相交＝「其一為另一之**祖先目錄**」 | **修正**：`file:templates`（未標目錄）× `file:templates/a.md` 落在該措辭之外。改為分量序列前綴，不看結尾斜線 | §2.3-3 |
| 4 | 未提及比對集合跨 repo | **補完**：Project #4 含兩個 repo 共 54 張非終態卡，`file:` 相交須加 repo 限定詞 | §4 |
| 5 | 未提及 Unicode 正規化 | **補完**：25 個現存 CJK 追蹤路徑落在活卡宣告涵蓋範圍內；macOS 正規化不敏感 | §3.3 |
| 6 | 未提及空路徑 | **補完**：`file:.` 正規化後為空序列，是所有序列的前綴，會靜默鎖死全 repo | §3.1-11 |
| 7 | 「宣告路徑是否存在」未提及 | **新增裁定**：不硬拒、強制提示；真正對應的機制是宣告×實際 diff 對帳，列非目標 | §7 |
| 8 | symlink 檢查未指明查詢方式 | **補完**：實測 git 不穿越 tree symlink，整條查與「路徑不存在」不可區分，必須逐分量走查 | §5.2 |

### 11.1 與 canonical 的一致性（驗證 3）

本檔**引用而非另立**：

- canonical `AI_WORKFLOW.md:145` 的資源前綴列舉（`file:`／`port:`／`container:`／`db:`）**未被本卡修改**。本卡只定義 `file:` 的相交語意，`port:`／`container:` 沿用字串相等，`db:` 沿用「read-only 才可共用」。
- `control-plane-contract.md:49` 的「比對本卡**寫入集** × 現役卡寫入集」——本卡使 `find_conflicts` 真的計算寫入集相交，**該行文字不需修改**。這是實作向契約靠攏，不是契約向實作讓步。
- 「現役」的定義（含 `📦已合併` 未收尾者，canonical §4.4）**未被本卡修改**；現行 `assign` 的活卡判準（非終態＋已指派）沿用不動。

> **本檔不修改任何 canonical 條文。** 若跨家族查核認為 §4 的 repo 限定詞屬 canonical `:145` 的語意擴充而非澄清，該判斷應退回並另走契約修訂 PR——本檔對此**不自行認定**。

---

## 12. 非目標與邊界（明說不涵蓋）

1. **派工之後才建立的未追蹤 symlink**（§5.4）。屬執行期紀律。
2. **跨主機併發 `assign`**（§6.2）。原子目錄鎖是同機的；遠端 CAS 不在射程內。
3. **宣告 × 實際寫入的事後對帳**（§7.3）。這是 #13 病灶的真正對應機制，觸發點在 `handoff`／`review`，**建議另開卡**，本檔不夾帶。
4. **`db:` 資源的相交語意**。沿用 canonical §4.1，未改動。
5. **活卡的定義**。沿用現行 `assign`，未改動。
6. **無法解析的資源宣告被靜默略過**——見 §12.1，本檔提出但不裁定。

### 12.1 邊界發現：無法解析的宣告目前 fail-open

**這是超出本卡五條驗收的發現，明列於此供需求方與查核者裁定，不靜默夾帶。**

現行 `assign_cmd.py` 對**別卡**解析失敗的宣告只警告、不擋（`try_parse_block` 回 `None` → `skipped_unparseable`）。實測今日有 **2 張已指派活卡**落在此列：`INIT-GAME-RECAP`、`ML-FIELD-OF1`。本卡自己的 `assign` 執行時即印出該警告。

這與 [#24](https://github.com/ruan6047/ai-workflow/issues/24) 卡面「服務的原始目標」寫的「**任何無法安全判定的情形一律拒絕派工而非放行**」**直接衝突**——無法解析正是「無法安全判定」的原型。

`assign_cmd.py` 的註解為此給了理由：遷移期舊卡尚未補宣告，不該讓新卡整個卡死。**該理由在 cutover 當時成立，但它是一個沒有到期日的 fail-open**，且今日仍有 2 張。

**建議的形狀**（不在此裁定）：預設 fail-closed，並提供 `--ignore-unparseable CARD-A,CARD-B` 的具名逃生門——把靜默的 fail-open 換成一次明示、可稽核、且必須逐張具名的行為。守衛的**預設**不再依賴任何人記得，而豁免留下痕跡。今日只需具名 2 張，代價有界。

**本檔不將其納入 §9 矩陣，亦不指派給衍生卡**——它超出本卡驗收射程，須由需求方明示納入後才動。

---

## 13. 執行者揭露

- 本檔為設計／契約文件，**無程式碼變更、無 CI**。§9 的矩陣**未被執行**，執行歸衍生卡。
- §1.1、§1.2、§3.2、§3.3、§4.1、§8.2、§8.3、§9.6 的所有數字，均由對真實 repo 與真實 Project #4 執行的探查程式產生，非人工清點。§9.6 的程式已內嵌於本檔，可重跑。
- §5.2 的 git symlink 行為以一個臨時 scratch repo 實測，該 repo 未進入本 repo；重現步驟即 §9.4 第 29–33 列。
- 撰寫過程中一項自查修正值得記錄：初次以 `git ls-files | grep -P '[^\x00-\x7F]'` 探查非 ASCII 路徑，得到「兩 repo 皆無」的**錯誤**結論——`git ls-files` 預設對非 ASCII 路徑做 C-style 八進位引號。改用 `-c core.quotePath=false` 後查出 25 筆。§3.3 因此從「不需要」翻轉為「需要」。**探查工具的預設值本身就是一個可以說謊的來源。**
