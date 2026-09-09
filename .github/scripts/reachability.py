#!/usr/bin/env python3
"""轉移表可達性測試（core/state-machine.md §5）。

讀 core/state-machine.md 的 `json wf-state-machine` 區塊與 core/enums.md 的 `json wf-enums`（階段／狀態值域），對每個合法 stage_plan 展開合成表，斷言：
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


ENUMBLOCK = re.compile(r"```json wf-enums\n(.*?)\n```", re.S)


def load() -> dict:
    text = (ROOT / "core/state-machine.md").read_text(encoding="utf-8")
    m = BLOCK.search(text)
    if not m:
        sys.exit("⛔ core/state-machine.md 沒有 json wf-state-machine 區塊")
    sm = json.loads(m.group(1))
    e = ENUMBLOCK.search((ROOT / "core/enums.md").read_text(encoding="utf-8"))
    if not e:
        sys.exit("⛔ core/enums.md 沒有 json wf-enums 區塊")
    en = json.loads(e.group(1))
    # 值域住 core/enums.md：狀態機區塊只放轉移與 delta。基底 states 只含 only_in_stage 有登記的終態（完成）；停止 由結案的 stage_delta 加。
    sm["stages"] = en["stages"]["enum"]
    sm["terminal"] = en["states_terminal"]["enum"]
    base_terminal = [s for s in sm["terminal"] if s in sm.get("only_in_stage", {})]
    sm["states"] = en["states_core"]["enum"] + base_terminal + en["state_blocked"]["enum"]
    return sm


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


HANDOFF_FILES = [ROOT / "core/return.md", ROOT / "core/dispatch.md"]
SCHEMA_BLOCK = re.compile(r"```json schema\n(.*?)```", re.S)
SECTIONS_BLOCK = re.compile(r"```json wf-module-sections\n(.*?)```", re.S)


def handoff_labels(text: str) -> tuple[dict[str, set[str]], dict[str, set[str]], list[str]]:
    """core/return.md 與 core/dispatch.md 內模組段名：交回單（wf-return $defs.module_return_sections 的 label）與派工單／裁定單（wf-module-sections）分開收。"""
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
    """模組 adds.handoff_sections 與交接文件段名的對帳：只比字串集合與歸屬，⛔ 不讀段內容。"""
    want = set(declared)
    r, o = ret.get(name, set()), other.get(name, set())
    errs = []
    if want - (r | o):
        errs.append(f"{name}: handoff_sections {sorted(want - (r | o))} 在交接文件無對應段名")
    if (r | o) - want:
        errs.append(f"{name}: 交接文件段名 {sorted((r | o) - want)} 未在模組宣告")
    if r & o:
        errs.append(f"{name}: 段名 {sorted(r & o)} 同時在交回單與派工單／裁定單")
    return errs


def delta_modules(mods: list[dict]) -> list[dict]:
    """帶狀態或轉移 delta 的模組；`transitions.remove` 也算 delta。"""
    return [m for m in mods
            if m.get("adds", {}).get("enums", {}).get("states")
            or any(m.get("adds", {}).get("transitions", {}).get(k) for k in ("add", "remove"))]


def module_cases(delta_mods: list[dict]) -> list[tuple[str, list[dict]]]:
    """delta 模組的冪集；每個組合一個案例。"""
    out = []
    for r in range(len(delta_mods) + 1):
        for combo in itertools.combinations(delta_mods, r):
            label = "無模組" if not combo else "啟用 " + "+".join(m["name"] for m in combo)
            out.append((label, list(combo)))
    return out


def orphan_errors(ret: dict[str, set[str]], other: dict[str, set[str]], names: set[str]) -> list[str]:
    """交接文件提到、但 modules/ 沒有的模組名。"""
    return [f"交接文件段名指向不存在的模組 {m}" for m in sorted((set(ret) | set(other)) - names)]


def check_module_sections() -> list[str]:
    ret, other, errs = handoff_labels("\n".join(f.read_text(encoding="utf-8") for f in HANDOFF_FILES))
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
        for st in adds.get("enums", {}).get("states", []):
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

    def from_states(tok: str, stage: str) -> list[str]:
        """`<非終態>`＝該階段值域內除終態與 阻塞 外的每個狀態，含模組加的狀態。"""
        if tok == "<非終態>":
            return [s for s in states_of(sm, stage) if s not in sm["terminal"] and s != "阻塞"]
        return tok.split("|")

    for t in sm["transitions"]:
        f, to = t["from"], t["to"]
        if not holds(t.get("if")):
            continue
        if f == "清單":
            edges["清單"].add(to)
            continue
        f_stage, f_states = f.split("/", 1)
        for fs in from_stages(f_stage):
            for st in from_states(f_states, fs):
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


def unreachable(sm: dict, plan: list[str]) -> list[str]:
    """從 initial 正向走不到的節點；印用，⛔ 不擋（core/state-machine.md §5）。"""
    edges = expand(sm, plan)
    seen: set[str] = set()
    stack = [sm["initial"]]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack.extend(edges.get(n, ()))
    return sorted(universe(sm, plan) - seen)


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
    """負控四件：砍終態邊；終態帶出邊；孤立非終態；只有阻塞往返的狀態。皆必 FAIL。

    孤立狀態的診斷分類隨正式表而變——`**/<非終態>` 在時每個非終態都帶進阻塞出邊，落「不可達結案」；
    改回四值枚舉時模組狀態落「無出邊」。負控只驗 `check()` 有沒有捕捉到該節點，⛔ 不釘死是哪一種診斷，
    否則正式表的正向可達會經 `--selftest` 的 rc 間接擋 merge。
    「無出邊」仍活於阻塞節點與清單（砍解除邊 14 條、砍清單出邊 1 條，實測）。
    """
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
    e3 = check(b3, plan); ok3 = any(e.startswith("非終態 需求/孤立 ") for e in e3)
    # 只有 阻塞 往返、無其他出邊的狀態：必 FAIL（曾是假陽性來源）
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
    fake = {"name": "fake", "adds": {"enums": {"states": ["孤模"]}, "transitions": {"add": [{"from": "執行/待確認", "to": "執行/孤模", "condition": "負控"}], "remove": []}}}
    e7 = check(compose(sm, [fake]), plan); ok7 = any(e.startswith("非終態 執行/孤模 ") for e in e7)
    research = next((m for m in load_modules() if m["name"] == "research"), None)
    rplan = [s for s in sm["stages"] if s in sm["required_stages"] or s == "研究"]
    ok8 = bool(research) and "研究/不可判定" in universe(compose(sm, [research]), rplan) and not check(compose(sm, [research]), rplan)
    print(f"selftest_module_state_without_exit: {'PASS' if ok7 else 'FAIL'}")
    print(f"selftest_module_state_in_universe: {'PASS' if ok8 else 'FAIL'}")
    bad += (not ok7) + (not ok8)
    # 負控：進阻塞邊改回四值枚舉，模組加的阻塞節點從 initial 走不到（2026-09-07 實測 384 個）
    b8 = copy.deepcopy(sm)
    for tr in b8["transitions"]:
        if tr["from"] == "**/<非終態>":
            tr["from"] = "**/待辦|進行中|待確認|退回"
    # 只驗偵測能力（`roles/conduct-common.md` §1 附負控輸出），⛔ 不斷言正式表——
    # 正式表的正向可達由 main() 的印承載（19 個系統性突變實測：印捕捉 10、本負控的正式表半唯一捕捉 0）
    ok9 = (bool(research)
           and unreachable(compose(b8, [research]), rplan) == ["研究/阻塞←不可判定"])
    print(f"selftest_blocked_from_covers_module_states: {'PASS' if ok9 else 'FAIL'}（負控 1 條）")
    bad += not ok9
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
    probe = {"name": "rm-only", "adds": {"enums": {"states": []}, "transitions": {"add": [], "remove": [{"from": "需求/待辦", "to": "需求/進行中"}]}}}
    inert = {"name": "no-delta", "adds": {"enums": {"states": []}, "transitions": {"add": [], "remove": []}}}
    dm = delta_modules([probe, inert])
    cs = module_cases(dm)
    ok3 = ([m["name"] for m in dm] == ["rm-only"]
           and len(cs) == 2
           and any(m["name"] == "rm-only" for _, ms in cs for m in ms))
    print(f"selftest_remove_only_module_is_delta: {'PASS' if ok3 else 'FAIL'}（負控 2 條）")
    bad = bad or not ok3
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
    delta_mods = delta_modules(mods)
    cases = module_cases(delta_mods)
    total = bad = 0

    def enabled(m: dict, plan: list[str]) -> bool:
        stages = m.get("adds", {}).get("stages", [])
        return all(st in plan for st in stages)  # 卡級模組只在含該階段的計畫上存在

    unreach = 0
    for label, ms in cases:
        n = f = u = 0
        for plan in plans:
            active = [m for m in ms if enabled(m, plan)]
            composed = compose(sm, active)
            errs = check(composed, plan)
            n += 1
            if errs:
                f += 1
                print(f"FAIL [{label}] {'→'.join(plan)}")
                for e in errs:
                    print(f"  ⛔ {e}")
            miss = unreachable(composed, plan)
            u += len(miss)
            for m in miss:
                print(f"  ⚠️ [{label}] {'→'.join(plan)}：{m} 從 initial 走不到")
        print(f"[{label}] stage_plan 案例：{n}，失敗 {f}，不可達節點 {u}")
        total += n
        bad += f
        unreach += u
    print(f"合計 {total} 案例，失敗 {bad}；模組 delta {len(delta_mods)} 個；不可達節點 {unreach}（印，⛔ 不擋）")
    return 1 if (bad or note_errs) else 0


if __name__ == "__main__":
    sys.exit(main())
