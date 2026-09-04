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

⛔ **``used`` 只在同一個視窗內單調遞增**（查核 R1-06）
--------------------------------------------------

本模組曾宣稱「用 ``used`` 差值就能避開 ``remaining`` 跨重置 [reset] 的負成本」。
**那個前提是錯的**：視窗一翻，``remaining`` 跳回 5000、``used`` 同樣跳回 0，兩者
一起說謊。跨視窗的 ``after - before`` 有兩種壞法，⛔ **後者比前者危險**：

  1. **負值**（4990 → 7 ⇒ −4983）：荒謬到一眼看得出來。
  2. **看起來正常的正值**（10 → 50，但 50 屬於**下一個**視窗）⇒ 差值 +40 非負、
     單調、量級合理，**沒有任何算術性質抓得到它**。只有 ``resetAt`` 抓得到。

⇒ ``account_delta()`` 一律先比 ``resetAt``，再比是否倒退；兩者任一不成立就判
**不可用**（回 ``None`` 而不是回一個數）。⛔ 不得為了「有個數字好填」而回退成
「取 abs」「取 max(0, …)」或「跨視窗就補上 limit」——補值等於拿猜的當量測。
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass

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
    """已用點數。n>1 時取 max。

    ⛔ **不得拿兩次本函式的回傳值相減當成本**（查核 R1-06 就是這樣壞掉的）：
    裸 ``int`` 把 ``resetAt`` 丟掉了，⇒ 呼叫端無從判斷兩次取樣是不是同一個視窗。
    要算差值一律走 ``account_delta(probe(), probe())``。
    ⚠️ 連 ``n>1 取 max`` 也只在同一視窗內成立——跨視窗時「較大的那個」是**舊的**。
    """
    return max(s["used"] for s in sample(n))


def used_with_evidence(n: int = 3) -> tuple[int, list[dict]]:
    s = sample(n)
    return max(x["used"] for x in s), s


def reset_epoch() -> int:
    import datetime

    iso = probe()["resetAt"].replace("Z", "+00:00")
    return int(datetime.datetime.fromisoformat(iso).timestamp())


@dataclass(frozen=True)
class AccountDelta:
    """兩次 ``rateLimit`` 取樣之間的**帳號層** ``used`` 差值判定。

    ⛔ 這是**帳號層觀測**，不是任何一支腳本自己的成本：同一把 token 的所有消費者
    （並行的代理、編輯器外掛、``gh`` 的其他呼叫）都記在同一本帳上。要「本腳本自己的
    成本」得用各 GraphQL 回應自報的 ``rateLimit.cost``（見
    ``snapshot_population._CostAccountingRunner``）。
    """

    usable: bool
    delta: int | None
    reason: str


def account_delta(before: dict, after: dict) -> AccountDelta:
    """判定 ``after["used"] - before["used"]`` 可不可用。⛔ 不可用時回 ``delta=None``。

    (a) 現在的行為：``resetAt`` 不同、或缺 ``resetAt``、或 ``used`` 倒退，一律判
        ``usable=False`` 且 **不回任何數字**。
    (b) 為什麼：``used`` 的單調性只在同一個視窗內成立（見模組 docstring）。跨視窗的
        差值可能是負的（一眼看得出來），也可能是**看起來完全正常的正值**——後者只有
        ``resetAt`` 抓得到，所以視窗比對是這裡的主判準，倒退檢查只是第二道網。
    (c) ⛔ 不得由 ``usable=True`` 推出「這段期間只有本腳本在消費」——那要靠控制組，
        而控制組也只證明「取樣的那一瞬間沒有他人」，⛔ 不證明整段量測期間都沒有。
    """
    b_reset, a_reset = before.get("resetAt"), after.get("resetAt")
    if b_reset is None or a_reset is None:
        return AccountDelta(False, None, "取樣缺 resetAt，無從判定是否同一視窗")
    if b_reset != a_reset:
        return AccountDelta(False, None, f"跨越 reset 視窗（{b_reset} → {a_reset}）")
    if after["used"] < before["used"]:
        # 同視窗內倒退在文件上不該發生；真的發生代表取樣或端點有鬼 ⇒ 一樣不給數字。
        return AccountDelta(
            False, None, f"同視窗內 used 倒退（{before['used']} → {after['used']}）"
        )
    return AccountDelta(True, after["used"] - before["used"], f"同一視窗（{a_reset}）且未倒退")


def control(label: str = "") -> tuple[dict, dict, bool]:
    """控制組：什麼都不做的前後量測，差值須為 0。回傳 (前取樣, 後取樣, 是否通過)。

    ⚠️ 回傳的是**整份取樣**（含 ``resetAt``）而不是 ``int``：呼叫端要拿 ``resetAt``
    去判視窗，只回 ``used`` 會把 R1-06 的洞原封不動搬到呼叫端。
    """
    a = probe()
    b = probe()
    d = account_delta(a, b)
    ok = d.usable and d.delta == 0
    if d.usable:
        detail = f"used {a['used']} → {b['used']}　差 {d.delta}"
    else:
        detail = f"used {a['used']} → {b['used']}　差值不可用（{d.reason}）"
    print(
        f"  控制組{(' ' + label) if label else ''}：{detail}　"
        f"{'✅ 通過' if ok else '⛔ 不通過（有並行消費者或跨越重置）'}"
    )
    return a, b, ok


if __name__ == "__main__":
    u, ev = used_with_evidence(6)
    print(f"權威 used = {u}")
    for e in ev:
        print(f"  remaining={e['remaining']:>5} used={e['used']:>5} cost={e['cost']} resetAt={e['resetAt']}")

