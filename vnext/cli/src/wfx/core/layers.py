"""四層注入。kind 恰四值：framework／user／project／task。

每段都是一個 Segment，輸出時逐段標示 `[來源: kind:path#節]`。
⛔ 不做 delta 合成、⛔ 不做模組層、⛔ 不解析散文語意。
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
