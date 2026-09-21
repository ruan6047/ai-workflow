"""值域的唯一居所是 rules/core/values.md；本模組只做機械抽取。

⛔ 不在程式碼內建任何值——內建等於幫值域開第二個居所。
"""

from __future__ import annotations

import re
from pathlib import Path

from wfx.core.errors import LayerMissing, ValueNotInDomain
from wfx.core.rules import read_doc

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
