"""``wfcli open``：依範本開卡（Issue／draft item＋git spec 檔骨架＋必填欄機械檢查）。

CLI 是唯一寫入通道：不經 CLI 直接在 GitHub UI 上手改欄位／Issue，即違反卡面紅線 1。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..card import Card, render_issue_body, render_spec_markdown
from ..config import add_target_args, resolve_target
from ..gh import default_runner
from ..project import (
    add_item_to_project,
    create_draft_item,
    create_repo_issue,
    ensure_fields,
    find_item_by_card_id,
    list_items,
    resolve_project,
    set_field_value,
)
from ..resources import ResourceDeclaration, ResourceDeclarationError
from ..validation import ValidationError, validate_open_fields


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "open", help="依範本開卡（Issue＋git spec 檔骨架；必填欄機械檢查）"
    )
    add_target_args(p)
    p.add_argument("card_id")
    p.add_argument("--feature", required=True, help="功能（卡面標題後半段）")
    p.add_argument("--tier", required=True, choices=["T0", "T1", "T2", "T3", "T4"])
    p.add_argument(
        "--db-scope",
        required=True,
        choices=["none", "read", "write", "schema", "data-migration"],
    )
    p.add_argument("--core-pain", required=True, help="核心痛點")
    p.add_argument("--service-goal", required=True, help="服務的原始目標")
    p.add_argument(
        "--resources",
        default="",
        help="逗號分隔資源清單，如 file:a.py,port:8080；預設空（僅 db_scope）",
    )
    p.add_argument("--initiative", default=None)
    p.add_argument("--requested-by", default="—")
    p.add_argument("--planned-by", default="—")
    p.add_argument("--executor", default="待指派")
    p.add_argument("--reviewer", default="待指派")
    p.add_argument("--spec-baseline", default="—")
    p.add_argument("--acceptance", action="append", default=[], help="可重複；驗收條件逐行")
    p.add_argument("--verification", action="append", default=[], help="可重複；驗證項目逐行")
    p.add_argument(
        "--spec-dir",
        default=None,
        help="git spec 檔骨架寫入目錄（慣例 tasks/）；未給則只開 Issue／item，不寫檔",
    )
    p.add_argument(
        "--needs-deploy",
        action="store_true",
        help="卡片需要部署驗證；初始部署狀態設為 ⏸未部署（預設 —不適用）。"
        "決定 handoff --next-stage release 時是否要求先 ✅已驗證。",
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    resources_list = [r.strip() for r in args.resources.split(",") if r.strip()]
    try:
        decl = ResourceDeclaration(db_scope=args.db_scope, resources=resources_list)
    except ResourceDeclarationError as exc:
        print(f"[open] 資源宣告錯誤：{exc}", file=sys.stderr)
        return 2

    try:
        validate_open_fields(
            card_id=args.card_id,
            feature=args.feature,
            tier=args.tier,
            core_pain=args.core_pain,
            service_goal=args.service_goal,
            db_scope=args.db_scope,
            resources=decl,
        )
    except ValidationError as exc:
        for e in exc.errors:
            print(f"[open] 必填欄檢查失敗：{e}", file=sys.stderr)
        return 2

    card = Card(
        card_id=args.card_id,
        feature=args.feature,
        tier=args.tier,
        db_scope=args.db_scope,
        core_pain=args.core_pain,
        service_goal=args.service_goal,
        resources=decl,
        initiative=args.initiative,
        requested_by=args.requested_by,
        planned_by=args.planned_by,
        executor=args.executor,
        reviewer=args.reviewer,
        spec_baseline=args.spec_baseline,
        acceptance=args.acceptance or ["TODO：填入可獨立驗證的條件"],
        verification=args.verification or ["TODO：填入驗證指令與證據要求"],
        deployment_status="⏸未部署" if args.needs_deploy else "—不適用",
    )

    target = resolve_target(
        owner=args.owner, project=args.project, repo=args.repo, config=args.config
    )
    runner = default_runner
    project = resolve_project(runner, target.owner, target.project)
    fields = ensure_fields(runner, target.owner, target.project)

    existing = list_items(runner, project)
    if find_item_by_card_id(existing, card.card_id):
        print(
            f"[open] 拒絕：卡ID {card.card_id} 已存在於 project {target.owner}/{target.project}",
            file=sys.stderr,
        )
        return 3

    body = render_issue_body(card)
    title = f"{card.card_id} {card.feature}"
    issue_number: int | None = None
    issue_url: str | None = None
    if target.repo:
        issue_number, issue_url = create_repo_issue(runner, target.repo, title, body)
        item_id = add_item_to_project(runner, target.owner, target.project, issue_url)
        content_type = "Issue"
    else:
        item_id = create_draft_item(runner, target.owner, target.project, title, body)
        content_type = "DraftIssue"

    values = {
        "卡ID": card.card_id,
        "Initiative": card.initiative or "—",
        "級別": card.tier,
        "功能": card.feature,
        "owner": card.owner,
        "分支worktree": card.branch_worktree,
        "iteration": card.iteration,
        "交付狀態": card.delivery_status,
        "部署狀態": card.deployment_status,
        "最後交接": card.last_handoff,
        "服務的原始目標": card.service_goal,
        "鏈深": card.chain_depth,
        "資源宣告": decl.summary(),
    }
    for name, value in values.items():
        set_field_value(runner, project, item_id, fields[name], value)

    spec_path: Path | None = None
    if args.spec_dir:
        spec_dir = Path(args.spec_dir)
        spec_dir.mkdir(parents=True, exist_ok=True)
        spec_path = spec_dir / f"{card.card_id}.md"
        spec_path.write_text(render_spec_markdown(card), encoding="utf-8")

    location = f"item_id={item_id}，type={content_type}"
    if issue_url:
        location += f"，issue=#{issue_number} {issue_url}"
    print(f"[open] 已建立卡 {card.card_id}（{location}）")
    if spec_path:
        print(f"[open] git spec 檔骨架：{spec_path}")
    return 0
