"""值域的唯一居所是 rules/core/values.md；本模組只做機械抽取。

⛔ 不在程式碼內建任何值——內建等於幫值域開第二個居所。
"""

from __future__ import annotations

import re
from pathlib import Path

from wfx.core.errors import LayerMissing, ValueNotInDomain
from wfx.core.rules import read_doc

# 概念名 → values.md 的表格列名。**值本身只住 values.md**；本表只記兩處命名的對應，
# ⛔ 不是第二個值域居所。未列入者（owner／期限／Resource）⛔ 無值域。
# 唯一居所在此：`write`（寫入前檢值域）與 `adopt`（比對 Project 的 SingleSelect 選項）共用同一份，
# ⛔ 不保留第二份對照表。
DOMAINS = {'狀態': '狀態', '階段': '階段', '風險': '風險影響', '緊急性': '緊急性'}

_ROW = re.compile(r"^\|(?P<name>[^|]+)\|(?P<vals>[^|]+)\|\s*$")
_COUNT = re.compile(r"[（(]\s*\d+\s*[）)]\s*$")


def read_enums(rules_root: Path) -> dict[str, tuple[str, ...]]:
    text = read_doc(rules_root, "core/values.md")
    enums: dict[str, tuple[str, ...]] = {}
    for line in text.splitlines():
        m = _ROW.match(line.strip())
        if not m:
            continue
        name = _COUNT.sub("", m.group("name").strip()).strip()
        raw = m.group("vals").strip()
        if not name or set(raw) <= {"-", ":"} or "／" not in raw:
            continue
        enums[name] = tuple(v.strip() for v in raw.split("／") if v.strip())
    return enums


def domain(rules_root: Path, concept: str) -> tuple[str, ...]:
    values = read_enums(rules_root).get(concept)
    if not values:
        raise LayerMissing(
            "framework", "core/values.md", f"表格中找不到「{concept}」的值域"
        )
    return values


def check(rules_root: Path, concept: str, value: str) -> str:
    allowed = domain(rules_root, concept)
    if value not in allowed:
        raise ValueNotInDomain(concept, value, allowed)
    return value
