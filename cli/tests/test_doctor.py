from __future__ import annotations

import shutil
from pathlib import Path

from wf_cli.doctor import audit_review_channel, run_doctor
from wf_cli.registry import RegisteredCard, TasksMdRegistry
from wf_cli.review import render_verdict_comment
from wf_cli.validation import validate_review_report

from .conftest import git


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
    finding = audit_review_channel(
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
