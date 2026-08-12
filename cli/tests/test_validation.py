from __future__ import annotations

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
    BLOCK_VERSION,
    CHECKPOINT_BLOCK_KEY,
    CHECKPOINT_LOG_TAG,
    PREFLIGHT_BASES,
    PREFLIGHT_BLOCK_KEY,
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
    find_block_by_key,
    log_line_indexes,
    preflight_basis_from_body,
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
    check_preflight_event_present,
    counted_attempts,
    derive_accepted_marking_binding,
    find_preflight_basis,
    validate_accepted_overrides,
    validate_checkpoint_input,
    validate_marked_by,
)

SHA_A, SHA_B, SHA_C = "a" * 40, "b" * 40, "c" * 40

# §3 第 1 款唯一合法的依據形狀：事件流上受管轄的 preflight pass event。
# **本 CLI 沒有任何路徑能產出它**（R2-01 的處置：移除「寫入者具結」那一支）；這裡直接
# 建構，是為了測「一旦承接卡讓它存在，整條鏈就會計數」。
def _preflight_body(card_id: str, sha: str) -> str:
    return "\n".join(
        [
            "```yaml",
            f"{PREFLIGHT_BLOCK_KEY}: {BLOCK_VERSION}",
            f"card_id: {card_id}",
            f"source_sha: {sha}",
            "preflight_passed: true",
            'summary: "全綠"',
            "```",
        ]
    )


EVENT_VERIFIED = preflight_basis_from_body(
    _preflight_body("CARD-A", SHA_A), card_id="CARD-A", source_sha=SHA_A
)

# 事件 marker 前綴刻意拆開書寫：只要有一則 GitHub 留言含它的字面，整張卡的自動裁決
# 判定就會被永久隔離（docs/CONSUMER_CONFORMANCE.md 記錄 #15／#17／#21 三張卡的實測）。
# 測試檔本身不是留言，但保持同一紀律可讓「交回前 grep 新增 0 處」成為機械可查的動作。
_MARKER_V1 = "wf-review-" + "event:v1"


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
    """review-escalation.md:276 的 cutover 語意：baseline 之前一律未知。"""
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

    card_body = _log() + f"\n- 2026-08-12 checkpoint by wf-cli → trigger {trigger}。"
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


# ---- §3 第 1 款：preflight event（R1／R2／R3 同一根因的第三次修正） ----


def test_preflight_basis_has_no_writer_attested_option_any_more():
    assert PREFLIGHT_BASES == ("event-verified", "not-established")
    assert PreflightBasis().established is False
    assert PreflightBasis(basis="event-verified").established is False


def test_preflight_reader_requires_all_four_facts_verbatim():
    """四項缺一即 None：版本、preflight_passed=true、同卡、同 SHA。"""
    ok = preflight_basis_from_body(
        _preflight_body("CARD-A", SHA_A), card_id="CARD-A", source_sha=SHA_A
    )
    assert ok is not None and ok.established

    # 他卡的 preflight 不算。
    assert (
        preflight_basis_from_body(
            _preflight_body("OTHER", SHA_A), card_id="CARD-A", source_sha=SHA_A
        )
        is None
    )
    # 別輪的 preflight 不算——source_sha 逐字比對即免時鐘的新鮮性（同 §4 (b′-2)）。
    assert (
        preflight_basis_from_body(
            _preflight_body("CARD-A", SHA_B), card_id="CARD-A", source_sha=SHA_A
        )
        is None
    )
    # preflight_passed 不是 true 就不算。
    failed = _preflight_body("CARD-A", SHA_A).replace(
        "preflight_passed: true", "preflight_passed: false"
    )
    assert preflight_basis_from_body(failed, card_id="CARD-A", source_sha=SHA_A) is None
    # 沒有區塊的留言不算。
    assert preflight_basis_from_body("一般留言", card_id="CARD-A", source_sha=SHA_A) is None


def test_missing_preflight_event_refuses_to_create_a_review_event():
    """R3-01：缺依據時**不建立 review event**，不是寫一個較誠實的值進去。"""
    with pytest.raises(ValidationError) as exc_info:
        check_preflight_event_present(PreflightBasis(), source_sha=SHA_A)
    message = "；".join(exc_info.value.errors)
    assert "不建立 review event" in message
    assert "不得以 unknown／unavailable 之類的新值擴充該布林欄位" in message
    assert "--validate-only" in message  # 指出仍可用的自檢路徑
    check_preflight_event_present(EVENT_VERIFIED, source_sha=SHA_A)  # 有依據就放行


def test_find_preflight_basis_scans_the_timeline():
    comments = [
        {"body": "無關留言", "url": "u0"},
        {"body": _preflight_body("CARD-A", SHA_A), "url": "u1"},
    ]
    basis = find_preflight_basis(comments, card_id="CARD-A", source_sha=SHA_A)
    assert basis.established and basis.source_event == "u1"
    assert not find_preflight_basis(comments, card_id="CARD-A", source_sha=SHA_B).established


def test_counts_derivation_refuses_to_run_without_an_established_basis():
    """防禦縱深：呼叫端漏擋時，推導本身也不得回傳一個值。"""
    report = _report(findings=[_finding()])
    marks = default_accepted_marks(report.findings)
    with pytest.raises(ValueError):
        derive_counts_toward_escalation(report, marks)
    with pytest.raises(ValueError):
        derive_counts_toward_escalation(report, marks, PreflightBasis())
    assert derive_counts_toward_escalation(report, marks, EVENT_VERIFIED) is True


def test_renderer_refuses_to_emit_an_event_without_a_preflight_basis():
    report = _report(findings=[_finding()])
    with pytest.raises(ValueError):
        render_escalation_facts_block(
            attempt=f"CARD-A-e0-{SHA_A}",
            escalation_epoch=0,
            report=report,
            marks=default_accepted_marks(report.findings),
            counts_toward_escalation=True,
        )


def test_written_block_asserts_preflight_passed_true_as_a_literal():
    """§5:168 把該欄釘為字面 true；寫出來的事件必須逐字如此。"""
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
    BLOCK_VERSION, PREFLIGHT_BASES, PREFLIGHT_BLOCK_KEY, AcceptedMark, Finding,
    PreflightBasis, ReviewReport, SelfRunEntry, derive_counts_toward_escalation,
    preflight_basis_from_body, render_escalation_facts_block,
)
from wf_cli.validation import (
    ValidationError, build_issue_event_history, check_preflight_event_present,
)

SHA = "a" * 40
OTHER = "b" * 40

def pf_body(card="C", sha=SHA, passed="true"):
    return chr(10).join([
        "```yaml",
        PREFLIGHT_BLOCK_KEY + ": " + BLOCK_VERSION,
        "card_id: " + card,
        "source_sha: " + sha,
        "preflight_passed: " + passed,
        "```",
    ])

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
        "寫入前的閘門變成 no-op（缺依據仍建立 review event）",
        "wf_cli/validation.py",
        "    if basis.established:\n        return",
        "    return",
        (
            "raises(ValidationError, lambda: check_preflight_event_present(\n"
            "    PreflightBasis(), source_sha=SHA))\n"
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
        "渲染器在無依據時照常產出 review event",
        "wf_cli/review.py",
        "    if not attestation.established:",
        "    if False:",
        (
            "r = report()\n"
            "raises(ValueError, lambda: render_escalation_facts_block(\n"
            "    attempt='C-e0-' + SHA, escalation_epoch=0, report=r,\n"
            "    marks=marks(r.findings), counts_toward_escalation=True))\n"
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
    (
        "preflight 讀取器不比對 source_sha（上一輪的 preflight 可掩護本輪）",
        "wf_cli/review.py",
        '    if str(data.get("source_sha") or "").strip() != source_sha:\n        return None',
        "    pass",
        (
            "assert preflight_basis_from_body(pf_body(sha=OTHER),\n"
            "    card_id='C', source_sha=SHA) is None\n"
        ),
    ),
    (
        "preflight 讀取器不比對 card_id（他卡的 preflight 可借用）",
        "wf_cli/review.py",
        '    if str(data.get("card_id") or "").strip() != card_id:\n        return None',
        "    pass",
        (
            "assert preflight_basis_from_body(pf_body(card='OTHER'),\n"
            "    card_id='C', source_sha=SHA) is None\n"
        ),
    ),
    (
        "preflight 讀取器接受 preflight_passed: false",
        "wf_cli/review.py",
        '    if str(data.get("preflight_passed") or "").strip() != "true":\n        return None',
        "    pass",
        (
            "assert preflight_basis_from_body(pf_body(passed='false'),\n"
            "    card_id='C', source_sha=SHA) is None\n"
        ),
    ),
]


@pytest.mark.parametrize("name, rel, old, new, probe", _MUTANTS, ids=[m[0] for m in _MUTANTS])
def test_fail_closed_predicate_dies_when_mutated(name, rel, old, new, probe):
    """基線必須先綠，突變後必須紅——否則 KILLED 判定無效。"""
    baseline = _run_probe(probe, None)
    assert baseline.returncode == 0, f"基線探針就不過，KILLED 判定無效：{baseline.stderr}"
    mutated = _run_probe(probe, (rel, old, new))
    assert mutated.returncode != 0, f"突變存活（缺一個「拿掉它就綠不了」的判準）：{name}"
