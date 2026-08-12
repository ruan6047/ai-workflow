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
from collections.abc import Mapping
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
    accepted_marks: Mapping[str, AcceptedMark] | None = None,
    preflight_passed: bool = True,
) -> str:
    """渲染寫進 Issue timeline 的裁決留言（canonical §4.3「事件＝結構化 comment」）。

    ``accepted_marks`` 未給時以 ``default_accepted_marks`` 推導（全部 ``accepted=true``，
    見該函式對不對稱 fail-closed 的說明）；``counts_toward_escalation`` 一律由
    ``derive_counts_toward_escalation`` 依 §3 算出，**不接受呼叫端傳值**——它是投影，
    不是輸入（review-escalation.md:276）。
    """
    review_attempt_id = attempt_id(card_id, escalation_epoch, source_sha)
    marks = dict(accepted_marks or default_accepted_marks(report.findings))
    counts = derive_counts_toward_escalation(report, marks)
    lines = [
        (
            "<!-- wf-review-event:v1 "
            f"card_id={card_id} source_sha={source_sha} attempt_id={review_attempt_id} -->"
        ),
        f"## 查核裁決：{report.review_result}",
        "",
        f"- 卡：`{card_id}`　attempt_id：`{review_attempt_id}`",
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
        "### escalation 帳（lifecycle writer 標記，review-escalation.md §2／§3／§5）",
        "",
        render_escalation_facts_block(
            attempt=review_attempt_id,
            escalation_epoch=escalation_epoch,
            report=report,
            marks=marks,
            counts_toward_escalation=counts,
            preflight_passed=preflight_passed,
        ),
        "",
        "---",
        "",
        "本留言由 `wfcli review` 依 `templates/review-prompt.md` §5 驗證後寫入（唯一寫入通道，canonical §4.3）。",
        (
            "`accepted` 由本指令以 lifecycle writer 身分標記（reviewer 自填一律忽略）；"
            "`status` 新採認一律 `open`（review-escalation.md §2）；"
            "`counts_toward_escalation` 為依 §3 算出的投影，不接受手填。"
        ),
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# escalation 帳的結構化事實（WF-22-CLI4 切片 A）
# --------------------------------------------------------------------------
#
# 承載方式的選擇（需求方 2026-08-12 裁定，方案 B）：**既有六個動詞的既有慣例**
# ——Issue 留言內的 fenced 結構化區塊 ＋ Issue body ``## Log`` 的索引行，**不發新
# marker 前綴**。理由不是技術不可行（``doctor.inspect_event_marker`` 的管轄判準是
# body 是否含既有事件 marker 前綴，新前綴根本不進該函式），而是：#30 正在設計宣告行
# 三分類、#35 正在設計版本升級策略，此刻自立第三套 marker 文法就是 #35 開卡要制止
# 的形態。方案 B 之後追加 marker 不會使既有事件失效；反之則留下需要遷移的歷史。
#
# 也刻意不放 Project 欄位：checkpoint 是 append-only 事件、每 epoch 多筆、帶
# ``deferred_findings`` 陣列，而 Project 欄位是 current-state 單值且 ``FIELD_SPECS``
# 凍結。把事件壓成狀態會讓 review-escalation.md:272「完整 replay 必須僅憑事件流
# 重建」直接失效。

FINDING_STATUSES = ("open", "resolved", "withdrawn")
CHECKPOINT_DECISIONS = ("continue", "replan", "change-executor", "escalate")

# review-escalation.md §3 第 3～4 款：只有這兩個 class ＋ executor 歸屬的 blocking
# finding 才可能讓 attempt 計入 escalation 額度。
COUNTING_FINDING_CLASSES = ("implementation", "authoritative-artifact")
COUNTING_ATTRIBUTION = "executor"

BLOCK_VERSION = "v1"
FACTS_BLOCK_KEY = "wf_escalation_facts"
CHECKPOINT_BLOCK_KEY = "wf_escalation_checkpoint"
BASELINE_BLOCK_KEY = "wf_contract_baseline"

# Log 索引行的固定前綴：與 assign／handoff／review 既有慣例同形（``<動詞> by wf-cli``）。
CHECKPOINT_LOG_TAG = "checkpoint by wf-cli"
BASELINE_LOG_TAG = "contract-baseline by wf-cli"

# review-escalation.md §5：``attempt_id: <card>-e<epoch>-<full source sha>``。
# 與 ``doctor._ATTEMPT_RE`` 是同一條契約的兩份實作——doctor.py 不在本卡宣告的寫入集
# 內，無法把它抽成共用常數。形狀由契約固定，兩處同時失效的風險低於越界改檔的風險；
# 待 doctor.py 進入某張卡的寫入集時應合併。
_ATTEMPT_ID_RE = re.compile(r"^(?P<card>.+)-e(?P<epoch>\d+)-(?P<sha>[0-9a-f]{40})$")


# ``accepted=false`` 這個標記的**授權綁定**取值。形狀取自 review-escalation.md §4／§5
# 的 ``authorization_binding``（WF-ESCALATION-RESOLUTION-GAP1，ai-workflow#39），理由同源：
# 當「標記者不得是被該標記嘉惠的一方」這個比對在本專案結構上恆真時，正確的處置是**把恆真
# 本身寫進事件流**，而不是留下一個看似有檢查的欄位讓消費者誤讀成「已有第二方獨立核可」。
#
# ⚠️ 這**不是** #39 的那個欄位：#39 的 ``authorization_binding`` 是 ``escalation-resolution``
# 事件的必填欄，其導出依需求方帳號與被授權 writer 集合；此處是同一個述詞套在另一組角色
# （標記者 vs 被嘉惠的執行者）上。故另取名，不共用鍵名——若日後有契約卡定義 accepted 標記
# 的授權 schema，本鍵應服從該 schema。
ACCEPTED_MARKING_BINDINGS = ("substantive", "structurally-vacuous", "not-applicable")


@dataclass(frozen=True)
class AcceptedMark:
    """一個 finding 的 ``accepted`` 標記（review-escalation.md §2：lifecycle writer 職權）。

    ``marked_by``／``reason`` 只在 ``accepted=false`` 時有值：標 true 是保守方向
    （finding 留在 open set），標 false 才是把 finding 移出 open set、同時抹掉它對
    carry、對根因 occurrence 與對 attempt 計數的貢獻。

    ``binding`` 由 adapter 導出、**不得手填**，且 ``structurally-vacuous`` 時仍須寫出
    而非省略（省略與漏填無法區分，與 ``findings: []`` 必須顯式同一紀律）。
    ``accepted=true`` 是免旗標的預設、不行使任何授權，故取 ``not-applicable``。
    """

    finding_id: str
    accepted: bool
    reason: str = ""
    marked_by: str = ""
    binding: str = "not-applicable"


@dataclass(frozen=True)
class EscalationFacts:
    """一則已落地 review event 的 escalation 帳事實（自留言的結構化區塊讀回）。"""

    attempt_id: str
    escalation_epoch: int
    review_result: str
    counts_toward_escalation: bool


@dataclass(frozen=True)
class CheckpointFacts:
    """一則已落地 ``escalation-checkpoint`` 事件的事實。"""

    escalation_epoch: int
    trigger_attempt_id: str
    unique_attempt_count: int
    checkpoint_decision: str


def parse_attempt_id(value: str) -> tuple[str, int, str] | None:
    """反解 ``attempt_id`` → ``(card_id, epoch, source_sha)``；不合形式回 None。"""
    match = _ATTEMPT_ID_RE.match(value or "")
    if not match:
        return None
    return match.group("card"), int(match.group("epoch")), match.group("sha")


def counting_eligible(finding: Finding) -> bool:
    """§3 第 3～4 款：blocking ＋ implementation／authoritative-artifact ＋ executor。

    ``status`` 不在此判斷內：新採認的 blocking finding 依 §2 一律以 ``open`` 開始，
    而本函式只用於「本次裁決新提出的 finding」。跨 attempt 的 open set 演變屬
    checkpoint 的歷史推導（切片 B，被 #30 擋住），本卡不做。
    """
    return (
        finding.blocking
        and finding.finding_class in COUNTING_FINDING_CLASSES
        and finding.attribution == COUNTING_ATTRIBUTION
    )


def default_accepted_marks(findings: tuple[Finding, ...]) -> dict[str, AcceptedMark]:
    """``accepted`` 的預設值：**一律 true**，不需任何旗標。

    這是**不對稱的 fail-closed**，刻意不照 review-escalation.md §4 (a′) 那套綁平台
    身分——那是為 ``defer`` 設計的，兩者失效方向不同：

    - ``defer`` 的危險是**被嘉惠方自己裁定**，所以要求裁定者的平台身分不得是 owner／
      reviewer；
    - ``accepted`` 的危險是**被標成 false**——那會把 finding 移出 open set，同時抹掉
      它對 carry、對根因 occurrence 與對 attempt 計數的貢獻。標成 true 是保守方向。

    因此 true 免旗標、false 要顯式旗標＋非空理由＋``marked_by``（見
    ``validation.validate_accepted_overrides``／``validate_marked_by``）。

    非 §3 第 3～4 款的 finding（governance／coordination／environment，或非 executor
    歸屬）同樣預設 true：那對它們不具承載力——依 §4「有效 open finding」的定義，
    它們無論 ``accepted`` 為何都不進 carry set，也不會讓 attempt 計數。統一預設可以
    少一條分支，方向仍是保守側。
    """
    return {f.finding_id: AcceptedMark(finding_id=f.finding_id, accepted=True) for f in findings}


def derive_counts_toward_escalation(
    report: ReviewReport, marks: Mapping[str, AcceptedMark]
) -> bool:
    """§3 的四款推導；``review-escalation.md:276``：這是投影，不得由 reviewer 自填。

    第 1 款（preflight 已通過且 review 有效）在此**由事件型別本身承擔**：§1 明定
    preflight 失敗寫 ``preflight-failed``、無效查核寫 ``review-invalid``，兩者都
    「不得建立 review event」。因此「有一則 review event 存在」即蘊含第 1 款。
    **這是約定不是強制**：本 CLI 沒有任何機械執行者去證實 preflight 真的跑過，
    只有 ``review_invalid_reasons`` 擋掉可機械判定的那一種無效查核。

    第 2～4 款則完全機械：結論為 ``REQUEST_CHANGES``，且存在至少一個
    ``accepted=true`` 的 §3 第 3～4 款 blocking finding（``status`` 依 §2 為 ``open``）。
    """
    if report.review_result != "REQUEST_CHANGES":
        return False
    for finding in report.findings:
        if not counting_eligible(finding):
            continue
        mark = marks.get(finding.finding_id)
        if mark is None or mark.accepted:
            return True
    return False


# --------------------------------------------------------------------------
# 結構化區塊的渲染與讀回
# --------------------------------------------------------------------------


def _yaml_scalar(value: Any) -> str:
    """把值渲染成 ``_parse_yaml_subset`` 讀得回來的純量。

    只要含空白、``#``、``:``、引號或為空字串就加雙引號——受限解析器對這些形態
    刻意拒收（歧義不猜），加引號是唯一不會在 round-trip 時失真的寫法。
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = " ".join(str(value).split())
    if text == "" or any(ch in text for ch in " #:\"'[]{}|&*") or text.startswith("-"):
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return text


def render_escalation_facts_block(
    *,
    attempt: str,
    escalation_epoch: int,
    report: ReviewReport,
    marks: Mapping[str, AcceptedMark],
    counts_toward_escalation: bool,
    preflight_passed: bool = True,
) -> str:
    """渲染 review event 的 escalation 帳區塊（review-escalation.md §5 的 adapter 欄位）。

    ``self_run`` 不重複進本區塊：它已逐項落在留言散文，複製一份只會讓同一事實有兩個
    可能不同步的來源。本區塊只承載**先前只存在於人腦裡**的那幾件事——``accepted``、
    ``status`` 與 ``counts_toward_escalation``。
    """
    lines = [
        "```yaml",
        f"{FACTS_BLOCK_KEY}: {BLOCK_VERSION}",
        f"attempt_id: {_yaml_scalar(attempt)}",
        f"escalation_epoch: {escalation_epoch}",
        f"preflight_passed: {_yaml_scalar(preflight_passed)}",
        f"review_result: {report.review_result}",
        f"core_pain_resolved: {report.core_pain_resolved}",
        f"counts_toward_escalation: {_yaml_scalar(counts_toward_escalation)}",
    ]
    if not report.findings:
        lines.append("findings: []")
    else:
        lines.append("findings:")
        for finding in report.findings:
            mark = marks.get(finding.finding_id) or AcceptedMark(
                finding_id=finding.finding_id, accepted=True
            )
            lines += [
                f"  - finding_id: {_yaml_scalar(finding.finding_id)}",
                f"    accepted: {_yaml_scalar(mark.accepted)}",
                f"    accepted_marked_by: {_yaml_scalar(mark.marked_by)}",
                f"    accepted_marking_binding: {mark.binding}",
                f"    accepted_reason: {_yaml_scalar(mark.reason)}",
                "    status: open",
                f"    blocking: {_yaml_scalar(finding.blocking)}",
                f"    finding_class: {finding.finding_class}",
                f"    attribution: {finding.attribution}",
                f"    root_cause_id: {_yaml_scalar(finding.root_cause_id)}",
                f"    counting_eligible: {_yaml_scalar(counting_eligible(finding))}",
            ]
    lines.append("```")
    return "\n".join(lines)


def find_block_by_key(text: str, key: str) -> dict[str, Any] | None:
    """取出留言中頂層含 ``key`` 的 fenced 結構化區塊；沒有回 None，多於一個拒收。

    與 ``extract_structured_block`` 同一條紀律：**不做「取最後一個」這種順序啟發式**。
    一則留言同時含兩個同型區塊時無法判定哪個算數，一律 fail closed。
    """
    hits: list[dict[str, Any]] = []
    for lang, content in _iter_fenced_blocks(text):
        if not re.search(rf"^[ \t]*[\"']?{re.escape(key)}[\"']?[ \t]*:", content, re.MULTILINE):
            continue
        if lang == "json":
            try:
                data = json.loads(content)
            except json.JSONDecodeError as exc:
                raise ReviewParseError(f"{key} 區塊不是合法 JSON：{exc}") from exc
            if not isinstance(data, dict):
                raise ReviewParseError(f"{key} 區塊的 JSON 頂層必須是物件")
        else:
            data = _parse_yaml_subset(content)
        if key in data:
            hits.append(data)
    if not hits:
        return None
    if len(hits) > 1:
        raise ReviewParseError(
            f"同一則留言出現 {len(hits)} 個 {key} 區塊，無法判定哪一個算數；一律拒收"
        )
    return hits[0]


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text == "true":
        return True
    if text == "false":
        return False
    return None


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def escalation_facts_from_body(body: str) -> EscalationFacts | None:
    """自一則 review event 留言讀回 escalation 帳事實；欄位讀不齊一律回 None。

    回 None 代表「**未知**」而不是「不計數」——呼叫端（``validation`` 的閘門）必須
    據此 fail-closed。這正是 review-escalation.md:276 的 cutover 語意：baseline 之前
    的 attempt 沒有 counts 事實，不得推定為不計數。
    """
    data = find_block_by_key(body, FACTS_BLOCK_KEY)
    if data is None:
        return None
    if str(data.get(FACTS_BLOCK_KEY)).strip() != BLOCK_VERSION:
        return None
    attempt = str(data.get("attempt_id") or "").strip()
    epoch = _as_int(data.get("escalation_epoch"))
    counts = _as_bool(data.get("counts_toward_escalation"))
    result = str(data.get("review_result") or "").strip()
    if not attempt or epoch is None or counts is None or result not in REVIEW_RESULTS:
        return None
    decomposed = parse_attempt_id(attempt)
    if decomposed is None or decomposed[1] != epoch:
        return None
    return EscalationFacts(
        attempt_id=attempt,
        escalation_epoch=epoch,
        review_result=result,
        counts_toward_escalation=counts,
    )


def checkpoint_facts_from_body(body: str) -> CheckpointFacts | None:
    """自一則留言讀回 ``escalation-checkpoint`` 事實；欄位讀不齊一律回 None。"""
    data = find_block_by_key(body, CHECKPOINT_BLOCK_KEY)
    if data is None:
        return None
    if str(data.get(CHECKPOINT_BLOCK_KEY)).strip() != BLOCK_VERSION:
        return None
    trigger = str(data.get("trigger_attempt_id") or "").strip()
    epoch = _as_int(data.get("escalation_epoch"))
    count = _as_int(data.get("unique_attempt_count"))
    decision = str(data.get("checkpoint_decision") or "").strip()
    if not trigger or epoch is None or count is None or decision not in CHECKPOINT_DECISIONS:
        return None
    return CheckpointFacts(
        escalation_epoch=epoch,
        trigger_attempt_id=trigger,
        unique_attempt_count=count,
        checkpoint_decision=decision,
    )


def body_has_contract_baseline(body: str) -> bool:
    """該留言是否為 ``contract-baseline`` one-shot 事件。"""
    data = find_block_by_key(body, BASELINE_BLOCK_KEY)
    return data is not None and str(data.get(BASELINE_BLOCK_KEY)).strip() == BLOCK_VERSION


def log_line_indexes(card_body: str, tag: str, token: str) -> bool:
    """Issue body ``## Log`` 是否有**同一行**同時含 ``tag`` 與 ``token`` 的索引行。

    ``token`` 以邊界比對，不用 ``in``：``attempt in line`` 會讓 ``…-e0-<sha>`` 命中
    ``…-e0-<sha>x``（doctor 已踩過三次的同一個子字串陷阱）。
    """
    boundary = re.compile(rf"(?<![\w-]){re.escape(token)}(?![\w-])")
    return any(
        tag in line and boundary.search(line) for line in (card_body or "").splitlines()
    )


def render_checkpoint_comment(
    *,
    card_id: str,
    escalation_epoch: int,
    trigger_attempt_id: str,
    unique_attempt_count: int,
    checkpoint_decision: str,
    checkpoint_rationale: str,
    written_by: str,
    timestamp: str,
) -> str:
    """渲染 ``escalation-checkpoint`` 事件留言（review-escalation.md §5 必填欄位）。

    **不發 marker**：本事件走既有的「fenced 區塊 ＋ Log 索引行」慣例（見上方模組註）。
    ``deferred_findings`` 固定渲染為空陣列——§4 的兩個 defer cause 在本 repo 今天都
    不可用（(c)／(c′) 明文 fail-closed），寫入端拒收，見
    ``validation.validate_checkpoint_input``。
    """
    rationale_lines = [f"  {line}".rstrip() for line in checkpoint_rationale.splitlines()]
    lines = [
        f"## Escalation checkpoint：{card_id} e{escalation_epoch}",
        "",
        f"- trigger_attempt_id：`{trigger_attempt_id}`",
        f"- 寫入者：{_fence_safe(written_by)}　寫入時間：{timestamp}",
        "",
        "```yaml",
        f"{CHECKPOINT_BLOCK_KEY}: {BLOCK_VERSION}",
        f"escalation_epoch: {escalation_epoch}",
        f"trigger_attempt_id: {_yaml_scalar(trigger_attempt_id)}",
        f"unique_attempt_count: {unique_attempt_count}",
        f"checkpoint_decision: {checkpoint_decision}",
        "checkpoint_rationale: |",
        *rationale_lines,
        "deferred_findings: []",
        "```",
        "",
        "---",
        "",
        (
            "本留言由 `wfcli checkpoint` 寫入。`unique_attempt_count` 與 `checkpoint_decision` "
            "由操作者提供並留痕，**未由事件流機械推導**——§4／§5 的兩個條件需要跨 attempt 的 "
            "carry set 與根因 occurrence 推導，該能力被 `review-marker-clearance` 的留痕解析停機"
            "（§1，解除表示法未定義）擋住，見 `docs/CONSUMER_CONFORMANCE.md` 落差 7。"
        ),
    ]
    return "\n".join(lines)


def render_contract_baseline_comment(
    *,
    card_id: str,
    declared_by: str,
    rationale: str,
    timestamp: str,
) -> str:
    """渲染 ``contract-baseline`` one-shot cutover 事件（review-escalation.md:276）。"""
    return "\n".join(
        [
            f"## Contract baseline：{card_id}",
            "",
            "```yaml",
            f"{BASELINE_BLOCK_KEY}: {BLOCK_VERSION}",
            "contract: templates/review-escalation.md",
            f"effective_from: {_yaml_scalar(timestamp)}",
            f"declared_by: {_yaml_scalar(declared_by)}",
            f"rationale: {_yaml_scalar(rationale)}",
            "```",
            "",
            "---",
            "",
            (
                "此 marker 為 one-shot cutover（`review-escalation.md` §5）：不得附在 review 等其他"
                "事件上，啟用後再次出現必須 fail loud。本行之前的 attempt 依契約「維持原貌」，"
                "其 `counts_toward_escalation` 為**未知**（而非「不計數」）；本行之後的 review "
                "event 一律由 `wfcli review` 附上結構化 counts 事實。"
            ),
        ]
    )


__all__ = [
    "ACCEPTED_MARKING_BINDINGS",
    "ATTRIBUTIONS",
    "BASELINE_BLOCK_KEY",
    "BASELINE_LOG_TAG",
    "BLOCK_VERSION",
    "CHECKPOINT_BLOCK_KEY",
    "CHECKPOINT_DECISIONS",
    "CHECKPOINT_LOG_TAG",
    "CORE_PAIN_VALUES",
    "COUNTING_ATTRIBUTION",
    "COUNTING_FINDING_CLASSES",
    "FACTS_BLOCK_KEY",
    "FINDING_CLASSES",
    "FINDING_KEYS",
    "FINDING_STATUSES",
    "REVIEW_RESULTS",
    "SEVERITIES",
    "STATUS_BY_RESULT",
    "WRITER_ONLY_KEYS",
    "AcceptedMark",
    "CheckpointFacts",
    "EscalationFacts",
    "Finding",
    "ReviewParseError",
    "ReviewReport",
    "SelfRunEntry",
    "attempt_id",
    "body_has_contract_baseline",
    "checkpoint_facts_from_body",
    "counting_eligible",
    "default_accepted_marks",
    "derive_counts_toward_escalation",
    "escalation_facts_from_body",
    "extract_structured_block",
    "find_block_by_key",
    "log_line_indexes",
    "parse_attempt_id",
    "parse_structured_block",
    "render_checkpoint_comment",
    "render_contract_baseline_comment",
    "render_escalation_facts_block",
    "render_verdict_comment",
]
