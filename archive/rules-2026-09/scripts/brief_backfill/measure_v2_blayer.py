#!/usr/bin/env python3
"""B 層的 ground truth 補量：⭐ 零命中的第三類歸因（觀測面看不到）。

V2 的 GT 定義是「卡 A 的 ``## Log`` 之前提到卡 B 的卡 ID」，而 **B 層 40 張遷移卡的
Issue body 是遷移 stub**——``## 核心痛點``／``## 驗收條件``／``## 驗證`` 全部留空，
唯一出現的卡 ID 是遷移樣板裡的 ``OPS-STATE-PLANE-MIG1``。

⇒ 對 B 層而言，GT 量到的**不是語意相關，是遷移出處**。真正的語意相關住在
``ruan6047/cpbl-analytics`` 凍結 SHA 的 ``docs/tasks/<卡ID>.md`` 裡，而 GT builder
從來不讀那個檔。本腳本改以該檔為來源重建 B 層的 GT，看簡介抓不抓得回。

⛔ 這不是要取代 V2 的判準——V2 的分母仍照卡面定義算。本量測只回答
「B 層那幾個零是哪一類零」。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "cli" / "src"))

from relatedness import head_of, mentions  # noqa: E402
from wf_cli import brief as brief_mod  # noqa: E402

FROZEN_SHA = "2f52562f575412a0a39b515a4436edd2831b2f65"
CPBL = "/Users/ruanruan/Dev/cpbl-analytics"


def spec_text(card_id: str) -> str | None:
    p = subprocess.run(
        ["git", "-C", CPBL, "show", f"{FROZEN_SHA}:docs/tasks/{card_id}.md"],
        capture_output=True, text=True,
    )
    return p.stdout if p.returncode == 0 else None


def main() -> int:
    items = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["items"]
    cards = [c for c in Path(sys.argv[2]).read_text(encoding="utf-8").split() if c]
    by_id = {(i.get("fields") or {}).get("卡ID"): i for i in items if (i.get("fields") or {}).get("卡ID")}
    all_ids = set(by_id)

    tot = hit = 0
    for cid in cards:
        spec = spec_text(cid)
        if spec is None:
            continue
        parsed = brief_mod.try_parse_block(by_id[cid].get("body") or "")
        text = parsed.text if parsed else ""
        # 以凍結 spec 檔為來源重建 GT（⛔ 排除自己）
        gt = sorted(b for b in all_ids if b != cid and mentions(spec, b))
        got = [b for b in gt if mentions(text, b)]
        tot += len(gt)
        hit += len(got)
        print(f"{cid}")
        print(f"  以 Issue body 建的 GT（已剔除簡介與 Log）: {sorted(b for b in all_ids if b != cid and mentions(head_of(by_id[cid]['body']), b))}")
        print(f"  以凍結 spec 檔建的 GT : {gt}")
        print(f"  簡介抓回              : {got}  →  {len(got)}/{len(gt)}")
    print()
    print(f"B 層以凍結 spec 檔為來源的合計：{hit}/{tot}"
          + (f" = {100.0 * hit / tot:.1f}%" if tot else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
