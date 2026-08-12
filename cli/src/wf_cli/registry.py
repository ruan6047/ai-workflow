"""卡註冊來源（可插拔）：doctor 用來判斷「這個 worktree 對得上哪張卡」。

遷移尚未 cutover 的專案（如 cpbl-analytics）目前仍以 ``docs/TASKS.md`` 的 Ledger
表格作為 current-state 事實來源；已 cutover 的專案改用 GitHub Project（見
``project.py``）。doctor／snapshot 的骨架刻意不綁定其中一種（卡面〈依賴與順序〉：
「doctor／snapshot 骨架不依賴 Issues 結構，可立即先行」），所以這裡定義一個共同的
最小介面 ``RegisteredCard``，兩種來源各自轉成這個形狀。

跨 repo 歸屬守衛（WF-WORKTREE-REPO-OWNERSHIP1 / #57）
=====================================================

本檔後半段（``normalize_repo_slug`` 起）是 ``WF-ORCHESTRATION-RECONCILE1``（#16）
§7「repo 歸屬純導出」的**判定引擎**：

    卡的 repo ← Issue URL；worktree 的 repo ← git commondir 的 origin remote；
    兩者不合 → 跨 repo 建立。

§8.3 的真實漂移（cpbl 卡的 worktree 建在 ai-workflow repo 內）之所以能存在數週，
是因為系統只有 ``doctor`` 的**事後對帳**，沒有建立當下的預防。本模組提供該預防的
**判定**部分。

.. warning::

   **判定 ≠ 強制。** 本模組只回傳 ``RepoOwnershipVerdict``，它不會讓任何指令
   失敗。真正的攔截點是 ``commands/assign_cmd.py`` 的 ``run()``——``--worktree``
   進入 ``format_branch_worktree``／``set_field_value`` 之前必須先呼叫
   ``check_assign_repo_ownership`` 並在 ``decision == "block"`` 時 return 非 0。
   該檔**不在本卡寫入集內**（由 #54 持有），因此在 #54 接上呼叫點之前，
   本模組的 ``block`` 判定**攔不下任何一次真實派工**。凡讀到「會擋下」而想確認
   執行者的人：執行者目前**不存在**，見本卡交回報告的「無機械執行者的宣稱」節。

**與 ``TasksMdRegistry`` 的隔離**：守衛的兩個輸入（Issue URL、git commondir）都是
即時事實，**都不經過 ``TASKS.md`` 投影**。這是刻意的——2026-08-12 實測 ``doctor``
把六個 WF 卡的 worktree 全報為孤兒，正是因為它讀已封存的 ``TASKS.md``。守衛函式的
簽章裡沒有任何 registry 參數，投影再怎麼過時都影響不到它
（``test_registry.py::test_guard_verdict_unaffected_by_stale_tasks_md_projection``
以「刻意寫一份錯誤的 TASKS.md」實測這條隔離）。
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .card import is_owner_assigned, parse_branch_worktree

_LINK_RE = re.compile(r"^\[([^\]]+)\]\(.*\)$")


@dataclass
class RegisteredCard:
    card_id: str
    branch: str | None
    worktree_path: str | None
    delivery_status: str | None
    owner: str | None
    last_handoff: str | None = None
    archived: bool = False
    #: 卡所屬 repo（``owner/repo``，小寫正規化）。
    #:
    #: ``TASKS.md`` Ledger **沒有 repo 欄**——這正是為什麼舊 registry 無法表達
    #: 跨 repo 漂移，doctor 只能把外來 worktree 一律歸類成 ``orphan_untracked``。
    #: cutover 後的 GitHub 來源可從 Issue URL 免費導出這一欄（見本檔「registry 的
    #: github 模式」裁定）。``TasksMdRegistry`` 永遠留 None：它真的不知道。
    repo: str | None = None

    def owner_assigned(self) -> bool:
        """owner 欄是否已指向真正的執行者，而非「待指派／待建立／—」佔位字串。"""
        return is_owner_assigned(self.owner)


def _cell_card_id(cell: str) -> str:
    match = _LINK_RE.match(cell.strip())
    return match.group(1) if match else cell.strip()


def _split_row(line: str) -> list[str]:
    # markdown table row："| a | b | c |" -> ["a","b","c"]；忽略頭尾的空字串
    parts = [p.strip() for p in line.strip().split("|")]
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return parts


def _is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-+:?", c) for c in cells if c)


def parse_markdown_tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    """粗略解析文件內所有 pipe table，回傳 [(header_cells, [row_cells,...]), ...]。

    只掃「看起來像表格」的連續 ``|`` 開頭行，不做完整 CommonMark 解析——本專案的
    Ledger／archive 表格格式穩定（見 templates/TASKS.md），夠用且不引入額外依賴。
    """
    tables: list[tuple[list[str], list[list[str]]]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|"):
            header = _split_row(line)
            if i + 1 < len(lines) and _is_separator_row(_split_row(lines[i + 1])):
                rows: list[list[str]] = []
                j = i + 2
                while j < len(lines) and lines[j].strip().startswith("|"):
                    rows.append(_split_row(lines[j]))
                    j += 1
                tables.append((header, rows))
                i = j
                continue
        i += 1
    return tables


def parse_active_ledger(text: str) -> list[RegisteredCard]:
    """解析「Ledger 總表（活卡）」：卡ID｜Initiative｜級別｜功能｜owner｜分支／worktree｜
    iteration｜交付狀態｜部署狀態｜最後交接。欄位順序以表頭名稱比對，不依賴位置。
    """
    out: list[RegisteredCard] = []
    for header, rows in parse_markdown_tables(text):
        try:
            card_idx = header.index("卡ID")
        except ValueError:
            continue
        bw_idx = next((k for k, h in enumerate(header) if "分支" in h and "worktree" in h), None)
        status_idx = next((k for k, h in enumerate(header) if h == "交付狀態"), None)
        owner_idx = next((k for k, h in enumerate(header) if h == "owner"), None)
        handoff_idx = next((k for k, h in enumerate(header) if h == "最後交接"), None)
        for row in rows:
            if card_idx >= len(row):
                continue
            card_id = _cell_card_id(row[card_idx])
            if not card_id or card_id == "—":
                continue
            branch = worktree = None
            if bw_idx is not None and bw_idx < len(row):
                branch, worktree = parse_branch_worktree(row[bw_idx].strip("` "))
            status = row[status_idx].strip() if status_idx is not None and status_idx < len(row) else None
            owner = row[owner_idx].strip() if owner_idx is not None and owner_idx < len(row) else None
            last_handoff = (
                row[handoff_idx].strip() if handoff_idx is not None and handoff_idx < len(row) else None
            )
            out.append(
                RegisteredCard(
                    card_id=card_id, branch=branch, worktree_path=worktree,
                    delivery_status=status, owner=owner, last_handoff=last_handoff,
                    archived=False,
                )
            )
    return out


def parse_archived_card_ids(text: str) -> set[str]:
    """封存表沒有分支／worktree 欄（依 worktree-lifecycle.md，結案時就該清掉），
    這裡只取卡ID集合，供 doctor 做「分支名稱是否疑似對應到某張已封存卡」的軟提示。
    """
    ids: set[str] = set()
    for header, rows in parse_markdown_tables(text):
        if "卡ID" not in header:
            continue
        card_idx = header.index("卡ID")
        for row in rows:
            if card_idx < len(row):
                cid = _cell_card_id(row[card_idx])
                if cid and cid != "—":
                    ids.add(cid)
    return ids


@dataclass
class TasksMdRegistry:
    active: list[RegisteredCard]
    archived_card_ids: set[str]
    source_paths: list[Path]


def _first_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def load_tasks_md_registry(repo_root: Path) -> TasksMdRegistry:
    active_path = _first_existing([repo_root / "docs" / "TASKS.md", repo_root / "TASKS.md"])
    archive_path = _first_existing(
        [repo_root / "docs" / "archive" / "TASKS_ARCHIVE.md", repo_root / "archive" / "TASKS_ARCHIVE.md"]
    )
    active: list[RegisteredCard] = []
    archived_ids: set[str] = set()
    source_paths: list[Path] = []
    if active_path:
        active = parse_active_ledger(active_path.read_text(encoding="utf-8"))
        source_paths.append(active_path)
    if archive_path:
        archived_ids = parse_archived_card_ids(archive_path.read_text(encoding="utf-8"))
        source_paths.append(archive_path)
    return TasksMdRegistry(active=active, archived_card_ids=archived_ids, source_paths=source_paths)


# ---------------------------------------------------------------------------
# 跨 repo 歸屬：判定引擎（#16 §7「repo 歸屬純導出」）
# ---------------------------------------------------------------------------

#: GitHub owner／repo 名稱允許的字元。用來拒絕「任意兩段路徑」被誤讀成 slug。
_GH_NAME_RE = re.compile(r"[A-Za-z0-9_.-]+")

#: scp-like remote：``git@github.com:owner/repo.git``（沒有 ``://``，冒號後接路徑）。
_SCP_LIKE_RE = re.compile(r"^[A-Za-z0-9_.+-]+@(?P<host>[^:/]+):(?P<path>.+)$")


def normalize_repo_slug(value: str | None) -> str | None:
    """把各種 repo 表示法正規化成小寫 ``owner/repo``；認不出來回 None。

    接受 ``owner/repo``、scp-like remote、``https://``／``ssh://`` remote，以及
    Issue／PR URL（``https://github.com/o/r/issues/57`` → ``o/r``）。

    **小寫比較**是刻意的：GitHub 的 owner／repo 不分大小寫，
    ``ruan6047/AI-Workflow`` 與 ``ruan6047/ai-workflow`` 是同一個 repo，若逐字比對
    會產生純大小寫造成的誤擋——守衛的第一要求是不誤擋。
    """
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None

    match = _SCP_LIKE_RE.match(raw)
    if match:
        path, url_like = match.group("path"), True
    elif "://" in raw:
        rest = raw.split("://", 1)[1]
        # 去掉 host（與可能的 user@host、:port）
        path, url_like = (rest.split("/", 1)[1] if "/" in rest else ""), True
    else:
        path, url_like = raw, False

    parts = [p for p in path.strip("/").split("/") if p]
    # 純 ``owner/repo`` 形式必須剛好兩段：三段以上的裸路徑（例如某個目錄）不該被
    # 當成 slug。URL 形式則允許尾隨 ``/issues/57`` 這類路徑，只取前兩段。
    if len(parts) < 2 or (not url_like and len(parts) != 2):
        return None
    owner, repo = parts[0], parts[1]
    repo = repo.removesuffix(".git")
    if not _GH_NAME_RE.fullmatch(owner) or not _GH_NAME_RE.fullmatch(repo):
        return None
    return f"{owner.lower()}/{repo.lower()}"


def card_repo_from_issue_url(issue_url: str | None) -> str | None:
    """「卡所屬 repo」的**唯一**判定來源：卡自己的 Issue URL。

    為什麼只認這一個來源，其他候選一律不採：

    - **``--repo`` 旗標／``.wfcli.json``／``WFCLI_REPO``**：那是**呼叫端的主張**，
      不是卡的性質。漂移案例的形狀恰恰是「人在 ai-workflow 的環境下操作一張 cpbl
      的卡」——把呼叫端的宣告當成卡的 repo，守衛就會拿被檢查對象的說法當答案，
      在真正該擋的那一刻恆真通過。這條不是保守，是把檢查做成同義反覆。
    - **卡 ID 前綴／命名慣例**（``WF-*`` vs 其他）：慣例沒有機械保證，改名即失效。
    - **worktree 路徑**：那是被檢查的另一邊，不能同時當基準。

    DraftIssue 沒有 Issue URL，因此判不出來 → 由 ``check_worktree_repo_ownership``
    以 fail-closed 處理（見該函式 docstring 的論證）。
    """
    slug = normalize_repo_slug(issue_url)
    if slug is None:
        return None
    # 裸 ``owner/repo`` 不是 Issue URL；這裡要求真的是 URL 形式，否則
    # 「把 --repo 的值餵進來」會偽裝成合法的卡 repo 來源。
    if "://" not in (issue_url or "") and not _SCP_LIKE_RE.match((issue_url or "").strip()):
        return None
    return slug


#: 唯讀 git 探測器：回傳 stdout（strip 過），失敗回 None。可注入以便測試。
GitProbe = Callable[[Path, list[str]], "str | None"]


def run_git_readonly(cwd: Path, args: list[str]) -> str | None:
    """執行唯讀 git 子命令；非 0 或例外一律回 None（判不出來，不是當機）。

    只准唯讀子命令進來——本函式的呼叫端全部寫在本檔內，且只用
    ``rev-parse``／``remote get-url``。
    """
    try:
        proc = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    out = proc.stdout.strip()
    return out or None


@dataclass(frozen=True)
class WorktreeRepoProbe:
    """「worktree 目標 repo」的探測結果。"""

    slug: str | None
    #: 實際被問到的目錄：目標路徑本身，或（路徑尚未建立時）其最近存在的祖先。
    probed_dir: str | None
    common_dir: str | None
    remote_url: str | None
    detail: str


def _nearest_existing_dir(path: Path) -> Path | None:
    current = path
    while True:
        if current.is_dir():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def probe_worktree_repo(
    worktree_path: str | Path,
    *,
    base_dir: str | Path | None = None,
    git: GitProbe = run_git_readonly,
) -> WorktreeRepoProbe:
    """由 worktree 路徑導出它會落在哪個 repo（#16 §7：worktree 的 repo ← commondir）。

    比對軸是 **origin remote 的 slug**，不是路徑：``commondir`` 對 submodule 會落在
    父 repo 的 ``.git/modules/...`` 底下，用路徑比對會把 submodule 誤判成父 repo。
    同一個 repo 的所有 worktree 共用 commondir，故 remote 也共用——這正是我們要的
    等價類。

    **路徑尚未建立時**（``assign`` 通常先於 ``git worktree add``）改問**最近存在的
    祖先目錄**。``<ai-workflow>/.claude/worktrees/新目錄`` 的祖先是 ai-workflow，
    答案與建立後一致，這是本守衛能在寫入前生效的原因。

    **已知邊界**：相對路徑以 ``base_dir``（預設 cwd）解析，因此對相對路徑而言，
    判定會隨「在哪裡執行指令」而變。Ledger 存的正是相對路徑
    （``.claude/worktrees/card-a``）。呼叫端若要不受 cwd 影響必須傳絕對路徑或明確的
    ``base_dir``；這一點沒有機械執行者。
    """
    base = Path(base_dir) if base_dir is not None else Path.cwd()
    target = Path(worktree_path).expanduser()
    if not target.is_absolute():
        target = base / target

    probe_dir = _nearest_existing_dir(target)
    if probe_dir is None:
        return WorktreeRepoProbe(
            slug=None, probed_dir=None, common_dir=None, remote_url=None,
            detail=f"路徑 {target} 與其所有祖先皆不存在，無從判斷所屬 repo",
        )

    common_dir = git(probe_dir, ["rev-parse", "--path-format=absolute", "--git-common-dir"])
    if common_dir is None:
        return WorktreeRepoProbe(
            slug=None, probed_dir=str(probe_dir), common_dir=None, remote_url=None,
            detail=f"{probe_dir} 不在任何 git repo 內（rev-parse --git-common-dir 失敗）",
        )

    remote_url = git(probe_dir, ["remote", "get-url", "origin"])
    if remote_url is None:
        return WorktreeRepoProbe(
            slug=None, probed_dir=str(probe_dir), common_dir=common_dir, remote_url=None,
            detail=f"repo（commondir {common_dir}）沒有 origin remote，無法導出 owner/repo",
        )

    slug = normalize_repo_slug(remote_url)
    if slug is None:
        return WorktreeRepoProbe(
            slug=None, probed_dir=str(probe_dir), common_dir=common_dir, remote_url=remote_url,
            detail=f"origin remote {remote_url!r} 無法解析為 owner/repo",
        )
    return WorktreeRepoProbe(
        slug=slug, probed_dir=str(probe_dir), common_dir=common_dir, remote_url=remote_url,
        detail=f"commondir {common_dir} 的 origin → {slug}",
    )


OwnershipDecision = Literal["allow", "block"]
OwnershipReason = Literal[
    "match",
    "repo_mismatch",
    "card_repo_undeterminable",
    "worktree_repo_undeterminable",
]

#: reason_code → decision 的**全表**。``check_worktree_repo_ownership`` 一律從這裡
#: 導出 decision，不另外寫 if。表是封閉的：新增 reason 就必須在此明示它放不放行，
#: 不會有「忘了處理所以預設 allow」的縫。
#:
#: ``test_registry.py::test_only_match_produces_allow`` 對本表**窮舉**，證明
#: ``match`` 是唯一放行碼——不是抽樣。
OWNERSHIP_DECISIONS: dict[OwnershipReason, OwnershipDecision] = {
    "match": "allow",
    "repo_mismatch": "block",
    "card_repo_undeterminable": "block",
    "worktree_repo_undeterminable": "block",
}


@dataclass(frozen=True)
class RepoOwnershipVerdict:
    reason_code: OwnershipReason
    card_repo: str | None
    worktree_repo: str | None
    detail: str

    @property
    def decision(self) -> OwnershipDecision:
        return OWNERSHIP_DECISIONS[self.reason_code]

    @property
    def blocked(self) -> bool:
        return self.decision == "block"

    def refusal_message(self) -> str:
        """被擋時要印給人看的訊息。**必須指出合法出路**，否則人只會學會繞過。

        出路取自 #16 §7.1：工作落在哪個 repo，卡就開在哪個 repo；跨 repo 需求以
        連結卡表達（來源 repo 的卡在 spec 基線宣告實作卡 Issue URL，反之亦然）。
        """
        head = {
            "repo_mismatch": (
                f"worktree 會落在 {self.worktree_repo}，但卡屬於 {self.card_repo}——"
                "跨 repo 建立 worktree"
            ),
            "card_repo_undeterminable": "判不出卡所屬 repo",
            "worktree_repo_undeterminable": "判不出 worktree 目標 repo",
            "match": "（未被擋）",
        }[self.reason_code]
        if self.reason_code == "match":
            return head
        return (
            f"{head}；{self.detail}。"
            "合法路徑（#16 §7.1）：工作落在哪個 repo，卡就開在哪個 repo；"
            "跨 repo 需求請在目標 repo 另開實作卡，兩張卡以 spec 基線的 Issue URL 互相連結。"
        )


def check_worktree_repo_ownership(
    *,
    card_repo: str | None,
    worktree_probe: WorktreeRepoProbe,
) -> RepoOwnershipVerdict:
    """比對卡 repo 與 worktree repo，回傳判定。

    **判不出來時 fail-closed（擋下），不放行。** 二擇一的論證：

    1. **代價不對稱。** 誤擋的代價是**當場、對人、可讀**的一次拒絕，附合法出路；
       誤放的代價是 §8.3 那種**沉默**的錯置——worktree 建在錯的 repo 照樣能寫程式、
       能 commit，數週後才在對帳裡浮出來，而那份對帳自己還會誤報。可偵測的即時
       痛感 vs 不可偵測的長期漂移，只有前者能被修。
    2. **判不出來的每一種輸入都不是合法穩態，且都可在一分鐘內修好。**
       ``card_repo_undeterminable`` 只發生在 DraftIssue（卡不在任何 repo 裡——但
       ``assign`` 本來就要把 Log 寫回卡面，正式流程要求真 Issue）；
       ``worktree_repo_undeterminable`` 只發生在路徑打錯、目標不在任何 git repo 內、
       或 repo 沒有 origin remote。三者都是「輸入本身有問題」，放行等於用一個
       壞掉的輸入換一次寫入。
    3. **fail-closed 不會被無關的故障觸發。** 卡 repo 來自 ``ItemSnapshot.issue_url``，
       那是 ``assign`` 早已為了別的理由抓下來的同一份資料；GitHub 掛掉時 ``assign``
       在到達本守衛之前就已經失敗。守衛**不新增任何網路相依**——這是 fail-closed
       站得住的前提，否則它會變成「別人的服務抖一下，全隊都不能派工」。

    刻意**沒有** ``--force``／``--allow-cross-repo`` 逃生口：漂移案例的成因不是
    有人想跨 repo，是沒人注意到自己跨了。給逃生口等於把「沒注意到」變成「按一下」。
    """
    if card_repo is None:
        return RepoOwnershipVerdict(
            reason_code="card_repo_undeterminable",
            card_repo=None,
            worktree_repo=worktree_probe.slug,
            detail="卡沒有可解析的 Issue URL（DraftIssue 或 URL 形式不合），"
                   "而卡所屬 repo 只認 Issue URL 一個來源",
        )
    if worktree_probe.slug is None:
        return RepoOwnershipVerdict(
            reason_code="worktree_repo_undeterminable",
            card_repo=card_repo,
            worktree_repo=None,
            detail=worktree_probe.detail,
        )
    if worktree_probe.slug != card_repo:
        return RepoOwnershipVerdict(
            reason_code="repo_mismatch",
            card_repo=card_repo,
            worktree_repo=worktree_probe.slug,
            detail=worktree_probe.detail,
        )
    return RepoOwnershipVerdict(
        reason_code="match",
        card_repo=card_repo,
        worktree_repo=worktree_probe.slug,
        detail=worktree_probe.detail,
    )


def check_assign_repo_ownership(
    *,
    issue_url: str | None,
    worktree_path: str | Path,
    base_dir: str | Path | None = None,
    git: GitProbe = run_git_readonly,
) -> RepoOwnershipVerdict:
    """``assign`` 用的端到端判定：卡的 Issue URL ＋ ``--worktree`` 路徑 → 判定。

    這是 ``commands/assign_cmd.py`` 應該呼叫的那一個函式（見本檔頂端 warning：
    呼叫點屬 #54，本卡未接）。簽章刻意**只有兩個事實輸入**，沒有
    ``TasksMdRegistry``／``--repo``／設定檔——投影過時或呼叫端環境設錯都影響不到
    判定。
    """
    return check_worktree_repo_ownership(
        card_repo=card_repo_from_issue_url(issue_url),
        worktree_probe=probe_worktree_repo(worktree_path, base_dir=base_dir, git=git),
    )


__all__ = [
    "OWNERSHIP_DECISIONS",
    "GitProbe",
    "OwnershipDecision",
    "OwnershipReason",
    "RegisteredCard",
    "RepoOwnershipVerdict",
    "TasksMdRegistry",
    "WorktreeRepoProbe",
    "card_repo_from_issue_url",
    "check_assign_repo_ownership",
    "check_worktree_repo_ownership",
    "load_tasks_md_registry",
    "normalize_repo_slug",
    "parse_active_ledger",
    "parse_archived_card_ids",
    "parse_markdown_tables",
    "probe_worktree_repo",
    "run_git_readonly",
]
