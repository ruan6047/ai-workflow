from __future__ import annotations

from pathlib import Path

from wf_cli.registry import (
    load_tasks_md_registry,
    parse_active_ledger,
    parse_archived_card_ids,
    parse_markdown_tables,
)

ACTIVE_LEDGER = """# 任務看板

## Ledger 總表（活卡）

| 卡ID | Initiative | 級別 | 功能 | owner | 分支／worktree | iteration | 交付狀態 | 部署狀態 | 最後交接 |
|---|---|---|---|---|---|---|---|---|---|
| [CARD-A](tasks/CARD-A.md) | None | T2 | 示範卡 A | someone | `ai/agent/CARD-A @ .claude/worktrees/card-a` | 0 | 🚧進行中 | —不適用 | 2026-08-01T00:00:00+08:00 |
| [CARD-B](tasks/CARD-B.md) | INIT-X | T3 | 示範卡 B | 待指派 | — | 0 | 📥Backlog | —不適用 | 2026-07-01T00:00:00+08:00 |

## 依賴註記

- 一些不相干的文字，不是表格。
"""

ARCHIVE_LEDGER = """# 封存

| 卡ID | 功能 | 交付狀態 | 部署狀態 | 封存位置 |
|---|---|---|---|---|
| CARD-OLD1 | 舊卡 | 🏁完成 | —不適用 | [tasks/CARD-OLD1.md](tasks/CARD-OLD1.md) |
"""


def test_parse_markdown_tables_finds_both_tables_and_ignores_prose():
    tables = parse_markdown_tables(ACTIVE_LEDGER)
    assert len(tables) == 1
    header, rows = tables[0]
    assert header[0] == "卡ID"
    assert len(rows) == 2


def test_parse_active_ledger_extracts_card_id_branch_and_worktree():
    cards = parse_active_ledger(ACTIVE_LEDGER)
    by_id = {c.card_id: c for c in cards}
    assert by_id["CARD-A"].branch == "ai/agent/CARD-A"
    assert by_id["CARD-A"].worktree_path == ".claude/worktrees/card-a"
    assert by_id["CARD-A"].delivery_status == "🚧進行中"
    assert by_id["CARD-A"].last_handoff == "2026-08-01T00:00:00+08:00"
    assert by_id["CARD-A"].owner_assigned() is True


def test_parse_active_ledger_handles_placeholder_branch_and_owner():
    cards = parse_active_ledger(ACTIVE_LEDGER)
    by_id = {c.card_id: c for c in cards}
    assert by_id["CARD-B"].branch is None
    assert by_id["CARD-B"].worktree_path is None
    assert by_id["CARD-B"].owner_assigned() is False


def test_parse_archived_card_ids_extracts_plain_text_ids():
    ids = parse_archived_card_ids(ARCHIVE_LEDGER)
    assert ids == {"CARD-OLD1"}


def test_load_tasks_md_registry_reads_docs_subdir(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "TASKS.md").write_text(ACTIVE_LEDGER, encoding="utf-8")
    archive_dir = docs / "archive"
    archive_dir.mkdir()
    (archive_dir / "TASKS_ARCHIVE.md").write_text(ARCHIVE_LEDGER, encoding="utf-8")

    registry = load_tasks_md_registry(tmp_path)
    assert {c.card_id for c in registry.active} == {"CARD-A", "CARD-B"}
    assert registry.archived_card_ids == {"CARD-OLD1"}
    assert len(registry.source_paths) == 2


def test_load_tasks_md_registry_falls_back_to_root_tasks_md(tmp_path: Path):
    (tmp_path / "TASKS.md").write_text(ACTIVE_LEDGER, encoding="utf-8")
    registry = load_tasks_md_registry(tmp_path)
    assert {c.card_id for c in registry.active} == {"CARD-A", "CARD-B"}


def test_load_tasks_md_registry_empty_when_no_files(tmp_path: Path):
    registry = load_tasks_md_registry(tmp_path)
    assert registry.active == []
    assert registry.archived_card_ids == set()
    assert registry.source_paths == []
