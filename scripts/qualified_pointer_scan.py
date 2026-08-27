#!/usr/bin/env python3
# LIFECYCLE: standing · 常設工具——這就是給你跑的；不要刪
r"""合格指標的目標存在性掃描器（WF-CANONICAL-SELF-STALENESS1）。

## 這支腳本回答的問題

散文與註解指名**別的來源檔**的某一行時，寫的是「路徑 ＋ 冒號 ＋ 行號」。被指的
那個檔每一次插行、刪行、搬移，那個數字都會**靜默失準**——不報錯、不轉紅，只是
從此指到別的東西。這與 canonical 的行號腐爛是同一個病，只是被指的檔不同。

``scripts/canonical_citation_scan.py`` 已經在管「指向 canonical 的行號」，而它的
模組 docstring **自己具名放棄**了這一塊（逐字：指名別的來源檔的行號「同樣會腐爛，
但它不是本卡射程，且它們**被剪掉當成雜訊**——本腳本對它們一無所知」）。本腳本
接手的正是那塊具名殘料。

## 判準：收窄形態、放大射程

兩個軸刻意往相反方向走：

- **形態收窄成「合格指標」**：路徑與行號**必須相鄰**（中間不得有任何字元），且
  副檔名必須是本 repo 實際存在的副檔名之一。⛔ **不用回看窗。**
- **檔案射程放大成全 repo 開放集合**：``git ls-files`` 全掃，新增的檔自動納管，
  ⛔ 不維護白名單（白名單漏過真實缺陷，見既有掃描器的模組 docstring）。

### 為什麼不用回看窗（實測，⛔ 不是偏好）

回看窗 k=1（允許路徑與行號之間隔一個 token）在本 repo 的實測是**誤綁的主要來源**：
它會把資源宣告 ``["file:a.py", "port:8080"]`` 這種**同一個字串裡兩個不相干的冒號值**
綁成一組指標。跑 ``--census`` 可以在當下的樹上重現這個對照：k=0 的誤綁數與 k=1
新增的綁定各是多少、每一筆長什麼樣，都印出來給人逐筆看。

⚠️ **k=0 的代價要說準**：未指名目標的裸「冒號 ＋ 數字」（節次夾行號、時間、格式
規格、字典字面值……）**全部不在射程**。它們今天有幾個由 ``--census`` 印出來——
⛔ **本腳本對它們一無所知**，⛔ 不得把本腳本全綠讀成「這個 repo 沒有壞掉的行號」。

## 五種裁決（fail-closed，⛔ 沒有「跳過」）

- ``ok``：目標檔存在、行號在範圍內、該行非空。
- ``F1``：路徑解析不到任何被追蹤檔。
- ``F2``：行號超出目標檔長度（或小於 1）。
- ``F3``：目標行是空行——⭐ 這是**漂移最常見的落點**，插行把目標推走之後，原本的
  行號往往落在段落之間的空行上。
- ``F4``：路徑同時對應到多個被追蹤檔（例如只寫檔名而 repo 裡有同名檔）。⛔ 猜一個
  等於製造假綠，所以判紅要求作者寫全路徑。

裁決全部由「repo 現況」導出，⛔ 沒有任何一個是釘死的常數 ⇒ 世界改變時它會自己
改變答案。

## 豁免登記簿（``EXEMPTIONS``）

刻意寫壞的指標（例如另一支腳本的 docstring 拿「不存在的檔」當示範佔位）必須具名
登記並寫明理由，⛔ 不得靠「掃不到」蒙混。三件性質是刻意的：

1. **鍵不含來源行號。** 鍵是 ``(來源檔, sha256(來源行去頭尾空白後的文字), 指標
   token)``。⭐ 若鍵用來源行號，登記簿本身就是一份會腐爛的行號——那是本腳本要治的
   病，不能自己犯。行搬家仍然命中；**行的文字被改動則該條目自動變成死條目**而
   轉紅，要求重新裁決。
2. **條目必須是 load-bearing 的。** 沒有實際擋下任何裁決的條目是死條目，測試逐項
   指名要求刪除（見 ``cli/tests/test_qualified_pointer_scan.py``）。⭐ 這條同時是
   **本腳本今日全綠不是零資訊**的證明：把核心裁決拿掉（讓 ``judge`` 恆回 ``ok``），
   兩個豁免條目立刻變死條目而轉紅。
3. **登記簿解析失敗一律紅。** ``validate_exemptions`` 對格式不合的條目直接拋錯，
   ⛔ 不靜默略過；登記簿是模組內的 dict，構造上不存在「檔案不見了」這種狀態。

## ⚠️ 本腳本驗不到什麼（明說，⛔ 不得當成比實際可靠）

- **⛔ 沒有做「目標內容變了」的偵測（V9 的 T3）。** 本腳本只問「目標行存不存在、
  是不是空的」，⛔ 不問「那一行還是不是當初被指的那一行」。⇒ 它**只抓漂移到空行
  或超出檔長的那一種**；漂移之後恰好落在另一行非空內容上的，**本腳本全綠**。
  ⇒ 任何由本腳本得到的紅數都是**下界**，⛔ 不是當日漂移總量。
- **未指名目標的裸「冒號 ＋ 數字」不在射程**（見上方 k=0 的代價）。已知該族包含
  「節次 ＋ 冒號 ＋ 行號」這種寫法。
- **副檔名必須是本 repo 既有的副檔名。** 指向 repo 裡不存在的檔案類型（例如一個
  沒有任何同型檔案的副檔名）的指標會被當成雜訊放掉。這個過濾器擋掉的 token 每次
  都印出計數，``--all`` 逐筆列出，⛔ 不靜默。
- **只看 ``git ls-files``**：未追蹤檔、非 UTF-8 檔不在射程。讀不到的檔列進
  ``unreadable`` 並由測試斷言為空，⛔ 不靜默略過。
- **不驗指得對不對。** 目標行非空即算過；那一行講的是不是引用者說的那件事，本腳本
  沒有意見。

## 什麼結果會讓本腳本的判定不成立（反證條件）

- **開放集合**：新增一個帶壞指標的檔後重跑，它沒有出現在輸出裡 → 判定不成立。
- **鑑別力**：把核心裁決換成恆 ``ok`` 之後，真實 repo 仍然全綠 → 本腳本是零資訊
  檢查，判定不成立。
- **豁免不是垃圾桶**：某個豁免條目拿掉之後輸出沒有多出對應的紅 → 那是死條目。
- **k=0 純度**：``--census`` 在當下的樹上出現任何一筆 k=0 誤綁 → 形態選錯。

用法::

    python3 scripts/qualified_pointer_scan.py            # 從 repo root 掃，有紅回 1
    python3 scripts/qualified_pointer_scan.py --all      # 連豁免與被過濾的 token 一起列
    python3 scripts/qualified_pointer_scan.py --census    # 印 k=0／k=1 對照與放掉的那一族
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

#: 合格指標：路徑 ＋ 冒號 ＋ 行號，**中間不得有任何字元**（k=0）。
#:
#: ⚠️ 副檔名只吃「字母開頭」的，因此版本號（點後面是數字）不會被誤認成路徑。
#: 真正把格式規格（f-string 的 ``{值:寬度}``）擋掉的不是這條 regex，是下面那層
#: 「副檔名必須是本 repo 既有副檔名」的過濾——⛔ 這條 regex 本身抓得到它們。
_POINTER = re.compile(r"([A-Za-z0-9_./-]+\.([A-Za-z][A-Za-z0-9]*)):(\d+)")

#: 完整 ISO 8601 日期時間。事件留痕行的時、分、秒不是行號；剪得這麼完整是為了
#: 不誤傷「節次 ＋ 冒號 ＋ 行號」（既有掃描器踩過這個坑並留下測試）。
_ISO_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:?\d{2}|Z)?")

#: 任何「冒號 ＋ 數字」。只在 ``--census`` 用來量「k=0 放掉了多少」。
_COLON_NUMBER = re.compile(r":\d+")

#: 像路徑的 token（不帶行號）。只在 ``--census`` 的 k=1 對照組用。
_PATHISH = re.compile(r"[A-Za-z0-9_./-]+\.([A-Za-z][A-Za-z0-9]*)")

VERDICT_OK = "ok"
VERDICT_UNRESOLVABLE = "F1_目標解析不到"
VERDICT_OUT_OF_RANGE = "F2_行號超出檔長"
VERDICT_EMPTY_TARGET = "F3_目標行為空"
VERDICT_AMBIGUOUS = "F4_目標不唯一"

#: 五種裁決的完整集合。⛔ 沒有第六種「跳過」——不在射程的 token 根本不會變成
#: ``Finding``，進到這裡的每一筆都拿得到裁決。
VERDICTS = (
    VERDICT_OK,
    VERDICT_UNRESOLVABLE,
    VERDICT_OUT_OF_RANGE,
    VERDICT_EMPTY_TARGET,
    VERDICT_AMBIGUOUS,
)


def pointer_token(path: str, lineno: int) -> str:
    """組出一個合格指標的字面。

    ⚠️ **存在的唯一理由是不讓本檔自己出現字面上的合格指標。** 本腳本掃全 repo、
    包含它自己與它的測試；寫字面值會被自己抓到。登記簿的鍵、測試的樣本一律經由
    這支組裝。
    """
    return f"{path}:{lineno}"


def exemption_key(source: str, source_line: str, token: str) -> tuple[str, str, str]:
    """豁免登記簿的鍵：``(來源檔, sha256(來源行), 指標 token)``。

    ⭐ **刻意不含來源行號。** 用行號當鍵等於在治行號腐爛的腳本裡再種一份行號；
    行搬家會讓條目失效，而失效的方向是「靜默放行」——最壞的那種。

    ``source_line`` 取 ``strip()`` 之後再雜湊：縮排調整不該逼人重新裁決，內容改動
    則必須。
    """
    digest = hashlib.sha256(source_line.strip().encode("utf-8")).hexdigest()
    return (source, digest, token)


#: **豁免登記簿。每一項都要寫清楚為什麼，⛔ 不只是列進來。**
#:
#: ⚠️ 這裡不是垃圾桶：「我不想修它」不是理由。每一項都必須是**修了反而錯**的格，
#: 而且必須是**用得上的**——測試會逐項檢查它是否真的擋下了一筆裁決，沒擋到的判死
#: 條目、必須刪除。
#:
#: 今日兩項，同源：``scripts/canonical_citation_scan.py`` 的模組 docstring 拿兩個
#: **刻意不存在**的檔當示範佔位，用來說明「本腳本對這一族一無所知」。那兩個字面
#: 就是那段論證本身，⛔ 改掉它們等於改掉那支腳本的自述。
#:
#: ⚠️ 下面兩條的「來源行原文」一律**用 ``pointer_token`` 拼接**，⛔ 不寫字面——本檔
#: 自己也在射程內，寫字面會被自己抓到，而那會逼出一條「豁免自己的豁免」的遞迴。
EXEMPTIONS: dict[tuple[str, str, str], str] = {
    exemption_key(
        "scripts/canonical_citation_scan.py",
        "- **不驗 canonical 之外的引用**。``"
        + pointer_token("templates/foo.md", 12)
        + "`` 這種指名別的來源檔的",
        pointer_token("templates/foo.md", 12),
    ): (
        "既有掃描器模組 docstring 的刻意示範佔位：它拿一個不存在的檔說明自己「對這一族"
        "一無所知」。該字面即論證本身，改掉它等於改掉那支腳本的自述（本卡 A3／V15 明令不得動）。"
    ),
    exemption_key(
        "scripts/canonical_citation_scan.py",
        "#: 指名了來源檔的引用（``"
        + pointer_token("doctor.py", 211)
        + "``、``"
        + pointer_token("templates/bar.md", 9)
        + "``）。它們指的不是",
        pointer_token("templates/bar.md", 9),
    ): (
        "同上，這是 `_QUALIFIED_REF` 常數就地說明裡的第二個刻意佔位；同一行另一個指標指向"
        "真實存在的檔並照常受檢，⇒ 豁免的射程是這一個 token，⛔ 不是整行（本卡 A3／V15 明令不得動）。"
    ),
}


@dataclass(frozen=True)
class Pointer:
    """一個合格指標 token 在某一行裡的位置與內容。純資料，⛔ 不含裁決。"""

    token: str
    path: str
    lineno: int
    start: int


@dataclass(frozen=True)
class Rejected:
    """被「副檔名不是本 repo 既有副檔名」擋掉的 token。**明說，⛔ 不靜默。**"""

    source: str
    source_lineno: int
    token: str
    extension: str


@dataclass(frozen=True)
class Finding:
    """一筆已裁決的指標。"""

    source: str
    source_lineno: int
    token: str
    verdict: str
    target: str | None = None
    detail: str = ""
    exempted_by: tuple[str, str, str] | None = None

    def render(self) -> str:
        mark = " [豁免]" if self.exempted_by else ""
        where = f" → {self.target}" if self.target else ""
        detail = f" {self.detail}" if self.detail else ""
        return (
            f"{self.source} 第 {self.source_lineno} 行: "
            f"[{self.verdict}]{mark} {self.token}{where}{detail}"
        )


@dataclass(frozen=True)
class Report:
    findings: tuple[Finding, ...]
    rejected: tuple[Rejected, ...]
    unreadable: tuple[str, ...]
    scanned_files: int
    extensions: frozenset[str]

    @property
    def blocking(self) -> tuple[Finding, ...]:
        return tuple(
            f for f in self.findings if f.verdict != VERDICT_OK and f.exempted_by is None
        )

    @property
    def exempted(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.exempted_by is not None)

    @property
    def dead_exemptions(self) -> tuple[tuple[str, str, str], ...]:
        """登記了卻沒擋下任何東西的條目。⭐ 這就是 ratchet 的第二向。"""
        used = {f.exempted_by for f in self.findings if f.exempted_by is not None}
        return tuple(sorted(set(EXEMPTIONS) - used))


# ==========================================================================
# 純函式層：只吃字串與 mapping，⛔ 不碰檔案系統，⛔ 不跑 git
# ==========================================================================


def tracked_extensions(paths: Iterable[str]) -> frozenset[str]:
    """從被追蹤檔清單導出「本 repo 的副檔名宇宙」。

    ⭐ **這是機械導出的封閉集合，⛔ 不是人挑的白名單。** 新增一種副檔名的檔案，
    指向它的指標自動納管；⛔ 沒有人需要記得改這裡。
    """
    exts: set[str] = set()
    for rel in paths:
        name = rel.rsplit("/", 1)[-1]
        if "." in name:
            ext = name.rsplit(".", 1)[-1].lower()
            if ext:
                exts.add(ext)
    return frozenset(exts)


def find_pointers(
    line: str, extensions: frozenset[str]
) -> tuple[tuple[Pointer, ...], tuple[tuple[str, str], ...]]:
    """抽出一行裡的合格指標。回傳（命中, 被副檔名過濾掉的 (token, ext)）。

    ⚠️ 純函式、只吃一行字串與副檔名集合：判準因此可以用合成輸入直接測，⛔ 不必
    準備一棵 repo。

    先剪掉完整 ISO 時戳再抽——留痕行的時分秒不是行號。剪的是**整段時戳**並補回
    等長空白，位移因此不變。
    """
    masked = _ISO_TIMESTAMP.sub(lambda m: " " * len(m.group(0)), line)
    hits: list[Pointer] = []
    rejected: list[tuple[str, str]] = []
    for match in _POINTER.finditer(masked):
        path, ext, num = match.group(1), match.group(2), match.group(3)
        if ext.lower() not in extensions:
            rejected.append((match.group(0), ext))
            continue
        hits.append(
            Pointer(token=match.group(0), path=path, lineno=int(num), start=match.start())
        )
    return tuple(hits), tuple(rejected)


def resolve_path(path: str, tracked: Sequence[str]) -> tuple[str, ...]:
    """把指標裡的路徑對到被追蹤檔。

    兩段式，⛔ 不猜：**完整路徑**優先；否則吃**路徑結尾**（沿元件邊界），命中多於
    一個就回多個交給裁決層判 ``F4``。⛔ 不做模糊比對、⛔ 不做最短距離。
    """
    needle = path[2:] if path.startswith("./") else path
    if needle in tracked:
        return (needle,)
    suffix = "/" + needle
    return tuple(rel for rel in tracked if rel.endswith(suffix))


def judge(
    source: str,
    source_lineno: int,
    pointer: Pointer,
    lines_by_path: Mapping[str, Sequence[str]],
) -> Finding:
    """對一個合格指標下裁決。**純函式**：目標樹以 mapping 餵進來。

    ⛔ 五種裁決都會回傳 ``Finding``，⛔ 沒有回 ``None`` 的路徑——「看不懂所以跳過」
    是靜默失敗，本函式構造上做不到。
    """
    candidates = resolve_path(pointer.path, tuple(lines_by_path))
    if not candidates:
        return Finding(
            source, source_lineno, pointer.token, VERDICT_UNRESOLVABLE,
            detail="（沒有任何被追蹤檔對得上這個路徑）",
        )
    if len(candidates) > 1:
        return Finding(
            source, source_lineno, pointer.token, VERDICT_AMBIGUOUS,
            detail=f"（同時對到 {len(candidates)} 個檔：{'、'.join(sorted(candidates))}）",
        )
    target = candidates[0]
    lines = lines_by_path[target]
    if pointer.lineno < 1 or pointer.lineno > len(lines):
        return Finding(
            source, source_lineno, pointer.token, VERDICT_OUT_OF_RANGE, target,
            detail=f"（該檔共 {len(lines)} 行）",
        )
    if not lines[pointer.lineno - 1].strip():
        return Finding(
            source, source_lineno, pointer.token, VERDICT_EMPTY_TARGET, target,
            detail="（指到空行——插行漂移最常見的落點）",
        )
    return Finding(source, source_lineno, pointer.token, VERDICT_OK, target)


def validate_exemptions(exemptions: Mapping[object, object]) -> None:
    """登記簿格式檢查。**fail-closed：格式不合直接拋錯，⛔ 不靜默略過。**

    這一段就是 V10 第五種（「登記簿缺檔或解析失敗一律紅」）在本腳本裡的落點：
    登記簿是模組內的 dict，⛔ 沒有「檔案不見了」這種狀態，而**內容壞掉會炸**。
    """
    for key, reason in exemptions.items():
        if not isinstance(key, tuple) or len(key) != 3:
            raise ValueError(f"豁免鍵必須是三元組（來源檔, sha256, token）：{key!r}")
        source, digest, token = key
        if not isinstance(source, str) or not source:
            raise ValueError(f"豁免鍵的來源檔必須是非空字串：{key!r}")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"豁免鍵的第二欄必須是 sha256 十六進位摘要：{key!r}")
        if not isinstance(token, str) or not _POINTER.fullmatch(token):
            raise ValueError(f"豁免鍵的第三欄必須是一個合格指標 token：{key!r}")
        if not isinstance(reason, str) or len(reason) < 40:
            raise ValueError(f"豁免項 {key!r} 的理由過短，看不出為什麼不該納管")


def scan_text(
    source: str,
    text: str,
    lines_by_path: Mapping[str, Sequence[str]],
    extensions: frozenset[str],
    *,
    exemptions: Mapping[tuple[str, str, str], str] | None = None,
    apply_exemptions: bool = True,
) -> tuple[tuple[Finding, ...], tuple[Rejected, ...]]:
    """掃一份檔案內容並逐筆裁決。**純函式**——目標樹與副檔名宇宙都是參數。"""
    return scan_lines(
        source, text.splitlines(), lines_by_path, extensions,
        exemptions=exemptions, apply_exemptions=apply_exemptions,
    )


def scan_lines(
    source: str,
    source_lines: Sequence[str],
    lines_by_path: Mapping[str, Sequence[str]],
    extensions: frozenset[str],
    *,
    exemptions: Mapping[tuple[str, str, str], str] | None = None,
    apply_exemptions: bool = True,
) -> tuple[tuple[Finding, ...], tuple[Rejected, ...]]:
    """``scan_text`` 的逐行版。真實樹層走這一支，⛔ 不再 join 回字串重切。"""
    table = EXEMPTIONS if exemptions is None else exemptions
    findings: list[Finding] = []
    rejected: list[Rejected] = []
    for lineno, line in enumerate(source_lines, 1):
        pointers, dropped = find_pointers(line, extensions)
        for token, ext in dropped:
            rejected.append(Rejected(source, lineno, token, ext))
        for pointer in pointers:
            finding = judge(source, lineno, pointer, lines_by_path)
            if finding.verdict != VERDICT_OK:
                key = exemption_key(source, line, pointer.token)
                if key in table:
                    if apply_exemptions:
                        finding = Finding(
                            finding.source, finding.source_lineno, finding.token,
                            finding.verdict, finding.target, finding.detail, key,
                        )
                    else:
                        finding = Finding(
                            finding.source, finding.source_lineno, finding.token,
                            finding.verdict, finding.target,
                            finding.detail + "（登記在豁免簿，本次刻意不套用）", None,
                        )
            findings.append(finding)
    return tuple(findings), tuple(rejected)


# ==========================================================================
# 真實樹層：``git ls-files`` 開放集合
# ==========================================================================


def tracked_files(root: Path) -> list[str]:
    """``git ls-files``。射程就是它——未追蹤檔不在內，模組 docstring 明說。"""
    out = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
    ).stdout
    return [line for line in out.splitlines() if line]


def read_tree(root: Path) -> tuple[dict[str, list[str]], list[str]]:
    """讀出整棵被追蹤樹。回傳（路徑 → 行清單, 讀不到的檔）。"""
    lines_by_path: dict[str, list[str]] = {}
    unreadable: list[str] = []
    for rel in tracked_files(root):
        try:
            lines_by_path[rel] = (root / rel).read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            unreadable.append(rel)
    return lines_by_path, unreadable


def scan_repo(root: Path, *, apply_exemptions: bool = True) -> Report:
    """全 repo 掃描。⚠️ 目標樹與來源樹是同一棵——指標指向的就是這個 repo 的檔。"""
    validate_exemptions(EXEMPTIONS)
    lines_by_path, unreadable = read_tree(root)
    extensions = tracked_extensions(lines_by_path)
    findings: list[Finding] = []
    rejected: list[Rejected] = []
    for rel, lines in lines_by_path.items():
        got, dropped = scan_lines(
            rel, lines, lines_by_path, extensions,
            apply_exemptions=apply_exemptions,
        )
        findings.extend(got)
        rejected.extend(dropped)
    return Report(
        findings=tuple(findings),
        rejected=tuple(rejected),
        unreadable=tuple(unreadable),
        scanned_files=len(lines_by_path) + len(unreadable),
        extensions=extensions,
    )


# ==========================================================================
# ``--census``：k=0 / k=1 對照，以及 k=0 放掉的那一族有多大
# ==========================================================================


@dataclass(frozen=True)
class Census:
    colon_numbers: int
    qualified: int
    released: int
    k1_extra: tuple[tuple[str, int, str, str, str], ...]

    @property
    def k0_coverage(self) -> float:
        return 0.0 if not self.colon_numbers else self.qualified / self.colon_numbers

    @property
    def k1_coverage(self) -> float:
        if not self.colon_numbers:
            return 0.0
        return (self.qualified + len(self.k1_extra)) / self.colon_numbers


def k1_extra_bindings(
    line: str, extensions: frozenset[str]
) -> tuple[tuple[str, str], ...]:
    """回看窗 k=1 **比 k=0 多綁到**的那些配對。回傳（路徑 token, 帶行號的 token）。

    做法：先把 k=0 的合格指標與 ISO 時戳挖掉，剩下的以空白切 token；某個 token 含
    「冒號 ＋ 數字」時，往回看**一個** token，那個 token 像路徑就綁。
    ⛔ 這支只在 ``--census`` 用來產生對照，⛔ 不參與任何裁決。
    """
    masked = _ISO_TIMESTAMP.sub(lambda m: " " * len(m.group(0)), line)

    def _blank(match: re.Match[str]) -> str:
        if match.group(2).lower() in extensions:
            return " " * len(match.group(0))
        return match.group(0)

    rest = _POINTER.sub(_blank, masked)
    tokens = rest.split()
    pairs: list[tuple[str, str]] = []
    for index, token in enumerate(tokens):
        if not _COLON_NUMBER.search(token) or index == 0:
            continue
        previous = tokens[index - 1]
        match = _PATHISH.search(previous)
        if match and match.group(1).lower() in extensions:
            pairs.append((previous, token))
    return tuple(pairs)


def census(root: Path) -> Census:
    lines_by_path, _ = read_tree(root)
    extensions = tracked_extensions(lines_by_path)
    colon_numbers = 0
    qualified = 0
    extra: list[tuple[str, int, str, str, str]] = []
    for rel, lines in lines_by_path.items():
        for lineno, line in enumerate(lines, 1):
            masked = _ISO_TIMESTAMP.sub(lambda m: " " * len(m.group(0)), line)
            colon_numbers += len(_COLON_NUMBER.findall(masked))
            hits, _dropped = find_pointers(line, extensions)
            qualified += len(hits)
            for previous, token in k1_extra_bindings(line, extensions):
                extra.append((rel, lineno, previous, token, line.strip()))
    return Census(
        colon_numbers=colon_numbers,
        qualified=qualified,
        released=colon_numbers - qualified,
        k1_extra=tuple(extra),
    )


def _print_census(data: Census) -> None:
    print("=== k=0 / k=1 對照（在當下這棵樹上重量，⛔ 不是抄來的定值）===")
    print(f"「冒號 ＋ 數字」總數（已剪 ISO 時戳）：{data.colon_numbers}")
    print(f"k=0 合格指標（路徑與行號相鄰）：{data.qualified}"
          f"　⇒ 覆蓋 {data.k0_coverage:.1%}")
    print(f"k=0 放掉的一族（未指名目標的裸「冒號 ＋ 數字」）：{data.released}"
          "　⚠️ ⛔ 本腳本對它們一無所知")
    print(f"k=1 回看窗比 k=0 多綁到：{len(data.k1_extra)}"
          f"　⇒ 覆蓋 {data.k1_coverage:.1%}")
    if data.k1_extra:
        print()
        print("k=1 多綁到的每一筆（逐筆列出供人裁決是不是誤綁）：")
        for rel, lineno, previous, token, text in data.k1_extra:
            print(f"  {rel} 第 {lineno} 行：[{previous}] ＋ [{token}]")
            print(f"      || {text[:160]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="掃描指名來源檔的行號指標是否還指得到東西")
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1], help="repo root"
    )
    parser.add_argument(
        "--all", action="store_true", help="連通過的指標與被副檔名過濾的 token 一起列（診斷用）"
    )
    parser.add_argument(
        "--no-exemptions",
        action="store_true",
        help="不套用豁免簿（診斷用）：用來確認被豁免的那幾筆今天是**被明文放行**、⛔ 不是被漏掉",
    )
    parser.add_argument(
        "--census", action="store_true", help="印 k=0／k=1 對照與被放掉的那一族有多大"
    )
    args = parser.parse_args(argv)

    if args.census:
        _print_census(census(args.root))
        return 0

    report = scan_repo(args.root, apply_exemptions=not args.no_exemptions)
    for finding in report.findings:
        if finding.verdict != VERDICT_OK or args.all:
            print(finding.render())
    for rel in report.unreadable:
        print(f"{rel}: [讀不到，未掃描]")
    if args.all and report.rejected:
        print()
        print("被「副檔名不是本 repo 既有副檔名」過濾掉的 token：")
        for item in report.rejected:
            print(f"  {item.source} 第 {item.source_lineno} 行：{item.token}"
                  f"（副檔名 {item.extension}）")

    # ⚠️ ``--no-exemptions`` 下每一項豁免都「沒擋到東西」，死條目檢查在該模式下
    # 構造上必然全紅 ⇒ 是零資訊，故只在正常模式跑。
    dead = () if args.no_exemptions else report.dead_exemptions
    print()
    print(f"掃描檔案數：{report.scanned_files}")
    print(f"合格指標（宇宙）：{len(report.findings)}")
    print(f"豁免：{len(report.exempted)}　登記簿：{len(EXEMPTIONS)} 項")
    print(f"可強制：{len(report.findings) - len(report.exempted)}")
    print(f"被副檔名過濾：{len(report.rejected)}")
    print(f"紅（不含豁免）：{len(report.blocking)}")
    if report.unreadable:
        print(f"⚠️ 讀不到：{len(report.unreadable)} 檔")
    if dead:
        print()
        print("⛔ 這些豁免項已無命中，是死條目，請刪除或重新裁決：")
        for key in dead:
            print(f"  {key[0]}　{key[2]}　sha256 {key[1][:12]}…")
    if report.blocking:
        print()
        print("指名來源檔的行號會隨那個檔插行而靜默失準——")
        print("改成「符號名或該行的實際字面」，或把行號更新到它今天真的在的位置。")
    return 1 if (report.blocking or dead) else 0


if __name__ == "__main__":
    sys.exit(main())
