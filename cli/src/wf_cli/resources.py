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
import unicodedata
from collections.abc import Sequence
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
CLAIMS_END_MARKER = _END

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
#: 2026-08-04 一次性遷移產生的資源宣告標題，**逐字**。
#:
#: ⭐ 這是**封閉集合的黃金值，⛔ 不是前綴樣式**。原本寫成 ``startswith(_SECTION_HEADING + "（")``
#: ——查核者 R1-01 抓到 ``## 資源宣告備註`` 會被誤認；自審再抓到補完之後
#: ``## 資源宣告（人工備註）`` **仍會被誤認並靜默刪除**。⇒ 前綴樣式是**開放集合**，
#: 每補一個反例就露出下一個。而這個後綴是遷移的歷史產物、⛔ 不是擴充點：
#: 全母體 194 張實測**只有這 1 種寫法、33 次**。⇒ 收成逐字比對。
#:
#: ⚠️ 代價說明：日後若真出現另一種合法後綴，解析會**找不到區段而拒收**（fail-closed）
#: ⇒ 該加就加進本常數，⛔ 不要改回前綴比對。
MIGRATION_SECTION_HEADING = (
    "## 資源宣告（機器可讀；`null`／`[]` 代表未正式宣告，不代表無資源）"
)

#: 資源宣告標題的**全部**合法寫法。⛔ 判定一律用本集合，不得在呼叫端另寫謂詞。
SECTION_HEADING_VARIANTS = (_SECTION_HEADING, MIGRATION_SECTION_HEADING)


def _heading_matches(line: str) -> bool:
    """該行是不是資源宣告的標題（相等，或以 ``## 資源宣告（`` 起始）。"""
    stripped = line.strip()
    return stripped in SECTION_HEADING_VARIANTS


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


# ===========================================================================
# `file:` 相交判定（`WF-REDESIGN-W3` 驗收 4(b)）
# ===========================================================================
#
# ⭐ **這一節取代的不是 `find_conflicts` 的謹慎，而是它的射程。**
# 舊 docstring 逐字「完全相同字串才算撞（**不做路徑前綴模糊比對，避免誤判**）」——
# 它迴避的是**字串前綴**；本節實作的是**分量序列前綴**，兩者⛔ 不是同一個運算：
#
#   `file:templates` × `file:templates2/a.md`
#       字串前綴 → **誤判相交**（原作者要避的就是這個）
#       分量序列 → `('templates',)` vs `('templates2','a.md')`，首分量不同 → **不相交**
#
#   `file:./templates/` × `file:templates/a.md`
#       字串前綴 → 不相交（**漏放**）
#       分量序列 → 相交
#
# ⇒ **原作者迴避的失敗面，這個既定語意本身就不產生。**
#
# ⚠️ **⛔ 不得照抄 `docs/WF_RESOURCE_WRITESET1.md` §8.5 的斷言方向**：該節把
# `templates` × `templates2/a.md` 斷言為**相交**，那是它的**立即階段**；本卡採
# **目標階段**（§2.2），同一對的正確斷言是**不相交**。

#: §2.1 的比對鍵：分量序列。⛔ 不含 `file:` 前綴、⛔ 不含空分量與 `.` 分量。
def comparison_key(resource: str) -> tuple[str, ...]:
    """把一個 ``file:`` 資源轉成 §2.1 的**比對鍵**（分量序列）。

    逐字依 ``docs/WF_RESOURCE_WRITESET1.md`` §2.1 四步：
    1. 去 ``file:`` 前綴；2. 以 ``/`` 切分並**捨棄空分量與 ``.`` 分量**
    （這摺疊了重複斜線與 ``./``）；3. 每個分量做 NFC 再 ``casefold()``；4. 成 tuple。

    ⚠️ **結尾斜線⛔ 不影響比對鍵**（§2.1 末段逐字）：它只表達宣告意圖，
    ⛔ 不參與相交判定。
    ⚠️ ``casefold`` 是**刻意的 fail-closed 側**（§2.3(2) 逐字）：開發機檔案系統實測
    大小寫不敏感 ⇒ 判定服從「實際會被寫的是什麼」，⛔ 不是「git 怎麼記」。
    代價明說：大小寫敏感的檔案系統上會**誤拒**兩個確實不同的檔案。
    """
    path = resource[len("file:"):] if resource.startswith("file:") else resource
    return tuple(
        unicodedata.normalize("NFC", part).casefold()
        for part in path.split("/")
        if part not in ("", ".")
    )


def file_resources_intersect(x: str, y: str) -> bool:
    """§2.2 的相交謂詞：兩個比對鍵其中之一為另一之**前綴**（含相等）。

    ⭐ **路徑邊界由「比對分量序列而非字串」自動保證**（§2.2 逐字）——⛔ 不需要另加
    一道邊界檢查，``startswith`` 的陷阱在切分那一步就消失了。
    """
    kx, ky = comparison_key(x), comparison_key(y)
    n = min(len(kx), len(ky))
    return kx[:n] == ky[:n]


#: §4.2：從 Issue URL 解析 repo 歸屬。⛔ 形狀不符即回 None（⇒ **不套用** repo 限定詞）。
_ISSUE_URL_REPO_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/issues/\d+")


def repo_of_issue_url(issue_url: str | None) -> str | None:
    """回傳 ``owner/repo``，解析不出來回 ``None``。

    ⚠️ ``None`` 的語意是「**歸屬無法確立**」，⛔ 不是「屬於別的 repo」——§4.2 逐字
    「歸屬必須**正向確立**，否則⛔ 不得套用此限定」，因為 repo 限定詞是**放行方向**
    的規則。誤拒的代價是排隊，漏放的代價是兩張卡同寫一檔，取前者。
    """
    if not issue_url:
        return None
    match = _ISSUE_URL_REPO_RE.match(issue_url.strip())
    return f"{match.group(1)}/{match.group(2)}" if match else None


# ===========================================================================
# `db:` 環境別名（`WF-REDESIGN-W3` 驗收 4(c)）
# ===========================================================================
#
# **別名表內嵌進碼、⛔ 不讀外部檔**（規劃階段裁定 7）。依據：`registry.py:605`–`:607`
# 逐字「守衛⛔ 不新增任何網路相依，也⛔ 不新增任何檔案系統相依——這是 fail-closed
# 站得住的前提」。
#
# ⚠️ **論證形狀明說**：今日別名**需求量未知**，⛔ 不是 0——這個機制從來沒上線過，
# 「0 筆需求」是因果倒置（⛔ 不得拿它當「不需要」的證據）。真正確定的是**打破
# fail-closed 前提的代價**，⇒ 取代價確定的那一側。

#: canonical 環境。**來源＝`templates/database-contract.md` §2 的表，逐字四列。**
#:
#: ⚠️ **這是本卡對「已登記」的解讀，卡面⛔ 未列舉 canonical 集合。** 若只把
#: `DB_ENVIRONMENT_ALIASES` 當「已登記」，今日表空 ⇒ 連 `db:production:schema` 這種
#: **正確拼法**都會吃到警示 ⇒ 三格中的「未登記」格會退化成「全部」。⇒ 已登記
#: ＝ canonical ∪ 別名。⛔ 若需求方認為 canonical 集合另有出處，本常數作廢。
DB_CANONICAL_ENVIRONMENTS: tuple[str, ...] = ("local", "test", "staging", "production")

#: 別名 → canonical 環境。**今日空**（⚠️ 新生 0：機制未曾存在，⛔ 不得讀成「不需要」）。
DB_ENVIRONMENT_ALIASES: dict[str, str] = {}


def _selfcheck_db_alias_schema() -> None:
    """**模組載入期 schema 自檢**（沿 `card_face._assert_schema_is_understood` 先例）。

    ⭐ **這是卡面第三格「registry 載入或解析失敗 → 在任何遠端寫入前拒絕 assign
    （fail-loud）」的落地形狀，⛔ 不是它的逐字。** 逐字在內嵌實作下**無法實作**：
    碼常數的「載入失敗」＝ Python import 失敗＝**整個 wfcli 起不來**，那⛔ 不是
    「拒絕 assign」。⇒ 改成載入即炸——同樣是 fail-loud，且同樣**早於任何遠端寫入**。
    ⛔ 不得降級為警告（需求方 2026-09-02 裁定 A-5）。
    """
    canonical = set(DB_CANONICAL_ENVIRONMENTS)
    if len(canonical) != len(DB_CANONICAL_ENVIRONMENTS):
        raise ResourceDeclarationError("DB_CANONICAL_ENVIRONMENTS 有重複值")
    for alias, target in DB_ENVIRONMENT_ALIASES.items():
        if not isinstance(alias, str) or not alias:
            raise ResourceDeclarationError(f"別名鍵必須是非空字串：{alias!r}")
        if target not in canonical:
            raise ResourceDeclarationError(
                f"別名 {alias!r} 指向 {target!r}，⛔ 不在 canonical 環境 {DB_CANONICAL_ENVIRONMENTS}"
            )
        if alias in canonical:
            raise ResourceDeclarationError(
                f"別名 {alias!r} 與 canonical 環境同名——那會讓「已登記」有兩個答案"
            )


_selfcheck_db_alias_schema()

#: `db:<env>:…` 的 env 分量。⚠️ 與 `_RESOURCE_PREFIX_RE` 的 `db:[^:]+:` 同一個口徑。
_DB_ENV_RE = re.compile(r"^db:(?P<env>[^:]+):(?P<rest>.+)$")


def normalize_db_resource(resource: str) -> tuple[str, bool]:
    """回傳 ``(正規化後的字面, env 是否已登記)``。

    封閉三格的前兩格：
    - **已登記別名** → 換成 canonical 環境（正規化命中）
    - **已登記 canonical** → 原樣（也算已登記，⛔ 不吃警示）
    - **未登記** → **按字面**回傳，第二元回 ``False``（呼叫端據此發 stderr 警示）

    ⛔ **別名表⛔ 不得用來正規化非法字面**（`0c629ac` 逐字「⛔ 不為舊文件訂特殊
    規則」）：不符 `_RESOURCE_PREFIX_RE` 的字面歸 `ResourceDeclarationError` 拒收，
    ⛔ 不在此處救。
    """
    match = _DB_ENV_RE.match(resource)
    if match is None:
        return resource, True  # ⛔ 非 db: 資源，本函式不管它
    env = match.group("env")
    if env in DB_ENVIRONMENT_ALIASES:
        return f"db:{DB_ENVIRONMENT_ALIASES[env]}:{match.group('rest')}", True
    return resource, env in DB_CANONICAL_ENVIRONMENTS


def unregistered_db_environments(resources: Sequence[str]) -> list[str]:
    """挑出 env 分量未登記的 `db:` 資源（供呼叫端印 stderr 警示）。"""
    return [r for r in resources if not normalize_db_resource(r)[1]]


# ===========================================================================
# 衝突的結構化結果
# ===========================================================================

#: 拒絕訊息四要件的第二項「觸發哪一來源」的封閉值域。
#: ⚠️ 一對資源可能同時滿足多條，判定**依下列順序取第一個命中**，⛔ 不並列。
CONFLICT_SOURCES: tuple[str, ...] = (
    "完全相同",
    "分量序列前綴",
    "casefold 等價",
    "NFC 等價",
    "db 資源相同",
)


@dataclass(frozen=True)
class ResourceConflict:
    """一組相交，攜帶拒絕訊息四要件所需的全部資料。

    ⛔ 這個 dataclass 存在的理由是**訊息**，⛔ 不是判定：判定仍由
    `file_resources_intersect` 一個謂詞說了算。
    """

    other_card_id: str
    #: 本卡的**原始字面**（⛔ 非比對鍵——四要件逐字要求原始字面）。
    mine: str
    #: 對方的原始字面。
    theirs: str
    source: str

    @property
    def key_mine(self) -> tuple[str, ...]:
        return comparison_key(self.mine)

    @property
    def key_theirs(self) -> tuple[str, ...]:
        return comparison_key(self.theirs)

    def narrowing_hint(self) -> str:
        """要件③ 的**收窄方向**：一句可據以判斷的話，且**帶著這一則衝突自己的字面**。

        ⭐ 收窄是本卡**唯一**的逃生口：⛔ 不給 `--force`（`registry.py:614` 先例逐字
        「給逃生口等於把『沒注意到』變成『按一下』」）、⛔ 不分級。

        ## ⚠️ 為什麼**每一種資源**都要帶識別資訊（`R4-001`，需求方裁定甲）

        修補前這裡對**非 `file:`** 的衝突回一個**常數句**「改宣告不重疊的資源」——
        兩則 `db:` 衝突因此印出**逐字相同**的方向，而需求方裁定
        （`issuecomment-5523123629`）逐字要求「**讓兩則衝突印出相同方向，斷言必須
        轉紅**」。⇒ 那個常數句**在構造上使該裁定不可滿足**。

        當時的處置是在測試裡對非 `file:` 衝突 `continue` 並登記為「射程缺口」，
        查核者 `R4-001` 判定那與裁定**直接相反** ⇒ 需求方裁定**甲：補識別資訊，
        ⛔ 不縮射程**（縮射程會是**第二次**為做不到而改射程）。

        ⚠️ 識別資訊**本來就在物件裡**（`mine`／`theirs` 兩個原始字面），⛔ 不需要新的
        資料來源——⛔ 這一點是這個修補成立的全部理由，⛔ 不是「想辦法湊出不同的字」。

        ## 兩種形狀，各自的收窄動作**不同**

        - **`file:`**：有深淺可言 ⇒ 指名**較深的那一個**，叫人收窄到它之下。
        - **非 `file:`**（`db:`／`port:`／`container:`）：⛔ **沒有**「更深的路徑」這個
          概念（`db:` 的分量是環境與物件名、`port:` 是一個數字）⇒ 動作只能是**改宣告**，
          但話裡仍指名**這一則衝突的雙方字面**，於是「逐則對應」對它也成立。
        """
        n = min(len(self.key_mine), len(self.key_theirs))
        if not self.mine.startswith("file:") or n == 0:
            # ⛔ **不要改回一句不帶字面的常數**：那正是 `R4-001` 的成因。
            return (
                f"{self.mine} 與 {self.theirs} 指的是同一個資源，"
                f"⛔ 沒有更深的路徑可收窄 ⇒ 改宣告不重疊的資源"
            )
        deeper = self.mine if len(self.key_mine) >= len(self.key_theirs) else self.theirs
        return f"把宣告收窄到 {deeper} 之下更深的路徑，或改宣告不重疊的資源"


def _conflict_source(mine: str, theirs: str) -> str:
    if mine == theirs:
        return "完全相同"
    if not mine.startswith("file:"):
        return "db 資源相同"
    raw_mine = mine[len("file:"):].split("/")
    raw_theirs = theirs[len("file:"):].split("/")
    nfc_mine = tuple(unicodedata.normalize("NFC", p) for p in raw_mine if p not in ("", "."))
    nfc_theirs = tuple(unicodedata.normalize("NFC", p) for p in raw_theirs if p not in ("", "."))
    if nfc_mine == nfc_theirs:
        # NFC 之後就相等 ⇒ 差別在 Unicode 組合形式，⛔ 不是大小寫也⛔ 不是深度。
        return "NFC 等價"
    if len(nfc_mine) == len(nfc_theirs):
        # 深度相同卻仍相交 ⇒ 只可能是 casefold 把它們拉在一起。
        return "casefold 等價"
    return "分量序列前綴"


def detailed_conflicts(
    mine: ResourceDeclaration,
    other_card_id: str,
    other: ResourceDeclaration,
    *,
    mine_repo: str | None = None,
    other_repo: str | None = None,
) -> list[ResourceConflict]:
    """回傳 mine 與 other 之間互斥衝突的**結構化**清單（可能為空）。

    **判定規則（2026-09-02 起，`WF-REDESIGN-W3` 驗收 4(b)）：**

    - ``file:`` 資源 —— **分量序列前綴**相交（``file_resources_intersect``，逐字依
      ``docs/WF_RESOURCE_WRITESET1.md`` §2.1／§2.2）。⛔ **不再是**完全相同字串；
      舊做法的假陰性實測 **19 對**（2026-09-02，全活卡 406 組合）。
    - ``file:`` 另受 **§4.2 repo 限定詞**：兩方歸屬**皆經正向確立**且不同時⛔ 不相交。
      任一方確立不了就**不套用**該限定（⇒ 視同同 repo，fail-closed 側）。
      ⚠️ ``port:``／``container:``／``db:`` **不適用** repo 限定（§4.3 逐字：它們是主機
      或環境層級資源，兩個 repo 搶同一個 ``port:4001`` 是真的搶）。
    - ``db:`` 資源 —— 先過 ``normalize_db_resource``（別名 → canonical）再比字面；
      雙方 ``db_scope`` 皆為 ``read`` 時視為可共用（canonical §4.1）。
    - ``port:``／``container:`` —— 完全相同字串。它們⛔ 沒有路徑結構，前綴語意在
      它們身上⛔ 不成立。

    ``file``／``port``／``container`` 一律互斥（即使雙方 ``db_scope`` 皆 ``read``），
    因為那些天生代表「這段時間我會寫」的獨佔宣告，``db_scope`` 只對 db 資源有意義。
    """
    both_read_only = mine.db_scope == "read" and other.db_scope == "read"
    repos_are_different = (
        mine_repo is not None and other_repo is not None and mine_repo != other_repo
    )

    found: list[ResourceConflict] = []
    seen: set[tuple[str, str]] = set()
    for a in mine.resources:
        for b in other.resources:
            if a.startswith("file:") and b.startswith("file:"):
                if repos_are_different:
                    continue  # §4.2：歸屬皆確立且不同 ⇒ 不相交
                hit = file_resources_intersect(a, b)
            elif a.startswith("db:") and b.startswith("db:"):
                if both_read_only:
                    continue  # canonical §4.1：雙方唯讀 ⇒ db 資源可共用
                hit = normalize_db_resource(a)[0] == normalize_db_resource(b)[0]
            else:
                hit = a == b
            if hit and (a, b) not in seen:
                seen.add((a, b))
                found.append(
                    ResourceConflict(
                        other_card_id=other_card_id,
                        mine=a,
                        theirs=b,
                        source=_conflict_source(a, b),
                    )
                )
    return sorted(found, key=lambda c: (c.mine, c.theirs))


def find_conflicts(
    mine: ResourceDeclaration,
    other_card_id: str,
    other: ResourceDeclaration,
    *,
    mine_repo: str | None = None,
    other_repo: str | None = None,
) -> list[str]:
    """``detailed_conflicts`` 的字串投影（回**本卡側**的原始字面）。

    ⛔ **本函式⛔ 不含任何自己的判定邏輯**——它只是投影。既有呼叫端與測試靠它，
    而拒絕訊息的四要件需要 ``ResourceConflict`` ⇒ 判定只有一份，在 detailed 那裡。
    """
    return sorted(
        {
            c.mine
            for c in detailed_conflicts(
                mine, other_card_id, other, mine_repo=mine_repo, other_repo=other_repo
            )
        }
    )


__all__ = [
    "CLAIMS_BEGIN_MARKER",
    "CLAIMS_END_MARKER",
    "CONFLICT_SOURCES",
    "DB_CANONICAL_ENVIRONMENTS",
    "DB_ENVIRONMENT_ALIASES",
    "DB_SCOPES",
    "MIGRATION_SECTION_HEADING",
    "SECTION_HEADING_VARIANTS",
    "ResourceConflict",
    "ResourceDeclaration",
    "ResourceDeclarationError",
    "declaration_heading",
    "comparison_key",
    "file_resources_intersect",
    "find_conflicts",
    "detailed_conflicts",
    "normalize_db_resource",
    "parse_block",
    "render_block",
    "repo_of_issue_url",
    "try_parse_block",
    "unregistered_db_environments",
]
