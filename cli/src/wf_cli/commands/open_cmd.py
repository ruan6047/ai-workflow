"""``wfcli open``：把一個**待審清單項**升級成卡（Issue 改寫＋上板＋必填欄機械檢查）。

CLI 是唯一寫入通道：不經 CLI 直接在 GitHub UI 上手改欄位／Issue，即違反卡面紅線 1。

⭐ **``--from-issue <url>`` 是唯一的開卡路徑**（`WF-REDESIGN-W1` 驗收 2）。
本指令**不再建立任何 issue**，也**不再建立 DraftIssue**：

- (a) 現在的行為：``open`` 只吃一個**已存在**的 issue URL，驗它是不是填齊了收件表單
  五欄，然後把它改寫成卡面、掛上 Project。
- (b) 為什麼：量到的痛點是「開卡速率高於可證明的推進速率下界」，⭐ 承重證據是
  2026-08-28 一天四張同族卡。產生器就在 ``open`` 自己身上——它能無中生有一張卡，
  於是「先開再說」的成本是零。改成只能升級既有清單項之後，開卡前必然先有一個
  **經過收件五條件**的清單項，而那五條件裡有「查重留痕」。
- (c) ⛔ **不得由此推出「開卡從此不會爆量」**：清單項本身仍可無限增加，本閘門只
  保證每一張卡都指得回一個填了表的清單項。清單當墓地是可接受的（收件條件檔逐字）。

⛔ **DraftIssue 的建立已封閉，但讀取相容⛔ 未移除**（就地留註，這一格是判斷不是疏漏）：
卡面驗收 2 逐字只要求「直接建 issue 與 DraftIssue **兩分支**移除」——那兩個分支在本檔，
已移除。卡面簡介另有一句「artifact 顯示 DraftIssue 列數 0 後，讀相容**方可**移除」，
其緊接的下一句是「創建封閉與遺留可讀**兩軸各有測試**」⇒ 遺留可讀是要留著並被測的那
一軸。⇒ ``project.list_items``／``set_item_body``／``review``／``checkpoint`` 等處的
DraftIssue 讀取路徑**刻意保留**。⛔ 不得由本檔的移除推出「那些也該刪」。
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from ..card import (
    CAPABILITY_TIERS,
    Card,
    MarkerWriteBoundaryError,
    append_log_line,
    now_iso8601,
    render_issue_body,
    render_spec_markdown,
    validate_capability_routing,
    validate_routing_names,
)
from ..card_face import CardFaceError, validate_issue_url
from ..card_face import validate as validate_card_face
from ..config import add_target_args, resolve_target
from ..gh import default_runner
from ..intake import missing_requirements, remediation
from ..project import (
    add_item_to_project,
    ensure_fields,
    find_item_by_card_id,
    list_items,
    resolve_project,
    set_field_value,
    set_issue_title,
    set_item_body,
)
from ..resources import ResourceDeclaration, ResourceDeclarationError
from ..brief import validate_shape as validate_brief_shape
from ..validation import ValidationError, validate_chain_depth, validate_open_fields

#: ``stage_plan`` 裡代表「這張卡要跑部署階段」的階段名。
#:
#: ⭐ **這是 ``--needs-deploy`` 的取代者**（`docs/research/WORKFLOW-REDESIGN-2026-08-30.md`
#: §一第 12 列逐字：被取代者＝``--needs-deploy`` 旗標，取代者＝開卡表單「階段計畫」，
#: owner＝W1）。⇒ 部署狀態的初值不再由一個獨立旗標宣告，而是**從階段計畫導出**：
#: 宣告要跑部署階段 ⇒ ``⏸未部署``；沒宣告 ⇒ ``—不適用``。
#:
#: ⚠️ 兩者的**值域完全相同**（那兩個字面沒有變），改變的只有「誰決定它」。
#: ⛔ 不得由此推出部署狀態欄已退位——欄位退位是取代清單第 7 列，owner 是切換
#: Initiative，⛔ 不在本卡射程。
DEPLOY_STAGE = "部署"


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "open", help="把待審清單項升級成卡（--from-issue 為唯一路徑；必填欄機械檢查）"
    )
    add_target_args(p)
    p.add_argument("card_id")
    p.add_argument(
        "--from-issue",
        required=True,
        metavar="URL",
        help="待審清單項的 issue URL（唯一開卡路徑）。形狀須為 "
        "https://github.com/<owner>/<repo>/issues/<n>，⛔ 不允許結尾斜線／query／fragment。"
        "該 issue 的 body 必須填齊收件表單五欄（stage-rules/list-intake-requirements.md），"
        "否則零寫入拒絕。",
    )
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
    p.add_argument(
        "--acceptance",
        action="append",
        required=True,
        help="可重複；驗收條件逐行。⭐ **必填且至少一條**（`WF-REDESIGN-W1` 驗收 4）——"
        "原本可為空，於是開得出一張沒有任何可驗收之物的卡，而那正是「開卡速率高於"
        "可證明的推進速率」的一個入口。空白字串同樣拒收。",
    )
    p.add_argument("--verification", action="append", default=[], help="可重複；驗證項目逐行")
    # ---- 卡面表單（`WF-REDESIGN-W1` 驗收 3）。schema 全文見 card_face.SCHEMA_TEXT ----
    p.add_argument(
        "--stage-plan",
        action="append",
        required=True,
        metavar="階段=目標",
        help="可重複；階段計畫逐條，格式 `<階段>=<該階段的目標>`。"
        "階段值域＝需求／研究／規劃／執行／審核／部署／維護／結案（card_face schema 的封閉列舉）。"
        "⛔ 同一個階段不得出現兩次。⭐ 含「部署」時，部署狀態初值為 ⏸未部署"
        "（`--needs-deploy` 的取代者，見 DEPLOY_STAGE）。",
    )
    p.add_argument(
        "--tier-basis-sensitive-surfaces",
        required=True,
        help="級別依據三子問之一：這張卡碰到哪些敏感面。",
    )
    p.add_argument(
        "--tier-basis-recoverability",
        required=True,
        help="級別依據三子問之一：錯了以後怎麼復原。",
    )
    p.add_argument(
        "--tier-basis-blast-radius",
        required=True,
        help="級別依據三子問之一：影響面有多大。",
    )
    p.add_argument(
        "--list-convergence",
        action="append",
        default=[],
        metavar="URL=claim",
        help="可重複；本卡涵蓋（covers）或相關（related）的**其他**清單項，"
        "格式 `<issue URL>=<covers|related>`。⭐ 預設空陣列是合法的。"
        "⛔ 同一個 URL 不得出現兩次。"
        "⚠️ ⛔ **不含 --from-issue 自己**：升級後那個 issue 就是本卡，指向自己沒有意義。",
    )
    p.add_argument(
        "--spec-dir",
        default=None,
        help="git spec 檔骨架寫入目錄（慣例 tasks/）；未給則只改 Issue／上板，不寫檔",
    )
    p.set_defaults(func=run)


def _parse_pairs(raw: list[str], *, flag: str, sep_from_right: bool) -> list[tuple[str, str]]:
    """把 ``a=b`` 形狀的重複旗標切成 pairs；形狀不對就拋 ``ValueError``。

    ``sep_from_right`` 決定從哪一側切：``--stage-plan`` 的目標可以含 ``=``（自由文字），
    ⇒ 從左切；``--list-convergence`` 的 URL 正規形**不含** ``=``（query 被禁），
    ⇒ 從右切，claim 才不會被目標裡的等號吃掉。
    """
    pairs: list[tuple[str, str]] = []
    for entry in raw:
        if "=" not in entry:
            raise ValueError(
                f"{flag} 的值 {entry!r} 缺少 `=`；格式為 "
                f"{'`<階段>=<目標>`' if not sep_from_right else '`<issue URL>=<covers|related>`'}"
            )
        left, right = entry.rsplit("=", 1) if sep_from_right else entry.split("=", 1)
        pairs.append((left.strip(), right.strip()))
    return pairs


def _build_card_face(args: argparse.Namespace) -> dict:
    """把旗標組成卡面表單。**⛔ 不在這裡驗 schema**——驗證由 ``card_face.validate``
    一處負責（writer／reader 共用同一個 validator 是卡面驗收 3 逐字的要求）。
    """
    stages = _parse_pairs(args.stage_plan, flag="--stage-plan", sep_from_right=False)
    convergence = _parse_pairs(
        args.list_convergence, flag="--list-convergence", sep_from_right=True
    )
    return {
        "schema_version": "1",
        "stage_plan": [{"stage": s, "goal": g} for s, g in stages],
        "tier_basis": {
            "sensitive_surfaces": args.tier_basis_sensitive_surfaces,
            "recoverability": args.tier_basis_recoverability,
            "blast_radius": args.tier_basis_blast_radius,
        },
        "list_convergence": [{"issue_url": u, "claim": c} for u, c in convergence],
    }


def _split_issue_url(issue_url: str) -> tuple[str, int]:
    """正規形 URL → ``(owner/repo, number)``。呼叫端須已跑過 ``validate_issue_url``。"""
    parts = issue_url.split("/")
    return f"{parts[-4]}/{parts[-3]}", int(parts[-1])


def _already_card_body(body: str) -> bool:
    """這份 body 是不是已經被寫成卡面。

    判準是**兩個結構性標記其中之一**（路由行版本標記／卡面表單哨兵），⛔ 不看自由文字：
    清單項的引文完全可能提到「執行」「驗收條件」這些字眼，拿它們當判準就是又一個
    「用內容猜格式版本」（card.py ``ROUTING_MARKER`` 上方那一整段記著這個病犯過兩次）。
    """
    from ..card import ROUTING_MARKER
    from ..card_face import BEGIN as CARD_FACE_BEGIN

    return ROUTING_MARKER in body or CARD_FACE_BEGIN in body


def _resume_runbook(owner_repo: str, number: int) -> str:
    """body 已是卡面時的**可跑**還原指令（平台 ``userContentEdits`` 取前一版）。"""
    owner, name = owner_repo.split("/", 1)
    query = (
        '{repository(owner:"%s",name:"%s"){issue(number:%d)'
        "{userContentEdits(last:1){nodes{diff}}}}}" % (owner, name, number)
    )
    return (
        "⇒ 這通常代表先前有一次 open 已改寫 body、但在上板或寫欄位時中斷。\n"
        "  還原清單項原文後再重跑（兩行都是真指令，已代入實際 repo 與編號）：\n"
        f"    gh api graphql -f query='{query}' "
        f"--jq '.data.repository.issue.userContentEdits.nodes[0].diff' > /tmp/intake-{number}.md\n"
        f"    gh issue edit {number} --repo {owner_repo} --body-file /tmp/intake-{number}.md\n"
        "  ⚠️ 若該 issue 其實已經在板上，那它已經是卡了——⛔ 不要重跑 open。"
    )


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


def run(args: argparse.Namespace) -> int:  # noqa: C901 - 逐旗標的前置檢查本就是平鋪的
    resources_list = [r.strip() for r in args.resources.split(",") if r.strip()]
    try:
        decl = ResourceDeclaration(db_scope=args.db_scope, resources=resources_list)
    except ResourceDeclarationError as exc:
        print(f"[open] 資源宣告錯誤：{exc}", file=sys.stderr)
        return 2

    # ⭐ 驗收條件 ≥1（卡面驗收 4）。argparse 的 ``required=True`` 已擋掉「一條都沒給」；
    # 這裡補的是它擋不到的**空白字串**——與 ``--core-pain`` 空白時同樣硬拒，不建卡。
    acceptance = [a for a in args.acceptance if a.strip()]
    if not acceptance:
        print(
            "[open] 拒絕：--acceptance 至少要有一條非空白的驗收條件"
            f"（收到 {len(args.acceptance)} 條，全部是空白）。"
            "⇒ 沒有可驗收之物的卡驗不了收，開了只會變成看板上的常駐項。",
            file=sys.stderr,
        )
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
    #
    # ⭐ 卡面表單同理：``card_face.validate`` 也是 ``Card.__post_init__`` 的防線，
    # 這裡先跑一次是為了**零遠端寫入**地給出 ``[open] 拒絕：`` 這一種訊息。
    try:
        validate_issue_url(args.from_issue)
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
        card_face = _build_card_face(args)
        validate_card_face(card_face)
    except (ValueError, CardFaceError) as exc:
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
            card_face=card_face,
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
            acceptance=acceptance,
            verification=args.verification or ["TODO：填入驗證指令與證據要求"],
            # ⭐ 部署狀態由**階段計畫**導出，⛔ 不再有 --needs-deploy（見 DEPLOY_STAGE）。
            deployment_status=(
                "⏸未部署"
                if any(s["stage"] == DEPLOY_STAGE for s in card_face["stage_plan"])
                else "—不適用"
            ),
            chain_depth=args.chain_depth,
        )
    except MarkerWriteBoundaryError as exc:
        # ⚠️ **刻意只收這一個型別，⛔ 不收父類 ``ValueError``**（就地留註，這一格改窄過一次）：
        # (a) 現在的行為：``Card.__post_init__`` 其餘的防線（tier／db_scope 不一致／
        #     路由名字保留字元／chain_depth／卡面表單）仍原樣往上拋。
        # (b) 為什麼：那幾條在 CLI 層**已經各自有前置檢查**給乾淨訊息，而
        #     ``tests/test_amend.py::test_open_refuses_an_unreadable_name_before_touching_github``
        #     刻意停用前置檢查、斷言 ``Card`` 建構仍會拋 ``ValueError`` ——那條測試釘的是
        #     「model 層是獨立防線」這個深層性質。收父類會把它吞掉，等於用一個新缺陷
        #     換掉舊缺陷。
        # (c) ⛔ **不得由此推出「其他 ValueError 的拒收是乾淨的」**：它們的乾淨度來自
        #     上面那兩道前置檢查，⛔ 不是來自這裡。
        print(f"[open] 拒絕：{exc}", file=sys.stderr)
        return 2

    owner_repo, issue_number = _split_issue_url(args.from_issue)
    target = resolve_target(
        owner=args.owner, project=args.project, repo=args.repo, config=args.config
    )
    if target.repo and target.repo != owner_repo:
        print(
            f"[open] 拒絕：--from-issue 指向 {owner_repo}，但目標設定的 repo 是 "
            f"{target.repo}。⇒ 卡所屬的 repo 由 issue URL 決定（registry 的軸 A 讀的就是它），"
            "兩者不一致時⛔ 不猜哪一個算數。請改 --repo 或改 --from-issue。",
            file=sys.stderr,
        )
        return 2

    runner = default_runner

    # ---- 收件閘門：讀清單項，驗五欄。⭐ 全程唯讀，拒絕時零寫入 ----
    issue = runner.run_json(
        ["issue", "view", str(issue_number), "--repo", owner_repo,
         "--json", "number,title,body,state,url"]
    )
    list_body = issue.get("body") or ""
    if _already_card_body(list_body):
        print(
            f"[open] 拒絕（未寫入任何狀態）：{args.from_issue} 的 body 已經是卡面"
            "（帶有路由行版本標記或卡面表單哨兵），⛔ 不是待審清單項。\n"
            + _resume_runbook(owner_repo, issue_number),
            file=sys.stderr,
        )
        return 2
    missing = missing_requirements(list_body)
    if missing:
        print(
            f"[open] 拒絕（未寫入任何狀態）：{args.from_issue} 缺收件表單欄位 "
            f"{missing}——五條件各一欄，缺任一項即退回提案者補"
            "（stage-rules/list-intake-requirements.md，⛔ PM 不代填）。\n"
            + remediation(args.from_issue, missing),
            file=sys.stderr,
        )
        return 2

    project = resolve_project(runner, target.owner, target.project)
    existing = list_items(runner, project)
    if find_item_by_card_id(existing, card.card_id):
        print(
            f"[open] 拒絕：卡ID {card.card_id} 已存在於 project {target.owner}/{target.project}",
            file=sys.stderr,
        )
        return 3
    # ⭐ 清單項的定義是「**不在** Project #4 的 issue」（決議紀錄 §四逐字）。
    # 已在板上的 issue 就是卡，⛔ 不得再升級一次——那會產生第二個卡ID 指向同一份 body。
    for snap in existing:
        if snap.issue_url == args.from_issue:
            print(
                f"[open] 拒絕：{args.from_issue} 已在 project "
                f"{target.owner}/{target.project} 上（item_id={snap.item_id}）"
                f"，⇒ 它已經是卡、⛔ 不是待審清單項。",
                file=sys.stderr,
            )
            return 3

    # ⭐ 欄位 schema 的準備**刻意擺在上面那三道拒收之後**。
    #
    # (a) 刻意如此：讀起來像「為什麼不跟 `resolve_project` 放一起」，答案是不能。
    # (b) 為什麼：`ensure_fields` 不是唯讀的——缺哪個凍結欄位就送一次
    #     `gh project field-create`。擺在拒收之前，「卡ID 已存在 ⇒ rc=3」這條路
    #     就會先改掉 Project 的欄位定義，而模組頂端逐字寫著「副作用先於驗證是本
    #     repo 明令要消滅的形狀」。
    # (c) ⛔ **也不得再往後搬**：它必須留在改寫 Issue body **之前**。
    #     反過來（先改 body 再 ensure_fields）會把失敗面換成「清單項已被改寫成卡面、
    #     欄位炸了」——一個既不是清單項也不是卡的中間態，那比現在糟。
    # (d) ⛔ 不得由這行的位置推出「ensure_fields 是唯讀的」——它不是，只是往後挪了。
    fields = ensure_fields(runner, target.owner, target.project)

    body = render_issue_body(card)
    # ⭐ 升級留痕：把「這張卡是從哪個清單項升上來的」寫進 Log，並記下被覆寫的清單項
    # 原文指紋。⛔ 不寫原文全文——原文**逐位元**留在平台的 `userContentEdits` 前一版
    # （2026-08-25 實測：`#105` 截斷前後 sha256 相符），而 body 容量是有上限的資源。
    # ⚠️ 代價與 `amend` 的指紋路徑相同且刻意一致：離線讀 Log 只拿得到指紋。
    body = append_log_line(
        body,
        f"{now_iso8601()} upgrade by wf-cli → 由待審清單項 {args.from_issue} 升級；"
        f"清單項原文 sha256:{hashlib.sha256(list_body.encode('utf-8')).hexdigest()}"
        "（原文見平台 userContentEdits 前一版）。",
    )
    title = f"{card.card_id} {card.feature}"

    # 寫入順序：body → title → 上板 → 欄位。
    # body 先是因為它是**權威居所**；title 與欄位都是它的導出。
    set_item_body(runner, "Issue", None, project, owner_repo, issue_number, body)
    set_issue_title(runner, owner_repo, issue_number, title)
    item_id = add_item_to_project(runner, target.owner, target.project, args.from_issue)

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

    print(
        f"[open] 已由清單項升級為卡 {card.card_id}"
        f"（item_id={item_id}，type=Issue，issue=#{issue_number} {args.from_issue}）"
    )
    if spec_path:
        print(f"[open] git spec 檔骨架：{spec_path}")
    return 0
