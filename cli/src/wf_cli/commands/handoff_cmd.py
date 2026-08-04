"""``wfcli handoff``：交接（狀態轉換＋source SHA＋證據欄必填）。

source_sha 必須是完整 40 字元 hex；``--repo-path`` 有給時另外唯讀驗證該 commit
真的存在於本機 repo（對齊 handoff-contract.md §1「sender 必須先 push source_sha
指向的 commit」的精神——CLI 能做的部份先擋，pushed／branch tip 一致性仍需
receiver 自行複查，CLI 不代替人類判斷）。release 若卡片需要部署且尚未 ✅已驗證，
機械拒絕（canonical §0「需部署卡在部署 ✅已驗證 前不得 release」）。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .. import git_ops
from ..card import append_log_line, now_iso8601
from ..config import add_target_args, resolve_target
from ..gh import default_runner
from ..project import (
    ensure_fields,
    find_item_by_card_id,
    list_items,
    resolve_project,
    set_field_value,
    set_item_body,
)
from ..validation import ValidationError, validate_evidence, validate_source_sha

STAGE_STATUS = {
    "implementation": "🚧進行中",
    "review": "🔍待查核",
}


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("handoff", help="交接：狀態轉換＋source SHA＋證據欄必填")
    add_target_args(p)
    p.add_argument("card_id")
    p.add_argument("--to", required=True, help="下一位 owner（角色／帳號／模型@工具）")
    p.add_argument(
        "--next-stage", required=True, choices=["implementation", "review", "release"]
    )
    p.add_argument("--source-sha", required=True, help="完整 40 字元 hex SHA")
    p.add_argument("--evidence", required=True, help="測試／CI／審核／決策連結或摘要")
    p.add_argument(
        "--repo-path",
        default=None,
        help="有給則唯讀驗證 source_sha 在該本機 repo 存在（不驗證是否已 push）",
    )
    p.add_argument("--status", default=None, help="覆寫依 next-stage 推導出的交付狀態")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    try:
        validate_source_sha(args.source_sha)
        validate_evidence(args.evidence)
    except ValidationError as exc:
        for e in exc.errors:
            print(f"[handoff] {e}", file=sys.stderr)
        return 2

    if args.repo_path:
        repo_root = Path(args.repo_path)
        if not git_ops.commit_exists(repo_root, args.source_sha):
            print(
                f"[handoff] 拒絕：source_sha {args.source_sha} 在 {repo_root} 找不到對應 commit",
                file=sys.stderr,
            )
            return 2

    target = resolve_target(
        owner=args.owner, project=args.project, repo=args.repo, config=args.config
    )
    runner = default_runner
    project = resolve_project(runner, target.owner, target.project)
    fields = ensure_fields(runner, target.owner, target.project)

    items = list_items(runner, project)
    item = find_item_by_card_id(items, args.card_id)
    if not item:
        print(f"[handoff] 找不到卡 {args.card_id}", file=sys.stderr)
        return 3

    if args.status:
        new_status = args.status
    elif args.next_stage == "release":
        deployment_status = item.fields.get("部署狀態")
        if deployment_status not in (None, "—不適用", "✅已驗證"):
            print(
                "[handoff] 拒絕：需部署卡在部署 ✅已驗證 前不得 release"
                f"（目前部署狀態={deployment_status}；canonical §0）",
                file=sys.stderr,
            )
            return 4
        new_status = "🏁完成"
    else:
        new_status = STAGE_STATUS[args.next_stage]

    iteration = item.fields.get("iteration")
    iteration = int(iteration) if iteration is not None else 0
    ts = now_iso8601()

    set_field_value(runner, project, item.item_id, fields["owner"], args.to)
    set_field_value(runner, project, item.item_id, fields["交付狀態"], new_status)
    set_field_value(runner, project, item.item_id, fields["最後交接"], ts)

    log_line = (
        f"{ts} handoff by wf-cli → owner {args.to}；iteration {iteration}；"
        f"SHA {args.source_sha}；證據 {args.evidence}。"
    )
    new_body = append_log_line(item.body, log_line)
    set_item_body(runner, item.content_type, item.content_id, project, target.repo, item.issue_number, new_body)

    print(f"[handoff] 已交接 {args.card_id} → {args.to}（狀態={new_status}，SHA={args.source_sha}）")
    return 0
