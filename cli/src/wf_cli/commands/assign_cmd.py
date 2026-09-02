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

**跨 repo 歸屬閘門**（WF-WORKTREE-REPO-OWNERSHIP1 / #57）：``assign`` 是 ``wfcli`` 全域
**唯一**會寫 ``分支worktree`` 註冊欄的指令（實測全域沒有任何 ``git worktree add``）。
因此 ``wfcli`` **這條路徑上**的攔截只能掛在這裡，而且必須排在**所有寫入之前**——
拒絕時零寫入，不留「owner 已改、worktree 沒改」的半套狀態。

⚠️ **承諾範圍：本閘門承諾的是 ``wfcli assign`` 這一條路徑，不是「登記面已被保護」**
（需求方 2026-08-13 二次裁定，#57 issuecomment-5273953073）。射程外三條：人在 shell
直接跑 ``git worktree add``；有人繞過 ``wfcli`` 直接以 web UI／``gh project item-edit``／
GraphQL 改寫 ``分支worktree`` TEXT 欄；既有登記不重掃。三條皆為**已知限制而非待辦**，
逐字條款與現況見 ``registry`` 模組頂端的 danger。

**兩條軸，兩個回傳碼**（``docs/ROADMAP.md`` §1.5，需求方 2026-08-13 裁定）：

- **軸 A ``registry.check_assign_repo_ownership``（歸屬，可攜）**→ 拒絕時 ``return 5``。
  卡的 repo 只認 Issue URL；worktree 的 repo 來自 ``--worktree-source-repo`` 宣告的
  **repo slug**。兩邊都是字串，**不讀檔案系統**，所以它在任何一台機器上同值。
- **軸 B ``registry.observe_local_worktree``（本機觀測，機器局部）**→ 觀測到矛盾時
  ``return 6``。它只在「登記的路徑此刻存在、而且本身就是另一個 repo 的 worktree」時
  說得出話，其餘一律沉默或只警告。**它的沉默不是判定。**

⚠️ **``--worktree-source-repo`` 收的是 slug 不是目錄**（本輪改動）。上一版收目錄並從
它反推 repo，而目錄只在單一台機器成立——需求方 2026-08-13 查證後推翻該前提，連帶作廢
2026-08-13 那則「絕對路徑**且**明示來源」的裁定（``issuecomment-5274150740``）。
現在 ``--worktree`` 給什麼形式的路徑都不影響歸屬：**絕對與相對都不再是歸屬的證據**，
路徑的用途回到 ``cleanup``／``doctor``／看板欄位。既有登記**不回溯檢查**。

判定結果會寫進 Log（``_ownership_log_fragment``）：allow 也要留痕，否則事後沒有任何
東西說得出這筆登記的歸屬是**有人明示宣告**還是**沒人說、依預設取自卡**。

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
    parse_branch_worktree,
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
from ..registry import (
    LocalWorktreeObservation,
    RepoOwnershipVerdict,
    check_assign_repo_ownership,
    observe_local_worktree,
)
from ..resources import (
    DB_CANONICAL_ENVIRONMENTS,
    ResourceConflict,
    ResourceDeclarationError,
    detailed_conflicts,
    parse_block,
    repo_of_issue_url,
    try_parse_block,
    unregistered_db_environments,
)

TERMINAL_STATUSES = {"🏁完成", "🛑已停止"}


def is_intersection_candidate(other) -> bool:
    """交集檢查的候選母體判準（`WF-REDESIGN-W3` 驗收 4(a)）。

    ⭐ **判準是聯集，⛔ 不是替換**：``owner`` 非佔位 **OR** ``分支worktree`` 有值。
    卡面逐字寫的是「old→new」，讀成**替換**會漏放——2026-09-02 實測（活卡 55）
    舊判準 33 張、新判準 15 張、**聯集 44 張**、交集 4 張 ⇒ 替換版**漏放 29 張**。
    需求方 2026-09-02 裁定 A-3 照准聯集。

    ⚠️ **為什麼兩個都要**：``owner`` 說「有人認領」、``分支worktree`` 說「已經有一條
    分支或工作樹在動」。兩者⛔ 不互相蘊含——assign 之外還有別的路徑會寫其中一欄。
    """
    if is_owner_assigned(other.owner_field):
        return True
    branch, worktree = parse_branch_worktree(other.branch_worktree or "")
    return bool(branch or worktree)


def render_conflict_refusal(card_id: str, conflicts: list[ResourceConflict]) -> str:
    """拒絕訊息。**四要件逐條齊全**（卡面驗收 4(b)）：

    ① 哪兩個分量序列互為前綴（含**雙方卡 ID 與原始字面**）
    ② 觸發哪一來源（`resources.CONFLICT_SOURCES` 的封閉值域）
    ③ 可貼進 `wfcli amend --resources` 的收窄寫法
    ④ 本則計入 `WF-REDESIGN-W3` 驗收 3 的「補可跑補救」母體

    ⛔ **⛔ 不給 `--force`**：`registry.py:614` 先例逐字「給逃生口等於把『沒注意到』
    變成『按一下』」。⛔ 也不分級——誤判母體是**結構性 0**（前身 matcher 是嚴格字串
    相等，構造上產不出前綴誤判）。**替代逃生口＝收窄宣告**，即要件 ③。
    """
    lines = [f"[assign] 拒絕：{card_id} 的資源宣告與下列活卡衝突"]
    for c in conflicts:
        lines.append(
            f"  - {c.other_card_id}：{c.mine}  ×  {c.theirs}"
        )
        lines.append(
            f"      分量序列 {c.key_mine} 與 {c.key_theirs} 互為前綴；來源＝{c.source}"
        )
        lines.append(f"      收窄：{c.narrowing_hint()}")
    lines.append(
        "  ⇒ 改宣告後重跑（已代入實際卡 ID；引號內換成收窄後的資源清單）："
    )
    lines.append(
        f"    wfcli amend {card_id} --resources file:收窄後的路徑 "
        f"--reason '收窄資源宣告以解除與上列活卡的交集'"
    )
    return "\n".join(lines)



def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "assign", help="派工：寫 owner／worktree 註冊欄＋資源互斥交集檢查"
    )
    add_target_args(p)
    p.add_argument("card_id")
    p.add_argument("--assignee", required=True, help="新 owner（帳號／模型@工具）")
    p.add_argument("--branch", required=True)
    p.add_argument(
        "--worktree",
        required=True,
        help="worktree 的**本機路徑**，供 cleanup／doctor 與看板欄位使用。"
        "⚠️ 它**不參與跨 repo 歸屬判定**（歸屬看 --worktree-source-repo 的 slug）："
        "絕對路徑只在單一台機器成立、相對路徑不帶 repo 資訊，兩種都不是歸屬證據。"
        "因此 2026-08-12「一律絕對路徑」那條慣例對本閘門已無作用（需求方 2026-08-13 裁定）。",
    )
    p.add_argument(
        "--worktree-source-repo",
        default=None,
        metavar="OWNER/REPO",
        help="這筆登記宣告 worktree 屬於哪個 repo，收 **slug**（``owner/repo``，也接受"
        "GitHub remote／Issue URL）。**不是目錄**——給目錄會被拒絕，不會被反推。"
        "省略＝宣告「屬於卡自己的 repo」，那是絕大多數情形，所以它**不是必填**；"
        "只有真的要登記跨 repo 時才需要打，而那時它會被擋下並指向 #16 §7.1 的連結卡做法。"
        "它不是 --force：給了之後仍要通過同一組比對，指錯 repo 照樣被拒。"
        "⚠️ 它是**宣告**：本閘門不觀測、也不綁定後續真正的 git worktree add。",
    )
    p.add_argument(
        "--status", default="🔨執行中", help="assign 後的交付狀態；預設 🔨執行中"
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


def _ownership_log_fragment(
    verdict: RepoOwnershipVerdict, observation: LocalWorktreeObservation
) -> str:
    """放行時要寫進 Log 的歸屬留痕。

    **為什麼 allow 也要留痕**：``allow`` 有兩種強度差很多的來源——``explicit`` 是
    「有人明示宣告了這個 repo」，``card_repo_default`` 是「沒人說，工具依預設取自卡」。
    兩者寫進看板的結果一模一樣，事後沒有任何東西分得出來。本卡的核心正是「登記本身
    不是已驗證的歸屬事實」；既然驗不到，至少要**記下這一筆是憑什麼放行的**
    （``docs/ROADMAP.md`` §0 目標 2）。

    軸 B 的觀測碼一併記下，且**標明它是機器局部的**——Log 會被跨機器讀，不寫清楚
    這一句，下一個人就會把「這台機器沒看到問題」讀成「沒問題」。
    """
    basis = {
        "explicit": f"呼叫端以 --worktree-source-repo 明示 {verdict.worktree_repo}",
        "card_repo_default": "未明示，依預設取自卡自己的 repo",
    }.get(verdict.basis or "", f"判定來源 {verdict.basis}")
    return (
        f"跨 repo 歸屬 {verdict.worktree_repo}（{basis}；"
        "本閘門不觀測也不綁定後續的 git worktree add）；"
        f"本機觀測 {observation.code}（機器局部，沉默不代表無誤）"
    )


def run(args: argparse.Namespace) -> int:
    target = resolve_target(
        owner=args.owner, project=args.project, repo=args.repo, config=args.config
    )
    runner = default_runner
    project = resolve_project(runner, target.owner, target.project)

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
    #
    # ⚠️ **這句紀律的射程逐字是「本檔每一道會 return 非 0 或拋例外的閘門」，⛔ 不只本行
    # 底下這一道**（2026-08-27 依查核 R2-02 就地更正）：本檔一度自己違反它——
    # `card.append_log_line` 內含的寫入邊界守衛會拋 `MarkerWriteBoundaryError`，而那次
    # 呼叫排在三個 `set_field_value` **之後** ⇒ 拒收時三欄已寫。⇒ 新增任何「可能拒絕」
    # 的步驟時，判準不是「它長不長得像閘門」，而是**它會不會終止本輪**；會，就必須排在
    # `ensure_fields` 之前。
    comparison = compare_capability_to_card(item.body, args.actual_capability)
    deviation_reason = (args.capability_deviation_reason or "").strip()
    if comparison.requires_reason and not deviation_reason:
        print(f"[assign] 拒絕：{comparison.refusal_message()}", file=sys.stderr)
        return 2

    # 跨 repo 歸屬閘門（#57）。與能力閘門同理排在所有 set_field_value／set_item_body
    # 之前：拒絕時必須零寫入。它也刻意排在資源交集檢查之前——歸屬是「這張卡該不該在
    # 這個 repo 有 worktree」，比「這個 worktree 跟誰搶資源」更根本，而且它不打 API。
    #
    # 射程：擋的是這一筆歸屬**登記**。磁碟上的 git worktree add 不經過這裡，本閘門
    # 既不觀測也不阻止（模組頂端 danger）。
    #
    # 軸 A（可攜）：純字串比對，不讀檔案系統。blocked 時的 return 5 是「登記被拒」，
    # 不是「建立已被阻止」。
    ownership = check_assign_repo_ownership(
        issue_url=item.issue_url,
        worktree_source_repo=args.worktree_source_repo,
    )
    if ownership.blocked:
        print(f"[assign] 拒絕：{ownership.refusal_message()}", file=sys.stderr)
        return 5

    # 軸 B（機器局部）：路徑在這台機器上是什麼。它**不參與歸屬判定**，回傳碼刻意與
    # 軸 A 分開（6 vs 5），這樣事後從回傳碼就分得出「這筆登記的宣告錯了」與「這台
    # 機器上的路徑與宣告矛盾」。只有觀測到真實矛盾才拒絕；祖先巢狀只警告——它的證據
    # 只有「路徑座落在誰底下」，而 canonical §4.5 明文路徑由實際建立者決定。
    observation = observe_local_worktree(
        args.worktree, expected_repo=ownership.worktree_repo
    )
    if observation.refuses:
        print(f"[assign] 拒絕：{observation.message()}", file=sys.stderr)
        return 6
    if observation.action == "warn":
        print(f"[assign] {observation.message()}", file=sys.stderr)

    # ---- §4.2 座標原點：本卡歸屬必須先確立 ----
    #
    # `WF_RESOURCE_WRITESET1` §4.2 逐字：「**本卡自身歸屬無法確立**且其宣告含任何
    # `file:` 資源：`assign` **拒絕派工**，要求先轉為真 Issue。本卡的歸屬是整個比對
    # 平面的**座標原點**，座標未定時整個比對沒有意義，退回『視同同 repo』也救不了。」
    mine_repo = repo_of_issue_url(item.issue_url)
    if mine_repo is None and any(r.startswith("file:") for r in mine.resources):
        print(
            f"[assign] 拒絕：{args.card_id} 的 repo 歸屬無法由 issue_url 確立"
            f"（實際值 {item.issue_url!r}），而它宣告了 file: 資源。\n"
            "  repo 歸屬是 file: 相交判定的座標原點（WF_RESOURCE_WRITESET1 §4.2）；"
            "座標未定時整個比對沒有意義，⛔ 退回「視同同 repo」也救不了。\n"
            "  ⇒ 先把這張 DraftIssue 轉成真 Issue 再派工。看目前狀態：\n"
            f"    wfcli snapshot --owner {target.owner} --project {target.project} "
            "--out-dir /tmp/wfcli-snapshot",
            file=sys.stderr,
        )
        return 4

    # ---- db: 環境未登記 ⇒ **按字面＋stderr 警示**（驗收 4(c) 第二格）----
    # ⛔ 不擋派工：未登記只代表「本表不認得這個環境」，⛔ 不代表宣告非法
    #（非法字面在 parse_block 就被 ResourceDeclarationError 擋掉了）。
    unregistered = unregistered_db_environments(mine.resources)
    if unregistered:
        print(
            "[assign] 警告：下列 db: 資源的環境分量未登記，交集檢查**按字面**比對"
            f"（⛔ 不做別名正規化）：{'、'.join(unregistered)}。\n"
            f"  已登記的 canonical 環境：{'、'.join(DB_CANONICAL_ENVIRONMENTS)}"
            f"（別名表今日為空）。若這是別名，須先登記進 "
            "`cli/src/wf_cli/resources.py::DB_ENVIRONMENT_ALIASES`。",
            file=sys.stderr,
        )

    conflicts: list[ResourceConflict] = []
    skipped_unparseable: list[str] = []
    for other in items:
        if other.item_id == item.item_id or not other.card_id:
            continue
        if (other.delivery_status or "") in TERMINAL_STATUSES:
            continue
        if not is_intersection_candidate(other):
            continue  # 既未認領、也沒有分支／工作樹在動 ⇒ 無實際執行中的東西可爭資源
        other_decl = try_parse_block(other.body)
        if other_decl is None:
            skipped_unparseable.append(other.card_id)
            continue
        conflicts.extend(
            detailed_conflicts(
                mine,
                other.card_id,
                other_decl,
                mine_repo=mine_repo,
                other_repo=repo_of_issue_url(other.issue_url),
            )
        )

    if skipped_unparseable:
        print(
            "[assign] 警告：以下活卡沒有可解析的資源宣告，交集檢查略過它們（不擋派工）："
            + "、".join(skipped_unparseable),
            file=sys.stderr,
        )

    if conflicts:
        print(render_conflict_refusal(args.card_id, conflicts), file=sys.stderr)
        return 4

    branch_worktree = format_branch_worktree(args.branch, args.worktree)

    # ⭐ **Log 行的組裝與寫入邊界守衛刻意排在所有遠端寫入之前**
    #    （WF-MARKER-WRITE-BOUNDARY1，2026-08-27 依查核 R2-02
    #    `guard-runs-after-remote-writes-half-write`）。
    #
    # (a) 現在的行為：`append_log_line` 是**純函式**，它內含的寫入邊界守衛在這裡就跑完；
    #     拒收時本輪一次遠端呼叫都還沒發出。
    # (b) 為什麼非搬不可：改動前它排在 `ensure_fields` 與三個 `set_field_value` 之後
    #     ——密封探針實測，守衛拋 `MarkerWriteBoundaryError` 時 body 沒壞，⛔ 但
    #     owner／分支worktree／交付狀態**三欄已全部寫入** ⇒ 留下「欄位已寫、Log 未寫」
    #     的半寫狀態。`templates/handoff-contract.md` §3.2 明訂拒收必須發生在**任何**
    #     遠端寫入之前，而本檔上方四道閘門的就地註解也逐字寫著「拒絕時必須零寫入」
    #     ——⛔ 同一個檔在這一格違反了它自己寫的紀律。
    # (c) ⛔ **不得由此推出「assign 的所有拒收路徑都零寫入」**：本段只管 gh 側，且只管
    #     到 `set_item_body` 為止。`set_item_body` 自己失敗仍會留下「三欄已寫、body 未
    #     更新」——那一格由重跑收斂，⛔ 不在本次改動的射程內。
    # ⛔ **也不得把這幾行搬回 `set_field_value` 之後**：搬回去等於把上面 (b) 的半寫狀態
    #     原樣復原，而它是一個 critical finding，不是風格偏好。
    log_line = (
        f"{now_iso8601()} assign by wf-cli → owner {args.assignee}；"
        f"分支worktree {branch_worktree}；交付狀態 {args.status}；"
        f"{comparison.log_fragment(deviation_reason)}；"
        f"{_ownership_log_fragment(ownership, observation)}。"
    )
    new_body = append_log_line(item.body, log_line)

    # ⭐ 欄位 schema 的準備**刻意擺在上面全部四道閘門之後**（能力／跨 repo 歸屬／
    # 本機觀測／資源交集），而不是跟 `resolve_project` 放一起。
    #
    # (a) 刻意如此。
    # (b) 為什麼：`ensure_fields` 不是唯讀的——缺凍結欄位就送 `gh project field-create`。
    #     擺在閘門前，被拒收的 assign（rc=2／4／5／6）仍會先改掉 Project 的欄位定義，
    #     而那幾道閘門的就地註解逐字寫著「拒絕時必須零寫入」。
    #     ⚠️ 這個位置**不是**因為有人主張早建欄位有好處：實查，它原本在
    #     `resolve_project` 旁邊只是沿用 2026-08-04 五動詞的建檔樣板，**沒有任何
    #     決策紀錄**；`test_commands_mocked.py` 那段常被引作理由的註解，主詞是
    #     「該測試的保證範圍與用詞強度」，⛔ 全段沒有一句主張早建欄位有好處。
    # (c) ⛔ 不得由此推出「所有 gh 寫入都可以往後搬」：能搬的唯一理由是
    #     `resolve_project` 到本行之間對 `fields` 這個名字的讀取次數是 0
    #     ——上面四道閘門吃的是 `item`（欄位**值**），⛔ 不吃欄位**定義**。
    #     ⛔ 也不得推出「ensure_fields 已是唯讀」——它不是，只是往後挪了。
    fields = ensure_fields(runner, target.owner, target.project)
    set_field_value(runner, project, item.item_id, fields["owner"], args.assignee)
    set_field_value(runner, project, item.item_id, fields["分支worktree"], branch_worktree)
    set_field_value(runner, project, item.item_id, fields["交付狀態"], args.status)
    set_item_body(runner, item.content_type, item.content_id, project, target.repo, item.issue_number, new_body)

    print(
        f"[assign] 已指派 {args.card_id} → {args.assignee}（{branch_worktree}）；"
        f"{comparison.log_fragment(deviation_reason)}"
    )
    return 0
