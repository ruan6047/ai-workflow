"""釘住 `assign` 交集檢查的三項行為（`WF-REDESIGN-W3` 驗收 4）。

卡面把這一條拆成 (a)(b)(c) 三項，本檔逐項對應，並多釘一句卡面自己寫的話：

> ⛔ **前綴測試不視為涵蓋母體。**

⇒ (b) 的四條前綴測試**⛔ 不能**替 (a) 的候選母體背書。(a) 另有自己的差集 inventory
測試（`test_the_union_is_a_strict_superset_of_the_old_criterion`），它量的是「哪些卡
會被納入比對」，⛔ 不是「兩個資源撞不撞」。

## 三個最容易被寫錯的地方

1. **(a) 讀成「替換」而非「聯集」。** 卡面逐字是「old→new（owner 非佔位 → 有 branch
   或 worktree）」，箭頭讀成替換 ⇒ 2026-09-02 實測**漏放 29 張活卡**（舊 33／新 15／
   聯集 44／交集 4）。需求方裁定 A-3 照准**聯集**。
2. **(b) 照抄 `WF_RESOURCE_WRITESET1` §8.5 的斷言方向。** 該節把
   `templates` × `templates2/a.md` 斷言為**相交**——那是它的**立即階段**；本卡採
   **目標階段**（§2.2），同一對的正確斷言是**不相交**。⭐ 這是本檔最大的陷阱。
3. **(c) 第三格照抄卡面逐字。** 「registry 載入或解析失敗 → 拒絕 assign」在**內嵌
   進碼**的實作下無法實作（碼常數的載入失敗＝整個 wfcli 起不來）⇒ 裁定 A-5 改成
   **模組載入期 schema 自檢**。本檔測的是後者。
"""

from __future__ import annotations

import pytest

from wf_cli.project import ItemSnapshot
from wf_cli.resources import (
    DB_CANONICAL_ENVIRONMENTS,
    DB_ENVIRONMENT_ALIASES,
    ResourceDeclaration,
    comparison_key,
    detailed_conflicts,
    file_resources_intersect,
    find_conflicts,
    normalize_db_resource,
    repo_of_issue_url,
    unregistered_db_environments,
)
from wf_cli.commands.assign_cmd import is_intersection_candidate, render_conflict_refusal


def _item(owner: str | None, branch_worktree: str | None) -> ItemSnapshot:
    return ItemSnapshot(
        item_id="PVTI_x",
        content_type="Issue",
        title="t",
        body="",
        fields={"owner": owner, "分支worktree": branch_worktree},
    )


def _decl(*resources: str, db_scope: str = "write") -> ResourceDeclaration:
    return ResourceDeclaration(db_scope=db_scope, resources=list(resources))


# =========================================================== (a) 候選母體＝聯集

@pytest.mark.parametrize(
    "owner,branch_worktree,expected",
    [
        # 四個象限窮舉。⛔ 不抽樣——判準只有兩個布林，母體就是這四格。
        ("ruan6047", "ai/x @ /tmp/w", True),   # 兩者皆有
        ("ruan6047", "—", True),               # 只有 owner（舊判準）
        ("待指派", "ai/x @ /tmp/w", True),      # ⭐ 只有 branch/worktree —— 替換版會漏放這一格
        ("待指派", "—", False),                 # 兩者皆無
    ],
)
def test_the_candidate_set_is_the_union_of_both_signals(owner, branch_worktree, expected):
    assert is_intersection_candidate(_item(owner, branch_worktree)) is expected


@pytest.mark.parametrize("placeholder", ["待指派", "待建立", "待認領", "—", "", None])
def test_every_owner_placeholder_is_still_a_placeholder(placeholder):
    """佔位值域沿 `card._OWNER_PLACEHOLDER_PREFIXES`，⛔ 不在本卡另打一份。"""
    assert is_intersection_candidate(_item(placeholder, "—")) is False


def test_the_union_is_a_strict_superset_of_the_old_criterion():
    """⭐ **差集 inventory**（卡面逐字要求「兩判準差集 inventory test」）。

    ⛔ 這條⛔ 不是「聯集比較大」這種同義反覆——它列出**差集裡實際有什麼形狀**，
    並斷言那個形狀恰好是「無 owner 但有分支／工作樹」，⛔ 沒有別的。
    """
    from wf_cli.card import is_owner_assigned, parse_branch_worktree

    fixtures = [
        ("ruan6047", "ai/x @ /tmp/w"),
        ("ruan6047", "—"),
        ("待指派", "ai/x @ /tmp/w"),
        ("待建立", "ai/y @ /tmp/z"),
        ("待指派", "—"),
        (None, None),
    ]
    old = {f for f in fixtures if is_owner_assigned(f[0])}
    new = {f for f in fixtures if any(parse_branch_worktree(f[1] or ""))}
    union = {f for f in fixtures if is_intersection_candidate(_item(*f))}

    assert union == old | new
    assert old < union, "聯集必須**嚴格**大於舊判準，否則這一條 AC 沒有做任何事"
    # 差集裡只有一種形狀：無 owner、有分支／工作樹。
    assert all(not is_owner_assigned(o) and any(parse_branch_worktree(b or ""))
               for o, b in union - old)


# ================================================= (b) `file:` 分量序列前綴相交

def test_component_boundary_a_bc_is_not_hit_by_a_b():
    """卡面逐字點名的那一對。字串 `startswith` 會誤判，分量序列⛔ 不會。"""
    assert file_resources_intersect("file:a/b", "file:a/bc") is False
    assert comparison_key("file:a/b") == ("a", "b")
    assert comparison_key("file:a/bc") == ("a", "bc")


def test_the_immediate_stage_assertion_direction_is_not_copied():
    """⭐⭐ **本檔最大的陷阱。**

    `docs/WF_RESOURCE_WRITESET1.md` §8.5 把 `templates` × `templates2/a.md` 斷言為
    **相交**——那是它的**立即階段**。本卡採**目標階段**（§2.2 逐字「首分量
    `templates ≠ templates2` → 不相交」）。⛔ 不得照抄 §8.5 的方向。
    """
    assert file_resources_intersect("file:templates", "file:templates2/a.md") is False


def test_nfc_equivalent_paths_hit():
    """同一個字的合成形式與分解形式。NFC 之後相等 ⇒ 相交。"""
    composed = "file:docs/é.md"        # é（U+00E9，單一碼位）
    decomposed = "file:docs/é.md"      # e + U+0301 組合尖音符
    assert composed != decomposed
    assert file_resources_intersect(composed, decomposed) is True


def test_casefold_equivalent_paths_hit():
    """`§2.3(2)` 逐字的**刻意 fail-closed 側**：開發機檔案系統實測大小寫不敏感。"""
    assert file_resources_intersect("file:docs/A.md", "file:docs/a.md") is True


def test_a_genuinely_non_prefix_pair_is_the_negative_control():
    """負控。⛔ 沒有這一條，上面四條全綠也可能只是「恆真」。"""
    assert file_resources_intersect("file:docs/a.md", "file:cli/b.py") is False
    assert file_resources_intersect("file:a/b/c", "file:a/x/c") is False


@pytest.mark.parametrize(
    "raw,key",
    [
        ("file:./templates/", ("templates",)),
        ("file:templates//a.md", ("templates", "a.md")),
        ("file:templates/./a.md", ("templates", "a.md")),
        ("file:templates", ("templates",)),
    ],
)
def test_trailing_slash_and_dot_components_do_not_change_the_key(raw, key):
    """§2.1 末段逐字：結尾斜線只表達宣告意圖，⛔ 不參與相交判定。"""
    assert comparison_key(raw) == key


def test_an_undeclared_directory_ancestor_still_intersects():
    """§2.3(3)：`file:templates`（宣告為檔案）× `file:templates/a.md` ⇒ **相交**。

    兩者對 `templates` 的型別認知矛盾且無法由字面判斷誰對 ⇒ 判 fail-closed 側，
    ⛔ 不讓它落進一個未定義的格子。
    """
    assert file_resources_intersect("file:templates", "file:templates/a.md") is True


# =========================================================== (b) §4.2 repo 限定詞

_A = "https://github.com/ruan6047/ai-workflow/issues/1"


def test_repo_of_issue_url_only_accepts_the_declared_shape():
    assert repo_of_issue_url(_A) == "ruan6047/ai-workflow"
    assert repo_of_issue_url(None) is None
    assert repo_of_issue_url("https://github.com/ruan6047/ai-workflow/pull/1") is None
    assert repo_of_issue_url("PVTI_draftissue") is None


def test_file_resources_in_different_repos_do_not_intersect():
    mine, other = _decl("file:cli/src/"), _decl("file:cli/src/x.py")
    assert find_conflicts(mine, "OTHER", other) == ["file:cli/src/"]
    assert find_conflicts(
        mine, "OTHER", other,
        mine_repo="ruan6047/ai-workflow", other_repo="ruan6047/cpbl-analytics",
    ) == []


@pytest.mark.parametrize("mine_repo,other_repo", [(None, "r/b"), ("r/a", None), (None, None)])
def test_the_repo_qualifier_is_not_applied_when_either_side_is_unestablished(mine_repo, other_repo):
    """§4.2 逐字「歸屬必須**正向確立**，否則⛔ 不得套用此限定」。

    它是**放行方向**的規則 ⇒ 前提必須被證明。誤拒的代價是排隊，漏放的代價是
    兩張卡同寫一檔，取前者。
    """
    mine, other = _decl("file:cli/src/"), _decl("file:cli/src/x.py")
    assert find_conflicts(mine, "OTHER", other, mine_repo=mine_repo, other_repo=other_repo)


def test_port_and_container_ignore_the_repo_qualifier():
    """§4.3 逐字：它們是主機層級資源，兩個 repo 搶同一個 `port:4001` 是真的搶。"""
    mine, other = _decl("port:4001", "container:pg"), _decl("port:4001", "container:pg")
    assert find_conflicts(
        mine, "OTHER", other, mine_repo="r/a", other_repo="r/b"
    ) == ["container:pg", "port:4001"]


def test_port_has_no_prefix_semantics():
    """`port:` ⛔ 沒有路徑結構 ⇒ ⛔ 不得套前綴語意（`port:400` 不撞 `port:4001`）。"""
    assert find_conflicts(_decl("port:400"), "OTHER", _decl("port:4001")) == []


# ================================================================ (c) db: 別名

def test_the_alias_table_is_empty_today_and_that_is_a_newborn_zero():
    """⚠️ **新生 0**：機制從未上線 ⇒ 「0 筆別名」是因果倒置，⛔ 不得讀成「不需要」。"""
    assert DB_ENVIRONMENT_ALIASES == {}


def test_cell_one_registered_alias_normalises(monkeypatch):
    """第一格：**已登記別名 → 正規化命中**。"""
    monkeypatch.setitem(DB_ENVIRONMENT_ALIASES, "prod", "production")
    assert normalize_db_resource("db:prod:schema") == ("db:production:schema", True)
    mine, other = _decl("db:prod:schema"), _decl("db:production:schema")
    assert find_conflicts(mine, "OTHER", other) == ["db:prod:schema"]


def test_cell_two_unregistered_environment_is_taken_literally():
    """第二格：**未登記 → 按字面**（第二元回 False，呼叫端據此發 stderr 警示）。"""
    assert normalize_db_resource("db:zzz:schema") == ("db:zzz:schema", False)
    assert unregistered_db_environments(["db:zzz:schema", "db:production:schema"]) == [
        "db:zzz:schema"
    ]
    # 按字面 ⇒ 與另一個未登記環境⛔ 不會被硬湊在一起。
    assert find_conflicts(_decl("db:zzz:schema"), "OTHER", _decl("db:yyy:schema")) == []


def test_canonical_environments_are_registered_and_do_not_warn():
    """canonical 集合來源＝`templates/database-contract.md` §2 的表，逐字四列。

    ⚠️ 這是本卡對「已登記」的解讀（卡面⛔ 未列舉 canonical 集合）；⛔ 若只把別名表
    當「已登記」，今日表空 ⇒ 連正確拼法都吃警示，第二格會退化成「全部」。
    """
    assert DB_CANONICAL_ENVIRONMENTS == ("local", "test", "staging", "production")
    assert unregistered_db_environments(
        [f"db:{env}:schema" for env in DB_CANONICAL_ENVIRONMENTS]
    ) == []


def test_cell_three_is_a_module_load_time_schema_selfcheck():
    """第三格：**載入期 schema 自檢**（裁定 A-5；卡面逐字在內嵌實作下無法實作）。

    ⛔ 不得降級為警告——本測試直接餵三種壞 schema，每一種都必須**丟例外**。
    """
    import wf_cli.resources as res

    for bad in (
        {"prod": "不存在的環境"},          # 指向非 canonical
        {"production": "production"},      # 別名與 canonical 同名 ⇒ 「已登記」有兩個答案
        {"": "production"},                # 空鍵
    ):
        original = dict(res.DB_ENVIRONMENT_ALIASES)
        res.DB_ENVIRONMENT_ALIASES.clear()
        res.DB_ENVIRONMENT_ALIASES.update(bad)
        try:
            with pytest.raises(res.ResourceDeclarationError):
                res._selfcheck_db_alias_schema()
        finally:
            res.DB_ENVIRONMENT_ALIASES.clear()
            res.DB_ENVIRONMENT_ALIASES.update(original)


def test_the_selfcheck_passes_on_todays_table():
    """正控。⛔ 沒有這一條，上一條可能只是「恆炸」。"""
    import wf_cli.resources as res

    res._selfcheck_db_alias_schema()  # ⛔ 不得丟例外


def test_the_alias_table_must_not_normalise_an_illegal_literal():
    """`0c629ac` 逐字「⛔ 不為舊文件訂特殊規則」：非法字面歸 `ResourceDeclarationError`。"""
    assert normalize_db_resource("db:production:cpbl") == ("db:production:cpbl", True)
    # ⚠️ 上面回 True 只代表 **env 分量**已登記；整串合不合法由 `RESOURCE_PATTERN`
    # 在 `parse_block` 那一關判，⛔ 不由別名表救。
    from wf_cli.resources import _RESOURCE_PREFIX_RE

    assert _RESOURCE_PREFIX_RE.match("db:production:cpbl") is None


# ============================================================ 拒絕訊息四要件

def test_the_refusal_message_carries_all_four_requirements():
    conflicts = detailed_conflicts(
        _decl("file:cli/src/"), "OTHER-CARD", _decl("file:cli/src/wf_cli/doctor.py")
    )
    assert len(conflicts) == 1
    text = render_conflict_refusal("MY-CARD", conflicts)

    # ① 哪兩個分量序列互為前綴，含雙方卡 ID 與**原始字面**
    assert "MY-CARD" in text and "OTHER-CARD" in text
    assert "file:cli/src/" in text and "file:cli/src/wf_cli/doctor.py" in text
    assert "('cli', 'src')" in text
    # ② 觸發哪一來源
    assert "來源＝分量序列前綴" in text
    # ③ 可貼進 `wfcli amend --resources` 的收窄**寫法**
    #
    # ⚠️ **2026-09-03（`R3-001`）改寫**：原斷言是 `"wfcli amend MY-CARD --resources" in text`
    # ——那一行實作成 `wfcli amend MY-CARD --resources file:收窄後的路徑 …`，而**同一則
    # 訊息的開頭**逐字寫著「⛔ 不給填空樣板」⇒ **自我矛盾**，查核者 R3-001 命其刪除。
    # ⛔ **這⛔ 不是把要件 ③ 拿掉**：③ 逐字是「收窄**寫法**」，⛔ 不是「一行可照貼的
    # 完整指令」。收窄到哪個路徑構造上是**人的判斷** ⇒ 寫法＝(a) 指名要動哪個旗標、
    # (b) 每一則衝突各附一句收窄方向。兩者現在都在，且⛔ 不含任何填空指令。
    assert "`--resources` ＝ **收窄後的真實路徑**" in text
    assert "wfcli amend --help" in text, "旗標與值域的入口仍要給，且它是可跑的"
    assert "收窄：" in text, "每一則衝突各附一句收窄方向"


def test_the_refusal_message_offers_no_force_escape_hatch():
    """`registry.py:614` 逐字「給逃生口等於把『沒注意到』變成『按一下』」。"""
    conflicts = detailed_conflicts(_decl("file:a"), "OTHER", _decl("file:a/b"))
    text = render_conflict_refusal("MY-CARD", conflicts)
    assert "--force" not in text


@pytest.mark.parametrize(
    "mine,theirs,source",
    [
        ("file:a/b.md", "file:a/b.md", "完全相同"),
        ("file:a", "file:a/b.md", "分量序列前綴"),
        ("file:a/B.md", "file:a/b.md", "casefold 等價"),
        ("file:a/é.md", "file:a/é.md", "NFC 等價"),
        ("db:production:schema", "db:production:schema", "完全相同"),
    ],
)
def test_the_source_is_drawn_from_the_closed_domain(mine, theirs, source):
    from wf_cli.resources import CONFLICT_SOURCES

    conflicts = detailed_conflicts(_decl(mine), "OTHER", _decl(theirs))
    assert len(conflicts) == 1
    assert conflicts[0].source == source
    assert source in CONFLICT_SOURCES


# ============================================================ 回歸：舊行為不變

def test_db_resources_are_still_shareable_when_both_sides_are_read_only():
    """canonical §4.1「read-only 才可共用」。⛔ 本卡不改它。"""
    mine = _decl("db:dev:table:players", db_scope="read")
    other = _decl("db:dev:table:players", db_scope="read")
    assert find_conflicts(mine, "OTHER", other) == []


def test_file_resources_conflict_even_when_both_sides_are_read_only():
    mine = _decl("file:shared.py", db_scope="read")
    other = _decl("file:shared.py", db_scope="read")
    assert find_conflicts(mine, "OTHER", other) == ["file:shared.py"]
