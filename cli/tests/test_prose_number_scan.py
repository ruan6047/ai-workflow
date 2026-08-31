# 規劃文書敘述數字掃描器的守衛測試（P1-38）。
#
# 負控是本測試的核心：R14 證明「掃描 0 命中」可以是假陰性——所以這裡先證明
# 掃描器對「未標日期的裸現況數」（阿拉伯與中文數字兩型）真的會響，再證明語料
# 目前乾淨。inventory 的行文 hash 釘住由 drift 測試證明：改一個字元即轉紅。
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts" / "prose_number_scan.py"

_spec = importlib.util.spec_from_file_location("prose_number_scan", _SCRIPT)
assert _spec is not None and _spec.loader is not None
pns = importlib.util.module_from_spec(_spec)
sys.modules["prose_number_scan"] = pns
_spec.loader.exec_module(pns)


def _scan_text(tmp_path: Path, text: str, inventory=None) -> list[dict]:
    f = tmp_path / "probe.md"
    f.write_text(text + "\n", encoding="utf-8")
    return pns.scan_file(f, inventory=inventory, rel="probe.md")


def test_negative_control_arabic_undated(tmp_path):
    rows = _scan_text(tmp_path, "目前看板上有 42 張卡待處理。")
    assert [r["class"] for r in rows] == ["unclassified"]


def test_negative_control_chinese_numerals(tmp_path):
    # R14 反例的形狀：中文數字＋量詞、無日期
    rows = _scan_text(tmp_path, "實測十二條 amend 中六條是可合併的。")
    assert [r["class"] for r in rows] == ["unclassified"]


def test_dated_line_classified_a(tmp_path):
    rows = _scan_text(tmp_path, "2026-08-30 實測：看板上有 42 張卡。")
    assert [r["class"] for r in rows] == ["a"]


def test_artifact_pointer_classified_c(tmp_path):
    rows = _scan_text(tmp_path, "拒絕點全集 144 項開卡時 artifact 重量。")
    assert [r["class"] for r in rows] == ["c"]


def test_inventory_pins_line_text(tmp_path):
    line = "信封固定為 8 欄，缺一即拒。"
    inv = {("probe.md", pns._line_key(line)): {"reason": "design-closed-set"}}
    rows = _scan_text(tmp_path, line, inventory=inv)
    assert [r["class"] for r in rows] == ["b"]
    # 行文改一個字元 ⇒ hash 脫鉤 ⇒ unclassified（⛔ 不是靜默沿用）
    rows2 = _scan_text(tmp_path, "信封固定為 9 欄，缺一即拒。", inventory=inv)
    assert [r["class"] for r in rows2] == ["unclassified"]


def test_corpus_is_fully_classified():
    result = pns.scan_corpus()
    assert result["unclassified"] == [], [
        f'{r["path"]}:{r["line"]} {r["text"][:80]}' for r in result["unclassified"]
    ]
    assert result["dead_entries"] == [], [
        f'{e["path"]} {e.get("excerpt", "")[:60]}' for e in result["dead_entries"]
    ]


def test_inventory_entries_all_carry_known_reason():
    data = json.loads((pns.INVENTORY_PATH).read_text(encoding="utf-8"))
    known = set(data["_meta"]["classes"])
    bad = [e for e in data["entries"] if e["reason"] not in known]
    assert bad == []


def test_cli_exit_code_red_on_unclassified(tmp_path):
    f = tmp_path / "probe.md"
    f.write_text("目前有 7 張卡。\n", encoding="utf-8")
    assert pns.main(["--file", str(f)]) == 1
    f.write_text("2026-08-30 有 7 張卡。\n", encoding="utf-8")
    assert pns.main(["--file", str(f)]) == 0
