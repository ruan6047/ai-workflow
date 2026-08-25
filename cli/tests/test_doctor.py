from __future__ import annotations

import pytest

import shutil
from pathlib import Path

from wf_cli.doctor import (
    ANCHOR_BLOCK,
    ANCHOR_FLOOR,
    ANCHOR_MERGE,
    CANONICAL_ANCHORS,
    CANONICAL_SECTION,
    CANONICAL_SECTION_HEADING,
    COMMIT_TRAILER_ROOT_CAUSE_ID,
    LEGACY_AUTHORITY_NOTE_EXPLANATION,
    LEGACY_AUTHORITY_NOTE_MARKER,
    SUPERSEDED_ROOT_CAUSE_IDS,
    TRAILER_GUARD_EPOCH,
    CommitRecord,
    DoctorReport,
    audit_commit_trailers,
    audit_legacy_authority_notes,
    audit_review_channel,
    canonical_cite,
    classify_commit_shape,
    evaluate_commit_trailers,
    find_legacy_authority_notes,
    required_trailers,
    run_doctor,
    severed_declared_keys,
)
from wf_cli.registry import RegisteredCard, TasksMdRegistry
from wf_cli.review import render_verdict_comment
from wf_cli.validation import validate_review_report

from .conftest import SANDBOX_COMMIT_DATE, fixed_date_env, git

_APPROVED = "✅通過"


def _audit_three_faces(*args, **kwargs):
    """三面一致的正常情境：Project 交付狀態與 APPROVE 裁決相符。

    這些測試驗的是「裁決確實成立」，因此 fixture 必須包含第三面；沒有它，
    audit_review_channel 依契約 §3.1.3 不得宣稱 recorded。
    """
    kwargs.setdefault("delivery_status", _APPROVED)
    return audit_review_channel(*args, **kwargs)



def _registry(active: list[RegisteredCard], archived: set[str] | None = None) -> TasksMdRegistry:
    return TasksMdRegistry(active=active, archived_card_ids=archived or set(), source_paths=[])


def test_worktree_classification_registered_orphan_prunable_and_detached(sandbox_repo, tmp_path):
    # 已註冊的活卡 worktree
    git(sandbox_repo, "branch", "ai/agent/CARD-A")
    wt_registered = tmp_path / "wt-registered"
    git(sandbox_repo, "worktree", "add", str(wt_registered), "ai/agent/CARD-A")

    # 從未被任何卡註冊過的孤兒 worktree
    git(sandbox_repo, "branch", "claude/some-orphan-abc123")
    wt_orphan = tmp_path / "wt-orphan"
    git(sandbox_repo, "worktree", "add", str(wt_orphan), "claude/some-orphan-abc123")

    # prunable：worktree 目錄被直接刪掉、沒有走 `git worktree remove`
    wt_prunable = tmp_path / "wt-prunable"
    git(sandbox_repo, "worktree", "add", "--detach", str(wt_prunable))
    shutil.rmtree(wt_prunable)

    # detached、非 prunable 的查核沙箱（worktree-lifecycle.md 認可的合法型態）
    wt_review = tmp_path / "wt-review-sandbox"
    git(sandbox_repo, "worktree", "add", "--detach", str(wt_review))

    registry = _registry(
        [
            RegisteredCard(
                card_id="CARD-A", branch="ai/agent/CARD-A", worktree_path="wt-registered",
                delivery_status="🔨執行中", owner="someone", last_handoff=None,
            )
        ]
    )
    report = run_doctor(sandbox_repo, registry)

    by_path = {Path(w.path).name: w for w in report.worktrees}
    assert by_path["wt-registered"].classification == "registered_active"
    assert by_path["wt-registered"].card_id == "CARD-A"
    assert by_path["wt-orphan"].classification == "orphan_untracked"
    assert by_path["wt-prunable"].classification == "orphan_prunable"
    assert by_path["wt-review-sandbox"].classification == "detached_sandbox"

    orphan_paths = {Path(w.path).name for w in report.orphan_worktrees()}
    assert orphan_paths == {"wt-orphan", "wt-prunable"}
    assert "wt-review-sandbox" not in orphan_paths  # detached 但非 prunable 不算孤兒


def test_main_worktree_itself_is_excluded_from_findings(sandbox_repo):
    report = run_doctor(sandbox_repo, _registry([]))
    assert report.worktrees == []


def test_submodule_uninitialized_is_flagged(sandbox_repo, tmp_path):
    other_repo = tmp_path / "other-repo"
    other_repo.mkdir()
    git(other_repo, "init", "-q", "-b", "main")
    git(other_repo, "config", "user.email", "test@example.com")
    git(other_repo, "config", "user.name", "wf-cli tests")
    (other_repo / "f.txt").write_text("x\n")
    git(other_repo, "add", "f.txt")
    git(other_repo, "commit", "-q", "-m", "init")

    git(
        sandbox_repo, "-c", "protocol.file.allow=always",
        "submodule", "add", str(other_repo), "vendor/other",
    )
    git(sandbox_repo, "commit", "-q", "-m", "add submodule")
    git(sandbox_repo, "submodule", "deinit", "-f", "vendor/other")

    report = run_doctor(sandbox_repo, _registry([]))
    assert len(report.submodules) == 1
    assert report.submodules[0].status == "uninitialized"
    assert report.submodules[0].path == "vendor/other"


def test_orphan_branch_detected_when_no_worktree_and_not_registered(sandbox_repo):
    git(sandbox_repo, "branch", "claude/dangling-branch-xyz")
    report = run_doctor(sandbox_repo, _registry([]))
    names = {b.branch for b in report.orphan_branches}
    assert "claude/dangling-branch-xyz" in names
    finding = next(b for b in report.orphan_branches if b.branch == "claude/dangling-branch-xyz")
    assert finding.merged_into_main is True  # branch 建立自 main tip，尚未額外 commit


def test_branch_with_worktree_is_not_double_reported_as_orphan_branch(sandbox_repo, tmp_path):
    git(sandbox_repo, "branch", "ai/agent/CARD-A")
    git(sandbox_repo, "worktree", "add", str(tmp_path / "wt-a"), "ai/agent/CARD-A")
    report = run_doctor(sandbox_repo, _registry([]))
    assert "ai/agent/CARD-A" not in {b.branch for b in report.orphan_branches}


def test_registered_branch_without_worktree_is_not_orphan_branch(sandbox_repo):
    git(sandbox_repo, "branch", "ai/agent/CARD-B")
    registry = _registry(
        [
            RegisteredCard(
                card_id="CARD-B", branch="ai/agent/CARD-B", worktree_path=None,
                delivery_status="📥Backlog", owner="待指派", last_handoff=None,
            )
        ]
    )
    report = run_doctor(sandbox_repo, registry)
    assert "ai/agent/CARD-B" not in {b.branch for b in report.orphan_branches}


def test_stale_lease_flagged_when_registered_worktree_path_missing_on_disk(sandbox_repo):
    registry = _registry(
        [
            RegisteredCard(
                card_id="CARD-GONE", branch="ai/agent/CARD-GONE",
                worktree_path=".claude/worktrees/does-not-exist",
                delivery_status="🔨執行中", owner="Claude Sonnet 5@Claude Code",
                last_handoff=None,
            )
        ]
    )
    report = run_doctor(sandbox_repo, registry)
    assert len(report.stale_leases) == 1
    assert report.stale_leases[0].card_id == "CARD-GONE"
    assert "不存在" in report.stale_leases[0].reason


def test_stale_lease_not_flagged_for_unassigned_owner(sandbox_repo):
    registry = _registry(
        [
            RegisteredCard(
                card_id="CARD-BACKLOG", branch=None, worktree_path=None,
                delivery_status="📥Backlog", owner="待指派", last_handoff=None,
            )
        ]
    )
    report = run_doctor(sandbox_repo, registry)
    assert report.stale_leases == []


def test_stale_lease_flagged_when_last_handoff_exceeds_ttl(sandbox_repo):
    registry = _registry(
        [
            RegisteredCard(
                card_id="CARD-OLD", branch=None, worktree_path=None,
                delivery_status="🔨執行中", owner="Claude Opus 5@Claude Code",
                last_handoff="2020-01-01T00:00:00+08:00",
            )
        ]
    )
    report = run_doctor(sandbox_repo, registry, lease_ttl_hours=48.0)
    assert len(report.stale_leases) == 1
    assert report.stale_leases[0].age_hours is not None
    assert report.stale_leases[0].age_hours > 48.0


def test_render_text_produces_readable_summary(sandbox_repo):
    report = run_doctor(sandbox_repo, _registry([]))
    text = report.render_text()
    assert "doctor 對帳報告" in text
    assert "摘要" in text


def test_review_channel_marks_receipt_without_state_event_as_untranscribed():
    sha = "a" * 40
    finding = audit_review_channel(
        [{
            "body": "<!-- wf-review-receipt:v1\ncard_id: CARD-A\nsource_sha: " + sha
            + "\nreport_sha256: " + "b" * 64 + "\n-->",
            "html_url": "https://github.com/acme/demo/issues/9#issuecomment-1",
            "user": {"login": "copilot-reviewer"},
        }],
        "CARD-A", sha,
    )
    assert finding.status == "receipt_untranscribed"
    assert finding.receipt_urls == ("https://github.com/acme/demo/issues/9#issuecomment-1",)
    assert finding.receipt_authors == ("copilot-reviewer",)


def test_review_channel_requires_receipt_or_event_but_does_not_claim_review_absent():
    finding = audit_review_channel([], "CARD-A", "a" * 40)
    assert finding.status == "unobservable"
    assert "不證明查核未發生" in finding.detail


def test_review_channel_accepts_renderer_event_only_with_matching_issue_log():
    sha = "a" * 40
    report = validate_review_report({
        "review_result": "APPROVE", "core_pain_resolved": "yes",
        "self_run": [{"command": "pytest", "observed": "1 passed"}], "findings": [],
    })
    body = render_verdict_comment(
        card_id="CARD-A", report=report, source_sha=sha, reviewer="reviewer",
        escalation_epoch=0, timestamp="2026-08-09T00:00:00+08:00",
    )
    finding = _audit_three_faces(
        [{"body": body}], "CARD-A", sha,
        card_body=f"2026-08-09 review by wf-cli → APPROVE；attempt CARD-A-e0-{sha}。",
    )
    assert finding.status == "recorded"


def test_review_channel_rejects_copied_event_or_event_from_another_card():
    sha = "a" * 40
    copied = f"## 查核裁決：APPROVE\n- 卡：`OTHER` attempt_id：`OTHER-e0-{sha}`"
    finding = audit_review_channel(
        [{"body": copied}], "CARD-A", sha,
        card_body=f"2026-08-09 review by wf-cli → APPROVE；attempt CARD-A-e0-{sha}。",
    )
    assert finding.status == "unobservable"


def test_review_channel_reads_receipt_from_pr_review_body():
    sha = "a" * 40
    finding = audit_review_channel(
        [], "CARD-A", sha,
        reviews=[{
            "body": "<!-- wf-review-receipt:v1\ncard_id: CARD-A\nsource_sha: " + sha + "\n-->",
            "html_url": "https://github.com/acme/demo/pull/9#pullrequestreview-1",
            "user": {"login": "copilot-reviewer"},
        }],
    )
    assert finding.status == "receipt_untranscribed"
    assert finding.receipt_authors == ("copilot-reviewer",)


# --------------------------------------------------------------------------
# WF-REVIEW-EVENT-MARKER-ENFORCE1：marker 合規的 fail-closed
#
# handoff-contract.md §3.1.3／§3.1.4 自 2026-08-10 起要求：受管轄但不合格的 marker
# 必須讓該卡停止自動裁決判定，不得回退 legacy。先前實作對五種不合格 marker 全數
# 回傳 recorded——契約寫著 fail-closed、消費者實際 fail-open。
# --------------------------------------------------------------------------

_ESHA = "a" * 40
_ECARD = "CARD-A"
_EATT = f"{_ECARD}-e0-{_ESHA}"
_ELOG = f"2026-08-09 review by wf-cli → APPROVE；attempt {_EATT}。"


def _conformant_marker(card: str = _ECARD, sha: str = _ESHA, attempt: str | None = None) -> str:
    att = attempt if attempt is not None else f"{card}-e0-{sha}"
    return f"<!-- wf-review-event:v1 card_id={card} source_sha={sha} attempt_id={att} -->"


def _verdict(marker: str) -> str:
    """帶 marker 的裁決留言；散文部分足以讓 legacy 分支也會命中（正是要證明它不再命中）。"""
    return f"{marker}\n## 查核裁決：APPROVE\n- attempt_id：`{_EATT}`"


@pytest.mark.parametrize(
    "name,marker",
    [
        ("unknown-version", f"<!-- wf-review-event:v2 card_id={_ECARD} source_sha={_ESHA} attempt_id={_EATT} -->"),
        ("missing-field", f"<!-- wf-review-event:v1 card_id={_ECARD} source_sha={_ESHA} -->"),
        ("unknown-key", f"<!-- wf-review-event:v1 card_id={_ECARD} source_sha={_ESHA} attempt_id={_EATT} verdict=APPROVE -->"),
        ("field-order", f"<!-- wf-review-event:v1 source_sha={_ESHA} card_id={_ECARD} attempt_id={_EATT} -->"),
        ("field-inconsistent", _conformant_marker(attempt=f"OTHER-e0-{_ESHA}")),
    ],
)
def test_nonconformant_marker_quarantines_instead_of_recorded(name, marker):
    finding = audit_review_channel([{"body": _verdict(marker)}], _ECARD, _ESHA, card_body=_ELOG)
    assert finding.status == "marker_quarantined", f"{name} 仍被判為 {finding.status}"
    assert finding.quarantine_reasons, "停機必須說明是哪一則、為什麼"


def test_quarantine_is_distinct_from_unobservable():
    """「找到訊號但讀不懂」與「找不到訊號」對人的指示完全不同，不得併態。"""
    bad = audit_review_channel(
        [{"body": _verdict(f"<!-- wf-review-event:v2 card_id={_ECARD} source_sha={_ESHA} attempt_id={_EATT} -->")}],
        _ECARD, _ESHA, card_body=_ELOG,
    )
    none = audit_review_channel([], _ECARD, _ESHA, card_body=_ELOG)
    assert bad.status == "marker_quarantined"
    assert none.status == "unobservable"


def test_conformant_marker_still_recorded():
    finding = _audit_three_faces([{"body": _verdict(_conformant_marker())}], _ECARD, _ESHA, card_body=_ELOG)
    assert finding.status == "recorded"


def test_legacy_event_without_prefix_is_unchanged():
    """legacy 判準是語法：完全不含 wf-review-event: 前綴者行為完全不變。"""
    legacy = f"## 查核裁決：APPROVE\n- 卡：`{_ECARD}`　attempt_id：`{_EATT}`"
    assert "wf-review-event:" not in legacy
    finding = _audit_three_faces([{"body": legacy}], _ECARD, _ESHA, card_body=_ELOG)
    assert finding.status == "recorded"


def test_duplicate_events_for_same_attempt_quarantine():
    """落差 8a：可驗證語意等價的機制到位前，重送不得被推定為安全。"""
    marker = _conformant_marker()
    finding = audit_review_channel(
        [{"body": _verdict(marker)}, {"body": _verdict(marker)}], _ECARD, _ESHA, card_body=_ELOG
    )
    assert finding.status == "marker_quarantined"
    assert any("同一 attempt_id 出現 2 則" in r for r in finding.quarantine_reasons)


def test_conformant_marker_for_another_card_does_not_quarantine_this_one():
    """別卡的合法 marker 不是本卡的事件，也不該讓本卡停機。"""
    other = _verdict(_conformant_marker(card="OTHER-CARD"))
    finding = audit_review_channel([{"body": other}], _ECARD, _ESHA, card_body=_ELOG)
    assert finding.status == "unobservable"


def test_prefix_quoted_in_prose_quarantines_conservatively():
    """契約明文承認的保守誤判：內文引用該字樣會被判為受管轄。方向是 fail-closed。"""
    prose = "討論：`wf-review-event:v1` 的三欄自洽規則是否過嚴？"
    finding = audit_review_channel([{"body": prose}], _ECARD, _ESHA, card_body=_ELOG)
    assert finding.status == "marker_quarantined"


def test_receipt_still_detected_when_no_governed_marker():
    receipt = f"<!-- wf-review-receipt:v1\ncard_id: {_ECARD}\nsource_sha: {_ESHA}\n-->"
    finding = audit_review_channel([{"body": receipt, "html_url": "u", "user": {"login": "x"}}], _ECARD, _ESHA)
    assert finding.status == "receipt_untranscribed"


# --------------------------------------------------------------------------
# 執行者自我對抗測試：marker 必須「恰為首行」
#
# 先前版本掃描所有行找 marker，造成三種 fail-open：埋在散文之後仍被採信、前導
# 空白仍被採信，以及最嚴重的——包在 code fence 裡的示範 marker 被當成真事件。
# 契約 §3.1.3 明寫「marker 置於留言首行」，示範與引用必須落在 fail-closed 那側。
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name,body",
    [
        ("buried-after-prose", f"閒聊一句\n再一句\n{_conformant_marker()}\n## 查核裁決：APPROVE"),
        ("leading-whitespace", f"  {_conformant_marker()}\n## 查核裁決：APPROVE"),
        ("two-markers-one-comment", f"{_conformant_marker()}\n{_conformant_marker()}\n## 查核裁決：APPROVE"),
        ("inside-code-fence", f"```text\n{_conformant_marker()}\n```\n這只是範例"),
        ("prefix-quoted-in-verdict-prose",
         f"{_conformant_marker()}\n## 查核裁決：APPROVE\n備註：`wf-review-event:v1` 的三欄自洽規則"),
    ],
)
def test_marker_must_be_exactly_the_first_line(name, body):
    finding = audit_review_channel([{"body": body}], _ECARD, _ESHA, card_body=_ELOG)
    assert finding.status == "marker_quarantined", f"{name} 被判為 {finding.status}（fail-open）"


def test_uppercase_sha_in_marker_is_not_conformant():
    """契約規定 source_sha 為完整 40 字元小寫 hex。"""
    marker = _conformant_marker().replace(_ESHA, _ESHA.upper())
    finding = audit_review_channel([{"body": _verdict(marker)}], _ECARD, _ESHA, card_body=_ELOG)
    assert finding.status == "marker_quarantined"


def test_same_sha_different_epoch_is_a_separate_attempt_not_a_duplicate():
    """同 SHA 在 replan 後重審屬不同 attempt，不是重複事件，不得停機。"""
    att = f"{_ECARD}-e1-{_ESHA}"
    marker = _conformant_marker(attempt=att)
    log = f"2026-08-09 review by wf-cli → APPROVE；attempt {att}。"
    finding = _audit_three_faces([{"body": _verdict(marker)}], _ECARD, _ESHA, card_body=log)
    assert finding.status == "recorded"


def test_log_must_index_the_same_attempt_as_the_event():
    """§3.1.3 三面一致要求 Log 索引的是**同一 attempt_id**。

    先前實作把它拆成兩個獨立全文檢查，於是 Log 索引 e0 也能讓 e1 的事件過關。
    """
    marker = _conformant_marker(attempt=f"{_ECARD}-e1-{_ESHA}")
    # 帶第三面，否則斷言會因「第三面未提供」而成立，測不到 Log 索引規則本身。
    finding = audit_review_channel(
        [{"body": _verdict(marker)}], _ECARD, _ESHA, card_body=_ELOG, delivery_status="✅通過"
    )
    assert finding.status != "recorded", "Log 索引的是 e0，不得讓 e1 的事件過關"


def test_log_index_conditions_must_be_on_the_same_line():
    """v1 事件：attempt 在 assign 行、review by wf-cli 在另一行，不構成索引。

    此要求**只施加於宣告受管轄的 v1 事件**；legacy 維持基線的全文各自搜尋
    （見 test_legacy_log_may_span_lines_as_in_baseline），否則就是回歸。
    """
    split_log = (
        f"## Log\n- assign by wf-cli；attempt {_EATT}。\n- review by wf-cli → 別的事。"
    )
    finding = audit_review_channel(
        [{"body": _verdict(_conformant_marker())}], _ECARD, _ESHA,
        card_body=split_log, delivery_status="✅通過",
    )
    assert finding.status != "recorded"


def test_receipt_card_id_must_match_exactly_not_by_prefix():
    """`"card_id: CARD-A" in "card_id: CARD-AB"` 為真——子字串比對會認錯收據。"""
    other = f"<!-- wf-review-receipt:v1\ncard_id: {_ECARD}B\nsource_sha: {_ESHA}\n-->"
    finding = audit_review_channel(
        [{"body": other, "html_url": "u", "user": {"login": "x"}}], _ECARD, _ESHA
    )
    assert finding.status == "unobservable", "別卡的收據不得被算成本卡的"


def test_json_payload_exposes_review_channel_finding():
    """停機必須出現在機器可讀輸出，否則 #16 的對帳讀不到它。"""
    from wf_cli.commands.doctor_cmd import build_json_payload

    report = DoctorReport(repo_root=".", generated_at="t", registry_sources=[])
    finding = audit_review_channel(
        [{"body": _verdict(f"<!-- wf-review-event:v2 card_id={_ECARD} source_sha={_ESHA} attempt_id={_EATT} -->")}],
        _ECARD, _ESHA, card_body=_ELOG,
    )
    payload = build_json_payload(report, finding)
    assert payload["review_channel"]["status"] == "marker_quarantined"
    assert payload["review_channel"]["quarantine_reasons"], "停機原因也必須可機器讀取"
    # 既有欄位不得被影響
    assert "worktrees" in payload and "stale_leases" in payload


def test_json_payload_review_channel_is_null_when_not_requested():
    from wf_cli.commands.doctor_cmd import build_json_payload

    report = DoctorReport(repo_root=".", generated_at="t", registry_sources=[])
    assert build_json_payload(report, None)["review_channel"] is None


@pytest.mark.parametrize("where", ["comments", "reviews"])
def test_quarantine_detected_in_both_comment_and_pr_review_bodies(where):
    """PR review body 與 Issue comment 走同一條判定，兩邊都要停機。"""
    bad = _verdict(f"<!-- wf-review-event:v2 card_id={_ECARD} source_sha={_ESHA} attempt_id={_EATT} -->")
    kwargs = {"card_body": _ELOG}
    args = ([{"body": bad}], _ECARD, _ESHA) if where == "comments" else ([], _ECARD, _ESHA)
    if where == "reviews":
        kwargs["reviews"] = [{"body": bad}]
    assert audit_review_channel(*args, **kwargs).status == "marker_quarantined"


@pytest.mark.parametrize(
    "bad_sha", ["abc123", "A" * 40, "", "z" * 40, "a" * 39, "a" * 41]
)
def test_doctor_rejects_invalid_source_sha_instead_of_reporting_unobservable(bad_sha, tmp_path, capsys):
    """無效 source_sha 必須當場拒絕，不得走到底回報 `unobservable`。

    `unobservable` 的語意是「該 source_sha 的查核在系統上不可觀測」。對打錯的輸入
    回這個狀態，等於拿確定的結論回答一個沒被評估的問題；加上 --strict 還會讓 CI 紅
    在「沒人查核」而不是「SHA 打錯了」。handoff／review 都驗格式，doctor 先前沒驗。
    """
    import argparse

    from wf_cli.commands import doctor_cmd

    args = argparse.Namespace(
        repo_root=str(tmp_path), registry="none", review_channel=True,
        repo="acme/x", issue_number=1, card_id="CARD-A", source_sha=bad_sha,
        owner="acme", project=1,
        conformance=False,
        commit_trailers=False, commit_range=None,
        trailer_epoch=TRAILER_GUARD_EPOCH, require_planned_by=False,
        main_ref="main", lease_ttl_hours=48.0, json=False, strict=False,
    )
    assert doctor_cmd.run(args) == 2
    assert "source" in capsys.readouterr().err


def test_doctor_accepts_valid_source_sha_format():
    from wf_cli.validation import validate_source_sha

    validate_source_sha("a" * 40)  # 不得拋


# --------------------------------------------------------------------------
# R1 查核回歸
# --------------------------------------------------------------------------


def test_log_attempt_must_match_on_token_boundary_not_substring():
    """R1-001：`attempt in line` 會讓較長的不同 attempt 以前綴命中。

    同一個子字串陷阱先前已在收據比對上出現過一次，這裡是它在 Log 對帳的複發。
    """
    log = f"2026-08-09 review by wf-cli → APPROVE；attempt {_EATT}x。"
    # 必須帶 delivery_status：否則第三面未提供就會讓斷言因為別的原因成立，
    # 這個測試等於沒在驗 token 邊界（#20 加入第三面檢查後一度變成如此）。
    finding = audit_review_channel(
        [{"body": _verdict(_conformant_marker())}], _ECARD, _ESHA,
        card_body=log, delivery_status="✅通過",
    )
    assert finding.status != "recorded", "attempt+x 不是同一個 attempt"


def test_legacy_log_may_span_lines_as_in_baseline():
    """R1-002：卡面驗收第 3 條要求 legacy 判定行為與本卡前一致。

    基線接受「Log 中各自存在 review 與 attempt」，不要求同一行。把 legacy 一併
    收緊會讓既有舊卡由 recorded 變成 unobservable——那是回歸，不是修復。
    """
    legacy = f"## 查核裁決：APPROVE\n- 卡：`{_ECARD}`　attempt_id：`{_EATT}`"
    assert "wf-review-event:" not in legacy
    split_log = f"- review by wf-cli → APPROVE。\n- assign by wf-cli；attempt {_EATT}。"
    finding = _audit_three_faces([{"body": legacy}], _ECARD, _ESHA, card_body=split_log)
    assert finding.status == "recorded"


def test_json_mode_sends_human_report_to_stderr(tmp_path, capsys, monkeypatch):
    """R1-003：--json 的 stdout 必須是可直接解析的 JSON。

    先前人類可讀報告與 JSON 都印到 stdout，`| jq .` 直接 parse error，CI 與 #16
    因此拿不到 review_channel。
    """
    import argparse
    import json as jsonlib

    from wf_cli.commands import doctor_cmd
    from wf_cli.doctor import DoctorReport

    monkeypatch.setattr(
        doctor_cmd, "run_doctor",
        lambda *a, **k: DoctorReport(repo_root=str(tmp_path), generated_at="t", registry_sources=[]),
    )
    args = argparse.Namespace(
        repo_root=str(tmp_path), registry="none", review_channel=False,
        repo=None, issue_number=None, card_id=None, source_sha=None,
        owner=None, project=None, cleanup_preview=False,
        conformance=False,
        commit_trailers=False, commit_range=None,
        trailer_epoch=TRAILER_GUARD_EPOCH, require_planned_by=False,
        main_ref="main", lease_ttl_hours=48.0, json=True, strict=False,
    )
    assert doctor_cmd.run(args) == 0
    captured = capsys.readouterr()
    payload = jsonlib.loads(captured.out)          # stdout 必須整份可解析
    assert payload["review_channel"] is None
    assert "doctor 對帳報告" in captured.err        # 人類可讀報告改走 stderr


# --------------------------------------------------------------------------
# R2-001：混合 v1／legacy 歷史的優先序
#
# 兩條放行路徑先前以 OR 合併：v1 事件即使沒有合格的同行 Log 索引，只要同卡有同
# attempt 的 legacy 文字加上基線式分行 Log，就從寬鬆那條放行——等於用舊標準替新
# 標準的事件背書，v1 的兩面一致從未真正被要求。
# --------------------------------------------------------------------------


def _legacy_verdict(attempt: str) -> str:
    body = f"## 查核裁決：APPROVE\n- 卡：`{_ECARD}`　attempt_id：`{attempt}`"
    assert "wf-review-event:" not in body
    return body


def test_legacy_must_not_vouch_for_a_v1_event_of_the_same_attempt():
    """同 attempt 已有受管轄的 v1 事件時，legacy 的寬鬆對帳不得替它背書。"""
    split_log = f"- review by wf-cli → APPROVE。\n- assign by wf-cli；attempt {_EATT}。"
    finding = audit_review_channel(
        [{"body": _verdict(_conformant_marker())}, {"body": _legacy_verdict(_EATT)}],
        _ECARD, _ESHA, card_body=split_log, delivery_status="✅通過",
    )
    assert finding.status != "recorded", "v1 事件缺同行索引，不得由 legacy 路徑放行"


def test_legacy_still_vouches_for_its_own_attempt_when_no_v1_exists():
    """legacy 對「沒有 v1 對應」的 attempt 仍維持基線寬鬆對帳（驗收第 3 條）。"""
    other = f"{_ECARD}-e1-{_ESHA}"
    split_log = f"- review by wf-cli → APPROVE。\n- assign by wf-cli；attempt {other}。"
    finding = _audit_three_faces(
        [{"body": _legacy_verdict(other)}], _ECARD, _ESHA, card_body=split_log
    )
    assert finding.status == "recorded"


def test_v1_with_proper_same_line_log_is_recorded_even_alongside_legacy():
    """v1 自己有合格索引時照常放行，legacy 的存在不影響。"""
    log = f"- review by wf-cli → APPROVE；attempt {_EATT}。"
    finding = _audit_three_faces(
        [{"body": _verdict(_conformant_marker())}, {"body": _legacy_verdict(_EATT)}],
        _ECARD, _ESHA, card_body=log,
    )
    assert finding.status == "recorded"


def test_quarantine_still_surfaces_any_receipt_found():
    """停機與收據是兩件事，下一步動作也不同，不得因停機而吞掉收據。

    停機要人去修一則壞掉的留言；收據則說明「裁決其實發生過、只是還沒轉錄」。
    先前收據只在未停機時才收集，兩者並存時操作者完全看不到收據存在。
    """
    bad = _verdict(f"<!-- wf-review-event:v2 card_id={_ECARD} source_sha={_ESHA} attempt_id={_EATT} -->")
    receipt = f"<!-- wf-review-receipt:v1\ncard_id: {_ECARD}\nsource_sha: {_ESHA}\n-->"
    finding = audit_review_channel(
        [{"body": bad}, {"body": receipt, "html_url": "https://x/1", "user": {"login": "reviewer"}}],
        _ECARD, _ESHA, card_body=_ELOG,
    )
    assert finding.status == "marker_quarantined"
    assert finding.receipt_urls == ("https://x/1",)
    assert finding.receipt_authors == ("reviewer",)


def test_receipt_untranscribed_unaffected_by_the_earlier_collection():
    """收據改在第一輪收集後，未停機時的行為必須完全不變。"""
    receipt = f"<!-- wf-review-receipt:v1\ncard_id: {_ECARD}\nsource_sha: {_ESHA}\n-->"
    finding = audit_review_channel(
        [{"body": receipt, "html_url": "https://x/2", "user": {"login": "r2"}}], _ECARD, _ESHA
    )
    assert finding.status == "receipt_untranscribed"
    assert finding.receipt_urls == ("https://x/2",)


# --------------------------------------------------------------------------
# WF-REVIEW-CHANNEL-THIRD-FACE1：三面一致的第三面（Project 交付狀態欄）
#
# 契約 §3.1.3 要求裁決成立需三面一致。先前只驗留言與 Log 兩面，於是 wfcli review
# 三次無交易性遠端寫入中「留言成功、狀態欄失敗」的半寫入，看起來與正常裁決一模一樣。
# --------------------------------------------------------------------------


def test_three_faces_agree_is_recorded():
    finding = audit_review_channel(
        [{"body": _verdict(_conformant_marker())}], _ECARD, _ESHA,
        card_body=_ELOG, delivery_status="✅通過",
    )
    assert finding.status == "recorded"
    assert finding.expected_delivery_status == "✅通過"
    assert finding.actual_delivery_status == "✅通過"


def test_status_field_mismatch_is_half_written():
    """留言與 Log 都在、狀態欄仍停在待查核＝半寫入，不得判 recorded。"""
    finding = audit_review_channel(
        [{"body": _verdict(_conformant_marker())}], _ECARD, _ESHA,
        card_body=_ELOG, delivery_status="🔍待查核",
    )
    assert finding.status == "half_written"
    assert finding.expected_delivery_status == "✅通過"
    assert finding.actual_delivery_status == "🔍待查核"
    assert "半寫入" in finding.detail


def test_request_changes_expects_returned_status():
    body = f"{_conformant_marker()}\n## 查核裁決：REQUEST_CHANGES\n- attempt_id：`{_EATT}`"
    ok = audit_review_channel([{"body": body}], _ECARD, _ESHA, card_body=_ELOG, delivery_status="↩退回")
    bad = audit_review_channel([{"body": body}], _ECARD, _ESHA, card_body=_ELOG, delivery_status="✅通過")
    assert ok.status == "recorded"
    assert bad.status == "half_written" and bad.expected_delivery_status == "↩退回"


def test_unreadable_status_field_must_not_claim_recorded():
    """讀不到第三面時只驗到兩面，依契約不得宣稱已有裁決。"""
    finding = audit_review_channel(
        [{"body": _verdict(_conformant_marker())}], _ECARD, _ESHA,
        card_body=_ELOG, delivery_status=None,
    )
    assert finding.status == "half_written"
    assert "無法讀取" in finding.detail


def test_verdict_heading_missing_blocks_third_face_comparison():
    """marker 合格但沒有可辨識的裁決結論時，無從比對狀態欄——不得放行。"""
    body = f"{_conformant_marker()}\n（這則留言沒有查核裁決標題）\n{_EATT}"
    finding = audit_review_channel(
        [{"body": body}], _ECARD, _ESHA, card_body=_ELOG, delivery_status="✅通過"
    )
    assert finding.status == "half_written"
    assert "無法辨識或不唯一" in finding.detail


def test_half_written_is_distinct_from_the_other_four_states():
    def st(**kw):
        return audit_review_channel(**kw).status

    bad_marker = _verdict(f"<!-- wf-review-event:v2 card_id={_ECARD} source_sha={_ESHA} attempt_id={_EATT} -->")
    assert st(comments=[{"body": _verdict(_conformant_marker())}], card_id=_ECARD,
              source_sha=_ESHA, card_body=_ELOG, delivery_status="🔍待查核") == "half_written"
    assert st(comments=[{"body": bad_marker}], card_id=_ECARD, source_sha=_ESHA,
              card_body=_ELOG, delivery_status="✅通過") == "marker_quarantined"
    assert st(comments=[], card_id=_ECARD, source_sha=_ESHA,
              card_body=_ELOG, delivery_status="✅通過") == "unobservable"


def test_half_written_still_surfaces_receipts():
    receipt = f"<!-- wf-review-receipt:v1\ncard_id: {_ECARD}\nsource_sha: {_ESHA}\n-->"
    finding = audit_review_channel(
        [{"body": _verdict(_conformant_marker())},
         {"body": receipt, "html_url": "https://x/9", "user": {"login": "rev"}}],
        _ECARD, _ESHA, card_body=_ELOG, delivery_status="🔍待查核",
    )
    assert finding.status == "half_written"
    assert finding.receipt_urls == ("https://x/9",)


def test_expected_status_is_read_from_the_deciding_comment_not_the_first_one():
    """legacy 路徑同樣要以「據以放行的 attempt」過濾，否則會抓到別卡的裁決結論。

    先前只用 v1 的 matched 當過濾集，legacy 路徑拿到空集合而失去過濾，前置的別卡
    留言就會決定 expected，造成 half_written 誤報——方向雖是 fail-closed，卻會擋住
    合法的 legacy 卡，而 legacy 相容是硬性驗收。
    """
    other = f"## 查核裁決：REQUEST_CHANGES\n- 卡：`OTHER-CARD` attempt_id：`OTHER-e0-{_ESHA}`"
    legacy = f"## 查核裁決：APPROVE\n- 卡：`{_ECARD}`　attempt_id：`{_EATT}`"
    finding = audit_review_channel(
        [{"body": other}, {"body": legacy}], _ECARD, _ESHA,
        card_body=_ELOG, delivery_status="✅通過",
    )
    assert finding.status == "recorded"
    assert finding.expected_delivery_status == "✅通過"


def test_expected_status_must_not_depend_on_comment_order():
    """review-escalation.md §2：不得依事件或陣列順序覆寫。

    同一 SHA 在 replan 後重審時，e0 與 e1 可能都被正確索引且結論相反。取「第一則」
    會讓結果隨留言排序而變——這是不可重現的判定，必須 fail-closed 交人裁定。
    """
    a1 = f"{_ECARD}-e1-{_ESHA}"
    def ev(attempt, result):
        return (f"{_conformant_marker(attempt=attempt)}\n"
                f"## 查核裁決：{result}\n- attempt_id：`{attempt}`")
    log = f"- review by wf-cli；attempt {_EATT}。\n- review by wf-cli；attempt {a1}。"
    order_a = audit_review_channel(
        [{"body": ev(_EATT, "REQUEST_CHANGES")}, {"body": ev(a1, "APPROVE")}],
        _ECARD, _ESHA, card_body=log, delivery_status="✅通過")
    order_b = audit_review_channel(
        [{"body": ev(a1, "APPROVE")}, {"body": ev(_EATT, "REQUEST_CHANGES")}],
        _ECARD, _ESHA, card_body=log, delivery_status="✅通過")
    assert order_a.status == order_b.status == "half_written"
    assert "多種裁決結論" in order_a.detail


def test_expected_status_comes_from_the_deciding_event_not_from_mentions():
    """只有「據以放行的那個事件」自己的裁決標題算數。

    先前事後重掃全部留言、以「有沒有提到這個 attempt」決定誰有資格提供結論，因而
    兩種誤報：討論串引用裁決標題並提及該 attempt；以及 `in` 子字串比對讓
    `…-e0-<sha>` 命中 `…-e0-<sha>x`。
    """
    event = _verdict(_conformant_marker())
    quoted = f"我引用一下：\n## 查核裁決：REQUEST_CHANGES\n（討論 {_EATT} 這個 attempt）"
    longer = f"## 查核裁決：REQUEST_CHANGES\n- attempt_id：`{_EATT}x`"
    for noise in (quoted, longer):
        finding = audit_review_channel(
            [{"body": event}, {"body": noise}], _ECARD, _ESHA,
            card_body=_ELOG, delivery_status="✅通過",
        )
        assert finding.status == "recorded", f"雜訊留言不得影響 expected：{noise[:20]}"


def test_conflicting_v1_and_legacy_verdicts_are_ambiguous_not_v1_wins():
    """兩個 v1 結論相反判歧義，v1 與 legacy 結論相反也必須判歧義。

    先前 `deciding = matched or legacy_only` 讓後者默默取 v1——同樣的處境兩種待遇。
    在不引入時間語意的前提下，無法宣稱 v1 較新而應勝出。
    """
    a1 = f"{_ECARD}-e1-{_ESHA}"
    v1 = f"{_conformant_marker()}\n## 查核裁決：APPROVE\n- attempt_id：`{_EATT}`"
    legacy = f"## 查核裁決：REQUEST_CHANGES\n- 卡：`{_ECARD}`　attempt_id：`{a1}`"
    log = f"- review by wf-cli；attempt {_EATT}。\n- review by wf-cli → APPROVE。\n- assign；attempt {a1}。"
    finding = audit_review_channel(
        [{"body": v1}, {"body": legacy}], _ECARD, _ESHA, card_body=log, delivery_status="✅通過"
    )
    assert finding.status == "half_written"
    assert "多種裁決結論" in finding.detail


def test_agreeing_v1_and_legacy_verdicts_still_record():
    a1 = f"{_ECARD}-e1-{_ESHA}"
    v1 = f"{_conformant_marker()}\n## 查核裁決：APPROVE\n- attempt_id：`{_EATT}`"
    legacy = f"## 查核裁決：APPROVE\n- 卡：`{_ECARD}`　attempt_id：`{a1}`"
    log = f"- review by wf-cli；attempt {_EATT}。\n- review by wf-cli → APPROVE。\n- assign；attempt {a1}。"
    finding = audit_review_channel(
        [{"body": v1}, {"body": legacy}], _ECARD, _ESHA, card_body=log, delivery_status="✅通過"
    )
    assert finding.status == "recorded"


def test_multiple_verdict_headings_in_one_comment_are_ambiguous():
    """同一則留言出現多個 `## 查核裁決：` 時不得取第一個。

    取第一個會讓結果隨標題在留言內的先後而變，與 review-escalation.md §2
    「不得依順序覆寫」同源。wfcli review 渲染的留言恰有一個標題；多個代表有人
    引用了另一則裁決或編輯過留言。
    """
    m = _conformant_marker()
    a = audit_review_channel(
        [{"body": f"{m}\n## 查核裁決：APPROVE\n\n附註：\n## 查核裁決：REQUEST_CHANGES"}],
        _ECARD, _ESHA, card_body=_ELOG, delivery_status="✅通過")
    b = audit_review_channel(
        [{"body": f"{m}\n## 查核裁決：REQUEST_CHANGES\n\n更正：\n## 查核裁決：APPROVE"}],
        _ECARD, _ESHA, card_body=_ELOG, delivery_status="✅通過")
    assert a.status == b.status == "half_written"


def test_repeated_identical_verdict_heading_is_also_unusable():
    """即使兩個標題文字相同也不得放行——判準是出現次數恰為一。

    set 去重會讓重複的相同結論被當成唯一。但 wfcli review 渲染的留言恰有一個標題，
    重複代表有人編輯或引用過，該留言已不是產生器的輸出，其結論不可信。
    """
    m = _conformant_marker()
    finding = audit_review_channel(
        [{"body": f"{m}\n## 查核裁決：APPROVE\n\n重申：\n## 查核裁決：APPROVE"}],
        _ECARD, _ESHA, card_body=_ELOG, delivery_status="✅通過")
    assert finding.status == "half_written"


# --------------------------------------------------------------------------
# WF-CLEANUP-GUARD1：收尾清理前提的唯讀預覽
#
# doctor 的紅線是「只列清單、不動手」。這裡驗的不只是它印出正確結論，更重要的是
# 跑完之後**磁碟上的東西一個都沒少**——一個會順手清理的 doctor 才是真正的風險。
# --------------------------------------------------------------------------


def _free_prober(_path):
    return "free", "fake prober：無人佔用"


_CLEANUP_BODY = """## 資源宣告
<!-- resource-claims:begin -->
```json
{"db_scope": "none", "resources": ["file:x.py"]}
```
<!-- resource-claims:end -->
"""


def _merged_card_repo(sandbox_repo, tmp_path):
    branch = "claude/MERGED-CARD1"
    wt = tmp_path / "merged-wt"
    git(sandbox_repo, "worktree", "add", "-q", str(wt), "-b", branch)
    (wt / "done.txt").write_text("done\n", encoding="utf-8")
    git(wt, "add", "done.txt")
    git(wt, "commit", "-q", "-m", "work")
    git(sandbox_repo, "merge", "-q", "--no-ff", "-m", "merge", branch)
    registry = _registry([
        RegisteredCard(card_id="MERGED-CARD1", branch=branch, worktree_path=str(wt),
                       delivery_status="📦已合併", owner="someone@tool"),
    ])
    return branch, wt, registry


def test_cleanup_preview_is_off_by_default(sandbox_repo, tmp_path):
    _, _, registry = _merged_card_repo(sandbox_repo, tmp_path)
    report = run_doctor(sandbox_repo, registry)
    assert report.cleanup_previews == []
    assert report.cleanup_preview_enabled is False
    assert "收尾清理前提" not in report.render_text()


def test_cleanup_preview_blocks_on_uncommitted_work_and_deletes_nothing(sandbox_repo, tmp_path):
    branch, wt, registry = _merged_card_repo(sandbox_repo, tmp_path)
    (wt / "draft.txt").write_text("未提交\n", encoding="utf-8")

    report = run_doctor(sandbox_repo, registry, cleanup_preview=True,
                        card_bodies={"MERGED-CARD1": _CLEANUP_BODY},
                        occupancy_prober=_free_prober)

    assert len(report.cleanup_previews) == 1
    preview = report.cleanup_previews[0]
    assert preview.mode == "detect_only"
    assert any("no_uncommitted_changes" in r for r in preview.blocking_reasons)
    # doctor 唯讀：worktree、分支、未提交內容全都必須還在
    assert wt.exists()
    assert (wt / "draft.txt").read_text(encoding="utf-8") == "未提交\n"
    assert branch in git_ops_local_branches(sandbox_repo)
    assert "收尾清理前提" in report.render_text()


def git_ops_local_branches(repo):
    from wf_cli import git_ops

    return git_ops.local_branches(repo)


def test_cleanup_preview_reports_obligations_as_non_blocking(sandbox_repo, tmp_path):
    """第 5–7 步永遠列在 outstanding_obligations，且不影響 mode。"""
    from wf_cli.cleanup import SUBSEQUENT_OBLIGATION_STEPS

    _, _, registry = _merged_card_repo(sandbox_repo, tmp_path)
    report = run_doctor(sandbox_repo, registry, cleanup_preview=True,
                        card_bodies={"MERGED-CARD1": _CLEANUP_BODY},
                        occupancy_prober=_free_prober)
    preview = report.cleanup_previews[0]
    assert preview.outstanding_obligations == SUBSEQUENT_OBLIGATION_STEPS
    assert "不阻擋 release" in report.render_text()


def test_cleanup_preview_only_covers_merged_cards(sandbox_repo, tmp_path):
    """未 merge 的在途卡不是收尾候選，不得出現在預覽（也就不會被誤導去刪）。"""
    branch = "claude/IN-FLIGHT1"
    wt = tmp_path / "inflight-wt"
    git(sandbox_repo, "worktree", "add", "-q", str(wt), "-b", branch)
    registry = _registry([
        RegisteredCard(card_id="IN-FLIGHT1", branch=branch, worktree_path=str(wt),
                       delivery_status="🔨執行中", owner="someone@tool"),
    ])
    report = run_doctor(sandbox_repo, registry, cleanup_preview=True,
                        occupancy_prober=_free_prober)
    assert report.cleanup_previews == []


def test_cleanup_preview_json_payload_carries_previews(sandbox_repo, tmp_path, capsys):
    import argparse
    import json as jsonlib

    from wf_cli.commands import doctor_cmd

    _merged_card_repo(sandbox_repo, tmp_path)
    args = argparse.Namespace(
        repo_root=str(sandbox_repo), registry="none", review_channel=False,
        repo=None, issue_number=None, card_id=None, source_sha=None,
        owner=None, project=None, cleanup_preview=True,
        conformance=False,
        commit_trailers=False, commit_range=None,
        trailer_epoch=TRAILER_GUARD_EPOCH, require_planned_by=False,
        main_ref="main", lease_ttl_hours=48.0, json=True, strict=False,
    )
    assert doctor_cmd.run(args) == 0
    payload = jsonlib.loads(capsys.readouterr().out)
    assert payload["cleanup_preview_enabled"] is True
    assert payload["cleanup_previews"] == []  # registry=none 時沒有卡可預覽


# --------------------------------------------------------------------------
# commit trailer 完整性（DEV-COMMIT-TRAILER-GUARD1）
# --------------------------------------------------------------------------
#
# 這一段的固定裝置全部是**真的 git commit**，不是拼出來的字串：本檢查器的整個
# 賣點是「用 git 自己的 trailer parser 判定」，用假訊息測等於繞過那一點。


def _rec(**kw) -> CommitRecord:
    base = {
        "sha": "a" * 40, "parents": ("b" * 40,), "committed_at": "2026-08-20T10:00:00+08:00",
        "authored_at": "2026-08-20T10:00:00+08:00", "subject": "s", "message": "s\n",
        "trailers": (), "changed_paths": ("f.txt",), "merge_content_paths": (),
    }
    base.update(kw)
    return CommitRecord(**base)  # type: ignore[arg-type]


_FULL = ("Requested-by: ruan6047", "Planned-by: M@Tool", "Implemented-by: M@Tool")


def _commit(
    repo, path: str | None, subject: str, tail: str = "\n".join(_FULL),
    when: str | None = None,
) -> str:
    """在 sandbox 建一筆 commit；`path=None` 代表空 commit。

    `when` 把這一筆的作者／提交者日期釘死（ISO8601）。凡是**測試斷言與日期有關**
    （界線分流是唯一一種）就必須傳，否則該 commit 採執行當下的時間，斷言就綁在
    牆上時鐘上。不傳＝這筆的日期與斷言無關。
    """
    args = ["commit", "-q", "-m", f"{subject}\n\n說明段落。\n\n{tail}" if tail else f"{subject}\n\n說明段落。"]
    if path is None:
        args.insert(2, "--allow-empty")
    else:
        (repo / path).write_text(path + "\n", encoding="utf-8")
        git(repo, "add", path)
    git(repo, *args, env=fixed_date_env(when) if when else None)
    return git(repo, "rev-parse", "HEAD").strip()


# ---- 形狀判定：四種形狀各自的裁定（卡面驗收第 2 條） --------------------


def test_shape_merge_without_combined_diff_is_not_an_implementation_commit():
    """乾淨 merge 的 tree 完全由 parent 解釋得出，沒有自己著作的內容。"""
    rec = _rec(parents=("b" * 40, "c" * 40), changed_paths=(), merge_content_paths=())
    assert classify_commit_shape(rec) == "merge_clean"
    # §6:222 對 merge commit 仍要求 Reviewed-by，但不要求實作三件式。
    assert required_trailers("merge_clean") == ("Reviewed-by",)


def test_shape_merge_with_combined_diff_is_held_to_the_implementation_floor():
    """衝突解法／evil merge 是在 merge 當下寫下的內容，必須有來歷。

    這一格同時是規避路徑的堵口：把改動塞進 merge commit 就能免除 trailer 的話，
    整個檢查器可以用一個 `--no-ff` 繞過去。
    """
    rec = _rec(parents=("b" * 40, "c" * 40), changed_paths=(), merge_content_paths=("x.py",))
    assert classify_commit_shape(rec) == "merge_with_content"
    assert required_trailers("merge_with_content") == ("Requested-by", "Implemented-by", "Reviewed-by")


def test_shape_empty_commit_requires_nothing_and_grants_nothing():
    """空 commit 沒有著作內容 → 無所要求；且**不繼承給任何其他 commit**。"""
    rec = _rec(changed_paths=(), trailers=(("Requested-by", "r"), ("Implemented-by", "i")))
    assert classify_commit_shape(rec) == "empty"
    assert required_trailers("empty") == ()
    finding = evaluate_commit_trailers(rec, epoch=None)
    assert finding.status == "not_applicable"
    assert "不繼承" in finding.detail, "必須明說它不會讓別的 commit 變綠"


def test_shape_root_commit_is_an_implementation_commit():
    """root commit 相對空樹的差異就是它的內容，不是特例。"""
    assert classify_commit_shape(_rec(parents=(), changed_paths=("a.txt",))) == "implementation"


# ---- 判定層 -------------------------------------------------------------


def test_floor_is_the_intersection_of_both_tiers_so_no_card_lookup_is_needed():
    """`Requested-by`／`Implemented-by` 是 T0/T1 與 T2 的交集，故不需知道級別。

    級別是卡面欄位、不在 commit 裡；把它做成必要輸入就違反「判準須可從 commit
    本身導出」。
    """
    assert required_trailers("implementation") == ("Requested-by", "Implemented-by")


def test_planned_by_is_reported_but_not_a_violation_unless_caller_declares_tier():
    rec = _rec(trailers=(("Requested-by", "r"), ("Implemented-by", "i")))
    default = evaluate_commit_trailers(rec, epoch=None)
    assert default.status == "compliant"
    assert default.undecidable == ("Planned-by",), "缺席要如實回報，只是不判違規"

    declared = evaluate_commit_trailers(rec, epoch=None, require_planned_by=True)
    assert declared.status == "violation" and declared.missing == ("Planned-by",)


def test_missing_floor_trailer_is_a_violation():
    rec = _rec(trailers=(("Co-Authored-By", "x"),))
    finding = evaluate_commit_trailers(rec, epoch=None)
    assert finding.status == "violation"
    assert finding.missing == ("Requested-by", "Implemented-by")


def test_commit_before_the_epoch_is_triaged_not_counted_as_a_violation():
    """界線前的 commit 補不了（禁改寫已推送歷史），列為界線前而非違規。"""
    rec = _rec(committed_at="2026-08-11T10:00:00+08:00", trailers=())
    finding = evaluate_commit_trailers(rec)
    assert finding.status == "pre_guard"
    assert finding.missing == ("Requested-by", "Implemented-by"), "分流不等於不記錄"
    assert "不裁定" in finding.detail, "採認與否是規則層裁定，本檢查器不得代為裁定"


def test_epoch_none_grades_the_whole_range():
    rec = _rec(committed_at="2020-01-01T00:00:00+08:00", trailers=())
    assert evaluate_commit_trailers(rec, epoch=None).status == "violation"


# ---- 「寫了但被空行切斷」的偵測（canonical `ANCHOR_BLOCK` 那條） --------


def test_severed_block_is_reported_separately_from_never_written():
    """兩種病不同：一種要補寫，一種要刪掉那個空行。"""
    message = (
        "subj\n\n說明。\n\n"
        "Requested-by: r\nPlanned-by: p\nImplemented-by: i\n\n"
        "Co-Authored-By: X <x@e>\n"
    )
    assert severed_declared_keys(message, {"co-authored-by"}) == (
        "Requested-by", "Implemented-by", "Planned-by",
    )


def test_prose_mentioning_the_trailer_names_is_not_reported_as_severed():
    """全文 regex 會把「討論 trailer 規則的 commit 訊息」誤判——本卡自己就是。"""
    message = (
        "subj\n\n本卡要求 Implemented-by: 這種欄位能被解析，並說明 Requested-by: 的語意。\n\n"
        "Requested-by: r\nImplemented-by: i\n"
    )
    assert severed_declared_keys(message, {"requested-by", "implemented-by"}) == ()


# ---- git 整合 + 突變注入 ------------------------------------------------


def test_audit_reads_real_git_history_and_classifies_every_shape(sandbox_repo, tmp_path):
    repo = sandbox_repo
    green = _commit(repo, "green.txt", "feat: 帶齊 trailer")
    bare = _commit(repo, "bare.txt", "feat: 完全沒寫 trailer", tail="")
    empty = _commit(repo, None, "chore: 空 commit")

    git(repo, "checkout", "-q", "-b", "topic", green)
    topic = _commit(repo, "topic.txt", "feat: topic 側")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--no-ff", "topic", "-m", "Merge topic\n\nReviewed-by: R@Tool")
    clean_merge = git(repo, "rev-parse", "HEAD").strip()

    report = audit_commit_trailers(repo, "main", epoch=None)
    by_sha = {f.sha: f for f in report.findings}

    assert by_sha[green].status == "compliant" and by_sha[green].shape == "implementation"
    assert by_sha[bare].status == "violation"
    assert by_sha[bare].missing == ("Requested-by", "Implemented-by")
    assert by_sha[empty].status == "not_applicable" and by_sha[empty].shape == "empty"
    assert by_sha[topic].status == "compliant"
    assert by_sha[clean_merge].shape == "merge_clean"
    assert by_sha[clean_merge].status == "compliant", "帶 Reviewed-by 的乾淨 merge 合規"


def test_evil_merge_content_is_detected_through_the_combined_diff(sandbox_repo):
    """把改動夾進 merge commit 不得因此免除 trailer。"""
    repo = sandbox_repo
    base = _commit(repo, "base.txt", "feat: base")
    git(repo, "checkout", "-q", "-b", "side", base)
    _commit(repo, "side.txt", "feat: side")
    git(repo, "checkout", "-q", "main")
    _commit(repo, "mainside.txt", "feat: main side")
    git(repo, "merge", "--no-ff", "--no-commit", "side")
    (repo / "smuggled.py").write_text("print('smuggled')\n", encoding="utf-8")
    git(repo, "add", "smuggled.py")
    git(repo, "commit", "-q", "-m", "Merge side\n\nReviewed-by: R@Tool")
    evil = git(repo, "rev-parse", "HEAD").strip()

    finding = {f.sha: f for f in audit_commit_trailers(repo, "main", epoch=None).findings}[evil]
    assert finding.shape == "merge_with_content"
    assert finding.status == "violation"
    assert finding.missing == ("Requested-by", "Implemented-by")


def test_cherry_pick_needs_no_special_case_because_the_message_travels(sandbox_repo):
    """`-x` 那一行不是 `key: value`，`only=true` 會濾掉，不切斷同區塊其他 trailer。"""
    repo = sandbox_repo
    base = git(repo, "rev-parse", "HEAD").strip()
    git(repo, "checkout", "-q", "-b", "src", base)
    src = _commit(repo, "picked.txt", "feat: 會被 cherry-pick 的變更")
    git(repo, "checkout", "-q", "main")
    git(repo, "cherry-pick", "-x", src)
    picked = git(repo, "rev-parse", "HEAD").strip()

    finding = {f.sha: f for f in audit_commit_trailers(repo, "main", epoch=None).findings}[picked]
    assert finding.shape == "implementation"
    assert finding.status == "compliant"
    assert "cherry picked from" in git(repo, "log", "-1", "--format=%B")


@pytest.mark.parametrize(
    "mutant_tail, expect_missing, expect_severed",
    [
        # 突變 1：拿掉一行 trailer。
        (
            "Requested-by: ruan6047\nPlanned-by: M@Tool\nCo-Authored-By: X <x@e>",
            ("Implemented-by",),
            (),
        ),
        # 突變 2：在治理 trailer 與 Co-Authored-By 之間插入空行（§6.1 第 5 條）。
        # 肉眼看訊息「三件都寫了」，`interpret-trailers` 在空行處切斷，實際一件都沒有。
        (
            "Requested-by: ruan6047\nPlanned-by: M@Tool\nImplemented-by: M@Tool\n\nCo-Authored-By: X <x@e>",
            ("Requested-by", "Implemented-by"),
            ("Requested-by", "Implemented-by", "Planned-by"),
        ),
    ],
    ids=["drop-one-trailer-line", "blank-line-severs-the-block"],
)
def test_mutations_of_a_green_commit_are_killed(sandbox_repo, mutant_tail, expect_missing, expect_severed):
    """突變注入：先證 baseline 為綠，再證同一形狀的突變被判紅。

    baseline 必須在同一個測試裡跑過——否則「突變被判紅」可能只是因為固定裝置
    本來就紅，斷言等於沒有鑑別力。
    """
    repo = sandbox_repo
    green_tail = "\n".join((*_FULL, "Co-Authored-By: X <x@e>"))
    green = _commit(repo, "green.txt", "feat: baseline", tail=green_tail)
    baseline = {f.sha: f for f in audit_commit_trailers(repo, "main", epoch=None).findings}[green]
    assert baseline.status == "compliant", "baseline 必須先是綠的，否則突變測試無意義"

    mutant = _commit(repo, "mutant.txt", "feat: mutant", tail=mutant_tail)
    finding = {f.sha: f for f in audit_commit_trailers(repo, "main", epoch=None).findings}[mutant]
    assert finding.status == "violation"
    assert finding.missing == expect_missing
    assert finding.severed == expect_severed


def test_epoch_triage_splits_history_from_new_commits_on_real_history(sandbox_repo):
    """同一份歷史、同一個檢查器，界線兩側判定不同——這就是「分流」。

    三筆 commit 的日期**全部**釘死（含 fixture 的初始 commit，見
    `conftest.SANDBOX_COMMIT_DATE`），界線本身也是傳進去的常數。故本測試不讀
    牆上時鐘：不論在哪一天執行，每筆 commit 落在界線的哪一側都是同一個答案。

    舊寫法只釘界線後那筆，界線前那筆採執行當下的時間，2026-08-13T00:00 一過就
    翻到界線後——不是 flaky，是必然到期。
    """
    repo = sandbox_repo
    epoch = "2026-08-13T00:00:00+08:00"
    old = _commit(repo, "old.txt", "feat: 界線前", tail="", when="2026-08-11T10:00:00+08:00")
    new = _commit(repo, "new.txt", "feat: 界線後", tail="", when="2026-08-20T10:00:00+08:00")

    report = audit_commit_trailers(repo, "main", epoch=epoch)
    by_sha = {f.sha: f for f in report.findings}
    assert by_sha[old].status == "pre_guard"
    assert by_sha[new].status == "violation"
    # 逐 SHA 比對而非只數個數：初始 commit 同樣沒有 trailer，它被算進界線前而非
    # 違規，正是分流要證明的事；只斷言個數的話，它跑到哪一側都看不出來。
    assert [f.sha for f in report.violations] == [new]


def test_sandbox_history_carries_no_wall_clock_date(sandbox_repo):
    """上面那個分流測試的前提，本身要被斷言，不能只靠註解。

    fixture 的初始 commit 一旦改回採「現在」，分流測試會在某個未來日期無聲地
    由綠轉紅（2026-08-13 已經發生過一次）。這條把那個前提釘成契約：契約破了，
    紅的是這一條，訊息直接指向根因，而不是讓人去追一個「昨天還好好的」測試。
    """
    assert git(sandbox_repo, "log", "-1", "--format=%cI").strip() == SANDBOX_COMMIT_DATE
    assert git(sandbox_repo, "log", "-1", "--format=%aI").strip() == SANDBOX_COMMIT_DATE
    pinned = _commit(sandbox_repo, "p.txt", "feat: 釘死日期", when=SANDBOX_COMMIT_DATE)
    assert git(sandbox_repo, "show", "-s", "--format=%cI", pinned).strip() == SANDBOX_COMMIT_DATE


# ---- 根因命名的裁定 ------------------------------------------------------


def test_canonical_root_cause_id_is_pinned_and_superseded_names_are_recorded():
    """名字一改，升級門檻的 join key 就變了；固定住它，並留下舊名對照。

    對照表是**唯讀紀錄**，不回寫任何已寫入的事件（本專案禁止追溯改寫）。
    """
    assert COMMIT_TRAILER_ROOT_CAUSE_ID == "commit-trailer-required-but-missing"
    assert "governance-provenance-trailer-omission" in SUPERSEDED_ROOT_CAUSE_IDS
    assert any(n.startswith("unknown-") for n in SUPERSEDED_ROOT_CAUSE_IDS)
    assert COMMIT_TRAILER_ROOT_CAUSE_ID not in SUPERSEDED_ROOT_CAUSE_IDS


def test_agents_md_records_the_canonical_root_cause_id():
    """裁定要寫在後續查核者引用得到的地方，不能只活在程式碼常數裡。"""
    agents = (Path(__file__).resolve().parents[2] / "AGENTS.md").read_text(encoding="utf-8")
    assert COMMIT_TRAILER_ROOT_CAUSE_ID in agents
    for superseded in SUPERSEDED_ROOT_CAUSE_IDS:
        assert superseded in agents, "舊名要留在對照表裡，否則後來的人看不出是同一族"


# ---- CLI ----------------------------------------------------------------


def _trailer_args(repo, **overrides):
    import argparse

    defaults = {
        "repo_root": str(repo), "registry": "none", "review_channel": False,
        "repo": None, "issue_number": None, "card_id": None, "source_sha": None,
        "owner": None, "project": None, "cleanup_preview": False,
        "conformance": False,
        "commit_trailers": True, "commit_range": "main",
        "trailer_epoch": "none", "require_planned_by": False,
        "main_ref": "main", "lease_ttl_hours": 48.0, "json": False, "strict": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def test_cli_requires_an_explicit_commit_range(sandbox_repo, capsys):
    """`HEAD` 在 git log 語意下是整段歷史；猜錯範圍比要求明講糟得多。"""
    from wf_cli.commands import doctor_cmd

    assert doctor_cmd.run(_trailer_args(sandbox_repo, commit_range=None)) == 2
    assert "--commit-range" in capsys.readouterr().err


def test_cli_strict_exits_non_zero_on_violation_and_zero_when_clean(sandbox_repo, capsys):
    from wf_cli.commands import doctor_cmd

    _commit(sandbox_repo, "ok.txt", "feat: 合規")
    assert doctor_cmd.run(_trailer_args(sandbox_repo, strict=True, commit_range="HEAD~1..HEAD")) == 0
    _commit(sandbox_repo, "bad.txt", "feat: 不合規", tail="")
    assert doctor_cmd.run(_trailer_args(sandbox_repo, strict=True, commit_range="HEAD~1..HEAD")) == 1
    capsys.readouterr()


def test_cli_json_payload_carries_commit_trailers_for_machine_consumers(sandbox_repo, capsys):
    """#48 的 CI 要機器判讀；只有人類可讀那份等於沒對外提供。"""
    import json as jsonlib

    from wf_cli.commands import doctor_cmd

    _commit(sandbox_repo, "bad.txt", "feat: 不合規", tail="")
    assert doctor_cmd.run(_trailer_args(sandbox_repo, json=True, commit_range="HEAD~1..HEAD")) == 0
    payload = jsonlib.loads(capsys.readouterr().out)
    assert payload["commit_trailers"]["rev_range"] == "HEAD~1..HEAD"
    assert [f["status"] for f in payload["commit_trailers"]["findings"]] == ["violation"]
    assert "worktrees" in payload and payload["review_channel"] is None


def test_cli_json_payload_omits_commit_trailers_when_not_requested(sandbox_repo, capsys):
    import json as jsonlib

    from wf_cli.commands import doctor_cmd

    assert doctor_cmd.run(_trailer_args(sandbox_repo, json=True, commit_trailers=False)) == 0
    assert jsonlib.loads(capsys.readouterr().out)["commit_trailers"] is None


def test_rendered_report_refuses_to_claim_it_blocks_anything(sandbox_repo):
    """ROADMAP §2：偵測器不得宣稱「已預防」。#57 R1-01 正是因此被判 blocking。"""
    _commit(sandbox_repo, "bad.txt", "feat: 不合規", tail="")
    text = audit_commit_trailers(sandbox_repo, "main", epoch=None).render_text()
    assert "唯讀" in text and "不阻擋" in text
    assert "DEV-AIWF-MINIMAL-CI1" in text, "必須指名強制面的承接者"


# --------------------------------------------------------------------------
# `#62` 之前的 amend 授權措辭：既存留痕的強度標記（WF-AMEND-AUTHZ-BINDING1）
# --------------------------------------------------------------------------
#
# 既存事件不得追溯改寫，所以處置是讓它們可被機械認出。判準是舊字面本身，且
# **必須落在授權欄內**——下面的假陰／假陽兩組測試就是在釘這條界線。
#
# 下面的夾具形狀取自 2026-08-16 全庫掃描實見的四行**沒有授權欄卻帶著舊措辭**的
# Log／正文（`#62` 的痛點正文、`#62` 的 `--acceptance` 與 `--resources` 兩筆 amend
# 原值／理由引用、`#22` 的 handoff 證據敘述）。報它們＝說一行「授權留痕不足」，
# 而它壓根沒有授權留痕。
#
# ⚠️ 誠實界線：真實那四行裡只有兩行帶完整的 `LEGACY_AUTHORITY_NOTE_MARKER`，另兩行
# 只引到前半句「已逐字核對」。夾具一律用完整 marker，是**刻意取較嚴的情形**——
# 那才真正考驗位置錨；但因此夾具是照形狀重建的，不是那四行的逐字複本。

_OLD_NOTE = f"（GitHub comment author 已逐字核對，{LEGACY_AUTHORITY_NOTE_MARKER}）"
_NEW_NOTE = (
    "（已核對：該 URL 指向本卡 issue 的既存留言，且其 GitHub author 欄逐字等於"
    "卡面「需求：」欄。本指令不讀取留言內文或操作者身分，故不判定留言內容是否"
    "構成裁定——上句「裁定」是操作者的宣告，不是本指令查得的事實——"
    "亦不區分「需求方本人張貼」與「他人代擬代貼」）"
)


def _amend_line(op: str, note: str, *, old_value: str = "舊痛點", ts: str = "2026-08-12T12:27:51+08:00") -> str:
    return (
        f"- {ts} amend by wf-cli（op {op}）→ 核心痛點："
        f"原值「{old_value}」→ 新值「新痛點」；理由 需求方裁定；"
        f"授權 依需求方 ruan6047 於 https://github.com/o/r/issues/1#issuecomment-5 的裁定{note}。"
    )


def test_legacy_authority_note_is_detected_with_locator():
    findings = find_legacy_authority_notes("CARD1", _amend_line("166322be", _OLD_NOTE))
    assert len(findings) == 1
    f = findings[0]
    assert (f.card_id, f.op_id, f.field_name) == ("CARD1", "166322be", "核心痛點")
    assert f.timestamp == "2026-08-12T12:27:51+08:00"


def test_new_wording_authority_note_is_not_reported():
    """`#62` 之後的措辭不得被報成舊留痕，否則修好的卡會永遠掛在報告上。"""
    assert find_legacy_authority_notes("CARD1", _amend_line("aaaaaaaa", _NEW_NOTE)) == []


@pytest.mark.parametrize(
    "shape, line",
    [
        (
            "卡的痛點正文（#62 本人）",
            f"- **痛點**：amend_cmd.py:507 無條件輸出常數字面「GitHub comment author "
            f"已逐字核對，{LEGACY_AUTHORITY_NOTE_MARKER}」到授權欄。",
        ),
        (
            "--acceptance amend 的原值引用（#62）",
            "- 2026-08-16T10:40:37+08:00 amend by wf-cli（op 05cf6174）→ 驗收條件："
            f"原值「[ ] 移除 amend_cmd.py:507 那句「…{LEGACY_AUTHORITY_NOTE_MARKER}」」"
            "→ 新值「[ ] 改寫措辭」；理由 需求方裁定。",
        ),
        (
            "handoff 的證據敘述（#22）",
            "- 2026-08-11T23:50:49+08:00 handoff by wf-cli → owner 跨家族查核；"
            f"證據 R3：三項 blocking 全處置，含「{LEGACY_AUTHORITY_NOTE_MARKER}」一節。",
        ),
    ],
)
def test_marker_outside_the_authority_field_is_not_reported(shape, line):
    """只是**引述**舊措辭的行沒有授權欄，報它就是新的過度宣稱。

    這三種形狀都是實見的（2026-08-16 掃描，見上方註解含誠實界線）。排除是
    **構造性**的——靠「授權欄」這個位置錨，不是把某張卡特判掉——所以將來任何
    新的引述同樣不會誤報。實測：對真實 149 張卡面，粗判準 16 行、錨定後 14 行。
    """
    assert find_legacy_authority_notes("CARD1", line) == [], f"誤報了：{shape}"


def test_old_literal_quoted_in_old_value_does_not_taint_a_new_authority_note():
    """同一行可以「原值引用舊字面」＋「授權欄已是新措辭」——不得誤報。

    這不是假想：`#62` 自己的痛點正文就引用著舊字面，日後用新版 CLI 再修訂它一次，
    產生的就正是這種行。用整行比對會判它是舊留痕。
    """
    line = _amend_line(
        "bbbbbbbb", _NEW_NOTE, old_value=f"…常數字面「{LEGACY_AUTHORITY_NOTE_MARKER}」…"
    )
    assert LEGACY_AUTHORITY_NOTE_MARKER in line  # 夾具確實含舊字面
    assert find_legacy_authority_notes("CARD1", line) == []


@pytest.mark.parametrize("n", [0, 1, 3, 7])
def test_finding_count_follows_the_input_and_is_never_hardcoded(n):
    """母體會隨新事件增減，所以檢查不得寫死任何計數。

    本卡在途期間該缺陷仍在生產新實例（13 → 14），釘死數字的檢查隔天就是錯的。
    """
    body = "\n".join(_amend_line(f"{i:08x}", _OLD_NOTE) for i in range(n))
    assert len(find_legacy_authority_notes("CARD1", body)) == n


def test_not_scanned_is_distinguished_from_scanned_and_clean():
    """沒掃 ≠ 沒有。兩者都回空清單，若報告不分就成了永不會響的偵測器。"""
    not_scanned = audit_legacy_authority_notes(None)
    assert (not_scanned.status, not_scanned.findings) == ("not_scanned", [])
    assert audit_legacy_authority_notes({}).status == "not_scanned"

    clean = audit_legacy_authority_notes({"CARD1": _amend_line("cccccccc", _NEW_NOTE)})
    assert (clean.status, clean.scanned_cards, clean.findings) == ("scanned", 1, [])

    dirty = audit_legacy_authority_notes(
        {"CARD1": _amend_line("dddddddd", _OLD_NOTE), "CARD2": _amend_line("eeeeeeee", _OLD_NOTE)}
    )
    assert dirty.status == "scanned" and len(dirty.findings) == 2
    assert dirty.affected_card_ids == ("CARD1", "CARD2")


def test_rendered_report_separates_not_scanned_from_clean(sandbox_repo):
    """render_text 也要分得開，否則人類讀者拿到的還是「一切乾淨」。"""
    unscanned = run_doctor(sandbox_repo).render_text()
    assert "未掃描" in unscanned and "這不等於沒有" in unscanned

    report = run_doctor(sandbox_repo)
    report.legacy_authority_notes = audit_legacy_authority_notes(
        {"CARD1": _amend_line("ffffffff", _OLD_NOTE)}
    )
    text = report.render_text()
    assert "CARD1" in text and "ffffffff" in text
    assert LEGACY_AUTHORITY_NOTE_EXPLANATION in text


def test_explanation_reports_evidence_strength_not_authorization_validity():
    """⚠️ 這個檢查本身不得變成新的過度宣稱。

    它必須說清楚三件事，且**第 3 件是關鍵**：報的是留痕強度不足，不是授權無效。
    doctor 讀不到那則留言的內文，沒有立場評價個別授權的真假。

    **突變檢驗**：把說明改成「該授權無效」之類的斷言，本測試轉紅。
    """
    text = LEGACY_AUTHORITY_NOTE_EXPLANATION
    # (1) 這是 #62 之前的措辭
    assert "#62 之前的措辭" in text
    # (2) 區辨力構造上不成立，且說明為什麼（同一個帳號 → 比對恆真）
    assert "構造上不成立" in text
    assert "恆真" in text and "同一個平台身分" in text
    # (3) 底下的授權可能仍然真實——這是強度陳述，不是效力裁定
    assert "不表示那些授權是假的" in text
    assert "不是「那次授權無效」" in text
    # 反向：不得出現把它讀成效力裁定的字樣
    for overclaim in ("授權無效", "授權不成立", "該次授權為假", "撤銷"):
        assert overclaim not in text.replace("不是「那次授權無效」", "")


def test_finding_carries_no_verdict_field_about_the_authorization():
    """finding 只帶定位資訊。加一個「這次授權有效嗎」的欄位就是越權。"""
    f = find_legacy_authority_notes("CARD1", _amend_line("11111111", _OLD_NOTE))[0]
    assert set(vars(f)) == {"card_id", "timestamp", "op_id", "field_name"}


# ---- CLI 接線（R3）------------------------------------------------------
#
# 上一輪的缺口：`doctor_cmd` 從不提供卡面，所以這一節從 CLI 跑必定印「未掃描」
# ——一個構造上不可能執行的檢查不構成「機械標記」。本組釘住接線本身。


class _FakeProjectRunner:
    """`resolve_project` / `list_items` 用的最小替身；不連網。"""

    def __init__(self, bodies: dict[str, str]):
        self.bodies = bodies
        self.calls: list[list[str]] = []

    def run_json(self, args):
        self.calls.append(list(args))
        raise AssertionError("本替身只支援 project 讀取路徑")


def _doctor_args(repo, **overrides):
    import argparse

    defaults = {
        "repo_root": str(repo), "registry": "none", "review_channel": False,
        "repo": None, "issue_number": None, "card_id": None, "source_sha": None,
        "owner": None, "project": None, "cleanup_preview": False,
        "conformance": False,
        "commit_trailers": False, "commit_range": None,
        "trailer_epoch": "none", "require_planned_by": False,
        "main_ref": "main", "lease_ttl_hours": 48.0, "json": False, "strict": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _patch_project(monkeypatch, bodies):
    """把 doctor_cmd 的 Project 讀取換掉，回傳給定卡面。"""
    from wf_cli.commands import doctor_cmd

    class _Item:
        """`ItemSnapshot` 的最小替身。⚠️ **必須有 `fields`**——真實快照有，替身沒有的話
        `doctor_cmd` 讀欄位時會拋 AttributeError 而被那個寬鬆 except 吞掉，測試看起來
        全綠但走的是「讀取失敗」那條路，等於在測一個不存在的世界。"""

        def __init__(self, card_id, body, fields=None):
            self.card_id, self.body = card_id, body
            self.fields = dict(fields or {})

    monkeypatch.setattr(doctor_cmd, "resolve_project", lambda *a, **k: {"id": "P"})
    monkeypatch.setattr(
        doctor_cmd, "list_items",
        lambda *a, **k: [
            _Item(cid, b if isinstance(b, str) else b["body"],
                  None if isinstance(b, str) else b.get("fields"))
            for cid, b in bodies.items()
        ],
    )
    return doctor_cmd


def test_cli_flag_actually_scans_and_reports(sandbox_repo, monkeypatch, capsys):
    """⚠️ 本組要擋的就是「測試綠但 CLI 跑不到」。

    **突變檢驗**：把 `doctor_cmd` 傳給 `run_doctor` 的
    `legacy_authority_card_bodies=legacy_bodies` 改回不傳（或傳 None），本測試轉紅。
    """
    doctor_cmd = _patch_project(monkeypatch, {"CARD1": _amend_line("166322be", _OLD_NOTE)})
    rc = doctor_cmd.run(
        _doctor_args(sandbox_repo, conformance=True, owner="acme", project=4)
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "已掃描 1 張卡" in out
    assert "CARD1" in out and "166322be" in out
    assert LEGACY_AUTHORITY_NOTE_EXPLANATION in out
    assert "未掃描" not in out


def test_cli_without_the_flag_stays_not_scanned(sandbox_repo, capsys):
    """不加旗標時仍是 `not_scanned`——不得謊報乾淨，也不得偷偷連網。"""
    from wf_cli.commands import doctor_cmd

    assert doctor_cmd.run(_doctor_args(sandbox_repo)) == 0
    out = capsys.readouterr().out
    assert "未掃描" in out and "這不等於沒有" in out
    # 指路必須指向**CLI 可用的**旗標，不能只講程式參數
    assert "--legacy-authority-notes" in out


def test_cli_flag_requires_owner_and_project(sandbox_repo, capsys):
    from wf_cli.commands import doctor_cmd

    assert doctor_cmd.run(_doctor_args(sandbox_repo, conformance=True)) == 2
    err = capsys.readouterr().err
    assert "--owner" in err and "--project" in err


def test_cli_keeps_not_scanned_when_card_fetch_fails(sandbox_repo, monkeypatch, capsys):
    """抓取失敗 → 維持 `not_scanned`，不中止、也不當成掃過且乾淨。"""
    from wf_cli.commands import doctor_cmd

    def _boom(*a, **k):
        raise RuntimeError("gh 掛了")

    monkeypatch.setattr(doctor_cmd, "resolve_project", _boom)
    rc = doctor_cmd.run(
        _doctor_args(sandbox_repo, conformance=True, owner="acme", project=4)
    )
    assert rc == 0, "抓取失敗不該讓整個 doctor 中止"
    captured = capsys.readouterr()
    assert "取不到 Project 卡面" in captured.err and "這不等於沒有" in captured.err
    assert "未掃描" in captured.out


def test_legacy_notes_never_affect_strict_exit_code(sandbox_repo, monkeypatch, capsys):
    """既存事件不可改寫，把它們算進 --strict 會讓 CI 恆紅且無人能修好。"""
    doctor_cmd = _patch_project(monkeypatch, {"CARD1": _amend_line("166322be", _OLD_NOTE)})
    rc = doctor_cmd.run(
        _doctor_args(
            sandbox_repo, conformance=True, owner="acme", project=4,
            registry="none", strict=True,
        )
    )
    assert "已掃描 1 張卡" in capsys.readouterr().out, "夾具必須真的有 finding"
    assert rc == 0, "--strict 不得因舊措辭留痕而失敗"


def test_cli_does_not_feed_cleanup_guard_when_scanning_legacy_notes(sandbox_repo, monkeypatch):
    """接線**不得**順手改變 `--cleanup-preview` 的判定。

    `run_doctor(card_bodies=...)` 餵的是 cleanup guard 第 3 步（資源宣告釋放），
    今天 `doctor_cmd` 從不提供它。本檢查若共用該參數，會沉默地讓原本跳過的
    資源釋放檢查開始生效——那是另一張卡的射程。
    """
    from wf_cli.commands import doctor_cmd

    seen = {}

    def _spy(repo_root, registry=None, **kw):
        seen.update(kw)
        return run_doctor(repo_root, registry, **kw)

    _patch_project(monkeypatch, {"CARD1": _amend_line("166322be", _OLD_NOTE)})
    monkeypatch.setattr(doctor_cmd, "run_doctor", _spy)
    doctor_cmd.run(
        _doctor_args(sandbox_repo, conformance=True, owner="acme", project=4)
    )
    assert seen.get("card_bodies") is None, "cleanup guard 的 card_bodies 不得被順手填上"
    assert seen.get("legacy_authority_card_bodies") == {
        "CARD1": _amend_line("166322be", _OLD_NOTE)
    }


def test_cli_json_payload_carries_legacy_authority_notes(sandbox_repo, monkeypatch, capsys):
    """機器消費端要讀得到；只有人類可讀那份等於沒有對外提供。"""
    import json as jsonlib

    doctor_cmd = _patch_project(monkeypatch, {"CARD1": _amend_line("166322be", _OLD_NOTE)})
    assert doctor_cmd.run(
        _doctor_args(
            sandbox_repo, conformance=True, owner="acme", project=4, json=True
        )
    ) == 0
    payload = jsonlib.loads(capsys.readouterr().out)["legacy_authority_notes"]
    assert payload["status"] == "scanned" and payload["scanned_cards"] == 1
    assert [f["op_id"] for f in payload["findings"]] == ["166322be"]


# --------------------------------------------------------------------------
# 狀態面漂移守衛（DEV-STATE-FACE-DRIFT-GUARD1，#65）
# --------------------------------------------------------------------------
#
# fixture 的 Log 行一律沿用各 writer 的**真實輸出格式**（assign_cmd／
# handoff_cmd／review_cmd／checkpoint_cmd／card.render_issue_body），不得
# 自創簡化格式——推導器解析的就是這些格式，fixture 偏離格式會讓測試測到
# 一個不存在的世界。

import inspect

from wf_cli.card import Card
from wf_cli.commands import handoff_cmd, open_cmd
from wf_cli.doctor import (
    HANDOFF_STAGE_EXPECTED_STATUS,
    OPEN_INITIAL_STATUS,
    REVIEW_RESULT_EXPECTED_STATUS,
    RULE_ASSIGN,
    RULE_OPEN,
    RULE_REVIEW,
    UNDECIDABLE_AMBIGUOUS_LOG,
    UNDECIDABLE_ASSIGN_NO_STATUS,
    UNDECIDABLE_FACE_UNREADABLE,
    UNDECIDABLE_HANDOFF,
    UNDECIDABLE_NO_EVENT,
    UNDECIDABLE_NO_LOG,
    UNDECIDABLE_REVIEW_INCONSISTENT,
    UNDECIDABLE_REVIEW_RESULT,
    UNDECIDABLE_UNKNOWN_EVENT,
    audit_state_face_drift,
    parse_log_events,
    render_state_face_drift,
)
from wf_cli.review import STATUS_BY_RESULT as _WRITER_STATUS_BY_RESULT


def _drift_body(*log_lines: str) -> str:
    """組一張最小卡面：標頭＋ ``## Log``。log_lines 已含時間戳、不含 ``- `` 前綴。"""
    log = "\n".join(f"- {line}" for line in log_lines)
    return (
        "- 需求：ruan6047　規劃：PM\n\n## 核心痛點\n\n- **痛點**：x\n\n"
        f"## Log\n\n{log}\n"
    )


_OPEN_LINE = "2026-08-12T10:46:32+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。"
_ASSIGN_LINE = (
    "2026-08-12T11:01:28+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code 子agent；"
    "分支worktree claude/X @ /tmp/wt；交付狀態 🔨執行中；實際能力層級 主力型（非偏離）。"
)
_HANDOFF_LINE = (
    "2026-08-12T12:41:23+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；"
    "iteration 1；SHA " + "a" * 40 + "；證據 R2 交付。"
)
_REVIEW_REJECT_LINE = (
    "2026-08-12T12:23:56+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理；"
    "core_pain_resolved no；self_run 3 項；findings 2 項（blocking 1）；counts_toward_escalation true；"
    "attempt CARD-A-e0-" + "b" * 40 + "。"
)
_REVIEW_APPROVE_LINE = (
    "2026-08-19T01:17:03+08:00 review by wf-cli → APPROVE（✅通過）；查核者 GPT-5@Copilot；"
    "core_pain_resolved yes；self_run 4 項；findings 0 項（blocking 0）；"
    "escalation_account not-asserted（preflight_basis_binding structurally-unavailable）；"
    "attempt CARD-A-e0-" + "c" * 40 + "。"
)
_AMEND_LINE = (
    "2026-08-12T12:27:51+08:00 amend by wf-cli（op 166322be）→ 核心痛點：原值「舊」→ 新值「新」；理由 r。"
)
_CHECKPOINT_LINE = (
    "2026-08-13T10:00:00+08:00 checkpoint by wf-cli → decision continue；trigger CARD-A-e0-"
    + "d" * 40 + "；unique_attempt_count 2；寫入者 ruan6047；留言 https://x/1。"
)
_BASELINE_LINE = (
    "2026-08-13T17:07:49+08:00 contract-baseline by wf-cli → contract templates/review-escalation.md；"
    "宣告者 ruan6047；留言 https://x/2。"
)


# ---- 推導表窮舉＋與寫入端釘同一性（突變注入的紅線；改錯任何一格必紅） ----


def test_drift_handoff_table_is_exhaustive_and_pinned_to_writer():
    """七個 next-stage 窮舉；前六格逐格等於 handoff_cmd.STAGE_STATUS，release 釘寫入端字面。

    卡面原文寫「三個 next-stage」，PR #102（2026-08-18）後機器現實是六個，
    WF-BACKLOG-STAGE1（2026-08-21）補上 ``backlog`` 後是七個；「窮舉」的要求管轄
    「三個」的字面（派工包修正 1）。

    ⚠️ 下面兩行釘的是**導出的同一性**（``set(...) == set(...) | {"release"}`` 與逐格
    相等），不是硬編清單——寫入端加一格會自動流進斷言，**只改一邊必紅**。
    """
    assert set(HANDOFF_STAGE_EXPECTED_STATUS) == set(handoff_cmd.STAGE_STATUS) | {"release"}
    for stage, status in handoff_cmd.STAGE_STATUS.items():
        assert HANDOFF_STAGE_EXPECTED_STATUS[stage] == status, stage
    # release 不在 STAGE_STATUS（handoff_cmd 內是獨立分支），釘住寫入端的字面：
    # 寫入端改了字面而表沒跟上時，這行必紅。
    assert HANDOFF_STAGE_EXPECTED_STATUS["release"] == "🏁完成"
    assert 'new_status = "🏁完成"' in inspect.getsource(handoff_cmd)


def test_drift_review_table_is_pinned_to_writer_status_by_result():
    assert REVIEW_RESULT_EXPECTED_STATUS == _WRITER_STATUS_BY_RESULT
    assert set(REVIEW_RESULT_EXPECTED_STATUS) == {"APPROVE", "REQUEST_CHANGES"}


def test_drift_open_initial_status_is_pinned_and_open_has_no_status_knob():
    """open 的初始狀態＝Card dataclass 預設；且 open 沒有 --status 旋鈕。

    後半是前半可推導的前提：open 若哪天長出 --status，初始狀態就不再是常數，
    這行會逼著推導器同步改成不判定。
    """
    assert OPEN_INITIAL_STATUS == Card.__dataclass_fields__["delivery_status"].default
    assert "--status" not in inspect.getsource(open_cmd)


# ---- 各動詞推導 ----


def test_drift_open_derives_requirement_and_flags_moved_face():
    """open 推導 ``💡需求``；欄位被搬到 ``📥Backlog`` 而 Log 只有 open ⇒ drift。

    ⚠️ 本卡（WF-OPEN-INITIAL-STATUS1）把這兩條斷言的語意整個反轉，逐條對照：

    - 第一條（consistent）。**舊判準**：open 之後的預期是 ``📥Backlog``，欄位停在
      ``📥Backlog`` 才算一致。**新判準**：規劃閘門在開卡**之後**才跑，開卡當下不可能
      已通過。依據是 canonical 的「規劃閘門三級制」那節（T3 列：「需求方批註放行後才進
      ``📥Backlog``」）與採用專案 cpbl 的 ROADMAP「規劃生命週期」那節（「所有新卡一律由
      ``💡需求`` 開始」）；⚠️ **不是本 repo 同名的 `docs/ROADMAP.md`**，該檔沒有這條。
      引節次標題而非節次編號：編號與行號一樣會隨改版靜默失準。
    - 第二條（drift）。**舊判準**：一張卡從 ``📥Backlog`` 移到 ``💡需求`` 是漂移——而
      那正是 PM 為了符合規劃閘門所做的**補救**，於是觀測面把合規記成異常，且與真正的
      違規（工具直接丟進 Backlog）在欄位上長得一模一樣。**新判準**：方向調轉，
      ``📥Backlog`` 才是需要一則明示事件來解釋的那一邊；沒有事件就報漂移。

    兩條都不是為了讓紅的變綠而放寬——斷言數量與強度不變（仍是逐字黃金值的三元組），
    變的只有「哪一個值是預期」。反向的鑑別力由下一個測試（明示事件在場時不得報漂移）
    補上，否則一個「永遠回 ``💡需求``」的實作也會通過本測試。
    """
    body = _drift_body(_OPEN_LINE)
    ok = audit_state_face_drift("CARD-A", body, "💡需求")
    assert (ok.verdict, ok.rule, ok.expected_status) == ("consistent", RULE_OPEN, "💡需求")
    moved = audit_state_face_drift("CARD-A", body, "📥Backlog")
    assert (moved.verdict, moved.expected_status, moved.actual_status) == ("drift", "💡需求", "📥Backlog")


def test_drift_explicit_move_to_backlog_is_consistent_and_handoff_stays_undecidable():
    """對照組：明示寫下 ``📥Backlog`` 的事件在場時，欄位是 ``📥Backlog`` 不得報漂移。

    ⚠️ 這一條是上一個測試的**反向可證偽**：只驗「open ⇒ 💡需求」會被一個「永遠回
    ``💡需求``」的推導器通過，本軸就退化成一個常數。這裡讓推導器必須真的讀事件。

    ⚠️ 卡面驗收原文寫的是「由 **handoff** 明示移到 ``📥Backlog``」，但 handoff 的 Log
    行構造上**不記** next-stage 也不記 ``--status`` 覆寫值（見 ``UNDECIDABLE_HANDOFF``
    的說明），所以 handoff 在本軸永遠落「不判定」、拿不到 ``consistent``。這與本卡無關、
    本卡也沒改它；末兩行把這個事實一併釘住，免得它日後被讀成本卡造成的。**真正逐字記下
    交付狀態的動詞是 assign**，對照組因此建在 assign 上。

    ⚠️ ``WF-BACKLOG-STAGE1``（``#120``，已合併）之後這一點**更容易被誤讀**，故明講：
    ``handoff --next-stage backlog`` 現在確實是 ``📥Backlog`` 的專責寫入者，但**寫得進去
    不等於本軸推得出來**——留痕格式沒變，末行那個 ``undecidable`` 因此不是舊事實的殘留，
    是合併後仍然成立的現況。

    ⛔ 這裡原本還有一句「若哪天 handoff 的 Log 行開始記狀態，末行會先轉紅」，**實測為假**
    （`#118` R2-002），已撤除。假在兩層：末行餵的是手打的 ``_HANDOFF_LINE`` 常數，與寫入端
    沒有連線；而且就算餵夾帶狀態的行進去，``derive_expected_status`` 對 ``handoff by wf-cli``
    開頭是**無條件短路、從不看行內容**，末行仍恆綠。⚠️ 所以本檔任何一條斷言都接不住那個
    變異——它是關於寫入端的事，得在寫入端量。真正跑得到的版本在
    ``test_commands_mocked.py`` 的 ``test_handoff_log_line_never_carries_the_status_it_wrote``。
    """
    line = _ASSIGN_LINE.replace("交付狀態 🔨執行中", "交付狀態 📥Backlog")
    moved = audit_state_face_drift("CARD-A", _drift_body(_OPEN_LINE, line), "📥Backlog")
    assert (moved.verdict, moved.rule, moved.expected_status) == ("consistent", RULE_ASSIGN, "📥Backlog")
    # 同一則事件在場、欄位卻停在 open 的初始值 ⇒ 仍須報漂移（推導器沒有偏袒 💡需求）。
    stale = audit_state_face_drift("CARD-A", _drift_body(_OPEN_LINE, line), "💡需求")
    assert (stale.verdict, stale.expected_status, stale.actual_status) == ("drift", "📥Backlog", "💡需求")
    handoff = audit_state_face_drift("CARD-A", _drift_body(_OPEN_LINE, _HANDOFF_LINE), "📥Backlog")
    assert (handoff.verdict, handoff.rule) == ("undecidable", UNDECIDABLE_HANDOFF)


def test_drift_backlog_face_needs_an_explaining_event_and_handoff_does_not_explain():
    """WF-BACKLOG-STAGE1 的雙向對照組：`📥Backlog` 欄位值不得默認通過。

    ⚠️ **為什麼三個案例都用 assign 形狀而不是 handoff 形狀**：handoff 的 Log 行不記
    ``--next-stage``（`doctor.HANDOFF_STAGE_EXPECTED_STATUS` 上方註解），所以
    ``handoff --next-stage backlog`` 對本軸構造性地不可判定——見本檔
    ``test_drift_handoff_is_undecidable_never_default_pass``，`📥Backlog` 已隨新增的
    表格自動流入該組。本測試因此驗的是**狀態面 vs 留痕**這條軸上「Backlog 有沒有事件
    依據」，這也是 #118 R1 明文接受的替代形狀。
    """
    to_backlog = _ASSIGN_LINE.replace("交付狀態 🔨執行中", "交付狀態 📥Backlog")

    # (a) 有解釋事件、欄位相符 → consistent
    ok = audit_state_face_drift("CARD-A", _drift_body(_OPEN_LINE, to_backlog), "📥Backlog")
    assert (ok.verdict, ok.rule, ok.expected_status) == ("consistent", RULE_ASSIGN, "📥Backlog")

    # (b) 對照組：欄位是 📥Backlog，但最後一筆解釋事件說的是別的值 → 仍須 drift。
    #     少了這一條，一個「永遠回 📥Backlog」的推導器也會讓 (a) 通過。
    moved = audit_state_face_drift("CARD-A", _drift_body(_OPEN_LINE, _ASSIGN_LINE), "📥Backlog")
    assert (moved.verdict, moved.expected_status, moved.actual_status) == (
        "drift", "🔨執行中", "📥Backlog",
    )

    # (c) 反向：有 Backlog 事件而欄位沒跟上（half-write）→ 也是 drift，不是 consistent。
    half = audit_state_face_drift("CARD-A", _drift_body(_OPEN_LINE, to_backlog), "🔨執行中")
    assert (half.verdict, half.expected_status, half.actual_status) == (
        "drift", "📥Backlog", "🔨執行中",
    )


def test_drift_assign_derives_the_logged_status_including_free_text_override():
    """assign 的 Log 行逐字記下寫入值，--status 自由文字覆寫因此**同樣可推導**。"""
    consistent = audit_state_face_drift("CARD-A", _drift_body(_OPEN_LINE, _ASSIGN_LINE), "🔨執行中")
    assert (consistent.verdict, consistent.rule) == ("consistent", RULE_ASSIGN)
    override_line = _ASSIGN_LINE.replace("交付狀態 🔨執行中", "交付狀態 ⏸阻塞")
    override = audit_state_face_drift("CARD-A", _drift_body(_OPEN_LINE, override_line), "🔨執行中")
    assert (override.verdict, override.expected_status, override.actual_status) == ("drift", "⏸阻塞", "🔨執行中")


def test_drift_assign_takes_the_field_not_a_later_quote_of_it():
    """交付狀態欄是格式第 3 段、先於自由文字；後段引用「；交付狀態 X」不得覆蓋。"""
    line = _ASSIGN_LINE.replace(
        "實際能力層級 主力型（非偏離）。",
        "實際能力層級 主力型（偏離理由引述他卡「；交付狀態 ✅通過；」云云）。",
    )
    finding = audit_state_face_drift("CARD-A", _drift_body(_OPEN_LINE, line), "🔨執行中")
    assert (finding.verdict, finding.expected_status) == ("consistent", "🔨執行中")


def test_drift_assign_without_status_segment_is_undecidable():
    line = "2026-08-12T11:01:28+08:00 assign by wf-cli → owner X；分支worktree b @ /w。"
    finding = audit_state_face_drift("CARD-A", _drift_body(_OPEN_LINE, line), "🔨執行中")
    assert (finding.verdict, finding.rule) == ("undecidable", UNDECIDABLE_ASSIGN_NO_STATUS)


@pytest.mark.parametrize("face", [*HANDOFF_STAGE_EXPECTED_STATUS.values(), "🛑已停止", "🚨已升級"])
def test_drift_handoff_is_undecidable_never_default_pass(face):
    """handoff 的 Log 行不含 next-stage／--status，寫入值反推不出。

    卡面驗收第 1 條的硬要求：推導不出的組合**明確落「不判定」而非默認通過**
    ——對七個 next-stage 可能寫入的每一個狀態值（外加兩個 --status 自由文字
    才寫得出的值）逐一驗證：verdict 恆為 undecidable，既不是 consistent 也
    不是 drift。

    ⚠️ parametrize 直接取 ``HANDOFF_STAGE_EXPECTED_STATUS.values()``，所以
    WF-BACKLOG-STAGE1 新增的 ``📥Backlog`` 自動進入本組：**handoff 寫出的
    Backlog 一樣落「不判定」**，這正是下方 backlog 對照組要用 assign 形狀而
    不能用 handoff 形狀的原因。
    """
    finding = audit_state_face_drift("CARD-A", _drift_body(_OPEN_LINE, _ASSIGN_LINE, _HANDOFF_LINE), face)
    assert finding.verdict == "undecidable"
    assert finding.rule == UNDECIDABLE_HANDOFF
    assert finding.expected_status is None


def test_drift_review_approve_and_reject_derive_by_result_table():
    ok = audit_state_face_drift("CARD-A", _drift_body(_OPEN_LINE, _REVIEW_APPROVE_LINE), "✅通過")
    assert (ok.verdict, ok.rule, ok.expected_status) == ("consistent", RULE_REVIEW, "✅通過")
    stuck = audit_state_face_drift("CARD-A", _drift_body(_OPEN_LINE, _REVIEW_REJECT_LINE), "🔍待查核")
    assert (stuck.verdict, stuck.expected_status, stuck.actual_status) == ("drift", "↩退回", "🔍待查核")


def test_drift_review_unknown_result_and_self_inconsistent_line_are_undecidable():
    waive = _REVIEW_REJECT_LINE.replace("REQUEST_CHANGES（↩退回）", "WAIVE（✅通過）")
    f1 = audit_state_face_drift("CARD-A", _drift_body(_OPEN_LINE, waive), "✅通過")
    assert (f1.verdict, f1.rule) == ("undecidable", UNDECIDABLE_REVIEW_RESULT)
    edited = _REVIEW_REJECT_LINE.replace("REQUEST_CHANGES（↩退回）", "APPROVE（↩退回）")
    f2 = audit_state_face_drift("CARD-A", _drift_body(_OPEN_LINE, edited), "✅通過")
    assert (f2.verdict, f2.rule) == ("undecidable", UNDECIDABLE_REVIEW_INCONSISTENT)


def test_drift_transparent_events_are_skipped_to_the_last_status_bearing_one():
    """amend／checkpoint／contract-baseline 不寫交付狀態，推導穿透它們。"""
    body = _drift_body(_OPEN_LINE, _REVIEW_REJECT_LINE, _AMEND_LINE, _BASELINE_LINE, _CHECKPOINT_LINE)
    finding = audit_state_face_drift("CARD-A", body, "↩退回")
    assert (finding.verdict, finding.rule) == ("consistent", RULE_REVIEW)
    assert finding.skipped_transparent == 3


def test_drift_unknown_last_event_is_undecidable_and_does_not_skip_past():
    """未知動詞可能寫過狀態；跳過它會把過時事件當現行依據，故 fail-closed。"""
    manual = "2026-08-13T09:00:00+08:00 PM 手動核可並調整看板（未走 wfcli）。"
    body = _drift_body(_OPEN_LINE, _ASSIGN_LINE, manual)
    finding = audit_state_face_drift("CARD-A", body, "🔨執行中")
    assert (finding.verdict, finding.rule) == ("undecidable", UNDECIDABLE_UNKNOWN_EVENT)
    assert finding.deciding_event is not None and "PM 手動核可" in finding.deciding_event


def test_drift_multiline_entry_boundaries_use_timestamped_bullets_only():
    """多段落證據（真 handoff 常態，如 #38 11:12）不得切斷事件；其後的 review 才是最後一筆。"""
    multiline_handoff = _HANDOFF_LINE + "\n\n執行者自行複驗並推翻了 PM 原記載的成因。\n- 這是證據裡的普通條列，不是新事件。"
    body = _drift_body(_OPEN_LINE, multiline_handoff, _REVIEW_APPROVE_LINE)
    events, reason = parse_log_events(body)
    assert reason is None and len(events) == 3
    finding = audit_state_face_drift("CARD-A", body, "✅通過")
    assert (finding.verdict, finding.rule) == ("consistent", RULE_REVIEW)


def test_drift_missing_log_ambiguous_log_empty_log_and_unreadable_face():
    no_log = audit_state_face_drift("CARD-A", "- 需求：x　規劃：y\n", "🔨執行中")
    assert (no_log.verdict, no_log.rule) == ("undecidable", UNDECIDABLE_NO_LOG)
    two = audit_state_face_drift("CARD-A", "## Log\n\n- x\n\n## Log\n", "🔨執行中")
    assert (two.verdict, two.rule) == ("undecidable", UNDECIDABLE_AMBIGUOUS_LOG)
    empty = audit_state_face_drift("CARD-A", "x\n\n## Log\n\n（尚無事件）\n", "🔨執行中")
    assert (empty.verdict, empty.rule) == ("undecidable", UNDECIDABLE_NO_EVENT)
    blind = audit_state_face_drift("CARD-A", _drift_body(_OPEN_LINE, _ASSIGN_LINE), None)
    assert (blind.verdict, blind.rule) == ("undecidable", UNDECIDABLE_FACE_UNREADABLE)
    assert blind.expected_status == "🔨執行中"  # 已推導的一面仍如實回報


# ---- 2026-08-12 四筆真實漂移的回放（驗收第 2 條） ----
#
# 歷史快照取不到：Projects v2 沒有欄位變更歷史的公開 API，四張卡的交付狀態
# 在修復時已被覆寫。fixture 的**忠實性論證**：``## Log`` 是 append-only，四張
# 卡今天的 Log 前綴就是漂移時點的完整 Log（修復事件全部落在其後，時間戳可
# 對）；以下事件行逐字取自 2026-08-19 讀回的真卡（證據截短、動詞／參數／
# 時間戳保留），交付狀態欄取自 #65 核心痛點的當事描述（待查核／進行中）。
# 漂移時點取需求方發問前、21:14–21:18 修復 handoff 之前（約 20:30）。
#
# **誠實結論（不粉飾）**：四筆之中三筆落「不判定」、一筆「一致」，**零筆被
# 本軸標成 drift**。成因是結構性的：這四筆的失真形態是「該發生的事件沒寫」，
# 事件缺席時 Log 與欄位一起過期、彼此一致，Log→欄位這條軸構造上看不見——
# 卡面核心痛點宣稱「Log 最後一筆事件的動詞與參數足以推導出應有狀態」對這
# 四筆並不成立（#47 的 Log 自己也說「合併從未留痕」）。本軸真正的鑑別力在
# 「事件寫了而欄位沒跟上」與「欄位被手動搬動」兩型（下兩個測試），#38 型
# 的「裁決只存在於收據」則由既有的 audit_review_channel（receipt_untranscribed）
# 承接。此結論是實測產物，詳見卡 #65 的交付報告。


def _aug12_card(card_id: str, *log_lines: str, face: str):
    return audit_state_face_drift(card_id, _drift_body(*log_lines), face)


def test_replay_38_at_drift_time_last_event_is_handoff_hence_undecidable():
    """#38：已宣告退回（收據在留言），狀態面停在 🔍待查核；Log 最後一筆是 12:41 handoff。"""
    finding = _aug12_card(
        "WF-DISPATCH-PRECHECK1",
        "2026-08-12T10:46:32+08:00 open by Claude Opus 5@Claude Code (PM)；owner 待指派；iteration 0。",
        "2026-08-12T11:01:28+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code（子 agent）；分支worktree claude/WF-DISPATCH-PRECHECK1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/wf-dispatch-precheck1；交付狀態 🚧進行中；實際能力層級 主力型（…）。",
        "2026-08-12T11:12:13+08:00 handoff by wf-cli → owner 跨家族查核（本卡規則約束 Coordinator，Coordinator 即 PM，須跨家族避免自我背書）；iteration 0；SHA 075a17ed11486218c917099b738acb5451ec955d；證據 R1：交付 templates/review-prompt.md 新增 §3.1（…）。",
        "2026-08-12T11:35:47+08:00 amend by wf-cli（op a96c569b）→ 驗收條件：原值「…」→ 新值「…」；理由 …。",
        "2026-08-12T12:02:16+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA 075a17ed11486218c917099b738acb5451ec955d；證據 …。",
        "2026-08-12T12:23:56+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼；…）；attempt WF-DISPATCH-PRECHECK1-e0-075a17ed11486218c917099b738acb5451ec955d。",
        "2026-08-12T12:27:51+08:00 amend by wf-cli（op 166322be）→ 核心痛點：原值「…」→ 新值「…」；理由 …。",
        "2026-08-12T12:28:48+08:00 handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 1；SHA 075a17ed11486218c917099b738acb5451ec955d；證據 …。",
        "2026-08-12T12:41:23+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 1；SHA 1ee62b0f2f4a3f0f5b3f0e9e8d7c6b5a4f3e2d1c；證據 …。",
        face="🔍待查核",
    )
    assert (finding.verdict, finding.rule) == ("undecidable", UNDECIDABLE_HANDOFF)


def test_replay_47_at_drift_time_reads_consistent_because_the_merge_left_no_event():
    """#47：碼早已在 main、狀態面停在 🚧進行中；Log 最後一筆是 13:50 assign（合併從未留痕）。

    assign 推導出 🚧進行中、欄位也是 🚧進行中——**一致**。失真在「真實 vs
    兩者」，不在「Log vs 欄位」；本軸對這型構造上盲，這正是「偵測不等於
    強制」必須寫進交付報告的理由（驗收第 3 條）。
    """
    finding = _aug12_card(
        "DEV-MAIN-RED-CAPABILITY-FLAGS1",
        "2026-08-12T13:47:57+08:00 open by Claude Opus 5@Claude Code PM；owner 待指派；iteration 0。",
        "2026-08-12T13:50:53+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code 子agent；分支worktree claude/DEV-MAIN-RED-CAPABILITY-FLAGS1 @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/dev-main-red-capability-flags1；交付狀態 🚧進行中；實際能力層級 主力型（…）。",
        face="🚧進行中",
    )
    assert (finding.verdict, finding.rule, finding.expected_status) == ("consistent", RULE_ASSIGN, "🚧進行中")


@pytest.mark.parametrize(
    ("card_id", "handoff_ts"),
    [("WF-EVENT-IDEMPOTENCY1-PROBE-CMD-DRIFT1", "2026-08-12T19:37:53+08:00"),
     ("WF-WORKTREE-REPO-OWNERSHIP1", "2026-08-12T19:38:16+08:00")],
)
def test_replay_52_and_57_at_drift_time_last_event_is_handoff_hence_undecidable(card_id, handoff_ts):
    """#52／#57：執行者已交回而卡未推進；Log 最後一筆是 19:37／19:38 的退回 handoff。"""
    finding = _aug12_card(
        card_id,
        "2026-08-12T17:23:37+08:00 open by Claude Opus 5@Claude Code PM；owner 待指派；iteration 0。",
        f"2026-08-12T18:00:14+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code 子agent；分支worktree claude/{card_id} @ /Users/ruanruan/Dev/ai-workflow/.claude/worktrees/x；交付狀態 🚧進行中；實際能力層級 主力型（…）。",
        "2026-08-12T18:24:41+08:00 handoff by wf-cli → owner 跨家族查核（GPT-5@Codex 子代理）；iteration 0；SHA " + "e" * 40 + "；證據 …。",
        "2026-08-12T19:25:27+08:00 review by wf-cli → REQUEST_CHANGES（↩退回）；查核者 GPT-5@Codex 子代理（需求方轉貼；…）；attempt " + card_id + "-e0-" + "e" * 40 + "。",
        f"{handoff_ts} handoff by wf-cli → owner Claude Opus 5@Claude Code 子agent；iteration 1；SHA " + "e" * 40 + "；證據 退回修正。",
        face="🚧進行中",
    )
    assert (finding.verdict, finding.rule) == ("undecidable", UNDECIDABLE_HANDOFF)


def test_equivalent_shape_38_one_event_later_verdict_transcribed_face_stuck_is_drift():
    """#38 型往前一步的等價形：裁決一旦轉錄（review ↩退回）而欄位沒跟上 → drift。

    忠實性：這正是 wfcli review 三次遠端寫入無交易性下「留言＋Log 成功、
    欄位失敗」的 half-write 實體，也是 #38 的失真在裁決被轉錄那一刻的樣子。
    本軸抓得到它——這是「鑑別力」的正面證明，與上面四筆回放的反面結論成對。
    """
    body = _drift_body(_OPEN_LINE, _ASSIGN_LINE.replace("🔨執行中", "🚧進行中"), _REVIEW_REJECT_LINE)
    finding = audit_state_face_drift("WF-DISPATCH-PRECHECK1", body, "🔍待查核")
    assert (finding.verdict, finding.expected_status, finding.actual_status) == ("drift", "↩退回", "🔍待查核")


def test_equivalent_shape_47_manual_board_move_without_event_is_drift():
    """#47 型的鏡像：欄位被手動搬到 📦已合併 而沒有任何事件 → drift。

    忠實性：#47 的修復若當時用手搬看板（而非補 handoff），本檢查在下一次
    doctor 就會報——「手動搬看板」正是本卡要讓其可被列舉的操作形態。
    """
    body = _drift_body(
        "2026-08-12T13:47:57+08:00 open by Claude Opus 5@Claude Code PM；owner 待指派；iteration 0。",
        "2026-08-12T13:50:53+08:00 assign by wf-cli → owner Claude Opus 5@Claude Code 子agent；分支worktree claude/DEV-MAIN-RED-CAPABILITY-FLAGS1 @ /w；交付狀態 🚧進行中；實際能力層級 主力型（…）。",
    )
    finding = audit_state_face_drift("DEV-MAIN-RED-CAPABILITY-FLAGS1", body, "📦已合併")
    assert (finding.verdict, finding.expected_status, finding.actual_status) == ("drift", "🚧進行中", "📦已合併")


def test_drift_render_reports_counts_share_and_itemizes_only_noteworthy_cards():
    findings = [
        # C1 一致／C2 漂移：兩者依 WF-OPEN-INITIAL-STATUS1 對調——open 的預期值改為
        # 💡需求，故停在 📥Backlog 的那張才是需要事件解釋的。計數與逐條列出的判準不變。
        audit_state_face_drift("C1", _drift_body(_OPEN_LINE), "💡需求"),
        audit_state_face_drift("C2", _drift_body(_OPEN_LINE), "📥Backlog"),
        audit_state_face_drift("C3", _drift_body(_OPEN_LINE, _ASSIGN_LINE, _HANDOFF_LINE), "🔍待查核"),
    ]
    text = render_state_face_drift(findings)
    assert "一致 1／漂移 1／不判定 1（不判定佔比 33%）" in text
    assert "[drift/open_initial] C2" in text
    assert f"[undecidable/{UNDECIDABLE_HANDOFF}] C3" in text
    assert "C1" not in text  # 一致的卡不逐條列出
    assert "#48" in text  # 強制面承接者必須寫在輸出裡，不只寫在文件裡


# --------------------------------------------------------------------------
# WF-REVIEW-RECEIPT-CHANNEL1：身分依據的據實標註（需求方 2026-08-19 裁定「丙＋甲的殘留」）
#
# 收據紀律已從派工包移除，因為跨家族查核者沒有 GitHub 寫入通道、收據構造上取不到。
# 殘留的配套是：doctor **不報錯、不改判定**，但要讓 recorded 不再讀起來像「身分已
# 驗證」。以下測試同時釘住兩件事——標註要出現，且它不得升格成警告或阻擋。
# --------------------------------------------------------------------------

_RECEIPT = f"<!-- wf-review-receipt:v1\ncard_id: {_ECARD}\nsource_sha: {_ESHA}\n-->"


def test_zero_receipt_recorded_still_recorded_but_marks_identity_as_endorsed():
    """零收據：判定不變（recorded），但身分依據標成需求方背書。

    這是 2026-08-19 五筆跨家族裁決的實際形態：--reviewer 是自由字串、收據數 0，
    而三面一致——因為三面都是 PM 寫的。
    """
    finding = audit_review_channel(
        [{"body": _verdict(_conformant_marker())}], _ECARD, _ESHA,
        card_body=_ELOG, delivery_status="✅通過",
    )
    assert finding.status == "recorded", "標註不得改變判定（改了就是退回甲）"
    assert finding.identity_basis == "requester_endorsed"
    assert "非機械可驗" in finding.detail
    assert "需求方背書" in finding.detail
    assert finding.receipt_urls == ()


def test_receipt_backed_recorded_is_distinguishable_from_free_string_recorded():
    """有收據且 card_id／source_sha 相符並已轉錄：身分依據＝平台可驗證的 author。

    先前這兩種 recorded 的輸出**逐字相同**（收據在 recorded 路徑上被丟棄），
    讀者無從分辨身分憑什麼成立——正是本卡要修的誤讀。
    """
    endorsed = audit_review_channel(
        [{"body": _verdict(_conformant_marker())}], _ECARD, _ESHA,
        card_body=_ELOG, delivery_status="✅通過",
    )
    backed = audit_review_channel(
        [{"body": _verdict(_conformant_marker())},
         {"body": _RECEIPT, "html_url": "https://x/r1", "user": {"login": "copilot-reviewer"}}],
        _ECARD, _ESHA, card_body=_ELOG, delivery_status="✅通過",
    )
    assert (endorsed.status, backed.status) == ("recorded", "recorded")
    assert backed.identity_basis == "receipt_backed"
    assert backed.receipt_urls == ("https://x/r1",)
    assert backed.receipt_authors == ("copilot-reviewer",)
    assert "GitHub comment author" in backed.detail
    assert backed.detail != endorsed.detail, "兩種身分依據的輸出必須可分辨"


def test_identity_annotation_is_not_a_warning_and_not_a_gate():
    """推翻條件的反面：標註不得改變 status，故 --strict 的 exit code 不受影響。

    doctor_cmd 的 exit code 只看 ``status != "recorded"``（doctor_cmd.py:264），
    所以「不阻擋」這件事等價於「零收據的 recorded 仍是 recorded」。有收據與零收據
    兩種輸入的 status／expected／actual 三欄逐欄相同，才叫判定不受身分依據影響。
    """
    endorsed = audit_review_channel(
        [{"body": _verdict(_conformant_marker())}], _ECARD, _ESHA,
        card_body=_ELOG, delivery_status="✅通過",
    )
    backed = audit_review_channel(
        [{"body": _verdict(_conformant_marker())},
         {"body": _RECEIPT, "html_url": "https://x/r3", "user": {"login": "rev"}}],
        _ECARD, _ESHA, card_body=_ELOG, delivery_status="✅通過",
    )
    judgment = lambda f: (f.status, f.expected_delivery_status, f.actual_delivery_status)
    assert judgment(endorsed) == judgment(backed) == ("recorded", "✅通過", "✅通過")
    # 措辭層面：標註必須自述「不改變判定」，否則讀者仍可能把它當成該處理的告警。
    assert "不改變上面的判定" in endorsed.detail
    assert "不是缺陷" in endorsed.detail


def test_half_written_also_carries_the_identity_basis():
    """裁決已被採認但狀態欄沒跟上時，身分維度的疑問與 recorded 完全一樣。"""
    finding = audit_review_channel(
        [{"body": _verdict(_conformant_marker())}], _ECARD, _ESHA,
        card_body=_ELOG, delivery_status="🔍待查核",
    )
    assert finding.status == "half_written"
    assert finding.identity_basis == "requester_endorsed"
    assert "非機械可驗" in finding.detail


def test_no_verdict_adopted_means_no_identity_claim():
    """unobservable／marker_quarantined 沒有採認任何裁決，就沒有「身分憑什麼」可談。

    在這裡標身分依據會反過來暗示有個結論成立了，所以維持 not_applicable。
    """
    unobservable = audit_review_channel([], _ECARD, _ESHA)
    quarantined = audit_review_channel(
        [{"body": f"<!-- wf-review-event:v2 card_id={_ECARD} source_sha={_ESHA} attempt_id={_EATT} -->"}],
        _ECARD, _ESHA, card_body=_ELOG, delivery_status="✅通過",
    )
    assert unobservable.status == "unobservable"
    assert quarantined.status == "marker_quarantined"
    assert unobservable.identity_basis == "not_applicable"
    assert quarantined.identity_basis == "not_applicable"


def test_untranscribed_receipt_reports_receipt_backed_identity():
    finding = audit_review_channel(
        [{"body": _RECEIPT, "html_url": "https://x/r2", "user": {"login": "copilot-reviewer"}}],
        _ECARD, _ESHA,
    )
    assert finding.status == "receipt_untranscribed"
    assert finding.identity_basis == "receipt_backed"
    assert "GitHub comment author" in finding.detail


def test_identity_basis_reaches_the_json_payload():
    """機器消費端要拿得到；文字面走 detail，機器面走 --json 的 review_channel 鍵。"""
    from wf_cli.commands.doctor_cmd import build_json_payload

    finding = audit_review_channel(
        [{"body": _verdict(_conformant_marker())}], _ECARD, _ESHA,
        card_body=_ELOG, delivery_status="✅通過",
    )
    report = DoctorReport(repo_root=".", generated_at="t", registry_sources=[])
    payload = build_json_payload(report, finding)
    assert payload["review_channel"]["identity_basis"] == "requester_endorsed"


# ---- canonical 引用的形狀守衛（R2-001） --------------------------------
#
# `doctor.py` 原本手寫「canonical 檔名 ＋ 冒號 ＋ 行號」。行號在 canonical 插行時
# **靜默失準**，而且已經失準三輪（#119 抓到既存漂移、#120 自己插兩行又推歪一批）。
# 引用改成條文原文片段之後，由下面兩條負責讓失準**轉紅**而不是繼續爛在註解裡。

# ⚠️ 路徑索引與檔名刻意拆兩行：下面那條守衛不准「點名 canonical 的行夾帶數字」，
# 而 `parents[...]` 的索引就是數字——寫成一行會自己打自己（實測會紅）。
_REPO_ROOT = Path(__file__).resolve().parents[2]
_CANONICAL_PATH = _REPO_ROOT / "AI_WORKFLOW.md"
_CITING_SOURCES = (
    _REPO_ROOT / "cli" / "src" / "wf_cli" / "doctor.py",
    Path(__file__).resolve(),
)


def _enclosing_h2(lines: list[str], index: int) -> str | None:
    """`index` 這一行往回找到的最近一個 `##` 級標題。`###` 不算（不是節，是小節）。"""
    for probe in range(index, -1, -1):
        if lines[probe].startswith("## "):
            return lines[probe]
    return None


def test_canonical_anchors_are_verbatim_and_in_the_cited_section():
    """⭐ 錨點必須是**驗得到的**：片段要逐字、唯一，且真的落在所引的那一節底下。

    ⚠️ 驗得到：片段被改寫／被刪／出現多筆（定位變歧義）／被搬去別節；宣告了卻沒人
    用的死錨點。
    ⚠️ 驗不到（明說）：條文語意被改寫而片段字串原封不動時**仍然全綠**——它比對的是
    字串在不在，不是條文說了什麼。整條規則被反轉、只要這一小段主詞句還在就不會響。
    """
    text = _CANONICAL_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    assert text.count(CANONICAL_SECTION_HEADING) == 1, "節標題必須唯一，否則節次定位有歧義"
    assert CANONICAL_SECTION == "§" + CANONICAL_SECTION_HEADING.removeprefix("## ").split(".", 1)[0]

    assert set(CANONICAL_ANCHORS) == {ANCHOR_FLOOR, ANCHOR_MERGE, ANCHOR_BLOCK}

    doctor_src = _CITING_SOURCES[0].read_text(encoding="utf-8")
    for key, name in ((ANCHOR_FLOOR, "ANCHOR_FLOOR"), (ANCHOR_MERGE, "ANCHOR_MERGE"),
                      (ANCHOR_BLOCK, "ANCHOR_BLOCK")):
        fragment = CANONICAL_ANCHORS[key]
        hits = [i for i, ln in enumerate(lines) if fragment in ln]
        assert len(hits) == 1, f"{name} 的片段在 canonical 出現 {len(hits)} 次，必須恰好一次"
        assert _enclosing_h2(lines, hits[0]) == CANONICAL_SECTION_HEADING, (
            f"{name} 的條文已不在 {CANONICAL_SECTION_HEADING} 底下"
        )
        # 死錨點檢查：扣掉常數定義與 `CANONICAL_ANCHORS` 的鍵之後，至少還要有一處
        # 真正的引用。⚠️ 不能用出現次數門檻——各錨點的引用數不同，門檻要嘛太鬆
        # （拿掉一處仍過）要嘛太緊（實測：`>= 3` 的版本殺不掉「拿掉一處引用」的變異）。
        cites = [
            ln for ln in doctor_src.splitlines()
            if name in ln
            and not ln.startswith(f"{name} = ")
            and not ln.strip().startswith(f"{name}:")
        ]
        assert cites, f"{name} 已無人引用，該刪掉或該補回引用"

        cite = canonical_cite(key)
        assert fragment in cite and CANONICAL_SECTION in cite


def test_canonical_citations_do_not_regrow_line_numbers():
    """引用長回行號形態時轉紅——這是同族第四次的預防，不是本次的修補。

    判準刻意取**封閉集合**：凡是點名 canonical 檔名的那一行，就不准同時帶任何數字。
    這比「掃某個特定寫法的 regex」強——`§6:220`、`第 220 行`、`L220` 都一樣會被抓到，
    不必事先窮舉寫法。代價是節次也得走 `CANONICAL_SECTION` 而不能手寫，這正是要的。

    ⚠️ 射程只有 `doctor.py` 與本檔——這兩支引用 canonical 時不帶節次數字，才禁得起
    「任何數字」這種判準。散文（`docs/`、`cleanup.py`、`handoff_cmd.py`）的引用長成
    `§4.1「原文片段」`，節次本身就有數字，改由下面那條以**行號形態**為準檢查。
    """
    offenders: list[str] = []
    for path in _CITING_SOURCES:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "AI_WORKFLOW" in line and any(ch.isdigit() for ch in line):
                offenders.append(f"{path.name}:{lineno}: {line.strip()}")
    assert not offenders, "點名 canonical 的行不得夾帶數字（行號會靜默失準）：\n" + "\n".join(offenders)



# ---- 散文引用的行號守衛已升級為全 repo 掃描 ------------------------------
#
# R3–R5 在此維護一份 `_PROSE_CITERS` **寫死清單**。那個形狀壞在構造上：新增引用
# canonical 的檔案不會自動納管，得有人記得手動加——而它**已經漏掉過真實缺陷**
# （`snapshots/README.md` 與 `scripts/daily_snapshot.sh` 兩處都壞著、都不在清單裡）。
#
# R6 依需求方裁定改成**開放集合 ＋ 明文排除集**：判準與清單搬到
# `scripts/canonical_citation_scan.py`，守衛在
# `cli/tests/test_canonical_citation_scan.py`，射程是 `git ls-files` 全部。
# 判準本身沒變（仍是「剪掉指名來源檔的引用之後還剩不剩冒號數字」），只是不再由
# 一份人維護的清單決定掃誰。


# --------------------------------------------------------------------------
# 事後符合性重驗（WF-POSTHOC-CONFORMANCE1，canonical §5.1.2）
# --------------------------------------------------------------------------
#
# ⚠️ 本組的 fixture 一律沿用**真實卡面的形狀**：標頭兩行（`- 需求：…　規劃：…` 與
# `- Initiative：…　spec 基線：…`）、`<!-- wf-routing:v1 -->` 標記、`## 核心痛點`
# 章節、資源宣告哨兵、`## Log`。實測 199 張活卡中相當比例缺其中某一項，⇒ 缺哪一項
# 是本檢查要判的東西本身，fixture 偏離真實形狀會讓測試測到一個不存在的世界。

from wf_cli.doctor import (
    CAUSE_CHANNEL_BYPASSED,
    CAUSE_DISPOSITIONS,
    CAUSE_RULE_CHANGED,
    CAUSE_TOOL_CANNOT_READ,
    CAUSE_UNDECIDABLE,
    CAUSE_WRITER_NONCONFORMANT,
    CONFORMANCE_CAUSES,
    CONFORMANCE_RULES,
    CREATED_AT_TRUSTED_FROM,
    DISPOSITION_ACCEPT_AS_LEGACY,
    DISPOSITION_MIGRATE,
    EXISTENCE_FROM_ISSUE,
    EXISTENCE_FROM_LOG,
    EXISTENCE_UNKNOWN,
    FIELD_DECLARED_UNUSED,
    FIELD_ORPHAN_VALUED,
    PROJECT_BUILTIN_FIELDS,
    RULE_EPOCH_BY_ID,
    STATE_FACE_DRIFT_EPOCH,
    VERB_AMEND_BRIEF,
    VERB_AMEND_CORE_PAIN,
    VERB_AMEND_RESOURCES,
    VERB_AMEND_SPEC_BASELINE,
    VERB_APPEND_ONLY,
    VERB_ASSIGN,
    ExistenceTime,
    attribute_cause,
    audit_conformance,
    audit_field_surface,
    audit_reachability,
    audit_state_face_drift_batch,
    evaluate_card_conformance,
    existence_time_of,
    has_channel_evidence,
    predates_rule,
    probe_reachability,
    render_conformance,
    render_reachability,
    scan_envelope,
)

_ROUTING = "<!-- wf-routing:v1 -->"
_RESOURCES = (
    "## 資源宣告\n<!-- resource-claims:begin -->\n```json\n"
    '{\n  "db_scope": "none",\n  "resources": []\n}\n'
    "```\n<!-- resource-claims:end -->\n"
)


def _conformant_body(*log_lines: str, pain: str = "x", brief: bool = True) -> str:
    """一張各項齊備的卡面（形狀取自 `card.render_issue_body` 的實際輸出）。"""
    head = (
        "- 需求：ruan6047　規劃：PM\n"
        f"{_ROUTING}\n"
        "- 執行：待指派　查核：待指派\n"
        "- Initiative：—　spec 基線：—\n"
        "- DB：db_scope=none\n"
        "- 服務的原始目標：讓事後重驗有東西可驗\n\n"
    )
    if brief:
        head += (
            "## 簡介\n<!-- card-brief:begin -->\n"
            "做什麼：測試用卡。適用時機：跑本組測試時。⛔ 非射程：其他。\n"
            "<!-- card-brief:end -->\n\n"
        )
    head += f"## 核心痛點\n\n- **痛點**：{pain}\n\n{_RESOURCES}\n"
    log = "\n".join(f"- {line}" for line in log_lines)
    return head + f"## Log\n\n{log}\n"


#: 一筆晚於全部 rule epoch 的 open 事件（2026-08-26）。
_LATE_OPEN = "2026-08-26T09:00:00+08:00 open by wf-cli；owner 待指派；iteration 0。"
#: 一筆早於全部 rule epoch 的 open 事件（2026-08-01）。
_EARLY_OPEN = "2026-08-01T09:00:00+08:00 open by wf-cli；owner 待指派；iteration 0。"


def test_five_causes_are_a_closed_ordered_set_with_a_disposition_each():
    """值域恰五類、順序即判準順序，且每一類都說得出處置。

    **突變檢驗**：增刪任一類、或調換 `CONFORMANCE_CAUSES` 的順序，本測試轉紅。
    """
    assert CONFORMANCE_CAUSES == (
        CAUSE_TOOL_CANNOT_READ,
        CAUSE_UNDECIDABLE,
        CAUSE_RULE_CHANGED,
        CAUSE_WRITER_NONCONFORMANT,
        CAUSE_CHANNEL_BYPASSED,
    )
    assert set(CAUSE_DISPOSITIONS) == set(CONFORMANCE_CAUSES), "每一類都要有處置文案"
    # 前兩類是我們自己的侷限，⛔ 不得寫成對人的指控。
    for limitation in (CAUSE_TOOL_CANNOT_READ, CAUSE_UNDECIDABLE):
        assert "⛔ 不" in CAUSE_DISPOSITIONS[limitation]


def test_tool_cannot_read_outranks_every_accusation():
    """⭐ **順序的變異檢驗**：讀不到的卡永遠先落 `tool_cannot_read`。

    這張卡同時滿足後面兩類的全部前提（晚於 epoch、有通道留痕）。判準順序若把
    `tool_cannot_read` 從第一順位移到最後，它會改被報成 `writer_nonconformant`
    ——也就是把「我們的解析器讀不到」講成「寫入端做錯了」。

    **突變檢驗**：把 `attribute_cause` 的 `if not tool_readable` 那段移到函式最後，
    本測試轉紅（第一個 assert）。⛔ 只跑正確順序是零資訊，故第二個 assert 逐字給出
    移位後的答案，證明兩者真的不同。
    """
    late = ExistenceTime("2026-08-26T09:00:00+08:00", EXISTENCE_FROM_LOG)
    epoch = RULE_EPOCH_BY_ID["core_pain_present"].epoch
    assert attribute_cause(
        tool_readable=False, existence=late, epoch=epoch, channel_evidenced=True
    ) == CAUSE_TOOL_CANNOT_READ
    # 同一張卡，只把「讀得到」這件事翻過來 → 落到指控那一側。
    assert attribute_cause(
        tool_readable=True, existence=late, epoch=epoch, channel_evidenced=True
    ) == CAUSE_WRITER_NONCONFORMANT


def test_undecidable_outranks_accusation_when_the_card_has_no_time():
    """取不到建立時刻時落 `undecidable`，⛔ 不猜、⛔ 不落到指控那兩類。"""
    unknown = ExistenceTime(None, EXISTENCE_UNKNOWN)
    for channel in (True, False):
        assert attribute_cause(
            tool_readable=True,
            existence=unknown,
            epoch=RULE_EPOCH_BY_ID["brief_present"].epoch,
            channel_evidenced=channel,
        ) == CAUSE_UNDECIDABLE


def test_writer_nonconformant_and_channel_bypassed_split_on_channel_evidence():
    """後兩類互斥且窮盡：走到第 4 步時，卡要嘛有通道留痕、要嘛沒有。"""
    late = ExistenceTime("2026-08-26T09:00:00+08:00", EXISTENCE_FROM_LOG)
    epoch = RULE_EPOCH_BY_ID["brief_present"].epoch
    assert attribute_cause(
        tool_readable=True, existence=late, epoch=epoch, channel_evidenced=True
    ) == CAUSE_WRITER_NONCONFORMANT
    assert attribute_cause(
        tool_readable=True, existence=late, epoch=epoch, channel_evidenced=False
    ) == CAUSE_CHANNEL_BYPASSED


def test_channel_bypassed_branch_is_reachable_on_a_constructed_card():
    """⭐ 母體實測 **0 筆**，⇒ 不構造就永遠測不到這條分支是否可達。

    形狀：卡晚於規則、卡面有 `## Log` 區段但裡頭一筆通道事件都沒有（欄位被手搬）。
    ⛔ 「掃到 0 筆」與「這條分支根本走不到」在輸出上長得一樣，本測試把兩者分開。
    """
    hand_moved = _conformant_body(
        "2026-08-26T09:00:00+08:00 手動更新交付狀態（無對應動詞）。", brief=False
    )
    assert has_channel_evidence(hand_moved) is False
    findings = evaluate_card_conformance(
        "CARD-HAND",
        hand_moved,
        service_goal="有",
        issue_created_at="2026-08-26T08:00:00+08:00",
    )
    assert [f.rule_id for f in findings] == ["brief_present"]
    assert findings[0].cause == CAUSE_CHANNEL_BYPASSED


def test_existence_time_prefers_the_log_open_event_over_issue_created_at():
    body = _conformant_body(_EARLY_OPEN)
    got = existence_time_of(body, "2026-08-04T12:00:00+08:00")
    assert (got.value, got.source) == ("2026-08-01T09:00:00+08:00", EXISTENCE_FROM_LOG)


def test_existence_time_falls_back_to_created_at_then_to_unknown():
    without_open = _conformant_body(
        "2026-08-20T09:00:00+08:00 handoff by wf-cli → owner X；iteration 0；SHA "
        + "a" * 40
        + "；證據 y。"
    )
    fallback = existence_time_of(without_open, "2026-08-20T08:00:00+08:00")
    assert (fallback.value, fallback.source) == (
        "2026-08-20T08:00:00+08:00",
        EXISTENCE_FROM_ISSUE,
    )
    assert existence_time_of(without_open, None).source == EXISTENCE_UNKNOWN


def test_created_at_cannot_judge_epochs_before_the_state_plane_cutover():
    """⭐ createdAt 退路的**邊界**（⛔ 只驗 happy path 是零資訊）。

    2026-08-04 遷移卡的 Issue 建立於遷移當天，而它承載的工作早於它 ⇒ 拿它去比
    cutover 之前落地的規則，必然把整批遷移卡判成「晚於規則卻仍不合規」。本測試
    釘住那條界線：**同一張卡、同一個時刻**，只換 `source` 就換答案。
    """
    migrated = ExistenceTime("2026-08-04T14:00:00+08:00", EXISTENCE_FROM_ISSUE)
    before_cutover = RULE_EPOCH_BY_ID["core_pain_present"].epoch  # 2026-08-04T22:53:12
    assert before_cutover < CREATED_AT_TRUSTED_FROM, "夾具前提：該 epoch 早於 cutover"
    assert predates_rule(migrated, before_cutover) is None, "⛔ 不得用 createdAt 判定"
    # 同一個時刻若來自 Log 的 open 事件（可信），就判得出來。
    from_log = ExistenceTime("2026-08-04T14:00:00+08:00", EXISTENCE_FROM_LOG)
    assert predates_rule(from_log, before_cutover) is True
    # 而 cutover 之後的規則，createdAt 仍然是有效答案 —— ⛔ 不是一律作廢。
    after_cutover = RULE_EPOCH_BY_ID["brief_present"].epoch
    assert predates_rule(migrated, after_cutover) is True


def test_migration_card_lands_on_undecidable_not_on_an_accusation():
    """把上一條接到端到端：只有 createdAt 的遷移卡 → `undecidable`，⛔ 非指控。"""
    migrated = _conformant_body(
        "2026-08-04T14:00:00+08:00 migrated by OPS-STATE-PLANE-MIG1。",
        pain="",
        brief=False,
    )
    findings = evaluate_card_conformance(
        "MIG-CARD", migrated, service_goal="有", issue_created_at="2026-08-04T14:00:00+08:00"
    )
    core_pain = [f for f in findings if f.rule_id == "core_pain_present"]
    assert len(core_pain) == 1
    assert core_pain[0].cause == CAUSE_UNDECIDABLE
    assert core_pain[0].created_at_source == EXISTENCE_FROM_ISSUE


def test_every_rule_epoch_declares_a_disposition_and_a_full_timestamp():
    """⭐ epoch 必須是**完整 ISO-8601 時刻**、disposition 必須是宣告過的兩個值之一。

    日期粒度不夠：路由行的規則卡是 13:01:38，而本檢查比對的標記字面由同日 18:29:56
    引入，晚 5.5 小時；用日期比會多判 5 張。

    **突變檢驗**：把任一條的 `epoch` 截成 `YYYY-MM-DD`，或把 `disposition` 改成
    第三個值，本測試轉紅。
    """
    assert CONFORMANCE_RULES, "清冊不得為空——空清冊是一個永遠不會響的偵測器"
    for rule in CONFORMANCE_RULES:
        assert rule.disposition in (DISPOSITION_MIGRATE, DISPOSITION_ACCEPT_AS_LEGACY)
        assert _parse_iso_or_none(rule.epoch) is not None, f"{rule.rule_id} 的 epoch 不可解析"
        assert len(rule.epoch) >= len("2026-08-04T22:53:12+08:00"), (
            f"{rule.rule_id} 的 epoch 只有日期粒度"
        )
        assert rule.artifact and rule.requirement
    assert len({r.rule_id for r in CONFORMANCE_RULES}) == len(CONFORMANCE_RULES)


def _parse_iso_or_none(value):
    from wf_cli.doctor import _parse_iso

    return _parse_iso(value)


def test_accept_as_legacy_only_gets_a_summary_line_while_migrate_is_itemized():
    """⭐ disposition 的兩個取值各驗一次，並**對照**兩份輸出。

    `migrate` 的殘餘逐張列出（那是待辦）；`accept_as_legacy` 的只有一行摘要
    （需求方已裁定不追溯，逐張列會製造一個永遠清不掉的池）。
    """
    # 缺路由標記（accept_as_legacy）＋缺簡介（migrate）的兩張早期卡。
    bodies = {
        cid: _conformant_body(_EARLY_OPEN, brief=False).replace(_ROUTING + "\n", "")
        for cid in ("CARD-A", "CARD-B")
    }
    report = audit_conformance(bodies, {cid: {"服務的原始目標": "有"} for cid in bodies})
    itemized = {(f.card_id, f.rule_id) for f in report.findings}
    assert itemized == {
        ("CARD-A", "brief_present"),
        ("CARD-B", "brief_present"),
    }, "migrate 的殘餘要逐張；accept_as_legacy 的⛔ 不得出現在 findings"
    assert len(report.accepted_as_legacy) == 1
    summary = report.accepted_as_legacy[0]
    assert "routing_marker_present" in summary and "2 張殘餘" in summary
    text = render_conformance(report)
    assert "CARD-A" in text and "CARD-B" in text  # migrate：逐張
    assert text.count("routing_marker_present") == 1  # accept_as_legacy：只有摘要那一行


def test_conformance_reports_not_scanned_rather_than_clean_when_given_nothing():
    """⛔ 沒掃不得被讀成乾淨——這是本檔三個既有掃描共用的立場。"""
    for empty in (None, {}):
        report = audit_conformance(empty)
        assert (report.status, report.findings) == ("not_scanned", [])
        assert "未掃描" in render_conformance(report) and "這不等於沒有" in render_conformance(report)


def test_zero_findings_for_a_rule_is_reported_as_scanned_not_silent():
    """⭐ 「掃過而零命中」必須印出來。

    一條規則零命中有兩種可能：真的沒有，或這條規則構造上不會響。輸出上長得一樣，
    ⇒ 報告要逐規則給數字，讓讀者至少看得到它被跑過。
    """
    body = _conformant_body(_LATE_OPEN)
    report = audit_conformance({"CARD-OK": body}, {"CARD-OK": {"服務的原始目標": "有"}})
    assert report.findings == []
    text = render_conformance(report)
    for rule in CONFORMANCE_RULES:
        if rule.disposition == DISPOSITION_MIGRATE:
            assert f"`{rule.rule_id}`" in text
    assert "⛔ 這不等於此規則不會響" in text


def test_conformance_finding_carries_both_timestamps_for_git_archaeology():
    """`writer_nonconformant` 追得下去的唯一依據是兩個時刻。

    狀態面沒有工具版本可查（`pyproject` 的 version 凍在 0.1.0、`wfcli` 無 `--version`、
    Log 行只寫 `by wf-cli`）⇒ 接手的人只能拿 rule_epoch 與卡的建立時刻做 commit 時序
    考古。兩者缺一，這一類就只是一句沒有下文的指控。
    """
    late = _conformant_body(_LATE_OPEN, brief=False)
    findings = evaluate_card_conformance("CARD-LATE", late, service_goal="有")
    assert len(findings) == 1
    finding = findings[0]
    assert finding.cause == CAUSE_WRITER_NONCONFORMANT
    assert finding.rule_epoch == RULE_EPOCH_BY_ID["brief_present"].epoch
    assert finding.card_created_at == "2026-08-26T09:00:00+08:00"
    assert finding.created_at_source == EXISTENCE_FROM_LOG


def test_core_pain_is_read_from_the_section_not_from_the_log_echo():
    """⛔ 判準只看 `## Log` **之前**的章節。

    真實形狀：handoff／review 事件的證據欄是**多行自由文字**，實務上會整段引用卡面
    ——包含 `## 核心痛點` 標題行與它底下的 `- **痛點**：`。一張**根本沒有**該章節的卡，
    若判準對全文搜尋，就會讀到 Log 裡的歷史回音而被判成合規：那是假陰性，而假陰性正是
    「偵測器永遠不會響」的那一半。

    **突變檢驗**：把 `_core_pain_value` 裡的 `split_at_log` 拿掉、改對全文 splitlines，
    本測試轉紅（第一個 assert 會變成空 findings）。

    第二個 assert 釘的是另一件事：**單行**的 amend 回音（`原值「- **痛點**：…」`）
    同樣不得被當成現值——那條由章節切界承接。
    """
    quoted_section = (
        "2026-08-20T09:00:00+08:00 handoff by wf-cli → owner X；iteration 1；SHA "
        + "a" * 40
        + "；證據 交付時的卡面原文如下：\n\n## 核心痛點\n\n- **痛點**：Log 裡的歷史回音\n"
    )
    no_section = (
        "- 需求：ruan6047　規劃：PM\n"
        f"{_ROUTING}\n"
        "- Initiative：—　spec 基線：—\n"
        "- 服務的原始目標：有\n\n"
        f"{_RESOURCES}\n"
        f"## Log\n\n- {_EARLY_OPEN}\n- {quoted_section}\n"
    )
    assert "## 核心痛點" in no_section, "夾具前提：字面確實出現在 Log 內"
    findings = evaluate_card_conformance("CARD-ECHO", no_section, service_goal="有")
    assert "core_pain_present" in [f.rule_id for f in findings], (
        "Log 內的章節回音⛔ 不得讓一張缺痛點的卡看起來合規"
    )

    single_line_echo = _conformant_body(
        _EARLY_OPEN,
        "2026-08-02T09:00:00+08:00 amend by wf-cli（op deadbeef）→ 核心痛點："
        "原值「- **痛點**：舊的痛點原文」。",
        pain="",
    )
    assert "core_pain_present" in [
        f.rule_id
        for f in evaluate_card_conformance("CARD-ECHO2", single_line_echo, service_goal="有")
    ]


def test_conformance_never_blocks_and_says_so_in_the_report():
    """⛔ 事後重驗非阻擋：它是唯讀報告，⛔ 不得讓既有卡因 canonical 改版而動不了。"""
    broken = "沒有任何章節的卡面"
    findings = evaluate_card_conformance("CARD-BROKEN", broken)
    assert findings, "壞掉的卡要被報出來"
    assert {f.cause for f in findings} == {CAUSE_TOOL_CANNOT_READ} or {
        f.cause for f in findings
    } == {CAUSE_UNDECIDABLE}
    report = audit_conformance({"CARD-BROKEN": broken})
    assert "⛔ 本節不修復、不阻擋" in render_conformance(report)


# ---- 欄位層對帳 ----------------------------------------------------------


def test_field_surface_reports_orphan_valued_fields_in_its_own_section():
    """⭐ 孤兒欄位是**狀態面本身**的形狀問題 ⇒ 一個欄位一筆，⛔ 不是 41 張卡各一筆。"""
    values = {
        f"CARD-{i}": {"卡ID": f"CARD-{i}", "分支／worktree": "b @ /w", "Title": "t"}
        for i in range(41)
    }
    report = audit_field_surface(values, ("卡ID", "分支worktree"))
    orphans = [f for f in report.findings if f.kind == FIELD_ORPHAN_VALUED]
    assert [(f.field_name, f.cards_with_value) for f in orphans] == [("分支／worktree", 41)]
    assert "Title" in PROJECT_BUILTIN_FIELDS and "Title" not in {
        f.field_name for f in report.findings
    }, "GitHub 內建欄位⛔ 不得被報成孤兒"


def test_field_surface_declared_but_unused_branch_is_reachable():
    """⭐ **負控**：(ii) 分支實測母體為 0，⇒ 不構造就永遠測不到。"""
    report = audit_field_surface({"CARD-1": {"卡ID": "CARD-1"}}, ("卡ID", "從沒人填過的欄位"))
    unused = [f for f in report.findings if f.kind == FIELD_DECLARED_UNUSED]
    assert [f.field_name for f in unused] == ["從沒人填過的欄位"]


def test_field_surface_treats_blank_values_as_absent():
    """空字串不算「有值」——否則佔位符會讓孤兒欄位看起來還活著。"""
    report = audit_field_surface({"C": {"孤兒": "   ", "卡ID": "C"}}, ("卡ID",))
    assert report.findings == []


def test_field_surface_not_scanned_is_not_clean():
    assert audit_field_surface(None, ("卡ID",)).status == "not_scanned"
    assert audit_field_surface({}, ("卡ID",)).status == "not_scanned"


# ---- 狀態面漂移的接線與依歸因分流的處置文案 ------------------------------


def test_state_face_drift_batch_attributes_only_drift_and_keeps_all_verdicts():
    early = _drift_body(
        "2026-08-01T09:00:00+08:00 open by wf-cli；owner 待指派；iteration 0。"
    )
    late = _drift_body(
        "2026-08-26T09:00:00+08:00 open by wf-cli；owner 待指派；iteration 0。"
    )
    report = audit_state_face_drift_batch(
        {"OLD": early, "NEW": late, "OK": early},
        {"OLD": "📥Backlog", "NEW": "📥Backlog", "OK": "💡需求"},
    )
    assert report.scanned_cards == 3 and len(report.verdicts) == 3
    assert {f.card_id for f in report.findings} == {"OLD", "NEW"}, "只有 drift 算 finding"
    assert report.causes == {"OLD": CAUSE_RULE_CHANGED, "NEW": CAUSE_WRITER_NONCONFORMANT}
    assert STATE_FACE_DRIFT_EPOCH.startswith("2026-08-19T")


def test_drift_disposition_text_branches_on_cause():
    """⭐ 對 `rule_changed` 輸出「補跑動詞、勿手動搬看板」是**錯誤的指控**。

    **突變檢驗**：把 `render_state_face_drift` 改回無條件輸出同一句處置，
    本測試轉紅（第二個 assert）。
    """
    early = _drift_body(
        "2026-08-01T09:00:00+08:00 open by wf-cli；owner 待指派；iteration 0。"
    )
    findings = [audit_state_face_drift("OLD", early, "📥Backlog")]
    accusing = "勿手動搬看板"
    with_cause = render_state_face_drift(findings, {"OLD": CAUSE_RULE_CHANGED})
    assert CAUSE_DISPOSITIONS[CAUSE_RULE_CHANGED] in with_cause
    assert accusing not in with_cause, "rule_changed 不得被指控成手動搬看板"
    bypassed = render_state_face_drift(findings, {"OLD": CAUSE_CHANNEL_BYPASSED})
    assert accusing in bypassed, "真的沒有留痕時，那句處置才是對的"
    # 沒有歸因就沒有下處置的依據 ⇒ 只印觀測。
    assert "處置：" not in render_state_face_drift(findings)


def test_drift_render_keeps_the_stats_line_and_the_enforcement_caveat():
    """A9 的保留項：統計行與「偵測不等於強制」段⛔ 不得在改寫中掉了。"""
    findings = [
        audit_state_face_drift("C1", _drift_body(_OPEN_LINE), "💡需求"),
        audit_state_face_drift("C2", _drift_body(_OPEN_LINE), "📥Backlog"),
        audit_state_face_drift("C3", _drift_body(_OPEN_LINE, _ASSIGN_LINE, _HANDOFF_LINE), "🔍待查核"),
    ]
    text = render_state_face_drift(findings, {"C2": CAUSE_RULE_CHANGED})
    assert "一致 1／漂移 1／不判定 1（不判定佔比 33%）" in text
    assert "偵測不等於強制" in text and "#48" in text


# ---- 共用信封 ------------------------------------------------------------


def test_scan_envelope_reads_only_the_shared_shape():
    """信封只讀 `status`／`scanned_cards`／`findings`／`routine_gaps`，⛔ 不讀內部欄位。"""
    report = audit_conformance(
        {"CARD-A": _conformant_body(_EARLY_OPEN, brief=False).replace(_ROUTING + "\n", "")},
        {"CARD-A": {"服務的原始目標": "有"}},
    )
    envelope = scan_envelope("conformance", report, enters_backlog=True)
    assert (envelope.kind, envelope.status, envelope.scanned_cards) == (
        "conformance", "scanned", 1,
    )
    assert envelope.findings == 1 and envelope.routine_gaps == 1
    assert "計入待辦" in envelope.render_line()


def test_legacy_authority_notes_never_enter_the_backlog():
    """⚠️ 它報的是**留痕強度不足，不是授權無效** ⇒ 那些行⛔ 不進待辦。

    既存事件 append-only、明令不得追溯改寫 ⇒ 把它們算進待辦等於製造一個永遠清不掉
    的池，與本卡要消滅的形態同構。

    **突變檢驗**：把 `scan_envelopes` 裡它的 `enters_backlog` 改成 True，本測試轉紅。
    """
    report = DoctorReport(repo_root="/x", generated_at="t", registry_sources=[])
    by_kind = {e.kind: e for e in report.scan_envelopes()}
    assert set(by_kind) == {
        "reachability", "conformance", "brief_drift", "state_face_drift",
        "legacy_authority_notes",
    }
    assert by_kind["legacy_authority_notes"].enters_backlog is False
    assert all(
        by_kind[kind].enters_backlog
        for kind in ("reachability", "conformance", "brief_drift", "state_face_drift")
    )


def test_all_four_scans_default_to_not_scanned():
    """四個掃描的預設都必須是 `not_scanned`，⛔ 不得讓空清單被讀成「都乾淨」。"""
    report = DoctorReport(repo_root="/x", generated_at="t", registry_sources=[])
    assert all(e.status == "not_scanned" for e in report.scan_envelopes())
    assert all("未掃描" in e.render_line() for e in report.scan_envelopes())


# ---- CLI 接線 ------------------------------------------------------------


def _conformance_args(repo, **kw):
    kw.setdefault("conformance", True)
    kw.setdefault("owner", "acme")
    kw.setdefault("project", 4)
    return _doctor_args(repo, **kw)


def test_cli_conformance_flag_scans_and_reports(sandbox_repo, monkeypatch, capsys):
    """⚠️ 本組要擋的是「測試綠但 CLI 跑不到」——`audit_state_face_drift` 自 2026-08-19
    起就存在，生產碼卻**零呼叫端**，測試一路全綠。

    **突變檢驗**：把 `doctor_cmd` 傳給 `run_doctor` 的 `project_field_values` 改成
    不傳，本測試轉紅。
    """
    body = _conformant_body(_EARLY_OPEN, brief=False)
    doctor_cmd = _patch_project(
        monkeypatch,
        {"CARD1": {"body": body, "fields": {"卡ID": "CARD1", "服務的原始目標": "有",
                                            "交付狀態": "📥Backlog", "分支／worktree": "b @ /w"}}},
    )
    assert doctor_cmd.run(_conformance_args(sandbox_repo)) == 0
    out = capsys.readouterr().out
    assert "事後符合性重驗" in out and "已對 1 張卡重跑" in out
    assert "brief_present" in out and CAUSE_RULE_CHANGED in out
    assert "分支／worktree" in out, "欄位層對帳要真的拿到欄位值"
    assert "狀態面漂移對帳" in out, "state_face_drift 必須真的被接上"
    assert "已對 1 張卡探測" in out, "可達性必須真的拿到卡面（⛔ 不得停在 not_scanned）"
    assert "卡面掃描面總表" in out


def test_cli_deprecated_alias_still_works(sandbox_repo, monkeypatch, capsys):
    """舊名保留為 alias——改名⛔ 不得弄壞任何沒被搜到的呼叫端。"""
    from wf_cli.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(
        ["doctor", str(sandbox_repo), "--legacy-authority-notes", "--owner", "a", "--project", "4"]
    )
    assert args.conformance is True
    assert parser.parse_args(["doctor", str(sandbox_repo), "--conformance",
                              "--owner", "a", "--project", "4"]).conformance is True


def test_cli_conformance_does_not_feed_the_cleanup_guard(sandbox_repo, monkeypatch):
    """⛔ 接線不得順手改變 `--cleanup-preview` 的判定（`card_bodies` 是另一個消費者）。"""
    from wf_cli.commands import doctor_cmd

    seen = {}

    def _spy(repo_root, registry=None, **kw):
        seen.update(kw)
        return run_doctor(repo_root, registry, **kw)

    _patch_project(
        monkeypatch,
        {"CARD1": {"body": _conformant_body(_EARLY_OPEN), "fields": {"卡ID": "CARD1"}}},
    )
    monkeypatch.setattr(doctor_cmd, "run_doctor", _spy)
    doctor_cmd.run(_conformance_args(sandbox_repo))
    assert seen.get("card_bodies") is None, "cleanup guard 的 card_bodies 不得被順手填上"
    assert set(seen.get("project_field_values") or {}) == {"CARD1"}


def test_cli_json_payload_carries_the_new_scans(sandbox_repo, monkeypatch, capsys):
    """機器消費端要讀得到；只有人類可讀那份等於沒有對外提供。"""
    import json as jsonlib

    doctor_cmd = _patch_project(
        monkeypatch,
        {"CARD1": {"body": _conformant_body(_EARLY_OPEN, brief=False),
                   "fields": {"卡ID": "CARD1", "服務的原始目標": "有", "交付狀態": "📥Backlog"}}},
    )
    assert doctor_cmd.run(_conformance_args(sandbox_repo, json=True)) == 0
    payload = jsonlib.loads(capsys.readouterr().out)
    assert payload["conformance"]["status"] == "scanned"
    assert [f["rule_id"] for f in payload["conformance"]["findings"]] == ["brief_present"]
    assert payload["conformance"]["findings"][0]["cause"] == CAUSE_RULE_CHANGED
    assert payload["field_surface"]["status"] == "scanned"
    assert payload["state_face_drift"]["status"] == "scanned"
    assert payload["reachability"]["status"] == "scanned"


def test_cli_conformance_stays_out_of_strict_exit_code(sandbox_repo, monkeypatch, capsys):
    """⛔ **非阻擋**：既有卡不合規⛔ 不得讓 doctor 以非 0 收場。

    那些卡的不合規多半是規則變更的殘餘（`rule_changed`），把它算進 exit code 等於
    讓 CI 從此恆紅且無人能立刻修好——「偵測器調成永遠會響」與「永遠不會響」同樣沒用。
    """
    doctor_cmd = _patch_project(
        monkeypatch,
        {"CARD1": {"body": _conformant_body(_EARLY_OPEN, brief=False),
                   "fields": {"卡ID": "CARD1", "服務的原始目標": "有"}}},
    )
    rc = doctor_cmd.run(_conformance_args(sandbox_repo, registry="none", strict=True))
    assert "不合規 1 筆" in capsys.readouterr().out, "夾具必須真的有 finding"
    assert rc == 0


# ---- 寫入通道可達性（⭐ 先於合規性） --------------------------------------


def test_reachability_is_per_verb_not_a_binary_property_of_the_card():
    """⭐ 「這張卡改不改得動」不是一個布林值。

    真實形狀（2026-08-04 遷移卡）：資源宣告讀不到 ⇒ `assign` 拒絕派工，但
    `handoff`／`review`／`checkpoint`／`deploy-*` 只做 `append_log_line`，照樣打得到。
    ⇒ 報告必須說得出**哪個動詞**打不到——兩者的處置完全不同。

    **突變檢驗**：把 `probe_reachability` 改成「任一探針失敗即整張卡不可達」而不記
    逐動詞，本測試轉紅（第二、三個 assert）。
    """
    body = _conformant_body(_EARLY_OPEN).replace(_RESOURCES, "")
    finding = probe_reachability("CARD-NO-RES", body, "💡需求")
    assert finding is not None
    assert VERB_ASSIGN in finding.unreachable_for
    assert VERB_AMEND_RESOURCES in finding.unreachable_for
    assert VERB_APPEND_ONLY in finding.reachable_for, "append-only 那一族⛔ 不受影響"
    assert VERB_AMEND_BRIEF in finding.reachable_for


def test_reachability_does_not_false_positive_on_a_healthy_card():
    """⛔ 只驗不可達那側是零資訊：一張齊備的卡必須全部動詞皆可達。"""
    assert probe_reachability("CARD-OK", _conformant_body(_EARLY_OPEN)) is None


def test_reachability_probes_are_zero_write_and_leave_the_body_untouched():
    """探針呼叫的是回傳新字串的純函式 ⇒ 逐位元不動原 body。"""
    body = _conformant_body(_EARLY_OPEN)
    before = body
    probe_reachability("CARD-OK", body)
    assert body == before


def test_reachability_catches_the_literal_backslash_n_before_the_log_heading():
    """真實個案：`## Log` 前面是**字面的**反斜線-n ⇒ `split_at_log` 拒絕整張卡。

    這張卡於 2026-08-09 由開卡動詞寫入，⛔ 至今沒有任何東西發現它。
    """
    broken = _conformant_body(_EARLY_OPEN).replace("\n## Log", "\\n## Log")
    finding = probe_reachability("CARD-BROKEN-LOG", broken, "🏁完成")
    assert finding is not None
    assert VERB_AMEND_CORE_PAIN in finding.unreachable_for
    assert VERB_AMEND_SPEC_BASELINE in finding.unreachable_for


def test_reachability_zero_findings_is_reported_as_scanned_not_as_silence():
    """⛔ 「零筆」與「沒掃」在輸出上不得長得一樣。"""
    scanned = audit_reachability({"CARD-OK": _conformant_body(_EARLY_OPEN)})
    assert (scanned.status, scanned.findings) == ("scanned", [])
    text = render_reachability(scanned)
    assert "全部動詞對全部卡皆可達" in text and "⛔ 不是沒掃" in text
    assert "未掃描" in render_reachability(audit_reachability(None))


def test_reachability_is_rendered_before_conformance():
    """⭐ 先分可達性、再談合規性——打不到的卡，其他不合規項在通道修好前修不了。"""
    report = DoctorReport(repo_root="/x", generated_at="t", registry_sources=[])
    text = report.render_text()
    assert text.index("寫入通道可達性") < text.index("事後符合性重驗")


def test_reachability_states_that_it_only_covers_the_card_face_gate():
    """⛔ 不得過度宣稱：指令層在卡面定位**之前**還有閘門。

    實測：`ML-FIELD-OF1` 的 `amend --core-pain --dry-run` 先被 `--ruling-url` 授權閘門
    拒收，⛔ 不是被本節給的錨點理由拒收。⇒ 「打得到」＝卡面這關過得了，⛔ 不等於
    「這個動詞現在就能成功」；報告必須自己說出這條界線。

    **突變檢驗**：把 `render_reachability` 的射程那行刪掉，本測試轉紅。
    """
    text = render_reachability(audit_reachability({"C": _conformant_body(_EARLY_OPEN)}))
    assert "只測**卡面定位**那一關" in text
    assert "--ruling-url" in text
    assert "⛔ 不等於「這個動詞現在就能成功」" in text


def test_a_structurally_unreachable_cause_is_declared_not_shown_as_a_clean_zero():
    """⭐ 零命中要說得出「什麼結果會推翻它」。

    取不到 Issue `createdAt` 時，唯一能給出存在時刻的來源是 Log 的 `open` 事件，
    而**那筆事件本身就是通道證據** ⇒ 凡是判得出時刻的卡必然在第 4 類被攔下，
    第 5 類（`channel_bypassed`）**構造上到不了**。⇒ 這個 0 是「機制未啟用」，
    ⛔ 不是「掃過而沒有」，報告必須自己講出這件事。

    **突變檢驗**：拿掉 `render_conformance` 的該段、或把 `created_at_available`
    改成恆真，本測試轉紅。
    """
    bodies = {"CARD-A": _conformant_body(_EARLY_OPEN, brief=False)}
    fields = {"CARD-A": {"服務的原始目標": "有"}}

    without = audit_conformance(bodies, fields, None)
    assert without.created_at_available is False
    text = render_conformance(without)
    assert f"`{CAUSE_CHANNEL_BYPASSED}` 今天構造上不可達" in text
    assert "⛔ 不是「掃過而沒有」" in text

    # 補上 createdAt 之後，該段必須消失——它宣稱的是「今天」的狀態，⛔ 不是永久事實。
    with_created = audit_conformance(bodies, fields, {"CARD-A": "2026-08-01T09:00:00+08:00"})
    assert with_created.created_at_available is True
    assert "構造上不可達" not in render_conformance(with_created)
