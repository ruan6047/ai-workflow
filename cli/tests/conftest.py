from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

#: sandbox 歷史的固定基準時刻。**刻意寫死，不取「現在」**：commit 日期只要跟著
#: 牆上時鐘走，任何以日期分流的判定（doctor 的 trailer 界線就是一個）都會在某個
#: 午夜自己由綠轉紅。2026-08-13T00:00 就這樣紅過一次——測試建 commit 時採當下
#: 時間，界線一到，本該落在界線前的那筆就跑到界線後去了。
#: 值取遠早於任何產品界線的過去，且**是常數**：它不隨執行時刻改變，故不論
#: 2026、2027 或更晚跑，同一筆 commit 永遠落在同一側。
SANDBOX_COMMIT_DATE = "2020-01-01T00:00:00+08:00"


def fixed_date_env(when: str) -> dict[str, str]:
    """把一筆 commit 的作者／提交者日期釘死在 `when`（ISO8601）。

    兩個都要設：git 的作者日期與提交者日期是各自獨立的欄位，只設一個，另一個
    仍會採當下時間；而 doctor 的界線分流讀的是**提交者**日期。
    """
    return {"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}


def git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, **env} if env else None,
    )
    return proc.stdout


@pytest.fixture
def sandbox_repo(tmp_path: Path) -> Path:
    """全新的一次性 git repo（非任何真實專案），供 doctor／git_ops 測試安全地
    `git worktree add`／建分支，不會碰到使用者機器上的任何實際 repo。

    初始 commit 的日期釘在 `SANDBOX_COMMIT_DATE`，理由見該常數。
    """
    repo = tmp_path / "sandbox-repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "wf-cli tests")
    (repo / "README.md").write_text("sandbox\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-q", "-m", "init", env=fixed_date_env(SANDBOX_COMMIT_DATE))
    return repo
