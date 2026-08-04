"""doctor：對帳（git worktree list vs 卡註冊、submodule 未初始化、殘留 lease、
孤兒分支、prunable worktree）。全程唯讀——本卡刻意不實作任何回收／清理動作
（見卡面紅線 3：破壞性操作必須先列清單再執行；本 CLI v1 只做「列清單」那一半，
清理是另一個未來、需要明確人工核可的獨立指令，不混進 doctor）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

from . import git_ops
from .card import now_iso8601
from .registry import RegisteredCard, TasksMdRegistry

WorktreeClass = Literal[
    "registered_active", "orphan_prunable", "orphan_untracked", "detached_sandbox"
]


@dataclass
class WorktreeFinding:
    path: str
    branch: str | None
    head_sha: str | None
    classification: WorktreeClass
    detail: str
    card_id: str | None = None

    @property
    def is_orphan(self) -> bool:
        return self.classification.startswith("orphan")


@dataclass
class SubmoduleFinding:
    path: str
    status: Literal["ok", "uninitialized", "out_of_sync"]
    sha: str
    detail: str


@dataclass
class BranchFinding:
    branch: str
    merged_into_main: bool | None
    detail: str


@dataclass
class LeaseFinding:
    card_id: str
    owner: str | None
    worktree_path: str | None
    reason: str
    age_hours: float | None = None


@dataclass
class DoctorReport:
    repo_root: str
    generated_at: str
    registry_sources: list[str]
    worktrees: list[WorktreeFinding] = field(default_factory=list)
    submodules: list[SubmoduleFinding] = field(default_factory=list)
    orphan_branches: list[BranchFinding] = field(default_factory=list)
    stale_leases: list[LeaseFinding] = field(default_factory=list)

    def orphan_worktrees(self) -> list[WorktreeFinding]:
        return [w for w in self.worktrees if w.is_orphan]

    def render_text(self) -> str:
        lines = [
            f"doctor 對帳報告 — {self.repo_root}",
            f"時間：{self.generated_at}",
            f"卡註冊來源：{', '.join(self.registry_sources) or '（無；僅本機 git 檢查）'}",
            "",
            "## 1. git worktree list vs 卡註冊",
        ]
        if not self.worktrees:
            lines.append("（無額外 worktree，僅主工作樹）")
        for w in self.worktrees:
            tag = {
                "registered_active": "OK",
                "orphan_prunable": "孤兒／PRUNABLE",
                "orphan_untracked": "孤兒／未註冊",
                "detached_sandbox": "detached（略過，非孤兒）",
            }[w.classification]
            branch_s = w.branch or "(detached)"
            lines.append(f"- [{tag}] {w.path}  分支={branch_s}  {w.detail}")
        lines.append("")
        lines.append("## 2. submodule 初始化狀態")
        if not self.submodules:
            lines.append("（無 submodule）")
        for s in self.submodules:
            lines.append(f"- [{s.status}] {s.path}  {s.detail}")
        lines.append("")
        lines.append("## 3. 孤兒分支（無 worktree 且未見於卡註冊）")
        if not self.orphan_branches:
            lines.append("（無）")
        for b in self.orphan_branches:
            merged = "已併入 main" if b.merged_into_main else (
                "未併入 main" if b.merged_into_main is False else "併入狀態未知"
            )
            lines.append(f"- {b.branch}（{merged}）{b.detail}")
        lines.append("")
        lines.append("## 4. 殘留 lease（owner 已認領但跡象顯示遺棄）")
        if not self.stale_leases:
            lines.append("（無）")
        for lease in self.stale_leases:
            age = f"，已 {lease.age_hours:.1f} 小時未交接" if lease.age_hours is not None else ""
            lines.append(f"- {lease.card_id}（owner={lease.owner}）{lease.reason}{age}")
        lines.append("")
        n_orphan = len(self.orphan_worktrees())
        lines.append(
            f"摘要：{len(self.worktrees)} 個額外 worktree，{n_orphan} 個孤兒；"
            f"{len(self.orphan_branches)} 個孤兒分支；{len(self.stale_leases)} 個殘留 lease 疑慮。"
        )
        return "\n".join(lines)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def run_doctor(
    repo_root: Path,
    registry: TasksMdRegistry | None = None,
    lease_ttl_hours: float = 48.0,
    main_ref: str = "main",
) -> DoctorReport:
    repo_root = repo_root.resolve()
    active: list[RegisteredCard] = registry.active if registry else []
    archived_ids = registry.archived_card_ids if registry else set()
    by_branch: dict[str, RegisteredCard] = {rc.branch: rc for rc in active if rc.branch}

    report = DoctorReport(
        repo_root=str(repo_root),
        generated_at=now_iso8601(),
        registry_sources=[str(p) for p in (registry.source_paths if registry else [])],
    )

    # 1) worktree list vs 卡註冊 + prunable
    entries = git_ops.worktree_list(repo_root)
    for entry in entries:
        if Path(entry.path).resolve() == repo_root:
            continue  # 主工作樹本身不算「卡的 worktree」
        if entry.is_prunable:
            report.worktrees.append(
                WorktreeFinding(
                    path=entry.path, branch=entry.branch, head_sha=entry.head_sha,
                    classification="orphan_prunable",
                    detail=f"git 回報 prunable：{entry.prunable_reason}",
                )
            )
            continue
        if entry.branch is None:
            report.worktrees.append(
                WorktreeFinding(
                    path=entry.path, branch=None, head_sha=entry.head_sha,
                    classification="detached_sandbox",
                    detail="detached HEAD、非 prunable；可能是查核用 disposable worktree"
                    "（worktree-lifecycle.md §3），無分支可比對卡註冊，不計孤兒",
                )
            )
            continue
        registered = by_branch.get(entry.branch)
        if registered:
            report.worktrees.append(
                WorktreeFinding(
                    path=entry.path, branch=entry.branch, head_sha=entry.head_sha,
                    classification="registered_active", card_id=registered.card_id,
                    detail=f"對應活卡 {registered.card_id}（交付狀態 {registered.delivery_status}）",
                )
            )
        else:
            hint = ""
            if entry.branch in archived_ids or any(
                aid.lower() in entry.branch.lower() for aid in archived_ids
            ):
                hint = "；分支名稱疑似對應到已封存卡，但封存表未留分支欄可精確核對"
            report.worktrees.append(
                WorktreeFinding(
                    path=entry.path, branch=entry.branch, head_sha=entry.head_sha,
                    classification="orphan_untracked",
                    detail=f"分支 {entry.branch!r} 未見於任何活卡的分支／worktree 欄{hint}",
                )
            )

    # 2) submodule 初始化狀態
    for sub in git_ops.submodule_status(repo_root):
        if not sub.initialized:
            status: Literal["ok", "uninitialized", "out_of_sync"] = "uninitialized"
            detail = "尚未 `git submodule update --init`"
        elif sub.out_of_sync:
            status = "out_of_sync"
            detail = "checkout 的 commit 與父repo記錄的 SHA 不同"
        else:
            status = "ok"
            detail = f"已初始化（{sub.describe or sub.sha[:12]}）"
        report.submodules.append(
            SubmoduleFinding(path=sub.path, status=status, sha=sub.sha, detail=detail)
        )

    # 3) 孤兒分支：本地分支存在、但沒有 worktree 也沒有卡註冊
    worktree_branches = {e.branch for e in entries if e.branch}
    try:
        all_branches = git_ops.local_branches(repo_root)
    except git_ops.GitError:
        all_branches = []
    for branch in all_branches:
        if branch == main_ref or branch in worktree_branches or branch in by_branch:
            continue
        merged: bool | None
        try:
            merged = git_ops.is_ancestor(repo_root, branch, main_ref)
        except git_ops.GitError:
            merged = None
        detail = "已完全併入 main，可安全清理（僅列出，未刪除）" if merged else "尚未併入 main，暫勿清理"
        report.orphan_branches.append(
            BranchFinding(branch=branch, merged_into_main=merged, detail=detail)
        )

    # 4) 殘留 lease：owner 已認領，但 worktree 路徑在磁碟上不存在（機械、確定）
    #    或最後交接已超過 lease_ttl_hours（啟發式、僅供人工判斷，不自動回收）。
    now = datetime.now().astimezone()
    for rc in active:
        if not rc.owner_assigned():
            continue
        reasons: list[str] = []
        if rc.worktree_path:
            wt_path = repo_root / rc.worktree_path
            if not wt_path.exists():
                reasons.append(f"註冊的 worktree 路徑 {rc.worktree_path} 在磁碟上不存在")
        age_hours: float | None = None
        handoff_dt = _parse_iso(rc.last_handoff)
        if handoff_dt is not None:
            age_hours = (now - handoff_dt).total_seconds() / 3600.0
            if age_hours > lease_ttl_hours:
                reasons.append(f"最後交接超過 lease TTL（{lease_ttl_hours}h）")
        if reasons:
            report.stale_leases.append(
                LeaseFinding(
                    card_id=rc.card_id, owner=rc.owner, worktree_path=rc.worktree_path,
                    reason="；".join(reasons), age_hours=age_hours,
                )
            )

    return report


__all__ = [
    "BranchFinding",
    "DoctorReport",
    "LeaseFinding",
    "SubmoduleFinding",
    "WorktreeFinding",
    "run_doctor",
]
