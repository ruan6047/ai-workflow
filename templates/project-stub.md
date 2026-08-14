# AI 協作工作流 (本專案採用)

> **完整規則見 canonical：[`~/Dev/ai-workflow/AI_WORKFLOW.md`](../../ai-workflow/AI_WORKFLOW.md)**（唯一權威來源，改規則改那裡）。
> 本專案狀態面見 `<GitHub Issues ＋ Project #<n>／TASKS.md>`。以下為**核心鐵律速查**，細節與流程圖以 canonical 為準。

## 核心鐵律（速查）
0. **治理與寫入通道（canonical §1.1／§4.3）**：開卡、派工、追加前置、資源調度、結案＝**需求方決策**；機械寫入由**唯一 PM 祕書 session** 經祕書 CLI 執行。其他 session 不得寫 control plane、不得自行開卡或建立背景待辦。需求方不在場時 **AI 只續做已派工作**，待決事項寫成**報告的一節**交回等裁定——不另立佇列、不建背景待辦。
1. **實作／審核分離**：同一張卡的執行與查核＝不同任務、不同經手者；**任何人不得自審自己實作的卡**（含 Claude Code）。**查核第一行必答核心痛點是否已消失（具否決權）；`APPROVE` 必附 `self_run`，否則無效**（canonical §5.1／§5.2）。
2. **變更分級 + 部署閘門**：依 canonical T0–T4 按風險、範圍、可逆性選閘門；**T2 以上程式碼(A 類)每卡開分支＋獨立 worktree（走註冊制，認領時登記實際路徑與分支）**；**只有 `main`（已審核合併）能部署，分支不部署**。
3. **獨立性紅線**：紅線卡（安全/金流/統計 ML 正確性/資安/資料正確性）審核**必換模型家族或人審**，且**必跑實測**——同家族審（含 Opus 審 Sonnet）不算數。一般卡同家族異 session 審可接受。
4. **退回不代改**：審核發現缺陷 → 以 PR review／event 留 finding → **原執行者同分支修** → 重審；審核者**不得順手改 source branch**。連續 ≥3 次退回 → `🚨已升級`。
5. **需求、設計與大型工作**：Discovery 確認問題與證據，Design 確認使用流程、狀態、可及性與可用性驗收，Plan 才決定實作；使用者可見的 T3/T4 必過 Design Gate，純技術卡必記錄 N/A 理由。大型工作以 Initiative 管理 spec 基線、依賴、里程碑與變更，子卡採可驗證切片。**規劃閘門三級制（canonical §3.1）**：Initiative／T4／不可逆＝同步對抗式質詢真對話；T3＝核心痛點三問並經需求方批註；所有 T2 以上＝前提清單逐條附實查證據。
6. **協作狀態**：多 writer／共享資源專案以 remote coordination（GitHub 為預設）管 task、review、lease、CI，以 local resource lock 管 worktree／port／container；event log 是歷史，Ledger 是投影。**資源宣告是鎖**：派工前比對寫入集交集，`📦已合併` 未收尾仍佔用；破壞性 CLI 啟動須驗 lease。
7. **留痕**：T0/T1 commit 至少填 `Requested-by`、`Implemented-by`；T2 以上實作 commit 加 trailer（**人＝GitHub 帳號如 `ruan6047`，勿寫「使用者」；AI＝`模型@工具`**）：
   ```
   Requested-by:   <GitHub 帳號 | 業務/來源>
   Planned-by:     <GitHub 帳號 | AI/模型>
   Implemented-by: <模型@工具>
   ```
   merge commit／PR 結案紀錄再加：
   ```
   Reviewed-by:    <GitHub 帳號 | 模型@工具>
   ```
8. **驗證與留痕（canonical §2、§6）**：先讀再說、不虛構不存在的 API/表/指令；secrets 永不進 git；交付必附「改什麼/為什麼/怎麼驗證(實測)」。
9. **狀態與部署（canonical §0、§2）**：交付與部署分欄；需部署的卡只有驗證成功才可 `🏁完成`；失敗／回滾不得封存。**`📥Backlog` ＝已登記、未排程**，不是佇列位置——⚠️ 交付狀態住在看板欄位而不在 Issue 本體，預設 Issue 視圖分不出它與待辦卡，故**「開著的卡數」不等於「待辦數」**，統計待辦前必須先扣掉。
10. **模型路由**：先依風險選能力與供應商；紅線 review 必換家族。模型名單與明確 model ID 住專案 `MODEL_ROUTING.md`，不使用 `latest` alias。
11. **卡範圍與鏈式停損（canonical §3.2／§3.3）**：**一根問題一張卡**——遇授權缺口**停下**，把「阻塞發現」寫成報告的一節回報需求方，由需求方裁定；裁定「現在做」才擴充現卡授權或開新卡，裁定「不是現在」則**開卡並直接置 `📥Backlog` 登記**（登記，不是排程）。執行者不自行擴權、不自行開卡。開新卡僅限「不同能力域／紅線隔離／可真平行」三情形。每卡必填**服務的原始目標**；全域問題脫鏈獨立運行；**鏈深上限＝原始目標之下 2 層**。
12. **派工包標準條款（canonical §6.1）**：範圍外發現寫報告回 PM（不 spawn 背景任務）／不停等背景通知／分支更新禁 `gh pr update-branch`（用本地 rebase ＋ `--force-with-lease`）／詭異數據標「待人工判讀」交需求方（外部佐證＝定性 only，數值以官方為準）／**trailer ＝末端連續單一區塊、中間無空行**／查核環境不得真跑有副作用的 CLI。

**本專案契約填空**（canonical §7）：

- 狀態面：`<GitHub Issues + Project #<n>／TASKS.md>`　寫入通道：`<祕書 CLI 指令>`
- **破壞性 CLI（啟動須驗 lease）**：`<清單>`
- **當前仍有副作用的 CLI 入口（查核／探索禁跑）**：`<清單／無>`
- 要宣告的 DB 表／資源詞彙：`<清單>`

**派工＝需求方決策、祕書機械執行**；任何工具擔任該卡執行者時都不得兼任查核。
