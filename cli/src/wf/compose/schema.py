"""消費 core/card-schema.md §1、core/enums.md「值域」、core/return.md schema、
core/state-machine.md §2 與 modules/*/module.md §0。
"""
from copy import deepcopy

from .blocks import Catalog


def materialize(schema: dict, catalog: Catalog) -> dict:
    """只展開 wf-enums 引用；保留本地引用，回傳獨立副本。"""
    enums, = catalog.by_label("json wf-enums")

    def expand(node):
        if isinstance(node, list):
            return [expand(value) for value in node]
        if not isinstance(node, dict):
            return deepcopy(node)
        result = {key: expand(value) for key, value in node.items()}
        ref = result.get("$ref", "")
        if ref.startswith("wf-enums#/"):
            target = enums.data
            for part in ref.removeprefix("wf-enums#/").split("/"):
                target = target[part.replace("~1", "/").replace("~0", "~")]
            del result["$ref"]
            result.update(deepcopy(target))
        return result

    return expand(schema)


def compose_schema(catalog: Catalog, identifier: str, enabled_modules=()) -> dict:
    """啟用清單由呼叫端供給；不讀專案設定、不改 catalog。"""
    schema = materialize(catalog.schemas[identifier].data, catalog)
    enabled = set(enabled_modules)
    definitions = schema.get("$defs", {})
    for block in catalog.by_label("yaml wf-module"):
        module = block.data
        name = module["name"]
        if identifier == "wf-card":
            schema["properties"].update(definitions["module_fields"].get(name, {}))
            if name in enabled:
                states = definitions["nonterminal"]["enum"]
                for state in module["adds"]["enums"]["states"]:
                    if state not in states:
                        states.append(state)
        elif identifier == "wf-return" and name in enabled:
            schema["properties"].update(definitions["module_return_sections"].get(name, {}))
    return schema
