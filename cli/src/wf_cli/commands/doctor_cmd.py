"""``wfcli doctor``：對帳（git worktree list vs 卡註冊、submodule、孤兒分支、殘留 lease、
prunable worktree）。全程唯讀，見 doctor.py 模組說明；本指令不實作任何清理動作。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from ..doctor import (
    TRAILER_GUARD_EPOCH,
    audit_commit_trailers,
    audit_review_channel,
    run_doctor,
)
from ..gh import default_runner
from ..project import find_item_by_card_id, list_items, resolve_project
from ..registry import load_tasks_md_registry
from ..validation import ValidationError, validate_source_sha


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "doctor", help="對帳：worktree／submodule／孤兒分支／殘留 lease／prunable（唯讀）"
    )
    p.add_argument("repo_root", help="要檢查的 git repo 路徑（唯讀操作，不寫入）")
    p.add_argument(
        "--registry",
        choices=["tasks-md", "none"],
        default="tasks-md",
        help="卡註冊來源：tasks-md 讀 docs/TASKS.md（⚠️ 僅限尚未 cutover 的專案；本 repo 與 cpbl 都已 cutover，讀到的是封存於 2026-08-05 的凍結快照）；none 只做純 git 檢查",
    )
    p.add_argument(
        "--review-channel",
        action="store_true",
        help="另對帳指定 Issue 的外部查核收據與 wfcli review event（唯讀、fail-closed）",
    )
    p.add_argument(
        "--cleanup-preview",
        action="store_true",
        help="預覽 `📦已合併` 卡的破壞性收尾前提是否成立（唯讀；doctor 永不刪除任何東西）",
    )
    p.add_argument(
        "--commit-trailers",
        action="store_true",
        help="檢查 --commit-range 內每筆 commit 的 §6 來歷 trailer 完整性（唯讀；不阻擋任何 push）",
    )
    p.add_argument(
        "--legacy-authority-notes",
        action="store_true",
        help="掃描 Project 全部卡面，列出使用 #62 之前措辭的 amend 授權留痕（唯讀，"
        "需 --owner／--project）。報的是留痕強度不足，不是授權無效；既存事件不得改寫",
    )
    p.add_argument(
        "--commit-range",
        help="--commit-trailers 的 git rev range，例如 origin/main..HEAD。刻意不給預設："
        "`HEAD` 在 git log 語意下是整段歷史，猜錯範圍比要求明講糟得多",
    )
    p.add_argument(
        "--trailer-epoch",
        default=TRAILER_GUARD_EPOCH,
        help=f"分流界線（committer date，ISO8601）；早於此者列為界線前、不計違規。"
        f"預設 {TRAILER_GUARD_EPOCH}；傳 none 則全範圍一律判定",
    )
    p.add_argument(
        "--require-planned-by",
        action="store_true",
        help="把 Planned-by 缺席計入違規。⚠️ 卡的級別不在 commit 裡，本旗標是**呼叫端**"
        "宣告該範圍屬 T2 以上，不是檢查器導出的判準",
    )
    p.add_argument("--repo", help="--review-channel 的 GitHub repo，格式 owner/repo")
    p.add_argument("--issue-number", type=int, help="--review-channel 的 Issue/PR number")
    p.add_argument("--card-id", help="--review-channel 的卡 ID")
    p.add_argument("--owner", help="--review-channel 讀取 Project 交付狀態欄所需的 owner")
    p.add_argument("--project", type=int, help="--review-channel 讀取交付狀態欄所需的 Project number")
    p.add_argument("--source-sha", help="--review-channel 的完整 40 字元受審 SHA")
    p.add_argument("--main-ref", default="main", help="判斷「已併入」與 lease 交集比對用的主幹分支")
    p.add_argument("--lease-ttl-hours", type=float, default=48.0)
    p.add_argument("--json", action="store_true", help="stdout 只輸出 JSON（供腳本消費）；人類可讀報告改走 stderr")
    p.add_argument(
        "--strict",
        action="store_true",
        help="有孤兒 worktree／分支時回傳非 0 exit code（CI 用；預設不失敗，純報告）",
    )
    p.set_defaults(func=run)


def build_json_payload(report, review_channel_finding, commit_trailer_report=None) -> dict:
    """組出 ``--json`` 的輸出。

    先前只序列化 ``DoctorReport``，而 review-channel 的判定結果**不在其中**——
    停機（`marker_quarantined`）因此只出現在人類可讀的 stdout。本卡的目的正是讓
    停機可被機器偵測，而 #16 要消費 doctor 輸出做對帳；一個機器讀不到的狀態等於
    沒有對外提供。新增的是獨立鍵，既有消費者不受影響。

    `commit_trailers` 同理：#48 的 CI 要能機器判讀，不能只有人類可讀那份。
    """
    payload = asdict(report)
    payload["review_channel"] = (
        asdict(review_channel_finding) if review_channel_finding is not None else None
    )
    payload["commit_trailers"] = (
        asdict(commit_trailer_report) if commit_trailer_report is not None else None
    )
    return payload


def run(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root)
    if not repo_root.exists():
        print(f"[doctor] repo 路徑不存在：{repo_root}", file=sys.stderr)
        return 2

    # 參數驗證一律先於實際工作：旗標打錯時不該先跑完整套 doctor 掃描再報錯。
    if args.commit_trailers and not args.commit_range:
        print("[doctor] --commit-trailers 缺必要旗標：--commit-range", file=sys.stderr)
        return 2
    if args.legacy_authority_notes:
        missing = [
            flag for flag, value in (("--owner", args.owner), ("--project", args.project))
            if not value
        ]
        if missing:
            print(
                f"[doctor] --legacy-authority-notes 缺必要旗標：{', '.join(missing)}",
                file=sys.stderr,
            )
            return 2
    if args.review_channel:
        missing = [
            flag for flag, value in (
                ("--repo", args.repo),
                ("--issue-number", args.issue_number),
                ("--card-id", args.card_id),
                ("--source-sha", args.source_sha),
                # 契約 §3.1.3 的三面一致要求比對 Project 交付狀態欄。少了它只驗到
                # 兩面，而兩面一致的半寫入（留言成功、狀態欄失敗）看起來與正常裁決
                # 完全一樣——那正是本卡要消滅的 fail-open，因此列為必填而非選配。
                ("--owner", args.owner),
                ("--project", args.project),
            ) if not value
        ]
        if missing:
            print(f"[doctor] --review-channel 缺必要旗標：{', '.join(missing)}", file=sys.stderr)
            return 2
        # source_sha 沒驗格式的話，打錯的輸入會一路走到底並回報 `unobservable`——
        # 而那個狀態的語意是「該 source_sha 的查核在系統上不可觀測」。等於拿一個
        # 聽起來確定的結論回答一個根本沒被評估的問題，加上 --strict 還會讓 CI 紅在
        # 「沒人查核」而不是「你 SHA 打錯了」。handoff 與 review 都驗，doctor 沒驗。
        try:
            validate_source_sha(args.source_sha)
        except ValidationError as exc:
            for error in exc.errors:
                print(f"[doctor] {error}", file=sys.stderr)
            return 2

    # 卡面抓取：**先於** run_doctor，因為結果要當參數傳進去。
    #
    # 抓不到時刻意**不中止**、也不當成「掃過且乾淨」——留在 `not_scanned`，由報告
    # 明說「未掃描，這不等於沒有」。這條路在接線後仍然是對的行為（網路失敗、權限
    # 不足、Project 讀不到），只是不再是**唯一**會走到的路。
    legacy_bodies: dict[str, str] | None = None
    brief_values: dict[str, str | None] | None = None
    if args.legacy_authority_notes:
        try:
            proj = resolve_project(default_runner, args.owner, args.project)
            snapshots = list_items(default_runner, proj)
            legacy_bodies = {
                item.card_id: item.body
                for item in snapshots
                if item.card_id and item.body
            }
            # 簡介的**欄位那一半**（canonical §6.3 雙居所）。與 legacy_bodies 同一次
            # 讀取取得——⚠️ 分兩次讀會讓「body 與欄位」跨了時間，漂移偵測就分不出
            # 「真的漂移」與「兩次讀之間有人改過」。
            brief_values = {
                item.card_id: item.fields.get("簡介")
                for item in snapshots
                if item.card_id and item.body
            }
        except Exception as exc:  # noqa: BLE001 - 任何讀取失敗都退回「未掃描」
            print(
                f"[doctor] 取不到 Project 卡面（{type(exc).__name__}: {exc}）；"
                "舊措辭授權留痕一節維持「未掃描」——這不等於沒有",
                file=sys.stderr,
            )

    registry = load_tasks_md_registry(repo_root) if args.registry == "tasks-md" else None
    report = run_doctor(
        repo_root,
        registry,
        lease_ttl_hours=args.lease_ttl_hours,
        main_ref=args.main_ref,
        cleanup_preview=args.cleanup_preview,
        legacy_authority_card_bodies=legacy_bodies,
        brief_field_values=brief_values,
    )
    # --json 時人類可讀報告改走 stderr：先前兩者都印到 stdout，整體輸出不是合法
    # JSON（`| jq .` 直接 parse error），機器消費端因此拿不到 review_channel。
    print(report.render_text(), file=sys.stderr if args.json else sys.stdout)
    review_channel_finding = None
    if args.review_channel:
        issue = default_runner.run_json(["api", f"repos/{args.repo}/issues/{args.issue_number}"])
        comments = default_runner.run_json(
            ["api", f"repos/{args.repo}/issues/{args.issue_number}/comments", "--paginate"]
        )
        # Issue number 不必然也是 PR number；只有 GitHub 明示 pull_request 才讀 review body，
        # 避免對純 Issue 送 /pulls/{n}/reviews 而把唯讀 doctor 誤變成 404。
        reviews = []
        if isinstance(issue, dict) and issue.get("pull_request") is not None:
            reviews = default_runner.run_json(
                ["api", f"repos/{args.repo}/pulls/{args.issue_number}/reviews", "--paginate"]
            )
        # 第三面：Project 交付狀態欄。讀不到就傳 None，audit_review_channel 會據此
        # 回報 half_written 而非宣稱 recorded——讀取失敗不得被當成一致。
        delivery_status = None
        try:
            proj = resolve_project(default_runner, args.owner, args.project)
            item = find_item_by_card_id(list_items(default_runner, proj), args.card_id)
            delivery_status = item.delivery_status if item else None
        except Exception as exc:  # noqa: BLE001 - 讀不到第三面是 finding，不是當機
            print(f"[doctor] 讀取 Project 交付狀態失敗（{type(exc).__name__}: {exc}）；"
                  "第三面將標記為未驗證", file=sys.stderr)
        finding = audit_review_channel(
            comments or [],
            args.card_id,
            args.source_sha,
            card_body=str((issue or {}).get("body") or ""),
            reviews=reviews or [],
            delivery_status=delivery_status,
        )
        review_channel_finding = finding
        out = sys.stderr if args.json else sys.stdout
        # 編號改 6：報告本體（render_text）新增了「## 5. 收尾清理前提」，此處若仍是 5
        # 會出現兩個同號章節。整份報告的章節編號由 render_text 的順序決定。
        print("\n## 6. 跨工具查核寫入通道", file=out)
        print(f"- [{finding.status}] {finding.detail}", file=out)
        for url, author in zip(finding.receipt_urls, finding.receipt_authors, strict=True):
            print(f"  - receipt: {url}（GitHub author: {author}）", file=out)
        if finding.status == "half_written":
            print(f"  - 交付狀態：預期 {finding.expected_delivery_status!r}／"
                  f"實際 {finding.actual_delivery_status!r}", file=out)
        for reason in finding.quarantine_reasons:
            # 停機的價值在於「要人去修哪一則留言」。只印狀態不印原因，使用者只知道
            # 卡住了卻不知道卡在哪，那和沒偵測到差不多。
            print(f"  - 停機原因: {reason}", file=out)
    commit_trailer_report = None
    if args.commit_trailers:
        epoch = None if str(args.trailer_epoch).lower() == "none" else args.trailer_epoch
        commit_trailer_report = audit_commit_trailers(
            repo_root,
            args.commit_range,
            epoch=epoch,
            require_planned_by=args.require_planned_by,
        )
        print(
            "\n" + commit_trailer_report.render_text(),
            file=sys.stderr if args.json else sys.stdout,
        )

    if args.json:
        print(json.dumps(build_json_payload(report, review_channel_finding, commit_trailer_report),
                         ensure_ascii=False, indent=2, default=str))

    # ⚠️ 舊措辭授權留痕**刻意不列入 --strict**。那些事件是 append-only 且明令
    # 不得追溯改寫，所以它們永遠不會消失——把它們算進 exit code，等於讓 CI 從此
    # 恆紅且無人能修好。那是「偵測器調成永遠會響」，與「永遠不會響」同樣沒用。
    # 它的用途是讓讀者知道那些授權欄該怎麼讀，不是閘門。
    if args.strict and (
        report.orphan_worktrees()
        or report.orphan_branches
        or (review_channel_finding is not None and review_channel_finding.status != "recorded")
        or (commit_trailer_report is not None and commit_trailer_report.violations)
    ):
        return 1
    return 0
