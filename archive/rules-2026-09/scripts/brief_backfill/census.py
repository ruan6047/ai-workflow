#!/usr/bin/env python3
"""唯讀：對快照全母體逐張跑 ``brief.parse_block`` 與 ``brief.drifted``。

A1 的四個數字（item 總數／有簡介／缺簡介／雙居所漂移）與 V1 的兩份具名清單
皆由本腳本產生。⛔ 不接受人工聲明。

⭐ 索引鍵一律 ``card_id``——Project #4 橫跨兩 repo，issue 號會撞。
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cli" / "src"))

from wf_cli import brief as brief_mod  # noqa: E402


def load(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["items"]


def classify(items: list[dict]) -> dict:
    has_brief: list[str] = []
    missing: list[str] = []
    drift: list[tuple[str, str]] = []
    shape_ok: list[str] = []
    shape_bad: list[tuple[str, str]] = []
    no_card_id: list[str] = []

    for it in items:
        cid = (it.get("fields") or {}).get("卡ID")
        body = it.get("body") or ""
        field_val = (it.get("fields") or {}).get(brief_mod.FIELD_NAME)
        key = cid or f"<no-card-id:{it['item_id']}>"
        if not cid:
            no_card_id.append(key)
        parsed = brief_mod.try_parse_block(body)
        if parsed is None:
            missing.append(key)
        else:
            has_brief.append(key)
            try:
                brief_mod.validate_shape(parsed.text)
                shape_ok.append(key)
            except brief_mod.BriefError as exc:
                shape_bad.append((key, str(exc)))
        is_drift, why = brief_mod.drifted(body, field_val)
        if is_drift:
            drift.append((key, why))
    return {
        "total": len(items),
        "has_brief": sorted(has_brief),
        "missing": sorted(missing),
        "drift": sorted(drift),
        "shape_ok": sorted(shape_ok),
        "shape_bad": sorted(shape_bad),
        "no_card_id": sorted(no_card_id),
    }


def main() -> int:
    snap = Path(sys.argv[1])
    items = load(snap)
    r = classify(items)
    print(f"snapshot          : {snap}")
    print(f"item 總數          : {r['total']}")
    print(f"有簡介 N           : {len(r['has_brief'])}")
    print(f"缺簡介 N           : {len(r['missing'])}")
    print(f"雙居所漂移 N       : {len(r['drift'])}")
    print(f"形狀皆合格         : {len(r['shape_ok'])}/{len(r['has_brief'])}")
    print(f"無卡ID item        : {len(r['no_card_id'])}")
    print()
    print("── 有簡介具名清單 ──")
    for k in r["has_brief"]:
        print(f"  {k}")
    print("── 漂移具名清單 ──")
    for k, why in r["drift"]:
        print(f"  {k}: {why}")
    if r["shape_bad"]:
        print("── 形狀不合格 ──")
        for k, why in r["shape_bad"]:
            print(f"  {k}: {why}")
    if r["no_card_id"]:
        print("── 無卡ID ──")
        for k in r["no_card_id"]:
            print(f"  {k}")
    # issue 號重複統計（證明索引鍵不能用 issue 號）
    nums = Counter(
        (it.get("issue_number"), it.get("issue_url", "").split("/")[4] if it.get("issue_url") else None)
        for it in items
        if it.get("issue_number")
    )
    raw_nums = Counter(it.get("issue_number") for it in items if it.get("issue_number"))
    dup = sum(1 for n, c in raw_nums.items() if c > 1)
    print()
    print(f"issue 號母體       : {sum(raw_nums.values())} 筆、相異 {len(raw_nums)} 個、重複號 {dup} 個")
    print(f"(repo, issue) 相異 : {len(nums)}")
    print(f"缺簡介清單長度     : {len(r['missing'])}（完整清單見 --missing）")
    if "--missing" in sys.argv:
        print("── 缺簡介具名清單 ──")
        for k in r["missing"]:
            print(f"  {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
