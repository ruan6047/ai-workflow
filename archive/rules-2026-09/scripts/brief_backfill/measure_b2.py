#!/usr/bin/env python3
"""V2／V3 的量測與統計檢定（第二批）。

⭐ **GT builder 與命中判準一律 import ``relatedness``，⛔ 不重打**——本 repo 已有五次
「驗證器自己打錯」造成的假陰性。``head_of`` 預設剔除 ``## 簡介`` 區段（先導批當場抓到
的循環量測修正），本腳本沿用該版本。

**GT-A**（卡面 V2 的逐字定義）：卡 A 的 ``## Log`` 之前提到卡 B 的**卡 ID**。
**GT-B**（追加，⚠️ 非卡面定義）：同上，另認 ``aiwf#N``／``cpbl#N``／同 repo 裸 ``#N``。

**基準**：同一組 (A, B)，兩卡的 ``resources`` 有無完全相同字串（``find_conflicts`` 判準）。

⛔ **哪一個數字是裁決，先講清楚（本腳本一次印四組，讀者會挑好看的那組當結論）**：

    **GT-A ／ 簡介 strict ＝ 卡面 V2 的逐字定義 ＝ 唯一的裁決數字。**

其餘三組（GT-A/ext、GT-B/strict、GT-B/ext）是**補充診斷**，用途是回答「沒過是因為
判準太窄還是簡介真的沒抓到」。⛔ 不得單獨引用其中任何一組宣稱 V2 通過——GT-B 是本輪
**追加**的定義（卡面沒有），ext 是**放寬**的命中判準；兩者都朝對簡介有利的方向鬆綁。
⚠️ 2026-08-26 實測即出現這個陷阱：GT-A/strict 不顯著（p=0.22）而 GT-B/ext 顯著
（p=0.042）——若只報後者就是**挑了會過的那把尺**。

統計檢定兩種，**兩種都報**：
  (1) **對母體基準的二項檢定**——卡面 V2 逐字「須顯著高於資源宣告的基準」，
      基準 p0 為**全母體現場重算**值；H1 為單尾 p > p0。
  (2) **McNemar 配對檢定**——同一組 pair 上「簡介中／資源宣告中」的配對比較。
      ⭐ 這是 apples-to-apples 的那個：兩個機制在**同一批 pair** 上比。
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "cli" / "src"))

from guard import a6_named_targets  # noqa: E402
from relatedness import _REPO_ALIAS, head_of, issue_refs, mentions, repo_of  # noqa: E402
from wf_cli import brief as brief_mod  # noqa: E402
from wf_cli import resources as res_mod  # noqa: E402


def binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k)，X ~ Binomial(n, p)。⛔ 不引 scipy（cli venv 沒有）。"""
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))


def mcnemar_exact(b: int, c: int) -> float:
    """精確 McNemar。b＝只有簡介中，c＝只有資源宣告中。

    ⭐ **刻意用精確二項而非 χ² 近似，且刻意取單尾。** 讀者會覺得兩者都「不標準」：

    * **精確而非 χ²**：不一致對數 ``b+c`` 在本卡的量級是個位數到十幾，χ² 近似在
      ``b+c < 25`` 時不成立。⛔ 不是忘了用 ``scipy``——``cli`` 的 venv 沒有 scipy，
      而為了一個檢定加一個相依不划算。
    * **單尾**：卡面 V2 的假說是**有方向的**——「簡介須**高於**資源宣告基準」。
      雙尾會把「簡介顯著**更差**」也算成顯著，那不是本卡要問的。
      ⚠️ 代價是這個檢定**對簡介有利**（同樣資料下 p 值是雙尾的一半）⇒
      ⛔ **它沒過就是真的沒過**，不得再以「換雙尾看看」尋找通過的組合。
    """
    n = b + c
    if n == 0:
        return 1.0
    return binom_sf(b, n, 0.5)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - s) / d, (c + s) / d)


def pct(k: int, n: int) -> str:
    return f"{100.0 * k / n:.1f}%" if n else "n/a"


def build(items: list[dict], override: dict | None = None):
    override = override or {}
    by_id = {(i.get("fields") or {}).get("卡ID"): i for i in items if (i.get("fields") or {}).get("卡ID")}
    ident = {}
    for cid, it in by_id.items():
        alias = _REPO_ALIAS.get(repo_of(it) or "")
        if alias and it.get("issue_number"):
            ident[(alias, int(it["issue_number"]))] = cid

    briefs = {}
    for cid, it in by_id.items():
        parsed = brief_mod.try_parse_block(it.get("body") or "")
        briefs[cid] = override.get(cid, parsed.text if parsed else None)
    decls = {cid: res_mod.try_parse_block(it.get("body") or "") for cid, it in by_id.items()}

    gt_a, gt_b = [], []
    for a_id, a in by_id.items():
        head = head_of(a.get("body") or "")  # ⭐ 已剔除 ## 簡介 區段
        ref_ids = {ident[r] for r in issue_refs(head, repo_of(a)) if r in ident}
        for b_id in by_id:
            if b_id == a_id:
                continue
            by_cid = mentions(head, b_id)
            if by_cid:
                gt_a.append((a_id, b_id))
            if by_cid or b_id in ref_ids:
                gt_b.append((a_id, b_id))

    def res_hit(a_id, b_id):
        da, db = decls.get(a_id), decls.get(b_id)
        return bool(da and db and set(da.resources) & set(db.resources))

    def brief_hit(a_id, b_id, mode="strict"):
        t = briefs.get(a_id)
        if not t:
            return False
        if mentions(t, b_id):
            return True
        if mode == "strict":
            return False
        return any(ident.get(r) == b_id for r in issue_refs(t, repo_of(by_id[a_id])))

    return by_id, briefs, gt_a, gt_b, res_hit, brief_hit


def main() -> int:
    snap = Path(sys.argv[1])
    subset = set(Path(sys.argv[2]).read_text(encoding="utf-8").split())
    # ⚠️ 空字串代表「不覆寫」——供 shell 以固定位置參數呼叫時佔位用
    ov_arg = sys.argv[3] if len(sys.argv) > 3 else ""
    override = json.loads(Path(ov_arg).read_text(encoding="utf-8")) if ov_arg else None
    label = sys.argv[4] if len(sys.argv) > 4 else "本批"

    items = json.loads(snap.read_text(encoding="utf-8"))["items"]
    by_id, briefs, gt_a, gt_b, res_hit, brief_hit = build(items, override)

    print(f"snapshot : {snap}")
    print(f"母體卡數 : {len(by_id)}；子集 {label} = {len(subset)} 張")
    if override:
        print(f"⚠️ 已套用 --override（{len(override)} 張以替代文字取代卡面現值）")
    print()

    for gname, gt in (("GT-A（卡面逐字定義：卡 ID）", gt_a), ("GT-B（追加：卡 ID 或 issue 參照）", gt_b)):
        n_all = len(gt)
        r_all = sum(1 for p in gt if res_hit(*p))
        print(f"══ {gname} ══")
        print(f"  全母體 GT 組數           : {n_all}")
        print(f"  ⭐ 資源宣告基準（現場重算）: {r_all}/{n_all} = {pct(r_all, n_all)}")
        # ⭐ **刻意：p0 取自「全母體」而 k/n 取自「子集」。** 讀者會以為分母對錯了——
        # ⛔ 沒有。卡面 V2 逐字要求「須顯著高於資源宣告的 15.8% 基準」，那個基準就是
        # **母體層級**的常數（本腳本現場重算，⛔ 不沿用研究輪數字）。把它當成已知的 p0
        # 做二項檢定，正是該條的字面意思。
        # ⚠️ 但這個檢定忽略了 p0 自身的估計誤差，且假設兩批 pair 可比 ⇒ **所以同時報
        # McNemar**：那個是在**同一批 pair** 上做的配對比較，不受此問題影響。
        # ⛔ 不得只報其中一個。
        p0 = r_all / n_all if n_all else 0.0
        sel = [p for p in gt if p[0] in subset]
        n = len(sel)
        r = sum(1 for p in sel if res_hit(*p))
        for mode in ("strict", "ext"):
            k = sum(1 for p in sel if brief_hit(*p, mode))
            lo, hi = wilson(k, n)
            pv = binom_sf(k, n, p0) if n else 1.0
            # McNemar：同一批 pair 上的配對比較
            b = sum(1 for p in sel if brief_hit(*p, mode) and not res_hit(*p))
            c = sum(1 for p in sel if not brief_hit(*p, mode) and res_hit(*p))
            mc = mcnemar_exact(b, c)
            print(f"  ── {label} 為來源、簡介 {mode} ──")
            print(f"     GT 組數 {n}（來源卡 {len({p[0] for p in sel})} 張）")
            print(f"     簡介抓回     : {k}/{n} = {pct(k, n)}  95%CI [{lo * 100:.1f}%, {hi * 100:.1f}%]")
            print(f"     同批資源宣告 : {r}/{n} = {pct(r, n)}")
            print(f"     二項檢定 vs 母體基準 p0={p0:.4f} → 單尾 p = {pv:.4f}"
                  f"  {'✅ 顯著' if pv < 0.05 else '❌ 不顯著'}(α=0.05)")
            print(f"     McNemar 配對 b(只簡介中)={b} c(只資源中)={c} → 單尾 p = {mc:.4f}"
                  f"  {'✅ 顯著' if mc < 0.05 else '❌ 不顯著'}(α=0.05)")
        print()

    print("══ 逐卡（GT-A／strict）══")
    for cid in sorted(subset):
        ps = [p for p in gt_a if p[0] == cid]
        hit = [p[1] for p in ps if brief_hit(*p, "strict")]
        miss = [p[1] for p in ps if not brief_hit(*p, "strict")]
        a6 = a6_named_targets(briefs.get(cid) or "")
        print(f"  {cid}: {len(hit)}/{len(ps)}")
        if hit:
            print(f"      命中 {hit}")
        if miss:
            print(f"      未中 {miss}")
        print(f"      A6 具名對象 {len(a6)} 個{'' if a6 else '  ⛔ A6 不通過'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
