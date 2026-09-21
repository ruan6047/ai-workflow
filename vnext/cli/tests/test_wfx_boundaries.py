"""C6 機械錨＋CLI 邊界：對**程式碼結構**的檢查，⛔ 不是散文判讀。"""
import ast
import subprocess
import sys
from pathlib import Path

import pytest

from wfx.core.context import ConfigError, load_config
from wfx.gh.client import (GhError, NotFound, NotLoggedIn, PermissionDenied, TransportError,
                           GhClient)
from wfx.gh.target import TargetError, parse_task, resolve_repository, slug_of
from wfx.verbs.main import main

from .fakes import RecordedRunner

SRC = Path(__file__).resolve().parents[1] / 'src/wfx'
NETWORK = {'subprocess', 'urllib', 'socket', 'http', 'requests', 'httpx', 'aiohttp', 'ftplib'}
PROVIDERS = {'anthropic', 'openai', 'google', 'cohere', 'mistralai', 'ollama', 'litellm'}


def imports(text):
    found = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            found.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level:
            found.add((node.module or '').split('.')[0])
    return found


def modules(text):
    names = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level:
            names.add(node.module or '')
    return names


def test_import_scope_negative_control():
    assert imports('import socket\nimport requests') & NETWORK == {'socket', 'requests'}
    assert modules('from wfx.gh.client import GhClient') == {'wfx.gh.client'}


def test_core_never_imports_gh_or_subprocess_and_tree_is_stdlib_only():
    paths = sorted(SRC.rglob('*.py'))
    assert paths, SRC
    total = 0
    for path in paths:
        source = path.read_text(encoding='utf-8')
        names, used = imports(source), modules(source)
        assert not (names - sys.stdlib_module_names - {'wfx'}), path
        assert not names & PROVIDERS, path
        if path.parts[path.parts.index('wfx') + 1] == 'core':
            assert not any(m.startswith('wfx.gh') for m in used), path
            assert 'subprocess' not in names, path
        if 'gh' not in path.parts:
            assert not names & NETWORK, path
        total += sum(1 for line in source.splitlines() if line.strip())
    print('WFX_SRC_NONBLANK', total)   # C7 行數只作警示；⛔ 無 rc≠0 的門檻斷言


def test_task_id_is_opaque_to_core_but_parsed_in_gh():
    assert (parse_task('370').slug, parse_task('370').number) == (None, 370)
    assert parse_task('#370').number == 370
    assert (parse_task('o/r#370').slug, parse_task('o/r#370').number) == ('o/r', 370)
    with pytest.raises(TargetError):
        parse_task('not-a-task')


def test_slug_only_matches_github_com():
    assert slug_of('git@github.com:o/r.git') == 'o/r'
    assert slug_of('https://github.com/o/r') == 'o/r'
    assert slug_of('https://gitlab.com/o/r') is None


def test_repository_candidates_must_be_unambiguous(tmp_path):
    root = tmp_path / 'r'
    root.mkdir()
    for args in (('init', '-q'), ('remote', 'add', 'a', 'git@github.com:o/one.git'),
                 ('remote', 'add', 'b', 'git@github.com:o/two.git')):
        subprocess.run(('git', '-C', str(root), *args), capture_output=True, check=True)
    with pytest.raises(TargetError, match='候選不唯一'):
        resolve_repository(root, env_repo=None)
    assert resolve_repository(root, configured='a').slug == 'o/one'
    with pytest.raises(TargetError, match='remote 不存在'):
        resolve_repository(root, configured='zz')


def test_no_remote_falls_back_to_gh_repo_then_fails_loud(tmp_path):
    assert resolve_repository(tmp_path, env_repo='o/r').slug == 'o/r'
    with pytest.raises(TargetError, match='未能取得 repository'):
        resolve_repository(tmp_path, env_repo=None)


def test_client_error_classification_never_infers_absence():
    def client(rc, stdout, stderr):
        return GhClient('o/r', runner=RecordedRunner([], default=(rc, stdout, stderr)))
    cases = ((1, '{}', 'HTTP 404'), (1, '{}', 'HTTP 403'), (1, '{}', 'HTTP 500'),
             (4, '{}', 'gh auth login'), (1, '{}', 'HTTP 422'))
    expected = (NotFound, PermissionDenied, TransportError, NotLoggedIn, GhError)
    for (rc, stdout, stderr), kind in zip(cases, expected):
        with pytest.raises(kind):
            client(rc, stdout, stderr).ci_checks('deadbeef')
    with pytest.raises(GhError):   # 未知錯誤⛔ 不得降級成 NotFound
        client(1, 'not json', 'weird failure').ci_checks('deadbeef')


def test_client_has_no_mutation_surface():
    banned = {'create', 'update', 'delete', 'add', 'close', 'post', 'edit', 'write', 'set'}
    for name in dir(GhClient):
        assert not any(name.startswith(prefix) for prefix in banned), name


def test_config_shape_only(tmp_path):
    assert load_config(tmp_path) == {'rules': None, 'remote': None, 'project': None}
    wf = tmp_path / '.wf'
    wf.mkdir()
    (wf / 'config.json').write_text('{"project": {"owner": "o", "number": 9}}')
    assert load_config(tmp_path)['project'] == {'owner': 'o', 'number': 9}
    (wf / 'config.json').write_text('{"modules": []}')
    with pytest.raises(ConfigError, match='未知鍵'):
        load_config(tmp_path)
    (wf / 'config.json').write_text('{"remote": "https://github.com/o/r"}')
    with pytest.raises(ConfigError, match='remote'):
        load_config(tmp_path)


def test_dispatch_is_exactly_facts_for_this_workpackage(capsys):
    """本工作包只登記 `facts`；brief／write 由 W1.6／W1.8 各自登記，此處⛔ 不預建。"""
    from wfx.verbs.main import DISPATCH
    assert set(DISPATCH) == {'facts'}
    assert main([]) == 2
    assert main(['write', '--task', '1']) == 2      # 尚未登記＝用法錯誤，⛔ 不是假成功
    assert main(['--project-root']) == 2            # 旗標缺值
    assert main(['facts', '--project-root', '.']) == 2   # 全域旗標⛔ 不得出現在動詞之後
    assert 'wfx [--project-root <p>] <facts>' in capsys.readouterr().err


def test_verb_error_paths_return_rc_one_not_a_traceback(tmp_path, capsys):
    (tmp_path / '.wf').mkdir()
    (tmp_path / '.wf/config.json').write_text('{ not json')
    assert main(['--project-root', str(tmp_path), 'facts', '--task', '1']) == 1
    assert 'ConfigError' in capsys.readouterr().err
