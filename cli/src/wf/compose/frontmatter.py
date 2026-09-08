"""消費 core/naming.md §5 的 frontmatter 與 core/handoff.md「每段首行」。"""
from dataclasses import dataclass
from pathlib import Path
import re

FIELDS = ("name", "when", "non_scope", "last_confirmed")
HEADER = re.compile(r"\A---\r?\n(.*?)^---[ \t]*(?:\r?\n|\Z)", re.M | re.S)


class MissingFrontmatterError(ValueError):
    def __init__(self, path: str, section: str, missing: tuple[str, ...]):
        self.path, self.section, self.missing = path, section, missing
        super().__init__(f"{path}#{section}: frontmatter 缺欄 {', '.join(missing)}")


@dataclass(frozen=True)
class Frontmatter:
    name: str
    when: str
    non_scope: str
    last_confirmed: str


def parse_frontmatter(text: str, path: str, section: str = "",
                      *, diagnostics: list | None = None) -> Frontmatter:
    """讀現有規則檔的單行文字欄位；保留值，不解讀日期或散文。"""
    match = HEADER.match(text)
    values = {}
    for line in match.group(1).splitlines() if match else ():
        key, separator, value = line.partition(":")
        if separator and key in FIELDS:
            values[key] = value.strip()
    missing = tuple(key for key in FIELDS if key not in values)
    if missing:
        error = MissingFrontmatterError(path, section, missing)
        if diagnostics is None:
            raise error
        diagnostics.append(error)
    return Frontmatter(**{key: values.get(key, "") for key in FIELDS})


def read_frontmatter(path: Path | str) -> Frontmatter:
    path = Path(path)
    return parse_frontmatter(path.read_text(encoding="utf-8"), str(path))
