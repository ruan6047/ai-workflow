"""wfcli 進入點：受控的 control-plane 子指令。"""

from __future__ import annotations

import argparse
import sys
from importlib import import_module

from .card import MarkerWriteBoundaryError
from .commands import COMMAND_MODULES
from .config import ConfigError
from .gh import GhError
from .git_ops import GitError
from .project import ProjectError
from .resources import ResourceDeclarationError
from .review import ReviewParseError
from .validation import ValidationError

#: ⭐ **``MarkerWriteBoundaryError`` 是刻意收在這裡的**（WF-MARKER-WRITE-BOUNDARY1，
#: 2026-08-27 依查核 R2-03 ``rejection-not-clean-traceback-escapes``）：
#:
#: (a) 現在的行為：``assign``／``handoff``／``review``／``checkpoint`` 這四支把使用者文字
#:     原樣交給 ``card.append_log_line``；守衛拒收時經 ``main`` 收成 ``[wfcli] 錯誤：…``
#:     ＋ rc=2。``open`` 另有自己的 ``except``（``[open] 拒絕：…``），兩層並存不衝突。
#: (b) 為什麼非收不可：`templates/handoff-contract.md` §3.2 逐字「以 stack trace 收場的
#:     fail-closed 不算乾淨拒絕」。少了這一行，那四支會以 traceback、rc=1 收場。
#: (c) ⛔ **不得由此推出「本清單可以收任何 ``ValueError``」**：收的是這個**具名型別**。
#:     ``card.AmendError``（它的父類）刻意留在外面——``tests/test_amend.py`` 有一條深層
#:     性質靠「model 層是獨立防線」成立，收父類會把它吞掉。⛔ 也不得反向繞道：讓某個
#:     新例外去繼承已在清單上的型別以取得 rc=2，是把授權問題藏進繼承鏈。
#:
#: ⚠️ 本 tuple 有凍結基線 ``cli/tests/test_cli_registry.py::EXPECTED_KNOWN_ERRORS``，
#: 同一次改動必須連它一起改。
KNOWN_ERRORS = (
    ConfigError,
    GhError,
    GitError,
    MarkerWriteBoundaryError,
    ProjectError,
    ResourceDeclarationError,
    ReviewParseError,
    ValidationError,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wfcli",
        description=(
            "祕書 CLI 最小集（WF-22-CLI1）：GitHub Issues/Projects v2 狀態面的唯一寫入通道。"
            "不經本 CLI 的狀態寫入即違規（見 cli/README.md 紅線 1）。"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    # 動詞註冊集合是 commands/__init__.py 的顯式封閉 tuple（見該檔 docstring）。
    # 這裡只負責照該清單的**字面順序**迭代——順序即 --help 的動詞順序。
    for module_name in COMMAND_MODULES:
        import_module(f".commands.{module_name}", __package__).add_parser(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KNOWN_ERRORS as exc:
        print(f"[wfcli] 錯誤：{exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
