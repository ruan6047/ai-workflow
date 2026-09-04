"""卡面規格節：`## 規格` 區段內的 `card-spec:v1` 哨兵區塊。

## 為什麼有這個模組（`WF-REDESIGN-W3` 驗收 1）

決議 §二 row 10 的取代者是「**規格住卡面**＋`spec_version`」，而實測 2026-09-02：
全板 217 張只有 1 張有 `## 規格` 標題、內容還是「規格不在卡面」；`spec_version`
在 `cli/src` **零命中**——⛔ 無 reader、⛔ 無 writer、⛔ 無 schema 欄位。
⇒ 這個機制**從未存在**。本模組是它的 reader 那一半。

## 為什麼是獨立哨兵，⛔ 不是塞進 W1 的 v1 fenced JSON

卡面驗收 1 逐字「只擴充／消費 W1 的 v1 schema……**⛔ 不另立 schema**」，而 v1 的
頂層與三個子物件皆 `additionalProperties: false` ⇒ **加鍵實測被拒**；加鍵就得改
schema、就得升 `schema_version`、就變成另立 v2 —— 被同一句逐字禁止。
⇒ **「擴充」＝零**，規格節走**獨立哨兵**，沿 `card-brief`（215 張）與
`resource-claims`（217 張）的既有形狀（`card_face.py:12` 逐字「兩個 fenced JSON
區塊在同一張卡面上共存是常態」）。

## 兩個版本號⛔ 不是同一件事

- 哨兵字面裡的 **`v1`** ＝**區塊格式**版本。照 `card_face.py:64` 逐字「v2 的哨兵是
  另一串字面」——格式若要改，換的是哨兵本身，⛔ 不是在區塊內加一個格式版本欄。
- 區塊第一行的 **`spec_version`** ＝**規格內容**版本。`planning.md:10` 逐字
  「每次改必 bump」。

⚠️ 兩者⛔ 不得互相代用，也⛔ 不得由其中一個推導另一個。

## 內容是 markdown，⛔ 不是 fenced JSON

規格是**給人讀的**；機器只需要「哨兵定界 ＋ 第一行版本號」這兩件事。既有形狀＝
`docs/research/drafts/wave-specs/w3.md:6`。⛔ 不把規格文字結構化成 JSON——那會把
一份人類文件變成一個會出錯的 schema。

## fail-open，⛔ 不擋任何動詞

`try_parse_block` 讀不到回 `None`，沿 `brief.try_parse_block` 的先例：**沒有規格節
是構造上合法的狀態**（今日 217 張裡 216 張都沒有），⛔ 不得讓那些卡因缺區塊而
無法 `amend` 或 `handoff`。⇒ 本模組的擋人點增量 **0**。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .resources import ResourceDeclarationError, _split_at_log

SECTION_HEADING = "## 規格"

#: ⚠️ `v1` 是**區塊格式**版本，⛔ 不是規格內容版本（後者是區塊第一行的 `spec_version`）。
#: 格式若要改，換的是這一串字面本身（`card_face.py:64` 逐字「v2 的哨兵是另一串字面」）。
BEGIN = "<!-- card-spec:v1:begin -->"
END = "<!-- card-spec:v1:end -->"

_BLOCK_RE = re.compile(
    re.escape(BEGIN) + r"\s*(?P<text>.*?)\s*" + re.escape(END),
    re.DOTALL,
)

#: 區塊第一行。⛔ 只認十進位整數——`planning.md:10` 逐字「每次改必 bump」，
#: 而「bump」在語意上要求可比大小，語意化版本或日期都會讓「有沒有 bump」變成
#: 一個需要 parser 的問題，⇒ 取最窄的形狀。
_VERSION_RE = re.compile(r"^spec_version:\s*(?P<version>\d+)\s*$")


class CardSpecError(ValueError):
    """規格節缺失、形狀不符，或哨兵定位失效。"""


@dataclass(frozen=True)
class CardSpec:
    #: 規格**內容**版本（`planning.md:10`：每次改必 bump）。
    spec_version: int
    #: 版本行之後的規格文字，markdown 原樣。⛔ 未做任何結構化。
    text: str


def _spec_head(body: str) -> str:
    """取 `## 規格` 標題**之後**、Log **之前**的全部文字。

    ⭐ **⛔ 不在下一個 `## ` 截斷**（`brief._brief_section` 是那樣做的，本模組刻意
    不同）：規格內容是 **markdown**，`## 一 · 目標` 這種標題是它的正常內容——照
    `brief` 的切法會在規格自己的第一個標題處截斷，把哨兵尾留在區段外，於是
    **任何有標題的規格都讀不出來**。⚠️ 這是實作首版踩過的，⛔ 不要改回去。
    ⇒ 邊界由**哨兵**負責（它是封閉定界符），標題只負責定位起點。

    ⭐ **先以 Log 標題切分**（`resources._split_at_log`），理由與 `brief` 相同：
    Log 是 append-only 的歷史區，裡面會有過去某次 amend 留下的**歷史回音**。
    ⛔ 不切分就會把歷史當成現行規格。

    定位失效一律拋 `CardSpecError`，⛔ 沒有「退回全文搜尋」的補救路徑——那正是
    `resources` 模組要消滅、而本模組沿用其紀律的失敗形態。
    """
    try:
        head, tail = _split_at_log(body)
    except ResourceDeclarationError as exc:  # Log 標題重複等排版破壞
        raise CardSpecError(f"無法以 Log 標題切分 body：{exc}") from exc
    lines = head.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip() == SECTION_HEADING]
    if len(starts) > 1:
        raise CardSpecError(
            f"body 的 Log 之前有 {len(starts)} 個 `{SECTION_HEADING}` 標題，"
            "無法判定哪一個是現行規格；⛔ 拒絕取第一個"
        )
    if not starts:
        if SECTION_HEADING in tail:
            hint = "（該字樣只出現在 `## Log` 區段內，那是 append-only 的歷史回音）"
        elif SECTION_HEADING in head:
            hint = "（該字樣出現在 Log 之前但不是獨立標題行，排版可能已被字面 \\n 破壞）"
        else:
            hint = ""
        raise CardSpecError(f"body 內找不到獨立標題行 `{SECTION_HEADING}`{hint}")
    return "\n".join(lines[starts[0] + 1 :])


def parse_block(body: str) -> CardSpec:
    """從卡片 body 解析規格節；找不到或形狀不符一律拋 `CardSpecError`。"""
    section = _spec_head(body)
    matches = list(_BLOCK_RE.finditer(section))
    if not matches:
        raise CardSpecError(
            f"`{SECTION_HEADING}` 標題之後找不到 `{BEGIN}` … `{END}` 哨兵區塊"
        )
    if len(matches) > 1:
        # 標題只有一個但哨兵有多個 ⇒ 後面某個 `## ` 區段裡也有一份。同樣⛔ 拒絕取第一個。
        raise CardSpecError(
            f"`{SECTION_HEADING}` 標題之後有 {len(matches)} 個 `{BEGIN}` 區塊；"
            "⛔ 拒絕取第一個"
        )
    match = matches[0]
    inner = match.group("text")
    lines = inner.splitlines()
    if not lines:
        raise CardSpecError("規格節哨兵區塊是空的；第一行必須是 `spec_version: <整數>`")
    version_match = _VERSION_RE.match(lines[0].strip())
    if version_match is None:
        raise CardSpecError(
            f"規格節第一行必須是 `spec_version: <整數>`，實際是 {lines[0].strip()!r}。"
            "⛔ 不由內容推導版本——`planning.md:10` 逐字「每次改必 bump」，"
            "推導出來的版本無法證明它被 bump 過。"
        )
    return CardSpec(
        spec_version=int(version_match.group("version")),
        text="\n".join(lines[1:]).strip(),
    )


def try_parse_block(body: str) -> CardSpec | None:
    """解析失敗時回 `None`——供「缺規格節⛔ 不阻擋任何動詞」的 fail-open 路徑使用。

    ⚠️ **缺規格節是構造上合法的狀態**：2026-09-02 實測全板 217 張中 **216 張**沒有
    `## 規格` 區段。⛔ 不得讓那些卡因缺區塊而無法 `amend` 或 `handoff`。
    形狀沿 `brief.try_parse_block`。
    """
    try:
        return parse_block(body)
    except CardSpecError:
        return None


def render_block(spec: CardSpec) -> str:
    """組出可直接貼進卡面的 `## 規格` 區段。"""
    return f"{SECTION_HEADING}\n{BEGIN}\nspec_version: {spec.spec_version}\n\n{spec.text}\n{END}"


__all__ = [
    "BEGIN",
    "END",
    "SECTION_HEADING",
    "CardSpec",
    "CardSpecError",
    "parse_block",
    "render_block",
    "try_parse_block",
]
