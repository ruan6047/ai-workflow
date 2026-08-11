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
    TIERS,
    CapabilityComparison,
    Card,
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
    match = ROUTING_LINE_RE.match(format_routing_line(card))
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
    body = LEGACY_BODY.replace(
        "- 執行：待指派　查核：獨立校讀",
        "- 執行：待指派　查核：獨立校讀\n- 執行：另一行（建議 高階型；理由）　查核：X（建議 高階型；理由）",
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
    body = LEGACY_BODY.replace(
        "- 執行：待指派　查核：獨立校讀",
        "- 執行：待指派（建議 旗艦型；理由）　查核：獨立校讀（建議 高階型；理由）",
    )
    c = compare_capability_to_card(body, "主力型")
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
            LEGACY_BODY.replace("- 執行：", "- 執行：x\n- 執行：", 1), "主力型"
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
