"""CLI-001：消費 core/verbs.md §1 review 列（本機分支頭比對、git 附錄取源與失敗逐字）、
§2（檢查先於首次遠端寫入）、core/return.md「卡與身分」列。

本機 git 用 tmp 內真的工作樹跑，⛔ 不造假 git 輸出；GitHub 全由既有替身接住，⛔ 不碰網路。
每條各帶一個負控（roles/conduct-common.md §1）：宣稱可防回歸的斷言先對缺陷版本跑紅。
"""
import ast
import json
from pathlib import Path
import socket
import subprocess

import pytest

from wf.gh import localrev
from wf.verbs.review import NO_APPENDIX, NO_LOCAL_HEAD, review

from .test_brief_sections import RULES, WRITES, card, make_client, make_root

REVIEW_PY = RULES / 'cli/src/wf/verbs/review.py'
SCAFFOLD_RUN = subprocess.run  # 測試自己建工作樹用的真 runner；護欄只管受測程式碼跑什麼


ALLOWED_GIT = {'rev-parse', 'log', 'diff'}  # review 的本機唯讀取源；⛔ 不含任何寫入型子指令


def git_subcommand(argv):
    """`git [全域旗標…] <子指令>` 的子指令；`-C` 另吃一個值。不是 git ⇒ None。"""
    if not argv or Path(argv[0]).name != 'git':
        return None
    rest = list(argv[1:])
    while rest:
        token = rest.pop(0)
        if token == '-C' and rest:
            rest.pop(0)
        elif not token.startswith('-'):
            return token
    return None


def strict_offline(monkeypatch, token):
    """嚴格放行（需求方 2026-09-14 裁定）：只有本機 git 的 rev-parse／log／diff 可跑——
    `review` 的本機分支頭比對與 git 附錄走 gh/localrev.py 這三個唯讀子指令（CLI-001）。
    字串型 shell command、gh／curl／wget／ssh、其他 git 子指令與任何其他子程序一律擋；
    socket 連線一律擋（roles/conduct-common.md §1）。"""
    real = subprocess.run

    def denied(*args, **kwargs):
        raise AssertionError(token)

    def guarded(argv, *args, **kwargs):
        if isinstance(argv, (str, bytes)) or git_subcommand([str(item) for item in argv]) not in ALLOWED_GIT:
            denied()
        return real(argv, *args, **kwargs)

    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(subprocess, 'run', guarded)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    strict_offline(monkeypatch, 'APPENDIX_DENIED')
    with pytest.raises(AssertionError, match='APPENDIX_DENIED'):
        subprocess.run(['gh', 'api', 'negative-control'])
    with pytest.raises(AssertionError, match='APPENDIX_DENIED'):
        subprocess.run('git rev-parse HEAD')          # 字串型 shell command
    with pytest.raises(AssertionError, match='APPENDIX_DENIED'):
        subprocess.run(['git', 'push', 'origin'])     # 寫入型 git 子指令
    with pytest.raises(AssertionError, match='APPENDIX_DENIED'):
        subprocess.run(['python', '-c', 'pass'])      # 其他子程序


def git(root, *args):
    return raw(root, *args).strip()


def raw(root, *args):
    """未經 strip 的 stdout：`diff --stat` 每檔一列的行首空白是輸出的一部分，⛔ 不可修剪。
    走 SCAFFOLD_RUN：建工作樹要 init／commit／checkout，那些⛔ 不在受測程式碼的放行集合內。"""
    return SCAFFOLD_RUN(('git', '-C', str(root), *args), capture_output=True, text=True,
                        check=True, timeout=60).stdout


def worktree(root, *, branch='wf/WF-001'):
    """root 上開一棵真工作樹：main 有一顆只在 main 的 commit，branch 有一顆只在 branch 的 commit。
    回 (main_sha, branch_sha)；兩邊各自獨有的檔案，讓三點與兩點的改動面可辨。"""
    git(root, 'init', '-q', '-b', 'main')
    git(root, 'config', 'user.email', 'cli-001@example.invalid')
    git(root, 'config', 'user.name', 'cli-001')
    (root / 'seed.txt').write_text('seed\n', encoding='utf-8')
    git(root, 'add', '--', 'seed.txt')
    git(root, 'commit', '-q', '-m', 'seed')
    git(root, 'checkout', '-q', '-b', branch)
    (root / 'on_branch.txt').write_text('branch\n', encoding='utf-8')
    git(root, 'add', '--', 'on_branch.txt')
    git(root, 'commit', '-q', '-m', '只在分支上的 commit')
    branch_sha = git(root, 'rev-parse', 'HEAD')
    git(root, 'checkout', '-q', 'main')
    (root / 'only_on_main.txt').write_text('main\n', encoding='utf-8')
    git(root, 'add', '--', 'only_on_main.txt')
    git(root, 'commit', '-q', '-m', '只在預設分支上的 commit')
    return git(root, 'rev-parse', 'HEAD'), branch_sha


def run_review(tmp_path, root, client, *, role='executor', data=None):
    path = tmp_path / 'return.json'
    path.write_text(json.dumps({} if data is None else data, ensure_ascii=False), encoding='utf-8')
    lines = []
    result = review(10, file=path, role=role, client=client, root=root, emit=lines.append)
    assert result.printed == tuple(lines)
    posted = [kwargs for name, kwargs in client.calls if name == 'post_comment']
    return result, lines, posted


def heads(mapping):
    def branch_head(branch):
        return mapping[branch]
    return branch_head


# ── 驗收 1／2：本機分支頭比對三案互不相同 ─────────────────────────────────────

@pytest.mark.parametrize('case', ['equal', 'mismatch', 'nongit'])
@pytest.mark.parametrize('shape', ['branch', 'null-branch'])
def test_local_head_three_cases(tmp_path, case, shape):
    """驗收 1／2：(a) 本機＝遠端⇒兩句都⛔ 不印；(b) 不等⇒恰一行含兩個 40 碼 SHA；
    (c) 非 git 工作樹⇒恰印「未能比對本機分支頭」。三案 rc 皆 0 且 stdout 互不相同。
    `null-branch`＝卡面 branch null 且卡在規劃：比對對象是 refs/heads/main，⛔ 不是字面 'None'。"""
    root = make_root(tmp_path, project=False)
    branch = None if shape == 'null-branch' else 'wf/WF-001'
    if case == 'nongit':
        main_sha, branch_sha = 'd' * 40, 'e' * 40
    else:
        main_sha, branch_sha = worktree(root, branch='wf/WF-001')
    remote = branch_sha if shape == 'branch' else main_sha
    if case == 'mismatch':
        remote = 'f' * 40
    current = card(branch=branch, source_sha='b' * 40,
                   stage='執行' if shape == 'branch' else '規劃')
    client = make_client(current, branch_head=heads({'main': main_sha, 'wf/WF-001': remote}
                                                   if shape == 'branch' else
                                                   {'main': remote, 'wf/WF-001': branch_sha}))
    result, lines, posted = run_review(tmp_path, root, client)
    assert result.rc == 0 and [kwargs['first_line'] for kwargs in posted] == ['wf:return']
    mismatch = [line for line in lines if line.startswith('本機分支頭 ≠ 遠端頭')]
    local_expected = main_sha if shape == 'null-branch' else branch_sha
    if case == 'equal':
        assert NO_LOCAL_HEAD not in lines and mismatch == []
    elif case == 'mismatch':
        assert NO_LOCAL_HEAD not in lines and len(mismatch) == 1
        assert local_expected in mismatch[0] and remote in mismatch[0]
        assert len([word for word in mismatch[0].replace('：', ' ').split()
                    if len(word) == 40]) == 2, mismatch[0]
    else:
        assert lines.count(NO_LOCAL_HEAD) == 1 and mismatch == []
    assert 'None' not in ' '.join(lines)
    print('LOCAL_HEAD', shape, case, [line for line in lines if NO_LOCAL_HEAD in line or mismatch])


def test_local_head_cases_are_mutually_distinguishable(tmp_path):
    """驗收 1 的負控：三案的本機比對行必須兩兩不同——缺陷版本三案都印同一句。"""
    stdouts = {}
    for case in ('equal', 'mismatch', 'nongit'):
        base = tmp_path / case
        base.mkdir()
        root = make_root(base, project=False)
        if case == 'nongit':
            main_sha, branch_sha = 'd' * 40, 'e' * 40
        else:
            main_sha, branch_sha = worktree(root)
        remote = 'f' * 40 if case == 'mismatch' else branch_sha
        client = make_client(card(branch='wf/WF-001', source_sha='b' * 40),
                             branch_head=heads({'main': main_sha, 'wf/WF-001': remote}))
        _, lines, _ = run_review(base, root, client)
        stdouts[case] = tuple(line for line in lines
                              if NO_LOCAL_HEAD in line or line.startswith('本機分支頭 ≠ 遠端頭'))
    assert len(set(stdouts.values())) == 3, stdouts
    print('LOCAL_HEAD_DISTINCT', stdouts)


# ── 驗收 3／4：git 附錄成功路徑 ────────────────────────────────────────────────

def test_git_appendix_lists_commits_and_diffstat(tmp_path):
    """驗收 3：commit 清單列數＝獨立跑 `git log --no-color --pretty=format:%H %s <base>..<head>`
    的列數；改動面每檔一列；body ⛔ 不含逐字「未能取得 git 附錄」。"""
    root = make_root(tmp_path, project=False)
    main_sha, branch_sha = worktree(root)
    client = make_client(card(branch='wf/WF-001', source_sha='b' * 40),
                         branch_head=heads({'main': main_sha, 'wf/WF-001': branch_sha}))
    result, lines, posted = run_review(tmp_path, root, client)
    assert result.rc == 0 and len(posted) == 1
    body = posted[0]['body']
    independent = raw(root, 'log', '--no-color', '--pretty=format:%H %s',
                      f'{main_sha}..{branch_sha}').splitlines()
    stat = raw(root, 'diff', '--stat', '--no-color', f'{main_sha}...{branch_sha}').splitlines()
    assert independent and stat
    for source in (lines, body.splitlines()):
        block = section(source, 'commit 清單')
        assert block == independent, (block, independent)
        assert section(source, '改動面') == stat
    assert NO_APPENDIX not in body
    assert 'on_branch.txt' in ' '.join(stat) and 'only_on_main.txt' not in ' '.join(stat)
    print('APPENDIX', len(independent), 'commit', len(stat), '列改動面')


def section(lines, head):
    """取 `<head>（…）：` 之後、下一個標題或結尾之前的那幾列。"""
    out, seen = [], False
    for line in lines:
        if line.startswith(head) and line.endswith('：'):
            seen = True
            continue
        if seen:
            if line.endswith('：') or line.startswith('```') or not line:
                break
            out.append(line)
    return out


def test_diff_stat_uses_three_dot_range(tmp_path):
    """驗收 4 負控：同一棵樹下，三點的改動面⛔ 不含 only_on_main.txt，兩點會含——
    證明本卡真的用三點，而非碰巧兩者相同。"""
    root = make_root(tmp_path, project=False)
    main_sha, branch_sha = worktree(root)
    three = localrev.diff_stat(main_sha, branch_sha, root=root)
    two = raw(root, 'diff', '--stat', '--no-color', f'{main_sha}..{branch_sha}').splitlines()
    assert 'only_on_main.txt' not in ' '.join(three)
    assert 'only_on_main.txt' in ' '.join(two), two
    assert [node for node in ast.walk(ast.parse(Path(localrev.__file__).read_text(encoding='utf-8')))
            if isinstance(node, ast.JoinedStr) and '...' in ast.unparse(node)]
    print('THREE_DOT', three, 'TWO_DOT', two)


# ── 驗收 5：失敗路徑逐字 ──────────────────────────────────────────────────────

@pytest.mark.parametrize('case', ['nongit', 'base-absent', 'head-absent'])
def test_git_appendix_failure_is_verbatim_with_reason(tmp_path, case):
    """驗收 5：stdout 與 body 各恰一行逐字「未能取得 git 附錄：<原因>」，原因非空；rc=0；
    ⛔ 不印空 commit 區段、⛔ 不印空 diffstat、⛔ 不冒充無改動。"""
    root = make_root(tmp_path, project=False)
    if case == 'nongit':
        main_sha, branch_sha = 'd' * 40, 'e' * 40
    else:
        main_sha, branch_sha = worktree(root)
        if case == 'base-absent':
            main_sha = 'd' * 40
        else:
            branch_sha = 'e' * 40
    client = make_client(card(branch='wf/WF-001', source_sha='b' * 40),
                         branch_head=heads({'main': main_sha, 'wf/WF-001': branch_sha}))
    result, lines, posted = run_review(tmp_path, root, client)
    assert result.rc == 0 and len(posted) == 1
    body = posted[0]['body']
    failures = [line for line in lines if line.startswith(NO_APPENDIX)]
    assert len(failures) == 1 and body.count(NO_APPENDIX) == 1
    assert failures[0] in body.splitlines()
    prefix, _, reason = failures[0].partition('：')
    assert prefix == NO_APPENDIX and reason.strip(), failures[0]
    for head in ('commit 清單', '改動面'):
        assert not [line for line in body.splitlines() if line.startswith(head)]
    assert '無改動' not in body
    print('APPENDIX_FAILURE', case, failures[0])


# ── 驗收 6：規則與實作一致 ────────────────────────────────────────────────────

CLAIMS = {
    'core/verbs.md': ('base＝遠端預設分支頭', 'head＝已補進交回單的 `source_sha`',
                      'project root 的本機工作樹', '未能取得 git 附錄：<原因>'),
    'core/return.md': ('base＝遠端預設分支頭', 'head＝`source_sha`',
                       'project root 的本機工作樹', '未能取得 git 附錄：<原因>'),
}


def row(path, needle):
    """規則檔裡含 needle 的那一列；兩個掃描面各只有一列（多於一列即斷言失敗）。"""
    rows = [line for line in (RULES / path).read_text(encoding='utf-8').splitlines()
            if needle in line]
    assert len(rows) == 1, (path, needle, len(rows))
    return rows[0]


def test_rules_and_docstring_declare_no_permanent_degradation():
    """驗收 6：兩個掃描面各逐字載明取源／計算位置／失敗逐字；review.py 的模組 docstring
    ⛔ 不再含「刻意降級」，也⛔ 不再宣告 localgit 無本機頭／log／diffstat 介面。
    掃描面＝core/verbs.md §1 review 列與 core/return.md「卡與身分」列，⛔ 不含 archive/、docs/、cli/tests/。"""
    review_row = row('core/verbs.md', '`review <card> --file')
    identity_row = row('core/return.md', '| 卡與身分 |')
    for text, claims in ((review_row, CLAIMS['core/verbs.md']), (identity_row, CLAIMS['core/return.md'])):
        for claim in claims:
            assert claim in text, (claim, text)
    doc = ast.get_docstring(ast.parse(REVIEW_PY.read_text(encoding='utf-8')))
    assert doc and '刻意降級' not in doc
    assert 'localgit' not in doc and 'merge_tree' not in doc
    assert 'localrev' in doc
    assert '刻意降級' in '刻意降級：只寫在註解的降級'  # 負控：檢查字串本身命中得了
    print('RULES_ALIGNED', len(review_row), len(identity_row), doc.splitlines()[0])


# ── 驗收 7：本機讀取先於首次遠端寫入 ──────────────────────────────────────────

@pytest.mark.parametrize('role', ['executor', 'reviewer'])
def test_local_reads_precede_the_first_remote_write(tmp_path, monkeypatch, role):
    """驗收 7：兩條路徑上所有 localrev 呼叫的序號 < 第一個 WRITES 呼叫的序號。
    負控＝把 localrev 的呼叫全部記進同一條序列，⛔ 不另建第二本帳。"""
    root = make_root(tmp_path, project=False)
    main_sha, branch_sha = worktree(root)
    client = make_client(card(branch='wf/WF-001', source_sha=branch_sha),
                         branch_head=heads({'main': main_sha, 'wf/WF-001': branch_sha}))
    real = subprocess.run

    def recorded(argv, *args, **kwargs):
        client.calls.append(('localrev', {'argv': list(argv)}))
        return real(argv, *args, **kwargs)

    monkeypatch.setattr(localrev.subprocess, 'run', recorded)
    result, _, posted = run_review(tmp_path, root, client, role=role)
    assert result.rc == 0 and len(posted) == 1
    names = [name for name, _ in client.calls]
    local = [index for index, name in enumerate(names) if name == 'localrev']
    writes = [index for index, name in enumerate(names) if name in WRITES]
    assert local and writes, names
    assert max(local) < min(writes), names
    print('ORDER', role, 'localrev', local, 'writes', writes)
