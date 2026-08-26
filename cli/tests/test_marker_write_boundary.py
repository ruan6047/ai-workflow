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
    _flatten_line_structure,
    _read_checklist_texts,
    amend_acceptance,
    amend_brief,
    amend_core_pain,
    amend_initiative,
    amend_resource_block,
    amend_spec_baseline,
    amend_verification,
    body_read_paths,
    enforce_write_boundary,
    render_issue_body,
    restore_migration_header,
    split_at_log,
)
from wf_cli.cli import build_parser
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


def main() -> int:  # pragma: no cover - 供人工重跑取證，不在測試路徑上
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

    ⭐ 取樣刻意選 ``owner``：它只出現在 Log 行，本檔逐字登記過它**沒有往返讀回器**
    ⇒ 這一格是「只有性質 (1) 抓得到」的乾淨樣本。⛔ 不能拿 acceptance 當樣本——
    那一格兩條性質都抓得到，變異掉一條也不會轉紅，測不出載重。
    """
    poisoned = {"owner": "小明\u2028## Log\u2028尾"}
    # 兩條都在：拒收（``_render_with`` 把拒收轉成 ``None``）。
    assert _render_with(poisoned, structural=True, roundtrip=True) is None
    with pytest.raises(MarkerWriteBoundaryError):
        make_card(**poisoned)  # 未經變異的真實路徑同樣拒收
    # 拿掉差分探測：放行，而放行的結果是一張讀不回的卡。
    leaked = _render_with(poisoned, structural=False, roundtrip=True)
    assert leaked is not None, "只留往返比對時，結構破壞這一格仍被擋——變異無效"
    with pytest.raises(Exception):
        split_at_log(leaked)


def _render_with(card_kwargs: dict, *, structural: bool, roundtrip: bool) -> str | None:
    """以「只開其中一條性質」的守衛重跑一次 ``open`` 渲染；被拒回 ``None``。"""
    from wf_cli import card as card_mod

    real = card_mod.enforce_write_boundary

    def partial(baseline, candidate, **kwargs):  # noqa: ANN001
        real(
            baseline,
            candidate if structural else baseline,
            roundtrip=kwargs.get("roundtrip", ()) if roundtrip else (),
            where=kwargs.get("where", ""),
        )

    card_mod.enforce_write_boundary = partial
    try:
        return render_issue_body(make_card(**card_kwargs))
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


def test_open_e2e_rejects_before_any_remote_write(runner, capsys):
    """``open`` 是主破口。⚠️ **拒收目前不乾淨**——見下方 xfail 的那條。"""
    with pytest.raises(MarkerWriteBoundaryError):
        _run(
            ["open", *_TARGET, "WB-E2E2",
             "--feature", "示範", "--tier", "T1", "--db-scope", "none",
             "--core-pain", "痛點", "--service-goal", "目標\u2028## Log",
             "--exec-capability", "主力型", "--exec-capability-reason", "一般實作",
             "--review-capability", "主力型", "--review-capability-reason", "一般 review"]
        )
    # 零遠端寫入：連 project 都沒被解析出來過。
    assert runner.projects == {}
    assert runner.items == {}


@pytest.mark.xfail(
    reason=(
        "⏸ 已登記的阻塞發現：open 路徑的拒收會以 traceback 收場（rc=1），"
        "§3.2 規則二逐字要求乾淨拒絕。修法須把 card 的例外接進 cli.KNOWN_ERRORS "
        "或在 open_cmd 包一層 try——⛔ 兩檔皆非本卡宣告資源（A10），交需求方裁決。"
    ),
    strict=True,
)
def test_open_rejection_is_clean_exit_two():
    rc = _run(
        ["open", *_TARGET, "WB-E2E3",
         "--feature", "示範", "--tier", "T1", "--db-scope", "none",
         "--core-pain", "痛點", "--service-goal", "目標\u2028## Log",
         "--exec-capability", "主力型", "--exec-capability-reason", "一般實作",
         "--review-capability", "主力型", "--review-capability-reason", "一般 review"]
    )
    assert rc == 2


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
    """
    # card_id 尾綴 `-`：字元層合法、單欄位往返成立。
    body = render_issue_body(make_card(spec_baseline="WB-DEMO1-"))
    assert "spec 基線：WB-DEMO1-" in body
    assert enforce_write_boundary(body, body, where="自我一致") is None
    # ⇒ 本守衛對它無異議。跨欄位自洽是另一個平面。


def test_roundtrip_reader_reads_what_the_amend_path_reads():
    """§3.2 規則三：解析側須走真正會跑的那條路徑。"""
    body, _ = amend_acceptance(CLEAN_BODY, ["甲", "乙"])
    assert _read_checklist_texts(body, "## 驗收條件") == ["甲", "乙"]


def test_flatten_only_removes_line_structure():
    assert _flatten_line_structure("a b\nc") == "abc"
    assert _flatten_line_structure("## Log") == "## Log"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
