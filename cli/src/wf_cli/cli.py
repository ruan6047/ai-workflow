"""wfcli 進入點：受控的 control-plane 子指令。"""

from __future__ import annotations

import argparse
import sys
from importlib import import_module

from .commands import COMMAND_MODULES
from .config import ConfigError
from .gh import GhError
from .git_ops import GitError
from .project import ProjectError
from .resources import ResourceDeclarationError
from .review import ReviewParseError
from .validation import ValidationError

KNOWN_ERRORS = (
    ConfigError,
    GhError,
    GitError,
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
