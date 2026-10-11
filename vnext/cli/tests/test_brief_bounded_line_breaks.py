"""brief 預設輸出的上限在「單筆資料內含換行」時仍成立。

上限由列數保證（test_brief_bounded.py）；前提是首屏「一列＝一個非空行」。單筆值——Project 欄位值、
`.wf/` 政策檔名、留言 url、相連卡回應的 state 與 issue_url、啟用模組名、任務識別——可以合法地含換行，
預設輸出把首屏每列與任務來源標記 escape 成恰一個實體行（`\\n`、`\\u2028`…），⛔ 不丟字元、⛔ 不截斷、
⛔ 不拒收來源資料、⛔ 不以 rc≠0 擋。原樣值只在 `--full`，`--full` 逐字不變。
全部走注入式快照與 tmp root，零網路、零 mutation。
"""

import json

import pytest

from wfx.core.render import split_output

from .conftest import TASK_ID
from .fakes import BODY, FakeLinkedClients, snapshot
from .test_brief import ROLES, STAGES
from .test_brief_bounded import LIMIT, extreme_body, extreme_comments, extreme_linked_clients, nonempty

BREAKS = 80
MULTILINE = "\n".join(f"資源{i}" for i in range(BREAKS + 1))      # 81 行的單一欄位值
NEWLINE_NAME = "p" + "\nx" * BREAKS + ".md"                        # 含 80 個換行的合法檔名
LINKED = "https://github.com/o/r/issues/1001"
LINKED_COMMENT = f"{LINKED}#issuecomment-1"


def with_resource(value):
    s = snapshot()
    s["items"][0]["fieldValues"]["Resource"] = {"text": value}
    return s


def linked_body():
    return f"{BODY}\n## 相連任務\n\n- {LINKED} {LINKED_COMMENT}\n"


def linked_clients(*, state="OPEN", comment_issue_url="https://api.github.com/repos/o/r/issues/1001"):
    issue = {"id": "I_1001", "number": 1001, "url": LINKED, "state": state,
             "updatedAt": "2026-10-12T00:00:00Z", "body": "## 需求\n\n需求原文\n"}
    comment = {"body": "## 規劃\n規劃原文\n", "html_url": LINKED_COMMENT, "issue_url": comment_issue_url}
    return FakeLinkedClients(issues={("o/r", 1001): issue}, comments={1: comment})


def enable_module(rules_root, project_root, name):
    directory = rules_root / "modules" / name
    directory.mkdir(parents=True)
    for stage in STAGES:
        (directory / f"{stage}.md").write_text(f"# m\n\n## 1 · 核對\n\n在{stage}。\n", encoding="utf-8")
    config_path = project_root / ".wf" / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["modules"] = [name]
    config_path.write_text(json.dumps(config), encoding="utf-8")


# 審核重現的兩例：政策檔名含 80 個換行、`Resource` 為 81 行文字——預設輸出仍 ≤ 上限，且與普通資料同列數
def test_policy_file_name_with_line_breaks_stays_one_row(run_cli, project_root):
    rc, plain, _ = run_cli(role="PM", full=False)
    (project_root / ".wf" / "model-policy.md").rename(project_root / ".wf" / NEWLINE_NAME)
    rc_odd, out, err = run_cli(role="PM", full=False)
    assert (rc, rc_odd, err) == (0, 0, "")
    assert len(nonempty(out)) == len(nonempty(plain)) <= LIMIT
    assert "- .wf/p" + "\\nx" * BREAKS + ".md（" in out


def test_multiline_core_concept_value_stays_one_row(run_cli):
    _, plain, _ = run_cli(role="PM", full=False, snapshots=[with_resource("單行")])
    rc, out, err = run_cli(role="PM", full=False, snapshots=[with_resource(MULTILINE)])
    assert (rc, err) == (0, "")
    assert len(nonempty(out)) == len(nonempty(plain)) <= LIMIT
    assert "Resource: " + MULTILINE.replace("\n", "\\n") + "\n" in out


# 同根因的其他插入點：每一種單筆值都在首屏佔恰一列（含換行與否，非空行數相同）
CASES = {
    "留言 url": dict(
        snapshots=lambda v: [snapshot(comments=({"url": f"https://example.invalid/c1{v}", "body": "x\n"},))]),
    "相連卡 state": dict(
        snapshots=lambda v: [snapshot(body=linked_body())],
        linked_clients=lambda v: linked_clients(state=f"OPEN{v}")),
    "相連卡回應的 issue_url": dict(
        snapshots=lambda v: [snapshot(body=linked_body())],
        linked_clients=lambda v: linked_clients(comment_issue_url=f"https://example.invalid/x{v}")),
    "任務識別前後的換行": dict(task=lambda v: "\n" * len(v) + TASK_ID + "\n" * len(v)),
    "Unicode 行分隔符": dict(snapshots=lambda v: [with_resource(v.replace("\n", " ") + "尾")]),
}


@pytest.mark.parametrize("case", sorted(CASES))
def test_line_breaks_inside_any_single_value_do_not_add_lines(run_cli, case):
    spec = CASES[case]

    def run(value):
        kwargs = {key: make(value) for key, make in spec.items()}
        kwargs.setdefault("snapshots", [snapshot()])
        return run_cli(role="執行者", full=False, **kwargs)

    _, plain, _ = run("")
    rc, out, err = run("\nx" * BREAKS)
    assert (rc, err) == (0, "")
    assert len(nonempty(out)) == len(nonempty(plain)) <= LIMIT, case


def test_module_name_with_line_breaks_stays_one_row(run_cli, rules_root, project_root):
    enable_module(rules_root, project_root, "m-plain")
    _, plain, _ = run_cli(full=False)
    (project_root / ".wf" / "config.json").write_text(json.dumps(
        {"project": {"owner": "o", "number": 9}, "modules": ["m" + "\nx" * BREAKS]}), encoding="utf-8")
    (rules_root / "modules" / "m-plain").rename(rules_root / "modules" / ("m" + "\nx" * BREAKS))
    rc, out, err = run_cli(full=False)
    assert (rc, err) == (0, "")
    assert len(nonempty(out)) == len(nonempty(plain)) <= LIMIT


# 極端筆數＋每一種含換行的單筆值同時出現：6 角色 × 5 階段的預設輸出都 ≤ 上限
@pytest.fixture
def extreme_with_line_breaks(rules_root, project_root, user_root):
    for i in range(1, 31):
        (project_root / ".wf" / f"policy-{i:02d}{chr(10) * 3}x{i}.md").write_text(
            f"# 政策 {i}\n\n## 1 · 甲\n\n內文\n", encoding="utf-8")
    (project_root / ".wf" / "model-policy.md").rename(project_root / ".wf" / NEWLINE_NAME)
    enable_module(rules_root, project_root, "m" + "\nx" * BREAKS)
    comments = tuple({"url": c["url"] + "\nx" * 5, "body": c["body"]} for c in extreme_comments())
    s = snapshot(body=extreme_body(), comments=comments)
    s["items"][0]["fieldValues"]["Resource"] = {"text": MULTILINE}
    s["items"][0]["fieldValues"]["owner"] = {"text": MULTILINE}
    linked = extreme_linked_clients()
    for key in linked.issues:
        linked.issues[key]["state"] = "OPEN" + "\nx" * 5
    for comment in linked.comments.values():
        comment["issue_url"] = "https://example.invalid/x" + "\nx" * 5

    def run(run_cli, role, stage, *, full):
        return run_cli(role=role, stage=stage, full=full, task=f"\n\n{TASK_ID}\n\n",
                       snapshots=[s], linked_clients=linked)

    return run


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("role", ROLES)
def test_default_output_stays_within_the_limit_with_line_breaks_everywhere(
        run_cli, extreme_with_line_breaks, role, stage):
    rc, out, err = extreme_with_line_breaks(run_cli, role, stage, full=False)
    assert (rc, err) == (0, "")
    assert len(nonempty(out)) <= LIMIT, len(nonempty(out))


# `--full` 原樣：含換行的值逐字出現在首屏與附錄，⛔ 不 escape
def test_full_output_keeps_line_breaking_values_verbatim(run_cli, project_root):
    (project_root / ".wf" / "model-policy.md").rename(project_root / ".wf" / NEWLINE_NAME)
    rc, out, err = run_cli(full=True, snapshots=[with_resource(MULTILINE)])
    assert (rc, err) == (0, "")
    first, appendix = split_output(out)
    assert f"Resource: {MULTILINE}\n" in first and f"Resource: {MULTILINE}\n" in appendix
    assert f"- .wf/{NEWLINE_NAME}（" in first and f"[來源: project:.wf/{NEWLINE_NAME}#全文]" in appendix
    assert "\\nx" not in out and "\\n資源" not in out
