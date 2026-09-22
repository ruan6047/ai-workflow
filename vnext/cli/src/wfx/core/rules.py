"""第 1 層：框架規則樹的載入與機械切段。

⛔ 不判哪一段適用——core 六份一律全載，stages／roles 由旗標選定。
⛔ 不解析散文語意；切段只認 markdown 的 `## ` 行。
"""

from __future__ import annotations

from importlib import metadata, resources
import re
from pathlib import Path

from wfx.core.errors import LayerMissing

CORE_DIR = "core"
STAGES_DIR = "stages"
ROLES_DIR = "roles"

# distribution 名稱＝`vnext/cli/pyproject.toml` 的 `[project] name`；版本值的唯一居所也在那裡。
DISTRIBUTION = "ai-workflow-vnext"
RULES_DIR = "rules"

# 第 1 層規則樹實際被讀的那一份，只有兩種來源。
PACKAGE, OVERRIDE = "package", "override"


def default_rules_root() -> Path:
    """預設＝`wfx` 套件內的 package data（`wfx/rules`）。

    走 `importlib.resources` 而非相對本檔數層 parents：裝在 site-packages 時沒有
    `vnext/` 那幾層，原始碼樹直跑時兩者指到同一個目錄。`--rules-root` 覆寫在兩種情況下都生效。
    """
    return Path(resources.files("wfx").joinpath(RULES_DIR))


def package_version() -> str:
    """`ai-workflow-vnext` 的安裝版本；**⛔ 不建立第二個版本來源**。

    未安裝（例如以 PYTHONPATH 直跑原始碼樹）＝`unknown`，⛔ 不改由檔案或常數補一個值。
    """
    try:
        return metadata.version(DISTRIBUTION)
    except metadata.PackageNotFoundError:
        return "unknown"


def rules_provenance(rules_root: Path | None) -> tuple[str, str]:
    """(來源, 版本)：給了 `--rules-root` 就是 `override`，否則讀套件內的規則樹。

    ⛔ 不讀該路徑、⛔ 不判它合不合法——那是 `brief` 載入時才會 fail-loud 的事。
    """
    return (OVERRIDE if rules_root is not None else PACKAGE), package_version()


def read_doc(rules_root: Path, rel: str) -> str:
    path = rules_root / rel
    if not path.is_file():
        raise LayerMissing("framework", rel, f"找不到 {path}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise LayerMissing("framework", rel, "檔案為空")
    return text


def core_docs(rules_root: Path) -> list[tuple[str, str]]:
    directory = rules_root / CORE_DIR
    if not directory.is_dir():
        raise LayerMissing("framework", CORE_DIR, f"找不到 {directory}")
    rels = sorted(f"{CORE_DIR}/{p.name}" for p in directory.glob("*.md"))
    if not rels:
        raise LayerMissing("framework", CORE_DIR, "目錄下沒有規則文件")
    return [(rel, read_doc(rules_root, rel)) for rel in rels]


def stage_doc(rules_root: Path, stage: str) -> tuple[str, str]:
    rel = f"{STAGES_DIR}/{stage}.md"
    return rel, read_doc(rules_root, rel)


def role_doc(rules_root: Path, role: str) -> tuple[str, str]:
    rel = f"{ROLES_DIR}/{role}.md"
    return rel, read_doc(rules_root, rel)


def split_sections(text: str) -> list[tuple[str, str]]:
    """切成 (節名, 內文)。第一個 `## ` 之前的內容（frontmatter＋H1）＝前言。"""
    anchor = "前言"
    buf: list[str] = []
    out: list[tuple[str, str]] = []
    for line in text.splitlines():
        if line.startswith("## "):
            out.append((anchor, "\n".join(buf).strip("\n")))
            anchor = line[3:].strip()
            buf = []
        else:
            buf.append(line)
    out.append((anchor, "\n".join(buf).strip("\n")))
    return [(a, b) for a, b in out if b]


def headings(text: str) -> list[str]:
    return [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]


# `core/github.md` §1 的五章節清單＝規則樹的居所；⛔ 不在程式碼內建標題字面。
_ISSUE_SECTION_ROW = re.compile(r"^\d+\.\s+`##\s+(?P<title>[^`]+)`")


def issue_section_titles(rules_root: Path) -> tuple[str, ...]:
    """從 `core/github.md` 機械抽出 Issue body 的固定章節標題。

    ⛔ 不判內容、⛔ 不硬寫標題——抽不到就是規則樹的問題，往上丟 typed 失敗。
    """
    text = read_doc(rules_root, f"{CORE_DIR}/github.md")
    titles = tuple(
        m.group("title").strip()
        for m in (_ISSUE_SECTION_ROW.match(line.strip()) for line in text.splitlines())
        if m
    )
    if not titles:
        raise LayerMissing("framework", f"{CORE_DIR}/github.md", "抽不出 Issue body 的固定章節標題")
    return titles


def section_spans(text: str) -> list[tuple[str, int, int]]:
    """每個 `## ` 節的 (節名, 起始行號 1-based, 內文非空行數)。

    ⛔ 只認 `## ` 行、⛔ 不含第一個 `## ` 之前的前言（那段沒有節名可定位）。
    同名節重複出現時逐個回，去重交給呼叫端決定要第幾個。
    """
    out: list[tuple[str, int, int]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if line.startswith("## "):
            out.append((line[3:].strip(), number, 0))
        elif line.strip() and out:
            anchor, start, filled = out[-1]
            out[-1] = (anchor, start, filled + 1)
    return out


# 固定章節的三態；`core/github.md` §1 的「標題在且其下非空」只有這三個結果。
PRESENT, EMPTY, MISSING = "非空", "空", "缺章節"


def required_sections(titles, text: str) -> list[tuple[str, str, int | None, int]]:
    """固定章節的機械事實：每個標題回 (標題, 三態, 起始行號｜None, 非空行數)。

    這是**必要章節的唯一解析來源**——`facts` 與 `brief` 都走這裡，兩邊才不會對同一份 body
    給出互相矛盾的事實。只認 `## `（`# ` ⛔ 不是契約寫的那個層級），同名重複時只看**第一個**
    （後面的由呼叫端另行照列）。⛔ 不解析散文語意、⛔ 不判內容好壞。
    """
    first: dict[str, tuple[int, int]] = {}
    for anchor, start, filled in section_spans(text or ""):
        first.setdefault(anchor, (start, filled))
    out: list[tuple[str, str, int | None, int]] = []
    for title in titles:
        span = first.get(title)
        if span is None:
            out.append((title, MISSING, None, 0))
        else:
            out.append((title, PRESENT if span[1] else EMPTY, span[0], span[1]))
    return out
