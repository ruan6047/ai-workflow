"""W2.1 套件化：規則樹是 package data、版本只有一個居所、`facts` 第 ⑦ 節報這兩件事。

被測物刻意只到「可在原始碼樹證明」的那一層：**wheel 內容與乾淨 venv 的行為**由執行階段的
實機驗證負責（那需要 build 與安裝，⛔ 不進 pytest）。
⛔ 不驗規則內容、⛔ 不比對版本值大小、⛔ 不做散文判讀。
"""
import tomllib
from pathlib import Path

from wfx.core import rules
from wfx.verbs import facts as facts_verb
from wfx.verbs.main import main

from .conftest import REPO_RULES, TASK_ID
from .fakes import FakeClient

CLI_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = CLI_ROOT / 'pyproject.toml'


def declaration():
    return tomllib.loads(PYPROJECT.read_text(encoding='utf-8'))


# ── 規則樹＝package data ────────────────────────────────────────────────

def test_default_rules_root_is_inside_the_package_not_the_repo_layout():
    """預設來源由 `importlib.resources` 解析，⛔ 不靠 `vnext/` 那幾層目錄存在。

    這正是安裝後沒有 checkout 也能跑的理由；在原始碼樹裡兩者指到同一個目錄。
    """
    root = rules.default_rules_root()
    assert root.name == 'rules' and root.parent.name == 'wfx'
    assert root == REPO_RULES


def test_every_rule_document_travels_with_the_package():
    """三個目錄與 17 份 markdown 全在套件內；`.gitkeep` ⛔ 不是規則、不列入。"""
    root = rules.default_rules_root()
    assert sorted(p.name for p in root.iterdir() if p.is_dir()) == ['core', 'roles', 'stages']
    assert len(sorted(root.rglob('*.md'))) == 17
    assert len(rules.core_docs(root)) == 6


def test_brief_loads_the_four_layers_without_any_rules_root_flag(project_root, user_root, capsys):
    """不帶 `--rules-root` 的 `brief`＝安裝後的正常路徑；rc=0 且四層俱全。"""
    rc = main(['--project-root', str(project_root), 'brief', '--task', TASK_ID,
               '--role', '執行者', '--stage', '執行'], client=FakeClient())
    out = capsys.readouterr().out
    assert rc == 0
    for kind in ('framework:', 'user:', 'project:', 'task:'):
        assert f'[來源: {kind}' in out


# ── 版本只有一個居所 ────────────────────────────────────────────────────

def test_version_lives_only_in_pyproject():
    """`pyproject.toml` 的 `[project] version` 是唯一居所——程式碼⛔ 無第二份版本值。"""
    assert declaration()['project']['version']
    for path in sorted((CLI_ROOT / 'src/wfx').rglob('*.py')):
        text = path.read_text(encoding='utf-8')
        assert '__version__' not in text, path
        assert 'VERSION =' not in text, path
    assert not list((CLI_ROOT / 'src/wfx').rglob('VERSION'))


def test_missing_distribution_metadata_is_unknown_not_a_guess(monkeypatch):
    """未安裝時（PYTHONPATH 直跑原始碼樹）就是 `unknown`，⛔ 不由檔案或常數補一個值。"""
    def absent(name):
        raise rules.metadata.PackageNotFoundError(name)
    monkeypatch.setattr(rules.metadata, 'version', absent)
    assert rules.package_version() == 'unknown'
    monkeypatch.setattr(rules.metadata, 'version', lambda name: '9.9.9')
    assert rules.package_version() == '9.9.9'
    assert rules.metadata.version.__name__ == '<lambda>'   # 確認被測的是同一條路徑


def test_names_are_declared_exactly_once_each():
    """distribution／console script／最低 Python 各自逐字，⛔ 不與舊 CLI 的 `wf` 相撞。"""
    project = declaration()['project']
    assert project['name'] == rules.DISTRIBUTION == 'ai-workflow-vnext'
    assert project['scripts'] == {'wfx': 'wfx.verbs.main:main'}
    assert project['requires-python'] == '>=3.14'
    assert project['dependencies'] == []       # `gh`／`git` 是外部指令，⛔ 不是 Python 相依
    assert declaration()['tool']['setuptools']['package-data'] == {'wfx': ['rules/**/*.md']}


# ── `facts` 第 ⑦ 節 ─────────────────────────────────────────────────────

def section_seven(text):
    return text.split('## 7 · ', 1)[1].splitlines()[1:]


def test_seventh_section_reports_package_by_default(tmp_path, project_root, capsys):
    rc = main(['--project-root', str(project_root), 'facts', '--task', TASK_ID],
              client=FakeClient(), env={})
    lines = section_seven(capsys.readouterr().out)
    assert rc == 0
    assert lines[:2] == ['rules source: package', f'package version: {rules.package_version()}']


def test_seventh_section_reports_override_when_rules_root_is_given(project_root, rules_root,
                                                                   capsys):
    rc = main(['--project-root', str(project_root), 'facts', '--task', TASK_ID,
               '--rules-root', str(rules_root)], client=FakeClient(), env={})
    lines = section_seven(capsys.readouterr().out)
    assert rc == 0
    assert lines[0] == 'rules source: override'
    assert not any(str(rules_root) in line for line in lines)   # ⛔ 不印絕對路徑


def test_seventh_section_comes_after_the_existing_six_and_adds_no_second_version_source(tmp_path):
    """既有六節⛔ 不插隊、⛔ 不改字；版本字面在整份輸出裡只出現在第 ⑦ 節那一行。"""
    from .test_facts_remote import gather
    facts = gather(tmp_path)[0]
    text = facts_verb.render(facts)
    head, tail = text.split('\n## 7 · ', 1)
    assert facts_verb.render(facts, None) == text
    assert '## 6 · 權限' in head and '## 7' not in head
    assert tail.splitlines()[1:3] == ['rules source: package',
                                      f'package version: {rules.package_version()}']
