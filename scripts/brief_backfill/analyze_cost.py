#!/usr/bin/env python3
"""逐張成本與延遲的分布，並回答「435／447 那種無法解釋的額度倍增有沒有再出現」。

⚠️ **本批的儀器與前兩批不同**：前兩批的 ``quota_cost`` 是用 REST ``gh api rate_limit``
量的，而該端點對 GraphQL 額度**量不準**（見 ``quota.py``）。本批改用 GraphQL 自身的
``rateLimit`` 欄位。⇒ ⛔ **兩批的數字不可直接比對**，只可比「有沒有出現同形狀的離群」。

**離群判準先講死，⛔ 不看完數據再挑**：
  以中位數 ``m`` 為基準，``quota_cost > 2 × m`` 即記為離群（前兩批的 435／447 對當時
  中位 228 恰是 1.9–2.0 倍，故取 2 倍為同形狀的門檻）。

⚠️ 本批與另一個消費者（``aiwf#122`` 的修復代理）並行 ⇒ **單張的 ``quota_cost`` 含對方的
用量**。⛔ 不得把每一筆離群都歸因為 ``amend`` 自己——那正是前兩批「未編成因」的原因。
本腳本同時印出**逐張延遲**：若某張耗點高而耗時未同步變長，較可能是併發雜訊而非該次
呼叫真的多做了事。⭐ 這是本批新增的鑑別訊號，前兩批沒有記延遲。
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path


def main() -> int:
    led = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    done = [r for r in led if r.get("rc") == 0 and r.get("quota_cost") is not None]
    fail = [r for r in led if r.get("rc") not in (0, None)]
    skipped = [r for r in led if r.get("guard") == "REJECTED"]
    err = [r for r in led if r.get("error")]

    # ⭐ **跨越每小時重置的那幾張必須剔除，⛔ 不是丟掉不方便的資料。**
    # ``quota_cost = remaining_before − remaining_after``；跨越重置時 ``remaining_after``
    # 跳回 5000 ⇒ 差值變成大負數（本批實測 min −2147）。那不是「這張卡回收了額度」，
    # 是**量測區間橫跨兩個 window**，該差值在構造上沒有意義。
    # ⚠️ 派工提示逐字警告過同一件事：PM 曾把 ``3965 → 5000`` 的重置讀成「消耗 1034 點」。
    # ⛔ 判準先講死：``quota_cost < 0`` 即為跨重置，剔除並**具名列出**，⛔ 不靜默丟棄。
    crossed = [r for r in done if r["quota_cost"] < 0]
    valid = [r for r in done if r["quota_cost"] >= 0]
    costs = [r["quota_cost"] for r in valid]
    secs = [r["amend_sec"] for r in valid if r.get("amend_sec") is not None]
    m = statistics.median(costs) if costs else 0
    print(f"  跨越每小時重置而剔除 : {len(crossed)} 張 "
          f"{[(r['card_id'], r['quota_cost']) for r in crossed]}")
    print(f"  納入成本統計          : {len(valid)} 張")

    print(f"ledger 筆數        : {len(led)}")
    print(f"  rc=0（寫入成功）  : {len(done)}")
    print(f"  rc≠0（失敗）      : {len(fail)} {[r['card_id'] for r in fail]}")
    print(f"  守衛拒收          : {len(skipped)} {[r['card_id'] for r in skipped]}")
    print(f"  例外              : {len(err)} {[r['card_id'] for r in err]}")
    print()
    if costs:
        print("══ 逐張 GraphQL 耗點（權威儀器：GraphQL rateLimit 欄位）══")
        print(f"  中位 {m}　平均 {statistics.mean(costs):.1f}　min {min(costs)}　max {max(costs)}")
        print(f"  合計 {sum(costs)} 點／{len(costs)} 張")
    if secs:
        ms = statistics.median(secs)
        print()
        print("══ 逐張 amend 延遲 ══")
        print(f"  中位 {ms:.1f}s　平均 {statistics.mean(secs):.1f}s　min {min(secs):.1f}s　max {max(secs):.1f}s")
        print()
        print("══ ⭐ 兩個天花板（哪一個綁住手腳）══")
        print(f"  額度天花板 : 5000 ÷ {m} = 每小時約 {5000 / m:.0f} 張" if m else "")
        print(f"  延遲天花板 : 3600 ÷ {ms:.1f} = 每小時約 {3600 / ms:.0f} 張")
        print(f"  ⇒ 綁住手腳的是 {'延遲' if 3600 / ms < 5000 / m else '額度'}")

    print()
    print(f"══ 離群（判準先講死：quota_cost > 2 × 中位 = {2 * m}）══")
    out = [r for r in done if r["quota_cost"] > 2 * m]
    if not out:
        print("  ⭐ 零筆。⛔ 零命中不等於「前兩批那個現象不存在」——本批換了儀器，")
        print("     前兩批的 435／447 有可能本來就是舊儀器的假象（未證實，見 quota.py）。")
    for r in out:
        print(f"  {r['card_id']}: {r['quota_cost']} 點 / {r.get('amend_sec')}s"
              f"（中位 {m} 點 / {statistics.median(secs):.1f}s）")
        print(f"      耗時是否同步變長: {'是 ⇒ 較可能真的多做了事' if r.get('amend_sec', 0) > 2 * statistics.median(secs) else '否 ⇒ 較可能是併發雜訊'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
