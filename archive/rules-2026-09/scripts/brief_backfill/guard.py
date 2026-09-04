#!/usr/bin/env python3
"""A5 紅線：呼叫 ``wfcli amend --brief`` **之前**自行拒收分行字元。

依據（卡面 A5，2026-08-26 真實卡面往返實測）：``amend_brief`` 對 ``str.splitlines()``
認得的字元**全穿**，連 ``\\n`` 都不擋。含 ``\\n## Log`` 的值會使卡面出現兩個
``## Log`` ⇒ 該卡當場變成 ``aiwf#15`` 那個**永久不可修改**的狀態。

⚠️ 卡面 A5 寫「11 個字元」，本模組導出的是 **10 個**。⛔ 兩者不衝突：CPython 文件把
``\\r\\n`` 也列為一個行界，那是**兩字元序列**不是第 11 個字元；``\\r`` 與 ``\\n`` 各自
都在這 10 個裡 ⇒ 覆蓋完整。（``prove_guard_load_bearing.py`` 對這 10 個逐一實跑。）

⭐ 字元集合**由 ``str.splitlines()`` 自身導出**，⛔ 不手打清單——手打的清單會漏，
而漏掉的那一個正是會 brick 卡的那一個（本 repo 已有「手打哨兵常數」造成假陰性的前例）。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cli" / "src"))

from wf_cli.brief import validate_shape  # noqa: E402


def _derive_line_breaking_chars() -> frozenset[str]:
    """掃 BMP，凡使 ``str.splitlines()`` 產生 >1 段者即為分行字元。

    ⛔ 不寫死 ``\\n\\r\\v\\f…``——那是「開放集合當封閉集合用」的形狀，
    本 repo 已證實會漏（同族三次）。這裡改成**封閉集合由行為導出**。
    """
    out = set()
    for cp in range(0x110000):
        ch = chr(cp)
        if len(f"a{ch}b".splitlines()) > 1:
            out.add(ch)
    return frozenset(out)


LINE_BREAKING_CHARS = _derive_line_breaking_chars()


#: Project v2 TEXT 欄位的上限，單位是 **UTF-8 位元組**，⛔ 不是字元。
#:
#: 2026-08-26 於本卡先導批實測（10 張真實卡面往返）：1,012 B／524 字元寫得進去、
#: 1,025 B／531 字元被 GraphQL 拒為
#: ``Column value must be a valid value for text column``；另有 1,045 B／**439 字元**
#: 也被拒 ⇒ **判準是位元組不是字元**（若是字元，439 與 531 都該過）。
#: ⚠️ 實測只夾出真實上限 L 落在 **[1012, 1024]**（1012 B 成功、1025 B 失敗）。
#: ⛔ **本常數取的是「實際寫成功過的最大值」1012，不是推測的 1024。**
#: 1024 是這種欄位常見的整數上限、看起來很像答案，但**沒有量到**——若 L 其實是
#: 1013，門檻設 1024 會讓 1014–1024 B 的值照樣壞掉，而壞法是靜默的（見下）。
#: ⛔ 未再往下細探：細探要在真實卡面上做狀態面寫入，而唯一寫入通道是 wfcli。
#:
#: ⭐ **這條非有不可**：超限時 ``amend`` 的 body 已寫成功、只有欄位寫入失敗，
#: 而 CLI 回 rc=2（其 docstring 逐字寫「未寫入任何狀態」）⇒ **退出碼會騙人**，
#: 卡片落入 ``brief.drifted`` 的「body 有簡介但欄位是空的」，正是 ``#140`` 那個
#: 需要另一條修復路徑的狀態。先導批 10 張撞了 3 張。
FIELD_BYTE_LIMIT = 1012


class BriefRejected(ValueError):
    """簡介文字在寫入前被本地守衛拒收（⛔ 未呼叫 amend、未寫入任何狀態）。"""


def assert_writable(text: str) -> None:
    """A5 的拒收。⛔ 任何寫入路徑都必須先過這裡。"""
    bad = sorted({ch for ch in text if ch in LINE_BREAKING_CHARS})
    if bad:
        raise BriefRejected(
            "簡介含 str.splitlines() 認得的分行字元 "
            f"{[hex(ord(c)) for c in bad]}；⛔ 拒絕呼叫 amend——"
            "amend_brief 不擋這些字元，寫進去會讓卡面出現第二個 `## Log`，"
            "該卡將永久不可修改（aiwf#15 的狀態）"
        )
    nbytes = len(text.encode("utf-8"))
    if nbytes > FIELD_BYTE_LIMIT:
        raise BriefRejected(
            f"簡介 {nbytes} UTF-8 位元組（{len(text)} 字元）超過 Project TEXT 欄位上限 "
            f"{FIELD_BYTE_LIMIT} B；⛔ 拒絕呼叫 amend——超限時 body 會寫成功而欄位寫入失敗，"
            "CLI 卻回 rc=2 宣稱「未寫入任何狀態」，卡片會落入雙居所漂移"
        )
    # 形狀由 canonical 的實作驗，⛔ 不在此重寫（brief.validate_shape）。
    validate_shape(text)


def a6_named_targets(text: str) -> list[str]:
    """A6：``⛔ 非射程：`` 之後有沒有指向卡外的具名對象。⭐ **篩不是閘**。"""
    import re

    marker = "⛔ 非射程："
    idx = text.find(marker)
    tail = text[idx + len(marker) :] if idx >= 0 else ""
    pats = {
        "卡ID": r"\b[A-Z][A-Z0-9]+(?:-[A-Z0-9]+){1,}\b",
        "issue號": r"\b(?:aiwf|cpbl)#\d+|(?<![\w#/-])#\d+",
        "檔路徑": r"[\w./-]+\.(?:py|md|sql|json|ts|tsx|toml|sh|yml|yaml)\b",
        "節號": r"§[\d.]+",
        "API路由": r"/(?:api|games|players|teams)[\w/\[\]-]*",
    }
    hits = []
    for kind, pat in pats.items():
        for m in re.findall(pat, tail):
            hits.append(f"{kind}:{m if isinstance(m, str) else m[0]}")
    return sorted(set(hits))


if __name__ == "__main__":
    print(f"導出的分行字元集合（{len(LINE_BREAKING_CHARS)} 個）：")
    for ch in sorted(LINE_BREAKING_CHARS):
        print(f"  U+{ord(ch):04X}  {ch!r}")
