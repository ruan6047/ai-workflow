"""卡註冊來源（可插拔）：doctor 用來判斷「這個 worktree 對得上哪張卡」。

遷移尚未 cutover 的專案（如 cpbl-analytics）目前仍以 ``docs/TASKS.md`` 的 Ledger
表格作為 current-state 事實來源；已 cutover 的專案改用 GitHub Project（見
``project.py``）。doctor／snapshot 的骨架刻意不綁定其中一種（卡面〈依賴與順序〉：
「doctor／snapshot 骨架不依賴 Issues 結構，可立即先行」），所以這裡定義一個共同的
最小介面 ``RegisteredCard``，兩種來源各自轉成這個形狀。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

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


__all__ = [
    "RegisteredCard",
    "TasksMdRegistry",
    "load_tasks_md_registry",
    "parse_active_ledger",
    "parse_archived_card_ids",
    "parse_markdown_tables",
]
