"""查核輸出契約：解析 ``templates/review-prompt.md`` §5 的結構化區塊。

本模組只負責**結構**（抽區塊、解析、資料類別、渲染裁決留言）；契約層的機械檢查
（必填欄、列舉值、``self_run`` 非空、第一判準否決權）集中在 ``validation.py``，
與 ``resources.py`` ／ ``validation.py`` 的既有分工一致。

## 為什麼自己寫解析器，不引 PyYAML

``pyproject.toml`` 的 ``dependencies`` 是空的（唯一寫入通道刻意零第三方 runtime
相依），但更關鍵的是**寬鬆解析與 fail-closed 互斥**：YAML 1.1 會把 ``yes`` 讀成
布林、把重複鍵靜默取最後一個、把 ``blocking: true`` 與 ``blocking: "true"`` 視為
不同型別。查核裁決是寫入通道的守門檢查，寧可看不懂就拒收，也不要猜錯還放行。

因此這裡實作的是 review-prompt.md §5 已經在用的**固定子集**，語法之外一律拒絕
（含 anchor／alias／flow mapping／巢狀序列／tab 縮排／重複鍵）：

- 頂層 ``key: value``（純量，可加引號）
- 頂層 ``key:`` ＋ 縮排的 ``- key: value`` mapping 序列；``key: []`` 表示空序列
- 區塊純量 ``|``／``|-``（``observed`` 常是多行輸出）

所有純量一律讀成**字串**，不做型別推斷；型別正規化（``blocking`` 的布林、
``core_pain_resolved`` 的 yes／no）留給 validation 層，以便 ```json 區塊（走
``json.loads``，天生有真布林）與 ```yaml 區塊走同一條檢查路徑。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

# 列舉值來源：templates/review-prompt.md §5＋templates/review-escalation.md §2。
REVIEW_RESULTS = ("APPROVE", "REQUEST_CHANGES")
CORE_PAIN_VALUES = ("yes", "no")
SEVERITIES = ("critical", "major", "minor", "info")
FINDING_CLASSES = (
    "implementation",
    "authoritative-artifact",
    "governance",
    "coordination",
    "environment",
)
ATTRIBUTIONS = ("executor", "planner", "coordinator", "reviewer", "external")

# review-prompt.md §5 的 finding 必填欄（reviewer 提交面）。
FINDING_KEYS = (
    "finding_id",
    "severity",
    "blocking",
    "finding_class",
    "attribution",
    "root_cause_id",
    "evidence",
    "disposition",
)

# review-escalation.md §2／§5：這些由 lifecycle writer 依可重現證據標記，
# reviewer 不得自行決定；出現在查核輸出裡只警示並忽略，不採用其值。
WRITER_ONLY_KEYS = ("accepted", "status", "counts_toward_escalation")

# review-escalation.md §1「實質查核」列：APPROVE→✅通過、REQUEST_CHANGES→↩退回。
STATUS_BY_RESULT = {"APPROVE": "✅通過", "REQUEST_CHANGES": "↩退回"}

_FENCE_OPEN_RE = re.compile(r"^```(yaml|yml|json)\s*$")
_FENCE_CLOSE = "```"
_KEY_LINE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)[ \t]*:(?:[ \t]+(.*))?$")
# 判斷「這個區塊是不是裁決」：YAML 要求頂層鍵在行首（避免把散文裡提到的
# review_result 誤認），JSON 則可能整份壓成一行，只能靠帶引號的鍵名比對。
_YAML_HAS_REVIEW_RESULT_RE = re.compile(r"^[ \t]*[\"']?review_result[\"']?[ \t]*:", re.MULTILINE)
_JSON_HAS_REVIEW_RESULT_RE = re.compile(r"[\"']review_result[\"']\s*:")


def _looks_like_verdict(lang: str, content: str) -> bool:
    pattern = _JSON_HAS_REVIEW_RESULT_RE if lang == "json" else _YAML_HAS_REVIEW_RESULT_RE
    return bool(pattern.search(content))


class ReviewParseError(ValueError):
    """查核輸出讀不到／看不懂；一律 fail closed，不猜測作者意圖。"""


@dataclass(frozen=True)
class SelfRunEntry:
    command: str
    observed: str


@dataclass(frozen=True)
class Finding:
    finding_id: str
    severity: str
    blocking: bool
    finding_class: str
    attribution: str
    root_cause_id: str
    evidence: str
    disposition: str


@dataclass(frozen=True)
class ReviewReport:
    """通過契約檢查後的查核裁決（``validation.validate_review_report`` 產出）。"""

    review_result: str
    core_pain_resolved: str
    self_run: tuple[SelfRunEntry, ...]
    findings: tuple[Finding, ...]
    writer_only_keys: tuple[str, ...] = ()

    @property
    def delivery_status(self) -> str:
        return STATUS_BY_RESULT[self.review_result]

    @property
    def blocking_findings(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.blocking)


def attempt_id(card_id: str, escalation_epoch: int, source_sha: str) -> str:
    """review-escalation.md §5：``attempt_id: <card>-e<epoch>-<full source sha>``。"""
    return f"{card_id}-e{escalation_epoch}-{source_sha}"


# --------------------------------------------------------------------------
# 區塊抽取
# --------------------------------------------------------------------------


def _iter_fenced_blocks(text: str) -> list[tuple[str, str]]:
    """回傳 ``[(lang, content), ...]``；只認 ```yaml／```yml／```json 三種圍籬。"""
    blocks: list[tuple[str, str]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        match = _FENCE_OPEN_RE.match(lines[i].strip())
        if not match:
            i += 1
            continue
        lang = match.group(1)
        body: list[str] = []
        i += 1
        closed = False
        while i < len(lines):
            if lines[i].strip() == _FENCE_CLOSE:
                closed = True
                i += 1
                break
            body.append(lines[i])
            i += 1
        if closed:
            blocks.append((lang, "\n".join(body)))
    return blocks


def extract_structured_block(text: str) -> tuple[str, str]:
    """從查核報告全文取出 §5 結構化區塊，回傳 ``(lang, content)``。

    選取規則（刻意不做「取最後一個」這種順序啟發式——查核報告常同時抄了範本
    區塊與實際裁決，順序猜錯就是靜默採用錯的裁決）：

    1. 掃出所有 ```yaml／```yml／```json 圍籬區塊，只留**含頂層 review_result 鍵**的。
    2. 剛好一個 → 用它；多於一個 → 拒收（要求作者只留一個）。
    3. 一個都沒有 → 若整份輸入自己就含 ``review_result:``（純 YAML／JSON 檔），
       整份當區塊；否則拒收。
    """
    if not text or not text.strip():
        raise ReviewParseError("查核輸出是空的：--input 檔案或 stdin 沒有任何內容")

    candidates = [
        (lang, content)
        for lang, content in _iter_fenced_blocks(text)
        if _looks_like_verdict(lang, content)
    ]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        raise ReviewParseError(
            f"找到 {len(candidates)} 個含 review_result 的結構化區塊，無法判定哪一個是本次裁決；"
            "請只保留一個（範本區塊請勿與實際裁決一起貼；見 templates/review-prompt.md §5）"
        )

    lang = "json" if text.lstrip().startswith("{") else "yaml"
    if _looks_like_verdict(lang, text):
        return lang, text
    raise ReviewParseError(
        "找不到含 review_result 的結構化區塊；查核報告必須附 templates/review-prompt.md §5 "
        "的 ```yaml 區塊（或整份輸入即該區塊）"
    )


# --------------------------------------------------------------------------
# 受限 YAML 子集解析
# --------------------------------------------------------------------------


def _is_skippable(line: str) -> bool:
    stripped = line.strip()
    return not stripped or stripped.startswith("#")


def _indent_of(line: str, lineno: int) -> int:
    prefix = line[: len(line) - len(line.lstrip(" \t"))]
    if "\t" in prefix:
        raise ReviewParseError(f"第 {lineno} 行以 tab 縮排；YAML 縮排只接受空白")
    return len(prefix)


# 單一 token ＋ 空白 ＋ #：註解無歧義（枚舉值、[]、| 都是單 token）。
_BARE_WORD_WITH_COMMENT_RE = re.compile(r"^(?P<word>[^\s\"'#]+)[ \t]+#")


def _value_token(rest: str | None) -> str:
    """把 ``key:`` 之後的原文正規化成「結構判定用」的 token。

    行內註解**只在無歧義時**切掉，因為 review-prompt.md §5 範本每一行都帶註解，
    照抄填值是最常見的用法：

    - 整段都是註解（``self_run:   # 必填：…``）→ 視同沒有值，也就是「鍵下面接序列」。
    - 值是單一 token 再接 ``' #'``（``review_result: APPROVE  # …``、``findings: []  # 無``、
      ``observed: |  # …``）→ 取該 token。枚舉值與結構符號本來就不含空白。

    片語後面接 ``' #'``（``evidence: 見 PR #12``）**不切**：那會靜默截成 ``見 PR``，
    截斷的 audit 記錄比被拒收糟得多。這種值由 ``_parse_scalar`` 拒收並要求加引號
    ——歧義不猜。
    """
    s = (rest or "").strip()
    if s.startswith("#"):
        return ""
    match = _BARE_WORD_WITH_COMMENT_RE.match(s)
    if match:
        return match.group("word")
    return s


def _parse_scalar(raw: str, lineno: int) -> str:
    s = _value_token(raw)
    if not s:
        return ""
    if s[0] in "\"'":
        return _parse_quoted(s, lineno)
    if " #" in s or "\t#" in s:
        raise ReviewParseError(
            f"第 {lineno} 行的值含 ' #'，無法判定是行內註解還是內容的一部分：{s!r}"
            "；請把值加上引號，或移除行內註解"
        )
    if s[0] in "&*":
        raise ReviewParseError(f"第 {lineno} 行使用 anchor／alias（{s[0]}），本解析器不支援")
    if s[0] == "{":
        raise ReviewParseError(f"第 {lineno} 行使用 flow mapping（{{...}}），請改用縮排區塊寫法")
    if s[0] == "[":
        raise ReviewParseError(
            f"第 {lineno} 行使用 flow 序列（[...]）；只接受空序列 [] 與縮排的 - 區塊序列"
        )
    if s in (">", ">-", ">+", "|+"):
        raise ReviewParseError(f"第 {lineno} 行的區塊純量 {s!r} 不支援；請改用 | 或 |-")
    return s


def _parse_quoted(s: str, lineno: int) -> str:
    quote = s[0]
    buf: list[str] = []
    i = 1
    closed = False
    while i < len(s):
        ch = s[i]
        if quote == '"' and ch == "\\" and i + 1 < len(s):
            buf.append(s[i + 1])
            i += 2
            continue
        if ch == quote:
            if quote == "'" and i + 1 < len(s) and s[i + 1] == "'":
                buf.append("'")
                i += 2
                continue
            closed = True
            i += 1
            break
        buf.append(ch)
        i += 1
    if not closed:
        raise ReviewParseError(f"第 {lineno} 行的引號未閉合：{s!r}")
    trailing = s[i:].strip()
    if trailing and not trailing.startswith("#"):
        raise ReviewParseError(f"第 {lineno} 行引號結束後仍有內容（{trailing!r}），無法判定值的範圍")
    return "".join(buf)


def _parse_block_scalar(
    lines: list[str], start: int, parent_indent: int, keep_trailing_newline: bool
) -> tuple[str, int]:
    """解析 ``|``／``|-`` 之後的縮排區塊；回傳 ``(值, 下一行索引)``。"""
    body: list[str] = []
    base: int | None = None
    i = start
    while i < len(lines):
        raw = lines[i]
        if not raw.strip():
            body.append("")
            i += 1
            continue
        indent = _indent_of(raw, i + 1)
        if indent <= parent_indent:
            break
        if base is None:
            base = indent
        body.append(raw[base:] if len(raw) >= base else raw.strip())
        i += 1
    while body and not body[-1].strip():
        body.pop()
    if base is None:
        raise ReviewParseError(f"第 {start} 行的區塊純量（|）後面沒有縮排內容")
    value = "\n".join(body)
    return (value + "\n" if keep_trailing_newline else value), i


def _parse_mapping_entry(
    lines: list[str], index: int, content: str, parent_indent: int, into: dict[str, Any]
) -> int:
    """把單行 ``key: value``（含可能的區塊純量）寫進 ``into``；回傳下一行索引。

    ``parent_indent`` 是這個鍵自己所在的欄位；區塊純量的內容必須**嚴格更深**才算
    同一個值，恰好同欄的行視為區塊結束（於是「忘了縮排的續行」會落到缺欄檢查，
    而不是被悄悄吞進上一個值）。
    """
    lineno = index + 1
    match = _KEY_LINE_RE.match(content)
    if not match:
        raise ReviewParseError(
            f"第 {lineno} 行不是可解析的 `key: value`：{content.strip()!r}"
            "（鍵只接受英數與 _ -，鍵與值之間需有空白）"
        )
    key, rest = match.group(1), _value_token(match.group(2))
    if key in into:
        raise ReviewParseError(f"第 {lineno} 行的鍵 {key!r} 重複；重複鍵會靜默覆蓋，一律拒收")
    if rest in ("|", "|-"):
        into[key], next_index = _parse_block_scalar(
            lines, index + 1, parent_indent, keep_trailing_newline=(rest == "|")
        )
        return next_index
    into[key] = _parse_scalar(rest, lineno)
    return index + 1


def _parse_sequence(lines: list[str], start: int) -> tuple[list[dict[str, Any]], int]:
    """解析縮排的 ``- key: value`` mapping 序列；回傳 ``(items, 下一行索引)``。"""
    items: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    dash_indent: int | None = None
    key_indent: int | None = None
    i = start
    while i < len(lines):
        raw = lines[i]
        if _is_skippable(raw):
            i += 1
            continue
        indent = _indent_of(raw, i + 1)
        if indent == 0:
            break
        stripped = raw.strip()
        if stripped.startswith("-"):
            after_dash = raw[indent + 1 :]
            lead = len(after_dash) - len(after_dash.lstrip(" "))
            if lead < 1:
                raise ReviewParseError(f"第 {i + 1} 行的 `-` 後面需要空白再接 `key: value`")
            if dash_indent is None:
                dash_indent = indent
                key_indent = indent + 1 + lead
            elif indent != dash_indent:
                raise ReviewParseError(
                    f"第 {i + 1} 行的序列縮排（{indent}）與第一項（{dash_indent}）不一致；"
                    "不支援巢狀序列"
                )
            current = {}
            items.append(current)
            assert key_indent is not None
            i = _parse_mapping_entry(lines, i, after_dash.strip(), key_indent, current)
            continue
        if current is None:
            raise ReviewParseError(f"第 {i + 1} 行縮排了但不屬於任何序列項目（序列項目須以 `- ` 開頭）")
        if indent != key_indent:
            raise ReviewParseError(
                f"第 {i + 1} 行縮排（{indent}）與同項目其他鍵（{key_indent}）不一致；"
                "不支援巢狀 mapping"
            )
        i = _parse_mapping_entry(lines, i, stripped, indent, current)
    return items, i


def _parse_yaml_subset(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    result: dict[str, Any] = {}
    i = 0
    while i < len(lines):
        raw = lines[i]
        if _is_skippable(raw):
            i += 1
            continue
        if _indent_of(raw, i + 1) != 0:
            raise ReviewParseError(f"第 {i + 1} 行縮排但沒有對應的頂層鍵：{raw.strip()!r}")
        match = _KEY_LINE_RE.match(raw)
        if not match:
            raise ReviewParseError(
                f"第 {i + 1} 行不是可解析的頂層 `key: value`：{raw.strip()!r}"
                "（區塊內不得混入散文；見 templates/review-prompt.md §5）"
            )
        key, rest = match.group(1), _value_token(match.group(2))
        if key in result:
            raise ReviewParseError(f"第 {i + 1} 行的頂層鍵 {key!r} 重複；重複鍵會靜默覆蓋，一律拒收")
        if rest == "":
            result[key], i = _parse_sequence(lines, i + 1)
            continue
        if rest == "[]":
            result[key] = []
            i += 1
            continue
        i = _parse_mapping_entry(lines, i, raw, 0, result)
    return result


def parse_structured_block(text: str) -> dict[str, Any]:
    """把整份查核輸出解析成 dict（``lang`` 決定走 json 還是受限 YAML 子集）。"""
    lang, content = extract_structured_block(text)
    if lang == "json":
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ReviewParseError(f"結構化區塊不是合法 JSON：{exc}") from exc
        if not isinstance(data, dict):
            raise ReviewParseError("結構化區塊的 JSON 頂層必須是物件（含 review_result 等鍵）")
        return data
    return _parse_yaml_subset(content)


# --------------------------------------------------------------------------
# 裁決留言渲染
# --------------------------------------------------------------------------


def _fence_safe(text: str) -> str:
    """留言內嵌使用者字串前先摺成單行，避免破壞 Markdown 條列結構。"""
    return " ".join(str(text).split())


def render_verdict_comment(
    *,
    card_id: str,
    report: ReviewReport,
    source_sha: str,
    reviewer: str,
    escalation_epoch: int,
    timestamp: str,
) -> str:
    """渲染寫進 Issue timeline 的裁決留言（canonical §4.3「事件＝結構化 comment」）。"""
    lines = [
        f"## 查核裁決：{report.review_result}",
        "",
        f"- 卡：`{card_id}`　attempt_id：`{attempt_id(card_id, escalation_epoch, source_sha)}`",
        f"- 查核者：{_fence_safe(reviewer)}　escalation_epoch：{escalation_epoch}",
        f"- source_sha：`{source_sha}`",
        f"- core_pain_resolved：**{report.core_pain_resolved}**"
        + ("（第一判準具否決權，canonical §5.1）" if report.core_pain_resolved == "no" else ""),
        f"- 交付狀態：{report.delivery_status}",
        f"- 寫入時間：{timestamp}",
        "",
        "### self_run（查核者實跑）",
        "",
    ]
    for entry in report.self_run:
        lines.append(f"- `{_fence_safe(entry.command)}`")
        for observed_line in str(entry.observed).strip().splitlines():
            lines.append(f"  - {observed_line.rstrip()}")
    lines += ["", f"### findings（{len(report.findings)}，其中 blocking {len(report.blocking_findings)}）", ""]
    if not report.findings:
        lines.append("- （無）")
    for f in report.findings:
        lines.append(
            f"- **{f.finding_id}**　severity={f.severity}　blocking={'true' if f.blocking else 'false'}"
            f"　class={f.finding_class}　attribution={f.attribution}　root_cause_id=`{f.root_cause_id}`"
        )
        lines.append(f"  - evidence：{_fence_safe(f.evidence)}")
        lines.append(f"  - disposition：{_fence_safe(f.disposition)}")
    lines += [
        "",
        "---",
        "",
        "本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。",
        (
            "`accepted`／`status`／`counts_toward_escalation` 依 `templates/review-escalation.md` §2／§3 "
            "由 lifecycle writer 另行標記，不在本指令的寫入範圍。"
        ),
    ]
    return "\n".join(lines)


__all__ = [
    "ATTRIBUTIONS",
    "CORE_PAIN_VALUES",
    "FINDING_CLASSES",
    "FINDING_KEYS",
    "REVIEW_RESULTS",
    "SEVERITIES",
    "STATUS_BY_RESULT",
    "WRITER_ONLY_KEYS",
    "Finding",
    "ReviewParseError",
    "ReviewReport",
    "SelfRunEntry",
    "attempt_id",
    "extract_structured_block",
    "parse_structured_block",
    "render_verdict_comment",
]
