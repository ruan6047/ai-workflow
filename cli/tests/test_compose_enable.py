"""驗證 modules/*/module.md §0 的 scope ∧ enable_if（core/modules.md §2），resource-lock 的事實由測試供給。"""
from copy import deepcopy
from pathlib import Path

import pytest

from wf.compose.blocks import load_blocks
from wf.compose.enable import KINDS, READY, UnknownEnableKindError, activate, is_enabled

ROOT = Path(__file__).resolve().parents[2]
MODULES = {block.data["name"]: block.data for block in load_blocks(ROOT).by_label("yaml wf-module")}


def _listing(module):
    """scope=project 的模組先要名列 .wf/modules.json 才談 enable_if（core/modules.md §2）。"""
    return {"modules_list": [module["name"]]} if module["scope"] == "project" else {}


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
    for key, value in _listing(module).items():
        positive.setdefault(key, value)
    original = deepcopy((module, positive))
    assert is_enabled(module, **positive)
    assert not is_enabled(module)
    assert (module, positive) == original
    print("ENABLE_IF", name, module["scope"], condition, "positive=True negative=False")


@pytest.mark.parametrize("name", sorted(MODULES))
def test_project_scope_requires_the_registry_listing(name):
    """scope=project 的模組：enable_if 成立但未列入 registry ⇒ 仍不啟用（resource-lock 的板上
    predicate 曾可在空 registry 下自動啟用，本條就是那個缺陷的負控）。scope=card 不受 registry 影響。"""
    module = MODULES[name]
    condition = module["enable_if"]
    facts = ([{"state": condition["state"], "owner_actor": "other"}] * condition["min"]
             if condition["kind"] == "other_actor_card_in_state" else [])
    card = {"owner": {"actor": "self"}, "stage_plan": ["研究", "部署", "維護"],
            "parent": "WF-000", "tier_basis": {"sensitive": ["statistics"]}}
    listed = is_enabled(module, modules_list=[name], card=card, board_facts=facts)
    unlisted = is_enabled(module, modules_list=[], card=card, board_facts=facts)
    assert listed is True, name
    assert unlisted == (module["scope"] != "project"), (name, module["scope"])
    print("SCOPE_GATE", name, module["scope"], "listed=True unlisted=" + str(unlisted))


@pytest.mark.parametrize("listed", [False, True])
@pytest.mark.parametrize("predicate", [False, True])
def test_resource_lock_activation_quadrants(listed, predicate):
    """四象限（registry 列名 × 板上 predicate）：只有兩者都成立才啟用。

    基線缺陷＝空 registry 下板上 predicate 成立就自動啟用（左上與左下同為 True）；
    scope=project 的合取把左欄壓成 False。啟用之後 capable 仍是空的——resource-lock 是
    experimental，⛔ 不進自動能力組合。
    """
    module = MODULES["resource-lock"]
    condition = module["enable_if"]
    facts = [{"state": condition["state"], "owner_actor": "other"}] * (condition["min"] if predicate else 0)
    result = activate([module], modules_list=["resource-lock"] if listed else [],
                      card={"owner": {"actor": "self"}}, board_facts=facts)
    assert bool(result.enabled) == (listed and predicate), (listed, predicate)
    assert result.names == []  # experimental ⇒ 四象限都不貢獻自動能力
    print(f"QUADRANT listed={listed} predicate={predicate} enabled={bool(result.enabled)} capable=0")


def test_activate_is_the_single_entry_and_splits_capable_from_enabled():
    """單一啟用入口輸出兩個集合：enabled＝scope ∧ enable_if，capable＝enabled ∧ maturity=ready。
    自動能力七項只收 capable；adds.notes 不在七項內，收 enabled（core/modules.md §3）。"""
    declarations = [MODULES[name] for name in sorted(MODULES)]
    listed = [name for name, module in MODULES.items() if module["scope"] == "project"]
    card = {"owner": {"actor": "self"}, "stage_plan": ["研究", "部署", "維護"],
            "parent": "WF-000", "tier_basis": {"sensitive": ["statistics"]}}
    facts = [{"state": "進行中", "owner_actor": "other"}]
    result = activate(declarations, modules_list=listed, card=card, board_facts=facts)
    enabled = {module["name"] for module in result.enabled}
    capable = {module["name"] for module in result.capable}
    assert capable == {name for name in enabled if MODULES[name]["maturity"] == READY}
    assert capable < enabled, (capable, enabled)  # 真子集：非 ready 的模組確實有啟用者
    assert set(result.names) == capable
    assert all(MODULES[name]["maturity"] != READY for name in enabled - capable)
    print("ACTIVATE", "enabled=" + str(sorted(enabled)), "capable=" + str(sorted(capable)))


def test_unavailable_modules_contribute_nothing_even_when_enabled():
    """deploy／maintenance 落 unavailable：stage_plan 含該階段時 enabled 收得到，capable 收不到。"""
    card = {"stage_plan": ["部署", "維護"]}
    result = activate([MODULES[name] for name in ("deploy", "maintenance")], card=card)
    assert {module["name"] for module in result.enabled} == {"deploy", "maintenance"}
    assert result.capable == [] and result.names == []
    for name in ("deploy", "maintenance"):
        adds = MODULES[name]["adds"]
        assert adds["stages"] == [] and adds["enums"]["states"] == []
        assert adds["transitions"] == {"add": [], "remove": []}
        assert adds["handoff_sections"] == [] and adds.get("counters", []) == []
        assert adds.get("move_prints", []) == []
    print("UNAVAILABLE_ZERO_INJECTION deploy, maintenance")


def test_unknown_kind_has_distinct_error_type():
    with pytest.raises(UnknownEnableKindError) as caught:
        is_enabled({"name": "sample", "scope": "card", "enable_if": {"kind": "unknown"}})
    print("ENABLE_NEGATIVE_CONTROL", type(caught.value).__name__, str(caught.value))


@pytest.mark.parametrize("minimum", [0, 1, 2])
@pytest.mark.parametrize("count", [0, 1, 2])
def test_board_min_boundaries_and_same_actor_excluded(minimum, count):
    module = deepcopy(MODULES["resource-lock"])
    condition = module["enable_if"]
    condition["min"] = minimum
    listed = [module["name"]]  # scope=project ⇒ 先列入才談板上 predicate
    card = {"owner": {"actor": "self"}}
    facts = [{"state": condition["state"], "owner_actor": "self"},
             {"state": "different-state", "owner_actor": "other"}]
    # 計數單位為卡，不是不同 actor 數；同 actor 的其他卡各自計數。
    facts += [{"state": condition["state"], "owner_actor": "other"} for _ in range(count)]
    assert is_enabled(module, modules_list=listed, card=card, board_facts=facts) == (count >= minimum)
    assert not is_enabled(module, card=card, board_facts=facts)  # 未列入 registry 一律不啟用
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
    scopes = {name: module["scope"] for name, module in MODULES.items()}
    maturities = {name: module["maturity"] for name, module in MODULES.items()}
    print("MODULE_COUNT", len(MODULES), "KINDS", sorted(kinds))
    print("SCOPES", sorted(scopes.items()), "MATURITIES", sorted(maturities.items()))
    assert kinds == KINDS  # 宣告用到的 kind 全在已實作封閉集內，⛔ 不重打字面
    assert {name for name, scope in scopes.items() if scope == "project"} == {
        "escalation", "resource-lock", "pitfalls-13", "identity", "snapshot", "db-contract"}
    assert {name for name, scope in scopes.items() if scope == "card"} == {
        "research", "deploy", "maintenance", "initiative", "stat-redline"}
    assert {name for name, value in maturities.items() if value == "ready"} == {
        "escalation", "initiative", "research"}
    assert {name for name, value in maturities.items() if value == "experimental"} == {
        "resource-lock", "snapshot"}
    assert {name for name, value in maturities.items() if value == "manual"} == {
        "db-contract", "identity", "pitfalls-13", "stat-redline"}
    assert {name for name, value in maturities.items() if value == "unavailable"} == {
        "deploy", "maintenance"}
