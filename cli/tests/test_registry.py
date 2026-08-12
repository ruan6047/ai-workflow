from __future__ import annotations

import json
from pathlib import Path

import pytest

from wf_cli.registry import (
    OWNERSHIP_DECISIONS,
    RepoOwnershipVerdict,
    WorktreeRepoProbe,
    card_repo_from_issue_url,
    check_assign_repo_ownership,
    check_worktree_repo_ownership,
    enumerate_ownership,
    fetch_project_ownership_rows,
    load_tasks_md_registry,
    main,
    normalize_repo_slug,
    parse_active_ledger,
    parse_archived_card_ids,
    parse_markdown_tables,
    probe_worktree_repo,
    run_git_readonly,
    summarize_ownership,
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
        slug=slug, source="target_dir", resolved_target="/tmp/x", probed_dir="/tmp/x",
        common_dir="/tmp/x/.git", remote_url="git@github.com:o/r.git", detail="probe detail",
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
        worktree_probe=WorktreeRepoProbe(slug=None, detail="路徑不存在"),
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


# --- R1-02：可判定的目標 repo 語意 -------------------------------------------
#
# 舊版的錯誤前提是「worktree 的 repo 由目標路徑座落在哪決定」。git 的真語意是
# 「由 git worktree add 的來源 repo 決定，與目標路徑落在磁碟哪裡無關」，而
# canonical §4.5 明文路徑由實際建立者決定、未限定巢狀於 repo。以下四條把
# 「repo 外的合法新 worktree」與「相對路徑不再吃 cwd」釘成回歸。


def test_absolute_target_outside_any_repo_is_allowed_with_source_repo(two_repos, tmp_path):
    """**R1-02 的正面反例**：目標在 repo 外（祖先是非 git 目錄）且尚未建立。

    canonical §4.5 允許這種配置。舊版必然走到 ``worktree_repo_undeterminable``
    並 block；給了來源 repo 之後它是可判定的，且判定正確。
    """
    _aiwf, cpbl = two_repos
    outside = tmp_path / "elsewhere"
    outside.mkdir()  # 存在但不是 git repo——舊版祖先探測就是死在這一格
    target = outside / "cpbl-card-wt"
    assert not target.exists()

    without = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=target)
    assert without.decision == "block"
    assert without.reason_code == "worktree_repo_undeterminable"
    assert "source_repo" in without.detail  # 必須指名補法，否則就是無出路的誤擋

    with_source = check_assign_repo_ownership(
        issue_url=CPBL_ISSUE, worktree_path=target, source_repo=cpbl
    )
    assert with_source.decision == "allow"
    assert with_source.reason_code == "match"


def test_source_repo_overrides_misleading_path_nesting(two_repos):
    """來源 repo 是權威，路徑巢狀只是資訊。

    合法情境：從 cpbl 執行 ``git worktree add`` 到一個座落在 ai-workflow 目錄樹底下
    的新路徑。純看路徑會推成 ai-workflow（誤擋 cpbl 的卡）；看來源 repo 才是對的。
    巢狀事實不丟——``nested_repo`` 照樣報出來，那正是 §8.3 漂移隱形的形狀。
    """
    aiwf, cpbl = two_repos
    target = aiwf / ".claude" / "worktrees" / "cpbl-wt-not-created"
    (aiwf / ".claude" / "worktrees").mkdir(parents=True)

    inferred = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=target)
    assert inferred.decision == "block" and inferred.inferred is True

    probe = probe_worktree_repo(target, source_repo=cpbl)
    assert probe.slug == "ruan6047/cpbl-analytics"
    assert probe.source == "source_repo"
    assert probe.inferred is False
    assert probe.nested_repo == "ruan6047/ai-workflow"
    assert check_worktree_repo_ownership(
        card_repo="ruan6047/cpbl-analytics", worktree_probe=probe
    ).decision == "allow"


def test_source_repo_is_not_a_force_flag(two_repos, tmp_path):
    """給錯來源 repo 照樣被擋——它補的是事實，不是繞過比對。"""
    aiwf, _cpbl = two_repos
    target = tmp_path / "elsewhere" / "wt"
    (tmp_path / "elsewhere").mkdir()
    v = check_assign_repo_ownership(
        issue_url=CPBL_ISSUE, worktree_path=target, source_repo=aiwf
    )
    assert v.decision == "block"
    assert v.reason_code == "repo_mismatch"
    assert v.worktree_repo == "ruan6047/ai-workflow"


def test_source_repo_must_exist(tmp_path):
    v = check_assign_repo_ownership(
        issue_url=CPBL_ISSUE, worktree_path=tmp_path / "wt",
        source_repo=tmp_path / "no-such-dir",
    )
    assert v.decision == "block"
    assert "不是既存目錄" in v.detail


def test_relative_path_without_base_dir_never_reads_cwd(two_repos, monkeypatch):
    """相對路徑必須綁定明確 base_dir；沒綁定就是不可判定，**不拿 cwd 補**。

    直接把 cwd 切進 ai-workflow repo 再問：若還讀 cwd，這裡會得到
    ``repo_mismatch``（cwd 那個 repo）。得到 ``worktree_path_unanchored`` 才證明
    cwd 完全沒被查詢——這是「67 筆中 18 筆相對路徑、cwd 錯置會讓誤擋暴增」那條
    自陳的機械封堵。
    """
    aiwf, _cpbl = two_repos
    (aiwf / ".claude" / "worktrees").mkdir(parents=True)
    monkeypatch.chdir(aiwf)

    v = check_assign_repo_ownership(
        issue_url=CPBL_ISSUE, worktree_path=".claude/worktrees/card-x"
    )
    assert v.reason_code == "worktree_path_unanchored"
    assert v.decision == "block"
    assert v.worktree_repo is None
    assert "base_dir" in v.refusal_message()


def test_unanchored_relative_path_is_still_decidable_with_source_repo(two_repos, monkeypatch):
    """給了來源 repo，相對路徑就不必錨定——repo 歸屬本來就與路徑無關。"""
    aiwf, cpbl = two_repos
    monkeypatch.chdir(aiwf)
    v = check_assign_repo_ownership(
        issue_url=CPBL_ISSUE, worktree_path=".claude/worktrees/card-x", source_repo=cpbl
    )
    assert v.decision == "allow"


def test_inferred_block_message_names_the_source_repo_remedy(two_repos):
    aiwf, _cpbl = two_repos
    (aiwf / ".claude" / "worktrees").mkdir(parents=True)
    v = check_assign_repo_ownership(
        issue_url=CPBL_ISSUE, worktree_path=aiwf / ".claude" / "worktrees" / "new"
    )
    assert v.inferred is True
    msg = v.refusal_message()
    assert "推測" in msg
    assert "source_repo" in msg


def test_existing_worktree_outside_its_repo_is_determinable_without_source_repo(two_repos, tmp_path):
    """已建立的 worktree 不需要 source_repo：它的 ``.git`` 直接指回來源 repo。"""
    _aiwf, cpbl = two_repos
    outside = tmp_path / "detached-worktrees"
    outside.mkdir()
    wt = outside / "cpbl-card"
    git(cpbl, "worktree", "add", "-q", "-b", "claude/CPBL-OUT1", str(wt))
    probe = probe_worktree_repo(wt)
    assert probe.slug == "ruan6047/cpbl-analytics"
    assert probe.source == "target_dir"
    assert probe.inferred is False
    assert check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=wt).decision == "allow"


# --- R1-03：唯讀枚舉器 --------------------------------------------------------


def _input_rows(aiwf: Path, cpbl: Path) -> list[dict]:
    return [
        {"card_id": "WF-OK", "issue_url": AIWF_ISSUE,
         "branch_worktree": f"claude/WF-OK @ {aiwf}"},
        {"card_id": "CPBL-DRIFT", "issue_url": CPBL_ISSUE,
         "branch_worktree": f"claude/CPBL-DRIFT @ {aiwf}"},
        {"card_id": "REL-UNANCHORED", "issue_url": CPBL_ISSUE,
         "branch_worktree": "claude/REL @ .claude/worktrees/rel"},
        {"card_id": "DRAFT", "issue_url": None,
         "branch_worktree": f"claude/DRAFT @ {cpbl}"},
    ]


def test_enumerator_reports_every_row_with_reason_and_decision(two_repos):
    aiwf, cpbl = two_repos
    rows = enumerate_ownership(_input_rows(aiwf, cpbl))
    by_id = {r.card_id: r for r in rows}
    assert len(rows) == 4
    assert by_id["WF-OK"].decision == "allow"
    assert by_id["CPBL-DRIFT"].reason_code == "repo_mismatch"
    assert by_id["CPBL-DRIFT"].worktree_repo == "ruan6047/ai-workflow"
    assert by_id["REL-UNANCHORED"].reason_code == "worktree_path_unanchored"
    assert by_id["DRAFT"].reason_code == "card_repo_undeterminable"
    assert by_id["WF-OK"].branch == "claude/WF-OK"


def test_enumerator_strips_markdown_backticks_from_registration(two_repos):
    """Project 欄位實測存著 ``` `branch @ path` ```；不剝反引號會讓存在的目錄被判成不存在。"""
    aiwf, _cpbl = two_repos
    rows = enumerate_ownership(
        [{"card_id": "TICKED", "issue_url": AIWF_ISSUE,
          "branch_worktree": f"`claude/TICKED @ {aiwf}`"}]
    )
    assert rows[0].branch == "claude/TICKED"
    assert rows[0].worktree_raw == str(aiwf)
    assert rows[0].target_exists is True
    assert rows[0].decision == "allow"


def test_summary_counts_are_derived_from_the_same_rows(two_repos):
    """§6.2：宣稱的數字與 artifact 同源。摘要不是另外數的。"""
    aiwf, cpbl = two_repos
    rows = enumerate_ownership(_input_rows(aiwf, cpbl))
    summary = summarize_ownership(rows)
    assert summary["total"] == len(rows)
    assert summary["allow"] + summary["block"] == summary["total"]
    assert summary["allow"] == sum(1 for r in rows if r.decision == "allow")
    assert sum(summary["by_reason_code"].values()) == len(rows)


def test_enumerator_cli_artifact_replay_is_a_fixed_point(two_repos, tmp_path):
    """產物可直接餵回 ``--input``，且逐字節相同（§6.2 的不動點要求）。"""
    aiwf, cpbl = two_repos
    src = tmp_path / "input.json"
    src.write_text(json.dumps({"rows": _input_rows(aiwf, cpbl)}), encoding="utf-8")

    first, second = tmp_path / "a.json", tmp_path / "b.json"
    assert main(["--input", str(src), "--output", str(first)]) == 0
    assert main(["--input", str(first), "--output", str(second)]) == 0
    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")

    artifact = json.loads(first.read_text(encoding="utf-8"))
    assert artifact["summary"]["total"] == 4
    assert len(artifact["input"]["rows"]) == 4  # 產物內含它用過的全部輸入
    assert artifact["rows"][0]["reason_code"]


def test_enumerator_tsv_carries_the_same_summary(two_repos, tmp_path, capsys):
    aiwf, cpbl = two_repos
    src = tmp_path / "input.json"
    src.write_text(json.dumps({"rows": _input_rows(aiwf, cpbl)}), encoding="utf-8")
    assert main(["--input", str(src), "--format", "tsv"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].split("\t")[:2] == ["card_id", "card_repo"]
    assert len(out) == 1 + 4 + 1  # header + 4 列 + summary
    assert json.loads(out[-1].split("\t", 1)[1])["total"] == 4


def test_fetch_project_rows_paginates_and_drops_rows_without_worktree():
    """注入假的 graphql runner：驗分頁、中文欄位名擷取、以及「無 worktree 註冊」被濾掉。"""
    pages = [
        {
            "data": {"user": {"projectV2": {"items": {
                "pageInfo": {"hasNextPage": True, "endCursor": "CUR"},
                "nodes": [
                    {"content": {"__typename": "Issue", "url": AIWF_ISSUE},
                     "fieldValues": {"nodes": [
                         {"text": "WF-A", "field": {"name": "卡ID"}},
                         {"text": "b @ /p/a", "field": {"name": "分支worktree"}},
                     ]}},
                    {"content": {"__typename": "Issue", "url": CPBL_ISSUE},
                     "fieldValues": {"nodes": [
                         {"text": "NO-WT", "field": {"name": "卡ID"}},
                         {"text": "—", "field": {"name": "分支worktree"}},
                     ]}},
                ],
            }}}}
        },
        {
            "data": {"user": {"projectV2": {"items": {
                "pageInfo": {"hasNextPage": False},
                "nodes": [
                    {"content": {"__typename": "DraftIssue"},
                     "fieldValues": {"nodes": [
                         {"text": "DRAFT-B", "field": {"name": "卡ID"}},
                         {"text": "b @ /p/b", "field": {"name": "分支／worktree"}},
                     ]}},
                ],
            }}}}
        },
    ]
    seen: list[object] = []

    def fake_run(payload):
        seen.append(payload["variables"]["after"])
        return pages[len(seen) - 1]

    rows = fetch_project_ownership_rows("ruan6047", 4, run=fake_run)
    assert seen == [None, "CUR"]
    assert [r["card_id"] for r in rows] == ["WF-A", "DRAFT-B"]
    assert rows[1]["issue_url"] is None  # DraftIssue 沒有 Issue URL，不猜
    assert rows[0]["branch_worktree"] == "b @ /p/a"


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
