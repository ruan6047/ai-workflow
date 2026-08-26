#!/usr/bin/env python3
"""V2／V3 的量測：語意相關 ground truth 上的覆蓋率。

**Ground truth（GT-A，卡面 V2 的逐字定義）**：卡 A 的 ``## Log`` 之前提到卡 B 的**卡 ID**。
**GT-B（本輪追加，⚠️ 非卡面定義）**：同上，但也認 ``aiwf#N``／``cpbl#N``／同 repo 裸 ``#N``
的 issue 參照。追加理由：實測卡面互相引用時**兩種寫法都在用**，只認卡 ID 會系統性漏掉
以 issue 號引用的那一半 ⇒ 兩份都報，⛔ 不擇一。

**基準**：同一組 (A, B)，兩卡的 ``resources`` 有無完全相同字串（``find_conflicts`` 的判準）。
**簡介覆蓋**：A 的簡介文字有無提到 B（strict＝卡 ID；ext＝卡 ID 或 issue 參照）。

``--override`` 可用一份 JSON 取代指定卡的簡介文字，供 V3 變異檢驗離線比較，
⛔ 不需要把摘要版真的寫進卡面。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "cli" / "src"))

from guard import a6_named_targets  # noqa: E402
from relatedness import _REPO_ALIAS, head_of, issue_refs, mentions, repo_of  # noqa: E402
from wf_cli import brief as brief_mod  # noqa: E402
from wf_cli import resources as res_mod  # noqa: E402


def pct(n: int, d: int) -> str:
    return f"{100.0 * n / d:.1f}%" if d else "n/a"


def main() -> int:
    snap = Path(sys.argv[1])
    subset = set(Path(sys.argv[2]).read_text(encoding="utf-8").split()) if len(sys.argv) > 2 else None
    override = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8")) if len(sys.argv) > 3 else {}

    items = json.loads(snap.read_text(encoding="utf-8"))["items"]
    by_id = {(i.get("fields") or {}).get("卡ID"): i for i in items if (i.get("fields") or {}).get("卡ID")}
    ident = {}
    for cid, it in by_id.items():
        alias = _REPO_ALIAS.get(repo_of(it) or "")
        if alias and it.get("issue_number"):
            ident[(alias, int(it["issue_number"]))] = cid

    briefs = {}
    for cid, it in by_id.items():
        parsed = brief_mod.try_parse_block(it.get("body") or "")
        briefs[cid] = override.get(cid, parsed.text if parsed else None)

    decls = {cid: res_mod.try_parse_block(it.get("body") or "") for cid, it in by_id.items()}

    gt_a, gt_b = [], []
    for a_id, a in by_id.items():
        head = head_of(a.get("body") or "")
        refs = issue_refs(head, repo_of(a))
        ref_ids = {ident[r] for r in refs if r in ident}
        for b_id in by_id:
            if b_id == a_id:
                continue
            by_card_id = mentions(head, b_id)
            if by_card_id:
                gt_a.append((a_id, b_id))
            if by_card_id or b_id in ref_ids:
                gt_b.append((a_id, b_id))

    def res_hit(a_id, b_id):
        da, db = decls.get(a_id), decls.get(b_id)
        return bool(da and db and set(da.resources) & set(db.resources))

    def brief_hit(a_id, b_id, mode):
        t = briefs.get(a_id)
        if not t:
            return False
        if mentions(t, b_id):
            return True
        if mode == "strict":
            return False
        return any(ident.get(r) == b_id for r in issue_refs(t, repo_of(by_id[a_id])))

    for name, gt in (("GT-A（卡面定義：卡 ID）", gt_a), ("GT-B（追加：卡 ID 或 issue 參照）", gt_b)):
        for label, sel in (
            ("全母體", gt),
            ("先導批 10 張為來源", [p for p in gt if subset and p[0] in subset]),
        ):
            if subset is None and label != "全母體":
                continue
            n = len(sel)
            r = sum(1 for p in sel if res_hit(*p))
            s = sum(1 for p in sel if brief_hit(*p, "strict"))
            e = sum(1 for p in sel if brief_hit(*p, "ext"))
            print(f"── {name} ／ {label} ──")
            print(f"   組數 {n}（來源卡 {len({p[0] for p in sel})} 張）")
            print(f"   資源宣告基準 : {r}/{n} = {pct(r, n)}")
            print(f"   簡介 strict  : {s}/{n} = {pct(s, n)}")
            print(f"   簡介 ext     : {e}/{n} = {pct(e, n)}")
            print()

    if subset:
        print("── 先導批逐卡（GT-A）──")
        for cid in sorted(subset):
            ps = [p for p in gt_a if p[0] == cid]
            hit = [p[1] for p in ps if brief_hit(*p, "strict")]
            miss = [p[1] for p in ps if not brief_hit(*p, "strict")]
            a6 = a6_named_targets(briefs.get(cid) or "")
            print(f"  {cid}: {len(hit)}/{len(ps)}  命中 {hit}  未中 {miss}")
            print(f"      A6 具名對象 {len(a6)} 個：{a6 if a6 else '⛔ 無（A6 不通過）'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
