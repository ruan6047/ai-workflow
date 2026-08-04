from __future__ import annotations

import pytest

from wf_cli.card import (
    Card,
    append_log_line,
    format_branch_worktree,
    now_iso8601,
    parse_branch_worktree,
    render_issue_body,
    render_spec_markdown,
)
from wf_cli.resources import ResourceDeclaration


def _make_card(**overrides):
    defaults = {
        "card_id": "DEMO-CARD1",
        "feature": "示範卡",
        "tier": "T3",
        "db_scope": "write",
        "core_pain": "機械寫入無單一通道",
        "service_goal": "消除人肉紀律缺口",
        "resources": ResourceDeclaration(db_scope="write", resources=["file:demo.py"]),
    }
    defaults.update(overrides)
    return Card(**defaults)


def test_card_rejects_invalid_tier():
    with pytest.raises(ValueError):
        _make_card(tier="T9")


def test_card_rejects_db_scope_mismatch_with_resource_declaration():
    with pytest.raises(ValueError):
        _make_card(db_scope="none")  # resources 宣告是 write，與 db_scope 不一致


def test_branch_worktree_formatting_round_trips():
    s = format_branch_worktree("ai/agent/DEMO-CARD1", ".claude/worktrees/demo-execution")
    assert s == "ai/agent/DEMO-CARD1 @ .claude/worktrees/demo-execution"
    branch, path = parse_branch_worktree(s)
    assert branch == "ai/agent/DEMO-CARD1"
    assert path == ".claude/worktrees/demo-execution"


def test_branch_worktree_placeholder_parses_to_none():
    assert parse_branch_worktree("—") == (None, None)
    assert parse_branch_worktree("") == (None, None)


def test_format_branch_worktree_with_no_values():
    assert format_branch_worktree(None, None) == "—"


def test_render_spec_markdown_contains_required_sections():
    card = _make_card()
    text = render_spec_markdown(card)
    assert "# DEMO-CARD1 示範卡" in text
    assert "## 核心痛點" in text
    assert "機械寫入無單一通道" in text
    assert "## 驗收條件" in text
    assert "## 驗證" in text
    # 新架構下，可變 Ledger 欄位不重複寫進 git spec 檔。
    assert "owner" in text and "GitHub Issue" in text


def test_render_issue_body_embeds_resource_block_and_log():
    card = _make_card()
    body = render_issue_body(card)
    assert "## 資源宣告" in body
    assert "<!-- resource-claims:begin -->" in body
    assert "file:demo.py" in body
    assert "## Log" in body
    assert "open by" in body


def test_append_log_line_creates_section_if_missing():
    body = "some content without a log section"
    updated = append_log_line(body, "test entry")
    assert "## Log" in updated
    assert "- test entry" in updated


def test_append_log_line_appends_to_existing_section():
    body = "content\n\n## Log\n\n- first entry\n"
    updated = append_log_line(body, "second entry")
    assert updated.count("## Log") == 1
    assert "- first entry" in updated
    assert "- second entry" in updated
    # 附加順序：新的一行在原本內容之後（append-only，不覆寫歷史）。
    assert updated.index("first entry") < updated.index("second entry")


def test_now_iso8601_has_timezone_offset():
    ts = now_iso8601()
    assert "T" in ts
    assert ts[-3] == ":" or ts.endswith("Z")  # +08:00 形式
