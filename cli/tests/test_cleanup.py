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

import ast
import dis
import inspect
import itertools
import re
import shutil
import subprocess
import sys
import textwrap
from collections.abc import Mapping
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

from .conftest import SANDBOX_COMMIT_DATE, fixed_date_env, git

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
    #: 收尾開始前的遠端分支 tip。條件式刪除的租約期望值必須等於它。
    tip_before_cleanup: str = ""


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
        tip_before_cleanup=git(wt, "rev-parse", "HEAD").strip(),
    )


@pytest.fixture
def env(tmp_path: Path, sandbox_repo: Path) -> Env:
    """已 merge、乾淨、可安全清理的收尾情境。"""
    return _build_env(tmp_path, sandbox_repo, merged=True)


@pytest.fixture
def env_unmerged(tmp_path: Path, sandbox_repo: Path) -> Env:
    return _build_env(tmp_path, sandbox_repo, merged=False)


def _build_squash_env(tmp_path: Path, sandbox_repo: Path) -> Env:
    """`ROADMAP §3.5` 生效之後**每一張卡**的形狀，逐步重現 #9／#63／#73 的真實情形。

    四件事缺一不可，少任何一件就不是那三張卡當天被擋下的那個形狀：

    1. 卡分支推上遠端之後，**別張卡先進了 main**（strict 政策因此要求本卡先更新）；
    2. `gh pr update-branch` 把 main 併進 PR 分支——**這是 GitHub 在伺服器端做的**；
    3. main 以 **squash** 收下整條分支：長出一筆全新 commit，分支 tip 不是它的祖先；
    4. 本機那條 branch ref **從來沒被第 2 步更新過**，因此本地 tip 比遠端 tip 舊。

    第 4 點是「比對 tree hash」這個候選判準在真實資料上失敗的地方：本地 tip 的整棵樹
    與 main 上任何一筆 commit 都不相同（它少了別張卡的內容）。
    """
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    git(sandbox_repo, "remote", "add", "origin", str(remote))
    git(sandbox_repo, "push", "-q", "-u", "origin", "main")

    wt = tmp_path / "card-worktree"
    git(sandbox_repo, "worktree", "add", "-q", str(wt), "-b", BRANCH)
    (wt / "work.txt").write_text(WORK_CONTENT, encoding="utf-8")
    _c(wt, "card work")
    git(wt, "push", "-q", "-u", "origin", BRANCH)
    stale_local_tip = git(wt, "rev-parse", "HEAD").strip()

    (sandbox_repo / "other-card.txt").write_text("別張卡先進 main\n", encoding="utf-8")
    _c(sandbox_repo, "別張卡")
    git(sandbox_repo, "push", "-q", "origin", "main")

    git(wt, "merge", "-q", "--no-edit", "main")  # = gh pr update-branch（伺服器端）
    git(wt, "push", "-q", "origin", BRANCH)
    remote_tip = git(wt, "rev-parse", "HEAD").strip()

    git(sandbox_repo, "merge", "-q", "--squash", BRANCH)
    _c(sandbox_repo, "squash: card（被審 SHA 記在訊息裡）")
    git(sandbox_repo, "push", "-q", "origin", "main")

    git(wt, "reset", "-q", "--hard", stale_local_tip)  # 本機 ref 從沒被更新過

    return Env(
        repo=sandbox_repo,
        remote=remote,
        wt=wt,
        target=CleanupTarget(
            repo_root=sandbox_repo, card_id=CARD_ID, branch=BRANCH, worktree_path=wt
        ),
        registry=_empty_registry(),
        tip_before_cleanup=remote_tip,
    )


@pytest.fixture
def env_squash(tmp_path: Path, sandbox_repo: Path) -> Env:
    """squash 合併、乾淨、應當可安全收尾的情境（本卡之前它是恆拒的）。"""
    return _build_squash_env(tmp_path, sandbox_repo)


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


# --- R4-002：形狀面從「AST 規則」換成「資料流限制」 -------------------------
#
# 上一版只有一條 AST 規則：函式體內不得把 `trigger` 讀在結果紀錄之外，且不得出現
# 觸發者名稱的字面常數。查核者兩行就繞過了它——`locals()["trig" + "ger"]` 不是
# `ast.Name(trigger)`，`"rec" + "oncile"` 不是完整的字面常數，AST 兩條規則都不認得。
#
# 修法不是再多列幾條「也不准這樣寫」（那是軍備競賽：封堵得再多也只是把繞過成本
# 抬高），而是把那個值**移出破壞性函式體的 scope**：`execute_closeout_transition()`
# 收下 `trigger` 之後只做兩件事——呼叫 `_execute_closeout()`（簽章裡沒有 trigger），
# 拿回結果後 `replace(..., trigger=...)` 貼標籤。函式體裡因此沒有任何名為 trigger
# 的區域變數、自由變數或模組全域，動態名稱查表查不到東西。
#
# 三條測試分別釘住三件事，強度與邊界寫在 docs/WF_CLEANUP_GUARD1.md §4.0：
#   T1 名稱面：窮舉 CPython 的名稱表，證明「按名字拿」拿不到。
#   T2 值面：在每個步驟間隙探 frame，抓「換個名字夾帶進去」。
#   T3 呼叫端：把貼標籤那層的位元碼符號集合釘死，讓它藏不下任何機關。

#: 破壞性函式體**允許**載入的全域／內建名稱。
#:
#: 這是允許清單，不是禁止清單，差別在漏一個的後果：禁止清單漏掉 `locals` 就被繞
#: 過；允許清單漏掉一個合法的新名字只是轉紅，得有人回來把它加進來——而那正是要
#: 的複核動作。`locals`／`globals`／`getattr`／`vars`／`eval`／`sys` 等等不必逐一
#: 列進禁止清單，它們單純不在這裡面。
_BODY_ALLOWED_GLOBALS = frozenset({
    "CleanupGuardError", "CloseoutResult", "DESTRUCTIVE_ORDER", "GuardCheck",
    "GuardDecision", "REMOTE_DELETE_CAS_ID", "RemoteCardFacts",
    "SUBSEQUENT_OBLIGATION_STEPS", "_run", "bool", "classify_state",
    "conditional_delete_args", "default_git_runner", "evaluate_cleanup_guard",
    "observe", "recheck_remote_branch", "remaining_status_face_steps", "str", "tuple",
})

_TRIGGER_VALUES = frozenset({"release", "reconcile"})


def _all_code_objects(code):
    """`code` 及其所有巢狀 code object（comprehension／lambda／巢狀函式）。"""
    yield code
    for const in code.co_consts:
        if hasattr(const, "co_code"):
            yield from _all_code_objects(const)


def _loaded_globals(code) -> set[str]:
    """位元碼實際以**全域／內建**身分載入的名稱（不含屬性存取）。

    用 `dis` 而不是 `co_names`：後者把 `LOAD_ATTR` 的屬性名也混在一起，會逼得允許
    清單得列出每一個屬性名，於是任何無關的重構都讓它轉紅——一條天天轉紅的測試等
    於沒有測試。
    """
    out: set[str] = set()
    for sub in _all_code_objects(code):
        for ins in dis.get_instructions(sub):
            if ins.opname in ("LOAD_GLOBAL", "LOAD_NAME", "STORE_GLOBAL", "DELETE_GLOBAL"):
                out.add(ins.argval)
    return out


def test_the_destructive_body_cannot_name_the_trigger() -> None:
    """T1 名稱面：破壞性函式體內**沒有任何叫 trigger 的東西可以拿**。

    CPython 的名稱只可能從三張表來：`co_varnames`（區域變數，含參數）、
    `co_freevars`／`co_cellvars`（閉包）、`co_names`（全域與屬性）。`locals()`／
    `globals()`／`getattr()` 這些動態查法查的也是同一批表，不會憑空多出東西。所以
    只要三張表裡都沒有 `trigger`、模組層也沒有同名全域，動態名稱查表必然落空——
    這是窮舉，不是逐條堵。

    最後一條斷言是允許清單：函式體只能載入 `_BODY_ALLOWED_GLOBALS` 裡的全域名。
    查核者那個 `locals()["trig" + "ger"]` 會在這裡先轉紅，理由指名 `locals`。
    """
    body = cleanup._execute_closeout
    assert "trigger" not in inspect.signature(body).parameters, (
        "破壞性函式體又收下 trigger 了——資料流限制被還原成上一版的 AST 規則"
    )

    for sub in _all_code_objects(body.__code__):
        assert "trigger" not in sub.co_varnames, f"{sub.co_name} 有名為 trigger 的區域變數"
        assert "trigger" not in sub.co_freevars, f"{sub.co_name} 從閉包拿得到 trigger"
        assert "trigger" not in sub.co_cellvars, f"{sub.co_name} 把 trigger 裝進 cell"
        assert "trigger" not in sub.co_names, f"{sub.co_name} 以全域／屬性名參照 trigger"

    assert "trigger" not in vars(cleanup), (
        "模組層出現了 trigger 全域——`globals()['trigger']` 會因此拿得到值"
    )

    consts = [c for sub in _all_code_objects(body.__code__) for c in sub.co_consts]
    assert not [c for c in consts if isinstance(c, str) and c in _TRIGGER_VALUES], (
        "函式體出現觸發者名稱的字面常數"
    )

    strays = _loaded_globals(body.__code__) - _BODY_ALLOWED_GLOBALS
    assert not strays, (
        f"破壞性函式體載入了不在允許清單內的全域名稱：{sorted(strays)}。"
        "若是正當的新相依，請把它加進 _BODY_ALLOWED_GLOBALS 並在 review 說明；"
        "若它是 locals／globals／getattr／vars／eval／sys 之類的動態查名工具，"
        "那正是本條要擋的東西"
    )


def _carries_a_trigger_value(value, depth: int = 0) -> bool:
    """`value` 本身或其淺層容器元素裡，有沒有等於觸發者名稱的字串。

    覆蓋範圍**刻意寫死**：字串本身、以及三層以內的 tuple／list／set／dict 元素。
    藏進自訂物件屬性的夾帶不在覆蓋內（見 §4.0 的邊界說明）——那需要遍歷任意物件
    圖，代價與誤報率都不成比例。
    """
    if isinstance(value, str):
        return value in _TRIGGER_VALUES
    if depth >= 3:
        return False
    if isinstance(value, Mapping):
        return any(_carries_a_trigger_value(v, depth + 1)
                   for v in itertools.chain(value.keys(), value.values()))
    if isinstance(value, (tuple, list, set, frozenset)):
        return any(_carries_a_trigger_value(v, depth + 1) for v in value)
    return False


def test_the_destructive_body_frame_never_holds_a_trigger_value(env: Env) -> None:
    """T2 值面：**換個名字夾帶**也不行——按值抓，不按名字抓。

    T1 只保證「沒有叫 trigger 的東西」。一個把觸發者改名成 `mode_hint` 傳進來的
    版本會通過 T1，卻照樣分叉得起來。這條在**每個步驟間隙**回頭探破壞性函式體的
    frame，逐一檢查它當下的區域變數有沒有誰的值是 "release"／"reconcile"。

    反假綠：先斷言探針真的打在 `_execute_closeout` 的 frame 上、且至少打了四次
    （guard_passed ＋ 三個破壞性動作），否則「沒抓到」可能只是根本沒探到。
    """
    seen: list[str] = []

    def probing_hook(step: str) -> None:
        frame = sys._getframe(1)
        assert frame.f_code is cleanup._execute_closeout.__code__, (
            f"探針打在 {frame.f_code.co_name}，不是破壞性函式體——本案例形同不存在"
        )
        seen.append(step)
        carriers = {k: v for k, v in frame.f_locals.items()
                    if _carries_a_trigger_value(v)}
        assert not carriers, (
            f"步驟 {step} 時破壞性函式體的區域變數帶著觸發者的值：{sorted(carriers)}；"
            "改個名字夾帶進來，資料流限制就形同虛設"
        )

    remote = FakeRemoteState()
    result = execute_closeout_transition(
        env.target, trigger="release", registry=env.registry, card_body=CARD_BODY,
        remote_facts=remote.facts(), effect_writer=FakeEffectWriter(remote),
        occupancy_prober=free_prober, step_hook=probing_hook,
    )
    assert result.mode == "applied", result.blocking_reasons
    assert len(seen) >= 1 + len(DESTRUCTIVE_ORDER), f"探針只打了 {seen}"
    # 標籤本身仍要貼得上，否則「值不在裡面」可以靠「根本沒有標籤」達成
    assert result.trigger == "release"


def test_the_labelling_wrapper_is_pinned_to_call_and_relabel() -> None:
    """T3 呼叫端：貼標籤那一層**只准認得兩個名字**。

    資料流限制把 `trigger` 擋在破壞性函式體之外，代價是它落在了外面這一層——所以
    這一層必須小到藏不下東西。位元碼的符號表窮舉了它能碰到的一切：`co_names`（全域
    ＋屬性）、`co_varnames`（區域變數）、`co_consts`（常數）。把三者釘死之後，任何
    機關都得先讓其中一張表長出新東西：政策查表要有 dict 常數或全域名、`locals()`
    要有 `locals`、屬性分派要有屬性名——三者都會在這裡轉紅。
    """
    fn = cleanup.execute_closeout_transition
    code = fn.__code__

    assert set(code.co_names) == {"_execute_closeout", "replace"}, (
        f"貼標籤層碰到了預期外的名字：{sorted(code.co_names)}"
    )
    assert code.co_varnames == tuple(inspect.signature(fn).parameters), (
        "貼標籤層多了參數以外的區域變數——它應該只有一個運算式"
    )
    assert code.co_freevars == () and code.co_cellvars == ()

    consts = [c for c in code.co_consts if c is not fn.__doc__]
    for const in consts:
        # 只允許 None 與「關鍵字引數名稱的元組」（CPython 呼叫慣例產生的常數）
        assert const is None or (isinstance(const, tuple)
                                 and all(isinstance(x, str) for x in const)), (
            f"貼標籤層出現預期外的常數 {const!r}"
        )
    flat = {x for c in consts if isinstance(c, tuple) for x in c}
    assert not (flat & _TRIGGER_VALUES), "貼標籤層出現觸發者名稱的字面常數"


def test_a_dynamic_name_lookup_from_inside_the_body_finds_nothing(env: Env) -> None:
    """§4.0 說「動態名稱查表查不到」，這裡就是那句話的一次**實際嘗試且失敗**。

    查核者的原句是在函式體內寫 `locals()["trig" + "ger"]`。這條測試不改原始碼，改
    從步驟間隙拿到**同一個 frame**再查一次：`frame.f_locals` 與函式體內 `locals()`
    讀的是同一批 fast locals，查不到就是查不到。`f_globals` 同理。

    這條與 T1 的分工：T1 證明的是「表裡沒有」（靜態、窮舉），這條證明的是「真的去
    拿會拿不到」（動態、實例）。承重宣稱要附一個失敗的繞過實例，指的就是它。
    """
    attempts: list[str] = []

    def bypass_attempt(step: str) -> None:
        frame = sys._getframe(1)
        assert frame.f_code is cleanup._execute_closeout.__code__
        attempts.append(step)
        with pytest.raises(KeyError):
            _ = frame.f_locals["trig" + "ger"]      # 查核者的原句，一字未改
        with pytest.raises(KeyError):
            _ = frame.f_globals["trig" + "ger"]
        assert not hasattr(cleanup, "trig" + "ger")

    remote = FakeRemoteState()
    result = execute_closeout_transition(
        env.target, trigger="reconcile", registry=env.registry, card_body=CARD_BODY,
        remote_facts=remote.facts(), effect_writer=FakeEffectWriter(remote),
        occupancy_prober=free_prober, step_hook=bypass_attempt,
    )
    assert result.mode == "applied", result.blocking_reasons
    assert attempts, "一次都沒試到——本案例形同不存在"


def _independent_env(root: Path) -> Env:
    """在 `root` 底下自建一個與 `env` fixture 同構、但完全獨立的沙箱收尾情境。

    兩個 trigger 必須各自跑在**自己的**乾淨 repo 上：共用一個 repo 時第二次執行看
    到的是第一次留下的殘骸，兩者根本不是同一個情境，比較就沒有意義。
    """
    repo = root / "sandbox-repo"
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "wf-cli tests")
    (repo / "README.md").write_text("sandbox\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-q", "-m", "init")
    return _build_env(root, repo, merged=True)


_HEX40_RE = re.compile(r"\b[0-9a-f]{40}\b")


def _normalise(text: str, root: Path) -> str:
    """抹掉兩個獨立 repo 之間必然不同的東西：路徑與 commit SHA。"""
    return _HEX40_RE.sub("<SHA>", text.replace(str(root), "<ROOT>"))


def _closeout_fingerprint(result, *, root: Path, argv_log, writer_calls) -> dict:
    """一次收尾在**可觀測面**上的全貌，`trigger` 標籤本身刻意不含在內。"""
    return {
        "mode": result.mode,
        "decision_mode": result.decision.mode,
        "checks": [(c.check_id, c.outcome) for c in result.decision.checks],
        "performed": result.actions_performed,
        "skipped": result.actions_skipped_absent,
        "aborted": result.actions_aborted,
        "rechecks": [(c.check_id, c.outcome) for c in result.recheck_checks],
        "state_after": result.state_after,
        "remaining": result.remaining_status_face_steps,
        "obligations": result.outstanding_obligations,
        "blocking": tuple(_normalise(r, root) for r in result.blocking_reasons),
        "writer": tuple(writer_calls),
        "argv": tuple(tuple(_normalise(a, root) for a in argv) for argv in argv_log),
    }


@pytest.mark.parametrize(
    ("prober", "expected_mode"),
    [(free_prober, "applied"), (occupied_prober, "detect_only")],
)
def test_swapping_the_trigger_changes_nothing_but_the_label(
    tmp_path: Path, prober, expected_mode: str
) -> None:
    """換一個 trigger 值，**送出的 git 指令與寫入的效果逐字相同**。

    與上面 `test_decision_identical_for_release_and_reconcile` 的差別有二，兩者都
    是本條存在的理由：

    1. 那條只比對 `decision`（守衛的判定），比不到「守衛放行之後 executor 做了
       什麼」。一個只在 `trigger == "release"` 時才送出遠端刪除的實作，在那條測試
       下完全可以是綠的。本條逐字比對實際送進 git runner 的 argv 與 effect writer
       的呼叫序列。
    2. 那條讓兩次執行共用同一個 repo，第二次跑在第一次的殘骸上；本條給兩個
       trigger 各一個獨立沙箱，兩邊是同一個情境的兩份複本。

    放行與拒絕兩條路徑都測：只測放行的話，「拒絕理由依觸發者不同」會漏掉。
    """
    fingerprints = {}
    for trigger in ("release", "reconcile"):
        root = tmp_path / trigger
        env = _independent_env(root)
        remote = FakeRemoteState()
        writer = FakeEffectWriter(remote)
        argv_log: list[list[str]] = []
        result = execute_closeout_transition(
            env.target, trigger=trigger, registry=env.registry, card_body=CARD_BODY,
            remote_facts=remote.facts(), effect_writer=writer,
            runner=recording_runner(argv_log), occupancy_prober=prober,
        )
        assert result.trigger == trigger
        assert result.mode == expected_mode, result.blocking_reasons
        # 反假綠：放行案例必須真的走完三個破壞性動作，否則「兩邊相同」比的是兩次
        # 空跑——一個對兩個 trigger 都不刪的實作也會讓上面那個相等成立。
        if expected_mode == "applied":
            assert result.actions_performed == DESTRUCTIVE_ORDER
        fingerprints[trigger] = _closeout_fingerprint(
            result, root=root, argv_log=argv_log, writer_calls=writer.calls
        )

    assert fingerprints["release"] == fingerprints["reconcile"]


# ---------------------------------------------------------------------------
# 4. --force 在 reconcile 路徑確實不可用（不只是文件寫著）
# ---------------------------------------------------------------------------


_HEX40 = "0123456789abcdef0123456789abcdef01234567"


@pytest.mark.parametrize(
    "args",
    [
        ["push", "origin", "--delete", "x", "--force"],
        ["branch", "-D", "x"],
        ["worktree", "remove", "--force", "/tmp/x"],
        ["push", "--force-with-lease", "origin", "x"],
        ["clean", "-f"],
        # 以下四種是「看起來像租約、其實會退化成無條件刪除」的近似形態，
        # 逐一擋掉——它們才是這道防線真正的邊界，不是拼字明顯的 --force。
        # 裸 lease＝拿本機 remote-tracking ref 當期望值（可能是幾小時前的）
        ["push", "--force-with-lease=refs/heads/x", "origin", "--delete", "x"],
        # 短名不會被 git 認成 lease 目標，租約靜默失效
        ["push", f"--force-with-lease=x:{_HEX40}", "origin", "--delete", "x"],
        # 全零＝「期望 ref 不存在」，刪既有分支時是自相矛盾且 fail-open 的期望
        ["push", f"--force-with-lease=refs/heads/x:{'0' * 40}", "origin", "--delete", "x"],
        # 期望值不是 SHA（分支名／ref 名可被解析成任意當下值）
        ["push", "--force-with-lease=refs/heads/x:HEAD", "origin", "--delete", "x"],
        # 租約合法，但同一條指令另外夾帶了真正的 force
        ["push", f"--force-with-lease=refs/heads/x:{_HEX40}", "--force", "origin", "x"],
    ],
)
def test_force_flags_are_rejected_at_the_git_entrypoint(tmp_path: Path, args) -> None:
    with pytest.raises(CleanupGuardError):
        default_git_runner(tmp_path, args)


def test_the_conditional_delete_lease_is_the_only_permitted_force_flag(tmp_path: Path) -> None:
    """唯一開的窄口：帶明確期望 SHA 的條件式刪除，必須真的能送出去。

    這條與上面那組是一對——只有拒絕測試而沒有這條，把 `_forbid_force` 寫成「全擋」
    也會全綠，而那會讓遠端刪除完全發不出去（另一種靜默失效）。
    """
    lease = f"--force-with-lease=refs/heads/claude/X:{_HEX40}"
    assert cleanup.is_conditional_delete_lease(lease)
    # 走得進 subprocess：git 會因為 tmp_path 不是 repo 而失敗，但**不是**被守衛擋下
    result = default_git_runner(tmp_path, ["push", lease, "origin", "--delete", "claude/X"])
    assert isinstance(result, cleanup.GitResult)


def test_conditional_delete_args_refuses_to_degrade_into_an_unconditional_delete() -> None:
    target = CleanupTarget(
        repo_root=Path("/nowhere"), card_id="X", branch="claude/X", worktree_path=None
    )
    argv = cleanup.conditional_delete_args(target, _HEX40)
    assert argv == [
        "push", f"--force-with-lease=refs/heads/claude/X:{_HEX40}",
        "origin", "--delete", "claude/X",
    ]
    for bad in ("", "HEAD", "0" * 40, "not-a-sha"):
        with pytest.raises(CleanupGuardError):
            cleanup.conditional_delete_args(target, bad)


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


def _delete_pushes(log: list[list[str]]) -> list[list[str]]:
    """實際送出的遠端刪除指令。

    刻意用「argv[0] == push 且含 --delete」而不是比對固定前綴：前綴比對會在指令
    形狀一改（例如中間插入租約旗標）時**靜靜地一條都對不上**，讓「最多刪一次」之
    類的斷言變成恆真。
    """
    return [argv for argv in log if argv[:1] == ["push"] and "--delete" in argv]


def test_applied_run_sends_no_force_flag_other_than_the_delete_lease(env: Env) -> None:
    """放行路徑的 argv 逐一比對：唯一允許出現的 ``--force*`` 是刪除租約本身。"""
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
    assert not [a for a in flat if a in {"-f", "-D", "-M"}]
    forced = [a for a in flat if a.startswith("--force")]
    assert all(cleanup.is_conditional_delete_lease(a) for a in forced), forced
    assert ["branch", "-d", BRANCH] in log, "本地分支刪除應使用安全的 -d"

    # 租約的期望值必須是**這一次複驗讀到的 tip**，不是任意值也不是本機 ref
    pushes = _delete_pushes(log)
    assert len(pushes) == 1, pushes
    leases = [a for a in pushes[0] if a.startswith("--force-with-lease=")]
    assert leases == [f"--force-with-lease=refs/heads/{BRANCH}:{env.tip_before_cleanup}"], (
        f"遠端刪除沒有帶上複驗讀到的 tip：{pushes[0]}"
    )


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
    # 恰好一次：`<= 1` 在「一條都沒對上」時也會綠，而指令形狀一改就正好是那樣。
    assert len(_delete_pushes(log)) == 1, _delete_pushes(log)
    assert writer.calls.count("close_issue") <= 1
    assert writer.calls.count("write_release_terminal") <= 1
    assert writer.calls[-1] == "write_release_terminal"


def _is_local_branch_delete(argv: list[str]) -> bool:
    return argv[:2] == ["branch", "-d"]


def _is_remote_branch_delete(argv: list[str]) -> bool:
    return argv[:1] == ["push"] and "--delete" in argv


def _silently_noop_runner(log: list[list[str]], matches) -> object:
    """讓某個刪除指令**回報成功但實際沒做**。

    這不是假想：受保護分支、鏡像同步、最終一致的遠端都可能讓 `push --delete`
    回 0 而分支還在。此時效果（第 4 步）若照寫，就會產生「Issue 已關但分支仍在」
    ——正是卡面驗證明文禁止的半完成組合。

    比對用述詞而非固定前綴：前綴一旦與實際 argv 對不上，這個 runner 會退化成
    「什麼都沒攔到的透明代理」，測試照樣全綠而覆蓋整條消失。
    """

    def run(cwd: Path, args):
        argv = list(args)
        log.append(argv)
        if matches(argv):
            return cleanup.GitResult(0, "", "")
        return default_git_runner(cwd, argv)

    return run


@pytest.mark.parametrize(
    ("matches", "still_present"),
    [
        (_is_local_branch_delete, "local"),
        (_is_remote_branch_delete, "remote"),
    ],
)
def test_effect_is_withheld_when_cleanup_did_not_actually_complete(
    env: Env, matches, still_present: str
) -> None:
    remote = FakeRemoteState()
    writer = FakeEffectWriter(remote)
    log: list[list[str]] = []
    result = execute_closeout_transition(
        env.target, trigger="reconcile", registry=env.registry, card_body=CARD_BODY,
        remote_facts=remote.facts(), effect_writer=writer,
        runner=_silently_noop_runner(log, matches), occupancy_prober=free_prober,
    )
    assert [argv for argv in log if matches(argv)], (
        "假成功 runner 一條指令都沒攔到——它退化成了透明代理，本案例形同不存在"
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
            runner=_silently_noop_runner(log, lambda a: a[:2] == ["worktree", "remove"]),
            occupancy_prober=free_prober,
        )
    assert writer.calls == []
    assert not [a for argv in log for a in argv if a == "-D"]
    assert_work_intact(env)


def test_a_failing_worktree_removal_stops_the_run_instead_of_being_ignored(env: Env) -> None:
    """`git worktree remove` **回非 0**（不是假成功）時必須停下來。

    這條原本沒有：既有案例只覆蓋「回 0 卻沒做」，於是把失敗檢查整個拿掉的突變體
    活了下來——後果是一個移不掉的 worktree 被當成已移除，接著往下刪分支。

    斷言的是**停在哪一步**，不只是「有丟例外」：拿掉檢查之後這條路徑照樣會炸——
    只是晚一步，炸在 `branch -d`（分支還被 checkout 著）。只驗 `pytest.raises` 會
    因為錯誤的理由而綠，與上一輪 M30 同型。
    """
    remote = FakeRemoteState()
    writer = FakeEffectWriter(remote)
    log: list[list[str]] = []

    def failing(cwd: Path, args):
        argv = list(args)
        log.append(argv)
        if argv[:2] == ["worktree", "remove"]:
            return cleanup.GitResult(1, "", "fatal: 無法移除 worktree（模擬失敗）")
        return default_git_runner(cwd, argv)

    with pytest.raises(CleanupGuardError, match="worktree remove"):
        execute_closeout_transition(
            env.target, trigger="release", registry=env.registry, card_body=CARD_BODY,
            remote_facts=remote.facts(), effect_writer=writer,
            runner=failing, occupancy_prober=free_prober,
        )
    assert [a for a in log if a[:2] == ["worktree", "remove"]], (
        "失敗 runner 沒攔到 worktree remove，本案例形同不存在"
    )
    assert not [a for a in log if a[:2] == ["branch", "-d"]], (
        "worktree 移除失敗卻繼續往下刪分支——失敗檢查沒有真的擋住這一步"
    )
    assert not _delete_pushes(log)
    assert writer.calls == []
    assert_work_intact(env)


# ---------------------------------------------------------------------------
# 6.0 R4-002：每一條保險絲都要有行為測試走過
#
# M48 之所以能在兩輪查核之間存活，不是因為規則寫得不夠多，是因為它分叉的那條保險
# 絲（複驗回報可刪卻沒帶回期望 tip）**整份行為套件一次都沒走過**。形狀面的規則不
# 挑路徑，所以它撐住了；但形狀面被繞過時，底下就什麼都沒有。
#
# 下面兩條分別補上：一條真的把那條保險絲走一遍，一條防止下一條保險絲又被漏掉。
# ---------------------------------------------------------------------------


class _TiplessRecheck:
    """複驗回報「可以刪」卻不交出期望 tip——保險絲的觸發條件。

    這是被改壞的複驗（正常路徑下 `verdict == "delete"` 必帶 tip），所以要靠注入才
    到得了。到得了不代表它可以被略過：沒有期望 tip 就組不出租約，退回無條件刪除
    正是 R2-001 被打穿的那個版本。
    """

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, target, runner):
        self.calls += 1
        return cleanup.RemoteDeleteDecision(
            verdict="delete",
            check=cleanup.GuardCheck(
                cleanup.RECHECK_REMOTE_ID, "pass", "（注入）複驗說可刪，但沒帶回 tip", 2
            ),
            expected_tip=None,
        )


@pytest.mark.parametrize("trigger", ["release", "reconcile"])
def test_a_recheck_that_reports_deletable_without_a_tip_stops_the_run(
    env: Env, monkeypatch: pytest.MonkeyPatch, trigger: str
) -> None:
    """複驗沒帶回期望 tip 時**停下來**，不刪、不寫狀態面（M48 的行為覆蓋）。

    斷言的是「停在哪一步」而不只是「有丟例外」（M30／M41 的教訓）：worktree 與本地
    分支已經照順序處理完，遠端刪除**一條都沒送出**，遠端分支還在，第 4 步一個字
    都沒寫。兩個 trigger 各跑一次——這條保險絲要是依觸發者分叉，其中一邊會綠。
    """
    fake = _TiplessRecheck()
    monkeypatch.setattr(cleanup, "recheck_remote_branch", fake)

    remote = FakeRemoteState()
    writer = FakeEffectWriter(remote)
    log: list[list[str]] = []

    with pytest.raises(CleanupGuardError, match="期望 tip"):
        execute_closeout_transition(
            env.target, trigger=trigger, registry=env.registry, card_body=CARD_BODY,
            remote_facts=remote.facts(), effect_writer=writer,
            runner=recording_runner(log), occupancy_prober=free_prober,
        )

    assert fake.calls == 1, "注入的複驗沒被呼叫到——本案例形同不存在"
    assert [a for a in log if a[:2] == ["worktree", "remove"]], "根本沒走到破壞性動作"
    assert not _delete_pushes(log), "沒有期望 tip 卻還是送出了遠端刪除"
    assert _remote_branch_exists(env.repo, "origin", BRANCH), "遠端分支被刪掉了"
    assert writer.calls == [], "清理未完成卻寫了狀態面"
    assert remote.issue_open is True and remote.terminal_written is False


#: 破壞性函式體內每一條 `raise CleanupGuardError` ↔ 走過它的行為測試。
#:
#: key 是保險絲訊息的可辨識片段，value 是本模組內確實會走到該保險絲的測試函式名。
_FUSE_BEHAVIOURAL_COVERS = {
    "git worktree remove 失敗":
        "test_a_failing_worktree_removal_stops_the_run_instead_of_being_ignored",
    "git branch -d 失敗":
        "test_failed_worktree_removal_stops_before_touching_the_status_face",
    "複驗回報可刪卻沒有帶回期望 tip":
        "test_a_recheck_that_reports_deletable_without_a_tip_stops_the_run",
}


def test_every_fuse_in_the_destructive_body_has_a_registered_behavioural_cover() -> None:
    """新增一條保險絲卻沒有行為測試走過它 → 轉紅。

    這條**不驗**登記的測試是不是真的走到那條保險絲（那需要逐行追蹤，成本與誤判率
    都不划算），它驗的是「有沒有人被迫想過這件事」：M48 的成因是一條保險絲被寫下
    來、而沒有任何行為案例走過它，形狀面因此成了唯一防線。要求登記，就讓下一條保
    險絲不可能默默地只靠形狀面撐著。
    """
    source = textwrap.dedent(inspect.getsource(cleanup._execute_closeout))
    fn = ast.parse(source).body[0]

    fuses: list[str] = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Raise) or node.exc is None:
            continue
        call = node.exc
        if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                and call.func.id == "CleanupGuardError"):
            continue
        text = " ".join(
            part.value for arg in call.args for part in ast.walk(arg)
            if isinstance(part, ast.Constant) and isinstance(part.value, str)
        )
        fuses.append(text)

    assert len(fuses) == len(_FUSE_BEHAVIOURAL_COVERS), (
        f"破壞性函式體有 {len(fuses)} 條保險絲，登記表有 "
        f"{len(_FUSE_BEHAVIOURAL_COVERS)} 條：{fuses}"
    )
    for text in fuses:
        matched = [k for k in _FUSE_BEHAVIOURAL_COVERS if k in text]
        assert len(matched) == 1, f"保險絲「{text[:40]}…」在登記表裡找不到唯一對應"
        cover = _FUSE_BEHAVIOURAL_COVERS[matched[0]]
        assert callable(globals().get(cover)), f"登記的行為測試 {cover} 不存在"


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


# ---------------------------------------------------------------------------
# 6.2 R2-001：複驗**之後**、刪除送出**之前**的窗
# ---------------------------------------------------------------------------


def _runner_pushing_between_recheck_and_delete(other: Path, log: list[list[str]], state: dict):
    """在遠端刪除指令送進 subprocess 的前一刻，讓另一個 clone 推入新提交。

    注入點的選擇是這條測試的全部價值所在。`step_hook("after_delete_local_branch")`
    **不是**這個窗：那個時點在「遠端刪除這一步開始之前」，注入的提交在複驗跑的時候
    就已經存在，於是複驗自己就會拒絕——那條測試驗的是複驗本身，不是複驗與刪除之間
    的時間差。上一輪的實作在複驗與刪除之間沒有 compare-and-swap，查核者用的正是這
    個窗，而既有測試一條都沒轉紅。

    這裡改用 runner 攔截：`_run()` 會先組好含租約的完整 argv、送進 runner，再由
    runner 交給 subprocess。在 runner 裡注入，等於卡在「複驗已回傳可刪」與「git 真
    的被執行」之間——就是被打穿的那一段。
    """

    def run(cwd: Path, args):
        argv = list(args)
        if _is_remote_branch_delete(argv) and not state["injected"]:
            state["injected"] = True
            state["new_sha"] = _push_new_commit_from_other_clone(other)
        log.append(argv)
        return default_git_runner(cwd, argv)

    return run


def test_remote_delete_refused_when_the_tip_moves_between_recheck_and_push(
    env: Env, tmp_path: Path
) -> None:
    """R2-001：複驗回傳「可刪」之後、`push` 送出之前推入的新提交也不得被刪掉。

    複驗是**讀**，不是保證。關掉這段窗的是條件式刪除：複驗讀到的 tip 原樣成為
    ``--force-with-lease=refs/heads/<branch>:<tip>`` 的期望值，遠端在這之間變動過，
    git 在送出任何更新指令之前就以 ``(stale info)`` 拒絕。
    """
    other = _other_clone(tmp_path, env.remote)
    remote_state = FakeRemoteState()
    writer = FakeEffectWriter(remote_state)
    log: list[list[str]] = []
    state: dict = {"injected": False, "new_sha": ""}

    result = execute_closeout_transition(
        env.target, trigger="release", registry=env.registry, card_body=CARD_BODY,
        remote_facts=remote_state.facts(), effect_writer=writer,
        runner=_runner_pushing_between_recheck_and_delete(other, log, state),
        occupancy_prober=free_prober,
    )

    # 0) 反空轉：注入沒發生的話，底下每一條都會因為錯誤的理由而綠
    assert state["injected"], "注入沒有發生——本案例形同不存在"
    assert state["new_sha"] and state["new_sha"] != env.tip_before_cleanup

    # 1) **先斷言真正重要的那件事**：別人的提交還在。
    #    斷言順序刻意如此——租約被拿掉時，第一個轉紅的必須是「工作沒了」，而不是
    #    某個欄位少一筆。前者說得出後果，後者只說得出記帳不符。
    assert _remote_branch_exists(env.repo, "origin", BRANCH), "遠端分支連同新提交被刪掉了"
    assert _remote_tip(env.repo, BRANCH) == state["new_sha"]
    assert _content_recoverable_from_remote(tmp_path, env.remote, "cas") == RESCUED_WORK

    # 2) 複驗當時是**通過**的（這正是與 6.1 的差別），擋下刪除的是租約
    outcomes = [(c.check_id, c.outcome) for c in result.recheck_checks]
    assert outcomes == [
        (cleanup.RECHECK_REMOTE_ID, "pass"),
        (cleanup.REMOTE_DELETE_CAS_ID, "fail"),
    ], outcomes
    assert result.mode == "aborted", result
    assert result.actions_aborted == ("delete_remote_branch",)
    assert result.actions_performed == ("remove_worktree", "delete_local_branch")
    assert any(cleanup.REMOTE_DELETE_CAS_ID in r for r in result.blocking_reasons)

    # 3) 送出的確實是條件式刪除，且租約期望值是複驗讀到的那個 tip（不是新的）
    pushes = _delete_pushes(log)
    assert len(pushes) == 1, pushes
    assert f"--force-with-lease=refs/heads/{BRANCH}:{env.tip_before_cleanup}" in pushes[0]

    # 4) 效果扣住、狀態停在合法暫時態
    assert writer.calls == []
    assert remote_state.issue_open is True and remote_state.terminal_written is False
    assert result.state_after == "cleanup_in_progress"
    assert result.legal_state

    # 5) 重跑不會「第二次就刪掉」：前提複驗此時看到未併入的遠端 tip，直接純偵測
    resumed = execute_closeout_transition(
        env.target, trigger="reconcile", registry=env.registry, card_body=CARD_BODY,
        remote_facts=remote_state.facts(), effect_writer=writer, occupancy_prober=free_prober,
    )
    assert resumed.mode == "detect_only"
    assert any("merge_verified_remote" in r for r in resumed.blocking_reasons)
    assert _content_recoverable_from_remote(tmp_path, env.remote, "cas-resumed") == RESCUED_WORK


def test_a_rejected_conditional_delete_aborts_rather_than_raising(env: Env) -> None:
    """遠端拒絕刪除時的處置必須與守衛其餘拒絕路徑同型：aborted ＋ 效果扣住。

    不是丟例外（呼叫端拿不到結構化理由），也不是靜默略過（會讓 `applied` 說謊）。
    這裡用一個只讓刪除指令回非 0 的 runner，與「遠端真的拒絕」等價。
    """
    remote_state = FakeRemoteState()
    writer = FakeEffectWriter(remote_state)

    def refusing(cwd: Path, args):
        argv = list(args)
        if _is_remote_branch_delete(argv):
            return cleanup.GitResult(1, "", "! [rejected] (delete) -> x (stale info)")
        return default_git_runner(cwd, argv)

    result = execute_closeout_transition(
        env.target, trigger="reconcile", registry=env.registry, card_body=CARD_BODY,
        remote_facts=remote_state.facts(), effect_writer=writer,
        runner=refusing, occupancy_prober=free_prober,
    )
    assert result.mode == "aborted"
    assert result.actions_aborted == ("delete_remote_branch",)
    assert [c.check_id for c in result.recheck_checks][-1] == cleanup.REMOTE_DELETE_CAS_ID
    assert any("stale info" in r for r in result.blocking_reasons)
    assert writer.calls == [], "刪除被拒卻寫了狀態面"
    assert _remote_branch_exists(env.repo, "origin", BRANCH)
    assert result.state_after == "cleanup_in_progress"
    assert result.legal_state


def test_recheck_reports_absent_remote_branch_as_nothing_to_delete(env: Env) -> None:
    """二次確認的 `absent` 不是拒絕：遠端分支本來就沒了，跳過即可，不得誤報阻擋。"""
    git(env.repo, "push", "-q", "origin", "--delete", BRANCH)
    decision = cleanup.recheck_remote_branch(env.target, default_git_runner)
    assert decision.verdict == "absent"
    assert decision.check.outcome == "pass"
    assert decision.expected_tip is None, "沒有可刪對象卻帶回期望 tip＝組得出租約"


def test_recheck_refuses_when_remote_is_unreadable(env: Env) -> None:
    """讀不到遠端＝不知道 tip 是誰。不知道就不刪。"""

    def broken(cwd: Path, args):
        if list(args)[:1] == ["ls-remote"]:
            return cleanup.GitResult(128, "", "fatal: unable to access remote")
        return default_git_runner(cwd, args)

    decision = cleanup.recheck_remote_branch(env.target, broken)
    assert decision.verdict == "refuse"
    assert decision.check.outcome == "unobservable"
    assert decision.expected_tip is None


def test_recheck_hands_back_the_tip_it_judged(env: Env) -> None:
    """複驗必須把據以裁決的 tip 一起交出來——否則刪除只能自己再讀一次，窗又開了。"""
    decision = cleanup.recheck_remote_branch(env.target, default_git_runner)
    assert decision.verdict == "delete"
    assert decision.expected_tip == env.tip_before_cleanup


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


# ---------------------------------------------------------------------------
# 11. WF-CLEANUP-SQUASH-AWARE1：squash 之後「內容已在 main」的證明
#
# 卡面驗收第 2 條：**只證明它接受 squash 的情形不算**。因此本節的骨幹是一張矩陣，
# 每一種「內容不在 main」的形狀都必須落在 `diverged`，而且是拿真的 git 建出來的
# 真的 repo 跑，不是餵假 runner。
#
# 矩陣另外拿 `git merge-tree --write-tree` 當**獨立神諭**交叉比對：那是 git 自己對
# 「把這條分支併進 main 會不會改變任何東西」的答案，與本模組的路徑交集判準是兩套
# 完全不同的實作。兩者對每一格都必須同意——同意不證明兩者都對，但**不同意一定有
# 一個錯**，而那正是這裡要抓的東西。
# ---------------------------------------------------------------------------

def _c(repo: Path, msg: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg, env=fixed_date_env(SANDBOX_COMMIT_DATE))


def _squash_into_main(repo: Path, branch: str) -> None:
    """重現 GitHub squash 合併：main 上長出一筆帶著分支全部內容的**全新 commit**。"""
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--squash", branch)
    _c(repo, f"squash: {branch}")


def _s_merged_no_ff(repo: Path, b: str) -> None:
    git(repo, "checkout", "-qb", b)
    (repo / "f.txt").write_text("F\n", encoding="utf-8")
    _c(repo, "card work")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--no-ff", "--no-edit", b)


def _s_squash_updated(repo: Path, b: str) -> None:
    """strict 政策下的真實形狀：分支先 update-branch 跟上 main，再被 squash。"""
    git(repo, "checkout", "-qb", b)
    (repo / "f.txt").write_text("F\n", encoding="utf-8")
    _c(repo, "card work")
    git(repo, "checkout", "-q", "main")
    (repo / "o.txt").write_text("O\n", encoding="utf-8")
    _c(repo, "別張卡")
    git(repo, "checkout", "-q", b)
    git(repo, "merge", "-q", "--no-edit", "main")
    _squash_into_main(repo, b)


def _s_squash_stale_local(repo: Path, b: str) -> None:
    """#9／#63／#73 的真實形狀：本地 ref 停在 update-branch 之前，遠端才是完整的。

    update-branch 的 merge commit 是 GitHub 在伺服器端做的，本機那條 ref 從來沒被
    更新過——所以本地 tip 的**整棵樹**跟 main 上任何一筆 commit 都不相同。這正是
    「比對 tree hash」這個候選判準在真實資料上失敗的地方。
    """
    git(repo, "checkout", "-qb", b)
    (repo / "f.txt").write_text("F\n", encoding="utf-8")
    _c(repo, "card work")
    stale = git(repo, "rev-parse", b).strip()
    git(repo, "checkout", "-q", "main")
    (repo / "o.txt").write_text("O\n", encoding="utf-8")
    _c(repo, "別張卡")
    git(repo, "checkout", "-q", b)
    git(repo, "merge", "-q", "--no-edit", "main")
    _squash_into_main(repo, b)
    git(repo, "branch", "-f", b, stale)


def _s_squash_then_main_advances(repo: Path, b: str) -> None:
    git(repo, "checkout", "-qb", b)
    (repo / "f.txt").write_text("F\n", encoding="utf-8")
    _c(repo, "card work")
    _squash_into_main(repo, b)
    for i in range(3):
        (repo / f"x{i}.txt").write_text(f"x{i}\n", encoding="utf-8")
        _c(repo, f"後續 {i}")


def _s_never_merged(repo: Path, b: str) -> None:
    git(repo, "checkout", "-qb", b)
    (repo / "f.txt").write_text("F\n", encoding="utf-8")
    _c(repo, "card work")
    git(repo, "checkout", "-q", "main")
    (repo / "o.txt").write_text("O\n", encoding="utf-8")
    _c(repo, "別張卡")


def _s_new_commit_after_squash(repo: Path, b: str) -> None:
    """⚠️ 最危險的真實情境：卡合併之後有人又往同一條分支推了東西。"""
    git(repo, "checkout", "-qb", b)
    (repo / "f.txt").write_text("F\n", encoding="utf-8")
    _c(repo, "card work")
    _squash_into_main(repo, b)
    git(repo, "checkout", "-q", b)
    (repo / "f.txt").write_text("F\n合併之後才寫的新工作\n", encoding="utf-8")
    _c(repo, "squash 之後的新工作")


def _s_reverted_on_main(repo: Path, b: str) -> None:
    git(repo, "checkout", "-qb", b)
    (repo / "f.txt").write_text("F\n", encoding="utf-8")
    _c(repo, "card work")
    _squash_into_main(repo, b)
    git(repo, "rm", "-q", "f.txt")
    _c(repo, "main 又 revert 掉")


def _s_deletion_not_on_main(repo: Path, b: str) -> None:
    git(repo, "checkout", "-qb", b)
    git(repo, "rm", "-q", "README.md")
    _c(repo, "分支刪掉 README")
    git(repo, "checkout", "-q", "main")
    (repo / "o.txt").write_text("O\n", encoding="utf-8")
    _c(repo, "別張卡")


def _s_rename_hides_a_deletion(repo: Path, b: str) -> None:
    """⚠️ 釘住 ``--no-renames``：開著改名偵測時這一格會誤放行。

    分支把 README.md 改名為 DOCS.md（＝刪掉 README.md）；main 另外加了同內容的
    DOCS.md，但 README.md 仍在。改名偵測會把分支那一刪一增併成單一路徑 DOCS.md，
    於是「分支刪掉了 main 還留著的檔案」這件事整個從集合 A 裡消失。
    """
    git(repo, "checkout", "-qb", b)
    git(repo, "mv", "README.md", "DOCS.md")
    _c(repo, "分支改名 README -> DOCS")
    git(repo, "checkout", "-q", "main")
    (repo / "DOCS.md").write_text("sandbox\n", encoding="utf-8")
    _c(repo, "main 另外加了同內容的 DOCS.md，README.md 沒動")


def _s_conflicting_edit(repo: Path, b: str) -> None:
    git(repo, "checkout", "-qb", b)
    (repo / "README.md").write_text("分支版本\n", encoding="utf-8")
    _c(repo, "分支改 README")
    git(repo, "checkout", "-q", "main")
    (repo / "README.md").write_text("main 版本\n", encoding="utf-8")
    _c(repo, "main 改 README")


def _s_net_zero_never_merged(repo: Path, b: str) -> None:
    """⚠️ 這一格是**已知的誤放行**，刻意釘住讓它不能悄悄改變。

    分支有 commit、從未被合併，但相對共同祖先淨改動為零（做完又自己 revert）。
    祖先關係會拒絕它，本判準放行。損失的是那次嘗試的 commit 紀錄，檔案內容零損失。
    """
    git(repo, "checkout", "-qb", b)
    (repo / "f.txt").write_text("F\n", encoding="utf-8")
    _c(repo, "card work")
    git(repo, "rm", "-q", "f.txt")
    _c(repo, "分支自己 revert 回去")
    git(repo, "checkout", "-q", "main")
    (repo / "o.txt").write_text("O\n", encoding="utf-8")
    _c(repo, "別張卡")


#: (情境 id, 建構函式, 期望的 MergeProofKind)
PROOF_MATRIX = [
    ("merge 合併（--no-ff）", _s_merged_no_ff, "ancestor"),
    ("squash：分支已 update-branch 跟上", _s_squash_updated, "content_absorbed"),
    ("squash：本地 ref 停在 update-branch 前", _s_squash_stale_local, "content_absorbed"),
    ("squash 後 main 又前進 3 個 commit", _s_squash_then_main_advances, "content_absorbed"),
    ("完全未合併", _s_never_merged, "diverged"),
    ("squash 後分支又推了新提交", _s_new_commit_after_squash, "diverged"),
    ("squash 後 main 又 revert 掉", _s_reverted_on_main, "diverged"),
    ("分支刪檔、main 未刪", _s_deletion_not_on_main, "diverged"),
    ("改名掩蓋刪除（釘 --no-renames）", _s_rename_hides_a_deletion, "diverged"),
    ("同檔衝突、未合併", _s_conflicting_edit, "diverged"),
    ("淨零分支、從未合併（已知誤放行）", _s_net_zero_never_merged, "content_absorbed"),
]


@pytest.mark.parametrize(
    "label,build,expected", PROOF_MATRIX, ids=[m[0] for m in PROOF_MATRIX]
)
def test_content_proof_matrix(sandbox_repo: Path, label, build, expected) -> None:
    build(sandbox_repo, BRANCH)
    proof = cleanup.prove_content_in_main(
        cleanup.default_git_runner, sandbox_repo, BRANCH, "main"
    )
    assert proof.kind == expected, f"{label}：期望 {expected}，實得 {proof.kind}（{proof.detail}）"
    # 放行與否必須與三值語意一致：只有兩種證明放行。
    assert proof.outcome == ("pass" if expected in {"ancestor", "content_absorbed"} else "fail")


@pytest.mark.parametrize(
    "label,build,expected", PROOF_MATRIX, ids=[m[0] for m in PROOF_MATRIX]
)
def test_content_proof_agrees_with_merge_tree_oracle(
    sandbox_repo: Path, label, build, expected
) -> None:
    """獨立神諭：``git merge-tree --write-tree`` 說「併進去不改變任何東西」嗎。

    這是 git 自己算的三方合併結果，與本模組的路徑交集判準毫無共用實作。兩者對同一
    格不同意的話，至少有一個是錯的。
    """
    build(sandbox_repo, BRANCH)
    probe = subprocess.run(
        ["git", "-C", str(sandbox_repo), "merge-tree", "--write-tree", "main", BRANCH],
        capture_output=True, text=True, check=False,
    )
    if "unknown option" in probe.stderr or "usage:" in probe.stderr.lower():
        pytest.skip("這個 git 版本沒有 merge-tree --write-tree（需 2.38+）")
    main_tree = git(sandbox_repo, "rev-parse", "main^{tree}").strip()
    oracle_says_absorbed = (
        probe.returncode == 0 and probe.stdout.splitlines()[0].strip() == main_tree
    )
    proof = cleanup.prove_content_in_main(
        cleanup.default_git_runner, sandbox_repo, BRANCH, "main"
    )
    assert oracle_says_absorbed == (proof.outcome == "pass"), (
        f"{label}：神諭說 absorbed={oracle_says_absorbed}，"
        f"本判準說 {proof.kind}——兩者不同意，至少一個是錯的"
    )


def test_the_proof_is_the_only_thing_stopping_an_unmerged_branch_from_being_deleted(
    env_unmerged: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """⚠️ 突變注入：把判準換成恆真，未合併分支就真的被刪光。

    這一條驗的不是正常行為，而是**鑑別力**：若把判準拿掉什麼都不會改變，那它根本沒在
    保護任何東西，前面那些「它擋下了」的測試也就證明不了東西。這裡讓突變在沙箱裡真的
    執行到底——worktree 被移除、本地與遠端分支被刪、`WORK_CONTENT` 消失。

    正常判準下的同一個 `env_unmerged` 由 `test_refuses_when_branch_not_merged` 覆蓋，
    兩條合起來才是雙向的。
    """
    真判準 = cleanup.prove_content_in_main(
        cleanup.default_git_runner, env_unmerged.repo, BRANCH, "main"
    )
    assert 真判準.kind == "diverged", "前提：這條分支確實沒被合併"

    monkeypatch.setattr(
        cleanup, "prove_content_in_main",
        lambda *a, **k: cleanup.MergeProof("content_absorbed", "突變：恆真"),
    )
    remote = FakeRemoteState()
    result = execute_closeout_transition(
        env_unmerged.target, trigger="release", registry=env_unmerged.registry,
        card_body=CARD_BODY, remote_facts=remote.facts(),
        effect_writer=FakeEffectWriter(remote), occupancy_prober=free_prober,
    )
    assert result.mode == "applied", "突變沒有生效，這條測試就證明不了鑑別力"
    assert not env_unmerged.wt.exists()
    assert not _local_branch_exists(env_unmerged.repo, BRANCH)
    assert not _remote_branch_exists(env_unmerged.repo, "origin", BRANCH)


def test_a_squash_merged_branch_reaches_a_completed_closeout(env_squash: Env) -> None:
    """squash 合併的卡跑完整收尾：mode=applied、worktree／本地／遠端分支全部清掉。

    §3.5 生效之後這是**每一張卡**的形狀；在本卡之前它是恆拒的。
    """
    remote = FakeRemoteState()
    result = execute_closeout_transition(
        env_squash.target, trigger="release", registry=env_squash.registry,
        card_body=CARD_BODY, remote_facts=remote.facts(),
        effect_writer=FakeEffectWriter(remote), occupancy_prober=free_prober,
    )
    assert result.mode == "applied", result.blocking_reasons
    assert result.state_after == "completed"
    assert set(result.actions_performed) == set(DESTRUCTIVE_ORDER)
    assert not env_squash.wt.exists()
    assert not _local_branch_exists(env_squash.repo, BRANCH)
    assert not _remote_branch_exists(env_squash.repo, "origin", BRANCH)
    # 放行的是哪一條 disjunct 必須看得出來，不能只知道「通過了」。
    merged_checks = [
        c for c in result.decision.checks if c.check_id.startswith("merge_verified")
    ]
    assert len(merged_checks) == 2
    for c in merged_checks:
        assert c.outcome == "pass"
        assert "content_absorbed" in c.detail, c.detail


def test_a_branch_pushed_to_after_the_squash_is_still_refused(env_squash: Env) -> None:
    """⚠️ 卡面驗收第 2 條的正面取證：squash 合併之後又有人推東西上去，必須擋下。

    這是新判準最該擋、而舊判準在 squash 世界裡根本走不到的那一格：分支確實被合併過，
    但它現在**不只**是被合併的那份內容。
    """
    git(env_squash.wt, "reset", "-q", "--hard", env_squash.tip_before_cleanup)
    (env_squash.wt / "work.txt").write_text(
        WORK_CONTENT + "合併之後才寫的新工作\n", encoding="utf-8"
    )
    _c(env_squash.wt, "squash 之後的新工作")
    git(env_squash.wt, "push", "-q", "origin", BRANCH)

    remote = FakeRemoteState()
    result = execute_closeout_transition(
        env_squash.target, trigger="release", registry=env_squash.registry,
        card_body=CARD_BODY, remote_facts=remote.facts(),
        effect_writer=FakeEffectWriter(remote), occupancy_prober=free_prober,
    )
    assert result.mode == "detect_only", result.actions_performed
    assert result.actions_performed == ()
    assert env_squash.wt.exists()
    assert _local_branch_exists(env_squash.repo, BRANCH)
    assert _remote_branch_exists(env_squash.repo, "origin", BRANCH)
    assert any("diverged" in r for r in result.blocking_reasons), result.blocking_reasons


def test_the_recheck_uses_the_same_proof_as_the_precondition(env_squash: Env) -> None:
    """複驗與前提必須走同一個函式：任一邊單獨改寬或改嚴都會產生破口。"""
    src = inspect.getsource(cleanup.recheck_remote_branch)
    assert "prove_content_in_main" in src
    assert "--is-ancestor" not in src, "複驗仍自己寫了一條祖先判斷，會與前提漂移"
    decision = cleanup.recheck_remote_branch(env_squash.target, cleanup.default_git_runner)
    assert decision.verdict == "delete"
    assert decision.expected_tip == env_squash.tip_before_cleanup


def test_the_merge_merged_path_still_passes_via_ancestry(env: Env) -> None:
    """merge 合併的路徑仍然可用（#48 就是這樣收尾的），且走的是**祖先**那一條。

    新舊判準的關係是 OR：舊判準沒有被換掉，只是在它答不出來的時候多了第二條路。
    """
    decision = guard(env)
    assert decision.mode == "proceed"
    for cid in ("merge_verified_local", "merge_verified_remote"):
        check = next(c for c in decision.checks if c.check_id == cid)
        assert "證明=ancestor" in check.detail, check.detail


def test_the_squash_merged_path_passes_via_content_absorption(env_squash: Env) -> None:
    """OR 的另一邊：squash 之後放行的是 `content_absorbed`，而且報告寫得出來是哪一條。"""
    decision = guard(env_squash)
    assert decision.mode == "proceed"
    for cid in ("merge_verified_local", "merge_verified_remote"):
        check = next(c for c in decision.checks if c.check_id == cid)
        assert "證明=content_absorbed" in check.detail, check.detail
