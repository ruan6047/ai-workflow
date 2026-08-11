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
