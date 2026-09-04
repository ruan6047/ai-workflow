#!/usr/bin/env python3
"""把兩次執行併成一份「原始 before → 最終 after」對照，供 V4 逐張驗不變量。

before 一律取**第一次執行前**的原始 body（``run-pilot/before``）——⛔ 不取修復輪的
before，那已含第一次寫進去的簡介，拿它當基準會讓「新增了什麼」少算一次。
after 取該卡**最後一次**寫入後的 body。
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


def main() -> int:
    pilot, fix, final = (Path(p) for p in sys.argv[1:4])
    (final / "before").mkdir(parents=True, exist_ok=True)
    (final / "after").mkdir(parents=True, exist_ok=True)

    led = {r["card_id"]: dict(r) for r in json.loads((pilot / "ledger.json").read_text(encoding="utf-8"))}
    fix_led = (
        {r["card_id"]: dict(r) for r in json.loads((fix / "ledger.json").read_text(encoding="utf-8"))}
        if (fix / "ledger.json").exists()
        else {}
    )

    for cid, rec in led.items():
        shutil.copy(pilot / "before" / f"{cid}.md", final / "before" / f"{cid}.md")
        src = fix if cid in fix_led else pilot
        shutil.copy(src / "after" / f"{cid}.md", final / "after" / f"{cid}.md")
        if cid in fix_led:
            rec["amend 次數"] = 2
            rec["第二輪"] = {
                k: fix_led[cid].get(k)
                for k in ("rc", "quota_cost", "waited_sec", "after_sha256", "after_len", "stderr")
            }
        else:
            rec["amend 次數"] = 1
    (final / "ledger.json").write_text(
        json.dumps(list(led.values()), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"併好 {len(led)} 張；其中二輪修復 {len(fix_led)} 張 → {final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
