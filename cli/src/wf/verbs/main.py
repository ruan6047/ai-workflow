"""入口。動詞集合固定為七個（core/verbs.md §1）；本檔只做分派，各動詞住 verbs/<name>.py。"""
import sys

VERBS = ("open", "move", "edit", "notes", "brief", "review", "snapshot")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in VERBS:
        print("wf <" + "|".join(VERBS) + "> …", file=sys.stderr)
        return 2
    print(f"{argv[0]}: 尚未實作", file=sys.stderr)
    return 2
