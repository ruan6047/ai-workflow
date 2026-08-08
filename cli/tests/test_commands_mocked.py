from __future__ import annotations

import json as jsonlib
import subprocess
from pathlib import Path

import pytest

from wf_cli.cli import build_parser
from wf_cli.commands import assign_cmd, deploy_state_cmd, handoff_cmd, open_cmd, snapshot_cmd
from wf_cli.project import (
    ensure_fields,
    find_item_by_card_id,
    list_items,
    resolve_project,
    set_field_value,
)

from .fake_gh import FakeGhRunner


@pytest.fixture
def fake_runner(monkeypatch):
    runner = FakeGhRunner()
    for module in (open_cmd, assign_cmd, handoff_cmd, snapshot_cmd, deploy_state_cmd):
        monkeypatch.setattr(module, "default_runner", runner)
    return runner


def run_cli(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


BASE_TARGET = ["--owner", "acme", "--project", "1"]


def _open_argv(card_id: str, **overrides) -> list[str]:
    defaults = {
        "--feature": "示範功能",
        "--tier": "T3",
        "--db-scope": "none",
        "--core-pain": "痛點文字",
        "--service-goal": "服務的原始目標文字",
    }
    defaults.update(overrides)
    argv = ["open", *BASE_TARGET, card_id]
    for k, v in defaults.items():
        argv += [k, v]
    return argv


def _deploy_state_argv(card_id: str, target: str, **overrides) -> list[str]:
    defaults = {
        "--repo": "acme/workflow",
        "--to": target,
        "--next-owner": "部署負責人",
        "--actor": "PM 祕書",
        "--evidence": "部署管線已完成對應步驟",
    }
    defaults.update(overrides)
    argv = ["deploy-state", *BASE_TARGET, card_id]
    for key, value in defaults.items():
        if isinstance(value, bool):
            if value:
                argv.append(key)
        else:
            argv += [key, value]
    return argv


def test_open_creates_draft_item_with_all_ledger_fields(fake_runner, capsys):
    rc = run_cli(_open_argv("DEMO-CARD1", **{"--resources": "file:demo.py,port:9000"}))
    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    items = list_items(fake_runner, project)
    assert len(items) == 1
    item = items[0]
    assert item.fields["卡ID"] == "DEMO-CARD1"
    assert item.fields["級別"] == "T3"
    assert item.fields["交付狀態"] == "📥Backlog"
    assert item.fields["部署狀態"] == "—不適用"
    assert "file:demo.py" in item.body
    assert "## 資源宣告" in item.body
    out = capsys.readouterr().out
    assert "已建立卡 DEMO-CARD1" in out


def test_open_rejects_blank_required_fields_even_though_argparse_accepted_them(fake_runner):
    rc = run_cli(_open_argv("DEMO-CARD2", **{"--core-pain": "   "}))
    assert rc == 2


def test_open_argparse_enforces_required_flags_are_present(fake_runner):
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["open", *BASE_TARGET, "DEMO-CARD3", "--feature", "x"])  # 缺 --tier 等必填旗標


def test_open_rejects_duplicate_card_id(fake_runner):
    assert run_cli(_open_argv("DUP-CARD1")) == 0
    assert run_cli(_open_argv("DUP-CARD1")) == 3


def test_open_writes_git_spec_file_skeleton(fake_runner, tmp_path: Path):
    spec_dir = tmp_path / "tasks"
    rc = run_cli(_open_argv("SPEC-CARD1", **{"--spec-dir": str(spec_dir)}))
    assert rc == 0
    spec_file = spec_dir / "SPEC-CARD1.md"
    assert spec_file.exists()
    text = spec_file.read_text(encoding="utf-8")
    assert "# SPEC-CARD1" in text
    assert "## 核心痛點" in text


def test_open_writes_chain_depth_zero_by_default(fake_runner):
    rc = run_cli(_open_argv("CHAINDEPTH-CARD1"))
    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["鏈深"] == 0


@pytest.mark.parametrize("depth", [0, 1, 2])
def test_open_writes_chain_depth_within_hard_cap(fake_runner, depth):
    rc = run_cli(_open_argv(f"CHAINDEPTH-CARD-OK{depth}", **{"--chain-depth": str(depth)}))
    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["鏈深"] == depth


def test_open_rejects_chain_depth_over_hard_cap(fake_runner, capsys):
    rc = run_cli(_open_argv("CHAINDEPTH-CARD-BAD", **{"--chain-depth": "3"}))
    assert rc == 2
    err = capsys.readouterr().err
    # 拒絕訊息須引用決議 5 鏈式停損協定，不能只是泛用「驗證失敗」字串。
    assert "決議 5" in err
    assert "整鏈重審" in err
    project = resolve_project(fake_runner, "acme", 1)
    assert find_item_by_card_id(list_items(fake_runner, project), "CHAINDEPTH-CARD-BAD") is None


def _assign_argv(card_id: str, assignee: str, branch: str, worktree: str) -> list[str]:
    return [
        "assign", *BASE_TARGET, card_id,
        "--assignee", assignee, "--branch", branch, "--worktree", worktree,
    ]


def test_assign_writes_owner_and_branch_worktree(fake_runner):
    run_cli(_open_argv("ASSIGN-CARD1"))
    rc = run_cli(_assign_argv("ASSIGN-CARD1", "Claude Sonnet 5@Claude Code", "ai/agent/ASSIGN-CARD1", ".claude/worktrees/assign-card1"))
    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["owner"] == "Claude Sonnet 5@Claude Code"
    assert item.fields["分支worktree"] == "ai/agent/ASSIGN-CARD1 @ .claude/worktrees/assign-card1"
    assert item.fields["交付狀態"] == "🚧進行中"
    assert "assign by wf-cli" in item.body


def test_assign_does_not_block_on_unassigned_backlog_sibling_with_same_resource(fake_runner):
    # 兩張卡都宣告同一檔案，但都還沒被 assign 過（單純躺在 Backlog）——
    # 此時沒有任何「執行中」的卡在爭這個資源，assign 第一張不該被擋。
    run_cli(_open_argv("CONFLICT-A", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    run_cli(_open_argv("CONFLICT-B", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    rc = run_cli(_assign_argv("CONFLICT-A", "someone", "ai/agent/CONFLICT-A", ".claude/worktrees/a"))
    assert rc == 0


def test_assign_rejects_on_resource_conflict_with_already_assigned_card(fake_runner):
    # CONFLICT-A 先被指派（進入「執行中」），CONFLICT-B 才嘗試指派到同一資源 → 應拒絕。
    run_cli(_open_argv("CONFLICT-A", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    run_cli(_open_argv("CONFLICT-B", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    rc1 = run_cli(_assign_argv("CONFLICT-A", "someone", "ai/agent/CONFLICT-A", ".claude/worktrees/a"))
    assert rc1 == 0
    rc2 = run_cli(_assign_argv("CONFLICT-B", "someone-else", "ai/agent/CONFLICT-B", ".claude/worktrees/b"))
    assert rc2 == 4  # 撞卡拒絕


def test_assign_allowed_when_conflicting_card_is_terminal(fake_runner):
    run_cli(_open_argv("TERMINAL-A", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    run_cli(_open_argv("TERMINAL-B", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    project = resolve_project(fake_runner, "acme", 1)
    fields = ensure_fields(fake_runner, "acme", 1)
    item_a = next(i for i in list_items(fake_runner, project) if i.fields.get("卡ID") == "TERMINAL-A")
    set_field_value(fake_runner, project, item_a.item_id, fields["交付狀態"], "🏁完成")

    rc = run_cli(_assign_argv("TERMINAL-B", "someone", "ai/agent/TERMINAL-B", ".claude/worktrees/b"))
    assert rc == 0  # TERMINAL-A 已完成，資源釋放，不再視為衝突


def _handoff_argv(card_id: str, sha: str, **overrides) -> list[str]:
    defaults = {
        "--to": "查核者",
        "--next-stage": "review",
        "--source-sha": sha,
        "--evidence": "pytest 全綠",
    }
    defaults.update(overrides)
    argv = ["handoff", *BASE_TARGET, card_id]
    for k, v in defaults.items():
        argv += [k, v]
    return argv


def test_handoff_rejects_invalid_sha(fake_runner):
    run_cli(_open_argv("HANDOFF-CARD1"))
    rc = run_cli(_handoff_argv("HANDOFF-CARD1", "not-a-sha"))
    assert rc == 2


def test_handoff_rejects_empty_evidence(fake_runner):
    run_cli(_open_argv("HANDOFF-CARD2"))
    rc = run_cli(_handoff_argv("HANDOFF-CARD2", "a" * 40, **{"--evidence": "   "}))
    assert rc == 2


def test_handoff_updates_owner_status_and_last_handoff(fake_runner):
    run_cli(_open_argv("HANDOFF-CARD3"))
    sha = "b" * 40
    rc = run_cli(_handoff_argv("HANDOFF-CARD3", sha))
    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["owner"] == "查核者"
    assert item.fields["交付狀態"] == "🔍待查核"
    assert "T" in item.fields["最後交接"]
    assert f"SHA {sha}" in item.body
    assert "證據 pytest 全綠" in item.body


def test_handoff_next_stage_implementation_auto_increments_iteration(fake_runner):
    # --next-stage implementation 承載「查核退回」語意：讀回現值 +1 寫回，
    # 連續兩次退回應累加而非固定寫 1。
    run_cli(_open_argv("ITER-CARD1"))
    project = resolve_project(fake_runner, "acme", 1)

    rc1 = run_cli(
        _handoff_argv("ITER-CARD1", "1" * 40, **{"--next-stage": "implementation"})
    )
    assert rc1 == 0
    item = list_items(fake_runner, project)[0]
    assert item.fields["iteration"] == 1
    assert "iteration 1" in item.body

    rc2 = run_cli(
        _handoff_argv("ITER-CARD1", "2" * 40, **{"--next-stage": "implementation"})
    )
    assert rc2 == 0
    item = list_items(fake_runner, project)[0]
    assert item.fields["iteration"] == 2
    assert "iteration 2" in item.body


def test_handoff_next_stage_review_does_not_increment_iteration(fake_runner):
    run_cli(_open_argv("ITER-CARD2"))
    rc = run_cli(_handoff_argv("ITER-CARD2", "3" * 40))  # 預設 --next-stage review
    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["iteration"] == 0


def test_handoff_next_stage_release_does_not_increment_iteration(fake_runner):
    run_cli(_open_argv("ITER-CARD3"))  # 預設部署狀態 —不適用，release 不受部署閘門阻擋
    rc = run_cli(_handoff_argv("ITER-CARD3", "4" * 40, **{"--next-stage": "release"}))
    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["iteration"] == 0


def test_handoff_iteration_override_sets_exact_value_and_warns(fake_runner, capsys):
    run_cli(_open_argv("ITER-CARD4"))
    rc = run_cli(_handoff_argv("ITER-CARD4", "5" * 40, **{"--iteration": "7"}))
    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["iteration"] == 7  # 顯式覆寫值，不是 current(0)+1
    err = capsys.readouterr().err
    assert "警示" in err
    assert "iteration" in err


def test_handoff_iteration_override_takes_precedence_over_auto_increment(fake_runner):
    # --iteration 覆寫與 --next-stage implementation 同時給時，覆寫值本身勝出，
    # 不會先自動 +1 再覆寫、也不會覆寫後再額外 +1。
    run_cli(_open_argv("ITER-CARD5"))
    rc = run_cli(
        _handoff_argv(
            "ITER-CARD5",
            "6" * 40,
            **{"--next-stage": "implementation", "--iteration": "10"},
        )
    )
    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["iteration"] == 10


def test_open_needs_deploy_flag_sets_initial_deployment_status(fake_runner):
    argv = _open_argv("DEPLOY-FLAG-CARD1")
    argv.append("--needs-deploy")
    assert run_cli(argv) == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["部署狀態"] == "⏸未部署"


def test_deploy_state_advances_one_legal_step_updates_builtin_status_and_issue_timeline(fake_runner):
    open_argv = _open_argv("DEPLOY-STATE-CARD1", **{"--repo": "acme/workflow"})
    open_argv.append("--needs-deploy")
    run_cli(open_argv)
    fake_runner.add_builtin_status("acme", 1, ["Todo", "In Progress", "Done"])

    rc = run_cli(_deploy_state_argv("DEPLOY-STATE-CARD1", "🚀待部署"))

    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["部署狀態"] == "🚀待部署"
    assert item.fields["Status"] == "Todo"
    assert item.fields["owner"] == "部署負責人"
    assert "T" in item.fields["最後交接"]
    assert fake_runner.issues[item.issue_url]["comments"][-1].startswith("## deployment-state")
    assert "⏸未部署 → 🚀待部署" in fake_runner.issues[item.issue_url]["comments"][-1]
    assert "card_id: DEPLOY-STATE-CARD1" in fake_runner.issues[item.issue_url]["comments"][-1]
    assert "actor: PM 祕書" in fake_runner.issues[item.issue_url]["comments"][-1]
    assert "evidence: 部署管線已完成對應步驟" in fake_runner.issues[item.issue_url]["comments"][-1]
    assert any("updateProjectV2ItemFieldValue" in query for query in fake_runner.graphql_calls)
    assert not any("updateProjectV2Field" in query for query in fake_runner.graphql_calls)


def test_deploy_state_maps_every_legal_step_to_the_expected_builtin_status(fake_runner):
    open_argv = _open_argv("DEPLOY-STATE-CARD-MAPPING", **{"--repo": "acme/workflow"})
    open_argv.append("--needs-deploy")
    run_cli(open_argv)
    fake_runner.add_builtin_status("acme", 1, ["Todo", "In Progress", "Done"])
    project = resolve_project(fake_runner, "acme", 1)

    for deployment_status, expected_project_status in (
        ("🚀待部署", "Todo"),
        ("⏳部署中", "In Progress"),
        ("✅已部署", "In Progress"),
        ("🧪驗證中", "In Progress"),
        ("✅已驗證", "Done"),
    ):
        assert run_cli(_deploy_state_argv("DEPLOY-STATE-CARD-MAPPING", deployment_status)) == 0
        item = list_items(fake_runner, project)[0]
        assert item.fields["部署狀態"] == deployment_status
        assert item.fields["Status"] == expected_project_status


def test_deploy_state_rejects_illegal_jump_without_timeline_or_item_mutation(fake_runner):
    open_argv = _open_argv("DEPLOY-STATE-CARD2", **{"--repo": "acme/workflow"})
    open_argv.append("--needs-deploy")
    run_cli(open_argv)
    fake_runner.add_builtin_status("acme", 1, ["Todo", "In Progress", "Done"])
    project = resolve_project(fake_runner, "acme", 1)
    item_before = list_items(fake_runner, project)[0]

    rc = run_cli(_deploy_state_argv("DEPLOY-STATE-CARD2", "✅已部署"))

    assert rc == 4
    item_after = list_items(fake_runner, project)[0]
    assert item_after.fields == item_before.fields
    assert fake_runner.issues[item_after.issue_url].get("comments") is None
    assert not any("mutation" in query for query in fake_runner.graphql_calls)


def test_deploy_state_cannot_reclassify_not_applicable_card_as_deployable(fake_runner):
    run_cli(_open_argv("DEPLOY-STATE-CARD-NOT-APPLICABLE", **{"--repo": "acme/workflow"}))
    fake_runner.add_builtin_status("acme", 1, ["Todo", "In Progress", "Done"])
    project = resolve_project(fake_runner, "acme", 1)

    rc = run_cli(_deploy_state_argv("DEPLOY-STATE-CARD-NOT-APPLICABLE", "🚀待部署"))

    assert rc == 4
    item = list_items(fake_runner, project)[0]
    assert item.fields["部署狀態"] == "—不適用"
    assert fake_runner.issues[item.issue_url].get("comments") is None
    assert not any("mutation" in query for query in fake_runner.graphql_calls)


def test_deploy_state_dry_run_validates_but_does_not_write(fake_runner, capsys):
    open_argv = _open_argv("DEPLOY-STATE-CARD3", **{"--repo": "acme/workflow"})
    open_argv.append("--needs-deploy")
    run_cli(open_argv)
    fake_runner.add_builtin_status("acme", 1, ["Todo", "In Progress", "Done"])

    rc = run_cli(_deploy_state_argv("DEPLOY-STATE-CARD3", "🚀待部署", **{"--dry-run": True}))

    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["部署狀態"] == "⏸未部署"
    assert fake_runner.issues[item.issue_url].get("comments") is None
    assert not any("mutation" in query for query in fake_runner.graphql_calls)
    assert "dry-run" in capsys.readouterr().out


def test_handoff_release_blocked_when_deploy_not_verified(fake_runner):
    argv = _open_argv("RELEASE-CARD1")
    argv.append("--needs-deploy")  # 部署狀態初始為 ⏸未部署，尚未 ✅已驗證
    run_cli(argv)

    rc = run_cli(_handoff_argv("RELEASE-CARD1", "c" * 40, **{"--next-stage": "release"}))
    assert rc == 4


def test_handoff_release_allowed_once_deployment_verified(fake_runner):
    # deployment_status 的後續轉移（🚀待部署→…→✅已驗證）不在本 CLI 五指令範圍內
    # （由各專案自己的部署管線／DEPLOYMENT.md 負責），這裡直接寫欄位模擬「已完成
    # 部署驗證」的前提，只驗證 handoff release 閘門本身在此前提下確實放行。
    argv = _open_argv("RELEASE-CARD1B")
    argv.append("--needs-deploy")
    run_cli(argv)
    project = resolve_project(fake_runner, "acme", 1)
    fields = ensure_fields(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    set_field_value(fake_runner, project, item.item_id, fields["部署狀態"], "✅已驗證")

    rc = run_cli(_handoff_argv("RELEASE-CARD1B", "c" * 40, **{"--next-stage": "release"}))
    assert rc == 0


def test_handoff_release_allowed_when_no_deploy_needed(fake_runner):
    run_cli(_open_argv("RELEASE-CARD2"))  # 預設部署狀態 —不適用
    rc = run_cli(_handoff_argv("RELEASE-CARD2", "d" * 40, **{"--next-stage": "release"}))
    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["交付狀態"] == "🏁完成"


def test_handoff_repo_path_verifies_sha_exists(fake_runner, sandbox_repo):
    run_cli(_open_argv("HANDOFF-SHA-CHECK1"))
    real_sha = subprocess.run(
        ["git", "-C", str(sandbox_repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    rc_ok = run_cli(
        _handoff_argv("HANDOFF-SHA-CHECK1", real_sha, **{"--repo-path": str(sandbox_repo)})
    )
    assert rc_ok == 0

    run_cli(_open_argv("HANDOFF-SHA-CHECK2"))
    fake_but_well_formed_sha = "f" * 40
    rc_fail = run_cli(
        _handoff_argv("HANDOFF-SHA-CHECK2", fake_but_well_formed_sha, **{"--repo-path": str(sandbox_repo)})
    )
    assert rc_fail == 2


def test_snapshot_writes_json_and_markdown(fake_runner, tmp_path: Path):
    run_cli(_open_argv("SNAP-CARD1", **{"--resources": "file:a.py"}))
    out_dir = tmp_path / "snapshot-out"
    rc = run_cli(["snapshot", *BASE_TARGET, "--out-dir", str(out_dir)])
    assert rc == 0
    json_path = out_dir / "snapshot.json"
    md_path = out_dir / "SNAPSHOT.md"
    assert json_path.exists()
    assert md_path.exists()

    payload = jsonlib.loads(json_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "wf-cli/state-snapshot/v1"
    assert len(payload["cards"]) == 1
    assert payload["cards"][0]["card_id"] == "SNAP-CARD1"
    assert "file:a.py" in payload["cards"][0]["resources"]

    md_text = md_path.read_text(encoding="utf-8")
    assert "SNAP-CARD1" in md_text
    assert "卡ID" in md_text


def test_doctor_cli_reports_orphan_and_supports_strict_exit_code(sandbox_repo, capsys):
    subprocess.run(["git", "-C", str(sandbox_repo), "branch", "claude/untracked-orphan"], check=True)
    subprocess.run(
        ["git", "-C", str(sandbox_repo), "worktree", "add", str(sandbox_repo.parent / "wt-orphan"),
         "claude/untracked-orphan"],
        check=True,
    )

    rc_default = run_cli(["doctor", str(sandbox_repo), "--registry", "none"])
    assert rc_default == 0  # 預設不因孤兒而失敗，純報告
    out = capsys.readouterr().out
    assert "orphan_untracked" in out or "孤兒／未註冊" in out

    rc_strict = run_cli(["doctor", str(sandbox_repo), "--registry", "none", "--strict"])
    assert rc_strict == 1  # --strict 時孤兒存在應以非 0 退出，供 CI 使用


def test_doctor_cli_json_output_is_valid_json_document(sandbox_repo, capsys):
    run_cli(["doctor", str(sandbox_repo), "--registry", "none", "--json"])
    out = capsys.readouterr().out
    # render_text() 與 JSON 都印到同一個 stdout；JSON 區塊是最後一個頂層 `{...}`。
    json_start = out.index("{")
    payload = jsonlib.loads(out[json_start:])
    assert payload["repo_root"] == str(sandbox_repo.resolve())
