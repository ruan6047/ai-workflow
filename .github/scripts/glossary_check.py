#!/usr/bin/env python3
"""core/glossary.md 的表結構對帳。

只比字串集合與形狀，⛔ 不掃規則正文、⛔ 不判用詞對不對——用詞違規是查核者的
`governance` finding（`roles/conduct-common.md` §2 逐字「⛔ 不擋」）。

檢查三條：
  G1 同一個禁用字被多列登記時，限定字樣逐字一致。
  G2 僅大小寫不同的同一個字必須併在同一列。
  G3 限定字樣形狀：最多一組全形括號、括號內非空。
"""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GLOSSARY = ROOT / "core/glossary.md"
ROW = re.compile(r"^\|(.+)\|$", re.M)
EMPTY = {"—", "-", ""}


def entries(text: str) -> list[tuple[str, str, str]]:
    """(詞, 禁用字本體, 限定字樣) 逐條；表頭與分隔列不計。"""
    out = []
    for row in ROW.findall(text):
        c = [x.strip() for x in row.split("|")]
        if len(c) < 4 or c[3] == "禁用同義詞" or c[0].startswith("-"):
            continue
        if c[3] in EMPTY:
            continue
        for tok in re.split(r"[、,，]", c[3]):
            tok = tok.strip("` ")
            if not tok:
                continue
            base = tok.split("（")[0].strip()
            out.append((c[0], base, tok[len(base):]))
    return out


def check(text: str) -> list[str]:
    ent = entries(text)
    errs: list[str] = []
    reg: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    for term, base, qual in ent:
        reg[base].append((term, qual))
    for base, v in sorted(reg.items()):
        quals = {q for _, q in v}
        if len(v) > 1 and len(quals) > 1:
            errs.append(f"G1 {base}: 被 {sorted(t for t, _ in v)} 登記，限定不一致 {sorted(quals)}")
    low: dict[str, set[str]] = collections.defaultdict(set)
    for base in reg:
        low[base.lower()].add(base)
    for k, v in sorted(low.items()):
        if len(v) > 1:
            errs.append(f"G2 {k}: 僅大小寫不同的同字未併列 {sorted(v)}")
    for term, base, qual in ent:
        if qual and not re.fullmatch(r"（[^（）]+）", qual):
            errs.append(f"G3 {term}: 條目「{base}{qual}」限定字樣形狀不合")
    return errs


def selftest() -> int:
    bad = 0
    head = "| 詞 | 定義 | ⛔ 不是什麼 | 禁用同義詞 |\n|---|---|---|---|\n"
    cases = [
        ("selftest_clean", head + "| 甲 | d | n | x |\n| 乙 | d | n | x |\n", 0),
        ("selftest_G1_限定不一致", head + "| 甲 | d | n | x |\n| 乙 | d | n | x（作為甲） |\n", 1),
        ("selftest_G2_大小寫未併", head + "| 甲 | d | n | Foo |\n| 乙 | d | n | foo |\n", 1),
        ("selftest_G3_兩組括號", head + "| 甲 | d | n | x（a）（b） |\n", 1),
        ("selftest_G3_空括號", head + "| 甲 | d | n | x（） |\n", 1),
    ]
    for name, text, want in cases:
        got = len(check(text))
        ok = (got == want) if want == 0 else (got >= want)
        print(f"{name}: {'PASS' if ok else 'FAIL'}（errs={got}, 期望{'=' if want == 0 else '≥'}{want}）")
        bad += not ok
    return 1 if bad else 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest()
    text = GLOSSARY.read_text(encoding="utf-8")
    errs = check(text)
    for e in errs:
        print(f"⛔ 詞表對帳：{e}")
    print(f"詞表對帳：{len(entries(text))} 個禁用條目，失敗 {len(errs)}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
