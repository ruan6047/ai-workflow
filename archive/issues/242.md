# #242 [清單] BriefError 不在 KNOWN_ERRORS：amend --brief 形狀不合時以 traceback ＋ rc=1 收場
- state: open  created: 2026-09-03T11:42:10Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/242
- comments: 1

## Body

## 條件 1 · 出處可指

執行 `ruan6047/ai-workflow#221`（`WF-REDESIGN-W3`）的 `R5-001` 處置時，PM 以 `wfcli amend --brief` 寫回卡面，第一次給的簡介**漏了 `⛔ 非射程：` 那一段**，指令以下列形式收場：

```
Traceback (most recent call last):
  File "/Users/ruanruan/Dev/ai-workflow/cli/.venv/bin/wfcli", line 10, in <module>
    sys.exit(main())
  File "/Users/ruanruan/Dev/ai-workflow/cli/src/wf_cli/cli.py", line 66, in main
    return args.func(args)
  File "/Users/ruanruan/Dev/ai-workflow/cli/src/wf_cli/commands/amend_cmd.py", line 1088, in run
    body, old = amend_brief(body, args.brief)
  File "/Users/ruanruan/Dev/ai-workflow/cli/src/wf_cli/card.py", line 1767, in amend_brief
    validate_brief_shape(new_value)
  File "/Users/ruanruan/Dev/ai-workflow/cli/src/wf_cli/brief.py", line 111, in validate_shape
    raise BriefError(
wf_cli.brief.BriefError: 簡介缺少必要標記 ['⛔ 非射程：']；canonical §6.3 要求必含 「適用時機」…
```

退出碼 **1**。留痕：`#221` 的 `issuecomment-5524000028` §四。

## 條件 2 · 是觀察不是結論

`BriefError`（`cli/src/wf_cli/brief.py:66`，`ValueError` 子類）**⛔ 不在 `cli/src/wf_cli/cli.py` 的 `KNOWN_ERRORS` tuple 內**。

⇒ `amend --brief` 給出不合形狀的簡介時，指令**以 traceback ＋ rc=1 收場**，而同一支指令的其他拒收路徑印 `[amend] 拒絕：…` ＋ rc=2。

⚠️ 同時觀察到的另一面：**該次失敗零寫入**——PM 逐位元比對前後 body，唯一差異是同期 handoff 的 Log 行。⇒ **拒收的時機在遠端寫入之前，⛔ 只有收場形狀不同。**

## 條件 3 · 查重留痕

```bash
gh issue list --repo ruan6047/ai-workflow --state all --search "<關鍵字>"
```

| 關鍵字 | 命中 |
|---|---|
| `BriefError` | `#134` `#221` `#165` |
| `KNOWN_ERRORS` | `#53` `#141` `#147` `#37` `#221` `#9` |
| `traceback` | `#141` `#37` `#137` `#9` `#221` |
| `乾淨拒絕` | 20 筆（`#57` `#221` `#142` `#217` `#84` `#16` `#103` `#38` `#129` `#106` `#24` `#43` `#120` `#37` `#141` `#134` `#154` `#107` `#42` `#19`） |
| `stack trace` | `#221` `#37` `#141` `#25` `#19` |

跨關鍵字共同命中且非本卡者：`#141`（CLOSED，`WF-MARKER-WRITE-BOUNDARY1`）／`#37`（CLOSED）／`#9`（CLOSED）／`#147`（CLOSED）／`#53`（CLOSED）。逐一開啟核對：`#37`／`#9` body 對 `BriefError` **零命中**；`#141` 提到 `brief` 12 次但處理的是**寫入邊界守衛偽造分界型控制標記的欄位值**，⛔ 非本項。

## 條件 4 · 屬哪個 repo

`ai-workflow`（將改 `cli/src/wf_cli/cli.py`）。

## 條件 5 · 提案者身分

| 格 | 值 |
|---|---|
| GitHub 帳號 | `ruan6047` |
| session ID | `cc0a7952-07a5-4978-8d03-8b5f48fbc690` |
| 該則訊息定位 | ⚠️ **未取**——本 session ⛔ 無法取得自己當前訊息的 `uuid`。**分類＝驗不了，⛔ 不編造。** |

---

## ⚠️ 收件檢查**⛔ 未做**（逐字登記，⛔ 不是漏填）

`stage-rules/list-intake-requirements.md` 逐字：「**當提案人是 PM：⛔ PM 不得檢查自己的提案。由另一個 PM 做這四項的收件檢查。**」

**本項的提案者就是 PM**（`session cc0a7952-…`，在執行 `#221` 的 `R5-001` 時撞到）⇒ **PM ⛔ 不得自行通過收件檢查**，本項因此**⛔ 沒有收件裁決**。

同檔亦逐字：「這道閘門**機械上不成立，效力只來自留痕**」「**第二個 PM 由誰擔任、原始輸出需求方看不看得到 —— 未定**」。

⇒ 本段即為該留痕。⛔ 不得由本項存在推出它已通過收件檢查。

## ⚠️ 與 `#221` 核心痛點的關係（登記，⛔ 非本項的結論）

`#221` 的核心痛點逐字引用 `templates/handoff-contract.md:205`：「**以 stack trace 收場的 fail-closed ⛔ 不算乾淨拒絕**」。⇒ 本項是該條文的一個**現存實例**，於 `#221` 施工期間由 PM 撞到並登記為另案（`#221` 的 `issuecomment-5524000028` §四）。⛔ `#221` 未修它——⛔ 不在該卡任何一條驗收內。


---

## ✅ 第二 PM 收件裁決 · 條件 2（2026-09-03）

**⚠️ 轉錄來源自述**：裁決由**第二 PM `Codex`**（canonical `AI_WORKFLOW.md:14` 明定「本專案＝Codex」）產出，經**需求方**轉貼，由 PM session `cc0a7952-07a5-4978-8d03-8b5f48fbc690` **逐字轉錄**。GitHub token 為 `ruan6047` ⇒ **author 欄⛔ 不足以區分撰寫者與裁決者**。⛔ **PM 未改動裁決一字。**

### 裁決（逐字）

> #242 條件 2
>
> * 判定：通過
> * 理由：已檢查本段三組陳述：`BriefError` 不在 `KNOWN_ERRORS`；不合形狀時以 traceback＋rc=1 收場、其他拒收路徑為 `[amend] 拒絕：…`＋rc=2；以及該次失敗零寫入、拒收發生於遠端寫入前。各句均在描述程式碼或實測可觀測結果，沒有解法，也沒有未經量測的因果推論。

### 裁決者身分（逐字）

> * GitHub 帳號：`ruan6047`
> * session ID：`01a067f1-4d91-7092-a568-584dbd401460`
> * 該則訊息定位：`2026-09-03T15:45:26.081Z`
> * 裁決時間：`2026-09-03T15:45:26.081Z`

⚠️ PM 註（⛔ 非裁決內容）：該 session ID 與本專案今日七輪查核所用的 `01a062d3-dd75-7be0-bedd-4dc5ca910e9b` **⛔ 不同** —— 這是一次獨立的第二 PM 調用，⛔ 非查核 session 的延續。

### ⚠️ 收件狀態更正

本 body 上方「條件 5」一節之後的原始內容曾記載「收件檢查⛔ 未做」，並引 `stage-rules/list-intake-requirements.md:115`「第二個 PM 由誰擔任 —— 未定」。**該引述是錯的**（見 `issuecomment-5525196715`）。

⇒ **現行狀態**：條件 1／3／4／5 由 PM 自判並已填；**條件 2 已由第二 PM Codex 裁定通過**。⇒ **五條件齊，收件通過。**

⚠️ ⛔ 仍不得由此推出本項該做或內容正確——`list-intake-requirements.md` 逐字「⛔ 不判斷這件事該不該做 —— 那是開卡之後、需求階段 R1 的事」。


## Comment 5525196715 · 2026-09-03T11:43:36Z

## PM 更正 · 收件檢查那一段引錯了（2026-09-03）

**轉錄來源自述**：本則由 PM session `cc0a7952-07a5-4978-8d03-8b5f48fbc690` 撰寫；GitHub token 為 `ruan6047`。**指認者是需求方**（原話：「第二ＰＭ不是由ＣＯＤＥＸ負責嗎」），⛔ 非 PM 自查；PM 已逐字複驗成立。

⚠️ 本則更正 body 末段「⚠️ 收件檢查⛔ 未做」的**兩處引述錯誤**。body 原文⛔ 未編輯，保留原樣。

### 一、⭐ 第二 PM **⛔ 不是「未定」——canonical 明定為 Codex**

`AI_WORKFLOW.md:14` 逐字：

> | 第二 PM | PM 自產物的檢查（**本專案＝Codex**）。⚠️ 它有**完整寫入通道**——「只查核、⛔ 不動狀態」是紀律⛔ 不是機制；身分靠 session ID ＋ transcript 核對 |

⇒ PM 在 body 引的 `stage-rules/list-intake-requirements.md:115`「⛔ 第二個 PM 由誰擔任 —— **未定**」**與 canonical 直接矛盾**，而 **canonical 是權威**。

### 二、需第二 PM 的**⛔ 不是四項，是一項**

決議 `docs/research/WORKFLOW-REDESIGN-2026-08-30.md:49` 逐字：

> **收件五條件**（PM 只判流程）：出處可指／**是觀察不是結論（⭐ 唯一需第二 PM）**／查重留痕（列關鍵字＋命中）／屬哪 repo／提案者身分

而 `list-intake-requirements.md:109` 逐字寫「由**另一個 PM** 做**這四項**的收件檢查」。⇒ **兩者矛盾**（四項 vs 一項）。

### 三、更正後的實際狀態

| 條件 | 誰判 | 現況 |
|---|---|---|
| 1 出處可指 | PM | ✅ 已填（traceback 全文＋留痕 URL） |
| **2 是觀察不是結論** | **第二 PM ＝ Codex** | ⏳ **待 Codex 裁決**——⛔ PM 不得自判 |
| 3 查重留痕 | PM | ✅ 已填（5 關鍵字＋逐一開啟核對） |
| 4 屬哪 repo | PM | ✅ `ai-workflow` |
| 5 提案者身分 | PM | ⚠️ 兩格已填；訊息定位格**未取**（本 session 取不到自己的 `uuid`），**分類＝驗不了，⛔ 不編造** |

⇒ **⛔ 不是整份收件檢查未做**，是**條件 2 一項待 Codex 裁決**。

⚠️ 機制上仍如 `:113` 所述：Codex **⛔ 沒有 wfcli 也⛔ 沒有 gh token** ⇒ 裁決須由**需求方轉貼、PM 逐字轉錄**，寫入 author 仍是 `ruan6047`。**⛔ 不得由 author 欄推斷裁決者。**

### 四、⚠️ 一併登記：`stage-rules/list-intake-requirements.md` 有兩處與上游矛盾

- `:115` 「第二個 PM 由誰擔任 —— 未定」 ⇔ **canonical `AI_WORKFLOW.md:14` 已明定為 Codex**
- `:109` 「由另一個 PM 做**這四項**」 ⇔ **決議 `:49` 明定只有條件 2 需要第二 PM**

⇒ **這是 stage-rules 對 canonical 與決議的漂移。** ⛔ 本項⛔ 不承接該修正（⛔ 不在本項射程），**登記於此**。⛔ 不得由本則存在推出它已被處理。

