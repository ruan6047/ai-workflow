"""R1-002：``wfcli handoff --next-stage release`` 接上 WF-CLEANUP-GUARD1 的守衛。

查核者 R1-002 指出 `execute_closeout_transition()` 寫好了卻**沒有任何呼叫點**。本檔
證明的是「那條路徑真的經過那個 executor」，不是只驗回傳碼：

- 放行案例同時斷言**真實副作用**（worktree 目錄消失、本地與遠端分支消失、Issue 被
  關、交付狀態變 🏁完成）——這些只有真的跑過 executor 才會發生；
- 另以 spy 攔截 `handoff_cmd.execute_closeout_transition`（**委派給真函式**，不是
  替身）確認它確實被呼叫、且 `trigger="release"`；
- 順序斷言直接記錄「寫每一個欄位的當下，待刪分支還在不在」，證明終態不先於清理。

破壞性動作全部發生在 pytest `tmp_path` 沙箱 repo 與 bare remote 內，不碰任何真實
專案。GitHub 側由 `FakeGhRunner` 的子類別模擬（本檔自帶，未改動 `fake_gh.py`）。

**與 reconcile 的界線**：本輪只接 `release`。`reconcile` 子命令目前不存在於
`cli.py`，其 `--apply` 白名單第 2 條在 #16 §5.2 仍標記 reserved；那條接線歸 #16 §9
的 G 卡。因此 **reconcile 側尚未受守衛保護**，核心痛點只解決了一半。
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest
from wf_cli import cleanup
from wf_cli.cli import build_parser
from wf_cli.commands import assign_cmd, handoff_cmd, open_cmd
from wf_cli.project import (
    ensure_fields,
    find_item_by_card_id,
    list_items,
    resolve_project,
    set_field_value,
)

from .conftest import git
from .fake_gh import FakeGhRunner

CARD_ID = "WF-RELEASE-SANDBOX1"
BRANCH = "claude/WF-RELEASE-SANDBOX1"
REPO = "acme/workflow"
BASE_TARGET = ["--owner", "acme", "--project", "1", "--repo", REPO]
WORK_CONTENT = "committed work\n"


def _is_remote_branch_delete(argv: list[str]) -> bool:
    """遠端刪除指令的形狀比對。

    刻意不用固定前綴：條件式刪除在 ``push`` 後面插了租約旗標，任何 ``argv[:3] ==
    [...]`` 的寫法都會靜靜地一條都對不上，讓攔截型 runner 退化成透明代理而測試照
    樣全綠。攔到幾條由呼叫端另外斷言。
    """
    return argv[:1] == ["push"] and "--delete" in argv


class ReleaseGhRunner(FakeGhRunner):
    """補上 `issue view --json state` 與 `issue close`。

    這兩條是本輪新增的讀寫路徑（第 4 步要知道 Issue 開著沒、並負責關它）。刻意寫在
    本檔而不是擴充 `fake_gh.py`——後者由現役卡 WF-CLI-ROUTING-TIER1 佔用。
    """

    def __init__(self) -> None:
        super().__init__()
        self.issue_states: dict[int, str] = {}
        self.closed_issues: list[int] = []
        #: 設為 True 時 `issue view` 直接失敗，用來驗 fail-closed。
        self.issue_view_broken = False

    def execute(self, args, input: str | None = None) -> str:  # type: ignore[override]
        args = list(args)
        if args[:2] == ["issue", "view"]:
            if self.issue_view_broken:
                from wf_cli.gh import GhError

                raise GhError(args, 1, "simulated: gh issue view failed")
            number = int(args[2])
            return json.dumps({"state": self.issue_states.get(number, "OPEN")})
        if args[:2] == ["issue", "close"]:
            number = int(args[2])
            self.closed_issues.append(number)
            self.issue_states[number] = "CLOSED"
            return ""
        return super().execute(args, input)


@dataclass
class Env:
    repo: Path
    remote: Path
    wt: Path
    runner: ReleaseGhRunner
    issue_number: int


def run_cli(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


def _open_argv(card_id: str) -> list[str]:
    return [
        "open", *BASE_TARGET, card_id,
        "--feature", "收尾清理接線示範",
        "--tier", "T4",
        "--db-scope", "none",
        "--core-pain", "痛點文字",
        "--service-goal", "服務的原始目標文字",
        "--resources", "file:cli/src/wf_cli/cleanup.py",
    ]


def handoff_argv(card_id: str, sha: str, **overrides) -> list[str]:
    defaults: dict[str, object] = {
        "--to": "封存",
        "--next-stage": "release",
        "--evidence": "本檔的沙箱實跑",
    }
    defaults.update(overrides)
    argv = ["handoff", *BASE_TARGET, card_id, "--source-sha", sha]
    for key, value in defaults.items():
        if isinstance(value, bool):
            if value:
                argv.append(key)
        else:
            argv += [key, str(value)]
    return argv


def local_branch_exists(repo: Path, branch: str = BRANCH) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", branch],
        capture_output=True, text=True, check=False,
    )
    return proc.returncode == 0 and bool(proc.stdout.strip())


def remote_branch_exists(repo: Path, branch: str = BRANCH) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo), "ls-remote", "--heads", "origin", branch],
        capture_output=True, text=True, check=False,
    )
    return proc.returncode == 0 and bool(proc.stdout.strip())


def card_fields(runner: ReleaseGhRunner) -> dict:
    project = resolve_project(runner, "acme", 1)
    item = find_item_by_card_id(list_items(runner, project), CARD_ID)
    assert item is not None
    return item.fields


@pytest.fixture
def env(tmp_path: Path, sandbox_repo: Path, monkeypatch: pytest.MonkeyPatch) -> Env:
    """已 merge、乾淨、狀態面停在 📦已合併 的收尾情境（真 git ＋ 假 GitHub）。"""
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
    git(sandbox_repo, "merge", "-q", "--no-ff", "-m", "merge card", BRANCH)
    git(sandbox_repo, "push", "-q", "origin", "main")

    runner = ReleaseGhRunner()
    for module in (open_cmd, assign_cmd, handoff_cmd):
        monkeypatch.setattr(module, "default_runner", runner)
    # lsof 全機掃描在測試裡又慢又依賴環境；只換探針，守衛其餘部分照跑真的。
    monkeypatch.setattr(cleanup, "lsof_cwd_prober", lambda _p: ("free", "測試探針"))

    assert run_cli(_open_argv(CARD_ID)) == 0
    assert run_cli([
        "assign", *BASE_TARGET, CARD_ID,
        "--assignee", "Claude@Claude Code",
        "--branch", BRANCH,
        "--worktree", str(wt),
    ]) == 0
    project = resolve_project(runner, "acme", 1)
    fields = ensure_fields(runner, "acme", 1)
    item = find_item_by_card_id(list_items(runner, project), CARD_ID)
    assert item is not None and item.issue_number is not None
    set_field_value(runner, project, item.item_id, fields["交付狀態"], "📦已合併")

    return Env(repo=sandbox_repo, remote=remote, wt=wt, runner=runner,
               issue_number=item.issue_number)


def head_sha(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD").strip()


# ---------------------------------------------------------------------------
# 1. 接線本體：release 真的走過 executor，且順序是「清理 → 狀態面」
# ---------------------------------------------------------------------------


def test_release_with_cleanup_goes_through_the_shared_executor(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[str] = []
    real = handoff_cmd.execute_closeout_transition

    def spy(target, **kwargs):
        # 委派給真函式：這是攔截，不是替身。若換成假的，下面的副作用斷言全會壞。
        seen.append(kwargs["trigger"])
        return real(target, **kwargs)

    monkeypatch.setattr(handoff_cmd, "execute_closeout_transition", spy)

    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo), "--cleanup": True}))

    assert rc == 0
    assert seen == ["release"], "release 沒有經過共用的 executor"
    # 真實副作用：權威清單第 2 步的三個刪除動作都發生了
    assert not env.wt.exists()
    assert not local_branch_exists(env.repo)
    assert not remote_branch_exists(env.repo)
    # 第 4 步：Issue 關閉 ＋ 終態落地
    assert env.runner.closed_issues == [env.issue_number]
    assert card_fields(env.runner)["交付狀態"] == "🏁完成"


def test_terminal_status_is_written_only_after_the_branch_is_gone(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """順序不是靠 handoff 自律，是靠 executor 只在清理完成後才呼叫 effect writer。

    這裡在每次欄位寫入的當下記錄「待刪分支還在不在」，因此若哪天有人把終態寫回
    清理之前，這條會直接抓到，而不必依賴閱讀程式碼的順序。
    """
    observed: list[tuple[str, bool]] = []
    real_set = handoff_cmd.set_field_value

    def spy(runner, project, item_id, field, value):
        observed.append((str(value), local_branch_exists(env.repo)))
        return real_set(runner, project, item_id, field, value)

    monkeypatch.setattr(handoff_cmd, "set_field_value", spy)

    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo), "--cleanup": True}))
    assert rc == 0
    terminal_writes = [(v, present) for v, present in observed if v == "🏁完成"]
    assert terminal_writes, "沒有觀察到終態寫入，這條斷言會變成空頭支票"
    assert all(not present for _, present in terminal_writes), (
        "終態在分支還在的時候就被寫下去了——這正是三段分離要禁止的組合"
    )
    assert env.runner.closed_issues == [env.issue_number]


# ---------------------------------------------------------------------------
# 2. 預設不清理：既有使用者的行為不變，但代價要講明
# ---------------------------------------------------------------------------


def test_release_without_cleanup_flag_deletes_nothing(env: Env, capsys) -> None:
    """預設值取較安全的一邊：沒要求就不刪。"""
    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo)}))
    assert rc == 0
    assert env.wt.exists()
    assert (env.wt / "work.txt").read_text(encoding="utf-8") == WORK_CONTENT
    assert local_branch_exists(env.repo)
    assert remote_branch_exists(env.repo)
    assert env.runner.closed_issues == []
    # 既有行為完全不變：狀態面照寫
    assert card_fields(env.runner)["交付狀態"] == "🏁完成"
    # 但它造出的是 illegal_terminal_before_cleanup，必須講明而非靜靜維持原狀
    assert "illegal_terminal_before_cleanup" in capsys.readouterr().err


def test_cleanup_after_a_status_only_release_is_refused_as_illegal(env: Env) -> None:
    """未帶 --cleanup 的 release 之後再補 --cleanup 會被擋——警示裡講的就是這件事。

    守衛刻意不自動修復非法態；這條把那個代價釘成可執行的事實，免得文件與實作各說
    各話。
    """
    assert run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                                **{"--repo-path": str(env.repo)})) == 0
    env.runner.issue_states[env.issue_number] = "CLOSED"

    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo), "--cleanup": True}))
    assert rc == 5
    assert env.wt.exists()
    assert local_branch_exists(env.repo)
    assert remote_branch_exists(env.repo)


# ---------------------------------------------------------------------------
# 3. 守衛擋下時：什麼都沒刪，狀態面也一個字都沒寫
# ---------------------------------------------------------------------------


def test_uncommitted_changes_block_release_and_leave_everything_intact(env: Env) -> None:
    (env.wt / "draft.txt").write_text("尚未提交的草稿\n", encoding="utf-8")

    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo), "--cleanup": True}))

    assert rc == 5
    assert (env.wt / "draft.txt").read_text(encoding="utf-8") == "尚未提交的草稿\n"
    assert (env.wt / "work.txt").read_text(encoding="utf-8") == WORK_CONTENT
    assert local_branch_exists(env.repo)
    assert remote_branch_exists(env.repo)
    # 狀態面停在原處：沒有終態、Issue 沒關
    assert card_fields(env.runner)["交付狀態"] == "📦已合併"
    assert env.runner.closed_issues == []


def test_unmerged_branch_blocks_release(env: Env) -> None:
    (env.wt / "later.txt").write_text("merge 之後才做的工作\n", encoding="utf-8")
    git(env.wt, "add", "later.txt")
    git(env.wt, "commit", "-q", "-m", "post-merge work")
    git(env.wt, "push", "-q", "origin", BRANCH)

    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo), "--cleanup": True}))

    assert rc == 5
    assert env.wt.exists()
    assert local_branch_exists(env.repo)
    assert remote_branch_exists(env.repo)
    assert card_fields(env.runner)["交付狀態"] == "📦已合併"


def test_unreadable_issue_state_fails_closed(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """讀不到 Issue 開關狀態就不動手——猜錯的後果是「自稱完成卻留著開著的 Issue」。

    只斷言 exit code 5 是不夠的：把 `state is None` 的分支拔掉後，`issue_open=None`
    會讓狀態分類**碰巧**判成非法態而同樣回 5（突變測試 M30 因此存活過一輪）。因此
    這裡改斷言「破壞性機器根本沒被啟動」——讀取失敗必須在進入 executor 之前就擋下。
    """
    started: list[str] = []
    real = handoff_cmd.execute_closeout_transition

    def spy(target, **kwargs):
        started.append(kwargs["trigger"])
        return real(target, **kwargs)

    monkeypatch.setattr(handoff_cmd, "execute_closeout_transition", spy)
    env.runner.issue_view_broken = True

    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo), "--cleanup": True}))
    assert rc == 5
    assert started == [], "Issue 狀態讀不到卻仍然啟動了收尾 executor"
    assert env.wt.exists()
    assert local_branch_exists(env.repo)
    assert card_fields(env.runner)["交付狀態"] == "📦已合併"


def test_release_fails_when_cleanup_reported_success_but_did_not_complete(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """遠端刪除回報成功、分支卻還在（受保護分支、鏡像同步、最終一致）。

    executor 此時刻意扣住第 4 步；CLI 這一層必須跟著回非 0，否則整條路徑會在狀態面
    沒寫、Issue 沒關的情況下對操作者宣稱成功（突變測試 M32）。
    """
    real_runner = cleanup.default_git_runner
    intercepted: list[list[str]] = []

    def lying_runner(cwd: Path, args):
        argv = list(args)
        if _is_remote_branch_delete(argv):
            intercepted.append(argv)
            return cleanup.GitResult(0, "", "")  # 回 0 但什麼也沒做
        return real_runner(cwd, argv)

    monkeypatch.setattr(cleanup, "default_git_runner", lying_runner)

    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo), "--cleanup": True}))

    assert intercepted, "假成功 runner 一條刪除指令都沒攔到，本案例形同不存在"
    assert rc == 5
    assert remote_branch_exists(env.repo), "前提設定失敗：遠端分支應該還在"
    assert card_fields(env.runner)["交付狀態"] == "📦已合併"
    assert env.runner.closed_issues == []


# ---------------------------------------------------------------------------
# 4. 清理中途失敗時，狀態面停在哪裡
# ---------------------------------------------------------------------------


def test_status_face_stays_put_when_the_remote_delete_is_aborted(
    env: Env, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R1-001 的情境走完整條 CLI：本機清理已完成、遠端刪除被拒。

    monkeypatch 只控制**時機**（在複驗前一刻讓另一個 clone 推新提交），複驗本身跑
    的是真函式、看到的是真的被換掉的 tip。

    要證明的是：狀態面**完全沒被寫**。卡停在 📦已合併、Issue 仍開著、iteration 與
    最後交接都沒動；本機資源部分完成是合法暫時態，重跑會重新觀測。
    """
    other = tmp_path / "other-clone"
    subprocess.run(["git", "clone", "-q", str(env.remote), str(other)], check=True)
    git(other, "config", "user.email", "other@example.com")
    git(other, "config", "user.name", "another clone")

    real_recheck = cleanup.recheck_remote_branch

    def push_then_recheck(target, runner):
        git(other, "checkout", "-q", "-B", BRANCH, f"origin/{BRANCH}")
        (other / "rescue.txt").write_text("別人的新工作\n", encoding="utf-8")
        git(other, "add", "rescue.txt")
        git(other, "commit", "-q", "-m", "work pushed during the window")
        git(other, "push", "-q", "origin", BRANCH)
        return real_recheck(target, runner)

    monkeypatch.setattr(cleanup, "recheck_remote_branch", push_then_recheck)

    before_fields = dict(card_fields(env.runner))
    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo), "--cleanup": True}))

    assert rc == 5
    # 新提交還在遠端
    assert remote_branch_exists(env.repo)
    verify = tmp_path / "verify-clone"
    subprocess.run(["git", "clone", "-q", "-b", BRANCH, str(env.remote), str(verify)], check=True)
    assert (verify / "rescue.txt").read_text(encoding="utf-8") == "別人的新工作\n"
    # 狀態面原封不動
    after_fields = card_fields(env.runner)
    assert after_fields["交付狀態"] == "📦已合併"
    assert after_fields.get("最後交接") == before_fields.get("最後交接")
    assert after_fields.get("owner") == before_fields.get("owner")
    assert env.runner.closed_issues == []


def test_status_face_stays_put_when_the_tip_moves_between_recheck_and_push(
    env: Env, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R2-001 走完整條 CLI：複驗**通過**之後、刪除送出之前，別人推了新提交。

    與上一條的差別只在**注入時機**，但那正是被打穿的地方：上一條在複驗前注入，複驗
    自己會拒絕；這一條在複驗之後注入，只剩條件式刪除的租約能接住。CLI 這一層必須跟
    著回非 0，且狀態面一個字都沒寫。
    """
    other = tmp_path / "other-clone"
    subprocess.run(["git", "clone", "-q", str(env.remote), str(other)], check=True)
    git(other, "config", "user.email", "other@example.com")
    git(other, "config", "user.name", "another clone")

    real_runner = cleanup.default_git_runner
    state: dict = {"injected": False, "new_sha": ""}

    def inject_then_run(cwd: Path, args):
        argv = list(args)
        if _is_remote_branch_delete(argv) and not state["injected"]:
            state["injected"] = True
            git(other, "checkout", "-q", "-B", BRANCH, f"origin/{BRANCH}")
            (other / "rescue.txt").write_text("別人的新工作\n", encoding="utf-8")
            git(other, "add", "rescue.txt")
            git(other, "commit", "-q", "-m", "work pushed after the recheck passed")
            git(other, "push", "-q", "origin", BRANCH)
            state["new_sha"] = git(other, "rev-parse", "HEAD").strip()
        return real_runner(cwd, argv)

    monkeypatch.setattr(cleanup, "default_git_runner", inject_then_run)

    before_fields = dict(card_fields(env.runner))
    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo), "--cleanup": True}))

    assert state["injected"], "注入沒有發生——本案例形同不存在"
    assert rc == 5
    assert remote_branch_exists(env.repo)
    verify = tmp_path / "verify-cas-clone"
    subprocess.run(["git", "clone", "-q", "-b", BRANCH, str(env.remote), str(verify)], check=True)
    assert (verify / "rescue.txt").read_text(encoding="utf-8") == "別人的新工作\n"
    after_fields = card_fields(env.runner)
    assert after_fields["交付狀態"] == "📦已合併"
    assert after_fields.get("最後交接") == before_fields.get("最後交接")
    assert env.runner.closed_issues == []


# ---------------------------------------------------------------------------
# 5. 旗標本身的邊界
# ---------------------------------------------------------------------------


def test_cleanup_requires_repo_path(env: Env) -> None:
    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo), **{"--cleanup": True}))
    assert rc == 2
    assert env.wt.exists()
    assert card_fields(env.runner)["交付狀態"] == "📦已合併"


def test_cleanup_is_release_only(env: Env) -> None:
    rc = run_cli(handoff_argv(
        CARD_ID, head_sha(env.repo),
        **{"--cleanup": True, "--repo-path": str(env.repo), "--next-stage": "review"},
    ))
    assert rc == 2
    assert env.wt.exists()
    assert local_branch_exists(env.repo)


def test_cleanup_refuses_when_the_card_has_no_registered_branch(env: Env) -> None:
    project = resolve_project(env.runner, "acme", 1)
    fields = ensure_fields(env.runner, "acme", 1)
    item = find_item_by_card_id(list_items(env.runner, project), CARD_ID)
    assert item is not None
    set_field_value(env.runner, project, item.item_id, fields["分支worktree"], "—")

    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo), "--cleanup": True}))
    assert rc == 2
    assert local_branch_exists(env.repo)
    assert card_fields(env.runner)["交付狀態"] == "📦已合併"


def test_no_force_flag_on_the_release_path(env: Env) -> None:
    """接線沒有順手開一個強制旗標的後門。"""
    parser = build_parser()
    handoff = parser._subparsers._group_actions[0].choices["handoff"]  # type: ignore[attr-defined]
    options = [o for a in handoff._actions for o in a.option_strings]
    assert not [o for o in options if o.startswith("--force") or o == "-f"]
    assert "--cleanup" in options
