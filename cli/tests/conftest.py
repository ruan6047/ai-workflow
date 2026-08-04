from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return proc.stdout


@pytest.fixture
def sandbox_repo(tmp_path: Path) -> Path:
    """全新的一次性 git repo（非任何真實專案），供 doctor／git_ops 測試安全地
    `git worktree add`／建分支，不會碰到使用者機器上的任何實際 repo。
    """
    repo = tmp_path / "sandbox-repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "wf-cli tests")
    (repo / "README.md").write_text("sandbox\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-q", "-m", "init")
    return repo
