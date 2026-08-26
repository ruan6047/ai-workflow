from __future__ import annotations

import functools
import os
import subprocess
import sys
from pathlib import Path

import pytest

#: sandbox 歷史的固定基準時刻。**刻意寫死，不取「現在」**：commit 日期只要跟著
#: 牆上時鐘走，任何以日期分流的判定（doctor 的 trailer 界線就是一個）都會在某個
#: 午夜自己由綠轉紅。2026-08-13T00:00 就這樣紅過一次——測試建 commit 時採當下
#: 時間，界線一到，本該落在界線前的那筆就跑到界線後去了。
#: 值取遠早於任何產品界線的過去，且**是常數**：它不隨執行時刻改變，故不論
#: 2026、2027 或更晚跑，同一筆 commit 永遠落在同一側。
SANDBOX_COMMIT_DATE = "2020-01-01T00:00:00+08:00"


def fixed_date_env(when: str) -> dict[str, str]:
    """把一筆 commit 的作者／提交者日期釘死在 `when`（ISO8601）。

    兩個都要設：git 的作者日期與提交者日期是各自獨立的欄位，只設一個，另一個
    仍會採當下時間；而 doctor 的界線分流讀的是**提交者**日期。
    """
    return {"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}


def git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, **env} if env else None,
    )
    return proc.stdout


@pytest.fixture
def sandbox_repo(tmp_path: Path) -> Path:
    """全新的一次性 git repo（非任何真實專案），供 doctor／git_ops 測試安全地
    `git worktree add`／建分支，不會碰到使用者機器上的任何實際 repo。

    初始 commit 的日期釘在 `SANDBOX_COMMIT_DATE`，理由見該常數。
    """
    repo = tmp_path / "sandbox-repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "wf-cli tests")
    (repo / "README.md").write_text("sandbox\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-q", "-m", "init", env=fixed_date_env(SANDBOX_COMMIT_DATE))
    return repo


# ===========================================================================
# 閘門前零寫入不變式（gate-before-write invariant）
# ===========================================================================
#
# **它守什麼**：一個動詞被自己的閘門拒收時（``rc != 0``），``project.ensure_fields``
# 不得排在本輪第一次真寫入之前。``ensure_fields`` 缺凍結欄位時會送
# ``gh project field-create``——把它擺在閘門之前，拒收路徑就會先改掉 Project 的
# 欄位定義，而那正是每個呼叫點今天各自用註解與紀律維持、⛔ 沒有任何機械擋得住的事。
#
# **它怎麼掛**（四件事一次解決，⛔ 不要改回 ``mod.run``）：
#   1. 動詞集合取自 ``COMMAND_MODULES``——repo 自己的顯式封閉 tuple，且
#      ``test_cli_registry.py`` 已對它做過檔案系統雙向比對。⛔ 不自己列動詞名。
#   2. 入口函式由 ``build_parser()`` 反查（``set_defaults(func=…)`` 註冊的那一個），
#      ⛔ 不是 ``mod.run``：``checkpoint_cmd`` 註冊的是 ``run_checkpoint`` 與
#      ``run_contract_baseline``，**根本沒有 ``run``** ⇒ 掛 ``mod.run`` 會靜默漏掉它，
#      看得到的動詞從 11 個掉到 5 個。
#   3. 換掉的是**模組層屬性**，因此兩條呼叫路徑都被涵蓋：``build_parser()`` 之後
#      ``args.func(args)``（``set_defaults`` 在 ``add_parser`` 執行時才解析全域名字），
#      以及測試直接呼叫 ``mod.run(args)``。把 ``run`` 改名＋薄轉呼也繞不過去。
#   4. ``functools.wraps`` 是**必要的、不是禮貌**：不加就會弄紅
#      ``test_cli_registry::test_every_verb_dispatches_into_its_own_module``
#      （它讀 ``func.__module__``）。
#
# **判準是順序事實，⛔ 不是「有沒有真的建了欄位」**：``ensure_fields`` 是一個
# *可能* 寫入的呼叫，「它排在拒收之前」在欄位齊全的世界一樣觀測得到 ⇒ 守衛
# **不擾動世界**（⛔ 不 forget 任何欄位），於是不必新寫任何測試、也不會改變任何
# 被測動詞走的路徑。
#
# ---------------------------------------------------------------------------
# ⛔ 八件「不得由本守衛綠燈推出」
# ---------------------------------------------------------------------------
#
# ⚠️ 這一節是交付的一部分，⛔ 不是註解裝飾；``tests/test_gate_before_write.py::
# test_the_eight_non_conclusions_are_still_there`` 會擋下靜默刪除。
#
#: 逐字八件。第一件排第一是刻意的——那句話就寫在這張卡的卡 ID 裡。
MUST_NOT_CONCLUDE: tuple[str, ...] = (
    # (1)
    (
        "⛔ 不得推出「ensure_fields 已經是唯讀的」。本卡**只改呼叫時點**，"
        "⛔ 沒有改變 ensure_fields 的唯讀性——它仍然會送 gh project field-create。"
        "⚠️ 卡 ID 逐字是 WF-ENSURE-FIELDS-READONLY-BY-DEFAULT1、簡介逐字是「把 "
        "ensure_fields 改成預設唯讀」，而惰性 Mapping 與拆本體兩條路都已被裁定不採 ⇒ "
        "**交付名稱與交付內容不一致**，這是本卡上最可能被誤讀的一句話。"
    ),
    # (2)
    (
        "⛔ 不得推出「生產環境安全」。守衛掛的是 tests.fake_gh.FakeGhRunner；"
        "真的 GhRunner 從來沒有被掛過，其子類是否都經由 super() 送出呼叫**未窮舉**"
        "（本輪只確認 test_pitfalls.CallLoggingRunner 走 super()）。"
        "⇒ 綠燈說的是「既有測試替身上的順序」，⛔ 不是「線上不會發生」。"
    ),
    # (3)
    (
        "⛔ 不得推出「ensure_fields 具併發安全性」。本卡未改變也未驗證該性質；"
        "project.py 的就地註解自己已寫明它沒有任何 project 層的鎖，"
        "缺口與該用什麼鎖見 docs/WF_EVENT_IDEMPOTENCY1.md §7.1／§2.2。"
    ),
    # (4)
    (
        "⛔ 不得推出「所有寫入都在拒收之後」。守衛只看得到 gh 出口，"
        "⛔ 完全看不到 git 側寫入——handoff --cleanup 的 "
        "cleanup.execute_closeout_transition（分支刪除、worktree 移除、push）不經過 gh。"
        "⚠️ handoff 那 11 條是靠把 gh 側的 ensure_fields 搬進 write_status_face 消掉的，"
        "**沒有一條是靠證明 git 側沒寫而消掉的**。"
    ),
    # (5)
    (
        "⛔ 不得推出「殘餘的那幾條（FROZEN）是缺陷」。它們是**觀測面的盲點**："
        "那兩條測試自己 monkeypatch 掉 amend_cmd.set_field_value，"
        "產品碼真的寫了、只是那次寫入不經過 gh 出口。理由逐字見 "
        "tests/test_gate_before_write.py 的 FROZEN_WHY。"
    ),
    # (6)
    (
        "⛔ 不得推出「本 repo 的同族問題已解決」。aiwf#148 給這個缺陷家族取的 "
        "root_cause_id = gate-placed-after-a-writing-precondition **全 repo 0 命中**；"
        "本守衛的判準逐字只認「ensure_fields 有沒有排在本輪第一次真寫入之前」"
        "⇒ 下一個「寫入早於閘門」的形狀（換一個會寫的前置條件）它抓不到。"
    ),
    # (7)
    (
        "⛔ 不得把 AST 面的 0 讀成 handoff 乾淨。不 descend 的 AST 掃描對 "
        "_release_with_cleanup 內的拒收**看不見**（那是為了換取決定性付的代價："
        "descend 版會因 set 迭代序而擲幣，20 次得兩種答案）。"
        "⇒ AST 報 0 只代表「不 descend 的那個設定看不到」，⛔ 不代表那裡沒有。"
    ),
    # (8)
    (
        "⛔ 不得把「某個突變沒讓守衛轉紅」讀成「守衛判它合法」。"
        "行為型守衛的覆蓋**恰好等於既有測試的覆蓋**：M-B 那種"
        "（在 assign 加一條必須讀欄位定義才判得出的拒收）之所以一格未動，"
        "是因為那條拒收在既有測試裡**從未被走到**（所有測試都先跑 open 把欄位建齊）。"
        "⇒ 那是覆蓋不足的另一面，⛔ 不是合法性判定。若它真的被走到，守衛會紅"
        "**而且紅得對**，正解是改用唯讀的 list_fields。"
    ),
)

#: 唯讀 gh 呼叫的**封閉白名單**（形狀沿用 tests/test_pitfalls.py 的 ``_READ_ONLY_GH``）。
#:
#: ⚠️ **漏一項的方向是 fail-open**：把唯讀呼叫誤分類成寫入，會讓它變成「本輪第一次
#: 寫入」而豁免整輪 ⇒ 真違規被吞掉。反方向（把寫入誤分類成唯讀）只會多紅。
#: ⇒ 這裡寧可**列全**唯讀項，也不做「不確定就當寫入」。承重檢驗見
#: ``test_gate_before_write.py::test_read_only_whitelist_is_load_bearing_in_the_fail_open_direction``。
#:
#: ``("project","field-list")`` 今天在 ``src/`` 有 0 處字面呼叫（``aiwf#151`` 之後
#: ``list_fields`` 改走原生 GraphQL），**刻意保留**，理由逐字見
#: ``test_gate_before_write.py::test_field_list_stays_on_the_whitelist_on_purpose``。
#: ``("api", …)`` 不列在這裡——``gh api`` 的路徑是動態組出來的，由 ``classify_gh``
#: 依「有沒有改方法的旗標」分流。
READ_ONLY_GH: frozenset[tuple[str, str]] = frozenset(
    {("project", "view"), ("project", "field-list"), ("issue", "view")}
)

#: 讓 ``gh api <path>`` 由預設的 GET 變成寫入的旗標（``gh api --help`` 的封閉集合）。
_API_WRITE_FLAGS: frozenset[str] = frozenset(
    {"-X", "--method", "-f", "--raw-field", "-F", "--field", "--input"}
)


def classify_gh(argv: list[str]) -> str:
    """把一次 gh 呼叫分類成 ``"read"`` 或 ``"write"``。

    ``api graphql`` 依 query 內文分流（含 ``mutation`` 即寫）；其餘 ``api`` 路徑
    預設 GET，帶 ``_API_WRITE_FLAGS`` 任一才算寫；其餘一律以 ``(argv0, argv1)``
    對白名單比對，**白名單外算寫入**。
    """
    head = (argv[0] if argv else "", argv[1] if len(argv) > 1 else "")
    if head[0] == "api":
        if head[1] == "graphql":
            return "write" if any("mutation" in a for a in argv) else "read"
        return "write" if any(a in _API_WRITE_FLAGS for a in argv) else "read"
    return "read" if head in READ_ONLY_GH else "write"


def is_full_run(args, testpaths, narrowing) -> bool:
    """這一次 pytest 是不是「整套跑」。**純函式**，變異檢驗見 test_gate_before_write。

    ⚠️ 這個判準有兩個很像對的錯法，⛔ 都不要改回去：
      * 掃 ``config.invocation_params.args`` 找不以 ``-`` 開頭的 token 當位置參數
        ——會被 ``-p no:cacheprovider`` 的**選項值**騙成「有位置參數」；
      * 看 ``config.args`` 是不是空的——pytest 會把 ini 的 ``testpaths`` 填進去，
        整套跑時它是 ``["tests"]`` 而不是 ``[]``。

    正解：與 ``testpaths`` 逐項相等，且任一收窄旗標有值即判非整套。
    ``testpaths`` 為空時一律回 False（fail closed：判不出來就不宣稱是整套跑，
    於是「少掉一條」那個方向不會亂紅）。
    """
    if any(narrowing):
        return False
    if not list(testpaths):
        return False
    return list(args) == list(testpaths)


# --- 觀測狀態（session 級；單執行緒，⛔ 未對 xdist 做過任何保證）-----------------

_DEPTH: list[int] = [0]  # 動詞入口的巢狀深度：只記最外層那一輪
_IN_EF: list[int] = [0]  # 是否在 ensure_fields 的視窗內
_EVENTS: list[str] = []  # 本輪的 EF／寫入序列
_NODEID: list[str] = [""]
_RUNS: list[int] = [0]
_NONZERO: list[int] = [0]
_VIOLATIONS: list[int] = [0]
_OBSERVED: dict[tuple[str, int], int] = {}
_DETAIL: dict[tuple[str, int], list[tuple[str, tuple[str, ...]]]] = {}
_INSTALLED: list[bool] = [False]
_REPORTED: list[bool] = [False]  # terminal summary 已經印過完整裁決了嗎


def _record_gh(argv: list[str]) -> None:
    if _DEPTH[0] <= 0:
        return
    if classify_gh(argv) != "write":
        return
    label = (
        "api graphql <mutation>"
        if argv[:2] == ["api", "graphql"]
        else " ".join(argv[:2])
    )
    # ⭐ ensure_fields **自己送出的** field-create 另記成 EFW:，⛔ 不得算成「先前的寫入」。
    # 不加這一款，ensure_fields 會拿自己的寫入豁免自己（實測 review rc=3 那條就是
    # 這樣被放掉的）——用被檢驗對象自己當豁免理由是錯的。
    _EVENTS.append(("EFW:" if _IN_EF[0] else "W:") + label)


def _wrap_ensure_fields(orig):
    @functools.wraps(orig)
    def wrapped(*a, **k):
        if _DEPTH[0] <= 0:
            # 測試直接呼叫 ensure_fields（建世界用）不屬於任何一輪動詞執行。
            return orig(*a, **k)
        _EVENTS.append("EF")
        _IN_EF[0] += 1
        try:
            return orig(*a, **k)
        finally:
            _IN_EF[0] -= 1
    return wrapped


def _wrap_verb(orig, verb: str):
    @functools.wraps(orig)  # ⛔ 必要，不是禮貌：test_cli_registry 讀 func.__module__
    def wrapped(args):
        if _DEPTH[0] > 0:  # 巢狀（理論上不發生）只記最外層，避免序列互相污染
            return orig(args)
        _DEPTH[0] = 1
        del _EVENTS[:]
        _IN_EF[0] = 0
        try:
            rc = orig(args)
        finally:
            _DEPTH[0] = 0
        _RUNS[0] += 1
        if not rc:
            # ⛔ 成功路徑刻意不判：rc == 0 時 ensure_fields 排在寫入之前是**正確的**
            # （不加這一款，未搬動的基線上會多響 374 次）。
            return rc
        _NONZERO[0] += 1
        seq = tuple(_EVENTS)
        if "EF" not in seq:
            return rc
        writes = [i for i, e in enumerate(seq) if e.startswith("W:")]
        if writes and writes[0] < seq.index("EF"):
            # 本輪第一次真寫入排在 ensure_fields 之前 ⇒ 這不是「閘門前」。
            return rc
        key = (verb, int(rc))
        _OBSERVED[key] = _OBSERVED.get(key, 0) + 1
        _DETAIL.setdefault(key, []).append((_NODEID[0], seq))
        _VIOLATIONS[0] += 1
        return rc
    return wrapped


def _install_guard() -> None:
    from importlib import import_module

    from wf_cli import project as project_mod
    from wf_cli.cli import build_parser
    from wf_cli.commands import COMMAND_MODULES

    from .fake_gh import FakeGhRunner

    mods = {name: import_module(f"wf_cli.commands.{name}") for name in COMMAND_MODULES}

    # (1) ensure_fields：本體 ＋ 每一個 `from ..project import ensure_fields` 的綁定。
    orig_ef = project_mod.ensure_fields
    wrapped_ef = _wrap_ensure_fields(orig_ef)
    project_mod.ensure_fields = wrapped_ef
    for mod in mods.values():
        if getattr(mod, "ensure_fields", None) is orig_ef:
            mod.ensure_fields = wrapped_ef

    # (2) gh 出口：execute 與 graphql 兩支都要掛。run_json 在 GhRunner 裡走
    #     self.execute，但 FakeGhRunner **覆寫了 graphql** ⇒ GraphQL 不經過 execute。
    orig_execute = FakeGhRunner.execute
    orig_graphql = FakeGhRunner.graphql

    def execute(self, args, input=None):  # type: ignore[override]
        _record_gh(list(args))
        return orig_execute(self, args, input)

    def graphql(self, query, **variables):  # type: ignore[override]
        _record_gh(["api", "graphql", query])
        return orig_graphql(self, query, **variables)

    FakeGhRunner.execute = execute
    FakeGhRunner.graphql = graphql

    # (3) 動詞入口：由 build_parser() 反查，三種判不出來的情況一律硬紅（fail closed）。
    parser = build_parser()
    subs = [a for a in parser._actions if hasattr(a, "_name_parser_map")]
    assert subs, "[gate-guard] build_parser() 找不到子指令 action ⇒ 判不了，fail closed"
    seen = 0
    for verb, sub in subs[0]._name_parser_map.items():
        func = sub.get_default("func")
        assert func is not None, f"[gate-guard] 動詞 {verb} 沒有 func ⇒ 判不了，fail closed"
        modname = func.__module__.rsplit(".", 1)[-1]
        assert modname in mods, f"[gate-guard] {verb} 的 func 不在 COMMAND_MODULES（{modname}）"
        target = getattr(mods[modname], func.__name__, None)
        assert target is not None, f"[gate-guard] {verb} 的 func 不是模組層屬性，換不掉"
        setattr(mods[modname], func.__name__, _wrap_verb(target, verb))
        seen += 1
    assert seen >= len(COMMAND_MODULES), f"[gate-guard] 只掛到 {seen} 個動詞，少於模組數"
    _INSTALLED[0] = True


def pytest_configure(config) -> None:
    _install_guard()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    _NODEID[0] = item.nodeid
    yield
    _NODEID[0] = ""


def _guard_report(full_run: bool) -> str | None:
    """比對觀測值與逐字黃金值。回 None ＝ 通過。

    ⭐ **方向非對稱，⛔ 不是 ``got == FROZEN``**：
      * **多出來的一律紅**——多出來的一定是真的多出來，子集跑也該紅。
      * **少掉的只在整套跑時紅**——沿用本 repo「排除集不是垃圾桶」的紀律；
        對稱比對會讓任何 ``-k``／指定檔案／IDE 單條跑都變紅（實測：``-k`` 得
        「實得 {}」而紅），⛔ 那是每個開發者每天都會做的事，守衛上線第一天就會被關掉。
    """
    from .test_gate_before_write import FROZEN

    got = dict(_OBSERVED)
    extra = {k: v for k, v in got.items() if v > FROZEN.get(k, 0)}
    missing = {k: v for k, v in FROZEN.items() if got.get(k, 0) < v}
    if not extra and not (missing and full_run):
        return None

    lines = [
        "[gate-guard] 閘門前零寫入不變式：觀測值與逐字黃金值不符",
        f"  期待 {dict(sorted(FROZEN.items()))}",
        f"  實得 {dict(sorted(got.items()))}   (full_run={full_run})",
        f"  本次動詞入口 {_RUNS[0]} 次／其中 rc≠0 {_NONZERO[0]} 次／違規 {_VIOLATIONS[0]} 次",
    ]
    for key in sorted(extra):
        lines.append(f"  ⚠️ {key}: {FROZEN.get(key, 0)} → {got[key]}")
        for nodeid, seq in _DETAIL.get(key, []):
            lines.append(f"      {nodeid}  seq={list(seq)}")
    if missing and full_run:
        for key in sorted(missing):
            lines.append(
                f"  ⚠️ {key}: {FROZEN[key]} → {got.get(key, 0)}（死條目：黃金值裡有、實際沒發生）"
            )
    lines += [
        "  ⇒ 新增的違規：把該動詞的 ensure_fields 搬到「本輪第一次真寫入」之前那一刻；",
        "    若該拒收必須讀欄位定義才判得出來，改用唯讀的 list_fields 而不是 ensure_fields。",
        "  ⇒ 少了一條（只在整套跑時判）：黃金值一起改小，⛔ 不要留死條目。",
    ]
    return "\n".join(lines)


def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:
    # ⚠️ A13 的限制在這裡被**部分**補上、⛔ 沒有被消除：
    # 守衛失敗時 `pytest_sessionfinish` 只改得動行程退出碼，**摘要行仍然印
    # `NNNN passed`**。這一段把裁決寫進 terminalreporter（stdout，與摘要同一份輸出），
    # 讓人不必只靠 stderr 才看得到；但 **摘要行本身仍是 `passed`**。
    # ⇒ ⛔ 禁止在任何驗證指令裡接 `| tail`：那會同時吃掉退出碼與這段裁決。
    if not _INSTALLED[0]:
        return
    report = _guard_report(is_full_run(config.args, config.getini("testpaths"), _narrowing(config)))
    if report is None:
        return
    terminalreporter.write_line("")
    for line in report.splitlines():
        terminalreporter.write_line(line, red=True)


def _narrowing(config) -> tuple:
    opt = config.option
    return (
        getattr(opt, "keyword", "") or "",
        getattr(opt, "markexpr", "") or "",
        getattr(opt, "deselect", None) or [],
        bool(getattr(opt, "lf", False)),
        bool(getattr(opt, "failedfirst", False)),
    )


def pytest_sessionfinish(session, exitstatus) -> None:
    if not _INSTALLED[0]:
        return
    config = session.config
    report = _guard_report(is_full_run(config.args, config.getini("testpaths"), _narrowing(config)))
    if report is None:
        return
    # ⚠️ 這裡**不能**用「terminal summary 已經印過了嗎」當旗標判斷：
    # `TerminalReporter.pytest_sessionfinish` 是 **hookwrapper**，它在 yield 之後才
    # 呼叫 `pytest_terminal_summary` ⇒ 本函式**必然**先跑，旗標必然還是 False，
    # 於是兩邊都印全文、CI log 出現兩份逐條清單（實測）。
    # ⇒ 改判「有沒有 terminalreporter 這個消費者」，那是本函式跑的當下就成立的事實。
    tr = session.config.pluginmanager.get_plugin("terminalreporter")
    _REPORTED[0] = tr is not None and not getattr(tr, "no_summary", False)
    if _REPORTED[0]:
        # 完整裁決稍後由 pytest_terminal_summary 印在 stdout（與摘要行同一份輸出）。
        # 這裡只補一行 stderr 指標，⛔ 不重印整份。
        print(
            "[gate-guard] 閘門前零寫入不變式**未通過**：完整裁決見上方 terminal summary；"
            "⚠️ pytest 的摘要行仍會印 passed，判定只在退出碼（本次 = 1）。",
            file=sys.stderr,
        )
    else:
        # ⛔ 沒有 terminalreporter（例如 -p no:terminal）時裁決不能就這樣不見。
        print(report, file=sys.stderr)
    session.exitstatus = 1
