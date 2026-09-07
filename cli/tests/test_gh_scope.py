"""第 6 步測試策略與 S05 射程：src 母體、stdlib、網路邊界及離線護欄。"""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from .test_compose_schema import ROOT
from .test_gh_write_recording import ensure_clean

NETWORK = {'subprocess', 'urllib', 'socket', 'http', 'requests', 'httpx', 'aiohttp', 'ftplib'}


def imports(text):
    found = set()
    for node in ast.walk(ast.parse(text, feature_version=(3, 11))):
        if isinstance(node, ast.Import):
            found.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level:
            found.add(node.module.split('.')[0])
    return found


def pytest_sessionstart(session):
    if os.environ.get('WF_S05_OFFLINE') != '1':
        return
    real_run = subprocess.run

    def offline_run(argv, *args, **kwargs):
        if isinstance(argv, (str, bytes)) or Path(argv[0]).name in {'gh', 'curl', 'wget', 'ssh'}:
            raise AssertionError('OFFLINE_NETWORK_DENIED')
        return real_run(argv, *args, **kwargs)

    subprocess.run = offline_run
    with pytest.raises(AssertionError, match='OFFLINE_NETWORK_DENIED'):
        subprocess.run(['gh', 'api', 'offline-negative-control'])
    print('OFFLINE_NETWORK_DENIED negative control passed')


def test_source_inventory_and_negative_controls():
    assert imports('import socket\nimport requests') & NETWORK == {'socket', 'requests'}
    assert imports('import requests') - sys.stdlib_module_names == {'requests'}
    print('IMPORT_NEGATIVE_CONTROL socket, requests detected')
    paths = sorted((ROOT / 'cli/src/wf').rglob('*.py'))
    total = 0
    for path in paths:
        source = path.read_text()
        names = imports(source)
        assert not (names - sys.stdlib_module_names - {'wf'}), path
        if path.parent.name != 'gh':
            assert not names & NETWORK, path
        count = len(source.splitlines())
        total += count
        print('SRC', path.relative_to(ROOT), count, json.dumps(sorted(names)))
    assert total <= 3000
    print('SRC_FILES', len(paths), 'SRC_TOTAL', total)
    for relative in ('compose/blocks.py', 'compose/project_config.py', 'gh/client.py', 'gh/writes.py', 'verbs/_write.py'):
        doc = ast.get_docstring(ast.parse((ROOT / 'cli/src/wf' / relative).read_text()))
        assert doc and '.md' in doc and '§' in doc, relative


def test_all_gh_fixtures_are_secret_free():
    with pytest.raises(ValueError, match='憑證'):
        ensure_clean({'body': 'github_pat_' + 'Z' * 30})
    paths = sorted(path for directory in ('gh', 's05')
                   for path in (ROOT / 'cli/tests/fixtures' / directory).glob('*.json'))
    for path in paths:
        ensure_clean(json.loads(path.read_text()))
        print('SECRET_SCANNED', path.relative_to(ROOT))
    assert paths
    print('SECRET_SCANNED_FILES', len(paths))
