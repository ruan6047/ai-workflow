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
    MarkerWriteBoundaryError,
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
from ..brief import validate_shape as validate_brief_shape
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
    p.add_argument(
        "--brief",
        default=None,
        help=(
            "卡片簡介（canonical §6.3）。⚠️ **可選**：既有卡在本欄位上線前一律沒有簡介，"
            "強制必填會讓所有既有卡的動詞失效。形狀兩個要求皆機械檢查——必含「適用時機」"
            "與「⛔ 非射程：」；⛔ 不驗字數（§6.3 逐字：由 70 個 skill description 推導的"
            "長度區間因母體未經品質檢查已整組撤回）。"
        ),
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


def _verify_brief_field(runner, project, item_id: str, expected: str) -> None:
    """讀回 Project 的簡介欄位並與 body 權威值**逐字比對**（canonical §6.3）。

    ⛔ 不做正規化、不比對「第一句」——那個切句規則本身就是會出錯的 parser。
    ⚠️ 讀不到 item（理論上剛建完就該在）視為**失敗**而非略過：靜默略過會讓
    「欄位寫入失敗」與「一切正常」在留痕上無法區分，而那正是本卡要消滅的形狀。
    """
    for snap in list_items(runner, project):
        if snap.item_id != item_id:
            continue
        actual = snap.fields.get("簡介")
        if actual == expected:
            return
        print(
            f"[open] 警示：簡介欄位讀回不符——body 為權威、欄位是恆等導出，"
            f"兩者現在不一致（欄位={actual!r}）。卡已建立，⛔ 請以 "
            f"`wfcli amend <卡ID> --brief` 重寫欄位後再派工。",
            file=sys.stderr,
        )
        return
    print(
        "[open] 警示：剛建立的 item 在讀回時找不到，簡介欄位無法驗證。"
        "⛔ 不視為成功——請以 `wfcli doctor` 確認雙居所是否一致。",
        file=sys.stderr,
    )


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
        # ⛔ **簡介形狀必須在任何 GitHub／Project 操作之前驗**（查核 R1-002）：
        # 原本它在 Card 建構時才驗，而 Card 建構排在 ensure_fields 之後 ⇒ 一個缺標記的
        # --brief 會先在 Project 上建出 15 個欄位才拋錯。**副作用先於驗證**是本 repo
        # 明令要消滅的形狀（零寫入拒絕，同 amend 的前置檢查）。
        if args.brief is not None:
            validate_brief_shape(args.brief)
    except ValueError as exc:
        print(f"[open] 拒絕：{exc}", file=sys.stderr)
        return 2

    try:
        validate_chain_depth(args.chain_depth)
    except ValidationError as exc:
        for e in exc.errors:
            print(f"[open] 拒絕：{e}", file=sys.stderr)
        return 2

    # ⭐ **``Card(...)`` 刻意包進錯誤處理，⛔ 不是防禦性 try**
    # （WF-MARKER-WRITE-BOUNDARY1，2026-08-27 依查核 R1-03 補上）：
    #
    # (a) 現在的行為：``Card.__post_init__`` 的寫入邊界守衛（以及它旁邊那幾道防線）
    #     拒收時，本指令印 ``[open] 拒絕：…`` 並回 rc=2，與上面兩道前置檢查同形。
    # (b) 為什麼：``open`` 是本卡量到的**主破口**（14 個旗標裡 9 個寫得出一張永久不可
    #     amend 的卡），而 ``templates/handoff-contract.md`` §3.2 規則二逐字要求拒收是
    #     **乾淨的**——「以 stack trace 收場的 fail-closed 不算乾淨拒絕」。原本這一段
    #     落在上面那個 try 之外，非法輸入得到的是 rc=1 ＋ traceback。
    #     ``cli.KNOWN_ERRORS`` 另外也收了同一個型別（§3.2 逐字的參考形狀：CLI 層前置
    #     檢查 ＋ model 層 ``__post_init__`` 防線，兩處共用同一份判準函式）；本層存在
    #     的意義是給出與其他 open 拒收一致的 ``[open] 拒絕：`` 前綴。
    # (c) ⛔ **不得由此推出「可以把整段 open 流程包進 try」**：本 try 只包住 ``Card``
    #     建構這一個**純函式**呼叫，它排在任何遠端寫入之前。包大一點就會把遠端寫入的
    #     失敗也吞成「拒絕」，而那兩者的處置完全不同。
    try:
        card = Card(
            card_id=args.card_id,
            feature=args.feature,
            tier=args.tier,
            db_scope=args.db_scope,
            core_pain=args.core_pain,
            service_goal=args.service_goal,
            brief=args.brief,
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
    except MarkerWriteBoundaryError as exc:
        # ⚠️ **刻意只收這一個型別，⛔ 不收父類 ``ValueError``**（就地留註，這一格改窄過一次）：
        # (a) 現在的行為：``Card.__post_init__`` 其餘的防線（tier／db_scope 不一致／
        #     路由名字保留字元／chain_depth）仍原樣往上拋。
        # (b) 為什麼：那幾條在 CLI 層**已經各自有前置檢查**給乾淨訊息，而
        #     ``tests/test_amend.py::test_open_refuses_an_unreadable_name_before_touching_github``
        #     刻意停用前置檢查、斷言 ``Card`` 建構仍會拋 ``ValueError`` ——那條測試釘的是
        #     「model 層是獨立防線」這個深層性質。收父類會把它吞掉，等於用一個新缺陷
        #     換掉舊缺陷。
        # (c) ⛔ **不得由此推出「其他 ValueError 的拒收是乾淨的」**：它們的乾淨度來自
        #     上面那兩道前置檢查，⛔ 不是來自這裡。
        print(f"[open] 拒絕：{exc}", file=sys.stderr)
        return 2

    target = resolve_target(
        owner=args.owner, project=args.project, repo=args.repo, config=args.config
    )
    runner = default_runner
    project = resolve_project(runner, target.owner, target.project)

    existing = list_items(runner, project)
    if find_item_by_card_id(existing, card.card_id):
        print(
            f"[open] 拒絕：卡ID {card.card_id} 已存在於 project {target.owner}/{target.project}",
            file=sys.stderr,
        )
        return 3

    # ⭐ 欄位 schema 的準備**刻意擺在「卡ID 已存在」那道拒收之後**。
    #
    # (a) 刻意如此：讀起來像「為什麼不跟 `resolve_project` 放一起」，答案是不能。
    # (b) 為什麼：`ensure_fields` 不是唯讀的——缺哪個凍結欄位就送一次
    #     `gh project field-create`。擺在拒收之前，「卡ID 已存在 ⇒ rc=3」這條路
    #     就會先改掉 Project 的欄位定義，而模組頂端逐字寫著「副作用先於驗證是本
    #     repo 明令要消滅的形狀」。
    # (c) ⛔ **也不得再往後搬**：它必須留在 `create_repo_issue` **之前**。
    #     反過來（先建 Issue 再 ensure_fields）會把失敗面換成「Issue 建了、欄位
    #     炸了」——一張沒有任何欄位值的孤兒卡，那比現在糟。這一行的位置是
    #     「拒收之後、第一次寫入之前」這個區間裡唯一的落點。
    # (d) ⛔ 不得由這行的位置推出「ensure_fields 是唯讀的」——它不是，只是往後挪了。
    fields = ensure_fields(runner, target.owner, target.project)

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
    # 雙居所的**導出**那一半（canonical §6.3）：body 已在上方寫成，欄位在此跟上。
    # ⚠️ 只在有簡介時寫——既有卡與不給 --brief 的新卡都不該被塞空字串，那會讓
    # brief.drifted 把「兩居所皆空」誤判成「欄位有值而 body 沒有」。
    if card.brief is not None:
        values["簡介"] = card.brief
    # 階段軸的初始值（canonical §0.1）：open 建的卡一律始於「需求」——
    # ⚠️ 與交付狀態 💡需求 同源但**不是同一件事**：那是狀態，這是階段。
    values["階段"] = "需求"
    for name, value in values.items():
        set_field_value(runner, project, item_id, fields[name], value)
    # ⭐ 讀回驗證（§6.3 逐字「寫入順序 body 先、欄位後並讀回驗證」）。
    # 失敗模式是「body 已更新、欄位過期」，⛔ 靜默失敗正是本卡要防的。
    if card.brief is not None:
        _verify_brief_field(runner, project, item_id, card.brief)

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
