"""釘住動詞註冊清單的形狀（DEV-CLI-VERB-REGISTRY1）。

本檔要擋的三件事：

1. **改成動態探索**（``pkgutil``／``iter_modules``／comprehension 生出清單）——
   註冊集合必須是顯式、封閉、可稽核的字面 tuple，順序即 ``--help`` 順序。
2. **漏註冊**——磁碟上有 ``*_cmd.py`` 卻不在清單裡（或清單裡的名字打錯字）。
3. **改回 eager import 模組物件**——那會讓 ``wf_cli.commands`` 在被觸及時就 import
   全部動詞模組，與 ``cleanup``／``doctor`` 反向 import ``commands.assign_cmd``
   形成循環。該環在 ``cli.py`` 當入口時**不會**觸發，整套既有測試也照不出來，
   只有「先 import ``wf_cli.cleanup``」這種冷啟動路徑會炸。所以這裡用子行程逐一
   冷啟動 import 每個模組來釘。
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from pathlib import Path

import pytest

import wf_cli
from wf_cli import cli as cli_mod
from wf_cli.commands import COMMAND_MODULES

PACKAGE_ROOT = Path(wf_cli.__file__).resolve().parent
COMMANDS_DIR = PACKAGE_ROOT / "commands"
REGISTRY_SOURCE = COMMANDS_DIR / "__init__.py"

# 錯誤處理契約的凍結基線：只有在**刻意**改 cli.py 的錯誤處理時才該動這份清單。
# 新增動詞不會碰它，所以它不是新動詞卡的衝突點。
#
# ⚠️ 2026-08-27 刻意變更（WF-MARKER-WRITE-BOUNDARY1，查核 R2-03）：新增
# ``wf_cli.card.MarkerWriteBoundaryError``。⛔ 它的父類 ``card.AmendError`` **刻意不收**
# ——``tests/test_amend.py`` 有一條深層性質靠「model 層是獨立防線」成立，收父類會吞掉它。
EXPECTED_KNOWN_ERRORS = (
    "wf_cli.config.ConfigError",
    "wf_cli.gh.GhError",
    "wf_cli.git_ops.GitError",
    "wf_cli.card.MarkerWriteBoundaryError",
    "wf_cli.project.ProjectError",
    "wf_cli.resources.ResourceDeclarationError",
    "wf_cli.review.ReviewParseError",
    "wf_cli.validation.ValidationError",
)


def _registry_assignment() -> ast.AST:
    tree = ast.parse(REGISTRY_SOURCE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", None) == "COMMAND_MODULES":
            assert node.value is not None
            return node.value
        if isinstance(node, ast.Assign) and any(
            getattr(t, "id", None) == "COMMAND_MODULES" for t in node.targets
        ):
            return node.value
    raise AssertionError("commands/__init__.py 找不到 COMMAND_MODULES 的模組層級指派")


def _subparsers_action(parser: argparse.ArgumentParser) -> argparse._SubParsersAction:
    return next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))


def _verbs_of(module_name: str) -> list[str]:
    """單獨把一個動詞模組註冊進拋棄式 parser，回傳它註冊了哪些動詞。"""
    from importlib import import_module

    module = import_module(f"wf_cli.commands.{module_name}")
    parser = argparse.ArgumentParser(prog="probe")
    sub = parser.add_subparsers(dest="command")
    module.add_parser(sub)
    return list(sub._name_parser_map)


def _instantiate(exc_type: type[BaseException]) -> BaseException:
    """用最少的 dummy 位置參數把例外實例化（GhError 之類需要 3 個參數）。"""
    for n in range(1, 6):
        try:
            return exc_type(*(["synthetic"] * n))
        except TypeError:
            continue
    raise AssertionError(f"無法實例化 {exc_type!r}")


# --------------------------------------------------------------------------
# 1. 清單是顯式的
# --------------------------------------------------------------------------


def test_registry_is_a_literal_tuple_of_string_constants() -> None:
    """COMMAND_MODULES 必須是字面 tuple。改成 ``tuple(...)``／comprehension／
    ``pkgutil`` 探索，這裡就會轉紅。"""
    value = _registry_assignment()
    assert isinstance(value, ast.Tuple), (
        f"COMMAND_MODULES 必須是字面 tuple，實際是 {type(value).__name__}；"
        "動態產生的註冊集合是隱式且開放的，違反本 repo 的封閉鍵集合紀律"
    )
    for element in value.elts:
        assert isinstance(element, ast.Constant) and isinstance(element.value, str), (
            f"COMMAND_MODULES 的元素必須是字串字面值，實際出現 {ast.dump(element)[:80]}"
        )
    literal = tuple(e.value for e in value.elts)
    assert literal == COMMAND_MODULES, (
        "原始碼字面值與 runtime 值不一致——代表清單在 import 期被改寫過"
    )


def test_registry_module_does_no_dynamic_import() -> None:
    """註冊清單所在的模組不得引入 import 機械或探索工具。

    這同時也是循環 import 的防線：本模組不 import 任何子模組，環就不存在。
    """
    tree = ast.parse(REGISTRY_SOURCE.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or ".")
    assert imported == ["__future__"], (
        f"commands/__init__.py 只該 import __future__，實際 import 了 {imported}"
    )
    forbidden = {"pkgutil", "importlib", "iter_modules", "walk_packages", "__import__"}
    used = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id in forbidden
    } | {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr in forbidden
    }
    assert not used, f"註冊清單不得使用動態探索：{sorted(used)}"


# --------------------------------------------------------------------------
# 2. 沒有漏註冊 / 沒有打錯字
# --------------------------------------------------------------------------


def test_registry_matches_command_modules_on_disk() -> None:
    """磁碟上的 ``*_cmd.py`` 與清單雙向相等：漏註冊或名字打錯都轉紅。"""
    on_disk = {p.stem for p in COMMANDS_DIR.glob("*_cmd.py")}
    registered = set(COMMAND_MODULES)
    assert on_disk - registered == set(), (
        f"有動詞模組沒被註冊（新增檔案後忘了 append 一行？）：{sorted(on_disk - registered)}"
    )
    assert registered - on_disk == set(), (
        f"清單裡有磁碟上不存在的模組名（打錯字？）：{sorted(registered - on_disk)}"
    )


def test_registry_has_no_duplicates() -> None:
    assert len(set(COMMAND_MODULES)) == len(COMMAND_MODULES)


def test_each_module_registers_at_least_one_verb() -> None:
    """一個模組**至少**註冊一個動詞。

    刻意不釘「剛好一個」：同一個模組註冊兩個同源動詞是既有的合法形狀
    （WF-22-CLI4／#9 的 ``checkpoint_cmd`` 同時註冊 ``checkpoint`` 與
    ``contract-baseline``）。help 順序仍可由清單推導——見
    ``test_help_order_equals_registry_order`` 的攤平比對。
    """
    for module_name in COMMAND_MODULES:
        assert _verbs_of(module_name), f"{module_name}.add_parser 沒有註冊任何動詞"


# --------------------------------------------------------------------------
# 3. help 順序＝清單順序；每個動詞派到自己模組的 run
# --------------------------------------------------------------------------


def test_help_order_equals_registry_order() -> None:
    """``--help`` 的動詞順序＝清單順序（多動詞模組則攤平後保序）。"""
    parser = cli_mod.build_parser()
    sub = _subparsers_action(parser)
    expected = [verb for name in COMMAND_MODULES for verb in _verbs_of(name)]
    assert [c.dest for c in sub._choices_actions] == expected
    assert list(sub._name_parser_map) == expected


def test_every_verb_dispatches_into_its_own_module() -> None:
    parser = cli_mod.build_parser()
    sub = _subparsers_action(parser)
    for module_name in COMMAND_MODULES:
        for verb in _verbs_of(module_name):
            func = sub._name_parser_map[verb].get_default("func")
            assert func is not None, f"{verb} 沒有 set_defaults(func=...)"
            assert func.__module__ == f"wf_cli.commands.{module_name}"


def test_top_level_help_lists_every_registered_verb() -> None:
    text = cli_mod.build_parser().format_help()
    for module_name in COMMAND_MODULES:
        for verb in _verbs_of(module_name):
            assert verb in text


# --------------------------------------------------------------------------
# 4. 錯誤處理契約
# --------------------------------------------------------------------------


def test_known_errors_frozen_baseline() -> None:
    actual = tuple(f"{e.__module__}.{e.__qualname__}" for e in cli_mod.KNOWN_ERRORS)
    assert actual == EXPECTED_KNOWN_ERRORS


@pytest.mark.parametrize("exc_type", cli_mod.KNOWN_ERRORS, ids=lambda e: e.__name__)
def test_known_error_exits_2(exc_type, capsys, monkeypatch) -> None:
    monkeypatch.setattr(cli_mod, "build_parser", _parser_raising(_instantiate(exc_type)))
    assert cli_mod.main([]) == 2
    assert "[wfcli] 錯誤：" in capsys.readouterr().err


def test_keyboard_interrupt_exits_130(monkeypatch) -> None:
    monkeypatch.setattr(cli_mod, "build_parser", _parser_raising(KeyboardInterrupt()))
    assert cli_mod.main([]) == 130


def test_unknown_error_propagates(monkeypatch) -> None:
    monkeypatch.setattr(cli_mod, "build_parser", _parser_raising(RuntimeError("boom")))
    with pytest.raises(RuntimeError):
        cli_mod.main([])


def test_success_returns_func_return_value(monkeypatch) -> None:
    parser = argparse.ArgumentParser(prog="probe")
    parser.set_defaults(func=lambda args: 7)
    monkeypatch.setattr(cli_mod, "build_parser", lambda: parser)
    assert cli_mod.main([]) == 7


def _parser_raising(exc: BaseException):
    def factory() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="probe")

        def boom(args):
            raise exc

        parser.set_defaults(func=boom)
        return parser

    return factory


# --------------------------------------------------------------------------
# 5. 循環 import 防線（每個模組冷啟動可獨立 import）
# --------------------------------------------------------------------------


def _module_names() -> list[str]:
    names = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        rel = path.relative_to(PACKAGE_ROOT).with_suffix("")
        parts = [p for p in rel.parts if p != "__init__"]
        names.append(".".join(["wf_cli", *parts]))
    return names


@pytest.mark.parametrize("module_name", _module_names())
def test_module_imports_standalone_in_fresh_interpreter(module_name: str) -> None:
    """每個 wf_cli 模組都必須能當**第一個** import 的模組。

    在同一個直譯器裡 import 會被 sys.modules 快取掩蓋順序問題，所以開子行程。
    若 commands/__init__.py 改回 eager import 模組物件，
    ``wf_cli.cleanup`` 與 ``wf_cli.doctor`` 這兩項會轉紅。
    """
    proc = subprocess.run(
        [sys.executable, "-c", f"import {module_name}"],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(PACKAGE_ROOT.parent.parent),
    )
    assert proc.returncode == 0, (
        f"冷啟動 import {module_name} 失敗（循環 import？）：\n{proc.stderr[-800:]}"
    )
