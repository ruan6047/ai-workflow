"""驗證 core/state-machine.md §1–4、core/enums.md 值域、card-schema.md §1、verbs.md §2 D1。

modules/{escalation,research,maintenance}/module.md §0；reachability.py 僅為等價對照。
"""
import ast
from copy import deepcopy
import importlib.util
from itertools import combinations
from pathlib import Path

import pytest

from wf.compose.blocks import Catalog, require_blocks
from wf.compose import transitions as subject

ROOT = Path(__file__).resolve().parents[2]
PLAN = ["需求", "執行", "審核", "結案"]


@pytest.fixture
def catalog():
    return Catalog([
        *require_blocks(ROOT, "core/state-machine.md", "json wf-state-machine"),
        *require_blocks(ROOT, "core/enums.md", "json wf-enums"),
    ], {})


@pytest.fixture
def oracle():
    spec = importlib.util.spec_from_file_location(
        "s04_reachability", ROOT / ".github/scripts/reachability.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def module(name):
    return require_blocks(ROOT, f"modules/{name}/module.md", "yaml wf-module")[0].data


def with_rows(catalog, rows):
    result = deepcopy(catalog)
    result.blocks[0].data["transitions"] = rows
    return result


def assert_same(actual, expected, case=""):
    assert actual == expected, case


def test_equivalence_matrix(catalog, oracle):
    sm = oracle.load()
    plans = oracle.legal_plans(sm)
    cases = oracle.module_cases(oracle.delta_modules(oracle.load_modules()))
    edge_equal = universe_equal = count = 0
    for label, mods in cases:
        for plan in plans:
            active = [m for m in mods
                      if all(s in plan for s in m.get("adds", {}).get("stages", []))]
            expected = oracle.compose(sm, active)
            edges = subject.expand(plan, active, catalog=catalog)
            nodes = subject.universe(plan, active, catalog=catalog)
            assert_same(edges, oracle.expand(expected, plan), (label, plan, "edges"))
            assert_same(nodes, oracle.universe(expected, plan), (label, plan, "universe"))
            count += 1
            edge_equal += 1
            universe_equal += 1
    assert count == len(plans) * len(cases) == 128
    print(f"MATRIX plans={len(plans)} module_cases={len(cases)} cases={count} "
          f"edges_equal={edge_equal} universe_equal={universe_equal}")


def test_equivalence_negative_controls(catalog, oracle):
    expected = oracle.expand(oracle.load(), PLAN)
    broken = deepcopy(expected)
    broken["需求/待辦"].remove("需求/進行中")
    with pytest.raises(AssertionError):
        assert_same(subject.expand(PLAN, [], catalog=catalog), broken)
    nodes = oracle.universe(oracle.load(), PLAN) - {"清單"}
    with pytest.raises(AssertionError):
        assert_same(subject.universe(PLAN, [], catalog=catalog), nodes)
    print("NEGATIVE_CONTROL removed_edge=detected removed_node=detected")


@pytest.mark.parametrize("token,includes_close", [("*", False), ("**", True)])
def test_stage_wildcards(catalog, token, includes_close):
    rules = with_rows(catalog, [{"from": f"{token}/待確認", "to": "same/退回"}])
    edges = subject.expand(PLAN, [], catalog=rules)
    assert ("結案/退回" in edges.get("結案/待確認", set())) is includes_close
    assert "執行/退回" in edges["執行/待確認"]


def test_next_skips_close_and_last_enters_close(catalog):
    edges = subject.expand(PLAN, [], catalog=catalog)
    assert "執行/待辦" in edges["需求/待確認"]
    assert "結案/待辦" not in edges["審核/待確認"]
    assert "結案/待確認" in edges["審核/待確認"]
    assert "結案/待確認" not in edges["執行/待確認"]


@pytest.mark.parametrize("name,stage,state", [
    ("escalation", "執行", "升級"), ("research", "研究", "不可判定"),
    ("maintenance", "維護", "運行中"),
])
def test_nonterminal_includes_module_states_and_from_is_exact(catalog, name, stage, state):
    plan = subject.legal_plans(catalog=catalog)[-1]
    edges = subject.expand(plan, [module(name)], catalog=catalog)
    blocked = subject.blocked_node(stage, state)
    assert blocked == f"{stage}/阻塞←{state}"
    assert blocked in edges[f"{stage}/{state}"]
    assert edges[blocked] == {f"{stage}/{state}"}
    assert f"{stage}/待辦" not in edges[blocked]
    assert f"{stage}/{state}" not in subject.universe(plan, [], catalog=catalog)


@pytest.mark.parametrize("has_planning", [False, True])
def test_if_filters_false_rows(catalog, has_planning):
    plan = ["需求", "規劃", "執行", "審核", "結案"] if has_planning else PLAN
    edges = subject.expand(plan, [], catalog=catalog)
    target = "規劃/退回" if has_planning else "需求/退回"
    other = "需求/退回" if has_planning else "規劃/退回"
    assert target in edges["審核/待確認"]
    assert other not in edges["審核/待確認"]


def test_list_node(catalog):
    edges = subject.expand(PLAN, [], catalog=catalog)
    assert edges["清單"] == {"需求/待辦"}
    assert "清單" in edges["需求/待確認"]
    assert "清單" in subject.universe(PLAN, [], catalog=catalog)


def test_legal_plans_from_artifact_powerset(catalog, oracle):
    sm = oracle.load()
    optional = set(sm["stages"]) - set(sm["required_stages"])
    plans = subject.legal_plans(catalog=catalog)
    expected = {tuple(s for s in sm["stages"] if s in sm["required_stages"] or s in subset)
                for r in range(len(optional) + 1) for subset in combinations(optional, r)}
    assert {tuple(p) for p in plans} == expected
    assert plans == oracle.legal_plans(sm)
    assert len(plans) == 2 ** len(optional) == 16
    print(f"PLANS optional={len(optional)} computed={2 ** len(optional)} actual={len(plans)}")


def test_empty_plan_unfilled_and_reachable(catalog):
    assert subject.is_legal_plan([], catalog=catalog) is True
    assert subject.is_legal_plan(PLAN, catalog=catalog) is True
    edges = subject.expand([], [], catalog=catalog)
    assert edges.plan_unfilled is True
    assert subject.expand(PLAN, [], catalog=catalog).plan_unfilled is False
    expected = {"清單", "需求/待辦", "需求/進行中", "需求/待確認", "需求/退回",
                "需求/阻塞←待辦", "需求/阻塞←進行中", "需求/阻塞←待確認", "需求/阻塞←退回"}
    assert subject.universe([], [], catalog=catalog) == set(edges) == expected
    assert set().union(*edges.values()) == expected
    reached, pending = set(), [catalog.blocks[0].data["initial"]]
    while pending:
        node = pending.pop()
        if node not in reached:
            reached.add(node)
            pending.extend(edges.get(node, ()))
    assert reached == expected
    print(f"EMPTY_PLAN unfilled={edges.plan_unfilled} nodes={sorted(expected)} reachable={sorted(reached)}")


@pytest.mark.parametrize("plan", [["執行", "需求", "審核", "結案"],
                                  ["需求", "執行", "結案"],
                                  ["需求", "需求", "執行", "審核", "結案"],
                                  ["需求", "未知", "執行", "審核", "結案"]])
def test_invalid_plans_rejected(catalog, plan):
    assert subject.is_legal_plan(plan, catalog=catalog) is False
    for fn in (subject.expand, subject.universe):
        with pytest.raises(ValueError, match="stage_plan"):
            fn(plan, [], catalog=catalog)


def test_legal_move_true(catalog):
    edges = subject.expand(PLAN, [], catalog=catalog)
    assert subject.is_legal_move("需求/待辦", "需求/進行中", edges)


def test_terminal_outgoing_false_even_if_injected(catalog):
    edges = subject.expand(PLAN, [], catalog=catalog)
    for terminal in catalog.blocks[1].data["states_terminal"]["enum"]:
        node = f"結案/{terminal}"
        assert not edges.get(node)
        edges[node] = {"需求/待辦"}
        assert not subject.is_legal_move(node, "需求/待辦", edges)


def test_missing_move_false(catalog):
    edges = subject.expand(PLAN, [], catalog=catalog)
    assert not subject.is_legal_move("需求/待辦", "結案/完成", edges)
    assert not subject.is_legal_move("不存在", "需求/待辦", edges)


def test_condition_retained_verbatim_and_never_evaluated(catalog):
    rows = [{"from": "需求/待辦", "to": "same/進行中", "condition": text}
            for text in ("不成立也只印\n逐字", "plan_lacks:需求")]
    edges = subject.expand(PLAN, [], catalog=with_rows(catalog, rows))
    assert edges["需求/待辦"] == {"需求/進行中"}
    assert edges.conditions[("需求/待辦", "需求/進行中")] == [r["condition"] for r in rows]


def test_union_then_remove_is_order_independent_and_exact(catalog):
    row = {"from": "需求/待辦", "to": "需求/進行中", "condition": "逐字"}
    kept = {**row, "condition": "另一條印字"}
    adding = {"adds": {"transitions": {"add": [row, kept]}}}
    removing = {"adds": {"transitions": {"remove": [row]}}}
    rules = with_rows(catalog, [])
    for mods in ([adding, removing], [removing, adding]):
        before = deepcopy(mods)
        edges = subject.expand(PLAN, mods, catalog=rules)
        assert edges.conditions[("需求/待辦", "需求/進行中")] == [kept["condition"]]
        assert mods == before
    assert rules.blocks[0].data["transitions"] == []


def test_runtime_reads_source_without_rule_cache(tmp_path, catalog):
    for block in catalog.blocks:
        target = tmp_path / block.source.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((ROOT / block.source.path).read_text(encoding="utf-8"), encoding="utf-8")
    assert len(subject.legal_plans(root=tmp_path)) == 16
    enums = tmp_path / "core/enums.md"
    enums.write_text(enums.read_text(encoding="utf-8").replace('"研究", ', ''), encoding="utf-8")
    assert len(subject.legal_plans(root=tmp_path)) == 8


def imports(text):
    return sorted({alias.name if isinstance(node, ast.Import) else
                   "." * node.level + (node.module or "") + "." + alias.name
                   for node in ast.walk(ast.parse(text))
                   if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names})


def assert_no_forbidden_imports(text):
    banned = {"subprocess", "urllib", "socket", "requests", "http", "os.system", "popen", "os.popen"}
    found = set(imports(text))
    aliases = {a.asname or a.name: a.name for n in ast.walk(ast.parse(text))
               if isinstance(n, ast.Import) for a in n.names}
    found.update(f"{aliases.get(n.value.id, n.value.id)}.{n.attr}"
                 for n in ast.walk(ast.parse(text))
                 if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name))
    assert not {name for name in found for bad in banned if name == bad or name.startswith(bad + ".")}


def test_compose_import_inventory():
    for sentinel in ("import subprocess", "from urllib import parse", "import socket",
                     "import requests", "from http import client", "from os import system",
                     "import os as o; o.system('sentinel')", "import popen", "from os import popen",
                     "import os; os.popen('sentinel')"):
        with pytest.raises(AssertionError):
            assert_no_forbidden_imports(sentinel)
        print(f"NEGATIVE_CONTROL sentinel={sentinel!r} detected")
    assert_no_forbidden_imports("import copy\nfrom pathlib import Path")
    paths = sorted((ROOT / "cli/src/wf/compose").rglob("*.py"))
    for path in paths:
        found = imports(path.read_text(encoding="utf-8"))
        print(f"IMPORTS {path.relative_to(ROOT)} {found}")
        assert_no_forbidden_imports(path.read_text(encoding="utf-8"))
    print(f"IMPORT_FILES scanned={len(paths)} population={len(paths)}")
