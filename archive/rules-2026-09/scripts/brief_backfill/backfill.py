#!/usr/bin/env python3
"""回填簡介。每張獨立、失敗不影響其他張、可自任意中斷點續跑。

紀律（卡面 A5／A7）：
  1. 呼叫 ``wfcli amend`` **之前**先過 ``guard.assert_writable``（分行字元拒收）。
  2. 每張之前查 ``rate_limit``；餘額 < ``--min-quota`` 就等到 reset。
  3. ``--repo`` **逐卡自 ``issue_url`` 導出**——Project #4 橫跨兩 repo，
     ⭐ 55 個 issue 號重複，餵錯 repo 會去改另一個 repo 的同號 Issue。
  4. 寫入前後各重讀一次該卡 body 全文並存檔（V4 不變量與 V5 負控的原始輸出）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "cli" / "src"))

import quota as _quota_mod  # noqa: E402
from guard import BriefRejected, a6_named_targets, assert_writable  # noqa: E402


def sh(args: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(args, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def quota() -> tuple[int, int]:
    """(remaining, reset_epoch)。⭐ 走 GraphQL 的 ``rateLimit`` 欄位。

    ⛔ **2026-08-26 第三批修正：本函式原本讀 REST 的 ``gh api rate_limit``，量不準。**
    實測同一時刻 REST 說 ``used=0/remaining=5000``、GraphQL 說 ``used=136/remaining=4864``；
    REST 在兩個互不同步的狀態間跳（40 次連讀有 4 次讀到另一個，序列非單調、讀回會變大），
    而 GraphQL 的 ``rateLimit`` 連讀 6 次完全一致。細節與取樣序列見 ``quota.py`` 的模組
    docstring。

    ⛔ **不得由此推出「前兩批的成本數字換算一下就好」**——那些數字是用壞掉的儀器量的，
    ⇒ 只能重量。前兩批登記的兩筆「無法解釋的 435／447 點」與本缺陷形狀相符，
    ⛔ 但未證實：當時的原始取樣沒留 ``reset`` 欄位，無從回溯判定。
    """
    r = _quota_mod.probe()
    import datetime

    reset = int(datetime.datetime.fromisoformat(r["resetAt"].replace("Z", "+00:00")).timestamp())
    return int(r["remaining"]), reset


def fetch_body(repo: str, number: int) -> str:
    rc, out, err = sh(["gh", "api", f"repos/{repo}/issues/{number}", "--jq", ".body"])
    if rc != 0:
        raise RuntimeError(f"讀 body 失敗 {repo}#{number}：{err}")
    # gh --jq 對字串輸出會補一個換行；⛔ 只剝那一個，不做其他正規化
    return out[:-1] if out.endswith("\n") else out


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--briefs", required=True)
    ap.add_argument("--cards", required=True, help="每行一個 card_id")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--reason", required=True)
    ap.add_argument("--min-quota", type=int, default=400)
    ap.add_argument("--wfcli", default="wfcli")
    ap.add_argument("--poison", action="store_true", help="V5 負控：在文字尾端接 \\n## Log")
    ap.add_argument("--dry-run", action="store_true", help="只跑守衛與 A6，⛔ 不呼叫 amend")
    args = ap.parse_args()

    out = Path(args.out_dir)
    (out / "before").mkdir(parents=True, exist_ok=True)
    (out / "after").mkdir(parents=True, exist_ok=True)

    items = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))["items"]
    by_id = {(i.get("fields") or {}).get("卡ID"): i for i in items if (i.get("fields") or {}).get("卡ID")}
    briefs = json.loads(Path(args.briefs).read_text(encoding="utf-8"))
    cards = [c for c in Path(args.cards).read_text(encoding="utf-8").split() if c]

    ledger: list[dict] = []
    for cid in cards:
        rec: dict = {"card_id": cid}
        try:
            item = by_id[cid]
            repo = "/".join((item["issue_url"] or "").split("/")[3:5])
            number = item["issue_number"]
            assert repo and number, f"{cid} 沒有 repo/issue 號，本腳本不處理 DraftIssue"
            text = briefs[cid]
            if args.poison:
                text = text + "\n## Log"
            rec.update(repo=repo, issue=number, brief_len=len(text))

            # 先取 before 快照（唯讀 REST）：⭐ 守衛拒收時也要有 before/after 對照，
            # 否則 V5 只能宣稱「沒寫」而拿不出「body 逐位元未變」的證據。
            before = fetch_body(repo, number)
            (out / "before" / f"{cid}.md").write_text(before, encoding="utf-8")
            rec["before_sha256"] = sha(before)
            rec["before_len"] = len(before)

            # ---- A5 守衛：在任何**寫入**呼叫之前 ----
            try:
                assert_writable(text)
                rec["guard"] = "pass"
            except BriefRejected as exc:
                after = fetch_body(repo, number)
                (out / "after" / f"{cid}.md").write_text(after, encoding="utf-8")
                rec.update(
                    guard="REJECTED", guard_msg=str(exc), rc=None, wrote=after != before,
                    after_sha256=sha(after), after_len=len(after),
                )
                print(f"[{cid}] 守衛拒收（body 未變={after == before}）：{exc}")
                ledger.append(rec)
                continue
            rec["a6_named_targets"] = a6_named_targets(text)

            if args.dry_run:
                rec.update(rc=None, wrote=False, note="dry-run")
                ledger.append(rec)
                continue

            q, reset = quota()
            waited = 0
            while q < args.min_quota:
                wait = max(reset - int(time.time()) + 5, 5)
                print(f"[{cid}] 額度 {q} < {args.min_quota}，等 {wait}s")
                time.sleep(wait)
                waited += wait
                q, reset = quota()
            rec.update(quota_before=q, waited_sec=waited)

            t_amend = time.time()
            rc, so, se = sh([
                args.wfcli, "amend", cid,
                "--brief", text,
                "--reason", args.reason,
                "--owner", "ruan6047", "--project", "4", "--repo", repo,
            ])
            elapsed = time.time() - t_amend
            rec.update(rc=rc, stdout=so.strip(), stderr=se.strip(), amend_sec=round(elapsed, 2))
            q2, _ = quota()
            rec.update(quota_after=q2, quota_cost=q - q2)

            after = fetch_body(repo, number)
            (out / "after" / f"{cid}.md").write_text(after, encoding="utf-8")
            rec.update(after_sha256=sha(after), after_len=len(after), wrote=after != before)
            print(f"[{cid}] rc={rc} 耗點={q - q2} body變動={after != before}")
        except Exception as exc:  # noqa: BLE001 —— 每張獨立，一張爆不影響其他張
            rec.update(error=f"{type(exc).__name__}: {exc}")
            print(f"[{cid}] 例外：{exc}")
        ledger.append(rec)

    (out / "ledger.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for r in ledger if r.get("rc") == 0)
    print(f"\n完成 {ok}/{len(cards)}；ledger → {out / 'ledger.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
