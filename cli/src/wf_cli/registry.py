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
    兩者不合 → 跨 repo 錯置。

**射程（需求方 2026-08-12 裁定，#57 issuecomment-5268265532）**：本守衛在
``assign``「**登記** worktree 歸屬」的當下攔截跨 repo 錯置。**它不是建立面的預防，
本檔任何一句都不得被讀成「``git worktree add`` 建到錯的 repo 會被擋下」。**

§8.3 的真實漂移（cpbl 卡的 worktree 建在 ai-workflow repo 內）之所以能存在數週，
是因為系統只有 ``doctor`` 的**事後對帳**——而該對帳看不見這種形狀（兩個 repo 的頂層
``git worktree list`` 皆 0 命中）。本模組把「登記一筆跨 repo 歸屬」從沉默變成當場拒絕；
**「建立一個跨 repo worktree」不在射程內**，見下方 danger。

**機械執行者**：``commands/assign_cmd.py`` 的 ``run()``。它在**任何**
``set_field_value``／``set_item_body`` 之前呼叫 ``check_assign_repo_ownership``，
``blocked`` 時印 ``refusal_message()`` 並 return 5（零寫入）。``assign`` 寫
``--worktree`` 註冊欄那一刻是 wfcli 全域唯一會讓「某卡的 worktree **登記**屬於某
repo」成為事實的地方（全域無任何 ``git worktree add``，實測零命中），所以那裡就是
**登記面**攔截的唯一有效位置。

.. danger::

   **本守衛擋的是登記，不是建立。**

   ``wfcli`` 全域沒有任何 ``git worktree add``（實測零命中），因此人在 shell 裡
   直接建立 worktree **完全不經過本閘門**：先建立再登記時，被擋下的是登記那一步，
   磁碟上那個建錯 repo 的目錄已經存在且不會被本閘門移除；建立後**不登記**，本閘門
   連看都看不到。需求方 2026-08-12 裁定把本卡射程縮為登記面，並將建立面另開承接卡。
   該裁定明文要求下面這句**逐字保留、不得因射程縮小而軟化**：

       該卡未落地前，本 repo 對「人直接在 shell 建到錯的 repo」沒有任何預防

   同一句在派審詞裡的等義寫法，一併逐字留存：

       該卡未落地前，本 repo 對「人直接在 shell 跑 git worktree add 建到錯的 repo」沒有任何預防

   **承接者的現況（2026-08-13）**：該承接卡**尚未開卡，今天沒有任何卡、任何碼、
   任何人承接建立面**。是否開卡與何時排程是需求方依 ``docs/ROADMAP.md`` §5 的
   判斷，不是本卡的交付物，本檔也不得假設它已被排程。在它落地之前，上面那句
   就是本 repo 在建立面的真實狀態。

.. warning::

   **接線之後，下列三件仍然不成立，寫報告與卡面時不得含混：**

   1. **``inferred`` 的判定不是事實。** 目標尚未建立時 slug 由最近存在的祖先推得
      （``ProbeSource`` 的 ``ancestor_dir``）。2026-08-12 對 Project #4 全量實跑：
      45 筆 allow 裡有 28 筆是這種推測。它們**不構成**「守衛不誤擋合法配置」的證據，
      只構成「守衛在慣例配置下不吵」。要事實就得給 ``source_repo``。
   2. **閘門只管新寫入的登記，不回溯。** 既有註冊（實測 14 筆相對路徑）不會被重新
      檢查，磁碟上已經存在的跨 repo worktree 也不會因此消失——那兩件事屬對帳與清理，
      不屬本閘門。要看現況請跑 ``python -m wf_cli.registry``。
   3. **``origin`` 不是 GitHub 形狀的 repo 一律過不了。** 卡的 repo 來自 Issue URL，
      worktree 的 repo 來自 origin，兩者要能比對就要求 origin 導得出 ``owner/repo``。
      origin 是本機路徑（測試沙盒、bare 鏡像）時判不出來 → fail-closed 拒絕。
      這是刻意的，但它是一條真實的使用限制，不是可忽略的邊角。

   ⚠️ 第 2 條與 danger 的差別要分清楚：第 2 條是**射程內**的已知限制（登記面本身
   還有沒被覆蓋的登記——既有列不重掃）；danger 講的是**射程外**（建立面整條路徑
   本閘門碰不到）。前者本卡可以做而選擇不做，後者本卡做不到。

**與 ``TasksMdRegistry`` 的隔離**：守衛的輸入（Issue URL、git commondir、來源 repo）
都是即時事實，**都不經過 ``TASKS.md`` 投影**。這是刻意的——2026-08-12 實測 ``doctor``
把六個 WF 卡的 worktree 全報為孤兒，正是因為它讀已封存的 ``TASKS.md``。守衛函式的
簽章裡沒有任何 registry 參數，投影再怎麼過時都影響不到它
（``test_registry.py::test_guard_verdict_unaffected_by_stale_tasks_md_projection``
以「刻意寫一份錯誤的 TASKS.md」實測這條隔離）。

**枚舉器**（R1-03）：``python -m wf_cli.registry`` 是唯讀枚舉器，把「現況全部
(卡, worktree) 配對逐筆判定」變成可重跑的指令輸出，取代 commit message 裡不可重跑
的數字。它可從 GitHub Project 現拉輸入（``--from-project``），也可重播先前產物
（``--input``）；產物內含它用的全部輸入列，因此重播是不動點（§6.2）。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
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


#: worktree 所屬 repo 的三種取得方式，**權威性由高到低**：
#:
#: - ``source_repo``：呼叫端明示「這筆登記所主張的來源 repo」。它對應 git 的真語意
#:   ——``git -C <src> worktree add <任意路徑>`` 產生的 worktree 永遠屬於 ``<src>``，
#:   **與目標路徑落在磁碟哪裡無關**。
#:
#:   ⚠️ **它是被 git 驗證過的宣告，不是被觀測到的建立行為。** 本模組驗的是「這個
#:   目錄確實是個有 GitHub 形狀 origin 的 repo」，**沒有執行也沒有觀測任何
#:   ``git worktree add``，更沒有把後續的建立動作綁到它**。因此給了與卡相符的
#:   ``source_repo`` 取得 allow 之後，仍然可以從別的 repo 直接建立——**那條路徑
#:   在本卡射程外**（見本檔頂端 danger）。這是登記面守衛的定義，不是漏洞掩飾：
#:   登記面能保證的上限就是「這筆登記的主張自洽且與卡相符」。
#: - ``target_dir``：目標路徑**已存在**且本身在某個 git repo 內。worktree 就在那裡，
#:   這是事實不是推測。
#: - ``ancestor_dir``：目標尚未建立，改問最近存在的祖先目錄。**這是推測**
#:   （``inferred=True``）：路徑巢狀於某 repo 內只是本專案的慣例，canonical §4.5
#:   明文「worktree 路徑與分支名由實際建立者決定」，並未要求巢狀。
ProbeSource = Literal["source_repo", "target_dir", "ancestor_dir"]


@dataclass(frozen=True)
class WorktreeRepoProbe:
    """「worktree 目標 repo」的探測結果。"""

    slug: str | None
    #: slug 由哪一種來源導出；判不出來時為 None。
    source: ProbeSource | None = None
    #: 解析後的絕對目標路徑；相對路徑且未綁定 base_dir 時為 None。
    resolved_target: str | None = None
    #: 實際被問到的目錄。
    probed_dir: str | None = None
    common_dir: str | None = None
    remote_url: str | None = None
    detail: str = ""
    #: slug 由 ``ancestor_dir`` 推測而來（非事實）。誤擋風險集中在這一格。
    inferred: bool = False
    #: 相對路徑且既沒有 ``base_dir`` 也沒有 ``source_repo``——路徑本身不帶任何
    #: repo 資訊（``.claude/worktrees/x`` 在兩個 repo 底下是同一串字），故不可判定。
    unanchored: bool = False
    #: 目標路徑**座落**在哪個 repo 的工作樹內（可與 ``slug`` 不同：submodule 的
    #: worktree 掛在父 repo 路徑底下正是 §8.3 漂移得以隱形的形狀）。純資訊，不參與判定。
    nested_repo: str | None = None


def _nearest_existing_dir(path: Path) -> Path | None:
    current = path
    while True:
        if current.is_dir():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _slug_of_dir(probe_dir: Path, git: GitProbe) -> tuple[str | None, str | None, str | None, str]:
    """問一個既存目錄屬於哪個 repo，回傳 ``(slug, common_dir, remote_url, detail)``。

    比對軸是 **origin remote 的 slug**，不是路徑：``commondir`` 對 submodule 會落在
    父 repo 的 ``.git/modules/...`` 底下，用路徑比對會把 submodule 誤判成父 repo。
    同一個 repo 的所有 worktree 共用 commondir，故 remote 也共用——這正是等價類。
    """
    common_dir = git(probe_dir, ["rev-parse", "--path-format=absolute", "--git-common-dir"])
    if common_dir is None:
        return None, None, None, f"{probe_dir} 不在任何 git repo 內（rev-parse --git-common-dir 失敗）"
    remote_url = git(probe_dir, ["remote", "get-url", "origin"])
    if remote_url is None:
        return None, common_dir, None, (
            f"repo（commondir {common_dir}）沒有 origin remote，無法導出 owner/repo"
        )
    slug = normalize_repo_slug(remote_url)
    if slug is None:
        return None, common_dir, remote_url, f"origin remote {remote_url!r} 無法解析為 owner/repo"
    return slug, common_dir, remote_url, f"commondir {common_dir} 的 origin → {slug}"


_SOURCE_REPO_REMEDY = (
    "worktree 可以合法地建在 repo 之外（canonical §4.5：路徑由實際建立者決定，"
    "未限定巢狀於 repo），因此路徑本身不足以導出所屬 repo——"
    "請以 source_repo 明示實際執行 git worktree add 的來源 repo 後重試"
)


def _nested_repo_slug(resolved: Path, git: GitProbe) -> str | None:
    """目標路徑座落在哪個 repo 的工作樹內（問它的父目錄）。純資訊、不參與判定。"""
    anchor = _nearest_existing_dir(resolved.parent)
    if anchor is None:
        return None
    return _slug_of_dir(anchor, git)[0]


def probe_worktree_repo(
    worktree_path: str | Path,
    *,
    source_repo: str | Path | None = None,
    base_dir: str | Path | None = None,
    git: GitProbe = run_git_readonly,
) -> WorktreeRepoProbe:
    """導出這個 worktree 會屬於哪個 repo（#16 §7：worktree 的 repo ← commondir）。

    **目標 repo 的語意**（R1-02）：worktree 的所屬 repo 由 ``git worktree add`` 的
    **來源 repo** 決定，**不是**由目標路徑座落在磁碟哪裡決定。三種取得方式的權威性
    見 ``ProbeSource``。優先序：``source_repo`` → 既存的目標目錄 → 祖先目錄（推測）。

    因此：

    - **repo 外的絕對路徑是合法配置**，給了 ``source_repo`` 就判得出來，不再落到
      「祖先是 ``/tmp`` 之類非 git 目錄 → block」。這是舊版被打穿的那條。
    - **相對路徑必須綁定明確 ``base_dir``**（或改給 ``source_repo``）。
      **本函式不再讀 ``Path.cwd()``**：``.claude/worktrees/x`` 在兩個 repo 底下是
      完全相同的字串，路徑本身零資訊，用 cwd 補等於讓判定隨「在哪執行」而變。
      兩者都沒有時回 ``unanchored=True``，交由 ``check_worktree_repo_ownership``
      fail-closed，訊息指名補法。
    - **祖先推測仍保留**（``inferred=True``），因為 ``assign`` 早於 ``git worktree add``
      時它是唯一能在寫入前生效的線索；但它被明確標成推測，被它擋下的訊息一律附上
      「若非如此請以 source_repo 明示」的出路。
    """
    target = Path(worktree_path).expanduser()
    resolved: Path | None
    unanchored = False
    if target.is_absolute():
        resolved = target
    elif base_dir is not None:
        # 只做接合、不做 resolve()：產物要留住登記的原樣，resolve 會改寫 symlink
        # （macOS 的 /tmp → /private/tmp）而讓對帳的人對不上自己登記的字串。
        resolved = Path(base_dir).expanduser() / target
    else:
        resolved = None
        unanchored = True

    resolved_str = str(resolved) if resolved is not None else None

    # (1) 權威來源：實際會執行 git worktree add 的 repo。目標路徑落在哪裡都不影響。
    if source_repo is not None:
        src = Path(source_repo).expanduser()
        if not src.is_dir():
            return WorktreeRepoProbe(
                slug=None, resolved_target=resolved_str, unanchored=unanchored,
                detail=f"source_repo {src} 不是既存目錄，無法作為來源 repo",
            )
        slug, common_dir, remote_url, detail = _slug_of_dir(src, git)
        return WorktreeRepoProbe(
            slug=slug, source="source_repo" if slug else None, resolved_target=resolved_str,
            probed_dir=str(src), common_dir=common_dir, remote_url=remote_url,
            detail=f"source_repo {src}：{detail}", unanchored=unanchored,
            nested_repo=_nested_repo_slug(resolved, git) if resolved is not None else None,
        )

    # (2) 相對路徑 ＋ 無 base_dir ＋ 無 source_repo → 路徑不帶 repo 資訊，不可判定。
    if resolved is None:
        return WorktreeRepoProbe(
            slug=None, resolved_target=None, unanchored=True,
            detail=(
                f"worktree 路徑 {worktree_path!r} 是相對路徑，但未綁定 base_dir 也未給 "
                "source_repo；相對路徑在任何 repo 底下都是同一串字，不帶所屬 repo 資訊"
            ),
        )

    # (3) 目標已存在 → 它就在某個 repo 裡，這是事實。
    if resolved.is_dir():
        slug, common_dir, remote_url, detail = _slug_of_dir(resolved, git)
        if slug is None:
            detail = f"{detail}；{_SOURCE_REPO_REMEDY}"
        return WorktreeRepoProbe(
            slug=slug, source="target_dir" if slug else None, resolved_target=resolved_str,
            probed_dir=resolved_str, common_dir=common_dir, remote_url=remote_url,
            detail=detail, nested_repo=_nested_repo_slug(resolved, git),
        )

    # (4) 目標尚未建立 → 問最近存在的祖先，但標記為推測。
    anchor = _nearest_existing_dir(resolved)
    if anchor is None:
        return WorktreeRepoProbe(
            slug=None, resolved_target=resolved_str,
            detail=f"路徑 {resolved} 與其所有祖先皆不存在；{_SOURCE_REPO_REMEDY}",
        )
    slug, common_dir, remote_url, detail = _slug_of_dir(anchor, git)
    if slug is None:
        detail = (
            f"目標 {resolved} 尚未建立，最近存在的祖先 {anchor} 導不出 repo（{detail}）；"
            f"{_SOURCE_REPO_REMEDY}"
        )
    else:
        detail = f"目標 {resolved} 尚未建立，改問最近存在的祖先 {anchor}：{detail}（推測）"
    return WorktreeRepoProbe(
        slug=slug, source="ancestor_dir" if slug else None, resolved_target=resolved_str,
        probed_dir=str(anchor), common_dir=common_dir, remote_url=remote_url,
        detail=detail, inferred=slug is not None, nested_repo=slug,
    )


OwnershipDecision = Literal["allow", "block"]
OwnershipReason = Literal[
    "match",
    "repo_mismatch",
    "card_repo_undeterminable",
    "worktree_repo_undeterminable",
    "worktree_path_unanchored",
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
    "worktree_path_unanchored": "block",
}


@dataclass(frozen=True)
class RepoOwnershipVerdict:
    reason_code: OwnershipReason
    card_repo: str | None
    worktree_repo: str | None
    detail: str
    #: worktree repo 由祖先目錄推測而來（``ProbeSource.ancestor_dir``）。被這種判定
    #: 擋下的人必須看到「若推測不成立該怎麼補」，否則就是無出路的誤擋。
    inferred: bool = False

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

        另有一條**判定層**的出路（R1-02）：判定不成立時補 ``source_repo``。它不是
        ``--force``——補的是**更權威的宣告且會被 git 驗證**，補完照樣要通過同一組
        比對；``--force`` 則是繞過比對。這個差別是本守衛刻意沒有 ``--force`` 的理由
        仍然成立的原因。

        訊息刻意說「拒絕登記」而不是「已阻止建立」：被擋下的是**這一筆歸屬登記**，
        磁碟上的 worktree 本閘門既不建立也不移除（射程見本檔頂端 danger）。
        """
        head = {
            "repo_mismatch": (
                f"這筆登記會把 worktree 歸給 {self.worktree_repo}，但卡屬於 "
                f"{self.card_repo}——跨 repo 錯置，拒絕登記"
            ),
            "card_repo_undeterminable": "判不出卡所屬 repo",
            "worktree_repo_undeterminable": "判不出 worktree 目標 repo",
            "worktree_path_unanchored": "worktree 路徑是相對路徑，未綁定明確 base_dir",
            "match": "（未被擋）",
        }[self.reason_code]
        if self.reason_code == "match":
            return head
        extra = ""
        if self.inferred:
            extra = (
                "（此判定由尚未建立之目標的最近存在祖先**推測**而得；"
                "若你實際是從別的 repo 執行 git worktree add，請以 source_repo 明示後重試）"
            )
        elif self.reason_code == "worktree_path_unanchored":
            extra = "（補法：改給絕對路徑，或指定 base_dir／source_repo）"
        return (
            f"{head}；{self.detail}。{extra}"
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
    2. **判不出來的每一種輸入都可在一分鐘內補齊，補法寫在拒絕訊息裡。**
       （上一輪這裡寫的是「每一種輸入都不是合法穩態」，**那句是錯的**，R1-02 舉出
       反例：repo 外的絕對路徑是 canonical §4.5 允許的合法配置。修法是加
       ``source_repo`` 這條補齊管道，不是繼續宣稱它不合法。）
       ``card_repo_undeterminable`` 只發生在 DraftIssue（卡不在任何 repo 裡——但
       ``assign`` 本來就要把 Log 寫回卡面，正式流程要求真 Issue）；
       ``worktree_repo_undeterminable`` 發生在路徑打錯、目標不在任何 git repo 內、
       或 repo 沒有 origin remote；``worktree_path_unanchored`` 發生在相對路徑未綁
       ``base_dir``。三者的補法分別是「改用真 Issue」「修路徑或補 ``source_repo``」
       「改絕對路徑或補 ``base_dir``／``source_repo``」，都不需要放行一次壞輸入。
    3. **fail-closed 不會被無關的故障觸發。** 卡 repo 來自 ``ItemSnapshot.issue_url``，
       那是 ``assign`` 早已為了別的理由抓下來的同一份資料；GitHub 掛掉時 ``assign``
       在到達本守衛之前就已經失敗。守衛**不新增任何網路相依**——這是 fail-closed
       站得住的前提，否則它會變成「別人的服務抖一下，全隊都不能派工」。

    刻意**沒有** ``--force``／``--allow-cross-repo`` 逃生口：漂移案例的成因不是
    有人想跨 repo，是沒人注意到自己跨了。給逃生口等於把「沒注意到」變成「按一下」。
    ``source_repo``（R1-02）**不是**逃生口：它補的是更權威且經 git 驗證的宣告，補完
    仍要通過同一組比對，補錯照樣被擋；``--force`` 則是把比對整個跳過。

    ⚠️ 本函式判的是**一筆登記**該不該寫下去。它不觀測、也擋不住磁碟上的建立動作
    （見本檔頂端 danger）。
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
            reason_code=(
                "worktree_path_unanchored" if worktree_probe.unanchored
                else "worktree_repo_undeterminable"
            ),
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
            inferred=worktree_probe.inferred,
        )
    return RepoOwnershipVerdict(
        reason_code="match",
        card_repo=card_repo,
        worktree_repo=worktree_probe.slug,
        detail=worktree_probe.detail,
        inferred=worktree_probe.inferred,
    )


def check_assign_repo_ownership(
    *,
    issue_url: str | None,
    worktree_path: str | Path,
    source_repo: str | Path | None = None,
    base_dir: str | Path | None = None,
    git: GitProbe = run_git_readonly,
) -> RepoOwnershipVerdict:
    """``assign`` 用的端到端判定：卡的 Issue URL ＋ ``--worktree`` 路徑 → 判定。

    這是 ``commands/assign_cmd.py::run`` 實際呼叫的那一個函式（已接線；接線後仍不
    成立的三件事見本檔頂端 warning，射程邊界見 danger）。簽章刻意只吃事實輸入，沒有
    ``TasksMdRegistry``／``--repo``／設定檔——投影過時或呼叫端環境設錯都影響不到
    判定。``source_repo`` 是唯一由呼叫端提供的輸入，它必須通過 git 驗證（既存且有
    GitHub 形狀 origin 的 repo）才算數；但**驗證的是那個目錄的身分，不是後續真的
    從那裡建立**——本函式回 ``allow`` 的意思是「這筆登記可以寫下去」，不是「建立
    行為已被綁定」。
    """
    return check_worktree_repo_ownership(
        card_repo=card_repo_from_issue_url(issue_url),
        worktree_probe=probe_worktree_repo(
            worktree_path, source_repo=source_repo, base_dir=base_dir, git=git
        ),
    )


# ---------------------------------------------------------------------------
# 唯讀枚舉器（R1-03）：把「現況全部配對逐筆判定」變成可重跑的指令輸出
# ---------------------------------------------------------------------------
#
# 為什麼是這個形狀：
#
# - **取代 commit message 的數字。** 「67 筆 64 allow／3 block」寫在 commit message
#   裡沒有任何人能重算。§6.2 要求完整性宣稱由指令輸出產生、artifact 在交付 HEAD
#   可重現，所以判定必須有一個唯讀入口，且它的產物要**內含它用過的全部輸入**。
# - **不動點。** 產物的 ``input.rows`` 可以直接餵回 ``--input``；磁碟狀態不變時
#   重跑逐字節相同（產物刻意**不含時間戳**——時間戳會讓不動點永遠不成立）。
# - **自指命中可見列計。** 本卡自己（WF-WORKTREE-REPO-OWNERSHIP1）與本 worktree
#   就在被掃的資料裡，不做任何排除，照常列出。
# - **不改 registry 的相依形狀。** ``gh`` 只在 ``main()``／``fetch_*`` 這條 CLI 路徑
#   上以 ``subprocess`` 呼叫（``subprocess`` 早已 import），判定路徑與 ``doctor``
#   import 本模組時**不新增任何相依**，守衛「不引入網路相依」的前提未被動搖。

#: 一列輸入的最小形狀。多的鍵一律保留於產物內，不丟。
OwnershipInputRow = dict[str, "str | None"]


@dataclass(frozen=True)
class OwnershipRow:
    """一筆 (卡, worktree) 配對的判定結果。欄位即產物欄位。"""

    card_id: str | None
    issue_url: str | None
    branch: str | None
    worktree_raw: str | None
    card_repo: str | None
    resolved_target: str | None
    target_exists: bool
    probe_source: str | None
    inferred: bool
    worktree_repo: str | None
    nested_repo: str | None
    reason_code: str
    decision: str
    detail: str

    def as_dict(self) -> dict[str, object]:
        return {
            "card_id": self.card_id,
            "issue_url": self.issue_url,
            "branch": self.branch,
            "worktree_raw": self.worktree_raw,
            "card_repo": self.card_repo,
            "resolved_target": self.resolved_target,
            "target_exists": self.target_exists,
            "probe_source": self.probe_source,
            "inferred": self.inferred,
            "worktree_repo": self.worktree_repo,
            "nested_repo": self.nested_repo,
            "reason_code": self.reason_code,
            "decision": self.decision,
            "detail": self.detail,
        }


TSV_COLUMNS = [
    "card_id", "card_repo", "worktree_raw", "resolved_target", "target_exists",
    "probe_source", "inferred", "worktree_repo", "nested_repo", "reason_code",
    "decision", "issue_url",
]


def enumerate_ownership(
    rows: list[OwnershipInputRow],
    *,
    base_dir: str | Path | None = None,
    git: GitProbe = run_git_readonly,
) -> list[OwnershipRow]:
    """對每一筆輸入跑同一組判定函式（**不是**另一套邏輯）。

    輸入列可給 ``worktree_path``，或給 Ledger 慣例的複合字串 ``branch_worktree``
    （``branch @ path``）。沒有 worktree 註冊的列不在此函式的職責內——呼叫端先濾。
    """
    out: list[OwnershipRow] = []
    for raw in rows:
        branch = raw.get("branch")
        worktree = raw.get("worktree_path")
        if worktree is None and raw.get("branch_worktree"):
            # 先剝 markdown code span 的反引號，與 ``parse_active_ledger`` 同一手法：
            # Project 欄位實際存著 ``` `branch @ path` ```（實測 OPS-STATE-PLANE-MIG1），
            # 不剝的話尾端反引號會留在路徑裡，讓存在的目錄被判成不存在。
            branch, worktree = parse_branch_worktree((raw["branch_worktree"] or "").strip("` "))
        issue_url = raw.get("issue_url")
        probe = probe_worktree_repo(worktree or "", base_dir=base_dir, git=git)
        verdict = check_worktree_repo_ownership(
            card_repo=card_repo_from_issue_url(issue_url), worktree_probe=probe
        )
        out.append(
            OwnershipRow(
                card_id=raw.get("card_id"),
                issue_url=issue_url,
                branch=branch,
                worktree_raw=worktree,
                card_repo=verdict.card_repo,
                resolved_target=probe.resolved_target,
                target_exists=bool(
                    probe.resolved_target and Path(probe.resolved_target).is_dir()
                ),
                probe_source=probe.source,
                inferred=probe.inferred,
                worktree_repo=probe.slug,
                nested_repo=probe.nested_repo,
                reason_code=verdict.reason_code,
                decision=verdict.decision,
                detail=probe.detail,
            )
        )
    return out


def summarize_ownership(rows: list[OwnershipRow]) -> dict[str, object]:
    """摘要與逐列產物**同一次執行**產生（§6.2：宣稱的數字與 artifact 同源）。"""
    by_reason: dict[str, int] = {}
    by_source: dict[str, int] = {}
    for r in rows:
        by_reason[r.reason_code] = by_reason.get(r.reason_code, 0) + 1
        key = r.probe_source or "undeterminable"
        by_source[key] = by_source.get(key, 0) + 1
    return {
        "total": len(rows),
        "allow": sum(1 for r in rows if r.decision == "allow"),
        "block": sum(1 for r in rows if r.decision == "block"),
        "target_exists": sum(1 for r in rows if r.target_exists),
        "inferred": sum(1 for r in rows if r.inferred),
        "by_reason_code": dict(sorted(by_reason.items())),
        "by_probe_source": dict(sorted(by_source.items())),
    }


_PROJECT_ITEMS_GQL = (
    "query($owner:String!,$number:Int!,$after:String){"
    "user(login:$owner){projectV2(number:$number){items(first:50,after:$after){"
    "pageInfo{hasNextPage endCursor} nodes{content{__typename ... on Issue{url number}} "
    "fieldValues(first:50){nodes{__typename ... on ProjectV2ItemFieldTextValue"
    "{text field{... on ProjectV2FieldCommon{name}}}}}}}}}}"
)


def _run_gh_graphql(payload: dict[str, object]) -> dict[str, object]:
    """走 ``gh api graphql --input -``。

    刻意**不用** ``gh project item-list``：它對中文欄位名的 JSON key 有編碼錯誤
    （``project.py::list_items`` 已記錄此雷；本檔實測 ``卡ID`` 被輸出成 U+FFFD）。
    """
    proc = subprocess.run(
        ["gh", "api", "graphql", "--input", "-"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh api graphql 失敗（exit {proc.returncode}）：{proc.stderr.strip()}")
    return json.loads(proc.stdout)


def fetch_project_ownership_rows(
    owner: str, number: int, *, run: Callable[[dict], dict] = _run_gh_graphql
) -> list[OwnershipInputRow]:
    """從 GitHub Project 拉出全部「有 worktree 註冊」的 (卡, worktree) 配對。

    這是唯讀查詢。回傳的列會原樣寫進產物的 ``input.rows``，因此產物本身即是可重播
    的釘住輸入（``--input``）。
    """
    rows: list[OwnershipInputRow] = []
    after: str | None = None
    while True:
        payload = {
            "query": _PROJECT_ITEMS_GQL,
            "variables": {"owner": owner, "number": number, "after": after},
        }
        data = run(payload)
        items = (
            ((data.get("data") or {}).get("user") or {}).get("projectV2") or {}
        ).get("items") or {}
        for node in items.get("nodes", []):
            content = node.get("content") or {}
            fields: dict[str, str] = {}
            for fv in (node.get("fieldValues") or {}).get("nodes", []):
                name = (fv.get("field") or {}).get("name")
                if name and "text" in fv:
                    fields[name] = fv["text"]
            bw = next((v for k, v in fields.items() if "worktree" in k), None)
            if not bw or not bw.strip() or bw.strip() == "—":
                continue
            rows.append(
                {
                    "card_id": fields.get("卡ID"),
                    "issue_url": content.get("url"),
                    "branch_worktree": bw,
                }
            )
        page = items.get("pageInfo") or {}
        if not page.get("hasNextPage"):
            return rows
        after = page.get("endCursor")


def _render_tsv(rows: list[OwnershipRow], summary: dict[str, object]) -> str:
    lines = ["\t".join(TSV_COLUMNS)]
    for r in rows:
        d = r.as_dict()
        lines.append("\t".join("" if d[c] is None else str(d[c]) for c in TSV_COLUMNS))
    lines.append(f"# summary\t{json.dumps(summary, ensure_ascii=False, sort_keys=True)}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """``python -m wf_cli.registry``：唯讀枚舉器。**不寫任何遠端狀態、不改磁碟。**"""
    parser = argparse.ArgumentParser(
        prog="python -m wf_cli.registry",
        description="唯讀枚舉：對現況每一筆 (卡, worktree) 配對跑跨 repo 歸屬判定",
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--from-project", metavar="OWNER/NUMBER", help="現拉 GitHub Project（唯讀）")
    src.add_argument(
        "--input", metavar="FILE",
        help="重播先前產物或原始輸入列（JSON：{\"rows\":[...]} 或本工具的產物）",
    )
    parser.add_argument("--format", choices=("json", "tsv"), default="json")
    parser.add_argument("--output", metavar="FILE", help="輸出檔；省略則印到 stdout")
    parser.add_argument(
        "--base-dir", metavar="DIR", default=None,
        help="相對 worktree 路徑的錨點。**不給就是不給**——本工具不會拿 cwd 當預設，"
             "沒有錨點的相對路徑一律判 worktree_path_unanchored（見 probe 的說明）。",
    )
    args = parser.parse_args(argv)

    if args.from_project:
        owner, _, number = args.from_project.partition("/")
        if not owner or not number.isdigit():
            parser.error("--from-project 格式為 OWNER/NUMBER，例如 ruan6047/4")
        rows = fetch_project_ownership_rows(owner, int(number))
        source = f"gh api graphql → user({owner}).projectV2(number:{number}).items"
    else:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        block = payload.get("input", payload)
        rows = block.get("rows", [])
        source = block.get("source") or f"replay of {args.input}"

    results = enumerate_ownership(rows, base_dir=args.base_dir)
    summary = summarize_ownership(results)
    artifact = {
        "tool": "python -m wf_cli.registry",
        "input": {"source": source, "base_dir": args.base_dir, "rows": rows},
        "rows": [r.as_dict() for r in results],
        "summary": summary,
    }
    text = (
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.format == "json"
        else _render_tsv(results, summary)
    )
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


__all__ = [
    "OWNERSHIP_DECISIONS",
    "TSV_COLUMNS",
    "GitProbe",
    "OwnershipDecision",
    "OwnershipInputRow",
    "OwnershipReason",
    "OwnershipRow",
    "ProbeSource",
    "RegisteredCard",
    "RepoOwnershipVerdict",
    "TasksMdRegistry",
    "WorktreeRepoProbe",
    "card_repo_from_issue_url",
    "check_assign_repo_ownership",
    "check_worktree_repo_ownership",
    "enumerate_ownership",
    "fetch_project_ownership_rows",
    "load_tasks_md_registry",
    "main",
    "normalize_repo_slug",
    "parse_active_ledger",
    "parse_archived_card_ids",
    "parse_markdown_tables",
    "probe_worktree_repo",
    "run_git_readonly",
    "summarize_ownership",
]


if __name__ == "__main__":  # pragma: no cover - 入口薄殼，行為全在 main()
    raise SystemExit(main())
