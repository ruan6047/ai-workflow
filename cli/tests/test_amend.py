"""WF-CLI-CARD-AMEND1：卡面修訂的純函式與 `wfcli amend` 指令。

分兩層：純函式層不碰網路，直接對 body 字串斷言（含 Log 不被動、勾選狀態保留、
拒絕不實留痕）；指令層用 FakeGhRunner 驗證呼叫序列與 Log 內容。
"""

from __future__ import annotations

import hashlib

import pytest

from wf_cli.card import (
    AmendError,
    amend_acceptance,
    amend_resource_block,
    amend_spec_baseline,
    amend_verification,
    repair_body_layout,
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


def test_repair_replaces_only_the_corrupted_token():
    body = "- 需求：x\\n## Log\\n\\n- 條目"
    repaired, original = repair_body_layout(body)
    assert original == body
    assert repaired == "- 需求：x\n\n## Log\n\n- 條目"
    split_at_log(repaired)


def test_repair_leaves_legitimate_literal_newline_in_log_untouched():
    """R3-01 破口一：#17 自己的 Log 敘述就含合法的字面 \\n（那行在描述『把字面 \\n 還原』）。"""
    body = (
        "- 需求：x\\n## Log\\n\\n"
        "- 2026-08-10 repair；將誤寫的字面 \\n 還原為真換行。"
    )
    repaired, _ = repair_body_layout(body)
    assert "字面 \\n 還原為真換行" in repaired, "Log 內文的合法字面 \\n 不得被改動"
    assert repaired.count("\\n") == 1


def test_repair_refuses_marker_inside_fenced_code_block():
    """R3-01 破口二：圍籬內的 \\n## Log 是內容不是標題，修復會在程式碼中生出標題。"""
    body = (
        "- 需求：x\n\n```text\n"
        "示範損壞：\\n## Log\\n\\n- 條目\n"
        "```\n\n## Log\n\n- 真正的條目"
    )
    with pytest.raises(AmendError, match="fenced code block"):
        repair_body_layout(body)


def test_repair_refuses_multiple_markers():
    body = "a\\n## Log\\n\\nb\\n## Log\\n\\nc"
    with pytest.raises(AmendError, match="出現 2 次"):
        repair_body_layout(body)


def test_repair_preserves_json_and_all_other_bytes():
    body = (
        "- 需求：x\n\n## 資源宣告\n"
        "<!-- resource-claims:begin -->\n"
        '```json\n{"db_scope": "none", "resources": ["file:a.py"], "note": "a\\nb"}\n```\n'
        "<!-- resource-claims:end -->"
        "\\n## Log\\n\\n- 條目"
    )
    repaired, original = repair_body_layout(body)
    idx = body.index("\\n## Log\\n\\n")
    assert repaired[:idx] == body[:idx], "損壞標記之前必須逐位元不變"
    assert repaired[idx + len("\n\n## Log\n\n"):] == body[idx + len("\\n## Log\\n\\n"):], \
        "損壞標記之後也必須逐位元不變"
    assert '"note": "a\\nb"' in repaired, "JSON 字串內的合法字面 \\n 不得被改動"
    assert parse_block(repaired).resources == parse_block(original).resources


def test_repair_round_trips_issue17_shaped_body():
    """完整 round-trip：對還原後的 body 再製造同一種損壞，修復必須回到原樣。"""
    good = (
        "- 需求：x\n- Initiative：—　spec 基線：base\n\n## 驗證\n\n- [ ] v\n\n"
        "## Log\n\n- 2026-08-10 open。\n- 2026-08-10 repair；把字面 \\n 還原。\n"
    )
    corrupted = good.replace("\n\n## Log\n\n", "\\n## Log\\n\\n", 1)
    repaired, _ = repair_body_layout(corrupted)
    assert repaired == good


def test_repair_command_requires_expected_hash(card):
    rc = run_cli(["amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "修排版", "--repair-log-layout"])
    assert rc == 2


def test_repair_command_rejects_combination_with_other_flags(card):
    rc = run_cli(
        [
            "amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "混用",
            "--repair-log-layout", "--expect-body-sha256", "0" * 64,
            "--spec-baseline", "順便改",
        ]
    )
    assert rc == 2


def test_repair_command_rejects_hash_mismatch(card):
    rc = run_cli(
        [
            "amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "修排版",
            "--repair-log-layout", "--expect-body-sha256", "0" * 64,
        ]
    )
    assert rc == 2


def test_repair_command_fixes_corrupted_log(card):
    """重放 ai-workflow#17 的實際事故：Log 標題被寫成字面 \\n。"""
    project = resolve_project(card, "acme", 1)
    item = _item(card)
    corrupted = item.body.replace("\n\n## Log\n\n", "\\n## Log\\n\\n", 1)
    set_item_body(card, item.content_type, item.content_id, project, None, item.issue_number, corrupted)
    digest = hashlib.sha256(corrupted.encode("utf-8")).hexdigest()

    rc = run_cli(
        [
            "amend", *BASE_TARGET, "AMEND-DEMO1", "--reason", "還原被寫成字面 \\n 的 Log 標題",
            "--repair-log-layout", "--expect-body-sha256", digest,
        ]
    )
    assert rc == 0
    fixed = _item(card).body
    assert "\\n## Log" not in fixed
    assert "amend by wf-cli" in fixed
    assert f"原 body SHA-256 {digest}" in fixed, "修復必須留下原 body 雜湊供還原"
    split_at_log(fixed)  # 修完必須能安全定位


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
# R2-01：修復範圍必須縮到 Log 區段，不得破壞 JSON 等非空白內容
# --------------------------------------------------------------------------


def _body_with_json_literal_newline() -> str:
    """資源宣告 JSON 內含合法的字面 \\n（JSON 字串跳脫），Log 區段則是壞掉的。"""
    return (
        "- 需求：x\n\n## 資源宣告\n"
        "<!-- resource-claims:begin -->\n"
        '```json\n{"db_scope": "none", "resources": ["file:a.py"], "note": "a\\nb"}\n```\n'
        "<!-- resource-claims:end -->"
        "\\n## Log\\n\\n- 條目"
    )


def test_repair_keeps_json_literal_newline_intact():
    """R2 的反例在新做法下應該通過而非拒絕：定點替換根本不碰 JSON 裡的字面 \\n。"""
    body = _body_with_json_literal_newline()
    repaired, original = repair_body_layout(body)
    assert '"note": "a\\nb"' in repaired, "JSON 字串內的合法字面 \\n 必須原封不動"
    assert parse_block(repaired).resources == parse_block(original).resources
    split_at_log(repaired)


def test_repair_leaves_pre_log_content_byte_identical():
    body = (
        "- 需求：x\n\n## 資源宣告\n"
        "<!-- resource-claims:begin -->\n"
        '```json\n{"db_scope": "none", "resources": ["file:a.py"]}\n```\n'
        "<!-- resource-claims:end -->"
        "\\n## Log\\n\\n- 條目"
    )
    repaired, original = repair_body_layout(body)
    head = body[: body.find("\\n## Log")]
    assert repaired.startswith(head), "Log 之前的內容必須逐位元不變"
    assert parse_block(repaired).resources == parse_block(original).resources


def test_repair_refuses_body_without_literal_log_marker():
    with pytest.raises(AmendError, match="找不到"):
        repair_body_layout("- 需求：x\\n 這裡有字面 n 但沒有 Log 標記")


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
# 執行者自我對抗測試：fence 偵測的盲點（R3 修法後自查發現）
#
# `body.count("```")` 只看得見反引號圍籬。`~~~` 圍籬、縮排式程式碼區塊、行內碼
# 裡的同一個 token 它都看不見；當 body 剛好沒有真正的 Log 標題時，「兩個 ## Log」
# 那道下游檢查也攔不住，修復就會在內容中間生出一個標題。
#
# 靠列舉 Markdown 語境補不完，因此改為兩道與語境無關的檢查：
#   1. token 所在行在它之前必須有非空白（真實事故中它緊接內容文字）。
#   2. 修復後的 Log 區段只能有標題、空行與 `- ` 條目。
# --------------------------------------------------------------------------

_TOK = "\\n## Log\\n\\n"


@pytest.mark.parametrize(
    "name,body",
    [
        ("tilde-fence-no-real-log", "a\n\n~~~text\n" + _TOK + "- 範例條目\n~~~\n"),
        ("four-space-indent", "a\n\n    " + _TOK + "- 範例\n"),
        ("tab-indent", "a\n\n\t" + _TOK + "- 範例\n"),
        ("inline-code-mention", "a\n\n- 文件說明：`" + _TOK + "` 是損壞形態\n"),
        ("backtick-fence", "a\n\n```text\n" + _TOK + "\n```\n\n## Log\n\n- 真"),
    ],
)
def test_repair_refuses_token_in_content_context(name, body):
    with pytest.raises(AmendError):
        repair_body_layout(body)


def test_repair_accepts_token_at_body_start():
    """token 位於 body 最開頭時沒有前綴可檢查，屬合法形態。"""
    repaired, _ = repair_body_layout(_TOK + "- 條目")
    assert repaired == "\n\n## Log\n\n- 條目"


def test_repair_result_log_section_contains_only_entries():
    """結構不變量：修復後 Log 區段只能有標題、空行與 `- ` 條目。"""
    body = "- 需求：x" + _TOK + "- 條目一\n- 條目二\n"
    repaired, _ = repair_body_layout(body)
    tail = split_at_log(repaired)[1].splitlines()
    assert tail[0].strip() == "## Log"
    assert all(not ln.strip() or ln.startswith("- ") for ln in tail[1:])
