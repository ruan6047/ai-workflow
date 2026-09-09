"""消費 core/verbs.md §2、roles/conduct-common.md §1；src 與依賴邊界。"""
import ast
import json
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
        assert count <= 400, (path, count)  # 單檔觸發器；觸發後可決定不拆，理由寫交回單
        longest = max((f.end_lineno - f.lineno + 1 for f in ast.walk(ast.parse(source))
                       if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))), default=0)
        assert longest <= 150, (path, longest)  # 單一函式觸發器（舊 wfcli 的 god function 形狀）
        total += count
        print('SRC', path.relative_to(ROOT), count, longest, json.dumps(sorted(names)))
    assert total <= 4000  # 寬鬆後盾；分桶由單檔與函式兩個觸發器守
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


def test_verbs_layout_matches_the_dispatch_table():
    """verbs/ 的結構不變式：不以 _ 開頭的檔＝一個動詞，必在 DISPATCH 且導出 run。
    HELPERS 是明列的例外（brief 的第二個 --for 目標、move 的模組層），⛔ 不得默默增加。"""
    from wf.verbs.main import DISPATCH
    HELPERS = {'main.py', 'closeout.py', 'move_modules.py'}
    files = {p.name for p in (ROOT / 'cli/src/wf/verbs').glob('*.py')
             if not p.name.startswith('_')}
    assert files - HELPERS == {f'{verb}.py' for verb in DISPATCH}, sorted(files - HELPERS)
    for verb, module in DISPATCH.items():
        assert callable(getattr(module, 'run', None)), verb
    assert not [name for name in DISPATCH if f'{name}.py' in HELPERS]
    print('VERBS_LAYOUT', len(DISPATCH), sorted(files - HELPERS))
