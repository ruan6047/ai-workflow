"""``wfcli amend``：開卡後修訂卡面欄位（唯一寫入通道補上缺的那一塊）。

痛點：`open` 之後卡面就凍住了。spec 基線隨上游卡 merge 而變、驗收條件被需求方追加、
tier 開卡時填錯——這些都是常態，但 CLI 沒有入口，於是每次更正都改用 `gh issue edit`
或 Project GraphQL mutation 直接寫，繞過唯一寫入通道。2026-08-10 一天之內就繞了四次
（ai-workflow#15 的 tier、#17 的 spec 基線與 Log 渲染修復），這不是紀律問題，是工具缺口。

範圍界定（#19 驗收第 4 條）：本指令**同時**涵蓋 body 欄位與 Project 的 `級別` 欄位，
`WF-CLI-TIER-MUTATION1`（ai-workflow#12）因此併入本卡，不另行實作。

四條紅線：

- **原值必留且不得截斷**：每個被改欄位 append 一行 Log，完整記下原值與理由。Log 是
  唯一還原點，摘要不能取代全文（R1-01）；主控台輸出才做可讀性截斷。
- **不動 Log**：修訂只作用於 `## Log` 之前。排版壞到無法安全定位 Log 時拒絕，但另提供
  `--repair-log-layout` 這條窄路，否則工具在最需要它的情境反而不能用（R1-02）。
- **半寫入可偵測且可自癒**：`級別` 先寫並讀回驗證，再寫 body。若 body 寫入失敗導致
  欄位已改卻沒有 Log，下一次同樣的 amend 會偵測到「欄位已是目標值但 Log 沒記」，
  並只補寫 Log（R1-03）。每次執行帶 `op` 識別碼，便於跨 Log 條目對齊同一次操作。
- **完成證據不隱式沿用**：清單整份替換預設重設為未勾選；要沿用須顯式 `--preserve-checked`（R1-04）。

退出碼：0 成功／2 參數或內容檢查失敗（未寫入）／3 找不到卡／5 寫入後讀回驗證不符。
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import uuid

from ..card import (
    TIERS,
    AmendError,
    amend_acceptance,
    amend_resource_block,
    amend_spec_baseline,
    amend_verification,
    append_log_line,
    now_iso8601,
    repair_body_layout,
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
        help="可重複；給定時整份取代驗收條件（預設全部重設為未勾選）",
    )
    p.add_argument(
        "--verification",
        action="append",
        default=None,
        help="可重複；給定時整份取代驗證項目（預設全部重設為未勾選）",
    )
    p.add_argument(
        "--preserve-checked",
        action="store_true",
        help="清單替換時，文字未變的項目沿用原勾選狀態。預設不沿用："
        "整份替換代表驗收語意已變動，文字相同不保證仍然成立",
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
        "--record-unlogged-change",
        action="store_true",
        help="半寫入補救：Project 級別欄已是 --tier 指定值但 Log 無對應紀錄時，"
        "只補寫 Log、不改欄位。CLI 分不出「開卡時就是這個值」與「先前半寫入」，"
        "故此判斷由操作者顯式承擔",
    )
    p.add_argument(
        "--repair-log-layout",
        action="store_true",
        help="窄路修復模式：把 body 內的字面 \\n 還原成真換行。只准動空白，"
        "不得與其他修訂旗標併用，且必須同時給 --expect-body-sha256",
    )
    p.add_argument(
        "--expect-body-sha256",
        default=None,
        help="現行 body 原文的 UTF-8 SHA-256；--repair-log-layout 必填，"
        "確保操作者確實看過將被改寫的內容",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="只驗證與列印將寫入的變更，不連 GitHub 寫入任何狀態",
    )
    p.set_defaults(func=run)


def _fold(text: str) -> str:
    """Log 是單行條目，原值摺成一行——但**不截斷**：Log 是唯一還原點。"""
    return " ".join(str(text).split())


def _short(text: str, limit: int = 100) -> str:
    """只給主控台看的可讀摘要；永遠不進 Log。"""
    folded = _fold(text)
    return folded if len(folded) <= limit else folded[:limit] + f"…（全文 {len(folded)} 字，見 Log）"


def _tier_change_logged(body: str, tier: str) -> bool:
    """body 的 Log 是否已記過「級別 → tier」這筆變更。

    逐行比對且不綁定完整格式：Log 行含 op 識別碼，欄位名又有「級別」與
    「級別（補記先前未留痕的變更）」兩種寫法。綁死字面格式會讓偵測器認不出
    自己寫的紀錄，把真正的 no-op 誤判成半寫入而重複「自癒」。
    """
    needle = f"→ 新值「{tier}」"
    return any(
        "amend by wf-cli" in line and "→ 級別" in line and needle in line
        for line in body.splitlines()
    )


def run(args: argparse.Namespace) -> int:  # noqa: C901 - 逐旗標的前置檢查本就是平鋪的
    if not args.reason.strip():
        print("[amend] 拒絕：--reason 不得為空（每次修訂都要能回答為什麼）", file=sys.stderr)
        return 2

    wants_resources = args.db_scope is not None or args.resources is not None
    field_flags = [args.spec_baseline, args.acceptance, args.verification, args.tier]
    wants_fields = any(f is not None for f in field_flags) or wants_resources

    if args.repair_log_layout:
        if wants_fields:
            print(
                "[amend] 拒絕：--repair-log-layout 是窄路修復模式，不得與其他修訂旗標併用"
                "（修排版與改內容混在一起就無法逐項稽核）",
                file=sys.stderr,
            )
            return 2
        if not args.expect_body_sha256:
            print(
                "[amend] 拒絕：--repair-log-layout 必須同時給 --expect-body-sha256"
                "（確保你確實看過將被改寫的 body）",
                file=sys.stderr,
            )
            return 2
    elif not wants_fields:
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

    op_id = uuid.uuid4().hex[:8]
    body = item.body
    changes: list[tuple[str, str, str]] = []  # (欄位, 原值, 新值)
    tier_needs_field_write = False

    if args.repair_log_layout:
        actual = hashlib.sha256(item.body.encode("utf-8")).hexdigest()
        if actual != args.expect_body_sha256.strip().lower():
            print(
                f"[amend] 拒絕：--expect-body-sha256 與現行 body 不符\n"
                f"  預期 {args.expect_body_sha256}\n  實際 {actual}",
                file=sys.stderr,
            )
            return 2
        try:
            body, original = repair_body_layout(item.body)
        except AmendError as exc:
            print(f"[amend] 拒收（未寫入任何狀態）：{exc}", file=sys.stderr)
            return 2
        changes.append(
            ("body 排版修復", f"原 body SHA-256 {actual}", "字面 \\n 已還原為真換行，非空白內容未變")
        )
        del original
    else:
        try:
            if args.spec_baseline is not None:
                body, old = amend_spec_baseline(body, args.spec_baseline)
                changes.append(("spec 基線", old, args.spec_baseline))
            if args.acceptance is not None:
                body, old = amend_acceptance(
                    body, args.acceptance, preserve_checked=args.preserve_checked
                )
                changes.append(("驗收條件", old, "；".join(args.acceptance)))
            if args.verification is not None:
                body, old = amend_verification(
                    body, args.verification, preserve_checked=args.preserve_checked
                )
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
            already_logged = _tier_change_logged(item.body, args.tier)
            if old_tier == args.tier and not args.record_unlogged_change:
                # 「欄位已是目標值且 Log 沒記」有兩種可能：開卡時就是這個值（正常
                # no-op），或先前 amend 寫完欄位後 body 寫入失敗（半寫入）。CLI 分不
                # 出來，也不該猜——猜錯就會把正常的 no-op 記成一筆不存在的變更。
                # 因此預設拒絕，並在確實可能是半寫入時提示補記旗標，由操作者承擔判斷。
                hint = (
                    ""
                    if already_logged
                    else "；若這是先前 amend 寫完欄位卻 body 寫入失敗所致，"
                    "請加 --record-unlogged-change 補記留痕"
                )
                print(
                    f"[amend] 拒收（未寫入任何狀態）：級別已是 {args.tier}"
                    f"，拒絕寫入不實的修訂留痕{hint}",
                    file=sys.stderr,
                )
                return 2
            if args.record_unlogged_change:
                if old_tier != args.tier:
                    print(
                        f"[amend] 拒絕：--record-unlogged-change 只補留痕、不改欄位，"
                        f"但級別現為 {old_tier!r} 而非 {args.tier}；請改用一般 --tier",
                        file=sys.stderr,
                    )
                    return 2
                if already_logged:
                    print(
                        f"[amend] 拒絕：級別 {args.tier} 的變更 Log 已存在，無需補記",
                        file=sys.stderr,
                    )
                    return 2
                changes.append(
                    (
                        "級別（補記先前未留痕的變更）",
                        "（Project 欄位已是目標值但 Log 無紀錄；操作者判定為先前半寫入）",
                        args.tier,
                    )
                )
            else:
                tier_needs_field_write = True
                changes.append(("級別", old_tier or "（未設定）", args.tier))

    timestamp = now_iso8601()
    for field_name, old, new in changes:
        body = append_log_line(
            body,
            f"{timestamp} amend by wf-cli（op {op_id}）→ {field_name}："
            f"原值「{_fold(old)}」→ 新值「{_fold(new)}」；理由 {_fold(args.reason)}。",
        )

    if args.dry_run:
        print(f"[amend] dry-run（未寫入任何狀態）：{args.card_id} 將修訂 {len(changes)} 個欄位")
        for field_name, old, new in changes:
            print(f"  - {field_name}：「{_short(old)}」→「{_short(new)}」")
        return 0

    # 級別先寫並讀回驗證，body 後寫。這個順序讓「欄位寫失敗」變成乾淨中止
    # （body 未動、無半寫入）；而「欄位成功、body 失敗」留下的不一致，由下一次
    # 同樣的 amend 依 _tier_change_logged 偵測並只補寫 Log 自癒。
    if tier_needs_field_write:
        set_field_value(runner, project, item.item_id, fields["級別"], args.tier)
        after = find_item_by_card_id(list_items(runner, project), args.card_id)
        actual_tier = after.text("級別") if after else None
        if actual_tier != args.tier:
            print(
                f"[amend] 寫入後讀回驗證失敗：級別預期 {args.tier}，實際 {actual_tier!r}；"
                "body 未寫入，請排除後重試（重試會偵測並補齊留痕）",
                file=sys.stderr,
            )
            return 5

    set_item_body(
        runner, item.content_type, item.content_id, project, target.repo, item.issue_number, body
    )

    print(f"[amend] 已修訂 {args.card_id}（op {op_id}，{len(changes)} 個欄位，原值已完整寫入 Log）")
    for field_name, old, new in changes:
        print(f"  - {field_name}：「{_short(old, 80)}」→「{_short(new, 80)}」")
    return 0
