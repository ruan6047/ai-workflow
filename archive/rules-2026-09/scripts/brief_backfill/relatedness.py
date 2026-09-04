#!/usr/bin/env python3
"""唯讀：V2 的 ground truth、資源宣告基準、簡介覆蓋率。

**Ground truth**（V2 逐字）：卡 A 的 ``## Log`` **之前**提到卡 B 的卡 ID ⇒ (A, B) 語意相關。
⚠️ 卡 ID 有前綴包含關係（``WF-CARD-BODY-BUDGET1`` ⊂ ``WF-CARD-BODY-BUDGET1-PROBE-DRAFT1``）
⇒ 比對須加右界（下一字元不得為 ``[A-Za-z0-9-]``），否則長 ID 的每次出現都會被算成短 ID 也被提到。

**資源宣告基準**：同一組 (A, B)，兩卡的 ``resources`` 是否有**完全相同**的字串
（``resources.find_conflicts`` 的判準：⛔ 不做路徑前綴模糊比對）。

**簡介覆蓋**：A 的簡介文字是否提到 B。兩種判準都算並分別報：
  strict = 卡 ID 字面（與 ground truth 同一把尺）
  ext    = 卡 ID 或 issue 參照（``aiwf#N``／``cpbl#N``／同 repo 的裸 ``#N``）

⛔ 索引鍵一律 ``card_id``；Project #4 橫跨兩 repo，issue 號 55 個重複。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cli" / "src"))

from wf_cli import brief as brief_mod  # noqa: E402
from wf_cli import resources as res_mod  # noqa: E402

_REPO_ALIAS = {"ai-workflow": "aiwf", "cpbl-analytics": "cpbl"}


def repo_of(item: dict) -> str | None:
    url = item.get("issue_url") or ""
    parts = url.split("/")
    return parts[4] if len(parts) > 4 else None


def head_of(body: str, *, drop_brief: bool = True) -> str:
    """``## Log`` 之前的內文，⭐ **預設剔除 ``## 簡介`` 區段**。

    ⛔ 不自寫 markdown 解析——沿用 ``resources._split_at_log``。

    ⭐ **為什麼要剔除簡介**（2026-08-26 先導批當場抓到的循環量測）：簡介區塊就住在
    ``## Log`` **之前**，⇒ 回填後，簡介裡指名的每一張卡都會被 GT builder 當成一條
    **新的 ground truth 邊**，而那條邊必然被簡介自己命中。實測：先導批回填後
    GT 由 21 組變 24 組、命中由 12 變 15，**增量三條逐一對得上簡介新指名的三個對象**
    （``WF-CARD-BRIEF-BACKFILL1``／``INGEST-POSTGAME-FINALIZE1``／``OPS-REMOTE-ROUTE1``）
    ⇒ 覆蓋率被自己抬高了 5.4 個百分點。⛔ 那是「看著答案建表再量涵蓋率」。
    """
    try:
        head, _ = res_mod._split_at_log(body or "")
    except res_mod.ResourceDeclarationError:
        # Log 標題重複／排版破壞：退回「第一個 `## Log` 之前」的保守切法
        marker = "\n## Log"
        idx = (body or "").find(marker)
        head = body if idx < 0 else body[:idx]
    if not drop_brief:
        return head
    lines = head.splitlines()
    starts = [i for i, ln in enumerate(lines) if ln.strip() == brief_mod.SECTION_HEADING]
    if not starts:
        return head
    s = starts[0]
    e = next((j for j in range(s + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
    return "\n".join(lines[:s] + lines[e:])


def mentions(text: str, card_id: str) -> bool:
    """card_id 是否以「獨立 token」出現在 text（右界防前綴誤命中）。"""
    for m in re.finditer(re.escape(card_id), text):
        nxt = text[m.end() : m.end() + 1]
        if not re.match(r"[A-Za-z0-9-]", nxt):
            return True
    return False


def issue_refs(text: str, self_repo: str | None) -> set[tuple[str, int]]:
    """抽出 (repo_alias, issue_number)。裸 ``#N`` 歸屬 A 自己所在的 repo。"""
    out: set[tuple[str, int]] = set()
    for m in re.finditer(r"\b(aiwf|cpbl)#(\d+)", text):
        out.add((m.group(1), int(m.group(2))))
    for m in re.finditer(r"(?<![\w#/-])#(\d+)", text):
        alias = _REPO_ALIAS.get(self_repo or "", None)
        if alias:
            out.add((alias, int(m.group(1))))
    return out


def build(items: list[dict]) -> dict:
    by_id: dict[str, dict] = {}
    for it in items:
        cid = (it.get("fields") or {}).get("卡ID")
        if cid:
            by_id[cid] = it
    ident: dict[tuple[str, int], str] = {}
    for cid, it in by_id.items():
        alias = _REPO_ALIAS.get(repo_of(it) or "", None)
        if alias and it.get("issue_number"):
            ident[(alias, int(it["issue_number"]))] = cid

    pairs: list[tuple[str, str]] = []
    for a_id, a in by_id.items():
        head = head_of(a.get("body") or "")
        for b_id in by_id:
            if b_id == a_id:
                continue
            if mentions(head, b_id):
                pairs.append((a_id, b_id))

    decls = {cid: res_mod.try_parse_block(it.get("body") or "") for cid, it in by_id.items()}

    def res_hit(a_id: str, b_id: str) -> bool:
        da, db = decls.get(a_id), decls.get(b_id)
        if da is None or db is None:
            return False
        return bool(set(da.resources) & set(db.resources))

    def brief_hit(a_id: str, b_id: str, mode: str) -> bool:
        a = by_id[a_id]
        parsed = brief_mod.try_parse_block(a.get("body") or "")
        if parsed is None:
            return False
        if mentions(parsed.text, b_id):
            return True
        if mode == "strict":
            return False
        refs = issue_refs(parsed.text, repo_of(a))
        return any(ident.get(r) == b_id for r in refs)

    return {
        "by_id": by_id,
        "pairs": pairs,
        "res_hit": res_hit,
        "brief_hit": brief_hit,
        "decls": decls,
    }


def pct(n: int, d: int) -> str:
    return f"{100.0 * n / d:.1f}%" if d else "n/a (0 分母)"


def report(items: list[dict], subset: set[str] | None, label: str) -> None:
    b = build(items)
    pairs = b["pairs"]
    sel = [p for p in pairs if subset is None or p[0] in subset]
    r_hit = sum(1 for p in sel if b["res_hit"](*p))
    s_hit = sum(1 for p in sel if b["brief_hit"](*p, "strict"))
    e_hit = sum(1 for p in sel if b["brief_hit"](*p, "ext"))
    print(f"── {label} ──")
    print(f"  母體（ground truth 組數）: {len(sel)}（全母體 {len(pairs)} 組）")
    print(f"  來源卡數                 : {len({p[0] for p in sel})}")
    print(f"  資源宣告抓回             : {r_hit} / {len(sel)} = {pct(r_hit, len(sel))}")
    print(f"  簡介抓回 (strict 卡ID)   : {s_hit} / {len(sel)} = {pct(s_hit, len(sel))}")
    print(f"  簡介抓回 (ext 含 issue號) : {e_hit} / {len(sel)} = {pct(e_hit, len(sel))}")
    print()


def main() -> int:
    snap = Path(sys.argv[1])
    items = json.loads(snap.read_text(encoding="utf-8"))["items"]
    print(f"snapshot: {snap}\n")
    report(items, None, "全母體基準")
    have = {
        cid
        for cid, it in build(items)["by_id"].items()
        if brief_mod.try_parse_block(it.get("body") or "") is not None
    }
    report(items, have, f"僅「已有簡介」的 {len(have)} 張為來源")
    for extra in sys.argv[2:]:
        ids = set(Path(extra).read_text(encoding="utf-8").split())
        report(items, ids, f"僅清單 {Path(extra).name} 的 {len(ids)} 張為來源")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
