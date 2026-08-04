from __future__ import annotations

import pytest

from wf_cli.resources import (
    ResourceDeclaration,
    ResourceDeclarationError,
    find_conflicts,
    parse_block,
    render_block,
    try_parse_block,
)


def test_valid_declaration_round_trips_through_render_and_parse():
    decl = ResourceDeclaration(db_scope="write", resources=["file:a.py", "port:8080"])
    body = f"intro text\n\n{render_block(decl)}\n\nmore text"
    parsed = parse_block(body)
    assert parsed.db_scope == "write"
    assert parsed.resources == ["file:a.py", "port:8080"]


def test_invalid_db_scope_rejected():
    with pytest.raises(ResourceDeclarationError):
        ResourceDeclaration(db_scope="bogus", resources=[])


@pytest.mark.parametrize(
    "bad_resource",
    ["nofile.py", "port:notanumber", "db:dev:badkind", "container:", "random:thing"],
)
def test_invalid_resource_strings_rejected(bad_resource):
    with pytest.raises(ResourceDeclarationError):
        ResourceDeclaration(db_scope="none", resources=[bad_resource])


@pytest.mark.parametrize(
    "good_resource",
    ["file:cli/src/wf_cli/card.py", "port:8080", "container:api", "db:dev:schema", "db:dev:table:players"],
)
def test_valid_resource_prefixes_accepted(good_resource):
    decl = ResourceDeclaration(db_scope="write", resources=[good_resource])
    assert decl.resources == [good_resource]


def test_parse_block_missing_raises():
    with pytest.raises(ResourceDeclarationError):
        parse_block("no resource section here at all")


def test_parse_block_malformed_json_raises():
    body = "## 資源宣告\n<!-- resource-claims:begin -->\n```json\n{not valid json\n```\n<!-- resource-claims:end -->"
    with pytest.raises(ResourceDeclarationError):
        parse_block(body)


def test_try_parse_block_returns_none_instead_of_raising():
    assert try_parse_block("nothing here") is None
    decl = ResourceDeclaration(db_scope="none", resources=[])
    assert try_parse_block(render_block(decl)) is not None


def test_find_conflicts_detects_shared_file_resource():
    mine = ResourceDeclaration(db_scope="write", resources=["file:shared.py"])
    other = ResourceDeclaration(db_scope="write", resources=["file:shared.py", "file:other.py"])
    assert find_conflicts(mine, "OTHER-CARD", other) == ["file:shared.py"]


def test_find_conflicts_no_overlap_is_empty():
    mine = ResourceDeclaration(db_scope="write", resources=["file:a.py"])
    other = ResourceDeclaration(db_scope="write", resources=["file:b.py"])
    assert find_conflicts(mine, "OTHER-CARD", other) == []


def test_find_conflicts_db_resource_shared_when_both_read_only():
    mine = ResourceDeclaration(db_scope="read", resources=["db:dev:table:players"])
    other = ResourceDeclaration(db_scope="read", resources=["db:dev:table:players"])
    assert find_conflicts(mine, "OTHER-CARD", other) == []


def test_find_conflicts_db_resource_still_conflicts_if_either_side_writes():
    mine = ResourceDeclaration(db_scope="write", resources=["db:dev:table:players"])
    other = ResourceDeclaration(db_scope="read", resources=["db:dev:table:players"])
    assert find_conflicts(mine, "OTHER-CARD", other) == ["db:dev:table:players"]


def test_find_conflicts_file_resource_always_conflicts_even_if_both_read_scope():
    # file/port/container 是獨佔宣告本身，不受 db_scope=read 影響。
    mine = ResourceDeclaration(db_scope="read", resources=["file:shared.py"])
    other = ResourceDeclaration(db_scope="read", resources=["file:shared.py"])
    assert find_conflicts(mine, "OTHER-CARD", other) == ["file:shared.py"]


def test_summary_lists_resources_or_notes_empty():
    empty = ResourceDeclaration(db_scope="none", resources=[])
    assert "無共享可寫資源" in empty.summary()
    non_empty = ResourceDeclaration(db_scope="write", resources=["file:a.py"])
    assert "file:a.py" in non_empty.summary()
