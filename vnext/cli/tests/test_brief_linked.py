"""#414：PM 登記的相連卡，其邊界與已核定規劃只帶入規劃者與執行者的 brief。

登記格式、帶入角色與帶入章節的居所＝`rules/core/github.md` §1「選用章節：相連任務登記」。
本檔全部以注入式替身驗：本卡走 `FakeClient`，相連卡走**另一個** `FakeLinkedClients` 工廠，零網路。
"""

import difflib
import json

import pytest

from wfx.core.render import split_output
from wfx.gh.client import GhClient, PermissionDenied

from .fakes import BODY, FakeClient, FakeLinkedClients, FixedTaskSource, RecordedRunner, snapshot
from .test_brief import ROLES, TOP_LEVEL, markers, section

CARRIED = ("規劃者", "執行者")
NOT_CARRIED = tuple(role for role in ROLES if role not in CARRIED)
STAGE_OF = {"規劃者": "規劃", "執行者": "執行", "研究者": "需求", "審核者": "審核",
            "需求方": "需求", "PM": "需求"}

URL5 = "https://github.com/o/r/issues/5"
URL6 = "https://github.com/o/r/issues/6"
COMMENT5 = f"{URL5}#issuecomment-55"
COMMENT6 = f"{URL6}#issuecomment-66"


def card_body(tag, *, linked=""):
    sections = {"需求": f"{tag} 需求原文：主要成果是 {tag}。", "限制與非目標": f"{tag} 限制原文。",
                "驗收": f"{tag} 驗收原文⛔ 不帶。", "風險與假設": f"{tag} 風險原文⛔ 不帶。",
                "裁定紀錄": f"{tag} 裁定原文⛔ 不帶。"}
    body = "\n".join(f"## {name}\n\n{text}\n" for name, text in sections.items())
    return body + (f"\n## 相連任務\n\n{linked}\n" if linked else "")


def issue(number, body, state="OPEN"):
    return {"id": f"I_{number}", "number": number, "url": f"https://github.com/o/r/issues/{number}",
            "state": state, "body": body, "updatedAt": "2026-10-08T00:00:00Z"}


def plan_comment(number, tag):
    return {"body": f"## 規劃階段完成卡 {tag}\n\n{tag} 規劃原文第一行\n{tag} 規劃原文第二行\n",
            "html_url": f"https://github.com/o/r/issues/{number}#issuecomment-{number}{number}",
            "issue_url": f"https://api.github.com/repos/o/r/issues/{number}"}


# 相連卡 5 自己也登記了本卡（互相登記）與第三張卡 7：⛔ 不得遞迴讀到它們
LINKED5 = card_body("L5", linked="- https://github.com/o/r/issues/370\n- https://github.com/o/r/issues/7")
LINKED6 = card_body("L6")


def linked_clients():
    return FakeLinkedClients(
        issues={("o/r", 5): issue(5, LINKED5), ("o/r", 6): issue(6, LINKED6, state="CLOSED"),
                ("o/r", 7): issue(7, card_body("L7")), ("o/r", 370): issue(370, card_body("SELF"))},
        comments={55: plan_comment(5, "L5"), 66: plan_comment(6, "L6")})


def registered(*lines):
    return BODY + "\n## 相連任務\n\n" + "\n".join(lines) + "\n"


ONE = registered(f"- {URL5} {COMMENT5}")


def run_linked(run_cli, body, role, *, clients=None, **kwargs):
    clients = linked_clients() if clients is None else clients
    rc, out, err = run_cli(role=role, stage=STAGE_OF[role], snapshots=[snapshot(body=body)],
                           linked_clients=clients, **kwargs)
    return rc, out, err, clients


def headings(out):
    return [line for line in out.splitlines()
            if line.split(" ", 1)[0] in ("##", "###") and line.split(" ", 1)[-1] in TOP_LEVEL]


# T1／T2：規劃者、執行者帶入相連卡兩章節原文與登記的規劃留言全文
@pytest.mark.parametrize("role", CARRIED)
def test_carried_roles_get_linked_boundaries_and_approved_plan(run_cli, role):
    rc, out, err, clients = run_linked(run_cli, ONE, role)
    assert (rc, err) == (0, "")
    first, appendix = split_output(out)
    index = section(out, "相連任務定位")
    assert index in first
    assert index.splitlines() == [
        "[來源: task:o/r#370#相連任務定位]",
        f"- 1｜{URL5}｜OPEN｜需求：在（第 1 行，1 非空行）｜限制與非目標：在（第 5 行，1 非空行）"
        f"｜已核定規劃：{COMMENT5}（3 非空行）",
    ]
    block = section(out, "相連任務原文")
    assert block in appendix
    assert f"[來源: task:{URL5}#需求]\nL5 需求原文：主要成果是 L5。" in block
    assert f"[來源: task:{URL5}#限制與非目標]\nL5 限制原文。" in block
    assert f"[來源: task:{URL5}#已核定規劃]\nurl: {COMMENT5}\n" + plan_comment(5, "L5")["body"].strip("\n") in block
    for absent in ("L5 驗收原文", "L5 風險原文", "L5 裁定原文", "issues/7", "SELF"):
        assert absent not in out                    # 只帶指定章節，⛔ 不帶其他章節與它的相連任務
    for raw in ("L5 需求原文", "L5 限制原文", "L5 規劃原文"):
        assert raw not in first                     # 首屏只有機械資料
    assert clients.calls == [("issue", "o/r", 5), ("issue_comment", "o/r", 55)]
    assert {m.group("kind") for m in markers(out)} <= {"framework", "user", "project", "task"}


# T3：未登記（無章節）⇒ 與 0.2.3 同形：零相連讀取、⛔ 無兩個新區塊
@pytest.mark.parametrize("role", CARRIED)
def test_unregistered_card_brings_nothing(run_cli, role):
    rc, out, err, clients = run_linked(run_cli, BODY, role)
    assert (rc, err) == (0, "")
    assert clients.created == [] and clients.calls == []
    assert "相連任務定位" not in out and "相連任務原文" not in out
    assert headings(out) == [
        "## 派工首屏", "### 核心概念現值", "### 必要清單", "### Issue body 章節定位", "### 留言定位索引",
        "### 模型資料狀態", "### 專案政策來源", "### 適用 core 規則定位",
        "## 完整原文附錄", "### 適用規則", "### 使用者層", "### 專案層", "### 任務層",
    ]


def test_registration_section_without_lines_reads_nothing(run_cli):
    rc, out, _, clients = run_linked(run_cli, BODY + "\n## 相連任務\n\n", "執行者")
    assert rc == 0 and clients.calls == []
    assert section(out, "相連任務定位").splitlines()[1] == "（章節在，其下⛔ 無登記行）"
    assert "### 相連任務原文" not in out


# T4：多筆依登記順序帶入；互相登記與相連卡的相連卡⛔ 不遞迴
def test_multiple_registrations_keep_order_and_never_recurse(run_cli):
    body = registered(f"- {URL6} {COMMENT6}", f"- {URL5} {COMMENT5}")
    rc, out, _, clients = run_linked(run_cli, body, "執行者")
    assert rc == 0
    index = section(out, "相連任務定位").splitlines()[1:]
    assert index[0].startswith(f"- 1｜{URL6}｜CLOSED｜") and index[1].startswith(f"- 2｜{URL5}｜OPEN｜")
    block = section(out, "相連任務原文")
    assert block.index("L6 需求原文") < block.index("L6 規劃原文第一行") < block.index("L5 需求原文")
    assert [call for call in clients.calls if call[0] == "issue"] == [("issue", "o/r", 6), ("issue", "o/r", 5)]
    assert "SELF" not in out and "L7" not in out


# T5：研究者、審核者、需求方、PM：本卡有登記也零相連讀取、⛔ 無相連區塊與原文
@pytest.mark.parametrize("role", NOT_CARRIED)
def test_other_roles_never_read_linked_cards(run_cli, role):
    rc, out, err, clients = run_linked(run_cli, ONE, role)
    assert (rc, err) == (0, "")
    assert clients.created == [] and clients.calls == []
    assert "相連任務定位" not in out and "相連任務原文" not in out
    for raw in ("L5 需求原文", "L5 限制原文", "L5 規劃原文", f"task:{URL5}"):
        assert raw not in out


# T6：同四角色：有／無登記章節的輸出差異只在本卡 body 原文與章節定位行
@pytest.mark.parametrize("role", NOT_CARRIED)
def test_other_roles_differ_only_by_this_cards_own_body(run_cli, role):
    _, without, _, _ = run_linked(run_cli, BODY, role)
    _, with_registration, _, _ = run_linked(run_cli, ONE, role)
    body_lines = set(ONE.splitlines())
    changed = [line[1:] for line in difflib.unified_diff(
        without.splitlines(), with_registration.splitlines(), lineterm="", n=0)
        if line[:1] in "+-" and not line.startswith(("+++", "---"))]
    assert changed
    for line in changed:
        assert line in body_lines or line.startswith("- （五章節以外）相連任務：第 "), line


# T7：失敗態一律照實印、rc 0，⛔ 不帶內容、⛔ 不當作未登記
def test_failure_states_are_reported_as_found(run_cli):
    url8, url9 = "https://github.com/o/r/issues/8", "https://github.com/o/r/issues/9"
    clients = linked_clients()
    clients.issues[("o/r", 9)] = issue(9, "## 需求\n\nL9 需求原文\n")
    clients.issues[("x/denied", 1)] = PermissionDenied("HTTP 403: Resource not accessible\n第二行⛔ 不印")
    body = registered(
        "- not a url",
        f"- {url8}",
        f"- {URL5} {URL5}#issuecomment-404",
        f"- {URL6} {URL6}#issuecomment-55",
        f"- {url9}",
        "- https://github.com/O/R/issues/5",
        "- https://github.com/x/denied/issues/1",
    )
    rc, out, err, _ = run_linked(run_cli, body, "規劃者", clients=clients)
    assert (rc, err) == (0, "")
    index = section(out, "相連任務定位").splitlines()[1:]
    assert index[0] == "- 1｜無法解讀（逐字）：- not a url"
    assert index[1] == f"- 2｜{url8}｜讀取失敗：NotFound: issue #8 不存在於 o/r"
    assert index[2].endswith(f"｜已核定規劃：{URL5}#issuecomment-404 讀取失敗：NotFound: HTTP 404: comment 404")
    assert index[3].endswith(f"｜已核定規劃：{URL6}#issuecomment-55 留言不屬於登記的相連卡："
                             "https://api.github.com/repos/o/r/issues/5")
    assert index[4] == (f"- 5｜{url9}｜OPEN｜需求：在（第 1 行，1 非空行）｜限制與非目標：⛔ 標題不在 body"
                        "｜已核定規劃：未登記")
    assert index[5] == "- 6｜https://github.com/O/R/issues/5｜重複登記（同第 3 筆），⛔ 不重讀"
    assert index[6] == ("- 7｜https://github.com/x/denied/issues/1｜讀取失敗："
                        "PermissionDenied: HTTP 403: Resource not accessible")
    appendix = split_output(out)[1]
    assert "L5 規劃原文" not in appendix              # 留言 404 與他卡留言都⛔ 不帶內文
    assert "L9 需求原文" in appendix and "第二行⛔ 不印" not in out


# T8：帶入角色抽自規則樹；值不在角色值域＝MalformedInput（rc 1）
def _rewrite_roles(rules_root, line):
    doc = rules_root / "core" / "github.md"
    text = doc.read_text(encoding="utf-8")
    assert text.count("帶入角色：`規劃者`、`執行者`") == 1
    doc.write_text(text.replace("帶入角色：`規劃者`、`執行者`", line), encoding="utf-8")


def test_carried_roles_come_from_the_rules_tree(run_cli, rules_root):
    _rewrite_roles(rules_root, "帶入角色：`審核者`")
    rc, out, _, clients = run_linked(run_cli, ONE, "審核者")
    assert rc == 0 and "L5 規劃原文第一行" in section(out, "相連任務原文")
    rc, out, _, clients = run_linked(run_cli, ONE, "執行者")
    assert rc == 0 and clients.calls == [] and "相連任務定位" not in out


def test_carried_role_outside_the_domain_is_malformed(run_cli, rules_root):
    _rewrite_roles(rules_root, "帶入角色：`規劃者`、`owner`")
    rc, out, err, _ = run_linked(run_cli, ONE, "研究者")   # 不論當前角色都驗
    assert (rc, out) == (1, "")
    assert err.startswith("MalformedInput: ") and "owner" in err


def test_missing_registration_rule_is_a_typed_failure(run_cli, rules_root):
    _rewrite_roles(rules_root, "（本行被刪）")
    rc, out, err, _ = run_linked(run_cli, ONE, "執行者")
    assert (rc, out) == (1, "") and "缺少必要層 framework" in err and "帶入角色" in err


def test_registration_rule_lines_never_become_a_required_issue_section(rules_root):
    from wfx.core.rules import issue_section_titles, linked_task_spec

    assert issue_section_titles(rules_root) == ("需求", "限制與非目標", "驗收", "風險與假設", "裁定紀錄")
    spec = linked_task_spec(rules_root)
    assert (spec.title, spec.roles, spec.sections) == ("相連任務", CARRIED, ("需求", "限制與非目標"))


# T9：同一快照跑兩次逐字相同
def test_linked_output_is_byte_identical_for_identical_inputs(run_cli):
    client, clients = FakeClient(snapshot(body=ONE)), linked_clients()
    first = run_cli(role="執行者", client=client, linked_clients=clients)
    second = run_cli(role="執行者", client=client, linked_clients=clients)
    assert first == second and first[0] == 0 and "相連任務原文" in first[1]


# 內部注入點：固定 TaskSource 也走同一個分流（角色不帶＝⛔ 不呼叫 fetch_linked）
def test_fixed_task_source_is_only_asked_for_carried_roles(run_cli):
    source = FixedTaskSource("o/r#370")
    assert run_cli(role="審核者", stage="審核", task_source=source)[0] == 0
    assert source.linked_reads == 0
    assert run_cli(role="執行者", task_source=source)[0] == 0
    assert source.linked_reads == 1


# 唯讀 client：單則留言走 REST GET，原樣回傳
def test_issue_comment_is_a_single_rest_get():
    payload = plan_comment(5, "L5")
    runner = RecordedRunner([(("gh", "api", "repos/o/r/issues/comments/55", "--method", "GET"),
                              (0, json.dumps(payload), ""))])
    assert GhClient("o/r", runner=runner).issue_comment(55) == payload
    assert runner.calls == [("gh", "api", "repos/o/r/issues/comments/55", "--method", "GET")]
