"""`brief`：把四層注入、必要清單與模型資料載出來給人或 AI 判斷。

⛔ 不判內容品質、⛔ 不選模型、⛔ 不呼叫 AI、⛔ 不查額度、⛔ 不判備註是否過期、
⛔ 不解析散文語意、⛔ 不判退回是否合法、⛔ 不認識「工作包」。
"""

from __future__ import annotations

from pathlib import Path

from wfx.core import layers, values
from wfx.core.render import render


def build(
    task: str,
    role: str,
    stage: str,
    rules_root: Path,
    project_root: Path,
    user_root: Path,
    task_snapshot: Path | None,
) -> str:
    values.check(rules_root, "角色", role)
    values.check(rules_root, "階段", stage)
    sections = [
        ("適用規則", layers.framework_rules(rules_root, role, stage)),
        ("必要清單", layers.required_checklist(rules_root, role, stage)),
        ("使用者層", layers.user_model_data(user_root)),
        ("專案層", layers.project_layer(project_root)),
        ("任務層", layers.task_layer(task_snapshot, task)),
    ]
    return render(task, role, stage, sections)
