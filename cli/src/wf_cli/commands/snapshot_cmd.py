"""``wfcli snapshot``：狀態面快照 export 回 git（JSON＋人類可讀 Ledger 渲染）。"""

from __future__ import annotations

import argparse
from pathlib import Path

from ..card import now_iso8601
from ..config import add_target_args, resolve_target
from ..gh import default_runner
from ..project import list_items, resolve_project
from ..snapshot import build_rows, render_json, render_markdown


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "snapshot", help="狀態面快照 export（JSON＋人類可讀 Ledger 渲染）"
    )
    add_target_args(p)
    p.add_argument(
        "--out-dir", required=True, help="輸出目錄（寫 snapshot.json 與 SNAPSHOT.md）"
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    target = resolve_target(
        owner=args.owner, project=args.project, repo=args.repo, config=args.config
    )
    runner = default_runner
    project = resolve_project(runner, target.owner, target.project)
    items = list_items(runner, project)
    rows = build_rows(items)

    ts = now_iso8601()
    json_str = render_json(rows, ts)
    md_str = render_markdown(rows, ts)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "snapshot.json"
    md_path = out_dir / "SNAPSHOT.md"
    json_path.write_text(json_str, encoding="utf-8")
    md_path.write_text(md_str, encoding="utf-8")

    print(f"[snapshot] {len(rows)} 張卡 → {json_path}, {md_path}")
    return 0
