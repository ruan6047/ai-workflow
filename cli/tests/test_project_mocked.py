from __future__ import annotations

import pytest

from wf_cli.project import (
    FIELD_SPECS,
    ProjectError,
    add_item_to_project,
    create_draft_item,
    create_repo_issue,
    ensure_fields,
    find_item_by_card_id,
    list_fields,
    list_items,
    resolve_project,
    set_field_value,
    set_item_body,
)

from .fake_gh import FakeGhRunner


def test_ensure_fields_creates_all_frozen_fields():
    runner = FakeGhRunner()
    fields = ensure_fields(runner, "acme", 1)
    assert set(fields) == set(FIELD_SPECS)
    for name, meta in fields.items():
        expected_type = FIELD_SPECS[name][0]
        assert meta.type == expected_type


def test_ensure_fields_is_idempotent():
    runner = FakeGhRunner()
    first = ensure_fields(runner, "acme", 1)
    second = ensure_fields(runner, "acme", 1)
    for name in FIELD_SPECS:
        assert first[name].id == second[name].id  # 沒有重複建立、id 不變


def test_single_select_field_has_expected_options():
    runner = FakeGhRunner()
    fields = ensure_fields(runner, "acme", 1)
    tier_options = set(fields["級別"].options)
    assert tier_options == {"T0", "T1", "T2", "T3", "T4"}


def test_set_field_value_text_number_and_single_select():
    runner = FakeGhRunner()
    fields = ensure_fields(runner, "acme", 1)
    project = resolve_project(runner, "acme", 1)
    item_id = create_draft_item(runner, "acme", 1, "title", "body")

    set_field_value(runner, project, item_id, fields["卡ID"], "DEMO1")
    set_field_value(runner, project, item_id, fields["iteration"], 2)
    set_field_value(runner, project, item_id, fields["級別"], "T3")

    items = list_items(runner, project)
    item = items[0]
    assert item.fields["卡ID"] == "DEMO1"
    assert item.fields["iteration"] == 2.0
    assert item.fields["級別"] == "T3"


def test_set_field_value_rejects_unknown_single_select_option():
    runner = FakeGhRunner()
    fields = ensure_fields(runner, "acme", 1)
    project = resolve_project(runner, "acme", 1)
    item_id = create_draft_item(runner, "acme", 1, "title", "body")
    with pytest.raises(ProjectError):
        set_field_value(runner, project, item_id, fields["級別"], "NOT_A_TIER")


def test_create_repo_issue_and_add_to_project_round_trips():
    runner = FakeGhRunner()
    project = resolve_project(runner, "acme", 1)
    number, url = create_repo_issue(runner, "acme/demo-repo", "hello", "world")
    assert number == 1
    assert url == "https://github.com/acme/demo-repo/issues/1"
    item_id = add_item_to_project(runner, "acme", 1, url)
    items = list_items(runner, project)
    assert items[0].item_id == item_id
    assert items[0].content_type == "Issue"
    assert items[0].issue_number == 1
    assert items[0].body == "world"


def test_set_item_body_updates_draft_item_via_content_id():
    runner = FakeGhRunner()
    project = resolve_project(runner, "acme", 1)
    create_draft_item(runner, "acme", 1, "title", "old body")
    item = list_items(runner, project)[0]
    assert item.content_id is not None
    assert item.content_id != item.item_id  # DI_ 前綴的內容 ID 與 PVTI_ 前綴的 item ID 不同

    set_item_body(runner, item.content_type, item.content_id, project, None, None, "new body")
    items = list_items(runner, project)
    assert items[0].body == "new body"


def test_set_item_body_rejects_project_item_id_for_draft_issue():
    """踩雷回歸鎖：`gh project item-edit --body` 對 draft issue 只認 DI_ 內容 ID，
    用 PVTI_ 的 ProjectV2Item ID 呼叫會被 gh 拒絕（實跑對 throwaway test Project
    才發現，見 project.set_item_body 說明）；這裡確保用錯 ID 會直接報錯，不會
    默默寫到別的地方或被忽略。
    """
    runner = FakeGhRunner()
    project = resolve_project(runner, "acme", 1)
    item_id = create_draft_item(runner, "acme", 1, "title", "old body")
    with pytest.raises(AssertionError):
        set_item_body(runner, "DraftIssue", item_id, project, None, None, "new body")


def test_set_item_body_updates_real_issue_via_issue_edit():
    runner = FakeGhRunner()
    project = resolve_project(runner, "acme", 1)
    number, url = create_repo_issue(runner, "acme/demo-repo", "hello", "old body")
    item_id = add_item_to_project(runner, "acme", 1, url)
    set_item_body(runner, "Issue", item_id, project, "acme/demo-repo", number, "new body")
    items = list_items(runner, project)
    assert items[0].body == "new body"


def test_find_item_by_card_id():
    runner = FakeGhRunner()
    fields = ensure_fields(runner, "acme", 1)
    project = resolve_project(runner, "acme", 1)
    item_id = create_draft_item(runner, "acme", 1, "title", "body")
    set_field_value(runner, project, item_id, fields["卡ID"], "FIND-ME1")
    items = list_items(runner, project)
    found = find_item_by_card_id(items, "FIND-ME1")
    assert found is not None
    assert found.item_id == item_id
    assert find_item_by_card_id(items, "NOPE") is None


def test_list_fields_defaults_unknown_field_to_text():
    runner = FakeGhRunner()
    # 模擬 project 已存在一個非凍結 schema 的自訂欄位（例如使用者手動加的）。
    runner._ensure_project("acme", 1)
    runner.execute(
        ["project", "field-create", "1", "--owner", "acme", "--name", "隨手加的欄位",
         "--data-type", "TEXT", "--format", "json"]
    )
    fields = list_fields(runner, "acme", 1)
    assert fields["隨手加的欄位"].type == "TEXT"
