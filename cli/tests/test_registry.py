from __future__ import annotations

from pathlib import Path

import pytest
from wf_cli.registry import (
    OWNERSHIP_DECISIONS,
    RepoOwnershipVerdict,
    WorktreeRepoProbe,
    card_repo_from_issue_url,
    check_assign_repo_ownership,
    check_worktree_repo_ownership,
    load_tasks_md_registry,
    normalize_repo_slug,
    parse_active_ledger,
    parse_archived_card_ids,
    parse_markdown_tables,
    probe_worktree_repo,
    run_git_readonly,
)

from .conftest import git

ACTIVE_LEDGER = """# 任務看板

## Ledger 總表（活卡）

| 卡ID | Initiative | 級別 | 功能 | owner | 分支／worktree | iteration | 交付狀態 | 部署狀態 | 最後交接 |
|---|---|---|---|---|---|---|---|---|---|
| [CARD-A](tasks/CARD-A.md) | None | T2 | 示範卡 A | someone | `ai/agent/CARD-A @ .claude/worktrees/card-a` | 0 | 🚧進行中 | —不適用 | 2026-08-01T00:00:00+08:00 |
| [CARD-B](tasks/CARD-B.md) | INIT-X | T3 | 示範卡 B | 待指派 | — | 0 | 📥Backlog | —不適用 | 2026-07-01T00:00:00+08:00 |

## 依賴註記

- 一些不相干的文字，不是表格。
"""

ARCHIVE_LEDGER = """# 封存

| 卡ID | 功能 | 交付狀態 | 部署狀態 | 封存位置 |
|---|---|---|---|---|
| CARD-OLD1 | 舊卡 | 🏁完成 | —不適用 | [tasks/CARD-OLD1.md](tasks/CARD-OLD1.md) |
"""


def test_parse_markdown_tables_finds_both_tables_and_ignores_prose():
    tables = parse_markdown_tables(ACTIVE_LEDGER)
    assert len(tables) == 1
    header, rows = tables[0]
    assert header[0] == "卡ID"
    assert len(rows) == 2


def test_parse_active_ledger_extracts_card_id_branch_and_worktree():
    cards = parse_active_ledger(ACTIVE_LEDGER)
    by_id = {c.card_id: c for c in cards}
    assert by_id["CARD-A"].branch == "ai/agent/CARD-A"
    assert by_id["CARD-A"].worktree_path == ".claude/worktrees/card-a"
    assert by_id["CARD-A"].delivery_status == "🚧進行中"
    assert by_id["CARD-A"].last_handoff == "2026-08-01T00:00:00+08:00"
    assert by_id["CARD-A"].owner_assigned() is True


def test_parse_active_ledger_handles_placeholder_branch_and_owner():
    cards = parse_active_ledger(ACTIVE_LEDGER)
    by_id = {c.card_id: c for c in cards}
    assert by_id["CARD-B"].branch is None
    assert by_id["CARD-B"].worktree_path is None
    assert by_id["CARD-B"].owner_assigned() is False


def test_parse_archived_card_ids_extracts_plain_text_ids():
    ids = parse_archived_card_ids(ARCHIVE_LEDGER)
    assert ids == {"CARD-OLD1"}


def test_load_tasks_md_registry_reads_docs_subdir(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "TASKS.md").write_text(ACTIVE_LEDGER, encoding="utf-8")
    archive_dir = docs / "archive"
    archive_dir.mkdir()
    (archive_dir / "TASKS_ARCHIVE.md").write_text(ARCHIVE_LEDGER, encoding="utf-8")

    registry = load_tasks_md_registry(tmp_path)
    assert {c.card_id for c in registry.active} == {"CARD-A", "CARD-B"}
    assert registry.archived_card_ids == {"CARD-OLD1"}
    assert len(registry.source_paths) == 2


def test_load_tasks_md_registry_falls_back_to_root_tasks_md(tmp_path: Path):
    (tmp_path / "TASKS.md").write_text(ACTIVE_LEDGER, encoding="utf-8")
    registry = load_tasks_md_registry(tmp_path)
    assert {c.card_id for c in registry.active} == {"CARD-A", "CARD-B"}


def test_load_tasks_md_registry_empty_when_no_files(tmp_path: Path):
    registry = load_tasks_md_registry(tmp_path)
    assert registry.active == []
    assert registry.archived_card_ids == set()
    assert registry.source_paths == []


def test_registered_card_repo_defaults_to_none_from_tasks_md(tmp_path: Path):
    """TASKS.md Ledger 沒有 repo 欄，所以本機來源永遠說「不知道」——不是猜。"""
    (tmp_path / "TASKS.md").write_text(ACTIVE_LEDGER, encoding="utf-8")
    registry = load_tasks_md_registry(tmp_path)
    assert all(c.repo is None for c in registry.active)


# ---------------------------------------------------------------------------
# 跨 repo 歸屬守衛（#57）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ruan6047/ai-workflow", "ruan6047/ai-workflow"),
        ("git@github.com:ruan6047/ai-workflow.git", "ruan6047/ai-workflow"),
        ("https://github.com/ruan6047/cpbl-analytics.git", "ruan6047/cpbl-analytics"),
        ("https://github.com/ruan6047/cpbl-analytics", "ruan6047/cpbl-analytics"),
        ("ssh://git@github.com/ruan6047/ai-workflow.git", "ruan6047/ai-workflow"),
        ("https://github.com/ruan6047/cpbl-analytics/issues/57", "ruan6047/cpbl-analytics"),
        ("https://github.com/ruan6047/ai-workflow/pull/51", "ruan6047/ai-workflow"),
        # 大小寫不分：逐字比對會製造純大小寫的誤擋
        ("https://github.com/Ruan6047/AI-Workflow", "ruan6047/ai-workflow"),
        ("  ruan6047/ai-workflow  ", "ruan6047/ai-workflow"),
        # 認不出來的一律 None，不猜
        (None, None),
        ("", None),
        ("   ", None),
        ("ai-workflow", None),
        ("/Users/ruanruan/Dev/ai-workflow", None),  # 裸路徑三段以上不得被讀成 slug
        ("https://github.com/ruan6047", None),
        ("owner/re po", None),
    ],
)
def test_normalize_repo_slug_table(raw, expected):
    assert normalize_repo_slug(raw) == expected


def test_card_repo_only_accepts_issue_url_not_bare_slug():
    """卡 repo 只認 Issue URL。

    這條是守衛的反同義反覆保險：若裸 ``owner/repo`` 也被接受，呼叫端就能把
    ``--repo``／``WFCLI_REPO``（＝被檢查者自己的主張）餵成「卡的 repo」，於是
    在該擋的那一刻兩邊必然相等。漂移案例的形狀正是呼叫端環境設錯。
    """
    assert card_repo_from_issue_url("https://github.com/ruan6047/cpbl-analytics/issues/57") == (
        "ruan6047/cpbl-analytics"
    )
    assert card_repo_from_issue_url("ruan6047/cpbl-analytics") is None
    assert card_repo_from_issue_url(None) is None
    assert card_repo_from_issue_url("") is None


def test_only_match_produces_allow_exhaustively():
    """對 reason→decision **全表**窮舉：``match`` 是唯一放行碼。

    不是抽樣：迭代 ``OWNERSHIP_DECISIONS`` 本身，新增 reason 而忘了裁定放不放行
    時這條會紅。同時驗 ``RepoOwnershipVerdict.decision`` 確實由該表導出，而非
    另有一套 if。
    """
    allowing = {r for r, d in OWNERSHIP_DECISIONS.items() if d == "allow"}
    assert allowing == {"match"}
    for reason, decision in OWNERSHIP_DECISIONS.items():
        verdict = RepoOwnershipVerdict(
            reason_code=reason, card_repo="o/r", worktree_repo="o/r", detail="x"
        )
        assert verdict.decision == decision
        assert verdict.blocked is (decision == "block")


def _probe(slug):
    return WorktreeRepoProbe(
        slug=slug, probed_dir="/tmp/x", common_dir="/tmp/x/.git",
        remote_url="git@github.com:o/r.git", detail="probe detail",
    )


def test_verdict_blocks_on_cross_repo():
    v = check_worktree_repo_ownership(
        card_repo="ruan6047/cpbl-analytics", worktree_probe=_probe("ruan6047/ai-workflow")
    )
    assert v.reason_code == "repo_mismatch"
    assert v.decision == "block"
    assert "cpbl-analytics" in v.refusal_message()
    assert "ai-workflow" in v.refusal_message()


def test_verdict_allows_same_repo():
    v = check_worktree_repo_ownership(
        card_repo="ruan6047/ai-workflow", worktree_probe=_probe("ruan6047/ai-workflow")
    )
    assert v.reason_code == "match"
    assert v.decision == "allow"


def test_verdict_fail_closed_when_card_repo_undeterminable():
    v = check_worktree_repo_ownership(
        card_repo=None, worktree_probe=_probe("ruan6047/ai-workflow")
    )
    assert v.reason_code == "card_repo_undeterminable"
    assert v.decision == "block"


def test_verdict_fail_closed_when_worktree_repo_undeterminable():
    v = check_worktree_repo_ownership(
        card_repo="ruan6047/ai-workflow",
        worktree_probe=WorktreeRepoProbe(None, None, None, None, "路徑不存在"),
    )
    assert v.reason_code == "worktree_repo_undeterminable"
    assert v.decision == "block"


def test_refusal_message_names_the_legitimate_path():
    """被擋的人必須看到出路（#16 §7.1），否則只會學會繞過守衛。"""
    for reason in (r for r, d in OWNERSHIP_DECISIONS.items() if d == "block"):
        msg = RepoOwnershipVerdict(reason, "o/a", "o/b", "detail").refusal_message()
        assert "卡就開在哪個 repo" in msg
        assert "連結" in msg


# --- 真實 git：兩個獨立 repo ＋ 真的 git worktree add -------------------------

def _repo_with_remote(root: Path, name: str, remote: str) -> Path:
    repo = root / name
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "wf-cli tests")
    git(repo, "remote", "add", "origin", remote)
    (repo / "README.md").write_text(name, encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-q", "-m", "init")
    return repo


@pytest.fixture
def two_repos(tmp_path: Path):
    """兩個真實 git repo，remote 分別對應本專案實際的兩個 repo。

    不是合成 fixture：真的 ``git init``／``git remote add``／``git worktree add``，
    判定走真實的 ``run_git_readonly``（真 subprocess），不注入任何假 probe。
    """
    aiwf = _repo_with_remote(tmp_path, "ai-workflow", "git@github.com:ruan6047/ai-workflow.git")
    cpbl = _repo_with_remote(tmp_path, "cpbl-analytics", "git@github.com:ruan6047/cpbl-analytics.git")
    return aiwf, cpbl


CPBL_ISSUE = "https://github.com/ruan6047/cpbl-analytics/issues/999"
AIWF_ISSUE = "https://github.com/ruan6047/ai-workflow/issues/57"


def test_real_cross_repo_existing_worktree_is_blocked(two_repos):
    """§8.3 的原案回放：cpbl 的卡，worktree 真的建在 ai-workflow repo 內。"""
    aiwf, _cpbl = two_repos
    wt = aiwf / ".claude" / "worktrees" / "cpbl-card"
    git(aiwf, "worktree", "add", "-q", "-b", "claude/CPBL-CARD1", str(wt))
    assert wt.is_dir()

    v = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=wt)
    assert v.decision == "block"
    assert v.reason_code == "repo_mismatch"
    assert v.card_repo == "ruan6047/cpbl-analytics"
    assert v.worktree_repo == "ruan6047/ai-workflow"


def test_real_cross_repo_blocked_before_worktree_exists(two_repos):
    """assign 早於 ``git worktree add``：路徑還不存在時就要能擋（否則預防太晚）。"""
    aiwf, _cpbl = two_repos
    not_created = aiwf / ".claude" / "worktrees" / "not-created-yet"
    assert not not_created.exists()
    v = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=not_created)
    assert v.decision == "block"
    assert v.reason_code == "repo_mismatch"
    assert v.worktree_repo == "ruan6047/ai-workflow"


def test_real_same_repo_worktree_is_allowed(two_repos):
    """合法配置：ai-workflow 的卡，worktree 建在 ai-workflow 內 → 放行。"""
    aiwf, _cpbl = two_repos
    wt = aiwf / ".claude" / "worktrees" / "wf-card"
    git(aiwf, "worktree", "add", "-q", "-b", "claude/WF-CARD1", str(wt))
    v = check_assign_repo_ownership(issue_url=AIWF_ISSUE, worktree_path=wt)
    assert v.decision == "allow"
    assert v.reason_code == "match"


def test_real_cpbl_card_in_cpbl_repo_is_allowed(two_repos):
    _aiwf, cpbl = two_repos
    wt = cpbl / ".claude" / "worktrees" / "cpbl-card"
    git(cpbl, "worktree", "add", "-q", "-b", "claude/CPBL-CARD1", str(wt))
    v = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=wt)
    assert v.decision == "allow"


def test_real_relative_worktree_path_resolved_against_base_dir(two_repos):
    """Ledger 存相對路徑；base_dir 決定它落在哪個 repo，兩邊都要判對。"""
    aiwf, cpbl = two_repos
    (aiwf / ".claude" / "worktrees").mkdir(parents=True)
    (cpbl / ".claude" / "worktrees").mkdir(parents=True)
    rel = ".claude/worktrees/card-x"
    assert check_assign_repo_ownership(
        issue_url=CPBL_ISSUE, worktree_path=rel, base_dir=cpbl
    ).decision == "allow"
    assert check_assign_repo_ownership(
        issue_url=CPBL_ISSUE, worktree_path=rel, base_dir=aiwf
    ).decision == "block"


def test_real_path_outside_any_git_repo_is_blocked(tmp_path: Path):
    outside = tmp_path / "not-a-repo"
    outside.mkdir()
    v = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=outside)
    assert v.decision == "block"
    assert v.reason_code == "worktree_repo_undeterminable"


def test_real_repo_without_origin_is_blocked(sandbox_repo: Path):
    """sandbox_repo 沒有 origin remote → 判不出 slug → fail-closed。"""
    v = check_assign_repo_ownership(issue_url=AIWF_ISSUE, worktree_path=sandbox_repo)
    assert v.decision == "block"
    assert v.reason_code == "worktree_repo_undeterminable"
    assert "origin" in v.detail


def test_draft_issue_card_is_blocked(two_repos):
    """DraftIssue 沒有 Issue URL → 卡 repo 判不出來 → fail-closed（已論證）。"""
    aiwf, _ = two_repos
    v = check_assign_repo_ownership(issue_url=None, worktree_path=aiwf)
    assert v.decision == "block"
    assert v.reason_code == "card_repo_undeterminable"


def test_probe_reports_commondir_and_remote(two_repos):
    aiwf, _ = two_repos
    probe = probe_worktree_repo(aiwf)
    assert probe.slug == "ruan6047/ai-workflow"
    assert probe.common_dir is not None and probe.common_dir.endswith(".git")
    assert probe.remote_url == "git@github.com:ruan6047/ai-workflow.git"


def test_run_git_readonly_returns_none_instead_of_raising(tmp_path: Path):
    assert run_git_readonly(tmp_path, ["rev-parse", "--git-common-dir"]) is None


def test_guard_verdict_unaffected_by_stale_tasks_md_projection(two_repos):
    """守衛不吃 ``TASKS.md`` 投影——doctor 今天的誤報源頭碰不到它。

    做法：在被檢查的 repo 內**刻意**放一份與事實矛盾的 Ledger（宣稱該 worktree
    屬於另一張卡、另一個分支），再跑同一組判定，證明結果一字未變。
    """
    aiwf, _ = two_repos
    wt = aiwf / ".claude" / "worktrees" / "cpbl-card"
    git(aiwf, "worktree", "add", "-q", "-b", "claude/CPBL-CARD1", str(wt))
    before = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=wt)

    (aiwf / "TASKS.md").write_text(ACTIVE_LEDGER, encoding="utf-8")
    registry = load_tasks_md_registry(aiwf)
    assert registry.active, "前提：投影確實被讀得到，否則這條測試證明不了隔離"
    assert not any(c.worktree_path == str(wt) for c in registry.active), "前提：投影與事實不符"

    after = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=wt)
    assert after == before
    assert after.decision == "block"
