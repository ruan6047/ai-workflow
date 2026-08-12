"""``wfcli review`` 的契約檢查與寫入行為。

樣本刻意寫成「完整查核報告」（散文＋圍籬區塊）而非裸 YAML：實務上查核者交回來
的就是報告全文，抽區塊本身是這條寫入通道的第一道關卡。
"""

from __future__ import annotations

import io
import json as jsonlib
from pathlib import Path

import pytest

from wf_cli.cli import build_parser
from wf_cli.commands import checkpoint_cmd, handoff_cmd, open_cmd, review_cmd
from wf_cli.project import (
    ensure_fields,
    find_item_by_card_id,
    list_items,
    resolve_project,
    set_field_value,
)
from wf_cli.review import ReviewParseError, parse_structured_block
from wf_cli.validation import (
    ValidationError,
    review_invalid_reasons,
    validate_review_report,
)

from .test_checkpoint import EventGhRunner

BASE_TARGET = ["--owner", "acme", "--project", "1"]
REPO = "acme/demo"
SHA = "a" * 40


@pytest.fixture
def fake_runner(monkeypatch):
    # EventGhRunner（見 tests/test_checkpoint.py）＝ FakeGhRunner ＋ 事件平面：
    # 留言可唯讀讀回、每則留言有自己的 URL、`gh api user`。review 自 WF-22-CLI4 起
    # 會在寫入前掃 timeline（去重／checkpoint 閘門），沒有這三條路徑就跑不起來。
    runner = EventGhRunner()
    for module in (open_cmd, handoff_cmd, review_cmd, checkpoint_cmd):
        monkeypatch.setattr(module, "default_runner", runner)
    return runner


def run_cli(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def open_card(card_id: str, *, repo: str | None = REPO) -> int:
    argv = ["open", *BASE_TARGET]
    if repo:
        argv += ["--repo", repo]
    argv += [
        card_id,
        "--feature", "示範功能",
        "--tier", "T2",
        "--db-scope", "none",
        "--core-pain", "痛點文字",
        "--service-goal", "服務的原始目標文字",
        "--exec-capability", "主力型",
        "--exec-capability-reason", "一般實作",
        "--review-capability", "主力型",
        "--review-capability-reason", "一般 review",
    ]
    return run_cli(argv)


def card_item(runner: EventGhRunner, card_id: str):
    project = resolve_project(runner, "acme", 1)
    return find_item_by_card_id(list_items(runner, project), card_id)


def issue_comments(runner: EventGhRunner, issue_url: str) -> list[str]:
    return runner.issues[issue_url].get("comments", [])


def review_argv(card_id: str, input_path: Path, *, repo: str | None = REPO, **extra) -> list[str]:
    argv = ["review", *BASE_TARGET]
    if repo:
        argv += ["--repo", repo]
    argv += [
        card_id,
        "--input", str(input_path),
        "--source-sha", extra.pop("source_sha", SHA),
        "--reviewer", extra.pop("reviewer", "Codex"),
    ]
    for flag, value in extra.items():
        argv += [f"--{flag.replace('_', '-')}"] + ([] if value is True else [str(value)])
    return argv


# --------------------------------------------------------------------------
# 樣本
# --------------------------------------------------------------------------

APPROVE_REPORT = """# 查核報告 DEMO-CARD1 R1

進駐 worktree 唯讀查核，HEAD 與 handoff 指定 source_sha 相符。

## 5. 結構化輸出

```yaml
core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: uv run pytest
    observed: 128 passed in 1.42s
  - command: git rev-parse HEAD
    observed: aaaaaaaa（與 handoff 的 source_sha 相符）
findings: []
```
"""

REQUEST_CHANGES_REPORT = """```yaml
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: uv run pytest -k review
    observed: 3 failed, 25 passed
findings:
  - finding_id: DEMO-CARD1-R1-01
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: self-run-parse
    evidence: uv run pytest -k review 於 tests/test_review.py::test_x 失敗
    disposition: 修正解析器對區塊純量的縮排判定後重送
```
"""

APPROVE_WITHOUT_SELF_RUN = """```yaml
core_pain_resolved: yes
review_result: APPROVE
findings: []
```
"""


# 會計數的裁決自 R1-01 起必須具結 preflight（review-escalation.md §3 第 1 款）。
PREFLIGHT_SUMMARY = "preflight: 分支已推、工作區乾淨、pytest 全綠、trailer 已檢查"


def write_input(tmp_path: Path, text: str, name: str = "review.md") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# 1. 合格 APPROVE
# --------------------------------------------------------------------------


def test_valid_approve_writes_comment_and_flips_status(fake_runner, tmp_path, capsys):
    open_card("DEMO-CARD1")
    item_before = card_item(fake_runner, "DEMO-CARD1")
    set_field_value(
        fake_runner,
        resolve_project(fake_runner, "acme", 1),
        item_before.item_id,
        ensure_fields(fake_runner, "acme", 1)["交付狀態"],
        "🔍待查核",
    )

    rc = run_cli(review_argv("DEMO-CARD1", write_input(tmp_path, APPROVE_REPORT)))
    assert rc == 0

    item = card_item(fake_runner, "DEMO-CARD1")
    assert item.fields["交付狀態"] == "✅通過"
    comments = issue_comments(fake_runner, item.issue_url)
    assert len(comments) == 1
    body = comments[0]
    assert "查核裁決：APPROVE" in body
    assert "uv run pytest" in body and "128 passed" in body  # self_run 逐項落留言
    assert f"DEMO-CARD1-e0-{SHA}" in body  # attempt_id（review-escalation §5）
    assert "Codex" in body
    assert "review by wf-cli → APPROVE" in item.body  # body Log 索引


def test_valid_approve_does_not_touch_iteration_or_owner(fake_runner, tmp_path):
    """iteration 由 handoff 獨占（WF-22-CLI2）；review 併動會讓一次退回被記兩次。"""
    open_card("ITER-CARD1")
    run_cli(
        [
            "handoff", *BASE_TARGET, "--repo", REPO, "ITER-CARD1",
            "--to", "查核者", "--next-stage", "review",
            "--source-sha", SHA, "--evidence", "pytest 全綠",
        ]
    )
    before = card_item(fake_runner, "ITER-CARD1")
    assert before.fields["iteration"] == 0

    assert (
        run_cli(
            review_argv(
                "ITER-CARD1",
                write_input(tmp_path, REQUEST_CHANGES_REPORT),
                preflight_passed=PREFLIGHT_SUMMARY,
            )
        )
        == 0
    )

    after = card_item(fake_runner, "ITER-CARD1")
    assert after.fields["iteration"] == 0  # 未被 review 動過
    assert after.fields["owner"] == "查核者"  # owner 也仍歸 handoff 管
    assert after.fields["最後交接"] == before.fields["最後交接"]


# --------------------------------------------------------------------------
# 2. 合格 REQUEST_CHANGES
# --------------------------------------------------------------------------


def test_valid_request_changes_flips_to_returned_and_lists_findings(fake_runner, tmp_path, capsys):
    open_card("DEMO-CARD2")
    rc = run_cli(
        review_argv(
            "DEMO-CARD2",
            write_input(tmp_path, REQUEST_CHANGES_REPORT),
            preflight_passed=PREFLIGHT_SUMMARY,
        )
    )
    assert rc == 0

    item = card_item(fake_runner, "DEMO-CARD2")
    assert item.fields["交付狀態"] == "↩退回"
    body = issue_comments(fake_runner, item.issue_url)[0]
    assert "DEMO-CARD1-R1-01" in body
    assert "severity=major" in body and "blocking=true" in body
    assert "core_pain_resolved：**no**" in body
    out = capsys.readouterr().out
    # 明確指出 iteration 遞增在 handoff，不在本指令（避免呼叫端自己補寫）。
    assert "handoff --next-stage implementation" in out


# --------------------------------------------------------------------------
# 3. 缺 self_run 的 APPROVE → review-invalid，一律拒收
# --------------------------------------------------------------------------


def test_approve_without_self_run_is_rejected_as_review_invalid(fake_runner, tmp_path, capsys):
    open_card("INVALID-CARD1")
    before = card_item(fake_runner, "INVALID-CARD1")

    rc = run_cli(review_argv("INVALID-CARD1", write_input(tmp_path, APPROVE_WITHOUT_SELF_RUN)))
    assert rc == 4  # review-invalid 與「格式錯誤」(2) 分開，供呼叫端分辨

    err = capsys.readouterr().err
    assert "review-invalid" in err
    assert "§5.2" in err  # 訊息須引 canonical §5.2 原文出處
    assert "不計 iteration" in err

    after = card_item(fake_runner, "INVALID-CARD1")
    assert after.fields["交付狀態"] == before.fields["交付狀態"]  # 狀態不變
    assert issue_comments(fake_runner, after.issue_url) == []  # 未寫任何遠端狀態


def test_approve_with_self_run_entries_that_have_no_command_is_review_invalid(tmp_path):
    text = """```yaml
review_result: APPROVE
core_pain_resolved: yes
self_run:
  - observed: 看起來沒問題
findings: []
```
"""
    assert review_invalid_reasons(parse_structured_block(text))  # 有 self_run 鍵不等於有自跑證據


def test_request_changes_without_self_run_is_schema_error_not_review_invalid(fake_runner, tmp_path, capsys):
    """§5「self_run 不得為空」對兩種結論都成立；只有 APPROVE 那條另有 review-invalid 處置。

    這份樣本同時踩到 2026-08-06 裁決的「REQUEST_CHANGES 不得零 finding」，兩個錯誤
    會一起列出（ValidationError 一次回報全部）——退出碼仍是 2，不是 review-invalid 的 4。
    """
    text = """```yaml
core_pain_resolved: no
review_result: REQUEST_CHANGES
findings: []
```
"""
    open_card("NOSELFRUN-CARD1")
    rc = run_cli(review_argv("NOSELFRUN-CARD1", write_input(tmp_path, text)))
    assert rc == 2
    err = capsys.readouterr().err
    assert "self_run 必填" in err
    assert issue_comments(fake_runner, card_item(fake_runner, "NOSELFRUN-CARD1").issue_url) == []


# --------------------------------------------------------------------------
# 4. 缺 core_pain_resolved
# --------------------------------------------------------------------------


def test_missing_core_pain_resolved_is_rejected(fake_runner, tmp_path, capsys):
    text = """```yaml
review_result: APPROVE
self_run:
  - command: uv run pytest
    observed: 128 passed
findings: []
```
"""
    open_card("NOPAIN-CARD1")
    rc = run_cli(review_argv("NOPAIN-CARD1", write_input(tmp_path, text)))
    assert rc == 2
    err = capsys.readouterr().err
    assert "core_pain_resolved 必填" in err
    assert "§5.1" in err  # 第一判準出處
    assert issue_comments(fake_runner, card_item(fake_runner, "NOPAIN-CARD1").issue_url) == []


def test_core_pain_no_with_approve_is_rejected():
    """第一判準具否決權：痛點未消不得 APPROVE（review-escalation §5）。"""
    data = {
        "review_result": "APPROVE",
        "core_pain_resolved": "no",
        "self_run": [{"command": "pytest", "observed": "ok"}],
        "findings": [],
    }
    with pytest.raises(ValidationError) as exc_info:
        validate_review_report(data)
    assert any("只能是 REQUEST_CHANGES" in e for e in exc_info.value.errors)


# --------------------------------------------------------------------------
# 5. findings 缺欄
# --------------------------------------------------------------------------


def test_finding_missing_required_keys_is_rejected(fake_runner, tmp_path, capsys):
    text = """```yaml
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: uv run pytest
    observed: 3 failed
findings:
  - finding_id: X-R1-01
    severity: major
    evidence: 缺 blocking／finding_class／attribution／root_cause_id／disposition
```
"""
    open_card("BADFINDING-CARD1")
    rc = run_cli(review_argv("BADFINDING-CARD1", write_input(tmp_path, text)))
    assert rc == 2
    err = capsys.readouterr().err
    for missing in ("blocking", "finding_class", "attribution", "root_cause_id", "disposition"):
        assert missing in err
    assert issue_comments(fake_runner, card_item(fake_runner, "BADFINDING-CARD1").issue_url) == []


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("severity", "blocker"),
        ("finding_class", "docs"),
        ("attribution", "reviewer-ish"),
        ("blocking", "maybe"),
    ],
)
def test_finding_enum_values_are_closed(field, bad_value):
    finding = {
        "finding_id": "X-R1-01",
        "severity": "major",
        "blocking": "true",
        "finding_class": "implementation",
        "attribution": "executor",
        "root_cause_id": "r1",
        "evidence": "e",
        "disposition": "d",
    }
    finding[field] = bad_value
    data = {
        "review_result": "REQUEST_CHANGES",
        "core_pain_resolved": "no",
        "self_run": [{"command": "pytest", "observed": "ok"}],
        "findings": [finding],
    }
    with pytest.raises(ValidationError) as exc_info:
        validate_review_report(data)
    assert any(field in e for e in exc_info.value.errors)


def test_duplicate_finding_id_is_rejected():
    finding = {
        "finding_id": "X-R1-01",
        "severity": "minor",
        "blocking": "false",
        "finding_class": "governance",
        "attribution": "planner",
        "root_cause_id": "r1",
        "evidence": "e",
        "disposition": "d",
    }
    data = {
        "review_result": "REQUEST_CHANGES",
        "core_pain_resolved": "yes",
        "self_run": [{"command": "pytest", "observed": "ok"}],
        "findings": [dict(finding), dict(finding)],
    }
    with pytest.raises(ValidationError) as exc_info:
        validate_review_report(data)
    assert any("重複" in e for e in exc_info.value.errors)


def test_missing_findings_key_is_rejected_rather_than_assumed_empty():
    data = {
        "review_result": "APPROVE",
        "core_pain_resolved": "yes",
        "self_run": [{"command": "pytest", "observed": "ok"}],
    }
    with pytest.raises(ValidationError) as exc_info:
        validate_review_report(data)
    assert any("findings" in e for e in exc_info.value.errors)


# --------------------------------------------------------------------------
# 5b. 結論與 findings 的語意一致性（需求方 2026-08-06 裁決 #8：警示 → 硬拒）
# --------------------------------------------------------------------------


def _finding(**overrides) -> dict:
    finding = {
        "finding_id": "X-R1-01",
        "severity": "major",
        "blocking": "true",
        "finding_class": "implementation",
        "attribution": "executor",
        "root_cause_id": "r1",
        "evidence": "重現方式",
        "disposition": "修法",
    }
    finding.update(overrides)
    return finding


def _report_data(result: str, findings: list[dict]) -> dict:
    return {
        "review_result": result,
        "core_pain_resolved": "yes" if result == "APPROVE" else "no",
        "self_run": [{"command": "uv run pytest", "observed": "164 passed"}],
        "findings": findings,
    }


def test_approve_with_blocking_finding_is_hard_rejected():
    """反例：有阻斷缺陷不得核可，二擇一。"""
    with pytest.raises(ValidationError) as exc_info:
        validate_review_report(_report_data("APPROVE", [_finding(blocking="true")]))
    message = "；".join(exc_info.value.errors)
    assert "X-R1-01" in message
    assert "語意矛盾" in message and "二擇一" in message
    assert "#8" in message  # 裁決出處


def test_approve_with_non_blocking_finding_is_accepted():
    """正例：非阻斷 finding 不影響 APPROVE。"""
    report = validate_review_report(_report_data("APPROVE", [_finding(blocking="false")]))
    assert report.review_result == "APPROVE"
    assert report.blocking_findings == ()


def test_request_changes_with_empty_findings_is_hard_rejected():
    """反例：退回必須附至少一項可執行 finding。"""
    with pytest.raises(ValidationError) as exc_info:
        validate_review_report(_report_data("REQUEST_CHANGES", []))
    message = "；".join(exc_info.value.errors)
    assert "findings 為空" in message and "至少一項" in message
    assert "#8" in message


def test_request_changes_with_one_finding_is_accepted():
    """正例：附了 finding 的退回照常通過。"""
    report = validate_review_report(_report_data("REQUEST_CHANGES", [_finding()]))
    assert report.review_result == "REQUEST_CHANGES"
    assert len(report.findings) == 1


def test_hard_rejects_go_through_the_cli_as_exit_2_without_writing(fake_runner, tmp_path, capsys):
    approve_with_blocking = """```yaml
core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: uv run pytest
    observed: 164 passed
findings:
  - finding_id: HARD-R1-01
    severity: critical
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: r1
    evidence: 重現方式
    disposition: 修法
```
"""
    open_card("HARD-CARD1")
    assert run_cli(review_argv("HARD-CARD1", write_input(tmp_path, approve_with_blocking))) == 2
    assert "語意矛盾" in capsys.readouterr().err

    empty_request_changes = """```yaml
core_pain_resolved: no
review_result: REQUEST_CHANGES
self_run:
  - command: uv run pytest
    observed: 1 failed
findings: []
```
"""
    open_card("HARD-CARD2")
    assert run_cli(review_argv("HARD-CARD2", write_input(tmp_path, empty_request_changes))) == 2
    assert "至少一項" in capsys.readouterr().err

    for card_id in ("HARD-CARD1", "HARD-CARD2"):
        item = card_item(fake_runner, card_id)
        assert issue_comments(fake_runner, item.issue_url) == []
        assert item.fields["交付狀態"] == "📥Backlog"  # 兩者都沒翻板


def test_malformed_finding_does_not_trigger_the_consistency_message(capsys):
    """finding 本身缺欄時只報缺欄；不讓衍生的矛盾訊息把作者導去修錯地方。"""
    broken = {"finding_id": "X-R1-01", "severity": "major"}  # 缺 blocking 等六欄
    with pytest.raises(ValidationError) as exc_info:
        validate_review_report(_report_data("APPROVE", [broken]))
    message = "；".join(exc_info.value.errors)
    assert "缺必填欄" in message
    assert "語意矛盾" not in message


# --------------------------------------------------------------------------
# 6. 非法 review_result
# --------------------------------------------------------------------------


@pytest.mark.parametrize("bad", ["approve", "LGTM", "APPROVE_WITH_NITS", "通過"])
def test_illegal_review_result_is_rejected(fake_runner, tmp_path, bad, capsys):
    text = f"""```yaml
core_pain_resolved: yes
review_result: {bad}
self_run:
  - command: uv run pytest
    observed: 128 passed
findings: []
```
"""
    card_id = f"BADRESULT-{abs(hash(bad)) % 10000}"
    open_card(card_id)
    rc = run_cli(review_argv(card_id, write_input(tmp_path, text)))
    assert rc == 2
    assert "review_result" in capsys.readouterr().err
    assert issue_comments(fake_runner, card_item(fake_runner, card_id).issue_url) == []


# --------------------------------------------------------------------------
# 輸入通道與 fail-closed 邊界
# --------------------------------------------------------------------------


def test_stdin_input_is_accepted(fake_runner, monkeypatch, capsys):
    open_card("STDIN-CARD1")
    monkeypatch.setattr("sys.stdin", io.StringIO(APPROVE_REPORT))
    rc = run_cli(
        [
            "review", *BASE_TARGET, "--repo", REPO, "STDIN-CARD1",
            "--source-sha", SHA, "--reviewer", "Codex",
        ]
    )
    assert rc == 0
    assert card_item(fake_runner, "STDIN-CARD1").fields["交付狀態"] == "✅通過"


def test_validate_only_touches_nothing_remote(fake_runner, tmp_path, capsys):
    open_card("VALIDATE-CARD1")
    before = card_item(fake_runner, "VALIDATE-CARD1")
    rc = run_cli(
        review_argv("VALIDATE-CARD1", write_input(tmp_path, APPROVE_REPORT), validate_only=True)
    )
    assert rc == 0
    after = card_item(fake_runner, "VALIDATE-CARD1")
    assert after.fields["交付狀態"] == before.fields["交付狀態"]
    assert issue_comments(fake_runner, after.issue_url) == []
    assert "未寫入任何狀態" in capsys.readouterr().out


def test_missing_repo_is_fail_closed(fake_runner, tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("WFCLI_REPO", raising=False)
    open_card("NOREPO-CARD1")
    rc = run_cli(review_argv("NOREPO-CARD1", write_input(tmp_path, APPROVE_REPORT), repo=None))
    assert rc == 2
    assert "--repo" in capsys.readouterr().err
    assert issue_comments(fake_runner, card_item(fake_runner, "NOREPO-CARD1").issue_url) == []


def test_draft_item_without_issue_timeline_is_rejected(fake_runner, tmp_path, capsys):
    open_card("DRAFT-CARD1", repo=None)  # Project draft item，無 Issue timeline
    rc = run_cli(review_argv("DRAFT-CARD1", write_input(tmp_path, APPROVE_REPORT)))
    assert rc == 2
    assert "draft item" in capsys.readouterr().err
    assert card_item(fake_runner, "DRAFT-CARD1").fields["交付狀態"] == "📥Backlog"


def test_unknown_card_returns_exit_3(fake_runner, tmp_path, capsys):
    rc = run_cli(review_argv("GHOST-CARD1", write_input(tmp_path, APPROVE_REPORT)))
    assert rc == 3
    assert "找不到卡" in capsys.readouterr().err


def test_bad_source_sha_is_rejected_before_reading_input(fake_runner, capsys):
    rc = run_cli(
        [
            "review", *BASE_TARGET, "--repo", REPO, "DEMO-CARD1",
            "--input", "/nonexistent/path.md",
            "--source-sha", "short", "--reviewer", "Codex",
        ]
    )
    assert rc == 2
    assert "source_sha" in capsys.readouterr().err


@pytest.mark.parametrize(
    "flag,value,expected",
    [("--reviewer", "  ", "reviewer"), ("--escalation-epoch", "-1", "escalation-epoch")],
)
def test_reviewer_and_epoch_guards_are_fail_closed(fake_runner, tmp_path, capsys, flag, value, expected):
    open_card("GUARD-CARD1")
    argv = [
        "review", *BASE_TARGET, "--repo", REPO, "GUARD-CARD1",
        "--input", str(write_input(tmp_path, APPROVE_REPORT)),
        "--source-sha", SHA, "--reviewer", "Codex",
    ]
    if flag == "--reviewer":
        argv[argv.index("Codex")] = value
    else:
        argv += [flag, value]
    assert run_cli(argv) == 2
    assert expected in capsys.readouterr().err
    assert issue_comments(fake_runner, card_item(fake_runner, "GUARD-CARD1").issue_url) == []


def test_missing_input_file_is_rejected(fake_runner, capsys):
    rc = run_cli(
        [
            "review", *BASE_TARGET, "--repo", REPO, "DEMO-CARD1",
            "--input", "/nonexistent/path.md",
            "--source-sha", SHA, "--reviewer", "Codex",
        ]
    )
    assert rc == 2
    assert "不存在" in capsys.readouterr().err


def test_status_mismatch_warns_but_does_not_block(fake_runner, tmp_path, capsys):
    # 契約沒規定「非 🔍待查核 不得下裁決」（補記舊裁決／⏸阻塞 期間收報告都是實務
    # 情境），所以只警示不硬擋；是否升級為硬拒屬新裁量，留給需求方。
    open_card("STATUS-CARD1")  # 停在 📥Backlog，不是 🔍待查核
    rc = run_cli(review_argv("STATUS-CARD1", write_input(tmp_path, APPROVE_REPORT)))
    assert rc == 0
    err = capsys.readouterr().err
    assert "警示" in err and "🔍待查核" in err and "📥Backlog" in err
    assert card_item(fake_runner, "STATUS-CARD1").fields["交付狀態"] == "✅通過"


def test_writer_only_keys_are_warned_and_ignored(fake_runner, tmp_path, capsys):
    text = """```yaml
core_pain_resolved: yes
review_result: APPROVE
counts_toward_escalation: false
self_run:
  - command: uv run pytest
    observed: 128 passed
findings: []
```
"""
    open_card("WRITERONLY-CARD1")
    rc = run_cli(review_argv("WRITERONLY-CARD1", write_input(tmp_path, text)))
    assert rc == 0
    err = capsys.readouterr().err
    assert "counts_toward_escalation" in err
    body = issue_comments(fake_runner, card_item(fake_runner, "WRITERONLY-CARD1").issue_url)[0]
    # reviewer 自填的 writer-only 值一律忽略：自 WF-22-CLI4 起 lifecycle writer 會自己
    # 依 §3 推導並寫進結構化區塊，而不是把該鍵留給別人。
    assert "counts_toward_escalation: false" in body
    assert "reviewer 自填一律忽略" in body


# --------------------------------------------------------------------------
# 解析器：區塊抽取與受限 YAML 子集
# --------------------------------------------------------------------------


def test_json_block_is_accepted_and_shares_the_same_checks():
    payload = {
        "core_pain_resolved": "yes",
        "review_result": "APPROVE",
        "self_run": [{"command": "pytest", "observed": "128 passed"}],
        "findings": [],
    }
    text = "報告\n\n```json\n" + jsonlib.dumps(payload, ensure_ascii=False) + "\n```\n"
    report = validate_review_report(parse_structured_block(text))
    assert report.review_result == "APPROVE"
    assert report.delivery_status == "✅通過"


def test_json_true_false_booleans_normalize_for_blocking():
    payload = {
        "core_pain_resolved": "no",
        "review_result": "REQUEST_CHANGES",
        "self_run": [{"command": "pytest", "observed": "1 failed"}],
        "findings": [
            {
                "finding_id": "X-R1-01",
                "severity": "critical",
                "blocking": True,
                "finding_class": "implementation",
                "attribution": "executor",
                "root_cause_id": "r1",
                "evidence": "e",
                "disposition": "d",
            }
        ],
    }
    report = validate_review_report(parse_structured_block("```json\n" + jsonlib.dumps(payload) + "\n```"))
    assert report.findings[0].blocking is True
    assert len(report.blocking_findings) == 1


def test_multiple_candidate_blocks_are_rejected_not_guessed():
    text = APPROVE_REPORT + "\n附錄（範本）：\n" + APPROVE_WITHOUT_SELF_RUN
    with pytest.raises(ReviewParseError) as exc_info:
        parse_structured_block(text)
    assert "無法判定" in str(exc_info.value)


def test_bare_yaml_file_without_fence_is_accepted():
    text = "core_pain_resolved: yes\nreview_result: APPROVE\nself_run:\n  - command: pytest\n    observed: ok\nfindings: []\n"
    assert validate_review_report(parse_structured_block(text)).review_result == "APPROVE"


def test_report_without_structured_block_is_rejected():
    with pytest.raises(ReviewParseError):
        parse_structured_block("看起來沒問題，APPROVE。\n\n```\nsome code\n```\n")


def test_empty_input_is_rejected():
    with pytest.raises(ReviewParseError):
        parse_structured_block("   \n\n")


def test_duplicate_key_is_rejected_instead_of_silently_overwritten():
    text = "review_result: REQUEST_CHANGES\nreview_result: APPROVE\ncore_pain_resolved: yes\n"
    with pytest.raises(ReviewParseError) as exc_info:
        parse_structured_block(text)
    assert "重複" in str(exc_info.value)


def test_literal_block_scalar_keeps_multiline_observed():
    text = """```yaml
core_pain_resolved: yes
review_result: APPROVE
self_run:
  - command: uv run pytest
    observed: |
      128 passed in 1.42s
      warnings: 0
findings: []
```
"""
    report = validate_review_report(parse_structured_block(text))
    assert report.self_run[0].observed.splitlines() == ["128 passed in 1.42s", "warnings: 0"]


def test_quoted_scalar_with_colon_is_preserved():
    text = 'review_result: "APPROVE"\ncore_pain_resolved: yes\nself_run:\n  - command: "grep -n \'a: b\' x"\n    observed: ok\nfindings: []\n'
    report = validate_review_report(parse_structured_block(text))
    assert report.self_run[0].command == "grep -n 'a: b' x"


def test_prose_inside_block_is_rejected():
    text = "```yaml\nreview_result: APPROVE\n看起來沒問題\ncore_pain_resolved: yes\n```"
    with pytest.raises(ReviewParseError) as exc_info:
        parse_structured_block(text)
    assert "散文" in str(exc_info.value)


@pytest.mark.parametrize(
    "text",
    [
        "review_result: &anchor APPROVE\n",
        "review_result: {a: b}\n",
        "review_result: [APPROVE, REQUEST_CHANGES]\n",
        "review_result: APPROVE\nself_run:\n\t- command: x\n",
    ],
)
def test_unsupported_yaml_constructs_fail_closed(text):
    with pytest.raises(ReviewParseError):
        parse_structured_block(text)


def test_template_inline_comments_survive_copy_and_fill():
    """review-prompt.md §5 範本每行都帶註解；照抄填值是最常見用法，必須能用。"""
    text = """```yaml
core_pain_resolved: yes            # 第一判準；no 一律 REQUEST_CHANGES
review_result: APPROVE             # APPROVE | REQUEST_CHANGES
self_run:                          # 必填：查核者自己實際跑過的指令與觀察到的輸出
  - command: uv run pytest
    observed: 159 passed
findings: []                       # 無 finding
```
"""
    report = validate_review_report(parse_structured_block(text))
    assert report.review_result == "APPROVE"
    assert report.core_pain_resolved == "yes"
    assert report.findings == ()
    assert len(report.self_run) == 1


def test_hash_inside_unquoted_value_is_rejected_not_silently_truncated():
    """`evidence: 見 PR #12` 若照 YAML 砍註解會變成 `見 PR`——寧可拒收也不截斷 audit 記錄。"""
    text = "review_result: APPROVE\ncore_pain_resolved: yes\nself_run:\n  - command: pytest\n    observed: 見 PR #12\nfindings: []\n"
    with pytest.raises(ReviewParseError) as exc_info:
        parse_structured_block(text)
    assert "加上引號" in str(exc_info.value)

    quoted = text.replace("observed: 見 PR #12", 'observed: "見 PR #12"')
    report = validate_review_report(parse_structured_block(quoted))
    assert report.self_run[0].observed == "見 PR #12"


def test_url_fragment_without_space_is_not_treated_as_comment():
    text = (
        "review_result: APPROVE\ncore_pain_resolved: yes\n"
        "self_run:\n  - command: pytest\n"
        "    observed: https://github.com/o/r/issues/8#issuecomment-1\nfindings: []\n"
    )
    report = validate_review_report(parse_structured_block(text))
    assert report.self_run[0].observed.endswith("#issuecomment-1")


def test_sequence_item_must_start_with_dash():
    text = "review_result: APPROVE\nself_run:\n  command: pytest\n"
    with pytest.raises(ReviewParseError):
        parse_structured_block(text)


# --------------------------------------------------------------------------
# escalation 帳（WF-22-CLI4 切片 A）：accepted 標記／去重／counts／checkpoint 閘門
# --------------------------------------------------------------------------

COUNTING_REPORT = """```yaml
core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: uv run pytest
    observed: 3 failed, 25 passed
findings:
  - finding_id: {fid}
    severity: major
    blocking: true
    finding_class: implementation
    attribution: executor
    root_cause_id: rc-1
    evidence: pytest 失敗
    disposition: 修好再送
```
"""

NON_COUNTING_REPORT = """```yaml
core_pain_resolved: yes
review_result: REQUEST_CHANGES
self_run:
  - command: uv run pytest
    observed: 1 failed
findings:
  - finding_id: GOV-01
    severity: minor
    blocking: true
    finding_class: governance
    attribution: coordinator
    root_cause_id: rc-gov
    evidence: 卡面缺 baseline 欄
    disposition: 補欄
```
"""


def _counting_review(
    tmp_path, card_id: str, sha: str, fid: str, *, extra=(), preflight=PREFLIGHT_SUMMARY
) -> int:
    path = write_input(tmp_path, COUNTING_REPORT.format(fid=fid), name=f"{fid}.md")
    argv = review_argv(card_id, path, source_sha=sha)
    if preflight is not None:
        argv += ["--preflight-passed", preflight]
    argv += list(extra)
    return run_cli(argv)


def last_comment(fake_runner, card_id: str) -> str:
    return issue_comments(fake_runner, card_item(fake_runner, card_id).issue_url)[-1]


def test_accepted_defaults_to_true_without_any_flag_and_counts_is_derived(fake_runner, tmp_path):
    open_card("ACC-CARD1")
    assert _counting_review(tmp_path, "ACC-CARD1", SHA, "ACC-CARD1-R1-01") == 0
    body = last_comment(fake_runner, "ACC-CARD1")
    assert "accepted: true" in body  # 免旗標的 fail-closed 預設
    assert "status: open" in body
    assert "counting_eligible: true" in body
    assert "counts_toward_escalation: true" in body
    assert "counts_toward_escalation true" in card_item(fake_runner, "ACC-CARD1").body


def test_non_counting_finding_class_does_not_consume_escalation_quota(fake_runner, tmp_path):
    """§3 第 3～4 款：governance／非 executor 歸屬不得消耗 executor 額度。"""
    open_card("ACC-CARD2")
    assert run_cli(review_argv("ACC-CARD2", write_input(tmp_path, NON_COUNTING_REPORT))) == 0
    body = last_comment(fake_runner, "ACC-CARD2")
    assert "accepted: true" in body  # 仍然採認
    assert "counting_eligible: false" in body
    assert "counts_toward_escalation: false" in body


def test_mark_not_accepted_requires_reason_and_records_platform_identity(fake_runner, tmp_path, capsys):
    open_card("ACC-CARD3")
    rc = _counting_review(
        tmp_path, "ACC-CARD3", SHA, "ACC-CARD3-R1-01",
        extra=["--mark-not-accepted", "ACC-CARD3-R1-01=證據不可重現，經需求方裁定撤銷採認"],
    )
    assert rc == 0
    body = last_comment(fake_runner, "ACC-CARD3")
    assert "accepted: false" in body
    assert "ruan6047" in body  # marked_by 取自 gh api user，不是自陳字串
    # 本 repo 的「標記者不得等於 owner」比對在結構上恆真；把恆真本身寫進事件流，
    # 而不是留一個看似有檢查的欄位（形狀同 ai-workflow#39 的 authorization_binding）。
    assert "accepted_marking_binding: structurally-vacuous" in body
    assert "counts_toward_escalation: false" in body  # 移出 open set 後不再計數
    assert "marked_by=ruan6047" in capsys.readouterr().out


@pytest.mark.parametrize(
    "value, needle",
    [
        ("ACC-CARD4-R1-01", "FINDING_ID=非空理由"),
        ("ACC-CARD4-R1-01=", "理由必填"),
        ("NOT-A-FINDING=理由", "不在本次查核輸出內"),
    ],
)
def test_mark_not_accepted_is_fail_closed_and_writes_nothing(fake_runner, tmp_path, capsys, value, needle):
    open_card("ACC-CARD4")
    item_before = card_item(fake_runner, "ACC-CARD4")
    rc = _counting_review(
        tmp_path, "ACC-CARD4", SHA, "ACC-CARD4-R1-01", extra=["--mark-not-accepted", value]
    )
    assert rc == 2
    assert needle in capsys.readouterr().err
    assert issue_comments(fake_runner, item_before.issue_url) == []


def test_duplicate_attempt_id_is_refused_before_writing(fake_runner, tmp_path, capsys):
    """doctor 對重複 attempt_id 判 marker_quarantined 且該隔離永久，故必須擋在寫入前。"""
    open_card("DUP-CARD1")
    assert _counting_review(tmp_path, "DUP-CARD1", SHA, "DUP-CARD1-R1-01") == 0
    before = issue_comments(fake_runner, card_item(fake_runner, "DUP-CARD1").issue_url)
    assert len(before) == 1

    assert _counting_review(tmp_path, "DUP-CARD1", SHA, "DUP-CARD1-R1-01") == 2
    err = capsys.readouterr().err
    assert "已存在於本 Issue timeline" in err
    assert "marker_quarantined" in err
    after = issue_comments(fake_runner, card_item(fake_runner, "DUP-CARD1").issue_url)
    assert len(after) == 1  # 沒有寫出第二則


def test_same_sha_in_a_new_epoch_is_not_a_duplicate(fake_runner, tmp_path):
    open_card("EPOCH-CARD1")
    assert _counting_review(tmp_path, "EPOCH-CARD1", SHA, "EPOCH-CARD1-R1-01") == 0
    rc = _counting_review(
        tmp_path, "EPOCH-CARD1", SHA, "EPOCH-CARD1-R2-01", extra=["--escalation-epoch", "1"]
    )
    assert rc == 0


def test_third_counted_attempt_warns_that_a_checkpoint_is_now_required(fake_runner, tmp_path, capsys):
    open_card("CNT-CARD1")
    for index, sha in enumerate(["a" * 40, "b" * 40, "c" * 40], start=1):
        assert _counting_review(tmp_path, "CNT-CARD1", sha, f"CNT-CARD1-R{index}-01") == 0
        out = capsys.readouterr().out
        if index < 3:
            assert "先建立 escalation-checkpoint" not in out
        else:
            assert "第 3 個可計數 attempt" in out
            assert "先建立 escalation-checkpoint" in out


def test_fourth_review_is_refused_until_the_third_checkpoint_exists(fake_runner, tmp_path, capsys):
    open_card("GATE-CARD1")
    shas = ["a" * 40, "b" * 40, "c" * 40]
    for index, sha in enumerate(shas, start=1):
        assert _counting_review(tmp_path, "GATE-CARD1", sha, f"GATE-CARD1-R{index}-01") == 0
    capsys.readouterr()

    before = len(issue_comments(fake_runner, card_item(fake_runner, "GATE-CARD1").issue_url))
    assert _counting_review(tmp_path, "GATE-CARD1", "d" * 40, "GATE-CARD1-R4-01") == 2
    err = capsys.readouterr().err
    assert "尚未建立 escalation-checkpoint" in err
    assert len(issue_comments(fake_runner, card_item(fake_runner, "GATE-CARD1").issue_url)) == before

    trigger = f"GATE-CARD1-e0-{shas[2]}"
    assert run_cli(
        [
            "checkpoint", *BASE_TARGET, "--repo", REPO, "GATE-CARD1",
            "--trigger-attempt-id", trigger, "--unique-attempt-count", "3",
            "--decision", "escalate", "--rationale", "第二條件成立。",
        ]
    ) == 0
    assert _counting_review(tmp_path, "GATE-CARD1", "d" * 40, "GATE-CARD1-R4-01") == 0


def test_unreadable_marker_makes_the_account_unknown_and_blocks_the_write(fake_runner, tmp_path, capsys):
    """未知不得推定為不計數（review-escalation.md:276）。"""
    open_card("UNK-CARD1")
    item = card_item(fake_runner, "UNK-CARD1")
    fake_runner.execute(
        [
            "issue", "comment", str(item.issue_number), "--repo", REPO,
            "--body", "討論：留言若含 wf-review-event" + ":v1 的字面就會被判受管轄。",
        ]
    )
    assert _counting_review(tmp_path, "UNK-CARD1", SHA, "UNK-CARD1-R1-01") == 2
    err = capsys.readouterr().err
    assert "無法自事件流重建" in err
    assert "不得推定為不計數" in err


def test_owner_snapshot_records_the_reviewer_not_the_executor_under_the_dispatch_convention(
    fake_runner, tmp_path
):
    """快照的可信度邊界，以實跑釘住而不是只寫在註解裡。

    `handoff --next-stage review --to <查核者>` 會把 Project 的 owner 欄改成查核者
    （handoff_cmd.py:136），而裁決是在那之後寫的。所以這個時點快照**通常是查核者**，
    不是產出 source_sha 的執行者——`review-escalation.md` §5 第 3 款要比對的卻是後者。
    這一條就是本欄不足以直接支撐該款的機械證據。
    """
    open_card("OWNER-CARD1")
    run_cli(
        [
            "handoff", *BASE_TARGET, "--repo", REPO, "OWNER-CARD1",
            "--to", "執行者A", "--next-stage", "implementation",
            "--source-sha", SHA, "--evidence", "開工",
        ]
    )
    run_cli(
        [
            "handoff", *BASE_TARGET, "--repo", REPO, "OWNER-CARD1",
            "--to", "查核者B", "--next-stage", "review",
            "--source-sha", SHA, "--evidence", "pytest 全綠",
        ]
    )
    assert _counting_review(tmp_path, "OWNER-CARD1", SHA, "OWNER-CARD1-R1-01") == 0

    body = last_comment(fake_runner, "OWNER-CARD1")
    assert "owner_field_at_verdict_write: 查核者B" in body  # ← 不是「執行者A」
    assert "執行者A" not in body
    # 留言散文必須把這個可信度邊界寫給人看，不能只有機器讀得到。
    assert "不是該 attempt 全程的 owner" in body


def test_counting_verdict_without_preflight_attestation_writes_nothing(fake_runner, tmp_path, capsys):
    """WF-22-CLI4-R1-01 的回歸：會計數的裁決缺 preflight 依據時，一則留言都不得寫出。"""
    open_card("PF-CARD1")
    item = card_item(fake_runner, "PF-CARD1")
    assert _counting_review(tmp_path, "PF-CARD1", SHA, "PF-CARD1-R1-01", preflight=None) == 2
    err = capsys.readouterr().err
    assert "第 1 款的 preflight 依據不存在" in err
    assert issue_comments(fake_runner, item.issue_url) == []
    assert card_item(fake_runner, "PF-CARD1").fields.get("交付狀態") != "↩退回"


def test_non_counting_verdict_needs_no_preflight_and_records_unknown(fake_runner, tmp_path):
    """APPROVE 的 counts 因第 2～4 款自己就是 false，與 preflight 無關，照常寫入。"""
    open_card("PF-CARD2")
    assert run_cli(review_argv("PF-CARD2", write_input(tmp_path, APPROVE_REPORT))) == 0
    body = last_comment(fake_runner, "PF-CARD2")
    assert "preflight_passed: unknown" in body
    assert "preflight_basis: not-established" in body
    assert "counts_toward_escalation: false" in body


def test_attested_preflight_lands_in_the_event_with_its_platform_identity(fake_runner, tmp_path):
    open_card("PF-CARD3")
    assert _counting_review(tmp_path, "PF-CARD3", SHA, "PF-CARD3-R1-01") == 0
    body = last_comment(fake_runner, "PF-CARD3")
    assert "preflight_passed: true" in body
    assert "preflight_basis: writer-attested" in body
    assert "preflight_attested_by: ruan6047" in body  # gh api user，不是自陳字串
    assert "counts_toward_escalation: true" in body


def test_empty_preflight_summary_is_refused(fake_runner, tmp_path, capsys):
    open_card("PF-CARD4")
    item = card_item(fake_runner, "PF-CARD4")
    assert _counting_review(tmp_path, "PF-CARD4", SHA, "PF-CARD4-R1-01", preflight="   ") == 2
    assert "檢查摘要" in capsys.readouterr().err
    assert issue_comments(fake_runner, item.issue_url) == []


def test_validate_only_warns_about_the_preflight_gate_but_still_exits_zero(fake_runner, tmp_path, capsys):
    """查核者自檢不掌握 preflight；那裡只警示，但必須明說實寫會被拒。"""
    open_card("PF-CARD5")
    path = write_input(tmp_path, COUNTING_REPORT.format(fid="PF-CARD5-R1-01"), name="pf5.md")
    rc = run_cli(review_argv("PF-CARD5", path) + ["--validate-only"])
    assert rc == 0
    err = capsys.readouterr().err
    assert "實寫會被拒" in err
    assert "第 1 款的 preflight 依據不存在" in err
