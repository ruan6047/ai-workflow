# 派工包範本 (Dispatch Package)

> 承載 canonical `AI_WORKFLOW.md` §6.1 與 `stage-rules/implementation.md` §3 的 ②。祕書（PM）派工時以此組裝；**§4 六條標準條款逐字帶入**，不得省略或改寫。派工是需求方的決策、PM 的機械寫入——本範本不授權任何 session 自行派工。
> 信封四段的權威定義在 [`handoff-contract.md`](handoff-contract.md) §3.3，⛔ 本檔不重寫定義。
> ⚠️ 看板值仍為舊語彙（15 值），對照見決議 §一；切換於切換 Initiative。

## 信封一 · 卡與身分

- 卡ID／Issue：`<CARD_ID>`（`<owner/repo>#<n>`）　級別：`<T0–T4>`　Initiative：`<父卡／—>`
- spec 基線：`<spec_version；Initiative 子卡註冊時即必填父卡當前版本，「—」視同不一致>`
- 階段：`執行`　輪次（iteration）：`<n>`　from：`<PM 帳號>`　to：`<執行者 模型@工具>`
- 服務的原始目標：`<這根鏈最終要解的問題>`　鏈深：`<0–2；> 2 不得派工，須整鏈重審>`
- 核心痛點（查核第一判準的錨）：`<卡面原文逐字；canonical §5.1>`
- `db_scope`：`<none｜read｜write｜schema｜data-migration>`
- 資源宣告（寫入集，卡面逐字）：`<file:／port:／container:／db: 逐條；含交付必要的重現工具>`
- 模型：實際 `<模型@工具>`　卡面建議 `<經濟型／主力型／高階型>`　偏離理由 `<相符時填「相符」>`

## 信封二 · 身分自述

- 組裝者 GitHub 帳號：`<帳號>`
- session ID：`<Claude：~/.claude/projects/<cwd>/<id>.jsonl 的 <id>；Codex：rollout-<時間>-<id>.jsonl 的 <id>>`
- 該則訊息定位：`<Claude：訊息 uuid；Codex：該則 timestamp>`

## 信封三 · 機械指令

- 驗證指令逐條：`<lint／測試／專案驗證命令；標註 worktree／容器／環境變數>`
- **rc 分開取，⛔ 不接管線**（`| tail` 會換掉 `$?` 並截掉守衛裁決）
- **完整性宣稱一律由指令輸出產生**；artifact 須在交付 HEAD 可重現（canonical §6.2）。「全部／全數」須附窮舉證據，⛔ 非人工聲明
- ⚠️ **`wfcli` 的拒絕訊息走 stderr**：回報「已寫入」前必須看**全文**輸出，⛔ 不得把 stderr 併進 stdout 之後再截斷——`| tail` 會同時換掉 `$?` 並吃掉守衛裁決。同族三犯的實據見 `stage-rules/pm-conduct.md` 四

## 信封四 · 已知未驗項

> PM 交出這份派工包時**自己**還沒驗的東西，逐項＋各自原因，三分類擇一。⛔ 不裸列。

| # | 未驗項 | 分類 | 原因 |
|---|---|---|---|
| 1 | `<項目>` | `驗不了`／`沒去驗`／`刻意不驗` | `<刻意不驗須寫委給誰及理由>` |

---

## 1. 進駐環境

- 從 `<repo 絕對路徑>` 以 `origin/main`（`<完整 40 碼 SHA>`）建 worktree
- worktree 路徑：`<絕對路徑>`　分支：`<實際分支名>`（**PM 於認領時寫回卡面**，canonical §4.5）
- **寫入授權**：`<允許動的路徑逐條列出>`；其餘一律唯讀
- **唯讀範圍**：`<跨 repo、submodule、生產資料、他卡射程等明確標唯讀；動到即為越界，須停下寫阻塞發現>`

## 2. 任務

- 要做什麼：`<範圍；規格權威居所＝卡面 body，⛔ 不是任何草稿檔>`
- 驗收條件：`<逐條抄自卡面，一條一列，⛔ 不改寫、⛔ 不摘要合併>`
- 非目標：`<卡面「⛔ 非射程」逐字>`

## 3. 注意事項回應清冊（三層編號）

- 附上 `stage-rules/<本階段>.md` §5 的**編號清單**（`F-<階段>-NN`），加上專案層 `P-` 與任務層 `T-` 各自的編號條目。三層**累加⛔ 不覆寫**。
- ③ 交回時必附**注意事項回應清冊**：對上列編號**逐條**回應，三值＝`已遵循`／`不適用：<原因>`／`發現：<處置>`。
- ④ 對**格數與值域**機械對照（⛔ 不判內容）；**格數不符＝退回**。
- ⚠️ 本清冊與**踩坑族清冊**是兩份不同的東西，值域也不同：踩坑族清冊有 13 族，逐族一行，三值＝`已檢查`／`不適用：<原因>`／`發現：<處置>`（族名與範本由 `wf_cli.pitfalls` 的 `roster_for()`／`report_template()` 取，⛔ 不手打）。⛔ 不得以其中一份充當另一份。
- 上一輪退回理由：`<有前輪時逐字帶入；無則寫「無前輪」>`

## 4. 標準條款（canonical §6.1，六條全帶）

1. **範圍外發現寫報告回 PM**：不得自行開卡、不得 spawn 背景任務或建立背景待辦 chip。範圍外的東西只能是報告的一節，由需求方裁決。
2. **不得停等背景通知**：需要等待時前景輪詢或不結束回合；不得以「等背景通知」為由結束回合。
3. **分支更新禁 `gh pr update-branch`**：它產生 synthetic merge、污染歷史與守衛判讀；一律**本地 rebase ＋ `git push --force-with-lease`**。**狹義例外**（需求方 2026-08-21 於 `ruan6047/ai-workflow#39` 的裁定留言，issuecomment-5367447565）：下列兩項**須同時成立**時不要求 rebase——(i) rebase 會使 **main 上已合併的碼**所引用的 SHA 失效；(ii) rebase 會把早於 `TRAILER_GUARD_EPOCH` 的 commit 推過界線，使其翻成無法修正的違規。例外**只免除「必須 rebase」，不免除任何 trailer**：該 merge commit 仍須帶 `merge_clean` 所要求的 `Reviewed-by`，無查核對象時填 canonical §6 的「不適用」形態。⚠️ **本例外沒有機械執行者**——「基線更新 merge」與整合 merge 在 commit 自身上都只是多個 parent，誰是 main 取決於你站在哪個 ref 上看，那是脈絡不是 commit 自身的性質。故它是**派工包層的約定**：由撰寫派工包者判定並**在本包內具名**、由查核者複核，⛔ 不得宣稱它已機械化。
   - 本卡是否援引狹義例外：`<否／是——是則逐項寫出 (i)(ii) 各自成立的證據，並具名判定者>`
4. **詭異數據標記「待人工判讀」交需求方**，不自行下結論。外部佐證走新聞／第三方通道時：**定性佐證 only**，數值以官方紀錄為權威，引用必附 URL ＋ 日期。
5. **commit trailer ＝ commit message 末端的連續單一區塊，中間無空行**（`git interpret-trailers --parse` 遇空行即切斷解析，守衛必紅）：

   ```text
   Requested-by: <GitHub 帳號／來源>
   Planned-by: <GitHub 帳號／模型@工具>
   Implemented-by: <模型@工具>
   Co-Authored-By: <專案自有 trailer，同一區塊內，前面不空行>
   ```

6. **CLI 探索紅線**：不得真跑爬蟲、訓練等有副作用的 CLI。本專案**當前仍有副作用的入口**：`<清單／無>`（來源＝專案 Contract，canonical §7）。

⚠️ 第 6 條的清單**必須指得出居所**。專案若沒有那份 Contract 檔，⛔ 不得留空跳過，也⛔ 不得由 PM 憑印象代填而不標明——代填時逐字標「PM 推導、⛔ 非引自 Contract」，並把「該清單無權威居所」寫成範圍外發現交需求方。

## 5. 交付方式

- **推分支到 origin，⛔ 不 merge**；回報最終 **40 碼 SHA** ＋逐驗收條件證據 ＋「待需求方裁決」清單。
- 交付報告依 [`delivery-report.md`](delivery-report.md) 組裝，**它是 ③ 的一部分**：只推 commit 沒報告＝仍在進行中，⛔ 不得轉待確認（`stage-rules/executor-conduct.md` 一）。
- 交接：由 PM 寫 `handoff` 事件並依 [`review-dispatch.md`](review-dispatch.md) 派審；⛔ 執行者不得自派查核者、⛔ 不得自 merge。
- 交回前把本 session 的 shell cwd 移出 worktree（自檢：`lsof +D <worktree 路徑>` 無輸出＝乾淨），否則 `handoff --next-stage release --cleanup` 會因 worktree 被占用而失敗。

## 6. 這份派工包的已知落差

> PM 自陳，⛔ 不得省略。與信封四的差別：信封四列的是「還沒驗的事實」，本節列的是「這份文件自己的缺陷」。

- `<逐條；無則逐字寫「無」，⛔ 不留空>`
