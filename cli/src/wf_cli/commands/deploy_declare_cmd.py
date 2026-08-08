"""``wfcli deploy-declare``：受控宣告既有卡需要部署。

這不是 ``deploy-state`` 的跳轉例外，而是需求方已作出明確決策時才可使用的一次性
更正入口。它唯一允許 ``—不適用 → ⏸未部署``，並把 decision/reason 留在真實
Issue timeline；所有 Project item 值仍只走 ``updateProjectV2ItemFieldValue``。
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

DECLARATION_SOURCE = "—不適用"
DECLARATION_TARGET = "⏸未部署"
PROJECT_STATUS = "Todo"
REQUIRED_FIELDS = ("部署狀態", "Status")


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "deploy-declare",
        help="依需求方明確決策將既有卡宣告為需要部署（僅 —不適用 → ⏸未部署）",
    )
    add_target_args(p)
    p.add_argument("card_id")
    p.add_argument(
        "--decision",
        required=True,
        choices=["needs-deploy"],
        help="需求方已確認的部署分類決策（唯一允許 needs-deploy）",
    )
    p.add_argument("--reason", required=True, help="需求方決策的具體理由，不得空白")
    p.add_argument("--actor", required=True, help="追加 declaration event 的 PM 祕書／操作者")
    p.add_argument("--dry-run", action="store_true", help="只驗證與輸出計畫，不寫 GitHub")
    p.set_defaults(func=run)


def _timeline_comment(*, card_id: str, actor: str, occurred_at: str, reason: str) -> str:
    return f"""## deployment-declaration

- event: deployment-declaration
- card_id: {card_id}
- actor: {actor}
- occurred_at: {occurred_at}
- decision: needs-deploy
- reason: {reason.strip()}
- transition: {DECLARATION_SOURCE} → {DECLARATION_TARGET}
- project_status: {PROJECT_STATUS}
"""


def run(args: argparse.Namespace) -> int:
    if not args.reason or not args.reason.strip():
        print("[deploy-declare] 拒絕：reason 必填，不得為空字串", file=sys.stderr)
        return 2

    target = resolve_target(
        owner=args.owner, project=args.project, repo=args.repo, config=args.config
    )
    if not target.repo:
        print("[deploy-declare] 拒絕：需要 --repo 才能追加 Issue timeline event", file=sys.stderr)
        return 2

    runner = default_runner
    project = resolve_project(runner, target.owner, target.project)
    fields = list_fields(runner, target.owner, target.project)
    missing = [name for name in REQUIRED_FIELDS if name not in fields]
    if missing:
        print(
            "[deploy-declare] 拒絕：Project 缺少既有必要欄位 " + "、".join(missing)
            + "；本命令不建立或修改欄位定義",
            file=sys.stderr,
        )
        return 2

    item = find_item_by_card_id(list_items(runner, project), args.card_id)
    if not item:
        print(f"[deploy-declare] 找不到卡 {args.card_id}", file=sys.stderr)
        return 3
    if item.content_type != "Issue" or item.issue_number is None:
        print("[deploy-declare] 拒絕：declaration 必須寫入真實 repo Issue，draft item 不可退化", file=sys.stderr)
        return 2

    current = item.fields.get("部署狀態")
    if current != DECLARATION_SOURCE:
        print(
            f"[deploy-declare] 拒絕：僅允許 {DECLARATION_SOURCE} → {DECLARATION_TARGET}；"
            f"目前部署狀態={current!r}",
            file=sys.stderr,
        )
        return 4
    if PROJECT_STATUS not in fields["Status"].options:
        print(
            f"[deploy-declare] 拒絕：Project 內建 Status 缺少映射選項 {PROJECT_STATUS!r}；"
            "不以 option 順序或顏色猜測",
            file=sys.stderr,
        )
        return 2

    occurred_at = now_iso8601()
    if args.dry_run:
        print(
            f"[deploy-declare] dry-run：{args.card_id} {DECLARATION_SOURCE} → "
            f"{DECLARATION_TARGET}；Status={PROJECT_STATUS}；不寫入 GitHub"
        )
        return 0

    # Event 先於 current-state 寫入，避免分類已更正卻無需求方決策依據。
    add_issue_comment(
        runner,
        target.repo,
        item.issue_number,
        _timeline_comment(
            card_id=args.card_id,
            actor=args.actor,
            occurred_at=occurred_at,
            reason=args.reason,
        ),
    )
    update_item_field_value(
        runner, project, item.item_id, fields["部署狀態"], DECLARATION_TARGET
    )
    update_item_field_value(runner, project, item.item_id, fields["Status"], PROJECT_STATUS)

    print(
        f"[deploy-declare] 已宣告 {args.card_id} 需要部署："
        f"{DECLARATION_SOURCE} → {DECLARATION_TARGET}；Status={PROJECT_STATUS}"
    )
    return 0
