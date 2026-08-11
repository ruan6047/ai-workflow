# WF-EVENT-IDEMPOTENCY1：lifecycle 事件的排序與冪等

> 卡：[ai-workflow#23](https://github.com/ruan6047/ai-workflow/issues/23)　基線：`origin/main` `7451b72ba7679893043950d71bad9642665e25da`
>
> spec 基線內容＝[#16](https://github.com/ruan6047/ai-workflow/issues/16) 設計文件 §3.1 於 SHA `2d361303ce438c6fecf475b2aaa1fcbc06518dc9` 的狀態（已歷 R5／R6／R7 三輪跨家族查核）。需求方 2026-08-11 裁定縮小 #16 射程後，機制本體歸本卡。
>
> 本檔是**設計與契約**，不含實作。所有可執行變更由衍生實作卡承接（§12）；本卡資源宣告僅含本檔，`cli/` 由 [#21](https://github.com/ruan6047/ai-workflow/issues/21) 佔用中。
>
> **四支內嵌探針**（§4.4、§4.5、§7.1、§7.1.2）皆為唯讀靜態分析，不連 GitHub、不寫任何狀態，可自 repo root 原樣重跑。**執行指令一律釘為 `uv run python`**（專案 venv，實測 3.12.13）。理由是 `python3` 這個名字在本機解析到三個不同的直譯器（`/usr/bin/python3` 3.9.6、`mise` 3.14.3、venv 3.12.13），前一版 §4.4 寫 `python3` 而其中一個會直接 `TypeError`——探針的重跑性不能依賴讀者的 `PATH`。四支探針已另行實測可在 3.9.6／3.12.13／3.14.3 三者下產生一致結果（§4.4 末表），但**釘選的仍是 `uv run python`**：實測範圍不等於一般性可攜宣稱。

## 0. 這份設計要解什麼

canonical `AI_WORKFLOW.md:141` 的 lifecycle event 最小 schema **已經**含 `event_id` 與 `state_version`，並已明定「同一卡的 `state_version` 必須單調遞增」。

**本檔不另立一套 schema，只把取號程序、異常處置與重試辨識補完。** 這三件事在 canonical 未定義，導致該行的兩個欄位在實務上都不成立：`event_id` 目前是隨機 UUID（`handoff-contract.md:16` 寫為 `<UUID>`），重試時認不出自己；`state_version` 沒有取號程序，而 GitHub 既無原子遞增也無 CAS。

射程邊界，先講清楚：

- **承接**：`review`／`amend`／`handoff`／`assign`／`deploy-declare`／`deploy-state` 六個動詞的排序與冪等。
- **不承接 `open`**（§8）。這不是遺漏，是 #16 R12-004 已裁定 `event_id` 在結構上解不了的一類問題。
- **與時間語意正交**：`state_version` 是計數不是時刻。canonical 同行另要求 `occurred_at` 取自寫入當下系統時鐘、不得估算——時戳與排序是兩件事，本設計只用後者，且冪等鍵**不取環境時鐘**（cpbl#123）。

---

## 1. `state_version`：取號程序與異常處置

### 1.1 取號程序

**讀該卡現有最大序號 +1。** GitHub 無原子遞增，故取號必然是 read-modify-write，這個事實無法用更聰明的寫法繞過，只能用鎖縮窗（§2）並對殘餘情形 fail-closed。

完整程序見 §5 的 resume 演算法——取號是該演算法的步驟 4，**不是獨立程序**。把取號寫成獨立步驟正是撞號的來源：讀與寫之間若不在同一個鎖裡，中間的空窗就是競態窗口。

### 1.2 五種情形，逐一處置（全函數，無「其餘」）

卡面要求處置**三種異常**（撞號、缺號、無序號）。要讓判準成為全函數，必須把正常情形與「同號同 `event_id`」一併列入——後者正是最容易被誤判成撞號的那一格。

判準的輸入是「該卡事件流中，序號 N 的事件集合」。閉包由該集合的大小窮舉而來：大小只有 0、1、>1 三種可能，其中 >1 依 `event_id` 是否全等再分二，另加序號欄位缺席的情形，共五格：

| 情形 | 機械判準 | 處置 |
|---|---|---|
| **正常** | 序號 N 恰有一筆事件 | 接受，繼續 |
| **同號同 `event_id`** | 序號 N 有多筆，但 `event_id` 全部相同 | **不是撞號**。這是同一次寫入的重試或重複觀測，交 §5 冪等路徑處理 |
| **撞號** | 序號 N 有多筆，且存在兩筆 `event_id` 不同 | **並行寫入的證據** → fail-closed：該卡降純偵測，人工裁定 |
| **缺號** | 序列 `[min..max]` 有洞 | 有事件遺失或未落地 → fail-closed：該卡降純偵測 |
| **無序號** | 事件不帶 `state_version` 欄位 | legacy 前綴，以 `epoch-anchor` 劃界（#16 §10.2），**不追溯**、不視為缺號；該卡若尚未錨定則**整條序列都無序號** → 自動修復降純偵測 |

**「同號同 `event_id` 不是撞號」是本卡最重要的一條，也是最容易實作錯的一條。** 天真的實作會把「序號 N 已被佔用」直接當成撞號，於是每一次「寫入成功但回應遺失」後的重試都會把該卡永久降級——防護機制反而成為最主要的故障來源。降級是不可逆的懲罰，代價與防護必須對稱。

> **為什麼 legacy 無序號不算缺號**：缺號的語意是「這條序列本來該有這一號」。錨點之前的事件從來不在同一條序列上（#16 §10.2 明定錨點前為**不透明前綴**，reducer 不解析），把它們算進去會讓每一張跨 cutover 的卡在第一次檢查時就全部降級。劃界的機制不是本卡新增的。
>
> **這裡要引對機制**（前一版引錯，本輪更正）：#16 §10.1 明文要求**寫入守衛**與 **reconcile 自動修復**兩種保護分開講，並警告「兩者混講就會同時宣稱互相衝突的事」。序號屬**後者**，其劃界物是 §10.2 的 **`epoch-anchor`**（逐卡 one-shot，指派 `state_version = 1`，錨點前視為不透明前綴）；`contract-baseline`（§10.3 步驟 3）是**前者**的劃線物，管的是「線後所有寫入適用新制寫入守衛」，與序號無關。前一版把 `state_version` 的劃界寫成 `contract-baseline`，正是 §10.1 警告的那種混講。
>
> **連帶後果，明說**：`epoch-anchor` 依 #16 §10.2 **僅適用 quiescent 卡**，且「已錨定張數不保證收斂」。因此**未錨定的卡整條序列都無序號**——本卡的 §1.2 對它不報缺號（正確），但它也拿不到自動修復，只能純偵測。本卡不改變這個結論，也不宣稱能替未錨定的卡提供冪等保護。

---

## 2. 撞號的並行防護：兩層，且不宣稱超出各層能力

**紀律不是機制。** 任兩個 resume 或人工作業即可撞號，而撞號的後果是該卡永久降級。靠「請勿同時操作」防護等於沒有防護——canonical `AI_WORKFLOW.md:148` 已明文把這句話排除在鎖的定義之外。

canonical 同行給出可用的一層：「本機可採**原子目錄鎖**；跨主機必須使用具併發控制的服務或 workflow。」照這條界線分兩層：

| 併發來源 | 機制 | 保證強度 |
|---|---|---|
| 同機多個 `wfcli` 程序（含 resume 與人工並行） | 以 `(owner, project, card_id)` 為鍵的**本機原子目錄鎖**，包住 §2.1 的**固定臨界區** | **可預防**。canonical 明文允許，且它是鎖不是狀態面 |
| 跨主機 | 無可用的併發控制服務 | **不可預防**。臨界區內的完整重讀縮窗，撞號 fail-closed |

**鎖的鍵必須是 `(owner, project, card_id)` 三元組**，不是 `card_id` 單獨。卡 ID 在跨 repo 的 user-level Project 聚合下不保證唯一（canonical `:162` 明示 user-level Project 跨 repo 聚合即多專案面板），單以 `card_id` 為鍵會讓兩張不同專案的同名卡互相阻塞。

**鎖不持有任何 lifecycle 狀態。** 它只保護臨界區，不儲存意圖、不記錄進度。這一點必須明確，否則本機鎖會偷偷變成 §5 明文拒絕的本機狀態，違反 canonical `:143`／`:165`（#16 §4.1 已詳述該推理，本檔不重述）。鎖目錄 runtime 必須 `.gitignore`。§2.3 允許鎖目錄攜帶**存活性 metadata**，該處另立劃界規則說明它為何不是本機狀態。

> **誠實界線**：跨主機撞號仍只能偵測，不能預防。這與 `wfcli amend` 現行的「重讀比對縮窗、不宣稱 CAS」（`amend_cmd.py:411` 的註解已自承殘餘競態視窗）是同一誠實等級。**但同機這一層已從紀律升格為機制**，而實測中 resume 與人工並行都落在這一層。

### 2.1 臨界區的內容是**固定**的，不是「至少包含」

前一版只寫「包住讀→寫整段」，那不夠：它容許實作在鎖外先讀事件流、判定「`event_id` 不存在、可以寫」，再進鎖只做「重讀最大序號 → 取號 → 寫」。這條路徑會被兩個同意圖的同機程序同時走通——A 先寫入，B 進鎖後**只重讀序號**、取到 `max+1`（一個沒被佔用的新號），於是寫出第二筆語意重複的事件，而且**不會被 §1.2 判為撞號**（兩筆序號不同）。防護在最該生效的情形下失效，成因是臨界區的邊界沒有被釘死。

> **裁定：原子臨界區的內容固定為下列五步，順序不可調換、步驟不可移出鎖外。**
>
> 1. **完整重讀該卡事件流**（不得沿用進鎖前的任何讀取結果）
> 2. 重新執行 §1.2 五情形判準
> 3. 重新依 §3.3 計算本次 `event_id`，並在**剛重讀的事件流**中查找
> 4. 命中 → `already_exists`（§5.2）；未命中 → 取 `max + 1` 為 `state_version`
> 5. 執行**首次寫入**（該動詞事件的第一個遠端寫入，見 §7.1）

三條隨附規則，缺一則臨界區不閉合：

- **禁止跨鎖攜帶讀取結果**。進鎖前的讀只能用於 `--dry-run` 與錯誤預檢，**不得**作為步驟 1–4 的輸入。實作若為省一次 API 呼叫而重用鎖外的事件流快照，即回到上述失效路徑。
- **首次寫入失敗或逾時，須在同一鎖內回到步驟 1 重跑**（有界重試）。理由是失敗與「寫入成功但回應遺失」在呼叫端不可區分；不重讀就重送，等於在自己剛可能寫成功的鏈上盲寫。仍持有鎖時重讀是安全的，因為同機互斥仍成立。
- **鎖取得失敗即 fail-closed**。逾時仍取不到鎖 → **不得改以無鎖路徑寫入**，以可辨識退出碼結束並指出持鎖者。「取不到鎖就當作沒有鎖」是把機制退回紀律，等於本節不存在。

**臨界區只涵蓋首次寫入，其餘寫入在鎖外完成**——這是刻意的，不是遺漏。序號只被首次寫入消耗；後續寫入由 #16 §4.2 的自描述首寫在 resume 時推導補齊（§5.1 步驟 3）。把整個動詞包進鎖會讓鎖的持有時間等於整段網路往返，放大 §2.3 的殘留鎖問題，而換不到額外保證。

### 2.2 兩個鎖層級：卡層與專案層

§7.1 的機械列舉顯示 `ensure_fields` 是**專案層**的寫入（建立 Project 欄位），與 `card_id` 無關。以 `(owner, project, card_id)` 為鍵的卡層鎖**保護不到它**：同一專案的兩張不同卡同時執行時各持不同的鎖，兩者都可能讀到「欄位不存在」而各自送出 `field-create`。

> **裁定：兩個層級的鎖，先後取得、不巢狀持有。**
>
> - `L_project = (owner, project)`：保護 `ensure_fields` 的「讀既有欄位 → 逐一建立缺欄位」整段。**執行完立即釋放。**
> - `L_card = (owner, project, card_id)`：保護 §2.1 的五步臨界區。
>
> 兩者**不得同時持有**（先 `L_project` 做完並釋放，再取 `L_card`）。不巢狀即無鎖序問題，也無死鎖。

`ensure_fields` 的「讀既有欄位 → 判斷缺哪個 → 建立」本身也是 read-modify-write，所以它需要的是與 §2.1 同型的完整臨界區，而不是只把 `field-create` 那一行包起來。

### 2.3 殘留鎖回收：安全規則在設計層釘死，只有 TTL 具體值歸實作卡

前一版把回收機制整包留給實作卡，只寫「必須可判定失效並回收」。那個留白會被最自然的實作填成 **TTL 奪鎖**——而 TTL 奪鎖會奪走**仍存活**的鎖：程序被 `SIGSTOP`／睡眠喚醒延遲、GitHub 端慢回應、或首次寫入本身耗時超過 TTL，都會讓一個正在臨界區內的活程序被別人接手，同機互斥當場失效。這比崩潰卡死更糟：卡死是可見的，奪鎖後的雙寫是靜默的。

> **裁定：不得僅以 TTL 判定鎖失效並奪取。** TTL 的角色**降級為「開始做死亡判定」的觸發條件**，本身不構成回收依據。

回收只在**可證明原持有者已死亡**時允許。可證明的判準是機械的：

- 取鎖時必須以原子方式（先寫暫存再 `rename`，或建目錄後寫入再 `rename`）在鎖目錄留下**存活性 metadata**：主機識別、開機識別（boot id／開機時刻）、pid、以及該 pid 的**啟動時刻**。
- 回收者只有在**同一主機、同一次開機**下，且驗證「該 pid 不存在」或「存在但啟動時刻與 metadata 不符（pid 已被重用）」時，才可回收。
- **不同主機、不同開機識別、metadata 缺欄或損毀 → 無法證明 → fail-closed**，不回收、不寫入，印出鎖路徑與持有者資訊交人。
- 人工逃生門必須是**顯式命令**（例如帶確認的強制解鎖），動作與操作者寫入稽核輸出。**逃生門是人工的，不是自動 TTL 的別名**——這正是「一次崩潰不得讓該卡永久卡死」的兌現方式，代價是需要一次人的判斷。

**回收鎖不等於「先前沒有寫入成功」。** 死掉的持有者可能已經完成首次寫入。因此回收者取得鎖後**必須照 §2.1 從步驟 1 完整重跑**——它會在步驟 3 命中既有 `event_id` 並走 `already_exists`。這條要求讓回收的安全性不依賴「死者做到哪一步」的推測。

> **存活性 metadata 為何不是 canonical `:143`／`:165` 禁止的本機狀態**：判準是它能回答什麼問題。這些欄位只能回答「這個鎖的持有者還活著嗎」，**不能也不得**被任何路徑用來回答「我上次做了什麼」「我上次寫到哪」。`event_id`、`state_version`、動詞、參數、進度一律不得寫入鎖目錄；resume（§5.1）也不得讀鎖目錄的任何內容作為輸入。違反這條界線，鎖就變成 #16 §4.1 拒絕的預寫意圖日誌 [WAL]。實作卡須以一條檢查釘住：鎖目錄的欄位集合是封閉白名單，新增欄位即失敗。

---

## 3. `event_id`：由意圖決定性導出

### 3.1 為什麼隨機 UUID 撐不過重試

本設計採本機零狀態（#16 §4.2 的自描述首寫）。零狀態下，重試的新程序沒有任何管道得知上一次產生的隨機 id——**它認不出自己**。重試唯一能依靠的，是「從相同輸入重新算出相同的 id」。

### 3.2 為什麼「以鏈尖端為材料」恰好在最需要的時候失效

這是本節必須說明的關鍵反例，也是最容易被誤選的設計。

以「寫入者觀察到的鏈尖端」（最新事件的 id、或當前 `state_version`）為冪等鍵材料，直覺上很合理：它便宜、天然唯一、且看起來能表達因果順序。

但把失效情境展開就會看到它壞在哪：

1. 第一次執行：觀察到尖端＝事件 `E_k`，算出 `event_id = f(..., E_k)`，寫入成功，鏈尖端變成 `E_{k+1}`。
2. **回應在網路上遺失**，CLI 不知道自己成功了。
3. 重試：觀察到尖端已經是 `E_{k+1}`（**自己剛寫的那一筆**），算出 `event_id = f(..., E_{k+1}) ≠ f(..., E_k)`。
4. 於是重試認不出先前的寫入，寫出第二筆語意重複的事件。

**失效點的位置是致命的**：這個鍵在鏈沒有變動時完全正常，只在「鏈剛剛被自己改過、而自己不知道」時失效——而那**正是**冪等鍵存在的唯一理由。它在所有不需要它的情況下都能用，在唯一需要它的情況下必定失效。

同樣的推理排除時鐘（每次重試都不同）與 `state_version`（取號依賴鏈的當前狀態，與尖端同構）。

### 3.3 導出式

```
event_id = uuid5(NS_WFCLI, canonical(target, card_id, verb, args, attempt_salt))
```

- `NS_WFCLI`：固定的 UUID namespace 常數，凍結於實作，變更即等同全體事件重新編號。
- `target`：**`resolve_target()` 解析後**的 `(owner, project, repo)` 三元組，**不是** `--owner`／`--project`／`--repo`／`--config` 四個原始旗標。這個區別是必要的而非潔癖：四個旗標是同一個目標的**四個來源**（`config.py:44`–`:50` 的優先序為 CLI flag > `--config` 檔 > 環境變數），`wfcli handoff --owner ruan6047` 與 `wfcli handoff --config f.json`（`f.json` 內 `owner` 為 `ruan6047`）**產生完全相同的事件**。若以原始旗標入鍵，兩者算出相異的鍵，於是第二次執行寫出重複事件——正是本卡要防的東西。故四個旗標一律**鍵外**（§4.1b），解析後的三元組直接入鍵。`repo` 為 `None`（draft issue 模式）時以零長度表示，與空字串 repo 不同型別故不碰撞。
- `args`：該動詞**其餘**的全部使用者輸入，依 §4 逐欄位型別正規化後，以「欄位名 ‖ 長度 ‖ 位元組」串接。**長度前綴不可省**——沒有它，`(a="x", b="yz")` 與 `(a="xy", b="z")` 會串出相同位元組（§4.5 探針末段有可重跑的反例）。
- `attempt_salt`：**旗標缺席時為零長度**；僅在操作者顯式帶 `--new-attempt <標籤>` 時取該標籤。它與 `args` 各欄位一樣是有型別的輸入，型別＝**嘗試標籤**，canonical bytes 定義見 §4.5，語意見 §5.3。
- **不含鏈尖端、不含時鐘、不含 `state_version`。**

欄位名本身也進入串接，且欄位須**依欄位名排序**後串接——否則 CLI 內部參數順序的重構會靜默改變所有既有事件的鍵。

---

## 4. `args` 的 canonical bytes：逐型別，全函數

「NFC ＋ 長度前綴」不足以定義所有欄位的規範位元組：換行、尾隨空白、結構化資料與 emoji 枚舉各有各的歧義來源。逐型別定義，**不留「其餘」格**。

### 4.1 七個型別

進入 `event_id` 的輸入**全部**在此表內，包含 `attempt_salt`——前一版把它寫在 §3.3 而未給型別，等於留了一個表外的第七種輸入，那正是本節宣稱要消滅的東西。

**「路徑」不再是其中一個型別**，理由見 §4.1b：那一列是分類錯誤，本輪已撤除。

| 型別 | 規範化 | 歧義來源 |
|---|---|---|
| **自由文字**（`--evidence`、`--reason`、`--actor`、查核報告） | Unicode **NFC**；行尾一律 `LF`；去除每行尾隨空白與整體尾隨換行 | CRLF、貼上時的尾白、輸入法產生的 NFD |
| **枚舉**（交付狀態、部署狀態、級別、`db_scope`、`next-stage`、`decision`） | **逐位元組取自 `FIELD_SPECS` 的凍結字串**；輸入含 **variation selector**（`U+FE0E`／`U+FE0F`）或零寬字元（`U+200B`–`U+200D`、`U+FEFF`）者**拒收** | 狀態值本身是 emoji，終端與輸入法會插入變體選擇符 |
| **記錄型路徑**（`--worktree`） | **逐字寫入狀態面的字串**，套自由文字規範化（NFC、行尾、去尾白）；**不做任何檔案系統解析**（不 `realpath`、不展開 `~`、不摺疊尾斜線） | 見 §4.1b：解析反而會製造錯誤 |
| **SHA／識別碼**（`--source-sha`、`card_id`、`--card-id`、`--main-ref`、`--branch`） | 小寫 hex 且長度固定（SHA）；識別碼逐位元組比對，不做大小寫摺疊 | 大小寫、短 SHA |
| **整數／布林**（`--iteration`、`--escalation-epoch`、`--project`、各 `--dry-run` 類旗標） | 十進位無前導零／`true`\|`false` | 空白、`True`、`+1`、前導零 |
| **結構化輸入**（`--acceptance`、`--verification`、`--resources`、findings 區塊） | 先解析為資料結構，再以**排序鍵、無註解、無錨點**的規範形式序列化；**不對原始文字取雜湊** | 縮排、鍵序、註解、YAML 別名 |
| **嘗試標籤**（`--new-attempt`，即 `attempt_salt`） | **封閉 ASCII 字元類** `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`，不合者拒收；不做 NFC（非 ASCII 已被擋在門外）；旗標缺席＝零長度 | 空字串與缺席同形、NFC／NFD、變體選擇符、零寬、換行、尾白、路徑形、無上限長度（§4.5） |

### 4.1b CLI 路徑引數：前一版的「路徑型別」是分類錯誤，本輪撤除

前一版把七個看起來像路徑的引數（`--worktree`、`--repo-path`、`--config`、`--input`、`--out-dir`、`--spec-dir`、`repo_root`）歸為一個「路徑」型別，並把它的規範化交給 [#24](https://github.com/ruan6047/ai-workflow/issues/24) 的封閉 namespace，§10 的 A2／A3 列為待驗假設。

**兩張卡都已交付，假設可判定了——不成立。** #24 §3.1 於其交付版明文劃界：該 namespace 規範的是**卡面 `file:` 資源宣告字串**，其規則 2／3 拒收 `/` 與 `~` 起始、規則 4 拒收 `..` 分量，理由是宣告必須是 repo 根相對路徑才有共同座標可比；而 CLI 引數必須解析到執行當下的真實檔案系統位置，絕對路徑與 `~` 在那裡合法且必要。#24 並把引數正規化明文**回指本卡**。兩者定義域不相容，`file:` 的規則套到 CLI 引數上是錯誤引用。

**但真正的問題不是「該由誰定義路徑正規化」，而是「這些引數根本不該被當成同一個型別」。** 分類鍵應該是**該引數對事件內容的貢獻**，不是它的表面語法長得像不像路徑——這正是 §4.3 已經對 `--status` 立下的原則（分類鍵是目的地，不是宣告）。前一版對 `--status` 用了這條原則，對路徑卻沒有，於是七個貢獻方式完全不同的引數被綁進同一格。

逐一追碼（承接的六個動詞，其餘三個引數只在不承接動詞上，見下）：

| 引數 | 對事件內容的實際貢獻 | 處置 |
|---|---|---|
| `--worktree`（`assign`，**required**） | `format_branch_worktree(args.branch, args.worktree)`（`card.py:67`–`:70`，純字串內插，無檔案系統存取）→ 逐字寫入 `分支worktree` 欄位（`assign_cmd.py:113`／`:115`） | **記錄型路徑**：以字面字串入鍵 |
| `--config`（六個動詞皆有） | 只供給 `resolve_target` 的 `(owner, project, repo)`（`config.py:44`–`:50`），本身不寫入任何欄位 | **鍵外**；解析後三元組入鍵（§3.3） |
| `--owner`／`--project`／`--repo`（六個動詞皆有） | 與 `--config` 同為目標解析的四個來源之一 | **鍵外**；同上 |
| `--repo-path`（`handoff`） | 僅唯讀驗證 `source_sha` 該 commit 存在（`handoff_cmd.py:77`–`:78`），不寫入事件內容 | **鍵外** |
| `--input`（`review`） | 讀入檔案**內容**（`review_cmd.py:139` `_read_input`），內容以自由文字入鍵 | **鍵外**；內容入鍵，路徑不入鍵 |

`--out-dir`／`--spec-dir`／`repo_root` 分別只存在於 `snapshot`／`open`／`doctor`——`open` 明示不承接（§8），`snapshot`／`doctor` 唯讀且不產生 lifecycle 事件，三者永不進 `event_id`。**這個豁免依據不是假設，是 §4.4 分類器的一條斷言**：任一者若出現在承接動詞上，檢查即紅（負向測試 D）。

**目標解析四旗標的豁免依據同樣經過查證，不是推定**。該豁免只有在「四個旗標對事件內容的影響**全部**經由 `resolve_target` 的回傳值」時才成立——若任一動詞另外直接讀 `args.owner`／`args.repo` 去寫欄位，那條路徑就繞過了鍵。機械核對（`grep -rn "args\.owner\|args\.repo\b\|args\.project\|args\.config" cli/src/wf_cli/commands/`）：六個承接動詞對這四個名字**只有一處出現**，即 `resolve_target(...)` 的引數列（`review_cmd.py:178`–`:179`、`amend_cmd.py:273`–`:274`、`handoff_cmd.py:86`–`:87`、`assign_cmd.py:64`–`:65`、`deploy_declare_cmd.py:70`–`:71`、`deploy_state_cmd.py:86`–`:87`）；其餘直接取用只出現在 `doctor_cmd.py` 與 `snapshot_cmd.py`，兩者皆不承接且唯讀。實作卡須把這條核對一併落為 CI，理由與負向測試 D 相同：**豁免依據是關於碼的事實宣稱，事實會變，宣稱就需要執行者。**

> **裁定：承接的六個動詞裡，沒有任何一個引數需要檔案系統路徑正規化。** 因此本卡**不定義**、也**不引用**任何 CLI 路徑正規化器；`event_id` 的位元組來源不再有任何一部分取自 #24。

**為什麼不選「自己定義一套保守的 CLI 路徑正規化」**（查核者提的第二條路）：因為那會是一個新的全函數宣稱，而它**做不到**。要讓同一邏輯路徑在不同 cwd／symlink 狀態下產生同一組位元組，就得 `realpath`，而 `realpath` 對尚未存在的路徑沒有定義（`--out-dir` 正是這種）；要處理大小寫與 NFC／NFD，就得知道該卷是否大小寫敏感、是否正規化不敏感（macOS APFS 與 Linux ext4 答案不同），**那是執行期的檔案系統性質，不是設計期可判定的常數**。寫得出來的只會是一個在某些機器上摺疊過度、在另一些機器上摺疊不足的函式——而摺疊過度的後果是把操作者顯式的新意圖靜默回答成 `already_exists`（§5.3 明文禁止的那件事）。**本專案對這類宣稱的標準已經很清楚：#24 連兩輪被打的都是「宣稱大於證據」。** 與其新增一個撐不住的宣稱，不如證明它不需要。

**為什麼也不是查核者提的第一條路（整批降級）**：實測顯示那會把卡打空。`--config` 存在於全部六個承接動詞，`assign --worktree` 是 **required**——以「引數面含路徑型別即該動詞退出冪等保護」實作，六個動詞會**全部**永久退出，本卡的保護面歸零。降級路徑（§4.2）仍然保留給未來真正需要檔案系統正規化的新引數，但今天沒有一個引數落在那裡。

**這個處置的代價，明說**：`--worktree` 以字面字串入鍵，意謂 `/a/b` 與 `/a/b/`、絕對與相對、symlink 與實體路徑會算出**不同的鍵**。這是**刻意的**——它們寫進 `分支worktree` 欄位的值本來就不同，是不同的事件，摺疊才是錯的。殘餘曝險是：操作者若在重試時把路徑**改寫成另一種拼法**，會寫出第二筆事件。這不是路徑特有的性質（任一引數改動都會改鍵，§6 已裁定），但路徑的「同一個東西的不同拼法」表面比其他型別寬，故在 §11 單獨列為殘餘限制。

### 4.2 沒有「其餘」格，靠的是 fail-closed 收尾規則

上表是**閉包**，不是常見情形的列舉。使其成立的是這條規則：

> **任何無法歸入上表七型別的新欄位，在其型別規範化定義補上之前，該動詞不得納入冪等鍵機制。**

這條規則讓分類成為全函數：新欄位不是落進某個沉默的預設格，而是**擋下整個動詞**。代價是新增欄位時會踩到明顯的阻擋，這是刻意的——沉默的預設格正是 #22 在自己新增的表格上漏掉一整格的成因，而漏掉的那格不會有人發現，直到它產生錯誤的鍵。

**「不得納入冪等鍵機制」的具體語意**：該動詞退回無冪等保護的狀態（即今日行為），**而非拒絕執行**。它必須在 stderr 明示「本動詞因欄位 X 無規範化定義而未受冪等保護，重試可能產生重複事件」。fail-closed 指的是不對未定義輸入計算鍵，不是把 CLI 鎖死。

**§4.1b 的「鍵外輸入」不得成為這條規則的逃生口。** 一個引數被判為鍵外，只有在下述條件成立時才合法：

> **鍵外條件**：該引數對「寫入的事件內容」的全部影響，已由其他入鍵材料完整涵蓋。

這個條件必須**逐引數具名論證並登錄**（§4.4 的 `KEY_EXEMPT` 是附理由的封閉表），不得由分類器推導、更不得作為未登錄引數的預設。理由與 §4.2 本身相同：一個沉默的「這個大概不重要」預設格，會讓真正影響事件內容的引數靜默逸出鍵，而後果（兩個不同意圖算出同鍵 → 第二次被回答 `already_exists` → 操作者以為寫成功了）比未分類更糟，因為它不會報錯。分類器對鍵外輸入**逐理由印出筆數**，使豁免面可稽核而不是一團數字。

### 4.3 分類鍵是**目的地欄位**，不是 argparse 宣告

設計本節時對現行 CLI 做了機械列舉（§4.4），發現一個會直接擊穿 emoji 拒收條款的缺陷：

**`handoff --status` 與 `assign --status` 直接寫入 `FIELD_SPECS["交付狀態"]`（SINGLE_SELECT），但兩者的 argparse 宣告都沒有 `choices=`。**

- `assign_cmd.py:58` 宣告 `--status`，預設 `🚧進行中`，無 `choices`；`:116` 將其原樣送進 `set_field_value(..., fields["交付狀態"], args.status)`。
- `handoff_cmd.py:57` 宣告 `--status` 為「覆寫依 next-stage 推導出的交付狀態」，無 `choices`；`:100` 取值後於 `:137` 寫入同一欄位。
- `amend_cmd.py:88` 的 `--db-scope` 同型：`open` 對 `--db-scope` 宣告了 `choices`，`amend` 沒有。同一個邏輯欄位，兩個動詞的驗證強度不一致。

後果很具體：**以 argparse 宣告為分類鍵的實作，會把 `--status` 判為自由文字**，於是套用 NFC 正規化——而 **NFC 不會移除 `U+FE0F`**。`--status "🚧進行中<U+FE0F>"` 因此會通過，並與不含變體選擇符的同一狀態算出**不同的 `event_id`**。這正是卡面驗證第 2 條要擋的情形，且它會因終端差異而不可重現。

**因此分類鍵定為欄位的目的地**：凡最終寫入 `FIELD_SPECS` 中 `SINGLE_SELECT` 欄位的輸入，一律套枚舉規範化，與該旗標在 argparse 是否宣告 `choices` 無關。

> 這是**設計層的裁定**，不是實作缺陷回報。實作卡另須補齊 `--status`／`--db-scope` 的 `choices` 驗證，但即使補齊了，分類鍵仍然是目的地欄位——因為「宣告與目的地不一致」隨時可能再次發生，而分類的正確性不該依賴另一處的紀律。

### 4.4 完備性如何驗證（可重跑，非斷言）

「七型別涵蓋全部輸入」是可以被機械檢查的宣稱，因此本節給出檢查方法而非斷言。分類器對 `wfcli` 全部子指令的參數面求值，**任何未分類的參數即為失敗**：

**關鍵設計**：分類器**不得有沉默的預設格**。「未登錄的旗標一律當自由文字」這種寫法會讓檢查變成恆真——那正是本節要防的缺陷，寫在檢查器自己身上。因此每個型別都是**顯式登錄集**，落在全部集合之外者回傳 `None` 並使檢查失敗。

分類器另須對**尚未存在的參數**成立。`--new-attempt` 在基線並不存在（`grep -rn "new-attempt" cli/` 無命中），若只跑基線參數面，`attempt_salt` 的型別登錄就沒有任何機械證據——這正是前一版讓它逸出 §4.1 的成因。因此腳本帶一個 `inject` 模式：把 `--new-attempt` 合成加到六個承接動詞上再跑一次。

```python
"""§4.4 分類器：無沉默預設格。未登錄的參數即未分類 → 失敗。
唯讀 argparse 內省，不連 GitHub、不寫任何狀態。自 repo root 執行。
用法：uv run python probe44.py [base|inject]
負向測試環境變數：DROP_ATTEMPT=1、DROP_DEST_ENUM=1、DROP_FREETEXT=1、LEAK_SPECDIR=1"""
import argparse, sys, os
sys.path.insert(0, "cli/src")
from wf_cli.cli import build_parser

IDEMPOTENT_VERBS = {"review", "amend", "handoff", "assign",
                    "deploy-declare", "deploy-state"}

# §4.1 記錄型路徑：逐字寫入狀態面，不做檔案系統解析（canonical bytes 同自由文字）。
RECORDED_PATH = {"--worktree"}
# §4.1b 鍵外輸入：對事件內容的全部影響已由其他入鍵材料涵蓋。封閉登錄，附理由。
KEY_EXEMPT = {
    # 目標解析來源：四者皆只供給 resolve_target 的 (owner, project, repo)，
    # 該三元組以「解析後的值」直接入鍵（§3.3）。個別旗標不入鍵，否則
    # `--owner X` 與 `--config f`（f 內 owner=X）會產生同事件而異鍵。
    "--owner":     "目標解析來源：以解析後的 (owner, project, repo) 入鍵",
    "--project":   "目標解析來源：以解析後的 (owner, project, repo) 入鍵",
    "--repo":      "目標解析來源：以解析後的 (owner, project, repo) 入鍵",
    "--config":    "目標解析來源：以解析後的 (owner, project, repo) 入鍵",
    "--repo-path": "唯讀本機驗證 source_sha，不寫入事件內容",
    "--input":     "內容來源：讀入的文字以自由文字入鍵，路徑本身不入鍵",
    "--out-dir":   "僅存在於不承接動詞（snapshot）",
    "--spec-dir":  "僅存在於不承接動詞（open）",
    "repo_root":   "僅存在於不承接動詞（doctor）",
}
# 上列後三者的豁免理由是「不在承接動詞上」，必須被機械釘住而非假設。
NON_COVERED_ONLY = {"--out-dir", "--spec-dir", "repo_root"}

SHA = {"--source-sha"}
IDENT = {"card_id", "--card-id", "--main-ref", "--branch"}
STRUCT = {"--acceptance", "--verification", "--resources"}
FREETEXT = {"--evidence", "--reason", "--actor", "--reviewer", "--assignee",
            "--to", "--next-owner", "--feature", "--core-pain", "--service-goal",
            "--initiative", "--requested-by", "--planned-by", "--executor",
            "--spec-baseline"}
if os.environ.get("DROP_FREETEXT"):
    FREETEXT = FREETEXT - {"--evidence"}
# §4.5 嘗試標籤：基線尚無此旗標，登錄先行以使 CI 在實作卡加入它的當下即生效。
ATTEMPT = set() if os.environ.get("DROP_ATTEMPT") else {"--new-attempt"}
# §4.3：argparse 宣告不足以決定型別者——直接寫入 FIELD_SPECS SINGLE_SELECT 欄位。
DEST_ENUM = set() if os.environ.get("DROP_DEST_ENUM") else {
    ("handoff", "--status"), ("assign", "--status"), ("amend", "--db-scope")}


def classify(verb, act, name):
    if name in ATTEMPT:
        return "嘗試標籤"
    if (verb, name) in DEST_ENUM:
        return "枚舉"
    if name in KEY_EXEMPT:
        return "鍵外輸入"
    if name in RECORDED_PATH:
        return "記錄型路徑"
    if isinstance(act, (argparse._StoreTrueAction, argparse._StoreFalseAction)):
        return "整數／布林"
    if act.choices is not None:
        return "枚舉"
    if act.type in (int, float):
        return "整數／布林"
    if name in SHA or name in IDENT:
        return "SHA／識別碼"
    if name in STRUCT:
        return "結構化輸入"
    if name in FREETEXT:
        return "自由文字"
    return None  # 無沉默預設格


mode = sys.argv[1] if len(sys.argv) > 1 else "base"
parser = build_parser()
sub = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
if mode == "inject":
    for verb in sorted(IDEMPOTENT_VERBS):
        sub.choices[verb].add_argument("--new-attempt", help="§5.3 顯式新一筆")
if os.environ.get("LEAK_SPECDIR"):  # 負向測試 D：把只該在 open 的旗標漏到承接動詞上
    sub.choices["handoff"].add_argument("--spec-dir", help="負向測試注入")

total, unclassified, counts, leaked, exempt_by_reason = 0, [], {}, [], {}
for verb, p in sub.choices.items():
    for act in p._actions:
        if isinstance(act, argparse._HelpAction):
            continue
        name = act.option_strings[0] if act.option_strings else act.dest
        kind = classify(verb, act, name)
        total += 1
        if kind is None:
            unclassified.append((verb, name))
        else:
            counts[kind] = counts.get(kind, 0) + 1
        if kind == "鍵外輸入":
            r = KEY_EXEMPT[name]
            exempt_by_reason.setdefault(r, []).append("%s %s" % (verb, name))
        # 豁免理由「只在不承接動詞上」必須成立，否則該豁免無依據。
        if name in NON_COVERED_ONLY and verb in IDEMPOTENT_VERBS:
            leaked.append((verb, name))

print("[%s] 直譯器 = %s" % (mode, ".".join(str(x) for x in sys.version_info[:3])))
print("[%s] 總參數數 = %d；未分類 = %d；豁免依據失效 = %d"
      % (mode, total, len(unclassified), len(leaked)))
for v, n in unclassified:
    print("  未分類 %s %s" % (v, n))
for v, n in leaked:
    print("  豁免依據失效：%s 出現在承接動詞 %s 上" % (n, v))
print("分類分佈：" + "、".join("%s %d" % (k, counts[k]) for k in sorted(counts)))
print("鍵外輸入逐理由（豁免須可稽核，不得是一團數字）：")
for r in sorted(exempt_by_reason):
    print("  %2d 筆　%s" % (len(exempt_by_reason[r]), r))
raise SystemExit(1 if (unclassified or leaked) else 0)
```

**基線參數面實跑**（9 個子指令，`open`／`doctor`／`snapshot` 一併列入以確認分類器對唯讀與不承接動詞同樣是全函數）：

```
[base] 直譯器 = 3.12.13
[base] 總參數數 = 106；未分類 = 0；豁免依據失效 = 0
分類分佈：SHA／識別碼 13、整數／布林 16、枚舉 10、結構化輸入 6、自由文字 20、記錄型路徑 1、鍵外輸入 40
鍵外輸入逐理由（豁免須可稽核，不得是一團數字）：
   1 筆　僅存在於不承接動詞（doctor）
   1 筆　僅存在於不承接動詞（open）
   1 筆　僅存在於不承接動詞（snapshot）
   1 筆　內容來源：讀入的文字以自由文字入鍵，路徑本身不入鍵
   1 筆　唯讀本機驗證 source_sha，不寫入事件內容
  35 筆　目標解析來源：以解析後的 (owner, project, repo) 入鍵
exit=0
```

**鍵外輸入 40 筆看似龐大，逐理由拆開後不是**：其中 **35 筆是 `--owner`／`--project`／`--repo`／`--config` 分佈在 9 個子指令上**，它們的值**並未離開鍵**，而是以 `resolve_target` 解析後的三元組入鍵一次（§3.3）——這是把同一個目標的四個來源收斂成一個鍵材料，不是豁免。真正「路徑形且不入鍵」的只有 5 筆，逐筆理由見 §4.1b。**逐理由列印是刻意的**：一個沒有拆解的「鍵外 40」無法被查核，而豁免面正是最需要被看見的地方。

**注入 `--new-attempt` 後實跑**（六個承接動詞各加一個）：

```
[inject] 直譯器 = 3.12.13
[inject] 總參數數 = 112；未分類 = 0；豁免依據失效 = 0
分類分佈：SHA／識別碼 13、嘗試標籤 6、整數／布林 16、枚舉 10、結構化輸入 6、自由文字 20、記錄型路徑 1、鍵外輸入 40
exit=0
```

**負向測試 A**（證明檢查非恆真）：`DROP_FREETEXT=1` 自 `FREETEXT` 移除 `--evidence` 後重跑基線——

```
[base] 總參數數 = 106；未分類 = 2；豁免依據失效 = 0
  未分類 deploy-state --evidence
  未分類 handoff --evidence
分類分佈：SHA／識別碼 13、整數／布林 16、枚舉 10、結構化輸入 6、自由文字 18、記錄型路徑 1、鍵外輸入 40
exit=1
```

**負向測試 B**（證明 §4.5 的登錄是必要的，不是裝飾）：`DROP_ATTEMPT=1` 清空 `ATTEMPT` 後跑注入模式——

```
[inject] 總參數數 = 112；未分類 = 6；豁免依據失效 = 0
  未分類 assign --new-attempt
  未分類 amend --new-attempt
  未分類 deploy-declare --new-attempt
  未分類 deploy-state --new-attempt
  未分類 handoff --new-attempt
  未分類 review --new-attempt
分類分佈：SHA／識別碼 13、整數／布林 16、枚舉 10、結構化輸入 6、自由文字 20、記錄型路徑 1、鍵外輸入 40
exit=1
```

未登錄的參數確實會被指名並使檢查失敗。**沒有這些負向測試，「未分類 = 0」不構成證據**——它同樣可能來自一個永遠回傳某個型別的分類器。負向測試 B 另有一層意義：`--new-attempt` 在有沉默預設格的分類器下會落入自由文字並套 NFC，**而 NFC 不移除 `U+FE0F`**——與 §4.3 的 `--status` 是同一個缺陷模式，只是換一個旗標復發。

**負向測試 C（§4.3 的證據）**：`DROP_DEST_ENUM=1` 清空 `DEST_ENUM`（即改以 argparse 宣告為唯一分類鍵）重跑基線——

```
[base] 總參數數 = 106；未分類 = 3；豁免依據失效 = 0
  未分類 assign --status
  未分類 amend --db-scope
  未分類 handoff --status
分類分佈：SHA／識別碼 13、整數／布林 16、枚舉 7、結構化輸入 6、自由文字 20、記錄型路徑 1、鍵外輸入 40
exit=1
```

這三個旗標**無法由 argparse 宣告分類**：它們既沒有 `choices`，也不屬於記錄型路徑／SHA／整數布林／結構化任何一類。有沉默預設格的分類器會把它們歸入自由文字並靜默通過，**於是 §4.1 的 emoji 拒收條款對真正的暴露面完全不生效**；無預設格的分類器則當場指名它們。這就是分類鍵必須是目的地欄位的機械證據。

**負向測試 D（§4.1b 豁免依據的證據，本輪新增）**：`--out-dir`／`--spec-dir`／`repo_root` 的豁免理由是「只出現在不承接動詞上」。這是一個**關於碼的事實宣稱**，不是設計者的斷言，因此必須有機械執行者。`LEAK_SPECDIR=1` 把 `--spec-dir` 合成加到 `handoff` 上模擬未來的擴充——

```
[base] 總參數數 = 107；未分類 = 0；豁免依據失效 = 1
  豁免依據失效：--spec-dir 出現在承接動詞 handoff 上
分類分佈：SHA／識別碼 13、整數／布林 16、枚舉 10、結構化輸入 6、自由文字 20、記錄型路徑 1、鍵外輸入 41
exit=1
```

注意這一格的重要性：**分類本身沒有失敗（未分類 = 0），失敗的是豁免的依據。** 若只檢查「每個參數都分得出型別」，這個情形會靜默通過——`--spec-dir` 仍然被歸為鍵外輸入，於是一個真正影響事件內容的引數逸出了鍵，而且不會有任何紅燈。這正是 §4.2「鍵外條件」需要獨立執行者的原因。

**跨直譯器實跑**（R2-002）：`python3` 在本機解析到三個不同的直譯器，故本節不宣稱一般性可攜，只報告**實測範圍**——

| 直譯器 | 取得方式 | `base` 結果 |
|---|---|---|
| 3.9.6 | `/usr/bin/python3`（macOS 系統） | 總參數 106／未分類 0／豁免依據失效 0，exit=0 |
| 3.12.13 | `uv run python`（專案 venv，**指令釘選於此**） | 同上，exit=0 |
| 3.14.3 | `mise` 安裝於 `PATH` 前段 | 同上，exit=0 |

三者輸出的分類分佈完全一致。**未實測 3.9.6 以下與 3.14.3 以上，本節不對該範圍外作任何宣稱。**

實作卡須把本腳本落為 CI 檢查（`base` 與 `inject` 兩個模式都跑，四個負向測試一併釘住）：**新增參數而未能分類、或豁免依據失效，即 CI 紅**，使 §4.2 的兩條規則（型別閉包、鍵外條件）都有機械執行者，而不是文件裡的一句「應該要」。

### 4.5 嘗試標籤的 canonical bytes

`--new-attempt` 的取值直接進 `event_id`（§3.3），所以它承受與其他欄位**完全相同**的規範化壓力：NFC／NFD、變體選擇符、零寬字元、CRLF、尾白、長度。前一版只寫「取該標籤」，等於把一個未定義的位元組來源接進鍵——同一個標籤在不同終端貼上就可能算出不同的鍵，而「不同的鍵」的後果是寫出第二筆重複事件（正是本卡要防的東西）。

**採取的處置是「禁止不安全的輸入形式」而非「事後正規化」**：字元類收窄到純 ASCII，所有 Unicode 歧義來源在門口就不存在，不需要正規化，也就沒有正規化實作差異的空間。標籤是操作者為稽核而取的短名，不是自由文字，收窄不損失表達力。

> **裁定：嘗試標籤的接受集合為 `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`（長度 1–64，首字元英數）。**
> canonical bytes ＝該字串的 ASCII 位元組，**不套 NFC**。旗標缺席時 `attempt_salt` 為**零長度**。

四條隨附規則：

- **空字串必須拒收**，這是可推導的而非品味問題：長度前綴串接下 `--new-attempt ""` 與「缺席」產生**同一組位元組**，因此同一個 `event_id`。若接受空字串，操作者顯式宣告「這是新的一筆」會被系統回答 `already_exists`——把明示意圖靜默降級為重試，正是 §5.3 禁止的那件事。接受集合的長度下限 1 讓這個情形無法構成。
- **非 ASCII 一律拒收**（含 CJK、`U+FE0E`／`U+FE0F`、`U+200B`–`U+200D`、`U+FEFF`、NFC 與 NFD 兩種寫法的組合字），錯誤訊息須指出合法字元類，不得靜默剝除。**靜默剝除等同於事後正規化，會讓兩個不同輸入摺疊成同一個鍵**，違反 §5.3 的 fail-loud。
- **空白（含前後空白、內部空白、換行、CR）拒收**，理由同上：修剪是一種靜默摺疊。
- **長度上限 64**，避免把整段自由文字塞進標籤而繞過型別。

參考驗證器與碰撞測試（可重跑，純函式，不需 `wf_cli`）：

```python
"""§4.5 嘗試標籤參考驗證器與碰撞測試。純函式，不連 GitHub、不寫任何狀態。"""
import re, uuid, unicodedata

NS_WFCLI = uuid.UUID("00000000-0000-5000-8000-000000000000")  # 佔位；實作卡凍結真值
LABEL_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")

class Reject(ValueError): pass

def attempt_bytes(raw):
    """缺席（None）→ b''。其餘先驗後取 ASCII 位元組，不做 NFC。"""
    if raw is None:
        return b""
    if not LABEL_RE.fullmatch(raw):
        raise Reject(f"attempt label 不合法：{raw!r}")
    return raw.encode("ascii")

def field(name, value):
    n = name.encode("utf-8")
    return len(n).to_bytes(4, "big") + n + len(value).to_bytes(4, "big") + value

def event_id(owner, project, card_id, verb, args, salt):
    parts = [field("owner", owner.encode()), field("project", str(project).encode()),
             field("card_id", card_id.encode()), field("verb", verb.encode())]
    parts += [field(k, args[k]) for k in sorted(args)]
    parts.append(field("attempt_salt", attempt_bytes(salt)))
    return str(uuid.uuid5(NS_WFCLI, b"".join(parts).decode("latin-1")))

BASE = dict(owner="ruan6047", project=4, card_id="WF-EVENT-IDEMPOTENCY1",
            verb="handoff", args={"evidence": b"x"})
REJECT_CASES = [
    ("空字串（--new-attempt \"\"）", ""), ("僅空白", "  "), ("含空白", "retry 2"),
    ("含 CJK（NFC 敏感）", "重跑"),
    ("NFD 組合字", unicodedata.normalize("NFD", "café")),
    ("NFC 組合字", unicodedata.normalize("NFC", "café")),
    ("含變體選擇符 U+FE0F", "retry️"), ("含零寬 U+200B", "re​try"),
    ("含 BOM U+FEFF", "﻿retry"), ("含換行", "retry\n"), ("含 LF+CR", "retry\r\n"),
    ("超長（65）", "a" * 65), ("首字元非英數", "-retry"), ("含斜線（路徑形）", "a/b"),
]
ACCEPT_CASES = ["r2", "a" * 64, "rerun.2026-08-11", "RETRY-x"]

bad = []
print("== 拒收案例 ==")
for label, raw in REJECT_CASES:
    try:
        attempt_bytes(raw); bad.append(label); print(f"  FAIL 未拒收：{label} {raw!r}")
    except Reject:
        print(f"  ok  拒收 {label}")
print("\n== 接受案例 ==")
for raw in ACCEPT_CASES:
    try:
        attempt_bytes(raw); print(f"  ok  接受 {raw!r}")
    except Reject:
        bad.append(raw); print(f"  FAIL 誤拒 {raw!r}")
print("\n== 碰撞測試 ==")
absent = event_id(**BASE, salt=None)
print(f"  缺席 salt 兩次同鍵：{'ok' if absent == event_id(**BASE, salt=None) else 'FAIL'}")
keys = {absent: "<缺席>"}
for raw in ACCEPT_CASES:
    k = event_id(**BASE, salt=raw)
    if k in keys:
        bad.append(raw); print(f"  FAIL 碰撞 {raw!r} 與 {keys[k]} 同鍵")
    else:
        keys[k] = raw; print(f"  ok  {raw!r} 與 <缺席> 及其他標籤皆不同鍵")
print(f"  同標籤重入同鍵："
      f"{'ok' if event_id(**BASE, salt='r2') == event_id(**BASE, salt='r2') else 'FAIL'}")
print("\n== 長度前綴必要性（§3.3 反例）==")
print(f"  無前綴：('x','yz') 與 ('xy','z') 串出相同位元組 = {'x'+'yz' == 'xy'+'z'}")
print(f"  有前綴：{field('a', b'x') + field('b', b'yz') == field('a', b'xy') + field('b', b'z')}")
print(f"\n失敗項 = {len(bad)}")
raise SystemExit(1 if bad else 0)
```

實跑輸出（14 個拒收案例全數拒收、4 個接受案例全數接受、碰撞 0）：

```
== 拒收案例 ==
  ok  拒收 空字串（--new-attempt ""）
  ok  拒收 僅空白
  ok  拒收 含空白
  ok  拒收 含 CJK（NFC 敏感）
  ok  拒收 NFD 組合字
  ok  拒收 NFC 組合字
  ok  拒收 含變體選擇符 U+FE0F
  ok  拒收 含零寬 U+200B
  ok  拒收 含 BOM U+FEFF
  ok  拒收 含換行
  ok  拒收 含 LF+CR
  ok  拒收 超長（65）
  ok  拒收 首字元非英數
  ok  拒收 含斜線（路徑形）

== 接受案例 ==
  ok  接受 'r2'
  ok  接受 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
  ok  接受 'rerun.2026-08-11'
  ok  接受 'RETRY-x'

== 碰撞測試 ==
  缺席 salt 兩次同鍵：ok
  ok  'r2' 與 <缺席> 及其他標籤皆不同鍵
  ok  'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' 與 <缺席> 及其他標籤皆不同鍵
  ok  'rerun.2026-08-11' 與 <缺席> 及其他標籤皆不同鍵
  ok  'RETRY-x' 與 <缺席> 及其他標籤皆不同鍵
  同標籤重入同鍵：ok

== 長度前綴必要性（§3.3 反例）==
  無前綴：('x','yz') 與 ('xy','z') 串出相同位元組 = True
  有前綴：False

失敗項 = 0
exit=0
```

> **這份腳本的角色是規格，不是實作**。`NS_WFCLI` 是佔位常數（鍵的**相對關係**——同輸入同鍵、異輸入異鍵——不因 namespace 取值而改變，所以碰撞測試在佔位值下仍然有效）；實作卡凍結真值後須以同一組案例重跑。行為的權威是上面的裁定與四條規則，腳本只是使它們可被機械檢查。

---

## 5. resume 演算法、`already_exists` 與 salt

### 5.1 演算法（純讀 GitHub，無本機狀態）

**步驟 1–4 全部在 §2.1 的卡層鎖臨界區內執行，順序即該處裁定的五步**。這裡不另立一套順序——前一版把演算法寫在鎖外、只把「重讀確認 → 寫入」放進鎖，那個落差就是 §2.1 修正的缺陷。

0.（鎖外，選配）預檢與 `--dry-run`。此處的讀取結果**不得**帶進步驟 1–4。取得 `L_card`（取不到即 fail-closed，§2.1）。
1. 讀該卡完整事件流，取得現有最大序號，並套用 §1.2 的五情形判準。任一 fail-closed 情形成立 → 該卡降純偵測，**演算法終止**。
2. 依 §3.3 算出本次的 `event_id`（**不需要鏈尖端**）。
3. **若該 `event_id` 已存在於剛讀到的事件流** → 這是同一意圖先前已落地的寫入：**不重寫**，改依 #16 §4.2 自該筆首寫推導後續步驟並補齊缺漏（#16 §5.2 白名單第 1 條），並以 §5.2 的退出語意告知操作者。
4. **若不存在** → 取 `max + 1` 為 `state_version`，執行**首次寫入**。寫入失敗或逾時 → 在同一鎖內回到步驟 1（有界重試）。
5. 首次寫入完成後釋放 `L_card`，其餘寫入在鎖外完成。若首次寫入的回應遺失，下一次執行從步驟 0 重來，**必然落到步驟 3**——因為鍵不依賴鏈的狀態。

步驟 5 是整個設計的收斂性論證：**鍵對鏈的狀態不敏感，所以重試必然自我辨識。** §3.2 的鏈尖端方案正是在這一步發散。

呼叫 `ensure_fields` 的四個承接動詞（`review`／`amend`／`handoff`／`assign`，見 §7.1）須在步驟 0 之前、以 `L_project` 單獨完成該前綴並釋放（§2.2）。它**不進事件流、不消耗序號**。

### 5.1.1 回讀契約：本卡只釘最小必要性質，不預設 #16 的形狀

前一版自承的最大缺口是：§7.1.2 要求首寫**攜帶 `event_id`**，但它寫在留言／Log 的**哪個位置**、resume **怎麼解析回來**，本卡沒有定義，而是歸給 #16 §4.2。**#16 目前 ⏸阻塞（等本卡與 #24 落地），於是形成循環**：本卡步驟 3 要機械成立需要回讀契約 → 回讀契約歸 #16 → #16 等本卡。

> **判定：這個循環不是真的。** 它成立的前提是「本卡需要知道**格式**」，但步驟 3 需要的不是格式，是**能力**。本卡可以在不指定任何序列化形式的前提下，把回讀契約必須滿足的性質釘死；#16（或其後繼卡）再選一個滿足它們的表示法。**消費者提需求、生產者選表示**，循環在這個方向上自然斷開。

步驟 3 的機械成立，需要且只需要下列五條。**這是必要條件的列舉，不是充分條件**——滿足五條的表示法不只一種，本卡刻意不從中挑選：

| # | 最小必要性質 | 為什麼是必要的 |
|---|---|---|
| **P1** | **可枚舉**：僅靠讀取該卡遠端狀態，即可列出已寫入的 `event_id` 集合 | 步驟 3 是「在剛重讀的事件流中查找本次的鍵」。查不到就退化成盲寫 |
| **P2** | **唯一歸屬**：一則首寫恰帶一個 `event_id`，一個 `event_id` 恰歸屬一則首寫 | 一對多會讓 §1.2 的「同號同 `event_id`」判準失去意義；多對一則無法定位要補齊哪一串後續步驟 |
| **P3** | **位元組穩定**：GitHub 的儲存與渲染不得改動該位元組（不被 Markdown 吞、不被自動連結改寫、不被截斷） | 鍵是逐位元組比對的。渲染改一個字元，重試就認不出自己——與 §3.2 的鏈尖端是同一類失效，只是成因在載體而非導出式 |
| **P4** | **不觸發既有隔離**：載體不得在留言中引入審核事件 marker 的字面前綴 | `doctor.py:175` `inspect_event_marker` 對該前綴做**全文子字串比對**：首行不是 marker、或首行之外另有該前綴，一律回不合格並停該卡的自動裁決。載體若不慎帶入該字面，會**隔離整張卡**——這是本專案已實證的故障模式，不是假設 |
| **P5** | **可與 payload 分離解析**：能在不解析 payload 語意的前提下取出 `event_id` | §5.4 要求「同鍵但 payload 語意不等 → fail-closed」。若取鍵必須先信任 payload，該判準就無法在 payload 已被竄改時成立 |

**本卡另外指名一條由碼查出的硬約束**，它會直接限制 #16 的選項，因此在這裡先講清楚：

> **既有的審核事件 marker（`v1`）不能直接載 `event_id`。** `templates/handoff-contract.md` §3.1.3 明文：「**鍵集合封閉**：`v1` 只有上列三鍵（`card_id`／`source_sha`／`attempt_id`）。出現任何未定義鍵即依 §3.1.4 處理……**要擴充欄位必須升版本**」，且 `doctor.py:168`–`:171` 的 `_CONFORMANT_MARKER_RE` 以固定順序、單一空白、封閉三鍵的整條 regex 比對，**多一個鍵即不匹配 → 該卡停機**。
>
> 因此「在既有 marker 上加一個 `event_id=` 欄」**不是低成本選項，而是會讓每一張卡當場停機的改動**。要走這條路必須升版本並改契約（紅線 PR）。
>
> 補充射程事實：該 marker 只存在於 **`review`** 的裁決留言；`amend`／`handoff`／`assign`／`deploy-declare`／`deploy-state` 五個動詞的首寫**沒有任何既有 marker 可搭**。回讀契約必須涵蓋六個動詞，不能只解 `review`。

**這一節誠實的殘餘**（不因為釘了性質就消失）：釘住 P1–P5 讓本卡的設計**閉合**（步驟 3 的前提被完整陳述，且可被查核者檢驗），但**不讓實作可以開工**——在有人選定一個滿足 P1–P5 的具體表示法之前，衍生實作卡 A 寫不出解析器。所以循環在**設計層**斷開了，在**排程層**沒有：#16（或接手回讀契約的卡）仍然必須先於實作卡 A 定案。本卡把這件事寫進 §12 的前置欄，不假裝它已經解決。

### 5.2 `already_exists`：可辨識退出碼，零狀態寫入

步驟 3 命中既有事件時，`wfcli` 以**非零但可辨識的退出碼**結束，**不寫入任何狀態**，訊息明指「已存在，視為重試；若確實要再寫一筆請帶 `--new-attempt <標籤>`」。

**退出碼須全域保留，不可沿用既有碼。** 基線 `7451b72` 的退出碼 `0`–`6` 與 `130` 皆已佔用，且**語意逐指令重疊**——`4` 在 `assign` 是資源宣告衝突（`assign_cmd.py:111`）、在 `review` 是拒收（`review_cmd.py:152`）、在 `handoff` 是狀態守衛（`handoff_cmd.py:109`）、在 `deploy-declare` 是前置狀態不符（`deploy_declare_cmd.py:104`）。腳本要區分「真的失敗」與「已經做過了」，就需要一個**跨動詞語意一致**的碼。

> **裁定：保留退出碼 `7` 專用於 `already_exists`，全動詞一致，且不得再賦予其他語意。**

`7` 於基線未被任何指令使用（機械核對：`grep -rn "return [0-9]\+$" cli/src/` 的相異值為 `0 1 2 3 4 5 6 130`）。實作卡須附一個 CI 檢查防止未來有人把 `7` 挪作他用。

### 5.3 `--new-attempt <標籤>`：salt 衝突 fail-loud

`--new-attempt` 是操作者對「這是刻意的新一筆，不是重試」的顯式聲明，取值進入 `attempt_salt`。**其 canonical bytes 與接受集合由 §4.5 定義**——本節只管語意，位元組層的歧義處置在那裡。

**若帶入的標籤與既有事件算出同一 `event_id`**（同卡、同動詞、同參數、**同標籤**）→ **拒絕並要求換標籤**，不得靜默視為重試。理由是操作者已明示要新的一筆，把明示意圖靜默降級為重試，比拒絕更糟——它讓操作者以為寫成功了。

這條 fail-loud 只有在 §4.5 的接受集合成立時才是可靠的：若標籤允許空字串、或允許「靜默剝除變體選擇符／trim 空白」，兩個操作者眼中不同的標籤會摺疊成同一個鍵，於是**系統會把一個顯式的新嘗試回答成 `already_exists`**，而操作者以為自己已經寫成功。§4.5 的收窄是這條規則的前提，不是額外的嚴格。

標籤本身寫入 Log 供稽核：事後必須能回答「為什麼這張卡有兩筆一模一樣的 `handoff`」。

### 5.4 同鍵不同內容 ＝ 竄改或非決定性缺陷

同一 `event_id` 出現兩筆、而 **payload 語意不等**（依 #16 §3.4 的結構化區塊比對，刻意排除 `occurred_at` 與 reviewer 自由文字這類每次都不同的欄位）→ **fail-closed**，純偵測交人。

兩種可能的成因都不能自動修：要嘛有人改了留言（竄改），要嘛 `event_id` 的導出實際上不決定性（實作缺陷）。**自動修復在兩種情況下都會擴大損害**——前者是掩蓋，後者是把缺陷的產物當成事實。

---

## 6. 理論界線：明文記錄，不假裝解決

> **本機零狀態下，「重試」與「刻意重跑同一指令」原則上不可區分。**

要區分兩者，就必須記住上一次做過什麼——而那正是 canonical `:143`／`:165` 封掉、且 #16 §4.1 據以拒絕本機預寫意圖日誌 [WAL] 的本機狀態。**任何宣稱能同時解決兩者的機制，都是把本機狀態藏在別的名字底下。**

因此必須選一邊犧牲：

| 選擇 | 代價 | 代價的性質 |
|---|---|---|
| 保留辨識重試（**已裁定**） | 卡＋動詞＋參數完全相同的第二次寫入被拒絕，即使是合法的刻意重跑 | 操作者多打一個 `--new-attempt` 旗標；**立即可見、可恢復** |
| 保留無聲重跑 | 回應遺失後的重試寫出第二筆事件 | append-only 歷史永久污染，reducer 無從分辨；**延遲發現、不可恢復** |

**需求方裁定：保留辨識重試，犧牲無聲重跑。** 保守側在拒絕這邊——拒絕一筆合法的重複，操作者當場就會知道並帶旗標重來；寫出一筆重複事件，沒有人會當場知道。

### 6.1 兩個明文代價

- **合法重跑須帶旗標**：逃生門是 `--new-attempt <標籤>`，標籤進入 Log，可事後稽核為何需要重複。
- **並行且意圖完全相同的兩個寫入者會被摺疊成一筆**：兩人同卡、同動詞、同參數，算出同一 `event_id`，後者被視為前者的重試而不寫入。這在語意上正確（兩人做同一件事，做一次就夠），但**它不是並行防護**——並行的偵測仍靠 `state_version` 撞號（§2），兩者不可互相取代。

---

## 7. 網路失敗注入測試矩陣

**矩陣在本卡定義，執行歸衍生實作卡**（卡面驗證第 1 條）：本卡資源宣告僅含本設計文件，`open_cmd.py` 等由 [#21](https://github.com/ruan6047/ai-workflow/issues/21) 佔用中。

### 7.1 寫入邊界：由 AST 機械列舉，不由設計者列表

前一版的動詞表是人工讀碼列出的，因此犯了一個**方向性**的錯：它把 `ensure_fields` 描述成「所有寫入動詞共用的**一個**注入點」。兩處都不成立——它不被所有動詞呼叫，也不是一個寫入。人工列表無法被重跑，所以錯誤沒有機械執行者會攔下。**本節改為由 AST 產生列舉，設計文件只登錄判準（哪些 `gh` 子指令算寫入），成員由碼決定。**

```python
"""§7.1 寫入邊界列舉器：由 AST 推導，不由設計者挑選成員。
唯讀靜態分析，不連 GitHub、不寫任何狀態。自 repo root 執行。"""
import ast, pathlib

ROOT = pathlib.Path("cli/src/wf_cli")
# gh 子指令 → 讀/寫。凍結表，無預設格：未登錄的子指令使檢查失敗。
GH_KIND = {
    ("project", "view"): "R", ("project", "field-list"): "R",
    ("project", "item-list"): "R", ("api", "graphql:query"): "R",
    ("project", "field-create"): "W", ("project", "item-create"): "W",
    ("project", "item-add"): "W", ("project", "item-edit"): "W",
    ("issue", "create"): "W", ("issue", "comment"): "W", ("issue", "edit"): "W",
    ("api", "graphql:mutation"): "W",
}

def _const_list(node, assigns):
    """把 execute/run_json 的第一個引數解析成字串前綴；追一層區域變數。"""
    if isinstance(node, ast.Name):
        node = assigns.get(node.id)
    while isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        node = node.left
    if not isinstance(node, ast.List):
        return None
    out = []
    for e in node.elts[:2]:
        if isinstance(e, ast.Constant) and isinstance(e.value, str):
            out.append(e.value)
        else:
            break
    return tuple(out) if len(out) == 2 else None

def scan_func(fn):
    assigns = {}
    for n in ast.walk(fn):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            assigns.setdefault(n.targets[0].id, n.value)
        if isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
            assigns.setdefault(n.target.id, None)
    loops = [n for n in ast.walk(fn) if isinstance(n, (ast.For, ast.While))]
    in_loop = lambda x: any(l.lineno <= x.lineno <= (l.end_lineno or l.lineno) for l in loops)
    hits = []
    for n in ast.walk(fn):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        attr = n.func.attr
        if attr in ("execute", "run_json") and isinstance(n.func.value, ast.Name):
            key = _const_list(n.args[0], assigns) if n.args else None
            hits.append((n.lineno, key or ("UNRESOLVED", attr), in_loop(n)))
        elif attr == "graphql" and isinstance(n.func.value, ast.Name):
            q = n.args[0] if n.args else None
            if isinstance(q, ast.Name):
                q = assigns.get(q.id)
            text = q.value if isinstance(q, ast.Constant) and isinstance(q.value, str) else None
            if text is None:  # query 由分支指派：取該函式全部字串常數
                text = "\n".join(c.value for c in ast.walk(fn)
                                 if isinstance(c, ast.Constant) and isinstance(c.value, str))
            sub = "mutation" if "mutation(" in text or text.strip().startswith("mutation") else "query"
            hits.append((n.lineno, ("api", f"graphql:{sub}"), in_loop(n)))
    return hits

# --- 第一層：project.py 的遠端呼叫盤點 ---
tree = ast.parse((ROOT / "project.py").read_text(encoding="utf-8"))
helpers, unknown, WRITERS = {}, [], {}
for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef)]:
    hits = scan_func(fn)
    if not hits:
        continue
    kinds = []
    for lineno, key, looped in hits:
        k = GH_KIND.get(key)
        if k is None:
            unknown.append((fn.name, lineno, key)); k = "?"
        kinds.append((lineno, key, k, looped))
    helpers[fn.name] = kinds

print("== 第一層：project.py 遠端呼叫（R=讀 W=寫） ==")
for name, kinds in helpers.items():
    w = [k for k in kinds if k[2] == "W"]
    detail = "、".join(f"{k[1][0]} {k[1][1]}@L{k[0]}{'（迴圈內）' if k[3] else ''}" for k in kinds)
    print(f"  {'WRITER' if w else 'reader':6} {name}: {detail}")
    if w:
        WRITERS[name] = (len(w), any(k[3] for k in w))

# --- 第二層：commands/*.py 對 WRITER 的呼叫點 ---
print("\n== 第二層：commands/* 的遠端寫入呼叫點 ==")
total_static = 0
for f in sorted((ROOT / "commands").glob("*.py")):
    if f.name == "__init__.py":
        continue
    t = ast.parse(f.read_text(encoding="utf-8"))
    cmd_loops = [n for n in ast.walk(t) if isinstance(n, (ast.For, ast.While))]
    calls = []
    for n in ast.walk(t):
        if isinstance(n, ast.Call):
            fname = (n.func.attr if isinstance(n.func, ast.Attribute)
                     else n.func.id if isinstance(n.func, ast.Name) else None)
            if fname in WRITERS:
                site_loop = any(l.lineno <= n.lineno <= (l.end_lineno or l.lineno)
                                for l in cmd_loops)
                calls.append((n.lineno, fname, site_loop))
    for lineno, fname, site_loop in sorted(calls):
        cnt, looped = WRITERS[fname]
        bits = []
        if cnt > 1:
            bits.append(f"helper 內 {cnt} 條寫入路徑")
        if looped:
            bits.append("helper 內迴圈：0..N 次")
        if site_loop:
            bits.append("呼叫點在迴圈內：N 次")
        print(f"  {f.stem:22} L{lineno:<5} {fname}{'（' + '；'.join(bits) + '）' if bits else ''}")
    total_static += len(calls)

print(f"\n靜態呼叫點總數 = {total_static}；未登錄 gh 子指令 = {len(unknown)}")
for u in unknown:
    print(f"  未登錄 {u}")
raise SystemExit(1 if unknown else 0)
```

實跑輸出：

```
== 第一層：project.py 遠端呼叫（R=讀 W=寫） ==
  reader resolve_project: project view@L125
  reader list_fields: project field-list@L134
  WRITER ensure_fields: project field-create@L168（迴圈內）
  WRITER create_draft_item: project item-create@L173
  WRITER create_repo_issue: issue create@L184
  WRITER add_issue_comment: issue comment@L199
  WRITER add_item_to_project: project item-add@L205
  WRITER set_field_value: project item-edit@L239
  WRITER update_item_field_value: api graphql:mutation@L293
  WRITER set_item_body: project item-edit@L318、issue edit@L322
  reader list_items: api graphql:query@L367（迴圈內）

== 第二層：commands/* 的遠端寫入呼叫點 ==
  amend_cmd              L229   add_issue_comment
  amend_cmd              L278   ensure_fields（helper 內迴圈：0..N 次）
  amend_cmd              L392   set_field_value
  amend_cmd              L423   set_item_body（helper 內 2 條寫入路徑）
  assign_cmd             L69    ensure_fields（helper 內迴圈：0..N 次）
  assign_cmd             L114   set_field_value
  assign_cmd             L115   set_field_value
  assign_cmd             L116   set_field_value
  assign_cmd             L123   set_item_body（helper 內 2 條寫入路徑）
  deploy_declare_cmd     L122   add_issue_comment
  deploy_declare_cmd     L134   update_item_field_value
  deploy_declare_cmd     L137   update_item_field_value
  deploy_state_cmd       L141   add_issue_comment
  deploy_state_cmd       L156   update_item_field_value
  deploy_state_cmd       L157   update_item_field_value
  deploy_state_cmd       L158   update_item_field_value
  deploy_state_cmd       L159   update_item_field_value
  handoff_cmd            L91    ensure_fields（helper 內迴圈：0..N 次）
  handoff_cmd            L136   set_field_value
  handoff_cmd            L137   set_field_value
  handoff_cmd            L138   set_field_value
  handoff_cmd            L139   set_field_value
  handoff_cmd            L146   set_item_body（helper 內 2 條寫入路徑）
  open_cmd               L133   ensure_fields（helper 內迴圈：0..N 次）
  open_cmd               L148   create_repo_issue
  open_cmd               L149   add_item_to_project
  open_cmd               L152   create_draft_item
  open_cmd               L171   set_field_value（呼叫點在迴圈內：N 次）
  review_cmd             L193   ensure_fields（helper 內迴圈：0..N 次）
  review_cmd             L230   add_issue_comment
  review_cmd             L231   set_field_value
  review_cmd             L242   set_item_body（helper 內 2 條寫入路徑）

靜態呼叫點總數 = 32；未登錄 gh 子指令 = 0
exit=0
```

### 7.1.1 由列舉導出的兩類注入點

輸出把寫入分成兩層，**必須分開建模**——它們的鍵、鎖層級與期望結果都不同：

**A 類：卡層 lifecycle 寫入**（`add_issue_comment`／`set_field_value`／`update_item_field_value`／`set_item_body`）。與 `card_id` 綁定，受 §2.1 卡層臨界區與 `event_id` 管轄。承接的六個動詞的靜態呼叫點：

| 動詞 | A 類呼叫點（行號） | 數 |
|---|---|---|
| `review` | `add_issue_comment`(:230) → 交付狀態(:231) → `set_item_body`(:242) | 3 |
| `amend` | `add_issue_comment`(:229，**`--escalate` 的拒收路徑**，非正常事件序列，見 §7.1.2) → 級別(:392，僅 `--tier`) → `set_item_body`(:423) | 3 |
| `handoff` | owner(:136) → 交付狀態(:137) → 最後交接(:138) → iteration(:139) → `set_item_body`(:146) | 5 |
| `assign` | owner(:114) → 分支worktree(:115) → 交付狀態(:116) → `set_item_body`(:123) | 4 |
| `deploy-declare` | `add_issue_comment`(:122) → 部署狀態(:134) → Status(:137) | 3 |
| `deploy-state` | `add_issue_comment`(:141) → 部署狀態(:156) → Status(:157) → owner(:158) → 最後交接(:159) | 5 |

**A 類共 23 個**，可由列舉輸出直接對帳：靜態點 32 − `open` 的 5 個（`:133`／`:148`／`:149`／`:152`／`:171`，不承接）− 其餘四個 `ensure_fields` 呼叫點（`amend:278`／`assign:69`／`handoff:91`／`review:193`）＝ 23，逐動詞加總 3+3+5+4+3+5 亦為 23。數字與前一版一致；改變的是它現在由腳本產生而非人工列出。

**B 類：專案層欄位建立前綴**（`ensure_fields`）。前一版對它的三項描述**逐項修正**：

| 前一版的宣稱 | 列舉輸出顯示的事實 | 後果 |
|---|---|---|
| 「**所有**寫入動詞共用」 | 呼叫者只有 `amend`(:278)、`assign`(:69)、`handoff`(:91)、`open`(:133)、`review`(:193)。**`deploy-declare` 與 `deploy-state` 不呼叫它**——兩者走唯讀 `list_fields` 並在欄位缺漏時直接失敗（`deploy_declare_cmd.py:79`、`deploy_state_cmd.py:95`） | 「共用前綴」的完整閉包宣稱不成立；deploy-* 的失敗模式與其他四個動詞**不同**（欄位不存在時 deploy-* 直接錯，其他四個會補建），矩陣須分開 |
| 「**一個**注入點」 | `field-create` 在 `for name, ... in FIELD_SPECS.items()` 迴圈內（`project.py:157`–`:168`），**每個缺欄位一次獨立遠端寫入**。`FIELD_SPECS` 於基線有 **13** 個欄位（機械核對：`uv run python -c "import sys;sys.path.insert(0,'cli/src');from wf_cli.project import FIELD_SPECS;print(len(FIELD_SPECS))"` → `13`）→ 每次呼叫 **0–13** 次寫入，各自可獨立失敗 | 「重試應為無操作」只在**全部 13 次都完成**時成立；中途回應遺失會留下部分建立的欄位集合 |
| 「天然冪等」 | 冪等來自 `if name in existing: continue` 的**讀後跳過**，即另一個 read-modify-write。序列重跑下成立；**並行下不成立**——兩個程序可同時讀到「欄位不存在」而各自送出 `field-create` | 需要 §2.2 的 `L_project` 鎖。且該鎖不能是卡層鎖，因為併發的兩張卡屬同一專案 |

另外 `set_item_body` 在 helper 內有**兩條**互斥的寫入路徑（DraftIssue 走 `project item-edit`:318、real issue 走 `issue edit`:322）。單次執行只走一條，故它仍是一個注入點，但**矩陣須覆蓋兩條分支**——只測 real issue 會漏掉 draft item 路徑。

**注入點總計：A 類 23 個 ＋ B 類 `ensure_fields` 的 0–13 次 field-create（四個承接動詞各一次呼叫）＋ `set_item_body` 的 2 條分支。** 不再宣稱一個整數的「全部注入點數」——因為 B 類的次數依專案既有欄位而變，**把可變的次數寫成固定的 24 正是前一版錯的地方**。

### 7.1.2 正確建模 A 類之後浮出來的問題：§2.1 的「首次寫入」對三個動詞尚未成立

§2.1 步驟 5 與 §5.1 步驟 3 都依賴一件事：**臨界區內的那一次寫入必須攜帶 `event_id`**，否則 resume 讀回事件流時找不到它，於是重新取號、重新寫一筆——E1 當場失敗。前一版沒有檢查這個前提，因為它把寫入邊界當成一串沒有差別的注入點。分開建模之後，差別立刻可見：**只有能寫自由形式載荷的寫入才放得下 `event_id`**（timeline 留言與 body Log），單一 Project 欄位值放不下。

```python
"""§7.1.2 首寫載荷能力探針。唯讀靜態分析，不連 GitHub、不寫任何狀態。自 repo root 執行。"""
import ast, pathlib

CMDS = pathlib.Path("cli/src/wf_cli/commands")
# helper → 能否攜帶自由形式載荷（可寫入 event_id 與推導後續步驟所需資訊）。
# 凍結表，無預設格：未登錄的 helper 不會被計入，新增 helper 須同步登錄。
PAYLOAD = {
    "add_issue_comment": True,      # Issue timeline 留言，全文自由
    "set_item_body": True,          # 改 body（Log 行），全文自由
    "set_field_value": False,       # 單一 Project 欄位值
    "update_item_field_value": False,
}
VERBS = {"review_cmd": "review", "amend_cmd": "amend", "handoff_cmd": "handoff",
         "assign_cmd": "assign", "deploy_declare_cmd": "deploy-declare",
         "deploy_state_cmd": "deploy-state"}

print("== A 類寫入依行序（承接的六個動詞）==")
rows = []
for stem, verb in sorted(VERBS.items(), key=lambda kv: kv[1]):
    t = ast.parse((CMDS / f"{stem}.py").read_text(encoding="utf-8"))
    calls = sorted((n.lineno, (n.func.attr if isinstance(n.func, ast.Attribute)
                               else n.func.id if isinstance(n.func, ast.Name) else None))
                   for n in ast.walk(t) if isinstance(n, ast.Call)
                   and (n.func.attr if isinstance(n.func, ast.Attribute)
                        else n.func.id if isinstance(n.func, ast.Name) else None) in PAYLOAD)
    print(f"  {verb:15} " + "、".join(
        f"{f}@L{l}{'[載荷]' if PAYLOAD[f] else '[裸欄位]'}" for l, f in calls))
    rows.append((verb, calls[0]))

print("\n== 行序首寫是否具載荷能力 ==")
for verb, (l, f) in rows:
    print(f"  {verb:15} 行序首寫 = {f}@L{l} → {'載荷' if PAYLOAD[f] else '裸欄位'}")
print("\n注意：行序 ≠ 執行序（條件分支與提前返回會改變實際首寫），"
      "本探針只機械判定 helper 的載荷能力；實際首寫須逐動詞讀路徑確認。")
```

實跑輸出：

```
== A 類寫入依行序（承接的六個動詞）==
  amend           add_issue_comment@L229[載荷]、set_field_value@L392[裸欄位]、set_item_body@L423[載荷]
  assign          set_field_value@L114[裸欄位]、set_field_value@L115[裸欄位]、set_field_value@L116[裸欄位]、set_item_body@L123[載荷]
  deploy-declare  add_issue_comment@L122[載荷]、update_item_field_value@L134[裸欄位]、update_item_field_value@L137[裸欄位]
  deploy-state    add_issue_comment@L141[載荷]、update_item_field_value@L156[裸欄位]、update_item_field_value@L157[裸欄位]、update_item_field_value@L158[裸欄位]、update_item_field_value@L159[裸欄位]
  handoff         set_field_value@L136[裸欄位]、set_field_value@L137[裸欄位]、set_field_value@L138[裸欄位]、set_field_value@L139[裸欄位]、set_item_body@L146[載荷]
  review          add_issue_comment@L230[載荷]、set_field_value@L231[裸欄位]、set_item_body@L242[載荷]

== 行序首寫是否具載荷能力 ==
  amend           行序首寫 = add_issue_comment@L229 → 載荷
  assign          行序首寫 = set_field_value@L114 → 裸欄位
  deploy-declare  行序首寫 = add_issue_comment@L122 → 載荷
  deploy-state    行序首寫 = add_issue_comment@L141 → 載荷
  handoff         行序首寫 = set_field_value@L136 → 裸欄位
  review          行序首寫 = add_issue_comment@L230 → 載荷
```

**探針的界線要照它自己印的那句話讀**：行序不是執行序。因此逐動詞讀路徑確認，得到的實際首寫如下（`amend` 的行序結果就是被條件分支推翻的那一格）：

| 動詞 | 實際首寫 | 具載荷 | 依據 |
|---|---|---|---|
| `review` | `add_issue_comment`(:230) | ✅ | 無前置分支；碼內註解已寫明「先留言、後翻狀態」的理由 |
| `deploy-declare` | `add_issue_comment`(:122) | ✅ | 無前置分支 |
| `deploy-state` | `add_issue_comment`(:141) | ✅ | 無前置分支 |
| `amend`（無 `--tier`） | `set_item_body`(:423) | ✅ | :229 的留言在 `--escalate` 的**拒收路徑**上（版面損壞 → 留言後 `return 2`），**不在正常事件寫入序列內**；:392 需 `--tier` |
| `amend --tier` | `set_field_value`(級別, :392) | ❌ | :392 在 :423 之前無條件執行；碼內註解自承「欄位成功、body 失敗」的不一致，靠下一次 amend 的 `_tier_change_logged` 自癒 |
| `handoff` | `set_field_value`(owner, :136) | ❌ | 四個欄位寫在 `set_item_body`(:146) 之前 |
| `assign` | `set_field_value`(owner, :114) | ❌ | 三個欄位寫在 `set_item_body`(:123) 之前 |

前三列與 #16 §4.3 的既有稽核一致；`deploy-declare`／`deploy-state` 在 #16 §4.3 明列為**未稽核**，本節補上（兩者皆合格）。

**`amend --tier` 這一格與 #16 §4.3 直接衝突，且本卡這側才是對的**（本輪逐條核對 #16 原文後更正的說法——前一版只寫「#16 未區分 `--tier` 分支」，低估了落差）：

- #16 §4.3 把 `amend` 的遠端寫入順序記為「**body Log → 級別欄（僅需要時）**」，據此判**合格**。
- 實際順序相反：`set_field_value`(級別) 在 `:392`、`set_item_body` 在 `:423`，**欄位先於 body**。碼內註解自己寫明了理由：「級別先寫並讀回驗證，body 後寫。這個順序讓『欄位寫失敗』變成乾淨中止……而『欄位成功、body 失敗』留下的不一致，由下一次同樣的 amend 依 `_tier_change_logged` 偵測並只補寫 Log 自癒。」

因此 #16 §4.3 對 `amend` 的「合格」**只在無 `--tier` 的路徑上成立**；`--tier` 路徑的首寫是裸欄位，不自描述。這不是本卡與 #16 的用詞差異，是一個**可由碼機械判定的事實落差**，#16 若要維持該表的「列舉閉包」宣稱應同步更正。本卡不代改 #16，只在此指名。

> **裁定：§2.1 步驟 5 的「首次寫入」定義為「該動詞第一次攜帶 `event_id` 的寫入」，而非「第一次遠端寫入」。實作卡必須把該寫入**排到動詞的最前面**；在排序完成前，`handoff`、`assign`、`amend --tier` **不得宣稱通過 E1**。

不排序而想別的辦法補救，兩條路都是封的：把 `event_id` 塞進 Project 欄位，等於新增 canonical `:141` 之外的欄位（§11 明列不做）；在本機記住「我已經寫了哪些欄位」，就是 canonical `:143`／`:165` 封掉的意圖日誌（§6）。**排序是唯一不牴觸既有紅線的解**，而它便宜——三個動詞各動一次寫入順序。

排序的副作用要一併說明：`handoff`／`assign` 改成 body Log 先寫，會讓「Log 已記、欄位未改」成為新的半寫入形狀（現況是反過來）。這個方向是對的——**Log 有記載的半寫入可以被 resume 補齊，欄位改了但無人知道的半寫入不行**。`amend --tier` 現有的 `_tier_change_logged` 自癒是同一個問題的單點解，排序後應由通用的 resume 路徑取代，實作卡須確認移除後行為不退化。

### 7.2 A 類矩陣：每個注入點 × 三項期望

對 §7.1.1 A 類的每一個注入點，注入「**請求送達 GitHub 且寫入成功，但回應遺失**」，重跑後逐項檢查：

| # | 期望 | 失敗即代表 |
|---|---|---|
| E1 | **不得產生第二筆事件** | `event_id` 導出不決定性，或用了鏈尖端（§3.2） |
| E2 | **不得判為撞號** | §1.2「同號同 `event_id` 不是撞號」未實作，該卡被誤降級 |
| E3 | **能正確補齊後續步驟** | 首寫自描述性不成立（#16 §4.3），或 resume 步驟 3 的推導有缺 |

覆蓋必須是 A 類 23 個注入點全部（`set_item_body` 的兩條分支各算一次），不得抽樣。合成 mock 可用於此項——**故障注入本來就無法用真實 timeline 取得**，這是方法論上的必要讓步，不是取巧。

> **一項紀律，來自 #17 的教訓**：合成 fixture 全綠不代表真卡安全（#17 的驗證當時真卡上已存在會觸發停機的留言，合成探針漏抓，遲至 #20 才發現）。因此除故障注入外，實作卡另須對**至少一張真卡**跑一次 `event_id` 導出並比對既有事件，確認導出結果與實際歷史一致。

### 7.2.1 B 類矩陣：`ensure_fields` 的期望與 A 類不同

| # | 情境 | 期望 |
|---|---|---|
| F1 | 單一 `field-create` 成功但回應遺失，重跑 | 該欄位**不得重複建立**；重跑為無操作，不得因欄位已存在而失敗 |
| F2 | 迴圈中途回應遺失（13 個欄位建到第 k 個），重跑 | 補齊剩餘 `13-k` 個，**不重建已建的 k 個** |
| F3 | 任何 `field-create` 失敗或部分完成 | **不得消耗 `state_version`、不得產生 lifecycle 事件**（B 類完全不進事件流） |
| F4 | 同專案**兩張不同卡**的兩個程序同時執行 | 依 §2.2 由 `L_project` 序列化；**不得出現同名重複欄位**。無鎖實作在此項必紅——這是 `L_project` 存在的驗收 |
| F5 | `deploy-declare`／`deploy-state` 在欄位缺漏的專案上執行 | **維持現行的直接失敗**（`deploy_declare_cmd.py:79`／`deploy_state_cmd.py:95`），不得為了「一致」而給它們加上補建行為——那會讓部署動詞取得改專案 schema 的權限，屬射程外的擴權 |

### 7.3 emoji 枚舉專項（卡面驗證第 2 條）

獨立列項，因為 §4.3 已證實它會被天真實作漏掉：

| # | 案例 | 期望 |
|---|---|---|
| M1 | 交付狀態值含 `U+FE0F`（如 `🚧進行中` 後綴變體選擇符） | **拒收**，非正規化後接受 |
| M2 | 交付狀態值含 `U+FE0E` | **拒收** |
| M3 | 交付狀態值含零寬字元（`U+200B`／`U+200D`／`U+FEFF`） | **拒收** |
| M4 | 同一狀態值分別來自插入變體選擇符與不插入的兩種終端 | 兩者**不得產生不同 `event_id`**（M1–M3 拒收後自然成立，但須有獨立測試防止未來改以「靜默剝除」實作） |
| M5 | `handoff --status`、`assign --status`、`amend --db-scope` 三個**無 `choices` 宣告**的旗標 | 同樣套 M1–M4，**證明分類鍵是目的地欄位而非 argparse 宣告**（§4.3） |

**M5 是本卡對 #22 缺陷模式的直接防護**：M1–M4 若只對「宣告了 `choices` 的旗標」測，會全綠通過，而實際暴露面完全沒被覆蓋。

### 7.3.1 嘗試標籤專項（§4.5）

| # | 案例 | 期望 |
|---|---|---|
| S1 | `--new-attempt ""` | **拒收**。接受即與「缺席」同鍵，把顯式新一筆靜默降級為重試（§4.5） |
| S2 | 標籤含非 ASCII（CJK、NFC 與 NFD 兩種寫法的 `café`） | **拒收**，且訊息指出合法字元類；**不得靜默正規化或剝除** |
| S3 | 標籤含 `U+FE0E`／`U+FE0F`／零寬／BOM | **拒收** |
| S4 | 標籤含前後空白、內部空白、`\n`、`\r\n` | **拒收**；**不得 trim 後接受** |
| S5 | 長度 64 接受、65 拒收；首字元非英數拒收 | 邊界值逐一測 |
| S6 | 同卡同動詞同參數、**同標籤**再跑一次 | `already_exists`（退出碼 `7`），且**訊息須明指要換標籤**，不得只說「已存在」（§5.3） |
| S7 | 缺席 vs 任一合法標籤、任兩個相異合法標籤 | **不得同鍵**（§4.5 碰撞測試的 CI 版） |

### 7.3.2 並行與鎖專項（§2）

前一版沒有並行測試，於是 §2 的「可預防」只是文件裡的一句話。以下六項是該宣稱的驗收：

| # | 案例 | 期望 |
|---|---|---|
| C1 | **同機兩程序、同一卡、意圖完全相同**，同時啟動 | 恰好一筆事件落地；另一程序 `already_exists`（退出碼 `7`）。**這是 §2.1 固定臨界區的直接驗收**——把步驟 1–3 移到鎖外的實作在此項必紅 |
| C2 | 同機兩程序、同一卡、**意圖不同**（如 `handoff` 與 `amend`），同時啟動 | 兩筆事件皆落地，序號相異且連續，**不得撞號** |
| C3 | 持鎖程序在首寫**送出後、回應前**被 `SIGKILL`；另一程序隨後執行 | 依 §2.3 證明死亡後回收，回收者照 §2.1 完整重跑 → 命中既有 `event_id` → `already_exists`，**不得寫出第二筆** |
| C4 | 持鎖程序被 `SIGSTOP`（存活但無進展）超過 TTL；另一程序嘗試回收 | **不得奪鎖**（pid 仍存在且啟動時刻相符）→ 等待或 fail-closed。**只用 TTL 的實作在此項必紅**——這是 §2.3 裁定的驗收 |
| C5 | 鎖 metadata 標示的主機／開機識別與當前不符 | **fail-closed**，不回收、不寫入，交人 |
| C6 | 鎖目錄含白名單以外的欄位 | **失敗**（§2.3 末段：鎖不得長成意圖日誌） |

### 7.4 執行歸屬

| 項目 | 承接 |
|---|---|
| §7.2 的 A 類 23 注入點 × E1–E3 | 衍生實作卡（`cli/` 資源，須待 #21 釋放） |
| §7.2.1 的 F1–F5 | 同上 |
| §7.3 的 M1–M5、§7.3.1 的 S1–S7、§7.3.2 的 C1–C6 | 同上 |
| §7.1.2 的寫入順序調整（`handoff`／`assign`／`amend --tier` 的自描述寫入排到最前） | 同上，**且是 E1 的前置** |
| §4.4 的分類器 CI 檢查（`base` ＋ `inject` 兩模式） | 同上 |
| §7.1 的寫入邊界列舉器 CI 檢查（新增未登錄 `gh` 子指令即紅） | 同上 |
| §7.1.2 的首寫載荷探針 CI 檢查（自描述寫入不在最前即紅） | 同上 |
| 退出碼 `7` 的佔用防護檢查 | 同上 |

---

## 8. 明示不承接 `open`

**本卡不涵蓋 `open`，且不宣稱任何機制能解決它。**

`open` 是唯一會**建立**遠端物件的動詞（`open_cmd.py:148` `create_repo_issue` → `:149` `add_item_to_project` → `:171` 逐欄寫入）。`create_repo_issue` 成功但回應遺失時：

- CLI 手上**沒有任何 Issue URL 或 number**，無從回頭讀既有事件流；
- `event_id` 的材料裡 `card_id` 是使用者給的，**無法反向定位那張已建立的 Issue**。

**`event_id` 只有在已能找到該 Issue 的事件之後才可比對，它解決不了「找不到」這一步。** #16 前一版曾把 `open` 指派給本卡的決定性 `event_id`，該處置**已判定不成立並撤回**（#16 R12-004、§4.3）。

若日後要解，需要的是一套 **discover-before-create**：由決定性材料導出一個可全域搜尋且唯一的 remote locator、先查後建、同鍵多筆 fail-closed，並附 create-success／response-lost 的失敗注入。**那是尚未被裁定的新設計，不是本卡可以順手承接的東西。**

`open` 的半寫入（Issue 已建但欄位未寫完）現況仍只能偵測、交人（#16 §4.5），且沒有預定的解決時程。

---

## 9. 與 canonical 的相容性核對

逐條核對，確認本設計**補完**而非**取代**既有權威：

| canonical 條文 | 本設計的關係 |
|---|---|
| `AI_WORKFLOW.md:141` 最小 schema 含 `event_id`、`state_version`，同卡 `state_version` 單調遞增 | **沿用，未改 schema**。本檔只補取號程序（§1）、異常處置（§1.2）與 `event_id` 的導出方式（§3）。欄位集合不變、欄位名不變 |
| `AI_WORKFLOW.md:141` `occurred_at` 須取寫入當下系統時鐘 | **不牴觸**。冪等鍵不取時鐘（§3.3），`occurred_at` 照原規則獨立寫入；排序用 `state_version` 而非時戳 |
| `AI_WORKFLOW.md:148` 本機可採原子目錄鎖；跨主機須具併發控制的服務 | **照該界線分層**（§2），且明示跨主機不可預防、只能偵測。§2.2 的兩個鎖層級仍都是本機目錄鎖，未引入新的協調服務。未宣稱超出 canonical 授權的保證 |
| `AI_WORKFLOW.md:143`／`:165` 本機檔案不得暫代狀態 | **遵守**。鎖不持有 lifecycle 狀態；§2.3 的存活性 metadata 有明文劃界（只能回答「持有者是否存活」，resume 不得讀它），並以封閉白名單防止它長成意圖日誌。resume 純讀 GitHub（§5.1）。#16 §4.1 的 WAL 拒絕理由本檔不重述 |
| `AI_WORKFLOW.md:139` remote coordination adapter 是唯一 lifecycle event writer | **不變**。本設計不新增 writer，只規範既有 writer 的取號與重試行為 |
| `FIELD_SPECS`（`project.py:28`）為凍結欄位 schema | **引用為枚舉的權威來源**（§4.1），不自訂枚舉清單。§4.3 的裁定是「以該表為分類鍵」，強化而非覆蓋它 |
| `handoff-contract.md:16` `event_id` 寫為 `<UUID>` | **需修訂**：UUIDv5 仍是合法 UUID，格式相容，但「隨機」的隱含語意須改為「由 §3.3 決定性導出」。此為契約修訂，走紅線 PR |
| `handoff-contract.md` §3.1.3 審核事件 marker `v1`：**鍵集合封閉**，「要擴充欄位必須升版本」 | **遵守，且據以排除一個選項**（§5.1.1）：`event_id` **不得**以加欄方式搭上 `v1` marker——`doctor.py:168`–`:171` 的整條 regex 多一鍵即不匹配，後果是該卡停機。若回讀契約選擇走 marker，須升版本並改契約（實作卡 D）。本卡不選定表示法，只排除這條會靜默傷卡的捷徑 |

**需要契約修訂的是最後兩列**，其餘皆為補完。第二列是**排除性結論**（指出一條不能走的路），不是本卡要求的修訂——是否真的要升版本，取決於回讀契約最後選了哪種表示法。

---

## 10. 對 #24 的相依：假設已判定，相依已解除

前一版把路徑型別的正規化交給 [#24](https://github.com/ruan6047/ai-workflow/issues/24)（`WF-RESOURCE-WRITESET1`），並把 A1–A4 四項列為**待驗假設**，明寫「刻意不對齊，讓差異在查核時暴露」。

**兩張卡都已交付，假設可判定了。逐項結案：**

| # | 前一版的假設 | 判定 | 依據 |
|---|---|---|---|
| A1 | #24 的路徑正規化對無法解析者 fail-closed | **已成立但不再相關** | #24 §8.7 已裁定 fail-closed。但本卡不再引用該正規化，故此假設對本卡失效 |
| A2 | #24 的輸出是位元組決定性、可當 canonical bytes | **不成立** | #24 §2.1 的 `K(r)` 是 **casefold 後的分量 tuple**，供**相交判定**用；它刻意摺疊大小寫與尾斜線（§2.3-2、§3.1-7），**摺疊過的鍵不能反推位元組**，故不可當 canonical bytes 來源 |
| A3 | #24 的 namespace 涵蓋本卡的七個路徑參數 | **不成立** | #24 §3.1 規則 2／3 拒收 `/` 與 `~` 起始、規則 4 拒收 `..` 分量。CLI 引數實務上多為絕對路徑，會被整批拒收 |
| A4 | 兩卡各自獨立、本輪不對齊 | **已達成目的，可撤回** | 差異確實暴露了，且兩側收斂到同一個解（見下） |

**兩側的分歧與其收斂，記錄於此**：#24 的查核者從其側裁定「兩者本來就是不同輸入域，#24 應在文件明示不涵蓋 CLI 引數」，並判定那**不構成 #24 本輪的 blocking finding**；本卡的查核者則從本側判為 major blocking。**修法方向兩側一致**——#24 §3.1 已加上定義域界線告示框並把引數正規化回指本卡，本卡則撤除該引用。分歧只在「誰記為 blocking」，而那不影響任何一份設計的內容。前一版「刻意不對齊」的做法在這一格是有效的：它讓一個真實的介面錯配在兩側同時被看見，而不是被兩邊各自的猜測填平。

> **裁定：本卡與 #24 之間，`event_id` 位元組來源方向的相依**已解除**。** §4.1b 已證明承接的六個動詞裡沒有任何引數需要檔案系統路徑正規化，故本卡不引用 #24 的任何正規化產物，也不自訂替代品。

**這不代表兩卡無關**：#24 的資源宣告互斥語意仍然是 `assign` 能不能派工的前置（`assign_cmd.py:91` 的交集檢查），本卡的 §2.2 `L_project` 與 #24 的宣告互斥也解決不同層次的問題（前者是同機程序互斥，後者是卡與卡的資源互斥）。解除的只是**路徑正規化這一條介面**。

**§4.2 的降級路徑仍然保留且仍然是本卡自己的**：未來若有新引數真的需要檔案系統正規化（今天沒有），它落回「無規範化定義 → 該動詞退出冪等保護 → stderr 明示」。這條路徑不依賴任何外部卡。

---

## 11. 非目標與殘餘限制

- **不做跨主機並行預防**：無可用併發控制服務，只偵測（§2）。宣稱能預防即是假保證。
- **不承接 `open` 的冪等性**（§8）。
- **不改 lifecycle event 的欄位集合**：schema 是 canonical `:141` 的，本卡只定義既有欄位怎麼取值。
- **不處理 legacy 前綴的追溯**：以 `epoch-anchor` 劃界（#16 §10.2），錨點前事件不重新編號（§1.2）。**未錨定的卡整條序列都無序號**，本卡對它不報缺號，但它也拿不到自動修復——`epoch-anchor` 僅適用 quiescent 卡且「已錨定張數不保證收斂」（#16 §10.2／§10.4），本卡不改變該結論。
- **`--status`／`--db-scope` 缺 `choices` 驗證**：本卡以「分類鍵＝目的地欄位」使其不影響冪等鍵正確性（§4.3），但**旗標本身的輸入驗證仍缺**，屬實作卡範圍。
- **殘留鎖的 TTL 具體值歸實作卡**：§2.3 已把**安全規則**釘死（不得僅以 TTL 奪鎖、只能在可證明死亡時回收、無法判定即 fail-closed、逃生門必須人工）。留給實作卡的只有「多久之後開始做死亡判定」這個數值，它調錯只影響等待時間，不影響正確性。
- **`ensure_fields` 的部分完成狀態不被本卡消除**：§7.2.1 F2 只要求重跑能補齊，**不要求 13 個欄位的建立是原子的**——GitHub 沒有提供批次建立欄位的原子 API，宣稱原子即是假保證。
- **`L_project` 只保護同機**：與 `L_card` 同一條 canonical 界線（`:148`），跨主機的兩個程序仍可能建出同名重複欄位，只能事後偵測。
- **對 #24 的路徑正規化相依已解除**（§10）：本卡不再引用其封閉 namespace，也不自訂替代品——§4.1b 已證明承接的六個動詞裡沒有引數需要檔案系統路徑正規化。**未來若出現需要的新引數，它落 §4.2 降級路徑**（該動詞退出冪等保護＋stderr 明示），本卡今天不預先為它定義正規化。
- **`--worktree` 以字面字串入鍵，不折疊路徑拼法**：`/a/b` 與 `/a/b/`、絕對與相對、symlink 與實體路徑算出不同的鍵（§4.1b）。這在語意上正確（它們寫進 `分支worktree` 欄位的值本來就不同），但殘餘曝險是**操作者在重試時改寫拼法會寫出第二筆事件**。這不是路徑特有的（任一引數改動都會改鍵，§6 已裁定），只是路徑的「同一個東西的不同拼法」表面比其他型別寬，故單獨列出。
- **回讀契約只釘性質、未定形式**（§5.1.1）：本卡釘死 P1–P5 五條最小必要性質，並指名一條硬約束（既有審核事件 marker 的 `v1` 鍵集合封閉，載 `event_id` 須升版本＋改契約），但**不選定表示法**。設計層閉合，排程層未解——實作卡 A 仍須等回讀契約定案。
- **`handoff`／`assign`／`amend --tier` 的首寫尚不自描述**：本卡給出裁定與驗收（§7.1.2），但排序本身是 `cli/` 的變更，歸實作卡 A′。**在它落地前，這三個動詞的 E1 不成立**——本檔不宣稱本設計已使全部六個承接動詞冪等，只宣稱設計完備且缺口已被指名。

---

## 12. 衍生實作卡（建議）

| 卡 | 內容 | 前置 |
|---|---|---|
| **A** | `event_id` 決定性導出（含 §3.3 的**解析後** `target` 三元組）＋ §4 型別正規化（含 §4.5 嘗試標籤驗證器）＋ §4.4 分類器 CI（`base`＋`inject` 兩模式，四個負向測試一併釘住） | #21 釋放 `cli/`；**且回讀契約（§5.1.1 P1–P5）已定案** |
| **A′** | §7.1.2 的寫入順序調整（`handoff`／`assign`／`amend --tier`）＋ 首寫載荷探針 CI | 可與 A 併行，**是 E1 的前置** |
| **B** | §2.1 固定臨界區 ＋ §2.2 兩個鎖層級 ＋ §2.3 死亡證明式回收 ＋ §1.2 五情形判準 ＋ 退出碼 `7` | A |
| **C** | §7.2 A 類 23 注入點 × E1–E3 ＋ §7.2.1 F1–F5 ＋ §7.3 M1–M5 ＋ §7.3.1 S1–S7 ＋ §7.3.2 C1–C6 ＋ §7.1／§7.1.2 列舉器與探針 CI | A、A′、B |
| **D** | `handoff-contract.md` 的 `event_id` 語意修訂（契約，紅線 PR）。**若回讀契約選擇搭既有審核事件 marker，另須升版本**——`v1` 鍵集合封閉，加欄即停機（§5.1.1） | A |

C 是驗收閘門：**A、A′、B 未通過 C 不得宣稱冪等性成立。** 其中 C1（同機同意圖並行）與 C4（`SIGSTOP` 不得被奪鎖）是 §2 兩條裁定各自的唯一驗收，缺任一項即 §2 的「可預防」退回文件宣稱；A′ 未完成則 `handoff`／`assign`／`amend --tier` 的 E1 不成立（§7.1.2）。

**排程上的真前置**（§5.1.1）：回讀契約的**表示法**目前無卡承接——#16 ⏸阻塞，本卡只釘性質不選形式。**A 在它定案前寫不出解析器。** 這一格是本輪未關掉的洞，明列於此而非藏在前置欄裡。
