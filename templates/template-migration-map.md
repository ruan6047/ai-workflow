# 範本異動對照（`WF-REDESIGN-W2B`）

> 本檔是 `WF-REDESIGN-W2B` AC1 的**封閉 mapping**：舊 → 新逐檔對照，各附 falsifier。
> ⛔ 本檔不是範本，⛔ 不要拿它組裝任何交接文件。它存在的唯一理由是：被移除的檔會在
> 歷史、註解與外部引用裡繼續出現，而讀者需要一個**指得到的地方**知道它們去哪了。
> ⚠️ 本檔自身是 mapping 文件，故「舊入口零引用」的 falsifier **把本檔排除在外**——
> 否則那條檢查會被本檔的存在永久卡住。

## 1. 被移除的五檔（封閉集合，⛔ 非六檔）

| 舊檔 | 處置 | 承接者 | falsifier（什麼觀察會讓本列不成立） |
|---|---|---|---|
| `templates/tasks-card.md` | **移除** | 卡面 fenced JSON（`WF-REDESIGN-W3` 落地）；規格單一居所＝卡面 body ＋ `spec_version` | 檔案仍存在；或 `WF-REDESIGN-W3` 之後仍找不到卡面機讀 schema 的居所 |
| `templates/bug-card.md` | **移除** | 缺陷走**待審清單項＋一般卡**，⛔ 不另立卡種 | 檔案仍存在；或有人被要求開一張 `BUG-` 卡而找不到範本 |
| `templates/bug-workflow.md` | **移除** | 同上；分級判準已在 `tier-rules.md` 與 canonical §3 | 檔案仍存在；或 `tier-rules.md` 查不到「這個 bug 該是幾級」 |
| `templates/initiative-card.md` | **移除** | 父卡模型住 [`../stage-rules/`](../stage-rules/)（父卡跑迴圈⛔ 不做事、子卡只在父卡規劃誕生、父卡⛔ 不宣告 `file:` 資源） | 檔案仍存在；或 `stage-rules/` 裡找不到父卡與子卡的關係規則 |
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

**母體排除三項**（⛔ 只有這三項，⛔ 不得再加）：

- **`archive/`**：歷史封存⛔ 不是現行入口，改寫它等於改寫已結案的紀錄。
- **`docs/research/`**：規劃期草稿與 inventory，owner 非本卡。
- **本檔**：AC1 逐字「mapping 文件自身除外」。

母體內的命中**逐 occurrence 三分類，⛔ 全部可見列計**——分類⛔ 不是豁免（沿
`scripts/pollution_check.py` 的自指命中設計）：

| 類 | 是什麼 | 判準 |
|---|---|---|
| **A** 現行入口殘留 | 本卡改得動、卻仍把被移除檔講得像現行 | ⭐ **必須為 0**；非 0 即本卡缺陷 |
| **B** 移除紀錄／合成語料 | 逐項處置表與歷史小節（以檔內 marker 界定）；對帳器在臨時目錄造同名檔的合成語料 | 構造上⛔ 不是入口 |
| **C** 授權外 | 本卡寫入授權外的檔（派工包 §2「其餘一律唯讀」） | ⛔ 不自行擴權，逐項上呈需求方 |

⭐ **B 以檔內 marker 界定，⛔ 不以檔名整檔排除**——有人把新的引用寫在 marker 之外，它會落回
A 而不是靜默通過。

<!-- old-entry-residual:begin -->

> 本區塊由 `old_entry_residual.py` 產生，⛔ 非手寫。重跑即重生。

**逐 occurrence 命中總數：80**　A 現行入口殘留（授權內）**0**／B 移除紀錄與合成語料 58／C 授權外待裁決 22

⭐ **通過判準只有一條：A ＝ 0。** B 與 C ⛔ 不是豁免，是**分類**——逐筆列出、逐檔列計，⛔ 不從母體中拿掉。

### 3.1 A · 現行入口殘留（授權內）：**0**

（無）

### 3.2 B · 移除紀錄與合成語料（58，在母體內、⛔ 非入口）

| 檔 | 命中的舊檔名 | 分類理由 |
|---|---|---|
| `cli/tests/test_contract_tool_reconcile.py` | `bug-card.md`×1、`initiative-card.md`×1、`tasks-card.md`×2 | 對帳器合成語料（臨時目錄造同名檔），命中的是字串常數 |
| `docs/CONTRACT_TOOL_RECONCILE.md` | `bug-card.md`×16、`bug-workflow.md`×1、`initiative-card.md`×13、`tasks-card.md`×24 | marker 界定的移除紀錄區塊（逐項處置表／歷史小節） |

⛔ **不得由此推出「這些地方可以藏東西」**：它們在母體內、每一筆都印得出來、逐檔逐檔名有計數。B(1) 以檔內 marker 界定 ⇒ 有人把新的引用寫在 marker 之外，它會落回 A 而不是靜默通過。

### 3.3 C · 授權外、待需求方裁決（22）

| 檔 | 命中的舊檔名 | 分類理由 |
|---|---|---|
| `ADOPTION.md` | `bug-card.md`×1、`initiative-card.md`×1、`tasks-card.md`×1、`templates/TASKS.md`×1 | 未列入本卡寫入授權 |
| `AI_WORKFLOW.md` | `bug-workflow.md`×1、`tasks-card.md`×1、`templates/TASKS.md`×1 | canonical 本體，`WF-REDESIGN-W2A` 已完成；派工包逐字標唯讀 |
| `cli/README.md` | `tasks-card.md`×3 | 未列入本卡寫入授權（授權只到 `cli/tests/test_contract_tool_reconcile.py`） |
| `cli/src/wf_cli/card.py` | `tasks-card.md`×7 | `cli/src/**`＝`WF-REDESIGN-W3` 射程；派工包逐字標唯讀 |
| `cli/src/wf_cli/card_face.py` | `tasks-card.md`×1 | `cli/src/**`＝`WF-REDESIGN-W3` 射程；派工包逐字標唯讀 |
| `cli/src/wf_cli/registry.py` | `templates/TASKS.md`×1 | `cli/src/**`＝`WF-REDESIGN-W3` 射程；派工包逐字標唯讀 |
| `cli/src/wf_cli/resources.py` | `tasks-card.md`×1 | `cli/src/**`＝`WF-REDESIGN-W3` 射程；派工包逐字標唯讀 |
| `cli/tests/test_card.py` | `tasks-card.md`×1 | 未列入本卡寫入授權 |
| `cli/tests/test_commands_mocked.py` | `tasks-card.md`×1 | 未列入本卡寫入授權 |

⭐ **C 的每一筆都是註解／敘述／文件指路，⛔ 沒有一處是會被執行的碼**（實測：移除五檔後 `cli/` 全套測試仍全綠）⇒ 它們是**懸空指標**，⛔ 不是功能缺陷。危害是讀者照著去找一個不存在的檔。本卡⛔ 不得自行擴權去改它們（`stage-rules/executor-conduct.md` 二：遇授權缺口停下）。

重跑：

```bash
for f in tasks-card.md bug-card.md bug-workflow.md initiative-card.md templates/TASKS.md; do
  echo "---- $f ----"
  git grep -n --fixed-strings -- "$f" \
    | grep -Ev '^archive/|^docs/research/|^templates/template-migration-map\.md:'
done
```

<!-- old-entry-residual:end -->
