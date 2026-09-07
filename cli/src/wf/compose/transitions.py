"""消費 core/state-machine.md §1–4、core/enums.md「值域」、core/card-schema.md §1、
core/verbs.md §1 move／§2 D1、modules/{escalation,research,maintenance}/module.md §0。

enabled_modules 由呼叫端提供已啟用的宣告 dict；catalog 可沿用 S01 Catalog，
未提供時僅透過 S01 讀 root 下的狀態機與值域原件，不快取或判模組啟用。
"""
from collections.abc import Iterable
from itertools import combinations
from pathlib import Path

from .blocks import Catalog, MissingBlockError, require_blocks


class Edges(dict[str, set[str]]):
    """鄰接集合；conditions 保留每條具體邊的逐字印項。"""

    def __init__(self, terminal_nodes: set[str]):
        super().__init__()
        self.terminal_nodes = frozenset(terminal_nodes)
        self.conditions: dict[tuple[str, str], list[str]] = {}

    def add(self, source: str, target: str, row: dict) -> None:
        self.setdefault(source, set()).add(target)
        if "condition" in row:
            values = self.conditions.setdefault((source, target), [])
            if row["condition"] not in values:
                values.append(row["condition"])


def _documents(catalog: Catalog | None, root: Path | str) -> tuple[dict, dict]:
    result = []
    for path, label in (("core/state-machine.md", "json wf-state-machine"),
                        ("core/enums.md", "json wf-enums")):
        blocks = (require_blocks(root, path, label) if catalog is None else
                  [b for b in catalog.blocks if b.source.path == path and b.label == label])
        if not blocks:
            raise MissingBlockError(path, "", f"缺區塊 {label}")
        result.append(blocks[0].data)
    return result[0], result[1]


def _plans(sm: dict, enums: dict) -> list[list[str]]:
    stages = enums["stages"]["enum"]
    required = sm["required_stages"]
    optional = [s for s in stages if s not in required]
    return [[s for s in stages if s in required or s in chosen]
            for size in range(len(optional) + 1) for chosen in combinations(optional, size)]


def legal_plans(*, catalog: Catalog | None = None, root: Path | str = ".") -> list[list[str]]:
    return _plans(*_documents(catalog, root))


def is_legal_plan(plan: Iterable[str], *, catalog: Catalog | None = None,
                  root: Path | str = ".") -> bool:
    """core/state-machine.md §1；空值合法，未填事實由 expand().plan_unfilled 提供。"""
    plan = list(plan)
    return not plan or plan in legal_plans(catalog=catalog, root=root)


def blocked_node(stage: str, from_state: str) -> str:
    return f"{stage}/阻塞←{from_state}"


class _Machine:
    def __init__(self, plan: Iterable[str], modules: Iterable[dict],
                 catalog: Catalog | None, root: Path | str):
        self.sm, enums = _documents(catalog, root)
        self.plan = list(plan)
        if self.plan and self.plan not in _plans(self.sm, enums):
            raise ValueError("stage_plan 非空時必須為階段序子序列且含 required_stages")
        self.plan_unfilled = not self.plan  # 未填；印由動詞層處理。
        if self.plan_unfilled:
            self.plan = [self.sm["initial"].partition("/")[0]]
        self.close = enums["stages"]["enum"][-1]
        self.non_close = [s for s in self.plan if s != self.close]
        self.terminal = set(enums["states_terminal"]["enum"])
        self.blocked = enums["state_blocked"]["enum"][0]
        self.base = list(enums["states_core"]["enum"]) + [
            s for s in enums["states_terminal"]["enum"] if s in self.sm["only_in_stage"]
        ] + list(enums["state_blocked"]["enum"])
        self.scoped: dict[str, set[str]] = {}
        rows, removed = list(self.sm["transitions"]), []
        for module in modules:
            adds = module.get("adds", {})
            delta = adds.get("transitions", {})
            additions = delta.get("add", [])
            rows.extend(additions)
            removed.extend(delta.get("remove", []))
            for state in adds.get("enums", {}).get("states", []):
                if state not in self.base:
                    self.base.append(state)
                tokens = {side.partition("/")[0] for row in additions
                          for side in (row["from"], row["to"])
                          if side.partition("/")[2] == state}
                self.scoped.setdefault(state, set()).update(tokens)
        self.rows = []
        for row in rows:
            if row not in removed and row not in self.rows:
                self.rows.append(row)

    def states(self, stage: str) -> set[str]:
        delta = self.sm["stage_delta"].get(stage, {})
        states = set()
        for state in self.base:
            if self.sm["only_in_stage"].get(state, stage) != stage:
                continue
            if state in delta.get("states_remove", []):
                continue
            if state in self.scoped:
                tokens = self.scoped[state]
                if not (stage in tokens or "**" in tokens or
                        (stage != self.close and tokens & {"*", "same"})):
                    continue
            states.add(state)
        return states | set(delta.get("states_add", []))

    def nonterminal(self, stage: str) -> set[str]:
        return self.states(stage) - self.terminal - {self.blocked}

    def universe(self) -> set[str]:
        nodes = {"清單"}
        for stage in self.plan:
            nodes.update(f"{stage}/{s}" for s in self.states(stage) if s != self.blocked)
            if self.blocked in self.states(stage):
                nodes.update(blocked_node(stage, s) for s in self.nonterminal(stage))
        return nodes

    def holds(self, condition: str | None) -> bool:
        if not condition:
            return True
        op, stage = condition.split(":", 1)
        if op == "plan_has":
            return stage in self.plan
        if op == "plan_lacks":
            return stage not in self.plan
        raise ValueError(f"未知的 if 運算子：{condition}")

    def sources(self, token: str) -> list[str]:
        if token == "*":
            return self.non_close
        if token == "**":
            return self.plan
        if token == "last":
            return self.non_close[-1:]
        return [token] if token in self.plan else []

    def target_stage(self, token: str, stage: str) -> str | None:
        if token == "same":
            return stage
        if token == "next":
            remaining = self.plan[self.plan.index(stage) + 1:]
            return remaining[0] if remaining and remaining[0] != self.close else None
        return token if token in self.plan else None

    def expand(self) -> Edges:
        nodes = self.universe()
        edges = Edges({n for n in nodes if n.partition("/")[2] in self.terminal})
        edges.plan_unfilled = self.plan_unfilled
        for row in self.rows:
            if not self.holds(row.get("if")):
                continue
            source, target = row["from"], row["to"]
            if source == "清單":
                if target in nodes:
                    edges.add(source, target, row)
                continue
            stage_token, state_token = source.split("/", 1)
            for stage in self.sources(stage_token):
                states = (self.nonterminal(stage) if state_token == "<非終態>"
                          else {state_token})
                for state in sorted(states & self.states(stage) - self.terminal):
                    if state == self.blocked:
                        if target != "same/<from>":
                            raise ValueError("阻塞的出邊只能是 same/<from>")
                        for previous in sorted(self.nonterminal(stage)):
                            edges.add(blocked_node(stage, previous), f"{stage}/{previous}", row)
                        continue
                    source_node = f"{stage}/{state}"
                    if target == "清單":
                        edges.add(source_node, target, row)
                        continue
                    target_token, target_state = target.split("/", 1)
                    target_stage = self.target_stage(target_token, stage)
                    if target_stage is None:
                        continue
                    target_node = (blocked_node(target_stage, state)
                                   if target_state == self.blocked else
                                   f"{target_stage}/{target_state}")
                    if target_node in nodes:
                        edges.add(source_node, target_node, row)
        return edges


def expand(plan: Iterable[str], enabled_modules: Iterable[dict], *,
           catalog: Catalog | None = None, root: Path | str = ".") -> Edges:
    return _Machine(plan, enabled_modules, catalog, root).expand()


def universe(plan: Iterable[str], enabled_modules: Iterable[dict], *,
             catalog: Catalog | None = None, root: Path | str = ".") -> set[str]:
    return _Machine(plan, enabled_modules, catalog, root).universe()


def is_legal_move(from_node: str, to_node: str, edges: Edges) -> bool:
    return from_node not in edges.terminal_nodes and to_node in edges.get(from_node, ())
