#!/usr/bin/env python3
"""A6 的**封閉集合**複驗。⭐ 與 ``guard.a6_named_targets``（開放集合正則）並列，⛔ 不取代它。

**為什麼要有這一支**：``guard.a6_named_targets`` 用正則抓「看起來像卡 ID 的 token」
（``\\b[A-Z][A-Z0-9]+(?:-[A-Z0-9]+){1,}\\b``）。2026-08-26 第三批的草擬代理各自獨立
回報同一件事：該形狀會把 **``UTF-8``／``NO-GO``／``R4-002``／``R12-004``** 這類
縮寫詞與 finding id 當成卡 ID 命中 ⇒ **A6 的通過數會被高估**。

⇒ 本模組把「卡 ID」由**開放集合（正則）換成封閉集合（真實存在的卡 ID）**，
issue 號同理驗證 ``(repo, number)`` 真的存在。這正是 memory ``shape-change-not-instance-fix``
記的那條跳出法：⛔ 不是再補一條排除規則（``UTF-8`` 修掉了還有下一個），
而是換成逐字比對真實母體。

⚠️⚠️ **本模組第一版的封閉集合取錯母體，已更正——這段留著當警示。**

第一版把「真實存在的卡 ID」定義為 **Project #4 快照的 204 張**，於是報出 5 張
「正則假陽性」：``DEV-CI-SCORELESS-DB-SKIP1``／``DEV-TRAILER-GUARD-SCOPE1``／
``WF-22-CLI1``／``ML-SIM1``／``UX-MATCHUP1``／``UX-MATCHUP2``／``UX-TEAM-SPLIT-SCOPE1``。
⛔ **那 5 張全是我錯**：逐一查證後，這些卡 ID 各有 **19–43 個 commit** 的歷史，
且逐字出現在 ``docs/archive/TASKS_ARCHIVE.md``／``docs/CONTROL_PLANE_CONTRACT.md``／
``docs/PRODUCT_UX_BLUEPRINT.md``／``archive/tasks/WF-22-CLI1.md`` ⇒ 它們是**真卡**，
只是 cutover 前的卡、不在現行看板上。「不在 Project #4」⛔ **不等於**「不存在」。

同一版還把 ``scripts/review_gate_preflight.py`` 判為假陽性，理由是「repo 裡沒這個檔」。
⛔ 也是我錯：那則簡介逐字寫的是「**不得建立**被明文否決的該檔」——**它不存在正是重點**。
⇒ A6 要的是「有沒有指向卡外的**具名**對象」，⛔ **不是**「那個對象現在存不存在」。

⇒ 兩處更正：(a) 卡 ID 封閉集合改為「Project #4 ∪ 兩 repo 的卡登記文件」；
(b) 檔路徑**只驗形狀不驗存在**。⭐ 這正是 memory ``refute-on-the-claims-own-population``
記的形狀——我拿另一個母體去否定既有結果，而「我發現既有結果有錯」獎賞感最高、
也最該先懷疑自己。

⛔ **不得由「strict 通過數較低」推出「回填品質較差」**：兩者量的是不同的東西——
loose 量「有沒有寫出像具名對象的東西」，strict 量「那個名字是不是這個專案真有的名字」。

⛔ **A6 仍是篩不是閘**：本腳本輸出逐張理由，⛔ 不回非零 rc、⛔ 不剔除任何卡。

第三批的 5 張不通過，人工逐張查證後的歸因（⛔ **刻意不改 pattern 讓數字變好看**）
------------------------------------------------------------------------------
卡面 A6 的判準是語意的——「指向**卡外的具名對象**（卡 ID／issue 號／檔路徑／``§`` 節號／
**表名**／API 路由）」；``guard.a6_named_targets`` 的正則只是它的一個實作，且**不完整**
（``表名`` 一類根本沒實作）。2026-08-26 逐張讀非射程段落後：

* **4 張是 pattern 涵蓋不到，⛔ 不是簡介沒寫具名對象**
  - ``OPS-CPBL-MERGE-GATE1``／``OPS-MIG1-CLAIMS-BACKFILL1``／``WF-AMEND-RESOURCE-CONFLICT1``
    各自逐字寫了 ``ai-workflow#48``／``ai-workflow#31``／``ai-workflow#94``。正則只認
    ``aiwf#N``／``cpbl#N``／裸 ``#N``，而裸 ``#N`` 的左界 ``(?<![\\w#/-])`` 正好被 ``ai-workflow``
    的 ``w`` 擋掉 ⇒ **全 repo 名寫法一個都抓不到**。
  - ``DOC-LIVELOG-SEMANTICS-GAP1`` 寫的是**目錄** ``src/cpbl/ingest/``，而檔路徑那條
    要求副檔名 ⇒ 目錄形式抓不到。
* **1 張是真的沒有**：``INIT-OFFICIAL-DATA1`` 的非射程整段是政策性敘述
  （不把官方 API 當永久契約、不擴大每日 Playwright…），沒有指向任何卡外具名對象。

⇒ 交付照 A6 逐字的 pattern 報 **153／158**，並附本節的逐張理由；
⛔ **不得**把「語意上 157／158」當成 A6 的通過數，也⛔ **不得**回頭改 pattern 湊高數字
——那是「看著答案調判準」（memory: ``numbers-need-evidence-or-discussion``）。
pattern 該不該補全 repo 名與目錄形式，是另一張卡的事。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "cli" / "src"))

from guard import a6_named_targets  # noqa: E402
from relatedness import _REPO_ALIAS, mentions, repo_of  # noqa: E402

MARKER = "⛔ 非射程："
_EXT = r"(?:py|md|sql|json|ts|tsx|toml|sh|yml|yaml|plist|txt|cfg|ini|lock)"


def tail_of(text: str) -> str:
    i = text.find(MARKER)
    return text[i + len(MARKER):] if i >= 0 else ""


def known_card_ids(project_ids: set[str]) -> set[str]:
    """卡 ID 的封閉集合＝Project #4 ∪ 兩 repo 的**卡登記文件**裡出現的卡 ID。

    ⭐ 登記文件是白名單（Ledger／archive／契約文件），⛔ 不是全 repo grep——全 repo grep
    會把 commit message 與隨手提及也算進來，那又退回開放集合了。
    """
    reg = [
        ("/Users/ruanruan/Dev/ai-workflow", ["TASKS.md", "archive/TASKS_ARCHIVE.md",
                                             "docs/CONTROL_PLANE_CONTRACT.md"]),
        ("/Users/ruanruan/Dev/cpbl-analytics", ["docs/TASKS.md", "docs/archive/TASKS_ARCHIVE.md",
                                                "docs/CONTROL_PLANE_CONTRACT.md",
                                                "docs/PRODUCT_UX_BLUEPRINT.md",
                                                "docs/GAME_RECAP_PRODUCT_SPEC.md"]),
    ]
    out = set(project_ids)
    pat = re.compile(r"\b[A-Z][A-Z0-9]+(?:-[A-Z0-9]+){1,}\b")
    for repo, files in reg:
        for f in files:
            p = subprocess.run(["git", "-C", repo, "show", f"HEAD:{f}"], capture_output=True, text=True)
            if p.returncode == 0:
                out |= set(pat.findall(p.stdout))
    # ai-workflow 的 archive/tasks/*.md 檔名即卡 ID
    p = subprocess.run(["git", "-C", "/Users/ruanruan/Dev/ai-workflow", "ls-files", "archive/tasks"],
                       capture_output=True, text=True)
    out |= {Path(x).stem for x in p.stdout.split() if x.endswith(".md")}
    return out


def strict_targets(text: str, all_card_ids: set[str], ident: dict, self_repo: str | None,
                   repo_files: dict[str, set[str]]) -> dict[str, list[str]]:
    """回傳各型別的具名對象。⚠️ 「已驗證」只適用於卡 ID 與 issue 號，⛔ 不適用檔路徑。"""
    tail = tail_of(text)
    out: dict[str, list[str]] = {}

    # 卡 ID：⭐ 封閉集合——逐一問「這個專案有沒有這張卡」，⛔ 不用正則猜形狀
    hits = sorted(c for c in all_card_ids if mentions(tail, c))
    if hits:
        out["卡ID(登記存在)"] = hits

    # issue 號：驗 (repo, number) 真的在 Project 母體裡
    iss = []
    for m in re.finditer(r"\b(aiwf|cpbl)#(\d+)", tail):
        if (m.group(1), int(m.group(2))) in ident:
            iss.append(f"{m.group(1)}#{m.group(2)}")
    for m in re.finditer(r"(?<![\w#/-])#(\d+)", tail):
        alias = _REPO_ALIAS.get(self_repo or "")
        if alias and (alias, int(m.group(1))) in ident:
            iss.append(f"{alias}#{m.group(1)}")
    if iss:
        out["issue號(母體存在)"] = sorted(set(iss))

    # 檔路徑：⭐ **只驗形狀，⛔ 刻意不驗存在**。
    # 第一版驗了存在並把 `scripts/review_gate_preflight.py` 判為假陽性——⛔ 那是我錯：
    # 該簡介逐字寫「不得建立」該檔，**它不存在正是重點**。A6 問的是有沒有具名對象，
    # ⛔ 不是那個對象現在存不存在。``repo_files`` 仍傳入但只用於**標註**是否存在。
    paths = sorted({m.group(0) for m in re.finditer(rf"[\w./-]+\.{_EXT}\b", tail)})
    if paths:
        marked = []
        for p in paths:
            base = p.rsplit("/", 1)[-1]
            exists = any(p in fs or any(f.endswith("/" + base) or f == base for f in fs)
                         for fs in repo_files.values())
            marked.append(f"{p}{'' if exists else '(repo 內不存在，⭐ 仍算具名)'}")
        out["檔路徑(只驗形狀)"] = marked

    # 節號與 API 路由：⚠️ **不驗存在性**——canonical 節號與路由沒有可機械查的母體，
    # ⛔ 不假裝驗過。列出即算，並在報告中與前三類分開呈現。
    sec = sorted(set(re.findall(r"§[\d.]+", tail)))
    if sec:
        out["節號(未驗存在)"] = sec
    api = sorted(set(re.findall(r"/(?:api|games|players|teams)[\w/\[\]-]*", tail)))
    if api:
        out["API路由(未驗存在)"] = api
    return out


def main() -> int:
    snap = Path(sys.argv[1])
    briefs = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    items = json.loads(snap.read_text(encoding="utf-8"))["items"]
    by_id = {(i.get("fields") or {}).get("卡ID"): i for i in items if (i.get("fields") or {}).get("卡ID")}
    ident = {}
    for cid, it in by_id.items():
        alias = _REPO_ALIAS.get(repo_of(it) or "")
        if alias and it.get("issue_number"):
            ident[(alias, int(it["issue_number"]))] = cid

    repo_files = {}
    for name, path in (("ai-workflow", "/Users/ruanruan/Dev/ai-workflow"),
                       ("cpbl-analytics", "/Users/ruanruan/Dev/cpbl-analytics")):
        p = subprocess.run(["git", "-C", path, "ls-files"], capture_output=True, text=True)
        repo_files[name] = set(p.stdout.split()) if p.returncode == 0 else set()

    all_ids = known_card_ids(set(by_id))
    print(f"卡 ID 封閉集合大小：{len(all_ids)}（Project #4 的 {len(by_id)} ∪ 兩 repo 卡登記文件）")
    loose_pass = strict_pass = 0
    only_loose: list[tuple[str, list[str]]] = []
    neither: list[str] = []
    for cid in sorted(briefs):
        text = briefs[cid]
        loose = a6_named_targets(text)
        strict = strict_targets(text, all_ids, ident, repo_of(by_id.get(cid, {})), repo_files)
        # ⭐ 存在性可驗的三類才算 strict 通過；節號／API 路由單獨列不算
        verified = {k: v for k, v in strict.items() if "未驗存在" not in k}
        if loose:
            loose_pass += 1
        if verified:
            strict_pass += 1
        elif loose:
            only_loose.append((cid, loose))
        else:
            neither.append(cid)

    n = len(briefs)
    print(f"母體卡數 : {len(by_id)}；本批簡介 {n} 則")
    print()
    print(f"A6 loose（guard 正則，開放集合）: {loose_pass}／{n}")
    print(f"A6 strict（母體/repo 逐字比對）  : {strict_pass}／{n}")
    print()
    print(f"── 只過 loose、strict 不過（正則假陽性）{len(only_loose)} 張 ──")
    for cid, hits in only_loose:
        print(f"  {cid}: loose 命中 {hits}")
    print()
    print(f"── loose 與 strict 都不過 {len(neither)} 張（A6 是篩不是閘，逐張理由見交付報告）──")
    for cid in neither:
        print(f"  {cid}: 非射程段落 = {tail_of(briefs[cid])[:110]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
