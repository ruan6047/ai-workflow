# 污染符 checker 的回歸／負控測試（WF-REDESIGN-W2A R1-003）。
#
# 三支各釘死 R1-003 的一條 evidence：
# (1) token 集合以決議 §二 為**單一來源**——首版註解誤稱 12 個且整個漏掉 `Discovery lead`；
# (2) 自指檔（checker／manifest／本測試檔，canonical §6.2 逐字的「工具或測試檔」）
#     **在母體內且可見列計**——首版把 checker 與 manifest 踢出母體，直接指定重跑才看得到 115 筆；
# (3) **逐 occurrence** ⛔ 非逐行——首版每行每 token 只 search 一次，同行重複被吃掉
#     （checker 檔實得 29 次只記 16 筆、manifest 實得 100 次只記 99 筆）。
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts" / "pollution_check.py"

_spec = importlib.util.spec_from_file_location("pollution_check", _SCRIPT)
assert _spec is not None and _spec.loader is not None
pc = importlib.util.module_from_spec(_spec)
sys.modules["pollution_check"] = pc
_spec.loader.exec_module(pc)

_DECISION = _REPO_ROOT / "docs" / "research" / "WORKFLOW-REDESIGN-2026-08-30.md"


def _decision_tokens() -> list[str]:
    """決議 §二 那一行的反引號 token，**照它的順序**。單一來源，⛔ 不在測試裡另抄一份。"""
    lines = _DECISION.read_text(encoding="utf-8").splitlines()
    idx = next(i for i, ln in enumerate(lines) if ln.startswith("## 二 · 污染符清單"))
    body = next(ln for ln in lines[idx + 1:] if ln.strip())
    return re.findall(r"`([^`]+)`", body)


def _write_allowlist(path: Path, entries: list[dict]) -> Path:
    path.write_text(json.dumps({"_meta": {}, "entries": entries}, ensure_ascii=False),
                    encoding="utf-8")
    return path


# ---- (1) token 集合＝決議 §二（回歸：Discovery lead 曾整個漏掉） ----

def test_pollution_tokens_match_the_decision_record_verbatim():
    want = _decision_tokens()
    got = [name for name, _pat, _src in pc.POLLUTION_TOKENS]
    assert got == want, f"與決議 §二 不一致：缺 {set(want) - set(got)} 多 {set(got) - set(want)}"
    # 負控：R1-003 指名的那一個必須在裡面，且真的會響
    assert "Discovery lead" in got
    assert any(rx.search("| Discovery lead | 把使用者研究整理為證據 |")
               for name, rx in pc._COMPILED if name == "Discovery lead")


def test_discovery_lead_is_flagged_on_a_fixture(tmp_path):
    probe = tmp_path / "probe.md"
    probe.write_text("| Discovery lead | 舊角色表列 |\n", encoding="utf-8")
    allow = _write_allowlist(tmp_path / "allow.json", [])
    result = pc.run(tmp_path, ["probe.md"], allow)
    assert result["unapproved_count"] == 1
    assert result["unapproved"][0].token == "Discovery lead"


# ---- (2) 自指檔在母體內且可見列計（canonical §6.2） ----

def _mini_repo(root: Path) -> str:
    """在 tmp 造一棵有一個 commit 的小 repo，回傳該 commit 的 SHA。

    ⚠️ **刻意⛔ 不對真 repo 跑 `post_image_paths`**：CI 的 checkout 是 shallow
    （`fetch-depth` 預設 1），`git diff <BASE_SHA>` 在那裡直接 `CalledProcessError`
    ——本測試首版就是這樣本機綠、CI 紅。判準本身與 repo 歷史無關，故改成合成樹。
    """
    def g(*a: str) -> str:
        return subprocess.run(["git", *a], cwd=root, check=True,
                              capture_output=True, text=True).stdout.strip()
    g("init", "-q", "-b", "main")
    g("config", "user.email", "t@example.invalid")
    g("config", "user.name", "t")
    (root / "seed.txt").write_text("seed\n", encoding="utf-8")
    g("add", "seed.txt")
    g("commit", "-qm", "seed")
    return g("rev-parse", "HEAD")


def test_self_reference_files_are_not_filtered_out_of_the_population(tmp_path):
    # 成員判準＝canonical §6.2 的「工具或測試檔」：checker、manifest、本測試檔
    assert pc.SELF_REFERENCE_PATHS == (
        "scripts/pollution_check.py",
        "scripts/pollution-allowlist.json",
        "cli/tests/test_pollution_check.py",
    )
    base = _mini_repo(tmp_path)
    for rel in (*pc.SELF_REFERENCE_PATHS, "docs/normal.md"):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("一行含 needs-deploy 的內容\n", encoding="utf-8")
    rels = pc.post_image_paths(tmp_path, base)
    for rel in pc.SELF_REFERENCE_PATHS:
        assert rel in rels, f"{rel} 被踢出母體——canonical §6.2 逐字禁止偷偷排除"
    assert "docs/normal.md" in rels


def test_self_reference_hits_are_visible_and_tallied():
    # ⛔ 不碰 git：直接指定三個檔，判準與 repo 歷史無關
    result = pc.run(_REPO_ROOT, list(pc.SELF_REFERENCE_PATHS), pc.ALLOWLIST_PATH)
    assert result["self_reference_count"] > 0
    # 命中計入母體總數，⛔ 不是被扣掉
    assert result["total_hits"] == result["self_reference_count"]
    # 「列出檔名⛔ 不等於列計命中」：逐檔逐 token 都要有數字
    assert set(result["self_reference_tally"]) == set(pc.SELF_REFERENCE_PATHS)
    for path, per_token in result["self_reference_tally"].items():
        assert per_token and all(n >= 1 for n in per_token.values()), (path, per_token)
    # 自指是分類⛔ 不是豁免：替它開 manifest 條目一律判 invalid（且不收斂，見模組 docstring）
    errs = pc.entry_errors({
        "path": pc.SELF_REFERENCE_PATHS[0], "token": "短版", "line_sha1": "a" * 40,
        "excerpt": "x", "occurrences": 1, "rationale": "測試用理由字串夠長",
    })
    assert any("自指" in e for e in errs), errs


# ---- (3) 逐 occurrence：同行同 token 重複，配額不足必紅 ----

def test_repeated_token_on_one_line_is_counted_per_occurrence(tmp_path):
    line = "舊語彙 needs-deploy 與另一個 needs-deploy 同行出現兩次。"
    probe = tmp_path / "probe.md"
    probe.write_text(line + "\n", encoding="utf-8")
    entry = {"path": "probe.md", "token": "needs-deploy",
             "line_sha1": pc.line_key(line), "excerpt": line[:40],
             "occurrences": 1, "rationale": "刻意只宣告一個 occurrence 作負控"}

    short = pc.run(tmp_path, ["probe.md"], _write_allowlist(tmp_path / "a1.json", [entry]))
    assert short["total_hits"] == 2, "逐行 search 會只記 1——R1-003 的原缺陷"
    assert short["unapproved_count"] == 1
    assert pc.main(["--root", str(tmp_path), "--files", "probe.md",
                    "--allowlist", str(tmp_path / "a1.json")]) == 1

    exact = dict(entry, occurrences=2)
    full = pc.run(tmp_path, ["probe.md"], _write_allowlist(tmp_path / "a2.json", [exact]))
    assert full["unapproved_count"] == 0
    assert pc.main(["--root", str(tmp_path), "--files", "probe.md",
                    "--allowlist", str(tmp_path / "a2.json")]) == 0
