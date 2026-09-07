"""消費 core/card-schema.md §1／§3／§4、core/enums.md「值域」、
core/state-machine.md §3、core/dispatch.md「模組段歸屬」與 wf-contract、
core/return.md 與 core/ruling.md 的 schema、modules/*/module.md §0、
core/naming.md §4／§5、core/handoff.md「每段首行」。
"""
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from .frontmatter import parse_frontmatter

LABELS = frozenset(("json schema", "json wf-enums", "json wf-state-machine",
                    "json wf-module-sections", "yaml wf-module"))


class BlockError(ValueError):
    def __init__(self, path: str, section: str, detail: str):
        self.path, self.section = path, section
        super().__init__(f"{path}#{section}: {detail}")


class MissingBlockError(BlockError):
    """找不到要求的區塊或閉合標記。"""


class BadJSONError(BlockError):
    """區塊內容無法解析為 JSON。"""


class DuplicateIDError(BlockError):
    """schema 索引已有同一 $id。"""


class UnknownLabelError(BlockError):
    """圍欄標籤不在本讀取器支援範圍。"""


class SkippedFence(BlockError):
    """非 CLI 圍欄略過診斷；不阻止讀取。"""


@dataclass(frozen=True)
class Source:
    path: str
    section: str
    name: str
    when: str
    last_confirmed: str


@dataclass(frozen=True)
class Block:
    label: str
    data: Any
    raw: str
    source: Source


@dataclass(frozen=True)
class Catalog:
    blocks: list[Block]
    schemas: dict[str, Block]
    diagnostics: list[ValueError] = field(default_factory=list)

    def by_label(self, label: str) -> list[Block]:
        """非 schema 區塊依標籤查找，不進 $id 命名空間。"""
        return [block for block in self.blocks if block.label == label]


def source_line(source: Source) -> str:
    return (f"[來源: {source.path}#{source.section} · {source.name}：{source.when}"
            f" · confirmed {source.last_confirmed}]")


def read_blocks(root: Path | str, relative: Path | str,
                *, diagnostics: list | None = None) -> list[Block]:
    """逐檔掃描；raw 是兩個圍欄行之間的逐字內容，包含末尾換行。

    刻意只記錄 ## 標題；沒有該層標題時 section 留空，不推測節名。
    沒有區塊的檔案回傳空清單；必需區塊由 require_blocks 明確查找。
    """
    path = Path(relative).as_posix()
    with (Path(root) / relative).open(encoding="utf-8", newline="") as handle:
        text = handle.read()
    diagnostics = diagnostics if diagnostics is not None else []
    metadata = parse_frontmatter(text, path, diagnostics=diagnostics)
    result = []
    section, label = "", None
    start, offset = 0, 0
    skipped = False
    for line in text.splitlines(keepends=True):
        marker = line.rstrip("\r\n")
        if skipped:
            if marker == "```":
                skipped = False
        elif label is not None:
            if marker == "```":
                raw = text[start:offset]
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError as error:
                    raise BadJSONError(path, section, str(error)) from error
                source = Source(path, section, metadata.name, metadata.when,
                                metadata.last_confirmed)
                result.append(Block(label, data, raw, source))
                label = None
        elif marker.startswith("## "):
            section = marker[3:]
        elif marker.startswith("```"):
            label = marker[3:]
            if label not in LABELS:
                if label.startswith(("json wf-", "yaml wf-")):
                    raise UnknownLabelError(path, section, f"未知標籤 {label!r}")
                diagnostics.append(SkippedFence(path, section, f"略過圍欄 {label!r}"))
                label, skipped = None, True
            start = offset + len(line)
        offset += len(line)
    if label is not None:
        raise MissingBlockError(path, section, f"{label} 缺閉合標記")
    return result


def require_blocks(root: Path | str, relative: Path | str, label: str,
                   *, section: str | None = None) -> list[Block]:
    path = Path(relative).as_posix()
    if label not in LABELS:
        raise UnknownLabelError(path, section or "", f"未知標籤 {label!r}")
    selected = [block for block in read_blocks(root, relative)
                if block.label == label and (section is None or block.source.section == section)]
    if not selected:
        raise MissingBlockError(path, section or "", f"缺區塊 {label}")
    return selected


def load_blocks(root: Path | str) -> Catalog:
    """每次從規則原件讀取，依 schema 的 $id 建索引；不驗 schema 或合成。"""
    root = Path(root)
    blocks, schemas, diagnostics = [], {}, []
    paths = sorted(root.glob("core/*.md")) + sorted(root.glob("modules/*/module.md"))
    for path in paths:
        for block in read_blocks(root, path.relative_to(root), diagnostics=diagnostics):
            blocks.append(block)
            if block.label != "json schema" or not isinstance(block.data, dict):
                continue
            identifier = block.data.get("$id")
            if identifier is None:
                continue  # 刻意不驗 schema 的必要鍵；此層只索引已宣告的 $id。
            if identifier in schemas:
                previous = schemas[identifier].source
                raise DuplicateIDError(block.source.path, block.source.section,
                                       f"重複 $id {identifier!r}；原件 {previous.path}#{previous.section}")
            schemas[identifier] = block
    return Catalog(blocks, schemas, diagnostics)
