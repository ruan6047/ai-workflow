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
from wf_cli.card import format_branch_worktree
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
    # 能力層級走 WF-CLI-ROUTING-TIER1 的必填路由旗標。值刻意反映這張沙箱卡本身的性質
    # 而非佔位字串：它是 T4，且做的是刪 worktree／本地與遠端分支、關 Issue 這類不可逆
    # 動作，故執行取高階型；AI_WORKFLOW.md §2「T4 紅線＝T3 ＋ 跨家族或人工審核」，
    # 查核同取高階型。
    return [
        "open", *BASE_TARGET, card_id,
        "--feature", "收尾清理接線示範",
        "--tier", "T4",
        "--exec-capability", "高階型",
        "--exec-capability-reason", "不可逆的破壞性清理，刪 worktree 與本地及遠端分支並關 Issue",
        "--review-capability", "高階型",
        "--review-capability-reason", "T4 紅線，須跨家族或人工查核",
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


def card_body(runner: ReleaseGhRunner) -> str:
    project = resolve_project(runner, "acme", 1)
    item = find_item_by_card_id(list_items(runner, project), CARD_ID)
    assert item is not None
    return item.body


def cleanup_log_lines(runner: ReleaseGhRunner) -> list[str]:
    """卡片 Log 裡由收尾留痕（非終態）寫下的行。

    刻意與 ``handoff by wf-cli`` 的交接行分開取：R3-01 要的正是「有一筆做過什麼的紀錄，
    但它不是交接、不是終態」，兩者混在一起數就分不出來了。
    """
    return [ln for ln in card_body(runner).splitlines() if "cleanup by wf-cli" in ln]


def handoff_log_lines(runner: ReleaseGhRunner) -> list[str]:
    return [ln for ln in card_body(runner).splitlines() if "handoff by wf-cli" in ln]


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
    project = resolve_project(runner, "acme", 1)
    fields = ensure_fields(runner, "acme", 1)
    item = find_item_by_card_id(list_items(runner, project), CARD_ID)
    assert item is not None and item.issue_number is not None

    # 註冊欄走**真的** `wfcli assign`。
    #
    # ⚠️ 上一輪這裡是直接 `set_field_value` 繞過 assign，理由是「沙箱 repo 的 origin
    # 是 tmp_path 底下的 bare 路徑，導不出 owner/repo，閘門 fail-closed 拒絕」——那條
    # 限制**來自把歸屬建立在 origin 反推上**，而需求方 2026-08-13 裁定歸屬改由 slug
    # 宣告表達（`docs/ROADMAP.md` §1.5）。origin 是什麼形狀已不再參與歸屬判定，於是
    # 這條繞道跟著消失，`assign` 這條指令路徑的覆蓋**被還回來**。
    #
    # 沙箱的 origin 仍然刻意留成本機 bare 路徑（偽造 GitHub 形狀會讓 cleanup 的
    # ls-remote／push --delete 打向真實網路）；它現在只會讓軸 B 判
    # `observed_repo_unidentifiable`——也就是「這台機器說不出這個 worktree 屬於誰」，
    # 而那不擋人。
    assert run_cli([
        "assign", *BASE_TARGET, CARD_ID,
        "--assignee", "Claude@Claude Code",
        "--branch", BRANCH,
        "--worktree", str(wt),
        "--actual-capability", "高階型",
    ]) == 0
    set_field_value(runner, project, item.item_id, fields["交付狀態"], "📦已合併")
    assert card_fields(runner)["分支worktree"] == format_branch_worktree(BRANCH, str(wt))

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


def test_repo_path_without_cleanup_is_refused_and_writes_nothing(env: Env, capsys) -> None:
    """WF-RELEASE-NO-CLEANUP-REFUSE1：看得見資源就不准製造非法態。

    先前這條測的是「預設值取較安全的一邊：沒要求就不刪」。⛔ 那個理由已被推翻——
    不可逆的那一半早就被 ``cleanup.AUTHORITY_BY_PROOF`` 以證明分級中和（只有分支
    已證明是 main 祖先時才刪分支，squash 只授權 remove_worktree，diverged 與
    unobservable 皆為空集合），⇒ 預設選的那一邊產生的才是比較不可回復的狀態。
    """
    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo)}))
    assert rc == 2
    # ⭐ 拒絕必須是乾淨的：資源全在、狀態面一個字都沒寫
    assert env.wt.exists()
    assert (env.wt / "work.txt").read_text(encoding="utf-8") == WORK_CONTENT
    assert local_branch_exists(env.repo)
    assert remote_branch_exists(env.repo)
    assert env.runner.closed_issues == []
    assert card_fields(env.runner)["交付狀態"] != "🏁完成"
    err = capsys.readouterr().err
    assert "illegal_terminal_before_cleanup" in err
    assert "--repo-path" in err


def test_release_without_repo_path_is_allowed_but_traced_on_the_card(env: Env, capsys) -> None:
    """無 --repo-path 的 release 不拒絕，但必須寫進卡上留痕。

    ⛔ 該分支不拒絕：沒有本機 repo 時 ``--cleanup`` 在構造上做不到（見既有的
    ``--cleanup and not args.repo_path`` 拒絕），且本專案無該情境的實例。
    ⭐ 但它先前只印 stderr、卡上零紀錄，使「不帶 --cleanup 的 release 發生過幾次」
    在事後不可觀測——實測搜三個收尾留痕字串，「已清除」有命中而「未走到」「無任何
    對象」皆 0，那個 0 是不可觀測不是未發生。本條把可稽核性釘成可執行的事實。
    """
    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo)))
    assert rc == 0
    # 行為不變：什麼都沒刪、狀態面照寫
    assert env.wt.exists()
    assert local_branch_exists(env.repo)
    assert remote_branch_exists(env.repo)
    assert card_fields(env.runner)["交付狀態"] == "🏁完成"
    # 警示照印
    assert "illegal_terminal_before_cleanup" in capsys.readouterr().err
    # ⭐ 而且寫進了卡上留痕，不只 stderr——用既有 helper 讀，不自己造存取路徑
    lines = handoff_log_lines(env.runner)
    assert lines, "release 應留下 handoff Log 行"
    assert "收尾清理未執行" in lines[-1]
    assert "未帶 --cleanup 且未帶 --repo-path" in lines[-1]


def test_cleanup_after_a_status_only_release_is_refused_as_illegal(env: Env) -> None:
    """未帶 --cleanup 的 release 之後再補 --cleanup 會被擋——警示裡講的就是這件事。

    守衛刻意不自動修復非法態；這條把那個代價釘成可執行的事實，免得文件與實作各說
    各話。⚠️ 現在只有「無 --repo-path」那條路徑到得了該非法態（帶 --repo-path 的
    組合已於前置檢查被拒），所以第一次呼叫刻意不帶 --repo-path。
    """
    assert run_cli(handoff_argv(CARD_ID, head_sha(env.repo))) == 0
    env.runner.issue_states[env.issue_number] = "CLOSED"

    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo), "--cleanup": True}))
    assert rc == 5
    assert env.wt.exists()
    assert local_branch_exists(env.repo)
    assert remote_branch_exists(env.repo)


def test_cleanup_help_states_the_two_branch_contract(capsys) -> None:
    """R1-001：help 與行為必須一致。

    ⛔ 實作改成兩分支後，``--cleanup`` 的 help 仍宣稱「預設不清理——刪除不可逆，
    預設值取代價可回復的那一邊」，而那個理由已被 ``cleanup.AUTHORITY_BY_PROOF``
    推翻（只有 ancestor 授權刪分支）。本條把一致性釘成可執行的事實。

    ⚠️ 斷言的是 **help 的實際輸出**，⛔ 不是 grep 原始碼——模組說明裡刻意保留了
    一段對舊說法的引述（標為已被推翻的歷史），grep 會誤判。
    """
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["handoff", "--help"])
    out = capsys.readouterr().out
    # ⛔ 被推翻的說法不得出現在使用者看得到的 help 裡
    assert "預設值取代價可回復的那一邊" not in out
    # ⭐ 兩分支契約必須講明
    assert "兩分支契約" in out
    assert "illegal_terminal_before_cleanup" in out
    assert "收尾清理未執行" in out


def test_non_release_stages_are_untouched_by_the_refusal(env: Env) -> None:
    """⛔ 拒絕只作用於 release：其他 next-stage 帶 --repo-path 不受影響。

    收緊過頭會擋掉正當流程——本卡今晚的每一次 handoff（research／planning／backlog）
    都帶 --repo-path 且沒有 --cleanup。
    """
    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo),
                                 "--next-stage": "implementation"}))
    assert rc == 0
    assert card_fields(env.runner)["交付狀態"] == "🔨執行中"


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
# 4.5 R3-01：動作發生了、終態沒寫時，Log 必須留得下那筆事實
# ---------------------------------------------------------------------------
#
# 上面第 4 節證明的是「狀態面停在原處」。那是安全規則，本節不動它——本節證明的是
# **另外半件事**：卡片上要有一筆看得出「做了什麼、被什麼擋住」的紀錄，而且那筆紀錄
# 明確不是終態。stdout／stderr 不是 Issue Log。


def _abort_the_remote_delete(
    env: Env, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """在複驗前一刻讓另一個 clone 推新提交，逼出 ``mode=aborted``。

    與 `test_status_face_stays_put_when_the_remote_delete_is_aborted` 是同一個注入
    手法（monkeypatch 只控制時機，複驗跑的是真函式）。抽成函式是為了讓本節的斷言
    與第 4 節的斷言看的是**同一條路徑**，而不是各自造一個近似情境。
    """
    other = tmp_path / "abort-clone"
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


def test_an_aborted_closeout_leaves_a_non_terminal_record_of_what_it_did(
    env: Env, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R3-01：worktree 已經被移除了，卡片不能一個字都沒有。

    這條同時釘住**雙面性質**，兩面缺一都算沒修好：

    1. **有紀錄**——Log 多出一行，內容能重建出「worktree 與本地分支已清除、遠端分支
       中止」與具名的阻擋原因；
    2. **不是終態**——交付狀態、owner、最後交接、iteration 全部原封不動，Issue 沒關，
       而且那一行不是 ``handoff by wf-cli`` 的交接行。

    第 2 面是本輪最容易寫壞的地方：把紀錄寫成「順便也寫個狀態」就等於推翻了第 4 節
    的安全規則。
    """
    _abort_the_remote_delete(env, tmp_path, monkeypatch)

    before_fields = dict(card_fields(env.runner))
    before_handoff_lines = handoff_log_lines(env.runner)
    assert cleanup_log_lines(env.runner) == [], "前提設定失敗：本次之前不該有收尾紀錄"

    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo), "--cleanup": True}))
    assert rc == 5

    # 前提：本機側真的被動過了，所以這筆紀錄不是可有可無的
    assert not env.wt.exists(), "前提設定失敗：worktree 應該已被移除"
    assert not local_branch_exists(env.repo), "前提設定失敗：本地分支應該已被刪除"
    assert remote_branch_exists(env.repo)

    # 1. 有紀錄，且內容由實際動作產生
    lines = cleanup_log_lines(env.runner)
    assert len(lines) == 1, f"收尾紀錄不是剛好一行：{lines}"
    line = lines[0]
    assert "mode=aborted" in line
    assert "已清除 worktree、本地分支" in line, line
    assert "遠端分支 已中止（刪除前複驗不通過）" in line, line
    assert "阻擋：" in line and "remote" in line, line

    # 2. 但它不是終態、不是交接
    after_fields = card_fields(env.runner)
    assert after_fields["交付狀態"] == "📦已合併"
    assert after_fields.get("owner") == before_fields.get("owner")
    assert after_fields.get("最後交接") == before_fields.get("最後交接")
    assert after_fields.get("iteration") == before_fields.get("iteration")
    assert env.runner.closed_issues == []
    assert handoff_log_lines(env.runner) == before_handoff_lines, (
        "收尾紀錄被寫成了交接行——那等於宣告了一次沒發生的交接"
    )
    assert "非終態紀錄" in line and "本次第 4 步寫入：無" in line, line


def test_actions_are_recorded_even_when_an_applied_run_had_its_effect_withheld(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`mode=applied` 也可能「做了事卻沒寫終態」——照 mode 分流會漏掉這一格。

    情境同 `test_release_fails_when_cleanup_reported_success_but_did_not_complete`：
    遠端刪除回報成功、分支卻還在，executor 因此扣住第 4 步。此時 worktree 與本地分支
    **已經不在了**，病灶與 aborted 完全相同，所以留痕的觸發條件讀的是動作集合而不是
    `result.mode`。
    """
    real_runner = cleanup.default_git_runner
    intercepted: list[list[str]] = []

    def lying_runner(cwd: Path, args):
        argv = list(args)
        if _is_remote_branch_delete(argv):
            intercepted.append(argv)
            return cleanup.GitResult(0, "", "")
        return real_runner(cwd, argv)

    monkeypatch.setattr(cleanup, "default_git_runner", lying_runner)

    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo), "--cleanup": True}))
    assert intercepted, "假成功 runner 一條刪除指令都沒攔到，本案例形同不存在"
    assert rc == 5
    assert not env.wt.exists(), "前提設定失敗：worktree 應該已被移除"

    lines = cleanup_log_lines(env.runner)
    assert len(lines) == 1, f"applied 但效果扣住時沒有留下紀錄：{lines}"
    assert "mode=applied" in lines[0] and "效果落地=否" in lines[0], lines[0]
    assert "已清除 worktree、本地分支、遠端分支" in lines[0], lines[0]
    # 仍然不是終態
    assert card_fields(env.runner)["交付狀態"] == "📦已合併"
    assert env.runner.closed_issues == []


def test_a_guard_block_that_touched_nothing_writes_no_record(env: Env) -> None:
    """守衛擋下、一個動作都沒走時**不寫**——否則每次被擋的重跑都在卡上疊一行噪音。

    判準不是「想不想少寫字」，是這條路徑什麼都沒動過：重跑會重新觀測、重新得到同一份
    判定，**沒有任何東西只存在於這一次 run 裡**。這與 aborted 的差別正是「不可逆動作
    已經發生」。
    """
    (env.wt / "draft.txt").write_text("尚未提交的草稿\n", encoding="utf-8")

    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo), "--cleanup": True}))
    assert rc == 5
    assert env.wt.exists()
    assert cleanup_log_lines(env.runner) == []
    assert card_fields(env.runner)["交付狀態"] == "📦已合併"


def test_a_completed_closeout_records_the_actions_exactly_once(env: Env) -> None:
    """收尾走完時，動作敘述只出現在終態那一行——不要再補一行非終態紀錄。

    否則同一件事會在 Log 裡出現兩行，而第二行還自稱非終態，直接製造出敘述打架。
    """
    rc = run_cli(handoff_argv(CARD_ID, head_sha(env.repo),
                              **{"--repo-path": str(env.repo), "--cleanup": True}))
    assert rc == 0
    assert cleanup_log_lines(env.runner) == []
    handoff_lines = handoff_log_lines(env.runner)
    assert len(handoff_lines) == 1
    assert "收尾清理：已清除 worktree、本地分支、遠端分支" in handoff_lines[0]


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
