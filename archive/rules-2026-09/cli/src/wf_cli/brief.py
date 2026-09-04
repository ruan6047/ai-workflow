"""卡片簡介（canonical ``AI_WORKFLOW.md`` §6.3）的哨兵區塊、形狀驗證與雙居所導出。

簡介的用途是讓讀者**決定相關性**——⛔ 它不是摘要。形狀取自 AI skill 的
``description``：先「做什麼」，後「什麼時候該看這張卡」。

**兩個形狀要求**（皆為 CLI 可驗，見 :func:`validate_shape`）：

1. 必含 ``適用時機``——什麼情況下該先看這張卡。
2. 必含 ``⛔ 非射程：``——什麼不在本卡範圍。

⛔ **不設任何字數。** canonical §6.3 逐字：本專案曾以 70 個現存 skill ``description``
的長度分佈推導區間，而該母體未經品質檢查——實讀最短六個，全部只回答「這是什麼」、
沒有一個回答「什麼時候該用我」⇒ 由該母體導出的中位與百分位全部失真，四組數值整組撤回。

居所
----

**雙居所，比照 §4.4 的資源宣告**：body 哨兵區塊為**權威**、Project TEXT 欄位為
**恆等導出**（非摘要、非截斷）。寫入順序 **body 先、欄位後並讀回驗證**；失敗模式為
「body 已更新、欄位過期」，偵測方式為兩居所實際值**直接字串比對**（:func:`drifted`）。

⚠️ 恆等導出的第二個理由是偵測最簡單：直接字串比對，⛔ 不需先算「第一句是哪一句」，
而那個切句規則本身就是一個會出錯的 parser。

與 ``resources`` 模組的耦合（⚠️ 已知且刻意）
--------------------------------------------

canonical §6.3 逐字要求「parser 須沿用 ``resources.py`` 已釘住的哨兵形狀並排除
``## Log`` 之後內容，**不得自寫 markdown 解析**」——本專案 corpus 中至少五個根因出自
自寫解析。故本模組**直接 import** :func:`resources._split_at_log`，⛔ 不複製一份。

⚠️ 該名稱是私有的，且 ``aiwf#105``（WF-RESOURCE-HEADING-SUFFIX1）宣告了
``resources.py``、可能改動其標題比對邏輯。:func:`_reuse_probe` 在模組載入時檢查該函式
仍存在且行為符合預期，**不符即拋** ``BriefError``——⛔ 不退回自寫解析，那正是本條要防的。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .resources import ResourceDeclarationError, _split_at_log

#: 兩個形狀要求的字面標記。⛔ 封閉集合、逐字比對——中文的否定表達比英文散，
#: 關鍵字比對會漏，故 canonical §6.3 定案採固定標記（issuecomment-5391005830，
#: ⚠️ 標記字面為 PM 的選擇而非量測所得，需求方可覆寫）。
MARKER_WHEN = "適用時機"
MARKER_NON_SCOPE = "⛔ 非射程："

SECTION_HEADING = "## 簡介"
BEGIN = "<!-- card-brief:begin -->"
END = "<!-- card-brief:end -->"

_BLOCK_RE = re.compile(
    re.escape(BEGIN) + r"\s*(?P<text>.*?)\s*" + re.escape(END),
    re.DOTALL,
)

#: Project 欄位名。恆等導出，非摘要、非截斷。
FIELD_NAME = "簡介"

#: 供 card.py import 的別名（該模組已有自己的 SECTION_HEADING 命名空間）。
BRIEF_SECTION_HEADING_ALIAS = SECTION_HEADING


class BriefError(ValueError):
    """簡介缺失、形狀不符，或哨兵定位失效。"""


def _reuse_probe(split=None) -> None:
    """確認 ``resources._split_at_log`` 仍是本模組預期的那個東西。

    ``split`` 可注入——⭐ 那不是為了彈性，是為了**這個檢查自己能被測**：不可注入時
    唯一的測法是 ``importlib.reload``，而 reload 失敗會留下半初始化的模組狀態，
    使測試本身變成不可靠的東西。

    ⛔ 不是型別檢查——是**行為**檢查：餵一個已知輸入，比對已知輸出。若
    ``aiwf#105`` 或任何人改動了該函式的語意，本檢查會在**模組載入時**就失敗，
    而不是讓簡介 parser 靜默地把 Log 內的歷史回音當成現行簡介。
    """
    fn = split if split is not None else _split_at_log
    probe = "head line\n\n## Log\n\n- tail line\n"
    head, tail = fn(probe)
    if head != "head line\n" or "tail line" not in tail:
        raise BriefError(
            "resources._split_at_log 的行為與本模組預期不符"
            f"（head={head!r}、tail={tail!r}）；"
            "⛔ 拒絕退回自寫 markdown 解析（canonical §6.3）"
        )


_reuse_probe()


@dataclass(frozen=True)
class Brief:
    """一則卡片簡介。``text`` 是權威值，Project 欄位是它的恆等導出。"""

    text: str

    def __post_init__(self) -> None:
        validate_shape(self.text)


def validate_shape(text: str) -> None:
    """驗證兩個形狀要求；不符即拋 :class:`BriefError`。⛔ 不驗字數。"""
    if not text.strip():
        raise BriefError("簡介不得為空")
    missing = [m for m in (MARKER_WHEN, MARKER_NON_SCOPE) if m not in text]
    if missing:
        raise BriefError(
            f"簡介缺少必要標記 {missing}；canonical §6.3 要求必含 "
            f"「{MARKER_WHEN}」（什麼情況下該先看這張卡）與 "
            f"「{MARKER_NON_SCOPE}」（什麼不在本卡範圍）。⛔ 本檢查不驗字數。"
        )


def render_block(brief: Brief) -> str:
    """渲染 body 內的簡介區段（含標題與哨兵）。"""
    return f"{SECTION_HEADING}\n{BEGIN}\n{brief.text}\n{END}"


def _brief_section(body: str) -> str:
    """回傳 ``## 簡介`` 標題行之後、下一個 ``## `` 標題之前的區段內文。

    定位失效一律拋 :class:`BriefError`，⛔ 沒有「退回全文搜尋」的補救路徑——
    那正是 ``resources`` 模組要消滅、而本模組沿用其紀律的失敗形態。
    """
    try:
        head, tail = _split_at_log(body)
    except ResourceDeclarationError as exc:  # Log 標題重複等排版破壞
        raise BriefError(f"無法以 Log 標題切分 body：{exc}") from exc
    lines = head.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip() == SECTION_HEADING]
    if len(starts) > 1:
        raise BriefError(
            f"body 的 Log 之前有 {len(starts)} 個 `{SECTION_HEADING}` 標題，"
            "無法判定哪一個是現行簡介；拒絕取第一個"
        )
    if not starts:
        if SECTION_HEADING in tail:
            hint = "（該字樣只出現在 `## Log` 區段內，那是 append-only 的歷史回音）"
        elif SECTION_HEADING in head:
            hint = "（該字樣出現在 Log 之前但不是獨立標題行，排版可能已被字面 \\n 破壞）"
        else:
            hint = ""
        raise BriefError(f"body 內找不到獨立標題行 `{SECTION_HEADING}`{hint}")
    start = starts[0]
    end = next(
        (j for j in range(start + 1, len(lines)) if lines[j].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start + 1 : end])


def parse_block(body: str) -> Brief:
    """從卡片 body 解析簡介；找不到或形狀不符一律拋 :class:`BriefError`。"""
    section = _brief_section(body)
    match = _BLOCK_RE.search(section)
    if match is None:
        raise BriefError(
            f"`{SECTION_HEADING}` 區段內找不到 `{BEGIN}` … `{END}` 哨兵區塊"
        )
    return Brief(text=match.group("text"))


def try_parse_block(body: str) -> Brief | None:
    """解析失敗時回 ``None``——供「缺簡介不阻擋任何動詞」的 fail-open 路徑使用。

    ⚠️ 缺簡介是**構造上合法**的狀態：``--brief`` 在 ``open``／``amend`` 都只是可選
    旗標（兩處皆 ``default=None``），``validation.py`` 也完全不驗簡介
    （canonical §6.3〈卡片簡介〉）。⛔ 不得讓這些卡因缺欄位而無法 ``amend``
    或 ``handoff``。

    ⛔ 此處刻意只轉述該節的判準、不逐字引它的句子：原先引的那一句已於 2026-08-26
    被 canonical 自己更正掉，⇒ 逐字轉引等於另立一份會獨立腐爛的副本。
    """
    try:
        return parse_block(body)
    except BriefError:
        return None


def drifted(body: str, field_value: str | None) -> tuple[bool, str]:
    """兩居所是否漂移。回傳 ``(是否漂移, 人類可讀說明)``。

    判準是**兩居所實際值直接字串比對**——⛔ 不做正規化、不比對「第一句」。
    body 為權威；欄位是恆等導出。
    """
    parsed = try_parse_block(body)
    authoritative = parsed.text if parsed else None
    derived = field_value if (field_value or "").strip() else None
    if authoritative is None and derived is None:
        return False, "兩居所皆無簡介（既有卡的預期狀態）"
    if authoritative is None:
        return True, "Project 欄位有值但 body 無簡介區塊（欄位是導出，不得單獨存在）"
    if derived is None:
        return True, "body 有簡介但 Project 欄位是空的（寫入順序 body 先、欄位後，疑似欄位寫入失敗）"
    if authoritative != derived:
        return True, (
            "兩居所值不同：body 權威值與 Project 欄位不是逐字相同"
            f"（body {len(authoritative)} 字、欄位 {len(derived)} 字）"
        )
    return False, "兩居所逐字一致"


__all__ = [
    "BEGIN",
    "END",
    "FIELD_NAME",
    "MARKER_NON_SCOPE",
    "MARKER_WHEN",
    "SECTION_HEADING",
    "Brief",
    "BriefError",
    "drifted",
    "parse_block",
    "render_block",
    "try_parse_block",
    "validate_shape",
]
