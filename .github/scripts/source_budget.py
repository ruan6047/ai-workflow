#!/usr/bin/env python3
"""CLI production source 的聚合行數治理軟警示（core/modules.md 非射程；WF-011 驗收第 5 條）。

被測物＝`cli/src/wf`。計數口徑：遞迴 `*.py`、排除空行；測試目錄與產生檔本就不在該樹下。
達門檻時印一行 GitHub Actions `::warning::` 註記（含當前行數與門檻），rc 恆 0——
這是**治理軟警示**，⛔ 不擋業務 CLI、⛔ 不要求壓行。

`TOTAL_LIMIT` 只有這一個字面居所：真掃描的比較函式 `aggregate` 與 `cli/tests/test_gh_scope.py`
的合成樹負控都從這裡匯入，⛔ 不重打。單檔 400 行與單一函式 150 行兩個既有觸發器住 test_gh_scope.py，
本檔⛔ 不重複它們。

`--selftest` 跑內建正負控（恰門檻判未達、門檻+1 判達）。
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
TARGET = "cli/src/wf"
TOTAL_LIMIT = 5000
WARNING = "::warning file={target}::CLI production source 聚合 {total} 行，達治理門檻 {limit} 行；規劃者與查核者須在交回單寫出責任邊界與行數增長原因（stages/planning.md §5、stages/review.md §5）"


def aggregate(root):
    """遞迴 `*.py` 的聚合行數與「是否達門檻」。

    真掃描據以判達與未達的比較函式就是這一個；合成樹負控用的也是這一個（同一函式，⛔ 不是複製品）。
    空行不計入（口徑排除空行）；非 `*.py` 的檔不進母體。
    """
    total = sum(1 for path in sorted(root.rglob("*.py"))
                for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return total, total >= TOTAL_LIMIT


def selftest(tmp) -> int:
    """負控：恰 TOTAL_LIMIT 行判達、TOTAL_LIMIT − 1 行判未達；兩棵樹的行數由 TOTAL_LIMIT 算出。"""
    def tree(name, lines):
        root = tmp / name
        (root / "pkg").mkdir(parents=True)
        head = lines // 2
        (root / "a.py").write_text("\n".join(["x = 0"] * head + [""] * 7) + "\n", encoding="utf-8")
        (root / "pkg" / "b.py").write_text("\n".join(["y = 0"] * (lines - head)) + "\n", encoding="utf-8")
        (root / "pkg" / "noise.txt").write_text("\n".join(["z"] * lines) + "\n", encoding="utf-8")
        return root

    at = aggregate(tree("at_limit", TOTAL_LIMIT))
    under = aggregate(tree("under_limit", TOTAL_LIMIT - 1))
    ok = at == (TOTAL_LIMIT, True) and under == (TOTAL_LIMIT - 1, False)
    print(f"selftest_budget_at_limit: {'PASS' if at == (TOTAL_LIMIT, True) else 'FAIL'}（{at}）")
    print(f"selftest_budget_under_limit: {'PASS' if under == (TOTAL_LIMIT - 1, False) else 'FAIL'}（{under}）")
    return 0 if ok else 1


def main(argv) -> int:
    if len(argv) > 1 and argv[1] == "--selftest":
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            return selftest(Path(tmp))
    total, reached = aggregate(ROOT / TARGET)
    if reached:
        print(WARNING.format(target=TARGET, total=total, limit=TOTAL_LIMIT))
    print(f"SOURCE_BUDGET {TARGET} {total}/{TOTAL_LIMIT} {'REACHED' if reached else 'UNDER'}")
    return 0  # 恆 0：治理軟警示，⛔ 不擋 CI、⛔ 不擋業務 CLI


if __name__ == "__main__":
    sys.exit(main(sys.argv))
