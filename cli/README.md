# wf-cli — 祕書 CLI 最小集（WF-22-CLI1）

> 決議 1「祕書單寫入通道」的機械化：任務狀態面遷移至 GitHub Issues/Projects v2 後，
> **本 CLI 是唯一寫入通道**。文件明示：**不經本 CLI 對 Ledger 欄位／資源宣告的狀態
> 寫入即違規**（例如直接在 GitHub UI 手改 Project 欄位）。CLI 本身不做權限強制
> （單機信任模型），紀律由治理承擔，不是技術鎖死。

## 九指令

| 指令 | 做什麼 | 讀寫 |
|---|---|---|
| `open` | 依範本開卡：建立 Issue／Project draft item ＋（可選）git spec 檔骨架；核心痛點／服務的原始目標／tier／db_scope／資源宣告／鏈深／**規劃期路由**（執行與查核各一能力層級＋理由）六＋一項機械檢查全過才建卡；`--chain-depth`（預設 0）> 2 依決議 5 鏈式停損協定硬拒 | 寫 |
| `assign` | 派工：寫 owner／分支worktree／交付狀態；比對本卡與其他**已認領**活卡的資源宣告交集，撞則拒絕並列出衝突卡；`--actual-capability` 必填並與卡面建議執行層級比對，非「相符」（偏離／無基線／無法解析）一律 fail-closed 要求 `--capability-deviation-reason`，實際層級與理由一併入 Log | 寫（有條件拒絕） |
| `amend` | 開卡後修訂卡面：spec 基線／驗收條件／驗證項目／資源宣告／`級別`；`--reason` 必填，每個被改欄位各 append 一行 Log 記下**完整原值**（不截斷，Log 是唯一還原點）並帶同一 `op` 識別碼；值未變、內容為空、錨點不唯一一律拒絕；清單替換預設重設未勾選，`--preserve-checked` 才沿用；`級別` 先寫並讀回驗證再寫 body；寫入前重讀比對，被他人改動即中止；`--record-unlogged-change` 補救半寫入；`--dry-run` 零遠端寫入 | 寫（有條件拒絕） |
| `handoff` | 交接：驗證 `source_sha`（完整 40 碼 hex）與證據欄非空，依 `--next-stage` 轉交付狀態、寫 owner／最後交接／iteration；`--next-stage implementation`（查核退回語意）自動 +1，`review`／`release` 不遞增，`--iteration N` 可顯式覆寫（印警示，理由寫在 `--evidence`）；`release` 且需部署卡在部署狀態 `✅已驗證` 前拒絕 | 寫（有條件拒絕） |
| `deploy-declare` | 需求方已明確裁決既有卡需要部署時，唯一允許 `—不適用 → ⏸未部署`；必填固定 `needs-deploy` decision、reason、actor，先追加真實 Issue timeline event，再只以 `updateProjectV2ItemFieldValue` 寫入部署狀態與內建 `Status=Todo`；`--dry-run` 零遠端寫入 | 寫（有條件拒絕） |
| `deploy-state` | 部署狀態只允許相鄰前進（`⏸未部署 → 🚀待部署 → ⏳部署中 → ✅已部署 → 🧪驗證中 → ✅已驗證`）；必填下一 stage owner、actor、evidence，先追加真實 Issue timeline event，再只以 `updateProjectV2ItemFieldValue` 寫入部署狀態、內建 `Status`、owner、最後交接；`--dry-run` 零遠端寫入 | 寫（有條件拒絕） |
| `review` | 查核裁決：驗 `templates/review-prompt.md` §5 結構化輸出（`review_result` 列舉、`core_pain_resolved` 必填、`self_run` 非空、finding 八欄 schema、結論與 findings 的語意一致性），過了才把裁決全文寫成 Issue 留言並轉交付狀態（`APPROVE`→`✅通過`／`REQUEST_CHANGES`→`↩退回`）；**無 `self_run` 的 `APPROVE` 記 `review-invalid` 拒收** | 寫（有條件拒絕） |
| `doctor` | 對帳：`git worktree list` vs 卡註冊、submodule 初始化、孤兒分支、殘留 lease、prunable worktree；`--review-channel` 另對帳查核寫入通道，依 `handoff-contract.md` §3.1 驗 marker 合規與**三面一致**（裁決留言／Log 索引行／Project 交付狀態欄），結果為 `recorded`／`half_written`／`marker_quarantined`／`receipt_untranscribed`／`unobservable` 五態之一；`--json` 時 stdout 只輸出 JSON（含 `review_channel` 鍵），人類報告走 stderr | **唯讀**，不清理 |
| `snapshot` | 匯出 Project 全部卡片為 JSON＋人類可讀 Markdown Ledger | 讀＋寫本機檔案（不寫回 GitHub） |

## 安裝與執行

```bash
cd cli
uv sync
uv run wfcli <command> --help
uv run pytest        # 全套測試（本 repo 新增；數量以此指令輸出為準）
```

## `open`：規劃期路由（WF-CLI-ROUTING-TIER1）

canonical `AI_WORKFLOW.md` §3 Plan：「Plan 產出必含建議執行／查核能力層級與理由
（層級語彙見專案 `MODEL_ROUTING.md`）」。`open` 因此有四個必填旗標：

```bash
wfcli open CARD-ID --repo owner/repo \
  --tier T3 \
  --exec-capability 主力型   --exec-capability-reason "跨模組改動、根因已知" \
  --review-capability 高階型 --review-capability-reason "資料正確性紅線，須跨家族查核" \
  ...
```

產出即 `templates/tasks-card.md` 第 4 行的形狀（`card.format_routing_line` 是唯一
渲染點，git spec 檔與 Issue body 共用，兩處不會 drift）：

```
- 執行：待指派（建議 主力型；跨模組改動、根因已知）　查核：待指派（建議 高階型；資料正確性紅線，須跨家族查核）
```

### ⚠️ 兩條不同的「層級」：`--tier` vs `--exec/review-capability`

**中英文都叫 tier／層級，但值域與語意完全不同，互不接受**：

| 旗標 | 卡面欄位 | 值域 | 這條軸在講什麼 |
|---|---|---|---|
| `--tier`（`amend --tier` 同義） | 級別 | `T0`–`T4` | **變更風險**：紅線、可逆性、影響面 |
| `--exec-capability`／`--review-capability` | 執行／查核括號內 | `經濟型`／`主力型`／`高階型` | **建議的模型能力**：這件事該派多強的執行者／查核者 |

值域刻意零交集，兩邊都用 argparse `choices` 硬擋：`--tier 主力型` 與
`--exec-capability T3` 都會直接被拒。

能力層級的語彙**照抄** repo 根目錄 `MODEL_ROUTING.md`「預設能力等級」欄，CLI 不自創
分類：該欄四列去掉修飾後恰好三級——「經濟型／deterministic automation」的斜線後段是
同一級的英文同義註解；「高階型 + 跨家族 review」的加號後段是**查核獨立性的附加要求**
（`templates/tasks-card.md` 第 4 行同樣寫「紅線須跨家族或人工」），寫進理由欄，不是第
四個層級。枚舉封閉，沒有「其他／未定」逃生格；`tests/test_card.py` 直接解析
`MODEL_ROUTING.md` 比對，語彙一漂移測試就紅。

卡面引用**層級**而非模型名，是因為模型名單會過期、層級才是穩定介面
（`MODEL_ROUTING.md` §「路由決定於規劃期」）。

### 缺欄＝硬拒，CLI 不代填預設值

四個旗標缺任何一個（argparse `required`）或理由為空白字串（`card.
validate_capability_routing`），一律拒絕且**不建卡**。刻意不採「預設＋警示」：
`MODEL_ROUTING.md` 要求「建議反映任務風險，不得因當下額度預先降級」，任何預設值都是在
沒讀過這張卡的風險的前提下代替規劃者作答——那只是把「靜默產出不符範本的卡」換成
「靜默填錯層級」，本能力要消除的痛點並未消失。

檢查在 CLI 層與 model 層各做一次：`Card` 把這四項放在 dataclass 的**必填區**（無預設
值），繞過 CLI 直接建構 `Card` 也產不出不符範本的卡。

### 派工端：`assign` 的偏離留痕

`MODEL_ROUTING.md` 第 14 行後半：「派工時可依可用性偏離建議，但**實際模型與偏離理由
記入 claim 事件**。」規劃端寫下建議、派工端記錄實際與偏離，兩端都在唯一寫入通道上：

```bash
# 相符：不需要理由
wfcli assign CARD-ID --assignee "某模型@某工具" --branch b --worktree /w \
  --actual-capability 主力型

# 偏離：未給理由會被拒（exit 2；拒絕路徑不做任何 item／body mutation）
wfcli assign CARD-ID ... --actual-capability 高階型 \
  --capability-deviation-reason "主力型當下額度不足，改派高階型"
```

`--assignee` 記具體模型名，`--actual-capability` 記它對應的能力層級——**卡面比對走層級**
（名單會過期，層級才是穩定介面），Log 兩者都留。

#### 比對是四格全函數，沒有「其餘」

`card.compare_capability_to_card` 把（卡面 body、實際層級）映到**恰好一格**：

| 結果態 | 什麼情況 | 需要理由？ | Log 措辭 |
|---|---|---|---|
| `matched` | 有版本標記、恰一行合格路由行，建議＝實際 | 否 | `（與卡面建議 X 相符）` |
| `deviated` | 有版本標記、恰一行合格路由行，建議≠實際 | **是** | `（偏離卡面建議 X；偏離理由：…）` |
| `absent` | **無版本標記**＝規劃期路由必填之前開的卡（#7–#25 全部屬此） | **是** | `（卡面無建議層級：…；理由：…）` |
| `ambiguous` | **有版本標記但讀不出可信的建議**：合格路由行不是恰一行，或任一欄不合格；body 排版損壞亦然 | **是** | `（卡面建議無法解析：…；理由：…）` |

#### `absent` 與 `ambiguous` 的分界＝遷移標記 `<!-- wf-routing:v1 -->`（R3-001）

**先講事實：舊卡與新卡在 body 內容上不可區分。** 舊制卡面第 4 行的執行／查核兩欄都是
**不受限的自由文字**，所以舊卡能產生與新制**逐位元組相同**的一行：

```
新制 Card(executor='待指派', executor_capability='主力型', …) 渲染
舊制 executor 自由文字填 '待指派（建議 主力型；跨模組）'
→ 兩者字串相等（test_old_card_can_be_byte_identical_to_a_new_one 釘住這條）
```

真實語料也支持：#16 的執行欄是 `待指派（先 grilling）`、#25 的查核欄是
`跨家族查核（T4 紅線：不可逆且會毀資料，須人工 sign-off）`——全形括號＋自由文字是常態。

因此「從內容判斷這張卡是不是新制」在資訊上不可能為真。先前兩輪都在這個不可能的問題上
調整啟發式，各壞一次：

| 版本 | 判準 | 壞在哪 |
|---|---|---|
| 初版 | 正規表示式有沒有匹配 | 排版壞掉的新卡被寫成「卡面無建議層級」（不實留痕）；理由被清空的卡判成 `matched`，反而**免除**理由要求 |
| 二版 | 行內有沒有「建議」字樣或能力層級值 | 舊卡寫「依建議降級」「主力型模型當班」被誤判為新制；新卡前綴被 U+200B 打斷後掉出判斷，又退回 `absent` |

**現行機制**：`open` 在新制卡的路由行上方寫入 `<!-- wf-routing:v1 -->`，分類**只查這個
標記是否存在**，完全不檢查自由文字：

- 標記不在 → `absent`（規劃期路由必填之前的卡），不看內容。
- 標記在 → 卡面自我宣告新制，就必須拿得出**恰好一行**合格路由行；否則 `ambiguous`。
  沒有「退回當舊卡」這條路。

標記沿用本 repo 既有的 HTML 註解慣例（`resources.py` 的 `<!-- resource-claims:begin -->`、
`doctor.py` 的 `<!-- wf-review-event:v1 ... -->`），不另創一套；與 doctor 的事件 marker
不碰撞（後者只掃 Issue **留言**且鎖 `wf-review-event:` 前綴）。標記只認**Log 之前**的
區段，Log 引用到它不算數。

> **殘留假設（明說，不宣稱絕對）**：舊卡的自由文字不會剛好含這串 HTML 註解。這與
> 「不會剛好含『建議』二字」是不同量級的假設——前者不是人會打進姓名欄的東西。

#### 為什麼不做零寬／格式字元正規化

前綴被 U+200B 打斷是**結構問題**，而標記機制已經在結構層解決它：標記在不在是布林事實，
不受行內字元破壞影響，所以壞掉的新卡必然落 `ambiguous`。反過來，若再加一層「哪些碼位
可以剝除」的正規化，等於重新造出一個猜測層——正是本輪要消滅的東西。層級值裡混入零寬
字元同樣落 `ambiguous`（`strip` 後查不到表），這是正確的 fail-closed 結果。

匹配成功也不等於合格，四欄逐一驗（**執行與查核兩軸都驗**，先前只驗了執行軸）：

| 破壞方式 | 分類 |
|---|---|
| 執行／查核理由為空或只有空白 | `ambiguous` |
| 全形分隔空白被改成半形 | `ambiguous` |
| 執行／查核層級不在 `MODEL_ROUTING` 語彙內 | `ambiguous` |
| 缺分號／缺左括號／缺右括號 | `ambiguous` |
| 括號與分號被改成半形 | `ambiguous` |
| 查核段整段缺失（執行段完整） | `ambiguous` |
| 執行段舊式但查核段新式 | `ambiguous` |
| 路由行前綴混入零寬／格式字元（U+200B、U+FE0F） | `ambiguous` |
| 層級值內混入零寬／格式字元 | `ambiguous` |
| 層級值前後有空白、行尾有多餘空白 | **`matched`／`deviated`**（空白不帶語意，`strip` 後查表） |
| 理由欄含「依建議降級」等字樣（其餘合格） | **`matched`／`deviated`**（內容不參與版本判定） |
| **無版本標記**，自由文字含「建議」「主力型」等詞 | `absent`（內容不參與版本判定） |

上表每一列都有對應測試。破壞類的每一列另有一條「Log 不得寫成『卡面無建議層級』」斷言，
舊卡類的每一列另有一條「Log 必須寫『卡面無建議層級』而非『偏離』」斷言。

兩個刻意的取捨：

- **`absent`／`ambiguous` 也要理由**，不比照 `matched` 放行。這兩格代表**沒有可比對的
  基線**，不是「比對過且相符」；當成相符放行等於用沉默宣稱一致性。與本 CLI 既有慣例
  一致——`assign` 對**目標卡自己**的資源宣告解析失敗同樣是 fail closed。代價只是舊卡
  派工時多打一個 `--capability-deviation-reason`。
- **`absent` 的 Log 不得寫成「偏離」**：沒有建議就沒有東西可偏離，寫成偏離是不實留痕。
  四格各自措辭，`log_fragment` 沒有共用的模糊字串，未知結果態直接拋例外。

理由政策存在顯式表（`_REASON_REQUIRED_BY_OUTCOME`），不是 `if/else` 加預設值：日後新增
結果態卻忘了決定政策，`requires_reason` 會 `KeyError` 當場炸，而不是靜默沿用「不需要」。

#### ⚠️ 卡面建議只在 Issue body 裡，解析有脆弱性

`project.FIELD_SPECS` 的 13 個凍結欄位**沒有任何一個**存能力層級（不新增欄位的理由見
下方「不進 Project 凍結欄位」），所以 `assign` 只能解析 Issue body 第 2 行。這是隱含
前提會出事的地方，明列如下：

1. **依賴渲染形狀**：解析器與 `format_routing_line` 同檔，並有 render → parse 的
   round-trip 測試；改了渲染卻忘了改解析會當場紅。兩支正規表達式刻意分開維護
   （測試那支是照 `templates/tasks-card.md` 寫的獨立 oracle），否則測試會變成套套邏輯。
2. **依賴 body 沒被手改壞**：因此**不猜**——版本由 `<!-- wf-routing:v1 -->` 標記機械
   判定，標記在而讀不出合格建議一律 `ambiguous` 要求理由，不「當作沒有建議」悄悄放行
   （分界與破壞方式列舉見上）。**內容永遠不參與版本判定。**
3. **只讀 `## Log` 之前的區段**：Log 會引用被 `amend` 掉的舊值原文，其中可能含字面的
   `- 執行：…（建議 …）`；不切掉就會把歷史當成現況讀。有專門測試鎖這條。

## `amend`：開卡後的卡面修訂（WF-CLI-CARD-AMEND1）

```bash
# 改 spec 基線（上游卡 merge 後）
wfcli amend CARD-ID --repo owner/repo --reason "上游卡已 merge" --spec-baseline "main <sha>"

# 整份替換驗收條件（預設全部重設為未勾選；要沿用原勾選加 --preserve-checked）
wfcli amend CARD-ID --repo owner/repo --reason "需求方追加" \
  --acceptance "條件一" --acceptance "條件二"

# 整份替換驗證項目（用法同 --acceptance）
wfcli amend CARD-ID --repo owner/repo --reason "查核裁定改寫" \
  --verification "驗證一" --verification "驗證二"

# 改資源宣告：--resources 整份取代（空字串代表清空），--db-scope 單獨改 scope
wfcli amend CARD-ID --repo owner/repo --reason "範圍調整" \
  --resources "file:a.py,file:b.py" --db-scope read

# 更正級別（`WF-CLI-TIER-MUTATION1` 併入本指令）
wfcli amend CARD-ID --repo owner/repo --reason "開卡時填錯" --tier T3
```

可同時給多個欄位；**任一欄位驗證失敗就整批不寫**，不留半套修改。

`--dry-run` 零遠端寫入，可先看將寫入什麼。

### 併發保證的界線

`amend` 每次都是**整份重寫 body**。寫入前會重讀並比對 body，被他人改動時以退出碼 6
中止而不覆寫——但這**不是**原子的 compare-and-swap：GitHub 對 issue body 沒有條件
寫入，重讀只把競態窗口從「整條指令執行期間」縮到「重讀與寫入之間」。真正的解法是
可序列化的唯一 writer 或底層條件寫入，不在本指令能提供的保證內。

### 半寫入的恢復（退出碼 5）

`--tier` 會先寫 Project 欄位、讀回驗證，再寫 body。若讀回驗證失敗（退出碼 5），body
一定沒被寫入，但欄位可能已改——此時卡處於「欄位改了、Log 沒記」。恢復步驟：

```bash
# 1. 先確認 Project 的級別實際值
# 2a. 若已是目標值 → 只補 Log、不再改欄位
wfcli amend CARD-ID --repo owner/repo --tier T3 --record-unlogged-change \
  --reason "先前寫入於讀回驗證階段中斷，補記留痕"
# 2b. 若仍是舊值 → 直接重跑原本的 amend
```

`--record-unlogged-change` 是**操作者的宣告，不是系統的自動證明**。CLI 無法區分
「欄位已是目標值且 Log 沒記」到底是先前半寫入、還是開卡時本來就填這個值，所以不猜；
它只補留痕、不改欄位，欄位不符時直接拒絕，避免變成偷改欄位的後門。

### 為什麼沒有排版修復

body 的 `## Log` 若被寫成字面 `\n`（曾實際發生於 ai-workflow#17），`amend` 會拒絕
一切修訂以免誤動 Log，且**不提供自動修復**。

曾經有過 `--repair-log-layout`，做了三輪查核後移除。移除的理由不是做不出來，而是
成本與價值不成比例：三輪查核加一次自我對抗測試，累計在同一個旗標上找到五個安全
破口，每一個都是同一類錯誤——拿「聽起來像不變量」的論證當安全保證。依序是：對整份
body 無差別替換（JSON 字串裡的 `{"note": "a\nb"}` 被改壞，而比較基準預先刪掉字面
`\n`，等於把破壞藏進證明裡）；限縮起點但仍對尾段無差別替換（Log 敘述中合法的字面
`\n` 被改掉、fenced code block 內的標記被誤認為 Log 起點）；以及 fence 偵測只看得見
反引號圍籬，`~~~` 圍籬、縮排區塊、行內碼三類在 body 沒有真 Log 時全數失守。

而它服務的損壞形態，正是 `gh issue edit` 直接寫 body 造成的——`amend` 上線後那條路
本來就該關。為一個「上線後不該再發生」的一次性歷史事件，維護一個難以證明安全的
改寫器並不划算。

#### 備案：可執行的人工程序 ＋ 機械驗證必要條件

「沒有自動修復」不等於「沒有出路」。`amend` 偵測到排版損壞時，除了拒絕，還會在 stderr
印出下列程序（含實際卡號）。核心設計是**工具不改 body，只機械驗證必要條件；語意判斷
留給人**——工具能證明的是「只改了那一處」，不是「那一處是對的」：

> ⚠️ 下列所有機械檢查都是**必要條件，不是安全證明**。是否真的修對了，最終由人判斷。

```bash
# 1. 取出現行 body，並另存一份原文副本供比對
gh issue view <N> --repo <owner/repo> --json body --jq .body > /tmp/body.md
cp /tmp/body.md /tmp/orig.md

# 2. 人工判斷（無法機械化）：確認 `\n## Log\n\n` 候選標記確實是被寫壞的 Log 標題，
#    而不是 code fence 內的範例、inline code 引用、或內文提到的字樣。

# 3. 編輯 /tmp/body.md：只把那一處的字面 \n 改回真換行，不動任何其他字元。

# 4. 檢查「只改了那一處」（必要條件）
python3 - /tmp/orig.md /tmp/body.md <<'PY'
import sys
o = open(sys.argv[1]).read(); n = open(sys.argv[2]).read()
t = "\\n## Log\\n\\n"; f = "\n\n## Log\n\n"
c = o.count(t)
if c != 1:
    print(f"NG：原文有 {c} 處候選標記，本程序只處理恰好 1 處。請人工判斷後個別處理")
elif o.replace(t, f, 1) != n:
    print("NG：除了那一處之外還動到別的地方，請重做")
else:
    print("必要條件通過：只還原了那一處候選標記。")
    print("⚠️ 這不是安全證明——本檢查無法判斷它是否真的是 Log 標題。")
    print("   請自行確認它不在 code fence／inline code／內文引用中，並審閱完整 diff。")
PY

# 5. 審閱完整 diff——不可省略，這是唯一能看見全部改動的地方
diff /tmp/orig.md /tmp/body.md

# 6. 寫回
gh issue edit <N> --repo <owner/repo> --body-file /tmp/body.md

# 7. 確認 amend 不再回報排版錯誤（必要條件，非充分）
wfcli amend <CARD-ID> --repo <owner/repo> --reason 驗證排版 --dry-run --spec-baseline '<現值>'

# 8. 在該 Issue 留言記錄這次人工寫入與原因
```

這個備案**不宣稱能機械證明修對了**。第 4 步只驗證兩件事：候選標記恰好一處，且除了
那一處之外沒有其他改動。它**無法**判斷那處標記是不是真的 Log 標題——查核者實測打穿過
兩次：多處候選時只修第一個卻仍印通過；code fence 內的標記被誤修後，`split_at_log` 還會
把它當成唯一的 Log 標題。因此語意判斷明確留給第 2 步的人工確認與第 5 步的完整 diff。

第 7 步的 `--dry-run` 同理：它只證明「找得到唯一一個 Log 標題」，不證明那個標題在對的
位置，也不保證 body 其他地方沒有殘留的字面 `\n`。

該驗證指令與 `amend` 印在 stderr 的那一份是**同一個常數**（`_LAYOUT_VERIFY_SNIPPET`），
並由測試實際執行——先前的版本只存在於字串裡、從未被跑過，同時出了兩個錯（引用一個從未
建立的 `orig.md`；以及用「刪掉全文所有字面 `\n` 再比」當判準，導致 #17 的正確修復被誤判
為竄改）。

#### `--escalate`：讓卡住這件事被看見

stderr 是瞬時的。腳本裡跑 `amend` 失敗，runbook 捲過去就沒了，卡面不留痕跡，沒人知道
有卡卡住。加 `--escalate` 時，排版損壞會在該 Issue 留下一則求助留言（含機器可 grep 的
`<!-- wf-amend-blocked:v1 ... -->` 標記與完整 runbook），交給人或 AI 接手：

```bash
wfcli amend <CARD-ID> --repo <owner/repo> --reason "..." --spec-baseline "..." --escalate
```

三個刻意的界線：

- **不碰 body**。body 已經壞了，再寫更危險；留言是唯一不必動 body 就能留下持久紀錄的通道。
- **不改交付狀態**。轉 `⏸阻塞` 是 lifecycle 決定，屬 PM 的判斷，不由一個修訂指令代勞。
- **只對排版損壞生效**。一般拒收（no-op、格式錯）不留升級紀錄，避免訊息噪音。

**這類損壞同時是一個訊號**：它代表某處仍在繞過 `wfcli` 直接寫 body。修完請一併追查來源。

## `review`：查核輸出契約的機械閘門（WF-22-CLI3）

```bash
# 查核者送審前自檢：只驗格式，完全不連 GitHub
wfcli review WF-22-CLI3 --input report.md --source-sha <40hex> --reviewer Codex --validate-only

# 祕書寫入裁決（真實副作用需 --repo）
wfcli review WF-22-CLI3 --repo ruan6047/ai-workflow --input report.md \
  --source-sha <40hex> --reviewer Codex
cat report.md | wfcli review WF-22-CLI3 --repo ... --source-sha <40hex> --reviewer Codex
```

`--input` 吃**整份查核報告**（散文＋圍籬區塊），自動抽出含 `review_result` 的
```` ```yaml ````／```` ```json ```` 區塊；抽到兩個以上一律拒收（不用「取最後一個」
這種順序啟發式猜哪個是裁決）。退出碼：

- `0` 通過並已寫入（或 `--validate-only` 驗證通過）
- `2` 讀不到／解析失敗／契約檢查失敗（含 `APPROVE` 帶 blocking finding、
  `REQUEST_CHANGES` 零 finding 兩條硬拒）／缺必要旗標——**未寫入任何遠端狀態**
- `3` 找不到卡
- `4` `review-invalid`（`templates/review-escalation.md` §1）：目前可機械判定的是
  「`APPROVE` 未附 `self_run`」；§1 規定此情形留在 `🔍待查核`、不計 iteration，
  所以刻意什麼都不寫

## 跨專案目標指定

```bash
wfcli open --owner ruan6047 --project 4 CARD-ID ...      # 明打旗標
wfcli open --config .wfcli.json CARD-ID ...               # 讀設定檔 {"owner":...,"project":...,"repo":...}
WFCLI_OWNER=ruan6047 WFCLI_PROJECT=4 wfcli open CARD-ID    # 環境變數
```

`--repo owner/repo` 有給時，`open` 建立**真實 repo Issue**（`gh issue create` + `gh project
item-add`）；未給則建立**Project draft issue**（無 repo 掛載，`gh project item-create`）。
兩種模式的 Ledger 欄位讀寫、資源宣告解析、`assign`／`handoff` 邏輯完全一致。

## 凍結欄位結構（`OPS-STATE-PLANE-MIG1` Task 1 + 需求方裁決）

13 個 Ledger 欄位對照 GitHub Project custom fields（`src/wf_cli/project.py::FIELD_SPECS`
是唯一事實來源，`ensure_fields` 冪等建立缺少的欄位）：

- TEXT：卡ID、Initiative、功能、owner、分支worktree、最後交接、服務的原始目標、資源宣告（摘要）
- NUMBER：iteration、鏈深
- SINGLE_SELECT：級別（T0–T4）、交付狀態（13 值，含 canonical §0 全集＋實務常見值）、部署狀態（7 值）

**最後交接**＝TEXT 完整 ISO-8601（`isoformat(timespec="seconds")`，例如
`2026-08-04T22:47:51+08:00`）：字典序即時序，不用 DATE（其 API 層會靜默截斷時分秒）。

**資源宣告**的 machine-of-record 是卡片 body 內固定的 `## 資源宣告` 區塊：

```
## 資源宣告
<!-- resource-claims:begin -->
```json
{"db_scope": "write", "resources": ["file:a.py", "port:8080"]}
```
<!-- resource-claims:end -->
```

Project 上的「資源宣告」TEXT 欄位只放人類可讀摘要，不參與 `assign` 的交集比對；
機械比對一律解析 body（`src/wf_cli/resources.py`）。刻意不用 `MULTI_SELECT`（GitHub
GraphQL schema 確實存在但未文件化、`gh` CLI 未曝露，见 Task 1 field-mapping 文件的
「意外發現」節）。

## 設計取捨（讀程式碼前建議先看這裡）

- **`assign` 的資源衝突比對範圍限定「已認領」的活卡**（owner 不是「待指派」等佔位
  字串）。單純兩張卡都在 Backlog、都規劃碰同一檔案，不會互相卡住——真正的風險是
  「兩張卡同時有人在執行」，這才是 worktree／資源撞車的實際情境。
- **`doctor` 是唯讀報告工具，不做任何清理／回收**。卡面紅線 3 要求破壞性操作「先列
  清單再執行」；本卡刻意把「列清單」與「執行清理」拆成兩個決策點，v1 只做前者。
- **`doctor` 的孤兒 worktree 判準**：`git worktree list --porcelain` 逐一分類——
  `prunable` 直接算孤兒；`detached` 但非 prunable 視為查核用 disposable worktree
  （worktree-lifecycle.md §3 認可的型態），**不**算孤兒；其餘依分支名稱比對卡註冊
  （TASKS.md Ledger 或 GitHub Project），對不上才算孤兒。這代表 doctor 找到的孤兒是
  「未見於任何活卡登記」，不是「保證真的沒人在用」——例如一個尚未正式開卡、但有人
  正在裡面工作的暫時性 worktree，也會被列出來，這是刻意的（見下方「已知限制」）。
- **殘留 lease 是啟發式，不是判決**：(a) 註冊的 worktree 路徑在磁碟上不存在＝機械
  確定的訊號；(b) 最後交接超過可設定的 TTL（預設 48h）＝時間啟發式，只供人工判斷，
  不觸發任何自動回收。
- **`deploy-declare` 是既有卡部署分類的唯一更正入口**：只在需求方明確決策後使用，
  固定要求 `--decision needs-deploy` 與非空 `--reason`，且只允許
  `—不適用 → ⏸未部署`。它不是 `deploy-state` 的跳轉例外；其餘重分類、重複宣告、
  跳級與倒退全數拒絕。新卡仍由 `open --needs-deploy` 決定初始分類。
- **`deploy-state` 是部署狀態的唯一中間轉移入口**：它只允許
  `⏸未部署` 後的相鄰前進轉換。
  內建 `Status` 固定映射為 `⏸未部署`／`🚀待部署`→`Todo`、
  `⏳部署中`／`✅已部署`／`🧪驗證中`→`In Progress`、`✅已驗證`→`Done`；Project
  缺少對應 option 一律拒絕，不以色彩或順序猜測。命令不建立或修改任何 Project
  欄位定義，所有 item 值都走 `updateProjectV2ItemFieldValue`。需要真實 repo Issue，
  draft item 直接拒絕，避免失去 timeline event。
- **`doctor` 的卡註冊來源可插拔**（`--registry tasks-md|none`）：`tasks-md` 解析
  `docs/TASKS.md`／`TASKS.md`（未 cutover 專案的現行事實來源）；未來完全 cutover 的
  repo 可改用 GitHub Project 作為登記來源（`src/wf_cli/registry.py` 留了擴充點，
  v1 未實作 `github` 模式，因為本卡驗收的唯讀對帳目標——cpbl-analytics——尚未
  cutover，`tasks-md` 已足夠覆蓋卡面驗收）。
- **鏈深與 iteration 的寫入路徑**（WF-22-CLI2）：`open --chain-depth` 與 `handoff`
  的 iteration 遞增在 CLI1 交付時只有底層 `set_field_value` 能寫、組裝層沒接，兩個
  凍結欄位形同虛設 0。`--chain-depth`＝原始目標之下第幾層，> 2 依決議 5「鏈式停損
  協定」在 `validation.validate_chain_depth`（CLI 層）與 `Card.__post_init__`（model
  層，供繞過 CLI 直接建構 Card 的呼叫端）雙重擋下，訊息固定引用「整鏈重審」與
  「決議 5」（`card.chain_depth_violation_message`，兩層共用同一段文字避免漂移）。
  iteration 遞增接點依需求方 2026-08-05 裁決：`handoff --next-stage implementation`
  （承載「查核退回」語意）讀回現值＋1 寫回；`review`／`release` 不遞增；`--iteration
  N` 是顯式覆寫逃生門（印警示，覆寫理由說明於既有必填的 `--evidence`，不另立欄位）。
- **規劃期路由不進 Project 凍結欄位**（WF-CLI-ROUTING-TIER1）：建議能力層級與理由只
  寫進卡面（Issue body 第 2 行＋git spec 檔），不新增 `FIELD_SPECS` 欄位。它是**規劃期
  的一次性建議**，不是會被 `assign`／`handoff` 持續改寫的 current-state；真正會變動的
  是「實際派到誰」（owner 欄）與偏離理由（claim 事件）。凍結欄位只放 current-state，
  多開一欄反而製造第二個真相來源。**代價**：`assign` 因此只能解析 Issue body 取得建議，
  該路徑的脆弱性與應對見上方「卡面建議只在 Issue body 裡」。
- **`review` 不碰 iteration／owner／最後交接**（WF-22-CLI3）：iteration 的唯一遞增點
  是 `handoff --next-stage implementation`，review 若也動就會讓一次退回被記成兩次；
  裁決也不是交接，所以 owner 與最後交接同樣留給 `handoff`。`review` 只寫兩件事——
  Issue 留言（裁決全文；canonical §4.3「事件＝Issue timeline ＋結構化 comment」）與
  交付狀態，另在 body `## Log` 補一行索引。
- **`review` 先留言、後翻狀態**：反過來若留言失敗，板上會留下沒有裁決全文的
  `✅通過`，那正是本卡要消滅的「宣稱與證據脫節」。
- **`APPROVE` 不得含 `blocking: true` 的 finding**（硬拒，exit 2）：有阻斷缺陷卻核可
  是語意矛盾，二擇一——改 `REQUEST_CHANGES`，或把該 finding 改為 `blocking: false`。
  需求方 2026-08-06 裁決（[`ruan6047/ai-workflow#8`](https://github.com/ruan6047/ai-workflow/issues/8) 查核留言），由警示升為硬拒。
- **`REQUEST_CHANGES` 不得零 finding**（硬拒，exit 2）：退回必須附至少一項可執行
  finding，否則執行者無從修起。與「`findings` 鍵須顯式存在」的互動：顯式寫
  `findings: []` 搭配 `REQUEST_CHANGES` 現在同樣被擋（顯式不等於豁免）。
  需求方 2026-08-06 裁決（[`ruan6047/ai-workflow#8`](https://github.com/ruan6047/ai-workflow/issues/8) 查核留言）。
  兩條的判準都在 `validation.validate_review_report`，且只在 finding 本身解析乾淨時
  才判——否則作者會同時看到「缺欄」與由缺欄衍生的矛盾訊息，被導去修錯的地方。
- **`review` 自己寫受限 YAML 子集解析器，不引 PyYAML**：除了零第三方 runtime 相依，
  更關鍵的是寬鬆解析與 fail-closed 互斥——YAML 1.1 會把 `yes` 讀成布林、重複鍵靜默
  取最後一個。這裡只認 review-prompt.md §5 已經在用的固定子集（頂層純量、`- key:
  value` mapping 序列、`[]`、`|`／`|-` 區塊純量），語法之外一律拒收；```json 區塊走
  `json.loads`，兩條路徑收斂到同一套契約檢查。
- **`review` 的行內註解規則**：`key:   # 說明` 與 `review_result: APPROVE  # 說明`
  這種「整段註解」或「單 token ＋註解」會切掉註解（範本每行都帶註解，照抄填值是最
  常見用法）；但**片語後接 `' #'` 一律拒收**（`evidence: 見 PR #12` 若照 YAML 砍註解
  會靜默截成 `見 PR`——截斷的 audit 記錄比被拒收糟），要求作者加引號。

## 已知限制

- `doctor` 無法分辨「未登記的 worktree」是真孤兒還是「有人正在用、只是還沒開卡」；
  這需要人類或另一層「哪些 session 目前存活」的資訊，本 CLI 不越權猜測。
- `assign`／`handoff` 對別卡（非本次目標卡）解析不出資源宣告時只警告、不擋——遷移期
  間舊卡尚未補宣告不該讓新卡整個卡死；目標卡自己解析失敗則直接拒絕（fail closed）。
- 目前只有 `open` 會做「重複卡ID」檢查；`assign`／`handoff` 找不到卡ID時回報「找不到
  卡」（exit 3），不會嘗試模糊比對或自動建卡。
- `review` 只能機械判定 `review-escalation.md` §1 六種 `review-invalid` 中的**一種**
  （`APPROVE` 未附 `self_run`）。查核順序、環境污染、reviewer 獨立性、審錯 artifact、
  同一 reviewer 對同一 SHA 重複回報都需要 CLI 拿不到的事實，由 Coordinator 判定——
  本指令不假裝能判定，但也不因此放行。
- `review` **不計算 `counts_toward_escalation`、不標記 `accepted`／`status`**
  （§2／§3 規定由 lifecycle writer 依可重現證據標記，reviewer 不得自決）；查核輸出裡
  出現這些 writer-only 欄位只會被警示並忽略。escalation 帳（epoch、attempt 去重、
  checkpoint）目前仍在 CLI 之外。
- `review` 只擋格式與契約，**不驗查核者的獨立性**（跨模型家族／人工）——`--reviewer`
  是自陳字串。canonical §5 的獨立性紅線仍由治理承擔。
- `review` 需要真實 repo Issue（`--repo`）：Project draft item 沒有 timeline 可留言，
  會被拒絕而不是退化成「只翻板狀態」。

## 專案結構

```
cli/
├── pyproject.toml
├── src/wf_cli/
│   ├── gh.py            # gh CLI／graphql 底層包裝（唯一 subprocess 出口）
│   ├── project.py        # Projects v2 adapter：欄位、item 建立、批次讀取
│   ├── resources.py      # 資源宣告 schema、fenced JSON 解析／渲染、交集比對
│   ├── review.py          # 查核輸出結構：區塊抽取、受限 YAML 子集解析、裁決留言渲染
│   ├── card.py           # Card model、spec／Issue body 範本渲染、Log 附加
│   ├── validation.py      # SHA／證據／必填欄／查核輸出契約的機械檢查
│   ├── registry.py        # TASKS.md Ledger 解析（doctor 的卡註冊來源）
│   ├── git_ops.py         # 唯讀 git worktree／submodule／branch 操作
│   ├── doctor.py          # 對帳邏輯（組合 git_ops + registry）
│   ├── snapshot.py        # JSON／Markdown Ledger 渲染
│   ├── config.py          # --owner/--project/--repo/--config 目標解析
│   ├── cli.py             # argparse 組裝＋錯誤處理
│   └── commands/          # 六個子指令的 argparse handler
└── tests/                  # pytest：純邏輯＋真實 sandbox git repo＋FakeGhRunner（數量見 uv run pytest）
```
