"""第 1 層：框架規則樹的載入與機械切段。

⛔ 不判哪一段適用——core 六份一律全載，stages／roles 由旗標選定。
⛔ 不解析散文語意；切段只認 markdown 的 `## ` 行。
"""

from __future__ import annotations

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
