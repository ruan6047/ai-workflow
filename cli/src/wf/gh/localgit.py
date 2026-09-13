"""消費 core/verbs.md §1 brief 列的「`merge-tree` 衝突」與 core/dispatch.md 基線列；另供本機 Git 身分
六類事實：worktree top-level、per-worktree git-dir、git common-dir、HEAD SHA 與 current ref、
selected remote name（住 `RepositoryIdentity.provenance`）、Git 展開後的 fetch/push URL，分別保存、
⛔ 不折成單一 root（linked worktree 的 git-dir≠common-dir；submodule 的 git-dir 是絕對路徑）。

本機 git 的唯一入口：`merge_tree` 只包 `git merge-tree --write-tree`，`local_git_facts` 只跑唯讀
plumbing。不連網、不寫本機 repo、不解析輸出內容語意（第零條）。rc 由呼叫端印，⛔ 不擋
（`core/verbs.md` §2「其餘一律印」）。
"""
from __future__ import annotations

from dataclasses import dataclass
import subprocess


class LocalGitUnavailable(RuntimeError):
    """本機 repo 不可用、git 未能執行或 merge-tree 自身失敗；呼叫端印，不當成無衝突。"""


@dataclass(frozen=True)
class RemoteFact:
    name: str
    fetch_url: str
    push_url: str
    is_upstream_of_current: bool


@dataclass(frozen=True)
class LocalGitFacts:
    top_level: str
    git_dir: str
    git_common_dir: str
    head_sha: str | None
    current_ref: str | None
    remotes: tuple[RemoteFact, ...]


def _run(args, *, root, runner):
    runner = subprocess.run if runner is None else runner
    try:
        return runner(['git', '-C', str(root), *args], capture_output=True, text=True, check=False,
                      timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise LocalGitUnavailable(str(exc)) from exc


def merge_tree(base, head, *, root='.', runner=None):
    """回傳 rc：0＝可合併、1＝有衝突（git merge-tree 的既有語意，⛔ 不重新定義）。"""
    result = _run(['merge-tree', '--write-tree', str(base), str(head)], root=root, runner=runner)
    if result.returncode not in (0, 1):
        raise LocalGitUnavailable((result.stderr or '').strip() or f'rc={result.returncode}')
    return result.returncode


def local_git_facts(root, *, runner=None):
    """六類事實各自取源（`--path-format=absolute` 讓 git-dir／common-dir 不含相對 cwd 前綴）；
    root 不在 git 工作樹內＝None（事實缺席，⛔ 不是錯誤）。"""
    def out(*args):
        result = _run(args, root=root, runner=runner)
        return result.stdout.strip() if result.returncode == 0 else None

    layout = out('rev-parse', '--path-format=absolute', '--show-toplevel', '--git-dir', '--git-common-dir')
    if layout is None:
        return None
    top_level, git_dir, common_dir = layout.splitlines()[:3]
    ref = out('symbolic-ref', '--quiet', 'HEAD')
    upstream = out('for-each-ref', '--format=%(upstream:remotename)', ref) if ref else None
    remotes = tuple(RemoteFact(name, out('remote', 'get-url', name) or '',
                               out('remote', 'get-url', '--push', name) or '', name == upstream)
                    for name in (out('remote') or '').split())
    return LocalGitFacts(top_level, git_dir, common_dir, out('rev-parse', '--verify', '--quiet', 'HEAD'),
                         ref, remotes)
