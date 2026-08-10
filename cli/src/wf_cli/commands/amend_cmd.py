"""``wfcli amend``：開卡後修訂卡面欄位（唯一寫入通道補上缺的那一塊）。

痛點：`open` 之後卡面就凍住了。spec 基線隨上游卡 merge 而變、驗收條件被需求方追加、
tier 開卡時填錯——這些都是常態，但 CLI 沒有入口，於是每次更正都改用 `gh issue edit`
或 Project GraphQL mutation 直接寫，繞過唯一寫入通道。2026-08-10 一天之內就繞了四次
（ai-workflow#15 的 tier、#17 的 spec 基線與 Log 渲染修復），這不是紀律問題，是工具缺口。

範圍界定（#19 驗收第 4 條）：本指令**同時**涵蓋 body 欄位與 Project 的 `級別` 欄位，
`WF-CLI-TIER-MUTATION1`（ai-workflow#12）因此併入本卡，不另行實作。兩者是不同的寫入面
（卡面文字 vs 狀態欄位），但對使用者是同一件事——「開完卡才發現要改」。

三條紅線：

- **原值必留**：每個被改的欄位都 append 一行 Log，記下原值與理由。沒有理由不准改
  （`--reason` 必填），值沒變也不准改（拒絕寫入不實的留痕）。
- **不動 Log**：修訂只作用於 `## Log` 之前；Log 是 append-only，本能力不為自己破例。
  body 排版壞到無法安全定位 Log 時直接拒絕，不猜。
- **先驗證後寫入**：任一欄位驗證失敗就整批不寫，不留半套修改。

退出碼：0 成功／2 參數或內容檢查失敗（未寫入）／3 找不到卡。
"""

from __future__ import annotations

import argparse
import sys

from ..card import (
    TIERS,
    AmendError,
    amend_acceptance,
    amend_resource_block,
    amend_spec_baseline,
    amend_verification,
    append_log_line,
    now_iso8601,
)
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
from ..resources import ResourceDeclaration, ResourceDeclarationError, parse_block, render_block


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "amend", help="開卡後修訂卡面：spec 基線／驗收／驗證／資源宣告／級別（原值寫入 Log）"
    )
    add_target_args(p)
    p.add_argument("card_id")
    p.add_argument("--reason", required=True, help="修訂理由；會寫進 Log，不得為空")
    p.add_argument("--spec-baseline", default=None)
    p.add_argument(
        "--acceptance",
        action="append",
        default=None,
        help="可重複；給定時整份取代驗收條件（文字未變的項目沿用原勾選狀態）",
    )
    p.add_argument(
        "--verification",
        action="append",
        default=None,
        help="可重複；給定時整份取代驗證項目（文字未變的項目沿用原勾選狀態）",
    )
    p.add_argument(
        "--db-scope",
        default=None,
        help="改資源宣告的 db_scope；與 --resources 至少給一個才會動資源宣告區塊",
    )
    p.add_argument(
        "--resources",
        default=None,
        help="逗號分隔資源清單，整份取代；空字串代表清空",
    )
    p.add_argument("--tier", choices=TIERS, default=None, help="更正級別（Project 欄位）")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="只驗證與列印將寫入的變更，不連 GitHub 寫入任何狀態",
    )
    p.set_defaults(func=run)


def _fold(text: str, limit: int = 400) -> str:
    """Log 是單行條目，原值先摺成一行。超長才截斷，並標明截斷位置。"""
    folded = " ".join(str(text).split())
    if len(folded) <= limit:
        return folded
    return folded[:limit] + f"…（全文共 {len(folded)} 字，此處截斷）"


def run(args: argparse.Namespace) -> int:
    if not args.reason.strip():
        print("[amend] 拒絕：--reason 不得為空（每次修訂都要能回答為什麼）", file=sys.stderr)
        return 2

    wants_resources = args.db_scope is not None or args.resources is not None
    if not any([args.spec_baseline, args.acceptance, args.verification, wants_resources, args.tier]):
        print("[amend] 拒絕：沒有指定任何要修訂的欄位", file=sys.stderr)
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
        print(f"[amend] 找不到卡 {args.card_id}", file=sys.stderr)
        return 3

    body = item.body
    changes: list[tuple[str, str, str]] = []  # (欄位, 原值, 新值)

    try:
        if args.spec_baseline is not None:
            body, old = amend_spec_baseline(body, args.spec_baseline)
            changes.append(("spec 基線", old, args.spec_baseline))
        if args.acceptance is not None:
            body, old = amend_acceptance(body, args.acceptance)
            changes.append(("驗收條件", old, "；".join(args.acceptance)))
        if args.verification is not None:
            body, old = amend_verification(body, args.verification)
            changes.append(("驗證", old, "；".join(args.verification)))
        if wants_resources:
            current = parse_block(item.body)
            db_scope = args.db_scope if args.db_scope is not None else current.db_scope
            resources = (
                [r.strip() for r in args.resources.split(",") if r.strip()]
                if args.resources is not None
                else current.resources
            )
            decl = ResourceDeclaration(db_scope=db_scope, resources=resources)
            body, old = amend_resource_block(body, render_block(decl))
            changes.append(("資源宣告", old, decl.summary()))
    except (AmendError, ResourceDeclarationError) as exc:
        print(f"[amend] 拒收（未寫入任何狀態）：{exc}", file=sys.stderr)
        return 2

    old_tier = item.text("級別")
    if args.tier is not None:
        if old_tier == args.tier:
            print(
                f"[amend] 拒收（未寫入任何狀態）：級別已是 {args.tier}；"
                "拒絕寫入不實的修訂留痕",
                file=sys.stderr,
            )
            return 2
        changes.append(("級別", old_tier or "（未設定）", args.tier))

    timestamp = now_iso8601()
    for field_name, old, new in changes:
        body = append_log_line(
            body,
            f"{timestamp} amend by wf-cli → {field_name}："
            f"原值「{_fold(old)}」→ 新值「{_fold(new)}」；理由 {_fold(args.reason)}。",
        )

    if args.dry_run:
        print(f"[amend] dry-run（未寫入任何狀態）：{args.card_id} 將修訂 {len(changes)} 個欄位")
        for field_name, old, new in changes:
            print(f"  - {field_name}：「{_fold(old, 120)}」→「{_fold(new, 120)}」")
        return 0

    # body 先寫、Project 欄位後寫：反過來若 body 寫失敗，板上會出現改過的級別卻沒有
    # 對應 Log，正是本卡要消滅的「改了但查不到為什麼」。
    set_item_body(
        runner, item.content_type, item.content_id, project, target.repo, item.issue_number, body
    )
    if args.tier is not None:
        set_field_value(runner, project, item.item_id, fields["級別"], args.tier)

    print(f"[amend] 已修訂 {args.card_id}（{len(changes)} 個欄位，原值已寫入 Log）")
    for field_name, old, new in changes:
        print(f"  - {field_name}：「{_fold(old, 80)}」→「{_fold(new, 80)}」")
    return 0
