"""測試共用夾具。

隔離原則：一律用只帶規則樹與 `.wf/` 的 tmp root，⛔ 不靠 repo 裡缺了什麼檔案來成立。
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

REPO_RULES = REPO_ROOT / "vnext" / "rules"

TASK_ID = "ruan/ai-workflow#370"

ISSUE_BODY = (
    "## 需求\n單一主要成果。最終需求方：ruan。\n\n"
    "## 限制與非目標\n⛔ 不新增第四個動詞。\n\n"
    "## 驗收\n六個角色各產生不同必要清單。\n\n"
    "## 風險與假設\n~/.wf/ 尚未存在。\n\n"
    "## 裁定紀錄\n- 需求核定：見留言 1\n"
)

STAGE_COMMENT = "## 規劃階段完成\n工作包：W1.1–W1.9。\n判斷留給讀者，CLI ⛔ 不解析。\n"

FIELDS = {
    "狀態": "進行中",
    "階段": "執行",
    "owner": "ruan",
    "風險": "重要",
    "緊急性": "一般",
    "期限": "",
    "Resource": "",
}


@pytest.fixture
def rules_root(tmp_path):
    """規則樹的獨立副本；動它⛔ 不影響 repo。"""
    dest = tmp_path / "checkout" / "rules"
    shutil.copytree(REPO_RULES, dest)
    return dest


@pytest.fixture
def project_root(tmp_path):
    root = tmp_path / "project"
    (root / ".wf").mkdir(parents=True)
    (root / ".wf" / "model-policy.md").write_text(
        "# 專案層政策\n具體模型名稱⛔ 不住這裡。\n", encoding="utf-8"
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
def snapshot(tmp_path):
    def make(name="task.json", **overrides):
        data = {
            "task": TASK_ID,
            "issue_body": ISSUE_BODY,
            "fields": dict(FIELDS),
            "comments": [{"url": "https://example.invalid/c1", "body": STAGE_COMMENT}],
        }
        data.update(overrides)
        path = tmp_path / name
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    return make


@pytest.fixture
def run_cli(rules_root, project_root, user_root, capsys):
    """跑真正的 CLI 進入點，回 (rc, stdout, stderr)。"""
    from wfx.verbs.main import main

    def run(*extra, role="執行者", stage="執行", task=TASK_ID, snapshot_path=None):
        argv = [
            "brief",
            "--task", task,
            "--role", role,
            "--stage", stage,
            "--rules-root", str(rules_root),
            "--project-root", str(project_root),
        ]
        if snapshot_path is not None:
            argv += ["--task-snapshot", str(snapshot_path)]
        argv += list(extra)
        rc = main(argv)
        captured = capsys.readouterr()
        return rc, captured.out, captured.err

    return run
