"""``wfcli checkpoint`` 與 ``wfcli contract-baseline``：escalation 帳的兩個事件 writer。

痛點：``review-escalation.md`` §4／§5 的 ``escalation-checkpoint`` 在本 repo 從來沒有
授權寫入通道——PM 只能手寫留言，七則全部不合契約（缺三個必填欄、多出四個未定義鍵）。
沒有 writer，``deferred_findings`` 整個機制也上不了線（§4 末段已明記這是本卡的缺口）。

## 兩個指令在同一個檔案

本卡宣告的寫入集只有 ``commands/checkpoint_cmd.py`` 一個新檔（Issue #9 body 的
``resource-claims``）。``contract-baseline`` 是 §5 的 one-shot cutover marker，與
checkpoint 是**不同的事件型別**（各自獨立的留言，不共用留痕），但把它另開一個
``contract_baseline_cmd.py`` 會擴張宣告的寫入集，而本卡的宣告已因與 #30 相交被收窄過
一次。契約要求的是「不得附在 review 等其他事件上」——那是**留言層**的分離，不是 CLI
檔案層的分離；兩個 parser 共用一個模組不違反它。待宣告界線允許時可拆檔。

## 事件的承載方式：fenced 區塊 ＋ Log 索引行，不發 marker

需求方 2026-08-12 裁定採方案 (B)。理由與被否決的兩案見 ``review.py`` 中
「escalation 帳的結構化事實」段的模組註。

定位機制做到無歧義：``gh.GhRunner.execute`` 會回傳 stdout，而 ``gh issue comment`` 的
stdout **就是新留言的 URL**；本模組直接呼叫 runner 取回該 URL 並逐字寫進 Log 行。
（``project.add_issue_comment`` 目前把它丟掉，而 ``project.py`` 不在本卡寫入集內，
故此處自行呼叫；把回傳值折回 ``project.py`` 屬後續卡。）

## 本指令**不**做的事（切片 B，被 #30 擋住）

``unique_attempt_count`` 與 ``checkpoint_decision`` 由操作者提供並留痕，**不由事件流
機械推導**。§4／§5 的兩個條件需要跨 attempt 的 carry set 與根因 occurrence 推導，而
§1／§2 明定留痕解析停機是**解析層 gate 且優先於語意層**：讀不出 marker 就談不上算帳。
``docs/CONSUMER_CONFORMANCE.md`` 落差 7 記錄該停機在本 repo 無解除路徑，實測 #15／#17／
#21 三張裁決完整的卡全部因派審留言引用 marker 前綴而 ``marker_quarantined``。嚴格實作的
歷史推導對今天多數真實卡**應該拒絕動作**，而解除路徑不存在。故本指令只做：

- 契約欄位的形狀檢查（§5 必填、列舉、``unique_attempt_count >= 3``）；
- **trigger attempt 的裁決確已落地**（§4「checkpoint 的評估時點」）——這一條是機械的：
  掃 timeline 找該 attempt 的合格 marker，並要求 Issue body ``## Log`` 有同行索引；
- 未定義鍵與 ``deferred_findings`` 的 fail-closed 拒收。

「條件成立時 ``checkpoint_decision`` 只能是 ``escalate``」（§4 末段）**沒有機械執行者**，
本指令不假裝有：它是**約定**，由操作者在 ``--rationale`` 裡自證。

退出碼：``0`` 已寫入；``2`` 欄位不合契約／前置不成立（未寫入）；``3`` 找不到卡。
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Any

from ..card import append_log_line, now_iso8601
from ..config import add_target_args, resolve_target
from ..gh import default_runner
from ..project import (
    find_item_by_card_id,
    list_items,
    resolve_project,
    set_item_body,
)
from ..review import (
    BASELINE_LOG_TAG,
    CHECKPOINT_DECISIONS,
    CHECKPOINT_LOG_TAG,
    log_line_indexes,
    render_checkpoint_comment,
    render_contract_baseline_comment,
)
from ..validation import (
    ValidationError,
    build_issue_event_history,
    validate_checkpoint_input,
)
from .review_cmd import fetch_issue_comments, resolve_platform_login


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "checkpoint",
        help="escalation-checkpoint 事件：第三個及其後每個可計數 attempt 出現時必建",
    )
    add_target_args(p)
    p.add_argument("card_id")
    p.add_argument(
        "--trigger-attempt-id",
        required=True,
        help="觸發本 checkpoint 的可計數 attempt（其 review 裁決須已落地；review-escalation.md §5）",
    )
    p.add_argument(
        "--unique-attempt-count",
        type=int,
        required=True,
        help="本 epoch 去重後的可計數 attempt 數（>= 3）",
    )
    p.add_argument("--decision", required=True, choices=list(CHECKPOINT_DECISIONS))
    p.add_argument(
        "--rationale",
        required=True,
        help="checkpoint_rationale：根因重複、閉環趨勢或需求方裁定（可多行）",
    )
    p.add_argument("--escalation-epoch", type=int, default=0)
    p.add_argument(
        "--escalation-resolution",
        default=None,
        help="（保留旗標，一律拒收）§5 未定義此鍵；契約缺口另開卡承接，見拒收訊息",
    )
    p.add_argument(
        "--defer-finding",
        action="append",
        default=[],
        metavar="FINDING_ID",
        help="（保留旗標，一律拒收）deferred_findings 的兩個 cause 在本 repo 皆不可用",
    )
    p.set_defaults(func=run_checkpoint)

    b = subparsers.add_parser(
        "contract-baseline",
        help="contract-baseline one-shot cutover 事件（review-escalation.md §5）",
    )
    add_target_args(b)
    b.add_argument("card_id")
    b.add_argument("--rationale", required=True, help="為何在此刻切 baseline")
    b.set_defaults(func=run_contract_baseline)


@dataclass(frozen=True)
class _Loaded:
    """``_load_item`` 的結果：要嘛 ``exit_code`` 有值（已印好理由），要嘛其餘欄位有值。"""

    exit_code: int | None = None
    runner: Any = None
    target: Any = None
    project: Any = None
    item: Any = None


def _load_item(args: argparse.Namespace, tag: str) -> _Loaded:
    """共用前置：解析目標、取卡、擋掉沒有 timeline 的 draft item。"""
    target = resolve_target(
        owner=args.owner, project=args.project, repo=args.repo, config=args.config
    )
    if not target.repo:
        print(
            f"[{tag}] 拒絕：事件留言需要真實 repo Issue，請給 --repo owner/repo",
            file=sys.stderr,
        )
        return _Loaded(exit_code=2)

    runner = default_runner
    project = resolve_project(runner, target.owner, target.project)
    item = find_item_by_card_id(list_items(runner, project), args.card_id)
    if not item:
        print(f"[{tag}] 找不到卡 {args.card_id}", file=sys.stderr)
        return _Loaded(exit_code=3)
    if item.content_type != "Issue" or item.issue_number is None:
        print(
            f"[{tag}] 拒絕：卡 {args.card_id} 是 Project draft item，沒有可留言的 Issue timeline",
            file=sys.stderr,
        )
        return _Loaded(exit_code=2)
    return _Loaded(runner=runner, target=target, project=project, item=item)


def _post_event(runner, repo: str, issue_number: int, body: str) -> str:
    """發事件留言並回傳其 URL（``gh issue comment`` 的 stdout 即新留言 URL）。"""
    return runner.execute(
        ["issue", "comment", str(issue_number), "--repo", repo, "--body", body]
    ).strip().splitlines()[-1].strip()


def run_checkpoint(args: argparse.Namespace) -> int:
    try:
        validate_checkpoint_input(
            card_id=args.card_id,
            escalation_epoch=args.escalation_epoch,
            trigger_attempt_id=args.trigger_attempt_id,
            unique_attempt_count=args.unique_attempt_count,
            checkpoint_decision=args.decision,
            checkpoint_rationale=args.rationale,
            escalation_resolution=args.escalation_resolution,
            deferred_findings=args.defer_finding,
        )
    except ValidationError as exc:
        print(
            "[checkpoint] 拒收：不符 review-escalation.md §5（未寫入任何遠端狀態）\n"
            "  ⇒ 改正下列欄位後重跑同一條指令。旗標與值域：\n"
            "    wfcli checkpoint --help\n"
            "  ⇒ 條文原文（本 repo 內，⛔ 不必連網）：\n"
            "    git show HEAD:stage-rules/review.md",
            file=sys.stderr,
        )
        for error in exc.errors:
            print(f"  - {error}", file=sys.stderr)
        return 2

    loaded = _load_item(args, "checkpoint")
    if loaded.exit_code is not None:
        return loaded.exit_code
    runner, target, item = loaded.runner, loaded.target, loaded.item

    history = build_issue_event_history(
        fetch_issue_comments(runner, target.repo, item.issue_number)
    )
    # §4「checkpoint 的評估時點」：trigger attempt 的裁決必須**已記錄**，否則第二條件
    # 因「下一輪尚未表態」而恆真，continue／replan／change-executor 三個分支永遠不可達。
    # 判準與 handoff-contract.md §3.1.3 同形：留言的合格 marker ＋ Log 的同行索引兩面。
    if args.trigger_attempt_id not in history.all_attempt_ids or not log_line_indexes(
        item.body, "review by wf-cli", args.trigger_attempt_id
    ):
        print(
            f"[checkpoint] 拒絕：找不到 attempt {args.trigger_attempt_id} 已落地的 review 裁決"
            "（判準為兩面一致：timeline 上的合格 marker ＋ Issue body ## Log 的同行索引）。"
            "review-escalation.md §4：trigger attempt 必須是已記錄且已判定 counts_toward_escalation"
            "=true 的 attempt；在其裁決落地前建 checkpoint 會讓第二條件恆真而失去鑑別力。\n"
            "  ⇒ 先看這張卡的 review 留痕實際有哪些 attempt（已代入實際值）。\n"
            "  ⚠️ **`--comments` 不可省**：attempt id 寫在**留言**裡，⛔ 不在 body ——\n"
            "     少了它 `attempt_id` 的命中數是 0（2026-09-03 實測）。\n"
            f"    gh issue view {item.issue_number} --repo {target.repo} --comments\n"
            f"    gh issue view {item.issue_number} --repo {target.repo} "
            "--json body --jq .body | grep 'review by wf-cli'",
            file=sys.stderr,
        )
        return 2
    for existing in history.checkpoints:
        if (
            existing.trigger_attempt_id == args.trigger_attempt_id
            and existing.escalation_epoch == args.escalation_epoch
        ):
            print(
                f"[checkpoint] 拒絕：attempt {args.trigger_attempt_id} 已有 checkpoint"
                f"（decision={existing.checkpoint_decision}）。一個可計數 attempt 一則 checkpoint；"
                "要改變裁定請追加事件，不得重寫（append-only，review-escalation.md §5）。\n"
                "  ⇒ 先看既有那一則寫了什麼（已代入實際值）：\n"
                f"    gh issue view {item.issue_number} --repo {target.repo} --comments\n"
                "  ⇒ 旗標與值域（可整行複製，⛔ 無需填任何欄位）：\n"
                "    wfcli checkpoint --help\n"
                f"  ⇒ 要改變裁定時用**新的** --escalation-epoch ＝ {args.escalation_epoch + 1} "
                f"重跑（--trigger-attempt-id {args.trigger_attempt_id}、--unique-attempt-count "
                f"{args.unique_attempt_count}、--decision {args.decision} 照舊），"
                "並自己寫 --rationale ＝ 改判理由。⛔ 不要重寫舊的那一則。\n"
                "  ⚠️ ⛔ 刻意**不給可照貼的重跑指令**：改判理由是你的判斷，填空樣板只會被照貼。",
                file=sys.stderr,
            )
            return 2

    written_by = resolve_platform_login(runner)
    timestamp = now_iso8601()
    comment = render_checkpoint_comment(
        card_id=args.card_id,
        escalation_epoch=args.escalation_epoch,
        trigger_attempt_id=args.trigger_attempt_id,
        unique_attempt_count=args.unique_attempt_count,
        checkpoint_decision=args.decision,
        checkpoint_rationale=args.rationale,
        written_by=written_by,
        timestamp=timestamp,
    )
    url = _post_event(runner, target.repo, item.issue_number, comment)

    log_line = (
        f"{timestamp} {CHECKPOINT_LOG_TAG} → decision {args.decision}；"
        f"trigger {args.trigger_attempt_id}；unique_attempt_count {args.unique_attempt_count}；"
        f"寫入者 {written_by}；留言 {url}。"
    )
    new_body = append_log_line(item.body, log_line)
    set_item_body(
        runner, item.content_type, item.content_id, loaded.project, target.repo,
        item.issue_number, new_body
    )

    print(
        f"[checkpoint] 已寫入 {args.card_id} e{args.escalation_epoch}："
        f"decision={args.decision}，trigger={args.trigger_attempt_id}，留言 {url}"
    )
    if args.decision == "escalate":
        print(
            "[checkpoint] 提醒：本指令不改交付狀態。decision=escalate 時卡片應轉 🚨已升級，"
            "請以 `wfcli handoff --status 🚨已升級` 由既有的狀態寫入通道完成——"
            "交付狀態是 current-state 平面，不屬本事件的射程。"
        )
        print(
            "[checkpoint] 升級狀態的**解除**是另一則事件：review-escalation.md §4「escalate "
            "之後的第三種結果」定義的 `escalation-resolution`（ai-workflow#39）。本 checkpoint "
            "的 decision 維持機械導出，不因需求方裁定而改寫；重規劃／換人仍走 "
            "escalation-epoch-change。該 writer 尚未實作（WF-22-CLI4 切片 A 之外），"
            "在它落地前，裁定只能以人讀留言存在，事件流上該區間仍是升級中。"
        )
    print(
        "[checkpoint] 誠實聲明：unique_attempt_count 與 decision 未由事件流機械推導"
        "（§4／§5 的兩個條件需要 carry set 與根因 occurrence 推導，被留痕解析停機擋住；"
        "見 docs/CONSUMER_CONFORMANCE.md 落差 7）。本指令機械保證的只有：欄位形狀、"
        "trigger attempt 裁決已落地、同一 trigger 不重複建。"
    )
    return 0


def run_contract_baseline(args: argparse.Namespace) -> int:
    if not (args.rationale or "").strip():
        print(
            "[contract-baseline] 拒絕：--rationale 不得為空——它是「為何在此刻切 baseline」"
            "的唯一留痕，空字串會讓那個判斷事後不可重建。\n"
            "  ⇒ 旗標與值域（可整行複製，⛔ 無需填任何欄位）：\n"
            "    wfcli contract-baseline --help\n"
            f"  ⇒ 重跑＝卡 ID {args.card_id} 照舊，補一個 --rationale，"
            "值＝「為何在此刻切 baseline」的一句話。\n"
            "  ⚠️ ⛔ 這裡刻意**不給一行可照貼的重跑指令**：理由是**你的判斷**，"
            "機械寫不出來；給一行填空樣板只會被照貼，寫進一筆無意義的 rationale。",
            file=sys.stderr,
        )
        return 2

    loaded = _load_item(args, "contract-baseline")
    if loaded.exit_code is not None:
        return loaded.exit_code
    runner, target, item = loaded.runner, loaded.target, loaded.item

    history = build_issue_event_history(
        fetch_issue_comments(runner, target.repo, item.issue_number)
    )
    if history.baseline_count:
        # review-escalation.md §5「該 marker 為 one-shot cutover」：逐字「該 marker 為
        # one-shot cutover……啟用後再次出現必須 fail loud」。
        print(
            f"[contract-baseline] 拒絕：本 Issue 已有 {history.baseline_count} 則 contract-baseline "
            "事件。該 marker 是 one-shot cutover，啟用後再次出現必須 fail loud"
            "（語意見 review-escalation.md §5「該 marker 為 one-shot cutover」）。\n"
            "  ⇒ 先看既有那幾則是什麼時候切的（已代入實際 repo 與編號）：\n"
            f"    gh issue view {item.issue_number} --repo {target.repo} --comments\n"
            "  ⛔ 這一格**沒有**重切的合法路徑：one-shot 的語意就是不得再來一次。"
            "真的需要再切，請把它當成契約變更上呈需求方。",
            file=sys.stderr,
        )
        return 2

    written_by = resolve_platform_login(runner)
    timestamp = now_iso8601()
    comment = render_contract_baseline_comment(
        card_id=args.card_id,
        declared_by=written_by,
        rationale=args.rationale,
        timestamp=timestamp,
    )
    url = _post_event(runner, target.repo, item.issue_number, comment)

    log_line = (
        f"{timestamp} {BASELINE_LOG_TAG} → contract templates/review-escalation.md；"
        f"宣告者 {written_by}；留言 {url}。"
    )
    new_body = append_log_line(item.body, log_line)
    set_item_body(
        runner, item.content_type, item.content_id, loaded.project, target.repo,
        item.issue_number, new_body
    )

    print(
        f"[contract-baseline] 已寫入 {args.card_id}：cutover 於 {timestamp}，留言 {url}"
    )
    print(
        "[contract-baseline] 邊界：one-shot 只在**本 Issue 範圍內**機械保證"
        "（本指令掃本卡 timeline 後拒絕第二則）。§5 說的是「採用專案」層級的 one-shot，"
        "而本 repo 沒有跨 Issue 的事件索引，跨卡唯一性目前是**約定**，沒有機械執行者。"
    )
    return 0
