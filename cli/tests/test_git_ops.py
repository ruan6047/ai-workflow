from __future__ import annotations

from wf_cli.git_ops import parse_submodule_status, parse_worktree_porcelain

# 真實擷取自 cpbl-analytics `git worktree list --porcelain`（2026-08-04 22:xx）的黃金樣本，
# 用來鎖住 porcelain 格式的解析邏輯——這組資料正好含 doctor 卡面驗收要求的 3 個已知孤兒
# （gate3-shadow-obs／website-naming-homepage-redesign-88e250／adoring-taussig-0d71cb），
# 是純字串解析的回歸測試；doctor 的分類邏輯另有 test_doctor.py 用真實 git repo 驗證。
REAL_CPBL_PORCELAIN = """worktree /Users/ruanruan/Dev/cpbl-analytics
HEAD 74ac4b7cb2ecf2d1b4230b22250b9f79c7db9a1b
branch refs/heads/main

worktree /private/tmp/claude-501/scratchpad/gate3-shadow-obs
HEAD 50edabee5ee7cd7ead946bd6e620aabbc150d208
detached
prunable gitdir file points to non-existent location

worktree /Users/ruanruan/Dev/cpbl-analytics/.claude/worktrees/adoring-taussig-0d71cb
HEAD 3590b47d2d0e0a9597d5c0b692c1c6579762d401
branch refs/heads/claude/task-status-check-1a2b08

worktree /Users/ruanruan/Dev/cpbl-analytics/.claude/worktrees/dev-trailer-guard-pr-checkout1-execution
HEAD fbd750594c55e8da32666af10a7a5fb1c8403c36
branch refs/heads/ai/claude-sonnet-5/DEV-TRAILER-GUARD-PR-CHECKOUT1

worktree /Users/ruanruan/Dev/cpbl-analytics/.claude/worktrees/ingest-player-bio-gap2-review
HEAD 3b9fe0e14be54f70b9dd48f516316fbba00f3c13
detached

worktree /Users/ruanruan/Dev/cpbl-analytics/.claude/worktrees/website-naming-homepage-redesign-88e250
HEAD 46aed5e1f0d969fc982b2bfab9b97dc19704080d
branch refs/heads/claude/website-naming-homepage-redesign-88e250
"""


def test_parses_all_entries_from_real_sample():
    entries = parse_worktree_porcelain(REAL_CPBL_PORCELAIN)
    assert len(entries) == 6
    by_path = {e.path: e for e in entries}
    assert set(by_path) == {
        "/Users/ruanruan/Dev/cpbl-analytics",
        "/private/tmp/claude-501/scratchpad/gate3-shadow-obs",
        "/Users/ruanruan/Dev/cpbl-analytics/.claude/worktrees/adoring-taussig-0d71cb",
        "/Users/ruanruan/Dev/cpbl-analytics/.claude/worktrees/dev-trailer-guard-pr-checkout1-execution",
        "/Users/ruanruan/Dev/cpbl-analytics/.claude/worktrees/ingest-player-bio-gap2-review",
        "/Users/ruanruan/Dev/cpbl-analytics/.claude/worktrees/website-naming-homepage-redesign-88e250",
    }


def test_main_worktree_has_branch_main_and_is_not_prunable():
    entries = parse_worktree_porcelain(REAL_CPBL_PORCELAIN)
    main = next(e for e in entries if e.path == "/Users/ruanruan/Dev/cpbl-analytics")
    assert main.branch == "main"
    assert not main.is_prunable
    assert not main.is_detached


def test_gate3_shadow_obs_is_detached_and_prunable_with_reason():
    entries = parse_worktree_porcelain(REAL_CPBL_PORCELAIN)
    gate3 = next(e for e in entries if e.path.endswith("gate3-shadow-obs"))
    assert gate3.is_detached
    assert gate3.branch is None
    assert gate3.is_prunable
    assert "non-existent location" in gate3.prunable_reason


def test_known_orphan_candidates_have_branches_and_are_not_prunable():
    entries = parse_worktree_porcelain(REAL_CPBL_PORCELAIN)
    by_path = {e.path: e for e in entries}
    adoring = by_path["/Users/ruanruan/Dev/cpbl-analytics/.claude/worktrees/adoring-taussig-0d71cb"]
    website = by_path[
        "/Users/ruanruan/Dev/cpbl-analytics/.claude/worktrees/website-naming-homepage-redesign-88e250"
    ]
    assert adoring.branch == "claude/task-status-check-1a2b08"
    assert not adoring.is_prunable
    assert website.branch == "claude/website-naming-homepage-redesign-88e250"
    assert not website.is_prunable


def test_review_sandbox_worktree_is_detached_but_not_prunable():
    # ingest-player-bio-gap2-review：worktree-lifecycle.md 定義的一次性審查沙箱，
    # 沒有分支也不是 prunable——doctor 必須把它跟「孤兒」分開處理，見 test_doctor.py。
    entries = parse_worktree_porcelain(REAL_CPBL_PORCELAIN)
    review = next(e for e in entries if e.path.endswith("ingest-player-bio-gap2-review"))
    assert review.is_detached
    assert review.branch is None
    assert not review.is_prunable


def test_parse_submodule_status_distinguishes_initialized_and_uninitialized():
    text = " e29f0f469261ce77a945c622dc0f125abf5b8886 .ai-workflow (heads/ai/gpt-5@codex/WF-21)\n"
    entries = parse_submodule_status(text)
    assert len(entries) == 1
    assert entries[0].initialized is True
    assert entries[0].out_of_sync is False
    assert entries[0].path == ".ai-workflow"


def test_parse_submodule_status_uninitialized_prefix():
    text = "-e29f0f469261ce77a945c622dc0f125abf5b8886 .ai-workflow\n"
    entries = parse_submodule_status(text)
    assert entries[0].initialized is False


def test_parse_submodule_status_out_of_sync_prefix():
    text = "+e29f0f469261ce77a945c622dc0f125abf5b8886 .ai-workflow (heads/main)\n"
    entries = parse_submodule_status(text)
    assert entries[0].initialized is True
    assert entries[0].out_of_sync is True
