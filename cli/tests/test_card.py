from __future__ import annotations

import re
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


# --- R4-003：破損不得把 ambiguous 降成 matched ------------------------------
#
# 本卡五輪來唯一一次錯在**不安全方向**。候選路由行原本用 startswith 收，前置一個
# U+200B 那行就整條被略過，於是「兩條路由行 → ambiguous」被降成「剩一條 → matched」，
# 連偏離理由都免除了。前幾輪的錯都在保守側（多要求理由），這次是放行。

INVISIBLE_CHARS = [
    "\u200b",  # ZWSP
    "\u200d",  # ZWJ
    "\ufeff",  # BOM / ZWNBSP
    "\u2060",  # WORD JOINER
    "\u00ad",  # SOFT HYPHEN
    "\ufe0f",  # VS16
]


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


def _invisible_char_perturbations(body: str):
    """在 Log 之前的每一行、每個位置插入每種不可見字元。"""
    head, sep, tail = body.partition("\n\n## Log")
    lines = head.split("\n")
    for index, line in enumerate(lines):
        for ch in INVISIBLE_CHARS:
            for pos in range(len(line) + 1):
                mutated = lines[:]
                mutated[index] = line[:pos] + ch + line[pos:]
                yield "\n".join(mutated) + sep + tail


@pytest.mark.parametrize("name", sorted(PERMISSIVENESS_BASES))
def test_corruption_never_relaxes_the_reason_requirement(name):
    """性質斷言（非逐案例列舉）：破損不得讓結果比未破損更寬鬆。

    列舉永遠會漏下一種擾動，所以這裡改成掃描——在 Log 之前的每一行每個位置插入每種
    不可見字元，斷言「原本要理由的卡面，破損後仍要理由」。``matched`` 是唯一免除理由
    的結果，所以這等價於「破損不得產生偽 matched」。
    """
    base = PERMISSIVENESS_BASES[name]
    actual = "高階型" if name.startswith("偏離") else "主力型"
    assert compare_capability_to_card(base, actual).requires_reason is True

    checked = 0
    for mutated in _invisible_char_perturbations(base):
        result = compare_capability_to_card(mutated, actual)
        assert result.requires_reason is True, (
            f"{name}：插入不可見字元後變成 {result.outcome}（免除理由）——"
            f"破損不得讓判定變寬鬆\n{mutated!r}"
        )
        checked += 1
    assert checked > 100, f"擾動樣本只有 {checked} 個，掃描範圍可能沒生效"


def test_detection_key_folds_invisibles_and_width_but_acceptance_does_not():
    # 兩側分工的直接斷言：偵測寬鬆（同一行的各種擾動都算候選）、受理嚴格（原始行不合格）。
    for ch in INVISIBLE_CHARS:
        corrupted = ch + WELL_FORMED_LINE
        body = (
            "- 需求：x\n"
            f"{ROUTING_MARKER}\n"
            f"{corrupted}\n"
            "\n## Log\n\n- x\n"
        )
        c = compare_capability_to_card(body, "主力型")
        # 偵測收得到它（否則會變成 0 候選，訊息會是「候選路由行有 0 行」）…
        assert c.outcome == CAPABILITY_BASELINE_AMBIGUOUS
        # …但受理端不替它補正，所以仍是 ambiguous 而非 matched。
        assert c.outcome != CAPABILITY_MATCHED


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
