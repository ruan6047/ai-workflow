from __future__ import annotations

import inspect
import json as jsonlib
import subprocess
from pathlib import Path

import pytest

from wf_cli.card import ROUTING_MARKER
from wf_cli.cli import build_parser
from wf_cli.commands import (
    amend_cmd,
    assign_cmd,
    deploy_declare_cmd,
    deploy_state_cmd,
    handoff_cmd,
    open_cmd,
    snapshot_cmd,
)
from wf_cli.doctor import (
    UNDECIDABLE_HANDOFF,
    audit_state_face_drift,
    parse_log_events,
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
def card_repo_dir(tmp_path: Path) -> Path:
    """一個 origin 指向 ``ASSIGN_REPO`` 的真 git repo，**只給軸 B（本機觀測）用**。

    ⚠️ 它**不再是歸屬判定的輸入**（需求方 2026-08-13 裁定：歸屬由 slug 表達，不由
    路徑反推）。上一版每一個 assign 測試都得帶著它才走得到閘門後面；現在只有真的要
    檢查「這台機器上路徑是什麼」的那幾條需要它。不需要任何 commit：``rev-parse
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
        amend_cmd,
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


def test_open_initial_status_is_the_same_for_every_tier(fake_runner):
    """五個級別全開一次，初始交付狀態必須逐級相同（⛔ 不得依 --tier 分流）。

    canonical 的「規劃閘門三級制」那節只點名 T3 那一列的批註放行；採用專案 cpbl 的
    ROADMAP 在「規劃生命週期」那節說「所有新卡一律由 `💡需求` 開始」——⚠️ **不是本 repo
    同名的 `docs/ROADMAP.md`**，該檔沒有這條。需求方 2026-08-21 裁定採後者：不讓 wfcli
    對「哪一級要過閘門」有自己的意見，且一律 💡需求 是保守方向（採用專案要放寬，在自己
    的流程裡多一次明示轉換即可；反向不安全）。這條把該裁定釘成機械事實：哪天有人為某
    一級開特例，逐級相同就會破。
    """
    project = resolve_project(fake_runner, "acme", 1)
    for tier in ("T0", "T1", "T2", "T3", "T4"):
        assert run_cli(_open_argv(f"TIER-{tier}-CARD1", **{"--tier": tier})) == 0
    seen = {
        i.fields["級別"]: i.fields["交付狀態"]
        for i in list_items(fake_runner, project)
        if i.fields["卡ID"].startswith("TIER-")
    }
    assert seen == {t: "💡需求" for t in ("T0", "T1", "T2", "T3", "T4")}, seen


def test_open_default_still_reaches_backlog_through_the_checked_transition(fake_runner):
    """⭐ 本卡（`#118`）與 `WF-BACKLOG-STAGE1`（`#120`）**組合起來**必須自洽。

    兩張卡各自合理、合起來才有可能把路走死，而那正是文字合併攔不住的東西（本輪實測：
    rebase 與 merge 都零衝突，語意衝突是 `contract_tool_reconcile --check` 抓到的）。
    ⛔ 所以這裡不用散文宣稱自洽，直接把**唯一一條受檢查的入池路徑**跑一遍。

    `#118` 之前 `open` 直接寫 `📥Backlog`——那條路**繞過** `#120` 的閘門，於是看板上
    最常見的入池方式根本不受檢查。`#118` 之後入池只剩三個口：本測試跑的受檢查轉換，
    以及 `assign --status`／`handoff --status` 兩個自由文字逃生口（後者由
    `test_handoff_backlog_gate_is_bypassed_by_the_free_text_status_flag` 誠實釘住）。

    ⚠️ 這條測試**不驗**「規劃真的做過」——`🧭規劃中` 一樣寫得進自由文字旗標。它驗的
    只有一件事：新的初始值沒有把 T2 以上的卡鎖在池外。
    """
    project = resolve_project(fake_runner, "acme", 1)
    assert run_cli(_open_argv("COHERE-CARD1")) == 0  # 預設 T3 ⇒ 課前提的那一支
    item = list_items(fake_runner, project)[0]
    assert item.fields["交付狀態"] == "💡需求"

    # 剛開的卡直接入池必須被擋——否則本測試的後半是零資訊的（閘門若失效，
    # 「走得到」對任何起點都成立，就證明不了那條路徑是**受檢查**的那一條）。
    assert run_cli(
        _handoff_argv("COHERE-CARD1", "a" * 40, **{"--next-stage": "backlog"})
    ) == 4
    assert list_items(fake_runner, project)[0].fields["交付狀態"] == "💡需求"

    # 而規劃階段本身不課前提，所以 💡需求 → 🧭規劃中 → 📥Backlog 這條路走得通。
    assert run_cli(
        _handoff_argv("COHERE-CARD1", "b" * 40, **{"--next-stage": "planning"})
    ) == 0
    assert run_cli(
        _handoff_argv("COHERE-CARD1", "c" * 40, **{"--next-stage": "backlog"})
    ) == 0
    assert list_items(fake_runner, project)[0].fields["交付狀態"] == "📥Backlog"


def test_open_creates_draft_item_with_all_ledger_fields(fake_runner, capsys):
    rc = run_cli(_open_argv("DEMO-CARD1", **{"--resources": "file:demo.py,port:9000"}))
    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    items = list_items(fake_runner, project)
    assert len(items) == 1
    item = items[0]
    assert item.fields["卡ID"] == "DEMO-CARD1"
    assert item.fields["級別"] == "T3"
    # WF-OPEN-INITIAL-STATUS1：open 寫 💡需求，不是 📥Backlog。規劃閘門在開卡**之後**
    # 才跑（canonical §3.1／採用專案 ROADMAP §2.0），開卡當下不可能已經通過。
    assert item.fields["交付狀態"] == "💡需求"
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
    source_repo: str | None = None,
) -> list[str]:
    argv = [
        "assign", *BASE_TARGET, "--repo", ASSIGN_REPO, card_id,
        "--assignee", assignee, "--branch", branch, "--worktree", worktree,
        "--actual-capability", actual_capability,
    ]
    if deviation_reason is not None:
        argv += ["--capability-deviation-reason", deviation_reason]
    if source_repo is not None:
        # 收的是 **slug**（``owner/repo``），不是目錄。本檔多數 assign 測試已不需要它——
        # 省略即宣告「屬於卡自己的 repo」，那是生產常態。留著這個參數是為了測**明示**
        # 那一格（相符與不相符各一）與「給目錄要響」。
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


def test_assign_matched_capability_needs_no_reason_and_proceeds(fake_runner):
    # 情形 1：實際層級＝卡面建議 → 不要求理由，照常派工。
    run_cli(_open_for_assign("DEV-MATCH1", **{"--exec-capability": "主力型"}))
    rc = run_cli(
        _assign_argv("DEV-MATCH1", "某模型@某工具", "b", "/w", actual_capability="主力型")
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


def test_recording_runner_actually_detects_mutations(fake_runner, monkeypatch):
    # 防「探針本身壞掉」：成功派工必須被同一支代理看見 mutation。
    # 沒有這條，上面的 mutations()==[] 可能只是代理沒接上。
    run_cli(_open_for_assign("DEV-SPY1", **{"--exec-capability": "主力型"}))
    spy = _RecordingRunner(fake_runner)
    monkeypatch.setattr(assign_cmd, "default_runner", spy)
    assert run_cli(
        _assign_argv("DEV-SPY1", "某模型@某工具", "b", "/w")
    ) == 0
    assert spy.mutations() != []


def test_assign_deviation_with_reason_records_both_and_reads_back(fake_runner):
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
        )
    )
    assert rc == 0
    log = _assign_log_line(fake_runner, "DEV-OK1")
    assert "實際能力層級 高階型" in log
    assert "偏離卡面建議 主力型" in log
    assert "主力型當下額度不足，改派高階型" in log


def test_assign_on_pre_routing_card_requires_reason_and_does_not_call_it_deviation(
    fake_runner, capsys
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
        _assign_argv("DEV-LEGACY1", "某模型@某工具", "b", "/w")
    ) == 2
    assert "沒有可比對的建議層級" in capsys.readouterr().err

    rc = run_cli(
        _assign_argv(
            "DEV-LEGACY1", "某模型@某工具", "b", "/w",
            deviation_reason="本卡開立於規劃期路由必填之前，無建議可比對",
        )
    )
    assert rc == 0
    log = _assign_log_line(fake_runner, "DEV-LEGACY1")
    assert "卡面無建議層級" in log
    assert "偏離卡面建議" not in log
    assert "本卡開立於規劃期路由必填之前" in log


def test_assign_on_declared_card_with_broken_line_logs_unparseable_not_absent(
    fake_runner
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
        _assign_argv("DEV-BROKEN1", "某模型@某工具", "b", "/w")
    ) == 2
    rc = run_cli(
        _assign_argv(
            "DEV-BROKEN1", "某模型@某工具", "b", "/w",
            deviation_reason="卡面路由行疑遭編輯破壞，先以主力型派工並待修卡",
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


def test_assign_writes_owner_and_branch_worktree(fake_runner):
    run_cli(_open_for_assign("ASSIGN-CARD1"))
    rc = run_cli(_assign_argv("ASSIGN-CARD1", "Claude Sonnet 5@Claude Code", "ai/agent/ASSIGN-CARD1", ".claude/worktrees/assign-card1"))
    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    assert item.fields["owner"] == "Claude Sonnet 5@Claude Code"
    assert item.fields["分支worktree"] == "ai/agent/ASSIGN-CARD1 @ .claude/worktrees/assign-card1"
    assert item.fields["交付狀態"] == "🔨執行中"
    assert "assign by wf-cli" in item.body


def test_assign_does_not_block_on_unassigned_backlog_sibling_with_same_resource(
    fake_runner
):
    # 兩張卡都宣告同一檔案，但都還沒被 assign 過（單純躺在 Backlog）——
    # 此時沒有任何「執行中」的卡在爭這個資源，assign 第一張不該被擋。
    run_cli(_open_for_assign("CONFLICT-A", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    run_cli(_open_for_assign("CONFLICT-B", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    rc = run_cli(_assign_argv("CONFLICT-A", "someone", "ai/agent/CONFLICT-A", ".claude/worktrees/a"))
    assert rc == 0


def test_assign_rejects_on_resource_conflict_with_already_assigned_card(fake_runner):
    # CONFLICT-A 先被指派（進入「執行中」），CONFLICT-B 才嘗試指派到同一資源 → 應拒絕。
    run_cli(_open_for_assign("CONFLICT-A", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    run_cli(_open_for_assign("CONFLICT-B", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    rc1 = run_cli(_assign_argv("CONFLICT-A", "someone", "ai/agent/CONFLICT-A", ".claude/worktrees/a"))
    assert rc1 == 0
    rc2 = run_cli(_assign_argv("CONFLICT-B", "someone-else", "ai/agent/CONFLICT-B", ".claude/worktrees/b"))
    assert rc2 == 4  # 撞卡拒絕


def test_assign_allowed_when_conflicting_card_is_terminal(fake_runner):
    run_cli(_open_for_assign("TERMINAL-A", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    run_cli(_open_for_assign("TERMINAL-B", **{"--resources": "file:shared.py", "--db-scope": "write"}))
    project = resolve_project(fake_runner, "acme", 1)
    fields = ensure_fields(fake_runner, "acme", 1)
    item_a = next(i for i in list_items(fake_runner, project) if i.fields.get("卡ID") == "TERMINAL-A")
    set_field_value(fake_runner, project, item_a.item_id, fields["交付狀態"], "🏁完成")

    rc = run_cli(_assign_argv("TERMINAL-B", "someone", "ai/agent/TERMINAL-B", ".claude/worktrees/b"))
    assert rc == 0  # TERMINAL-A 已完成，資源釋放，不再視為衝突


# ---------------------------------------------------------------------------
# 跨 repo 歸屬閘門（WF-WORKTREE-REPO-OWNERSHIP1 / #57）
#
# 攔截點在 assign 寫**登記**欄那一刻。以下每一條驗的都是「這筆登記寫不寫得下去」，
# 沒有任何一條驗「磁碟上的 git worktree add 有沒有被阻止」——那在本卡射程外
# （需求方 2026-08-12 裁定，射程與逐字條款見 registry 模組頂端 danger）。
# ---------------------------------------------------------------------------


OTHER_REPO = "acme/other-project"


def _other_repo(tmp_path: Path) -> Path:
    other = tmp_path / "other-project"
    other.mkdir()
    git(other, "init", "-q", "-b", "main")
    git(other, "remote", "add", "origin", f"git@github.com:{OTHER_REPO}.git")
    return other


def test_assign_blocks_declared_cross_repo_before_any_mutation(
    fake_runner, capsys, monkeypatch
):
    """軸 A 的核心路徑：卡屬 acme/workflow，這筆登記卻**明示宣告** worktree 屬於
    acme/other-project → 登記被拒（return 5）。

    只驗回傳碼不算數——這裡同時用 ``_RecordingRunner`` 證明**整條拒絕路徑一次
    mutation 都沒有**，以及卡面欄位與 body 一字未動。閘門若排在任何 set_field_value
    之後，這條會紅。

    ⚠️ 兩件事不要混淆：
    1. 它證明的是「錯的歸屬登記寫不進看板」。它**不**證明磁碟上不會出現跨 repo
       worktree——本測試從頭到尾沒有跑過 ``git worktree add``。
    2. 被擋的是**明示的**宣告。沒帶旗標的跨 repo 登記軸 A 抓不到（``registry`` 模組
       頂端 warning 第 2 條），那一格由軸 B 在路徑已存在時才看得見。
    """
    run_cli(_open_for_assign("CROSS-REPO1"))
    project = resolve_project(fake_runner, "acme", 1)
    before = find_item_by_card_id(list_items(fake_runner, project), "CROSS-REPO1")

    spy = _RecordingRunner(fake_runner)
    monkeypatch.setattr(assign_cmd, "default_runner", spy)
    rc = run_cli(
        _assign_argv("CROSS-REPO1", "某模型@某工具", "b", "/w", source_repo=OTHER_REPO)
    )
    assert rc == 5
    err = capsys.readouterr().err
    assert OTHER_REPO in err and ASSIGN_REPO in err
    assert "卡就開在哪個 repo" in err  # 拒絕訊息必附合法出路（#16 §7.1）

    assert spy.mutations() == []
    assert spy.calls, "代理必須真的攔到呼叫，否則這個斷言是空的"
    after = find_item_by_card_id(list_items(fake_runner, project), "CROSS-REPO1")
    assert after.fields.get("owner") == before.fields.get("owner")
    assert after.fields.get("分支worktree") == before.fields.get("分支worktree")
    assert after.fields["交付狀態"] == before.fields["交付狀態"]
    assert after.body == before.body


def test_assign_refuses_a_directory_given_as_the_declared_repo(fake_runner, tmp_path, capsys):
    """把**目錄**餵給 ``--worktree-source-repo`` 要響，而且不得被反推回 slug。

    上一版這個參數收的正是目錄，並從它的 ``origin`` 反推 repo——需求方 2026-08-13
    查證後推翻該前提（目錄只在單一台機器成立）。所以這裡刻意餵一個**確實存在、
    origin 也確實正確**的目錄：它仍然必須被拒絕。「剛好在這台機器上讀得出正確答案」
    不是接受它的理由。
    """
    run_cli(_open_for_assign("DIRARG1"))
    good_dir = _other_repo(tmp_path)
    rc = run_cli(
        _assign_argv("DIRARG1", "某模型@某工具", "b", "/w", source_repo=str(good_dir))
    )
    assert rc == 5
    err = capsys.readouterr().err
    assert "slug" in err and "不是目錄" in err


def test_assign_needs_no_flag_for_the_production_shape(fake_runner, card_repo_dir):
    """生產慣例（絕對路徑、巢狀在卡自己的 repo 底下、目標尚未建立）→ **零旗標放行**。

    ⚠️ **這條上一輪斷言的是相反的結果**：R3-02 曾要求這一格必須補
    ``--worktree-source-repo``，代價是「未來每一次 assign 多打一個旗標」。需求方
    2026-08-13 推翻了它所依賴的前提（歸屬不該由路徑推），連帶作廢那則裁定，
    所以旗標回到「只有真的要宣告跨 repo 時才打」。
    """
    run_cli(_open_for_assign("NESTED-OK1"))
    wt = card_repo_dir / ".claude" / "worktrees" / "nested-ok1"
    assert not wt.exists()

    assert run_cli(_assign_argv("NESTED-OK1", "某模型@某工具", "b", str(wt))) == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = find_item_by_card_id(list_items(fake_runner, project), "NESTED-OK1")
    assert item.fields["分支worktree"] == f"b @ {wt}"


def test_assign_accepts_a_relative_worktree_path(fake_runner):
    """相對路徑不再被擋。

    Project #4 上實存 18 筆相對路徑（cpbl 那半的慣例）。需求方 2026-08-13 的查證指出
    ``.claude/worktrees/xxx`` 在任何 clone 上指向同一相對位置，**比絕對路徑更可攜**；
    上一版把它判 ``worktree_path_unanchored``／block，收緊的正是比較可攜的那一種。
    """
    run_cli(_open_for_assign("REL-PATH1"))
    rc = run_cli(_assign_argv("REL-PATH1", "某模型@某工具", "b", ".claude/worktrees/x"))
    assert rc == 0
    project = resolve_project(fake_runner, "acme", 1)
    item = find_item_by_card_id(list_items(fake_runner, project), "REL-PATH1")
    assert item.fields["分支worktree"] == "b @ .claude/worktrees/x"


def test_assign_refuses_when_this_machine_contradicts_the_card(
    fake_runner, tmp_path, capsys, monkeypatch
):
    """軸 B：路徑此刻**確實**是別的 repo 的 worktree → 拒絕（return 6），零寫入。

    這是 §8.3 真實漂移的形狀，也是本版唯一還抓得到「沒被注意到的跨 repo」的一格。
    ⚠️ 它是**機器局部**的：換一台沒有這個目錄的機器，這條檢查不會響——訊息必須自己
    講出這件事，否則下一個人會把它讀成歸屬已被驗證。回傳碼刻意與軸 A 分開（6 vs 5）。
    """
    run_cli(_open_for_assign("LOCAL-CONTRA1"))
    other = _other_repo(tmp_path)
    git(other, "-c", "user.email=t@e.com", "-c", "user.name=t", "commit",
        "-q", "--allow-empty", "-m", "init")
    wt = tmp_path / "drifted-wt"
    git(other, "worktree", "add", "-q", "-b", "claude/DRIFT1", str(wt))
    assert wt.is_dir()

    project = resolve_project(fake_runner, "acme", 1)
    before = find_item_by_card_id(list_items(fake_runner, project), "LOCAL-CONTRA1")
    spy = _RecordingRunner(fake_runner)
    monkeypatch.setattr(assign_cmd, "default_runner", spy)

    rc = run_cli(_assign_argv("LOCAL-CONTRA1", "某模型@某工具", "b", str(wt)))
    assert rc == 6
    err = capsys.readouterr().err
    assert OTHER_REPO in err and ASSIGN_REPO in err
    assert "這台機器" in err and "沉默不是判定" in err

    assert spy.mutations() == []
    after = find_item_by_card_id(list_items(fake_runner, project), "LOCAL-CONTRA1")
    assert after.body == before.body


def test_assign_warns_but_proceeds_on_path_nesting_conflict(fake_runner, tmp_path, capsys):
    """路徑座落在別的 repo 目錄樹底下、但目標尚未建立 → **只警告，照樣派工**。

    ⚠️ 這是本版相對上一版**已量測的偵測落差**：同樣的形狀上一版判 block。降級的理由
    不是它沒價值，是它的證據只有「路徑座落在誰底下」，換一台機器就消失。
    **警告沒有執行者**（``docs/ROADMAP.md`` §0），這條測試把那件事寫成可讀的事實。
    """
    run_cli(_open_for_assign("NESTING1"))
    other = _other_repo(tmp_path)
    wt = other / ".claude" / "worktrees" / "not-created"

    rc = run_cli(_assign_argv("NESTING1", "某模型@某工具", "b", str(wt)))
    assert rc == 0
    err = capsys.readouterr().err
    assert "不擋" in err and OTHER_REPO in err

    project = resolve_project(fake_runner, "acme", 1)
    item = find_item_by_card_id(list_items(fake_runner, project), "NESTING1")
    assert item.fields["分支worktree"] == f"b @ {wt}"


def test_assign_log_records_what_the_allow_was_based_on(fake_runner):
    """放行也要留痕：Log 必須說得出這筆歸屬是**有人明示宣告**還是**沒人說**。

    看板欄位對兩種 allow 一模一樣，所以「憑什麼放行」只能靠 Log 保存。軸 B 的觀測碼
    一併記下並標明機器局部——Log 會被跨機器讀，不寫清楚這一句，下一個人就會把「這台
    機器沒看到問題」讀成「沒問題」。
    """
    run_cli(_open_for_assign("PROV-DEFAULT1"))
    assert run_cli(_assign_argv("PROV-DEFAULT1", "某模型@某工具", "b", "/w")) == 0
    log = _assign_log_line(fake_runner, "PROV-DEFAULT1")
    assert f"跨 repo 歸屬 {ASSIGN_REPO}" in log
    assert "未明示，依預設取自卡自己的 repo" in log
    assert "不觀測也不綁定後續的 git worktree add" in log
    assert "本機觀測" in log and "機器局部" in log

    run_cli(_open_for_assign("PROV-EXPLICIT1"))
    assert run_cli(
        _assign_argv("PROV-EXPLICIT1", "某模型@某工具", "b", "/w", source_repo=ASSIGN_REPO)
    ) == 0
    explicit = _assign_log_line(fake_runner, "PROV-EXPLICIT1")
    assert "--worktree-source-repo" in explicit and ASSIGN_REPO in explicit
    # 兩種 allow 在 Log 上必須分得出來，否則留痕等於沒留。
    assert "未明示" not in explicit


def test_assign_blocks_draft_issue_card(fake_runner, capsys):
    """DraftIssue 沒有 Issue URL → 卡的 repo 判不出來 → fail-closed。

    這正是本檔其餘 assign 測試全部得改成真 Issue 的原因，明寫成一條測試而不是
    藏在 fixture 的沉默行為裡。
    """
    run_cli(_open_argv("DRAFT-CARD1"))  # 沒有 --repo ＝ DraftIssue
    rc = run_cli(_assign_argv("DRAFT-CARD1", "某模型@某工具", "b", "/w"))
    assert rc == 5
    assert "判不出卡所屬 repo" in capsys.readouterr().err


def test_assign_registers_the_worktree_source_repo_flag():
    """旗標必須真的註冊在 CLI 上，且**收的是 slug**——型別寫在 metavar 上，不只寫在
    說明文字裡，因為 ``--help`` 的第一眼就是 metavar。"""
    parser = build_parser()
    args = parser.parse_args(
        _assign_argv("FLAG-CARD1", "a", "b", "/w", source_repo="acme/workflow")
    )
    assert args.worktree_source_repo == "acme/workflow"
    # 省略時為 None（＝宣告「屬於卡自己的 repo」），不是空字串。
    assert parser.parse_args(_assign_argv("FLAG-CARD1", "a", "b", "/w")).worktree_source_repo is None

    action = next(
        a for a in parser._subparsers._group_actions[0].choices["assign"]._actions
        if a.dest == "worktree_source_repo"
    )
    assert action.metavar == "OWNER/REPO"


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


def test_handoff_log_line_never_carries_the_status_it_wrote(fake_runner):
    """`UNDECIDABLE_HANDOFF` 的**前提**：handoff 寫進欄位的狀態，復原不出來。

    ⚠️ 本測試是為了取代 `test_doctor.py` 一句**實測為假**的保證而寫（`#118` R2-002）。
    那句話說「若哪天 handoff 的 Log 行開始記狀態，`test_drift_explicit_move_to_backlog_
    is_consistent_and_handoff_stays_undecidable` 的末行會先轉紅」。實測兩件事都不成立：

    1. 該處餵的是手打的 `_HANDOFF_LINE` 常數，與寫入端沒有連線。把 `handoff_cmd` 的
       Log 行改成夾帶 `交付狀態 {new_status}` 之後，那條測試照樣綠。
    2. **就算把夾帶狀態的行直接餵進 `audit_state_face_drift` 也還是綠**——
       `derive_expected_status` 對 `handoff by wf-cli` 開頭是無條件短路、從不看行內容。
       所以查核者建議的「改成真正從 handoff 輸出餵入 doctor」這個修法**單獨也救不了
       那句話**：只要讀取端還短路，那條斷言就恆綠。要它轉紅得同時改讀取端，而那不是
       一句註解描述得了的事。

    真正可證偽、也真正撐住 `undecidable` 正當性的，是**寫入端的留痕復原不出狀態**這件
    事本身——那與 doctor 怎麼判無關。下面三條各自會被什麼推翻，逐條講明：

    - `written_status not in line`：寫入端開始把狀態值寫進 Log 行時紅。**這就是那句
      保證原本想講的事**，改由這裡承接。
    - `stage not in line`：寫入端改記 `--next-stage` 鍵（`review`…）時紅。那同樣讓
      `doctor.HANDOFF_STAGE_EXPECTED_STATUS` 查得出狀態，是第二條復原路徑。
    - 餵**產生器實際輸出**進 doctor 仍回 `UNDECIDABLE_HANDOFF`：寫入端改掉行首前綴、
      或改到 `parse_log_events` 切不出事件時紅。實測改前綴時**先紅的是上面那行
      `startswith`**，但把該行拿掉本條自己也接得住（落 `unrecognized_event`）——兩條
      各自成立，不是一條靠另一條。⚠️ 它**不會**因為行內多了狀態而紅（上面第 2 點）；
      列在這裡是為了釘「寫入端前綴 ↔ 讀取端前綴」這條連線，不是為了接住狀態。

    ⛔ 沒封住的：狀態若以上面兩個字面之外的編碼進 Log（自創縮寫、內部代碼），本測試
    看不見。那是開放集合，不假裝封得住。
    """
    project = resolve_project(fake_runner, "acme", 1)
    run_cli(_open_argv("HANDOFF-LOGLINE1"))

    # 六個 next-stage 逐一跑**真的** handoff。順序讓 planning 緊接 backlog 之前，
    # 好讓 `BACKLOG_REQUIRED_PRIOR_STATUS` 的前提自然成立（不是繞過閘門）。
    ordered = ["requirement", "research", "planning", "backlog", "implementation", "review"]
    assert set(ordered) == set(handoff_cmd.STAGE_STATUS), ordered

    for i, stage in enumerate(ordered):
        assert run_cli(
            _handoff_argv("HANDOFF-LOGLINE1", str(i) * 40, **{"--next-stage": stage})
        ) == 0, stage
        item = list_items(fake_runner, project)[0]
        written_status = item.fields["交付狀態"]
        assert written_status == handoff_cmd.STAGE_STATUS[stage], stage

        # 這一行是產生器**這一次實際寫下**的東西，不是測試自己組的字串。
        events, undecidable_reason = parse_log_events(item.body)
        assert undecidable_reason is None, (stage, undecidable_reason)
        line = events[-1].splitlines()[0]
        assert line.startswith("handoff by wf-cli"), line

        assert written_status not in line, (stage, line)
        assert stage not in line, (stage, line)

        finding = audit_state_face_drift("HANDOFF-LOGLINE1", item.body, written_status)
        assert (finding.verdict, finding.rule) == ("undecidable", UNDECIDABLE_HANDOFF), stage

    # `release` 不在迴圈裡（它另有部署驗證前提），但它與上面六個共用同一個格式字串。
    # 「共用」不用散文宣稱：整個模組只有這一處產生 handoff 的 Log 行。多出第二處時本行
    # 紅，屆時上面的迴圈就不再窮舉，得有人回來補。
    assert inspect.getsource(handoff_cmd).count("handoff by wf-cli") == 1


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


def test_handoff_next_stage_backlog_writes_backlog_only_from_planning(fake_runner, capsys):
    """WF-BACKLOG-STAGE1 端到端：`📥Backlog` 有了專責 writer，且那個 writer 受前提檢查。

    ⚠️ 兩個方向都在同一條測試裡，因為只驗放行那一半的話，一個「無條件寫
    📥Backlog」的實作也會通過。
    """
    run_cli(_open_argv("BACKLOG-CARD1"))
    project = resolve_project(fake_runner, "acme", 1)

    # ⚠️ 起點刻意先推到 🔨執行中。**本註解的原始理由已於 WF-OPEN-INITIAL-STATUS1
    # 失效**：寫下它時 `open` 的預設是 📥Backlog，所以剛開的卡分不出「拒絕生效」與
    # 「拒絕失效」；現在 `open` 預設是 💡需求，那個混淆不存在了。但這一步**保留**，
    # 理由換成更強的一條：💡需求 與 🔨執行中 都不是 🧭規劃中，而 🔨執行中 是實際
    # 看板上最常見的非法起點，用它當樣本比用開卡預設值更有鑑別力。
    assert run_cli(
        _handoff_argv("BACKLOG-CARD1", "0" * 40, **{"--next-stage": "implementation"})
    ) == 0
    assert list_items(fake_runner, project)[0].fields["交付狀態"] == "🔨執行中"

    # (b) 前提不成立時必須拒絕：🔨執行中 不是 🧭規劃中。
    blocked_sha = "1" * 40
    rc_blocked = run_cli(
        _handoff_argv("BACKLOG-CARD1", blocked_sha, **{"--next-stage": "backlog"})
    )
    assert rc_blocked == 4
    # 卡的級別是 T3（`_open_argv` 預設）⇒ 走課前提的那一支。
    assert "當下交付狀態必須是 🧭規劃中" in capsys.readouterr().err
    item = list_items(fake_runner, project)[0]
    assert item.fields["交付狀態"] == "🔨執行中"      # 欄位一格都沒被寫
    assert f"SHA {blocked_sha}" not in item.body      # Log 也沒留下這次交接

    # 先合規地過規劃階段。
    assert run_cli(
        _handoff_argv("BACKLOG-CARD1", "2" * 40, **{"--next-stage": "planning"})
    ) == 0
    item = list_items(fake_runner, project)[0]
    assert item.fields["交付狀態"] == "🧭規劃中"

    # (a) 前提成立 → 專責動詞寫出 📥Backlog。
    assert run_cli(
        _handoff_argv("BACKLOG-CARD1", "3" * 40, **{"--next-stage": "backlog", "--to": "待認領"})
    ) == 0
    item = list_items(fake_runner, project)[0]
    assert item.fields["交付狀態"] == "📥Backlog"
    assert item.fields["owner"] == "待認領"
    assert item.fields["iteration"] == 1  # 起點那次 implementation 記的 1，backlog 不遞增
    assert f"SHA {'3' * 40}" in item.body


def test_handoff_backlog_gate_is_bypassed_by_the_free_text_status_flag(fake_runner):
    """誠實邊界：``--status`` 仍然繞得過本閘門——與 ``release`` 的部署閘門同形。

    這**不是**本卡新開的口（`--status` 加 choices 是獨立一問，見
    docs/CONTRACT_TOOL_RECONCILE.md §4.1）。釘住它是為了讓「這個檢查有多強」寫在
    測試裡而不是只寫在散文裡：宣稱它擋得住所有路徑的人會被這條測試打臉。
    """
    run_cli(_open_argv("BACKLOG-CARD2"))
    project = resolve_project(fake_runner, "acme", 1)
    assert run_cli(
        _handoff_argv("BACKLOG-CARD2", "4" * 40, **{"--next-stage": "implementation"})
    ) == 0
    assert list_items(fake_runner, project)[0].fields["交付狀態"] == "🔨執行中"

    # 卡在 🔨執行中（非 🧭規劃中），但帶 --status 就整條前提鏈都不跑。
    assert run_cli(
        _handoff_argv(
            "BACKLOG-CARD2", "5" * 40,
            **{"--next-stage": "backlog", "--status": "📥Backlog"},
        )
    ) == 0
    assert list_items(fake_runner, project)[0].fields["交付狀態"] == "📥Backlog"


@pytest.mark.parametrize("tier", ["T0", "T1"])
def test_handoff_backlog_lets_t0_t1_through_without_any_precondition(fake_runner, capsys, tier):
    """R1-001 丙案的**放行**那一半：T0／T1 直通，而且明說「這裡沒有檢查」。

    canonical ``AI_WORKFLOW.md`` §3.1 的表沒有 T0／T1 的列 ⇒ 沒有條文就沒有可執行的
    前提。⚠️ 這條測試同時釘住 stderr 的告知：直通分支必須**看得出來它沒檢查**，
    不能與「檢查通過」在輸出上長得一樣——那正是空殼閘門的形態。
    """
    card = f"BACKLOG-{tier}"
    run_cli(_open_argv(card, **{"--tier": tier}))
    project = resolve_project(fake_runner, "acme", 1)

    # 推到 🔨執行中：一個對 T2 以上必定被拒的起點，用來證明放行不是因為狀態剛好合格。
    assert run_cli(_handoff_argv(card, "6" * 40, **{"--next-stage": "implementation"})) == 0
    assert list_items(fake_runner, project)[0].fields["交付狀態"] == "🔨執行中"
    capsys.readouterr()

    assert run_cli(_handoff_argv(card, "7" * 40, **{"--next-stage": "backlog"})) == 0
    assert list_items(fake_runner, project)[0].fields["交付狀態"] == "📥Backlog"
    err = capsys.readouterr().err
    assert f"級別 {tier} 直通" in err
    assert "本次未做任何前身狀態檢查" in err


def test_handoff_backlog_gate_applies_from_t2_up_not_only_t3(fake_runner, capsys):
    """R1-001 丙案的**擋人**那一半，且刻意逐級別列舉——甲案（T3-only）會在 T2 那格轉紅。

    ⚠️ 只驗 T3 被擋是不夠的：甲案與丙案在 T3 上的行為完全相同，那個樣本分不出兩者。
    有鑑別力的樣本是 **T2**（實測看板上佔 35%）。
    """
    blocked: dict[str, int] = {}
    for tier in ("T2", "T3", "T4"):
        card = f"BACKLOG-GATED-{tier}"
        run_cli(_open_argv(card, **{"--tier": tier}))
        assert run_cli(_handoff_argv(card, "8" * 40, **{"--next-stage": "implementation"})) == 0
        capsys.readouterr()
        blocked[tier] = run_cli(_handoff_argv(card, "9" * 40, **{"--next-stage": "backlog"}))
        err = capsys.readouterr().err
        assert f"級別 {tier}" in err
        assert "當下交付狀態必須是 🧭規劃中" in err

    assert blocked == {"T2": 4, "T3": 4, "T4": 4}

    # 欄位一格都沒被寫（拒絕路徑零寫入）。
    project = resolve_project(fake_runner, "acme", 1)
    for item in list_items(fake_runner, project):
        if (item.fields.get("卡ID") or "").startswith("BACKLOG-GATED-"):
            assert item.fields["交付狀態"] == "🔨執行中"


def test_handoff_backlog_gate_blocks_when_tier_is_unreadable(fake_runner, capsys):
    """級別讀不到／為空／不在語彙內 → 照 T2 以上處理（fail closed）。

    ⚠️ 這三種輸入**只走 ``wfcli`` 產不出來**（``open`` 必填且驗過語彙，Project 欄位是
    只有 T0–T4 的 SINGLE_SELECT），所以這裡直接構造 fake 的欄位字典——它模擬的是**帶外**
    途徑：GitHub UI 改欄位／加選項，或 ``open`` 半寫入。這條測試證明的是「真的發生時往
    哪邊倒」，不是「這件事常發生」。
    """
    run_cli(_open_argv("BACKLOG-BADTIER"))
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]

    raw_fields = fake_runner.items[item.item_id]["fields"]
    for label, mutate in (
        ("缺欄位", lambda f: f.pop("級別", None)),
        ("空字串", lambda f: f.__setitem__("級別", "")),
        ("語彙外", lambda f: f.__setitem__("級別", "T9")),
        ("非字串", lambda f: f.__setitem__("級別", 2.0)),
    ):
        raw_fields["級別"] = "T3"
        mutate(raw_fields)
        # ⭐ 起點刻意是 🔨執行中（**不合格**的前身）：fail closed 會拒、fail open 會放行，
        # 兩種預設在這個樣本上分得開。起點若取 🧭規劃中，兩者都放行、樣本零鑑別力。
        raw_fields["交付狀態"] = "🔨執行中"
        capsys.readouterr()
        rc = run_cli(_handoff_argv("BACKLOG-BADTIER", "b" * 40, **{"--next-stage": "backlog"}))
        assert rc == 4, label
        assert "不在 T0–T4 語彙內" in capsys.readouterr().err, label
        assert raw_fields["交付狀態"] == "🔨執行中", label


def test_handoff_backlog_gate_does_not_accept_blocked_as_a_prior_status(fake_runner, capsys):
    """⛔ ``⏸阻塞`` 不是合法前身——實查 ``⏸阻塞`` → ``📥Backlog`` 的實例為 0。

    釘住它是因為「已經被阻塞過的卡回待辦池」聽起來很合理；把它加進合法前身集合會讓
    這道閘門變成零資訊的檢查，而那個改動不會有任何既有測試轉紅。
    """
    run_cli(_open_argv("BACKLOG-BLOCKED"))
    project = resolve_project(fake_runner, "acme", 1)
    item = list_items(fake_runner, project)[0]
    fields = ensure_fields(fake_runner, "acme", 1)
    set_field_value(fake_runner, project, item.item_id, fields["交付狀態"], "⏸阻塞")
    capsys.readouterr()

    assert run_cli(_handoff_argv("BACKLOG-BLOCKED", "c" * 40, **{"--next-stage": "backlog"})) == 4
    assert "目前交付狀態=⏸阻塞" in capsys.readouterr().err
    assert list_items(fake_runner, project)[0].fields["交付狀態"] == "⏸阻塞"


def test_backlog_gate_exempt_tiers_mirror_the_canonical_rule_text(fake_runner):
    """⭐ 分流規則必須先寫進 canonical，工具只是執行者。

    ⚠️ 這條測試讀的是 ``AI_WORKFLOW.md`` 的正文。它會在「有人改了碼裡的級別集合卻沒
    改條文」時轉紅——那正是本卡要治的病（工具執行 canonical 沒說的規則）。
    """
    canonical = (
        Path(__file__).resolve().parents[2] / "AI_WORKFLOW.md"
    ).read_text(encoding="utf-8")
    rule = [ln for ln in canonical.splitlines() if "進 `📥Backlog` 的狀態前提依級別分流" in ln]
    assert len(rule) == 1, "canonical 必須恰好有一條分流條文"
    text = rule[0]
    assert "**T2 以上**" in text and "當下的交付狀態必須是 `🧭規劃中`" in text
    assert "**T0／T1 直通**" in text
    assert "不在 T0–T4 語彙內時，一律照 T2 以上處理" in text
    # 碼側的豁免集合逐字對得上條文點名的兩級，且**只有**這兩級。
    assert handoff_cmd.BACKLOG_GATE_EXEMPT_TIERS == ("T0", "T1")
    assert all(f"{t}／" in text or f"／{t}" in text for t in handoff_cmd.BACKLOG_GATE_EXEMPT_TIERS)


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


# ---------------------------------------------------------------------------
# 標題後綴守衛（WF-RESOURCE-HEADING-SUFFIX1；需求方 2026-08-25 於 T3 放行時裁定加入）
#
# 2026-08-04 的 state-plane 遷移寫出的標題逐字帶括號補述，而那句補述**不是排版**：
# 它是「未正式宣告 vs 無資源」這條分界今天的**唯一載體**——schema 的 resources 型別
# 是 list[str]，`null` 被拒、缺鍵靜默變 []，⇒ 機器面沒有第三個狀態（實測）。
#
# ⚠️ 本測試**必須端到端**（amend_cmd → render_block → amend_resource_block）：
# 缺陷形態是「**呼叫端沒傳 heading**」，只測 render_block 一個函式測不到它。
# ---------------------------------------------------------------------------

MIGRATION_SUFFIXED_HEADING = (
    "## 資源宣告（機器可讀；`null`／`[]` 代表未正式宣告，不代表無資源）"
)


def test_amend_resources_preserves_the_migration_heading_suffix_end_to_end(fake_runner):
    run_cli(_open_argv("SUFFIX-CARD", **{"--repo": ASSIGN_REPO, "--resources": "file:a.py"}))
    project = resolve_project(fake_runner, "acme", 1)
    item = find_item_by_card_id(list_items(fake_runner, project), "SUFFIX-CARD")
    body = item.body.replace("## 資源宣告", MIGRATION_SUFFIXED_HEADING, 1)
    set_item_body(
        fake_runner, item.content_type, item.content_id, project,
        ASSIGN_REPO, item.issue_number, body,
    )

    rc = run_cli([
        "amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "SUFFIX-CARD",
        "--reason", "換宣告內容，驗標題是否被正規化掉",
        "--resources", "file:b.py", "--db-scope", "none",
    ])
    assert rc == 0

    after = find_item_by_card_id(list_items(fake_runner, project), "SUFFIX-CARD").body
    head = after.split("\n## Log", 1)[0]
    headings = [l for l in head.splitlines() if l.startswith("## 資源宣告")]
    assert headings == [MIGRATION_SUFFIXED_HEADING], f"標題被正規化掉了：{headings}"
    # ⭐ 這一條是**守衛自己的負控**：若寫入根本沒發生，「標題保留」是零資訊。
    assert "file:b.py" in after
    assert "file:a.py" not in head


def test_amend_restores_the_migration_header_end_to_end(fake_runner):
    """⭐ 端到端，⛔ 非單元：單元測不到「旗標沒接上 dispatch」這個形態。

    ⚠️ 卡面用的是**真實遷移卡** body（`cpbl#57`，見 tests/test_card.py 的
    `_REAL_MIGRATION_HEAD`），⛔ 不是 `render_issue_body` 造的——自造樣本必然帶
    完整章節，測不出這條路徑要處理的形狀。
    """
    from tests.test_card import _REAL_MIGRATION_HEAD

    run_cli(_open_argv("MIG-HEADER-CARD", **{"--repo": ASSIGN_REPO}))
    project = resolve_project(fake_runner, "acme", 1)
    item = find_item_by_card_id(list_items(fake_runner, project), "MIG-HEADER-CARD")
    log = item.body.split("\n## Log", 1)[1]
    migrated = _REAL_MIGRATION_HEAD + "\n\n## Log" + log
    set_item_body(
        fake_runner, item.content_type, item.content_id, project,
        ASSIGN_REPO, item.issue_number, migrated,
    )

    rc = run_cli([
        "amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "MIG-HEADER-CARD",
        "--reason", "第四段：補回標頭；來源 18b71cc5:docs/tasks/X.md，舊值原文 `ruan6047（…）`，"
                    "正規化規則＝去尾端括號補述、括號原文留在本行",
        "--restore-migration-header",
        "--header-requested-by", "ruan6047",
        "--header-planned-by", "本卡 spec",
        "--header-spec-baseline", "`2f52562f`",
    ])
    assert rc == 0

    after = find_item_by_card_id(list_items(fake_runner, project), "MIG-HEADER-CARD").body
    head = after.split("\n## Log", 1)[0]
    assert head.splitlines()[0] == "- 需求：ruan6047\u3000規劃：本卡 spec"
    for heading in ("## 核心痛點", "## 驗收條件", "## 驗證"):
        assert [l.strip() for l in head.splitlines()].count(heading) == 1
    # ⭐ 負控：證明寫入真的發生過，⛔ 否則上面的斷言在「什麼都沒做」時也可能成立。
    assert "遷移自" in head and "第四段：補回標頭" in after
    # ⛔ 不得產生內容。
    assert "- **痛點**：" not in head


def test_amend_restore_header_refuses_a_card_that_already_has_it(fake_runner):
    """⛔ 負控：對正規卡面（open 產生的）必須拒絕，rc != 0 且 body 逐位元不變。"""
    run_cli(_open_argv("MIG-HEADER-OK", **{"--repo": ASSIGN_REPO}))
    project = resolve_project(fake_runner, "acme", 1)
    before = find_item_by_card_id(list_items(fake_runner, project), "MIG-HEADER-OK").body

    rc = run_cli([
        "amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "MIG-HEADER-OK",
        "--reason", "應被拒",
        "--restore-migration-header",
        "--header-requested-by", "ruan6047", "--header-planned-by", "x",
    ])
    assert rc != 0
    after = find_item_by_card_id(list_items(fake_runner, project), "MIG-HEADER-OK").body
    assert after == before


# ---------------------------------------------------------------------------
# WF-CARD-BODY-BUDGET1：Log 成本 O(1) 化 ＋ 卡面容量預算
#
# ⚠️ 這些測試必須真的走到**指紋**路徑。先前一版用
# `runner.run_json(["api","graphql",...])`，`FakeGhRunner` 認不得 ⇒ 拋錯 ⇒ 被
# `_prior_revision_recoverable` 的 except 吞掉 ⇒ 一律回傳 False ⇒ **全部測試都走全文
# 退路、指紋路徑一次都不會被跑到**。那是「守衛在測試裡從不執行」，⛔ 不得再發生。
# 下面每一支都斷言「Log 裡有沒有 sha256:」，正向與負向各自釘住一條路徑。
# ---------------------------------------------------------------------------


def _budget_card(fake_runner, card_id="BUDGET-CARD"):
    run_cli(_open_argv(card_id, **{"--repo": ASSIGN_REPO}))
    project = resolve_project(fake_runner, "acme", 1)
    return project, find_item_by_card_id(list_items(fake_runner, project), card_id)


def test_log_records_fingerprints_not_full_text_when_a_revision_exists(fake_runner):
    """V1：有前一版時，Log 記指紋、⛔ 不含舊值任何一段連續 20 字元。"""
    project, _ = _budget_card(fake_runner)
    marker = "這段舊驗收條文長到足以逐字比對" * 2
    run_cli(["amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "BUDGET-CARD",
             "--reason", "先放一段可辨識的舊值", "--acceptance", marker])
    run_cli(["amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "BUDGET-CARD",
             "--reason", "改掉它，這次應記指紋", "--acceptance", "新的驗收"])
    body = find_item_by_card_id(list_items(fake_runner, project), "BUDGET-CARD").body
    log = body.split("\n## Log", 1)[1]
    last = log.strip().splitlines()[-1]
    assert "sha256:" in last, f"沒走到指紋路徑：{last[:200]}"
    assert marker[:20] not in last, "舊值全文仍留在最後一筆 Log"


def test_first_write_falls_back_to_full_text(fake_runner):
    """V4：`totalCount == 0`（首寫）平台無前一版 ⇒ 必須寫全文。"""
    project, _ = _budget_card(fake_runner, "BUDGET-FIRST")
    run_cli(["amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "BUDGET-FIRST",
             "--reason", "首寫", "--acceptance", "只有這一條"])
    body = find_item_by_card_id(list_items(fake_runner, project), "BUDGET-FIRST").body
    last = body.split("\n## Log", 1)[1].strip().splitlines()[-1]
    assert "sha256:" not in last
    assert "totalCount=0" in last, f"未載明退回全文的理由：{last[:200]}"


def test_unavailable_revision_content_falls_back_to_full_text(fake_runner):
    """⭐ 第三條退路：平台記了版本但內容取回 null ⇒ 仍須寫全文。

    ⚠️ 這條是本卡執行期新增的。A9 的實測只把已驗證區間由 39 版推到 50 版
    （`aiwf#16`，50/50 全數可取），⛔ 沒有證明無上限、⛔ 沒有官方保證、
    >39 版的樣本只有 1 個、最舊僅回溯 8 天。⇒ 設計必須對「取不到」fail-safe。
    """
    project, _ = _budget_card(fake_runner, "BUDGET-NULL")
    run_cli(["amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "BUDGET-NULL",
             "--reason", "建立一版", "--acceptance", "第一版"])
    fake_runner.revision_content_unavailable = True
    try:
        run_cli(["amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "BUDGET-NULL",
                 "--reason", "內容取不到時應退回全文", "--acceptance", "第二版"])
    finally:
        fake_runner.revision_content_unavailable = False
    last = find_item_by_card_id(list_items(fake_runner, project), "BUDGET-NULL").body
    last = last.split("\n## Log", 1)[1].strip().splitlines()[-1]
    assert "sha256:" not in last
    assert "取回為 null" in last, f"未載明退回全文的理由：{last[:200]}"


def test_non_body_sourced_old_value_is_always_written_in_full(fake_runner):
    """⭐ 第四條退路：舊值不是取自 body 者一律寫全文。

    `userContentEdits` 保存的是**前一版 body**。雙面不同步自癒時，舊值只存在於
    Project 欄位、**從來沒出現在任何一版 body 裡** ⇒ 指紋不可還原。
    ⇒ 旗標**預設 False**，body 來源者才 opt-in：日後新增非 body 來源而忘了標記時，
    退路是「多寫全文」⛔ 不是「靜默丟資料」。

    ⚠️ **本測試在自審時被換掉。** 原版只斷言一個本機 tuple 的長度與預設值
    ——把預設改成危險方向（`True`）它照樣全綠 ⇒ **零資訊**。
    ⭐ 真正的負控是 `test_amend.py::test_stale_project_field_converges_on_rerun`
    （逐字斷言「原值必須留在 Log」），已實測：把預設改成 `True` 時它轉紅。
    本測試改為釘住**預設方向本身**在原始碼裡的字面，讓「有人把它改回 True」
    這件事在本檔也留下一道明示的檢查。
    """
    from pathlib import Path

    from wf_cli.commands import amend_cmd

    source = Path(amend_cmd.__file__).read_text(encoding="utf-8")
    assert "else False" in source and "body_sourced = entry[4] if len(entry) > 4 else False" in source, (
        "body_sourced 的預設必須是 False（寫全文）。"
        "⛔ 改成 True 會讓非 body 來源的舊值被指紋化而永久不可還原；"
        "端到端負控見 test_amend.py::test_stale_project_field_converges_on_rerun。"
    )
    assert hasattr(amend_cmd, "_fingerprint")


def test_budget_line_is_printed_on_every_write(fake_runner, capsys):
    """V7：預算行的四個數字。"""
    _budget_card(fake_runner, "BUDGET-LINE")
    capsys.readouterr()
    run_cli(["amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "BUDGET-LINE",
             "--reason", "看預算行", "--acceptance", "一條"])
    out = capsys.readouterr().out
    assert "卡面預算：" in out
    for token in ("本次 +", "寫入後 ", "上限 129,486", "餘裕 ", "還能改 "):
        assert token in out, f"預算行缺 {token!r}：{out}"


def test_budget_line_is_printed_on_dry_run_too(fake_runner, capsys):
    """V7：`--dry-run` 也要印（A4 逐字），且要說明這次會用哪種記法。"""
    _budget_card(fake_runner, "BUDGET-DRY")
    capsys.readouterr()
    run_cli(["amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "BUDGET-DRY",
             "--reason", "dry-run 也要有", "--acceptance", "一條", "--dry-run"])
    out = capsys.readouterr().out
    assert "卡面預算：" in out
    assert "Log 記法：" in out


def test_hard_line_refuses_and_leaves_the_body_untouched(fake_runner, capsys):
    """V5：寫入後會超過上限 ⇒ rc≠0、body 逐位元未變、訊息指出最大可壓縮章節。"""
    project, _ = _budget_card(fake_runner, "BUDGET-HARD")
    before = find_item_by_card_id(list_items(fake_runner, project), "BUDGET-HARD").body
    capsys.readouterr()
    rc = run_cli(["amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "BUDGET-HARD",
                  "--reason", "超大寫入", "--acceptance", "撐" * 70_000])
    assert rc != 0
    after = find_item_by_card_id(list_items(fake_runner, project), "BUDGET-HARD").body
    assert after == before, "拒絕時必須零寫入"
    err = capsys.readouterr().err
    assert "超過上限" in err
    assert "最大的可壓縮章節" in err


def test_soft_threshold_warns_but_passes(fake_runner, capsys):
    """V6：餘裕低於軟門檻時**警告但放行**——⛔ 擋了會讓人學會繞過。"""
    from wf_cli.commands.amend_cmd import BODY_LIMIT, BODY_SOFT_MARGIN

    project, item = _budget_card(fake_runner, "BUDGET-SOFT")
    # 先寫一次建立平台版本，⇒ 第二次走指紋路徑、Log 成本 O(1)，
    # 大小才由驗收欄本身決定。⛔ 不寫死魔術數字：由 BODY_LIMIT 推算落點。
    run_cli(["amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "BUDGET-SOFT",
             "--reason", "建立一版", "--acceptance", "短"])
    item = find_item_by_card_id(list_items(fake_runner, project), "BUDGET-SOFT")
    base = len(item.body)  # ⚠️ 字元，⛔ 不是位元組
    # 目標：寫入後落在 (BODY_LIMIT - BODY_SOFT_MARGIN, BODY_LIMIT) 之間。
    target = BODY_LIMIT - BODY_SOFT_MARGIN // 2
    padding = "撐" * max(1, target - base - 600)
    capsys.readouterr()
    rc = run_cli(["amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "BUDGET-SOFT",
                  "--reason", "逼近但不超過", "--acceptance", padding])
    assert rc == 0, "軟門檻不得阻擋"
    err = capsys.readouterr().err
    assert "警告" in err and "本次仍放行" in err
    body = find_item_by_card_id(list_items(fake_runner, project), "BUDGET-SOFT").body
    assert "撐" * 100 in body, "放行卻沒寫進去"


def test_body_limit_is_the_measured_value_not_the_documented_one():
    """A5：⛔ 不得寫 65,536。"""
    from wf_cli.commands.amend_cmd import BODY_LIMIT

    assert BODY_LIMIT == 129_486
    assert BODY_LIMIT != 65_536


def test_fingerprint_is_full_length_sha256_with_byte_count():
    """A1：⛔ 不截短——碰撞成本必須留在密碼學等級。"""
    import hashlib

    from wf_cli.commands.amend_cmd import _fingerprint

    text = "測試值"
    fp = _fingerprint(text)
    assert hashlib.sha256(text.encode()).hexdigest() in fp
    assert f"({len(text.encode())} bytes)" in fp


def test_hard_line_tells_a_shrinking_repair_that_the_direction_is_right(fake_runner, capsys):
    """⭐ 自審抓到：**已經**超上限的卡在做壓縮修復時，訊息不能叫它「請先壓縮」。

    `aiwf#105` 曾是 129,651 位元組。若它用 `amend` 一次縮不到上限以下，
    原本的訊息會給出它正在執行的那個指示 ⇒ ⛔ 零幫助。
    ⇒ `cost < 0`（body 變小）與 `cost >= 0`（撐大）給的下一步完全不同。
    ⚠️ 兩者都仍 rc≠0：body 超過上限時 GitHub 本來就會拒收——這裡擋的是白跑一趟。

    情境構造：`## 驗證` 單獨就超過上限（⇒ 怎麼壓 `## 驗收條件` 都回不到線下），
    而 `## 驗收條件` 有可觀大小（⇒ 換成小值時 body 確實變小）。
    """
    import re

    from wf_cli.commands.amend_cmd import BODY_LIMIT

    project, _ = _budget_card(fake_runner, "BUDGET-SHRINK")
    run_cli(["amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "BUDGET-SHRINK",
             "--reason", "建立一版", "--acceptance", "短"])
    item = find_item_by_card_id(list_items(fake_runner, project), "BUDGET-SHRINK")

    # 直接把 body 灌成「已超限」的事故狀態：驗證 > 上限、驗收條件另有 30,000 位元組。
    head, _, log = item.body.partition("\n## Log")
    head = re.sub(r"## 驗收條件\n.*?(?=\n## )", "## 驗收條件\n\n- [ ] " + "甲" * 10_000, head, flags=re.DOTALL)
    head = re.sub(r"## 驗證\n.*$", "## 驗證\n\n- [ ] " + "乙" * (BODY_LIMIT + 500), head, flags=re.DOTALL)
    over = head + "\n## Log" + log
    assert len(over) > BODY_LIMIT, "構造失敗：卡沒有超過上限"
    fake_runner.issues[item.issue_url]["body"] = over
    for it in fake_runner.items.values():
        if it.get("issue_url") == item.issue_url:
            it["body"] = over

    capsys.readouterr()
    rc = run_cli(["amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "BUDGET-SHRINK",
                  "--reason", "壓縮修復：把驗收條件縮成一行", "--acceptance", "壓縮後的一行"])
    # ⚠️ 只能取一次——第二次 readouterr() 拿到的是清空後的新捕獲。
    captured = capsys.readouterr()
    err = captured.err
    assert rc != 0, "驗證欄單獨就超限，⇒ 這次不可能回到線下"
    assert "方向對了、幅度不夠" in err, f"縮小中的修復收到錯誤指引：{err[:400]}"
    assert "請先把該章節的原文封存成留言" not in err


def test_draft_issue_card_always_falls_back_to_full_text(fake_runner):
    """A2(a)：`DraftIssue` 型別上**沒有** `userContentEdits` ⇒ 平台零保存 ⇒ 必須寫全文。

    ⚠️ 2026-08-25 對真實 GraphQL schema 實測：
    `{ __type(name:"DraftIssue"){ fields{name} } }` 回
    `assignees body bodyHTML bodyText createdAt creator id projectV2Items projectsV2 title updatedAt`
    ——⛔ 無 `userContentEdits`。⇒ 對 draft 卡記指紋是**不可逆損失**。

    ⭐ A2 逐字要求「兩條各須有獨立測試」。自審發現 (b) 有、(a) 沒有——本檔原有的
    四處 `DraftIssue` 全屬 `assign` 的 repo 判定，⛔ 與本卡無關。
    """
    run_cli(_open_argv("DRAFT-BUDGET"))  # 沒有 --repo ＝ DraftIssue
    project = resolve_project(fake_runner, "acme", 1)
    run_cli(["amend", *BASE_TARGET, "DRAFT-BUDGET",
             "--reason", "draft 卡必須寫全文", "--acceptance", "可辨識的驗收原文"])
    body = find_item_by_card_id(list_items(fake_runner, project), "DRAFT-BUDGET").body
    last = body.split("\n## Log", 1)[1].strip().splitlines()[-1]
    assert "sha256:" not in last, f"draft 卡竟走了指紋路徑：{last[:200]}"
    assert "content_type=DraftIssue" in last, f"未載明退回全文的理由：{last[:200]}"


def test_fingerprint_path_never_says_the_full_text_is_in_the_log(fake_runner, capsys):
    """R1-001（`GPT-5@Codex` 2026-08-26，major／blocking）。

    `_short()` 原本無條件輸出「全文 N 字，**見 Log**」，而指紋路徑的 Log
    **只有 sha256、沒有全文** ⇒ 同一次輸出會同時出現「Log 記法：指紋」與
    「見 Log」，後者是**錯誤的還原指引**。

    查核者逐字要求的回歸：「建立可還原版本後，以**超過 `_short` 門檻**的舊值
    執行 `amend`／`dry-run`，斷言輸出不含「見 Log」且明示平台版本還原路徑。」
    """
    _budget_card(fake_runner, "SHORT-WHERE")
    long_old = "確認訊息一致性的長字串" * 40          # 遠超過 _short 的 80/100 門檻
    run_cli(["amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "SHORT-WHERE",
             "--reason", "建立一版可還原的前一版", "--acceptance", long_old])
    capsys.readouterr()
    run_cli(["amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "SHORT-WHERE",
             "--reason", "這次應走指紋路徑", "--acceptance", "新的短驗收"])
    out = capsys.readouterr().out
    assert "Log 記法" not in out or "指紋" in out
    assert "見 Log" not in out, f"指紋路徑仍宣稱全文在 Log：{out}"
    assert "見平台前一版" in out, f"未明示平台版本還原路徑：{out}"


def test_full_text_path_still_says_the_log(fake_runner, capsys):
    """⭐ 負控：走**全文**退路時「見 Log」是**對的**，⛔ 不得一併刪掉。

    ⛔ 只驗「指紋路徑不說見 Log」是零資訊——把 `where` 寫死成
    「見平台前一版」也能讓那支測試全綠，而那對全文退路是錯的指引。
    """
    _budget_card(fake_runner, "SHORT-WHERE-FULL")
    capsys.readouterr()
    # 首寫 ⇒ totalCount==0 ⇒ 走全文退路
    run_cli(["amend", *BASE_TARGET, "--repo", ASSIGN_REPO, "SHORT-WHERE-FULL",
             "--reason", "首寫應走全文", "--acceptance", "確認訊息一致性的長字串" * 40])
    out = capsys.readouterr().out
    assert "見 Log" in out, f"全文退路卻沒指向 Log：{out}"
    assert "見平台前一版" not in out


def test_fold_docstring_no_longer_claims_the_log_is_the_only_recovery_point():
    """R1-001 的第二半：`_fold()` 的 docstring 逐字寫「Log 是唯一還原點」，
    而那正是本卡推翻的前提——⛔ 改了行為卻沒改它。
    """
    from wf_cli.commands.amend_cmd import _fold

    doc = _fold.__doc__ or ""
    assert "Log 是唯一還原點。" not in doc, "過期前提仍留在 docstring"
    assert "userContentEdits" in doc, "未說明真正的還原點"
    assert "不截斷" in doc, "⛔ 不得連同仍然成立的部分一起刪掉"


def test_no_user_facing_text_still_claims_the_log_holds_the_full_old_value():
    """⭐ 自審（R2 送審前）：R1-001 的同族還有兩處，查核者沒點到。

    - `add_parser` 的 help 逐字「原值寫入 Log」
    - 模組 docstring 逐字「唯一還原點，摘要不能取代全文」

    ⇒ 掃全檔的**使用者可見字串**，斷言沒有任何一處無條件宣稱全文在 Log。
    ⛔ 註解與 docstring 裡「解釋這個前提已被推翻」的敘述不算違規——
    判準是**是否作為指引輸出給使用者**。
    """
    import inspect

    from wf_cli.commands import amend_cmd

    src = inspect.getsource(amend_cmd)
    banned = ["原值寫入 Log", "唯一還原點，摘要不能取代全文"]
    hits = [b for b in banned if b in src]
    assert not hits, f"仍有過期的還原指引：{hits}"
    # ⭐ 負控：確認掃描抓得到東西——這兩句必須存在，否則本測試是零資訊。
    assert "見平台前一版" in src and "原值已完整寫入 Log" in src
