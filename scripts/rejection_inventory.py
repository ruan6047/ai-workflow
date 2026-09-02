#!/usr/bin/env python3
r"""拒絕訊息全集盤點（`WF-REDESIGN-W3` 驗收 4 的 artifact 產生器）。

## 本腳本做什麼、不做什麼

卡面驗收 4 逐字要求「**開卡時 artifact 重列全集**」。本腳本產生那份 artifact：
掃 ``cli/src`` 的 ``.py``，把每一則拒絕訊息連同**它所在的完整 statement** 抽出來，
逐則附三條**機械必要條件**的判定。

⛔ **本腳本不判「這則訊息有沒有跑得出的補救」。** 那是**內容判斷**，決議
``docs/research/WORKFLOW-REDESIGN-2026-08-30.md:70`` 逐字「拒收點三層：執行者提出→
**PM 判**『訊息有沒有跑得出的補救』→⛔ 不可補上呈」⇒ 判定者是 PM，⛔ 不是 regex。
本腳本輸出的 ``mechanical`` 欄是**必要非充分**的前置篩，PM 在其上做內容判斷。

## 三條機械必要條件（規劃階段裁定 17，⛔ 非充分）

1. 訊息含一條**可整行複製**的指令（行內出現 ``wfcli``／``git``／``gh`` 起首的片段）
2. 該指令的**首 token** ∈ ``{wfcli, git, gh}``
3. 該指令**⛔ 不含 ``<…>`` 佔位符**

⚠️ 三條**同時成立**才記 ``mechanical.pass = true``；⛔ 那只代表「值得 PM 看」，
⛔ 不代表「補救跑得出來」。反之 ``false`` 也⛔ 不代表補不出——PM 仍須逐則判。

## 定位口徑＝grep，AST 只用來取完整片段

⭐ **總數必須與規格釘死的量法逐位元一致**：卡面驗收 4 的量法逐字是
``grep -rnoE '\[[a-z-]+\] 拒[絕收]' --include='*.py' cli/src``（逐行、**逐 occurrence**），
今日值 **73**。⇒ 本腳本的**定位**照同一口徑走（逐行 ``finditer``），⛔ 不用 AST 走訪節點。

⚠️ **為什麼不用 AST 定位**（實測登記）：``ast.walk`` 會**同時**訪問 ``JoinedStr`` 與它內部的
``Constant`` ⇒ 同一個關鍵字被算兩次，首版實測得 **109** 則（>73）。分母 61 建立在 73 上，
口徑不一致就整個垮掉。⇒ **定位歸 grep，AST 只負責把命中行擴成完整 statement。**

## 為什麼仍要 AST（只用來取片段）

拒絕訊息是**多行 f-string 拼接**（實例：``amend_cmd.py:1002``–``:1004`` 一則跨三行、
``pitfalls.py:389``–``:409`` 一則跨二十行且含 ``lines.append`` 迴圈）。若片段只取命中
那一行，訊息的補救段落**恰好通常在後續行** ⇒ 三條機械條件會全部誤判為不成立。
⇒ 命中行定位好之後，用 AST 找**包住該行的最內層 statement**，取其完整 source segment。

⚠️ **能力上界，明說**：本腳本取的是**原始碼字面**，⛔ 不是執行期的實際輸出。訊息裡的
``{變數}`` 插值、以及像 ``pitfalls.refusal_message`` 那樣由 ``report_template(phase)``
在執行期展開的內容，本腳本**看不到展開後的樣子**。⇒ ``mechanical`` 欄對這類訊息會
偏保守（可能低估）。PM 判定時應以原始碼片段為準，必要時實跑該指令看輸出。

## 母體與分母

- **全集**：關鍵字集逐字 ``/\[[a-z-]+\] 拒[絕收]/``、語料 ``cli/src`` 之 ``.py``、
  計 **occurrence**（同一 statement 內出現兩次即計兩則）。
- **可動母體**：全集扣除 ``deploy_state_cmd.py`` 與 ``deploy_declare_cmd.py``——
  卡面非射程逐字「⛔ 不動 ``deploy-state``／``deploy-declare``」。那兩檔的訊息
  **仍列進全集**（盤點唯讀），但標 ``in_scope: false``。
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

#: 關鍵字集。**逐字取自卡面核心痛點**，⛔ 不得改寫——改了就不是同一個母體。
KEYWORD_RE = re.compile(r"\[[a-z-]+\] 拒[絕收]")

#: 非射程的兩支動詞檔（卡面非射程逐字「⛔ 不動 deploy-state／deploy-declare」）。
#: 它們的訊息**仍進全集**（盤點是唯讀的），只是 ``in_scope=False``。
OUT_OF_SCOPE_FILES = frozenset({"deploy_state_cmd.py", "deploy_declare_cmd.py"})

#: **切界上限**：一則訊息的 statement 跨行數超過它，即判定 AST 定位**切界失敗**。
#:
#: ⭐ **為什麼要有這一條**（`WF-REDESIGN-W3` R1／需求方 2026-09-02 裁定）：AST 只看得見
#: **statement**，看不見 `#` 註解。命中行落在註解裡時，「包住它的最內層 statement」會
#: 退化成整個 `FunctionDef` ⇒ 片段變成幾百行，而三條機械條件會從那幾百行的**別處**
#: 撈到一條指令，判成 `passes: true`。實測：`open_cmd.py:358`／`:403`／`:410` 各取到
#: 整個 `run()`（**324 行**），其 `command` 是從無關的地方撈來的。
#:
#: **20 這個值的依據是斷層，⛔ 不是品味**（量測日 2026-09-02，可動母體 66 則）：
#: 跨行數中位數 **6**，第 5 大是 **15**，而前 4 大是 **324／324／324／54**。
#: ⛔ **不得改成白名單列那四個位置**——那是「開放集合→封閉集合」反過來走。
STATEMENT_SPAN_CEILING = 20

#: 裁定 17 第 (ii) 條的首 token 封閉集合。⛔ 不得擴張——值域的 owner 是規劃階段的規格。
RUNNABLE_HEADS = ("wfcli", "git", "gh")

#: 裁定 17 第 (iii) 條：佔位符樣式。``<…>`` 之間⛔ 不含換行與 ``>``。
PLACEHOLDER_RE = re.compile(r"<[^<>\n]{1,60}>")

#: 從訊息片段裡撈「看起來像可整行複製的指令」。**下界**：只認以三個首 token 起首、
#: 且該 token 前面只有空白或引號的位置。⚠️ 認不出被字串拼接切斷的指令。
_COMMAND_RE = re.compile(
    r"(?:^|[\s\"'`])(" + "|".join(RUNNABLE_HEADS) + r")\s+([^\n\"'`]{1,200})"
)


@dataclass
class Mechanical:
    """裁定 17 的三條機械必要條件，逐條記錄，⛔ 不合併成一個布林就丟掉細節。"""

    has_command: bool
    head_ok: bool
    no_placeholder: bool
    #: 撈到的第一條指令原文（供 PM 判定時直接看）；沒撈到為 ``None``。
    command: str | None = None
    #: 指令若是由**呼叫到的同檔函式**產生，記下那個函式名；直接在本 statement 內為 ``None``。
    #: ⭐ 這一欄讓「機械看不見的補救」變成看得見的（第四個 artifact 缺陷）。
    command_via: str | None = None

    #: AST 定位有沒有切在合理的邊界上（見 :data:`STATEMENT_SPAN_CEILING`）。
    #: ⚠️ 這**不是**裁定 17 的第四條——它是**前三條能不能被信任**的前提：切界失敗時
    #: 那三條看的根本不是這一則訊息的文字。
    boundary_ok: bool = True

    @property
    def passes(self) -> bool:
        return self.boundary_ok and self.has_command and self.head_ok and self.no_placeholder


@dataclass
class Rejection:
    file: str
    #: 關鍵字出現的行號（1-indexed）。
    line: int
    #: ``[<verb>]`` 裡的動詞字面。
    verb: str
    #: 關鍵字字面（``拒絕`` 或 ``拒收``）。
    keyword: str
    #: 該關鍵字所在 statement 的完整原始碼片段。
    statement: str
    statement_lines: tuple[int, int]
    in_scope: bool
    #: ``message``／``comment``／``docstring``。
    #:
    #: ⭐ **釘死的 grep 抓的是字面，抓得到「講這個格式的文字」**：函式 docstring 在
    #: 描述檢查行為時會引用 ``[open] 拒絕：…``，`#:` 註解也會。那些**不是訊息**，
    #: 補不了「跑得出的補救」。需求方 2026-09-02 裁定**移出可動母體**。
    #: ⚠️ 它們**仍列進全集**——全集的定義是釘死的 grep，⛔ 不因為分類而改口徑。
    kind: str
    #: statement 跨行數。⚠️ 與 :data:`STATEMENT_SPAN_CEILING` 比對。
    span: int
    mechanical: Mechanical
    #: PM 逐則判定的欄位，本腳本一律留空——⛔ 內容判斷不由機械代算。
    pm_verdict: str = ""
    pm_remedy: str = ""


def _docstring_line_numbers(tree: ast.AST) -> set[int]:
    """所有 docstring 佔用的行號。

    ⛔ 只認**真正的 docstring**（模組／函式／類別 body 的第一個字串 `Expr`），
    ⛔ 不認任何字串字面——訊息本身就是字串字面，認寬了會把訊息全部誤判掉。
    """
    lines: set[int] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            lines.update(range(first.lineno, (first.end_lineno or first.lineno) + 1))
    return lines


def _enclosing_statement_at(tree: ast.AST, lineno: int) -> ast.stmt | None:
    """回傳包住 ``target`` 的最近 statement。

    ⭐ **為什麼要走到 statement 而不是停在命中行**：訊息的補救段落通常在**後續行**
    （``print("拒絕：…"\n      "  請改用 wfcli …")``），只取命中行會把補救切掉 ⇒
    三條機械條件會全部誤判為不成立。
    """
    best: ast.stmt | None = None
    best_span = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.stmt):
            continue
        lo = node.lineno
        hi = node.end_lineno
        if hi is None or not (lo <= lineno <= hi):
            continue
        span = hi - lo
        # 取範圍最小的那個 ⇒ 最內層 statement。
        if best_span is None or span < best_span:
            best, best_span = node, span
    return best


def _render_text(node: ast.AST) -> str:
    """把一個 statement 內的字串字面**依原始順序**串成「訊息大致長什麼樣」。

    ⭐ **為什麼非做不可**（`WF-REDESIGN-W3` 驗收 3，第五與第六個 artifact 缺陷）：

    - **第五**：本 repo 的訊息是**多行字串串接**，而可複製的指令常常橫跨兩個字面
      （``f"    wfcli snapshot --owner {o} --project {p} "`` ＋ ``"--out-dir /tmp/x"``）。
      直接對原始碼跑正規式會**在換行處截斷** ⇒ 把一條完整的指令誤判成缺旗標。
      實測：`assign_cmd.py`／`open_cmd.py`／`review_cmd.py` 的三則 `wfcli snapshot`
      被切成「缺 `--out-dir`」，而訊息本身是完整的。
    - **第六**：散文裡**用反引號提到**一個指令（例：「唯一的出路是走
      `gh issue edit --body-file` 手動截斷」）**不是**可複製的指令行。串好之後改以
      **行首**判定（見 :func:`_command_lines`），散文提及自然落選。

    ⚠️ **能力上界**：``{變數}`` 以原樣的佔位形式保留（⛔ 不求值——本腳本讀的是原始碼
    字面，見模組 docstring）。⇒ 這是「訊息**大致**長什麼樣」，⛔ 不是執行期輸出。
    """
    parts: list[str] = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.JoinedStr):
            for value in sub.values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    parts.append(value.value)
                elif isinstance(value, ast.FormattedValue):
                    # ⛔ 不求值；保留一個**不含 `<…>`** 的佔位，免得誤觸第 (iii) 條。
                    parts.append("{…}")
        elif isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            if not any(sub is v for j in ast.walk(node)
                       if isinstance(j, ast.JoinedStr) for v in j.values):
                parts.append(sub.value)
    return "".join(parts)


def _command_lines(text: str) -> list[str]:
    """從串好的訊息裡挑出**可整行複製**的指令行。

    判準：該行 strip 之後**以** :data:`RUNNABLE_HEADS` 之一**起首**。
    ⭐ 這一條把「散文裡提到指令」擋在外面——散文行不會以 ``wfcli``／``git``／``gh``
    起首。⛔ 不改回「行內任意位置出現」，那正是第六個缺陷的來源。
    """
    found: list[str] = []
    for raw in text.splitlines():
        line = raw.strip().strip("`")
        for head in RUNNABLE_HEADS:
            if line.startswith(head + " "):
                found.append(line)
                break
    return found


def _evaluate(
    segment: str,
    span: int = 1,
    node: ast.AST | None = None,
    helpers: dict[str, ast.AST] | None = None,
) -> Mechanical:
    """三條機械必要條件 ＋ **切界是否可信**。

    ⚠️ `span` 超過 :data:`STATEMENT_SPAN_CEILING` 時，前三條看的根本不是這一則訊息的
    文字（片段被撐成整個函式）⇒ `passes` 一律 `False`，⛔ 不論那三條長怎樣。

    ⭐ **`helpers` 讓判準看得見「補救由函式產生」**（第四個 artifact 缺陷）：
    ``print(f"…拒絕…" + _resume_runbook(owner, n), …)`` 的指令在 `_resume_runbook`
    的**函式體**裡，⛔ 不在本 statement 內。⇒ 對本 statement 呼叫到的**同檔模組級
    函式**展開**一層**，把它們的字串一併算進來。
    ⚠️ **只展開一層**——遞迴會讓「這一則訊息到底印了什麼」變成一個要解整個呼叫圖
    才答得出的問題。⚠️ 展開範圍含**同檔**與**語料內其他模組**的模組級函式（實例：
    `open_cmd` 的 `remediation` 來自 `intake`）；同名時**同檔優先**。
    """
    boundary_ok = span <= STATEMENT_SPAN_CEILING
    if not boundary_ok:
        # ⛔ **切界失敗時⛔ 不再擷取指令**：片段是整個函式，把它的字串全串起來只會
        # 得到一串亂碼（實測：`open_cmd` 的三則會串出
        # ``gh issue list …--limit 20issueview--repo--json…``）。留一個假指令在
        # artifact 裡，PM 逐則裁定時會拿它去跑——那正是本輪要收的形態。
        return Mechanical(
            has_command=False, head_ok=False, no_placeholder=False, boundary_ok=False
        )

    text = _render_text(node) if node is not None else segment
    lines = _command_lines(text)
    via: str | None = None
    if not lines and node is not None and helpers:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                helper = helpers.get(sub.func.id)
                if helper is None:
                    continue
                helper_lines = _command_lines(_render_text(helper))
                if helper_lines:
                    lines = helper_lines
                    via = sub.func.id
                    break

    if not lines:
        return Mechanical(
            has_command=False, head_ok=False, no_placeholder=False, boundary_ok=boundary_ok
        )
    command = lines[0]
    head = command.split(" ", 1)[0]
    return Mechanical(
        has_command=True,
        head_ok=head in RUNNABLE_HEADS,
        no_placeholder=PLACEHOLDER_RE.search(command) is None,
        command=command,
        command_via=via,
        boundary_ok=boundary_ok,
    )


def _collect_helpers(src_root: Path) -> dict[str, ast.AST]:
    """語料內**全部**模組級函式，供 :func:`_evaluate` 展開一層用。

    ⭐ 為什麼要跨檔：`open_cmd` 的補救由 `intake.remediation` 產生——只掃同檔會判成
    「沒有補救」，而那是**機械看不見真的有補救**（artifact 第四個缺陷的另一半）。
    ⚠️ **同名以最後掃到的為準，且同檔優先**（見 :func:`scan`）；⛔ 不解 import 別名圖
    ——那要解整個模組圖，而本腳本的定位是盤點器⛔ 不是型別檢查器。此上界明說於此。
    """
    helpers: dict[str, ast.AST] = {}
    for path in sorted(src_root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover - 語料是本 repo 自己的碼
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                helpers.setdefault(node.name, node)
    return helpers


def scan(src_root: Path) -> list[Rejection]:
    rows: list[Rejection] = []
    global_helpers = _collect_helpers(src_root)
    for path in sorted(src_root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:  # pragma: no cover - 語料是本 repo 自己的碼
            print(f"[inventory] ⛔ 解析失敗 {path}: {exc}", file=sys.stderr)
            raise
        docstring_lines = _docstring_line_numbers(tree)
        helpers: dict[str, ast.AST] = dict(global_helpers)
        # ⚠️ 同名時**同檔優先**——同檔的那一個才是這則訊息真正呼叫到的。
        helpers.update(
            {
                n.name: n
                for n in tree.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
        )
        # ⭐ 定位＝grep 口徑：逐行、逐 occurrence。⛔ 不用 AST 走訪（會重複計數）。
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in KEYWORD_RE.finditer(line):
                stmt = _enclosing_statement_at(tree, lineno)
                if stmt is None:
                    segment = line.strip()
                    bounds = (lineno, lineno)
                else:
                    segment = ast.get_source_segment(text, stmt) or line.strip()
                    bounds = (stmt.lineno, stmt.end_lineno or stmt.lineno)
                span = bounds[1] - bounds[0] + 1

                # ⭐ **命中落在註解或 docstring 裡 ⇒ 它不是一則訊息。**
                # `#` 註解對 AST **完全不可見** ⇒ 「最內層 statement」退化成整個
                # `FunctionDef`；docstring 是 `ast.Expr`，片段看起來正常但內容是
                # **描述訊息格式的文字**，⛔ 不是訊息本身。兩者都補不了補救。
                if line.lstrip().startswith("#"):
                    kind = "comment"
                elif lineno in docstring_lines:
                    kind = "docstring"
                else:
                    kind = "message"

                verb = match.group(0).split("]")[0].lstrip("[")
                rows.append(
                    Rejection(
                        file=str(path.relative_to(src_root.parent.parent)),
                        line=lineno,
                        verb=verb,
                        keyword=match.group(0).split("] ")[1],
                        statement=segment,
                        statement_lines=bounds,
                        in_scope=path.name not in OUT_OF_SCOPE_FILES,
                        kind=kind,
                        span=span,
                        mechanical=_evaluate(segment, span, stmt, helpers),
                    )
                )
    rows.sort(key=lambda r: (r.file, r.line))
    return rows


def summarise(rows: list[Rejection]) -> dict:
    """三層母體，逐層各有各的定義，⛔ 不得互相代用。

    | 層 | 定義 |
    |---|---|
    | **全集** | 釘死的 grep 的全部命中。⛔ 口徑不因任何分類而改。 |
    | **可動母體** | 全集扣掉非射程的兩支 deploy 動詞檔。 |
    | ⭐ **可補母體** | 可動母體再扣掉 `kind != "message"` 的那些——需求方 2026-09-02 裁定：註解與 docstring **不是訊息**，補不了「跑得出的補救」。 |
    """
    in_scope = [r for r in rows if r.in_scope]
    fixable = [r for r in in_scope if r.kind == "message"]
    per_file: dict[str, int] = {}
    kinds: dict[str, int] = {}
    for r in rows:
        per_file[r.file] = per_file.get(r.file, 0) + 1
    for r in in_scope:
        kinds[r.kind] = kinds.get(r.kind, 0) + 1
    return {
        "total": len(rows),
        "in_scope": len(in_scope),
        "out_of_scope": len(rows) - len(in_scope),
        "in_scope_by_kind": dict(sorted(kinds.items())),
        "fixable": len(fixable),
        "boundary_failures": sum(1 for r in in_scope if not r.mechanical.boundary_ok),
        "mechanical_pass_in_scope": sum(1 for r in in_scope if r.mechanical.passes),
        "mechanical_pass_in_fixable": sum(1 for r in fixable if r.mechanical.passes),
        "statement_span_ceiling": STATEMENT_SPAN_CEILING,
        "per_file": dict(sorted(per_file.items(), key=lambda kv: -kv[1])),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="拒絕訊息全集盤點（驗收 4 的 artifact 產生器）")
    parser.add_argument(
        "--src",
        default=None,
        help="cli/src 的路徑；預設由本檔位置推導（<repo>/cli/src）",
    )
    parser.add_argument("--json", action="store_true", help="stdout 只輸出 JSON")
    args = parser.parse_args(argv)

    src = Path(args.src) if args.src else Path(__file__).resolve().parents[1] / "cli" / "src"
    if not src.exists():
        print(f"[inventory] ⛔ 找不到語料目錄：{src}", file=sys.stderr)
        return 2

    rows = scan(src)
    summary = summarise(rows)
    payload = {
        "artifact": "wf-cli/rejection-inventory/v1",
        "keyword_regex": KEYWORD_RE.pattern,
        "corpus": str(src),
        "out_of_scope_files": sorted(OUT_OF_SCOPE_FILES),
        "summary": summary,
        "statement_span_ceiling": STATEMENT_SPAN_CEILING,
        "rows": [asdict(r) | {"mechanical": asdict(r.mechanical) | {"passes": r.mechanical.passes}} for r in rows],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"拒絕訊息全集：{summary['total']} 則")
    print(f"  可動母體（扣非射程 {summary['out_of_scope']} 則）：{summary['in_scope']}")
    print(f"    逐類：{summary['in_scope_by_kind']}")
    print(
        f"  ⭐ 可補母體（再扣註解與 docstring）：{summary['fixable']}"
        "　← 需求方 2026-09-02 裁定：那些**不是訊息**"
    )
    print(
        f"  切界失敗（statement 跨行 > {summary['statement_span_ceiling']}）："
        f"{summary['boundary_failures']} 則　← 命中落在註解裡，AST 片段被撐成整個函式"
    )
    print(f"  三條機械必要條件同時成立（可補母體內）：{summary['mechanical_pass_in_fixable']}")
    print("\n逐檔：")
    for f, n in summary["per_file"].items():
        mark = " ⛔非射程" if Path(f).name in OUT_OF_SCOPE_FILES else ""
        print(f"  {n:3d}  {f}{mark}")
    print("\n⛔ 「有沒有跑得出的補救」是內容判斷，歸 PM（決議 :70 逐字）。")
    print("   本輸出的 mechanical 欄是必要非充分的前置篩，⛔ 不是判定。")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
