from __future__ import annotations

import ast
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

import pytest

from wf_cli.resources import ResourceDeclaration
from wf_cli.validation import (
    ValidationError,
    validate_chain_depth,
    validate_evidence,
    validate_open_fields,
    validate_source_sha,
)


def test_valid_full_sha_passes():
    validate_source_sha("a" * 40)  # 不拋例外即算通過


@pytest.mark.parametrize(
    "bad_sha",
    [
        "short",
        "a" * 39,
        "a" * 41,
        "ai/claude-sonnet-5/DEMO-CARD1",  # branch name，非 SHA
        "ABCDEF0123456789ABCDEF0123456789ABCDEF01",  # 大寫不接受（既有慣例小寫 hex）
        "",
    ],
)
def test_invalid_sha_rejected(bad_sha):
    with pytest.raises(ValidationError):
        validate_source_sha(bad_sha)


def test_evidence_required():
    validate_evidence("some real evidence")
    with pytest.raises(ValidationError):
        validate_evidence("")
    with pytest.raises(ValidationError):
        validate_evidence("   ")


def _valid_open_kwargs(**overrides):
    kwargs = {
        "card_id": "DEMO-CARD1",
        "feature": "示範",
        "tier": "T3",
        "core_pain": "痛點",
        "service_goal": "目標",
        "db_scope": "none",
        "resources": ResourceDeclaration(db_scope="none", resources=[]),
    }
    kwargs.update(overrides)
    return kwargs


def test_validate_open_fields_accepts_complete_card():
    validate_open_fields(**_valid_open_kwargs())  # 不拋例外


def test_validate_open_fields_reports_all_missing_fields_at_once():
    with pytest.raises(ValidationError) as exc_info:
        validate_open_fields(
            **_valid_open_kwargs(
                card_id="", feature="", tier="T9", core_pain="", service_goal="", db_scope="bogus", resources=None
            )
        )
    errors = exc_info.value.errors
    assert len(errors) >= 6  # 一次列出全部缺漏，而非只回報第一個


def test_validate_open_fields_rejects_db_scope_mismatch_with_declaration():
    with pytest.raises(ValidationError):
        validate_open_fields(
            **_valid_open_kwargs(
                db_scope="write",
                resources=ResourceDeclaration(db_scope="read", resources=[]),
            )
        )


@pytest.mark.parametrize("depth", [0, 1, 2])
def test_validate_chain_depth_accepts_up_to_hard_cap(depth):
    validate_chain_depth(depth)  # 不拋例外即算通過


@pytest.mark.parametrize("depth", [3, 4, 10])
def test_validate_chain_depth_rejects_over_hard_cap(depth):
    with pytest.raises(ValidationError) as exc_info:
        validate_chain_depth(depth)
    message = "；".join(exc_info.value.errors)
    # 拒絕訊息須引用決議 5 鏈式停損協定，不能只是泛用錯誤字串。
    assert "決議 5" in message
    assert "整鏈重審" in message
    assert "2" in message  # 硬上限具體數字（原始目標之下最深 2 層）


# --------------------------------------------------------------------------
# escalation 帳的純函式（WF-22-CLI4 切片 A）
# --------------------------------------------------------------------------

from wf_cli.review import (
    CHECKPOINT_BLOCK_KEY,
    CHECKPOINT_LOG_TAG,
    ESCALATION_ACCOUNT_STATES,
    PREFLIGHT_BASES,
    PREFLIGHT_BASIS_BINDING,
    PREFLIGHT_BASIS_BINDINGS,
    WRITER_STAMPED_KEYS,
    AcceptedMark,
    CheckpointFacts,
    Finding,
    PreflightBasis,
    ReviewParseError,
    ReviewReport,
    SelfRunEntry,
    counting_eligible,
    default_accepted_marks,
    derive_counts_toward_escalation,
    derive_preflight_basis_binding,
    find_block_by_key,
    log_line_indexes,
    render_checkpoint_comment,
    render_contract_baseline_comment,
    render_escalation_facts_block,
    render_verdict_comment,
)
from wf_cli.validation import (
    build_accepted_marks,
    build_issue_event_history,
    check_attempt_not_duplicated,
    check_checkpoint_gate,
    counted_attempts,
    derive_accepted_marking_binding,
    derive_preflight_basis,
    unasserted_attempts,
    validate_accepted_overrides,
    validate_checkpoint_input,
    validate_marked_by,
    validate_review_report,
)

SHA_A, SHA_B, SHA_C = "a" * 40, "b" * 40, "c" * 40

# §3 第 1 款唯一合法的依據形狀：事件流上受管轄的 preflight pass event。
# **本 CLI 沒有任何路徑能產出它**——R2-01 移除了「寫入者具結」那一支，R4-01 移除了
# 「讀一則留言」那一支（留言內文判定不出 canonical §4.1 的「受管轄」）。這裡直接具名
# 建構，是為了測「一旦承接卡讓依據存在，整條鏈就會計數」；產線沒有任何輸入抵達得了
# 這一行（窮舉見本檔 test_no_source_path_constructs_an_event_verified_basis）。
EVENT_VERIFIED = PreflightBasis(
    basis="event-verified",
    source_event="https://github.com/acme/demo/issues/1#issuecomment-1",
    summary="（模擬承接卡）全綠",
)

# 事件 marker 前綴刻意拆開書寫：只要有一則 GitHub 留言含它的字面，整張卡的自動裁決
# 判定就會被永久隔離（docs/CONSUMER_CONFORMANCE.md 記錄 #15／#17／#21 三張卡的實測）。
# 測試檔本身不是留言，但保持同一紀律可讓「交回前 grep 新增 0 處」成為機械可查的動作。
_MARKER_V1 = "wf-review-" + "event:v1"


# 一份合格的 finding 提交載荷（給 validate_review_report 用，非 Finding 物件）。
_FINDING_PAYLOAD = {
    "finding_id": "F-01",
    "severity": "major",
    "blocking": "true",
    "finding_class": "implementation",
    "attribution": "executor",
    "root_cause_id": "rc-1",
    "evidence": "重現步驟",
    "disposition": "修好",
}


def _finding(fid="F-01", **overrides) -> Finding:
    kwargs = {
        "finding_id": fid,
        "severity": "major",
        "blocking": True,
        "finding_class": "implementation",
        "attribution": "executor",
        "root_cause_id": "rc-1",
        "evidence": "重現步驟",
        "disposition": "修好",
    }
    kwargs.update(overrides)
    return Finding(**kwargs)


def _report(result="REQUEST_CHANGES", findings=()) -> ReviewReport:
    return ReviewReport(
        review_result=result,
        core_pain_resolved="yes",
        self_run=(SelfRunEntry(command="pytest", observed="1 failed"),),
        findings=tuple(findings),
    )


# ---- accepted 的不對稱預設 ----


def test_accepted_defaults_to_true_for_every_finding():
    findings = (_finding("F-01"), _finding("F-02", finding_class="governance"))
    marks = default_accepted_marks(findings)
    assert all(m.accepted for m in marks.values())
    assert all(m.marked_by == "" and m.reason == "" for m in marks.values())


@pytest.mark.parametrize(
    "overrides, eligible",
    [
        ({}, True),
        ({"blocking": False}, False),
        ({"finding_class": "governance"}, False),
        ({"finding_class": "coordination"}, False),
        ({"finding_class": "environment"}, False),
        ({"finding_class": "authoritative-artifact"}, True),
        ({"attribution": "planner"}, False),
        ({"attribution": "reviewer"}, False),
    ],
)
def test_counting_eligible_follows_section_3_clauses_3_and_4(overrides, eligible):
    assert counting_eligible(_finding(**overrides)) is eligible


def test_counts_is_false_for_approve_regardless_of_findings():
    """§3 第 2 款：結論不是 REQUEST_CHANGES 就不計數，與 finding 是否合格無關。

    第二個案例（APPROVE ＋ 合格 blocking finding）走不出 CLI——
    ``validate_review_report`` 會先硬拒——但推導本身不得依賴那道檢查，
    否則第 2 款在推導層形同不存在。
    """
    lenient = _report("APPROVE", [_finding(blocking=False)])
    assert (
        derive_counts_toward_escalation(
            lenient, default_accepted_marks(lenient.findings), EVENT_VERIFIED
        )
        is False
    )
    contradictory = _report("APPROVE", [_finding()])
    assert (
        derive_counts_toward_escalation(
            contradictory, default_accepted_marks(contradictory.findings), EVENT_VERIFIED
        )
        is False
    )


def test_counts_is_true_only_with_an_eligible_accepted_blocking_finding():
    report = _report(findings=[_finding()])
    assert (
        derive_counts_toward_escalation(
            report, default_accepted_marks(report.findings), EVENT_VERIFIED
        )
        is True
    )

    non_eligible = _report(findings=[_finding(finding_class="coordination")])
    assert (
        derive_counts_toward_escalation(
            non_eligible, default_accepted_marks(non_eligible.findings), EVENT_VERIFIED
        )
        is False
    )


def test_marking_accepted_false_removes_the_finding_from_the_counting_set():
    report = _report(findings=[_finding("F-01")])
    marks = {"F-01": AcceptedMark(finding_id="F-01", accepted=False, reason="r", marked_by="u")}
    assert derive_counts_toward_escalation(report, marks, EVENT_VERIFIED) is False


# ---- --mark-not-accepted 的解析與身分檢查 ----


@pytest.mark.parametrize(
    "raw, needle",
    [
        ("F-01", "FINDING_ID=非空理由"),
        ("=理由", "finding_id 為空"),
        ("F-01=   ", "理由必填"),
        ("F-99=理由", "不在本次查核輸出內"),
    ],
)
def test_validate_accepted_overrides_is_fail_closed(raw, needle):
    with pytest.raises(ValidationError) as exc_info:
        validate_accepted_overrides([raw], [_finding("F-01")])
    assert needle in "；".join(exc_info.value.errors)


def test_validate_accepted_overrides_rejects_the_same_finding_twice():
    with pytest.raises(ValidationError) as exc_info:
        validate_accepted_overrides(["F-01=甲", "F-01=乙"], [_finding("F-01")])
    assert "給了多次" in "；".join(exc_info.value.errors)


def test_validate_accepted_overrides_returns_the_reason_map():
    assert validate_accepted_overrides(["F-01=證據不可重現"], [_finding("F-01")]) == {
        "F-01": "證據不可重現"
    }


def test_marked_by_must_be_present_and_must_not_be_the_card_owner():
    validate_marked_by("ruan6047", "Claude Opus 5@Claude Code（子 agent）")  # 不拋
    with pytest.raises(ValidationError):
        validate_marked_by("", "someone")
    with pytest.raises(ValidationError):
        validate_marked_by("ruan6047", "ruan6047")


def test_build_accepted_marks_layers_defaults_and_overrides():
    findings = [_finding("F-01"), _finding("F-02")]
    marks = build_accepted_marks(findings, {"F-02": "撤銷理由"}, "ruan6047")
    assert marks["F-01"].accepted is True and marks["F-01"].marked_by == ""
    assert marks["F-02"].accepted is False
    assert marks["F-02"].marked_by == "ruan6047" and marks["F-02"].reason == "撤銷理由"


def test_accepted_marking_binding_is_vacuous_while_the_writer_set_is_undeclared():
    """handoff-contract.md §5 的 writer 集合未宣告 → 恆為 structurally-vacuous。

    形狀取自 review-escalation.md §4／§5 的 authorization_binding（ai-workflow#39）：
    比對在結構上不可能失敗時，要把恆真寫進事件流，不是留一個看似有檢查的欄位。
    """
    assert (
        derive_accepted_marking_binding("ruan6047", "Claude Opus 5@Claude Code（子 agent）")
        == "structurally-vacuous"
    )
    # 宣告了 writer 集合，但 owner 欄仍是自由文字（不在集合內）→ 仍然無鑑別力。
    assert (
        derive_accepted_marking_binding(
            "ruan6047",
            "Claude Opus 5@Claude Code（子 agent）",
            authorized_writers=["ruan6047", "someone-else"],
        )
        == "structurally-vacuous"
    )
    # 兩者都落在已宣告的帳號集合內 → 「不得等於 owner」這條檢查才可能失敗。
    assert (
        derive_accepted_marking_binding(
            "ruan6047", "someone-else", authorized_writers=["ruan6047", "someone-else"]
        )
        == "substantive"
    )


def test_accepted_true_carries_not_applicable_binding_written_explicitly():
    """accepted=true 沒有行使授權；但**顯式寫出**而非省略——省略與漏填無法區分。"""
    marks = build_accepted_marks([_finding("F-01")], {}, "")
    assert marks["F-01"].binding == "not-applicable"

    report = _report(findings=[_finding("F-01")])
    block = render_escalation_facts_block(
        attempt=f"CARD-A-e0-{SHA_A}",
        escalation_epoch=0,
        report=report,
        marks=marks,
        counts_toward_escalation=True,
        preflight=EVENT_VERIFIED,
    )
    assert "accepted_marking_binding: not-applicable" in block


def test_binding_is_derived_not_hand_filled():
    """呼叫端無法從外部塞值：build_accepted_marks 只吃導出所需的輸入。"""
    marks = build_accepted_marks(
        [_finding("F-01")],
        {"F-01": "撤銷"},
        "ruan6047",
        owner_field="someone-else",
        authorized_writers=["ruan6047", "someone-else"],
    )
    assert marks["F-01"].binding == "substantive"
    marks_vacuous = build_accepted_marks(
        [_finding("F-01")], {"F-01": "撤銷"}, "ruan6047", owner_field="自由文字 owner"
    )
    assert marks_vacuous["F-01"].binding == "structurally-vacuous"


# ---- 事件流的讀回與閘門 ----


def _verdict_comment(
    card: str, sha: str, findings=(), url: str = "u", preflight=EVENT_VERIFIED
) -> dict:
    report = _report(findings=findings)
    body = render_verdict_comment(
        card_id=card,
        report=report,
        source_sha=sha,
        reviewer="Codex",
        escalation_epoch=0,
        timestamp="2026-08-12T10:00:00+08:00",
        preflight=preflight,
    )
    return {"body": body, "url": url}


def _checkpoint_comment(card: str, trigger: str, count: int = 3) -> dict:
    return {
        "body": render_checkpoint_comment(
            card_id=card,
            escalation_epoch=0,
            trigger_attempt_id=trigger,
            unique_attempt_count=count,
            checkpoint_decision="escalate",
            checkpoint_rationale="第二條件成立。",
            written_by="ruan6047",
            timestamp="2026-08-12T10:00:00+08:00",
        ),
        "url": "u-cp",
    }


def _log(*attempts: str) -> str:
    lines = ["## Log", ""]
    for attempt in attempts:
        lines.append(f"- 2026-08-12 review by wf-cli → REQUEST_CHANGES；attempt {attempt}。")
    return "\n".join(lines)


def test_escalation_facts_round_trip_through_the_rendered_comment():
    comment = _verdict_comment("CARD-A", SHA_A, findings=[_finding()])
    history = build_issue_event_history([comment])
    assert history.unknown_reasons == ()
    assert len(history.scoped_facts) == 1
    assert history.scoped_facts[0].attempt_id == f"CARD-A-e0-{SHA_A}"
    assert history.scoped_facts[0].counts_toward_escalation is True


def test_a_review_event_without_the_facts_block_is_unknown_not_non_counting():
    """cutover 語意：baseline 之前一律未知（語意見 review-escalation.md §5
    「cutover 前歷史事件維持原貌」）。"""
    legacy = {
        "body": (
            "<!-- " + _MARKER_V1 + f" card_id=CARD-A source_sha={SHA_A} "
            f"attempt_id=CARD-A-e0-{SHA_A} -->\n## 查核裁決：REQUEST_CHANGES"
        ),
        "url": "u",
    }
    history = build_issue_event_history([legacy])
    assert history.scoped_facts == ()
    assert any("未知" in reason for reason in history.unknown_reasons)


def test_contract_baseline_scopes_the_history_and_is_counted():
    junk = {"body": "派審詞引用了 wf-review-event" + ":v1 的字面", "url": "u0"}
    baseline = {
        "body": render_contract_baseline_comment(
            card_id="CARD-A",
            declared_by="ruan6047",
            rationale="切 cutover",
            timestamp="2026-08-12T09:00:00+08:00",
        ),
        "url": "u1",
    }
    history = build_issue_event_history([junk, baseline, _verdict_comment("CARD-A", SHA_A)])
    assert history.baseline_count == 1
    assert history.unknown_reasons == ()  # baseline 之前的壞留痕不進 scope


def test_duplicate_attempt_is_refused_using_the_whole_timeline():
    history = build_issue_event_history([_verdict_comment("CARD-A", SHA_A)])
    with pytest.raises(ValidationError) as exc_info:
        check_attempt_not_duplicated(history, f"CARD-A-e0-{SHA_A}")
    assert "marker_quarantined" in "；".join(exc_info.value.errors)
    check_attempt_not_duplicated(history, f"CARD-A-e0-{SHA_B}")  # 不同 SHA 不拋


def test_counted_attempts_dedupes_and_filters_by_epoch():
    comments = [
        _verdict_comment("CARD-A", SHA_A, findings=[_finding("F-1")]),
        _verdict_comment("CARD-A", SHA_A, findings=[_finding("F-1")]),  # 同 attempt 重送
        _verdict_comment("CARD-A", SHA_B, findings=[_finding("F-2", finding_class="governance")]),
    ]
    history = build_issue_event_history(comments)
    counted = counted_attempts(history, 0)
    assert [f.attempt_id for f in counted] == [f"CARD-A-e0-{SHA_A}"]
    assert counted_attempts(history, 1) == []


def _three_counted_history(card="CARD-A"):
    comments = [
        _verdict_comment(card, sha, findings=[_finding(f"F-{i}")])
        for i, sha in enumerate((SHA_A, SHA_B, SHA_C), start=1)
    ]
    return build_issue_event_history(comments)


def test_gate_passes_below_three_counted_attempts():
    comments = [
        _verdict_comment("CARD-A", sha, findings=[_finding(f"F-{i}")])
        for i, sha in enumerate((SHA_A, SHA_B), start=1)
    ]
    check_checkpoint_gate(build_issue_event_history(comments), escalation_epoch=0, card_body="")


def test_gate_blocks_when_the_third_counted_attempt_has_no_checkpoint():
    with pytest.raises(ValidationError) as exc_info:
        check_checkpoint_gate(_three_counted_history(), escalation_epoch=0, card_body="")
    assert "尚未建立 escalation-checkpoint" in "；".join(exc_info.value.errors)


def test_gate_requires_both_faces_comment_block_and_log_index():
    trigger = f"CARD-A-e0-{SHA_C}"
    comments = [
        _verdict_comment("CARD-A", sha, findings=[_finding(f"F-{i}")])
        for i, sha in enumerate((SHA_A, SHA_B, SHA_C), start=1)
    ] + [_checkpoint_comment("CARD-A", trigger)]
    history = build_issue_event_history(comments)

    # 只有留言、Log 沒有同行索引 → 仍算未建立。
    with pytest.raises(ValidationError):
        check_checkpoint_gate(history, escalation_epoch=0, card_body=_log())

    # ⭐ **時戳必須帶時分秒與時區，⛔ 不能只寫日期。**
    #
    # (a) 現在的行為：這一行用完整 ISO-8601（`<date>T<time><tz>`），⛔ 不是 `2026-08-12`。
    # (b) 為什麼：閘門的 Log 面走 `review.log_line_indexes`，而它只認
    #     `doctor._DRIFT_EVENT_START_RE` 判定為**事件起始行**的那些行——該樣式要求完整
    #     時戳。產線那一側 `commands/checkpoint_cmd` 寫的是 `card.now_iso8601()`，本來就
    #     帶時分秒；夾具若用無時分秒的日期，就是**測試比產線寬鬆**：改動前
    #     `log_line_indexes` 逐物理行掃描，那種不合格的行照樣被當成索引通過。
    # (c) ⛔ **不得由此推出「所有夾具的時戳都該改成完整 ISO」**——只有**會被
    #     `_DRIFT_EVENT_START_RE` 讀**的那些行才需要。本檔同一個測試裡的 `_log()` 寫的是
    #     `review by wf-cli` 標籤，而本閘門查的是 `checkpoint by wf-cli` ⇒ 它**不承重**，
    #     實測改與不改結果相同，故刻意留著原樣。
    card_body = _log() + (
        f"\n- 2026-08-12T10:00:00+08:00 checkpoint by wf-cli → trigger {trigger}。"
    )
    check_checkpoint_gate(history, escalation_epoch=0, card_body=card_body)


def test_gate_refuses_when_any_scoped_marker_is_unreadable():
    history = build_issue_event_history(
        [{"body": "討論中引用 wf-review-event" + ":v1 前綴", "url": "u"}]
    )
    with pytest.raises(ValidationError) as exc_info:
        check_checkpoint_gate(history, escalation_epoch=0, card_body="")
    assert "不得推定為不計數" in "；".join(exc_info.value.errors)


def test_gate_fails_loud_on_a_second_contract_baseline():
    baseline = {
        "body": render_contract_baseline_comment(
            card_id="CARD-A", declared_by="ruan6047", rationale="切", timestamp="t"
        ),
        "url": "u",
    }
    history = build_issue_event_history([baseline, baseline])
    with pytest.raises(ValidationError) as exc_info:
        check_checkpoint_gate(history, escalation_epoch=0, card_body="")
    assert "one-shot" in "；".join(exc_info.value.errors)


# ---- checkpoint 欄位檢查 ----


def _checkpoint_kwargs(**overrides):
    kwargs = {
        "card_id": "CARD-A",
        "escalation_epoch": 0,
        "trigger_attempt_id": f"CARD-A-e0-{SHA_C}",
        "unique_attempt_count": 3,
        "checkpoint_decision": "escalate",
        "checkpoint_rationale": "第二條件成立。",
    }
    kwargs.update(overrides)
    return kwargs


def test_validate_checkpoint_input_accepts_a_conformant_event():
    validate_checkpoint_input(**_checkpoint_kwargs())


@pytest.mark.parametrize(
    "overrides, needle",
    [
        ({"trigger_attempt_id": "not-an-attempt"}, "不符 `<card>-e<epoch>"),
        ({"trigger_attempt_id": f"OTHER-e0-{SHA_C}"}, "與本次 card_id"),
        ({"trigger_attempt_id": f"CARD-A-e1-{SHA_C}"}, "不符；checkpoint 只結本 epoch 的帳"),
        ({"unique_attempt_count": 2}, "必須 >= 3"),
        ({"checkpoint_decision": "continue-ish"}, "checkpoint_decision 必須是"),
        ({"checkpoint_rationale": "   "}, "必填且不得為空"),
        ({"checkpoint_rationale": "有 ``` 圍籬"}, "圍籬字元"),
    ],
)
def test_validate_checkpoint_input_is_fail_closed(overrides, needle):
    with pytest.raises(ValidationError) as exc_info:
        validate_checkpoint_input(**_checkpoint_kwargs(**overrides))
    assert needle in "；".join(exc_info.value.errors)


def test_checkpoint_rejects_escalation_resolution_and_points_at_the_separate_event_type():
    """缺口已由 ai-workflow#39 補上，而補法**否決**了 checkpoint 欄位這條路。

    拒收行為本身不變；此測試釘住的是訊息指向的方向——不得再暗示「等契約卡落地後
    這個鍵就會合法」，也不得叫人把裁定寫進 checkpoint_rationale 冒充裁定。
    """
    with pytest.raises(ValidationError) as exc_info:
        validate_checkpoint_input(**_checkpoint_kwargs(escalation_resolution="continue"))
    message = "；".join(exc_info.value.errors)
    assert "escalation_resolution" in message
    assert "永遠不會是" in message
    assert "escalation-resolution" in message  # 指向獨立事件型別
    assert "不構成裁定" in message  # rationale 只是人讀脈絡
    # 舊訊息把讀者導向一個已被否決的結局，不得復活。
    assert "另開卡承接" not in message
    assert "請等該契約卡落地" not in message


def test_checkpoint_rejects_deferred_findings_because_both_causes_are_unavailable():
    with pytest.raises(ValidationError) as exc_info:
        validate_checkpoint_input(**_checkpoint_kwargs(deferred_findings=["F-01"]))
    message = "；".join(exc_info.value.errors)
    assert "deferred_findings" in message
    assert "closure_reporting_requested" in message  # 指名缺的是哪兩欄


def test_rendered_checkpoint_block_never_carries_an_event_marker_prefix():
    body = render_checkpoint_comment(
        card_id="CARD-A",
        escalation_epoch=0,
        trigger_attempt_id=f"CARD-A-e0-{SHA_C}",
        unique_attempt_count=3,
        checkpoint_decision="continue",
        checkpoint_rationale="根因已收斂。",
        written_by="ruan6047",
        timestamp="t",
    )
    assert "wf-review-event" not in body  # 方案 B：不自立第三套 marker 文法
    facts = CheckpointFacts(
        escalation_epoch=0,
        trigger_attempt_id=f"CARD-A-e0-{SHA_C}",
        unique_attempt_count=3,
        checkpoint_decision="continue",
    )
    assert build_issue_event_history([{"body": body, "url": "u"}]).checkpoints == (facts,)


def test_facts_block_survives_values_that_need_quoting():
    report = _report(findings=[_finding("F 01: 帶空白與冒號", root_cause_id="rc #1")])
    block = render_escalation_facts_block(
        attempt=f"CARD-A-e0-{SHA_A}",
        escalation_epoch=0,
        report=report,
        marks=default_accepted_marks(report.findings),
        counts_toward_escalation=True,
        preflight=EVENT_VERIFIED,
    )
    history = build_issue_event_history(
        [{"body": "<!-- " + _MARKER_V1 + f" card_id=CARD-A source_sha={SHA_A} "
                  f"attempt_id=CARD-A-e0-{SHA_A} -->\n{block}", "url": "u"}]
    )
    assert history.unknown_reasons == ()
    assert history.scoped_facts[0].counts_toward_escalation is True


def test_log_index_uses_token_boundary_not_substring():
    """`attempt in line` 會讓 `…-e0-<sha>` 命中 `…-e0-<sha>x`（doctor 已踩過三次）。"""
    trigger = f"CARD-A-e0-{SHA_C}"
    assert log_line_indexes(f"- checkpoint by wf-cli → trigger {trigger}。", CHECKPOINT_LOG_TAG, trigger)
    assert not log_line_indexes(
        f"- checkpoint by wf-cli → trigger {trigger}x。", CHECKPOINT_LOG_TAG, trigger
    )
    # 同一行才算：tag 與 token 分行不成立。
    assert not log_line_indexes(
        f"- checkpoint by wf-cli\n- trigger {trigger}。", CHECKPOINT_LOG_TAG, trigger
    )


def test_two_same_type_blocks_in_one_comment_are_refused_not_guessed():
    body = render_checkpoint_comment(
        card_id="CARD-A",
        escalation_epoch=0,
        trigger_attempt_id=f"CARD-A-e0-{SHA_C}",
        unique_attempt_count=3,
        checkpoint_decision="escalate",
        checkpoint_rationale="甲",
        written_by="ruan6047",
        timestamp="t",
    )
    doubled = body + "\n" + body
    with pytest.raises(ReviewParseError):
        find_block_by_key(doubled, CHECKPOINT_BLOCK_KEY)


# ---- owner 的時點快照（#39 §5 第 3 款的載荷） ----


def test_owner_snapshot_key_is_named_as_a_point_in_time_not_an_intrinsic_property():
    """鍵名承載語意：叫 `owner` 會讓下游把時點值當成 attempt 的固有屬性。"""
    report = _report(findings=[_finding()])
    block = render_escalation_facts_block(
        attempt=f"CARD-A-e0-{SHA_A}",
        escalation_epoch=0,
        report=report,
        marks=default_accepted_marks(report.findings),
        counts_toward_escalation=True,
        preflight=EVENT_VERIFIED,
        owner_field_at_verdict_write="Codex",
    )
    assert "owner_field_at_verdict_write: Codex" in block
    # 不得出現裸的頂層 `owner:` 鍵——那正是要避免的讀法。
    assert not any(line.strip().startswith("owner:") for line in block.splitlines())


def test_owner_snapshot_is_written_even_when_the_project_field_is_empty():
    """省略與漏填無法區分：欄位為空時寫 ""（鍵在、值空），不是不寫。"""
    report = _report(findings=[])
    block = render_escalation_facts_block(
        attempt=f"CARD-A-e0-{SHA_A}",
        escalation_epoch=0,
        report=report,
        marks={},
        counts_toward_escalation=False,
        preflight=EVENT_VERIFIED,
        owner_field_at_verdict_write=None,
    )
    assert 'owner_field_at_verdict_write: ""' in block


def test_absent_owner_key_and_empty_owner_value_are_distinguishable_on_read_back():
    """三態：None＝鍵不存在（未知）／""＝欄位為空／其餘＝快照值。"""
    def facts_for(owner):
        comment = _verdict_comment("CARD-A", SHA_A, findings=[_finding()])
        body = comment["body"]
        if owner is None:  # 模擬「鍵根本不在」的舊事件
            body = "\n".join(
                line for line in body.splitlines()
                if not line.strip().startswith("owner_field_at_verdict_write:")
            )
        else:
            body = body.replace(
                'owner_field_at_verdict_write: ""',
                f"owner_field_at_verdict_write: {owner}" if owner else 'owner_field_at_verdict_write: ""',
            )
        return build_issue_event_history([{"body": body, "url": "u"}]).scoped_facts[0]

    assert facts_for(None).owner_field_at_verdict_write is None
    assert facts_for("").owner_field_at_verdict_write == ""
    assert facts_for("Codex").owner_field_at_verdict_write == "Codex"


def test_missing_owner_key_does_not_make_the_attempt_unknown_to_the_gate():
    """owner 快照不是閘門輸入：缺它不得多產生一條讓閘門拒絕的路徑。"""
    body = _verdict_comment("CARD-A", SHA_A, findings=[_finding()])["body"]
    body = "\n".join(
        line for line in body.splitlines()
        if not line.strip().startswith("owner_field_at_verdict_write:")
    )
    history = build_issue_event_history([{"body": body, "url": "u"}])
    assert history.unknown_reasons == ()
    assert len(history.scoped_facts) == 1


# ---- §3 第 1 款：preflight 依據（R1／R2／R3／R4 同一根因的第四次修正） ----
#
# 四輪的線，寫在這裡讓後來的人一眼看見出口在哪裡被堵上：
#   R1 預設 true → R2 具結 true → R3 三值 unknown／unavailable → R4 讀留言內文。
# 前三輪都在換「寫什麼值」，R3 才動「要不要寫」，R4 打的是「憑什麼判定可以寫」。
# 本輪的處置不是把讀取器驗得更嚴，是**移除讀取器**：canonical §4.1 的「受管轄」是通道
# 屬性，留言內文任何人都寫得出來，補欄位只是把同一個洞往後推一格。
#
# ⚠️ 需求方 2026-08-12 裁定另否決了本輪初稿的「恆拒寫入」：那會讓狀態面再次分不出
# 「已查核」與「未查核」（ai-workflow#13 解過的問題）。故最終判準是**照寫，但把恆虛性
# 導出到事件上**——`preflight_basis_binding: structurally-unavailable` ＋
# `escalation_account: not-asserted`，由 writer 加蓋、提交面不得含此鍵（#39 §5 第 7 款）。


def test_preflight_basis_has_no_writer_attested_option_any_more():
    assert PREFLIGHT_BASES == ("event-verified", "not-established")
    assert PreflightBasis().established is False
    assert PreflightBasis(basis="event-verified").established is False


def test_the_binding_is_named_structurally_unavailable_not_merely_absent():
    """恆虛的成因必須有名字：等承接卡，不是等下一則留言（形狀同 #39 的 structurally-vacuous）。"""
    assert PREFLIGHT_BASIS_BINDING == "structurally-unavailable"
    assert PREFLIGHT_BASIS_BINDINGS == ("event-verified", "structurally-unavailable")
    assert ESCALATION_ACCOUNT_STATES == ("asserted", "not-asserted")


def test_derive_preflight_basis_never_establishes_and_never_raises():
    """R4-01＋需求方裁定：依據恆不成立，但**不得拒絕寫入**（否則狀態面又分不出已查核）。"""
    basis = derive_preflight_basis(card_id="CARD-A", source_sha=SHA_A)
    assert basis.established is False
    assert basis.basis == "not-established"
    # 導出綁定：恆為 structurally-unavailable，且**呼叫端塞不進值**（只吃 basis 物件）。
    assert derive_preflight_basis_binding(basis) == "structurally-unavailable"
    assert derive_preflight_basis_binding(EVENT_VERIFIED) == "event-verified"
    assert derive_preflight_basis_binding(None) == "structurally-unavailable"


def test_writer_stamped_keys_are_rejected_on_the_submission_side():
    """#39 §5 第 7 款：驗來源不驗值——提交面含此鍵即拒收，**即使值等於導出值**。"""
    assert WRITER_STAMPED_KEYS == (
        "preflight_passed",
        "preflight_basis_binding",
        "escalation_account",
    )
    for key, value in (
        ("preflight_basis_binding", "structurally-unavailable"),  # 恰好等於導出值
        ("escalation_account", "not-asserted"),
        ("preflight_passed", "true"),
    ):
        payload = {
            "review_result": "REQUEST_CHANGES",
            "core_pain_resolved": "yes",
            "self_run": [{"command": "uv run pytest", "observed": "1 failed"}],
            "findings": [dict(_FINDING_PAYLOAD)],
            key: value,
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_review_report(payload)
        message = "；".join(exc_info.value.errors)
        assert key in message
        assert "即使值恰好等於導出值也一樣拒收" in message
    # finding 層級同樣擋。
    finding_payload = dict(_FINDING_PAYLOAD)
    finding_payload["escalation_account"] = "asserted"
    with pytest.raises(ValidationError):
        validate_review_report(
            {
                "review_result": "REQUEST_CHANGES",
                "core_pain_resolved": "yes",
                "self_run": [{"command": "uv run pytest", "observed": "1 failed"}],
                "findings": [finding_payload],
            }
        )


def test_no_reader_from_comment_content_exists_any_more():
    """R4-01 的重現對象已不存在：沒有任何 `body → PreflightBasis` 的公開路徑。"""
    import inspect

    import wf_cli.review as review_mod
    import wf_cli.validation as validation_mod

    for name in ("preflight_basis_from_body", "PREFLIGHT_BLOCK_KEY"):
        assert not hasattr(review_mod, name), f"review.{name} 應已移除"
    for name in ("find_preflight_basis", "check_preflight_event_present"):
        assert not hasattr(validation_mod, name), f"validation.{name} 應已移除"

    # 與 preflight 有關的函式恰為兩個導出器，**兩個都不吃任何留言內容**。
    producers = {
        f"{mod.__name__}.{name}"
        for mod in (review_mod, validation_mod)
        for name in dir(mod)
        if "preflight" in name.lower() and inspect.isfunction(getattr(mod, name, None))
    }
    assert producers == {
        "wf_cli.validation.derive_preflight_basis",
        "wf_cli.review.derive_preflight_basis_binding",
    }, producers
    assert list(inspect.signature(derive_preflight_basis).parameters) == [
        "card_id",
        "source_sha",
    ]
    assert list(inspect.signature(derive_preflight_basis_binding).parameters) == ["preflight"]


@pytest.mark.parametrize(
    "body, label",
    [
        ("一般留言，沒有任何區塊。", "任意一般 Issue 留言"),
        (
            "\n".join(
                ["```yaml", "wf_preflight_pass: v1", "card_id: CARD-A",
                 f"source_sha: {SHA_A}", "preflight_passed: true", "```"]
            ),
            "查核者的原始重現：四欄、缺 event_url",
        ),
        (
            "\n".join(
                ["```yaml", "wf_preflight_pass: v1", "card_id: CARD-A",
                 f"source_sha: {SHA_A}", "preflight_passed: true",
                 "event_url: https://example.invalid/#issuecomment-1", "```"]
            ),
            "四欄＋event_url",
        ),
        (
            "\n".join(
                ["```yaml", "wf_preflight_pass: v1", "card_id: CARD-A",
                 f"source_sha: {SHA_A}", "preflight_passed: true",
                 "event_id: 018f-dead-beef", "type: handoff-accepted",
                 "actor: ruan6047", "occurred_at: 2026-08-12T21:00:00+08:00",
                 "state_version: 7", "iteration: 4", "evidence: pytest 全綠",
                 "event_url: https://example.invalid/#issuecomment-1", "```"]
            ),
            "補齊 canonical §4.1 的整組 lifecycle envelope",
        ),
    ],
)
def test_no_issue_comment_of_any_shape_can_establish_a_preflight_basis(body, label):
    """留言內文是資料不是通道證明：補到 envelope 齊全一樣不成立依據。

    做法是**窮舉** `wf_cli.review` 裡每一個吃 `body` 的公開函式，把這則留言餵進去，斷言
    沒有任何一個回傳 `PreflightBasis`。這比「檢查某個函式已刪除」強：它擋的是「換個名字
    重新長出來」。掃到的函式清單列在失敗訊息裡，避免「掃到零個所以零命中」的假通過。
    """
    import inspect

    import wf_cli.review as review_mod

    probed: list[str] = []
    for name in sorted(review_mod.__all__):
        fn = getattr(review_mod, name)
        if not inspect.isfunction(fn):
            continue
        params = list(inspect.signature(fn).parameters)
        if not params or params[0] != "body":
            continue
        probed.append(name)
        try:
            result = fn(body)
        except (ReviewParseError, TypeError, ValueError):
            continue
        assert not isinstance(result, PreflightBasis), (
            f"{label}：{name}() 由留言內文產出了 preflight 依據（R4-01 的形狀）"
        )
    assert probed, "沒有掃到任何吃 body 的公開函式，證據無效"
    # 判準（需求方 2026-08-12 裁定後）：不是「一律拒絕」，是**一律導出
    # structurally-unavailable**——留言擺在那裡也改變不了導出值。
    basis = derive_preflight_basis(card_id="CARD-A", source_sha=SHA_A)
    assert basis.established is False
    assert derive_preflight_basis_binding(basis) == PREFLIGHT_BASIS_BINDING


def test_no_source_path_constructs_an_event_verified_basis():
    """窮舉 `src/wf_cli` 全部模組：沒有任何一處建構 `basis="event-verified"`。

    「可計數在今天結構上不可達」是本卡從 R2 起反覆宣稱的事實。前幾輪它靠散文與旗標盤點
    支撐，而 R4-01 證明那不夠——讀取器就是一條沒被盤到的建構路徑。這裡改由 AST 窮舉產生
    證據（canonical §6.2：完整性宣稱必須由指令輸出產生），掃到的檔案清單一併列在失敗訊息
    裡，避免「掃了零個檔案所以零命中」這種假通過。
    """
    scanned: list[str] = []
    offenders: list[str] = []
    for path in sorted(_SRC_ROOT.rglob("*.py")):
        scanned.append(str(path.relative_to(_SRC_ROOT)))
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name not in {"PreflightBasis", "replace"}:
                continue
            for kw in node.keywords:
                if (
                    kw.arg == "basis"
                    and isinstance(kw.value, ast.Constant)
                    and kw.value.value == "event-verified"
                ):
                    offenders.append(f"{path.relative_to(_SRC_ROOT)}:{node.lineno}")
    assert len(scanned) >= 10, f"掃到的檔案太少，證據無效：{scanned}"
    assert offenders == [], (
        f"src 內出現建構 event-verified 依據的路徑：{offenders}"
        f"（已掃 {len(scanned)} 檔：{scanned}）"
    )


def test_counts_derivation_refuses_to_run_without_an_established_basis():
    """防禦縱深：呼叫端漏擋時，推導本身也不得回傳一個值。"""
    report = _report(findings=[_finding()])
    marks = default_accepted_marks(report.findings)
    with pytest.raises(ValueError):
        derive_counts_toward_escalation(report, marks)
    with pytest.raises(ValueError):
        derive_counts_toward_escalation(report, marks, PreflightBasis())
    assert derive_counts_toward_escalation(report, marks, EVENT_VERIFIED) is True


def test_renderer_refuses_to_assert_the_account_without_a_basis():
    """防禦縱深：無依據卻帶 counts＝本卡族四輪的病灶本體，直接拋錯。"""
    report = _report(findings=[_finding()])
    with pytest.raises(ValueError):
        render_escalation_facts_block(
            attempt=f"CARD-A-e0-{SHA_A}",
            escalation_epoch=0,
            report=report,
            marks=default_accepted_marks(report.findings),
            counts_toward_escalation=True,  # 無 preflight 卻要斷言
        )
    # 反向：有依據卻不給 counts，也是留白，同樣拒絕。
    with pytest.raises(ValueError):
        render_escalation_facts_block(
            attempt=f"CARD-A-e0-{SHA_A}",
            escalation_epoch=0,
            report=report,
            marks=default_accepted_marks(report.findings),
            counts_toward_escalation=None,
            preflight=EVENT_VERIFIED,
        )


def test_unavailable_block_stamps_the_binding_and_omits_the_two_asserting_keys():
    """需求方裁定的核心：寫得出事件，且**事件上看得見**這道閘門沒有鑑別力。"""
    report = _report(findings=[_finding()])
    block = render_escalation_facts_block(
        attempt=f"CARD-A-e0-{SHA_A}",
        escalation_epoch=0,
        report=report,
        marks=default_accepted_marks(report.findings),
        counts_toward_escalation=None,
    )
    assert "preflight_basis_binding: structurally-unavailable" in block
    assert "escalation_account: not-asserted" in block
    # 兩個斷言用的鍵**都不出現**——不是寫成 unknown／unavailable（R3-01 的禁令）。
    assert "preflight_passed" not in block
    assert "counts_toward_escalation" not in block
    assert "unknown" not in block and "unavailable:" not in block
    # findings 仍逐項落地：不斷言帳，不等於不記錄查核內容。
    assert "finding_id: F-01" in block and "accepted: true" in block


def test_written_block_asserts_preflight_passed_true_as_a_literal():
    """§5「Adapter 必填欄位」把該欄釘為字面 true；依據成立時寫出來的事件必須逐字如此。"""
    report = _report(findings=[_finding()])
    block = render_escalation_facts_block(
        attempt=f"CARD-A-e0-{SHA_A}",
        escalation_epoch=0,
        report=report,
        marks=default_accepted_marks(report.findings),
        counts_toward_escalation=True,
        preflight=EVENT_VERIFIED,
    )
    assert "preflight_passed: true" in block
    assert "preflight_basis_binding: event-verified" in block
    assert "escalation_account: asserted" in block
    assert "unknown" not in block and "unavailable" not in block


def test_non_boolean_counts_value_is_unreadable_not_a_third_state():
    """讀取側同樣不接受擴充值：unavailable 一律視為讀不懂 → 未知 → 閘門 fail-closed。"""
    comment = _verdict_comment("CARD-A", SHA_A, findings=[_finding()])
    comment["body"] = comment["body"].replace(
        "counts_toward_escalation: true", "counts_toward_escalation: unavailable"
    )
    history = build_issue_event_history([comment])
    assert history.scoped_facts == ()
    assert any("未知" in reason for reason in history.unknown_reasons)


def test_not_asserted_event_is_readable_but_never_counts():
    """「未斷言」與「讀不懂」必須分開：前者讀得出來、閘門不擋，但一律不計數。"""
    report = _report(findings=[_finding()])
    body = render_verdict_comment(
        card_id="CARD-A",
        report=report,
        source_sha=SHA_A,
        reviewer="Codex",
        escalation_epoch=0,
        timestamp="2026-08-12T12:00:00+08:00",
    )
    history = build_issue_event_history([{"body": body, "url": "u1"}])
    assert history.unknown_reasons == ()  # 讀得懂 → 下一則裁決不會被閘門擋住
    (fact,) = history.scoped_facts
    assert fact.counts_toward_escalation is None
    assert fact.account_asserted is False
    assert fact.counts is False  # 不計數
    assert fact.preflight_basis_binding == "structurally-unavailable"
    assert counted_attempts(history, 0) == []
    # 但**不得**被讀成「執行者沒有累計」：未斷言的 attempt 拿得到。
    assert [f.attempt_id for f in unasserted_attempts(history, 0)] == [f"CARD-A-e0-{SHA_A}"]


@pytest.mark.parametrize(
    "mangle, label",
    [
        (lambda b: b.replace("escalation_account: not-asserted", "escalation_account: asserted"),
         "帳狀態與綁定互相矛盾"),
        (lambda b: b.replace(
            "preflight_basis_binding: structurally-unavailable",
            "preflight_basis_binding: structurally-unavailable\ncounts_toward_escalation: true"),
         "未斷言的事件卻帶 counts"),
        (lambda b: b.replace(
            "preflight_basis_binding: structurally-unavailable",
            "preflight_basis_binding: structurally-unavailable\npreflight_passed: true"),
         "未斷言的事件卻帶 preflight_passed"),
        (lambda b: b.replace("escalation_account: not-asserted", "escalation_account: 隨便"),
         "帳狀態不在封閉列舉內"),
    ],
)
def test_self_contradictory_account_blocks_are_unreadable(mangle, label):
    """事後被改過的事件不得被半信半疑地採用：自相矛盾一律回未知 → 閘門 fail-closed。"""
    report = _report(findings=[_finding()])
    body = render_verdict_comment(
        card_id="CARD-A",
        report=report,
        source_sha=SHA_A,
        reviewer="Codex",
        escalation_epoch=0,
        timestamp="2026-08-12T12:00:00+08:00",
    )
    history = build_issue_event_history([{"body": mangle(body), "url": "u1"}])
    assert history.scoped_facts == (), label
    assert any("未知" in reason for reason in history.unknown_reasons), label


# --------------------------------------------------------------------------
# 在庫的突變證據（跨家族查核者跑得到的那一份）
# --------------------------------------------------------------------------
#
# 前三輪的突變證據都放在 scratchpad 的一次性 harness 裡，**查核者看不到也跑不了**，
# 於是「40 條全數 KILLED」對他而言只是一句自陳——而自陳大於證據正是本卡族被打了三輪
# 的同一個病。這裡把最吃重的幾條 fail-closed 判準搬進 repo：每一條都在**臨時複本**上
# 改壞原始碼，再以子行程驗證該判準真的不成立。
#
# 每個探針都先斷言 `wf_cli.__file__` 落在複本裡——「宣告成功前先核執行身分」：
# 不能出現「我以為測到的是突變版，其實載到的是原版」。

_SRC_ROOT = pathlib.Path(__file__).resolve().parents[1] / "src"

_PROBE_PREAMBLE = """
import os, sys
import wf_cli
assert wf_cli.__file__.startswith(os.environ["EXPECT_ROOT"]), (
    "載到的不是複本：" + wf_cli.__file__
)
from wf_cli.review import (
    PREFLIGHT_BASES, PREFLIGHT_BASIS_BINDING, AcceptedMark, Finding,
    PreflightBasis, ReviewReport, SelfRunEntry, derive_counts_toward_escalation,
    derive_preflight_basis_binding, render_escalation_facts_block,
)
from wf_cli.validation import (
    ValidationError, build_issue_event_history, derive_preflight_basis,
)

SHA = "a" * 40
OTHER = "b" * 40

def finding(**kw):
    base = dict(finding_id="F-01", severity="major", blocking=True,
                finding_class="implementation", attribution="executor",
                root_cause_id="rc-1", evidence="e", disposition="d")
    base.update(kw)
    return Finding(**base)

def report(result="REQUEST_CHANGES", findings=None):
    fs = (finding(),) if findings is None else tuple(findings)
    return ReviewReport(review_result=result, core_pain_resolved="yes",
                        self_run=(SelfRunEntry(command="pytest", observed="1 failed"),),
                        findings=fs)

def marks(fs):
    return {f.finding_id: AcceptedMark(finding_id=f.finding_id, accepted=True) for f in fs}

def raises(exc, fn):
    try:
        fn()
    except exc:
        return
    raise AssertionError("預期拋出 " + exc.__name__ + "，但沒有")
"""


def _run_probe(probe_body: str, mutation: tuple[str, str, str] | None) -> subprocess.CompletedProcess:
    """在 ``src`` 的臨時複本上（可選地）套用一處突變，然後跑探針。"""
    with tempfile.TemporaryDirectory() as tmp:
        dst = pathlib.Path(tmp) / "src"
        shutil.copytree(_SRC_ROOT, dst)
        if mutation is not None:
            rel, old, new = mutation
            target = dst / rel
            text = target.read_text(encoding="utf-8")
            assert text.count(old) == 1, f"突變錨點在 {rel} 出現 {text.count(old)} 次（需恰為 1）"
            target.write_text(text.replace(old, new), encoding="utf-8")
        env = {**os.environ, "PYTHONPATH": str(dst), "EXPECT_ROOT": str(dst)}
        env.pop("PYTHONDONTWRITEBYTECODE", None)
        return subprocess.run(
            [sys.executable, "-c", _PROBE_PREAMBLE + probe_body],
            capture_output=True, text=True, env=env, check=False,
        )


# (突變名, 檔, 原字串, 改成, 探針)
#
# 每一條對應一個「拿掉它就綠不了」的 fail-closed 判準。查核者可直接
# `uv run pytest -k mutated` 自己重現——前三輪的突變證據放在 scratchpad，查核者跑不到，
# 等於自陳；那個缺口本身就是本卡族被打的同一種病。
_MUTANTS = [
    (
        "依據導出器改成回傳 event-verified（R4-01 的形狀：任意輸入即可解鎖計數）",
        "wf_cli/validation.py",
        "    **本函式刻意不掃留言**（``comments`` 不在簽章上）：能被留言影響的依據就不是導出值。\n    \"\"\"\n    return PREFLIGHT_NOT_ESTABLISHED",
        "    **本函式刻意不掃留言**（``comments`` 不在簽章上）：能被留言影響的依據就不是導出值。\n    \"\"\"\n    return PreflightBasis(basis=\"event-verified\", source_event=\"x\")",
        (
            "b = derive_preflight_basis(card_id='C', source_sha=SHA)\n"
            "assert b.established is False\n"
            "assert derive_preflight_basis_binding(b) == 'structurally-unavailable'\n"
        ),
    ),
    (
        "綁定導出器把恆虛性說成 event-verified（事件上再也看不見閘門沒有鑑別力）",
        "wf_cli/review.py",
        'return "event-verified" if (preflight and preflight.established) else PREFLIGHT_BASIS_BINDING',
        'return "event-verified"',
        (
            "assert derive_preflight_basis_binding(None) == 'structurally-unavailable'\n"
            "assert derive_preflight_basis_binding(PreflightBasis()) == "
            "'structurally-unavailable'\n"
        ),
    ),
    (
        "綁定值被改寫成「只是這一則沒有」（等承接卡 vs 等下一則留言，處置不同）",
        "wf_cli/review.py",
        'PREFLIGHT_BASIS_BINDING = "structurally-unavailable"',
        'PREFLIGHT_BASIS_BINDING = "not-established"',
        (
            "assert PREFLIGHT_BASIS_BINDING == 'structurally-unavailable'\n"
            "b = derive_preflight_basis(card_id='C', source_sha=SHA)\n"
            "assert derive_preflight_basis_binding(b) == 'structurally-unavailable'\n"
        ),
    ),
    (
        "無依據時偷偷把帳斷言成 false（洗白：本該未斷言的 attempt 變成已判定不計數）",
        "wf_cli/review.py",
        "    if not asserted and counts_toward_escalation is not None:",
        "    if False:",
        (
            "r = report()\n"
            "blk = render_escalation_facts_block(attempt='C-e0-' + SHA, escalation_epoch=0,\n"
            "    report=r, marks=marks(r.findings), counts_toward_escalation=None)\n"
            "assert 'escalation_account: not-asserted' in blk\n"
            "assert 'counts_toward_escalation' not in blk\n"
            "raises(ValueError, lambda: render_escalation_facts_block(\n"
            "    attempt='C-e0-' + SHA, escalation_epoch=0, report=r,\n"
            "    marks=marks(r.findings), counts_toward_escalation=False))\n"
        ),
    ),
    (
        "無依據時仍寫出 preflight_passed: true（R1-01 的偽造，換個位置回來）",
        "wf_cli/review.py",
        '    if asserted:\n        # §5「Adapter 必填欄位」的字面 true，且**只在依據成立時**才寫得出來。\n        lines.append("preflight_passed: true")',
        '    if True:\n        lines.append("preflight_passed: true")',
        (
            "r = report()\n"
            "blk = render_escalation_facts_block(attempt='C-e0-' + SHA, escalation_epoch=0,\n"
            "    report=r, marks=marks(r.findings), counts_toward_escalation=None)\n"
            "assert 'preflight_passed' not in blk\n"
        ),
    ),
    (
        "讀取側把「未斷言」當成「已判定不計數」（消費者會把真實退回讀成零）",
        "wf_cli/review.py",
        "        return self.counts_toward_escalation is True",
        "        return self.counts_toward_escalation is not True",
        (
            "from wf_cli.review import EscalationFacts\n"
            "f = EscalationFacts(attempt_id='C-e0-' + SHA, escalation_epoch=0,\n"
            "    review_result='REQUEST_CHANGES', counts_toward_escalation=None)\n"
            "assert f.counts is False\n"
        ),
    ),
    (
        "讀取側接受自相矛盾的事件（帳狀態與綁定不一致仍照收）",
        "wf_cli/review.py",
        '    if (account == "asserted") != (binding == "event-verified"):\n        return None',
        "    pass",
        (
            "r = report()\n"
            "blk = render_escalation_facts_block(attempt='C-e0-' + SHA, escalation_epoch=0,\n"
            "    report=r, marks=marks(r.findings), counts_toward_escalation=None)\n"
            "from wf_cli.review import escalation_facts_from_body\n"
            # 綁定說「依據成立」、帳狀態說「未斷言」——拿掉一致性檢查就會照收，
            # 並在事件流上留下一則綁定值不可信的事實。
            "bad = blk.replace('preflight_basis_binding: structurally-unavailable',\n"
            "                  'preflight_basis_binding: event-verified')\n"
            "assert escalation_facts_from_body(bad) is None\n"
        ),
    ),
    (
        "not-established 的 sentinel 被換成已成立的依據（繞過閘門的另一條路）",
        "wf_cli/review.py",
        "PREFLIGHT_NOT_ESTABLISHED = PreflightBasis()",
        'PREFLIGHT_NOT_ESTABLISHED = PreflightBasis(basis="event-verified", source_event="x")',
        (
            "from wf_cli.review import PREFLIGHT_NOT_ESTABLISHED\n"
            "assert PREFLIGHT_NOT_ESTABLISHED.established is False\n"
        ),
    ),
    (
        "推導在無依據時回傳值而不是拒絕（防禦縱深被拆掉）",
        "wf_cli/review.py",
        "    if preflight is None or not preflight.established:\n        raise ValueError(",
        "    if False:\n        raise ValueError(",
        (
            "r = report()\n"
            "raises(ValueError, lambda: derive_counts_toward_escalation(r, marks(r.findings)))\n"
        ),
    ),
    (
        "渲染器在無依據時照常斷言帳（防禦縱深被拆掉）",
        "wf_cli/review.py",
        "    if asserted and counts_toward_escalation is None:",
        "    if False:",
        (
            "r = report()\n"
            "raises(ValueError, lambda: render_escalation_facts_block(\n"
            "    attempt='C-e0-' + SHA, escalation_epoch=0, report=r,\n"
            "    marks=marks(r.findings), counts_toward_escalation=None,\n"
            "    preflight=PreflightBasis(basis='event-verified', source_event='u')))\n"
        ),
    ),
    (
        "移除 event-verified 對來源事件的要求（回到「打字即依據」）",
        "wf_cli/review.py",
        'return self.basis == "event-verified" and bool(self.source_event.strip())',
        'return self.basis == "event-verified"',
        'assert PreflightBasis(basis="event-verified").established is False\n',
    ),
    (
        "把 writer-attested 放回合法 basis 列舉",
        "wf_cli/review.py",
        'PREFLIGHT_BASES = ("event-verified", "not-established")',
        'PREFLIGHT_BASES = ("event-verified", "writer-attested", "not-established")',
        'assert "writer-attested" not in PREFLIGHT_BASES\n',
    ),
]
# ⚠️ 移除了三條錨定在 `preflight_basis_from_body` 的突變（不比對 source_sha／card_id／
# preflight_passed）。**該讀取器本輪已刪除**，錨點不存在的突變會被 harness 判 SKIP，而
# 「錨點失效的突變等於沒測」（R2 那輪的 M04 已踩過一次）。取代它們的是上方錨在兩個導出器、
# 綁定值、以及「未斷言 vs 已判定不計數」上的突變，加上
# `test_no_source_path_constructs_an_event_verified_basis` 的 AST 窮舉——後者擋的正是
# 「讀取器換個名字重新長出來」。


@pytest.mark.parametrize("name, rel, old, new, probe", _MUTANTS, ids=[m[0] for m in _MUTANTS])
def test_fail_closed_predicate_dies_when_mutated(name, rel, old, new, probe):
    """基線必須先綠，突變後必須紅——否則 KILLED 判定無效。"""
    baseline = _run_probe(probe, None)
    assert baseline.returncode == 0, f"基線探針就不過，KILLED 判定無效：{baseline.stderr}"
    mutated = _run_probe(probe, (rel, old, new))
    assert mutated.returncode != 0, f"突變存活（缺一個「拿掉它就綠不了」的判準）：{name}"
