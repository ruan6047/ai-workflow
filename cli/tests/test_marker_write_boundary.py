"""WF-MARKER-WRITE-BOUNDARY1：卡面寫入邊界的兩條性質。

規範依據 ``templates/handoff-contract.md`` §3.2，其機械形式逐字為
「**序列化成功 ⟹ 解析成功，且回傳逐字相同的值。**」判準見 ``card.enforce_write_boundary``：

  (1) **差分結構探測**——讀取路徑在寫入前後各跑一次，寫入前讀得回、寫入後讀不回 ⇒ 拒收；
  (2) **值往返逐位元比對**——讀取端讀回的值必須 ``==`` 寫進去的值。

⭐ **本檔同時是「讀取路徑清單」的導出程式**（A1 逐字要求清單由可重跑的程式產生、
⛔ 不得手打）。直接執行即印出當次命中的清單：

    cd cli && uv run python -m tests.test_marker_write_boundary

（⚠️ 必須用 ``-m``：本檔對 ``tests.fake_gh`` 有相對匯入，直接跑檔名會 ImportError。）

⚠️ **非宣稱（逐字，⛔ 不得放大）**：本檔與本守衛涵蓋的是
``card.body_read_paths()`` **當次導出命中的那組讀取路徑**，⛔ **不宣稱涵蓋全部讀取端**；
兩條性質是單欄位性質，⛔ **不涵蓋跨欄位不變量**（見本檔末 ``V7 未涵蓋類別`` 一節）。
"""

from __future__ import annotations

import dataclasses
import sys

import pytest

from wf_cli.card import (
    AmendError,
    Card,
    MarkerWriteBoundaryError,
    _append_log_line_raw,
    _flatten_line_structure,
    _read_brief_text,
    _read_checklist_texts,
    amend_acceptance,
    amend_brief,
    amend_core_pain,
    amend_initiative,
    amend_resource_block,
    amend_spec_baseline,
    amend_verification,
    append_log_line,
    body_read_paths,
    enforce_write_boundary,
    parse_requested_by,
    render_issue_body,
    restore_migration_header,
    split_at_log,
)
from wf_cli import doctor
from wf_cli.cli import build_parser, main as cli_main
from wf_cli.commands import amend_cmd, open_cmd
from wf_cli.project import find_item_by_card_id, list_items, resolve_project
from wf_cli.resources import ResourceDeclaration, render_block

from .fake_gh import FakeGhRunner

# --------------------------------------------------------------------------
# 導出程式：讀取路徑清單
# --------------------------------------------------------------------------


def export_read_paths() -> list[str]:
    """當次命中的讀取路徑限定名（偵測條件見 ``card.body_read_paths`` 的 docstring）。"""
    return [name for name, _ in body_read_paths()]


def export_line_separators() -> list[str]:
    """``str.splitlines()`` 認得的**單字元**分行符——由 ``splitlines`` 自身窮舉導出。

    ⛔ **不是手打清單**：逐一試遍整個 Unicode 碼位空間，問 ``splitlines`` 自己。
    ⚠️ CRLF 是**雙字元序列**，⛔ 不在本清單內，另由 ``test_crlf_...`` 單獨驗。
    """
    return [
        chr(i)
        for i in range(sys.maxunicode + 1)
        if len(("a" + chr(i) + "b").splitlines()) > 1
    ]


_SEPARATORS = export_line_separators()


# --------------------------------------------------------------------------
# 全母體普查 harness（V4／V8：完整性宣稱必須由 artifact 產生）
# --------------------------------------------------------------------------
#
# ⭐ **為什麼 harness 在測試檔裡而不是另立腳本**：
# (a) 現在的行為：分類器 :func:`census` 是純函式，pytest 每次都跑得到
#     （``test_census_harness_*``）；打真實看板的那一半由 ``--census`` 手動叫。
# (b) 為什麼：canonical §6.2 要求完整性數字**由 artifact 產生**，⇒ 產生器必須進版控。
#     而本卡的資源宣告只含 ``cli/tests/test_card.py`` 與本檔兩個測試檔（新增第三個
#     檔案等於改未宣告的資源，A10 逐字要求停下來）⇒ 放這裡是**授權邊界內唯一**
#     既進版控、又被 pytest 收得到的位置。``testpaths = ["tests"]`` 收本檔。
# (c) ⛔ **不得由此推出「跑 pytest 就等於跑過普查」**——沒有。pytest 跑的是分類器；
#     母體數字要跑 ``--census``，它需要 gh 認證與網路。


@dataclasses.dataclass(frozen=True)
class Cell:
    """普查的一格：一張卡 × 一個寫入動詞。"""

    card_id: str
    verb: str
    verdict: str
    detail: str = ""


#: 進分母的判定。⛔ 其餘一律具名排除，⛔ 不得默默併入分子或分母。
COUNTED_VERDICTS = ("intercepted", "intercepted_by_legacy_check", "leaked")

_INJ = "\u2028## Log"
_CENSUS_TS = "2026-08-27T00:00:00+08:00"


def _census_verbs():
    """``(動詞名, 乾淨值寫入, 注入值寫入)``；兩者只差在值裡多一段分行結構。

    ⛔ 刻意讓乾淨值與注入值**共用同一個寫入函式**：控制組若走另一條路徑，
    「不合格樣本走到另一條錯誤路徑而看起來像攔截」那個病就會回來（V4 逐字）。
    """
    def block(tag: str) -> str:
        return render_block(ResourceDeclaration(db_scope="none", resources=[f"file:{tag}"]))

    return (
        ("amend --acceptance",
         lambda b: amend_acceptance(b, ["普查控制組條件"]),
         lambda b: amend_acceptance(b, [f"普查注入條件{_INJ}"])),
        ("amend --verification",
         lambda b: amend_verification(b, ["普查控制組驗證"]),
         lambda b: amend_verification(b, [f"普查注入驗證{_INJ}"])),
        ("amend --core-pain",
         lambda b: amend_core_pain(b, "普查控制組痛點"),
         lambda b: amend_core_pain(b, f"普查注入痛點{_INJ}")),
        ("amend --initiative",
         lambda b: amend_initiative(b, "普查控制組父卡"),
         lambda b: amend_initiative(b, f"普查注入父卡{_INJ}")),
        ("amend --spec-baseline",
         lambda b: amend_spec_baseline(b, "普查控制組基線"),
         lambda b: amend_spec_baseline(b, f"普查注入基線{_INJ}")),
        ("amend --brief",
         lambda b: amend_brief(b, _GOOD_BRIEF),
         lambda b: amend_brief(b, f"{_GOOD_BRIEF}{_INJ}")),
        ("amend --resources",
         lambda b: amend_resource_block(b, block("census-control.py")),
         lambda b: amend_resource_block(b, block(f"census-inject{_INJ}y.py"))),
        ("append_log_line（assign／handoff／review／checkpoint）",
         lambda b: append_log_line(b, f"{_CENSUS_TS} 普查控制組"),
         lambda b: append_log_line(b, f"{_CENSUS_TS} 普查注入{_INJ}- 偽造")),
        # ⭐ 第 9 個動詞刻意**不用分行字元**：它注入的是一整行合法的 `- 需求：…` ——
        # 差分探測靠 `parse_requested_by` 讀不回而擋下它。⛔ 少了這一格，普查就量不到
        # V4 逐字登記的那個預壞控制組（需求欄是 `—` 佔位的卡，該路徑寫入前就已讀不回）。
        ("amend --brief（獨立成行的需求行）",
         lambda b: amend_brief(b, _GOOD_BRIEF),
         lambda b: amend_brief(b, _BRIEF_WITH_STANDALONE_REQUESTER_LINE)),
    )


@dataclasses.dataclass
class Census:
    """普查結果。⛔ 每個數字都由 :attr:`cells` 導出，⛔ 沒有手打的計數器。"""

    cells: list[Cell] = dataclasses.field(default_factory=list)
    #: 具名的預壞控制組：``(card_id, 寫入前就讀不回的讀取路徑)``。⛔ 排除於分母之外。
    pre_broken: list[tuple[str, tuple[str, ...]]] = dataclasses.field(default_factory=list)
    cards: int = 0

    def _by(self, verdict: str) -> list[Cell]:
        return [c for c in self.cells if c.verdict == verdict]

    @property
    def denominator(self) -> list[Cell]:
        return [c for c in self.cells if c.verdict in COUNTED_VERDICTS]

    @property
    def leaked(self) -> list[Cell]:
        return self._by("leaked")

    @property
    def control_passed(self) -> list[Cell]:
        """⚠️ V4 逐字：**只報攔截率是零資訊**——不合格樣本會走到另一條錯誤路徑而看起來
        像攔截。⇒ 必須同時報「有多少格的乾淨值真的寫得進去」。"""
        return [
            c for c in self.cells
            if c.verdict not in ("control_unusable", "control_false_positive")
        ]

    @property
    def control_false_positive(self) -> list[Cell]:
        return self._by("control_false_positive")

    @property
    def interception_rate(self) -> float:
        total = len(self.denominator)
        return 1.0 if total == 0 else (total - len(self.leaked)) / total

    def summary(self) -> str:
        lines = [
            f"卡數：{self.cards}",
            f"預壞控制組（具名排除於分母之外）：{len(self.pre_broken)} 張",
        ]
        for card_id, paths in self.pre_broken:
            lines.append(
                f"  - {card_id}：比健康卡多跳過 {'、'.join(paths)}"
                "（守衛的差分閘門因此對它沉默）"
            )
        lines.append(f"逐格總數：{len(self.cells)}")
        for verdict in sorted({c.verdict for c in self.cells}):
            mark = "（進分母）" if verdict in COUNTED_VERDICTS else "（具名排除）"
            lines.append(f"  {verdict}{mark}：{len(self._by(verdict))}")
        lines.append(
            f"控制組通過數：{len(self.control_passed)}"
            f"（＝進分母 {len(self.denominator)} ＋ 具名預壞 {len(self._by('excluded_pre_broken'))}）"
        )
        lines.append(f"分母：{len(self.denominator)}　漏網：{len(self.leaked)}")
        lines.append(f"控制組偽陽性：{len(self.control_false_positive)}（目標 0）")
        lines.append(f"注入攔截率：{self.interception_rate * 100:.4f}%（目標 100%）")
        for cell in self.leaked + self.control_false_positive:
            lines.append(f"  ⛔ {cell.card_id} / {cell.verb} / {cell.verdict}：{cell.detail}")
        return "\n".join(lines)


@dataclasses.dataclass(frozen=True)
class GuardTrace:
    """守衛在**這一次**寫入上實際做了什麼。

    ⭐ **這是分類器分辨「真漏網」與「預壞而被跳過」的唯一依據，⛔ 不是推想**：
    A1 的兩條性質都是**差分閘門**——寫入前就讀不回的讀取路徑一律跳過、寫入前就讀不回
    的往返讀回器也一律跳過。⇒ 一張既有損壞的卡上，注入可能**依設計**寫得進去。
    要分辨它與守衛失效，就得看得到「這一次守衛少跑了哪些」，⛔ 而不是猜。
    """

    #: 差分探測當次因「寫入前就讀不回」而跳過的讀取路徑。
    skipped: frozenset
    #: 當次實際執行的往返比對數（``append_log_line`` 的閘門會把它降到 0）。
    roundtrip: int
    #: 寫入結果：``None`` 代表寫得進去（＝守衛沒攔），否則是攔下來的例外。
    error: Exception | None = None


def _observe(fn, body: str) -> GuardTrace:
    """跑一次寫入，並記錄守衛當次跳過了什麼。⛔ 不改變守衛的判定。"""
    from wf_cli import card as card_mod

    real = card_mod.enforce_write_boundary
    seen = {"skipped": frozenset(), "roundtrip": 0}

    def spy(baseline, candidate, *, roundtrip=(), invariants=(), where):
        seen["skipped"] = frozenset(
            name
            for name, reader in card_mod.body_read_paths()
            if card_mod._reads_back(reader, baseline) is not None
        )
        seen["roundtrip"] = len(roundtrip)
        return real(
            baseline, candidate, roundtrip=roundtrip, invariants=invariants, where=where
        )

    card_mod.enforce_write_boundary = spy
    error: Exception | None = None
    try:
        fn(body)
    except Exception as exc:  # noqa: BLE001
        error = exc
    finally:
        card_mod.enforce_write_boundary = real
    return GuardTrace(seen["skipped"], seen["roundtrip"], error)


def _reference_traces() -> dict[str, GuardTrace]:
    """每個動詞的注入在一張**健康卡**上留下的守衛軌跡。

    ⭐ **它是「守衛本來會跑多少」的基準**：健康卡上守衛跳過的那幾條，是所有卡都會
    跳過的（例如 ``brief.parse_block`` 對沒有簡介的卡、兩個遷移函式對已遷移的卡）
    ——⛔ 那些**不是**損壞。真正的預壞是「這張卡比健康卡多跳過了什麼」。
    ⚠️ 本卡在這一格踩過一次：第一版拿「全部讀取路徑」當基準，於是每一張卡都落進
    預壞桶、分母歸零、攔截率變成恆真的 100%——零資訊的量測不是通過。
    """
    ref = render_issue_body(make_card(brief=_GOOD_BRIEF))
    return {verb: _observe(inject, ref) for verb, _, inject in _census_verbs()}


def census(cards) -> Census:
    """對 ``(card_id, body)`` 序列逐張逐動詞跑「控制組 → 注入」兩次寫入。

    分類（⛔ 逐格具名，⛔ 不得只報一個比率）：

    * ``control_unusable``——乾淨值被**非**寫入邊界的理由拒收（章節缺失／值未變更／
      grammar／該卡沒有那個欄位）⇒ 這個動詞打不到這張卡，該格無從量測，具名排除。
    * ``control_false_positive``——乾淨值被**寫入邊界**拒收 ⇒ **偽陽性，目標 0**。
    * ``intercepted``／``intercepted_by_legacy_check``——注入被擋，進分母。
    * ``excluded_pre_broken``——注入寫得進去，**而且量得到守衛是被差分閘門關掉的**：
      這張卡比健康卡**多**跳過了某些讀取路徑，或往返比對被閘門降到 0。差分探測逐字
      只罰迴歸、⛔ 不罰既有損壞 ⇒ 依 V4 逐字**具名排除於分母之外**。
    * ``leaked``——注入寫得進去，而守衛跑得和健康卡一樣多 ⇒ **真漏網，目標 0**。

    ⚠️ ``excluded_pre_broken`` 與 ``leaked`` 的分界**由 :class:`GuardTrace` 量測決定，
    ⛔ 不由人判**，也⛔ 不由「這張卡看起來壞不壞」判。
    """
    refs = _reference_traces()
    out = Census()
    verbs = _census_verbs()
    for card_id, body in cards:
        out.cards += 1
        excused: set[str] = set()
        for verb, control, inject in verbs:
            control_trace = _observe(control, body)
            if isinstance(control_trace.error, MarkerWriteBoundaryError):
                out.cells.append(
                    Cell(card_id, verb, "control_false_positive", str(control_trace.error)[:200])
                )
                continue
            if control_trace.error is not None:
                exc = control_trace.error
                out.cells.append(
                    Cell(card_id, verb, "control_unusable", f"{type(exc).__name__}: {exc}"[:200])
                )
                continue
            trace = _observe(inject, body)
            if isinstance(trace.error, MarkerWriteBoundaryError):
                out.cells.append(Cell(card_id, verb, "intercepted"))
                continue
            if trace.error is not None:
                out.cells.append(
                    Cell(card_id, verb, "intercepted_by_legacy_check", type(trace.error).__name__)
                )
                continue
            ref = refs[verb]
            extra_skipped = trace.skipped - ref.skipped
            gated_roundtrip = trace.roundtrip < ref.roundtrip
            if extra_skipped or gated_roundtrip:
                excused |= set(extra_skipped)
                why = "、".join(sorted(extra_skipped)) or "往返比對被差分閘門跳過"
                out.cells.append(Cell(card_id, verb, "excluded_pre_broken", why))
            else:
                out.cells.append(
                    Cell(
                        card_id, verb, "leaked",
                        f"守衛跑得與健康卡一樣多（跳過 {len(trace.skipped)} 條、"
                        f"往返 {trace.roundtrip} 次）卻沒攔下來",
                    )
                )
        if excused:
            out.pre_broken.append((card_id, tuple(sorted(excused))))
    return out


def inline_mentions(cards) -> list[tuple[str, str]]:
    """真實卡面上**行內**提及分界標記的行（``(card_id, 行)``）。

    ⭐ **取樣是位置性的，⛔ 不問守衛的意見**（否則就是拿答案建表）：只要 ``## `` 或
    ``<!-- `` 出現在該行的**非開頭位置**，它就不可能是獨立成行的區段標題或哨兵 ⇒
    依定義是行內提及。⇒ 這批行是 V2 的負控母體：本 repo 的交付報告、痛點欄、驗收
    條目本來就大量這樣寫，守衛擋掉它們就是把工具弄壞。
    """
    out: list[tuple[str, str]] = []
    for card_id, body in cards:
        for line in (body or "").splitlines():
            if not line.strip():
                continue
            for token in ("## ", "<!-- "):
                at = line.find(token)
                if at > 0 and line[:at].strip():
                    out.append((card_id, line))
                    break
    return out


def inline_mention_control(cards) -> tuple[int, list[tuple[str, str]]]:
    """把每一行行內提及當成值寫一次 ``append_log_line``；回傳 ``(總數, 被誤擋的)``。

    ⛔ 目標是**誤擋 0**。走 ``append_log_line`` 而不是 ``amend --brief``：後者另有
    形狀檢查（``validate_brief_shape``），任意真實行過不了它 ⇒ 會把「守衛擋掉」與
    「形狀檢查擋掉」混成同一個數字。
    """
    healthy = render_issue_body(make_card(brief=_GOOD_BRIEF))
    mentions = inline_mentions(cards)
    rejected: list[tuple[str, str]] = []
    for card_id, line in mentions:
        try:
            append_log_line(healthy, f"{_CENSUS_TS} {line}")
        except MarkerWriteBoundaryError:
            rejected.append((card_id, line))
        except Exception:  # noqa: BLE001 - 非本守衛的拒收不計入
            continue
    return len(mentions), rejected


def _live_cards():  # pragma: no cover - 需要 gh 認證與網路
    """真實看板全母體 ``(card_id, body)``。

    ⛔ 走 ``project.list_items``（wfcli 自己的讀取路徑），⛔ 不用 ``gh project item-list``
    ——後者對中文欄位名的 JSON key 有編碼錯誤（見 ``project.list_items`` docstring）。
    """
    import os

    from wf_cli.gh import default_runner
    from wf_cli.project import list_items, resolve_project

    owner = os.environ.get("WFCLI_OWNER", "ruan6047")
    number = int(os.environ.get("WFCLI_PROJECT", "4"))
    meta = resolve_project(default_runner, owner, number)
    return [(item.title.split()[0] if item.title else item.item_id, item.body or "")
            for item in list_items(default_runner, meta)]


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - 供人工重跑取證
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--census" in argv:
        import json

        cards = _live_cards()
        result = census(cards)
        print(result.summary())
        total, rejected = inline_mention_control(cards)
        seen_cards = len({cid for cid, _ in inline_mentions(cards)})
        print(f"行內提及負控：{total} 行／{seen_cards} 張卡，誤擋 {len(rejected)}（目標 0）")
        for card_id, line in rejected[:20]:
            print(f"  ⛔ {card_id}：{line[:120]}")
        idx = argv.index("--census")
        out_path = argv[idx + 1] if len(argv) > idx + 1 else None
        if out_path:
            with open(out_path, "w", encoding="utf-8") as fh:
                for cell in result.cells:
                    fh.write(json.dumps(dataclasses.asdict(cell), ensure_ascii=False) + "\n")
            print(f"# 逐格 artifact：{out_path}（{len(result.cells)} 列）")
        return 0 if not (result.leaked or result.control_false_positive or rejected) else 1

    paths = export_read_paths()
    print(f"# 讀取路徑（當次命中 {len(paths)} 條）")
    for name in paths:
        print(f"  {name}")
    seps = export_line_separators()
    print(f"# str.splitlines() 單字元分行符（窮舉 U+0000–U+{sys.maxunicode:04X}，{len(seps)} 個）")
    print("  " + " ".join(hex(ord(ch)) for ch in seps))
    print("# ⛔ 非宣稱：以上是本次導出命中的那組，不宣稱涵蓋全部讀取端。")
    return 0


# --------------------------------------------------------------------------
# 樣本工廠
# --------------------------------------------------------------------------

_GOOD_BRIEF = "做什麼一句話。適用時機：需要判斷相關性時。⛔ 非射程：不做別的。"


def make_card(**overrides) -> Card:
    defaults = dict(
        card_id="WB-DEMO1",
        feature="示範卡",
        tier="T2",
        db_scope="none",
        core_pain="寫入端不擋自己讀不回的值",
        service_goal="防止低級事故",
        resources=ResourceDeclaration(db_scope="none", resources=["file:demo.py"]),
        executor_capability="主力型",
        executor_capability_reason="跨模組改動",
        reviewer_capability="高階型",
        reviewer_capability_reason="紅線",
        requested_by="ruan6047",
        planned_by="PM",
        spec_baseline="—",
        acceptance=["原條件"],
        verification=["原驗證"],
    )
    defaults.update(overrides)
    return Card(**defaults)


CLEAN_BODY = render_issue_body(make_card())


def readable_by(body: str) -> set[str]:
    """這個 body 現在讀得回的讀取路徑集合。"""
    out = set()
    for name, fn in body_read_paths():
        try:
            fn(body)
        except Exception:  # noqa: BLE001
            continue
        out.add(name)
    return out


# --------------------------------------------------------------------------
# 導出程式本身的性質（⛔ 不逐字釘死清單——釘死等於把手打清單偷渡回來）
# --------------------------------------------------------------------------


def test_export_yields_a_nonempty_read_path_list():
    paths = export_read_paths()
    assert paths == sorted(paths)
    assert len(paths) >= 20


@pytest.mark.parametrize(
    "must_be_present",
    [
        "wf_cli.card.split_at_log",
        "wf_cli.brief.try_parse_block",
        "wf_cli.resources.parse_block",
    ],
)
def test_export_includes_the_structural_readers_the_guard_relies_on(must_be_present):
    """⛔ 只斷言「這幾條必須在裡面」，⛔ 不斷言「裡面只有這些」。

    後者會把 A1 明令禁止的封閉清單以測試的形式重新引入：偵測條件一放寬，命中集就變，
    而本卡第三輪的實測正是「放寬後由 7 變 11，漏掉的正是反例本人」。
    """
    assert must_be_present in export_read_paths()


def test_line_separator_export_matches_splitlines_itself():
    """窮舉導出的單字元分行符恰為 10 個。⚠️ 這是**驗證用的量測**，⛔ 不是判準。

    判準是兩條性質；涵蓋範圍由 ``str.splitlines()`` 自身導出。這條測試只是把
    「導出程式真的問了 splitlines」這件事釘住——若有人把導出換成手打清單，它會紅。
    """
    assert len(_SEPARATORS) == 10
    for ch in _SEPARATORS:
        assert len(("a" + ch + "b").splitlines()) > 1
    assert "\r\n" not in _SEPARATORS  # CRLF 是雙字元序列，不計入單字元


# --------------------------------------------------------------------------
# 性質 (1)：差分結構探測
# --------------------------------------------------------------------------


@pytest.mark.parametrize("sep", _SEPARATORS, ids=[hex(ord(c)) for c in _SEPARATORS])
def test_every_derived_separator_is_blocked_on_the_open_path(sep):
    with pytest.raises(MarkerWriteBoundaryError):
        make_card(service_goal=f"目標{sep}## Log")


def test_crlf_sequence_is_blocked_on_the_open_path():
    """CRLF 是雙字元序列，A8 逐字要求另測。"""
    with pytest.raises(MarkerWriteBoundaryError):
        make_card(service_goal="目標\r\n## Log")


@pytest.mark.parametrize("sep", _SEPARATORS, ids=[hex(ord(c)) for c in _SEPARATORS])
def test_every_derived_separator_is_blocked_on_the_amend_path(sep):
    """⭐ 刻意選 ``amend_acceptance``：⛔ 該路徑**沒有**既有的逐欄位換行檢查，
    ⇒ 擋下來的只能是本卡的守衛，⛔ 不會被舊檢查代打而看起來像通過。
    （對照組：``amend_core_pain`` 自己就擋 ``\n``／``\r``，另見
    ``test_legacy_per_field_checks_still_fire_first``。）
    """
    before = CLEAN_BODY
    with pytest.raises(MarkerWriteBoundaryError):
        amend_acceptance(before, [f"條件{sep}## Log"])
    assert before == CLEAN_BODY  # 純函式：來源逐位元未變


@pytest.mark.parametrize("sep", ["\n", "\r"], ids=["0xa", "0xd"])
def test_legacy_per_field_checks_still_fire_first(sep):
    """``\n``／``\r`` 在 ``amend_core_pain`` 由既有的逐欄位檢查先擋 ⇒ 型別是
    ``AmendError`` 而非 ``MarkerWriteBoundaryError``。⛔ 這不是守衛失效，是順序。"""
    with pytest.raises(AmendError):
        amend_core_pain(CLEAN_BODY, f"新痛點{sep}## Log")


def test_migration_header_blocks_all_four_fields():
    """R1-02 的原始形態：四個欄位裡只驗了兩個。現在四個都由同一份判準涵蓋。"""
    legacy = "## Spec\n\n舊卡沒有 canonical 標頭\n\n## Log\n\n- x\n"
    for field in ("requested_by", "planned_by", "initiative", "spec_baseline"):
        kwargs = dict(
            requested_by="ruan6047", planned_by="PM", initiative="—", spec_baseline="—"
        )
        kwargs[field] = f"值{_SEPARATORS[0]}## Log"
        with pytest.raises(ValueError):  # AmendError 或 MarkerWriteBoundaryError
            restore_migration_header(legacy, **kwargs)


def test_resource_grammar_hole_is_blocked_at_the_write_boundary():
    """``_RESOURCE_PREFIX_RE`` 的 ``.`` 不排除 U+2028，``json.dumps`` 也不逃脫它。

    ⇒ 這個值過得了 grammar，寫進去卻讓卡面多一個 ``## Log``。⛔ 修法不是補字元清單。
    """
    # ⚠️ 尾綴那個分行符是**必要的**：``json.dumps(indent=2)`` 會把值包在引號裡，
    # 少了它，注入的 `## Log` 後面緊跟著 `"` ⇒ 不是獨立標題行 ⇒ 本來就無害。
    # ⛔ 這一格第一次寫錯過（少了尾綴），就地留註以免下一個人再簡化回去。
    decl = ResourceDeclaration(db_scope="none", resources=["file:x\u2028## Log\u2028y"])
    with pytest.raises(MarkerWriteBoundaryError):
        amend_resource_block(CLEAN_BODY, render_block(decl))


# --------------------------------------------------------------------------
# P0：``card.append_log_line``（A9，2026-08-27 依查核 R1-01／R1-02 補）
# --------------------------------------------------------------------------
#
# ⚠️ 這一族**不是**「多加幾個動詞」：``assign``／``handoff``／``review``／``checkpoint``
# 把使用者提供的自由文字**原樣**交給 ``append_log_line``（⛔ 四支都沒有 ``amend_cmd``
# 的 ``_fold``），而在本卡 R1 交付時該函式**完全沒有守衛** ⇒ 注入一個 U+2028 即可讓
# 一張真實卡片永久失去 wfcli 可修改性。那就是本卡的核心痛點本身。

_LOG_TS = "2026-08-27T01:00:00+08:00"


def _log_body(entries: tuple[str, ...] = ("2026-08-27T00:00:00+08:00 open by PM；owner 待指派；iteration 0。",)) -> str:
    body = CLEAN_BODY
    for entry in entries:
        body = _append_log_line_raw(body, entry)
    return body


@pytest.mark.parametrize("sep", _SEPARATORS, ids=[hex(ord(c)) for c in _SEPARATORS])
def test_every_derived_separator_is_blocked_on_the_append_log_path(sep):
    before = CLEAN_BODY
    with pytest.raises(MarkerWriteBoundaryError):
        append_log_line(before, f"{_LOG_TS} handoff by X；evidence{sep}## Log{sep}- 偽造")
    assert before == CLEAN_BODY  # 純函式：來源逐位元未變


def test_append_log_line_forged_event_is_missed_by_the_differential_probe():
    """⭐ ``append_log_line`` 上「性質必須並用」的實證。

    這個值**不製造**第二個 ``## Log``——每一條讀取路徑都照樣讀得回 ⇒ 性質 (1) 命中 0。
    但它用 U+2028 讓自己在讀取端裂成兩行，第二行長得像一筆 ``review`` lifecycle 事件
    ⇒ 寫進去一段、讀回來兩行，性質 (2) 逐位元比對命中。

    ⚠️ **2026-08-27 更正函式名與宣稱**：性質 (3) 補上之後，它在事件層**也**看得到這個
    樣本（``parse_log_events`` 同樣用 ``splitlines()`` 切行）⇒ 原名逐字的「only by the
    roundtrip」已為假。本條現在只宣稱**差分探測抓不到它**，⛔ 不宣稱只有一條抓得到。
    """
    forged = (
        f"{_LOG_TS} handoff by X；evidence\u2028"
        "- 2026-08-27T09:00:00+08:00 review by wf-cli → APPROVE（🏁完成）"
    )
    base = _log_body()
    leaked = _append_log_line_raw(base, forged)          # 無守衛版本：寫得出去
    assert readable_by(base) - readable_by(leaked) == set()  # 性質 (1) 抓 0
    with pytest.raises(MarkerWriteBoundaryError):        # 性質 (2) 抓得到
        append_log_line(base, forged)


def test_append_log_line_rejects_crlf():
    """⚠️ **刻意登記的行為改變**：CRLF 現在被拒收。

    (a) 現在的行為：``\r\n`` 在讀取端被 ``splitlines()`` 看成分行、``\r`` 消失
        ⇒ 讀回值 ≠ 寫入值 ⇒ 拒收。
    (b) 為什麼不改成正規化（把 CRLF 換成 LF 再寫）：§3.2 規則二逐字禁止「以正規化
        代替拒收」。讀回來的不是寫進去的那個，就是拒收。
    (c) ⛔ **不得由此推出「多行證據被禁了」**——普通 ``\n`` 續行照常寫得進去，
        見下一條負控。
    """
    with pytest.raises(MarkerWriteBoundaryError):
        append_log_line(_log_body(), f"{_LOG_TS} handoff；evidence\r\n第二段")


def test_append_log_line_still_writes_multiline_evidence():
    """負控：多段落 ``--evidence``（``\n`` 續行）是 ``parse_log_events`` 明文支援的
    形狀，⛔ 守衛不得擋它。"""
    entry = f"{_LOG_TS} handoff by X；evidence 見下\n  第二段：量法與指令\n  第三段：SHA"
    written = append_log_line(_log_body(), entry)
    events, why = doctor.parse_log_events(written)
    assert why is None and events is not None
    assert events[-1].splitlines()[0].startswith("handoff by X")
    assert len(events[-1].splitlines()) == 3   # 續行歸入同一筆事件


def test_append_log_line_still_writes_the_doctor_reachability_probe_value():
    """負控（**真實呼叫端**，⛔ 非自造）：``doctor`` 的可達性探針逐字餵
    ``f"- {_PROBE_TOKEN}"``——沒有時戳、開頭還多一個 ``- ``。它必須照樣寫得進去，
    否則全母體每一張卡都會被誤報成 append-only 動詞不可達。"""
    from wf_cli.doctor import _PROBE_TOKEN

    written = append_log_line(_log_body(), f"- {_PROBE_TOKEN}")
    assert written.rstrip("\n").endswith(f"- - {_PROBE_TOKEN}")


def test_append_log_line_still_writes_inline_mentions():
    """負控：行內提及 ``## Log``／``<!-- card-brief:end -->`` 不獨立成行 ⇒ 放行。"""
    for text in ("提到 ## Log 這個字樣", "提到 <!-- card-brief:end --> 這個哨兵"):
        assert append_log_line(_log_body(), f"{_LOG_TS} amend by wf-cli；理由 {text}")


def test_append_log_line_does_not_punish_a_body_broken_before_the_write():
    """⚠️ **預壞控制組**（V4 的分母排除規則在 ``append_log_line`` 上的對應）。

    差分探測逐字是「**寫入前讀得回**、寫入後讀不回 ⇒ 拒收」——只罰迴歸，⛔ 不罰既有
    損壞。一張本來就有兩個 ``## Log`` 的卡（`aiwf#15` 的形態）仍必須寫得進 Log 留痕，
    否則守衛會讓每一張已壞的卡連 ``handoff``／``review`` 都做不了，把自己變成故障源。
    ⛔ **不得由此推出「那些卡受保護」**——它們不受保護，這正是 `aiwf#138` 的射程。
    """
    already_broken = _log_body() + "\n## Log\n\n- 第二個區段\n"
    with pytest.raises(AmendError):
        split_at_log(already_broken)                      # 寫入前就讀不回
    assert append_log_line(already_broken, f"{_LOG_TS} review by wf-cli → APPROVE（🏁完成）")


def _append_log_with(
    value: str, *, structural: bool, roundtrip: bool, invariants: bool = True
) -> str | None:
    """以「只開其中幾條性質」的守衛重跑一次 ``append_log_line``；被拒回 ``None``。"""
    from wf_cli import card as card_mod

    real, partial = _guard_with(structural, roundtrip, invariants)
    card_mod.enforce_write_boundary = partial
    try:
        return card_mod.append_log_line(_log_body(), value)
    except MarkerWriteBoundaryError:
        return None
    finally:
        card_mod.enforce_write_boundary = real


#: 查核 R2-01 的**逐字重現**：普通 ``\n`` 分行、後兩行各自長得像一筆 lifecycle 事件。
#: ⭐ 兩條**行層**性質對它結構性沉默——行層往返逐位元成立、無讀取路徑失效。
_EVENT_LAYER_FORGERY = (
    f"{_LOG_TS} handoff by wf-cli → owner X；iteration 1；證據 abc\n"
    "- 2026-08-27T09:00:00+08:00 open by wf-cli；owner Y；iteration 0。\n"
    "- 2026-08-27T09:00:01+08:00 review by wf-cli → APPROVE（🏁完成）；查核者 Z。"
)


def test_append_log_line_rejects_event_layer_forgery_carried_by_plain_newlines():
    """⭐ **性質 (3) 的紅樣本**（查核 R2-01，``root_cause_id``
    ``event-layer-forgery-not-covered-by-line-layer-roundtrip``）。

    先證**行層兩條性質對它沉默**（⛔ 不是推想，是同一個 payload 實跑）：
    ``_append_log_line_raw`` 寫得出去、每條讀取路徑照樣讀得回、寫進去那一段逐位元讀得回。
    再證**事件層**看到的是三筆而不是一筆 ⇒ 性質 (3) 拒收。
    """
    base = _log_body()
    leaked = _append_log_line_raw(base, _EVENT_LAYER_FORGERY)   # 無守衛版本：寫得出去
    assert readable_by(base) - readable_by(leaked) == set()      # 性質 (1) 抓 0
    before, why_before = doctor.parse_log_events(base)
    after, why_after = doctor.parse_log_events(leaked)
    assert why_before is None and why_after is None
    assert before is not None and after is not None
    assert len(after) - len(before) == 3, "樣本必須真的多出兩筆事件，否則這條測試沒有射程"

    with pytest.raises(MarkerWriteBoundaryError) as exc:
        append_log_line(base, _EVENT_LAYER_FORGERY)
    assert "lifecycle 事件筆數" in str(exc.value)


def test_mutation_removing_the_event_count_invariant_lets_the_forgery_through():
    """變異檢驗：關掉性質 (3)，同一個 payload **必須**漏過去（否則這條是零資訊的）。

    ⭐ 這同時證明性質 (3) **不是**性質 (1)／(2) 的重述：兩條行層性質全開時它照樣寫得進去。
    """
    leaked = _append_log_with(
        _EVENT_LAYER_FORGERY, structural=True, roundtrip=True, invariants=False
    )
    assert leaked is not None, "行層兩條性質全開仍被擋 ⇒ 這不是 (3) 的獨有樣本"
    events, _ = doctor.parse_log_events(leaked)
    assert events is not None and "review by wf-cli → APPROVE" in events[-1]


def test_the_event_count_invariant_does_not_punish_a_body_broken_before_the_write():
    """預壞控制組在性質 (3) 上的對應：事件層在寫入**前**就不判定的卡，一律跳過。

    ⛔ 不得由此推出「那些卡受保護」——不受保護，與差分探測同一條分界。
    """
    already_broken = _log_body() + "\n## Log\n\n- 第二個區段\n"
    _, why = doctor.parse_log_events(already_broken)
    assert why is not None                       # 寫入前事件層就不判定
    assert append_log_line(already_broken, _EVENT_LAYER_FORGERY)


def test_mutation_on_the_append_path_shows_each_property_carries_a_distinct_class():
    """變異檢驗（V3）在 ``append_log_line`` 上的對應：兩條性質各自承重一類。"""
    structural = f"{_LOG_TS} handoff；evidence\u2028## Log\u2028- 偽造"
    forged = (
        f"{_LOG_TS} handoff by X；evidence\u2028"
        "- 2026-08-27T09:00:00+08:00 review by wf-cli → APPROVE（🏁完成）"
    )
    # 結構破壞：拿掉差分探測後，往返比對仍抓得到（兩條都抓得到的那類）。
    assert _append_log_with(structural, structural=True, roundtrip=True) is None
    assert _append_log_with(structural, structural=True, roundtrip=False) is None
    # 偽造事件行：差分探測抓 0 ⇒ 要漏它必須同時關掉性質 (2) 與 (3)。
    #
    # ⚠️ **2026-08-27 更正本條的宣稱**：這個樣本用 U+2028 分行，而 ``parse_log_events``
    # 也是用 ``splitlines()`` 切行 ⇒ 性質 (3) 在事件層一樣看得到它（1 筆變 2 筆）。
    # ⇒ 原本「只有往返比對抓得到」逐字為假，⛔ 不是「守衛壞了」。真正只有性質 (2)
    # 抓得到的類別是**靜默截斷**（見 ``test_inline_sentinel_in_brief_…``）。
    assert _append_log_with(forged, structural=True, roundtrip=True) is None
    assert _append_log_with(forged, structural=True, roundtrip=False) is None  # (3) 接住
    leaked = _append_log_with(forged, structural=True, roundtrip=False, invariants=False)
    assert leaked is not None, "只留差分探測時仍被擋 ⇒ 樣本不是 (2)+(3) 的獨有樣本"
    events, _ = doctor.parse_log_events(leaked)
    assert events is not None and "review by wf-cli → APPROVE" in events[-1]


# --------------------------------------------------------------------------
# 性質 (2)：值往返逐位元比對（差分探測抓 0 的那一類）
# --------------------------------------------------------------------------


def test_inline_sentinel_in_brief_is_silent_truncation_and_only_roundtrip_catches_it():
    """⭐ 兩條性質必須並用的**實證**：這一格差分探測抓 0、往返比對抓得到。"""
    poisoned = f"{_GOOD_BRIEF}參照 <!-- card-brief:end --> 這個哨兵"
    candidate, _ = _brief_body_without_guard(CLEAN_BODY, poisoned)
    # 差分探測：每一條讀取路徑都照樣讀得回 ⇒ 性質 (1) 命中 0 條。
    assert readable_by(CLEAN_BODY) - readable_by(candidate) == set()
    # 往返比對：讀回的值比寫進去的短 ⇒ 性質 (2) 命中。
    with pytest.raises(MarkerWriteBoundaryError):
        amend_brief(CLEAN_BODY, poisoned)


def _brief_body_without_guard(body: str, value: str) -> tuple[str, str | None]:
    """跑 ``amend_brief`` 但把守衛的例外吞掉，只為取得「若不拒收會寫成什麼」。

    ⛔ 只在測試裡用來取證，⛔ 不是可用的寫入路徑。
    """
    from wf_cli import card as card_mod

    real = card_mod.enforce_write_boundary
    card_mod.enforce_write_boundary = lambda *a, **k: None
    try:
        return card_mod.amend_brief(body, value)
    finally:
        card_mod.enforce_write_boundary = real


def test_brief_whose_entire_value_is_a_heading_is_caught_by_roundtrip():
    """值裡**沒有任何分行字元**，卻被哨兵區塊放到自己那一行 ⇒ 只有性質 (2) 抓得到。"""
    with pytest.raises(MarkerWriteBoundaryError):
        amend_brief(CLEAN_BODY, f"## Log{_GOOD_BRIEF}")


# --------------------------------------------------------------------------
# 性質 (1)：差分結構探測（往返比對抓 0 的那一類）
# --------------------------------------------------------------------------
#
# ⭐ **這一節存在的理由是「兩條必須並用」原本只證了一半**（2026-08-27 補）：
# 交付當下只有性質 (2) 的獨有樣本（上一節的靜默截斷），性質 (1) 一條都沒有 ⇒ 對
# ``if broken:`` 做變異時整份測試仍全綠，那條性質在測試集上**不承重**。
#
# ⚠️ **它不承重不是因為「沒被跑到」**：實測差分探測在整份測試集內跑了數百次、其中
# 一百多次真的抓到——只是每一次往返比對也抓得到。⇒ 缺的是**只有它抓得到**的樣本。
#
# ⭐ 構造判準（⛔ 不是試出來的，是從兩條性質的定義推出來的）：
#
#   * 往返比對讀的是**被寫的那個欄位自己**。單行欄位的讀回器逐行比對 ⇒ 值裡只要有
#     一個 ``splitlines()`` 分行符，該欄位就讀回截斷值 ⇒ 性質 (2) 必然命中。
#   * ⇒ 只有性質 (1) 抓得到的值，必須是「**這個欄位自己逐位元讀得回**、卻讓**別的**
#     讀取路徑讀不回」的值。
#   * ⇒ 需要一個**多行且逐字讀回**的欄位：``--brief``（哨兵區塊之間的內容原樣讀回），
#     再讓它注入一行去打壞一條**不在本次往返清單裡**的讀取路徑。
#
# ⭐ 選中的靶是 ``card.parse_requested_by``：它是**fail-closed 的授權閘門**（核心痛點
# 更正、``review-escalation.md`` §4 的 deferred_findings 出口都用它比對需求方身分），
# 且它對「``- 需求：…　規劃：…`` 命中次數 ≠ 1」拋例外、⛔ 不是回 None。⇒ 打壞它
# 等於讓那張卡的需求方身分**永久無法機械核對**，與本卡痛點同一族。


#: ⚠️ 這個值**每一個字元都合法**，也沒有任何 marker 被「偽造成」別的東西——
#: 它只是把一句本來就會出現在簡介裡的引用**放到自己那一行**。
_BRIEF_WITH_STANDALONE_REQUESTER_LINE = (
    "適用時機：需要說明需求方欄長什麼樣子時。\n"
    "- 需求：someone　規劃：other\n"
    "⛔ 非射程：不做別的。"
)


def test_standalone_requester_line_in_brief_is_only_caught_by_the_differential_probe():
    """⭐ 與上一節對稱的**實證**：這一格往返比對抓 0、差分探測抓得到。

    ⚠️ 斷言刻意分成三段，⛔ 不只斷言「被拒收」——只斷言拒收的話，兩條性質哪一條在
    承重是看不出來的（那正是本節要補的洞）。
    """
    poisoned = _BRIEF_WITH_STANDALONE_REQUESTER_LINE
    candidate, _ = _brief_body_without_guard(CLEAN_BODY, poisoned)

    # (a) 性質 (1) 命中：寫入前讀得回、寫入後讀不回。
    lost = readable_by(CLEAN_BODY) - readable_by(candidate)
    assert "wf_cli.card.parse_requested_by" in lost, (
        f"差分探測沒抓到；當次少掉的讀取路徑＝{sorted(lost)}"
    )

    # (b) 性質 (2) **抓 0**：這次寫的欄位自己逐位元讀得回。
    assert _read_brief_text(candidate) == poisoned

    # (c) 真實路徑（兩條都在）拒收，且訊息指名那條讀取路徑。
    with pytest.raises(MarkerWriteBoundaryError) as excinfo:
        amend_brief(CLEAN_BODY, poisoned)
    assert "wf_cli.card.parse_requested_by" in str(excinfo.value)


def test_the_same_sentence_mentioned_inline_still_writes():
    """負控：同一句話**不獨立成行**時必須寫得進去，且授權閘門仍讀得回。

    ⛔ 沒有這一格，(c) 的拒收可能只是「凡是提到 `- 需求：` 就拒」——那是本卡逐字
    禁止的字面黑名單，而不是結構判準。
    """
    inline = (
        "適用時機：需要說明需求方欄長什麼樣子時，例如 "
        "`- 需求：someone　規劃：other` 這一行。⛔ 非射程：不做別的。"
    )
    body, _ = amend_brief(CLEAN_BODY, inline)
    assert _read_brief_text(body) == inline
    assert parse_requested_by(body) == "ruan6047"


def test_owner_damage_is_caught_by_both_properties_not_only_the_differential():
    """⚠️ **就地更正一個先前寫錯的宣稱**（⛔ 不得再拿 ``owner`` 當「只有 (1) 抓得到」）。

    (a) 現在的事實：``owner`` 確實**沒有專屬的往返讀回器**（它只出現在 Log 行），
        但把 ``## Log`` 塞進它會讓 ``split_at_log`` 拋錯，而**其餘每一個**往返讀回器
        都經由 ``_head_lines`` → ``split_at_log`` ⇒ 它們**全部**跟著拋 ⇒ 性質 (2)
        照樣命中。
    (b) 為什麼要留這條測試：先前的變異測試以 ``owner`` 為「乾淨樣本」，⇒ 對差分探測
        做變異時不會轉紅，而那份綠色被讀成「差分探測有承重」。
    (c) ⛔ **不得由此推出「owner 有往返保證」**：它沒有。它只是**恰好**每次都連坐到
        別人的往返讀回器；一個不碰 ``## Log`` 的 owner 值（例如塞進一行
        ``- 需求：…``，那是 Log 區、讀取端本來就不看）今天兩條性質都抓不到。
    """
    poisoned = {"owner": "小明 ## Log 尾"}
    with pytest.raises(MarkerWriteBoundaryError):
        make_card(**poisoned)
    # 往返讀回器**單獨**就抓得到（無差分探測）。
    assert _render_with(poisoned, structural=False, roundtrip=True) is None
    # 差分探測**單獨**也抓得到（無往返比對）。
    assert _render_with(poisoned, structural=True, roundtrip=False) is None
    # ⇒ 這一格是兩條性質的**交集**，⛔ 不是任一條的獨有樣本。


# --------------------------------------------------------------------------
# 逐欄位窮舉：⛔ 欄位清單由 dataclasses.fields 導出，不手打
# --------------------------------------------------------------------------

_STR_FIELDS = [
    f.name
    for f in dataclasses.fields(Card)
    if isinstance(getattr(make_card(), f.name), (str, list))
]


@pytest.mark.parametrize("field_name", _STR_FIELDS)
def test_no_card_field_can_produce_a_body_its_own_readers_reject(field_name):
    """⭐ **本檔最重要的一條**：不是「某個 marker 被擋」，而是

        對**每一個**欄位、每一個導出的分行符，
        **要嘛寫入被拒，要嘛寫出來的卡面仍被原本讀得回它的每一條讀取路徑讀得回。**

    ⛔ 欄位由 ``dataclasses.fields(Card)`` 導出：新增欄位自動納入，⛔ 不需要有人記得
    回來改這裡；漏掉的欄位會讓本測試紅，⛔ 不會靜默放行。
    """
    base_ok = readable_by(CLEAN_BODY)
    for sep in _SEPARATORS:
        payload = f"值{sep}## Log{sep}尾"
        current = getattr(make_card(), field_name)
        value = [payload] if isinstance(current, list) else payload
        try:
            body = render_issue_body(make_card(**{field_name: value}))
        except ValueError:
            continue  # 拒收（含 __post_init__ 的既有欄位檢查）——這是合格的一半
        assert base_ok - readable_by(body) == set(), (
            f"{field_name} 寫得進去卻讓 {sorted(base_ok - readable_by(body))} 讀不回"
        )


# --------------------------------------------------------------------------
# 負控（V2）：行內提及必須寫得進去
# --------------------------------------------------------------------------

_INLINE_MENTIONS = [
    "卡面出現兩個 ## Log 時 split_at_log 會拋錯",
    "沿用 <!-- resource-claims:begin --> 哨兵慣例",
    "位置型標記 <!-- wf-routing:v1 --> 不在射程",
    "## 驗收條件 與 ## 驗證 兩章節須於離開規劃前填實",
    "brief 的 <!-- card-brief:begin --> / <!-- card-brief:end --> 是一對",
]


@pytest.mark.parametrize("text", _INLINE_MENTIONS)
def test_inline_mentions_still_write(text):
    """⛔ 只驗拒收是零資訊——「全部拒絕」也能讓正向測試全綠。"""
    body, _ = amend_core_pain(CLEAN_BODY, text)
    assert text in body
    assert readable_by(CLEAN_BODY) - readable_by(body) == set()


@pytest.mark.parametrize("text", _INLINE_MENTIONS)
def test_inline_mentions_still_open(text):
    assert text in render_issue_body(make_card(service_goal=text))


def test_clean_values_pass_every_guarded_amend_verb():
    assert amend_acceptance(CLEAN_BODY, ["新條件甲", "新條件乙"])[0] != CLEAN_BODY
    assert amend_verification(CLEAN_BODY, ["新驗證"])[0] != CLEAN_BODY
    assert amend_initiative(CLEAN_BODY, "INIT-1")[0] != CLEAN_BODY
    assert amend_spec_baseline(CLEAN_BODY, "abc1234")[0] != CLEAN_BODY
    assert amend_core_pain(CLEAN_BODY, "新的痛點敘述")[0] != CLEAN_BODY
    assert amend_brief(CLEAN_BODY, _GOOD_BRIEF)[0] != CLEAN_BODY


# --------------------------------------------------------------------------
# 變異檢驗（V3）：對象是**兩條性質本身**，⛔ 不是「每個 marker 的拒收」
# --------------------------------------------------------------------------


def test_mutation_removing_the_differential_probe_lets_structural_damage_through():
    """變異一：拿掉差分結構探測 ⇒ 結構破壞漏掉。

    ⭐ **取樣必須是「只有性質 (1) 抓得到」的那一格**，⛔ 不能拿兩條都抓得到的樣本——
    那種樣本變異掉一條也不會轉紅，測不出載重。本卡 2026-08-27 在此踩過一次：原樣本
    用 ``owner``，理由是「它沒有往返讀回器」——⛔ 該理由不成立（見
    ``test_owner_damage_is_caught_by_both_properties_not_only_the_differential``），
    ⇒ 對 ``if broken:`` 做變異時整份測試仍全綠。

    現行樣本＝簡介裡多一行獨立成行的 ``- 需求：…　規劃：…``：該欄位自己逐位元讀得回
    （往返抓 0），而 ``card.parse_requested_by`` 這條 fail-closed 授權閘門讀不回了。
    """
    poisoned = _BRIEF_WITH_STANDALONE_REQUESTER_LINE
    # 兩條都在：拒收。
    assert _amend_brief_with(poisoned, structural=True, roundtrip=True) is None
    with pytest.raises(MarkerWriteBoundaryError):
        amend_brief(CLEAN_BODY, poisoned)  # 未經變異的真實路徑同樣拒收
    # 只留往返比對（拿掉差分探測）：放行，而放行的結果是一張授權讀不回的卡。
    leaked = _amend_brief_with(poisoned, structural=False, roundtrip=True)
    assert leaked is not None, "只留往返比對時這一格仍被擋 ⇒ 樣本不是 (1) 的獨有樣本"
    with pytest.raises(Exception):
        parse_requested_by(leaked)
    # 對照：只留差分探測時仍被擋 ⇒ 擋它的確實是性質 (1)。
    assert _amend_brief_with(poisoned, structural=True, roundtrip=False) is None


def _guard_with(structural: bool, roundtrip: bool, invariants: bool = True):
    """回傳一個「只開其中幾條性質」的 ``enforce_write_boundary`` 替身。

    ⭐ **關掉差分探測的做法是把 baseline 換成 candidate，⛔ 不是把 candidate 換成
    baseline**（就地留註，這一格寫反過一次）：

    (a) 現在的行為：``structural=False`` 時傳 ``(candidate, candidate)`` ⇒ 每條讀取
        路徑在「寫入前後」讀到的是同一份 body ⇒ 差分恆空，而**往返比對仍看得到真正的
        candidate**。
    (b) 為什麼：原寫法傳 ``(baseline, baseline)``，往返讀回器拿到的也是 baseline
        ⇒ **兩條性質同時被關掉** ⇒ 該變異測試對任何樣本都會綠，是零資訊的變異。
    (c) ⛔ 不得由此推出「兩種寫法只差在參數順序」：差別是**變異的射程**，寫反了會讓
        「這條性質承不承重」這個問題本身量不出來。
    """
    from wf_cli import card as card_mod

    real = card_mod.enforce_write_boundary

    def partial(baseline, candidate, **kwargs):  # noqa: ANN001
        real(
            baseline if structural else candidate,
            candidate,
            roundtrip=kwargs.get("roundtrip", ()) if roundtrip else (),
            # ⚠️ 性質 (3) 也必須是**顯式**的一軸，⛔ 不能靠 ``**kwargs`` 默默吃掉它：
            # 吃掉等於每一個變異案例都在「性質 (3) 已關」的世界裡跑，於是「拿掉它會不會
            # 漏」這個問題**量不出來**——那正是本檔 (b) 段記的同一個錯。
            invariants=kwargs.get("invariants", ()) if invariants else (),
            where=kwargs.get("where", ""),
        )

    return real, partial


def _render_with(card_kwargs: dict, *, structural: bool, roundtrip: bool) -> str | None:
    """以「只開其中一條性質」的守衛重跑一次 ``open`` 渲染；被拒回 ``None``。"""
    from wf_cli import card as card_mod

    real, partial = _guard_with(structural, roundtrip)
    card_mod.enforce_write_boundary = partial
    try:
        return render_issue_body(make_card(**card_kwargs))
    except MarkerWriteBoundaryError:
        return None
    finally:
        card_mod.enforce_write_boundary = real


def _amend_brief_with(value: str, *, structural: bool, roundtrip: bool) -> str | None:
    """以「只開其中一條性質」的守衛重跑一次 ``amend_brief``；被拒回 ``None``。"""
    from wf_cli import card as card_mod

    real, partial = _guard_with(structural, roundtrip)
    card_mod.enforce_write_boundary = partial
    try:
        return card_mod.amend_brief(CLEAN_BODY, value)[0]
    except MarkerWriteBoundaryError:
        return None
    finally:
        card_mod.enforce_write_boundary = real


def test_mutation_removing_the_roundtrip_lets_silent_truncation_through():
    """變異二：拿掉值往返比對 ⇒ 靜默截斷漏掉（實測那是唯一抓得到它的）。"""
    poisoned = f"{_GOOD_BRIEF}參照 <!-- card-brief:end --> 這個哨兵"
    candidate, _ = _brief_body_without_guard(CLEAN_BODY, poisoned)
    # 只留差分探測：每條讀取路徑都讀得回 ⇒ 放行。
    assert readable_by(CLEAN_BODY) - readable_by(candidate) == set()
    from wf_cli.brief import try_parse_block

    parsed = try_parse_block(candidate)
    assert parsed is not None and parsed.text != poisoned  # 放行的結果被靜默截斷


def test_mutation_split_on_backslash_n_misses_the_other_separators():
    """變異三：把 ``splitlines()`` 換成 ``split("\\n")`` ⇒ 有分行符會漏掉。

    ⛔ 這裡不斷言「漏 8 個」——那是舊卡面的數字。斷言的是**構造上必然漏**：
    ``split("\\n")`` 看不見的分行符，導出集合裡不只一個。
    """
    missed = [ch for ch in _SEPARATORS if len(("a" + ch + "b").split("\n")) == 1]
    assert len(missed) >= 2
    for ch in missed:
        # 現行守衛擋得住……
        with pytest.raises(AmendError):
            amend_acceptance(CLEAN_BODY, [f"條件{ch}## Log"])
        # ……而換成 split("\n") 的謂詞看不見它。
        assert f"新痛點{ch}## Log".split("\n") == [f"新痛點{ch}## Log"]


# --------------------------------------------------------------------------
# 端到端（V1）：rc≠0 且 body 逐位元未變
# --------------------------------------------------------------------------

_TARGET = ["--owner", "acme", "--project", "1"]


def _run(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


@pytest.fixture
def runner(monkeypatch):
    fake = FakeGhRunner()
    for module in (open_cmd, amend_cmd):
        monkeypatch.setattr(module, "default_runner", fake)
    return fake


@pytest.fixture
def opened(runner):
    rc = _run(
        [
            "open", *_TARGET, "WB-E2E1",
            "--feature", "示範", "--tier", "T1", "--db-scope", "none",
            "--core-pain", "痛點", "--service-goal", "目標",
            "--exec-capability", "主力型", "--exec-capability-reason", "一般實作",
            "--review-capability", "主力型", "--review-capability-reason", "一般 review",
            "--resources", "file:demo.py",
            "--acceptance", "原條件", "--verification", "原驗證",
            "--spec-baseline", "原基線",
        ]
    )
    assert rc == 0
    return runner


def _body(runner) -> str:
    project = resolve_project(runner, "acme", 1)
    return find_item_by_card_id(list_items(runner, project), "WB-E2E1").body


def test_amend_e2e_rejects_and_leaves_body_bit_identical(opened, capsys):
    before = _body(opened)
    rc = _run(
        ["amend", *_TARGET, "WB-E2E1", "--reason", "注入測試",
         "--acceptance", "新條件\u2028## Log"]
    )
    assert rc == 2
    assert _body(opened) == before  # 逐位元未變
    err = capsys.readouterr().err
    assert "寫入邊界拒收（未寫入任何狀態）" in err
    # ⭐ 拒收訊息**不得**帶出排版修復 runbook：卡面是好的，該修的是值。
    assert "gh issue edit" not in err
    assert "本指令刻意不自動修" not in err


_OPEN_POISONED = [
    "--feature", "示範", "--tier", "T1", "--db-scope", "none",
    "--core-pain", "痛點", "--service-goal", "目標\u2028## Log",
    "--exec-capability", "主力型", "--exec-capability-reason", "一般實作",
    "--review-capability", "主力型", "--review-capability-reason", "一般 review",
]


def test_open_e2e_rejects_cleanly_before_any_remote_write(runner, capsys):
    """``open`` 是主破口（14 個旗標裡 9 個寫得出永久不可 amend 的卡）。

    ⭐ 這條同時是 §3.2 規則二的三個要件：**任何遠端寫入之前**、**可辨識訊息**、
    **非零退出碼**。⛔ ``pytest.raises`` 不再是通過條件——以例外收場的 fail-closed
    正是規則二逐字不接受的那種（「以 stack trace 收場的 fail-closed 不算乾淨拒絕」）。
    """
    rc = _run(["open", *_TARGET, "WB-E2E2", *_OPEN_POISONED])
    assert rc == 2
    err = capsys.readouterr().err
    assert err.startswith("[open] 拒絕：")
    assert "寫入邊界拒收（未寫入任何狀態）" in err
    assert "Traceback" not in err
    # 零遠端寫入：連 project 都沒被解析出來過。
    assert runner.projects == {}
    assert runner.items == {}


def test_open_rejection_through_cli_main_never_escapes_as_a_traceback(runner, capsys):
    """⭐ **經 ``cli.main`` 的那條路徑另外驗一次，⛔ 不是重複**：``_run`` 直接呼叫
    ``args.func``，繞過 ``cli.KNOWN_ERRORS``。使用者實際跑的是 ``main``，而本卡的
    第二道乾淨化（``KNOWN_ERRORS``）只在那條路徑上生效。
    """
    rc = cli_main(["open", *_TARGET, "WB-E2E3", *_OPEN_POISONED])
    assert rc == 2
    assert "Traceback" not in capsys.readouterr().err


def test_the_four_log_verbs_rejection_is_not_yet_clean_at_the_cli_layer():
    """⏸ **把阻塞發現釘成可執行的紀錄**（⛔ 這條不驗守衛，它驗「還缺什麼」）。

    (a) 現在的行為：``card.MarkerWriteBoundaryError`` 不在 ``cli.KNOWN_ERRORS`` 內
        ⇒ ``assign``／``handoff``／``review``／``checkpoint`` 在守衛拒收時經 ``cli.main``
        會以 traceback、rc=1 收場。``open`` 不在此列——它自己接住並回 rc=2。
    (b) 為什麼沒補：補法是把該型別加進那個 tuple（一行），但
        ``cli/tests/test_cli_registry.py`` 的 ``EXPECTED_KNOWN_ERRORS`` 是凍結基線，
        同一次改動必須連它一起改，而**該檔不在本卡宣告資源**內（A10 逐字：發現須改
        未宣告的檔即停）。
    (c) ⛔ **不得由此推出「那四支沒有守衛」**——值一樣寫不進去（見上一條），
        缺的只是訊息與退出碼的乾淨度。
    ⭐ 這條在有人補上那一行的當天會**轉紅**——那是刻意的：紅的意思是「回來把這段
    敘述改成事實」，⛔ 不是「有人弄壞了」。
    """
    from wf_cli import card as card_mod
    from wf_cli import cli as cli_mod

    assert card_mod.MarkerWriteBoundaryError not in cli_mod.KNOWN_ERRORS
    assert not issubclass(card_mod.MarkerWriteBoundaryError, tuple(cli_mod.KNOWN_ERRORS))


@pytest.mark.parametrize(
    "verb",
    ["assign", "handoff", "review", "checkpoint"],
)
def test_the_four_verbs_without_fold_are_registered_as_going_through_the_guard(verb):
    """⛔ **這條不跑那四支指令，它釘的是「它們共用同一個被守衛的函式」。**

    (a) 現在的行為：斷言四支動詞的模組都從 ``card`` 匯入 ``append_log_line``，且
        ``card.append_log_line`` 就是被守衛的那一個（⛔ 不是 ``_append_log_line_raw``）。
    (b) 為什麼不端到端跑：那四支的端到端各自需要真實看板狀態（owner／階段／報告／
        凍結欄位）才走得到 Log 附加那一步，而它們的指令檔**不在本卡宣告資源**內
        （A9 逐字：非射程仍為不動 ``assign_cmd``／``handoff_cmd``／``review_cmd``／
        ``checkpoint_cmd``）。⇒ 這裡只證共用，端到端登記在交付報告的未驗清單。
    (c) ⛔ **不得由此推出「那四支已端到端驗過」**——沒有。
    """
    import importlib

    module = importlib.import_module(f"wf_cli.commands.{verb}_cmd")
    from wf_cli import card as card_mod

    assert module.append_log_line is card_mod.append_log_line
    assert card_mod.append_log_line is not card_mod._append_log_line_raw


# --------------------------------------------------------------------------
# V7 未涵蓋類別：跨欄位不變量（⛔ 逐字登記，⛔ 不宣稱涵蓋）
# --------------------------------------------------------------------------


def test_cross_field_invariants_are_registered_as_out_of_scope():
    """⭐ 這條測試**不驗守衛**，它把「本守衛涵蓋不到什麼」釘成可執行的紀錄。

    §3.2 逐字：「字元層的清單不足以保證往返：**跨欄位不變量也必須擋在寫入端**。判準
    不是『值的字元合法』，而是**寫入端的接受集 ⊆ 讀取端的接受集**。」該節舉的實例是
    ``v2`` marker 的 ``card_id`` 字母集允許尾綴 ``-``，而 ``event=review`` 的三欄自洽
    檢查在讀取端會退回它——**寫得出、讀不回**。

    本守衛的兩條性質都是**單欄位**性質：它比對「這個值寫進去、再讀出來是否逐位元
    相同」，⛔ 不比對「欄位 A 與欄位 B 之間是否自洽」。⇒ 該類**不在本卡射程**，
    須另有承接者（見卡面 V7 與交付報告的承接者指名）。

    下面這個樣本每個欄位各自都讀得回，本守衛因此**放行**——⛔ 這不是缺陷，是宣稱邊界。

    ⚠️⚠️ **2026-08-27 更正（本卡 R1 的卡面錯誤，就地登記）**：上一版這段註解逐字寫
    「反例 1：``card_id`` 尾綴 ``-``」，而底下的碼跑的是 ``spec_baseline="WB-DEMO1-"``
    ⇒ **測的欄位與宣稱的欄位不同**，V7 的跨欄位反例宣稱因此不成立。現在改成真的用
    ``card_id``，並把兩件實測到的事實一起寫下來，⛔ 不再借另一個欄位假裝。
    """
    # 反例 1（§3.2 逐字舉的那個）：``card_id`` 尾綴 `-`。
    #
    # 實測事實一：**``card_id`` 根本不進 body**（它進 Issue 標題）⇒ 兩條性質在結構上
    # 看不到它。這裡以「只差一個尾綴 `-` 的兩張卡渲染出**逐位元相同**的 body」把這件事
    # 釘成可執行的斷言，⛔ 不是 `enforce_write_boundary(body, body)` 那種恆真式。
    plain = render_issue_body(make_card(card_id="WB-DEMO1"))
    trailing_dash = render_issue_body(make_card(card_id="WB-DEMO1-"))
    assert plain == trailing_dash          # 守衛的輸入裡沒有這個欄位
    assert "WB-DEMO1" not in plain         # 連字面都不在 body 裡

    # 實測事實二：§3.2 那句話裡的**讀取端**（``v2`` marker 的 ``event=review`` 三欄
    # 自洽檢查）在本 repo **尚未實作**——``review.py`` 逐字選了「方案 B：不自立第三套
    # marker 文法」。今日唯一會分解 ``card_id`` 的是 ``attempt_id``／``parse_attempt_id``，
    # 而它對尾綴 `-` 往返成立 ⇒ 該反例**今天在本 repo 無法以碼重現**。
    # ⛔ 不得由此推出「跨欄位不變量已被涵蓋」——是**沒有消費者可據以量測**，
    # 那正是 V7 要求指名承接者的理由。
    from wf_cli.review import attempt_id, parse_attempt_id

    sha = "0" * 40
    for card_id in ("WB-DEMO1", "WB-DEMO1-"):
        assert parse_attempt_id(attempt_id(card_id, 0, sha))[0] == card_id


def test_counterexample_two_body_is_authority_and_the_field_can_exist_alone():
    """反例 2（**真實樣本**，⛔ 非自造）：Project「簡介」欄有值、body 卻沒有簡介區塊。

    canonical §6.3：body 哨兵區塊為權威、Project TEXT 欄為**恆等導出** ⇒ 欄位不得單獨
    存在。2026-08-27 對全母體實跑 ``brief.drifted``，命中真實卡
    ``WF-RESOURCE-HEADING-SUFFIX1-PROBE-ASSIGN1``（🛑已停止）。

    ⭐ 兩條性質對它**完全沉默**：它們只比對「寫進 body 的值 vs 從 body 讀回的值」，
    ⛔ 從不看 Project 欄位那個平面。⇒ 跨平面不變量與跨欄位不變量同屬未涵蓋類別。
    """
    from wf_cli.brief import drifted

    no_brief = render_issue_body(make_card())  # ⛔ 不給 brief ⇒ body 無簡介區塊
    assert enforce_write_boundary(no_brief, no_brief, where="自我一致") is None
    drift, why = drifted(no_brief, "欄位上殘留的舊簡介")
    assert drift and why  # 讀取端看得到，寫入邊界看不到


def test_counterexample_three_two_db_scopes_can_disagree_on_one_card():
    """反例 3（**在真實卡面形狀上構造**）：標頭行的 ``db_scope`` 與資源宣告 JSON 的
    ``db_scope`` 可以互相矛盾，而兩條性質各自都成立。

    ``amend_resource_block`` 的往返比對只問「寫進去的宣告 == 讀回的宣告」，⛔ 不問
    「它與標頭行那一格是否一致」。⇒ 寫得出一張自相矛盾的卡；退回它的是**讀取端**的
    ``Card.__post_init__``（逐字「db_scope 與資源宣告內的 db_scope 不一致」）。
    """
    from wf_cli.resources import parse_block

    body = render_issue_body(make_card(db_scope="none"))
    new_body, _ = amend_resource_block(
        body, render_block(ResourceDeclaration(db_scope="write", resources=["file:x.py"]))
    )
    assert "- DB：db_scope=none" in new_body      # 標頭行沒動
    assert parse_block(new_body).db_scope == "write"  # JSON 已改 ⇒ 兩者矛盾
    with pytest.raises(ValueError):               # 消費者在讀取端退回
        make_card(db_scope="none", resources=parse_block(new_body))


def test_differential_probe_does_not_protect_a_path_already_broken_before_the_write():
    """⚠️ **登記差分探測自己的涵蓋界線**（V4 全母體實跑逼出來的，⛔ 不是推想）。

    (a) 現在的行為：差分探測逐字是「**寫入前讀得回**、寫入後讀不回 ⇒ 拒收」。⇒ 一條
        在寫入前**就已經**讀不回的路徑，它一律跳過。
    (b) 為什麼刻意如此：反過來（不管寫入前狀態、一律要求讀得回）會讓每一張既有損壞的
        卡連合法修訂都做不了——而「修好已壞的卡」逐字是本卡的非射程。fail-open 的方向
        選在這裡，是因為另一邊會把守衛變成故障源。
    (c) ⛔ **不得由此推出「這些卡受保護」**：2026-08-27 對全母體 204 張實跑，
        ``card.parse_requested_by`` 在 11 張上**寫入前就讀不回**（10 張需求欄是 `—`
        佔位、1 張 body 已壞）⇒ 對那 11 張，本卡新補的那類注入**寫得進去**。
        數字會漂，量法是：對每張卡跑一次 ``parse_requested_by``。
    """
    placeholder = render_issue_body(make_card(requested_by="—"))
    with pytest.raises(AmendError):
        parse_requested_by(placeholder)          # 寫入前就讀不回
    # ⇒ 同一個注入在這張卡上**不被拒收**（其餘讀取路徑無恙、簡介自己往返成立）。
    written, _ = amend_brief(placeholder, _BRIEF_WITH_STANDALONE_REQUESTER_LINE)
    assert _read_brief_text(written) == _BRIEF_WITH_STANDALONE_REQUESTER_LINE


# --------------------------------------------------------------------------
# 普查 harness 自身的性質（⭐ 這是「harness 會被跑到」的機械證明）
# --------------------------------------------------------------------------


def test_census_classifier_separates_the_buckets():
    """⭐ **這條驗的是分類器，⛔ 不是母體數字**（母體數字要跑 ``--census``）。

    餵三種**形狀已知**的 body：乾淨卡（全攔、零偽陽性）、需求欄是 ``—`` 佔位的卡
    （第 9 個動詞的注入必須落 ``excluded_pre_broken`` 並具名）、已有兩個 ``## Log``
    的卡（每個動詞的控制組都打不到它 ⇒ ``control_unusable``）。
    ⛔ 這裡不用真實卡面——真實卡面是 ``--census`` 的輸入；這條要的是「分類邏輯本身
    沒寫反」，而那需要形狀可控的樣本。
    """
    clean = render_issue_body(make_card(brief=_GOOD_BRIEF))
    placeholder = render_issue_body(make_card(brief=_GOOD_BRIEF, requested_by="—"))
    result = census([("CLEAN", clean), ("PLACEHOLDER", placeholder)])

    assert result.cards == 2
    assert result.control_false_positive == []          # 偽陽性 0
    assert result.leaked == []                          # 真漏網 0
    assert result.interception_rate == 1.0              # 排除預壞後 100%

    # 乾淨卡：一格都不該落進預壞桶。
    assert [c for c in result.cells if c.card_id == "CLEAN" and c.verdict == "excluded_pre_broken"] == []
    # 佔位卡：第 9 個動詞正是 V4 登記的那一格 ⇒ 具名排除，⛔ 不算漏網。
    excused = [c for c in result.cells
               if c.card_id == "PLACEHOLDER" and c.verdict == "excluded_pre_broken"]
    assert excused and all("parse_requested_by" in c.detail for c in excused)
    assert ("PLACEHOLDER", ("wf_cli.card.parse_requested_by",)) in result.pre_broken


def test_census_counts_a_leak_when_the_guard_is_removed():
    """⛔ **負向半邊**（§3.2 規則三逐字要求）：拿掉守衛，普查必須報出漏網。

    否則無從分辨「攔截率 100%」與「這個 harness 根本沒在量」。
    """
    from wf_cli import card as card_mod

    clean = render_issue_body(make_card(brief=_GOOD_BRIEF))
    real = card_mod.enforce_write_boundary
    card_mod.enforce_write_boundary = lambda *a, **k: None
    try:
        result = census([("CLEAN", clean)])
    finally:
        card_mod.enforce_write_boundary = real
    # ⭐ 必須落 ``leaked`` 而**不是** ``excluded_pre_broken``：守衛被拔掉時它跑得與
    # 健康卡「一樣多」（兩邊都是 0），⇒ 分類器沒有藉口可以豁免它。
    assert result.leaked, "拿掉守衛後普查仍報 0 漏網 ⇒ 這個 harness 是零資訊的"
    assert [c for c in result.cells if c.verdict == "excluded_pre_broken"] == []
    assert result.interception_rate < 1.0


def test_inline_mention_sampler_picks_mid_line_markers_only():
    """取樣器的性質：⛔ 不得把獨立成行的標題／哨兵當成行內提及。"""
    body = "\n".join([
        "## Log",                                  # 標題本身 ⇒ ⛔ 不取
        "<!-- card-brief:begin -->",               # 哨兵本身 ⇒ ⛔ 不取
        "- 說明：本節見 ## Log 那一段",              # 行內 ⇒ 取
        "  <!-- resource-claims:begin -->",        # 只有縮排，前綴無實字 ⇒ ⛔ 不取
        "見 <!-- card-brief:end --> 這個哨兵",       # 行內 ⇒ 取
    ])
    picked = [line for _, line in inline_mentions([("X", body)])]
    assert picked == ["- 說明：本節見 ## Log 那一段", "見 <!-- card-brief:end --> 這個哨兵"]


def test_inline_mention_control_rejects_nothing_on_a_healthy_corpus():
    """V2 的負控在合成語料上先自證：⛔ 誤擋必須是 0。"""
    body = "- 說明：本節見 ## Log 那一段\n見 <!-- card-brief:end --> 這個哨兵\n"
    total, rejected = inline_mention_control([("X", body)])
    assert total == 2 and rejected == []


def test_census_summary_names_every_excluded_card():
    """完整性宣稱要可稽核：排除的卡必須**逐張具名**，⛔ 不得只報一個數字。"""
    placeholder = render_issue_body(make_card(brief=_GOOD_BRIEF, requested_by="—"))
    text = census([("PLACEHOLDER", placeholder)]).summary()
    assert "PLACEHOLDER：比健康卡多跳過 wf_cli.card.parse_requested_by" in text
    assert "注入攔截率" in text


def test_roundtrip_reader_reads_what_the_amend_path_reads():
    """§3.2 規則三：解析側須走真正會跑的那條路徑。"""
    body, _ = amend_acceptance(CLEAN_BODY, ["甲", "乙"])
    assert _read_checklist_texts(body, "## 驗收條件") == ["甲", "乙"]


def test_flatten_only_removes_line_structure():
    assert _flatten_line_structure("a b\nc") == "abc"
    assert _flatten_line_structure("## Log") == "## Log"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
