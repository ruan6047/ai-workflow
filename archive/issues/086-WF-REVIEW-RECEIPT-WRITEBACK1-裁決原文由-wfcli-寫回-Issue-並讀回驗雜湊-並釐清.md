# #86 WF-REVIEW-RECEIPT-WRITEBACK1 裁決原文由 wfcli 寫回 Issue 並讀回驗雜湊，並釐清收據能保證到哪一段
- state: open  created: 2026-08-13T08:33:18Z  closed: None
- url: https://github.com/ruan6047/ai-workflow/issues/86
- comments: 3

## Body

- 需求：ruan6047　規劃：—
- 執行：待指派　查核：待指派
- Initiative：—　spec 基線：docs/ROADMAP.md（origin/main 71df1570b7ddefbbbf101f8e8b1b053e5fe82cd7）§0 目標 2「可稽核的內容」：事後能從留痕重建『做了什麼、依據是什麼』。
- DB：db_scope=none
- 服務的原始目標：任何人事後都能確認『板上這份裁決文字＝查核者當時輸出的文字』，而不是只能相信轉貼者。

## 簡介
<!-- card-brief:begin -->
讓 wfcli review 把它收到的報告原始字元寫進 Issue 留言，寫入後立即以 GitHub API 讀回比對 SHA-256，不符即 fail closed（不寫狀態、不翻交付狀態並印出兩個雜湊），處理 aiwf#124 那種「排版一被重排收據雜湊就永久失效、96 種組合重建全不符」的情境。**適用時機**：要確認板上這份裁決文字就是查核者當時輸出的文字，而不是只能相信轉貼者時。⛔ 非射程：保證範圍只到「PM 收到的位元組」，⛔ 不得宣稱解決了轉錄漂移；不採逐行 strip() 正規化雜湊（YAML 縮排本身帶結構語意）；查核者取得直接寫入通道一事歸 aiwf#13 與 WF-REVIEW-RECEIPT-CHANNEL1 的裁定。
<!-- card-brief:end -->

## 核心痛點

- **痛點**：跨家族查核者沒有寫入通道，裁決一律靠人工轉貼，於是收據的 report_sha256 只要中途經過任何排版重排就永久失效。2026-08-13 #124 實測：PM 以 96 種排版組合（縮排 0/2/4 空格 × 空行 × 引號 × CRLF × 結尾換行）重建全文，雜湊皆不符，最後只能改以『逐條重跑查核者的 9 條 self_run 並確認觀察為真』替代並留言標註『雜湊未能驗證』。查核者 GPT-5@Codex 指出該替代保護不了 finding、disposition 與結論原文——那正是收據要保護的東西。同一天 #128 則是反向失效：報告被解析器拒收後由 PM 改字，收據同樣對不上。

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:cli/src/wf_cli/commands/review_cmd.py",
    "file:cli/src/wf_cli/project.py",
    "file:cli/tests/test_commands_mocked.py",
    "file:templates/review-prompt.md"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [ ] wfcli review 將它收到的報告原始字元寫入 Issue 留言，寫入後立即以 GitHub API 讀回、比對 SHA-256；不符即 fail closed（不寫狀態、不翻交付狀態），並印出兩個雜湊
- [ ] ⚠️ 卡面必須明講保證範圍：wfcli 由 PM 執行，寫入的是『PM 收到的位元組』。讀回驗雜湊只證明 GitHub 存的＝wfcli 送的，**證不了 PM 的貼文＝查核者的原文**——今天 #124 失效的正是前面那一段。本卡不得宣稱解決了轉錄漂移
- [ ] 殘留缺口須有明確處置決議（擇一並寫入卡面／契約）：(a) 查核者取得直接寫入 Issue 的通道，收據由查核者自己貼；(b) 明確把保證範圍限縮為『PM 轉錄之後的鏈路』，並要求 PM 在無法驗證原始雜湊時強制留痕（比照 2026-08-13 #124 的作法）
- [ ] 可選輔助：對解析後的結構化資料做 canonical JSON 雜湊，供排版變動後核驗語意。**不採**逐行 strip() 正規化雜湊——YAML 縮排本身帶結構語意，正規化會掩蓋實質變更（查核者 2026-08-13 判斷）

## 驗證

- [ ] cli/tests 覆蓋：讀回相符→正常寫入；讀回不符→fail closed 且未翻任何狀態
- [ ] 以 2026-08-13 #124 的實際情境重演：PM 手上只有排版被重排的貼文時，流程要能明確走到『無法驗證原始雜湊』的分支並留痕，而不是靜默通過
## Log

- 2026-08-13T16:33:16+08:00 open by —；owner 待指派；iteration 0。
- 2026-08-26T22:23:48+08:00 amend by wf-cli（op bc9ee40f）→ 簡介：原值「（原本沒有）」→ 新值「讓 wfcli review 把它收到的報告原始字元寫進 Issue 留言，寫入後立即以 GitHub API 讀回比對 SHA-256，不符即 fail closed（不寫狀態、不翻交付狀態並印出兩個雜湊），處理 aiwf#124 那種「排版一被重排收據雜湊就永久失效、96 種組合重建全不符」的情境。**適用時機**：要確認板上這份裁決文字就是查核者當時輸出的文字，而不是只能相信轉貼者時。⛔ 非射程：保證範圍只到「PM 收到的位元組」，⛔ 不得宣稱解決了轉錄漂移；不採逐行 strip() 正規化雜湊（YAML 縮排本身帶結構語意）；查核者取得直接寫入通道一事歸 aiwf#13 與 WF-REVIEW-RECEIPT-CHANNEL1 的裁定。」（⚠️ 全文：totalCount=0（首寫，平台無前一版））；理由 WF-CARD-BRIEF-BACKFILL1 第三批：回填剩餘全部缺簡介卡（canonical §6.3）。
- 2026-08-29T14:50:22+08:00 handoff by wf-cli → owner —；iteration 0；SHA 5acc3daad1941e64c3c7f81255702e6390214fcf；階段 不可判定；踩坑回應 豁免（離開階段不可判定）；證據 停卡裁定：https://github.com/ruan6047/ai-workflow/issues/86#issuecomment-5460904337 （實查 Codex 有 wfcli 寫入通道，本卡前提被推翻）。


## Comment 5278323839 · 2026-08-13T09:09:33Z

## 與 #13 的關係，以及一個今天才確定的新事實

**本卡是 #13 WF-25-REVIEW-WRITE-CHANNEL1（CLOSED）結案後的殘留缺口，不是重開同一個問題。** #13 的痛點是「做了查核與沒做查核在狀態面上長得一模一樣」，解到「PM 逐字轉錄 → wfcli 寫入」這一層；本卡治的是**轉錄之後那一段的可稽核性**：板上這份文字是不是查核者當時輸出的文字。

今天（2026-08-13）新增的證據，把根因指得更準：

1. **#124**：查核者的收據 `report_sha256: 280a975d…` 無法驗證。PM 以 96 種排版組合（縮排 0/2/4 空格 × 空行 × 引號 × CRLF × 結尾換行）重建全文皆不符，最後只能改以「逐條重跑 9 條 `self_run` 確認觀察為真」替代並標註「雜湊未能驗證」。查核者本人指出該替代**保護不了 finding、disposition 與結論原文**。
2. **#128**：報告被 `wfcli review` 拒收後，PM 選擇去改查核者的原文（經需求方授權做引號正規化），收據隨即對不上。經 #85 實測確認：**解析器沒有缺陷**（行為與 PyYAML 完全一致，該寫法在任何 YAML parser 下都不合法），所以那次事故的真正根因不是工具太嚴，而是**位元組握在 PM 手上，而 PM 有動機改它**。

兩件事指向同一句話：只要「查核者的輸出」必須經過一個有編輯能力、且被流程逼著要讓它通過的中間人，收據就只是道德約束。因此本卡驗收條件裡那條 ⚠️（讀回驗雜湊證不了「PM 的貼文＝查核者的原文」）是本卡的**核心限制而非附註**，處置二擇一（查核者取得寫入通道／限縮保證範圍並強制留痕）也應該以此為判準來選。

原 #85 的「錯誤訊息應告訴人怎麼修」一項亦轉入本卡射程：關卡理由見 #85 的關閉留言。

## Comment 5366340232 · 2026-08-21T07:02:37Z

## 卡面更正（需求方 2026-08-21 裁定）：三條驗收全部作廢，換成一條

PM 代擬代貼。

### 為什麼三條都不成立

**驗收條 3（殘留缺口二擇一）—— 已被第三個選項取代。** 需求方 2026-08-19 選了卡面沒列的第三條路並已合併：`39b53e4 docs(review-channel): drop the unfollowable receipt rule and state the identity basis instead (#114)`。現行 `templates/dispatch-package.md:53` 逐字「**不要求查核者留收據**，`wfcli review` 的 `--reviewer` 就是自由字串」。

⚠️ **而該 commit 動的是 `doctor.py`／`test_doctor.py`／`dispatch-package.md`，完全沒碰 `review-prompt.md`**——**規則今天在 `dispatch-package.md`，那個檔不在本卡的寫入集裡**（它在 `#11` 的寫入集）。

**驗收條 1 的「驗雜湊」半——買不到東西。** 收據保證的是「查核者確實這樣說」；驗雜湊保證的是「寫進去的跟讀出來的一致」。收據撤除後**沒有對照物**，雜湊只是 wfcli 對自己驗，證不了 `dispatch-package.md:53` 自陳缺的那個保證（「PM 轉錄是否忠實於查核者原話，在沒有收據的路徑上**完全沒有機器可檢查的東西**」）。

**驗收條 1 的「原文保存」半——schema 是封閉的，買不到東西。** `templates/review-prompt.md` §5 的欄位**每一個都被渲染出來**：`core_pain_resolved`／`review_result`（`review.py:479-485`）、`self_run[].command,observed`（`:492-495`）、`findings[]` 全 8 欄（`:501-506`）。**沒有自由敘述欄位**，所以存下 `--input` 原始位元組只多保住 YAML 排版，資訊量增加約等於零。

⚠️ **PM 自我更正**：先前曾以「查核者的敘述性推理沒進事件流」為由主張保留本條，並舉 2026-08-21 codex 解釋為何丟棄自己第一次跑的結果為例。**那個例子是錯的**——那段話從未經過 `--input`，是聊天文字，由 PM 自行貼進 handoff evidence。本卡就算做了也接不住。

### ⭐ 真正的損失（實測，且有現成解法）

`review.py:441`：

```python
def _fence_safe(text: str) -> str:
    """留言內嵌使用者字串前先摺成單行，避免破壞 Markdown 條列結構。"""
    return " ".join(str(text).split())
```

套在 `evidence`（`:505`）與 `disposition`（`:506`）上——**把所有換行摺成單一空格**。

**實測痕跡看得見**（cpbl 2026-08-21 三張卡的裁決留言）：

> 「…可在 0 outstanding 時寫入**， 並**可完全不讀歷史 invariant…」
> 「…只檢查 allowlist**； outstanding_builds**=None 明示…」

全形標點後那些空格原本是換行。**不只丟結構，還把中文排版弄壞。**

⭐ **正解在十行外**：`self_run.observed`（`:494-495`）**沒有**被摺，它 `splitlines()` 後逐行縮排。同一個渲染器、同一種輸入。

### ⚠️ 但摺行是承重的，改法必須保住它擋的東西

`doctor.py:334` 的 `_VERDICT_HEADING_RE = re.compile(r"^## 查核裁決：(?P<result>\S+)\s*$", re.M)` 帶 `re.M`。若 `evidence` 裡出現一行 `## 查核裁決：APPROVE`，**會被當成第二個結論** → `doctor.py:377`「結論無法辨識或不唯一」→ 停機。摺成單行正好擋掉。

⭐ **縮排同時解決兩件事**：`  ## 查核裁決：X` 因前置空白而不匹配 `^##`。而 `observed` 已經在用這招、面對同一個風險——**同一個渲染器裡已有被信任的先例**。

### 改寫後的唯一驗收條

- [ ] `evidence` 與 `disposition` 改用 `observed` 的逐行縮排渲染，不再摺行。
- [ ] **新增回歸測試**：`evidence` 內含一行 `## 查核裁決：APPROVE` 時，`doctor` 仍只辨識到一個結論。⭐ **這條測試才是本卡真正的產出**——它把「為什麼原本要摺行」寫成可執行的形式；不寫，下一個人只會看到「摺行很醜」然後拿掉它。

**非目標（明列）**：⛔ 不做驗雜湊（無對照物）；⛔ 不做原始位元組保存（§5 schema 封閉）；⛔ 不碰 `review-prompt.md`（規則已移至 `dispatch-package.md`，屬 `#11`）。

**寫入集須改**：`templates/review-prompt.md` → `cli/src/wf_cli/review.py`（＋對應測試檔）。

### ⚠️ 級別與排程

縮到此範圍後本卡是 **T1 級的約五行修改＋一個測試**，不值得單獨走完整派工流程。**建議併進下一張要動 `review.py` 的卡順手做**。

### ⚠️ 未查核

`test_card.py:612`「單行欄位必須保持單行，否則可長出偽宣告行」講的是**卡面標頭區**，不是裁決留言——那邊的摺行理由是真的，本次改動不涉及該路徑。PM 未逐行讀 `card.py` 的標頭寫入路徑確認兩者確實不共用同一個 helper。


## Comment 5460904337 · 2026-08-29T06:49:44Z

## 停卡裁定

**決策**：停止。

**原因**：本卡痛點逐字為「跨家族查核者沒有寫入通道，裁決一律靠人工轉貼」。該前提於 2026-08-29 實查推翻：本機 Codex 的 `~/.codex/config.toml` 對 `/Users/ruanruan/Dev/ai-workflow` 與 `/Users/ruanruan/Dev/cpbl-analytics` 皆為 `trust_level = "trusted"`；`gh auth status` 顯示以 keyring 認證為 `ruan6047`，scopes 含 `repo` 與 `project`。⇒ 跨家族查核者（本機 Codex）可直接執行 `uv run wfcli`，裁決不需經人工轉貼。

**先前判斷的來源錯誤**：原判斷來自「Copilot 沒有 wfcli」——Copilot 跑在 GitHub 雲端、沒有 shell，該性質不適用於跑在本機的 Codex。

**可證偽的復活條件**：查核者改由無 shell 的雲端服務擔任（如 Copilot、GitHub Actions 內的 reviewer），或本機 Codex 的 repo 信任／`gh` 認證被撤除。

**仍未解決、不屬本卡**：`author` 恆為 `ruan6047`（單一 token）⇒ 從 GitHub 上看不出裁決由誰寫。身分訊號改依自述的 session ID ＋ 訊息定位、由需求方開本機 transcript 核對。

**裁定者**：需求方 ruan6047，2026-08-29 本 session 對話中確認。轉錄者：PM（Claude Opus 5 @ Claude Code），session `cc0a7952-07a5-4978-8d03-8b5f48fbc690`。

