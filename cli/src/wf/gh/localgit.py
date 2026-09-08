"""消費 core/verbs.md §1 brief 列的「`merge-tree` 衝突」與 core/dispatch.md 基線列。

本機 git 的唯一入口，只包 `git merge-tree --write-tree`：不連網、不寫本機 repo、
不解析輸出內容（第零條）。rc 由呼叫端印，⛔ 不擋（`core/verbs.md` §2「其餘一律印」）。
"""
import subprocess


class LocalGitUnavailable(RuntimeError):
    """本機 repo 不可用、git 未能執行或 merge-tree 自身失敗；呼叫端印，不當成無衝突。"""


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
