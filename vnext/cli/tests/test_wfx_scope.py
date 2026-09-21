"""結構錨：CLI 的邊界靠程式碼結構釘住，不是靠散文判讀。

沿用舊 test_gh_scope.py 的 import-scope 形狀，加上 C6 的兩條斷言。
⛔ 不做禁用字串掃描、⛔ 不設行數門檻——那些撞 A3。
"""

import ast
import re
from pathlib import Path

from conftest import REPO_ROOT
from wfx.core.layers import CORE_CONCEPTS

WFX = REPO_ROOT / "vnext" / "cli" / "src" / "wfx"

# 模型 provider SDK 與 HTTP client：CLI ⛔ 不呼叫 AI、⛔ 不查額度、⛔ 不連任何 provider。
FORBIDDEN_ROOTS = {
    "anthropic", "openai", "google", "cohere", "mistralai", "ollama", "litellm",
    "requests", "httpx", "urllib", "urllib3", "http", "socket", "aiohttp",
}


def modules(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module


def sources(subdir=""):
    return sorted((WFX / subdir).rglob("*.py"))


def test_wfx_imports_no_http_or_model_provider_sdk():
    offenders = []
    for path in sources():
        for name in modules(path):
            if name.split(".")[0] in FORBIDDEN_ROOTS:
                offenders.append(f"{path.relative_to(WFX)}: {name}")
    assert offenders == []


def test_core_does_not_import_the_github_adapter_or_subprocess():
    offenders = []
    for path in sources("core"):
        for name in modules(path):
            root = name.split(".")[0]
            if name.startswith("wfx.gh") or root == "subprocess":
                offenders.append(f"{path.relative_to(WFX)}: {name}")
    assert offenders == []


def test_core_keeps_the_task_identifier_opaque():
    """核心⛔ 不理解任務識別的格式——不得出現 repo#issue 的解析。"""
    for path in sources("core"):
        text = path.read_text(encoding="utf-8")
        assert "split('#')" not in text and 'split("#")' not in text


def test_seven_core_concepts_match_the_rules_document():
    """七個核心概念的唯一居所是 core/github.md；程式碼只固定呈現順序。"""
    text = (REPO_ROOT / "vnext" / "rules" / "core" / "github.md").read_text(encoding="utf-8")
    block = text.split("## 2 · 七個核心概念", 1)[1].split("\n## ", 1)[0]
    rows = [
        m.group(1).strip()
        for m in re.finditer(r"^\|([^|]+)\|[^|]+\|[^|]*\|\s*$", block, re.M)
    ]
    named = {r for r in rows if r and r not in {"概念", "落地"} and set(r) - set("-: ")}
    assert named == set(CORE_CONCEPTS)
