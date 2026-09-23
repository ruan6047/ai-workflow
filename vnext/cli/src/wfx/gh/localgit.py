"""本機 git 的另外兩組唯讀事實：`merge-tree` 與 remote 身分。

`merge-tree` 的 rc 由呼叫端印，⛔ 不擋、⛔ 不重新定義其語意。
remote 事實只供 resolved repository 取源（gh/target.py），⛔ 不進 facts 輸出——
worktree 路徑因機器而異，印出來會讓「同一 SHA 的本機事實逐字相同」不成立。
"""
from __future__ import annotations

from dataclasses import dataclass
import subprocess


class LocalGitUnavailable(RuntimeError):
    """本機 repo 不可用、git 未能執行或 merge-tree 自身失敗；呼叫端印，⛔ 不當成無衝突。"""


@dataclass(frozen=True)
class RemoteFact:
    name: str
    fetch_url: str
    is_upstream_of_current: bool


def merge_tree(base, head, *, root='.', runner=None):
    """回傳 rc：0＝可合併、1＝有衝突（git merge-tree 的既有語意）。"""
    runner = subprocess.run if runner is None else runner
    args = ['git', '-C', str(root), 'merge-tree', '--write-tree', str(base), str(head)]
    try:
        result = runner(args, capture_output=True, text=True, check=False, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise LocalGitUnavailable(str(exc)) from exc
    if result.returncode not in (0, 1):
        raise LocalGitUnavailable((result.stderr or '').strip() or f'rc={result.returncode}')
    return result.returncode


def remote_facts(root, *, runner=None):
    """每個 remote 一筆；root 不在 git 工作樹內＝None（事實缺席，⛔ 不是錯誤）；
    git 不可執行＝LocalGitUnavailable。"""
    runner = subprocess.run if runner is None else runner

    def out(*args):
        try:
            result = runner(('git', '-C', str(root), *args), capture_output=True, text=True,
                            check=False, timeout=60)
        except (OSError, subprocess.SubprocessError) as exc:
            raise LocalGitUnavailable(str(exc)) from exc
        return result.stdout.strip() if result.returncode == 0 else None

    if out('rev-parse', '--git-dir') is None:
        return None
    ref = out('symbolic-ref', '--quiet', 'HEAD')
    upstream = out('for-each-ref', '--format=%(upstream:remotename)', ref) if ref else None
    return tuple(RemoteFact(name, out('remote', 'get-url', name) or '', name == upstream)
                 for name in (out('remote') or '').split())
