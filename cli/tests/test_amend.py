"""WF-CLI-CARD-AMEND1：卡面修訂的純函式與 `wfcli amend` 指令。

分兩層：純函式層不碰網路，直接對 body 字串斷言（含 Log 不被動、勾選狀態保留、
拒絕不實留痕）；指令層用 FakeGhRunner 驗證呼叫序列與 Log 內容。
"""

from __future__ import annotations

import ast
import inspect
import json
import re
import string
import textwrap

import pytest

from wf_cli.card import (
    _ROUTING_PARSE_RE,
    CAPABILITY_BASELINE_ABSENT,
    CAPABILITY_BASELINE_AMBIGUOUS,
    CAPABILITY_MATCHED,
    CAPABILITY_TIERS,
    REQUESTER_GATED_TIERS,
    ROUTING_MARKER,
    ROUTING_NAME_RESERVED,
    ROUTING_REASON_RESERVED,
    ROUTING_STRUCTURAL_CHARS,
    AmendError,
    Card,
    RequesterUnparseable,
    amend_acceptance,
    amend_core_pain,
    amend_initiative,
    amend_resource_block,
    amend_spec_baseline,
    amend_verification,
    compare_capability_to_card,
    format_routing_line,
    is_tier_downgrade,
    parse_requested_by,
    split_at_log,
    tier_downgrade_needs_ruling,
)
from wf_cli.cli import build_parser
from wf_cli.commands import amend_cmd, open_cmd
from wf_cli.project import (
    ensure_fields,
    find_item_by_card_id,
    list_items,
    resolve_project,
    set_field_value,
    set_item_body,
)
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


def test_acceptance_resets_checkboxes_by_default():
    """R1-04：整份替換代表驗收語意已變動，文字相同不保證仍然成立，預設不沿用勾選。"""
    new_body, _ = amend_acceptance(BODY, ["已完成的條件", "新增的條件"])
    assert "- [ ] 已完成的條件" in new_body
    assert "- [x]" not in new_body


def test_acceptance_preserves_checkbox_state_only_when_asked():
    new_body, _ = amend_acceptance(
        BODY, ["已完成的條件", "新增的條件"], preserve_checked=True
    )
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
            "--exec-capability", "主力型", "--exec-capability-reason", "一般實作",
            "--review-capability", "主力型", "--review-capability-reason", "一般 review",
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
    assert "→ spec 基線：原值「原基線」→ 新值「新基線 dbfdb9c」" in body
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
    assert "→ 級別：原值「T1」→ 新值「T3」" in item.body


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
    assert "→ 資源宣告：" in _item(card).body


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


# --------------------------------------------------------------------------
# R1-01：原值不得截斷（Log 是唯一還原點）
# --------------------------------------------------------------------------


def test_long_original_value_is_written_to_log_in_full(card):
    long_value = "基" * 800
    run_cli(["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "先塞長值", "--spec-baseline", long_value])
    rc = run_cli(
        ["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "再改回", "--spec-baseline", "短基線"]
    )
    assert rc == 0
    body = _item(card).body
    assert f"原值「{long_value}」" in body, "超長原值必須完整寫入 Log，不得截斷"
    assert "此處截斷" not in body


def test_long_checklist_original_written_in_full(card):
    long_item = "條" * 500
    run_cli(["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "塞長清單", "--acceptance", long_item])
    rc = run_cli(["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "換掉", "--acceptance", "短條件"])
    assert rc == 0
    assert f"[ ] {long_item}" in _item(card).body


# --------------------------------------------------------------------------
# R1-02：Log 排版修復的窄路
# --------------------------------------------------------------------------






















# --------------------------------------------------------------------------
# R1-03：半寫入的偵測與自癒
# --------------------------------------------------------------------------


def test_tier_write_failure_aborts_before_touching_body(card, monkeypatch):
    """欄位寫入沒生效時讀回驗證要擋下，且 body 一個字都不能動。"""
    before = _item(card).body
    monkeypatch.setattr(amend_cmd, "set_field_value", lambda *a, **k: None)
    rc = run_cli(["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "模擬欄位寫入失敗", "--tier", "T3"])
    assert rc == 5
    assert _item(card).body == before
    assert _item(card).text("級別") == "T1"


def test_unlogged_tier_change_is_self_healed_by_rerun(card):
    """模擬「欄位寫成功、body 寫失敗」：欄位已是 T3 但 Log 沒記，重跑應只補 Log。"""
    project = resolve_project(card, "acme", 1)
    fields = ensure_fields(card, "acme", 1)
    item = _item(card)
    set_field_value(card, project, item.item_id, fields["級別"], "T3")
    assert "→ 級別" not in _item(card).body

    # 沒有旗標時必須拒絕：CLI 分不出「開卡就是這個值」與「先前半寫入」，不准猜
    assert run_cli(["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "不該猜", "--tier", "T3"]) == 2

    rc = run_cli(
        ["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "補齊先前失敗的留痕",
         "--tier", "T3", "--record-unlogged-change"]
    )
    assert rc == 0
    body = _item(card).body
    assert "級別（補記先前未留痕的變更）" in body
    assert "操作者判定為先前半寫入" in body
    assert _item(card).text("級別") == "T3"


def test_second_rerun_after_self_heal_is_rejected(card):
    """自癒過一次之後，Log 已有紀錄，再跑就是真正的 no-op，必須拒絕。"""
    project = resolve_project(card, "acme", 1)
    fields = ensure_fields(card, "acme", 1)
    item = _item(card)
    set_field_value(card, project, item.item_id, fields["級別"], "T3")
    assert run_cli(
        ["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "補齊", "--tier", "T3",
         "--record-unlogged-change"]
    ) == 0
    rc = run_cli(
        ["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "又跑一次", "--tier", "T3",
         "--record-unlogged-change"]
    )
    assert rc == 2


def test_op_id_links_log_lines_of_one_invocation(card):
    rc = run_cli(
        [
            "amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "一次改兩欄",
            "--spec-baseline", "新基線", "--tier", "T2",
        ]
    )
    assert rc == 0
    lines = [ln for ln in _item(card).body.splitlines() if "amend by wf-cli" in ln]
    assert len(lines) == 2
    ops = {ln.split("op ")[1].split("）")[0] for ln in lines}
    assert len(ops) == 1, "同一次執行的 Log 條目必須帶同一個 op 識別碼"


def test_record_unlogged_change_refuses_when_field_differs(card):
    """補記旗標只補留痕、不改欄位；欄位不是目標值時必須拒絕，避免拿它當偷改欄位的後門。"""
    rc = run_cli(
        ["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "想偷改", "--tier", "T4",
         "--record-unlogged-change"]
    )
    assert rc == 2
    assert _item(card).text("級別") == "T1"


# --------------------------------------------------------------------------
# R2-02：寫入前重讀，擋掉整份覆寫他人內容
# --------------------------------------------------------------------------


def test_amend_aborts_when_body_changed_by_another_writer(card, monkeypatch):
    project = resolve_project(card, "acme", 1)
    original_list = amend_cmd.list_items
    state = {"n": 0}

    def racing_list_items(runner, proj):
        items = original_list(runner, proj)
        state["n"] += 1
        if state["n"] == 2:  # 第二次讀取＝寫入前重讀，此時模擬他人已改動
            for it in items:
                if it.card_id == "AMEND-DEMO1":
                    it.body = it.body + "\n- 別人剛加的一行"
        return items

    monkeypatch.setattr(amend_cmd, "list_items", racing_list_items)
    rc = run_cli(
        ["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "併發", "--spec-baseline", "新基線"]
    )
    assert rc == 6
    assert "別人剛加的一行" not in _item(card).body or "新基線" not in _item(card).body


# --------------------------------------------------------------------------
# R2-03：exit 5 必須印出可直接執行的恢復指令
# --------------------------------------------------------------------------


def test_exit5_message_points_to_record_unlogged_change(card, monkeypatch, capsys):
    monkeypatch.setattr(amend_cmd, "set_field_value", lambda *a, **k: None)
    rc = run_cli(["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "模擬失敗", "--tier", "T3"])
    assert rc == 5
    err = capsys.readouterr().err
    assert "--record-unlogged-change" in err
    assert "wfcli amend AMEND-DEMO1 --tier T3" in err
    assert "操作者的宣告" in err




# --------------------------------------------------------------------------
# 備案：沒有自動修復，但必須有可執行的人工程序與機械驗證出口
# --------------------------------------------------------------------------


def test_layout_failure_prints_actionable_runbook(card, capsys):
    """排版損壞時不只是拒絕，要告訴人怎麼修、怎麼驗證修好了。"""
    project = resolve_project(card, "acme", 1)
    item = _item(card)
    corrupted = item.body.replace("\n\n## Log\n\n", "\\n## Log\\n\\n", 1)
    set_item_body(card, item.content_type, item.content_id, project, None, item.issue_number, corrupted)

    rc = run_cli(
        ["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "想改", "--spec-baseline", "新基線"]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "不是獨立標題行" in err, "先說明為什麼拒絕"
    assert "gh issue view" in err and "gh issue edit" in err, "要給可直接執行的取出／寫回指令"
    assert "--dry-run" in err, "要給機械驗證出口"
    assert "AMEND-DEMO1" in err, "驗證指令要帶上實際卡號"
    assert "繞過 wfcli" in err, "要標明這是繞過通道的訊號"
    # 拒絕就是拒絕：body 一個字都不能動
    assert _item(card).body == corrupted


def test_duplicate_log_headings_also_get_runbook(card, capsys):
    project = resolve_project(card, "acme", 1)
    item = _item(card)
    set_item_body(
        card, item.content_type, item.content_id, project, None, item.issue_number,
        item.body + "\n\n## Log\n\n- 第二個標題",
    )
    rc = run_cli(["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "想改", "--spec-baseline", "新基線"])
    assert rc == 2
    assert "gh issue edit" in capsys.readouterr().err


def test_healthy_body_does_not_print_runbook(card, capsys):
    """一般的拒收（例如 no-op）不該噴出排版 runbook，避免訊息噪音。"""
    rc = run_cli(["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "同值", "--spec-baseline", "原基線"])
    assert rc == 2
    assert "gh issue view" not in capsys.readouterr().err


@pytest.fixture
def issue_card(fake_runner):
    """真實 repo Issue 型別的卡：draft item 沒有 timeline，測不到 --escalate 的留言路徑。"""
    rc = run_cli(
        ["open", *BASE_TARGET, "--repo", "acme/wf", "ESC-DEMO1",
         "--feature", "示範", "--tier", "T1", "--db-scope", "none",
         "--core-pain", "痛點", "--service-goal", "目標", "--spec-baseline", "原基線",
         "--exec-capability", "主力型", "--exec-capability-reason", "一般實作",
         "--review-capability", "主力型", "--review-capability-reason", "一般 review"]
    )
    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = find_item_by_card_id(list_items(fake_runner, project), "ESC-DEMO1")
    assert item.content_type == "Issue" and item.issue_number is not None
    corrupted = item.body.replace("\n\n## Log\n\n", "\\n## Log\\n\\n", 1)
    set_item_body(fake_runner, item.content_type, item.content_id, project, "acme/wf",
                  item.issue_number, corrupted)
    return fake_runner, corrupted


_ESC_TARGET = ["--owner", "acme", "--project", "1", "--repo", "acme/wf"]


def _esc_item(runner):
    project = resolve_project(runner, "acme", 1)
    return find_item_by_card_id(list_items(runner, project), "ESC-DEMO1")


def test_escalate_leaves_durable_comment_without_touching_body(issue_card, monkeypatch):
    runner, corrupted = issue_card
    posted: list = []
    monkeypatch.setattr(amend_cmd, "add_issue_comment",
                        lambda r, repo, n, b: posted.append((repo, n, b)))
    rc = run_cli(["amend", *_ESC_TARGET, "ESC-DEMO1", "--reason", "想改",
                  "--spec-baseline", "新基線", "--escalate"])
    assert rc == 2
    assert _esc_item(runner).body == corrupted, "body 一個字都不能動"
    assert len(posted) == 1, "真 Issue 卡必須實際留言（不可像舊測試那樣兩路都放行）"
    _, _, comment = posted[0]
    assert "wf-amend-blocked:v1" in comment
    assert "ESC-DEMO1" in comment
    assert "需要人或 AI 接手" in comment
    assert "gh issue edit" in comment


def test_escalate_skipped_under_dry_run(issue_card, monkeypatch, capsys):
    """--dry-run 承諾零遠端寫入；留言同樣是寫入，不得破例。"""
    runner, _ = issue_card
    posted: list = []
    monkeypatch.setattr(amend_cmd, "add_issue_comment", lambda *a: posted.append(a))
    rc = run_cli(["amend", *_ESC_TARGET, "ESC-DEMO1", "--reason", "試算",
                  "--spec-baseline", "新基線", "--dry-run", "--escalate"])
    assert rc == 2
    assert posted == [], "dry-run 期間不得送出任何留言"
    assert "略過 --escalate 的留言" in capsys.readouterr().err


def test_escalate_comment_failure_does_not_crash(issue_card, monkeypatch, capsys):
    """升級是盡力而為；它失敗不得蓋掉原本的拒收語意與 runbook。"""
    runner, _ = issue_card

    def boom(*a, **k):
        raise RuntimeError("GitHub 500")

    monkeypatch.setattr(amend_cmd, "add_issue_comment", boom)
    rc = run_cli(["amend", *_ESC_TARGET, "ESC-DEMO1", "--reason", "想改",
                  "--spec-baseline", "新基線", "--escalate"])
    assert rc == 2, "留言失敗不得改變退出碼"
    err = capsys.readouterr().err
    assert "留言失敗" in err
    assert "gh issue edit" in err, "runbook 仍須可見"


def test_escalate_is_noop_for_non_layout_rejections(card, capsys, monkeypatch):
    posted: list = []
    monkeypatch.setattr(amend_cmd, "add_issue_comment", lambda *a: posted.append(a))
    rc = run_cli(
        ["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "同值", "--spec-baseline", "原基線", "--escalate"]
    )
    assert rc == 2
    assert not posted, "一般拒收不該留升級紀錄"
    assert "只對排版損壞生效" in capsys.readouterr().err


# --------------------------------------------------------------------------
# R4：runbook 必須真的能跑（前一版從未被實跑過，同時出了兩個錯）
# --------------------------------------------------------------------------


def _issue17_shaped_body() -> str:
    """#17 的關鍵形狀：Log 內文本身含合法的字面 \\n（那行在描述「把字面 \\n 還原」）。"""
    return (
        "- 需求：x\n- Initiative：—　spec 基線：base\n\n"
        "## 驗證\n\n- [ ] v\n\n"
        "## Log\n\n"
        "- 2026-08-10 open。\n"
        "- 2026-08-10 repair；將誤寫的字面 \\n 還原為真換行。\n"
    )


def _run_verify(tmp_path, orig: str, fixed: str) -> str:
    """實際執行 stderr runbook 第 3 步印出的那一行指令。"""
    import subprocess

    (tmp_path / "orig.md").write_text(orig, encoding="utf-8")
    (tmp_path / "body.md").write_text(fixed, encoding="utf-8")
    cmd = amend_cmd._LAYOUT_VERIFY_SNIPPET.replace(
        "/tmp/orig.md", str(tmp_path / "orig.md")
    ).replace("/tmp/body.md", str(tmp_path / "body.md"))
    out = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    assert out.returncode == 0, f"驗證指令本身跑不起來：{out.stderr}"
    return out.stdout.strip()


def test_runbook_verify_accepts_correct_issue17_repair(tmp_path):
    """R4-02：#17 的正確修復不得被誤判為竄改（Log 內合法的字面 \\n 必須留著）。"""
    good = _issue17_shaped_body()
    corrupted = good.replace("\n\n## Log\n\n", "\\n## Log\\n\\n", 1)
    assert "\\n 還原為真換行" in corrupted, "前提：Log 內文仍有合法的字面 \\n"
    assert _run_verify(tmp_path, corrupted, good).startswith("必要條件通過")


def test_runbook_verify_rejects_extra_edits(tmp_path):
    good = _issue17_shaped_body()
    corrupted = good.replace("\n\n## Log\n\n", "\\n## Log\\n\\n", 1)
    tampered = good.replace("spec 基線：base", "spec 基線：偷改的值")
    assert _run_verify(tmp_path, corrupted, tampered).startswith("NG")


def test_runbook_verify_rejects_stripping_legit_literal_newline(tmp_path):
    """把 Log 內文合法的字面 \\n 也「順手還原」是錯的，必須被抓到。"""
    good = _issue17_shaped_body()
    corrupted = good.replace("\n\n## Log\n\n", "\\n## Log\\n\\n", 1)
    overzealous = good.replace("字面 \\n 還原", "字面 \n 還原")
    assert _run_verify(tmp_path, corrupted, overzealous).startswith("NG")


def test_runbook_step1_creates_the_file_step3_reads(card, capsys):
    """R4-01：第 3 步讀 orig.md，第 1 步就必須建立它，否則整份程序跑不動。"""
    project = resolve_project(card, "acme", 1)
    item = _item(card)
    set_item_body(card, item.content_type, item.content_id, project, None, item.issue_number,
                  item.body.replace("\n\n## Log\n\n", "\\n## Log\\n\\n", 1))
    run_cli(["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "想改", "--spec-baseline", "新基線"])
    err = capsys.readouterr().err
    assert "cp /tmp/body.md /tmp/orig.md" in err, "runbook 必須自己建立 orig 副本"
    assert err.index("cp /tmp/body.md") < err.index("python3 - /tmp/orig.md"), "建立要早於使用"


# --------------------------------------------------------------------------
# R5-01：「OK」只是必要條件，不是安全證明
#
# 查核者打穿兩處：多個候選 token 時 replace(...,1) 只修第一個，剩下的損壞留著卻
# 印 OK；code fence 內的 token 被誤修後，split_at_log 還會把它當成唯一 Log 標題。
# 根因是把「第一個字串被替換了」當成「那個字串是 Log 標題」的證明。
# --------------------------------------------------------------------------


def test_verify_refuses_when_multiple_candidate_tokens(tmp_path):
    """多處候選時必須拒絕，而不是修掉第一個就宣稱通過。"""
    good = _issue17_shaped_body()
    corrupted = good.replace("\n\n## Log\n\n", "\\n## Log\\n\\n", 1)
    corrupted += "\n- 範例：\\n## Log\\n\\n 這行也長得像\n"
    fixed_first_only = corrupted.replace("\\n## Log\\n\\n", "\n\n## Log\n\n", 1)
    out = _run_verify(tmp_path, corrupted, fixed_first_only)
    assert out.startswith("NG"), "多 token 時不得印通過"
    assert "2 處候選標記" in out


def test_verify_refuses_token_inside_code_fence_by_count(tmp_path):
    """code fence 內另有一處候選時同樣落入「不只一處」而被擋下。"""
    good = _issue17_shaped_body()
    corrupted = good.replace("\n\n## Log\n\n", "\\n## Log\\n\\n", 1)
    corrupted = "```text\n\\n## Log\\n\\n- 範例\n```\n\n" + corrupted
    out = _run_verify(tmp_path, corrupted, corrupted.replace("\\n## Log\\n\\n", "\n\n## Log\n\n", 1))
    assert out.startswith("NG")


def test_verify_output_disclaims_being_a_safety_proof(tmp_path):
    """通過訊息必須明說它不是安全證明，並要求人工確認語意位置。"""
    good = _issue17_shaped_body()
    corrupted = good.replace("\n\n## Log\n\n", "\\n## Log\\n\\n", 1)
    out = _run_verify(tmp_path, corrupted, good)
    assert "不是安全證明" in out
    assert "code fence" in out


def test_runbook_requires_human_judgement_and_full_diff(card, capsys):
    """runbook 必須含「無法機械化的人工判斷」與「審閱完整 diff」兩步。"""
    project = resolve_project(card, "acme", 1)
    item = _item(card)
    set_item_body(card, item.content_type, item.content_id, project, None, item.issue_number,
                  item.body.replace("\n\n## Log\n\n", "\\n## Log\\n\\n", 1))
    run_cli(["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "想改", "--spec-baseline", "新基線"])
    err = capsys.readouterr().err
    assert "必要條件，不是安全證明" in err
    assert "人工判斷（無法機械化）" in err
    assert "diff /tmp/orig.md /tmp/body.md" in err
    assert "不證明那個標題在對的位置" in err


# ==========================================================================
# 殘餘射程卡：核心痛點的授權綁定／級別降級的不對稱／雙居所欄位同步
# ==========================================================================
#
# 三項的設計理由見 commands/amend_cmd.py 的模組 docstring。這裡只釘行為。


# --------------------------------------------------------------------------
# 純函式：核心痛點
# --------------------------------------------------------------------------


def test_core_pain_replaced_and_old_value_returned():
    new_body, old = amend_core_pain(BODY, "新的痛點敘述")
    assert old == "痛點文字"
    assert "- **痛點**：新的痛點敘述" in new_body
    assert "痛點文字" not in split_at_log(new_body)[0]


def test_core_pain_does_not_touch_log():
    new_body, _ = amend_core_pain(BODY, "新的痛點敘述")
    assert log_section(new_body).strip() == "## Log\n\n" + LOG_TAIL


def test_core_pain_rejects_empty():
    """空值等於移除具否決權的判準來源，不是一次合法的更正。"""
    with pytest.raises(AmendError, match="不得為空"):
        amend_core_pain(BODY, "   ")


def test_core_pain_rejects_newline():
    """允許換行會讓下一次修訂定位不到唯一錨點，把可改欄位變成不可改。"""
    with pytest.raises(AmendError, match="不得含換行"):
        amend_core_pain(BODY, "第一行\n第二行")


def test_core_pain_rejects_no_op():
    with pytest.raises(AmendError, match="與現值相同"):
        amend_core_pain(BODY, "痛點文字")


def test_core_pain_rejects_missing_anchor():
    body = BODY.replace("- **痛點**：痛點文字", "痛點不見了")
    with pytest.raises(AmendError, match="必須恰好 1 次"):
        amend_core_pain(body, "任何值")


# --------------------------------------------------------------------------
# 純函式：Initiative
# --------------------------------------------------------------------------


def test_initiative_replaced_without_touching_spec_baseline():
    new_body, old = amend_initiative(BODY, "ai-workflow#99")
    assert old == "—"
    assert "- Initiative：ai-workflow#99　spec 基線：舊基線 abc123" in new_body


def test_initiative_and_spec_baseline_are_independent():
    """兩者同一行；改其中一個時另一個必須逐字保留。"""
    once, _ = amend_initiative(BODY, "ai-workflow#99")
    twice, _ = amend_spec_baseline(once, "新基線 zzz")
    assert "- Initiative：ai-workflow#99　spec 基線：新基線 zzz" in twice


def test_initiative_rejects_no_op_and_empty():
    with pytest.raises(AmendError, match="與現值相同"):
        amend_initiative(BODY, "—")
    with pytest.raises(AmendError, match="不得為空"):
        amend_initiative(BODY, "  ")


# --------------------------------------------------------------------------
# 純函式：需求方解析（跨卡共用）
# --------------------------------------------------------------------------


def test_parse_requested_by_reads_declared_account():
    assert parse_requested_by(BODY) == "ruan6047"


def test_parse_requested_by_ignores_log_quotations():
    """Log 區段內若出現行首的「- 需求：」，不得被當成現況讀。

    不切掉 Log 就會把歷史當成現況——與 compare_capability_to_card 同一個理由。
    這種行在手寫／遷移進來的舊卡上是真的會出現的（本 repo 有 18 張前 CLI 時代的卡）。

    註：污染行必須**行首**就是「- 需求：」才真的重現危害。內嵌在其他文字中的
    引用（如「舊值「- 需求：x」」）不會匹配 ^ 錨點，拿它當固定裝置會讓這條測試
    因為錯誤的理由變綠——本測試先前正是如此，經突變測試 M8 抓出後改成現在這樣。
    """
    polluted = BODY + "- 需求：attacker　規劃：X\n"
    assert "## Log" in polluted.split("- 需求：attacker")[0], "污染行必須落在 Log 區段內"
    assert parse_requested_by(polluted) == "ruan6047"


def test_parse_requested_by_fails_closed_when_absent():
    body = BODY.replace("- 需求：ruan6047　規劃：PM\n", "")
    with pytest.raises(RequesterUnparseable, match="必須恰好 1 次"):
        parse_requested_by(body)


def test_parse_requested_by_fails_closed_on_placeholder():
    """「—」是佔位符不是帳號；當成帳號會讓授權比對變成比對佔位字串。"""
    body = BODY.replace("- 需求：ruan6047　", "- 需求：—　")
    with pytest.raises(RequesterUnparseable, match="未宣告實際帳號"):
        parse_requested_by(body)


def test_parse_requested_by_fails_closed_when_ambiguous():
    body = BODY.replace("- DB：db_scope=none", "- 需求：someone　規劃：X")
    with pytest.raises(RequesterUnparseable, match="必須恰好 1 次"):
        parse_requested_by(body)


# --------------------------------------------------------------------------
# 純函式：級別降級判準
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("old", "new", "downgrade", "needs_ruling"),
    [
        ("T4", "T2", True, True),    # 移除紅線卡的跨家族／人工 sign-off
        ("T4", "T3", True, True),    # 移除 T4 的同步對抗式質詢
        ("T3", "T2", True, True),    # 移除 T3 的三問放行
        ("T2", "T1", True, False),   # T2 以下無需求方閘門可移除
        ("T1", "T0", True, False),
        ("T2", "T4", False, False),  # 升級是安全方向
        ("T3", "T3", False, False),
        (None, "T2", False, False),  # 讀不出原值不當成降級
    ],
)
def test_tier_downgrade_table(old, new, downgrade, needs_ruling):
    assert is_tier_downgrade(old, new) is downgrade
    assert tier_downgrade_needs_ruling(old, new) is needs_ruling


def test_requester_gated_tiers_match_canonical_gate_levels():
    """canonical §3.1 只有 T3／T4 的閘門由需求方親自操作。

    這條釘的是**判準的來源**：降級授權要求綁在這兩級，不是憑感覺選的門檻。
    """
    assert REQUESTER_GATED_TIERS == ("T3", "T4")


# --------------------------------------------------------------------------
# 指令層：授權綁定
# --------------------------------------------------------------------------

REQUESTER = "ruan6047"
GOV_TARGET = ["--owner", "acme", "--project", "1", "--repo", "acme/wf"]


class CommentAwareRunner(FakeGhRunner):
    """FakeGhRunner ＋ `gh api /repos/<o>/<r>/issues/comments/<id>` 的唯讀替身。

    留言 author 由測試指定，模擬平台身分。刻意實作成「查不到就拋」，讓
    fail-closed 路徑真的被走到，而不是回一個空 dict 讓比對悄悄通過。
    """

    def __init__(self) -> None:
        super().__init__()
        self.comment_authors: dict[str, str] = {}
        self.api_calls: list[str] = []

    def execute(self, args, input=None):  # type: ignore[override]
        args = list(args)
        if args[:1] == ["api"] and "/issues/comments/" in args[1]:
            self.api_calls.append(args[1])
            comment_id = args[1].rsplit("/", 1)[-1]
            if comment_id not in self.comment_authors:
                raise AssertionError(f"no such comment {comment_id}")
            return json.dumps({"user": {"login": self.comment_authors[comment_id]}})
        return super().execute(args, input)


@pytest.fixture
def gov_runner(monkeypatch):
    runner = CommentAwareRunner()
    for module in (open_cmd, amend_cmd):
        monkeypatch.setattr(module, "default_runner", runner)
    return runner


@pytest.fixture
def gov_card(gov_runner):
    """真實 Issue 卡，需求方欄填實際帳號、tier 為 T4（可測降級）。"""
    rc = run_cli(
        ["open", *GOV_TARGET, "GOV-DEMO1",
         "--feature", "示範", "--tier", "T4", "--db-scope", "none",
         "--core-pain", "原始痛點", "--service-goal", "目標",
         "--requested-by", REQUESTER, "--planned-by", "PM",
         "--resources", "file:demo.py", "--spec-baseline", "原基線",
         "--exec-capability", "主力型", "--exec-capability-reason", "一般實作",
         "--review-capability", "高階型", "--review-capability-reason", "紅線跨家族"]
    )
    assert rc == 0
    gov_runner.comment_authors["555"] = REQUESTER
    return gov_runner


def _gov_item(runner):
    project = resolve_project(runner, "acme", 1)
    return find_item_by_card_id(list_items(runner, project), "GOV-DEMO1")


def _ruling(comment_id: str = "555", issue: int = 1, repo: str = "acme/wf") -> str:
    return f"https://github.com/{repo}/issues/{issue}#issuecomment-{comment_id}"


def test_core_pain_requires_ruling_url(gov_card):
    """只有 --reason 的自述不足以改具否決權的欄位。"""
    rc = run_cli(["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "想改", "--core-pain", "新痛點"])
    assert rc == 2
    assert "原始痛點" in _gov_item(gov_card).body


def test_core_pain_cannot_share_an_invocation_with_other_fields(gov_card):
    """op 識別碼與治理裁定必須 1:1，否則稽核者分不出授權的是哪一項。"""
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "順手一起改",
         "--core-pain", "新痛點", "--spec-baseline", "新基線",
         "--ruling-url", _ruling()]
    )
    assert rc == 2
    item = _gov_item(gov_card)
    assert "原始痛點" in item.body and "原基線" in item.body


def test_core_pain_succeeds_with_requester_ruling_and_records_authority(gov_card):
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "需求方縮小射程",
         "--core-pain", "收窄後的痛點", "--ruling-url", _ruling()]
    )
    assert rc == 0
    body = _gov_item(gov_card).body
    assert "- **痛點**：收窄後的痛點" in body
    assert "→ 核心痛點：原值「原始痛點」→ 新值「收窄後的痛點」" in body
    # 授權必須逐字留在 Log：稽核者要能區分「開卡就這樣寫」與「事後經誰裁定改的」
    assert f"授權 依需求方 {REQUESTER} 於" in body
    # 註記的措辭本身由 test_authority_note_* 三條釘住（見下）。


# 授權註記的**措辭**：字面為真還不夠，語意不得誇大（WF-AMEND-AUTHZ-BINDING1）
#
# 本卡治的病：舊註記「GitHub comment author 已逐字核對，非留言內文自述」字面為真
# （確實比對過），語意卻誤導——後半句把本檢查描述成「排除了自述」，讀者因此以為
# 它有區辨力。而 amend 這條路徑從不讀取操作者身分，且本 repo 只有一個人類帳號
# （PM 的 gh 與需求方同為 ruan6047），那道比對對代貼者恆真，從未區辨過任何東西。
# 已實現後果：13 筆事件／9 張卡（2026-08-16 對 Project #4 全部 148 個 item 逐張掃描）。
#
# ---- 守衛的形狀：四代演進，以及為什麼這一代不是第五代的前身 -----------------
#
# 前三代打的是「這串字說了什麼」，我每次釘一個**性質**，下一輪就有人找到不違反該
# 性質卻仍然誇大的寫法：
#
#   R0 「…已逐字核對，非留言內文自述」   → 那是區辨力宣稱
#   R1 「宣告完整性已檢查：…」            → 總結標籤，涵蓋範圍大於列出的內容
#   R2 拿掉標籤 ＋ 釘住「（」後的插入位置 → 標籤改插在第一個事實**之後**即繞過
#                                            （R2-001，實測 3 passed）
#
# R3 用逐字比對把那一族關掉了：措辭與位置都是開放集合，而「必須恰好等於這串字」
# 是封閉的。**那個判斷沒有被推翻。**
#
# 第四代打的是另一件事——**守衛涵蓋哪些輸入**：
#
#   R3 逐字比對函式的**回傳值** → 只以 fixture 的固定 (author, url) 呼叫一次。
#      M20：`'' if url.endswith('-555') else '授權綁定成立；'`，fixture 那組維持
#      黃金值、其他合法輸入帶標籤，970 tests 全綠（R3-001 blocking）。
#
# 對輸出取樣，取幾組都還是取樣——**輸入也是開放集合**。所以這一輪不是「再多測幾組
# comment id」（那才是第五代），而是把斷言的對象從「一次呼叫的輸出」搬到「產生輸出
# 的那個東西」：
#
#   (1) 模板唯一且逐字被釘        —— test_authority_note_template_is_verbatim_golden
#   (2) 函式恆為「模板 ＋ 代入」    —— test_authority_note_is_template_substitution_
#                                     by_construction（AST，非取樣）
#
# 模板只有一個 ∧ 函式只會回它的代入 ⇒ 對所有 (author, url) 都是同一個模板的代入。
# 量詞從「對這些輸入」變成「由構造」，這是與前四代不同層的東西。
#
# **為什麼不受空白 reflow 影響**（#57 R5 同型陷阱）：斷言對象是**執行期字串**與
# **AST**，都不是原始碼文字。實作用相鄰字串常值併接，換行／縮排怎麼排都不改變兩者。
#
# ---- 威脅模型：這組守衛防誰，以及防不到誰 ---------------------------------
#
# **防的是無意的後續編輯，不防蓄意繞過的提交者。**（需求方 2026-08-16 裁定）
#
# 無意的那一類，下列四個實例已實測會紅：
#
#   M20 依 comment id 分支，讓 fixture 那組維持黃金值
#   M22 模板加一個 `{label}` 插值、預設空字串
#   M25 直接改模板措辭
#   M26b 執行期以 globals() 把模板換成帶標籤的版本
#
# ⚠️ **這是四個實例，不是對「所有無意編輯」的保證**——那一類同樣是開放集合，而本卡
# 四輪的教訓就是不要再對開放集合下全稱宣稱。這裡只說這四個跑過、都紅。
#
# 蓄意的那一類**已知不涵蓋且不修**：M27（在 return 前改寫 `author`）繞得過上面的
# AST，因為 AST 釘的是 return 的語法、不是 `author` 這個值的來源。要關掉就得約束
# 資料流，而其後還有裝飾器、`_resolve_ruling_author` 內部、以及 monkeypatch。
# **對擁有這份碼的人，任何測試與任何執行期檢查都無效。**
#
# ⚠️ 這是比例判斷不是證明。需求方 2026-08-16 裁定原句，**逐字保留、不得軟化**，
# 刻意不折行以免日後 reflow 把它拆散（#57 R5 同型陷阱）：
#
#     需求方不能證明 M27 不會發生，只能說它不是這個守衛被開出來要擋的東西
#
# **已知不涵蓋的縫**（四條，不宣稱其中任何一條已被處理）：
#
#   1. AST 只約束 `_authorize_by_requester_ruling` 一個函式；模組別處用
#      `globals()[...] = ...` 這種動態寫法改常數，AST 看不見。
#   2. **執行期 monkeypatch 無解**：原始碼層面攔不住，沒有辦法。
#   3. 呼叫端事後加工（`run()` 的 `_fold`）只由固定輸入的測試覆蓋，仍是取樣。
#   4. 模板與測試黃金值兩邊同時改錯仍會綠：保證「被看見」，不保證「被看對」。

#: 已退役的措辭。**不是**守衛，只是讓歷史上被打掉的兩句各留一個具名的回歸點，
#: 失敗訊息才看得出「又退回哪一代」。
#: R0：宣稱本比對排除了「留言內文自述」，即宣稱了它沒有的區辨力。
#: R1：把兩個欄位相等總結成一個名為「完整性」、斷言「已檢查」的結論（R1-001）。
_RETIRED_CLAIMS = ("非留言內文自述", "宣告完整性已檢查")

#: 授權註記模板的**逐字**黃金值。`{author}` 與 `{url}` 是僅有的兩個插值點，
#: 其餘每一個字元都被釘死。改這個常數＝改治理留痕的措辭，請連同 amend_cmd 一起改。
_GOLDEN_AUTHORITY_NOTE = (
    "依需求方 {author} 於 {url} 的裁定"
    "（已核對：該 URL 指向本卡 issue 的既存留言，"
    "且其 GitHub author 欄逐字等於卡面「需求：」欄。"
    "本指令不讀取留言內文或操作者身分，故不判定留言內容是否構成裁定"
    "——上句「裁定」是操作者的宣告，不是本指令查得的事實——"
    "亦不區分「需求方本人張貼」與「他人代擬代貼」）"
)


def _golden_note(url: str | None = None) -> str:
    return _GOLDEN_AUTHORITY_NOTE.format(author=REQUESTER, url=url or _ruling())


def _amend_core_pain(gov_card) -> str:
    """跑一次成功的核心痛點更正，回傳卡面 body。"""
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "需求方縮小射程",
         "--core-pain", "收窄後的痛點", "--ruling-url", _ruling()]
    )
    assert rc == 0
    return _gov_item(gov_card).body


def _authority_note_of(gov_card, url: str | None = None) -> str:
    """直接取 `_authorize_by_requester_ruling` 的**原始回傳值**（未經 `_fold`）。

    不透過卡面 body 取，是為了讓斷言看到的就是實作產出的那一份字串：body 那條
    路徑會先經過 `_fold`（摺行），而摺行有可能把「多打了一個換行」這種改動吃掉。
    直接取回傳值就沒有這層轉換，逐字比對才真的是逐字。
    """
    import argparse

    from wf_cli.config import resolve_target

    return amend_cmd._authorize_by_requester_ruling(
        gov_card,
        resolve_target(owner="acme", project=1, repo="acme/wf"),
        _gov_item(gov_card),
        argparse.Namespace(ruling_url=url or _ruling()),
        "核心痛點更正",
    )


def test_authority_note_template_is_verbatim_golden():
    """守衛 (1)：模板本身逐字元等於黃金值，且**只有一個**模板。

    對輸出取樣永遠只是取樣（R3-001）；對模板取值不是——模板不吃輸入，它是常數。
    這一條因此對所有 (author, url) 一次成立。
    """
    assert amend_cmd.AUTHORITY_NOTE_TEMPLATE == _GOLDEN_AUTHORITY_NOTE
    # 插值點恰為兩個資料欄位。多一個 `{label}` 之類的插值會讓上面那行先紅，
    # 這裡再把「可用的欄位名只有這兩個」講成機械事實。
    assert sorted(
        f[1] for f in string.Formatter().parse(amend_cmd.AUTHORITY_NOTE_TEMPLATE) if f[1] is not None
    ) == ["author", "url"]


def _authorize_source_tree():
    """`_authorize_by_requester_ruling` 的 AST（去掉縮排後 parse）。"""
    src = textwrap.dedent(inspect.getsource(amend_cmd._authorize_by_requester_ruling))
    return ast.parse(src).body[0]


def test_authority_note_is_template_substitution_by_construction():
    """守衛 (2)：函式**恆為**「模板 ＋ 代入」——由構造，不是由取樣。

    這一條是 R3-001 的直接處置。M20 的形狀是「依 url 分支，fixture 那組回黃金值、
    其他輸入回帶標籤的字串」；只要斷言是對輸出做的，多測幾組也只是把取樣點加密，
    仍然擋不住一個針對測試輸入特化的實作。

    所以改成約束**原始碼形狀**：函式只有一個 return，且該 return 的運算式逐節點
    等於 ``AUTHORITY_NOTE_TEMPLATE.format(author=author, url=args.ruling_url)``。
    在此形狀下輸出恆等於模板代入，因此**不存在**任何輸入能得到別的字串——任何
    條件式、f-string、字串拼接、額外 kwarg 都會讓 AST 不相等。

    比對方式刻意是「兩邊都用同一個 ``ast.dump``」而非寫死 dump 字串：後者會隨
    Python 版本的 dump 格式改變而假紅。
    """
    fn = _authorize_source_tree()
    returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return)]
    assert len(returns) == 1, f"預期恰好一個 return，實際 {len(returns)} 個"
    # 沒有巢狀函式／lambda：否則 return 可能藏在別的作用域裡
    nested = [
        n for n in ast.walk(fn)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) and n is not fn
    ]
    assert nested == [], "本函式內不得有巢狀函式或 lambda"

    expected = ast.parse(
        "AUTHORITY_NOTE_TEMPLATE.format(author=author, url=args.ruling_url)", mode="eval"
    ).body
    assert ast.dump(returns[0].value) == ast.dump(expected)

    # 模板名在函式內只能被讀取，不得被重新指派／遮蔽
    stores = [
        n for n in ast.walk(fn)
        if isinstance(n, ast.Name)
        and n.id == "AUTHORITY_NOTE_TEMPLATE"
        and not isinstance(n.ctx, ast.Load)
    ]
    assert stores == [], "AUTHORITY_NOTE_TEMPLATE 不得在函式內被重新指派"


def test_authority_note_template_is_assigned_exactly_once_in_the_module():
    """守衛 (3)：模組內只有一處指派該常數。

    補的是 (2) 的縫：AST 只約束那一個函式，擋不住「模組別處把常數換掉」。這一條
    讓 import 期改寫也要改到一個看得見的地方。

    ⚠️ 仍擋不住執行期 monkeypatch——那不是原始碼層面攔得住的，見交付說明。
    """
    module_ast = ast.parse(inspect.getsource(amend_cmd))
    targets = [
        t
        for node in ast.walk(module_ast)
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign))
        for t in (node.targets if isinstance(node, ast.Assign) else [node.target])
        if isinstance(t, ast.Name) and t.id == "AUTHORITY_NOTE_TEMPLATE"
    ]
    assert len(targets) == 1, f"預期恰好一處指派，實際 {len(targets)} 處"


@pytest.mark.parametrize(
    "author, comment_id",
    [
        ("ruan6047", "555"),
        ("ruan6047", "999"),
        ("some-other-requester", "555"),
        ("some-other-requester", "424242"),
    ],
)
def test_runtime_output_matches_the_template_for_varied_inputs(gov_runner, author, comment_id):
    """交叉檢查：實際執行的輸出確實等於模板代入。

    ⚠️ **這一條不是封閉性的來源**——它是取樣，四組擋不住第五組。封閉性來自 (1)+(2)。
    它的作用是證明「我對 AST 的解讀」與「執行期真的發生的事」沒有脫節：AST 斷言
    讀的是原始碼，這條讀的是實際回傳值，兩者對上才排除「我把 AST 讀錯了」。

    仍刻意換掉 author 與 comment id 兩個維度，讓 R3-001 的 M20（依 url 分支）在
    這一條上也會紅，而不是只在 AST 那條紅。
    """
    import argparse

    from wf_cli.config import resolve_target

    rc = run_cli(
        ["open", *GOV_TARGET, "GOV-VARY1",
         "--feature", "示範", "--tier", "T4", "--db-scope", "none",
         "--core-pain", "原始痛點", "--service-goal", "目標",
         "--requested-by", author, "--planned-by", "PM",
         "--resources", "file:vary.py", "--spec-baseline", "原基線",
         "--exec-capability", "主力型", "--exec-capability-reason", "一般實作",
         "--review-capability", "高階型", "--review-capability-reason", "紅線跨家族"]
    )
    assert rc == 0
    gov_runner.comment_authors[comment_id] = author
    project = resolve_project(gov_runner, "acme", 1)
    item = find_item_by_card_id(list_items(gov_runner, project), "GOV-VARY1")
    url = _ruling(comment_id, issue=item.issue_number)

    note = amend_cmd._authorize_by_requester_ruling(
        gov_runner,
        resolve_target(owner="acme", project=1, repo="acme/wf"),
        item,
        argparse.Namespace(ruling_url=url),
        "核心痛點更正",
    )
    assert note == _GOLDEN_AUTHORITY_NOTE.format(author=author, url=url)


def test_golden_note_also_reaches_the_log_verbatim(gov_card):
    """黃金值不只要從函式出來，還要原封不動落進 Log 的授權欄。

    分成兩條的理由：上一條證明**產出**正確，這一條證明**寫入路徑**沒有加工它
    （例如被 `_fold` 摺掉、被截斷、或混進 `--reason` 的自由文字）。前後各釘一個
    界線字元，讓比對在 Log 行內是封閉的而不是鬆散的子字串。
    """
    body = _amend_core_pain(gov_card)
    assert f"；授權 {_golden_note()}。" in body


def test_golden_note_is_reflow_stable(gov_card):
    """把「正規化規則」本身釘住：這裡的規則是**不做正規化**。

    #57 R5 抓到過同型陷阱——banned 字串因排版 reflow 的空白而沒命中。本組不受
    該類影響，理由是斷言對象為執行期字串，而實作用相鄰字串常值併接，原始碼怎麼
    換行都不改變結果。本測試把「黃金值不含任何連續空白或換行」變成機械事實，
    從而保證 Log 寫入時的 `_fold`（`" ".join(text.split())`）對它是恆等函式；
    否則 body 那條斷言就會在「多一個換行」時被摺行悄悄救回來。
    """
    note = _authority_note_of(gov_card)
    assert "\n" not in note and "\t" not in note
    assert "  " not in note
    assert " ".join(note.split()) == note, "note 經 _fold 後應完全不變"


def test_authority_note_still_discloses_the_three_limits(gov_card):
    """⚠️ 本條**不是守衛**（守衛是上面的黃金值那條）。

    它記錄的是：若有人**刻意**更新黃金值，哪些內容必須存活下來。黃金值那條會逼
    改動被看見，這條說明看見之後該檢查什麼——本函式沒看的東西有三類：留言內文、
    操作者身分，以及由前兩者衍生的「這則留言到底算不算裁定」。
    """
    note = _authority_note_of(gov_card)
    assert "該 URL 指向本卡 issue 的既存留言" in note
    assert "其 GitHub author 欄逐字等於卡面「需求：」欄" in note
    assert "本指令不讀取留言內文或操作者身分" in note
    assert "不判定留言內容是否構成裁定" in note
    assert "不區分「需求方本人張貼」與「他人代擬代貼」" in note
    assert "上句「裁定」是操作者的宣告，不是本指令查得的事實" in note


def test_retired_claims_never_come_back(gov_card):
    """⚠️ 同上，**不是守衛**，是具名的回歸點。

    黃金值那條已經涵蓋這兩句；分開留著只為了讓失敗訊息直接說出「退回了哪一代」，
    而不是丟一坨字串 diff 給讀的人自己比對。
    """
    note = _authority_note_of(gov_card)
    for claim in _RETIRED_CLAIMS:
        assert claim not in note, f"已退役的誇大措辭又出現在授權欄：{claim!r}"


def test_core_pain_rejected_when_ruling_author_is_not_the_requester(gov_card):
    """**授權綁定的承重測試**：留言存在、URL 形狀正確、指向本卡，但 author 不是需求方。

    這一條若因為 author 比對被拿掉而轉綠，等於任何人在本卡留一則言就能改
    具否決權的欄位——正是 review-escalation.md §4 (a′) 要擋的那件事。
    """
    gov_card.comment_authors["666"] = "someone-else"
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "冒充裁定",
         "--core-pain", "被冒充改掉的痛點", "--ruling-url", _ruling("666")]
    )
    assert rc == 2
    body = _gov_item(gov_card).body
    assert "原始痛點" in body
    assert "被冒充改掉的痛點" not in body
    assert "amend by wf-cli" not in body


def test_core_pain_rejected_when_ruling_author_is_the_current_owner(gov_card):
    """裁定者不得是被該裁定嘉惠的人（review-escalation.md §4 第 3 款同向）。"""
    project = resolve_project(gov_card, "acme", 1)
    fields = ensure_fields(gov_card, "acme", 1)
    set_field_value(gov_card, project, _gov_item(gov_card).item_id, fields["owner"], REQUESTER)
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "自己裁定自己",
         "--core-pain", "自己改的痛點", "--ruling-url", _ruling()]
    )
    assert rc == 2
    assert "原始痛點" in _gov_item(gov_card).body


def test_ruling_url_must_point_at_this_card(gov_card):
    """指向他卡的裁定不成立——形狀對不等於指涉對。"""
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "搬別卡的裁定",
         "--core-pain", "新痛點", "--ruling-url", _ruling(issue=99)]
    )
    assert rc == 2
    assert "原始痛點" in _gov_item(gov_card).body


def test_ruling_url_must_point_at_this_repo(gov_card):
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "站外連結",
         "--core-pain", "新痛點", "--ruling-url", _ruling(repo="evil/elsewhere")]
    )
    assert rc == 2
    assert "原始痛點" in _gov_item(gov_card).body


@pytest.mark.parametrize(
    "bad_url",
    [
        "https://github.com/acme/wf/issues/1",                 # 沒指到單一留言
        "https://example.com/acme/wf/issues/1#issuecomment-5",  # 站外
        "acme/wf#1",                                            # 非 URL
    ],
)
def test_ruling_url_shape_is_fail_closed(gov_card, bad_url):
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "形狀不對",
         "--core-pain", "新痛點", "--ruling-url", bad_url]
    )
    assert rc == 2
    assert "原始痛點" in _gov_item(gov_card).body


def test_core_pain_rejected_when_requester_field_unparseable(gov_card):
    """「需求：」欄無法解析時 fail-closed，不得退回「找不到就放行」。"""
    project = resolve_project(gov_card, "acme", 1)
    item = _gov_item(gov_card)
    set_item_body(
        gov_card, item.content_type, item.content_id, project, "acme/wf", item.issue_number,
        item.body.replace(f"- 需求：{REQUESTER}　", "- 需求：—　"),
    )
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "需求方欄被清空",
         "--core-pain", "新痛點", "--ruling-url", _ruling()]
    )
    assert rc == 2
    assert "原始痛點" in _gov_item(gov_card).body


def test_core_pain_rejected_when_comment_cannot_be_read(gov_card):
    """取不到 author 一律拒絕，不得以「讀不到就當作成立」放行。"""
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "留言不存在",
         "--core-pain", "新痛點", "--ruling-url", _ruling("404404")]
    )
    assert rc == 2
    assert "原始痛點" in _gov_item(gov_card).body


def test_core_pain_unavailable_on_draft_cards(card):
    """draft item 沒有 timeline，授權綁定不可用——此時拒絕，而不是略過檢查。"""
    rc = run_cli(
        ["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "draft 卡",
         "--core-pain", "新痛點", "--ruling-url", _ruling()]
    )
    assert rc == 2
    assert "痛點" in _item(card).body


# --------------------------------------------------------------------------
# 指令層：級別降級的不對稱
# --------------------------------------------------------------------------


def test_tier_downgrade_from_redline_requires_ruling(gov_card):
    """T4→T2 會移除紅線卡的跨家族／人工 sign-off 要求。"""
    rc = run_cli(["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "想降級", "--tier", "T2"])
    assert rc == 2
    assert _gov_item(gov_card).text("級別") == "T4"


def test_tier_downgrade_from_redline_succeeds_with_ruling(gov_card):
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "需求方裁定非紅線",
         "--tier", "T2", "--ruling-url", _ruling()]
    )
    assert rc == 0
    item = _gov_item(gov_card)
    assert item.text("級別") == "T2"
    # 降級必須逐字標記，稽核者不必自己比 T 值大小
    assert "→ 級別（降級）：原值「T4」→ 新值「T2」" in item.body
    assert f"授權 依需求方 {REQUESTER} 於" in item.body
    # 降級與核心痛點共用同一個 ruling_note，故**同一個黃金值也適用這條路徑**。
    # 用完整黃金值而非片段：日後若把兩條路徑拆成各自的註記，其中一條改了措辭
    # 就會在這裡當場紅，不會靜默退化（跨家族查核 R1 的非阻擋建議）。
    assert f"；授權 {_golden_note()}。" in item.body


def test_tier_upgrade_needs_no_ruling(gov_card):
    """升級是加保護的方向，不設額外門檻。"""
    project = resolve_project(gov_card, "acme", 1)
    fields = ensure_fields(gov_card, "acme", 1)
    set_field_value(gov_card, project, _gov_item(gov_card).item_id, fields["級別"], "T2")
    rc = run_cli(["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "查核判為紅線", "--tier", "T4"])
    assert rc == 0
    item = _gov_item(gov_card)
    assert item.text("級別") == "T4"
    assert "→ 級別：原值「T2」→ 新值「T4」" in item.body
    assert "（降級）" not in item.body


def test_tier_downgrade_below_gate_threshold_needs_no_ruling(gov_card):
    """T2 以下沒有需求方親自操作的閘門可移除，只需 --reason；仍標記為降級。"""
    project = resolve_project(gov_card, "acme", 1)
    fields = ensure_fields(gov_card, "acme", 1)
    set_field_value(gov_card, project, _gov_item(gov_card).item_id, fields["級別"], "T2")
    rc = run_cli(["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "範圍比預期小", "--tier", "T1"])
    assert rc == 0
    item = _gov_item(gov_card)
    assert item.text("級別") == "T1"
    assert "→ 級別（降級）：原值「T2」→ 新值「T1」" in item.body


def test_unneeded_ruling_url_is_not_recorded_as_authority(gov_card):
    """未經核對的 URL 不得進 Log——指標不證明內容，寫進去會誤導稽核者。

    刻意選**級別升級**當固定裝置：那條路徑的 changes 確實會帶 ruling_note，
    所以「授權註記只在真的核對過時才存在」在這裡是可被打破的性質。
    （先前用 --spec-baseline 寫這條，而該路徑硬編 None，測試因此對任何突變
    免疫——綠得沒有理由。經突變測試 M9 抓出後改成現在這樣。）
    """
    project = resolve_project(gov_card, "acme", 1)
    fields = ensure_fields(gov_card, "acme", 1)
    set_field_value(gov_card, project, _gov_item(gov_card).item_id, fields["級別"], "T2")
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "查核判為紅線，回到 T4",
         "--tier", "T4", "--ruling-url", _ruling()]
    )
    assert rc == 0
    body = _gov_item(gov_card).body
    assert "→ 級別：原值「T2」→ 新值「T4」" in body
    # 比對 Log 的授權欄位標記本身（`；授權 …`），不是裸字串「授權」——後者會被
    # --reason 的自由文字誤中，那正是本測試先前紅得莫名其妙的原因。
    assert "；授權 " not in body
    assert "issuecomment-555" not in body


# --------------------------------------------------------------------------
# 指令層：雙居所欄位同步
# --------------------------------------------------------------------------


def test_resources_amend_writes_both_body_and_project_field(gov_card):
    """先前只寫 body，Project 欄位留在開卡值——本測試釘住兩面同步。"""
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "收窄宣告",
         "--resources", "file:a.py,file:b.py"]
    )
    assert rc == 0
    item = _gov_item(gov_card)
    assert item.text("資源宣告") == "db_scope=none；file:a.py、file:b.py"
    assert parse_block(item.body).resources == ["file:a.py", "file:b.py"]


def test_db_scope_amend_also_syncs_project_field(gov_card):
    rc = run_cli(["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "改唯讀", "--db-scope", "read"])
    assert rc == 0
    item = _gov_item(gov_card)
    assert item.text("資源宣告").startswith("db_scope=read；")
    assert parse_block(item.body).db_scope == "read"


def test_stale_project_field_converges_on_rerun(gov_card):
    """**這條是雙面同步的迴歸樁，形狀取自實際事故。**

    現場有一張 T4 卡：body 已被 amend 收窄／擴充過，Project 欄位卻仍是開卡值——
    看板顯示它只佔一份文件，實際持有八個檔（含 cleanup.py／doctor.py／
    handoff_cmd.py）。那是 **fail-open** 方向：靠看板／Ledger 判斷佔用的人會低估它。
    （assign 的交集檢查讀 body，所以擋派工是對的；壞的是看板那一面。）

    本測試重現該狀態，並要求「重跑同一條 amend」即收斂，而不是拒為 no-op。
    """
    project = resolve_project(gov_card, "acme", 1)
    fields = ensure_fields(gov_card, "acme", 1)
    item = _gov_item(gov_card)
    wide = ["file:cli/src/wf_cli/cleanup.py", "file:cli/src/wf_cli/doctor.py",
            "file:cli/src/wf_cli/commands/handoff_cmd.py"]
    # body 走 amend（會同步兩面），再把 Project 欄位手動打回窄值，製造事故狀態
    assert run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "擴充宣告",
         "--resources", ",".join(wide)]
    ) == 0
    set_field_value(gov_card, project, item.item_id, fields["資源宣告"],
                    "db_scope=none；file:docs/only-one-file.md")
    assert parse_block(_gov_item(gov_card).body).resources == wide
    assert _gov_item(gov_card).text("資源宣告") == "db_scope=none；file:docs/only-one-file.md"

    # 重跑同一條 amend：body 已是目標值，不得拒為 no-op，須補寫欄位並留 Log
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "修復雙面不同步",
         "--resources", ",".join(wide)]
    )
    assert rc == 0
    item = _gov_item(gov_card)
    assert item.text("資源宣告") == "db_scope=none；" + "、".join(wide)
    assert "資源宣告（Project 欄位補寫；body 已是目標值）" in item.body
    assert "file:docs/only-one-file.md" in item.body, "原值必須留在 Log"


def test_resources_true_no_op_is_still_rejected(gov_card):
    """兩個居所都已一致才是真 no-op——此時仍拒絕寫入不實留痕。"""
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "沒變", "--resources", "file:demo.py"]
    )
    assert rc == 2
    assert "amend by wf-cli" not in _gov_item(gov_card).body


def test_initiative_amend_writes_both_surfaces(gov_card):
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "掛到父卡", "--initiative", "ai-workflow#99"]
    )
    assert rc == 0
    item = _gov_item(gov_card)
    assert item.text("Initiative") == "ai-workflow#99"
    assert "- Initiative：ai-workflow#99　spec 基線：原基線" in item.body


def test_body_first_ordering_keeps_the_first_write_self_describing(gov_card, monkeypatch):
    """雙居所欄位的首寫必須是 body（攜帶 Log 行），不是 Project 欄位。

    級別走的是相反順序（欄位先寫），那已被判為首寫不自描述；本卡新增的欄位
    不得再製造第三個。這裡以呼叫序列證明，而非靠註解宣稱。
    """
    seq: list[str] = []
    real_set_field, real_set_body = amend_cmd.set_field_value, amend_cmd.set_item_body
    monkeypatch.setattr(amend_cmd, "set_field_value",
                        lambda *a, **k: (seq.append("field"), real_set_field(*a, **k))[1])
    monkeypatch.setattr(amend_cmd, "set_item_body",
                        lambda *a, **k: (seq.append("body"), real_set_body(*a, **k))[1])
    assert run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "收窄", "--resources", "file:x.py"]
    ) == 0
    assert seq[0] == "body", f"雙居所欄位的首寫必須自描述，實際序列 {seq}"
    assert "field" in seq


def test_amend_never_touches_project_field_definitions(gov_card):
    """⚠️ 本專案曾因 updateProjectV2Field（改欄位定義、重生選項 ID）清空 56 張卡狀態。

    所有欄位寫入必須走 item 值那條路；本測試釘住 amend 全程不呼叫 field-create，
    也不發出任何觸及欄位定義的 GraphQL。
    """
    before = len(gov_card.graphql_calls)
    assert run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "降級", "--tier", "T2",
         "--ruling-url", _ruling()]
    ) == 0
    assert run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "收窄", "--resources", "file:y.py"]
    ) == 0
    for query in gov_card.graphql_calls[before:]:
        assert "updateProjectV2Field" not in query
        assert "createProjectV2Field" not in query


def test_stale_field_after_body_write_reports_exit_7_with_recovery(gov_card, monkeypatch, capsys):
    """body 已寫、Project 欄位補寫讀回不符 → 退出碼 7，並指出重跑即收斂。

    這是 body-先寫順序的**代價**那一側。它不是「解法」，是被選中的失敗模式：
    可直接偵測（兩個居所的值可互比）且重跑同一條 amend 即收斂，不需要
    --record-unlogged-change 那種由操作者宣告的補救。
    """
    monkeypatch.setattr(amend_cmd, "set_field_value", lambda *a, **k: None)
    rc = run_cli(
        ["amend", *GOV_TARGET, "GOV-DEMO1", "--reason", "模擬欄位補寫失敗",
         "--resources", "file:z.py"]
    )
    assert rc == 7
    err = capsys.readouterr().err
    assert "body 已寫入" in err
    assert "重跑同一條 amend 即會收斂" in err
    # body 確實已寫（含 Log），欄位確實過期——這正是要能被偵測的狀態
    item = _gov_item(gov_card)
    assert parse_block(item.body).resources == ["file:z.py"]
    assert item.text("資源宣告") == "db_scope=none；file:demo.py"
    assert "→ 資源宣告：" in item.body, "首寫是 body 且自描述：Log 已記下這筆變更"


# --------------------------------------------------------------------------
# 路由行保留字元與讀寫往返（WF-CARD-FIELD-CORRECTION1，2026-08-12 追加驗收）
# --------------------------------------------------------------------------
#
# **為什麼這一段長在 test_amend.py 而不是 test_card.py：** 本卡的資源宣告圈的是
# ``card.py``／``amend_cmd.py``／``test_amend.py``／``open_cmd.py``（末者由需求方
# 2026-08-12 以 op f9df9cb6 追加），``test_card.py`` 不在其中。主題上這些測試更貼近
# test_card.py，但寫入集是硬界線，逸出要由需求方裁定而不是由執行者自行擴張，
# 故落在這裡並以本註解說明歸屬。
#
# 修的缺陷（WF-CLI-ROUTING-TIER1／#21 已 🏁完成、APPROVE 0 finding、已併入 main 之後
# 才被發現）：``open`` 寫得出的路由行，``assign`` 讀不回。已知的兩個真實形態——
#
#   形態一（名字）  ``- 執行：Claude Opus 5@Claude Code（子 agent）（建議 主力型；…）``
#   形態二（理由）  ``…（建議 主力型；…真實歸因（PM 的 checkpoint…不符），再判斷…）``
#                   ← #38 開卡當下中招：assign 落 ambiguous、要求偏離理由後才放行
#                     （不是被拒絕派工）；同批的 #39 理由無全形括號，assign 直接 matched
#
# 兩者根因相同、修法方向相反，而方向是**實測**決定的，不是照範本第 4 行的外觀推的：
# 名字段對四個結構字元全部失配（禁），理由段只對全形空格失配（其餘放行）。


def _routing_line(
    executor="待指派",
    exec_tier="主力型",
    exec_reason="理由甲",
    reviewer="獨立校讀",
    rev_tier="高階型",
    rev_reason="理由乙",
):
    """獨立於 ``format_routing_line`` 的第二份組裝器（往返測試不可自我對照）。"""
    return (
        f"- 執行：{executor}（建議 {exec_tier}；{exec_reason}）"
        f"　查核：{reviewer}（建議 {rev_tier}；{rev_reason}）"
    )


ROUTING_FIELD_NAMES = ("executor", "reviewer")
ROUTING_FIELD_REASONS = ("exec_reason", "rev_reason")
ROUTING_FIELD_TIERS = ("exec_tier", "rev_tier")

# 逐欄位的**宣告**保留字元；下方測試逐格比對「宣告」與「實測」是否一致。
_DECLARED = {
    **{f: ROUTING_NAME_RESERVED for f in ROUTING_FIELD_NAMES},
    **{f: ROUTING_REASON_RESERVED for f in ROUTING_FIELD_REASONS},
}

_MATRIX = [
    (field, ch)
    for field in (*ROUTING_FIELD_NAMES, *ROUTING_FIELD_REASONS)
    for ch in ROUTING_STRUCTURAL_CHARS
]


@pytest.mark.parametrize("field,ch", _MATRIX, ids=[f"{f}-{ord(c):04X}" for f, c in _MATRIX])
def test_declared_reserved_chars_match_measured_parser_sensitivity(field, ch):
    """(a) 保留字元清單必須逐欄位對上**實測**的解析敏感度，不得多禁也不得少禁。

    這是本輪最重要的一條，因為它把「格式規定得夠不夠清楚」從人的判斷換成機器：
    每個欄位 × 每個結構字元恰好落在兩格之一，沒有第三格——

      * 宣告為保留 → 讀取端必須**失配**（不把它當資料收）
      * 未宣告為保留 → 讀取端必須**往返成立**（讀回逐字相同的值）

    少禁會留下「寫得出、讀不回」（#21／#38 的缺陷）；多禁會擋掉合法卡面
    （理由是中文散文，全形括號與全形分號是常態，禁它們就是製造第二個缺陷）。
    """
    value = f"甲{ch}乙"
    match = _ROUTING_PARSE_RE.match(_routing_line(**{field: value}))
    if ch in _DECLARED[field]:
        assert match is None, (
            f"{field} 宣告 {ch!r} 為保留字元，讀取端卻仍收下它——寫入端會白擋"
        )
    else:
        assert match is not None, (
            f"{field} 未宣告 {ch!r} 為保留字元，讀取端卻失配——這正是 #38 的形態"
        )
        assert match.group(field) == value, (
            f"{field} 讀回 {match.group(field)!r} 與寫入的 {value!r} 不同（靜默錯讀）"
        )


def test_reserved_lists_are_pinned_to_the_measured_per_field_policy():
    """逐欄位清單的**內容**本身要有守門人，不只是「宣告與解析器一致」。

    上一條測的是一致性；但解析器的字元類與宣告同源，改宣告會讓兩者一起變，一致性
    因此擋不住「把清單改小／改大」。這條把 2026-08-12 實測＋需求方裁定的結論釘死：
    改動任一格都必須是**刻意**的，並且要重跑那次逐欄位實測。
    """
    assert ROUTING_NAME_RESERVED == ("（", "）", "；", "　"), "名字段四個結構字元全禁"
    assert ROUTING_REASON_RESERVED == ("　",), (
        "理由段只禁全形空格——全形括號與全形分號是中文散文的常態用法，"
        "禁它們會重現 #38 那條合法理由被判成不可解析的結果"
    )


@pytest.mark.parametrize("field", ROUTING_FIELD_TIERS)
def test_tier_fields_are_protected_by_closed_vocabulary_not_by_a_reserved_list(field):
    """層級段不設保留字元清單，其保護是封閉語彙——這條保證必須有機械執行者。

    實測中唯一會**靜默錯讀**的格子就在層級段：層級值若含全形分號，解析讀回的是被
    截斷的前半段而不是失配。因此「使用者不可能寫出這種值」不能只留在註解裡。
    """
    for tier in CAPABILITY_TIERS:
        for ch in ROUTING_STRUCTURAL_CHARS:
            assert ch not in tier, f"能力層級語彙 {tier!r} 含結構字元 {ch!r}"
        match = _ROUTING_PARSE_RE.match(_routing_line(**{field: tier}))
        assert match is not None and match.group(field) == tier


# --- (c) 讀寫往返：語料含真實使用過的值 --------------------------------------

# 三筆語料由需求方 2026-08-12 指名，全部取自真實開卡：
#   1. 名字形態（#37 的 owner 名，改寫為合規的半形括號）
#   2. 理由形態（#38 的 --exec-capability-reason 原文，全形括號原樣保留）
#   3. 兩者同時
PM_REAL_REASON = (
    "須先自行查證兩起來源事故的真實歸因（PM 的 checkpoint 記錄與可稽核留痕不符），"
    "再判斷正解落在範本層、CLI 層還是偵測層；推理鏈中等但要求不接受上游敘述。"
)
PM_REAL_NAME = "Claude Opus 5@Claude Code (子 agent)"

ROUND_TRIP_CORPUS = [
    ("純樸素值", {}),
    ("真實名字（#37 owner，半形括號）", {"executor": PM_REAL_NAME, "reviewer": PM_REAL_NAME}),
    ("真實理由含全形括號（#38 中招處）", {"exec_reason": PM_REAL_REASON}),
    (
        "名字與理由同時",
        {"executor": PM_REAL_NAME, "reviewer": PM_REAL_NAME, "exec_reason": PM_REAL_REASON},
    ),
    ("理由含全形分號（#35／#37 現行用法）", {"exec_reason": "紅線卡須跨模型家族；查核重點在授權綁定"}),
    ("理由以全形右括號結尾", {"exec_reason": "見 review-escalation.md §4 (a′)（需求方平台身分）"}),
]


@pytest.mark.parametrize(
    "label,overrides", ROUND_TRIP_CORPUS, ids=[c[0] for c in ROUND_TRIP_CORPUS]
)
def test_open_written_routing_line_is_readable_by_the_assign_side(
    fake_runner, label, overrides
):
    """(c) ``open`` 寫得出的路由行，``assign`` 的兩支消費者都必須讀得回。

    刻意走**完整指令**而不是直接呼叫 ``format_routing_line``：缺陷正是出在
    「寫入端與讀取端各自成立、合起來不成立」，只測純函式就會漏掉它。
    """
    card_id = f"ROUNDTRIP-{abs(hash(label)) % 10**6}"
    values = {
        "executor": "待指派",
        "reviewer": "獨立校讀",
        "exec_reason": "理由甲",
        "rev_reason": "理由乙",
        **overrides,
    }
    rc = run_cli(
        [
            "open", *BASE_TARGET, card_id,
            "--feature", "往返語料", "--tier", "T2", "--db-scope", "none",
            "--core-pain", "痛點", "--service-goal", "目標",
            "--executor", values["executor"], "--reviewer", values["reviewer"],
            "--exec-capability", "主力型", "--exec-capability-reason", values["exec_reason"],
            "--review-capability", "高階型", "--review-capability-reason", values["rev_reason"],
        ]
    )
    assert rc == 0, f"{label}：open 拒絕了一個它本該寫得出的值"

    project = resolve_project(fake_runner, "acme", 1)
    body = find_item_by_card_id(list_items(fake_runner, project), card_id).body

    # 消費者一：assign 的能力層級比對（實際唯一會被消費的欄位）
    comparison = compare_capability_to_card(body, "主力型")
    assert comparison.outcome == CAPABILITY_MATCHED, (
        f"{label}：assign 讀不回 open 剛寫下的建議（{comparison.detail}）"
    )
    assert comparison.requires_reason is False

    # 消費者二：解析器逐欄位的值保真（層級以外的欄位不被消費，但錯讀即是資料損壞）
    line = next(ln for ln in body.splitlines() if ln.startswith("- 執行："))
    match = _ROUTING_PARSE_RE.match(line)
    assert match is not None, label
    for field, expected in (
        ("executor", values["executor"]),
        ("reviewer", values["reviewer"]),
        ("exec_reason", values["exec_reason"]),
        ("rev_reason", values["rev_reason"]),
    ):
        assert match.group(field) == expected, f"{label}：{field} 讀回的值與寫入的不同"


def test_the_exact_line_that_broke_assign_on_card_38_now_matches():
    """#38 的實時重現：同一條路由行，修法前 ambiguous、修法後 matched。

    語料是 2026-08-12 從 ai-workflow#38 卡面取回的**原文**（未經改寫），對照組是
    同批開卡的 #39（理由無全形括號，當時即一次通過）——證明差異由值的內容決定，
    不是環境問題。
    """
    broke = _routing_line(exec_reason=PM_REAL_REASON)
    body = f"- 需求：ruan6047　規劃：PM\n{ROUTING_MARKER}\n{broke}\n\n## Log\n\n- x\n"
    assert compare_capability_to_card(body, "主力型").outcome == CAPABILITY_MATCHED

    # 舊解析器（理由段 [^）]+）在此語料上失配——這條把「修法前確實壞」寫成機械事實，
    # 免得後人以為這條測試從一開始就是綠的。
    old = re.compile(
        r"^- 執行：(?P<executor>[^（]*)（建議 (?P<exec_tier>[^；）]+)；(?P<exec_reason>[^）]+)）"
        r"　查核：(?P<reviewer>[^（]*)（建議 (?P<rev_tier>[^；）]+)；(?P<rev_reason>[^）]+)）$"
    )
    assert old.match(broke) is None, "語料選錯了：這條線在舊解析器上本來就通過"


# --- (b) 寫入端拒收 ---------------------------------------------------------


def _card_kwargs(**overrides):
    base = {
        "card_id": "RESERVED-DEMO1",
        "feature": "示範",
        "tier": "T2",
        "db_scope": "none",
        "core_pain": "痛點",
        "service_goal": "目標",
        "resources": ResourceDeclaration(db_scope="none", resources=[]),
        "executor_capability": "主力型",
        "executor_capability_reason": "理由甲",
        "reviewer_capability": "高階型",
        "reviewer_capability_reason": "理由乙",
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize("axis", ["executor", "reviewer"])
@pytest.mark.parametrize("ch", ROUTING_NAME_RESERVED, ids=[f"{ord(c):04X}" for c in ROUTING_NAME_RESERVED])
def test_card_refuses_to_hold_a_name_it_could_not_read_back(axis, ch):
    """(b) 寫入端不得靜默接受一個自己讀不回的名。

    擋在 ``Card`` 建構而不是只擋在 CLI：繞過 CLI 直接建 Card 的路徑同樣不該產出
    無法解析的路由行。訊息必須說明字元承擔什麼結構並給出替代寫法——被擋的人要的
    是「那我該怎麼寫」。
    """
    with pytest.raises(ValueError) as exc:
        Card(**_card_kwargs(**{axis: f"某人{ch}某工具"}))
    message = str(exc.value)
    assert "保留字元" in message
    assert repr(ch) in message
    assert "半形" in message


@pytest.mark.parametrize("axis", ["executor", "reviewer"])
def test_card_refuses_a_name_carrying_a_line_break(axis):
    """換行同屬「寫得出、讀不回」：它會在標頭區多長出一行，使候選路由行不唯一。"""
    with pytest.raises(ValueError, match="保留字元"):
        Card(**_card_kwargs(**{axis: "某人\n<!-- 偽造宣告 -->"}))


@pytest.mark.parametrize("axis", ["exec", "review"])
def test_open_rejects_fullwidth_space_in_reason_without_creating_the_card(
    fake_runner, capsys, axis
):
    """理由段唯一的保留字元是全形空格；拒絕形狀為退出碼 2、不建卡。

    理由段的拒收落在 ``validate_capability_routing``，名字段落在
    ``validate_routing_names``；``open_cmd`` 兩者都呼叫，且共用同一個
    ``except ValueError`` 出口，所以兩側的訊息前綴與退出碼**逐字相同**。
    名字側的對應測試見 ``test_open_rejects_a_reserved_char_name_with_exit_code_2_…``。
    """
    rc = run_cli(
        [
            "open", *BASE_TARGET, f"RESERVED-REASON-{axis}",
            "--feature", "示範", "--tier", "T2", "--db-scope", "none",
            "--core-pain", "痛點", "--service-goal", "目標",
            "--exec-capability", "主力型",
            "--exec-capability-reason", "理由甲　含全形空格" if axis == "exec" else "理由甲",
            "--review-capability", "高階型",
            "--review-capability-reason", "理由乙　含全形空格" if axis == "review" else "理由乙",
        ]
    )
    assert rc == 2
    assert "保留字元" in capsys.readouterr().err
    project = resolve_project(fake_runner, "acme", 1)
    assert find_item_by_card_id(list_items(fake_runner, project), f"RESERVED-REASON-{axis}") is None


def _reserved_name_argv(card_id="RESERVED-NAME1"):
    return [
        "open", *BASE_TARGET, card_id,
        "--feature", "示範", "--tier", "T2", "--db-scope", "none",
        "--core-pain", "痛點", "--service-goal", "目標",
        "--executor", "Claude Opus 5@Claude Code（子 agent）",
        "--exec-capability", "主力型", "--exec-capability-reason", "理由甲",
        "--review-capability", "高階型", "--review-capability-reason", "理由乙",
    ]


def test_open_refuses_an_unreadable_name_before_touching_github(fake_runner, monkeypatch):
    """名字側的拒收 fail-closed：全程沒有任何 GitHub 寫入呼叫，不留半寫狀態。

    這條釘的是**深層性質**，與訊息品質（退出碼與前綴，見下一條）是兩件事，所以
    ``open_cmd`` 補上前置檢查之後仍然保留、也不被下一條取代。第二段刻意**停用**
    那道前置檢查，證明即使它被拿掉，``Card.__post_init__`` 仍是防線——而 Card
    建構早於任何 GitHub 呼叫，這正是「拒收不留半寫狀態」的機制來源。
    """
    before = len(fake_runner.graphql_calls)
    assert run_cli(_reserved_name_argv()) == 2
    assert len(fake_runner.graphql_calls) == before, "CLI 前置檢查那條路徑不得有任何寫入呼叫"

    monkeypatch.setattr(open_cmd, "validate_routing_names", lambda **kw: None)
    with pytest.raises(ValueError, match="保留字元"):
        run_cli(_reserved_name_argv("RESERVED-NAME1-BYPASS"))
    assert len(fake_runner.graphql_calls) == before, (
        "前置檢查被停用時，model 層防線同樣必須早於任何寫入呼叫"
    )


def test_open_rejects_a_reserved_char_name_with_exit_code_2_and_no_traceback(
    fake_runner, capsys
):
    """名字側的拒收必須與理由側同一種形狀：``[open] 拒絕：…`` ＋ 退出碼 2。

    **以 stack trace 收場的 fail-closed 不算乾淨拒絕**——本卡存在的理由正是建立
    乾淨的寫入端拒收。``cli.py`` 的 ``KNOWN_ERRORS`` 不收 ``ValueError``，所以
    只靠 ``Card.__post_init__`` 那條防線會吐 traceback；乾淨的那一半由
    ``open_cmd`` 的前置檢查提供。
    """
    try:
        rc = run_cli(_reserved_name_argv("RESERVED-NAME-CLEAN1"))
    except ValueError as exc:  # pragma: no cover - 只在缺前置檢查時走到
        pytest.fail(f"名字未被乾淨拒絕，以 ValueError 收場（CLI 會呈現為 traceback）：{exc}")
    assert rc == 2
    err = capsys.readouterr().err
    assert err.startswith("[open] 拒絕："), f"訊息前綴須與理由側一致，實際：{err[:40]!r}"
    assert "保留字元" in err
    assert "Traceback" not in err
    project = resolve_project(fake_runner, "acme", 1)
    assert find_item_by_card_id(list_items(fake_runner, project), "RESERVED-NAME-CLEAN1") is None


# --- 驗證：既有 18 張永久 absent 卡的既成狀態不得被改變 -----------------------

# 2026-08-12 以 ``gh issue view`` 逐張取回 ai-workflow#7–#25 的卡面第 4 行原文
# （#14 是 PR 不是卡片，故 18 張）。
#
# **R4-002 是帶條件的選言，不是禁令。** 引用裁決時不得強化其約束力——這條形態出自
# #11（WF-24-EVIDENCE-STRENGTH1）驗收 (d)，該卡 2026-08-12 仍 🚧進行中，故此處是
# 引用其形態而非援引一條已上線的 canonical 條款。
# 原文（2026-08-12 以 ``gh issue view 21 --comments`` 逐字核對）：
#
#     「需求方須明定並留痕：既有卡永久以 absent 派工，**或**提供具四項路由值、
#      原值 Log 與審核界線的遷移路徑；先完成選擇及測試再合併。」
#
# 需求方選了**第一支**（既有卡永久以 absent 派工）。第二支（遷移路徑）**並未被禁止**，
# 但要付三個條件：四項路由值、原值 Log、審核界線，且須先完成選擇及測試才可合併。
# 本卡的修法建立在「第一支已被選中」這個既成狀態上，故不得使那 18 張改變判定——
# 這與「遷移入口不得存在」是兩回事，本註解先前把後者寫成了裁定內容。
#
# **這份語料的邊界要說清楚**：釘住的是 18 條**真實路由行**放進標準舊卡 body 的判定，
# 不是 18 份真實 body 的逐位元組重放。真實 body 另有一張（#15）因其 ``## Log``
# 排版本就損壞而落 ambiguous——那是 #21 當時就記錄在案的既有狀態，與本卡無關。
REAL_LEGACY_ROUTING_LINES = [
    (7, "- 執行：待指派　查核：待指派"),
    (8, "- 執行：待指派　查核：待指派"),
    (9, "- 執行：待指派　查核：待指派"),
    (10, "- 執行：待指派　查核：待指派"),
    (11, "- 執行：待指派　查核：待指派"),
    (12, "- 執行：待指派　查核：待指派"),
    (13, "- 執行：待指派　查核：待指派"),
    (15, "- 執行：待指派　查核：獨立校讀"),
    (16, "- 執行：待指派（先 grilling）　查核：跨家族架構查核"),
    (17, "- 執行：待指派　查核：獨立校讀"),
    (18, "- 執行：待指派　查核：獨立校讀"),
    (19, "- 執行：待指派　查核：獨立校讀"),
    (20, "- 執行：待指派　查核：獨立校讀"),
    (21, "- 執行：待指派　查核：獨立校讀"),
    (22, "- 執行：待指派　查核：跨家族查核（契約本體，依 AI_WORKFLOW.md B2 例外須走 PR）"),
    (23, "- 執行：待指派　查核：跨家族查核（契約本體，須走 PR）"),
    (24, "- 執行：待指派　查核：跨家族查核（契約本體，須走 PR）"),
    (25, "- 執行：待指派　查核：跨家族查核（T4 紅線：不可逆且會毀資料，須人工 sign-off）"),
]


def test_the_legacy_corpus_really_is_the_eighteen_cards():
    assert len(REAL_LEGACY_ROUTING_LINES) == 18


@pytest.mark.parametrize(
    "issue,line", REAL_LEGACY_ROUTING_LINES, ids=[f"#{n}" for n, _ in REAL_LEGACY_ROUTING_LINES]
)
def test_legacy_cards_stay_absent_after_the_round_trip_fix(issue, line):
    """R4-002 被選中那一支的既成狀態：這 18 張以 absent 派工，不得變成 ambiguous 或 matched。"""
    body = f"- 需求：ruan6047　規劃：PM\n{line}\n\n## Log\n\n- x\n"
    c = compare_capability_to_card(body, "主力型")
    assert c.outcome == CAPABILITY_BASELINE_ABSENT, f"#{issue} 的既成狀態被改變了"
    assert "卡面無建議層級" in c.log_fragment("舊卡無基線")


@pytest.mark.parametrize("ch", ROUTING_STRUCTURAL_CHARS, ids=[f"{ord(c):04X}" for c in ROUTING_STRUCTURAL_CHARS])
def test_absent_verdict_does_not_depend_on_routing_line_content_at_all(ch):
    """比逐張釘住更強的一條：未宣告標記的卡面，判定與路由行內容**無關**。

    absent 在到達解析器之前就決定了（標記不在標頭區即 absent），所以任何對保留字元
    或字元類的調整都在結構上碰不到那 18 張卡。這條把「碰不到」從論證變成測試。
    """
    line = _routing_line(executor=f"某人{ch}某工具", exec_reason=f"理由{ch}甲")
    body = f"- 需求：ruan6047　規劃：PM\n{line}\n\n## Log\n\n- x\n"
    assert compare_capability_to_card(body, "主力型").outcome == CAPABILITY_BASELINE_ABSENT


def test_already_written_fullwidth_paren_names_stay_ambiguous_never_matched():
    """#35／#37 那種**已經寫進卡面**的全形括號名，仍是 ambiguous（fail-closed）。

    寫入端拒收只防新的；已寫下的不會被本卡追溯修好，也不得被悄悄放行成 matched
    ——那會讓一個從未被解析成功的建議冒充成「比對過且相符」。
    """
    line = _routing_line(executor="Claude Opus 5@Claude Code（子 agent）")
    body = f"- 需求：ruan6047　規劃：PM\n{ROUTING_MARKER}\n{line}\n\n## Log\n\n- x\n"
    c = compare_capability_to_card(body, "主力型")
    assert c.outcome == CAPABILITY_BASELINE_AMBIGUOUS
    assert c.requires_reason is True


def test_comparison_never_mutates_the_body_it_reads():
    """既有的 deviation 記錄不得因本卡的修法失效或被追溯改寫。

    ``compare_capability_to_card`` 是純讀取：它不回寫 body，也不碰 Log。已寫下的
    「無基線／偏離」理由留在 Log 裡原樣不動——本測試釘住「讀取不改寫」這一半。
    """
    line = _routing_line(exec_reason=PM_REAL_REASON)
    log = "- 2026-08-12T10:00:00+08:00 assign by wf-cli → 實際能力層級 主力型（卡面建議無法解析：…；理由：…）。"
    body = f"- 需求：ruan6047　規劃：PM\n{ROUTING_MARKER}\n{line}\n\n## Log\n\n{log}\n"
    before = body
    compare_capability_to_card(body, "主力型")
    assert body == before
    assert log in body


def test_format_routing_line_and_the_parser_agree_on_every_accepted_value():
    """渲染端與解析端的最後一道對齊：``format_routing_line`` 的輸出必須解析得回。

    ``_routing_line`` 是測試自備的第二份組裝器，本條則以**產品碼的渲染器**再驗一次，
    確保上面那些往返結論不是只對測試自己的組裝器成立。
    """
    card = Card(
        **_card_kwargs(
            executor=PM_REAL_NAME,
            reviewer="跨家族查核 (待需求方指派)",
            executor_capability_reason=PM_REAL_REASON,
        )
    )
    rendered = format_routing_line(card).splitlines()[-1]
    match = _ROUTING_PARSE_RE.match(rendered)
    assert match is not None
    assert match.group("executor") == PM_REAL_NAME
    assert match.group("exec_reason") == PM_REAL_REASON
    assert match.group("exec_tier") == "主力型"
