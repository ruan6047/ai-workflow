# 消費者符合度登記 — ai-workflow

本檔是 [`templates/handoff-contract.md`](../templates/handoff-contract.md) §6 所要求的登記，登記對象是 **ai-workflow repo 自身的消費者**。

本 repo 是該契約的 canonical 來源，同時也受自己定義的機制管理（dogfooding）。它沒有 `docs/HANDOFF_CONTRACT.md` 這種採用者副本，因此 §6 的登記無處可填——這份獨立檔案就是它的落點。反過來說，各採用專案應在**自己的**副本 §6 就地登記，或另立同名檔案，**不要**引用本檔：本檔記錄的是 ai-workflow 的實作狀態，不是任何其他專案的。

> **未登記等同未生效。** 本檔存在的唯一理由，是讓「契約寫著 fail-closed、消費者實際 fail-open」這種狀態可被查出來。若某項要求在下表沒有對應列，一律視為未實作。

## 1. 消費者：`audit_review_channel()`

- 位置：[`cli/src/wf_cli/doctor.py`](../cli/src/wf_cli/doctor.py)（`wfcli doctor --review-channel`）
- 讀取的 marker：`wf-review-event:v1`、`wf-review-receipt:v1`
- 對照的契約版本：`templates/handoff-contract.md` §3.1（`WF-REVIEW-EVENT-MARKER-CONTRACT1`）

### 1.1 已實作

- §3.1.3 三面一致中的兩面：要求 Issue body 的 `review by wf-cli` 索引行與同 `attempt_id` 同時命中，才回 `recorded`。
- §3.1.6 的 `receipt_untranscribed` 與 `unobservable` 兩態，且 `unobservable` 的輸出文字明確禁止「沒有紀錄 → 沒有查核」的推論。
- receipt 的同卡、同 `source_sha` 比對，並輸出收據 URL 與 GitHub author。

### 1.2 落差

| # | 契約要求 | 現況 | 失效方向 | 追蹤 |
|---|---|---|---|---|
| 1 | §3.1.4 未知版本不得回退 legacy | `v2` marker ＋ 舊式標題 → `recorded` | **fail-open** | [#17](https://github.com/ruan6047/ai-workflow/issues/17) |
| 2 | §3.1.3 必填三欄 | 缺 `attempt_id` → `recorded` | **fail-open** | [#17](https://github.com/ruan6047/ai-workflow/issues/17) |
| 3 | §3.1.3 鍵集合封閉 | 多出未定義鍵 → `recorded` | **fail-open** | [#17](https://github.com/ruan6047/ai-workflow/issues/17) |
| 4 | §3.1.3 順序與單一空白鎖定 | 欄位錯序 → `recorded` | **fail-open** | [#17](https://github.com/ruan6047/ai-workflow/issues/17) |
| 5 | §3.1.3 三欄自洽 | `attempt_id` 屬別卡 → `recorded` | **fail-open** | [#17](https://github.com/ruan6047/ai-workflow/issues/17) |
| 6 | §3.1.4 per-card halt 結果態 | 無；三態裝不下「找到訊號但讀不懂」 | fail-open（併入 `recorded`） | [#17](https://github.com/ruan6047/ai-workflow/issues/17) |
| 7 | §3.1.4 halt 解除路徑 | **契約已定義**（`review-escalation.md` §5 `review-marker-clearance`）；consumer 未實作 | fail-open（停機根本未發生，故無從解除） | [#17](https://github.com/ruan6047/ai-workflow/issues/17) |
| 8a | §3.1.5 重複 event 的保守停機 | 無；同 `attempt_id` 多則事件不被偵測 | **fail-open** | [#17](https://github.com/ruan6047/ai-workflow/issues/17) |
| 8b | §3.1.5 語意比對（放行合法重送） | 無；裁決語意只在散文，無結構化承載 | fail-closed（合法重送會被停機卡住） | 設計歸 [#16](https://github.com/ruan6047/ai-workflow/issues/16)；實作卡未開 |
| 9 | §3.1.3 三面一致的第三面（Project 交付狀態欄） | 未讀取；半寫入無表達態 | fail-open | [#17](https://github.com/ruan6047/ai-workflow/issues/17) |

落差 8a／8b 的拆分理由：§3.1.5 延遲生效期間的保守行為（多則同 `attempt_id` 事件一律停止判定）**只需要消費者變更**，不依賴結構化承載，故可在 #17 內完成；只有「分辨語意一致以放行合法重送」才需要寫入端提供結構化裁決承載。兩者失效方向相反，混為一項會掩蓋 8a 的 fail-open 性質。

落差 1–5 的證據可重跑：以下探針對六個案例呼叫 `audit_review_channel()`，前五個依 §3.1.4 應為不可判定，實測全部回 `recorded`。

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

**§3.1.4 與 §3.1.5 在本 repo 目前皆未生效。** 在 [#17](https://github.com/ruan6047/ai-workflow/issues/17) 完成前，`wfcli doctor --review-channel` 回傳 `recorded` **不足以證明**該 attempt 的 marker 合格；它只證明有一則帶 `attempt_id` 的裁決文字與一行 Log 索引。任何據此結案的流程都必須另行人工核對 marker。

## 2. 其他消費者

目前無其他解析 §3.1 marker 的工具。新增消費者時在此建列，缺列即視為未實作。

## 3. 維護規則

- 每次改動消費者行為或契約條文，**同一個 commit** 內更新本檔；落差消失才可刪列。
- fail-open 方向的落差**必須**有追蹤卡（§6 硬性要求）；fail-closed 方向可暫無卡但仍須登記。
- 本檔記錄的是**實測結果**，不是意圖。新增或關閉落差列時附可重跑的探針或測試名稱。
