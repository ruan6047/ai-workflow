"""doctor：對帳（git worktree list vs 卡註冊、submodule 未初始化、殘留 lease、
孤兒分支、prunable worktree）。全程唯讀——本卡刻意不實作任何回收／清理動作
（見卡面紅線 3：破壞性操作必須先列清單再執行；本 CLI v1 只做「列清單」那一半，
清理是另一個未來、需要明確人工核可的獨立指令，不混進 doctor）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re
from typing import Any, Literal

from . import git_ops
from .card import now_iso8601
from .registry import RegisteredCard, TasksMdRegistry

WorktreeClass = Literal[
    "registered_active", "orphan_prunable", "orphan_untracked", "detached_sandbox"
]


@dataclass
class WorktreeFinding:
    path: str
    branch: str | None
    head_sha: str | None
    classification: WorktreeClass
    detail: str
    card_id: str | None = None

    @property
    def is_orphan(self) -> bool:
        return self.classification.startswith("orphan")


@dataclass
class SubmoduleFinding:
    path: str
    status: Literal["ok", "uninitialized", "out_of_sync"]
    sha: str
    detail: str


@dataclass
class BranchFinding:
    branch: str
    merged_into_main: bool | None
    detail: str


@dataclass
class LeaseFinding:
    card_id: str
    owner: str | None
    worktree_path: str | None
    reason: str
    age_hours: float | None = None


@dataclass(frozen=True)
class ReviewChannelFinding:
    """同一 source SHA 的「外部收據」與 control-plane review event 對帳結果。

    這裡刻意不把缺收據解讀成「查核沒做」。外部工具內的行為在沒有可讀收據時
    不可觀測；doctor 只能誠實地指出狀態面尚不能證明裁決已被轉錄。
    """

    status: Literal[
        "recorded", "receipt_untranscribed", "unobservable", "marker_quarantined"
    ]
    card_id: str
    source_sha: str
    detail: str
    receipt_urls: tuple[str, ...] = ()
    receipt_authors: tuple[str, ...] = ()
    quarantine_reasons: tuple[str, ...] = ()


@dataclass
class DoctorReport:
    repo_root: str
    generated_at: str
    registry_sources: list[str]
    worktrees: list[WorktreeFinding] = field(default_factory=list)
    submodules: list[SubmoduleFinding] = field(default_factory=list)
    orphan_branches: list[BranchFinding] = field(default_factory=list)
    stale_leases: list[LeaseFinding] = field(default_factory=list)

    def orphan_worktrees(self) -> list[WorktreeFinding]:
        return [w for w in self.worktrees if w.is_orphan]

    def render_text(self) -> str:
        lines = [
            f"doctor 對帳報告 — {self.repo_root}",
            f"時間：{self.generated_at}",
            f"卡註冊來源：{', '.join(self.registry_sources) or '（無；僅本機 git 檢查）'}",
            "",
            "## 1. git worktree list vs 卡註冊",
        ]
        if not self.worktrees:
            lines.append("（無額外 worktree，僅主工作樹）")
        for w in self.worktrees:
            tag = {
                "registered_active": "OK",
                "orphan_prunable": "孤兒／PRUNABLE",
                "orphan_untracked": "孤兒／未註冊",
                "detached_sandbox": "detached（略過，非孤兒）",
            }[w.classification]
            branch_s = w.branch or "(detached)"
            lines.append(f"- [{tag}] {w.path}  分支={branch_s}  {w.detail}")
        lines.append("")
        lines.append("## 2. submodule 初始化狀態")
        if not self.submodules:
            lines.append("（無 submodule）")
        for s in self.submodules:
            lines.append(f"- [{s.status}] {s.path}  {s.detail}")
        lines.append("")
        lines.append("## 3. 孤兒分支（無 worktree 且未見於卡註冊）")
        if not self.orphan_branches:
            lines.append("（無）")
        for b in self.orphan_branches:
            merged = "已併入 main" if b.merged_into_main else (
                "未併入 main" if b.merged_into_main is False else "併入狀態未知"
            )
            lines.append(f"- {b.branch}（{merged}）{b.detail}")
        lines.append("")
        lines.append("## 4. 殘留 lease（owner 已認領但跡象顯示遺棄）")
        if not self.stale_leases:
            lines.append("（無）")
        for lease in self.stale_leases:
            age = f"，已 {lease.age_hours:.1f} 小時未交接" if lease.age_hours is not None else ""
            lines.append(f"- {lease.card_id}（owner={lease.owner}）{lease.reason}{age}")
        lines.append("")
        n_orphan = len(self.orphan_worktrees())
        lines.append(
            f"摘要：{len(self.worktrees)} 個額外 worktree，{n_orphan} 個孤兒；"
            f"{len(self.orphan_branches)} 個孤兒分支；{len(self.stale_leases)} 個殘留 lease 疑慮。"
        )
        return "\n".join(lines)


# --------------------------------------------------------------------------
# wf-review-event:v1 marker 合規檢查（handoff-contract.md §3.1.3／§3.1.4）
# --------------------------------------------------------------------------
#
# 契約自 2026-08-10 起要求：受管轄但不合格的 marker 必須讓該卡停止自動裁決判定，
# 不得回退到 legacy 分支。先前實作對五種不合格 marker 全數回傳 recorded——契約寫著
# fail-closed、消費者實際 fail-open，那比沒有契約更危險，因為它讓人以為有閘門。
#
# legacy 的判準是**語法**：完全不含 `wf-review-event:` 前綴的舊裁決留言，行為完全
# 不變。只要出現該前綴，該留言即宣告自己受契約管轄，不合格就得停機。契約明文承認
# 一個保守誤判：在留言中「引用」該字樣（例如討論契約本身）會被判為受管轄而停機。
# 那是往 fail-closed 方向的誤判，予以接受。

_EVENT_PREFIX = "wf-review-event:"

# 一次把「順序固定、單一空白分隔、鍵集合封閉」三件事編碼進同一條 regex：
# 多出未定義鍵會讓 `attempt_id=(\S+) -->` 對不上（中間多一個空白段），錯序同理。
_CONFORMANT_MARKER_RE = re.compile(
    r"^<!-- wf-review-event:v1 "
    r"card_id=(?P<card>\S+) source_sha=(?P<sha>[0-9a-f]{40}) attempt_id=(?P<attempt>\S+) -->$"
)
_ATTEMPT_RE = re.compile(r"^(?P<card>.+)-e(?P<epoch>\d+)-(?P<sha>[0-9a-f]{40})$")


def inspect_event_marker(body: str) -> tuple[str | None, str | None]:
    """檢查一則留言的 marker 合規性。

    回傳 ``(attempt_id, 不合格原因)``：兩者恰有一個為 None。留言未宣告受管轄時
    兩者皆 None——那是 legacy，不歸本檢查管。

    **marker 必須恰為留言首行**（契約 §3.1.3：「marker 置於留言首行」），且整則
    留言只能出現一處前綴。先前版本掃描所有行找 marker，導致三種 fail-open：
    marker 埋在散文之後仍被採信、前導空白仍被採信、以及最嚴重的——**包在 code
    fence 裡的示範 marker 被當成真事件**。示範與引用必須落在 fail-closed 那一側，
    不能因為「找得到一行長得像 marker」就放行。
    """
    if _EVENT_PREFIX not in body:
        return None, None
    lines = body.splitlines()
    first = lines[0] if lines else ""
    if not first.startswith("<!-- " + _EVENT_PREFIX):
        # 前綴出現在別處：內文引用、code fence 示範，或 marker 沒放在首行。
        # 一律停機——契約承認這個保守誤判，方向是 fail-closed。
        return None, (
            "留言含 `wf-review-event:` 前綴但**首行不是 marker**"
            "（契約要求 marker 置於留言首行；內文引用、code fence 示範、"
            "前導空白皆屬此類）"
        )
    extra = sum(1 for line in lines if _EVENT_PREFIX in line) - 1
    if extra > 0:
        return None, (
            f"留言首行是 marker，但另有 {extra} 處 `wf-review-event:` 前綴；"
            "一則事件一則留言，無法判斷哪一個才算數"
        )
    line = first
    if not line.startswith("<!-- wf-review-event:v1 "):
        version = line.split()[1] if len(line.split()) > 1 else line
        return None, f"未知或不支援的 marker 版本：{version}（只認 v1；不得回退 legacy）"
    match = _CONFORMANT_MARKER_RE.match(line)
    if not match:
        return None, (
            "marker 不符 v1 語法：必須恰為 card_id／source_sha／attempt_id 三鍵、"
            "依序排列、以單一空白分隔（缺欄、多出未定義鍵、錯序皆屬此類）"
        )
    attempt = match.group("attempt")
    decomposed = _ATTEMPT_RE.match(attempt)
    if not decomposed:
        return None, f"attempt_id 不符 `<card>-e<epoch>-<40 hex sha>` 形式：{attempt}"
    if decomposed.group("card") != match.group("card") or decomposed.group("sha") != match.group("sha"):
        return None, (
            "marker 三欄不自洽：attempt_id 反解出的 card_id／source_sha "
            f"（{decomposed.group('card')}／{decomposed.group('sha')}）"
            f"與欄位值（{match.group('card')}／{match.group('sha')}）不符"
        )
    return attempt, None


def audit_review_channel(
    comments: list[dict[str, Any]],
    card_id: str,
    source_sha: str,
    *,
    card_body: str = "",
    reviews: list[dict[str, Any]] | None = None,
) -> ReviewChannelFinding:
    """唯讀比對 Issue timeline 上的收據與 wfcli review event。

    收據是外部查核者在 GitHub Issue/PR conversation 留下的非狀態證據，固定格式：
    ``<!-- wf-review-receipt:v1 ... -->``。其 GitHub comment author 是平台可驗證
    身分；其中的模型／工具文字不是身分證明。wfcli review event 仍是唯一狀態寫入。
    """
    receipt_urls: list[str] = []
    receipt_authors: list[str] = []
    receipt_marker = "<!-- wf-review-receipt:v1"
    attempt_pattern = re.compile(
        rf"{re.escape(card_id)}-e\d+-{re.escape(source_sha)}"
    )
    state_marker = "## 查核裁決："

    def log_indexes(attempt: str) -> bool:
        """Issue body 的 ``## Log`` 是否有**對應同一 attempt_id** 的 review 索引行。

        契約 §3.1.3 的三面一致要求「Log 中對應**同一 attempt_id** 的
        `review by wf-cli` 索引行」。先前實作把它拆成兩個獨立的全文檢查
        （`"review by wf-cli" in card_body` 與 attempt 正則各自 search），
        因此兩種 fail-open：Log 索引的是 e0 卻讓 e1 的事件過關；以及 attempt
        出現在 assign 行、`review by wf-cli` 出現在另一行也算數。索引行必須是
        **同一行同時含兩者**，否則它索引的根本不是這個事件。
        """
        return any(
            "review by wf-cli" in line and attempt in line
            for line in card_body.splitlines()
        )

    def receipt_matches(body: str) -> bool:
        """收據的 card_id／source_sha 須整行相等，不可用子字串比對。

        `"card_id: CARD-A" in "card_id: CARD-AB"` 為真——稽核 CARD-A 時會把
        CARD-AB 的收據算成自己的，進而回報一份不存在的收據等待轉錄。
        """
        lines = [line.strip() for line in body.splitlines()]
        return f"card_id: {card_id}" in lines and f"source_sha: {source_sha}" in lines

    expected_attempt_prefix = f"{card_id}-e"
    expected_attempt_suffix = f"-{source_sha}"
    quarantine_reasons: list[str] = []
    conformant_attempts: list[str] = []
    legacy_attempts: list[str] = []

    all_comments = [*comments, *(reviews or [])]

    # 第一輪只做解析層判定。契約 §2 明定留痕解析停機是**解析層** gate，且優先於
    # 語意層裁決——讀不出 marker 就談不上這則留言算不算裁決，所以必須先掃完全部
    # 留言、確認沒有受管轄但不合格者，才輪得到「有沒有裁決」這個問題。
    for comment in all_comments:
        body = str(comment.get("body") or "")
        attempt, reason = inspect_event_marker(body)
        if reason is not None:
            url = str(comment.get("html_url") or comment.get("url") or "（URL 未提供）")
            quarantine_reasons.append(f"{reason}（{url}）")
        elif attempt is not None and attempt.startswith(expected_attempt_prefix) and attempt.endswith(expected_attempt_suffix):
            conformant_attempts.append(attempt)
        elif attempt is None and state_marker in body:
            # legacy：完全不含 wf-review-event: 前綴的舊裁決留言。判準（語法）不變，
            # 但同樣要求 Log 索引的是這一則的 attempt，而非「body 裡任何一個 attempt」。
            hit = attempt_pattern.search(body)
            if hit:
                legacy_attempts.append(hit.group(0))

    # 落差 8a：同一 attempt 多則事件。§3.1.5 在結構化裁決承載到位前的保守行為是
    # 一律停止判定——不得把重送視為安全。放行需要能證明兩則語意等價，而裁決語意
    # 目前只存在於渲染後的散文裡，證不了。
    for attempt in set(conformant_attempts):
        if conformant_attempts.count(attempt) > 1:
            quarantine_reasons.append(
                f"同一 attempt_id 出現 {conformant_attempts.count(attempt)} 則事件"
                f"（{attempt}）；在可驗證語意等價的機制到位前一律停機，不得推定為冪等重送"
            )

    if quarantine_reasons:
        return ReviewChannelFinding(
            status="marker_quarantined",
            card_id=card_id,
            source_sha=source_sha,
            detail=(
                "timeline 上有受契約管轄但不合格的 review marker，依 handoff-contract.md "
                "§3.1.4 停止本卡的自動裁決判定。這與 unobservable 不同：那是找不到訊號，"
                "這是找到訊號但讀不懂——前者要去查有沒有人查核過，後者要去修一則壞掉的留言。"
                "解除須依 review-escalation.md §5 的 review-marker-clearance；該事件在留言"
                "平面的表示法尚未定義（見 docs/CONSUMER_CONFORMANCE.md），故目前只能人工處理。"
            ),
            quarantine_reasons=tuple(quarantine_reasons),
        )

    if any(log_indexes(a) for a in [*conformant_attempts, *legacy_attempts]):
        return ReviewChannelFinding(
            status="recorded",
            card_id=card_id,
            source_sha=source_sha,
            detail="已找到同一卡、同一 attempt 的 wfcli review event 與 Issue Log；狀態面已有裁決。",
        )

    for comment in all_comments:
        body = str(comment.get("body") or "")
        if receipt_marker in body and receipt_matches(body):
            url = str(comment.get("html_url") or comment.get("url") or "（收據 URL 未提供）")
            receipt_urls.append(url)
            user = comment.get("user") or {}
            login = user.get("login") if isinstance(user, dict) else None
            receipt_authors.append(str(login or "（GitHub author 未提供）"))

    if receipt_urls:
        return ReviewChannelFinding(
            status="receipt_untranscribed",
            card_id=card_id,
            source_sha=source_sha,
            detail=(
                "找到外部查核收據，但找不到對應 wfcli review event："
                "裁決已可觀測、但尚未轉錄到狀態面；保持待查核並要求 PM 轉錄。"
            ),
            receipt_urls=tuple(receipt_urls),
            receipt_authors=tuple(receipt_authors),
        )
    return ReviewChannelFinding(
        status="unobservable",
        card_id=card_id,
        source_sha=source_sha,
        detail=(
            "找不到外部收據或 wfcli review event。這不證明查核未發生；"
            "只表示該 source_sha 的查核在系統上不可觀測，必須 fail-closed。"
        ),
    )


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def run_doctor(
    repo_root: Path,
    registry: TasksMdRegistry | None = None,
    lease_ttl_hours: float = 48.0,
    main_ref: str = "main",
) -> DoctorReport:
    repo_root = repo_root.resolve()
    active: list[RegisteredCard] = registry.active if registry else []
    archived_ids = registry.archived_card_ids if registry else set()
    by_branch: dict[str, RegisteredCard] = {rc.branch: rc for rc in active if rc.branch}

    report = DoctorReport(
        repo_root=str(repo_root),
        generated_at=now_iso8601(),
        registry_sources=[str(p) for p in (registry.source_paths if registry else [])],
    )

    # 1) worktree list vs 卡註冊 + prunable
    entries = git_ops.worktree_list(repo_root)
    for entry in entries:
        if Path(entry.path).resolve() == repo_root:
            continue  # 主工作樹本身不算「卡的 worktree」
        if entry.is_prunable:
            report.worktrees.append(
                WorktreeFinding(
                    path=entry.path, branch=entry.branch, head_sha=entry.head_sha,
                    classification="orphan_prunable",
                    detail=f"git 回報 prunable：{entry.prunable_reason}",
                )
            )
            continue
        if entry.branch is None:
            report.worktrees.append(
                WorktreeFinding(
                    path=entry.path, branch=None, head_sha=entry.head_sha,
                    classification="detached_sandbox",
                    detail="detached HEAD、非 prunable；可能是查核用 disposable worktree"
                    "（worktree-lifecycle.md §3），無分支可比對卡註冊，不計孤兒",
                )
            )
            continue
        registered = by_branch.get(entry.branch)
        if registered:
            report.worktrees.append(
                WorktreeFinding(
                    path=entry.path, branch=entry.branch, head_sha=entry.head_sha,
                    classification="registered_active", card_id=registered.card_id,
                    detail=f"對應活卡 {registered.card_id}（交付狀態 {registered.delivery_status}）",
                )
            )
        else:
            hint = ""
            if entry.branch in archived_ids or any(
                aid.lower() in entry.branch.lower() for aid in archived_ids
            ):
                hint = "；分支名稱疑似對應到已封存卡，但封存表未留分支欄可精確核對"
            report.worktrees.append(
                WorktreeFinding(
                    path=entry.path, branch=entry.branch, head_sha=entry.head_sha,
                    classification="orphan_untracked",
                    detail=f"分支 {entry.branch!r} 未見於任何活卡的分支／worktree 欄{hint}",
                )
            )

    # 2) submodule 初始化狀態
    for sub in git_ops.submodule_status(repo_root):
        if not sub.initialized:
            status: Literal["ok", "uninitialized", "out_of_sync"] = "uninitialized"
            detail = "尚未 `git submodule update --init`"
        elif sub.out_of_sync:
            status = "out_of_sync"
            detail = "checkout 的 commit 與父repo記錄的 SHA 不同"
        else:
            status = "ok"
            detail = f"已初始化（{sub.describe or sub.sha[:12]}）"
        report.submodules.append(
            SubmoduleFinding(path=sub.path, status=status, sha=sub.sha, detail=detail)
        )

    # 3) 孤兒分支：本地分支存在、但沒有 worktree 也沒有卡註冊
    worktree_branches = {e.branch for e in entries if e.branch}
    try:
        all_branches = git_ops.local_branches(repo_root)
    except git_ops.GitError:
        all_branches = []
    for branch in all_branches:
        if branch == main_ref or branch in worktree_branches or branch in by_branch:
            continue
        merged: bool | None
        try:
            merged = git_ops.is_ancestor(repo_root, branch, main_ref)
        except git_ops.GitError:
            merged = None
        detail = "已完全併入 main，可安全清理（僅列出，未刪除）" if merged else "尚未併入 main，暫勿清理"
        report.orphan_branches.append(
            BranchFinding(branch=branch, merged_into_main=merged, detail=detail)
        )

    # 4) 殘留 lease：owner 已認領，但 worktree 路徑在磁碟上不存在（機械、確定）
    #    或最後交接已超過 lease_ttl_hours（啟發式、僅供人工判斷，不自動回收）。
    now = datetime.now().astimezone()
    for rc in active:
        if not rc.owner_assigned():
            continue
        reasons: list[str] = []
        if rc.worktree_path:
            wt_path = repo_root / rc.worktree_path
            if not wt_path.exists():
                reasons.append(f"註冊的 worktree 路徑 {rc.worktree_path} 在磁碟上不存在")
        age_hours: float | None = None
        handoff_dt = _parse_iso(rc.last_handoff)
        if handoff_dt is not None:
            age_hours = (now - handoff_dt).total_seconds() / 3600.0
            if age_hours > lease_ttl_hours:
                reasons.append(f"最後交接超過 lease TTL（{lease_ttl_hours}h）")
        if reasons:
            report.stale_leases.append(
                LeaseFinding(
                    card_id=rc.card_id, owner=rc.owner, worktree_path=rc.worktree_path,
                    reason="；".join(reasons), age_hours=age_hours,
                )
            )

    return report


__all__ = [
    "BranchFinding",
    "DoctorReport",
    "LeaseFinding",
    "ReviewChannelFinding",
    "SubmoduleFinding",
    "WorktreeFinding",
    "audit_review_channel",
    "run_doctor",
]
