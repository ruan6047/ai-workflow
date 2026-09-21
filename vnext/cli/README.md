# wfx — vNext CLI

動詞只有三個：`brief`／`facts`／`write`，W1.6／W1.7／W1.8 已全部交付。

CLI 只載入與呈現資訊、只交客觀事實，**內容判斷由人或負責該內容的 AI 完成**（`rules/core/boundaries.md` §4）。

## 跑它

```
PYTHONPATH=vnext/cli/src python -m wfx [--project-root <p>] <verb> [動詞參數…]

PYTHONPATH=vnext/cli/src python -m wfx --project-root vnext \
  brief --task 'ruan6047/ai-workflow#370' --role 執行者 --stage 執行
PYTHONPATH=vnext/cli/src python -m wfx --project-root vnext facts --task 370 --sha <sha>
PYTHONPATH=vnext/cli/src python -m wfx --project-root vnext \
  write --task 370 --field 狀態=進行中 --expect-updated-at 2026-09-21T11:05:20Z
```

`--project-root` 是**全域**旗標，只認動詞之前，由入口的前綴迴圈消耗。
console script 由 W2.1 提供；在那之前一律用 `PYTHONPATH=vnext/cli/src python -m wfx`。

**rc 慣例**：`0`＝成功、`2`＝用法錯（未知動詞、旗標形狀不對）、`1`＝typed 錯（缺層、設定形狀、
GitHub 讀取未完成、本機 git 不可用）。兩類刻意可區分。

### `brief` 的公開契約

| 旗標 | 預設 | 說明 |
|---|---|---|
| `--task` | 必填 | 不透明任務識別，核心⛔ 不理解其格式（`370`／`#370`／`owner/name#370`） |
| `--role` | 必填 | 角色六值之一 |
| `--stage` | 必填 | 階段五值之一 |
| `--rules-root` | 原始碼樹的 `vnext/rules` | 第 1 層來源，可指向另一個本機 checkout |

角色與階段的值域**只住 `rules/core/values.md`**，程式碼⛔ 不內建任何值——換規則樹就換值域。
⛔ 無 `--task-snapshot`：第 4 層走與 `facts` 同一條唯讀 `wfx.gh`。測試用的固定快照由
`brief.build(..., task_source=…)` 這個**內部**注入點提供，⛔ 不是公開旗標。

## `brief` 的輸出＝派工首屏 ＋ 完整原文附錄

`#370` 的需求方裁定（`issuecomment-5763204699`）：同一份輸出分成兩塊，前面是可直接接手的派工
索引，後面是逐字原文。**整份 brief ⛔ 不是一個畫面**——四層原文會隨卡片生命週期單調成長，
只有首屏有界。以 `#370`／執行者／執行實測：首屏 68 行（8 個來源段）、整份 618 行、
附錄 550 行（62 個來源段）；同一條件下改版前是 574 行、64 段（必要清單那 2 段移進首屏，四層原文零遺漏）。
這些數字是量測，**⛔ 不是 CI 或 rc 的通過條件**，程式與 CI 都⛔ 無行數門檻。

```
# brief
task: … / role: … / stage: …
## 派工首屏          ← 首屏從輸出第一行開始
### 核心概念現值 / 必要清單 / Issue body 章節定位 / 留言定位索引
### 模型資料狀態 / 專案政策來源 / 適用 core 規則定位
## 完整原文附錄      ← 邊界：這一行，常數、恰出現一次
### 適用規則 / 使用者層 / 專案層 / 任務層
```

**邊界可機械定位**：`## 完整原文附錄` 這一行。取首屏就是

```
wfx … brief … | awk '/^## 完整原文附錄$/{exit} {print}'
```

程式內用 `wfx.core.render.split_output(text) -> (首屏, 附錄)`，切開後兩段相加逐字等於原輸出。
PM 可以只把首屏貼進派工單，需要核對時再給整份。

**首屏只有機械資料**：欄位值、相對路徑、節錨、行號、留言 url 與每則留言的首個 `## ` 標題（逐字）。
⛔ 無摘要、⛔ 無截斷、⛔ 無 LLM、⛔ 無內容判讀、⛔ 無留言分類。Issue body 的章節只判
「標題在且其下非空」——這正是 `rules/core/github.md` §1 交給 CLI 的那一件事；五個章節標題本身
也從該節機械抽出，程式碼⛔ 不內建標題字面。

**附錄逐字保留四層全部原文**：Issue body、該卡全部留言、兩類模型資料、專案政策、框架規則，
順序固定、同一來源只出現一次。首屏的索引段⛔ 不重複出現在附錄。唯一刻意的重複是七個核心概念
（首屏一份值、附錄任務層一份值），因為它既是派工要看的現值、也是第 4 層的一段。

**必要清單住在首屏、⛔ 不在附錄再出現一次**：它本來就是角色與階段兩份文件的章節清單，不是原文；
那兩份文件的全文仍逐字在附錄的 `### 適用規則` 裡。

## 四層注入與來源標記

每一段都帶 `[來源: kind:path#節]`，`kind` 恰四值：

| kind | 來源 | 缺了會怎樣 |
|---|---|---|
| `framework` | `--rules-root` 下的 `core/*.md` 六份全載，加選定的 `stages/<階段>.md` 與 `roles/<角色>.md` | typed 失敗（rc=1） |
| `user` | `~/.wf/model-usage.md`、`~/.wf/model-availability.md`，原樣呈現 | **合法 unknown，rc=0** |
| `project` | `<project-root>/.wf/*.md` | typed 失敗（rc=1） |
| `task` | Issue body ＋七個核心概念＋**該卡全部留言**（唯讀 GitHub） | Issue 取不到或 body 為空＝typed 失敗（rc=1） |

使用者層兩檔缺任一檔都印 `使用者層模型資料：unknown`。這是**檔案層**檢查，
⛔ 不逐則判欄位缺漏、⛔ 不判時效——新鮮度由 PM 在派工當下自行判斷（`rules/roles/PM.md` §2）。

**必要清單**＝該角色與該階段兩份文件的章節逐項列出，六個角色各不相同；呈現在首屏。

### 第 4 層的三條邊界

- **全部留言原樣納入、⛔ 不分類。** `rules/core/github.md` §3 的四類是**內容分類**，CLI 判不得；
  自己加「哪些算階段完成留言」的篩選＝CLI 做內容判讀。
- **只投影七個核心概念。** Project 的其餘內建欄位（`Title` 等）**原樣忽略**，⛔ 不是第八個核心概念、
  ⛔ 不因此拒收整份 brief。七概念的唯一居所是 `rules/core/github.md` §2。
- **`.wf/config.json` 未設 `project`、或該卡尚⛔ 無 Project item 時**，七概念照 `facts` 同一形狀印
  `unknown` 且 rc=0，⛔ 不 typed fail。

### `write` 的公開契約

```
write --task <id> [--field k=v …] [--comment-file <f>] [--expect-updated-at <ts>] [--dry-run] [--rules-root <p>]
```

| 旗標 | 說明 |
|---|---|
| `--field k=v` | 可重複；`k` 只收七個核心概念之一，`k=`（空值）＝**清空**該欄位 |
| `--comment-file` | 檔案內容逐字貼成一則留言 |
| `--expect-updated-at` | 寫入基準，逐字取自 `facts` §3 **同一個物件**那一行 |
| `--dry-run` | 遠端零 mutation；⛔ 不要求基準 |

**正常路徑＝`facts` → `write --expect-updated-at <該基準>`，一次成功**；缺基準即拒寫是**負控與安全網**，
⛔ 不是預期會頻繁走到的路徑。值只檢查在不在 `core/values.md` 的值域內——`狀態=退回` 被拒的理由
逐字只有「值不在值域內」，⛔ 不判轉移是否合法。

**基準對應被改的物件**：改欄位比 Project item 的 `updatedAt`、貼留言比 Issue 的。因此
**一次呼叫只改一個物件**：同時給 `--field` 與 `--comment-file` ＝用法錯（rc=2），
因為一個 `--expect-updated-at` 無法同時對到兩個物件。一次退回事件＝**≥1 次欄位寫入 ＋ 1 則留言**
＝兩次呼叫，各自帶自己物件的基準；CLI ⛔ 不耦合兩者、⛔ 不阻擋單獨呼叫、⛔ 不要求成對。

比對只在**第一個 mutation 之前**做一次。**基準只縮小視窗、⛔ 不構成鎖**——基準讀取與寫入之間
⛔ 不具原子性（`rules/core/github.md` §7）。⛔ 無 envelope／fingerprint／續作／鎖定服務／寫入帳本、
⛔ 無開卡／關卡／改 body 能力、⛔ 不重試、⛔ 不做部分失敗補償：一次呼叫寫多個欄位時
逐欄送出、逐欄印結果，中途失敗就停在該欄並以 rc≠0 結束（已寫入的欄位照實印在輸出裡）。

mutation surface 只住 `wfx/gh/writes.py`，且只有 `verbs/write.py` 匯入它；唯讀的 `GhClient`
⛔ 無任何寫入方法（機械錨＝`test_wfx_boundaries.py`）。

## `facts` 的 base 解析

第 ④ 節的 base＝**本次受查 head SHA** 的預期合併目標，以 SHA 查、⛔ 不以分支名查
（detached checkout 與 `--sha` 都沒有分支名，用分支名會讓審核者與執行者算出不同的 base）：

1. 該 SHA 的開啟中 PR `baseRefName` 唯一 ⇒ 用它。
2. 對到多個開啟中 PR 且 base 不同 ⇒ `unknown`，⛔ 不猜。
3. 查詢失敗 ⇒ `unknown`，⛔ 不得當成「沒有 PR」而靜默改用預設分支。
4. **確認**⛔ 無關聯的開啟中 PR ⇒ 才用 repository 預設分支，並在來源標記寫明本行來自預設分支。

⛔ 未新增 `--base` 旗標（公開契約仍是 `facts --task <id> [--sha <sha>]`）。

## 可重現性

**全部輸入不變時輸出逐字相同**：⛔ 無時間戳、⛔ 無絕對路徑、⛔ 無隨機序。
「全部輸入」含同一次遠端讀取；**遠端資料變動導致輸出不同是正確行為**，
⛔ 不得為了讓測試穩定而快取或凍結即時遠端資料。

## 測試

```
python -m pytest vnext/cli/tests -q     # Python 3.14
```

`test_wfx_boundaries.py` 是**單一** C6 結構錨：`wfx` 全樹⛔ 無實際網路客戶端與模型 provider SDK
（純 `urllib.parse` 是網址編碼工具，逐名放行；`urllib.request`／`http`／`socket`／`requests`／
`httpx` 仍全樹禁止），`wfx/core/**` ⛔ 無 `wfx.gh` 與 `subprocess`，`subprocess` 只住 `wfx/gh/`。
⛔ 不做禁用字串掃描、⛔ 不設行數門檻。
