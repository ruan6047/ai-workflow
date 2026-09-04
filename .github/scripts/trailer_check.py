#!/usr/bin/env python3
"""P5：commit trailer 鍵在允許集合內，且是訊息末端的連續單一區塊。

只驗兩件事（骨架 §三 P5）：
1. trailer 區塊＝末段（最後一個空行之後）且至少一行的鍵在允許集合內；區塊內每行都要是
   `Key: value` 且 Key 在允許集合內。末段沒有任何允許鍵＝沒有 trailer，不驗（散文、
   conventional subject 都不是 trailer）。
2. 允許集合內的鍵不得出現在非末段（被空行切斷＝不是連續區塊）。
⛔ 不驗哪些 trailer 必須出現、不驗值——那是 core/platform.md 的條文，不在本步。

`--selftest` 跑內建正負控。
"""
import re
import subprocess
import sys

ALLOWED = {"requested-by", "planned-by", "implemented-by", "reviewed-by", "co-authored-by"}
TRAILER = re.compile(r"^([A-Za-z][A-Za-z-]*):\s+.+$")


def commits(rng: str, cwd: str | None = None) -> list[str]:
    # merge commit 一樣受檢（P5 無 merge 例外；Reviewed-by 正是落在 merge 上）。
    out = subprocess.run(["git", "rev-list", rng], capture_output=True, text=True, check=True, cwd=cwd).stdout
    return out.split()


def message(sha: str, cwd: str | None = None) -> str:
    return subprocess.run(["git", "log", "-1", "--format=%B", sha], capture_output=True, text=True, check=True, cwd=cwd).stdout


def run_range(rng: str, cwd: str | None = None) -> tuple[int, list[str]]:
    shas = commits(rng, cwd)
    errors: list[str] = []
    for sha in shas:
        errors.extend(check(sha, message(sha, cwd)))
    return len(shas), errors


def key_of(line: str) -> str | None:
    m = TRAILER.match(line.strip())
    return m.group(1).lower() if m else None


def check(sha: str, body: str) -> list[str]:
    paragraphs = [p for p in re.split(r"\n\s*\n", body.strip("\n")) if p.strip()]
    if not paragraphs:
        return []
    errors: list[str] = []
    last = paragraphs[-1].splitlines()
    keys = [key_of(line) for line in last]
    if any(k in ALLOWED for k in keys):
        for line, k in zip(last, keys):
            if k is None:
                errors.append(f"{sha[:7]}: trailer 區塊混入非 trailer 行「{line.strip()}」——區塊不純")
            elif k not in ALLOWED:
                errors.append(f"{sha[:7]}: trailer 區塊內未知鍵「{line.strip().split(':')[0]}」")
    for para in paragraphs[:-1]:
        for line in para.splitlines():
            k = key_of(line)
            if k in ALLOWED:
                errors.append(f"{sha[:7]}: trailer「{line.strip().split(':')[0]}」被空行切出末段——不是連續區塊")
    return errors


FIXTURES: list[tuple[str, str, bool]] = [
    ("no_trailer_plain_subject", "add archive index\n", True),
    ("no_trailer_conventional_subject", "fix: add archive\n", True),
    ("no_trailer_colon_body_tail", "fix: x\n\nNote: migration is intentional\n", True),
    ("trailer_ok", "fix: x\n\nbody\n\nRequested-by: a\nCo-Authored-By: b <b@x>\n", True),
    ("trailer_split_by_blank", "fix: x\n\nRequested-by: a\n\nCo-Authored-By: b <b@x>\n", False),
    ("trailer_impure", "fix: x\n\nRequested-by: a\nsee above\n", False),
    ("trailer_unknown_key", "fix: x\n\nRequested-by: a\nSigned-off-by: c\n", False),
]


def merge_commit_fixture() -> bool:
    """負控：違規 trailer 落在 merge commit 上也要被抓到。"""
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@x",
               "HOME": d, "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"}
        g = lambda *a: subprocess.run(["git", *a], cwd=d, env=env, check=True, capture_output=True, text=True)
        g("init", "-q", "-b", "main")
        g("commit", "-q", "--allow-empty", "-m", "base")
        g("checkout", "-q", "-b", "topic")
        g("commit", "-q", "--allow-empty", "-m", "topic\n\nCo-Authored-By: b <b@x>")
        g("checkout", "-q", "main")
        g("merge", "-q", "--no-ff", "topic", "-m", "merge\n\nRequested-by: a\n\nCo-Authored-By: b <b@x>")
        n, errors = run_range("main~1..main", d)
        merge_flagged = any("被空行切出末段" in e for e in errors)
        print(f"merge_commit_split_trailer: {'PASS' if (n == 2 and merge_flagged) else 'FAIL'} (受檢 {n}, rc={1 if errors else 0})")
        return n == 2 and merge_flagged


def selftest() -> int:
    bad = 0
    for name, body, expect_ok in FIXTURES:
        ok = not check("1111111", body)
        print(f"{name}: {'PASS' if ok == expect_ok else 'FAIL'} (rc={0 if ok else 1})")
        bad += ok != expect_ok
    bad += not merge_commit_fixture()
    return 1 if bad else 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest()
    rng = sys.argv[1] if len(sys.argv) > 1 else "HEAD~1..HEAD"
    n, errors = run_range(rng)
    print(f"受檢 commit：{n}（{rng}）")
    for e in errors:
        print(f"⛔ {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
