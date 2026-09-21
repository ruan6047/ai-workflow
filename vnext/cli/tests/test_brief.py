"""W1.6 驗收：brief 的四層注入、必要清單與模型資料載入。

驗收編號對應 VNEXT-PLAN-2026-09-21.md 的 E 表 W1.6 (1)–(10)。
"""

import re

import pytest

from conftest import STAGE_COMMENT, TASK_ID
from wfx.core.errors import LayerMissing, MalformedInput, ValueNotInDomain
from wfx.core.layers import KINDS, UNKNOWN_MODEL_DATA

MARKER = re.compile(r"^\[來源: (?P<kind>[a-z]+):(?P<path>[^#]+)#(?P<section>.+)\]$")
ROLES = ("需求方", "PM", "研究者", "規劃者", "執行者", "審核者")
STAGES = ("需求", "規劃", "執行", "審核", "結案")


# brief 自己的結構行；載入的規則與 Issue body 也用 `## `，因此只認這五個標題。
TOP_LEVEL = ("適用規則", "必要清單", "使用者層", "專案層", "任務層")


def section(out, title):
    lines = out.splitlines()
    start = lines.index(f"## {title}") + 1
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## ") and lines[index][3:] in TOP_LEVEL:
            end = index
            break
    return "\n".join(lines[start:end])


def markers(out):
    return [MARKER.match(line) for line in out.splitlines() if line.startswith("[來源: ")]


# (1) 全部輸入不變時逐字穩定
def test_same_inputs_produce_byte_identical_output(run_cli, snapshot):
    path = snapshot()
    first = run_cli(snapshot_path=path)
    second = run_cli(snapshot_path=path)
    assert first == second
    assert first[0] == 0


# (2) 六個角色各產生不同必要清單
def test_each_role_gets_its_own_required_checklist(run_cli, snapshot):
    path = snapshot()
    lists = {}
    for role in ROLES:
        rc, out, _ = run_cli(role=role, snapshot_path=path)
        assert rc == 0
        checklist = section(out, "必要清單")
        assert f"framework:roles/{role}.md#章節" in checklist
        lists[role] = checklist
    assert len(set(lists.values())) == len(ROLES)


def test_each_stage_loads_its_own_stage_document(run_cli, snapshot):
    path = snapshot()
    for stage in STAGES:
        rc, out, _ = run_cli(stage=stage, snapshot_path=path)
        assert rc == 0
        assert f"framework:stages/{stage}.md#章節" in section(out, "必要清單")


# (3) 每段帶來源標記，且 kind 恰在四層內
def test_every_segment_is_marked_with_one_of_the_four_kinds(run_cli, snapshot):
    rc, out, _ = run_cli(snapshot_path=snapshot())
    assert rc == 0
    found = markers(out)
    assert found and all(m is not None for m in found)
    kinds = {m.group("kind") for m in found}
    assert kinds <= set(KINDS)
    assert kinds == set(KINDS)


# (4) --rules-root 指向另一個 checkout 時輸出隨之改變
def test_rules_root_selects_which_checkout_is_loaded(run_cli, snapshot, tmp_path, rules_root):
    import shutil

    other = tmp_path / "other-checkout" / "rules"
    shutil.copytree(rules_root, other)
    doc = other / "roles" / "執行者.md"
    doc.write_text(doc.read_text(encoding="utf-8") + "\n## 7 · 另一個 checkout 才有的節\n內文\n", encoding="utf-8")

    path = snapshot()
    _, baseline, _ = run_cli(snapshot_path=path)
    _, changed, _ = run_cli("--rules-root", str(other), snapshot_path=path)
    assert changed != baseline
    assert "7 · 另一個 checkout 才有的節" in changed


# (5) 缺任一必要層＝typed 失敗，⛔ 不靜默略過
def test_missing_task_layer_is_a_typed_failure(run_cli):
    rc, out, err = run_cli()
    assert rc == 2
    assert out == ""
    assert "缺少必要層 task" in err


def test_missing_project_layer_is_a_typed_failure(run_cli, snapshot, project_root):
    (project_root / ".wf" / "model-policy.md").unlink()
    rc, _, err = run_cli(snapshot_path=snapshot())
    assert rc == 2
    assert "缺少必要層 project" in err


def test_missing_framework_document_is_a_typed_failure(run_cli, snapshot, rules_root):
    (rules_root / "roles" / "執行者.md").unlink()
    rc, _, err = run_cli(snapshot_path=snapshot())
    assert rc == 2
    assert "缺少必要層 framework" in err
    assert "roles/執行者.md" in err


def test_missing_layers_raise_typed_errors(rules_root, project_root, tmp_path):
    from wfx.core import layers

    with pytest.raises(LayerMissing) as missing:
        layers.project_layer(tmp_path / "nowhere")
    assert missing.value.kind == "project"

    with pytest.raises(LayerMissing) as missing:
        layers.task_layer(None, TASK_ID)
    assert missing.value.kind == "task"


# (6) 兩類模型資料原樣呈現，含其來源與最後確認時間
def test_user_model_files_are_reproduced_verbatim(run_cli, snapshot, user_root):
    usage = "# 模型使用說明\n家族 A 適合長脈絡。\n來源：需求方；最後確認時間：2026-09-21\n"
    availability = "# 可用性備註\n家族 B：額度受限。\n來源：主控台；最後確認時間：2026-09-20\n"
    user_root.mkdir(parents=True)
    (user_root / "model-usage.md").write_text(usage, encoding="utf-8")
    (user_root / "model-availability.md").write_text(availability, encoding="utf-8")

    rc, out, _ = run_cli(snapshot_path=snapshot())
    assert rc == 0
    block = section(out, "使用者層")
    assert usage.strip("\n") in block
    assert availability.strip("\n") in block
    assert "[來源: user:~/.wf/model-usage.md#全文]" in block
    assert "[來源: user:~/.wf/model-availability.md#全文]" in block
    assert UNKNOWN_MODEL_DATA not in block


# (7) 兩檔皆不存在時 unknown 且照常完成；單檔缺同樣是 unknown
def test_absent_user_model_files_are_unknown_and_do_not_block(run_cli, snapshot, user_root):
    assert not user_root.exists()
    rc, out, err = run_cli(snapshot_path=snapshot())
    assert rc == 0
    assert err == ""
    assert section(out, "使用者層").count(UNKNOWN_MODEL_DATA) == 2


def test_one_absent_user_model_file_is_unknown(run_cli, snapshot, user_root):
    user_root.mkdir(parents=True)
    (user_root / "model-usage.md").write_text("# 模型使用說明\n家族 A。\n", encoding="utf-8")
    rc, out, _ = run_cli(snapshot_path=snapshot())
    assert rc == 0
    block = section(out, "使用者層")
    assert "[來源: user:~/.wf/model-availability.md#缺]" in block
    assert block.count(UNKNOWN_MODEL_DATA) == 1


# (8) 第 4 層含已貼出的階段完成留言，原樣納入且⛔ 不解析
def test_task_layer_carries_issue_body_fields_and_comments_verbatim(run_cli, snapshot):
    rc, out, _ = run_cli(snapshot_path=snapshot())
    assert rc == 0
    block = section(out, "任務層")
    assert STAGE_COMMENT.strip("\n") in block
    assert f"[來源: task:{TASK_ID}#comment-1]" in block
    assert f"[來源: task:{TASK_ID}#issue-body]" in block
    assert "## 裁定紀錄" in block
    for line in ("狀態: 進行中", "階段: 執行", "owner: ruan", "期限: ", "Resource: "):
        assert line in block


def test_multiple_stage_comments_keep_snapshot_order(run_cli, snapshot):
    path = snapshot(comments=[{"body": "第一則"}, {"body": "第二則"}])
    rc, out, _ = run_cli(snapshot_path=path)
    assert rc == 0
    block = section(out, "任務層")
    assert block.index("第一則") < block.index("第二則")
    assert "#comment-2]" in block


# (9) 待辦與進行中兩種輸入都能正常呈現
@pytest.mark.parametrize("status", ["待辦", "進行中"])
def test_both_status_inputs_render(run_cli, snapshot, status):
    fields = {"狀態": status, "階段": "執行", "owner": "ruan", "風險": "重要",
              "緊急性": "一般", "期限": "", "Resource": ""}
    rc, out, _ = run_cli(snapshot_path=snapshot(fields=fields))
    assert rc == 0
    assert f"狀態: {status}" in section(out, "任務層")


# (10) 零網路：brief 只碰檔案系統
def test_brief_succeeds_with_all_sockets_blocked(run_cli, snapshot, monkeypatch):
    import socket

    def blocked(*args, **kwargs):
        raise AssertionError("brief ⛔ 不得連線")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    rc, out, _ = run_cli(snapshot_path=snapshot())
    assert rc == 0
    assert out.startswith("# brief\n")


# 值域：角色與階段的唯一居所是 values.md，訊息只談值域
def test_role_outside_the_domain_is_rejected(run_cli, snapshot):
    rc, _, err = run_cli(role="owner", snapshot_path=snapshot())
    assert rc == 2
    assert "不在值域內" in err


def test_domain_comes_from_values_md_not_from_code(rules_root):
    from wfx.core import values

    doc = rules_root / "core" / "values.md"
    doc.write_text(
        doc.read_text(encoding="utf-8").replace(
            "| 角色（6） | 需求方／PM／研究者／規劃者／執行者／審核者 |",
            "| 角色（6） | 需求方／PM |",
        ),
        encoding="utf-8",
    )
    assert values.domain(rules_root, "角色") == ("需求方", "PM")
    with pytest.raises(ValueNotInDomain):
        values.check(rules_root, "角色", "執行者")


# 形狀檢查：⛔ 不判內容，但格式壞掉要說出來
def test_snapshot_task_id_must_match_the_flag(run_cli, snapshot):
    rc, _, err = run_cli(snapshot_path=snapshot(task="other/repo#1"))
    assert rc == 2
    assert "不符" in err


def test_eighth_core_concept_is_rejected(run_cli, snapshot):
    fields = {"狀態": "待辦", "級別": "T1"}
    rc, _, err = run_cli(snapshot_path=snapshot(fields=fields))
    assert rc == 2
    assert "級別" in err


def test_broken_snapshot_json_is_a_typed_failure(run_cli, snapshot, tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    rc, _, err = run_cli(snapshot_path=path)
    assert rc == 2
    assert "合法 JSON" in err


def test_malformed_input_is_typed(tmp_path):
    from wfx.core import layers

    path = tmp_path / "s.json"
    path.write_text('{"task": "a#1", "issue_body": "x", "fields": []}', encoding="utf-8")
    with pytest.raises(MalformedInput):
        layers.task_layer(path, "a#1")


def test_empty_issue_body_is_a_missing_task_layer(tmp_path):
    from wfx.core import layers

    path = tmp_path / "s.json"
    path.write_text('{"task": "a#1", "issue_body": "  "}', encoding="utf-8")
    with pytest.raises(LayerMissing) as missing:
        layers.task_layer(path, "a#1")
    assert missing.value.kind == "task"
