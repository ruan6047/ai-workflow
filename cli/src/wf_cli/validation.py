"""機械檢查：open 的必填欄／鏈深硬上限、handoff 的 source SHA／證據格式、
review 的查核輸出契約。

集中在這裡是因為卡面把「機械檢查」列為紅線相關的驗收條件（open 的必填欄、
鏈深硬上限、handoff 的 SHA／證據），測試要能單獨鎖住這些規則，不want 散在各
command 裡各自判斷、drift 出不一致的檢查標準。查核輸出的**結構**解析在
``review.py``，這裡只做契約層判準（必填、列舉、self_run 非空、第一判準否決權）。
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .card import CHAIN_DEPTH_HARD_CAP, TIERS, chain_depth_violation_message
from .resources import DB_SCOPES, ResourceDeclaration
from .review import (
    ATTRIBUTIONS,
    CORE_PAIN_VALUES,
    FINDING_CLASSES,
    FINDING_KEYS,
    REVIEW_RESULTS,
    SEVERITIES,
    WRITER_ONLY_KEYS,
    Finding,
    ReviewReport,
    SelfRunEntry,
)

SHA_RE = re.compile(r"^[0-9a-f]{40}$")

# 拒收訊息固定引用 canonical §5.2 原文，讓被擋的查核者直接看到規則出處，
# 而不是只看到一句泛用的「驗證失敗」。
SELF_RUN_CITATION = (
    "canonical AI_WORKFLOW.md §5.2：「`self_run` 必填——查核者自己實際跑過的指令與"
    "觀察到的輸出。沒有 `self_run` 的 `APPROVE` 無效」"
    "（記 review-invalid、不計 iteration；templates/review-escalation.md §1）"
)


class ValidationError(ValueError):
    """攜帶多筆錯誤訊息，讓呼叫端一次印出全部而非一個一個修。"""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("；".join(errors))


def validate_source_sha(sha: str) -> None:
    if not SHA_RE.fullmatch(sha or ""):
        message = (
            f"source_sha 必須是完整 40 字元小寫 hex SHA，收到 {sha!r}"
            "（不接受 branch name、短 SHA 或未提交工作區——見 handoff-contract.md §1）"
        )
        raise ValidationError([message])


def validate_evidence(evidence: str) -> None:
    if not evidence or not evidence.strip():
        raise ValidationError(["證據欄必填，不得為空字串"])


def validate_chain_depth(chain_depth: int) -> None:
    """決議 5 鏈式停損協定的硬上限機械檢查：原始目標之下最深 2 層，
    超過（> ``CHAIN_DEPTH_HARD_CAP``）一律硬拒，不得逕行加深。
    """
    if chain_depth > CHAIN_DEPTH_HARD_CAP:
        raise ValidationError([chain_depth_violation_message(chain_depth)])


def validate_open_fields(
    *,
    card_id: str,
    feature: str,
    tier: str,
    core_pain: str,
    service_goal: str,
    db_scope: str,
    resources: ResourceDeclaration | None,
) -> None:
    """open 的機械檢查：核心痛點、服務的原始目標、tier、db_scope、資源宣告。"""
    errors: list[str] = []
    if not card_id or not card_id.strip():
        errors.append("卡ID 必填")
    if not feature or not feature.strip():
        errors.append("功能 必填")
    if tier not in TIERS:
        errors.append(f"tier 必須是 {TIERS} 之一，收到 {tier!r}")
    if not core_pain or not core_pain.strip():
        errors.append("核心痛點 必填")
    if not service_goal or not service_goal.strip():
        errors.append("服務的原始目標 必填")
    if db_scope not in DB_SCOPES:
        errors.append(f"db_scope 必須是 {sorted(DB_SCOPES)} 之一，收到 {db_scope!r}")
    if resources is None:
        errors.append("資源宣告必填（至少 db_scope；resources 可為空陣列）")
    elif resources.db_scope != db_scope:
        errors.append(
            f"資源宣告內 db_scope（{resources.db_scope!r}）與 --db-scope（{db_scope!r}）不一致"
        )
    if errors:
        raise ValidationError(errors)


def _as_text(value: Any) -> str:
    """把解析結果正規化成字串比對用的文字。

    ```yaml 區塊走受限解析器（一律字串），```json 區塊走 ``json.loads``（會有真
    布林／數字）；兩條路徑必須落在同一套判準上，所以在這裡收斂型別差異，
    而不是讓每個檢查各自 ``isinstance``。
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    return str(value)


def _normalize_blocking(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = _as_text(value).strip()
    if text == "true":
        return True
    if text == "false":
        return False
    return None


def _has_self_run_evidence(data: Mapping[str, Any]) -> bool:
    """是否真的附了自跑證據（至少一項有非空 command）。"""
    raw = data.get("self_run")
    if not isinstance(raw, list):
        return False
    return any(
        isinstance(item, Mapping) and _as_text(item.get("command")).strip() for item in raw
    )


def review_invalid_reasons(data: Mapping[str, Any]) -> list[str]:
    """回傳 ``review-invalid`` 的理由（templates/review-escalation.md §1）。

    §1 列的無效查核有六種，其中**只有「`APPROVE` 未附 `self_run`」在寫入通道可以
    機械判定**；其餘（查核順序、環境污染、reviewer 獨立性、審錯 artifact、同一
    reviewer 對同一 SHA 重複回報）需要 CLI 拿不到的事實，由 Coordinator 判定。
    刻意不假裝能判定那些，也刻意不因此就放行——本函式回傳非空即拒收。
    """
    if _as_text(data.get("review_result")).strip() != "APPROVE":
        return []
    if _has_self_run_evidence(data):
        return []
    return [
        (
            "APPROVE 未附 self_run（或所有項目都沒有 command）：沒有自跑證據的通過不是查核。"
            f"依 {SELF_RUN_CITATION}"
        )
    ]


def _validate_finding(item: Any, index: int, seen_ids: set[str], errors: list[str]) -> Finding | None:
    if not isinstance(item, Mapping):
        errors.append(f"findings 第 {index} 項必須是含 {FINDING_KEYS[0]} 等鍵的 mapping，收到 {item!r}")
        return None

    finding_id = _as_text(item.get("finding_id")).strip()
    label = finding_id or f"第 {index} 項"

    missing = [k for k in FINDING_KEYS if not _as_text(item.get(k)).strip()]
    if missing:
        errors.append(
            f"finding {label} 缺必填欄：{'、'.join(missing)}"
            "（templates/review-prompt.md §5 的 finding schema，八欄全必填）"
        )

    if finding_id:
        if finding_id in seen_ids:
            errors.append(
                f"finding_id {finding_id!r} 重複；finding_id 必須跨 attempt 穩定且唯一"
                "（review-escalation.md §2 以它追蹤 open set 與根因）"
            )
        seen_ids.add(finding_id)

    severity = _as_text(item.get("severity")).strip()
    if severity and severity not in SEVERITIES:
        errors.append(f"finding {label} 的 severity 必須是 {list(SEVERITIES)} 之一，收到 {severity!r}")

    finding_class = _as_text(item.get("finding_class")).strip()
    if finding_class and finding_class not in FINDING_CLASSES:
        errors.append(
            f"finding {label} 的 finding_class 必須是 {list(FINDING_CLASSES)} 之一，收到 {finding_class!r}"
        )

    attribution = _as_text(item.get("attribution")).strip()
    if attribution and attribution not in ATTRIBUTIONS:
        errors.append(
            f"finding {label} 的 attribution 必須是 {list(ATTRIBUTIONS)} 之一，收到 {attribution!r}"
        )

    blocking = _normalize_blocking(item.get("blocking"))
    if _as_text(item.get("blocking")).strip() and blocking is None:
        errors.append(
            f"finding {label} 的 blocking 必須是 true 或 false，收到 {item.get('blocking')!r}"
        )

    if missing or blocking is None or severity not in SEVERITIES:
        return None
    if finding_class not in FINDING_CLASSES or attribution not in ATTRIBUTIONS:
        return None
    return Finding(
        finding_id=finding_id,
        severity=severity,
        blocking=blocking,
        finding_class=finding_class,
        attribution=attribution,
        root_cause_id=_as_text(item.get("root_cause_id")).strip(),
        evidence=_as_text(item.get("evidence")).strip(),
        disposition=_as_text(item.get("disposition")).strip(),
    )


def validate_review_report(data: Mapping[str, Any]) -> ReviewReport:
    """查核輸出契約的機械檢查；全部錯誤一次列出，通過才回傳 ``ReviewReport``。

    判準來源：canonical §5.1（核心痛點第一判準具否決權）、§5.2（結構化輸出四件、
    ``self_run`` 必填）、templates/review-prompt.md §5（欄位與列舉）、
    templates/review-escalation.md §2／§5（finding schema、writer-only 欄位）。
    """
    errors: list[str] = []

    review_result = _as_text(data.get("review_result")).strip()
    if not review_result:
        errors.append("review_result 必填（APPROVE 或 REQUEST_CHANGES；canonical §5.2 結構化輸出）")
    elif review_result not in REVIEW_RESULTS:
        errors.append(
            f"review_result 必須是 {list(REVIEW_RESULTS)} 之一，收到 {review_result!r}"
            "（大小寫需完全相符；自由文字結論不受理）"
        )

    core_pain_resolved = _as_text(data.get("core_pain_resolved")).strip()
    if not core_pain_resolved:
        errors.append(
            "core_pain_resolved 必填：查核第一判準——核心痛點是否已消失"
            "（canonical §5.1，具否決權；驗收清單全過但痛點未消一律 REQUEST_CHANGES）"
        )
    elif core_pain_resolved not in CORE_PAIN_VALUES:
        errors.append(
            f"core_pain_resolved 必須是 {list(CORE_PAIN_VALUES)} 之一，收到 {core_pain_resolved!r}"
        )
    elif core_pain_resolved == "no" and review_result == "APPROVE":
        errors.append(
            "core_pain_resolved=no 時 review_result 只能是 REQUEST_CHANGES"
            "（第一判準具否決權；canonical §5.1、review-escalation.md §5）"
        )

    self_run: list[SelfRunEntry] = []
    raw_self_run = data.get("self_run")
    if raw_self_run is None:
        errors.append(f"self_run 必填——{SELF_RUN_CITATION}")
    elif not isinstance(raw_self_run, list):
        errors.append("self_run 必須是 `- command:` ／ `observed:` 的清單，不接受單一字串或 mapping")
    elif not raw_self_run:
        errors.append(f"self_run 不得為空——{SELF_RUN_CITATION}")
    else:
        for index, item in enumerate(raw_self_run, start=1):
            if not isinstance(item, Mapping):
                errors.append(f"self_run 第 {index} 項必須是含 command／observed 的 mapping，收到 {item!r}")
                continue
            command = _as_text(item.get("command")).strip()
            observed = _as_text(item.get("observed")).strip()
            if not command:
                errors.append(f"self_run 第 {index} 項缺 command（或為空）")
            if not observed:
                errors.append(
                    f"self_run 第 {index} 項缺 observed（或為空）：只列指令不算自跑證據，"
                    "必須附觀察到的輸出／數字"
                )
            if command and observed:
                self_run.append(SelfRunEntry(command=command, observed=observed))

    findings: list[Finding] = []
    if "findings" not in data or data.get("findings") is None:
        errors.append(
            "findings 必填；沒有 finding 請顯式寫 `findings: []`"
            "——省略與漏填無法區分，不得由 CLI 代為推定"
        )
    elif not isinstance(data["findings"], list):
        errors.append("findings 必須是清單（每項為 review-prompt.md §5 的 finding mapping）")
    else:
        seen_ids: set[str] = set()
        for index, item in enumerate(data["findings"], start=1):
            finding = _validate_finding(item, index, seen_ids, errors)
            if finding is not None:
                findings.append(finding)

    if errors:
        raise ValidationError(errors)

    writer_only = {k for k in data if k in WRITER_ONLY_KEYS}
    for item in data["findings"]:
        writer_only.update(k for k in item if k in WRITER_ONLY_KEYS)

    return ReviewReport(
        review_result=review_result,
        core_pain_resolved=core_pain_resolved,
        self_run=tuple(self_run),
        findings=tuple(findings),
        writer_only_keys=tuple(sorted(writer_only)),
    )


__all__ = [
    "SELF_RUN_CITATION",
    "SHA_RE",
    "ValidationError",
    "review_invalid_reasons",
    "validate_chain_depth",
    "validate_evidence",
    "validate_open_fields",
    "validate_review_report",
    "validate_source_sha",
]
