"""W1.7 驗收 (4)(5) 的本機側：rev-parse／log／diff --stat／merge-tree。

母體＝tmp_path 內臨時建立的 git repo，⛔ 不釘本 repo 的任何 SHA、內容或缺檔。
"""
import subprocess

import pytest

from wfx.gh.facts import git_facts
from wfx.gh.localgit import LocalGitUnavailable, merge_tree
from wfx.gh.localrev import LocalRevUnavailable, diff_stat, log_commits, rev_parse

from .fakes import RecordedRunner


def git(root, *args):
    result = subprocess.run(('git', '-C', str(root), *args), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / 'r'
    root.mkdir()
    git(root, 'init', '-q', '-b', 'main')
    git(root, 'config', 'user.email', 't@example.invalid')
    git(root, 'config', 'user.name', 't')
    (root / 'a.txt').write_text('base\n')
    git(root, 'add', 'a.txt')
    git(root, 'commit', '-qm', 'base')
    git(root, 'branch', 'work')
    git(root, 'checkout', '-q', 'work')
    (root / 'b.txt').write_text('head\n')
    git(root, 'add', 'b.txt')
    git(root, 'commit', '-qm', 'head')
    return root


def test_local_facts_for_the_same_sha_are_byte_identical(repo):
    """同一 SHA 兩次讀取逐字相同（⛔ 不含工作樹路徑或執行時間）。"""
    head = git(repo, 'rev-parse', 'HEAD')
    first = git_facts(repo, default_branch='main', remote_names=(), sha=head)
    second = git_facts(repo, default_branch='main', remote_names=(), sha=head)
    assert first == second
    assert first.base_ref == 'refs/heads/main'
    assert first.head_sha == head
    assert len(first.log) == 1 and first.log[0].endswith(' head')
    assert any('b.txt' in line for line in first.diff_stat)
    assert first.merge_tree_rc == 0
    assert first.unknown == ()


def test_remote_tracking_ref_is_preferred_and_never_hardcoded_origin(repo):
    git(repo, 'update-ref', 'refs/remotes/up/main', git(repo, 'rev-parse', 'main'))
    facts = git_facts(repo, default_branch='main', remote_names=('up',), sha=None)
    assert facts.base_ref == 'refs/remotes/up/main'


def test_conflicting_branches_report_rc_one_not_a_verdict(repo):
    git(repo, 'checkout', '-q', 'main')
    (repo / 'b.txt').write_text('other\n')
    git(repo, 'add', 'b.txt')
    git(repo, 'commit', '-qm', 'conflict')
    facts = git_facts(repo, default_branch='main', remote_names=(), sha='work')
    assert facts.merge_tree_rc == 1


def test_unresolvable_base_is_typed_unknown_not_empty_lists(repo):
    facts = git_facts(repo, default_branch='no-such-branch', remote_names=(), sha=None)
    assert facts.base_sha is None
    assert facts.log is None and facts.diff_stat is None and facts.merge_tree_rc is None
    assert any('base ref' in reason for reason in facts.unknown)
    assert any('⛔ 不以空結果冒充沒有改動' in reason for reason in facts.unknown)


def test_missing_default_branch_from_api_is_typed_unknown(repo):
    facts = git_facts(repo, default_branch=None, remote_names=(), sha=None)
    assert 'base ref：repository 無預設分支（API 回 null）' in facts.unknown


def test_non_worktree_root_is_typed_unknown(tmp_path):
    facts = git_facts(tmp_path, default_branch='main', remote_names=(), sha=None)
    assert facts.head_sha is None
    assert facts.log is None and facts.diff_stat is None
    assert len(facts.unknown) == 1 and facts.unknown[0].startswith('rev-parse HEAD：')


def test_absent_revision_is_fact_absence_and_broken_git_raises(repo):
    assert rev_parse('refs/heads/nope', root=repo) is None
    broken = RecordedRunner([], default=(128, '', 'fatal: not a git repository'))
    with pytest.raises(LocalRevUnavailable, match='not a git repository'):
        rev_parse('HEAD', root=repo, runner=broken)
    with pytest.raises(LocalRevUnavailable):
        log_commits('a', 'b', root=repo, runner=broken)
    with pytest.raises(LocalRevUnavailable):
        diff_stat('a', 'b', root=repo, runner=broken)
    with pytest.raises(LocalGitUnavailable):
        merge_tree('a', 'b', root=repo, runner=RecordedRunner([], default=(128, '', 'boom')))
