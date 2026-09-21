"""四層注入。kind 恰四值：framework／user／project／task。

每段都是一個 Segment，輸出時逐段標示 `[來源: kind:path#節]`。
⛔ 不做 delta 合成、⛔ 不做模組層、⛔ 不解析散文語意。
"""

from __future__ import annotations

import json
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


def task_layer(snapshot_path: Path | None, task_id: str) -> list[Segment]:
    """任務層＝Issue body 五章節＋七個核心概念＋已貼出的階段完成留言。

    W1.6 的來源是一份固定快照；讀遠端當下值是 `facts`（W1.7）的事。
    三者一律原樣納入，⛔ 不解析、⛔ 不驗章節、⛔ 不判留言屬於哪一類。
    """
    if snapshot_path is None:
        raise LayerMissing("task", "--task-snapshot", "任務層資料來源未提供")
    if not snapshot_path.is_file():
        raise LayerMissing("task", str(snapshot_path))
    try:
        data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MalformedInput(f"任務層快照不是合法 JSON：{exc}") from exc
    if not isinstance(data, dict):
        raise MalformedInput("任務層快照的最外層必須是 object")

    snapshot_task = data.get("task")
    if snapshot_task != task_id:
        raise MalformedInput(
            f"任務層快照的 task 是 {snapshot_task!r}，與 --task {task_id!r} 不符"
        )

    body = data.get("issue_body")
    if not isinstance(body, str) or not body.strip():
        raise LayerMissing("task", f"{task_id}#issue-body", "快照缺 issue_body 或為空")

    fields = data.get("fields", {})
    if not isinstance(fields, dict):
        raise MalformedInput("任務層快照的 fields 必須是 object")
    unknown = sorted(set(fields) - set(CORE_CONCEPTS))
    if unknown:
        raise MalformedInput(
            f"fields 出現七個核心概念以外的鍵：{'、'.join(unknown)}"
        )

    comments = data.get("comments", [])
    if not isinstance(comments, list):
        raise MalformedInput("任務層快照的 comments 必須是 array")

    out = [Segment("task", task_id, "issue-body", body.strip("\n"))]
    rendered = "\n".join(f"{name}: {fields.get(name, '')}" for name in CORE_CONCEPTS)
    out.append(Segment("task", task_id, "核心概念", rendered))
    for index, comment in enumerate(comments, start=1):
        if not isinstance(comment, dict) or not isinstance(comment.get("body"), str):
            raise MalformedInput(f"comments[{index - 1}] 缺 body 或型別不對")
        lines = []
        url = comment.get("url")
        if isinstance(url, str) and url:
            lines.append(f"url: {url}")
        lines.append(comment["body"].strip("\n"))
        out.append(Segment("task", task_id, f"comment-{index}", "\n".join(lines)))
    return out
