# WF-EVENT-IDEMPOTENCY1：lifecycle 事件的排序與冪等

> 卡：[ai-workflow#23](https://github.com/ruan6047/ai-workflow/issues/23)　基線：`origin/main` `7451b72ba7679893043950d71bad9642665e25da`
>
> spec 基線內容＝[#16](https://github.com/ruan6047/ai-workflow/issues/16) 設計文件 §3.1 於 SHA `2d361303ce438c6fecf475b2aaa1fcbc06518dc9` 的狀態（已歷 R5／R6／R7 三輪跨家族查核）。需求方 2026-08-11 裁定縮小 #16 射程後，機制本體歸本卡。
>
> 本檔是**設計與契約**，不含實作。所有可執行變更由衍生實作卡承接（§9）；本卡資源宣告僅含本檔，`cli/` 由 [#21](https://github.com/ruan6047/ai-workflow/issues/21) 佔用中。

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
| **無序號** | 事件不帶 `state_version` 欄位 | legacy epoch，以 `contract-baseline` 劃界（#16 §10），**不追溯**、不視為缺號 |

**「同號同 `event_id` 不是撞號」是本卡最重要的一條，也是最容易實作錯的一條。** 天真的實作會把「序號 N 已被佔用」直接當成撞號，於是每一次「寫入成功但回應遺失」後的重試都會把該卡永久降級——防護機制反而成為最主要的故障來源。降級是不可逆的懲罰，代價與防護必須對稱。

> **為什麼 legacy 無序號不算缺號**：缺號的語意是「這條序列本來該有這一號」。legacy epoch 的事件從來不在同一條序列上，把它們算進去會讓每一張跨 cutover 的卡在第一次檢查時就全部降級。劃界的機制不是本卡新增的，見 #16 §10.2 的 `contract-baseline` 錨定。

---

## 2. 撞號的並行防護：兩層，且不宣稱超出各層能力

**紀律不是機制。** 任兩個 resume 或人工作業即可撞號，而撞號的後果是該卡永久降級。靠「請勿同時操作」防護等於沒有防護——canonical `AI_WORKFLOW.md:148` 已明文把這句話排除在鎖的定義之外。

canonical 同行給出可用的一層：「本機可採**原子目錄鎖**；跨主機必須使用具併發控制的服務或 workflow。」照這條界線分兩層：

| 併發來源 | 機制 | 保證強度 |
|---|---|---|
| 同機多個 `wfcli` 程序（含 resume 與人工並行） | 以 `(owner, project, card_id)` 為鍵的**本機原子目錄鎖**，包住「讀最大序號 → 重讀確認 → 寫首寫」整段 | **可預防**。canonical 明文允許，且它是鎖不是狀態面 |
| 跨主機 | 無可用的併發控制服務 | **不可預防**。取號後、寫入前重讀比對以縮窗，撞號 fail-closed |

**鎖的鍵必須是 `(owner, project, card_id)` 三元組**，不是 `card_id` 單獨。卡 ID 在跨 repo 的 user-level Project 聚合下不保證唯一（canonical `:162` 明示 user-level Project 跨 repo 聚合即多專案面板），單以 `card_id` 為鍵會讓兩張不同專案的同名卡互相阻塞。

**鎖不持有任何狀態。** 它只保護「讀→寫」這段臨界區，不儲存意圖、不記錄進度。這一點必須明確，否則本機鎖會偷偷變成 §5 明文拒絕的本機狀態，違反 canonical `:143`／`:165`（#16 §4.1 已詳述該推理，本檔不重述）。鎖目錄 runtime 必須 `.gitignore`，且**崩潰後的殘留鎖必須可由後續程序判定失效並回收**——否則一次崩潰會讓該卡永久卡死，這與撞號降級是同一種不對稱代價。

> **誠實界線**：跨主機撞號仍只能偵測，不能預防。這與 `wfcli amend` 現行的「重讀比對縮窗、不宣稱 CAS」（`amend_cmd.py:411` 的註解已自承殘餘競態視窗）是同一誠實等級。**但同機這一層已從紀律升格為機制**，而實測中 resume 與人工並行都落在這一層。

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
event_id = uuid5(NS_WFCLI, canonical(owner, project, card_id, verb, args, attempt_salt))
```

- `NS_WFCLI`：固定的 UUID namespace 常數，凍結於實作，變更即等同全體事件重新編號。
- `args`：該動詞的全部使用者輸入，依 §4 逐欄位型別正規化後，以「欄位名 ‖ 長度 ‖ 位元組」串接。**長度前綴不可省**——沒有它，`(a="x", b="yz")` 與 `(a="xy", b="z")` 會串出相同位元組。
- `attempt_salt`：**預設空字串**；僅在操作者顯式帶 `--new-attempt <標籤>` 時取該標籤（§5.3）。
- **不含鏈尖端、不含時鐘、不含 `state_version`。**

欄位名本身也進入串接，且欄位須**依欄位名排序**後串接——否則 CLI 內部參數順序的重構會靜默改變所有既有事件的鍵。

---

## 4. `args` 的 canonical bytes：逐型別，全函數

「NFC ＋ 長度前綴」不足以定義所有欄位的規範位元組：換行、尾隨空白、結構化資料與 emoji 枚舉各有各的歧義來源。逐型別定義，**不留「其餘」格**。

### 4.1 六個型別

| 型別 | 規範化 | 歧義來源 |
|---|---|---|
| **自由文字**（`--evidence`、`--reason`、`--actor`、查核報告） | Unicode **NFC**；行尾一律 `LF`；去除每行尾隨空白與整體尾隨換行 | CRLF、貼上時的尾白、輸入法產生的 NFD |
| **枚舉**（交付狀態、部署狀態、級別、`db_scope`、`next-stage`、`decision`） | **逐位元組取自 `FIELD_SPECS` 的凍結字串**；輸入含 **variation selector**（`U+FE0E`／`U+FE0F`）或零寬字元（`U+200B`–`U+200D`、`U+FEFF`）者**拒收** | 狀態值本身是 emoji，終端與輸入法會插入變體選擇符 |
| **路徑**（`--worktree`、`--repo-path`、`--input`、`--config`、`--out-dir`、`--spec-dir`、`repo_root`） | #16 §7.2 →〔歸 [#24](https://github.com/ruan6047/ai-workflow/issues/24)〕的封閉 namespace 正規化 | 相對／絕對、symlink、尾斜線 |
| **SHA／識別碼**（`--source-sha`、`card_id`、`--repo`、`--owner`、`--branch`） | 小寫 hex 且長度固定（SHA）；識別碼逐位元組比對，不做大小寫摺疊 | 大小寫、短 SHA |
| **整數／布林**（`--iteration`、`--escalation-epoch`、`--project`、各 `--dry-run` 類旗標） | 十進位無前導零／`true`\|`false` | 空白、`True`、`+1`、前導零 |
| **結構化輸入**（`--acceptance`、`--verification`、`--resources`、findings 區塊） | 先解析為資料結構，再以**排序鍵、無註解、無錨點**的規範形式序列化；**不對原始文字取雜湊** | 縮排、鍵序、註解、YAML 別名 |

### 4.2 沒有「其餘」格，靠的是 fail-closed 收尾規則

上表是**閉包**，不是常見情形的列舉。使其成立的是這條規則：

> **任何無法歸入上表六型別的新欄位，在其型別規範化定義補上之前，該動詞不得納入冪等鍵機制。**

這條規則讓分類成為全函數：新欄位不是落進某個沉默的預設格，而是**擋下整個動詞**。代價是新增欄位時會踩到明顯的阻擋，這是刻意的——沉默的預設格正是 #22 在自己新增的表格上漏掉一整格的成因，而漏掉的那格不會有人發現，直到它產生錯誤的鍵。

**「不得納入冪等鍵機制」的具體語意**：該動詞退回無冪等保護的狀態（即今日行為），**而非拒絕執行**。它必須在 stderr 明示「本動詞因欄位 X 無規範化定義而未受冪等保護，重試可能產生重複事件」。fail-closed 指的是不對未定義輸入計算鍵，不是把 CLI 鎖死。

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

「六型別涵蓋全部輸入」是可以被機械檢查的宣稱，因此本節給出檢查方法而非斷言。分類器對 `wfcli` 全部子指令的參數面求值，**任何未分類的參數即為失敗**：

**關鍵設計**：分類器**不得有沉默的預設格**。「未登錄的旗標一律當自由文字」這種寫法會讓檢查變成恆真——那正是本節要防的缺陷，寫在檢查器自己身上。因此每個型別都是**顯式登錄集**，落在全部集合之外者回傳 `None` 並使檢查失敗。

```python
"""§4.4 分類器：無沉默預設格。未登錄的參數即未分類 → 失敗。
唯讀 argparse 內省，不連 GitHub、不寫任何狀態。自 repo root 執行。"""
import argparse, sys
sys.path.insert(0, "cli/src")
from wf_cli.cli import build_parser

PATH = {"--worktree", "--repo-path", "--config", "--input",
        "--out-dir", "--spec-dir", "repo_root"}
SHA = {"--source-sha"}
IDENT = {"card_id", "--repo", "--owner", "--card-id", "--main-ref", "--branch"}
STRUCT = {"--acceptance", "--verification", "--resources"}
FREETEXT = {"--evidence", "--reason", "--actor", "--reviewer", "--assignee",
            "--to", "--next-owner", "--feature", "--core-pain", "--service-goal",
            "--initiative", "--requested-by", "--planned-by", "--executor",
            "--spec-baseline"}
# §4.3：argparse 宣告不足以決定型別者——直接寫入 FIELD_SPECS SINGLE_SELECT 欄位。
DEST_ENUM = {("handoff", "--status"), ("assign", "--status"), ("amend", "--db-scope")}

def classify(verb, act, name):
    if (verb, name) in DEST_ENUM:
        return "枚舉"
    if isinstance(act, argparse._StoreTrueAction | argparse._StoreFalseAction):
        return "整數／布林"
    if act.choices is not None:
        return "枚舉"
    if act.type in (int, float):
        return "整數／布林"
    if name in SHA or name in IDENT:
        return "SHA／識別碼"
    if name in PATH:
        return "路徑"
    if name in STRUCT:
        return "結構化輸入"
    if name in FREETEXT:
        return "自由文字"
    return None  # 無沉默預設格

parser = build_parser()
sub = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
total, unclassified, counts = 0, [], {}
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
print(f"總參數數 = {total}；未分類 = {len(unclassified)}")
for v, n in unclassified:
    print(f"  未分類 {v} {n}")
print("分類分佈：" + "、".join(f"{k} {counts[k]}" for k in sorted(counts)))
raise SystemExit(1 if unclassified else 0)
```

**於基線 `7451b72` 的實跑結果**（9 個子指令，`open`／`doctor`／`snapshot` 一併列入以確認分類器對唯讀與不承接動詞同樣是全函數）：

```
總參數數 = 106；未分類 = 0
分類分佈：SHA／識別碼 31、整數／布林 25、枚舉 10、結構化輸入 6、自由文字 20、路徑 14
exit=0
```

**負向測試**（證明檢查非恆真）：自 `FREETEXT` 移除 `--evidence` 後重跑——

```
總參數數 = 106；未分類 = 2
  未分類 deploy-state --evidence
  未分類 handoff --evidence
exit=1
```

未登錄的參數確實會被指名並使檢查失敗。**沒有這個負向測試，「未分類 = 0」不構成證據**——它同樣可能來自一個永遠回傳某個型別的分類器。

**§4.3 的證據**：把 `DEST_ENUM` 清空（即改以 argparse 宣告為唯一分類鍵）重跑——

```
總參數數 = 106；未分類 = 3
  未分類 assign --status
  未分類 amend --db-scope
  未分類 handoff --status
分類分佈：… 枚舉 7 …
exit=1
```

這三個旗標**無法由 argparse 宣告分類**：它們既沒有 `choices`，也不屬於路徑／SHA／整數布林／結構化任何一類。有沉默預設格的分類器會把它們歸入自由文字並靜默通過（枚舉 7／自由文字 23），**於是 §4.1 的 emoji 拒收條款對真正的暴露面完全不生效**；無預設格的分類器則當場指名它們。這就是分類鍵必須是目的地欄位的機械證據。

實作卡須把本腳本落為 CI 檢查：**新增參數而未能分類即 CI 紅**，使 §4.2 的 fail-closed 規則有機械執行者，而不是文件裡的一句「應該要」。

---

## 5. resume 演算法、`already_exists` 與 salt

### 5.1 演算法（純讀 GitHub，無本機狀態）

1. 讀該卡完整事件流，取得現有最大序號，並套用 §1.2 的五情形判準。任一 fail-closed 情形成立 → 該卡降純偵測，**演算法終止**。
2. 依 §3.3 算出本次的 `event_id`（**不需要鏈尖端**）。
3. **若該 `event_id` 已存在於事件流** → 這是同一意圖先前已落地的寫入：**不重寫**，改依 #16 §4.2 自該筆首寫推導後續步驟並補齊缺漏（#16 §5.2 白名單第 1 條），並以 §5.2 的退出語意告知操作者。
4. **若不存在** → 取 `max + 1` 為 `state_version`，在 §2 的同機原子目錄鎖內完成「重讀確認 → 寫入」。
5. 寫入後若回應遺失，下一次執行從步驟 1 重來，**必然落到步驟 3**——因為鍵不依賴鏈的狀態。

步驟 5 是整個設計的收斂性論證：**鍵對鏈的狀態不敏感，所以重試必然自我辨識。** §3.2 的鏈尖端方案正是在這一步發散。

### 5.2 `already_exists`：可辨識退出碼，零狀態寫入

步驟 3 命中既有事件時，`wfcli` 以**非零但可辨識的退出碼**結束，**不寫入任何狀態**，訊息明指「已存在，視為重試；若確實要再寫一筆請帶 `--new-attempt <標籤>`」。

**退出碼須全域保留，不可沿用既有碼。** 基線 `7451b72` 的退出碼 `0`–`6` 與 `130` 皆已佔用，且**語意逐指令重疊**——`4` 在 `assign` 是資源宣告衝突（`assign_cmd.py:111`）、在 `review` 是拒收（`review_cmd.py:152`）、在 `handoff` 是狀態守衛（`handoff_cmd.py:109`）、在 `deploy-declare` 是前置狀態不符（`deploy_declare_cmd.py:104`）。腳本要區分「真的失敗」與「已經做過了」，就需要一個**跨動詞語意一致**的碼。

> **裁定：保留退出碼 `7` 專用於 `already_exists`，全動詞一致，且不得再賦予其他語意。**

`7` 於基線未被任何指令使用（機械核對：`grep -rn "return [0-9]\+$" cli/src/` 的相異值為 `0 1 2 3 4 5 6 130`）。實作卡須附一個 CI 檢查防止未來有人把 `7` 挪作他用。

### 5.3 `--new-attempt <標籤>`：salt 衝突 fail-loud

`--new-attempt` 是操作者對「這是刻意的新一筆，不是重試」的顯式聲明，取值進入 `attempt_salt`。

**若帶入的標籤與既有事件算出同一 `event_id`**（同卡、同動詞、同參數、**同標籤**）→ **拒絕並要求換標籤**，不得靜默視為重試。理由是操作者已明示要新的一筆，把明示意圖靜默降級為重試，比拒絕更糟——它讓操作者以為寫成功了。

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

### 7.1 寫入邊界：逐動詞列舉（依基線 `7451b72` 的實際呼叫）

閉包由 `cli/src/wf_cli/commands/` 目錄列舉決定，不由本設計挑選成員。每一個遠端寫入呼叫即一個注入點：

| 動詞 | 遠端寫入序列 | 注入點數 |
|---|---|---|
| `review` | `add_issue_comment`(:230) → 交付狀態(:231) → `set_item_body`(:242) | 3 |
| `amend` | `add_issue_comment`(:229，僅 `--escalate`) → 級別(:392，僅 `--tier`) → `set_item_body`(:423) | 3 |
| `handoff` | owner(:136) → 交付狀態(:137) → 最後交接(:138) → iteration(:139) → `set_item_body`(:146) | 5 |
| `assign` | owner(:114) → 分支worktree(:115) → 交付狀態(:116) → `set_item_body`(:123) | 4 |
| `deploy-declare` | `add_issue_comment`(:122) → 部署狀態(:134) → Status(:137) | 3 |
| `deploy-state` | `add_issue_comment`(:141) → 部署狀態(:156) → Status(:157) → owner(:158) → 最後交接(:159) | 5 |
| `open` | **不承接**，見 §8 | — |
| `doctor`／`snapshot` | **唯讀**，無注入點 | 0 |

**共 23 個注入點。** 另有一個所有寫入動詞共用的前綴 `ensure_fields`（建立 Project 欄位）：它與卡內容無關且天然冪等，**列為第 24 個注入點但期望結果不同**——重試應為無操作，不得因欄位已存在而失敗。

### 7.2 矩陣：每個注入點 × 三項期望

對 §7.1 的每一個注入點，注入「**請求送達 GitHub 且寫入成功，但回應遺失**」，重跑後逐項檢查：

| # | 期望 | 失敗即代表 |
|---|---|---|
| E1 | **不得產生第二筆事件** | `event_id` 導出不決定性，或用了鏈尖端（§3.2） |
| E2 | **不得判為撞號** | §1.2「同號同 `event_id` 不是撞號」未實作，該卡被誤降級 |
| E3 | **能正確補齊後續步驟** | 首寫自描述性不成立（#16 §4.3），或 resume 步驟 3 的推導有缺 |

合成 mock 可用於此項——**故障注入本來就無法用真實 timeline 取得**，這是方法論上的必要讓步，不是取巧。但覆蓋必須是 §7.1 的全部 24 個注入點，不得抽樣。

> **一項紀律，來自 #17 的教訓**：合成 fixture 全綠不代表真卡安全（#17 的驗證當時真卡上已存在會觸發停機的留言，合成探針漏抓，遲至 #20 才發現）。因此除故障注入外，實作卡另須對**至少一張真卡**跑一次 `event_id` 導出並比對既有事件，確認導出結果與實際歷史一致。

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

### 7.4 執行歸屬

| 項目 | 承接 |
|---|---|
| §7.2 的 24 注入點 × E1–E3 | 衍生實作卡（`cli/` 資源，須待 #21 釋放） |
| §7.3 的 M1–M5 | 同上 |
| §4.4 的分類器 CI 檢查 | 同上 |
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
| `AI_WORKFLOW.md:148` 本機可採原子目錄鎖；跨主機須具併發控制的服務 | **照該界線分層**（§2），且明示跨主機不可預防、只能偵測。未宣稱超出 canonical 授權的保證 |
| `AI_WORKFLOW.md:143`／`:165` 本機檔案不得暫代狀態 | **遵守**。鎖不持有狀態（§2）；resume 純讀 GitHub（§5.1）。#16 §4.1 的 WAL 拒絕理由本檔不重述 |
| `AI_WORKFLOW.md:139` remote coordination adapter 是唯一 lifecycle event writer | **不變**。本設計不新增 writer，只規範既有 writer 的取號與重試行為 |
| `FIELD_SPECS`（`project.py:28`）為凍結欄位 schema | **引用為枚舉的權威來源**（§4.1），不自訂枚舉清單。§4.3 的裁定是「以該表為分類鍵」，強化而非覆蓋它 |
| `handoff-contract.md:16` `event_id` 寫為 `<UUID>` | **需修訂**：UUIDv5 仍是合法 UUID，格式相容，但「隨機」的隱含語意須改為「由 §3.3 決定性導出」。此為契約修訂，走紅線 PR |

**唯一需要契約修訂的是最後一列**，其餘皆為補完。

---

## 10. 非目標與殘餘限制

- **不做跨主機並行預防**：無可用併發控制服務，只偵測（§2）。宣稱能預防即是假保證。
- **不承接 `open` 的冪等性**（§8）。
- **不改 lifecycle event 的欄位集合**：schema 是 canonical `:141` 的，本卡只定義既有欄位怎麼取值。
- **不處理 legacy epoch 的追溯**：以 `contract-baseline` 劃界，界前事件不重新編號（§1.2）。
- **`--status`／`--db-scope` 缺 `choices` 驗證**：本卡以「分類鍵＝目的地欄位」使其不影響冪等鍵正確性（§4.3），但**旗標本身的輸入驗證仍缺**，屬實作卡範圍。
- **殘留鎖的回收策略未定死**：§2 已要求「可判定失效並回收」，但 TTL 具體值歸實作卡——本設計只給紅線（不得讓一次崩潰使該卡永久卡死）。

---

## 11. 衍生實作卡（建議）

| 卡 | 內容 | 前置 |
|---|---|---|
| **A** | `event_id` 決定性導出 ＋ §4 六型別正規化 ＋ §4.4 分類器 CI | #21 釋放 `cli/` |
| **B** | §2 原子目錄鎖 ＋ §1.2 五情形判準 ＋ 退出碼 `7` | A |
| **C** | §7 全 24 注入點 × E1–E3 ＋ §7.3 M1–M5 | A、B |
| **D** | `handoff-contract.md` 的 `event_id` 語意修訂（契約，紅線 PR） | A |

C 是驗收閘門：**A、B 未通過 C 不得宣稱冪等性成立。**
