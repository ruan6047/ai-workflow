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

#: ⏸ **已登記的阻塞發現（WF-MARKER-WRITE-BOUNDARY1 R2，2026-08-27）**
#:
#: (a) 現在的行為：``card.MarkerWriteBoundaryError`` **不在**本清單內 ⇒
#:     ``assign``／``handoff``／``review``／``checkpoint`` 這四支（它們把使用者文字原樣
#:     交給 ``card.append_log_line``）在守衛拒收時，經 ``main`` 會以 traceback、rc=1
#:     收場。``open`` 不受影響——它在 ``commands/open_cmd.py`` 自己接住並回 rc=2。
#: (b) 為什麼還沒補：補法是把 ``MarkerWriteBoundaryError`` 加進本 tuple（一行），
#:     但 ``cli/tests/test_cli_registry.py`` 的 ``EXPECTED_KNOWN_ERRORS`` 是**凍結基線**
#:     （該檔逐字：「只有在刻意改 cli.py 的錯誤處理時才該動這份清單」）⇒ 同一次改動
#:     必須同時改那個檔，而它**不在本卡宣告資源**內。canonical §3.2／本卡 A10 逐字要求
#:     「發現須改未宣告的檔即停、寫阻塞發現、交需求方裁決」。
#: (c) ⛔ **不得由此推出「那四支沒有守衛」**——守衛在 ``card.append_log_line`` 內，
#:     值一樣寫不進去；缺的只是**訊息與退出碼的乾淨度**。⛔ 也不得繞道：讓
#:     ``MarkerWriteBoundaryError`` 去繼承某個已在清單上的型別，是把授權問題藏進
#:     繼承鏈，⛔ 明令不採。
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
