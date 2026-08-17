#!/usr/bin/env python3
"""契約↔工具對帳器（WF-REVIEW-INVALID-TRACE1）。

## 這支腳本回答的問題

契約文件（canonical ``AI_WORKFLOW.md``、``templates/*.md``、``docs/ROADMAP.md``）宣告了
一批**事件型別／交付狀態／卡面欄位**；寫入通道（``cli/`` 的 ``wfcli``）只實作了一部分。
兩者從來沒有對過帳，於是缺口是**撞出來的，不是找出來的**——2026-08-16 一天內踩到五個，
全部靠實際操作失敗才發現。

本腳本把「有幾個洞」變成一個**可重跑的機械輸出**。

## 三條設計紅線（違反其一，這支腳本就退化成它要消滅的那個東西）

1. **契約側的 universe 必須由掃描文件導出，不得由人登記。**
   本檔**沒有**任何「已知事件型別清單」常數。所有符號都用**語法規則**從文件正文抽出
   （見 ``extract_*`` 三個函式）。規則寧可**過度抽取**也不欠抽：多抽一個符號的代價是
   表上多一列，漏抽一個的代價是那個洞繼續看不見。

2. **``grep`` 會騙你，所以工具側判定走 AST 而不是字串搜尋。**
   ``review-invalid`` 這個字串**確實出現在** ``review_cmd.py``——出現在一個 ``print()``
   的引數裡。任何「grep 得到就算有實作」的判定都會把它判成已實作，那正是本卡要抓的
   反面。本檔用 ``ast`` ＋ ``tokenize`` 把每一次字面出現分類成 comment／docstring／
   診斷輸出／散文引述／讀取／詞彙表／寫入，**只有真正流進遠端寫入呼叫的才算 writer**。

3. **漏掃的後果必須是可見失敗，不是靜默通過。**
   ``--check`` 把機械導出的缺口集合與 ``docs/CONTRACT_TOOL_RECONCILE.md`` 登記的處置
   逐項比對，**三個方向都會紅**：出現未登記的缺口、登記了已不存在的缺口、同一符號的
   判定變了。所以那份處置表**不能靠刪掉一列讓檢查變綠**。

## 什麼結果會讓每個判定不成立（反證條件）

- **universe 由文件導出**：在任一契約文件加一個新的 kebab 反引號符號後重跑，它沒有
  出現在輸出裡 → 判定不成立。（測試以臨時檔實測，見 ``test_contract_tool_reconcile.py``。）
- **writer 判定**：把一個符號從 ``print()`` 改成流進 ``project.set_item_body``，它仍被
  判成 mention-only → 判定不成立；反向（改回 print 仍判成 writer）亦然。
- **amend 可改性**：在 ``card.py`` 新增一個 ``amend_<x>`` 函式並讓 ``amend_cmd`` import
  它，對應欄位沒有從「改不動」翻成「可改」→ 判定不成立。
- **``--check``**：在完全不動碼與文件的情況下重跑兩次卻一次綠一次紅（例如把日期納入
  比對）→ 檢查不成立。**本檔的 ``--check`` 不讀時鐘。**

## 已知限制（誠實列出，不假裝機械判定是全知的）

- 呼叫圖以「模組.函式」為節點，跨模組呼叫先查本模組定義、再查 import 來源，都查不到
  才退回同名全集。最後那條退路會**高估**可達性，方向是把缺口藏起來——因此本腳本報出
  的缺口是**下界**，不是上界。
- 「哪些 ``gh`` 子命令算寫入」是本檔唯一的外部種子（``MUTATING_GH_SUBCOMMANDS``）。它是
  ``gh`` CLI 的通用語彙、不是本 repo 的清單，且擴充它只會讓更多東西被判成 writer
  （同樣偏寬鬆）。GhRunner 的方法名則從 ``gh.py`` 的 AST 導出，不寫死。
- **writer 判定量的是「這個符號進不進得了狀態面」，不是「有沒有一個該型別的事件」。**
  一則被寫出去的留言若在散文裡提到某事件名，散文判定（見 ``_is_prose_context``）會把它
  降級為 mention；但若某符號以結構化形狀寫進留言正文（例如 ``- event: xxx``），它會被
  判成 writer——那是「狀態面上出現得了這個字」，語意上是不是一個合格事件仍須人讀。
- 過度抽取是刻意的：``data-migration``（``db_scope`` 值）、``spec-narrowed``
  （``defer_cause`` 值）這類非事件符號也會進表。它們多半有 reader，因此不會被判成缺口；
  真正沒有實作的才會浮出來。

用法：

    python3 scripts/contract_tool_reconcile.py                # Markdown 對帳表
    python3 scripts/contract_tool_reconcile.py --gaps-only    # 只列缺口
    python3 scripts/contract_tool_reconcile.py --format json  # 機器可讀
    python3 scripts/contract_tool_reconcile.py --check        # 與登記處置對帳，不符即非零退出
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import re
import sys
import tokenize
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# ==========================================================================
# 0. 射程：用 glob，不列檔名
# ==========================================================================
#
# templates/ 新增一份範本時它自動進射程；寫死檔名就會靜默漏掉。

CANONICAL_DOC = "AI_WORKFLOW.md"
TEMPLATE_GLOB = "templates/*.md"
ROADMAP_DOC = "docs/ROADMAP.md"
CARD_TEMPLATE_GLOB = "templates/*card*.md"
TOOL_ROOT = "cli/src/wf_cli"


def contract_docs(root: Path) -> list[Path]:
    paths: list[Path] = []
    canonical = root / CANONICAL_DOC
    if canonical.exists():
        paths.append(canonical)
    paths.extend(sorted(root.glob(TEMPLATE_GLOB)))
    roadmap = root / ROADMAP_DOC
    if roadmap.exists():
        paths.append(roadmap)
    out: list[Path] = []
    for p in paths:
        if p not in out:
            out.append(p)
    return out


def card_templates(root: Path) -> list[Path]:
    return sorted(root.glob(CARD_TEMPLATE_GLOB))


def tool_sources(root: Path) -> list[Path]:
    return sorted((root / TOOL_ROOT).rglob("*.py"))


def _module_path(root: Path, stem: str) -> Path | None:
    for p in tool_sources(root):
        if p.stem == stem:
            return p
    return None


# ==========================================================================
# 1. 契約側 universe：由掃描文件導出
# ==========================================================================

# 事件型別候選：反引號包住的 kebab-case token。
#
# 為什麼是這個形狀：canonical §4.1 的 lifecycle event envelope 有 ``type`` 欄，而文件裡
# 每一個被當成事件名的東西都寫成 `preflight-failed`／`review-invalid`／
# `escalation-epoch-change` 這種形狀。用**詞法**當判準（而不是語意），是因為語意判準需要
# 一份「哪些是事件」的人維護清單——那正是本卡要消滅的東西。
_KEBAB_IN_BACKTICKS = re.compile(r"`([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`")

# 交付狀態候選：emoji ＋ 緊接的非空白 token。emoji 以 Unicode 區段界定，不列舉具體
# emoji——列舉就又成了人維護清單。
_EMOJI_CLASS = (
    "←-⇿"  # 箭頭（↩退回）
    "⌀-⏿"  # 雜項技術符號（⏸⏳）
    "☀-➿"  # 雜項符號與 Dingbats（✅）
    "\U0001f300-\U0001faff"  # 各式 emoji 區段（🔨🚧🔍📦🏁🚨🛑💡📥）
)
_STATUS_TOKEN = re.compile(rf"([{_EMOJI_CLASS}]️?[0-9A-Za-z㐀-䶿一-鿿]+)")

# 卡面欄位候選：卡面標頭條列的 ``- <名稱>：``／全形空白分隔的 ``　<名稱>：``，以及
# ``## <名稱>`` 標準章節名。兩者都是範本的**結構**，不是內容。
#
# ⚠️ 欄位名**容許內含空白**：``spec 基線`` 與 ``Merge SHA`` 都是契約明列的欄位，而第一版
# 的字元類把 ``\s`` 排掉，於是這兩個欄位靜默不進表——那正是本卡要消滅的「漏掃」。容許空白
# 會多抓一些標頭條列的雜訊，方向是對的：多一列看得見，少一列看不見。
_CARD_FIELD_BULLET = re.compile(r"^-\s*([^：<>*`\[\]\n]{1,20}?)\s*：")
_CARD_FIELD_INLINE = re.compile(r"　\s*([^：<>*`\[\]\n]{1,20}?)\s*：")
_CARD_SECTION = re.compile(r"^##\s+(.+?)\s*$")
_FIRST_SECTION = re.compile(r"^##\s", re.MULTILINE)

KIND_EVENT = "event"
KIND_STATUS = "delivery_status"
KIND_FIELD = "card_field"


@dataclass(frozen=True)
class DocHit:
    path: str
    line: int


@dataclass
class ContractSymbol:
    kind: str
    name: str
    hits: list[DocHit] = field(default_factory=list)


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _add(bucket: dict[tuple[str, str], ContractSymbol], kind: str, name: str, hit: DocHit) -> None:
    sym = bucket.setdefault((kind, name), ContractSymbol(kind=kind, name=name))
    if hit not in sym.hits:
        sym.hits.append(hit)


def extract_events(docs: list[Path], root: Path) -> dict[tuple[str, str], ContractSymbol]:
    out: dict[tuple[str, str], ContractSymbol] = {}
    for path in docs:
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(root))
        for m in _KEBAB_IN_BACKTICKS.finditer(text):
            _add(out, KIND_EVENT, m.group(1), DocHit(rel, _line_of(text, m.start(1))))
    return out


def extract_delivery_statuses(docs: list[Path], root: Path) -> dict[tuple[str, str], ContractSymbol]:
    out: dict[tuple[str, str], ContractSymbol] = {}
    for path in docs:
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(root))
        for m in _STATUS_TOKEN.finditer(text):
            _add(out, KIND_STATUS, m.group(1), DocHit(rel, _line_of(text, m.start(1))))
    return out


def extract_card_fields(templates: list[Path], root: Path) -> dict[tuple[str, str], ContractSymbol]:
    out: dict[tuple[str, str], ContractSymbol] = {}
    for path in templates:
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(root))
        first = _FIRST_SECTION.search(text)
        header = text[: first.start()] if first else text
        for lineno, line in enumerate(header.splitlines(), start=1):
            m = _CARD_FIELD_BULLET.match(line)
            if m:
                _add(out, KIND_FIELD, m.group(1), DocHit(rel, lineno))
            for inline in _CARD_FIELD_INLINE.finditer(line):
                _add(out, KIND_FIELD, inline.group(1), DocHit(rel, lineno))
        for lineno, line in enumerate(text.splitlines(), start=1):
            m = _CARD_SECTION.match(line)
            if m:
                _add(out, KIND_FIELD, m.group(1), DocHit(rel, lineno))
    return out


def build_universe(root: Path) -> list[ContractSymbol]:
    docs = contract_docs(root)
    templates = card_templates(root)
    merged: dict[tuple[str, str], ContractSymbol] = {}
    for chunk in (
        extract_events(docs, root),
        extract_delivery_statuses(docs, root),
        extract_card_fields(templates, root),
    ):
        for key, sym in chunk.items():
            if key in merged:
                for hit in sym.hits:
                    if hit not in merged[key].hits:
                        merged[key].hits.append(hit)
            else:
                merged[key] = sym
    return sorted(merged.values(), key=lambda s: (s.kind, s.name))


# ==========================================================================
# 2. 工具側：AST 判定
# ==========================================================================

MUTATING_GH_SUBCOMMANDS = frozenset(
    {
        "edit", "comment", "create", "close", "reopen", "delete",
        "item-edit", "item-create", "item-add", "item-delete", "field-create",
    }
)

ROLE_WRITE = "write"
ROLE_READ = "read"
ROLE_VOCAB = "vocabulary"
ROLE_PROSE = "prose"
ROLE_DIAGNOSTIC = "diagnostic"
ROLE_DOCSTRING = "docstring"
ROLE_COMMENT = "comment"
ROLE_OTHER = "other"

MENTION_ROLES = (ROLE_COMMENT, ROLE_DOCSTRING, ROLE_DIAGNOSTIC, ROLE_PROSE, ROLE_OTHER)
NON_WRITABLE_ROLES = (ROLE_COMMENT, ROLE_DOCSTRING, ROLE_DIAGNOSTIC, ROLE_PROSE)

_ROLE_RANK = {
    ROLE_COMMENT: 0, ROLE_DOCSTRING: 1, ROLE_PROSE: 2, ROLE_DIAGNOSTIC: 3,
    ROLE_OTHER: 4, ROLE_VOCAB: 5, ROLE_READ: 6, ROLE_WRITE: 7,
}

DIAGNOSTIC_CALLS = frozenset({"print", "warn", "warning", "debug"})
READ_CALLS = frozenset(
    {"compile", "match", "search", "fullmatch", "startswith", "endswith",
     "find", "index", "count", "split", "rsplit", "get"}
)


@dataclass(frozen=True)
class Occurrence:
    path: str
    line: int
    role: str
    symbol: str


@dataclass
class ModuleIndex:
    rel: str
    stem: str
    tree: ast.Module
    comments: list[tuple[int, str]]


def _read_comments(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                out.append((tok.start[0], tok.string))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return out


def load_modules(root: Path) -> list[ModuleIndex]:
    mods: list[ModuleIndex] = []
    for path in tool_sources(root):
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        mods.append(
            ModuleIndex(
                rel=str(path.relative_to(root)),
                stem=path.stem,
                tree=tree,
                comments=_read_comments(text),
            )
        )
    return mods


def _iter_functions(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _string_constants(node: ast.AST) -> set[str]:
    return {
        c.value
        for c in ast.walk(node)
        if isinstance(c, ast.Constant) and isinstance(c.value, str)
    }


def gh_runner_methods(root: Path) -> set[str]:
    """從 ``gh.py`` 的 AST 導出 GhRunner 的公開方法名，不寫死。"""
    gh_path = root / TOOL_ROOT / "gh.py"
    if not gh_path.exists():
        return set()
    tree = ast.parse(gh_path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and not item.name.startswith("__"):
                    names.add(item.name)
    return names


# ---------------------------------------------------------------- 呼叫圖


@dataclass
class CallGraph:
    """節點是「模組.函式」，不是裸函式名。

    裸名版本會把 ``assign_cmd.run`` 與 ``amend_cmd.run`` 混成同一個節點，於是
    「amend 有沒有跑 find_conflicts」這個問題永遠答「有」——本卡的已知缺口 #4 正是
    被這種混淆藏起來的。
    """

    edges: dict[str, set[str]]
    node_of: dict[str, ast.AST]
    module_of: dict[str, str]


def build_call_graph(modules: list[ModuleIndex]) -> CallGraph:
    defined: dict[str, set[str]] = {}
    node_of: dict[str, ast.AST] = {}
    module_of: dict[str, str] = {}
    imports: dict[str, dict[str, str]] = {}

    for mod in modules:
        names = defined.setdefault(mod.stem, set())
        for fn in _iter_functions(mod.tree):
            names.add(fn.name)
            key = f"{mod.stem}.{fn.name}"
            node_of[key] = fn
            module_of[key] = mod.stem
        imp = imports.setdefault(mod.stem, {})
        for node in ast.walk(mod.tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                src = node.module.split(".")[-1]
                for alias in node.names:
                    imp[alias.asname or alias.name] = src

    by_name: dict[str, set[str]] = {}
    for key in node_of:
        by_name.setdefault(key.split(".", 1)[1], set()).add(key)

    def resolve(module: str, node: ast.Call) -> set[str]:
        """把一個呼叫解析成 qualified key 集合。**解析不到就不連邊。**

        ⚠️ 先前這裡有一條「同名全集」退路，後果是 ``gh.execute`` 裡的
        ``subprocess.run(...)`` 連到了 ``assign_cmd.run``，於是
        ``amend_cmd → … → assign_cmd.run → find_conflicts`` 憑空可達——本卡的已知缺口
        #4 剛好就被這條假邊藏起來。解析不到時**不連邊**：少一條邊只會讓工具少判一些
        「有實作」，方向是多報缺口，不是少報。
        """
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            # ``card.append_log_line(...)`` 這種模組屬性呼叫。
            holder = imports.get(module, {}).get(func.value.id, func.value.id)
            if f"{holder}.{func.attr}" in node_of:
                return {f"{holder}.{func.attr}"}
        name = _call_name(node)
        if not name:
            return set()
        if name in defined.get(module, set()):
            return {f"{module}.{name}"}
        src = imports.get(module, {}).get(name)
        if src and f"{src}.{name}" in node_of:
            return {f"{src}.{name}"}
        return set()

    edges: dict[str, set[str]] = {}
    for mod in modules:
        for fn in _iter_functions(mod.tree):
            key = f"{mod.stem}.{fn.name}"
            out = edges.setdefault(key, set())
            for node in ast.walk(fn):
                if isinstance(node, ast.Call):
                    out |= resolve(mod.stem, node)
    assert by_name is not None  # 保留索引供除錯；解析路徑刻意不使用它
    return CallGraph(edges=edges, node_of=node_of, module_of=module_of)


def remote_mutating_functions(
    modules: list[ModuleIndex], graph: CallGraph, gh_methods: set[str]
) -> set[str]:
    """遠端寫入函式（RMF）：種子（自己跑寫入型 gh 子命令）＋ 呼叫者傳遞閉包。"""
    seeds: set[str] = set()
    for mod in modules:
        for fn in _iter_functions(mod.tree):
            for node in ast.walk(fn):
                if not isinstance(node, ast.Call):
                    continue
                if _call_name(node) not in gh_methods:
                    continue
                if _string_constants(node) & MUTATING_GH_SUBCOMMANDS:
                    seeds.add(f"{mod.stem}.{fn.name}")
    rmf = set(seeds)
    changed = True
    while changed:
        changed = False
        for caller, callees in graph.edges.items():
            if caller not in rmf and callees & rmf:
                rmf.add(caller)
                changed = True
    return rmf


def state_plane_connected(graph: CallGraph, rmf: set[str]) -> set[str]:
    """RMF ∪ 被 RMF（遞移）呼叫到的函式。

    ``card.render_issue_body`` 自己不碰 gh，但 ``open_cmd.run``（RMF）呼叫它並把結果
    交給 ``create_repo_issue``。它產出的字面**確實會落到狀態面**，所以必須算進來。
    """
    connected = set(rmf)
    frontier = set(rmf)
    while frontier:
        nxt: set[str] = set()
        for key in frontier:
            nxt |= graph.edges.get(key, set())
        nxt -= connected
        connected |= nxt
        frontier = nxt
    return connected


# ------------------------------------------------------- 字面出現的角色分類

_WORDISH = re.compile(r"[0-9A-Za-z_-]")


def _contains_symbol(haystack: str, symbol: str) -> bool:
    """字面比對，對 ASCII 邊界加詞界。

    ⚠️ 這條詞界是必要的：``deploy_state_cmd.py`` 寫出 ``deployment-status-change``，
    沒有詞界的話 ``status-change`` 會被誤判成「有 writer」，而 ``status-change``
    沒有專責動詞正是本卡的已知缺口之一。
    """
    idx = haystack.find(symbol)
    while idx != -1:
        before_ok = idx == 0 or not _WORDISH.match(haystack[idx - 1])
        end = idx + len(symbol)
        after_ok = end >= len(haystack) or not _WORDISH.match(haystack[end])
        if not _WORDISH.match(symbol[0]):
            before_ok = True
        if not _WORDISH.match(symbol[-1]):
            after_ok = True
        if before_ok and after_ok:
            return True
        idx = haystack.find(symbol, idx + 1)
    return False


def _is_cjk_letter(ch: str) -> bool:
    """CJK／全形**文字**（不含全形標點）。用 Unicode 屬性判，不列舉字元。

    ⚠️ 必須排掉標點：卡面欄位的分隔符正是全形冒號 ``：``（category ``Po``、寬度 ``F``）。
    只看寬度的話，``"- 需求："`` 會被判成散文，於是**每一個卡面欄位都失去 writer**——
    第一版就是這樣把 ``需求`` 判成 mention-only 卻碰巧「看起來對」。
    """
    return unicodedata.east_asian_width(ch) in ("W", "F") and unicodedata.category(ch)[0] in "LN"


def _is_prose_context(value: str, symbol: str) -> bool:
    """符號是不是被包在**散文**裡（而不是結構化位置）。

    判準：符號左右最近的非空白字元若是 CJK／全形字或反引號，即視為散文引述。
    ``- event: deployment-status-change\\n`` 左右是 ``:`` 與換行 → 結構化；
    ``依 §5 的 review-marker-clearance 解除`` 左右是中文 → 散文。

    為什麼需要它：文件式的長字串（錯誤訊息、留言正文的說明段）幾乎必然提到契約名詞，
    若一律當成 writer，缺口會被自己的說明文字蓋掉。
    """
    idx = value.find(symbol)
    while idx != -1:
        left = value[:idx].rstrip()
        right = value[idx + len(symbol) :].lstrip()
        left_ch = left[-1] if left else ""
        right_ch = right[0] if right else ""
        prose = False
        for ch in (left_ch, right_ch):
            if ch and (_is_cjk_letter(ch) or ch == "`"):
                prose = True
        if not prose:
            return False  # 至少有一處是結構化位置
        idx = value.find(symbol, idx + 1)
    return True


def _docstring_ids(tree: ast.Module) -> set[int]:
    ids: set[int] = set()
    containers: list[ast.AST] = [tree]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            containers.append(node)
    for c in containers:
        body = getattr(c, "body", [])
        if body and isinstance(body[0], ast.Expr):
            val = body[0].value
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                ids.add(id(val))
    return ids


def _syntactic_role(node: ast.Constant, parents: list[ast.AST], docstrings: set[int]) -> str:
    if id(node) in docstrings:
        return ROLE_DOCSTRING
    for p in reversed(parents):
        if isinstance(p, ast.Call):
            name = _call_name(p)
            if name in DIAGNOSTIC_CALLS:
                return ROLE_DIAGNOSTIC
            if name in READ_CALLS:
                return ROLE_READ
            return ROLE_OTHER
        if isinstance(p, ast.Compare):
            return ROLE_READ
        if isinstance(p, ast.Subscript):
            return ROLE_READ
        if isinstance(p, (ast.Dict, ast.Set, ast.Tuple, ast.List)):
            return ROLE_VOCAB
        if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module, ast.ClassDef)):
            break
    return ROLE_OTHER


def classify_module(
    mod: ModuleIndex, symbols: list[str], connected: set[str]
) -> list[Occurrence]:
    docstrings = _docstring_ids(mod.tree)
    out: list[Occurrence] = []

    for lineno, comment in mod.comments:
        for sym in symbols:
            if _contains_symbol(comment, sym):
                out.append(Occurrence(mod.rel, lineno, ROLE_COMMENT, sym))

    # 每個函式節點 → 它所屬的 qualified key（用來判斷有沒有連到狀態面）。
    owner: dict[int, str] = {}
    for fn in _iter_functions(mod.tree):
        for node in ast.walk(fn):
            owner.setdefault(id(node), f"{mod.stem}.{fn.name}")

    def visit(node: ast.AST, parents: list[ast.AST]) -> None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            hits = [s for s in symbols if _contains_symbol(node.value, s)]
            if hits:
                base = _syntactic_role(node, parents, docstrings)
                key = owner.get(id(node))
                for sym in hits:
                    if base in (ROLE_COMMENT, ROLE_DOCSTRING, ROLE_DIAGNOSTIC):
                        role = base  # 註解／docstring／印給人看的，都不是狀態面
                    elif _is_prose_context(node.value, sym):
                        role = ROLE_PROSE  # 被包在散文裡的引述，不是結構化位置
                    elif base in (ROLE_READ, ROLE_VOCAB):
                        role = base  # 比對／封閉列舉：讀取側
                    elif key is not None and key in connected:
                        role = ROLE_WRITE  # 在連到狀態面的函式裡，這個字面進得了狀態面
                    else:
                        role = ROLE_OTHER
                    out.append(Occurrence(mod.rel, getattr(node, "lineno", 0), role, sym))
        for child in ast.iter_child_nodes(node):
            visit(child, parents + [node])

    visit(mod.tree, [])
    return out


# ==========================================================================
# 3. 卡面欄位第二軸：open 寫得到 vs amend 改得動
# ==========================================================================

_CARD_RENDERERS = ("render_issue_body", "render_spec_markdown", "format_routing_line")


def _labels_in(value: str) -> set[str]:
    """對任意字串套與契約側**同一條**卡面欄位規則。兩邊同規則才對得上帳。"""
    labels: set[str] = set()
    for line in value.splitlines():
        stripped = line.strip()
        m = _CARD_FIELD_BULLET.match(stripped)
        if m:
            labels.add(m.group(1))
        # ⚠️ 行內欄位要在**未 strip** 的原行上找：分隔符是全形空白 U+3000，而
        # ``str.strip()`` 會把它當空白吃掉，於是 ``　spec 基線：`` 永遠匹配不到，
        # 該欄位就被判成「open 沒有渲染」——那是假的。
        for inline in _CARD_FIELD_INLINE.finditer(line):
            labels.add(inline.group(1))
        sec = _CARD_SECTION.match(stripped)
        if sec:
            labels.add(sec.group(1))
    return labels


def module_constant_labels(tree: ast.Module) -> dict[str, set[str]]:
    """模組層級常數名 → 其字面裡的卡面欄位標籤。

    ``## 資源宣告`` 這個標題在 ``resources.py`` 是常數 ``_SECTION_HEADING``，函式體裡
    只有這個名字、沒有字面；不解常數就會漏掉它。正規表示式錨點（``^- 需求：…``）也
    在這裡一併拆開。
    """
    out: dict[str, set[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        labels: set[str] = set()
        for c in _string_constants(node.value):
            labels |= _labels_in(c)
            labels |= _labels_in(c.replace("^", "").replace("\\s*", ""))
        if labels:
            out[target.id] = labels
    return out


def open_written_fields(root: Path, graph: CallGraph | None = None) -> set[str]:
    """開卡時實際渲染出來的卡面欄位。

    起點是 ``card.py`` 的三個渲染樣板，並沿呼叫圖往下收——``## 資源宣告`` 這個標題不在
    ``card.py`` 的字面裡，它由 ``resources.render_block`` 產出；只掃起點會漏掉它。
    """
    path = root / TOOL_ROOT / "card.py"
    if not path.exists():
        return set()
    out: set[str] = set()
    seeds = {f"card.{name}" for name in _CARD_RENDERERS}
    reach = set(seeds)
    if graph is not None:
        frontier = set(seeds)
        while frontier:
            nxt: set[str] = set()
            for k in frontier:
                nxt |= graph.edges.get(k, set())
            nxt -= reach
            reach |= nxt
            frontier = nxt
        const_by_module: dict[str, dict[str, set[str]]] = {}
        for stem in {k.split(".", 1)[0] for k in reach}:
            src = _module_path(root, stem)
            if src is not None:
                const_by_module[stem] = module_constant_labels(
                    ast.parse(src.read_text(encoding="utf-8"))
                )
        for key in reach:
            node = graph.node_of.get(key)
            if node is None:
                continue
            for c in _string_constants(node):
                out |= _labels_in(c)
            consts = const_by_module.get(key.split(".", 1)[0], {})
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name) and sub.id in consts:
                    out |= consts[sub.id]
        return out

    tree = ast.parse(path.read_text(encoding="utf-8"))
    for fn in _iter_functions(tree):
        if fn.name in _CARD_RENDERERS:
            for c in _string_constants(fn):
                out |= _labels_in(c)
    return out


def amendable_fields(root: Path) -> set[str]:
    """開卡後改得動的卡面欄位——**由 AST 導出，不是人登記**。

    導法：``amend_cmd.py`` import 進來的 ``card.amend_*`` 函式，各自引用了哪些模組層級
    的錨點常數（``_CORE_PAIN_HEADING``、``_SPEC_BASELINE_RE``…），再對那些常數的字面套
    與契約側同一條欄位規則。

    這條規則會自動答對已知缺口 #5：``_REQUESTED_BY_RE``（``- 需求：…　規劃：…``）確實
    存在於 ``card.py``，但只被 ``parse_requested_by``（**讀取器**）引用，沒有任何
    ``amend_*`` 碰它 → 「需求」不在可改集合裡。
    """
    card_path = root / TOOL_ROOT / "card.py"
    amend_path = root / TOOL_ROOT / "commands" / "amend_cmd.py"
    if not card_path.exists() or not amend_path.exists():
        return set()

    card_tree = ast.parse(card_path.read_text(encoding="utf-8"))
    amend_tree = ast.parse(amend_path.read_text(encoding="utf-8"))

    # amend_cmd 從 card 匯入了哪些 amend_* 函式。
    imported: set[str] = set()
    for node in ast.walk(amend_tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("card"):
            for alias in node.names:
                if alias.name.startswith("amend_"):
                    imported.add(alias.name)

    const_labels = module_constant_labels(card_tree)

    out: set[str] = set()
    for fn in _iter_functions(card_tree):
        if fn.name not in imported:
            continue
        for node in ast.walk(fn):
            if isinstance(node, ast.Name) and node.id in const_labels:
                out |= const_labels[node.id]
    return out


def amend_read_fields(root: Path) -> set[str]:
    """``amend_cmd.py`` 讀哪些卡面欄位當判準（用來抓「讀得到卻改不動」）。"""
    amend_path = root / TOOL_ROOT / "commands" / "amend_cmd.py"
    card_path = root / TOOL_ROOT / "card.py"
    if not amend_path.exists() or not card_path.exists():
        return set()
    amend_tree = ast.parse(amend_path.read_text(encoding="utf-8"))
    card_tree = ast.parse(card_path.read_text(encoding="utf-8"))

    imported: set[str] = set()
    for node in ast.walk(amend_tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("card"):
            for alias in node.names:
                imported.add(alias.name)

    const_labels = module_constant_labels(card_tree)

    out: set[str] = set()
    for fn in _iter_functions(card_tree):
        if fn.name not in imported or fn.name.startswith("amend_"):
            continue
        for node in ast.walk(fn):
            if isinstance(node, ast.Name) and node.id in const_labels:
                out |= const_labels[node.id]
    return out


def cli_verbs(root: Path) -> set[str]:
    """從各 ``commands/*_cmd.py`` 的 ``subparsers.add_parser("<verb>")`` 導出動詞集合。"""
    out: set[str] = set()
    for path in (root / TOOL_ROOT / "commands").glob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _call_name(node) == "add_parser" and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    out.add(first.value)
    return out


def related_verbs(symbol: str, verbs: set[str]) -> list[str]:
    """事件名與 CLI 動詞的 token 交集。

    為什麼需要它：``escalation-checkpoint`` 在符號層是 mention-only（``wfcli checkpoint``
    寫出的留言標題是 ``## Escalation checkpoint：…``，從不吐出契約那串字面），但
    **動詞是存在的**。若不區分，這張表會把「連動詞都沒有」（``preflight-failed``）與
    「動詞有、只是沒吐出契約名」（``escalation-checkpoint``）混為一談——那是過度宣稱。
    """
    tokens = set(symbol.split("-"))
    return sorted(v for v in verbs if v in tokens)


def project_field_options(root: Path) -> dict[str, set[str]]:
    """從 ``project.FIELD_SPECS`` 的 AST 導出各 SINGLE_SELECT 欄位的選項集合。"""
    path = root / TOOL_ROOT / "project.py"
    if not path.exists():
        return {}
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: dict[str, set[str]] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        target = node.targets[0] if isinstance(node, ast.Assign) else node.target
        if not isinstance(target, ast.Name) or target.id != "FIELD_SPECS":
            continue
        value = node.value
        if not isinstance(value, ast.Dict):
            continue
        for k, v in zip(value.keys, value.values):
            if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
                continue
            opts = {
                c.value
                for c in ast.walk(v)
                if isinstance(c, ast.Constant)
                and isinstance(c.value, str)
                and c.value not in {"TEXT", "NUMBER", "SINGLE_SELECT"}
            }
            if opts:
                out[k.value] = opts
    return out


# ==========================================================================
# 4. 守衛覆蓋：同一份資料，誰寫得動、誰跑了驗證
# ==========================================================================

_GUARD_NAME = re.compile(r"^_?(validate|check|verify|find_conflicts|assert)")
_SERIALIZER_NAME = re.compile(r"^_?(render|build|format|set)_")


@dataclass
class GuardGap:
    writer: str
    module: str
    serializer: str
    guard: str
    detail: str


def guard_coverage(modules: list[ModuleIndex], graph: CallGraph) -> list[GuardGap]:
    """找出「寫得動某份資料、卻沒跑該資料自己的驗證器」的入口。

    規則（純語法，無人維護清單）：
      1. 模組 M 同時定義 serializer（``render_*``／``build_*``／``format_*``／``set_*``）
         與 guard（``validate_*``／``check_*``／``find_conflicts``…）→ M 是「有守衛的資料
         模組」。
      2. 任何 import 了 M 的 serializer 的模組，若其呼叫圖到不了 M 的任一 guard，即為一個
         守衛覆蓋缺口。

    這條規則抓到的第一個實例就是已知缺口 #4：``resources.py`` 同時有 ``render_block`` 與
    ``find_conflicts``，而 ``amend_cmd.py`` 只 import 前者——先 assign 小射程、再 amend
    擴大，即可繞過派工閘門建立的不變量。
    """
    guarded: dict[str, tuple[set[str], set[str]]] = {}
    for mod in modules:
        serializers: set[str] = set()
        guards: set[str] = set()
        for node in mod.tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if _GUARD_NAME.match(node.name):
                    guards.add(node.name)
                elif _SERIALIZER_NAME.match(node.name):
                    serializers.add(node.name)
        if serializers and guards:
            guarded[mod.stem] = (serializers, guards)

    gaps: list[GuardGap] = []
    for mod in modules:
        imported: set[str] = set()
        for node in ast.walk(mod.tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported.add(alias.name)
        entries = {k for k in graph.edges if graph.module_of.get(k) == mod.stem}
        reach: set[str] = set(entries)
        frontier = set(entries)
        while frontier:
            nxt: set[str] = set()
            for k in frontier:
                nxt |= graph.edges.get(k, set())
            nxt -= reach
            reach |= nxt
            frontier = nxt

        for target_stem, (serializers, guards) in guarded.items():
            if target_stem == mod.stem:
                continue
            used = imported & serializers
            if not used:
                continue
            guard_keys = {f"{target_stem}.{g}" for g in guards}
            if reach & guard_keys:
                continue
            gaps.append(
                GuardGap(
                    writer=mod.rel,
                    module=target_stem,
                    serializer="／".join(sorted(used)),
                    guard="／".join(sorted(guards)),
                    detail=(
                        f"{mod.rel} import 了 {target_stem}.{'／'.join(sorted(used))}"
                        f"（因此寫得動該份資料），但其呼叫圖到不了 {target_stem} 的任一守衛"
                        f"（{'／'.join(sorted(guards))}）"
                    ),
                )
            )
    return sorted(gaps, key=lambda g: (g.writer, g.module))


# ==========================================================================
# 5. 對帳
# ==========================================================================

VERDICT_ABSENT = "absent"
VERDICT_MENTION_ONLY = "mention-only"
VERDICT_READ_ONLY = "read-only"
VERDICT_WRITE_ONLY = "write-only"
VERDICT_OK = "ok"

GAP_VERDICTS = (VERDICT_ABSENT, VERDICT_MENTION_ONLY, VERDICT_READ_ONLY, VERDICT_WRITE_ONLY)


@dataclass
class Row:
    kind: str
    name: str
    verdict: str
    doc_hits: list[DocHit]
    writers: list[Occurrence]
    readers: list[Occurrence]
    mentions: list[Occurrence]
    notes: list[str] = field(default_factory=list)

    @property
    def is_gap(self) -> bool:
        return self.verdict in GAP_VERDICTS

    def to_json(self) -> dict:
        return {
            "kind": self.kind,
            "name": self.name,
            "verdict": self.verdict,
            "doc_hits": [f"{h.path}:{h.line}" for h in self.doc_hits[:4]],
            "writers": [f"{o.path}:{o.line}" for o in self.writers[:4]],
            "readers": [f"{o.path}:{o.line}" for o in self.readers[:4]],
            "mentions": [f"{o.path}:{o.line}" for o in self.mentions[:4]],
            "notes": self.notes,
        }


_STATUS_VOCAB_MODULE = "project.py"


def _transition_sites(occs: list[Occurrence]) -> list[Occurrence]:
    """狀態值出現在「值的位置」而且不在 ``project.py`` 的詞彙表裡 → 有動詞轉得進去。

    ``project.py`` 的 ``FIELD_SPECS`` 只宣告「這個 SINGLE_SELECT 欄位有哪些選項」，
    它被寫進遠端的是**欄位定義**，不是任何一張卡的狀態轉換。把它排掉之後，剩下的命中
    才是真的有某個動詞拿這個值去設卡片狀態（argparse 預設值／choices、對照表的值、
    命令內的常數）。比對位置（``!= "📦已合併"``）不算——那是讀，不是轉。
    """
    return [
        o
        for o in occs
        if not o.path.endswith(_STATUS_VOCAB_MODULE)
        and o.role in (ROLE_WRITE, ROLE_VOCAB, ROLE_OTHER)
    ]


@dataclass
class Reconciliation:
    rows: list[Row]
    guard_gaps: list[GuardGap]

    @property
    def gaps(self) -> list[Row]:
        return [r for r in self.rows if r.is_gap]


def reconcile(root: Path) -> Reconciliation:
    universe = build_universe(root)
    symbols = [s.name for s in universe]

    modules = load_modules(root)
    graph = build_call_graph(modules)
    rmf = remote_mutating_functions(modules, graph, gh_runner_methods(root))
    connected = state_plane_connected(graph, rmf)

    per_symbol: dict[str, list[Occurrence]] = {s: [] for s in symbols}
    for mod in modules:
        for occ in classify_module(mod, symbols, connected):
            per_symbol.setdefault(occ.symbol, []).append(occ)

    open_fields = open_written_fields(root, graph)
    amendable = amendable_fields(root)
    amend_reads = amend_read_fields(root)
    verbs = cli_verbs(root)
    field_options = project_field_options(root)
    status_options: set[str] = set()
    for name, opts in field_options.items():
        if "狀態" in name:
            status_options |= opts

    rows: list[Row] = []
    for sym in universe:
        best: dict[tuple[str, int], Occurrence] = {}
        for occ in per_symbol.get(sym.name, []):
            key = (occ.path, occ.line)
            cur = best.get(key)
            if cur is None or _ROLE_RANK[occ.role] > _ROLE_RANK[cur.role]:
                best[key] = occ
        occs = sorted(best.values(), key=lambda o: (o.path, o.line))

        writers = [o for o in occs if o.role == ROLE_WRITE]
        readers = [o for o in occs if o.role in (ROLE_READ, ROLE_VOCAB)]
        mentions = [o for o in occs if o.role in MENTION_ROLES]

        notes: list[str] = []
        if sym.kind == KIND_EVENT:
            related = related_verbs(sym.name, verbs)
            notes.append(f"相關動詞={'／'.join(related) if related else '無'}")
        if sym.kind == KIND_FIELD:
            in_open = sym.name in open_fields
            can_amend = sym.name in amendable
            notes.append(f"open 渲染={'是' if in_open else '否'}")
            notes.append(f"amend 可改={'是' if can_amend else '否'}")
            if in_open and not can_amend:
                notes.append("⚠️ 開卡寫得進、開卡後改不動")
            if sym.name in amend_reads and not can_amend:
                notes.append("⚠️ amend 讀它當判準卻改不動它")
        if not occs:
            verdict = VERDICT_ABSENT
        elif writers and readers:
            verdict = VERDICT_OK
        elif writers:
            verdict = VERDICT_WRITE_ONLY
        elif readers:
            verdict = VERDICT_READ_ONLY
        else:
            verdict = VERDICT_MENTION_ONLY

        if sym.kind == KIND_STATUS:
            # 交付狀態需要專屬判準：實際的狀態轉換是**資料驅動**的
            # （``set_field_value(..., args.status)``），字面在通用規則下永遠停在
            # ``project.FIELD_SPECS`` 的詞彙表裡，於是每一個狀態都會被判成 read-only ——
            # 那等於沒有鑑別力。真正的問題是「**有沒有任何動詞轉得進這個狀態**」。
            in_options = sym.name in status_options
            transition = _transition_sites(occs)
            notes.append(f"Project 選項={'是' if in_options else '否'}")
            notes.append(f"轉得進去={'是' if transition else '否'}")
            if in_options:
                verdict = VERDICT_OK if transition else VERDICT_READ_ONLY
                if not transition:
                    notes.append("⚠️ 狀態表列了這個選項，但沒有任何動詞轉得進去")
            if transition:
                writers = transition

        rows.append(
            Row(
                kind=sym.kind,
                name=sym.name,
                verdict=verdict,
                doc_hits=sym.hits,
                writers=writers,
                readers=readers,
                mentions=mentions,
                notes=notes,
            )
        )

    return Reconciliation(rows=rows, guard_gaps=guard_coverage(modules, graph))


# ==========================================================================
# 6. 輸出與 --check
# ==========================================================================

DISPOSITION_DOC = "docs/CONTRACT_TOOL_RECONCILE.md"
DISPOSITION_BEGIN = "<!-- reconcile-dispositions:begin -->"
DISPOSITION_END = "<!-- reconcile-dispositions:end -->"


def parse_dispositions(root: Path) -> dict[str, str]:
    """讀處置登記。缺檔／缺區塊／解析失敗一律回空 dict → ``--check`` 全紅。"""
    path = root / DISPOSITION_DOC
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    start = text.find(DISPOSITION_BEGIN)
    end = text.find(DISPOSITION_END)
    if start == -1 or end == -1 or end < start:
        return {}
    fence = re.search(r"```json\s*(.*?)```", text[start + len(DISPOSITION_BEGIN) : end], re.DOTALL)
    if not fence:
        return {}
    try:
        data = json.loads(fence.group(1))
    except json.JSONDecodeError:
        return {}
    return {str(k): str(v) for k, v in data.get("gaps", {}).items()}


def gap_key(row: Row) -> str:
    return f"{row.kind}/{row.name}"


def guard_gap_key(gap: GuardGap) -> str:
    """守衛覆蓋缺口的登記鍵。

    ⚠️ 這一支是補上去的：第一版的 ``--check`` 只比對符號列，守衛覆蓋缺口完全不在
    ratchet 內。變異檢驗 M3（把呼叫圖退回同名全集）當場證明了這個洞——已知缺口 #4
    整個消失，而 ``--check`` 仍然是綠的。**沒被 ratchet 蓋住的檢查等於沒有檢查。**
    """
    return f"guard/{gap.writer}→{gap.module}"


def all_gap_entries(rec: "Reconciliation") -> dict[str, str]:
    entries = {gap_key(r): r.verdict for r in rec.gaps}
    for g in rec.guard_gaps:
        entries[guard_gap_key(g)] = g.guard
    return entries


def _cells(items: list[str], limit: int = 3) -> str:
    if not items:
        return "—"
    shown = [f"`{i}`" for i in items[:limit]]
    if len(items) > limit:
        shown.append(f"…共 {len(items)}")
    return "<br>".join(shown)


def render_markdown(rec: Reconciliation, shown: list[Row]) -> str:
    out: list[str] = []
    out.append(f"- 契約側符號總數：**{len(rec.rows)}**（由掃描文件導出，非人工登記）")
    out.append(f"- 判定為缺口：**{len(rec.gaps)}**")
    out.append(f"- 守衛覆蓋缺口：**{len(rec.guard_gaps)}**")
    out.append("")
    for kind, label in (
        (KIND_EVENT, "事件型別"),
        (KIND_STATUS, "交付狀態"),
        (KIND_FIELD, "卡面欄位"),
    ):
        subset = [r for r in shown if r.kind == kind]
        if not subset:
            continue
        out.append(f"### {label}（{len(subset)}）")
        out.append("")
        out.append("| 符號 | 判定 | 契約出處 | 寫入者 | 讀取者 | 備註 |")
        out.append("|---|---|---|---|---|---|")
        for r in sorted(subset, key=lambda r: (r.verdict == VERDICT_OK, r.name)):
            out.append(
                "| `{n}` | {v} | {d} | {w} | {rd} | {no} |".format(
                    n=r.name,
                    v=r.verdict,
                    d=_cells([f"{h.path}:{h.line}" for h in r.doc_hits]),
                    w=_cells([f"{o.path}:{o.line}" for o in r.writers]),
                    rd=_cells([f"{o.path}:{o.line}" for o in r.readers]),
                    no="；".join(r.notes) or "—",
                )
            )
        out.append("")
    out.append(f"### 守衛覆蓋缺口（{len(rec.guard_gaps)}）")
    out.append("")
    if not rec.guard_gaps:
        out.append("（無）")
    else:
        out.append("| 寫入入口 | 資料模組 | 用到的 serializer | 未跑的守衛 |")
        out.append("|---|---|---|---|")
        for g in rec.guard_gaps:
            out.append(f"| `{g.writer}` | `{g.module}` | `{g.serializer}` | `{g.guard}` |")
    out.append("")
    return "\n".join(out)


def run_check(root: Path, rec: Reconciliation, stream=None) -> int:
    """把機械缺口集合與登記處置逐項比對。三個方向都會紅。"""
    err = stream or sys.stderr
    registered = parse_dispositions(root)
    actual = all_gap_entries(rec)

    missing = sorted(set(actual) - set(registered))
    stale = sorted(set(registered) - set(actual))
    changed = sorted(k for k in set(actual) & set(registered) if actual[k] != registered[k])

    if not (missing or stale or changed):
        print(f"[reconcile] OK：{len(actual)} 個缺口全部有登記處置，判定一致。")
        return 0

    print("[reconcile] 對帳不符：", file=err)
    for k in missing:
        print(f"  - 缺口未登記處置：{k}（判定 {actual[k]}）", file=err)
    for k in stale:
        print(f"  - 登記了已不存在的缺口：{k}（登記 {registered[k]}）", file=err)
    for k in changed:
        print(f"  - 判定變了：{k}　登記 {registered[k]} → 實際 {actual[k]}", file=err)
    print(
        f"  ⚠️ 實際缺口 {len(actual)}、登記 {len(registered)}；處置表在 {DISPOSITION_DOC}，"
        "刪掉一列不會讓這個檢查變綠。",
        file=err,
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="契約↔工具對帳器")
    parser.add_argument("--root", default=str(REPO_ROOT))
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument("--check", action="store_true", help="與登記處置對帳，不符即非零退出")
    parser.add_argument("--gaps-only", action="store_true", help="只列缺口")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    rec = reconcile(root)

    if args.check:
        return run_check(root, rec)

    shown = rec.gaps if args.gaps_only else rec.rows
    if args.format == "json":
        print(
            json.dumps(
                {
                    "symbol_count": len(rec.rows),
                    "gap_count": len(rec.gaps),
                    "rows": [r.to_json() for r in shown],
                    "guard_gaps": [
                        {
                            "writer": g.writer,
                            "module": g.module,
                            "serializer": g.serializer,
                            "guard": g.guard,
                            "detail": g.detail,
                        }
                        for g in rec.guard_gaps
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(render_markdown(rec, shown))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
