"""消費 core/modules.md §2／§3 與 modules/*/module.md §0 `scope`／`enable_if`／`maturity`；
resource-lock/module.md §0 的板上事實。

`activate` 是 `cli/src/wf` 取得啟用集合的單一入口（core/modules.md §2）：動詞層 ⛔ 不自行組合
`modules_list` 與 predicate。`is_enabled` 只是它的逐一判定，留作值域與邊界測試的被測物。
"""
from dataclasses import dataclass

# 已實作的 enable_if kind 封閉集；宣告驗證從這裡取值（core/modules.md §1），⛔ 不重打字面。
KINDS = frozenset(("project_module_listed", "stage_plan_has", "field_nonempty",
                   "field_contains", "other_actor_card_in_state"))
PROJECT_SCOPE = "project"  # core/enums.md module_scope
READY = "ready"            # core/enums.md module_maturity：唯一具自動能力的值


class UnknownEnableKindError(ValueError):
    """宣告的 enable_if kind 沒有對應的事實運算。"""


@dataclass(frozen=True)
class Activation:
    """單一啟用入口的輸出。`enabled`＝scope ∧ enable_if；`capable`＝enabled ∧ maturity=ready。

    刻意分兩個集合：core/modules.md §3 的自動能力七項只收 `capable`，而 `adds.notes` 不在七項內
    ⇒ notes 合成收 `enabled`。⛔ 不得由 `capable` 推出「非 ready 模組未啟用」。
    """
    enabled: list[dict]
    capable: list[dict]

    @property
    def names(self) -> list[str]:
        """自動能力組合的模組名（`capable`）；投影／schema 合成的既有參數形狀。"""
        return [module["name"] for module in self.capable]


def _field(card: dict, path: str):
    value = card
    for key in path.split("."):
        value = value.get(key) if isinstance(value, dict) else None
    return value


def is_enabled(module: dict, *, modules_list=(), card=None, board_facts=()) -> bool:
    """純資料運算；呼叫端供給本卡與板上 state／owner_actor。

    core/modules.md §2：`scope=project` 須先名列 `.wf/modules.json`，再看 `enable_if`；
    `scope=card` 只看 `enable_if`。兩者是合取，⛔ 不是二選一。
    """
    card = {} if card is None else card
    if module["scope"] == PROJECT_SCOPE and module["name"] not in modules_list:
        return False
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


def activate(declarations, *, modules_list=(), card=None, board_facts=()) -> Activation:
    """單一啟用入口（core/modules.md §2）：宣告序列 → Activation；⛔ 不讀檔、⛔ 不連網。"""
    enabled = [module for module in declarations
               if is_enabled(module, modules_list=modules_list, card=card, board_facts=board_facts)]
    return Activation(enabled, [module for module in enabled if module["maturity"] == READY])
