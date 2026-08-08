# 派工包範本 (Dispatch Package)

> 承載 canonical `AI_WORKFLOW.md` §6.1。祕書派工時以此組裝；**§4 六條標準條款逐字帶入**，不得省略或改寫。派工是需求方的決策、祕書的機械寫入（§1.1）——本範本不授權任何 session 自行派工。

## 1. 卡與基線

- 卡ID／Issue：`<CARD_ID>`（`<owner/repo>#<n>`）　級別：`<T0–T4>`　Initiative：`<父卡／—>`
- spec 基線：`<版本；Initiative 子卡註冊時即必填父卡當前版本，「—」視同不一致>`
- 服務的原始目標：`<這根鏈最終要解的問題>`　鏈深：`<0–2；> 2 不得派工，須整鏈重審>`
- 核心痛點：`<一句話；查核第一判準以此為錨，canonical §5.1>`
- `db_scope`：`<none｜read｜write｜schema｜data-migration>`
- 資源宣告（寫入集）：`<file:／port:／container:／db: 逐條；含交付必要的重現工具>`

## 2. 進駐環境

- 從 `<repo 絕對路徑>` 以 `origin/main`（`<完整 40 碼 SHA>`）建 worktree
- worktree 路徑：`<絕對路徑>`　分支：`<實際分支名>`（**祕書於認領時寫回卡面**，canonical §4.5）
- **寫入授權**：`<允許動的路徑逐條列出>`；其餘一律唯讀
- **唯讀範圍**：`<跨 repo、submodule、生產資料等明確標唯讀；跨 repo 需修改時寫報告交 PM>`

## 3. 任務

- 要做什麼：`<範圍；引用 spec 章節>`
- 驗收條件：`<逐條抄自卡面，一條一列>`
- 非目標：`<明確不做的事>`

## 4. 標準條款（canonical §6.1，六條全帶）

1. **範圍外發現寫報告回 PM**：不得自行開卡、不得 spawn 背景任務或建立背景待辦 chip。範圍外的東西只能是報告的一節，由需求方裁決。
2. **不得停等背景通知**：需要等待時前景輪詢或不結束回合；不得以「等背景通知」為由結束回合。
3. **分支更新禁 `gh pr update-branch`**（產生 synthetic merge、污染歷史與守衛判讀）；一律本地 rebase ＋ `git push --force-with-lease`。
4. **詭異數據標記「待人工判讀」交需求方**，不自行下結論。外部佐證走新聞／第三方通道時：**定性佐證 only**，數值以官方紀錄為權威，引用必附 URL ＋ 日期。
5. **commit trailer ＝ commit message 末端的連續單一區塊，中間無空行**（`git interpret-trailers --parse` 遇空行即切斷解析，守衛必紅）：

   ```text
   Requested-by: <GitHub 帳號／來源>
   Planned-by: <GitHub 帳號／模型@工具>
   Implemented-by: <模型@工具>
   Co-Authored-By: <專案自有 trailer，同一區塊內，前面不空行>
   ```

6. **CLI 探索紅線**：不得真跑爬蟲、訓練等有副作用的 CLI。本專案**當前仍有副作用的入口**：`<清單／無>`（來源＝專案 Contract，canonical §7）。

## 5. 驗證與交付

- 驗證指令：`<lint／測試／專案驗證命令；標註 worktree／容器／環境變數>`
- **完整性宣稱一律由指令輸出產生**；artifact 須在交付 HEAD 可重現（canonical §6.2）
- 交付方式：**推分支到 origin，不 merge**；回報最終 **40 碼 SHA** ＋逐驗收條件證據 ＋「待需求方裁決」清單
- 交接：由祕書寫 `handoff` 事件並派審；執行者不得自派查核者、不得自 merge（canonical §2.1）

### 跨工具查核收據（查核者無 `wfcli` 時）

- 查核者先在被審 Issue conversation 或 PR review body 留 `wf-review-receipt:v1`（`card_id`、完整 `source_sha`、查核報告 UTF-8 `report_sha256`）；GitHub author 才是可驗證身分，模型／工具名稱只是自述。
- PM 僅能逐字轉錄與收據 hash 相符的報告，並在 `wfcli review` evidence 引用 receipt URL；不能以 `--reviewer` 自由字串代替收據。
- 交付／結案前執行 `wfcli doctor <repo_root> --review-channel --repo <owner/repo> --issue-number <n> --card-id <CARD_ID> --source-sha <40 SHA>`。`receipt_untranscribed` 或 `unobservable` 一律不得視為已查核；前者催轉錄，後者只可陳述「不可觀測」。
