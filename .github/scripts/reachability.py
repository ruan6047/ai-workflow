#!/usr/bin/env python3
"""轉移表可達性測試（骨架 §四；core/state-machine.md §5）。

讀 core/state-machine.md 的 `json wf-state-machine` 區塊，對每個合法 stage_plan 展開合成表，斷言：
1. 合成表定義集合（階段計畫 × 狀態值域 ∪ 清單）內每個非終態有出邊，且可達 完成 或 停止；
2. 完成 與 停止 的出邊集合為空。
模組案例（第 4a 步起）：讀 modules/*/module.md 的 `yaml wf-module` 區塊（JSON 子集），對每個帶
transitions／states delta 的模組跑「單獨啟用」，再跑「全部啟用」；卡級模組只在含該階段的計畫上啟用。
"""
from __future__ import annotations

import glob
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


MODBLOCK = re.compile(r"```yaml wf-module\n(.*?)\n```", re.S)


def load_modules() -> list[dict]:
    mods = []
    for f in sorted(glob.glob(str(ROOT / "modules/*/module.md"))):
        m = MODBLOCK.search(Path(f).read_text(encoding="utf-8"))
        if not m:
            sys.exit(f"⛔ {f} 沒有 yaml wf-module 區塊")
        mods.append(json.loads(m.group(1)))
    return mods


NOTE_ID = re.compile(r"^- ([^：\s]+)：", re.M)  # §2 每條起首的 id，形狀另驗，⛔ 不因不合形狀而漏抓


def notes_errors(name: str, declared: list, body: str) -> list[str]:
    """§0 adds.notes 與 §2 條列 id 的對帳：只比 id 集合、順序與前綴，⛔ 不讀條文內容。"""
    sec = body.split("## 2 · 注意事項", 1)
    listed = NOTE_ID.findall(sec[1]) if len(sec) == 2 else []
    errs = []
    if declared != listed:
        errs.append(f"{name}: adds.notes={declared} ≠ §2 條列={listed}")
    shape = re.compile(rf"^F-{re.escape(name)}-\d{{2}}$")
    for i in declared + [x for x in listed if x not in declared]:
        if not shape.match(i):
            errs.append(f"{name}: id {i} 不是 F-{name}-NN 形狀")
    return errs


HANDOFF = ROOT / "core/handoff.md"
SCHEMA_BLOCK = re.compile(r"```json schema\n(.*?)```", re.S)
SECTIONS_BLOCK = re.compile(r"```json wf-module-sections\n(.*?)```", re.S)


def handoff_labels(text: str) -> tuple[dict[str, set[str]], dict[str, set[str]], list[str]]:
    """core/handoff.md 內模組段名：交回單（wf-return $defs.module_return_sections 的 label）與派工單／裁定單（wf-module-sections）分開收。"""
    ret: dict[str, set[str]] = {}
    other: dict[str, set[str]] = {}
    errs: list[str] = []
    for blk in SCHEMA_BLOCK.findall(text):
        d = json.loads(blk)
        if d.get("$id") != "wf-return":
            continue
        for mod, secs in d.get("$defs", {}).get("module_return_sections", {}).items():
            for key, v in secs.items():
                lab = v.get("label")
                if not lab:
                    errs.append(f"{mod}: $defs 段 {key} 缺 label")
                    continue
                if lab in ret.get(mod, set()):
                    errs.append(f"{mod}: $defs label 重複 {lab}")
                ret.setdefault(mod, set()).add(lab)
    m = SECTIONS_BLOCK.search(text)
    if m:
        for doc in json.loads(m.group(1)).values():
            for mod, labels in doc.items():
                other.setdefault(mod, set()).update(labels)
    return ret, other, errs


def sections_errors(name: str, declared: list, ret: dict[str, set[str]], other: dict[str, set[str]]) -> list[str]:
    """模組 adds.handoff_sections 與 handoff.md 段名的對帳：只比字串集合與歸屬，⛔ 不讀段內容。"""
    want = set(declared)
    r, o = ret.get(name, set()), other.get(name, set())
    errs = []
    if want - (r | o):
        errs.append(f"{name}: handoff_sections {sorted(want - (r | o))} 在 core/handoff.md 無對應段名")
    if (r | o) - want:
        errs.append(f"{name}: core/handoff.md 段名 {sorted((r | o) - want)} 未在模組宣告")
    if r & o:
        errs.append(f"{name}: 段名 {sorted(r & o)} 同時在交回單與派工單／裁定單")
    return errs


def orphan_errors(ret: dict[str, set[str]], other: dict[str, set[str]], names: set[str]) -> list[str]:
    """core/handoff.md 提到、但 modules/ 沒有的模組名。"""
    return [f"core/handoff.md 段名指向不存在的模組 {m}" for m in sorted((set(ret) | set(other)) - names)]


def check_module_sections() -> list[str]:
    ret, other, errs = handoff_labels(HANDOFF.read_text(encoding="utf-8"))
    names: set[str] = set()
    for f in sorted(glob.glob(str(ROOT / "modules/*/module.md"))):
        m = MODBLOCK.search(Path(f).read_text(encoding="utf-8"))
        if not m:
            continue
        d = json.loads(m.group(1))
        names.add(d["name"])
        adds = d.get("adds", {})
        errs += sections_errors(d["name"], adds.get("handoff_sections", []), ret, other)
        for c in adds.get("counters", []):
            if c not in adds.get("fields", []):
                errs.append(f"{d['name']}: counters {c} 不在 adds.fields")
    return errs + orphan_errors(ret, other, names)


def check_module_notes() -> list[str]:
    errs = []
    for f in sorted(glob.glob(str(ROOT / "modules/*/module.md"))):
        body = Path(f).read_text(encoding="utf-8")
        m = MODBLOCK.search(body)
        if not m:
            continue  # load_modules 已擋
        d = json.loads(m.group(1))
        errs += notes_errors(d["name"], d.get("adds", {}).get("notes", []), body)
    return errs


def compose(sm: dict, mods: list[dict]) -> dict:
    """核心 ∪ add − remove；模組加的狀態進 states，only_in_stage 由該模組 transitions 所及的階段決定。"""
    import copy
    out = copy.deepcopy(sm)
    out.setdefault("module_states", {})
    for m in mods:
        adds = m.get("adds", {})
        tr = adds.get("transitions", {})
        for st in adds.get("states", []):
            if st not in out["states"]:
                out["states"].append(st)
            stages = set()
            for t in tr.get("add", []):
                for side in (t["from"], t["to"]):
                    stage_tok, _, state = side.partition("/")
                    if state == st:
                        stages.add(stage_tok)
            out["module_states"][st] = stages  # 記法 token：'*'、'**'、'same' 或字面階段
        out["transitions"] = [t for t in out["transitions"] if t not in tr.get("remove", [])] + list(tr.get("add", []))
    return out


def legal_plans(sm: dict) -> list[list[str]]:
    optional = [s for s in sm["stages"] if s not in sm["required_stages"]]
    plans = []
    for r in range(len(optional) + 1):
        for chosen in itertools.combinations(optional, r):
            plans.append([s for s in sm["stages"] if s in sm["required_stages"] or s in chosen])
    return plans


def states_of(sm: dict, stage: str) -> list[str]:
    only = sm.get("only_in_stage", {})
    delta = sm.get("stage_delta", {}).get(stage, {})
    scoped = sm.get("module_states", {})
    core = []
    for s in sm["states"]:
        if only.get(s, stage) != stage or s in delta.get("states_remove", []):
            continue
        if s in scoped:
            toks = scoped[s]
            if not (stage in toks or "**" in toks or ("*" in toks and stage != "結案") or ("same" in toks and stage != "結案")):
                continue
        core.append(s)
    return core + delta.get("states_add", [])


def blocked_node(stage: str, frm: str) -> str:
    """阻塞節點保留確切 blocked.from：每個非終態各一個。"""
    return f"{stage}/阻塞←{frm}"


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

    def holds(cond: str | None) -> bool:
        if not cond:
            return True
        op, stage = cond.split(":", 1)
        if op not in ("plan_has", "plan_lacks"):
            sys.exit(f"⛔ 未知的 if 運算子：{cond}")
        return (stage in plan) if op == "plan_has" else (stage not in plan)

    for t in sm["transitions"]:
        f, to = t["from"], t["to"]
        if not holds(t.get("if")):
            continue
        if f == "清單":
            edges["清單"].add(to)
            continue
        f_stage, f_states = f.split("/", 1)
        for fs in from_stages(f_stage):
            for st in f_states.split("|"):
                if st not in states_of(sm, fs):
                    continue
                t_stage_tok, t_state = to.split("/", 1) if to != "清單" else ("清單", "")
                if st == "阻塞":
                    # 解除：每個阻塞節點只回自己的 from；阻塞不得有其他出邊
                    if t_state != "<from>":
                        sys.exit(f"⛔ 阻塞的出邊只能是 same/<from>：{t}")
                    for frm in states_of(sm, fs):
                        if frm not in sm["terminal"] and frm != "阻塞":
                            edges[blocked_node(fs, frm)].add(f"{fs}/{frm}")
                    continue
                src = f"{fs}/{st}"
                if to == "清單":
                    edges[src].add("清單")
                    continue
                ts = to_stage(t_stage_tok, fs)
                if ts is None:
                    continue
                if t_state == "阻塞":
                    edges[src].add(blocked_node(ts, st))
                elif t_state in states_of(sm, ts):
                    edges[src].add(f"{ts}/{t_state}")
    return edges


def universe(sm: dict, plan: list[str]) -> set[str]:
    nodes: set[str] = set()
    for st in plan:
        ss = states_of(sm, st)
        for s in ss:
            if s == "阻塞":
                nodes.update(blocked_node(st, frm) for frm in ss if frm not in sm["terminal"] and frm != "阻塞")
            else:
                nodes.add(f"{st}/{s}")
    nodes.add("清單")
    return nodes


def check(sm: dict, plan: list[str]) -> list[str]:
    edges = expand(sm, plan)
    terminal = {f"結案/{s}" for s in sm["terminal"]}
    errors = []
    # 終態出邊：對全部節點檢查，不依可達性
    for n, outs in edges.items():
        if n in terminal and outs:
            errors.append(f"終態 {n} 有出邊 {sorted(outs)}")
    # 反向可達終態
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
    for n in sorted(universe(sm, plan) - terminal):
        if not edges.get(n):
            errors.append(f"非終態 {n} 無出邊")
        elif n not in can_finish:
            errors.append(f"非終態 {n} 不可達結案")
    # initial 必在定義集合內且可達結案
    if sm["initial"] not in can_finish:
        errors.append(f"initial {sm['initial']} 不可達結案")
    return errors


def selftest(sm: dict) -> int:
    """負控四件：砍終態邊；終態帶出邊；孤立非終態；只有阻塞往返的狀態。皆必 FAIL。"""
    import copy
    plan = [s for s in sm["stages"] if s in sm["required_stages"]]
    bad = 0
    b1 = copy.deepcopy(sm)
    b1["transitions"] = [t for t in b1["transitions"] if not t["to"].startswith("結案/完成") and not t["to"].startswith("結案/停止")]
    e1 = check(b1, plan); ok1 = any("不可達結案" in e or "無出邊" in e for e in e1)
    b2 = copy.deepcopy(sm)
    b2["transitions"].append({"from": "結案/停止", "to": "結案/待確認", "condition": "負控：終態出邊"})
    e2 = check(b2, plan); ok2 = any(e.startswith("終態 結案/停止 有出邊") for e in e2)
    b3 = copy.deepcopy(sm)
    b3["states"] = b3["states"] + ["孤立"]
    e3 = check(b3, plan); ok3 = any("非終態 需求/孤立 無出邊" in e for e in e3)
    # 只有 阻塞 往返、無其他出邊的狀態：必 FAIL（第 1 步審核 R3-01 的假陽性）
    b4 = copy.deepcopy(sm)
    b4["states"] = b4["states"] + ["孤島"]
    b4["transitions"].append({"from": "**/孤島", "to": "same/阻塞", "condition": "負控"})
    e4 = check(b4, plan); ok4 = any("非終態 需求/孤島 不可達結案" in e for e in e4)
    # R1 退回目標唯一：含規劃的計畫不得有 需求/退回 邊；缺規劃的計畫不得有 規劃/退回 邊
    with_plan = [s for s in sm["stages"] if s in sm["required_stages"] or s == "規劃"]
    e_with = expand(sm, with_plan)
    ok5 = "需求/退回" not in e_with.get("審核/待確認", set()) and "規劃/退回" in e_with.get("審核/待確認", set())
    e_without = expand(sm, plan)
    ok6 = "規劃/退回" not in e_without.get("審核/待確認", set()) and "需求/退回" in e_without.get("審核/待確認", set())
    print(f"selftest_r1_return_target_unique: {'PASS' if (ok5 and ok6) else 'FAIL'}")
    bad += not (ok5 and ok6)
    # 模組負控：模組加的狀態只有進邊沒有出邊，必 FAIL；正控：research 的 不可判定 節點確實進了定義集合
    fake = {"name": "fake", "adds": {"states": ["孤模"], "transitions": {"add": [{"from": "執行/待確認", "to": "執行/孤模", "condition": "負控"}], "remove": []}}}
    e7 = check(compose(sm, [fake]), plan); ok7 = any("非終態 執行/孤模 無出邊" in e for e in e7)
    research = next((m for m in load_modules() if m["name"] == "research"), None)
    rplan = [s for s in sm["stages"] if s in sm["required_stages"] or s == "研究"]
    ok8 = bool(research) and "研究/不可判定" in universe(compose(sm, [research]), rplan) and not check(compose(sm, [research]), rplan)
    print(f"selftest_module_state_without_exit: {'PASS' if ok7 else 'FAIL'}")
    print(f"selftest_module_state_in_universe: {'PASS' if ok8 else 'FAIL'}")
    bad += (not ok7) + (not ok8)
    for name, ok, errs in (("broken_terminal_edges", ok1, e1), ("terminal_with_outedge", ok2, e2), ("isolated_nonterminal", ok3, e3), ("blocked_loop_only", ok4, e4)):
        print(f"selftest_{name}: {'PASS' if ok else 'FAIL'}（{len(errs)} 條錯誤）")
        bad += not ok
    good = "```yaml wf-module\n{}\n```\n## 2 · 注意事項\n\n- F-x-01：a。\n- F-x-02：b。\n"
    e_ok = notes_errors("x", ["F-x-01", "F-x-02"], good)
    e_missing = notes_errors("x", [], good)
    e_order = notes_errors("x", ["F-x-02", "F-x-01"], good)
    e_prefix = notes_errors("x", ["F-y-01", "F-x-02"], good.replace("F-x-01", "F-y-01"))
    e_shape = notes_errors("x", ["F-x-extra-01", "F-x-02"], good.replace("F-x-01", "F-x-extra-01"))
    e_listed_prefix = notes_errors("x", [], good.replace("F-x-01", "P-x-01").replace("F-x-02", "P-x-02"))
    e_listed_digits = notes_errors("x", [], good.replace("F-x-01", "F-x-1").replace("F-x-02", "F-x-2"))
    ok = (not e_ok and len(e_missing) == 1 and len(e_order) == 1 and len(e_prefix) == 1 and len(e_shape) == 1
          and e_listed_prefix and e_listed_digits)
    print(f"selftest_module_notes_consistency: {'PASS' if ok else 'FAIL'}（負控 6 條）")
    bad = bad or not ok
    ret, oth = {"m": {"A"}}, {"m": {"B"}}
    s_ok = sections_errors("m", ["A", "B"], ret, oth)
    s_missing = sections_errors("m", ["A", "B", "C"], ret, oth)
    s_extra = sections_errors("m", ["A"], ret, oth)
    s_none = sections_errors("z", ["A"], ret, oth)
    s_both = sections_errors("m", ["A", "B"], {"m": {"A", "B"}}, oth)
    _, _, lab_errs = handoff_labels('```json schema\n{"$id": "wf-return", "$defs": {"module_return_sections": {"m": {"k": {"type": "string"}}}}}\n```')
    s_orphan = orphan_errors({"ghost": {"A"}}, {}, {"m"})
    probe = [{"name": "rm-only", "adds": {"states": [], "transitions": {"add": [], "remove": [{"from": "需求/待辦", "to": "需求/進行中"}]}}}]
    is_delta = bool(probe[0]["adds"]["states"] or any(probe[0]["adds"]["transitions"].get(k) for k in ("add", "remove")))
    print(f"selftest_remove_only_module_is_delta: {'PASS' if is_delta else 'FAIL'}（負控 1 條）")
    bad = bad or not is_delta
    ok2 = (not s_ok and len(s_missing) == 1 and len(s_extra) == 1 and len(s_none) == 1 and len(s_both) == 1
           and len(lab_errs) == 1 and len(s_orphan) == 1)
    print(f"selftest_module_sections_consistency: {'PASS' if ok2 else 'FAIL'}（負控 6 條）")
    bad = bad or not ok2
    return 1 if bad else 0


def main() -> int:
    sm = load()
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest(sm)
    plans = legal_plans(sm)
    mods = load_modules()
    note_errs = check_module_notes()
    for e in note_errs:
        print(f"⛔ adds.notes 對帳：{e}")
    print(f"模組 adds.notes 對帳：{len(mods)} 檔，失敗 {len(note_errs)}")
    sec_errs = check_module_sections()
    for e in sec_errs:
        print(f"⛔ handoff_sections 對帳：{e}")
    print(f"模組 handoff_sections 對帳：{len(mods)} 檔，失敗 {len(sec_errs)}")
    note_errs += sec_errs
    delta_mods = [m for m in mods if m.get("adds", {}).get("states") or any(m.get("adds", {}).get("transitions", {}).get(k) for k in ("add", "remove"))]
    cases = []
    for r in range(len(delta_mods) + 1):
        for combo in itertools.combinations(delta_mods, r):
            label = "無模組" if not combo else "啟用 " + "+".join(m["name"] for m in combo)
            cases.append((label, list(combo)))
    total = bad = 0

    def enabled(m: dict, plan: list[str]) -> bool:
        stages = m.get("adds", {}).get("stages", [])
        return all(st in plan for st in stages)  # 卡級模組只在含該階段的計畫上存在

    for label, ms in cases:
        n = f = 0
        for plan in plans:
            active = [m for m in ms if enabled(m, plan)]
            errs = check(compose(sm, active), plan)
            n += 1
            if errs:
                f += 1
                print(f"FAIL [{label}] {'→'.join(plan)}")
                for e in errs:
                    print(f"  ⛔ {e}")
        print(f"[{label}] stage_plan 案例：{n}，失敗 {f}")
        total += n
        bad += f
    print(f"合計 {total} 案例，失敗 {bad}；模組 delta {len(delta_mods)} 個")
    return 1 if (bad or note_errs) else 0


if __name__ == "__main__":
    sys.exit(main())
