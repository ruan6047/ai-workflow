from __future__ import annotations

import pytest

from wf_cli.gh import GhRunner
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

from .ensure_fields_oracle import field_diff, oracle_reentrant
from .fake_gh import FakeGhRunner


def test_ensure_fields_creates_all_frozen_fields():
    runner = FakeGhRunner()
    fields = ensure_fields(runner, "acme", 1)
    # ⚠️ **超集合、⛔ 不是相等**：`ensure_fields` 回的是 `list_fields` 看到的全部欄位，
    # 而真 Project 恆帶內建欄（`Title`／`Assignees`／`Status`／`Labels`…，實測 Project #4
    # 有 13 個）。上一版寫相等只因替身**省略了內建欄** ⇒ 那個相等是替身造出來的假事實。
    # ⛔ 不得改回相等：改回去等於再次要求替身比真實平台窄。
    assert set(FIELD_SPECS) <= set(fields)
    for name in FIELD_SPECS:
        assert fields[name].type == FIELD_SPECS[name][0]


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


# --------------------------------------------------------------------------
# ensure_fields 的兩條路徑：回傳值正確性（V1／V2）與呼叫次數（V3）
#
# ⭐ 兩件事**必須併用**，單獨都不足：
#   - 只釘次數：無條件 `return existing`（M1）也是 1 次 ⇒ 次數綠、回傳錯。
#   - 只驗回傳：現況（無條件重查兩次）也永遠正確 ⇒ 修法靜默回退沒人知道。
# --------------------------------------------------------------------------


class _CallLog(FakeGhRunner):
    """記下每一次 gh 呼叫，供次數斷言用（形狀沿用 `_RecordingRunner` 的作法）。

    刻意做在測試檔內而非改 `tests/fake_gh.py`：後者是「gh 長什麼樣」的替身，
    記帳是測試自己的需求，混進去會讓每個用它的測試都付這筆成本。

    ⚠️ 排除差分預言自己發的查詢（`oracle_reentrant()`）：跑
    `-p tests.ensure_fields_oracle` 時它會在每次 `ensure_fields` 後多讀一次欄位，
    那是取證工具的呼叫、不是被測程式的行為，記進來會讓次數斷言假紅。
    """

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[list[str]] = []

    def execute(self, args, input=None):  # type: ignore[override]
        if not oracle_reentrant():
            self.calls.append(list(args))
        return super().execute(args, input)

    def graphql(self, query: str, **variables):  # type: ignore[override]
        if not oracle_reentrant():
            # 只記「這是哪一種查詢」，不記全文：斷言看的是次數與種類。
            kind = "fields" if "ProjectV2SingleSelectField" in query else "other"
            self.calls.append(["graphql", kind])
        return super().graphql(query, **variables)

    def counts(self) -> dict[str, int]:
        return {
            "field_read": sum(1 for c in self.calls if c == ["graphql", "fields"]),
            "gh_field_list": sum(1 for c in self.calls if c[:2] == ["project", "field-list"]),
            "field_create": sum(1 for c in self.calls if c[:2] == ["project", "field-create"]),
            "project_view": sum(1 for c in self.calls if c[:2] == ["project", "view"]),
        }


def test_ensure_fields_creation_path_return_matches_fresh_read():
    """**有建立**路徑：回傳必須與「呼叫結束後重新讀一次」逐位元相同（驗收 A2）。

    ⛔ **鍵集合相同不算通過**——`field_diff` 是順序敏感且逐欄位（id／type／每個
    option 的 id）比對的。研究輪實測：off-by-one 錯位與 option id 全填第一個這兩種
    變異，其鍵集合與型別都與正確版相同，`test_ensure_fields_creates_all_frozen_fields`
    對兩者全綠。

    ⭐ 這一條與下一條**成對**存在，缺一不可：M1／M2／M3 三種錯誤實作在**零建立**
    情境全部 PASS，只有這一條（有建立）會轉紅。
    """
    runner = FakeGhRunner()
    returned = ensure_fields(runner, "acme", 1)
    fresh = list_fields(runner, "acme", 1)
    assert field_diff(returned, fresh) == []
    assert set(FIELD_SPECS) <= set(returned), "前提沒成立：這一次應該真的建了欄位"


def test_ensure_fields_zero_creation_path_return_matches_fresh_read():
    """**零建立**路徑：回傳仍必須與重讀逐位元相同（驗收 A1／A2）。

    ⚠️ 這一條**構造上抓不到** M1／M2／M3——零建立時它們與正確實作行為相同。
    留著是因為它釘的是另一件事：C1 的條件分支回傳的是**第一次**查詢的結果，
    這條保證那份結果本身沒有被截斷或改寫。
    """
    runner = FakeGhRunner()
    ensure_fields(runner, "acme", 1)  # 第一次：把欄位建起來
    returned = ensure_fields(runner, "acme", 1)  # 第二次：零建立
    fresh = list_fields(runner, "acme", 1)
    assert field_diff(returned, fresh) == []


def test_ensure_fields_zero_creation_issues_exactly_one_field_read():
    """零建立時只讀一次欄位（V3）。現況是 2 次，第二次是純浪費的 102 點。

    ⛔ 本條**單獨不足以驗正確性**（M1 也是 1 次），必須與上面兩條差分比對併用。
    存在的理由：實查既有測試**沒有任何一個**釘住欄位查詢次數 ⇒ 沒有這條，
    修法退回無條件重查時整套仍全綠，沒有人會知道。
    """
    runner = _CallLog()
    ensure_fields(runner, "acme", 1)  # 建欄位
    runner.calls.clear()

    ensure_fields(runner, "acme", 1)  # 零建立
    counts = runner.counts()
    assert counts["field_create"] == 0, f"前提沒成立：這一次不該建任何欄位（{counts}）"
    assert counts["field_read"] == 1, f"零建立時欄位查詢應恰 1 次，實得 {counts}"
    # A7：整條路徑上不得再出現 `gh project field-list`（102 點的來源）。
    assert counts["gh_field_list"] == 0, f"不該再走 gh project field-list（{counts}）"


def test_ensure_fields_creation_path_reads_fields_twice():
    """有建立時**必須**讀第二次——否則新欄位的 id／option id 無從取得。

    這是上一條的反面負控：沒有它，「永遠只讀一次」也會讓上一條全綠。
    """
    runner = _CallLog()
    ensure_fields(runner, "acme", 1)
    counts = runner.counts()
    assert counts["field_create"] == len(FIELD_SPECS), f"前提沒成立（{counts}）"
    assert counts["field_read"] == 2, f"有建立時欄位查詢應為 2 次，實得 {counts}"


def test_list_fields_with_project_id_skips_the_project_lookup():
    """帶 `project_id` 時不再 `gh project view`；省略時才內部 resolve（A7 向後相容）。"""
    runner = _CallLog()
    project = resolve_project(runner, "acme", 1)
    ensure_fields(runner, "acme", 1)
    runner.calls.clear()

    with_id = list_fields(runner, "acme", 1, project_id=project.id)
    assert runner.counts()["project_view"] == 0
    runner.calls.clear()

    without_id = list_fields(runner, "acme", 1)
    assert runner.counts()["project_view"] == 1
    assert field_diff(with_id, without_id) == []


def test_ensure_fields_preserves_non_frozen_fields_on_both_paths():
    """非 `FIELD_SPECS` 的既有欄位（GitHub 內建 Status）在兩條路徑都原樣回來（A3）。"""
    runner = FakeGhRunner()
    runner.add_builtin_status("acme", 1, ["Todo", "In Progress", "Done"])

    created_path = ensure_fields(runner, "acme", 1)  # 這一次會建 FIELD_SPECS
    zero_path = ensure_fields(runner, "acme", 1)  # 這一次零建立

    for label, fields in (("有建立", created_path), ("零建立", zero_path)):
        status = fields.get("Status")
        assert status is not None, f"{label} 路徑掉了內建 Status"
        assert status.type == "SINGLE_SELECT", f"{label} 路徑把內建 single select 判成 {status.type}"
        assert set(status.options) == {"Todo", "In Progress", "Done"}
    assert field_diff(created_path, zero_path) == []


class _PagedFieldsRunner(GhRunner):
    """只回欄位定義的兩頁 stub，用來驗 `list_fields` 的分頁迴圈（V6）。

    ⚠️ **刻意不用 `FakeGhRunner`**：那支永遠回單頁。而真實 API 上也造不出這個情境
    ——單頁上限 100 欄，本 repo 的 Project #4 只有 29 欄 ⇒ 分頁只能在這裡驗，
    ⛔ 不得宣稱「分頁已在真實 API 上驗過」。
    """

    def __init__(self, pages) -> None:
        self.pages = pages
        self.seen_cursors: list[str | None] = []

    def run_json(self, args):  # type: ignore[override]
        assert list(args)[:2] == ["project", "view"], f"非預期的呼叫 {args}"
        return {"id": "PVT_paged", "owner": {"login": "acme"}, "number": 1, "url": "u"}

    def graphql(self, query: str, **variables):  # type: ignore[override]
        self.seen_cursors.append(variables.get("after"))
        nodes, has_next, end_cursor = self.pages[len(self.seen_cursors) - 1]
        return {
            "data": {
                "node": {
                    "fields": {
                        "pageInfo": {"hasNextPage": has_next, "endCursor": end_cursor},
                        "nodes": nodes,
                    }
                }
            }
        }


def test_list_fields_follows_field_pagination():
    page1 = (
        [
            {"__typename": "ProjectV2Field", "id": "F1", "name": "卡ID"},
            {"__typename": "ProjectV2Field", "id": "F2", "name": "owner"},
        ],
        True,
        "CURSOR_1",
    )
    page2 = (
        [
            {
                "__typename": "ProjectV2SingleSelectField",
                "id": "F3",
                "name": "級別",
                "options": [{"id": "O1", "name": "T0"}, {"id": "O2", "name": "T1"}],
            }
        ],
        False,
        None,
    )
    runner = _PagedFieldsRunner([page1, page2])
    fields = list_fields(runner, "acme", 1)

    assert list(fields) == ["卡ID", "owner", "級別"], "第二頁掉了，或順序沒有照 API 回的來"
    assert fields["級別"].options == {"T0": "O1", "T1": "O2"}
    # 第一次不得帶 after（空字串會被 gh 送成 `after: ""` 而不是 null）；第二次要帶 cursor。
    assert runner.seen_cursors == [None, "CURSOR_1"]


def test_list_fields_stops_at_a_single_page():
    """負控：`hasNextPage` 為假時只查一次——否則上一條也會綠（分頁迴圈永遠多跑一輪）。"""
    page = ([{"__typename": "ProjectV2Field", "id": "F1", "name": "卡ID"}], False, None)
    runner = _PagedFieldsRunner([page])
    fields = list_fields(runner, "acme", 1)
    assert list(fields) == ["卡ID"]
    assert runner.seen_cursors == [None]
