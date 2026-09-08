"""驗證 modules/*/module.md §0 的 enable_if，resource-lock 的事實由測試供給。"""
from copy import deepcopy
from pathlib import Path

import pytest

from wf.compose.blocks import load_blocks
from wf.compose.enable import UnknownEnableKindError, is_enabled

ROOT = Path(__file__).resolve().parents[2]
MODULES = {block.data["name"]: block.data for block in load_blocks(ROOT).by_label("yaml wf-module")}


@pytest.mark.parametrize("name", sorted(MODULES))
def test_every_declared_module_positive_negative(name):
    module = MODULES[name]
    condition = module["enable_if"]
    kind = condition["kind"]
    positive = {}
    if kind == "project_module_listed":
        assert set(condition) == {"kind"}
        positive = {"modules_list": [name]}
    elif kind == "stage_plan_has":
        assert set(condition) == {"kind", "stage"}
        positive = {"card": {"stage_plan": [condition["stage"]]}}
    elif kind == "field_nonempty":
        assert set(condition) == {"kind", "field"}
        positive = {"card": {condition["field"]: "WF-001"}}
    elif kind == "field_contains":
        assert set(condition) == {"kind", "field", "value"}
        head, tail = condition["field"].split(".")
        positive = {"card": {head: {tail: [condition["value"]]}}}
    elif kind == "other_actor_card_in_state":
        assert set(condition) == {"kind", "state", "min"}
        positive = {"card": {"owner": {"actor": "self"}},
                    "board_facts": [{"state": condition["state"], "owner_actor": "other"}]}
    else:
        pytest.fail(f"宣告新增未涵蓋 kind: {kind}")
    original = deepcopy((module, positive))
    assert is_enabled(module, **positive)
    assert not is_enabled(module)
    assert (module, positive) == original
    print("ENABLE_IF", name, condition, "positive=True negative=False")


def test_unknown_kind_has_distinct_error_type():
    with pytest.raises(UnknownEnableKindError) as caught:
        is_enabled({"name": "sample", "enable_if": {"kind": "unknown"}})
    print("ENABLE_NEGATIVE_CONTROL", type(caught.value).__name__, str(caught.value))


@pytest.mark.parametrize("minimum", [0, 1, 2])
@pytest.mark.parametrize("count", [0, 1, 2])
def test_board_min_boundaries_and_same_actor_excluded(minimum, count):
    module = deepcopy(MODULES["resource-lock"])
    condition = module["enable_if"]
    condition["min"] = minimum
    card = {"owner": {"actor": "self"}}
    facts = [{"state": condition["state"], "owner_actor": "self"},
             {"state": "different-state", "owner_actor": "other"}]
    # 計數單位為卡，不是不同 actor 數；同 actor 的其他卡各自計數。
    facts += [{"state": condition["state"], "owner_actor": "other"} for _ in range(count)]
    assert is_enabled(module, card=card, board_facts=facts) == (count >= minimum)
    print(f"BOARD_MIN min={minimum} matches={count} enabled={count >= minimum}")


@pytest.mark.parametrize("card", [{}, {"parent": None}, {"parent": ""}])
def test_nonempty_unfilled(card):
    assert not is_enabled(MODULES["initiative"], card=card)


@pytest.mark.parametrize("basis", [None, {}, {"sensitive": []}, {"sensitive": ["rules"]},
                                        {"sensitive": "statistics"}])
def test_nested_field_requires_exact_list_member(basis):
    assert not is_enabled(MODULES["stat-redline"], card={"tier_basis": basis})


def test_module_inventory():
    kinds = {module["enable_if"]["kind"] for module in MODULES.values()}
    print("MODULE_COUNT", len(MODULES), "KINDS", sorted(kinds))
    assert kinds == {"project_module_listed", "stage_plan_has", "field_nonempty",
                     "field_contains", "other_actor_card_in_state"}
