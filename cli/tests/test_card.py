from __future__ import annotations

import re
from pathlib import Path

import pytest

from wf_cli.card import (
    CAPABILITY_TIERS,
    TIERS,
    Card,
    append_log_line,
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
