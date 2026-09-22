"""W1.7 驗收 (4)(5) 的本機側：rev-parse／log／diff --stat／merge-tree。

母體＝tmp_path 內臨時建立的 git repo，⛔ 不釘本 repo 的任何 SHA、內容或缺檔。
"""
import json
import subprocess

import pytest

from wfx.core.context import Context
from wfx.gh.facts import git_facts
from wfx.gh.localgit import LocalGitUnavailable, merge_tree
from wfx.gh.localrev import LocalRevUnavailable, diff_stat, log_commits, rev_parse
from wfx.gh.target import TargetError, remote_names_for, resolve_repository
from wfx.verbs.facts import collect
from wfx.verbs.main import main

from .fakes import FakeClient, FakeWriter, RecordedRunner, fixed_base, snapshot


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
    first = git_facts(repo, base=fixed_base('main'), remote_names=(), sha=head)
    second = git_facts(repo, base=fixed_base('main'), remote_names=(), sha=head)
    assert first == second
    assert first.base_ref == 'refs/heads/main'
    assert first.head_sha == head
    assert len(first.log) == 1 and first.log[0].endswith(' head')
    assert any('b.txt' in line for line in first.diff_stat)
    assert first.merge_tree_rc == 0
    assert first.unknown == ()


def test_remote_tracking_ref_is_preferred_and_never_hardcoded_origin(repo):
    git(repo, 'update-ref', 'refs/remotes/up/main', git(repo, 'rev-parse', 'main'))
    facts = git_facts(repo, base=fixed_base('main'), remote_names=('up',), sha=None)
    assert facts.base_ref == 'refs/remotes/up/main'


def test_conflicting_branches_report_rc_one_not_a_verdict(repo):
    git(repo, 'checkout', '-q', 'main')
    (repo / 'b.txt').write_text('other\n')
    git(repo, 'add', 'b.txt')
    git(repo, 'commit', '-qm', 'conflict')
    facts = git_facts(repo, base=fixed_base('main'), remote_names=(), sha='work')
    assert facts.merge_tree_rc == 1


def test_unresolvable_base_is_typed_unknown_not_empty_lists(repo):
    facts = git_facts(repo, base=fixed_base('no-such-branch'), remote_names=(), sha=None)
    assert facts.base_sha is None
    assert facts.log is None and facts.diff_stat is None and facts.merge_tree_rc is None
    assert any('本機解不到 no-such-branch' in reason for reason in facts.unknown)
    assert any('⛔ 不以空結果冒充沒有改動' in reason for reason in facts.unknown)


def test_unresolved_base_from_the_resolver_is_typed_unknown(repo):
    reason = 'base ref：repository 無預設分支（API 回 null）'
    facts = git_facts(repo, base=fixed_base(None, unknown=reason), remote_names=(), sha=None)
    assert reason in facts.unknown
    assert facts.base_ref is None and facts.log is None


def test_non_worktree_root_is_typed_unknown(tmp_path):
    facts = git_facts(tmp_path, base=fixed_base('main'), remote_names=(), sha=None)
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


def build_repo_with_remote(root, remote_slug='o/r'):
    """落後的本機 `main`、已前進的 `refs/remotes/up/main`，其上再一筆本次成果。

    remote 刻意⛔ 不叫 origin：候選是從本機 remote 查出來的，⛔ 不寫死名字。
    """
    root.mkdir()
    git(root, 'init', '-q', '-b', 'main')
    git(root, 'config', 'user.email', 't@example.invalid')
    git(root, 'config', 'user.name', 't')
    git(root, 'remote', 'add', 'up', f'git@github.com:{remote_slug}.git')
    (root / 'a.txt').write_text('base\n')
    git(root, 'add', 'a.txt')
    git(root, 'commit', '-qm', 'base')
    git(root, 'checkout', '-qb', 'work')
    (root / 'upstream-only.txt').write_text('已在合併目標上\n')
    git(root, 'add', 'upstream-only.txt')
    git(root, 'commit', '-qm', 'upstream')
    git(root, 'update-ref', 'refs/remotes/up/main', git(root, 'rev-parse', 'HEAD'))
    (root / 'feature.txt').write_text('本次成果\n')
    git(root, 'add', 'feature.txt')
    git(root, 'commit', '-qm', 'feature')
    return root, git(root, 'rev-parse', 'HEAD')


@pytest.fixture
def repo_with_remote(tmp_path):
    return build_repo_with_remote(tmp_path / 'rr')


def collected(root, task_id, sha):
    """同一 repo／同一 head／同一 API 快照，只有 `--task` 的寫法不同。"""
    return collect(Context(root, task_id), task_id, sha,
                   client=FakeClient(snapshot(pull_requests=())), env={})


def test_full_task_form_gets_the_same_remote_base_as_the_short_form(repo_with_remote):
    """`o/r#370` 與 `370` 對同一 repository 必須取到同一組本機 remote-tracking 候選。

    完整寫法曾把「身分已知」當成「不必查本機 remote」，於是退回較舊的 `refs/heads/main`，
    把已在合併目標上的改動算成本次成果。
    """
    root, head = repo_with_remote
    short, full = collected(root, '370', head), collected(root, 'o/r#370', head)
    assert short.git.base_ref == 'refs/remotes/up/main'
    assert full.git == short.git
    assert len(short.git.log) == 1
    assert [row for row in short.git.diff_stat if 'upstream-only.txt' in row] == []


def test_a_slug_without_a_matching_local_remote_falls_back_to_the_local_branch(repo_with_remote):
    """本機⛔ 無指向該 repository 的 remote＝⛔ 無 remote-tracking 候選（邊界，不是缺陷）。"""
    root, head = repo_with_remote
    facts = collected(root, 'other/elsewhere#370', head)
    assert facts.git.base_ref == 'refs/heads/main'


def test_a_broken_remote_setting_fails_loud_in_both_task_forms(repo_with_remote):
    """設定鍵指向不存在的 remote＝precedence 不成立；⛔ 不得因為身分已知就靜默換候選。"""
    root, head = repo_with_remote
    for task_id in ('370', 'o/r#370'):
        context = Context(root, task_id, {'rules': None, 'remote': 'zz', 'project': None})
        with pytest.raises(TargetError, match='remote 不存在'):
            collect(context, task_id, head,
                    client=FakeClient(snapshot(pull_requests=())), env={})


@pytest.mark.parametrize('remote_slug, task_slug', (('o/r', 'O/R'), ('O/R', 'o/r')))
def test_the_same_repository_in_another_letter_case_keeps_the_same_remote_base(
        tmp_path, remote_slug, task_slug):
    """GitHub 的 owner/name 大小寫不同仍是同一個 repository，候選⛔ 不得因字面不同被濾掉。

    兩個方向都要測：remote URL 小寫／task 大寫，以及 remote URL 大寫／task 小寫；
    否則只因為複製來的寫法換了大小寫，就會退回較舊的本機 branch 並多算 log／diff。
    """
    root, head = build_repo_with_remote(tmp_path / 'case', remote_slug)
    short, full = collected(root, '370', head), collected(root, f'{task_slug}#370', head)
    assert short.git.base_ref == 'refs/remotes/up/main'
    assert full.git == short.git
    assert len(full.git.log) == 1
    assert [row for row in full.git.diff_stat if 'upstream-only.txt' in row] == []


def build_repo_with_two_remotes(root, up_slug='o/r', mirror_slug='O/R'):
    """`up` 之外再加一個 `mirror`；兩個 slug 決定它們是不是同一個 repository。

    同時把這棵樹當第 3 層（`.wf/`），三個動詞才能都從真正的進入點跑。
    """
    root, head = build_repo_with_remote(root, up_slug)
    git(root, 'remote', 'add', 'mirror', f'https://github.com/{mirror_slug}.git')
    (root / '.wf').mkdir()
    (root / '.wf' / 'model-policy.md').write_text('# 專案層政策\n具體模型名稱⛔ 不住這裡。\n',
                                                 encoding='utf-8')
    (root / '.wf' / 'config.json').write_text(
        json.dumps({'rules': None, 'remote': None, 'project': {'owner': 'o', 'number': 9}}),
        encoding='utf-8')
    return root, head


def run_verb(root, rules_root, verb, task, sha):
    """真正的進入點；`write` 一律 `--dry-run`＋`FakeWriter`＝遠端零 mutation。"""
    extra = {'facts': ('--sha', sha),
             'brief': ('--role', '執行者', '--stage', '執行', '--rules-root', str(rules_root)),
             'write': ('--field', '狀態=待辦', '--dry-run', '--rules-root', str(rules_root))}[verb]
    writer = FakeWriter()
    injected = {'writer': writer} if verb == 'write' else {}
    rc = main(['--project-root', str(root), verb, '--task', task, *extra],
              client=FakeClient(snapshot(pull_requests=())), env={}, **injected)
    return rc, writer.calls


@pytest.mark.parametrize('up_slug, mirror_slug', (('o/r', 'O/R'), ('O/R', 'o/r')))
def test_two_remotes_of_one_repository_do_not_make_the_short_task_ambiguous(
        tmp_path, rules_root, user_root, capsys, up_slug, mirror_slug):
    """同一 repository 的兩個 remote 只差大小寫＝一個身分；簡式 `370` ⛔ 不得被判成多義。

    三動詞共用同一條解析，任一個回 rc=1 就等於整條派工在審核用 checkout 上停擺；
    兩個方向都要測，否則只證明了「第一個候選剛好是小寫」。
    """
    root, head = build_repo_with_two_remotes(tmp_path / f'two-{up_slug[0]}', up_slug, mirror_slug)
    for verb in ('facts', 'brief', 'write'):
        for task in ('370', 'o/r#370', 'O/R#370'):
            rc, calls = run_verb(root, rules_root, verb, task, head)
            capsys.readouterr()
            assert (verb, task, rc, calls) == (verb, task, 0, [])


def test_all_three_task_forms_get_the_same_merged_remote_candidates(tmp_path):
    """候選一致＝同一組、同一順序；顯示 slug 取候選順序中第一個的字面（deterministic）。"""
    root, head = build_repo_with_two_remotes(tmp_path / 'merged')
    target = resolve_repository(root)
    assert target.remote_names == ('mirror', 'up')   # ＝`git remote` 的列出順序，合併⛔ 不重排
    assert target.slug == 'O/R'                      # mirror 的字面，⛔ 不改寫成別的大小寫
    assert '合併 mirror、up' in target.provenance.detail
    for task_slug in ('o/r', 'O/R'):
        assert remote_names_for(root, task_slug) == target.remote_names
    short = collected(root, '370', head)
    assert short.git.base_ref == 'refs/remotes/up/main'
    assert collected(root, 'O/R#370', head).git == short.git


def test_two_remotes_of_different_repositories_still_fail_loud_in_all_three_verbs(
        tmp_path, rules_root, user_root, capsys):
    """真正不同的 repository＝多義，照樣硬擋、零 mutation；⛔ 不得因合併同身分就改成挑第一個。"""
    root, head = build_repo_with_two_remotes(tmp_path / 'distinct', 'o/r', 'other/r')
    for verb in ('facts', 'brief', 'write'):
        rc, calls = run_verb(root, rules_root, verb, '370', head)
        err = capsys.readouterr().err
        assert (verb, rc, calls) == (verb, 1, [])
        assert 'repository 候選不唯一：o/r←up；other/r←mirror' in err
