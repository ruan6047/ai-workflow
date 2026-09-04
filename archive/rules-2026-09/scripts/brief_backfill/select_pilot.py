#!/usr/bin/env python3
"""唯讀：先導批 10 張的抽樣。⛔ 種子寫死並印出，抽樣可重現。

組成（卡面 A4／A8 與派工提示）：
  必含 aiwf#122 `WF-TRANSITION-TABLE-UNWRITTEN1`、aiwf#130 `WF-STAGE-STATE-TWO-AXIS1`
  ≥3 張 B 層（body 有 `## Spec`，內容在 cpbl-analytics 凍結 SHA 的 docs/tasks/）
  ≥2 張終態卡（`assign_cmd.TERMINAL_STATUSES`，⛔ 不手打字面）
  其餘自 A 層缺簡介池隨機
排除：aiwf#15（A2，body 有字面 \\n，amend --brief rc≠0，⛔ 不修）、
      #140 `WF-RESOURCE-HEADING-SUFFIX1-PROBE-ASSIGN1`（A3，雙居所漂移走另一路徑）、
      本卡自己（已有簡介）、其餘已有簡介者。
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cli" / "src"))

from wf_cli import brief as brief_mod  # noqa: E402
from wf_cli.commands.assign_cmd import TERMINAL_STATUSES  # noqa: E402

SEED = 20260826
EXCLUDE_CARD_IDS = {
    "WF-REVIEW-EVENT-MARKER-CONTRACT1",  # aiwf#15，A2
    "WF-RESOURCE-HEADING-SUFFIX1-PROBE-ASSIGN1",  # #140，A3
}
MANDATORY = ["WF-TRANSITION-TABLE-UNWRITTEN1", "WF-STAGE-STATE-TWO-AXIS1"]


def layer(item: dict) -> str:
    body = item.get("body") or ""
    if (item.get("fields") or {}).get("卡ID") == "WF-RESOURCE-HEADING-SUFFIX1-PROBE-ASSIGN1":
        return "C"
    if any(line.strip() == "## Spec" for line in body.splitlines()):
        return "B"
    return "A"


def main() -> int:
    snap = Path(sys.argv[1])
    items = json.loads(snap.read_text(encoding="utf-8"))["items"]
    by_id = {(it.get("fields") or {}).get("卡ID"): it for it in items if (it.get("fields") or {}).get("卡ID")}

    pool = {
        cid: it
        for cid, it in by_id.items()
        if brief_mod.try_parse_block(it.get("body") or "") is None
        and cid not in EXCLUDE_CARD_IDS
    }
    print(f"種子 random.Random({SEED})")
    print(f"缺簡介池（已扣除 A2/A3 兩張排除）: {len(pool)}")
    print(f"  A 層 {sum(1 for i in pool.values() if layer(i)=='A')}"
          f" / B 層 {sum(1 for i in pool.values() if layer(i)=='B')}"
          f" / C 層 {sum(1 for i in pool.values() if layer(i)=='C')}")
    print(f"終態列舉（import 自 assign_cmd）: {sorted(TERMINAL_STATUSES)}")

    rng = random.Random(SEED)
    picked: list[str] = []
    for cid in MANDATORY:
        assert cid in pool, f"必含卡 {cid} 不在缺簡介池"
        picked.append(cid)

    b_pool = sorted(cid for cid, it in pool.items() if layer(it) == "B" and cid not in picked)
    picked += rng.sample(b_pool, 3)

    term_pool = sorted(
        cid
        for cid, it in pool.items()
        if layer(it) == "A"
        and (it.get("fields") or {}).get("交付狀態") in TERMINAL_STATUSES
        and cid not in picked
    )
    picked += rng.sample(term_pool, 2)

    rest_pool = sorted(cid for cid in pool if cid not in picked)
    picked += rng.sample(rest_pool, 10 - len(picked))

    print()
    print(f"{'卡ID':<48} {'issue':<20} {'層':<3} {'交付狀態':<8} body 長度")
    for cid in picked:
        it = pool[cid]
        repo = (it.get("issue_url") or "").split("/")[4] if it.get("issue_url") else "(draft)"
        num = f"{repo}#{it.get('issue_number')}" if it.get("issue_number") else "(draft)"
        st = (it.get("fields") or {}).get("交付狀態")
        print(f"{cid:<48} {num:<20} {layer(it):<3} {st:<8} {len(it.get('body') or '')}")
    n_term = sum(1 for c in picked if (pool[c].get("fields") or {}).get("交付狀態") in TERMINAL_STATUSES)
    print()
    print(f"檢核：共 {len(picked)} 張；B 層 {sum(1 for c in picked if layer(pool[c])=='B')} 張；"
          f"終態 {n_term} 張；必含 {[c in picked for c in MANDATORY]}")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    if out:
        out.write_text("\n".join(picked) + "\n", encoding="utf-8")
        print(f"清單已寫入 {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
