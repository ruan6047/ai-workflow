"""P2 採用清單：五類分類、rc 契約、schema 比對、逐字穩定與零寫入。

隔離原則沿用 conftest：`git`／`gh` 一律走注入式 runner 替身、Project schema 走注入式 client，
**⛔ 不連網、⛔ 不執行真正的 `gh`**、⛔ 不 mutation 任何遠端資源。
被測的是分類與渲染，⛔ 不驗規則內容、⛔ 不做散文判讀。
"""
import hashlib
import json
import re

import pytest

from wfx.core import adopt
from wfx.gh import adopt as gh_adopt
from wfx.verbs.main import main

from .fakes import FIELD_NAMES, RecordedRunner, field_node

GIT_VERSION = 'git version 2.50.1 (Apple Git-155)'
GH_VERSION = 'gh version 2.92.0 (2026-04-28)'


class SchemaClient:
    """Project schema 的注入式替身：只回欄位節點，⛔ 無任何寫入方法。"""

    def __init__(self, names=FIELD_NAMES, overrides=()):
        self.nodes = [field_node(name) for name in names]
        for node in self.nodes:
            for name, key, value in overrides:
                if node['name'] == name:
                    node[key] = value

    def project(self, owner, number):
        return {'id': 'PVT_1', 'title': 'board', 'url': 'u', 'viewerCanUpdate': True}

    def project_field_names(self, project_id):
        return self.nodes


def runner(*, git=(0, GIT_VERSION + '\n', ''), gh=(0, GH_VERSION + '\n', ''),
           auth=(0, '', ''), worktree=(0, '.git\n', ''), default=None):
    """外部指令替身。順序有意義：`git --version` 必須排在 `git -C …` 之前。"""
    return RecordedRunner([
        (('git', '--version'), git),
        (('gh', '--version'), gh),
        (('gh', 'auth', 'status'), auth),
        (('git', '-C'), worktree),
    ], default=default)


def listing(project_root, rules_root, capsys, **kwargs):
    rc = main(['--project-root', str(project_root), 'facts', '--adopt',
               '--rules-root', str(rules_root)], env={}, **kwargs)
    return rc, capsys.readouterr().out


def states(text):
    """(項目名 → 類別)；只認第 1–5 節的清單項，⛔ 不把第 6 節的下一步算成第二份項目。"""
    out = {}
    for line in text.split(f'## 6 · {adopt.SECTION_TITLES[5]}', 1)[0].splitlines():
        if line.startswith('- ') and '：' in line:
            name, _, rest = line[2:].partition('：')
            out[name] = rest.partition('（')[0]
    return out


def tree(root):
    return sorted((str(p.relative_to(root)),
                   hashlib.sha256(p.read_bytes()).hexdigest())
                  for p in root.rglob('*') if p.is_file())


# ── rc 契約與互斥 ───────────────────────────────────────────────────────

def test_adopt_produces_the_listing_with_rc_zero_in_an_empty_directory(tmp_path, rules_root,
                                                                       capsys):
    """空的既存目錄：⛔ 不需 task／git 工作樹／`.wf/`／Project，清單照樣完整、rc=0。"""
    rc, out = listing(tmp_path, rules_root, capsys,
                      runner=runner(worktree=(128, '', 'fatal: not a git repository')))
    result = states(out)
    assert rc == 0
    for number, title in enumerate(adopt.SECTION_TITLES, start=1):
        assert f'## {number} · {title}' in out
    # 專案側每一項都還沒成立；`已完成` 只會出現在執行環境與框架套件那兩節
    # （那兩節反映的是**跑清單的這台機器**，⛔ 不是採用專案的狀態）。
    for name in ('.wf/ 目錄', '.wf/config.json', '.wf/model-policy.md', 'git 工作樹'):
        assert result[name] == adopt.MISSING, name
    for name in ('.wf/config.json 的 project', 'github.com repository 身分', 'Project 可讀'):
        assert result[name] == adopt.UNVERIFIED, name


def test_rc_one_when_even_the_listing_cannot_be_produced(tmp_path, rules_root, capsys):
    """`--project-root` 不是既存目錄＝連清單都產不出來；rc=1，⛔ 不印半份清單。"""
    rc = main(['--project-root', str(tmp_path / 'absent'), 'facts', '--adopt',
               '--rules-root', str(rules_root)], env={}, runner=runner())
    captured = capsys.readouterr()
    assert rc == 1
    assert 'AdoptUnavailable' in captured.err
    assert captured.out == ''


def test_adopt_is_mutually_exclusive_with_task_and_sha(tmp_path, rules_root):
    for extra in (['--task', '370'], ['--sha', 'deadbeef']):
        with pytest.raises(SystemExit) as exit_info:
            main(['--project-root', str(tmp_path), 'facts', '--adopt', *extra], env={})
        assert exit_info.value.code == 2


def test_neither_task_nor_adopt_is_a_usage_error(tmp_path):
    with pytest.raises(SystemExit) as exit_info:
        main(['--project-root', str(tmp_path), 'facts'], env={})
    assert exit_info.value.code == 2


def test_the_verb_set_is_still_exactly_three():
    """`--adopt` 是 `facts` 的另一種輸出，⛔ 不是第四個動詞。"""
    from wfx.verbs.main import DISPATCH
    assert set(DISPATCH) == {'brief', 'facts', 'write'}


# ── 五類都走得到 ───────────────────────────────────────────────────────

def test_all_five_classes_appear_in_one_listing(tmp_path, rules_root, capsys):
    (tmp_path / '.wf').mkdir()
    (tmp_path / '.wf/config.json').write_text('{"modules": []}', encoding='utf-8')
    rc, out = listing(tmp_path, rules_root, capsys,
                      runner=runner(auth=(1, '', 'You are not logged into any GitHub hosts.'),
                                    worktree=(128, '', 'fatal: not a git repository')))
    found = set(states(out).values())
    assert rc == 0
    assert found == set(adopt.STATES)


def test_blocked_items_carry_tool_rc_and_first_stderr_line(tmp_path, rules_root, capsys):
    rc, out = listing(tmp_path, rules_root, capsys,
                      runner=runner(gh=(127, '', 'zsh: command not found: gh\n第二行⛔ 不進清單')))
    assert rc == 0
    assert '- gh 可執行：環境阻塞（gh｜rc=127｜zsh: command not found: gh）' in out
    assert '第二行⛔ 不進清單' not in out
    assert states(out)['gh 已登入'] == adopt.UNVERIFIED


def test_auth_status_stdout_never_reaches_the_listing(tmp_path, rules_root, capsys):
    """`gh auth status` 的 **stdout** 帶帳號名與 token scope，⛔ 不得進清單——登入與未登入都是。

    `probe_login` 是唯一會碰到這份 stdout 的地方，它刻意丟掉；沒有這條，把 blocked 的第三欄
    改成 `stdout or stderr`（看起來像「訊息更完整」）能讓其餘所有 adopt 測試照樣全綠。
    登入成功那一支同理：`ok` 的 fact 是固定字串，⛔ 不是 stdout。
    """
    secret = '✓ Logged in to github.com account <帳號> (keyring)\n- Token scopes: repo, project'
    rc, out = listing(tmp_path, rules_root, capsys,
                      runner=runner(auth=(1, secret, 'You are not logged into any GitHub hosts.')))
    assert rc == 0
    assert ('- gh 已登入：環境阻塞（gh auth status｜rc=1｜'
            'You are not logged into any GitHub hosts.）') in out
    for leaked in ('Logged in to', '<帳號>', 'Token scopes', 'keyring'):
        assert leaked not in out, leaked

    rc, out = listing(tmp_path, rules_root, capsys, runner=runner(auth=(0, secret, '')))
    assert rc == 0
    assert '- gh 已登入：已完成（gh auth status rc=0）' in out
    for leaked in ('Logged in to', '<帳號>', 'Token scopes', 'keyring'):
        assert leaked not in out, leaked


def test_unexecutable_tool_reports_rc_unknown_not_a_made_up_code(tmp_path, rules_root, capsys):
    def explode(args, **kwargs):
        raise FileNotFoundError("[Errno 2] No such file or directory: 'git'")
    rc, out = listing(tmp_path, rules_root, capsys, runner=explode)
    assert rc == 0
    assert '- git 可執行：環境阻塞（git｜rc=unknown｜' in out
    assert states(out)['git 工作樹'] == adopt.UNVERIFIED


def test_broken_config_is_one_malformed_item_not_a_failed_listing(tmp_path, rules_root, capsys):
    """壞掉的 `config.json` 在清單上是一項「格式錯誤」，rc 仍 0；⛔ 不炸掉整份清單。"""
    (tmp_path / '.wf').mkdir()
    (tmp_path / '.wf/config.json').write_text('{ not json', encoding='utf-8')
    rc, out = listing(tmp_path, rules_root, capsys, runner=runner())
    assert rc == 0
    assert states(out)['.wf/config.json'] == adopt.MALFORMED
    assert states(out)['.wf/config.json 的 project'] == adopt.UNVERIFIED
    assert str(tmp_path) not in out            # 訊息裡的絕對路徑已換成相對寫法


def test_document_items_only_check_presence_and_non_emptiness(tmp_path, rules_root, capsys):
    (tmp_path / '.wf').mkdir()
    (tmp_path / '.wf/model-policy.md').write_text('   \n', encoding='utf-8')
    rc, out = listing(tmp_path, rules_root, capsys, runner=runner())
    assert states(out)['.wf/model-policy.md'] == adopt.MALFORMED
    (tmp_path / '.wf/model-policy.md').write_text('# 專案層政策\n', encoding='utf-8')
    rc, out = listing(tmp_path, rules_root, capsys, runner=runner())
    assert rc == 0
    assert states(out)['.wf/model-policy.md'] == adopt.DONE


# ── Project schema 比對 ────────────────────────────────────────────────

def configured(tmp_path, *, owner='o', number=9):
    (tmp_path / '.wf').mkdir(exist_ok=True)
    (tmp_path / '.wf/config.json').write_text(
        json.dumps({'project': {'owner': owner, 'number': number}}), encoding='utf-8')
    (tmp_path / '.wf/model-policy.md').write_text('# 專案層政策\n', encoding='utf-8')
    return tmp_path


def test_matching_schema_marks_every_core_concept_done(tmp_path, rules_root, capsys):
    rc, out = listing(configured(tmp_path), rules_root, capsys,
                      runner=runner(), client=SchemaClient())
    result = states(out)
    assert rc == 0
    assert result['Project 可讀'] == adopt.DONE
    assert result['「狀態」欄唯一居所'] == adopt.DONE
    for concept in ('狀態', '階段', 'owner', '風險', '緊急性', '期限', 'Resource'):
        assert result[f'核心概念「{concept}」'] == adopt.DONE, concept


def test_wrong_data_type_is_malformed_against_github_md_section_two(tmp_path, rules_root, capsys):
    client = SchemaClient(overrides=(('期限', 'dataType', 'TEXT'),))
    rc, out = listing(configured(tmp_path), rules_root, capsys, runner=runner(), client=client)
    assert rc == 0
    assert states(out)['核心概念「期限」'] == adopt.MALFORMED
    assert '期限 的型別＝TEXT' in out and 'core/github.md §2 要求 DATE' in out


def test_single_select_options_must_equal_values_md_verbatim(tmp_path, rules_root, capsys):
    client = SchemaClient(overrides=(('階段', 'options',
                                      [{'id': 'x', 'name': n} for n in ('需求', '規劃')]),))
    rc, out = listing(configured(tmp_path), rules_root, capsys, runner=runner(), client=client)
    assert rc == 0
    assert states(out)['核心概念「階段」'] == adopt.MALFORMED
    assert '需求／規劃／執行／審核／結案' in out


def test_missing_field_is_missing_and_the_remedy_never_creates_it(tmp_path, rules_root, capsys):
    client = SchemaClient(names=tuple(n for n in FIELD_NAMES if n != 'Resource'))
    rc, out = listing(configured(tmp_path), rules_root, capsys, runner=runner(), client=client)
    assert rc == 0
    assert states(out)['核心概念「Resource」'] == adopt.MISSING
    assert 'CLI ⛔ 不代建、⛔ 不改 Project schema' in out


def test_builtin_status_plus_custom_status_is_a_second_home(tmp_path, rules_root, capsys):
    """同時存在內建 `Status` 與自訂 `狀態` ⇒ 狀態有第二個居所＝格式錯誤。"""
    client = SchemaClient(names=FIELD_NAMES + ('狀態',))
    rc, out = listing(configured(tmp_path), rules_root, capsys, runner=runner(), client=client)
    result = states(out)
    assert rc == 0
    assert result['「狀態」欄唯一居所'] == adopt.MALFORMED
    assert result['核心概念「狀態」'] == adopt.UNVERIFIED
    assert '刪掉另建的「狀態」欄，只留內建的「Status」' in out


def test_schema_read_failure_is_blocked_with_the_gh_return_code(tmp_path, rules_root, capsys):
    rc, out = listing(configured(tmp_path), rules_root, capsys,
                      runner=runner(default=(1, '{}', 'gh: HTTP 500\n忽略第二行')))
    assert rc == 0
    assert '- Project 可讀：環境阻塞（gh｜rc=1｜gh: HTTP 500）' in out
    assert states(out)['核心概念「階段」'] == adopt.UNVERIFIED


def test_schema_is_not_probed_when_upstream_is_unmet(tmp_path, rules_root, capsys):
    """未登入時⛔ 不去讀 schema——那會把「無法確認」冒充成「環境阻塞」。"""
    calls = runner(auth=(1, '', 'not logged in'), default=(0, '{}', ''))
    rc, out = listing(configured(tmp_path), rules_root, capsys, runner=calls)
    assert rc == 0
    assert states(out)['Project 可讀'] == adopt.UNVERIFIED
    assert not any(call[:2] == ('gh', 'api') for call in calls.calls)


def test_expectations_come_from_the_rules_tree_not_from_code(rules_root):
    """七個概念與其欄位型別都是從 `core/github.md` §2 機械抽出的。"""
    found = gh_adopt.expectations(rules_root)
    assert [e.concept for e in found] == ['狀態', '階段', 'owner', '風險', '緊急性',
                                          '期限', 'Resource']
    assert [e.data_type for e in found] == ['SINGLE_SELECT', 'SINGLE_SELECT', 'TEXT',
                                            'SINGLE_SELECT', 'SINGLE_SELECT', 'DATE', 'TEXT']
    assert found[0].builtin_names == ('狀態', 'Status') and found[1].builtin_names == ()


# ── 穩定輸出與零寫入 ───────────────────────────────────────────────────

def test_same_state_twice_is_byte_identical_and_has_no_absolute_path(tmp_path, rules_root,
                                                                     capsys):
    root = configured(tmp_path)
    first = listing(root, rules_root, capsys, runner=runner(), client=SchemaClient())[1]
    second = listing(root, rules_root, capsys, runner=runner(), client=SchemaClient())[1]
    assert first == second
    for absolute in (str(root), str(rules_root)):
        assert absolute not in first
    assert re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:', first) is None       # ⛔ 無時間戳


def test_the_listing_writes_nothing_at_all(tmp_path, rules_root, capsys):
    root = configured(tmp_path)
    before = tree(root)
    for _ in range(2):
        listing(root, rules_root, capsys, runner=runner(), client=SchemaClient())
    assert tree(root) == before


def test_summary_counts_every_item_exactly_once(tmp_path, rules_root, capsys):
    rc, out = listing(tmp_path, rules_root, capsys, runner=runner())
    summary = out.split(f'## 7 · {adopt.SECTION_TITLES[6]}', 1)[1]
    counted = {line.split(': ')[0]: int(line.split(': ')[1])
               for line in summary.splitlines() if ': ' in line}
    assert rc == 0
    assert sum(counted[state] for state in adopt.STATES) == counted['總計'] == len(states(out))


def test_next_steps_only_lists_the_unfinished_and_says_the_cli_applies_nothing(tmp_path,
                                                                              rules_root, capsys):
    rc, out = listing(tmp_path, rules_root, capsys, runner=runner())
    steps = out.split(f'## 6 · {adopt.SECTION_TITLES[5]}', 1)[1].split('## 7 · ', 1)[0]
    assert 'CLI 只印，⛔ 不代為套用' in steps
    assert 'python 直譯器' not in steps          # 已完成的⛔ 不列
    assert '.wf/config.json' in steps
    assert not any(line != line.rstrip() for line in steps.splitlines())


# ── 既有三動詞的 fail-loud 相容 ────────────────────────────────────────

def test_broken_config_still_fails_loud_for_the_three_ordinary_verbs(tmp_path, rules_root,
                                                                     capsys):
    """`load_config()` 下放到動詞的 `run()` 之後，rc 與訊息逐字不變。"""
    (tmp_path / '.wf').mkdir()
    (tmp_path / '.wf/config.json').write_text('{ not json', encoding='utf-8')
    calls = (['facts', '--task', '1'],
             ['brief', '--task', '1', '--role', '執行者', '--stage', '執行'],
             ['write', '--task', '1', '--field', 'owner=x'])
    for argv in calls:
        assert main(['--project-root', str(tmp_path), *argv], env={}) == 1
        assert 'ConfigError' in capsys.readouterr().err
