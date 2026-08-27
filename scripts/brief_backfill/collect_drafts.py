#!/usr/bin/env python3
"""把各 chunk 的草稿併成一份 ``briefs-b3.json``，並在**寫入前**逐則過守衛。

⭐ **零遠端呼叫**——這支只做本地驗收。⛔ 不合格的不會被靜默丟掉，一律列名並回非零 rc。

檢查項（與 ``backfill.py`` 實際會呼叫的**同一支** ``guard.assert_writable``）：
  * A5 分行字元（``guard.LINE_BREAKING_CHARS``，由 ``str.splitlines()`` 行為導出）
  * A5 UTF-8 位元組上限（``guard.FIELD_BYTE_LIMIT``）
  * ``brief.validate_shape``（兩個標記）
  * A6 跨界具名（``guard.a6_named_targets``；⭐ **篩不是閘**——不通過只列名不剔除）

⛔ **不在此重打任何常數或判準**：全部 import。本 repo 已有五次「驗證器自己打錯」
造成的假陰性（memory: ``verifier-must-import-not-retype``）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "cli" / "src"))

from guard import BriefRejected, a6_named_targets, assert_writable  # noqa: E402


def main() -> int:
    draft_dir = Path(sys.argv[1])
    expect_file = Path(sys.argv[2])
    out_file = Path(sys.argv[3])

    expected = [c for c in expect_file.read_text(encoding="utf-8").split() if c]
    merged: dict[str, str] = {}
    dup: list[str] = []
    for p in sorted(draft_dir.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for k, v in d.items():
            if k in merged:
                dup.append(k)
            merged[k] = v

    missing = [c for c in expected if c not in merged]
    extra = [c for c in merged if c not in expected]

    ok, rejected, no_a6 = [], [], []
    for cid in expected:
        if cid not in merged:
            continue
        try:
            assert_writable(merged[cid])
        except BriefRejected as exc:
            rejected.append((cid, str(exc)))
            continue
        except Exception as exc:  # brief.BriefError（形狀）
            rejected.append((cid, f"{type(exc).__name__}: {exc}"))
            continue
        ok.append(cid)
        if not a6_named_targets(merged[cid]):
            no_a6.append(cid)

    sizes = sorted(len(merged[c].encode("utf-8")) for c in ok)
    print(f"chunk 檔數        : {len(list(draft_dir.glob('*.json')))}")
    print(f"預期卡數          : {len(expected)}")
    print(f"併出草稿數        : {len(merged)}（重複 key {len(dup)}：{sorted(set(dup))}）")
    print(f"缺草稿            : {len(missing)} {missing}")
    print(f"多出（不在清單）  : {len(extra)} {extra}")
    print(f"⭐ 過守衛          : {len(ok)}／{len(expected)}")
    print(f"⛔ 被守衛拒收      : {len(rejected)}")
    for cid, why in rejected:
        print(f"    {cid}: {why}")
    print(f"A6 具名（篩不是閘）: 通過 {len(ok) - len(no_a6)}／{len(ok)}；不通過 {len(no_a6)} {no_a6}")
    if sizes:
        print(f"位元組長度        : min {sizes[0]} / 中位 {sizes[len(sizes) // 2]} / max {sizes[-1]}"
              f"（上限 1012）")

    out = {c: merged[c] for c in ok}
    out_file.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_file.parent / "b3_writable.txt").write_text("\n".join(ok) + "\n", encoding="utf-8")
    print(f"\n可寫入清單 → {out_file.parent / 'b3_writable.txt'}（{len(ok)} 張）")
    print(f"簡介 JSON  → {out_file}")
    return 0 if not rejected and not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
