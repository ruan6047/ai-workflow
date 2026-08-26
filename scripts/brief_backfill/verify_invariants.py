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

⛔ **本工具 fail-closed**（查核 R1-05）
------------------------------------

⚠️ 舊版有兩個洞，兩個都會讓它**印出「全數通過」卻其實沒驗到**：

1. ledger 有這張卡、但 ``before``／``after`` 檔缺一，**直接 ``continue`` 跳過**，
   而總判定變數 ``all_ok`` 不受影響 ⇒ 158 張裡少驗任何一張都照印「全數通過」、
   ``rc=0``。⭐ **驗不到 ≠ 通過**。負控實測：從通過的 158 張刪掉一個 ``before``，
   舊版仍印「全數通過」、``rc=0``、只有一行不起眼的「跳過」。
2. 上面第 (3) 條的 ``## 核心痛點`` 只被**算出來印在報表上**，⛔ **沒有進入 ``ok``**。
   負控實測：在 before/after 同位置各注入第二個 ``## 核心痛點``（同位置注入才不會
   被「新增行」那條攔下，⇒ 這個變異只穿透這一個洞），舊版該卡照印 ``PASS``、
   報表上明明白白寫著「## 核心痛點 出現次數: 2」。

⇒ 現版：缺檔即該卡判 ``FAIL`` 並讓總判定不通過（``rc=1``）、``ok`` 納入
``## 核心痛點 == 1``，且總判定行**一律印出已驗筆數／ledger 筆數**，
使「驗了幾張」不再只能靠讀完整份輸出去數。
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
    checked = 0
    missing: list[str] = []
    for rec in ledger:
        cid = rec["card_id"]
        bp, ap = run / "before" / f"{cid}.md", after_dir / f"{cid}.md"
        if not bp.exists() or not ap.exists():
            # ⛔ **刻意 fail-closed，不得改回 continue**（查核 R1-05）：
            # ledger 說這張卡被改過，而我們拿不到 before／after ⇒ 這張卡的不變量
            # **未經證明**。舊版在此 `continue` 且不動 `all_ok`，於是「少驗一張」
            # 與「全部驗過」印出來一模一樣。⛔ 不得由「沒有 FAIL」推出「不變量成立」——
            # 只能由「已驗筆數 == ledger 筆數且無 FAIL」推出。
            lost = [str(p) for p in (bp, ap) if not p.exists()]
            print(f"FAIL  {cid}")
            print(f"      ⛔ 缺檔，無法比對（⇒ 本卡不變量未經證明）：{lost}")
            print()
            missing.append(cid)
            all_ok = False
            continue
        r = check(cid, bp.read_text(encoding="utf-8"), ap.read_text(encoding="utf-8"), briefs[cid])
        checked += 1
        ok = (
            r["所有 before 非空行逐字保留且順序不變"]
            and r["新增行 = 簡介區塊四行"]
            and not r["其他非預期新增行"]
            and r["## Log 出現次數"] == 1
            # ⭐ 本行是 R1-05 補上的：舊版把它算出來印在報表上卻沒納入判定，
            # ⇒ 報表寫著「出現次數: 2」而該卡照印 PASS。第二個 `## 核心痛點`
            # 會讓日後的 `card.amend_core_pain` 定位失敗，是真的壞掉不是美觀問題。
            and r["## 核心痛點 出現次數"] == 1
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
    # ⭐ 覆蓋率與判定同一行印出：「全數通過」這四個字只有在
    #    已驗筆數 == ledger 筆數時才可能出現（缺檔已在上面判 FAIL 並拉倒 all_ok）。
    if missing:
        print(f"⛔ 缺 before/after 而無法比對：{len(missing)} 張 → {missing}")
    print(
        f"V4 總判定：{'全數通過' if all_ok else '有不通過項'}"
        f"（已驗 {checked}/{len(ledger)} 張）"
    )
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
