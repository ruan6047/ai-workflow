"""``wfcli deploy-state``：受控部署轉換與 Projects Status 視覺同步。

部署狀態是 canonical AI_WORKFLOW.md §0 的獨立線性狀態機。這個命令只接受相鄰
前進轉換，先追加 Issue timeline event，再用 GraphQL
``updateProjectV2ItemFieldValue`` 寫入 item 值；不建立、不修改任何 Project 欄位定義。
"""

from __future__ import annotations

import argparse
import sys

from ..card import now_iso8601
from ..config import add_target_args, resolve_target
from ..gh import default_runner
from ..project import (
    add_issue_comment,
    find_item_by_card_id,
    list_fields,
    list_items,
    resolve_project,
    update_item_field_value,
)
from ..validation import ValidationError, validate_evidence

DEPLOYMENT_TRANSITIONS = {
    "⏸未部署": "🚀待部署",
    "🚀待部署": "⏳部署中",
    "⏳部署中": "✅已部署",
    "✅已部署": "🧪驗證中",
    "🧪驗證中": "✅已驗證",
}

# GitHub Projects 的內建 Status 是視覺投影，不取代部署狀態本身。映射故意小且
# 固定，Project 若沒有這三個內建選項就拒絕，避免依顏色或 option 排序猜測語意。
PROJECT_STATUS_BY_DEPLOYMENT_STATUS = {
    "⏸未部署": "Todo",
    "🚀待部署": "Todo",
    "⏳部署中": "In Progress",
    "✅已部署": "In Progress",
    "🧪驗證中": "In Progress",
    "✅已驗證": "Done",
}
REQUIRED_FIELDS = ("部署狀態", "owner", "最後交接", "Status")


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "deploy-state",
        help="受控轉換部署狀態，並同步 Project 內建 Status 與 Issue timeline",
    )
    add_target_args(p)
    p.add_argument("card_id")
    p.add_argument("--to", required=True, choices=tuple(DEPLOYMENT_TRANSITIONS.values()))
    p.add_argument("--next-owner", required=True, help="轉換後的 stage owner")
    p.add_argument("--actor", required=True, help="追加 deployment event 的 PM 祕書／操作者")
    p.add_argument("--evidence", required=True, help="部署或驗證的可稽核證據")
    p.add_argument("--dry-run", action="store_true", help="只驗證與輸出計畫，不寫 GitHub")
    p.set_defaults(func=run)


def _timeline_comment(
    *, card_id: str, actor: str, owner: str, occurred_at: str,
    current: str, target: str, project_status: str, evidence: str,
) -> str:
    return f"""## deployment-state

- event: deployment-status-change
- card_id: {card_id}
- actor: {actor}
- owner: {owner}
- occurred_at: {occurred_at}
- transition: {current} → {target}
- project_status: {project_status}
- evidence: {evidence.strip()}
"""


def run(args: argparse.Namespace) -> int:
    try:
        validate_evidence(args.evidence)
    except ValidationError as exc:
        print(f"[deploy-state] 拒絕：{exc}", file=sys.stderr)
        return 2

    target = resolve_target(
        owner=args.owner, project=args.project, repo=args.repo, config=args.config
    )
    if not target.repo:
        print("[deploy-state] 拒絕：需要 --repo 才能追加 Issue timeline event", file=sys.stderr)
        return 2

    runner = default_runner
    project = resolve_project(runner, target.owner, target.project)
    fields = list_fields(runner, target.owner, target.project)
    missing = [name for name in REQUIRED_FIELDS if name not in fields]
    if missing:
        print(
            "[deploy-state] 拒絕：Project 缺少既有必要欄位 " + "、".join(missing)
            + "；本命令不建立或修改欄位定義",
            file=sys.stderr,
        )
        return 2

    item = find_item_by_card_id(list_items(runner, project), args.card_id)
    if not item:
        print(f"[deploy-state] 找不到卡 {args.card_id}", file=sys.stderr)
        return 3
    if item.content_type != "Issue" or item.issue_number is None:
        print("[deploy-state] 拒絕：部署事件必須寫入真實 repo Issue，draft item 不可退化", file=sys.stderr)
        return 2

    current = item.fields.get("部署狀態")
    expected = DEPLOYMENT_TRANSITIONS.get(current)
    if expected != args.to:
        print(
            f"[deploy-state] 拒絕：非法部署轉換 {current!r} → {args.to!r}；"
            f"此狀態只允許下一步 {expected!r}",
            file=sys.stderr,
        )
        return 4

    project_status = PROJECT_STATUS_BY_DEPLOYMENT_STATUS[args.to]
    if project_status not in fields["Status"].options:
        print(
            f"[deploy-state] 拒絕：Project 內建 Status 缺少映射選項 {project_status!r}；"
            "不以 option 順序或顏色猜測",
            file=sys.stderr,
        )
        return 2

    occurred_at = now_iso8601()
    if args.dry_run:
        print(
            f"[deploy-state] dry-run：{args.card_id} {current} → {args.to}；"
            f"Status={project_status}；owner={args.next_owner}；不寫入 GitHub"
        )
        return 0

    # Event 先於 current-state 寫入，避免值已翻轉卻缺少稽核證據。
    add_issue_comment(
        runner,
        target.repo,
        item.issue_number,
        _timeline_comment(
            card_id=args.card_id,
            actor=args.actor,
            owner=args.next_owner,
            occurred_at=occurred_at,
            current=current,
            target=args.to,
            project_status=project_status,
            evidence=args.evidence,
        ),
    )
    update_item_field_value(runner, project, item.item_id, fields["部署狀態"], args.to)
    update_item_field_value(runner, project, item.item_id, fields["Status"], project_status)
    update_item_field_value(runner, project, item.item_id, fields["owner"], args.next_owner)
    update_item_field_value(runner, project, item.item_id, fields["最後交接"], occurred_at)

    print(
        f"[deploy-state] 已轉換 {args.card_id}：{current} → {args.to}；"
        f"Status={project_status}；owner={args.next_owner}"
    )
    return 0
