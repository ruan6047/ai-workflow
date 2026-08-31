#!/usr/bin/env python3
# LIFECYCLE: standing · 常設工具——這就是給你跑的；不要刪
"""規劃文書敘述數字的完備分類掃描器（WF-REDESIGN1 P1-38）。

## 這支腳本回答的問題

「敘述⛔ 不承載現況數字」（需求方 2026-08-31 裁定）生效後，規劃文書裡的每一個
敘述數字必須逐項可歸類為三形態之一：

- **(a) 日期化歷史**——同一行帶 ISO 日期，快照數被釘在時間上；
- **(b) 白名單**——閾值／裁定值、不變量與封閉集合基數（數字本身即設計）；
- **(c) 量法＋artifact 指向**——同一行指向重量指令或已釘 hash 的 artifact。

R14 裁決（P1-38）證明人工終掃是假陰性製造機：只掃阿拉伯數字漏中文數字、
只掃固定 regex 漏「未查」段。本腳本把「有數字但三態皆非」這件事**轉紅**。
唯一判準：``unclassified_count == 0``（外加 inventory 死條目為零——見下）。

## 分類的機械來源

(a) 與 (c) 由行內訊號自動判定（日期 regex／artifact 訊號）。(b) **沒有可靠的
形狀訊號**——「11 個動詞」（可漂移的現況 inventory）與「信封 8 欄」（設計封閉
集合）長得一模一樣，這正是 R14 打穿形狀判定的點。因此 (b) 一律住
``docs/research/drafts/prose-number-inventory.json``：每條＝(路徑, 行文 SHA-1)
→ 分類理由。⛔ 這不是排除清單——條目以**行文 hash 釘住**，該行改一個字元即
脫鉤轉紅，逼重新分類；且每條帶理由可稽核。

- 行文被改／被刪 ⇒ inventory 條目變**死條目**（load-bearing 檢查，轉紅）。
- 新增未分類數字 ⇒ unclassified，轉紅。

## 射程

封閉語料＝P1-38 裁決點名的規劃文書（決議＋brief＋wave-specs＋stage-rules）。
⛔ 不是全 repo 開放集合：本規範管的是「規劃敘述」，程式碼與 canonical 另有
守衛。父卡卡面不是 repo 檔，用 ``--file`` 對匯出檔跑（僅自動分類，資訊性）。

## 偵測（Arabic ＋ 中文數字）

先剝識別子（SHA／日期／P1-NN／issue 號／regex 常數／行首編號…），剩下的
阿拉伯數字、或**帶量詞的中文數字**（「十二條」「六條」——R14 反例的形狀）即為
候選。單獨「一」只在後接量詞時算（「一次授權」「唯一」是慣用語不是量測）。
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
# artifact 指向訊號：hash 字面／artifact 檔／「量法」「artifact 重量／重列」宣告
ARTIFACT_SIGNAL = r"[0-9a-f]{12,64}|baseline-universe|\.json\b|量法|artifact ?重[量列]"

# 剝掉的識別子：不是「量」的數字（引用號、版本、regex、hash、行首編號…）
ID_PATS = [
    r"\b[0-9a-f]{7,40}\b",
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
    r"2020-12",
    r"\bop [0-9a-f]{8}\b",
    r"WF-\d+|WF-REDESIGN\d*",
    r"aiwf#\d+",
    r"cpbl#\d+",
    r"[Pp]hase ?[12]\b",
    r"8×10",
    r"ruan6047",
    r"first:\d+",
    r"shasum -a 256",
    r"AC ?\d+[a-b]?(?:[,，–-]\d+[a-b]?)*",
    r"^\s*\d+[a-b]?[\.、]",
    r"^\s*\|\s*\d+\s*\|",
    r"^\s*- \*?\*?\d+[\.、]",
]

MEASURE_WORDS = "張條筆欄格種類段波卡檔項輪批次個列份步天例處行題值族層面軸房盞問座支套門"
CN_NUM = "[一二三四五六七八九十百千兩]"


def _strip_ids(text: str) -> str:
    text = re.sub(DATE, " ", text)
    for pat in ID_PATS:
        text = re.sub(pat, " ", text, flags=re.M)
    return re.sub(r"`[^`]*`", " ", text)


def _line_key(text: str) -> str:
    return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()


def scan_file(path: Path, inventory: dict[tuple[str, str], dict] | None = None,
              rel: str | None = None) -> list[dict]:
    """回傳該檔每個含候選數字行的分類列。inventory=None 時 (b) 永不命中。"""
    rel = rel if rel is not None else str(path.relative_to(REPO_ROOT))
    rows = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if re.match(r"^#{1,4} ", line):
            continue  # 標題的章節序號不是敘述數字
        stripped = _strip_ids(line)
        arabic = re.findall(r"\d+(?:[.,]\d+)*%?", stripped)
        chinese = re.findall(CN_NUM + "+(?=[" + MEASURE_WORDS + "])", stripped)
        if not (arabic or chinese):
            continue
        if re.search(DATE, line):
            cls, reason = "a", "dated-history"
        elif re.search(ARTIFACT_SIGNAL, line):
            cls, reason = "c", "artifact-pinned"
        else:
            entry = (inventory or {}).get((rel, _line_key(line)))
            if entry is not None:
                cls, reason = "b", entry["reason"]
            else:
                cls, reason = "unclassified", ""
        rows.append({"path": rel, "line": lineno, "tokens": arabic + chinese,
                     "class": cls, "reason": reason, "text": line})
    return rows


def load_inventory(path: Path = INVENTORY_PATH) -> dict[tuple[str, str], dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {(e["path"], e["line_sha1"]): e for e in data["entries"]}


def scan_corpus() -> dict:
    inventory = load_inventory()
    rows: list[dict] = []
    for p in corpus_paths():
        rows.extend(scan_file(p, inventory))
    used = {(r["path"], _line_key(r["text"])) for r in rows if r["class"] == "b"}
    dead = [e for k, e in inventory.items() if k not in used]
    return {
        "rows": rows,
        "unclassified": [r for r in rows if r["class"] == "unclassified"],
        "dead_entries": dead,
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
    if args.json:
        print(json.dumps({k: result[k] for k in ("unclassified", "dead_entries")},
                         ensure_ascii=False, indent=1))
    else:
        for r in result["unclassified"]:
            print(f'[unclassified] {r["path"]}:{r["line"]} {r["tokens"]} | {r["text"][:100]}')
        for e in result["dead_entries"]:
            print(f'[dead-entry] {e["path"]} sha1={e["line_sha1"][:12]} ({e["reason"]})')
        counts = {"total": len(result["rows"]),
                  "unclassified": len(result["unclassified"]),
                  "dead_entries": len(result["dead_entries"])}
        print(json.dumps(counts, ensure_ascii=False))
    red = result["unclassified"] or result["dead_entries"]
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
