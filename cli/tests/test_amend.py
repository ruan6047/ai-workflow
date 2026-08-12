"""WF-CLI-CARD-AMEND1：卡面修訂的純函式與 `wfcli amend` 指令。

分兩層：純函式層不碰網路，直接對 body 字串斷言（含 Log 不被動、勾選狀態保留、
拒絕不實留痕）；指令層用 FakeGhRunner 驗證呼叫序列與 Log 內容。
"""

from __future__ import annotations

import json

import pytest

from wf_cli.card import (
    REQUESTER_GATED_TIERS,
    AmendError,
    RequesterUnparseable,
    amend_acceptance,
    amend_core_pain,
    amend_initiative,
    amend_resource_block,
    amend_spec_baseline,
    amend_verification,
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
    assert "GitHub comment author 已逐字核對" in body


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
