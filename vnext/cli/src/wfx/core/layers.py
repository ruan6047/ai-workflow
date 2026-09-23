"""四層注入。kind 恰四值：framework／user／project／task。

每段都是一個 Segment，輸出時逐段標示 `[來源: kind:path#節]`。
⛔ 不做 delta 合成、⛔ 不做模組層、⛔ 不解析散文語意。
已啟用的選用文件模組住在框架規則樹，因此仍是 `framework` 段，⛔ 不是第五種 kind。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
            out.append(Segment("user", display, "全文", path.read_text(encoding="utf-8").strip("\n")))
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
        Segment("project", f".wf/{p.name}", "全文", p.read_text(encoding="utf-8").strip("\n"))
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
            filled = len([l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()])
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
