"""#509：`brief --full` 首屏的 `### 模組文件定位`。

內容角色要能定位模組短文引用的 `wfx/docs/*.md`：不帶 `--omit-user-layer` 印實際路徑，帶了只印文件識別與取得方式；
⛔ 不注入文件內容、⛔ 不動預設輸出與未啟用輸出。全部走注入式快照，零網路、零 mutation。
"""

import re
import shutil
import sys

import pytest

from wfx.core import rules
from wfx.core.layers import MODULE_DOC_MISSING
from wfx.core.render import split_output
from wfx.verbs.brief import (
    MODULE_DOC_NOTE, MODULE_DOC_OVERRIDE_NOTE, MODULE_DOC_PACKAGE_NOTE, MODULE_DOC_TITLE, MODULE_DOC_WEB,
)
from wfx.verbs.main import main

from .conftest import REPO_RULES, TASK_ID
from .fakes import FakeClient, FakeLinkedClients
from .test_brief import section
from .test_modules import configure

FLAG = "--omit-user-layer"
HEADING = f"### {MODULE_DOC_TITLE}"
BOTH = ["architecture", "codegraph"]
BOTH_DOCS = ["wfx/docs/ARCHITECTURE.md", "wfx/docs/CODEGRAPH.md"]
TAG_URL = "https://github.com/ruan6047/ai-workflow/blob/vnext-v"
ROW = re.compile(r"^- (?P<ref>wfx/docs/[^：]+)(：(?P<where>.+))?$")


def rows(out):
    """`### 模組文件定位` 的 (文件識別, 位置)；只讀首屏，與附錄的模組原文無關。"""
    found = [ROW.match(line) for line in section(split_output(out)[0], MODULE_DOC_TITLE).splitlines()]
    return [(match["ref"], match["where"]) for match in found if match]


@pytest.fixture
def run_package(project_root, user_root, capsys):
    """不帶 `--rules-root` 的 CLI 進入點＝套件來源。"""
    def run(*extra, role="規劃者", stage="規劃"):
        rc = main(["--project-root", str(project_root), "brief", "--task", TASK_ID, "--role", role,
                   "--stage", stage, "--full", *extra],
                  client=FakeClient(), linked_clients=FakeLinkedClients())
        captured = capsys.readouterr()
        return rc, captured.out, captured.err
    return run


def assert_reads_originals(out, docs_dir):
    """照輸出的路徑逐檔讀：內容必須等於框架文件原檔。"""
    found = dict(rows(out))
    assert sorted(found) == BOTH_DOCS
    for ref, where in found.items():
        name = ref.removeprefix("wfx/docs/")
        assert where.startswith("/") and where == str(docs_dir.resolve() / name)
        with open(where, encoding="utf-8") as document:
            assert document.read() == (REPO_RULES.parent / "docs" / name).read_text(encoding="utf-8")


# D1 覆寫來源：`--rules-root` 指向 repo 的 `wfx/rules`，絕對與相對路徑都印成絕對路徑
def test_override_source_prints_readable_paths(run_cli, project_root, monkeypatch):
    configure(project_root, modules=BOTH)
    rc, out, err = run_cli("--rules-root", str(REPO_RULES), role="規劃者", stage="規劃")
    assert (rc, err) == (0, "")
    assert section(out, MODULE_DOC_TITLE).startswith(MODULE_DOC_NOTE)
    assert_reads_originals(out, REPO_RULES.parent / "docs")

    monkeypatch.chdir(REPO_RULES.parent)
    rc, relative, err = run_cli("--rules-root", "rules", role="規劃者", stage="規劃")
    assert (rc, err) == (0, "")
    assert relative == out


# D2 套件來源：路徑落在 `default_rules_root()` 同層 `docs/`
def test_package_source_prints_readable_paths(run_package, project_root):
    configure(project_root, modules=BOTH)
    rc, out, err = run_package()
    assert (rc, err) == (0, "")
    assert_reads_originals(out, rules.default_rules_root().parent / "docs")


# D3 覆寫來源旁沒有 `docs/`：逐檔列「找不到」、rc 0、⛔ 不退回套件來源
def test_override_without_docs_reports_missing_per_file(run_cli, project_root, rules_root):
    configure(project_root, modules=BOTH)
    rc, out, err = run_cli(role="規劃者", stage="規劃")
    assert (rc, err) == (0, "")
    assert rows(out) == [(ref, MODULE_DOC_MISSING) for ref in BOTH_DOCS]
    assert str(rules.default_rules_root().parent) not in split_output(out)[0]

    docs = rules_root.parent / "docs"
    docs.mkdir()
    shutil.copy(REPO_RULES.parent / "docs" / "CODEGRAPH.md", docs)
    _, partial, _ = run_cli(role="規劃者", stage="規劃")
    assert rows(partial) == [(BOTH_DOCS[0], MODULE_DOC_MISSING),
                             (BOTH_DOCS[1], str(docs.resolve() / "CODEGRAPH.md"))]


def assert_no_local_path(out, *paths):
    for path in (*paths, sys.prefix):
        assert str(path) not in out, path


# D4 省略使用者層：兩種來源都有文件識別、取得方式與回報 PM；輸出不含任何本機路徑
def test_omit_package_source_says_how_to_get_the_documents(
        run_package, project_root, tmp_path, user_root, monkeypatch):
    configure(project_root, modules=BOTH)
    monkeypatch.setattr(rules, "package_version", lambda: "9.9.9")
    rc, out, err = run_package(FLAG)
    assert (rc, err) == (0, "")
    assert rows(out) == [(ref, None) for ref in BOTH_DOCS]
    block = section(out, MODULE_DOC_TITLE)
    assert f"{rules.DISTRIBUTION} 套件（版本 9.9.9）" in block
    assert 'importlib.resources 讀 files("wfx") 下的 docs/<檔名>' in block
    assert f"{TAG_URL}9.9.9/vnext/cli/src/wfx/docs/<檔名>" in block
    assert "讀不到時回報 PM" in block
    assert_no_local_path(out, tmp_path, user_root.parent, rules.default_rules_root().parent)


def test_omit_override_source_points_beside_the_rules_directory(run_cli, project_root, rules_root,
                                                                 tmp_path, user_root):
    configure(project_root, modules=BOTH)
    rc, out, err = run_cli(FLAG, role="規劃者", stage="規劃")
    assert (rc, err) == (0, "")
    assert rows(out) == [(ref, None) for ref in BOTH_DOCS]
    block = section(out, MODULE_DOC_TITLE)
    assert MODULE_DOC_OVERRIDE_NOTE in block
    assert "同層的 docs/<檔名>" in block and "讀不到時回報 PM" in block
    assert "https://" not in block and rules.DISTRIBUTION not in block     # 覆寫來源不對應版本網址
    assert_no_local_path(out, tmp_path, user_root.parent, rules_root, rules.default_rules_root().parent)


def test_omit_package_source_with_unknown_version_has_no_tag_url(run_package, project_root, monkeypatch):
    configure(project_root, modules=BOTH)
    monkeypatch.setattr(rules, "package_version", lambda: rules.UNKNOWN_VERSION)
    rc, out, err = run_package(FLAG)
    assert (rc, err) == (0, "")
    block = section(out, MODULE_DOC_TITLE)
    assert "https://" not in block
    assert "版本 unknown" in block and "importlib.resources" in block and "讀不到時回報 PM" in block
    assert rows(out) == [(ref, None) for ref in BOTH_DOCS]


# D5 階段與停用：區塊跟著本階段已注入的模組短文（需求方裁定 issuecomment-6684201051）
@pytest.mark.parametrize("config", [{}, {"modules": None}, {"modules": ["tdd"]}])
@pytest.mark.parametrize("stage", ["需求", "規劃", "執行", "審核", "結案"])
@pytest.mark.parametrize("extra", [(), (FLAG,)])
def test_no_block_without_a_reference(run_cli, project_root, config, stage, extra):
    configure(project_root, **config)
    rc, out, _ = run_cli(*extra, stage=stage)
    assert rc == 0
    assert HEADING not in out


@pytest.mark.parametrize("stage,expected", [
    ("需求", BOTH_DOCS[:1]), ("規劃", BOTH_DOCS), ("執行", BOTH_DOCS), ("審核", BOTH_DOCS), ("結案", None)])
@pytest.mark.parametrize("extra", [(), (FLAG,)])
def test_block_follows_the_stage_documents(run_cli, project_root, stage, expected, extra):
    configure(project_root, modules=BOTH)
    rc, out, _ = run_cli(*extra, stage=stage)
    assert rc == 0
    if expected is None:
        assert HEADING not in out
    else:
        assert [ref for ref, _ in rows(out)] == expected


# 清單順序＝宣告順序下的出現順序；同一份被引用兩次只列一次
def test_refs_keep_first_seen_order_and_are_unique(run_cli, project_root, rules_root):
    directory = rules_root / "modules" / "sample"
    directory.mkdir()
    (directory / "執行.md").write_text("# 樣本\n\n見 `wfx/docs/Z.md`，再見 `wfx/docs/A.md` 與 `wfx/docs/Z.md`。\n",
                                       encoding="utf-8")
    configure(project_root, modules=["sample", "codegraph"])
    _, out, _ = run_cli(FLAG)
    assert [ref for ref, _ in rows(out)] == ["wfx/docs/Z.md", "wfx/docs/A.md", "wfx/docs/CODEGRAPH.md"]


# D6 預設輸出：無區塊、無絕對路徑
@pytest.mark.parametrize("extra", [(), (FLAG,)])
def test_default_output_has_no_block_and_no_absolute_path(run_cli, project_root, tmp_path, extra):
    configure(project_root, modules=BOTH)
    rc, out, _ = run_cli("--rules-root", str(REPO_RULES), *extra, role="規劃者", stage="規劃", full=False)
    assert rc == 0
    assert HEADING not in out and "wfx/docs/" not in out
    assert_no_local_path(out, tmp_path, REPO_RULES.parent)


# D7 不注入與範圍：兩份文件的獨有行不在輸出；core 提到的 `ADOPTION.md` 不被列出
@pytest.mark.parametrize("extra", [(), (FLAG,)])
def test_document_content_is_not_injected(run_cli, project_root, extra):
    configure(project_root, modules=BOTH)
    rc, out, _ = run_cli("--rules-root", str(REPO_RULES), *extra, role="規劃者", stage="規劃")
    assert rc == 0
    rule_lines = {line for path in REPO_RULES.rglob("*.md")
                  for line in path.read_text(encoding="utf-8").splitlines()}
    out_lines = set(out.splitlines())
    for name in ("ARCHITECTURE.md", "CODEGRAPH.md"):
        text = (REPO_RULES.parent / "docs" / name).read_text(encoding="utf-8")
        unique = {line for line in text.splitlines() if line.strip()} - rule_lines
        assert unique and not unique & out_lines
    assert "wfx/docs/ADOPTION.md" in out                       # 規則原文確實提到它
    assert "ADOPTION.md" not in section(out, MODULE_DOC_TITLE)  # 但不在定位範圍


# D8 說明文字只描述內容，⛔ 不以目的地為條件（判準同 test_flag_defaults_off_and_describes_content_only）
def test_notes_describe_content_only():
    texts = (MODULE_DOC_NOTE, MODULE_DOC_PACKAGE_NOTE, MODULE_DOC_WEB, MODULE_DOC_OVERRIDE_NOTE)
    for word in ("外送", "外部", "external", "審核者"):
        assert not any(word in text for text in texts), word


# 同機同輸入逐字相同：路徑只隨安裝位置變動
def test_full_output_is_stable_on_one_machine(run_cli, project_root):
    configure(project_root, modules=BOTH)
    assert run_cli("--rules-root", str(REPO_RULES)) == run_cli("--rules-root", str(REPO_RULES))
