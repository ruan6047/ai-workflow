# 範本異動對照（`WF-REDESIGN-W2B`）

> 本檔是 `WF-REDESIGN-W2B` AC1 的**封閉 mapping**：舊 → 新逐檔對照，各附 falsifier。
> ⛔ 本檔不是範本，⛔ 不要拿它組裝任何交接文件。它存在的唯一理由是：被移除的檔會在
> 歷史、註解與外部引用裡繼續出現，而讀者需要一個**指得到的地方**知道它們去哪了。
> ⚠️ 本檔自身是 mapping 文件，故「舊入口零引用」的 falsifier **把本檔排除在外**——
> 否則那條檢查會被本檔的存在永久卡住。

## 1. 被移除的五檔（封閉集合，⛔ 非六檔）

| 舊檔 | 處置 | 承接者 | falsifier（什麼觀察會讓本列不成立） |
|---|---|---|---|
| `templates/tasks-card.md` | **移除** | **卡面 fenced JSON——⭐ 今天就在跑**（`cli/src/wf_cli/card_face.py` 的 `card-face-form:v1`；卡面 `#220` body 實查含 `resource-claims:begin`／`card-face-form:v1:begin`／`card-brief:begin`／`wf-routing:v1` 四個標記）。`WF-REDESIGN-W3` 的 AC2 逐字是「**只擴充／消費 W1 的 v1 schema**」，⛔ 不是「屆時才落地」。規格單一居所＝卡面 body ＋ `spec_version` | 檔案仍存在；或 `card_face.py` 查不到 `card-face-form:v1` 的實作；或某張卡的 body 取不到那四個標記 |
| `templates/bug-card.md` | **移除** | 缺陷走**待審清單項＋一般卡**，⛔ 不另立卡種——條文居所＝[`../stage-rules/defect-path.md`](../stage-rules/defect-path.md) 一（`WF-REDESIGN-W2B` 新寫，需求方 2026-09-01 裁定 1 授權） | 檔案仍存在；或 `stage-rules/defect-path.md` 查不到「⛔ 沒有 bug 專屬卡種」這條 |
| `templates/bug-workflow.md` | **移除** | 分級判準與留痕分流移入 [`../stage-rules/defect-path.md`](../stage-rules/defect-path.md) 二／三；canonical §3 的分級句已同批**指路更正**指向該檔。⚠️ **更正本卡首版**：首版寫「判準已在 `tier-rules.md`」是**過度宣稱**——`grep -cin "bug\|缺陷" tier-rules.md` ⇒ **0** | 檔案仍存在；或 `stage-rules/defect-path.md` 查不到分級表；或 canonical §3 仍指向本檔 |
| `templates/initiative-card.md` | **移除** | 父卡模型的本體住 **canonical §3**（目標／spec 基線／依賴圖／里程碑／決策與風險）＋ [`baseline-cascade.md`](baseline-cascade.md)（基線變更的凍結、影響評估與傳播）；[`../stage-rules/planning.md`](../stage-rules/planning.md) 承接「父卡：子卡切片與依賴序」。⚠️ **更正本卡首版**：首版寫「住 `stage-rules/`」是**位置錯**——該目錄只有切片與依賴序那半句 | 檔案仍存在；或 canonical §3 查不到父卡的目標／基線／依賴圖／里程碑／決策與風險 |
| `templates/TASKS.md` | **移除** | 狀態面（GitHub Project）；現況一律用查詢指令取 | 檔案仍存在；或有專案被要求建一份 `docs/TASKS.md` Ledger |

⚠️ **移除 ≠ 修復。** 這五份的欄位有一批在契約 ↔ 工具對帳表上判為缺口（工具側完全不渲染）。
移除讓那些符號**離開契約 universe**，⛔ 不是讓工具長出渲染能力——工具側一行都沒有增加。
逐符號的處置見 [`../docs/CONTRACT_TOOL_RECONCILE.md`](../docs/CONTRACT_TOOL_RECONCILE.md) §7。

## 2. 新增與改寫（六檔）

決議紀錄 §六列的**五份交接文件**＋結案報告。六份共用同一個四段信封，定義在
[`handoff-contract.md`](handoff-contract.md) §3.3。

| 檔 | 狀態 | 是什麼 | 誰寫 |
|---|---|---|---|
| [`dispatch-package.md`](dispatch-package.md) | 改寫 | 派工包 | PM |
| [`delivery-report.md`](delivery-report.md) | 新 | 交付報告（⭐ 是 ③ 的一部分） | 執行者 |
| [`review-dispatch.md`](review-dispatch.md) | 新 | 派審詞（派審信封） | PM |
| [`verdict.md`](verdict.md) | 新 | 裁決（人讀範本） | 查核者 |
| [`status-change-ruling.md`](status-change-ruling.md) | 新 | 狀態變更裁定單 | PM 準備、需求方裁定 |
| [`closeout-report.md`](closeout-report.md) | 新 | 結案報告（一屏七段） | PM，④ 由需求方 |

**存在性判準（falsifier）＝檔案存在 ＋ 含信封四段標題**，一條指令跑得出來：

```bash
for f in dispatch-package delivery-report review-dispatch verdict status-change-ruling closeout-report; do
  n=$(grep -c '^## 信封[一二三四] · ' "templates/$f.md")
  [ "$n" = 4 ] && echo "OK   $f" || echo "FAIL $f（信封段數 $n，應為 4）"
done
```

⛔ 段數不是 4 即本列不成立。⛔ 不得以「四段的意思有寫到」代替四個標題——判準是 grep 得到，⛔ 不是語意等價。

### 2.1 保留改寫：`review-prompt.md`

[`review-prompt.md`](review-prompt.md) **保留**，因為 `wfcli review` 把它的 §5 當成寫入前的
機械閘門，`cli/src/` 有六個檔逐處引用它的節次（`review.py`／`validation.py`／
`commands/review_cmd.py` 引 §5，`card.py`／`commands/amend_cmd.py` 引 §2，
`replay_escalation_rules.py` 引 §6；另 [`review-escalation.md`](review-escalation.md) 引 §6）。

改寫的內容是**分工**，⛔ 不是節次：

- `review-prompt.md` §5 ＝ **schema**（機器面；欄位與列舉的權威居所）
- [`verdict.md`](verdict.md) ＝ **人讀範本**（同一次裁決寫給人看的那一份）
- [`review-dispatch.md`](review-dispatch.md) ＝ **派審信封**（PM 交給查核者的那一份）

**falsifier**：`review-prompt.md` 的 `## 1.`–`## 6.` 六個節次編號若有任何一個改動、
或 §5 的 yaml 區塊不再含 `core_pain_resolved`／`review_result`／`self_run`／`findings` 四個鍵，
本列不成立。一條指令：

```bash
grep -c '^## [1-6]\. ' templates/review-prompt.md   # 應為 6
for k in core_pain_resolved review_result self_run findings; do
  grep -q "^$k:" templates/review-prompt.md || echo "FAIL 缺 $k"
done
```

## 3. 「舊入口零引用」的 falsifier 與現況

AC1 要求被移除各舊檔於 post-image `git grep` 檔名驗零引用。

**排除集的唯一權威居所＝下方 §3.1**（機械產生），四項具名，依需求方 2026-09-01 裁定 3。
⛔ **本節⛔ 不另立第二套排除規則**——`WF-REDESIGN-W2B` R1-2 抓到的正是本處曾與 §3.1 並存
兩套互斥政策（舊版在此宣告「母體排除三項」且整個 `docs/research/` 都排除），讀者無法判定
該跑哪一套。舊政策已刪除，⛔ 不得回寫。

母體內的命中**逐筆三分類，⛔ 全部可見列計**——分類⛔ 不是豁免（沿
`scripts/pollution_check.py` 的自指命中設計）。**單位＝唯一 `(檔, 行)`**，⛔ 不是 occurrence：

| 類 | 是什麼 | 判準 |
|---|---|---|
| **A** 現行入口殘留 | 本卡改得動、卻仍把被移除檔講得像現行 | ⭐ **必須為 0**；非 0 即本卡缺陷 |
| **B** 移除紀錄／合成語料 | 同行逐字標明已移除者；逐項處置表與歷史小節（以檔內 marker 界定）；對帳器在臨時目錄造同名檔的合成語料 | 構造上⛔ 不是入口 |
| **C** 授權外 | 本卡寫入授權外的檔（派工包 §2「其餘一律唯讀」） | ⛔ 不自行擴權，逐項上呈需求方 |

⭐ **B 以逐行判準與檔內 marker 界定，⛔ 不以檔名整檔排除**——有人把新的引用寫在 marker 之外、
或寫一行沒有「已移除」字樣的引用，它會落回 A 而不是靜默通過。五條分類規則逐字見 §3.5。

<!-- old-entry-residual:begin -->

> 本區塊由指令產生，⛔ 非手寫。重跑見本節末的完整指令。

**單位＝唯一 `(檔, 行)`。** ⛔ 逐名 `git grep -c` 相加會把同一行含兩個檔名的情形重複計入——本卡首版即因此報出偏高的數字，已登記為失誤。

套用排除集後：**A 現行入口殘留（授權內）0**／B 移除紀錄與合成語料 54／C 授權外 15。

⭐ **通過判準只有一條：A ＝ 0。** B 與 C ⛔ 不是豁免，是**分類**——逐檔列計，⛔ 不從母體拿掉。

### 3.1 排除集（具名＋理由＋load-bearing）

⛔ **不得整目錄排除 `docs/research/`**——`scripts/prose_number_scan.py` 的語料**含** `docs/research/drafts/wave-specs/*.md`，整目錄排除與既有守衛的納管作法直接衝突（需求方 2026-09-01 裁定 3）。形狀沿用 `scripts/canonical_citation_scan.py` 的 `EXCLUSIONS`。

| 排除項 | load-bearing 增量（唯一 `(檔,行)`） | 理由 |
|---|---|---|
| `templates/template-migration-map.md` | 6 | 卡面 AC1 逐字「mapping 文件自身除外」——本檔即該 mapping 文件。 |
| `archive/` | 3 | 已結案卡的歷史紀錄⛔ 不是現行入口，改寫它等於改寫已結案的帳（需求方 2026-09-01 裁定 3 准）。另：`scripts/prose_number_scan.py` 的語料本就不含 `archive/`，兩個守衛的納管界線一致。 |
| `docs/research/drafts/wave-specs/w2b.md` | 2 | 本卡自己的來源草稿；規格權威居所是卡面 body，該檔於結案時封存（PM 開卡留痕）。 |
| `docs/research/drafts/wave-specs/baseline-universe.json` | 1 | AC2 自己釘死的基線 artifact——它逐字載著被移除範本的 doc_hits，把它算成「入口」等於要求 AC2 的基線刪掉自己的內容。 |

⭐ **欄位口徑逐字**：`load-bearing 增量` ＝**拿掉該排除項後，唯一 `(檔,行)` 總數的增加量**（⛔ 不是該項命中的 occurrence 數——`WF-REDESIGN-W2B` R1-3 抓到的正是這兩個口徑被混用）。⭐ **排除集⛔ 不是垃圾桶**：任一項增量為 0 即判**死條目**，本節轉紅（沿 `canonical_citation_scan` 的 load-bearing 檢查）。　**本次：無死條目。**

### 3.2 A · 現行入口殘留（授權內）：0

（無）

### 3.3 B · 移除紀錄與合成語料（在母體內、⛔ 非入口）：54

| 檔 | 唯一 (檔:行) 命中 | 分類理由 |
|---|---|---|
| `ADOPTION.md` | 3 | 同行逐字標明該檔已移除 |
| `AI_WORKFLOW.md` | 2 | 本卡依需求方裁定 2 就地註記為「由 `WF-REDESIGN-W2B` 移除」並指向 mapping 文件 |
| `cli/tests/test_contract_tool_reconcile.py` | 3 | 對帳器合成語料（臨時目錄造同名檔），命中的是字串常數 |
| `docs/CONTRACT_TOOL_RECONCILE.md` | 42 | marker 界定的移除紀錄區塊（逐項處置表／歷史小節） |
| `stage-rules/defect-path.md` | 4 | 同行逐字標明該檔已移除 |

### 3.4 C · 授權外：15

| 檔 | 唯一 (檔:行) 命中 | 分類理由 |
|---|---|---|
| `cli/README.md` | 3 | 未列入本卡寫入授權（授權只到 `cli/tests/test_contract_tool_reconcile.py`） |
| `cli/src/wf_cli/card.py` | 7 | `cli/src/**`＝`WF-REDESIGN-W3` 射程；派工包逐字標唯讀 |
| `cli/src/wf_cli/card_face.py` | 1 | `cli/src/**`＝`WF-REDESIGN-W3` 射程；派工包逐字標唯讀 |
| `cli/src/wf_cli/registry.py` | 1 | `cli/src/**`＝`WF-REDESIGN-W3` 射程；派工包逐字標唯讀 |
| `cli/src/wf_cli/resources.py` | 1 | `cli/src/**`＝`WF-REDESIGN-W3` 射程；派工包逐字標唯讀 |
| `cli/tests/test_card.py` | 1 | 未列入本卡寫入授權 |
| `cli/tests/test_commands_mocked.py` | 1 | 未列入本卡寫入授權 |

⭐ C 的每一筆都是註解／docstring，⛔ 沒有一處是會被執行的碼（實測：移除五檔後 `cli/` 全套測試仍全綠）⇒ 懸空指標。⚠️ 本卡首版曾把 `ADOPTION.md` 一併說成「只是註解」——**那是錯的**，該檔 §2 是人工執行程序，已依需求方裁定 2 就地註記，現歸 B。

### 3.5 完整重跑指令

```bash
cd <worktree>
for f in tasks-card.md bug-card.md bug-workflow.md initiative-card.md templates/TASKS.md; do
  git grep -n --fixed-strings -- "$f"
done \
  | grep -Ev '^templates/template-migration-map\.md:' \
  | grep -Ev '^archive/' \
  | grep -Ev '^docs/research/drafts/wave-specs/w2b\.md:' \
  | grep -Ev '^docs/research/drafts/wave-specs/baseline-universe\.json:' \
  | cut -d: -f1,2 | sort -u | wc -l          # ⇐ 套排除集後的唯一 (檔:行) 總數

# load-bearing 負控：拿掉上面任一條 grep -Ev 重跑，總數必須變大。
# ⛔ 下面兩個數字**由本區塊在產生當下量出**，⛔ 不是釘死值——樹一動就跟著動，
#    重跑產生器即重生。⛔ 不得把它們當成跨 commit 有效的常數。
#    產生當下：完整排除集 69；拿掉 archive 那條 72 ⇒ 該項確實在擋東西。
```

⚠️ **上面那串只給「排除集後的總數」，⛔ 不給 A／B／C 的切分。**切分需要四條規則同時成立，一行 shell ⛔ 做不到——⛔ 不得拿一個只實作其中一條的指令冒充它（`templates/handoff-contract.md` §3.2 規則三：寫得出的，解析器必須讀得回，且值逐字相同）。四條規則逐字如下，**上面 3.2–3.4 的逐檔表即依此產生**：

1. **排除集**（§3.1 具名四項）先套用，命中即不進母體，並各自計數以驗 load-bearing。
2. **B · 同行標明**：該命中所在行逐字含「已移除」⇒ 讀者在 `git grep` 當下即看得出該檔不存在 ⇒ 構造上⛔ 不是入口。
3. **B · marker 區塊與合成語料**：落在 `docs/CONTRACT_TOOL_RECONCILE.md` 的 `w2b-setdiff:begin`／`w2b-historical:begin` 兩對 marker 之間者；或位於 `cli/tests/test_contract_tool_reconcile.py`（在臨時目錄造同名檔的合成語料，命中的是字串常數）。
4. **B · 就地註記檔**：`ADOPTION.md` 與 `AI_WORKFLOW.md` —— 依需求方 2026-09-01 裁定 2 就地註記為「由 `WF-REDESIGN-W2B` 移除」並指向本檔。⚠️ 這兩檔的註記句寫的是「由…移除」⛔ 非連續的「已移除」，故規則 2 蓋不到，需要本條；本條**實測 load-bearing**（拿掉即有命中落回 A）。
5. **A vs C**：其餘命中依卡面資源宣告切——落在寫入集內為 **A**（⭐ 必須為 0），否則為 **C**（授權外，逐項上呈，⛔ 不自行擴權）。

⚠️ **規則 2 的已知限制**：它只看字面 ⇒ 「⛔ 不要移除 `X`」這類句子會被誤判為 B。代價已接受，因為每一筆都逐檔列計、人讀得到；⛔ 不得由此推出「寫上『已移除』就能藏東西」。

<!-- old-entry-residual:end -->
