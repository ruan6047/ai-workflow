# Handoff Contract — <專案名>

> 通用不變量見 canonical `AI_WORKFLOW.md` §4.1。此文件規範跨 writer 的 remote handoff；它不要求 tmux、daemon、Babashka 或本機 queue。

## 1. 不變量

- handoff 是 remote lifecycle event；聊天、PR 留言、tmux 訊息只可作通知，不可作狀態。
- sender 必須先 push `source_sha` 指向的 commit；`source_sha` 固定為完整 40 字元 SHA，不接受 branch name、短 SHA 或未提交工作區。
- receiver 驗證成功後才寫入 `handoff-accepted`；此事件才可轉移 owner。驗證失敗寫 `⏸阻塞` 或 findings，不得自行修正 sender 的內容。
- 每次 handoff 引用有效 `claim_event_id`；lease 過期、baseline 不一致或證據不足時不得接受。
- 本機 queue／`.swarmforge`／tmux runtime 必須 `.gitignore`；重啟時以 remote event 查詢未完成 handoff，不信任本機暫存狀態。

## 2. Handoff event payload

```yaml
event_id: <UUID>
type: handoff
card_id: <CARD_ID>
actor: <lifecycle event writer；通常等於 from>
from: <GitHub account / model@tool>
to: <role / GitHub account / model@tool>
next_stage: implementation | review | release
source_sha: <full-40-char-commit-sha>
branch: <pushed remote branch>
claim_event_id: <active claim event ID>
state_version: <strictly increasing integer>
iteration: <integer>
baseline: <spec/design baseline version or N/A>
evidence:
  - <test / CI / review / decision URL>
summary: <one-line change or request>
occurred_at: <write-time ISO 8601>
```

## 3. Receiver acceptance checklist

- [ ] `source_sha` 可從已推送的 remote ref 解析為 commit，且與 handoff payload 完全相符。
- [ ] card、iteration、next stage 與 `claim_event_id` 對應的有效 lease 一致。
- [ ] baseline 與卡片／Initiative 一致，或 handoff 明確標記為 blocked 並附基線變更事件。
- [ ] 所需 evidence 存在、可讀，且工作區／驗證環境符合任務要求。
- [ ] receiver 在 remote adapter 追加 `handoff-accepted`，記錄 `source_sha`、actor、時間與驗證證據；之後才開始工作。

## 3.1 查核留痕契約：`wf-review-event:v1` 與 `wf-review-receipt:v1`

本節是這兩個 marker 的權威定義。任何解析 Issue／PR 留言以判斷「這張卡的這個 SHA 是否已有查核裁決」的工具——`doctor`、看板對帳、任務編排器、CI 檢查——一律引用本節，不得從留言外觀、標題文字或作者身分自行推測語意。

本節規範的是**應然**。契約允許領先實作，但落差必須登記在 §6，否則會出現「契約寫著 fail-closed、實際在 fail-open」而無人看得出來的狀態。

### 3.1.1 角色分工

跨工具查核者不能執行 `wfcli` 時，**不得**把「PR 頁面沒有 review」推論為「查核未發生」。留痕因此分兩段：查核者留下 receipt（證據），lifecycle writer 轉錄為 event（狀態）。兩者不是同一份東西的兩種寫法，權責、語法與嚴格度都不同：

| 面向 | `wf-review-event:v1` | `wf-review-receipt:v1` |
|---|---|---|
| 產生者 | 只有 `wfcli review`（lifecycle writer） | 查核者本人的 GitHub 帳號 |
| 是否 lifecycle 狀態 | 是；唯一的狀態面裁決事件 | 否；只是 evidence，不改卡片狀態 |
| marker 語法 | 單行、`key=value`、以單一空白分隔 | 多行、`key: value`、以換行分隔 |
| 鍵集合 | 封閉（§3.1.3） | 開放 |
| 未知版本的失效方向 | 既有解析器會誤放行，故須明文 halt（§3.1.4） | 比對不命中即視為不存在，落 `unobservable`，方向已屬保守 |

最後一列是兩者嚴格度不對稱的**原因**，不是疏漏：event 有一條會**放行**的錯誤路徑要堵，receipt 沒有。對 receipt 套用同等嚴格度，只會在沒有風險的地方製造遷移成本。

receipt 不是 event 的必要前置。它只在查核者無法執行 `wfcli` 時需要；能自行執行 `wfcli` 的查核者直接產生 event，缺 receipt 不構成缺陷。但這留下一個必須明說的洞：**沒有 receipt 的 event，其查核者身分只有 `--reviewer` 的自由文字，而該欄只驗非空**。此類 event 在身分維度上等同無佐證，任何依賴「誰查核的」做判斷的流程都不得單獨採信它。

### 3.1.2 `wf-review-receipt:v1`

查核者在被審 Issue conversation 或 PR review body 留下一則不可覆寫的收據，並保留 GitHub URL。固定內容如下：

```text
<!-- wf-review-receipt:v1
card_id: <CARD_ID>
source_sha: <full-40-char-commit-sha>
report_sha256: <查核報告原文 UTF-8 SHA-256>
-->
```

GitHub comment author 是可驗證的帳號身分；收據內模型／工具名稱只屬自述，不能取代平台身分驗證。

收據**不含** `escalation_epoch` 或 `attempt_id`。因此同一張卡、同一個 `source_sha` 在 epoch 遞增後重審時，兩份收據除 `report_sha256` 外逐字相同，僅憑收據無法判定各自對應哪個 attempt。轉錄者必須以 `report_sha256` 對帳報告原文來區分，不得以留言時序推定。

### 3.1.3 `wf-review-event:v1`

由 `wfcli review` 在通過契約驗證後寫入被審 Issue timeline 的裁決留言，marker 置於留言首行。它是狀態面唯一的裁決事件識別符。逐字語法：

```text
<!-- wf-review-event:v1 card_id=<CARD_ID> source_sha=<full-40-char-commit-sha> attempt_id=<CARD_ID>-e<epoch>-<full-40-char-commit-sha> -->
```

**必填三欄**：`card_id`、`source_sha`、`attempt_id`。三者皆為必填，缺任一即依 §3.1.4 處理。

**鍵集合封閉**：`v1` 只有上列三鍵。出現任何未定義鍵即依 §3.1.4 處理，不得忽略後照常解析。要擴充欄位必須升版本——契約若對自己管轄範圍內的未知內容選擇忽略，那麼擋住未知版本卻放行未知欄位，只是把同一個漏洞換個位置。

**順序與分隔固定**：三欄依 `card_id`、`source_sha`、`attempt_id` 排列，以單一空白分隔。這不是排版偏好：既有消費者以整段前綴字串比對，換順序或多一個空白就完全不命中，而不命中會落入 §3.1.4 要堵的 legacy 分支。語意等價但格式不同的 marker **不是**合法 `v1` marker。

**三欄必須自洽**：`attempt_id` 冗餘編碼了另外兩欄，其反解出的 `card_id` 與 `source_sha` 必須與同一 marker 的對應欄位逐字相同。不自洽即依 §3.1.4 處理。

**epoch 只能反解**：marker 不帶 `escalation_epoch` 欄，epoch 僅能由 `attempt_id` 的 `-e<N>-` 段取得。attempt identity 是 `(card_id, escalation_epoch, source_sha)`（`review-escalation.md` §3），因此丟失 `attempt_id` 等同丟失 epoch。

**marker 是識別符，不是裁決本體**。marker 只是 comment body 裡的純文字，沒有任何簽章性質，任何有留言權限的身分都能逐字複製一份。因此**單憑 marker 不得裁決**。狀態面裁決成立需三面同時一致，缺一不可：

1. Issue timeline 上帶合法 `v1` marker 的裁決留言全文；
2. Issue body `## Log` 中對應同一 `attempt_id` 的 `review by wf-cli` 索引行；
3. Project 交付狀態欄與該裁決結論相符。

這是 AND 不是 OR，理由有二。其一，要求三面命中並不能杜絕偽造，但它把偽造面從「一則留言」擴大到留言、body、Project 欄位三處，而 Project 欄位另有 GitHub 稽核軌跡。其二，`wfcli review` 的三次遠端寫入沒有交易性，**半寫入是真實可能狀態**；AND 語意讓半寫入被偵測而非被靜默當成完成。三面不一致時不得裁決，也不得挑其中一面作準。

**已知限制：裁決結果不在 marker 內。** marker 只承載 identity，`APPROVE`／`REQUEST_CHANGES`、`core_pain_resolved`、findings 等語意只存在於渲染後的散文，留言內沒有結構化區塊。消費者找到 marker 後仍無法從 marker 得知裁決是什麼。此限制影響 §3.1.5 的可實作性，其解法需改動寫入端，不在本節規範範圍。

### 3.1.4 未知版本、缺欄與 fail-closed

> **生效狀態（必讀，否則本節提供的是虛假保證）**：本節規範**應然**，其效力**不因寫入本檔而自動存在**。一個消費者是否真的 fail-closed，取決於它自己是否實作了本節，而那件事只能從 §6 的登記查到。**在 §6 登記證實之前，任何流程都不得假定本節的 fail-closed 保證已生效**，也不得以「契約有寫」作為放行或結案的理由。
>
> 尤其：契約寫著 halt、消費者實際放行，比沒有契約更危險——它讓讀者以為有一道閘門。因此 §6 對 fail-open 落差**強制要求追蹤卡**。

**legacy 的判準是語法，不是時間。** legacy 裁決留言 ≡ **完全不含 `wf-review-event:` 前綴**的留言。它們是 marker 引入前寫下的，既有相容規則對它們維持不變。

反之，只要留言出現 `wf-review-event:` 前綴，該留言即宣告自己受本契約管轄。此時版本不是 `v1`、或 `v1` 但不符 §3.1.3 任一要求（缺欄、多出未定義鍵、順序或分隔不符、三欄不自洽），一律 fail-closed，**不得回退到 legacy 路徑**。用時間或 cutover 時點定義 legacy 會引入時鐘、時區與「編輯過的留言算哪個時間」等問題，那屬時間語意契約的範圍；語法判準只看單則留言的內容，與時間契約正交。

**fail-closed 的作用域是整張卡，不是單則留言。** 一旦出現受管轄但不合格的 marker，該卡的自動裁決判定立即停止，回報「不可判定」；即使 timeline 別處存在合法 `v1` event，也不得自動放行。

作用域必須是 per-card，因為失效方向不對稱。同一張卡出現多個 SHA、先退回後通過是常態；若只跳過讀不懂的那則、繼續採用較早的合法 event，那麼當讀不懂的那則其實是**撤銷或降級**裁決時，結果是「讀不懂一則留言，所以放行」。那不是比較寬鬆的 fail-closed，那是 fail-open。

**解除路徑必須存在，否則這條規則就是死鎖。** per-card halt 意味著任何有留言權限的身分，貼一行不合格 marker 即可凍結該卡的自動判定。這是已知的可用性代價：凍結需要人介入，但不會產生錯誤的通過。

解除以 [`review-escalation.md`](review-escalation.md) §5 的 **`review-marker-clearance`** 事件為之，該處定義其必填欄位與語意。要點：

- **停機狀態由現行內容導出**，不由簿記推定——留言隔離後遭編輯即再次停機，但**任何**編輯結果都有可發的解除路徑（編輯成合格 marker 走 `repaired-verified`），不得出現無法解除的狀態。
- 解除範圍以留言為單位；多則不合格 marker 需多則 clearance。
- `forged-rejected` **不解除停機**：偽造是安全事件，不由任何機器判定自動放行。它只把「這是冒充」寫進事件流；宣告與恢復是兩個動作，恢復另發 `reissue-required`。（先前版本以需求方裁定＋body hash 綁定來自動解除，該防重放推理已撤回——內容由攻擊者撰寫，hash 可預先計算，不構成 nonce。詳見 §5。）
- **分類不得靠自述降類**：留言 author 不在 §5 宣告的 review event writer 帳號集合、內容卻看似裁決者，不得判為 `malformed-ignored`，**也不得**判為 `repaired-verified`——否則外人可自行編輯留言後以「已修復」洗白。
- `repaired-verified` 另須 adapter 驗證現行 body **確實已合格**且該留言**已有前一筆有效 clearance**；否則壞 marker 只要改成另一個壞 marker 就能藉此出口解鎖。
- `reissue-required` 解除停機但不得據以認定該卡已有裁決。
- 修復首選是不編輯原留言、改以正規通道另發合法事件並 `superseded`；不得刪除被停機的留言，也不得回寫既有事件。

**已承認的保守誤判**：一則本身合法的 legacy 留言，若在內文中**引用**了 `wf-review-event:` 字樣（例如討論契約本身），會被判為受管轄且不合格而觸發 halt。這是往 fail-closed 方向的誤判——卡住而非放行——故予以接受，但不假裝它不存在。

### 3.1.5 重複 event 與冪等重送

同一 `attempt_id` 出現多則 event 時：**裁決語意一致者視為同一筆**，不重複計入 attempt，也不觸發 §3.1.4 的 halt；**語意衝突者**依 §3.1.4 停止該卡的自動判定，交由 Coordinator／需求方裁定。

重複不必然是異常。寫入端沒有重複執行防護，而遠端寫入中斷後的重送，其**成功樣態就是產生一則重複留言**。若規定重複即 halt，等於讓每一次成功的重送都凍結該卡，也就等於禁止了可恢復的重送機制。

**比對基準是裁決語意，不是逐字。** 比對 `review_result`、`core_pain_resolved`、交付狀態結論，以及 findings 的 `finding_id`／`accepted`／`status` 集合；**排除**寫入時間與 reviewer 自由文字。寫入時間每次執行都重新取值，合法重送必然在該行不同；若採逐字比對，本節就退化成「重複即 halt」。

> **生效狀態**：本節目前是**延遲生效契約** [deferred contract]。§3.1.3 末段的限制使它無法被可靠實作——上列語意欄位只存在於散文中，沒有結構化承載，消費者要判定「語意是否一致」就得剖析中文散文與條列。
>
> 在寫入端提供結構化裁決承載之前，消費者**不得**宣稱實作了本節。此期間的保守行為是：**遇到同一 `attempt_id` 的多則 event，一律視為無法判定語意一致性，依 §3.1.4 停止該卡的自動判定**，而不是猜測它們相同。這會讓合法重送也被卡住，是刻意選擇的方向——寧可卡住重送，不可把衝突的兩份裁決當成同一份。解除本節的延遲狀態需要寫入端變更，其追蹤卡與生效條件登記於 §6。

### 3.1.6 轉錄與 doctor 判定

PM 祕書以收據原文與 hash 對帳後，才用 `wfcli review` 轉錄結構化報告；review event evidence 必須引用該收據 URL。`--reviewer` 的自由文字不可單獨作為身分證明。

若收據已存在而 review event 尚未出現，`wfcli doctor --review-channel` 必須報
`receipt_untranscribed`：這是「查核裁決已可觀測、尚未進狀態面」，保持 `🔍待查核` 並要求轉錄。
若兩者皆無，doctor 報 `unobservable`，**不是**宣告查核未發生；系統只能 fail-closed，不能放行或事後編造結論。

「找不到訊號」與「找到訊號但讀不懂」是不同結果，不得併入同一態：前者要人去查有沒有人查核過，後者要人去修一則壞掉的留言。§3.1.4 的 halt 與 §3.1.5 的衝突因此需要與 `unobservable` 分離的結果態；三面不一致的半寫入（§3.1.3）同理。消費者若尚無足夠的結果態表達這些情形，須在 §6 登記。

## 4. Optional local tmux adapter

| 能力 | 可否使用 | 限制 |
|---|---|---|
| 對每個 worktree 開 session | ✅ | session 不代表 claim 或 owner |
| 收到 remote handoff 後喚醒 idle agent | ✅ | wake-up 可遺失；agent 仍需查 remote event |
| 本機 inbox/outbox | ✅ | 僅快取 remote event，不得成為跨機 queue 或唯一 audit trail |
| 直接改 Ledger／lease／state | ❌ | 只能由 remote coordination adapter 寫入 |

## 5. 專案實作

- Remote handoff writer／API：<GitHub Action、App 或其他受保護 adapter>
- SHA 驗證命令：<command>
- `handoff-accepted` writer 與授權：<identity／workflow>
- **被授權的 review event writer 帳號集合**：<GitHub 帳號，可多個>
  （`review-escalation.md` §5 的 `forged-rejected`／`malformed-ignored` 分類界線以此為準：
  留言 author 不在此集合而內容看似裁決者，不得降類為「寫壞了」。未宣告則該分類無法機械核對，
  adapter 必須一律 fail-closed。）
- tmux launcher／wake-up：<可選 command；不用填—>
- Runtime 路徑與 `.gitignore`：<path>
- 失敗、重試與人工介入：<runbook link>

## 6. 消費者符合度登記

任何解析 §3.1 marker 的工具都是本契約的消費者。§3.1 規範應然，允許契約領先實作；本節讓落差可稽核。不登記的落差會讓契約寫著 fail-closed、實際在 fail-open，而沒有人看得出來——那比沒有契約更危險，因為它同時提供了虛假的保證。

每個採用專案在此逐一登記，或另立單一登記檔並於此填入其路徑：<`<專案>/docs/CONSUMER_CONFORMANCE.md` 或「就地登記於本節」>

- 消費者：<工具／檔案／函式>
  - 讀取的 marker：<`wf-review-event:v1`／`wf-review-receipt:v1`>
  - 已實作：<逐條，對應 §3.1 的哪一項要求>
  - 落差：<逐條；每項必須註明失效方向為 fail-open 或 fail-closed>
  - 落差追蹤：<Issue／卡 ID；無則填「未追蹤」>

**fail-open 方向的落差必須有追蹤卡**：它代表契約承諾會擋下的情形，實際上會被放行。fail-closed 方向的落差（過度保守、誤卡）可暫時無追蹤卡，但仍須登記，否則無從判斷一次凍結是規則生效還是實作缺陷。

**未登記等同未生效**：§3.1.4 與 §3.1.5 的保證只在此處有對應登記時才可被依賴。沒有登記的消費者，一律視為未實作該節；引用契約的流程不得因為「規範已寫入本檔」就假定閘門存在。
