"""``wfcli doctor``：對帳（git worktree list vs 卡註冊、submodule、孤兒分支、殘留 lease、
prunable worktree）。全程唯讀，見 doctor.py 模組說明；本指令不實作任何清理動作。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from ..doctor import run_doctor
from ..registry import load_tasks_md_registry


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "doctor", help="對帳：worktree／submodule／孤兒分支／殘留 lease／prunable（唯讀）"
    )
    p.add_argument("repo_root", help="要檢查的 git repo 路徑（唯讀操作，不寫入）")
    p.add_argument(
        "--registry",
        choices=["tasks-md", "none"],
        default="tasks-md",
        help="卡註冊來源：tasks-md 讀 docs/TASKS.md（未 cutover 專案）；none 只做純 git 檢查",
    )
    p.add_argument("--main-ref", default="main", help="判斷「已併入」與 lease 交集比對用的主幹分支")
    p.add_argument("--lease-ttl-hours", type=float, default=48.0)
    p.add_argument("--json", action="store_true", help="額外輸出 JSON（供腳本消費）")
    p.add_argument(
        "--strict",
        action="store_true",
        help="有孤兒 worktree／分支時回傳非 0 exit code（CI 用；預設不失敗，純報告）",
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root)
    if not repo_root.exists():
        print(f"[doctor] repo 路徑不存在：{repo_root}", file=sys.stderr)
        return 2

    registry = load_tasks_md_registry(repo_root) if args.registry == "tasks-md" else None
    report = run_doctor(
        repo_root,
        registry,
        lease_ttl_hours=args.lease_ttl_hours,
        main_ref=args.main_ref,
    )
    print(report.render_text())
    if args.json:
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2, default=str))

    if args.strict and (report.orphan_worktrees() or report.orphan_branches):
        return 1
    return 0
