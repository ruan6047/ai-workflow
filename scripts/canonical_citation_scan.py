#!/usr/bin/env python3
# LIFECYCLE: standing · 常設工具——這就是給你跑的；不要刪
r"""canonical 引用的行號掃描器（WF-BACKLOG-STAGE1）。

## 這支腳本回答的問題

散文與註解引用 canonical（``AI_WORKFLOW.md``）時寫「檔名 ＋ 冒號 ＋ 行號」，
而 canonical **每一次插行都會讓那些數字靜默失準**——不報錯、不轉紅，只是從此
指到別條規則。已經失準四輪：``#119`` 抓到既存漂移、``#120`` 自己在 §3.1 插兩行
把一批引用整批推歪、``#120`` R3 才改形狀、R5 又發現清單制漏了真實缺陷。

正解是引用**節次 ＋ 條文原文片段**：片段可以 grep，不需要知道它今天在第幾行。
本腳本負責讓「長回行號」這件事**轉紅**，而不是繼續爛在註解裡。

## 為什麼是全 repo 掃描，不是白名單

R3–R5 用的是**寫死的檔案清單**（``_PROSE_CITERS``）。那個形狀壞在構造上：新增
引用 canonical 的檔案不會自動納管，得有人記得手動加。**它已經漏掉過真實缺陷**
——``snapshots/README.md`` 與 ``scripts/daily_snapshot.sh`` 兩處都壞著、都不在
清單裡，前者 R5 才補、後者 R4 列「另有 N 處」時整個漏掉。

同族連三輪修不好就是形狀錯了。本腳本改成**開放集合**：``git ls-files`` 全掃，
不合格就紅；要不掃某個檔，必須在 ``EXCLUSIONS`` 具名並寫明理由，且該排除得是
**用得上的**（見 ``cli/tests/test_canonical_citation_scan.py`` 的 load-bearing
檢查——沒有命中的排除項會被判死條目而轉紅）。

## 判準（封閉集合，不追寫法）

不去窮舉「行號有幾種寫法」——節次後面夾一個行號、寫成「第 N 行」、寫成 ``L`` 加
數字、連檔名都不寫直接在 ``canonical`` 後面接冒號數字……都是同一件事，而 R4 實測
**寫法窮舉不完**（起初只掃「檔名加冒號數字」與反引號包住的冒號數字，漏了節次夾
行號與連反引號都沒有的那種）。改問一個封閉的問題：

⚠️ 上一段刻意**不寫出任何一個真的長成行號的字面例子**。本腳本掃全 repo，包含它
自己：舉一個字面例子就會被自己抓到。這不是潔癖——``cli/tests/test_doctor.py`` 的
舊註解正是因為寫了字面例子而在本輪轉紅。要造字面例子請照測試檔的做法用字串拼接。

**點名 canonical 的那一行，剪掉「已指名來源檔」的引用與「完整 ISO 時戳」之後，
還剩不剩冒號數字？**

剩下的必然是無主行號。兩條規則：

1. ``canonical 檔名 ＋ 冒號 ＋ 數字`` —— 直接命中，不必剪。
2. 剪除後仍有冒號數字 —— 無主行號。

### 為什麼剪 ISO 時戳，以及為什麼不能剪得更鬆

事件留痕行長成 ``<ISO 時戳> handoff by …``，其中時、分、秒之間的冒號數字是時間
不是行號。全 repo 實測有四行純粹因為時戳而誤判（``archive/tasks/`` 的 handoff 留痕）。

但**鬆散的時戳過濾會製造漏報**：R4 用過「一到兩位數字、冒號、兩位數字」這種過濾，
它會把「節次數字 ＋ 冒號 ＋ 三位行號」的前半段一起吃掉，於是一個真缺陷變成零命中。

所以這裡剪的是**完整 ISO 8601 日期時間**（``YYYY-MM-DDTHH:MM:SS`` ＋ 選配時區），
形態完整到不可能誤傷節次夾行號——節次夾行號沒有日期前綴，剪不到它。這條性質由
``test_iso_stripping_does_not_swallow_a_section_line_ref`` 釘住（該測試用字串拼接
造出真的長成節次夾行號的樣本），那正是 R4 踩過的坑。

## 什麼結果會讓本腳本的判定不成立（反證條件）

- **開放集合**：新增一個帶行號 canonical 引用的檔案後重跑，它沒有出現在輸出裡
  → 判定不成立。（測試以合成樹實測。）
- **排除集不是垃圾桶**：把 ``EXCLUSIONS`` 的某一項刪掉後重跑，輸出沒有多出該檔的
  命中 → 那項排除是死條目，判定不成立。（測試逐項實測。）
- **時戳剪除**：純時戳行被判成命中，或 ``§6:222`` 沒被判成命中 → 判定不成立。

## ⚠️ 本腳本驗不到什麼（明說，不得當成比實際可靠）

- **只驗形態，不驗指得對不對。** ``§4.1「一段 canonical 裡根本不存在的文字」``
  照樣全綠。散文片段的**逐字性完全沒有守衛**：本輪實測全 repo 有 47 段引號內容
  逐字命中 canonical、56 段沒有，但那 56 段絕大多數是中文行文的一般引號（如
  「我上次做了什麼」），不是引用。要驗散文逐字性得先發明一個機器可辨識的引用
  語法並全面改寫——**本輪沒做**，這是已知且尚未關閉的缺口。
- **``doctor.py`` 的三個具名錨點是例外**：它們有逐字＋唯一＋落在所引節次的守衛
  （``test_doctor.py::test_canonical_anchors_are_verbatim_and_in_the_cited_section``），
  但那只涵蓋那三個，不涵蓋任何散文片段。
- **條文語意被改寫而片段字串原封不動時仍然全綠。** 比對的是字串在不在，不是條文
  說了什麼。整條規則被反轉、只要那一小段主詞句還在，什麼都不會響。
- **只看 ``git ls-files``**：未追蹤檔、已刪除但仍被引用的路徑、以及非 UTF-8 檔
  都不在射程。讀不到的檔會列進 ``unreadable`` 並由測試斷言為空，不靜默略過。
- **不驗 canonical 之外的引用**。``templates/foo.md:12`` 這種指名別的來源檔的
  行號同樣會腐爛，但它不是本卡射程，且它們**被剪掉當成雜訊**——本腳本對它們
  一無所知。

用法：

    python3 scripts/canonical_citation_scan.py          # 從 repo root 掃，有命中回 1
    python3 scripts/canonical_citation_scan.py --all    # 連被排除的檔一起列（診斷用）
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

#: canonical 的檔名。全 repo 只有這一份，引用它的行號才是本腳本的射程。
CANONICAL_FILENAME = "AI_WORKFLOW.md"

#: 觸發檢查的關鍵字。一行要先「點名 canonical」才會被判定——``canonical`` 一詞
#: 也算，因為實測有引用連檔名都不寫（``scripts/daily_snapshot.sh`` 曾寫成
#: ``canonical`` 直接接冒號行號）。
_MENTIONS = (CANONICAL_FILENAME.removesuffix(".md"), "canonical")

#: 指名了來源檔的引用（``doctor.py:211``、``templates/bar.md:9``）。它們指的不是
#: canonical，canonical 插行動不到它們，故先剪掉再看該行還剩什麼。
_QUALIFIED_REF = re.compile(r"[A-Za-z0-9_./-]+\.[A-Za-z]+:\d+")

#: 完整 ISO 8601 日期時間。**刻意寫得這麼完整**：鬆散的 ``\d{1,2}:\d{2}`` 會吃掉
#: ``§6:222`` 造成漏報（R4 實測）。有日期前綴才剪，節次夾行號因此絕對倖免。
_ISO_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:?\d{2}|Z)?")

#: 剪完之後還剩的冒號數字＝無主行號。
_BARE_LINE_REF = re.compile(r":\d+")

#: canonical 自己被冠上行號。單獨一條，因為這形態會被 ``_QUALIFIED_REF`` 剪掉。
_CANONICAL_LINE_REF = re.compile(re.escape(CANONICAL_FILENAME) + r":\d+")

KIND_CANONICAL = "canonical帶行號"
KIND_BARE = "無主行號"

#: **具名排除集。每一項都要寫清楚為什麼，而不只是列進來。**
#:
#: ⚠️ 排除集不是垃圾桶：「我不想修它」不是排除理由。這裡的每一項都必須是
#: **修了反而錯**或**構造上不該納管**的檔；而且必須是**用得上的**——測試會逐項
#: 拿掉再掃，沒有命中的排除項判死條目、必須刪除（見
#: ``test_every_exclusion_is_load_bearing``）。
#:
#: ⚠️ **現在是空的，而空是正確的終點、⛔ 不是「還沒填」。** 唯一那一項
#: （``docs/CONTRACT_TOOL_RECONCILE.md``）的理由逐字寫著「要改的是產生器的輸出格式，
#: 不是這裡」；2026-08-27 產生器改成輸出 ``路徑::符號名``／``路徑 §節標題`` 之後，該檔
#: 一個行號錨點都不剩，排除項因此變成死條目，由
#: ``test_every_exclusion_is_load_bearing`` 指名要求刪除。
#: ⛔ 不得把它加回來當「暫時繞過」——加回來就得先讓它有命中，而有命中代表產生器又在
#: 輸出行號。
EXCLUSIONS: dict[str, str] = {}


@dataclass(frozen=True)
class Offence:
    """一筆命中。``path`` 是相對 repo root 的路徑。"""

    path: str
    lineno: int
    kind: str
    line: str
    excluded_by: str | None = None

    def render(self) -> str:
        mark = f" [排除：{self.excluded_by}]" if self.excluded_by else ""
        return f"{self.path}:{self.lineno}: [{self.kind}]{mark} {self.line.strip()}"


def line_offence_kinds(line: str) -> tuple[str, ...]:
    """這一行犯了哪幾種行號引用。沒點名 canonical 就一律空。

    ⚠️ 純函式、只吃一行字串：判準因此可以被合成輸入直接測，不必準備一棵 repo。
    """
    if not any(token in line for token in _MENTIONS):
        return ()
    kinds: list[str] = []
    if _CANONICAL_LINE_REF.search(line):
        kinds.append(KIND_CANONICAL)
    stripped = _ISO_TIMESTAMP.sub("", _QUALIFIED_REF.sub("", line))
    if _BARE_LINE_REF.search(stripped):
        kinds.append(KIND_BARE)
    return tuple(kinds)


def scan_text(path: str, text: str) -> list[Offence]:
    """掃一份檔案內容。``path`` 只用來標示，不影響判定（排除在呼叫端套用）。"""
    found: list[Offence] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for kind in line_offence_kinds(line):
            found.append(Offence(path=path, lineno=lineno, kind=kind, line=line))
    return found


def tracked_files(root: Path) -> list[str]:
    """``git ls-files``。射程就是它——未追蹤檔不在內，這一點在模組 docstring 明說。"""
    out = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
    ).stdout
    return [line for line in out.splitlines() if line]


def scan_repo(
    root: Path, *, apply_exclusions: bool = True
) -> tuple[list[Offence], list[str]]:
    """全 repo 掃描。回傳（命中清單, 讀不到的檔）。

    ``apply_exclusions=False`` 時**照樣掃排除集內的檔**，但把命中標記 ``excluded_by``
    而不是濾掉——測試靠這個判斷某項排除是不是死條目。
    """
    offences: list[Offence] = []
    unreadable: list[str] = []
    for rel in tracked_files(root):
        try:
            text = (root / rel).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            unreadable.append(rel)
            continue
        reason = EXCLUSIONS.get(rel)
        for offence in scan_text(rel, text):
            if reason is None:
                offences.append(offence)
            elif not apply_exclusions:
                offences.append(
                    Offence(offence.path, offence.lineno, offence.kind, offence.line, reason)
                )
    return offences, unreadable


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="掃描 canonical 引用是否帶行號")
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1], help="repo root"
    )
    parser.add_argument(
        "--all", action="store_true", help="連被排除的檔一起列（診斷用，不影響 exit code）"
    )
    args = parser.parse_args(argv)

    offences, unreadable = scan_repo(args.root, apply_exclusions=not args.all)
    blocking = [o for o in offences if o.excluded_by is None]

    for offence in offences:
        print(offence.render())
    for rel in unreadable:
        print(f"{rel}: [讀不到，未掃描]")

    print()
    print(f"掃描檔案數：{len(tracked_files(args.root))}")
    print(f"命中（不含排除）：{len(blocking)}")
    print(f"排除集：{len(EXCLUSIONS)} 項")
    if unreadable:
        print(f"⚠️ 讀不到：{len(unreadable)} 檔")
    if blocking:
        print()
        print("引用 canonical 只准「節次 ＋ 條文原文片段」，不准行號——")
        print("canonical 插行會讓行號靜默失準，而失準不會有任何東西報錯。")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
