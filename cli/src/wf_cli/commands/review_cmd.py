"""``wfcli review``：查核裁決落地（結構化輸出驗證＋Issue 留言＋交付狀態轉換）。

痛點：查核輸出契約（`self_run` 必填、無 `self_run` 的 `APPROVE` 無效）原本只有紙面
規則，寫入通道擋不住——只能靠人工核對。本指令把 canonical §5.1／§5.2 與
``templates/review-prompt.md`` §5 變成寫入前的機械閘門。

**驗證全部在任何遠端呼叫之前**：不合格式一律 fail closed，不寫任何遠端狀態
（連讀 project 都不做，除了 ``--validate-only`` 本來就不碰網路）。

退出碼：

- ``0`` 通過並已寫入（或 ``--validate-only`` 驗證通過）
- ``2`` 讀不到／解析失敗／契約檢查失敗／缺必要旗標（未寫入任何遠端狀態）
- ``3`` 找不到卡
- ``4`` ``review-invalid``（templates/review-escalation.md §1）：目前可機械判定的是
  「`APPROVE` 未附 `self_run`」。§1 表列此情形**留在 `🔍待查核`、不計 iteration**，
  所以這裡刻意不寫任何狀態——維持現狀就是契約要求的結果。

結論與 findings 的語意一致性（需求方 2026-08-06 裁決，ruan6047/ai-workflow#8，
由警示升為硬拒，走 exit 2）：`APPROVE` 不得含 `blocking: true` 的 finding；
`REQUEST_CHANGES` 不得零 finding。判準實作在 ``validation.validate_review_report``。

與 handoff 的分工（勿重複發明）：

- **iteration 由 handoff 獨占**。``handoff --next-stage implementation`` 承載「查核
  退回」語意並讀回現值＋1（WF-22-CLI2，需求方 2026-08-05 拍板）。review 若也動
  iteration，一次退回會被記成兩次。REQUEST_CHANGES 後仍須走 handoff 把卡交回執行者，
  遞增在那裡發生。
- **最後交接由 handoff 獨占**：裁決不是交接，owner 也不在本指令改。
- review 只寫兩件事：Issue 留言（裁決全文，canonical §4.3「事件＝Issue timeline ＋
  結構化 comment」）＋交付狀態（``✅通過``／``↩退回``，review-escalation.md §1）；
  另在 body 的 ``## Log`` 補一行索引，與 assign／handoff 的留痕慣例一致。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..card import append_log_line, now_iso8601
from ..config import add_target_args, resolve_target
from ..gh import default_runner
from ..project import (
    add_issue_comment,
    ensure_fields,
    find_item_by_card_id,
    list_items,
    resolve_project,
    set_field_value,
    set_item_body,
)
from ..review import (
    ReviewParseError,
    attempt_id,
    parse_structured_block,
    render_verdict_comment,
)
from ..validation import (
    ValidationError,
    review_invalid_reasons,
    validate_review_report,
    validate_source_sha,
)

AWAITING_REVIEW_STATUS = "🔍待查核"


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "review", help="查核裁決：驗證結構化輸出→Issue 留言＋交付狀態轉換"
    )
    add_target_args(p)
    p.add_argument("card_id")
    p.add_argument(
        "--input",
        default=None,
        help="查核報告檔路徑（templates/review-prompt.md §5 的結構化區塊）；"
        "未給或給 - 時從 stdin 讀",
    )
    p.add_argument(
        "--source-sha",
        required=True,
        help="被審的完整 40 字元 hex SHA（與 handoff 指定的 source_sha 相同）",
    )
    p.add_argument(
        "--reviewer",
        required=True,
        help="查核者（帳號／模型@工具）；紅線卡須跨模型家族或人工，見 canonical §5",
    )
    p.add_argument(
        "--escalation-epoch",
        type=int,
        default=0,
        help="attempt_id 的 epoch（review-escalation.md §5，預設 0）；"
        "epoch 遞增須另有 escalation-epoch-change 授權，本指令不代為切換",
    )
    p.add_argument(
        "--validate-only",
        action="store_true",
        help="只驗證查核輸出格式，不連 GitHub、不寫任何狀態（查核者送審前自檢用）",
    )
    p.set_defaults(func=run)


def _read_input(path: str | None) -> str:
    if path and path != "-":
        file_path = Path(path)
        if not file_path.exists():
            raise ReviewParseError(f"--input 檔案不存在：{file_path}")
        return file_path.read_text(encoding="utf-8")
    if sys.stdin.isatty():
        raise ReviewParseError(
            "沒有 --input 也沒有 stdin 輸入：請用 --input <檔案> 或把查核報告導入 stdin"
        )
    return sys.stdin.read()


def run(args: argparse.Namespace) -> int:
    try:
        validate_source_sha(args.source_sha)
    except ValidationError as exc:
        for error in exc.errors:
            print(f"[review] {error}", file=sys.stderr)
        return 2

    if not args.reviewer.strip():
        print("[review] 拒絕：--reviewer 不得為空（裁決必須可歸屬到查核者）", file=sys.stderr)
        return 2
    if args.escalation_epoch < 0:
        print(
            f"[review] 拒絕：--escalation-epoch 不得為負（收到 {args.escalation_epoch}）；"
            "epoch 只能由 escalation-epoch-change 逐一遞增（review-escalation.md §4）",
            file=sys.stderr,
        )
        return 2

    try:
        raw_text = _read_input(args.input)
        data = parse_structured_block(raw_text)
    except ReviewParseError as exc:
        print(f"[review] 拒收：{exc}", file=sys.stderr)
        return 2

    # review-invalid 先判：它在 §1 是獨立層次（不計 iteration、不建立 attempt），
    # 與「格式不合」的處置不同，必須能被呼叫端用退出碼分辨。
    invalid = review_invalid_reasons(data)
    if invalid:
        print("[review] 拒收（review-invalid，不計 iteration、卡片狀態不變）：", file=sys.stderr)
        for reason in invalid:
            print(f"  - {reason}", file=sys.stderr)
        return 4

    try:
        report = validate_review_report(data)
    except ValidationError as exc:
        print("[review] 拒收：查核輸出不符契約（未寫入任何遠端狀態）", file=sys.stderr)
        for error in exc.errors:
            print(f"  - {error}", file=sys.stderr)
        return 2

    if report.writer_only_keys:
        print(
            "[review] 警示：查核輸出含 "
            + "、".join(report.writer_only_keys)
            + " 等 writer-only 欄位；依 review-escalation.md §2／§5 由 lifecycle writer "
            "依可重現證據標記，reviewer 不得自行決定，本次一律忽略其值。",
            file=sys.stderr,
        )
    if args.validate_only:
        print(
            f"[review] 驗證通過（--validate-only，未寫入任何狀態）："
            f"{report.review_result}／core_pain_resolved={report.core_pain_resolved}／"
            f"self_run {len(report.self_run)} 項／findings {len(report.findings)} 項"
        )
        return 0

    target = resolve_target(
        owner=args.owner, project=args.project, repo=args.repo, config=args.config
    )
    if not target.repo:
        # 裁決留言必須落在真實 Issue timeline（canonical §4.3）；沒有 repo 就沒有
        # 可留言的對象，寧可不寫也不要只翻板狀態、留下沒有裁決全文的「已通過」。
        print(
            "[review] 拒絕：裁決留言需要真實 repo Issue，請給 --repo owner/repo"
            "（或設定檔 repo／環境變數 WFCLI_REPO）",
            file=sys.stderr,
        )
        return 2

    runner = default_runner
    project = resolve_project(runner, target.owner, target.project)
    fields = ensure_fields(runner, target.owner, target.project)

    items = list_items(runner, project)
    item = find_item_by_card_id(items, args.card_id)
    if not item:
        print(f"[review] 找不到卡 {args.card_id}", file=sys.stderr)
        return 3
    if item.content_type != "Issue" or item.issue_number is None:
        print(
            f"[review] 拒絕：卡 {args.card_id} 是 Project draft item，沒有可留言的 Issue timeline；"
            "請先以真實 repo Issue 承載此卡（canonical §4.3：卡狀態＝Issue）",
            file=sys.stderr,
        )
        return 2

    current_status = item.delivery_status
    if current_status != AWAITING_REVIEW_STATUS:
        # 不硬擋：review-escalation.md §1 只定義了 review 的結果與狀態，沒有規定
        # 「非 🔍待查核 不得下裁決」（補記舊裁決、⏸阻塞 期間收到報告都是實務情境）。
        # 是否升級為硬拒屬新裁量，留給需求方。
        print(
            f"[review] 警示：卡 {args.card_id} 目前交付狀態為 {current_status!r}，"
            f"非 {AWAITING_REVIEW_STATUS}；本次仍照寫，請確認查核順序無誤。",
            file=sys.stderr,
        )

    timestamp = now_iso8601()
    comment = render_verdict_comment(
        card_id=args.card_id,
        report=report,
        source_sha=args.source_sha,
        reviewer=args.reviewer,
        escalation_epoch=args.escalation_epoch,
        timestamp=timestamp,
    )
    # 先留言、後翻狀態：反過來若留言失敗，板上會出現沒有裁決全文的 ✅通過，
    # 那正是本卡要消滅的「宣稱與證據脫節」。
    add_issue_comment(runner, target.repo, item.issue_number, comment)
    set_field_value(runner, project, item.item_id, fields["交付狀態"], report.delivery_status)

    log_line = (
        f"{timestamp} review by wf-cli → {report.review_result}"
        f"（{report.delivery_status}）；查核者 {args.reviewer}；"
        f"core_pain_resolved {report.core_pain_resolved}；"
        f"self_run {len(report.self_run)} 項；findings {len(report.findings)} 項"
        f"（blocking {len(report.blocking_findings)}）；"
        f"attempt {attempt_id(args.card_id, args.escalation_epoch, args.source_sha)}。"
    )
    new_body = append_log_line(item.body, log_line)
    set_item_body(
        runner, item.content_type, item.content_id, project, target.repo, item.issue_number, new_body
    )

    print(
        f"[review] 已寫入裁決 {args.card_id} → {report.review_result}"
        f"（交付狀態={report.delivery_status}，留言於 #{item.issue_number}）"
    )
    if report.review_result == "REQUEST_CHANGES":
        print(
            "[review] iteration 不由本指令遞增：請以 "
            "`wfcli handoff --next-stage implementation` 把卡交回執行者，"
            "遞增在該處發生（WF-22-CLI2 既有規則）"
        )
    return 0
