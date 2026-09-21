"""第 1 層：框架規則樹的載入與機械切段。

⛔ 不判哪一段適用——core 六份一律全載，stages／roles 由旗標選定。
⛔ 不解析散文語意；切段只認 markdown 的 `## ` 行。
"""

from __future__ import annotations

import re
from pathlib import Path

from wfx.core.errors import LayerMissing

CORE_DIR = "core"
STAGES_DIR = "stages"
ROLES_DIR = "roles"


def default_rules_root() -> Path:
    """W1.6 的預設＝原始碼樹的 vnext/rules。

    W2.1 會把規則樹打包成 package data 並改由套件解析；`--rules-root` 覆寫在
    兩種情況下都生效。
    """
    # core → wfx → src → cli → vnext
    return Path(__file__).resolve().parents[4] / "rules"


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
