from __future__ import annotations

import pytest

import shutil
from pathlib import Path

from wf_cli.doctor import DoctorReport, audit_review_channel, run_doctor
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
    finding = audit_review_channel([{"body": _verdict(marker)}], _ECARD, _ESHA, card_body=_ELOG)
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
    finding = audit_review_channel(
        [{"body": _verdict(_conformant_marker())}], _ECARD, _ESHA, card_body=log
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
        owner=None, project=None,
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
        _ECARD, _ESHA, card_body=split_log,
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
    assert "沒有可辨識" in finding.detail


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
