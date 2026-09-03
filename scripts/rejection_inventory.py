#!/usr/bin/env python3
r"""拒絕訊息**清單**（`WF-REDESIGN-W3` 驗收 4 的 artifact 產生器）。

⛔ **本工具⛔ 非必須、⛔ 非權威產物。** 它只輸出**清單**（哪一個檔的哪一行有一則拒絕
訊息）。⛔ 不重建訊息文字、⛔ 不抽取指令、⛔ 不做任何判定——每一個衍生欄位在本卡都
至少錯過一次，⛔ 寧可不產生。判斷歸 AI／PM。需求方裁定見 ``ruan6047/ai-workflow#221``。

⛔ **本清單⛔ 不分辨命中落在訊息、註解還是 docstring**——那是內容判斷，歸 AI／PM。

## 為什麼砍成這樣（登記，⛔ 不是設計品味）

需求方 2026-09-03 原話逐字：「**如果有疑慮的機械產生資訊寧願不要 只需要確認該項目再
確認清單 交給ＡＩ處裡**」。依據是本卡的實測——**每一個衍生欄位都至少錯過一次**：

| 衍生欄位 | 它錯過的那一次 |
|---|---|
| ``mechanical.command`` | 只取第一條 ⇒ PM 的 10/13 誤判、漏掉 `assign_cmd:210` |
| ``statement``（AST） | artifact 缺陷 1–3：``#`` 註解對 AST 不可見，片段被撐成整個 `FunctionDef` |
| ``command_lines`` | R4 才補上；`R2-003` 之前三輪都因它未閉環 |
| ``cjk_value_lines`` | 執行者自陳「同時含真值」⇒ ⛔ 非判準 |
| ``placeholder_lines`` | 只認角括號 ⇒ 中文佔位進不去（R4「為何現有測試沒抓到」） |
| ``_render_text`` | 缺陷 7：相鄰字面被黏成一行，產出**實際不存在**的指令 |
| ``kind`` | ``docstring`` 那一格要 parse AST ⇒ 同屬「有疑慮的衍生資訊」 |

⇒ **唯一從沒錯過的是 ``file:line``。** 本腳本現在只產生它。

## 定位口徑＝釘死的 grep，⛔ 無 AST

卡面驗收 4 的量法逐字是
``grep -rnoE '\[[a-z-]+\] 拒[絕收]' --include='*.py' cli/src``（逐行、**逐 occurrence**）。
本腳本逐行 ``finditer`` 走同一口徑 ⇒ 總數逐位元一致。
⛔ **不用 ``ast`` 走訪**：那會把 ``JoinedStr`` 與它內部的 ``Constant`` 各算一次
（實測 109 vs 73）。本檔現在**完全沒有 import ast**。

## 兩層母體，⛔ 不得互相代用

| 層 | 定義 |
|---|---|
| **全集** | 釘死的 grep 的全部命中。⛔ 口徑不因任何分類而改。 |
| **可動母體** | 全集扣掉非射程的兩支 deploy 動詞檔（卡面逐字排除）。 |

⚠️ 從前有第三層「可補母體」（再扣註解與 docstring）——那一層倚賴 ``kind``，**已隨
``kind`` 一起移除**。需求方 2026-09-02「註解與 docstring **不是訊息**」的裁定
**⛔ 未失效**，它從「機械欄位」變成 **PM 逐則裁定裡的一行**（與「一則多態」的處理同構）。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

#: 卡面釘死的關鍵字量法，**逐字**。⛔ 不得放寬也⛔ 不得收窄——總數要與卡面的 grep 一致。
KEYWORD_RE = re.compile(r"\[[a-z-]+\] 拒[絕收]")

#: 卡面逐字排除的兩支 deploy 動詞檔。它們**進全集**、⛔ 不進可動母體。
OUT_OF_SCOPE_FILES = frozenset({"deploy_state_cmd.py", "deploy_declare_cmd.py"})


@dataclass
class Rejection:
    """清單的一列。**五個欄位全部直接來自那條 grep 或檔名**，⛔ 無任何推導。"""

    file: str
    #: 關鍵字出現的行號（1-indexed）。
    line: int
    #: ``[<verb>]`` 裡的動詞字面。
    verb: str
    #: 關鍵字字面（``拒絕`` 或 ``拒收``）。
    keyword: str
    #: 檔名是否落在 :data:`OUT_OF_SCOPE_FILES` 之外。⛔ 這是檔名比對，⛔ 不是內容判斷。
    in_scope: bool


def scan(src_root: Path) -> list[Rejection]:
    """逐檔逐行跑釘死的 grep。⛔ 不 parse、⛔ 不重建、⛔ 不判定。"""
    rows: list[Rejection] = []
    for path in sorted(src_root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in KEYWORD_RE.finditer(line):
                hit = match.group(0)
                rows.append(
                    Rejection(
                        file=str(path.relative_to(src_root.parent.parent)),
                        line=lineno,
                        verb=hit.split("]")[0].lstrip("["),
                        keyword=hit.split("] ")[1],
                        in_scope=path.name not in OUT_OF_SCOPE_FILES,
                    )
                )
    rows.sort(key=lambda r: (r.file, r.line))
    return rows


def summarise(rows: list[Rejection]) -> dict:
    """只有母體則數。⛔ 沒有任何「合格數」——機械只檢查「是否有」。"""
    per_file: dict[str, int] = {}
    for row in rows:
        per_file[row.file] = per_file.get(row.file, 0) + 1
    in_scope = [r for r in rows if r.in_scope]
    return {
        "total": len(rows),
        "in_scope": len(in_scope),
        "out_of_scope": len(rows) - len(in_scope),
        "per_file": dict(sorted(per_file.items(), key=lambda kv: -kv[1])),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="拒絕訊息清單（驗收 4 的 artifact 產生器）")
    parser.add_argument(
        "--src",
        default=None,
        help="cli/src 的路徑；預設由本檔位置推導（<repo>/cli/src）",
    )
    parser.add_argument("--json", action="store_true", help="stdout 只輸出 JSON")
    args = parser.parse_args(argv)

    src = Path(args.src) if args.src else Path(__file__).resolve().parents[1] / "cli" / "src"
    if not src.exists():
        print(f"[inventory] ⛔ 找不到語料目錄：{src}", file=sys.stderr)
        return 2

    rows = scan(src)
    summary = summarise(rows)
    payload = {
        "artifact": "wf-cli/rejection-inventory/v2",
        "keyword_regex": KEYWORD_RE.pattern,
        "corpus": str(src),
        "out_of_scope_files": sorted(OUT_OF_SCOPE_FILES),
        "summary": summary,
        "rows": [asdict(r) for r in rows],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"拒絕訊息全集：{summary['total']} 則")
    print(f"  可動母體（扣非射程 {summary['out_of_scope']} 則）：{summary['in_scope']}")
    print()
    print("逐檔：")
    for name, count in summary["per_file"].items():
        mark = " ⛔非射程" if Path(name).name in OUT_OF_SCOPE_FILES else ""
        print(f"  {count:3d}  {name}{mark}")
    print()
    print("⛔ 本清單只說「哪一行有一則拒絕訊息」。")
    print("   ⛔ 不重建訊息文字、⛔ 不抽取指令、⛔ 不分辨訊息／註解／docstring、⛔ 不判定。")
    print("   判斷歸 AI／PM（需求方裁定，ruan6047/ai-workflow#221）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
