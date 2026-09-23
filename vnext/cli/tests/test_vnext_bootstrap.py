"""W1.1 bootstrap 測試：只證明 vNext 的 CI 管道與空骨架可運作。

⛔ 不預建後續功能：本檔不 import wfx、不驗任何規則內容、不做散文判讀。
被測物＝(1) vnext.yml 釘的 Python 版本實際生效、(2) C1 列出的骨架目錄存在。
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

SKELETON_DIRS = (
    "vnext/cli/src/wfx/rules/core",
    "vnext/cli/src/wfx/rules/stages",
    "vnext/cli/src/wfx/rules/roles",
    "vnext/.wf",
    "vnext/cli/src/wfx/core",
    "vnext/cli/src/wfx/gh",
    "vnext/cli/src/wfx/verbs",
    "vnext/cli/tests",
)


def test_runs_on_pinned_python():
    assert sys.version_info[:2] == (3, 14)


def test_skeleton_directories_exist():
    missing = [d for d in SKELETON_DIRS if not (REPO_ROOT / d).is_dir()]
    assert missing == []


def test_repo_root_resolution_is_correct():
    assert (REPO_ROOT / "vnext").is_dir()
    assert (REPO_ROOT / ".github" / "workflows" / "vnext.yml").is_file()
