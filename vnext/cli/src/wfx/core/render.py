"""輸出組版。全部輸入不變時逐字穩定：⛔ 無時間戳、⛔ 無絕對路徑、⛔ 無隨機序。"""

from __future__ import annotations

from wfx.core.layers import Segment


def _block(segments: list[Segment]) -> list[str]:
    out: list[str] = []
    for segment in segments:
        out.append(segment.marker())
        out.append(segment.body)
        out.append("")
    return out


def render(
    task: str,
    role: str,
    stage: str,
    sections: list[tuple[str, list[Segment]]],
) -> str:
    lines = [
        "# brief",
        f"task: {task}",
        f"role: {role}",
        f"stage: {stage}",
        "",
    ]
    for title, segments in sections:
        lines.append(f"## {title}")
        lines.append("")
        lines.extend(_block(segments))
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"
