"""消費 core/verbs.md §2 D3、core/card-schema.md §1／§3／§4，
core/dispatch.md、core/return.md、core/ruling.md 的 json schema；format 僅記錄。
"""
from dataclasses import dataclass
import re

SUPPORTED_KEYWORDS = frozenset((
    "type", "enum", "const", "required", "additionalProperties", "properties", "items",
    "uniqueItems", "pattern", "minimum", "minLength", "anyOf", "$ref", "format", "$defs",
    "$id", "label",  # 原件的識別字與段名註記，不限制資料。
))


@dataclass(frozen=True)
class ValidationError:
    path: str
    keyword: str
    message: str


def _pointer(path, key):
    return path + "/" + str(key).replace("~", "~0").replace("/", "~1")


def _equal(left, right):
    if isinstance(left, bool) != isinstance(right, bool):
        return False
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_equal(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_equal(a, b) for a, b in zip(left, right))
    return left == right


def validate(value, schema: dict, *, formats: list | None = None) -> list[ValidationError]:
    """回傳結構錯誤；path 為 JSON pointer（根為空字串），format 註記可另收集。"""
    formats = [] if formats is None else formats

    def visit(value, node, path, active=frozenset()):
        errors = []

        def fail(keyword, at=path):
            errors.append(ValidationError(at, keyword, f"不符合 {keyword}"))

        if "$ref" in node:
            ref = node["$ref"]
            if not ref.startswith("#/") or (ref, path) in active:
                raise ValueError(f"無法解析本地 $ref: {ref} at {path}")
            target = schema
            for part in ref[2:].split("/"):
                target = target[part.replace("~1", "/").replace("~0", "~")]
            errors.extend(visit(value, target, path, active | {(ref, path)}))
        if "format" in node:
            formats.append((path, node["format"]))
        if "type" in node:
            types = node["type"] if isinstance(node["type"], list) else [node["type"]]
            matches = {"null": value is None, "boolean": isinstance(value, bool),
                       "string": isinstance(value, str), "array": isinstance(value, list),
                       "object": isinstance(value, dict),
                       "integer": type(value) in (int, float) and value % 1 == 0,
                       "number": type(value) in (int, float)}
            if not any(matches[kind] for kind in types):
                fail("type")
        if "enum" in node and not any(_equal(value, item) for item in node["enum"]):
            fail("enum")
        if "const" in node and not _equal(value, node["const"]):
            fail("const")
        if "anyOf" in node:
            branches = [visit(value, branch, path, active) for branch in node["anyOf"]]
            if all(branches):
                fail("anyOf")
        if isinstance(value, dict):
            properties = node.get("properties", {})
            for key in node.get("required", []):
                if key not in value:
                    fail("required", _pointer(path, key))
            for key, item in value.items():
                at = _pointer(path, key)
                if key in properties:
                    errors.extend(visit(item, properties[key], at, active))
                elif node.get("additionalProperties") is False:
                    fail("additionalProperties", at)
        if isinstance(value, list):
            for index, item in enumerate(value):
                if "items" in node:
                    errors.extend(visit(item, node["items"], _pointer(path, index), active))
                if node.get("uniqueItems") and any(_equal(item, old) for old in value[:index]):
                    fail("uniqueItems", _pointer(path, index))
        if isinstance(value, str):
            if "pattern" in node and re.search(node["pattern"], value) is None:
                fail("pattern")
            if "minLength" in node and len(value) < node["minLength"]:
                fail("minLength")
        if type(value) in (int, float) and "minimum" in node and value < node["minimum"]:
            fail("minimum")
        return errors

    return visit(value, schema, "")
