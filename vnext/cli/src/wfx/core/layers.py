"""四層注入。kind 恰四值：framework／user／project／task。

每段都是一個 Segment，輸出時逐段標示 `[來源: kind:path#節]`。
⛔ 不做 delta 合成、⛔ 不做模組層、⛔ 不解析散文語意。
已啟用的選用文件模組住在框架規則樹，因此仍是 `framework` 段，⛔ 不是第五種 kind。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import unicodedata

from wfx.core.errors import LayerMissing, MalformedInput
from wfx.core import rules

KINDS = ("framework", "user", "project", "task")

# 七個核心概念的落地與值見 rules/core/github.md §2；此處只固定呈現順序。
CORE_CONCEPTS = ("狀態", "階段", "owner", "風險", "緊急性", "期限", "Resource")

# 使用者層的兩類模型資料（rules/core/boundaries.md §2）。兩者都缺＝合法 unknown。
USER_MODEL_FILES = ("model-usage.md", "model-availability.md")

UNKNOWN_MODEL_DATA = "使用者層模型資料：unknown"


@dataclass(frozen=True)
class Segment:
    kind: str
    path: str
    section: str
    body: str

    def marker(self) -> str:
        return f"[來源: {self.kind}:{self.path}#{self.section}]"


# 會斷行或不可見的字元：控制字元（含 LF／CR）與 Unicode 行／段分隔符。
_LINE_BREAKING = ("Cc", "Zl", "Zp")


def _one_line(text: str) -> str:
    """檔名裡會斷行或不可見的字元換成 escape 寫法（`\\n`、`\\x1b`、`\\u2028`…），其餘字元原樣保留。"""
    return "".join(
        ch.encode("unicode_escape").decode("ascii") if unicodedata.category(ch) in _LINE_BREAKING else ch
        for ch in text
    )


def _read_utf8(path: Path, display: str) -> str:
    """讀使用者層／專案層的一份檔案；不是 UTF-8＝`MalformedInput`（rc=1）。

    訊息單行、只帶顯示路徑（`~/.wf/<檔名>`、`.wf/<檔名>`），⛔ 不含絕對路徑；顯示路徑來自檔名，
    其中會斷行的字元一律 escape，訊息才保證是一行。
    ⛔ 不改用其他編碼、⛔ 不替換壞字元、⛔ 不捕捉 `UnicodeDecodeError` 以外的例外。
    """
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise MalformedInput(f"{_one_line(display)} 不是 UTF-8，編碼讀取失敗：{exc}") from exc


def _doc_segments(rel: str, text: str) -> list[Segment]:
    return [
        Segment("framework", rel, section, body)
        for section, body in rules.split_sections(text)
    ]


def framework_rules(rules_root: Path, role: str, stage: str) -> list[Segment]:
    """core 六份全載；stages／roles 各載選定的那一份。"""
    segments: list[Segment] = []
    for rel, text in rules.core_docs(rules_root):
        segments.extend(_doc_segments(rel, text))
    for rel, text in (
        rules.stage_doc(rules_root, stage),
        rules.role_doc(rules_root, role),
    ):
        segments.extend(_doc_segments(rel, text))
    return segments


def module_docs(rules_root: Path, names, stages, stage: str) -> list[tuple[str, tuple[str, str] | None]]:
    """已啟用模組（依 `.wf/config.json` 的宣告順序）在當前階段的文件；該階段沒有文件＝None。

    每個已啟用模組都完整驗過，不論當前階段——名稱打錯在任何階段都 typed 失敗，⛔ 不靜默略過。
    """
    return [(name, rules.module_stage_docs(rules_root, name, stages).get(stage)) for name in names]


def module_segments(docs) -> list[Segment]:
    return [segment for _, doc in docs if doc for segment in _doc_segments(*doc)]


def required_checklist(rules_root: Path, role: str, stage: str) -> list[Segment]:
    """必要清單＝該角色與該階段兩份文件的章節逐項列出。

    ⛔ 不改寫、⛔ 不排序、⛔ 不判哪一項重要——只是把清單載出來給讀者逐項對。
    """
    out: list[Segment] = []
    for rel, text in (
        rules.role_doc(rules_root, role),
        rules.stage_doc(rules_root, stage),
    ):
        items = "\n".join(f"- {h}" for h in rules.headings(text))
        if items:
            out.append(Segment("framework", rel, "章節", items))
    return out


def user_model_data(user_root: Path) -> list[Segment]:
    """使用者層兩檔原樣呈現；缺檔是合法的 unknown，⛔ 不是失敗。

    ⛔ 不判時效、⛔ 不逐則判欄位缺漏、⛔ 不解析內容。
    """
    out: list[Segment] = []
    for name in USER_MODEL_FILES:
        path = user_root / name
        display = f"~/.wf/{name}"
        if path.is_file():
            out.append(Segment("user", display, "全文", _read_utf8(path, display).strip("\n")))
        else:
            out.append(Segment("user", display, "缺", UNKNOWN_MODEL_DATA))
    return out


def project_layer(project_root: Path) -> list[Segment]:
    """專案層＝`<project-root>/.wf/` 下的 *.md（含 model-policy.md）。"""
    directory = project_root / ".wf"
    if not directory.is_dir():
        raise LayerMissing("project", ".wf", f"找不到 {directory}")
    paths = sorted(directory.glob("*.md"), key=lambda p: p.name)
    if not paths:
        raise LayerMissing("project", ".wf", "目錄下沒有專案層資料")
    return [
        Segment("project", f".wf/{p.name}", "全文", _read_utf8(p, f".wf/{p.name}").strip("\n"))
        for p in paths
    ]


def task_layer(data) -> list[Segment]:
    """任務層＝Issue body 五章節＋七個核心概念＋**該卡全部留言**（原樣，⛔ 不分類）。

    `data` 是動詞層交進來的純資料（`wfx.gh.task.TaskData`）——`wfx.core` ⛔ 不 import `wfx.gh`，
    也⛔ 不理解任務識別的格式。三者一律原樣納入，⛔ 不解析、⛔ 不驗章節、⛔ 不判留言屬於哪一類。
    """
    if not isinstance(data.fields, dict):
        raise MalformedInput("任務層的 fields 必須是 object")
    missing = [name for name in CORE_CONCEPTS if name not in data.fields]
    if missing:
        raise MalformedInput(f"任務層缺核心概念：{'、'.join(missing)}")
    body = data.issue_body
    if not isinstance(body, str) or not body.strip():
        raise LayerMissing("task", f"{data.task}#issue-body", "Issue body 缺或為空")

    out = [Segment("task", data.task, "issue-body", body.strip("\n"))]
    # 只投影七個核心概念；Project 的其餘內建欄位原樣忽略，⛔ 不是第八個核心概念、⛔ 不拒收
    rendered = "\n".join(f"{name}: {data.fields[name]}" for name in CORE_CONCEPTS)
    out.append(Segment("task", data.task, "核心概念", rendered))
    for index, (url, comment_body) in enumerate(data.comments, start=1):
        lines = [f"url: {url}"] if url else []
        lines.append((comment_body or "").strip("\n"))
        out.append(Segment("task", data.task, f"comment-{index}", "\n".join(lines)))
    return out


# ── 派工首屏：只由機械資料組成的定位索引 ────────────────────────────
# 全部內容都是路徑、節錨、行數、既有欄位值與 url。
# ⛔ 不摘要、⛔ 不判讀留言屬於哪一類、⛔ 不截斷任何原文——原文一律在附錄逐字保留。

NO_COMMENTS = "（該卡⛔ 無留言）"
NO_HEADING = "⛔ 無 ## 標題"


def _anchor_line(rel: str, text: str) -> str:
    anchors = [anchor for anchor, _ in rules.split_sections(text)]
    return f"- {rel}（{len(anchors)} 節）：" + "／".join(anchors)


def core_concept_values(data) -> Segment:
    """七個核心概念的當下值；與附錄任務層同一份投影，⛔ 不另行加工。"""
    rendered = "\n".join(f"{name}: {data.fields[name]}" for name in CORE_CONCEPTS)
    return Segment("task", data.task, "核心概念", rendered)


def rules_index(rules_root: Path) -> Segment:
    """core 六份的路徑與節錨。

    ⛔ 不印 rules-root 絕對路徑（那會讓逐字穩定隨機器而破）；
    stages／roles 兩份的節錨逐項列在「必要清單」，此處⛔ 不重複。
    """
    lines = [_anchor_line(rel, text) for rel, text in rules.core_docs(rules_root)]
    return Segment("framework", "rules/core/", "節索引", "\n".join(lines))


NO_MODULE_DOC = "本階段⛔ 無文件，⛔ 不注入"


def module_index(docs) -> Segment:
    """已啟用模組逐個一行：當前階段的文件路徑與節錨，或「本階段無文件」。全文在附錄。"""
    lines = [
        _anchor_line(*doc) if doc else f"- {rules.MODULES_DIR}/{name}/：{NO_MODULE_DOC}"
        for name, doc in docs
    ]
    return Segment("framework", f"rules/{rules.MODULES_DIR}/", "啟用模組", "\n".join(lines))


def project_policy_index(project_segments: list[Segment]) -> Segment:
    """第 3 層每份政策檔的路徑與節錨；全文在附錄。傳入的就是附錄那份，⛔ 不重讀檔案。"""
    lines = [_anchor_line(segment.path, segment.body) for segment in project_segments]
    return Segment("project", ".wf/", "節索引", "\n".join(lines))


def user_model_index(user_root: Path) -> Segment:
    """兩類模型資料的狀態與來源檔名；⛔ 不判時效、⛔ 不解析內容。"""
    lines = []
    for name in USER_MODEL_FILES:
        path = user_root / name
        if path.is_file():
            text = _read_utf8(path, f"~/.wf/{name}")
            filled = len([l for l in text.splitlines() if l.strip()])
            lines.append(f"- ~/.wf/{name}：在（{filled} 非空行，全文見附錄）")
        else:
            lines.append(f"- ~/.wf/{name}：{UNKNOWN_MODEL_DATA}")
    return Segment("user", "~/.wf/", "狀態", "\n".join(lines))


def issue_section_index(rules_root: Path, data) -> Segment:
    """Issue body 五章節的存在性與定位。

    `core/github.md` §1 明訂 CLI 只確認「標題在且其下非空」；本函式只做這件事，
    ⛔ 不解析散文語意。非五章節的 `## ` 標題一律照列，⛔ 不判它合不合法。
    """
    titles = rules.issue_section_titles(rules_root)
    # 五章節的存在／非空走 `rules.required_sections`＝與 `facts` 同一份解析來源
    required = rules.required_sections(titles, data.issue_body)
    lines = []
    for title, state, start, filled in required:
        if state == rules.MISSING:
            lines.append(f"- {title}：⛔ 標題不在 body")
        elif state == rules.EMPTY:
            lines.append(f"- {title}：標題在第 {start} 行、其下空")
        else:
            lines.append(f"- {title}：在（第 {start} 行，{filled} 非空行）")
    firsts = {title: start for title, _, start, _ in required}
    for anchor, start, _ in rules.section_spans(data.issue_body):
        if anchor not in titles:
            lines.append(f"- （五章節以外）{anchor}：第 {start} 行")
        elif start != firsts[anchor]:
            lines.append(f"- （同名重複）{anchor}：第 {start} 行")
    return Segment("task", data.task, "issue-body 章節", "\n".join(lines))


def comment_index(data) -> Segment:
    """全部留言逐則一行：編號、url、行數、該則首個 `## ` 標題（逐字）。

    ⛔ 不分類（`github.md` §3 的四類是內容分類，CLI 判不得）、⛔ 不挑「哪幾則是裁定」——
    裁定留言的定位靠 body §裁定紀錄 的連結索引與這份全量索引兩邊對照。
    """
    lines = []
    for index, (url, body) in enumerate(data.comments, start=1):
        text = (body or "").strip("\n")
        filled = len([l for l in text.splitlines() if l.strip()])
        heading = next(
            (l[3:].strip() for l in text.splitlines() if l.startswith("## ")), NO_HEADING
        )
        lines.append(f"- comment-{index}｜{url or '（⛔ 無 url）'}｜{filled} 非空行｜{heading}")
    return Segment("task", data.task, "留言索引", "\n".join(lines) or NO_COMMENTS)


# ── 相連任務（`core/github.md` §1 選用章節）：只對帶入角色呈現 ──────────────
# `linked` 是動詞層交進來的純資料（`wfx.gh.task.LinkedTask` 序列）；本層只讀屬性、⛔ 不理解 URL。
# 首屏只放機械事實（url／state／行號／行數／失敗類別），原文逐字在附錄。

LINKED_EMPTY = "（章節在，其下⛔ 無登記行）"
LINKED_COMMENT_SECTION = "已核定規劃"


def _linked_sections_line(entry, sections) -> str:
    parts = []
    for title, state, start, filled in rules.required_sections(sections, entry.body):
        if state == rules.MISSING:
            parts.append(f"{title}：⛔ 標題不在 body")
        elif state == rules.EMPTY:
            parts.append(f"{title}：標題在第 {start} 行、其下空")
        else:
            parts.append(f"{title}：在（第 {start} 行，{filled} 非空行）")
    return "｜".join(parts)


def _linked_comment_line(entry) -> str:
    if entry.comment_url is None:
        return f"{LINKED_COMMENT_SECTION}：未登記"
    if entry.comment_error is not None:
        return f"{LINKED_COMMENT_SECTION}：{entry.comment_url} 讀取失敗：{entry.comment_error}"
    if entry.comment_foreign is not None:
        return f"{LINKED_COMMENT_SECTION}：{entry.comment_url} 留言不屬於登記的相連卡：{entry.comment_foreign}"
    filled = len([l for l in entry.comment_body.splitlines() if l.strip()])
    return f"{LINKED_COMMENT_SECTION}：{entry.comment_url}（{filled} 非空行）"


def linked_index(task: str, linked, sections) -> Segment:
    """每筆登記一行：序號、相連卡 url、讀取結果、state、帶入章節定位、規劃留言定位。

    ⛔ 不判是否真的相連、⛔ 不判規劃是否已核定；形狀不合的行照原文印出，⛔ 不猜、⛔ 不略過。
    """
    lines = []
    for index, entry in enumerate(linked, start=1):
        if entry.issue_url is None:
            lines.append(f"- {index}｜無法解讀（逐字）：{entry.line}")
        elif entry.duplicate_of is not None:
            lines.append(f"- {index}｜{entry.issue_url}｜重複登記（同第 {entry.duplicate_of} 筆），⛔ 不重讀")
        elif entry.error is not None:
            lines.append(f"- {index}｜{entry.issue_url}｜讀取失敗：{entry.error}")
        else:
            lines.append(f"- {index}｜{entry.issue_url}｜{entry.state}｜"
                         f"{_linked_sections_line(entry, sections)}｜{_linked_comment_line(entry)}")
    return Segment("task", task, "相連任務定位", "\n".join(lines) or LINKED_EMPTY)


def linked_segments(linked, sections) -> list[Segment]:
    """每張讀到的相連卡：帶入章節逐字（標題在且其下非空者）＋登記的規劃留言全文。

    來源標記 kind 仍是 `task`（⛔ 不是第五種 kind），path＝相連卡 issue url（⛔ 不含 `#`）。
    """
    out: list[Segment] = []
    for entry in linked:
        if entry.issue_url is None or entry.duplicate_of is not None or entry.error is not None:
            continue
        for title in sections:
            text = rules.section_text(entry.body, title)
            if text:
                out.append(Segment("task", entry.issue_url, title, text))
        if entry.comment_body is not None:
            out.append(Segment("task", entry.issue_url, LINKED_COMMENT_SECTION,
                               f"url: {entry.comment_url}\n{entry.comment_body.strip(chr(10))}"))
    return out
