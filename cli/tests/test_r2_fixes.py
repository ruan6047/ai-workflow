"""釘住 R2 兩項歸執行者的 finding，以及第三輪 artifact 修補（`WF-REDESIGN-W3`）。

## R2-001 —— 專案層清冊在真實入口上構造性不可達

`assign_cmd` 讀 `getattr(args, "repo_path", None)`，而 `assign` 的 parser **⛔ 沒有
`--repo-path`** ⇒ 真實 CLI 上那個 `getattr` **恆為 `None`**，專案層 `P-<階段>-NN`
**永遠是空集合**，與 `--note-report` 的 help 承諾不一致。查核者複驗
`grep -c '"--repo-path"' assign_cmd.py` ＝ **0**。

⚠️ **本檔第一組測試刻意走真實 parser**（`build_parser().parse_args`），⛔ 不直接
呼叫 `_pm_note_gate`：直接呼叫的測試對這個缺陷**完全瞎**——它可以自己在
`Namespace` 上塞一個 `repo_path`，於是永遠是綠的。缺陷住在「parser 有沒有這個
旗標」，⇒ 只有經過 parser 的測試量得到。

## R2-002 —— 重跑指令遺失裁決輸入

`review` 的 `--reviewer` 為空拒絕所給的重跑指令**只有 reviewer 與 source SHA**，
⛔ 無 `--input`、⛔ 未保留 stdin ⇒ 查核者逐字執行得 `rc=2`「查核輸出是空的」。

## ⛔ 一個⛔ 不得由本檔綠燈推出的東西

本檔證明的是**訊息裡給得出可跑的東西、且原報告來源沒有遺失**。它⛔ 不證明
「這 6 則訊息在驗收 3 的三條判準下計數」——`--reviewer`／`--rationale`／`--reason`
這類值**在構造上就是人要填的**，⛔ 沒有任何機械能代它決定。⇒ 那幾則訊息的
「重跑形狀」刻意寫成**散文**、⛔ 不寫成可整行複製的指令行；判準 (iii) 的既有全域
複查（`test_rejection_inventory.test_the_remedy_commands_contain_no_placeholder_at_all`）
因此仍然全綠，⛔ 不是被放寬。
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

from wf_cli import pitfalls
from wf_cli.cli import build_parser
from wf_cli.commands import assign_cmd, review_cmd

# `F-執行-06` 逐字「驗證器要 import ⛔ 不重打」：開卡與世界快照的配件全部沿用
# `test_pitfalls` 那一份，⛔ 不在此另建一套 fixture。
from .test_pitfalls import (  # noqa: F401  （fixture 需在模組層取名，pytest 才看得到）
    _TARGET,
    _open,
    _run,
    _world,
    runner,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]

#: 測試要跑的是**使用者真的會貼進 shell 的那一行**⇒ 用 venv 裡的 console script，
#: ⛔ 不是 `python -m wf_cli`（那個入口今天不存在，用它會量到一個假的 rc）。
_WFCLI = Path(sys.executable).parent / "wfcli"

_spec = importlib.util.spec_from_file_location(
    "rejection_inventory", _REPO_ROOT / "scripts" / "rejection_inventory.py"
)
assert _spec is not None and _spec.loader is not None
ri = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("rejection_inventory", ri)
_spec.loader.exec_module(ri)


def _assign(card_id: str, **overrides) -> int:
    defaults = {
        "--assignee": "ruan",
        "--branch": "ai/x/CARD1",
        "--worktree": "/tmp/wt",
        "--actual-capability": "主力型",
    }
    defaults.update(overrides)
    argv = ["assign", *_TARGET, card_id]
    for key, value in defaults.items():
        if value is None:
            continue
        argv += [key, value]
    return _run(argv)


def _deploy_card(runner, card_id: str) -> None:
    """把卡推到**框架層 0 條**的階段，⇒ 清冊裡只剩專案層那幾條。

    ⭐ 這正是 R2-001 disposition 逐字要求的形狀：「證明**只有專案層** `P-<階段>-NN`
    時也會在任何寫入前要求回應」。`部署` 與 `維護` 的框架層是**結構性 0**
    （兩份 stage-rules 的 §5 各有 0 條 `F-`）⇒ 拿它當載體。
    """
    assert _open(card_id) == 0
    raw = next(iter(runner.items.values()))
    raw["fields"]["階段"] = "部署"


def _project_root(tmp_path: Path, body: str, stage: str = "deploy") -> Path:
    (tmp_path / "stage-rules").mkdir(parents=True, exist_ok=True)
    (tmp_path / "stage-rules" / f"{stage}.md").write_text(body, encoding="utf-8")
    return tmp_path


_ONE_PROJECT_NOTE = "## 5 注意事項\n\n- **P-部署-01** 本專案的加嚴條文\n"


# ============================================ (1) R2-001：旗標真的存在

def test_the_assign_parser_actually_declares_repo_path():
    """⭐ 承重：缺陷的**本體**就是這個旗標不存在。

    ⛔ 不用 `hasattr(args, "repo_path")` 當斷言——`argparse` 對**沒宣告**的旗標
    根本不建屬性，而 `getattr(..., None)` 會把那件事吞掉。⇒ 直接對 parser 的
    option strings 斷言。
    """
    assign = build_parser()._subparsers._group_actions[0].choices["assign"]
    flags = {opt for action in assign._actions for opt in action.option_strings}
    assert "--repo-path" in flags


def test_a_parsed_assign_namespace_carries_repo_path():
    """經過**真實 parser** 之後 `args.repo_path` 拿得到值（⛔ 不再恆為 None）。"""
    args = build_parser().parse_args(
        ["assign", *_TARGET, "C1", "--assignee", "a", "--branch", "b",
         "--worktree", "/tmp/w", "--actual-capability", "主力型",
         "--repo-path", "/tmp"]
    )
    assert args.repo_path == "/tmp"


# =============================== (2) R2-001：只有專案層時也擋，且零寫入

def test_a_project_only_roster_still_demands_a_response_before_any_write(
    runner, tmp_path, capsys
):
    """⭐ **本檔的承重測試**（R2-001 disposition 逐字）。

    框架層 0 條 ＋ 專案層 1 條 ⇒ 清冊非空 ⇒ 必須要求回應，且**世界狀態逐位元不變**。
    修補前這條路上 `roster` 恆為 `()` ⇒ 會走「清冊為空 ⇒ 本次未要求回應」那條豁免，
    一路放行到寫入。
    """
    _deploy_card(runner, "R2-PROJ1")
    root = _project_root(tmp_path, _ONE_PROJECT_NOTE)
    before = _world(runner)
    capsys.readouterr()

    assert _assign("R2-PROJ1", **{"--repo-path": str(root)}) == 2

    assert _world(runner) == before, "拒收必須零寫入"
    err = capsys.readouterr().err
    assert "P-部署-01" in err, err
    assert "專案層 1 條" in err, err


def test_the_same_card_without_repo_path_is_waved_through_and_says_so(runner, capsys):
    """⛔ 豁免不得是靜默的：未給 `--repo-path` ⇒ 專案層視為空集合，**且明說**。

    ⚠️ 這一條同時是 R2-001 的**反面對照**：同一張卡、同一份專案層條文，只差有沒有
    把根目錄送進來，結果就從「擋下」變成「放行」。⇒ 那個旗標⛔ 不是裝飾。
    """
    _deploy_card(runner, "R2-PROJ2")
    capsys.readouterr()

    assert _assign("R2-PROJ2") == 0

    err = capsys.readouterr().err
    assert "未給 --repo-path" in err
    assert "專案層注意事項視為空集合" in err
    assert "⛔ 不代表該專案沒有加嚴條文" in err


def test_the_project_only_roster_is_satisfied_by_the_project_entry(runner, tmp_path):
    """給對清冊 ⇒ 放行。⇒ 上一條的 rc=2 是**清冊被讀到了**，⛔ 不是壞掉。"""
    _deploy_card(runner, "R2-PROJ3")
    root = _project_root(tmp_path, _ONE_PROJECT_NOTE)
    report = pitfalls.note_report_template("部署", root)
    assert report == "P-部署-01：已遵循"

    assert _assign("R2-PROJ3", **{"--repo-path": str(root), "--note-report": report}) == 0


def test_a_framework_layer_answer_does_not_satisfy_the_project_layer(runner, tmp_path):
    """⛔ 不得拿別階段的框架層編號頂掉專案層那一條——判準是**逐格序列相等**。"""
    _deploy_card(runner, "R2-PROJ4")
    root = _project_root(tmp_path, _ONE_PROJECT_NOTE)
    assert _assign(
        "R2-PROJ4", **{"--repo-path": str(root), "--note-report": "F-執行-01：已遵循"}
    ) == 2


# ==================================== (3) R2-001：輸入本身要被驗證

def test_a_repo_path_that_is_not_a_directory_is_refused_with_zero_writes(
    runner, tmp_path, capsys
):
    """disposition 逐字要求「**經驗證的**本機專案根目錄輸入」。

    ⚠️ ⛔ 不驗它是不是 git repo：`project_roster_for` 讀的是單一具名檔，非 git 的
    目錄照樣可以合法擺著它。此上界寫在 `_pm_note_gate` 的註解裡。
    """
    _deploy_card(runner, "R2-PROJ5")
    missing = tmp_path / "does-not-exist"
    before = _world(runner)
    capsys.readouterr()

    assert _assign("R2-PROJ5", **{"--repo-path": str(missing)}) == 2

    assert _world(runner) == before, "拒收必須零寫入"
    err = capsys.readouterr().err
    assert "不是一個存在的目錄" in err
    assert "git rev-parse --show-toplevel" in err


def test_that_refusal_carries_a_runnable_remedy(runner, tmp_path, capsys):
    """新造的擋人點也要**自己付得起補救**（驗收 3 的紀律，⛔ 不豁免新碼）。"""
    _deploy_card(runner, "R2-PROJ6")
    capsys.readouterr()
    _assign("R2-PROJ6", **{"--repo-path": str(tmp_path / "nope")})
    command = _remedy_lines(capsys.readouterr().err)
    assert command, "訊息裡沒有可整行複製的指令"
    assert ri._evaluate(command[0]).passes
    assert subprocess.run(command[0], shell=True, cwd=_REPO_ROOT,
                          capture_output=True).returncode == 0


def _remedy_lines(text: str) -> list[str]:
    """從 stderr 撈出**可整行複製**的指令行，判準與 artifact 產生器同一支。"""
    return ri._command_lines(text)


# ============================== (4) R2-002：重跑指令帶得走原報告來源

def _review_reject(tmp_path, monkeypatch, capsys, *, input_arg, stdin_text=None):
    argv = ["review", *_TARGET, "W3", "--reviewer", "  ",
            "--source-sha", "a" * 40]
    if input_arg is not None:
        argv += ["--input", input_arg]
    if stdin_text is None:
        monkeypatch.setattr(review_cmd.sys.stdin, "isatty", lambda: True, raising=False)
    else:
        import io

        stream = io.StringIO(stdin_text)
        stream.isatty = lambda: False  # type: ignore[method-assign]
        monkeypatch.setattr(review_cmd.sys, "stdin", stream)
    capsys.readouterr()
    rc = _run(argv)
    return rc, capsys.readouterr().err


def test_the_retry_names_the_input_path_you_actually_gave(tmp_path, monkeypatch, capsys):
    report = tmp_path / "verdict.md"
    report.write_text("報告內容", encoding="utf-8")
    rc, err = _review_reject(tmp_path, monkeypatch, capsys, input_arg=str(report))
    assert rc == 2
    assert f"--input ＝ {report}" in err, err


def test_a_stdin_report_is_spilled_to_a_file_so_the_retry_can_use_it(
    tmp_path, monkeypatch, capsys
):
    """⭐ **stdin ⛔ 讀不回來**——重跑時那份輸入已經沒了。

    ⇒ 就地落到暫存檔並在訊息裡指名。⚠️ 這是拒絕路徑上唯一的副作用，只寫本機暫存
    目錄、⛔ 不碰任何遠端狀態，且⛔ 不靜默。
    """
    payload = "## 結構化區塊\n\nreview_result: APPROVE\n"
    rc, err = _review_reject(tmp_path, monkeypatch, capsys, input_arg=None,
                             stdin_text=payload)
    assert rc == 2
    match = re.search(r"已原樣存到 (\S+\.md)", err)
    assert match, err
    spilled = Path(match.group(1))
    assert spilled.read_text(encoding="utf-8") == payload
    assert f"--input ＝ {spilled}" in err, err


def test_a_tty_with_no_report_says_so_instead_of_inventing_a_path(
    tmp_path, monkeypatch, capsys
):
    """⛔ 不假造路徑：本次根本沒有報告輸入時，明說那件事。"""
    rc, err = _review_reject(tmp_path, monkeypatch, capsys, input_arg=None)
    assert rc == 2
    assert "⛔ 無查核報告輸入（stdin 是終端機）" in err


def test_the_preserved_path_actually_works_end_to_end(tmp_path, monkeypatch, capsys):
    """⭐ **端到端**：從拒絕訊息擷取到的 `--input` 路徑，補上 reviewer 後真的跑得起來。

    ⚠️ 這一條量的是 R2-002 的**核心**：查核者逐字執行舊訊息給的重跑指令得 `rc=2`
    「查核輸出是空的」，成因就是 `--input` 遺失。⇒ 這裡把訊息裡指名的路徑餵回
    `wfcli review --validate-only`，證明它**不再是空的**。
    """
    from .test_review import APPROVE_REPORT

    rc, err = _review_reject(tmp_path, monkeypatch, capsys, input_arg=None,
                             stdin_text=APPROVE_REPORT)
    assert rc == 2
    spilled = re.search(r"已原樣存到 (\S+\.md)", err).group(1)

    done = subprocess.run(
        [str(_WFCLI), "review", *_TARGET, "W3",
         "--reviewer", "gpt-5.6-sol@Codex/OpenAI", "--source-sha", "a" * 40,
         "--input", spilled, "--validate-only"],
        capture_output=True, text=True, cwd=_REPO_ROOT,
    )
    combined = done.stdout + done.stderr
    # ⭐ 承重：**rc=0**。舊訊息給的重跑指令在這裡是 rc=2「查核輸出是空的」。
    assert done.returncode == 0, combined
    assert "查核輸出是空的" not in combined, combined


def test_the_review_refusal_still_offers_a_runnable_command(tmp_path, monkeypatch, capsys):
    """訊息⛔ 不得只剩散文——`--help` 那一行必須仍是可整行複製、且實跑 rc=0。"""
    rc, err = _review_reject(tmp_path, monkeypatch, capsys, input_arg=None)
    assert rc == 2
    lines = _remedy_lines(err)
    assert lines and lines[0] == "wfcli review --help"
    assert ri._evaluate(lines[0]).passes


# ================================= (5) 第七個 artifact 缺陷：字面被黏住

def test_render_text_does_not_glue_separate_list_elements():
    """⭐ **第七個 artifact 缺陷**（R2 這一輪量到的）。

    舊版 `ast.walk` ＋ `"".join` 會把清單的相鄰元素黏成一行 ⇒ 產出一條**實際不存在**
    的「指令行」。實測 `pitfalls.py:391` 因此被黏出
    `git show HEAD:AI_WORKFLOW.md  - 階段判定依據：…<原因>…`，誤觸判準 (iii)。
    """
    import ast

    tree = ast.parse('x = ["a\\n    git show HEAD:f.md", "  - 值三選一：<原因>"]')
    rendered = ri._render_text(tree.body[0])
    command_lines = ri._command_lines(rendered)
    assert command_lines == ["git show HEAD:f.md"], rendered
    assert "<原因>" not in command_lines[0]


def test_render_text_separates_call_arguments_with_a_space():
    """`print(a, b)` 的實際輸出是 ``a`` 空白 ``b`` ⇒ ⛔ 不得黏成一個 token。"""
    import ast

    tree = ast.parse('print("wfcli x --help", "尾巴")')
    assert ri._render_text(tree.body[0]) == "wfcli x --help 尾巴 "


def test_criterion_three_scans_every_command_line_not_just_the_first():
    """⭐ 判準 (iii) 掃**每一條**指令行。

    ⛔ 不得只看 `lines[0]`：那會讓「第一行乾淨、第二行要人填」的訊息被判成合格——
    那是 `R2-003` 那個誤判的**鏡像**。
    """
    text = "wfcli a --help\nwfcli b --reason <你要填的>"
    verdict = ri._evaluate(text)
    assert verdict.command == "wfcli a --help"
    assert verdict.placeholder_lines == ["wfcli b --reason <你要填的>"]
    assert verdict.no_placeholder is False
    assert verdict.passes is False


def test_the_cjk_candidate_list_is_recorded_but_never_changes_the_verdict():
    """⚠️ CJK 候選是**清單⛔ 不是判準**——它會誤中**真的值**。

    `wfcli amend … --reason '修復資源宣告區塊的排版'` 是一句寫好的理由，⛔ 不是佔位。
    ⇒ 它進 `cjk_value_lines`、**⛔ 不進** `passes`。
    """
    verdict = ri._evaluate("wfcli amend C1 --reason '修復資源宣告區塊的排版'")
    assert verdict.cjk_value_lines == ["wfcli amend C1 --reason '修復資源宣告區塊的排版'"]
    assert verdict.no_placeholder is True
    assert verdict.passes is True


def test_an_fstring_field_is_not_a_placeholder():
    """⚠️ `{…}` 執行時會被代入真值 ⇒ ⛔ 非佔位。PM 上一輪把兩者混為一談才漏掉一列。"""
    verdict = ri._evaluate("wfcli amend {…} --reason {…}")
    assert verdict.no_placeholder is True
    assert verdict.cjk_value_lines == []


# ============================ (6) 六則曾含人工佔位的訊息，現況逐則釘住

_FORMERLY_PLACEHOLDER = {
    ("assign_cmd.py", "wfcli amend --help"),
    ("assign_cmd.py", "gh issue view"),
    ("checkpoint_cmd.py", "wfcli checkpoint --help"),
    ("checkpoint_cmd.py", "wfcli contract-baseline --help"),
    ("open_cmd.py", "wfcli amend --help"),
    ("review_cmd.py", "wfcli review --help"),
}


def test_no_command_line_in_the_corpus_carries_a_human_fill_slot():
    """全語料複查：**⛔ 沒有任何指令行**含 `<…>`。

    ⭐ 這一條是「把填空寫進指令行」那個作法的**反面**：本輪 6 則的重跑形狀刻意寫成
    散文，於是這裡維持 0。⛔ 不得為了讓那 6 則「計數」而把填空塞回指令行——
    `intake.py` 逐字禁止 `<在此填寫>` 這種**指令**佔位。
    """
    offenders = [
        (r.file, r.line, r.mechanical.placeholder_lines)
        for r in ri.scan(_REPO_ROOT / "cli" / "src")
        if r.in_scope and r.kind == "message" and r.mechanical.placeholder_lines
    ]
    assert offenders == [], offenders


def test_every_formerly_placeholder_message_now_leads_with_a_clean_command():
    """六則各自的第一條指令行現在都乾淨且**實跑 rc=0**。

    ⚠️ 第六則（`checkpoint_cmd.py:231` 的 `--rationale '改判理由寫在這裡'`）**⛔ 不在
    PM 點名的 5 則裡**——它是本輪窮舉時量出來的，PM 的 59 列對帳把它記成 ✅ 合格。
    """
    heads = {
        (r.file.split("/")[-1], (r.mechanical.command or "").split(" --")[0].strip())
        for r in ri.scan(_REPO_ROOT / "cli" / "src")
        if r.in_scope and r.kind == "message" and r.mechanical.command
    }
    for expected in _FORMERLY_PLACEHOLDER:
        assert any(f == expected[0] and c.startswith(expected[1].split(" --")[0])
                   for f, c in heads), (expected, sorted(heads))


@pytest.mark.parametrize(
    "command",
    ["wfcli amend --help", "wfcli review --help", "wfcli checkpoint --help",
     "wfcli contract-baseline --help", "wfcli assign --help"],
)
def test_each_help_remedy_actually_exits_zero(command):
    """判準 (i)「可直接執行」的**實跑**檢驗，⛔ 不是眼看。"""
    done = subprocess.run(
        [str(_WFCLI), *command.split()[1:]],
        capture_output=True, text=True, cwd=_REPO_ROOT,
    )
    assert done.returncode == 0, done.stderr
