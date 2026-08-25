from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pytest

from wf_cli.card import (
    CAPABILITY_BASELINE_ABSENT,
    CAPABILITY_BASELINE_AMBIGUOUS,
    CAPABILITY_COMPARISON_OUTCOMES,
    CAPABILITY_DEVIATED,
    CAPABILITY_MATCHED,
    CAPABILITY_TIERS,
    ROUTING_MARKER,
    TIERS,
    AmendError,
    CapabilityComparison,
    Card,
    _routing_line_candidates,
    amend_acceptance,
    amend_spec_baseline,
    amend_verification,
    append_log_line,
    compare_capability_to_card,
    format_branch_worktree,
    format_routing_line,
    now_iso8601,
    parse_branch_worktree,
    render_issue_body,
    render_spec_markdown,
    validate_capability_routing,
)
from wf_cli.resources import ResourceDeclaration


def _make_card(**overrides):
    defaults = {
        "card_id": "DEMO-CARD1",
        "feature": "示範卡",
        "tier": "T3",
        "db_scope": "write",
        "core_pain": "機械寫入無單一通道",
        "service_goal": "消除人肉紀律缺口",
        "resources": ResourceDeclaration(db_scope="write", resources=["file:demo.py"]),
        "executor_capability": "主力型",
        "executor_capability_reason": "跨模組改動、根因已知",
        "reviewer_capability": "高階型",
        "reviewer_capability_reason": "紅線卡，須跨家族獨立查核",
    }
    defaults.update(overrides)
    return Card(**defaults)


def test_card_rejects_invalid_tier():
    with pytest.raises(ValueError):
        _make_card(tier="T9")


# ---------------------------------------------------------------------------
# 規劃期路由：能力層級語彙、缺欄硬拒、與 T0–T4 不相混（WF-CLI-ROUTING-TIER1）
# ---------------------------------------------------------------------------

_MODEL_ROUTING = Path(__file__).resolve().parents[2] / "MODEL_ROUTING.md"


def _authoritative_capability_tiers() -> set[str]:
    """直接從 ``MODEL_ROUTING.md``「預設能力等級」欄抽出權威語彙。

    這支解析器存在的唯一目的，是讓「CAPABILITY_TIERS 有沒有自創分類」變成可機械
    判定的事，而不是靠人聲稱有對過。去修飾規則與 ``card.py`` 註解一致：
    「經濟型／deterministic automation」的斜線後段是同一級的英文同義註解、
    「高階型 + 跨家族 review」的加號後段是查核獨立性附加要求，兩者都不是額外層級。
    """
    tiers: set[str] = set()
    for line in _MODEL_ROUTING.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 3:
            continue
        level = cells[1]
        if level == "預設能力等級" or set(level) <= set("-: "):  # 表頭與分隔列
            continue
        tiers.add(re.split(r"[／/+]", level)[0].strip())
    return tiers


def test_capability_tiers_are_copied_from_model_routing_not_invented():
    # 權威在 repo 根目錄；cli/ 被單獨 vendored 出去時跳過，而不是假裝通過。
    if not _MODEL_ROUTING.exists():  # pragma: no cover - 僅在脫離 repo 時發生
        pytest.skip(f"找不到權威檔 {_MODEL_ROUTING}")
    assert set(CAPABILITY_TIERS) == _authoritative_capability_tiers()


def test_capability_enum_is_closed_with_no_fallback_bucket():
    # 全函數：每個輸入落在且僅落在一格，沒有「其餘／未定／其他」逃生格。
    assert len(CAPABILITY_TIERS) == len(set(CAPABILITY_TIERS))
    assert not {"其他", "其餘", "未定", "N/A", "—"} & set(CAPABILITY_TIERS)


def test_capability_tiers_do_not_collide_with_risk_tiers():
    # 能力層級（MODEL_ROUTING）與風險級別 T0–T4 是兩條軸，值域不得有交集。
    assert set(CAPABILITY_TIERS).isdisjoint(set(TIERS))


@pytest.mark.parametrize("capability", CAPABILITY_TIERS)
def test_card_accepts_every_authoritative_capability_tier(capability):
    card = _make_card(executor_capability=capability, reviewer_capability=capability)
    assert card.executor_capability == capability


@pytest.mark.parametrize("axis", ["executor_capability", "reviewer_capability"])
def test_card_rejects_risk_tier_used_as_capability_tier(axis):
    # 誤把 T0–T4 當能力層級填是本卡預期的主要誤用；必須硬拒且訊息點名兩軸之別。
    with pytest.raises(ValueError) as exc_info:
        _make_card(**{axis: "T3"})
    message = str(exc_info.value)
    assert "MODEL_ROUTING" in message
    assert "T0–T4" in message


@pytest.mark.parametrize("axis", ["executor_capability", "reviewer_capability"])
def test_card_rejects_invented_capability_tier(axis):
    with pytest.raises(ValueError):
        _make_card(**{axis: "旗艦型"})


@pytest.mark.parametrize(
    "axis", ["executor_capability_reason", "reviewer_capability_reason"]
)
@pytest.mark.parametrize("blank", ["", "   ", "\n"])
def test_card_rejects_blank_capability_reason(axis, blank):
    # 缺欄處理＝硬拒（非預設＋警示）；訊息須寫明為何不設預設值。
    with pytest.raises(ValueError) as exc_info:
        _make_card(**{axis: blank})
    assert "必填" in str(exc_info.value)


def test_validate_capability_routing_passes_on_well_formed_input():
    validate_capability_routing(
        executor_capability="經濟型",
        executor_capability_reason="純格式與狀態同步",
        reviewer_capability="主力型",
        reviewer_capability_reason="語意不變，一般 review 即可",
    )


def test_card_rejects_db_scope_mismatch_with_resource_declaration():
    with pytest.raises(ValueError):
        _make_card(db_scope="none")  # resources 宣告是 write，與 db_scope 不一致


def test_card_accepts_chain_depth_up_to_hard_cap():
    _make_card(chain_depth=2)  # 不拋例外即算通過（0-2 皆合法）


def test_card_rejects_chain_depth_over_hard_cap():
    # 這是 CLI 層 validate_chain_depth 之外的 model 層防線：直接建構 Card（略過
    # CLI 驗證）時仍不得逃過決議 5 鏈式停損硬上限。
    with pytest.raises(ValueError) as exc_info:
        _make_card(chain_depth=3)
    assert "決議 5" in str(exc_info.value)
    assert "整鏈重審" in str(exc_info.value)


def test_branch_worktree_formatting_round_trips():
    s = format_branch_worktree("ai/agent/DEMO-CARD1", ".claude/worktrees/demo-execution")
    assert s == "ai/agent/DEMO-CARD1 @ .claude/worktrees/demo-execution"
    branch, path = parse_branch_worktree(s)
    assert branch == "ai/agent/DEMO-CARD1"
    assert path == ".claude/worktrees/demo-execution"


def test_branch_worktree_placeholder_parses_to_none():
    assert parse_branch_worktree("—") == (None, None)
    assert parse_branch_worktree("") == (None, None)


def test_format_branch_worktree_with_no_values():
    assert format_branch_worktree(None, None) == "—"


# templates/tasks-card.md 第 4 行的形狀（括號內：層級；理由。分隔用全形空白）。
ROUTING_LINE_RE = re.compile(
    r"^- 執行：(?P<executor>[^（]+)（建議 (?P<exec_tier>[^；）]+)；(?P<exec_reason>[^）]+)）"
    r"　查核：(?P<reviewer>[^（]+)（建議 (?P<rev_tier>[^；）]+)；(?P<rev_reason>[^）]+)）$"
)


def test_format_routing_line_matches_template_line4_shape():
    card = _make_card(executor="待指派", reviewer="獨立校讀")
    rendered = format_routing_line(card)
    # 第一行是機器可辨識的版本標記，第二行才是範本第 4 行本體。
    assert rendered.split("\n")[0] == ROUTING_MARKER
    match = ROUTING_LINE_RE.match(rendered.split("\n")[-1])
    assert match is not None
    assert match.group("executor") == "待指派"
    assert match.group("exec_tier") == "主力型"
    assert match.group("exec_reason") == "跨模組改動、根因已知"
    assert match.group("reviewer") == "獨立校讀"
    assert match.group("rev_tier") == "高階型"
    assert match.group("rev_reason") == "紅線卡，須跨家族獨立查核"


def test_both_renderers_emit_the_same_routing_line():
    # spec 檔與 Issue body 兩條渲染路徑不得 drift——範本一致性正是本欄位的目的。
    card = _make_card()
    line = format_routing_line(card)
    assert line in render_spec_markdown(card)
    assert line in render_issue_body(card)
    # 舊的無層級形式（#17／#19／#20 卡面長的樣子）不得再出現。
    legacy = f"- 執行：{card.executor}　查核：{card.reviewer}"
    assert legacy not in render_spec_markdown(card)
    assert legacy not in render_issue_body(card)


def test_render_spec_markdown_contains_required_sections():
    card = _make_card()
    text = render_spec_markdown(card)
    assert "# DEMO-CARD1 示範卡" in text
    assert "## 核心痛點" in text
    assert "機械寫入無單一通道" in text
    assert "## 驗收條件" in text
    assert "## 驗證" in text
    # 新架構下，可變 Ledger 欄位不重複寫進 git spec 檔。
    assert "owner" in text and "GitHub Issue" in text


def test_render_issue_body_embeds_resource_block_and_log():
    card = _make_card()
    body = render_issue_body(card)
    assert "## 資源宣告" in body
    assert "<!-- resource-claims:begin -->" in body
    assert "file:demo.py" in body
    assert "## Log" in body
    assert "open by" in body


# ---------------------------------------------------------------------------
# 派工端比對：四格全函數（WF-CLI-ROUTING-TIER1 R1-001）
# ---------------------------------------------------------------------------

# 規劃期路由必填之前開的卡長這樣（#17／#19／#20／#21 實際形狀）。
LEGACY_BODY = """- 需求：ruan6047　規劃：Claude Opus 5@Claude Code
- 執行：待指派　查核：獨立校讀
- Initiative：—　spec 基線：—

## Log

- 2026-08-11T02:22:49+08:00 open by Claude Opus 5@Claude Code；iteration 0。
"""


def _body_with_suggestion(exec_capability: str) -> str:
    return render_issue_body(
        _make_card(executor_capability=exec_capability, executor_capability_reason="理由")
    )


@pytest.mark.parametrize("outcome", CAPABILITY_COMPARISON_OUTCOMES)
def test_reason_policy_is_defined_for_every_outcome(outcome):
    # 全函數的第一半：四格各自有明確的理由政策，沒有 else 預設值。
    comparison = CapabilityComparison(outcome, "主力型", None, "")
    assert isinstance(comparison.requires_reason, bool)


def test_unknown_outcome_raises_instead_of_defaulting_to_no_reason():
    # 未來新增結果態卻忘了決定政策時，必須當場炸而不是靜默沿用「不需要理由」。
    comparison = CapabilityComparison("something-new", "主力型", None, "")
    with pytest.raises(KeyError):
        _ = comparison.requires_reason


def test_matched_when_actual_equals_card_suggestion():
    c = compare_capability_to_card(_body_with_suggestion("主力型"), "主力型")
    assert c.outcome == CAPABILITY_MATCHED
    assert c.suggested == "主力型"
    assert c.requires_reason is False


def test_deviated_when_actual_differs_from_card_suggestion():
    c = compare_capability_to_card(_body_with_suggestion("主力型"), "高階型")
    assert c.outcome == CAPABILITY_DEVIATED
    assert c.suggested == "主力型"
    assert c.requires_reason is True


def test_absent_for_cards_opened_before_routing_was_required():
    # #17／#19／#20 那批舊卡：有「- 執行：」行但沒有括號段。
    c = compare_capability_to_card(LEGACY_BODY, "主力型")
    assert c.outcome == CAPABILITY_BASELINE_ABSENT
    assert c.suggested is None
    assert c.requires_reason is True


def test_absent_when_there_is_no_executor_line_at_all():
    c = compare_capability_to_card("- 需求：ruan6047\n\n## Log\n\n- x\n", "主力型")
    assert c.outcome == CAPABILITY_BASELINE_ABSENT


def test_ambiguous_when_executor_line_is_not_unique():
    body = _body_with_line(
        f"{WELL_FORMED_LINE}\n- 執行：另一行（建議 高階型；理由）　查核：X（建議 高階型；理由）"
    )
    c = compare_capability_to_card(body, "主力型")
    assert c.outcome == CAPABILITY_BASELINE_AMBIGUOUS
    assert "2 行" in c.detail


# --- 破損卡面的系統性列舉（R2-001 回歸）-------------------------------------
#
# R2-001 的根因：解析器把「任何不匹配」都當成舊卡（absent），於是排版損壞的卡面被
# 寫成「卡面無建議層級」——不實留痕。修法是先判「這行是否自稱新制」，自稱了就必須
# 完整合格，否則 ambiguous。
#
# 下表把「不完整符合新制欄位」的破壞方式逐一列出。原則：**卡面看得出有建議、但讀
# 不出可信的層級 → 一律 ambiguous 並要求理由**；只有完全沒有新制痕跡才是 absent。

WELL_FORMED_LINE = (
    "- 執行：待指派（建議 主力型；理由甲）　查核：獨立校讀（建議 高階型；理由乙）"
)


def _body_with_line(line: str) -> str:
    """**宣告為新制**的卡面（帶版本標記），該行內容可任意破壞。"""
    return f"- 需求：x\n{ROUTING_MARKER}\n{line}\n\n## Log\n\n- x\n"


def _legacy_body_with_line(line: str) -> str:
    """**未宣告**新制的舊卡（無版本標記），該行是不受限的自由文字。"""
    return f"- 需求：x\n{line}\n\n## Log\n\n- x\n"


CORRUPTED_ROUTING_LINES = [
    # (破壞方式, 該行內容)
    ("執行理由為空", WELL_FORMED_LINE.replace("；理由甲", "；")),
    ("查核理由為空", WELL_FORMED_LINE.replace("；理由乙", "；")),
    ("執行理由只有空白", WELL_FORMED_LINE.replace("理由甲", "   ")),
    ("查核理由只有空白", WELL_FORMED_LINE.replace("理由乙", "   ")),
    ("全形分隔空白被改成半形", WELL_FORMED_LINE.replace("）　查核", "） 查核")),
    ("執行層級不在語彙內", WELL_FORMED_LINE.replace("建議 主力型", "建議 旗艦型")),
    ("查核層級不在語彙內", WELL_FORMED_LINE.replace("建議 高階型", "建議 旗艦型")),
    ("缺分號", WELL_FORMED_LINE.replace("主力型；理由甲", "主力型 理由甲")),
    ("缺右括號", WELL_FORMED_LINE.replace("理由甲）", "理由甲")),
    ("缺左括號", WELL_FORMED_LINE.replace("待指派（建議", "待指派 建議")),
    ("查核段整段缺失", "- 執行：待指派（建議 主力型；理由甲）"),
    ("執行段舊式但查核段新式", "- 執行：待指派　查核：獨立校讀（建議 高階型；理由乙）"),
    (
        "括號與分號被改成半形",
        WELL_FORMED_LINE.replace("（", "(").replace("）", ")").replace("；", ";"),
    ),
]


@pytest.mark.parametrize(
    "how,line", CORRUPTED_ROUTING_LINES, ids=[c[0] for c in CORRUPTED_ROUTING_LINES]
)
def test_corrupted_routing_line_is_ambiguous_never_absent(how, line):
    c = compare_capability_to_card(_body_with_line(line), "主力型")
    assert c.outcome == CAPABILITY_BASELINE_AMBIGUOUS, how
    assert c.requires_reason is True
    assert c.suggested is None


@pytest.mark.parametrize(
    "how,line", CORRUPTED_ROUTING_LINES, ids=[c[0] for c in CORRUPTED_ROUTING_LINES]
)
def test_corrupted_routing_line_log_never_claims_missing_baseline(how, line):
    # 查核者指定的回歸點：Log 不得把「格式受損的建議」寫成「卡面無建議層級」。
    fragment = compare_capability_to_card(_body_with_line(line), "主力型").log_fragment(
        "查核者指定的回歸情境"
    )
    assert "卡面建議無法解析" in fragment, how
    assert "卡面無建議層級" not in fragment
    assert "偏離卡面建議" not in fragment


@pytest.mark.parametrize(
    "how,line",
    [
        ("層級值前後有空白（空白不帶語意）", WELL_FORMED_LINE.replace("建議 主力型", "建議  主力型 ")),
        ("行尾有多餘空白", WELL_FORMED_LINE + "   "),
    ],
)
def test_insignificant_whitespace_still_parses_as_matched(how, line):
    # 明列「哪些變形仍算合格」，避免把寬容度也留成未定義行為。
    c = compare_capability_to_card(_body_with_line(line), "主力型")
    assert c.outcome == CAPABILITY_MATCHED, how
    assert c.suggested == "主力型"


# --- R3-001：格式版本判準必須是機器標記，不是自然語言 token -------------------
#
# 前兩輪的判準都在猜「這張卡是不是新制」：先看正規表示式有沒有匹配，再看行內有沒有
# 「建議」字樣或能力層級值。兩者都壞在同一個地方——舊制的執行／查核兩欄是**不受限的
# 自由文字**，所以：
#
#   * 舊卡寫「依建議降級」「主力型模型當班」會被誤判為新制（要求根本不存在的偏離理由）
#   * 新卡被零寬字元打斷前綴後掉出判斷，又被寫成「卡面無建議層級」——不實留痕
#
# 而且這不是判準沒調好，是問題本身無解：舊卡能產生與新卡**逐位元組相同**的一行
# （見 test_old_card_can_be_byte_identical_to_a_new_one）。所以改用遷移標記。

# 真實語料：本 repo 現存舊卡的執行行（2026-08-11 取自 Issue #7–#25），
# 證明「執行／查核欄含全形括號與自由文字」是常態而非邊緣案例。
REAL_LEGACY_LINES = [
    "- 執行：待指派　查核：待指派",
    "- 執行：待指派　查核：獨立校讀",
    "- 執行：待指派（先 grilling）　查核：跨家族架構查核",
    "- 執行：待指派　查核：跨家族查核（契約本體，依 AI_WORKFLOW.md B2 例外須走 PR）",
    "- 執行：待指派　查核：跨家族查核（T4 紅線：不可逆且會毀資料，須人工 sign-off）",
]


@pytest.mark.parametrize("line", REAL_LEGACY_LINES)
def test_real_legacy_cards_are_absent_not_ambiguous(line):
    c = compare_capability_to_card(_legacy_body_with_line(line), "主力型")
    assert c.outcome == CAPABILITY_BASELINE_ABSENT
    assert "卡面無建議層級" in c.log_fragment("舊卡無基線")


@pytest.mark.parametrize(
    "line",
    [
        "- 執行：待指派（理由：依建議降級）　查核：獨立校讀",
        "- 執行：主力型模型當班　查核：獨立校讀",
        "- 執行：待指派　查核：獨立校讀（建議由需求方決定）",
        "- 執行：經濟型　查核：高階型",
    ],
    ids=["理由含建議二字", "含主力型三字", "查核欄含建議", "兩欄剛好是層級名"],
)
def test_legacy_free_text_containing_routing_words_is_still_absent(line):
    # R3-001 指定回歸：自然語言 token 不得再觸發「自稱新制」。
    c = compare_capability_to_card(_legacy_body_with_line(line), "主力型")
    assert c.outcome == CAPABILITY_BASELINE_ABSENT
    assert c.requires_reason is True  # 無基線仍要理由，但理由是「無基線」不是「偏離」


ZWSP = "\u200b"  # 零寬空白
VS16 = "\ufe0f"  # variation selector-16


@pytest.mark.parametrize(
    "corrupt",
    [
        lambda s: ZWSP + s,  # 前綴前置零寬空白 → 掉出 startswith
        lambda s: s.replace("- 執行：", f"-{ZWSP} 執行：", 1),
        lambda s: s.replace("- 執行：", f"- 執{VS16}行：", 1),
        lambda s: s.replace("主力型", f"主{ZWSP}力型", 1),
        lambda s: s.replace("高階型", f"高{VS16}階型", 1),
    ],
    ids=["前置U+200B", "前綴內U+200B", "前綴內U+FE0F", "執行層級內U+200B", "查核層級內U+FE0F"],
)
def test_declared_new_card_broken_by_format_chars_is_ambiguous_never_absent(corrupt):
    # R3-001 指定回歸：宣告了新制的卡被零寬／格式字元破壞後，必須是 ambiguous。
    # 版本判準只看標記，所以行內字元怎麼壞都不會退化成「卡面無建議層級」。
    body = _body_with_line(corrupt(WELL_FORMED_LINE))
    c = compare_capability_to_card(body, "主力型")
    assert c.outcome == CAPABILITY_BASELINE_AMBIGUOUS
    fragment = c.log_fragment("格式字元破壞")
    assert "卡面無建議層級" not in fragment
    assert "偏離卡面建議" not in fragment


def test_well_formed_new_card_whose_reason_mentions_routing_words_still_matches():
    # 反向：合格新制卡的理由欄本來就可能寫「依建議降級」，不得因此被判壞。
    c = compare_capability_to_card(
        _body_with_line(WELL_FORMED_LINE.replace("理由甲", "依建議降級改派")), "主力型"
    )
    assert c.outcome == CAPABILITY_MATCHED


def test_old_card_can_be_byte_identical_to_a_new_one():
    """這條測試釘住「為什麼必須有標記」：兩種卡在**內容上不可區分**。

    舊制 executor／reviewer 是自由文字，填成下面這樣就與新制渲染逐位元組相同。
    只要這條成立，任何「從行內容判斷版本」的判準都必然錯——標記是唯一誠實解。
    """
    card = _make_card(
        executor="待指派",
        reviewer="獨立校讀",
        executor_capability="主力型",
        executor_capability_reason="跨模組",
        reviewer_capability="高階型",
        reviewer_capability_reason="紅線",
    )
    new_line = format_routing_line(card).split("\n")[-1]
    legacy_line = "- 執行：待指派（建議 主力型；跨模組）　查核：獨立校讀（建議 高階型；紅線）"
    assert new_line == legacy_line  # 內容不可區分

    # 但加上標記後可區分：同一行，有標記＝新制、無標記＝舊卡。
    assert (
        compare_capability_to_card(_body_with_line(legacy_line), "主力型").outcome
        == CAPABILITY_MATCHED
    )
    assert (
        compare_capability_to_card(_legacy_body_with_line(legacy_line), "主力型").outcome
        == CAPABILITY_BASELINE_ABSENT
    )


# --- R4-001：宣告是結構位置，不是子字串出現 ---------------------------------
#
# 前一版寫 `ROUTING_MARKER in head`，把「出現」當成「宣告」。但 amend 能把任意文字寫進
# Log 之前——舊卡的驗收條件只要提到這串標記，分類就從 absent 誤升 ambiguous。入口不在
# 使用者手打，在本 CLI 自己的 amend。與 R3-001 是同一個病的不同層（內容 vs 存在性）。

LEGACY_WITH_SECTIONS = (
    "- 需求：x\n"
    "- 執行：待指派　查核：獨立校讀\n"
    "\n"
    "## 驗收條件\n"
    "\n"
    "- [ ] 原條件\n"
    "\n"
    "## 驗證\n"
    "\n"
    "- [ ] 原驗證\n"
    "\n"
    "## Log\n"
    "\n"
    "- x\n"
)


@pytest.mark.parametrize(
    "amend_fn,items",
    [
        (amend_acceptance, [f"驗收要求卡面帶 {ROUTING_MARKER} 標記"]),
        (amend_acceptance, [ROUTING_MARKER]),
        (amend_acceptance, [f"前段\n{ROUTING_MARKER}\n後段"]),
        (amend_verification, [f"驗證卡面含 {ROUTING_MARKER}"]),
        (amend_verification, [ROUTING_MARKER]),
    ],
    ids=["驗收含marker", "驗收整項是marker", "驗收內嵌換行", "驗證含marker", "驗證整項是marker"],
)
def test_amend_cannot_promote_a_legacy_card_by_writing_the_marker(amend_fn, items):
    # R4-001 指定回歸：舊卡經 amend 寫入該字串後，仍須判 absent。
    assert (
        compare_capability_to_card(LEGACY_WITH_SECTIONS, "主力型").outcome
        == CAPABILITY_BASELINE_ABSENT
    )
    amended, _ = amend_fn(LEGACY_WITH_SECTIONS, items)
    assert ROUTING_MARKER in amended  # 字串確實進了 body（Log 之前）
    c = compare_capability_to_card(amended, "主力型")
    assert c.outcome == CAPABILITY_BASELINE_ABSENT  # 但那不是宣告
    assert "卡面無建議層級" in c.log_fragment("舊卡無基線")


@pytest.mark.parametrize(
    "line",
    [
        f"- 執行：待指派 {ROUTING_MARKER}　查核：獨立校讀",
        f"- 需求：x {ROUTING_MARKER}",
        f"前後有字 {ROUTING_MARKER} 還有字",
    ],
    ids=["行內夾在執行行", "行內夾在需求行", "行內前後都有字"],
)
def test_marker_not_on_its_own_line_is_not_a_declaration(line):
    # 條件 (1)：獨立成行。行內出現一律不算宣告。
    body = f"- 需求：x\n{line}\n- 執行：待指派　查核：獨立校讀\n\n## Log\n\n- x\n"
    assert (
        compare_capability_to_card(body, "主力型").outcome == CAPABILITY_BASELINE_ABSENT
    )


def test_marker_below_the_first_heading_is_not_a_declaration():
    # 條件 (2)：位於標頭區（第一個 `## ` 之前）。章節內的標記不算宣告。
    body = (
        "- 需求：x\n"
        "- 執行：待指派　查核：獨立校讀\n"
        "\n## 核心痛點\n\n"
        f"{ROUTING_MARKER}\n"
        f"{WELL_FORMED_LINE}\n"
        "\n## Log\n\n- x\n"
    )
    assert (
        compare_capability_to_card(body, "主力型").outcome == CAPABILITY_BASELINE_ABSENT
    )


def test_marker_in_header_but_not_adjacent_to_routing_line_is_ambiguous():
    # 條件 (3)：緊鄰。標記在標頭區但沒挨著路由行 → 宣告成立卻讀不出基線 → ambiguous。
    body = (
        "- 需求：x\n"
        f"{ROUTING_MARKER}\n"
        "- DB：db_scope=none\n"
        f"{WELL_FORMED_LINE}\n"
        "\n## Log\n\n- x\n"
    )
    c = compare_capability_to_card(body, "主力型")
    assert c.outcome == CAPABILITY_BASELINE_AMBIGUOUS
    assert "緊鄰" in c.detail


def test_two_declarations_in_header_are_ambiguous():
    body = (
        "- 需求：x\n"
        f"{ROUTING_MARKER}\n"
        f"{WELL_FORMED_LINE}\n"
        f"{ROUTING_MARKER}\n"
        "\n## Log\n\n- x\n"
    )
    c = compare_capability_to_card(body, "主力型")
    assert c.outcome == CAPABILITY_BASELINE_AMBIGUOUS
    assert "2 個" in c.detail


def test_amend_spec_baseline_rejects_newlines_that_would_inject_a_header_line():
    # 標頭區唯一的其他 amend 寫入路徑；單行欄位必須保持單行，否則可長出偽宣告行。
    body = render_issue_body(_make_card())
    with pytest.raises(AmendError):
        amend_spec_baseline(body, f"main abc\n{ROUTING_MARKER}")


# --- R4-003／R5-001：破損不得把 ambiguous 降成 matched ----------------------
#
# 本卡唯二錯在**不安全方向**的兩輪，形狀相同：
#
#   R4-003：候選路由行用 startswith 收 → 前置 U+200B 那行整條被略過。
#   R5-001：改成「NFKC ＋ 剝除 Cc／Cf／Mn／Me 與空白後比前綴」 → 前置 U+02B0（Lm）或
#           U+0378（Cn）這種不在剝除清單裡的碼位，照樣掉出候選集。
#
# 兩次都是「兩條路由行 → ambiguous」被降成「剩一條 → matched」，連偏離理由都免除。
# 修法不再是「多列舉一類字元」（那必然有第六次），而是把候選資格定義成**「已知非
# 路由行」的補集**：看不懂的行一律算候選。下面的測試分三層——
#
#   (1) 查核者指定的兩個碼位（U+02B0／U+0378）與 Unicode 各 general category 的代表字元；
#   (2) **全碼位**掃描：任何單一碼位當前綴都不得讓那行離開候選集（機械窮舉，非人工列舉）；
#   (3) 單調性與逐位置性質：插字元／插整行只能讓候選變多，且位置覆蓋可被證明。

INVISIBLE_CHARS = [
    "\u200b",  # ZWSP
    "\u200d",  # ZWJ
    "\ufeff",  # BOM / ZWNBSP
    "\u2060",  # WORD JOINER
    "\u00ad",  # SOFT HYPHEN
    "\ufe0f",  # VS16
]

# R5-001 \u67e5\u6838\u8005\u7684\u539f\u59cb\u6ce8\u5165\u6848\u4f8b\u3002\u5169\u8005\u90fd**\u4e0d\u5728**\u524d\u4e00\u7248\u7684\u525d\u9664\u6e05\u55ae\uff08Cc\uff0fCf\uff0fMn\uff0fMe\uff09\u5167\uff0c
# \u6240\u4ee5\u524d\u4e00\u7248\u6703\u8b93\u7b2c\u4e8c\u689d\u8def\u7531\u884c\u975c\u9ed8\u6d88\u5931\u4e26\u56de\u5831 matched\u3002
LM_MODIFIER = "\u02b0"  # MODIFIER LETTER SMALL H\uff0cgeneral category Lm
CN_UNASSIGNED = "\u0378"  # \u672a\u6307\u6d3e\u78bc\u4f4d\uff0cgeneral category Cn

# \u6027\u8cea\u6e2c\u8a66\u7528\u7684\u64fe\u52d5\u5b57\u5143\u3002**\u9019\u4efd\u6e05\u55ae\u4e0d\u662f\u6db5\u84cb\u9762\u7684\u8b49\u660e**\u2014\u2014\u6db5\u84cb\u9762\u7531\u4e0b\u9762\u7684\u5168\u78bc\u4f4d\u6383\u63cf\u8207
# \u55ae\u8abf\u6027\u65b7\u8a00\u63d0\u4f9b\uff1b\u6e05\u55ae\u53ea\u662f\u8b93\u9010\u4f4d\u7f6e\u6383\u63cf\u6709\u5177\u9ad4\u5b57\u5143\u53ef\u63d2\u3002
PERTURBATION_CHARS = [*INVISIBLE_CHARS, LM_MODIFIER, CN_UNASSIGNED]


def _two_routing_lines_body(second: str) -> str:
    return (
        "- 需求：x\n"
        f"{ROUTING_MARKER}\n"
        f"{WELL_FORMED_LINE}\n"
        f"{second}\n"
        "\n## Log\n\n- x\n"
    )


@pytest.mark.parametrize(
    "make_second",
    [
        lambda: WELL_FORMED_LINE,
        lambda: ZWSP + WELL_FORMED_LINE,
        lambda: "\ufeff" + WELL_FORMED_LINE,
        lambda: WELL_FORMED_LINE.replace("- 執行：", f"-{chr(0x200d)} 執行：", 1),
        lambda: WELL_FORMED_LINE.replace("- 執行：", "- 執行:", 1),
        lambda: WELL_FORMED_LINE.replace("執行", f"執{VS16}行", 1),
        lambda: WELL_FORMED_LINE.replace("- 執行：", "-  執行：", 1),
        lambda: WELL_FORMED_LINE + "   ",
    ],
    ids=[
        "兩條都正常", "前置ZWSP", "前置BOM", "前綴內ZWJ",
        "全形冒號改半形", "前綴含VS16", "前綴多空白", "行尾空白",
    ],
)
def test_second_routing_line_cannot_be_hidden_by_format_chars(make_second):
    # 候選集寧可多收：任何讓第二條「看起來不像」的擾動都不得使它從候選集消失。
    c = compare_capability_to_card(_two_routing_lines_body(make_second()), "主力型")
    assert c.outcome == CAPABILITY_BASELINE_AMBIGUOUS
    assert c.requires_reason is True


def test_exactly_one_routing_line_still_matches():
    # 對照組：沒有第二條時仍須正常判 matched，證明上面的嚴格不是把全部打成 ambiguous。
    body = (
        "- 需求：x\n"
        f"{ROUTING_MARKER}\n"
        f"{WELL_FORMED_LINE}\n"
        "\n## Log\n\n- x\n"
    )
    assert compare_capability_to_card(body, "主力型").outcome == CAPABILITY_MATCHED


@pytest.mark.parametrize(
    "prefix",
    [LM_MODIFIER, CN_UNASSIGNED, LM_MODIFIER + CN_UNASSIGNED, CN_UNASSIGNED + ZWSP],
    ids=["U+02B0(Lm)", "U+0378(Cn)", "Lm+Cn", "Cn+ZWSP"],
)
def test_second_routing_line_survives_categories_outside_any_strip_list(prefix):
    """R5-001 查核者的原始注入案例：前一版對這兩個碼位回報 matched 且免除理由。

    前一版剝除 Cc／Cf／Mn／Me；U+02B0 是 Lm、U+0378 是 Cn，兩者都不在清單內，於是
    第二條路由行從候選集消失、「唯一候選」成立。現行判準不看字元類別，看的是這行能不能
    被正面辨識為已知欄位行——認不出來就算候選。
    """
    c = compare_capability_to_card(_two_routing_lines_body(prefix + WELL_FORMED_LINE), "主力型")
    assert c.outcome == CAPABILITY_BASELINE_AMBIGUOUS
    assert c.requires_reason is True
    assert "有 2 行" in c.detail


def _one_codepoint_per_general_category() -> dict[str, str]:
    """每個 Unicode general category 取一個代表碼位（掃 BMP，取第一個命中）。"""
    found: dict[str, str] = {}
    for cp in range(0x110000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        ch = chr(cp)
        cat = unicodedata.category(ch)
        if cat not in found:
            found[cat] = ch
        if cp > 0xFFFF and len(found) >= 30:
            break
    return found


def test_every_general_category_prefix_keeps_the_line_in_the_candidate_set():
    """逐 general category 的代表字元：前置任何一類都不得讓那行離開候選集。

    這條刻意寫成「掃出所有類別」而非手打清單——手打清單正是 R5-001 的失敗形態
    （清單裡沒有 Lm／Cn）。
    """
    representatives = _one_codepoint_per_general_category()
    assert len(representatives) >= 25, f"只掃到 {len(representatives)} 個類別，掃描沒生效"
    for category, ch in sorted(representatives.items()):
        if ch in "\n\r":
            continue  # 換行不是「行內字元」，它會多切一行，另有插行測試覆蓋
        header = ["- 需求：x", ROUTING_MARKER, WELL_FORMED_LINE, ch + WELL_FORMED_LINE]
        assert _routing_line_candidates(header) == [2, 3], (
            f"category {category}（{ch!r}）前置後，第二條路由行離開了候選集"
        )


def test_no_single_codepoint_prefix_can_remove_a_line_from_the_candidate_set():
    """**全碼位機械窮舉**：U+0000–U+10FFFF（扣除代理區與換行）每一個碼位當前綴。

    這是本節唯一一條「窮盡」宣稱，且限定在明確的範圍內：**單一碼位前綴**這個攻擊面。
    它不宣稱涵蓋所有輸入形態——多字元前綴、行內插入、插整行分別由單調性、逐位置性質
    與插行測試覆蓋。
    """
    swept = 0
    for cp in range(0x110000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        ch = chr(cp)
        if ch in "\n\r":
            continue
        header = ["- 需求：x", ROUTING_MARKER, WELL_FORMED_LINE, ch + WELL_FORMED_LINE]
        assert _routing_line_candidates(header) == [2, 3], f"U+{cp:04X} 讓那行離開候選集"
        swept += 1
    # 掃描量由範圍算出來，不是「大於某個數」——少掃了會對不上。
    assert swept == 0x110000 - 0x800 - 2


def test_candidate_set_is_monotone_under_arbitrary_line_insertion():
    """插一整行——**不論內容是什麼碼位**——都只會讓候選變多，絕不變少。

    這是本設計的承載性保證：候選資格是「已知非路由行」的補集，插入的行只要不是那幾種
    已知形狀就是候選。攻擊者無法用「系統看不懂的行」換到更寬鬆的判定。
    """
    base_header = ["- 需求：x", ROUTING_MARKER, WELL_FORMED_LINE]
    assert _routing_line_candidates(base_header) == [2]

    covered_positions: set[int] = set()
    for insert_at in range(len(base_header) + 1):
        for ch in PERTURBATION_CHARS:
            for payload in (ch + WELL_FORMED_LINE, WELL_FORMED_LINE + ch, ch, ch * 3):
                header = base_header[:insert_at] + [payload] + base_header[insert_at:]
                assert len(_routing_line_candidates(header)) >= 2, (
                    f"插在第 {insert_at} 行的 {payload!r} 沒被算成候選"
                )
                body = "\n".join(header) + "\n\n## Log\n\n- x\n"
                assert compare_capability_to_card(body, "主力型").requires_reason is True
        covered_positions.add(insert_at)
    assert covered_positions == set(range(len(base_header) + 1))


def test_every_generated_header_line_is_positively_classified():
    """漂移守衛：渲染端產出的標頭行，除了路由行以外每一行都必須被正面辨識。

    渲染端新增／改名標頭欄位卻沒同步 ``_KNOWN_HEADER_PREFIXES`` 時這條會紅。失敗方向
    是保守的（新卡落 ambiguous），但仍要當場知道，而不是等派工時才發現全部卡都要理由。
    """
    body = render_issue_body(_make_card())
    head = body.split("\n## ")[0]
    header = head.split("\n")
    routing_index = header.index(ROUTING_MARKER) + 1
    assert _routing_line_candidates(header) == [routing_index]


def test_routing_shape_hidden_behind_a_known_prefix_is_still_a_candidate():
    # 借殼：把路由行接在已知前綴後面，企圖換到「已知非路由行」的豁免。
    body = (
        "- 需求：x\n"
        f"{ROUTING_MARKER}\n"
        f"{WELL_FORMED_LINE}\n"
        f"- DB：db_scope=none {WELL_FORMED_LINE}\n"
        "\n## Log\n\n- x\n"
    )
    c = compare_capability_to_card(body, "主力型")
    assert c.outcome == CAPABILITY_BASELINE_AMBIGUOUS
    assert c.requires_reason is True


def test_duplicated_known_header_prefix_loses_its_exemption():
    # 同一個已知欄位出現兩次＝結構異常；重複者全數回到候選集。
    header = ["- 需求：x", ROUTING_MARKER, WELL_FORMED_LINE, "- DB：a", "- DB：b"]
    assert _routing_line_candidates(header) == [2, 3, 4]
    # 單次出現則照常豁免（證明上面的嚴格不是把已知欄位一律打成候選）。
    assert _routing_line_candidates(["- 需求：x", ROUTING_MARKER, WELL_FORMED_LINE, "- DB：a"]) == [2]


# 需要理由的基準卡面：性質斷言就是要證明「破損不會讓這些卡面變得不需要理由」。
PERMISSIVENESS_BASES = {
    "兩條路由行(ambiguous)": _two_routing_lines_body(WELL_FORMED_LINE),
    "舊卡(absent)": LEGACY_WITH_SECTIONS,
    "偏離(deviated)": (
        "- 需求：x\n"
        f"{ROUTING_MARKER}\n"
        f"{WELL_FORMED_LINE}\n"
        "\n## Log\n\n- x\n"
    ),
}


def _head_lines(body: str) -> tuple[list[str], str, str]:
    head, sep, tail = body.partition("\n\n## Log")
    return head.split("\n"), sep, tail


def _char_perturbations(body: str):
    """在 Log 之前的每一行、每個位置插入每種擾動字元。

    yield ``(line_index, position, char, mutated_body)``——位置資訊一併回傳，呼叫端
    才能斷言「掃描確實覆蓋了每一行的每一個位置」，而不是只數樣本數（R5-003）。
    """
    lines, sep, tail = _head_lines(body)
    for index, line in enumerate(lines):
        for ch in PERTURBATION_CHARS:
            for pos in range(len(line) + 1):
                mutated = lines[:]
                mutated[index] = line[:pos] + ch + line[pos:]
                yield index, pos, ch, "\n".join(mutated) + sep + tail


def _expected_perturbation_slots(body: str) -> set[tuple[int, int, str]]:
    """掃描**應該**覆蓋的 (行號, 位置, 字元) 全集；獨立於受測產生器算出來。"""
    lines, _, _ = _head_lines(body)
    return {
        (index, pos, ch)
        for index, line in enumerate(lines)
        for ch in PERTURBATION_CHARS
        for pos in range(len(line) + 1)
    }


@pytest.mark.parametrize("name", sorted(PERMISSIVENESS_BASES))
def test_corruption_never_relaxes_the_reason_requirement(name):
    """性質斷言（非逐案例列舉）：破損不得讓結果比未破損更寬鬆。

    列舉永遠會漏下一種擾動，所以這裡改成掃描——在 Log 之前的每一行每個位置插入每種
    擾動字元，斷言「原本要理由的卡面，破損後仍要理由」。``matched`` 是唯一免除理由
    的結果，所以這等價於「破損不得產生偽 matched」。

    R5-003：覆蓋面**不以樣本數宣稱**。實際掃到的 (行號, 位置, 字元) 三元組必須與
    獨立算出的全集**相等**——少一個位置就當場紅，多一個也不行。
    """
    base = PERMISSIVENESS_BASES[name]
    actual = "高階型" if name.startswith("偏離") else "主力型"
    assert compare_capability_to_card(base, actual).requires_reason is True

    visited: set[tuple[int, int, str]] = set()
    for index, pos, ch, mutated in _char_perturbations(base):
        result = compare_capability_to_card(mutated, actual)
        assert result.requires_reason is True, (
            f"{name}：在第 {index} 行第 {pos} 位插入 {ch!r} 後變成 {result.outcome}"
            f"（免除理由）——破損不得讓判定變寬鬆\n{mutated!r}"
        )
        visited.add((index, pos, ch))

    expected = _expected_perturbation_slots(base)
    assert visited == expected, (
        f"{name}：掃描未覆蓋全部位置——缺 {sorted(expected - visited)[:5]}，"
        f"多 {sorted(visited - expected)[:5]}"
    )


def test_insertion_never_relaxes_a_matched_card_either():
    """對照面：基準是 ``matched``（唯一免除理由的一格）時的逐位置性質。

    上面那條測的是「要理由的卡面不得變成不要」，這條測的是「不要理由的卡面被動過之後，
    要嘛結果完全不變，要嘛變成要理由」——不存在「動了手腳卻仍以 matched 免除理由，
    但讀到的建議已經不是原本那一行」的中間態。
    """
    base = render_issue_body(_make_card(executor_capability="主力型"))
    assert compare_capability_to_card(base, "主力型").outcome == CAPABILITY_MATCHED

    visited: set[tuple[int, int, str]] = set()
    for index, pos, ch, mutated in _char_perturbations(base):
        result = compare_capability_to_card(mutated, "主力型")
        assert result.requires_reason or result.outcome == CAPABILITY_MATCHED, (
            f"第 {index} 行第 {pos} 位插入 {ch!r} 後變成 {result.outcome}"
        )
        if result.outcome == CAPABILITY_MATCHED:
            # 仍判相符時，讀到的建議必須還是原本那個值——不得讀到別行去。
            assert result.suggested == "主力型"
        visited.add((index, pos, ch))
    assert visited == _expected_perturbation_slots(base)


def test_detection_is_permissive_while_acceptance_uses_the_raw_line():
    # 兩側分工的直接斷言：偵測寬鬆（各種擾動仍算候選）、受理嚴格（原始行不合格）。
    for ch in PERTURBATION_CHARS:
        corrupted = ch + WELL_FORMED_LINE
        body = (
            "- 需求：x\n"
            f"{ROUTING_MARKER}\n"
            f"{corrupted}\n"
            "\n## Log\n\n- x\n"
        )
        c = compare_capability_to_card(body, "主力型")
        # 偵測收得到它（漏收會變成 0 候選，detail 會是「候選路由行有 0 行」）…
        assert c.outcome == CAPABILITY_BASELINE_AMBIGUOUS
        assert "候選路由行有" not in c.detail
        # …但受理端不替它補正，所以是「格式不符」而非 matched。
        assert "第 4 行格式" in c.detail


def test_renderers_emit_the_version_marker():
    card = _make_card()
    for text in (render_spec_markdown(card), render_issue_body(card)):
        assert ROUTING_MARKER in text


def test_marker_survives_an_amend_round_trip():
    # 標記若被 amend 洗掉，新卡會退化成 absent——這條鎖住那個回歸。
    body = render_issue_body(_make_card())
    amended, _ = amend_acceptance(body, ["改過的條件"])
    assert ROUTING_MARKER in amended
    assert compare_capability_to_card(amended, "主力型").outcome == CAPABILITY_MATCHED


def test_empty_reason_no_longer_counts_as_matched():
    # R2-001 (1) 的精確回歸：理由被清空的卡不得判 matched，更不得因此免除理由要求。
    c = compare_capability_to_card(
        _body_with_line(WELL_FORMED_LINE.replace("；理由甲", "；")), "主力型"
    )
    assert c.outcome != CAPABILITY_MATCHED
    assert c.requires_reason is True


def test_halfwidth_separator_no_longer_counts_as_absent():
    # R2-001 (2) 的精確回歸：排版損壞不得被寫成「卡面無建議」。
    c = compare_capability_to_card(
        _body_with_line(WELL_FORMED_LINE.replace("）　查核", "） 查核")), "主力型"
    )
    assert c.outcome != CAPABILITY_BASELINE_ABSENT
    assert c.outcome == CAPABILITY_BASELINE_AMBIGUOUS


def test_ambiguous_when_card_face_tier_is_outside_model_routing_vocabulary():
    # 有人手改卡面填了不存在的層級：不得當成「沒有建議」放行，也不得當成相符。
    c = compare_capability_to_card(
        _body_with_line(WELL_FORMED_LINE.replace("建議 主力型", "建議 旗艦型")), "主力型"
    )
    assert c.outcome == CAPABILITY_BASELINE_AMBIGUOUS
    assert "旗艦型" in c.detail


def test_ambiguous_when_body_layout_is_broken():
    broken = LEGACY_BODY.replace("\n\n## Log\n\n", "\\n## Log\\n\\n", 1)
    c = compare_capability_to_card(broken, "主力型")
    assert c.outcome == CAPABILITY_BASELINE_AMBIGUOUS


def test_all_four_outcomes_are_reachable():
    # 全函數的第二半：四格都有實際輸入能到達，沒有死格。
    observed = {
        compare_capability_to_card(_body_with_suggestion("主力型"), "主力型").outcome,
        compare_capability_to_card(_body_with_suggestion("主力型"), "高階型").outcome,
        compare_capability_to_card(LEGACY_BODY, "主力型").outcome,
        compare_capability_to_card(
            _body_with_line(f"{WELL_FORMED_LINE}\n{WELL_FORMED_LINE}"), "主力型"
        ).outcome,
    }
    assert observed == set(CAPABILITY_COMPARISON_OUTCOMES)


def test_suggestion_is_read_from_card_face_not_from_log_history():
    # Log 會引用被 amend 掉的舊值原文，其中可能含字面的「- 執行：…（建議 …）」。
    # 讀到那裡就是把歷史當現況——必須仍判 absent。
    body = append_log_line(
        LEGACY_BODY,
        "2026-08-11 amend → 原值「- 執行：待指派（建議 高階型；舊理由）　查核：X（建議 高階型；舊）」",
    )
    c = compare_capability_to_card(body, "主力型")
    assert c.outcome == CAPABILITY_BASELINE_ABSENT


def test_marker_appearing_only_in_log_does_not_promote_a_legacy_card():
    # 標記也可能被 amend 的原值引用進 Log；Log 是歷史，不得用來宣告現況版本。
    body = append_log_line(
        LEGACY_BODY, f"2026-08-11 amend → 原值「{ROUTING_MARKER}」"
    )
    assert compare_capability_to_card(body, "主力型").outcome == CAPABILITY_BASELINE_ABSENT


def test_render_then_parse_round_trips_the_suggested_tier():
    # 解析器與渲染器同檔：改了渲染形狀卻忘了改解析，這裡當場紅。
    for tier in CAPABILITY_TIERS:
        c = compare_capability_to_card(_body_with_suggestion(tier), tier)
        assert c.outcome == CAPABILITY_MATCHED
        assert c.suggested == tier


def test_compare_rejects_actual_capability_outside_vocabulary():
    with pytest.raises(ValueError) as exc_info:
        compare_capability_to_card(_body_with_suggestion("主力型"), "T3")
    assert "MODEL_ROUTING" in str(exc_info.value)


def test_log_fragment_never_calls_a_missing_baseline_a_deviation():
    absent = compare_capability_to_card(LEGACY_BODY, "主力型")
    fragment = absent.log_fragment("暫無主力型額度")
    assert "卡面無建議層級" in fragment
    assert "偏離卡面建議" not in fragment  # 不得寫成不實的「偏離」留痕
    assert "暫無主力型額度" in fragment


def test_log_fragment_records_actual_and_suggested_on_deviation():
    deviated = compare_capability_to_card(_body_with_suggestion("主力型"), "高階型")
    fragment = deviated.log_fragment("主力型當下不可用")
    assert "實際能力層級 高階型" in fragment
    assert "偏離卡面建議 主力型" in fragment
    assert "主力型當下不可用" in fragment


def test_log_fragment_keeps_optional_note_when_matched():
    matched = compare_capability_to_card(_body_with_suggestion("主力型"), "主力型")
    assert matched.log_fragment("") == "實際能力層級 主力型（與卡面建議 主力型 相符）"
    # 相符時理由非必填，但操作者若給了就照錄，不靜默丟棄。
    assert "備註：順帶說明" in matched.log_fragment("順帶說明")


def test_refusal_message_cites_model_routing_and_names_the_case():
    deviated = compare_capability_to_card(_body_with_suggestion("主力型"), "高階型")
    assert "MODEL_ROUTING" in deviated.refusal_message()
    absent = compare_capability_to_card(LEGACY_BODY, "主力型")
    assert "沒有可比對的建議層級" in absent.refusal_message()


def test_append_log_line_creates_section_if_missing():
    body = "some content without a log section"
    updated = append_log_line(body, "test entry")
    assert "## Log" in updated
    assert "- test entry" in updated


def test_append_log_line_appends_to_existing_section():
    body = "content\n\n## Log\n\n- first entry\n"
    updated = append_log_line(body, "second entry")
    assert updated.count("## Log") == 1
    assert "- first entry" in updated
    assert "- second entry" in updated
    # 附加順序：新的一行在原本內容之後（append-only，不覆寫歷史）。
    assert updated.index("first entry") < updated.index("second entry")


def test_now_iso8601_has_timezone_offset():
    ts = now_iso8601()
    assert "T" in ts
    assert ts[-3] == ":" or ts.endswith("Z")  # +08:00 形式


# ---------------------------------------------------------------------------
# 後綴相容只給資源宣告（WF-RESOURCE-HEADING-SUFFIX1）
# ---------------------------------------------------------------------------


def test_locate_section_does_not_widen_other_headings_by_default():
    """⛔ `_locate_section` 是泛用的（核心痛點／驗收條件／簡介都走它）。

    放寬若做成全域，`## 驗收條件（…）` 這種今天**不存在**的形態也會被接受
    ——那是為不存在的形態開門。⇒ 預設關閉，只有資源宣告那一個呼叫端打開。
    """
    from wf_cli.card import AmendError, _locate_section

    lines = ["## 核心痛點（補述）", "- 內容"]
    with pytest.raises(AmendError):
        _locate_section(lines, "## 核心痛點")
    # 顯式打開才認得（本函式本身有能力，是呼叫端不給）
    start, end = _locate_section(lines, "## 核心痛點", allow_suffix=True)
    assert (start, end) == (0, 2)


# ---------------------------------------------------------------------------
# 一次性結構修復：補哨兵與刪殘留（WF-RESOURCE-HEADING-SUFFIX1 第一／二段）
#
# 兩支都刻意做得很窄——它們是在修別人留下的殘留，⛔ 不是通用的區段編輯器。
# 形狀不符一律拋錯不猜，下面每一支「拒絕」測試守的就是那條。
# ---------------------------------------------------------------------------

_SUFFIXED = "## 資源宣告（機器可讀；`null`／`[]` 代表未正式宣告，不代表無資源）"
_RAW_JSON = '```json\n{\n  "db_scope": "none",\n  "resources": [\n    "file:a.py"\n  ]\n}\n```'
_WRAPPED = (
    "<!-- resource-claims:begin -->\n"
    '```json\n{"db_scope": "none", "resources": []}\n```\n'
    "<!-- resource-claims:end -->"
)


def _card(*blocks: str) -> str:
    return "- 需求：x　規劃：y\n\n" + "\n\n".join(blocks) + "\n\n## Log\n\n- 舊事件\n"


def test_adopt_sentinels_preserves_the_payload_verbatim():
    """⭐ 這是第二段的核心不變量：內容**逐字**保留。

    實測母體 33 張中有 3 張帶真實資源清單，⇒ 若改成「寫入一份新的空宣告」
    就會把它們抹掉，並把「未正式宣告」偽造成「已確認無資源」——
    那是 `aiwf#31` §3.2 逐字禁止的轉譯。
    """
    from wf_cli.card import adopt_resource_sentinels
    from wf_cli.resources import parse_block

    body = _card(_SUFFIXED + "\n" + _RAW_JSON)
    new_body, old = adopt_resource_sentinels(body)
    assert parse_block(new_body).resources == ["file:a.py"]
    # 原 fence 內容逐行仍在（只是外面多了兩行哨兵）
    for line in _RAW_JSON.splitlines():
        assert line in new_body
    assert "file:a.py" in old  # 原區段原文有回傳，供 Log 留痕


def test_adopt_sentinels_keeps_the_heading_and_trailing_marker():
    from wf_cli.card import adopt_resource_sentinels

    marker = "<!-- state-plane-mig1:card_id=X -->"
    body = _card(_SUFFIXED + "\n" + _RAW_JSON + "\n\n" + marker)
    new_body, _ = adopt_resource_sentinels(body)
    assert _SUFFIXED in new_body
    assert marker in new_body


def test_adopt_sentinels_refuses_when_already_wrapped():
    from wf_cli.card import AmendError, adopt_resource_sentinels

    with pytest.raises(AmendError):
        adopt_resource_sentinels(_card("## 資源宣告\n" + _WRAPPED))


def test_adopt_sentinels_refuses_when_the_fence_count_is_not_one():
    from wf_cli.card import AmendError, adopt_resource_sentinels

    with pytest.raises(AmendError):  # 0 個
        adopt_resource_sentinels(_card(_SUFFIXED + "\n（未正式宣告）"))
    with pytest.raises(AmendError):  # 2 個
        adopt_resource_sentinels(_card(_SUFFIXED + "\n" + _RAW_JSON + "\n" + _RAW_JSON))


def test_drop_stale_section_removes_only_the_sentinel_less_one():
    from wf_cli.card import drop_sentinel_less_resource_section
    from wf_cli.resources import parse_block

    body = _card(_SUFFIXED + "\n" + _RAW_JSON, "## 資源宣告\n" + _WRAPPED)
    new_body, removed = drop_sentinel_less_resource_section(body)
    assert _SUFFIXED not in new_body          # 殘留被刪
    assert "## 資源宣告" in new_body           # 正規區段留著
    assert parse_block(new_body).resources == []
    assert "file:a.py" in removed              # 被刪原文有回傳 ⇒ Log 留得下
    assert "舊事件" in new_body                # ⛔ Log 未被動到


def test_drop_stale_section_refuses_when_shape_is_not_exactly_two_headings():
    from wf_cli.card import AmendError, drop_sentinel_less_resource_section

    with pytest.raises(AmendError):  # 只有 1 個
        drop_sentinel_less_resource_section(_card("## 資源宣告\n" + _WRAPPED))


def test_drop_stale_section_refuses_when_both_or_neither_has_sentinels():
    from wf_cli.card import AmendError, drop_sentinel_less_resource_section

    with pytest.raises(AmendError):  # 兩個都有哨兵 → 分不出誰是殘留
        drop_sentinel_less_resource_section(
            _card(_SUFFIXED + "\n" + _WRAPPED, "## 資源宣告\n" + _WRAPPED)
        )
    with pytest.raises(AmendError):  # 兩個都沒有 → 同上
        drop_sentinel_less_resource_section(
            _card(_SUFFIXED + "\n" + _RAW_JSON, "## 資源宣告\n" + _RAW_JSON)
        )


# ---------------------------------------------------------------------------
# WF-RESOURCE-HEADING-SUFFIX1 第四段：遷移卡標頭復原
#
# ⚠️ 樣本一律取**真實既有卡面**（`cpbl#57` 於 2026-08-25 的 body，逐字），
# ⛔ 不用 `render_issue_body` 造樣本——自造樣本必然帶著範本該有的每個章節，
# ⇒ 拿它測「處理既有資料的路徑」是零資訊。這是同族第四次（`aiwf#31`／`#105`／`#134`）。
# ---------------------------------------------------------------------------

_REAL_MIGRATION_HEAD = '> 遷移自 `docs/tasks/INGEST-POSTGAME-FINALIZE1.md`（baseline `2f52562f575412a0a39b515a4436edd2831b2f65`，OPS-STATE-PLANE-MIG1 Task 2 一次性遷移；結構凍結 `a04a862`）。\n>\n> **cutover 已完成（2026-08-04，終筆 `8271d7c`）：本 Issue＋Project #4 即作業狀態唯一事實來源**；\n> events.jsonl 已封存唯讀。下方「現況摘要」為遷移當下快照，現行狀態以 Project 欄位與本 Issue 留言為準。\n> 派工時由 PM 補資源宣告區塊（canonical v2 §4.4）。\n\n## Spec\n- [`docs/tasks/INGEST-POSTGAME-FINALIZE1.md`](https://github.com/ruan6047/cpbl-analytics/blob/2f52562f575412a0a39b515a4436edd2831b2f65/docs/tasks/INGEST-POSTGAME-FINALIZE1.md)（baseline SHA `2f52562f575412a0a39b515a4436edd2831b2f65`）\n\n## 現況摘要（遷移當下，來自 Ledger @ `2f52562f575412a0a39b515a4436edd2831b2f65`）\n- Initiative：—\n- 級別：T3\n- 功能：依官方可用性補齊完賽資料\n- owner：待指派\n- 分支／worktree：—\n- iteration：0\n- 交付狀態：📥Backlog\n- 部署狀態：⏸未部署\n- 最後交接：2026-08-03T01:04:14+08:00\n\n## 新制欄位\n- 服務的原始目標：未填寫（本卡於新制欄位定案前建立，2026-08-04）\n- 鏈深：未分類（決議 5 剛定案，尚未逐卡分類；非 0）\n\n## 資源宣告（機器可讀；`null`／`[]` 代表未正式宣告，不代表無資源）\n```json\n{\n  "db_scope": "write",\n  "resources": []\n}\n```\n\n<!-- state-plane-mig1:card_id=INGEST-POSTGAME-FINALIZE1 -->\n'


def _real_migration_card(log: str = "\n\n## Log\n\n- 2026-08-04T00:00:00+08:00 open by wf-cli。") -> str:
    return _REAL_MIGRATION_HEAD + log


def test_restore_header_on_a_real_migration_card_makes_the_two_lines_parse():
    """⭐ 真正的判準不是「有插入文字」，是**既有 parser 讀得到**。"""
    from wf_cli.card import _SPEC_BASELINE_RE, parse_requested_by, restore_migration_header

    new_body, inserted = restore_migration_header(
        _real_migration_card(),
        requested_by="ruan6047",
        planned_by="本卡 spec",
        initiative="—",
        spec_baseline="`2f52562f575412a0a39b515a4436edd2831b2f65`",
    )
    assert parse_requested_by(new_body) == "ruan6047"
    # `規劃` 沒有專屬 parser，⇒ 直接驗標頭行逐字（分隔字元是全形空格 U+3000）。
    assert "- 需求：ruan6047\u3000規劃：本卡 spec" in new_body
    hits = [l for l in new_body.splitlines() if _SPEC_BASELINE_RE.match(l.strip())]
    assert len(hits) == 1
    assert "ruan6047" in inserted


def test_restore_header_adds_the_three_sections_exactly_once_each():
    from wf_cli.card import restore_migration_header

    new_body, _ = restore_migration_header(
        _real_migration_card(), requested_by="ruan6047", planned_by="x",
        initiative="—", spec_baseline="—",
    )
    lines = [l.strip() for l in new_body.split("\n## Log")[0].splitlines()]
    for heading in ("## 核心痛點", "## 驗收條件", "## 驗證"):
        assert lines.count(heading) == 1, heading


def test_restore_header_does_not_invent_content():
    """⛔ 補結構**不得產生內容**——補完後三個章節必須是空的。

    ⇒ 事後掃描仍會把這些卡報成「缺核心痛點／缺驗收」，那是**對的**結果。
    若這條斷言鬆掉，代表本函式偷偷替需求方寫了痛點。
    """
    import re

    from wf_cli.card import restore_migration_header

    new_body, _ = restore_migration_header(
        _real_migration_card(), requested_by="ruan6047", planned_by="x",
        initiative="—", spec_baseline="—",
    )
    head = new_body.split("\n## Log")[0]
    for heading in ("## 核心痛點", "## 驗收條件", "## 驗證"):
        after = head.split(heading, 1)[1]
        body_of_section = after.split("## ", 1)[0]
        assert body_of_section.strip() == "", f"{heading} 不是空的：{body_of_section!r}"
    assert not re.search(r"- \*\*痛點\*\*：", head)
    assert not re.search(r"^- \[[ xX]\] ", head, re.M)


def test_restore_header_preserves_the_original_body_verbatim():
    """⭐ 除了插入的行以外，原卡面必須**逐行**不變（含遷移 blockquote 與既有章節）。"""
    from wf_cli.card import restore_migration_header

    original = _real_migration_card()
    new_body, _ = restore_migration_header(
        original, requested_by="ruan6047", planned_by="x",
        initiative="—", spec_baseline="—",
    )
    inserted = {
        "- 需求：ruan6047　規劃：x",
        "- Initiative：—　spec 基線：—",
        "## 核心痛點",
        "## 驗收條件",
        "## 驗證",
    }
    kept = [l for l in new_body.splitlines() if l.strip() and l not in inserted]
    orig = [l for l in original.splitlines() if l.strip()]
    assert kept == orig


def test_restore_header_refuses_when_only_the_requester_line_exists():
    """⛔ 負控，且**逐道守衛隔離**。

    ⚠️ 這支測試原本兩行都放，⇒ 關掉「已有需求行」守衛後第二道照樣攔下、測試仍綠
    ——變異檢驗當場抓到它是零資訊。現在每支只放**一行**，各自釘住一道守衛。
    """
    from wf_cli.card import AmendError, restore_migration_header

    only_requester = "- 需求：ruan6047　規劃：—\n\n## Log\n\n- x"
    with pytest.raises(AmendError) as e:
        restore_migration_header(only_requester, requested_by="a", planned_by="b",
                                 initiative="—", spec_baseline="—")
    assert "需求" in str(e.value)


def test_restore_header_refuses_when_only_the_baseline_line_exists():
    from wf_cli.card import AmendError, restore_migration_header

    only_baseline = "- Initiative：—　spec 基線：—\n\n## Log\n\n- x"
    with pytest.raises(AmendError) as e:
        restore_migration_header(only_baseline, requested_by="a", planned_by="b",
                                 initiative="—", spec_baseline="—")
    assert "spec 基線" in str(e.value)


def test_restore_header_refuses_when_a_target_section_already_exists():
    from wf_cli.card import AmendError, restore_migration_header

    partial = _REAL_MIGRATION_HEAD + "\n\n## 驗收條件\n\n- [ ] x\n\n## Log\n\n- y"
    with pytest.raises(AmendError) as e:
        restore_migration_header(partial, requested_by="a", planned_by="b",
                                 initiative="—", spec_baseline="—")
    assert "驗收條件" in str(e.value)


@pytest.mark.parametrize("bad", ["", "   ", "ruan6047\u3000後綴", "ruan\n6047"])
def test_restore_header_refuses_unusable_requester_values(bad):
    """⚠️ `需求` 會成為 --ruling-url 的授權基準 ⇒ 空值或含分隔字元一律硬拒。"""
    from wf_cli.card import AmendError, restore_migration_header

    with pytest.raises(AmendError):
        restore_migration_header(_real_migration_card(), requested_by=bad,
                                 planned_by="x", initiative="—", spec_baseline="—")


# ---------------------------------------------------------------------------
# R1 查核（GPT-5@Codex）的兩個 blocking finding。
# ⚠️ 樣本逐字取自查核者給的重現方式，⛔ 不改寫、⛔ 不自造更容易通過的版本。
# ---------------------------------------------------------------------------


def test_drop_stale_refuses_a_sibling_heading_that_merely_shares_the_prefix():
    """R1-01：`## 資源宣告備註` ⛔ 不是資源宣告區段。

    查核者逐字：「用過寬的 `startswith` 判定標題。實測正常資源宣告旁有
    `## 資源宣告備註` 時，指令會把備註誤認為殘留區段並刪除。」
    ⇒ 修法是把標題判準抽成 `_heading_hit` 兩處共用，⛔ 不是在原處補 if。
    """
    from wf_cli.card import AmendError, drop_sentinel_less_resource_section

    body = _card(
        "## 資源宣告\n" + _WRAPPED + "\n\n"
        "## 資源宣告備註\n\n這段是人寫的說明，⛔ 不是殘留區段。"
    )
    with pytest.raises(AmendError):
        drop_sentinel_less_resource_section(body)


def test_drop_stale_still_works_on_the_real_dual_heading_shape():
    """⭐ 負控：收窄之後，**真正**的雙標題（帶括號補述）仍須被處理。

    ⛔ 只驗「誤刪被擋」是零資訊——那用「永遠拒絕」也能通過。
    """
    from wf_cli.card import drop_sentinel_less_resource_section

    body = _card(_SUFFIXED + "\n" + _RAW_JSON + "\n\n## 資源宣告\n" + _WRAPPED)
    new_body, removed = drop_sentinel_less_resource_section(body)
    assert _SUFFIXED not in new_body
    assert "## 資源宣告" in new_body
    assert removed


@pytest.mark.parametrize(
    "field, kwargs",
    [
        ("initiative", {"initiative": "A\n## Log\n\n- 偽造", "spec_baseline": "—"}),
        ("spec_baseline", {"initiative": "—", "spec_baseline": "B\n## Log\n\n- 偽造"}),
        ("initiative", {"initiative": "A\u3000B", "spec_baseline": "—"}),
        ("spec_baseline", {"initiative": "—", "spec_baseline": "A\u3000B"}),
    ],
)
def test_restore_header_refuses_newline_injection_in_the_other_two_fields(field, kwargs):
    """R1-02：`initiative`／`spec_baseline` 也會被寫進標頭行 ⇒ 同樣要驗。

    查核者逐字：「兩者可注入換行，實測會接受並寫出兩個 `## Log`，破壞後續解析
    與 append-only 留痕。」⚠️ 那個狀態＝ `aiwf#15`——`split_at_log` 拋錯 ⇒
    該卡**永久無法以 wfcli 修改**，而 A13 已實測它既無自動修法也無可用人工程序。
    ⛔ 原本只驗 requested_by／planned_by，是漏了一整類輸入。
    """
    from wf_cli.card import AmendError, restore_migration_header

    with pytest.raises(AmendError):
        restore_migration_header(
            _real_migration_card(), requested_by="ruan6047", planned_by="x", **kwargs
        )


def test_restore_header_still_accepts_the_real_values_used_in_production():
    """⭐ 負控：收窄之後，第四段實際寫過的 40 張的值仍須通過。

    ⛔ 只驗「注入被擋」是零資訊。這裡取真實用過的值（含帶括號的規劃者、
    反引號包住的 SHA）。
    """
    from wf_cli.card import restore_migration_header

    new_body, _ = restore_migration_header(
        _real_migration_card(),
        requested_by="ruan6047",
        planned_by="Claude Fable 5@Claude Code（PM 祕書，三問經需求方批註）",
        initiative="INIT-OFFICIAL-DATA1",
        spec_baseline="`2f52562f575412a0a39b515a4436edd2831b2f65`",
    )
    assert new_body.split("\n## Log")[0].count("## Log") == 0
    assert new_body.count("\n## Log") == 1
