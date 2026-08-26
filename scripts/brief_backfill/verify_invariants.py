#!/usr/bin/env python3
"""V4 卡面不變量：逐張比對回填前後 body（真實樣本，⛔ 不自造）。

證明三件事：
  (1) **所有非空行逐字保留且順序不變**（以最長共同子序列比對，⛔ 不用集合——
      集合比對看不出順序，而順序正是「插入位置對不對」的判準）。
  (2) 新增的非空行恰為 ``## 簡介`` ＋三行哨兵區塊，外加 N 行 ``## Log`` 條目
      （N = 本卡實際跑過的 amend 次數；⚠️ Log 行由 ``amend_cmd`` 追加，
      ⛔ 不是 ``card.amend_brief`` 產生的，兩者要分開驗）。
  (3) ``## Log`` 與 ``## 核心痛點`` 標題各只出現一次。

另附**純函式**層的不變量：對 before 直接跑 ``card.amend_brief``，證明它只加那四行。
"""

from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "cli" / "src"))

from wf_cli.brief import BEGIN, END, SECTION_HEADING, parse_block  # noqa: E402
from wf_cli.card import amend_brief  # noqa: E402

LOG_LINE_RE = re.compile(r"^- \d{4}-\d{2}-\d{2}T[\d:+\-]+ amend by wf-cli（op [0-9a-f]{8}）→ 簡介：")


def nonempty(body: str) -> list[str]:
    return [ln for ln in body.splitlines() if ln.strip()]


def check(cid: str, before: str, after: str, brief_text: str) -> dict:
    b, a = nonempty(before), nonempty(after)
    sm = difflib.SequenceMatcher(a=b, b=a, autojunk=False)
    kept, added, removed = [], [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            kept += a[j1:j2]
        elif tag == "insert":
            added += a[j1:j2]
        elif tag == "delete":
            removed += b[i1:i2]
        else:  # replace
            removed += b[i1:i2]
            added += a[j1:j2]

    expected_block = [SECTION_HEADING, BEGIN, brief_text, END]
    log_added = [ln for ln in added if LOG_LINE_RE.match(ln)]
    other_added = [ln for ln in added if ln not in expected_block and ln not in log_added]

    parsed = parse_block(after)
    # 純函式層：對原 body 直接跑 amend_brief，看它只加哪些非空行
    pure_body, pure_old = amend_brief(before, brief_text)
    pure_added = [ln for ln in nonempty(pure_body) if ln not in nonempty(before)]

    return {
        "card_id": cid,
        "非空行 before/after": [len(b), len(a)],
        "所有 before 非空行逐字保留且順序不變": len(kept) == len(b) and not removed,
        "移除的行": removed,
        "新增行 = 簡介區塊四行": sorted(ln for ln in added if ln in expected_block) == sorted(expected_block),
        "新增的 Log 條目數": len(log_added),
        "其他非預期新增行": other_added,
        "## Log 出現次數": sum(1 for ln in after.splitlines() if ln.strip() == "## Log"),
        "## 核心痛點 出現次數": sum(1 for ln in after.splitlines() if ln.strip() == "## 核心痛點"),
        "## 簡介 出現次數": sum(1 for ln in after.splitlines() if ln.strip() == SECTION_HEADING),
        "回讀 parse_block 逐字相符": parsed.text == brief_text,
        "純函式 amend_brief 新增非空行": pure_added,
        "純函式 舊值": pure_old,
    }


def main() -> int:
    run = Path(sys.argv[1])
    briefs = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    after_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else run / "after"
    ledger = json.loads((run / "ledger.json").read_text(encoding="utf-8"))
    all_ok = True
    for rec in ledger:
        cid = rec["card_id"]
        bp, ap = run / "before" / f"{cid}.md", after_dir / f"{cid}.md"
        if not bp.exists() or not ap.exists():
            print(f"[{cid}] 缺 before/after 檔，跳過")
            continue
        r = check(cid, bp.read_text(encoding="utf-8"), ap.read_text(encoding="utf-8"), briefs[cid])
        ok = (
            r["所有 before 非空行逐字保留且順序不變"]
            and r["新增行 = 簡介區塊四行"]
            and not r["其他非預期新增行"]
            and r["## Log 出現次數"] == 1
            and r["## 簡介 出現次數"] == 1
            and r["回讀 parse_block 逐字相符"]
            and r["純函式 amend_brief 新增非空行"] == [SECTION_HEADING, BEGIN, briefs[cid], END]
        )
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {cid}")
        for k, v in r.items():
            if k == "card_id":
                continue
            if k == "純函式 amend_brief 新增非空行":
                v = f"{len(v)} 行 = {[x[:24] + '…' if len(x) > 24 else x for x in v]}"
            print(f"      {k}: {v}")
        print()
    print("V4 總判定：", "全數通過" if all_ok else "有不通過項")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
