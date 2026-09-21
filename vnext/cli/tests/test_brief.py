"""W1.6 驗收：brief 的四層注入、必要清單與模型資料載入。

驗收編號對應 VNEXT-PLAN-2026-09-21.md 的 E 表 W1.6 (1)–(10)。
第 4 層走與 `facts` 同一條唯讀 `wfx.gh`；本檔全部以注入式快照驗，零網路、零 mutation。
"""

import json
import re

import pytest

from wfx.core.errors import LayerMissing, MalformedInput, ValueNotInDomain
from wfx.core.layers import CORE_CONCEPTS, KINDS, UNKNOWN_MODEL_DATA
from wfx.gh.client import NotFound
from wfx.gh.task import UNKNOWN_CONCEPT, TaskData

from .conftest import TASK_ID
from .fakes import COMMENTS, FIELD_NAMES, FakeClient, FixedTaskSource, snapshot

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


# (1) 全部輸入不變時逐字穩定（同一份遠端讀取快照）
def test_same_inputs_produce_byte_identical_output(run_cli):
    client = FakeClient(snapshot())
    first = run_cli(client=client)
    second = run_cli(client=client)
    assert first == second
    assert first[0] == 0


# (2) 六個角色各產生不同必要清單
def test_each_role_gets_its_own_required_checklist(run_cli):
    lists = {}
    for role in ROLES:
        rc, out, _ = run_cli(role=role)
        assert rc == 0
        checklist = section(out, "必要清單")
        assert f"framework:roles/{role}.md#章節" in checklist
        lists[role] = checklist
    assert len(set(lists.values())) == len(ROLES)


def test_each_stage_loads_its_own_stage_document(run_cli):
    for stage in STAGES:
        rc, out, _ = run_cli(stage=stage)
        assert rc == 0
        assert f"framework:stages/{stage}.md#章節" in section(out, "必要清單")


# (3) 每段帶來源標記，且 kind 恰在四層內
def test_every_segment_is_marked_with_one_of_the_four_kinds(run_cli):
    rc, out, _ = run_cli()
    assert rc == 0
    found = markers(out)
    assert found and all(m is not None for m in found)
    assert {m.group("kind") for m in found} == set(KINDS)


# (4) --rules-root 指向另一個 checkout 時輸出隨之改變
def test_rules_root_selects_which_checkout_is_loaded(run_cli, tmp_path, rules_root):
    import shutil

    other = tmp_path / "other-checkout" / "rules"
    shutil.copytree(rules_root, other)
    doc = other / "roles" / "執行者.md"
    doc.write_text(doc.read_text(encoding="utf-8") + "\n## 7 · 另一個 checkout 才有的節\n內文\n",
                   encoding="utf-8")

    client = FakeClient(snapshot())
    _, baseline, _ = run_cli(client=client)
    _, changed, _ = run_cli("--rules-root", str(other), client=client)
    assert changed != baseline
    assert "7 · 另一個 checkout 才有的節" in changed


# (5) 缺任一必要層＝typed 失敗（rc=1），⛔ 不靜默略過
def test_missing_project_layer_is_a_typed_failure(run_cli, project_root):
    (project_root / ".wf" / "model-policy.md").unlink()
    rc, out, err = run_cli()
    assert (rc, out) == (1, "")
    assert "缺少必要層 project" in err


def test_missing_framework_document_is_a_typed_failure(run_cli, rules_root):
    (rules_root / "roles" / "執行者.md").unlink()
    rc, _, err = run_cli()
    assert rc == 1
    assert "缺少必要層 framework" in err and "roles/執行者.md" in err


def test_empty_issue_body_is_a_missing_task_layer(run_cli):
    rc, out, err = run_cli(snapshots=[snapshot(body="   ")])
    assert (rc, out) == (1, "")
    assert "缺少必要層 task" in err


def test_unreadable_task_layer_fails_loud_and_is_not_an_empty_brief(run_cli):
    class Missing(FakeClient):
        def issue(self, number):
            raise NotFound("issue #370 不存在於 o/r")

    rc, out, err = run_cli(client=Missing())
    assert (rc, out) == (1, "")
    assert "NotFound" in err


def test_missing_layers_raise_typed_errors(tmp_path):
    from wfx.core import layers

    with pytest.raises(LayerMissing) as missing:
        layers.project_layer(tmp_path / "nowhere")
    assert missing.value.kind == "project"

    with pytest.raises(LayerMissing) as missing:
        layers.task_layer(TaskData(TASK_ID, "  ", {c: "" for c in CORE_CONCEPTS}, ()))
    assert missing.value.kind == "task"


def test_task_layer_shape_errors_are_typed(tmp_path):
    from wfx.core import layers

    with pytest.raises(MalformedInput, match="缺核心概念"):
        layers.task_layer(TaskData(TASK_ID, "body", {"狀態": "待辦"}, ()))
    with pytest.raises(MalformedInput, match="必須是 object"):
        layers.task_layer(TaskData(TASK_ID, "body", [], ()))


# (6) 兩類模型資料原樣呈現，含其來源與最後確認時間
def test_user_model_files_are_reproduced_verbatim(run_cli, user_root):
    usage = "# 模型使用說明\n家族 A 適合長脈絡。\n來源：需求方；最後確認時間：2026-09-21\n"
    availability = "# 可用性備註\n家族 B：額度受限。\n來源：主控台；最後確認時間：2026-09-20\n"
    user_root.mkdir(parents=True)
    (user_root / "model-usage.md").write_text(usage, encoding="utf-8")
    (user_root / "model-availability.md").write_text(availability, encoding="utf-8")

    rc, out, _ = run_cli()
    assert rc == 0
    block = section(out, "使用者層")
    assert usage.strip("\n") in block
    assert availability.strip("\n") in block
    assert "[來源: user:~/.wf/model-usage.md#全文]" in block
    assert "[來源: user:~/.wf/model-availability.md#全文]" in block
    assert UNKNOWN_MODEL_DATA not in block


# (7) 兩檔皆不存在時 unknown 且照常完成；單檔缺同樣是 unknown
def test_absent_user_model_files_are_unknown_and_do_not_block(run_cli, user_root):
    assert not user_root.exists()
    rc, out, err = run_cli()
    assert (rc, err) == (0, "")
    assert section(out, "使用者層").count(UNKNOWN_MODEL_DATA) == 2


def test_one_absent_user_model_file_is_unknown(run_cli, user_root):
    user_root.mkdir(parents=True)
    (user_root / "model-usage.md").write_text("# 模型使用說明\n家族 A。\n", encoding="utf-8")
    rc, out, _ = run_cli()
    assert rc == 0
    block = section(out, "使用者層")
    assert "[來源: user:~/.wf/model-availability.md#缺]" in block
    assert block.count(UNKNOWN_MODEL_DATA) == 1


# (8) 第 4 層含已貼出的留言，原樣納入且⛔ 不解析、⛔ 不分類
def test_task_layer_carries_issue_body_fields_and_comments_verbatim(run_cli):
    rc, out, _ = run_cli()
    assert rc == 0
    block = section(out, "任務層")
    assert f"[來源: task:{TASK_ID}#issue-body]" in block
    assert "## 裁定紀錄" in block
    for line in ("狀態: 進行中", "階段: 執行", "owner: ruan6047", "期限: 2026-09-30", "Resource: "):
        assert line in block


def test_every_comment_is_carried_verbatim_and_never_classified(run_cli):
    """該卡**全部**留言原樣納入；⛔ 不篩「哪些算階段完成留言」——四類是內容分類，CLI 判不得。"""
    rc, out, _ = run_cli()
    assert rc == 0
    block = section(out, "任務層")
    for index, comment in enumerate(COMMENTS, start=1):
        assert f"[來源: task:{TASK_ID}#comment-{index}]" in block
        assert f"url: {comment['url']}" in block
        assert comment["body"].strip("\n") in block
    assert block.index(COMMENTS[0]["body"].strip("\n")) < block.index(COMMENTS[1]["body"].strip("\n"))


# (9) 待辦與進行中兩種輸入都能正常呈現
@pytest.mark.parametrize("status", ["待辦", "進行中"])
def test_both_status_inputs_render(run_cli, status):
    rc, out, _ = run_cli(snapshots=[snapshot(status=status)])
    assert rc == 0
    assert f"狀態: {status}" in section(out, "任務層")


# (10) 零網路呼叫至模型 provider：注入 TaskSource＋阻斷 socket 與 subprocess
def test_brief_succeeds_with_the_provider_path_blocked(run_cli, monkeypatch):
    import socket
    import subprocess

    def blocked(*args, **kwargs):
        raise AssertionError("brief ⛔ 不得連線或起子行程")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(subprocess, "run", blocked)
    rc, out, _ = run_cli(task_source=FixedTaskSource(TASK_ID, comments=[("", "一則留言")]))
    assert rc == 0
    assert out.startswith("# brief\n")
    assert "一則留言" in section(out, "任務層")


# Project 未設定／該卡尚⛔ 無 item：七概念印 unknown，rc=0（⛔ 不 typed fail）
def test_project_not_configured_renders_seven_unknown_concepts(run_cli, tmp_path):
    root = tmp_path / "no-project"
    (root / ".wf").mkdir(parents=True)
    (root / ".wf" / "model-policy.md").write_text("# 專案層政策\n", encoding="utf-8")
    (root / ".wf" / "config.json").write_text(json.dumps({"project": None}), encoding="utf-8")
    rc, out, _ = run_cli(project=root)
    assert rc == 0
    block = section(out, "任務層")
    assert block.count(UNKNOWN_CONCEPT) == len(CORE_CONCEPTS)


def test_card_without_a_project_item_renders_seven_unknown_concepts(run_cli):
    rc, out, _ = run_cli(snapshots=[snapshot(item=False)])
    assert rc == 0
    assert section(out, "任務層").count(UNKNOWN_CONCEPT) == len(CORE_CONCEPTS)


# 第八個平台欄位：原樣忽略、只呈現七概念、rc=0（⛔ 不當成新增核心概念而拒收整份 brief）
def test_extra_platform_field_is_ignored_and_never_rejected(run_cli):
    rc, out, err = run_cli(snapshots=[snapshot(field_names=FIELD_NAMES + ("級別",))])
    assert (rc, err) == (0, "")
    block = section(out, "任務層")
    assert "級別" not in block and "T1" not in block
    concepts = section(out, "任務層").split("#核心概念]\n", 1)[1]
    assert [line.split(":")[0] for line in concepts.splitlines() if line.strip()][:7] == list(CORE_CONCEPTS)


# 值域：角色與階段的唯一居所是 values.md，訊息只談值域
def test_role_outside_the_domain_is_rejected(run_cli):
    rc, _, err = run_cli(role="owner")
    assert rc == 1
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


# 公開契約：brief 恰三個必填旗標＋--rules-root，⛔ 無 --task-snapshot
def test_public_flags_are_exactly_the_contract(run_cli):
    from wfx.verbs.brief import parse_args

    args = parse_args(["--task", TASK_ID, "--role", "執行者", "--stage", "執行"])
    assert vars(args) == {"task": TASK_ID, "role": "執行者", "stage": "執行", "rules_root": None}
    with pytest.raises(SystemExit) as exit_code:      # 用法錯＝rc=2，與 typed 錯（rc=1）可區分
        parse_args(["--task", TASK_ID, "--role", "執行者", "--stage", "執行",
                    "--task-snapshot", "x.json"])
    assert exit_code.value.code == 2
