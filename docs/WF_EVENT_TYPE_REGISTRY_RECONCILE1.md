# WF-EVENT-TYPE-REGISTRY-RECONCILE1 — 事件型別語彙的管轄裁定與對帳閘門設計

> 卡：[ai-workflow#58](https://github.com/ruan6047/ai-workflow/issues/58)　狀態：**純裁定卡**，不修改任一份語彙
> 基線：`e8a638c40f1028b6b85f6c59fd12ee9c1e85582d`（`git merge-base origin/main HEAD`，已驗為 HEAD 祖先）
> 寫入集：本檔單檔。實作與任何語彙修改由衍生卡依本裁定執行。
>
> ⚠️ **引用紀律**：本檔全程以「event marker 前綴」指稱該字面，**不逐字寫出**；在必須逐字引用
> 原始碼／登記檔的三處，該前綴以 `«前綴»` 代入（§6.1、§6.2），被代入的內容不影響該處要證明的事。
> 原因見 [`WF_EVENT_MARKER_V2.md`](WF_EVENT_MARKER_V2.md) 檔頭：任何**留言**只要含該前綴即被判為
> 受管轄，引用即停機。**本檔新增該前綴字面 0 處，故可安全整段引用進留言**（驗證見 §10）。

---

## 0. 這份文件是什麼

卡片問三個規格問題、要一個閘門設計、要一個「誰是執行者」的判斷。本檔逐一回答。

它**不是**什麼：不是實作，不是對任一份語彙的修改，不是查核裁決。§7 說明為什麼兩份都不必立即改，
§8 列出四張衍生卡承接實作。

**先讀 §1——卡面的兩個前提經重跑後不成立，而其中一個改變了差集本身。**

---

## 1. 事實基線更正：卡面的兩個前提不成立

卡片要求「PM 已實測，請自己重跑」。重跑後兩項前提與 `main` 的實況不符。兩項都不影響卡片要解的
問題成立與否，但都改變了問題的形狀，故先更正。

### 1.1 「`main` 上 18 項」描述的是一個**未合併分支**

卡面（與 #42 的交付摘要）稱 `templates/control-plane-contract.md` §2 的列舉為 18 項，
「#42 於 `b8a4a16` 補登後」。`b8a4a16` **不在 `main` 上**：

```console
$ git merge-base --is-ancestor b8a4a16 origin/main && echo YES || echo NO
NO

$ git branch -a --contains b8a4a16
+ claude/WF-CONTROL-PLANE-TYPE-REGISTRY1
  remotes/origin/claude/WF-CONTROL-PLANE-TYPE-REGISTRY1

$ git show origin/main:templates/control-plane-contract.md | grep -c '^type:'
1
$ git show origin/main:templates/control-plane-contract.md | wc -l
67
```

#42 目前是 🔍待查核，其分支上的 R1（`b1429220`，14→16）與 R2（`b8a4a16`，16→18）都尚未併入。
`main` 上的列舉是 **14 項**。

這不是 #42 的錯——它的交付對它自己的樹是正確的。錯的是把分支上的狀態當成 `main` 的狀態來描述，
而這正是本 repo 記錄過的同型教訓（規劃前先對齊 `origin/main`）。**本卡的裁定必須同時對 S1（今天的
`main`）與 S2（#42 併入後）成立**，否則 #42 一併入，裁定就過期。

### 1.2 「兩份封閉語彙，各自 fail-closed」——**只有一份是封閉的**

這是更重要的一項。`templates/control-plane-contract.md` 全檔出現「封閉」**零次**，且它明文宣告自己
可擴充：

```console
$ git show origin/main:templates/control-plane-contract.md | grep -c 封閉
0
$ git show origin/main:docs/WF_EVENT_MARKER_V2.md | grep -c 封閉
10

$ git show origin/main:templates/control-plane-contract.md | sed -n '32,33p'
`REJECT` event 直接視為一次升級計數。專案可擴充 event type，但必須文件化狀態轉移，
不得將未識別 type 默默當成 review attempt。
```

§2 的「不得將未識別 type 默默當成 review attempt」是**對未知型別的處置規則**，不是**封閉語彙**。
兩者是不同的東西：前者說「遇到不認得的就別亂猜」，後者說「不在表內就拒絕」。§2 選的是前者，並且
**明文允許擴充**。

`WF_EVENT_MARKER_V2.md` 選的是後者，逐字：

```console
$ git show origin/main:docs/WF_EVENT_MARKER_V2.md | sed -n '164p;422p'
`event` 值是**封閉語彙**，不在表內即 fail-closed。缺鍵、多出未定義鍵、順序不符、非單一空白，一律 fail-closed（§7 D 組窮舉證明）。
# event 值：封閉語彙。未列即 fail-closed。
```

**所以病灶不是「兩份封閉語彙互相衝突」，是「一份開放基準與一份封閉登記之間沒有包含關係檢查」。**
這個更正直接決定閘門的形狀：雙向差集**不應該**兩個方向都判 FAIL（§5.3）。

### 1.3 更正後的雙向差集（指令輸出）

抽取器（可重跑；`bash`，**不可用 `zsh`**，理由見 §5.4 註）：

```bash
extract_L1(){ git show "${1}:templates/control-plane-contract.md" \
  | awk '/^## 2\. /{f=1} f&&/^## 3\. /{f=0} f' \
  | sed -n 's/^type: //p' | tr '|' '\n' | tr -d ' ' | sed '/^$/d' | sort -u; }

extract_L2(){ git show "${1}:docs/WF_EVENT_MARKER_V2.md" \
  | sed -n '/^EVENTS: dict\[str, tuple\[str, \.\.\.\]\] = {$/,/^}$/p' \
  | sed -n 's/^ *"\([a-z][a-z-]*\)":.*/\1/p' | sort -u; }
```

**S1 — 今天的 `origin/main`（`e8a638c`）**

```console
$ extract_L1 origin/main > /tmp/A.txt; wc -l < /tmp/A.txt
14
$ extract_L2 origin/main > /tmp/B.txt; wc -l < /tmp/B.txt
7

$ comm -12 /tmp/A.txt /tmp/B.txt          # 交集
handoff
review

$ comm -13 /tmp/A.txt /tmp/B.txt          # 只在 L2（有 marker 無 type）
amend
assign
deployment-declaration
deployment-status-change
review-marker-clearance

$ comm -23 /tmp/A.txt /tmp/B.txt          # 只在 L1（有 type 無 marker）
claim
contract-baseline
correction
escalation-checkpoint
escalation-epoch-change
handoff-accepted
merge
preflight-failed
release
review-correction
review-invalid
status-change
```

**S2 — 假設 #42（`b8a4a16`）併入後**

```console
$ extract_L1 b8a4a16 > /tmp/A2.txt; wc -l < /tmp/A2.txt
18

$ comm -12 /tmp/A2.txt /tmp/B.txt         # 交集
handoff
review
review-marker-clearance

$ comm -13 /tmp/A2.txt /tmp/B.txt         # 只在 L2
amend
assign
deployment-declaration
deployment-status-change
```

**差異**：卡面寫「兩份皆有的只有 `review`／`handoff`／`review-marker-clearance`」——那是 **S2**。
今天的 `main`（S1）交集只有 **`review`／`handoff`** 兩項；`review-marker-clearance` 進入 L1 是 #42
分支上的未合併變更。`只在 L2` 的四項在 S2 成立、在 S1 是五項。

卡面陳述屬 S2、非 S1。**卡面更正屬 `amend`，逸出本卡寫入集，本檔僅記錄不代改。**

### 1.4 一個卡面與 #42 都沒提到的第三個宣告面

§2 內部除了 `type:` 那一行，還有**第二個**宣告 type 值的位置：

```console
$ git show origin/main:templates/control-plane-contract.md | grep -n 'resource-acquired'
35:local telemetry 另以同一 envelope 記錄 `resource-acquired | resource-released`，但必填 `lifecycle: false`、`claim_event_id`，且不得填 `state_version` 或改 card state。

$ for t in resource-acquired resource-released; do
    printf '%s 在 type: 行的出現次數 = ' "$t"
    git show origin/main:templates/control-plane-contract.md | grep -c "^type:.*$t"
  done
resource-acquired 在 type: 行的出現次數 = 0
resource-released 在 type: 行的出現次數 = 0
```

`resource-acquired`／`resource-released` 走**同一個 envelope**（故必然是 `type` 欄的合法值），
卻不在 `type:` 列舉內。任何把「§2 的列舉」等同於「`type:` 那一行」的抽取器——包含本檔 §1.3 的
`extract_L1`、包含 #42 兩輪用的——都**看不見這兩個**。

這不是本卡要解的分歧，但它是**同一個病的第三個實例**，而且它證明了 §5.2 要立的判準是必要的：
「哪些文字算型別宣告」如果靠讀者判斷，同一個檔案裡的第二個宣告面就會被漏掉，兩輪查核都沒抓到。

---

## 2. 裁定一：兩者管轄不同層，各自為權威

### 2.1 裁定

**不設單一權威。兩份分別是兩個層的權威：**

- **L1 邏輯層（事件模型）**——哪些 lifecycle 事實存在、其 envelope 欄位、狀態轉移、誰可寫。
  權威：`templates/control-plane-contract.md` §2，經 `ADOPTION.md` 實例化為各採用專案的
  `<專案>/docs/CONTROL_PLANE_CONTRACT.md`。**開放可擴充**（§1.2 已引其明文）。
- **L2 表示層（單一傳輸的線上格式）**——L1 事件中哪些以 Issue 留言 marker 承載，以及該 marker 的
  鍵集合與字母集。權威：機制歸 `templates/handoff-contract.md` §3.1.7，**成員名單**歸採用專案的
  設計文件（本 repo 為 `docs/WF_EVENT_MARKER_V2.md` §3.2）。**封閉**。

### 2.2 為什麼是分層，而不是我在兩個候選之間挑一個

三項可稽核依據，任一單獨成立即排除「單一權威」：

**（a）兩者的生命形態不同：一個是範本，一個是實例。**

```console
$ grep -n 'control-plane-contract' ADOPTION.md
23:從 [`templates/control-plane-contract.md`](templates/control-plane-contract.md) 建立 `<專案>/docs/CONTROL_PLANE_CONTRACT.md`，…

$ ls docs/
CONSUMER_CONFORMANCE.md
WF-25-REVIEW-WRITE-CHANNEL1.md
WF_CLEANUP_GUARD1.md
WF_EVENT_IDEMPOTENCY1.md
WF_EVENT_MARKER_V2.md
WF_RESOURCE_WRITESET1.md
```

`ai-workflow` 這個 repo **自己沒有** `docs/CONTROL_PLANE_CONTRACT.md`。`templates/` 下那份從來沒有
管轄過本 repo 的任何一個具體事件——它管轄的是**各採用專案的契約長什麼樣**。而
`docs/WF_EVENT_MARKER_V2.md` 管轄的是本 repo 的 `wfcli` 實際寫出的字元。

把 L1 設為 L2 的權威，等於要求每個採用專案的 control-plane 契約去列舉 marker 鍵——但 §1 的
Adapter 表明文允許 event store 是「外部 append-only store」，那樣的專案根本沒有 marker。

**（b）L2 依構造只涵蓋子集。** #42 的執行者已指名：「反向差集不必然是分歧，因該表只涵蓋具留言
marker 的子集」。把 L2 設為權威，等於讓一個傳輸的實作細節去定義邏輯事件模型；`merge`、`release`
今天沒有 marker，卻顯然是 lifecycle 事件。

**（c）兩者的開閉性不同，且各自的選擇對各自的層是正確的**（§1.2）。開放的基準與封閉的登記無法
合併成一份：合併後若封閉，採用專案就不能擴充；若開放，marker 解析就失去 fail-closed。

### 2.3 層界在哪：一條可判定的線

> **一個型別屬於 L2，當且僅當該事件以 Issue 留言 marker 承載其識別符。其餘 L1 型別只屬 L1。**

這條線是可判定的，因為「有沒有 marker」是 `WF_EVENT_MARKER_V2.md` §2.3 已逐動詞裁定過的事
（`open` 判否，其餘六個判是）。它不需要新的判斷，只需要把既有裁定讀出來。

### 2.4 跨層同名時誰說了算

同名不是衝突，是**同一個事件的兩個面**。分工：

- **L1 說了算的**：該型別的**語意**——它代表什麼事實、必填 envelope 欄位、狀態轉移、誰可寫。
- **L2 說了算的**：該型別的**表示**——有沒有 marker、marker 的鍵集合、順序、字母集。

**兩邊都不得越界**：L2 不得為一個型別定義狀態轉移，L1 不得規定 marker 的鍵。這與
`WF_EVENT_MARKER_V2.md` §1.3 已經立下的兩階段分工同構（階段一只看位置、階段二只看版本與鍵），
本裁定只是把同一種切法往上提一層。

### 2.5 由分層導出的唯一硬約束：包含關係 **L2 ⊆ L1**

**每一個 L2 型別必須是一個已登記的 L1 型別。反向不要求。**

論證：L2 事件依 `WF_EVENT_MARKER_V2.md` §2.5 裁定「lifecycle 事件的 canonical 載體一律是留言」，
即 L2 成員都是 lifecycle 事件，都會被寫進 event store。若一個 marker 型別不是 L1 型別，則 L1 的
消費者讀到它時會落進「未識別 type」分支——而 §2 對該分支只寫了一條禁令（不得默默當成 review
attempt），沒有寫可用的處置。**那正是 #42 指名的失效形狀**：未登記使 §2 自己那條規則無從遵守。

反向（L1 有而 L2 無）**不是分歧**，因為一個 L1 型別可以完全不需要留言 marker（`merge`、`release`
即是）。但它必須是**被宣告過的無**，而不是**沒人想過的無**——見 §5.3。

**⚠️ 本節的「必須」今天沒有機械執行者。** 見 §6 與 §9 第 1 條。

---

## 3. 裁定二：CLI 動詞不是事件型別

### 3.1 裁定

**動詞是寫入動作，型別是被寫下的事實；兩者同名是實作巧合，不是身分。**
因此「`assign`／`amend` 算不算事件型別」問錯了——正確的問題是：**它們寫下的事實，在 L1 是否已有型別。**

成文判準：

> 一個 CLI 動詞需不需要一個**新的** L1 型別，取決於它寫下的事實在 L1 是否已有型別，
> **不取決於動詞叫什麼**。動詞名不得直接充當型別名。

### 3.2 套用到這兩個動詞

`assign` 確實改 card state，故它寫下的事實**是** lifecycle 事件：

```console
$ sed -n '145p;147p' cli/src/wf_cli/commands/assign_cmd.py
    set_field_value(runner, project, item.item_id, fields["owner"], args.assignee)
    set_field_value(runner, project, item.item_id, fields["交付狀態"], args.status)
```

而 L1 已經有一個型別在描述「認領／指派」這件事，且本 repo **沒有**與之同名的子命令：

```console
$ grep -rn '"claim"\|add_parser(.claim' cli/src/wf_cli/ | wc -l
0
$ ls cli/src/wf_cli/commands/
__init__.py  amend_cmd.py  assign_cmd.py  deploy_declare_cmd.py  deploy_state_cmd.py
doctor_cmd.py  handoff_cmd.py  open_cmd.py  review_cmd.py  snapshot_cmd.py
```

`templates/control-plane-contract.md:44` 有一個待填槽「claim command／workflow：<命令或 URL>」。
本 repo 若要填它，唯一的候選是 `wfcli assign`。

同理 `amend`（開卡後修訂卡面欄位、原值留 Log）對應 L1 既有的 `correction`。

**提議映射（非既成事實）**：

| L2 動詞名 | 提議對應的 L1 型別 | 依據 |
|---|---|---|
| `assign` | `claim` | §3 的 claim 槽無其他候選；`assign` 是唯一寫 owner 且改交付狀態的認領動作 |
| `amend` | `correction` | `amend` 的語意即「開卡後更正卡面欄位並留原值」 |

### 3.3 這兩個映射是提議，不是我查到的事實

**沒有任何檔案宣告 `assign` 就是 `claim`；`wfcli` 也不寫 `type=` 欄位**，所以沒有任何執行期證據
可以印證或推翻它。上表是我依「claim 槽無其他候選」推出來的，強度是**推論**，不是**引用**。
批准權在 `templates/control-plane-contract.md` 的管轄者，不在本卡。

兩個分支都必須先想好，否則衍生卡會卡住：

- **映射被批准** → L2 的 `assign`／`amend` 是動詞名誤用為型別名，應在 v2 寫入端落地**之前**
  改名為 `claim`／`correction`。否則 L2 ⊆ L1 會靠「往 L1 補登兩個同義型別」來滿足，L1 從此帶兩組
  同義字，而那是比今天更難修的狀態。
- **映射被否決** → L1 必須補登 `assign`／`amend`，並依 §2 自己的要求「文件化狀態轉移」。

**改名的時間窗現在還開著**，因為 v2 尚未實作（§7）。v2 寫入端一落地，改名就變成遷移。

### 3.4 順帶指名一個範圍外的缺口

`open` 建立卡片，`WF_EVENT_MARKER_V2.md` §2.3 裁定它不需要 marker（Issue number 已足）——**但
L1 也沒有任何型別描述「卡片被建立」**（`migration-baseline` 只涵蓋遷移進來的卡）。這是 L1 的缺口，
不是 L1／L2 分歧，逸出本卡。記錄於此，併入衍生卡 3 的範圍評估。

---

## 4. 裁定三：部署事件**受** §2 envelope 管轄，但屬 §2 今天沒有的第三類

### 4.1 先回答「§2 的管轄邊界為什麼沒寫在任何地方」

#42 指出讀者今天靠比對欄位集自行推斷（`deployment-status-change` 無 `event_id`、無 `state_version`、
無 `type`）。**成因是：那條線從來沒有被決定過。** §2 今天恰好只有兩類事件——

1. **lifecycle 類**：有 `state_version`（嚴格遞增），改 card state。
2. **local telemetry 類**：`lifecycle: false`、`claim_event_id`、**不得**填 `state_version`、不改 card state。

——而「有沒有 `state_version`」是這兩類的**區別特徵**，不是**管轄判準**。讀者把區別特徵當成管轄
判準來用，於是任何沒有 `state_version` 的東西看起來都在管轄外。那是一個副作用，不是一個裁定。

### 4.2 裁定：受管轄

論證有二，第二個是決定性的。

**（a）它是跨人協作事件，寫進 event store。** §1 Adapter 表把 remote coordination 定義為
「唯一 lifecycle writer：跨人 task、review、lease、CI 與**協作事件**」。部署宣告與部署轉換是跨人
協作事件，且 `deploy-state` 明確**先寫 timeline event 再寫 Project 欄位**：

```console
$ sed -n '1,5p' cli/src/wf_cli/commands/deploy_state_cmd.py
"""``wfcli deploy-state``：受控部署轉換與 Projects Status 視覺同步。

部署狀態是 canonical AI_WORKFLOW.md §0 的獨立線性狀態機。這個命令只接受相鄰
前進轉換，先追加 Issue timeline event，再用 GraphQL
``updateProjectV2ItemFieldValue`` 寫入 item 值；不建立、不修改任何 Project 欄位定義。
```

**（b）決定性：`release` 的前置條件若無部署事件即不可驗證。** canonical `AI_WORKFLOW.md` §0：

> 部署狀態獨立：`—不適用`，或 `⏸未部署 → 🚀待部署 → ⏳部署中 → ✅已部署 → 🧪驗證中 → ✅已驗證`；
> 失敗／回滾不得結案。release 事件必以**終態**交付狀態落地：免部署卡 release 即 `🏁完成`，
> **需部署卡在部署 `✅已驗證` 前不得 release**。

`release` 是 L1 型別。它的前置條件是一個部署狀態。**若部署事件在 §2 管轄之外，L1 的消費者就無法
從 event store 判斷一次 `release` 是否合法**——一個 L1 型別的合法性會依賴 L1 看不見的東西。
這不是風格問題，是可驗證性的斷裂。

### 4.3 但它兩類都不屬：§2 需要第三類

部署事件**不是** local telemetry（它是遠端的、跨人的，且它確實改變一個持久化狀態），**也不是**
今天定義的 lifecycle 類（它不推進 card 的 `state_version`，它推進**另一個**狀態機）。

裁定：§2 應立第三類——**獨立狀態機事件**：同一 envelope、`type` 必填、`event_id` 必填、
`state_version` 改為**該狀態機自己的序**或明示不適用、並**明文標示它推進的是哪一個狀態變數**。

**定義出處已經存在，不必發明**：canonical `AI_WORKFLOW.md` §0 已寫死部署狀態機的完整轉移
（六態線性 ＋ `—不適用`）。依 §2 自己的要求「專案可擴充 event type，但必須文件化狀態轉移」，
這兩個型別的登記條件**今天就已滿足**——缺的只是有人去登記。這使衍生卡 3 是低風險的。

### 4.4 附帶結論

一旦第三類成文，§1.4 那兩個 telemetry 型別的地位也連帶清楚：它們是第二類，且它們**應該**出現在
某個被抽取器讀得到的登記面上，而不是只出現在一行散文裡。

---

## 5. 雙向差集閘門的設計

**本節是設計，不是實作。** 實作寫入集含 `cli/`，逸出本卡，見衍生卡 1。

### 5.1 閘門讀哪些來源——是「宣告面」，不是「檔案」

閘門的輸入不是兩個檔案，而是一份**宣告面登記表 [declaration-surface registry]**。每一列是一個三元組：

    (檔案路徑, 錨點, 抽取式) → 該面所屬的層與類

初始登記表（依 §1.3、§1.4、§2 的實測；`†` 表示尚在 #42 分支、併入後生效）：

| # | 檔案 | 錨點 | 層／類 |
|---|---|---|---|
| 1 | `templates/control-plane-contract.md` | §2 `type:` 行 | L1 / lifecycle |
| 2 | `templates/control-plane-contract.md` | §2 telemetry 行的反引號列舉 | L1 / telemetry |
| 3 | `docs/WF_EVENT_MARKER_V2.md` | §3.2 表首欄 | L2 |
| 4 | `docs/WF_EVENT_MARKER_V2.md` | §7 探針的 `EVENTS` dict 鍵 | L2 |
| 5† | `templates/control-plane-contract.md` | §2.1 定義出處登記表首欄 | L1 / 定義出處交叉核對 |
| 6† | `templates/control-plane-contract.md` | §2.2 provisional 表首欄 | L1 / provisional |

第 3 與第 4 是**同一份語彙的兩個面**，今天實測一致：

```console
$ diff <(awk '/^### 3\.2 /{f=1} f&&/^### 3\.3 /{f=0} f' docs/WF_EVENT_MARKER_V2.md \
         | sed -n 's/^| `\([a-z][a-z-]*\)` |.*/\1/p' | sort -u) \
       <(sed -n '/^EVENTS: dict\[str, tuple\[str, \.\.\.\]\] = {$/,/^}$/p' docs/WF_EVENT_MARKER_V2.md \
         | sed -n 's/^ *"\([a-z][a-z-]*\)":.*/\1/p' | sort -u) && echo IDENTICAL
IDENTICAL
```

### 5.2 「什麼算型別宣告」的成文判準

這是卡片指名的最弱一環，也是 #42 自陳「沒有證明覆蓋完整」的那一項。#42 兩輪用的規則是
**反引號 kebab token ＋ 該行含 事件／event／type**——那是一個**搜尋啟發式**，它試圖對自由文字
證明一個否定命題（「沒有別的型別了」），而那是不可證明的。本輪那個新檔恰好證明該風險是真的。

**判準（成文）：**

> 一個 token 是型別宣告，**當且僅當**它出現在宣告面登記表某一列所指定的（檔案，錨點，抽取式）
> 所抽出的集合中。登記表以外的任何文字——包含散文、註解、範例、卡片、Issue 正文——**一律不是**
> 型別宣告，不論它長得多像。

三個直接後果：

1. **新增型別**必須把它加進某個已登記的面，否則它在定義上不是型別宣告。抽取器因此**必然**看得見
   每一個型別——這一半是構造保證，不是抽樣。
2. **新增一個宣告面**必須先登記該面。這是判準唯一的漏洞，而它是**可見且可審的**：面的清單短、
   粗、人讀得完（今天 6 列），而型別的清單是開放的、散在自由文字裡的。
3. 因此判準把「**窮舉型別**」這個不可證明的問題，換成「**窮舉宣告面**」這個可審的問題。

**這是遷移，不是消除。** 我沒有解決 #42 那個問題，我把它搬到一個更小、更粗、有限且人可窮盡
檢視的物件上。承認這一點很重要，理由見 §9 第 6 條。

**啟發式仍然有用，但降級為偵測器而非判準**：#42 那條規則（或任何類似的掃描）應作為
**候選提名器**跑——它掃出登記面之外的可疑 token，交人裁定「這是不是一個未登記的宣告面」。
提名器漏掉不影響判準的正確性，只影響發現速度。**啟發式負責發現，登記表負責判斷**——今天這兩件事
混在一起，於是一個不完整的掃描規則被當成了完整性論證。

### 5.3 差集非空時的行為——**兩個方向不對稱**

這是 §1.2 那個更正的直接後果。若閘門對兩個方向都判 FAIL，它就把 L1 的開放性當成缺陷來報，
每一個沒有 marker 的 L1 型別（今天 12 個）都會是一筆假警報，而一個天天噴 12 筆假警報的閘門
會在第三天被關掉。

- **`L2 \ L1` 非空 → FAIL（阻擋）。** 這違反 §2.5 的包含關係硬約束。今天此集合非空
  （S1 五項、S2 四項），故**閘門一落地即為紅**——這是正確的，它就該是紅的，直到衍生卡 2、3 處理完。
- **`L1 \ L2` 非空 → 不 FAIL，但每一項必須在 L1 側帶一個明示的「無 marker」宣告。**
  缺該宣告的項目 → FAIL，訊息須與上一條**分離**，指名成因為「該 L1 型別未宣告其表示層地位」。
  這條把「被宣告過的無」與「沒人想過的無」分開——這正是 §2.5 要求的區別，也是唯一能讓
  `L1 \ L2` 這個方向產生訊號而不是噪音的作法。
- **兩個訊息不得共用同一句話。** 同型的理由 `handoff-contract.md` §3.1.7 已經立過
  （未知版本的停機訊息必須與「marker 寫壞了」分離）：共用一句話會讓一次可行動的阻擋看起來像雜訊。

### 5.4 抽取器必須對**零產出** fail-closed

**這是本設計中最容易被漏掉、且我在本輪親身踩到的一項。**

若某個抽取器因錨點漂移而抽到 0 筆，差集會**假性為空**，閘門判 PASS。失效方向是 **fail-open**：
語彙壞了，閘門說沒事。

實證一（本輪真實發生）：本檔 §1.3 的抽取式第一次是在 `zsh` 下跑的，`"$1:templates/…"` 被 `zsh`
的 `:t` 修飾符吃掉，`extract_L1` 抽到 **0 筆**，而 `comm` 照樣印出一份看起來乾淨的結果。
**若當時沒有印出筆數，這份文件會建立在一個空集合上。**（此即抽取式必須以 `bash` 跑、
且參數必須加大括號的原因。）

實證二（可重跑）：

```console
$ printf 'EVENTS = {\n    "review": ("card_id",),\n}\n' > /tmp/fake.py
$ sed -n '/^EVENTS: dict\[str, tuple\[str, \.\.\.\]\] = {$/,/^}$/p' /tmp/fake.py \
    | sed -n 's/^ *"\([a-z][a-z-]*\)":.*/\1/p' | sort -u | wc -l
0
```

錨點只要從 `EVENTS: dict[...] = {` 變成 `EVENTS = {`，抽取結果就從 7 筆變 0 筆，而差集會變空。

**規則：每個宣告面必須宣告其最小期望筆數（≥1），抽取結果低於該數即 FAIL，訊息指名
「來源未被讀到」而非「差集為空」。** 驗值不等於驗來源；一個讀不到來源的比對器，其輸出與
「兩邊一致」逐字相同。

### 5.5 閘門的執行者，以及它今天不存在

閘門是一支腳本 ＋ 一個呼叫它的地方。**呼叫它的地方今天不存在**：

```console
$ ls -d .github 2>/dev/null || echo "no .github"
no .github
```

無 CI。因此衍生卡 1 若只交付腳本，它的宣稱強度就是「可以跑」，不是「會擋」——這正是本 repo
被 `claim-exceeds-evidence` 打過的形狀之一。**衍生卡 1 必須同時交付腳本與呼叫點**，否則它應
在自己的交付物裡把「會擋下」逐字寫成「約定」。

---

## 6. 「今天沒有任何機制在協調兩份語彙」——執行者是誰

### 6.1 答案：**沒有。是空集合，不是弱執行者。**

```console
$ grep -rn 'control-plane-contract' cli/ scripts/ | wc -l
0
$ grep -rn 'WF_EVENT_MARKER_V2' cli/ scripts/ | wc -l
0
$ ls -d .github 2>/dev/null || echo "no .github"
no .github
$ grep -rn 'control-plane-contract' . --exclude-dir=.git -l
./ADOPTION.md
./MIGRATION.md
./docs/WF_RESOURCE_WRITESET1.md
./README.md
```

四處命中全是散文引註，沒有一處是程式。**兩份語彙都沒有任何程式讀者。**

更進一步：唯一與 marker 有關的機械消費者 `doctor.py` **完全沒有事件型別列舉**。它把 v1 的三鍵
寫死在一條 regex 裡，隱含地只認識一個事件：

```console
$ sed -n '211,212p;249,251p' cli/src/wf_cli/doctor.py
_CONFORMANT_MARKER_RE = re.compile(
    r"^<!-- «前綴»v1 "
    if not line.startswith("<!-- «前綴»v1 "):
        version = line.split()[1] if len(line.split()) > 1 else line
        return None, f"未知或不支援的 marker 版本：{version}（只認 v1；不得回退 legacy）"
```

**所以實況比卡面描述的更歪：不是兩份語彙，是三份。** 第三份是 `doctor.py` 隱含的、基數為 1 的
語彙 `{review}`，而它是**唯一今天真的在跑的那一份**。前兩份都沒有執行者，第三份沒有文件。

### 6.2 該不該有？該有——但**現在還不該建，而觸發條件是可檢查的**

反直覺，所以講清楚。今天的分歧**不可能造成任何錯誤裁決**，因為 L2 語彙**尚未生效**。三項獨立證據：

```console
$ sed -n '160p' templates/handoff-contract.md
> **生效狀態（必讀）**：`v2` **尚未實作**。本節規範應然；依 §6 的「未登記等同未生效」，在有消費者於 §6 登記實作 `v2` 之前，任何流程都不得假定 `v2` 已可用，寫入端也不得產出 `v2` 事件…

$ sed -n '12p' docs/CONSUMER_CONFORMANCE.md
- 讀取的 marker：`«前綴»v1`、`wf-review-receipt:v1`
```

——契約明文 v2 未實作且寫入端不得產出；唯一登記的消費者只讀 v1；`doctor` 對 v2 一律停機（上方
`:249`）。**L2 今天有 0 個寫入端、0 個讀取端。**

所以現在建閘門，是去守一個沒有人寫也沒有人讀的語彙。真正的風險點在別處：

> **`WF_EVENT_MARKER_V2.md` §9 第 1 條要求 v2 讀取器先落地。那張實作卡會在 `doctor` 裡新增一份
> `EVENTS` 等價物。若對帳未先成文，那一刻語彙就從三份變四份——而新的那一份是有執行者的。**

**觸發條件（可機械檢查）**：任何在 `cli/` 內新增事件型別列舉的變更。今天該條件的可觀測訊號是：

```console
$ # 回 0 = 尚未發生；非 0 = 閘門必須已經在位
$ grep -rn 'EVENTS\|event_type\|事件型別' cli/src/wf_cli/ | wc -l
0
```

（此命令是**可觀測訊號**，不是閘門：它是一個啟發式掃描，會漏掉用其他措辭寫的列舉。
依 §5.2 的分工，它的角色是提名，不是判斷。）

**裁定：閘門與 v2 讀取器必須同批落地，不得在其後。** 這是一個排程宣稱，執行者是排期者（PM），
**沒有機械執行者**——見 §9 第 5 條。

### 6.3 寫成約定

> **約定（無機械執行者）**：任何變更若新增、移除或改名一個事件型別，須同時更新宣告面登記表所列
> 的每一個受影響的面，並使 `L2 \ L1` 維持為空。今天此約定的執行者是該次變更的**查核者**與兩檔的
> **管轄者**；不存在任何程式會發現違反。此約定在衍生卡 1 落地前一直是約定。

---

## 7. 有沒有哪一份必須立即改？——**沒有**，且我說明為什麼等得起

卡片要求：若認為某一份必須立即改，須指名並說明為什麼不能等。**我的結論是兩份都不必立即改。**

安全性論證，依據 §6.2 的三項證據：L2 有 0 個寫入端、0 個讀取端，故今天的分歧**不可能**產生一次
錯誤的裁決。它能產生的傷害只有一種——**有人照現行文字去實作 v2**——而那條路徑的入口是
一張尚未派工的實作卡，不是一個隨時可能發生的執行期事件。

必須立刻做的**不是編輯，是排程**：把閘門綁到 v2 讀取器那張卡上（§6.2）。那是排期動作，
不需要改任何一份語彙。

三項附帶結論，都不構成「立即改」：

- **#42（`b8a4a16`）不需要因本卡而改。** 它的「已知分歧」段落對它自己的樹是準確的——我以 S2
  複驗，`只在 L2` 恰為它列的那四項（§1.3）。它明確不裁定，而本卡就是承接那個不裁定的卡。
- **卡 #58 的卡面陳述屬 S2 而非 S1**（§1.1、§1.3）。更正屬 `amend`，逸出本卡寫入集，我不代改。
- **§3.3 的改名時間窗現在開著**，v2 寫入端一落地就關。這是「愈早愈省」，不是「不能等」——
  區別在於前者的代價隨時間線性增加，後者現在就在流血。**本卡的其餘結論不依賴它。**

---

## 8. 衍生卡

四張，依相依排序。前兩張的寫入集互不相交，可並行；卡 2 必須在卡 3 之前定案。

1. **`WF-EVENT-TYPE-SURFACE-REGISTRY1`** — 把 §5.1 的宣告面登記表寫進
   `templates/control-plane-contract.md`，並實作 §5.2–§5.4 的雙向差集閘門（含零產出 fail-closed 與
   雙向不對稱處置）。寫入集：`templates/control-plane-contract.md` ＋ `cli/`（＋呼叫點）。
   **⚠️ 排程紅線：必須與 `WF_EVENT_MARKER_V2.md` §9 第 1 條的 v2 讀取器實作卡同批**（§6.2）。
   **⚠️ 依 §5.5，若只交付腳本而無呼叫點，交付物須把「會擋下」寫成「約定」。**
   落地當下閘門即為紅（§5.3），這是預期行為，不是缺陷。

2. **`WF-VERB-TYPE-MAPPING1`** — 批准或否決 §3.2 的兩個映射（`assign`→`claim`、
   `amend`→`correction`）。批准則 L2 改名，否決則 L1 補登並文件化狀態轉移。
   寫入集：兩檔。**須跨家族**——錯了會讓 L1 永久帶兩組同義字，且 v2 落地後修復成本從改名升為遷移。

3. **`WF-DEPLOY-EVENT-ENVELOPE1`** — 依 §4.3 在 §2 立第三類「獨立狀態機事件」，登記
   `deployment-declaration`／`deployment-status-change`（定義出處指向 canonical `AI_WORKFLOW.md` §0，
   已存在），並把 §2 的**管轄邊界寫成明文**（§4.1 指出它從未被決定過）。
   範圍評估時一併處理 §3.4 的卡片建立事件缺口。

4. **`WF-CONTROL-PLANE-TELEMETRY-SURFACE1`**（小，可併入卡 1）— §1.4 的 telemetry 行是一個未登記的
   宣告面，`resource-acquired`／`resource-released` 不在 `type:` 列舉內。裁定它們是否為 `type` 值，
   並使其落在一個抽取器讀得到的面上。

---

## 9. 自我適用：本輪立下而**沒有機械執行者**的宣稱

| # | 宣稱 | 執行者 | 邊界外會怎樣 | 強制／約定 |
|---|---|---|---|---|
| 1 | 「L2 ⊆ L1 是硬約束」（§2.5） | **無** | 任何人可在任一份加型別，無程式會發現 | **約定**；衍生卡 1 落地後才可能成為強制 |
| 2 | 「`assign`→`claim`、`amend`→`correction`」（§3.2） | **無** | 這是**我的推論**，非引用；`wfcli` 不寫 `type=`，無執行期證據可證偽 | **提議**，待衍生卡 2 批准 |
| 3 | 「部署事件受 §2 管轄」（§4.2） | **無** | §2 今天沒有可容納它的類；在衍生卡 3 之前，本裁定不改變任何檔案 | **約定** |
| 4 | 「宣告面登記表使窮舉可審」（§5.2） | **無**（表今天不存在） | 未登記新面仍可能發生；判準只把問題從不可審換成可審 | **約定** |
| 5 | 「閘門必須與 v2 讀取器同批落地」（§6.2） | **無**（排期者） | 排在其後 → 語彙變四份且新的那份有執行者 | **約定**；§6.2 的 `grep` 是可觀測訊號，不是閘門 |
| 6 | 「本輪差集已窮舉」 | 部分 | 見下 | **僅對兩個具名來源強制，整體為約定** |

**第 6 條要講清楚，因為它是本輪最容易被高估的一項。**

**是機械的**：§1.3 的差集、§5.1 的兩面一致、§1.4 的 telemetry 缺席、§6.1 的四個零命中、
§6.2 的三項未生效證據、§5.4 的零產出實證——全部是指令輸出，任何人可重跑，我沒有人工清點任何一筆。

**不是機械的**：「除了這些之外沒有別的宣告面」。我確實去找過第三、第四個面，並且找到了一個
（§1.4 的 telemetry 行，卡面與 #42 兩輪都沒提），也排除了一個候選
（`handoff-contract.md` §3.1.7 規範 v2 機制但**委派**成員名單、不自列，故不是登記面）。
但**我不能證明我找完了**——而這正是 §5.2 的判準要處理的東西。

**因此：我沒有解決 #42 那個「沒有證明覆蓋完整」的問題，我把它搬到一個更小的物件上。**
#42 要窮舉的是散在自由文字裡的型別；本檔要窮舉的是 6 列的宣告面清單。後者可審，前者不可審。
**但「可審」不是「已證明」**——把本檔的判準當成完整性證明，就是本 repo 反覆被打的那個形狀。

最後，一項**不是**我的宣稱、但值得指名的機械事實：§6.1 顯示今天真正在跑的語彙是
`doctor.py` 隱含的 `{review}`，基數 1，且它沒有出現在任何一份登記裡。**本卡裁定的兩份語彙，
今天都不是本 repo 執行期的事實來源。**

---

## 10. 驗證摘要

本檔所有數字與集合皆由指令輸出產生，無人工清點。可重跑清單：

- §1.1 `b8a4a16` 非 `origin/main` 祖先 → `git merge-base --is-ancestor`
- §1.3 雙向差集，S1 與 S2 兩態 → `extract_L1` / `extract_L2` ＋ `comm`
- §1.4 telemetry 型別不在 `type:` 行 → `grep -c "^type:.*$t"`
- §2.2(a) 本 repo 無 `docs/CONTROL_PLANE_CONTRACT.md` → `ls docs/`
- §1.2 開／閉自宣告 → `grep -c 封閉`（14 項那份為 0，7 項那份為 10）
- §3.2 無 `claim` 子命令 → `grep -rn '"claim"' cli/src/wf_cli/ | wc -l` → 0
- §5.1 §3.2 表與 `EVENTS` dict 一致 → `diff <(…) <(…)` → IDENTICAL
- §5.4 零產出陷阱 → `/tmp/fake.py` 重放
- §6.1 兩份語彙皆無程式讀者、無 CI → 三道 `grep`／`ls`
- §6.2 v2 未生效 → `handoff-contract.md:160`、`CONSUMER_CONFORMANCE.md:12`、`doctor.py:249`

環境註記：抽取式須以 `bash` 執行。`zsh` 會把 `"$1:t…"` 當成 `:t` 修飾符，導致抽取結果為 0 而
差集假性為空（§5.4 實證一）。

引用紀律驗證（本檔新增 event marker 前綴字面 0 處）：

```bash
grep -c 'wf-review''-event' docs/WF_EVENT_TYPE_REGISTRY_RECONCILE1.md   # 預期 0
```
