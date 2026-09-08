"""消費 core/dispatch.md 基線列、core/verbs.md §1 brief 列（reviewer 三印）。
S11 驗收 4／8／10：merge-tree 用本機 fixture repo，其餘遠端事實由手構替身接住。
"""
import ast
from pathlib import Path
import re
import shutil
import subprocess

import pytest

from .test_brief_sections import (RULES, card, emitted, make_client, make_root, sections)
from wf.gh.client import NotFound
from wf.gh.localgit import LocalGitUnavailable, merge_tree
from wf.verbs.brief import TARGETS, brief, run

LOCALGIT = RULES / 'cli/src/wf/gh/localgit.py'
FORBIDDEN = ('push', 'commit', 'fetch', 'clone', 'reset', 'checkout', 'apply', 'am', 'merge')


def git(root, *args, check=True):
    return subprocess.run(('git', '-C', str(root)) + args, capture_output=True, text=True,
                          check=check)


def git_repo(root):
    """回傳 (base, left, right)：left 與 right 各自改同一行 ⇒ 兩者 merge-tree 必衝突。"""
    if shutil.which('git') is None:
        pytest.skip('本機沒有 git')
    git(root, 'init', '-q', '-b', 'main')
    git(root, 'config', 'user.email', 'fixture@example.invalid')
    git(root, 'config', 'user.name', 'fixture')
    (root / 'f.txt').write_text('base\n', encoding='utf-8')
    git(root, 'add', 'f.txt')
    git(root, 'commit', '-qm', 'base')
    base = git(root, 'rev-parse', 'HEAD').stdout.strip()
    (root / 'f.txt').write_text('left\n', encoding='utf-8')
    git(root, 'commit', '-qam', 'left')
    left = git(root, 'rev-parse', 'HEAD').stdout.strip()
    git(root, 'checkout', '-q', base)
    (root / 'f.txt').write_text('right\n', encoding='utf-8')
    git(root, 'commit', '-qam', 'right')
    return base, left, git(root, 'rev-parse', 'HEAD').stdout.strip()


def baseline(lines):
    return dict(sections(lines))['基線'][1:]


def test_baseline_uses_merge_base_when_the_branch_exists(tmp_path):
    """驗收 4：有分支 ⇒ merge-base 40 碼，且不印無分支。"""
    root = make_root(tmp_path)
    client = make_client(card(branch='feat'), branch_head='c' * 40, merge_base='b' * 40)
    _, lines = emitted(client, root)
    assert baseline(lines) == ['合併基底 SHA：' + 'b' * 40]
    assert len(baseline(lines)[0].split('：')[1]) == 40
    assert ('merge_base', {'base': 'main', 'head': 'feat'}) in client.calls


@pytest.mark.parametrize('branch', [None, 'gone'])
def test_baseline_falls_back_to_main_head(tmp_path, branch):
    """驗收 4：branch null 或遠端無此分支 ⇒ 印無分支並用 main 頭。"""
    def head(branch):
        if branch != 'main':
            raise NotFound(branch)
        return 'a' * 40
    root = make_root(tmp_path, name=f'root-{branch}')
    _, lines = emitted(make_client(card(branch=branch), branch_head=head), root)
    assert baseline(lines) == ['無分支，基線＝main 頭', '合併基底 SHA：' + 'a' * 40]


def test_reviewer_lists_branch_and_source_sha(tmp_path):
    """驗收 4：--for reviewer 另列被審分支與 source_sha；executor 不列（負控）。"""
    root = make_root(tmp_path)
    data = card(branch='feat', source_sha='c' * 40)
    _, lines = emitted(make_client(data, branch_head='c' * 40), root, 'reviewer')
    assert baseline(lines)[1:3] == ['被審分支：feat', '來源 SHA：' + 'c' * 40]
    _, executor = emitted(make_client(data, branch_head='c' * 40), root)
    assert baseline(executor) == ['合併基底 SHA：' + 'b' * 40]


def test_reviewer_prints_branch_head_mismatch(tmp_path):
    """驗收 8（印一）：分支頭 ≠ 來源 SHA。"""
    root = make_root(tmp_path)
    _, lines = emitted(make_client(card(branch='feat', source_sha='c' * 40),
                                   branch_head='d' * 40), root, 'reviewer')
    assert f"分支頭 ≠ 來源 SHA：{'d' * 40} ≠ {'c' * 40}" in baseline(lines)
    _, same = emitted(make_client(card(branch='feat', source_sha='c' * 40),
                                  branch_head='c' * 40), root, 'reviewer')
    assert not [line for line in baseline(same) if line.startswith('分支頭 ≠')]


def test_reviewer_prints_source_sha_not_pushed(tmp_path):
    """驗收 8（印二）：來源 SHA 未 push；已 push 是負控。"""
    root = make_root(tmp_path)
    data = card(branch='feat', source_sha='c' * 40)
    _, lines = emitted(make_client(data, branch_head='c' * 40, commit_exists=False),
                       root, 'reviewer')
    assert '來源 SHA 未 push' in baseline(lines)
    _, pushed = emitted(make_client(data, branch_head='c' * 40, commit_exists=True),
                        root, 'reviewer')
    assert '來源 SHA 未 push' not in baseline(pushed)
    assert '來源 SHA 已 push' in baseline(pushed)


def test_reviewer_prints_merge_tree_conflict(tmp_path):
    """驗收 8（印三）：本機 fixture repo 的兩個衝突 commit ⇒ merge-tree 衝突；可合併是負控。"""
    root = make_root(tmp_path)
    base, left, right = git_repo(root)
    data = card(branch='feat', source_sha=right)
    _, lines = emitted(make_client(data, branch_head=right, merge_base=left), root, 'reviewer')
    assert 'merge-tree 衝突' in baseline(lines)
    _, clean = emitted(make_client(data, branch_head=right, merge_base=base), root, 'reviewer')
    assert 'merge-tree 無衝突' in baseline(clean)
    assert merge_tree(left, right, root=root) == 1 and merge_tree(base, right, root=root) == 0


def test_merge_tree_unavailable_is_printed_not_raised(tmp_path):
    """驗收 8：本機 repo 不可用 ⇒ 印未能比對 merge-tree，rc 仍 0。"""
    root = make_root(tmp_path)
    data = card(branch='feat', source_sha='c' * 40)
    result, lines = emitted(make_client(data, branch_head='c' * 40), root, 'reviewer')
    assert result.rc == 0 and '未能比對 merge-tree' in baseline(lines)
    with pytest.raises(LocalGitUnavailable):
        merge_tree('a' * 40, 'b' * 40, root=root)


def test_executor_never_runs_the_three_reviewer_prints(tmp_path):
    """驗收 8 的負控：executor 段不含三印，也不呼叫 commit_exists。"""
    root = make_root(tmp_path)
    client = make_client(card(branch='feat', source_sha='c' * 40), branch_head='d' * 40,
                         commit_exists=False)
    _, lines = emitted(client, root)
    assert baseline(lines) == ['合併基底 SHA：' + 'b' * 40]
    assert 'commit_exists' not in [name for name, _ in client.calls]


def test_localgit_wraps_merge_tree_only():
    """驗收 10：gh/localgit.py 只包 merge-tree；負控證明檢查會響。"""
    text = LOCALGIT.read_text(encoding='utf-8')
    literals = [node for node in ast.walk(ast.parse(text)) if isinstance(node, ast.List)]
    argv = [[item.value for item in node.elts if isinstance(item, ast.Constant)]
            for node in literals]
    assert len(argv) == 1 and argv[0][0] == 'git' and 'merge-tree' in argv[0]
    assert not [word for word in argv[0] if word in FORBIDDEN]
    fake = [node for node in ast.walk(ast.parse("['git', 'push', 'origin']"))
            if isinstance(node, ast.List)][0]
    assert [item.value for item in fake.elts if item.value in FORBIDDEN] == ['push']
    assert re.findall(r"'git'", text) == ["'git'"]


def test_run_wires_for_choices_and_card_id_lookup(tmp_path):
    """verbs.md §1：`--for` 值域＝TARGETS 的鍵（S12 掛 closeout）；卡ID 可查 issue 號。"""
    root = make_root(tmp_path)
    assert sorted(TARGETS) == ['executor', 'reviewer']
    assert run(['10', '--for', 'reviewer'], client=make_client(card()), root=root) == 0
    with pytest.raises(SystemExit):
        run(['10', '--for', 'closeout'], client=make_client(card()), root=root)
    lines = []
    result = brief('WF-001', target='executor', client=make_client(card()), root=root,
                   emit=lines.append)
    assert result.rc == 0 and result.card['card_id'] == 'WF-001'
    with pytest.raises(NotFound):
        brief('WF-404', target='executor', client=make_client(card()), root=root,
              emit=lines.append)
