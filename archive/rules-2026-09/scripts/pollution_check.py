#!/usr/bin/env python3
# LIFECYCLE: disposable · 拋棄式——WF-REDESIGN-W2A 專用；本波結案後可刪，⛔ 不是常設工具
r"""污染符 allowlist-aware checker（WF-REDESIGN-W2A，AC4＋AC5）。

## 這支腳本回答的問題

決議紀錄 §二 列了一組**污染符**：新規則文字裡不該再長出來的舊語彙。原本的做法是查核者
對施工卡 diff 逐字 grep——而 P1-31 指出那個形狀壞在兩處：

- **raw grep 無法同時表達「0」與「豁免」。** 有一個核准過的例外，命中數就不是 0；
  於是判準只好退化成人眼看一遍。
- **零命中還回 `rc=1`。** `grep` 找不到就是 1，跟「工具壞掉」同一個退出碼。

⇒ 改成本腳本：逐符**逐 occurrence** 掃描 → 逐命中輸出 → 核准例外住 versioned manifest →
**唯一 pass criterion＝`unapproved_count == 0`**。

AC5 併入同一份輸出：三個腐爛自述（`短版` ／ `最後核實` ／ 行數自述樣式）也是本腳本的
**輸入 token**，⛔ 不另外宣告一個 raw count；它們的豁免同樣走 manifest。

## token 集合的單一來源

**決議紀錄 §二 的那一行就是 universe，⛔ 不另立第二份。** 該行有 **13** 個符
（R1-003 實據：本腳本首版註解誤稱 12 個，且整個漏掉 `Discovery lead`）。
⇒ :data:`POLLUTION_TOKENS` 逐字照抄該行的順序與內容；:data:`ROT_TOKENS` 是 AC5 另加的三個。
⚠️ 增刪 token 必須先改決議 §二，⛔ 不得只改這裡——封閉值域只能由 owner 裁定擴張。

## 逐 occurrence，⛔ 不是逐行

`re.finditer`，⛔ 不是 `search`。R1-003 實據：改之前同一 token 在同一行重複只記一筆，
本腳本自己的檔實得 29 次卻只記 16 筆、manifest 實得 100 次只記 99 筆
⇒ manifest 的 `occurrences` 綁到的是「命中的行數」而不是 AC 要的**逐 hit 數**。

## 射程＝post-image，⛔ 不是全 repo

掃的是**本卡改過的那些檔案的當前內容**（`git diff --name-only <BASE>` 的存活路徑
＋未追蹤檔）。⛔ 不掃全 repo：污染符在 `archive/` 的舊卡裡本來就到處都是，那些不是
「新規則文脈」，把它們掃進來只會逼出一份幾百筆的豁免清單，而那份清單本身就會變成沒有人
讀的東西。

⚠️ **它得到的是下界**（沿決議 §二 逐字「抓字面不抓換句話說」）：換句話說寫出來的舊語彙
本腳本一無所知；`（新規則文脈）` 那類限定詞是**人的判斷**，機器只能給你命中，
由 manifest 的 `rationale` 承接判斷。

## 自指命中：**在母體內、可見、列計**，⛔ 不排除

本腳本、它的 manifest 與它的測試檔也在掃描母體內（:data:`SELF_REFERENCE_PATHS`）。它們的命中歸入
獨立的 **`self_reference`** 類：**逐筆列出、逐檔逐 token 列計**，並計入 `total_hits`。
承接 canonical §6.2 逐字「工具或測試檔本身被自己掃到時，明確歸類為**自指命中並可見列計**，
不得偷偷排除」——R1-003 逐字指出「列出檔名⛔ 不等於列計命中」，首版把 checker 與 manifest 整個踢出母體是錯的；
測試檔同屬 §6.2 逐字點名的「測試檔」一類。

**為什麼自指命中⛔ 不走 manifest（而是自成一類）**：manifest 的每一筆條目自己會寫下
`"token": "<那個符>"` 與 `"excerpt": "<那一行>"` 兩行，兩行都含該符 ⇒ 為一筆自指命中開一筆
豁免，就長出兩筆新的自指命中，再各要一筆豁免……**這個過程不收斂**（每輪至少 ×2）。
⇒ 用 manifest 表達自指是構造上做不到的，只能分類。
(c) ⛔ **不得由此推出「這三個檔可以藏東西」**：它們在母體內、每一筆命中都印得出來、
逐檔逐 token 有計數；⛔ 不得推出「self_reference 是豁免」——它是**分類**，
`unapproved_count` ⛔ 不涵蓋它是因為它另有一條可稽核的可見通道，⛔ 不是因為它被跳過。

## manifest 的形狀

`scripts/pollution-allowlist.json`，逐 hit 綁三件事：

- `token`——命中的是哪一個符；
- `path`——哪一個檔；
- `line_sha1`——**穩定 anchor**：該行 strip 後的 SHA-1。⛔ 刻意不用行號——行號在檔案插行
  時靜默失準，而失準不會有任何東西報錯（同 canonical 引用守衛的教訓）。

外加 `occurrences`：該 (path, token, line_sha1) 預期有幾**個 occurrence**（⛔ 不是幾行）。
實際多於宣告 ⇒ 多出來的算**未核准**（fail-closed）；實際少於宣告 ⇒ 那是**過期條目**
（`stale_entries`），列出來但⛔ 不進 rc——AC4 逐字寫死「唯一 pass criterion＝
`unapproved_count==0`」，⛔ 本腳本不得自行多加一個判準。⚠️ 這是**已知缺口**，
⛔ 不當它不存在。

## 什麼結果會讓本腳本的判定不成立（反證條件）

- **負控**：在 temp fixture 放一行含污染符的文字後對它掃，若 `unapproved_count == 0`
  → 判定不成立。（負控**必須跑在 temp fixture 或 worktree 副本**，
  ⛔ 不得把樣本寫進會被合併的樹。）
- **anchor 穩定性**：把被豁免那一行改一個字元後重掃，該行若仍算已核准 → 判定不成立。
- **逐 occurrence**：同一行同一 token 出現兩次而 manifest 只宣告 1，若 `unapproved_count == 0`
  → 判定不成立。
- **自指可見**：自指檔的命中若沒有出現在輸出裡、沒有逐檔逐 token 列計、或沒有進
  `total_hits` → 判定不成立。

上述四條各有一支測試（`cli/tests/test_pollution_check.py`）。

用法：

    python3 scripts/pollution_check.py                 # 對 post-image 掃，未核准命中回 1
    python3 scripts/pollution_check.py --json          # 機讀（含自指命中全表）
    python3 scripts/pollution_check.py --root DIR --files a.md b.md   # 負控用，掃指定檔
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = REPO_ROOT / "scripts" / "pollution-allowlist.json"

#: 守衛基線**釘死字面**，⛔ 不動態算 merge-base——合併之後動態算會變成空集合，
#: 於是這支守衛在最需要它的那一刻剛好什麼都掃不到（規劃階段注意事項 F-規劃-05）。
BASE_SHA = "f656a678e540d4083740e0f30f1214e887e42c04"

#: 自指命中的三個檔。**它們在掃描母體內**——這裡不是排除集，是**分類鍵**。
#: 成員判準逐字取 canonical §6.2 的「**工具或測試檔**本身被自己掃到」：本 checker、
#: 它的 manifest、以及它的測試檔——三者的**用途就是定義或驗證 token 集合本身**。
#: ⛔ 不是「我不想修它」的收容所；⛔ 恰好三項，由 `cli/tests/test_pollution_check.py` 釘死。
SELF_REFERENCE_PATHS = (
    "scripts/pollution_check.py",
    "scripts/pollution-allowlist.json",
    "cli/tests/test_pollution_check.py",
)

#: 決議紀錄 §二 的污染符，**逐字照抄該行的順序**（13 個）。
#: ``(名稱, 正規表達式, 出處)``；名稱即 manifest 的 ``token`` 值域。
POLLUTION_TOKENS: tuple[tuple[str, str, str], ...] = (
    ("claim 事件", r"claim 事件", "決議 §二"),
    ("claim event", r"claim event", "決議 §二"),
    ("events.jsonl", r"events\.jsonl", "決議 §二"),
    ("workflow_ledger", r"workflow_ledger", "決議 §二"),
    ("control-plane", r"control-plane", "決議 §二（新規則文脈）"),
    ("📥Backlog", r"📥Backlog", "決議 §二（新規則文脈）"),
    ("⏳待執行", r"⏳待執行", "決議 §二"),
    ("🚧進行中", r"🚧進行中", "決議 §二"),
    ("🔍待查核", r"🔍待查核", "決議 §二（新規則文脈）"),
    ("部署狀態", r"部署狀態", "決議 §二（作為狀態軸）"),
    ("needs-deploy", r"needs-deploy", "決議 §二"),
    ("spec-dir", r"spec-dir", "決議 §二"),
    ("Discovery lead", r"Discovery lead", "決議 §二（角色表文脈）"),
)

#: AC5 的三個腐爛自述。⛔ 與污染符分開宣告，因為出處不同（AC5 ⛔ 非決議 §二）。
ROT_TOKENS: tuple[tuple[str, str, str], ...] = (
    ("短版", r"短版", "AC5 腐爛自述"),
    ("最後核實", r"最後核實", "AC5 腐爛自述"),
    ("行數自述", r"[0-9]{3,} ?行", "AC5 腐爛自述"),
)

TOKENS: tuple[tuple[str, str, str], ...] = POLLUTION_TOKENS + ROT_TOKENS

_COMPILED = tuple((name, re.compile(pat)) for name, pat, _src in TOKENS)
_ALLOWED_TOKENS = frozenset(name for name, _, _ in TOKENS)


def line_key(text: str) -> str:
    """穩定 anchor：strip 後的 SHA-1。⛔ 刻意不是行號。"""
    return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Hit:
    """一筆命中。``col`` 是該 occurrence 在行內的起始位置——同行同 token 的多次命中靠它區分。"""

    path: str
    lineno: int
    col: int
    token: str
    line_sha1: str
    line: str

    @property
    def is_self_reference(self) -> bool:
        return self.path in SELF_REFERENCE_PATHS

    def render(self) -> str:
        return (f"{self.path}:{self.lineno}:{self.col}: [{self.token}] "
                f"sha1={self.line_sha1[:12]} | {self.line.strip()[:110]}")


def post_image_paths(root: Path, base: str) -> list[str]:
    """本卡改過、且仍存在的檔。

    ⚠️ **未追蹤檔也算 post-image**：``git diff`` 只看得見已追蹤的路徑，而本卡的新增檔在
    ``git add`` 之前對它是隱形的 ⇒ 少了這一段，一個全新的檔可以帶著污染符靜默通過。
    ⛔ 不倚賴「查核時應該都 commit 了」這種慣例。

    ⚠️ **⛔ 不從這裡扣掉自指檔**（R1-003）：它們留在母體內，由 :func:`run` 分類。
    """
    def _git(*argv: str) -> list[str]:
        out = subprocess.run(["git", *argv], cwd=root,
                             capture_output=True, text=True, check=True).stdout
        return [x for x in out.splitlines() if x]

    rels = _git("diff", "--name-only", "--diff-filter=d", base)
    rels += _git("ls-files", "--others", "--exclude-standard")
    seen: list[str] = []
    for rel in rels:
        if rel not in seen and (root / rel).is_file():
            seen.append(rel)
    return seen


def scan_paths(root: Path, rels: list[str]) -> tuple[list[Hit], list[str]]:
    """逐檔逐行逐 token **逐 occurrence** 掃描（``finditer``，⛔ 非 ``search``）。"""
    hits: list[Hit] = []
    unreadable: list[str] = []
    for rel in rels:
        try:
            text = (root / rel).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            unreadable.append(rel)
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            key = line_key(line)
            for name, rx in _COMPILED:
                for m in rx.finditer(line):
                    hits.append(Hit(rel, lineno, m.start(), name, key, line))
    return hits, unreadable


_ENTRY_KEYS = {"path", "token", "line_sha1", "excerpt", "occurrences", "rationale"}


def entry_errors(entry: dict) -> list[str]:
    errs: list[str] = []
    if set(entry) != _ENTRY_KEYS:
        errs.append(f"鍵不等於封閉集合：缺 {sorted(_ENTRY_KEYS - set(entry))} "
                    f"多 {sorted(set(entry) - _ENTRY_KEYS)}")
        return errs
    if not isinstance(entry["path"], str) or not entry["path"]:
        errs.append("path 缺失或非字串")
    if entry["token"] not in _ALLOWED_TOKENS:
        errs.append(f"token 非法：{entry['token']!r}")
    if not isinstance(entry["line_sha1"], str) \
            or not re.fullmatch(r"[0-9a-f]{40}", entry["line_sha1"]):
        errs.append("line_sha1 非 40 位 hex")
    if not isinstance(entry["excerpt"], str) or not entry["excerpt"]:
        errs.append("excerpt 缺失或非字串")
    if not isinstance(entry["occurrences"], int) or isinstance(entry["occurrences"], bool) \
            or entry["occurrences"] < 1:
        errs.append("occurrences 非正整數")
    if not isinstance(entry["rationale"], str) or len(entry["rationale"].strip()) < 10:
        errs.append("rationale 空缺或過短（⛔ 不接受「已核准」這種零資訊理由）")
    if isinstance(entry.get("path"), str) and entry["path"] in SELF_REFERENCE_PATHS:
        # 自指命中是分類⛔ 不是豁免；替它開條目會讓 manifest 不收斂（見模組 docstring）
        errs.append(f"path 屬自指檔 {SELF_REFERENCE_PATHS}——自指命中走分類⛔ 不走 manifest")
    return errs


def load_allowlist(path: Path) -> tuple[dict[tuple[str, str, str], dict], list[dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    approved: dict[tuple[str, str, str], dict] = {}
    invalid: list[dict] = []
    for idx, entry in enumerate(data.get("entries", [])):
        e = entry if isinstance(entry, dict) else {}
        errs = entry_errors(e)
        key = (str(e.get("path")), str(e.get("token")), str(e.get("line_sha1")))
        if not errs and key in approved:
            errs = ["duplicate (path, token, line_sha1)——⛔ 靜默覆蓋"]
        if errs:
            invalid.append({"index": idx, "path": e.get("path", "?"),
                            "token": e.get("token", "?"), "errors": errs})
            continue
        approved[key] = e
    return approved, invalid


def run(root: Path, rels: list[str], allowlist: Path) -> dict:
    hits, unreadable = scan_paths(root, rels)
    approved, invalid = load_allowlist(allowlist)

    self_hits = [h for h in hits if h.is_self_reference]
    other_hits = [h for h in hits if not h.is_self_reference]

    seen: dict[tuple[str, str, str], list[Hit]] = {}
    for h in other_hits:
        seen.setdefault((h.path, h.token, h.line_sha1), []).append(h)

    unapproved: list[Hit] = []
    for key, group in seen.items():
        entry = approved.get(key)
        quota = entry["occurrences"] if entry else 0
        unapproved.extend(group[quota:])          # 超出配額的 occurrence 一律未核准

    stale = [dict(e, actual=len(seen.get((e["path"], e["token"], e["line_sha1"]), [])))
             for key, e in approved.items()
             if len(seen.get(key, [])) < e["occurrences"]]

    # 自指命中的逐檔逐 token 列計（⛔ 不是只列檔名——R1-003 逐字）
    self_tally: dict[str, dict[str, int]] = {}
    for h in self_hits:
        self_tally.setdefault(h.path, {})
        self_tally[h.path][h.token] = self_tally[h.path].get(h.token, 0) + 1

    return {
        "scanned_files": len(rels),
        "token_count": len(TOKENS),
        "pollution_token_count": len(POLLUTION_TOKENS),
        "self_reference_paths": list(SELF_REFERENCE_PATHS),
        "total_hits": len(hits),
        "self_reference": self_hits,
        "self_reference_count": len(self_hits),
        "self_reference_tally": self_tally,
        "unapproved": unapproved,
        "unapproved_count": len(unapproved),
        "approved_entries": len(approved),
        "invalid_entries": invalid,
        "stale_entries": stale,
        "unreadable": unreadable,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="污染符 allowlist-aware checker")
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    ap.add_argument("--base", default=BASE_SHA, help="post-image 的基線（釘死字面）")
    ap.add_argument("--files", nargs="+", help="直接指定要掃的檔（負控用；⛔ 不走 git diff）")
    ap.add_argument("--allowlist", type=Path, default=ALLOWLIST_PATH)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    try:
        rels = args.files if args.files else post_image_paths(args.root, args.base)
        result = run(args.root, rels, args.allowlist)
    except (OSError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        msg = f"{type(exc).__name__}: {exc}"
        # 守衛自身失效＝fail-closed，且證據可讀（⛔ 裸 traceback）
        print(json.dumps({"checker_error": msg}, ensure_ascii=False) if args.json
              else f"[checker-error] {msg}", file=sys.stderr)
        return 2

    if args.json:
        payload = dict(result)
        payload["unapproved"] = [h.__dict__ for h in result["unapproved"]]
        payload["self_reference"] = [h.__dict__ for h in result["self_reference"]]
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        for h in result["unapproved"]:
            print(f"[unapproved] {h.render()}")
        for h in result["self_reference"]:
            print(f"[self-reference] {h.render()}")
        for v in result["invalid_entries"]:
            print(f'[invalid-entry] #{v["index"]} {v["path"]} [{v["token"]}] {v["errors"]}')
        for s in result["stale_entries"]:
            print(f'[stale-entry] {s["path"]} [{s["token"]}] sha1={s["line_sha1"][:12]} '
                  f'宣告 {s["occurrences"]} 實得 {s["actual"]}')
        for u in result["unreadable"]:
            print(f"[unreadable] {u}")
        print(json.dumps({k: result[k] for k in
                          ("scanned_files", "token_count", "total_hits",
                           "self_reference_count", "unapproved_count",
                           "approved_entries")}, ensure_ascii=False))
        print("自指命中逐檔逐 token 列計（在母體內、⛔ 非豁免）："
              + json.dumps(result["self_reference_tally"], ensure_ascii=False))
    # 唯一 pass criterion（AC4 逐字）：unapproved_count == 0
    return 1 if result["unapproved_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
