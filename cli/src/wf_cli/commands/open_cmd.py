"""``wfcli open``：依範本開卡（Issue／draft item＋git spec 檔骨架＋必填欄機械檢查）。

CLI 是唯一寫入通道：不經 CLI 直接在 GitHub UI 上手改欄位／Issue，即違反卡面紅線 1。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..card import (
    CAPABILITY_TIERS,
    Card,
    render_issue_body,
    render_spec_markdown,
    validate_capability_routing,
    validate_routing_names,
)
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
from ..validation import ValidationError, validate_chain_depth, validate_open_fields


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "open", help="依範本開卡（Issue＋git spec 檔骨架；必填欄機械檢查）"
    )
    add_target_args(p)
    p.add_argument("card_id")
    p.add_argument("--feature", required=True, help="功能（卡面標題後半段）")
    p.add_argument(
        "--tier",
        required=True,
        choices=["T0", "T1", "T2", "T3", "T4"],
        help="**風險級別** T0–T4（卡面欄位「級別」）。這條軸講的是變更風險，"
        "與 --exec-capability／--review-capability 的**能力層級**"
        "（經濟型／主力型／高階型）是兩條不同的軸，名稱雖都含 tier／層級但不可互代。",
    )
    p.add_argument(
        "--exec-capability",
        required=True,
        choices=list(CAPABILITY_TIERS),
        help="建議**執行**能力層級（MODEL_ROUTING.md「預設能力等級」欄的語彙）。"
        "引用層級而非模型名：名單會過期，層級才是穩定介面。"
        "**不是** T0–T4 風險級別（那是 --tier）。",
    )
    p.add_argument(
        "--exec-capability-reason",
        required=True,
        help="建議執行能力層級的理由（能力軸；須反映任務風險）。"
        "缺或空白一律硬拒，CLI 不代填預設值。",
    )
    p.add_argument(
        "--review-capability",
        required=True,
        choices=list(CAPABILITY_TIERS),
        help="建議**查核**能力層級（語彙同 --exec-capability）。"
        "紅線卡另須跨家族或人工查核，該獨立性要求疊加於層級之上、"
        "寫進理由，不是第四個層級。",
    )
    p.add_argument(
        "--review-capability-reason",
        required=True,
        help="建議查核能力層級的理由（能力軸）。缺或空白一律硬拒。",
    )
    p.add_argument(
        "--db-scope",
        required=True,
        choices=["none", "read", "write", "schema", "data-migration"],
    )
    p.add_argument("--core-pain", required=True, help="核心痛點")
    p.add_argument("--service-goal", required=True, help="服務的原始目標")
    p.add_argument(
        "--chain-depth",
        type=int,
        default=0,
        help="鏈深：原始目標之下第幾層（預設 0）。硬上限 2，超過依決議 5 鏈式"
        "停損協定拒絕，須整鏈重審後降級或擱置，不得逕行加深。",
    )
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

    # 規劃期路由（canonical §3 Plan／MODEL_ROUTING.md「路由決定於規劃期」）。
    # argparse 的 required＋choices 已擋掉「沒給」與「不在語彙內」；這裡補的是
    # argparse 擋不到的空白字串理由——與 --core-pain 空白時同樣硬拒，不建卡。
    #
    # ``validate_routing_names`` 檢查的是路由行**名字欄**的保留字元（見 card.py
    # 「路由行的保留字元」一段）。它同時也是 ``Card.__post_init__`` 的防線，所以拿掉
    # 這裡仍然不會建出讀不回的卡——但那條路徑拋的是 ``cli.py`` 的 ``KNOWN_ERRORS``
    # 不收的 ``ValueError``，會以 traceback 收場。**以 stack trace 收場的 fail-closed
    # 不算乾淨拒絕**，而乾淨的寫入端拒收正是本卡存在的理由，故在此補上前置檢查，
    # 讓名字側與理由側輸出同一種訊息與退出碼。
    try:
        validate_capability_routing(
            executor_capability=args.exec_capability,
            executor_capability_reason=args.exec_capability_reason,
            reviewer_capability=args.review_capability,
            reviewer_capability_reason=args.review_capability_reason,
        )
        validate_routing_names(executor=args.executor, reviewer=args.reviewer)
    except ValueError as exc:
        print(f"[open] 拒絕：{exc}", file=sys.stderr)
        return 2

    try:
        validate_chain_depth(args.chain_depth)
    except ValidationError as exc:
        for e in exc.errors:
            print(f"[open] 拒絕：{e}", file=sys.stderr)
        return 2

    card = Card(
        card_id=args.card_id,
        feature=args.feature,
        tier=args.tier,
        db_scope=args.db_scope,
        core_pain=args.core_pain,
        service_goal=args.service_goal,
        resources=decl,
        executor_capability=args.exec_capability,
        executor_capability_reason=args.exec_capability_reason,
        reviewer_capability=args.review_capability,
        reviewer_capability_reason=args.review_capability_reason,
        initiative=args.initiative,
        requested_by=args.requested_by,
        planned_by=args.planned_by,
        executor=args.executor,
        reviewer=args.reviewer,
        spec_baseline=args.spec_baseline,
        acceptance=args.acceptance or ["TODO：填入可獨立驗證的條件"],
        verification=args.verification or ["TODO：填入驗證指令與證據要求"],
        deployment_status="⏸未部署" if args.needs_deploy else "—不適用",
        chain_depth=args.chain_depth,
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
