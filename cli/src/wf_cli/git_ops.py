"""唯讀 git 操作：worktree／submodule／branch 檢視。doctor 與 handoff 的 SHA 驗證共用。

紅線：這個模組只准出現讀取類子命令（``list``／``status``／``for-each-ref``／
``cat-file -e``／``merge-base``）。doctor 的破壞性操作（lease 回收、worktree
清理）本卡刻意不實作，只列清單（見卡面紅線 3）。
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(RuntimeError):
    pass


def _run(repo_root: Path, args: list[str]) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


@dataclass
class WorktreeEntry:
    path: str
    head_sha: str | None
    branch: str | None  # short name, e.g. "main"；detached 則 None
    is_bare: bool = False
    is_detached: bool = False
    is_prunable: bool = False
    prunable_reason: str = ""


def parse_worktree_porcelain(text: str) -> list[WorktreeEntry]:
    entries: list[WorktreeEntry] = []
    current: dict[str, str] = {}

    def flush() -> None:
        if not current:
            return
        branch_ref = current.get("branch")
        branch = branch_ref.removeprefix("refs/heads/") if branch_ref else None
        entries.append(
            WorktreeEntry(
                path=current["worktree"],
                head_sha=current.get("HEAD"),
                branch=branch,
                is_bare="bare" in current,
                is_detached="detached" in current,
                is_prunable="prunable" in current,
                prunable_reason=current.get("prunable", ""),
            )
        )

    for line in text.splitlines():
        if not line.strip():
            flush()
            current = {}
            continue
        if line == "bare":
            current["bare"] = "true"
            continue
        if line == "detached":
            current["detached"] = "true"
            continue
        parts = line.split(" ", 1)
        key = parts[0]
        value = parts[1] if len(parts) > 1 else "true"
        current[key] = value
    flush()
    return entries


def worktree_list(repo_root: Path) -> list[WorktreeEntry]:
    out = _run(repo_root, ["worktree", "list", "--porcelain"])
    return parse_worktree_porcelain(out)


@dataclass
class SubmoduleEntry:
    sha: str
    path: str
    initialized: bool
    out_of_sync: bool  # '+' 前綴：checkout 的 commit 與記錄的 SHA 不同
    describe: str | None = None


_SUBMODULE_LINE_RE = re.compile(r"^(?P<flag>[ +\-U])(?P<sha>[0-9a-f]{40}) (?P<path>\S+)(?: \((?P<describe>.+)\))?$")


def parse_submodule_status(text: str) -> list[SubmoduleEntry]:
    entries: list[SubmoduleEntry] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        match = _SUBMODULE_LINE_RE.match(line)
        if not match:
            continue
        flag = match.group("flag")
        entries.append(
            SubmoduleEntry(
                sha=match.group("sha"),
                path=match.group("path"),
                initialized=flag != "-",
                out_of_sync=flag == "+",
                describe=match.group("describe"),
            )
        )
    return entries


def submodule_status(repo_root: Path) -> list[SubmoduleEntry]:
    if not (repo_root / ".gitmodules").exists():
        return []
    out = _run(repo_root, ["submodule", "status"])
    return parse_submodule_status(out)


def local_branches(repo_root: Path) -> list[str]:
    out = _run(repo_root, ["for-each-ref", "--format=%(refname:short)", "refs/heads/"])
    return [line.strip() for line in out.splitlines() if line.strip()]


def is_ancestor(repo_root: Path, sha: str, ref: str = "main") -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", sha, ref],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def commit_exists(repo_root: Path, sha: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "-e", f"{sha}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def branch_tip(repo_root: Path, branch: str) -> str | None:
    try:
        out = _run(repo_root, ["rev-parse", "--verify", branch])
    except GitError:
        return None
    return out.strip() or None


__all__ = [
    "GitError",
    "SubmoduleEntry",
    "WorktreeEntry",
    "branch_tip",
    "commit_exists",
    "is_ancestor",
    "local_branches",
    "parse_submodule_status",
    "parse_worktree_porcelain",
    "submodule_status",
    "worktree_list",
]
