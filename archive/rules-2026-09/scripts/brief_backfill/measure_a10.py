#!/usr/bin/env python3
"""A10 的三條價值論證，**現場重算**（卡面 A10 逐字要求交付時重跑並附時點）。

⛔ **本腳本刻意不計算 A10 的第 (3) 條。** 那條是「2026-08-26 PM 差點開出兩張重複卡、
三個機制無一攔得住」——當事人自陳的**事件**，⛔ 不是可由快照導出的統計量。想把它機械化
會變成「找兩張內容相似的卡」，那是另一個判準、也不是該條在說的事。⇒ 由交付報告逐字轉述
並附可複驗的出處，⛔ 不在此偽造一個數字。

⛔ **同樣刻意不引用**：canonical §6.3 的「規則要求」（§0.1 自己逐字寫「⛔ 未驗證簡介對
AI 判斷相關性的實效」），以及 ``WF-OPEN-DUPLICATE-DETECT1`` 卡面的舊實害（該卡 2026-08-24
的 Log 逐字記載「實查兩者毫無關係……該證據無法成立」）。需求方 2026-08-26 裁定更換。

第 (1) 條的 GT 用 ``relatedness.head_of``（**已剔除 ``## 簡介`` 區段**）⇒ 回填前後的
邊集合構造上相同，⛔ 不會因為回填而自己把分母做大。本腳本對 before／after 兩份快照都
可跑，數字應一致；不一致代表 ``head_of`` 的剔除失效，那是要查的事。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "cli" / "src"))

from relatedness import head_of, mentions  # noqa: E402
from wf_cli import resources as res_mod  # noqa: E402

#: 驗收條件裡代表「做了相關性判斷」的詞。⚠️ **這是一份開放集合當封閉集合用的清單**，
#: 逐字取自卡面 A10 第 (2) 條所列的四個詞。⛔ 不得由「命中 N 張」推出「恰有 N 張做過
#: 相關性判斷」——寫法沒用到這四個詞的一樣是在做相關性判斷，本數字是**下界**。
#:
#: ⚠️ **卡面 A10(2) 宣稱 21/203，本腳本重算不出來。** 2026-08-26 第三批以四種區段定義
#: 各跑一次（母體 204）：只看 ``## 驗收條件`` 區段 **7**、``## Log`` 之前全文（含簡介）
#: **8**、``## Log`` 之前全文（剔簡介）**8**、body 全文含 Log **16**。四種都不是 21。
#: （母體 204 vs 卡面 203 差 1 張，A1 已載明母體會動；且 204 張**全部**都有
#: ``## 驗收條件`` 標題 ⇒ 差距不是「切不到區段」造成的。）
#:
#: ⇒ 判定 **「無法重現」，⛔ 不是「卡面數字錯」**：原量測的判準沒有隨數字載明（詞表可能
#: 更寬、或母體/區段定義不同），⇒ 我沒有它的判準就無從證偽。⭐ **並且刻意不去搜一份
#: 能湊出 21 的詞表**——那就是「看著答案調判準」，本 repo 已有同族前例
#: （memory: ``numbers-need-evidence-or-discussion``）。本腳本只報這四個詞的下界。
RELATEDNESS_WORDS = ("劃界", "語意重疊", "不是子集", "序位")


def acceptance_section(body: str) -> str:
    """``## 驗收條件`` 到下一個 ``## `` 之間。⛔ 不自寫 markdown 解析器——只切標題行。"""
    lines = (body or "").splitlines()
    try:
        s = next(i for i, ln in enumerate(lines) if ln.strip() == "## 驗收條件")
    except StopIteration:
        return ""
    e = next((j for j in range(s + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
    return "\n".join(lines[s + 1 : e])


def main() -> int:
    snap = Path(sys.argv[1])
    items = json.loads(snap.read_text(encoding="utf-8"))["items"]
    by_id = {(i.get("fields") or {}).get("卡ID"): i for i in items if (i.get("fields") or {}).get("卡ID")}
    decls = {cid: res_mod.try_parse_block(it.get("body") or "") for cid, it in by_id.items()}

    # ── (1) 語意相關邊 vs 資源宣告抓得到的比例 ──
    edges = []
    for a_id, a in by_id.items():
        head = head_of(a.get("body") or "")  # ⭐ 已剔除 ## 簡介，⛔ 不循環量測
        for b_id in by_id:
            if b_id != a_id and mentions(head, b_id):
                edges.append((a_id, b_id))

    def res_hit(a_id, b_id):
        da, db = decls.get(a_id), decls.get(b_id)
        return bool(da and db and set(da.resources) & set(db.resources))

    hit = [e for e in edges if res_hit(*e)]
    n, k = len(edges), len(hit)
    print(f"snapshot : {snap}")
    print(f"母體卡數 : {len(by_id)}")
    print()
    print("══ A10(1) 語意相關邊，資源宣告抓得到幾條 ══")
    print(f"  語意相關邊（GT，`## Log` 之前提到對方卡 ID，已剔除簡介區段）: {n} 條")
    print(f"  ⭐ 資源宣告抓得到 : {k} 條 = {100.0 * k / n:.1f}%" if n else "  n=0")
    print(f"  ⛔ 今天沒有任何機制找得到 : {n - k} 條 = {100.0 * (n - k) / n:.1f}%" if n else "")

    # ── (2) 驗收裡有相關性判斷條款的卡數 ──
    named = []
    for cid, it in by_id.items():
        sec = acceptance_section(it.get("body") or "")
        got = [w for w in RELATEDNESS_WORDS if w in sec]
        if got:
            named.append((cid, got))
    print()
    print("══ A10(2) 驗收條件裡出現相關性判斷條款的卡 ══")
    print(f"  ⭐ {len(named)}／{len(by_id)} 張 ⇒ 那 {len(named)} 次相關性判斷全是人工做的")
    print(f"  用詞（逐字取自卡面 A10，⚠️ 開放集合⇒本數字是下界）: {list(RELATEDNESS_WORDS)}")
    for cid, got in sorted(named):
        print(f"    {cid}: {got}")

    # ── (3) 刻意不算 ──
    print()
    print("══ A10(3) 2026-08-26 經查證的實害 ══")
    print("  ⛔ 本腳本刻意不計算：那是當事人自陳的事件，不是快照可導出的統計量。")
    print("     見本腳本 docstring 與交付報告的逐字轉述。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
