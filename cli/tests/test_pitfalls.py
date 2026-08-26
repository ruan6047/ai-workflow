"""``wf_cli.pitfalls`` 與 ``handoff`` 離開閘門的守衛（WF-STAGE-PITFALL-LIST1）。

⚠️ **本檔刻意獨立成一支。** ``test_commands_mocked.py`` 同時被 6 張活卡宣告，是本
repo 競爭最激烈的檔；新測試開新檔是本卡驗收條逐字要求的資源最小集。

⛔ **本檔不宣稱閘門擋得住敷衍。** 下面每一條驗的都是機械性質（窮舉性、值域、
非空、留痕形狀），⛔ 沒有一條驗得了「這個人真的檢查過」。
"""

from __future__ import annotations

import copy
import re
from pathlib import Path

import pytest
from wf_cli import pitfalls
from wf_cli.cli import build_parser
from wf_cli.commands import assign_cmd, handoff_cmd, open_cmd
from wf_cli.project import (
    FIELD_SPECS,
    ProjectError,
    find_item_by_card_id,
    list_items,
    resolve_project,
)

from .fake_gh import FakeGhRunner

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CANONICAL = _REPO_ROOT / "AI_WORKFLOW.md"


# ---- 既有測試的共用配件（本卡新增的必要前提改變了它們的契約）--------------


def with_pitfall_report(argv: list[str], card_id: str) -> list[str]:
    """把「離開現階段的族清冊回應」補進一組 ``handoff`` argv。

    ⚠️ **為什麼既有測試需要這個。** 本卡在 ``handoff`` 的前置段加了一道必要前提，
    於是「這組 argv 回 0」這個契約對**所有**既有呼叫點都變了。那不是新測試該去的
    地方（新測試在本檔下半），是既有測試要適應的新前提。

    ⛔ **不塞固定字串。** 清冊由 :func:`pitfalls.report_template` 依**離開階段**
    導出，而離開階段是**卡此刻的狀態**決定的、不是呼叫端寫得死的：
    ``test_handoff_log_line_never_carries_the_status_it_wrote`` 連跑六次 handoff，
    第 6 圈離開的是 ``執行``（13 族），其餘五圈離開 ``需求``／``研究``／``規劃``
    （各 8 族）。任何一個固定字串都會讓另一半的呼叫點轉紅。

    ``handoff_cmd.default_runner`` **就是這道指令待會要問的那個 runner**（三個測試
    檔的 fixture 都 monkeypatch 它）⇒ 這裡算出的格數與閘門看到的必然一致。

    ⚠️ **驗不到什麼（明說）**：本函式與產線共用同一個 :func:`
    pitfalls.resolve_departing_phase`，所以它對「離開階段判得對不對」是**零資訊**
    的——⛔ 不得把靠它變綠的那 33 條讀成閘門的守衛。閘門本身由本檔下半的端到端
    條目驗，清冊來源由上半的互含測試驗。這裡只負責讓既有測試繼續驗它們原本在驗
    的東西（iteration／狀態轉換／收尾清理／owner 快照）。

    三種情況原樣回傳（此時閘門構造上也不會要求報告，⇒ 不是放水）：
    呼叫端已自備 ``--pitfall-report``、卡不存在（``handoff`` 先回 rc=3）、
    離開階段判不出來（閘門走明文豁免那條分流）。
    """
    if "--pitfall-report" in argv:
        return argv

    runner = handoff_cmd.default_runner
    owner = argv[argv.index("--owner") + 1]
    number = int(argv[argv.index("--project") + 1])
    try:
        project = resolve_project(runner, owner, number)
    except ProjectError:
        return argv

    item = find_item_by_card_id(list_items(runner, project), card_id)
    if item is None:
        return argv

    resolution = pitfalls.resolve_departing_phase(
        item.text("階段"),
        item.fields.get("交付狀態"),
        handoff_cmd.STAGE_STATUS,
        handoff_cmd.STAGE_PHASE,
    )
    if resolution.phase is None:
        return argv
    return [*argv, "--pitfall-report", pitfalls.report_template(resolution.phase)]

#: 踩坑清單那一節的標題**逐字**。標題被改寫時下面的擷取會拿不到節，測試轉紅
#: ——那是要的：族清冊的來源不見了，碼側的清冊就沒有對照面。
_SECTION_HEADING = "### 6.4 分階段踩坑清單（WF-STAGE-STATE-TWO-AXIS1）"

#: 該節內「全階段族」那一行的行首逐字。
_CROSS_STAGE_PREFIX = "**全階段族（2）**："

#: 該節內階段族表格的列：``| `族名` | occ | 實測階段 |``。
_TABLE_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|")

#: 表格「實測階段」欄表示「沒有實測」的值**逐字**。⛔ 不用「含否定詞」這種開放
#: 判準——那會把任何新寫法都當成無實測而靜默放行。
_NO_MEASURED_STAGE = "⛔ 無實測"


def _canonical_section() -> list[str]:
    lines = _CANONICAL.read_text(encoding="utf-8").splitlines()
    hits = [i for i, ln in enumerate(lines) if ln == _SECTION_HEADING]
    assert len(hits) == 1, f"節標題必須恰好出現一次，實際 {len(hits)} 次"
    start = hits[0]
    end = next(
        (j for j in range(start + 1, len(lines)) if lines[j].startswith("#### ")),
        len(lines),
    )
    return lines[start:end]


def _canonical_families() -> tuple[tuple[str, ...], dict[str, tuple[str, ...]]]:
    """從條文抽出（全階段族, {實測階段: 階段族…}）。

    ⚠️ 抽取規則走**結構**（那一行的行首、表格的欄），不走「族名長什麼樣」——
    後者需要一份人維護的族名清單，而那正是本測試要對照的東西，會變成自我循環。
    """
    section = _canonical_section()

    cross_lines = [ln for ln in section if ln.startswith(_CROSS_STAGE_PREFIX)]
    assert len(cross_lines) == 1, "全階段族那一行必須恰好一行"
    cross = tuple(re.findall(r"`([^`]+)`", cross_lines[0]))

    by_stage: dict[str, list[str]] = {}
    unmeasured: list[str] = []
    for line in section:
        m = _TABLE_ROW.match(line)
        if not m:
            continue
        name, _occ, stage = m.groups()
        if stage == _NO_MEASURED_STAGE:
            unmeasured.append(name)
        else:
            by_stage.setdefault(stage, []).append(name)

    # §6.4 的處置逐字：無實測的族**暫列入全階段層一起印**。
    return cross + tuple(unmeasured), {k: tuple(v) for k, v in by_stage.items()}


# ---- A8：碼是權威、canonical 是引用面，兩個方向逐字互含 ------------------


def test_family_lists_are_mutually_inclusive_with_canonical():
    """⭐ **兩個方向都斷言**，缺一不可。

    - 條文有而碼沒有 ⇒ 該印的族印不出來，清冊靜默縮水。
    - 碼有而條文沒有 ⇒ 查核者引用不到，裁定只活在程式碼常數裡（樣板是
      ``doctor`` 的 root_cause_id 互含測試，其逐字理由是「裁定要寫在後續查核者
      引用得到的地方」）。

    ⚠️ **驗不到什麼**（明說）：它比對的是**族名字串**與**階段歸屬**，⛔ 不驗
    每一族的語意有沒有被改寫。條文把某族的解釋整段反轉而族名不動時，本條全綠。
    """
    doc_all_stage, doc_by_stage = _canonical_families()

    assert set(doc_all_stage) == set(pitfalls.ALL_STAGE_FAMILIES), (
        "全階段層（跨階段兩族 ＋ 無實測六族）兩側不一致：\n"
        f"  只在條文：{sorted(set(doc_all_stage) - set(pitfalls.ALL_STAGE_FAMILIES))}\n"
        f"  只在碼：{sorted(set(pitfalls.ALL_STAGE_FAMILIES) - set(doc_all_stage))}"
    )
    assert len(pitfalls.ALL_STAGE_FAMILIES) == len(set(pitfalls.ALL_STAGE_FAMILIES))

    assert doc_by_stage.keys() == pitfalls.STAGE_FAMILIES.keys(), (
        f"有實測階段的鍵不一致：條文 {sorted(doc_by_stage)}／"
        f"碼 {sorted(pitfalls.STAGE_FAMILIES)}"
    )
    for stage, families in doc_by_stage.items():
        assert set(families) == set(pitfalls.STAGE_FAMILIES[stage]), stage

    # 13 族全集：兩側同樣互含（上面兩條合起來已蘊含，這裡把它講成一句可讀的斷言）。
    doc_total = set(doc_all_stage) | {n for v in doc_by_stage.values() for n in v}
    assert doc_total == set(pitfalls.all_families())
    assert len(doc_total) == 13, f"條文側族數應為 13，實際 {len(doc_total)}"


def test_occurrence_numbers_never_enter_the_code():
    """⛔ occ 不得作為任何機械判斷的輸入——歸併映射從未被寫下，今天不可複驗。

    判準取**封閉集合**：碼側的 13 族全集裡，一個族名都不准帶數字，且模組本身
    不得出現條文表格裡的任何一個 occ 值作為獨立 token。⚠️ 後半是弱檢查（數字
    也可能是別的東西），故只掃**族名旁邊**的位置，不掃整份原始碼——否則
    ``DEGENERATION_SAMPLE_SIZE`` 這類正當常數會誤紅。
    """
    for name in pitfalls.all_families():
        assert not any(ch.isdigit() for ch in name), name

    source = (_REPO_ROOT / "cli" / "src" / "wf_cli" / "pitfalls.py").read_text(encoding="utf-8")
    for line in source.splitlines():
        if any(f'"{name}"' in line for name in pitfalls.all_families()):
            assert not any(ch.isdigit() for ch in line), f"族名那一行不得夾帶數字：{line}"


# ---- A7：有一個階段構造上永遠印不出來 -----------------------------------


def test_phases_mirror_the_project_stage_field_options():
    """七個階段是 Project 欄位選項的鏡射，⛔ 不是本模組另立的語彙。兩個方向。"""
    _, options = FIELD_SPECS["階段"]
    assert tuple(options) == pitfalls.PHASES


def test_the_maintenance_phase_is_unreachable_by_construction():
    """⭐ 逐字寫明：**維護階段的族清單在本實作下永遠印不出來。**

    三條路各自堵死，⛔ 不是「今天剛好沒人走」：

    1. ``--next-stage`` 的 choices 沒有 ``maintenance``——argparse 直接擋。
    2. ``STAGE_PHASE`` 沒有對應鍵 ⇒ 進入側寫不出維護。
    3. 交付狀態的反函數也產不出它 ⇒ 離開側同樣判不到。

    承接條件：新增維護屬**語彙變更**，會觸發採用專案 cpbl 的
    ``roadmap_lines.gate_of`` fail-closed。⛔ 不在本卡射程。
    """
    assert "維護" in pitfalls.PHASES
    assert "維護" in pitfalls.UNREACHABLE_PHASES

    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["handoff", "--owner", "acme", "--project", "1", "C1",
             "--to", "x", "--next-stage", "maintenance",
             "--source-sha", "a" * 40, "--evidence", "e"]
        )

    assert "維護" not in handoff_cmd.STAGE_PHASE.values()
    inverse = pitfalls.status_to_phase(handoff_cmd.STAGE_STATUS, handoff_cmd.STAGE_PHASE)
    assert "維護" not in inverse.values()

    # ⚠️ 而清冊本身**算得出來**——不可達的是輸入，不是函式。這一格分清楚，
    # 免得後人以為補上語彙還要重寫清冊。
    assert pitfalls.roster_for("維護") == pitfalls.ALL_STAGE_FAMILIES


# ---- A4：離開階段的取值 --------------------------------------------------


def test_status_inverse_is_injective_and_covers_exactly_five_statuses():
    """退路的前提：交付狀態 → 階段必須是**函數**（單射才有反函數）。

    ⛔ ``📥Backlog`` 不在結果裡，且那是對的：它改的是狀態不是階段。
    """
    inverse = pitfalls.status_to_phase(handoff_cmd.STAGE_STATUS, handoff_cmd.STAGE_PHASE)
    assert len(set(handoff_cmd.STAGE_STATUS.values())) == len(handoff_cmd.STAGE_STATUS)
    assert set(inverse.values()) == {"需求", "研究", "規劃", "執行", "審核"}
    assert len(inverse) == 5
    assert handoff_cmd.STAGE_STATUS["backlog"] not in inverse


def test_a_duplicated_status_is_dropped_rather_than_guessed():
    """兩個 next-stage 映到同一個交付狀態時**整個丟掉**，⛔ 不靠字典順序決定。"""
    inverse = pitfalls.status_to_phase(
        {"research": "X", "planning": "X", "review": "Y"},
        {"research": "研究", "planning": "規劃", "review": "審核"},
    )
    assert inverse == {"Y": "審核"}


@pytest.mark.parametrize(
    "stage_field,status,expected_phase,expected_source",
    [
        ("執行", "💡需求", "執行", "field"),        # 欄位優先
        (None, "🔨執行中", "執行", "status"),        # 欄位無值 → 反函數
        ("", "🔍待查核", "審核", "status"),
        ("亂寫的值", "🧭規劃中", "規劃", "status"),  # 欄位不可信 → 退回反函數
        (None, "📥Backlog", None, "none"),           # 兩條都不成立
        ("亂寫的值", "📥Backlog", None, "none"),
        (None, None, None, "none"),
    ],
)
def test_departing_phase_resolution(stage_field, status, expected_phase, expected_source):
    got = pitfalls.resolve_departing_phase(
        stage_field, status, handoff_cmd.STAGE_STATUS, handoff_cmd.STAGE_PHASE
    )
    assert (got.phase, got.source) == (expected_phase, expected_source)
    assert got.basis, "判定依據不得為空——豁免與拒收都要說得出理由"


# ---- A2／A3：粒度與預先登記的否證條件 -----------------------------------


def test_roster_is_all_stage_families_plus_the_stage_ones():
    assert pitfalls.roster_for("研究") == pitfalls.ALL_STAGE_FAMILIES
    assert len(pitfalls.roster_for("執行")) == len(pitfalls.ALL_STAGE_FAMILIES) + 5
    assert set(pitfalls.roster_for("執行")) == set(pitfalls.all_families())
    assert pitfalls.roster_for("不存在的階段") == pitfalls.ALL_STAGE_FAMILIES


def test_degeneration_thresholds_are_pinned_before_launch():
    """⛔ 門檻寫死在碼裡，不得事後訂——事後訂等於看著結果決定什麼叫失敗。"""
    assert pitfalls.DEGENERATION_SAMPLE_SIZE == 30
    assert pitfalls.DEGENERATION_CHECKED_RATIO == 0.80
    assert pitfalls.DEGENERATION_FOUND_CEILING == 0


def test_the_epoch_states_it_is_a_triage_aid_not_a_security_boundary():
    """⚠️ 誠實聲明逐字照抄自 ``doctor`` 的界線常數；它不在，就是漏抄了。"""
    source = (_REPO_ROOT / "cli" / "src" / "wf_cli" / "pitfalls.py").read_text(encoding="utf-8")
    assert "界線是**分流輔助**，不是安全邊界" in source
    assert pitfalls.PITFALL_GATE_EPOCH == "2026-08-26T00:00:00+08:00"


def _full_report(phase: str) -> str:
    return pitfalls.report_template(phase)


def test_a_full_roster_report_parses_clean():
    parsed = pitfalls.parse_report(_full_report("執行"), pitfalls.roster_for("執行"))
    assert parsed.ok, parsed.errors
    assert len(parsed.rows) == len(pitfalls.roster_for("執行"))
    assert parsed.counts() == {"checked": 13, "not_applicable": 0, "found": 0}


def test_all_three_verdicts_are_accepted_and_counted():
    roster = pitfalls.roster_for("研究")
    lines = [f"{roster[0]}：已檢查", f"{roster[1]}：不適用：本階段沒有寫入"]
    lines += [f"{n}：發現：已開卡追" for n in roster[2:]]
    parsed = pitfalls.parse_report("\n".join(lines), roster)
    assert parsed.ok, parsed.errors
    assert parsed.counts() == {"checked": 1, "not_applicable": 1, "found": 6}
    assert "踩坑回應 8 族" in parsed.digest()


def test_markdown_bullets_are_tolerated():
    roster = pitfalls.roster_for("審核")
    text = "\n".join(f"- {n}：已檢查" for n in roster)
    assert pitfalls.parse_report(text, roster).ok


def test_missing_one_family_is_refused():
    """**缺一即拒**——少答一族就過關的話，窮舉性就沒了。"""
    roster = pitfalls.roster_for("執行")
    text = "\n".join(f"{n}：已檢查" for n in roster[:-1])
    parsed = pitfalls.parse_report(text, roster)
    assert not parsed.ok
    assert any("缺 1 族未回答" in e and roster[-1] in e for e in parsed.errors), parsed.errors


def test_an_extra_family_name_is_refused():
    """**多一即拒**——湊行數也能過關的話，格數就不再由清冊決定。"""
    roster = pitfalls.roster_for("規劃")
    text = "\n".join(f"{n}：已檢查" for n in roster) + "\n不存在的族：已檢查"
    parsed = pitfalls.parse_report(text, roster)
    assert not parsed.ok
    assert any("不在本階段的族清冊內" in e for e in parsed.errors), parsed.errors


def test_a_duplicated_family_is_refused():
    roster = pitfalls.roster_for("規劃")
    text = "\n".join(f"{n}：已檢查" for n in roster) + f"\n{roster[0]}：已檢查"
    parsed = pitfalls.parse_report(text, roster)
    assert not parsed.ok
    assert any("出現 2 次" in e for e in parsed.errors), parsed.errors


@pytest.mark.parametrize("verdict", ["ok", "看過了", "不適用", "發現", "已檢查了", ""])
def test_values_outside_the_three_domains_are_refused(verdict):
    roster = pitfalls.roster_for("需求")
    lines = [f"{roster[0]}：{verdict}"] + [f"{n}：已檢查" for n in roster[1:]]
    parsed = pitfalls.parse_report("\n".join(lines), roster)
    assert not parsed.ok, verdict


def test_an_empty_reason_after_the_colon_is_refused():
    roster = pitfalls.roster_for("需求")
    lines = [f"{roster[0]}：不適用："] + [f"{n}：已檢查" for n in roster[1:]]
    parsed = pitfalls.parse_report("\n".join(lines), roster)
    assert not parsed.ok
    assert any("冒號之後是空的" in e for e in parsed.errors), parsed.errors


def test_a_found_row_keeps_everything_after_the_first_separator():
    """``發現：`` 自己帶的冒號不得把族名切壞（取**第一個**分隔符）。"""
    roster = pitfalls.roster_for("需求")
    lines = [f"{roster[0]}：發現：見留言：已開卡"] + [f"{n}：已檢查" for n in roster[1:]]
    parsed = pitfalls.parse_report("\n".join(lines), roster)
    assert parsed.ok, parsed.errors
    assert parsed.rows[0].family == roster[0]
    assert parsed.rows[0].detail == "見留言：已開卡"


def test_the_refusal_message_prints_a_usable_template():
    msg = pitfalls.refusal_message("執行", "測試用依據")
    for name in pitfalls.roster_for("執行"):
        assert name in msg
    assert "測試用依據" in msg
    # ⛔ 拒收訊息必須自陳它驗不到什麼，否則會被讀成比實際更強。
    assert "分不出認真讀過與隨手打一行" in msg


# ---- 端到端：閘門掛在寫入之前 -------------------------------------------


@pytest.fixture
def runner(monkeypatch):
    fake = FakeGhRunner()
    for module in (open_cmd, assign_cmd, handoff_cmd):
        monkeypatch.setattr(module, "default_runner", fake)
    return fake


_TARGET = ["--owner", "acme", "--project", "1"]


def _run(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def _open(card_id: str, **overrides) -> int:
    defaults = {
        "--feature": "示範功能", "--tier": "T3", "--db-scope": "none",
        "--core-pain": "痛點文字", "--service-goal": "服務的原始目標文字",
        "--exec-capability": "主力型", "--exec-capability-reason": "跨模組改動",
        "--review-capability": "主力型", "--review-capability-reason": "一般 review 即可",
    }
    defaults.update(overrides)
    argv = ["open", *_TARGET, card_id]
    for k, v in defaults.items():
        if isinstance(v, bool):
            if v:
                argv.append(k)
        else:
            argv += [k, v]
    return _run(argv)


def _handoff(card_id: str, sha: str, **overrides) -> int:
    defaults = {
        "--to": "查核者", "--next-stage": "review",
        "--source-sha": sha, "--evidence": "pytest 全綠",
    }
    defaults.update(overrides)
    argv = ["handoff", *_TARGET, card_id]
    for k, v in defaults.items():
        argv += [k, v]
    return _run(argv)


def _only_item(runner: FakeGhRunner):
    return list_items(runner, resolve_project(runner, "acme", 1))[0]


#: ``FakeGhRunner`` 上**不屬於世界狀態**的屬性：它們只記「問過什麼」／是測試旋鈕，
#: 被動到不代表遠端被改。⛔ 這是唯一的例外清單，其餘一律納入比對。
_NON_WORLD_ATTRS = frozenset({"graphql_calls", "calls", "revision_content_unavailable"})


def _world(runner: FakeGhRunner) -> dict:
    """整個 fake 世界的深拷貝快照（items ＋ **projects 的欄位定義** ＋ issues ＋ 序號）。

    ⭐ **刻意由 ``vars()`` 取全部屬性再扣掉明列的例外，⛔ 不是列舉「要比對哪幾格」。**
    查核 R1-001 的漏檢成因正是那種開放集合：舊斷言只深拷 ``runner.items``，於是
    ``ensure_fields`` 改掉 ``runner.projects[...]["fields"]``（欄位**定義**）時，
    比對面上完全看不見。封閉集合的好處是預設方向反過來——`FakeGhRunner` 之後長出
    任何新的狀態屬性都自動被納入，要排除得有人明寫進 ``_NON_WORLD_ATTRS``。

    ``_seq``／``_issue_seq`` 也在比對範圍內，而且它們是很靈敏的哨兵：`_next()` 只
    在「建立了什麼」時才被呼叫，⇒ 拒收路徑上序號一動就代表有東西被配置出來。
    """
    return {
        key: copy.deepcopy(value)
        for key, value in vars(runner).items()
        if key not in _NON_WORLD_ATTRS
    }


#: **唯讀** gh 子命令的白名單（封閉集合）。
#:
#: ⛔ 刻意不寫成「哪些會寫」的黑名單——`test_commands_mocked._RecordingRunner.MUTATING`
#: 就是黑名單形狀，而 R1-001 恰好是它擋不住的那一類：`field-create` 明明列在黑名單
#: 裡，卻沒有人想到 `ensure_fields` 會在前置段送出它，於是探針從沒對準過那條路。
#: 白名單反過來：**沒被明文宣告成唯讀的一切都算違規**，新增的 gh 動詞預設轉紅。
_READ_ONLY_GH: frozenset[tuple[str, ...]] = frozenset(
    {("project", "view"), ("project", "field-list")}
)


class CallLoggingRunner(FakeGhRunner):
    """記下每一次 gh 呼叫的 ``FakeGhRunner``。

    ``run_json`` 沒有被覆寫，它在 ``GhRunner`` 裡是走 ``self.execute``——⇒ 覆寫
    ``execute`` 與 ``graphql`` 兩支就覆蓋了全部出口。⚠️ ``FakeGhRunner`` 覆寫了
    ``graphql``，因此 GraphQL 呼叫**不會**經過 ``execute``，兩支都要掛。
    """

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[list[str]] = []

    def execute(self, args, input: str | None = None) -> str:  # type: ignore[override]
        self.calls.append(list(args))
        return super().execute(args, input)

    def graphql(self, query: str, **variables: str) -> dict:  # type: ignore[override]
        self.calls.append(["api", "graphql", query])
        return super().graphql(query, **variables)

    def not_declared_read_only(self) -> list[list[str]]:
        """回傳所有**沒被宣告成唯讀**的呼叫。空 list ＝ 這條路上一次寫入都沒有。"""
        offenders: list[list[str]] = []
        for call in self.calls:
            if call[:2] == ["api", "graphql"]:
                if "mutation" in call[2]:
                    offenders.append(["api", "graphql", "<mutation>"])
                continue
            if tuple(call[:2]) not in _READ_ONLY_GH:
                offenders.append(call)
        return offenders


@pytest.fixture
def logging_runner(monkeypatch):
    fake = CallLoggingRunner()
    for module in (open_cmd, assign_cmd, handoff_cmd):
        monkeypatch.setattr(module, "default_runner", fake)
    return fake


def _forget_field(runner: FakeGhRunner, name: str) -> None:
    """讓 Project 退回到**沒有這個凍結欄位**的樣子（欄位定義與所有 item 值一起拿掉）。

    模擬的是真實母體，不是人造病例：``FIELD_SPECS`` 會長新欄位（``階段`` 就是最近
    才加的那個），早於它建立的 Project 與卡就是這個形狀，而 ``ensure_fields`` 存在
    的理由正是補上它們。

    ⚠️ item 值要一起拿掉：``FakeGhRunner`` 的批次讀取會拿欄位名回查欄位型別，留著
    孤兒值會在**讀取端**就 KeyError——那是測試替身的假象，不是產線行為，會把測試
    引到另一條錯誤路徑上去（「複驗要用會通過的樣本」）。
    """
    runner.projects[("acme", 1)]["fields"].pop(name, None)
    for raw in runner.items.values():
        raw["fields"].pop(name, None)


def test_missing_report_refuses_with_zero_writes(runner, capsys):
    """⭐ 缺報告 ⇒ rc≠0，且**整個 fake 世界逐位元未變**。

    「零寫入」不用散文宣稱：快照走 :func:`_world`（含 Project 的欄位定義），
    任何一格被動到都會紅。⚠️ 本條的 Project 欄位是齊的，⇒ 它對 R1-001 那條路
    **沒有鑑別力**（欄位不缺時 ``ensure_fields`` 本來就不會建東西）；有鑑別力的
    是下面 ``test_missing_report_leaves_the_project_field_schema_untouched``。
    """
    assert _open("PITFALL-E2E1") == 0
    before = _world(runner)
    capsys.readouterr()

    rc = _handoff("PITFALL-E2E1", "a" * 40)

    assert rc == 2
    assert _world(runner) == before, "拒收路徑上狀態面必須一個字都沒寫"
    err = capsys.readouterr().err
    assert "須附踩坑族清冊回應" in err
    assert "狀態面一個字都沒寫" in err
    for name in pitfalls.roster_for("需求"):
        assert name in err


def test_a_valid_report_lets_the_handoff_through_and_lands_in_the_log(runner):
    """合格報告必須寫得進去（負控），且留痕帶**離開側**階段。"""
    assert _open("PITFALL-E2E2") == 0
    rc = _handoff(
        "PITFALL-E2E2", "b" * 40,
        **{"--pitfall-report": pitfalls.report_template("需求")},
    )
    assert rc == 0
    item = _only_item(runner)
    assert item.fields["交付狀態"] == "🔍待查核"

    line = [ln for ln in item.body.splitlines() if "iteration" in ln][-1]
    assert f"；{handoff_cmd.PHASE_LOG_LABEL} 需求；" in line, line
    assert "踩坑回應 8 族" in line, line
    # A5 的位置要求：階段段落在「證據」之前。
    assert line.index(handoff_cmd.PHASE_LOG_LABEL) < line.index("證據"), line


def test_the_report_can_be_read_from_a_file(runner, tmp_path):
    assert _open("PITFALL-E2E3") == 0
    path = tmp_path / "report.txt"
    path.write_text(pitfalls.report_template("需求"), encoding="utf-8")
    assert _handoff(
        "PITFALL-E2E3", "c" * 40, **{"--pitfall-report": f"@{path}"}
    ) == 0


def test_a_short_report_is_refused_with_zero_writes(runner, capsys):
    assert _open("PITFALL-E2E4") == 0
    roster = pitfalls.roster_for("需求")
    short = "\n".join(f"{n}：已檢查" for n in roster[:-1])
    before = _world(runner)
    capsys.readouterr()

    assert _handoff("PITFALL-E2E4", "d" * 40, **{"--pitfall-report": short}) == 2
    assert _world(runner) == before
    assert "缺 1 族未回答" in capsys.readouterr().err


def test_an_undeterminable_departing_phase_is_exempted_out_loud(runner, capsys):
    """⚠️ 這是一個**真實的口**，不是「檢查通過了」。

    把交付狀態改成沒有反函數的值就繞得過去——本測試把那條路走給人看，並要求
    它在 stderr 上自己承認。⛔ 不得把它讀成「這裡有檢查」。
    """
    # 造出**界線前既有卡**的形狀：階段欄無值（該欄是後來才加的，既有卡一片空白）
    # ＋交付狀態落在沒有反函數的那一格。⚠️ 這裡直接改 fake 的狀態面而不是走
    # ``wfcli``——因為 ``open`` 今天就會把階段寫成「需求」，走指令造不出既有卡的
    # 形狀，而既有卡才是這條分流真正要處理的母體。
    assert _open("PITFALL-E2E5") == 0
    raw = next(iter(runner.items.values()))
    raw["fields"].pop("階段", None)
    raw["fields"]["交付狀態"] = "📥Backlog"
    item = _only_item(runner)
    assert item.text("階段") is None
    capsys.readouterr()

    rc = _handoff("PITFALL-E2E5", "f" * 40, **{"--next-stage": "review"})
    assert rc == 0, "判不出階段時明文豁免（A4 允許的兩條之一）"
    err = capsys.readouterr().err
    assert "判不出正在離開哪個階段" in err
    assert "這條路上沒有檢查" in err

    line = [ln for ln in _only_item(runner).body.splitlines() if "iteration" in ln][-1]
    assert handoff_cmd.PHASE_UNDECIDABLE_MARK in line, line
    assert "豁免" in line, line


def test_before_the_epoch_no_report_is_required(runner, capsys, monkeypatch):
    """界線之前不要求。⚠️ 時戳釘死成常數，⛔ 不取「現在」——以牆上時鐘分流的
    判定會在某個午夜自己由綠轉紅（本 repo 已經被咬過一次）。"""
    assert _open("PITFALL-E2E6") == 0
    monkeypatch.setattr(handoff_cmd, "now_iso8601", lambda: "2020-01-01T00:00:00+08:00")
    capsys.readouterr()

    assert _handoff("PITFALL-E2E6", "0" * 40) == 0
    err = capsys.readouterr().err
    assert "早於踩坑閘門界線" in err
    assert "界線是分流輔助，不是安全邊界" in err


def test_a_malformed_timestamp_requires_the_report_rather_than_exempting(runner):
    """界線解析不了時 fail 的方向是**要求**，不是豁免。"""
    assert _open("PITFALL-E2E7") == 0
    assert handoff_cmd._before_epoch("不是時戳", pitfalls.PITFALL_GATE_EPOCH) is False


def test_a_stale_stage_field_is_reported_not_silently_preferred(runner, capsys):
    """⭐ 實測缺陷：``assign`` 只寫交付狀態、不寫階段欄 ⇒ 兩軸會對不上。

    掃描全 Project 時，兩個來源都判得出來的卡有 6 張、其中 **2 張不一致**，兩張
    都是「被指派執行、階段欄仍停在研究」。本條把那個形狀釘住：工具**不偷偷改判**
    （哪一軸權威是條文問題），但必須把分歧印出來。
    """
    assert _open("PITFALL-E2E9") == 0
    raw = next(iter(runner.items.values()))
    raw["fields"]["階段"] = "研究"
    raw["fields"]["交付狀態"] = "🔨執行中"
    capsys.readouterr()

    rc = _handoff(
        "PITFALL-E2E9", "8" * 40,
        **{"--pitfall-report": pitfalls.report_template("研究")},
    )
    assert rc == 0, "以階段欄為準 ⇒ 要的是研究的 8 族"
    err = capsys.readouterr().err
    assert "階段欄說「研究」" in err and "反推出「執行」" in err, err
    assert "assign 只寫交付狀態" in err


def test_the_gate_runs_after_the_existing_preflight_refusals(runner, capsys):
    """既有拒收路徑的退出碼不得被本閘門搶走。

    ⭐ 這條是**位置**的守衛：閘門若擺到既有檢查之前，同一個錯誤會換一個 rc
    回報，而那些 rc 已經被別的測試依賴。這裡拿部署閘門（rc=4）當代表。
    """
    assert _open("PITFALL-E2E8", **{"--needs-deploy": True}) == 0
    capsys.readouterr()
    rc = _handoff("PITFALL-E2E8", "9" * 40, **{"--next-stage": "release"})
    assert rc == 4, "部署閘門的 rc=4 必須先於踩坑閘門的 rc=2"


# ---- R1-001：閘門之前連 Project 的**欄位定義**都不准被動 -----------------
#
# 查核以「空欄位 Project」探針重現：`handoff` 回 rc=2，但 `field_created_before_gate
# =True`、`project_state_unchanged=False`。成因是 `ensure_fields` 並非唯讀（缺凍結
# 欄位就送 `gh project field-create`），而它原本擺在 `resolve_project` 旁邊——閘門
# 之前。下面三條分別是：正向（缺欄位＋缺報告 ⇒ 零寫入）、負控（缺欄位＋合格報告
# ⇒ 欄位確實被建）、以及呼叫面的獨立佐證。


def test_missing_report_leaves_the_project_field_schema_untouched(logging_runner, capsys):
    """⭐ **正向**：Project 少一個凍結欄位 ＋ 缺報告 ⇒ rc≠0 且欄位 schema 逐位元不變。

    這是 R1-001 的回歸條。⛔ 斷言不只比 ``runner.items``——那正是漏檢的成因；
    :func:`_world` 把 ``runner.projects`` 的欄位定義一起納入比對。
    """
    assert _open("PITFALL-FIELD1") == 0
    _forget_field(logging_runner, "階段")
    assert "階段" not in logging_runner.projects[("acme", 1)]["fields"], (
        "前提沒成立就不是這條測試要驗的世界"
    )
    before = _world(logging_runner)
    capsys.readouterr()

    rc = _handoff("PITFALL-FIELD1", "1" * 40)

    assert rc == 2
    assert "階段" not in logging_runner.projects[("acme", 1)]["fields"], (
        "拒收路徑上建了欄位＝R1-001 復發"
    )
    assert _world(logging_runner) == before, "欄位定義／items／序號都必須逐位元不變"
    assert "須附踩坑族清冊回應" in capsys.readouterr().err


def test_missing_report_makes_no_gh_write_call_at_all(logging_runner, capsys):
    """⭐ 同一條路的**呼叫面**佐證：整趟只送出被明文宣告成唯讀的 gh 呼叫。

    狀態比對過不了「寫進去又改回來」那關，呼叫紀錄過得了；反過來呼叫紀錄過不了
    「白名單漏列了某個其實會寫的動詞」，狀態比對過得了。⇒ 兩條一起才是證據。

    ⛔ 這條**不宣稱** wfcli 全指令零寫入。

    ⚠️ 原文的理由逐字寫「`assign`／`open` **仍刻意**在前置段呼叫 `ensure_fields`」
    ——`aiwf#154` 把五個命令模組的呼叫點全搬到各自的拒收之後，該前提⛔ 已為假
    （實測：`open` 的 `ensure_fields` 之前有 5 條非 0 return、`assign` 有 6 條）。
    故理由重寫如下：

    (a) 現在的順序：那五個動詞的 `ensure_fields` 都排在自己那幾道拒收**之後**。
    (b) 為什麼本條仍不宣稱零寫入——理由是**射程**而不是順序：本條只觀測
        `handoff` 缺報告那一條路的呼叫序列，⛔ 對其他動詞、其他路徑、成功路徑
        零資訊。
    (c) ⛔ 不得由此推出「`ensure_fields` 已是唯讀」——它不是，缺凍結欄位仍送
        `gh project field-create`，只是被搬到閘門之後。
    (d) ⛔ 更不得推出「拒收路徑已全面零寫入」：跨動詞的順序不變式由
        ``tests/conftest.py`` 的 gate-guard 守，而它今天仍帶著逐字登記的殘餘
        ``FROZEN = {("amend", 5): 2}``——那是**觀測面的盲點清單**，⛔ 不是
        「已驗證安全」清單（見 ``test_gate_before_write.FROZEN_WHY``）。

    同型的更正見 ``test_commands_mocked`` 對 assign 那條的就地註記。
    """
    assert _open("PITFALL-FIELD3") == 0
    _forget_field(logging_runner, "階段")
    logging_runner.calls.clear()
    capsys.readouterr()

    assert _handoff("PITFALL-FIELD3", "3" * 40) == 2

    assert logging_runner.calls, "代理沒攔到任何呼叫的話，下一句斷言是空的"
    assert logging_runner.not_declared_read_only() == [], (
        f"閘門之前出現非唯讀呼叫：{logging_runner.not_declared_read_only()}"
    )
    # ⭐ 白名單只說「沒有壞的」，⛔ 說不出「有哪些」。這一行把呼叫序列**逐筆釘死**
    # 成兩筆，正是 `handoff_cmd` 閘門旁那句就地註解——「只送出過 `gh project view`
    # 與批次讀 items 的 GraphQL query 兩種唯讀呼叫」——的機械驗證。⚠️ 注意
    # ``project field-list`` 也在白名單上，⇒ 沒有這一行的話，`ensure_fields`
    # 只搬走一半（例如只留 `list_fields`）仍會全綠，而那句註解就又變成假的。
    shapes = [
        ("api", "graphql") if call[:2] == ["api", "graphql"] else tuple(call[:2])
        for call in logging_runner.calls
    ]
    assert shapes == [("project", "view"), ("api", "graphql")], shapes


def test_a_valid_report_still_creates_the_missing_field(logging_runner):
    """⭐ **負控**：缺欄位 ＋ 合格報告 ⇒ rc=0 且那個欄位**確實被建出來**。

    沒有這條的話，「正向那條變綠」與「`ensure_fields` 整個被弄丟」在觀測面上長得
    一模一樣。⇒ 這裡不只看欄位定義出現，還要求值真的寫得進去（`write_status_face`
    的 ``"階段" in fields`` 分支若拿到舊的 fields 就會靜靜跳過）。
    """
    assert _open("PITFALL-FIELD2") == 0
    _forget_field(logging_runner, "階段")

    rc = _handoff(
        "PITFALL-FIELD2", "2" * 40,
        **{"--pitfall-report": pitfalls.report_template("需求")},
    )

    assert rc == 0
    assert "階段" in logging_runner.projects[("acme", 1)]["fields"], (
        "閘門過了卻沒補欄位＝ensure_fields 被搬丟了"
    )
    item = _only_item(logging_runner)
    assert item.fields["階段"] == handoff_cmd.STAGE_PHASE["review"]
    assert item.fields["交付狀態"] == handoff_cmd.STAGE_STATUS["review"]
