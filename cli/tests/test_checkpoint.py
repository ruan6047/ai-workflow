"""``wfcli checkpoint`` 與 ``wfcli contract-baseline`` 的寫入行為與 fail-closed 閘門。

全部走 ``EventGhRunner``（純記憶體），**不碰任何真實卡片**。
"""

from __future__ import annotations

import json as jsonlib

import pytest

from wf_cli.cli import build_parser
from wf_cli.commands import checkpoint_cmd, handoff_cmd, open_cmd, review_cmd
from wf_cli.project import find_item_by_card_id, list_items, resolve_project
from wf_cli.review import (
    BASELINE_LOG_TAG,
    CHECKPOINT_LOG_TAG,
    PreflightBasis,
    render_verdict_comment,
)
from wf_cli.validation import validate_review_report

from .fake_gh import FakeGhRunner, _parse_flags

BASE_TARGET = ["--owner", "acme", "--project", "1"]
REPO = "acme/demo"


class EventGhRunner(FakeGhRunner):
    """``FakeGhRunner`` ＋ 事件平面：留言唯讀讀回、每則留言有自己的 URL、``gh api user``。

    ``fake_gh.py`` 不在 WF-22-CLI4 宣告的寫入集內，故這三條路徑在測試側以子類補上，
    而不是改共用替身。
    """

    def __init__(self) -> None:
        super().__init__()
        self.login = "ruan6047"
        self._comment_seq = 0
        self.comment_records: dict[str, list[dict[str, str]]] = {}

    def execute(self, args, input: str | None = None) -> str:  # type: ignore[override]
        args = list(args)
        flags = _parse_flags(args)

        if args[:2] == ["api", "user"]:
            return self.login + "\n"

        if args[:2] == ["issue", "view"] and "--json" in flags:
            url = f"https://github.com/{flags['--repo']}/issues/{int(args[2])}"
            return jsonlib.dumps({"comments": self.comment_records.get(url, [])})

        if args[:2] == ["issue", "comment"]:
            repo, number = flags["--repo"], int(args[2])
            url = f"https://github.com/{repo}/issues/{number}"
            if url not in self.issues:
                raise AssertionError(f"EventGhRunner: 對不存在的 issue 留言 {url}")
            self._comment_seq += 1
            comment_url = f"{url}#issuecomment-{self._comment_seq}"
            self.issues[url].setdefault("comments", []).append(flags["--body"])
            self.comment_records.setdefault(url, []).append(
                {"body": flags["--body"], "url": comment_url, "author": {"login": self.login}}
            )
            return comment_url + "\n"

        return super().execute(args, input)


# --------------------------------------------------------------------------
# 模擬「承接卡落地後的世界」（WF-22-CLI4-R4-01）
# --------------------------------------------------------------------------
#
# 本 repo 今天沒有受管轄的 preflight pass event writer，也沒有該事件的可驗證格式，
# 故 `validation.require_preflight_basis` **無條件拋出**，`wfcli review` 寫不進任何裁決。
# 端對端測「承接卡落地後」的行為，唯一的辦法是**把那個閘門換掉**——這件事本身就是本輪的
# 核心事實：沒有任何 Issue 留言、旗標或輸入能解鎖它（窮舉見 test_validation 的
# `test_no_issue_comment_of_any_shape_can_establish_a_preflight_basis`），只有改碼可以。
#
# 上一輪這裡是 `arm_preflight()` 往 timeline 貼一則四欄 YAML 留言——那正是查核者用來
# 重現 R4-01 的同一件事。它現在改成純測試側的登記表，src 不再有對應的讀取器。
_SIMULATED_PREFLIGHT: set[tuple[str, str]] = set()


def event_verified(card_id: str, sha: str) -> PreflightBasis:
    """承接卡落地後、該卡該 SHA 的合格依據。**本 CLI 今天產不出它**（見上方說明）。"""
    return PreflightBasis(
        basis="event-verified",
        source_event=f"https://github.com/{REPO}/issues/1#issuecomment-999",
        summary="（模擬）分支已推、工作區乾淨、pytest 全綠、trailer 已檢查",
    )


def arm_preflight(card_id: str, sha: str) -> None:
    """登記「承接卡已為該卡該 SHA 寫出 preflight event」。只影響被換掉的閘門。"""
    _SIMULATED_PREFLIGHT.add((card_id, sha))


def _simulated_require_preflight_basis(*, card_id: str, source_sha: str) -> PreflightBasis:
    if (card_id, source_sha) in _SIMULATED_PREFLIGHT:
        return event_verified(card_id, source_sha)
    # 未登記時的行為必須與 src 的真實閘門一致：拒絕，而不是回一個 not-established
    # 讓下游自己判——真實閘門今天就是恆拋。
    return _real_require_preflight_basis(card_id=card_id, source_sha=source_sha)


_real_require_preflight_basis = review_cmd.require_preflight_basis


@pytest.fixture(autouse=True)
def simulated_preflight_writer(monkeypatch):
    """把 review_cmd 的 preflight 閘門換成「承接卡落地後」的版本（預設登記表為空）。

    autouse 是刻意的：本模組每個端對端寫入測試都需要它，而**沒有登記的卡仍會被真實閘門
    擋下**（見 `_simulated_require_preflight_basis`），所以它不會把 fail-closed 洗掉。
    """
    _SIMULATED_PREFLIGHT.clear()
    monkeypatch.setattr(
        review_cmd, "require_preflight_basis", _simulated_require_preflight_basis
    )
    yield
    _SIMULATED_PREFLIGHT.clear()


@pytest.fixture
def fake_runner(monkeypatch):
    runner = EventGhRunner()
    for module in (open_cmd, handoff_cmd, review_cmd, checkpoint_cmd):
        monkeypatch.setattr(module, "default_runner", runner)
    return runner


def run_cli(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def open_card(card_id: str) -> int:
    return run_cli(
        [
            "open", *BASE_TARGET, "--repo", REPO, card_id,
            "--feature", "示範功能", "--tier", "T2", "--db-scope", "none",
            "--core-pain", "痛點文字", "--service-goal", "服務的原始目標文字",
            "--exec-capability", "主力型", "--exec-capability-reason", "一般實作",
            "--review-capability", "主力型", "--review-capability-reason", "一般 review",
        ]
    )


def card_item(runner: EventGhRunner, card_id: str):
    return find_item_by_card_id(list_items(runner, resolve_project(runner, "acme", 1)), card_id)


def comments_of(runner: EventGhRunner, card_id: str) -> list[str]:
    item = card_item(runner, card_id)
    return runner.issues[item.issue_url].get("comments", [])


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


def write_review(tmp_path, card_id: str, sha: str, fid: str, runner=None, **extra) -> int:
    """跑一次 `wfcli review`；`runner` 有給時先登記該 SHA 的 preflight 依據。"""
    if runner is not None:
        arm_preflight(card_id, sha)
    path = tmp_path / f"{fid}.md"
    path.write_text(COUNTING_REPORT.format(fid=fid), encoding="utf-8")
    argv = [
        "review", *BASE_TARGET, "--repo", REPO, card_id,
        "--input", str(path), "--source-sha", sha, "--reviewer", "Codex",
    ]
    for flag, value in extra.items():
        argv += [f"--{flag.replace('_', '-')}", str(value)]
    return run_cli(argv)


def checkpoint_argv(card_id: str, trigger: str, **overrides) -> list[str]:
    argv = [
        "checkpoint", *BASE_TARGET, "--repo", REPO, card_id,
        "--trigger-attempt-id", trigger,
        "--unique-attempt-count", str(overrides.pop("unique_attempt_count", 3)),
        "--decision", overrides.pop("decision", "escalate"),
        "--rationale", overrides.pop("rationale", "第二條件成立：前輪 finding 未被明列閉合。"),
    ]
    for flag, value in overrides.items():
        argv += [f"--{flag.replace('_', '-')}", str(value)]
    return argv


def inject_counted_attempt(runner: EventGhRunner, card_id: str, sha: str, fid: str) -> str:
    """直接把一則**帶 event-verified 依據**的裁決事件寫進 timeline ＋ Log 索引行。

    模擬承接卡讓 preflight 事件存在之後的世界；回傳 attempt_id。
    """
    report = validate_review_report(
        {
            "review_result": "REQUEST_CHANGES",
            "core_pain_resolved": "yes",
            "self_run": [{"command": "uv run pytest", "observed": "3 failed"}],
            "findings": [
                {
                    "finding_id": fid,
                    "severity": "major",
                    "blocking": "true",
                    "finding_class": "implementation",
                    "attribution": "executor",
                    "root_cause_id": "rc-1",
                    "evidence": "pytest 失敗",
                    "disposition": "修好再送",
                }
            ],
        }
    )
    body = render_verdict_comment(
        card_id=card_id,
        report=report,
        source_sha=sha,
        reviewer="Codex",
        escalation_epoch=0,
        timestamp="2026-08-12T12:00:00+08:00",
        preflight=event_verified(card_id, sha),
    )
    item = card_item(runner, card_id)
    runner.execute(
        ["issue", "comment", str(item.issue_number), "--repo", REPO, "--body", body]
    )
    attempt = f"{card_id}-e0-{sha}"
    new_body = (
        item.body.rstrip("\n")
        + f"\n- 2026-08-12 review by wf-cli → REQUEST_CHANGES；attempt {attempt}。\n"
    )
    runner.execute(["issue", "edit", str(item.issue_number), "--repo", REPO, "--body", new_body])
    return attempt


def seed_three_counted_attempts(fake_runner, tmp_path, card_id: str) -> list[str]:
    """開卡並注入三個**可計數**的 attempt；回傳三個 attempt_id。"""
    open_card(card_id)
    shas = ["a" * 40, "b" * 40, "c" * 40]
    return [
        inject_counted_attempt(fake_runner, card_id, sha, f"{card_id}-R{i}-01")
        for i, sha in enumerate(shas, start=1)
    ]


# --------------------------------------------------------------------------
# 1. checkpoint 寫入
# --------------------------------------------------------------------------


def test_checkpoint_writes_comment_and_log_index_with_comment_url(fake_runner, tmp_path, capsys):
    attempts = seed_three_counted_attempts(fake_runner, tmp_path, "CP-CARD1")
    assert run_cli(checkpoint_argv("CP-CARD1", attempts[2])) == 0

    body = comments_of(fake_runner, "CP-CARD1")[-1]
    assert "wf_escalation_checkpoint: v1" in body
    assert f"trigger_attempt_id: {attempts[2]}" in body
    assert "unique_attempt_count: 3" in body
    assert "checkpoint_decision: escalate" in body
    assert "deferred_findings: []" in body
    # 契約未定義的四個鍵一個都不得出現。
    for forbidden in ("escalation_resolution", "decided_by", "attempts_so_far"):
        assert forbidden not in body
    # 不發 marker（方案 B）。
    assert "wf-review-event" not in body

    card_body = card_item(fake_runner, "CP-CARD1").body
    log_lines = [line for line in card_body.splitlines() if CHECKPOINT_LOG_TAG in line]
    assert len(log_lines) == 1
    assert attempts[2] in log_lines[0]
    assert "#issuecomment-" in log_lines[0]  # Log 行逐字載明該則留言的 URL

    out = capsys.readouterr().out
    assert "未由事件流機械推導" in out  # 不得宣稱有機械推導
    assert "🚨已升級" in out  # decision=escalate 時提醒交付狀態另由 handoff 寫


def test_checkpoint_refuses_when_trigger_verdict_not_recorded(fake_runner, tmp_path, capsys):
    open_card("CP-NOVERDICT1")
    unknown = f"CP-NOVERDICT1-e0-{'d' * 40}"
    assert run_cli(checkpoint_argv("CP-NOVERDICT1", unknown)) == 2
    assert "找不到 attempt" in capsys.readouterr().err
    assert comments_of(fake_runner, "CP-NOVERDICT1") == []


def test_checkpoint_refuses_second_checkpoint_for_same_trigger(fake_runner, tmp_path, capsys):
    attempts = seed_three_counted_attempts(fake_runner, tmp_path, "CP-DUP1")
    assert run_cli(checkpoint_argv("CP-DUP1", attempts[2])) == 0
    before = len(comments_of(fake_runner, "CP-DUP1"))
    assert run_cli(checkpoint_argv("CP-DUP1", attempts[2], decision="continue")) == 2
    assert "已有 checkpoint" in capsys.readouterr().err
    assert len(comments_of(fake_runner, "CP-DUP1")) == before  # 未寫入


def test_checkpoint_rejects_undefined_escalation_resolution_key(fake_runner, tmp_path, capsys):
    attempts = seed_three_counted_attempts(fake_runner, tmp_path, "CP-RESOL1")
    before = len(comments_of(fake_runner, "CP-RESOL1"))
    rc = run_cli(checkpoint_argv("CP-RESOL1", attempts[2], escalation_resolution="continue"))
    assert rc == 2
    err = capsys.readouterr().err
    assert "escalation_resolution" in err
    # ai-workflow#39 否決了「checkpoint 上的獨立欄位」，採獨立事件型別；訊息須指向後者。
    assert "永遠不會是" in err
    assert "escalation-resolution" in err
    assert len(comments_of(fake_runner, "CP-RESOL1")) == before


def test_checkpoint_rejects_deferred_findings_while_both_causes_unavailable(
    fake_runner, tmp_path, capsys
):
    attempts = seed_three_counted_attempts(fake_runner, tmp_path, "CP-DEFER1")
    before = len(comments_of(fake_runner, "CP-DEFER1"))
    rc = run_cli(checkpoint_argv("CP-DEFER1", attempts[2], defer_finding="CP-DEFER1-R1-01"))
    assert rc == 2
    err = capsys.readouterr().err
    assert "deferred_findings" in err and "不可用" in err
    assert len(comments_of(fake_runner, "CP-DEFER1")) == before


@pytest.mark.parametrize(
    "overrides, needle",
    [
        ({"unique_attempt_count": 2}, "unique_attempt_count 必須 >= 3"),
        ({"rationale": "  "}, "checkpoint_rationale 必填"),
        ({"rationale": "帶 ``` 圍籬"}, "圍籬字元"),
    ],
)
def test_checkpoint_field_checks_are_fail_closed(fake_runner, tmp_path, capsys, overrides, needle):
    attempts = seed_three_counted_attempts(fake_runner, tmp_path, "CP-FIELD1")
    before = len(comments_of(fake_runner, "CP-FIELD1"))
    assert run_cli(checkpoint_argv("CP-FIELD1", attempts[2], **overrides)) == 2
    assert needle in capsys.readouterr().err
    assert len(comments_of(fake_runner, "CP-FIELD1")) == before


def test_checkpoint_rejects_trigger_from_another_card_or_epoch(fake_runner, tmp_path, capsys):
    attempts = seed_three_counted_attempts(fake_runner, tmp_path, "CP-XCARD1")
    other = attempts[2].replace("CP-XCARD1", "OTHER-CARD")
    assert run_cli(checkpoint_argv("CP-XCARD1", other)) == 2
    err = capsys.readouterr().err
    assert "與本次 card_id" in err


# --------------------------------------------------------------------------
# 2. contract-baseline（one-shot cutover）
# --------------------------------------------------------------------------


def baseline_argv(card_id: str, rationale: str = "切 cutover：自此 review event 帶 counts 事實") -> list[str]:
    return ["contract-baseline", *BASE_TARGET, "--repo", REPO, card_id, "--rationale", rationale]


def test_contract_baseline_writes_once_and_fails_loud_on_second(fake_runner, capsys):
    open_card("BASE-CARD1")
    assert run_cli(baseline_argv("BASE-CARD1")) == 0
    body = comments_of(fake_runner, "BASE-CARD1")[-1]
    assert "wf_contract_baseline: v1" in body
    assert "one-shot" in body
    card_body = card_item(fake_runner, "BASE-CARD1").body
    assert any(BASELINE_LOG_TAG in line for line in card_body.splitlines())

    before = len(comments_of(fake_runner, "BASE-CARD1"))
    assert run_cli(baseline_argv("BASE-CARD1")) == 2
    assert "one-shot" in capsys.readouterr().err
    assert len(comments_of(fake_runner, "BASE-CARD1")) == before


def test_contract_baseline_moves_unreadable_history_out_of_scope(fake_runner, tmp_path, capsys):
    """baseline 之前的讀不懂留痕依 §5「維持原貌」，不再讓閘門 fail-closed。"""
    open_card("BASE-SCOPE1")
    item = card_item(fake_runner, "BASE-SCOPE1")
    # 一則受管轄但不合格的 marker（派審詞引用前綴的實測形態）。
    fake_runner.execute(
        [
            "issue", "comment", str(item.issue_number), "--repo", REPO,
            "--body", "派審詞：請注意留言不得出現 wf-review-event" + ":v1 的字面。",
        ]
    )
    assert write_review(tmp_path, "BASE-SCOPE1", "a" * 40, "BASE-SCOPE1-R1-01", runner=fake_runner) == 2
    assert "無法自事件流重建" in capsys.readouterr().err

    assert run_cli(baseline_argv("BASE-SCOPE1")) == 0
    assert write_review(tmp_path, "BASE-SCOPE1", "a" * 40, "BASE-SCOPE1-R1-01") == 0  # preflight 已於上方佈署
