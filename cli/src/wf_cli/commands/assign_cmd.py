"""``wfcli assign``：派工（寫 owner／worktree 註冊欄；資源宣告交集檢查，撞則拒絕）。

交集檢查規則見 ``resources.find_conflicts``：file/port/container 一律互斥；
db:* 資源雙方 db_scope 皆為 read 時可共用。

**衝突比對範圍刻意限定「已指派」的活卡**（owner 非「待指派」等佔位字串），不含
單純躺在 Backlog、還沒人認領的卡：後者只是「未來可能touch」的宣告，尚未有實際
執行中的分支／worktree 與它爭資源，此時擋下 assign 只會讓資源宣告機制在實務上
變得毫無用處（任兩張卡只要都規劃碰同一檔案就永遠卡死）。真正的風險是「兩張卡
同時有人在執行」，這正是 WF-22-CLI1 核心痛點描述的 worktree／資源撞車情境。

別卡（非本次目標卡）若資源宣告解析不出來，只警告、不擋本次 assign——本卡是唯一
寫入通道的「新」入口，遷移期間舊卡尚未補宣告不該讓新卡整個卡死；但目標卡「自己」
的宣告解析失敗則直接拒絕（fail closed on self）。

**規劃期路由的派工端**（WF-CLI-ROUTING-TIER1 R1-001）：``MODEL_ROUTING.md`` 第 14 行
後半要求「派工時可依可用性偏離建議，但實際模型與偏離理由記入 claim 事件」。因此
``--actual-capability`` 必填（實際模型以能力層級表述，語彙同開卡端；``--assignee``
記的是具體模型名），並與卡面第 4 行的建議執行層級比對——非「相符」一律 fail-closed
要求 ``--capability-deviation-reason``。比對是四格全函數，見
``card.compare_capability_to_card``。
"""

from __future__ import annotations

import argparse
import sys

from ..card import (
    CAPABILITY_TIERS,
    append_log_line,
    compare_capability_to_card,
    format_branch_worktree,
    is_owner_assigned,
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
from ..resources import (
    ResourceDeclarationError,
    find_conflicts,
    parse_block,
    try_parse_block,
)

TERMINAL_STATUSES = {"🏁完成", "🛑已停止"}


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "assign", help="派工：寫 owner／worktree 註冊欄＋資源互斥交集檢查"
    )
    add_target_args(p)
    p.add_argument("card_id")
    p.add_argument("--assignee", required=True, help="新 owner（帳號／模型@工具）")
    p.add_argument("--branch", required=True)
    p.add_argument("--worktree", required=True)
    p.add_argument(
        "--status", default="🚧進行中", help="assign 後的交付狀態；預設 🚧進行中"
    )
    p.add_argument(
        "--actual-capability",
        required=True,
        choices=list(CAPABILITY_TIERS),
        help="**實際**派到的能力層級（MODEL_ROUTING.md「預設能力等級」語彙；具體模型名"
        "寫在 --assignee）。會與卡面第 4 行的建議執行層級比對，非相符即需偏離理由。"
        "**不是** T0–T4 風險級別（那是卡面「級別」欄，由 open --tier／amend --tier 寫）。",
    )
    p.add_argument(
        "--capability-deviation-reason",
        default=None,
        help="實際能力層級與卡面建議不符時的偏離理由；卡面無建議或建議無法解析時同樣"
        "必填（無基線不得以沉默宣稱一致）。相符時可省略，若仍提供則以備註寫入 Log。",
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    target = resolve_target(
        owner=args.owner, project=args.project, repo=args.repo, config=args.config
    )
    runner = default_runner
    project = resolve_project(runner, target.owner, target.project)
    fields = ensure_fields(runner, target.owner, target.project)

    items = list_items(runner, project)
    item = find_item_by_card_id(items, args.card_id)
    if not item:
        print(f"[assign] 找不到卡 {args.card_id}", file=sys.stderr)
        return 3

    try:
        mine = parse_block(item.body)
    except ResourceDeclarationError as exc:
        print(f"[assign] 拒絕：目標卡資源宣告解析失敗（{exc}），無法安全派工", file=sys.stderr)
        return 2

    # 規劃期路由的派工端閘門。刻意排在所有 set_field_value 之前：拒絕時必須零寫入，
    # 不能留下「owner 已改、Log 沒有偏離紀錄」的半套狀態。
    comparison = compare_capability_to_card(item.body, args.actual_capability)
    deviation_reason = (args.capability_deviation_reason or "").strip()
    if comparison.requires_reason and not deviation_reason:
        print(f"[assign] 拒絕：{comparison.refusal_message()}", file=sys.stderr)
        return 2

    conflicts: list[tuple[str, list[str]]] = []
    skipped_unparseable: list[str] = []
    for other in items:
        if other.item_id == item.item_id or not other.card_id:
            continue
        if (other.delivery_status or "") in TERMINAL_STATUSES:
            continue
        if not is_owner_assigned(other.owner_field):
            continue  # 尚未認領，無實際執行中的分支／worktree 可爭資源
        other_decl = try_parse_block(other.body)
        if other_decl is None:
            skipped_unparseable.append(other.card_id)
            continue
        overlap = find_conflicts(mine, other.card_id, other_decl)
        if overlap:
            conflicts.append((other.card_id, overlap))

    if skipped_unparseable:
        print(
            "[assign] 警告：以下活卡沒有可解析的資源宣告，交集檢查略過它們（不擋派工）："
            + "、".join(skipped_unparseable),
            file=sys.stderr,
        )

    if conflicts:
        print(f"[assign] 拒絕：{args.card_id} 的資源宣告與下列活卡衝突", file=sys.stderr)
        for cid, overlap in conflicts:
            print(f"  - {cid}：{', '.join(overlap)}", file=sys.stderr)
        return 4

    branch_worktree = format_branch_worktree(args.branch, args.worktree)
    set_field_value(runner, project, item.item_id, fields["owner"], args.assignee)
    set_field_value(runner, project, item.item_id, fields["分支worktree"], branch_worktree)
    set_field_value(runner, project, item.item_id, fields["交付狀態"], args.status)

    log_line = (
        f"{now_iso8601()} assign by wf-cli → owner {args.assignee}；"
        f"分支worktree {branch_worktree}；交付狀態 {args.status}；"
        f"{comparison.log_fragment(deviation_reason)}。"
    )
    new_body = append_log_line(item.body, log_line)
    set_item_body(runner, item.content_type, item.content_id, project, target.repo, item.issue_number, new_body)

    print(
        f"[assign] 已指派 {args.card_id} → {args.assignee}（{branch_worktree}）；"
        f"{comparison.log_fragment(deviation_reason)}"
    )
    return 0
