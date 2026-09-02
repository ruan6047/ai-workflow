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

    @property
    def passes(self) -> bool:
        return self.has_command and self.head_ok and self.no_placeholder


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
    mechanical: Mechanical
    #: PM 逐則判定的欄位，本腳本一律留空——⛔ 內容判斷不由機械代算。
    pm_verdict: str = ""
    pm_remedy: str = ""


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


def _evaluate(segment: str) -> Mechanical:
    m = _COMMAND_RE.search(segment)
    if m is None:
        return Mechanical(has_command=False, head_ok=False, no_placeholder=False)
    command = (m.group(1) + " " + m.group(2)).strip()
    return Mechanical(
        has_command=True,
        head_ok=m.group(1) in RUNNABLE_HEADS,
        no_placeholder=PLACEHOLDER_RE.search(command) is None,
        command=command,
    )


def scan(src_root: Path) -> list[Rejection]:
    rows: list[Rejection] = []
    for path in sorted(src_root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:  # pragma: no cover - 語料是本 repo 自己的碼
            print(f"[inventory] ⛔ 解析失敗 {path}: {exc}", file=sys.stderr)
            raise
        # ⭐ 定位＝grep 口徑：逐行、逐 occurrence。⛔ 不用 AST 走訪（會重複計數）。
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in KEYWORD_RE.finditer(line):
                stmt = _enclosing_statement_at(tree, lineno)
                if stmt is None:
                    segment = line.strip()
                    span = (lineno, lineno)
                else:
                    segment = ast.get_source_segment(text, stmt) or line.strip()
                    span = (stmt.lineno, stmt.end_lineno or stmt.lineno)
                verb = match.group(0).split("]")[0].lstrip("[")
                rows.append(
                    Rejection(
                        file=str(path.relative_to(src_root.parent.parent)),
                        line=lineno,
                        verb=verb,
                        keyword=match.group(0).split("] ")[1],
                        statement=segment,
                        statement_lines=span,
                        in_scope=path.name not in OUT_OF_SCOPE_FILES,
                        mechanical=_evaluate(segment),
                    )
                )
    rows.sort(key=lambda r: (r.file, r.line))
    return rows


def summarise(rows: list[Rejection]) -> dict:
    in_scope = [r for r in rows if r.in_scope]
    per_file: dict[str, int] = {}
    for r in rows:
        per_file[r.file] = per_file.get(r.file, 0) + 1
    return {
        "total": len(rows),
        "in_scope": len(in_scope),
        "out_of_scope": len(rows) - len(in_scope),
        "mechanical_pass_in_scope": sum(1 for r in in_scope if r.mechanical.passes),
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
        "rows": [asdict(r) | {"mechanical": asdict(r.mechanical) | {"passes": r.mechanical.passes}} for r in rows],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"拒絕訊息全集：{summary['total']} 則")
    print(f"  可動母體（扣非射程 {summary['out_of_scope']} 則）：{summary['in_scope']}")
    print(f"  三條機械必要條件同時成立（可動母體內）：{summary['mechanical_pass_in_scope']}")
    print("\n逐檔：")
    for f, n in summary["per_file"].items():
        mark = " ⛔非射程" if Path(f).name in OUT_OF_SCOPE_FILES else ""
        print(f"  {n:3d}  {f}{mark}")
    print("\n⛔ 「有沒有跑得出的補救」是內容判斷，歸 PM（決議 :70 逐字）。")
    print("   本輸出的 mechanical 欄是必要非充分的前置篩，⛔ 不是判定。")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
