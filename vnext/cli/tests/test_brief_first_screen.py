"""#370 裁定（comment 5763204699）：brief ＝派工首屏＋同一輸出後方的完整原文附錄。

被驗的是**呈現**：首屏只放機械定位資料、附錄逐字保留四層原文且同一來源只出現一次。
⛔ 無行數 gate——行數是報告裡的量測，不是通過條件。
"""

import re

import pytest

from wfx.core.layers import CORE_CONCEPTS, UNKNOWN_MODEL_DATA, USER_MODEL_FILES
from wfx.core.render import APPENDIX_HEADING, FIRST_SCREEN_HEADING, split_output
from wfx.core.rules import issue_section_titles

from .conftest import TASK_ID
from .fakes import COMMENTS, FakeClient, snapshot
from .test_brief import ROLES, TOP_LEVEL, markers, section

MARKER_LINE = re.compile(r"^\[來源: .+\]$")


def parts(out):
    return split_output(out)


def marked_blocks(text):
    """把附錄切成 [(來源標記, 逐字內文)]；結構標題（##／###）＝段落結束。"""
    lines = text.splitlines()
    out, index = [], 0
    while index < len(lines):
        if not MARKER_LINE.match(lines[index]):
            index += 1
            continue
        marker, index, buf = lines[index], index + 1, []
        while index < len(lines):
            line = lines[index]
            head = line.split(" ", 1)
            if MARKER_LINE.match(line) or (head[0] in ("##", "###") and len(head) == 2
                                           and head[1] in TOP_LEVEL):
                break
            buf.append(line)
            index += 1
        out.append((marker, "\n".join(buf).strip("\n")))
    return out


# 首屏在附錄之前，邊界是一行常數＝可機械定位
def test_first_screen_precedes_the_appendix_and_the_boundary_is_mechanical(run_cli):
    rc, out, _ = run_cli()
    assert rc == 0
    assert out.startswith("# brief\n")
    assert out.index(FIRST_SCREEN_HEADING) < out.index(APPENDIX_HEADING)
    first, appendix = parts(out)
    assert first + appendix == out                    # 切開後零遺漏、零重疊
    assert appendix.startswith(APPENDIX_HEADING)
    assert APPENDIX_HEADING not in first
    assert out.count(APPENDIX_HEADING) == 1


# 首屏⛔ 不含任一原文正文（七核心概念的欄位值是既有投影、⛔ 不是原文，故排除）
def test_first_screen_reproduces_no_source_body(run_cli, user_root):
    user_root.mkdir(parents=True)
    (user_root / "model-usage.md").write_text("# 使用說明\n家族 A 的長脈絡備註。\n", encoding="utf-8")
    rc, out, _ = run_cli()
    assert rc == 0
    first, appendix = parts(out)
    # 排除兩種⛔ 非原文的段：七概念投影，與缺檔時 CLI 自己的 unknown 標記
    bodies = [body for marker, body in marked_blocks(appendix)
              if body and "#核心概念]" not in marker and body != UNKNOWN_MODEL_DATA]
    assert bodies
    leaked = [body.splitlines()[0] for body in bodies if body in first]
    assert leaked == []


# 首屏帶齊定位資訊：身分、七概念值、五章節、每則留言、模型資料、專案政策、core 路徑與節錨
def test_first_screen_locates_every_source(run_cli, rules_root):
    rc, out, _ = run_cli()
    assert rc == 0
    first, _ = parts(out)
    for line in (f"task: {TASK_ID}", "role: 執行者", "stage: 執行"):
        assert line in first
    for concept in CORE_CONCEPTS:
        assert f"\n{concept}: " in first
    for title in issue_section_titles(rules_root):
        assert f"- {title}：" in first
    for index, comment in enumerate(COMMENTS, start=1):
        assert f"- comment-{index}｜{comment['url']}｜" in first
    for name in USER_MODEL_FILES:
        assert f"- ~/.wf/{name}：" in first
    assert "- .wf/model-policy.md（" in first
    for rel in ("core/boundaries.md", "core/flow.md", "core/github.md",
                "core/independence.md", "core/research.md", "core/values.md"):
        assert f"- {rel}（" in first
    assert "1 · 分層注入（四層）" in first                   # core 節錨逐項在首屏
    assert "[來源: framework:roles/執行者.md#章節]" in first  # 角色必要清單的來源節錨
    assert "[來源: framework:stages/執行.md#章節]" in first   # 階段必要清單的來源節錨


# 附錄保留每一個原來源，且同一來源只出現一次
def test_appendix_keeps_every_source_exactly_once(run_cli, user_root):
    user_root.mkdir(parents=True)
    for name in USER_MODEL_FILES:
        (user_root / name).write_text(f"# {name}\n備註一行。\n", encoding="utf-8")
    rc, out, _ = run_cli()
    assert rc == 0
    _, appendix = parts(out)
    found = [marker for marker, _ in marked_blocks(appendix)]
    assert len(found) == len(set(found))
    expected = {
        f"[來源: user:~/.wf/{USER_MODEL_FILES[0]}#全文]",
        f"[來源: user:~/.wf/{USER_MODEL_FILES[1]}#全文]",
        "[來源: project:.wf/model-policy.md#全文]",
        f"[來源: task:{TASK_ID}#issue-body]",
        f"[來源: task:{TASK_ID}#核心概念]",
        "[來源: framework:core/github.md#1 · Issue body 五章節]",
        "[來源: framework:roles/執行者.md#前言]",
        "[來源: framework:stages/執行.md#前言]",
    } | {f"[來源: task:{TASK_ID}#comment-{i}]" for i in range(1, len(COMMENTS) + 1)}
    assert expected <= set(found)
    # 首屏的索引段⛔ 不重複出現在附錄
    for index_marker in (f"[來源: task:{TASK_ID}#留言索引]", "[來源: framework:rules/core/#節索引]",
                         "[來源: project:.wf/#節索引]", "[來源: user:~/.wf/#狀態]"):
        assert index_marker not in appendix


def test_every_comment_body_is_verbatim_in_the_appendix(run_cli):
    rc, out, _ = run_cli()
    assert rc == 0
    _, appendix = parts(out)
    for index, comment in enumerate(COMMENTS, start=1):
        assert f"[來源: task:{TASK_ID}#comment-{index}]" in appendix
        body = comment["body"].strip("\n")
        assert appendix.count(body) == 1


def test_project_policy_and_framework_rules_survive_in_full(run_cli, project_root, rules_root):
    rc, out, _ = run_cli()
    assert rc == 0
    _, appendix = parts(out)
    policy = (project_root / ".wf" / "model-policy.md").read_text(encoding="utf-8")
    assert policy.strip("\n") in appendix
    boundaries = (rules_root / "core" / "boundaries.md").read_text(encoding="utf-8")
    assert boundaries.splitlines()[-1].strip() in appendix


# 逐字穩定：同一份快照跑兩次，首屏與附錄都完全相同
def test_first_screen_is_byte_identical_for_identical_inputs(run_cli):
    client = FakeClient(snapshot())
    _, first_run, _ = run_cli(client=client)
    _, second_run, _ = run_cli(client=client)
    assert parts(first_run) == parts(second_run)


# 六個角色的必要清單在首屏仍兩兩互異
def test_six_roles_still_get_distinct_checklists_inside_the_first_screen(run_cli):
    seen = {}
    for role in ROLES:
        rc, out, _ = run_cli(role=role)
        assert rc == 0
        first, _ = parts(out)
        checklist = section(out, "必要清單")
        assert checklist in first
        seen[role] = checklist
    assert len(set(seen.values())) == len(ROLES)


# 五章節標題的居所是規則樹，⛔ 不是程式碼
def test_issue_section_titles_come_from_the_rules_tree(run_cli, rules_root):
    doc = rules_root / "core" / "github.md"
    doc.write_text(doc.read_text(encoding="utf-8").replace("`## 驗收`", "`## 驗收條件`"),
                   encoding="utf-8")
    assert "驗收條件" in issue_section_titles(rules_root)
    rc, out, _ = run_cli()
    assert rc == 0
    first, _ = parts(out)
    assert "- 驗收條件：⛔ 標題不在 body" in first


# 缺章節與多出來的章節都照實呈現，⛔ 不改寫、⛔ 不判合不合法
def test_missing_and_extra_issue_sections_are_reported_as_found(run_cli):
    body = "## 需求\n\n一行\n\n## 驗收\n\n## 自訂章節\n\n內容\n"
    rc, out, _ = run_cli(snapshots=[snapshot(body=body)])
    assert rc == 0
    first, _ = parts(out)
    assert "- 需求：在（第 1 行，1 非空行）" in first
    assert "- 驗收：標題在第 5 行、其下空" in first
    assert "- 限制與非目標：⛔ 標題不在 body" in first
    assert "- （五章節以外）自訂章節：第 7 行" in first


# ⛔ 無截斷、⛔ 無行數 gate：留言變多時首屏照長、rc 仍是 0
def test_many_comments_neither_truncate_nor_fail(run_cli):
    many = tuple({"url": f"https://example.invalid/c{i}", "body": f"## 第 {i} 則\n內文 {i}\n"}
                 for i in range(1, 41))
    rc, out, err = run_cli(snapshots=[snapshot(comments=many)])
    assert (rc, err) == (0, "")
    first, appendix = parts(out)
    assert first.count("｜https://example.invalid/c") == 40
    for i in range(1, 41):
        assert f"內文 {i}\n" in appendix


@pytest.mark.parametrize("role", ROLES)
def test_boundary_exists_for_every_role(run_cli, role):
    rc, out, _ = run_cli(role=role)
    assert rc == 0
    assert out.count(APPENDIX_HEADING) == 1 and out.count(FIRST_SCREEN_HEADING) == 1


# 同名章節重複出現：取最先那個，其餘照列在「五章節以外」，⛔ 不改寫、⛔ 不去重原文
def test_duplicate_issue_section_headings_are_reported_not_collapsed(run_cli):
    body = "## 需求\n\n第一份\n\n## 限制與非目標\n\n一行\n\n## 需求\n\n第二份\n"
    rc, out, _ = run_cli(snapshots=[snapshot(body=body)])
    assert rc == 0
    first, appendix = parts(out)
    assert "- 需求：在（第 1 行，1 非空行）" in first
    assert "- （同名重複）需求：第 9 行" in first
    assert "第一份" in appendix and "第二份" in appendix     # 原文兩份都在
