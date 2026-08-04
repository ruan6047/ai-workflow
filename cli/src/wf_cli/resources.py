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
_BEGIN = "<!-- resource-claims:begin -->"
_END = "<!-- resource-claims:end -->"

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


def parse_block(body: str) -> ResourceDeclaration:
    """從卡片 body 解析資源宣告；找不到或格式錯誤一律拋 ``ResourceDeclarationError``。

    刻意 fail closed（不得靜默略過）：assign 的交集檢查若讀不到宣告，代表該卡
    根本沒有走 CLI 開卡流程，這本身就是治理缺口，必須讓呼叫端知道，不能當成
    「無資源」悄悄放行。
    """
    match = _BLOCK_RE.search(body or "")
    if not match:
        raise ResourceDeclarationError(
            f"body 內找不到 {_BEGIN} ... {_END} 之間的 fenced JSON 資源宣告區塊"
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
    "DB_SCOPES",
    "ResourceDeclaration",
    "ResourceDeclarationError",
    "find_conflicts",
    "parse_block",
    "render_block",
    "try_parse_block",
]
