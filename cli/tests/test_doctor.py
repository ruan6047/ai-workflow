from __future__ import annotations

import pytest

import shutil
from pathlib import Path

from wf_cli.doctor import (
    COMMIT_TRAILER_ROOT_CAUSE_ID,
    SUPERSEDED_ROOT_CAUSE_IDS,
    TRAILER_GUARD_EPOCH,
    CommitRecord,
    DoctorReport,
    audit_commit_trailers,
    audit_review_channel,
    classify_commit_shape,
    evaluate_commit_trailers,
    required_trailers,
    run_doctor,
    severed_declared_keys,
)
from wf_cli.registry import RegisteredCard, TasksMdRegistry
from wf_cli.review import render_verdict_comment
from wf_cli.validation import validate_review_report

from .conftest import git

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
                delivery_status="🚧進行中", owner="someone", last_handoff=None,
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
                delivery_status="🚧進行中", owner="Claude Sonnet 5@Claude Code",
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
                delivery_status="🚧進行中", owner="Claude Opus 5@Claude Code",
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


def _commit(repo, path: str | None, subject: str, tail: str = "\n".join(_FULL)) -> str:
    """在 sandbox 建一筆 commit；`path=None` 代表空 commit。"""
    args = ["commit", "-q", "-m", f"{subject}\n\n說明段落。\n\n{tail}" if tail else f"{subject}\n\n說明段落。"]
    if path is None:
        args.insert(2, "--allow-empty")
    else:
        (repo / path).write_text(path + "\n", encoding="utf-8")
        git(repo, "add", path)
    git(repo, *args)
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


# ---- 「寫了但被空行切斷」的偵測（AI_WORKFLOW.md:220） -------------------


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


def test_epoch_triage_splits_history_from_new_commits_on_real_history(sandbox_repo, monkeypatch):
    """同一份歷史、同一個檢查器，界線兩側判定不同——這就是「分流」。"""
    repo = sandbox_repo
    old = _commit(repo, "old.txt", "feat: 界線前", tail="")
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2026-08-20T10:00:00+08:00")
    monkeypatch.setenv("GIT_AUTHOR_DATE", "2026-08-20T10:00:00+08:00")
    new = _commit(repo, "new.txt", "feat: 界線後", tail="")

    report = audit_commit_trailers(repo, "main", epoch="2026-08-13T00:00:00+08:00")
    by_sha = {f.sha: f for f in report.findings}
    assert by_sha[old].status == "pre_guard"
    assert by_sha[new].status == "violation"
    assert len(report.violations) == 1


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
