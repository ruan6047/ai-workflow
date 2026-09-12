"""驗證 core/card-schema.md §1／§3／§4、core/enums.md 值域、core/return.md schema 與 verbs.md §2 D3。"""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from wf.compose.blocks import Block, Catalog, load_blocks
from wf.compose.schema import compose_schema, materialize
from wf.compose.validate import SUPPORTED_KEYWORDS, validate

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def catalog():
    return load_blocks(ROOT)


@pytest.fixture
def card():
    return {
        "schema_version": 2, "card_id": "WF-001", "source_issue": 1, "feature": "",
        "core_pain": "", "non_scope": [], "stage_plan": [], "stage": "需求", "state": "待辦",
        "list_convergence": [], "service_goal": "", "tier": None, "tier_basis": None,
        "exec_capability": None, "review_capability": None, "db_scope": None, "resources": [],
        "when": "", "spec_version": 1, "iteration": 0, "acceptance": [], "verification": [],
        "parent": None, "blocked": None, "grilling": None, "owner": None, "branch": None,
        "source_sha": None, "notes": [],
    }


def refs(node, path=()):
    if isinstance(node, dict):
        if str(node.get("$ref", "")).startswith("wf-enums#/"):
            yield path, node["$ref"]
        for key, value in node.items():
            yield from refs(value, path + (key,))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from refs(value, path + (index,))


def test_enum_refs_match_original_file_slices(catalog):
    text = (ROOT / "core/enums.md").read_text()
    start = text.index("\n", text.index("```json wf-enums")) + 1
    enums = json.loads(text[start:text.index("```", start)])
    original = catalog.schemas["wf-card"].data
    composed = materialize(original, catalog)
    found = list(refs(original))
    assert found
    for path, ref in found:
        actual = composed
        for key in path:
            actual = actual[key]
        key = ref.split("/", 1)[1]
        assert actual == enums[key]
        # 比對原件每一個 enum 陣列切片，保留值、順序與 Unicode 字面。
        line = next(line for line in text.splitlines() if line.lstrip().startswith('"' + key + '"'))
        raw_array = line[line.index("["):line.rindex("]") + 1]
        assert json.dumps(actual["enum"], ensure_ascii=False) == raw_array
        print("ENUM_REF", "/" + "/".join(map(str, path)), ref, raw_array)
    assert not list(refs(composed))
    print("ENUM_REF_COUNT", len(found))


@pytest.mark.parametrize("name,state", [("fake", "X"), ("escalation", "升級")])
def test_only_enabled_module_states_pass(catalog, card, name, state):
    if name == "fake":
        source = catalog.blocks[0].source
        module = {"name": name, "adds": {"enums": {"states": [state]}, "fields": []}}
        catalog = Catalog(catalog.blocks + [Block("yaml wf-module", module, "", source)], catalog.schemas)
    snapshot = deepcopy(catalog)
    card["state"] = state
    assert validate(card, compose_schema(catalog, "wf-card", [name])) == []
    errors = validate(card, compose_schema(catalog, "wf-card"))
    assert any(e.path == "/state" for e in errors)
    card["state"] = "阻塞"
    card["blocked"] = {"from": state, "ruling": None}
    assert validate(card, compose_schema(catalog, "wf-card", [name])) == []
    assert any(e.path == "/blocked/from" for e in validate(card, compose_schema(catalog, "wf-card")))
    assert catalog == snapshot


@pytest.mark.parametrize("enabled", [[], ["initiative"], ["escalation", "initiative"]])
def test_declared_fields_remain_legal_unknown_keys_rejected(catalog, card, enabled):
    schema = compose_schema(catalog, "wf-card", enabled)
    card["parent_spec_version"] = 1
    assert validate(card, schema) == []
    card["foo"] = "not declared"
    assert [(e.path, e.keyword) for e in validate(card, schema)] == [("/foo", "additionalProperties")]


@pytest.mark.parametrize("patch,path,keyword", [
    ({"tier": "T9"}, "/tier", "anyOf"),
    ({"db_scope": None}, None, None),
    ({"state": "升級"}, "/state", "anyOf"),
    ({"owner": {"role": "pm2", "actor": "a"}}, "/owner/role", "enum"),
    ({"schema_version": 1}, "/schema_version", "const"),
    ({"notes": [{"id": "bad", "text": "", "origin": ""}]}, "/notes/0/id", "pattern"),
])
def test_d3_negative_controls(catalog, card, patch, path, keyword):
    schema = compose_schema(catalog, "wf-card")
    assert validate(card, schema) == []
    card.update(patch)
    errors = validate(card, schema)
    assert [(error.path, error.keyword) for error in errors] == ([] if path is None else [(path, keyword)])
    print("D3", json.dumps(patch, ensure_ascii=False), errors)


def schema_keywords(node):
    """只走 schema 位置；兩個 module_* 定義是 properties 映射，非 schema。"""
    found = set(node)
    for key, value in node.items():
        if key == "properties":
            for child in value.values():
                found |= schema_keywords(child)
        elif key == "$defs":
            for name, child in value.items():
                if name in {"module_fields", "module_return_sections"}:
                    for fields in child.values():
                        for field in fields.values():
                            found |= schema_keywords(field)
                else:
                    found |= schema_keywords(child)
        elif key in {"items", "additionalProperties"} and isinstance(value, dict):
            found |= schema_keywords(value)
        elif key == "anyOf":
            for child in value:
                found |= schema_keywords(child)
    return found


def test_schema_keyword_inventory_and_negative_control(catalog):
    used = set()
    for identifier, block in catalog.schemas.items():
        keywords = schema_keywords(block.data)
        used |= keywords
        print("SCHEMA_KEYWORDS", identifier, sorted(keywords))
    assert used <= SUPPORTED_KEYWORDS
    mutated = deepcopy(catalog.schemas["wf-card"].data)
    mutated["properties"]["new"] = {"maxLength": 3}
    extra = schema_keywords(mutated) - SUPPORTED_KEYWORDS
    assert extra == {"maxLength"}
    with pytest.raises(AssertionError):
        assert schema_keywords(mutated) <= SUPPORTED_KEYWORDS
    print("KEYWORD_NEGATIVE_CONTROL", sorted(extra))
    print("SCHEMA_COUNT", len(catalog.schemas), "KEYWORDS", sorted(used))


def test_return_sections_enabled_only_and_no_required_added(catalog):
    raw = catalog.schemas["wf-return"].data
    for name, fields in raw["$defs"]["module_return_sections"].items():
        schema = compose_schema(catalog, "wf-return", [name])
        assert all(schema["properties"][key] == value for key, value in fields.items())
        assert not (fields.keys() & compose_schema(catalog, "wf-return")["properties"].keys())
        assert schema["required"] == raw["required"]
        print("RETURN_SECTIONS", name, list(fields))
    value = {"card_id": "WF-001", "iteration": 1, "role": "executor", "source_sha": "a" * 40,
             "conclusion": {"verdict": "可判定"}}
    assert validate(value, compose_schema(catalog, "wf-return", ["research"])) == []
    assert validate(value, compose_schema(catalog, "wf-return"))[0].path == "/conclusion"


@pytest.mark.parametrize("schema,good,bad,keyword", [
    ({"type": "integer"}, 1.0, True, "type"),
    ({"type": "number"}, 2.5, False, "type"),
    ({"type": "boolean"}, False, 0, "type"),
    ({"const": 1}, 1.0, True, "const"),
    ({"enum": [{"x": [1]}]}, {"x": [1.0]}, {"x": [True]}, "enum"),
    ({"type": "array", "uniqueItems": True}, [True, 1], [{"x": 1}, {"x": 1.0}], "uniqueItems"),
    ({"minimum": 1}, 1, 0, "minimum"),
    ({"minLength": 1}, "字", "", "minLength"),
    ({"required": ["a"]}, {"a": 0}, {}, "required"),
    ({"items": {"type": "string"}}, ["a"], [0], "type"),
    ({"pattern": "b"}, "abc", "xyz", "pattern"),
])
def test_keyword_semantics(schema, good, bad, keyword):
    assert validate(good, schema) == []
    assert any(error.keyword == keyword for error in validate(bad, schema))


def test_local_pointer_escaping_siblings_and_format_annotations():
    schema = {"$defs": {"a/b~c": {"type": "string"}},
              "properties": {"a/b~c": {"$ref": "#/$defs/a~1b~0c", "minLength": 1, "format": "uri"}}}
    assert validate({"a/b~c": ""}, schema)[0].path == "/a~1b~0c"
    assert validate({"a/b~c": 0}, schema)[0].keyword == "type"
    annotations = []
    assert validate({"a/b~c": "not a uri"}, schema, formats=annotations) == []
    assert annotations == [("/a~1b~0c", "uri")]
    with pytest.raises(ValueError, match="ref"):
        validate({}, {"$ref": "https://example.invalid/schema"})


def test_all_declared_card_fields_from_original(catalog):
    schema = compose_schema(catalog, "wf-card")
    definitions = catalog.schemas["wf-card"].data["$defs"]["module_fields"]
    for block in catalog.by_label("yaml wf-module"):
        module = block.data
        fields = definitions.get(module["name"], {})
        assert set(module["adds"]["fields"]) == set(fields)
        assert all(schema["properties"][key] == value for key, value in fields.items())
        print("CARD_FIELDS", module["name"], list(fields))


# A2：§4 wf-note 與 §1 notes.items 是同一份契約；兩處都從 load_blocks 讀出後比較，⛔ 不重打常數。
def test_wf_note_three_key_contract_and_id_pattern_equals_notes_items(catalog):
    note = catalog.schemas["wf-note"].data
    items = catalog.schemas["wf-card"].data["properties"]["notes"]["items"]
    assert note["additionalProperties"] is False
    assert note["required"] == items["required"] == ["id", "text", "origin"]
    assert set(note["properties"]) == {"id", "text", "origin"}
    assert "schema_version" not in note["properties"]
    assert note["properties"]["id"]["pattern"] == items["properties"]["id"]["pattern"]
    assert note["properties"]["text"]["minLength"] == 1
    assert note["properties"]["origin"]["format"] == "uri"
    schema = compose_schema(catalog, "wf-note")
    good = {"id": "T-執行-01", "text": "逐字", "origin": "https://example.invalid/1"}
    assert validate(good, schema) == []
    cases = [({"id": "bad"}, ("/id", "pattern")), ({"text": ""}, ("/text", "minLength")),
             ({"extra": 1}, ("/extra", "additionalProperties"))]
    for patch, expected in cases:
        assert [(e.path, e.keyword) for e in validate(good | patch, schema)] == [expected]
    for key in good:
        missing = {k: v for k, v in good.items() if k != key}
        assert [(e.path, e.keyword) for e in validate(missing, schema)] == [("/" + key, "required")]
    print("WF_NOTE_ID_PATTERN", note["properties"]["id"]["pattern"])
