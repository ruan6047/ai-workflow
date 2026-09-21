# wfx — vNext CLI

動詞只有三個：`brief`／`facts`／`write`。**本次（W1.6）只交 `brief`。**

CLI 只載入與呈現資訊，**內容判斷由人或負責該內容的 AI 完成**（`rules/core/boundaries.md` §4）。
`brief` ⛔ 不判內容品質、⛔ 不選模型、⛔ 不呼叫 AI、⛔ 不查額度、⛔ 不判備註是否過期、
⛔ 不解析散文語意、⛔ 不判退回是否合法、⛔ 不認識「工作包」。

## 跑它

```
PYTHONPATH=vnext/cli/src python -m wfx brief \
  --task 'ruan/ai-workflow#370' --role 執行者 --stage 執行 \
  --project-root vnext --task-snapshot <快照.json>
```

console script 由 W2.1 提供；在那之前一律用 `PYTHONPATH=vnext/cli/src python -m wfx`。

| 旗標 | 預設 | 說明 |
|---|---|---|
| `--task` | 必填 | 不透明任務識別，核心⛔ 不理解其格式 |
| `--role` | 必填 | 角色六值之一 |
| `--stage` | 必填 | 階段五值之一 |
| `--rules-root` | 原始碼樹的 `vnext/rules` | 第 1 層來源，可指向另一個本機 checkout |
| `--project-root` | 目前工作目錄 | 第 3 層；讀 `<project-root>/.wf/*.md` |
| `--task-snapshot` | 無 | 第 4 層；見下節 |

角色與階段的值域**只住 `rules/core/values.md`**，程式碼⛔ 不內建任何值——換規則樹就換值域。

## 四層注入與來源標記

每一段都帶 `[來源: kind:path#節]`，`kind` 恰四值：

| kind | 來源 | 缺了會怎樣 |
|---|---|---|
| `framework` | `--rules-root` 下的 `core/*.md` 六份全載，加選定的 `stages/<階段>.md` 與 `roles/<角色>.md` | typed 失敗（rc=2） |
| `user` | `~/.wf/model-usage.md`、`~/.wf/model-availability.md`，原樣呈現 | **合法 unknown，rc=0** |
| `project` | `<project-root>/.wf/*.md` | typed 失敗（rc=2） |
| `task` | Issue body 五章節＋七個核心概念＋已貼出的階段完成留言 | typed 失敗（rc=2） |

使用者層兩檔缺任一檔都印 `使用者層模型資料：unknown`。這是**檔案層**檢查，
⛔ 不逐則判欄位缺漏、⛔ 不判時效——新鮮度由 PM 在派工當下自行判斷（`rules/roles/PM.md` §2）。

**必要清單**＝該角色與該階段兩份文件的章節逐項列出，六個角色各不相同。

## 任務層快照

W1.6 時 `facts`（W1.7）與 vNext Project（W1.5）都還不存在，任務層因此由一份**固定快照**注入。
`facts` 交付後，遠端當下值由它提供；快照仍可用來對同一份輸入逐字重跑。

```json
{
  "task": "ruan/ai-workflow#370",
  "issue_body": "## 需求\n…\n## 裁定紀錄\n…",
  "fields": {"狀態": "進行中", "階段": "執行", "owner": "ruan",
             "風險": "重要", "緊急性": "一般", "期限": "", "Resource": ""},
  "comments": [{"url": "https://…", "body": "## 規劃階段完成\n…"}]
}
```

- `task` 必須與 `--task` 逐字相同，不符即 typed 失敗。
- `fields` 只認七個核心概念；出現第八個鍵 ⇒ typed 失敗（`rules/core/github.md` §2）。
  缺鍵合法，印成空值——W1.5 建立 item 時欄位本來就可能是空的或平台預設。
- `issue_body` 與每則 `comments[].body` **原樣輸出**，⛔ 不驗章節、⛔ 不判留言屬於哪一類。

## 可重現性

**全部輸入不變時，輸出逐字相同**：⛔ 無時間戳、⛔ 無絕對路徑、⛔ 無隨機序。
輸入（規則樹、`~/.wf/`、`.wf/`、快照）變了輸出就該變——那是正確行為，
⛔ 不得為了讓測試穩定而快取或凍結資料。

## 測試

```
python -m pytest vnext/cli/tests -q     # Python 3.14
```

`test_wfx_scope.py` 是結構錨：`wfx` 全樹⛔ 無 HTTP／模型 provider SDK import，
`wfx/core/**` ⛔ 無 `wfx.gh` 與 `subprocess`。⛔ 不做禁用字串掃描、⛔ 不設行數門檻。
