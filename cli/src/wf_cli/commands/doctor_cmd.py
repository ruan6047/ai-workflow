"""``wfcli doctor``：對帳（git worktree list vs 卡註冊、submodule、孤兒分支、殘留 lease、
prunable worktree）。全程唯讀，見 doctor.py 模組說明；本指令不實作任何清理動作。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from ..doctor import audit_review_channel, run_doctor
from ..gh import default_runner
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
    p.add_argument(
        "--review-channel",
        action="store_true",
        help="另對帳指定 Issue 的外部查核收據與 wfcli review event（唯讀、fail-closed）",
    )
    p.add_argument("--repo", help="--review-channel 的 GitHub repo，格式 owner/repo")
    p.add_argument("--issue-number", type=int, help="--review-channel 的 Issue/PR number")
    p.add_argument("--card-id", help="--review-channel 的卡 ID")
    p.add_argument("--source-sha", help="--review-channel 的完整 40 字元受審 SHA")
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
    review_channel_finding = None
    if args.review_channel:
        missing = [
            flag for flag, value in (
                ("--repo", args.repo),
                ("--issue-number", args.issue_number),
                ("--card-id", args.card_id),
                ("--source-sha", args.source_sha),
            ) if not value
        ]
        if missing:
            print(f"[doctor] --review-channel 缺必要旗標：{', '.join(missing)}", file=sys.stderr)
            return 2
        comments = default_runner.run_json(
            ["api", f"repos/{args.repo}/issues/{args.issue_number}/comments", "--paginate"]
        )
        finding = audit_review_channel(comments or [], args.card_id, args.source_sha)
        review_channel_finding = finding
        print("\n## 5. 跨工具查核寫入通道")
        print(f"- [{finding.status}] {finding.detail}")
        for url in finding.receipt_urls:
            print(f"  - receipt: {url}")
    if args.json:
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2, default=str))

    if args.strict and (
        report.orphan_worktrees()
        or report.orphan_branches
        or (review_channel_finding is not None and review_channel_finding.status != "recorded")
    ):
        return 1
    return 0
