"""V1 差分預言：把既有測試套件整包變成 ``ensure_fields`` 的正確性斷言。

**用法（opt-in，⛔ 預設不載入）**：

    cd cli && uv run pytest -q -p tests.ensure_fields_oracle

做的事：把每一個模組裡 ``ensure_fields`` 這個名字綁到一層包裝上。包裝在原函式回傳
R 之後，**立刻**重讀一次 ``list_fields`` 得 F，並以順序敏感的逐欄位比對斷言
``R == F``。⇒ 套件裡每一次 ``ensure_fields`` 呼叫都變成一個斷言，且**兩條路徑都
會被覆蓋**——`FakeGhRunner` 的 project 預設是空的，所以「有建立」那條是預設行為，
不需要刻意造欄位缺失。

**為什麼是 opt-in 而不是常駐**：它讓每次 ``ensure_fields`` 多發一次欄位查詢，會直接
打壞 ``test_project_mocked.py`` 裡釘呼叫次數的那幾條（V3）。常駐＝那些斷言必須放寬，
而放寬它們等於拿掉「修法靜默回退」的唯一守衛。⇒ 兩者刻意分開：次數守衛常駐、
差分預言按需跑。

⛔ **不得由本模組推出「ensure_fields 已被持續驗證」**：它只在有人加 ``-p`` 時才跑，
CI 沒有跑它（見 ``.github/workflows/ci.yml`` 的 pytest 步驟）。它是**取證工具**，
不是守衛。
"""

from __future__ import annotations

import sys
from typing import Any

from wf_cli import project
from wf_cli.project import FieldMeta

#: 原函式。⚠️ 一定要在安裝包裝**之前**抓，且之後一律呼叫這個綁定——
#: 包裝會把 ``project.ensure_fields`` 自己也換掉，透過模組屬性叫就是無窮遞迴。
_ORIG = project.ensure_fields

#: 包裝正在跑自己的驗證讀取。呼叫端（例如釘次數的測試代理）用 ``oracle_reentrant()``
#: 把這段期間的呼叫排除，才不會把「預言自己發的查詢」算進被測程式的帳上。
_REENTRANT = False


def oracle_reentrant() -> bool:
    """差分預言此刻正在做它自己的驗證讀取嗎？

    未載入本 plugin 時模組仍可 import（``tests`` 是套件），此函式恆為 False。
    """
    return _REENTRANT


class _Stats:
    def __init__(self) -> None:
        self.calls = 0
        self.with_creation = 0
        self.without_creation = 0
        self.fields_created = 0
        self.mismatches: list[str] = []
        #: 原函式或驗證讀取自己拋錯的次數。⭐ 這些**不是** PASS——是「這一次沒被
        #: 驗到」。分開記，⛔ 不併進成功數。
        self.unverifiable = 0
        self.patched_modules: list[str] = []


STATS = _Stats()


def _pairs(fields: dict[str, FieldMeta]) -> list[tuple[str, str, str, str, list[tuple[str, str]]]]:
    """攤平成順序敏感、可逐項比對的元組序列。

    ⛔ **不能只用 dict 的 ``==``**：dict 相等不看插入順序，而驗收 A2 要的是逐位元。
    索引用欄位名（Project 內欄位名唯一），且把名字**同時**放進值裡——鍵與值不一致
    （例如 off-by-one 把 B 的 meta 掛到 A 名下）才會現形。
    """
    return [
        (name, meta.id, meta.name, meta.type, list(meta.options.items()))
        for name, meta in fields.items()
    ]


def field_diff(returned: dict[str, FieldMeta], fresh: dict[str, FieldMeta]) -> list[str]:
    """兩份欄位表的逐項差異；空 list 代表逐位元相同。

    ⭐ 刻意做成公開名字並由 ``test_project_mocked.py`` 的常駐測試共用：
    「逐位元」在本卡只有這一個定義，兩處各寫一份遲早會分歧。
    """
    a, b = _pairs(returned), _pairs(fresh)
    if a == b:
        return []
    problems: list[str] = []
    if [x[0] for x in a] != [x[0] for x in b]:
        problems.append(f"欄位名序列不同：回傳 {[x[0] for x in a]} vs 重讀 {[x[0] for x in b]}")
    for x, y in zip(a, b):
        if x != y:
            problems.append(f"欄位 {x[0]!r}：回傳 {x[1:]} vs 重讀 {y[1:]}")
    if len(a) != len(b):
        problems.append(f"欄位數不同：回傳 {len(a)} vs 重讀 {len(b)}")
    return problems


def _count_field_creates(runner: Any) -> tuple[Any, list[list[str]]]:
    """暫時把 runner.execute 換成會記帳的版本，回傳 (還原用的原值, 記錄)。"""
    created: list[list[str]] = []
    original = runner.execute

    def counting(args, input=None):  # noqa: A002 - 對齊被包裝方法的參數名
        argv = list(args)
        if argv[:2] == ["project", "field-create"]:
            created.append(argv)
        return original(args, input)

    runner.execute = counting
    return original, created


def _restore_execute(runner: Any, original: Any) -> None:
    try:
        del runner.execute  # 實例屬性拿掉，露出類別上的方法
    except AttributeError:
        runner.execute = original


def _wrapper(runner, owner, number, *args, **kwargs):
    global _REENTRANT
    STATS.calls += 1
    try:
        original_execute, created = _count_field_creates(runner)
    except Exception:  # pragma: no cover - runner 不允許設屬性時退回不記帳
        original_execute, created = None, []
    try:
        result = _ORIG(runner, owner, number, *args, **kwargs)
    except Exception:
        STATS.unverifiable += 1
        raise
    finally:
        if original_execute is not None:
            _restore_execute(runner, original_execute)

    if created:
        STATS.with_creation += 1
        STATS.fields_created += len(created)
    else:
        STATS.without_creation += 1

    _REENTRANT = True
    try:
        fresh = project.list_fields(runner, owner, number)
    except Exception as exc:  # 驗證讀取本身失敗 ⇒ 這一次判不了，⛔ 不算通過
        STATS.unverifiable += 1
        print(f"[oracle] 驗證讀取失敗（判不了，非 PASS）：{exc!r}", file=sys.stderr)
        return result
    finally:
        _REENTRANT = False

    problems = field_diff(result, fresh)
    if problems:
        path = "有建立" if created else "零建立"
        STATS.mismatches.append(f"[{path}] " + "；".join(problems))
        raise AssertionError(
            f"差分預言失敗（{path}路徑）：ensure_fields 的回傳與立刻重讀不一致\n  "
            + "\n  ".join(problems)
        )
    return result


def _install() -> None:
    for name, mod in list(sys.modules.items()):
        if mod is None:
            continue
        try:
            current = getattr(mod, "ensure_fields", None)
        except Exception:  # pragma: no cover - 有些模組的 __getattr__ 會炸
            continue
        if current is _ORIG:
            setattr(mod, "ensure_fields", _wrapper)
            STATS.patched_modules.append(name)


def pytest_collection_finish(session):
    """收集完成後才安裝：測試模組是在收集期 import 的，
    ``from wf_cli.project import ensure_fields`` 產生的綁定那時才存在。"""
    _install()


def pytest_runtest_setup(item):
    """每個測試前補掃一次：有些模組是在測試函式體內才 import 的
    （例：``test_card_brief`` 內的 ``import wf_cli.commands.amend_cmd``）。"""
    _install()


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    w = terminalreporter.write_line
    w("")
    w("=== V1 差分預言統計 ===")
    w(f"ensure_fields 觸發次數      : {STATS.calls}")
    w(f"  其中「有建立」路徑        : {STATS.with_creation}")
    w(f"  其中「零建立」路徑        : {STATS.without_creation}")
    w(f"  判不了（拋錯，非 PASS）   : {STATS.unverifiable}")
    w(f"共建立欄位數                : {STATS.fields_created}")
    w(f"被掛上包裝的模組數          : {len(set(STATS.patched_modules))}")
    w(f"比對不一致次數              : {len(STATS.mismatches)}")
    for m in STATS.mismatches[:20]:
        w(f"  - {m}")
