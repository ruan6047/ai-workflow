"""釘住注意事項回應清冊與結案閘門（`WF-REDESIGN-W3` 驗收 6 與 8）。

## 兩份清冊⛔ 不得互相代用——這是本檔最重要的一條

`templates/delivery-report.md` 逐字「⛔ 不得互相代用」。兩者的**值域第一格不同**：

    踩坑族清冊     → `已檢查`／`不適用：<原因>`／`發現：<處置>`
    注意事項回應   → `已遵循`／`不適用：<原因>`／`發現：<處置>`
                      ~~~~~~

後兩格字面相同（故共用常數），第一格**刻意不同**。混用會讓兩份報告在事後統計上
無法分辨，⇒ 本檔對「拿 `已檢查` 回答注意事項」有專門的拒收測試。

## 判準是**逐格序列相等**，⛔ 非集合相等

`[A, A, B]` 對 `{A, B}` 在集合語意下**相等** ⇒ 重複一格就能頂掉另一格，格數不再由
清冊決定。⇒ 卡面逐字要求「重複 ID 本身即拒收」。

## ⛔ 兩件不得由本檔綠燈推出的事

1. **⛔ 不得推出「內容被驗過」。** CLI 只驗編號窮舉性、值域與非空——**判內容的是
   檢閱那一環（人或另一個 AI）**。
2. **⛔ 不得推出「結案已不可直接設定」。** 驗收 8 的閘門**射程逐字限
   `handoff_cmd.py`**；`assign_cmd.py` 的 `--status` 同為零驗證自由文字 ⇒
   `wfcli assign --status 🏁完成` 照樣繞得過。本檔最後一組測試把那個事實**釘成
   斷言**，免得有人把閘門讀成全面修復。
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

from wf_cli import pitfalls
from wf_cli.commands import assign_cmd, handoff_cmd

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STAGE_RULES = _REPO_ROOT / "stage-rules"


_F_LINE = re.compile(r"^[-*]\s+\*\*(?P<id>F-[^\s*-]+-\d+)\*\*")


# ============================================ (1) 框架層：雙向互含

def test_the_roster_keys_are_exactly_the_phases():
    """鍵集合以 `PHASES` 為**單一來源**。少一個鍵與「該階段沒有條目」長得一樣。"""
    assert tuple(pitfalls.NOTE_ROSTER) == pitfalls.PHASES
    assert tuple(pitfalls.STAGE_RULE_FILES) == pitfalls.PHASES


@pytest.mark.parametrize("phase", pitfalls.PHASES)
def test_the_roster_matches_the_stage_rules_file_in_both_directions(phase):
    """⭐ 碼側 dict × `stage-rules/<階段>.md` §5，**雙向**互含，漂移即紅。

    ⛔ 單向（只驗「碼裡的都在檔裡」）會漏掉「檔裡新增了一條而碼沒跟上」。
    """
    path = _STAGE_RULES / f"{pitfalls.STAGE_RULE_FILES[phase]}.md"
    in_file = tuple(
        m.group("id") for m in map(_F_LINE.match, path.read_text(encoding="utf-8").splitlines()) if m
    )
    assert pitfalls.NOTE_ROSTER[phase] == in_file


def test_the_total_is_fifty_eight_today():
    """裸值有量測日：**2026-09-02，58 條**（需求 15／研究 14／規劃 8／執行 12／審核 9）。

    ⚠️ 這是**移動標靶**——條文增刪就會變。它在這裡是為了讓「悄悄少掉一整個階段」
    在數字上看得見；真正的守衛是上面那條雙向互含。
    """
    counts = {phase: len(ids) for phase, ids in pitfalls.NOTE_ROSTER.items()}
    assert counts == {"需求": 15, "研究": 14, "規劃": 8, "執行": 12, "審核": 9, "部署": 0, "維護": 0}
    assert sum(counts.values()) == 58


def test_deploy_and_maintenance_are_structurally_zero_not_missing():
    """⚠️ **結構性 0**：兩份 stage-rules 的 §5 各有 0 條 `F-`，⛔ 不是遺漏。"""
    for phase in ("部署", "維護"):
        path = _STAGE_RULES / f"{pitfalls.STAGE_RULE_FILES[phase]}.md"
        assert not [m for m in map(_F_LINE.match, path.read_text(encoding="utf-8").splitlines()) if m]
        assert pitfalls.NOTE_ROSTER[phase] == ()
        assert phase in pitfalls.NOTE_ROSTER, "鍵必須在，⛔ 不得因為空而拿掉"


# ============================================ (2) 值域⛔ 不得互相代用

def test_the_first_verdict_differs_from_the_family_roster():
    assert pitfalls.NOTE_VERDICT_FOLLOWED == "已遵循"
    assert pitfalls.VERDICT_CHECKED == "已檢查"
    assert pitfalls.NOTE_VERDICT_FOLLOWED != pitfalls.VERDICT_CHECKED


def test_answering_a_note_with_the_family_verdict_is_rejected():
    """⭐ 直接的代用嘗試。訊息必須點名兩份清冊⛔ 不得互相代用。"""
    parsed = pitfalls.parse_note_report("F-規劃-01：已檢查", ("F-規劃-01",))
    assert not parsed.ok
    assert any("不得互相代用" in e for e in parsed.errors)


def test_the_template_uses_the_note_verdict():
    assert all(
        line.endswith(f"{pitfalls.FIELD_SEPARATOR}已遵循")
        for line in pitfalls.note_report_template("規劃").splitlines()
    )


# ============================================ (3) 六種拒收各有 fixture

def _full(phase="規劃", verdict="已遵循"):
    return "\n".join(
        f"{n}{pitfalls.FIELD_SEPARATOR}{verdict}" for n in pitfalls.note_roster_for(phase)
    )


def test_a_complete_report_passes():
    """正控。⛔ 沒有這一條，下面六條全紅也可能只是「恆拒」。"""
    parsed = pitfalls.parse_note_report(_full(), pitfalls.note_roster_for("規劃"))
    assert parsed.ok, parsed.errors
    assert len(parsed.rows) == 8


def test_reject_missing_id():
    text = "\n".join(_full().splitlines()[:-1])
    parsed = pitfalls.parse_note_report(text, pitfalls.note_roster_for("規劃"))
    assert any("缺 1 條未回應" in e for e in parsed.errors)


def test_reject_extra_id():
    text = _full() + "\nF-規劃-99：已遵循"
    parsed = pitfalls.parse_note_report(text, pitfalls.note_roster_for("規劃"))
    assert any("多一即拒" in e for e in parsed.errors)


def test_reject_duplicate_id():
    """⭐ **序列相等⛔ 非集合相等**：`[A, A, B]` 對 `{A, B}` 集合語意下相等，此處必拒。"""
    lines = _full().splitlines()
    text = "\n".join([lines[0], lines[0]] + lines[1:])
    parsed = pitfalls.parse_note_report(text, pitfalls.note_roster_for("規劃"))
    assert any("逐格序列相等" in e for e in parsed.errors)


def test_reject_out_of_domain_verdict():
    parsed = pitfalls.parse_note_report(
        _full().replace("F-規劃-01：已遵循", "F-規劃-01：大概吧"),
        pitfalls.note_roster_for("規劃"),
    )
    assert any("不在三個合法值域內" in e for e in parsed.errors)


def test_reject_not_applicable_without_a_reason():
    parsed = pitfalls.parse_note_report(
        _full().replace("F-規劃-01：已遵循", "F-規劃-01：不適用："),
        pitfalls.note_roster_for("規劃"),
    )
    assert any("冒號之後是空的" in e for e in parsed.errors)


def test_reject_found_without_a_disposition():
    parsed = pitfalls.parse_note_report(
        _full().replace("F-規劃-01：已遵循", "F-規劃-01：發現："),
        pitfalls.note_roster_for("規劃"),
    )
    assert any("冒號之後是空的" in e for e in parsed.errors)


def test_reject_wrong_order_even_when_every_id_is_present():
    """序列相等的最後一格：格數與內容都對，**順序**不同⇒ 仍拒。"""
    lines = _full().splitlines()
    parsed = pitfalls.parse_note_report(
        "\n".join(reversed(lines)), pitfalls.note_roster_for("規劃")
    )
    assert any("順序與清冊不同" in e for e in parsed.errors)


# ============================================ (4) 專案層 reader

def _project(tmp_path: Path, body: str, stage="planning") -> Path:
    (tmp_path / "stage-rules").mkdir(parents=True, exist_ok=True)
    (tmp_path / "stage-rules" / f"{stage}.md").write_text(body, encoding="utf-8")
    return tmp_path


def test_no_project_root_is_an_empty_set():
    assert pitfalls.project_roster_for("規劃", None) == ()


def test_a_missing_file_means_no_project_layer_notes_not_unfilled(tmp_path):
    """契約逐字：**⛔ 沒有該檔＝沒有專案層注意事項**（⛔ 非「未填」）。"""
    assert pitfalls.project_roster_for("規劃", tmp_path) == ()


def test_a_section_five_with_no_p_entries_is_also_zero(tmp_path):
    root = _project(tmp_path, "## 5 注意事項\n\n（本專案暫無加嚴條文）\n")
    assert pitfalls.project_roster_for("規劃", root) == ()


def test_p_entries_under_section_five_are_read_in_order(tmp_path):
    root = _project(
        tmp_path,
        "## 4 各角色\n\n- 略\n\n## 5 注意事項\n\n"
        "- **P-規劃-01** 本專案的第一條加嚴\n"
        "- **P-規劃-02** 第二條\n\n"
        "## 6 其他\n\n- **P-規劃-99** 這一條在 §5 之外，⛔ 不該被讀到\n",
    )
    assert pitfalls.project_roster_for("規劃", root) == ("P-規劃-01", "P-規劃-02")


def test_p_entries_without_a_section_five_are_loud_not_silently_zero(tmp_path):
    """⭐ 有資料但放錯地方 ⇒ **拒收**。

    靜默回 0 會讓專案以為自己的加嚴條文生效了，而實際上一條都沒被讀到——
    **那正是本卡在收的失敗形態**，⛔ 不得在這裡新造一個。
    """
    root = _project(tmp_path, "## 注意事項\n\n- **P-規劃-01** 放錯地方了\n")
    with pytest.raises(pitfalls.ProjectNoteRosterError) as exc:
        pitfalls.project_roster_for("規劃", root)
    assert "⛔ 沒有 `## 5` 標題" in str(exc.value)


def test_the_combined_roster_is_additive_with_the_framework_layer_first(tmp_path):
    """契約逐字：**累加⛔ 不覆寫**——框架層的 `F-` 一條都不會消失。"""
    root = _project(tmp_path, "## 5 注意事項\n\n- **P-規劃-01** 加嚴\n")
    combined = pitfalls.combined_note_roster("規劃", root)
    assert combined[: len(pitfalls.note_roster_for("規劃"))] == pitfalls.note_roster_for("規劃")
    assert combined[-1] == "P-規劃-01"
    assert len(combined) == 9


def test_the_reader_does_not_glob(tmp_path):
    """⛔ **不做動態探索**：只讀該階段對應的**單一具名檔**。"""
    root = _project(tmp_path, "## 5 注意事項\n\n- **P-執行-01** 別的階段\n", stage="implementation")
    assert pitfalls.project_roster_for("規劃", root) == ()
    assert pitfalls.project_roster_for("執行", root) == ("P-執行-01",)


# ============================================ (5) stage-rules 的落地

_REMOVED = ("requirement", "research", "planning", "implementation", "review")
_KEPT = ("deploy", "maintenance", "closeout", "defect-path")


@pytest.mark.parametrize("stem", _REMOVED)
def test_the_not_yet_effective_marker_is_gone_from_the_five(stem):
    """移除即啟用（決議 §三之二）。這五檔的 `F-` 條數皆 > 0 且階段在 `PHASES` 內。"""
    assert "未生效" not in (_STAGE_RULES / f"{stem}.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("stem", _KEPT)
def test_the_marker_stays_on_the_other_four(stem):
    """⛔ **不移除這四行**，各有理由：

    - `deploy`／`maintenance`：`F-` 條數 **0** ⇒ 啟用即零資訊。
    - `closeout`：`結案` **⛔ 不在** `pitfalls.PHASES` 七值內 ⇒ 沒有 writer。
    - `defect-path`：逐字轉指實際階段，本身不是一個階段。
    """
    assert "未生效" in (_STAGE_RULES / f"{stem}.md").read_text(encoding="utf-8")


def test_the_project_layer_contract_is_byte_identical_across_the_five_files():
    """⚠️ 契約在 5 個檔各一份 ⇒ **會漂**。本條把「不得漂」變成機械的。

    （`tier-rules.md` 在 repo 根、**⛔ 不在本卡 write-set**，故無法只放一份。）
    """
    def contract(stem: str, phase: str) -> str:
        text = (_STAGE_RULES / f"{stem}.md").read_text(encoding="utf-8")
        start = text.index("### 專案層注意事項的居所契約")
        return text[start:].replace(stem, "<FILE>").replace(phase, "<PHASE>")

    phases = dict(zip(_REMOVED, ("需求", "研究", "規劃", "執行", "審核"), strict=True))
    rendered = {contract(stem, phases[stem]) for stem in _REMOVED}
    assert len(rendered) == 1, "五份契約已經漂開"
    only = rendered.pop()
    for phrase in (
        "累加⛔ 不覆寫",
        "只能加嚴⛔ 不得放寬",
        "⛔ 沒有該檔＝沒有專案層注意事項",
        "project_roster_for",
        "是**新生的**",
    ):
        assert phrase in only, phrase


# ============================================ (6) 驗收 8：結案閘門

def test_the_gate_value_domain_is_only_the_closeout_status():
    """⛔ **不得改用 `TERMINAL_STATUSES`**（那含 `🛑已停止`）。

    `🛑已停止` 的條文是另一回事——canonical §0 要求「必填**決策與原因**後封存」，
    而那兩個必填今天**⛔ 沒有任何地方可驗**。
    """
    assert handoff_cmd.TERMINAL_BY_CLEANUP_ONLY == {"🏁完成"}
    assert handoff_cmd.TERMINAL_BY_CLEANUP_ONLY < assign_cmd.TERMINAL_STATUSES
    assert "🛑已停止" not in handoff_cmd.TERMINAL_BY_CLEANUP_ONLY


def test_the_log_mark_is_a_bare_boolean():
    """⛔ **不記繞過哪個閘門、⛔ 不記狀態值、⛔ 不記 next-stage。**

    ⭐ 理由是一個既有前提有**兩個**條件：`doctor` 的推導以「`handoff` 的留痕
    ⛔ 不含 next-stage **也** ⛔ 不含 `--status` 覆寫值」為前提。而 `--status` 之後的
    `elif` 鏈裡有閘門的只有 `release` 與 `backlog` ⇒ 寫「繞過 release 閘門」就洩漏了
    `next_stage`，直接破掉第一個條件。
    """
    mark = handoff_cmd.STATUS_OVERRIDE_LOG_MARK
    assert mark == "status-override 是"
    for leak in ("🏁完成", "release", "backlog", "next-stage", "繞過"):
        assert leak not in mark


def test_the_registration_that_assign_still_bypasses_is_present():
    """⛔ **不得推出「結案已不可直接設定」**——`assign` 那一側⛔ 不在射程。

    ⛔ 這⛔ 不是文件測試：`assign_cmd` 今天仍是零驗證自由文字，把那個事實從碼裡
    刪掉，下一個讀 `handoff` 閘門的人就會以為結案已經全面守住了。
    """
    source = Path(handoff_cmd.__file__).read_text(encoding="utf-8")
    assert "assign_cmd.py" in source
    assert "在 `assign` 那一側**完全無效**" in source
    # 反向佐證：`assign` 的 `--status` 至今⛔ 無 choices。
    parser_source = Path(assign_cmd.__file__).read_text(encoding="utf-8")
    assert 'p.add_argument(\n        "--status", default="🔨執行中"' in parser_source


# ============================================ (7) 驗收 8：端到端

# `F-執行-06` 逐字「驗證器要 import ⛔ 不重打」：開卡／交接／世界快照的配件全部
# 沿用 `test_pitfalls` 那一份，⛔ 不在此另建一套 fixture。
from .test_pitfalls import (  # noqa: E402  （fixture 需在模組層取名，pytest 才看得到）
    _handoff as _handoff_raw,
)
from .test_pitfalls import (  # noqa: E402
    _open,
    _only_item,
    _world,
    runner,
)


def _handoff(card_id: str, sha: str, **overrides) -> int:
    """在 `test_pitfalls._handoff` 之上**再補族清冊報告**。

    ⚠️ 那一支刻意**只**補注意事項那一份（本檔的族清冊測試量的就是族清冊閘門在
    各種輸入下的行為，自動補會讓它們變成零資訊）。本檔量的是**驗收 6 與 8**，
    族清冊那道對這裡是**前置條件⛔ 不是被測物** ⇒ 在這一層補齊。
    """
    if "--pitfall-report" not in overrides:
        overrides = {**overrides, "--pitfall-report": pitfalls.report_template("需求")}
    return _handoff_raw(card_id, sha, **overrides)


def test_the_gate_refuses_the_closeout_status_with_rc_four_and_zero_writes(runner, capsys):
    """⭐ 承重：`--status 🏁完成` 必須 **rc=4 且世界狀態逐位元不變**。"""
    assert _open("CLOSEOUT-GATE1") == 0
    before = _world(runner)
    capsys.readouterr()

    assert _handoff("CLOSEOUT-GATE1", "1" * 40, **{"--status": "🏁完成"}) == 4

    assert _world(runner) == before, "拒收必須零寫入"
    err = capsys.readouterr().err
    assert "不是任何角色可直接設定的值" in err
    assert "wfcli handoff CLOSEOUT-GATE1" in err
    assert "--next-stage release" in err and "--cleanup" in err


def test_the_refusal_message_carries_no_placeholder(runner, capsys):
    """裁定 17 第 (iii) 條的**實戰檢驗**：訊息裡⛔ 不得有 `<…>` 佔位符。

    ⭐ 規劃階段草擬的版本含 `<卡ID>`／`<路徑>`，違反該條 ⇒ 實作改成代入實際值。
    """
    assert _open("CLOSEOUT-GATE2") == 0
    capsys.readouterr()
    _handoff("CLOSEOUT-GATE2", "2" * 40, **{"--status": "🏁完成"})
    command = [
        line.strip() for line in capsys.readouterr().err.splitlines()
        if line.strip().startswith("wfcli handoff")
    ]
    assert command, "訊息裡沒有可整行複製的指令"
    # ⚠️ 對**真的 stderr 字串**查 `<…>`，⛔ 不經 artifact 的任何重建（2026-09-03 改）。
    assert not re.search(r"<[^<>\n]{1,60}>", command[0]), command[0]


def test_a_non_closeout_status_override_still_goes_through(runner, capsys):
    """負控：閘門**依值**動作，⛔ 不是恆擋。`🛑已停止` ⛔ 不在值域內 ⇒ 放行。"""
    assert _open("CLOSEOUT-GATE3") == 0
    capsys.readouterr()
    assert _handoff("CLOSEOUT-GATE3", "3" * 40, **{"--status": "🛑已停止"}) == 0
    assert _only_item(runner).fields["交付狀態"] == "🛑已停止"


def test_the_log_line_records_the_override_as_a_bare_boolean(runner):
    """使用可反推：`grep 'status-override 是'` 即得使用次數。"""
    assert _open("CLOSEOUT-GATE4") == 0
    assert _handoff("CLOSEOUT-GATE4", "4" * 40, **{"--status": "⏸阻塞"}) == 0
    line = [ln for ln in _only_item(runner).body.splitlines() if "iteration" in ln][-1]
    assert f"；{handoff_cmd.STATUS_OVERRIDE_LOG_MARK}" in line, line
    # ⛔ 既有前提的兩個條件都不得被破：⛔ 不含 next-stage、⛔ 不含 --status 的值。
    assert "⏸阻塞" not in line, line
    for stage in ("release", "backlog", "review", "implementation"):
        assert stage not in line, line


def test_the_log_line_carries_no_mark_when_status_was_not_used(runner):
    """未走該路徑時**完全⛔ 不加這一段**——否則 grep 出來的次數恆等於交接次數。"""
    assert _open("CLOSEOUT-GATE5") == 0
    assert _handoff("CLOSEOUT-GATE5", "5" * 40) == 0
    line = [ln for ln in _only_item(runner).body.splitlines() if "iteration" in ln][-1]
    assert handoff_cmd.STATUS_OVERRIDE_LOG_MARK not in line, line


def test_the_note_gate_refuses_a_missing_report_with_zero_writes(runner, capsys):
    """驗收 6 的閘門端到端：缺報告 ⇒ rc=2 且世界狀態逐位元不變。"""
    assert _open("NOTE-GATE1") == 0
    before = _world(runner)
    capsys.readouterr()

    assert _handoff("NOTE-GATE1", "6" * 40, **{"--note-report": ""}) == 2

    assert _world(runner) == before, "拒收必須零寫入"
    err = capsys.readouterr().err
    assert "須附注意事項回應清冊" in err
    assert "判內容的是檢閱那一環" in err


def test_the_note_gate_says_out_loud_that_the_project_layer_was_empty(runner, capsys):
    """未給 `--repo-path` ⇒ 專案層視為空集合，**且在 stderr 明示**（⛔ 不靜默）。"""
    assert _open("NOTE-GATE2") == 0
    capsys.readouterr()
    assert _handoff("NOTE-GATE2", "7" * 40) == 0
    err = capsys.readouterr().err
    assert "專案層注意事項視為空集合" in err
    assert "⛔ 不代表該專案沒有加嚴條文" in err


def test_the_note_response_lands_in_the_log_line(runner):
    assert _open("NOTE-GATE3") == 0
    assert _handoff("NOTE-GATE3", "8" * 40) == 0
    line = [ln for ln in _only_item(runner).body.splitlines() if "iteration" in ln][-1]
    assert "注意事項回應 15 條" in line, line
    assert "踩坑回應" in line, line  # 兩份清冊各自留痕，⛔ 不合併
