#!/usr/bin/env python3
"""V5 的另一半：證明 A5 守衛**承重**——沒有它，那些字元真的會穿過去。

⛔ 純函式、零遠端寫入：拿**真實既有卡的 body**（非自造樣本）餵
``card.amend_brief``，看它擋不擋。擋不住即證明守衛不是零資訊檢查。

⚠️ 「真實樣本非自造」：自造樣本必然符合範本，測不出實際形狀。
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "cli" / "src"))

from guard import LINE_BREAKING_CHARS  # noqa: E402
from wf_cli.card import AmendError, amend_brief  # noqa: E402

BASE = "測試值。適用時機：不適用。⛔ 非射程：不適用（`docs/AI_RUNBOOK.md`）。"


def main() -> int:
    body = Path(sys.argv[1]).read_text(encoding="utf-8")
    print(f"真實卡面樣本：{sys.argv[1]}（{len(body)} 字元）")
    print(f"原 body 的 `## Log` 標題行數：{sum(1 for line in body.splitlines() if line.strip() == '## Log')}")
    print()
    passed_through = []
    for ch in sorted(LINE_BREAKING_CHARS):
        value = BASE + ch + "## Log"
        try:
            new_body, _old = amend_brief(body, value)
        except AmendError as exc:
            print(f"  U+{ord(ch):04X}  amend_brief 拒收：{exc}")
            continue
        except Exception as exc:  # noqa: BLE001
            print(f"  U+{ord(ch):04X}  {type(exc).__name__}：{exc}")
            continue
        logs = sum(1 for line in new_body.splitlines() if line.strip() == "## Log")
        passed_through.append((ch, logs))
        print(f"  U+{ord(ch):04X}  ⛔ 穿過（未拒收）；新 body 的 `## Log` 標題行數 = {logs}")
    print()
    print(f"結論：{len(passed_through)}/{len(LINE_BREAKING_CHARS)} 個字元穿過 amend_brief；"
          f"其中造成兩個 `## Log` 的有 {sum(1 for _, n in passed_through if n >= 2)} 個")
    print("⇒ 守衛承重（若移除守衛，這些值會實際寫進卡面）。⛔ 本檢查零遠端寫入。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
