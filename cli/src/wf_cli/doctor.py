"""doctor：對帳（git worktree list vs 卡註冊、submodule 未初始化、殘留 lease、
孤兒分支、prunable worktree、commit trailer 完整性）。全程唯讀——本卡刻意不實作
任何回收／清理動作（見卡面紅線 3：破壞性操作必須先列清單再執行；本 CLI v1 只做
「列清單」那一半，清理是另一個未來、需要明確人工核可的獨立指令，不混進 doctor）。

**doctor 不阻擋任何操作。** 它是唯讀顧問：把缺失變成可枚舉的清單，讓人（或 CI）
拿去用。commit trailer 這一段尤其要講清楚——它偵測得到 `git push` 之後的缺漏，
但它不在 push 路徑上，也不在 merge 路徑上，因此**擋不住任何一次違規的落地**。
最接近執行面的是 CI（`DEV-AIWF-MINIMAL-CI1`，#48，持有 `.github/workflows/`），
但依 `docs/ROADMAP.md` §2，**#48 本身也擋不了人**：CI 產生的是紅叉，紅叉要變成
閘門需要 repo 的 `required_status_checks` ruleset，而 repo setting 不是檔案、
不在任何寫入集的值域裡。**牙齒長出來的時點是 ruleset 套用那一刻**，不是 #48 合併
那一刻。在那之前，本模組的全部效果就是「跑了才看得到」。
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re
from typing import Any, Literal

from . import git_ops
from .card import now_iso8601
from .cleanup import (
    DESTRUCTIVE_ORDER,
    SUBSEQUENT_OBLIGATION_STEPS,
    CleanupTarget,
    GuardMode,
    OccupancyProber,
    evaluate_cleanup_guard,
)
from .registry import RegisteredCard, TasksMdRegistry
from .review import STATUS_BY_RESULT

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
        "recorded",
        "receipt_untranscribed",
        "unobservable",
        "marker_quarantined",
        "half_written",
    ]
    card_id: str
    source_sha: str
    detail: str
    receipt_urls: tuple[str, ...] = ()
    receipt_authors: tuple[str, ...] = ()
    quarantine_reasons: tuple[str, ...] = ()
    expected_delivery_status: str | None = None
    actual_delivery_status: str | None = None


@dataclass(frozen=True)
class CleanupPreviewFinding:
    """`📦已合併` 但收尾未完成的卡：破壞性清理的前提現在成不成立（**唯讀**）。

    這是 reconcile 白名單第 2 條的偵測面。doctor 永遠只印，不動手；真正執行由
    `cleanup.execute_closeout_transition` 負責，兩者共用同一份 `evaluate_cleanup_guard`，
    所以「doctor 說可以」與「executor 願意做」不可能各說各話。
    """

    card_id: str
    branch: str | None
    worktree_path: str | None
    mode: GuardMode
    blocking_reasons: tuple[str, ...]
    #: 第 5–7 步永遠列在這裡：它們是其後義務，不寫狀態面，**不阻擋 release**。
    outstanding_obligations: tuple[int, ...] = SUBSEQUENT_OBLIGATION_STEPS
    #: 前提成立時**實際會被授權執行**的動作（`cleanup.AUTHORITY_BY_PROOF`）。
    #: 前提全部成立 ≠ 三個刪除動作都會做：squash 合併的卡只授權移除 worktree。
    #: 少了這一欄，預覽會讓人以為分支也會被刪。
    authorized_actions: frozenset[str] = frozenset()


@dataclass
class DoctorReport:
    repo_root: str
    generated_at: str
    registry_sources: list[str]
    worktrees: list[WorktreeFinding] = field(default_factory=list)
    submodules: list[SubmoduleFinding] = field(default_factory=list)
    orphan_branches: list[BranchFinding] = field(default_factory=list)
    stale_leases: list[LeaseFinding] = field(default_factory=list)
    cleanup_previews: list[CleanupPreviewFinding] = field(default_factory=list)
    cleanup_preview_enabled: bool = False

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
        if self.cleanup_preview_enabled:
            lines.append("## 5. 收尾清理前提（唯讀預覽；doctor 不執行任何刪除）")
            if not self.cleanup_previews:
                lines.append("（無 `📦已合併` 待收尾的卡）")
            for prev in self.cleanup_previews:
                if prev.mode == "proceed":
                    granted = "、".join(
                        a for a in DESTRUCTIVE_ORDER if a in prev.authorized_actions
                    ) or "（無）"
                    verdict = (
                        f"前提全部成立；授權範圍＝{granted}"
                        "（仍須由 release／reconcile 發動）"
                    )
                else:
                    verdict = "前提未全部成立 → 純偵測，不得刪除"
                lines.append(f"- [{prev.mode}] {prev.card_id}（分支={prev.branch or '—'}）{verdict}")
                for reason in prev.blocking_reasons:
                    lines.append(f"  - 阻擋：{reason}")
                lines.append(
                    "  - 其後義務（第 "
                    + "／".join(str(s) for s in prev.outstanding_obligations)
                    + " 步）不寫狀態面，未完成不阻擋 release"
                )
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


_VERDICT_HEADING_RE = re.compile(r"^## 查核裁決：(?P<result>\S+)\s*$", re.M)


def _verdict_of(body: str) -> str | None:
    """取出一則裁決留言自己的結論並映射為交付狀態；無法辨識或不唯一回 None。

    契約 §3.1.3 的已知限制：裁決結果不在 marker 內，只在渲染後的散文標題
    ``## 查核裁決：<result>``。此依賴會在結構化承載到位後消失（落差 8b）。

    ``wfcli review`` 渲染的裁決留言**恰有一個**該標題。出現多個代表有人引用了另一則
    裁決或編輯過留言——此時不得取第一個（那會讓結果隨標題在留言內的先後而變，與
    ``review-escalation.md`` §2「不得依順序覆寫」同源），也不得因為兩個標題文字相同
    就當成唯一：該留言已不是產生器的輸出，其結論不可信。判準是**標題出現次數恰為
    一**，零個、非列舉值、或多個一律視為無法辨識。
    """
    headings = _VERDICT_HEADING_RE.findall(body)
    # 以**出現次數**判定，不是以去重後的結論數。set 去重會讓「同一結論重複兩次」
    # 被當成唯一而放行——但 wfcli review 渲染的留言恰有一個標題，重複代表有人編輯
    # 或引用過，該留言已不是產生器的輸出。零個、非列舉值、或多個（即使文字相同）
    # 一律視為無法辨識。
    if len(headings) != 1:
        return None
    return STATUS_BY_RESULT.get(headings[0])


def _expected_delivery_status(
    verdicts: dict[str, str | None], deciding_attempts: list[str]
) -> tuple[str | None, str | None]:
    """由**據以放行的那些事件自己的結論**決定交付狀態應有的值。

    回傳 ``(expected, 歧義說明)``：兩者恰有一個為 None。

    先前是事後重掃全部留言、以「有沒有提到這個 attempt」決定誰有資格提供結論，
    因而兩種誤報：討論串引用裁決標題並提及該 attempt 會被算進來；以及 ``in``
    子字串比對讓 ``…-e0-<sha>`` 命中 ``…-e0-<sha>x``（同一個陷阱第三次）。
    改為在第一輪分類時就從該事件留言自身取下結論，不再有「誰有資格」的問題。

    **不得依留言順序決定**（``review-escalation.md`` §2）：同一 SHA 在 replan 後
    重審時，e0 與 e1 可能都被正確索引且結論相反，取「第一則」會讓結果隨排序而變。
    """
    results = {verdicts.get(a) for a in deciding_attempts}
    if None in results:
        return None, (
            "據以放行的事件中，有留言的 `## 查核裁決：` 結論無法辨識或不唯一"
            "（缺標題、結論非列舉值、或同一則留言出現多個結論），無從比對交付狀態。"
        )
    if not results:
        return None, None
    if len(results) > 1:
        return None, (
            "據以放行的 attempt 對應到多種裁決結論"
            f"（{'、'.join(sorted(r for r in results if r))}），無從判斷交付狀態應為何。"
            "同一 SHA 在 replan 後重審且結論相反時會出現此形態；依 review-escalation.md "
            "§2 不得依留言順序決定，請人工裁定。"
        )
    return results.pop(), None


def _check_third_face(expected: str | None, actual: str | None) -> str | None:
    """三面一致的第三面。回傳不一致的說明；一致則回 None。

    ``wfcli review`` 先寫 Issue 留言、再寫交付狀態、最後寫 body Log，三次遠端呼叫
    沒有交易性。留言與 Log 都成功而狀態欄失敗，就是半寫入——先前兩面一致即回
    ``recorded``，這種卡因此看起來完全正常，實際上看板上仍是待查核。
    """
    if actual is None:
        return (
            "無法讀取 Project 交付狀態欄，第三面未能驗證。契約 §3.1.3 要求三面一致，"
            "只驗到留言與 Log 兩面時不得宣稱已有裁決。"
        )
    if expected is None:
        return (
            f"找到裁決留言與 Log 索引，但留言中沒有可辨識的 `## 查核裁決：` 結論，"
            f"無從比對 Project 交付狀態（現為 {actual!r}）。"
        )
    if expected != actual:
        return (
            f"半寫入：裁決留言與 Log 索引都在，但 Project 交付狀態為 {actual!r}，"
            f"與裁決結論應有的 {expected!r} 不符。`wfcli review` 的三次遠端寫入沒有"
            "交易性，留言成功而狀態欄失敗即為此形態；請補齊狀態欄，不要重跑查核。"
        )
    return None


def audit_review_channel(
    comments: list[dict[str, Any]],
    card_id: str,
    source_sha: str,
    *,
    card_body: str = "",
    reviews: list[dict[str, Any]] | None = None,
    delivery_status: str | None = None,
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
        `review by wf-cli` 索引行」。三個要件缺一不可：

        1. 同一行同時含 `review by wf-cli` 與該 attempt——否則 attempt 出現在
           assign 行、review 出現在另一行也會算數。
        2. attempt 必須以 **token 邊界**比對，不能用 ``in``。``attempt in line``
           會讓 ``CARD-A-e0-<sha>`` 命中 Log 裡的 ``CARD-A-e0-<sha>x``：較長的
           不同 attempt 只要以前者為前綴就被誤認成同一個，fail-open 從頭來過。
           （同一個子字串陷阱先前已在收據比對上出現過一次。）
        3. 只用於 v1 事件；legacy 的判準見下方 ``legacy_log_present``。
        """
        boundary = re.compile(rf"(?<![\w-]){re.escape(attempt)}(?![\w-])")
        return any(
            "review by wf-cli" in line and boundary.search(line)
            for line in card_body.splitlines()
        )

    # legacy 的 Log 對帳刻意維持基線行為：全文各自搜尋，不要求同一行。
    # 卡面驗收第 3 條要求「legacy 判定行為與本卡前一致」，而基線接受「Log 中各自
    # 存在 review 與 attempt」。收緊它會讓既有舊卡由 recorded 變成 unobservable，
    # 那是回歸而不是修復。新的同行要求只施加於宣告受管轄的 v1 事件。
    legacy_log_present = "review by wf-cli" in card_body and bool(
        attempt_pattern.search(card_body)
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
    verdicts: dict[str, str | None] = {}

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
            verdicts[attempt] = _verdict_of(body)
        if receipt_marker in body and receipt_matches(body):
            url = str(comment.get("html_url") or comment.get("url") or "（收據 URL 未提供）")
            receipt_urls.append(url)
            user = comment.get("user") or {}
            login = user.get("login") if isinstance(user, dict) else None
            receipt_authors.append(str(login or "（GitHub author 未提供）"))
        if attempt is None and reason is None and state_marker in body:
            # legacy：完全不含 wf-review-event: 前綴的舊裁決留言。判準（語法）不變，
            # 但同樣要求 Log 索引的是這一則的 attempt，而非「body 裡任何一個 attempt」。
            hit = attempt_pattern.search(body)
            if hit:
                legacy_attempts.append(hit.group(0))
                verdicts.setdefault(hit.group(0), _verdict_of(body))

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
            # 停機與收據是兩件不同的事，下一步動作也不同：停機要人去修一則壞掉的
            # 留言，收據則說明「裁決其實發生過、只是還沒轉錄」。先前收據只在未停機
            # 時才收集，於是兩者並存時操作者只看得到停機，完全不知道有收據。
            receipt_urls=tuple(receipt_urls),
            receipt_authors=tuple(receipt_authors),
        )

    # 混合歷史的優先序：**同一 attempt 一旦存在受管轄的 v1 事件，就不得再由 legacy
    # 路徑替它背書**。兩條路徑先前以 OR 合併，於是 v1 事件即使沒有合格的同行 Log
    # 索引，只要同卡有同 attempt 的 legacy 文字加上基線式分行 Log，就從寬鬆那條放行
    # ——等於用舊標準替新標準的事件背書，v1 的兩面一致因此從未真正被要求。
    #
    # legacy 對其他 attempt 的寬鬆對帳保持不變（卡面驗收第 3 條），只排除與 v1 撞號者。
    v1_attempts = set(conformant_attempts)
    legacy_only = [a for a in legacy_attempts if a not in v1_attempts]
    matched = [a for a in conformant_attempts if log_indexes(a)]
    if matched or (legacy_only and legacy_log_present):
        # 過濾集必須涵蓋**實際據以放行的那些 attempt**。先前只傳 v1 的 matched，
        # legacy 路徑因此拿到空集合而失去過濾，_expected_delivery_status 會抓到
        # 第一則帶裁決標題的留言——包括別卡的，造成 half_written 誤報。誤報方向
        # 雖是 fail-closed，但它會擋住合法的 legacy 卡，而 legacy 相容是硬性驗收。
        # 兩條路徑都成立時取**聯集**而非只取 v1。先前寫成 `matched or legacy_only`，
        # 於是「兩個 v1 結論相反」判歧義、「v1 與 legacy 結論相反」卻默默取 v1——
        # 同樣的處境兩種待遇，而且沒有理由：在不引入時間語意的前提下，無法宣稱 v1
        # 較新而應勝出。結論一致就照常放行，不一致則與多 v1 情形一樣判歧義。
        deciding = [*matched, *legacy_only]
        expected, ambiguity = _expected_delivery_status(verdicts, deciding)
        third_face = ambiguity or _check_third_face(expected, delivery_status)
        if third_face is not None:
            return ReviewChannelFinding(
                status="half_written",
                card_id=card_id,
                source_sha=source_sha,
                detail=third_face,
                receipt_urls=tuple(receipt_urls),
                receipt_authors=tuple(receipt_authors),
                expected_delivery_status=expected,
                actual_delivery_status=delivery_status,
            )
        return ReviewChannelFinding(
            status="recorded",
            card_id=card_id,
            source_sha=source_sha,
            detail=(
                "已找到同一卡、同一 attempt 的 wfcli review event 與 Issue Log，"
                "且 Project 交付狀態與裁決結論相符；三面一致，狀態面已有裁決。"
            ),
            expected_delivery_status=expected,
            actual_delivery_status=delivery_status,
        )

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


# --------------------------------------------------------------------------
# commit trailer 完整性檢查（AI_WORKFLOW.md §6:210-226、AGENTS.md:10）
# --------------------------------------------------------------------------
#
# 規則早就成文，守衛一直不存在：`AI_WORKFLOW.md:220` 白紙黑字寫「守衛必紅」，
# 而 2026-08-12 之前全 repo 非 docs 路徑 grep `Implemented-by`／`interpret-trailers`
# 零命中。後果同日實現——當日落 main 的 31 筆非 merge commit，`Implemented-by`
# 解析得出者 0 筆。本節就是那個從缺的守衛的**偵測面**。
#
# 判定一律以 **git 自己的 trailer parser** 為準，不自行重寫：讀取層用
# `%(trailers:only=true,unfold=true)`，它與 `git interpret-trailers --parse` 同一份
# 實作。這一點是本檢查器有沒有鑑別力的關鍵——`AI_WORKFLOW.md:220` 的規則正是
# 「trailer 與 `Co-Authored-By` 之間插一個空行就切斷解析」，而肉眼看訊息尾端
# 「明明寫了 Implemented-by」。自行寫 regex 掃訊息會把那種 commit 判綠，等於
# 守衛在最常發生的失敗形態上失效。
#
# **身分**：依 `docs/ROADMAP.md` §1，系統需要的身分只有「角色」與「模型」兩個
# 維度，且執行面是**完整性檢查**——欄位有沒有填、能不能被解析出來。本檢查器
# 不驗證、也刻意不提供任何手段去驗證「他真的是他」：trailer 的值一律當成**宣稱**
# 收下，只檢查該宣稱在不在。任何比對 GitHub 帳號、模型名單或簽章的機制都不屬
# 本模組射程（本 repo 的人類、PM、執行者、查核者共用同一個帳號，那種檢查恆真）。

#: 每個級別都要求的下限。`AI_WORKFLOW.md:211`（T0／T1）與 `:216`（T2 以上）的交集
#: ——因此判定它**不需要知道卡的級別**，而級別不在 commit 裡。
FLOOR_TRAILERS: tuple[str, ...] = ("Requested-by", "Implemented-by")

#: 只有 T2 以上要求（`AI_WORKFLOW.md:216`）。級別是卡面欄位、不在 commit 裡，故
#: **預設不判為違規**，只如實回報有無；要把它升成違規須由呼叫端明示（見
#: `require_planned_by`），那是呼叫端提供的級別知識，不是本檢查器導出的。
TIER2_TRAILER = "Planned-by"

#: merge commit／PR 結案紀錄／B2 權威文件核可 commit 另必加（`AI_WORKFLOW.md:222`）。
MERGE_TRAILER = "Reviewed-by"

#: 「寫了但被空行切斷」的偵測範圍。只看治理 trailer，不含 `Co-Authored-By`。
_DECLARED_TRAILERS: tuple[str, ...] = (*FLOOR_TRAILERS, TIER2_TRAILER, MERGE_TRAILER)
_TRAILER_LINE_RE = re.compile(r"^(?P<key>[A-Za-z0-9-]+)[ \t]*:")
_PARAGRAPH_SPLIT_RE = re.compile(r"\n[ \t]*\n")


def severed_declared_keys(message: str, present: set[str]) -> tuple[str, ...]:
    """訊息尾端**寫成 trailer 樣子、卻沒被 git 解析成 trailer** 的治理欄位。

    這是 `AI_WORKFLOW.md:220` 那條規則的直接偵測面：`Implemented-by` 明明寫在
    訊息末端，只因為與 `Co-Authored-By` 之間多一個空行，`interpret-trailers`
    就在那裡切斷，整段變成內文。肉眼看是「有寫」，機器看是「沒有」——不把兩者
    分開講，操作者會以為守衛壞了。

    判準是**自末端往回走連續的 trailer 形狀段落**，遇到第一個散文段落就停。
    不是全文 regex：全文掃描會把「在 commit 訊息裡討論 trailer 規則」的句子
    誤判成被切斷的 trailer——本卡自己的 commit 就會是那種訊息。

    已知的漏（往少報的方向）：trailer 區塊後面又接了散文段落時，往回走第一步就
    停，因此不會回報。此時 `missing` 仍照常成立，只是說明少了一句「你寫了但被
    切斷」。誤判方向是少說，不是錯判。
    """
    found: list[str] = []
    for para in reversed(_PARAGRAPH_SPLIT_RE.split(message.strip("\n"))):
        lines = [ln for ln in para.splitlines() if ln.strip()]
        if not lines:
            continue
        keys: list[str] = []
        for line in lines:
            match = _TRAILER_LINE_RE.match(line)
            if match is None:
                # 續行（以空白開頭）只在段落已有 trailer 行時算數；其餘一律散文。
                if keys and line[:1] in (" ", "\t"):
                    continue
                keys = []
                break
            keys.append(match.group("key").lower())
        if not keys:
            break  # 散文段落：再往前都是內文，停。
        found.extend(keys)
    return tuple(k for k in _DECLARED_TRAILERS if k.lower() in found and k.lower() not in present)

#: 分流界線（committer date）。**不是任選**：
#:
#: 1. 補 trailer 只能改寫已推送歷史，本專案明令禁止 → 界線之前的 commit 產出的是
#:    沒有人被允許修的 finding，那是噪音不是 finding。故界線不得早於「機械執行者
#:    存在的時點」。
#: 2. 執行者存在的時點＝本卡落 main 的時點，而那個 SHA 在寫這行時還不存在
#:    （雞生蛋）。**日期**寫得出來、手算得出來，SHA 不行。
#: 3. 本 repo 的 main 會被 `pull --rebase` 線性化，SHA 界線會被壓平成孤兒而失效；
#:    committer date 在 rebase 後仍指向「它進入這條歷史的時點」，界線不會失效。
#:
#: 界線是**分流輔助**，不是安全邊界：`GIT_COMMITTER_DATE` 可任意設定，想繞的人
#: 一行環境變數就繞過去了。它的作用是讓「不可補正的歷史」與「新 commit」分開列，
#: 不是防禦。
TRAILER_GUARD_EPOCH = "2026-08-13T00:00:00+08:00"

#: 本缺陷家族的 canonical `root_cause_id`（裁定見 `AGENTS.md`「commit trailer」節）。
#: 只約束未來；既有事件不追溯改寫。
COMMIT_TRAILER_ROOT_CAUSE_ID = "commit-trailer-required-but-missing"

#: 同一缺陷在本卡開卡前用過的其他名字。**這是唯讀的對照紀錄**，不回寫任何已寫入
#: 的事件——留在這裡是為了讓後來的人看得出它們是同一族，而不是三件事。
SUPERSEDED_ROOT_CAUSE_IDS: tuple[str, ...] = (
    "governance-provenance-trailer-omission",
    "unknown-DEV-AIWF-MINIMAL-CI1-R2-002",
)

CommitShape = Literal["implementation", "empty", "merge_clean", "merge_with_content"]
CommitTrailerStatus = Literal["compliant", "violation", "pre_guard", "not_applicable"]


@dataclass(frozen=True)
class CommitRecord:
    """一筆 commit 的原始事實。**判定層只吃這個**，不碰 git。

    `trailers` 已經是 git 自己解析出來的結果（key, value），不是本模組掃出來的。
    """

    sha: str
    parents: tuple[str, ...]
    committed_at: str
    authored_at: str
    subject: str
    message: str
    trailers: tuple[tuple[str, str], ...]
    #: 本 commit 相對其第一個 parent 改動的路徑（root commit 相對空樹）。
    changed_paths: tuple[str, ...] = ()
    #: 只對 merge commit 有意義：combined diff（`git diff-tree --cc`）列出的路徑，
    #: 即**與所有 parent 都不同**的內容——衝突解法或 evil merge 夾帶的改動。
    merge_content_paths: tuple[str, ...] = ()

    def trailer_keys(self) -> set[str]:
        return {k.lower() for k, _ in self.trailers}


@dataclass(frozen=True)
class CommitTrailerFinding:
    sha: str
    subject: str
    committed_at: str
    shape: CommitShape
    status: CommitTrailerStatus
    #: 該形狀所要求、而 git 解析不出來的 trailer。
    missing: tuple[str, ...] = ()
    #: 訊息裡**寫了**但沒被 git 解析成 trailer 的治理欄位——`AI_WORKFLOW.md:220`
    #: 的空行切斷即為此形態。與「根本沒寫」是兩種不同的病，處置也不同。
    severed: tuple[str, ...] = ()
    #: 只回報、不判違規的欄位（級別不在 commit 裡時的 `Planned-by`）。
    undecidable: tuple[str, ...] = ()
    detail: str = ""


@dataclass
class CommitTrailerReport:
    rev_range: str
    epoch: str | None
    require_planned_by: bool
    findings: list[CommitTrailerFinding] = field(default_factory=list)

    def by_status(self, status: CommitTrailerStatus) -> list[CommitTrailerFinding]:
        return [f for f in self.findings if f.status == status]

    @property
    def violations(self) -> list[CommitTrailerFinding]:
        return self.by_status("violation")

    def render_text(self) -> str:
        lines = [
            f"## commit trailer 完整性（範圍 {self.rev_range}；AI_WORKFLOW.md §6）",
            f"- 分流界線（committer date）：{self.epoch or '（無；全範圍一律判定）'}",
            f"- Planned-by：{'計入違規（呼叫端宣告本範圍為 T2 以上）' if self.require_planned_by else '只回報不判違規（級別不在 commit 裡）'}",
            f"- canonical root_cause_id：`{COMMIT_TRAILER_ROOT_CAUSE_ID}`",
            "- **doctor 唯讀，不阻擋任何 push／merge**。最接近執行面的是 CI"
            "（DEV-AIWF-MINIMAL-CI1，#48），但依 ROADMAP §2 連 #48 也只產生紅叉；"
            "紅叉要變成閘門須套 repo 的 required_status_checks ruleset。",
        ]
        counts = {
            s: len(self.by_status(s))  # type: ignore[arg-type]
            for s in ("violation", "pre_guard", "compliant", "not_applicable")
        }
        lines.append(
            f"- 統計：違規 {counts['violation']}／界線前（不判違規）{counts['pre_guard']}"
            f"／合規 {counts['compliant']}／無所要求 {counts['not_applicable']}"
            f"（共 {len(self.findings)} 筆）"
        )
        for f in self.findings:
            if f.status in ("compliant", "not_applicable"):
                continue
            flag = "違規" if f.status == "violation" else "界線前"
            lines.append(f"- [{flag}／{f.shape}] {f.sha[:12]} {f.committed_at} {f.subject}")
            lines.append(f"  - {f.detail}")
        return "\n".join(lines)


def classify_commit_shape(record: CommitRecord) -> CommitShape:
    """判定 commit 形狀。**判準全部從 commit 自身導出**，不看卡面、不看人工標註。

    四種被明確裁定的形狀（卡面驗收第 2 條）：

    - **merge commit**（`parents >= 2`）：分兩種。combined diff（`--cc`）為空的是
      `merge_clean`——它的 tree 完全由 parent 解釋得出，**沒有自己著作的內容**，
      故不是實作 commit。combined diff 非空的是 `merge_with_content`：那些行與
      **每一個** parent 都不同，是在 merge 當下寫下的（衝突解法／evil merge），
      屬著作內容，故照實作 commit 辦。這也順手堵掉「把改動塞進 merge commit」
      這條規避路徑。
    - **基線更新 merge**：也是 merge commit，同一格處理。本模組**刻意不區分**
      它與整合 merge——兩者都只是 `parents >= 2`，誰是 main 取決於你站在哪個
      ref 上看，那是脈絡不是 commit 自身的性質。既然導不出來就不假裝導得出來；
      何況兩者要求相同（`AI_WORKFLOW.md:222` 對 merge commit 一視同仁），區分了
      也不改變判定。
    - **cherry-pick**：不設特例，一律當普通實作 commit。理由是它**認不出來**：
      `-x` 才會留 `(cherry picked from commit …)`，而 `-x` 是選配，沒帶就與原生
      commit 完全無法區分。認不出來就 fail-closed。代價為零——cherry-pick 連
      訊息一起複製，來源合規則結果也合規；`-x` 那一行不是 `key: value`，
      `only=true` 會濾掉它，不影響同區塊其他 trailer 的解析。
    - **空 commit**（單 parent 且無任何路徑改動）：不是實作 commit。它沒有著作
      任何內容，也就沒有內容的來歷需要宣告——與 `merge_clean` 同一條原則
      （**要求 trailer 的是內容，不是 commit 這個容器**），不是兩條臨時規則。
      推論一：空 commit 藏不了東西，豁免它不開洞。推論二：本檢查器**逐 commit
      獨立判定、不繼承**——一筆帶齊 trailer 的空 commit 不會使它前面那筆裸的
      commit 變綠（git metadata 本來就不由 descendant 繼承）。至於治理層要不要
      **採認**那種補記，是規則層裁定，**不在本卡射程**（見卡面射程說明）；本模組
      只提供分流能力，不代替需求方裁定。

    root commit（`parents` 為空）走 `implementation`：它相對空樹的差異就是它的內容。
    """
    if len(record.parents) >= 2:
        return "merge_with_content" if record.merge_content_paths else "merge_clean"
    if not record.changed_paths:
        return "empty"
    return "implementation"


def required_trailers(shape: CommitShape, *, require_planned_by: bool = False) -> tuple[str, ...]:
    """該形狀在 `AI_WORKFLOW.md` §6 下必須帶的 trailer。"""
    if shape == "empty":
        return ()
    if shape == "merge_clean":
        return (MERGE_TRAILER,)
    required = list(FLOOR_TRAILERS)
    if require_planned_by:
        required.append(TIER2_TRAILER)
    if shape == "merge_with_content":
        required.append(MERGE_TRAILER)
    return tuple(required)


def evaluate_commit_trailers(
    record: CommitRecord,
    *,
    epoch: str | None = TRAILER_GUARD_EPOCH,
    require_planned_by: bool = False,
) -> CommitTrailerFinding:
    """對單一 commit 下判定。純函式，不碰 git，可用建構出來的 record 直接測。"""
    shape = classify_commit_shape(record)
    required = required_trailers(shape, require_planned_by=require_planned_by)
    present = record.trailer_keys()
    missing = tuple(k for k in required if k.lower() not in present)

    severed = severed_declared_keys(record.message, present)

    undecidable: tuple[str, ...] = ()
    if (
        not require_planned_by
        and shape in ("implementation", "merge_with_content")
        and TIER2_TRAILER.lower() not in present
    ):
        undecidable = (TIER2_TRAILER,)

    committed = _parse_iso(record.committed_at)
    epoch_dt = _parse_iso(epoch)
    before_epoch = (
        epoch_dt is not None and committed is not None and committed < epoch_dt
    )

    if not required:
        detail = (
            "空 commit：無任何路徑改動，沒有著作內容，故 §6 的來歷 trailer 無所加諸。"
            "注意本檢查器逐 commit 獨立判定、不繼承——它不會使任何其他 commit 變綠。"
        )
        return CommitTrailerFinding(
            sha=record.sha, subject=record.subject, committed_at=record.committed_at,
            shape=shape, status="not_applicable", severed=severed, detail=detail,
        )

    if not missing:
        detail = f"已帶齊 {'／'.join(required)}（由 git trailer parser 解析得出）。"
        if severed:
            detail += f" 但另有寫了卻被空行切斷的欄位：{'／'.join(severed)}。"
        return CommitTrailerFinding(
            sha=record.sha, subject=record.subject, committed_at=record.committed_at,
            shape=shape, status="compliant", severed=severed, undecidable=undecidable,
            detail=detail,
        )

    parts = [f"缺 {'／'.join(missing)}"]
    if severed:
        parts.append(
            f"訊息末端**寫了** {'／'.join(severed)} 但 git 解析不到——"
            "`AI_WORKFLOW.md:220`：trailer 與 `Co-Authored-By` 等之間插入空行即切斷解析，"
            "被切掉的行不算 trailer"
        )
    if before_epoch:
        parts.append(
            f"committer date 早於分流界線 {epoch}，補它只能改寫已推送歷史（本專案禁止）；"
            "故列為界線前，不計違規。是否採認屬規則層裁定，本檢查器不裁定"
        )
    return CommitTrailerFinding(
        sha=record.sha, subject=record.subject, committed_at=record.committed_at,
        shape=shape, status="pre_guard" if before_epoch else "violation",
        missing=missing, severed=severed, undecidable=undecidable,
        detail="；".join(parts) + "。",
    )


def _git_read(repo_root: Path, args: list[str]) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args], capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise git_ops.GitError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


_REC = "\x00"
_FLD = "\x1f"
_END = "\x1e"
_LOG_FORMAT = (
    f"%x00%H{_FLD}%P{_FLD}%cI{_FLD}%aI{_FLD}%s{_FLD}"
    "%(trailers:only=true,unfold=true)" + _END
)


def _parse_trailer_block(text: str) -> tuple[tuple[str, str], ...]:
    out: list[tuple[str, str]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        out.append((key.strip(), value.strip()))
    return tuple(out)


def read_commit_records(repo_root: Path, rev_range: str) -> list[CommitRecord]:
    """讀出 rev_range 內每筆 commit 的事實。唯讀（`log`／`diff-tree`）。

    刻意用 `%(trailers:…)` 而非自行解析：那個 placeholder 與
    `git interpret-trailers --parse` 是同一份實作，`AI_WORKFLOW.md:220` 指名的
    就是它的行為。自己寫 regex 會在「空行切斷」這個最常見的失敗形態上判錯。
    """
    log = _git_read(repo_root, ["log", rev_range, f"--format={_LOG_FORMAT}", "--name-only"])
    bodies_raw = _git_read(repo_root, ["log", rev_range, f"--format=%x00%H{_FLD}%B"])

    bodies: dict[str, str] = {}
    for chunk in bodies_raw.split(_REC):
        if not chunk.strip():
            continue
        sha, _, body = chunk.partition(_FLD)
        bodies[sha.strip()] = body

    records: list[CommitRecord] = []
    for chunk in log.split(_REC):
        if not chunk.strip():
            continue
        head, _, files = chunk.partition(_END)
        fields = head.split(_FLD)
        if len(fields) < 6:
            continue
        sha, parents, cdate, adate, subject, trailers = fields[:6]
        parent_shas = tuple(p for p in parents.split() if p)
        changed = tuple(ln for ln in (l.strip() for l in files.splitlines()) if ln)
        merge_paths: tuple[str, ...] = ()
        if len(parent_shas) >= 2:
            cc = _git_read(
                repo_root,
                ["diff-tree", "--cc", "--no-commit-id", "-r", "--name-only", sha],
            )
            merge_paths = tuple(ln for ln in (l.strip() for l in cc.splitlines()) if ln)
        records.append(
            CommitRecord(
                sha=sha, parents=parent_shas, committed_at=cdate, authored_at=adate,
                subject=subject, message=bodies.get(sha, ""),
                trailers=_parse_trailer_block(trailers),
                changed_paths=changed, merge_content_paths=merge_paths,
            )
        )
    return records


def audit_commit_trailers(
    repo_root: Path,
    rev_range: str,
    *,
    epoch: str | None = TRAILER_GUARD_EPOCH,
    require_planned_by: bool = False,
) -> CommitTrailerReport:
    report = CommitTrailerReport(
        rev_range=rev_range, epoch=epoch, require_planned_by=require_planned_by
    )
    for record in read_commit_records(repo_root, rev_range):
        report.findings.append(
            evaluate_commit_trailers(
                record, epoch=epoch, require_planned_by=require_planned_by
            )
        )
    return report


def run_doctor(
    repo_root: Path,
    registry: TasksMdRegistry | None = None,
    lease_ttl_hours: float = 48.0,
    main_ref: str = "main",
    cleanup_preview: bool = False,
    card_bodies: dict[str, str] | None = None,
    occupancy_prober: OccupancyProber | None = None,
) -> DoctorReport:
    repo_root = repo_root.resolve()
    active: list[RegisteredCard] = registry.active if registry else []
    archived_ids = registry.archived_card_ids if registry else set()
    by_branch: dict[str, RegisteredCard] = {rc.branch: rc for rc in active if rc.branch}

    report = DoctorReport(
        repo_root=str(repo_root),
        generated_at=now_iso8601(),
        registry_sources=[str(p) for p in (registry.source_paths if registry else [])],
        cleanup_preview_enabled=cleanup_preview,
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

    # 5) 收尾清理前提（唯讀）。只看 `📦已合併`：那是「merge 已完成、收尾未走完」的
    #    可觀測標記，也正是 reconcile --apply 白名單第 2 條的分歧形態。刻意**不看**
    #    第 4 步（Issue 是否關閉／是否已寫終態）——那是本轉換的效果，拿它當前提會
    #    構成循環，release 將永遠無法發動。
    if cleanup_preview:
        bodies = card_bodies or {}
        for rc in active:
            if (rc.delivery_status or "") != "📦已合併" or not rc.branch:
                continue
            wt = None
            if rc.worktree_path:
                candidate = Path(rc.worktree_path)
                wt = candidate if candidate.is_absolute() else repo_root / candidate
            decision = evaluate_cleanup_guard(
                CleanupTarget(
                    repo_root=repo_root, card_id=rc.card_id, branch=rc.branch,
                    worktree_path=wt, main_ref=main_ref,
                ),
                registry=registry,
                card_body=bodies.get(rc.card_id),
                occupancy_prober=occupancy_prober,
            )
            report.cleanup_previews.append(
                CleanupPreviewFinding(
                    card_id=rc.card_id, branch=rc.branch,
                    worktree_path=str(wt) if wt else None,
                    mode=decision.mode, blocking_reasons=decision.reasons,
                    authorized_actions=decision.authorized_actions,
                )
            )

    return report


__all__ = [
    "COMMIT_TRAILER_ROOT_CAUSE_ID",
    "FLOOR_TRAILERS",
    "MERGE_TRAILER",
    "SUPERSEDED_ROOT_CAUSE_IDS",
    "TIER2_TRAILER",
    "TRAILER_GUARD_EPOCH",
    "BranchFinding",
    "CleanupPreviewFinding",
    "CommitRecord",
    "CommitTrailerFinding",
    "CommitTrailerReport",
    "DoctorReport",
    "LeaseFinding",
    "ReviewChannelFinding",
    "SubmoduleFinding",
    "WorktreeFinding",
    "audit_commit_trailers",
    "audit_review_channel",
    "classify_commit_shape",
    "evaluate_commit_trailers",
    "read_commit_records",
    "required_trailers",
    "run_doctor",
    "severed_declared_keys",
]
