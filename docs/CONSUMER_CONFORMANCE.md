# 消費者符合度登記 — ai-workflow

本檔是 [`templates/handoff-contract.md`](../templates/handoff-contract.md) §6 所要求的登記，登記對象是 **ai-workflow repo 自身的消費者**。

本 repo 是該契約的 canonical 來源，同時也受自己定義的機制管理（dogfooding）。它沒有 `docs/HANDOFF_CONTRACT.md` 這種採用者副本，因此 §6 的登記無處可填——這份獨立檔案就是它的落點。反過來說，各採用專案應在**自己的**副本 §6 就地登記，或另立同名檔案，**不要**引用本檔：本檔記錄的是 ai-workflow 的實作狀態，不是任何其他專案的。

> **未登記等同未生效。** 本檔存在的唯一理由，是讓「契約寫著 fail-closed、消費者實際 fail-open」這種狀態可被查出來。若某項要求在下表沒有對應列，一律視為未實作。

## 1. 消費者：`audit_review_channel()`

- 位置：[`cli/src/wf_cli/doctor.py`](../cli/src/wf_cli/doctor.py)（`wfcli doctor --review-channel`）
- 讀取的 marker：`wf-review-event:v1`、`wf-review-receipt:v1`
- 對照的契約版本：`templates/handoff-contract.md` §3.1（`WF-REVIEW-EVENT-MARKER-CONTRACT1`）

### 1.1 已實作

- §3.1.3 三面一致中的兩面（第三面見落差 9）。v1 事件與 legacy 的 Log 對帳判準**刻意不同**：
  - **v1 事件**：同一行同時含 `review by wf-cli` 與該 `attempt_id`，且 attempt 以 token 邊界比對（`attempt in line` 會讓 `…-e0-<sha>` 命中 `…-e0-<sha>x`）。
  - **legacy**（完全不含 `wf-review-event:` 前綴者）：維持基線的全文各自搜尋，不要求同一行。收緊它會讓既有舊卡由 `recorded` 變成 `unobservable`，那是回歸而非修復。
  - **混合歷史的優先序**：同一 `attempt_id` 一旦存在受管轄的 v1 事件，**不得再由 legacy 路徑替它背書**。否則 v1 事件只要旁邊有一則同 attempt 的 legacy 文字，就能繞過同行索引要求——v1 的兩面一致將從未被真正要求。legacy 對「沒有 v1 對應」的 attempt 仍維持寬鬆對帳。
- §3.1.6 的 `receipt_untranscribed` 與 `unobservable` 兩態，且 `unobservable` 的輸出文字明確禁止「沒有紀錄 → 沒有查核」的推論。
- receipt 的同卡、同 `source_sha` 比對，並輸出收據 URL 與 GitHub author。

### 1.2 落差

| # | 契約要求 | 現況 | 失效方向 | 追蹤 |
|---|---|---|---|---|
| 1 | §3.1.4 未知版本不得回退 legacy | ✅ 已修：`v2` marker → `marker_quarantined` | — | 已閉（#17） |
| 2 | §3.1.3 必填三欄 | ✅ 已修：缺 `attempt_id` → `marker_quarantined` | — | 已閉（#17） |
| 3 | §3.1.3 鍵集合封閉 | ✅ 已修：多出未定義鍵 → `marker_quarantined` | — | 已閉（#17） |
| 4 | §3.1.3 順序與單一空白鎖定 | ✅ 已修：欄位錯序 → `marker_quarantined` | — | 已閉（#17） |
| 5 | §3.1.3 三欄自洽 | ✅ 已修：`attempt_id` 屬別卡 → `marker_quarantined` | — | 已閉（#17） |
| 6 | §3.1.4 per-card halt 結果態 | ✅ 已修：新增 `marker_quarantined`，與 `unobservable` 分離 | — | 已閉（#17） |
| 7 | §3.1.4 halt 解除路徑 | **仍缺**：契約只定義 `review-marker-clearance` 的事件欄位，未定義其在 Issue 留言平面的表示法，亦無 writer；消費者無從辨識哪則留言是 clearance | fail-closed（停機無法由機器解除，只能人工處理） | 表示法定義歸 [#16](https://github.com/ruan6047/ai-workflow/issues/16)；消費實作卡未開 |
| 8a | §3.1.5 重複 event 的保守停機 | ✅ 已修：同 `attempt_id` 多則事件 → `marker_quarantined` | — | 已閉（#17） |
| 8b | §3.1.5 語意比對（放行合法重送） | 無；裁決語意只在散文，無結構化承載 | fail-closed（合法重送會被停機卡住） | 設計歸 [#16](https://github.com/ruan6047/ai-workflow/issues/16)；實作卡未開 |
| 9 | §3.1.3 三面一致的第三面（Project 交付狀態欄） | 未讀取；半寫入無表達態 | fail-open | [#20](https://github.com/ruan6047/ai-workflow/issues/20) |

**落差 7 的性質已改變。** 修復前它是 fail-open（停機根本不會發生，所以「無從解除」不痛不癢）；修復後停機真的會發生，而解除路徑仍不存在——方向轉為 fail-closed，代價是**遇到不合格 marker 的卡只能人工處理**。這是刻意的取捨：卡住要人看，好過放行一則讀不懂的裁決。

**落差 9 已開追蹤卡 [#20](https://github.com/ruan6047/ai-workflow/issues/20)。** 它在 #17 的驗收條件中未涵蓋（#17 聚焦 marker 合規與停機態），而 `audit_review_channel()` 的簽章不接受 Project 欄位值，補它需要改呼叫端。方向是 fail-open，依 §6 規則必須有追蹤卡；該卡由 #17 的 R1-004 查核裁定要求開立。

落差 8a／8b 的拆分理由：§3.1.5 延遲生效期間的保守行為（多則同 `attempt_id` 事件一律停止判定）**只需要消費者變更**，不依賴結構化承載，故可在 #17 內完成；只有「分辨語意一致以放行合法重送」才需要寫入端提供結構化裁決承載。兩者失效方向相反，混為一項會掩蓋 8a 的 fail-open 性質。

落差 1–5、8a 的修復證據可重跑：以下探針對六個案例呼叫 `audit_review_channel()`，前五個依 §3.1.4 應為不可判定。**修復前實測全部回 `recorded`；修復後全部回 `marker_quarantined`，對照組維持 `recorded`。**

```bash
cd cli && uv run python -c "
import sys; sys.path.insert(0,'src')
from wf_cli.doctor import audit_review_channel
C,S='CARD-A','a'*40; A=f'{C}-e0-{S}'
body=f'## Log\n- review by wf-cli；attempt {A}。'
cases={
 'missing-attempt_id': f'<!-- wf-review-event:v1 card_id={C} source_sha={S} -->\n## 查核裁決：APPROVE\n{A}',
 'unknown-version':    f'<!-- wf-review-event:v2 card_id={C} source_sha={S} attempt_id={A} -->\n## 查核裁決：APPROVE',
 'extra-key':          f'<!-- wf-review-event:v1 card_id={C} source_sha={S} attempt_id={A} verdict=APPROVE -->\n## 查核裁決：APPROVE',
 'wrong-order':        f'<!-- wf-review-event:v1 source_sha={S} card_id={C} attempt_id={A} -->\n## 查核裁決：APPROVE',
 'inconsistent':       f'<!-- wf-review-event:v1 card_id={C} source_sha={S} attempt_id=OTHER-e0-{S} -->\n## 查核裁決：APPROVE\n{A}',
 'conformant(control)':f'<!-- wf-review-event:v1 card_id={C} source_sha={S} attempt_id={A} -->\n## 查核裁決：APPROVE',
}
for n,b in cases.items():
    print(f'{n:24}', audit_review_channel([{'body':b,'html_url':'u','user':{'login':'x'}}],C,S,card_body=body).status)"
```

### 1.3 生效結論

**§3.1.4 的 marker 合規判定已生效**（#17）：`wfcli doctor --review-channel` 回傳 `recorded` 現在確實蘊含「該卡 timeline 上沒有受管轄但不合格的 marker」。五種不合格形態與重複事件皆轉 `marker_quarantined`，並在輸出中逐則列出停機原因。

**但仍有兩項未生效，據此結案前必須知道**：

- **停機無法由機器解除**（落差 7）。遇到不合格 marker 的卡會持續停機，`review-marker-clearance` 的留言平面表示法尚未定義，只能人工處理。方向是 fail-closed。
- **§3.1.5 的語意等價放行未生效**（落差 8b）。合法的冪等重送目前會被當成衝突而停機。

**三面一致仍只驗到兩面**（落差 9，追蹤卡 [#20](https://github.com/ruan6047/ai-workflow/issues/20)）：`recorded` 證明「有裁決留言 ＋ 有 Log 索引行」，**不**證明 Project 交付狀態欄與之相符。半寫入（留言成功、狀態欄失敗）目前仍無表達態，且該落差方向是 fail-open。

## 2. 其他消費者

目前無其他解析 §3.1 marker 的工具。新增消費者時在此建列，缺列即視為未實作。

## 3. 維護規則

- 每次改動消費者行為或契約條文，**同一個 commit** 內更新本檔；落差消失才可刪列。
- fail-open 方向的落差**必須**有追蹤卡（§6 硬性要求）；fail-closed 方向可暫無卡但仍須登記。
- 本檔記錄的是**實測結果**，不是意圖。新增或關閉落差列時附可重跑的探針或測試名稱。
