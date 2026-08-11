"""WF-CLEANUP-GUARD1：破壞性收尾守衛的驗證。

**這些測試會真的刪東西**——但只在 pytest 的 `tmp_path` 沙箱 repo 內。沒有任何一
條會碰到使用者機器上的實際 repo。

驗證策略（卡面「驗證」五條）：

1. 五種危險情境全數拒絕，且**拒絕後工作內容仍完整存在**（不只驗回傳碼）——
   `assert_work_intact()` 逐項核對檔案內容、本地分支、遠端分支、stash。
2. 故障注入：`step_hook` 在每個步驟間隙丟例外，續作後不得半完成、不得重複刪除。
3. 循環前置專項：守衛不檢查第 4 步；第 5–7 步不阻擋。
4. `--force` 不可用：擋在 git 執行入口 ＋ 掃描整個 argparse 樹 ＋ 逐一比對實際
   送出的 argv。
5. 全函數分類：`aggregate_mode` 與 `classify_state` 窮舉驗證，沒有「其餘」。
"""

from __future__ import annotations

import inspect
import itertools
import shutil
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from wf_cli import cleanup, git_ops
from wf_cli.cleanup import (
    CHECK_IDS,
    CHECK_STEP_REF,
    DESTRUCTIVE_ORDER,
    EFFECT_STEP,
    LEGAL_STATES,
    PRECONDITION_STEPS,
    STEP_ROLES,
    SUBSEQUENT_OBLIGATION_STEPS,
    CleanupGuardError,
    CleanupTarget,
    CloseoutObservation,
    RemoteCardFacts,
    aggregate_mode,
    classify_state,
    default_git_runner,
    evaluate_cleanup_guard,
    execute_closeout_transition,
    observe,
    parse_worktree_records,
)
from wf_cli.registry import RegisteredCard, TasksMdRegistry

from .conftest import git

CARD_ID = "WF-SANDBOX-CARD1"
BRANCH = "claude/WF-SANDBOX-CARD1"
WORK_CONTENT = "committed work that must never vanish\n"

CARD_BODY = """## 資源宣告
<!-- resource-claims:begin -->
```json
{"db_scope": "none", "resources": ["file:cli/src/wf_cli/cleanup.py"]}
```
<!-- resource-claims:end -->
"""


def free_prober(_: Path) -> tuple[str, str]:
    return "free", "fake prober：無人佔用"


def occupied_prober(_: Path) -> tuple[str, str]:
    return "occupied", "fake prober：有 process 佔用"


def unobservable_prober(_: Path) -> tuple[str, str]:
    return "unobservable", "fake prober：探不到"


@dataclass
class Env:
    repo: Path
    remote: Path
    wt: Path
    target: CleanupTarget
    registry: TasksMdRegistry


def _empty_registry() -> TasksMdRegistry:
    return TasksMdRegistry(active=[], archived_card_ids=set(), source_paths=[])


def _build_env(tmp_path: Path, sandbox_repo: Path, *, merged: bool) -> Env:
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    git(sandbox_repo, "remote", "add", "origin", str(remote))
    git(sandbox_repo, "push", "-q", "-u", "origin", "main")

    wt = tmp_path / "card-worktree"
    git(sandbox_repo, "worktree", "add", "-q", str(wt), "-b", BRANCH)
    (wt / "work.txt").write_text(WORK_CONTENT, encoding="utf-8")
    git(wt, "add", "work.txt")
    git(wt, "commit", "-q", "-m", "card work")
    git(wt, "push", "-q", "-u", "origin", BRANCH)

    if merged:
        git(sandbox_repo, "merge", "-q", "--no-ff", "-m", "merge card", BRANCH)
        git(sandbox_repo, "push", "-q", "origin", "main")

    return Env(
        repo=sandbox_repo,
        remote=remote,
        wt=wt,
        target=CleanupTarget(
            repo_root=sandbox_repo, card_id=CARD_ID, branch=BRANCH, worktree_path=wt
        ),
        registry=_empty_registry(),
    )


@pytest.fixture
def env(tmp_path: Path, sandbox_repo: Path) -> Env:
    """已 merge、乾淨、可安全清理的收尾情境。"""
    return _build_env(tmp_path, sandbox_repo, merged=True)


@pytest.fixture
def env_unmerged(tmp_path: Path, sandbox_repo: Path) -> Env:
    return _build_env(tmp_path, sandbox_repo, merged=False)


def guard(env: Env, *, prober=free_prober, body: str | None = CARD_BODY, registry=None):
    return evaluate_cleanup_guard(
        env.target,
        registry=env.registry if registry is None else registry,
        card_body=body,
        occupancy_prober=prober,
    )


def _local_branch_exists(repo: Path, branch: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", branch],
        capture_output=True, text=True, check=False,
    )
    return proc.returncode == 0 and bool(proc.stdout.strip())


def _remote_branch_exists(repo: Path, remote: str, branch: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo), "ls-remote", "--heads", remote, branch],
        capture_output=True, text=True, check=False,
    )
    return proc.returncode == 0 and bool(proc.stdout.strip())


def _stash_count(repo: Path) -> int:
    out = subprocess.run(
        ["git", "-C", str(repo), "stash", "list"],
        capture_output=True, text=True, check=False,
    ).stdout
    return len([ln for ln in out.splitlines() if ln.strip()])


def assert_work_intact(env: Env, *, extra_file: tuple[str, str] | None = None,
                       expected_stashes: int = 0) -> None:
    """拒絕之後，**工作內容必須原封不動**——這才是本卡真正要保住的東西。

    只驗 exit code 會漏掉「守衛回報拒絕，但某個步驟已經先把東西刪掉了」。
    """
    assert env.wt.exists(), "worktree 目錄被刪除了"
    assert (env.wt / "work.txt").read_text(encoding="utf-8") == WORK_CONTENT, "已提交的工作內容被改動"
    if extra_file is not None:
        name, content = extra_file
        assert (env.wt / name).read_text(encoding="utf-8") == content, f"{name} 的未提交內容遺失"
    assert _local_branch_exists(env.repo, BRANCH), "本地分支被刪除了"
    assert _remote_branch_exists(env.repo, "origin", BRANCH), "遠端分支被刪除了"
    assert _stash_count(env.repo) == expected_stashes, "stash 被動到了"


# ---------------------------------------------------------------------------
# 1. 五種危險情境：全數拒絕，且工作內容完整存在
# ---------------------------------------------------------------------------


def test_refuses_when_uncommitted_changes(env: Env) -> None:
    (env.wt / "draft.txt").write_text("尚未提交的草稿\n", encoding="utf-8")
    result = execute_closeout_transition(
        env.target, trigger="reconcile", registry=env.registry, card_body=CARD_BODY,
        remote_facts=RemoteCardFacts(False, True), occupancy_prober=free_prober,
    )
    assert result.mode == "detect_only"
    assert result.actions_performed == ()
    assert any("no_uncommitted_changes" in r for r in result.blocking_reasons)
    assert_work_intact(env, extra_file=("draft.txt", "尚未提交的草稿\n"))


def test_refuses_when_stash_present(env: Env) -> None:
    (env.wt / "work.txt").write_text("modified\n", encoding="utf-8")
    git(env.wt, "stash", "push", "-q", "-m", "unfinished")
    assert _stash_count(env.repo) == 1
    result = execute_closeout_transition(
        env.target, trigger="reconcile", registry=env.registry, card_body=CARD_BODY,
        remote_facts=RemoteCardFacts(False, True), occupancy_prober=free_prober,
    )
    assert result.mode == "detect_only"
    assert any("no_stash" in r for r in result.blocking_reasons)
    assert_work_intact(env, expected_stashes=1)
    # stash 的內容也要還在，不只是條目數
    assert "modified" in subprocess.run(
        ["git", "-C", str(env.repo), "stash", "show", "-p", "stash@{0}"],
        capture_output=True, text=True, check=False,
    ).stdout


def test_refuses_when_active_lease_held_by_other_card(env: Env) -> None:
    registry = TasksMdRegistry(
        active=[
            RegisteredCard(
                card_id="OTHER-CARD1", branch=BRANCH, worktree_path=str(env.wt),
                delivery_status="🔨執行中", owner="someone@tool",
            )
        ],
        archived_card_ids=set(), source_paths=[],
    )
    result = execute_closeout_transition(
        env.target, trigger="reconcile", registry=registry, card_body=CARD_BODY,
        remote_facts=RemoteCardFacts(False, True), occupancy_prober=free_prober,
    )
    assert result.mode == "detect_only"
    assert any("no_foreign_active_lease" in r for r in result.blocking_reasons)
    assert_work_intact(env)


def test_refuses_when_worktree_is_cwd(env: Env, monkeypatch: pytest.MonkeyPatch) -> None:
    """真的把 process 的 cwd 移進待刪 worktree（權威清單：禁止在 worktree 內移除自身）。"""
    monkeypatch.chdir(env.wt)
    result = execute_closeout_transition(
        env.target, trigger="reconcile", registry=env.registry, card_body=CARD_BODY,
        remote_facts=RemoteCardFacts(False, True), occupancy_prober=free_prober,
    )
    assert result.mode == "detect_only"
    assert any("not_self_cwd" in r for r in result.blocking_reasons)
    assert_work_intact(env)


def test_refuses_when_branch_not_merged(env_unmerged: Env) -> None:
    env = env_unmerged
    result = execute_closeout_transition(
        env.target, trigger="reconcile", registry=env.registry, card_body=CARD_BODY,
        remote_facts=RemoteCardFacts(False, True), occupancy_prober=free_prober,
    )
    assert result.mode == "detect_only"
    reasons = " ".join(result.blocking_reasons)
    # 本地與遠端各自驗，兩條都必須報
    assert "merge_verified_local" in reasons
    assert "merge_verified_remote" in reasons
    assert_work_intact(env)


# ---------------------------------------------------------------------------
# 其餘阻擋條件（把驗收第 1 條的枚舉補齊）
# ---------------------------------------------------------------------------


def test_refuses_when_worktree_locked(env: Env) -> None:
    git(env.repo, "worktree", "lock", str(env.wt))
    decision = guard(env)
    assert decision.mode == "detect_only"
    assert any(c.check_id == "no_locked_worktree" and c.outcome == "fail" for c in decision.checks)
    git(env.repo, "worktree", "unlock", str(env.wt))


def test_refuses_when_occupancy_unobservable(env: Env) -> None:
    """探不到 ≠ 沒人佔用。unobservable 必須與 fail 同等阻擋。"""
    decision = guard(env, prober=unobservable_prober)
    assert decision.mode == "detect_only"
    assert any(
        c.check_id == "not_occupied_by_process" and c.outcome == "unobservable"
        for c in decision.checks
    )


def test_refuses_when_occupied_by_process(env: Env) -> None:
    decision = guard(env, prober=occupied_prober)
    assert decision.mode == "detect_only"


def test_refuses_primary_worktree(env: Env) -> None:
    target = replace(env.target, worktree_path=env.repo, branch="main")
    decision = evaluate_cleanup_guard(
        target, registry=env.registry, card_body=CARD_BODY, occupancy_prober=free_prober
    )
    assert decision.mode == "detect_only"
    assert any(c.check_id == "not_primary_worktree" and c.outcome == "fail" for c in decision.checks)


def test_refuses_when_no_registry(env: Env) -> None:
    decision = evaluate_cleanup_guard(
        env.target, registry=None, card_body=CARD_BODY, occupancy_prober=free_prober
    )
    assert decision.mode == "detect_only"
    assert any(
        c.check_id == "no_foreign_active_lease" and c.outcome == "unobservable"
        for c in decision.checks
    )


def test_refuses_when_non_file_resources_still_declared(env: Env) -> None:
    body = CARD_BODY.replace('"file:cli/src/wf_cli/cleanup.py"', '"port:4001"')
    decision = guard(env, body=body)
    assert decision.mode == "detect_only"
    assert any(c.check_id == "resources_released" and c.outcome == "fail" for c in decision.checks)


def test_refuses_when_card_body_missing(env: Env) -> None:
    decision = guard(env, body=None)
    assert decision.mode == "detect_only"


def test_stash_with_an_unparseable_message_is_unobservable(env: Env) -> None:
    """歸屬不明的 stash 必須擋。

    突變測試 M04（把「解析不出所屬分支」改成直接略過該筆）在此之前存活——沒有任何
    案例覆蓋這條規則。真實 stash 幾乎都長成 ``WIP on X:``／``On X:``，所以這裡直接
    餵一筆解析不出來的 stash list 輸出，而不是想辦法把 git 的 reflog 弄壞。
    """

    def runner(cwd: Path, args):
        if list(args)[:2] == ["stash", "list"]:
            return cleanup.GitResult(0, "stash@{0}\tsomething nobody can parse\n", "")
        return default_git_runner(cwd, args)

    decision = evaluate_cleanup_guard(
        env.target, registry=env.registry, card_body=CARD_BODY,
        runner=runner, occupancy_prober=free_prober,
    )
    check = next(c for c in decision.checks if c.check_id == "no_stash")
    assert check.outcome == "unobservable", "無法證明這筆 stash 不屬於待刪分支，就不能放行"
    assert decision.mode == "detect_only"


def test_remote_commit_missing_from_the_local_object_store_is_unobservable(
    env: Env, tmp_path: Path
) -> None:
    """前提檢查也不對「本機沒見過的 commit」下祖先判斷。

    突變測試 M15（拿掉 `cat-file` 可觀測性檢查）在此之前存活：少了它，守衛會對一個
    自己沒有的物件跑 `merge-base`，git 只會回一個籠統的錯誤，於是「觀測不到」被降級
    成「未併入」——結論碰巧一樣，理由卻是錯的，而理由才是報告給人看的東西。
    """
    other = _other_clone(tmp_path, env.remote)
    _push_new_commit_from_other_clone(other)  # 本機刻意不 fetch

    decision = evaluate_cleanup_guard(
        env.target, registry=env.registry, card_body=CARD_BODY, occupancy_prober=free_prober
    )
    check = next(c for c in decision.checks if c.check_id == "merge_verified_remote")
    assert check.outcome == "unobservable"
    assert "不在本地物件庫" in check.detail
    assert decision.mode == "detect_only"


@pytest.mark.skipif(shutil.which("lsof") is None, reason="此機器沒有 lsof")
def test_real_lsof_prober_detects_own_cwd(env: Env, monkeypatch: pytest.MonkeyPatch) -> None:
    """真探針、真 process：不是只有 fake 會回 occupied。"""
    monkeypatch.chdir(env.wt)
    outcome, detail = cleanup.lsof_cwd_prober(env.wt)
    if outcome == "unobservable":
        pytest.skip(f"lsof 在此環境不可用：{detail}")
    assert outcome == "occupied", detail


# ---------------------------------------------------------------------------
# 2. 正向對照：前提全成立時真的會清乾淨（沒有它，上面的拒絕測試可能是空頭支票）
# ---------------------------------------------------------------------------


class FakeRemoteState:
    def __init__(self) -> None:
        self.terminal_written = False
        self.issue_open = True

    def facts(self) -> RemoteCardFacts:
        return RemoteCardFacts(self.terminal_written, self.issue_open)


class FakeEffectWriter:
    def __init__(self, remote: FakeRemoteState) -> None:
        self.remote = remote
        self.calls: list[str] = []

    def close_issue(self, target: CleanupTarget) -> None:
        self.calls.append("close_issue")
        self.remote.issue_open = False

    def write_release_terminal(self, target: CleanupTarget) -> None:
        self.calls.append("write_release_terminal")
        self.remote.terminal_written = True


def recording_runner(log: list[list[str]]):
    def run(cwd: Path, args):
        log.append(list(args))
        return default_git_runner(cwd, args)

    return run


def test_clean_case_actually_cleans_up(env: Env) -> None:
    remote = FakeRemoteState()
    writer = FakeEffectWriter(remote)
    result = execute_closeout_transition(
        env.target, trigger="release", registry=env.registry, card_body=CARD_BODY,
        remote_facts=remote.facts(), effect_writer=writer, occupancy_prober=free_prober,
    )
    assert result.mode == "applied", result.blocking_reasons
    assert result.actions_performed == DESTRUCTIVE_ORDER
    assert not env.wt.exists()
    assert not _local_branch_exists(env.repo, BRANCH)
    assert not _remote_branch_exists(env.repo, "origin", BRANCH)
    # 第 4 步的順序：先關 Issue，終態最後落地
    assert writer.calls == ["close_issue", "write_release_terminal"]
    assert result.state_after == "completed"


def test_second_run_is_a_noop(env: Env) -> None:
    remote = FakeRemoteState()
    writer = FakeEffectWriter(remote)
    common = dict(registry=env.registry, card_body=CARD_BODY, effect_writer=writer,
                  occupancy_prober=free_prober)
    execute_closeout_transition(env.target, trigger="release",
                               remote_facts=remote.facts(), **common)
    again = execute_closeout_transition(env.target, trigger="reconcile",
                                        remote_facts=remote.facts(), **common)
    assert again.mode == "applied"
    assert again.actions_performed == ()
    assert set(again.actions_skipped_absent) == set(DESTRUCTIVE_ORDER)
    assert writer.calls == ["close_issue", "write_release_terminal"], "第 4 步被重複寫入"


# ---------------------------------------------------------------------------
# 3. 同一份實作：不得依觸發者切分
# ---------------------------------------------------------------------------


def test_guard_signature_has_no_trigger_and_no_force() -> None:
    params = set(inspect.signature(evaluate_cleanup_guard).parameters)
    assert "trigger" not in params, "守衛能看見觸發者，就有依觸發者放寬前提的空間"
    assert not any("force" in p for p in params)
    exec_params = set(inspect.signature(execute_closeout_transition).parameters)
    assert not any("force" in p for p in exec_params)


@pytest.mark.parametrize("prober", [free_prober, occupied_prober, unobservable_prober])
def test_decision_identical_for_release_and_reconcile(env: Env, prober) -> None:
    a = execute_closeout_transition(
        env.target, trigger="release", registry=env.registry, card_body=CARD_BODY,
        remote_facts=RemoteCardFacts(False, True), occupancy_prober=prober,
    )
    b = execute_closeout_transition(
        env.target, trigger="reconcile", registry=env.registry, card_body=CARD_BODY,
        remote_facts=RemoteCardFacts(False, True), occupancy_prober=prober,
    )
    assert a.decision.mode == b.decision.mode
    assert [c.outcome for c in a.decision.checks] == [c.outcome for c in b.decision.checks]
    assert a.blocking_reasons == b.blocking_reasons


# ---------------------------------------------------------------------------
# 4. --force 在 reconcile 路徑確實不可用（不只是文件寫著）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "args",
    [
        ["push", "origin", "--delete", "x", "--force"],
        ["branch", "-D", "x"],
        ["worktree", "remove", "--force", "/tmp/x"],
        ["push", "--force-with-lease", "origin", "x"],
        ["clean", "-f"],
    ],
)
def test_force_flags_are_rejected_at_the_git_entrypoint(tmp_path: Path, args) -> None:
    with pytest.raises(CleanupGuardError):
        default_git_runner(tmp_path, args)


def test_force_rejected_even_with_a_custom_runner(tmp_path: Path) -> None:
    """換掉 runner 也繞不過：禁用檢查掛在 `_run`，不是掛在 default runner 裡。"""
    called: list[list[str]] = []

    def permissive(cwd: Path, a):
        called.append(list(a))
        return cleanup.GitResult(0, "", "")

    with pytest.raises(CleanupGuardError):
        cleanup._run(permissive, tmp_path, ["branch", "-D", "x"])
    assert called == [], "禁用旗標在送進 runner 之前就該被擋下"


def test_no_force_flag_anywhere_in_the_cli_parser() -> None:
    from wf_cli.cli import build_parser

    def option_strings(parser) -> list[str]:
        out: list[str] = []
        for action in parser._actions:
            out.extend(action.option_strings)
            if hasattr(action, "choices") and isinstance(action.choices, dict):
                for sub in action.choices.values():
                    out.extend(option_strings(sub))
        return out

    forced = [o for o in option_strings(build_parser()) if o.startswith("--force") or o == "-f"]
    assert forced == [], f"CLI 暴露了強制旗標：{forced}"


def test_doctor_rejects_force_flag(tmp_path: Path) -> None:
    from wf_cli.cli import build_parser

    with pytest.raises(SystemExit):
        build_parser().parse_args(["doctor", str(tmp_path), "--force"])


def test_applied_run_never_sends_a_force_flag(env: Env) -> None:
    log: list[list[str]] = []
    remote = FakeRemoteState()
    result = execute_closeout_transition(
        env.target, trigger="reconcile", registry=env.registry, card_body=CARD_BODY,
        remote_facts=remote.facts(), effect_writer=FakeEffectWriter(remote),
        runner=recording_runner(log), occupancy_prober=free_prober,
    )
    assert result.mode == "applied"
    assert log, "沒有記錄到任何 git 呼叫，這條驗證會變成空頭支票"
    flat = [a for argv in log for a in argv]
    assert not [a for a in flat if a.startswith("--force") or a in {"-f", "-D", "-M"}]
    assert ["branch", "-d", BRANCH] in log, "本地分支刪除應使用安全的 -d"


# ---------------------------------------------------------------------------
# 5. 三段分離與循環前置專項
# ---------------------------------------------------------------------------


def test_step_roles_partition_the_authoritative_list() -> None:
    assert set(STEP_ROLES) == {1, 2, 3, 4, 5, 6, 7}
    buckets = {
        "precondition": set(PRECONDITION_STEPS),
        "effect": {EFFECT_STEP},
        "subsequent_obligation": set(SUBSEQUENT_OBLIGATION_STEPS),
    }
    for step, role in STEP_ROLES.items():
        assert step in buckets[role]
    union: set[int] = set()
    for members in buckets.values():
        assert not (union & members), "同一步落在兩個角色 = 分類不是全函數"
        union |= members
    assert union == {1, 2, 3, 4, 5, 6, 7}


def test_guard_never_checks_step_four(env: Env) -> None:
    """守衛若檢查第 4 步（Issue 關閉／終態），release 永遠無法發動。"""
    assert EFFECT_STEP not in set(CHECK_STEP_REF.values())
    decision = guard(env)
    assert {c.step_ref for c in decision.checks} <= set(PRECONDITION_STEPS)
    assert EFFECT_STEP not in {c.step_ref for c in decision.checks}
    # 守衛的輸入裡根本沒有狀態面事實
    assert "remote_facts" not in inspect.signature(evaluate_cleanup_guard).parameters


def test_release_proceeds_while_issue_still_open_and_status_not_terminal(env: Env) -> None:
    """第 4 步尚未發生（Issue 開著、非終態）恰恰是 release 該被允許的前提。"""
    result = execute_closeout_transition(
        env.target, trigger="release", registry=env.registry, card_body=CARD_BODY,
        remote_facts=RemoteCardFacts(terminal_status_written=False, issue_open=True),
        occupancy_prober=free_prober,
    )
    assert result.mode == "applied"


def test_subsequent_obligations_never_block(env: Env) -> None:
    """第 5–7 步未完成（本函式根本不執行它們）不得阻擋 release。"""
    remote = FakeRemoteState()
    result = execute_closeout_transition(
        env.target, trigger="release", registry=env.registry, card_body=CARD_BODY,
        remote_facts=remote.facts(), effect_writer=FakeEffectWriter(remote),
        occupancy_prober=free_prober,
    )
    assert result.mode == "applied"
    assert result.outstanding_obligations == SUBSEQUENT_OBLIGATION_STEPS
    assert result.state_after == "completed"
    # 其後義務不寫狀態面，故不列入 remaining_status_face_steps
    assert result.remaining_status_face_steps == ()
    assert not set(SUBSEQUENT_OBLIGATION_STEPS) & set(result.remaining_status_face_steps)


def test_terminal_write_is_last_of_the_status_face_sequence(env: Env) -> None:
    remote = FakeRemoteState()
    writer = FakeEffectWriter(remote)
    order: list[str] = []
    execute_closeout_transition(
        env.target, trigger="release", registry=env.registry, card_body=CARD_BODY,
        remote_facts=remote.facts(), effect_writer=writer, occupancy_prober=free_prober,
        step_hook=order.append,
    )
    assert order.index("after_delete_remote_branch") < order.index("after_write_terminal")
    assert order.index("after_close_issue") < order.index("after_write_terminal")


def test_terminal_before_cleanup_is_illegal_and_not_repaired(env: Env) -> None:
    remote = FakeRemoteState()
    remote.terminal_written = True
    remote.issue_open = False
    result = execute_closeout_transition(
        env.target, trigger="reconcile", registry=env.registry, card_body=CARD_BODY,
        remote_facts=remote.facts(), effect_writer=FakeEffectWriter(remote),
        occupancy_prober=free_prober,
    )
    assert result.mode == "detect_only"
    assert result.state_after == "illegal_terminal_before_cleanup"
    assert not result.legal_state
    assert_work_intact(env)


# ---------------------------------------------------------------------------
# 6. 故障注入：每個步驟間隙都有案例
# ---------------------------------------------------------------------------


GAPS = [
    "guard_passed",
    "after_remove_worktree",
    "after_delete_local_branch",
    "after_delete_remote_branch",
    "after_close_issue",
    "after_write_terminal",
]


class Boom(RuntimeError):
    pass


@pytest.mark.parametrize("gap", GAPS)
def test_interrupt_at_each_gap_then_resume(env: Env, gap: str) -> None:
    remote = FakeRemoteState()
    writer = FakeEffectWriter(remote)
    log: list[list[str]] = []

    def hook(step: str) -> None:
        if step == gap:
            raise Boom(step)

    with pytest.raises(Boom):
        execute_closeout_transition(
            env.target, trigger="reconcile", registry=env.registry, card_body=CARD_BODY,
            remote_facts=remote.facts(), effect_writer=writer,
            runner=recording_runner(log), occupancy_prober=free_prober, step_hook=hook,
        )

    # 中斷當下必須落在合法暫時態：本機可部分完成，遠端不得先於清理寫終態
    mid = observe(env.target, remote.facts())
    assert classify_state(mid) in LEGAL_STATES, f"中斷於 {gap} 產生非法組合"

    # 續作只讀當下事實，不靠任何「做到哪」的本機紀錄
    resumed = execute_closeout_transition(
        env.target, trigger="release", registry=env.registry, card_body=CARD_BODY,
        remote_facts=remote.facts(), effect_writer=writer,
        runner=recording_runner(log), occupancy_prober=free_prober,
    )
    assert resumed.mode == "applied", resumed.blocking_reasons
    assert resumed.state_after == "completed"
    assert not env.wt.exists()
    assert not _local_branch_exists(env.repo, BRANCH)
    assert not _remote_branch_exists(env.repo, "origin", BRANCH)

    # 不得重複刪除：每個破壞性 argv 在兩次執行加總後最多出現一次
    def count(prefix: list[str]) -> int:
        return sum(1 for argv in log if argv[: len(prefix)] == prefix)

    assert count(["worktree", "remove"]) <= 1
    assert count(["branch", "-d"]) <= 1
    assert count(["push", "origin", "--delete"]) <= 1
    assert writer.calls.count("close_issue") <= 1
    assert writer.calls.count("write_release_terminal") <= 1
    assert writer.calls[-1] == "write_release_terminal"


def _silently_noop_runner(log: list[list[str]], prefix: list[str]):
    """讓某個刪除指令**回報成功但實際沒做**。

    這不是假想：受保護分支、鏡像同步、最終一致的遠端都可能讓 `push --delete`
    回 0 而分支還在。此時效果（第 4 步）若照寫，就會產生「Issue 已關但分支仍在」
    ——正是卡面驗證明文禁止的半完成組合。
    """

    def run(cwd: Path, args):
        log.append(list(args))
        if list(args)[: len(prefix)] == prefix:
            return cleanup.GitResult(0, "", "")
        return default_git_runner(cwd, args)

    return run


@pytest.mark.parametrize(
    ("prefix", "still_present"),
    [
        (["branch", "-d"], "local"),
        (["push", "origin", "--delete"], "remote"),
    ],
)
def test_effect_is_withheld_when_cleanup_did_not_actually_complete(
    env: Env, prefix: list[str], still_present: str
) -> None:
    remote = FakeRemoteState()
    writer = FakeEffectWriter(remote)
    log: list[list[str]] = []
    result = execute_closeout_transition(
        env.target, trigger="reconcile", registry=env.registry, card_body=CARD_BODY,
        remote_facts=remote.facts(), effect_writer=writer,
        runner=_silently_noop_runner(log, prefix), occupancy_prober=free_prober,
    )
    assert result.mode == "applied"
    assert writer.calls == [], "清理未真正完成就寫狀態面，會造出非法半完成組合"
    assert remote.issue_open is True and remote.terminal_written is False
    if still_present == "local":
        assert _local_branch_exists(env.repo, BRANCH)
    else:
        assert _remote_branch_exists(env.repo, "origin", BRANCH)
    assert result.state_after == "cleanup_in_progress"
    assert result.legal_state
    assert set(result.remaining_status_face_steps) == {2, EFFECT_STEP}


def test_failed_worktree_removal_stops_before_touching_the_status_face(env: Env) -> None:
    """worktree 假成功 → 分支仍被 checkout → `branch -d` 必失敗且不得升級為 -D。"""
    remote = FakeRemoteState()
    writer = FakeEffectWriter(remote)
    log: list[list[str]] = []
    with pytest.raises(CleanupGuardError):
        execute_closeout_transition(
            env.target, trigger="release", registry=env.registry, card_body=CARD_BODY,
            remote_facts=remote.facts(), effect_writer=writer,
            runner=_silently_noop_runner(log, ["worktree", "remove"]),
            occupancy_prober=free_prober,
        )
    assert writer.calls == []
    assert not [a for argv in log for a in argv if a == "-D"]
    assert_work_intact(env)


# ---------------------------------------------------------------------------
# 6.1 R1-001：守衛通過後、遠端刪除前的時間窗（TOCTOU）
# ---------------------------------------------------------------------------

RESCUED_WORK = "work pushed by another clone after the guard had already passed\n"


def _other_clone(tmp_path: Path, remote: Path) -> Path:
    """另一個 clone——代表「另一台機器／另一個人」，與本 repo 只共用 bare remote。"""
    other = tmp_path / "other-clone"
    subprocess.run(["git", "clone", "-q", str(remote), str(other)], check=True)
    git(other, "config", "user.email", "other@example.com")
    git(other, "config", "user.name", "another clone")
    return other


def _push_new_commit_from_other_clone(other: Path) -> str:
    git(other, "checkout", "-q", "-B", BRANCH, f"origin/{BRANCH}")
    (other / "rescue.txt").write_text(RESCUED_WORK, encoding="utf-8")
    git(other, "add", "rescue.txt")
    git(other, "commit", "-q", "-m", "work that must survive the cleanup")
    git(other, "push", "-q", "origin", BRANCH)
    return git(other, "rev-parse", "HEAD").strip()


def _remote_tip(repo: Path, branch: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(repo), "ls-remote", "--heads", "origin", branch],
        capture_output=True, text=True, check=True,
    ).stdout
    return out.split("\t")[0].strip()


def _content_recoverable_from_remote(tmp_path: Path, remote: Path, name: str) -> str:
    """從遠端**重新** clone 一份，證明內容真的還在遠端，不是只有本機看起來還在。"""
    check = tmp_path / f"verify-{name}"
    subprocess.run(["git", "clone", "-q", "-b", BRANCH, str(remote), str(check)], check=True)
    return (check / "rescue.txt").read_text(encoding="utf-8")


@pytest.mark.parametrize("fetch_after_push", [False, True])
def test_remote_delete_refused_when_tip_moved_after_the_guard_passed(
    env: Env, tmp_path: Path, fetch_after_push: bool
) -> None:
    """R1-001：守衛通過 → 本機清理完成 → **別人推了新提交** → 遠端刪除必須拒絕。

    這是本模組唯一會真的毀掉他人已提交內容的路徑。舊實作在此只重新確認「遠端分支
    還在」——分支確實還在，但 tip 已經換人，照刪就把新提交刪掉了。

    兩個參數化分支覆蓋二次確認的兩種拒絕理由：
    - ``fetch_after_push=False``：新提交不在本地物件庫 → `unobservable`（守衛不代為
      fetch，也不刪自己沒看過的東西）；
    - ``fetch_after_push=True``：本機已 fetch 得到該 commit → `cat-file` 過得了，
      但 `merge-base --is-ancestor` 不成立 → `fail`。
      沒有這一半，只要有人在別處先 fetch 過，守衛就會退回舊行為。
    """
    other = _other_clone(tmp_path, env.remote)
    remote_state = FakeRemoteState()
    writer = FakeEffectWriter(remote_state)
    new_sha = ""

    def hook(step: str) -> None:
        nonlocal new_sha
        if step == "after_delete_local_branch":
            new_sha = _push_new_commit_from_other_clone(other)
            if fetch_after_push:
                git(env.repo, "fetch", "-q", "origin", BRANCH)

    result = execute_closeout_transition(
        env.target, trigger="release", registry=env.registry, card_body=CARD_BODY,
        remote_facts=remote_state.facts(), effect_writer=writer,
        occupancy_prober=free_prober, step_hook=hook,
    )

    # 1) 遠端刪除被拒，且拒絕理由指名是「刪除前的二次確認」而非前提檢查
    assert result.mode == "aborted", result
    assert result.actions_aborted == ("delete_remote_branch",)
    assert result.actions_performed == ("remove_worktree", "delete_local_branch")
    assert any(cleanup.RECHECK_REMOTE_ID in r for r in result.blocking_reasons)
    expected = "unobservable" if not fetch_after_push else "fail"
    assert [c.outcome for c in result.recheck_checks] == [expected]

    # 2) 新提交仍在遠端——不是只驗回傳碼，是真的再 clone 一份把內容讀出來
    assert _remote_branch_exists(env.repo, "origin", BRANCH)
    assert _remote_tip(env.repo, BRANCH) == new_sha
    assert _content_recoverable_from_remote(tmp_path, env.remote, "aborted") == RESCUED_WORK

    # 3) 效果被扣住：狀態面沒寫、Issue 沒關，停在合法的暫時態
    assert writer.calls == []
    assert remote_state.issue_open is True and remote_state.terminal_written is False
    assert result.state_after == "cleanup_in_progress"
    assert result.legal_state
    assert set(result.remaining_status_face_steps) == {2, EFFECT_STEP}

    # 4) 重跑不會「第二次就刪掉」：前提複驗此時看到未併入的遠端 tip，直接純偵測
    resumed = execute_closeout_transition(
        env.target, trigger="reconcile", registry=env.registry, card_body=CARD_BODY,
        remote_facts=remote_state.facts(), effect_writer=writer, occupancy_prober=free_prober,
    )
    assert resumed.mode == "detect_only"
    assert any("merge_verified_remote" in r for r in resumed.blocking_reasons)
    assert _content_recoverable_from_remote(tmp_path, env.remote, "resumed") == RESCUED_WORK


def test_recheck_reports_absent_remote_branch_as_nothing_to_delete(env: Env) -> None:
    """二次確認的 `absent` 不是拒絕：遠端分支本來就沒了，跳過即可，不得誤報阻擋。"""
    git(env.repo, "push", "-q", "origin", "--delete", BRANCH)
    verdict, check = cleanup.recheck_remote_branch(env.target, default_git_runner)
    assert verdict == "absent"
    assert check.outcome == "pass"


def test_recheck_refuses_when_remote_is_unreadable(env: Env) -> None:
    """讀不到遠端＝不知道 tip 是誰。不知道就不刪。"""

    def broken(cwd: Path, args):
        if list(args)[:1] == ["ls-remote"]:
            return cleanup.GitResult(128, "", "fatal: unable to access remote")
        return default_git_runner(cwd, args)

    verdict, check = cleanup.recheck_remote_branch(env.target, broken)
    assert verdict == "refuse"
    assert check.outcome == "unobservable"


def test_recheck_runs_on_the_happy_path_too(env: Env) -> None:
    """放行路徑也必須留下二次確認的紀錄，否則「有沒有複驗過」無從對帳。"""
    remote_state = FakeRemoteState()
    result = execute_closeout_transition(
        env.target, trigger="release", registry=env.registry, card_body=CARD_BODY,
        remote_facts=remote_state.facts(), effect_writer=FakeEffectWriter(remote_state),
        occupancy_prober=free_prober,
    )
    assert result.mode == "applied"
    assert [c.check_id for c in result.recheck_checks] == [cleanup.RECHECK_REMOTE_ID]
    assert [c.outcome for c in result.recheck_checks] == ["pass"]


def test_resume_uses_no_local_progress_record(env: Env, tmp_path: Path) -> None:
    """觀測式續作：中斷後把整個 repo 目錄以外的東西全丟掉也能續作。

    這裡以「換一個全新的 CleanupTarget 物件、不帶任何前次執行的殘留」代表
    「新 process、新機器」。若實作偷藏了 in-memory／檔案進度，這條會壞。
    """
    remote = FakeRemoteState()
    writer = FakeEffectWriter(remote)

    def hook(step: str) -> None:
        if step == "after_remove_worktree":
            raise Boom(step)

    with pytest.raises(Boom):
        execute_closeout_transition(
            env.target, trigger="reconcile", registry=env.registry, card_body=CARD_BODY,
            remote_facts=remote.facts(), effect_writer=writer, occupancy_prober=free_prober,
            step_hook=hook,
        )

    fresh_target = CleanupTarget(
        repo_root=env.repo, card_id=CARD_ID, branch=BRANCH, worktree_path=env.wt
    )
    resumed = execute_closeout_transition(
        fresh_target, trigger="reconcile", registry=_empty_registry(), card_body=CARD_BODY,
        remote_facts=remote.facts(), effect_writer=writer, occupancy_prober=free_prober,
    )
    assert resumed.state_after == "completed"
    assert "remove_worktree" in resumed.actions_skipped_absent


# ---------------------------------------------------------------------------
# 7. 全函數分類：沒有「其餘」
# ---------------------------------------------------------------------------


def test_aggregate_mode_is_total() -> None:
    values = ("pass", "fail", "unobservable")
    seen = set()
    for combo in itertools.product(values, repeat=4):
        mode = aggregate_mode(list(combo))
        assert mode in {"proceed", "detect_only"}
        assert mode == ("proceed" if all(v == "pass" for v in combo) else "detect_only")
        seen.add(mode)
    assert seen == {"proceed", "detect_only"}
    assert aggregate_mode([]) == "proceed"  # 空集合＝無阻擋項


def test_classification_is_total_over_all_32_combinations() -> None:
    classes = {
        "cleanup_in_progress",
        "cleanup_done_effect_pending",
        "effect_in_progress",
        "completed",
        "illegal_terminal_before_cleanup",
    }
    counts: dict[str, int] = {c: 0 for c in classes}
    for combo in itertools.product([False, True], repeat=5):
        obs = CloseoutObservation(*combo)
        state = classify_state(obs)
        assert state in classes, f"{combo} 落在列舉之外"
        counts[state] += 1
        # 非法的定義：清理未完成卻已動狀態面終態序列
        assert (state == "illegal_terminal_before_cleanup") == (
            not obs.cleanup_done and obs.effect_started
        )
        assert (state in LEGAL_STATES) != (state == "illegal_terminal_before_cleanup")
    assert sum(counts.values()) == 32
    assert all(n > 0 for n in counts.values()), f"有分類永遠取不到：{counts}"


def test_check_ids_cover_every_emitted_check(env: Env) -> None:
    decision = guard(env)
    assert [c.check_id for c in decision.checks] == list(CHECK_IDS)
    assert set(CHECK_STEP_REF) == set(CHECK_IDS)


def test_remaining_steps_never_include_obligations() -> None:
    for combo in itertools.product([False, True], repeat=5):
        obs = CloseoutObservation(*combo)
        steps = cleanup.remaining_status_face_steps(obs)
        assert not set(steps) & set(SUBSEQUENT_OBLIGATION_STEPS)
        assert set(steps) <= {2, EFFECT_STEP}


# ---------------------------------------------------------------------------
# 8. 引用權威而非重述：順序漂移必須被抓到
# ---------------------------------------------------------------------------


def _authority_lines() -> list[str]:
    root = Path(__file__).resolve().parents[2]
    return (root / cleanup.AUTHORITY_PATH).read_text(encoding="utf-8").splitlines()


def test_destructive_order_matches_authority() -> None:
    lines = _authority_lines()
    head = lines[10]  # 第 11 行（1-based）
    assert head.lstrip().startswith("5."), f"權威清單不在第 11 行了：{head[:40]!r}"
    sub = [lines[10 + i] for i in range(1, 8)]
    for i, line in enumerate(sub, start=1):
        assert line.strip().startswith(f"{i}."), f"第 {i} 個子步驟形狀改變：{line[:40]!r}"
    assert set(STEP_ROLES) == set(range(1, 8)), "權威清單是七步，STEP_ROLES 必須逐一對應"
    cleanup_step = sub[1]
    positions = [cleanup_step.find(tok) for tok in ("移除目錄", "刪本地分支", "刪遠端分支")]
    assert all(p >= 0 for p in positions), f"第 2 步不再列出三個刪除動作：{cleanup_step!r}"
    assert positions == sorted(positions), "權威清單的刪除順序變了，本模組必須同步"
    assert DESTRUCTIVE_ORDER == (
        "remove_worktree", "delete_local_branch", "delete_remote_branch"
    )


def test_worktree_parsers_agree() -> None:
    """本模組的 porcelain 解析器與 git_ops 既有解析器不得各自漂移。"""
    text = (
        "worktree /a\nHEAD 1111111111111111111111111111111111111111\nbranch refs/heads/main\n\n"
        "worktree /b\nHEAD 2222222222222222222222222222222222222222\n"
        "branch refs/heads/feat\nlocked in use\n\n"
        "worktree /c\nHEAD 3333333333333333333333333333333333333333\ndetached\n\n"
    )
    mine = parse_worktree_records(text)
    theirs = git_ops.parse_worktree_porcelain(text)
    assert [(r.path, r.branch) for r in mine] == [(e.path, e.branch) for e in theirs]
    assert [r.locked for r in mine] == [False, True, False]
    assert [r.is_primary for r in mine] == [True, False, False]
