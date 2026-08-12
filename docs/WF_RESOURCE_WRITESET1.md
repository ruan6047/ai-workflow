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
> 它**不是**一個通用的路徑正規化器，**明確不涵蓋 CLI 的路徑引數**（如 `--worktree <path>`、指向檔案的命令參數）。兩者定義域不相容：資源宣告必須是 repo 根的相對路徑，才能有共同座標可比（§3.1-1、§4）；而 CLI 引數必須解析到執行當下的**真實檔案系統位置**，因此絕對路徑與 `~` 在那裡是合法且必要的——本節第 2、3 條把它們拒收，正是因為在**宣告**的定義域裡它們會使相交判定失去座標。**把本節的規則套到 CLI 引數上會是錯誤引用。**（定義域不相容是兩側共同結論，非本卡單方宣稱：[#23](https://github.com/ruan6047/ai-workflow/issues/23) §10 的 A3 判定與本節同向。）
>
> **但「錯誤引用」不等於「正確版本在別處」。** 本卡曾把引數正規化的歸屬指向 #23；**#23 已於其交付版（`d824d16`）§4.1b／§10 明文拒絕承接**：它逐一追碼六個承接動詞的引數，裁定「承接的六個動詞裡，沒有任何一個引數需要檔案系統路徑正規化」，因而**不定義**也**不引用**任何 CLI 路徑正規化器。**故 CLI 路徑引數的正規化目前無人擁有。這是事實陳述，不是待辦——沒有人欠這個函式。**
>
> **先看 #23 的判準，因為它很可能也適用於下一個人**：分類鍵應該是「該引數對**事件內容**的實際貢獻」，不是它的表面語法長得像不像路徑。照這條追碼的結果是——`--worktree` 逐字寫入狀態面故**字面入鍵**（不 `realpath`、不展開 `~`、不摺疊尾斜線）；`--config`／`--owner`／`--project`／`--repo` 只餵目標解析故**鍵外**；`--repo-path` 只做唯讀驗證、`--input` 只有內容入鍵而路徑不入鍵。七個看起來像路徑的引數，**沒有一個真的需要解析到檔案系統**。多數「我需要路徑正規化」的需求會在這一步消解。
>
> **若追完仍然需要，要證明的是什麼**：#23 已論證「自訂一套保守的 CLI 路徑正規化」是一個**做不到的全函數宣稱**——要讓同一邏輯路徑在不同 cwd／symlink 狀態下產生同一組位元組就得 `realpath`，而 `realpath` 對**尚未存在**的路徑沒有定義（`--out-dir` 正是這種）；大小寫與 NFC／NFD 敏感度是**執行期的檔案系統性質**（APFS 與 ext4 答案不同），不是設計期可判定的常數。寫得出來的只會是在某些機器上摺疊過度、另一些機器上摺疊不足的函式，而**摺疊過度＝把操作者顯式的新意圖靜默回答成 `already_exists`**。因此需要者**須自行開卡**，並在卡上一併提出：(a) 具體引數與它對事件／狀態面的實際貢獻；(b) 為何「字面入鍵」或「鍵外」不足以涵蓋該貢獻；(c) 在什麼檔案系統性質假設下該正規化是良定義的，以及該假設不成立時的 fail-closed 行為。**缺 (c) 就不要寫這個函式**——#23 對「未來真的需要正規化的新引數」給的答案是**降級**（該動詞退出冪等保護並在 stderr 明示），不是補一個正規化器。

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
| 57 | 本檔 §9.9 的自檢落成 repo 內腳本並掛 CI，對本檔執行 | 退出碼 **0**；且對**人為植入**的八種變異退出碼 **非 0**：(a) 「f-string 取值部含反斜線」（PEP 701，3.12+ 才合法）、(b) **`type _MutAlias = int`（PEP 695 型別別名語句，3.12+ 才合法，與 f-string 無關）**、(c) 「刪去一個探針區塊」、(c2) 「新增一個未登記區塊」、(c3) 「刪去 `probe-blocks` 登記行」、(c4) 「植入互相矛盾的第二行登記」、(e) 「探針改以非 0 退出碼結束」、(f) 「拿掉某探針的 `probe-requires` 登記」。(b) 的作用是釘住閘門**不是只認得已知那一種形狀**——它必須攔下任意高於下限的語法；(c2)–(c4)(e)(f) 的作用是釘住 R6 新增的三個機制各自沒有靜默放行路徑（實跑輸出見 §9.9.4） |
| 57a | 自檢執行環境**找不到**版本 ≤ 3.11 的直譯器 | 退出碼 **非 0**，訊息為「可攜性宣稱無從佐證」；**不得**退回用執行中的直譯器編譯而靜默 PASS（§9.9.1-C） |
| 57b | 自檢對**本檔以外**的文件執行（跨檔一般性） | 對一份**有** `probe-blocks` 登記、四支探針皆離線的文件退出碼 **0**，且四支**全部實際執行**；對同一份**無**登記者退出碼 **非 0** 且違例恰為登記缺失一筆。另須釘住三個約定各自成立：`if __name__ == "__main__":` 包住主體的探針**有被執行**、探針的 `sys.argv[1:]` 為空、`sys.exit(0)` 與 `raise SystemExit(0)` 皆判通過（§9.9.7；R6 新增，這一列是 R4「一般性只在單一樣本上驗證」的直接處置） |

**另須斷言**：`assign` 的程式路徑中**不存在**任何「解析失敗 → 記錄後 `continue`」的分支（`skipped_unparseable` 已移除）。此為結構性斷言，衍生卡須以測試覆蓋第 44 列的**退出碼**而非僅訊息文字。

### 9.7 真實資料調查（生成式證據）

**驗證 1 要求納入 #16／#22 真實反例，本節使其可重跑。** 下列程式對 Project #4 的活卡跑三條規則並輸出對照，同時盤點 §8.7 的 fail-closed 阻擋名單；衍生卡須將其納入 repo（需 `amend` 擴充資源宣告）並在 CI 或交付報告中附上輸出。**唯讀，不寫入任何狀態面。**

```python
# §9.7 對 Project #4 活卡跑 A/B/C 三規則 + 無法解析宣告的 fail-closed 盤點。
# 依賴：wf_cli（gh CLI 已登入）。唯讀。
# probe-requires: 網路與 gh 憑證，list_items 打 GitHub API
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
# probe-requires: 網路與 gh 憑證，list_items 打 GitHub API
# 註：本區塊以四個反引號圍起，因為程式內含 ``` 字面（MIG1_JSON 正則要比對 fenced JSON）。
# 註：所有含反斜線的正則一律先編譯成模組層常數，不得內嵌進 f-string 的取值部——
#     那在 Python 3.12 以前是 SyntaxError（§9.9 的自檢以真實 <=3.11 直譯器編譯本區塊來擋）。
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

下列程式**抽出目標文件全部 `python` 圍籬區塊**，把每一段交給一個**版本不高於宣稱可攜下限的真實直譯器**編譯，並實際執行其中未宣告需要外部資源者。它自身也是一個 `python` 區塊，因此**會抽到自己**（以行首錨定的 `# probe-self` 標記避免遞迴執行，但仍受閘門編譯）。**無網路、無 `wf_cli` 依賴；退出碼非 0 即失敗，可直接掛 CI。**

> **R3-001 的處置（R4 重寫）**：前一版用**執行中的直譯器** `ast.parse` 加一道「f-string 取值部反斜線」掃描來宣稱 3.11 可攜性。那個宣稱兌現不了——在 3.12+ 上跑，任何**其他** 3.12+ 新語法都會編譯通過又不被掃描命中。R4 改為查核者 disposition 的**第 1 條**：以真實舊直譯器實際編譯。為什麼不走第 2 條（版本化語法閘門），見 §9.9.2 的機械反例。
>
> **R6 的處置（本輪）**：R4 的自檢**只在本檔上驗過**，[#23](https://github.com/ruan6047/ai-workflow/issues/23) 第一次把它原樣指向別的文件就踩到三個缺陷（假陽性、靜默的覆蓋損失、恆真檢查）。本輪把三者連同兩個同族的隱性假設一併關掉，並在**本檔以外的文件上實跑取證**（§9.9.7）。R4 犯的是與 R3-001 同一個形狀的錯：**一般性宣稱只在單一樣本上兌現**——詳見 §9.9.8。

**逐檔登記（本輪新增）。** 自檢不再對目標文件做任何推斷，三件事全部由文件**顯式登記**，且全部**行首錨定**，不做「原始碼含某子字串」那種寬鬆比對：

- 文件層 `<!-- probe-blocks: N -->`（本檔的登記行即下一行，markdown 不渲染）：宣告本檔登記幾個探針區塊。**缺登記即 fail-closed**，理由見 §9.9.1-E。
- 區塊層 `# probe-self`：本區塊即自檢自身，抽到時不遞迴執行。
- 區塊層 `# probe-requires: <理由>`：本區塊需要網路／憑證等外部資源，自檢只編譯不執行；**理由必須寫出來**，因為它是「這支探針的執行覆蓋被放棄了」的唯一留痕。**未登記者一律執行**——預設是做事，跳過才需要理由（§9.9.1-D）。

<!-- probe-blocks: 4 -->

```python
# §9.9 探針自檢：抽出目標文件全部 python 探針，交給一個版本**不高於**宣稱可攜下限的真實直譯器
# 逐一編譯，並實際執行未登記需外部資源者。找不到這種直譯器即 fail-closed。
# 三個登記標記全部行首錨定（見本節正文）：文件層 probe-blocks、區塊層 probe-self／probe-requires。
# 無網路、無 wf_cli 依賴；退出碼非 0 即失敗，可直接掛 CI。
# probe-self
import ast, os, pathlib, re, shutil, subprocess, sys

DOC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "docs/WF_RESOURCE_WRITESET1.md")
TICK = chr(96)                   # 反引號；不寫字面，以免本區塊被自己的內容提前關閉
FLOOR = (3, 11)                  # cli/pyproject.toml 的 requires-python 下限
OPENER = re.compile("^(" + TICK + "{3,})python[ \t]*$")
BLOCKS_DECL = re.compile("^<!--[ \t]*probe-blocks:[ \t]*([0-9]+)[ \t]*-->[ \t]*$")
SELF_MARK = re.compile("^#[ \t]*probe-self[ \t]*$", re.M)
EXTERNAL_MARK = re.compile("^#[ \t]*probe-requires:[ \t]*(\\S.*)$", re.M)
VER = "import sys; print('%d.%d.%d' % sys.version_info[:3])"
COMPILE = "import ast, sys; ast.parse(sys.stdin.read())"


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


def declared_blocks(text):
    """逐檔登記的區塊數。回傳 (值, 診斷)；值為 None 代表未登記或登記互相矛盾 → fail-closed。
    這一格在 R4 是寫死的常數 4——那是**本檔**的區塊數，在區塊數多於 4 的文件上恆真（#23 指名）。"""
    vals = [int(m.group(1)) for m in (BLOCKS_DECL.match(ln) for ln in text.splitlines()) if m]
    if not vals:
        return None, "文件未登記區塊數"
    if len(set(vals)) > 1:
        return None, "文件登記了互相矛盾的區塊數 " + repr(sorted(set(vals)))
    return vals[0], "文件登記 %d 個" % vals[0]


def gate_candidates():
    """列出可當閘門的直譯器 [(版本, 路徑)]；版本一律由直譯器自報，不從檔名推斷。"""
    names = ["python3.%d" % m for m in range(FLOOR[1], 5, -1)] + ["python3", "python"]
    paths = [shutil.which(n) for n in names] + ["/usr/bin/python3", sys.executable]
    found, seen = [], set()
    for p in paths:
        if not p: continue
        real = os.path.realpath(p)
        if real in seen: continue
        seen.add(real)
        try:
            r = subprocess.run([p, "-c", VER], capture_output=True, text=True, timeout=30)
        except OSError:
            continue
        if r.returncode: continue
        v = tuple(int(x) for x in r.stdout.strip().split("."))
        if v[:2] <= FLOOR: found.append((v, p))
    return sorted(found, reverse=True)


def floor_hint(src):
    """單向診斷。ast 的 feature_version 是 best-effort：它**接受** f-string 取值部反斜線
    （正是 R2-001 那個 case），所以『接受』不帶任何資訊，只有『拒收』可採信。
    因此它永遠不得當閘門，也不得用來放行。"""
    if sys.version_info[:2] < FLOOR: return ""
    try:
        ast.parse(src, feature_version=FLOOR)
    except SyntaxError:
        return f"；feature_version={floor} 亦拒收 → 確屬下限違例"
    return (f"；feature_version={floor} 未複現——該閘門 best-effort 且已知漏 PEP 701 這類，"
            "故『接受』不代表下限合法；要分辨真違例與嚴於下限的誤拒只能裝真 3.11 複驗")


text = DOC.read_text(encoding="utf-8")
probes, failures, ran = extract(text), [], 0
run_ver = ".".join(str(n) for n in sys.version_info[:3])
floor = "%d.%d" % FLOOR
cands = gate_candidates()
exact = [c for c in cands if c[0][:2] == FLOOR]
gate = exact[0] if exact else (cands[0] if cands else None)
mode = "exact" if exact else ("stricter" if cands else "none")
print(f"探針自檢：{DOC}；抽出 python 區塊 {len(probes)} 個；執行直譯器 {run_ver}；宣稱可攜下限 {floor}")
if gate is None:
    print(f"可攜門檻：找不到版本 ≤ {floor} 的直譯器 → 無法佐證")
    failures.append(("整份", f"本機無版本 ≤ {floor} 的直譯器，可攜性宣稱無從佐證（fail-closed）"))
else:
    gv = ".".join(str(n) for n in gate[0])
    kind = "等於下限" if mode == "exact" else "低於下限：嚴於宣稱而非等價，見 §9.9.1"
    print(f"可攜門檻：{gv}（{gate[1]}）｜模式 {mode}（{kind}）")
declared, decl_note = declared_blocks(text)
print(f"區塊數登記：{decl_note}")
if declared is None:
    failures.append(("整份", decl_note + "；無登記即無從察覺區塊被刪掉，fail-closed（§9.9.1-E）"))
elif declared != len(probes):
    failures.append(("整份", f"抽到 {len(probes)} 個區塊，與文件登記的 {declared} 個不符"))
for start, end, src in probes:
    label, note, ok_exec = f"L{start}-{end}", [], False
    if gate is not None:
        r = subprocess.run([gate[1], "-c", COMPILE], input=src, capture_output=True, text=True)
        if r.returncode:
            tail = (r.stderr.strip().splitlines() or ["(無 stderr)"])[-1]
            extra = floor_hint(src) if mode == "stricter" else ""
            failures.append((label, f"閘門 {'.'.join(str(n) for n in gate[0])} 編譯失敗：{tail}{extra}"))
            print(f"  {label}：閘門編譯失敗"); continue
        note.append("閘門編譯 OK")
    try:
        tree = ast.parse(src, f"{DOC}:{start}")
    except SyntaxError as exc:
        failures.append((label, f"執行直譯器編譯失敗：{exc}")); print(f"  {label}：編譯失敗"); continue
    ext = EXTERNAL_MARK.search(src)
    if SELF_MARK.search(src):
        note.append("自身，不遞迴執行")
    elif ext:
        note.append("依區塊內登記需外部資源，僅編譯（" + ext.group(1).strip() + "）")
    else:
        print(f"  {label}：↓ 以下為該探針原樣執行的輸出")
        ns = {"__name__": "__main__"}     # 原樣執行＝當腳本跑，__main__ 守衛必須成立（§9.9.1-F）
        saved_argv = sys.argv[:]
        sys.argv = [f"{DOC}#{label}"]     # 不把自檢自己的引數漏給探針（§9.9.1-F）
        try:
            exec(compile(tree, f"{DOC}:{start}", "exec"), ns)
        except SystemExit as exc:         # 退出碼 0／None＝乾淨結束，不是拋錯（§9.9.1-C）
            code = 0 if exc.code is None else exc.code
            if code == 0:
                ok_exec = True; note.append("已執行（SystemExit 0＝乾淨結束）")
            else:
                failures.append((label, f"探針以非 0 狀態結束：SystemExit({exc.code!r})"))
                note.append("執行失敗")
        except KeyboardInterrupt:
            raise                          # 使用者中斷不是探針缺陷，往外拋而非記成 FAIL
        except BaseException as exc:
            failures.append((label, f"執行拋錯：{type(exc).__name__}: {exc}")); note.append("執行失敗")
        else:
            ok_exec = True; note.append("已執行")
        finally:
            sys.argv = saved_argv
        if ok_exec:
            ran += 1
            if ns.get("ok") is False: failures.append((label, "該探針自身斷言判 FAIL"))
    print(f"  {label}：{'；'.join(note) or '—'}")
print(f"實際執行 {ran} 個離線探針；違例 {len(failures)} 筆")
for label, msg in failures: print(f"  [FAIL] {label}：{msg}")
print(f"[裁決] {'PASS' if not failures else 'FAIL'}")
sys.exit(1 if failures else 0)
```

#### 9.9.1 它檢查什麼，為什麼是這七件

A、B、C 是 R4 定下的可攜性主幹，未改；D–G 是 R6 為了讓它在**別人的文件**上也成立而改的。

**A. 閘門直譯器的選取（`gate_candidates`）。** 候選是 PATH 上的 `python3.6`–`python3.11`、`python3`、`python`，加上 `/usr/bin/python3` 與 `sys.executable`；**版本一律問直譯器本人**，不從檔名推斷——本機的 `/usr/bin/python3` 就是 3.9.6，而 PATH 上根本沒有叫 `python3.9` 的東西，信檔名會整批漏掉。取到恰為 3.11 者 → 模式 `exact`；否則取**低於下限中版本最高者** → 模式 `stricter`。

**B. 逐區塊交給閘門實際編譯**（`subprocess` + `ast.parse(stdin)`）。這是 R3-001 disposition 的第 1 條：**不是**在執行中的直譯器上掃已知形狀，而是讓一個真的跑不動高版本語法的直譯器去拒收。它沒有「已知形狀」清單，因此攔得下 f-string 反斜線以外的任意高版本語法（§9.9.4 的變異 (b) 即為此而設）。

**C. 找不到 ≤ 3.11 的直譯器 → fail-closed**（§9.6 第 57a 列）。**這是 R3-001 的核心**：前一版在這個情形會退回用執行中的直譯器編譯，於是在 3.12+ 的 CI 上靜默 PASS，宣稱與證據脫節。現在該情形直接 `[FAIL]` 並非 0 退出。

**D. 退出碼 0 的 `SystemExit` 是乾淨結束，不是拋錯**（R6 修，#23 §4.4.1 第 1 項）。R4 寫的是 `except BaseException`，而 `SystemExit` 是 `BaseException` 的子類——以 `sys.exit(0)` 或 `raise SystemExit(0)` 結束的探針一律被記成「執行拋錯」判 FAIL。#23 的 §4.5 與 §7.1 兩支探針**自身裁決全過**（同一份輸出裡就印著「失敗項 = 0」「未登錄 gh 子指令 = 0」）卻被判 FAIL，是**自檢的假陽性**，不是探針的缺陷。現在：`code` 為 `0` 或 `None` → 計入「已執行」；其餘（含字串型 `code`）→ 判 FAIL 並印出實際 code。同一批 `BaseException` 子類一併檢過：`KeyboardInterrupt` 現在**往外拋**而不是記成探針失敗——使用者中斷不是被測物的缺陷，把它記成 FAIL 會產生一筆假的違例紀錄。

> **為什麼不反過來要求探針改用模組層 `ok`**：退出碼是 CI 唯一真正會看的訊號，而 `raise SystemExit(1 if bad else 0)` 是它的原生表達。要求別人為了配合自檢改掉更強的約定，是把自檢的缺陷轉嫁給被檢者。`ok` 慣例仍然支援（§9.8 用它），兩者並存。

**E. 區塊數改為逐檔登記**（R6 修，#23 指名）。R4 寫的是 `len(probes) < 4`，那個 `4` 是**本檔**的區塊數。#23 的文件恰好也是 4 純屬巧合；在區塊數本來就多於 4 的文件上，這是**恆真檢查**——「刪掉一個探針區塊」的變異抓不到。現在改讀文件自己的 `probe-blocks` 登記行，並用 `!=` 而非 `<`（多出未登記的區塊同樣是不符，§9.9.4 變異 (c2)）。**缺登記 → fail-closed**，與 C 同一個原則：無從驗證的不變式不得靜默視為成立。代價是採用本自檢的文件必須加一行；那一行是它宣告自己受此不變式保護的唯一憑據。

**F. 執行環境不再洩漏自檢自己的狀態**（R6 修，(d) 的判斷）。R4 用 `ns = {"__name__": "__probe__"}`，且把自檢自己的 `sys.argv` 原樣留給探針。兩者都是**靜默的覆蓋損失**，與 (b) 同族：

- `__name__` 現在設為 `"__main__"`。R4 那個值的原意大概是「避免探針被當腳本執行」，但**方向是反的**：本節宣稱的是「探針可原樣抽出執行」，而原樣執行就是 `python probe.py`，那時 `__name__` 就是 `"__main__"`。以 `if __name__ == "__main__":` 包住主體的探針在 R4 下會**整支不執行卻仍判 PASS**——文件今日零實例，但這是慣用寫法，第一個這樣寫的採用者就會中。
- `sys.argv` 現在在執行期間換成 `[f"{DOC}#{label}"]`，結束後還原。R4 會把自檢的引數漏進去：#23 的 §4.4 探針正是 `mode = sys.argv[1] if len(sys.argv) > 1 else "base"`，一旦執行就會把**目標文件路徑**當成模式名。這一條在 R4 從未浮現，只因為 §4.4 被 (b) 的錯誤推論擋在執行之外——**一個缺陷遮住另一個缺陷**。
- **未提供 `__file__`**：用到它的探針會以 `NameError` 判 FAIL。這是 fail-closed 的已知粗糙面，不是靜默跳過，故不補。

**G. 兩個區塊層標記都改為行首錨定的正則，不再用「原始碼含某子字串」。** R4 判自身用 `SELF in src`（`src` 任何位置出現 `probe-selfcheck` 即不執行）。那正是本檔在別處反覆點名的病：**用寬鬆的字面比對代替結構判定，代價是安靜地少做事**——任何在探針裡提到該字串的文件都會被靜默跳過一整個區塊。現在 `# probe-self` 與 `# probe-requires:` 都必須是**整行的註解**才算數。

**執行仍在「執行中的」直譯器上，不在閘門上**：閘門負責編譯（可攜性），執行負責語意。這是刻意的——`stricter` 模式下閘門是 3.9.6，在它上面**執行**會因 3.10／3.11 新增的**標準庫**（非語法）而產生與可攜性無關的假失敗。#23 §4.4.1 要求「§4.4 探針須在下限直譯器上實際執行」，那是**更強**的要求，需要 `exact` 模式（CI 釘 3.11）才安全；本自檢不宣稱做到它，歸屬見 §9.9.6。

##### `stricter` 模式嚴在哪、以及它唯一沒機械化的前提（明說，不含糊）

本機沒有 3.11，實跑用的是 3.9.6，所以本次交付的輸出是 `stricter` 而非 `exact`。這**嚴於**宣稱下限，不等價，具體是：

- **正向可用**：3.9 接受 ⇒ 3.11 接受。這一步靠的是「3.10／3.11 沒有移除任何 3.9 合法的語法」這個**前提**。它與 CPython 那兩版的變更紀錄相符，但本檔**沒有把它機械化**——這是本節唯一未由程式產生的環節，如實記在此處，不寫進任何「已證明」的句子。
- **反向會誤拒**：3.11 合法而 3.9 拒收者確實存在（3.10 的 `match`、3.11 的 `except*`）。若日後有探針用到這類語法，`stricter` 模式會**誤拒**。
- **誤拒的處置是 fail-closed，不放寬**：訊息會附一則單向診斷（`floor_hint`）。它只採信「`feature_version=3.11` **也**拒收 → 確屬違例」這一向；**「接受」不帶任何資訊**，理由見 §9.9.2。要真正分辨真違例與誤拒，只能裝一個 3.11 直譯器複驗（CI 上用 `setup-python` 釘 3.11 即可得到 `exact`，這是衍生卡該做的事，§9.9.6）。
- **現況**：本檔四個探針在 3.9.6 下**全數通過**，所以誤拒風險目前是零實例。那是現況，不是保證。

#### 9.9.2 為什麼不走 disposition 的第 2 條（版本化語法閘門）

第 2 條要求「等價且**可證明覆蓋完整** Python 3.11 語法」。標準庫裡唯一的現成候選是 `ast.parse(..., feature_version=)`，而 CPython 文件自述它是 best-effort、只影響語法的一個子集。這不是措辭保守，有機械反例——**它漏掉的正好就是 R2-001 那一個 case**：

```text
原始碼： print(f"{__import__('re').match(r'a\.b','a.b')}")
ast.parse(feature_version=(3,11)) → 接受，無例外
真實 3.9.6 直譯器 → SyntaxError: f-string expression part cannot include a backslash
```

**用它當閘門，會原樣放行本卡上一輪被打的那個 bug。** 要讓第 2 條成立，就得自備一份完整的 3.11 文法並證明其覆蓋完整——那正是「宣稱大於證據」的典型，也是本卡連兩輪被打的形態。故本輪明確放棄第 2 條，並把它記為已裁定的非目標。

#### 9.9.3 在修正前的檔案上執行的輸出（反向驗證）

自檢若只在修好之後跑一次，證明不了它抓得到東西。以 **R2 交付版**（`cb6028f`）的檔案為輸入，用 **R6 這一版**的自檢重跑：

```text
探針自檢：…/r2.md；抽出 python 區塊 3 個；執行直譯器 3.14.3；宣稱可攜下限 3.11
可攜門檻：3.9.6（/usr/bin/python3）｜模式 stricter（低於下限：嚴於宣稱而非等價，見 §9.9.1）
區塊數登記：文件未登記區塊數
  L609-664：↓ 以下為該探針原樣執行的輸出
  L609-664：閘門編譯 OK；執行失敗
  L692-733：閘門編譯失敗
  L768-855：↓ 以下為該探針原樣執行的輸出
  L768-855：閘門編譯 OK；已執行
實際執行 1 個離線探針；違例 3 筆
  [FAIL] 整份：文件未登記區塊數；無登記即無從察覺區塊被刪掉，fail-closed（§9.9.1-E）
  [FAIL] L609-664：執行拋錯：ModuleNotFoundError: No module named 'wf_cli'
  [FAIL] L692-733：閘門 3.9.6 編譯失敗：SyntaxError: f-string expression part cannot include a backslash；feature_version=3.11 未複現——該閘門 best-effort 且已知漏 PEP 701 這類，故『接受』不代表下限合法；要分辨真違例與嚴於下限的誤拒只能裝真 3.11 複驗
[裁決] FAIL
```

（`[1]`–`[4]` 等 §9.8 自身巢狀印出的輸出此處略去；退出碼 `1`。）

三筆逐一對：**第三筆是 R2-001 本身**——新閘門在沒有任何「f-string」專用知識的情況下抓到了同一段，它只是把那段碼丟給 3.9.6 去編譯，與查核者當初手動 `sed -n '694,733p' | python3` 撞到的是同一處。第一筆是該檔沒有 `probe-blocks` 登記行（R2 版連 §9.9 都還不存在）。**第二筆是 R6 的行為改變，不是 R2 檔的新缺陷**：R4 靠「有沒有 import `wf_cli`」把 §9.7 擋在執行外，R6 改成未登記即執行，於是它在無 `wf_cli` 的環境下如實失敗。這正是 §9.9.1-D／G 要的方向——**跳過要有登記，沒登記就吵**，而不是靜默少做事。

#### 9.9.4 變異測試：八種變異，八次非 0（§9.6 第 57／57a／57b 列）

(a)(b) 植入本檔 §9.7b 探針的首行之後（該區塊只編譯不執行——**刻意選它**，證明「從不執行的區塊」一樣被守住）。全部以同一支自檢、同一條命令跑：

```text
變異 (a) f-string 取值部含反斜線（PEP 701，3.12+ 才合法）　　退出碼 1
  [FAIL] L718-765：閘門 3.9.6 編譯失敗：SyntaxError: f-string expression part cannot include a backslash；feature_version=3.11 未複現……

變異 (b) type _MutAlias = int（PEP 695 型別別名語句，3.12+ 才合法，與 f-string 無關）　　退出碼 1
  [FAIL] L718-765：閘門 3.9.6 編譯失敗：SyntaxError: invalid syntax；feature_version=3.11 亦拒收 → 確屬下限違例

變異 (c) 刪去 §9.8 整個探針區塊　　退出碼 1
  區塊數登記：文件登記 4 個
  [FAIL] 整份：抽到 3 個區塊，與文件登記的 4 個不符

變異 (c2) 新增一個未登記的探針區塊　　退出碼 1
  [FAIL] 整份：抽到 5 個區塊，與文件登記的 4 個不符

變異 (c3) 刪掉 probe-blocks 登記行本身　　退出碼 1
  區塊數登記：文件未登記區塊數
  [FAIL] 整份：文件未登記區塊數；無登記即無從察覺區塊被刪掉，fail-closed（§9.9.1-E）

變異 (c4) 植入第二行互相矛盾的登記　　退出碼 1
  區塊數登記：文件登記了互相矛盾的區塊數 [4, 7]
  [FAIL] 整份：文件登記了互相矛盾的區塊數 [4, 7]；無登記即無從察覺區塊被刪掉，fail-closed（§9.9.1-E）

變異 (e) 把 §9.8 探針的結尾改成 raise SystemExit(3)　　退出碼 1
  [FAIL] L803-891：探針以非 0 狀態結束：SystemExit(3)

變異 (f) 拿掉 §9.7 的 probe-requires 登記行　　退出碼 1
  [FAIL] L630-685：執行拋錯：ModuleNotFoundError: No module named 'wf_cli'

情境 (57a) 把 FLOOR 改成本機不存在的 (3, 6) 以觸發「無可用閘門」分支　　退出碼 1
  可攜門檻：找不到版本 ≤ 3.6 的直譯器 → 無法佐證
  [FAIL] 整份：本機無版本 ≤ 3.6 的直譯器，可攜性宣稱無從佐證（fail-closed）
```

**變異 (b) 是 R4 新增的、查核者指定的非 f-string 高版本語法變異**。它的意義不在於「PEP 695 也被擋住」，而在於：閘門攔下它時**沒有用到任何關於 PEP 695 的知識**——R3 的 AST 掃描只認得 f-string 反斜線，對 (b) 會靜默放行，這正是 R3-001 的實證。(b) 的診斷欄顯示 `feature_version` 這次**有**複現，(a) 則沒有；同一份診斷在兩個真違例上一真一假，正是 §9.9.2 拒絕第 2 條的理由。

**(c2)–(c4)、(e)、(f) 是 R6 新增，全部針對「只在自己文件上成立」那個病**：(c2) 釘住 `!=` 而非 `<`；(c3)(c4) 釘住「缺登記／登記矛盾一律 fail-closed」，否則 §9.9.1-E 的登記機制自己就有一條靜默放行路徑；(e) 釘住 D 的**非 0** 那一半——只把 `SystemExit(0)` 放行而不擋非 0，等於把 R4 的假陽性換成假陰性；(f) 釘住 G 的方向：拿掉登記後該探針是**吵著失敗**而不是靜默跳過。

**唯一沒有變異覆蓋的是 §9.9.1-F 的兩項**（`__name__`、`sys.argv`）——它們在本檔零實例，植入變異就等於自己造一個實例。改以**第三份文件**取證，見 §9.9.7 的 (2)。

#### 9.9.5 在本次交付版上的輸出

```text
探針自檢：docs/WF_RESOURCE_WRITESET1.md；抽出 python 區塊 4 個；執行直譯器 3.14.3；宣稱可攜下限 3.11
可攜門檻：3.9.6（/usr/bin/python3）｜模式 stricter（低於下限：嚴於宣稱而非等價，見 §9.9.1）
區塊數登記：文件登記 4 個
  L630-686：閘門編譯 OK；依區塊內登記需外部資源，僅編譯（網路與 gh 憑證，list_items 打 GitHub API）
  L718-764：閘門編譯 OK；依區塊內登記需外部資源，僅編譯（網路與 gh 憑證，list_items 打 GitHub API）
  L803-890：↓ 以下為該探針原樣執行的輸出
  L803-890：閘門編譯 OK；已執行
  L936-1086：閘門編譯 OK；自身，不遞迴執行
實際執行 1 個離線探針；違例 0 筆
[裁決] PASS
```

（略去 §9.8 在 `L803-890` 執行時巢狀印出的 `[1]`–`[4]` 與其 `[裁決] PASS`；退出碼 `0`。）

四個區塊即 §9.7（`L630-686`）、§9.7b（`L718-764`）、§9.8（`L803-890`）、§9.9 自身（`L936-1086`）。**行號會隨本檔任何編輯而漂移，所以它由自檢輸出，不寫進正文其他地方**；本節四組行號全部落在 §9.9.5 之前，因此本節後續的編輯不會使它們失效。

**只有一支探針被實際執行，而這一次那是有登記的**：§9.7／§9.7b 的「僅編譯」現在來自兩者區塊內的 `probe-requires` 註解，理由印在輸出裡；R4 那一版印的「需 gh 登入」是自檢自己**推斷**出來的，那個推斷在 #23 的文件上就錯了（§9.9.7）。

**模式欄是 `stricter` 不是 `exact`，這是本次交付的實際狀態**：本機無 3.11 直譯器，閘門是 3.9.6。§9.9.1 已把「嚴於而非等價」與其唯一前提寫死在該處，不在此處重述。

#### 9.9.6 CI 歸屬與行號的自動化

- **CI**：衍生卡須把本探針落成 repo 內腳本並掛進 CI（§9.6 第 57／57a 列、§10），且 **CI runner 必須備妥 3.11 直譯器**（`actions/setup-python` 釘 `3.11` 即可），讓閘門在 CI 上是 `exact` 而非 `stricter`——本次交付因本機無 3.11 只能給 `stricter`，那是環境限制，不該被繼承成永久狀態。§9.6 第 57a 列同時保證：runner 若連 ≤ 3.11 都沒有，CI 是紅的而不是綠的。
- **本卡只宣告 `docs/WF_RESOURCE_WRITESET1.md` 一個資源，不得新增 workflow 或 script 檔案**——這是資源宣告互斥語意的卡在自己身上的應用，不是偷懶。上一段那個「CI 上裝 3.11」的要求，本卡同樣只能寫成規格，不能自己去改 workflow。
- **行號**：上列輸出的 `L<起>-<訖>` 即各探針在本檔中的行號區間，**由程式列出、不由人維護**。查核者若要沿用手動 `sed -n '<起>,<訖>p' docs/WF_RESOURCE_WRITESET1.md | PYTHONPATH=cli/src python3` 的重現方式，直接讀該次自檢輸出即可，不必信任文件裡任何寫死的行號。
- **在下限直譯器上「執行」**（不只編譯）是 #23 §4.4.1 對其實作卡 A 提的要求，比本自檢做的多一層。本自檢只在**執行中的**直譯器上執行（§9.9.1 末段），理由是 `stricter` 模式下在 3.9.6 執行會產生與可攜性無關的標準庫假失敗。CI 釘 3.11 取得 `exact` 後兩者才等價，那同樣在衍生卡。

#### 9.9.7 在本檔以外的文件上實跑（R6 的核心取證）

R4 的一般性宣稱是「這支自檢可以驗證**任何**文件的探針可攜性」，而它只在本檔上跑過。本節是那個宣稱第一次被外部樣本檢驗。

**(1) [#23](https://github.com/ruan6047/ai-workflow/issues/23) 的 `docs/WF_EVENT_IDEMPOTENCY1.md`（`claude/WF-EVENT-IDEMPOTENCY1` 分支，一字未改）。** 該檔不在本卡寫入集內，故以 `git show` 取出到工作區外執行；R6 版自檢、退出碼 `1`：

```text
探針自檢：…/WF_EVENT_IDEMPOTENCY1.md；抽出 python 區塊 4 個；執行直譯器 3.14.3；宣稱可攜下限 3.11
可攜門檻：3.9.6（/usr/bin/python3）｜模式 stricter（低於下限：嚴於宣稱而非等價，見 §9.9.1）
區塊數登記：文件未登記區塊數
  L256-366：↓ 以下為該探針原樣執行的輸出
  L256-366：閘門編譯 OK；已執行（SystemExit 0＝乾淨結束）
  L511-580：↓ 以下為該探針原樣執行的輸出
  L511-580：閘門編譯 OK；已執行（SystemExit 0＝乾淨結束）
  L730-845：↓ 以下為該探針原樣執行的輸出
  L730-845：閘門編譯 OK；已執行（SystemExit 0＝乾淨結束）
  L936-969：↓ 以下為該探針原樣執行的輸出
  L936-969：閘門編譯 OK；已執行
實際執行 4 個離線探針；違例 1 筆
  [FAIL] 整份：文件未登記區塊數；無登記即無從察覺區塊被刪掉，fail-closed（§9.9.1-E）
[裁決] FAIL
```

（四支探針巢狀印出的內容此處略去；`L256-366` 印出的首行是 `[base] 直譯器 = 3.14.3`，`[base]` 三個字就是 §9.9.1-F 的 `sys.argv` 隔離生效的證據——R4 會在該處印出目標文件的完整路徑。）

**四個區塊全部正確處理**，逐一對照 #23 §4.4.1 指名的兩項：`L256-366`（其 §4.4，`from wf_cli.cli import build_parser` 做 argparse 內省）**實際執行**而非只編譯，這是 (b) 修好的直接證據；`L511-580`／`L730-845`（其 §4.5／§7.1，以 `raise SystemExit(0)` 乾淨結束）判為已執行，這是 (a) 修好的直接證據。R4 在同一份文件上對這三支各給一次錯判（一次靜默跳過、兩次假陽性 FAIL）。

**剩下那一筆 `[FAIL]` 是真的，不是假陽性。** 它說的是事實：該檔沒有 `probe-blocks` 登記行，因此「區塊被刪掉」這個不變式在它身上**無從驗證**。處置與 §9.9.1-C 同一原則——不可驗證即不得靜默視為成立。它也正是 #23 自己指名要求的機制（「共用腳本須改為逐檔登記」），所以該檔補上一行登記即可，動作在 #23 的寫入集內、不在本卡。為證明只差那一行，把該檔複製到工作區外**只加一行登記、其餘一字未改**再跑一次，退出碼 `0`：

```text
區塊數登記：文件登記 4 個
  L258-368：閘門編譯 OK；已執行（SystemExit 0＝乾淨結束）
  L513-582：閘門編譯 OK；已執行（SystemExit 0＝乾淨結束）
  L732-847：閘門編譯 OK；已執行（SystemExit 0＝乾淨結束）
  L938-971：閘門編譯 OK；已執行
實際執行 4 個離線探針；違例 0 筆
[裁決] PASS
```

**(2) 第三份文件：三個約定的最小樣本。** #23 的文件湊不齊 §9.9.1-F 的兩項（它沒有 `__main__` 守衛），故另備一份只含三個區塊的最小文件，把 A=`__main__` 守衛＋`sys.argv` 內省、B=`probe-requires` 登記、C=`sys.exit(0)` 各釘一格。同一份文件、兩支自檢：

```text
── R4（修正前）　退出碼 1
A: 這行不該被印出——守衛沒生效
  L6-11：閘門編譯 OK；已執行
  L15-17：閘門編譯 OK；執行失敗
  L21-24：閘門編譯 OK；執行失敗
實際執行 1 個離線探針；違例 3 筆
  [FAIL] 整份：只抽到 3 個區塊，少於本檔登記的 4 個
  [FAIL] L15-17：執行拋錯：ModuleNotFoundError: No module named 'wf_cli_does_not_exist'
  [FAIL] L21-24：執行拋錯：SystemExit: 0
[裁決] FAIL

── R6（本輪）　退出碼 0
區塊數登記：文件登記 3 個
A: __name__ = __main__ argv 額外引數 = []
  L6-11：閘門編譯 OK；已執行（SystemExit 0＝乾淨結束）
  L15-17：閘門編譯 OK；依區塊內登記需外部資源，僅編譯（假裝需要憑證）
  L21-24：閘門編譯 OK；已執行（SystemExit 0＝乾淨結束）
實際執行 2 個離線探針；違例 0 筆
[裁決] PASS
```

R4 那一欄四種錯法同時現形：`A: 這行不該被印出` 是 `__name__` 造成的**整支不執行卻仍計入「已執行」**（§9.9.1-F）；`ModuleNotFoundError` 是 `imports_wf_cli` 的名稱比對對 `wf_cli_does_not_exist` 不成立（**它的判準連自己那條規則都是脆的**）；`SystemExit: 0` 是 (a)；`少於本檔登記的 4 個` 是 (c) 那個常數在一份只有 3 個區塊的文件上給出的錯話。R6 那一欄的 `argv 額外引數 = []` 與 `__name__ = __main__` 是 F 兩項的直接證據。

#### 9.9.8 R6 的自我歸因：同一個形狀，第四次

R3-001 打的是「§9.9 宣稱一般性可攜，實作只兌現一個特例」。**R4 的修法有同一個形狀，只是換了一層**：它把「一般性可攜性檢查」做出來了，但那個**一般性只在本檔上驗證過**——第一次被指向別的文件就同時暴露三個缺陷，其中兩個（`SystemExit`、`__name__`／`argv`）是**靜默的或假陽性的**，一個（`len(probes) < 4`）在別人的文件上是**恆真的**。

用 R4 自己寫下的那把量尺（「已寫下的宣稱有多少沒兌現」）重檢一次 §9.9 的文字：

| §9.9 寫下的宣稱 | R4 的實際狀態 | R6 |
|---|---|---|
| 「抽出**本檔**全部 python 區塊」 | 兌現 | 兌現（改為「目標文件」） |
| 「交給版本不高於下限的真實直譯器編譯」 | 兌現 | 未改 |
| 「實際執行其中不需網路者」 | **未兌現**：判準是 import 圖不是網路需求，#23 §4.4 因此被跳過 | 改為顯式登記，未登記即執行 |
| 「退出碼非 0 即失敗，可直接掛 CI」 | **未兌現**：乾淨結束的探針被判失敗，掛上 CI 會紅 | `SystemExit(0)` 視為通過 |
| §9.6 第 57 列「刪掉一個探針區塊 → 非 0」 | 只在本檔成立 | 逐檔登記 |
| 「探針可**原樣**抽出執行」 | **未兌現**：`__name__` 與 `sys.argv` 都不是原樣 | 兩者對齊 `python probe.py` |

**六條裡有三條在別人的文件上不成立，而它們全部寫在本卡、實作也在本卡。** 歸因與 R4 那次相同：不是歸屬遺漏、不是覆蓋率不足，是**宣稱與實作不一致**。差別在量尺又換了一次——R4 學會用「宣稱有多少沒兌現」代替「還要多做多少」，但**只在自己的文件上量**。這一輪補的是量的方法：**一般性宣稱要用一般性樣本量**，所以 §9.9.7 有三份文件而不是一份。

---

## 10. 歸屬

契約語意（§2–§8）定義在本卡。實作歸衍生卡（基線 §9-L）：

- `resources.py`：§2.1 正規化、§2.2 相交謂詞、§3 語彙拒收、§4 repo 限定詞、§8.1–§8.5 兩階段。
- `open_cmd.py`／`amend_cmd.py`：§3.4 拒收時機、§5.1 tracked symlink 逐分量走查、§7.1 存在性提示。
- `assign_cmd.py`：§5.3 realpath 與 containment、§6 revision 釘選與 TOCTOU、§4.2 repo 歸屬 fail-closed、**§8.6 不變式 I 的各站處置、§8.7 移除 `skipped_unparseable`、§8.8 `--ignore-unparseable` 與 `UNPARSEABLE_EXEMPTION_SUNSET` 常數**。
- `doctor.py`：§8.8.2 的母體殘量與距 sunset 天數輸出（唯讀報告）。
- **CI ＋ 一支 repo 內腳本**：§9.9 的探針自檢（抽取目標文件全部 `python` 區塊 → **以 ≤ 3.11 的真實直譯器編譯** ＋ 執行未登記需外部資源者），連同 §9.6 第 57 列的八個變異測試、第 57a 列的無閘門情境、**第 57b 列的跨檔一般性**；CI 須釘 3.11 以取得 `exact` 模式（§9.9.6）。腳本落地後即是 **repo 內的共用資產**，[#23](https://github.com/ruan6047/ai-workflow/issues/23) §4.4.1 已裁定沿用它而不另立第二套，該卡實作卡 A 另有一項更強的要求（§4.4 探針須在**下限直譯器上執行**而非只編譯），需 `exact` 模式才安全。**本卡不落地它**——本卡只宣告 `docs/WF_RESOURCE_WRITESET1.md`，新增腳本或 workflow 會逸出自己的寫入集。
- 測試：§9 全部 63 列（1–43 原有＋28a／28b＋44–57＋49a／49b／57a／57b 共 20 列新增）＋五項列舉式斷言（§9.2 零遷移負債、§9.3 第 28／28b、§9.6 第 54、§9.7／§9.7b／§9.8 的生成式輸出）。

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
7. **CLI 路徑引數的正規化**（`--worktree` 等）。§3.1 的封閉 namespace 只規範卡面 `file:` 資源宣告；兩者定義域不相容（此結論 [#23](https://github.com/ruan6047/ai-workflow/issues/23) §10 的 A3 同向認定），理由見該節的界線告示。**且此項目前無人擁有**：#23 已於 `d824d16` §4.1b／§10 裁定其六個承接動詞沒有任何引數需要檔案系統路徑正規化，因而不定義也不引用任何正規化器。**需要者不得逕行引用本節或 #23 當作實作依據**，須先照 §3.1 界線告示的判準追碼，仍需要時連同該節列的 (a)(b)(c) 三項舉證另行開卡。
8. **在單一直譯器內「證明覆蓋完整 Python 3.11 文法」的版本化語法閘門**（R3-001 disposition 的第 2 條）。經機械反例否決，理由與證據見 §9.9.2：唯一的現成候選 `ast.parse(feature_version=)` 是 best-effort，且**恰好漏掉 R2-001 那個 case**；自備完整文法即是本卡連兩輪被打的「宣稱大於證據」形態。本檔改走第 1 條（真實舊直譯器實際編譯），**並在 §9.9.1 明記其 `stricter` 模式不等價於下限**。

### 12.1 已從非目標移出並裁定的項目（記錄）

前一版（R1 交付）把「無法解析的資源宣告被靜默略過」列為本節第 6 項「提出但不裁定」。**R1 查核以 blocking finding 退回該處置，判定正確**：把一個已知的 fail-open 標為「不處理」，等於用文件把靜默放行合法化，與卡面「任何無法安全判定的情形一律拒絕派工」直接矛盾。

**現已裁定於 §8.6（不變式 I）、§8.7（fail-closed）、§8.8（具名／可稽核／到期的豁免），並納入 §9.6 矩陣第 44–56 列與 §10 的衍生卡歸屬。** 本節保留此段是為了讓「曾經被列為非目標」這件事留在紙上，而不是被無痕改寫。

殘留的 fail-open（含豁免本身）明列於 §8.9，**不宣稱已關閉**。

---

## 13. 執行者揭露

- 本檔為設計／契約文件，**無程式碼變更、無 CI**。§9 的矩陣**未被執行**，執行歸衍生卡。
- §1.1、§1.2、§3.2、§3.3、§4.1、§4.2、§8.2、§8.3、§8.7、§8.8、§9.7、§9.7b、§9.8 的所有數字，均由探查程式對真實 repo 與真實 Project #4 產生，非人工清點。四支探針（§9.7 活卡三規則、§9.7b 封閉母體普查、§9.8 離線窮舉、§9.9 探針自檢）**全部內嵌於本檔並可原樣抽出執行**，其中 §9.8 與 §9.9 不需網路與 `gh` 登入。「原樣」的精確定義（`__name__`／`sys.argv` 與 `python probe.py` 對齊，但**未**提供 `__file__`、未做行程隔離）見 §9.9.1-F 與本節 R6 自陳（三）。
- **上一句在 R2 交付版是假的，而它是我自己寫的。** R2 版逐字寫著「三支探針全部內嵌於本檔並可原樣重跑」，實際上 §9.7b 抽出來即 `SyntaxError`（f-string 取值部含反斜線，Python < 3.12），由查核者以 `sed | python3` 撞出（R2-001）。**這條紀律的教訓不是「要更小心」**：我在 Python 3.14 上寫、在 3.14 上驗，而該寫法在 3.14 合法——**同一份檔案在不同直譯器上有不同結果，靠自律看不見**。故 R3 不只修那一行，而是把「探針可原樣抽出執行」本身變成 §9.9 的機械檢查，並要求衍生卡以變異測試釘住它（§9.6 第 57 列）。
- **R3 處理 R2-001**：修 §9.7b 的可攜性缺陷並以修正後程式重跑（§9.7／§9.7b 同一 session，釘選 2026-08-12 01:28 +0800）、新增 §9.9 探針自檢與 §9.6 第 57 列、補 §3.1 的定義域界線告示與 §12 第 7 項（跨卡裁決，對 [#23](https://github.com/ruan6047/ai-workflow/issues/23)）、修正 §4.2 對 §9.7／§9.7b 的誤標，並在 §1.2／§9.7 記錄「線上反例已消失」與上一版把線上狀態誤當不變量的措辭錯誤。**§2、§3（除新增告示）、§5–§8 未改動；§9.8 一字未改**（其 `[裁決] PASS` 在 R3 由 §9.9 自動執行複現）。
- **R4 處理 R3-001**：§9.9 的自檢被判「兌現不了自己的一般性宣稱」——它固定宣稱 3.11 可攜，卻只掃一種已知形狀（f-string 反斜線）並用**執行中的**直譯器編譯，於是在 3.12+ 上任何**其他**高版本語法都會靜默通過。本輪把自檢改為 disposition 的**第 1 條**：以真實的 ≤ 3.11 直譯器 `subprocess` 實際編譯每個抽出的區塊，找不到這種直譯器即 fail-closed（§9.6 第 57a 列）。同時新增 §9.9.2（機械反例否決第 2 條）、§9.9.4（三種變異＋無閘門情境的實跑輸出）、§9.6 第 57 列的非 f-string 變異 (b)、§12 第 8 項。**§1–§8 一字未改；§9.1–§9.8 除第 57／57a 列外未改。**
- **R4 的自我歸因（歸屬判斷 vs 嚴重度誤判）**：**是嚴重度誤判，不是歸屬遺漏。** R3 的報告確實自陳「可攜性檢查只涵蓋 f-string 反斜線這一種形狀」，可見我**看見了**這個洞；錯在我把它記成「涵蓋率待擴充」，於是歸給衍生卡的 CI 設定。正確的量尺是：§9.9 的**文字宣稱**是「檢查跨直譯器版本可攜性」，那是一般性宣稱，而實作只兌現一個特例——**這不是覆蓋率不足，是宣稱與實作不一致，而宣稱寫在本卡、實作也寫在本卡，因此修它從來不需要逸出寫入集**（本輪的修正正是一個字都沒動到 `docs/WF_RESOURCE_WRITESET1.md` 以外）。我用「還要多做多少」當量尺，該用「已寫下的宣稱有多少沒兌現」當量尺。這與本卡連兩輪被打的是同一個病灶的第三次發作：**宣稱大於證據**，只是這次發作在自檢自己身上。
- **R5 處理跨卡對帳 X1，範圍限於兩處歸屬敘述**：R3 加的界線告示把 CLI 引數正規化**歸屬**給 #23，而 #23 本輪（`d824d16`）已明文拒絕承接——指標指向一張已拒收的卡，照著走過去會被告知那不存在。本輪把 §3.1 告示框與 §12 第 7 項改為「本卡不涵蓋 → #23 已裁定其六個承接動詞不需要 → 故目前無人擁有 → 需要者須自行舉證並開卡」，並把 #23 的判準（分類鍵＝對事件內容的貢獻）與其不可行性論證（`realpath` 對不存在路徑無定義、大小寫／NFC 敏感度是執行期檔案系統性質、摺疊過度＝靜默 `already_exists`）寫進告示，使誤引者拿得到判準而不只是拿到一句「沒人管」。**定義域不相容的結論未被修改**（兩側共同認定）；**§1–§11、§9 全部探針、§12 其餘各項一字未改**。
- **R6（本輪）處理自審迴圈找出的三個缺陷（非新一輪查核 finding），全部在 §9.9 自檢內**：(a) `except BaseException` 把 `SystemExit(0)` 當拋錯 → 退出碼 0／`None` 視為乾淨結束，`KeyboardInterrupt` 改為往外拋（§9.9.1-D）；(b) 「有 import `wf_cli` ⇒ 需憑證 ⇒ 只編譯」的推論不成立，造成靜默的覆蓋損失 → 改為區塊內 `probe-requires` 顯式登記，**未登記一律執行**（§9.9.1-D 段末、G）；(c) `len(probes) < 4` 是本檔區塊數的寫死常數，在區塊數多於 4 的文件上恆真（#23 指名）→ 改為文件層 `probe-blocks` 逐檔登記、`!=` 比對、缺登記 fail-closed（§9.9.1-E）。連帶修 (d)：`__name__` 由 `"__probe__"` 改為 `"__main__"`、執行期隔離 `sys.argv`（§9.9.1-F），兩者皆為與 (b) 同族的靜默覆蓋損失。新增 §9.9.7（三份文件的跨檔實跑）、§9.9.8（自我歸因）、§9.6 第 57b 列與第 57 列的五個新變異，並改 §10 的 CI 歸屬敘述（納入 57b 與 #23 §4.4.1 的沿用裁定）。§9.7／§9.7b 兩個區塊**各只多一行 `probe-requires` 註解**，兩支程式的可執行敘述與既有輸出未變。**改動全部落在第 619 行之後**（`git diff -U0` 的 hunk 起點可驗）：§1–§8、§9.1–§9.5、§11、§12 一字未改，§9.7／§9.7b／§9.8 的可執行敘述一字未改。
- **R6 的自我歸因**：見 §9.9.8。摘要——R4 修好了「可攜性宣稱只兌現一個特例」，但**它的一般性只在本檔上驗證過**，第一次被 #23 指向別的文件就同時暴露三個缺陷（兩個靜默／假陽性、一個恆真）。這是同一個病灶（宣稱大於證據）的第四次發作，且**發作點正是上一次的修法本身**。R4 學到的量尺（「已寫下的宣稱有多少沒兌現」）是對的，錯在**只在自己的樣本上量**；本輪的處置是把量的方法一併改掉——一般性宣稱用一般性樣本量，故 §9.9.7 有三份文件。
- **R2 處理 R1-001**：新增 §8.6–§8.9、§9.6 矩陣 13 列、§9.7b／§9.8 兩支探針，改寫 §4.2、§12.1，並補 §11 第 9／10 列。§2、§3、§5–§7 的既有內容未被修改（R1 查核已驗證通過的 `B ⊇ C`、窮舉 `b_misses_c=0`、`templates/` vs `templates2/a.md` 不相交三項結論在 §9.8 被重新生成並維持不變）。
- **R4 自陳，未修（一）：本次交付的可攜性閘門是 `stricter`（3.9.6）不是 `exact`（3.11）。** 本機沒有 3.11 直譯器（`uv python list` 顯示 3.11.15 僅「可下載」），而下載安裝直譯器是對開發機的環境變更、且查核者的機器未必跟進，故不做。**「3.9 通過 ⇒ 3.11 通過」是一個未機械化的前提**（依據是 3.10／3.11 未移除 3.9 合法語法），§9.9.1 已把它與「反向會誤拒 `match`／`except*`」一起明寫。要升級成 `exact`，動作是 CI 釘 3.11（§9.9.6），**那確實在衍生卡**——但這次的歸屬理由與 R3 那次不同：本卡能寫下的規格（第 57／57a 列、§9.9.6）已經寫完，剩下的只有 workflow 檔案本身，那是真的逸出寫入集。
- **R4 自陳，未修（二）：`floor_hint` 的診斷是單向的，本檔沒有辦法自動分辨「真違例」與「嚴於下限的誤拒」。** §9.9.4 的 (a)／(b) 兩個變異剛好示範了同一份診斷在兩個真違例上一真一假。目前的處置是**一律 fail-closed 並要求人去裝 3.11 複驗**——這在誤拒發生時會擋住合法的探針。本檔四支探針今日在 3.9.6 下全過，所以此洞**零實例**，但它是設計上真實存在的粗糙面，不是已解決。
- **R6 自陳，未修（一）：探針的「執行」仍在執行中的直譯器上，不在閘門上。** 閘門只負責編譯。#23 §4.4.1 對其實作卡 A 提的是更強的「在下限直譯器上**執行**」，本自檢不宣稱做到。不做的理由寫在 §9.9.1 末段（`stricter` 模式下在 3.9.6 執行會產生與可攜性無關的標準庫假失敗），要兩者等價得先有 `exact`（CI 釘 3.11，§9.9.6）。**這一條是刻意的射程界線，不是遺漏**，但它確實使「探針可原樣執行」只在**編譯**這一半上機械化。
- **R6 自陳，未修（二）：`probe-blocks` 登記與探針本體在同一份檔案裡，同一次編輯可以一起改掉。** 這個不變式擋得住「刪區塊忘了改登記」，擋不住「刪區塊順手改登記」——後者要靠 code review。它與 R4 那個寫死的 `4` 相比是嚴格變好（那個在別人的文件上根本不會響），但**不是密封的**。同理，`probe-requires` 是自我宣告：一支其實離線的探針貼上該登記就會被跳過，登記理由必須寫出來正是為了讓這件事在 review 時看得見。
- **R6 自陳，未修（三）：執行探針會污染自檢自己的行程狀態。** `sys.path`、`os.environ`、已 import 的模組在探針之間**不隔離**（#23 的 §4.4 探針就會 `sys.path.insert(0, "cli/src")`），因此區塊的執行順序理論上可影響結果，且探針必須從 repo root 執行才能解析相對路徑。真正的處置是每支探針各起一個子行程；那與「未修（一）」是同一個修法，一併歸 CI 落地那張卡。今日四支探針無此依賴，**是零實例，不是已解決**。
- **R6 自陳，未修（四）：把預設從「不執行」翻成「執行」，同時翻掉的還有一層意外的安全網。** R4 的錯誤推論（import `wf_cli` ⇒ 只編譯）順帶使**任何**碰狀態面的碼都不會被自檢跑到；R6 改成未登記即執行之後，一支會寫入狀態面或檔案系統的探針**會被真的執行**。這個方向仍是對的——靜默少做事比吵著失敗危險——但代價必須寫出來：**採用本自檢的文件，其 `python` 圍籬區塊必須是唯讀的，否則要掛 `probe-requires` 登記**。本檔四支與 #23 四支經逐支確認皆唯讀（`list_items`／`ls-tree`／argparse 內省／字串語料）。真正的處置是把執行放進沙箱子行程，與自陳（一）（三）同一個修法，歸 CI 落地那張卡。
- **R6 自陳，未修（五）：探針的工作目錄由呼叫者決定，自檢不設定也不檢查。** 本檔四支探針不讀相對路徑，所以「從哪裡跑都一樣」在本檔上成立——**這正是「只在自己文件上成立」的又一例，只是它今天還沒咬人**。#23 的 §4.4／§7.1 都以 `cli/src/...` 這類相對路徑讀檔，必須從 repo root 執行；§9.9.7 的實跑是從 repo root 跑的，換個目錄就會 FAIL。沒有立刻修，是因為正確的答案不明顯（釘死 repo root 會讓自檢無法用於別的 repo，釘死文件所在目錄對本 repo 又是錯的），**在 §9.6 第 57b 列的 CI 落地時應一併定案**；在那之前，執行位置是操作紀律而非機械保證。
- **R3 自陳，未修：§9.9 的自檢只涵蓋內嵌於本檔的四支探針，本檔仍有數字不在其射程內。** 具體是 §1.1 的「送入宣告全數被接受」對照表、§4.1 的 repo 分佈表（非終態 10／44、已指派 7／11）、§3.2 的 `*`／`?`／`[` 計數（0／0／41）、§3.3 的 25 個非 ASCII 路徑——這些來自一次性 session 腳本，**與 R2-001 是同一族的「不可重跑證據」，只是還沒有人踩到**。本輪不補的理由是它們支撐的都是**定性結論**（語彙檢查為零、Project 跨兩 repo、中括號不可誤拒、CJK 路徑真實存在），定性結論不因計數漂移而翻轉；而 §8.7.2／§8.8.1 靠的是**具體數值與具名清單**，那才是非可重跑不可的。**這個界線是我畫的，查核者可以不接受**——若判定要全數補成內嵌探針，工作量在本檔內、不逸出寫入集。
- **§8.2 的「258 組合」數字來自 R1 當時的一次性 session 腳本，不可重跑**；本輪以 §9.8 的內嵌程式取代其角色（23 條語料、276 組合、`b_misses_c = 0`），結論相同而證據升級為可稽核。兩者語料不同故組合數不同——**這是刻意的替換，不是數字對不上**。
- §5.2 的 git symlink 行為以一個臨時 scratch repo 實測，該 repo 未進入本 repo；重現步驟即 §9.4 第 29–33 列。
- 撰寫過程中一項自查修正值得記錄：初次以 `git ls-files | grep -P '[^\x00-\x7F]'` 探查非 ASCII 路徑，得到「兩 repo 皆無」的**錯誤**結論——`git ls-files` 預設對非 ASCII 路徑做 C-style 八進位引號。改用 `-c core.quotePath=false` 後查出 25 筆。§3.3 因此從「不需要」翻轉為「需要」。**探查工具的預設值本身就是一個可以說謊的來源。**
