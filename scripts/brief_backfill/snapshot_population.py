#!/usr/bin/env python3
"""唯讀：抓 Project #4 全母體並落地成 JSON 快照，供後續分析零額外額度重跑。

⛔ 不寫任何東西到 GitHub。⛔ 不用 ``gh project item-list``（中文欄位 key 編碼壞，
見 project.py:377）——一律走 ``wf_cli.project.list_items``，使盤點與守衛同源。
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cli" / "src"))

from wf_cli.gh import default_runner  # noqa: E402
from wf_cli.project import list_items, resolve_project  # noqa: E402


def graphql_remaining() -> int:
    out = subprocess.run(
        ["gh", "api", "rate_limit", "--jq", ".resources.graphql.remaining"],
        capture_output=True,
        text=True,
        check=True,
    )
    return int(out.stdout.strip())


def main() -> int:
    out_path = Path(sys.argv[1])
    before = graphql_remaining()
    project = resolve_project(default_runner, "ruan6047", 4)
    items = list_items(default_runner, project)
    after = graphql_remaining()
    payload = {
        "project_url": project.url,
        "item_count": len(items),
        "graphql_before": before,
        "graphql_after": after,
        "graphql_cost": before - after,
        "items": [asdict(i) for i in items],
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"items={len(items)} graphql_cost={before - after} out={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
