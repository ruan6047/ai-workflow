"""釘住 R1 四項 blocking finding 的修補（`WF-REDESIGN-W3` 查核輪 1）。

查核者 `gpt-5.6-sol@Codex/OpenAI`（跨家族）逐字開的四條，各自的 disposition 都點名了
**要補哪一種測試**。本檔逐條對應，⛔ 不合併、⛔ 不用「相近的既有測試」抵充。

| finding | disposition 逐字點名的測試 | 本檔的節 |
|---|---|---|
| `R1-002` | 「至少新增 assign 長分支值的**零呼叫負控**」 | (1) |
| `R1-003` | 「補**缺報告／錯格數**時零寫入測試」 | (2) |
| `R1-004` | 「補**每階段交叉負控**」 | (3) |
| `R1-005` | 「補『**未登記環境只在 other**』fixture」 | (4) |

⚠️ **每一條都先重現查核者的觀察，再斷言它被修掉。** ⛔ 不直接寫「現在會擋」——
那讀不出修補前後的差別，而「差別」正是這四條 finding 的內容。
"""

from __future__ import annotations

import pytest

from wf_cli import pitfalls
from wf_cli.project import (
    FieldMeta,
    ProjectError,
    TEXT_FIELD_BYTE_LIMIT,
    oversized_text_fields,
    set_field_value,
)

from .test_pitfalls import _world  # noqa: F401
from .test_commands_mocked import (  # noqa: F401  （fixture 需在模組層取名）
    ASSIGN_REPO,
    BASE_TARGET,
    _assign_argv,
    _open_argv,
    fake_runner,
    run_cli,
)


def _long(nbytes: int = TEXT_FIELD_BYTE_LIMIT + 1) -> str:
    return "a" * nbytes


# =================================================== (1) R1-002：零呼叫負控

def test_r1_002_reproduce_set_field_value_used_to_send_an_oversize_value():
    """⭐ 先重現查核者的觀察：**修補前** `set_field_value` 對 1025-byte TEXT 直接送出。

    修補後它丟 `ProjectError`。⚠️ **這一道是網⛔ 不是閘門**——它排在寫入序列**之中**，
    響的時候同一輪先前的欄位可能已經寫出去了。真正的閘門是各動詞的整批預檢（下一條）。
    """
    calls: list[list[str]] = []

    class _Recorder:
        def execute(self, args, input=None):
            calls.append(list(args))

    field = FieldMeta(id="F", name="簡介", type="TEXT", options={})
    project = type("P", (), {"id": "PVT"})()

    with pytest.raises(ProjectError) as exc:
        set_field_value(_Recorder(), project, "ITEM", field, _long())
    assert "1025 bytes" in str(exc.value)
    assert "⛔ 不保證零寫入" in str(exc.value), "訊息必須自陳它不是閘門"
    assert calls == [], "最後防線響的時候⛔ 不得已經把這一格送出去"

    # 正控：恰好 1024 bytes 照樣送得出去 ⇒ 這一道是**依長度**動作、⛔ 不是恆擋。
    set_field_value(_Recorder(), project, "ITEM", field, "a" * TEXT_FIELD_BYTE_LIMIT)
    assert len(calls) == 1


def test_r1_002_assign_rejects_a_long_worktree_with_zero_remote_writes(fake_runner, capsys):
    """⭐ disposition 逐字點名的那一條：**assign 長分支值的負控**。

    查核者的證據逐字「`assign_cmd.py:434` 會先寫 owner，再寫可能超標的分支欄，
    仍可半寫」⇒ 本條斷言的是**世界狀態逐位元不變**，⛔ 不只是 rc≠0。

    ⚠️ **名字刻意⛔ 不叫「零呼叫」**（disposition 的字面是「零呼叫負控」）：`assign`
    構造上必須先**讀**看板才判得動資源交集 ⇒ 零呼叫對它不可能成立，寫成那樣會是
    一個名實不符的斷言。零**寫入**是更強的判準——它連「寫進去又改回來」都擋得住。
    這一處與 disposition 字面的差異已寫進交付報告，⛔ 不當成已照辦。
    """
    assert run_cli(_open_argv("R1-002-CARD1")) == 0
    before = _world(fake_runner)
    capsys.readouterr()

    rc = run_cli(_assign_argv("R1-002-CARD1", "ruan6047", "ai/x", _long()))

    assert rc == 2
    # ⚠️ **斷言的是零遠端「寫入」，⛔ 不是零呼叫。** disposition 逐字寫「零呼叫」，
    # 但 `assign` 構造上必須先**讀**看板才判得動資源交集 ⇒ 零呼叫對它不可能成立。
    # 世界快照逐位元不變是更強的判準：它連「寫進去又改回來」都擋得住。
    assert _world(fake_runner) == before, "超標拒收路徑⛔ 不得有任何遠端寫入"
    err = capsys.readouterr().err
    assert "[assign] 拒絕（零遠端寫入）" in err
    assert "分支worktree" in err


def test_r1_002_the_precheck_covers_the_whole_batch_not_one_field_at_a_time():
    """disposition 逐字「預檢**整批**待寫 TEXT」——⛔ 不是逐欄檢查後逐欄寫。

    ⭐ 反證：兩欄同時超標時，一次就要把**兩欄都**報出來。若實作是逐欄檢查逐欄寫，
    第一欄就會先被寫出去，第二欄永遠等不到報告。
    """
    found = oversized_text_fields(
        {"owner": _long(), "分支worktree": _long(1200), "交付狀態": "🔨執行中"}
    )
    assert sorted(f.name for f in found) == ["owner", "分支worktree"]


@pytest.mark.parametrize("verb", ["assign", "handoff", "review"])
def test_r1_002_every_writer_prechecks_before_any_remote_write(verb):
    """三個修補前沒有預檢的 writer，現在各自都在第一次遠端寫入之前呼叫預檢。

    ⛔ 這條⛔ 不是文件測試：它讀的是**碼**——`oversized_text_fields` 這個名字必須
    出現在該模組裡。`open`／`amend` 於 AC7 已有，⛔ 不在本條射程。
    """
    import importlib
    from pathlib import Path

    module = importlib.import_module(f"wf_cli.commands.{verb}_cmd")
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "oversized_text_fields(" in source, f"{verb} 沒有整批預檢"
    assert "render_oversize_rejection(" in source


# =============================================== (2) R1-003：PM 派審詞 validator

def test_r1_003_reproduce_assign_used_to_have_no_validator(fake_runner, capsys):
    """⭐ 先重現：查核者證據逐字「本次 PM 派審正是經 assign 完成，**未經 validator**」。

    修補後缺報告即 rc=2 且**零寫入**。
    """
    assert run_cli(_open_argv("R1-003-CARD1")) == 0
    before = _world(fake_runner)
    capsys.readouterr()

    argv = [
        "assign", *BASE_TARGET, "--repo", ASSIGN_REPO, "R1-003-CARD1",
        "--assignee", "ruan6047", "--branch", "ai/x", "--worktree", "/tmp/w",
        "--actual-capability", "主力型",
    ]
    assert run_cli(argv) == 2  # ⛔ 刻意**不**過 with_pm_note_report

    assert _world(fake_runner) == before, "缺報告的拒收必須零寫入"
    err = capsys.readouterr().err
    assert "[assign] 拒絕：離開「需求」階段須附注意事項回應清冊" in err
    assert "判內容的是檢閱那一環" in err


def test_r1_003_a_wrong_cell_count_is_rejected_with_zero_writes(fake_runner, capsys):
    """disposition 逐字的另一半：**錯格數**時零寫入。"""
    assert run_cli(_open_argv("R1-003-CARD2")) == 0
    before = _world(fake_runner)
    capsys.readouterr()

    short = "\n".join(pitfalls.note_report_template("需求").splitlines()[:-1])
    argv = [
        "assign", *BASE_TARGET, "--repo", ASSIGN_REPO, "R1-003-CARD2",
        "--assignee", "ruan6047", "--branch", "ai/x", "--worktree", "/tmp/w",
        "--actual-capability", "主力型", "--note-report", short,
    ]
    assert run_cli(argv) == 2

    assert _world(fake_runner) == before, "錯格數的拒收必須零寫入"
    assert "缺 1 條未回應" in capsys.readouterr().err


def test_r1_003_assign_and_handoff_share_one_validator():
    """「走**同一個** validator」——⛔ 不是兩份判準相近的實作。

    ⭐ 反證：`assign_cmd` 必須呼叫 `pitfalls.parse_note_report`，且⛔ 不得自帶
    另一個解析器（碼裡⛔ 不出現第二個 `def parse_note`）。
    """
    from pathlib import Path

    from wf_cli.commands import assign_cmd, handoff_cmd

    for module in (assign_cmd, handoff_cmd):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "parse_note_report(" in source
        assert "def parse_note" not in source, f"{module.__name__} 自帶了第二個解析器"


def test_r1_003_the_closeout_report_path_also_passes_the_validator():
    """結案報告走 `handoff --next-stage release`，而 `_note_gate` 在 `run()` 裡
    **無條件**執行（⛔ 不看 `next_stage`）⇒ 該路徑同樣過同一個 validator。

    ⛔ 這條⛔ 不是文件測試：它斷言閘門的呼叫**不在任何 `next_stage` 分支之內**。
    """
    import ast
    from pathlib import Path

    from wf_cli.commands import handoff_cmd

    tree = ast.parse(Path(handoff_cmd.__file__).read_text(encoding="utf-8"))
    run = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "run"
    )
    calls = [
        node for node in run.body  # ⭐ 只看 `run` 的**頂層** statement
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "_note_gate"
    ]
    assert calls, "`_note_gate` ⛔ 不在 run() 的頂層 ⇒ 它落在某個分支裡了"


# ============================================= (3) R1-004：每階段交叉負控

_STAGE_PAIRS = [
    (phase, other)
    for phase in pitfalls.PHASES
    for other in pitfalls.PHASES
    if phase != other
]


@pytest.mark.parametrize("phase,wrong_phase", _STAGE_PAIRS)
def test_r1_004_a_wrong_phase_prefix_is_fail_closed(tmp_path, phase, wrong_phase):
    """⭐ **每階段交叉負控**（disposition 逐字）：七個階段兩兩交叉共 42 格。

    查核者實測逐字：`project_roster_for("規劃", …P-審核-01…)` **rc=0，回
    `('P-審核-01',)`** ⇒ 規劃階段的 reader 接受了審核階段的 ID。
    修補後**任何**階段對**任何**別的階段都 fail-closed。
    """
    stem = pitfalls.STAGE_RULE_FILES[phase]
    (tmp_path / "stage-rules").mkdir(parents=True, exist_ok=True)
    (tmp_path / "stage-rules" / f"{stem}.md").write_text(
        f"## 5 注意事項\n\n- **P-{wrong_phase}-01** 錯階段\n", encoding="utf-8"
    )
    with pytest.raises(pitfalls.ProjectNoteRosterError) as exc:
        pitfalls.project_roster_for(phase, tmp_path)
    assert "階段前綴不符" in str(exc.value)
    assert f"P-{wrong_phase}-01" in str(exc.value), "訊息要指名是哪一條"


@pytest.mark.parametrize("phase", pitfalls.PHASES)
def test_r1_004_the_matching_phase_is_still_accepted(tmp_path, phase):
    """正控。⛔ 沒有這一條，上面 42 格全綠也可能只是「恆炸」。"""
    stem = pitfalls.STAGE_RULE_FILES[phase]
    (tmp_path / "stage-rules").mkdir(parents=True, exist_ok=True)
    (tmp_path / "stage-rules" / f"{stem}.md").write_text(
        f"## 5 注意事項\n\n- **P-{phase}-01** 對的階段\n", encoding="utf-8"
    )
    assert pitfalls.project_roster_for(phase, tmp_path) == (f"P-{phase}-01",)


def test_r1_004_wrong_phase_is_not_silently_dropped(tmp_path):
    """⛔ **不是靜默丟棄**——那會讓「寫錯階段」與「這個階段沒有條目」長得一模一樣。

    ⭐ 反證：檔裡同時有對的與錯的，正確的處置仍是**拒收整份**，⛔ 不是回傳對的那一條。
    """
    (tmp_path / "stage-rules").mkdir(parents=True, exist_ok=True)
    (tmp_path / "stage-rules" / "planning.md").write_text(
        "## 5 注意事項\n\n- **P-規劃-01** 對的\n- **P-審核-02** 錯的\n", encoding="utf-8"
    )
    with pytest.raises(pitfalls.ProjectNoteRosterError):
        pitfalls.project_roster_for("規劃", tmp_path)


# ======================================== (4) R1-005：未登記環境只在 other

def test_r1_005_an_unregistered_environment_only_on_the_other_side_is_warned(
    fake_runner, capsys
):
    """⭐ disposition 逐字點名的 fixture：**未登記環境只在 other**。

    查核者的證據逐字「只對 `mine.resources` 呼叫 `unregistered_db_environments`；
    其他活卡的 `other_decl.resources` 沒有同一檢查」。

    ⚠️ **這一半才是危險的那一半**：本卡自己拼對、別卡拼錯 ⇒ 兩者被按字面判為
    **不相交**而雙雙放行。
    """
    assert run_cli(
        _open_argv("R1-005-OTHER1", **{"--db-scope": "write", "--resources": "db:zzz:schema"})
    ) == 0
    assert run_cli(_assign_argv("R1-005-OTHER1", "ruan6047", "ai/o", "/tmp/o")) == 0

    assert run_cli(
        _open_argv("R1-005-MINE1", **{"--db-scope": "write", "--resources": "db:production:schema"})
    ) == 0
    capsys.readouterr()
    assert run_cli(_assign_argv("R1-005-MINE1", "ruan6047", "ai/m", "/tmp/m")) == 0

    err = capsys.readouterr().err
    assert "db:zzz:schema" in err, "別卡側的未登記環境沒有被警示"
    assert "本卡與所有候選活卡兩側" in err


def test_r1_005_the_warning_is_deduplicated(fake_runner, capsys):
    """「**去重後**輸出 stderr」（disposition 逐字）：同一個未登記環境⛔ 不得印兩次。"""
    # ⭐ **兩張別卡宣告同一個未登記環境**（但各自不同的 table ⇒ ⛔ 不會互撞），
    # 然後跑**一次** assign ⇒ 該環境只能被印一次。
    for i in (1, 2):
        assert run_cli(
            _open_argv(
                f"R1-005-DUP{i}",
                **{"--db-scope": "write", "--resources": f"db:zzz:table:t{i}"},
            )
        ) == 0
        assert run_cli(_assign_argv(f"R1-005-DUP{i}", "ruan6047", f"ai/d{i}", f"/tmp/d{i}")) == 0

    assert run_cli(
        _open_argv("R1-005-DUP3", **{"--db-scope": "write", "--resources": "db:staging:schema"})
    ) == 0
    capsys.readouterr()
    assert run_cli(_assign_argv("R1-005-DUP3", "ruan6047", "ai/d3", "/tmp/d3")) == 0

    err = capsys.readouterr().err
    tokens = [line for line in err.splitlines() if "未登記" in line and "警告" in line]
    assert len(tokens) == 1, f"⛔ 只能印一行警告，實得 {len(tokens)}"
    assert tokens[0].count("db:zzz:table:t1") == 1
    assert tokens[0].count("db:zzz:table:t2") == 1
