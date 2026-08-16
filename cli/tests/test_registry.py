from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

import wf_cli.registry
from wf_cli.registry import (
    LOCAL_OBSERVATION_ACTIONS,
    OWNERSHIP_DECISIONS,
    LocalWorktreeObservation,
    RepoOwnershipVerdict,
    card_repo_from_issue_url,
    check_assign_repo_ownership,
    check_worktree_repo_ownership,
    enumerate_ownership,
    fetch_project_ownership_rows,
    load_tasks_md_registry,
    main,
    normalize_repo_slug,
    observe_local_worktree,
    parse_active_ledger,
    parse_archived_card_ids,
    parse_markdown_tables,
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
# 跨 repo 歸屬守衛（#57）：軸 A（可攜的歸屬判定）與軸 B（機器局部的本機觀測）
# ---------------------------------------------------------------------------
#
# 本段的結構刻意對應 ``docs/ROADMAP.md`` §1.5 的裁定：
#
#     欄位若同時承載可攜的宣告與機器局部的操作細節，判定必須建立在可攜的那一半上。
#
# 所以測試也分兩區：軸 A 的每一條都必須在「沒有檔案系統」的世界裡成立，軸 B 的每一條
# 都必須標明它是這台機器的觀測。**混寫兩者就是把上一版的錯誤搬進測試裡。**

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


def test_module_docstring_does_not_claim_the_local_axis_is_portable():
    """R4-01 的反向釘死：軸 B 的性質不得被寫成可攜。

    這是本輪裁定的核心誤讀風險——``local_*`` 欄一旦被讀成「repo 的事實」，就會有人
    再一次拿它當對帳基準（需求方 2026-08-13 指出先前那 64 筆正是這樣被使用的）。
    所以把「這台機器」與「不是 repo 的事實」列為**必須在場**的字面，同時禁掉會讓人
    誤以為觀測結果跨機器成立的說法。
    """
    doc = wf_cli.registry.__doc__ or ""
    for required in ("這台機器", "不是 repo 的事實", "沉默不是判定"):
        assert required in doc, f"軸 B 的限定詞消失了：{required}"
    for banned in ("路徑就是歸屬", "由路徑導出歸屬", "跨機器一致的觀測"):
        assert banned not in doc, f"軸 B 被寫成可攜：{banned}"


def test_module_docstring_does_not_state_the_assign_before_create_order_as_structural():
    """釘死「登記早於建立」是**操作慣例**而非結構必然。

    這是本卡四輪未收斂的成因在文件層的殘留。前四輪每一輪都把「``assign`` 發生在建立
    之前」當成不可動的前提，於是每次都去縮**承諾**，沒有人去問那個**順序**能不能動——
    而 ``templates/worktree-lifecycle.md`` 第 1 點規定的順序其實是相反的（claim 成功後
    先建立 worktree，再把實際路徑寫回卡面）。順序一旦倒過來，「歸屬」這個事實在登記
    那一刻就已經存在，軸 B 便有東西可查（見
    ``test_local_observation_catches_the_real_cross_repo_worktree``）。

    ⚠️ 本測試**不**主張該順序應該被改——那是需求方的取捨，代價是 assign 只能在
    worktree 所在的機器上跑。它只擋一件事：**把一個可改的操作順序重新寫成定律**，
    因為那正是讓四輪把力氣全花在縮承諾上的那句話。
    """
    doc = " ".join((wf_cli.registry.__doc__ or "").split())

    for required in (
        "操作慣例，不是結構必然",
        "worktree-lifecycle.md",
        "本卡未做",
    ):
        assert required in doc, f"順序的限定詞消失了：{required}"

    # 前一版的原句（未加限定詞）。它與現行句子的差別就是「今天的」與「所以這一刻的」
    # 兩個限定詞，所以這個字面只會在限定詞被拿掉時重新出現。
    banned = "assign 發生在建立之前，而「歸屬」這個事實在建立之後才存在——單點檢查拿不到它"
    assert banned not in doc, "順序又被寫成結構必然（限定詞被移除）"


def test_refusal_message_says_registration_rejected_not_creation_prevented():
    """拒絕訊息講的是「拒絕登記」，不得讓讀的人以為建立已被阻止。"""
    verdict = RepoOwnershipVerdict(
        reason_code="repo_mismatch",
        card_repo="ruan6047/cpbl-analytics",
        worktree_repo="ruan6047/ai-workflow",
        detail="登記明示來源 repo 為 ruan6047/ai-workflow",
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


# --- 軸 A：歸屬判定必須可攜 ---------------------------------------------------
#
# 本區每一條都不碰檔案系統。下面兩條把「不碰」從慣例升級成機械保證——它們是本輪
# 裁定的驗收判準（「改成 slug 判定之後，這個檢查在另一台機器上跑會得到相同結果嗎」）
# 唯一能自動化的部分。


def test_ownership_signature_has_no_path_or_filesystem_input():
    """**簽章即裁定**：歸屬判定的入口不得收路徑、目錄、base_dir 或 git probe。

    這是 §1.5「判定必須建立在可攜的那一半上」在型別層的形狀。上一版的
    ``check_assign_repo_ownership(issue_url, worktree_path, source_repo, base_dir, git)``
    有四個機器局部的參數；只要它們還在簽章裡，任何人都能把判定重新綁回磁碟。
    """
    entry = set(inspect.signature(check_assign_repo_ownership).parameters)
    assert entry == {"issue_url", "worktree_source_repo"}

    core = set(inspect.signature(check_worktree_repo_ownership).parameters)
    assert core == {"card_repo", "declared_repo"}

    banned = {"worktree_path", "base_dir", "git", "source_repo", "worktree_probe"}
    assert not (entry | core) & banned


def test_ownership_axis_never_touches_the_filesystem(monkeypatch, tmp_path):
    """把 ``subprocess`` 與 ``Path.is_dir`` 換成會爆炸的替身，判定照樣得出同一答案。

    這條比「讀 code 沒看到 open()」強：它證明的是**執行期**一次都沒碰。若日後有人為了
    「順手補一下」而在歸屬路徑上加一行 ``git``，這裡會直接炸開。
    """
    def explode(*_a, **_k):  # pragma: no cover - 被呼叫就是測試失敗
        raise AssertionError("歸屬判定不得接觸檔案系統／子行程")

    monkeypatch.setattr(wf_cli.registry.subprocess, "run", explode)
    monkeypatch.setattr(Path, "is_dir", explode)
    monkeypatch.chdir(tmp_path)

    assert check_assign_repo_ownership(issue_url=AIWF_ISSUE).decision == "allow"
    assert check_assign_repo_ownership(
        issue_url=AIWF_ISSUE, worktree_source_repo="ruan6047/cpbl-analytics"
    ).reason_code == "repo_mismatch"
    assert check_assign_repo_ownership(issue_url=None).reason_code == "card_repo_undeterminable"


def test_ownership_verdict_is_identical_from_any_working_directory(
    two_repos, tmp_path, monkeypatch
):
    """**驗收判準的直接檢驗**：同一組輸入，在三個完全不同的 cwd 下判定逐欄相同。

    ai-workflow 內、cpbl-analytics 內、以及一個連 git repo 都不是的目錄。上一版在這三
    個位置會得到三種答案（``ancestor_dir`` 推測隨磁碟佈局而變）；本版三者必須全等。
    這是本機能做到的最接近「換一台機器」的實驗——真正的另一台機器不在測試能到達的
    範圍內，見報告的「證明不了的部分」。
    """
    aiwf, cpbl = two_repos
    outside = tmp_path / "nowhere"
    outside.mkdir()

    def verdicts() -> list[RepoOwnershipVerdict]:
        return [
            check_assign_repo_ownership(issue_url=AIWF_ISSUE),
            check_assign_repo_ownership(issue_url=CPBL_ISSUE),
            check_assign_repo_ownership(
                issue_url=AIWF_ISSUE, worktree_source_repo="ruan6047/cpbl-analytics"
            ),
            check_assign_repo_ownership(issue_url=None),
        ]

    baseline = verdicts()
    for cwd in (aiwf, cpbl, outside):
        monkeypatch.chdir(cwd)
        assert verdicts() == baseline


def test_verdict_blocks_on_declared_cross_repo():
    v = check_worktree_repo_ownership(
        card_repo="ruan6047/cpbl-analytics", declared_repo="ruan6047/ai-workflow"
    )
    assert v.reason_code == "repo_mismatch"
    assert v.decision == "block"
    assert v.basis == "explicit"
    assert "cpbl-analytics" in v.refusal_message()
    assert "ai-workflow" in v.refusal_message()


def test_verdict_allows_declared_same_repo():
    v = check_worktree_repo_ownership(
        card_repo="ruan6047/ai-workflow", declared_repo="git@github.com:Ruan6047/AI-Workflow.git"
    )
    assert v.reason_code == "match"
    assert v.decision == "allow"
    assert v.basis == "explicit"
    assert v.worktree_repo == "ruan6047/ai-workflow"


def test_verdict_fail_closed_when_card_repo_undeterminable():
    v = check_worktree_repo_ownership(card_repo=None, declared_repo="ruan6047/ai-workflow")
    assert v.reason_code == "card_repo_undeterminable"
    assert v.decision == "block"


@pytest.mark.parametrize(
    "given",
    [
        "/Users/ruanruan/Dev/ai-workflow",
        "../ai-workflow",
        ".",
        "ai-workflow",
    ],
)
def test_directory_given_as_declaration_is_refused_not_reinterpreted(given):
    """把**目錄**餵給 ``--worktree-source-repo`` 必須響，而且**不得被反推回 slug**。

    「不得反推」是本輪裁定的重點：上一版正是收目錄再讀它的 ``origin``，而那條路徑
    只在單一台機器成立。給錯型別就該當場說清楚，不能靠讀磁碟補回來——那等於把被
    拆掉的那條軸從後門接回去。
    """
    v = check_worktree_repo_ownership(card_repo="ruan6047/ai-workflow", declared_repo=given)
    assert v.reason_code == "declared_repo_unparseable"
    assert v.decision == "block"
    assert "slug" in v.refusal_message()
    assert "不是目錄" in v.refusal_message()


def test_default_declaration_is_a_no_op_on_the_ownership_axis():
    """⚠️ **把本版最弱的一環釘成測試**：沒帶旗標時軸 A 必然放行。

    模組頂端 warning 第 2 條寫了這件事，這裡讓它有執行者——不是為了讓它變好，是為了
    讓它**不能被悄悄描述成別的樣子**。任何人日後把「assign 通過閘門」讀成「歸屬已被
    檢查」，這條測試就是反例：``card_repo_default`` 這一格，卡的 repo 是什麼、判定就
    說 worktree 屬於什麼，兩邊同源，比對必然成立。
    """
    for issue in (AIWF_ISSUE, CPBL_ISSUE, "https://github.com/other/repo/issues/1"):
        v = check_assign_repo_ownership(issue_url=issue)
        assert v.decision == "allow"
        assert v.reason_code == "match"
        assert v.basis == "card_repo_default"
        assert v.worktree_repo == v.card_repo
        # 留痕必須說得出它是「沒人說」而不是「有人說對了」。
        assert "未明示" in v.detail


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
    軸 B 走真實的 ``run_git_readonly``（真 subprocess），不注入任何假 probe。
    """
    aiwf = _repo_with_remote(tmp_path, "ai-workflow", "git@github.com:ruan6047/ai-workflow.git")
    cpbl = _repo_with_remote(tmp_path, "cpbl-analytics", "git@github.com:ruan6047/cpbl-analytics.git")
    return aiwf, cpbl


CPBL_ISSUE = "https://github.com/ruan6047/cpbl-analytics/issues/999"
AIWF_ISSUE = "https://github.com/ruan6047/ai-workflow/issues/57"


def test_ownership_allow_does_not_bind_the_actual_creation(two_repos):
    """**證明不了的那一半，寫成測試**：allow 不綁定建立行為。

    模組頂端 warning 第 1 條引用的就是這一條。取得 allow 之後照樣可以從別的 repo
    把同一路徑建起來——本測試真的做了一次，並確認它**成功**。

    它不是漏洞報告，是射程的機械化陳述：**今天的** ``assign`` 發生在建立之前，
    「歸屬」這個事實在建立之後才存在，所以那一刻的單點檢查拿不到它。

    ⚠️ 這裡釘的是**「登記早於建立時會怎樣」**，不是「登記必然早於建立」。那個先後是
    操作慣例（``templates/worktree-lifecycle.md`` 第 1 點規定的順序其實相反），
    ``test_local_observation_catches_the_real_cross_repo_worktree`` 釘的就是順序倒過來
    以後軸 B 抓得到。兩條一起讀才是完整的射程。
    """
    aiwf, cpbl = two_repos
    (aiwf / ".claude" / "worktrees").mkdir(parents=True)
    target = aiwf / ".claude" / "worktrees" / "declared-aiwf"

    allowed = check_assign_repo_ownership(
        issue_url=AIWF_ISSUE, worktree_source_repo="ruan6047/ai-workflow"
    )
    assert allowed.decision == "allow"

    # 宣告說屬於 aiwf；實際從 cpbl 建立。軸 A 不觀測，所以它成功。
    git(cpbl, "worktree", "add", "-q", "-b", "claude/DECLARED1", str(target))
    observed = observe_local_worktree(target, expected_repo="ruan6047/ai-workflow")
    assert observed.observed_repo == "ruan6047/cpbl-analytics"
    # 事後才觀測得到，而且只在這台機器上。
    assert observed.code == "contradiction"
    assert observed.machine_local is True


# --- 軸 B：本機觀測 -----------------------------------------------------------
#
# 每一條都要同時驗「它說了什麼」與「它是不是機器局部的」。軸 B 唯一有資格拒絕的是
# **觀測到的矛盾**；祖先巢狀只警告（它的證據只有路徑座落在誰底下）。


def test_local_axis_only_contradiction_refuses_exhaustively():
    """對 code→action **全表**窮舉：``contradiction`` 是唯一會拒絕的碼。"""
    refusing = {c for c, a in LOCAL_OBSERVATION_ACTIONS.items() if a == "refuse"}
    assert refusing == {"contradiction"}
    warning = {c for c, a in LOCAL_OBSERVATION_ACTIONS.items() if a == "warn"}
    assert warning == {"nesting_conflict"}
    for code, action in LOCAL_OBSERVATION_ACTIONS.items():
        obs = LocalWorktreeObservation(code=code, expected_repo="o/r")
        assert obs.action == action
        assert obs.refuses is (action == "refuse")
        assert obs.machine_local is True


def test_local_observation_catches_the_real_cross_repo_worktree(two_repos):
    """§8.3 的原案回放：cpbl 的卡，worktree 真的建在 ai-workflow repo 內。

    ⚠️ 注意這條**不再是歸屬判定**：軸 A 對這筆登記說 allow（沒人宣告跨 repo），
    軸 B 才說矛盾。分軸之後，抓到這個案例的是「這台機器看到的事實」，而不是
    「從路徑反推出來的歸屬」——同一個結果，但來源誠實了。
    """
    aiwf, _cpbl = two_repos
    wt = aiwf / ".claude" / "worktrees" / "cpbl-card"
    git(aiwf, "worktree", "add", "-q", "-b", "claude/CPBL-CARD1", str(wt))

    ownership = check_assign_repo_ownership(issue_url=CPBL_ISSUE)
    assert ownership.decision == "allow"  # 軸 A 看不到它——這是本版誠實的代價

    obs = observe_local_worktree(wt, expected_repo=ownership.worktree_repo)
    assert obs.code == "contradiction"
    assert obs.refuses is True
    assert obs.observed_repo == "ruan6047/ai-workflow"
    assert obs.expected_repo == "ruan6047/cpbl-analytics"
    msg = obs.message()
    assert "這台機器" in msg
    assert "沉默不是判定" in msg


def test_local_observation_is_silent_when_target_not_created(two_repos):
    """生產常態（登記早於建立）→ 軸 B 沉默、放行。

    上一版在這一格 block（``worktree_repo_inferred``），代價是「未來每一次 assign 多
    打一個旗標」。本版不擋，因為那個 block 的全部證據是路徑巢狀。
    """
    aiwf, _cpbl = two_repos
    (aiwf / ".claude" / "worktrees").mkdir(parents=True)
    target = aiwf / ".claude" / "worktrees" / "not-created-yet"
    assert not target.exists()

    obs = observe_local_worktree(target, expected_repo="ruan6047/ai-workflow")
    assert obs.code == "target_absent"
    assert obs.action == "pass"


def test_nesting_conflict_warns_but_never_refuses(two_repos):
    """路徑座落在別的 repo 底下、目標尚未建立 → 只警告。

    ⚠️ **這正是本版相對上一版的偵測落差所在**（Project #4 全量枚舉裡真有這麼一筆）。
    降級的理由不是它沒價值，是它的證據只有「路徑座落在誰底下」，而 canonical §4.5
    明文路徑由實際建立者決定、未要求巢狀——換一台機器該證據直接消失。
    """
    aiwf, _cpbl = two_repos
    (aiwf / ".claude" / "worktrees").mkdir(parents=True)
    target = aiwf / ".claude" / "worktrees" / "cpbl-card-not-created"

    obs = observe_local_worktree(target, expected_repo="ruan6047/cpbl-analytics")
    assert obs.code == "nesting_conflict"
    assert obs.action == "warn"
    assert obs.refuses is False
    assert obs.nested_repo == "ruan6047/ai-workflow"
    assert "不擋" in obs.message()


def test_relative_registration_is_no_longer_blocked(two_repos, monkeypatch):
    """相對路徑（Project 上實存 18 筆、cpbl 那半的慣例）不再被擋。

    需求方 2026-08-13 的查證：``.claude/worktrees/xxx`` 在任何 clone 上指向同一相對
    位置，**比絕對路徑更可攜**。上一版把它判 ``worktree_path_unanchored``／block，
    收緊的正是比較可攜的那一種。本版：軸 A 照常放行，軸 B 只說「這台機器解析不到」。

    順帶保留 R1-02 的機械封堵——cwd 切進另一個 repo 也不得改變任何結果。
    """
    aiwf, _cpbl = two_repos
    (aiwf / ".claude" / "worktrees").mkdir(parents=True)
    monkeypatch.chdir(aiwf)

    ownership = check_assign_repo_ownership(issue_url=CPBL_ISSUE)
    assert ownership.decision == "allow"

    obs = observe_local_worktree(
        ".claude/worktrees/card-x", expected_repo=ownership.worktree_repo
    )
    assert obs.code == "path_unanchored"
    assert obs.action == "pass"
    assert obs.observed_repo is None  # cwd 一次都沒被查詢


def test_local_observation_resolves_relative_path_only_against_explicit_base_dir(two_repos):
    """給了 ``base_dir`` 才解析，且解析結果隨 base_dir 走——不隨 cwd 走。"""
    aiwf, cpbl = two_repos
    for root in (aiwf, cpbl):
        (root / ".claude" / "worktrees").mkdir(parents=True)
    rel = ".claude/worktrees/card-x"

    same = observe_local_worktree(rel, expected_repo="ruan6047/cpbl-analytics", base_dir=cpbl)
    assert same.code == "target_absent"

    other = observe_local_worktree(rel, expected_repo="ruan6047/cpbl-analytics", base_dir=aiwf)
    assert other.code == "nesting_conflict"
    assert other.nested_repo == "ruan6047/ai-workflow"


def test_local_observation_is_silent_when_origin_is_not_github_shaped(sandbox_repo: Path):
    """origin 是本機路徑（測試沙盒、bare 鏡像）→ 軸 B 沉默、**不再擋人**。

    上一版這一格是 fail-closed block，並且逼得 ``test_release_cleanup.py`` 整支繞過
    ``wfcli assign``。歸屬既然不再由 origin 反推，這條限制就跟著消失了——這是分軸的
    附帶收穫，不是本輪特地去修的。
    """
    obs = observe_local_worktree(sandbox_repo, expected_repo="acme/workflow")
    assert obs.code == "observed_repo_unidentifiable"
    assert obs.action == "pass"


def test_local_observation_does_not_change_the_ownership_verdict(two_repos):
    """**分軸的核心不變式**：軸 B 說什麼都不影響軸 A。

    做法：同一張卡、同一個宣告，一次指向乾淨路徑、一次指向已知矛盾的 worktree，
    比對兩次的軸 A 判定逐欄相同。軸 A 根本收不到路徑，所以這條在型別上就成立——
    但把它寫下來是為了讓「哪天有人把觀測結果餵回判定」立刻紅。
    """
    aiwf, _cpbl = two_repos
    wt = aiwf / ".claude" / "worktrees" / "drifted"
    git(aiwf, "worktree", "add", "-q", "-b", "claude/DRIFT1", str(wt))

    ownership = check_assign_repo_ownership(issue_url=CPBL_ISSUE)
    contradicting = observe_local_worktree(wt, expected_repo=ownership.worktree_repo)
    clean = observe_local_worktree(aiwf / "nope", expected_repo=ownership.worktree_repo)

    assert contradicting.refuses is not clean.refuses
    assert check_assign_repo_ownership(issue_url=CPBL_ISSUE) == ownership


def test_run_git_readonly_returns_none_instead_of_raising(tmp_path: Path):
    assert run_git_readonly(tmp_path, ["rev-parse", "--git-common-dir"]) is None


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
        {"card_id": "DECLARED-CROSS", "issue_url": AIWF_ISSUE,
         "branch_worktree": f"claude/DECLARED-CROSS @ {cpbl}",
         "worktree_source_repo": "ruan6047/cpbl-analytics"},
    ]


def test_enumerator_reports_both_axes_per_row(two_repos):
    aiwf, cpbl = two_repos
    rows = enumerate_ownership(_input_rows(aiwf, cpbl))
    by_id = {r.card_id: r for r in rows}
    assert len(rows) == 5

    # 軸 A：只有明示的跨 repo 宣告會被擋，DraftIssue 一律 fail-closed。
    assert by_id["WF-OK"].ownership_decision == "allow"
    assert by_id["WF-OK"].declaration_basis == "card_repo_default"
    assert by_id["CPBL-DRIFT"].ownership_decision == "allow"
    assert by_id["DRAFT"].ownership_reason == "card_repo_undeterminable"
    assert by_id["DECLARED-CROSS"].ownership_reason == "repo_mismatch"
    assert by_id["DECLARED-CROSS"].declaration_basis == "explicit"

    # 軸 B：抓到 CPBL-DRIFT（cpbl 的卡指向 ai-workflow 的工作樹），且標明機器局部。
    assert by_id["CPBL-DRIFT"].local_code == "contradiction"
    assert by_id["CPBL-DRIFT"].observed_repo == "ruan6047/ai-workflow"
    assert by_id["CPBL-DRIFT"].local_machine_local is True
    assert by_id["WF-OK"].local_code == "consistent"
    assert by_id["REL-UNANCHORED"].local_code == "path_unanchored"
    assert by_id["DRAFT"].local_code == "expected_repo_unknown"
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
    assert rows[0].ownership_decision == "allow"
    assert rows[0].local_code == "consistent"


def test_summary_counts_are_derived_from_the_same_rows(two_repos):
    """§6.2：宣稱的數字與 artifact 同源。摘要不是另外數的。"""
    aiwf, cpbl = two_repos
    rows = enumerate_ownership(_input_rows(aiwf, cpbl))
    summary = summarize_ownership(rows)
    assert summary["total"] == len(rows)
    assert summary["allow"] + summary["block"] == summary["total"]
    assert summary["allow"] == sum(1 for r in rows if r.ownership_decision == "allow")
    assert sum(summary["by_reason_code"].values()) == len(rows)
    assert sum(summary["local"]["by_code"].values()) == len(rows)
    assert summary["local"]["refuse"] == sum(1 for r in rows if r.local_action == "refuse")


def test_summary_labels_the_local_block_as_machine_local(two_repos):
    """摘要被貼進報告時最容易掉的是限定詞，所以限定詞就寫在數字旁邊。"""
    aiwf, cpbl = two_repos
    summary = summarize_ownership(enumerate_ownership(_input_rows(aiwf, cpbl)))
    assert "這台機器" in summary["local"]["note"]
    assert "不是 repo 的事實" in summary["local"]["note"]
    # 軸 A 的 allow／block 不得把軸 B 的數字混進去。
    assert summary["allow"] + summary["block"] == summary["total"]


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
    assert artifact["summary"]["total"] == 5
    assert len(artifact["input"]["rows"]) == 5  # 產物內含它用過的全部輸入
    assert artifact["rows"][0]["ownership_reason"]
    assert artifact["rows"][0]["local_code"]


def test_enumerator_tsv_carries_the_same_summary(two_repos, tmp_path, capsys):
    aiwf, cpbl = two_repos
    src = tmp_path / "input.json"
    src.write_text(json.dumps({"rows": _input_rows(aiwf, cpbl)}), encoding="utf-8")
    assert main(["--input", str(src), "--format", "tsv"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].split("\t")[:3] == ["card_id", "card_repo", "declared_repo"]
    assert len(out) == 1 + 5 + 1  # header + 5 列 + summary
    assert json.loads(out[-1].split("\t", 1)[1])["total"] == 5


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
    屬於另一張卡、另一個分支），再跑同一組判定，證明兩條軸的結果都一字未變。
    """
    aiwf, _ = two_repos
    wt = aiwf / ".claude" / "worktrees" / "cpbl-card"
    git(aiwf, "worktree", "add", "-q", "-b", "claude/CPBL-CARD1", str(wt))
    before_a = check_assign_repo_ownership(issue_url=CPBL_ISSUE)
    before_b = observe_local_worktree(wt, expected_repo=before_a.worktree_repo)

    (aiwf / "TASKS.md").write_text(ACTIVE_LEDGER, encoding="utf-8")
    registry = load_tasks_md_registry(aiwf)
    assert registry.active, "前提：投影確實被讀得到，否則這條測試證明不了隔離"
    assert not any(c.worktree_path == str(wt) for c in registry.active), "前提：投影與事實不符"

    assert check_assign_repo_ownership(issue_url=CPBL_ISSUE) == before_a
    assert observe_local_worktree(wt, expected_repo=before_a.worktree_repo) == before_b
    assert before_b.refuses is True
