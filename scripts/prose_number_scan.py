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
- claims 逐 occurrence：每筆 (b) 條目帶 ``claims``（occurrence＋token → reason
  ＋rationale），scanner 驗 (occurrence, token) 對集一一相等（R16 行級放行被退
  回；需求方 2026-08-31 裁定乙＝逐 token claims、R17 起綁 occurrence）。
- **唯一判準（單一 predicate，居所＝``RED_KEYS``／``is_red``）**：
  ``unclassified == 0 && dead_entries == 0 && invalid_entries == 0 &&
  claims_mismatch == 0``。``uncovered_claims``／``extra_claims`` 只是 mismatch
  的**診斷投影**⛔ 不構成判準——同 occurrence 重複 claim 可使兩投影皆零而
  mismatch 仍在（R19 反例）。module doc、human summary、corpus 測試三處共用
  此 predicate，⛔ 不得各自另定（R19：三處漂移即本輪 blocking）。

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
    # 生效後的 stage-rules 住 repo 根（W0 搬 conduct 三檔＋收件條件，W2A 搬其餘八份階段檔）。
    # ⚠️ 刻意保留 drafts glob，而它現在**掃到零個檔**——W2A 之後 drafts/stage-rules/ 已空。
    # (a) 刻意如此，⛔ 不是忘了刪。
    # (b) 為什麼：這條 glob 的職責是「drafts/ 下若再出現階段規則草稿，它自動納管」；
    #     刪掉它，下一份草稿就會靜默脫離語料——而脫離語料⛔ 不會有任何東西轉紅。
    # (c) ⛔ 不得由「它今天零命中」推出「它是死條目」——死條目的判準住 EXCLUSIONS
    #     那一套（測試逐項實測），⛔ 不適用於語料 glob；語料要的是開放集合。
    paths += sorted((REPO_ROOT / "stage-rules").glob("*.md"))
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
    # stage-rules 注意事項編號 F-<階段>-NN（W2A 全編號化）——識別子⛔ 非量測。
    # 刻意收窄成「F- ＋ 中日韓字 ＋ - ＋ 數字」，⛔ 不放寬到任意前綴：決議 §三之二 另列的
    # P-／T- 兩層本卡⛔ 未引入，先加樣式就是替一個還不存在的東西開剝除面。
    r"F-[\u4e00-\u9fff]+-\d+",
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
    """closed entry＋claim schema 驗證：鍵**恰等**封閉集合（缺鍵與多鍵同罪）、
    identity 型別與 SHA-1 形狀、reason 屬兩值、rationale 非空、occurrence 非負。"""
    errs = []
    if set(entry) != _ENTRY_KEYS:
        errs.append(f"entry 鍵不等於封閉集合：缺 {sorted(_ENTRY_KEYS - set(entry))} "
                    f"多 {sorted(set(entry) - _ENTRY_KEYS)}")
    if not isinstance(entry.get("path"), str) or not entry.get("path"):
        errs.append("path 缺失或非字串")
    if not isinstance(entry.get("line_sha1"), str) \
            or not re.fullmatch(r"[0-9a-f]{40}", entry.get("line_sha1") or ""):
        errs.append("line_sha1 缺失或非 40 位 hex")
    if not isinstance(entry.get("excerpt"), str) or not entry.get("excerpt"):
        errs.append("excerpt 缺失或非字串")
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
        if not isinstance(c["occurrence"], int) or isinstance(c["occurrence"], bool) \
                or c["occurrence"] < 0:
            errs.append(f"claim[{i}] occurrence 非法")
        if not isinstance(c["token"], str) or not c["token"]:
            errs.append(f"claim[{i}] token 非法")
    return errs


def load_inventory(path: Path | None = None) -> tuple[dict[tuple[str, str], dict], list[dict]]:
    """回傳 (inventory map, load 期 invalid 證據)。缺 identity 的 entry ⛔ 不先索引
    再崩潰（R18：缺 path／line_sha1 曾 KeyError）；重複 (path, line_sha1) fail-closed
    ⛔ 不靜默覆蓋。晚綁定：預設參數在 import 時凍結會讓測試替身打不進。"""
    data = json.loads((path or INVENTORY_PATH).read_text(encoding="utf-8"))
    inventory: dict[tuple[str, str], dict] = {}
    load_errors: list[dict] = []
    for idx, e in enumerate(data.get("entries", [])):
        entry = e if isinstance(e, dict) else {}
        errs = _entry_schema_errors(entry)
        key = (entry.get("path"), entry.get("line_sha1"))
        if not errs and key in inventory:
            errs = ["duplicate (path, line_sha1)——⛔ 靜默覆蓋"]
        if errs:
            load_errors.append({"index": idx, "path": entry.get("path", "?"),
                                "excerpt": str(entry.get("excerpt", ""))[:40],
                                "errors": errs})
            continue
        inventory[key] = entry
    return inventory, load_errors


def scan_corpus() -> dict:
    inventory, load_errors = load_inventory()
    rows: list[dict] = []
    for p in corpus_paths():
        rows.extend(scan_file(p, inventory))
    used = {(r["path"], _line_key(r["text"]))
            for r in rows if r["class"] in ("b", "claims-mismatch")}
    dead = [e for k, e in inventory.items() if k not in used]
    mismatch = []
    invalid = [dict(v, line=None) for v in load_errors]
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


# pass/fail 的單一 predicate——module doc、main、corpus 測試三處共用（R19）
RED_KEYS = ("unclassified", "dead_entries", "invalid_entries", "claims_mismatch")


def is_red(result: dict) -> bool:
    return any(result[k] for k in RED_KEYS)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--file", help="只掃這個檔（自動分類 a/c，資訊性；不套 inventory）")
    ap.add_argument("--json", action="store_true", help="輸出機讀 JSON")
    args = ap.parse_args(argv)

    if args.file:
        try:
            rows = scan_file(Path(args.file), inventory=None, rel=args.file)
        except (OSError, UnicodeDecodeError) as exc:
            msg = f"{type(exc).__name__}: {exc}"
            print(json.dumps({"file_error": msg}, ensure_ascii=False)
                  if args.json else f"[file-error] {msg}")
            return 1
        bad = [r for r in rows if r["class"] == "unclassified"]
        if args.json:
            print(json.dumps({"rows": rows}, ensure_ascii=False, indent=1))
        else:
            for r in bad:
                print(f'{r["path"]}:{r["line"]} {r["tokens"]} | {r["text"][:100]}')
            print(f"unclassified_count={len(bad)}")
        return 1 if bad else 0

    try:
        result = scan_corpus()
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        # inventory 讀不到／壞 JSON＝守衛自身失效，fail-closed 且證據可讀（⛔ 裸 traceback）
        msg = {"inventory_error": f"{type(exc).__name__}: {exc}"}
        print(json.dumps(msg, ensure_ascii=False) if args.json
              else f"[inventory-error] {msg['inventory_error']}")
        return 1
    evidence_keys = ("unclassified", "dead_entries", "invalid_entries",
                     "uncovered_claims", "extra_claims", "claims_mismatch")
    if args.json:
        # 失敗證據契約：RED_KEYS 判準計數＋兩投影＋逐列 mismatch／invalid 證據全數輸出
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
            loc = v.get("line") if v.get("line") is not None else f'entry#{v.get("index", "?")}'
            print(f'[invalid-claims] {v["path"]}:{loc} {v["errors"]}')
        for m in result["claims_mismatch"]:
            print(f'[claims-mismatch] {m["path"]}:{m["line"]} '
                  f'uncovered={m["uncovered"]} extra={m["extra"]}')
        counts = {"total": len(result["rows"])}
        counts.update({k: len(result[k]) for k in RED_KEYS})
        counts.update({k: len(result[k]) for k in ("uncovered_claims", "extra_claims")})
        print(json.dumps(counts, ensure_ascii=False))
    return 1 if is_red(result) else 0


if __name__ == "__main__":
    sys.exit(main())
