#!/usr/bin/env python3
"""P5：commit trailer 鍵在允許集合內，且是訊息末端的連續單一區塊。

只驗兩件事（骨架 §三 P5）：
1. 末段（最後一個空行之後）若含 trailer 形狀的行，則整段每行都要是 `Key: value`，Key 在允許集合內。
2. 允許集合內的 Key 不得出現在非末段（被空行切斷＝不是連續區塊）。
⛔ 不驗哪些 trailer 必須出現、不驗值——那是 core/platform.md 的條文，不在本步。
"""
import re
import subprocess
import sys

ALLOWED = {"requested-by", "planned-by", "implemented-by", "reviewed-by", "co-authored-by"}
TRAILER = re.compile(r"^([A-Za-z][A-Za-z-]*):\s+.+$")


def commits(rng: str) -> list[str]:
    out = subprocess.run(["git", "rev-list", "--no-merges", rng], capture_output=True, text=True, check=True).stdout
    return out.split()


def message(sha: str) -> str:
    return subprocess.run(["git", "log", "-1", "--format=%B", sha], capture_output=True, text=True, check=True).stdout


def check(sha: str, body: str) -> list[str]:
    paragraphs = [p for p in re.split(r"\n\s*\n", body.strip("\n")) if p.strip()]
    if not paragraphs:
        return []
    errors: list[str] = []
    last = paragraphs[-1].splitlines()
    shaped = [TRAILER.match(line.strip()) for line in last]
    if any(shaped):
        for line, m in zip(last, shaped):
            if m is None:
                errors.append(f"{sha[:7]}: 末段混入非 trailer 行「{line.strip()}」——區塊不純")
            elif m.group(1).lower() not in ALLOWED:
                errors.append(f"{sha[:7]}: 未知 trailer 鍵「{m.group(1)}」")
    for para in paragraphs[:-1]:
        for line in para.splitlines():
            m = TRAILER.match(line.strip())
            if m and m.group(1).lower() in ALLOWED:
                errors.append(f"{sha[:7]}: trailer「{m.group(1)}」被空行切出末段——不是連續區塊")
    return errors


def main() -> int:
    rng = sys.argv[1] if len(sys.argv) > 1 else "HEAD~1..HEAD"
    shas = commits(rng)
    errors: list[str] = []
    for sha in shas:
        errors.extend(check(sha, message(sha)))
    print(f"受檢 commit：{len(shas)}（{rng}）")
    for e in errors:
        print(f"⛔ {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
