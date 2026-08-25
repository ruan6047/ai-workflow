"""資源宣告：Issue body 內的 fenced JSON 結構化區塊。

凍結結構（見 OPS-STATE-PLANE-MIG1 Task 1 對照表 + 需求方裁決）：
    資源宣告＝Issue body 內 fenced JSON 結構化區塊（CLI 解析它做寫入集交集比對）；
    不用 MULTI_SELECT（未文件化型別）。

區塊格式（``## 資源宣告`` 是標準章節名，錨定同 ``templates/tasks-card.md`` 的
「驗收條件」／「驗證」慣例，不得改寫）：

    ## 資源宣告
    <!-- resource-claims:begin -->
    ```json
    {"db_scope": "none", "resources": ["file:a.py", "port:8080"]}
    ```
    <!-- resource-claims:end -->

Project 上另有一個同名 TEXT 欄位（見 project.py FIELD_SPECS）只放摘要／人類可讀版，
machine-of-record 一律是 body 這個區塊（對照表方案 C）。

**定位是兩層的，不是全文搜尋**（WF-RESOURCE-BLOCK-ANCHOR1）：先以**獨立標題行**
``## 資源宣告`` 切出區段，再**只在該區段內**找哨兵。舊版 ``_BLOCK_RE.search(body)``
取全文第一個命中，任何寫在真區塊之前的同名哨兵字面（例如把格式示範寫進驗收條件、
或 amend 把舊宣告原樣回音進 ``## Log``）都會贏，且無任何錯誤訊息——那是治理閘門的
靜默 fail-open，因為結果直接餵給 ``find_conflicts`` 與 ``assign`` 的寫入集閘門。

fail-closed 紀律刻意與 ``card.split_at_log``／``card._locate_section`` 同一組（以獨立
標題行定位、排版損壞即拒絕、同名標題多於一個即拒絕）。**沒有直接 import 重用是因為
``card.py`` 已 import 本模組的 ``render_block``，反向 import 會成環**；語意對齊靠
``tests/test_resources.py`` 的對照測試釘住，不是靠約定。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

# db_scope 封閉列舉，來源 canonical AI_WORKFLOW.md §4.2。
DB_SCOPES = {"none", "read", "write", "schema", "data-migration"}

# 共享可寫資源前綴，來源 canonical AI_WORKFLOW.md §4.1：
#   file:<path> / port:<n> / container:<name> / db:<env>:schema / db:<env>:table:<name>
_RESOURCE_PREFIX_RE = re.compile(
    r"^(file:.+|port:\d+|container:.+|db:[^:]+:(schema|table:.+))$"
)

_SECTION_HEADING = "## 資源宣告"
# ``## Log`` 是 append-only 留痕區（見 card.append_log_line）。amend 會把被覆寫的舊
# 宣告原樣寫進 Log，因此 Log 內幾乎必然有哨兵字面的歷史回音——它是歷史，不是宣告。
_LOG_HEADING = "## Log"
_BEGIN = "<!-- resource-claims:begin -->"
_END = "<!-- resource-claims:end -->"

#: 公開別名，供 ``card`` 判斷某個區段裡有沒有哨兵（比照 ``brief`` 的
#: ``BRIEF_SECTION_HEADING_ALIAS``）。⛔ 不讓 ``card`` 自己寫一份字面——
#: 兩份字面就是兩個事實來源，而本模組是哨兵語法的持有者。
CLAIMS_BEGIN_MARKER = _BEGIN

_BLOCK_RE = re.compile(
    re.escape(_BEGIN) + r"\s*```json\s*(?P<json>.*?)```\s*" + re.escape(_END),
    re.DOTALL,
)


class ResourceDeclarationError(ValueError):
    """資源宣告缺失或格式不符（open 的必填欄機械檢查會用到）。"""


@dataclass
class ResourceDeclaration:
    db_scope: str
    resources: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.db_scope not in DB_SCOPES:
            raise ResourceDeclarationError(
                f"db_scope 必須是 {sorted(DB_SCOPES)} 之一，收到 {self.db_scope!r}"
            )
        bad = [r for r in self.resources if not _RESOURCE_PREFIX_RE.match(r)]
        if bad:
            raise ResourceDeclarationError(
                "資源宣告格式錯誤（須為 file:<path> / port:<n> / container:<name> / "
                f"db:<env>:schema / db:<env>:table:<name>）：{bad}"
            )

    def summary(self) -> str:
        """給 Project 的「資源宣告」TEXT 欄位用的人類可讀摘要。"""
        if not self.resources:
            return f"db_scope={self.db_scope}；無共享可寫資源"
        return f"db_scope={self.db_scope}；" + "、".join(self.resources)

    def to_json(self) -> str:
        return json.dumps(
            {"db_scope": self.db_scope, "resources": self.resources},
            ensure_ascii=False,
        )


def render_block(decl: ResourceDeclaration) -> str:
    """渲染完整的 ``## 資源宣告`` 區塊（含標題），供組進卡片 body。"""
    payload = json.dumps(
        {"db_scope": decl.db_scope, "resources": decl.resources},
        ensure_ascii=False,
        indent=2,
    )
    return (
        f"{_SECTION_HEADING}\n"
        f"{_BEGIN}\n"
        f"```json\n{payload}\n```\n"
        f"{_END}"
    )


def _split_at_log(body: str) -> tuple[str, str]:
    """切成「``## Log`` 之前」與「``## Log`` 起的全部」。定位只准看前者。

    語意刻意等同 ``card.py`` 的 ``split_at_log()``：以**獨立標題行**判定，多於一個
    即拒絕，出現字樣卻無獨立標題行即拒絕（排版已被字面 ``\\n`` 破壞時，任何依標題
    定位的切段都可能把 Log 的歷史回音當成現況）。**不 import 重用是因為 card.py 已
    import 本模組的 render_block，反向 import 會成環**。

    引用一律錨定**函式名**、不寫行號：``card.py`` 在別人手上（WF-CARD-FIELD-CORRECTION1
    已於本卡在飛期間 +156 行），行號會漂，錨定函式名才找得回來。
    """
    lines = body.splitlines()
    idx = [i for i, line in enumerate(lines) if line.strip() == _LOG_HEADING]
    if len(idx) > 1:
        raise ResourceDeclarationError(
            f"body 內有 {len(idx)} 個 `{_LOG_HEADING}` 標題，無法安全切出「Log 之前」的定位範圍"
        )
    if not idx:
        if _LOG_HEADING in body:
            raise ResourceDeclarationError(
                f"body 含 `{_LOG_HEADING}` 字樣但它不是獨立標題行（排版可能已被字面 \\n "
                "破壞）；拒絕定位資源宣告，以免把 Log 內的歷史回音當成現行宣告"
            )
        return body, ""
    return "\n".join(lines[: idx[0]]), "\n".join(lines[idx[0] :])


#: ⭐ **後綴相容只給「資源宣告」這一個標題**（WF-RESOURCE-HEADING-SUFFIX1）。
#:
#: 2026-08-04 的 state-plane 遷移寫出的標題逐字是
#: ``## 資源宣告（機器可讀；`null`／`[]` 代表未正式宣告，不代表無資源）``，
#: 而本模組原本以逐字相等定位 ⇒ 那批卡的 ``amend --resources`` 可達 0/33（實測）。
#:
#: ⛔ **不放寬到其他標題**：``## 驗收條件（…）`` 這種後綴今天不存在（實測全母體
#: ``^##\s*資源宣告.*$`` 相異寫法恰 2 種、``^#+.*資源.*$`` 無其他同義標題），
#: 放寬它等於為不存在的形態開門。
#:
#: ⚠️ **「恰好 1 次」的不變量在新謂詞下仍是唯一的劫持防線**：真區段前插一個帶後綴的
#: 假區段會讓命中數變 2 而被拒；兩種標題並存同樣命中 2 次而被拒（#43 的兩層定位不因此失效）。
def _heading_matches(line: str) -> bool:
    """該行是不是資源宣告的標題（相等，或以 ``## 資源宣告（`` 起始）。"""
    stripped = line.strip()
    return stripped == _SECTION_HEADING or stripped.startswith(_SECTION_HEADING + "（")


def declaration_heading(body: str) -> str:
    """回傳卡面實際使用的資源宣告標題**逐字**（含可能的後綴）。

    ⭐ 存在的理由：``_declaration_section`` 只回區段**內文**，⇒ 呼叫端拿不回標題，
    而後綴今天是「未正式宣告 vs 無資源」這條分界的**唯一載體**（schema 的
    ``resources`` 型別是 ``list[str]``，``null`` 被拒、缺鍵靜默變 ``[]``）。
    ⇒ 需要一條讀得回標題的路，否則任何重寫都會靜默把它正規化掉。
    """
    head, _ = _split_at_log(body or "")
    lines = head.splitlines()
    starts = [i for i, line in enumerate(lines) if _heading_matches(line)]
    if len(starts) != 1:
        raise ResourceDeclarationError(
            f"body 的 Log 之前有 {len(starts)} 個資源宣告標題，必須恰好 1 個"
        )
    return lines[starts[0]].strip()


def _declaration_section(body: str) -> str:
    """回傳 ``## 資源宣告`` 標題行**之後、下一個 ``## `` 標題之前**的區段內文。

    定位失效一律拋 ``ResourceDeclarationError``，沒有「退回全文搜尋」的補救路徑——
    那正是本模組要消滅的失敗形態。
    """
    head, tail = _split_at_log(body)
    lines = head.splitlines()
    starts = [i for i, line in enumerate(lines) if _heading_matches(line)]
    if len(starts) > 1:
        raise ResourceDeclarationError(
            f"body 的 Log 之前有 {len(starts)} 個 `{_SECTION_HEADING}` 標題，"
            "無法判定哪一個是現行宣告；拒絕取第一個"
        )
    if not starts:
        if _SECTION_HEADING in head:
            hint = (
                f"（`{_SECTION_HEADING}` 字樣出現在 Log 之前但不是獨立標題行，"
                "排版可能已被字面 \\n 破壞）"
            )
        elif _SECTION_HEADING in tail:
            hint = (
                f"（`{_SECTION_HEADING}` 字樣只出現在 `{_LOG_HEADING}` 區段內，"
                "那是 append-only 的歷史回音，不是現行宣告）"
            )
        else:
            hint = ""
        raise ResourceDeclarationError(
            f"body 內找不到獨立標題行 `{_SECTION_HEADING}`{hint}"
        )
    start = starts[0]
    end = next(
        (j for j in range(start + 1, len(lines)) if lines[j].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start + 1 : end])


def parse_block(body: str) -> ResourceDeclaration:
    """從卡片 body 解析資源宣告；找不到或格式錯誤一律拋 ``ResourceDeclarationError``。

    刻意 fail closed（不得靜默略過）：assign 的交集檢查若讀不到宣告，代表該卡
    根本沒有走 CLI 開卡流程，這本身就是治理缺口，必須讓呼叫端知道，不能當成
    「無資源」悄悄放行。

    定位分兩層（見模組 docstring）：``_declaration_section`` 先以標題結構切出區段，
    哨兵只在該區段內找。區段外的哨兵字面——不論在驗收條件、核心痛點還是 Log——
    一律不參與定位，也不會讓解析「改用」它們。
    """
    section = _declaration_section(body or "")
    begins, ends = section.count(_BEGIN), section.count(_END)
    if begins != 1 or ends != 1:
        if begins == 0 and ends == 0:
            outside = ""
            if _BEGIN in (body or ""):
                outside = (
                    "；哨兵字面出現在該區段之外（驗收條件／核心痛點／Log 內的示範或"
                    "歷史回音都不算宣告）"
                )
            raise ResourceDeclarationError(
                f"`{_SECTION_HEADING}` 區段內找不到 {_BEGIN} ... {_END} 之間的 "
                f"fenced JSON 資源宣告區塊{outside}"
            )
        raise ResourceDeclarationError(
            f"`{_SECTION_HEADING}` 區段內有 {begins} 個 begin／{ends} 個 end 哨兵，"
            "必須各恰好 1 個才能判定哪一組是宣告；拒絕取第一個"
        )
    match = _BLOCK_RE.search(section)
    if not match:
        raise ResourceDeclarationError(
            f"`{_SECTION_HEADING}` 區段內的 {_BEGIN} ... {_END} 之間不是合法的 "
            "```json fenced 區塊"
        )
    raw = match.group("json").strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ResourceDeclarationError(f"資源宣告 JSON 解析失敗：{exc}") from exc
    if not isinstance(data, dict) or "db_scope" not in data:
        raise ResourceDeclarationError("資源宣告 JSON 必須是含 db_scope 鍵的物件")
    resources = data.get("resources", [])
    if not isinstance(resources, list) or not all(isinstance(r, str) for r in resources):
        raise ResourceDeclarationError("資源宣告的 resources 必須是字串陣列")
    return ResourceDeclaration(db_scope=data["db_scope"], resources=resources)


def try_parse_block(body: str) -> ResourceDeclaration | None:
    """寬鬆版 parse_block：解析不出來回傳 None 而非拋例外（doctor／snapshot 用；
    這些是報告型指令，遇到別卡壞掉的宣告不該讓整條指令當掉）。
    """
    try:
        return parse_block(body)
    except ResourceDeclarationError:
        return None


def find_conflicts(
    mine: ResourceDeclaration, other_card_id: str, other: ResourceDeclaration
) -> list[str]:
    """回傳 mine 與 other 之間互斥衝突的資源字串清單（可能為空）。

    規則：完全相同字串才算撞（不做路徑前綴模糊比對，避免誤判）。
    ``db:*`` 資源在雙方 db_scope 皆為 ``read`` 時視為可共用（canonical §4.1
    「read-only 才可共用」）；file/port/container 一律互斥，因為那些天生代表
    「這段時間我會寫」的獨佔宣告，db_scope 只對 db 資源本身有意義。
    """
    both_read_only = mine.db_scope == "read" and other.db_scope == "read"
    mine_set = set(mine.resources)
    other_set = set(other.resources)
    shared = mine_set & other_set
    if not shared:
        return []
    if both_read_only:
        # 雙方都宣告唯讀，db:* 資源可共用；但 file/port/container 本質仍是獨佔宣告。
        shared = {r for r in shared if not r.startswith("db:")}
    return sorted(shared)


__all__ = [
    "CLAIMS_BEGIN_MARKER",
    "declaration_heading",
    "DB_SCOPES",
    "ResourceDeclaration",
    "ResourceDeclarationError",
    "find_conflicts",
    "parse_block",
    "render_block",
    "try_parse_block",
]
