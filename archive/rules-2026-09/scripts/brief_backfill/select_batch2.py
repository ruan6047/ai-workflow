#!/usr/bin/env python3
"""唯讀：第二批 20 張的抽樣。⭐ **純隨機，⛔ 不分層構造**。

需求方 2026-08-26 裁定：先導批的分層構造（必含 §6.3 的兩張例證卡、保證 3 張 B 層、
2 張終態）使 57.1% 那個數字不可外推——構造挑中的正是「本來就互相引用」的卡。
第二批改**純隨機**，作為研究輪 n=8 隨機估計（23.1%）的第一次大樣本檢驗。

池 = 缺簡介者 − {aiwf#15（A2 具名排除）, #140（A3 雙居所漂移走特殊路徑）,
                 先導批已回填的 10 張（構造上已不在缺簡介池，此處再顯式扣一次）,
                 無 issue 號的 DraftIssue（amend 路徑不同）}

⛔ 種子寫死並印出；層別（A/B）**事後標註**供報告用，⛔ 不參與抽樣。
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cli" / "src"))

from wf_cli import brief as brief_mod  # noqa: E402
from wf_cli.commands.assign_cmd import TERMINAL_STATUSES  # noqa: E402

#: ⭐ **刻意**：Python 的數字底線分隔符，實際值為 ``202608262``（⛔ 不是打錯的日期，
#: 也不是浮點數）。與先導批的 ``20260826`` 不同，避免抽出同一組。
#:
#: ⛔ **這個種子抽出的樣本事後被證實是「邊稀疏」的離群抽樣，而它仍然是定案的樣本。**
#: 2026-08-26 實測：本種子抽出的 20 張只帶 **10 條** GT-A 邊，而同池重抽 20,000 次的
#: 中位是 **22 條**、抽到 ≤10 的機率僅 **0.0009**；換其他種子（1–10）得 16–28 條。
#: ⭐ 已逐項排除實作缺陷：抽樣可重現（重抽 == ``batch2.txt``）、``random.sample`` 對
#: 排序後清單仍為均勻抽樣、獨立重數與 ``measure_b2.py`` 一致（皆 10）。
#: ⇒ 結論是**運氣**不是 bug。
#:
#: ⛔ **不得為了把分母做大而換種子重抽。** 種子在抽樣前即已宣告並寫死；抽完才因為
#: 「數字不好看」換一個，就是「看著答案調判準」——本 repo 已有同族前例
#: （memory: ``numbers-need-evidence-or-discussion``／``verification-sample-must-be-a-passing-one``）。
#: 交付須照實報告這是一次不幸的抽樣，由需求方裁定要不要另抽一批**新的**（⛔ 而非取代本批）。
SEED = 20260826_2
EXCLUDE_CARD_IDS = {
    "WF-REVIEW-EVENT-MARKER-CONTRACT1",  # aiwf#15，A2 具名排除
    "WF-RESOURCE-HEADING-SUFFIX1-PROBE-ASSIGN1",  # #140，A3 走特殊路徑
}
N = 20


def layer(item: dict) -> str:
    """A／B 層標註。

    ⭐ **刻意：本函式的結果只用於報告，⛔ 完全不參與抽樣。** 讀者會看到它被算出來
    卻沒進 ``rng.sample`` 而以為是漏接——**那是對的，本批就是純隨機**。先導批用層別
    構造樣本（保證 3 張 B 層、2 張終態、必含 §6.3 的兩張例證卡），需求方 2026-08-26
    裁定第二批改純隨機，正是為了讓數字可外推。⛔ 不得把本函式接回選樣邏輯。

    ⚠️ 判準「body 有 ``## Spec``」已在**已知會命中的樣本**上驗過（先導批標為 B 的
    ``UX-GAME-RECAP1``／``MATCHUP-DATA2`` 皆 True，A 層的 ``OPS-CLEANUP-SMOKE1`` 為
    False）。⛔ 不用「有 ``## Spec`` 且無 ``## 核心痛點``」——先導批第一版那樣寫得 0 張，
    真相是 40 張遷移卡都有一個**空的** ``## 核心痛點``。
    """
    body = item.get("body") or ""
    if any(line.strip() == "## Spec" for line in body.splitlines()):
        return "B"
    return "A"


def main() -> int:
    snap = Path(sys.argv[1])
    pilot = set(Path(sys.argv[2]).read_text(encoding="utf-8").split())
    items = json.loads(snap.read_text(encoding="utf-8"))["items"]
    by_id = {(it.get("fields") or {}).get("卡ID"): it for it in items if (it.get("fields") or {}).get("卡ID")}

    missing = {
        cid: it for cid, it in by_id.items() if brief_mod.try_parse_block(it.get("body") or "") is None
    }
    draft_only = {cid for cid, it in missing.items() if not it.get("issue_number")}
    pool = {
        cid: it
        for cid, it in missing.items()
        if cid not in EXCLUDE_CARD_IDS and cid not in pilot and cid not in draft_only
    }

    print(f"snapshot            : {snap}")
    print(f"種子                : random.Random({SEED})")
    print(f"缺簡介總數          : {len(missing)}")
    print(f"  − A2 具名排除      : {sorted(EXCLUDE_CARD_IDS & set(missing))}")
    print(f"  − 先導批已回填     : {len(pilot & set(missing))}（先導批 10 張已有簡介，構造上不在缺簡介池）")
    print(f"  − 無 issue 號      : {sorted(draft_only)}")
    print(f"抽樣池              : {len(pool)}")
    print(f"  池內 A 層 {sum(1 for i in pool.values() if layer(i) == 'A')} / B 層 {sum(1 for i in pool.values() if layer(i) == 'B')}")

    rng = random.Random(SEED)
    picked = sorted(rng.sample(sorted(pool), N))

    print()
    print(f"{'卡ID':<46} {'issue':<14} {'層':<3} {'交付狀態':<10} body字元")
    for cid in picked:
        it = pool[cid]
        repo = (it.get("issue_url") or "").split("/")[4] if it.get("issue_url") else "(draft)"
        alias = {"ai-workflow": "aiwf", "cpbl-analytics": "cpbl"}.get(repo, repo)
        num = f"{alias}#{it.get('issue_number')}"
        st = (it.get("fields") or {}).get("交付狀態") or "-"
        print(f"{cid:<46} {num:<14} {layer(it):<3} {st:<10} {len(it.get('body') or '')}")
    nb = sum(1 for c in picked if layer(pool[c]) == "B")
    nt = sum(1 for c in picked if (pool[c].get("fields") or {}).get("交付狀態") in TERMINAL_STATUSES)
    print()
    print(f"抽出 {len(picked)} 張；事後標註：B 層 {nb} 張、A 層 {len(picked) - nb} 張、終態 {nt} 張")
    print(f"終態列舉（import 自 assign_cmd，⛔ 不手打）: {sorted(TERMINAL_STATUSES)}")

    if len(sys.argv) > 3:
        Path(sys.argv[3]).write_text("\n".join(picked) + "\n", encoding="utf-8")
        print(f"清單已寫入 {sys.argv[3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
