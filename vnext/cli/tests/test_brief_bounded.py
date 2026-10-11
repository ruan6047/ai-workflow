"""#434：brief 預設輸出＝有界首屏＋一行指標；`--full`＝完整輸出（首屏不設上限＋完整原文附錄）。

上限與性質的定義居所＝`rules/core/flow.md` §4（brief 預設輸出 ≤ 120 非空行，硬性）；本檔是它的機械測試。
上限靠**呈現方式**達成：首屏資料驅動的索引清單依位置只列一部分、印省略數，原文與完整索引一律在 `--full`。
⛔ 不是 rc≠0 的行數 gate（超量不會失敗，只是不印）——這也不是 A3「⛔ 不設行數門檻」所指的
程式碼與文件規模門檻。全部走注入式快照，零網路、零 mutation。
"""

import pytest

from wfx.core.render import APPENDIX_HEADING, FIRST_SCREEN_HEADING, split_output
from wfx.verbs.brief import BOUNDED_NOTE, FIRST_SCREEN_NOTE, FULL_POINTER

from .fakes import BODY, FakeLinkedClients, snapshot
from .test_brief import ROLES, STAGES

LIMIT = 120          # rules/core/flow.md §4：brief 預設輸出的硬性上限（非空行）

N_COMMENTS = 200
N_LINKED = 30
N_POLICIES = 30
N_EXTRA_SECTIONS = 20
MODULES = ("bounded-a", "bounded-b", "bounded-c")


def nonempty(text):
    return [line for line in text.splitlines() if line.strip()]


def extreme_body():
    """五章節＋20 個五章節以外的標題＋30 筆相連任務登記。"""
    extras = "\n".join(f"## 自訂章節 {i}\n\n內容 {i}\n" for i in range(1, N_EXTRA_SECTIONS + 1))
    linked = "\n".join(f"- https://github.com/o/r/issues/{1000 + i} "
                       f"https://github.com/o/r/issues/{1000 + i}#issuecomment-{i}"
                       for i in range(1, N_LINKED + 1))
    return f"{BODY}\n{extras}\n## 相連任務\n\n{linked}\n"


def extreme_comments():
    return tuple({"url": f"https://example.invalid/c{i}",
                  "body": f"## 第 {i} 則留言的標題\n第 {i} 則內文第一行\n第 {i} 則內文第二行\n"}
                 for i in range(1, N_COMMENTS + 1))


def extreme_linked_clients():
    issues, comments = {}, {}
    for i in range(1, N_LINKED + 1):
        number = 1000 + i
        issues[("o/r", number)] = {
            "id": f"I_{number}", "number": number, "url": f"https://github.com/o/r/issues/{number}",
            "state": "OPEN", "updatedAt": "2026-10-12T00:00:00Z",
            "body": f"## 需求\n\n相連卡 {number} 需求原文\n\n## 限制與非目標\n\n相連卡 {number} 限制原文\n"}
        comments[i] = {"body": f"## 規劃階段完成卡 {number}\n相連卡 {number} 規劃原文\n",
                       "html_url": f"https://github.com/o/r/issues/{number}#issuecomment-{i}",
                       "issue_url": f"https://api.github.com/repos/o/r/issues/{number}"}
    return FakeLinkedClients(issues=issues, comments=comments)


@pytest.fixture
def extreme(rules_root, project_root, user_root):
    """極端輸入：200 則留言、30 筆相連登記、30 份 `.wf/*.md`、20 個五章節以外標題、3 個啟用模組。"""
    import json

    for i in range(1, N_POLICIES + 1):
        (project_root / ".wf" / f"policy-{i:02d}.md").write_text(
            f"# 政策 {i}\n\n## 1 · 甲\n\n內文\n\n## 2 · 乙\n\n內文\n", encoding="utf-8")
    for name in MODULES:
        directory = rules_root / "modules" / name
        directory.mkdir(parents=True)
        for stage in STAGES:
            (directory / f"{stage}.md").write_text(f"# {name}\n\n## 1 · 核對\n\n{name} 在{stage}。\n",
                                                   encoding="utf-8")
    config = json.loads((project_root / ".wf" / "config.json").read_text(encoding="utf-8"))
    config["modules"] = list(MODULES)
    (project_root / ".wf" / "config.json").write_text(json.dumps(config), encoding="utf-8")
    user_root.mkdir(parents=True)
    for name in ("model-usage.md", "model-availability.md"):
        (user_root / name).write_text(f"# {name}\n" + "備註一行。\n" * 50, encoding="utf-8")

    def run(run_cli, role, stage, *, full):
        return run_cli(role=role, stage=stage, full=full,
                       snapshots=[snapshot(body=extreme_body(), comments=extreme_comments())],
                       linked_clients=extreme_linked_clients())

    return run


# 驗收 3：極端輸入下 6 角色 × 5 階段的預設輸出都 ≤ 120 非空行、⛔ 無附錄、印省略數與 `--full` 指標
@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("role", ROLES)
def test_default_output_stays_within_the_limit_under_extreme_inputs(run_cli, extreme, role, stage):
    rc, out, err = extreme(run_cli, role, stage, full=False)
    assert (rc, err) == (0, "")
    assert len(nonempty(out)) <= LIMIT, len(nonempty(out))
    assert APPENDIX_HEADING not in out
    assert out.count(FIRST_SCREEN_HEADING) == 1
    assert out.rstrip("\n").endswith(FULL_POINTER)
    assert BOUNDED_NOTE in out and FIRST_SCREEN_NOTE not in out
    assert f"- （較早的 {N_COMMENTS - 15} 項未列；完整索引加 `--full`）" in out
    assert out.count("項未列；完整索引加 `--full`）") >= 3      # 留言、五章節以外、`.wf/*.md`


# 同一份極端輸入在 `--full` 下零遺漏：全部索引列與全部留言原文都在
def test_full_output_keeps_every_index_row_and_every_source(run_cli, extreme):
    rc, out, err = extreme(run_cli, "執行者", "執行", full=True)
    assert (rc, err) == (0, "")
    first, appendix = split_output(out)
    assert FULL_POINTER not in out and "項未列" not in out
    assert first.count("｜https://example.invalid/c") == N_COMMENTS
    assert first.count("- （五章節以外）自訂章節 ") == N_EXTRA_SECTIONS
    assert first.count("- .wf/policy-") == N_POLICIES
    assert first.count("｜https://github.com/o/r/issues/10") == N_LINKED
    for i in range(1, N_COMMENTS + 1):
        assert f"第 {i} 則內文第二行\n" in appendix
    for i in range(1, N_LINKED + 1):
        assert f"相連卡 {1000 + i} 規劃原文" in appendix


# 預設輸出只少了索引的列：其餘每一行都逐字出現在 `--full` 的首屏；保留的列依位置
def test_default_output_only_omits_index_rows(run_cli, extreme):
    _, bounded, _ = extreme(run_cli, "執行者", "執行", full=False)
    _, full, _ = extreme(run_cli, "執行者", "執行", full=True)
    first, _ = split_output(full)
    own = {BOUNDED_NOTE, FULL_POINTER}
    for line in bounded.splitlines():
        if line in own or "項未列；完整索引加 `--full`）" in line:
            continue
        assert line in first.splitlines(), line
    # 留言保留最新 15 則（原序號不變），其餘清單保留最先的 K 筆
    assert f"- comment-{N_COMMENTS - 14}｜" in bounded and f"- comment-{N_COMMENTS - 15}｜" not in bounded
    assert "- （五章節以外）自訂章節 5：" in bounded and "- （五章節以外）自訂章節 6：" not in bounded
    assert "- .wf/policy-07.md（" in bounded and "- .wf/policy-08.md（" not in bounded
    assert "- 8｜https://github.com/o/r/issues/1008｜" in bounded
    assert "- 9｜https://github.com/o/r/issues/1009｜" not in bounded


# 未超出上限時，預設輸出＝`--full` 的首屏（只換結構說明）＋一行指標：⛔ 不丟任何索引
def test_small_card_default_output_is_the_full_first_screen_plus_pointer(run_cli):
    rc, bounded, _ = run_cli(full=False)
    _, full, _ = run_cli(full=True)
    assert rc == 0
    first, _ = split_output(full)
    expected = first.rstrip("\n").replace(FIRST_SCREEN_NOTE, BOUNDED_NOTE) + f"\n\n{FULL_POINTER}\n"
    assert bounded == expected


def test_default_output_is_byte_identical_for_identical_inputs(run_cli, extreme):
    assert extreme(run_cli, "PM", "執行", full=False) == extreme(run_cli, "PM", "執行", full=False)


# 預設輸出⛔ 無附錄邊界：要機械切開就得用 `--full`
def test_split_output_needs_the_full_output(run_cli):
    _, bounded, _ = run_cli(full=False)
    with pytest.raises(ValueError):
        split_output(bounded)
