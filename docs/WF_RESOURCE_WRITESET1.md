# WF-RESOURCE-WRITESET1：資源宣告的互斥語意

> **本檔定位**：契約／設計卡，定義 `file:` 資源宣告的**寫入集** [write set] 相交語意、封閉的路徑語彙 [path namespace]、symlink 判定，以及 `assign` 的 revision 釘選與 TOCTOU 防護。
>
> **本檔不含實作**。`cli/src/wf_cli/resources.py` 與 `cli/src/wf_cli/commands/assign_cmd.py` 的改動歸衍生實作卡（§10）；`assign_cmd.py` 目前由 [#21](https://github.com/ruan6047/ai-workflow/issues/21) 佔用。§9 的回歸測試矩陣**在本卡定義、由衍生卡執行**。
>
> **spec 基線**：自 [#16](https://github.com/ruan6047/ai-workflow/issues/16) 設計文件 §7.2 切出，基準內容為 SHA `2d361303ce438c6fecf475b2aaa1fcbc06518dc9` 的 `docs/WF_ORCHESTRATION_RECONCILE1.md`。本檔對該節的修正與補完逐條列於 §11（該表即完整清單）。
>
> **貫穿全檔的不變式**：派工守衛的每一站，對每一個它無法安全判定的輸入，必須以「阻擋」或「一次性、具名、留痕的豁免」結束——**不得有任何路徑以「略過並繼續」結束**（§8.6）。§2–§7 逐節論證各自謂詞的全函數性，§8.6–§8.9 論證謂詞**之外**的管線各站。

---

## 1. 問題陳述：既有權威用的詞是「寫入集」，實作用的是字串相等

本節**引用**既有權威，不另立分類。

- canonical `AI_WORKFLOW.md:145`：「共享可寫資源必須宣告並互斥：`file:<path>`、`port:<n>`、`container:<name>`、`db:<env>:schema`、`db:<env>:table:<name>`；read-only 才可共用。」
- `templates/control-plane-contract.md:49`：「派工前資源交集比對：〈命令；**比對本卡寫入集 × 現役卡寫入集**，撞則排隊。〉」

兩處權威講的都是**寫入集相交**。而 `cli/src/wf_cli/resources.py` 的 `find_conflicts` 實作為「完全相同字串才算撞（不做路徑前綴模糊比對，避免誤判）」。

**字串相等是寫入集相交的一個不完備代理** [incomplete proxy]。把代理當成 `assign` 的安全守衛，守衛就是宣稱而非保證。本卡的職責是讓兩者對齊——**不是發明新語意**。

### 1.1 現況實測

以下數字由 §9.7 的調查程式對 Project #4 的真實活卡產生，非人工聲明。

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

對已指派、非終態的活卡做全對比對（2026-08-11 重跑：17 張，其中 15 張宣告可解析、2 張不可解析——後者見 §8.7），三條規則的結果：

| 規則 | 同 repo 相交對數 | 跨 repo 相交對數 |
|---|---|---|
| A：現行字串相等 | **0** | 0 |
| B：立即階段（§8.1） | **1** | 0 |
| C：目標階段（§2） | **1** | 0 |

規則 A 在真實資料上找到 **0 個衝突**——守衛是睡著的。規則 B／C 各找到 **1 個**，且正是 #16 × #22。

**張數是快照，結論不是**：活卡集合逐日變動（R1 交付當時為 16 張），查核者重跑會看到不同張數。**另有 2 張活卡因宣告無法解析而完全未進入這張表**——這正是 §8.7 要處理的洞：**比對表上看不見的卡，才是守衛最大的盲區**。

> **⚠️ 這個線上反例已於 2026-08-12 消失（R3 重跑實測，非推測）。** #16 的卡面異動軌跡逐字記錄：`2026-08-12T00:13:42+08:00 amend by wf-cli（op df7e0929）`，把宣告從 `["file:docs/WF_ORCHESTRATION_RECONCILE1.md", "file:templates/"]` 收窄為單一檔案，理由是「本卡自開卡至今從未寫入 `templates/` 底下任何檔案……該目錄級宣告在階層路徑包含語意下與 `WF-ESCALATION-DEFERRED-FINDINGS1` 相交，等於整張卡的生命週期都在擋別人而一次也沒用到」。因此 §9.7 於 **2026-08-12 01:28 +0800** 重跑得到規則 B／C **0 對**（見該節）。
>
> **這不削弱本卡的論證，但它修正了上一版的一句話。** 上一版寫「不變的是結論：規則 B／C 找到 #16 × #22」——那句話把一個**線上狀態**誤當成不變量，而線上狀態當然會變。被斷言的不變量只有兩件，且都不依賴線上資料：(a) 對**固定輸入**，A 判不相交而 B／C 判相交（§9.1 第 1 列＋§9.8 離線窮舉，兩者把這對路徑凍結成語料）；(b) 現行守衛在**任何**時點的真實活卡上都不曾判出 `file:` 階層相交。#16 × #22 的角色是「這個缺口曾在線上真實成立」的**歷史舉證**，其證據是上引的 amend 軌跡與本節，不是每日可重跑的普查。
>
> 附帶一提，消失的**原因**恰好是本契約的預期出路：§9.7 的「立即後果一」寫的是「#22 在 #16 進入終態或 `amend` 其資源宣告前不得派工」，而 #16 的 amend 理由逐字援引了本檔定義的階層包含語意。**契約在成文階段就已經改變了它所描述的世界**——這對本卡是好消息，對「拿線上快照當證據」則是一記警告。

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

### 3.1 語彙規則（**只管卡面 `file:` 資源宣告，不管 CLI 路徑引數**）

> **定義域界線（跨卡裁決，記錄於此以免被誤引）**：本節的封閉 namespace 規範的是**寫在卡面資源宣告區塊裡的 `file:` 資源字串**，其消費端是相交判定（§2）；拒收時機是 `open`／`amend`（§3.4）。
>
> 它**不是**一個通用的路徑正規化器，**明確不涵蓋 CLI 的路徑引數**（如 `--worktree <path>`、指向檔案的命令參數）。兩者定義域不相容：資源宣告必須是 repo 根的相對路徑，才能有共同座標可比（§3.1-1、§4）；而 CLI 引數必須解析到執行當下的**真實檔案系統位置**，因此絕對路徑與 `~` 在那裡是合法且必要的——本節第 2、3 條把它們拒收，正是因為在**宣告**的定義域裡它們會使相交判定失去座標。**把本節的規則套到 CLI 引數上會是錯誤引用**；引數的正規化歸 [#23](https://github.com/ruan6047/ai-workflow/issues/23)，與本卡無語意衝突。

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

> **相交判定只在同一 repo 內進行。** 兩張卡的資源，若其所屬 repo **經正向確立**且不同，一律**不相交**（`port:` / `container:` / `db:` 資源不適用此限定，見 §4.3）。
>
> **repo 歸屬的來源**：卡的 Issue 所在 repo，由 Project item 的 `issue_url` 以 `https://github.com/<owner>/<repo>/issues/` 解析。
>
> **歸屬必須正向確立，否則不得套用此限定**（此限定是**放行方向**的規則——它把本來會相交的兩張卡判為不相交，因此它的前提必須被證明，不能被假定）：
>
> - **別卡歸屬無法確立**（DraftIssue 無 `issue_url`，或 `issue_url` 不符上述形狀）：**不套用 repo 限定詞**，逕行以 §2 比對，即**視同與本卡同 repo**。誤拒的代價是排隊，漏放的代價是兩張卡同寫一檔——取前者。
> - **本卡自身歸屬無法確立**且其宣告含任何 `file:` 資源：`assign` **拒絕派工**，要求先轉為真 Issue。本卡的歸屬是整個比對平面的座標原點，座標未定時整個比對沒有意義，退回「視同同 repo」也救不了。

**今日誤拒為 0，是運氣不是設計**：§1.2 的表顯示跨 repo 相交對數為 0——那只是因為目前兩 repo 的活卡路徑碰巧不重疊。**這個限定詞遲早會真的擋掉某次誤拒，也就遲早會真的放行某一對；它的正確性完全依賴歸屬判定不出錯，所以上面兩條把「判不出來」導向 fail-closed 側，而不是導向「歸屬不同」。** 實測 Project #4 全部有卡 ID 的 item 中，`issue_url` 無法解析出 `owner/repo` 者 **0 筆**（由 **§9.7b** 的探針列舉產生——上一版誤標為 §9.7，而 §9.7 只掃已指派活卡，涵蓋面較窄，此處要的是全 item），故此規則可即刻生效、零遷移負債。

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

## 8. 落地與守衛完整性：兩階段都機械，且無靜默放行（驗收 5）

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

實測驗證（9 個案例，含 #16 × #22、邊界、冗餘 `./`、重複斜線、大小寫、祖先未標目錄、Next.js 中括號、CJK 檔名）：**B 漏放 C 的例數 = 0**。此結論另由 §9.8 的**文件內嵌、離線可重跑**窮舉程式獨立重現（23 條語料、276 組合，`b_misses_c = 0`）——證明從「一次性腳本的口頭數字」升級為「查核者可原樣重跑的 artifact」。

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

### 8.6 不變式 I：守衛管線不得有靜默放行

§8.4 已經處理了一個「謂詞在某類輸入上無定義」的格子。**但那只是謂詞層。真正的漏洞在謂詞之前**：`assign` 是一條管線，謂詞只是其中一站，而**前面每一站都可能失敗，而失敗的預設處置歷來是「略過」**。略過一張活卡，等於把它的寫入集當成空集合——這比謂詞判錯更嚴重，因為它讓那張卡在守衛眼中根本不存在。

> **不變式 I**：派工守衛的**每一站**，對它**無法安全判定**的每一個輸入，必須以「**阻擋**」或「**一次性、具名、留痕的豁免**」二者之一結束。**不得有任何路徑以「略過並繼續」結束。**

管線逐站的處置表。**「現行」欄是實測，不是推測**；「本檔裁定」欄凡標 ★ 者為本檔新增：

| 站 | 無法安全判定的輸入 | 現行行為 | 本檔裁定 | 依據 |
|---|---|---|---|---|
| S1 | **本卡**宣告解析失敗 | 拒絕派工（exit 2） | 維持，並由 §9.6 釘住不得回退 | 現行 `assign_cmd.py` |
| S2 | **別卡**宣告解析失敗 | **略過該卡、只印警告** → **fail-open** | ★ **阻擋派工**，輸出 card id 與解析錯誤原文；唯一出路是 §8.8 的具名豁免 | §8.7 |
| S3 | **本卡** repo 歸屬無法確立 | 無此檢查 | ★ 拒絕派工 | §4.2 |
| S4 | **別卡** repo 歸屬無法確立 | 無此檢查（歸屬根本未被使用） | ★ 不套用 repo 限定詞，視同同 repo 比對 | §4.2 |
| S5 | 路徑語彙非法（`..`／glob／絕對／`~`／空） | 全數接受 | `open`／`amend` 拒收；`assign` 重跑同套檢查 | §3 |
| S6 | 立即階段遇到尚未被 S5 攔下的非法宣告 | 不適用（立即階段尚未落地） | 視為與對方每個 `file:` 資源皆相交 | §8.4 |
| S7 | tracked symlink 走查所需的 `git ls-tree` 查詢失敗（`resource_check_rev` 不存在、repo 損壞、非零 exit） | 無此檢查 | ★ **拒絕派工**。查詢失敗與「查無此分量」**必須分開處置**——後者是合法的「將要新增」，前者是資訊缺失 | §5.2 |
| S8 | realpath 解析拋 `OSError`（symlink 迴圈、權限不足） | 無此檢查 | ★ **拒絕派工**。不得以「解析不到就當它不存在」略過 | §5.3 |
| S9 | `HEAD` 無法解析為 40 hex，或檢查後、寫入前變動 | 無此檢查 | 放棄本次派工 | §6 |
| S10 | 資源字串不符四種前綴 | 正則已拒（`ResourceDeclarationError`） | 維持；此錯誤在 S1／S2 上浮 | 現行 `resources.py` |

**S7 的分開處置值得單獨強調**，因為 §5.2 已經證明 git 對「tree 中的 symlink 之下」與「路徑不存在」回傳**同樣的空**——那是查詢**成功**但結果為空。若把「查詢**失敗**」也塞進同一格，三種語意就被壓成一種，而其中兩種是安全的、一種不是。

### 8.7 R1-001 裁定：無法解析的資源宣告 fail-closed

**這是 R1 查核的 blocking finding。前一版把它列在 §12 非目標「提出但不裁定」——那個處置本身就是不變式 I 的違例：把一個已知的 fail-open 標記為「不處理」，等於用文件把靜默放行合法化。本節裁定它。**

#### 8.7.1 為什麼那兩張卡解析不了（先查證，再修法）

實測結論由 §9.7b 的普查程式產生：

- Project #4 有卡 ID 的 item **96 張**，宣告無法解析 **33 張**。
- 33 張**全數**帶 `<!-- state-plane-mig1:card_id=… -->` marker，即 `OPS-STATE-PLANE-MIG1` 一次性遷移寫入的卡。
- 帶 `<!-- resource-claims:begin -->` sentinel 卻仍解析失敗者：**0 張**。
- 因此**「無法解析」與「MIG1 遷移佔位卡」在今日的資料上是同一個集合**，母體外的解析失敗數為 **0**。

失敗的**近因**是：遷移寫出的區塊形狀與 CLI 的 `render_block` 不同——它是

````text
## 資源宣告（機器可讀；`null`／`[]` 代表未正式宣告，不代表無資源）
```json
{ "db_scope": null, "resources": [] }
```
````

**有 fenced JSON，但沒有 `resource-claims` sentinel 對**。卡首另有一行「派工時由 PM 補資源宣告區塊」——遷移**知道**自己寫的不是正式宣告，並把補齊的責任交給了人。

**所以答案是三者皆非**：不是宣告缺漏（區塊在）、不是格式舊到不可辨（JSON 合法）、也不是解析器太嚴——**是遷移刻意寫了一個自我標示為「未正式宣告」的佔位符，而「補齊」這一步從未被機械強制**。§1.3 的 #13 是「宣告寫錯了」，這 33 張是「宣告從未存在」，兩者是同一個病灶的兩端：**都由人工紀律承接，也都失守了**。

#### 8.7.2 因此「放寬解析器」是陷阱，不是修法

直覺的修法是讓解析器也接受這個舊形狀。**實測顯示那會製造一個比現況更糟的 fail-open**：

- 母體 33 張的佔位 `db_scope` 分佈實測為 `'none'` 11、`'read'` 10、`'write'` 8、`'schema'` 1、`null` 3。**30/33 的值落在封閉列舉內**——放寬 sentinel 比對後，這 30 張會**解析成功**，得到 `resources: []`。
- 而該區塊的標題**逐字寫著**「`null`／`[]` 代表未正式宣告，**不代表無資源**」。放寬解析＝把「寫入集未知」轉譯成「寫入集為空」，且**不再有任何警告**——守衛會安靜地認為這 30 張卡不碰任何檔案。

現況的略過至少還印警告；放寬後連警告都沒有。**寬鬆化會把一個吵鬧的 fail-open 換成一個安靜的 fail-open。**

補充一筆同向證據：母體內有 1 張（`DEV-REVIEW-PREFLIGHT-GATE1`）的 `resources` 陣列裡混進了一個**卡 ID** `DEV-REVIEW-DEACCEPT-TRAIL1`，不符任何資源前綴。手寫宣告會漂移成什麼形狀，這就是實例。

> **裁定 A**：**解析器不放寬。** `parse_block` 的嚴格性是正確的——它忠實回報「這裡沒有可信的宣告」。缺口在**閘門**，不在解析器。
>
> **裁定 B**：`assign` 對**別卡**解析失敗，**一律拒絕派工**（與現行對本卡的處置一致），錯誤訊息須逐張列出 **card id ＋ 解析錯誤原文**，並指明唯一出路是「替該卡補上正式宣告」或「§8.8 的具名豁免」。`skipped_unparseable` 這條只印警告就放行的路徑**移除**。

**立即後果**（實測，非推測）：今日 `assign` 任何一張卡都會被 `INIT-GAME-RECAP`、`ML-FIELD-OF1` 兩張擋下，除非具名豁免。這正是 fail-closed 應有的痛感——**它把「有兩張活卡的寫入集是未知的」這個事實，從一行沒人讀的警告變成一次擋下**。

### 8.8 具名豁免機制：具名、可稽核、到期

裁定 B 若沒有逃生門，會在補完 33 張卡之前卡死整個派工。但逃生門本身不能是新的 fail-open。**形狀**：

> ```
> wfcli assign … --ignore-unparseable <CARD-ID>[,<CARD-ID>…]
> ```

#### 8.8.1 具名

- **逐張列出 card id**。不接受 `*`、`all`、空字串、前綴萬用、或「略過全部」語意。名單中未列到的解析失敗卡**仍然擋**。
- **只對本次 `assign` 生效**，不寫入任何持久設定檔、不讀環境變數。**沒有一個可以被打開後遺忘的開關**——這是「臨時措施變成永久 fail-open」的標準病灶，此處以「無處可存」在結構上排除。
- **封閉母體限定**：只有母體成員可被具名。母體外的解析失敗**硬阻擋、不可豁免**——那代表 CLI 自己寫出的宣告壞了，是 bug，不是遺產。

  **母體的定義必須是凍結的名單，不是對 body 的謂詞。** 直覺做法是「body 帶 `state-plane-mig1:card_id=` marker 且不帶 sentinel」，但 **body 可以被任何人在 GitHub 網頁上手改**（§3.4 已為此把 `assign` 的語彙檢查設為縱深防禦），於是任何新卡只要貼上那行 marker 就能取得豁免資格——**謂柢式母體不是封閉的**。
  
  > **裁定**：衍生卡須把 §9.7b 於**釘選日期**列舉出的 card ID 逐一寫成 CLI 內的**字面常數清單**（今日為 33 個）。母體＝該清單 ∩「仍無法解析」∩「不帶 sentinel」∩「未註冊 worktree」。清單是原始碼，加名字要走 PR 與查核；貼 marker 進 body 不再能取得資格。marker 判準降為**交叉檢查**：清單內但 marker 不在者，同樣拒絕豁免並報告不一致。
- **無 worktree 限定**：被具名的卡，其「分支worktree」欄必須為空（未註冊／`—`）。已註冊 worktree 代表它真的在執行，「寫入集未知」的風險是實的，此時**不可豁免**。實測母體 33 張中已註冊 worktree 者 **0 張**（§9.7b），故此限定今日零成本，而它封住了豁免最危險的用法。

#### 8.8.2 可稽核

- 每次使用，把 **(a)** 被豁免的 card id 逐張、**(b)** 各自的解析錯誤原文、**(c)** 執行者、**(d)** `resource_check_rev`，寫入 assign 事件的 log 行。豁免因此與派工本身同壽命、可事後盤點「這半年豁免過幾次、豁免了誰」。
- **陳舊豁免即錯誤**：名單中若有一張其實**解析得出來**的卡，`assign` **拒絕**並要求把它從名單移除。這條把「名單只會被加、不會被刪」這個熵增方向反轉成強制收縮。
- `doctor`（唯讀）須輸出**當前母體殘量**與**距 sunset 的天數**。殘量從 33 走向 0 的過程因此在觀測面上是可見的，而不是靠誰記得。

#### 8.8.3 到期：三層，每層都機械

「暫時」「過渡期」之所以會變成永久，是因為它們沒有終止條件。這裡給三個，且**都不依賴任何人記得**：

**E1 — 母體在釘選當下就封頂，且以原始碼固定。** 成員清單是字面常數（§8.8.1），**上界固定為 33，且增長路徑只有「改原始碼並過 PR」一條**——不是「在結構上不可能」，而是「不可能靜默發生」。這是誠實的強度：任何以 body 內容為依據的封閉性都會被手改 body 打穿，而原始碼常數不會。

**E2 — 單調收縮，且收縮由使用行為驅動。** 任一張卡經 `amend` 補上正式宣告後即帶 sentinel 且可解析，**永久離開母體**（成員判準含「仍無法解析」，離開後無法回頭）。加上 §8.8.2 的「陳舊豁免即錯誤」，名單被強迫跟著母體縮。母體大小非遞增且每次補宣告嚴格遞減 → **程序有限步終止**。

**E3 — 硬性 sunset 日期。** E1＋E2 保證母體不會變大，**不保證它會變小**——沒有人被強制去補那 33 張。因此再加一層純機械的截止：

> CLI 內建常數 **`UNPARSEABLE_EXEMPTION_SUNSET = 2026-09-30`**。系統日期超過該日後，`--ignore-unparseable` **一律拒絕**，不看名單內容、不看母體殘量。到期後唯一出路是補上正式宣告。

該日期是**契約值，定在本檔**：需求方要改，改的是這一行，而不是散落在程式裡的某個判斷。衍生卡須把它落成單一常數並由測試釘住（§9.6 第 50 列）。**選 2026-09-30 的理由**：距本檔撰寫日約七週，而今日真正被擋的只有 2 張、母體 33 張全部無 worktree，補宣告的工作量有界且不阻塞任何執行中的卡。

**E3 的代價明說**：若到期時母體仍非空且那些卡仍是活卡，**全 Project 的 `assign` 會硬停**。這是刻意的——一個「到期後自動放寬」的截止不是截止。停下來的成本是可見且可立即解除的（補宣告即可），而繼續 fail-open 的成本是不可見的。**兩者都不舒服，但只有一個會被人注意到。**

**E3 不防的事**：改系統時鐘、或直接改那個常數。前者不在任何 CLI 的威脅模型內；後者要過 PR 與查核，與 E1 同性質——**可稽核，不是不可能**。

#### 8.8.4 豁免仍是 fail-open，只是有界——明說

豁免的語意是「我知道這張卡的寫入集未知，我仍然派工」。**這是真的放行，不是安全的放行。** 它與現況的差別在四件事，每一件都機械：它必須被逐張打出來（不可能不知情）、它留痕（可事後盤點）、它的母體封頂且單調收縮（有界）、它有硬到期日（會結束）。

**一個必須被點名的錯誤修法**：有人會發現 `INIT-GAME-RECAP`（owner 為「子卡依 v1.3 藍圖推進」）與 `ML-FIELD-OF1`（owner 為「ruan6047（Design Gate）」）根本不是執行中的卡，而想去收緊 `is_owner_assigned` 讓它們掉出比對集合。**那是把 fail-open 偽裝成清理**——縮小比對集合的每一步都在減少會被抓到的衝突，而它會順手把未來真正該被比對的卡也一起排除。活卡定義沿用現行（§12-5），**要改必須另開卡並以「這會漏掉什麼」為驗收**，不得夾帶在本卡。

### 8.9 仍未關閉的 fail-open 殘留（本檔明列，不宣稱已解決）

不變式 I 保證的是**守衛管線內部**沒有靜默放行。以下四項在管線之外，本檔**不宣稱**涵蓋：

1. **豁免本身**（§8.8.4）。有界、留痕、有到期，但確實是放行。
2. **`[abc]` 被寫成字元類別的意圖**（§3.2）。判定是確定的（字面），但**宣告的意義與宣告者的意圖可能不同**，於是靜默少保護。它不是「無法判定」，而是「判定了，但判的不是他想說的」——與 §3.2 那 41 個 Next.js 動態路由檔案是同一個字面處理規則的兩面：規則保住了那 41 個，代價是無法分辨誰在寫模式。§7.1 的存在性提示會對不存在的字面路徑響，但那是**提示**，不是閘門。
3. **宣告與實際寫入脫鉤**（§7.3）。上一項與 §1.3 的 #13 都是它的實例。真正的機制是 `handoff`／`review` 時比對 `git diff --name-only` × 資源宣告，**歸另一張卡**（§12-3）。**本檔的守衛只能保證「宣告的東西不撞」，保證不了「宣告的就是會寫的」。**

   **R3 補一筆同向實證，且它使這一項更緊迫、不是更輕**：#16 於 2026-08-12 收窄宣告的 `amend` 理由，逐字引用了 `git diff --name-only origin/main` 只有一個檔案、從未寫入 `templates/`（§1.2）。**那正是本項所指的對帳，只是由需求方用眼睛做的**——與 §1.3 的 #13「由 PM 人工發現」是同一個形狀的第二個實例。兩次都靠人抓到，代表機制有效且必要，也代表**它仍然完全沒有機械執行者**。本輪修的是 §9.7b 的可攜性，與本項無關，**故本項維持原狀不作任何弱化**：宣告 × 實際寫入的對帳在本卡射程之外，R3 沒有推進它一寸。
4. **派工之後才建立的未追蹤 symlink**（§5.4）、**跨主機併發 `assign`**（§6.2）。

第 2、3 兩項共用同一個根因，也共用同一個解——**事後對帳**。本檔把它們指向同一張建議新卡，而不是各自發明半套機制。

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
| 25 | 一張 ai-workflow 卡 `file:docs/x.md` × 一張 cpbl 卡 `file:docs/`（兩者歸屬皆已確立） | **不相交** |
| 26 | 兩張不同 repo 的卡，`port:4001` × `port:4001` | **相交**（§4.3） |
| 27 | **目標卡自身**為 DraftIssue（無 `issue_url`）且持有 `file:` 宣告 → `assign` | **拒絕派工**（§4.2） |
| 28 | 現存活卡中 DraftIssue 持 `file:` 宣告者 | 計數為 **0**（列舉產生） |
| 28a | **別卡**歸屬無法確立（DraftIssue，或 `issue_url` 不符 `…/<owner>/<repo>/issues/` 形狀），路徑會相交 | **相交**——不套用 repo 限定詞，視同同 repo（§4.2；**不得**判為跨 repo 而放行） |
| 28b | 全 Project item 的 `issue_url` 無法解析出 `owner/repo` 者 | 計數為 **0**（列舉產生，§9.7b） |

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

### 9.6 無法解析的宣告、具名豁免、管線其餘各站與探針自檢（§8.6–§8.8、§9.9）

| # | 情境 | 期望 |
|---|---|---|
| 44 | 別卡宣告無法解析，未給 `--ignore-unparseable` | **拒絕派工**；訊息逐張列出 card id ＋解析錯誤原文（§8.7-B） |
| 45 | **本卡**宣告無法解析 | **拒絕派工**（現行行為；本列的作用是釘住它不得被回退） |
| 46 | `--ignore-unparseable A,B`，A、B 皆在封閉母體且無 worktree 註冊，且解析失敗的恰為 A、B | 放行；assign 事件記下 A、B 的 card id、各自解析錯誤、執行者、`resource_check_rev`（§8.8.2） |
| 47 | 解析失敗的是 A、B，但名單只列 A | **仍拒絕**，並指名 B |
| 48 | 名單含一張其實解析得出來的卡（陳舊豁免） | **拒絕**，要求移除該名字（§8.8.2） |
| 49 | 名單含一張**不在封閉母體字面清單**的卡（帶 sentinel 但 JSON 壞） | **拒絕**：母體外一律不可豁免（§8.8.1） |
| 49a | 一張**新**卡的 body 被手動貼入 `state-plane-mig1:card_id=` marker 後具名豁免 | **拒絕**：母體是原始碼中的字面清單，貼 marker 不能取得資格（§8.8.1／E1） |
| 49b | 卡在字面清單內，但 body 已無 MIG1 marker | **拒絕豁免**並報告清單與 body 不一致（交叉檢查，§8.8.1） |
| 50 | 系統日期 > `UNPARSEABLE_EXEMPTION_SUNSET`（2026-09-30） | `--ignore-unparseable` **一律拒絕**，不看名單內容（§8.8.3-E3） |
| 51 | 名單含一張母體成員，但其「分支worktree」欄已註冊 | **拒絕**：已在執行者不可豁免（§8.8.1） |
| 52 | 母體成員經 `amend` 補上正式宣告後 | 永久離開母體（body 帶 sentinel，成員判準不再命中）；再具名它即觸發第 48 列 |
| 53 | `--ignore-unparseable` 給 `*`／`all`／空字串 | **拒絕**：只接受逐張 card id（§8.8.1） |
| 54 | 現存無法解析卡的普查 | **33 張全數落在 MIG1 封閉母體、母體外 0 張、帶 sentinel 卻失敗 0 張**（列舉產生，§9.7b） |
| 55 | `git ls-tree` 對 `resource_check_rev` 查詢**失敗**（rev 不存在／非零 exit） | **拒絕派工**；不得與「查無此分量」（合法的「將要新增」）同格處置（§8.6-S7） |
| 56 | realpath 解析拋 `OSError`（symlink 迴圈、權限不足） | **拒絕派工**；不得當成「路徑不存在」略過（§8.6-S8） |
| 57 | 本檔 §9.9 的自檢落成 repo 內腳本並掛 CI，對本檔執行 | 退出碼 **0**；且對**人為植入**「f-string 取值部含反斜線」與「刪去一個探針區塊」兩種變異，退出碼 **非 0**（變異測試——只驗 PASS 的自檢等於沒驗，§9.9.2 已示範反向案例） |

**另須斷言**：`assign` 的程式路徑中**不存在**任何「解析失敗 → 記錄後 `continue`」的分支（`skipped_unparseable` 已移除）。此為結構性斷言，衍生卡須以測試覆蓋第 44 列的**退出碼**而非僅訊息文字。

### 9.7 真實資料調查（生成式證據）

**驗證 1 要求納入 #16／#22 真實反例，本節使其可重跑。** 下列程式對 Project #4 的活卡跑三條規則並輸出對照，同時盤點 §8.7 的 fail-closed 阻擋名單；衍生卡須將其納入 repo（需 `amend` 擴充資源宣告）並在 CI 或交付報告中附上輸出。**唯讀，不寫入任何狀態面。**

```python
# §9.7 對 Project #4 活卡跑 A/B/C 三規則 + 無法解析宣告的 fail-closed 盤點。
# 依賴：wf_cli（gh CLI 已登入）。唯讀。
import re, unicodedata
from itertools import combinations
from wf_cli.card import is_owner_assigned
from wf_cli.gh import default_runner
from wf_cli.project import list_items, resolve_project
from wf_cli.resources import ResourceDeclarationError, parse_block

TERMINAL = {"🏁完成", "🛑已停止"}
SENTINEL = "<!-- resource-claims:begin -->"
MIG1_MARK = re.compile(r"<!--\s*state-plane-mig1:card_id=")   # §8.8.1 封閉母體成員判準

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
cards, blocking = [], []
for it in list_items(default_runner, project):
    if not it.card_id or (it.delivery_status or "") in TERMINAL: continue
    if not is_owner_assigned(it.owner_field): continue
    try:
        decl = parse_block(it.body)
    except ResourceDeclarationError as exc:                       # §8.7：不得略過
        blocking.append((it.card_id, str(exc),
                         bool(MIG1_MARK.search(it.body or "")),
                         SENTINEL in (it.body or "")))
        continue
    m = re.match(r"https://github\.com/([^/]+/[^/]+)/issues/", it.issue_url or "")
    cards.append((it.card_id, m.group(1) if m else None,
                  [r for r in decl.resources if r.startswith("file:")]))

print(f"已指派活卡 {len(cards) + len(blocking)} 張；可解析 {len(cards)}、不可解析 {len(blocking)}")
print("[fail-closed] 無法解析而阻擋派工的活卡（§8.7）：")
for cid, err, in_cohort, has_sent in (blocking or []):
    elig = "可具名豁免" if (in_cohort and not has_sent) else "不可豁免（不在封閉母體）"
    print(f"  - {cid}：{err}｜MIG1 母體={in_cohort}｜sentinel={has_sent}｜{elig}")
if not blocking: print("  （無）")

for name, rule in (("A 現行", rule_a), ("B 立即", rule_b), ("C 目標", rule_c)):
    same = cross = unknown = 0
    for (c1, r1, f1), (c2, r2, f2) in combinations(cards, 2):
        if not any(rule(x, y) for x in f1 for y in f2): continue
        if r1 is None or r2 is None: unknown += 1; same += 1   # §4.2：歸屬未確立→視同同 repo
        elif r1 == r2: same += 1
        else: cross += 1
    print(f"{name}：同 repo {same} 對（其中歸屬未確立而 fail-closed 併入者 {unknown}）；跨 repo {cross} 對")
```

**2026-08-12 01:28 +0800 重跑輸出**（與 §9.7b 為同一次 session，兩節數字互相一致）：

```text
已指派活卡 17 張；可解析 15、不可解析 2
[fail-closed] 無法解析而阻擋派工的活卡（§8.7）：
  - INIT-GAME-RECAP：body 內找不到 <!-- resource-claims:begin --> ... <!-- resource-claims:end --> 之間的 fenced JSON 資源宣告區塊｜MIG1 母體=True｜sentinel=False｜可具名豁免
  - ML-FIELD-OF1：body 內找不到 <!-- resource-claims:begin --> ... <!-- resource-claims:end --> 之間的 fenced JSON 資源宣告區塊｜MIG1 母體=True｜sentinel=False｜可具名豁免
A 現行：同 repo 0 對（其中歸屬未確立而 fail-closed 併入者 0）；跨 repo 0 對
B 立即：同 repo 0 對（其中歸屬未確立而 fail-closed 併入者 0）；跨 repo 0 對
C 目標：同 repo 0 對（其中歸屬未確立而 fail-closed 併入者 0）；跨 repo 0 對
```

**輸出隨時間變動的逐項交代**（前一版為 2026-08-11：17 張、B／C 各 1 對；R1 當時為 16 張）：

- **活卡張數**（17）：集合逐日變動，查核者重跑得到不同張數是預期的。
- **B／C 由 1 對變 0 對**：唯一那對是 `WF-ORCHESTRATION-RECONCILE1` × `WF-ESCALATION-DEFERRED-FINDINGS1`（`file:templates/` ~ `file:templates/review-escalation.md`），而 #16 已於 `2026-08-12T00:13:42+08:00` 由 `amend`（op `df7e0929`）把 `file:templates/` 移出宣告（軌跡與理由見 §1.2 的告示框）。**線上反例是被本契約的語意說服而消解的，不是被推翻的。**
- **不變的是**：規則 A 在真實資料上**從未**判出任何 `file:` 階層相交；跨 repo 相交 0 對；阻擋名單全數落在 §8.8.1 的封閉母體內。

**因此本節的角色必須被正確理解**：它是「今天這份守衛在真實資料上會做什麼」的**可重跑普查**，不是「#16 × #22 存在」的證據來源。後者是歷史事實，凍結在 §9.1 第 1 列與 §9.8 的離線語料裡——**會變的東西不該被當成不變量引用**，這正是上一版措辭的錯誤，R3 已改。

> **立即後果一（相交語意）**：本節生效後，#22 在 #16 進入終態或 `amend` 其資源宣告前**不得派工**——即使現行實作判它們不衝突。**實作現況不等於契約應然**，而本卡的職責正是讓兩者對齊。
>
> **立即後果二（fail-closed）**：§8.7 生效後，**任何**卡的 `assign` 都會被上列 2 張擋下，除非依 §8.8 逐張具名豁免。這是刻意的痛感。

### 9.7b 封閉母體普查（生成式證據，支撐 §8.7.1／§8.8.1）

「無法解析 ≡ MIG1 佔位卡」「母體外 0 張」「30/33 的 db_scope 落在封閉列舉內」這三個宣稱**必須由程式產生**，因為 §8.7.2 的整個論證（放寬解析器是陷阱）都架在第三個宣稱上。

````python
# §9.7b 封閉母體普查。依賴：wf_cli（gh CLI 已登入）。唯讀。
# 註：本區塊以四個反引號圍起，因為程式內含 ``` 字面（MIG1_JSON 正則要比對 fenced JSON）。
# 註：所有含反斜線的正則一律先編譯成模組層常數，不得內嵌進 f-string 的取值部——
#     那在 Python 3.12 以前是 SyntaxError（見 §9.9，該規則由自檢探針機械執行）。
import json, re
from collections import Counter
from wf_cli.gh import default_runner
from wf_cli.project import list_items, resolve_project
from wf_cli.resources import ResourceDeclarationError, parse_block

SENTINEL = "<!-- resource-claims:begin -->"
MIG1_MARK = re.compile(r"<!--\s*state-plane-mig1:card_id=")
MIG1_JSON = re.compile(r"##\s*資源宣告（機器可讀[^\n]*\n```json\s*(?P<j>.*?)```", re.DOTALL)
ISSUE_URL = re.compile(r"https://github\.com/([^/]+/[^/]+)/issues/")   # §4.2 的歸屬解析形狀
PREFIX = re.compile(r"^(file:.+|port:\d+|container:.+|db:[^:]+:(schema|table:.+))$")

items = [it for it in list_items(default_runner, resolve_project(default_runner, "ruan6047", 4))
         if it.card_id]
fail = []
for it in items:
    try: parse_block(it.body)
    except ResourceDeclarationError: fail.append(it)

in_cohort = [it for it in fail if MIG1_MARK.search(it.body or "")]
with_worktree = [it.card_id for it in in_cohort
                 if (it.branch_worktree or "—").strip() not in ("", "—")]
no_repo = sum(1 for it in items if not ISSUE_URL.match(it.issue_url or ""))
print(f"Project #4 有卡ID 的 item {len(items)} 張；宣告無法解析 {len(fail)} 張")
print(f"  帶 state-plane-mig1 marker（封閉母體）：{len(in_cohort)}")
print(f"  帶 resource-claims sentinel 卻仍失敗：{sum(1 for it in fail if SENTINEL in (it.body or ''))}")
print(f"  母體外的解析失敗（＝不可豁免、硬阻擋）：{len(fail) - len(in_cohort)}")
print(f"  母體中已註冊「分支worktree」者：{with_worktree or 0}")
print(f"  全 item 中 issue_url 無法解析出 owner/repo 者：{no_repo}")

scopes, tainted = Counter(), []
for it in in_cohort:
    m = MIG1_JSON.search(it.body or "")
    if not m: scopes["（無 JSON）"] += 1; continue
    d = json.loads(m.group("j"))
    scopes[repr(d.get("db_scope"))] += 1
    bad = [r for r in d.get("resources") or [] if not PREFIX.match(r)]
    if bad: tainted.append((it.card_id, bad))
print(f"  母體內佔位 db_scope 分佈：{dict(scopes)}")
print(f"  母體內 resources 含不合前綴項目者：{tainted or '無'}")
print("  封閉母體字面清單（衍生卡直接落成常數，§8.8.1）：")
print("    " + ", ".join(sorted(it.card_id for it in in_cohort)))
````

**2026-08-12 01:28 +0800 輸出**（與 §9.7 同一次 session；本區塊由**修正後的程式原樣抽出執行**產生，見 §9.9）：

```text
Project #4 有卡ID 的 item 99 張；宣告無法解析 33 張
  帶 state-plane-mig1 marker（封閉母體）：33
  帶 resource-claims sentinel 卻仍失敗：0
  母體外的解析失敗（＝不可豁免、硬阻擋）：0
  母體中已註冊「分支worktree」者：0
  全 item 中 issue_url 無法解析出 owner/repo 者：0
  母體內佔位 db_scope 分佈：{"'none'": 11, "'read'": 10, "'write'": 8, "'schema'": 1, 'None': 3}
  母體內 resources 含不合前綴項目者：[('DEV-REVIEW-PREFLIGHT-GATE1', ['DEV-REVIEW-DEACCEPT-TRAIL1'])]
  封閉母體字面清單（衍生卡直接落成常數，§8.8.1）：
    DEV-CI-RED-OWNERSHIP1, DEV-EVENT-REPAIR-ANCHOR1, DEV-REVIEW-DEACCEPT-TRAIL1,
    DEV-REVIEW-PREFLIGHT-GATE1, DEV-REVIEW-PREFLIGHT-SELFCHECK1, DEV-TRAILER-GUARD-PR-CHECKOUT1,
    DEV-VERIFY-TM-ASSERTS1, DOC-CARD-SPEC-RULES1, INGEST-GAME-TM-REFACTOR1,
    INGEST-LIVE-RECONCILE1, INGEST-PLAYER-BIO-GAP2, INGEST-POSTGAME-FINALIZE1,
    INGEST-SPLITS-IMPORT-RESTATE1, INIT-GAME-RECAP, INIT-OFFICIAL-DATA1, INIT-PRODUCT-UX,
    MATCHUP-DATA2, ML-FIELD-LINEUP1, ML-FIELD-OAA-VAL1, ML-FIELD-OF1, ML-PA-SIM-CONTEXT1,
    ML-PA-SIM-TEAM1, ML-PT3, ML-SIM2, OPS-BACKUP-DR1, OPS-CONTROL-PLANE-PR-GUARD1,
    OPS-POSTGAME-OBSERVE1, OPS-REMOTE-CUTOVER1, OPS-REMOTE-PROBE1, OPS-REMOTE-ROUTE1,
    OPS-REMOTE-WORKER1, OPS-STATE-PLANE-MIG1, UX-TEAM-FIELD-HIST1
```

（原始輸出為單行；此處為版面折行，內容逐字相同、順序為 `sorted()`。**這 33 個 ID 就是 §8.8.1 要求衍生卡落成的字面常數**——它由程式列舉，不由人清點。）

**釘選與變動交代（R3）**：本節全部數字釘選在 **2026-08-12 01:28 +0800** 這一次執行，該次與 §9.7 為同一 session。與 2026-08-11 版相比，**唯一變動是 `item 96 → 99`**（Project 新增 3 張有卡 ID 的 item）；解析失敗 33、母體 33、母體外 0、sentinel 卻失敗 0、已註冊 worktree 0、`db_scope` 分佈、混入卡 ID 的那 1 張、以及 33 個 ID 的字面清單**逐字未變**。

**這份輸出在 R2 是不存在的**：R2 版的程式把一個含反斜線的正則直接放進 f-string 取值部，在 Python 3.12 以前是 `SyntaxError`（而 `cli/pyproject.toml` 的 `requires-python` 下限是 **3.11**），因此上一版所有「33 張」「母體外 0」「30/33」等數字**在文件形態下無法被重跑驗證**——那是 R2-001 的實質，不是排版瑕疵。R3 的修法是把所有含反斜線的正則提升為模組層 `re.compile` 常數（`ISSUE_URL`、`PREFIX`），並以 §9.9 的自檢探針把「這件事不得再發生」變成**機械檢查**而非人的自律。

**讀法**：`db_scope` 分佈中 **30/33 落在封閉列舉內**（`none`＋`read`＋`write`＋`schema`）——這正是 §8.7.2 的關鍵數字：放寬 sentinel 比對後，這 30 張會解析**成功**並產生 `resources: []`，把「寫入集未知」靜默轉譯成「寫入集為空」。

### 9.8 離線窮舉（生成式證據，支撐 §2／§3／§8.2／§8.5）

§8.2 的 `B ⊇ C` 與 §3.1 的「拒收條件是完整列舉」是**完整性宣稱**，必須由可重跑的 artifact 產生。下列程式**不依賴網路、不依賴 `wf_cli`**，查核者可原樣複製執行。

```python
# §9.8 離線窮舉：語彙分類的完整性 + 立即階段 ⊇ 目標階段。無網路、無 wf_cli 依賴。
import unicodedata
from itertools import combinations_with_replacement

REJECT_RULES = {2: "絕對路徑", 3: "家目錄", 4: "..", 5: "萬用字元", 11: "空路徑"}

def classify(raw):                      # 回傳 ("reject", rule_no) 或 ("accept", K)
    if raw.startswith("/"):  return ("reject", 2)
    if raw.startswith("~"):  return ("reject", 3)
    comps = [c for c in raw.split("/") if c not in ("", ".")]
    if any(c == ".." for c in comps):    return ("reject", 4)
    if any(("*" in c or "?" in c) for c in comps): return ("reject", 5)
    if not comps:                        return ("reject", 11)
    return ("accept", tuple(unicodedata.normalize("NFC", c).casefold() for c in comps))

def rule_b(kx, ky):                      # 立即階段：字串前綴（§8.1）
    a, b = "/".join(kx), "/".join(ky)
    return a.startswith(b) or b.startswith(a)

def rule_c(kx, ky):                      # 目標階段：分量序列前綴（§2.2）
    n = min(len(kx), len(ky))
    return kx[:n] == ky[:n]

ACCEPT_CORPUS = [
    "templates/", "templates", "templates/a.md", "templates/review-escalation.md",
    "templates2/a.md", "templates2/", "Templates/", "./templates/", "templates//",
    "docs/", "docs/A.md", "docs/a.md", "docs/WF_RESOURCE_WRITESET1.md",
    "docs/reference/", "docs/reference/棒球規則.txt",
    "a/b", "a/b/c.md", "a/b/d.md", "./a//b/c.md",
    "web/src/app/games/[sno]/", "web/src/app/games/[sno]/page.tsx",
    "cli/src/wf_cli/", "cli/src/wf_cli/resources.py",
]
REJECT_CORPUS = [
    "../outside.md", "a/../b.md", "/etc/passwd", "/", "~/secrets", "~",
    "src/**/*.py", "a?.md", ".", "./", "", "a//../b", "**", "docs/*",
]

# --- 斷言 1：分類是全函數且分割（每個輸入恰好一個結果，拒收理由來自封閉列舉）
bad = []
for raw in ACCEPT_CORPUS:
    kind, payload = classify(raw)
    if kind != "accept" or not payload: bad.append(("應接受卻拒收", raw, payload))
for raw in REJECT_CORPUS:
    kind, payload = classify(raw)
    if kind != "reject": bad.append(("應拒收卻接受", raw, payload))
    elif payload not in REJECT_RULES: bad.append(("拒收理由不在封閉列舉", raw, payload))
print(f"[1] 語彙分類：接受語料 {len(ACCEPT_CORPUS)} 筆、拒收語料 {len(REJECT_CORPUS)} 筆；"
      f"分類錯誤 {len(bad)} 筆 {bad if bad else ''}")

# --- 斷言 2：B ⊇ C（立即階段不漏放目標階段會抓的）
keys = {raw: classify(raw)[1] for raw in ACCEPT_CORPUS}
pairs = list(combinations_with_replacement(ACCEPT_CORPUS, 2))
b_misses_c, b_only = [], []
for x, y in pairs:
    c, b = rule_c(keys[x], keys[y]), rule_b(keys[x], keys[y])
    if c and not b: b_misses_c.append((x, y))
    if b and not c: b_only.append((x, y))
print(f"[2] 組合數 {len(pairs)}（含自配對）；b_misses_c = {len(b_misses_c)} "
      f"{b_misses_c if b_misses_c else '（B ⊇ C 成立）'}")

# --- 斷言 3：立即階段的過度拒絕必須存在且被釘住（§8.5）
print(f"[3] 立即階段獨有的過度拒絕 {len(b_only)} 對：")
for x, y in sorted(b_only): print(f"      {x!r} × {y!r}")

# --- 斷言 4：§9.1 矩陣第 1–11 列的期望值逐列驗證
MATRIX = [
    (1,  "templates/", "templates/review-escalation.md", True,  True),
    (2,  "templates/", "templates2/a.md",                False, True),
    (3,  "templates/", "templates",                      True,  True),
    (4,  "templates",  "templates/a.md",                 True,  True),
    (5,  "docs/A.md",  "docs/a.md",                      True,  True),
    (6,  "./templates/", "templates/a.md",               True,  True),
    (7,  "templates//", "templates/a.md",                True,  True),
    (8,  "Templates/", "templates/a.md",                 True,  True),
    (9,  "a/b/c.md",   "a/b/d.md",                       False, False),
    (10, "web/src/app/games/[sno]/", "web/src/app/games/[sno]/page.tsx", True, True),
    (11, "docs/reference/", "docs/reference/棒球規則.txt", True, True),
]
fails = []
for no, x, y, exp_c, exp_b in MATRIX:
    kx, ky = classify(x)[1], classify(y)[1]
    got_c, got_b = rule_c(kx, ky), rule_b(kx, ky)
    if (got_c, got_b) != (exp_c, exp_b):
        fails.append((no, x, y, (got_c, got_b), (exp_c, exp_b)))
print(f"[4] §9.1 第 1–11 列：{len(MATRIX)} 列，不符期望 {len(fails)} 列 {fails if fails else ''}")

ok = not bad and not b_misses_c and not fails and b_only
print(f"[裁決] {'PASS' if ok else 'FAIL'}")
```

**2026-08-11 輸出**：

```text
[1] 語彙分類：接受語料 23 筆、拒收語料 14 筆；分類錯誤 0 筆
[2] 組合數 276（含自配對）；b_misses_c = 0 （B ⊇ C 成立）
[3] 立即階段獨有的過度拒絕 10 對：
      'templates' × 'templates2/'
      'templates' × 'templates2/a.md'
      'templates/' × 'templates2/'
      'templates/' × 'templates2/a.md'
      'templates2/' × './templates/'
      'templates2/' × 'Templates/'
      'templates2/' × 'templates//'
      'templates2/a.md' × './templates/'
      'templates2/a.md' × 'Templates/'
      'templates2/a.md' × 'templates//'
[4] §9.1 第 1–11 列：11 列，不符期望 0 列
[裁決] PASS
```

**[3] 的清單就是 §8.5 要求被釘住的東西**：立即階段的誤拒不是 bug，而且它的**完整範圍**在此以生成方式列出——日後有人想「修掉」其中任何一對，會直接撞上這份清單與 `[裁決] PASS` 的條件（`b_only` 非空是 PASS 的必要條件之一）。

**語料的邊界誠實聲明**：這是**有限語料上的窮舉**，不是對全部字串的證明。§8.2 的證明本身是形式化的（對任意分量序列成立）；本節的角色是**回歸防護**——確保實作與該證明不脫節，並把 §8.5 的過度拒絕範圍固定下來。語料涵蓋 §9.1／§9.2 的全部輸入類別（邊界、大小寫、`./`、重複斜線、中括號、CJK、多層路徑）。

### 9.9 探針自檢：把「探針可原樣重跑」變成機械檢查（R2-001 的結構性處置）

R2-001 的教訓不是「有一行寫錯」，而是**「文件內的證據可以原樣重跑」這件事本身沒有任何檢查**。§9.7／§9.7b／§9.8 三支探針是 §8.7.2、§8.8.1、§8.2、§8.5 全部完整性宣稱的唯一支撐，而其中一支壞了七天沒被發現——直到查核者手動 `sed | python3` 才撞上。**人工保證失效過一次，就不該再被當成保證。**

下列程式**抽出本檔全部 `python` 圍籬區塊**，逐一編譯、檢查跨直譯器可攜性，並實際執行其中不需網路者。它自身也是一個 `python` 區塊，因此**會抽到自己**（以 `probe-selfcheck` 標記避免遞迴執行，但仍受編譯與可攜性檢查）。**無網路、無 `wf_cli` 依賴；退出碼非 0 即失敗，可直接掛 CI。**

```python
# §9.9 探針自檢（probe-selfcheck）：抽出本檔全部 python 探針，逐一編譯、檢查跨直譯器版本
# 可攜性，並實際執行其中不需網路者。無網路、無 wf_cli 依賴；退出碼非 0 即失敗，可直接掛 CI。
import ast, pathlib, re, sys

DOC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "docs/WF_RESOURCE_WRITESET1.md")
TICK = chr(96)                   # 反引號；不寫字面，以免本區塊被自己的內容提前關閉
FLOOR = (3, 11)                  # cli/pyproject.toml 的 requires-python 下限
OPENER = re.compile("^(" + TICK + "{3,})python[ \t]*$")
SELF = "probe-selfcheck"         # 本區塊自身的標記：抽到自己時不遞迴執行

def extract(text):
    """回傳 [(起始行, 結束行, 原始碼)]，行號 1-based 且含端點。"""
    lines, out, i = text.splitlines(), [], 0
    while i < len(lines):
        m = OPENER.match(lines[i])
        if not m:
            i += 1; continue
        fence, j = m.group(1), i + 1
        while j < len(lines):
            s = lines[j].strip()
            if s and set(s) == {TICK} and len(s) >= len(fence): break
            j += 1
        if j >= len(lines): raise SystemExit(f"第 {i+1} 行的 python 區塊未閉合")
        out.append((i + 2, j, "\n".join(lines[i+1:j])))
        i = j + 1
    return out

def imports_wf_cli(tree):
    """是否真的 import wf_cli。不可用字串比對：§9.8 的語料裡就有 cli/src/wf_cli/ 這條路徑。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(a.name.split(".")[0] == "wf_cli" for a in node.names): return True
        if isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] == "wf_cli": return True
    return False

def fstring_backslash(tree, src):
    """f-string 取值部含反斜線者，在 Python 3.12 以前（PEP 701 之前）是 SyntaxError。"""
    if sys.version_info < (3, 12):
        return []                # 該版本的 compile() 本身即精確閘門，且 f-string 內位置不可靠
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.JoinedStr): continue
        for part in node.values:
            if not isinstance(part, ast.FormattedValue): continue
            seg = ast.get_source_segment(src, part.value) or ""
            if "\\" in seg: hits.append((part.lineno, seg.strip()))
    return hits

text = DOC.read_text(encoding="utf-8")
probes, failures, ran = extract(text), [], 0
ver = ".".join(str(n) for n in sys.version_info[:3])
floor = f"{FLOOR[0]}.{FLOOR[1]}"
print(f"探針自檢：{DOC}；抽出 python 區塊 {len(probes)} 個；直譯器 {ver}；宣稱可攜下限 {floor}")
if len(probes) < 4: failures.append(("整份", f"只抽到 {len(probes)} 個區塊，少於本檔登記的 4 個"))
for start, end, src in probes:
    label, note = f"L{start}-{end}", []
    try:
        tree = ast.parse(src, f"{DOC}:{start}")
    except SyntaxError as exc:
        failures.append((label, f"編譯失敗：{exc}")); print(f"  {label}：編譯失敗"); continue
    for lineno, seg in fstring_backslash(tree, src):
        failures.append((label, f"第 {start + lineno - 1} 行 f-string 取值部含反斜線"
                                f"（{floor} 上會 SyntaxError）：{seg}"))
        note.append("可攜性違例")
    if SELF in src:
        note.append("自身，不遞迴執行")
    elif imports_wf_cli(tree):
        note.append("需 gh 登入，僅編譯")
    else:
        ns = {"__name__": "__probe__"}
        try:
            exec(compile(tree, f"{DOC}:{start}", "exec"), ns)
        except BaseException as exc:
            failures.append((label, f"執行拋錯：{type(exc).__name__}: {exc}")); note.append("執行失敗")
        else:
            ran += 1
            note.append("已執行")
            if ns.get("ok") is False: failures.append((label, "該探針自身斷言判 FAIL"))
    print(f"  {label}：編譯 OK；{'；'.join(note) or '—'}")
print(f"實際執行 {ran} 個離線探針；違例 {len(failures)} 筆")
for label, msg in failures: print(f"  [FAIL] {label}：{msg}")
print(f"[裁決] {'PASS' if not failures else 'FAIL'}")
sys.exit(1 if failures else 0)
```

#### 9.9.1 它檢查什麼，為什麼是這三件

1. **編譯**（`ast.parse`）：抓 R2-001 那一類「抽出來根本跑不起來」。在 3.12 以前的直譯器上，這一步就是精確閘門。
2. **可攜性**（f-string 取值部的反斜線）：**這才是 R2-001 的真正形狀**。在 3.12+（PEP 701）該寫法合法，於是**用新直譯器自檢會看不見它**——查核者用系統 Python 3.9 撞到、執行者用 3.14 沒撞到，同一份檔案兩種結果。故在 3.12+ 上補一道 AST 掃描，把宣稱的可攜下限（`requires-python >= 3.11`）機械化。3.12 以下不掃：那些版本的 `compile()` 已是精確閘門，且 f-string 內的位置資訊不可靠，掃了會產生假陽性。
3. **執行**：不 import `wf_cli` 的探針（今日只有 §9.8）**實際跑完**，並在其自訂 `ok` 為 `False` 時判 FAIL。需 `gh` 登入者只編譯——CI 不該依賴 GitHub 憑證，但**語法與可攜性不需要憑證就能守住**。

`imports_wf_cli` 用 AST 判 import 而非字串比對，是因為 §9.8 的語料裡就有 `"cli/src/wf_cli/"` 這條**路徑字串**——用 `"wf_cli" in src` 會把離線探針誤判成需憑證而**靜默不執行它**。這是本檔反覆出現的同一種病：**用寬鬆的字面比對代替結構判定，代價是安靜地少做事。**

#### 9.9.2 在修正前的檔案上執行的輸出（反向驗證）

自檢若只在修好之後跑一次，證明不了它抓得到東西。以 **R2 交付版**（`cb6028f`）的檔案為輸入：

```text
探針自檢：docs/WF_RESOURCE_WRITESET1.md；抽出 python 區塊 3 個；直譯器 3.14.3；宣稱可攜下限 3.11
  L609-664：編譯 OK；需 gh 登入，僅編譯
  L692-733：編譯 OK；可攜性違例；需 gh 登入，僅編譯
  L768-855：編譯 OK；已執行
實際執行 1 個離線探針；違例 2 筆
  [FAIL] 整份：只抽到 3 個區塊，少於本檔登記的 4 個
  [FAIL] L692-733：第 720 行 f-string 取值部含反斜線（3.11 上會 SyntaxError）：sum(1 for it in items if not re.match(r'https://github\.com/([^/]+/[^/]+)/issues/', it.issue_url or ''))
[裁決] FAIL
```

（`[3]`／`[4]` 等 §9.8 自身的輸出在執行時會巢狀印出，此處略去。）

**它在 Python 3.14 上、且在 `compile()` 通過的情況下，仍然指到了第 720 行**——與查核者用系統 Python 3.9 手動 `sed -n '694,733p' | python3` 撞到的是同一行。第一筆 `[FAIL]` 則是自檢**抽到自己之前**的狀態（R2 版沒有 §9.9，只有 3 個區塊）。

#### 9.9.3 在本次交付版上的輸出

```text
探針自檢：docs/WF_RESOURCE_WRITESET1.md；抽出 python 區塊 4 個；直譯器 3.14.3；宣稱可攜下限 3.11
  L622-677：編譯 OK；需 gh 登入，僅編譯
  L709-754：編譯 OK；需 gh 登入，僅編譯
  L793-880：編譯 OK；已執行
  L914-997：編譯 OK；自身，不遞迴執行
實際執行 1 個離線探針；違例 0 筆
[裁決] PASS
```

（同樣略去 §9.8 在 `L793-880` 執行時巢狀印出的 `[1]`–`[4]` 與其 `[裁決] PASS`；退出碼 `0`。）

四個區塊即 §9.7（`L622-677`）、§9.7b（`L709-754`）、§9.8（`L793-880`）、§9.9 自身（`L914-997`）。**行號會隨本檔任何編輯而漂移，所以它由自檢輸出，不寫進正文其他地方。**

#### 9.9.4 CI 歸屬與行號的自動化

- **CI**：衍生卡須把本探針落成 repo 內腳本並掛進 CI（§9.6 第 57 列、§10）。**本卡只宣告 `docs/WF_RESOURCE_WRITESET1.md` 一個資源，不得新增 workflow 或 script 檔案**——這是資源宣告互斥語意的卡在自己身上的應用，不是偷懶。
- **行號**：上列輸出的 `L<起>-<訖>` 即各探針在本檔中的行號區間，**由程式列出、不由人維護**。查核者若要沿用手動 `sed -n '<起>,<訖>p' docs/WF_RESOURCE_WRITESET1.md | PYTHONPATH=cli/src python3` 的重現方式，直接讀該次自檢輸出即可，不必信任文件裡任何寫死的行號。

---

## 10. 歸屬

契約語意（§2–§8）定義在本卡。實作歸衍生卡（基線 §9-L）：

- `resources.py`：§2.1 正規化、§2.2 相交謂詞、§3 語彙拒收、§4 repo 限定詞、§8.1–§8.5 兩階段。
- `open_cmd.py`／`amend_cmd.py`：§3.4 拒收時機、§5.1 tracked symlink 逐分量走查、§7.1 存在性提示。
- `assign_cmd.py`：§5.3 realpath 與 containment、§6 revision 釘選與 TOCTOU、§4.2 repo 歸屬 fail-closed、**§8.6 不變式 I 的各站處置、§8.7 移除 `skipped_unparseable`、§8.8 `--ignore-unparseable` 與 `UNPARSEABLE_EXEMPTION_SUNSET` 常數**。
- `doctor.py`：§8.8.2 的母體殘量與距 sunset 天數輸出（唯讀報告）。
- **CI ＋ 一支 repo 內腳本**：§9.9 的探針自檢（抽取本檔全部 `python` 區塊 → 編譯 ＋ 可攜性 ＋ 執行離線者），連同 §9.6 第 57 列的兩個變異測試。**本卡不落地它**——本卡只宣告 `docs/WF_RESOURCE_WRITESET1.md`，新增腳本或 workflow 會逸出自己的寫入集。
- 測試：§9 全部 61 列（1–43 原有＋28a／28b＋44–57＋49a／49b 共 18 列新增）＋五項列舉式斷言（§9.2 零遷移負債、§9.3 第 28／28b、§9.6 第 54、§9.7／§9.7b／§9.8 的生成式輸出）。

**排程限制**：`assign_cmd.py` 目前由 [#21](https://github.com/ruan6047/ai-workflow/issues/21) 佔用（宣告 `file:cli/src/wf_cli/commands/assign_cmd.py`），衍生卡須待其釋放。`resources.py` 目前**無活卡佔用**，故 §8.1 的立即階段可先行落地——這正是兩階段切分的實務價值。

---

## 11. 對基線 §7.2 的修正（逐條）

本檔非基線的重述。下表即完整清單：**3 處實測修正、5 處補完、2 處新增裁定**（第 9、10 列為 R1 查核後新增）。

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
| 9 | 未涵蓋「別卡宣告解析失敗」 | **新增裁定**（R1-001）：現行只警告不擋，是 fail-open；改為阻擋派工，逃生門為具名／留痕／有到期的豁免。放寬解析器經實測是更糟的選項 | §8.6–§8.8 |
| 10 | 未涵蓋「repo 歸屬判不出來」 | **補完**：repo 限定詞是放行方向的規則，其前提須正向確立；別卡歸屬未確立時退回「視同同 repo」比對，本卡歸屬未確立則拒絕派工 | §4.2 |

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
5. **活卡的定義**。沿用現行 `assign`（非終態＋已指派），未改動。**收緊它是 fail-open 方向的變更**，理由見 §8.8.4，須另開卡並以「這會漏掉什麼」為驗收。
6. **`open`／`amend` 對既有 33 張 MIG1 佔位卡的批次補宣告**。§8.8 給了到期壓力，但**誰去補、怎麼補**是作業排程，不是契約語意。
7. **CLI 路徑引數的正規化**（`--worktree` 等）。§3.1 的封閉 namespace 只規範卡面 `file:` 資源宣告；兩者定義域不相容，理由見該節的界線告示，歸屬 [#23](https://github.com/ruan6047/ai-workflow/issues/23)。

### 12.1 已從非目標移出並裁定的項目（記錄）

前一版（R1 交付）把「無法解析的資源宣告被靜默略過」列為本節第 6 項「提出但不裁定」。**R1 查核以 blocking finding 退回該處置，判定正確**：把一個已知的 fail-open 標為「不處理」，等於用文件把靜默放行合法化，與卡面「任何無法安全判定的情形一律拒絕派工」直接矛盾。

**現已裁定於 §8.6（不變式 I）、§8.7（fail-closed）、§8.8（具名／可稽核／到期的豁免），並納入 §9.6 矩陣第 44–56 列與 §10 的衍生卡歸屬。** 本節保留此段是為了讓「曾經被列為非目標」這件事留在紙上，而不是被無痕改寫。

殘留的 fail-open（含豁免本身）明列於 §8.9，**不宣稱已關閉**。

---

## 13. 執行者揭露

- 本檔為設計／契約文件，**無程式碼變更、無 CI**。§9 的矩陣**未被執行**，執行歸衍生卡。
- §1.1、§1.2、§3.2、§3.3、§4.1、§4.2、§8.2、§8.3、§8.7、§8.8、§9.7、§9.7b、§9.8 的所有數字，均由探查程式對真實 repo 與真實 Project #4 產生，非人工清點。四支探針（§9.7 活卡三規則、§9.7b 封閉母體普查、§9.8 離線窮舉、§9.9 探針自檢）**全部內嵌於本檔並可原樣抽出執行**，其中 §9.8 與 §9.9 不需網路與 `gh` 登入。
- **上一句在 R2 交付版是假的，而它是我自己寫的。** R2 版逐字寫著「三支探針全部內嵌於本檔並可原樣重跑」，實際上 §9.7b 抽出來即 `SyntaxError`（f-string 取值部含反斜線，Python < 3.12），由查核者以 `sed | python3` 撞出（R2-001）。**這條紀律的教訓不是「要更小心」**：我在 Python 3.14 上寫、在 3.14 上驗，而該寫法在 3.14 合法——**同一份檔案在不同直譯器上有不同結果，靠自律看不見**。故 R3 不只修那一行，而是把「探針可原樣抽出執行」本身變成 §9.9 的機械檢查，並要求衍生卡以變異測試釘住它（§9.6 第 57 列）。
- **R3（本輪）處理 R2-001**：修 §9.7b 的可攜性缺陷並以修正後程式重跑（§9.7／§9.7b 同一 session，釘選 2026-08-12 01:28 +0800）、新增 §9.9 探針自檢與 §9.6 第 57 列、補 §3.1 的定義域界線告示與 §12 第 7 項（跨卡裁決，對 [#23](https://github.com/ruan6047/ai-workflow/issues/23)）、修正 §4.2 對 §9.7／§9.7b 的誤標，並在 §1.2／§9.7 記錄「線上反例已消失」與上一版把線上狀態誤當不變量的措辭錯誤。**§2、§3（除新增告示）、§5–§8 未改動；§9.8 一字未改**（其 `[裁決] PASS` 在 R3 由 §9.9 自動執行複現）。
- **R2 處理 R1-001**：新增 §8.6–§8.9、§9.6 矩陣 13 列、§9.7b／§9.8 兩支探針，改寫 §4.2、§12.1，並補 §11 第 9／10 列。§2、§3、§5–§7 的既有內容未被修改（R1 查核已驗證通過的 `B ⊇ C`、窮舉 `b_misses_c=0`、`templates/` vs `templates2/a.md` 不相交三項結論在 §9.8 被重新生成並維持不變）。
- **R3 自陳，未修：§9.9 的自檢只涵蓋內嵌於本檔的四支探針，本檔仍有數字不在其射程內。** 具體是 §1.1 的「送入宣告全數被接受」對照表、§4.1 的 repo 分佈表（非終態 10／44、已指派 7／11）、§3.2 的 `*`／`?`／`[` 計數（0／0／41）、§3.3 的 25 個非 ASCII 路徑——這些來自一次性 session 腳本，**與 R2-001 是同一族的「不可重跑證據」，只是還沒有人踩到**。本輪不補的理由是它們支撐的都是**定性結論**（語彙檢查為零、Project 跨兩 repo、中括號不可誤拒、CJK 路徑真實存在），定性結論不因計數漂移而翻轉；而 §8.7.2／§8.8.1 靠的是**具體數值與具名清單**，那才是非可重跑不可的。**這個界線是我畫的，查核者可以不接受**——若判定要全數補成內嵌探針，工作量在本檔內、不逸出寫入集。
- **§8.2 的「258 組合」數字來自 R1 當時的一次性 session 腳本，不可重跑**；本輪以 §9.8 的內嵌程式取代其角色（23 條語料、276 組合、`b_misses_c = 0`），結論相同而證據升級為可稽核。兩者語料不同故組合數不同——**這是刻意的替換，不是數字對不上**。
- §5.2 的 git symlink 行為以一個臨時 scratch repo 實測，該 repo 未進入本 repo；重現步驟即 §9.4 第 29–33 列。
- 撰寫過程中一項自查修正值得記錄：初次以 `git ls-files | grep -P '[^\x00-\x7F]'` 探查非 ASCII 路徑，得到「兩 repo 皆無」的**錯誤**結論——`git ls-files` 預設對非 ASCII 路徑做 C-style 八進位引號。改用 `-c core.quotePath=false` 後查出 25 筆。§3.3 因此從「不需要」翻轉為「需要」。**探查工具的預設值本身就是一個可以說謊的來源。**
