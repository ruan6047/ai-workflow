"""入口。動詞集合固定為三個（wfx/rules/core/boundaries.md「CLI 邊界」）；本檔只做分派。

public shape：`wfx [--project-root <p>] <verb> [動詞參數…]`。全域旗標只認動詞之前，由前綴迴圈消耗、
⛔ 不傳給動詞的 parse_args。本檔⛔ 不判內容、⛔ 不代動詞印、⛔ 不呼叫 AI。
三個動詞（`brief`／`facts`／`write`）已全部登記。rc 慣例：**用法錯 rc=2、typed 錯 rc=1**（兩類可區分）。
"""
import os
from pathlib import Path
import sys

from wfx.core.context import ConfigError, load_config
from wfx.core.errors import WfxError
from wfx.gh.client import GhError
from wfx.gh.localgit import LocalGitUnavailable
from wfx.gh.localrev import LocalRevUnavailable
from wfx.gh.target import TargetError
from wfx.verbs import brief, facts, write

DISPATCH = {'brief': brief, 'facts': facts, 'write': write}
GLOBAL_FLAGS = ('--project-root',)
USAGE = f'用法：wfx [--project-root <p>] <{"｜".join(DISPATCH)}> [動詞參數…]'


def global_flags(argv):
    """前綴迴圈：只消耗動詞之前的全域旗標（`--x v` 或 `--x=v`，重複以後者為準）。
    形狀不對、或全域旗標出現在動詞之後＝None（呼叫端印用法、rc=2）。"""
    flags, rest = {}, list(argv)
    while rest and rest[0].startswith('--'):
        name, has_value, value = rest[0].partition('=')
        if name not in GLOBAL_FLAGS or (not has_value and len(rest) < 2):
            return None
        flags[name] = value if has_value else rest[1]
        rest = rest[1 if has_value else 2:]
    if any(token.partition('=')[0] in GLOBAL_FLAGS for token in rest[1:]):
        return None
    return flags, rest


def main(argv=None, *, env=None, **injected):
    """`injected`＝動詞層的內部注入點（`client`／`runner`／`task_source`），測試專用、⛔ 非公開旗標。"""
    env = os.environ if env is None else env
    parsed = global_flags(sys.argv[1:] if argv is None else argv)
    if parsed is None:
        print(USAGE, file=sys.stderr)
        return 2
    flags, rest = parsed
    if not rest or rest[0] not in DISPATCH:
        print(USAGE, file=sys.stderr)
        return 2
    project_root = Path(flags.get('--project-root', '.')).resolve()
    try:
        config = load_config(project_root)
        return DISPATCH[rest[0]].run(rest[1:], project_root=project_root, config=config,
                                     env=env, **injected)
    except (ConfigError, WfxError, GhError, TargetError,
            LocalGitUnavailable, LocalRevUnavailable) as exc:
        print(f'{type(exc).__name__}: {exc}', file=sys.stderr)
        return 1
