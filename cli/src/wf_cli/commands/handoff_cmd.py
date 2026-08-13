"""``wfcli handoff``：交接（狀態轉換＋source SHA＋證據欄必填）。

source_sha 必須是完整 40 字元 hex；``--repo-path`` 有給時另外唯讀驗證該 commit
真的存在於本機 repo（對齊 handoff-contract.md §1「sender 必須先 push source_sha
指向的 commit」的精神——CLI 能做的部份先擋，pushed／branch tip 一致性仍需
receiver 自行複查，CLI 不代替人類判斷）。release 若卡片需要部署且尚未 ✅已驗證，
機械拒絕（canonical §0「需部署卡在部署 ✅已驗證 前不得 release」）。

iteration 遞增（需求方 2026-08-05 拍板；WF-22-CLI2）：``--next-stage
implementation`` 承載「查核退回」語意（review → 退回 implementation 修正），讀回
現值＋1 寫回；``review``／``release`` 這兩個方向不遞增。``--iteration N`` 是顯式
覆寫逃生門（供 iteration counter 需要異常修正時使用），會印出警示，覆寫理由請
說明於既有必填的 ``--evidence``，不另建新旗標。

## ``--cleanup``：release 接上 WF-CLEANUP-GUARD1 的守衛（R1-002）

``--next-stage release`` 原本只寫狀態面。帶 ``--cleanup`` 時改走
`cleanup.execute_closeout_transition`——與 `reconcile --apply` 白名單第 2 條**同一份**
守衛與同一個 executor（`cleanup.py` 模組說明）。差別只在誰發動，前提一條都不放寬。

**預設不清理，理由寫在這裡而不是只寫在文件裡**：

1. `release` 現行使用者的預期是「只改狀態」。把預設改成會刪 worktree 與遠端分支，
   等於讓一個既有指令在沒人要求的情況下開始刪東西——那正是本卡（canonical
   ``AI_WORKFLOW.md:146``「禁止靜默刪除工作內容」）要消滅的形態。
2. 兩種預設的錯誤代價不對稱：漏清理可以再跑一次補；刪錯了沒有補救。預設值取
   代價可回復的那一邊。
3. ``--cleanup`` 需搭配 ``--repo-path``。沒有 repo 就沒有可刪對象，這個旗標因此
   無法被設定檔或環境變數「不小心變成預設」。

**刻意不提供 ``--main-ref``／``--remote``**：它們是能讓祖先檢查名存實亡的旋鈕
（把 main_ref 指向待刪分支自己，``merge-base --is-ancestor`` 必然通過）。doctor 的
同名旗標無妨，因為 doctor 唯讀；破壞性路徑上不開這個口。

**``--cleanup`` 做哪幾件事不是固定的**（WF-CLEANUP-SQUASH-AWARE1）：授權範圍由合併
方式決定——merge 合併走 ``ancestor``，三個動作全做；squash 合併走 ``content_absorbed``，
**只移除 worktree、分支保留**（`cleanup.AUTHORITY_BY_PROOF`）。因此本指令的輸出與
寫回卡片的終態留痕**都由實際執行的動作集合產生**（`cleanup.describe_cleanup`），
不是固定字串——上一版就是寫死字串，於是授權分流上線後留痕開始宣稱一件沒發生的事。

**不帶 ``--cleanup`` 的代價也必須講明**：那條路徑會在清理完成前寫入終態，依
`cleanup.classify_state` 的分類即 ``illegal_terminal_before_cleanup``；守衛不自動
修復非法態，所以事後再補 ``--cleanup`` 會被擋。因此該路徑會印出警示，而不是靜靜
維持原狀。
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from .. import git_ops
from ..card import append_log_line, now_iso8601, parse_branch_worktree
from ..cleanup import (
    SUBSEQUENT_OBLIGATION_STEPS,
    CleanupTarget,
    CleanupOutcome,
    CloseoutResult,
    RemoteCardFacts,
    describe_cleanup,
    execute_closeout_transition,
)
from ..config import add_target_args, resolve_target
from ..gh import GhError, GhRunner, default_runner
from ..project import (
    ItemSnapshot,
    ensure_fields,
    find_item_by_card_id,
    list_items,
    resolve_project,
    set_field_value,
    set_item_body,
)
from ..registry import RegisteredCard, TasksMdRegistry
from ..validation import ValidationError, validate_evidence, validate_source_sha
from .assign_cmd import TERMINAL_STATUSES

STAGE_STATUS = {
    "implementation": "🚧進行中",
    "review": "🔍待查核",
}

#: 不帶 ``--cleanup`` 的 release 會造出「終態已寫、清理未做」的組合。這不是猜測，
#: 是 `cleanup.classify_state` 對該組合的分類名稱。
NO_CLEANUP_WARNING = (
    "[handoff] 警示：未帶 --cleanup 的 release 只寫狀態面。worktree 與分支"
    "（權威清單 templates/worktree-lifecycle.md 第 2 步）不會被清理，而終態已經寫下去了"
    "——依 WF_CLEANUP_GUARD1 的分類，這是 illegal_terminal_before_cleanup。"
    "守衛不自動修復非法態，事後再補 --cleanup 會被擋，屆時只能人工收尾。"
)


class _CallbackEffectWriter:
    """把第 4 步的兩次狀態面寫入包成 `cleanup.CloseoutEffectWriter`。

    本類別只負責「怎麼寫」；**「何時寫」完全由 executor 決定**——它只在第 1–3 步
    確實完成後才呼叫。因此「終態先於清理」這個組合在這條路徑上寫不出來，不是靠
    呼叫端自律。
    """

    def __init__(
        self,
        close_issue: Callable[[], None],
        write_terminal: Callable[[CleanupOutcome], None],
    ) -> None:
        self._close_issue = close_issue
        self._write_terminal = write_terminal
        self.calls: list[str] = []

    def close_issue(self, target: CleanupTarget) -> None:
        self.calls.append("close_issue")
        self._close_issue()

    def write_release_terminal(
        self, target: CleanupTarget, outcome: CleanupOutcome
    ) -> None:
        # `outcome` 原樣轉交，本類別**不加工也不加註**：留痕的措辭只有
        # `cleanup.describe_cleanup()` 一個產生點。
        self.calls.append("write_release_terminal")
        self._write_terminal(outcome)


def registry_from_items(items: list[ItemSnapshot]) -> TasksMdRegistry:
    """用 Project items 組出守衛要的卡註冊。

    `no_foreign_active_lease` 要問的是「別張活卡是不是還握著同一條分支／worktree」。
    已 cutover 到 GitHub Issues 的專案，那個事實在 Project 欄位裡，不在 docs/TASKS.md，
    所以這裡就地轉成守衛認得的 `RegisteredCard` 形狀（`registry.py` 未改動）。
    """
    active: list[RegisteredCard] = []
    for it in items:
        if not it.card_id:
            continue
        branch, worktree = parse_branch_worktree(it.branch_worktree or "")
        active.append(
            RegisteredCard(
                card_id=it.card_id,
                branch=branch,
                worktree_path=worktree,
                delivery_status=it.delivery_status,
                owner=it.owner_field,
                last_handoff=it.text("最後交接"),
            )
        )
    return TasksMdRegistry(active=active, archived_card_ids=set(), source_paths=[])


def _issue_open(runner: GhRunner, repo: str, issue_number: int) -> bool | None:
    """Issue 現在是不是開著。讀不到回 ``None``——由呼叫端 fail closed。

    這個值決定第 4 步要不要關 Issue。猜錯的後果是「Issue 還開著卻回報 completed」，
    也就是一個看起來成功的半完成收尾，因此不猜。
    """
    try:
        data = runner.run_json(
            ["issue", "view", str(issue_number), "--repo", repo, "--json", "state"]
        )
    except GhError:
        return None
    state = str((data or {}).get("state") or "").upper()
    if state not in {"OPEN", "CLOSED"}:
        return None
    return state == "OPEN"


def _print_closeout(result: CloseoutResult, card_id: str) -> None:
    """stderr／stdout 的逐項回報。**與終態留痕同源**：兩者都由動作集合產生。

    `mode=applied` 不代表三個動作都做了——squash 路徑只做 worktree。因此這裡逐格
    印出，並在最後印一行與終態留痕**逐字相同**的摘要，讓「畫面上看到的」與「寫進
    卡片的」不可能各說各話。
    """
    outcome = result.cleanup_outcome
    print(f"[handoff] 收尾轉換（{card_id}）：mode={result.mode}／"
          f"狀態={result.state_after}（合法={result.legal_state}）")
    if result.authorized_actions:
        print(f"  - 本次授權：{', '.join(sorted(result.authorized_actions))}")
    if outcome.performed:
        print(f"  - 已執行：{', '.join(outcome.performed)}")
    if outcome.skipped_absent:
        print(f"  - 跳過（本來就不存在）：{', '.join(outcome.skipped_absent)}")
    if outcome.withheld_unauthorized:
        print(f"  - 保留（授權不足，刻意不刪）：{', '.join(outcome.withheld_unauthorized)}")
    if outcome.aborted:
        print(f"  - 中止（刪除前複驗不通過）：{', '.join(outcome.aborted)}")
    if outcome.unaccounted:
        print(f"  - 未走到：{', '.join(outcome.unaccounted)}")
    print(f"  - 留痕敘述：{describe_cleanup(outcome)}")
    for reason in result.blocking_reasons:
        print(f"  - 阻擋：{reason}", file=sys.stderr)
    print(f"  - 其後義務（不寫狀態面、不阻擋 release）：第 "
          f"{'、'.join(str(s) for s in SUBSEQUENT_OBLIGATION_STEPS)} 步仍待完成")


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("handoff", help="交接：狀態轉換＋source SHA＋證據欄必填")
    add_target_args(p)
    p.add_argument("card_id")
    p.add_argument("--to", required=True, help="下一位 owner（角色／帳號／模型@工具）")
    p.add_argument(
        "--next-stage", required=True, choices=["implementation", "review", "release"]
    )
    p.add_argument("--source-sha", required=True, help="完整 40 字元 hex SHA")
    p.add_argument("--evidence", required=True, help="測試／CI／審核／決策連結或摘要")
    p.add_argument(
        "--repo-path",
        default=None,
        help="有給則唯讀驗證 source_sha 在該本機 repo 存在（不驗證是否已 push）",
    )
    p.add_argument("--status", default=None, help="覆寫依 next-stage 推導出的交付狀態")
    p.add_argument(
        "--cleanup",
        action="store_true",
        help="僅 --next-stage release：連同執行守衛化的收尾清理，全部前提成立才動手。"
        "**實際做哪幾個動作視合併方式而定**：merge 合併（分支是 main 的祖先）會移除 "
        "worktree 並刪本地與遠端分支；squash 合併只移除 worktree，分支刻意保留"
        "（cleanup.AUTHORITY_BY_PROOF）。做了什麼以本次輸出與寫回卡片的留痕為準。"
        "**預設不清理**——刪除不可逆，預設值取代價可回復的那一邊；需搭配 --repo-path",
    )
    p.add_argument(
        "--iteration",
        type=int,
        default=None,
        help="顯式覆寫 iteration（僅供異常修正逃生門；會印出警示，"
        "覆寫理由請說明於 --evidence；不覆寫時依 --next-stage 自動推導）",
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    try:
        validate_source_sha(args.source_sha)
        validate_evidence(args.evidence)
    except ValidationError as exc:
        for e in exc.errors:
            print(f"[handoff] {e}", file=sys.stderr)
        return 2

    if args.cleanup and args.next_stage != "release":
        print("[handoff] 拒絕：--cleanup 只適用於 --next-stage release", file=sys.stderr)
        return 2
    if args.cleanup and not args.repo_path:
        print("[handoff] 拒絕：--cleanup 需要 --repo-path（守衛要在真實 repo 上驗前提）",
              file=sys.stderr)
        return 2

    if args.repo_path:
        repo_root = Path(args.repo_path)
        if not git_ops.commit_exists(repo_root, args.source_sha):
            print(
                f"[handoff] 拒絕：source_sha {args.source_sha} 在 {repo_root} 找不到對應 commit",
                file=sys.stderr,
            )
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
        print(f"[handoff] 找不到卡 {args.card_id}", file=sys.stderr)
        return 3

    if args.status:
        new_status = args.status
    elif args.next_stage == "release":
        deployment_status = item.fields.get("部署狀態")
        if deployment_status not in (None, "—不適用", "✅已驗證"):
            print(
                "[handoff] 拒絕：需部署卡在部署 ✅已驗證 前不得 release"
                f"（目前部署狀態={deployment_status}；canonical §0）",
                file=sys.stderr,
            )
            return 4
        new_status = "🏁完成"
    else:
        new_status = STAGE_STATUS[args.next_stage]

    current_iteration = item.fields.get("iteration")
    current_iteration = int(current_iteration) if current_iteration is not None else 0

    if args.iteration is not None:
        # 顯式覆寫逃生門：直接採用給定值，不套用自動遞增規則（供 iteration
        # counter 因例外狀況需要人工修正時使用；理由寫在既有必填的 --evidence，
        # 不另立新旗標）。
        new_iteration = args.iteration
        print(
            f"[handoff] 警示：顯式覆寫 iteration（{current_iteration} → {new_iteration}），"
            "非自動遞增路徑；此為異常修正逃生門，覆寫理由須說明於 --evidence",
            file=sys.stderr,
        )
    elif args.next_stage == "implementation":
        # 查核退回語意：handoff → implementation 代表送回修正，讀回現值＋1
        # 寫回（需求方 2026-08-05 拍板；review／release 兩個方向不遞增）。
        new_iteration = current_iteration + 1
    else:
        new_iteration = current_iteration

    ts = now_iso8601()

    def write_status_face(cleanup_note: str = "") -> None:
        set_field_value(runner, project, item.item_id, fields["owner"], args.to)
        set_field_value(runner, project, item.item_id, fields["交付狀態"], new_status)
        set_field_value(runner, project, item.item_id, fields["最後交接"], ts)
        set_field_value(runner, project, item.item_id, fields["iteration"], new_iteration)

        log_line = (
            f"{ts} handoff by wf-cli → owner {args.to}；iteration {new_iteration}；"
            f"SHA {args.source_sha}；證據 {args.evidence}{cleanup_note}。"
        )
        new_body = append_log_line(item.body, log_line)
        set_item_body(
            runner, item.content_type, item.content_id, project, target.repo,
            item.issue_number, new_body,
        )

    if args.cleanup:
        rc = _release_with_cleanup(
            args, runner, target.repo, item, items, write_status_face
        )
        if rc != 0:
            return rc
    else:
        if args.next_stage == "release":
            print(NO_CLEANUP_WARNING, file=sys.stderr)
        write_status_face()

    print(f"[handoff] 已交接 {args.card_id} → {args.to}（狀態={new_status}，SHA={args.source_sha}）")
    return 0


def _release_with_cleanup(
    args: argparse.Namespace,
    runner: GhRunner,
    repo: str | None,
    item: ItemSnapshot,
    items: list[ItemSnapshot],
    write_status_face: Callable[[str], None],
) -> int:
    """release 的守衛化路徑：清理先於狀態面，兩者由同一個 executor 串起來。

    這裡**不自己判斷任何前提**，也不自己決定寫入順序——那些全在
    `cleanup.execute_closeout_transition` 裡，與 reconcile 共用。本函式只負責把
    Project 上的事實翻譯成守衛要的輸入，並把第 4 步的寫入包成 effect writer。
    """
    branch, worktree = parse_branch_worktree(item.branch_worktree or "")
    if not branch:
        print(f"[handoff] 拒絕：{args.card_id} 的「分支worktree」欄沒有可解析的分支，"
              "無法界定要清理什麼（請先修欄位，不要讓守衛猜）", file=sys.stderr)
        return 2

    repo_root = Path(args.repo_path).resolve()
    worktree_path: Path | None = None
    if worktree:
        candidate = Path(worktree)
        worktree_path = candidate if candidate.is_absolute() else repo_root / candidate

    issue_open = False
    if item.issue_number is not None:
        if not repo:
            print("[handoff] 拒絕：卡由 Issue 承載但沒有 --repo，讀不到 Issue 開關狀態",
                  file=sys.stderr)
            return 2
        state = _issue_open(runner, repo, item.issue_number)
        if state is None:
            # fail closed：讀不到就不動手。猜「已關」會讓收尾自稱 completed 卻留著
            # 開著的 Issue；猜「開著」則會對已關的 Issue 再關一次。兩個都不做。
            print(f"[handoff] 拒絕：讀不到 Issue #{item.issue_number} 的開關狀態，"
                  "無法判斷第 4 步該做什麼；不猜、不動手", file=sys.stderr)
            return 5
        issue_open = state

    def close_issue() -> None:
        if item.issue_number is not None and repo:
            runner.execute(["issue", "close", str(item.issue_number), "--repo", repo])

    def write_terminal(outcome: CleanupOutcome) -> None:
        # ⚠️ 這句話**必須由 executor 實際做過的動作產生**，不得是固定字串。
        #
        # R2 之前它寫死成「worktree 與本地／遠端分支皆已不存在」，理由是「executor
        # 只在清理確實完成後才呼叫本函式」——那個理由在 squash 授權分流上線的當下就
        # 失效了：squash 路徑刻意保留分支，而這句話仍宣稱分支不存在。
        # **行為改了、敘述沒改，因為兩者不同源。** 現在同源：唯一的產生點是
        # `cleanup.describe_cleanup()`，輸入是這一輪的 `CleanupOutcome`。
        write_status_face("；" + describe_cleanup(outcome))

    writer = _CallbackEffectWriter(close_issue, write_terminal)
    target_spec = CleanupTarget(
        repo_root=repo_root,
        card_id=args.card_id,
        branch=branch,
        worktree_path=worktree_path,
    )
    result = execute_closeout_transition(
        target_spec,
        trigger="release",
        registry=registry_from_items(items),
        card_body=item.body,
        remote_facts=RemoteCardFacts(
            terminal_status_written=(item.delivery_status or "") in TERMINAL_STATUSES,
            issue_open=issue_open,
        ),
        effect_writer=writer,
    )
    _print_closeout(result, args.card_id)

    if result.mode != "applied":
        # 守衛擋下或中途中止：狀態面**一個字都沒寫**（第 4 步由 executor 在清理
        # 完成後才呼叫）。卡停在原本的交付狀態，Issue 維持原狀，可重跑續作。
        print(f"[handoff] 拒絕 release：收尾未完成（mode={result.mode}），"
              "狀態面未寫入；請處理上列阻擋原因後重跑", file=sys.stderr)
        return 5
    if not result.observation_after.effect_done:
        # applied 但效果沒落地：清理回報成功而實際沒完成（受保護分支、鏡像同步…）。
        # 此時 executor 刻意扣住第 4 步，這裡跟著回非 0，不讓它看起來像成功。
        print("[handoff] 拒絕 release：清理未真正完成，第 4 步已被守衛扣住，"
              "終態未落地", file=sys.stderr)
        return 5
    if writer.calls and writer.calls[-1] != "write_release_terminal":
        print("[handoff] 拒絕：第 4 步的寫入順序異常（終態不是最後一步）", file=sys.stderr)
        return 5
    if not writer.calls:
        # 卡早已在終態且清理也已完成：本次是冪等空跑，不重複寫入。
        print(f"[handoff] {args.card_id} 已在終態且清理完成，本次為冪等空跑，未重複寫入狀態面")
    return 0
