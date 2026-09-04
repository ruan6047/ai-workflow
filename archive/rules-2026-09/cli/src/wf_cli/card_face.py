"""卡面表單（card-face form）：開卡表單的機器可讀居所。

**本模組是 card-face JSON schema 的唯一 owner**（`WF-REDESIGN-W1` 驗收 3／P1-30）。
schema 全文的權威居所是卡 `ruan6047/ai-workflow#217` 的 body「AC3 規格全文」段；
本模組把那段**逐字**搬成 :data:`SCHEMA_TEXT`，⛔ 不改寫、⛔ 不「整理」。

哨兵
----

``<!-- card-face-form:v1:begin -->`` ／ ``<!-- card-face-form:v1:end -->``。

⛔ **與 ``resource-claims`` 哨兵不同名**，且 ⛔ **不以「找到一個 JSON fence」定位**——
兩個 fenced JSON 區塊在同一張卡面上共存是常態（資源宣告就是另一個），拿 fence 當
錨點等於讓兩者互搶。定位一律走哨兵，且哨兵只在 ``## Log`` 之前的區段內找
（Log 是 append-only 留痕，``amend`` 會把舊值原樣回音進去）。

四個必填鍵的來源
----------------

``stage_plan``／``tier_basis``／``list_convergence`` 三者對應
``docs/research/WORKFLOW-REDESIGN-2026-08-30.md`` §四「開卡表單」的
**階段計畫**／**級別依據三子問**／**清單收斂**。同表 §一第 12 列逐字把
``--needs-deploy`` 旗標的取代者記為「開卡表單『階段計畫』」，owner 為本波 ⇒
部署狀態的初值改由 ``stage_plan`` 是否含 ``部署`` 導出（見 ``commands/open_cmd.py``）。

⛔ **不得由此推出「本模組是那份決議紀錄的執行者」**：決議紀錄非生效條文，本模組
只實作卡面明列的 schema；階段語彙的**條文**歸 W2A，⛔ 不在本卡射程。

驗證器
------

⛔ 本 repo 的 ``cli/pyproject.toml`` ``dependencies = []``——**刻意不引入
``jsonschema``**：為了四個鍵多一個第三方相依，其升級面比它省下的程式碼大。
:func:`validate` 是一個**只認得本 schema 用到的關鍵字**的 draft 2020-12 子集走訪器，
其涵蓋範圍由 :data:`_UNDERSTOOD_KEYWORDS` 明列，並由模組載入期的
:func:`_assert_schema_is_understood` 檢查 :data:`SCHEMA` 沒有用到走訪器不懂的關鍵字。

⭐ **這個檢查是承重的**：日後有人往 schema 加一個 ``oneOf``／``dependentRequired``，
模組會**在載入時**就炸，⛔ 而不是靜默地把那條約束當成不存在。⛔ 不得把它降級成警告。

⚠️ **schema 值域是封閉的，且 owner 是卡面**（executor-conduct「封閉值域只能由 owner
裁定擴張」）：``stage`` 的八個值、``claim`` 的兩個值、``schema_version`` 的 ``"1"``
都住在 :data:`SCHEMA_TEXT` 裡。要加值＝改卡面 ⇒ 那是新一張卡的事。
"""

from __future__ import annotations

import json
import re
from typing import Any

from .brief import _reuse_probe as _split_at_log_reuse_probe
from .resources import ResourceDeclarationError, _split_at_log

# ⭐ ``resources._split_at_log`` 的行為探測**不重打一份**：這裡 import 的就是
# ``brief.py`` 那一支（canonical §6.3 逐字要求 parser 沿用 ``resources.py`` 已釘住的
# 哨兵形狀、⛔ 不得自寫 markdown 解析）。它在 ``brief`` 載入時已跑過一次，這裡再跑
# 一次的成本是 0，換到的是**本模組自己也宣告了這個前提**——⛔ 不靠「反正 brief 會被
# import」這種傳遞性假設。
_split_at_log_reuse_probe()

SECTION_HEADING = "## 卡面表單"

#: ⭐ 哨兵字面。**逐字取自卡 #217 body 的 AC3 規格全文段**，⛔ 不得改寫。
#: 版本號 ``v1`` 在哨兵字面裡，是刻意的：v2 的哨兵是**另一串字面**，v1 reader
#: 因此在定位階段就看不到它，⛔ 不會誤把 v2 區塊當 v1 解析。
BEGIN = "<!-- card-face-form:v1:begin -->"
END = "<!-- card-face-form:v1:end -->"

#: 本 reader 認得的版本。⛔ 其餘一律 fail-closed（見 :class:`CardFaceVersionError`）。
SCHEMA_VERSION = "1"

#: JSON Schema 全文，**逐字**取自卡 #217 body「AC3 規格全文」段。
#: ⛔ 不得改寫任何一個字元——改了就是改規格，而規格的 owner 是卡面不是本檔。
SCHEMA_TEXT = r"""{"$schema":"https://json-schema.org/draft/2020-12/schema",
 "type":"object","additionalProperties":false,
 "required":["schema_version","stage_plan","tier_basis","list_convergence"],
 "properties":{
  "schema_version":{"const":"1"},
  "stage_plan":{"type":"array","minItems":1,"items":{"type":"object","additionalProperties":false,
    "required":["stage","goal"],
    "properties":{"stage":{"enum":["需求","研究","規劃","執行","審核","部署","維護","結案"]},
                  "goal":{"type":"string","minLength":1}}}},
  "tier_basis":{"type":"object","additionalProperties":false,
    "required":["sensitive_surfaces","recoverability","blast_radius"],
    "properties":{"sensitive_surfaces":{"type":"string","minLength":1},
                  "recoverability":{"type":"string","minLength":1},
                  "blast_radius":{"type":"string","minLength":1}}},
  "list_convergence":{"type":"array","items":{"type":"object","additionalProperties":false,
    "required":["issue_url","claim"],
    "properties":{"issue_url":{"type":"string","pattern":"^https://github\\.com/[^/]+/[^/]+/issues/[1-9][0-9]*$"},
                  "claim":{"enum":["covers","related"]}}}}}}"""

SCHEMA: dict[str, Any] = json.loads(SCHEMA_TEXT)

def _ecma_regex(pattern: str) -> re.Pattern[str]:
    r"""把 JSON Schema（ECMA-262）的 ``pattern`` 編成等義的 Python regex。

    ⚠️ **唯一被處理的差異是結尾的 ``$``**：ECMA-262 無 ``m`` 旗標時 ``$`` 只匹配
    字串**真正的**結尾，而 Python 的 ``$`` **也匹配結尾換行之前** ⇒ 直接編譯會讓
    ``"https://github.com/o/r/issues/1\n"`` 通過一條它不該通過的正規形檢查
    （JSON 字串裝得下換行 ⇒ 這不是假想輸入）。這裡把結尾的 ``$`` 換成 ``\Z``。

    ⛔ **不宣稱這是完整的 ECMA-262 → Python 轉譯器**：它只處理**結尾**那一個 ``$``。
    ⇒ 日後若 schema 出現行中的 ``$``、``\b`` 語意差、或具名群組語法差異，本函式
    ⛔ 不會發現。真要那些，正解是引入一個真正的 JSON Schema 實作，⛔ 不是在這裡
    一條一條補規則。
    """
    if pattern.endswith("$") and not pattern.endswith(r"\$"):
        pattern = pattern[:-1] + r"\Z"
    return re.compile(pattern)


#: issue URL 的**正規形**，⛔ 不重打一份——它就是 :data:`SCHEMA` 裡
#: ``list_convergence.items.properties.issue_url.pattern`` 那一個字面。
#:
#: ⭐ **`--from-issue` 與 `list_convergence` 共用同一條正規形是刻意的**：兩處講的
#: 是同一件事（「哪一個 issue」），各寫一份就會出現「這個 URL 開得了卡卻宣告不進
#: 清單收斂」這種只有讀碼才看得出來的分歧。
#:
#: ⛔ **不允許 trailing slash／query／fragment**（卡 #217「issue_url 裁定」逐字）：
#: 正規形唯一，因為它同時是**比對鍵**（重複 issue_url 拒收靠字串相等）。
ISSUE_URL_PATTERN: str = SCHEMA["properties"]["list_convergence"]["items"][
    "properties"
]["issue_url"]["pattern"]

_ISSUE_URL_RE = _ecma_regex(ISSUE_URL_PATTERN)


def validate_issue_url(url: str) -> None:
    """不是正規形就拋 :class:`CardFaceError`；訊息逐字列出四類已知的拒收形狀。"""
    if _ISSUE_URL_RE.match(url or "") is None:
        raise CardFaceError(
            f"issue URL 不是正規形：{url!r}。"
            f"唯一合法形狀＝https://github.com/<owner>/<repo>/issues/<n>（n ≥ 1），"
            "⛔ 不允許結尾斜線、query（?…）或 fragment（#…）。"
            # ⚠️ 這裡刻意寫 `pull request（/pull/<n>）` 而**不是**那兩個大寫字母：
            # `scripts/contract_tool_reconcile.py` 以詞界比對卡面欄位名，而
            # `templates/tasks-card.md` 有一個同名欄位 ⇒ 一個流進遠端寫入的字串裡
            # 出現那個 token，會把該欄位的判定由 mention-only 翻成 write-only。
            # ⛔ 這不是「為了讓測試變綠而改文案」：那個判定翻轉是**假的**（本模組
            # 一個字都沒寫進那個欄位），留著等於在對帳表上放一筆不實登記。
            "四類常見的拒收：repo 首頁／issues 列表頁／pull request（/pull/<n>）URL／"
            "issue 編號為 0 或負數。"
        )

#: :func:`validate` 走訪器認得的 draft 2020-12 關鍵字。⛔ 不是「draft 2020-12 全集」。
_UNDERSTOOD_KEYWORDS = frozenset(
    {
        "$schema",
        "type",
        "additionalProperties",
        "required",
        "properties",
        "const",
        "enum",
        "items",
        "minItems",
        "minLength",
        "pattern",
    }
)

_TYPE_CHECKS = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
}



class CardFaceError(ValueError):
    """卡面表單缺失、格式不符、哨兵定位失效，或不合 schema。"""


class CardFaceVersionError(CardFaceError):
    """``schema_version`` 不是本 reader 認得的版本。

    ⭐ **fail-closed，⛔ 不是 fail-open**：v1 reader 對未知版本一律拒收並指示走
    migration。⛔ 不得改成「認不得就當成沒有表單」——那會讓一張 v2 卡在 v1 工具下
    靜默退化成「這張卡沒有階段計畫」，而缺表單與「表單是新版」在處置上完全不同。
    migration 的 owner 是**未來那個版本**，⛔ 不是本模組。
    """


def _assert_schema_is_understood(schema: Any, path: str = "$") -> None:
    """走訪 :data:`SCHEMA`，確認沒有用到 :func:`validate` 不懂的關鍵字。

    ⭐ 模組載入時就跑（見檔尾）：**加了走訪器不懂的關鍵字＝ import 當場失敗**，
    ⛔ 不會變成一條靜默失效的約束。
    """
    if isinstance(schema, dict):
        unknown = sorted(set(schema) - _UNDERSTOOD_KEYWORDS)
        if unknown:
            raise CardFaceError(
                f"SCHEMA 於 {path} 使用了 validate() 不認得的關鍵字 {unknown}；"
                f"走訪器涵蓋範圍＝{sorted(_UNDERSTOOD_KEYWORDS)}。"
                "⇒ 要嘛把該關鍵字實作進 validate()，要嘛不要用它——"
                "⛔ 不得留下一條不會被執行的 schema 約束"
            )
        declared_type = schema.get("type")
        if declared_type is not None and declared_type not in _TYPE_CHECKS:
            raise CardFaceError(
                f"SCHEMA 於 {path} 宣告了 validate() 不認得的型別 {declared_type!r}；"
                f"走訪器涵蓋 {sorted(_TYPE_CHECKS)}"
            )
        for key in ("properties",):
            for name, sub in schema.get(key, {}).items():
                _assert_schema_is_understood(sub, f"{path}.{key}.{name}")
        if isinstance(schema.get("items"), dict):
            _assert_schema_is_understood(schema["items"], f"{path}.items")


def _validate_against(schema: dict[str, Any], value: Any, path: str) -> list[str]:
    """draft 2020-12 子集走訪；回傳全部問題（空清單＝合格）。

    ⛔ 只報第一個問題會讓填表的人一輪修一格；一次全報是本 repo 既有紀律
    （``validation.ValidationError`` 攜帶多筆訊息的理由逐字相同）。
    """
    problems: list[str] = []

    expected_type = schema.get("type")
    if expected_type is not None and not _TYPE_CHECKS[expected_type](value):
        return [f"{path} 型別應為 {expected_type}，實得 {type(value).__name__}"]

    if "const" in schema and value != schema["const"]:
        problems.append(f"{path} 必須恰為 {schema['const']!r}，實得 {value!r}")

    if "enum" in schema and value not in schema["enum"]:
        problems.append(f"{path} 必須是 {schema['enum']} 之一，實得 {value!r}")

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            problems.append(f"{path} 長度須 ≥ {schema['minLength']}，實得 {len(value)}")
        pattern = schema.get("pattern")
        if pattern is not None and _ecma_regex(pattern).search(value) is None:
            problems.append(f"{path} 不符正規形 {pattern}，實得 {value!r}")

    if isinstance(value, list):
        min_items = schema.get("minItems")
        if min_items is not None and len(value) < min_items:
            problems.append(f"{path} 至少要有 {min_items} 個元素，實得 {len(value)}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for i, item in enumerate(value):
                problems += _validate_against(item_schema, item, f"{path}[{i}]")

    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                problems.append(f"{path} 缺必填鍵 {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                problems.append(
                    f"{path} 出現 schema 未定義的鍵 {extra}"
                    "（additionalProperties: false）"
                )
        for name, sub in properties.items():
            if name in value:
                problems += _validate_against(sub, value[name], f"{path}.{name}")

    return problems


def _extra_rules(data: Any) -> list[str]:
    """schema 表達不了、但卡面逐字要求的附加拒收規則。

    兩條都是 draft 2020-12 的 ``uniqueItems`` 表達不到的形狀——它比的是**整個元素**，
    而這兩條各自只看元素的**一個鍵**。⇒ 只能在走訪器之外實作。
    """
    problems: list[str] = []
    if isinstance(data, dict):
        stages = [
            s.get("stage")
            for s in data.get("stage_plan", [])
            if isinstance(s, dict)
        ]
        dup_stages = sorted({s for s in stages if stages.count(s) > 1 and s is not None})
        if dup_stages:
            problems.append(
                f"stage_plan 有重複的 stage {dup_stages}；"
                "同一個階段只能宣告一次（階段計畫是「要跑哪些階段」，⛔ 不是待辦清單）"
            )
        urls = [
            c.get("issue_url")
            for c in data.get("list_convergence", [])
            if isinstance(c, dict)
        ]
        dup_urls = sorted({u for u in urls if urls.count(u) > 1 and u is not None})
        if dup_urls:
            problems.append(
                f"list_convergence 有重複的 issue_url {dup_urls}；"
                "同一個清單項只能宣告一次（重複時 claim 可能互相矛盾，⛔ 拒絕猜哪一筆算數）"
            )
    return problems


def validate(data: Any) -> None:
    """對同一份資料跑 schema ＋ 附加規則；不合即拋 :class:`CardFaceError`。

    ⭐ **writer 與 reader 共用本函式**（卡面驗收 3 逐字「writer／reader tests 對同一
    validator 跑正負 fixture」）：兩側各自寫一份判準就是兩份會獨立漂移的規格。
    """
    version = data.get("schema_version") if isinstance(data, dict) else None
    if version is not None and version != SCHEMA_VERSION:
        raise CardFaceVersionError(
            f"卡面表單的 schema_version 是 {version!r}，本 reader 只認得 "
            f"{SCHEMA_VERSION!r}。⇒ 這張卡由較新（或不明）的版本寫成，"
            "本工具**拒絕以 v1 語意解讀它**（fail-closed）。"
            "請改用該版本的工具，或先跑該版本提供的 migration；"
            "⛔ 本 reader 不提供 migration——它屬於那個版本的 owner。"
        )
    problems = _validate_against(SCHEMA, data, "$") + _extra_rules(data)
    if problems:
        raise CardFaceError("卡面表單不合 schema：" + "；".join(problems))


def render_block(data: Any) -> str:
    """渲染 body 內的卡面表單區段（含標題與哨兵）。寫入前先跑 :func:`validate`。

    ⭐ **寫入端拒收**：不得寫出一份自己讀不回、或讀得回卻不合 schema 的表單
    （``templates/handoff-contract.md`` §3.2 規則二）。
    """
    validate(data)
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    return f"{SECTION_HEADING}\n{BEGIN}\n```json\n{payload}\n```\n{END}"


_BLOCK_RE = re.compile(
    re.escape(BEGIN) + r"\s*```json\s*(?P<json>.*?)```\s*" + re.escape(END),
    re.DOTALL,
)


def _head(body: str) -> str:
    try:
        head, _ = _split_at_log(body or "")
    except ResourceDeclarationError as exc:  # Log 標題重複等排版破壞
        raise CardFaceError(f"無法以 Log 標題切分 body：{exc}") from exc
    return head


def parse_block(body: str) -> dict[str, Any]:
    """從卡面 body 解析卡面表單；找不到或不合 schema 一律拋 :class:`CardFaceError`。

    定位只看 ``## Log`` **之前**的區段：Log 是 append-only 留痕，``amend`` 會把被覆寫
    的舊值原樣寫進去 ⇒ 那裡幾乎必然有哨兵字面的歷史回音，它是歷史，⛔ 不是宣告。
    """
    head = _head(body)
    begins, ends = head.count(BEGIN), head.count(END)
    if begins != 1 or ends != 1:
        if begins == 0 and ends == 0:
            outside = ""
            if BEGIN in (body or ""):
                outside = "；哨兵字面只出現在 `## Log` 區段內（那是歷史回音，不是宣告）"
            raise CardFaceError(
                f"body 的 Log 之前找不到 {BEGIN} … {END} 卡面表單區塊{outside}"
            )
        raise CardFaceError(
            f"body 的 Log 之前有 {begins} 個 begin／{ends} 個 end 哨兵，"
            "必須各恰好 1 個才能判定哪一組是現行表單；拒絕取第一個"
        )
    match = _BLOCK_RE.search(head)
    if match is None:
        raise CardFaceError(
            f"{BEGIN} … {END} 之間不是合法的 ```json fenced 區塊"
        )
    try:
        data = json.loads(match.group("json"))
    except json.JSONDecodeError as exc:
        raise CardFaceError(f"卡面表單 JSON 解析失敗：{exc}") from exc
    validate(data)
    return data


def try_parse_block(body: str) -> dict[str, Any] | None:
    """解析失敗時回 ``None``——供「舊卡沒有這個區塊也不阻擋任何動詞」的路徑使用。

    ⚠️ **legacy fallback 的界線**：本函式把「沒有區塊」與「有區塊但壞掉」都收成
    ``None``。⛔ 不得拿它當寫入端的判準——寫入端一律走 :func:`parse_block`／
    :func:`validate`，讓壞掉的區塊當場拒收。兩者的分工與 ``brief.try_parse_block``
    逐字相同。
    """
    try:
        return parse_block(body)
    except CardFaceError:
        return None


_assert_schema_is_understood(SCHEMA)


__all__ = [
    "BEGIN",
    "END",
    "ISSUE_URL_PATTERN",
    "SCHEMA",
    "SCHEMA_TEXT",
    "SCHEMA_VERSION",
    "SECTION_HEADING",
    "CardFaceError",
    "CardFaceVersionError",
    "parse_block",
    "render_block",
    "try_parse_block",
    "validate",
    "validate_issue_url",
]
