"""消費 core/verbs.md §1 brief 列的「`merge-tree` 衝突」與 core/dispatch.md 基線列。

本機 git 的唯一入口，只包 `git merge-tree --write-tree`：不連網、不寫本機 repo、
不解析輸出內容（第零條）。rc 由呼叫端印，⛔ 不擋（`core/verbs.md` §2「其餘一律印」）。
本機 Git 身分六類事實的值物件也住這裡（取源住 gh/target.py `local_git_facts`，本檔仍只包 merge-tree）：
top-level、git-dir、common-dir、HEAD SHA 與 current ref、remote 名稱與展開後的 fetch/push URL，⛔ 不折成單一 root。
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


def merge_tree(base, head, *, root='.', runner=None):
    """回傳 rc：0＝可合併、1＝有衝突（git merge-tree 的既有語意，⛔ 不重新定義）。"""
    runner = subprocess.run if runner is None else runner
    args = ['git', '-C', str(root), 'merge-tree', '--write-tree', str(base), str(head)]
    try:
        result = runner(args, capture_output=True, text=True, check=False, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise LocalGitUnavailable(str(exc)) from exc
    if result.returncode not in (0, 1):
        raise LocalGitUnavailable((result.stderr or '').strip() or f'rc={result.returncode}')
    return result.returncode
