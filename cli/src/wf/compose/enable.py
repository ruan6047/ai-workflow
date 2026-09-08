"""消費 modules/*/module.md §0 enable_if；resource-lock/module.md §0 的板上事實。"""


class UnknownEnableKindError(ValueError):
    """宣告的 enable_if kind 沒有對應的事實運算。"""


def _field(card: dict, path: str):
    value = card
    for key in path.split("."):
        value = value.get(key) if isinstance(value, dict) else None
    return value


def is_enabled(module: dict, *, modules_list=(), card=None, board_facts=()) -> bool:
    """純資料運算；呼叫端供給本卡與板上 state／owner_actor。"""
    card = {} if card is None else card
    condition = module["enable_if"]
    kind = condition["kind"]
    if kind == "project_module_listed":
        return module["name"] in modules_list
    if kind == "stage_plan_has":
        return condition["stage"] in card.get("stage_plan", [])
    if kind == "field_nonempty":
        return _field(card, condition["field"]) not in (None, "", [], {})
    if kind == "field_contains":
        values = _field(card, condition["field"])
        return isinstance(values, list) and condition["value"] in values
    if kind == "other_actor_card_in_state":
        actor = _field(card, "owner.actor")
        return sum(fact["state"] == condition["state"] and fact["owner_actor"] != actor
                   for fact in board_facts) >= condition["min"]
    raise UnknownEnableKindError(f"未知 enable_if kind: {kind!r}")
