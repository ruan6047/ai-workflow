"""專用入口的程序邊界；只執行 fake，空 .codegraph 不是實際索引。"""
import json
import sys

import pytest

from wfx import codegraph


@pytest.fixture
def setup(tmp_path, monkeypatch):
    project = tmp_path / 'workflow'
    (project / '.wf').mkdir(parents=True)
    (project / '.wf/config.json').write_text('{"modules": ["codegraph"]}')
    root = tmp_path / 'code tree'
    (root / '.codegraph').mkdir(parents=True)
    log = tmp_path / 'calls.jsonl'
    binary = tmp_path / 'fake codegraph'
    binary.write_text(f'#!{sys.executable}\n' + '''
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ['STUB_LOG'], 'a') as log:
    log.write(json.dumps({'argv': args, 'cwd': str(Path.cwd()),
                         'env': {k: os.environ.get(k) for k in (
                             'DO_NOT_TRACK', 'CODEGRAPH_TELEMETRY',
                             'CODEGRAPH_NO_UPDATE_CHECK', 'CODEGRAPH_NO_DOWNLOAD',
                             'NODE_DISABLE_COMPILE_CACHE', 'CODEGRAPH_DIR', 'PATH')}}) + '\\n')
if args == ['--version']:
    print(os.environ.get('STUB_VERSION', '1.6.2'))
    sys.exit(int(os.environ.get('STUB_VERSION_RC', '0')))
assert args[0] in ('query', 'explore'), args
assert args[1] == '--path' and args[-2] == '--', args
assert args[3:-2] == (['--json'] if args[0] == 'query' else []), args
sys.stdout.buffer.write(b'raw output\\nno-reread footer\\n')
sys.stderr.buffer.write(b'raw stderr\\n')
sys.exit(int(os.environ.get('STUB_RC', '0')))
''')
    binary.chmod(0o755)
    monkeypatch.setenv('WFX_CODEGRAPH_BIN', str(binary))
    monkeypatch.setenv('STUB_LOG', str(log))
    return project, root, binary, log


def invoke(setup, *args):
    project, root, _, _ = setup
    return codegraph.main(['--project-root', str(project), '--path', str(root), *args])


def calls(setup):
    log = setup[-1]
    return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


@pytest.mark.parametrize('command,text', [('query', 'two words; $(untouched)'),
                                         ('query', '-leading dash'),
                                         ('explore', '依賴關係'), ('explore', '--help')])
def test_fixed_argv_environment_and_native_streams(setup, monkeypatch, capfd, command, text):
    for name in ('DO_NOT_TRACK', 'CODEGRAPH_TELEMETRY', 'CODEGRAPH_NO_UPDATE_CHECK',
                 'CODEGRAPH_NO_DOWNLOAD', 'NODE_DISABLE_COMPILE_CACHE', 'CODEGRAPH_DIR'):
        monkeypatch.setenv(name, 'inherited-wrong')
    monkeypatch.setenv('STUB_RC', '23')
    assert invoke(setup, command, '--', text) == 23
    captured = capfd.readouterr()
    assert captured.out == 'raw output\nno-reread footer\n'
    assert captured.err == 'raw stderr\n'
    version, operation = calls(setup)
    assert version['argv'] == ['--version']
    expected = [command, '--path', str(setup[1].resolve())]
    assert operation['argv'] == expected + (['--json'] if command == 'query' else []) + ['--', text]
    for call in (version, operation):
        assert call['cwd'] == str(setup[1].resolve())
        assert call['env'] == {'DO_NOT_TRACK': '1', 'CODEGRAPH_TELEMETRY': '0',
                               'CODEGRAPH_NO_UPDATE_CHECK': '1', 'CODEGRAPH_NO_DOWNLOAD': '1',
                               'NODE_DISABLE_COMPILE_CACHE': '1', 'CODEGRAPH_DIR': '.codegraph',
                               'PATH': __import__('os').environ['PATH']}


@pytest.mark.parametrize('value', [None, '{}', '{"modules": null}', '{"modules": ["tdd"]}'])
def test_disabled_or_absent_config_never_starts_binary(setup, value):
    config = setup[0] / '.wf/config.json'
    config.unlink() if value is None else config.write_text(value)
    assert invoke(setup, 'query', 'symbol') == 1
    assert calls(setup) == []


@pytest.mark.parametrize('value', ['{', '{"modules": []}', '{"unknown": true}'])
def test_invalid_config_is_usage_error_without_child(setup, value):
    (setup[0] / '.wf/config.json').write_text(value)
    assert invoke(setup, 'query', 'symbol') == 2
    assert calls(setup) == []


@pytest.mark.parametrize('kind', ['missing', 'parent', 'symlink', 'file'])
def test_requires_own_index_directory(setup, kind):
    root = setup[1]
    (root / '.codegraph').rmdir()
    if kind in ('parent', 'symlink'):
        other = root.parent / '.codegraph'
        other.mkdir()
        if kind == 'symlink':
            (root / '.codegraph').symlink_to(other, target_is_directory=True)
    elif kind == 'file':
        (root / '.codegraph').touch()
    assert invoke(setup, 'query', 'symbol') == 1
    assert calls(setup) == []


@pytest.mark.parametrize('version,rc', [('1.6.3', '0'), ('garbage 1.6.2', '0'), ('1.6.2', '4')])
def test_version_must_match_and_succeed_before_operation(setup, monkeypatch, version, rc):
    monkeypatch.setenv('STUB_VERSION', version)
    monkeypatch.setenv('STUB_VERSION_RC', rc)
    assert invoke(setup, 'query', 'symbol') == 1
    assert [c['argv'] for c in calls(setup)] == [['--version']]


@pytest.mark.parametrize('kind,expected', [('relative', 2), ('missing', 1), ('nonexec', 1)])
def test_binary_must_be_absolute_existing_executable(setup, monkeypatch, kind, expected):
    if kind == 'relative':
        monkeypatch.setenv('WFX_CODEGRAPH_BIN', 'codegraph')
    elif kind == 'missing':
        setup[2].unlink()
    else:
        setup[2].chmod(0o644)
    assert invoke(setup, 'query', 'symbol') == expected
    assert calls(setup) == []


def test_default_binary_location_and_canonical_root(setup, monkeypatch):
    home = setup[2].parent
    target = home / '.local/bin/codegraph'
    target.parent.mkdir(parents=True)
    setup[2].rename(target)
    monkeypatch.delenv('WFX_CODEGRAPH_BIN')
    monkeypatch.setattr(codegraph.Path, 'home', lambda: home)
    root_alias = home / 'tree alias'
    root_alias.symlink_to(setup[1], target_is_directory=True)
    assert codegraph.main(['--project-root', str(setup[0]), '--path', str(root_alias),
                           'query', 'symbol']) == 0
    assert calls(setup)[-1]['cwd'] == str(setup[1].resolve())


@pytest.mark.parametrize('args', [[], ['init', 'x'], ['sync', 'x'],
                                   ['install'], ['serve'], ['query', 'x', '--json'],
                                   ['query', 'one', 'two']])
def test_no_arbitrary_commands_or_arguments(setup, args):
    with pytest.raises(SystemExit) as exc:
        invoke(setup, *args)
    assert exc.value.code == 2
    assert calls(setup) == []


def test_missing_path_fails_without_process(setup):
    assert codegraph.main(['--project-root', str(setup[0]), '--path', str(setup[1] / 'absent'),
                           'query', 'symbol']) == 2
    assert calls(setup) == []


def test_both_roots_are_required(setup):
    for args in (['query', 'x'], ['--path', str(setup[1]), 'query', 'x'],
                 ['--project-root', str(setup[0]), 'query', 'x']):
        with pytest.raises(SystemExit) as exc:
            codegraph.main(args)
        assert exc.value.code == 2
    assert calls(setup) == []


def test_help_works_without_any_setup(capsys):
    with pytest.raises(SystemExit) as exc:
        codegraph.main(['--help'])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert '1.6.2' in output and 'wfx/docs/CODEGRAPH.md' in output
