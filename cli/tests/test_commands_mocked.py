from __future__ import annotations

import json as jsonlib
import subprocess
from pathlib import Path

import pytest

from wf_cli.card import ROUTING_MARKER
from wf_cli.cli import build_parser
from wf_cli.commands import (
    assign_cmd,
    deploy_declare_cmd,
    deploy_state_cmd,
    handoff_cmd,
    open_cmd,
    snapshot_cmd,
)
from wf_cli.project import (
    ProjectError,
    ensure_fields,
    find_item_by_card_id,
    list_items,
    resolve_project,
    set_field_value,
    set_item_body,
)

from .conftest import git
from .fake_gh import FakeGhRunner
from .test_card import ROUTING_LINE_RE

#: 跨 repo 歸屬閘門（#57）接上之後，assign 的卡必須是**真 Issue**（卡的 repo 只認
#: Issue URL），而 ``--worktree`` 必須落在可判定的 repo 上。本檔原本全用 DraftIssue ＋
#: 虛構路徑，那組輸入在閘門眼中是 ``card_repo_undeterminable``，會被正確地拒絕。
ASSIGN_REPO = "acme/workflow"


@pytest.fixture
def source_repo(tmp_path: Path) -> Path:
    """一個 origin 指向 GitHub 形狀 URL 的真 git repo。

    閘門讀的是**真的** git（commondir ＋ origin remote），簽章裡沒有注入點——這是刻意
    的（守衛的輸入必須是事實，不能由呼叫端宣稱）。代價就是這些原本純 mock 的 assign
    測試需要一個真 repo 才走得到閘門後面。不需要任何 commit：``rev-parse
    --git-common-dir`` 與 ``remote get-url`` 在空 repo 上就已經回答得出來。
    """
    repo = tmp_path / "workflow"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "remote", "add", "origin", f"git@github.com:{ASSIGN_REPO}.git")
    return repo


@pytest.fixture
def fake_runner(monkeypatch):
    runner = FakeGhRunner()
    for module in (
        open_cmd,
        assign_cmd,
        handoff_cmd,
        snapshot_cmd,
        deploy_state_cmd,
        deploy_declare_cmd,
    ):
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
        "--exec-capability": "主力型",
        "--exec-capability-reason": "跨模組改動",
        "--review-capability": "主力型",
        "--review-capability-reason": "一般 review 即可",
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


def _deploy_declare_argv(card_id: str, **overrides) -> list[str]:
    defaults = {
        "--repo": "acme/workflow",
        "--decision": "needs-deploy",
        "--reason": "需求方已確認此卡需要部署驗證",
        "--actor": "PM 祕書",
    }
    defaults.update(overrides)
    argv = ["deploy-declare", *BASE_TARGET, card_id]
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


# ---------------------------------------------------------------------------
# 規劃期路由欄位（WF-CLI-ROUTING-TIER1）
# ---------------------------------------------------------------------------


def test_open_renders_routing_line_into_issue_body_and_spec_file(fake_runner, tmp_path: Path):
    spec_dir = tmp_path / "tasks"
    rc = run_cli(
        _open_argv(
            "ROUTING-CARD1",
            **{
                "--exec-capability": "主力型",
                "--exec-capability-reason": "跨模組、根因已知",
                "--review-capability": "高階型",
                "--review-capability-reason": "資料正確性紅線，須跨家族",
                "--spec-dir": str(spec_dir),
            },
        )
    )
    assert rc == 0
    expected = (
        "- 執行：待指派（建議 主力型；跨模組、根因已知）"
        "　查核：待指派（建議 高階型；資料正確性紅線，須跨家族）"
    )
    project = resolve_project(fake_runner, "acme", 1)
    item = find_item_by_card_id(list_items(fake_runner, project), "ROUTING-CARD1")
    assert item is not None
    assert expected in item.body
    assert expected in (spec_dir / "ROUTING-CARD1.md").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "flag",
    [
        "--exec-capability",
        "--exec-capability-reason",
        "--review-capability",
        "--review-capability-reason",
    ],
)
def test_open_argparse_requires_every_routing_flag(fake_runner, flag):
    # 缺欄＝硬拒（argparse required），不得靜默產出不符範本第 4 行的卡。
    argv = list(_open_argv("ROUTING-MISSING"))
    idx = argv.index(flag)
    del argv[idx : idx + 2]
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(argv)


@pytest.mark.parametrize(
    "flag", ["--exec-capability-reason", "--review-capability-reason"]
)
def test_open_rejects_blank_routing_reason_without_creating_card(fake_runner, capsys, flag):
    rc = run_cli(_open_argv("ROUTING-BLANK", **{flag: "   "}))
    assert rc == 2
    err = capsys.readouterr().err
    assert "必填" in err
    project = resolve_project(fake_runner, "acme", 1)
    assert find_item_by_card_id(list_items(fake_runner, project), "ROUTING-BLANK") is None


@pytest.mark.parametrize("flag", ["--exec-capability", "--review-capability"])
def test_open_rejects_risk_tier_value_in_capability_flag(fake_runner, flag):
    # 命名碰撞的實際誤用：把 T0–T4 填進能力層級旗標，argparse choices 直接擋。
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(_open_argv("ROUTING-CONFUSED", **{flag: "T3"}))


def test_open_rejects_capability_tier_value_in_risk_tier_flag(fake_runner):
    # 反向：把能力層級填進 --tier（級別）也必須擋，兩軸值域互不接受。
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(_open_argv("ROUTING-CONFUSED2", **{"--tier": "主力型"}))


# #17／#19／#20 的實際開卡情境重放：三張卡當初產出的執行行都是
# 「- 執行：待指派　查核：獨立校讀」（缺括號內的層級與理由，即本卡的核心痛點）。
# 以相同參數重跑新版 open，證明產出改為符合 templates/tasks-card.md 第 4 行。
_REPLAY_CARDS = [
    (
        "WF-REVIEW-EVENT-MARKER-ENFORCE1",
        "doctor 落實 wf-review-event:v1 不合格 marker 的 fail-closed",
        "高階型",
        "查核寫入通道的 fail-closed 判準，錯判會讓卡停機",
    ),
    (
        "WF-CLI-CARD-AMEND1",
        "wfcli 補上開卡後的通用卡面修訂能力",
        "主力型",
        "唯一寫入通道的新寫入路徑，跨模組",
    ),
    (
        "WF-REVIEW-CHANNEL-THIRD-FACE1",
        "doctor 補上三面一致的第三面（Project 交付狀態欄）",
        "主力型",
        "既有對帳邏輯延伸，根因與範圍已知",
    ),
]


@pytest.mark.parametrize("card_id,feature,capability,reason", _REPLAY_CARDS)
def test_open_replays_real_cards_into_template_line4_format(
    fake_runner, card_id, feature, capability, reason
):
    rc = run_cli(
        _open_argv(
            card_id,
            **{
                "--feature": feature,
                "--reviewer": "獨立校讀",
                "--exec-capability": capability,
                "--exec-capability-reason": reason,
                "--review-capability": "高階型",
                "--review-capability-reason": "跨家族獨立查核",
            },
        )
    )
    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = find_item_by_card_id(list_items(fake_runner, project), card_id)
    assert item is not None
    routing = [ln for ln in item.body.splitlines() if ln.startswith("- 執行：")]
    assert len(routing) == 1
    assert ROUTING_LINE_RE.match(routing[0]) is not None
    # 三張卡當初的產出形狀（無層級無理由）不得再出現。
    assert routing[0] != "- 執行：待指派　查核：獨立校讀"


def _open_for_assign(card_id: str, **overrides) -> list[str]:
    """開一張**真 Issue** 的卡。閘門的「卡所屬 repo」只認 Issue URL，DraftIssue 判不出來。"""
    overrides.setdefault("--repo", ASSIGN_REPO)
    return _open_argv(card_id, **overrides)


def _assign_argv(
    card_id: str,
    assignee: str,
    branch: str,
    worktree: str,
    *,
    actual_capability: str = "主力型",  # 與 _open_argv 的建議執行層級相同＝相符路徑
    deviation_reason: str | None = None,
    source_repo: Path | str | None = None,
) -> list[str]:
    argv = [
        "assign", *BASE_TARGET, "--repo", ASSIGN_REPO, card_id,
        "--assignee", assignee, "--branch", branch, "--worktree", worktree,
        "--actual-capability", actual_capability,
    ]
    if deviation_reason is not None:
        argv += ["--capability-deviation-reason", deviation_reason]
    if source_repo is not None:
        # 本檔的 worktree 路徑是虛構的（``/w``、``.claude/worktrees/a``），路徑本身導不出
        # repo。明示來源 repo 才是誠實的做法——而不是把路徑改成剛好座落在某個 repo 底下，
        # 那會讓這些測試偷偷依賴磁碟佈局。
        argv += ["--worktree-source-repo", str(source_repo)]
    return argv


# --- assign 偏離專項：三種情形（卡面驗證明列）-------------------------------


def _assign_log_line(runner, card_id: str) -> str:
    project = resolve_project(runner, "acme", 1)
    item = find_item_by_card_id(list_items(runner, project), card_id)
    assert item is not None
    lines = [ln for ln in item.body.splitlines() if " assign by wf-cli " in ln]
    assert len(lines) == 1
    return lines[0]


def test_assign_matched_capability_needs_no_reason_and_proceeds(fake_runner, source_repo):
    # 情形 1：實際層級＝卡面建議 → 不要求理由，照常派工。
    run_cli(_open_for_assign("DEV-MATCH1", **{"--exec-capability": "主力型"}))
    rc = run_cli(
        _assign_argv("DEV-MATCH1", "某模型@某工具", "b", "/w", actual_capability="主力型",
                     source_repo=source_repo)
    )
    assert rc == 0
    log = _assign_log_line(fake_runner, "DEV-MATCH1")
    assert "實際能力層級 主力型（與卡面建議 主力型 相符）" in log


class _RecordingRunner:
    """把每一次 gh 呼叫記下來的代理（R2-002）。

    先前那版「零寫入」測試只比對最終狀態值——`FakeGhRunner` 不記呼叫，所以測不出
    「有沒有發生 mutation」，只測得出「最後看起來一樣」。狀態比對過不了「探針通過
    但程式不正確」這關（例如寫進去又改回來），改用呼叫紀錄才是真證據。

    刻意做在測試檔內而非改 `tests/fake_gh.py`：後者不在本卡資源宣告內。
    """

    # gh 子命令中會改變遠端狀態的那些；其餘（view／field-list／item-list）是唯讀。
    MUTATING = (
        ("project", "item-edit"),
        ("project", "item-create"),
        ("project", "item-add"),
        ("project", "field-create"),
        ("issue", "create"),
        ("issue", "edit"),
        ("issue", "comment"),
    )

    def __init__(self, inner):
        self.inner = inner
        self.calls: list[list[str]] = []

    def execute(self, args, input=None):
        self.calls.append(list(args))
        return self.inner.execute(args, input)

    def run_json(self, args):
        self.calls.append(list(args))
        return self.inner.run_json(args)

    def graphql(self, query: str, **variables):
        self.calls.append(["graphql", query])
        return self.inner.graphql(query, **variables)

    def mutations(self) -> list[list[str]]:
        found = []
        for call in self.calls:
            is_mutating_subcommand = any(
                call[: len(m)] == list(m) for m in self.MUTATING
            )
            is_mutating_graphql = call[0] == "graphql" and "mutation" in call[1]
            if is_mutating_subcommand or is_mutating_graphql:
                found.append(call)
        return found


def test_assign_deviation_without_reason_is_refused_before_any_mutation(
    fake_runner, capsys, monkeypatch
):
    # 情形 2：不符且未給理由 → fail-closed 拒絕。
    #
    # 保證的**精確範圍**：拒絕路徑不發生任何 mutation 呼叫。注意 assign 在能力檢查
    # 之前會呼叫 ensure_fields，那是冪等的欄位 schema 準備——本測試在欄位已存在的
    # project 上跑，故連 field-create 都不該發生；但「絕對零寫入」不是本指令在所有
    # 情境下的保證（全新 project 會先建欄位），因此不用那個更強的詞。
    run_cli(_open_argv("DEV-FAIL1", **{"--exec-capability": "主力型"}))
    project = resolve_project(fake_runner, "acme", 1)
    before = find_item_by_card_id(list_items(fake_runner, project), "DEV-FAIL1")

    spy = _RecordingRunner(fake_runner)
    monkeypatch.setattr(assign_cmd, "default_runner", spy)
    rc = run_cli(
        _assign_argv("DEV-FAIL1", "某模型@某工具", "b", "/w", actual_capability="高階型")
    )
    assert rc == 2
    assert "MODEL_ROUTING" in capsys.readouterr().err

    # 真證據：整條拒絕路徑上一次 mutation 都沒有。
    assert spy.mutations() == []
    assert spy.calls, "代理必須真的攔到呼叫，否則這個斷言是空的"

    # 狀態值也確實沒變（與呼叫紀錄互為佐證）。
    after = find_item_by_card_id(list_items(fake_runner, project), "DEV-FAIL1")
    assert after.fields["owner"] == before.fields["owner"]
    assert after.fields["交付狀態"] == before.fields["交付狀態"]
    assert after.body == before.body


def test_recording_runner_actually_detects_mutations(fake_runner, monkeypatch, source_repo):
    # 防「探針本身壞掉」：成功派工必須被同一支代理看見 mutation。
    # 沒有這條，上面的 mutations()==[] 可能只是代理沒接上。
    run_cli(_open_for_assign("DEV-SPY1", **{"--exec-capability": "主力型"}))
    spy = _RecordingRunner(fake_runner)
    monkeypatch.setattr(assign_cmd, "default_runner", spy)
    assert run_cli(
        _assign_argv("DEV-SPY1", "某模型@某工具", "b", "/w", source_repo=source_repo)
    ) == 0
    assert spy.mutations() != []


def test_assign_deviation_with_reason_records_both_and_reads_back(fake_runner, source_repo):
    # 情形 3：給了理由 → 實際層級與偏離理由皆入 Log，且可被讀回。
    run_cli(_open_for_assign("DEV-OK1", **{"--exec-capability": "主力型"}))
    rc = run_cli(
        _assign_argv(
            "DEV-OK1",
            "某模型@某工具",
            "b",
            "/w",
            actual_capability="高階型",
            deviation_reason="主力型當下額度不足，改派高階型",
            source_repo=source_repo,
        )
    )
    assert rc == 0
    log = _assign_log_line(fake_runner, "DEV-OK1")
    assert "實際能力層級 高階型" in log
    assert "偏離卡面建議 主力型" in log
    assert "主力型當下額度不足，改派高階型" in log


def test_assign_on_pre_routing_card_requires_reason_and_does_not_call_it_deviation(
    fake_runner, capsys, source_repo
):
    # 無基線格（#17／#19／#20 那批舊卡）：同樣 fail-closed，但留痕不得寫成「偏離」。
    run_cli(_open_for_assign("DEV-LEGACY1"))
    project = resolve_project(fake_runner, "acme", 1)
    item = find_item_by_card_id(list_items(fake_runner, project), "DEV-LEGACY1")
    # 真正的規劃期路由必填之前的卡：**沒有版本標記**，執行行是舊格式自由文字。
    legacy_body = item.body.replace(
        next(ln for ln in item.body.splitlines() if ln.startswith("- 執行：")),
        "- 執行：待指派　查核：獨立校讀",
    ).replace(ROUTING_MARKER + "\n", "")
    set_item_body(fake_runner, item.content_type, item.content_id, project,
                  ASSIGN_REPO, item.issue_number, legacy_body)

    assert run_cli(
        _assign_argv("DEV-LEGACY1", "某模型@某工具", "b", "/w", source_repo=source_repo)
    ) == 2
    assert "沒有可比對的建議層級" in capsys.readouterr().err

    rc = run_cli(
        _assign_argv(
            "DEV-LEGACY1", "某模型@某工具", "b", "/w",
            deviation_reason="本卡開立於規劃期路由必填之前，無建議可比對",
            source_repo=source_repo,
        )
    )
    assert rc == 0
    log = _assign_log_line(fake_runner, "DEV-LEGACY1")
    assert "卡面無建議層級" in log
    assert "偏離卡面建議" not in log
    assert "本卡開立於規劃期路由必填之前" in log


def test_assign_on_declared_card_with_broken_line_logs_unparseable_not_absent(
    fake_runner, source_repo
):
    # R3-001 的第二個方向，走完整 CLI 路徑：卡面**宣告**了新制但路由行被破壞
    # （這裡用零寬字元打斷前綴），Log 必須寫「無法解析」而非「卡面無建議層級」。
    run_cli(_open_for_assign("DEV-BROKEN1", **{"--exec-capability": "主力型"}))
    project = resolve_project(fake_runner, "acme", 1)
    item = find_item_by_card_id(list_items(fake_runner, project), "DEV-BROKEN1")
    routing = next(ln for ln in item.body.splitlines() if ln.startswith("- 執行："))
    broken = item.body.replace(routing, "\u200b" + routing)  # 標記仍在，行壞了
    set_item_body(fake_runner, item.content_type, item.content_id, project,
                  ASSIGN_REPO, item.issue_number, broken)

    assert run_cli(
        _assign_argv("DEV-BROKEN1", "某模型@某工具", "b", "/w", source_repo=source_repo)
    ) == 2
    rc = run_cli(
        _assign_argv(
            "DEV-BROKEN1", "某模型@某工具", "b", "/w",
            deviation_reason="卡面路由行疑遭編輯破壞，先以主力型派工並待修卡",
            source_repo=source_repo,
        )
    )
    assert rc == 0
    log = _assign_log_line(fake_runner, "DEV-BROKEN1")
    assert "卡面建議無法解析" in log
    assert "卡面無建議層級" not in log
    assert "偏離卡面建議" not in log


def test_assign_argparse_requires_actual_capability(fake_runner):
    argv = _assign_argv("DEV-REQ1", "某模型@某工具", "b", "/w")
    idx = argv.index("--actual-capability")
    del argv[idx : idx + 2]
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(argv)


def test_assign_rejects_risk_tier_value_in_actual_capability(fake_runner):
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(
            _assign_argv("DEV-REQ2", "某模型@某工具", "b", "/w", actual_capability="T3")
        )


def test_assign_writes_owner_and_branch_worktree(fake_runner, source_repo):
    run_cli(_open_for_assign("ASSIGN-CARD1"))
    rc = run_cli(_assign_argv("ASSIGN-CARD1", "Claude Sonnet 5@Claude Code", "ai/agent/ASSIGN-CARD1", ".claude/worktrees/assign-card1", source_repo=source_repo))
    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["owner"] == "Claude Sonnet 5@Claude Code"
    assert item.fields["分支worktree"] == "ai/agent/ASSIGN-CARD1 @ .claude/worktrees/assign-card1"
    assert item.fields["交付狀態"] == "🚧進行中"
    assert "assign by wf-cli" in item.body


def test_assign_does_not_block_on_unassigned_backlog_sibling_with_same_resource(
    fake_runner, source_repo
):
    # 兩張卡都宣告同一檔案，但都還沒被 assign 過（單純躺在 Backlog）——
    # 此時沒有任何「執行中」的卡在爭這個資源，assign 第一張不該被擋。
    run_cli(_open_for_assign("CONFLICT-A", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    run_cli(_open_for_assign("CONFLICT-B", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    rc = run_cli(_assign_argv("CONFLICT-A", "someone", "ai/agent/CONFLICT-A", ".claude/worktrees/a", source_repo=source_repo))
    assert rc == 0


def test_assign_rejects_on_resource_conflict_with_already_assigned_card(fake_runner, source_repo):
    # CONFLICT-A 先被指派（進入「執行中」），CONFLICT-B 才嘗試指派到同一資源 → 應拒絕。
    run_cli(_open_for_assign("CONFLICT-A", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    run_cli(_open_for_assign("CONFLICT-B", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    rc1 = run_cli(_assign_argv("CONFLICT-A", "someone", "ai/agent/CONFLICT-A", ".claude/worktrees/a", source_repo=source_repo))
    assert rc1 == 0
    rc2 = run_cli(_assign_argv("CONFLICT-B", "someone-else", "ai/agent/CONFLICT-B", ".claude/worktrees/b", source_repo=source_repo))
    assert rc2 == 4  # 撞卡拒絕


def test_assign_allowed_when_conflicting_card_is_terminal(fake_runner, source_repo):
    run_cli(_open_for_assign("TERMINAL-A", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    run_cli(_open_for_assign("TERMINAL-B", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    project = resolve_project(fake_runner, "acme", 1)
    fields = ensure_fields(fake_runner, "acme", 1)
    item_a = next(i for i in list_items(fake_runner, project) if i.fields.get("卡ID") == "TERMINAL-A")
    set_field_value(fake_runner, project, item_a.item_id, fields["交付狀態"], "🏁完成")

    rc = run_cli(_assign_argv("TERMINAL-B", "someone", "ai/agent/TERMINAL-B", ".claude/worktrees/b", source_repo=source_repo))
    assert rc == 0  # TERMINAL-A 已完成，資源釋放，不再視為衝突


# ---------------------------------------------------------------------------
# 跨 repo 歸屬閘門（WF-WORKTREE-REPO-OWNERSHIP1 / #57）——攔截點在 assign
# ---------------------------------------------------------------------------


def _other_repo(tmp_path: Path) -> Path:
    other = tmp_path / "other-project"
    other.mkdir()
    git(other, "init", "-q", "-b", "main")
    git(other, "remote", "add", "origin", "git@github.com:acme/other-project.git")
    return other


def test_assign_blocks_cross_repo_worktree_before_any_mutation(
    fake_runner, tmp_path, capsys, monkeypatch
):
    """核心痛點的直接回放：卡屬 acme/workflow，worktree 卻要建在 acme/other-project。

    只驗回傳碼不算數——這裡同時用 ``_RecordingRunner`` 證明**整條拒絕路徑一次
    mutation 都沒有**，以及卡面欄位與 body 一字未動。閘門若排在任何 set_field_value
    之後，這條會紅。
    """
    run_cli(_open_for_assign("CROSS-REPO1"))
    project = resolve_project(fake_runner, "acme", 1)
    before = find_item_by_card_id(list_items(fake_runner, project), "CROSS-REPO1")

    spy = _RecordingRunner(fake_runner)
    monkeypatch.setattr(assign_cmd, "default_runner", spy)
    rc = run_cli(
        _assign_argv("CROSS-REPO1", "某模型@某工具", "b", "/w",
                     source_repo=_other_repo(tmp_path))
    )
    assert rc == 5
    err = capsys.readouterr().err
    assert "acme/other-project" in err and "acme/workflow" in err
    assert "卡就開在哪個 repo" in err  # 拒絕訊息必附合法出路（#16 §7.1）

    assert spy.mutations() == []
    assert spy.calls, "代理必須真的攔到呼叫，否則這個斷言是空的"
    after = find_item_by_card_id(list_items(fake_runner, project), "CROSS-REPO1")
    assert after.fields.get("owner") == before.fields.get("owner")
    assert after.fields.get("分支worktree") == before.fields.get("分支worktree")
    assert after.fields["交付狀態"] == before.fields["交付狀態"]
    assert after.body == before.body


def test_assign_allows_absolute_worktree_under_the_card_repo(fake_runner, source_repo):
    """生產慣例的那條路：絕對路徑、尚未建立、巢狀在卡自己的 repo 底下 → 放行。

    不給 ``--worktree-source-repo``，走祖先推測。這是需求方 2026-08-12 裁定的預設用法，
    必須不被誤擋。
    """
    run_cli(_open_for_assign("NESTED-OK1"))
    wt = source_repo / ".claude" / "worktrees" / "nested-ok1"
    assert not wt.exists()
    assert run_cli(_assign_argv("NESTED-OK1", "某模型@某工具", "b", str(wt))) == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = find_item_by_card_id(list_items(fake_runner, project), "NESTED-OK1")
    assert item.fields["分支worktree"] == f"b @ {wt}"


def test_assign_blocks_relative_worktree_path_with_actionable_message(fake_runner, capsys):
    """相對路徑不帶 repo 資訊 → 拒絕，且訊息要講得出補法（需求方裁定的新慣例）。"""
    run_cli(_open_for_assign("REL-PATH1"))
    rc = run_cli(_assign_argv("REL-PATH1", "某模型@某工具", "b", ".claude/worktrees/x"))
    assert rc == 5
    err = capsys.readouterr().err
    assert "相對路徑" in err
    assert "base_dir" in err or "source_repo" in err


def test_assign_blocks_draft_issue_card(fake_runner, source_repo, capsys):
    """DraftIssue 沒有 Issue URL → 卡的 repo 判不出來 → fail-closed。

    這正是本檔其餘 assign 測試全部得改成真 Issue 的原因，明寫成一條測試而不是
    藏在 fixture 的沉默行為裡。
    """
    run_cli(_open_argv("DRAFT-CARD1"))  # 沒有 --repo ＝ DraftIssue
    rc = run_cli(_assign_argv("DRAFT-CARD1", "某模型@某工具", "b", "/w",
                              source_repo=source_repo))
    assert rc == 5
    assert "判不出卡所屬 repo" in capsys.readouterr().err


def test_assign_registers_the_worktree_source_repo_flag():
    """旗標必須真的註冊在 CLI 上——原型階段漏掉它，等於閘門的出路只存在於文件裡。"""
    parser = build_parser()
    args = parser.parse_args(
        _assign_argv("FLAG-CARD1", "a", "b", "/w", source_repo="/some/repo")
    )
    assert args.worktree_source_repo == "/some/repo"
    # 省略時為 None（走路徑推測），不是空字串。
    assert parser.parse_args(_assign_argv("FLAG-CARD1", "a", "b", "/w")).worktree_source_repo is None


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


def test_deploy_declare_corrects_not_applicable_to_undeployed_with_auditable_decision(fake_runner):
    run_cli(_open_argv("DEPLOY-DECLARE-CARD1", **{"--repo": "acme/workflow"}))
    fake_runner.add_builtin_status("acme", 1, ["Todo", "In Progress", "Done"])

    rc = run_cli(_deploy_declare_argv("DEPLOY-DECLARE-CARD1"))

    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["部署狀態"] == "⏸未部署"
    assert item.fields["Status"] == "Todo"
    comment = fake_runner.issues[item.issue_url]["comments"][-1]
    assert comment.startswith("## deployment-declaration")
    assert "card_id: DEPLOY-DECLARE-CARD1" in comment
    assert "actor: PM 祕書" in comment
    assert "decision: needs-deploy" in comment
    assert "reason: 需求方已確認此卡需要部署驗證" in comment
    assert "—不適用 → ⏸未部署" in comment
    assert any("updateProjectV2ItemFieldValue" in query for query in fake_runner.graphql_calls)
    assert not any("updateProjectV2Field" in query for query in fake_runner.graphql_calls)
    single_select_queries = [
        query for query in fake_runner.graphql_calls if "singleSelectOptionId" in query
    ]
    assert single_select_queries
    assert all("$value: String!" in query for query in single_select_queries)


def test_deploy_declare_reports_partial_write_when_item_mutation_fails_after_timeline_event(
    fake_runner, monkeypatch, capsys
):
    run_cli(_open_argv("DEPLOY-DECLARE-PARTIAL", **{"--repo": "acme/workflow"}))
    fake_runner.add_builtin_status("acme", 1, ["Todo", "In Progress", "Done"])

    def reject_item_mutation(*_args, **_kwargs):
        raise ProjectError("GitHub rejected the item field value")

    monkeypatch.setattr(deploy_declare_cmd, "update_item_field_value", reject_item_mutation)

    rc = run_cli(_deploy_declare_argv("DEPLOY-DECLARE-PARTIAL"))

    assert rc == 5
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["部署狀態"] == "—不適用"
    assert fake_runner.issues[item.issue_url]["comments"][-1].startswith("## deployment-declaration")
    captured = capsys.readouterr()
    assert "部分寫入" in captured.err
    assert "Issue timeline" in captured.err
    assert "對帳" in captured.err
    assert "已宣告" not in captured.out


def test_deploy_declare_rejects_any_state_other_than_not_applicable(fake_runner):
    open_argv = _open_argv("DEPLOY-DECLARE-CARD2", **{"--repo": "acme/workflow"})
    open_argv.append("--needs-deploy")
    run_cli(open_argv)
    fake_runner.add_builtin_status("acme", 1, ["Todo", "In Progress", "Done"])
    project = resolve_project(fake_runner, "acme", 1)

    rc = run_cli(_deploy_declare_argv("DEPLOY-DECLARE-CARD2"))

    assert rc == 4
    item = list_items(fake_runner, project)[0]
    assert item.fields["部署狀態"] == "⏸未部署"
    assert item.fields.get("Status") is None
    assert fake_runner.issues[item.issue_url].get("comments") is None
    assert not any("mutation" in query for query in fake_runner.graphql_calls)


def test_deploy_declare_rejects_blank_reason_without_remote_mutation(fake_runner):
    run_cli(_open_argv("DEPLOY-DECLARE-CARD3", **{"--repo": "acme/workflow"}))
    fake_runner.add_builtin_status("acme", 1, ["Todo", "In Progress", "Done"])

    rc = run_cli(_deploy_declare_argv("DEPLOY-DECLARE-CARD3", **{"--reason": "   "}))

    assert rc == 2
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["部署狀態"] == "—不適用"
    assert fake_runner.issues[item.issue_url].get("comments") is None
    assert not any("mutation" in query for query in fake_runner.graphql_calls)


def test_deploy_declare_dry_run_writes_nothing(fake_runner, capsys):
    run_cli(_open_argv("DEPLOY-DECLARE-CARD4", **{"--repo": "acme/workflow"}))
    fake_runner.add_builtin_status("acme", 1, ["Todo", "In Progress", "Done"])

    rc = run_cli(_deploy_declare_argv("DEPLOY-DECLARE-CARD4", **{"--dry-run": True}))

    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["部署狀態"] == "—不適用"
    assert item.fields.get("Status") is None
    assert fake_runner.issues[item.issue_url].get("comments") is None
    assert not any("mutation" in query for query in fake_runner.graphql_calls)
    assert "dry-run" in capsys.readouterr().out


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
