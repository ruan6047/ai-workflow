"""機械檢查：open 的必填欄／鏈深硬上限、handoff 的 source SHA／證據格式、
review 的查核輸出契約。

集中在這裡是因為卡面把「機械檢查」列為紅線相關的驗收條件（open 的必填欄、
鏈深硬上限、handoff 的 SHA／證據），測試要能單獨鎖住這些規則，不want 散在各
command 裡各自判斷、drift 出不一致的檢查標準。查核輸出的**結構**解析在
``review.py``，這裡只做契約層判準（必填、列舉、self_run 非空、第一判準否決權）。
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .card import CHAIN_DEPTH_HARD_CAP, TIERS, chain_depth_violation_message
from .doctor import inspect_event_marker
from .resources import DB_SCOPES, ResourceDeclaration
from .review import (
    ATTRIBUTIONS,
    BLOCK_VERSION,
    CHECKPOINT_DECISIONS,
    CHECKPOINT_LOG_TAG,
    CORE_PAIN_VALUES,
    FINDING_CLASSES,
    FINDING_KEYS,
    PREFLIGHT_BLOCK_KEY,
    REVIEW_RESULTS,
    SEVERITIES,
    WRITER_ONLY_KEYS,
    AcceptedMark,
    CheckpointFacts,
    EscalationFacts,
    Finding,
    PreflightBasis,
    ReviewParseError,
    ReviewReport,
    SelfRunEntry,
    body_has_contract_baseline,
    checkpoint_facts_from_body,
    escalation_facts_from_body,
    log_line_indexes,
    parse_attempt_id,
    preflight_basis_from_body,
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

    # 結論與 findings 的語意一致性。需求方 2026-08-06 裁決（ruan6047/ai-workflow#8）：
    # 這兩種矛盾由「警示照寫」升為硬拒。只在 findings 本身解析乾淨時才判——否則作者
    # 會同時看到「finding 缺欄」與由缺欄衍生的矛盾訊息，被導去修錯的地方。
    findings_clean = isinstance(data.get("findings"), list) and len(findings) == len(
        data["findings"]
    )
    if findings_clean and review_result == "APPROVE":
        blocking_ids = [f.finding_id for f in findings if f.blocking]
        if blocking_ids:
            errors.append(
                f"review_result=APPROVE 但含 blocking=true 的 finding（{'、'.join(blocking_ids)}）："
                "語意矛盾——有阻斷缺陷不得核可，二擇一：改 REQUEST_CHANGES，"
                "或把該 finding 改為 blocking: false"
                "（需求方 2026-08-06 裁決，ruan6047/ai-workflow#8）"
            )
    if findings_clean and review_result == "REQUEST_CHANGES" and not findings:
        errors.append(
            "review_result=REQUEST_CHANGES 但 findings 為空：退回必須附至少一項可執行 finding，"
            "否則執行者無從修起（需求方 2026-08-06 裁決，ruan6047/ai-workflow#8）"
        )

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


# --------------------------------------------------------------------------
# escalation 帳的機械檢查（WF-22-CLI4 切片 A）
# --------------------------------------------------------------------------


def validate_accepted_overrides(
    raw_values: Sequence[str], findings: Iterable[Finding]
) -> dict[str, str]:
    """解析並檢查 ``--mark-not-accepted FINDING_ID=理由``；回傳 ``{finding_id: 理由}``。

    ``accepted`` 的預設是 true 且免旗標（見 ``review.default_accepted_marks``）；
    **標成 false 是把 finding 移出 open set 的那一側**，所以三件事缺一不可：顯式旗標、
    非空理由、以及呼叫端另行取得的 ``marked_by``（見 ``validate_marked_by``）。
    """
    known = {f.finding_id for f in findings}
    errors: list[str] = []
    overrides: dict[str, str] = {}
    for raw in raw_values:
        if "=" not in raw:
            errors.append(
                f"--mark-not-accepted 需寫成 `FINDING_ID=非空理由`，收到 {raw!r}"
                "（review-escalation.md §2：撤銷採認必須留下可稽核的理由）"
            )
            continue
        finding_id, _, reason = raw.partition("=")
        finding_id = finding_id.strip()
        reason = reason.strip()
        if not finding_id:
            errors.append(f"--mark-not-accepted 的 finding_id 為空：{raw!r}")
            continue
        if finding_id not in known:
            errors.append(
                f"--mark-not-accepted 指名的 finding_id {finding_id!r} 不在本次查核輸出內"
                f"（本次 findings：{sorted(known) or '（無）'}）；"
                "跨 attempt 的事後降級屬 review-correction，不是本指令的射程"
            )
            continue
        if not reason:
            errors.append(f"finding {finding_id!r} 標 accepted=false 但理由為空；理由必填")
            continue
        if finding_id in overrides:
            errors.append(f"--mark-not-accepted 對同一 finding {finding_id!r} 給了多次，無法判定採用哪一個")
            continue
        overrides[finding_id] = reason
    if errors:
        raise ValidationError(errors)
    return overrides


def validate_marked_by(marked_by: str, owner_field: str | None) -> None:
    """``accepted=false`` 的標記者身分檢查。

    ``marked_by`` 由呼叫端以 ``gh api user --jq .login`` 取得——**平台身分，不是自陳
    字串**。機械檢查只有一條：不得逐字等於卡面 owner 欄（標記者不得是被該標記嘉惠
    的執行者本人）。

    ⚠️ **這條檢查今天恆真，是已知的 fail-closed 落差**：本 repo 只有 ``ruan6047``
    一個人類 GitHub 帳號，而 owner 欄裝的是「Claude Opus 5@Claude Code（子 agent）」
    這類自由文字，兩者不在同一個命名空間，永遠不可能逐字相等。此落差應登記於
    ``docs/CONSUMER_CONFORMANCE.md``（該檔不在本卡寫入集，故此處只指名，不代改）。
    在 owner 欄承載平台帳號之前，本檢查提供的是**形狀**保證而非身分保證。
    """
    if not (marked_by or "").strip():
        raise ValidationError(
            [
                (
                    "accepted=false 需要 marked_by（平台身分），但取不到 `gh api user` 的 login；"
                    "無法機械核對的授權不得以自述成立（review-escalation.md §4 第 2 款同向）"
                )
            ]
        )
    if owner_field and marked_by.strip() == owner_field.strip():
        raise ValidationError(
            [
                (
                    f"marked_by（{marked_by}）逐字等於卡面 owner；"
                    "撤銷採認的裁定者不得是被該標記嘉惠的執行者本人"
                )
            ]
        )


def derive_accepted_marking_binding(
    marked_by: str,
    owner_field: str | None,
    *,
    authorized_writers: Sequence[str] | None = None,
) -> str:
    """導出 ``accepted=false`` 標記的授權綁定值；**呼叫端不得手填**。

    與 review-escalation.md §4／§5 的 ``authorization_binding``（ai-workflow#39）同一個
    述詞，套在另一組角色上：``validate_marked_by`` 要求標記者不得逐字等於卡面 owner，
    而**該比對是否可能失敗**，取決於兩個值是否落在同一個命名空間。

    - ``substantive``：``handoff-contract.md`` §5 已宣告被授權的 review event writer
      帳號集合，且 ``marked_by`` 與 owner 欄兩者都落在該集合內——此時「不得等於 owner」
      是一條真的會擋下東西的檢查。
    - ``structurally-vacuous``：以上任一不成立。**本 repo 今天恆為此值**：
      ``handoff-contract.md`` §5 的 writer 集合仍是未填的樣板佔位，且 owner 欄裝的是
      「Claude Opus 5@Claude Code（子 agent）」這類自由文字、與 GitHub login 不同型別，
      兩者永遠不可能相等。

    ``structurally-vacuous`` **不使標記無效**（否則本 repo 無法運作），但消費者**不得**
    據以宣稱該次撤銷採認經第二方獨立核可。何時開始有鑑別力也一併指名：§5 宣告 writer
    集合，**且** owner 欄承載可與帳號逐字比對的平台身分。在那之前這是**約定**，
    其執行者是人——該落差應登記於 ``docs/CONSUMER_CONFORMANCE.md``（不在本卡寫入集）。
    """
    if not authorized_writers:
        return "structurally-vacuous"
    writers = {w.strip() for w in authorized_writers if w and w.strip()}
    if not marked_by.strip() or not (owner_field or "").strip():
        return "structurally-vacuous"
    if marked_by.strip() in writers and owner_field.strip() in writers:
        return "substantive"
    return "structurally-vacuous"


def build_accepted_marks(
    findings: Iterable[Finding],
    overrides: Mapping[str, str],
    marked_by: str,
    *,
    owner_field: str | None = None,
    authorized_writers: Sequence[str] | None = None,
) -> dict[str, AcceptedMark]:
    """把預設 true 與顯式 false 疊成最終的 ``accepted`` 標記表。

    ``binding`` 一律由 ``derive_accepted_marking_binding`` 導出；``accepted=true`` 沒有
    行使任何授權，取 ``not-applicable``（顯式寫出，不省略）。
    """
    binding = derive_accepted_marking_binding(
        marked_by, owner_field, authorized_writers=authorized_writers
    )
    marks: dict[str, AcceptedMark] = {}
    for finding in findings:
        reason = overrides.get(finding.finding_id)
        if reason is None:
            marks[finding.finding_id] = AcceptedMark(finding_id=finding.finding_id, accepted=True)
        else:
            marks[finding.finding_id] = AcceptedMark(
                finding_id=finding.finding_id,
                accepted=False,
                reason=reason,
                marked_by=marked_by,
                binding=binding,
            )
    return marks


@dataclass(frozen=True)
class IssueEventHistory:
    """自 Issue timeline 掃出的 escalation 帳歷史（唯讀投影）。

    ``all_attempt_ids`` 涵蓋**整條 timeline**（去重用）；其餘欄位只涵蓋
    ``contract-baseline`` 事件**之後**的留言——review-escalation.md:276 的 cutover
    語意：baseline 之前的歷史事件「維持原貌」，不追溯要求補欄。沒有 baseline 時
    scope 即全部留言，於是任何一則讀不出帳的舊事件都會讓閘門 fail-closed。
    """

    all_attempt_ids: tuple[str, ...] = ()
    scoped_facts: tuple[EscalationFacts, ...] = ()
    unknown_reasons: tuple[str, ...] = ()
    checkpoints: tuple[CheckpointFacts, ...] = ()
    baseline_count: int = 0


def build_issue_event_history(comments: Sequence[Mapping[str, Any]]) -> IssueEventHistory:
    """掃 Issue 留言，重建 escalation 帳可用的事實。

    ``comments`` 依建立順序（``gh issue view --json comments`` 的回傳順序）；
    cutover 位置以「第一則 contract-baseline 事件」的索引界定。
    """
    baseline_indexes = [
        i for i, c in enumerate(comments) if body_has_contract_baseline(str(c.get("body") or ""))
    ]
    scope_start = baseline_indexes[0] if baseline_indexes else 0

    all_attempts: list[str] = []
    facts: list[EscalationFacts] = []
    unknown: list[str] = []
    checkpoints: list[CheckpointFacts] = []

    for index, comment in enumerate(comments):
        body = str(comment.get("body") or "")
        url = str(comment.get("url") or comment.get("html_url") or "（URL 未提供）")
        attempt, reason = inspect_event_marker(body)
        if attempt is not None:
            all_attempts.append(attempt)
        if index < scope_start:
            continue
        if reason is not None:
            unknown.append(f"{reason}（{url}）")
            continue
        try:
            if attempt is not None:
                found = escalation_facts_from_body(body)
                if found is None or found.attempt_id != attempt:
                    unknown.append(
                        f"attempt {attempt} 的 review event 沒有可讀的 escalation 帳事實"
                        f"（{url}）；依 review-escalation.md:276 這是**未知**而非「不計數」"
                    )
                else:
                    facts.append(found)
            checkpoint = checkpoint_facts_from_body(body)
            if checkpoint is not None:
                checkpoints.append(checkpoint)
        except ReviewParseError as exc:
            unknown.append(f"{exc}（{url}）")

    return IssueEventHistory(
        all_attempt_ids=tuple(all_attempts),
        scoped_facts=tuple(facts),
        unknown_reasons=tuple(unknown),
        checkpoints=tuple(checkpoints),
        baseline_count=len(baseline_indexes),
    )


def counted_attempts(history: IssueEventHistory, escalation_epoch: int) -> list[EscalationFacts]:
    """本 epoch 依 §3 計數的 attempt，依留言順序去重（§3：同一 attempt 最多計一次）。"""
    seen: set[str] = set()
    out: list[EscalationFacts] = []
    for fact in history.scoped_facts:
        if fact.escalation_epoch != escalation_epoch or not fact.counts:
            continue
        if fact.attempt_id in seen:
            continue
        seen.add(fact.attempt_id)
        out.append(fact)
    return out


def find_preflight_basis(
    comments: Sequence[Mapping[str, Any]], *, card_id: str, source_sha: str
) -> PreflightBasis:
    """掃 Issue 留言找受管轄的 preflight pass event；找不到回 ``not-established``。"""
    for comment in comments:
        try:
            basis = preflight_basis_from_body(
                str(comment.get("body") or ""), card_id=card_id, source_sha=source_sha
            )
        except ReviewParseError:
            continue
        if basis is not None:
            url = str(comment.get("url") or comment.get("html_url") or "").strip()
            return basis if not url else PreflightBasis(
                basis=basis.basis, source_event=url, summary=basis.summary
            )
    return PreflightBasis()


def check_preflight_event_present(basis: PreflightBasis, *, source_sha: str) -> None:
    """**所有遠端寫入之前**的閘門：沒有受管轄的 preflight event 就不建立 review event。

    這是 WF-22-CLI4-R3-01 的處置，也是本卡族第一次動「要不要寫」而不是「寫什麼值」。
    前三輪分別把 ``preflight_passed`` 寫成無來源的 ``true``、任意字串具結的 ``true``、
    以及擴充 schema 的 ``unknown``／``unavailable``——三次都在找一個誠實的值，卻沒問
    「這一則到底該不該存在」。

    契約的答案是不該：§1 明定 preflight 缺口「不得建立 review event 或派 reviewer」；
    §5:168 的 review event schema 把 ``preflight_passed`` 釘為**字面 ``true``**（對照
    同區塊的 ``escalation_epoch: <integer>``、``counts_toward_escalation: <boolean
    derived from §3>`` 即知那不是型別佔位）。斷不出 ``true`` 的事件不是合格的 review
    event，寫下去只是製造一則不合 schema 的留痕。

    我先前反對這條的理由是「拒絕等於把真實發生的查核從狀態面抹掉」。**該理由不成立**：
    查核仍可留在 Issue 的收據（``handoff-contract.md`` §3.1.2 的 ``wf-review-receipt``）
    與報告全文裡，那正是為「查核者無法執行 wfcli」設計的證據面；被拒絕的只有**狀態面
    的裁決事件**，而狀態面本來就要求 preflight 已通過。用 ``--validate-only`` 仍可完整
    驗證查核輸出格式，不受本閘門影響。
    """
    if basis.established:
        return
    raise ValidationError(
        [
            (
                "找不到本卡、本 source_sha 的受管轄 preflight pass event，"
                "依 review-escalation.md §1 不建立 review event（未寫入任何遠端狀態）。"
                f"需要 timeline 上有一則 `{PREFLIGHT_BLOCK_KEY}: {BLOCK_VERSION}` 區塊，"
                f"逐字帶 preflight_passed: true、card_id、source_sha: {source_sha}。"
                "§5:168 把 review event 的 preflight_passed 釘為字面 true，"
                "斷不出 true 的事件不是合格的 review event；"
                "**不得以 unknown／unavailable 之類的新值擴充該布林欄位**。"
                "產出該事件的 writer 需要 handoff 的寫入集，不在本卡射程內，已交由承接卡；"
                "在它落地前，查核證據請走 handoff-contract.md §3.1.2 的收據，"
                "格式自檢請用 `wfcli review --validate-only`（不寫任何狀態，不受本閘門影響）。"
            )
        ]
    )


def check_attempt_not_duplicated(history: IssueEventHistory, target_attempt_id: str) -> None:
    """寫入前的 ``attempt_id`` 去重（review-escalation.md §3：一個 attempt 一個識別符）。

    必須擋在**寫入前**：``doctor.py:409-415`` 對重複 ``attempt_id`` 判
    ``marker_quarantined``，而該隔離**沒有解除表示法**（歸 #30），寫下去就是製造一個
    今天解不開的狀態。

    邊界（無機械執行者的部分，誠實寫明）：去重只涵蓋**讀得出 marker** 的既有事件。
    一則受管轄但不合格的 marker 背後若藏著同一個 attempt，本檢查看不見它——那正是
    切片 B 被 #30 擋住的同一個解析層缺口。呼叫端另以 ``unknown_reasons`` fail-closed
    間接覆蓋這條路徑（讀不懂就不准寫），但那是閘門 4 的副作用，不是本函式的保證。
    """
    if target_attempt_id in history.all_attempt_ids:
        raise ValidationError(
            [
                (
                    f"attempt_id {target_attempt_id} 已存在於本 Issue timeline，拒絕重複寫入。"
                    "同一 attempt 多則事件會讓 `doctor --review-channel` 永久判 marker_quarantined"
                    "（handoff-contract.md §3.1.5 的保守停機），而解除表示法尚未定義。"
                    "要重新裁決同一 SHA 須先經 escalation-epoch-change 遞增 epoch"
                    "（review-escalation.md §4 末段）。"
                )
            ]
        )


def check_checkpoint_gate(
    history: IssueEventHistory,
    *,
    escalation_epoch: int,
    card_body: str,
) -> None:
    """checkpoint 漏建的閘門：寫第 N 輪裁決前，第 N-1 輪的 checkpoint 必須已存在。

    §4：「第三個及其後每個可計數 attempt 出現時先建立 ``escalation-checkpoint``」，
    且 §4「checkpoint 的評估時點」要求 trigger attempt 的裁決**已落地**。兩者合起來
    唯一可機械檢查的時點就是**下一輪裁決寫入前**：此時第 N-1 輪的裁決已在事件流上，
    它的 checkpoint 若還沒建，就是真的漏了。

    未知一律拒絕（不得推定為不計數）：``unknown_reasons`` 非空即 fail-closed。

    已知較早的位置是 ``handoff --next-stage review`` 派審前（更貼近 §4「例行建立」的
    語意），但 ``handoff_cmd.py`` 不在本卡宣告的寫入集內，故列為後續卡的建議，不為它
    擴張宣告。代價是**晚一輪**：PM 實際漏建的兩次（#22 第四個 attempt 前、#24 第三個
    attempt 前）都會被這道抓到，只是在下一次裁決寫入時才擋。
    """
    if history.baseline_count > 1:
        raise ValidationError(
            [
                (
                    f"本 Issue timeline 有 {history.baseline_count} 則 contract-baseline 事件；"
                    "該 marker 是 one-shot cutover，啟用後再次出現必須 fail loud"
                    "（review-escalation.md:276）"
                )
            ]
        )
    if history.unknown_reasons:
        raise ValidationError(
            [
                "escalation 帳無法自事件流重建，拒絕寫入（不得推定為不計數）："
                + "；".join(history.unknown_reasons)
                + "。處置：修好該留痕，或由需求方以 `wfcli contract-baseline` 明示 cutover "
                "後重試——baseline 之前的事件依 review-escalation.md:276 維持原貌。"
            ]
        )

    counted = counted_attempts(history, escalation_epoch)
    if len(counted) < 3:
        return
    previous = counted[-1]
    for checkpoint in history.checkpoints:
        if (
            checkpoint.trigger_attempt_id == previous.attempt_id
            and checkpoint.escalation_epoch == escalation_epoch
            and log_line_indexes(card_body, CHECKPOINT_LOG_TAG, previous.attempt_id)
        ):
            return
    raise ValidationError(
        [
            (
                f"第 {len(counted)} 個可計數 attempt（{previous.attempt_id}）尚未建立 "
                "escalation-checkpoint，拒絕寫入下一輪裁決。"
                "review-escalation.md §4：第三個及其後每個可計數 attempt 出現時先建立 checkpoint，"
                "不得只按整數直接寫 🚨已升級。請先跑 `wfcli checkpoint`"
                f" --trigger-attempt-id {previous.attempt_id}。"
                "（判準是**兩面一致**：留言的結構化區塊 ＋ Issue body ## Log 的同行索引；"
                "只有其一視為未建立。）"
            )
        ]
    )


def validate_checkpoint_input(
    *,
    card_id: str,
    escalation_epoch: int,
    trigger_attempt_id: str,
    unique_attempt_count: int,
    checkpoint_decision: str,
    checkpoint_rationale: str,
    escalation_resolution: str | None = None,
    deferred_findings: Sequence[str] = (),
) -> None:
    """``escalation-checkpoint`` 事件的欄位檢查（review-escalation.md §5）。

    刻意**不**接受 PM 手寫七則裡多出的四個未定義鍵：``escalation_resolution``、
    ``decided_by``、``counts_toward_escalation``、``attempts_so_far``。其中：

    - ``counts_toward_escalation`` 放在 checkpoint 上是分類錯誤——§5 把它定為 review
      event 的欄位，§1 表列 checkpoint 本身不計 escalation 額度；而它又剛好是
      ``review.WRITER_ONLY_KEYS`` 裡的名字，同名不同義。
    - ``attempts_so_far`` 不等於 ``unique_attempt_count``（差一）：PM 的建立時點慣例是
      「派下一輪審之前」，而 §4 要求 trigger attempt 的裁決已落地。本指令以
      ``trigger_attempt_id`` 正名該語意。
    - ``escalation_resolution`` 曾是真實的契約缺口，但該缺口已由
      ``WF-ESCALATION-RESOLUTION-GAP1``（ai-workflow#39，``058100ad``）補上，而補法
      **否決了 checkpoint 欄位這條路**：它是獨立的事件型別 ``escalation-resolution``，
      **永遠不會**成為 checkpoint 的欄位。詳見下方拒收訊息。
    """
    errors: list[str] = []

    decomposed = parse_attempt_id(trigger_attempt_id)
    if decomposed is None:
        errors.append(
            f"--trigger-attempt-id 不符 `<card>-e<epoch>-<40 hex sha>` 形式：{trigger_attempt_id!r}"
            "（review-escalation.md §5）"
        )
    else:
        trigger_card, trigger_epoch, _ = decomposed
        if trigger_card != card_id:
            errors.append(
                f"--trigger-attempt-id 反解出的卡（{trigger_card}）與本次 card_id（{card_id}）不符"
            )
        if trigger_epoch != escalation_epoch:
            errors.append(
                f"--trigger-attempt-id 的 epoch（e{trigger_epoch}）與 --escalation-epoch"
                f"（{escalation_epoch}）不符；checkpoint 只結本 epoch 的帳（§4 末段：新 epoch 從零計數）"
            )

    if unique_attempt_count < 3:
        errors.append(
            f"unique_attempt_count 必須 >= 3，收到 {unique_attempt_count}"
            "（review-escalation.md §5；checkpoint 只在第三個及其後的可計數 attempt 建立）"
        )

    if checkpoint_decision not in CHECKPOINT_DECISIONS:
        errors.append(
            f"checkpoint_decision 必須是 {list(CHECKPOINT_DECISIONS)} 之一，收到 {checkpoint_decision!r}"
        )

    if not (checkpoint_rationale or "").strip():
        errors.append("checkpoint_rationale 必填且不得為空（review-escalation.md §5）")
    elif "```" in checkpoint_rationale:
        errors.append(
            "checkpoint_rationale 含 ``` 圍籬字元，會破壞結構化區塊；請改寫（本欄是區塊純量）"
        )

    if escalation_resolution is not None:
        errors.append(
            "`escalation_resolution` 不是 checkpoint 的欄位，而且**永遠不會是**。"
            "review-escalation.md §4「escalate 之後的第三種結果」已裁定"
            "（WF-ESCALATION-RESOLUTION-GAP1，ai-workflow#39，058100ad）："
            "把它做成 checkpoint 上的獨立欄位是候選（乙），已被否決——那會把**告警與解除"
            "綁進同一則事件**，使機械判定成為人類裁定的人質（需求方一天不表態，escalate "
            "一天不進事件流），且「條件已成立但尚無人裁定」變成無表示法，漏建誘因被制度化；"
            "先寫再編輯則湮滅原文，§5 已否決編輯路徑。採用的是候選（丙）：獨立事件型別 "
            "`escalation-resolution`——checkpoint 照常記 escalate、卡片轉 🚨已升級，"
            "裁定到達時**另發一則**解除事件，兩則之間的區間就是升級狀態本身。"
            "本 CLI 尚未實作該 writer（在 WF-22-CLI4 切片 A 之外），故此處 fail-closed。"
            "checkpoint_rationale 可記人讀脈絡，但它**不構成裁定**——升級狀態的解除須待 "
            "escalation-resolution writer，不得以自創鍵或散文代替。"
        )

    if deferred_findings:
        errors.append(
            "`deferred_findings` 在本 repo 尚不可用，一律拒收（review-escalation.md §4 專節 "
            "(c)／(c′)）：`instruction-omitted` 依賴 handoff payload 的 review_prompt_url 與 "
            "closure_reporting_requested 兩欄（尚未存在）；`spec-narrowed` 依賴讀取留言 author "
            "與 body 並逐字綁定本輪 attempt_id 與 finding_id（本 writer 未實作）。契約明文："
            "證據不可得時本 cause 不可用，對應 finding 落「未提及」格並強制 escalate；"
            "adapter 不得以「讀不到證據」為由改判成立。"
        )

    if errors:
        raise ValidationError(errors)


__all__ = [
    "SELF_RUN_CITATION",
    "SHA_RE",
    "IssueEventHistory",
    "ValidationError",
    "build_accepted_marks",
    "build_issue_event_history",
    "check_attempt_not_duplicated",
    "check_checkpoint_gate",
    "check_preflight_event_present",
    "counted_attempts",
    "derive_accepted_marking_binding",
    "find_preflight_basis",
    "review_invalid_reasons",
    "validate_accepted_overrides",
    "validate_chain_depth",
    "validate_checkpoint_input",
    "validate_evidence",
    "validate_marked_by",
    "validate_open_fields",
    "validate_review_report",
    "validate_source_sha",
]
