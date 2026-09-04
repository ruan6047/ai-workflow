#!/usr/bin/env python3
"""唯讀：抓 Project #4 全母體並落地成 JSON 快照，供後續分析零額外額度重跑。

⛔ 不寫任何東西到 GitHub。⛔ 不用 ``gh project item-list``（中文欄位 key 編碼壞，
見 ``project.py::list_items``）——一律走 ``wf_cli.project.list_items``，使盤點與守衛同源。

額度量測（查核 R1-06）
----------------------

本檔的成本數字前後錯過兩次，⛔ **兩次的錯法不同，不要只記得後面那次**：

1. 最早用 REST 的 ``gh api rate_limit`` 量，卻把差值叫做 ``graphql_cost``。那個端點
   量不到 GraphQL 消耗（實測同一時刻兩個狀態並存、序列非單調，見 ``quota.py``），
   ⇒ 名字說是 GraphQL 成本、儀器卻是 REST。
2. 改走 GraphQL 的 ``rateLimit`` 之後，把 ``remaining`` 差值換成 ``used`` 差值，理由
   寫「``used`` 單調遞增，不會像 ``remaining`` 那樣跨重置 [reset] 回跳」。**這個理由
   是錯的**：視窗一翻兩者一起歸零。注入 ``used 4990 → 7`` 實測，舊版照印
   ``graphql_cost=-4983``、``quota_control_ok=true``、``rc=0``。

⭐ 現版把「本腳本的成本」與「帳號層的觀測」**拆成兩個欄位，用兩把不同的尺量**：

``graphql_cost_attributed``
    ``_CostAccountingRunner`` 在**每一支** GraphQL query 裡多要一個
    ``rateLimit { cost … }``，把各回應**自報的 cost 累加**起來。這是本腳本自己送出的
    那些 query 的實際計費，**與視窗無關、與其他消費者無關**——不需要控制組來救。
    實測（2026-08-26，204 張母體）：5 頁各 cost=1、合計 5，同期帳號層 ``used``
    也剛好只動 5（69 → 74）⇒ 注入 ``rateLimit`` 本身不加價（GraphQL 最低計費為 1，
    5 頁不可能低於 5 點，故加價只能是 0）。

``account_used_delta``
    帳號層 ``used`` 差值。⛔ **這不是本腳本的成本**：同一把 token 的所有消費者都記在
    同一本帳。它現在只有一個用途——當 ``graphql_cost_attributed`` 的**對帳**。

⚠️ 歸因不完整，而且是**結構性的**：``resolve_project`` 走的是
``gh project view``（``run_json``），不是 ``runner.graphql``，⇒ 沒有回應可以注入
``rateLimit``。兩次量到都是 **2 點**（67 → 69；另一次由 7 − 5 反推）——⛔ **n=2 不是
「固定 2 點」的保證**，那 2 點只能觀測、無法自報，`gh` 換版就可能改。本檔如實記成
``gh_calls_unattributed``，⛔ **不得把它折算進 attributed 假裝歸因完整**。

對帳的可證偽前提：``account_used_delta >= graphql_cost_attributed``
（帳號同時記到本腳本未注入的呼叫與他人用量，只會多不會少）。
⛔ **這只抓得到高報，抓不到低報**——若 GitHub 自報的 ``cost`` 系統性偏低，本對帳
一樣會通過。要推翻「現版不再說謊」，就從這裡下手：找一支自報 cost 低於實際計費的
query，屆時 attributed 會偏低而對帳照樣綠。

⛔ **不得由本檔的成本數字推出前兩批的成本**：前兩批是用壞掉的 REST 儀器量的，
⇒ 只能重量，不能校正（見 ``quota.py`` 模組 docstring）。
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "cli" / "src"))

import quota as _quota_mod  # noqa: E402
from wf_cli.gh import GhRunner  # noqa: E402
from wf_cli.project import list_items, resolve_project  # noqa: E402

#: 注入到每支 query 最外層 selection set 的欄位。
#: ⛔ 本字串內不得出現 "mutation" 字樣：``tests/test_commands_mocked.py`` 的
#: ``_RecordingRunner`` 以 ``"mutation" in query`` 判定一次呼叫是不是寫入。
_RATE_LIMIT_SELECTION = "rateLimit { cost used remaining resetAt }"

#: 第一個 ``{`` 之前允許出現的東西：可選的 ``query``／操作名／變數定義。
#: ⛔ 刻意不自己寫 GraphQL parser——比對不上就**放棄注入並記成未歸因**（fail-closed），
#: 不硬插。``mutation`` 開頭一定比對不上，這是刻意的：``rateLimit`` 只掛在 Query root。
_OPERATION_PREFIX_RE = re.compile(r"^\s*(query\b\s*([A-Za-z_]\w*)?\s*)?(\([^(){}]*\))?\s*$")


def inject_rate_limit(query: str) -> str | None:
    """在 query 最外層 selection set 開頭插入 ``rateLimit``；無法安全插入時回 ``None``。"""
    brace = query.find("{")
    if brace < 0:
        return None
    if not _OPERATION_PREFIX_RE.match(query[:brace]):
        return None
    return f"{query[: brace + 1]}\n  {_RATE_LIMIT_SELECTION}\n{query[brace + 1 :]}"


class _CostAccountingRunner(GhRunner):
    """在每支 GraphQL query 裡順便要 ``rateLimit``，累加各回應**自報的 cost**。

    (a) 現在的行為：``graphql()`` 送出的是**注入後**的 query，回應多一個
        ``data.rateLimit``（呼叫端只讀 ``data.node``，多一個 key 無害），其 ``cost``
        累進 ``rate_samples``。所有 ``gh`` 呼叫都經過 ``execute()`` ⇒ ``gh_calls`` 是
        總數，``instrumented`` 是其中拿得到自報 cost 的那些，兩者相減即未歸因筆數。
    (b) 為什麼不改 ``wf_cli.gh.GhRunner``：那支被 1270 個測試釘著，而「量自己的額度」
        是本腳本的需求，不是 CLI 的契約。包在腳本這一側，同源讀取（``list_items``）
        與量測兩件事互不污染。
    (c) ⛔ 不得由 ``gh_calls == instrumented`` 之外的情況推出「成本已完整歸因」；
        也⛔ 不得由 ``instrumented`` 筆數推出「這些就是全部的 GraphQL 請求」——
        ``gh project view`` 內部也送 GraphQL，只是我們看不到它的回應。
    """

    def __init__(self, binary: str = "gh") -> None:
        super().__init__(binary=binary)
        self.rate_samples: list[dict] = []
        self.gh_calls = 0
        self.instrumented = 0

    def execute(self, args: Sequence[str], input: str | None = None) -> str:
        self.gh_calls += 1
        return super().execute(args, input=input)

    def graphql(self, query: str, **variables: str) -> dict:
        injected = inject_rate_limit(query)
        if injected is None:
            return super().graphql(query, **variables)
        out = super().graphql(injected, **variables)
        rl = (out.get("data") or {}).get("rateLimit")
        if isinstance(rl, dict) and isinstance(rl.get("cost"), int):
            self.rate_samples.append(rl)
            self.instrumented += 1
        return out

    @property
    def attributed_cost(self) -> int:
        return sum(s["cost"] for s in self.rate_samples)

    @property
    def unattributed_calls(self) -> int:
        return self.gh_calls - self.instrumented


def cross_check(attributed: int, delta: _quota_mod.AccountDelta) -> tuple[bool, str]:
    """用帳號層差值對帳自報成本。回傳 (是否通過, 判詞)。

    (a) 現在的行為：差值不可用（跨視窗／倒退）就判**不通過**，⛔ 不是「當作通過」也
        ⛔ 不是「拿個替代數字繼續算」。差值可用但**小於**自報成本 ⇒ 判不通過。
    (b) 為什麼：前提是「帳號記到的 ≥ 本腳本自報的」。差值不可用時這個前提無從檢驗，
        而「檢驗不了」不等於「通過」——那正是 R1-05／R1-06 兩張 finding 的同一個病。
    (c) ⛔ 不得由本函式通過推出「自報成本正確」：它只抓高報，不抓低報（見模組 docstring）。
    """
    if not delta.usable:
        return False, f"⛔ 無法對帳：{delta.reason} ⇒ 帳號層差值不可用"
    assert delta.delta is not None
    if delta.delta < attributed:
        return False, (
            f"⛔ 對帳矛盾：帳號層只動了 {delta.delta} 點，本腳本卻自報 {attributed} 點"
        )
    return True, f"✅ 對帳通過：自報 {attributed} ≤ 帳號層 {delta.delta}"


def main() -> int:
    out_path = Path(sys.argv[1])
    runner = _CostAccountingRunner()
    _, _, ctrl_pre_ok = _quota_mod.control("（量測前）")
    before = _quota_mod.probe()
    project = resolve_project(runner, "ruan6047", 4)
    items = list_items(runner, project)
    after = _quota_mod.probe()
    _, _, ctrl_post_ok = _quota_mod.control("（量測後）")

    attributed = runner.attributed_cost
    delta = _quota_mod.account_delta(before, after)
    reconciled, verdict = cross_check(attributed, delta)

    payload = {
        "project_url": project.url,
        "item_count": len(items),
        # ⭐ 本腳本自己的成本：各 GraphQL 回應自報 cost 的累加。與視窗、與他人無關。
        "graphql_cost_attributed": attributed,
        "gh_calls_total": runner.gh_calls,
        "gh_calls_instrumented": runner.instrumented,
        # ⚠️ 恆 ≥ 1（`gh project view` 無回應可注入）⇒ attributed 是**下界**不是全部。
        "gh_calls_unattributed": runner.unattributed_calls,
        "cost_attribution_complete": runner.unattributed_calls == 0,
        # ⛔ 以下是**帳號層觀測**，含其他消費者；⛔ 不得當成本腳本的成本引用。
        # 舊欄位名 `graphql_cost` 已移除：那個名字宣稱的東西它從來沒有量到過。
        "account_used_delta": delta.delta,
        "account_delta_usable": delta.usable,
        "account_delta_reason": delta.reason,
        "graphql_used_before": before["used"],
        "graphql_used_after": after["used"],
        "graphql_reset_at_before": before.get("resetAt"),
        "graphql_reset_at_after": after.get("resetAt"),
        "quota_source": "graphql rateLimit (quota.py) + 逐回應自報 cost",
        "quota_reconciled": reconciled,
        "quota_verdict": verdict,
        # 控制組不通過 ⇒ 取樣瞬間就有並行消費者，帳號層差值更不可解讀。
        "quota_control_ok": ctrl_pre_ok and ctrl_post_ok,
        "items": [asdict(i) for i in items],
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    print(
        f"items={len(items)}　本腳本自報成本={attributed} 點"
        f"（{runner.instrumented}/{runner.gh_calls} 支已注入，"
        f"{runner.unattributed_calls} 支未歸因）"
    )
    account = delta.delta if delta.usable else "不可用"
    print(
        f"  帳號層 used {before['used']} → {after['used']}　差值={account}"
        f"（{delta.reason}）"
    )
    print(f"  {verdict}")
    if not (ctrl_pre_ok and ctrl_post_ok):
        print("  ⚠️ 控制組不通過：帳號層差值含他人用量（不影響上面的自報成本）")
    print(f"out={out_path}")

    if not reconciled:
        # ⛔ **刻意讓對帳失敗吃到退出碼，不得改回恆 0**（查核 R1-06）：舊版對
        # 「used 4990 → 7」印 -4983 卻 rc=0，呼叫端（run_all_checks_b3.sh）只 echo rc，
        # ⇒ 一個荒謬的成本數字可以一路無聲流進交付報告。
        # ⛔ 不得由 rc=3 推出「快照檔壞了」：items 已經寫出去而且完整，
        #    紅的只有額度帳。census/measure_* 照樣可以吃這份快照。
        print("⛔ 額度對帳不通過 ⇒ rc=3（⚠️ 快照檔本身已完整寫出，可正常供後續分析使用）")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
