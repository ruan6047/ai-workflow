# WF-25：跨家族查核寫入通道

產生時間：2026-08-08（Asia/Taipei）
基線：`origin/main` `16953b1a535bf9551e4bac300e98a67b2f17d41a`

## 1. 實測能力盤點

此表只記錄可由本次命令輸出證實的能力；「未量測」不是否定能力。刻意不以對真實
Issue/PR 的寫入來測試，以免為盤點製造不屬本卡的 control-plane event。

| 實際查核者 | `wfcli` | GitHub 留言 | GitHub PR review | 證據與結論 |
| --- | --- | --- | --- | --- |
| GPT-5@Codex（本執行環境；使用者明示也是查核者） | 已實測 `wfcli review --validate-only` 成功；真實狀態寫入未測 | 未量測 | 未量測 | `gh auth status` 顯示帳號 `ruan6047`、token scope 含 `repo`／`project`；scope 不是一次寫入實測，故不把它升格為「已測」 |
| Claude@GitHub Copilot（#111/#112/#113 的實際跨家族查核者） | 未能實測 | 未能實測 | 未能實測 | 本環境沒有其 session／憑證／可操作 UI；不得由「看起來合理」推定能力 |

實測命令與輸出摘要（可重跑）：

```text
cd cli && uv run wfcli review --validate-only ...
[review] 驗證通過（--validate-only，未寫入任何狀態）：APPROVE／core_pain_resolved=yes／self_run 1 項／findings 0 項

gh auth status
Active account: ruan6047
Token scopes: gist, project, read:org, repo, workflow
```

## 2. 候選方案比較

| 方案 | 漏轉錄的失效方向 | 跨工具憑證 | 身分偽造面 | `doctor` 可偵測什麼 |
| --- | --- | --- | --- | --- |
| A. 給每個查核工具 `wfcli` 憑證 | 寫入失敗時保守地卡在待查核；若憑證遭冒用則危險地偽造通過 | 需要，且要解決保管、撤銷、工具是否可持有 | CLI 本身不驗證操作者；`--reviewer` 仍是自由字串 | 僅能檢查 event 存在，不能證明持證者真是宣稱的查核者 |
| B. 查核者在 GitHub Issue comment 或 PR review body 留固定收據，PM 以 `wfcli` 轉錄 | 收據有、轉錄漏時保守地卡住；收據和 event 都沒有時不得判斷是否查核 | 不需要 `wfcli` 憑證；只需查核工具可用其 GitHub 身分留言／review | GitHub author 可驗證；模型/工具名仍只是自述，`--reviewer` 不可單獨信任 | 收據有但無 event → `receipt_untranscribed`；兩者都無 → `unobservable`（非「未查核」） |
| C. 純 PM 轉錄（現況明文化） | 漏轉錄時保守地把已查核當未查核，流程卡住 | 不需要 | PM 可任填 `--reviewer`，沒有外部可核對身分 | 無法區分「未查核」與「已查核但 PM 漏轉錄」；不符合本卡核心痛點 |

## 3. 建議：採 B，並保留 C 作為受控 fallback

採 B 的理由是它不把跨工具憑證當成前提，且把原先不可見的外部裁決變成可查的
GitHub artifact。PM 仍是唯一 lifecycle writer：收據只是一份 evidence，不改 Issue
狀態；`wfcli review` 才建立 review event 和狀態轉換。

收據格式如下，報告 hash 使用完整查核報告原文的 UTF-8 SHA-256；PM 轉錄前必須重算：

```text
<!-- wf-review-receipt:v1
card_id: <CARD_ID>
source_sha: <40-char SHA>
report_sha256: <64-char lowercase hex>
-->
```

「查核者身分」拆成兩層：GitHub author 為可驗證帳號；`Claude@GitHub Copilot` 一類
模型/工具標籤只能被記錄為自述。若 Copilot 無法留收據，C 仍可作為例外轉錄，但必須
標記 `unobservable`，不允許把自由字串升格為已驗證身分，也不允許結案前跳過人工確認。

`wfcli doctor` 的具體呼叫：

```bash
wfcli doctor /abs/repo --review-channel \
  --owner ruan6047 --project 4 \
  --repo owner/repo --issue-number 123 --card-id CARD-ID \
  --source-sha 0123456789012345678901234567890123456789
```

> `--owner`／`--project` 自 #20 起為必填（**破壞性介面變更**）：三面一致的第三面要讀
> Project 交付狀態欄，少了它只驗到留言與 Log 兩面，而兩面一致的半寫入看起來與正常
> 裁決完全一樣。舊格式的呼叫會以 exit 2 失敗並列出缺少的旗標。

它輸出**五種**互斥結果（本檔原記三種，#17 與 #20 各增一種）：

| 結果 | 意義 | 下一步 |
| --- | --- | --- |
| `recorded` | 三面一致：裁決留言、同 attempt 的 Log 索引行、Project 交付狀態欄相符 | 無 |
| `half_written` | 前兩面成立但交付狀態不符或讀不到（#20） | 補齊狀態欄，**不要重跑查核** |
| `marker_quarantined` | 找到受契約管轄但不合格的 marker（#17） | 去修那一則壞掉的留言 |
| `receipt_untranscribed` | 有外部收據、無 review event | 要求 PM 轉錄 |
| `unobservable` | 兩者皆無 | 去查有沒有人查核過 |

除 `recorded` 外皆 fail-closed；加上 `--strict` 時回傳 exit 1。尤其 `unobservable` 的
文字明確禁止「沒有紀錄」→「沒有查核」的推論。
這是偵測「可觀測留痕缺口」的上限：一個完全沒有外部訊號的私有對話，系統無從偵測
它實際是否發生，任何聲稱能偵測都會是虛假能力。

## 4. 2026-08-08 三案回放

| 卡 | 當時的查核 | 若已有 B | doctor 結果與後續 |
| --- | --- | --- | --- |
| #111 | Claude@GitHub Copilot T4 APPROVE | 查核者在 #111 留收據，SHA `789995fe0aba50157c13182010bc1c26867a1af9`；PM hash 對帳後轉錄 APPROVE | `recorded`；保留 GitHub author 與原報告 hash，`INFO-002` 的事實錯誤仍原樣轉錄、另立 PM 更正 |
| #112 | R1 `REQUEST_CHANGES` @ `e2d6bb1`，amend 成 `3235bea` 後 R2 APPROVE；tree/parent 相同且 diff 空 | **兩個收據、兩個 SHA**：R1 對 `e2d6bb19e8b0412652b6eb8b19bad6e9f8e7a179`，R2 對 `3235beaf8fa0b442e7a15f1e6e2858f794e90eb2`。即使 tree 相同，attempt identity 仍是 `(card, epoch, source_sha)`，不可合併 | R1 必須先轉錄退回、handoff iteration +1；R2 收據只可對 R2 SHA 轉錄 APPROVE。對任一 SHA 漏轉錄都會各自報 `receipt_untranscribed`，不會把 R1/R2 混成一筆 |
| #113 | Claude@GitHub Copilot APPROVE，17 項 self_run、4 則 findings | 查核者在 #113 留 `0b8aad45622abd85a9168e5f7110ba81b7598634` 收據，PM 再轉錄 | `recorded`；PR 的 0 reviews/0 comments 只代表 PR 沒紀錄，不能再被用來反推查核未發生 |

## 5. 實作與驗證

- `cli/src/wf_cli/doctor.py` 新增純函式 `audit_review_channel()`；只有同卡、同 attempt 的 `wfcli review` event，且 Issue Log 有對應 `review by wf-cli` 索引才是 `recorded`。
- `wfcli doctor --review-channel` 唯讀讀取 Issue comment，若目標是 PR 另讀 PR review body；輸出收據 URL 與 GitHub author。
- 單元測試涵蓋：已收據未轉錄、完全不可觀測、真實 renderer 輸出、跨卡／貼上裁決拒收、PR review body 收據。
- 驗證：`cd cli && uv run pytest tests/test_doctor.py -q`。
