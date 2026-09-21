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

**必要清單**＝該角色與該階段兩份文件的章節逐項列出，六個角色各不相同。

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
