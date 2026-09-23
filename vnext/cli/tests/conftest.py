"""測試共用夾具。

隔離原則：一律用只帶規則樹與 `.wf/` 的 tmp root，⛔ 不靠 repo 裡缺了什麼檔案來成立。
遠端一律走注入式替身（tests/fakes.py），⛔ 不連網、⛔ 不 mutation 任何遠端資源。
"""

import json
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC = REPO_ROOT / "vnext" / "cli" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# 規則樹＝`wfx` 的 package data；repo 內的居所與安裝後的相對路徑同為 `wfx/rules`。
REPO_RULES = SRC / "wfx" / "rules"

TASK_ID = "o/r#370"


@pytest.fixture
def rules_root(tmp_path):
    """規則樹的獨立副本；動它⛔ 不影響 repo。"""
    dest = tmp_path / "checkout" / "rules"
    shutil.copytree(REPO_RULES, dest)
    return dest


@pytest.fixture
def project_root(tmp_path):
    """第 3 層＋`.wf/config.json`（`facts`／`brief` 都從這裡取 Project 位置）。"""
    root = tmp_path / "project"
    (root / ".wf").mkdir(parents=True)
    (root / ".wf" / "model-policy.md").write_text(
        "# 專案層政策\n具體模型名稱⛔ 不住這裡。\n", encoding="utf-8"
    )
    (root / ".wf" / "config.json").write_text(
        json.dumps({"rules": None, "remote": None, "project": {"owner": "o", "number": 9}}),
        encoding="utf-8",
    )
    return root


@pytest.fixture
def user_root(tmp_path, monkeypatch):
    """把 HOME 指到 tmp；預設 `~/.wf/` 不存在＝合法 unknown。"""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home / ".wf"


@pytest.fixture
def run_cli(rules_root, project_root, user_root, capsys):
    """跑真正的 CLI 進入點（含全域旗標前綴迴圈），回 (rc, stdout, stderr)。

    `client`／`task_source` 是動詞層的**內部**注入點，⛔ 不是公開旗標。
    """
    from wfx.verbs.main import main

    from .fakes import FakeClient

    def run(*extra, role="執行者", stage="執行", task=TASK_ID, snapshots=None,
            client=None, task_source=None, project=None):
        injected = {}
        if task_source is not None:
            injected["task_source"] = task_source
        else:
            injected["client"] = FakeClient(*(snapshots or ())) if client is None else client
        argv = [
            "--project-root", str(project if project is not None else project_root),
            "brief",
            "--task", task,
            "--role", role,
            "--stage", stage,
            "--rules-root", str(rules_root),
        ]
        argv += list(extra)
        rc = main(argv, **injected)
        captured = capsys.readouterr()
        return rc, captured.out, captured.err

    return run
