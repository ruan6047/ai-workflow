"""WF-CLI-CARD-AMEND1：卡面修訂的純函式與 `wfcli amend` 指令。

分兩層：純函式層不碰網路，直接對 body 字串斷言（含 Log 不被動、勾選狀態保留、
拒絕不實留痕）；指令層用 FakeGhRunner 驗證呼叫序列與 Log 內容。
"""

from __future__ import annotations

import pytest

from wf_cli.card import (
    AmendError,
    amend_acceptance,
    amend_resource_block,
    amend_spec_baseline,
    amend_verification,
    split_at_log,
)
from wf_cli.cli import build_parser
from wf_cli.commands import amend_cmd, open_cmd
from wf_cli.project import find_item_by_card_id, list_items, resolve_project
from wf_cli.resources import ResourceDeclaration, parse_block, render_block

from .fake_gh import FakeGhRunner

BODY = """- 需求：ruan6047　規劃：PM
- 執行：待指派　查核：獨立校讀
- Initiative：—　spec 基線：舊基線 abc123
- DB：db_scope=none
- 服務的原始目標：目標文字

## 核心痛點

- **痛點**：痛點文字

## 資源宣告
<!-- resource-claims:begin -->
```json
{
  "db_scope": "none",
  "resources": [
    "file:a.py"
  ]
}
```
<!-- resource-claims:end -->

## 驗收條件

- [x] 已完成的條件
- [ ] 未完成的條件

## 驗證

- [ ] 驗證一

## Log

- 2026-01-01T00:00:00+08:00 open by PM；owner 待指派；iteration 0。
"""

LOG_TAIL = "- 2026-01-01T00:00:00+08:00 open by PM；owner 待指派；iteration 0。"


def log_section(body: str) -> str:
    return split_at_log(body)[1]


# --------------------------------------------------------------------------
# 純函式：spec 基線
# --------------------------------------------------------------------------


def test_spec_baseline_replaced_and_old_value_returned():
    new_body, old = amend_spec_baseline(BODY, "新基線 dbfdb9c")
    assert old == "舊基線 abc123"
    assert "- Initiative：—　spec 基線：新基線 dbfdb9c" in new_body
    assert "舊基線 abc123" not in new_body
    # Initiative 欄不得被連帶改掉
    assert "- Initiative：—　" in new_body


def test_spec_baseline_rejects_no_op():
    with pytest.raises(AmendError, match="與現值相同"):
        amend_spec_baseline(BODY, "舊基線 abc123")


def test_spec_baseline_rejects_empty():
    with pytest.raises(AmendError, match="不得為空"):
        amend_spec_baseline(BODY, "   ")


def test_spec_baseline_rejects_missing_anchor():
    with pytest.raises(AmendError, match="必須恰好 1 次"):
        amend_spec_baseline("## Log\n\n- 只有 Log", "任何值")


# --------------------------------------------------------------------------
# 純函式：驗收／驗證清單
# --------------------------------------------------------------------------


def test_acceptance_replaced_wholesale():
    new_body, old = amend_acceptance(BODY, ["條件甲", "條件乙", "條件丙"])
    assert old == "[x] 已完成的條件；[ ] 未完成的條件"
    assert "- [ ] 條件甲" in new_body
    assert "- [ ] 條件丙" in new_body
    assert "已完成的條件" not in new_body


def test_acceptance_preserves_checkbox_state_for_unchanged_text():
    """文字沒變的項目要沿用原勾選狀態，否則修訂清單會默默取消別人的進度。"""
    new_body, _ = amend_acceptance(BODY, ["已完成的條件", "新增的條件"])
    assert "- [x] 已完成的條件" in new_body
    assert "- [ ] 新增的條件" in new_body


def test_acceptance_rejects_empty_items():
    with pytest.raises(AmendError, match="不得為空"):
        amend_acceptance(BODY, ["有效", "   "])
    with pytest.raises(AmendError, match="不得為空"):
        amend_acceptance(BODY, [])


def test_verification_replaced_and_acceptance_untouched():
    new_body, old = amend_verification(BODY, ["驗證甲"])
    assert old == "[ ] 驗證一"
    assert "- [ ] 驗證甲" in new_body
    # 相鄰章節不得被波及
    assert "- [x] 已完成的條件" in new_body
    assert "- [ ] 未完成的條件" in new_body


# --------------------------------------------------------------------------
# 純函式：資源宣告
# --------------------------------------------------------------------------


def test_resource_block_replaced_and_reparseable():
    decl = ResourceDeclaration(db_scope="read", resources=["file:b.py", "port:8080"])
    new_body, old = amend_resource_block(BODY, render_block(decl))
    assert "file:a.py" in old
    reparsed = parse_block(new_body)
    assert reparsed.db_scope == "read"
    assert reparsed.resources == ["file:b.py", "port:8080"]
    # 章節順序不得錯亂
    assert new_body.index("## 資源宣告") < new_body.index("## 驗收條件")


def test_resource_block_rejects_no_op():
    same = ResourceDeclaration(db_scope="none", resources=["file:a.py"])
    with pytest.raises(AmendError, match="與現值相同"):
        amend_resource_block(BODY, render_block(same))


# --------------------------------------------------------------------------
# 純函式：Log 不可被動（append-only 不為本能力破例）
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mutate",
    [
        lambda b: amend_spec_baseline(b, "新值")[0],
        lambda b: amend_acceptance(b, ["新條件"])[0],
        lambda b: amend_verification(b, ["新驗證"])[0],
        lambda b: amend_resource_block(
            b, render_block(ResourceDeclaration(db_scope="write", resources=[]))
        )[0],
    ],
)
def test_log_section_is_never_modified(mutate):
    assert log_section(mutate(BODY)).strip() == f"## Log\n\n{LOG_TAIL}".strip()


def test_split_rejects_duplicate_log_headings():
    with pytest.raises(AmendError, match="2 個"):
        split_at_log("## Log\n\n- a\n\n## Log\n\n- b")


def test_split_rejects_literal_newline_corrupted_log():
    """ai-workflow#17 的實際事故：Log 標題被寫成字面 \\n，排版壞掉。

    此時任何依標題定位的區段替換都可能誤動 Log，必須拒絕而不是猜。
    """
    corrupted = "- 需求：x\\n## Log\\n\\n- 條目"
    with pytest.raises(AmendError, match="不是獨立標題行"):
        split_at_log(corrupted)


def test_split_allows_body_without_log():
    head, tail = split_at_log("- 需求：x\n\n## 驗證\n\n- [ ] a\n")
    assert tail == ""
    assert "## 驗證" in head


# --------------------------------------------------------------------------
# 指令層
# --------------------------------------------------------------------------

BASE_TARGET = ["--owner", "acme", "--project", "1"]


@pytest.fixture
def fake_runner(monkeypatch):
    runner = FakeGhRunner()
    for module in (open_cmd, amend_cmd):
        monkeypatch.setattr(module, "default_runner", runner)
    return runner


def run_cli(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


@pytest.fixture
def card(fake_runner):
    rc = run_cli(
        [
            "open", *BASE_TARGET, "AMEND-DEMO1",
            "--feature", "示範", "--tier", "T1", "--db-scope", "none",
            "--core-pain", "痛點", "--service-goal", "目標",
            "--resources", "file:demo.py",
            "--acceptance", "原條件甲",
            "--verification", "原驗證甲",
            "--spec-baseline", "原基線",
        ]
    )
    assert rc == 0
    return fake_runner


def _item(runner):
    project = resolve_project(runner, "acme", 1)
    return find_item_by_card_id(list_items(runner, project), "AMEND-DEMO1")


def test_amend_writes_body_and_records_old_value_in_log(card):
    rc = run_cli(
        ["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "上游卡已 merge", "--spec-baseline", "新基線 dbfdb9c"]
    )
    assert rc == 0
    body = _item(card).body
    assert "spec 基線：新基線 dbfdb9c" in body
    assert "amend by wf-cli → spec 基線：原值「原基線」→ 新值「新基線 dbfdb9c」" in body
    assert "理由 上游卡已 merge" in body
    # 開卡那行 Log 仍在（append-only）
    assert "open by" in body


def test_amend_tier_updates_project_field_and_logs(card):
    rc = run_cli(
        ["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "開卡時填錯", "--tier", "T3"]
    )
    assert rc == 0
    item = _item(card)
    assert item.text("級別") == "T3"
    assert "amend by wf-cli → 級別：原值「T1」→ 新值「T3」" in item.body


def test_amend_rejects_same_tier(card):
    rc = run_cli(["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "無意義", "--tier", "T1"])
    assert rc == 2
    assert "amend by wf-cli" not in _item(card).body


def test_amend_requires_reason(card):
    rc = run_cli(["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "   ", "--tier", "T3"])
    assert rc == 2
    assert _item(card).text("級別") == "T1"


def test_amend_requires_at_least_one_field(card):
    rc = run_cli(["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "沒指定欄位"])
    assert rc == 2


def test_amend_dry_run_writes_nothing(card, capsys):
    before = _item(card).body
    rc = run_cli(
        ["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "先看看", "--spec-baseline", "新基線", "--dry-run"]
    )
    assert rc == 0
    assert _item(card).body == before
    assert "dry-run" in capsys.readouterr().out


def test_amend_multiple_fields_logs_one_line_each(card):
    rc = run_cli(
        [
            "amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "需求方追加",
            "--spec-baseline", "新基線",
            "--acceptance", "新條件甲", "--acceptance", "新條件乙",
            "--tier", "T2",
        ]
    )
    assert rc == 0
    body = _item(card).body
    assert body.count("amend by wf-cli") == 3
    assert _item(card).text("級別") == "T2"


def test_amend_resources_replaces_declaration(card):
    rc = run_cli(
        ["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "範圍調整", "--resources", "file:x.py,file:y.py"]
    )
    assert rc == 0
    decl = parse_block(_item(card).body)
    assert decl.resources == ["file:x.py", "file:y.py"]
    assert decl.db_scope == "none"
    assert "amend by wf-cli → 資源宣告：" in _item(card).body


def test_amend_rejects_bad_resource_prefix_without_writing(card):
    before = _item(card).body
    rc = run_cli(
        ["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "打錯", "--resources", "不合法的資源"]
    )
    assert rc == 2
    assert _item(card).body == before


def test_amend_failure_in_one_field_writes_nothing(card):
    """任一欄位驗證失敗就整批不寫，不留半套修改。"""
    before = _item(card).body
    rc = run_cli(
        [
            "amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "混合",
            "--spec-baseline", "新基線",      # 這個合法
            "--acceptance", "  ",             # 這個不合法
        ]
    )
    assert rc == 2
    assert _item(card).body == before
