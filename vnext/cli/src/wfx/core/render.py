"""輸出組版。全部輸入不變時逐字穩定：⛔ 無時間戳、⛔ 無絕對路徑、⛔ 無隨機序。

輸出恰兩部分：`## 派工首屏`（機械資料）與 `## 完整原文附錄`（四層原文逐字）。
邊界＝`APPENDIX_HEADING` 這一行，可機械定位；⛔ 不做行數 gate、⛔ 不截斷、⛔ 不摘要。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from wfx.core.layers import Segment

FIRST_SCREEN_HEADING = "## 派工首屏"
APPENDIX_HEADING = "## 完整原文附錄"


@dataclass(frozen=True)
class Block:
    """一個標題區塊。`level` 只影響 `#` 個數；`note` 是本工具自己的結構說明、⛔ 不是來源內容。"""
    title: str
    segments: list = field(default_factory=list)
    level: int = 2
    note: str = ""


def _block(segments: list[Segment]) -> list[str]:
    out: list[str] = []
    for segment in segments:
        out.append(segment.marker())
        out.append(segment.body)
        out.append("")
    return out


def _emit(blocks: list[Block]) -> list[str]:
    lines: list[str] = []
    for block in blocks:
        lines.append(f"{'#' * block.level} {block.title}")
        if block.note:
            lines.append(block.note)
        if block.segments:
            lines.extend(_block(block.segments))
        else:
            lines.append("")
    return lines


def render(
    task: str,
    role: str,
    stage: str,
    first_screen: list[Block],
    appendix: list[Block],
) -> str:
    lines = [
        "# brief",
        f"task: {task}",
        f"role: {role}",
        f"stage: {stage}",
        "",
    ]
    lines.extend(_emit(first_screen))
    lines.extend(_emit(appendix))
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def split_output(text: str) -> tuple[str, str]:
    """機械切出 (首屏, 附錄)。⛔ 不讀內容，只認 `APPENDIX_HEADING` 那一行。"""
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.rstrip("\n") == APPENDIX_HEADING:
            return "".join(lines[:index]), "".join(lines[index:])
    raise ValueError(f"輸出裡找不到附錄邊界：{APPENDIX_HEADING}")
