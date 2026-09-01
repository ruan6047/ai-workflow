"""``scripts/contract_tool_reconcile.py`` 的測試。

分兩組，**兩組都必要**：

- **合成樹**（``synthetic_repo``）：釘住判定規則本身。規則要能對「一個我完全控制內容的
  repo」給出可預測的答案，否則它量到的只是巧合。變異檢驗全部在這一組——把規則改壞，
  對應測試必須轉紅。
- **真實 repo**：釘住五個已知實例的判定（本卡的正控組）。五個都在，才證明對帳器在量
  東西而不是在印空表。

⚠️ 本檔**不含**任何「預期的符號清單」。合成樹的斷言問的是「我剛寫進文件的這個新符號有
沒有出現」，不是「universe 應該恰好等於這 N 個」——後者會變成第二份人維護清單，正是本卡
要消滅的形狀。
"""

from __future__ import annotations

import importlib.util
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts" / "contract_tool_reconcile.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("contract_tool_reconcile", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


ctr = _load_module()


# ==========================================================================
# 合成樹：一棵我完全控制內容的最小 repo
# ==========================================================================

_GH_PY = '''
class GhRunner:
    def execute(self, args, input=None):
        return ""

    def run_json(self, args):
        return {}
'''

_PROJECT_PY = '''
FIELD_SPECS = {
    "交付狀態": (
        "SINGLE_SELECT",
        ("🔨執行中", "🔍待查核", "⏸阻塞"),
    ),
}


def set_item_body(runner, body):
    runner.execute(["issue", "edit", "1", "--body", body])
'''

_RESOURCES_PY = '''
_SECTION_HEADING = "## 資源宣告"


def render_block(decl):
    return _SECTION_HEADING + "\\n" + str(decl)


def find_conflicts(mine, other_id, other):
    return []
'''

_CARD_PY = '''
_CORE_PAIN_HEADING = "## 核心痛點"
_REQUESTED_BY_RE = "^- 需求：(?P<r>.*)　規劃：(?P<p>.*)$"

from .resources import render_block


def render_issue_body(c):
    return f"""- 需求：{c.requested_by}　規劃：{c.planned_by}

{_CORE_PAIN_HEADING}

{render_block(c.resources)}
"""


def parse_requested_by(body):
    import re
    return re.match(_REQUESTED_BY_RE, body)


def amend_core_pain(body, new_value):
    return body.replace(_CORE_PAIN_HEADING, _CORE_PAIN_HEADING), ""
'''

_OPEN_CMD_PY = '''
from ..card import render_issue_body
from ..project import set_item_body


def run(args):
    body = render_issue_body(args.card)
    set_item_body(args.runner, body)
    return 0


def add_parser(subparsers):
    subparsers.add_parser("open", help="開卡")
'''

_AMEND_CMD_PY = '''
from ..card import amend_core_pain, parse_requested_by
from ..resources import render_block
from ..project import set_item_body


def run(args):
    body, _old = amend_core_pain(args.body, args.new)
    body = body + render_block(args.resources)
    parse_requested_by(body)
    set_item_body(args.runner, body)
    return 0


def add_parser(subparsers):
    subparsers.add_parser("amend", help="改卡面")
'''

_REVIEW_CMD_PY = '''
import sys

from ..project import set_item_body


def run(args):
    if args.invalid:
        # review-invalid 在契約 §1 是獨立層次
        print("[review] 拒收（review-invalid，不計 iteration）", file=sys.stderr)
        return 4
    set_item_body(args.runner, "已裁決")
    return 0


def add_parser(subparsers):
    subparsers.add_parser("review", help="查核裁決")
'''

_CANONICAL = """\
# 契約

事件：`preflight-failed`、`review-invalid`、`ghost-event`。
狀態：🔨執行中 / 🔍待查核 / ⏸阻塞。
"""

_TASKS_CARD = """\
# <卡ID> <功能名>

- 需求：<帳號>　規劃：<模型>
- 幽靈欄：<這個欄位契約有、工具沒有>

## 核心痛點

- **痛點**：<一句話>

## 資源宣告

<!-- resource-claims:begin -->
"""

_ROADMAP = """\
# Roadmap

- `roadmap-only-symbol` 尚未實作。
"""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def synthetic_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    _write(root / "AI_WORKFLOW.md", _CANONICAL)
    _write(root / "templates" / "tasks-card.md", _TASKS_CARD)
    _write(root / "docs" / "ROADMAP.md", _ROADMAP)
    src = root / "cli" / "src" / "wf_cli"
    _write(src / "gh.py", _GH_PY)
    _write(src / "project.py", _PROJECT_PY)
    _write(src / "resources.py", _RESOURCES_PY)
    _write(src / "card.py", _CARD_PY)
    _write(src / "commands" / "open_cmd.py", _OPEN_CMD_PY)
    _write(src / "commands" / "amend_cmd.py", _AMEND_CMD_PY)
    _write(src / "commands" / "review_cmd.py", _REVIEW_CMD_PY)
    return root


def _row(rec, kind: str, name: str):
    for r in rec.rows:
        if r.kind == kind and r.name == name:
            return r
    raise AssertionError(f"對帳表沒有 {kind}/{name}；實際有 {[(x.kind, x.name) for x in rec.rows]}")


def _has_row(rec, kind: str, name: str) -> bool:
    return any(r.kind == kind and r.name == name for r in rec.rows)


# ==========================================================================
# 驗收條 5：universe 由掃描文件導出，不得由人登記
# ==========================================================================


def test_new_symbol_in_canonical_appears_without_touching_the_tool(synthetic_repo: Path):
    """⚠️ 變異檢驗（驗收條 5 的主檢）。

    在契約文件加一個從未出現過的符號，重跑後它必須進表。**若有人把 universe 改成人登記
    的清單，這個測試立刻轉紅**——那份清單裡不會有 ``brand-new-contract-event``。

    什麼結果會讓這個檢查不成立：若對帳器對「文件裡新增的符號」與「文件裡沒有的符號」給
    出相同輸出（都出現或都不出現），它就沒有在讀文件。下一個測試釘反方向。
    """
    assert not _has_row(ctr.reconcile(synthetic_repo), "event", "brand-new-contract-event")

    doc = synthetic_repo / "AI_WORKFLOW.md"
    doc.write_text(
        doc.read_text(encoding="utf-8") + "\n新事件：`brand-new-contract-event`。\n",
        encoding="utf-8",
    )

    row = _row(ctr.reconcile(synthetic_repo), "event", "brand-new-contract-event")
    assert row.verdict == ctr.VERDICT_ABSENT
    assert row.is_gap


def test_removing_a_symbol_from_docs_removes_it_from_the_table(synthetic_repo: Path):
    """反方向：契約不再提，符號就該離開 universe（否則它是被人記住的，不是掃出來的）。"""
    assert _has_row(ctr.reconcile(synthetic_repo), "event", "ghost-event")
    doc = synthetic_repo / "AI_WORKFLOW.md"
    doc.write_text(doc.read_text(encoding="utf-8").replace("、`ghost-event`", ""), encoding="utf-8")
    assert not _has_row(ctr.reconcile(synthetic_repo), "event", "ghost-event")


def test_template_scope_is_globbed_not_enumerated(synthetic_repo: Path):
    """新增一份範本檔就該自動進射程；若射程是寫死的檔名清單，這裡會紅。"""
    assert not _has_row(ctr.reconcile(synthetic_repo), "event", "symbol-from-new-template")
    _write(
        synthetic_repo / "templates" / "brand-new-template.md",
        "# 新範本\n\n事件：`symbol-from-new-template`。\n",
    )
    assert _has_row(ctr.reconcile(synthetic_repo), "event", "symbol-from-new-template")


def test_card_field_universe_comes_from_the_template(synthetic_repo: Path):
    """卡面欄位同樣掃出來：範本裡的「幽靈欄」工具完全沒有，必須以缺口現身。"""
    row = _row(ctr.reconcile(synthetic_repo), "card_field", "幽靈欄")
    assert row.verdict == ctr.VERDICT_ABSENT
    assert "open 渲染=否" in row.notes
    assert "amend 可改=否" in row.notes


def test_roadmap_is_in_scope(synthetic_repo: Path):
    assert _has_row(ctr.reconcile(synthetic_repo), "event", "roadmap-only-symbol")


# ==========================================================================
# 變異檢驗：writer 判定量的是「進不進得了狀態面」，不是「grep 得不得到」
# ==========================================================================


def test_symbol_only_inside_print_is_not_a_writer(synthetic_repo: Path):
    """``review-invalid`` 的字面**確實在** ``review_cmd.py`` 裡——在 ``print()`` 的引數裡。

    什麼結果會讓這個檢查不成立：若對帳器把它判成 writer，它量的就是 grep 而不是留痕。
    """
    row = _row(ctr.reconcile(synthetic_repo), "event", "review-invalid")
    assert row.verdict == ctr.VERDICT_MENTION_ONLY
    assert row.writers == []
    assert any("review_cmd.py" in o.path for o in row.mentions)


def test_same_symbol_becomes_a_writer_when_it_reaches_the_state_plane(synthetic_repo: Path):
    """把同一個符號從 ``print()`` 搬到寫入路徑上，判定必須翻面。

    這是上一個測試的成對變異：只有「同一個符號、只改位置、判定就改變」才證明判準抓的是
    位置而不是字串存在與否。兩個測試少任何一個都證不出這件事。
    """
    cmd = synthetic_repo / "cli" / "src" / "wf_cli" / "commands" / "review_cmd.py"
    cmd.write_text(
        cmd.read_text(encoding="utf-8").replace(
            'set_item_body(args.runner, "已裁決")',
            'set_item_body(args.runner, "- event: review-invalid")',
        ),
        encoding="utf-8",
    )
    row = _row(ctr.reconcile(synthetic_repo), "event", "review-invalid")
    assert row.verdict != ctr.VERDICT_MENTION_ONLY
    assert row.writers, "搬到寫入路徑後仍判成沒有 writer"


def test_comment_only_symbol_is_not_a_writer(synthetic_repo: Path):
    """只寫在 ``#`` 註解裡的符號不算實作（``preflight-failed`` 在真 repo 正是這個形狀）。"""
    card = synthetic_repo / "cli" / "src" / "wf_cli" / "card.py"
    card.write_text("# 提到 preflight-failed 而已\n" + card.read_text(encoding="utf-8"), "utf-8")
    row = _row(ctr.reconcile(synthetic_repo), "event", "preflight-failed")
    assert row.verdict == ctr.VERDICT_MENTION_ONLY
    assert row.writers == []


def test_word_boundary_prevents_substring_false_positive(synthetic_repo: Path):
    """``deployment-status-change`` 不得讓 ``status-change`` 看起來有 writer。"""
    doc = synthetic_repo / "AI_WORKFLOW.md"
    doc.write_text(doc.read_text(encoding="utf-8") + "\n事件：`status-change`。\n", "utf-8")
    cmd = synthetic_repo / "cli" / "src" / "wf_cli" / "commands" / "review_cmd.py"
    cmd.write_text(
        cmd.read_text(encoding="utf-8").replace(
            'set_item_body(args.runner, "已裁決")',
            'set_item_body(args.runner, "- event: deployment-status-change")',
        ),
        encoding="utf-8",
    )
    row = _row(ctr.reconcile(synthetic_repo), "event", "status-change")
    assert row.writers == []
    assert row.verdict == ctr.VERDICT_ABSENT


def test_full_width_colon_does_not_make_card_fields_look_like_prose(synthetic_repo: Path):
    """``- 需求：`` 的分隔符是全形冒號。只看字寬會把每個卡面欄位判成散文而失去 writer。"""
    row = _row(ctr.reconcile(synthetic_repo), "card_field", "需求")
    assert row.writers, "卡面欄位在 render_issue_body 裡卻被判成沒有 writer"
    assert "open 渲染=是" in row.notes


# ==========================================================================
# 變異檢驗：amend 可改性由 AST 導出
# ==========================================================================


def test_field_read_by_a_parser_is_not_thereby_amendable(synthetic_repo: Path):
    """``需求`` 的錨點常數存在，但只被讀取器引用 → 不可 amend（已知缺口 #5 的形狀）。"""
    row = _row(ctr.reconcile(synthetic_repo), "card_field", "需求")
    assert "amend 可改=否" in row.notes
    assert "⚠️ 開卡寫得進、開卡後改不動" in row.notes


def test_adding_an_amend_function_flips_amendability(synthetic_repo: Path):
    """新增一個 ``amend_requested_by`` 並讓 ``amend_cmd`` import 它，判定必須翻面。

    什麼結果會讓這個檢查不成立：若加了 amend 函式判定仍是「改不動」，那個欄位軸讀的
    就不是碼。
    """
    card = synthetic_repo / "cli" / "src" / "wf_cli" / "card.py"
    card.write_text(
        card.read_text(encoding="utf-8")
        + "\n\ndef amend_requested_by(body, new_value):\n"
        "    import re\n"
        "    return re.sub(_REQUESTED_BY_RE, new_value, body), ''\n",
        encoding="utf-8",
    )
    amend = synthetic_repo / "cli" / "src" / "wf_cli" / "commands" / "amend_cmd.py"
    amend.write_text(
        amend.read_text(encoding="utf-8").replace(
            "from ..card import amend_core_pain, parse_requested_by",
            "from ..card import amend_core_pain, amend_requested_by, parse_requested_by",
        ),
        encoding="utf-8",
    )
    row = _row(ctr.reconcile(synthetic_repo), "card_field", "需求")
    assert "amend 可改=是" in row.notes
    assert "⚠️ 開卡寫得進、開卡後改不動" not in row.notes


# ==========================================================================
# 變異檢驗：狀態的「專責動詞」軸
# ==========================================================================


def test_status_declared_as_option_but_with_no_verb_is_a_gap(synthetic_repo: Path):
    """``⏸阻塞`` 只出現在 ``FIELD_SPECS``：選項有、沒有動詞轉得進去。"""
    row = _row(ctr.reconcile(synthetic_repo), "delivery_status", "⏸阻塞")
    assert row.verdict == ctr.VERDICT_READ_ONLY
    assert "Project 選項=是" in row.notes
    assert "專責動詞=否" in row.notes


def test_status_with_a_verb_is_not_a_gap(synthetic_repo: Path):
    """同一個狀態一旦有動詞拿它當值，判定必須翻面——證明上一條量的是動詞不是列舉。"""
    cmd = synthetic_repo / "cli" / "src" / "wf_cli" / "commands" / "amend_cmd.py"
    cmd.write_text(
        cmd.read_text(encoding="utf-8").replace(
            'subparsers.add_parser("amend", help="改卡面")',
            'p = subparsers.add_parser("amend", help="改卡面")\n'
            '    p.add_argument("--status", default="⏸阻塞")',
        ),
        encoding="utf-8",
    )
    row = _row(ctr.reconcile(synthetic_repo), "delivery_status", "⏸阻塞")
    assert "專責動詞=是" in row.notes
    assert row.verdict == ctr.VERDICT_OK


# ==========================================================================
# 變異檢驗：守衛覆蓋與呼叫圖精確度
# ==========================================================================


def test_writer_that_skips_the_guard_is_reported(synthetic_repo: Path):
    """``amend_cmd`` import 了 ``render_block`` 卻到不了 ``find_conflicts`` → 缺口。"""
    rec = ctr.reconcile(synthetic_repo)
    hits = [g for g in rec.guard_gaps if g.writer.endswith("amend_cmd.py") and g.module == "resources"]
    assert hits, f"沒抓到 amend_cmd 的守衛覆蓋缺口；實際：{rec.guard_gaps}"
    assert "find_conflicts" in hits[0].guard


def test_calling_the_guard_clears_the_gap(synthetic_repo: Path):
    """接上守衛後缺口必須消失——否則這個檢查對「有沒有跑守衛」沒有鑑別力。"""
    cmd = synthetic_repo / "cli" / "src" / "wf_cli" / "commands" / "amend_cmd.py"
    cmd.write_text(
        cmd.read_text(encoding="utf-8")
        .replace("from ..resources import render_block", "from ..resources import find_conflicts, render_block")
        .replace("    parse_requested_by(body)", "    parse_requested_by(body)\n    find_conflicts([], '', None)"),
        encoding="utf-8",
    )
    rec = ctr.reconcile(synthetic_repo)
    assert not [
        g for g in rec.guard_gaps if g.writer.endswith("amend_cmd.py") and g.module == "resources"
    ]


def test_unresolvable_calls_do_not_create_call_graph_edges(synthetic_repo: Path):
    """呼叫圖不得靠「同名全集」連邊。

    真 repo 上那條退路讓 ``gh.execute`` 裡的 ``subprocess.run`` 連到 ``assign_cmd.run``，
    於是 amend 憑空「到得了」``find_conflicts``，已知缺口 #4 被藏住。這裡直接釘住：一個
    只呼叫外部名字的函式，不得多出任何指向本專案函式的邊。
    """
    src = synthetic_repo / "cli" / "src" / "wf_cli" / "extra.py"
    src.write_text("def helper():\n    return run()\n", encoding="utf-8")
    modules = ctr.load_modules(synthetic_repo)
    graph = ctr.build_call_graph(modules)
    assert graph.edges["extra.helper"] == set()


# ==========================================================================
# --check：漏掃的後果必須是可見失敗
# ==========================================================================


def _write_dispositions(root: Path, mapping: dict[str, str]) -> None:
    import json

    body = json.dumps({"gaps": mapping}, ensure_ascii=False, indent=2)
    _write(
        root / ctr.DISPOSITION_DOC,
        f"# 處置\n\n{ctr.DISPOSITION_BEGIN}\n```json\n{body}\n```\n{ctr.DISPOSITION_END}\n",
    )


def _run_check(root: Path) -> tuple[int, str]:
    rec = ctr.reconcile(root)
    err = io.StringIO()
    out = io.StringIO()
    with redirect_stdout(out):
        code = ctr.run_check(root, rec, stream=err)
    return code, err.getvalue() + out.getvalue()


def test_check_is_red_when_dispositions_are_missing_entirely(synthetic_repo: Path):
    code, text = _run_check(synthetic_repo)
    assert code == 1
    assert "缺口未登記處置" in text


def test_check_is_green_when_every_gap_is_registered(synthetic_repo: Path):
    rec = ctr.reconcile(synthetic_repo)
    _write_dispositions(synthetic_repo, ctr.all_gap_entries(rec))
    code, text = _run_check(synthetic_repo)
    assert code == 0, text


def test_deleting_a_registered_gap_does_not_turn_check_green(synthetic_repo: Path):
    """⚠️ 這條是「處置表不是人維護清單」的關鍵不對稱。

    處置表能做的只有**承認**缺口，不能**消除**缺口：刪掉一列，該缺口立刻變成「未登記」
    而檢查轉紅。三個方向（漏登記／登記了不存在的／判定變了）都紅，見以下三個測試。
    """
    rec = ctr.reconcile(synthetic_repo)
    mapping = ctr.all_gap_entries(rec)
    victim = sorted(mapping)[0]
    del mapping[victim]
    _write_dispositions(synthetic_repo, mapping)
    code, text = _run_check(synthetic_repo)
    assert code == 1
    assert victim in text


def test_check_is_red_for_a_registered_gap_that_no_longer_exists(synthetic_repo: Path):
    rec = ctr.reconcile(synthetic_repo)
    mapping = ctr.all_gap_entries(rec)
    mapping["event/a-gap-that-was-fixed"] = ctr.VERDICT_ABSENT
    _write_dispositions(synthetic_repo, mapping)
    code, text = _run_check(synthetic_repo)
    assert code == 1
    assert "登記了已不存在的缺口" in text


def test_check_is_red_when_a_verdict_changes(synthetic_repo: Path):
    rec = ctr.reconcile(synthetic_repo)
    mapping = ctr.all_gap_entries(rec)
    victim = sorted(mapping)[0]
    mapping[victim] = "some-other-verdict"
    _write_dispositions(synthetic_repo, mapping)
    code, text = _run_check(synthetic_repo)
    assert code == 1
    assert "判定變了" in text


def test_guard_gaps_are_covered_by_check(synthetic_repo: Path):
    """守衛覆蓋缺口也必須進 ratchet。

    ⚠️ 這條是變異檢驗 M3 抓出來的洞：第一版 ``--check`` 只比對符號列，於是把呼叫圖退回
    「同名全集」讓已知缺口 #4 整個消失時，``--check`` **仍然是綠的**。沒被 ratchet 蓋住
    的檢查等於沒有檢查。

    什麼結果會讓這個檢查不成立：接上守衛使缺口消失後 ``--check`` 仍是綠的——那表示守衛
    覆蓋沒有被登記面觀測到。
    """
    rec = ctr.reconcile(synthetic_repo)
    assert any(k.startswith("guard/") for k in ctr.all_gap_entries(rec))
    _write_dispositions(synthetic_repo, ctr.all_gap_entries(rec))
    assert _run_check(synthetic_repo)[0] == 0

    cmd = synthetic_repo / "cli" / "src" / "wf_cli" / "commands" / "amend_cmd.py"
    cmd.write_text(
        cmd.read_text(encoding="utf-8")
        .replace(
            "from ..resources import render_block",
            "from ..resources import find_conflicts, render_block",
        )
        .replace(
            "    parse_requested_by(body)",
            "    parse_requested_by(body)\n    find_conflicts([], '', None)",
        ),
        encoding="utf-8",
    )
    code, text = _run_check(synthetic_repo)
    assert code == 1
    assert "登記了已不存在的缺口" in text
    assert "amend_cmd.py" in text


def test_check_is_red_when_a_new_contract_symbol_appears_unregistered(synthetic_repo: Path):
    """契約長出新東西而沒人處置 → 可見失敗。這正是「漏掃不得靜默通過」的操作面。"""
    rec = ctr.reconcile(synthetic_repo)
    _write_dispositions(synthetic_repo, ctr.all_gap_entries(rec))
    assert _run_check(synthetic_repo)[0] == 0
    doc = synthetic_repo / "AI_WORKFLOW.md"
    doc.write_text(doc.read_text(encoding="utf-8") + "\n`unregistered-newcomer` 上線了。\n", "utf-8")
    code, text = _run_check(synthetic_repo)
    assert code == 1
    assert "event/unregistered-newcomer" in text


def test_check_does_not_read_the_clock(synthetic_repo: Path):
    """同一棵樹連跑兩次結果必須逐位相同。

    什麼結果會讓這個檢查不成立：若把 ``as_of = date.today()`` 之類的東西納入比對，這個
    測試在跨午夜時仍會綠（同一秒跑兩次），所以它**不夠**——真正的保證是原始碼裡沒有
    時鐘呼叫，由下一個測試釘住。
    """
    rec = ctr.reconcile(synthetic_repo)
    _write_dispositions(synthetic_repo, ctr.all_gap_entries(rec))
    assert _run_check(synthetic_repo) == _run_check(synthetic_repo)


def test_reconciler_source_contains_no_clock_calls():
    """對帳器不得讀牆上時鐘——否則它會有「明天起每天必紅」的那種假檢查。"""
    src = _SCRIPT.read_text(encoding="utf-8")
    for forbidden in ("datetime.now", "date.today", "time.time", "utcnow"):
        assert forbidden not in src, f"對帳器出現時鐘呼叫 {forbidden}"


# ==========================================================================
# 真實 repo：本卡的五個正控組
# ==========================================================================


@pytest.fixture(scope="module")
def live():
    return ctr.reconcile(_REPO_ROOT)


def test_control_1_review_invalid_has_no_writer(live):
    row = _row(live, "event", "review-invalid")
    assert row.verdict == ctr.VERDICT_MENTION_ONLY
    assert row.writers == []
    assert any("review_cmd.py" in o.path for o in row.mentions)


def test_control_2_preflight_failed_has_no_writer(live):
    row = _row(live, "event", "preflight-failed")
    assert row.verdict == ctr.VERDICT_MENTION_ONLY
    assert row.writers == []
    assert "相關動詞=無" in row.notes


def test_control_3_blocked_status_has_no_verb(live):
    row = _row(live, "delivery_status", "⏸阻塞")
    assert row.verdict == ctr.VERDICT_READ_ONLY
    assert "Project 選項=是" in row.notes
    assert "專責動詞=否" in row.notes
    # 契約 §1 另有 status-change → ⏸阻塞 這個事件名，工具側連字面都沒有。
    assert _row(live, "event", "status-change").verdict == ctr.VERDICT_ABSENT


def test_control_4_amend_can_write_resources_without_running_find_conflicts(live):
    hits = [
        g
        for g in live.guard_gaps
        if g.writer.endswith("commands/amend_cmd.py") and g.module == "resources"
    ]
    assert hits, f"沒抓到 amend 繞過 find_conflicts；實際：{live.guard_gaps}"
    assert "find_conflicts" in hits[0].guard
    assert "render_block" in hits[0].serializer


def test_control_5_card_field_universe_is_empty_until_the_fenced_json_card_face_lands(live):
    """原正控組 5（``需求`` 欄：開卡寫得進、開卡後改不動）**在真 repo 上已無標的**。

    ``WF-REDESIGN-W2B`` 移除了 ``templates/*card*.md`` 三份範本（`tasks-card.md`／
    `bug-card.md`／`initiative-card.md`），而 :data:`ctr.CARD_TEMPLATE_GLOB` 是 ``card_field``
    universe 的**唯一**來源 ⇒ 該 kind 整類離開對帳表，``_row(live, "card_field", "需求")``
    不再有東西可取。

    ⭐ **這是對帳器的盲區，⛔ 不是「卡面欄位契約消失了」。** 契約仍在，只是搬到本對帳器
    看不到的地方：``cli/src/wf_cli/card_face.py`` 的 ``card-face-form:v1`` 已實作並在跑，
    卡面 body 逐張帶 ``resource-claims``／``card-face-form:v1``／``card-brief``／``wf-routing:v1``。
    ⇒ **本對帳器現在對「卡面欄位」這一軸沒有覆蓋，而它⛔ 不會因此轉紅**——``--check`` 只比對
    「缺口有沒有登記」，一個不存在的 kind 沒有缺口可登記。⛔ 不得把下面兩條 assert 的綠燈
    讀成「覆蓋還在」；它們釘的只是「這個盲區是刻意的、而且會在範本回歸時喊」。

    ⛔ **這不是把控制組刪掉，是把它換成一條會響的 ratchet。** 本測試現在釘的是
    「card_field 是空的，而且空得有機械理由」：

    - 若有人在 ``templates/`` 下再放一份 ``*card*.md``（例如 ``WF-REDESIGN-W3`` 落地
      卡面 fenced JSON 的 schema 範本），下面兩條 assert **當場轉紅**，逼那張卡回來把
      真 repo 的 card_field 正控組重新建立起來——⛔ 不會靜默地少一組控制。
    - 反之，若對帳器自己壞掉而讓 card_field 憑空消失，``card_templates()`` 仍會回傳
      非空清單 ⇒ 第一條 assert 抓得到。兩條分開寫就是為了分辨這兩種成因。

    ⚠️ **誠實登記**：在 ``WF-REDESIGN-W3`` 之前，「open 寫得進／amend 改不動」這組
    **真 repo** 上的正控組不存在；同名判定的鑑別力只剩合成 repo 那幾條
    （``test_field_read_by_a_parser_is_not_thereby_amendable``／
    ``test_adding_an_amend_function_flips_amendability``）。⛔ 不得把本測試通過讀成
    「那組控制仍在跑」。
    """
    assert ctr.card_templates(_REPO_ROOT) == [], (
        "templates/ 下又出現 *card*.md ⇒ card_field universe 已恢復，"
        "請把真 repo 的正控組（開卡寫得進、開卡後改不動）一併重建"
    )
    assert [r for r in live.rows if r.kind == ctr.KIND_FIELD] == []


def test_live_table_is_not_vacuous(live):
    """正控組的另一半：表上必須同時存在「有實作」與「缺口」的列。

    全綠或全紅的表都沒有鑑別力。這條釘住**表上實際存在的每一個 kind** 各至少有一列判定為
    ``ok``、也至少有一列是缺口——若某次改動讓判定塌成單一值，這裡會紅。

    ⚠️ **``card_field`` 自 ``WF-REDESIGN-W2B`` 起不在母體內**（成因與 ratchet 見
    ``test_control_5_card_field_universe_is_empty_until_the_fenced_json_card_face_lands``）。
    ⛔ 母體改成「表上實際存在的 kind」而不是寫死三個，是為了讓本條在那之後仍有鑑別力；
    ⛔ 不得由此推出「kind 少一個沒關係」——少了哪一個由上面那條專門的測試負責喊。
    """
    kinds = sorted({r.kind for r in live.rows})
    assert kinds == sorted({ctr.KIND_STATUS, ctr.KIND_EVENT}), f"表上的 kind 集合變了：{kinds}"
    for kind in kinds:
        ok = [r for r in live.rows if r.kind == kind and r.verdict == ctr.VERDICT_OK]
        gaps = [r for r in live.rows if r.kind == kind and r.is_gap]
        assert ok, f"{kind} 沒有任何判定為 ok 的列，對帳器可能整體失效"
        assert gaps, f"{kind} 沒有任何缺口"


def test_live_dispositions_cover_every_gap():
    """真 repo 上 ``--check`` 必須是綠的：每個缺口都已在文件登記處置。"""
    rec = ctr.reconcile(_REPO_ROOT)
    code, text = _run_check(_REPO_ROOT)
    assert code == 0, f"{len(rec.gaps)} 個缺口與登記處置不符：\n{text}"
