"""入口。動詞集合固定為七個（core/verbs.md §1）；本檔只做分派，各動詞住 verbs/<name>.py。

消費 core/verbs.md §1 七列／§2、ADOPTION.md §2（`.wf/modules.json` 位置）。
本檔只定位 repo、建 client、載 catalog、確認設定可讀，再把其餘 argv 交給該動詞的 `run`；
⛔ 不判內容、⛔ 不代動詞印、⛔ 不寫遠端（設定不合法時連 `wf:reject` 都不貼）。
repo 取源＝`GH_REPO`，其次本機 `.git/config` 的 origin URL：`gh/` 是唯一有網路的層，
`verbs/` ⛔ 不得 import subprocess（cli/tests/test_gh_scope.py），故 ⛔ 不跑 `git remote` 子指令。
"""
import os
from pathlib import Path
import re
import sys

from wf.compose.blocks import load_blocks
from wf.compose.project_config import ProjectConfigError, load_project_config
from wf.gh.client import GhClient
from wf.verbs import brief, edit, move, notes, review, snapshot
from wf.verbs import open as open_verb

DISPATCH = {'open': open_verb, 'move': move, 'edit': edit, 'notes': notes,
            'brief': brief, 'review': review, 'snapshot': snapshot}
VERBS = tuple(DISPATCH)
ORIGIN = re.compile(r'^\[remote "origin"\][ \t]*$(.*?)(?=^\[|\Z)', re.M | re.S)
URL = re.compile(r'^[ \t]*url[ \t]*=[ \t]*(.+?)[ \t]*$', re.M)
SLUG = re.compile(r'[/:]([^/:]+/[^/:]+?)(?:\.git)?/?$')


def git_dir(root):
    """`.git` 目錄；分離 worktree／submodule 的 `.git` 是指向真 gitdir 的檔。"""
    path = Path(root) / '.git'
    if not path.is_file():
        return path
    target = Path(path.read_text(encoding='utf-8').partition('gitdir:')[2].strip())
    common = target / 'commondir'
    return (target / common.read_text(encoding='utf-8').strip()) if common.is_file() else target


def repo_slug(root, *, env=None):
    """`owner/name`：`GH_REPO` 優先，其次 `.git/config` 的 origin URL；取不到＝None。"""
    env = os.environ if env is None else env
    if env.get('GH_REPO'):
        return env['GH_REPO']
    try:
        text = (git_dir(root) / 'config').read_text(encoding='utf-8')
    except OSError:
        return None
    section = ORIGIN.search(text)
    url = URL.search(section[1]) if section else None
    match = SLUG.search(url[1]) if url else None
    return match[1] if match else None


def main(argv=None, *, client=None, root=None, env=None) -> int:
    """argv[0]＝動詞；client／env 供測試注入，缺省走真實 GhClient 與環境變數。"""
    argv = sys.argv[1:] if argv is None else list(argv)
    if not argv or argv[0] not in DISPATCH:
        print('wf <' + '|'.join(VERBS) + '> …', file=sys.stderr)
        return 2
    root = '.' if root is None else root
    try:
        load_project_config(root)
    except ProjectConfigError as exc:
        print(f'.wf/modules.json 不合法：{exc}', file=sys.stderr)
        return 1
    if client is None:
        slug = repo_slug(root, env=env)
        if slug is None:
            print('未能取得 repo：設 GH_REPO 或在有 origin 的 git repo 內執行', file=sys.stderr)
            return 1
        client = GhClient(slug)
    return DISPATCH[argv[0]].run(argv[1:], client=client, root=root, catalog=load_blocks(root))
