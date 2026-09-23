"""本機 git 唯讀 revision 事實：`rev-parse`／`log`／`diff --stat`（wfx/rules/core/boundaries.md「CLI 邊界」）。

不連網、不寫本機 repo、不改工作樹、⛔ 不解析輸出語意。
取不到就 raise，交呼叫端印一行帶原因：⛔ 不回空清單冒充「沒有改動」。
"""
from __future__ import annotations

import subprocess

LOG_FORMAT = '--pretty=format:%H %s'


class LocalRevUnavailable(RuntimeError):
    """root 非 git 工作樹、git 不可執行，或唯讀子指令自身非零；原因逐字取自該次 stderr。"""


def _run(root, args, runner):
    runner = subprocess.run if runner is None else runner
    try:
        return runner(('git', '-C', str(root), *args), capture_output=True, text=True,
                      check=False, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise LocalRevUnavailable(str(exc)) from exc


def _lines(result, what):
    if result.returncode:
        raise LocalRevUnavailable((result.stderr or '').strip() or f'{what} rc={result.returncode}')
    return (result.stdout or '').splitlines()


def rev_parse(revision, *, root='.', runner=None):
    """解到 40 碼 commit SHA。本機沒有這個 revision＝None（事實缺席，⛔ 不是錯誤）；
    root 非工作樹或 git 不可執行＝LocalRevUnavailable（stderr 逐字）。"""
    result = _run(root, ('rev-parse', '--verify', '--quiet', f'{revision}^{{commit}}'), runner)
    if result.returncode == 0:
        return (result.stdout or '').strip() or None
    reason = (result.stderr or '').strip()
    if reason:
        raise LocalRevUnavailable(reason)
    return None


def log_commits(base, head, *, root='.', runner=None):
    """`git log --no-color --pretty=format:%H %s <base>..<head>` 每列一筆（兩點＝只列 head 側新增）。
    真的沒有新 commit＝空 list；失敗一律 raise，⛔ 不與空 list 混用。"""
    return _lines(_run(root, ('log', '--no-color', LOG_FORMAT, f'{base}..{head}'), runner), 'git log')


def diff_stat(base, head, *, root='.', runner=None):
    """`git diff --stat --no-color <base>...<head>` 每列一筆（三點＝左端取 merge-base）。
    ⛔ 不用兩點：兩點會把只在 base 上變動的檔算進改動面。"""
    return _lines(_run(root, ('diff', '--stat', '--no-color', f'{base}...{head}'), runner), 'git diff')
