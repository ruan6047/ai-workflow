from __future__ import annotations

import pytest

import shutil
from pathlib import Path

from wf_cli.doctor import DoctorReport, audit_review_channel, run_doctor
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
    finding = audit_review_channel([{"body": _verdict(_conformant_marker())}], _ECARD, _ESHA, card_body=_ELOG)
    assert finding.status == "recorded"


def test_legacy_event_without_prefix_is_unchanged():
    """legacy 判準是語法：完全不含 wf-review-event: 前綴者行為完全不變。"""
    legacy = f"## 查核裁決：APPROVE\n- 卡：`{_ECARD}`　attempt_id：`{_EATT}`"
    assert "wf-review-event:" not in legacy
    finding = audit_review_channel([{"body": legacy}], _ECARD, _ESHA, card_body=_ELOG)
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
    finding = audit_review_channel([{"body": _verdict(marker)}], _ECARD, _ESHA, card_body=log)
    assert finding.status == "recorded"


def test_log_must_index_the_same_attempt_as_the_event():
    """§3.1.3 三面一致要求 Log 索引的是**同一 attempt_id**。

    先前實作把它拆成兩個獨立全文檢查，於是 Log 索引 e0 也能讓 e1 的事件過關。
    """
    marker = _conformant_marker(attempt=f"{_ECARD}-e1-{_ESHA}")
    finding = audit_review_channel([{"body": _verdict(marker)}], _ECARD, _ESHA, card_body=_ELOG)
    assert finding.status != "recorded", "Log 索引的是 e0，不得讓 e1 的事件過關"


def test_log_index_conditions_must_be_on_the_same_line():
    """attempt 出現在 assign 行、review by wf-cli 出現在另一行，不構成索引。"""
    split_log = (
        f"## Log\n- assign by wf-cli；attempt {_EATT}。\n- review by wf-cli → 別的事。"
    )
    finding = audit_review_channel(
        [{"body": _verdict(_conformant_marker())}], _ECARD, _ESHA, card_body=split_log
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
