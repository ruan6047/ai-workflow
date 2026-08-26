#!/usr/bin/env python3
"""GraphQL 額度的**權威**讀取。⭐ 取代 ``gh api rate_limit``（REST）。

⛔ **REST 的 ``rate_limit`` 端點量不準 GraphQL 額度**（2026-08-26 第三批開工時現場
量到，本卡前兩批的所有成本數字都是用它量的）。實測它在**兩個互不同步的狀態**之間跳：

    remaining=5000 used=0     reset 每次讀取都 +1（滑動）  ← 沒有記到任何用量
    remaining=4927 used=73    reset 固定 1787750329        ← 有記帳但落後

兩者的 ``reset`` **都在未來**（12 次取樣逐筆驗過，⛔ 不是「過期快取」——我第一次
判成 stale 是自己拿舊的 ``now`` 去減，算錯了）。40 次連續讀取中 4 次讀到後者，序列
**非單調**（5000 → 4935 → 5000，讀回變大 3/39 次）。更糟的是「取 max(used) 就好」
也不成立：跑完 20 次 ``ensure_fields`` 後連取 8 次**全部**讀到 used=0，算出 −76 點。

⭐ **權威來源是 GraphQL 自己的 ``rateLimit`` 欄位**：由 GraphQL API 在同一個請求裡評
估，實測連續 6 次讀數**完全一致**（used=136 / remaining=4864 / resetAt 固定），而
同一時刻 REST 說 used=0。⇒ 本模組一律走 ``gh api graphql``。

⚠️ ``rateLimit`` 查詢**回報 ``cost=1`` 但不實際計費**：連續 6 次探針後 ``used`` 未動
（136 → 136）。⛔ 不得由此推出「所有 GraphQL 查詢都不計費」——這是 ``rateLimit``
這個欄位的特例，GitHub 文件明列。

⛔ **不得由本模組推出「前兩批的成本數字只要換算就好」**：那些數字是用壞掉的儀器量的，
⇒ **只能重量，不能校正**。前兩批登記的兩筆「無法解釋的 435／447 點」與這個儀器缺陷
形狀相符，但⛔ **未證實**——當時的原始取樣序列沒有留下 ``reset`` 欄位，無從回溯判定。

⚠️ 另一個消費者（``aiwf#122`` 的修復代理）與本腳本並行 ⇒ 任何量測都要跑控制組：
量測前後各取一次 ``used``，中間**不做任何事**，差值須為 0。
"""

from __future__ import annotations

import json
import subprocess
import time

_QUERY = "{ rateLimit { limit cost remaining used resetAt } }"


def probe() -> dict:
    """單次權威讀取。⛔ 走 GraphQL，不走 REST ``rate_limit``。"""
    p = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={_QUERY}"], capture_output=True, text=True
    )
    if p.returncode != 0:
        raise RuntimeError(f"rateLimit 探針失敗：{p.stderr}")
    r = json.loads(p.stdout)["data"]["rateLimit"]
    r["t"] = int(time.time())
    return r


def sample(n: int = 3) -> list[dict]:
    return [probe() for _ in range(n)]


def used(n: int = 1) -> int:
    """已用點數。⭐ n>1 時取 max（單調遞增量，取 max 即最新）。"""
    return max(s["used"] for s in sample(n))


def used_with_evidence(n: int = 3) -> tuple[int, list[dict]]:
    s = sample(n)
    return max(x["used"] for x in s), s


def reset_epoch() -> int:
    import datetime

    iso = probe()["resetAt"].replace("Z", "+00:00")
    return int(datetime.datetime.fromisoformat(iso).timestamp())


def control(label: str = "") -> tuple[int, int, bool]:
    """控制組：什麼都不做的前後量測，差值須為 0。回傳 (前, 後, 是否通過)。"""
    a = used()
    b = used()
    ok = a == b
    print(
        f"  控制組{(' ' + label) if label else ''}：used {a} → {b}　差 {b - a}　"
        f"{'✅ 通過' if ok else '⛔ 不通過（有並行消費者或跨越重置）'}"
    )
    return a, b, ok


if __name__ == "__main__":
    u, ev = used_with_evidence(6)
    print(f"權威 used = {u}")
    for e in ev:
        print(f"  remaining={e['remaining']:>5} used={e['used']:>5} cost={e['cost']} resetAt={e['resetAt']}")

