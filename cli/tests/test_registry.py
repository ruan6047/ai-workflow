from __future__ import annotations

import json
from pathlib import Path

import pytest

import wf_cli.registry
from wf_cli.registry import (
    OWNERSHIP_DECISIONS,
    RepoOwnershipVerdict,
    WorktreeRepoProbe,
    card_repo_from_issue_url,
    check_assign_repo_ownership,
    check_worktree_repo_ownership,
    enumerate_ownership,
    fetch_project_ownership_rows,
    load_tasks_md_registry,
    main,
    normalize_repo_slug,
    parse_active_ledger,
    parse_archived_card_ids,
    parse_markdown_tables,
    probe_worktree_repo,
    run_git_readonly,
    summarize_ownership,
)

from .conftest import git

ACTIVE_LEDGER = """# 任務看板

## Ledger 總表（活卡）

| 卡ID | Initiative | 級別 | 功能 | owner | 分支／worktree | iteration | 交付狀態 | 部署狀態 | 最後交接 |
|---|---|---|---|---|---|---|---|---|---|
| [CARD-A](tasks/CARD-A.md) | None | T2 | 示範卡 A | someone | `ai/agent/CARD-A @ .claude/worktrees/card-a` | 0 | 🚧進行中 | —不適用 | 2026-08-01T00:00:00+08:00 |
| [CARD-B](tasks/CARD-B.md) | INIT-X | T3 | 示範卡 B | 待指派 | — | 0 | 📥Backlog | —不適用 | 2026-07-01T00:00:00+08:00 |

## 依賴註記

- 一些不相干的文字，不是表格。
"""

ARCHIVE_LEDGER = """# 封存

| 卡ID | 功能 | 交付狀態 | 部署狀態 | 封存位置 |
|---|---|---|---|---|
| CARD-OLD1 | 舊卡 | 🏁完成 | —不適用 | [tasks/CARD-OLD1.md](tasks/CARD-OLD1.md) |
"""


def test_parse_markdown_tables_finds_both_tables_and_ignores_prose():
    tables = parse_markdown_tables(ACTIVE_LEDGER)
    assert len(tables) == 1
    header, rows = tables[0]
    assert header[0] == "卡ID"
    assert len(rows) == 2


def test_parse_active_ledger_extracts_card_id_branch_and_worktree():
    cards = parse_active_ledger(ACTIVE_LEDGER)
    by_id = {c.card_id: c for c in cards}
    assert by_id["CARD-A"].branch == "ai/agent/CARD-A"
    assert by_id["CARD-A"].worktree_path == ".claude/worktrees/card-a"
    assert by_id["CARD-A"].delivery_status == "🚧進行中"
    assert by_id["CARD-A"].last_handoff == "2026-08-01T00:00:00+08:00"
    assert by_id["CARD-A"].owner_assigned() is True


def test_parse_active_ledger_handles_placeholder_branch_and_owner():
    cards = parse_active_ledger(ACTIVE_LEDGER)
    by_id = {c.card_id: c for c in cards}
    assert by_id["CARD-B"].branch is None
    assert by_id["CARD-B"].worktree_path is None
    assert by_id["CARD-B"].owner_assigned() is False


def test_parse_archived_card_ids_extracts_plain_text_ids():
    ids = parse_archived_card_ids(ARCHIVE_LEDGER)
    assert ids == {"CARD-OLD1"}


def test_load_tasks_md_registry_reads_docs_subdir(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "TASKS.md").write_text(ACTIVE_LEDGER, encoding="utf-8")
    archive_dir = docs / "archive"
    archive_dir.mkdir()
    (archive_dir / "TASKS_ARCHIVE.md").write_text(ARCHIVE_LEDGER, encoding="utf-8")

    registry = load_tasks_md_registry(tmp_path)
    assert {c.card_id for c in registry.active} == {"CARD-A", "CARD-B"}
    assert registry.archived_card_ids == {"CARD-OLD1"}
    assert len(registry.source_paths) == 2


def test_load_tasks_md_registry_falls_back_to_root_tasks_md(tmp_path: Path):
    (tmp_path / "TASKS.md").write_text(ACTIVE_LEDGER, encoding="utf-8")
    registry = load_tasks_md_registry(tmp_path)
    assert {c.card_id for c in registry.active} == {"CARD-A", "CARD-B"}


def test_load_tasks_md_registry_empty_when_no_files(tmp_path: Path):
    registry = load_tasks_md_registry(tmp_path)
    assert registry.active == []
    assert registry.archived_card_ids == set()
    assert registry.source_paths == []


def test_registered_card_repo_defaults_to_none_from_tasks_md(tmp_path: Path):
    """TASKS.md Ledger 沒有 repo 欄，所以本機來源永遠說「不知道」——不是猜。"""
    (tmp_path / "TASKS.md").write_text(ACTIVE_LEDGER, encoding="utf-8")
    registry = load_tasks_md_registry(tmp_path)
    assert all(c.repo is None for c in registry.active)


# ---------------------------------------------------------------------------
# 跨 repo 歸屬守衛（#57）
# ---------------------------------------------------------------------------

#: 需求方裁定明文要求逐字保留在 ``registry`` 模組頂端 danger 區塊的句子。
#:
#: 前兩句（2026-08-12 裁定，#57 issuecomment-5268265532）描述**建立面**現況；射程從
#: 「建立面預防」縮為「登記面攔截」之後，它們是唯一還在描述建立面的條款，**不得因
#: 縮射程而軟化或刪除**。卡面版與派審詞版字面不同（後者多了 ``git worktree add``），
#: 兩者都要在。
#:
#: 第三句（2026-08-13 二次裁定，#57 issuecomment-5273953073）描述**登記面本身**的
#: 另一條射程外路徑：Project 的 TEXT 欄可被直接改寫。需求方要求它以與前兩句**同等的
#: 強度**寫下——兩次縮射程的形狀相同（``wfcli`` 是慣例不是機制），所以兩個限制都必須
#: 讀得到，不得靠人記得。
REQUIRED_DANGER_SENTENCES = (
    "該卡未落地前，本 repo 對「人直接在 shell 建到錯的 repo」沒有任何預防",
    "該卡未落地前，本 repo 對「人直接在 shell 跑 git worktree add 建到錯的 repo」沒有任何預防",
    "本 repo 對「有人繞過 wfcli 直接改寫 Project 的分支worktree 欄」沒有任何預防",
)


@pytest.mark.parametrize("sentence", REQUIRED_DANGER_SENTENCES)
def test_module_danger_block_keeps_the_mandated_sentence_verbatim(sentence):
    """裁定要求的句子必須逐字在模組 docstring 裡。

    這條是**該裁定唯一的機械執行者**：句子沒有執行者就只是句子，下一個人重寫
    docstring 時不會有任何東西響。子字串比對刻意不做正規化（不 strip、不換行折疊、
    不去標點），因為「逐字」的判準就是逐字。
    """
    doc = wf_cli.registry.__doc__ or ""
    assert sentence in doc


def test_module_docstring_does_not_claim_creation_time_prevention():
    """兩次縮射程的反向釘死：被降級掉的宣稱不得回流。

    宣稱回流是最容易發生的退化——有人補一段說明時順手寫回舊框架——所以這裡把被禁的
    字面列出來擋住。前三個屬 R2-01（建立面移出射程），後兩個屬 R3-01（承諾降為
    「``wfcli assign`` 這一條路徑」，**不是**「登記面已被保護」）。
    """
    doc = wf_cli.registry.__doc__ or ""

    # 唯一被允許的例外：裁定原句的**否定式引用**。承諾降級的那句話用需求方的原詞
    # 寫下來比改寫成同義詞誠實，所以這裡只挖掉這一個逐字的否定形，其餘位置一律禁。
    # 挖掉的是**完整的否定片語**——把 "不是" 去掉就會被下面抓到。
    for allowed_negation in ('**不是「登記面已被保護」**',):
        assert allowed_negation in doc, "否定式引用被改寫了，這條例外就該一起撤掉"
        doc = doc.replace(allowed_negation, "")

    banned_claims = (
        "建立當下的預防",
        "建立當下被擋",
        "預防的唯一有效位置",
        "登記面已被保護",
        "登記面攔截的唯一有效位置",
    )
    for banned in banned_claims:
        assert banned not in doc, f"射程外的宣稱回流：{banned}"


def test_refusal_message_says_registration_rejected_not_creation_prevented():
    """拒絕訊息講的是「拒絕登記」，不得讓讀的人以為建立已被阻止。"""
    verdict = RepoOwnershipVerdict(
        reason_code="repo_mismatch",
        card_repo="ruan6047/cpbl-analytics",
        worktree_repo="ruan6047/ai-workflow",
        detail="commondir 的 origin → ruan6047/ai-workflow",
    )
    msg = verdict.refusal_message()
    assert "拒絕登記" in msg
    assert "阻止" not in msg and "已預防" not in msg


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ruan6047/ai-workflow", "ruan6047/ai-workflow"),
        ("git@github.com:ruan6047/ai-workflow.git", "ruan6047/ai-workflow"),
        ("https://github.com/ruan6047/cpbl-analytics.git", "ruan6047/cpbl-analytics"),
        ("https://github.com/ruan6047/cpbl-analytics", "ruan6047/cpbl-analytics"),
        ("ssh://git@github.com/ruan6047/ai-workflow.git", "ruan6047/ai-workflow"),
        ("https://github.com/ruan6047/cpbl-analytics/issues/57", "ruan6047/cpbl-analytics"),
        ("https://github.com/ruan6047/ai-workflow/pull/51", "ruan6047/ai-workflow"),
        # 大小寫不分：逐字比對會製造純大小寫的誤擋
        ("https://github.com/Ruan6047/AI-Workflow", "ruan6047/ai-workflow"),
        ("  ruan6047/ai-workflow  ", "ruan6047/ai-workflow"),
        # 認不出來的一律 None，不猜
        (None, None),
        ("", None),
        ("   ", None),
        ("ai-workflow", None),
        ("/Users/ruanruan/Dev/ai-workflow", None),  # 裸路徑三段以上不得被讀成 slug
        ("https://github.com/ruan6047", None),
        ("owner/re po", None),
    ],
)
def test_normalize_repo_slug_table(raw, expected):
    assert normalize_repo_slug(raw) == expected


def test_card_repo_only_accepts_issue_url_not_bare_slug():
    """卡 repo 只認 Issue URL。

    這條是守衛的反同義反覆保險：若裸 ``owner/repo`` 也被接受，呼叫端就能把
    ``--repo``／``WFCLI_REPO``（＝被檢查者自己的主張）餵成「卡的 repo」，於是
    在該擋的那一刻兩邊必然相等。漂移案例的形狀正是呼叫端環境設錯。
    """
    assert card_repo_from_issue_url("https://github.com/ruan6047/cpbl-analytics/issues/57") == (
        "ruan6047/cpbl-analytics"
    )
    assert card_repo_from_issue_url("ruan6047/cpbl-analytics") is None
    assert card_repo_from_issue_url(None) is None
    assert card_repo_from_issue_url("") is None


def test_only_match_produces_allow_exhaustively():
    """對 reason→decision **全表**窮舉：``match`` 是唯一放行碼。

    不是抽樣：迭代 ``OWNERSHIP_DECISIONS`` 本身，新增 reason 而忘了裁定放不放行
    時這條會紅。同時驗 ``RepoOwnershipVerdict.decision`` 確實由該表導出，而非
    另有一套 if。
    """
    allowing = {r for r, d in OWNERSHIP_DECISIONS.items() if d == "allow"}
    assert allowing == {"match"}
    for reason, decision in OWNERSHIP_DECISIONS.items():
        verdict = RepoOwnershipVerdict(
            reason_code=reason, card_repo="o/r", worktree_repo="o/r", detail="x"
        )
        assert verdict.decision == decision
        assert verdict.blocked is (decision == "block")


def _probe(slug):
    return WorktreeRepoProbe(
        slug=slug, source="target_dir", resolved_target="/tmp/x", probed_dir="/tmp/x",
        common_dir="/tmp/x/.git", remote_url="git@github.com:o/r.git", detail="probe detail",
    )


def test_verdict_blocks_on_cross_repo():
    v = check_worktree_repo_ownership(
        card_repo="ruan6047/cpbl-analytics", worktree_probe=_probe("ruan6047/ai-workflow")
    )
    assert v.reason_code == "repo_mismatch"
    assert v.decision == "block"
    assert "cpbl-analytics" in v.refusal_message()
    assert "ai-workflow" in v.refusal_message()


def test_verdict_allows_same_repo():
    v = check_worktree_repo_ownership(
        card_repo="ruan6047/ai-workflow", worktree_probe=_probe("ruan6047/ai-workflow")
    )
    assert v.reason_code == "match"
    assert v.decision == "allow"


def test_verdict_fail_closed_when_card_repo_undeterminable():
    v = check_worktree_repo_ownership(
        card_repo=None, worktree_probe=_probe("ruan6047/ai-workflow")
    )
    assert v.reason_code == "card_repo_undeterminable"
    assert v.decision == "block"


def test_verdict_fail_closed_when_worktree_repo_undeterminable():
    v = check_worktree_repo_ownership(
        card_repo="ruan6047/ai-workflow",
        worktree_probe=WorktreeRepoProbe(slug=None, detail="路徑不存在"),
    )
    assert v.reason_code == "worktree_repo_undeterminable"
    assert v.decision == "block"


def test_refusal_message_names_the_legitimate_path():
    """被擋的人必須看到出路（#16 §7.1），否則只會學會繞過守衛。"""
    for reason in (r for r, d in OWNERSHIP_DECISIONS.items() if d == "block"):
        msg = RepoOwnershipVerdict(reason, "o/a", "o/b", "detail").refusal_message()
        assert "卡就開在哪個 repo" in msg
        assert "連結" in msg


# --- 真實 git：兩個獨立 repo ＋ 真的 git worktree add -------------------------

def _repo_with_remote(root: Path, name: str, remote: str) -> Path:
    repo = root / name
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "wf-cli tests")
    git(repo, "remote", "add", "origin", remote)
    (repo / "README.md").write_text(name, encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-q", "-m", "init")
    return repo


@pytest.fixture
def two_repos(tmp_path: Path):
    """兩個真實 git repo，remote 分別對應本專案實際的兩個 repo。

    不是合成 fixture：真的 ``git init``／``git remote add``／``git worktree add``，
    判定走真實的 ``run_git_readonly``（真 subprocess），不注入任何假 probe。
    """
    aiwf = _repo_with_remote(tmp_path, "ai-workflow", "git@github.com:ruan6047/ai-workflow.git")
    cpbl = _repo_with_remote(tmp_path, "cpbl-analytics", "git@github.com:ruan6047/cpbl-analytics.git")
    return aiwf, cpbl


CPBL_ISSUE = "https://github.com/ruan6047/cpbl-analytics/issues/999"
AIWF_ISSUE = "https://github.com/ruan6047/ai-workflow/issues/57"


def test_real_cross_repo_existing_worktree_is_blocked(two_repos):
    """§8.3 的原案回放：cpbl 的卡，worktree 真的建在 ai-workflow repo 內。"""
    aiwf, _cpbl = two_repos
    wt = aiwf / ".claude" / "worktrees" / "cpbl-card"
    git(aiwf, "worktree", "add", "-q", "-b", "claude/CPBL-CARD1", str(wt))
    assert wt.is_dir()

    v = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=wt)
    assert v.decision == "block"
    assert v.reason_code == "repo_mismatch"
    assert v.card_repo == "ruan6047/cpbl-analytics"
    assert v.worktree_repo == "ruan6047/ai-workflow"


def test_real_cross_repo_blocked_before_worktree_exists(two_repos):
    """登記早於 ``git worktree add``：路徑還不存在時就要能擋下這筆登記。

    生產慣例是先 ``assign`` 登記、再由人去建立，所以「目標尚未存在」是常態而非邊角；
    此時仍判不出來就等於閘門在最常見的情形下失效。**它擋下的是登記，不是建立**
    （射程見 ``registry`` 模組頂端 danger）。
    """
    aiwf, _cpbl = two_repos
    not_created = aiwf / ".claude" / "worktrees" / "not-created-yet"
    assert not not_created.exists()
    v = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=not_created)
    assert v.decision == "block"
    assert v.reason_code == "repo_mismatch"
    assert v.worktree_repo == "ruan6047/ai-workflow"


def test_real_same_repo_worktree_is_allowed(two_repos):
    """合法配置：ai-workflow 的卡，worktree 建在 ai-workflow 內 → 放行。"""
    aiwf, _cpbl = two_repos
    wt = aiwf / ".claude" / "worktrees" / "wf-card"
    git(aiwf, "worktree", "add", "-q", "-b", "claude/WF-CARD1", str(wt))
    v = check_assign_repo_ownership(issue_url=AIWF_ISSUE, worktree_path=wt)
    assert v.decision == "allow"
    assert v.reason_code == "match"


def test_real_cpbl_card_in_cpbl_repo_is_allowed(two_repos):
    _aiwf, cpbl = two_repos
    wt = cpbl / ".claude" / "worktrees" / "cpbl-card"
    git(cpbl, "worktree", "add", "-q", "-b", "claude/CPBL-CARD1", str(wt))
    v = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=wt)
    assert v.decision == "allow"


def test_real_relative_worktree_path_resolved_against_base_dir(two_repos):
    """Ledger 存相對路徑；``base_dir`` 決定它落在哪個 repo，兩邊都要**導對 slug**。

    ⚠️ R3-02 之後兩邊都是 block（目標尚未建立 → ``ancestor_dir`` 推測 → 一律不放行），
    所以這條改成驗**導出的 repo** 與**被擋的理由**，而不是驗放行——放行與否已不是
    base_dir 語意的鑑別點，reason code 才是：同一個相對路徑錨在自己的 repo 是
    ``worktree_repo_inferred``（看起來相符但只有推測），錨在另一個 repo 是
    ``repo_mismatch``（推測就已經說不對）。
    """
    aiwf, cpbl = two_repos
    (aiwf / ".claude" / "worktrees").mkdir(parents=True)
    (cpbl / ".claude" / "worktrees").mkdir(parents=True)
    rel = ".claude/worktrees/card-x"

    own = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=rel, base_dir=cpbl)
    assert own.worktree_repo == "ruan6047/cpbl-analytics"
    assert own.reason_code == "worktree_repo_inferred"
    assert own.decision == "block"

    other = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=rel, base_dir=aiwf)
    assert other.worktree_repo == "ruan6047/ai-workflow"
    assert other.reason_code == "repo_mismatch"
    assert other.decision == "block"

    # base_dir 真的是鑑別點：兩次導出的 slug 不同。
    assert own.worktree_repo != other.worktree_repo

    # 兩邊都補上來源 repo 就都判得出來（且判對）——推測不放行不等於這條路走不通。
    assert check_assign_repo_ownership(
        issue_url=CPBL_ISSUE, worktree_path=rel, base_dir=cpbl, source_repo=cpbl
    ).decision == "allow"


def test_real_path_outside_any_git_repo_is_blocked(tmp_path: Path):
    outside = tmp_path / "not-a-repo"
    outside.mkdir()
    v = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=outside)
    assert v.decision == "block"
    assert v.reason_code == "worktree_repo_undeterminable"


def test_real_repo_without_origin_is_blocked(sandbox_repo: Path):
    """sandbox_repo 沒有 origin remote → 判不出 slug → fail-closed。"""
    v = check_assign_repo_ownership(issue_url=AIWF_ISSUE, worktree_path=sandbox_repo)
    assert v.decision == "block"
    assert v.reason_code == "worktree_repo_undeterminable"
    assert "origin" in v.detail


def test_draft_issue_card_is_blocked(two_repos):
    """DraftIssue 沒有 Issue URL → 卡 repo 判不出來 → fail-closed（已論證）。"""
    aiwf, _ = two_repos
    v = check_assign_repo_ownership(issue_url=None, worktree_path=aiwf)
    assert v.decision == "block"
    assert v.reason_code == "card_repo_undeterminable"


def test_probe_reports_commondir_and_remote(two_repos):
    aiwf, _ = two_repos
    probe = probe_worktree_repo(aiwf)
    assert probe.slug == "ruan6047/ai-workflow"
    assert probe.common_dir is not None and probe.common_dir.endswith(".git")
    assert probe.remote_url == "git@github.com:ruan6047/ai-workflow.git"


def test_run_git_readonly_returns_none_instead_of_raising(tmp_path: Path):
    assert run_git_readonly(tmp_path, ["rev-parse", "--git-common-dir"]) is None


# --- R1-02：可判定的目標 repo 語意 -------------------------------------------
#
# 舊版的錯誤前提是「worktree 的 repo 由目標路徑座落在哪決定」。git 的真語意是
# 「由 git worktree add 的來源 repo 決定，與目標路徑落在磁碟哪裡無關」，而
# canonical §4.5 明文路徑由實際建立者決定、未限定巢狀於 repo。以下四條把
# 「repo 外的合法新 worktree」與「相對路徑不再吃 cwd」釘成回歸。


def test_absolute_target_outside_any_repo_is_allowed_with_source_repo(two_repos, tmp_path):
    """**R1-02 的正面反例**：目標在 repo 外（祖先是非 git 目錄）且尚未建立。

    canonical §4.5 允許這種配置。舊版必然走到 ``worktree_repo_undeterminable``
    並 block；給了來源 repo 之後它是可判定的，且判定正確。
    """
    _aiwf, cpbl = two_repos
    outside = tmp_path / "elsewhere"
    outside.mkdir()  # 存在但不是 git repo——舊版祖先探測就是死在這一格
    target = outside / "cpbl-card-wt"
    assert not target.exists()

    without = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=target)
    assert without.decision == "block"
    assert without.reason_code == "worktree_repo_undeterminable"
    assert "source_repo" in without.detail  # 必須指名補法，否則就是無出路的誤擋

    with_source = check_assign_repo_ownership(
        issue_url=CPBL_ISSUE, worktree_path=target, source_repo=cpbl
    )
    assert with_source.decision == "allow"
    assert with_source.reason_code == "match"


def test_source_repo_overrides_misleading_path_nesting(two_repos):
    """來源 repo 是權威，路徑巢狀只是資訊。

    合法情境：從 cpbl 執行 ``git worktree add`` 到一個座落在 ai-workflow 目錄樹底下
    的新路徑。純看路徑會推成 ai-workflow（誤擋 cpbl 的卡）；看來源 repo 才是對的。
    巢狀事實不丟——``nested_repo`` 照樣報出來，那正是 §8.3 漂移隱形的形狀。
    """
    aiwf, cpbl = two_repos
    target = aiwf / ".claude" / "worktrees" / "cpbl-wt-not-created"
    (aiwf / ".claude" / "worktrees").mkdir(parents=True)

    inferred = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=target)
    assert inferred.decision == "block" and inferred.inferred is True

    probe = probe_worktree_repo(target, source_repo=cpbl)
    assert probe.slug == "ruan6047/cpbl-analytics"
    assert probe.source == "source_repo"
    assert probe.inferred is False
    assert probe.nested_repo == "ruan6047/ai-workflow"
    assert check_worktree_repo_ownership(
        card_repo="ruan6047/cpbl-analytics", worktree_probe=probe
    ).decision == "allow"


def test_source_repo_is_not_a_force_flag(two_repos, tmp_path):
    """給錯來源 repo 照樣被擋——它補的是事實，不是繞過比對。"""
    aiwf, _cpbl = two_repos
    target = tmp_path / "elsewhere" / "wt"
    (tmp_path / "elsewhere").mkdir()
    v = check_assign_repo_ownership(
        issue_url=CPBL_ISSUE, worktree_path=target, source_repo=aiwf
    )
    assert v.decision == "block"
    assert v.reason_code == "repo_mismatch"
    assert v.worktree_repo == "ruan6047/ai-workflow"


def test_source_repo_must_exist(tmp_path):
    v = check_assign_repo_ownership(
        issue_url=CPBL_ISSUE, worktree_path=tmp_path / "wt",
        source_repo=tmp_path / "no-such-dir",
    )
    assert v.decision == "block"
    assert "不是既存目錄" in v.detail


def test_relative_path_without_base_dir_never_reads_cwd(two_repos, monkeypatch):
    """相對路徑必須綁定明確 base_dir；沒綁定就是不可判定，**不拿 cwd 補**。

    直接把 cwd 切進 ai-workflow repo 再問：若還讀 cwd，這裡會得到
    ``repo_mismatch``（cwd 那個 repo）。得到 ``worktree_path_unanchored`` 才證明
    cwd 完全沒被查詢——這是「67 筆中 18 筆相對路徑、cwd 錯置會讓誤擋暴增」那條
    自陳的機械封堵。
    """
    aiwf, _cpbl = two_repos
    (aiwf / ".claude" / "worktrees").mkdir(parents=True)
    monkeypatch.chdir(aiwf)

    v = check_assign_repo_ownership(
        issue_url=CPBL_ISSUE, worktree_path=".claude/worktrees/card-x"
    )
    assert v.reason_code == "worktree_path_unanchored"
    assert v.decision == "block"
    assert v.worktree_repo is None
    assert "base_dir" in v.refusal_message()


def test_unanchored_relative_path_is_still_decidable_with_source_repo(two_repos, monkeypatch):
    """給了來源 repo，相對路徑就不必錨定——repo 歸屬本來就與路徑無關。"""
    aiwf, cpbl = two_repos
    monkeypatch.chdir(aiwf)
    v = check_assign_repo_ownership(
        issue_url=CPBL_ISSUE, worktree_path=".claude/worktrees/card-x", source_repo=cpbl
    )
    assert v.decision == "allow"


def test_inferred_block_message_names_the_source_repo_remedy(two_repos):
    aiwf, _cpbl = two_repos
    (aiwf / ".claude" / "worktrees").mkdir(parents=True)
    v = check_assign_repo_ownership(
        issue_url=CPBL_ISSUE, worktree_path=aiwf / ".claude" / "worktrees" / "new"
    )
    assert v.inferred is True
    msg = v.refusal_message()
    assert "推測" in msg
    assert "source_repo" in msg


def test_existing_worktree_outside_its_repo_is_determinable_without_source_repo(two_repos, tmp_path):
    """已建立的 worktree 不需要 source_repo：它的 ``.git`` 直接指回來源 repo。"""
    _aiwf, cpbl = two_repos
    outside = tmp_path / "detached-worktrees"
    outside.mkdir()
    wt = outside / "cpbl-card"
    git(cpbl, "worktree", "add", "-q", "-b", "claude/CPBL-OUT1", str(wt))
    probe = probe_worktree_repo(wt)
    assert probe.slug == "ruan6047/cpbl-analytics"
    assert probe.source == "target_dir"
    assert probe.inferred is False
    assert check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=wt).decision == "allow"


# --- R3-02：推測不得放行，以及補了 source_repo 之後**還是**剩下什麼 -----------
#
# 查核者的論點：``ancestor_dir`` 被標成 ``inferred`` 且模組明說它不是事實，
# 判定卻仍對它回 allow。以下四條把新規則與**它到不了的地方**一起釘住——後者刻意
# 用真的 ``git worktree add`` 寫成測試，免得日後有人把「補了 source_repo」讀成
# 「歸屬已被驗證」。


def test_ancestor_inference_never_allows_even_when_it_matches(two_repos):
    """R3-02 的核心：推測**相符**也不放行。

    這是生產最常見的那一格（登記早於建立、路徑巢狀在卡自己的 repo 底下），舊行為
    在此回 ``match``／allow。新行為回 ``worktree_repo_inferred``／block，且訊息要
    指名補法。
    """
    aiwf, _cpbl = two_repos
    (aiwf / ".claude" / "worktrees").mkdir(parents=True)
    target = aiwf / ".claude" / "worktrees" / "wf-card-not-created"
    assert not target.exists()

    v = check_assign_repo_ownership(issue_url=AIWF_ISSUE, worktree_path=target)
    assert v.worktree_repo == "ruan6047/ai-workflow" == v.card_repo  # 推測「看起來相符」
    assert v.reason_code == "worktree_repo_inferred"
    assert v.decision == "block"
    assert v.inferred is True
    assert "source_repo" in v.refusal_message()

    # 補上來源 repo 就過——被拒的是推測，不是這個配置本身。
    fixed = check_assign_repo_ownership(
        issue_url=AIWF_ISSUE, worktree_path=target, source_repo=aiwf
    )
    assert fixed.decision == "allow" and fixed.probe_source == "source_repo"


def test_ancestor_inference_cannot_be_used_to_register_a_cross_repo_creation(two_repos):
    """端到端：**無法**以祖先推測取得 allow，然後把同一路徑建成另一個 repo 的 worktree。

    這條走完查核者指定的完整劇本，全程真 git：

    1. 卡屬 ai-workflow，登記一個尚未建立、巢狀在 ai-workflow 底下的路徑
       → 推測說「相符」，但判定 **block**（取不到 allow，劇本第一步就斷）。
    2. 接著真的從 **cpbl** 執行 ``git worktree add`` 到同一路徑——**它成功了**。
       這證明本閘門確實沒有綁定建立行為（射程外，模組頂端 danger 第 1 條）。
    3. 建立後重新探測同一路徑：``target_dir`` 說它屬於 cpbl。**推測當初是錯的**，
       而錯的推測若被放行，看板上就會多一筆與事實相反的歸屬登記。

    第 3 步是這條測試的重點：它不是「推測不夠嚴謹」的美學問題，是推測會**指向與
    事實相反的 repo**，而它唯一的證據只有「這條路徑座落在誰底下」。
    """
    aiwf, cpbl = two_repos
    (aiwf / ".claude" / "worktrees").mkdir(parents=True)
    target = aiwf / ".claude" / "worktrees" / "looks-like-aiwf"

    before = check_assign_repo_ownership(issue_url=AIWF_ISSUE, worktree_path=target)
    assert before.decision == "block"
    assert before.reason_code == "worktree_repo_inferred"

    git(cpbl, "worktree", "add", "-q", "-b", "claude/SNEAKY1", str(target))
    assert target.is_dir()

    after = probe_worktree_repo(target)
    assert after.source == "target_dir"
    assert after.inferred is False
    assert after.slug == "ruan6047/cpbl-analytics"          # 事實
    assert before.worktree_repo == "ruan6047/ai-workflow"   # 推測，與事實相反
    assert check_assign_repo_ownership(
        issue_url=AIWF_ISSUE, worktree_path=target
    ).reason_code == "repo_mismatch"


def test_source_repo_allow_does_not_bind_the_actual_creation(two_repos):
    """**證明不了的那一半，寫成測試**：``source_repo`` 的 allow 不綁定建立行為。

    模組頂端 warning 第 1 條引用的就是這一條。取得 allow 之後照樣可以從別的 repo
    把同一路徑建起來——本測試真的做了一次，並確認它**成功**。

    它不是漏洞報告，是射程的機械化陳述：``assign`` 發生在建立之前，「歸屬」這個事實
    在建立之後才存在，單點檢查拿不到它。任何人日後想把「登記已通過閘門」讀成
    「這個 worktree 一定屬於這張卡的 repo」，這條會擋在他面前。
    """
    aiwf, cpbl = two_repos
    (aiwf / ".claude" / "worktrees").mkdir(parents=True)
    target = aiwf / ".claude" / "worktrees" / "declared-aiwf"

    allowed = check_assign_repo_ownership(
        issue_url=AIWF_ISSUE, worktree_path=target, source_repo=aiwf
    )
    assert allowed.decision == "allow" and allowed.probe_source == "source_repo"

    # 宣告說會從 aiwf 建立；實際從 cpbl 建立。閘門不觀測，所以它成功。
    git(cpbl, "worktree", "add", "-q", "-b", "claude/DECLARED1", str(target))
    assert probe_worktree_repo(target).slug == "ruan6047/cpbl-analytics"


def test_allow_records_which_probe_source_it_came_from(two_repos):
    """放行必須留下「憑什麼放行」——兩種 allow 的強度差很多，事後要分得出來。"""
    _aiwf, cpbl = two_repos
    wt = cpbl / ".claude" / "worktrees" / "existing"
    git(cpbl, "worktree", "add", "-q", "-b", "claude/EXISTING1", str(wt))

    fact = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=wt)
    assert fact.decision == "allow" and fact.probe_source == "target_dir"

    declared = check_assign_repo_ownership(
        issue_url=CPBL_ISSUE, worktree_path=cpbl / "not-created", source_repo=cpbl
    )
    assert declared.decision == "allow" and declared.probe_source == "source_repo"


# --- R1-03：唯讀枚舉器 --------------------------------------------------------


def _input_rows(aiwf: Path, cpbl: Path) -> list[dict]:
    return [
        {"card_id": "WF-OK", "issue_url": AIWF_ISSUE,
         "branch_worktree": f"claude/WF-OK @ {aiwf}"},
        {"card_id": "CPBL-DRIFT", "issue_url": CPBL_ISSUE,
         "branch_worktree": f"claude/CPBL-DRIFT @ {aiwf}"},
        {"card_id": "REL-UNANCHORED", "issue_url": CPBL_ISSUE,
         "branch_worktree": "claude/REL @ .claude/worktrees/rel"},
        {"card_id": "DRAFT", "issue_url": None,
         "branch_worktree": f"claude/DRAFT @ {cpbl}"},
    ]


def test_enumerator_reports_every_row_with_reason_and_decision(two_repos):
    aiwf, cpbl = two_repos
    rows = enumerate_ownership(_input_rows(aiwf, cpbl))
    by_id = {r.card_id: r for r in rows}
    assert len(rows) == 4
    assert by_id["WF-OK"].decision == "allow"
    assert by_id["CPBL-DRIFT"].reason_code == "repo_mismatch"
    assert by_id["CPBL-DRIFT"].worktree_repo == "ruan6047/ai-workflow"
    assert by_id["REL-UNANCHORED"].reason_code == "worktree_path_unanchored"
    assert by_id["DRAFT"].reason_code == "card_repo_undeterminable"
    assert by_id["WF-OK"].branch == "claude/WF-OK"


def test_enumerator_strips_markdown_backticks_from_registration(two_repos):
    """Project 欄位實測存著 ``` `branch @ path` ```；不剝反引號會讓存在的目錄被判成不存在。"""
    aiwf, _cpbl = two_repos
    rows = enumerate_ownership(
        [{"card_id": "TICKED", "issue_url": AIWF_ISSUE,
          "branch_worktree": f"`claude/TICKED @ {aiwf}`"}]
    )
    assert rows[0].branch == "claude/TICKED"
    assert rows[0].worktree_raw == str(aiwf)
    assert rows[0].target_exists is True
    assert rows[0].decision == "allow"


def test_summary_counts_are_derived_from_the_same_rows(two_repos):
    """§6.2：宣稱的數字與 artifact 同源。摘要不是另外數的。"""
    aiwf, cpbl = two_repos
    rows = enumerate_ownership(_input_rows(aiwf, cpbl))
    summary = summarize_ownership(rows)
    assert summary["total"] == len(rows)
    assert summary["allow"] + summary["block"] == summary["total"]
    assert summary["allow"] == sum(1 for r in rows if r.decision == "allow")
    assert sum(summary["by_reason_code"].values()) == len(rows)


def test_enumerator_cli_artifact_replay_is_a_fixed_point(two_repos, tmp_path):
    """產物可直接餵回 ``--input``，且逐字節相同（§6.2 的不動點要求）。"""
    aiwf, cpbl = two_repos
    src = tmp_path / "input.json"
    src.write_text(json.dumps({"rows": _input_rows(aiwf, cpbl)}), encoding="utf-8")

    first, second = tmp_path / "a.json", tmp_path / "b.json"
    assert main(["--input", str(src), "--output", str(first)]) == 0
    assert main(["--input", str(first), "--output", str(second)]) == 0
    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")

    artifact = json.loads(first.read_text(encoding="utf-8"))
    assert artifact["summary"]["total"] == 4
    assert len(artifact["input"]["rows"]) == 4  # 產物內含它用過的全部輸入
    assert artifact["rows"][0]["reason_code"]


def test_enumerator_tsv_carries_the_same_summary(two_repos, tmp_path, capsys):
    aiwf, cpbl = two_repos
    src = tmp_path / "input.json"
    src.write_text(json.dumps({"rows": _input_rows(aiwf, cpbl)}), encoding="utf-8")
    assert main(["--input", str(src), "--format", "tsv"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].split("\t")[:2] == ["card_id", "card_repo"]
    assert len(out) == 1 + 4 + 1  # header + 4 列 + summary
    assert json.loads(out[-1].split("\t", 1)[1])["total"] == 4


def test_fetch_project_rows_paginates_and_drops_rows_without_worktree():
    """注入假的 graphql runner：驗分頁、中文欄位名擷取、以及「無 worktree 註冊」被濾掉。"""
    pages = [
        {
            "data": {"user": {"projectV2": {"items": {
                "pageInfo": {"hasNextPage": True, "endCursor": "CUR"},
                "nodes": [
                    {"content": {"__typename": "Issue", "url": AIWF_ISSUE},
                     "fieldValues": {"nodes": [
                         {"text": "WF-A", "field": {"name": "卡ID"}},
                         {"text": "b @ /p/a", "field": {"name": "分支worktree"}},
                     ]}},
                    {"content": {"__typename": "Issue", "url": CPBL_ISSUE},
                     "fieldValues": {"nodes": [
                         {"text": "NO-WT", "field": {"name": "卡ID"}},
                         {"text": "—", "field": {"name": "分支worktree"}},
                     ]}},
                ],
            }}}}
        },
        {
            "data": {"user": {"projectV2": {"items": {
                "pageInfo": {"hasNextPage": False},
                "nodes": [
                    {"content": {"__typename": "DraftIssue"},
                     "fieldValues": {"nodes": [
                         {"text": "DRAFT-B", "field": {"name": "卡ID"}},
                         {"text": "b @ /p/b", "field": {"name": "分支／worktree"}},
                     ]}},
                ],
            }}}}
        },
    ]
    seen: list[object] = []

    def fake_run(payload):
        seen.append(payload["variables"]["after"])
        return pages[len(seen) - 1]

    rows = fetch_project_ownership_rows("ruan6047", 4, run=fake_run)
    assert seen == [None, "CUR"]
    assert [r["card_id"] for r in rows] == ["WF-A", "DRAFT-B"]
    assert rows[1]["issue_url"] is None  # DraftIssue 沒有 Issue URL，不猜
    assert rows[0]["branch_worktree"] == "b @ /p/a"


def test_guard_verdict_unaffected_by_stale_tasks_md_projection(two_repos):
    """守衛不吃 ``TASKS.md`` 投影——doctor 今天的誤報源頭碰不到它。

    做法：在被檢查的 repo 內**刻意**放一份與事實矛盾的 Ledger（宣稱該 worktree
    屬於另一張卡、另一個分支），再跑同一組判定，證明結果一字未變。
    """
    aiwf, _ = two_repos
    wt = aiwf / ".claude" / "worktrees" / "cpbl-card"
    git(aiwf, "worktree", "add", "-q", "-b", "claude/CPBL-CARD1", str(wt))
    before = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=wt)

    (aiwf / "TASKS.md").write_text(ACTIVE_LEDGER, encoding="utf-8")
    registry = load_tasks_md_registry(aiwf)
    assert registry.active, "前提：投影確實被讀得到，否則這條測試證明不了隔離"
    assert not any(c.worktree_path == str(wt) for c in registry.active), "前提：投影與事實不符"

    after = check_assign_repo_ownership(issue_url=CPBL_ISSUE, worktree_path=wt)
    assert after == before
    assert after.decision == "block"
