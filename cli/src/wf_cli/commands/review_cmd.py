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

## escalation 帳（WF-22-CLI4 切片 A）

本指令自此以 **lifecycle writer** 身分標記 ``accepted``、把 ``status`` 記為 ``open``
（§2：新採認的 blocking finding 以 open 開始），並依 §3 推導 ``counts_toward_escalation``
寫進留言的結構化區塊與 Log 索引行。reviewer 自填的這三個鍵仍一律警示並忽略。

§3 第 1 款（preflight）**不是閘門**，是一個由 writer 加蓋到事件上的導出值
（``preflight_basis_binding``）。今天恆為 ``structurally-unavailable``：本 repo 沒有受管轄的
preflight pass event writer，也沒有該事件的可驗證格式，故該款無從成立，本指令寫出的每一則
裁決都帶 ``escalation_account: not-asserted``（不對帳作斷言），並**缺** §5「Adapter 必填欄位」的
``preflight_passed: true``——已知且刻意記錄的 schema 落差。

這是 WF-22-CLI4-R4-01 的處置＋需求方 2026-08-12 的裁定：上一輪把「有沒有依據」交給一個讀
留言內文的讀取器，任意四欄 YAML 就能解鎖（留言內文判定不出 canonical §4.1 的「受管轄」，
那是通道屬性）；本輪刪掉讀取器，但**不改成恆拒**——恆拒會讓狀態面再次分不出「已查核」與
「未查核」，那是 WF-25-REVIEW-WRITE-CHANNEL1（ai-workflow#13）解過的問題。正解是照寫並
把恆虛性寫在事件上。

寫入前另有三道 fail-closed 閘門（全部走 exit 2，未寫入任何遠端狀態）：

1. **``attempt_id`` 去重**：同一 attempt 已存在即拒。必須擋在寫入前——``doctor.py``
   對重複 attempt 判 ``marker_quarantined``，而該隔離的解除表示法未定義（#30）。
2. **帳可重建**：cutover（``contract-baseline``）之後的留痕若有讀不懂的 marker，或
   review event 缺結構化 counts 事實，一律拒絕；**未知不得推定為不計數**
   （語意見 review-escalation.md §5「cutover 前歷史事件維持原貌」）。
3. **checkpoint 漏建**：上一個可計數 attempt 序位 ≥3 卻找不到對應 checkpoint 即拒。
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
    derive_counts_toward_escalation,
    derive_preflight_basis_binding,
    parse_structured_block,
    render_verdict_comment,
)
from ..validation import (
    ValidationError,
    build_accepted_marks,
    build_issue_event_history,
    check_attempt_not_duplicated,
    check_checkpoint_gate,
    counted_attempts,
    derive_preflight_basis,
    review_invalid_reasons,
    unasserted_attempts,
    validate_accepted_overrides,
    validate_marked_by,
    validate_review_report,
    validate_source_sha,
)

AWAITING_REVIEW_STATUS = "🔍待查核"


def fetch_issue_comments(runner, repo: str, issue_number: int) -> list[dict]:
    """讀回 Issue 的留言（唯讀）。依 ``gh`` 回傳順序，即建立順序。

    刻意不放 ``project.py``：那是 Projects v2 adapter，而留言屬 Issue timeline；且
    ``project.py`` 不在本卡宣告的寫入集內。``runner`` 只需具備 ``run_json``（鴨子型別），
    因此本函式不引入任何新的模組相依。
    """
    data = runner.run_json(
        ["issue", "view", str(issue_number), "--repo", repo, "--json", "comments"]
    )
    return list((data or {}).get("comments") or [])


def resolve_platform_login(runner) -> str:
    """``accepted=false`` 標記者的平台身分：``gh api user --jq .login``。

    刻意不接受自陳字串：``--reviewer`` 那一欄只驗非空（handoff-contract.md §3.1.1
    明記此洞），身分維度上等同無佐證；撤銷採認是把 finding 移出 open set 的動作，
    不能靠自述成立。
    """
    return runner.execute(["api", "user", "--jq", ".login"]).strip()


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
        "--mark-not-accepted",
        action="append",
        default=[],
        metavar="FINDING_ID=理由",
        help="把某個 finding 標為 accepted=false（預設全部 true，見 review-escalation.md §2）；"
        "理由必填，標記者身分取自 `gh api user`。可重複給。",
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
        print(
            "[review] 拒絕：--reviewer 不得為空（裁決必須可歸屬到查核者）\n"
            "  ⇒ 補上查核者後重跑（已代入你本次給的卡 ID；引號內換成真的查核者）：\n"
            f"    wfcli review {args.card_id} --reviewer '查核者的帳號或模型@工具'",
            file=sys.stderr,
        )
        return 2
    if args.escalation_epoch < 0:
        print(
            f"[review] 拒絕：--escalation-epoch 不得為負（收到 {args.escalation_epoch}）；"
            "epoch 只能由 escalation-epoch-change 逐一遞增（review-escalation.md §4）。\n"
            "  ⇒ 先看這張卡目前在第幾個 epoch（已代入實際卡 ID）：\n"
            f"    wfcli doctor --owner {args.owner} --project {args.project}",
            file=sys.stderr,
        )
        return 2

    try:
        raw_text = _read_input(args.input)
        data = parse_structured_block(raw_text)
    except ReviewParseError as exc:
        print(
            f"[review] 拒收：{exc}\n"
            + "  ⇒ 旗標與值域（可整行複製）：\n"
            "    wfcli review --help",
            file=sys.stderr,
        )
        return 2

    # review-invalid 先判：它在 §1 是獨立層次（不計 iteration、不建立 attempt），
    # 與「格式不合」的處置不同，必須能被呼叫端用退出碼分辨。
    invalid = review_invalid_reasons(data)
    if invalid:
        print(
            "[review] 拒收（review-invalid，不計 iteration、卡片狀態不變）：\n"
            + "  ⇒ 契約原文在本 repo 內，⛔ 不必連網：\n"
            "    git show HEAD:stage-rules/review.md",
            file=sys.stderr,
        )
        for reason in invalid:
            print(f"  - {reason}", file=sys.stderr)
        return 4

    try:
        report = validate_review_report(data)
    except ValidationError as exc:
        print(
            "[review] 拒收：查核輸出不符契約（未寫入任何遠端狀態）\n"
            + "  ⇒ 契約原文在本 repo 內，⛔ 不必連網：\n"
            "    git show HEAD:stage-rules/review.md",
            file=sys.stderr,
        )
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
    try:
        overrides = validate_accepted_overrides(args.mark_not_accepted, report.findings)
    except ValidationError as exc:
        print(
            "[review] 拒收：accepted 標記不合格（未寫入任何遠端狀態）\n"
            + "  ⇒ 契約原文在本 repo 內，⛔ 不必連網：\n"
            "    git show HEAD:stage-rules/review.md",
            file=sys.stderr,
        )
        for error in exc.errors:
            print(f"  - {error}", file=sys.stderr)
        return 2

    if args.validate_only:
        print(
            f"[review] 驗證通過（--validate-only，未寫入任何狀態）："
            f"{report.review_result}／core_pain_resolved={report.core_pain_resolved}／"
            f"self_run {len(report.self_run)} 項／findings {len(report.findings)} 項"
        )
        print(
            "[review] 注意：--validate-only 不連 GitHub，因此去重、帳可重建與 checkpoint "
            "三道閘門都未執行；實寫時才會檢查。⚠️ 另請知悉：實寫時 preflight_basis_binding "
            "今天恆為 structurally-unavailable（本 repo 沒有受管轄的 preflight pass event "
            "writer 與可驗證格式），故該則裁決會帶 escalation_account: not-asserted、"
            "不對 escalation 帳作任何斷言。查核輸出的格式與契約檢查在此已完整跑過。",
            file=sys.stderr,
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
            "（或設定檔 repo／環境變數 WFCLI_REPO）。\n"
            "  ⇒ 目前這台機器上的預設 repo 是哪一個：\n"
            "    git remote get-url origin",
            file=sys.stderr,
        )
        return 2

    runner = default_runner
    project = resolve_project(runner, target.owner, target.project)

    items = list_items(runner, project)
    item = find_item_by_card_id(items, args.card_id)
    if not item:
        print(f"[review] 找不到卡 {args.card_id}", file=sys.stderr)
        return 3
    if item.content_type != "Issue" or item.issue_number is None:
        print(
            f"[review] 拒絕：卡 {args.card_id} 是 Project draft item，沒有可留言的 Issue timeline；"
            "請先以真實 repo Issue 承載此卡（canonical §4.3：卡狀態＝Issue）。\n"
            "  ⇒ 先看這張 draft item 現在的內容（已代入實際 owner 與 project）：\n"
            f"    wfcli snapshot --owner {args.owner} --project {args.project} "
            "--out-dir /tmp/wfcli-snapshot",
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

    # ---- 寫入前的閘門（全部 fail-closed，未寫入任何遠端狀態）----
    target_attempt = attempt_id(args.card_id, args.escalation_epoch, args.source_sha)
    comments = fetch_issue_comments(runner, target.repo, item.issue_number)
    history = build_issue_event_history(comments)
    # §3 第 1 款的依據：**刻意不掃留言**——留言內文判定不出 canonical §4.1 的「受管轄」，
    # 上一輪就是在這裡放了一個讀取器而讓任意四欄 YAML 解鎖（R4-01）。本 repo 今天恆回
    # not-established，其恆虛性由 render_verdict_comment 以
    # preflight_basis_binding: structurally-unavailable 加蓋進事件（需求方 2026-08-12
    # 裁定：保留寫入能力，把空虛性寫進事件，而不是拒寫）。
    preflight = derive_preflight_basis(card_id=args.card_id, source_sha=args.source_sha)
    try:
        check_attempt_not_duplicated(history, target_attempt)
        check_checkpoint_gate(
            history, escalation_epoch=args.escalation_epoch, card_body=item.body
        )
    except ValidationError as exc:
        print(
            "[review] 拒絕（未寫入任何遠端狀態）：升級 checkpoint 閘門未過。\n"
            "  ⇒ 先看這張卡已有哪些 checkpoint 事件（已代入實際 repo 與編號）：\n"
            f"    gh issue view {item.issue_number} --repo {target.repo} --comments",
            file=sys.stderr,
        )
        for error in exc.errors:
            print(f"  - {error}", file=sys.stderr)
        return 2

    marked_by = ""
    if overrides:
        marked_by = resolve_platform_login(runner)
        try:
            validate_marked_by(marked_by, item.owner_field)
        except ValidationError as exc:
            print(
                "[review] 拒絕（未寫入任何遠端狀態）：accepted 標記的署名不合格。\n"
                "  ⇒ 確認你現在是以哪個帳號在操作：\n"
                "    gh api user --jq .login",
                file=sys.stderr,
            )
            for error in exc.errors:
                print(f"  - {error}", file=sys.stderr)
            return 2

    marks = build_accepted_marks(
        report.findings,
        overrides,
        marked_by,
        owner_field=item.owner_field,
        # handoff-contract.md §5 的「被授權的 review event writer 帳號集合」在本 repo
        # 仍是未填的樣板佔位，故傳 None——導出值因此恆為 structurally-vacuous，而那正是
        # 要被寫進事件流的事實（review-escalation.md §4／§5 同型處理，ai-workflow#39）。
        # 本 CLI 不代為解析該樣板：那是跨檔的契約宣告，應由專案自己的設定承載。
        authorized_writers=None,
    )

    timestamp = now_iso8601()
    comment = render_verdict_comment(
        card_id=args.card_id,
        report=report,
        source_sha=args.source_sha,
        reviewer=args.reviewer,
        escalation_epoch=args.escalation_epoch,
        timestamp=timestamp,
        accepted_marks=marks,
        preflight=preflight,
        # current-state 平面的時點快照（見 review.render_escalation_facts_block 的說明）。
        # 每次 handoff 都會覆寫這一欄，故它只有在 append-only 的事件留言裡才留得住；
        # 但留住的是「寫裁決那一刻該欄長什麼樣」，不是 attempt 的固有屬性。
        owner_field_at_verdict_write=item.owner_field,
    )
    binding = derive_preflight_basis_binding(preflight)
    counts = (
        derive_counts_toward_escalation(report, marks, preflight)
        if preflight.established
        else None
    )
    # Log 索引行同樣不得把「未斷言」寫成 false——那是洗白（R3 的原話）。
    counts_text = (
        f"counts_toward_escalation {'true' if counts else 'false'}"
        if counts is not None
        else f"escalation_account not-asserted（preflight_basis_binding {binding}）"
    )
    log_line = (
        f"{timestamp} review by wf-cli → {report.review_result}"
        f"（{report.delivery_status}）；查核者 {args.reviewer}；"
        f"core_pain_resolved {report.core_pain_resolved}；"
        f"self_run {len(report.self_run)} 項；findings {len(report.findings)} 項"
        f"（blocking {len(report.blocking_findings)}）；"
        f"{counts_text}；"
        f"attempt {target_attempt}。"
    )
    # ⭐ **本行以上全是純計算，第一次遠端寫入在本行以下**
    #    （WF-MARKER-WRITE-BOUNDARY1，2026-08-27 依查核 R2-02
    #    `guard-runs-after-remote-writes-half-write`）。
    #
    # (a) 現在的行為：`append_log_line` 內含的寫入邊界守衛在這裡跑完；拒收時本輪一次
    #     遠端呼叫都還沒發出（裁決留言沒發、交付狀態沒翻、body 沒動）。
    # (b) 為什麼非搬不可：改動前 `ensure_fields`／`add_issue_comment`／`set_field_value`
    #     三者都排在本行之前 ⇒ 守衛拒收時，板上已經留下一則裁決留言、交付狀態也已翻，
    #     ⛔ 而 Log 沒有對應的 `review` 事件。§3.2 明訂拒收必須發生在**任何**遠端寫入
    #     之前，`doctor` 的狀態面漂移稽核也會把那種卡報成不一致。
    # (c) ⛔ **不得由此推出「留言與翻狀態的相對順序可以動」**——⛔ 不可以，見下方那段。
    #     本次只把**整組**遠端寫入往後搬到守衛之後，組內順序逐字不變。
    new_body = append_log_line(item.body, log_line)

    # ⭐ 欄位 schema 的準備**刻意擺在上面全部拒收之後**（缺 repo rc=2／找不到卡 rc=3／
    # draft item rc=2／去重與 checkpoint rc=2／marked_by 身分 rc=2／⭐ 寫入邊界拒收），
    # 而不是跟 `resolve_project` 放一起。
    #
    # (a) 刻意如此。
    # (b) 為什麼：`ensure_fields` 不是唯讀的——缺凍結欄位就送 `gh project field-create`。
    #     上面那幾條的就地訊息逐字寫著「未寫入任何遠端狀態」；擺在它們之前，那句話
    #     對缺欄位的 Project 就是假的。本行的位置是「最後一道拒收之後、第一次寫入
    #     （`add_issue_comment`）之前」，⇒ 兩邊的保證同時成立。
    #     ⚠️ 2026-08-27 更正：「最後一道拒收」現在是**寫入邊界守衛**（在 `append_log_line`
    #     內），⛔ 不再是 `marked_by` 身分那一條——本行因此連同整組寫入一起往後搬。
    # (c) ⛔ 不得再往後搬到 `add_issue_comment` 之後：先留言、後翻狀態的順序是刻意的
    #     （反過來留言失敗會留下沒有裁決全文的 ✅通過），而欄位定義必須在
    #     `set_field_value` 之前就緒 ⇒ 本行只能在這兩者之間。
    # (d) ⛔ 不得由此推出「ensure_fields 已是唯讀」——它不是，只是往後挪了。
    fields = ensure_fields(runner, target.owner, target.project)
    # 先留言、後翻狀態：反過來若留言失敗，板上會出現沒有裁決全文的 ✅通過，
    # 那正是本卡要消滅的「宣稱與證據脫節」。
    add_issue_comment(runner, target.repo, item.issue_number, comment)
    set_field_value(runner, project, item.item_id, fields["交付狀態"], report.delivery_status)
    set_item_body(
        runner, item.content_type, item.content_id, project, target.repo, item.issue_number, new_body
    )

    print(
        f"[review] 已寫入裁決 {args.card_id} → {report.review_result}"
        f"（交付狀態={report.delivery_status}，留言於 #{item.issue_number}）"
    )
    if overrides:
        print(
            "[review] accepted=false 標記："
            + "、".join(f"{fid}（marked_by={marked_by}）" for fid in sorted(overrides))
        )
    if report.review_result == "REQUEST_CHANGES":
        print(
            "[review] iteration 不由本指令遞增：請以 "
            "`wfcli handoff --next-stage implementation` 把卡交回執行者，"
            "遞增在該處發生（WF-22-CLI2 既有規則）"
        )
    if counts is None:
        prior = len(unasserted_attempts(history, args.escalation_epoch)) + 1
        print(
            f"[review] ⚠️ preflight_basis_binding={binding}：本則裁決**不對 escalation 帳"
            f"作任何斷言**（escalation_account: not-asserted），本 epoch 累計 {prior} 個"
            "未斷言 attempt。本 repo 沒有受管轄的 preflight pass event writer 與可驗證格式，"
            "故 §3 第 1 款無從成立——自動計數（**含三振門檻**）在承接卡落地前不可用，"
            "請勿把「沒有可計數 attempt」讀成「執行者沒有累計」。"
            "本事件另缺 review-escalation.md §5「Adapter 必填欄位」的 preflight_passed: true，"
            "屬已知且刻意記錄的 schema 落差（登記於 docs/CONSUMER_CONFORMANCE.md）。",
            file=sys.stderr,
        )
    if counts:
        ordinal = len(counted_attempts(history, args.escalation_epoch)) + 1
        print(
            f"[review] counts_toward_escalation=true：本輪是本 epoch 第 {ordinal} 個可計數 attempt。"
        )
        if ordinal >= 3:
            print(
                "[review] ⚠️ review-escalation.md §4：第三個及其後每個可計數 attempt 出現時"
                "**先建立 escalation-checkpoint**，不得只按整數直接寫 🚨已升級。請執行："
                f"`wfcli checkpoint {args.card_id} --trigger-attempt-id {target_attempt} "
                f"--unique-attempt-count {ordinal} --escalation-epoch {args.escalation_epoch} "
                "--decision <continue|replan|change-executor|escalate> --rationale <理由>`。"
                "下一輪裁決寫入前若仍缺此 checkpoint，`wfcli review` 會拒絕。"
            )
    return 0
