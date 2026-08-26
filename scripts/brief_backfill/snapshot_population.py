#!/usr/bin/env python3
"""唯讀：抓 Project #4 全母體並落地成 JSON 快照，供後續分析零額外額度重跑。

⛔ 不寫任何東西到 GitHub。⛔ 不用 ``gh project item-list``（中文欄位 key 編碼壞，
見 project.py:377）——一律走 ``wf_cli.project.list_items``，使盤點與守衛同源。

額度量測（查核 R1-06）
----------------------

⛔ **本腳本原本用 REST 的 ``gh api rate_limit`` 量，卻把差值叫做 ``graphql_cost``。**
那個端點量不到 GraphQL 消耗：實測同一時刻它與 GraphQL 兩個狀態並存（REST 說
``used=0/remaining=5000``、GraphQL 說 ``used=73``），40 次連讀有 4 次讀到後者，
序列非單調（5000 → 4935 → 5000），跑完 20 次 ``ensure_fields`` 後可算出 **−76 點**。
⇒ 名字說是 GraphQL 成本、儀器卻是 REST，查核者重跑時它**錯報 0**。

⭐ 現版一律走 ``quota.py``（GraphQL 自身的 ``rateLimit`` 欄位，同一請求內評估，
連讀 6 次完全一致），且成本以 **``used`` 的差值**計算而非 ``remaining``——
``used`` 單調遞增，``remaining`` 會因跨越 reset 而回跳成負成本。

⚠️ 量測前後各跑一次控制組（什麼都不做的前後量測，差值須為 0）：本專案量測期間
常有並行的另一個 GitHub 消費者，控制組不為 0 時本次成本數字**含他人用量**，
⛔ 不得當成本腳本自己的成本引用。

⛔ **不得由本檔的成本數字推出前兩批的成本**：前兩批是用壞掉的 REST 儀器量的，
⇒ 只能重量，不能校正（見 ``quota.py`` 模組 docstring）。
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "cli" / "src"))

import quota as _quota_mod  # noqa: E402
from wf_cli.gh import default_runner  # noqa: E402
from wf_cli.project import list_items, resolve_project  # noqa: E402


def graphql_used() -> int:
    """已用 GraphQL 點數（權威）。⛔ 走 GraphQL ``rateLimit``，不走 REST ``rate_limit``。"""
    return _quota_mod.used()


def main() -> int:
    out_path = Path(sys.argv[1])
    _, _, ctrl_pre_ok = _quota_mod.control("（量測前）")
    before = graphql_used()
    project = resolve_project(default_runner, "ruan6047", 4)
    items = list_items(default_runner, project)
    after = graphql_used()
    _, _, ctrl_post_ok = _quota_mod.control("（量測後）")
    cost = after - before
    payload = {
        "project_url": project.url,
        "item_count": len(items),
        # ⭐ 欄位名與儀器一致：這是 GraphQL 自身 rateLimit 的 used 差值。
        "graphql_used_before": before,
        "graphql_used_after": after,
        "graphql_cost": cost,
        "quota_source": "graphql rateLimit (quota.py)",
        # 控制組不通過 ⇒ 有並行消費者或跨越 reset，cost 含他人用量。
        "quota_control_ok": ctrl_pre_ok and ctrl_post_ok,
        "items": [asdict(i) for i in items],
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    note = "" if (ctrl_pre_ok and ctrl_post_ok) else "　⚠️ 控制組不通過，成本含他人用量"
    print(f"items={len(items)} graphql_cost={cost}（used {before}→{after}）out={out_path}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
