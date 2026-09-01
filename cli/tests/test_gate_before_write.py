"""閘門前零寫入不變式的**黃金值載體**與關於守衛自身的斷言。

守衛本體（掛法、觀測、判定、回報）在 ``tests/conftest.py``；本檔只放兩種東西：

1. **黃金值** ``FROZEN``／``FROZEN_WHY``——守衛拿它比對。放這裡而不是 conftest，
   是為了不讓 conftest 同時是守衛又是斷言（守衛在 session 級跑，斷言由 pytest 收集）。
2. **關於守衛自身的斷言**——「排除集不是垃圾桶」、「整套跑」判準的變異檢驗、
   唯讀白名單的承重檢驗、以及那八件「⛔ 不得由它綠燈推出」不得被靜默刪掉。

⛔ **本檔不驗產品行為**。產品行為由既有測試套件驗；守衛只是在那些測試跑的時候
順帶記下順序事實。
"""

from __future__ import annotations

import pytest
from wf_cli.commands import (
    amend_cmd,
    assign_cmd,
    checkpoint_cmd,
    handoff_cmd,
    open_cmd,
    review_cmd,
)
from wf_cli.project import find_item_by_card_id, list_items, resolve_project

from . import conftest as guard
from .fake_gh import FakeGhRunner, open_required_argv
from .test_amend import GOV_TARGET
from .test_checkpoint import EventGhRunner
from .test_commands_mocked import _assign_argv, _open_for_assign, run_cli
from .test_review import APPROVE_REPORT, open_card, review_argv, write_input

# ---------------------------------------------------------------------------
# 黃金值
# ---------------------------------------------------------------------------

#: 已知且**逐字登記**的殘餘違規：鍵＝``(動詞, rc)``，值＝整套跑時的出現次數。
#:
#: **為什麼鍵是 ``(動詞, rc)`` 而不是 nodeid**：測試改名不該弄紅它，但新增一條同
#: ``(動詞, rc)`` 的違規會讓計數 2→3 而轉紅。（實測未搬動的 ``b169c242`` 上 60 次
#: 違規只對應 13 個 ``(動詞, rc)`` 組合 ⇒ 鍵集合小、可讀、對重構穩定。）
FROZEN: dict[tuple[str, int], int] = {("amend", 5): 2}

#: 每一個 ``FROZEN`` 條目**為什麼在這裡**。⛔ 沒有理由的條目就是死條目——
#: ``test_every_frozen_entry_carries_a_reason`` 會擋下沒寫理由的新增。
FROZEN_WHY: dict[tuple[str, int], str] = {
    ("amend", 5): (
        "⭐ **為什麼觀測面看不到那次寫入**（⛔ 這不是「amend 的拒收路徑零寫入」）：\n"
        "  `tests/test_amend.py::test_tier_write_failure_aborts_before_touching_body` 與\n"
        "  `tests/test_amend.py::test_exit5_message_points_to_record_unlogged_change` 兩條\n"
        "  自己做了 `monkeypatch.setattr(amend_cmd, \"set_field_value\", …)`，把寫入函式\n"
        "  掉包成 no-op。⇒ 產品碼**真的呼叫了** `set_field_value`（級別欄先寫、body 後寫），\n"
        "  但那次呼叫從來沒有走到 `FakeGhRunner` 的出口，於是守衛（掛在 gh 出口上）\n"
        "  必然看不到它，序列只剩 `['EF']`。\n"
        "  ⛔ **不得把這兩條讀成缺陷**：它們量的是「欄位寫失敗時 body 不被動」，\n"
        "  掉包寫入函式正是它們製造失敗的手段。\n"
        "  ⛔ **也不得把它讀成守衛的漏洞而去修掛法**：被掉包的是模組屬性，任何掛在\n"
        "  更下游（gh 出口）或更上游（動詞入口）的觀測面都看不到——這是觀測面的\n"
        "  結構性上限，不是掛錯地方。\n"
        "  ⇒ 這兩條在 `ensure_fields` 搬動之後仍會被點名，因此逐字凍結在這裡。"
    ),
}


def test_every_frozen_entry_carries_a_reason() -> None:
    """黃金值裡的每一條都要寫得出「為什麼看不到」，否則就是死條目。

    沿用本 repo 既有的「排除集不是垃圾桶」紀律（``test_every_exclusion_is_load_bearing``
    是同一個形狀）。⛔ 沒有這條，黃金值會變成「紅了就加一行」的垃圾桶，而守衛的
    鑑別力會被一行一行地餵掉。
    """
    assert set(FROZEN) == set(FROZEN_WHY), (
        f"黃金值與理由不對齊：只有值 {sorted(set(FROZEN) - set(FROZEN_WHY))}；"
        f"只有理由 {sorted(set(FROZEN_WHY) - set(FROZEN))}"
    )
    for key, why in FROZEN_WHY.items():
        assert len(why.strip()) >= 80, f"{key} 的理由太短，寫不出「為什麼看不到」：{why!r}"


def test_frozen_entries_name_the_observation_blind_spot_not_a_defect() -> None:
    """⛔ 黃金值不得被讀成「這些拒收路徑零寫入」。

    ``FROZEN`` 是**觀測面的盲點清單**，⛔ 不是「已驗證安全」清單。這條把那句話
    釘在測試裡：理由文字必須逐字帶著「monkeypatch」與「看不到」。
    """
    why = FROZEN_WHY[("amend", 5)]
    assert "monkeypatch" in why
    assert "看不到" in why


# ---------------------------------------------------------------------------
# V13：「整套跑」判準本身的變異檢驗
# ---------------------------------------------------------------------------
#
# ⚠️ 這個判準**很容易寫錯，而且錯了不會有人發現**——它只影響「少掉一條時要不要
# 紅」，而少掉一條在日常開發裡幾乎不出現。第 3 輪研究者連錯兩次：
#
#   (錯 1) 掃 `config.invocation_params.args` 找「不以 `-` 開頭」的 token 當位置參數
#          ⇒ 被 `-p no:cacheprovider` 的**選項值** `no:cacheprovider` 騙成「有位置參數」。
#   (錯 2) 看 `config.args` 是不是空的
#          ⇒ pytest 會把 ini 的 `testpaths` 填進 `config.args`，整套跑時它是 `["tests"]`
#             而不是 `[]`。
#
# ⇒ 正解是**與 `testpaths` 逐項相等**，再加上「任一收窄旗標有值即非整套」。
# 下面把兩個錯法連同正解一起寫成表，讓「判準被改回錯法」轉紅。


@pytest.mark.parametrize(
    ("args", "testpaths", "narrowing", "expected", "case"),
    [
        (["tests"], ["tests"], (), True, "整套跑：args 等於 testpaths"),
        ([], ["tests"], (), False, "空 args ≠ 整套（錯 2 會判 True）"),
        (["tests/test_amend.py"], ["tests"], (), False, "指定單檔"),
        (["tests", "docs"], ["tests"], (), False, "多一個路徑"),
        (["tests"], ["tests"], ("creates_the_missing",), False, "-k 收窄"),
        (["tests"], ["tests"], ("", "slow"), False, "-m 收窄"),
        (["tests"], ["tests"], ("", "", ["tests/test_amend.py::x"]), False, "--deselect 收窄"),
        (["tests"], ["tests"], ("", "", [], True), False, "--lf 收窄"),
        (["tests"], ["tests"], ("", "", [], False, True), False, "--ff 收窄"),
        (["tests"], [], (), False, "沒設 testpaths 時不宣稱整套（fail closed）"),
    ],
)
def test_full_run_predicate(args, testpaths, narrowing, expected, case) -> None:
    assert guard.is_full_run(args, testpaths, narrowing) is expected, case


def test_full_run_predicate_does_not_read_invocation_params() -> None:
    """⛔ 判準不得回頭去掃 `invocation_params.args`（錯 1）。

    ``is_full_run`` 是純函式：它只吃 (args, testpaths, 收窄旗標) 三個值。這條把
    「純函式」這件事釘住——簽章一旦長回去吃 config，這裡就轉紅。
    """
    import inspect

    params = list(inspect.signature(guard.is_full_run).parameters)
    assert params == ["args", "testpaths", "narrowing"], params


# ---------------------------------------------------------------------------
# 唯讀白名單：承重檢驗
# ---------------------------------------------------------------------------


def test_read_only_whitelist_is_load_bearing_in_the_fail_open_direction() -> None:
    """⭐ 白名單漏一項的方向是 **fail-open**，⛔ 不是 fail-closed。

    判準是「``ensure_fields`` 排在本輪第一次真寫入之前」。⇒ 把一個**唯讀**呼叫誤
    分類成寫入，會讓它變成「第一次寫入」而**豁免**整輪 ⇒ 真違規被吞掉。
    （反方向——把寫入誤分類成唯讀——只會多紅，那才是安全的一側。）

    這條把方向釘住：``("project","view")`` 是每一個動詞在 ``ensure_fields`` 之前
    必定送出的呼叫，它若不在白名單上，**每一輪**都會被豁免、守衛恆綠。
    """
    assert ("project", "view") in guard.READ_ONLY_GH
    assert guard.classify_gh(["project", "view", "1", "--owner", "acme"]) == "read"
    assert guard.classify_gh(["project", "field-create", "1", "--owner", "acme"]) == "write"
    assert guard.classify_gh(["project", "item-edit", "--id", "X"]) == "write"
    assert guard.classify_gh(["issue", "edit", "1", "--repo", "a/b"]) == "write"
    assert guard.classify_gh(["issue", "close", "1", "--repo", "a/b"]) == "write"
    # `gh api <path>` 預設 GET；帶 -X/--method/-f/--input 才是寫。
    assert guard.classify_gh(["api", "user", "--jq", ".login"]) == "read"
    assert guard.classify_gh(["api", "repos/a/b/issues/1"]) == "read"
    assert guard.classify_gh(["api", "repos/a/b/issues/1", "-X", "PATCH"]) == "write"
    # graphql 由 query 內容分流。
    assert guard.classify_gh(["api", "graphql", "-f", "query=query{x}"]) == "read"
    assert guard.classify_gh(["api", "graphql", "-f", "query=mutation{x}"]) == "write"


def test_field_list_stays_on_the_whitelist_on_purpose() -> None:
    """⚠️ ``("project","field-list")`` 今天在 ``src/`` 有 **0 處字面呼叫**（``aiwf#151``
    合併後 ``list_fields`` 改走原生 GraphQL）——它是一個**沒有現役消費者**的白名單條目。

    ⭐ **刻意保留**，理由是承重的、不是「留著以防萬一」：

    (a) 刻意如此：它留在集合裡，而不是被刪掉。
    (b) 為什麼：``gh project field-list`` 在構造上不可能改變遠端狀態；若它日後回到
        ``src/``（例如原生查詢被回退），而白名單少了它，它會被分類成「寫入」——
        依上面那條測試的方向分析，那是 **fail-open**：它排在 ``ensure_fields``
        之前，於是每一輪都被豁免、守衛靜靜恆綠。⇒ 刪掉它換來的是一個**會靜默
        失效**的守衛，那比一個沒有現役消費者的條目糟得多。
    (c) ⛔ 不得由本條推出「``field-list`` 仍在使用」——它不在；也⛔ 不得推出
        ``tests/test_pitfalls.py`` 的 ``_READ_ONLY_GH`` 該一併保留或刪除，那個集合
        不在本卡資源宣告內，本卡一個字都沒動它。
    """
    assert ("project", "field-list") in guard.READ_ONLY_GH


# ---------------------------------------------------------------------------
# 八件「⛔ 不得由它綠燈推出」不得被靜默刪掉
# ---------------------------------------------------------------------------


def test_the_eight_non_conclusions_are_still_there() -> None:
    """守衛旁那八件「⛔ 不得由它綠燈推出」是交付的一部分，⛔ 不是註解裝飾。

    它們最可能的死法不是被反駁，是**被下一次重構順手刪掉**。這條把數量與第一件
    的內容釘住：第一件必須是「``ensure_fields`` 仍不是唯讀的」——因為那句話就寫在
    這張卡的卡 ID 裡（``WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1``），是本卡最可能
    被誤讀的一句。
    """
    items = guard.MUST_NOT_CONCLUDE
    assert len(items) == 8, f"應為 8 件，實得 {len(items)}"
    assert all(len(t.strip()) >= 40 for t in items), "每一件都要寫得出「為什麼不得推出」"
    assert "唯讀" in items[0] and "呼叫時點" in items[0], items[0]


# ---------------------------------------------------------------------------
# V3／V14：負控——「拒收路徑變綠」與「ensure_fields 被弄丟」不得長得一樣
# ---------------------------------------------------------------------------
#
# ⭐ **為什麼非有不可**：本卡把 `ensure_fields` 往後搬。搬過頭（搬到某條寫入之後）
# 或搬丟（有人「順手」改成唯讀的 `list_fields`）之後，守衛只會更綠——它量的是
# 「EF 有沒有排在第一次寫入之前」，EF 不存在時它一句話都不會說。⇒ 必須有另一組
# 測試從**正向**釘住「該建的欄位真的被建出來」。
#
# ⚠️ **本輪實測到的缺口（⛔ 這不是假設）**：把五個呼叫點逐一由 `ensure_fields`
# 換成唯讀的 `list_fields`（＝功能被弄丟、碼照樣跑得動）之後，既有測試套件的
# 結果是——
#
#     open     149 failed ＋ 78 errors   ⇒ 紅（既有覆蓋足夠）
#     handoff  多 1 條紅：test_pitfalls.py::test_a_valid_report_still_creates_the_missing_field
#                                        ⇒ 紅（`aiwf#148` 為 R1-001 補的那條）
#     assign   逐條與基線相同            ⇒ ⛔ **綠**
#     review   逐條與基線相同            ⇒ ⛔ **綠**
#     amend    逐條與基線相同            ⇒ ⛔ **綠**
#
# ⇒ 下面三條就是補上 assign／review／amend 那三格。⛔ open 與 handoff 不重複造，
#   它們已有承重的既有測試（逐字見上方兩行）。
#
# ⛔ **不得由這三條推出「ensure_fields 在生產環境會建出欄位」**：它們跑在
#   `FakeGhRunner` 上，量的是 CLI 組裝出的呼叫序列，⛔ 不是真 `gh` 的行為。


def _forget_field(runner, name: str, owner: str = "acme", number: int = 1) -> None:
    """讓 Project 退回到**沒有這個凍結欄位**的樣子（欄位定義與所有 item 值一起拿掉）。

    ⚠️ item 值要一起拿掉：``FakeGhRunner`` 的批次讀取會拿欄位名回查欄位型別，留著
    孤兒值會在**讀取端**就 KeyError——那是測試替身的假象，不是產線行為。
    （形狀與 ``tests/test_pitfalls.py`` 的同名 helper 相同；⛔ 不 import 它——
    那是別張卡的私有 helper，本檔自帶四行比建立跨檔耦合便宜。）
    """
    runner.projects[(owner, number)]["fields"].pop(name, None)
    for raw in runner.items.values():
        raw["fields"].pop(name, None)


def _item(runner, card_id: str):
    return find_item_by_card_id(list_items(runner, resolve_project(runner, "acme", 1)), card_id)


@pytest.fixture
def cmd_runner(monkeypatch):
    runner = FakeGhRunner()
    for module in (open_cmd, assign_cmd, amend_cmd, handoff_cmd):
        monkeypatch.setattr(module, "default_runner", runner)
    return runner


@pytest.fixture
def review_runner(monkeypatch):
    # EventGhRunner（tests/test_checkpoint.py）＝ FakeGhRunner ＋ 事件平面；
    # review 自 WF-22-CLI4 起會在寫入前掃 timeline，少了它跑不起來。
    runner = EventGhRunner()
    for module in (open_cmd, handoff_cmd, review_cmd, checkpoint_cmd):
        monkeypatch.setattr(module, "default_runner", runner)
    return runner


@pytest.fixture
def gov_style_card(cmd_runner):
    """一張 T4 真 Issue 卡（形狀逐字取自 ``tests/test_amend.py`` 的 ``gov_card``）。

    ⛔ **刻意不 import 那個 fixture**：把別的測試模組的 fixture import 進來會讓
    ruff 判 F811（參數遮蔽同名 import），而在本檔加 ``# noqa`` 只是把雜訊換個位置。
    本檔需要的只是「一張可以 amend 的卡」，⛔ 不需要 ``gov_card`` 那顆
    ``CommentAwareRunner``（它是為了 ``--ruling-url`` 的留言身分查核而存在的）。
    """
    assert run_cli(
        ["open", *GOV_TARGET, "GOV-DEMO1",
         *open_required_argv(cmd_runner, "acme/wf"),
         "--feature", "示範", "--tier", "T4", "--db-scope", "none",
         "--core-pain", "原始痛點", "--service-goal", "目標",
         "--requested-by", "ruan6047", "--planned-by", "PM",
         "--resources", "file:demo.py", "--spec-baseline", "原基線",
         "--exec-capability", "主力型", "--exec-capability-reason", "一般實作",
         "--review-capability", "高階型", "--review-capability-reason", "紅線跨家族"]
    ) == 0
    return cmd_runner


def test_assign_recreates_the_field_it_is_about_to_write(cmd_runner) -> None:
    """`assign` 的 `ensure_fields` 搬到四道閘門之後了——它仍必須真的把欄位補回來。"""
    assert run_cli(_open_for_assign("EFCTRL-A1", **{"--exec-capability": "主力型"})) == 0
    _forget_field(cmd_runner, "分支worktree")
    assert "分支worktree" not in cmd_runner.projects[("acme", 1)]["fields"]

    rc = run_cli(_assign_argv("EFCTRL-A1", "某模型@某工具", "b", "/w", actual_capability="主力型"))

    assert rc == 0
    assert "分支worktree" in cmd_runner.projects[("acme", 1)]["fields"], (
        "閘門過了卻沒補欄位＝assign 的 ensure_fields 被搬丟了"
    )
    # ⭐ 不只看欄位定義出現，還要求值真的寫得進去——只補定義而拿到舊的 fields
    # 會靜靜跳過寫入，那在觀測面上與「補對了」長得一樣。
    assert _item(cmd_runner, "EFCTRL-A1").fields["分支worktree"] == "b @ /w"


def test_review_recreates_the_field_it_is_about_to_write(review_runner, tmp_path) -> None:
    """`review` 的 `ensure_fields` 搬到最後一道拒收之後了——它仍必須真的補回欄位。"""
    open_card("DEMO-CARD1", runner=review_runner)
    _forget_field(review_runner, "交付狀態")
    assert "交付狀態" not in review_runner.projects[("acme", 1)]["fields"]

    rc = run_cli(review_argv("DEMO-CARD1", write_input(tmp_path, APPROVE_REPORT)))

    assert rc == 0
    assert "交付狀態" in review_runner.projects[("acme", 1)]["fields"], (
        "閘門過了卻沒補欄位＝review 的 ensure_fields 被搬丟了"
    )
    assert _item(review_runner, "DEMO-CARD1").fields["交付狀態"] == "✅通過"


def test_amend_recreates_the_dual_home_field_it_is_about_to_write(gov_style_card) -> None:
    """`amend` 的第二個取值點（body 之後補寫雙居所欄位）仍必須真的補回欄位。"""
    _forget_field(gov_style_card, "Initiative")
    assert "Initiative" not in gov_style_card.projects[("acme", 1)]["fields"]

    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "掛到父卡", "--initiative", "ai-workflow#99"]
    )

    assert rc == 0
    assert "Initiative" in gov_style_card.projects[("acme", 1)]["fields"], (
        "閘門過了卻沒補欄位＝amend 的 ensure_fields 被搬丟了"
    )
    assert _item(gov_style_card, "GOV-DEMO1").text("Initiative") == "ai-workflow#99"


def test_amend_tier_branch_recreates_the_field_it_is_about_to_write(gov_style_card) -> None:
    """`amend` 的**第一個**取值點（級別欄先寫那條）是另一條路，各自要有負控。

    ⚠️ 兩個取值點是本卡把一個呼叫拆成兩個的產物 ⇒ 一條測試只釘得住一個。
    """
    _forget_field(gov_style_card, "級別")
    assert "級別" not in gov_style_card.projects[("acme", 1)]["fields"]

    rc = run_cli(["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "改級別", "--tier", "T3"])

    assert rc == 0
    assert "級別" in gov_style_card.projects[("acme", 1)]["fields"], (
        "閘門過了卻沒補欄位＝amend 級別分支的 ensure_fields 被搬丟了"
    )
    assert _item(gov_style_card, "GOV-DEMO1").text("級別") == "T3"
