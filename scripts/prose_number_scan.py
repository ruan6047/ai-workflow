#!/usr/bin/env python3
# LIFECYCLE: standing · 常設工具——這就是給你跑的；不要刪
"""規劃文書敘述數字的完備分類掃描器（WF-REDESIGN1 P1-38）。

## 這支腳本回答的問題

「敘述⛔ 不承載現況數字」（需求方 2026-08-31 裁定）生效後，規劃文書裡的每一個
敘述數字必須逐項可歸類為三形態之一：

- **(a) 日期化歷史**——同一行帶 ISO 日期，快照數被釘在時間上；
- **(b) 白名單**——僅兩類：閾值／裁定值、不變量／設計封閉集合基數
  （pm-conduct「量測與轉述紀律」段的封閉定義；⛔ 本工具不得自行增類——R15
  曾以 environment-fact 等三個自造類擴張白名單，被裁決退回）；
- **(c) 量法＋artifact 指向**——行內有明文重量契約（「量法」「artifact 重量／
  重列」），或 artifact 檔指向**與** hash 字面同時在場。⛔ 單獨出現 `.json`
  路徑或一段 hex 不算（R15 反例：「inventory.json 目前有 44 張卡」曾被誤判綠）。

R14/R15 兩輪證明假陰性是這裡的主要敵人：R14 漏中文數字與未查段；R15 漏
inline code 內的數字、數字 heading、7 位以上純十進位（被 SHA regex 吃掉）、
量詞「人」。修法⛔ 不是再加 broad regex，而是：偵測面**縮小剝除範圍**（fenced
code block 整塊排除＝Markdown tokenization；inline code 內容保留掃描；heading
只剝行首章節序號後照掃；SHA 樣式必須含至少一個 a-f），並以 detector-escape
suite（成對測試：真識別子剝除／同形量測必響）釘住每一條剝除規則。

## 分類的機械來源

(a) 與 (c) 由行內訊號自動判定。(b) **沒有可靠的形狀訊號**——「11 個動詞」
（可漂移的現況 inventory）與「信封 8 欄」（設計封閉集合）長得一模一樣。因此
(b) 一律住 ``docs/research/drafts/prose-number-inventory.json``：每條＝
(路徑, 行文 SHA-1) → reason（僅 threshold-ruling／design-closed-set 兩值，
測試對 pm-conduct 的封閉定義釘死，⛔ 不以 inventory 自宣告的集合自證）＋
**line-specific rationale**（該行的數字為何屬白名單，逐筆可稽核）。
⛔ 這不是排除清單——條目以行文 hash 釘住，該行改一個字元即脫鉤轉紅。

- 行文被改／被刪 ⇒ inventory 條目變**死條目**（load-bearing 檢查，轉紅）。
- 新增未分類數字 ⇒ unclassified，轉紅。
- claims 逐 token：每筆 (b) 條目帶 ``claims``（token → reason＋rationale），
  scanner 驗偵測 token multiset 與 claims **一一相等**——漏一（uncovered）、
  多一（extra）、同 token 不同語意未分開，均轉紅（R16：行級單一 rationale
  放行整列 tokens 被裁決退回；需求方 2026-08-31 裁定乙＝逐 token claims）。
- 唯一判準（四項全零）：``unclassified == 0 && dead_entries == 0 &&
  uncovered_claims == 0 && extra_claims == 0``。

## 射程

封閉語料＝P1-38 裁決點名的規劃文書（決議＋brief＋wave-specs＋stage-rules）。
⛔ 不是全 repo 開放集合：本規範管的是「規劃敘述」，程式碼與 canonical 另有
守衛。父卡卡面不是 repo 檔，用 ``--file`` 對匯出檔跑（僅自動分類，資訊性）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = REPO_ROOT / "docs" / "research" / "drafts" / "prose-number-inventory.json"

# pm-conduct (b) 的封閉定義；測試釘住這個集合（⛔ 不讀 inventory 自宣告）
ALLOWED_B_REASONS = frozenset({"threshold-ruling", "design-closed-set"})

CORPUS = [
    "docs/research/WORKFLOW-REDESIGN-2026-08-30.md",
    "docs/research/drafts/WORKFLOW-REDESIGN-INITIATIVE-BRIEF.md",
]


def corpus_paths() -> list[Path]:
    paths = [REPO_ROOT / p for p in CORPUS]
    paths += sorted((REPO_ROOT / "docs/research/drafts/wave-specs").glob("*.md"))
    paths += sorted((REPO_ROOT / "docs/research/drafts/stage-rules").glob("*.md"))
    return paths


DATE = r"20\d\d-\d\d(?:-\d\d)?"

# (c) 訊號：明文重量契約，或 artifact 檔指向＋hash 字面同行並存
_MEASURE_CONTRACT = re.compile(r"量法|artifact ?重[量列]")
_ARTIFACT_FILE = re.compile(r"[\w-]+\.json\b|baseline-universe")
_HASH_LITERAL = re.compile(r"\b(?=[0-9a-f]*[a-f])[0-9a-f]{12,64}\b")


def _has_artifact_signal(line: str) -> bool:
    if _MEASURE_CONTRACT.search(line):
        return True
    return bool(_ARTIFACT_FILE.search(line) and _HASH_LITERAL.search(line))


# 剝掉的識別子：不是「量」的數字（引用號、版本、regex 錨、hash、行首編號…）。
# ⚠️ 每一條都要在 detector-escape suite 有成對測試：真識別子剝除＝不產列；
# 相鄰同形量測＝必產列。SHA 樣式要求至少含一個 a-f——純十進位長數是「量」。
ID_PATS = [
    r"\b(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b",
    r"P1-\d+",
    r"§[\d.．]+(?:\.\d+)*",
    r"§[一二三四五六七八九十]+(?:之[一二三四五六七八九十]+)?",
    r"#\d+",
    r"issuecomment-\d+",
    r"\bW\d[AB]?′?\b",
    r"\bR\d+(?:–R?\d+)?\b",
    r"\bT\d(?:[/+‒–-]T?\d)*\b",
    r"\bL\d(?:[/‒–-]L?\d)*\b",
    r"\bv\d+\b",
    r"canonical-v1|event-v1|inv-v1",
    r"\b\d{3}_[a-z_]+\b",
    r"UUIDv?\d?",
    r"sha-?256|SHA-256",
    r"128-bit",
    r"issues/\d+",
    r"PR ?#?\d+",
    r"\bQ\d\b",
    r"\d{2}:\d{2}",
    r"\+08:00",
    r"\b0\.\d+\.\d+\b",
    r"\bop [0-9a-f]{8}\b",
    r"WF-\d+|WF-REDESIGN\d*",
    r"aiwf#\d+",
    r"cpbl#\d+",
    r"[Pp]hase ?[12]\b",
    r"ruan6047",
    r"first:\d+",
    r"shasum -a 256",
    r"AC ?\d+[a-b]?(?:[,，–-]\d+[a-b]?)*",
    r"^\s*\d+[a-b]?[\.、]",
    r"^\s*\|\s*\d+\s*\|",
    r"^\s*- \*?\*?\d+[\.、]",
    # regex 字元類量詞（如行數自述 token 的樣式本體）——機器形狀非量測
    r"\[\d(?:-\d)?\]\{\d+,?\d*\}( ?\?)?",
    # API／機讀識別子與結構引用（各有 detector-escape 成對測試）
    r"[A-Za-z_]+V2[A-Za-z_]*",
    r"[\w/.-]+\.(?:py|md|sql|sh|yml|json|jsonl):\d+",
    r"\bA\d\b",
    r"條件 ?\d",
    r"波 ?\d",
    r"rows? ?\d+(?:、\d+)*",
    r"replacement_rows: ?\[[\d, ]*\]",
    r"spec_version: ?\d+",
    r"\brc ?= ?\d+",
    r"WF_[A-Z_]+\d*",
]

MEASURE_WORDS = (
    "張條筆欄格種類段波卡檔項輪批次個列份步天例處行題值族層面軸房盞問座支套門人位名"
)
CN_NUM = "[一二三四五六七八九十百千兩]"

# heading 行首的章節序號（「## 八 ·」「### 3.」）——剝掉序號後其餘照掃，
# ⛔ 不整行跳過（R15 反例：「## 目前有 43 張卡」曾整行漏掃）
_HEADING_ORDINAL = re.compile(
    r"^(#{1,4}) (?:[一二三四五六七八九十]+(?:之[一二三四五六七八九十]+)? ?[·．]?|\d+[\.、]? ?)"
)


def _strip_ids(text: str) -> str:
    text = re.sub(DATE, " ", text)
    for pat in ID_PATS:
        text = re.sub(pat, " ", text, flags=re.M)
    return text


def _line_key(text: str) -> str:
    return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()


_FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def _prose_lines(text: str):
    """逐行產出 (行號, 行文)，整塊跳過 fenced code block。

    fence 狀態機依 CommonMark 子集三條規則（R16 反例：單一 boolean 翻轉會被
    「四反引號外層＋三反引號內文」的合法 Markdown 打穿）：
    - opener 記住**字元種類與長度**（```` 與 ``` 是不同 opener）；
    - closer 須同字元、長度**不短於** opener、且整行除尾端空白外只有 fence
      （帶 info string 的行不是 closer）；反引號與波浪號**不互關**；
    - EOF 隱式關閉。
    """
    fence_char: str | None = None
    fence_len = 0
    for lineno, line in enumerate(text.splitlines(), 1):
        m = _FENCE_OPEN.match(line)
        if fence_char is None:
            if m:
                fence_char = m.group(1)[0]
                fence_len = len(m.group(1))
                continue
            yield lineno, line
        else:
            if (m and m.group(1)[0] == fence_char
                    and len(m.group(1)) >= fence_len
                    and m.group(2).strip() == ""):
                fence_char = None
                fence_len = 0
            continue


def scan_file(path: Path, inventory: dict[tuple[str, str], dict] | None = None,
              rel: str | None = None) -> list[dict]:
    """回傳該檔每個含候選數字行的分類列。inventory=None 時 (b) 永不命中。"""
    rel = rel if rel is not None else str(path.relative_to(REPO_ROOT))
    rows = []
    for lineno, line in _prose_lines(path.read_text(encoding="utf-8")):
        scannable = _HEADING_ORDINAL.sub(r"\1 ", line, count=1)
        stripped = _strip_ids(scannable)
        arabic = re.findall(r"\d+(?:[.,]\d+)*%?", stripped)
        chinese = re.findall(CN_NUM + "+(?=[" + MEASURE_WORDS + "])", stripped)
        if not (arabic or chinese):
            continue
        if re.search(DATE, line):
            cls, reason = "a", "dated-history"
        elif _has_artifact_signal(line):
            cls, reason = "c", "artifact-pinned"
        else:
            entry = (inventory or {}).get((rel, _line_key(line)))
            if entry is None:
                cls, reason = "unclassified", ""
            elif _entry_schema_errors(entry):
                # scanner 自身驗 closed claim schema——⛔ 不倚賴 pytest 對當下檔案
                cls, reason = "invalid-claims", ""
            else:
                # 逐 occurrence 綁定：第 i 個偵測必須恰有一個 claim(occurrence=i, token=t_i)
                detected = arabic + chinese
                pairs = {(c["occurrence"], c["token"]) for c in entry["claims"]}
                want = {(i, t) for i, t in enumerate(detected)}
                if pairs == want and len(entry["claims"]) == len(detected):
                    cls, reason = "b", "claims"
                else:
                    cls, reason = "claims-mismatch", ""
        rows.append({"path": rel, "line": lineno, "tokens": arabic + chinese,
                     "class": cls, "reason": reason, "text": line})
    return rows


_ENTRY_KEYS = {"path", "line_sha1", "excerpt", "claims"}
_CLAIM_KEYS = {"token", "occurrence", "reason", "rationale"}


def _entry_schema_errors(entry: dict) -> list[str]:
    """closed claim schema 驗證：鍵封閉、reason 屬兩值、rationale 非空、occurrence 非負。"""
    errs = []
    extra = set(entry) - _ENTRY_KEYS
    if extra:
        errs.append(f"entry 鍵超出封閉集合：{sorted(extra)}")
    claims = entry.get("claims")
    if not isinstance(claims, list) or not claims:
        errs.append("claims 缺失或為空")
        return errs
    for i, c in enumerate(claims):
        if not isinstance(c, dict) or set(c) != _CLAIM_KEYS:
            errs.append(f"claim[{i}] 鍵不等於封閉集合 {sorted(_CLAIM_KEYS)}")
            continue
        if c["reason"] not in ALLOWED_B_REASONS:
            errs.append(f"claim[{i}] reason 非法：{c['reason']!r}")
        if not isinstance(c["rationale"], str) or not c["rationale"].strip() \
                or c["rationale"].strip() == c["reason"]:
            errs.append(f"claim[{i}] rationale 空缺或自證")
        if not isinstance(c["occurrence"], int) or c["occurrence"] < 0:
            errs.append(f"claim[{i}] occurrence 非法")
        if not isinstance(c["token"], str) or not c["token"]:
            errs.append(f"claim[{i}] token 非法")
    return errs


def load_inventory(path: Path | None = None) -> dict[tuple[str, str], dict]:
    # 晚綁定：預設參數在 import 時凍結會讓測試替身打不進（monkeypatch 失效）
    data = json.loads((path or INVENTORY_PATH).read_text(encoding="utf-8"))
    return {(e["path"], e["line_sha1"]): e for e in data["entries"]}


def scan_corpus() -> dict:
    inventory = load_inventory()
    rows: list[dict] = []
    for p in corpus_paths():
        rows.extend(scan_file(p, inventory))
    used = {(r["path"], _line_key(r["text"]))
            for r in rows if r["class"] in ("b", "claims-mismatch")}
    dead = [e for k, e in inventory.items() if k not in used]
    mismatch = []
    invalid = []
    for r in rows:
        entry = inventory.get((r["path"], _line_key(r["text"])))
        if r["class"] == "invalid-claims":
            invalid.append({"path": r["path"], "line": r["line"],
                            "errors": _entry_schema_errors(entry or {}),
                            "text": r["text"]})
        if r["class"] != "claims-mismatch" or entry is None:
            continue
        want = [(i, t) for i, t in enumerate(r["tokens"])]
        got = [(c["occurrence"], c["token"]) for c in entry["claims"]]
        uncovered = [p for p in want if p not in got]
        extra = [p for p in got if p not in want]
        mismatch.append({"path": r["path"], "line": r["line"],
                         "uncovered": uncovered, "extra": extra,
                         "text": r["text"]})
    return {
        "rows": rows,
        "unclassified": [r for r in rows if r["class"] == "unclassified"],
        "dead_entries": dead,
        "invalid_entries": invalid,
        "uncovered_claims": [m for m in mismatch if m["uncovered"]],
        "extra_claims": [m for m in mismatch if m["extra"]],
        "claims_mismatch": mismatch,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--file", help="只掃這個檔（自動分類 a/c，資訊性；不套 inventory）")
    ap.add_argument("--json", action="store_true", help="輸出機讀 JSON")
    args = ap.parse_args(argv)

    if args.file:
        rows = scan_file(Path(args.file), inventory=None, rel=args.file)
        bad = [r for r in rows if r["class"] == "unclassified"]
        if args.json:
            print(json.dumps({"rows": rows}, ensure_ascii=False, indent=1))
        else:
            for r in bad:
                print(f'{r["path"]}:{r["line"]} {r["tokens"]} | {r["text"][:100]}')
            print(f"unclassified_count={len(bad)}")
        return 1 if bad else 0

    result = scan_corpus()
    evidence_keys = ("unclassified", "dead_entries", "invalid_entries",
                     "uncovered_claims", "extra_claims", "claims_mismatch")
    if args.json:
        # 失敗證據契約：四項計數＋逐列 mismatch／invalid 證據全數輸出
        payload = {k: result[k] for k in evidence_keys}
        payload["counts"] = {k: len(result[k]) for k in evidence_keys}
        payload["total"] = len(result["rows"])
        print(json.dumps(payload, ensure_ascii=False, indent=1, default=str))
    else:
        for r in result["unclassified"]:
            print(f'[unclassified] {r["path"]}:{r["line"]} {r["tokens"]} | {r["text"][:100]}')
        for e in result["dead_entries"]:
            print(f'[dead-entry] {e["path"]} sha1={e["line_sha1"][:12]} '
                  f'({e.get("excerpt", "")[:40]})')
        for v in result["invalid_entries"]:
            print(f'[invalid-claims] {v["path"]}:{v["line"]} {v["errors"]}')
        for m in result["claims_mismatch"]:
            print(f'[claims-mismatch] {m["path"]}:{m["line"]} '
                  f'uncovered={m["uncovered"]} extra={m["extra"]}')
        counts = {"total": len(result["rows"]),
                  "unclassified": len(result["unclassified"]),
                  "dead_entries": len(result["dead_entries"]),
                  "invalid_entries": len(result["invalid_entries"]),
                  "uncovered_claims": len(result["uncovered_claims"]),
                  "extra_claims": len(result["extra_claims"])}
        print(json.dumps(counts, ensure_ascii=False))
    red = (result["unclassified"] or result["dead_entries"]
           or result["invalid_entries"] or result["claims_mismatch"])
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
