"""卡註冊來源（可插拔）：doctor 用來判斷「這個 worktree 對得上哪張卡」。

遷移尚未 cutover 的專案（如 cpbl-analytics）目前仍以 ``docs/TASKS.md`` 的 Ledger
表格作為 current-state 事實來源；已 cutover 的專案改用 GitHub Project（見
``project.py``）。doctor／snapshot 的骨架刻意不綁定其中一種（卡面〈依賴與順序〉：
「doctor／snapshot 骨架不依賴 Issues 結構，可立即先行」），所以這裡定義一個共同的
最小介面 ``RegisteredCard``，兩種來源各自轉成這個形狀。

跨 repo 歸屬守衛（WF-WORKTREE-REPO-OWNERSHIP1 / #57）
=====================================================

本檔後半段（``normalize_repo_slug`` 起）是 ``WF-ORCHESTRATION-RECONCILE1``（#16）
§7「repo 歸屬純導出」的**判定引擎**。它由**兩條互不相通的軸**組成，這個分軸本身就是
``docs/ROADMAP.md`` §1.5（需求方 2026-08-13 裁定）的實作：

    **欄位若同時承載可攜的宣告與機器局部的操作細節，判定必須建立在可攜的那一半上。**

+----------------------+--------------------------------------------------------+
| 軸 A **歸屬判定**    | 卡的 repo ← Issue URL；worktree 的 repo ← **這筆登記    |
| （可攜）             | 宣告的 repo slug**。兩個都是字串，比對是純字串比對——    |
|                      | ``check_assign_repo_ownership`` 的簽章裡**沒有任何路徑、|
|                      | 沒有任何目錄、不讀檔案系統、不呼叫 git**。因此它在任何   |
|                      | 一台機器上對同一張卡＋同一個宣告得到**同一個結果**。    |
+----------------------+--------------------------------------------------------+
| 軸 B **本機觀測**    | 登記的路徑在**這台機器**上解析得到什麼。它只回答「這台   |
| （機器局部）         | 機器現在看到什麼」，**不回答 repo 的事實**，也**不參與   |
|                      | 軸 A 的判定**。換一台機器它多半什麼都看不到，而**看不到 |
|                      | 不是判定**。                                            |
+----------------------+--------------------------------------------------------+

⚠️ **上一版把這兩者混在同一條軸上，並且判定建在錯的那一半。** 舊的
``probe_worktree_repo`` 從路徑讀 ``commondir`` 反推 repo；``/Users/ruanruan/Dev/…``
只在單一台機器成立，換一台機器該探測必然失敗。需求方 2026-08-13 的查證同時指出
``.claude/worktrees/xxx`` 這種**相對**路徑其實比絕對路徑更可攜（在任何 clone 上指向
同一相對位置），也就是說先前收緊的方向**收緊的是比較不可攜的那一種**。所以本版：
歸屬由 slug 表達，路徑退回它該待的位置。

⚠️ **路徑不可移除，也沒有被移除。** ``cleanup.py`` 用它做破壞性收尾
（``status --porcelain`` 檢查乾淨、``resolve()`` 後刪除），``doctor``／``snapshot``／
``handoff`` 亦讀它。本模組拿掉的只有一件事：**路徑不再是歸屬的證據**。

**承諾範圍（需求方 2026-08-13 二次裁定，#57 issuecomment-5273953073）**：本守衛承諾的是
``wfcli assign`` **這一條路徑**上的跨 repo 歸屬檢查，**不是「登記面已被保護」**。
本檔任何一句都不得被讀成「``git worktree add`` 建到錯的 repo 會被擋下」，
也不得被讀成「``分支worktree`` 欄不可能被寫成跨 repo 的值」。

§8.3 的真實漂移（cpbl 卡的 worktree 建在 ai-workflow repo 內）之所以能存在數週，
是因為系統只有 ``doctor`` 的**事後對帳**——而該對帳看不見這種形狀（兩個 repo 的頂層
``git worktree list`` 皆 0 命中）。本模組把「**經 assign** 登記一筆跨 repo 歸屬」從沉默
變成當場拒絕；射程外的三條路徑列在下方 danger，**它們是已知限制，不是待辦**。

**機械執行者**：``commands/assign_cmd.py`` 的 ``run()``。它在**任何**
``set_field_value``／``set_item_body`` 之前依序呼叫 ``check_assign_repo_ownership``
（軸 A，``blocked`` → return 5）與 ``observe_local_worktree``（軸 B，``refuses`` →
return 6），兩者都是零寫入拒絕。``assign`` 是 wfcli 全域唯一會寫 ``分支worktree`` 欄的
指令（全域無任何 ``git worktree add``，實測零命中），所以那裡就是 ``wfcli``
**這條路徑上**唯一有效的攔截位置——**「wfcli 這條路徑」不等於「所有寫入路徑」**，
見 danger 第 2 條。

.. danger::

   **本守衛擋的是 ``wfcli assign`` 這一條路徑上的登記；不是登記面整體，更不是建立。**

   需求方 2026-08-13 二次裁定明列**三條射程外的路徑，皆為已知限制而非待辦**：

   1. **``git worktree add`` 直接建立。** ``wfcli`` 全域沒有任何 ``git worktree add``
      （實測零命中），因此人在 shell 裡直接建立 worktree **完全不經過本閘門**：
      先建立再登記時，被擋下的是登記那一步，磁碟上那個建錯 repo 的目錄已經存在且
      不會被本閘門移除；建立後**不登記**，本閘門連看都看不到。該裁定明文要求下面
      這句**逐字保留、不得因射程縮小而軟化**：

          該卡未落地前，本 repo 對「人直接在 shell 建到錯的 repo」沒有任何預防

      同一句在派審詞裡的等義寫法，一併逐字留存：

          該卡未落地前，本 repo 對「人直接在 shell 跑 git worktree add 建到錯的 repo」沒有任何預防

   2. **Project 欄位直接寫入。** ``分支worktree`` 是 GitHub Project 的 **TEXT 欄**，
      web UI、``gh project item-edit``、GraphQL 三條路都能直接改寫它，一次都不會經過
      本閘門。「唯一寫入通道＝wfcli」是**治理慣例，不是機制**；而 Project 的欄位權限
      是 **setting、不是檔案、不在資源模型的值域裡**（``docs/ROADMAP.md`` §2），
      本卡不可能為它宣告寫入集、也就不可能為它加執行者。需求方 2026-08-13 要求這一條
      以與上面**同等的強度**寫下：

          本 repo 對「有人繞過 wfcli 直接改寫 Project 的分支worktree 欄」沒有任何預防

   3. **既有登記不重掃。** 本閘門只在新的 assign 寫入時生效；Project 上已經存在的
      註冊列（本輪實測 64 筆）不會因為本卡落地而被重新檢查，磁碟上已經存在的跨 repo
      worktree 也不會因此消失。要看現況只能自己跑 ``python -m wf_cli.registry``——
      **那是枚舉器，不是執行者**（``docs/ROADMAP.md`` §0：沒有執行者的偵測器不算
      達成目標 1）。

   ⚠️ **兩次縮射程的形狀完全相同：``wfcli`` 是慣例不是機制。** 第 1 條與第 2 條不是
   兩個不同的問題，是同一句話在建立面與登記面各講一次。讀本檔的人若想加第三個閘門，
   先問它守的是不是又一條「只有守規矩的人會走」的路。

   **承接者的現況（2026-08-13）**：建立面的承接卡**尚未開卡，今天沒有任何卡、任何碼、
   任何人承接建立面**；Project 欄位直接寫入依裁定**不開卡**（結構上拿不到執行者）。
   是否開卡與何時排程是需求方依 ``docs/ROADMAP.md`` §5 的判斷，不是本卡的交付物，
   本檔也不得假設它已被排程。在它落地之前，上面那些句子就是本 repo 的真實狀態。

.. warning::

   **接線之後，下列四件仍然不成立，寫報告與卡面時不得含混：**

   1. **``allow`` 不是「歸屬已被驗證」，只是「這筆登記的宣告與卡相符」。**
      軸 A 比的是兩個字串：卡的 Issue URL 導出的 slug，與這筆登記宣告的 slug。
      **宣告不是觀測**——本模組沒有執行也沒有觀測任何 ``git worktree add``，取得 allow
      之後人照樣可以從別的 repo 建立同一路徑
      （``test_registry.py::test_ownership_allow_does_not_bind_the_actual_creation``
      用真的 ``git worktree add`` 把這個殘留缺口釘成測試）。
      **這是 danger 第 1 條在判定層的倒影，不是新問題。** assign 發生在建立之前，
      而「歸屬」這個事實在建立之後才存在——單點檢查拿不到它。
   2. ⚠️ **不宣告即視為宣告「卡自己的 repo」，所以沒帶旗標的 assign 在軸 A 上必然通過。**
      這是刻意的、也是必須寫明的：``--worktree-source-repo`` 唯一合理的預設值就是卡自己
      的 repo，強迫每次手打一個工具已經知道的值，是 ``docs/ROADMAP.md`` §1 點名的
      「看起來在檢查、實際恆真」那種條文的社會層版本。因此軸 A 真正擋得住的只有
      **明示的**跨 repo 宣告——而那正是「人已經知道自己在跨 repo」的情形。
      **沒被注意到的漂移，軸 A 抓不到。** 抓得到的是軸 B，而軸 B 是機器局部的。
   3. **閘門只管新寫入的登記，不回溯。** 既有註冊（本輪實測 64 筆）不會被重新檢查，
      磁碟上已經存在的跨 repo worktree 也不會因此消失——那兩件事屬對帳與清理，不屬
      本閘門。要看現況請跑 ``python -m wf_cli.registry``。
   4. **軸 B 的沉默不是判定。** 它只在「登記的路徑在這台機器上解析得到、而且本身就是
      某個 repo 的 worktree」時才說得出話；目標尚未建立（生產常態）、相對路徑未錨定、
      或換一台機器，它一律沉默。**沉默＝這台機器沒有資訊**，不是「沒問題」。
      因此軸 B 拒絕的那一格（``contradiction``）在別台機器上不會重現——這是它與軸 A
      最重要的差別，也是它為什麼不准影響軸 A 的原因。

   ⚠️ 第 3 條與 danger 的差別要分清楚：第 3 條是**射程內**的已知限制（``wfcli assign``
   這條路徑本身還有沒被覆蓋的登記——既有列不重掃）；danger 講的是**射程外**（另外兩條
   寫入／建立路徑本閘門碰不到）。前者本卡可以做而選擇不做，後者本卡做不到。

   ⚠️ **本版相對於上一版的偵測落差，量測後誠實記錄**：Project #4 全量枚舉裡有一筆
   （``WF-25-REVIEW-WRITE-CHANNEL1``：ai-workflow 的卡、路徑指向 cpbl 目錄樹、目標
   尚未建立）上一版靠**祖先目錄推測**判成 ``repo_mismatch``／block，本版軸 A 看不到它
   （沒有明示宣告）、軸 B 也看不到它（目標不存在）。它降級為枚舉器的
   ``nesting_conflict`` **警示**——看得到、但沒有執行者。**這是本裁定的代價，不是疏漏**：
   那個 block 的全部證據就是「這條路徑座落在誰底下」，而該證據換一台機器即消失。

**與 ``TasksMdRegistry`` 的隔離**：守衛的輸入（Issue URL、登記宣告的 slug、軸 B 才用得到
的路徑）都是即時事實，**都不經過 ``TASKS.md`` 投影**。這是刻意的——2026-08-12 實測
``doctor`` 把六個 WF 卡的 worktree 全報為孤兒，正是因為它讀已封存的 ``TASKS.md``。
守衛函式的簽章裡沒有任何 registry 參數，投影再怎麼過時都影響不到它
（``test_registry.py::test_guard_verdict_unaffected_by_stale_tasks_md_projection``
以「刻意寫一份錯誤的 TASKS.md」實測這條隔離）。

**枚舉器**（R1-03）：``python -m wf_cli.registry`` 是唯讀枚舉器，把「現況全部
(卡, worktree) 配對逐筆判定」變成可重跑的指令輸出，取代 commit message 裡不可重跑
的數字。它可從 GitHub Project 現拉輸入（``--from-project``），也可重播先前產物
（``--input``）；產物內含它用的全部輸入列，因此重播是不動點（§6.2）。

⚠️ **枚舉器的兩欄要分開讀**：``ownership_*`` 欄是軸 A，換機器不變；``local_*`` 欄是
軸 B，**是「這台機器現在看到什麼」的快照，不是 repo 的事實**。需求方 2026-08-13 指出
先前那 64 筆一直被當成對帳視圖使用，而它對帳的是本機磁碟——本版把這件事寫進欄名，
不再靠讀的人自己記得。
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
    # 純點段（``.``／``..``）是路徑語法，不是 GitHub 名稱。不排掉它，``../ai-workflow``
    # 這種**相對目錄**會偽裝成合法 slug 進到歸屬判定裡——而拒絕目錄正是本版的重點。
    if owner.strip(".") == "" or repo.strip(".") == "":
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


def _nested_repo_slug(resolved: Path, git: GitProbe) -> str | None:
    """目標路徑座落在哪個 repo 的工作樹內（問它的父目錄）。**純資訊、不參與判定。**"""
    anchor = _nearest_existing_dir(resolved.parent)
    if anchor is None:
        return None
    return _slug_of_dir(anchor, git)[0]


# ---------------------------------------------------------------------------
# 軸 A：歸屬判定（可攜。純字串比對，不讀檔案系統）
# ---------------------------------------------------------------------------

OwnershipDecision = Literal["allow", "block"]
OwnershipReason = Literal[
    "match",
    "repo_mismatch",
    "card_repo_undeterminable",
    "declared_repo_unparseable",
]

#: reason_code → decision 的**全表**。``check_worktree_repo_ownership`` 一律從這裡
#: 導出 decision，不另外寫 if。表是封閉的：新增 reason 就必須在此明示它放不放行，
#: 不會有「忘了處理所以預設 allow」的縫。
#:
#: ``test_registry.py::test_only_match_produces_allow_exhaustively`` 對本表**窮舉**，
#: 證明 ``match`` 是唯一放行碼——不是抽樣。
OWNERSHIP_DECISIONS: dict[OwnershipReason, OwnershipDecision] = {
    "match": "allow",
    "repo_mismatch": "block",
    "card_repo_undeterminable": "block",
    "declared_repo_unparseable": "block",
}

#: 這筆登記所宣告的 repo 是**明示的**還是**取自卡自己的 repo**。
#:
#: ⚠️ ``card_repo_default`` 這一格在軸 A 上必然 ``match``——這不是被藏起來的縫，是
#: 刻意的設計，理由與代價寫在本檔頂端 warning 第 2 條，並由
#: ``test_registry.py::test_default_declaration_is_a_no_op_on_the_ownership_axis``
#: 逐字釘住。放行留痕必須帶上這個欄位，否則事後分不出「有人說了」與「沒人說」。
DeclarationBasis = Literal["explicit", "card_repo_default"]


@dataclass(frozen=True)
class RepoOwnershipVerdict:
    """軸 A 的判定。**它的每一個輸入都是可攜的字串**，所以它跨機器同值。"""

    reason_code: OwnershipReason
    card_repo: str | None
    #: 這筆登記主張 worktree 屬於哪個 repo（正規化後的 slug）。
    worktree_repo: str | None
    detail: str
    #: 上面那個 slug 是明示的，還是預設取自卡自己的 repo。
    basis: DeclarationBasis | None = None

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

        訊息刻意說「拒絕登記」而不是「已阻止建立」：被擋下的是**這一筆歸屬登記**，
        磁碟上的 worktree 本閘門既不建立也不移除（射程見本檔頂端 danger）。
        """
        head = {
            "repo_mismatch": (
                f"這筆登記主張 worktree 屬於 {self.worktree_repo}，但卡屬於 "
                f"{self.card_repo}——跨 repo 錯置，拒絕登記"
            ),
            "card_repo_undeterminable": "判不出卡所屬 repo",
            "declared_repo_unparseable": "宣告的來源 repo 解析不出 owner/repo",
            "match": "（未被擋）",
        }[self.reason_code]
        if self.reason_code == "match":
            return head
        extra = ""
        if self.reason_code == "declared_repo_unparseable":
            extra = (
                "（補法：--worktree-source-repo 收的是 **repo slug**（``owner/repo``，"
                "也接受 GitHub remote／Issue URL），**不是目錄**。改收 slug 是因為目錄"
                "只在單一台機器成立，而歸屬必須跨機器可稽核——本機路徑仍然要給，但它給的"
                "是 --worktree，供 cleanup／doctor 使用，不參與歸屬判定）"
            )
        return (
            f"{head}；{self.detail}。{extra}"
            "合法路徑（#16 §7.1）：工作落在哪個 repo，卡就開在哪個 repo；"
            "跨 repo 需求請在目標 repo 另開實作卡，兩張卡以 spec 基線的 Issue URL 互相連結。"
        )


def check_worktree_repo_ownership(
    *,
    card_repo: str | None,
    declared_repo: str | None = None,
) -> RepoOwnershipVerdict:
    """比對卡 repo 與**這筆登記宣告的** repo，回傳判定。

    **本函式不接受路徑、不接受目錄、不呼叫 git、不碰檔案系統。** 這不是實作細節，
    是 ``docs/ROADMAP.md`` §1.5 的裁定在簽章層的形狀：判定必須建立在可攜的那一半上，
    所以能進來的東西只有可攜的東西。
    ``test_registry.py::test_ownership_axis_never_touches_the_filesystem`` 把
    ``subprocess`` 整支換成會爆炸的替身來釘死這條。

    **判不出來時 fail-closed（擋下），不放行。** 二擇一的論證：

    1. **代價不對稱。** 誤擋的代價是**當場、對人、可讀**的一次拒絕，附合法出路；
       誤放的代價是 §8.3 那種**沉默**的錯置——worktree 建在錯的 repo 照樣能寫程式、
       能 commit，數週後才在對帳裡浮出來，而那份對帳自己還會誤報。可偵測的即時
       痛感 vs 不可偵測的長期漂移，只有前者能被修。
    2. **兩種判不出來都可在一分鐘內補齊，補法寫在拒絕訊息裡。**
       ``card_repo_undeterminable`` 只發生在 DraftIssue（卡不在任何 repo 裡——但
       ``assign`` 本來就要把 Log 寫回卡面，正式流程要求真 Issue）；
       ``declared_repo_unparseable`` 發生在有人把目錄餵給 ``--worktree-source-repo``。
       ⚠️ 後者刻意**不**退化成「那就自己去讀那個目錄的 origin」——那正是本版拆掉的
       那條軸。給錯型別要響，不能靠猜補回來。
    3. **fail-closed 不會被無關的故障觸發。** 卡 repo 來自 ``ItemSnapshot.issue_url``，
       那是 ``assign`` 早已為了別的理由抓下來的同一份資料；GitHub 掛掉時 ``assign``
       在到達本守衛之前就已經失敗。守衛**不新增任何網路相依**，也不新增任何檔案系統
       相依——這是 fail-closed 站得住的前提，否則它會變成「別人的服務抖一下，全隊都
       不能派工」。

    **``declared_repo=None`` 的語意是「這筆登記宣告它屬於卡自己的 repo」**，不是
    「判不出來」。理由與它的代價寫在本檔頂端 warning 第 2 條：唯一合理的預設值就是
    卡自己的 repo，強迫每次手打一個工具已經知道的值不會多抓到任何東西，只會多一個
    儀式。**必須同時承認的是**：因此軸 A 擋得住的只有**明示的**跨 repo 宣告。

    刻意**沒有** ``--force``／``--allow-cross-repo`` 逃生口：漂移案例的成因不是
    有人想跨 repo，是沒人注意到自己跨了。給逃生口等於把「沒注意到」變成「按一下」。

    ⚠️ 本函式判的是**一筆登記**該不該寫下去。它不觀測、也擋不住磁碟上的建立動作
    （見本檔頂端 danger）。
    """
    basis: DeclarationBasis | None = None
    declared_slug: str | None = None
    if declared_repo is not None and str(declared_repo).strip():
        basis = "explicit"
        declared_slug = normalize_repo_slug(str(declared_repo))
        if declared_slug is None:
            return RepoOwnershipVerdict(
                reason_code="declared_repo_unparseable",
                card_repo=card_repo,
                worktree_repo=None,
                detail=(
                    f"宣告的來源 repo {str(declared_repo)!r} 不是 owner/repo slug（也不是"
                    "可解析的 GitHub remote／Issue URL）"
                ),
                basis=basis,
            )

    if card_repo is None:
        return RepoOwnershipVerdict(
            reason_code="card_repo_undeterminable",
            card_repo=None,
            worktree_repo=declared_slug,
            detail="卡沒有可解析的 Issue URL（DraftIssue 或 URL 形式不合），"
                   "而卡所屬 repo 只認 Issue URL 一個來源",
            basis=basis,
        )

    if declared_slug is None:
        # 沒有明示 ＝ 宣告「屬於卡自己的 repo」。見本函式 docstring 與頂端 warning 2。
        return RepoOwnershipVerdict(
            reason_code="match",
            card_repo=card_repo,
            worktree_repo=card_repo,
            detail=(
                f"這筆登記未明示來源 repo，依預設視為宣告它屬於卡自己的 {card_repo}"
                "（軸 A 在這一格必然相符——它擋得住的只有明示的跨 repo 宣告）"
            ),
            basis="card_repo_default",
        )

    if declared_slug != card_repo:
        return RepoOwnershipVerdict(
            reason_code="repo_mismatch",
            card_repo=card_repo,
            worktree_repo=declared_slug,
            detail=f"登記明示來源 repo 為 {declared_slug}，卡的 Issue URL 導出 {card_repo}",
            basis=basis,
        )

    return RepoOwnershipVerdict(
        reason_code="match",
        card_repo=card_repo,
        worktree_repo=declared_slug,
        detail=f"登記明示來源 repo 為 {declared_slug}，與卡的 repo 相符",
        basis=basis,
    )


def check_assign_repo_ownership(
    *,
    issue_url: str | None,
    worktree_source_repo: str | None = None,
) -> RepoOwnershipVerdict:
    """``assign`` 用的軸 A 端到端判定：卡的 Issue URL ＋ 登記宣告的 slug → 判定。

    ⚠️ **請注意這個簽章少了什麼**：沒有 ``worktree_path``、沒有 ``base_dir``、沒有
    ``git``。歸屬判定不需要知道 worktree 在磁碟哪裡，也**不准**知道——那正是
    ``docs/ROADMAP.md`` §1.5 的裁定。本機路徑仍然是 ``assign`` 的必填參數，但它流向
    的是軸 B 與看板欄位（供 ``cleanup``／``doctor`` 使用），不流進這裡。

    這是 ``commands/assign_cmd.py::run`` 實際呼叫的第一支閘門（接線後仍不成立的四件
    事見本檔頂端 warning，射程邊界見 danger）。
    """
    return check_worktree_repo_ownership(
        card_repo=card_repo_from_issue_url(issue_url),
        declared_repo=worktree_source_repo,
    )


# ---------------------------------------------------------------------------
# 軸 B：本機觀測（機器局部。只說「這台機器現在看到什麼」）
# ---------------------------------------------------------------------------

LocalObservationAction = Literal["pass", "warn", "refuse"]
LocalObservationCode = Literal[
    "consistent",
    "contradiction",
    "expected_repo_unknown",
    "nesting_conflict",
    "target_absent",
    "target_not_in_repo",
    "observed_repo_unidentifiable",
    "path_unanchored",
]

#: code → 動作的**全表**。只有一格 ``refuse``，而它要求的是**實際觀測到的矛盾**：
#: 登記的路徑此刻存在、而且它自己就是另一個 repo 的 worktree。
#:
#: ``nesting_conflict`` 刻意只 ``warn``：它的全部證據是「這條路徑座落在誰底下」，
#: 而 canonical §4.5 明文 worktree 路徑由實際建立者決定、未要求巢狀。上一版讓這種
#: 推測擋人，被需求方 2026-08-13 推翻——推測可以說「這裡看起來不對」，不可以當判定。
#: **降級的代價已量測**：見本檔頂端 warning 最後一段那筆具名的落差。
LOCAL_OBSERVATION_ACTIONS: dict[LocalObservationCode, LocalObservationAction] = {
    "consistent": "pass",
    "contradiction": "refuse",
    # 軸 A 沒給出歸屬（例如 DraftIssue）→ 沒有可比的基準，不是「一致」。
    "expected_repo_unknown": "pass",
    "nesting_conflict": "warn",
    "target_absent": "pass",
    "target_not_in_repo": "pass",
    "observed_repo_unidentifiable": "pass",
    "path_unanchored": "pass",
}


@dataclass(frozen=True)
class LocalWorktreeObservation:
    """軸 B 的觀測結果。**每一個欄位都是這台機器的快照，不是 repo 的事實。**"""

    code: LocalObservationCode
    #: 軸 A 認定的歸屬（拿來比對用），觀測本身不決定它。
    expected_repo: str | None
    #: 路徑此刻**實際**所屬的 repo（``commondir`` 的 origin）；看不到時 None。
    observed_repo: str | None = None
    #: 路徑**座落**在哪個 repo 的工作樹底下。與 ``observed_repo`` 不同：submodule 的
    #: worktree 掛在父 repo 路徑底下正是 §8.3 漂移得以隱形的形狀。**純資訊。**
    nested_repo: str | None = None
    resolved_target: str | None = None
    probed_dir: str | None = None
    common_dir: str | None = None
    remote_url: str | None = None
    detail: str = ""
    #: 這個結果只在這台機器上成立。留成欄位而不是註解，是為了讓消費端沒有藉口
    #: 把它當成 repo 的事實——它會一路寫進枚舉器產物與 Log。
    machine_local: bool = True

    @property
    def action(self) -> LocalObservationAction:
        return LOCAL_OBSERVATION_ACTIONS[self.code]

    @property
    def refuses(self) -> bool:
        return self.action == "refuse"

    def message(self) -> str:
        if self.code == "contradiction":
            return (
                f"這筆登記的路徑在**這台機器**上是 {self.observed_repo} 的 worktree，"
                f"與這張卡的 {self.expected_repo} 矛盾——拒絕寫入自相矛盾的登記；"
                f"{self.detail}。"
                "⚠️ 這是**機器局部**的觀測，不是歸屬判定：換一台機器沒有這個目錄時本檢查"
                "不會響，而**它的沉默不是判定**。歸屬判定（軸 A）與這台機器無關。"
                "合法路徑（#16 §7.1）：工作落在哪個 repo，卡就開在哪個 repo；"
                "跨 repo 需求請在目標 repo 另開實作卡，兩張卡以 spec 基線的 Issue URL 互相連結。"
            )
        if self.code == "nesting_conflict":
            return (
                f"提醒（不擋）：登記的路徑座落在 {self.nested_repo} 的目錄樹底下，"
                f"而這張卡屬於 {self.expected_repo}；{self.detail}。"
                "⚠️ 路徑座落在哪裡**不是**歸屬證據（canonical §4.5：路徑由實際建立者決定），"
                "所以這只是提醒，沒有執行者。"
            )
        return self.detail


def observe_local_worktree(
    worktree_path: str | Path,
    *,
    expected_repo: str | None,
    base_dir: str | Path | None = None,
    git: GitProbe = run_git_readonly,
) -> LocalWorktreeObservation:
    """看一眼這條登記路徑在**這台機器**上是什麼，與 ``expected_repo`` 比對。

    它**不導出歸屬**，只回答「此刻在這裡看到什麼」。三種說得出話的情形：

    - 目標存在且本身是某 repo 的 worktree → ``consistent`` 或 ``contradiction``。
      這是唯一有 ``refuse`` 資格的一格，因為它是**觀測**不是推測。
    - 目標尚未建立、最近存在的祖先屬於別的 repo → ``nesting_conflict``（只 ``warn``）。
    - 其餘（路徑未錨定、祖先也導不出 repo、origin 不是 GitHub 形狀）→ 沉默。

    **不讀 ``Path.cwd()``**（R1-02 的機械封堵保留）：``.claude/worktrees/x`` 在兩個
    repo 底下是完全相同的字串，用 cwd 補等於讓觀測隨「在哪執行」而變。相對路徑沒有
    ``base_dir`` 時直接回 ``path_unanchored``——**而那在本版不再擋人**：路徑既然不是
    歸屬證據，它未錨定就只是這台機器少一則資訊。
    """
    target = Path(worktree_path).expanduser()
    if target.is_absolute():
        resolved: Path | None = target
    elif base_dir is not None:
        # 只做接合、不做 resolve()：產物要留住登記的原樣，resolve 會改寫 symlink
        # （macOS 的 /tmp → /private/tmp）而讓對帳的人對不上自己登記的字串。
        resolved = Path(base_dir).expanduser() / target
    else:
        return LocalWorktreeObservation(
            code="path_unanchored",
            expected_repo=expected_repo,
            detail=(
                f"worktree 路徑 {worktree_path!r} 是相對路徑且未綁定 base_dir，"
                "這台機器解析不到它；相對路徑不帶所屬 repo 資訊，但那不影響歸屬判定"
                "（歸屬由登記宣告的 slug 決定）"
            ),
        )

    resolved_str = str(resolved)

    if resolved.is_dir():
        slug, common_dir, remote_url, detail = _slug_of_dir(resolved, git)
        if slug is None:
            return LocalWorktreeObservation(
                code=("target_not_in_repo" if common_dir is None
                      else "observed_repo_unidentifiable"),
                expected_repo=expected_repo, resolved_target=resolved_str,
                probed_dir=resolved_str, common_dir=common_dir, remote_url=remote_url,
                detail=detail,
            )
        nested = _nested_repo_slug(resolved, git)
        if expected_repo is None:
            code: LocalObservationCode = "expected_repo_unknown"
        else:
            code = "consistent" if slug == expected_repo else "contradiction"
        return LocalWorktreeObservation(
            code=code,
            expected_repo=expected_repo, observed_repo=slug, nested_repo=nested,
            resolved_target=resolved_str, probed_dir=resolved_str,
            common_dir=common_dir, remote_url=remote_url, detail=detail,
        )

    anchor = _nearest_existing_dir(resolved)
    if anchor is None:
        return LocalWorktreeObservation(
            code="target_absent", expected_repo=expected_repo,
            resolved_target=resolved_str,
            detail=f"路徑 {resolved} 與其所有祖先在這台機器上皆不存在",
        )
    nested, common_dir, remote_url, detail = _slug_of_dir(anchor, git)
    if nested is not None and expected_repo is not None and nested != expected_repo:
        return LocalWorktreeObservation(
            code="nesting_conflict", expected_repo=expected_repo, nested_repo=nested,
            resolved_target=resolved_str, probed_dir=str(anchor),
            common_dir=common_dir, remote_url=remote_url,
            detail=f"目標 {resolved} 尚未建立；最近存在的祖先 {anchor}：{detail}",
        )
    return LocalWorktreeObservation(
        code="target_absent", expected_repo=expected_repo, nested_repo=nested,
        resolved_target=resolved_str, probed_dir=str(anchor),
        common_dir=common_dir, remote_url=remote_url,
        detail=f"目標 {resolved} 尚未建立；最近存在的祖先 {anchor}：{detail}",
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
    """一筆 (卡, worktree) 配對的結果。欄位即產物欄位。

    ⚠️ **``ownership_*`` 與 ``local_*`` 是兩件不同的事，不要合著讀**：前者換機器不變，
    後者是這台機器的快照。``local_machine_local`` 恆為 true，留在產物裡是為了讓任何
    下游消費者都得先看到這一欄才讀得到 ``local_code``。
    """

    card_id: str | None
    issue_url: str | None
    branch: str | None
    worktree_raw: str | None
    # --- 軸 A：可攜 ---
    card_repo: str | None
    declared_repo: str | None
    worktree_repo: str | None
    declaration_basis: str | None
    ownership_reason: str
    ownership_decision: str
    ownership_detail: str
    # --- 軸 B：機器局部 ---
    resolved_target: str | None
    target_exists: bool
    observed_repo: str | None
    nested_repo: str | None
    local_code: str
    local_action: str
    local_machine_local: bool
    local_detail: str

    def as_dict(self) -> dict[str, object]:
        return {
            "card_id": self.card_id,
            "issue_url": self.issue_url,
            "branch": self.branch,
            "worktree_raw": self.worktree_raw,
            "card_repo": self.card_repo,
            "declared_repo": self.declared_repo,
            "worktree_repo": self.worktree_repo,
            "declaration_basis": self.declaration_basis,
            "ownership_reason": self.ownership_reason,
            "ownership_decision": self.ownership_decision,
            "ownership_detail": self.ownership_detail,
            "resolved_target": self.resolved_target,
            "target_exists": self.target_exists,
            "observed_repo": self.observed_repo,
            "nested_repo": self.nested_repo,
            "local_code": self.local_code,
            "local_action": self.local_action,
            "local_machine_local": self.local_machine_local,
            "local_detail": self.local_detail,
        }


TSV_COLUMNS = [
    "card_id", "card_repo", "declared_repo", "worktree_repo", "declaration_basis",
    "ownership_reason", "ownership_decision",
    "worktree_raw", "resolved_target", "target_exists", "observed_repo", "nested_repo",
    "local_code", "local_action", "local_machine_local", "issue_url",
]


def enumerate_ownership(
    rows: list[OwnershipInputRow],
    *,
    base_dir: str | Path | None = None,
    git: GitProbe = run_git_readonly,
) -> list[OwnershipRow]:
    """對每一筆輸入跑同一組判定函式（**不是**另一套邏輯）。

    輸入列可給 ``worktree_path``，或給 Ledger 慣例的複合字串 ``branch_worktree``
    （``branch @ path``）；``worktree_source_repo`` 可選，給了就是這筆登記明示的
    repo slug。沒有 worktree 註冊的列不在此函式的職責內——呼叫端先濾。

    ⚠️ **現況的 Project 欄位裡沒有 slug**（``分支worktree`` 只存 ``branch @ path``），
    所以現拉出來的每一列 ``declared_repo`` 都是 None，軸 A 一律走
    ``card_repo_default``。**那使得軸 A 在既有資料上近乎恆真**——這正是為什麼本枚舉器
    的價值改由軸 B 承擔，也正是為什麼軸 B 的每一欄都標著「機器局部」。
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
        declared = raw.get("worktree_source_repo")
        verdict = check_worktree_repo_ownership(
            card_repo=card_repo_from_issue_url(issue_url), declared_repo=declared
        )
        observation = observe_local_worktree(
            worktree or "", expected_repo=verdict.worktree_repo, base_dir=base_dir, git=git
        )
        out.append(
            OwnershipRow(
                card_id=raw.get("card_id"),
                issue_url=issue_url,
                branch=branch,
                worktree_raw=worktree,
                card_repo=verdict.card_repo,
                declared_repo=declared,
                worktree_repo=verdict.worktree_repo,
                declaration_basis=verdict.basis,
                ownership_reason=verdict.reason_code,
                ownership_decision=verdict.decision,
                ownership_detail=verdict.detail,
                resolved_target=observation.resolved_target,
                target_exists=bool(
                    observation.resolved_target and Path(observation.resolved_target).is_dir()
                ),
                observed_repo=observation.observed_repo,
                nested_repo=observation.nested_repo,
                local_code=observation.code,
                local_action=observation.action,
                local_machine_local=observation.machine_local,
                local_detail=observation.detail,
            )
        )
    return out


def summarize_ownership(rows: list[OwnershipRow]) -> dict[str, object]:
    """摘要與逐列產物**同一次執行**產生（§6.2：宣稱的數字與 artifact 同源）。

    ``allow``／``block`` 只數軸 A（可攜）；軸 B 的數字全部關在 ``local`` 底下，
    並帶一句 ``note`` ——摘要被貼進報告時最容易掉的就是那句限定詞。
    """
    by_reason: dict[str, int] = {}
    by_local: dict[str, int] = {}
    by_basis: dict[str, int] = {}
    for r in rows:
        by_reason[r.ownership_reason] = by_reason.get(r.ownership_reason, 0) + 1
        by_local[r.local_code] = by_local.get(r.local_code, 0) + 1
        key = r.declaration_basis or "none"
        by_basis[key] = by_basis.get(key, 0) + 1
    return {
        "total": len(rows),
        "allow": sum(1 for r in rows if r.ownership_decision == "allow"),
        "block": sum(1 for r in rows if r.ownership_decision == "block"),
        "by_reason_code": dict(sorted(by_reason.items())),
        "by_declaration_basis": dict(sorted(by_basis.items())),
        "local": {
            "note": "以下全部是「這台機器現在看到什麼」，不是 repo 的事實；換一台機器不會重現",
            "target_exists": sum(1 for r in rows if r.target_exists),
            "refuse": sum(1 for r in rows if r.local_action == "refuse"),
            "warn": sum(1 for r in rows if r.local_action == "warn"),
            "by_code": dict(sorted(by_local.items())),
        },
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
        description=(
            "唯讀枚舉：對現況每一筆 (卡, worktree) 配對跑軸 A（可攜的歸屬判定）"
            "與軸 B（這台機器的觀測）。⚠️ local_* 欄不是 repo 的事實"
        ),
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
        help="相對 worktree 路徑的錨點，**只影響軸 B（本機觀測）**。**不給就是不給**"
             "——本工具不會拿 cwd 當預設，沒有錨點的相對路徑一律 local_code="
             "path_unanchored，也就是這台機器沒有資訊；歸屬判定不受影響。",
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
    "LOCAL_OBSERVATION_ACTIONS",
    "OWNERSHIP_DECISIONS",
    "TSV_COLUMNS",
    "DeclarationBasis",
    "GitProbe",
    "LocalObservationAction",
    "LocalObservationCode",
    "LocalWorktreeObservation",
    "OwnershipDecision",
    "OwnershipInputRow",
    "OwnershipReason",
    "OwnershipRow",
    "RegisteredCard",
    "RepoOwnershipVerdict",
    "TasksMdRegistry",
    "card_repo_from_issue_url",
    "check_assign_repo_ownership",
    "check_worktree_repo_ownership",
    "enumerate_ownership",
    "fetch_project_ownership_rows",
    "load_tasks_md_registry",
    "main",
    "normalize_repo_slug",
    "observe_local_worktree",
    "parse_active_ledger",
    "parse_archived_card_ids",
    "parse_markdown_tables",
    "run_git_readonly",
    "summarize_ownership",
]


if __name__ == "__main__":  # pragma: no cover - 入口薄殼，行為全在 main()
    raise SystemExit(main())
