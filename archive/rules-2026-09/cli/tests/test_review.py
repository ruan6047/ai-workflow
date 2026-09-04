"""``wfcli review`` 的契約檢查與寫入行為。

樣本刻意寫成「完整查核報告」（散文＋圍籬區塊）而非裸 YAML：實務上查核者交回來
的就是報告全文，抽區塊本身是這條寫入通道的第一道關卡。
"""

from __future__ import annotations

import ast
import collections
import contextlib
import io
import json as jsonlib
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import warnings
from pathlib import Path

import pytest

from wf_cli import review as review_mod
from wf_cli.cli import build_parser
from wf_cli.commands import checkpoint_cmd, handoff_cmd, open_cmd, review_cmd
from wf_cli.project import (
    ensure_fields,
    find_item_by_card_id,
    list_items,
    resolve_project,
    set_field_value,
)
from wf_cli.review import (
    FACTS_BLOCK_KEY,
    ReviewParseError,
    find_block_by_key,
    parse_structured_block,
)
from wf_cli.validation import (
    ValidationError,
    derive_preflight_basis,
    review_invalid_reasons,
    validate_review_report,
)

from .fake_gh import seed_legacy_draft_card
from .test_checkpoint import (  # noqa: F401  （simulated_preflight_writer 以 fixture 形式使用）
    EventGhRunner,
    arm_preflight,
    inject_counted_attempt,
    simulated_preflight_writer,
)
from .test_pitfalls import with_pitfall_report

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


def open_card(
    card_id: str, *, repo: str | None = REPO, runner=None, preflight_shas=(SHA,)
) -> int:
    """開卡；``runner`` 有給時順便為 ``preflight_shas`` 登記「承接卡已寫出的」preflight 依據。

    本 repo 今天拿不到依據（導出值恆為 ``structurally-unavailable``），故登記只作用在被換掉
    的導出器上（見 test_checkpoint 的 ``simulated_preflight_writer``），不是往 timeline 貼
    留言。**刻意做成顯式參數而不是自動**：測產線語意的測試傳 ``runner=None``（或空 tuple），
    一眼看得出它是故意不登記的——那些測試看到的就是今天真實的行為。
    """
    rc = _open_card(card_id, repo=repo)
    if runner is not None:
        for sha in preflight_shas:
            arm_preflight(card_id, sha)
    return rc


def _open_card(card_id: str, *, repo: str | None = REPO) -> int:
    argv = ["open", *BASE_TARGET]
    if repo:
        argv += ["--repo", repo]
    argv += [
        card_id,
        "--from-issue", open_cmd.default_runner.seed_list_issue(repo or "acme/workflow"),
        "--acceptance", "可獨立驗證的驗收條件一條",
        "--stage-plan", "需求=把清單項變成一張可派工的卡",
        "--tier-basis-sensitive-surfaces", "wfcli 狀態面寫入通道",
        "--tier-basis-recoverability", "git revert",
        "--tier-basis-blast-radius", "單一 repo",
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


def write_input(tmp_path: Path, text: str, name: str = "review.md") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# 1. 合格 APPROVE
# --------------------------------------------------------------------------


def test_valid_approve_writes_comment_and_flips_status(fake_runner, tmp_path, capsys):
    open_card("DEMO-CARD1", runner=fake_runner)
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
    comments = verdict_comments(fake_runner, "DEMO-CARD1")
    assert len(comments) == 1
    body = comments[0]
    assert "查核裁決：APPROVE" in body
    assert "uv run pytest" in body and "128 passed" in body  # self_run 逐項落留言
    assert f"DEMO-CARD1-e0-{SHA}" in body  # attempt_id（review-escalation §5）
    assert "Codex" in body
    assert "review by wf-cli → APPROVE" in item.body  # body Log 索引


def test_valid_approve_does_not_touch_iteration_or_owner(fake_runner, tmp_path):
    """iteration 由 handoff 獨占（WF-22-CLI2）；review 併動會讓一次退回被記兩次。"""
    open_card("ITER-CARD1", runner=fake_runner)
    # ⚠️ ``with_pitfall_report`` 是 WF-STAGE-PITFALL-LIST1 加的必要前提：``handoff``
    # 要有一份離開現階段的族清冊回應才肯寫任何一格。清冊由該階段導出，⛔ 不塞字串。
    run_cli(
        with_pitfall_report(
            [
                "handoff", *BASE_TARGET, "--repo", REPO, "ITER-CARD1",
                "--to", "查核者", "--next-stage", "review",
                "--source-sha", SHA, "--evidence", "pytest 全綠",
            ],
            "ITER-CARD1",
        )
    )
    before = card_item(fake_runner, "ITER-CARD1")
    assert before.fields["iteration"] == 0

    assert (
        run_cli(
            review_argv("ITER-CARD1", write_input(tmp_path, REQUEST_CHANGES_REPORT))
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
    open_card("DEMO-CARD2", runner=fake_runner)
    rc = run_cli(
        review_argv("DEMO-CARD2", write_input(tmp_path, REQUEST_CHANGES_REPORT))
    )
    assert rc == 0

    item = card_item(fake_runner, "DEMO-CARD2")
    assert item.fields["交付狀態"] == "↩退回"
    body = next(c for c in issue_comments(fake_runner, item.issue_url) if "查核裁決" in c)
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
    open_card("INVALID-CARD1", runner=fake_runner)
    before = card_item(fake_runner, "INVALID-CARD1")

    rc = run_cli(review_argv("INVALID-CARD1", write_input(tmp_path, APPROVE_WITHOUT_SELF_RUN)))
    assert rc == 4  # review-invalid 與「格式錯誤」(2) 分開，供呼叫端分辨

    err = capsys.readouterr().err
    assert "review-invalid" in err
    assert "§5.2" in err  # 訊息須引 canonical §5.2 原文出處
    assert "不計 iteration" in err

    after = card_item(fake_runner, "INVALID-CARD1")
    assert after.fields["交付狀態"] == before.fields["交付狀態"]  # 狀態不變
    assert [c for c in issue_comments(fake_runner, after.issue_url) if "查核裁決" in c] == []  # 未寫任何遠端狀態


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
    open_card("NOSELFRUN-CARD1", runner=fake_runner)
    rc = run_cli(review_argv("NOSELFRUN-CARD1", write_input(tmp_path, text)))
    assert rc == 2
    err = capsys.readouterr().err
    assert "self_run 必填" in err
    assert verdict_comments(fake_runner, "NOSELFRUN-CARD1") == []


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
    open_card("NOPAIN-CARD1", runner=fake_runner)
    rc = run_cli(review_argv("NOPAIN-CARD1", write_input(tmp_path, text)))
    assert rc == 2
    err = capsys.readouterr().err
    assert "core_pain_resolved 必填" in err
    assert "§5.1" in err  # 第一判準出處
    assert verdict_comments(fake_runner, "NOPAIN-CARD1") == []


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
    open_card("BADFINDING-CARD1", runner=fake_runner)
    rc = run_cli(review_argv("BADFINDING-CARD1", write_input(tmp_path, text)))
    assert rc == 2
    err = capsys.readouterr().err
    for missing in ("blocking", "finding_class", "attribution", "root_cause_id", "disposition"):
        assert missing in err
    assert verdict_comments(fake_runner, "BADFINDING-CARD1") == []


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
    open_card("HARD-CARD1", runner=fake_runner)
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
    open_card("HARD-CARD2", runner=fake_runner)
    assert run_cli(review_argv("HARD-CARD2", write_input(tmp_path, empty_request_changes))) == 2
    assert "至少一項" in capsys.readouterr().err

    for card_id in ("HARD-CARD1", "HARD-CARD2"):
        item = card_item(fake_runner, card_id)
        assert [c for c in issue_comments(fake_runner, item.issue_url) if "查核裁決" in c] == []
        assert item.fields["交付狀態"] == "💡需求"  # 兩者都沒翻板（open 的初始值）


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
    open_card("STDIN-CARD1", runner=fake_runner)
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
    open_card("VALIDATE-CARD1", runner=fake_runner)
    before = card_item(fake_runner, "VALIDATE-CARD1")
    rc = run_cli(
        review_argv("VALIDATE-CARD1", write_input(tmp_path, APPROVE_REPORT), validate_only=True)
    )
    assert rc == 0
    after = card_item(fake_runner, "VALIDATE-CARD1")
    assert after.fields["交付狀態"] == before.fields["交付狀態"]
    assert [c for c in issue_comments(fake_runner, after.issue_url) if "查核裁決" in c] == []
    assert "未寫入任何狀態" in capsys.readouterr().out


def test_missing_repo_is_fail_closed(fake_runner, tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("WFCLI_REPO", raising=False)
    open_card("NOREPO-CARD1", runner=fake_runner)
    rc = run_cli(review_argv("NOREPO-CARD1", write_input(tmp_path, APPROVE_REPORT), repo=None))
    assert rc == 2
    assert "--repo" in capsys.readouterr().err
    assert verdict_comments(fake_runner, "NOREPO-CARD1") == []


def test_draft_item_without_issue_timeline_is_rejected(fake_runner, tmp_path, capsys):
    # ⚠️ ``open`` 已建不出 DraftIssue（`WF-REDESIGN-W1` 驗收 2）⇒ 直接以 project API
    # 造一張，模擬板上既有的歷史 draft 卡。這一條就是「遺留可讀」那一軸。
    seed_legacy_draft_card(fake_runner, "DRAFT-CARD1")
    rc = run_cli(review_argv("DRAFT-CARD1", write_input(tmp_path, APPROVE_REPORT)))
    assert rc == 2
    assert "draft item" in capsys.readouterr().err
    assert card_item(fake_runner, "DRAFT-CARD1").fields["交付狀態"] == "💡需求"  # 停在初始值


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
    open_card("GUARD-CARD1", runner=fake_runner)
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
    assert verdict_comments(fake_runner, "GUARD-CARD1") == []


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
    open_card("STATUS-CARD1", runner=fake_runner)  # 停在 open 的初始值 💡需求，不是 🔍待查核
    rc = run_cli(review_argv("STATUS-CARD1", write_input(tmp_path, APPROVE_REPORT)))
    assert rc == 0
    err = capsys.readouterr().err
    assert "警示" in err and "🔍待查核" in err and "💡需求" in err
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
    open_card("WRITERONLY-CARD1", runner=fake_runner)
    rc = run_cli(review_argv("WRITERONLY-CARD1", write_input(tmp_path, text)))
    assert rc == 0
    err = capsys.readouterr().err
    assert "counts_toward_escalation" in err
    body = verdict_comments(fake_runner, "WRITERONLY-CARD1")[0]
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


def _counting_review(tmp_path, card_id: str, sha: str, fid: str, *, extra=()) -> int:
    """符合 §3 第 2～4 款的裁決。**它不會計數**——第 1 款的依據在本 repo 不可得，
    故 counts 落 `unavailable`（見 test_..._records_unavailable_not_false）。"""
    path = write_input(tmp_path, COUNTING_REPORT.format(fid=fid), name=f"{fid}.md")
    argv = review_argv(card_id, path, source_sha=sha)
    argv += list(extra)
    return run_cli(argv)


def last_comment(fake_runner, card_id: str) -> str:
    return issue_comments(fake_runner, card_item(fake_runner, card_id).issue_url)[-1]


def facts_block_of(body: str) -> dict:
    """裁決留言裡的結構化帳區塊。**斷言只看它，不看散文**——散文本來就會提到那些鍵名。"""
    data = find_block_by_key(body, FACTS_BLOCK_KEY)
    assert data is not None, "裁決留言沒有 escalation 帳區塊"
    return data


def verdict_comments(fake_runner, card_id: str) -> list[str]:
    """只算裁決留言——preflight event 也是留言，不能混進「有沒有寫入」的判定。"""
    item = card_item(fake_runner, card_id)
    return [c for c in issue_comments(fake_runner, item.issue_url) if "查核裁決" in c]


def test_accepted_defaults_to_true_without_any_flag_and_counts_is_derived(fake_runner, tmp_path):
    open_card("ACC-CARD1", runner=fake_runner)
    assert _counting_review(tmp_path, "ACC-CARD1", SHA, "ACC-CARD1-R1-01") == 0
    body = last_comment(fake_runner, "ACC-CARD1")
    assert "accepted: true" in body  # 免旗標的 fail-closed 預設
    assert "status: open" in body
    assert "counting_eligible: true" in body
    assert "counts_toward_escalation: true" in body
    assert "counts_toward_escalation true" in card_item(fake_runner, "ACC-CARD1").body
    assert "preflight_passed: true" in body  # §5「Adapter 必填欄位」的字面 true，由 preflight event 支撐


def test_non_counting_finding_class_does_not_consume_escalation_quota(fake_runner, tmp_path):
    """§3 第 3～4 款：governance／非 executor 歸屬不得消耗 executor 額度。"""
    open_card("ACC-CARD2", runner=fake_runner)
    assert run_cli(review_argv("ACC-CARD2", write_input(tmp_path, NON_COUNTING_REPORT))) == 0
    body = last_comment(fake_runner, "ACC-CARD2")
    assert "accepted: true" in body  # 仍然採認
    assert "counting_eligible: false" in body
    assert "counts_toward_escalation: false" in body


def test_mark_not_accepted_requires_reason_and_records_platform_identity(fake_runner, tmp_path, capsys):
    open_card("ACC-CARD3", runner=fake_runner)
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
    # 移出 open set 後第 2～4 款不再成立，故 false 是**有依據的**，不是 unavailable。
    assert "counts_toward_escalation: false" in body
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
    open_card("ACC-CARD4", runner=fake_runner)
    rc = _counting_review(
        tmp_path, "ACC-CARD4", SHA, "ACC-CARD4-R1-01", extra=["--mark-not-accepted", value]
    )
    assert rc == 2
    assert needle in capsys.readouterr().err
    assert verdict_comments(fake_runner, "ACC-CARD4") == []


def test_duplicate_attempt_id_is_refused_before_writing(fake_runner, tmp_path, capsys):
    """doctor 對重複 attempt_id 判 marker_quarantined 且該隔離永久，故必須擋在寫入前。"""
    open_card("DUP-CARD1", runner=fake_runner)
    assert _counting_review(tmp_path, "DUP-CARD1", SHA, "DUP-CARD1-R1-01") == 0
    before = verdict_comments(fake_runner, "DUP-CARD1")
    assert len(before) == 1

    assert _counting_review(tmp_path, "DUP-CARD1", SHA, "DUP-CARD1-R1-01") == 2
    err = capsys.readouterr().err
    assert "已存在於本 Issue timeline" in err
    assert "marker_quarantined" in err
    after = verdict_comments(fake_runner, "DUP-CARD1")
    assert len(after) == 1  # 沒有寫出第二則
def test_review_without_a_preflight_basis_still_writes_but_asserts_nothing(
    fake_runner, tmp_path, capsys, monkeypatch
):
    """需求方 2026-08-12 裁定的核心：**寫得進去**，且事件上看得見閘門沒有鑑別力。

    這條同時守著兩個相反方向的錯誤：往回退成「恆拒」（狀態面又分不出已查核／未查核，
    ai-workflow#13 解過的問題），或往前滑成「寫個 false／true」（洗白／偽造）。
    """
    monkeypatch.setattr(review_cmd, "derive_preflight_basis", derive_preflight_basis)
    open_card("PF-CARD1", runner=None)  # 刻意不登記 preflight → 走 src 真身
    before = card_item(fake_runner, "PF-CARD1")

    assert _counting_review(tmp_path, "PF-CARD1", SHA, "PF-CARD1-R1-01") == 0
    block = facts_block_of(last_comment(fake_runner, "PF-CARD1"))
    assert block["preflight_basis_binding"] == "structurally-unavailable"
    assert block["escalation_account"] == "not-asserted"
    # 兩個斷言用的鍵都不出現——不寫 true（偽造）、不寫 false（洗白）、不擴充成三值。
    assert "preflight_passed" not in block
    assert "counts_toward_escalation" not in block

    after = card_item(fake_runner, "PF-CARD1")
    assert after.fields.get("交付狀態") != before.fields.get("交付狀態")  # 狀態面真的翻了
    assert "escalation_account not-asserted" in after.body  # Log 索引行同樣不寫 false
    err = capsys.readouterr().err
    assert "不對 escalation 帳作任何斷言" in err
    assert "含三振門檻" in err
    assert "執行者沒有累計" in err  # 明說消費者不得如此讀


def test_a_second_review_is_not_blocked_by_the_first_unasserted_one(
    fake_runner, tmp_path, capsys, monkeypatch
):
    """恆拒版的真正代價在這裡：未斷言的事件必須**讀得懂**，否則下一輪就寫不進去。"""
    monkeypatch.setattr(review_cmd, "derive_preflight_basis", derive_preflight_basis)
    open_card("PF-CARD4", runner=None)
    assert _counting_review(tmp_path, "PF-CARD4", SHA, "PF-CARD4-R1-01") == 0
    assert _counting_review(tmp_path, "PF-CARD4", "e" * 40, "PF-CARD4-R2-01") == 0
    assert len(verdict_comments(fake_runner, "PF-CARD4")) == 2


def test_validate_only_still_works_without_any_preflight_event(fake_runner, tmp_path, capsys):
    """--validate-only 只驗格式；但它必須把「實寫時帳不會被斷言」講在前面。"""
    open_card("PF-CARD3", runner=None)
    path = write_input(tmp_path, COUNTING_REPORT.format(fid="PF-CARD3-R1-01"), name="pf3.md")
    assert run_cli(review_argv("PF-CARD3", path) + ["--validate-only"]) == 0
    out, err = capsys.readouterr()
    assert "驗證通過" in out
    assert "structurally-unavailable" in err
    assert "not-asserted" in err


# ---- R4-01：查核者的重現在 CLI 層的端對端回歸 ----
#
# R4-01 的重現是「把任意四欄 YAML 餵給 `preflight_basis_from_body` 就得 event-verified，
# 缺 event_url 也照過」。那個讀取器已刪除；這裡從 CLI 這一端釘死同一件事：**無論 timeline
# 上有什麼留言**，導出值都是 structurally-unavailable、帳都不被斷言。
#
# ⚠️ 判準在需求方 2026-08-12 裁定後改了：不是「一律拒絕寫入」，是「一律導出
# structurally-unavailable，且沒有任何輸入能把它變成 event-verified」。裁決照寫。


def _preflight_lookalike(card_id: str, sha: str, *, extra_lines: tuple[str, ...] = ()) -> str:
    """一則「長得像受管轄 preflight pass event」的留言。任何人都打得出來——這正是重點。"""
    return "\n".join(
        [
            "## Preflight pass",
            "",
            "```yaml",
            "wf_preflight_pass: v1",
            f"card_id: {card_id}",
            f"source_sha: {sha}",
            "preflight_passed: true",
            *extra_lines,
            "```",
        ]
    )


@pytest.mark.parametrize(
    "extra_lines, label",
    [
        ((), "查核者的原始重現：四欄，連 event_url 都沒有"),
        (('event_url: "https://github.com/acme/demo/issues/1#issuecomment-1"',), "補上 event_url"),
        (
            (
                "event_id: 018f-dead-beef",
                "type: handoff-accepted",
                "actor: ruan6047",
                "occurred_at: 2026-08-12T21:00:00+08:00",
                "state_version: 7",
                "iteration: 4",
                'evidence: "pytest 全綠"',
                'event_url: "https://github.com/acme/demo/issues/1#issuecomment-1"',
            ),
            "補齊 canonical §4.1 的整組 lifecycle envelope",
        ),
    ],
)
def test_no_lookalike_comment_unlocks_the_write(
    fake_runner, tmp_path, capsys, monkeypatch, extra_lines, label
):
    """補欄位不會讓留言變成受管轄事件——「受管轄」是通道屬性，不是內文屬性。"""
    # 「宣告成功前先核執行身分」：明確把導出器還原成 src 的真身，不倚賴模擬版的 fallthrough。
    monkeypatch.setattr(review_cmd, "derive_preflight_basis", derive_preflight_basis)
    open_card("R4-CARD1", runner=None)
    item = card_item(fake_runner, "R4-CARD1")
    fake_runner.execute(
        [
            "issue", "comment", str(item.issue_number), "--repo", REPO,
            "--body", _preflight_lookalike("R4-CARD1", SHA, extra_lines=extra_lines),
        ]
    )

    assert _counting_review(tmp_path, "R4-CARD1", SHA, "R4-CARD1-R1-01") == 0, label
    block = facts_block_of(last_comment(fake_runner, "R4-CARD1"))
    # 那則留言就擺在 timeline 上，導出值仍是 structurally-unavailable。
    assert block["preflight_basis_binding"] == "structurally-unavailable", label
    assert block["escalation_account"] == "not-asserted", label
    assert "preflight_passed" not in block, label
    assert "counts_toward_escalation" not in block, label
    assert "不對 escalation 帳作任何斷言" in capsys.readouterr().err, label




def test_fourth_review_is_refused_until_the_third_checkpoint_exists(fake_runner, tmp_path, capsys):
    """閘門本身沒壞：一旦承接卡讓 preflight 事件存在，整條鏈照常運作。

    三個可計數 attempt 以 `inject_counted_attempt` 直接構造（帶 event-verified 依據），
    因為 `wfcli review` 今天產不出 counts=true。
    """
    open_card("GATE-CARD1", runner=fake_runner, preflight_shas=("d" * 40,))
    attempts = [
        inject_counted_attempt(fake_runner, "GATE-CARD1", sha, f"GATE-CARD1-R{i}-01")
        for i, sha in enumerate(["a" * 40, "b" * 40, "c" * 40], start=1)
    ]
    capsys.readouterr()

    before = len(verdict_comments(fake_runner, "GATE-CARD1"))
    assert _counting_review(tmp_path, "GATE-CARD1", "d" * 40, "GATE-CARD1-R4-01") == 2
    err = capsys.readouterr().err
    assert "尚未建立 escalation-checkpoint" in err
    assert len(verdict_comments(fake_runner, "GATE-CARD1")) == before

    assert run_cli(
        [
            "checkpoint", *BASE_TARGET, "--repo", REPO, "GATE-CARD1",
            "--trigger-attempt-id", attempts[2], "--unique-attempt-count", "3",
            "--decision", "escalate", "--rationale", "第二條件成立。",
        ]
    ) == 0
    assert _counting_review(tmp_path, "GATE-CARD1", "d" * 40, "GATE-CARD1-R4-01") == 0




def test_unreadable_marker_makes_the_account_unknown_and_blocks_the_write(fake_runner, tmp_path, capsys):
    """未知不得推定為不計數（語意見 review-escalation.md §5「cutover 前歷史事件維持原貌」）。"""
    open_card("UNK-CARD1", runner=fake_runner)
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
    （`handoff_cmd.run.write_status_face` 逐字 `fields["owner"], args.to`），而裁決是
    在那之後寫的。所以這個時點快照**通常是查核者**，
    不是產出 source_sha 的執行者——`review-escalation.md` §5 第 3 款要比對的卻是後者。
    這一條就是本欄不足以直接支撐該款的機械證據。
    """
    open_card("OWNER-CARD1", runner=fake_runner)
    # ⚠️ 兩次呼叫要的**不是同一份清冊**：第一次離開 ``需求``（8 族），而它把階段推到
    # ``執行``，於是第二次離開 ``執行``（13 族）。⇒ 逐次由該階段導出，⛔ 不塞字串。
    run_cli(
        with_pitfall_report(
            [
                "handoff", *BASE_TARGET, "--repo", REPO, "OWNER-CARD1",
                "--to", "執行者A", "--next-stage", "implementation",
                "--source-sha", SHA, "--evidence", "開工",
            ],
            "OWNER-CARD1",
        )
    )
    run_cli(
        with_pitfall_report(
            [
                "handoff", *BASE_TARGET, "--repo", REPO, "OWNER-CARD1",
                "--to", "查核者B", "--next-stage", "review",
                "--source-sha", SHA, "--evidence", "pytest 全綠",
            ],
            "OWNER-CARD1",
        )
    )
    assert _counting_review(tmp_path, "OWNER-CARD1", SHA, "OWNER-CARD1-R1-01") == 0

    body = last_comment(fake_runner, "OWNER-CARD1")
    assert "owner_field_at_verdict_write: 查核者B" in body  # ← 不是「執行者A」
    assert "執行者A" not in body
    # 留言散文必須把這個可信度邊界寫給人看，不能只有機器讀得到。
    assert "不是該 attempt 全程的 owner" in body


# ===========================================================================
# WF-BLOCK-VERSION-REGRESSION1（aiwf#161）：升版 ⇒ 既有事件全部讀不回
# ===========================================================================
#
# **守的是什麼**：`review.BLOCK_VERSION` 由數種結構化區塊共用（數目由下方 AST
# 導出，⛔ 不寫死），而已落地的事件留言是**不可變**的——其版本字面永遠停在寫入
# 當下的值。把常數改成別的值，讀取端就對**每一則**既有事件回「讀不懂」，而
# `validation` 的閘門把「讀不懂」當 fail-closed，於是整批卡當場停機。
#
# ⛔ **本節不實作、也不主張任何升版路徑**，⛔ 也不指名由哪張卡承接。它只讓「升版」
# 這件事在 CI 上**會紅**，並在紅的時候印出「既有事件不會跟著升版」這句話。

#: 已寫進 timeline 的事件所**凍結**的區塊版本字面。
#:
#: ⭐ **刻意不由 `review.BLOCK_VERSION` 導出。** 導出就會跟著升版一起變，於是這條
#: 測試永遠綠——那是零資訊。它是逐字黃金值：升版時本節必須紅。
#:
#: ⚠️ **把這個值跟著改大，不會讓任何一則既有事件變得讀得回。** 既有留言是不可變的，
#: 它們的版本字面停在寫入當下。改這裡只是把偵測器關掉；活看板那一條
#: （`test_the_live_board_events_still_carry_the_frozen_block_version`）就是為了讓
#: 這個關法在 CI 上仍然會紅而存在的。
_FROZEN_BLOCK_VERSION_IN_WRITTEN_EVENTS = "v1"

#: 變異用的探針值。值本身沒有語意，只要求「不等於 `BLOCK_VERSION`」。
_PROBE_BLOCK_VERSION = "v-probe-not-a-real-version"

#: AST 面的識別後綴：`review.py` 的區塊鍵常數一律以此結尾。
_BLOCK_KEY_SUFFIX = "_BLOCK_KEY"


def _nodes_with_enclosing_function(tree: ast.AST):
    """走訪 AST，逐一回傳 `(節點, 外圍函式名堆疊)`。"""

    def walk(node, stack):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield from walk(child, (*stack, child.name))
            else:
                yield child, stack
                yield from walk(child, stack)

    yield from walk(tree, ())


def _block_version_sites() -> tuple[dict[str, tuple], dict[str, tuple]]:
    """由 `review.py` 的 AST 導出「誰比對 `BLOCK_VERSION`」與「誰寫出它」。

    ⛔ **不得改成手打清單。** 判準是**節點形態**：
      * 讀取端 ＝ 含 `BLOCK_VERSION` 的 `ast.Compare`（⛔ 不篩運算子——今天三處裡
        有兩處是 `!=`、一處是 `==`，只認 `!=` 會靜默漏掉 `body_has_contract_baseline`）；
      * 寫入端 ＝ 含 `BLOCK_VERSION` 的 f-string（`ast.JoinedStr`）。

    每一處必須恰好引用一個 `*_BLOCK_KEY` 常數，且必須有外圍函式——判不出來一律
    硬紅（fail closed），⛔ 不猜。回傳的兩個 dict 以**區塊鍵字串**為鍵。
    """
    tree = ast.parse(Path(review_mod.__file__).read_text(encoding="utf-8"))
    readers: dict[str, tuple] = {}
    writers: dict[str, tuple] = {}
    for node, stack in _nodes_with_enclosing_function(tree):
        if isinstance(node, ast.Compare):
            bucket, kind = readers, "讀取端比較"
        elif isinstance(node, ast.JoinedStr):
            bucket, kind = writers, "寫入端 f-string"
        else:
            continue
        names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
        if "BLOCK_VERSION" not in names:
            continue
        keys = sorted(n for n in names if n.endswith(_BLOCK_KEY_SUFFIX))
        assert len(keys) == 1, (
            f"review.py:{node.lineno} 的{kind}引用了 {len(keys)} 個 {_BLOCK_KEY_SUFFIX} "
            f"常數（{keys}）⇒ 對不到唯一的區塊鍵，判不了，fail closed"
        )
        assert stack, f"review.py:{node.lineno} 的{kind}不在任何函式內 ⇒ 找不到讀寫入口"
        key = getattr(review_mod, keys[0])
        assert key not in bucket, (
            f"區塊鍵 {key!r} 有多於一處{kind}（review.py:{node.lineno}）⇒ "
            "本節的語料對應是一對一的，多出來的那處不在射程內，先來這裡登記"
        )
        bucket[key] = (keys[0], stack[-1], node.lineno)
    assert readers, (
        "AST 掃不到任何一處與 BLOCK_VERSION 的比較 ⇒ 本節在檢查一個不存在的東西，"
        "fail closed（可能是 review.py 改寫了比對形態，判準須跟著改）"
    )
    return readers, writers


@contextlib.contextmanager
def _block_version_is(value: str):
    """暫時把 `review.BLOCK_VERSION` 換成 `value`（模組層屬性，讀取端呼叫時才取）。"""
    original = review_mod.BLOCK_VERSION
    review_mod.BLOCK_VERSION = value
    try:
        yield
    finally:
        review_mod.BLOCK_VERSION = original


def _facts_block_bodies() -> tuple[str, ...]:
    """`wf_escalation_facts` 語料：由產線 renderer 產出，⛔ 非手打 YAML。

    兩種形狀都取：`not-asserted`（今日產線唯一走得到的那支）與 `asserted`
    （模擬承接卡落地後的世界，見 `PreflightBasis` 的說明）。
    """
    report = review_mod.ReviewReport(
        review_result=review_mod.REVIEW_RESULTS[0],
        core_pain_resolved=review_mod.CORE_PAIN_VALUES[0],
        self_run=(),
        findings=(),
    )
    attempt = review_mod.attempt_id("BV-REGRESSION1", 0, "b" * 40)
    return (
        review_mod.render_escalation_facts_block(
            attempt=attempt,
            escalation_epoch=0,
            report=report,
            marks={},
            counts_toward_escalation=None,
        ),
        review_mod.render_escalation_facts_block(
            attempt=attempt,
            escalation_epoch=0,
            report=report,
            marks={},
            counts_toward_escalation=True,
            preflight=review_mod.PreflightBasis(
                basis="event-verified",
                source_event="https://example.invalid/preflight-pass-event",
                summary="測試語料；產線沒有任何輸入抵達得了這裡",
            ),
        ),
    )


def _checkpoint_block_bodies() -> tuple[str, ...]:
    """`wf_escalation_checkpoint` 語料：由產線 renderer 產出。

    ⚠️ 這一種區塊在活看板上**今天一則都沒有**（2026-08-27 實測 0 則）⇒ 只靠活看板
    導出語料會讓 `checkpoint_facts_from_body` 那一處比較**完全不在射程內**，
    移除它測試也不會紅。這就是本節的語料必須由 renderer 產生、⛔ 不能只取活看板的
    原因；⭐ 這一段是「涵蓋面」的實質，⛔ 不是形式。
    """
    return (
        review_mod.render_checkpoint_comment(
            card_id="BV-REGRESSION1",
            escalation_epoch=0,
            trigger_attempt_id=review_mod.attempt_id("BV-REGRESSION1", 0, "b" * 40),
            unique_attempt_count=1,
            checkpoint_decision=review_mod.CHECKPOINT_DECISIONS[0],
            checkpoint_rationale="語料由產線 renderer 產生。",
            written_by="wf-cli tests",
            timestamp="2020-01-01T00:00:00+08:00",
        ),
    )


def _baseline_block_bodies() -> tuple[str, ...]:
    """`wf_contract_baseline` 語料：由產線 renderer 產出。"""
    return (
        review_mod.render_contract_baseline_comment(
            card_id="BV-REGRESSION1",
            declared_by="wf-cli tests",
            rationale="語料由產線 renderer 產生。",
            timestamp="2020-01-01T00:00:00+08:00",
        ),
    )


#: 區塊鍵 → 語料工廠。⛔ 鍵不手打字面，一律取 `review` 的常數。
#:
#: ⚠️ **這張表不決定涵蓋面，AST 才決定**：下方測試會比對它的鍵集合與 AST 導出的
#: 讀取端／寫入端鍵集合是否**三者相等**。日後新增第四種區塊而沒有來這裡補語料，
#: 那條比對就會紅——這正是 A2 要的「不得把 3 寫死」。
_CORPUS_FACTORIES = {
    review_mod.FACTS_BLOCK_KEY: _facts_block_bodies,
    review_mod.CHECKPOINT_BLOCK_KEY: _checkpoint_block_bodies,
    review_mod.BASELINE_BLOCK_KEY: _baseline_block_bodies,
}


def _readable(reader, body: str) -> bool:
    """讀得回嗎。三個讀取端回傳型別不同（dataclass／dataclass／bool），統一成布林。"""
    return bool(reader(body))


def test_bumping_block_version_makes_every_already_written_event_unreadable():
    """升版 `review.BLOCK_VERSION` ⇒ 已寫進 timeline 的事件**全部**讀不回。

    ## 母體怎麼來、為什麼不釘數字（⚠️ 這一段是交付的一部分，⛔ 不是註解裝飾）

    **母體不是一個數字，是一組關係。** 本節的語料由兩層導出，兩層都在**跑的當下**
    重算，⛔ 沒有任何一處把母體大小寫成常數：

    1. **有幾種區塊受 `BLOCK_VERSION` 管**：由 `review.py` 的 AST 導出
       （`_block_version_sites`），⛔ 不手打、⛔ 不寫死數目。今天是三種；日後多一種
       而沒有人來補語料，`_CORPUS_FACTORIES` 的鍵集合比對就會紅。
    2. **每一種區塊的事件長什麼樣**：由**產線 renderer 本人**在跑的當下渲染
       （`_CORPUS_FACTORIES`），⛔ 不手打 YAML。渲染時把 `BLOCK_VERSION` 暫時換成
       `_FROZEN_BLOCK_VERSION_IN_WRITTEN_EVENTS`，也就是**模擬「當年寫下這些事件時
       常數是什麼」**——既有留言不可變，它們的版本字面就是停在那個值。

    **為什麼不釘數字。** 活看板上的事件則數每天都在變（每一輪查核就多一則），把
    「111 則」這種當日快照寫進斷言，只會讓這條測試在某個與 `BLOCK_VERSION` 完全無關
    的日子紅掉，然後被人調大——那是把偵測器訓練成雜訊。**這條測試斷言的是關係，不是
    規模**：不論母體是 1 則還是 10,000 則，「現況全數讀得回」與「換掉常數後一則都讀
    不回」這兩條關係都必須同時成立；母體為空時第三條斷言會硬紅，⛔ 不讓前兩條變成
    空真。

    ## ⛔ 這條測試不涵蓋什麼

    * ⛔ **不驗**既有事件的**內容**正確性（那是 `aiwf#138` 的射程）——它只驗
      「版本不符時讀不回」。
    * ⛔ **不驗**升版之後的遷移路徑：本 repo 今日**沒有** v2 實作，本節也不提供。
    * ⛔ **不驗** `_CORPUS_FACTORIES` 以外的讀取端；涵蓋面恰好等於 AST 導出的那幾處。
    * ⛔ 綠燈**不得**被讀成「相容性已保證」。它只說：今天這幾處讀取端與這些語料在
      同一個版本上；⛔ 沒有任何東西保證別台機器上的那份 `wfcli` 也在同一版。
    """
    readers, writers = _block_version_sites()
    assert set(readers) == set(writers), (
        f"讀取端區塊鍵 {sorted(readers)} 與寫入端 {sorted(writers)} 不相等 ⇒ 有一種區塊"
        "只讀不寫或只寫不讀，本節建不出它的語料，fail closed"
    )
    assert set(readers) == set(_CORPUS_FACTORIES), (
        f"AST 導出的區塊鍵 {sorted(readers)} 與語料工廠 {sorted(_CORPUS_FACTORIES)} 不相等。"
        "⇒ 若你剛新增了一種受 BLOCK_VERSION 管的區塊，請來 _CORPUS_FACTORIES 補上它的"
        "語料工廠；⛔ 不要把這條比對刪掉——它就是「不得把種數寫死」的那個機械執行者"
    )

    # 語料在「當年的常數」下渲染：模擬不可變的既有事件。
    with _block_version_is(_FROZEN_BLOCK_VERSION_IN_WRITTEN_EVENTS):
        corpus = {key: factory() for key, factory in _CORPUS_FACTORIES.items()}

    total = sum(len(bodies) for bodies in corpus.values())
    assert total > 0, "語料母體為空 ⇒ 下面兩條關係都會是空真，fail closed"
    for key, bodies in corpus.items():
        assert bodies, f"區塊 {key!r} 的語料為空 ⇒ 它那一處比較不在射程內，fail closed"

    # 關係一：現況下每一則既有事件都讀得回。
    unreadable = [
        (key, body)
        for key, bodies in corpus.items()
        for body in bodies
        if not _readable(getattr(review_mod, readers[key][1]), body)
    ]
    assert not unreadable, (
        f"{len(unreadable)}/{total} 則既有形狀的事件讀不回了。\n"
        f"⇒ 若你剛把 review.BLOCK_VERSION 由 "
        f"{_FROZEN_BLOCK_VERSION_IN_WRITTEN_EVENTS!r} 改成 {review_mod.BLOCK_VERSION!r}："
        "**既有事件不會跟著升版**。它們是不可變留言，版本字面停在寫入當下；升版後"
        "每一則都會被讀成「讀不懂」，而閘門把讀不懂當 fail-closed ⇒ 整批卡停機。\n"
        "⇒ 正解是先落地一個同時認舊版與新版的讀取端（⛔ 本節不指名由誰做），⛔ 不是把本節的"
        "黃金值一起改大——那只是把偵測器關掉。\n"
        f"讀不回的區塊：{sorted({key for key, _ in unreadable})}"
    )

    # 關係二：把常數換成別的值之後，一則都讀不回。
    with _block_version_is(_PROBE_BLOCK_VERSION):
        still_readable = [
            (key, readers[key][2])
            for key, bodies in corpus.items()
            for body in bodies
            if _readable(getattr(review_mod, readers[key][1]), body)
        ]
    assert not still_readable, (
        f"換掉 BLOCK_VERSION 之後仍有 {len(still_readable)}/{total} 則讀得回："
        f"{sorted(set(still_readable))}\n"
        "⇒ 那條讀取路徑**沒有走版本檢查**（比較被移除或被繞過）。這正是本節的負控："
        "它紅代表守衛不在，⛔ 不是語料壞了"
    )


# ---------------------------------------------------------------------------
# 活看板那一條：讓「連黃金值一起改大」這個關法也會紅
# ---------------------------------------------------------------------------
#
# ⚠️ 上面那條測試有一個明確的關法：把 `BLOCK_VERSION` 與
# `_FROZEN_BLOCK_VERSION_IN_WRITTEN_EVENTS` **一起**改大，它就回綠——而真實看板上
# 那批不可變事件仍然讀不回。⛔ 純離線的檢查對這個關法**無能為力**：既有事件在 repo
# 之外，樹裡沒有任何東西知道它們的版本字面。
#
# 這條測試就是那個缺口的處置：**在跑的當下**把活看板上的既有事件抓下來，斷言它們
# 仍然全數讀得回、且其版本字面仍等於上面那個黃金值。
#
# ⚠️ **它是盡力而為的，⛔ 不是不變式**：抓不到（離線、逾時、被匿名額度擋下）就
# `skip`，⛔ 不 fail——否則 GitHub 打噴嚏就會讓 CI 紅，而「紅得沒道理」訓練出來的
# 是「紅了先重跑」。⇒ 涵蓋宣稱逐字收窄為：**上面那條是不變式，這一條是偵測器。**

#: 只在 CI 或明確 opt-in 時打網路。理由：本地 `pytest` 一天要跑幾十次，匿名額度是
#: 每小時 60 次／每個 IP，而本檢查一次要用掉數次 ⇒ 掛在每次本地跑上會把額度燒光，
#: 且讓一套原本不連網的測試變成連網的。CI 是它該跑的地方（GitHub Actions 恆設 `CI`）。
_LIVE_BOARD_OPT_IN = "WF_LIVE_BOARD_CORPUS"


def _origin_repo_slug() -> str | None:
    """本 repo 在 GitHub 上的 `owner/name`。⛔ 不寫死字面。"""
    slug = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if slug:
        return slug
    try:
        url = subprocess.run(
            ["git", "-C", str(Path(review_mod.__file__).resolve().parent), "remote", "get-url", "origin"],
            capture_output=True, text=True, check=True, timeout=30,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?$", url)
    return match.group(1) if match else None


#: 看板橫跨的 repo，**明文列舉**。
#:
#: ⚠️ 這個集合**導不出來**：卡分佈在哪些 repo 是治理事實，樹裡沒有任何檔案記載它
#: （`origin` 只知道自己）。曾經只取 `origin`，於是另一個 repo 上的同型不可變事件
#: 整批不在母體內——離線層**替代不了**它們，因為那些事件在 repo 之外。
#:
#: ⛔ **這不是母體大小。** 母體是每個 repo 上真正抓到的事件則數，那個數字仍然不進
#: 任何斷言（見上方測試 docstring 的漂移聲明）。這裡列的是「要去哪裡取」。
#: ⇒ 新增 repo 時來這裡加一行；⛔ 不要改回只看 `origin`。
_LISTED_BOARD_REPOS: tuple[str, ...] = (
    "ruan6047/ai-workflow",
    "ruan6047/cpbl-analytics",
)


def _board_repos() -> tuple[str, ...]:
    """要取語料的 repo 清單 ＝ 明文列舉 ∪ 機械導出的 `origin`（去重、保序）。

    取聯集而不是二選一：明文那份可能忘了加，`origin` 那份可能不在明文裡，
    兩邊都納入的方向只會讓母體變大，⛔ 不會讓它靜默變小。
    """
    origin = _origin_repo_slug()
    return tuple(dict.fromkeys([*_LISTED_BOARD_REPOS, *([origin] if origin else [])]))


def _fetch_issue_comments(slug: str) -> list[dict]:
    """抓 repo 的全部 issue 留言（匿名 REST；這些 repo 為 public）。"""
    out: list[dict] = []
    for page in range(1, 51):
        request = urllib.request.Request(
            f"https://api.github.com/repos/{slug}/issues/comments?per_page=100&page={page}",
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "wf-cli-tests/block-version-regression",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = jsonlib.loads(response.read().decode("utf-8"))
        out.extend(batch)
        if len(batch) < 100:
            break
    return out


def test_the_live_board_events_still_carry_the_frozen_block_version():
    """活看板上的既有事件，其版本字面仍等於本檔凍結的黃金值。

    ## 母體怎麼來（⛔ 同樣不釘數字）

    母體 ＝ **跑的當下**自 `_board_repos()` 的每一個 repo 的 issue 留言裡導出的
    「帶事件 marker 前綴、且含 `wf_escalation_facts` 區塊」那一批。前綴取 `doctor`
    的產線常數，⛔ 不手打；則數每天都在變（同一個 repo 一個晚上就從 62 變成 64），
    ⛔ 不進斷言，只在失敗訊息裡當**當次紀錄**印出來。**斷言的是關係不是規模**：
    全數讀得回、版本字面全等於黃金值、換掉常數後一則都讀不回、母體非空。

    ## ⚠️ 部分可達時的行為：以抓得到的那些做斷言，⛔ 不整條放掉

    匿名額度是 60 次/小時/IP 而 runner IP 共用 ⇒ 「一個 repo 抓得到、另一個被擋」
    是會發生的。此時**仍對抓得到的那些斷言**，並把抓不到的那些以 `UserWarning`
    ＋ stdout 逐字標明（pytest 的 warnings summary 在 `-q` 下仍會印）。
    ⛔ 只有**全部**都抓不到才 skip——那時沒有任何母體可斷言。

    ## ⛔ 這條測試不涵蓋什麼

    * ⛔ 抓不到就 skip，所以它是**偵測器**不是不變式；⛔ 綠燈不得被讀成「已保證」。
    * ⛔ 只看 `wf_escalation_facts`：另兩種區塊今天在看板上分別是 0 則與極少數，
      涵蓋由上面那條離線測試承擔。
    * ⛔ 只看 `_board_repos()` 列到的 repo。沒列到的 repo 上的事件不在母體內，而
      本測試**看不出**有沒有漏列——那是治理事實，⛔ 不是它判得出來的東西。
    """
    if not (os.environ.get("CI") or os.environ.get(_LIVE_BOARD_OPT_IN)):
        pytest.skip(f"未設 CI 或 {_LIVE_BOARD_OPT_IN}：本地預設不打網路（見上方說明）")
    repos = _board_repos()
    assert repos, "導不出任何 repo ⇒ 沒有母體可取，fail closed"

    from wf_cli.doctor import _EVENT_PREFIX  # 產線常數，⛔ 不手打前綴字面

    fetched: dict[str, int] = {}
    unreachable: list[tuple[str, str]] = []
    corpus: list[tuple[str, str, str, dict]] = []   # (repo, url, body, block)
    for slug in repos:
        try:
            comments = _fetch_issue_comments(slug)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            unreachable.append((slug, f"{type(exc).__name__}: {exc}"))
            continue
        fetched[slug] = len(comments)
        for comment in comments:
            body = comment.get("body") or ""
            if _EVENT_PREFIX not in body:
                continue
            try:
                block = find_block_by_key(body, FACTS_BLOCK_KEY)
            except ReviewParseError as exc:
                url = comment.get("html_url") or "（無 URL）"
                raise AssertionError(
                    f"{slug} 的既有事件 {url} 含 {FACTS_BLOCK_KEY} 區塊卻無法解析 ⇒ "
                    "它不能被排出母體；既有事件讀不懂時必須 fail closed"
                ) from exc
            if block is not None:
                corpus.append((slug, comment.get("html_url") or "", body, block))

    if unreachable:
        # ⛔ 不 skip、⛔ 不 fail：以抓得到的那些斷言，但被略過的那些必須看得見。
        notice = "⚠️ 本輪未取到、其事件⛔不在母體內的 repo：" + "；".join(
            f"{slug}（{reason}）" for slug, reason in unreachable
        ) + f"　｜　本輪實際取到並斷言的 repo：{sorted(fetched) or '（無）'}"
        warnings.warn(notice, stacklevel=1)
        print(notice)

    if not fetched:
        pytest.skip(
            "全部 repo 都取不到 ⇒ 沒有任何母體可斷言，偵測器本輪不跑："
            + "；".join(f"{slug}（{reason}）" for slug, reason in unreachable)
        )

    per_repo = collections.Counter(slug for slug, _, _, _ in corpus)
    assert corpus, (
        f"取到了 {sorted(fetched)} 卻導不出任何一則含 {FACTS_BLOCK_KEY} 區塊的事件 ⇒ 母體為空，"
        f"下面的斷言會變成空真，fail closed。（當次紀錄：留言則數 {dict(fetched)}）"
    )
    empty = [slug for slug in fetched if per_repo[slug] == 0]
    assert not empty, (
        f"這些 repo 取到了留言卻一則事件都導不出來：{empty}（當次紀錄：留言則數 "
        f"{dict(fetched)}、事件則數 {dict(per_repo)}）\n"
        "⇒ 母體**靜默變小**了：可能是該 repo 的事件形態改了，也可能是它本來就不該在"
        f"清單裡。⛔ 不要直接把它從 {_LISTED_BOARD_REPOS!r} 刪掉了事，先判是哪一種"
    )

    drifted = [
        (url, str(block.get(FACTS_BLOCK_KEY)).strip())
        for _, url, _, block in corpus
        if str(block.get(FACTS_BLOCK_KEY)).strip() != _FROZEN_BLOCK_VERSION_IN_WRITTEN_EVENTS
    ]
    assert not drifted, (
        f"{len(drifted)}/{len(corpus)} 則既有事件的版本字面不等於本檔凍結的 "
        f"{_FROZEN_BLOCK_VERSION_IN_WRITTEN_EVENTS!r}：{drifted[:5]}\n"
        "⇒ 若你剛把 BLOCK_VERSION 與本檔黃金值「一起」改大：那批舊事件沒有跟著改，"
        "現在它們讀不回了。⛔ 這條比對就是為了讓那個關法紅在這裡\n"
        f"（當次紀錄：逐 repo 事件則數 {dict(per_repo)}）"
    )

    unreadable = [url for _, url, body, _ in corpus if not review_mod.escalation_facts_from_body(body)]
    assert not unreadable, (
        f"{len(unreadable)}/{len(corpus)} 則既有事件讀不回：{unreadable[:5]}"
        f"（當次紀錄：逐 repo 事件則數 {dict(per_repo)}）"
    )

    with _block_version_is(_PROBE_BLOCK_VERSION):
        still = [url for _, url, body, _ in corpus if review_mod.escalation_facts_from_body(body)]
    assert not still, (
        f"換掉 BLOCK_VERSION 之後仍有 {len(still)}/{len(corpus)} 則既有事件讀得回："
        f"{still[:5]} ⇒ 有一條讀取路徑沒有走版本檢查"
    )


def test_live_board_detector_rejects_malformed_facts_alongside_a_valid_event(monkeypatch):
    """一筆正常事件不得掩蓋同 repo 另一筆讀不懂的 facts 區塊。"""
    from wf_cli.doctor import _EVENT_PREFIX

    valid = _EVENT_PREFIX + "\n" + _facts_block_bodies()[0]
    malformed = "\n".join(
        [
            _EVENT_PREFIX,
            "```yaml",
            f"{FACTS_BLOCK_KEY}: {review_mod.BLOCK_VERSION}",
            f"{FACTS_BLOCK_KEY}: {review_mod.BLOCK_VERSION}",
            "```",
        ]
    )
    comments = [
        {"html_url": "https://example.invalid/valid", "body": valid},
        {"html_url": "https://example.invalid/malformed", "body": malformed},
    ]
    monkeypatch.setenv(_LIVE_BOARD_OPT_IN, "1")
    module = sys.modules[__name__]
    monkeypatch.setattr(module, "_board_repos", lambda: ("example/board",))
    monkeypatch.setattr(module, "_fetch_issue_comments", lambda slug: comments)

    with pytest.raises(AssertionError, match="example.invalid/malformed"):
        test_the_live_board_events_still_carry_the_frozen_block_version()
