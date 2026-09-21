"""C6 機械錨＋CLI 邊界：對**程式碼結構**的檢查，⛔ 不是散文判讀。

本檔是整合後的**單一** C6 錨（W1.6 的 test_wfx_scope.py 已併入此處）：
`wfx` 全樹⛔ 無實際網路客戶端與模型 provider SDK；`wfx/core/**` ⛔ 無 `wfx.gh`、⛔ 無 `subprocess`。
⛔ 不做禁用字串掃描、⛔ 不設行數門檻——那些撞 A3。
"""
import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest

from wfx.core.context import ConfigError, load_config
from wfx.core.layers import CORE_CONCEPTS
from wfx.gh.client import (GhError, NotFound, NotLoggedIn, PermissionDenied, TransportError,
                           GhClient)
from wfx.gh.target import TargetError, parse_task, resolve_repository, slug_of
from wfx.verbs.main import main

from .conftest import REPO_ROOT
from .fakes import RecordedRunner

SRC = Path(__file__).resolve().parents[1] / 'src/wfx'
# 會連網的匯入根。`urllib.parse` 是純網址編碼工具、⛔ 不是網路客戶端，因此逐名放行；
# `urllib.request`／`http`／`socket`／`requests`／`httpx` 仍全樹禁止。
NETWORK = {'urllib', 'socket', 'http', 'requests', 'httpx', 'aiohttp', 'ftplib'}
URL_TOOLS = {'urllib.parse'}
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


def network_modules(text):
    """實際會連網的匯入（逐名比對）；`urllib.parse` 這類純編碼工具⛔ 不算。"""
    return {name for name in modules(text)
            if name.split('.')[0] in NETWORK and name not in URL_TOOLS}


def test_import_scope_negative_control():
    """放行 `urllib.parse` 之後，這條錨仍抓得到真正的網路與 provider 匯入。"""
    assert network_modules('import socket\nimport requests') == {'socket', 'requests'}
    assert network_modules('from urllib.request import urlopen') == {'urllib.request'}
    assert network_modules('from urllib.parse import quote') == set()
    assert imports('import anthropic\nimport openai') & PROVIDERS == {'anthropic', 'openai'}
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
        assert not network_modules(source), path          # 全樹：⛔ 無實際網路客戶端
        if path.parts[path.parts.index('wfx') + 1] == 'core':
            assert not any(m.startswith('wfx.gh') for m in used), path
            assert 'subprocess' not in names, path
        if 'gh' not in path.parts:
            assert 'subprocess' not in names, path        # 起 `gh` 子行程只住 wfx.gh
        total += sum(1 for line in source.splitlines() if line.strip())
    print('WFX_SRC_NONBLANK', total)   # C7 行數只作警示；⛔ 無 rc≠0 的門檻斷言


def test_core_keeps_the_task_identifier_opaque():
    """核心⛔ 不理解任務識別的格式——不得出現 repo#issue 的解析。"""
    for path in sorted((SRC / 'core').rglob('*.py')):
        text = path.read_text(encoding='utf-8')
        assert "split('#')" not in text and 'split("#")' not in text, path


def test_seven_core_concepts_match_the_rules_document():
    """七個核心概念的唯一居所是 core/github.md；程式碼只固定呈現順序。"""
    text = (REPO_ROOT / 'vnext' / 'rules' / 'core' / 'github.md').read_text(encoding='utf-8')
    block = text.split('## 2 · 七個核心概念', 1)[1].split('\n## ', 1)[0]
    rows = [m.group(1).strip()
            for m in re.finditer(r'^\|([^|]+)\|[^|]+\|[^|]*\|\s*$', block, re.M)]
    named = {r for r in rows if r and r not in {'概念', '落地'} and set(r) - set('-: ')}
    assert named == set(CORE_CONCEPTS)


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


def test_dispatch_is_exactly_the_three_verbs(capsys):
    """W1.8 登記第三個動詞後動詞集合固定為三；⛔ 不長出第四個。"""
    from wfx.verbs.main import DISPATCH
    assert set(DISPATCH) == {'brief', 'facts', 'write'}
    assert main([]) == 2
    assert main(['move', '--task', '1']) == 2       # 未登記的動詞＝用法錯誤，⛔ 不是假成功
    assert main(['--project-root']) == 2            # 旗標缺值
    assert main(['facts', '--project-root', '.']) == 2   # 全域旗標⛔ 不得出現在動詞之後
    assert 'wfx [--project-root <p>] <brief｜facts｜write>' in capsys.readouterr().err


def test_mutation_surface_lives_only_in_gh_writes():
    """寫入能力只住 `wfx/gh/writes.py`，且只有 `verbs/write.py` 匯入它。

    這是對**程式碼結構**的檢查：唯讀的 `facts`／`brief` 路徑不可能夾帶 mutation。
    """
    importers = {path.relative_to(SRC).as_posix() for path in sorted(SRC.rglob('*.py'))
                 if any(m.startswith('wfx.gh.writes')
                        for m in modules(path.read_text(encoding='utf-8')))}
    assert importers == {'verbs/write.py'}
    mutating = {path.relative_to(SRC).as_posix() for path in sorted(SRC.rglob('*.py'))
                if 'mutation(' in path.read_text(encoding='utf-8')}
    assert mutating == {'gh/writes.py'}


def test_verb_error_paths_return_rc_one_not_a_traceback(tmp_path, capsys):
    (tmp_path / '.wf').mkdir()
    (tmp_path / '.wf/config.json').write_text('{ not json')
    assert main(['--project-root', str(tmp_path), 'facts', '--task', '1']) == 1
    assert 'ConfigError' in capsys.readouterr().err
