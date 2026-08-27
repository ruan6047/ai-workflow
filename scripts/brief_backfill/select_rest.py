#!/usr/bin/env python3
"""唯讀：第三批＝**剩餘全部**（需求方裁定丁案「續做到底」）。

⛔ **本批不抽樣**——前兩批是抽樣（先導批分層構造 10 張、第二批純隨機 20 張），
本批射程是「把池清空」⇒ 沒有種子、沒有 ``rng``。⚠️ 讀者若在找 ``SEED`` 而找不到，
那是對的：⛔ 不得為了與前兩批「一致」而補一個抽樣步驟進來。

池 = 缺簡介者 − {aiwf#15（A2 具名排除）, #140（A3 雙居所漂移走另一路徑）}

⚠️ ``select_batch2.py`` 另外排除了「無 issue 號的 DraftIssue」；本腳本**照樣算出來
並印出**，但⛔ 不預先排除——本批要清空池，DraftIssue 若存在必須被看見而不是被靜默
跳過。實際筆數由輸出決定，⛔ 不在此假設為 0。

層別（A／B）在本批**是派工依據**（B 層必須實讀凍結 spec），⇒ 與 ``select_batch2.py``
的「事後標註、不參與抽樣」**刻意不同**。⛔ 不得把該檔的註解直接套到這裡。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cli" / "src"))

from wf_cli import brief as brief_mod  # noqa: E402
from wf_cli.commands.assign_cmd import TERMINAL_STATUSES  # noqa: E402

EXCLUDE_CARD_IDS = {
    "WF-REVIEW-EVENT-MARKER-CONTRACT1",  # aiwf#15，A2 具名排除（body 有字面 \n）
    "WF-RESOURCE-HEADING-SUFFIX1-PROBE-ASSIGN1",  # #140，A3 走 V6 特殊路徑
}
FROZEN_SHA = "2f52562f575412a0a39b515a4436edd2831b2f65"
CPBL = "/Users/ruanruan/Dev/cpbl-analytics"


def layer(item: dict) -> str:
    """A／B 層。判準「body 有 ``## Spec``」沿用 ``select_batch2.layer``。

    ⚠️ ⛔ 不用「有 ``## Spec`` 且無 ``## 核心痛點``」——先導批第一版那樣寫得 0 張，
    真相是 40 張遷移卡都有一個**空的** ``## 核心痛點``。
    """
    body = item.get("body") or ""
    return "B" if any(ln.strip() == "## Spec" for ln in body.splitlines()) else "A"


def _show(sha: str, card_id: str) -> str | None:
    p = subprocess.run(
        ["git", "-C", CPBL, "show", f"{sha}:docs/tasks/{card_id}.md"],
        capture_output=True, text=True,
    )
    return p.stdout if p.returncode == 0 else None


def spec_text(card_id: str, body: str = "") -> tuple[str | None, str]:
    """回傳 (spec 全文, 取材的 SHA)。優先凍結 SHA，找不到才退回卡面自述的 baseline。

    ⭐ **刻意保留這條退路，⛔ 但它不是「凍結 SHA 不可信」的證據。** A4 逐字說 B 層內容
    在凍結 SHA ``2f52562f`` 的 ``docs/tasks/``「恰 40 檔」——實測該處確實有 40 檔，
    ⛔ 但那 40 檔**不等於** B 層卡的集合：``OPS-CODE-BRANCH-PROTECT1``（cpbl#83）的
    spec 檔在凍結 SHA 已不存在，它的卡面 ``## Spec`` 連結逐字指向**自己的** baseline
    ``18b71cc5``，該處檔案存在（2,478 B）。

    ⇒ 退回規則：**只取卡面 ``## Spec`` 自述的那個 SHA**，⛔ 不掃描全 repo 找同名檔、
    ⛔ 不取最新版——後兩者會把 cutover 之後的修改當成 spec，那正是「凍結」要防的。

    ⛔ **不得由本函式推出「B 層可以不讀 spec」**：退回路徑仍是實讀凍結內容，只是換了
    一個同樣被釘死的 SHA。找不到任何一版時回 ``(None, "")``，由呼叫端顯式處理。
    """
    s = _show(FROZEN_SHA, card_id)
    if s is not None:
        return s, FROZEN_SHA
    m = re.search(r"baseline SHA `([0-9a-f]{40})`", body or "")
    if m:
        s = _show(m.group(1), card_id)
        if s is not None:
            return s, m.group(1)
    return None, ""


def main() -> int:
    snap = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    items = json.loads(snap.read_text(encoding="utf-8"))["items"]
    by_id = {(it.get("fields") or {}).get("卡ID"): it for it in items if (it.get("fields") or {}).get("卡ID")}

    missing = {cid: it for cid, it in by_id.items() if brief_mod.try_parse_block(it.get("body") or "") is None}
    pool = {cid: it for cid, it in missing.items() if cid not in EXCLUDE_CARD_IDS}
    draft_only = sorted(cid for cid, it in pool.items() if not it.get("issue_number"))

    a_ids = sorted(cid for cid, it in pool.items() if layer(it) == "A")
    b_ids = sorted(cid for cid, it in pool.items() if layer(it) == "B")

    print(f"snapshot        : {snap}")
    print(f"母體 item 總數  : {len(items)}")
    print(f"缺簡介          : {len(missing)}")
    print(f"  − A2/A3 排除  : {sorted(EXCLUDE_CARD_IDS & set(missing))}")
    print(f"本批池          : {len(pool)}　（A 層 {len(a_ids)} ／ B 層 {len(b_ids)}）")
    print(f"無 issue 號(Draft): {len(draft_only)} {draft_only}")
    print(f"終態列舉(import) : {sorted(TERMINAL_STATUSES)}")
    n_term = sum(1 for c in pool if (pool[c].get("fields") or {}).get("交付狀態") in TERMINAL_STATUSES)
    print(f"池中終態卡      : {n_term}")

    # B 層凍結 spec 可讀性逐張查（⛔ 派工前就要知道哪幾張讀不到，不能到草擬時才發現）
    b_ok, b_missing_spec = [], []
    for cid in b_ids:
        txt, sha = spec_text(cid, pool[cid].get("body") or "")
        (b_ok if txt is not None else b_missing_spec).append(f"{cid}@{sha[:8]}" if txt is not None else cid)
    print(f"B 層凍結 spec 可讀 : {len(b_ok)}／{len(b_ids)}")
    if b_missing_spec:
        print(f"  ⛔ 讀不到 spec : {b_missing_spec}")

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "rest_all.txt").write_text("\n".join(sorted(pool)) + "\n", encoding="utf-8")
    (out_dir / "rest_a.txt").write_text("\n".join(a_ids) + "\n", encoding="utf-8")
    (out_dir / "rest_b.txt").write_text("\n".join(b_ids) + "\n", encoding="utf-8")

    # 派工素材：每張一個檔。A 層＝Issue body；B 層＝Issue body ＋ 凍結 spec 全文。
    mat = out_dir / "material"
    mat.mkdir(exist_ok=True)
    for cid, it in pool.items():
        parts = [f"# 卡ID: {cid}", f"# layer: {layer(it)}",
                 f"# issue: {(it.get('issue_url') or '').split('/')[4] if it.get('issue_url') else '(draft)'}#{it.get('issue_number')}",
                 f"# 交付狀態: {(it.get('fields') or {}).get('交付狀態')}",
                 "", "===== ISSUE BODY =====", it.get("body") or ""]
        if layer(it) == "B":
            s, sha = spec_text(cid, it.get("body") or "")
            parts += ["", f"===== 凍結 SPEC ({sha[:8] or '找不到'}:docs/tasks/{cid}.md) =====",
                      s if s is not None else "(⛔ 讀不到)"]
        (mat / f"{cid}.txt").write_text("\n".join(parts), encoding="utf-8")
    print(f"\n派工素材 → {mat}（{len(pool)} 檔）")
    print(f"清單 → {out_dir}/rest_all.txt, rest_a.txt, rest_b.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
