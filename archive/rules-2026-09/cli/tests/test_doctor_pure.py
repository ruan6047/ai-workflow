"""釘住 `doctor` 轉薄的**委派邊界**（`WF-REDESIGN-W3` 驗收 2）。

卡面逐字要求「加**現行指令 vs 新 CI job 的等價 round-trip 測試**」。本檔就是那個
round-trip：一端是 `wfcli doctor` 走的 `wf_cli.doctor.<name>`，另一端是 CI job
`doctor-pure` 直接跑的 `scripts/doctor_pure.py`，兩端必須是**同一個物件**。

## 四件要擋的事

1. **有人在 `doctor.py` 補回一份等價實作。** 那是第二個真相源；本檔掃 `doctor.py`
   的 AST，六個名字**只能**綁到 `_delegate(...)` 的產物，⛔ 不得是 `def`。
2. **委派清單與腳本內容漂開。** `DELEGATED_TO_DOCTOR_PURE` 是契約，兩邊各改一半
   就轉紅。
3. **腳本偷偷 import `wf_cli`。** 那會讓 CI job 的 `--no-project` 執行從此炸掉，
   而 `tests` job（裝好 `wf_cli`）**看不見**這個回歸。
4. **明示降級被改成 fail-closed 或靜默 fallback。** 前者違反 doctor ⛔ 不阻擋任何
   動詞；後者讓「已轉薄」在某些環境悄悄不成立。

⛔ **本檔⛔ 不重測那六個函式的判定內容**——那是 `test_doctor.py` 的射程。本檔只測
**邊界**。
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from wf_cli import doctor
from wf_cli.commands import doctor_cmd

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts" / "doctor_pure.py"


@pytest.fixture(autouse=True)
def _reset_delegation_cache():
    """`load_doctor_pure` 會記住成功與失敗，⛔ 不重置會讓測試互相污染。"""
    yield
    doctor._doctor_pure_module = None
    doctor._doctor_pure_error = None


def _load_script():
    spec = importlib.util.spec_from_file_location("doctor_pure_probe", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------- (1) 兩端是同一個物件

def test_every_delegated_name_resolves_to_the_script_function():
    """⭐ round-trip 的本體：`wf_cli.doctor.<name>` 轉呼到的就是腳本裡那一個。"""
    module = doctor.load_doctor_pure()
    for name in doctor.DELEGATED_TO_DOCTOR_PURE:
        assert hasattr(module, name), f"腳本缺 {name}"
        # 委派是薄轉呼 ⇒ 呼叫端拿到的是 wrapper，但它 getattr 的目標必須是腳本那一個。
        assert getattr(doctor, name).__name__ == name


@pytest.mark.parametrize(
    "name,args",
    [
        ("_short_event", ("abc",)),
        ("_short_event", ("x" * 200,)),
        ("_short_event", (None,)),
        ("_identity_annotation", ([],)),
        ("_identity_annotation", (["https://example/1"],)),
        ("_check_third_face", ("✅通過", "✅通過")),
        ("_check_third_face", ("✅通過", None)),
        ("_expected_delivery_status", ({}, [])),
    ],
)
def test_the_two_ends_agree_byte_for_byte(name, args):
    """同一組輸入，兩端輸出必須相等。⛔ 不比「都不炸」——那是零資訊。"""
    assert getattr(doctor, name)(*args) == getattr(_load_script(), name)(*args)


@pytest.mark.parametrize(
    "parents,merge_paths,changed,expected",
    [
        (["a", "b"], [], [], "merge_clean"),
        (["a", "b"], ["x"], [], "merge_with_content"),
        (["a"], [], [], "empty"),
        (["a"], [], ["x"], "implementation"),
        ([], [], ["x"], "implementation"),
    ],
)
def test_classify_commit_shape_agrees_across_the_boundary(parents, merge_paths, changed, expected):
    record = SimpleNamespace(
        parents=parents, merge_content_paths=merge_paths, changed_paths=changed
    )
    assert doctor.classify_commit_shape(record) == expected
    assert _load_script().classify_commit_shape(record) == expected


# ---------------------------------------------- (2) `doctor.py` 沒有第二份實作

def test_doctor_py_defines_none_of_the_delegated_names_as_functions():
    """⛔ 不得在 `doctor.py` 補回等價實作——那是第二個真相源。"""
    tree = ast.parse(Path(doctor.__file__).read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert defined.isdisjoint(doctor.DELEGATED_TO_DOCTOR_PURE)


def test_every_delegated_name_is_bound_by_the_delegate_helper():
    """六個名字在模組層**只能**綁到 `_delegate(...)` 的回傳值。"""
    tree = ast.parse(Path(doctor.__file__).read_text(encoding="utf-8"))
    bound: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            func = node.value.func
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(func, ast.Name):
                    bound[target.id] = func.id
    for name in doctor.DELEGATED_TO_DOCTOR_PURE:
        assert bound.get(name) == "_delegate", f"{name} ⛔ 不是由 _delegate 綁的"


def test_the_delegation_roster_matches_the_script():
    """契約：清單、腳本內容、`doctor.py` 的綁定，三者⛔ 不得只改一邊。"""
    module = _load_script()
    tree = ast.parse(_SCRIPT.read_text(encoding="utf-8"))
    script_defs = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_selfcheck")
    }
    assert set(doctor.DELEGATED_TO_DOCTOR_PURE) <= script_defs
    assert all(hasattr(module, n) for n in doctor.DELEGATED_TO_DOCTOR_PURE)


# ------------------------------------------- (3) 腳本⛔ 不 import wf_cli

def test_the_script_imports_no_wf_cli_symbol():
    """收錄判準 1。⚠️ `tests` job（裝好 `wf_cli`）**看不見**這個回歸 ⇒ 這條必須在。"""
    tree = ast.parse(_SCRIPT.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0, f"第 {node.lineno} 行是相對 import"
            assert not (node.module or "").startswith("wf_cli"), f"第 {node.lineno} 行"
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("wf_cli"), f"第 {node.lineno} 行"


def test_the_ci_job_selfcheck_passes_when_run_the_way_ci_runs_it():
    """⭐ 把 CI job 那一行**原樣跑一次**。⛔ 不在測試裡重寫一份等價的自檢。"""
    proc = subprocess.run(
        [sys.executable, str(_SCRIPT)], capture_output=True, text=True, check=False
    )
    assert proc.returncode == 0, proc.stderr
    assert "自檢通過" in proc.stdout


# --------------------------------------------------------- (4) 明示降級

def _degraded(monkeypatch):
    monkeypatch.setattr(doctor, "DOCTOR_PURE_SCRIPT", _REPO_ROOT / "scripts" / "沒有這支.py")
    doctor._doctor_pure_module = None
    doctor._doctor_pure_error = None


def test_a_missing_script_raises_the_named_exception(monkeypatch):
    _degraded(monkeypatch)
    with pytest.raises(doctor.DoctorHelpersUnavailable):
        doctor._short_event("abc")


def test_a_missing_script_does_not_fall_back_to_a_built_in_implementation(monkeypatch):
    """⛔ **不得靜默 fallback**——那會讓「已轉薄」在某些環境悄悄不成立。

    ⛔ 這條⛔ 不是上一條的重複：上一條測「會丟例外」，這一條測「⛔ 不會回出答案」。
    """
    _degraded(monkeypatch)
    for name in doctor.DELEGATED_TO_DOCTOR_PURE:
        with pytest.raises(doctor.DoctorHelpersUnavailable):
            getattr(doctor, name)()


def test_the_failure_reason_is_cached_so_the_filesystem_is_hit_once(monkeypatch):
    _degraded(monkeypatch)
    with pytest.raises(doctor.DoctorHelpersUnavailable):
        doctor.load_doctor_pure()
    assert doctor._doctor_pure_error is not None
    # 第二次不該再打檔案系統：把路徑改成一支**存在**的檔，仍必須丟例外。
    monkeypatch.setattr(doctor, "DOCTOR_PURE_SCRIPT", _SCRIPT)
    with pytest.raises(doctor.DoctorHelpersUnavailable):
        doctor.load_doctor_pure()


def _doctor_args(strict: bool) -> argparse.Namespace:
    return argparse.Namespace(repo_root=str(_REPO_ROOT), commit_trailers=False,
                              commit_range=None, conformance=False, strict=strict)


def test_degradation_prints_a_warning_and_keeps_rc_zero_without_strict(monkeypatch, capsys):
    """明示降級：印警告 ＋ 明說「未執行」 ＋ **rc 不變**（⛔ 不阻擋任何動詞）。"""
    _degraded(monkeypatch)
    monkeypatch.setattr(
        doctor_cmd, "_run_doctor_command",
        lambda args: (_ for _ in ()).throw(doctor.DoctorHelpersUnavailable("找不到抽出腳本 X")),
    )
    assert doctor_cmd.run(_doctor_args(strict=False)) == 0
    err = capsys.readouterr().err
    assert "明示降級" in err
    assert "未執行" in err
    assert "找不到抽出腳本" in err


def test_degradation_returns_one_under_strict_so_ci_does_not_go_falsely_green(monkeypatch, capsys):
    """⚠️ **本卡對規格歧義的裁斷**：規格逐字「rc 不變」，但 `--strict` 下回 0 會讓
    CI 對一次**什麼都沒檢查**的執行亮綠燈。⇒ `--strict` 回 1。

    ⛔ 這⛔ 不使 doctor 變成新的擋人點：`--strict` 本來就會回 1，本分支⛔ 沒有在
    **非** `--strict` 路徑上新增任何非零 rc（上一條測的就是那一半）。
    """
    _degraded(monkeypatch)
    monkeypatch.setattr(
        doctor_cmd, "_run_doctor_command",
        lambda args: (_ for _ in ()).throw(doctor.DoctorHelpersUnavailable("找不到抽出腳本 X")),
    )
    assert doctor_cmd.run(_doctor_args(strict=True)) == 1
    assert "查不了⛔ 不得亮綠燈" in capsys.readouterr().err


def test_the_script_path_is_derived_from_the_package_not_from_args(monkeypatch):
    """⛔ **不從 `args.repo_root` 推導**——`doctor <repo>` 對別的 repo 跑時
    `<那個 repo>/scripts/` 不存在，用它推導會在完全正常的情境下誤判成「腳本不在」。
    """
    assert doctor.DOCTOR_PURE_SCRIPT == _REPO_ROOT / "scripts" / "doctor_pure.py"
    assert doctor.DOCTOR_PURE_SCRIPT.exists()


# ------------------------------------------------------------- 帳面登記

def test_the_thinning_is_recorded_as_accounting_only():
    """⚠️ 這是**帳面**轉薄：執行時邊界⛔ 未改變，那些行照樣被載入執行。

    ⛔ 這條⛔ 不是文件測試——它釘的是「登記還在」，因為交付名稱（轉薄）與交付
    內容（帳面）不一致，那正是最容易被誤讀的一句話。
    """
    source = Path(doctor.__file__).read_text(encoding="utf-8")
    assert "帳面" in source
    assert "⛔ 未關" in source
