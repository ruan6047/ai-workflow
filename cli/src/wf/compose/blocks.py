"""消費 core/card-schema.md §1／§3／§4／§5、core/enums.md「值域」、
core/state-machine.md §3、core/dispatch.md「模組段歸屬」與 wf-contract、
core/return.md 與 core/ruling.md 的 schema、modules/*/module.md §0、
core/naming.md §4／§5、core/handoff.md「每段首行」。
規則原件只經 `wf.context.RulesSource` 讀（`load_blocks` 收 RulesSource 或路徑；路徑＝自舉簡寫，
經 `rules_of` 包成檔案系統 adapter），⛔ 不從 project root 讀規則。
"""
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from wf.context import RulesSourceError, rules_of
from .frontmatter import parse_frontmatter

LABELS = frozenset(("json schema", "json wf-enums", "json wf-state-machine",
                    "json wf-module-sections", "yaml wf-module", "json wf-projection"))
KINDS = ("core", "module", "project", "card")  # core/handoff.md 每段首行的 <kind>（core/glossary.md「來源（四個）」）


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
    """來源＝{kind, path, section}（core/handoff.md 每段首行、core/verbs.md §3）：kind ∈ KINDS；path 相對該 kind
    的 root 可直接開啟——core／module 相對 rules root、project 相對 project root、card＝完整 Issue URL；
    ⛔ 不把 kind 串進 path。name／when／last_confirmed 取該檔 frontmatter；無 frontmatter（專案層、卡面）為 None。"""
    kind: str
    path: str
    section: str
    name: str | None = None
    when: str | None = None
    last_confirmed: str | None = None


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


def projection(catalog: Catalog) -> dict:
    """core/card-schema.md §5 的欄名、順序與每欄設定逐字取自區塊。"""
    block, = catalog.by_label("json wf-projection")
    return json.loads(block.raw)


def kind_of(relative: Path | str) -> str:
    """規則資產的 kind：`modules/` 下＝module，其餘（core／stages／roles）＝core。"""
    return "module" if Path(relative).as_posix().startswith("modules/") else "core"


def source_line(source: Source) -> str:
    """`[來源: <kind>:<path>#<節> · <name>：<when> · confirmed <日期>]`；節為空不補 `#`，無 frontmatter 只印前段。"""
    head = f"[來源: {source.kind}:{source.path}" + (f"#{source.section}" if source.section else "")
    if source.name is None:
        return head + "]"
    return head + f" · {source.name}：{source.when} · confirmed {source.last_confirmed}]"


def read_asset(source, relative: str) -> str | None:
    """source＝RulesSource（規則資產）或專案 root 路徑（`.wf/stages/<階段>.md`）；缺檔＝None。"""
    if isinstance(source, (str, Path)):
        path = Path(source) / relative
        return path.read_text(encoding="utf-8") if path.is_file() else None
    try:
        return source.read_text(relative)
    except RulesSourceError:
        return None


def note_scopes(module: dict) -> dict:
    """modules/*/module.md §0 `adds.notes` 的 {id, roles} → {id: roles 或 None}；roles 缺席＝全角色（None）。
    形狀的封閉驗證住 WF-011（CI 對帳 `.github/scripts/reachability.py`），此處⛔ 不拒收——
    非物件元素只當 id、roles 非陣列當缺席。"""
    entries = (item if isinstance(item, dict) else {"id": item}
               for item in module.get("adds", {}).get("notes", []))
    return {entry.get("id"): entry["roles"] if isinstance(entry.get("roles"), list) else None
            for entry in entries}


def section_lines(text: str, heading: str | None) -> tuple[str, list[str]]:
    """只取該 `## <heading>` 節的 (節名, 行)；heading 為 None 時取全檔、節名空。散文由呼叫端過濾。"""
    if heading is None:
        return "", text.splitlines()
    title, lines, keep = "", [], False
    for line in text.splitlines():
        if line.startswith("## "):
            keep = line.startswith("## " + heading)
            title = line[3:] if keep else title
        elif keep:
            lines.append(line)
    return title, lines


def read_blocks(root: Path | str, relative: Path | str,
                *, diagnostics: list | None = None, text: str | None = None) -> list[Block]:
    """逐檔掃描；raw 是兩個圍欄行之間的逐字內容，包含末尾換行。text 給定時不開檔（RulesSource 供文）。

    刻意只記錄 ## 標題；沒有該層標題時 section 留空，不推測節名。
    沒有區塊的檔案回傳空清單；必需區塊由 require_blocks 明確查找。
    """
    path = Path(relative).as_posix()
    if text is None:
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
                source = Source(kind_of(path), path, section, metadata.name, metadata.when,
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


def load_blocks(root) -> Catalog:
    """每次從規則原件讀取，依 schema 的 $id 建索引；不驗 schema 或合成。root＝RulesSource 或路徑。"""
    source = rules_of(root)
    blocks, schemas, diagnostics = [], {}, []
    paths = [*source.iter_assets("core/*.md"), *source.iter_assets("modules/*/module.md")]
    for path in paths:
        for block in read_blocks(source.identity, path, diagnostics=diagnostics, text=source.read_text(path)):
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
