# Control-plane Contract — <專案名>

> 共同不變量見 canonical `AI_WORKFLOW.md` §4.1、§4.3、§4.4。本檔定義該專案如何把協作狀態與本機資源鎖分離；不得填入 token、secret 或使用者個資。

## 1. Adapter 邊界

| 範圍 | 實作 | 事實來源／用途 |
|---|---|---|
| Remote coordination（GitHub 預設） | <Issue／Project #<n>／Actions workflow> | 唯一 lifecycle writer：跨人 task、review、lease、CI 與協作事件 |
| **狀態寫入通道** | <祕書 CLI 指令；canonical §4.3 要求唯一通道> | 繞過它的狀態寫入（含看板 UI 手改欄位）即違規 |
| Local resource | <原子目錄鎖／OS lock／container runtime> | worktree、port、container、未提交變更的暫時互斥；只回報 telemetry，不改 card state |
| Event store | <Issue timeline ＋結構化 comment／受保護 Git history／外部 append-only store> | 事件歷史；採 Issue timeline 時必須有定期 snapshot export 作離線稽核副本 |
| Ledger projection | <產生方式與位置；cutover 後＝snapshot 產生，不手改> | 活卡 current-state 顯示；不得手改 |
| **封存的舊狀態面** | <舊 event log／Ledger 路徑與終筆 SHA；已 cutover 才填> | 唯讀，不得再追加或重建 |

## 2. Event schema 與狀態

```yaml
event_id: <UUID/monotonic ID>
card_id: <CARD_ID>
type: migration-baseline | claim | handoff | handoff-accepted | contract-baseline | baseline-change-request | preflight-failed | review | review-invalid | review-correction | review-marker-clearance | escalation-epoch-change | escalation-checkpoint | escalation-resolution | status-change | correction | merge | release
actor: <GitHub account / model@tool>
occurred_at: <ISO 8601>
state_version: <strictly increasing integer>
iteration: <integer>
source_sha: <required for review/handoff/merge/release>
evidence: <PR, CI, test or decision link>
```

review preflight／退回／升級另依 [`review-escalation.md`](review-escalation.md) 實作
`attempt_id`、`escalation_epoch`、結構化 findings 與 `counts_toward_escalation`；不得把所有
`REJECT` event 直接視為一次升級計數。專案可擴充 event type，但必須文件化狀態轉移，
不得將未識別 type 默默當成 review attempt。

local telemetry 另以同一 envelope 記錄 `resource-acquired | resource-released`，但必填 `lifecycle: false`、`claim_event_id`，且不得填 `state_version` 或改 card state。

獨立狀態機事件另以同一 envelope 記錄 `deployment-declaration | deployment-status-change`，`type` 與 `event_id` 必填，但**不推進本卡的 `state_version`**、不改交付狀態；必須明示它推進的是哪一個狀態變數（部署狀態機見 canonical `AI_WORKFLOW.md` §0）。

**本節的管轄邊界**：凡使用本 envelope 的事件皆受本節管轄，今天共三類——lifecycle（上方 `type:`
列舉）、local telemetry、獨立狀態機事件。判準是**是否走本 envelope**，不是「有沒有
`state_version`」；後者只是三類的**區別特徵**，把區別特徵當管轄判準會使任何不帶 `state_version`
的事件看起來在管轄之外。三類各自的宣告面登記於 §2.4。

列出允許的狀態轉移、Gate／preflight 退回、`⏸阻塞` 的 TTL、escalation checkpoint 與
`🚨已升級` 的決策 owner：

<專案實作>

### 2.1 型別登記表

上方三個宣告面只登記**名稱**；每個 type 的必填欄位與狀態轉移由其**定義出處**承載，本檔不複述。
`表示層` 欄是 §2.3 的 L1→L2 解析函數：值為 `無`，或該型別在 L2 登記的 `event` 值。
登記新 type 時三欄一併填；缺定義出處或缺表示層宣告者不得列入上方宣告面。
**這是約定，不是機械強制**：§2.4 的對帳器可重跑且會判紅，但本 repo 無 CI、無任何程式讀取本檔
（`grep -rn "control-plane-contract" cli/ scripts/` 零命中），故**沒有呼叫點**——執行者仍是本檔
管轄者與該次變更的查核者。

| type | 類 | 定義出處 | 表示層 |
|---|---|---|---|
| `migration-baseline` | lifecycle | `MIGRATION.md` §1 第 3 點；該事件即該卡的 `state_version: 1` | `無` |
| `claim` | lifecycle | canonical `AI_WORKFLOW.md` §4.1（`:144` 逐項列出必填欄位） | `assign` |
| `handoff` | lifecycle | [`handoff-contract.md`](handoff-contract.md) | `handoff` |
| `handoff-accepted` | lifecycle | [`handoff-contract.md`](handoff-contract.md) | `無` |
| `contract-baseline` | lifecycle | [`review-escalation.md`](review-escalation.md) | `無` |
| `baseline-change-request` | lifecycle | [`baseline-cascade.md`](baseline-cascade.md)〈程序〉第 1 點「凍結」 | `無` |
| `preflight-failed` | lifecycle | [`review-escalation.md`](review-escalation.md) | `無` |
| `review` | lifecycle | 無專屬定義檔；語意見本檔第 3–5 節與 canonical `AI_WORKFLOW.md` §4.1／§4.3，狀態轉移由採用專案在上方〈專案實作〉補齊 | `review` |
| `review-invalid` | lifecycle | [`review-escalation.md`](review-escalation.md) | `無` |
| `review-correction` | lifecycle | [`review-escalation.md`](review-escalation.md) | `無` |
| `review-marker-clearance` | lifecycle | [`review-escalation.md`](review-escalation.md) §5「`review-marker-clearance` 解除 §1 的留痕解析停機，必填：」 | `review-marker-clearance` |
| `escalation-epoch-change` | lifecycle | [`review-escalation.md`](review-escalation.md) | `無` |
| `escalation-checkpoint` | lifecycle | [`review-escalation.md`](review-escalation.md) | `無` |
| `escalation-resolution` | lifecycle | **provisional，見 §2.2** | `無` |
| `status-change` | lifecycle | [`review-escalation.md`](review-escalation.md) | `無` |
| `correction` | lifecycle | 無專屬定義檔；語意見本檔第 3–5 節與 canonical `AI_WORKFLOW.md` §4.1／§4.3，狀態轉移由採用專案在上方〈專案實作〉補齊 | `amend` |
| `merge` | lifecycle | 無專屬定義檔；語意見本檔第 3–5 節與 canonical `AI_WORKFLOW.md` §4.1／§4.3，狀態轉移由採用專案在上方〈專案實作〉補齊 | `無` |
| `release` | lifecycle | [`worktree-lifecycle.md`](worktree-lifecycle.md) | `無` |
| `resource-acquired` | telemetry | 上方 telemetry 行＋ canonical `AI_WORKFLOW.md` §4.1（`:141` 末句） | `無` |
| `resource-released` | telemetry | 上方 telemetry 行＋ canonical `AI_WORKFLOW.md` §4.1（`:141` 末句） | `無` |
| `deployment-declaration` | 獨立狀態機 | canonical `AI_WORKFLOW.md` §0 的部署狀態機（六態線性 ＋ `—不適用`） | `deployment-declaration` |
| `deployment-status-change` | 獨立狀態機 | canonical `AI_WORKFLOW.md` §0 的部署狀態機（六態線性 ＋ `—不適用`） | `deployment-status-change` |

### 2.2 Provisional 登記

定義出處尚未併入本 repo `main` 的 type 以 **provisional** 登記，並釘住相依 SHA 使其可稽核。
provisional 期間 consumer 對該 type 的處置：視為**已登記但無本地定義**——依上方規則不得當成
review attempt，且不得依其欄位做任何裁決，只能記錄並 fail-closed。

| type | 相依 | 釘住 SHA | 該 SHA 內的定義位置 | 釘住時狀態 |
|---|---|---|---|---|
| `escalation-resolution` | `ruan6047/ai-workflow` #39，分支 `claude/WF-ESCALATION-RESOLUTION-GAP1` | `b039c0b08113382566d9b687087dea1f08f3915c` | `templates/review-escalation.md` §5 | 🔍待查核；最近一次查核 REQUEST_CHANGES |

對帳命令（任何人可重跑，輸出即判準，不依賴任何人的記憶）：

```bash
# 釘住的定義仍在（預期非空）
git show b039c0b:templates/review-escalation.md | grep -c '^`escalation-resolution` 解除'
# 是否已落地 main（0 = 尚未落地；非 0 = 落地對帳已到期）
git show origin/main:templates/review-escalation.md | grep -c '^`escalation-resolution` 解除'
```

**落地對帳**：相依卡併入 `main` 時以三款結算，全成立才將該列移出本節並轉為正式登記；
任一不成立即自上方列舉移除該 token。(1) `main` 的定義出處存在名稱**逐位元組等於**該 token
的定義；(2) 其必填欄位集合與釘住 SHA 相同，或差異隨同一次變更一併登記；(3) 本節對應列同時
刪除，不留孤兒 pin。相依卡被否決或改名時第 (1) 款即不成立。**本節是約定，其執行者是相依卡的
merge 授權者與本檔管轄者**；上面第二道命令回傳非 `0` 是它到期的可觀測訊號。

採用專案複製本範本時連同本節複製，該 token 在該專案同樣是 provisional，待上游結算後隨範本轉正。

### 2.3 L1／L2 分層、層界與包含關係

事件型別語彙在本 repo 有兩份登記。本節裁定其管轄關係，本檔是該裁定的落地面。

**不設單一權威**，兩份分屬兩層：

- **L1 邏輯層**——哪些 lifecycle 事實存在、envelope 欄位、狀態轉移、誰可寫。權威是本檔 §2，
  經 `ADOPTION.md` 實例化為各採用專案的 `<專案>/docs/CONTROL_PLANE_CONTRACT.md`。
  **開放可擴充**（上方明文「專案可擴充 event type」，本檔全檔未宣告自己封閉）。
- **L2 表示層**——L1 事件中哪些以 Issue 留言 marker 承載其識別符，及該 marker 的鍵集合與順序。
  機制歸 [`handoff-contract.md`](handoff-contract.md) §3.1.7，**成員名單**歸採用專案的設計文件。
  **封閉**：不在表內即 fail-closed。

**層界（可判定）**：一個型別屬於 L2，**當且僅當**該事件以 Issue 留言 marker 承載其識別符。
**跨層分工**：L1 管語意（事實是什麼、必填欄位、狀態轉移、誰可寫）；L2 管表示（有無 marker、
marker 的鍵與順序、以及**寫在線上的那個名字**）。兩邊不得越界：L2 不得為型別定義狀態轉移，
L1 不得規定 marker 的鍵。

**唯一的硬約束是包含關係，且兩個方向不對稱**：

1. **每個 L2 成員必須解析到一個已登記的 L1 型別。** 否則 L1 消費者讀到它會落進「未識別 type」
   分支，而 §2 對該分支只有一條禁令、沒有可用處置——未登記正好使那條禁令無從遵守。
   此方向非空即**阻擋**。
2. **反向（L1 有而 L2 無）不是分歧。** 一個 L1 型別可以完全不需要 marker（`merge`、`release`
   即是）。但它必須是**被宣告過的無**，故 §2.1 的 `表示層` 欄對每個型別必填；缺該宣告才是缺陷，
   且其訊息必須與第 1 條**分離**。把 L1 的開放性當缺陷來報，會產生十餘筆恆紅的假警報，
   而一個天天噴假警報的檢查會被關掉。

**第 1 條比對的是解析結果，不是兩個名稱集合的差集。** 理由出自本節自己的分工：**線上的那個
名字屬於表示層**。動詞是寫入動作，型別是被寫下的事實，兩者同名是實作巧合、不是身分；
把 L2 的 `event` 值當成型別名去做名稱差集，消除差集的唯一手段就會是把動詞名補登為型別名，
L1 從此帶兩組同義字，比今天更難修。§2.1 的 `表示層` 欄即該解析函數。

本檔管轄者據此裁定兩筆**非同名**解析（其餘為同名）：

- `assign` → `claim`。依據是引用不是推論：canonical `AI_WORKFLOW.md` §3（`:100`）要求派工時的
  能力偏離「記入 claim 事件」，而 `cli/src/wf_cli/commands/assign_cmd.py` 的 docstring 正以該條
  為由要求 `--actual-capability`；本 repo 亦無 `claim` 子命令。**未閉合的落差（僅指名，逸出本檔）**：
  canonical §4.1（`:144`）要求 claim 記錄 `lease_expires_at`，`assign` 今天不寫 lease。
- `amend` → `correction`。強度較弱且據實標示：`correction` 在本 repo **無專屬定義檔**，故這是
  **名稱層裁定**——`amend`（開卡後更正已寫入的卡面欄位、原值留 Log）落在 `correction` 的字面
  涵蓋內，且 §2 內無第二候選（`review-correction` 由 `review-escalation.md` 定義且限於 review
  finding 閉合）。`correction` 的語意補齊逸出本檔。

### 2.4 宣告面登記表與對帳器

**判準（成文）**：一個 token 是型別宣告，**當且僅當**它出現在下表某一列指定的（檔案，錨點）
所抽出的集合中。表以外的任何文字——散文、註解、範例、任務卡、Issue 正文、CLI 動詞清單——
**一律不是**型別宣告，不論它多像。此判準把不可證明的「窮舉型別」換成可審的「窮舉宣告面」：
面的清單短、粗、人讀得完；型別的清單是開放的、散在自由文字裡。**這是遷移不是消除**——
漏登一個新面仍可能發生，但那是可見且可審的一件事，不是對自由文字證明否定命題。

掃描式啟發（例如「反引號 kebab token ＋ 該行含 事件／event／type」）**降級為候選提名器**：
負責發現可疑 token 交人裁定「這是不是一個未登記的宣告面」，不負責判斷。啟發式漏掉只影響
發現速度，不影響判準的正確性。

`最小筆數` 是登記當下的實測筆數；抽取結果低於它即判「來源未被讀到」而非「差集為空」——
**驗值不等於驗來源，一個讀不到來源的比對器其輸出與「兩邊一致」逐字相同**。下修最小筆數是
刻意的登記行為，必須與該次刪除同批進行。

| id | 檔案 | 錨點 | 層／類 | 最小筆數 |
|---|---|---|---|---|
| `s1` | 本檔 | §2 `type:` 行 | L1 / lifecycle | 18 |
| `s2` | 本檔 | §2 telemetry 行的反引號列舉 | L1 / telemetry | 2 |
| `s3` | 本檔 | §2 獨立狀態機事件行的反引號列舉 | L1 / 獨立狀態機 | 2 |
| `s4` | 本檔 | §2.1 表首欄 | L1 / 全型別交叉核對 | 22 |
| `s5` | 本檔 | §2.1 表 `表示層` 欄 | L1→L2 解析函數 | 22 |
| `s6` | `docs/WF_EVENT_MARKER_V2.md` | §3.2 表首欄 | L2 | 7 |
| `s7` | `docs/WF_EVENT_MARKER_V2.md` | §7 探針 `EVENTS` dict 鍵 | L2 | 7 |
| `s8` | 本檔 | §2.2 provisional 表首欄 | L1 / provisional | 0 |
| `s9` | `docs/WF_EVENT_MARKER_V2.md` | §2.3 裁定表的 `event=` 值 | L2 / 動詞→event 對照 | 6 |

`s6`／`s7` 兩列是同一份語彙的兩個面，對帳器逐項比對；`s9` 是第三個面（動詞→`event` 的對照裁定），
它依構造只涵蓋子集（`open` 無 marker），故對它驗**子集**而非等於。`s8` 的最小筆數是 `0`——它可以合法地
空掉（provisional 全數結算），故對它改以**錨點探測**代替筆數下限；這是 `最小筆數 ≥ 1` 這條
通則的唯一例外，其代價是 `s8` 只能偵測錨點消失、不能偵測列被誤刪。

採用專案複製本範本時，`s6`／`s7` 兩列換成該專案自己的 L2 登記檔；若該專案的 event store 不是
Issue timeline（§1 允許外部 append-only store），則該專案沒有 L2，刪去兩列並把對帳器的
`L2DOC` 檢查停用即可，第 2 條方向的檢查仍然有效。

對帳器（自本檔抽出後執行，任何人可重跑；輸出即判準）：

```bash
#!/usr/bin/env bash
# event-type-reconcile v1 — §2.4 的對帳器。自 repo 根目錄執行。
# 抽出並執行：
#   awk '/^#!\/usr\/bin\/env bash$/{f=1} f{print} /^# --- end event-type-reconcile ---$/{if(f)exit}' \
#     templates/control-plane-contract.md > /tmp/reconcile.sh && bash /tmp/reconcile.sh
# 退出碼：0 PASS｜1 FAIL（包含關係或宣告缺失）｜2 來源未被讀到（零產出 fail-closed）
set -uo pipefail
CPC="${CPC:-templates/control-plane-contract.md}"
L2DOC="${L2DOC:-docs/WF_EVENT_MARKER_V2.md}"
fail=0; hard=0
sec(){ awk -v a="$1" -v b="$2" '$0 ~ a {f=1} f && $0 ~ b && $0 !~ a {f=0} f' "$3"; }
row(){ awk -F'|' -v n="$1" 'NF==n && $2 ~ /^ *`[a-z][a-z-]*` *$/'; }
cell(){ awk -F'|' -v c="$1" '{gsub(/[` ]/,"",$c); print $c}'; }

x_s1(){ sec '^## 2\. ' '^### 2\.1 ' "$CPC" | sed -n 's/^type: //p' | tr '|' '\n' | tr -d ' ' | sed '/^$/d'; }
x_s2(){ sec '^## 2\. ' '^### 2\.1 ' "$CPC" | sed -n 's/^local telemetry .*記錄 `\([^`]*\)`.*/\1/p' | tr '|' '\n' | tr -d ' ' | sed '/^$/d'; }
x_s3(){ sec '^## 2\. ' '^### 2\.1 ' "$CPC" | sed -n 's/^獨立狀態機事件.*記錄 `\([^`]*\)`.*/\1/p' | tr '|' '\n' | tr -d ' ' | sed '/^$/d'; }
t21(){ sec '^### 2\.1 ' '^### 2\.2 ' "$CPC" | row 6; }
x_s4(){ t21 | cell 2; }
x_s5(){ t21 | cell 5 | sed 's/^$/<空>/'; }   # 空格填佔位，使「缺宣告」由第 5 檢查報，不被誤報成來源未讀到
x_s6(){ sec '^### 3\.2 ' '^### 3\.3 ' "$L2DOC" | row 4 | cell 2; }
x_s7(){ sed -n '/^EVENTS: dict\[str, tuple\[str, \.\.\.\]\] = {$/,/^}$/p' "$L2DOC" | sed -n 's/^ *"\([a-z][a-z-]*\)":.*/\1/p'; }
x_s8(){ sec '^### 2\.2 ' '^### 2\.3 ' "$CPC" | row 7 | cell 2; }
x_s9(){ sec '^### 2\.3 ' '^### 2\.4 ' "$L2DOC" | grep -o 'event=[a-z][a-z-]*' | sed 's/^event=//' | sort -u; }

# 0) 登記表的 id 集合必須與抽取器函式集合逐項相符
regids=$(sec '^### 2\.4 ' '^#!/usr/bin/env bash' "$CPC" | awk -F'|' 'NF==7 && $2 ~ /^ *`s[0-9]+` *$/' | cell 2 | sort)
fnids=$(declare -F | sed -n 's/^declare -f x_\(s[0-9]*\)$/\1/p' | sort)
if [ "$regids" != "$fnids" ]; then
  echo "FAIL[登記表與抽取器不符] 登記=$(echo $regids) 抽取器=$(echo $fnids)"; fail=1
fi

# 1) 每個面：抽取結果不得低於登記的最小筆數（零產出 fail-closed）
while IFS='|' read -r id min; do
  n=$("x_$id" | sed '/^$/d' | wc -l | tr -d ' ')
  echo "INFO 面 $id 抽到 $n 筆（登記下限 $min）"
  if [ "$n" -lt "$min" ]; then
    echo "FAIL[來源未被讀到] $id 抽到 $n 筆，低於登記的最小筆數 $min"; hard=1
  fi
done < <(sec '^### 2\.4 ' '^#!/usr/bin/env bash' "$CPC" | awk -F'|' 'NF==7 && $2 ~ /^ *`s[0-9]+` *$/ {gsub(/[` ]/,"",$2); gsub(/ /,"",$6); print $2"|"$6}')
grep -q '^### 2\.2 ' "$CPC" || { echo "FAIL[來源未被讀到] s8 錨點 §2.2 不存在"; hard=1; }
grep -q '^EVENTS: dict\[str, tuple\[str, \.\.\.\]\] = {$' "$L2DOC" || { echo "FAIL[來源未被讀到] s7 錨點不存在"; hard=1; }
[ "$hard" = 1 ] && { echo "RESULT FAIL(2) 來源未被讀到，其餘比對不可信"; exit 2; }

L1=$( { x_s1; x_s2; x_s3; } | sort -u )
REG=$(x_s4 | sort -u); L2A=$(x_s6 | sort -u); L2B=$(x_s7 | sort -u)

# 2) L2 的兩個面必須一致
d=$(comm -3 <(echo "$L2A") <(echo "$L2B")); [ -n "$d" ] && { echo "FAIL[L2 兩面不一致] $d"; fail=1; }

# 2b) L2 的動詞→event 對照表只可宣告封閉語彙內的值（子集，非等於：`open` 無 marker）
d=$(comm -23 <(x_s9) <(echo "$L2A")); [ -n "$d" ] && { echo "FAIL[L2 對照表宣告的 event 值不在封閉語彙內] $(echo $d)"; fail=1; }

# 3) §2.1 登記表必須與三個宣告面逐項相符
d=$(comm -23 <(echo "$L1") <(echo "$REG")); [ -n "$d" ] && { echo "FAIL[宣告面有而登記表無] $(echo $d)"; fail=1; }
d=$(comm -13 <(echo "$L1") <(echo "$REG")); [ -n "$d" ] && { echo "FAIL[登記表有而宣告面無] $(echo $d)"; fail=1; }

# 4) 阻擋方向：每個 L2 成員必須解析到一個已登記 L1 型別
unres=""
while read -r e; do
  t21 | awk -F'|' -v e="$e" '{gsub(/[` ]/,"",$5)} $5==e {found=1} END{exit !found}' || unres="$unres $e"
done <<< "$L2A"
[ -n "$unres" ] && { echo "FAIL[L2 成員無法解析到已登記 L1 型別]$unres"; fail=1; }

# 5) 非阻擋方向：每個 L1 型別必須帶明示的表示層宣告，且不得指向不存在的 L2 值
while IFS=$'\t' read -r t r; do
  [ -z "$r" ] && { echo "FAIL[L1 型別未宣告表示層地位] $t"; fail=1; continue; }
  [ "$r" = "無" ] && continue
  echo "$L2A" | grep -qx -- "$r" || { echo "FAIL[表示層指向不存在的 L2 值] $t -> $r"; fail=1; }
done < <(t21 | awk -F'|' '{gsub(/[` ]/,"",$2); gsub(/[` ]/,"",$5); print $2"\t"$5}')

# 6) provisional 不得留孤兒 pin
while read -r p; do
  [ -z "$p" ] && continue
  echo "$REG" | grep -qx -- "$p" || { echo "FAIL[孤兒 provisional pin] $p"; fail=1; }
done <<< "$(x_s8)"

# 7) 資訊列（非阻擋）：原始名稱差集，供人對照；非同名解析使它預期非空
echo "INFO 原始名稱差集 L2\\L1（僅供對照，非判準；非同名解析使它預期非空）= $(comm -13 <(echo "$L1") <(echo "$L2A") | tr '\n' ' ')"
echo "INFO 未解析的 L2 成員數 = $(echo "$unres" | wc -w | tr -d ' ')"
[ "$fail" = 1 ] && { echo "RESULT FAIL(1)"; exit 1; }
echo "RESULT PASS"; exit 0
# --- end event-type-reconcile ---
```

**本對帳器擋不住什麼**（逐項，勿當成完整性證明）：

1. **沒有呼叫點。** 本 repo 無 `.github`、無 CI，且無任何程式讀取本檔。它是可重跑的**檢查器**，
   不是會擋下變更的**閘門**；「會擋」在有呼叫點之前一律是約定。
2. **漏登一個宣告面它看不見。** 判準把問題搬到「窮舉宣告面」，沒有消除它。新增一個面而不登記，
   對帳器不會知道——它只保證**已登記的面**之間一致。
3. **`s8` 只驗錨點不驗筆數**，provisional 列被誤刪不會轉紅。
4. **它不驗語意。** 定義出處欄是否真的定義了該型別、`表示層` 的兩筆非同名解析（§2.3）是否正確，
   全在它的能力之外；它只驗集合關係與來源可讀。
5. **它不驗 marker 的鍵集合與順序**，那是 L2 自己的 fail-closed 範圍。
6. **抽取式依賴文字錨點。** 錨點漂移由最小筆數擋成 FAIL(2)，但**格式改寫成仍可抽到足量卻抽錯
   內容**這種情形擋不住。
7. **`s9` 只驗子集**：動詞→`event` 對照表若**漏掉**一個本該有 marker 的動詞，它看不見；
   它只保證該表宣告的值都在封閉語彙內。

## 3. Claim、lease 與 WIP

- claim command／workflow：<命令或 URL>
- concurrency key：<repository + card/resource key>
- lease TTL／續約：<時間與命令>
- 到期回收：<未提交變更檢查、通知與人工介入>
- WIP limit：agent <n>；review queue <n>；超過時 <行為>
- **派工前資源交集比對**：<命令；比對本卡寫入集 × 現役卡寫入集，撞則排隊。現役含 `📦已合併` 未收尾者—canonical §4.4>
- **破壞性 CLI（啟動須驗 lease，無 lease 拒跑）**：<入口清單>
- **當前仍有副作用的 CLI 入口（查核／探索禁跑）**：<入口清單／無—canonical §6.1 第 6 條>
- **worktree 註冊**：<認領時把實際路徑＋分支寫回卡的命令>；派工前必跑的 `doctor` 對帳：<命令>

## 4. Handoff 與 optional tmux adapter

- Handoff contract：從 [`handoff-contract.md`](handoff-contract.md) 建立 `<專案>/docs/HANDOFF_CONTRACT.md`；T2 以上或 owner 變更必填。
- Receiver 驗證：<驗證完整 SHA、baseline、lease、證據的 command／workflow>
- Receiver 接受事件：<`handoff-accepted` writer 與權限>
- tmux：<不用／僅 session launcher／僅 wake-up；不得作為遠端狀態來源>
- Local runtime：<路徑；必須在 `.gitignore`；清理／重啟程序>

## 5. 權限與事故處理

- GitHub Actions token／App 權限：<最小 permissions>
- 外部協作者可做／不可做：<claim、review、merge、release>
- GitHub 不可用時：<停止 claim／本機鎖的限制／恢復程序>
- 對帳：<claim、handoff、merge、release 後的檢查命令>
