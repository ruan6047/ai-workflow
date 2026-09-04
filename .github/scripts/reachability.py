#!/usr/bin/env python3
"""轉移表可達性測試（骨架 §四；core/state-machine.md §5）。

讀 core/state-machine.md 的 `json wf-state-machine` 區塊，對每個合法 stage_plan 展開合成表，斷言：
1. 每個從 initial 可達的非終態有出邊，且可達 完成 或 停止；
2. 完成 與 停止 的出邊集合為空。
模組 delta 的案例在第 4 步隨模組加入；本步只有無模組案例。
"""
import itertools
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BLOCK = re.compile(r"```json wf-state-machine\n(.*?)\n```", re.S)


def load() -> dict:
    text = (ROOT / "core/state-machine.md").read_text(encoding="utf-8")
    m = BLOCK.search(text)
    if not m:
        sys.exit("⛔ core/state-machine.md 沒有 json wf-state-machine 區塊")
    return json.loads(m.group(1))


def legal_plans(sm: dict) -> list[list[str]]:
    optional = [s for s in sm["stages"] if s not in sm["required_stages"]]
    plans = []
    for r in range(len(optional) + 1):
        for chosen in itertools.combinations(optional, r):
            plans.append([s for s in sm["stages"] if s in sm["required_stages"] or s in chosen])
    return plans


def states_of(sm: dict, stage: str) -> list[str]:
    return sm["states"] + sm.get("stage_delta", {}).get(stage, {}).get("states_add", [])


def expand(sm: dict, plan: list[str]) -> dict[str, set[str]]:
    """回傳 node -> set(node)。node 形狀 '階段/狀態' 或 '清單'。"""
    edges: dict[str, set[str]] = defaultdict(set)
    non_close = [s for s in plan if s != "結案"]
    last = non_close[-1]

    def from_stages(tok: str) -> list[str]:
        if tok == "*":
            return non_close
        if tok == "**":
            return plan
        if tok == "last":
            return [last]
        return [tok] if tok in plan else []

    def to_stage(tok: str, frm: str) -> str | None:
        if tok == "same":
            return frm
        if tok == "next":
            i = plan.index(frm)
            nxt = plan[i + 1] if i + 1 < len(plan) else None
            return None if nxt in (None, "結案") else nxt
        return tok if tok in plan else None

    for t in sm["transitions"]:
        f, to = t["from"], t["to"]
        if f == "清單":
            edges["清單"].add(to)
            continue
        f_stage, f_states = f.split("/", 1)
        for fs in from_stages(f_stage):
            for st in f_states.split("|"):
                if st not in states_of(sm, fs):
                    continue
                src = f"{fs}/{st}"
                if to == "清單":
                    edges[src].add("清單")
                    continue
                t_stage_tok, t_state = to.split("/", 1)
                ts = to_stage(t_stage_tok, fs)
                if ts is None:
                    continue
                if t_state == "<from>":
                    for back in states_of(sm, ts):
                        if back not in sm["terminal"] and back != "阻塞":
                            edges[src].add(f"{ts}/{back}")
                elif t_state in states_of(sm, ts):
                    edges[src].add(f"{ts}/{t_state}")
    return edges


def check(sm: dict, plan: list[str]) -> list[str]:
    edges = expand(sm, plan)
    terminal = {f"結案/{s}" for s in sm["terminal"]}
    errors = []
    # reachable from initial
    seen, stack = set(), [sm["initial"]]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack.extend(edges.get(n, ()))
    # reverse reachability to terminal
    rev: dict[str, set[str]] = defaultdict(set)
    for a, bs in edges.items():
        for b in bs:
            rev[b].add(a)
    can_finish, stack = set(), list(terminal)
    while stack:
        n = stack.pop()
        if n in can_finish:
            continue
        can_finish.add(n)
        stack.extend(rev.get(n, ()))
    for n in sorted(seen):
        if n in terminal:
            if edges.get(n):
                errors.append(f"終態 {n} 有出邊 {sorted(edges[n])}")
            continue
        if not edges.get(n):
            errors.append(f"非終態 {n} 無出邊")
        elif n not in can_finish:
            errors.append(f"非終態 {n} 不可達結案")
    return errors


def selftest(sm: dict) -> int:
    """負控：砍掉結案的兩條終態邊，必須 FAIL。"""
    import copy
    broken = copy.deepcopy(sm)
    broken["transitions"] = [t for t in broken["transitions"] if not t["to"].startswith("結案/完成") and not t["to"].startswith("結案/停止")]
    errs = check(broken, [s for s in sm["stages"] if s in sm["required_stages"]])
    ok = any("不可達結案" in e or "無出邊" in e for e in errs)
    print(f"selftest_broken_table: {'PASS' if ok else 'FAIL'}（{len(errs)} 條錯誤）")
    return 0 if ok else 1


def main() -> int:
    sm = load()
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest(sm)
    plans = legal_plans(sm)
    bad = 0
    for plan in plans:
        errs = check(sm, plan)
        tag = "→".join(plan)
        print(f"{'PASS' if not errs else 'FAIL'} {tag}")
        for e in errs:
            print(f"  ⛔ {e}")
        bad += bool(errs)
    print(f"stage_plan 案例：{len(plans)}，失敗 {bad}（無模組）")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
